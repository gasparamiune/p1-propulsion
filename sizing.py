#!/usr/bin/env python3
"""sizing.py — Dimensionamiento del waterjet P1-J (jet boat de Jorge).

Cadena: masas → hidrostática → R(V) (desplazamiento/joroba/Savitsky) → bomba diseñada para el
motor → equilibrio motor–bomba–sistema a cada V → planeo, V máx., bollard, 5 kn, energía,
cavitación, térmico, eléctrico y mecánico. Un optimizador recorre motor × controlador × batería ×
Ø impulsor × relación de tobera y elige la combinación de menor costo que cumple las
restricciones duras (02_calculos.md §4).

Salidas: resultados/sizing.json, resultados/sizing_tablas.md, figuras/*.png
"""
from __future__ import annotations

import argparse
import copy
import itertools
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p1calc import hull, power  # noqa: E402
from p1calc.io import FIG_DIR, RESULTS_DIR, load_inputs, save_json  # noqa: E402
from p1calc.motor import Motor  # noqa: E402
from p1calc.planing import Resistance  # noqa: E402
from p1calc.waterjet import JetDrive, JetGeometry, Pump  # noqa: E402

G = 9.81
KMH = 1 / 3.6
V_FINE = np.round(np.arange(0.0, 11.01, 0.1), 3)        # m/s (0–39,6 km/h) — informe final
V_COARSE = np.round(np.arange(0.0, 11.01, 0.25), 3)     # m/s — barrido del optimizador
V_GRID = V_FINE


# ============================================================================= selección
def jet_mass(inp: dict) -> float:
    """Masa de la unidad de jet: del CAD si existe (manifest), si no la estimada."""
    p = RESULTS_DIR / "manifest.json"
    if p.exists():
        try:
            m = json.loads(p.read_text(encoding="utf-8")).get("totals", {}).get("jet_unit_mass_kg")
            if m:
                return float(m)
        except (ValueError, OSError):
            pass
    return inp["masses"]["jet_mass_estimate_kg"]


def build(inp, mk, ek, bk, D_mm, nr):
    mo, es, ba = inp["motor"]["options"][mk], inp["esc"]["options"][ek], inp["battery"]["options"][bk]
    sel = {"battery_kg": ba["mass_kg"], "motor_kg": mo["mass_kg"], "jet_kg": jet_mass(inp)}
    ms = hull.mass_summary(hull.mass_items(inp, sel))
    h_sub = hull.hydrostatics(inp, ms["total_kg"], ms["vcg_m"])["draft_m"] - inp["waterjet"]["axis_height_m"]
    return {"mo": mo, "es": es, "ba": ba, "ms": ms, "motor": Motor(mo, mk),
            "geo": JetGeometry(inp, D_mm / 1000, D_mm / 1000 * nr, h_sub), "sel": sel}


_R_CACHE: dict = {}


def resistance_for(inp, ms):
    key = (round(ms["total_kg"], 1), round(ms["lcg_m"], 3), round(ms["vcg_m"], 3),
           json.dumps(inp["resistance"], sort_keys=True), json.dumps(inp["boat"], sort_keys=True))
    if key not in _R_CACHE:
        _R_CACHE[key] = Resistance(inp, ms["total_kg"], ms["lcg_m"], ms["vcg_m"])
    return _R_CACHE[key]


def motor_speed_at_power(motor, P, V_bat, eta_esc, duty):
    """rps del motor a plena tensión (duty máx.) entregando P al eje."""
    lo, hi = 1.0, 300.0
    for _ in range(60):
        n = 0.5 * (lo + hi)
        if motor.op_point(n, P / (2 * math.pi * n), V_bat, eta_esc)["duty"] < duty:
            lo = n
        else:
            hi = n
    return 0.5 * (lo + hi)


def limits(inp, s):
    """Límites del controlador: corriente de fase y de batería; potencia continua y pico."""
    mo, es, ba = s["mo"], s["es"], s["ba"]
    i_ph = min(mo["i_max_a"] * inp["motor"]["current_limit_frac"], es["i_cont_a"] / (1 + inp["esc"]["margin_min_frac"]))
    i_bat = ba["i_cont_a"] * inp["battery"]["bms_current_derate"]
    eta_m = mo.get("eta", 0.9)
    return i_ph, i_bat, mo["p_cont_w"] / (eta_m * es["eta"]), mo["p_max_w"] / (eta_m * es["eta"])


def design_pump(inp, s, R, f_pow):
    """El impulsor se diseña para absorber P_d = P_cont + f·(P_máx − P_cont) del motor a plena
    tensión nominal, en la V de equilibrio de planeo (banda nominal) con esa potencia. Con
    motor directo las rpm las fija la tensión: para tener potencia pico en la joroba la bomba
    tiene que poder absorberla (f > 0) y en crucero el controlador limita a P_cont."""
    geo, mo, es, ba = s["geo"], s["mo"], s["es"], s["ba"]
    eta_d = inp["waterjet"]["pump"]["eta_design"]
    P_d = (mo["p_cont_w"] + f_pow * (mo["p_max_w"] - mo["p_cont_w"])) * inp["drivetrain"]["eta_mech"]
    Vs = V_GRID[V_GRID > 2.0]
    T = np.array([geo.thrust(geo.Q_for_hydraulic_power(eta_d * P_d, v), v) for v in Vs])
    ok = np.where(T >= R(Vs, "nominal"))[0]
    V_d = float(Vs[ok[-1]]) if len(ok) else inp["operation"]["top_speed_target_kmh"] * KMH
    n_d = motor_speed_at_power(s["motor"], P_d / inp["drivetrain"]["eta_mech"], ba["v_nom"], es["eta"], inp["esc"]["duty_max"])
    return Pump(geo, V_d, P_d, n_d), V_d


def cav_limited(drv, V, V_bat, i_ph, p_bat, s_max, n_hi):
    """Máximas rpm con S ≤ S_máx (el controlador limita la corriente a baja velocidad)."""
    lo, hi, best = 1.0, n_hi, None
    for _ in range(45):
        n = 0.5 * (lo + hi)
        pp, op = drv.at(n, V, V_bat)
        if pp["S"] <= s_max:
            lo, best = n, {**pp, **op}
        else:
            hi = n
    if best is None:
        pp, op = drv.at(1.0, V, V_bat)
        best = {**pp, **op}
    best["limiter"] = "cavitación (S)"
    return best


CURVE_KEYS = ("T", "n_rpm", "P_shaft", "P_bat", "I_bat", "I_m", "S", "sigma_tip", "eta_pump", "eta_jet",
              "Q_m3s", "H_m", "Vj", "limiter", "duty", "torque", "IVR")


def curve(drv, R, V_bat, band, i_ph, i_bat, p_bat, s_max=None, n_cap=None, grid=None):
    rows = []
    for v in (V_FINE if grid is None else grid):
        st = drv.full_throttle(float(v), V_bat, i_lim=i_ph, p_bat_lim=p_bat, n_cap_rps=n_cap)
        if s_max is not None and st["S"] > s_max:
            st = cav_limited(drv, float(v), V_bat, i_ph, p_bat, s_max, st["n_rpm"] / 60)
        rows.append({**{k: st[k] for k in CURVE_KEYS}, "V": float(v), "R": float(R(v, band))})
    return rows


def analyse_curve(rows, margin, v_planing):
    """V de equilibrio alcanzable desde 0 (primer cruce T = R) y margen mínimo en la joroba."""
    V = np.array([r["V"] for r in rows])
    ex = np.array([r["T"] - r["R"] for r in rows])
    idx = np.where(ex[1:] < 0)[0]
    if len(idx) == 0:
        v_eq = float(V[-1])
    else:
        i = idx[0] + 1
        v_eq = float(V[i - 1] + (V[i] - V[i - 1]) * ex[i - 1] / (ex[i - 1] - ex[i]))
    R = np.array([r["R"] for r in rows])
    hump = (V > 0.3) & (V <= v_planing)
    m = float(np.min(ex[hump] / np.maximum(R[hump], 1e-6))) if hump.any() else math.inf
    return {"V_eq": v_eq, "planes": v_eq >= v_planing, "hump_margin_min": m,
            "hump_ok": m >= margin and v_eq >= v_planing}


def sustained_vmax(cont, planes, v_pl):
    """V máx sostenida con potencia continua una vez en planeo (rama estable de planeo)."""
    V = np.array([r["V"] for r in cont])
    ex = np.array([r["T"] - r["R"] for r in cont])
    if not planes:
        return analyse_curve(cont, 0.0, v_pl)["V_eq"]
    above = np.where((V >= v_pl) & (ex >= 0))[0]
    if not len(above):
        return analyse_curve(cont, 0.0, v_pl)["V_eq"]
    j = above[0]
    while j + 1 < len(V) and ex[j + 1] >= 0:
        j += 1
    if j + 1 < len(V):
        return float(V[j] + (V[j + 1] - V[j]) * ex[j] / (ex[j] - ex[j + 1]))
    return float(V[j])


def accel_time(rows, mass, v_target, added=0.10):
    """t de 0 a v_target integrando (T − R)/m_eff con la curva de pico [masa agregada ESTIMADO 10 %]."""
    V = np.array([r["V"] for r in rows])
    F = np.array([r["T"] - r["R"] for r in rows])
    t, m_eff = 0.0, mass * (1 + added)
    for i in range(len(V) - 1):
        if V[i] >= v_target:
            return t
        f = 0.5 * (F[i] + F[i + 1])
        if f <= 0:
            return math.inf
        t += m_eff * (V[i + 1] - V[i]) / f
    return t if V[-1] >= v_target else math.inf


def evaluate(inp, mk, ek, bk, D_mm, nr, f_pow=0.0, detail=False, pump_fix=None):
    """pump_fix = (V_d, P_d, n_d): usa un impulsor ya diseñado (sensibilidad a entradas inciertas)."""
    grid = V_FINE if detail else V_COARSE
    s = build(inp, mk, ek, bk, D_mm, nr)
    R = resistance_for(inp, s["ms"])
    if pump_fix is None:
        pump, V_d = design_pump(inp, s, R, f_pow)
    else:
        pump, V_d = Pump(s["geo"], *pump_fix), pump_fix[0]
    i_ph, i_bat, P_cont, P_peak = limits(inp, s)
    drv = JetDrive(pump, s["motor"], s["es"], i_ph, i_bat, inp["drivetrain"]["eta_mech"], inp["esc"]["duty_max"])
    ba, op, pmp = s["ba"], inp["operation"], inp["waterjet"]["pump"]
    band = inp["resistance"]["design_band"]
    v_pl = R.fn_p * R.vref
    peak = curve(drv, R, ba["v_nom"], band, i_ph, i_bat, P_peak, pmp["suction_s_max"], grid=grid)
    cont = curve(drv, R, ba["v_nom"], "nominal", i_ph, i_bat, P_cont, pmp["suction_s_max"], grid=grid)
    a_peak = analyse_curve(peak, op["plane_margin_frac"], v_pl)
    v_max = sustained_vmax(cont, a_peak["planes"], v_pl)
    st_top = drv.full_throttle(v_max, ba["v_nom"], i_lim=i_ph, p_bat_lim=P_cont)
    v_leg = op["legal_speed_limit_kmh"] * KMH
    st_leg = drv.for_thrust(float(R(v_leg, band)), v_leg, ba["v_nom"])
    E_req = (st_top["P_bat"] * op["mission_fast_h"] + st_leg["P_bat"] * op["mission_legal_h"]) \
        * (1 + op["reserve_frac"]) / inp["battery"]["usable_dod"]
    E_nom = power.battery_energy_wh(ba)
    rep = pump.design_report()
    U_max = max(r["n_rpm"] for r in peak) / 60 * math.pi * D_mm / 1000
    I_bat_pk = max(r["I_bat"] for r in peak)
    v_ok = ba["v_nom"] <= inp["electrical"]["max_nominal_voltage_v"] or inp["electrical"]["allow_72v"]
    P_mech_peak = max(r["P_shaft"] for r in peak) / 1000
    ok = {
        "voltage": bool(v_ok and s["mo"]["v_class"] == ba["v_class"] == s["es"]["v_class"]
                        and ba["v_max"] <= s["es"]["v_max"] * 0.95
                        and ba.get("cells", 0) <= s["mo"].get("cells_max", 99)),
        "speedboat": P_mech_peak < inp["electrical"]["speedboat_power_kw"],
        "planes": a_peak["hump_ok"],
        "energy": E_nom >= E_req,
        "cavitation_top": st_top["S"] <= pmp["suction_s_max"],
        "tip_speed": U_max <= pmp["tip_speed_max_ms"],
        "pump_phi": pmp["phi_range"][0] <= rep["phi_d"] <= pmp["phi_range"][1],
        "pump_omega_s": pmp["omega_s_range"][0] <= rep["omega_s"] <= pmp["omega_s_range"][1],
        "battery_current": I_bat_pk <= i_bat * 1.001,
        "vmax_target": v_max * 3.6 >= op["top_speed_target_kmh"],
    }
    cost = s["mo"]["price_eur"] + s["es"]["price_eur"] + ba["price_eur"] + ba.get("charger", {}).get("price_eur", 0.0) \
        + (inp["electrical"]["extra_72v_eur"] if ba["v_class"] == 72 else 0.0)
    row = {"motor": mk, "esc": ek, "battery": bk, "D_imp_mm": D_mm, "nozzle_ratio": nr, "f_pow": f_pow,
           "P_design_W": pump.P_d,
           "D_noz_mm": D_mm * nr, "mass_kg": s["ms"]["total_kg"], "lcg_m": s["ms"]["lcg_m"],
           "V_design_kmh": V_d * 3.6, "n_design_rpm": rep["n_d_rpm"], "phi_d": rep["phi_d"],
           "psi_d": rep["psi_d"], "omega_s": rep["omega_s"], "vmax_cont_kmh": v_max * 3.6,
           "hump_margin": a_peak["hump_margin_min"], "planes": a_peak["planes"],
           "bollard_N": peak[0]["T"], "P_bat_top_W": st_top["P_bat"], "P_bat_legal_W": st_leg["P_bat"],
           "E_req_wh": E_req, "E_nom_wh": E_nom, "S_top": st_top["S"], "U_tip_max": U_max,
           "I_bat_peak_A": I_bat_pk, "P_shaft_peak_kW": P_mech_peak, "cost_eur": cost,
           **{f"ok_{k}": bool(v) for k, v in ok.items()},
           "hard_ok": all(v for k, v in ok.items() if k != "vmax_target")}
    if not detail:
        return row
    return {"row": row, "s": s, "R": R, "pump": pump, "drv": drv, "peak": peak, "cont": cont,
            "a_peak": a_peak, "st_top": st_top, "st_leg": st_leg, "limits": (i_ph, i_bat, P_cont, P_peak),
            "v_pl": v_pl, "rep": rep}


SENS = [  # (ruta, (bajo, alto) relativo si es número < 1 con signo, o absolutos con "abs"), etiqueta, re-diseña la bomba
    ("boat.hull_mass_kg", ("rel", 0.30), "Masa del casco ±30 %", False),
    ("masses.items.pilot.kg", ("abs", 70.0, 110.0), "Masa del piloto 70–110 kg", False),
    ("masses.items.pilot.x_m", ("abs", 1.20, 1.55), "Posición del piloto (LCG) 1,20–1,55 m", False),
    ("resistance.r_hump.high", ("rel", 0.25), "R/Δ en la joroba ±25 %", False),
    ("resistance.planing_band.nominal", ("rel", 0.10), "Resistencia de planeo ±10 %", False),
    ("boat.deadrise_deg", ("abs", 4.0, 14.0), "Astilla muerta 4–14°", False),
    ("boat.planing_beam_m", ("rel", 0.10), "Manga de planeo ±10 %", False),
    ("waterjet.pump.eta_design", ("abs", 0.65, 0.78), "Rendimiento de bomba 0,65–0,78", True),
    ("waterjet.intake_eta", ("abs", 0.55, 0.85), "Recuperación en la toma 0,55–0,85", False),
    ("motor.options.{motor}.p_cont_w", ("rel", 0.25), "Potencia continua del motor ±25 %", True),
]


def _set(d, path, val):
    ks = path.split(".")
    for k in ks[:-1]:
        d = d[k]
    d[ks[-1]] = val


def _get(d, path):
    for k in path.split("."):
        d = d[k]
    return d


def _sens_one(args):
    inp, best, path, spec, label, redesign, pump_fix = args
    path = path.format(motor=best["motor"])
    v0 = _get(inp, path)
    lo, hi = (v0 * (1 - spec[1]), v0 * (1 + spec[1])) if spec[0] == "rel" else (spec[1], spec[2])
    out = {}
    for tag, val in (("lo", lo), ("hi", hi)):
        ii = copy.deepcopy(inp)
        _set(ii, path, val)
        r = evaluate(ii, best["motor"], best["esc"], best["battery"], best["D_imp_mm"], best["nozzle_ratio"],
                     best["f_pow"], pump_fix=None if redesign else pump_fix)
        out[tag] = {"value": val, "vmax": r["vmax_cont_kmh"], "hump": r["hump_margin"], "P_leg": r["P_bat_legal_W"],
                    "planes": r["planes"]}
    return {"param": path, "label": label, **out,
            "swing_vmax_kmh": abs(out["hi"]["vmax"] - out["lo"]["vmax"]),
            "swing_hump": abs(out["hi"]["hump"] - out["lo"]["hump"])}


def sensitivity(inp, best, pump):
    pf = (pump.V_d, pump.P_d, pump.n_d)
    jobs = [(inp, best, *x, pf) for x in SENS]
    workers = max(1, min(len(jobs), (os.cpu_count() or 2) - 1))
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            rows = list(ex.map(_sens_one, jobs))
    else:
        rows = [_sens_one(j) for j in jobs]
    rows.sort(key=lambda r: -(r["swing_vmax_kmh"] / 5 + r["swing_hump"]))
    return {"rows": rows, "top3": [r["label"] for r in rows[:3]],
            "any_no_plane": [r["label"] for r in rows if not (r["lo"]["planes"] and r["hi"]["planes"])]}


def _eval_safe(inp, job):
    mk, ek, bk, D, nr, fp = job
    try:
        return evaluate(inp, mk, ek, bk, D, nr, fp)
    except (RuntimeError, ValueError, TypeError, ZeroDivisionError) as e:
        return {"motor": mk, "esc": ek, "battery": bk, "D_imp_mm": D, "nozzle_ratio": nr, "f_pow": fp,
                "error": str(e), "hard_ok": False, "cost_eur": math.inf}


def optimize(inp):
    j = inp["waterjet"]

    def pick(sec):
        return [inp[sec]["chosen"]] if inp[sec]["chosen"] != "auto" else list(inp[sec]["options"])

    jobs = []
    for mk, ek, bk in itertools.product(pick("motor"), pick("esc"), pick("battery")):
        mo, es, ba = inp["motor"]["options"][mk], inp["esc"]["options"][ek], inp["battery"]["options"][bk]
        if not (mo["v_class"] == es["v_class"] == ba["v_class"]):
            continue
        for D, nr, fp in itertools.product(j["impeller_d_options_mm"], j["nozzle_ratio_options"],
                                           j["design_power_frac_options"]):
            jobs.append((mk, ek, bk, D, nr, fp))
    workers = max(1, min(len(jobs), (os.cpu_count() or 2) - 1))
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            rows = list(ex.map(_eval_safe, [inp] * len(jobs), jobs, chunksize=4))
    else:
        rows = [_eval_safe(inp, jb) for jb in jobs]
    good = [r for r in rows if r["hard_ok"]]
    if good:
        fast = [r for r in good if r["ok_vmax_target"]]
        pool = fast or good
        cmin = min(r["cost_eur"] for r in pool)
        band = [r for r in pool if r["cost_eur"] <= cmin * (1 + inp["costs"]["selection_cost_band_frac"])]
        best = max(band, key=lambda r: (round(r["vmax_cont_kmh"], 1), r["hump_margin"]))
        status = "ok" if fast else "sin_vmax_objetivo"
    else:
        cand = [r for r in rows if "error" not in r]
        best = max(cand, key=lambda r: (sum(1 for k in r if k.startswith("ok_") and r[k]), r["vmax_cont_kmh"]))
        status = "sin_solucion_dura"
    return best, rows, status


# ============================================================================= mecánica y cargas
def mechanical(inp, d):
    sh, br = inp["shaft"], inp["bearings"]
    i_ph = d["limits"][0]
    T_max = d["s"]["motor"].kt * i_ph * sh["locked_rotor_factor"]    # par que deja pasar el controlador
    T_top = d["st_top"]["torque"]
    dsh = sh["d_mm"] / 1000

    def tau(T):
        return 16 * T / (math.pi * dsh ** 3) * sh["kt_keyway"]

    fs_static = 0.577 * sh["sy_mpa"] * 1e6 / tau(T_max)
    ta, tm = 0.10 * tau(T_top), tau(T_top)             # [ESTIMADO: ±10 % de rizado de par por paso de pala]
    fs_fat = 1 / (ta / (0.577 * sh["se_mpa"] * 1e6) + tm / (0.577 * sh["su_mpa"] * 1e6))
    n_max = max(r["n_rpm"] for r in d["peak"])
    Fa = max(r["T"] for r in d["peak"])                # empuje axial máx. (bollard) al rodamiento fijo
    Fr = 0.6 * G + 0.05 * Fa                           # [ESTIMADO: peso del impulsor + 5 % del empuje]
    P_top = 0.35 * Fr + 0.57 * d["st_top"]["T"]        # [ESTIMADO: par 7204 BEP, Fa/Fr > e]
    L10 = (br["C_dyn_n"] / P_top) ** 3 * 1e6 / (60 * max(d["st_top"]["n_rpm"], 1))
    # velocidad crítica: eje simplemente apoyado entre el par de rodamientos (seco, a proa) y el buje
    # de agua del cubo del estator (popa), con el impulsor como masa puntual (Dunkerley, sin la masa del eje)
    E, I = sh["e_gpa"] * 1e9, math.pi * dsh ** 4 / 64
    D = d["s"]["geo"].D
    ca = math.cos(math.radians(inp["waterjet"]["shaft_incline_deg"]))
    S_brg_c = (1.85 * D / ca + 0.015 + 0.010 + 0.040)  # [CALCULADO: misma regla que 04_diseno/params.py]
    X_bush = 0.48 * D + 0.030                            # [CALCULADO: params_bomba (buje en el cubo del estator)]
    X_imp_c = 0.21 * D
    L_span = S_brg_c + X_bush
    a_, b_ = L_span - (X_bush - X_imp_c), X_bush - X_imp_c
    nu = inp["waterjet"]["hub_ratio"]
    m_imp = sh["density_kg_m3"] * math.pi / 4 * (nu * D) ** 2 * 0.42 * D * 1.3   # [ESTIMADO: cubo macizo + 30 % de álabes]
    k = 3 * E * I * L_span / (a_ ** 2 * b_ ** 2)
    n_crit = math.sqrt(k / m_imp) / (2 * math.pi) * 60
    v_seal = math.pi * dsh * n_max / 60
    tgt = inp["materials"]["fs_target_metal"]
    # pasador de corte impulsor–eje (corte doble en el eje): T_corte = 2·(π/4·d²)·τ_u·(D_eje/2)
    spn = inp["waterjet"]["shear_pin"]
    T_need = spn["fuse_factor_vs_tmax"] * T_max
    pin = None
    for dp in spn["d_options_mm"]:
        T_cut = 2 * math.pi / 4 * (dp / 1000) ** 2 * spn["tau_u_mpa"] * 1e6 * dsh / 2
        if T_cut >= T_need:
            pin = {"d_mm": dp, "T_cut_Nm": T_cut}
            break
    if pin is None:
        dp = spn["d_options_mm"][-1]
        pin = {"d_mm": dp, "T_cut_Nm": 2 * math.pi / 4 * (dp / 1000) ** 2 * spn["tau_u_mpa"] * 1e6 * dsh / 2}
    pin.update({"T_need_Nm": T_need, "material": spn["material"],
                "fs_shaft_at_cut": 0.577 * sh["sy_mpa"] * 1e6 / tau(pin["T_cut_Nm"])})
    return {"T_max_Nm": T_max, "T_top_Nm": T_top, "tau_max_MPa": tau(T_max) / 1e6,
            "fs_shaft_static": fs_static, "fs_shaft_fatigue": fs_fat, "n_max_rpm": n_max,
            "Fa_max_N": Fa, "Fr_N": Fr, "L10_top_h": L10, "n_crit_rpm": n_crit, "L_span_m": L_span, "m_impeller_kg": m_imp,
            "crit_ratio": n_crit / n_max, "seal_speed_ms": v_seal,
            "seal_ok": v_seal <= inp["seal"]["v_max_ms"], "bearing_ok": L10 >= br["life_target_h"],
            "shaft_ok": fs_static >= tgt and fs_fat >= tgt, "crit_ok": n_crit / n_max >= 1.3,
            "shear_pin": pin, "shear_pin_ok": pin["fs_shaft_at_cut"] >= 1.2}


def loads(inp, d):
    rho = inp["water"]["density_kg_m3"]
    peak = d["peak"]
    T_b = peak[0]["T"]
    H_max = max(r["H_m"] for r in peak)
    Vj = max(r["Vj"] for r in peak)
    rev = inp["waterjet"]["reverse"]
    dmax = math.radians(inp["waterjet"]["steering"]["max_deflection_deg"])
    return {"T_bollard_N": T_b, "T_top_N": d["st_top"]["T"], "H_max_m": H_max,
            "p_pump_max_Pa": rho * G * H_max, "p_nozzle_dyn_Pa": 0.5 * rho * Vj ** 2, "Vj_max_ms": Vj,
            "F_steer_side_N": T_b * math.sin(dmax),
            "F_bucket_N": T_b * (1 + rev["thrust_frac"]) * rev["power_limit_frac"] ** (2 / 3),
            "Q_max_m3s": max(r["Q_m3s"] for r in peak), "torque_max_Nm": max(r["torque"] for r in peak)}


# ============================================================================= run
def run(inp: dict, make_plots: bool = True, quiet: bool = False) -> dict:
    best, rows, status = optimize(inp)
    d = evaluate(inp, best["motor"], best["esc"], best["battery"], best["D_imp_mm"], best["nozzle_ratio"],
                 best["f_pow"], detail=True)
    s, R, ba, ms = d["s"], d["R"], d["s"]["ba"], d["s"]["ms"]
    hs = hull.hydrostatics(inp, ms["total_kg"], ms["vcg_m"])
    cap = hull.capacity_uscg(inp, hs["disp_max_kg"], ms["machinery_kg"])
    heel = hull.heel_for_offset(ms["total_kg"], hs["GM_m"], inp["masses"]["items"]["pilot"]["kg"], 0.10)
    axis = inp["waterjet"]["axis_height_m"]
    priming = {"axis_height_m": axis, "draft_m": hs["draft_m"], "axis_below_wl_m": hs["draft_m"] - axis,
               "primes": hs["draft_m"] - axis >= 0.0}
    band = inp["resistance"]["design_band"]
    i_ph, i_bat, P_cont, P_peak = d["limits"]
    drv, s_max = d["drv"], inp["waterjet"]["pump"]["suction_s_max"]
    vm = {}
    for name, vb in (("v_nom", ba["v_nom"]), ("v_min", ba["v_min"]), ("v_max", ba["v_max"])):
        c = curve(drv, R, vb, "nominal", i_ph, i_bat, P_cont, s_max)
        p = curve(drv, R, vb, band, i_ph, i_bat, P_peak, s_max)
        ap = analyse_curve(p, inp["operation"]["plane_margin_frac"], d["v_pl"])
        vm[name] = {"V_bat": vb, "vmax_cont_kmh": sustained_vmax(c, ap["planes"], d["v_pl"]) * 3.6,
                    "planes": ap["planes"], "hump_margin": ap["hump_margin_min"]}
    t_plane = accel_time(d["peak"], ms["total_kg"], d["v_pl"])
    # V máx. "por ratos" con potencia pico (banda nominal) y cuánto dura antes del límite térmico
    pk_nom = curve(drv, R, ba["v_nom"], "nominal", i_ph, i_bat, P_peak, s_max)
    v_pk = sustained_vmax(pk_nom, d["a_peak"]["planes"], d["v_pl"])
    st_pk = drv.full_throttle(v_pk, ba["v_nom"], i_lim=i_ph, p_bat_lim=P_peak)
    T_amb = inp["air"]["temp_max_c"]
    T0 = s["motor"].steady_temp(d["st_top"]["P_loss_motor"], T_amb)
    t_pk = s["motor"].time_to_limit_s(st_pk["P_loss_motor"], T_amb, T0)
    # refrigeración por agua: caudal por el orificio con la altura de la bomba a V máx. sostenida
    cl = inp["waterjet"]["cooling"]
    A_o = math.pi / 4 * (cl["orifice_d_mm"] / 1000) ** 2
    q_cool = cl["cd"] * A_o * math.sqrt(2 * G * max(d["st_top"]["H_m"], 0.1))
    q_cool_legal = cl["cd"] * A_o * math.sqrt(2 * G * max(d["st_leg"]["H_m"], 0.1))
    P_heat = d["st_top"]["P_loss_motor"] + d["st_top"]["P_loss_esc"]
    cooling = {"Q_l_min_top": q_cool * 60000, "Q_l_min_legal": q_cool_legal * 60000, "P_heat_W": P_heat,
               "dT_water_K": P_heat / (4186 * q_cool * inp["water"]["density_kg_m3"]),
               "ok": P_heat / (4186 * q_cool * inp["water"]["density_kg_m3"]) <= cl["dT_max_k"]}
    # tope legal de rpm: 5 kn con piloto liviano, banda baja y batería llena (caso más rápido)
    ii = copy.deepcopy(inp)
    ii["masses"]["items"]["pilot"]["kg"] = inp["masses"]["light_pilot_kg"]
    ms_l = hull.mass_summary(hull.mass_items(ii, s["sel"]))
    R_l = Resistance(ii, ms_l["total_kg"], ms_l["lcg_m"], ms_l["vcg_m"])
    v_leg = inp["operation"]["legal_speed_limit_kmh"] * KMH
    st_cap = drv.for_thrust(float(R_l(v_leg, "low")), v_leg, ba["v_max"])
    E_us = power.battery_energy_wh(ba) * inp["battery"]["usable_dod"]
    legal = {"rpm_cap": st_cap["n_rpm"], "erpm_cap": st_cap["n_rpm"] * s["mo"].get("pole_pairs", 5),
             "P_bat_legal_W": d["st_leg"]["P_bat"], "autonomy_legal_h": E_us / d["st_leg"]["P_bat"],
             "n_legal_rpm": d["st_leg"]["n_rpm"], "mass_light_kg": ms_l["total_kg"]}
    energy = {"E_nom_wh": power.battery_energy_wh(ba), "E_usable_wh": E_us, "E_req_wh": d["row"]["E_req_wh"],
              "t_top_min": E_us / d["st_top"]["P_bat"] * 60,
              "range_top_km": E_us / d["st_top"]["P_bat"] * d["st_top"]["V"] * 3.6,
              "t_legal_h": legal["autonomy_legal_h"]}
    P_loss = d["st_top"]["P_loss_motor"]
    T_m = s["motor"].steady_temp(P_loss, T_amb)
    thermal = {"P_loss_motor_W": P_loss, "T_motor_steady_C": T_m, "t_winding_max_C": s["mo"]["t_winding_max_c"],
               "ok": T_m <= s["mo"]["t_winding_max_c"], "P_loss_esc_W": d["st_top"]["P_loss_esc"]}
    I_pk, I_top = d["row"]["I_bat_peak_A"], d["st_top"]["I_bat"]
    e = inp["electrical"]
    need = max(I_top * e["fuse_factor"], I_pk)
    fuse_a = next((r for r in e["fuse_ratings_a"] if r >= need), e["fuse_ratings_a"][-1])
    cab_dc = power.cable(inp, I_pk, e["len_battery_to_esc_m"], ba["v_nom"], I_ampacity=fuse_a)
    cab_ph = power.cable(inp, i_ph, e["len_esc_to_motor_m"], ba["v_nom"])
    out = {
        "status": status,
        "selection": {**{k: best[k] for k in ("motor", "esc", "battery", "D_imp_mm", "nozzle_ratio", "D_noz_mm",
                                              "f_pow", "P_design_W")},
                      "motor_desc": s["mo"]["desc"], "esc_desc": s["es"]["desc"], "battery_desc": ba["desc"],
                      "v_class": ba["v_class"], "hub_d_mm": best["D_imp_mm"] * inp["waterjet"]["hub_ratio"],
                      "cost_core_eur": best["cost_eur"]},
        "masses": {**{k: v for k, v in ms.items() if k != "items"}, "items": ms["items"]},
        "hydrostatics": hs, "capacity": cap, "heel_pilot_0p1m_deg": heel, "priming": priming,
        "resistance": {"V_kmh": [float(v * 3.6) for v in V_GRID],
                       **{b: [float(R(v, b)) for v in V_GRID] for b in ("low", "nominal", "high")},
                       "v_planing_kmh": d["v_pl"] * 3.6, "v_hump_kmh": R.fn_h * R.vref * 3.6,
                       "savitsky": [{"V_kmh": float(v * 3.6), **p} for v, p in zip(R.Vp, R.planing)]},
        "pump": {**d["rep"], "D_mm": best["D_imp_mm"], "hub_ratio": inp["waterjet"]["hub_ratio"],
                 "eta_design": inp["waterjet"]["pump"]["eta_design"], "V_design_kmh": best["V_design_kmh"],
                 "blades": inp["waterjet"]["blades"], "stator_vanes": inp["waterjet"]["stator_vanes"],
                 "tip_clearance_mm": best["D_imp_mm"] * inp["waterjet"]["tip_clearance_frac"],
                 "U_tip_max": best["U_tip_max"],
                 "hub_free_vortex_ok": d["rep"]["sections"]["cubo"]["u"] > d["rep"]["sections"]["cubo"]["cu2"]},
        "performance": {"peak_curve": d["peak"], "cont_curve": d["cont"],
                        "vmax_cont_kmh": best["vmax_cont_kmh"], "planes": d["a_peak"]["planes"],
                        "hump_margin_min": d["a_peak"]["hump_margin_min"], "t_to_plane_s": t_plane,
                        "bollard_N": d["peak"][0]["T"],
                        "reverse_N": d["peak"][0]["T"] * inp["waterjet"]["reverse"]["thrust_frac"]
                        * inp["waterjet"]["reverse"]["power_limit_frac"] ** (2 / 3),
                        "top": _slim(d["st_top"]), "legal": _slim(d["st_leg"]), "vmax_by_battery": vm,
                        "vmax_peak_kmh": v_pk * 3.6, "peak_top": _slim(st_pk), "P_shaft_peak_kW": best["P_shaft_peak_kW"],
                        "t_peak_from_cruise_min": t_pk / 60 if t_pk != math.inf else math.inf},
        "cooling": cooling,
        "success": {"bollard_min_N": d["peak"][0]["T"] * inp["operation"]["success"]["bollard_frac"],
                    "vmax_min_kmh": best["vmax_cont_kmh"] * inp["operation"]["success"]["vmax_frac"],
                    "p_legal_max_W": d["st_leg"]["P_bat"] * inp["operation"]["success"]["p_legal_frac"],
                    "t_plane_max_s": inp["operation"]["accel_target_s"]},
        "legal_speed": legal, "energy": energy, "thermal": thermal,
        "electrical": {"I_bat_peak_A": I_pk, "I_bat_top_A": I_top, "I_phase_limit_A": i_ph, "I_bat_limit_A": i_bat,
                       "P_bat_cont_W": P_cont, "P_bat_peak_W": P_peak, "cable_dc": cab_dc, "cable_phase": cab_ph,
                       "fuse_a": fuse_a, "fuse_protects_cable": fuse_a <= cab_dc["ampacity_a"]},
        "mech": mechanical(inp, d), "loads": loads(inp, d),
        "sensitivity": sensitivity(inp, best, d["pump"]),
        "optimization": {"status": status, "n_evaluated": len(rows),
                         "n_hard_ok": sum(1 for r in rows if r.get("hard_ok")), "rows": rows},
        "checks": {k: v for k, v in best.items() if k.startswith("ok_")},
    }
    save_json(out, "sizing.json")
    write_tables(out, inp)
    if make_plots:
        plots(out, inp)
    if not quiet:
        print_summary(out)
    return out


def _slim(st):
    keys = ("V", "T", "n_rpm", "P_shaft", "P_bat", "I_bat", "I_m", "S", "sigma_tip", "eta_pump", "eta_jet",
            "Q_m3s", "H_m", "Vj", "torque", "IVR", "duty", "P_loss_motor", "P_loss_esc", "limiter")
    return {k: (float(st[k]) if isinstance(st.get(k), (int, float, np.floating)) else st.get(k)) for k in keys}


def write_tables(o, inp):
    sel, pf, pm = o["selection"], o["performance"], o["pump"]
    hs, en, me = o["hydrostatics"], o["energy"], o["mech"]
    L = ["| Magnitud | Valor | Etiqueta |", "|---|---|---|"]

    def add(a, b, t="[CALCULADO]"):
        L.append(f"| {a} | {b} | {t} |")

    add("Estado del optimizador", o["status"])
    add("Motor / controlador / batería", f"{sel['motor_desc']} / {sel['esc_desc']} / {sel['battery_desc']}", "[CALCULADO: optimizador]")
    add("Masa total / LCG desde el espejo", f"{o['masses']['total_kg']:.0f} kg / {o['masses']['lcg_m']:.2f} m")
    add("Calado / GM / escora con el piloto 0,1 m a un lado", f"{hs['draft_m']*1000:.0f} mm / {hs['GM_m']*1000:.0f} mm / {o['heel_pilot_0p1m_deg']:.0f}°")
    add("Eje del impulsor bajo la flotación (cebado)", f"{o['priming']['axis_below_wl_m']*1000:.0f} mm ({'ceba' if o['priming']['primes'] else 'NO ceba'})")
    add("Impulsor / cubo / tobera", f"Ø{sel['D_imp_mm']:.0f} / Ø{sel['hub_d_mm']:.0f} / Ø{sel['D_noz_mm']:.0f} mm")
    add("Punto de diseño de la bomba", f"{pm['V_design_kmh']:.1f} km/h, {pm['n_d_rpm']:.0f} rpm, φ {pm['phi_d']:.3f}, ψ {pm['psi_d']:.3f}, Ω_s {pm['omega_s']:.2f}")
    add("¿Planea? / margen mínimo en la joroba", f"{'sí' if pf['planes'] else 'NO'} / {pf['hump_margin_min']*100:.0f} %")
    add("Tiempo de 0 a planeo", f"{pf['t_to_plane_s']:.1f} s")
    add("V máx. sostenida (potencia continua, banda nominal)", f"{pf['vmax_cont_kmh']:.1f} km/h (objetivo {inp['operation']['top_speed_target_kmh']:.0f})")
    add("P de batería a V máx. / a 5 kn", f"{pf['top']['P_bat']:.0f} W / {pf['legal']['P_bat']:.0f} W")
    add("Empuje a punto fijo / en reversa", f"{pf['bollard_N']:.0f} N / {pf['reverse_N']:.0f} N")
    add("Autonomía a V máx. / a 5 kn", f"{en['t_top_min']:.0f} min ({en['range_top_km']:.1f} km) / {en['t_legal_h']:.1f} h")
    add("Energía de la misión requerida / nominal", f"{en['E_req_wh']:.0f} / {en['E_nom_wh']:.0f} Wh")
    add("Cavitación S a V máx. (límite)", f"{pf['top']['S']:.2f} ({inp['waterjet']['pump']['suction_s_max']})")
    add("Velocidad periférica máx.", f"{pm['U_tip_max']:.1f} m/s")
    add("Corriente pico de batería / límite de fase", f"{o['electrical']['I_bat_peak_A']:.0f} A / {o['electrical']['I_phase_limit_A']:.0f} A")
    add("Motor a V máx. sostenida (estacionario)", f"{o['thermal']['T_motor_steady_C']:.0f} °C (máx. {o['thermal']['t_winding_max_C']:.0f})")
    add("Eje Ø / FS estático / FS fatiga", f"{inp['shaft']['d_mm']:.0f} mm / {me['fs_shaft_static']:.1f} / {me['fs_shaft_fatigue']:.1f}")
    add("Rodamientos L10 a V máx. / vel. crítica / sello", f"{me['L10_top_h']:.0f} h / {me['crit_ratio']:.1f}× n máx. / {me['seal_speed_ms']:.1f} m/s")
    main = "\n".join(L)
    C = ["| V [km/h] | R diseño [N] | T pico [N] | rpm | P bat [W] | I bat [A] | S | Limita |", "|---|---|---|---|---|---|---|---|"]
    for r in pf["peak_curve"][::10]:
        C.append(f"| {r['V']*3.6:.0f} | {r['R']:.0f} | {r['T']:.0f} | {r['n_rpm']:.0f} | {r['P_bat']:.0f} | {r['I_bat']:.0f} | {r['S']:.2f} | {r['limiter']} |")
    Pt = ["| Sección | r [mm] | u [m/s] | c_m [m/s] | β1 [°] | β2 [°] | desvío [°] | entrada estator [°] | de Haller |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, r in pm["sections"].items():
        Pt.append(f"| {k} | {r['r_mm']:.1f} | {r['u']:.1f} | {r['cm']:.1f} | {r['beta1_deg']:.1f} | {r['beta2_deg']:.1f} | {r['turning_deg']:.1f} | {r['stator_inlet_deg']:.1f} | {r['de_haller']:.2f} |")
    O = ["| Motor | Batería | Ø imp | D_t/D | V máx [km/h] | Margen joroba | Costo [€] | Duras OK |", "|---|---|---|---|---|---|---|---|"]
    for r in sorted([r for r in o["optimization"]["rows"] if "error" not in r],
                    key=lambda r: (-r["hard_ok"], r["cost_eur"], -r["vmax_cont_kmh"]))[:15]:
        O.append(f"| {r['motor']} | {r['battery']} | {r['D_imp_mm']:.0f} | {r['nozzle_ratio']:.2f} | {r['vmax_cont_kmh']:.1f} | {r['hump_margin']*100:.0f} % | {r['cost_eur']:.0f} | {'sí' if r['hard_ok'] else 'no'} |")
    tabs = {"main": main, "curve": "\n".join(C), "pump": "\n".join(Pt), "opt": "\n".join(O)}
    with open(RESULTS_DIR / "sizing_tablas.md", "w", encoding="utf-8") as f:
        f.write("<!-- generado por sizing.py — no editar a mano -->\n\n## Resumen\n\n" + tabs["main"] +
                "\n\n## Curva a fondo (potencia pico, banda de diseño, batería nominal)\n\n" + tabs["curve"] +
                "\n\n## Triángulos de velocidad del impulsor\n\n" + tabs["pump"] +
                "\n\n## Optimizador (15 mejores)\n\n" + tabs["opt"] + "\n")
    o["_tables"] = tabs


def plots(o, inp):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG_DIR.mkdir(exist_ok=True)
    r = o["resistance"]
    pk, ct = o["performance"]["peak_curve"], o["performance"]["cont_curve"]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.fill_between(r["V_kmh"], r["low"], r["high"], color="#cccccc", alpha=0.6, label="R (banda baja–alta)")
    ax.plot(r["V_kmh"], r["nominal"], "k-", lw=1, label="R nominal")
    ax.plot([x["V"] * 3.6 for x in pk], [x["T"] for x in pk], "r-", label="Empuje a potencia pico")
    ax.plot([x["V"] * 3.6 for x in ct], [x["T"] for x in ct], "b--", label="Empuje a potencia continua")
    ax.axvline(inp["operation"]["legal_speed_limit_kmh"], color="g", ls=":", label="5 kn (300 m)")
    ax.axvline(r["v_planing_kmh"], color="0.5", ls=":", lw=0.8)
    ax.set_xlabel("V [km/h]"); ax.set_ylabel("Fuerza [N]"); ax.set_xlim(0, 40); ax.set_ylim(0, None)
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
    ax.set_title(f"Empuje vs resistencia — {o['masses']['total_kg']:.0f} kg, Ø{o['selection']['D_imp_mm']:.0f}/Ø{o['selection']['D_noz_mm']:.0f}")
    fig.tight_layout(); fig.savefig(FIG_DIR / "empuje_resistencia.png", dpi=130); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot([x["V"] * 3.6 for x in pk], [x["P_bat"] for x in pk], "r-", label="P batería (pico)")
    ax.plot([x["V"] * 3.6 for x in ct], [x["P_bat"] for x in ct], "b--", label="P batería (continua)")
    ax2 = ax.twinx()
    ax2.plot([x["V"] * 3.6 for x in pk], [x["S"] for x in pk], "m-", lw=0.8, label="S succión")
    ax2.axhline(inp["waterjet"]["pump"]["suction_s_max"], color="m", ls=":", lw=0.8)
    ax.set_xlabel("V [km/h]"); ax.set_ylabel("P [W]"); ax2.set_ylabel("S [-]")
    ax.grid(alpha=0.3); ax.legend(loc="lower left", fontsize=8); ax2.legend(loc="lower right", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG_DIR / "potencia_cavitacion.png", dpi=130); plt.close(fig)


def print_summary(o):
    print("=" * 72)
    print("P1-J waterjet — resumen")
    print("=" * 72)
    print(o["_tables"]["main"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default=None)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--no-plots", action="store_true")
    a = ap.parse_args(argv)
    run(load_inputs(a.inputs), make_plots=not a.no_plots, quiet=a.quiet)


if __name__ == "__main__":
    main()
