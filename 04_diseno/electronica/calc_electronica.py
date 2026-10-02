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
    "n_vs_power_exp": (1 / 3, "—", "[CALCULADO: bomba P ∝ n³ → n ∝ P^(1/3); con batería llena el límite de corriente de batería deja P × V_máx/V_nom]"),
    "lead_motor": ((13.30e-6, 0.30), "m², m", "[VERIFICADO: página Maytech MTI120116 — '6AWGx300mm'; 6 AWG = 13,30 mm² CALCULADO (fórmula AWG)]"),
    "lead_esc": ((8.37e-6, 0.20), "m², m", "[VERIFICADO: página Flipsky FSESC 75350 — 'Motor wire: 8AWG' (8 AWG = 8,37 mm² CALCULADO)]; largo 0,20 m [ESTIMADO: no publicado, medir]"),
    "v_cell_max": (3.65, "V", f"[ESTIMADO: {R06} §4.3, LFP 3,65 V/celda máx.]"),
    "v_cell_nom": (3.2, "V", f"[ESTIMADO: {R06} §4.3, LFP 3,2 V/celda nominal]"),
    "v_cell_cut_start": (3.0, "V", f"[ESTIMADO: {R06} §2.4, corte LFP 3,0 V/celda]"),
    "v_cell_cut_end": (2.8, "V", f"[ESTIMADO: {R06} §2.4, corte LFP 2,8 V/celda]"),
    "c_bus_f": (2.0e-3, "F", f"[ESTIMADO: {R06} §3.4, C de bus del VESC 1–2 mF no publicado; se toma el mayor]"),
    "r_pre_ohm": (100.0, "Ω", f"[SUPUESTO: {R06} §3.4 (100 Ω → 5τ ≤ 1 s)]"),
    "k1_model": ("TE Connectivity KILOVAC EV200AAANA", "—",
                 "[VERIFICADO: hoja EV200 Series (TE, 'KILOVAC EV200 Series Contactor', https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5986/EV200_Series.pdf)]"),
    "k1_i_cont_a": (500.0, "A", "[VERIFICADO: hoja EV200 — 500 A @ 85 °C (400 mcm); 12–900 V CC]"),
    "k1_coil_range_v": ((9.0, 36.0), "V", "[VERIFICADO: hoja EV200 — bobina 'A' 9–36 V CC (opera), pickup máx. 9 V, dropout mín. 6 V]"),
    "k1_coil_hold_a": (0.13, "A", "[VERIFICADO: hoja EV200 — holding current 0,13 A @ 12 V (economizador incorporado, 1,7 W)]"),
    "k1_coil_inrush": ((3.8, 0.130), "A, s", "[VERIFICADO: hoja EV200 — inrush máx. 3,8 A, inrush time máx. 130 ms]"),
    "k1_release_ms": (12.0, "ms", "[VERIFICADO: hoja EV200 — release (incluye arco) máx. 12 ms @ 2000 A; close típ. 15 ms]"),
    "k1_back_emf_v": (0.0, "V", "[VERIFICADO: hoja EV200 — 'built-in coil economizer … limits back EMF to 0V']"),
    "k1_price_eur": (149.0, "EUR sin IVA", "[VERIFICADO: https://eveurope.eu/en/product/hoofdstroomrelais-ev200-500-amp-2/ — 149,00 € ex. VAT, 54 en stock, 2026-10-02]"),
    "v_ctl_nom": (12.0, "V", "[VERIFICADO: Mean Well RSD-60-SPEC (2026-07-09) — RSD-60L-12: 12 V, 5 A, entrada 18–72 V CC]; mando de K1 a 12 V (auditoría H3, R2-E1)"),
    "v_ctl_tol": (0.02, "—", "[VERIFICADO: Mean Well RSD-60-SPEC (2026-07-09) — tolerancia de salida ±2,0 %]"),
    "rsd_vin": ((18.0, 72.0), "V", "[VERIFICADO: Mean Well RSD-60-SPEC (2026-07-09) — 'VOLTAGE RANGE CONTINUOUS' L: 18 ~ 72 VDC (G: 9 ~ 36 VDC: NO sirve con 12S)]"),
    "rsd_i_out_a": (5.0, "A", "[VERIFICADO: Mean Well RSD-60-SPEC (2026-07-09) — RSD-60L-12 5 A; sobrecarga 105–135 % con limitación de corriente constante]"),
    "rsd_idle_w": ((0.5, 1.5), "W", "[ESTIMADO: consumo en vacío de un DC-DC aislado de 60 W; la ficha no lo publica — medir en T0.4]"),
    "bilge_i_a": ((2.0, 8.0), "A", "[ESTIMADO: Attwood Sahara S500 ≈ 2 A en marcha y ~4× en el arranque (motor CC); la ficha no se abrió]"),
    "k1_hold_min_v": (7.5, "V", "[VERIFICADO: hoja EV200 — Hold Voltage (Min.) 7,5 V CC (bobina 'A')]"),
    "hold_target_v": (9.0, "V", "[SUPUESTO: no bajar de 9 V (pickup máx. de la hoja EV200) durante el hueco: margen de 1,5 V sobre la retención mínima]"),
    "hold_t_s": (0.25, "s", "[SUPUESTO: hueco del riel de 12 V al arrancar la bomba de achique contra el límite de corriente del DC-DC (arranque < 0,1 s × 2,5); lo valida T0.4]"),
    "schottky_vf": (0.5, "V", "[ESTIMADO: Schottky 3 A (1N5822) a 0,2 A]"),
    "cap_std_mf": ((4.7, 6.8, 10.0, 15.0, 22.0, 33.0, 47.0), "mF", "[SUPUESTO: valores comerciales de electrolíticos ≥ 25 V]"),
    "batt_r_int_ohm": ((0.010, 0.050), "Ω", "[ESTIMADO: LiTime no publica la R interna (página 2026-10-02); 0,050 Ω = Power Queen 24 V 50 Ah 'R int. ≤ 40 mΩ' (R08a, VERIFICADO) escalada a 12S 60 Ah; 0,010 Ω = 12 celdas prismáticas de 60 Ah de ≈ 0,5 mΩ + BMS y bornes]"),
    "mrbf_aic_a": (2000.0, "A", "[VERIFICADO: research/R06_electrica.md §5.4 — MRBF 10 kA @ 14 V / 5 kA @ 32 V / 2 kA @ 58 V]"),
    "classt_aic_a": (20000.0, "A", "[VERIFICADO: Blue Sea 5113 Class T — '20,000 Ampere Interrupt Capacity (AIC)', 160 V CC máx. (fisheriessupply.com, 2026-10-02)]"),
    "brake_frac": (0.3, "—", "[SUPUESTO: corriente de frenado = 30 % de l_current_max (un jet casi no regenera; protege BMS)]"),
    "weed_rev_frac": (0.25, "—", "[SUPUESTO: giro inverso lento (≤ 25 % de las rpm de 5 kn) solo para soltar algas de la rejilla]"),
    "pump_P_T_exp": (1.5, "—", "[CALCULADO: bomba con T ∝ n², P ∝ n³ → P ∝ T^1,5; límite de par = P_frac^(2/3)]"),
    "opto_vr_max": (5.0, "V", "[ESTIMADO: V_R máx. del LED de optoacopladores de fototransistor típicos 5–6 V; verificar en la hoja del elegido]"),
    "diode_vf": (0.7, "V", "[ESTIMADO: diodo de silicio]"),
    "vih_frac": (0.6, "—", "[ESTIMADO: V_IH mín. ATmega328P = 0,6·Vcc (hoja de datos; no releída en esta sesión)]"),
    "vesc_iq_unknown": (None, "A", "[SUPUESTO: el consumo en reposo del VESC 75100 no está publicado; se mide en T0.3]"),
    "kill_switch_rating_a": (5.0, "A", f"[VERIFICADO: Sea Dog SD-420487-1, 5 A máx. ({R06} §3.2)]"),
    "f2_factor": (1.25, "—", "[SUPUESTO: fusible de mando (lento) ≥ 1,25 × corriente de cierre de la bobina]"),
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
    # rpm a fondo con batería llena: el límite de corriente de batería deja P × V_máx/V_nom → n ∝ P^(1/3)
    n_full = n_max * (v_max / v_nom) ** val("n_vs_power_exp")
    erpm_tech_ok = erpm_tech / pp > n_full
    erpm_legal = sz.get('legal_speed', {}).get('erpm_cap')
    if erpm_legal:
        erpm_max = min(erpm_max, int(erpm_legal // 100 * 100))   # modo costa (D-30): 5 kn a < 300 m
    erpm_min = -round(n_rev * pp, -2)
    i_in_max = ceil_to(val("i_in_margin") * i_bat_pk, 5.0)
    n_par = int(bat.get("parallel", 1))
    share = el.get("parallel_share_max", 1.0) if n_par > 1 else 1.0     # reparto peor entre ramas en paralelo
    i_bms_branch = i_bms / n_par
    i_in_cap_derate = val("bms_frac") * i_bms                          # 80 % del BMS total (reparto perfecto)
    i_in_cap_share = i_bms_branch / share                              # 100 % del BMS de la rama más cargada
    i_in_cap = min(i_in_cap_derate, i_in_cap_share)
    i_in_limited = i_in_max > i_in_cap
    i_in_max = min(i_in_max, i_in_cap)
    i_branch_at_limit = share * i_in_max                               # rama más cargada con el VESC al límite
    cut_start = round(cells * val("v_cell_cut_start"), 1)
    cut_end = round(cells * val("v_cell_cut_end"), 1)
    max_vin = round(val("v_max_vin_factor") * v_max, 0)
    rows = []

    def add(group, name, value, unit, default, t, note=""):
        rows.append({"grupo": group, "parametro": name, "valor": value, "unidad": unit,
                     "default": default, "tag": t, "nota": note})

    esc_o = inp["esc"]["options"][sel["esc"]]
    fw_fac = esc_o.get("fw_factory")
    add("Firmware", "versión de firmware", "≥ 6.00", "—", fw_fac or "—",
        f"[VERIFICADO: {R06} §2.2 — KILL_SW_MODE aparece en 5.03] · ≥ 6.00 por LispBM (vesc_perfil.lisp) "
        f"[VERIFICADO: vedderb/bldc lispBM/README.md, FW 6.00+]"
        + (f" · de fábrica {fw_fac} [inputs.yaml esc.options.{sel['esc']}.fw_factory, allí VERIFICADO]" if fw_fac else ""),
        "FLASHEAR antes de configurar (T0.0): con el FW de fábrica no hay LispBM y el perfil COSTA/ABIERTO no funciona"
        if fw_fac and float(fw_fac) < 6.0 else "")
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
        f"[CALCULADO: ⌈{fa(val('i_in_margin'))} × I_bat pico {fa(round(i_bat_pk, 1))} A⌉ a 5 A, ≤ mín({fa(val('bms_frac') * 100)} % × BMS {fa(i_bms)} A = "
        f"{fa(i_in_cap_derate)} A; BMS de rama {fa(i_bms_branch)} A / reparto {fa(share)} = {fa(round(i_in_cap_share, 1))} A)] · "
        f"reparto [inputs.yaml electrical.parallel_share_max, allí SUPUESTO]",
        ("LIMITA la V máx: I_bat pico de sizing > límite" if i_in_limited else
         f"No limita el pico de sizing ({fa(round(i_bat_pk, 1))} A)")
        + (f". Con {n_par} baterías en paralelo y reparto {fa(share * 100)}/{fa(100 - share * 100)} la rama más cargada lleva "
           f"{fa(round(i_branch_at_limit, 1))} A = {fa(round(i_branch_at_limit / i_bms_branch * 100, 0))} % de su BMS ({fa(i_bms_branch)} A): "
           f"no supera el BMS, pero el margen del 80 % solo vale con reparto parejo. Medir el reparto en T1 (pinza en cada rama)"
           if n_par > 1 else ""))
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
        f"[CALCULADO: KV {mot['kv_rpm_v']:.0f} × {fa(v_max)} V]; el límite lo baja a {erpm_max / pp:.0f} rpm. "
        f"ERPM = rpm × {pp:.0f} pares de polos [inputs.yaml motor.options.{sel['motor']}.pole_pairs]")
    if erpm_max < erpm_tech:
        add("Velocidad", "l_max_erpm (perfil 2: fuera de la franja de 300 m)", erpm_tech, "ERPM", 100000,
            f"[CALCULADO: {fa(val('erpm_margin'))} × {n_max:.0f} rpm (n máx. de sizing) × {pp:.0f} pares de polos]",
            f"Perfil ABIERTO (vesc_perfil.lisp, en RAM); por defecto arranca SIEMPRE en COSTA (5 kn, R13). "
            f"{'✔' if erpm_tech_ok else '✘ NO ALCANZA:'} {erpm_tech / pp:.0f} rpm > {n_full:.0f} rpm a fondo con batería llena "
            f"[CALCULADO: {n_max:.0f} × ({fa(v_max)}/{fa(v_nom)})^(1/3)] — el tope no recorta la V máx.")
    cav = sz.get("cavitation_cap")
    if cav:
        add("Velocidad", "tope de cavitación (NO se programa)", round(cav["erpm"], -2), "ERPM", "—",
            f"[CALCULADO: sizing.cavitation_cap — {cav['rpm']:.0f} rpm con S ≤ {cav['S_lim']:.1f} a punto fijo × {cav['pole_pairs']:.0f} pares de polos]",
            f"A punto fijo el límite de corriente ya deja el impulsor en S ≈ {cav['S_lim']:.1f} (sizing); a velocidad la inmersión "
            f"y la presión de toma suben y S baja. Un tope fijo de ERPM recortaría la V máx. por ratos a "
            f"{cav['vmax_peak_capped_kmh']:.1f} km/h, por eso no se programa: verificar en T2 (sin ruido de cavitación a punto fijo)")
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
        "Bucket, dwell y el único giro inverso (limpieza de rejilla) los gestiona el MCU (§5); alternativa DUTY si la bomba cavita (R06 §2.6)")
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
                        "dcdc_vin_max": val("dcdc_vin_max"), "dcdc_ok": max_vin < val("dcdc_vin_max"),
                        "n_full_batt_rpm": n_full, "erpm_tech_ok": erpm_tech_ok, "n_parallel": n_par,
                        "parallel_share_max": share, "i_bms_branch": i_bms_branch, "i_in_cap_derate": i_in_cap_derate,
                        "i_in_cap_share": i_in_cap_share, "i_branch_at_limit": i_branch_at_limit,
                        "fw_min": "6.00", "fw_factory": fw_fac}

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

    # ---------------- Bobina del contactor y circuito de mando (12 V desde B-12V, auditoría H3)
    vctl = val("v_ctl_nom")
    vctl_lo, vctl_hi = vctl * (1 - val("v_ctl_tol")), vctl * (1 + val("v_ctl_tol"))
    c_lo, c_hi = val("k1_coil_range_v")
    i_hold = val("k1_coil_hold_a")
    i_inr, t_inr = val("k1_coil_inrush")
    p_hold = vctl * i_hold
    e_usable = sz["energy"]["E_usable_wh"]
    t_end = inp["operation"]["mission_fast_h"] + inp["operation"]["mission_legal_h"]
    f2 = next(x for x in (0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0) if x >= val("f2_factor") * i_inr)
    ks_v, ks_a = val("kill_switch_watski")
    R["bobina"] = {
        "modelo": val("k1_model"), "V_nom": vctl, "V_ctl_range": (vctl_lo, vctl_hi), "V_coil_range": (c_lo, c_hi),
        "coil_ok": c_lo <= vctl_lo and vctl_hi <= c_hi, "I_hold_A": i_hold, "I_inrush_A": i_inr, "t_inrush_s": t_inr,
        "I_max_A": i_inr, "P_hold_W": p_hold,
        "E_mision_Wh": p_hold * t_end, "endurance_h": t_end, "frac_E_usable": p_hold * t_end / e_usable,
        "F2_A": f2, "kill_switch_rating_A": val("kill_switch_rating_a"),
        "kill_switch_margin": val("kill_switch_rating_a") / i_inr,
        "watski_V_A": (ks_v, ks_a), "watski_ok": vctl <= ks_v * (1 + val("v_ctl_tol")) + 1e-9 and i_inr <= ks_a,
        "release_ms": val("k1_release_ms"), "back_emf_V": val("k1_back_emf_v"),
        "k1_i_cont_A": val("k1_i_cont_a"), "precio_eur_sin_iva": val("k1_price_eur"),
    }
    # tensión en N1/N2 al abrir: el economizador limita la fuerza contraelectromotriz a 0 V (hoja EV200)
    v_n2_neg = -val("k1_back_emf_v")
    R["bobina"]["V_N2_negativo_V"] = v_n2_neg

    # ---------------- Retención de la bobina ante huecos del riel de 12 V (R2-E2): Schottky + C aguas arriba de seta/cordón
    i_leds = 3 * 6e-3                                                       # 3 LED de opto ≈ 6 mA c/u (§7)
    p_node = p_hold + vctl * i_leds
    v0 = vctl_lo - val("schottky_vf")
    vt = val("hold_target_v")
    c_req = 2 * p_node * val("hold_t_s") / (v0 ** 2 - vt ** 2)
    c_sel = next(x for x in val("cap_std_mf") if x / 1000 >= c_req)
    t_hold_real = 0.5 * c_sel / 1000 * (v0 ** 2 - vt ** 2) / p_node
    R["retencion"] = {"P_nodo_W": p_node, "V0_V": v0, "V_objetivo_V": vt, "V_hold_min_V": val("k1_hold_min_v"),
                      "t_hueco_s": val("hold_t_s"), "C_req_F": c_req, "C_sel_mF": c_sel, "t_cubierto_s": t_hold_real,
                      "I_rsd_A": val("rsd_i_out_a"), "I_bomba_A": val("bilge_i_a")}
    # consumo en reposo (bote amarrado): B-12V está aguas arriba de S1
    idle_lo, idle_hi = val("rsd_idle_w")
    R["reposo"] = {"P_dcdc_W": (idle_lo, idle_hi), "P_bobina_clip_W": p_hold,
                   "dias_sin_clip": (e_usable / idle_hi / 24, e_usable / idle_lo / 24),
                   "dias_con_clip": (e_usable / (idle_hi + p_hold) / 24, e_usable / (idle_lo + p_hold) / 24)}

    # ---------------- Optoacopladores (sensado de N1/N2 hacia el MCU y habilitación de ADC2)
    vf, ift = val("opto_vf"), val("opto_if_target")
    r2 = e_series((vctl - 2 * vf) / ift)   # U2 + U3 en serie (nodo N2, mando de 12 V)
    r1 = e_series((vctl - vf) / ift)       # U1 (nodo N1)
    i_lo = (vctl_lo - 2 * vf) / r2
    R["optos"] = {
        "R_U2U3_ohm": r2, "I_U2U3_A": ((vctl_lo - 2 * vf) / r2, (vctl_hi - 2 * vf) / r2),
        "P_R_U2U3_W": (vctl_hi - 2 * vf) ** 2 / r2,
        "R_U1_ohm": r1, "I_U1_A": ((vctl_lo - vf) / r1, (vctl_hi - vf) / r1), "P_R_U1_W": (vctl_hi - vf) ** 2 / r1,
        "Ic_min_A": val("opto_ctr_min") * i_lo, "I_pullup_5V_A": 5.0 / val("pullup_ohm"),
        "I_pullup_3V3_A": 3.3 / val("pullup_ohm"),
        "V_inversa_LED_V": -v_n2_neg, "V_R_max_V": val("opto_vr_max"),
        "necesita_diodo_antiparalelo": -v_n2_neg > val("opto_vr_max"),
        "I_diodo_antiparalelo_A": max(0.0, (-v_n2_neg - 2 * val("diode_vf")) / r2),
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
            (val("k1_release_ms") / 1000, f"release máx. de {val('k1_model')} (economizador incorporado) {tag('k1_release_ms')}"),
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
    (a_m, l_m), (a_e, l_e) = val("lead_motor"), val("lead_esc")
    r_leads = el["rho_cu_ohm_m"] * (l_m / a_m + l_e / a_e)
    i_ph_lim = elc["I_phase_limit_A"]
    r_lo, r_hi = val("batt_r_int_ohm")
    isc_one = (v_max / r_hi, v_max / r_lo)                     # una batería (falla en su cable de rama)
    n_p = int(bat.get("parallel", 1))
    isc_all = (n_p * isc_one[0], n_p * isc_one[1])              # todas (falla aguas abajo de F1)
    R["cortocircuito"] = {"R_int_ohm": (r_lo, r_hi), "I_sc_bateria_A": isc_one, "I_sc_total_A": isc_all,
                          "MRBF_AIC_A": val("mrbf_aic_a"), "ClassT_AIC_A": val("classt_aic_a"),
                          "MRBF_ok": isc_all[1] <= val("mrbf_aic_a"), "ClassT_ok": isc_all[1] <= val("classt_aic_a")}
    R["cables"] = {"dc_mm2": elc["cable_dc"]["section_mm2"], "phase_mm2": elc["cable_phase"]["section_mm2"],
                   "fuse_branch_a": elc.get("fuse_branch_a", elc["fuse_a"]), "n_parallel": elc.get("n_parallel", 1),
                   "R_phase_leads_ohm": r_leads, "I_phase_limit_A": i_ph_lim,
                   "phase_drop_leads_frac": 2 * i_ph_lim * r_leads / v_nom,
                   "dc_drop_frac": elc["cable_dc"]["drop_frac"], "phase_drop_frac": elc["cable_phase"]["drop_frac"],
                   "fuse_a": elc["fuse_a"], "fuse_min_a": el["fuse_factor"] * elc["I_bat_top_A"],
                   "ampacity_dc_a": elc["cable_dc"]["ampacity_a"], "fuse_protects_cable": elc.get("fuse_protects_cable")}
    # clase de tensión → contactor, fusible, aislamiento (R10b H8, R11 §8)
    hv = v_class >= 72 or v_max > 60.0
    R["clase"] = {"v_class": v_class, "hv": hv, "imd": hv,
                  "contactor": val("k1_model").replace("TE Connectivity ", ""),
                  "fuse": "fusible ≥ 100 V CC (buscar: Littelfuse CNN 125 V / clase T 125 VDC)" if hv else
                          "Class T Blue Sea (160 V CC, 20 kA) en portafusible Class T con tapa",
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
    # mando de K1 a 12 V desde B-12V (conectado en la barra +, aguas ARRIBA de F1/S1): no depende de S1 ni de F1
    n1 = bool(F2 and seta)                           # nodo entre seta y cordón (opto U1 → D3)
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
    sc = R["cortocircuito"]
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
        ["Bobina K1", f"{b['modelo']}: bobina 9–36 V con economizador, alimentada a {fmt(b['V_nom'], 0)} V "
                      f"({fmt(b['V_ctl_range'][0])}–{fmt(b['V_ctl_range'][1])} V) desde B-12V → "
                      f"{'✔ dentro de' if b['coil_ok'] else '✘ FUERA de'} {fmt(b['V_coil_range'][0], 0)}–{fmt(b['V_coil_range'][1], 0)} V; "
                      f"cierre {fmt(b['I_inrush_A'])} A ≤ {fmt(b['t_inrush_s'] * 1e3, 0)} ms, retención {fmt(b['I_hold_A'], 2)} A = {fmt(b['P_hold_W'], 2)} W",
         f"{tag('k1_coil_range_v')} · {tag('k1_coil_hold_a')} · {tag('k1_coil_inrush')} · {tag('v_ctl_nom')} · {tag('v_ctl_tol')}"],
        ["Apertura de K1 / fuerza contraelectromotriz", f"≤ {fmt(b['release_ms'], 0)} ms; N1/N2 no bajan de {fmt(b['back_emf_V'], 0)} V al abrir (sin supresor externo)",
         f"{tag('k1_release_ms')} · {tag('k1_back_emf_v')}"],
        ["Consumo de bobina en la misión ({} h)".format(fmt(b["endurance_h"], 2)), f"{fmt(b['E_mision_Wh'], 2)} Wh = {fmt(b['frac_E_usable'] * 100, 2)} % de la energía usable (sizing)",
         "[CALCULADO: P_retención × t]; con el bote amarrado y el clip PUESTO la bobina sigue tomando esa potencia (B-12V está aguas arriba de S1): sacar el clip al dejar el bote"],
        ["Fusible de mando F2 (salida de B-12V, lento)", f"{fmt(b['F2_A'], 0)} A", f"[CALCULADO: primer valor normalizado ≥ {fmt(val('f2_factor'), 2)} × I de cierre {fmt(b['I_inrush_A'])} A] · factor {tag('f2_factor')}"],
        ["Interruptor de cordón (Watski 12 V – 15 A) en el mando de 12 V",
         f"{'✔' if b['watski_ok'] else '✘'} {fmt(b['V_nom'], 0)} V ≤ {fmt(b['watski_V_A'][0], 0)} V nominal; cierre {fmt(b['I_inrush_A'])} A ≤ {fmt(b['watski_V_A'][1], 0)} A; "
         f"abre {fmt(b['I_hold_A'], 2)} A sin sobretensión inductiva (economizador). Alternativa Sea Dog 5 A: margen {fmt(b['kill_switch_margin'])}× sobre el cierre",
         f"{tag('kill_switch_watski')} · {tag('kill_switch_rating_a')}"],
        ["R serie de U2+U3 (nodo bobina)", f"{o['R_U2U3_ohm']:.0f} Ω, {fmt(o['I_U2U3_A'][0] * 1e3)}–{fmt(o['I_U2U3_A'][1] * 1e3)} mA, P {fmt(o['P_R_U2U3_W'], 2)} W → 0,25 W",
         f"[CALCULADO: E12 ≤ (12 V − 2·Vf)/I, mando de 12 V] {tag('opto_vf')}"],
        ["R serie de U1 (nodo seta)", f"{o['R_U1_ohm']:.0f} Ω, {fmt(o['I_U1_A'][0] * 1e3)}–{fmt(o['I_U1_A'][1] * 1e3)} mA, P {fmt(o['P_R_U1_W'], 2)} W → 0,25 W",
         "[CALCULADO]"],
        ["Tensión inversa en los LED de U1–U3 al abrir la bobina",
         f"N2 → {fmt(b['V_N2_negativo_V'], 0)} V (economizador de K1) vs V_R máx. {fmt(o['V_R_max_V'], 0)} V → "
         + ("**diodo 1N4148 en antiparalelo con cada LED** (conduce " + fmt(o['I_diodo_antiparalelo_A'] * 1e3) + " mA de pico por R2)"
            if o["necesita_diodo_antiparalelo"] else
            "no hace falta diodo con el EV200; se deja el 1N4148 antiparalelo como protección si se reemplaza K1 por uno sin economizador"),
         f"{tag('k1_back_emf_v')} · {tag('opto_vr_max')}"],
        ["Precarga con el consumo en reposo del VESC",
         f"I_q ≤ {fmt(p['Iq_max_90pct_A'] * 1e3)} mA para llegar al 90 % con K1 abierto; al 80 % la energía del cierre de K1 es {fmt(p['E_cierre_80pct_J'] * 1e3, 0)} mJ",
         f"[CALCULADO: 0,1·V_nom/R; ½·C·(0,2·V_nom)²] · {tag('vesc_iq_unknown')}"],
        ["Corriente de colector mínima (CTR 50 %) vs pull-up", f"{fmt(o['Ic_min_A'] * 1e3, 2)} mA ≫ {fmt(o['I_pullup_5V_A'] * 1e3, 2)} mA (5 V) / {fmt(o['I_pullup_3V3_A'] * 1e3, 2)} mA (3,3 V)",
         f"[CALCULADO] {tag('opto_ctr_min')}"],
        ["Retención de la bobina (hueco del riel de 12 V al arrancar el achique)",
         f"P del nodo {fmt(R['retencion']['P_nodo_W'], 2)} W (bobina + 3 LED), de {fmt(R['retencion']['V0_V'], 2)} V a {fmt(R['retencion']['V_objetivo_V'], 1)} V en "
         f"{fmt(R['retencion']['t_hueco_s'], 2)} s → C ≥ {fmt(R['retencion']['C_req_F'] * 1e3, 1)} mF → **{fmt(R['retencion']['C_sel_mF'], 0)} mF** "
         f"(cubre {fmt(R['retencion']['t_cubierto_s'], 2)} s); bomba {fmt(R['retencion']['I_bomba_A'][0], 0)}–{fmt(R['retencion']['I_bomba_A'][1], 0)} A vs DC-DC {fmt(R['retencion']['I_rsd_A'], 0)} A con límite de corriente",
         f"[CALCULADO: C = 2·P·t / (V0² − V²)] · {tag('k1_hold_min_v')} · {tag('hold_target_v')} · {tag('hold_t_s')} · {tag('schottky_vf')} · {tag('bilge_i_a')} · {tag('rsd_i_out_a')}"],
        ["Consumo en reposo (bote amarrado, S1 abierto)",
         f"DC-DC {fmt(R['reposo']['P_dcdc_W'][0], 1)}–{fmt(R['reposo']['P_dcdc_W'][1], 1)} W → la energía usable dura {R['reposo']['dias_sin_clip'][0]:.0f}–{R['reposo']['dias_sin_clip'][1]:.0f} días; "
         f"con el clip PUESTO (+{fmt(R['reposo']['P_bobina_clip_W'], 2)} W de bobina) {R['reposo']['dias_con_clip'][0]:.0f}–{R['reposo']['dias_con_clip'][1]:.0f} días. "
         "Invierno: sacar F5 (y los F_BR) y guardar la batería a carga de almacenamiento",
         f"[CALCULADO: E usable de sizing / P] · {tag('rsd_idle_w')}"],
        ["Cortocircuito presunto (bornes de batería, sin cable)",
         f"una batería {fmt(sc['I_sc_bateria_A'][0] / 1000, 1)}–{fmt(sc['I_sc_bateria_A'][1] / 1000, 1)} kA; las {cab['n_parallel']} en paralelo "
         f"{fmt(sc['I_sc_total_A'][0] / 1000, 1)}–{fmt(sc['I_sc_total_A'][1] / 1000, 1)} kA vs MRBF {fmt(sc['MRBF_AIC_A'] / 1000, 0)} kA a 58 V "
         f"({'✔' if sc['MRBF_ok'] else '✘ NO alcanza'}) y Class T {fmt(sc['ClassT_AIC_A'] / 1000, 0)} kA ({'✔' if sc['ClassT_ok'] else '✘'}) → F1 y F_BR Class T",
         f"[CALCULADO: V_máx / R_int] · {tag('batt_r_int_ohm')} · {tag('mrbf_aic_a')} · {tag('classt_aic_a')}"],
        ["Fusibles F1 (barra +) / F_BR por rama / cable DC", f"{R['cables']['fuse_a']:.0f} A (mín. {fmt(R['cables']['fuse_min_a'])}) / "
         f"{R['cables']['n_parallel']} × {R['cables']['fuse_branch_a']:.0f} A / {R['cables']['dc_mm2']} mm²",
         "[CALCULADO: resultados/sizing.json fuse_a, fuse_branch_a (rama = reparto 60/40 × I pico), cable_dc]"],
        ["Fases ESC → motor", f"cables propios: motor 6 AWG × 300 mm a ESC 8 AWG, unión con conectores bala 8 mm (sin el tramo de "
         f"{R['cables']['phase_mm2']} mm² de sizing); caída ≈ {fmt(R['cables']['phase_drop_leads_frac'] * 100, 2)} % a {fmt(R['cables']['I_phase_limit_A'], 0)} A",
         "[CALCULADO: ρ·L/A con 6 AWG 13,3 mm² × 0,30 m + 8 AWG 8,37 mm² × 0,20 m [ESTIMADO: largo del cable del ESC no publicado]] · "
         "calibres [inputs.yaml motor/esc leads, allí VERIFICADO] · sección del tramo: §4 Cables"],
    ])
    B["componentes"] = md_table(["Ref.", "Componente", "Especificación mínima", "Elegido / referencia (BOM)", "Etiqueta"], [
        ["BAT", "Batería LiFePO4 de la selección", f"{m['cells_series']}S, BMS ≥ {vv['i_bms']:.0f} A cont. (total); bornes cubiertos; caja estanca elevada",
         f"{m['battery_desc']} (B-BAT)", "[CALCULADO: selección de sizing (inputs.yaml battery)]"],
        ["F_BR", "Fusible de rama (uno por batería)", f"{cab['n_parallel']} × {cab['fuse_branch_a']:.0f} A, ≥ {fmt(m['v_max'] * 1.2, 0)} V CC, "
         f"poder de corte ≥ {fmt(sc['I_sc_bateria_A'][1] / 1000, 1)} kA (§7), a ≤ 178 mm del borne + de CADA batería",
         "Class T Blue Sea (160 V CC, 20 kA) en portafusible Blue Sea 5007100 (110–200 A) (B-FUSE-BR, B-FUSEH-BR)",
         f"[CALCULADO: sizing.json electrical.fuse_branch_a] · 178 mm [VERIFICADO: R06 §5.1 ABYC E-11] · {tag('classt_aic_a')}"],
        ["F1", "Fusible principal (barra +)", f"{cab['fuse_a']:.0f} A (≥ {fmt(cab['fuse_min_a'])} A), ≥ {fmt(m['v_max'] * 1.2, 0)} V CC, "
         f"poder de corte ≥ {fmt(sc['I_sc_total_A'][1] / 1000, 1)} kA (§7), junto a la barra + (protege el cable de {cab['dc_mm2']} mm²)",
         R["clase"]["fuse"] + " (B-FUSE, B-FUSEH)",
         f"[CALCULADO: sizing.json electrical.fuse_a] · {tag('classt_aic_a')} · MRBF descartado: {tag('mrbf_aic_a')}"],
        ["F6", "Fusible de la toma de carga (Anderson SB50)", "32 A gPV 10×38, ≥ 1000 V CC, poder de corte ≥ 10 kA CC, en la barra +; cable ≤ 16 mm²",
         "gPV 10×38 32 A + portafusible estanco (B-CHGFUSE)", "[ESTIMADO: fusibles gPV 10×38 de 1000 V CC con poder de corte de decenas de kA (verificar en la ficha del elegido); cargador 15 A (R08a §5)]"],
        ["S1", "Desconectador manual", f"≥ {cab['fuse_a']:.0f} A cont., ≥ {fmt(m['v_max'], 0)} V CC, llave removible",
         "Biltema Hovedafbryder AFD 275 A 12–48 V (B-SW)" if not R["clase"]["hv"] else "desconectador ≥ 100 V CC (buscar)",
         "[VERIFICADO: R08a §3]"],
        ["K1", "Contactor MONOestable (nunca biestable)",
         f"NA, ≥ {cab['fuse_a']:.0f} A cont., corte bajo carga ≥ {fmt(m['v_max'])} V CC; bobina de {fmt(b['V_nom'], 0)} V del mando (B-12V), "
         f"con economizador (sin sobretensión inductiva al abrir)",
         f"{R['clase']['contactor']}: {fmt(b['k1_i_cont_A'], 0)} A, 12–900 V CC, bobina 9–36 V, retención {fmt(b['I_hold_A'], 2)} A (B-CONT)",
         f"{tag('k1_model')} · {tag('k1_i_cont_a')} · {tag('k1_price_eur')}"],
        ["R_pre", "Resistencia de precarga ∥ K1", f"{p['R_ohm']:.0f} Ω, ≥ {p['P_rating_W']:.0f} W, carcasa de Al atornillada a la base del controlador (P1-ELE-01) con disipador propio",
         "100 Ω 50 W carcasa de Al (B-RPRE)", f"[CALCULADO] {tag('r_pre_ohm')}"],
        ["ASW", "Antichispa MOSFET (NO se compra)", "solo arranque suave aguas abajo de K1; falla en corto → NO es seguridad; 100 A < I de batería",
         "Flipsky Antispark Pro V3.0 (B-ASW, qty 0)", "[VERIFICADO: R06 §3.1]"],
        ["12V", "Fuente del mando y de achique", f"DC-DC aislado → {fmt(b['V_nom'], 0)} V, entrada ≥ {fmt(m['v_max'], 1)} V y que arranque con ≤ {fmt(m['v_min_load'], 1)} V "
         f"(RSD-60L: {fmt(val('rsd_vin')[0], 0)}–{fmt(val('rsd_vin')[1], 0)} V); conectado a la barra + aguas ARRIBA de F1/S1 con su fusible F5 (removible: aislación de invierno)",
         "Mean Well RSD-60L-12 (B-12V); NO la G (9–36 V)", f"{tag('rsd_vin')} · {tag('v_ctl_tol')}"],
        ["HOLD", "Retención de la bobina de K1", f"Schottky 3 A (1N5822) en serie + {fmt(R['retencion']['C_sel_mF'], 0)} mF ≥ 25 V a 12 V−, entre F2 y la seta "
         f"(aguas ARRIBA de seta/cordón: no demora el corte)",
         "1N5822 + electrolítico (B-HOLD)", f"[CALCULADO, §7] · {tag('hold_t_s')}"],
        ["F2", "Fusible de mando (bobina K1, salida 12 V)", f"{fmt(b['F2_A'], 0)} A lento, portafusible en línea estanco", "B-CFUSE",
         f"[CALCULADO: ≥ {fmt(val('f2_factor'), 2)} × cierre {fmt(b['I_inrush_A'])} A]"],
        ["F3", "Fusible del DC-DC 5 V (entrada, lado batería)", "1 A, ≥ 58 V CC, portafusible en línea", "B-CFUSE",
         f"[SUPUESTO: protege el cable de 0,5 mm²; consumo de entrada ≈ 10 mA [ESTIMADO: 0,3 W / {fmt(m['v_nom'])} V / 0,8]]"],
        ["F5", "Fusible de entrada de B-12V (lado batería)", "3 A, ≥ 58 V CC, portafusible en línea", "B-CFUSE",
         f"[ESTIMADO: 60 W / {fmt(m['v_min_load'], 0)} V / 0,85 ≈ 2 A de entrada a plena carga → 3 A]"],
        ["CORDÓN", "Interruptor de hombre al agua", f"contacto CERRADO con clip (fail-safe), ≥ {fmt(b['I_inrush_A'], 1)} A de cierre a {fmt(b['V_nom'], 0)} V CC",
         "Watski Dødmands kontakt universal, polos M (B-KILL); alt. Sea Dog SD-420487-1",
         f"{tag('kill_switch_watski')} — {'✔ cumple en el mando de 12 V' if b['watski_ok'] else '✘ no cumple'} · Sea Dog 5 A {tag('kill_switch_rating_a')}"],
        ["SETA", "Seta de emergencia", "NC, enclavamiento (girar para rearmar), Ø22, IP65, ≥ 5 A a 12 V CC", "B-ESTOP", "[ESTIMADO: especificación de BOM]"],
        ["J1", "Conector IP68 del hall (caña)", "4 polos apantallado: 5 V, GND, OUT, malla", "Lumberg 0332-04 + 0322-04 (B-SIGNAL)", "[VERIFICADO: R08a §8]"],
        ["J2", "Conector IP68 del cordón (caña)", f"2 polos, ≥ {fmt(b['F2_A'], 0)} A", "Cliffcon 68 FM686812 (B-KCONN)", "[VERIFICADO: R08a §8]"],
        ["ESC", "VESC de la selección", f"FW ≥ {vv['fw_min']} (LispBM; de fábrica {vv['fw_factory'] or '—'} → flashear en T0.0), l_current_max {vv['l_current_max']:.0f} A, "
         "entradas PPM, ADC1 y ADC2 accesibles; caja de agua en el circuito de refrigeración",
         f"{m['esc_desc']} (B-ESC) — sobre base elevada P1-ELE-01 + capota P1-ELE-02",
         "[VERIFICADO: research/R11 §2] · FW de fábrica [inputs.yaml esc.options, allí VERIFICADO]"],
        ["M", "Motor", "sensor de temperatura del bobinado leído por el VESC; sensor hall",
         f"{m['motor_desc']}, variante CON hall (B-MOT); NTC10K 3950 de fábrica (cable amarillo) → TEMP del VESC",
         "[VERIFICADO: página Maytech MTI120116 — 'Yellow: Temp Sensor (NTC10K 3950k)'; R06 §1.2 soporte NTC 10 k en el VESC]"],
        ["IMD", "Monitor de aislamiento", "solo clase 72 V (sistema flotante > 50 V CC)", R["clase"]["imd_desc"], "[VERIFICADO: research/R11 §8; R10b H8]"],
        ["DC-DC", "Regulador → 5 V (MCU)", f"5 V ≥ 0,5 A; entrada máx. > l_max_vin = {vv['l_max_vin']:.0f} V; alimentado aguas abajo de S1 y aguas ARRIBA de K1",
         R["clase"]["dcdc"] + " (B-DCDC)", f"{tag('dcdc_vin_max')} · {tag('dcdc_alt_vin_max')}"],
        ["MCU", "Arduino Nano (ATmega328P, 5 V, 16 MHz)", "bootloader NUEVO (Optiboot): el viejo entra en bucle tras un reset por WDT",
         "Arduino Nano V3 (B-MCU)", "[VERIFICADO: R08a §9] · bootloader [ESTIMADO: problema conocido; se prueba en T0.18]"],
        ["HALL", "Sensor hall lineal ratiométrico 5 V + imán", "salida analógica ratiométrica; imán NdFeB Ø10×3 diametral",
         "Allegro A1324 (B-HALL)", "[VERIFICADO: R08a §9 (sensor)]; imán [ESTIMADO]"],
        ["U1–U3", "Optoacoplador de fototransistor (×3)", f"CTR ≥ {fa(val('opto_ctr_min') * 100)} % a 5 mA, Vceo ≥ 30 V, aislación ≥ 2,5 kV",
         "genérico 4 pines (B-PCB)", tag("opto_ctr_min")],
        ["D_U1–D_U3", "Diodo antiparalelo de cada LED de opto",
         f"1N4148 o similar (≥ 75 V, ≥ 100 mA), cátodo al ánodo del LED (con el EV200 N2 no baja de {fmt(-b['V_N2_negativo_V'], 0)} V; "
         "queda como protección ante un K1 de reemplazo sin economizador)",
         "genérico (B-PCB)", "[CALCULADO, §7]"],
        ["R1 / R2", "R serie de los LED de U1 / U2+U3 (mando de 12 V)",
         f"{o['R_U1_ohm'] / 1000:.1f} kΩ / {o['R_U2U3_ohm'] / 1000:.1f} kΩ, 0,25 W".replace(".", ","), "genéricas (B-PCB)", "[CALCULADO]"],
        ["Q_EN", "Transistor de habilitación (ADC2 del VESC)", "NPN Vceo ≥ 30 V, Ic ≥ 50 mA; base 1 kΩ desde D4 y 10 kΩ a GND",
         "genérico", "[SUPUESTO]"],
        ["Pasivos", "Pull-ups y filtros", "D2/D3: 10 kΩ a 5 V + 100 nF; ADC2: 10 kΩ a 3,3 V; A0: 1 kΩ + 100 nF + 100 kΩ a GND; PPM: 10 kΩ a GND",
         "genéricos", f"{tag('pullup_ohm')} · {tag('rc_filter_s')}"],
        ["LED", "LED de estado de panel", "IP67, 5 V con resistencia", "genérico", "[SUPUESTO]"],
        ["Cables", "Potencia / fases / mando / señal",
         f"DC {cab['dc_mm2']} mm² (barras–F1–S1–K1–ESC) y 35 mm² de rama (estañados); fases: cables PROPIOS del motor (6 AWG × 300 mm) y del ESC (8 AWG) "
         f"unidos con conectores bala 8 mm (sin tramo de {cab['phase_mm2']} mm²: el calibre lo fijan esos cables; caída {fmt(cab['phase_drop_leads_frac'] * 100, 2)} %); "
         "mando 0,75–1 mm² estañado; hall: 4 × 0,25 mm² apantallado redondo; cordón: 2 × 0,75 mm² redondo",
         "Skyllermarks estañado (B-CAB-DC, B-CAB-PAR); B-PHCON; B-LUG10 (cables 8 AWG del ESC a terminales M8)",
         "[CALCULADO: sizing.json cables; §7 caída de fases] · mando/señal [SUPUESTO]"],
        ["Prensaestopas", "Pasamuros IP68", f"caja de batería: un cable REDONDO por prensaestopas, M32 para {cab['dc_mm2']} mm² [ESTIMADO: Ø ext ≈ 17 mm]; M16 4–8 mm (hall, cordón) en la consola",
         "M32 (B-GLAND32) / Biltema M16 (B-GLAND16)", "[VERIFICADO: R08a §8] · regla de un cable [ESTIMADO: R05 §B8]"],
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
           "Fin de carrera bucket", "Motor", "Límite del comando", "Barreras activas (mín–máx)", "Comb."]
    rows = []
    for r in R["tabla_resumen"]:
        rows.append([r["caso"], r["cordon"], r["seta"], r["desconectador"], r["F1"], r["F2"], r["K1"], r["MCU_armado"],
                     r["timeout_VESC"], r["falla_sensor"], r["fin_carrera_bucket"], f"**{r['motor']}**", r["limite_cmd"],
                     f"{r['barreras_min']}–{r['barreras_max']}: {r['barreras']}", r["n_combinaciones"]])
    n = len(R["tabla_verdad"])
    ng = sum(1 for r in R["tabla_verdad"] if r["motor"] != "PARADO")
    B["verdad"] = md_table(hdr, rows) + (
        f"\n\nEnumeración completa: **{n} combinaciones** en [`tabla_verdad.csv`](tabla_verdad.csv) "
        f"(1 = cerrado/sano/sí, 0 = abierto/fundido/no; \"–\" = cualquier valor). El motor puede girar en **{ng}** "
        "de ellas: todas exigen cordón, seta, desconectador, F1, F2, MCU armado, PPM válido y sensor sano; "
        "las variables libres son K1 (normal o soldado: un K1 soldado no se nota en marcha → se prueba antes de cada salida) "
        "y el fin de carrera del bucket, que no detiene el motor: abierto (bucket abajo o cable cortado) limita el comando "
        "a reverse_limit, siempre en avance (§5).")
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


LISP = HERE / "firmware" / "vesc_perfil.lisp"


def update_lisp(txt, R):
    """Reescribe las constantes de ERPM de vesc_perfil.lisp desde electronica.json (no se editan a mano)."""
    vv = R["vesc_values"]
    for name, key in (("erpm-costa", "l_max_erpm"), ("erpm-abierto", "erpm_tech")):
        txt, k = re.subn(rf"\(define {name} -?[\d.]+\)", f"(define {name} {float(vv[key]):.1f})", txt)
        if k != 1:
            raise ValueError(f"vesc_perfil.lisp: no encuentro (define {name} …)")
    return txt


def to_json(R):
    R2 = {k: v for k, v in R.items() if k != "tabla_verdad"}
    return json.dumps(R2, indent=2, ensure_ascii=False, default=float) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    R = compute()
    B = blocks(R)
    outs = {HERE / "electronica.json": to_json(R), HERE / "tabla_verdad.csv": write_csv(R)}
    if LISP.exists():
        outs[LISP] = update_lisp(LISP.read_text(encoding="utf-8"), R)
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
