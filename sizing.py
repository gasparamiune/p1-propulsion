#!/usr/bin/env python3
"""sizing.py — Dimensionamiento del prototipo P1 (lee inputs.yaml).

Salidas:
    resultados/sizing.json        todos los resultados numéricos (los usa el CAD y la BOM)
    resultados/sizing_tablas.md   tablas en Markdown (se insertan en 02_calculos.md)
    figuras/*.png                 R(v), P(v), autonomía(v), sensibilidad
Uso:
    python sizing.py [--inputs ruta.yaml] [--quiet]
"""
from __future__ import annotations

import argparse
import copy
import math
import sys

import numpy as np

from p1calc import geometry, hydro, mech, power
from p1calc.io import FIG_DIR, RESULTS_DIR, load_inputs, save_json
from p1calc.system import Drive, R_at

KMH = 1 / 3.6


# =============================================================================
def select_ratio(inp, mass, bat_key):
    """Barrido de poleas HTD-5M: maximiza V_max (banda de diseño, batería baja);
    desempate: menor potencia de batería en crucero."""
    dt = inp["drivetrain"]
    bat = inp["battery"]["options"][bat_key]
    v_cr = inp["operation"]["cruise_speed_kmh"] * KMH
    rows = []
    for zm in dt["z_motor_options"]:
        for zs in dt["z_shaft_options"]:
            d1, d2 = zm * 5 / math.pi, zs * 5 / math.pi
            if (d1 + d2) / 2 + 12 > dt["center_distance_mm"]:
                continue
            drv = Drive(inp, zm, zs, bat_key)
            vmax = drv.max_speed(mass, bat["v_min"])
            if not vmax.get("feasible", False):
                continue
            cr = drv.at_speed(v_cr, R_at(inp, mass, v_cr, "design"), bat["v_nom"])
            if not cr["feasible"]:
                continue
            rows.append({"z_motor": zm, "z_shaft": zs, "ratio": zs / zm,
                         "vmax_kmh": vmax["V"] * 3.6, "P_bat_cruise": cr["P_bat"],
                         "duty_cruise": cr["duty"]})
    if not rows:
        raise RuntimeError("ninguna relación de poleas es factible")
    vbest = max(r["vmax_kmh"] for r in rows)
    cand = [r for r in rows if r["vmax_kmh"] >= 0.99 * vbest]
    best = min(cand, key=lambda r: (r["P_bat_cruise"], -r["ratio"]))
    return best, rows


def resolve(inp: dict, prop_key: str, bat_key: str) -> dict:
    """Copia de inputs con la hélice y batería concretas (reemplaza "auto")."""
    ii = copy.deepcopy(inp)
    ii["propeller"]["chosen"] = prop_key
    ii["battery"]["chosen"] = bat_key
    return ii


def _h_shaft(ii, mass):
    hs = hydro.hydrostatics(ii, mass)
    return geometry.layout(ii, hs["draft_m"])["prop_center_depth_mm"] / 1000


def _candidates(inp, section):
    ch = inp[section]["chosen"]
    return list(inp[section]["options"]) if ch == "auto" else [ch]


def optimize(inp: dict) -> dict:
    """Evalúa cada combinación hélice × batería (con su mejor relación de poleas) y elige
    la de MENOR COSTO que cumple: energía (2 h + reserva, banda de diseño), corriente
    (BMS/ESC), V máx objetivo (banda nominal, batería nominal) y calado máx. de hélice."""
    op = inp["operation"]
    v_cr = op["cruise_speed_kmh"] * KMH
    unit_m = inp["architecture"]["unit_mass_estimate_kg"]
    rows = []
    for pk in _candidates(inp, "propeller"):
        p = inp["propeller"]["options"][pk]
        tip_depth = p["D_mm"] * (1 + inp["architecture"]["prop_tip_immersion_frac_D"])
        for bk in _candidates(inp, "battery"):
            ii = resolve(inp, pk, bk)
            b = ii["battery"]["options"][bk]
            mass = hydro.masses(ii, b["mass_kg"], unit_m)["total_kg"]
            try:
                rb, _ = select_ratio(ii, mass, bk)
            except RuntimeError:
                continue
            drv = Drive(ii, rb["z_motor"], rb["z_shaft"], bk)
            cr = drv.at_speed(v_cr, R_at(ii, mass, v_cr, "design"), b["v_nom"])
            vmn = drv.max_speed(mass, b["v_nom"], "nominal")
            vmd = drv.max_speed(mass, b["v_min"], "design")
            bol = drv.bollard(b["v_nom"])
            I_pk = max(vmd.get("I_bat", 0), bol["I_bat"])
            E_req = power.required_energy_wh(ii, cr["P_bat"])
            E_nom = power.battery_energy_wh(b)
            ok = {
                "energy": E_nom >= E_req,
                "current": b["i_cont_a"] >= I_pk,
                "vmax": vmn["V"] * 3.6 >= op["vmax_target_kmh"] - op["vmax_tolerance_kmh"],
                "voltage": b["v_nom"] <= ii["electrical"]["max_nominal_voltage_v"],
                "cavitation": drv.prop.keller_min_bar(bol["T_shaft"], _h_shaft(ii, mass), ii["water"]) <= drv.prop.BAR,
                "draft": tip_depth <= op["max_prop_tip_depth_mm"],
                "esc_margin": ii["esc"]["options"][ii["esc"]["chosen"]]["i_cont_a"] >= (1 + ii["esc"]["margin_min_frac"]) * I_pk,
            }
            rows.append({"prop": pk, "battery": bk, "z_motor": rb["z_motor"], "z_shaft": rb["z_shaft"],
                         "mass_kg": mass, "P_bat_cruise_des_W": cr["P_bat"], "E_req_wh": E_req,
                         "E_nom_wh": E_nom, "vmax_nom_kmh": vmn["V"] * 3.6,
                         "vmax_des_vmin_kmh": vmd["V"] * 3.6, "bollard_N": bol["T_horiz"],
                         "I_peak_A": I_pk, "tip_depth_mm": tip_depth,
                         "cost_eur": b["price_eur"] + p["price_eur"],
                         **{f"ok_{k}": v for k, v in ok.items()}, "all_ok": all(ok.values())})
    feas = [r for r in rows if r["all_ok"]]
    if feas:
        best = min(feas, key=lambda r: (r["cost_eur"], r["P_bat_cruise_des_W"]))
    else:  # ninguna cumple todo: la que más requisitos cumple, luego la más barata
        best = max(rows, key=lambda r: (sum(r[k] for k in r if k.startswith("ok_")), -r["cost_eur"]))
    return {"best": best, "rows": rows}


def run(inp: dict, make_plots: bool = True, quiet: bool = False) -> dict:
    op = inp["operation"]
    v_cr = op["cruise_speed_kmh"] * KMH
    rho = inp["water"]["density_kg_m3"]
    unit_m = inp["architecture"]["unit_mass_estimate_kg"]

    # ---- optimización: hélice × batería × relación de poleas -------------------------
    opt = optimize(inp)
    prop_key, bat_key = opt["best"]["prop"], opt["best"]["battery"]
    inp = resolve(inp, prop_key, bat_key)
    bat = inp["battery"]["options"][bat_key]
    ms = hydro.masses(inp, bat["mass_kg"], unit_m)
    mass = ms["total_kg"]
    ratio_best, ratio_rows = select_ratio(inp, mass, bat_key)
    drv = Drive(inp, ratio_best["z_motor"], ratio_best["z_shaft"], bat_key)
    hist = opt["rows"]
    bat = inp["battery"]["options"][bat_key]
    E_bat = power.battery_energy_wh(bat)
    E_use = E_bat * inp["battery"]["usable_dod"]
    hs = hydro.hydrostatics(inp, mass)
    hsp = hydro.hull_speed(inp)

    # ---- barrido de velocidad -----------------------------------------------------
    v0, v1, dv = op["speed_sweep_kmh"]
    vk = np.arange(v0, v1 + 1e-9, dv)
    vs = vk * KMH
    res = hydro.resistance(inp, mass, vs)
    sweep = []
    for i, V in enumerate(vs):
        row = {"v_kmh": vk[i], "Fr_L": res["Fr_L"][i], "R_N": res["R"][i],
               "R_low_N": res["R_low"][i], "R_high_N": res["R_high"][i],
               "RF_N": res["RF"][i], "RTR_N": res["RTR"][i], "RW_N": res["RW"][i],
               "Rair_N": res["Rair"][i]}
        for band, key in (("nom", "R"), ("des", "R_high")):
            st = drv.at_speed(V, float(res[key][i]), bat["v_nom"])
            row[f"P_eff_{band}_W"] = st["P_eff"]
            row[f"P_shaft_{band}_W"] = st["prop"]["PD"]
            row[f"P_bat_{band}_W"] = st["P_bat"]
            row[f"I_bat_{band}_A"] = st["I_bat"]
            row[f"rpm_prop_{band}"] = st["prop"]["n"] * 60
            row[f"eta_total_{band}"] = st["eta_total"]
            row[f"eta0_{band}"] = st["prop"]["eta0"]
            row[f"feasible_{band}"] = st["feasible"]
            row[f"autonomy_{band}_h"] = E_use / st["P_bat"] if st["P_bat"] > 0 else math.inf
            row[f"range_{band}_km"] = row[f"autonomy_{band}_h"] * vk[i]
            row[f"Wh_per_km_{band}"] = st["P_bat"] / vk[i]
        sweep.append(row)

    # ---- crucero, máxima, bollard ----------------------------------------------------
    cr_nom = drv.at_speed(v_cr, R_at(inp, mass, v_cr, "nominal"), bat["v_nom"])
    cr_des = drv.at_speed(v_cr, R_at(inp, mass, v_cr, "design"), bat["v_nom"])
    vmax = {
        "design_vmin": drv.max_speed(mass, bat["v_min"], "design"),
        "nominal_vmin": drv.max_speed(mass, bat["v_min"], "nominal"),
        "design_vnom": drv.max_speed(mass, bat["v_nom"], "design"),
        "nominal_vnom": drv.max_speed(mass, bat["v_nom"], "nominal"),
    }
    bol_f = drv.bollard(bat["v_nom"])
    bol_r = drv.bollard(bat["v_nom"], inp["motor"]["reverse_current_frac"])
    # reversa: hélice de paso fijo girando al revés rinde ~ 60–70 % del empuje avante
    rev_eff = 0.65   # [ESTIMADO: hélice de fueraborda en marcha atrás 0.55–0.75 del empuje avante a igual potencia]
    bol_r["T_shaft"] *= rev_eff
    bol_r["T_horiz"] *= rev_eff

    # tiempo sostenible a velocidades altas
    T_amb = inp["air"]["temp_max_c"]
    sustain = []
    for vk_h in [7.0, 8.0, 9.0, 10.0, 11.0, 12.0]:
        V = vk_h * KMH
        for band in ("nominal", "design"):
            st = drv.at_speed(V, R_at(inp, mass, V, band), bat["v_nom"])
            t_E = E_use / st["P_bat"] * 60
            t_th = drv.motor.time_to_limit_s(st["P_loss_motor"], T_amb) / 60
            sustain.append({"v_kmh": vk_h, "band": band, "feasible": st["feasible"],
                            "limiter": drv.limiter(st) if not st["feasible"] else "—",
                            "P_bat_W": st["P_bat"], "I_bat_A": st["I_bat"],
                            "t_energy_min": t_E, "t_thermal_min": t_th,
                            "t_sustain_min": min(t_E, t_th) if st["feasible"] else 0.0})

    # condiciones adversas: viento de proa + olas
    adv = drv.max_speed(mass, bat["v_min"], "design", wind_ms=op["design_headwind_m_s"], waves=True)
    sog_adv = adv["V"] - op["design_current_m_s"]

    # ---- geometría de la cola larga ---------------------------------------------------
    lay = geometry.layout(inp, hs["draft_m"])

    # ---- cavitación ---------------------------------------------------------------
    h_shaft = lay["prop_center_depth_mm"] / 1000
    cav = {}
    for name, st in (("bollard", None), ("cruise", cr_des), ("vmax", vmax["design_vmin"])):
        if st is None:
            T, n, Va = bol_f["T_shaft"], bol_f["n_prop_rpm"] / 60, 0.0
        else:
            T, n, Va = st["T_shaft"], st["prop"]["n"], st["Va"]
        bur = drv.prop.burrill(T, n, Va, h_shaft, inp["water"])
        from p1calc.prop import burrill_tau_limit
        cav[name] = {"T_N": T, "n_rpm": n * 60,
                     "keller_min_BAR": drv.prop.keller_min_bar(T, h_shaft, inp["water"]),
                     "BAR": drv.prop.BAR, **bur, "tau_limit": burrill_tau_limit(bur["sigma07"])}

    # ---- térmico ------------------------------------------------------------------
    therm = {}
    for name, st in (("cruise_design", cr_des), ("vmax_design", vmax["design_vmin"])):
        therm[name] = {"P_loss_motor_W": st["P_loss_motor"], "P_loss_esc_W": st["P_loss_esc"],
                       "T_motor_steady_C": drv.motor.steady_temp(st["P_loss_motor"], T_amb),
                       "t_to_limit_min": drv.motor.time_to_limit_s(st["P_loss_motor"], T_amb) / 60}
    bol_th = {"P_loss_motor_W": bol_f["P_loss_motor"],
              "t_to_limit_min": drv.motor.time_to_limit_s(bol_f["P_loss_motor"], T_amb) / 60}
    therm["bollard"] = bol_th

    # ---- ESC / cables / fusible ---------------------------------------------------------
    I_bat_peak = max(vmax["design_vmin"]["I_bat"], bol_f["I_bat"])
    esc = drv.esc
    esc_margin = esc["i_cont_a"] / I_bat_peak - 1
    I_phase = inp["motor"]["current_limit_a"]
    cab_dc = power.cable(inp, I_bat_peak, inp["electrical"]["len_battery_to_esc_m"], bat["v_min"])
    cab_ph = power.cable(inp, I_phase, inp["electrical"]["len_esc_to_motor_m"], bat["v_min"])
    fus = power.fuse(inp, I_bat_peak, cab_dc["ampacity_a"])

    # ---- mecánica ----------------------------------------------------------------
    eta_tr = drv.eta_tr
    Q_lock_m = drv.motor.kt * inp["motor"]["current_limit_a"]          # torque motor al límite
    Q_lock = Q_lock_m * drv.ratio * eta_tr                              # en el eje de hélice
    Q_normal_max = max(Q_lock, bol_f["Q_prop"], vmax["design_vmin"]["prop"]["Q"])
    pin = mech.shear_pin(inp, inp["propeller"]["shear_pin"]["target_factor_vs_qmax"] * Q_normal_max)
    belt = mech.belt_checks(inp, Q_lock_m, drv.z_motor, drv.z_shaft, pin["Q_shear_Nm"])
    T_ax = max(bol_f["T_shaft"], vmax["design_vmin"]["T_shaft"])
    p_spec = inp["propeller"]["options"][inp["propeller"]["chosen"]]
    F_side = 0.15 * T_ax + p_spec["mass_kg"] * 9.81      # [ESTIMADO: fuerza lateral por flujo oblicuo ~15 % T]
    n_max = max(bol_f["n_prop_rpm"], vmax["design_vnom"]["prop"]["n"] * 60)
    shaft = mech.shaft_checks(inp, lay, Q_normal_max, pin["Q_shear_Nm"], belt["F_radial_N"],
                              T_ax, F_side, n_max)
    brg = mech.bearing_life(inp, lay, belt["F_radial_N"] * cr_des["Q_m"] / Q_lock_m,
                            cr_des["T_shaft"], cr_des["prop"]["n"] * 60)
    brg_max = mech.bearing_life(inp, lay, belt["F_radial_N"], T_ax, n_max)

    # masas concentradas de la unidad (u, v en mm; marco local) [ESTIMADO pre-CAD]
    sh = inp["shaft"]
    tube_lin = sh["tube_density_kg_m3"] * math.pi * ((sh["tube_od_mm"] / 1000) ** 2 - ((sh["tube_od_mm"] - 2 * sh["tube_wall_mm"]) / 1000) ** 2) / 4
    e = lay["e_mm"]
    Ltube = lay["tube_length_mm"]
    um = {
        "motor": (drv.motor.mass, lay["u_plate_aft"] + 45, lay["motor_v_mm"]),
        "placa+cuna+tapa+caña": (2.2, -40, 30),
        "poleas+rodamientos": (0.45, lay["u_pulley_c"], -e + 40),
        "tubo": (tube_lin * Ltube / 1000, lay["u_tube_top"] + Ltube / 2, -e),
        "eje": (shaft["mass_kg"], (lay["u_shaft_top"] + lay["u_shaft_bot"]) / 2, -e),
        "carcasa inf.+patín+protector": (0.9, lay["s_prop_mm"] - 20, -e - 40),
        "hélice": (p_spec["mass_kg"], lay["s_prop_mm"], -e),
    }
    inert = mech.unit_inertia(inp, lay, um)
    # brazo de contacto del patín (punto más bajo, delante de la hélice)
    r_c = math.hypot(lay["s_prop_mm"] - 60, -e - p_spec["D_mm"] / 2 - 15) / 1000
    imp = mech.impact_force(inp, inert["I_pivot_kgm2"], r_c)
    # momentos de basculación
    M_fwd = bol_f["T_shaft"] * e / 1000          # empuje avante: clava la cola contra el tope
    M_rev = bol_r["T_shaft"] * e / 1000          # marcha atrás: tiende a levantar la cola
    M_det = inp["mount"]["detent_release_moment_nm"]
    det = mech.detent(inp, M_det)
    hold_rev = inert["M_gravity_Nm"] + M_det
    kick = {
        "M_thrust_fwd_Nm": M_fwd, "M_thrust_rev_Nm": M_rev, "M_gravity_Nm": inert["M_gravity_Nm"],
        "M_detent_Nm": M_det, "fs_reverse_hold": hold_rev / max(M_rev, 1e-6),
        "M_release_running_fwd_Nm": hold_rev + M_fwd,
        # fuerza horizontal en el patín (a profundidad) que dispara el kick-up en marcha avante
        "F_release_at_skeg_fwd_N": (hold_rev + M_fwd) / (abs(geometry.local_to_boat(lay["s_prop_mm"] - 60, -e - p_spec["D_mm"] / 2 - 15, lay["theta_rad"], (0, 0))[1]) / 1000),
    }

    # ---- cargas por caso de carga (las usa 04_diseno/structural.py) ------------------------
    W_unit = inert["mass_kg"] * 9.81
    loadcases = {
        "LC1_empuje_avance": {"F_shaft_N": bol_f["T_shaft"], "M_pivot_Nm": M_fwd,
                              "desc": "Empuje máximo sostenido avante (bollard al límite de corriente)"},
        "LC2_marcha_atras": {"F_shaft_N": bol_r["T_shaft"], "M_pivot_Nm": M_rev,
                             "desc": "Empuje máximo en marcha atrás (límite de firmware)"},
        "LC3_rotor_trabado": {"Q_shaft_Nm": Q_lock, "Q_motor_Nm": Q_lock_m, "Fe_belt_N": belt["Fe_N"],
                              "desc": "Rotor trabado al límite de corriente del ESC"},
        "LC4_golpe_helice": {"Q_shaft_Nm": pin["Q_shear_Nm"], "Fe_belt_N": belt["Fe_at_shear_pin_N"],
                             "desc": "Golpe de hélice: torque hasta corte del pasador"},
        "LC5_varada_impacto": {"F_N": imp["F_peak_N"], "r_contact_m": r_c,
                               "desc": "Impacto del patín en arena/objeto a v de impacto"},
        "LC6_ola_vibracion": {"f_blade_hz": drv.prop.Z * cr_des["prop"]["n"],
                              "F_alt_N": 0.15 * cr_des["T_shaft"], "W_unit_N": W_unit,
                              "slam_g": inp["mount"]["wave_slam_g"],
                              "desc": "Fatiga: ±15 % del empuje a frecuencia de paso de pala + golpe de ola"},
        "LC7_manipulacion": {"F_N": inp["mount"]["handling_load_n"],
                             "desc": "Manipulación: carga en el extremo de la caña / izado"},
    }

    # ---- sensibilidad --------------------------------------------------------------
    sens = sensitivity(inp, ratio_best, bat_key, mass)

    # ---- criterios de éxito -----------------------------------------------------------
    success = {
        "bollard_pull_min_N": round(0.85 * bol_f["T_horiz"], 0),
        "bollard_pull_pred_N": bol_f["T_horiz"],
        "cruise_speed_kmh": op["cruise_speed_kmh"],
        "cruise_P_bat_max_W": round(cr_des["P_bat"], 0),
        "endurance_min_h": op["cruise_time_h"],
        "vmax_min_kmh": round(vmax["nominal_vmin"]["V"] * 3.6 * 0.9, 1),
        "watertight_after_immersion": "0 g de agua en caja ESC tras 30 min a 0,5 m (T1)",
        "T_motor_case_max_C": 80.0,
        "T_printed_parts_max_C": inp["materials"]["PETG"]["t_service_max_c"],
        "kill_time_max_s": inp["electrical"]["kill_switch_response_s_max"],
    }

    out = {
        "inputs_version": inp["meta"]["version"],
        "masses": ms, "hydrostatics": hs, "hull_speed": hsp,
        "optimization": hist, "requirements_met": opt["best"]["all_ok"],
        "selection": {"propeller": inp["propeller"]["chosen"], "prop_model": drv.prop.model,
                      "motor": drv.motor.name, "esc": inp["esc"]["chosen"],
                      "battery": bat_key, "battery_desc": bat["desc"],
                      "z_motor": drv.z_motor, "z_shaft": drv.z_shaft, "ratio": drv.ratio},
        "ratio_sweep": ratio_rows,
        "battery": {"key": bat_key, "E_nom_wh": E_bat, "E_usable_wh": E_use,
                    "E_required_wh": power.required_energy_wh(inp, cr_des["P_bat"]),
                    "options": power.select_battery(inp, power.required_energy_wh(inp, cr_des["P_bat"]), I_bat_peak)[1],
                    "mass_kg": bat["mass_kg"], "price_eur": bat["price_eur"],
                    "C_rate_peak": I_bat_peak / bat["ah"]},
        "cruise": {"nominal": _slim(cr_nom), "design": _slim(cr_des),
                   "autonomy_nominal_h": E_use / cr_nom["P_bat"],
                   "autonomy_design_h": E_use / cr_des["P_bat"]},
        "vmax": {k: _slim(v) for k, v in vmax.items()},
        "adverse": {"vmax_headwind_waves_kmh": adv["V"] * 3.6, "sog_against_current_kmh": sog_adv * 3.6,
                    "ok_min_sog": sog_adv * 3.6 >= op["min_speed_over_ground_kmh"]},
        "bollard_fwd": bol_f, "bollard_rev": bol_r, "sustain": sustain,
        "cavitation": cav, "thermal": therm,
        "esc": {"i_cont_a": esc["i_cont_a"], "I_bat_peak_a": I_bat_peak, "margin_frac": esc_margin,
                "ok": esc_margin >= inp["esc"]["margin_min_frac"]},
        "cables": {"dc": cab_dc, "phase": cab_ph}, "fuse": fus,
        "mech": {"Q_lock_motor_Nm": Q_lock_m, "Q_lock_shaft_Nm": Q_lock, "Q_normal_max_Nm": Q_normal_max,
                 "shear_pin": pin, "belt": belt, "shaft": shaft, "bearing_cruise": brg,
                 "bearing_max": brg_max, "detent": det, "inertia": inert, "unit_masses": um,
                 "impact": imp, "kickup": kick, "F_side_prop_N": F_side},
        "layout": lay, "loadcases": loadcases, "sensitivity": sens, "success": success,
        "sweep": sweep,
    }
    save_json(out, "sizing.json")
    write_tables(out, inp)
    if make_plots:
        plots(out, inp)
    if not quiet:
        print_summary(out)
    return out


def _fmt_t(x: float) -> str:
    return "∞" if math.isinf(x) else f"{x:.0f}"


def _slim(st: dict) -> dict:
    keep = {k: v for k, v in st.items() if not isinstance(v, dict)}
    if "prop" in st:
        keep["prop_n_rpm"] = st["prop"]["n"] * 60
        keep["prop_Q_Nm"] = st["prop"]["Q"]
        keep["prop_J"] = st["prop"]["J"]
        keep["prop_eta0"] = st["prop"]["eta0"]
        keep["P_shaft_W"] = st["prop"]["PD"]
        keep["V_kmh"] = st["V"] * 3.6
    return keep


# =============================================================================
SENS_PARAMS = [
    ("load.mass_per_person_kg", 0.20, "Masa por persona"),
    ("resistance.wave_cw", 0.30, "Coef. de olas c_w (calibración)"),
    ("boat.lwl_m", 0.10, "Eslora de flotación"),
    ("boat.hull_mass_kg", 0.30, "Masa del casco"),
    ("propeller.efficiency_factor", 0.10, "Rendimiento de hélice (modelo)"),
    ("propeller.guard.thrust_loss_frac", 0.50, "Pérdida por protector"),
    ("architecture.shaft_angle_deg", 0.20, "Ángulo de eje"),
    ("boat.transom_beam_m", 0.20, "Ancho de espejo sumergido"),
    ("motor.options.OR6374_190.r_ohm", 0.30, "Resistencia del motor"),
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


def sensitivity(inp, ratio_best, bat_key, mass0):
    """Efecto de ±Δ en cada entrada incierta sobre P_bat de crucero y V_max."""
    v_cr = inp["operation"]["cruise_speed_kmh"] * KMH
    bat = inp["battery"]["options"][bat_key]

    def evaluate(ii):
        ms = hydro.masses(ii, bat["mass_kg"], ii["architecture"]["unit_mass_estimate_kg"])
        drv = Drive(ii, ratio_best["z_motor"], ratio_best["z_shaft"], bat_key)
        cr = drv.at_speed(v_cr, R_at(ii, ms["total_kg"], v_cr, "design"), bat["v_nom"])
        vm = drv.max_speed(ms["total_kg"], bat["v_min"], "design")
        return cr["P_bat"], vm["V"] * 3.6

    base_P, base_V = evaluate(inp)
    rows = []
    for path, rel, label in SENS_PARAMS:
        try:
            v0 = _get(inp, path)
        except KeyError:
            continue
        out = {}
        for sgn in (-1, 1):
            ii = copy.deepcopy(inp)
            _set(ii, path, v0 * (1 + sgn * rel))
            P, V = evaluate(ii)
            out[sgn] = (P, V)
        dP = (max(out[1][0], out[-1][0]) - base_P) / base_P
        dV = (min(out[1][1], out[-1][1]) - base_V) / base_V
        rows.append({"param": path, "label": label, "rel_change": rel,
                     "P_minus": out[-1][0], "P_plus": out[1][0],
                     "V_minus": out[-1][1], "V_plus": out[1][1],
                     "dP_worst_frac": dP, "dV_worst_frac": dV,
                     "swing_P_frac": abs(out[1][0] - out[-1][0]) / base_P})
    rows.sort(key=lambda r: -r["swing_P_frac"])
    return {"base_P_bat_cruise_W": base_P, "base_vmax_kmh": base_V, "rows": rows,
            "top3": [r["label"] for r in rows[:3]]}


# =============================================================================
def write_tables(o: dict, inp: dict):
    """Tablas Markdown con los resultados (se insertan en 02_calculos.md por docgen)."""
    L = []
    s, ms, hs = o["selection"], o["masses"], o["hydrostatics"]
    cr, vm = o["cruise"], o["vmax"]
    L.append("| Magnitud | Valor | Etiqueta |\n|---|---|---|")
    rows = [
        ("Masa total de diseño", f"{ms['total_kg']:.0f} kg", "[CALCULADO]"),
        ("Carga útil vs placa de capacidad", f"{ms['payload_kg']:.0f} / {ms['capacity_kg']:.0f} kg ({ms['capacity_ratio']*100:.0f} %)", "[CALCULADO]"),
        ("Calado / francobordo", f"{hs['draft_m']*1000:.0f} / {hs['freeboard_m']*1000:.0f} mm", "[CALCULADO]"),
        ("Velocidad de casco (Fr_L=0.40)", f"{o['hull_speed']['v_hull_kmh']:.2f} km/h", "[CALCULADO]"),
        ("Fr_L a velocidad de crucero", f"{cr['design']['V']/math.sqrt(9.81*inp['boat']['lwl_m']):.3f}", "[CALCULADO]"),
        ("R crucero (nominal / diseño)", f"{cr['nominal']['R']:.0f} / {cr['design']['R']:.0f} N", "[CALCULADO]"),
        ("Empuje en el eje en crucero (diseño)", f"{cr['design']['T_shaft']:.0f} N", "[CALCULADO]"),
        ("Hélice", f"{s['propeller']} — modelo {s['prop_model']}", "[SUPUESTO]"),
        ("rpm hélice / J / η0 crucero (diseño)", f"{cr['design']['prop_n_rpm']:.0f} rpm / {cr['design']['prop_J']:.2f} / {cr['design']['prop_eta0']:.2f}", "[CALCULADO]"),
        ("Potencia al eje crucero (diseño)", f"{cr['design']['P_shaft_W']:.0f} W", "[CALCULADO]"),
        ("Potencia de batería crucero (nominal / diseño)", f"{cr['nominal']['P_bat']:.0f} / {cr['design']['P_bat']:.0f} W", "[CALCULADO]"),
        ("Rendimiento total batería→R·V (diseño)", f"{cr['design']['eta_total']*100:.0f} %", "[CALCULADO]"),
        ("Relación de correa", f"{s['z_motor']}T : {s['z_shaft']}T = {s['ratio']:.2f}", "[CALCULADO]"),
        ("Batería elegida", f"{s['battery_desc']}", "[CALCULADO]"),
        ("Energía requerida / usable", f"{o['battery']['E_required_wh']:.0f} / {o['battery']['E_usable_wh']:.0f} Wh", "[CALCULADO]"),
        ("Autonomía a crucero (nominal / diseño)", f"{cr['autonomy_nominal_h']:.2f} / {cr['autonomy_design_h']:.2f} h", "[CALCULADO]"),
        ("V máx. (diseño, batería baja)", f"{vm['design_vmin']['V_kmh']:.1f} km/h — limita: {vm['design_vmin'].get('limiter','')}", "[CALCULADO]"),
        ("V máx. (nominal, batería nominal)", f"{vm['nominal_vnom']['V_kmh']:.1f} km/h", "[CALCULADO]"),
        ("Bollard pull avante (horizontal)", f"{o['bollard_fwd']['T_horiz']:.0f} N ({o['bollard_fwd']['T_horiz']/9.81:.1f} kgf) — limita: {o['bollard_fwd']['limiter']}", "[CALCULADO]"),
        ("Bollard pull marcha atrás", f"{o['bollard_rev']['T_horiz']:.0f} N", "[CALCULADO]"),
        ("Corriente pico de batería / margen ESC", f"{o['esc']['I_bat_peak_a']:.0f} A / {o['esc']['margin_frac']*100:.0f} %", "[CALCULADO]"),
        ("Cable DC / fases", f"{o['cables']['dc']['section_mm2']} mm² ({o['cables']['dc']['drop_frac']*100:.1f} %) / {o['cables']['phase']['section_mm2']} mm² ({o['cables']['phase']['drop_frac']*100:.1f} %)", "[CALCULADO]"),
        ("Fusible principal", f"{o['fuse']['rating_a']} A", "[CALCULADO]"),
        ("Pasador de corte", f"Ø{o['mech']['shear_pin']['d_std_mm']} mm {o['mech']['shear_pin']['material']} → corta a {o['mech']['shear_pin']['Q_shear_Nm']:.1f} N·m", "[CALCULADO]"),
        ("Velocidad crítica del eje / rpm máx.", f"{o['mech']['shaft']['n_crit_rpm']:.0f} / {o['mech']['shaft']['n_max_rpm']:.0f} rpm", "[CALCULADO]"),
        ("Largo de eje / tubo", f"{o['layout']['shaft_length_mm']:.0f} / {o['layout']['tube_length_mm']:.0f} mm", "[CALCULADO]"),
    ]
    for r in rows:
        L.append(f"| {r[0]} | {r[1]} | {r[2]} |")
    main = "\n".join(L)

    # tabla de barrido (cada 1 km/h)
    S = ["| v [km/h] | Fr_L | R nom [N] | R diseño [N] | P_bat nom [W] | P_bat diseño [W] | rpm hélice | Autonomía nom [h] | Autonomía diseño [h] | Wh/km diseño |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in o["sweep"]:
        if abs(r["v_kmh"] - round(r["v_kmh"])) < 1e-6 and 2 <= r["v_kmh"] <= 13:
            fe = "" if r["feasible_des"] else " ✗"
            S.append(f"| {r['v_kmh']:.0f} | {r['Fr_L']:.2f} | {r['R_N']:.0f} | {r['R_high_N']:.0f} | "
                     f"{r['P_bat_nom_W']:.0f} | {r['P_bat_des_W']:.0f}{fe} | {r['rpm_prop_des']:.0f} | "
                     f"{r['autonomy_nom_h']:.2f} | {r['autonomy_des_h']:.2f} | {r['Wh_per_km_des']:.0f} |")
    sweep = "\n".join(S)

    T = ["| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |",
         "|---|---|---|---|---|---|---|---|"]
    for r in o["sustain"]:
        T.append(f"| {r['v_kmh']:.0f} | {r['band']} | {'sí' if r['feasible'] else 'no (' + r['limiter'] + ')'} | "
                 f"{r['P_bat_W']:.0f} | {r['I_bat_A']:.0f} | {r['t_energy_min']:.0f} | "
                 f"{_fmt_t(r['t_thermal_min'])} | "
                 f"{r['t_sustain_min']:.0f} |")
    sustain = "\n".join(T)

    Sx = ["| Entrada | ±Δ | P_bat crucero (−/+) [W] | V máx (−/+) [km/h] | Variación P | ",
          "|---|---|---|---|---|"]
    for r in o["sensitivity"]["rows"]:
        Sx.append(f"| {r['label']} | ±{r['rel_change']*100:.0f} % | {r['P_minus']:.0f} / {r['P_plus']:.0f} | "
                  f"{r['V_minus']:.1f} / {r['V_plus']:.1f} | {r['swing_P_frac']*100:.0f} % |")
    sens = "\n".join(Sx)

    with open(RESULTS_DIR / "sizing_tablas.md", "w", encoding="utf-8") as f:
        f.write("<!-- generado por sizing.py — no editar a mano -->\n\n")
        f.write("## Resumen\n\n" + main + "\n\n## Barrido de velocidad\n\n" + sweep +
                "\n\n## Tiempo sostenible a velocidad alta\n\n" + sustain +
                "\n\n## Sensibilidad\n\n" + sens + "\n")
    o["_tables"] = {"main": main, "sweep": sweep, "sustain": sustain, "sens": sens}


def plots(o: dict, inp: dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG_DIR.mkdir(exist_ok=True)
    sw = o["sweep"]
    v = np.array([r["v_kmh"] for r in sw])
    def col(k):
        return np.array([r[k] for r in sw], dtype=float)
    vh = o["hull_speed"]["v_hull_kmh"]
    vc = inp["operation"]["cruise_speed_kmh"]

    # R(v)
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.fill_between(v, col("R_low_N"), col("R_high_N"), color="#9ecae1", alpha=0.5, label="Banda de incertidumbre")
    ax.plot(v, col("R_N"), "k-", lw=2, label="R total (nominal)")
    ax.plot(v, col("RF_N"), "--", label="Fricción ITTC-57·(1+k)")
    ax.plot(v, col("RTR_N"), "--", label="Espejo sumergido (Holtrop)")
    ax.plot(v, col("RW_N"), "--", label="Olas/joroba (calibrable)")
    ax.axvline(vh, color="gray", ls=":", label=f"Vel. de casco {vh:.1f} km/h")
    ax.axvline(vc, color="green", ls=":", label=f"Crucero {vc:.1f} km/h")
    ax.set_xlabel("Velocidad [km/h]"); ax.set_ylabel("Resistencia [N]")
    ax.set_title(f"R(v) — jon boat {inp['boat']['lwl_m']} m LWL, {o['masses']['total_kg']:.0f} kg")
    ax.grid(alpha=0.3); ax.legend(fontsize=8); ax.set_xlim(v[0], v[-1]); ax.set_ylim(0, None)
    fig.tight_layout(); fig.savefig(FIG_DIR / "R_v.png", dpi=130); plt.close(fig)

    # P(v)
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(v, col("P_eff_des_W"), label="P efectiva R·v (diseño)")
    ax.plot(v, col("P_shaft_des_W"), label="P al eje de hélice (diseño)")
    ax.plot(v, col("P_bat_des_W"), "k-", lw=2, label="P de batería (diseño)")
    ax.plot(v, col("P_bat_nom_W"), "k--", label="P de batería (nominal)")
    gp = hydro.gerr_power_w(inp, o["masses"]["total_kg"], v / 3.6)
    ax.plot(v, gp, ":", color="purple", label="Contraste Gerr (P al eje)")
    feas = np.array([r["feasible_des"] for r in sw])
    if (~feas).any():
        ax.axvspan(v[~feas].min(), v[-1], color="red", alpha=0.08, label="Fuera de límites (diseño)")
    ax.axvline(vc, color="green", ls=":")
    ax.set_xlabel("Velocidad [km/h]"); ax.set_ylabel("Potencia [W]")
    ax.set_title("Potencia vs velocidad"); ax.grid(alpha=0.3); ax.legend(fontsize=8)
    ax.set_ylim(0, 4000); ax.set_xlim(v[0], v[-1])
    fig.tight_layout(); fig.savefig(FIG_DIR / "P_v.png", dpi=130); plt.close(fig)

    # autonomía(v)
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(v, col("autonomy_nom_h"), label="Autonomía (nominal)")
    ax.plot(v, col("autonomy_des_h"), "k-", lw=2, label="Autonomía (diseño)")
    ax2 = ax.twinx()
    ax2.plot(v, col("range_des_km"), "C2--", label="Alcance (diseño) [km]")
    ax.axhline(inp["operation"]["cruise_time_h"], color="red", ls=":", label="Requisito 2 h")
    ax.axvline(vc, color="green", ls=":")
    ax.set_xlabel("Velocidad [km/h]"); ax.set_ylabel("Autonomía [h]"); ax2.set_ylabel("Alcance [km]")
    ax.set_title(f"Autonomía con {o['selection']['battery_desc']}")
    ax.set_ylim(0, 8); ax.grid(alpha=0.3)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG_DIR / "autonomia_v.png", dpi=130); plt.close(fig)

    # sensibilidad (tornado)
    rows = o["sensitivity"]["rows"]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    base = o["sensitivity"]["base_P_bat_cruise_W"]
    for i, r in enumerate(reversed(rows)):
        lo, hi = sorted([r["P_minus"], r["P_plus"]])
        ax.barh(i, hi - lo, left=lo, color="#3182bd")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{r['label']} ±{r['rel_change']*100:.0f}%" for r in reversed(rows)], fontsize=8)
    ax.axvline(base, color="k")
    ax.set_xlabel("P de batería en crucero [W] (banda de diseño)")
    ax.set_title("Sensibilidad (tornado)"); ax.grid(alpha=0.3, axis="x")
    fig.tight_layout(); fig.savefig(FIG_DIR / "sensibilidad.png", dpi=130); plt.close(fig)


def print_summary(o: dict):
    print("=" * 72)
    print("P1 sizing — resumen")
    print("=" * 72)
    print(o["_tables"]["main"])
    print()
    print("Sensibilidad — top 3:", ", ".join(o["sensitivity"]["top3"]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default=None)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--no-plots", action="store_true")
    a = ap.parse_args(argv)
    inp = load_inputs(a.inputs)
    run(inp, make_plots=not a.no_plots, quiet=a.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
