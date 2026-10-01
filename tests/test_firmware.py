"""Tests de la lógica del acelerador del waterjet de P1 (04_diseno/electronica/firmware/throttle_logic.c).

Compila throttle_logic.c con gcc (C99 estricto, -Werror) a una librería compartida en un directorio
temporal y la ejecuta desde Python vía ctypes, tick a tick (banco de pruebas `Sim`). Los estados/flags
se leen del header (no se duplican aquí); los requisitos (tiempo de corte, límite con el bucket abajo,
l_min_erpm de la limpieza de rejilla) se leen de inputs.yaml / calc_electronica.py.

Waterjet: la marcha atrás es el BUCKET; el motor gira siempre en avance (comando >= 0) salvo en la
limpieza de rejilla (pulsador, acelerador en 0, <= 3 s, |comando| <= weed_cmd).
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
                                               "TL_DWELL_ZERO", "TL_FAULT", "TL_WEED")}
ARMED_STATES = {ST["ARMED"], ST["RUN_FWD"], ST["RUN_REV"], ST["DWELL_ZERO"], ST["WEED"]}
F = {k[5:]: v for k, v in D.items() if k.startswith("TL_F_")}
COAST, OPEN = D["TL_PROF_COAST"], D["TL_PROF_OPEN"]


# ------------------------------------------------------------------ espejo ctypes de los structs
class Cfg(ctypes.Structure):
    _fields_ = [("deadband", c_float), ("expo", c_float), ("reverse_limit", c_float), ("jump_travel_per_s", c_float),
                ("weed_cmd", c_float),
                ("adc_rev", c_uint16), ("adc_center", c_uint16), ("adc_fwd", c_uint16), ("adc_fault_low", c_uint16),
                ("adc_fault_high", c_uint16), ("min_half_span", c_uint16), ("jump_noise_counts", c_uint16),
                ("arm_hold_ms", c_uint16), ("ramp_up_ms", c_uint16), ("ramp_down_ms", c_uint16),
                ("dwell_ms", c_uint16), ("watchdog_ms", c_uint16), ("ppm_min_us", c_uint16),
                ("ppm_center_us", c_uint16), ("ppm_max_us", c_uint16), ("weed_max_ms", c_uint16),
                ("weed_hold_ms", c_uint16), ("sw_debounce_ms", c_uint16), ("cal_valid", c_uint8), ("use_vesc_ok", c_uint8)]


class Inp(ctypes.Structure):
    _fields_ = [("adc", c_uint16), ("kill_cord_ok", c_uint8), ("estop_ok", c_uint8), ("vesc_ok", c_uint8),
                ("bucket_up", c_uint8), ("sel_open", c_uint8), ("weed_btn", c_uint8)]


class Out(ctypes.Structure):
    _fields_ = [("cmd", c_float), ("target", c_float), ("flags", c_uint32), ("ppm_us", c_uint16),
                ("state", c_uint8), ("enable", c_uint8), ("profile", c_uint8), ("_pad", c_uint8 * 3)]


class Ctx(ctypes.Structure):
    _fields_ = [("cfg", Cfg), ("last", Out), ("out", c_float), ("uptime_ms", c_uint32), ("arm_ms", c_uint32),
                ("zero_ms", c_uint32), ("latched", c_uint32), ("bkt_up_ms", c_uint32), ("sel_ms", c_uint32),
                ("weed_press_ms", c_uint32), ("weed_ms", c_uint32), ("prev_adc", c_uint16), ("prev_valid", c_uint8),
                ("armed", c_uint8), ("arm_run", c_uint8), ("zero_run", c_uint8), ("last_dir", c_int8),
                ("cfg_err", c_uint8), ("bkt_down", c_uint8), ("bkt_up_run", c_uint8), ("bkt_hold", c_uint8),
                ("sel_db", c_uint8), ("sel_run", c_uint8), ("sel_ready", c_uint8), ("profile", c_uint8),
                ("weed_run", c_uint8), ("weed_ready", c_uint8), ("weed_press_run", c_uint8), ("_pad", c_uint8 * 2)]


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
    L.tl_thrust.argtypes = [POINTER(Cfg), c_float, c_uint8]
    L.tl_thrust.restype = c_float
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


def vesc_values():
    import calc_electronica as ce
    return ce.compute()["vesc_values"]


class Sim:
    """Banco de pruebas: llama tl_tick con dt fijo y guarda la traza.
    Los movimientos grandes de la palanca se hacen con goto() (mano real, 100 ms): un salto instantáneo
    centro→tope es físicamente imposible y el detector de saltos lo marca como falla (test aparte).
    Entradas persistentes (se cambian asignando el atributo): bucket (1 = fin de carrera cerrado =
    ARRIBA), sel (1 = selector en ABIERTO), weed (1 = pulsador de rejilla apretado)."""

    def __init__(self, L, cfg=None, dt=DT, bucket=1, sel=0, weed=0):
        self.L, self.dt, self.t, self.pos = L, dt, 0, 0.0
        self.bucket, self.sel, self.weed = bucket, sel, weed
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

    def step(self, adc=None, pos=None, kill=1, estop=1, vesc=1, bucket=None, sel=None, weed=None, dt=None):
        if adc is None:
            if pos is not None:
                self.pos = pos
            adc = self.adc(self.pos)
        dt = self.dt if dt is None else dt
        bucket = self.bucket if bucket is None else bucket
        sel = self.sel if sel is None else sel
        weed = self.weed if weed is None else weed
        o = self.L.tl_tick(byref(self.ctx), byref(Inp(adc, kill, estop, vesc, bucket, sel, weed)), dt)
        self.t += dt
        self.trace.append(dict(t=self.t, adc=adc, kill=kill, estop=estop, dt=dt, cmd=o.cmd, ppm=o.ppm_us,
                               state=o.state, flags=o.flags, en=o.enable, target=o.target, prof=o.profile,
                               bucket=bucket, sel=sel, weed=weed))
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

    def since(self, n0):
        return self.trace[n0:]


def is_neutral(o):
    return o.cmd == 0.0 and o.ppm_us == 1500 and o.enable == 0


def last_zero_before(trace, idx):
    """Tiempo del último tick con cmd == 0 antes del índice idx."""
    j = idx
    while j >= 0 and trace[j]["cmd"] != 0.0:
        j -= 1
    return trace[j]["t"] if j >= 0 else 0


def runs(trace, pred):
    """Tramos consecutivos [i0, i1] de la traza donde pred(r) es verdadero."""
    out, i0 = [], None
    for i, r in enumerate(trace):
        if pred(r) and i0 is None:
            i0 = i
        elif not pred(r) and i0 is not None:
            out.append((i0, i - 1))
            i0 = None
    if i0 is not None:
        out.append((i0, len(trace) - 1))
    return out


# ================================================================== estructura y configuración
def test_struct_layout_matches_c(lib):
    """El espejo ctypes tiene el mismo tamaño que los structs de C (si no, todo lo demás es inválido)."""
    assert ctypes.sizeof(Cfg) == lib.tl_sizeof_config()
    assert ctypes.sizeof(Inp) == lib.tl_sizeof_inputs()
    assert ctypes.sizeof(Out) == lib.tl_sizeof_outputs()
    assert ctypes.sizeof(Ctx) == lib.tl_sizeof_ctx()


def test_defaults_match_requirements(lib, inp, sizing):
    c = default_cfg(lib, calibrated=False)
    assert c.cal_valid == 0                       # sin calibrar no arma
    assert abs(c.deadband - 0.08) < 1e-6          # ±8 % de la carrera
    assert c.ramp_up_ms >= 1000                   # 0→100 % en ≥ 1 s
    assert c.ramp_down_ms < c.ramp_up_ms          # bajada rápida
    assert c.dwell_ms >= 500 and c.arm_hold_ms >= 1000 and c.watchdog_ms == 100
    assert (c.ppm_min_us, c.ppm_center_us, c.ppm_max_us) == (1000, 1500, 2000)
    assert abs(c.adc_fault_low * 5.0 / 1023 - 0.3) < 0.01 and abs(c.adc_fault_high * 5.0 / 1023 - 4.7) < 0.01
    vv = vesc_values()
    assert vv["pulse_us"] == [c.ppm_min_us, c.ppm_center_us, c.ppm_max_us]
    # bucket abajo: límite = P_frac^(2/3) de calc_electronica (bomba P ∝ T^1,5)
    p_rev = inp["waterjet"]["reverse"]["power_limit_frac"]
    assert vv["reverse_current_frac"] == pytest.approx(p_rev ** (2 / 3))
    assert c.reverse_limit == pytest.approx(vv["reverse_current_frac"], abs=0.005)
    # limpieza de rejilla: ≤ 3 s, comando chico, pulsación sostenida; la velocidad la topea el VESC
    assert 0 < c.weed_max_ms <= 3000 and c.weed_max_ms <= D["TL_WEED_MAX_MS_LIMIT"]
    assert 0.0 < c.weed_cmd <= 0.15
    assert c.weed_hold_ms >= 200 and c.sw_debounce_ms <= 100
    pp = vv["motor_poles"] / 2
    assert vv["l_min_erpm"] < 0 and -vv["l_min_erpm"] < 0.5 * vv["l_max_erpm"]       # giro inverso LENTO
    assert -vv["l_min_erpm"] / pp == pytest.approx(vv["n_rev_weed_rpm"], abs=50 / pp + 1e-9)
    assert vv["n_rev_weed_rpm"] <= 0.25 * sizing["legal_speed"]["n_legal_rpm"] + 1e-6


@pytest.mark.parametrize("field,value", [("weed_max_ms", 3001), ("weed_cmd", 0.3), ("weed_cmd", -0.1),
                                         ("weed_hold_ms", 0), ("reverse_limit", 0.0), ("reverse_limit", 1.2),
                                         ("sw_debounce_ms", 2000)])
def test_config_check_rejects_unsafe_params(lib, field, value):
    c = default_cfg(lib)
    setattr(c, field, value)
    assert lib.tl_config_check(byref(c)) & D["TL_CFG_ERR_PARAM"]
    s = Sim(lib, cfg=c)                           # con la config inválida no arma nunca
    o = s.hold(3000, pos=0.0)
    assert o.state == ST["FAULT"] and o.flags & F["CAL"] and is_neutral(o)


def test_uncalibrated_never_arms(lib):
    s = Sim(lib, cfg=default_cfg(lib, calibrated=False), sel=1)
    o = s.hold(5000, pos=0.0)
    assert o.state == ST["FAULT"] and o.flags & F["CAL"] and is_neutral(o)
    assert all(r["en"] == 0 and r["cmd"] == 0.0 and r["prof"] == COAST for r in s.trace)


# ================================================================== armado, rampa, kill
@pytest.mark.parametrize("pos,bucket", [(0.6, 1), (1.0, 1), (-1.0, 0), (0.5, 0)])
def test_power_on_with_throttle_open_does_not_start(lib, pos, bucket):
    s = Sim(lib, bucket=bucket)
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
    s.goto(0.0, ms=30)                            # resortes devuelven la palanca en ~30 ms
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
    """Encendido con el cordón afuera (o la seta pulsada) y la palanca en cero: no arma nunca; al reponerlo
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


# ================================================================== bucket (marcha atrás)
def test_bucket_down_limits_output(lib):
    """Bucket abajo + palanca a tope atrás: el motor gira en AVANCE con comando = reverse_limit."""
    s = Sim(lib)
    s.arm()
    rl = s.cfg.reverse_limit
    s.bucket = 0                                  # palanca del bucket abajo (acelerador en 0)
    o = s.hold(200)
    assert o.state == ST["ARMED"] and o.flags & F["BKT_DOWN"] and not o.flags & F["BKT_HOLD"]
    n0 = len(s.trace)
    o = s.hold(3000, pos=-1.0)
    assert o.state == ST["RUN_REV"] and o.flags & F["BKT_LIM"] and not o.flags & F["BKT_MISM"]
    assert o.cmd == pytest.approx(rl, abs=1e-6) and o.ppm_us == round(1500 + 500 * rl)
    tr = s.since(n0)
    assert all(0.0 <= r["cmd"] <= rl + 1e-6 for r in tr)                    # nunca negativo, nunca > límite
    i_full = next(i for i, r in enumerate(s.trace) if i >= n0 and r["cmd"] >= rl - 1e-6)
    assert s.trace[i_full]["t"] - last_zero_before(s.trace, i_full) >= rl * s.cfg.ramp_up_ms  # con rampa
    # a mitad de recorrido: proporcional y limitado
    o = s.hold(500, pos=-0.5)
    assert o.cmd == pytest.approx(rl * lib.tl_shape(byref(s.cfg), 0.5), abs=1e-4)


def test_bucket_switch_open_at_power_on_limits_forward_too(lib):
    """Fin de carrera abierto (cable cortado) desde el encendido: se arma, pero el avance queda limitado
    (fail-safe) y se marca la incoherencia palanca/fin de carrera."""
    s = Sim(lib, bucket=0)
    s.arm()
    o = s.hold(3000, pos=1.0)
    assert o.cmd == pytest.approx(s.cfg.reverse_limit, abs=1e-6) and o.state == ST["RUN_REV"]
    assert o.flags & F["BKT_MISM"] and o.flags & F["BKT_LIM"]
    assert max(r["cmd"] for r in s.trace) <= s.cfg.reverse_limit + 1e-6


def test_reverse_side_with_bucket_up_gives_zero(lib):
    """Palanca del lado de reversa con el fin de carrera en ARRIBA (enclavamiento roto o fin de carrera
    pegado): sin empuje (el bote iría hacia adelante cuando se pide atrás)."""
    s = Sim(lib)
    s.arm()
    o = s.hold(2000, pos=-1.0)
    assert o.cmd == 0.0 and o.enable == 1 and o.flags & F["BKT_MISM"] and o.state == ST["ARMED"]
    assert all(r["cmd"] == 0.0 for r in s.trace)


def test_never_reverse_rotation_without_weed_button(lib):
    """Sin el pulsador de rejilla el comando nunca es negativo, con cualquier palanca y bucket."""
    for bucket in (1, 0):
        s = Sim(lib, bucket=bucket)
        s.arm()
        for p in (1.0, -1.0, 0.0, -0.5, 0.7, -1.0, 0.0, 1.0, -1.0):
            s.goto(p, ms=150)
            s.hold(600)
        assert min(r["cmd"] for r in s.trace) >= 0.0
        assert all(r["state"] != ST["WEED"] for r in s.trace)


def test_bucket_down_is_immediate_up_needs_debounce(lib):
    s = Sim(lib)
    s.arm()
    deb = s.cfg.sw_debounce_ms
    o = s.step(bucket=0)                          # contacto abierto: ABAJO en el mismo tick
    assert o.flags & F["BKT_DOWN"]
    for k in range(41):                           # rebote 10 ms abierto / 10 ms cerrado: sigue ABAJO
        o = s.step(bucket=k % 2)
        assert o.flags & F["BKT_DOWN"]
    s.bucket = 1
    t0 = s.t + DT                                 # primera muestra cerrada
    while s.step().flags & F["BKT_DOWN"]:
        assert s.t - t0 <= deb + DT
    assert s.t - t0 >= deb


@pytest.mark.parametrize("start_bucket,lever", [(1, 0.6), (0, -0.6), (0, 0.6)])
def test_bucket_transition_with_throttle_open_holds_zero(lib, start_bucket, lever):
    """Si el fin de carrera cambia con el acelerador fuera de cero (falla de cable/enclavamiento, o el
    bucket llegando tarde): salida 0 en ese tick y hasta que el acelerador vuelva a cero."""
    s = Sim(lib, bucket=start_bucket)
    s.arm()
    s.hold(1500, pos=lever)
    assert s.trace[-1]["cmd"] > 0.0
    s.bucket = 1 - start_bucket
    n0 = len(s.trace)
    while True:                                   # hacia ARRIBA hay antirrebote: buscar el tick del cambio
        o = s.step()
        if bool(o.flags & F["BKT_DOWN"]) != bool(start_bucket == 0):
            break
        assert s.t - s.trace[n0]["t"] <= s.cfg.sw_debounce_ms + DT
    assert o.cmd == 0.0 and o.enable == 1 and o.flags & F["BKT_HOLD"]   # mismo tick, sin rampa
    n_tr = len(s.trace) - 1
    o = s.hold(2000)                              # acelerador sigue abierto: sigue en 0
    assert all(r["cmd"] == 0.0 and r["en"] == 1 for r in s.since(n_tr))
    assert o.flags & F["BKT_HOLD"]
    o = s.goto(0.0)                               # vuelve a cero: se libera
    assert not o.flags & F["BKT_HOLD"] and o.state in ARMED_STATES
    o = s.hold(1500, pos=abs(lever))              # y vuelve a responder (limitado si quedó abajo)
    expect = lib.tl_thrust(byref(s.cfg), abs(lever), 1 if start_bucket == 1 else 0)
    assert o.cmd == pytest.approx(expect, abs=1e-4) and o.cmd > 0.0


def test_bucket_change_with_throttle_at_zero_no_hold(lib):
    s = Sim(lib)
    s.arm()
    for b in (0, 1, 0):
        s.bucket = b
        s.hold(200)
    o = s.hold(1500, pos=-0.8)
    assert o.cmd > 0.0 and o.state == ST["RUN_REV"]
    assert not any(r["flags"] & F["BKT_HOLD"] for r in s.trace)


def test_bucket_lowered_while_output_ramping_down_is_clamped(lib):
    s = Sim(lib)
    s.arm()
    s.hold(1500, pos=1.0)
    s.goto(0.0, ms=30)                            # suelta: la salida baja por rampa (250 ms)
    assert s.trace[-1]["cmd"] > s.cfg.reverse_limit
    o = s.step(bucket=0)                          # baja el bucket enseguida (el enclavamiento lo permite)
    assert 0.0 < o.cmd <= s.cfg.reverse_limit + 1e-6


# ================================================================== limpieza de rejilla
def test_weed_clear_slow_reverse_limited_in_time(lib):
    s = Sim(lib)
    s.arm()
    c = s.cfg
    n0 = len(s.trace)
    t_press = s.t + DT
    s.weed = 1
    s.hold(6000)                                  # pulsador sostenido 6 s
    tr = s.since(n0)
    neg = runs(tr, lambda r: r["cmd"] < 0.0)
    assert len(neg) == 1, "una sola limpieza por pulsación"
    i0, i1 = neg[0]
    assert tr[i0]["t"] - t_press >= c.weed_hold_ms                     # pulsación sostenida
    assert (i1 - i0 + 1) * DT <= c.weed_max_ms                         # ≤ 3 s de giro inverso
    assert tr[i1]["t"] - tr[i0]["t"] >= c.weed_max_ms - 3 * DT          # y dura lo pedido
    assert all(-c.weed_cmd - 1e-6 <= r["cmd"] for r in tr)              # |comando| ≤ weed_cmd
    assert all(r["state"] == ST["WEED"] and r["flags"] & F["WEED"] for r in tr[i0:i1 + 1])
    assert min(r["ppm"] for r in tr) == round(1500 - 500 * c.weed_cmd)
    assert all(r["cmd"] == 0.0 for r in tr[i1 + 1:])                   # terminó: no re-arranca sostenido
    s.weed = 0                                    # soltar y volver a apretar: otra limpieza
    s.hold(100)
    n1 = len(s.trace)
    s.weed = 1
    s.hold(1000)
    assert any(r["cmd"] < 0.0 for r in s.since(n1))
    s.weed = 0                                    # soltar corta en el mismo tick
    o = s.step()
    assert o.cmd == 0.0 and o.state == ST["DWELL_ZERO"]


def test_weed_requires_throttle_zero_and_motor_stopped(lib):
    s = Sim(lib)
    s.arm()
    c = s.cfg
    s.hold(1000, pos=0.5)                         # avanzando
    n0 = len(s.trace)
    s.weed = 1
    o = s.hold(1000)                              # pulsador con el acelerador abierto: nada
    assert all(r["cmd"] > 0.0 for r in s.since(n0)) and o.flags & F["WEED_WAIT"]
    s.goto(0.0, ms=30)
    s.hold(4500)                                  # acelerador a 0 y pulsador sostenido
    tr = s.since(n0)
    i_neg = next(i for i, r in enumerate(tr) if r["cmd"] < 0.0)
    i_zero = next(i for i, r in enumerate(tr) if r["cmd"] == 0.0)
    assert tr[i_neg]["t"] - tr[i_zero]["t"] >= c.dwell_ms             # motor parado ≥ dwell antes de invertir
    assert all(s.in_zero(r["adc"]) for r in tr[i_neg:] if r["cmd"] < 0.0)
    (j0, j1), = runs(tr, lambda r: r["cmd"] < 0.0)                     # la ventana de 3 s cuenta desde que
    assert tr[j1]["t"] - tr[j0]["t"] >= c.weed_max_ms - 3 * DT          # gira al revés, no durante el dwell
    assert not any(r["state"] == ST["WEED"] for r in tr[:j0])


@pytest.mark.parametrize("case", ["reverse_side_bucket_up", "bucket_hold"])
def test_weed_never_starts_with_lever_off_zero_even_if_output_is_zero(lib, case):
    """Salida en 0 pero palanca fuera de cero (lado de reversa con el bucket arriba, o retención por
    cambio de bucket): el pulsador no invierte el giro."""
    s = Sim(lib)
    s.arm()
    if case == "reverse_side_bucket_up":
        s.hold(1000, pos=-0.6)
    else:
        s.hold(1500, pos=0.6)
        s.bucket = 0
        s.hold(1000)
        assert s.trace[-1]["flags"] & F["BKT_HOLD"]
    assert s.trace[-1]["cmd"] == 0.0
    n0 = len(s.trace)
    s.weed = 1
    o = s.hold(2000)
    assert all(r["cmd"] >= 0.0 for r in s.since(n0)) and o.flags & F["WEED_WAIT"]


def test_weed_aborts_when_throttle_moves_and_forward_waits_dwell(lib):
    s = Sim(lib)
    s.arm()
    s.weed = 1
    s.hold(1000)
    assert s.trace[-1]["cmd"] < 0.0
    n0 = len(s.trace)
    s.goto(0.6)                                   # mueve el acelerador durante la limpieza
    tr = s.since(n0)
    i_out = next(i for i, r in enumerate(tr) if not s.in_zero(r["adc"]))
    assert tr[i_out]["cmd"] == 0.0 and all(r["cmd"] >= 0.0 for r in tr[i_out:])   # corte inmediato
    s.hold(1500)
    tr = s.since(n0)
    t_pos = next(r["t"] for r in tr if r["cmd"] > 0.0)
    assert t_pos - tr[i_out]["t"] >= s.cfg.dwell_ms - DT                # avance recién tras el dwell
    assert all(r["cmd"] >= 0.0 for r in tr[i_out:])                     # sostener el pulsador no re-invierte


def test_weed_short_press_and_bounce_ignored(lib):
    s = Sim(lib)
    s.arm()
    s.weed = 1
    s.hold(s.cfg.weed_hold_ms - 2 * DT)           # pulsación corta
    s.weed = 0
    s.hold(200)
    for k in range(100):                          # rebote/golpes 10 ms on/off durante 1 s
        s.step(weed=k % 2)
    assert all(r["cmd"] >= 0.0 for r in s.trace)


def test_weed_button_held_at_arming_is_ignored(lib):
    """Pulsador apretado (o en corto) desde el encendido: no hace nada hasta soltarlo y volver a apretar."""
    s = Sim(lib, weed=1)
    s.arm()
    s.hold(3000)
    assert all(r["cmd"] == 0.0 for r in s.trace)
    s.weed = 0
    s.hold(100)
    s.weed = 1
    s.hold(600)
    assert any(r["cmd"] < 0.0 for r in s.trace)


def test_weed_cut_by_kill_and_not_resumed(lib):
    s = Sim(lib)
    s.arm()
    s.weed = 1
    s.hold(800)
    assert s.trace[-1]["cmd"] < 0.0
    o = s.step(kill=0)
    assert is_neutral(o) and o.state == ST["DISARMED"]
    o = s.hold(1500)                              # re-arma con el pulsador todavía apretado: no invierte
    assert o.state == ST["ARMED"] and all(r["cmd"] == 0.0 for r in s.trace[-150:])


# ================================================================== perfil costa / abierto
@pytest.mark.parametrize("sel_at_power_on", [0, 1])
def test_profile_coast_by_default_at_power_on(lib, sel_at_power_on):
    s = Sim(lib, sel=sel_at_power_on)
    s.arm()
    o = s.hold(2000)
    assert all(r["prof"] == COAST for r in s.trace)                    # COSTA aunque el selector diga abierto
    assert bool(o.flags & F["PROF_WAIT"]) == bool(sel_at_power_on)
    s.sel = 0                                     # pasar el selector por costa → abierto
    s.hold(100)
    s.sel = 1
    o = s.hold(100)
    assert o.profile == OPEN and o.flags & F["PROF_OPEN"] and not o.flags & F["PROF_WAIT"]


def test_profile_open_needs_throttle_zero_and_coast_is_immediate(lib):
    s = Sim(lib)
    s.arm()
    s.hold(1500, pos=0.6)
    s.sel = 1
    o = s.hold(1000)                              # abierto pedido en marcha: sigue en costa
    assert o.profile == COAST and o.flags & F["PROF_WAIT"]
    n0 = len(s.trace)
    s.goto(0.0, ms=30)
    s.hold(500)
    tr = s.since(n0)
    i_open = next(i for i, r in enumerate(tr) if r["prof"] == OPEN)
    assert tr[i_open]["cmd"] == 0.0                                     # cambia solo con la salida en 0
    s.hold(1500, pos=0.6)
    assert s.trace[-1]["prof"] == OPEN and s.trace[-1]["cmd"] > 0.0
    t0 = s.t
    s.sel = 0                                     # volver a costa: en marcha, inmediato (antirrebote)
    while s.step().profile != COAST:
        assert s.t - t0 <= s.cfg.sw_debounce_ms + 2 * DT
    s.step(sel=1)                                 # un glitch del selector no vuelve a abierto
    assert s.hold(300).profile == COAST


def test_profile_resets_to_coast_on_disarm_and_rearm(lib):
    s = Sim(lib)
    s.arm()
    s.sel = 1
    assert s.hold(100).profile == OPEN
    o = s.step(kill=0)
    assert o.profile == COAST and o.state == ST["DISARMED"]
    o = s.hold(1500)                              # re-armado con el selector en abierto: COSTA
    assert o.state == ST["ARMED"] and o.profile == COAST and o.flags & F["PROF_WAIT"]
    s.sel = 0
    s.hold(100)
    s.sel = 1
    assert s.hold(100).profile == OPEN


# ================================================================== sensor, watchdog, forma
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


def test_sensor_fault_during_weed_and_bucket_down(lib):
    for setup in ("weed", "bucket"):
        s = Sim(lib, bucket=0 if setup == "bucket" else 1)
        s.arm()
        if setup == "weed":
            s.weed = 1
            s.hold(800)
        else:
            s.hold(1500, pos=-1.0)
        assert s.trace[-1]["cmd"] != 0.0
        o = s.step(adc=0)
        assert is_neutral(o) and o.state == ST["FAULT"]


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
    """Timeout de señal/lazo: un tick tardío (> watchdog_ms) corta y desarma."""
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


def test_deadband_and_thrust(lib):
    c = default_cfg(lib)
    db, rl = c.deadband, c.reverse_limit
    for pos in (0.0, 0.5 * db, 0.99 * db, -0.99 * db, db, -db):
        assert lib.tl_shape(byref(c), pos) == 0.0
    small = lib.tl_shape(byref(c), db + 0.01)
    assert 0.0 < small < 0.02                     # continuo en el borde de la zona muerta
    assert lib.tl_shape(byref(c), 1.0) == pytest.approx(1.0)
    assert lib.tl_shape(byref(c), -1.0) == pytest.approx(-1.0)
    # empuje (siempre ≥ 0): bucket arriba / abajo × lado de la palanca
    assert lib.tl_thrust(byref(c), 1.0, 0) == pytest.approx(1.0)
    assert lib.tl_thrust(byref(c), -1.0, 0) == 0.0
    assert lib.tl_thrust(byref(c), -1.0, 1) == pytest.approx(rl)
    assert lib.tl_thrust(byref(c), 1.0, 1) == pytest.approx(rl)
    assert all(lib.tl_thrust(byref(c), x / 50, b) >= 0.0 for x in range(-50, 51) for b in (0, 1))
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
        mode = rnd.choice(["fwd", "half", "bucket", "weed"])
        s = Sim(lib, bucket=0 if mode == "bucket" else 1)
        s.arm()
        if mode == "weed":
            s.weed = 1
            s.hold(rnd.randint(500, 2500))
        else:
            s.hold(rnd.randint(1200, 2500), pos={"fwd": 1.0, "half": 0.5, "bucket": -1.0}[mode])
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
    """30 000 ticks aleatorios (glitches, kill, seta, dt tardíos, bucket, pulsador, selector): invariantes."""
    rnd = random.Random(42)
    s = Sim(lib)
    c = s.cfg
    pos, seg_left, mode, last_sign, zero_since = 0.0, 0, "rest", 0, None
    bucket, weed, sel = 1, 0, 0
    neg_start, press_start, n_weed, prev_prof = None, None, 0, COAST

    for i in range(30000):
        if seg_left <= 0:                         # segmentos: descanso en cero, manejo, golpes de palanca
            mode = rnd.choice(["rest", "rest", "rest", "ride", "ride", "snap"])
            seg_left = rnd.randint(50, 250)
        seg_left -= 1
        if mode == "rest":
            pos = max(-0.07, min(0.07, pos * 0.5 + rnd.uniform(-0.01, 0.01)))
            if rnd.random() < 0.01:
                bucket = 1 - bucket               # bucket se mueve con el acelerador en neutro
        elif mode == "ride":
            lo, hi = (-1.0, 0.1) if bucket == 0 else (-0.1, 1.0)
            pos = max(lo, min(hi, pos + rnd.uniform(-0.05, 0.05)))
        elif rnd.random() < 0.05:
            pos = rnd.choice([-1.0, -0.5, 0.0, 0.3, 1.0])              # a veces "imposible" → FAULT
        if rnd.random() < 0.004:
            weed = 1 - weed
        if rnd.random() < 0.002:
            sel = 1 - sel
        b_in = bucket if rnd.random() > 0.002 else 1 - bucket          # glitch del fin de carrera
        adc = s.adc(pos)
        if rnd.random() < 0.001:
            adc = rnd.choice([0, 20, 1010, 1023, rnd.randint(0, 1023)])
        kill = 0 if rnd.random() < 0.0007 else 1
        estop = 0 if rnd.random() < 0.0004 else 1
        dt = DT if rnd.random() > 0.004 else rnd.choice([0, 1, 25, c.watchdog_ms, c.watchdog_ms + 1, 400])
        prev_cmd = s.trace[-1]["cmd"] if s.trace else 0.0
        press_start = (press_start if press_start is not None else s.t) if weed else None
        o = s.step(adc=adc, kill=kill, estop=estop, dt=dt, bucket=b_in, sel=sel, weed=weed)
        assert 1000 <= o.ppm_us <= 2000
        assert (o.ppm_us == 1500) == (o.cmd == 0.0) or abs(o.cmd) < 0.002
        unsafe = (not kill or not estop or dt > c.watchdog_ms or adc < c.adc_fault_low or adc > c.adc_fault_high)
        if unsafe:
            assert is_neutral(o) and o.state in (ST["DISARMED"], ST["FAULT"]), i
        assert (o.enable == 1) == (o.state in ARMED_STATES)
        # giro inverso: solo limpieza de rejilla, lenta, con acelerador en 0 y pulsador sostenido
        assert o.cmd >= -c.weed_cmd - 1e-6, i
        if o.cmd < 0.0:
            assert weed and s.in_zero(adc) and o.state == ST["WEED"], i
            if neg_start is None:
                neg_start = s.t
                n_weed += 1
                assert s.t - press_start >= c.weed_hold_ms, i
            assert s.t - neg_start < c.weed_max_ms, i
        else:
            neg_start = None
        # bucket abajo (contacto abierto en este tick): nunca más que reverse_limit
        if not b_in:
            assert o.cmd <= c.reverse_limit + 1e-6, i
        if o.flags & F["BKT_HOLD"]:
            assert o.cmd == 0.0, i
        # perfil: abierto solo armado, y el paso costa → abierto solo con la salida en 0
        if o.profile == OPEN:
            assert o.state in ARMED_STATES and sel, i
            if prev_prof == COAST:
                assert o.cmd == 0.0, i
        prev_prof = o.profile
        if abs(o.cmd) > abs(prev_cmd) and o.cmd * prev_cmd >= 0:
            assert abs(o.cmd) - abs(prev_cmd) <= dt / c.ramp_up_ms + 1e-5, i
        if o.cmd == 0.0:                          # cambio de sentido: ≥ dwell en cero entre signos opuestos
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
            assert tr[k]["prof"] == COAST, k     # cada armado arranca en COSTA
            j = k
            while j - 1 >= 0 and ok(tr[j - 1]):
                j -= 1
            assert ok(tr[k]) and tr[k]["t"] - tr[j]["t"] >= c.arm_hold_ms, k
    assert n_arm >= 5                             # el fuzz efectivamente re-armó varias veces
    assert n_weed >= 3                            # … y ejercitó la limpieza de rejilla
    assert any(r["prof"] == OPEN for r in tr) and any(r["state"] == ST["RUN_REV"] for r in tr)


# ================================================================== tabla de verdad y coherencia
def test_truth_table_only_all_ok_runs():
    import calc_electronica as ce
    tt = ce.truth_table()
    assert len(tt) == 2 ** 9 * 3
    runs_ = [r for r in tt if r["motor"] != "PARADO"]
    assert len(runs_) == 4
    assert {(r["K1"], r["fin_carrera_bucket"]) for r in runs_} == {(k, b) for k in ("normal", "soldado") for b in (0, 1)}
    for r in runs_:
        assert (r["cordon"], r["seta"], r["desconectador"], r["F1"], r["F2"], r["MCU_armado"],
                r["timeout_VESC"], r["falla_sensor"]) == (1, 1, 1, 1, 1, 1, 0, 0)
        assert ("reverse_limit" in r["limite_cmd"]) == (r["fin_carrera_bucket"] == 0)
    for r in tt:
        if r["cordon"] == 0 or r["seta"] == 0:
            assert r["motor"] == "PARADO" and r["n_barreras"] >= 1 and r["limite_cmd"] == "0"
            if r["MCU_coherente"] and r["K1"] == "normal" and r["desconectador"] and r["F1"]:
                assert r["n_barreras"] >= 3      # contactor + kill ADC2 + MCU neutro
    nominal = {v[0]: v[2] for v in ce.VARS}
    for name, values, ok in ce.VARS:          # cualquier desvío único del estado nominal para el motor…
        for v in values:
            if v == ok or (name == "K1" and v == "soldado"):
                continue
            d = dict(nominal, **{name: v})
            if name == "fin_carrera_bucket":      # … salvo el bucket: no para, limita (siempre en avance)
                assert ce.chain(**d)["motor"] == "PUEDE GIRAR" and "reverse_limit" in ce.chain(**d)["limite_cmd"]
                continue
            assert ce.chain(**d)["motor"] == "PARADO", (name, v)


def test_truth_table_bucket_rows_match_firmware(lib):
    """Las filas que giran de tabla_verdad.csv coinciden con la lógica real: con el fin de carrera
    cerrado la palanca a fondo da 100 %; abierto, reverse_limit; nunca negativo."""
    import calc_electronica as ce
    for r in (r for r in ce.truth_table() if r["motor"] != "PARADO"):
        s = Sim(lib, bucket=r["fin_carrera_bucket"])
        s.arm()
        s.hold(2500, pos=1.0)
        s.goto(0.0)
        s.hold(1000, pos=-1.0)
        mx = max(x["cmd"] for x in s.trace)
        assert min(x["cmd"] for x in s.trace) >= 0.0
        assert mx == pytest.approx(1.0 if r["fin_carrera_bucket"] else s.cfg.reverse_limit, abs=1e-6)


def test_sketch_uses_identical_logic_copy_and_required_io():
    for f in ("throttle_logic.c", "throttle_logic.h"):
        assert (FW / f).read_bytes() == (FW / "p1_throttle" / "src" / f).read_bytes(), \
            f"copiar firmware/{f} a firmware/p1_throttle/src/"
    ino = (FW / "p1_throttle" / "p1_throttle.ino").read_text(encoding="utf-8")
    for needle in ("WDTO_120MS", "PIN_HALL = A0", "PIN_KILL = 2", "PIN_ESTOP = 3", "PIN_PPM = 9",
                   "PIN_BUCKET = 5", "PIN_PROFILE_SEL = 7", "PIN_WEED = 8", "PIN_PROFILE_OUT = 12",
                   "pinMode(PIN_BUCKET, INPUT_PULLUP)", "pinMode(PIN_PROFILE_SEL, INPUT_PULLUP)",
                   "pinMode(PIN_WEED, INPUT_PULLUP)", "in.bucket_up = (digitalRead(PIN_BUCKET) == LOW)",
                   "in.sel_open = (digitalRead(PIN_PROFILE_SEL) == LOW)", "in.weed_btn = (digitalRead(PIN_WEED) == LOW)",
                   "INPUT_PULLUP", "tl_tick(", "ISR(INT0_vect)", "ISR(INT1_vect)", "wdt_reset()"):
        assert needle in ino, needle
    pins = re.findall(r"static const uint8_t (PIN_\w+) = (\w+);", ino)
    assert len({v for _, v in pins}) == len(pins), f"pines repetidos: {pins}"
    # D10 es OC1B del Timer1 del PPM y D13 el LED: no usarlos para entradas/salidas nuevas
    assert not {"10", "13"} & {v for _, v in pins}
    # la salida de perfil arranca en COSTA (BAJO) antes de configurar el pin como salida
    assert ino.index("digitalWrite(PIN_PROFILE_OUT, LOW)") < ino.index("pinMode(PIN_PROFILE_OUT, OUTPUT)")
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
    vv = vesc_values()
    assert vv["l_current_max"] == round(sizing["electrical"]["I_phase_limit_A"], 0)
    assert vv["l_current_min"] == pytest.approx(-vv["brake_frac"] * vv["l_current_max"])
    assert vv["l_current_reverse"] == pytest.approx(round(vv["reverse_current_frac"] * vv["l_current_max"]))
    assert vv["l_in_current_max"] <= 0.8 * vv["i_bms"] + 1e-9
    assert vv["i_in_limited"] or vv["l_in_current_max"] >= sizing["electrical"]["I_bat_peak_A"]
    assert vv["l_battery_cut_start"] > vv["l_battery_cut_end"]
    pp = vv["motor_poles"] / 2
    assert vv["n_max_loaded_rpm"] < vv["erpm_tech"] / pp < vv["n_noload_rpm"]      # perfil abierto
    assert vv["l_max_erpm"] <= vv["erpm_tech"]                                      # perfil costa (por defecto)
    if vv["erpm_legal"]:
        assert vv["l_max_erpm"] <= vv["erpm_legal"]
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
    for needle in ("F1", "S1 desconectador", "K1 ", "R_pre", "CORDÓN", "SETA", "F2", "Bobina K1",
                   "DC-DC", "Arduino Nano", "Sensor hall", "J1 IP68", "ADC2", "PPM", "Q_EN", "BAT−", "CASCO",
                   "ISO 13297", "≤ 178 mm", "D5 ← bucket"):
        assert needle in texts, needle
    assert f"F1 {sizing['electrical']['fuse_a']:.0f} A" in texts
