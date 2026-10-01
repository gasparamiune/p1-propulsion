"""Tests de la lógica del acelerador de P1 (04_diseno/electronica/firmware/throttle_logic.c).

Compila throttle_logic.c con gcc (C99 estricto, -Werror) a una librería compartida en un directorio
temporal y la usa vía ctypes. Los estados/flags se leen del header (no se duplican aquí); los
requisitos (tiempo de corte, límite de reversa) se leen de inputs.yaml / calc_electronica.py.
"""
from __future__ import annotations

import ctypes
import random
import re
import shutil
import subprocess
import sys
import xml.dom.minidom
from ctypes import POINTER, byref, c_float, c_int8, c_uint8, c_uint16, c_uint32
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ELEC = ROOT / "04_diseno" / "electronica"
FW = ELEC / "firmware"
SRC_C, SRC_H = FW / "throttle_logic.c", FW / "throttle_logic.h"
sys.path.insert(0, str(ELEC))

INO = FW / "p1_throttle" / "p1_throttle.ino"
# Tick del banco de pruebas = TICK_MS del sketch (leído, no duplicado)
DT = int(re.search(r"\bTICK_MS\s*=\s*(\d+)", INO.read_text(encoding="utf-8")).group(1))


# ------------------------------------------------------------------ constantes del header
def _defines():
    txt = SRC_H.read_text(encoding="utf-8")
    return {m.group(1): int(m.group(2), 0)
            for m in re.finditer(r"#define\s+(TL_\w+)\s+(0x[0-9A-Fa-f]+|\d+)u?\b", txt)}


D = _defines()
ST = {k[3:]: v for k, v in D.items() if k in ("TL_DISARMED", "TL_ARMED", "TL_RUN_FWD", "TL_RUN_REV",
                                               "TL_DWELL_ZERO", "TL_FAULT")}
ARMED_STATES = {ST["ARMED"], ST["RUN_FWD"], ST["RUN_REV"], ST["DWELL_ZERO"]}
F = {k[5:]: v for k, v in D.items() if k.startswith("TL_F_")}


# ------------------------------------------------------------------ espejo ctypes de los structs
class Cfg(ctypes.Structure):
    _fields_ = [("deadband", c_float), ("expo", c_float), ("reverse_limit", c_float), ("jump_travel_per_s", c_float),
                ("adc_rev", c_uint16), ("adc_center", c_uint16), ("adc_fwd", c_uint16), ("adc_fault_low", c_uint16),
                ("adc_fault_high", c_uint16), ("min_half_span", c_uint16), ("jump_noise_counts", c_uint16),
                ("arm_hold_ms", c_uint16), ("ramp_up_ms", c_uint16), ("ramp_down_ms", c_uint16),
                ("dwell_ms", c_uint16), ("watchdog_ms", c_uint16), ("ppm_min_us", c_uint16),
                ("ppm_center_us", c_uint16), ("ppm_max_us", c_uint16), ("cal_valid", c_uint8), ("use_vesc_ok", c_uint8)]


class Inp(ctypes.Structure):
    _fields_ = [("adc", c_uint16), ("kill_cord_ok", c_uint8), ("estop_ok", c_uint8), ("vesc_ok", c_uint8),
                ("_pad", c_uint8 * 3)]


class Out(ctypes.Structure):
    _fields_ = [("cmd", c_float), ("target", c_float), ("ppm_us", c_uint16), ("flags", c_uint16),
                ("state", c_uint8), ("enable", c_uint8), ("_pad", c_uint8 * 2)]


class Ctx(ctypes.Structure):
    _fields_ = [("cfg", Cfg), ("last", Out), ("out", c_float), ("uptime_ms", c_uint32), ("arm_ms", c_uint32),
                ("zero_ms", c_uint32), ("latched", c_uint16), ("prev_adc", c_uint16), ("prev_valid", c_uint8),
                ("armed", c_uint8), ("arm_run", c_uint8), ("zero_run", c_uint8), ("last_dir", c_int8),
                ("cfg_err", c_uint8), ("_pad", c_uint8 * 2)]


# ------------------------------------------------------------------ compilación
@pytest.fixture(scope="session")
def lib(tmp_path_factory):
    gcc = shutil.which("gcc")
    if gcc is None:
        pytest.skip("gcc no disponible")
    out = tmp_path_factory.mktemp("fw") / "libthrottle.so"
    cmd = [gcc, "-std=c99", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion", "-Wshadow",
           "-Wdouble-promotion", "-Werror", "-fPIC", "-shared", "-o", str(out), str(SRC_C)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"gcc falló:\n{r.stderr}"
    L = ctypes.CDLL(str(out))
    L.tl_default_config.argtypes = [POINTER(Cfg)]
    L.tl_config_check.argtypes = [POINTER(Cfg)]
    L.tl_config_check.restype = c_uint8
    L.tl_calibrate.argtypes = [POINTER(Cfg), c_uint16, c_uint16, c_uint16]
    L.tl_calibrate.restype = c_uint8
    L.tl_init.argtypes = [POINTER(Ctx), POINTER(Cfg)]
    L.tl_tick.argtypes = [POINTER(Ctx), POINTER(Inp), c_uint32]
    L.tl_tick.restype = Out
    L.tl_position.argtypes = [POINTER(Cfg), c_uint16]
    L.tl_position.restype = c_float
    L.tl_shape.argtypes = [POINTER(Cfg), c_float]
    L.tl_shape.restype = c_float
    L.tl_cmd_to_ppm.argtypes = [POINTER(Cfg), c_float]
    L.tl_cmd_to_ppm.restype = c_uint16
    L.tl_state_name.argtypes = [c_uint8]
    L.tl_state_name.restype = ctypes.c_char_p
    for f in ("config", "inputs", "outputs", "ctx"):
        getattr(L, f"tl_sizeof_{f}").restype = c_uint16
    return L


def default_cfg(L, calibrated=True):
    c = Cfg()
    L.tl_default_config(byref(c))
    if calibrated:
        assert L.tl_calibrate(byref(c), c.adc_rev, c.adc_center, c.adc_fwd) == 0
    return c


class Sim:
    """Banco de pruebas: llama tl_tick con dt fijo y guarda la traza.
    Los movimientos grandes del puño se hacen con goto() (mano real, 100 ms): un salto instantáneo
    centro→tope es físicamente imposible y el detector de saltos lo marca como falla (test aparte)."""

    def __init__(self, L, cfg=None, dt=DT):
        self.L, self.dt, self.t, self.pos = L, dt, 0, 0.0
        self.cfg = cfg if cfg is not None else default_cfg(L)
        self.ctx = Ctx()
        L.tl_init(byref(self.ctx), byref(self.cfg))
        self.trace = []

    def adc(self, pos):
        c = self.cfg
        if pos >= 0:
            return int(round(c.adc_center + pos * (c.adc_fwd - c.adc_center)))
        return int(round(c.adc_center + (-pos) * (c.adc_rev - c.adc_center)))

    def in_zero(self, adc):
        return abs(self.L.tl_position(byref(self.cfg), adc)) <= self.cfg.deadband + 1e-6

    def step(self, adc=None, pos=None, kill=1, estop=1, vesc=1, dt=None):
        if adc is None:
            if pos is not None:
                self.pos = pos
            adc = self.adc(self.pos)
        dt = self.dt if dt is None else dt
        o = self.L.tl_tick(byref(self.ctx), byref(Inp(adc, kill, estop, vesc)), dt)
        self.t += dt
        self.trace.append(dict(t=self.t, adc=adc, kill=kill, estop=estop, dt=dt, cmd=o.cmd, ppm=o.ppm_us,
                               state=o.state, flags=o.flags, en=o.enable, target=o.target))
        return o

    def goto(self, pos, ms=100, **kw):
        p0, n = self.pos, max(1, int(round(ms / self.dt)))
        o = None
        for k in range(1, n + 1):
            o = self.step(pos=p0 + (pos - p0) * k / n, **kw)
        return o

    def hold(self, ms, pos=None, **kw):
        o = None
        if pos is not None and abs(pos - self.pos) > 1e-9:
            o = self.goto(pos, **kw)
        for _ in range(int(round(ms / self.dt))):
            o = self.step(**kw)
        return o

    def arm(self):
        o = self.hold(1000 + 2 * self.dt, pos=0.0)
        assert o.state == ST["ARMED"], self.L.tl_state_name(o.state)
        return o


def is_neutral(o):
    return o.cmd == 0.0 and o.ppm_us == 1500 and o.enable == 0


def last_zero_before(trace, idx):
    """Tiempo del último tick con cmd == 0 antes del índice idx."""
    j = idx
    while j >= 0 and trace[j]["cmd"] != 0.0:
        j -= 1
    return trace[j]["t"] if j >= 0 else 0


# ================================================================== tests
def test_struct_layout_matches_c(lib):
    """El espejo ctypes tiene el mismo tamaño que los structs de C (si no, todo lo demás es inválido)."""
    assert ctypes.sizeof(Cfg) == lib.tl_sizeof_config()
    assert ctypes.sizeof(Inp) == lib.tl_sizeof_inputs()
    assert ctypes.sizeof(Out) == lib.tl_sizeof_outputs()
    assert ctypes.sizeof(Ctx) == lib.tl_sizeof_ctx()


def test_defaults_match_requirements(lib, inp):
    c = default_cfg(lib, calibrated=False)
    assert c.cal_valid == 0                       # sin calibrar no arma
    assert abs(c.deadband - 0.08) < 1e-6          # ±8 % de la carrera
    assert c.ramp_up_ms >= 1000                   # 0→100 % en ≥ 1 s
    assert c.ramp_down_ms < c.ramp_up_ms          # bajada rápida
    assert c.dwell_ms >= 500 and c.arm_hold_ms >= 1000 and c.watchdog_ms == 100
    assert abs(c.reverse_limit - inp["motor"]["reverse_current_frac"]) < 1e-6
    assert (c.ppm_min_us, c.ppm_center_us, c.ppm_max_us) == (1000, 1500, 2000)
    assert abs(c.adc_fault_low * 5.0 / 1023 - 0.3) < 0.01 and abs(c.adc_fault_high * 5.0 / 1023 - 4.7) < 0.01
    import calc_electronica as ce
    assert ce.compute()["vesc_values"]["pulse_us"] == [c.ppm_min_us, c.ppm_center_us, c.ppm_max_us]


def test_uncalibrated_never_arms(lib):
    s = Sim(lib, cfg=default_cfg(lib, calibrated=False))
    o = s.hold(5000, pos=0.0)
    assert o.state == ST["FAULT"] and o.flags & F["CAL"] and is_neutral(o)
    assert all(r["en"] == 0 and r["cmd"] == 0.0 for r in s.trace)


@pytest.mark.parametrize("pos", [0.6, 1.0, -1.0])
def test_power_on_with_throttle_open_does_not_start(lib, pos):
    s = Sim(lib)
    s.step(pos=pos)                               # ya abierto en el primer tick tras encender
    o = s.hold(5000)
    assert o.state == ST["DISARMED"] and o.flags & F["NOT_ZERO"]
    assert all(r["cmd"] == 0.0 and r["ppm"] == 1500 and r["en"] == 0 for r in s.trace)


def test_arms_only_after_1s_continuous_zero(lib):
    s = Sim(lib)
    s.hold(2000, pos=0.7)                         # encendido con el acelerador abierto
    n0 = len(s.trace)
    s.goto(0.0)
    t0 = next(r["t"] for r in s.trace[n0:] if s.in_zero(r["adc"]))
    while s.trace[-1]["state"] != ST["ARMED"]:
        s.step(pos=0.0)
        assert s.t - t0 <= 1000 + DT, "no armó a tiempo"
    held = s.t - t0                               # tiempo entre la 1.ª muestra en cero y el armado
    assert 1000 <= held <= 1000 + DT
    assert all(r["state"] == ST["DISARMED"] for r in s.trace[:-1])
    # Una interrupción a mitad de camino reinicia el conteo
    s = Sim(lib)
    s.hold(500, pos=0.0)
    s.step(pos=0.4)                               # un tick fuera de cero
    for _ in range(99):                           # 99 muestras en cero = 980 ms
        o = s.step(pos=0.0)
    assert o.state == ST["DISARMED"]
    for _ in range(3):
        o = s.step(pos=0.0)
    assert o.state == ST["ARMED"]


def test_ramp_up_limited(lib):
    s = Sim(lib)
    s.arm()
    c = s.cfg
    n0 = len(s.trace)
    s.hold(1500, pos=1.0)
    tr = s.trace[n0:]
    prev = 0.0
    for r in tr:
        assert r["cmd"] - prev <= DT / c.ramp_up_ms + 1e-6 and r["cmd"] >= prev
        prev = r["cmd"]
    i_full = next(i for i, r in enumerate(s.trace) if i >= n0 and r["cmd"] >= 1.0 - 1e-6)
    assert s.trace[i_full]["t"] - last_zero_before(s.trace, i_full) >= 1000
    assert s.trace[-1]["state"] == ST["RUN_FWD"] and s.trace[-1]["ppm"] == 2000


def test_ramp_down_fast(lib):
    s = Sim(lib)
    s.arm()
    s.hold(1500, pos=1.0)
    start = s.t
    s.goto(0.0, ms=30)                            # resortes devuelven el puño en ~30 ms
    while s.trace[-1]["cmd"] > 0.0:
        s.step(pos=0.0)
        assert s.t - start <= s.cfg.ramp_down_ms + 3 * DT
    assert s.t - start < 1000


@pytest.mark.parametrize("which", ["kill", "estop"])
def test_kill_and_estop_cut_same_tick_and_latch(lib, which):
    s = Sim(lib)
    s.arm()
    s.hold(1500, pos=1.0)
    assert s.trace[-1]["cmd"] == pytest.approx(1.0)
    o = s.step(**{which: 0})                      # cordón/seta abiertos con el acelerador a fondo
    assert is_neutral(o) and o.state == ST["DISARMED"]
    flag = F["KILL_CORD"] if which == "kill" else F["ESTOP"]
    assert o.flags & flag
    o = s.hold(3000)                              # vuelve el cordón/seta, acelerador abierto: NO re-arma
    assert is_neutral(o) and o.state == ST["DISARMED"] and o.flags & F["NOT_ZERO"] and o.flags & flag
    o = s.goto(0.0)                               # acelerador a cero: re-arma recién tras ≥ 1 s continuo
    o = s.hold(980)
    assert o.state == ST["DISARMED"] and is_neutral(o)
    o = s.hold(30)
    assert o.state == ST["ARMED"] and o.flags == 0     # el armado limpia el latch


@pytest.mark.parametrize("which", ["kill", "estop"])
def test_power_on_with_cord_or_estop_open_never_arms(lib, which):
    """Encendido con el cordón afuera (o la seta pulsada) y el puño en cero: no arma nunca; al reponerlo
    arma recién tras ≥ arm_hold_ms continuos con todo OK (el tiempo previo en cero no cuenta)."""
    s = Sim(lib)
    o = s.hold(5000, pos=0.0, **{which: 0})
    assert all(r["en"] == 0 and r["cmd"] == 0.0 for r in s.trace) and o.state == ST["DISARMED"]
    o = s.hold(s.cfg.arm_hold_ms - 2 * DT)
    assert o.state == ST["DISARMED"] and is_neutral(o)
    o = s.hold(3 * DT)
    assert o.state == ST["ARMED"]


def test_single_tick_kill_glitch_disarms(lib):
    s = Sim(lib)
    s.arm()
    s.hold(500, pos=0.5)
    o = s.step(kill=0)
    assert is_neutral(o)
    o = s.hold(2000)                              # cordón de vuelta, acelerador abierto
    assert is_neutral(o) and o.state == ST["DISARMED"]


def test_reverse_limited_to_50_percent(lib, inp):
    lim = inp["motor"]["reverse_current_frac"]
    s = Sim(lib)
    s.arm()
    n0 = len(s.trace)
    o = s.hold(3000, pos=-1.0)
    assert o.state == ST["RUN_REV"] and o.flags & F["REV_LIM"]
    assert o.cmd == pytest.approx(-lim, abs=1e-6)
    assert min(r["cmd"] for r in s.trace) >= -lim - 1e-6
    assert o.ppm_us == round(1500 - 500 * lim)
    i_full = next(i for i, r in enumerate(s.trace) if i >= n0 and r["cmd"] <= -lim + 1e-6)
    assert s.trace[i_full]["t"] - last_zero_before(s.trace, i_full) >= lim * s.cfg.ramp_up_ms


@pytest.mark.parametrize("first,second", [(1.0, -1.0), (-1.0, 1.0)])
def test_direction_reversal_requires_dwell(lib, first, second):
    s = Sim(lib)
    s.arm()
    s.hold(2000, pos=first)
    n0 = len(s.trace)
    s.hold(2000, pos=second)                      # inversión del puño tope a tope en 100 ms
    tr = s.trace[n0:]
    sgn = 1 if first > 0 else -1
    t_zero = next(r["t"] for r in tr if r["cmd"] == 0.0)
    t_opp = next(r["t"] for r in tr if r["cmd"] * sgn < 0)
    waiting = [r for r in tr if t_zero <= r["t"] < t_opp]
    assert all(r["cmd"] == 0.0 and r["ppm"] == 1500 for r in waiting)     # en cero todo el dwell
    assert t_opp - t_zero >= s.cfg.dwell_ms
    assert all(r["state"] == ST["DWELL_ZERO"] for r in waiting)
    assert any(r["flags"] & F["DWELL"] for r in waiting)
    assert tr[-1]["state"] == (ST["RUN_REV"] if second < 0 else ST["RUN_FWD"])


def test_slow_sweep_through_zero_still_needs_dwell(lib):
    s = Sim(lib)
    s.arm()
    s.hold(2000, pos=1.0)
    n0 = len(s.trace)
    s.goto(-1.0, ms=300)                          # barrido lineal +1 → −1 en 300 ms
    s.hold(1500)
    tr = s.trace[n0:]
    t_zero = next(r["t"] for r in tr if r["cmd"] == 0.0)
    t_neg = next(r["t"] for r in tr if r["cmd"] < 0.0)
    assert t_neg - t_zero >= s.cfg.dwell_ms


def test_same_direction_reapply_has_no_dwell(lib):
    s = Sim(lib)
    s.arm()
    s.hold(1500, pos=1.0)
    s.goto(0.0, ms=30)
    s.hold(370)                                   # suelta: dwell en curso
    assert s.trace[-1]["state"] == ST["DWELL_ZERO"] and s.trace[-1]["cmd"] == 0.0
    o = s.step(pos=0.3)                           # mismo sentido: sigue de inmediato (con rampa)
    assert o.cmd > 0.0 and o.state == ST["RUN_FWD"]
    o = s.hold(700, pos=0.0)                      # pasado el dwell queda ARMED
    assert o.state == ST["ARMED"]


@pytest.mark.parametrize("adc,flag", [(0, "SENS_LOW"), (30, "SENS_LOW"), (60, "SENS_LOW"),
                                      (963, "SENS_HIGH"), (1000, "SENS_HIGH"), (1023, "SENS_HIGH")])
def test_sensor_open_or_short_gives_neutral_and_fault(lib, adc, flag):
    s = Sim(lib)
    s.arm()
    s.hold(1500, pos=0.8)
    o = s.step(adc=adc)                           # cable de señal/5 V cortado (≈0 V) o corto a 5 V
    assert is_neutral(o) and o.state == ST["FAULT"] and o.flags & F[flag]
    o = s.hold(500, pos=0.0)                      # el sensor vuelve: sigue en FAULT (latch)
    assert o.state == ST["FAULT"] and is_neutral(o)
    o = s.hold(600)                               # re-armado tras ≥ 1 s en cero con sensor sano
    assert o.state == ST["ARMED"]


def test_sensor_band_edges_are_valid(lib):
    c = default_cfg(lib)
    for adc in (c.adc_fault_low, c.adc_fault_high):
        o = Sim(lib).step(adc=adc)
        assert not o.flags & (F["SENS_LOW"] | F["SENS_HIGH"]) and o.state == ST["DISARMED"]


def test_sensor_impossible_jump_is_fault_but_hand_motion_is_not(lib):
    s = Sim(lib)
    s.arm()
    o = s.step(pos=1.0)                           # centro → tope en 10 ms: imposible a mano
    assert o.state == ST["FAULT"] and o.flags & F["SENS_JUMP"] and is_neutral(o)
    s = Sim(lib)
    s.arm()
    s.goto(1.0, ms=150)                           # 0 → 100 % en 150 ms (mano rápida)
    s.hold(200)
    s.goto(0.0, ms=30)                            # 100 % → 0 en 30 ms (resortes de retorno)
    s.goto(-1.0, ms=100)
    assert not any(r["flags"] & F["SENS_JUMP"] for r in s.trace)
    assert all(r["state"] != ST["FAULT"] for r in s.trace)


def test_logic_watchdog(lib):
    s = Sim(lib)
    s.arm()
    s.hold(1500, pos=0.5)
    o = s.step(dt=s.cfg.watchdog_ms)              # justo en el límite: sigue
    assert o.cmd > 0
    o = s.step(dt=s.cfg.watchdog_ms + 1)          # tick tardío → neutro y desarme
    assert is_neutral(o) and o.state == ST["DISARMED"] and o.flags & F["WATCHDOG"]
    s.goto(0.0)                                   # entra a zona muerta 1 tick antes del final
    o = s.hold(970)
    assert o.state == ST["DISARMED"]
    o = s.hold(30)
    assert o.state == ST["ARMED"]
    s = Sim(lib)                                  # un dt enorme en cero no cuenta como "1 s en cero"
    s.hold(200, pos=0.0)
    o = s.step(dt=5000)
    assert o.state == ST["DISARMED"] and o.flags & F["WATCHDOG"]
    o = s.hold(500)
    assert o.state == ST["DISARMED"]


def test_deadband(lib):
    c = default_cfg(lib)
    db = c.deadband
    for pos in (0.0, 0.5 * db, 0.99 * db, -0.99 * db, db, -db):
        assert lib.tl_shape(byref(c), pos) == 0.0
    small = lib.tl_shape(byref(c), db + 0.01)
    assert 0.0 < small < 0.02                     # continuo en el borde de la zona muerta
    assert lib.tl_shape(byref(c), 1.0) == pytest.approx(1.0)
    assert lib.tl_shape(byref(c), -1.0) == pytest.approx(-c.reverse_limit)
    s = Sim(lib)
    o = s.hold(1100, pos=0.9 * db)                # dentro de la zona muerta se puede armar
    assert o.state == ST["ARMED"] and o.cmd == 0.0
    o = s.hold(500)
    assert o.state == ST["ARMED"] and o.cmd == 0.0 and o.ppm_us == 1500
    o = s.hold(500, pos=-0.9 * db)
    assert o.state == ST["ARMED"] and o.cmd == 0.0
    o = s.hold(300, pos=2 * db)                   # fuera de la zona muerta: avanza
    assert o.cmd > 0.0


def test_expo_shape(lib):
    c = default_cfg(lib)
    c.expo = 0.5
    ys = [lib.tl_shape(byref(c), x / 100) for x in range(0, 101)]
    assert all(b >= a for a, b in zip(ys, ys[1:]))
    assert ys[-1] == pytest.approx(1.0)
    lin = default_cfg(lib)
    assert lib.tl_shape(byref(c), 0.55) < lib.tl_shape(byref(lin), 0.55)


def test_calibration_validation(lib):
    c = default_cfg(lib, calibrated=False)
    assert lib.tl_calibrate(byref(c), 500, 512, 520) != 0          # semicarrera muy chica
    assert lib.tl_calibrate(byref(c), 300, 512, 400) != 0          # no monótono
    assert lib.tl_calibrate(byref(c), 40, 512, 760) != 0           # tope dentro de la zona de falla
    assert c.cal_valid == 0
    assert lib.tl_calibrate(byref(c), 760, 512, 260) == 0          # imán invertido: válido
    assert c.cal_valid == 1
    assert lib.tl_position(byref(c), 260) == pytest.approx(1.0)
    assert lib.tl_position(byref(c), 760) == pytest.approx(-1.0)
    s = Sim(lib, cfg=c)
    s.arm()
    o = s.hold(1500, pos=1.0)
    assert o.state == ST["RUN_FWD"] and o.cmd == pytest.approx(1.0) and s.trace[-1]["adc"] == 260


def test_vesc_fault_input(lib):
    c = default_cfg(lib)
    c.use_vesc_ok = 1
    s = Sim(lib, cfg=c)
    s.arm()
    s.hold(1500, pos=0.5)
    o = s.step(vesc=0)
    assert is_neutral(o) and o.state == ST["FAULT"] and o.flags & F["VESC"]
    s = Sim(lib)                                  # sin telemetría: la entrada se ignora
    s.arm()
    o = s.hold(500, pos=0.5, vesc=0)
    assert o.cmd > 0


def test_total_cut_time_below_requirement(lib, inp):
    """Corte < requisito: la lógica responde en el MISMO tick (latencia ≤ 1 tick de 10 ms desde el
    evento) y cada camino físico (calc_electronica) por separado queda bajo el requisito."""
    import calc_electronica as ce
    req = inp["electrical"]["kill_switch_response_s_max"]
    rnd = random.Random(1)
    for _ in range(30):
        s = Sim(lib)
        s.arm()
        s.hold(rnd.randint(1200, 2500), pos=rnd.choice([1.0, 0.5, -1.0]))
        assert s.trace[-1]["cmd"] != 0.0
        which = rnd.choice(["kill", "estop"])
        o = s.step(**{which: 0})                  # el evento ocurrió dentro de este intervalo de tick
        assert is_neutral(o)                      # → latencia de la lógica ≤ DT
    assert DT <= 20
    R = ce.compute()
    for name, p in R["corte"]["caminos"].items():
        assert p["t_s"] < req, name
    vv = R["vesc_values"]
    assert DT / 1000 + 0.020 + vv["ramp_time_neg"] < req     # tick + trama PPM + rampa negativa del VESC


def test_fuzz_invariants(lib):
    """20 000 ticks aleatorios (glitches, kill, seta, dt tardíos): invariantes de seguridad."""
    rnd = random.Random(42)
    s = Sim(lib)
    c = s.cfg
    pos, seg_left, mode, last_sign, zero_since = 0.0, 0, "rest", 0, None

    for i in range(20000):
        if seg_left <= 0:                         # segmentos: descanso en cero, manejo, golpes de puño
            mode = rnd.choice(["rest", "rest", "ride", "ride", "snap"])
            seg_left = rnd.randint(50, 250)
        seg_left -= 1
        if mode == "rest":
            pos = max(-0.07, min(0.07, pos * 0.5 + rnd.uniform(-0.01, 0.01)))
        elif mode == "ride":
            pos = max(-1.0, min(1.0, pos + rnd.uniform(-0.05, 0.05)))
        elif rnd.random() < 0.05:
            pos = rnd.choice([-1.0, -0.5, 0.0, 0.3, 1.0])              # a veces "imposible" → FAULT
        adc = s.adc(pos)
        if rnd.random() < 0.001:
            adc = rnd.choice([0, 20, 1010, 1023, rnd.randint(0, 1023)])
        kill = 0 if rnd.random() < 0.001 else 1
        estop = 0 if rnd.random() < 0.0005 else 1
        dt = DT if rnd.random() > 0.004 else rnd.choice([0, 1, 25, c.watchdog_ms, c.watchdog_ms + 1, 400])
        prev_cmd = s.trace[-1]["cmd"] if s.trace else 0.0
        o = s.step(adc=adc, kill=kill, estop=estop, dt=dt)
        assert 1000 <= o.ppm_us <= 2000
        assert (o.ppm_us == 1500) == (o.cmd == 0.0) or abs(o.cmd) < 0.002
        assert o.cmd >= -c.reverse_limit - 1e-6
        unsafe = (not kill or not estop or dt > c.watchdog_ms or adc < c.adc_fault_low or adc > c.adc_fault_high)
        if unsafe:
            assert is_neutral(o) and o.state in (ST["DISARMED"], ST["FAULT"]), i
        assert (o.enable == 1) == (o.state in ARMED_STATES)
        if abs(o.cmd) > abs(prev_cmd) and o.cmd * prev_cmd >= 0:
            assert abs(o.cmd) - abs(prev_cmd) <= dt / c.ramp_up_ms + 1e-5, i
        if o.cmd == 0.0:                          # inversión: ≥ dwell en cero entre signos opuestos
            zero_since = s.t if zero_since is None else zero_since
        else:
            sg = 1 if o.cmd > 0 else -1
            if last_sign and sg != last_sign:
                assert zero_since is not None and s.t - zero_since >= c.dwell_ms, i
            last_sign, zero_since = sg, None
    # cada armado fue precedido por ≥ arm_hold_ms de muestras con todo OK y acelerador en zona muerta
    tr = s.trace

    def ok(r):
        return (r["kill"] and r["estop"] and r["dt"] <= c.watchdog_ms and
                c.adc_fault_low <= r["adc"] <= c.adc_fault_high and s.in_zero(r["adc"]))

    n_arm = 0
    for k in range(1, len(tr)):
        if tr[k]["state"] in ARMED_STATES and tr[k - 1]["state"] not in ARMED_STATES:
            n_arm += 1
            j = k
            while j - 1 >= 0 and ok(tr[j - 1]):
                j -= 1
            assert ok(tr[k]) and tr[k]["t"] - tr[j]["t"] >= c.arm_hold_ms, k
    assert n_arm >= 5                             # el fuzz efectivamente re-armó varias veces


def test_truth_table_only_all_ok_runs():
    import calc_electronica as ce
    tt = ce.truth_table()
    assert len(tt) == 2 ** 8 * 3
    runs = [r for r in tt if r["motor"] != "PARADO"]
    assert len(runs) == 2 and {r["K1"] for r in runs} == {"normal", "soldado"}
    for r in runs:
        assert (r["cordon"], r["seta"], r["desconectador"], r["F1"], r["F2"], r["MCU_armado"],
                r["timeout_VESC"], r["falla_sensor"]) == (1, 1, 1, 1, 1, 1, 0, 0)
    for r in tt:
        if r["cordon"] == 0 or r["seta"] == 0:
            assert r["motor"] == "PARADO" and r["n_barreras"] >= 1
            if r["MCU_coherente"] and r["K1"] == "normal" and r["desconectador"] and r["F1"]:
                assert r["n_barreras"] >= 3      # contactor + kill ADC2 + MCU neutro
    nominal = {v[0]: v[2] for v in ce.VARS}
    for name, values, ok in ce.VARS:          # cualquier desvío único del estado nominal para el motor
        for v in values:
            if v == ok or (name == "K1" and v == "soldado"):
                continue
            d = dict(nominal, **{name: v})
            assert ce.chain(**d)["motor"] == "PARADO", (name, v)


def test_sketch_uses_identical_logic_copy_and_required_io():
    for f in ("throttle_logic.c", "throttle_logic.h"):
        assert (FW / f).read_bytes() == (FW / "p1_throttle" / "src" / f).read_bytes(), \
            f"copiar firmware/{f} a firmware/p1_throttle/src/"
    ino = (FW / "p1_throttle" / "p1_throttle.ino").read_text(encoding="utf-8")
    for needle in ("WDTO_120MS", "PIN_HALL = A0", "PIN_KILL = 2", "PIN_ESTOP = 3", "PIN_PPM = 9",
                   "INPUT_PULLUP", "tl_tick(", "ISR(INT0_vect)", "ISR(INT1_vect)", "wdt_reset()"):
        assert needle in ino, needle
    assert ino.count("wdt_reset();") == 1         # una sola llamada: solo tras un tick completo
    # con -flto, una función en .init3 sin `used` se descarta (nadie la llama): el WDT no se apagaría
    m = re.search(r"void p1_early_init\(void\)([^;]*);", ino)
    assert m and "used" in m.group(1) and ".init3" in m.group(1), "p1_early_init necesita __attribute__((used))"


def test_avr_build_if_toolchain_available(tmp_path):
    """Compila para ATmega328P si hay avr-gcc o arduino-cli (P1_ARDUINO_CLI=ruta); si no, se salta."""
    import os
    cli = os.environ.get("P1_ARDUINO_CLI") or shutil.which("arduino-cli")
    avr = shutil.which("avr-gcc")
    if not cli and not avr:
        pytest.skip("sin toolchain AVR (avr-gcc / arduino-cli)")
    if avr:
        r = subprocess.run([avr, "-mmcu=atmega328p", "-std=c99", "-Os", "-Wall", "-Wextra", "-Werror", "-c",
                            str(SRC_C), "-o", str(tmp_path / "tl.o")], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
    if cli:
        bp = tmp_path / "b"
        r = subprocess.run([cli, "compile", "--fqbn", "arduino:avr:nano", "--build-path", str(bp),
                            str(FW / "p1_throttle")], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        # p1_early_init sobrevivió a LTO: el ELF lee MCUSR (I/O 0x34) dentro de .init3, antes de main
        pr = subprocess.run([cli, "compile", "--fqbn", "arduino:avr:nano", "--show-properties", str(FW / "p1_throttle")],
                            capture_output=True, text=True)
        tool = re.search(r"^runtime\.tools\.avr-gcc\.path=(.+)$", pr.stdout, re.M)
        objdump = Path(tool.group(1).strip()) / "bin" / "avr-objdump" if tool else None
        if objdump and objdump.exists():
            dis = subprocess.run([str(objdump), "-d", str(bp / "p1_throttle.ino.elf")], capture_output=True, text=True).stdout
            init = dis.split("<__do_copy_data>:")[0]
            assert re.search(r"<_Z13p1_early_initv>:", init) and re.search(r"\bin\s+r\d+, 0x34", init), \
                "p1_early_init no está en .init3 del ELF (LTO la descartó)"


def test_vesc_config_consistent_with_sizing(inp, sizing):
    import calc_electronica as ce
    vv = ce.compute()["vesc_values"]
    assert vv["l_current_max"] == inp["motor"]["current_limit_a"]
    assert vv["l_current_min"] == pytest.approx(-inp["motor"]["reverse_current_frac"] * vv["l_current_max"])
    assert vv["l_in_current_max"] <= 0.8 * vv["i_bms"] + 1e-9
    assert vv["i_in_limited"] or vv["l_in_current_max"] >= sizing["esc"]["I_bat_peak_a"]
    assert vv["l_battery_cut_start"] > vv["l_battery_cut_end"]
    pp = vv["motor_poles"] / 2
    assert vv["n_max_loaded_rpm"] < vv["l_max_erpm"] / pp < vv["n_noload_rpm"]
    assert vv["n_rev_bollard_rpm"] < -vv["l_min_erpm"] / pp
    assert vv["timeout_msec"] / 1000 < inp["electrical"]["kill_switch_response_s_max"]
    sel = sizing["selection"]["motor"]
    mot = inp["motor"]["options"][sel]
    assert vv["motor_poles"] == 2 * mot["pole_pairs"]                  # inputs.yaml es la única fuente
    assert vv["l_temp_motor_start"] <= mot["t_winding_max_c"]          # el VESC limita desde t_winding_max de sizing


def test_circuit_findings_are_reflected():
    """Sobretensión de bobina y tensión inversa en los LED de los optos: si el cálculo las detecta,
    la lista de componentes las exige (no basta con calcularlas)."""
    import calc_electronica as ce
    R = ce.compute()
    comp = ce.blocks(R)["componentes"]
    if R["optos"]["necesita_diodo_antiparalelo"]:
        assert "D_U1–D_U3" in comp and "1N4148" in comp
    o24 = R["bobina"]["opciones"][f"{R['bobina']['V_nom']:.0f}"]
    if not o24["P_vmax_le_prolonged"]:
        assert "CONTINUOS" in comp                                     # K1: bobina apta para V_máx continua
    sk = ce.sketch_consts()
    assert sk["tick_ms"] == DT and sk["ppm_frame_ms"] == 20.0


def test_generated_files_are_current(tmp_path):
    """README (bloques ELEC), electronica.json, tabla_verdad.csv y el SVG coinciden con lo que generan hoy
    calc_electronica.py y diagrama_cableado.py a partir de inputs.yaml + sizing.json (no quedaron viejos)."""
    import calc_electronica as ce
    import diagrama_cableado as dc
    assert ce.main(["--check"]) == 0, "correr: python 04_diseno/electronica/calc_electronica.py"
    out = dc.build(tmp_path / "d.svg")
    assert out.read_bytes() == (ELEC / "diagrama_cableado.svg").read_bytes(), \
        "correr: python 04_diseno/electronica/diagrama_cableado.py"


def test_wiring_diagram_generates(tmp_path, sizing):
    import diagrama_cableado as dc
    out = dc.build(tmp_path / "d.svg")
    doc = xml.dom.minidom.parse(str(out))
    texts = " ".join(t.firstChild.nodeValue for t in doc.getElementsByTagName("text") if t.firstChild)
    for needle in ("F1", "S1 desconectador", "K1 contactor", "R_pre", "CORDÓN", "SETA", "F2", "Bobina K1",
                   "DC-DC", "Arduino Nano", "Sensor hall", "J1 IP68", "ADC2", "PPM", "Q_EN", "BAT−", "CASCO",
                   "ISO 13297", "≤ 178 mm"):
        assert needle in texts, needle
    assert f"F1 {sizing['fuse']['rating_a']:.0f} A" in texts
