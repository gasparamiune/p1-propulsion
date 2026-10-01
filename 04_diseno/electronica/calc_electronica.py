#!/usr/bin/env python3
"""calc_electronica.py — Cálculos eléctricos y de la cadena de seguridad de P1.

Lee inputs.yaml (única fuente de entradas) y resultados/sizing.json (no hardcodea cargas) y produce:
  • 04_diseno/electronica/electronica.json   valores calculados (config VESC, precarga, bobina,
                                             optos, presupuesto de tiempo de corte, componentes)
  • 04_diseno/electronica/tabla_verdad.csv   enumeración COMPLETA de la cadena de habilitación
  • Bloques <!-- ELEC:nombre --> ... <!-- /ELEC:nombre --> del README.md de esta carpeta

Uso:  python 04_diseno/electronica/calc_electronica.py [--check]
      --check: no escribe; exit 1 si el README/JSON/CSV no coinciden con lo calculado.
Etiquetas: [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO].
"""
from __future__ import annotations

import csv
import io
import itertools
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

VESC_SRC = "https://raw.githubusercontent.com/vedderb/bldc/master"
R06 = "research/R06_electrica.md"

# ----------------------------------------------------------------------------------------------
# Supuestos y datos propios de este módulo (todo lo demás sale de inputs.yaml / sizing.json)
# ----------------------------------------------------------------------------------------------
A = {
    "v_cell_max": (3.65, "V", f"[ESTIMADO: {R06} §4.3, LFP 3,65 V/celda máx.]"),
    "v_cell_nom": (3.2, "V", f"[ESTIMADO: {R06} §4.3, LFP 3,2 V/celda nominal]"),
    "v_cell_cut_start": (3.0, "V", f"[ESTIMADO: {R06} §2.4, corte LFP 3,0 V/celda]"),
    "v_cell_cut_end": (2.8, "V", f"[ESTIMADO: {R06} §2.4, corte LFP 2,8 V/celda]"),
    "c_bus_f": (2.0e-3, "F", f"[ESTIMADO: {R06} §3.4, C de bus del VESC 1–2 mF no publicado; se toma el mayor]"),
    "r_pre_ohm": (100.0, "Ω", f"[SUPUESTO: {R06} §3.4 (100 Ω → 5τ ≤ 1 s)]"),
    "coil_p_w": ((7.0, 13.0), "W", f"[VERIFICADO: Albright SW80, bobina continua 7–13 W ({R06} §3.3)]"),
    "coil_v_options": ((12.0, 24.0, 36.0, 48.0, 72.0, 96.0), "V", f"[VERIFICADO: Albright SW80/SW80B, bobinas de 6–240 V CC ({R06} §3.3)]; se elige la menor con V_máx/Us ≤ 1,10 y cierre ≤ V en reposo al corte"),
    "coil_over_max": (1.10, "—", "[SUPUESTO: sobretensión continua de bobina ≤ 110 % Us sin confirmación del fabricante]"),
    "brake_frac": (0.3, "—", "[SUPUESTO: corriente de frenado = 30 % de l_current_max (un jet casi no regenera; protege BMS)]"),
    "weed_rev_frac": (0.25, "—", "[SUPUESTO: giro inverso lento (≤ 25 % de las rpm de 5 kn) solo para soltar algas de la rejilla]"),
    "pump_P_T_exp": (1.5, "—", "[CALCULADO: bomba con T ∝ n², P ∝ n³ → P ∝ T^1,5; límite de par = P_frac^(2/3)]"),
    "coil_pullin_frac": (0.66, "—", f"[VERIFICADO: Albright SW80, cierre máx. 66 % Us, tipo continuo ({R06} §3.3)]"),
    "coil_p_prolonged_w": ((13.0, 15.0), "W", f"[VERIFICADO: Albright SW80, bobina prolongada 13–15 W ({R06} §3.3)]"),
    "coil_r_sup_factor": (1.0, "—", "[SUPUESTO: R del supresor diodo+R ≈ R de bobina (pico ≈ 2·V); el valor real lo fija T0.4]"),
    "opto_vr_max": (5.0, "V", "[ESTIMADO: V_R máx. del LED de optoacopladores de fototransistor típicos 5–6 V; verificar en la hoja del elegido]"),
    "diode_vf": (0.7, "V", "[ESTIMADO: diodo de silicio]"),
    "vih_frac": (0.6, "—", "[ESTIMADO: V_IH mín. ATmega328P = 0,6·Vcc (hoja de datos; no releída en esta sesión)]"),
    "vesc_iq_unknown": (None, "A", "[SUPUESTO: el consumo en reposo del VESC 75100 no está publicado; se mide en T0.3]"),
    "contactor_open_ms": ((8.0, 20.0, 50.0), "ms", f"[VERIFICADO: SW80 apertura 8–20 ms con diodo+resistencia, 50 ms solo diodo ({R06} §3.3)]"),
    "kill_switch_rating_a": (5.0, "A", f"[VERIFICADO: Sea Dog SD-420487-1, 5 A máx. ({R06} §3.2)]"),
    "f2_factor": (3.0, "—", "[SUPUESTO: fusible de mando ≥ 3 × I_bobina máx.]"),
    "opto_vf": (1.2, "V", "[ESTIMADO: LED IR de optoacoplador típico 1,1–1,4 V]"),
    "opto_if_target": (5.0e-3, "A", "[SUPUESTO: 5 mA a tensión nominal]"),
    "opto_ctr_min": (0.5, "—", "[SUPUESTO: especificación mínima de compra CTR ≥ 50 %]"),
    "pullup_ohm": (10e3, "Ω", "[SUPUESTO: pull-up externo 10 kΩ (D2/D3 a 5 V; ADC2 a 3,3 V, R06 §2.5)]"),
    "rc_filter_s": (1.0e-3, "s", "[SUPUESTO: 10 kΩ × 100 nF en D2/D3 (inmunidad a ruido del motor)]"),
    # tick_ms y ppm_frame_ms se leen del sketch (sketch_consts()), no se duplican acá.
    "vesc_kill_poll_ms": (10.0, "ms", f"[VERIFICADO: {VESC_SRC}/timeout.c — hilo de timeout/kill duerme 10 ms]"),
    "vesc_ppm_timeout_ms": (250.0, "ms", "[SUPUESTO: 12 tramas PPM perdidas; default 1000 ms VERIFICADO appconf_default.h]"),
    "vesc_ramp_neg_s": (0.1, "s", "[SUPUESTO: bajada rápida en el VESC; default 0,2 s VERIFICADO appconf_default.h]"),
    "vesc_ramp_pos_s": (1.0, "s", f"[SUPUESTO: redundante con la rampa del MCU ({R06} §2.6 ~1 s); default 0,4 s VERIFICADO]"),
    "vesc_hyst": (0.02, "—", "[SUPUESTO: el MCU ya aplica la zona muerta; default 0,15 VERIFICADO se comería el 15 % inferior]"),
    # polos del motor: 2 × inputs.yaml motor.options.<elegido>.pole_pairs (no se duplica acá)
    "erpm_margin": (1.15, "—", "[SUPUESTO: 15 % sobre las rpm máximas con carga de sizing]"),
    "erpm_rev_margin": (1.5, "—", "[SUPUESTO: 50 % sobre las rpm del bollard en reversa (arrancada hacia atrás)]"),
    "i_in_margin": (1.05, "—", "[SUPUESTO: l_in_current_max ≥ 1,05 × I_bat pico de sizing, redondeado a 5 A]"),
    "bms_frac": (0.8, "—", f"[ESTIMADO: {R06} §2.4, ≤ 80 % de la corriente continua del BMS]"),
    "i_in_min": (-10.0, "A", "[SUPUESTO: la hélice regenera poco; protege el BMS al frenar/invertir]"),
    "v_max_vin_factor": (1.2, "—", "[SUPUESTO: l_max_vin = 1,2 × V carga plena → protege el DC-DC ante un BMS abierto regenerando]"),
    "dcdc_vin_max": (36.0, "V", "[VERIFICADO: research/R08a §9 — TRACO TSR 1-2450E, entrada 7–36 V → 5 V 1 A]"),
    "dcdc_alt_vin_max": (72.0, "V", "[VERIFICADO: research/R08a §9 — RECOM R-78HB5.0-0.5, entrada 9–72 V → 5 V 0,5 A]"),
    "kill_switch_watski": ((12.0, 15.0), "V, A", "[VERIFICADO: research/R08a §3 — Watski 'Dødmands kontakt universal' 12 V – 15 A]"),
}


SKETCH = HERE / "firmware" / "p1_throttle" / "p1_throttle.ino"


def sketch_consts():
    """Constantes de tiempo leídas de p1_throttle.ino (única fuente): TICK_MS, PPM_PERIOD_US, WDT."""
    txt = SKETCH.read_text(encoding="utf-8")

    def get(name):
        m = re.search(rf"\b{name}\s*=\s*(\d+)", txt)
        if not m:
            raise ValueError(f"{name} no encontrado en {SKETCH.name}")
        return float(m.group(1))

    wdt = re.search(r"wdt_enable\(WDTO_(\d+)MS\)", txt)
    return {"tick_ms": get("TICK_MS"), "ppm_frame_ms": get("PPM_PERIOD_US") / 1000.0,
            "wdt_ms": float(wdt.group(1)) if wdt else None}


def val(k):
    return A[k][0]


def tag(k):
    return A[k][2]


def load():
    from p1calc.io import load_inputs
    inp = load_inputs()
    with open(ROOT / "resultados" / "sizing.json", encoding="utf-8") as f:
        sz = json.load(f)
    return inp, sz


def ceil_to(x, step):
    return step * math.ceil(x / step - 1e-9)


def e_series(x, series=(1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2)):
    """Valor E12 más cercano por debajo o igual (resistencias)."""
    dec = 10 ** math.floor(math.log10(x))
    cands = [s * dec for s in series] + [10 * dec]
    return max(c for c in cands if c <= x * 1.0001)


# ----------------------------------------------------------------------------------------------
def compute(inp=None, sz=None):
    if inp is None or sz is None:
        inp, sz = load()
    sel = sz["selection"]
    bat = inp["battery"]["options"][sel["battery"]]
    mot = inp["motor"]["options"][sel["motor"]]
    el = inp["electrical"]
    cells = int(bat.get("cells") or round(bat["v_nom"] / val("v_cell_nom")))
    v_nom = bat["v_nom"]
    v_max = cells * val("v_cell_max")
    v_min_load = bat["v_min"]
    i_bms = bat["i_cont_a"]
    elc = sz["electrical"]
    i_mot = round(elc["I_phase_limit_A"], 0)
    rev = val("brake_frac")
    p_rev = inp["waterjet"]["reverse"]["power_limit_frac"]
    t_rev = p_rev ** (1 / val("pump_P_T_exp"))                  # fracción de par/corriente con el bucket abajo
    i_bat_pk = elc["I_bat_peak_A"]
    v_class = sel.get("v_class", 48)
    poles = int(round(2 * mot["pole_pairs"]))
    poles_tag = (f"[inputs.yaml motor.options.{sel['motor']}.pole_pairs = {mot['pole_pairs']} (allí con su etiqueta)] · "
                 "default FW 14 [VERIFICADO: mcconf_default.h MCCONF_SI_MOTOR_POLES]; CONTAR imanes del motor real")
    sk = sketch_consts()

    R = {"meta": {"battery": sel["battery"], "battery_desc": bat["desc"], "motor": sel["motor"],
                  "motor_desc": mot["desc"], "motor_kv": mot["kv_rpm_v"], "esc": sel["esc"],
                  "esc_desc": inp["esc"]["options"][sel["esc"]]["desc"], "cells_series": cells,
                  "v_nom": v_nom, "v_max": v_max, "v_min_load": v_min_load}}

    # ---------------- Configuración del VESC (FW ≥ 5.03)
    pp = poles / 2
    n_max = sz["mech"]["n_max_rpm"]
    n_rev = val("weed_rev_frac") * sz["legal_speed"].get("n_legal_rpm", n_max / 2)
    n_noload = mot["kv_rpm_v"] * v_max
    erpm_max = round(val("erpm_margin") * n_max * pp, -2)
    erpm_tech = erpm_max
    erpm_legal = sz.get('legal_speed', {}).get('erpm_cap')
    if erpm_legal:
        erpm_max = min(erpm_max, int(erpm_legal // 100 * 100))   # modo costa (D-30): 5 kn a < 300 m
    erpm_min = -round(n_rev * pp, -2)
    i_in_max = ceil_to(val("i_in_margin") * i_bat_pk, 5.0)
    i_in_cap = val("bms_frac") * i_bms
    i_in_limited = i_in_max > i_in_cap
    i_in_max = min(i_in_max, i_in_cap)
    cut_start = round(cells * val("v_cell_cut_start"), 1)
    cut_end = round(cells * val("v_cell_cut_end"), 1)
    max_vin = round(val("v_max_vin_factor") * v_max, 0)
    rows = []

    def add(group, name, value, unit, default, t, note=""):
        rows.append({"grupo": group, "parametro": name, "valor": value, "unidad": unit,
                     "default": default, "tag": t, "nota": note})

    add("Firmware", "versión de firmware", "≥ 5.03", "—", "—",
        f"[VERIFICADO: {R06} §2.2 — KILL_SW_MODE aparece en 5.03; no existe en 5.02]")
    no_filter = any(k in sel["esc"].replace(" ", "") for k in ("75100", "FSESC75200", "75200W"))
    add("Firmware", "foc_phase_filter_enable", "false" if no_filter else "true (dejar)", "—", "true (false en target 75_100, FW ≥ 6.00)",
        f"[VERIFICADO: {R06} §2.1 — Flipsky: con FW ≥ 5.3 apagar el filtro de fase o se daña el 75100]; "
        f"default [VERIFICADO: mcconf_default.h MCCONF_FOC_PHASE_FILTER_ENABLE; hw_75_100.h false ({R06} §2.2)]",
        "Solo Flipsky 75100/75200 sin filtro; el FSESC 75350 y el 110300 SÍ tienen filtro de fase (research/R11 §2)")
    add("Motor", "si_motor_poles", poles, "—", 14, poles_tag)
    add("Motor", "l_current_max", i_mot, "A", 60.0,
        f"[CALCULADO: sizing.json electrical.I_phase_limit_A = {fa(round(elc['I_phase_limit_A'], 1))} A: par T_max {fa(round(sz['mech']['T_max_Nm'], 1))} N·m "
        f"< par de corte del pasador / {fa(inp['waterjet']['shear_pin']['fuse_factor_vs_tmax'])}] · default 60 A [VERIFICADO: mcconf_default.h]",
        "Límite de FASE: fija el par máx. (el pasador de corte no corta en arranques). En PPM Current acelera con servo × l_current_max [VERIFICADO: app_ppm.c]")
    add("Motor", "l_current_min", -rev * i_mot, "A", -60.0,
        f"[CALCULADO: −{fa(rev)} × l_current_max] · {tag('brake_frac')}",
        "Corriente de FRENADO (servo opuesto a las rpm) [VERIFICADO: app_ppm.c]")
    add("Motor", "límite de potencia en REVERSA (bucket abajo, MCU)",
        f"P ≤ {fa(p_rev)} × P → corriente ≤ {fa(round(t_rev, 2))} × l_current_max = {fa(round(t_rev * i_mot, 0))}", "A", "—",
        f"[CALCULADO: inputs.yaml waterjet.reverse.power_limit_frac {fa(p_rev)}; {tag('pump_P_T_exp')}]",
        "El jet NO invierte el giro: la reversa es el bucket. El MCU lee el fin de carrera del bucket y topea el PPM "
        "(reverse_limit del firmware = este valor; fin de carrera en D5, README §5)")
    add("Batería", "l_in_current_max", i_in_max, "A", "99 (100 en target 75_100)",
        f"[CALCULADO: ⌈{fa(val('i_in_margin'))} × I_bat pico {fa(round(i_bat_pk, 1))} A⌉ a 5 A, ≤ {fa(val('bms_frac') * 100)} % × BMS {fa(i_bms)} A]",
        "LIMITA la V máx: I_bat pico de sizing > 80 % del BMS" if i_in_limited else
        f"No limita el pico de sizing ({fa(round(i_bat_pk, 1))} A) y deja {fa(i_in_cap - i_in_max)} A de margen al 80 % del BMS")
    add("Batería", "l_in_current_min", val("i_in_min"), "A", "-60 (-100 en target 75_100)",
        f"{tag('i_in_min')} · defaults [VERIFICADO: mcconf_default.h; hw_75_100.h ({R06} §2.4)]")
    add("Batería", "l_battery_cut_start", cut_start, "V", 10.0,
        f"[CALCULADO: {cells} celdas × {fa(val('v_cell_cut_start'))} V] · {tag('v_cell_cut_start')}")
    add("Batería", "l_battery_cut_end", cut_end, "V", 8.0,
        f"[CALCULADO: {cells} × {fa(val('v_cell_cut_end'))} V] · {tag('v_cell_cut_end')}",
        (f"OJO: sizing usa V mín bajo carga = {fa(v_min_load)} V < cut_end → con batería baja el VESC recorta "
         "antes de lo que supone el cálculo de V máx" if v_min_load < cut_end else ""))
    add("Batería", "l_max_vin", max_vin, "V", "57 (90 en target 75_100)",
        f"[CALCULADO: {fa(val('v_max_vin_factor'))} × {fa(v_max)} V] · {tag('v_max_vin_factor')}",
        f"< entrada máx. del DC-DC TSR 1-2450E {val('dcdc_vin_max'):.0f} V" if max_vin < val("dcdc_vin_max") else
        "OJO: ≥ entrada máx. del DC-DC → usar R-78HB (72 V)")
    add("Velocidad", "l_max_erpm", erpm_max, "ERPM", 100000,
        (f"[CALCULADO: tope legal 'modo costa' = rpm a 5 kn con carga liviana (sizing.legal_speed, D-30); "
         f"techo técnico {erpm_tech:.0f} = {fa(val('erpm_margin'))} × {n_max:.0f} rpm × {pp:.0f} pares de polos]"
         if erpm_max < erpm_tech else
         f"[CALCULADO: {fa(val('erpm_margin'))} × {n_max:.0f} rpm (máx. con carga, sizing) × {pp:.0f} pares de polos]"),
        f"Sin carga (hélice fuera del agua) el motor iría a {n_noload:.0f} rpm = {n_noload * pp:.0f} ERPM "
        f"[CALCULADO: KV {mot['kv_rpm_v']:.0f} × {fa(v_max)} V]; el límite lo baja a {erpm_max / pp:.0f} rpm")
    if erpm_max < erpm_tech:
        add("Velocidad", "l_max_erpm (perfil 2: fuera de la franja de 300 m)", erpm_tech, "ERPM", 100000,
            f"[CALCULADO: {fa(val('erpm_margin'))} × {n_max:.0f} rpm (n máx. de sizing) × {pp:.0f} pares de polos]",
            "Segundo perfil del VESC (o mcconf alternativo cargado por UART); por defecto arranca SIEMPRE en el perfil legal de 5 kn (R13)")
    add("Velocidad", "l_min_erpm", erpm_min, "ERPM", -100000,
        f"[CALCULADO: −{n_rev:.0f} rpm × {pp:.0f} pares de polos] · {tag('weed_rev_frac')}",
        "Solo giro inverso lento para limpiar la rejilla; la reversa de marcha es el bucket")
    add("Velocidad", "l_max_duty", 0.95, "—", 0.95, "[VERIFICADO: mcconf_default.h MCCONF_L_MAX_DUTY 0,95; mantener]")
    add("Temperatura", "l_temp_fet_start / end", "85 / 100", "°C", "85 / 100",
        "[VERIFICADO: mcconf_default.h; mantener]")
    t_wmax = mot["t_winding_max_c"]
    t_m_start = min(85.0, t_wmax)
    t_m_end = t_m_start + 15.0
    add("Temperatura", "l_temp_motor_start / end", f"{t_m_start:.0f} / {t_m_end:.0f}", "°C", "85 / 100",
        f"[CALCULADO: start = mín(85 default, t_winding_max_c {t_wmax:.0f} °C de inputs.yaml); end = start + 15 como el default] "
        "· default 85/100 [VERIFICADO: mcconf_default.h]",
        "sizing toma t_winding_max_c como la temperatura donde el VESC EMPIEZA a limitar: no subir start sin rehacer "
        "el cálculo térmico. Requiere NTC 10 k en el bobinado (TEMP_SENSOR_NTC_10K_25C, R06 §1.2)")
    add("App", "app_to_use", "PPM", "—", "UART", "[VERIFICADO: appconf_default.h APPCONF_APP_TO_USE = APP_UART → cambiar]")
    add("App PPM", "ctrl_type", "PPM_CTRL_TYPE_CURRENT", "—", "NONE",
        f"[VERIFICADO: {VESC_SRC}/applications/app_ppm.c — reversa directa con signo]",
        "La lógica de dwell/inversión la hace el MCU; alternativa DUTY si la hélice ventila (R06 §2.6)")
    add("App PPM", "pulse_start / center / end", "1,0 / 1,5 / 2,0", "ms", "1,0 / 1,5 / 2,0",
        "[VERIFICADO: appconf_default.h] = salida del MCU (throttle_logic.c)")
    add("App PPM", "hyst (zona muerta VESC)", val("vesc_hyst"), "—", 0.15, tag("vesc_hyst"),
        "app_ppm.c aplica utils_deadband(servo, hyst) [VERIFICADO: app_ppm.c]")
    add("App PPM", "throttle_exp", 0.0, "—", 0.0, "[VERIFICADO: default lineal; la expo la hace el MCU]")
    add("App PPM", "ramp_time_pos", val("vesc_ramp_pos_s"), "s", 0.4, tag("vesc_ramp_pos_s"))
    add("App PPM", "ramp_time_neg", val("vesc_ramp_neg_s"), "s", 0.2, tag("vesc_ramp_neg_s"))
    add("App PPM", "safe_start", "true", "—", "true",
        "[VERIFICADO: app_ppm.c MIN_PULSES_WITHOUT_POWER 50 → ≈ 1 s de neutro a 50 Hz [CALCULADO]]")
    add("General", "timeout_msec", val("vesc_ppm_timeout_ms"), "ms", 1000, tag("vesc_ppm_timeout_ms"),
        "Sin PPM válido → corriente de freno de timeout [VERIFICADO: app_ppm.c]")
    add("General", "timeout_brake_current", 0.0, "A", 0.0, "[VERIFICADO: appconf_default.h; 0 = rueda libre]")
    add("General", "kill_sw_mode", "KILL_SW_MODE_ADC2_HIGH", "—", "DISABLED",
        f"[VERIFICADO: {VESC_SRC}/timeout.c — kill si V(ADC_EXT2) > 1,65 V, sondeo cada 10 ms]",
        "Pull-up 10 kΩ a 3,3 V en ADC2; Q_EN + opto U3 lo llevan a GND solo con cordón+seta+MCU armado")
    add("General", "multi_esc", "false", "—", "true", "[VERIFICADO: appconf_default.h APPCONF_PPM_MULTI_ESC true; un solo ESC]")
    R["vesc"] = rows
    R["vesc_values"] = {"l_current_max": i_mot, "l_current_min": -rev * i_mot, "l_in_current_max": i_in_max,
                        "l_in_current_min": val("i_in_min"), "l_battery_cut_start": cut_start,
                        "l_battery_cut_end": cut_end, "l_max_vin": max_vin, "l_max_erpm": erpm_max,
                        "l_min_erpm": erpm_min, "timeout_msec": val("vesc_ppm_timeout_ms"),
                        "ramp_time_pos": val("vesc_ramp_pos_s"), "ramp_time_neg": val("vesc_ramp_neg_s"),
                        "ppm_hyst": val("vesc_hyst"), "pulse_us": [1000, 1500, 2000],
                        "motor_poles": poles, "i_bat_peak": i_bat_pk, "i_bms": i_bms,
                        "l_temp_motor_start": t_m_start, "l_temp_motor_end": t_m_end, "t_winding_max_c": t_wmax,
                        "i_in_limited": i_in_limited, "n_max_loaded_rpm": n_max, "n_noload_rpm": n_noload,
                        "n_rev_weed_rpm": n_rev, "brake_frac": rev, "reverse_power_frac": p_rev,
                        "reverse_current_frac": t_rev, "l_current_reverse": round(t_rev * i_mot, 0),
                        "erpm_legal": erpm_legal, "erpm_tech": erpm_tech, "v_class": v_class,
                        "dcdc_vin_max": val("dcdc_vin_max"), "dcdc_ok": max_vin < val("dcdc_vin_max")}

    # ---------------- Precarga (resistencia en paralelo con el contactor)
    C, Rp = val("c_bus_f"), val("r_pre_ohm")
    tau = Rp * C
    p_cruise = sz["legal_speed"]["P_bat_legal_W"]
    R["precarga"] = {
        "R_ohm": Rp, "C_F": C, "tau_s": tau, "t_95_s": 3 * tau, "t_5tau_s": 5 * tau,
        "I_peak_A": v_max / Rp, "E_J": 0.5 * C * v_max ** 2, "P_short_W": v_max ** 2 / Rp,
        "P_rating_W": ceil_to(1.5 * v_max ** 2 / Rp, 5.0),
        "P_max_transfer_W": v_max ** 2 / (4 * Rp), "P_cruise_W": p_cruise,
        "transfer_frac_of_cruise": v_max ** 2 / (4 * Rp) / p_cruise,
        "wait_s": ceil_to(5 * tau * 2, 1.0),
    }

    # ---------------- Bobina del contactor y circuito de mando
    pmin, pmax = val("coil_p_w")
    v_rest = cells * val("v_cell_cut_start")
    vc = next((u for u in val("coil_v_options") if v_max / u <= val("coil_over_max") and val("coil_pullin_frac") * u <= v_rest),
              val("coil_v_options")[-1])
    r_coil = (vc ** 2 / pmax, vc ** 2 / pmin)
    i_coil_max = v_max / r_coil[0]
    p_coil_nom = (v_nom ** 2 / r_coil[1], v_nom ** 2 / r_coil[0])
    e_usable = sz["energy"]["E_usable_wh"]
    t_end = inp["operation"]["mission_fast_h"] + inp["operation"]["mission_legal_h"]
    f2 = next(x for x in (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0) if x >= val("f2_factor") * i_coil_max)
    R["bobina"] = {
        "V_nom": vc, "R_coil_ohm": r_coil, "I_max_A": i_coil_max, "P_at_vnom_W": p_coil_nom,
        "E_2h_Wh": (p_coil_nom[0] * t_end, p_coil_nom[1] * t_end), "endurance_h": t_end,
        "frac_E_usable": (p_coil_nom[0] * t_end / e_usable, p_coil_nom[1] * t_end / e_usable),
        "F2_A": f2, "kill_switch_rating_A": val("kill_switch_rating_a"),
        "kill_switch_margin": val("kill_switch_rating_a") / i_coil_max,
        "v_range_required": (v_min_load, v_max),
    }
    # Bobina a carga plena: 29,2 V sobre una bobina de 24 V = 122 % Us (sin tolerancia publicada, R06 §3.3 d)
    v_rest_min = cells * val("v_cell_cut_start")      # pack en reposo al corte de descarga del VESC
    coil_opts = {}
    i_vc = val("coil_v_options").index(vc)
    for us in sorted({vc, val("coil_v_options")[max(i_vc - 1, 0)]}):
        r_lo, r_hi = us ** 2 / pmax, us ** 2 / pmin
        coil_opts[f"{us:.0f}"] = {
            "Us_V": us, "frac_Us_at_vmax": v_max / us, "P_at_vmax_W": (v_max ** 2 / r_hi, v_max ** 2 / r_lo),
            "pullin_max_V": val("coil_pullin_frac") * us, "closes_at_v_rest_min": val("coil_pullin_frac") * us <= v_rest_min,
            "I_max_A": v_max / r_lo,
            "P_vmax_le_prolonged": v_max ** 2 / r_lo <= val("coil_p_prolonged_w")[1]}
    R["bobina"]["opciones"] = coil_opts
    R["bobina"]["v_rest_min"] = v_rest_min
    # Supresor diodo + R: al abrir, la corriente de bobina recircula y el nodo N2 (y N1 si abre la seta) va a −(Vd + I·R_sup)
    r_sup = val("coil_r_sup_factor") * r_coil[0]
    v_n2_neg = -(val("diode_vf") + i_coil_max * r_sup)
    R["bobina"]["R_sup_ohm"] = r_sup
    R["bobina"]["V_N2_negativo_V"] = v_n2_neg

    # ---------------- Optoacopladores (sensado de N1/N2 hacia el MCU y habilitación de ADC2)
    vf, ift = val("opto_vf"), val("opto_if_target")
    r2 = e_series((v_nom - 2 * vf) / ift)   # U2 + U3 en serie (nodo N2)
    r1 = e_series((v_nom - vf) / ift)       # U1 (nodo N1)
    i_lo = (v_min_load - 2 * vf) / r2
    R["optos"] = {
        "R_U2U3_ohm": r2, "I_U2U3_A": ((v_min_load - 2 * vf) / r2, (v_max - 2 * vf) / r2),
        "P_R_U2U3_W": (v_max - 2 * vf) ** 2 / r2,
        "R_U1_ohm": r1, "I_U1_A": ((v_min_load - vf) / r1, (v_max - vf) / r1), "P_R_U1_W": (v_max - vf) ** 2 / r1,
        "Ic_min_A": val("opto_ctr_min") * i_lo, "I_pullup_5V_A": 5.0 / val("pullup_ohm"),
        "I_pullup_3V3_A": 3.3 / val("pullup_ohm"),
        "V_inversa_LED_V": -v_n2_neg, "V_R_max_V": val("opto_vr_max"),
        "necesita_diodo_antiparalelo": -v_n2_neg > val("opto_vr_max"),
        "I_diodo_antiparalelo_A": (-v_n2_neg - 2 * val("diode_vf")) / r2,
    }
    # Precarga con el consumo en reposo del VESC (no publicado): corriente máx. para llegar al 90 % con K1 abierto
    R["precarga"]["Iq_max_90pct_A"] = 0.1 * v_nom / Rp
    R["precarga"]["E_cierre_80pct_J"] = 0.5 * C * (0.2 * v_nom) ** 2

    # ---------------- Presupuesto de tiempo de corte (cada camino por separado debe ser < requisito)
    req = el["kill_switch_response_s_max"]
    rc = val("rc_filter_s") * -math.log(1.0 - val("vih_frac"))  # cruce de V_IH: 0,92 τ [CALCULADO]
    tick_s, frame_s = sk["tick_ms"] / 1000, sk["ppm_frame_ms"] / 1000
    paths = {
        "MCU → PPM neutro → VESC (rampa negativa)":
            (rc + tick_s + frame_s + val("vesc_ramp_neg_s"),
             "filtro RC + 1 tick + 1 trama PPM + ramp_time_neg"),
        "MCU → Q_EN abre → kill por ADC2 del VESC":
            (rc + tick_s + val("vesc_kill_poll_ms") / 1000,
             "filtro RC + 1 tick + sondeo de 10 ms del VESC"),
        "Hardware: opto U3 apaga → kill por ADC2 (sin MCU)":
            (val("vesc_kill_poll_ms") / 1000 + 0.001, "sondeo 10 ms + conmutación del opto"),
        "Hardware: bobina sin corriente → contactor abre":
            (val("contactor_open_ms")[2] / 1000, "peor caso SW80 con solo diodo (50 ms); 8–20 ms con diodo+resistencia"),
        "MCU muerto: sin PPM → timeout del VESC":
            (val("vesc_ppm_timeout_ms") / 1000, "timeout_msec configurado"),
    }
    if sk["wdt_ms"]:
        paths["MCU colgado: WDT de hardware → reset → Q_EN abre → kill ADC2"] = (
            1.1 * sk["wdt_ms"] / 1000 + val("vesc_kill_poll_ms") / 1000,
            f"WDTO_{sk['wdt_ms']:.0f}MS del sketch × 1,1 [ESTIMADO: tolerancia del oscilador del WDT] + sondeo 10 ms")
    R["corte"] = {"requisito_s": req,
                  "caminos": {k: {"t_s": v[0], "base": v[1], "ok": v[0] < req} for k, v in paths.items()},
                  "peor_s": max(v[0] for v in paths.values())}

    # ---------------- Cables y protecciones (de sizing)
    R["cables"] = {"dc_mm2": elc["cable_dc"]["section_mm2"], "phase_mm2": elc["cable_phase"]["section_mm2"],
                   "dc_drop_frac": elc["cable_dc"]["drop_frac"], "phase_drop_frac": elc["cable_phase"]["drop_frac"],
                   "fuse_a": elc["fuse_a"], "fuse_min_a": el["fuse_factor"] * elc["I_bat_top_A"],
                   "ampacity_dc_a": elc["cable_dc"]["ampacity_a"], "fuse_protects_cable": elc.get("fuse_protects_cable")}
    # clase de tensión → contactor, fusible, aislamiento (R10b H8, R11 §8)
    hv = v_class >= 72 or v_max > 60.0
    R["clase"] = {"v_class": v_class, "hv": hv, "imd": hv,
                  "contactor": "Albright SW80B (96 V)" if hv else "Albright SW80",
                  "fuse": "fusible ≥ 100 V CC (buscar: Littelfuse CNN 125 V / clase T 125 VDC)" if hv else
                          "IMAXX midiOTO/megaOTO 58 V + portafusible HMD4-MG1-H (base aislante HIB1 > 32 V)",
                  "imd_desc": "Bender ISOMETER iso175C-1 (R11 §8, 709 €)" if hv else "no requerido (≤ 50 V CC)",
                  "dcdc": (f"TRACO TSR 1-2450E 7–{val('dcdc_vin_max'):.0f} V" if max_vin < val("dcdc_vin_max") else
                           f"RECOM R-78HB5.0-0.5 9–{val('dcdc_alt_vin_max'):.0f} V" if max_vin < val("dcdc_alt_vin_max") else
                           "DC-DC de entrada ≥ 110 V (buscar: Mean Well RSD-60H-12 + regulador 5 V)")}
    R["tabla_verdad"] = truth_table()
    R["tabla_resumen"] = truth_summary()
    return R


# ----------------------------------------------------------------------------------------------
# Tabla de verdad de la cadena de habilitación (modelo lógico del circuito del diagrama)
# ----------------------------------------------------------------------------------------------
VARS = [  # (nombre, valores posibles, valor "sano/OK")
    ("cordon", (1, 0), 1),          # 1 = clip puesto (contacto cerrado)
    ("seta", (1, 0), 1),            # 1 = liberada (NC cerrado)
    ("desconectador", (1, 0), 1),   # 1 = ON
    ("F1", (1, 0), 1),              # fusible principal 1 = sano
    ("F2", (1, 0), 1),              # fusible de mando 1 = sano
    ("K1", ("normal", "soldado", "bobina_abierta"), "normal"),
    ("MCU_armado", (1, 0), 1),      # lo que el MCU "cree" (1 también modela un MCU defectuoso)
    ("timeout_VESC", (0, 1), 0),    # 1 = PPM perdida (cable PPM cortado, MCU colgado)
    ("falla_sensor", (0, 1), 0),    # 1 = hall abierto/corto/salto
    ("fin_carrera_bucket", (1, 0), 1),  # D5: 1 = NC cerrado (bucket ARRIBA); 0 = abierto (ABAJO o cable cortado)
]


def chain(cordon, seta, desconectador, F1, F2, K1, MCU_armado, timeout_VESC, falla_sensor, fin_carrera_bucket=1):
    """Evalúa el circuito. Devuelve dict con nodos intermedios, barreras y estado del motor."""
    upstream = bool(F1 and desconectador)            # tensión aguas abajo de F1 y S1
    n1 = upstream and bool(F2 and seta)              # nodo entre seta y cordón (opto U1 → D3)
    n2 = n1 and bool(cordon)                         # nodo de la bobina (optos U2 → D2, U3 → ADC2)
    k1_closed = K1 == "soldado" or (K1 == "normal" and n2)
    bus = upstream and k1_closed                     # potencia completa en el bus del VESC
    mcu_on = upstream                                # DC-DC alimentado aguas abajo de S1 (F3)
    mcu = bool(MCU_armado) and mcu_on
    # Un firmware correcto (tests) no puede estar armado sin cordón/seta o con sensor en falla:
    coherente = (not MCU_armado) or (n2 and not falla_sensor and mcu_on)
    kill_released = n2 and mcu                       # U3 (hardware) EN SERIE con Q_EN (MCU)
    ppm_ok = mcu_on and not timeout_VESC
    cmd = mcu and not falla_sensor                   # sensor en falla → el firmware manda neutro
    barreras = []
    if not bus:
        barreras.append("bus sin potencia (K1/F1/S1)")
    if not kill_released:
        barreras.append("VESC en kill (ADC2)")
    if not ppm_ok:
        barreras.append("VESC en timeout PPM")
    if not cmd:
        barreras.append("MCU manda neutro")
    gira = bus and kill_released and ppm_ok and cmd
    return {"N1": int(n1), "N2_bobina": int(n2), "K1_cerrado": int(k1_closed), "bus_VESC": int(bus),
            "precarga_sola": int(upstream and not k1_closed), "kill_liberado": int(kill_released),
            "PPM_valido": int(ppm_ok), "comando_posible": int(cmd), "MCU_coherente": int(coherente),
            "motor": "PUEDE GIRAR" if gira else "PARADO", "n_barreras": len(barreras),
            "barreras": "; ".join(barreras) if barreras else "—",
            # firmware (tests/test_firmware.py): el bucket no para el motor, limita el comando (siempre en avance)
            "limite_cmd": ("0" if not gira else "100 % avance" if fin_carrera_bucket
                           else "≤ reverse_limit, avance (bucket abajo)")}


def truth_table():
    names = [v[0] for v in VARS]
    out = []
    for combo in itertools.product(*[v[1] for v in VARS]):
        d = dict(zip(names, combo))
        out.append({**d, **chain(**d)})
    return out


SUMMARY_ROWS = [  # None = cualquier valor (se verifica que el resultado sea el mismo en todas)
    ("Todo OK, MCU armado", dict(cordon=1, seta=1, desconectador=1, F1=1, F2=1, K1="normal", MCU_armado=1, timeout_VESC=0, falla_sensor=0, fin_carrera_bucket=1)),
    ("Todo OK, bucket abajo (o fin de carrera cortado)", dict(cordon=1, seta=1, desconectador=1, F1=1, F2=1, K1="normal", MCU_armado=1, timeout_VESC=0, falla_sensor=0, fin_carrera_bucket=0)),
    ("Cordón tirado (MCU sano → desarma)", dict(cordon=0, seta=1, desconectador=1, F1=1, F2=1, K1="normal", MCU_armado=0, timeout_VESC=None, falla_sensor=None)),
    ("Cordón tirado + MCU defectuoso que sigue armado", dict(cordon=0, seta=1, desconectador=1, F1=1, F2=1, K1="normal", MCU_armado=1, timeout_VESC=None, falla_sensor=None)),
    ("Cordón tirado + K1 soldado (MCU sano)", dict(cordon=0, seta=1, desconectador=1, F1=1, F2=1, K1="soldado", MCU_armado=0, timeout_VESC=None, falla_sensor=None)),
    ("Cordón tirado + K1 soldado + MCU defectuoso", dict(cordon=0, seta=1, desconectador=1, F1=1, F2=1, K1="soldado", MCU_armado=1, timeout_VESC=None, falla_sensor=None)),
    ("Seta pulsada (cualquier cordón/MCU/K1)", dict(cordon=None, seta=0, desconectador=1, F1=1, F2=1, K1=None, MCU_armado=None, timeout_VESC=None, falla_sensor=None)),
    ("Desconectador OFF (cualquier otro estado)", dict(cordon=None, seta=None, desconectador=0, F1=None, F2=None, K1=None, MCU_armado=None, timeout_VESC=None, falla_sensor=None)),
    ("Fusible principal F1 fundido", dict(cordon=None, seta=None, desconectador=None, F1=0, F2=None, K1=None, MCU_armado=None, timeout_VESC=None, falla_sensor=None)),
    ("Fusible de mando F2 fundido", dict(cordon=None, seta=None, desconectador=1, F1=1, F2=0, K1=None, MCU_armado=None, timeout_VESC=None, falla_sensor=None)),
    ("K1 con bobina abierta (no cierra)", dict(cordon=None, seta=None, desconectador=None, F1=None, F2=None, K1="bobina_abierta", MCU_armado=None, timeout_VESC=None, falla_sensor=None)),
    ("K1 soldado, todo lo demás OK", dict(cordon=1, seta=1, desconectador=1, F1=1, F2=1, K1="soldado", MCU_armado=1, timeout_VESC=0, falla_sensor=0)),
    ("MCU desarmado (arranque, re-armado pendiente)", dict(cordon=None, seta=None, desconectador=None, F1=None, F2=None, K1=None, MCU_armado=0, timeout_VESC=None, falla_sensor=None)),
    ("PPM perdida (timeout del VESC)", dict(cordon=None, seta=None, desconectador=None, F1=None, F2=None, K1=None, MCU_armado=None, timeout_VESC=1, falla_sensor=None)),
    ("Falla de sensor hall", dict(cordon=None, seta=None, desconectador=None, F1=None, F2=None, K1=None, MCU_armado=None, timeout_VESC=None, falla_sensor=1)),
]


def truth_summary():
    names = [v[0] for v in VARS]
    tt = truth_table()
    out = []
    for label, pat in SUMMARY_ROWS:
        match = [r for r in tt if all(pat.get(n) is None or r[n] == pat[n] for n in names)]
        motors = {r["motor"] for r in match}
        nb = [r["n_barreras"] for r in match]
        bars = sorted({b for r in match for b in r["barreras"].split("; ") if b != "—"})
        out.append({"caso": label, **{n: ("–" if pat.get(n) is None else pat[n]) for n in names},
                    "n_combinaciones": len(match), "motor": " / ".join(sorted(motors)),
                    "limite_cmd": " / ".join(sorted({r["limite_cmd"] for r in match})),
                    "barreras_min": min(nb), "barreras_max": max(nb), "barreras": "; ".join(bars) or "—"})
    return out


# ----------------------------------------------------------------------------------------------
# Salidas: JSON, CSV y bloques del README
# ----------------------------------------------------------------------------------------------
def fa(x):
    """Número con coma decimal y la precisión justa (hasta 3 decimales, sin ceros de más)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return str(x)
    if abs(x) >= 100:
        return f"{x:.0f}"
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def fmt(x, nd=1):
    if isinstance(x, float):
        s = f"{x:.{nd}f}"
        return s.replace(".", ",")
    return str(x)


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def blocks(R):
    B = {}
    B["vesc"] = md_table(["Grupo", "Parámetro (VESC Tool)", "Valor P1", "Unidad", "Default FW", "Etiqueta", "Nota"],
                         [[r["grupo"], f"`{r['parametro']}`", fa(r["valor"]), r["unidad"], fa(r["default"]), r["tag"],
                           r["nota"] or "—"] for r in R["vesc"]])
    p = R["precarga"]
    b = R["bobina"]
    o = R["optos"]
    m = R["meta"]
    vv = R["vesc_values"]
    cab = R["cables"]
    B["calc"] = md_table(["Magnitud", "Valor", "Etiqueta / base"], [
        ["Pack", f"{m['battery_desc']} → {m['cells_series']}S LFP, {fmt(m['v_nom'])} V nom., {fmt(m['v_max'])} V carga plena",
         f"[CALCULADO: inputs.yaml battery] · V/celda {tag('v_cell_max')}"],
        ["R de precarga (en paralelo con K1)", f"{p['R_ohm']:.0f} Ω, ≥ {p['P_rating_W']:.0f} W (carcasa de Al sobre la tapa-disipador)",
         f"{tag('r_pre_ohm')}; potencia [CALCULADO: 1,5 × V²/R en corto del bus]"],
        ["τ = R·C_bus / 5τ", f"{fmt(p['tau_s'], 2)} s / {fmt(p['t_5tau_s'], 2)} s", f"[CALCULADO] con C_bus {p['C_F'] * 1e3:.0f} mF {tag('c_bus_f')}"],
        ["Pico de corriente / energía en R", f"{fmt(p['I_peak_A'], 2)} A / {fmt(p['E_J'], 2)} J", "[CALCULADO: V_máx/R; ½·C·V²]"],
        ["Potencia máx. que pasa por R con K1 abierto", f"{fmt(p['P_max_transfer_W'], 1)} W = {fmt(p['transfer_frac_of_cruise'] * 100, 2)} % del crucero ({p['P_cruise_W']:.0f} W, sizing)",
         "[CALCULADO: V²/4R] → sin empuje con K1 abierto"],
        ["Espera con cordón AFUERA tras encender S1", f"≥ {p['wait_s']:.0f} s", "[CALCULADO: ≥ 2 × 5τ, redondeado]"],
        ["Bobina K1", f"{b['V_nom']:.0f} V, R = {fmt(b['R_coil_ohm'][0])}–{fmt(b['R_coil_ohm'][1])} Ω, I máx {fmt(b['I_max_A'], 2)} A a {fmt(m['v_max'])} V",
         f"[CALCULADO] desde {tag('coil_p_w')}; rango de bobina requerido {fmt(b['v_range_required'][0])}–{fmt(b['v_range_required'][1])} V"],
        ["Bobina a carga plena (sobretensión)",
         "; ".join(f"Us {o_['Us_V']:.0f} V: {fmt(o_['frac_Us_at_vmax'] * 100, 0)} % Us → {fmt(o_['P_at_vmax_W'][0])}–{fmt(o_['P_at_vmax_W'][1])} W, "
                   f"cierra con ≤ {fmt(o_['pullin_max_V'])} V ({'✔' if o_['closes_at_v_rest_min'] else '✘'} vs {fmt(b['v_rest_min'])} V en reposo al corte, "
                   f"margen {fmt(b['v_rest_min'] - o_['pullin_max_V'])} V)"
                   for o_ in b["opciones"].values()),
         f"[CALCULADO: V_máx²/R_bobina] · {tag('coil_p_prolonged_w')} · {tag('coil_pullin_frac')} · {tag('coil_v_options')} → "
         f"bobina elegida {b['V_nom']:.0f} V ({tag('coil_over_max')})"],
        ["Consumo de bobina en {:.0f} h".format(b["endurance_h"]), f"{fmt(b['E_2h_Wh'][0])}–{fmt(b['E_2h_Wh'][1])} Wh = {fmt(b['frac_E_usable'][0] * 100)}–{fmt(b['frac_E_usable'][1] * 100)} % de la energía usable (sizing)",
         "[CALCULADO: V_nom²/R × t]"],
        ["Fusible de mando F2", f"{fmt(b['F2_A'])} A", f"[CALCULADO: primer valor normalizado ≥ {val('f2_factor'):.0f} × I_bobina máx] · factor {tag('f2_factor')}"],
        ["Margen del interruptor de cordón", f"{fmt(b['kill_switch_rating_A'])} A / {fmt(b['I_max_A'], 2)} A = {fmt(b['kill_switch_margin'])}× (peor caso: Sea Dog 5 A; Watski 15 A)",
         f"{tag('kill_switch_rating_a')} · {tag('kill_switch_watski')}"],
        ["R serie de U2+U3 (nodo bobina)", f"{o['R_U2U3_ohm']:.0f} Ω, {fmt(o['I_U2U3_A'][0] * 1e3)}–{fmt(o['I_U2U3_A'][1] * 1e3)} mA, P {fmt(o['P_R_U2U3_W'], 2)} W → 0,5 W",
         f"[CALCULADO: E12 ≤ (V_nom − 2·Vf)/I] {tag('opto_vf')}"],
        ["R serie de U1 (nodo seta)", f"{o['R_U1_ohm']:.0f} Ω, {fmt(o['I_U1_A'][0] * 1e3)}–{fmt(o['I_U1_A'][1] * 1e3)} mA, P {fmt(o['P_R_U1_W'], 2)} W → 0,5 W",
         "[CALCULADO]"],
        ["Tensión inversa en los LED de U1–U3 al abrir la bobina",
         f"N2 → {fmt(b['V_N2_negativo_V'])} V (supresor diodo + R {fmt(b['R_sup_ohm'], 0)} Ω) vs V_R máx. {fmt(o['V_R_max_V'], 0)} V → "
         + ("**diodo 1N4148 en antiparalelo con cada LED** (conduce " + fmt(o['I_diodo_antiparalelo_A'] * 1e3) + " mA de pico por R2)"
            if o["necesita_diodo_antiparalelo"] else "sin diodo"),
         f"[CALCULADO: −(V_d + I_bobina·R_sup)] · {tag('coil_r_sup_factor')} · {tag('opto_vr_max')}"],
        ["Precarga con el consumo en reposo del VESC",
         f"I_q ≤ {fmt(p['Iq_max_90pct_A'] * 1e3)} mA para llegar al 90 % con K1 abierto; al 80 % la energía del cierre de K1 es {fmt(p['E_cierre_80pct_J'] * 1e3, 0)} mJ",
         f"[CALCULADO: 0,1·V_nom/R; ½·C·(0,2·V_nom)²] · {tag('vesc_iq_unknown')}"],
        ["Corriente de colector mínima (CTR 50 %) vs pull-up", f"{fmt(o['Ic_min_A'] * 1e3, 2)} mA ≫ {fmt(o['I_pullup_5V_A'] * 1e3, 2)} mA (5 V) / {fmt(o['I_pullup_3V3_A'] * 1e3, 2)} mA (3,3 V)",
         f"[CALCULADO] {tag('opto_ctr_min')}"],
        ["Fusible principal F1 / cable DC / fases", f"{R['cables']['fuse_a']:.0f} A (mín. {fmt(R['cables']['fuse_min_a'])}) / {R['cables']['dc_mm2']} mm² / {R['cables']['phase_mm2']} mm²",
         "[CALCULADO: resultados/sizing.json fuse, cables]"],
    ])
    B["componentes"] = md_table(["Ref.", "Componente", "Especificación mínima", "Elegido / referencia (BOM)", "Etiqueta"], [
        ["BAT", "Batería LiFePO4 de la selección", f"{m['cells_series']}S, BMS ≥ {vv['i_bms']:.0f} A cont. (total); bornes cubiertos; caja estanca elevada",
         f"{m['battery_desc']} (B-BAT)", "[CALCULADO: selección de sizing (inputs.yaml battery)]"],
        ["F1", "Fusible principal", f"{cab['fuse_a']:.0f} A (≥ {fmt(cab['fuse_min_a'])} A), ≥ {fmt(m['v_max'] * 1.2, 0)} V CC, a ≤ 178 mm del borne +",
         R["clase"]["fuse"] + " (B-FUSE)",
         "[CALCULADO: sizing.json electrical.fuse_a] · 178 mm [VERIFICADO: R06 §5.1 ABYC E-11] · tensión [R08a §6 / R11 §8]"],
        ["S1", "Desconectador manual", f"≥ {cab['fuse_a']:.0f} A cont., ≥ {fmt(m['v_max'], 0)} V CC, llave removible",
         "Biltema Hovedafbryder AFD 275 A 12–48 V (B-SW)" if not R["clase"]["hv"] else "desconectador ≥ 100 V CC (buscar)",
         "[VERIFICADO: R08a §3]"],
        ["K1", "Contactor MONOestable (nunca biestable)",
         f"NA, ≥ {cab['fuse_a']:.0f} A cont., corte bajo carga ≥ {fmt(m['v_max'])} V CC, bobina apta para {fmt(m['v_max'])} V CONTINUOS "
         f"y que cierre con ≤ {fmt(b['v_rest_min'])} V → bobina de {b['V_nom']:.0f} V ({fmt(m['v_max'] / b['V_nom'] * 100, 0)} % Us a carga plena), supresor diodo+R/TVS",
         f"{R['clase']['contactor']} bobina {b['V_nom']:.0f} V (B-CONT); NO relés sin corte CC publicado (p. ej. FRC3)",
         "[VERIFICADO: R06 §3.3 SW80: 48 V con corte, 8–20 ms, cierre ≤ 66 % Us] · sobretensión de bobina [CALCULADO, §7]"],
        ["R_pre", "Resistencia de precarga ∥ K1", f"{p['R_ohm']:.0f} Ω, ≥ {p['P_rating_W']:.0f} W, carcasa de Al atornillada a la base del controlador (P1-ELE-01) con disipador propio",
         "genérica (agregar a la BOM)", f"[CALCULADO] {tag('r_pre_ohm')}"],
        ["ASW", "Antichispa MOSFET (OPCIONAL)", "solo arranque suave aguas abajo de K1; falla en corto → NO es seguridad",
         "Flipsky Antispark Pro V3.0 (B-ASW)", "[VERIFICADO: R06 §3.1]"],
        ["F2", "Fusible de mando (bobina)", f"{fmt(b['F2_A'], 0)} A, portafusible en línea estanco", "genérico (agregar a la BOM)", "[CALCULADO]"],
        ["F3", "Fusible del DC-DC", "1 A, portafusible en línea", "genérico (agregar a la BOM)",
         "[SUPUESTO: protege el cable de 0,5 mm²; consumo de entrada ≈ 15 mA [ESTIMADO: 0,3 W / 25,6 V / 0,8]]"],
        ["CORDÓN", "Interruptor de hombre al agua", f"contacto CERRADO con clip (fail-safe), ≥ {fmt(b['I_max_A'] * 2, 1)} A a {fmt(m['v_max'])} V CC",
         "Watski Dødmands kontakt universal, polos M (B-KILL); alt. Sea Dog SD-420487-1",
         f"≥ [CALCULADO: 2 × I_bobina máx] · {tag('kill_switch_watski')} — nominal 12 V < {fmt(m['v_max'])} V → ensayo T0.19 (200 aperturas) · Sea Dog 5 A {tag('kill_switch_rating_a')}"],
        ["SETA", "Seta de emergencia", "NC, enclavamiento (girar para rearmar), Ø22, IP65, ≥ 1 A", "B-ESTOP", "[ESTIMADO: especificación de BOM]"],
        ["J1", "Conector IP68 del hall (caña)", "4 polos apantallado: 5 V, GND, OUT, malla", "Lumberg 0332-04 + 0322-04 (B-SIGNAL)", "[VERIFICADO: R08a §8]"],
        ["J2", "Conector IP68 del cordón (caña)", "2 polos, ≥ 1 A", "Cliffcon 68 FM686812 (B-KCONN)", "[VERIFICADO: R08a §8]"],
        ["ESC", "VESC de la selección", f"FW ≥ 5.03, l_current_max {vv['l_current_max']:.0f} A, entradas PPM y ADC2 accesibles, sensor de motor; caja de agua en el circuito de refrigeración",
         f"{m['esc_desc']} (B-ESC) — sobre base elevada P1-ELE-01 + capota P1-ELE-02", "[VERIFICADO: research/R11 §2]"],
        ["M", "Motor", "sensor de temperatura del bobinado leído por el VESC (si no trae: NTC 10 k pegado al estator)", f"{m['motor_desc']} (B-MOT)",
         "[VERIFICADO: R06 §1.2 soporte NTC] · R11 §10.4: el MTI120116 no declara sensor"],
        ["IMD", "Monitor de aislamiento", "solo clase 72 V (sistema flotante > 50 V CC)", R["clase"]["imd_desc"], "[VERIFICADO: research/R11 §8; R10b H8]"],
        ["DC-DC", "Regulador → 5 V", f"5 V ≥ 0,5 A; entrada máx. > l_max_vin = {vv['l_max_vin']:.0f} V; alimentado aguas ARRIBA de K1",
         R["clase"]["dcdc"], f"{tag('dcdc_vin_max')} · {tag('dcdc_alt_vin_max')}"],
        ["MCU", "Arduino Nano (ATmega328P, 5 V, 16 MHz)", "bootloader NUEVO (Optiboot): el viejo entra en bucle tras un reset por WDT",
         "Arduino Nano V3 (B-MCU)", "[VERIFICADO: R08a §9] · bootloader [ESTIMADO: problema conocido; se prueba en T0.18]"],
        ["HALL", "Sensor hall lineal ratiométrico 5 V + imán", "salida analógica ratiométrica; imán NdFeB Ø10×3 diametral",
         "Allegro A1324 (B-HALL)", "[VERIFICADO: R08a §9 (sensor)]; imán [ESTIMADO]"],
        ["U1–U3", "Optoacoplador de fototransistor (×3)", f"CTR ≥ {fa(val('opto_ctr_min') * 100)} % a 5 mA, Vceo ≥ 30 V, aislación ≥ 2,5 kV",
         "genérico 4 pines (agregar a la BOM)", tag("opto_ctr_min")],
        ["D_U1–D_U3", "Diodo antiparalelo de cada LED de opto",
         f"1N4148 o similar (≥ 75 V, ≥ 100 mA), cátodo al ánodo del LED: limita la tensión inversa a ≈ 0,7 V (sin él: {fmt(-b['V_N2_negativo_V'])} V)",
         "genérico (agregar a la BOM)", "[CALCULADO, §7]"],
        ["R1 / R2", "R serie de los LED de U1 / U2+U3",
         f"{o['R_U1_ohm'] / 1000:.1f} kΩ / {o['R_U2U3_ohm'] / 1000:.1f} kΩ, 0,5 W".replace(".", ","), "genéricas", "[CALCULADO]"],
        ["Q_EN", "Transistor de habilitación (ADC2 del VESC)", "NPN Vceo ≥ 30 V, Ic ≥ 50 mA; base 1 kΩ desde D4 y 10 kΩ a GND",
         "genérico", "[SUPUESTO]"],
        ["Pasivos", "Pull-ups y filtros", "D2/D3: 10 kΩ a 5 V + 100 nF; ADC2: 10 kΩ a 3,3 V; A0: 1 kΩ + 100 nF + 100 kΩ a GND; PPM: 10 kΩ a GND",
         "genéricos", f"{tag('pullup_ohm')} · {tag('rc_filter_s')}"],
        ["LED", "LED de estado de panel", "IP67, 5 V con resistencia", "genérico", "[SUPUESTO]"],
        ["Cables", "Potencia / mando / señal",
         f"DC {cab['dc_mm2']} mm², fases {cab['phase_mm2']} mm² (estañados); mando 0,75–1 mm² estañado; hall: 4 × 0,25 mm² apantallado redondo; cordón: 2 × 0,75 mm² redondo",
         "Skyllermarks estañado (B-CAB-DC, B-CAB-PH)", "[CALCULADO: sizing.json cables] · mando/señal [SUPUESTO]"],
        ["Prensaestopas", "Pasamuros IP68", f"caja de batería: un cable REDONDO por prensaestopas, M32 para {cab['dc_mm2']} mm² [ESTIMADO: Ø ext ≈ 17 mm]; M16 4–8 mm (hall, cordón) en la consola",
         "Biltema M32 / M16 (B-GLAND)", "[VERIFICADO: R08a §8] · regla de un cable [ESTIMADO: R05 §B8]"],
    ])
    B["firmware"] = md_table(["Parámetro (`tl_config_t`)", "Valor por defecto", "Etiqueta"],
                             [[f"`{n_}`", v_, g_] for n_, v_, g_ in firmware_defaults()])
    c = R["corte"]
    B["corte"] = md_table(["Camino de corte (cada uno por separado)", "t [ms] [CALCULADO]", "Base", f"< {fmt(c['requisito_s'])} s"],
                          [[k, f"{v['t_s'] * 1e3:.0f}", v["base"], "✔" if v["ok"] else "✘"] for k, v in c["caminos"].items()])
    B["corte"] += (f"\n\nRequisito {fmt(c['requisito_s'])} s [VERIFICADO: inputs.yaml electrical.kill_switch_response_s_max]; "
                   f"peor camino individual **{c['peor_s'] * 1e3:.0f} ms** [CALCULADO]. El corte real es el del camino más rápido "
                   "que siga sano; el requisito se exige a cada camino por separado.")
    hdr = ["Caso", "Cordón", "Seta", "Descon.", "F1", "F2", "K1", "MCU armado", "Timeout VESC", "Falla sensor",
           "Motor", "Barreras activas (mín–máx)", "Comb."]
    rows = []
    for r in R["tabla_resumen"]:
        rows.append([r["caso"], r["cordon"], r["seta"], r["desconectador"], r["F1"], r["F2"], r["K1"], r["MCU_armado"],
                     r["timeout_VESC"], r["falla_sensor"], f"**{r['motor']}**",
                     f"{r['barreras_min']}–{r['barreras_max']}: {r['barreras']}", r["n_combinaciones"]])
    n = len(R["tabla_verdad"])
    ng = sum(1 for r in R["tabla_verdad"] if r["motor"] != "PARADO")
    B["verdad"] = md_table(hdr, rows) + (
        f"\n\nEnumeración completa: **{n} combinaciones** en [`tabla_verdad.csv`](tabla_verdad.csv) "
        f"(1 = cerrado/sano/sí, 0 = abierto/fundido/no; \"–\" = cualquier valor). El motor puede girar en **{ng}** "
        "de ellas: todas exigen cordón, seta, desconectador, F1, F2, MCU armado, PPM válido y sensor sano; "
        "la única variable libre es K1 (normal o soldado): un K1 soldado no se nota en marcha → se prueba antes de cada salida.")
    return B


def firmware_defaults():
    """Lee los valores por defecto y sus etiquetas de tl_default_config() en throttle_logic.c."""
    src = (HERE / "firmware" / "throttle_logic.c").read_text(encoding="utf-8")
    body = src[src.index("void tl_default_config"):src.index("uint8_t tl_config_check")]
    rows = []
    for m in re.finditer(r"c->(\w+)\s*=\s*([^;]+);\s*(?:/\*\s*(.*?)\s*\*/)?", body):
        name, expr, comment = m.group(1), m.group(2).strip(), (m.group(3) or "")
        mv = re.match(r"TL_MV_TO_ADC\((\d+)u?\)", expr)
        if mv:
            mvv = int(mv.group(1))
            expr = f"{mvv / 1000:.2f} V → {(mvv * 1023 + 2500) // 5000} cuentas".replace(".", ",")
        else:
            expr = expr.rstrip("uf").replace(".", ",")
        tg = re.search(r"\[.*\]", comment)
        rows.append((name, expr, tg.group(0) if tg else ("[ESTIMADO: provisorio tipo SS49E; lo reemplaza la calibración (T0.5); con cal_valid = 0 no arma]" if name.startswith("adc_") else "—")))
    return rows


def write_csv(R):
    buf = io.StringIO()
    cols = list(R["tabla_verdad"][0].keys())
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in R["tabla_verdad"]:
        w.writerow(r)
    return buf.getvalue()


def update_readme(txt, B):
    pat = re.compile(r"(<!-- ELEC:(\w+) -->)(.*?)(<!-- /ELEC:\2 -->)", re.S)

    def rb(m):
        name = m.group(2)
        if name not in B:
            return m.group(0)
        return f"{m.group(1)}\n{B[name]}\n{m.group(4)}"

    return pat.sub(rb, txt)


def to_json(R):
    R2 = {k: v for k, v in R.items() if k != "tabla_verdad"}
    return json.dumps(R2, indent=2, ensure_ascii=False, default=float) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    R = compute()
    B = blocks(R)
    outs = {HERE / "electronica.json": to_json(R), HERE / "tabla_verdad.csv": write_csv(R)}
    readme = HERE / "README.md"
    if readme.exists():
        outs[readme] = update_readme(readme.read_text(encoding="utf-8"), B)
    stale = [p.name for p, t in outs.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
    if check:
        print("calc_electronica --check:", "OK" if not stale else f"DESACTUALIZADO: {stale}")
        return 1 if stale else 0
    for p, t in outs.items():
        p.write_text(t, encoding="utf-8")
    c = R["corte"]
    print(f"calc_electronica: VESC {len(R['vesc'])} parámetros; tabla de verdad {len(R['tabla_verdad'])} filas; "
          f"peor camino de corte {c['peor_s'] * 1e3:.0f} ms (req. {c['requisito_s']} s); actualizados: {stale or 'nada'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
