#!/usr/bin/env python3
"""structural.py — Cálculo estructural a mano de P1: FS por pieza y por caso de carga.

Resistencias de diseño del PETG impreso (inputs.yaml → materials):
    S_corta    = σ_XY · f_agua · f_temp · f_proceso          (cargas de corta duración)
    S_sost     = S_corta · f_creep                            (cargas sostenidas horas–días)
    S_fat      = S_corta · f_fatiga                           (amplitud, 1e7–1e8 ciclos: paso de pala)
    S_lcf      = S_corta · f_fatiga_lcf                       (amplitud, ~1e5–1e6 ciclos: olas, maniobras)
    × f_Z si la tensión cruza capas (se evita por orientación; ver META de cada pieza)
FS = S / σ_aplicada. Requisito: FS ≥ 3 (impresas), ≥ 2 (metálicas).
Salidas: resultados/estructural.json, resultados/estructural_tabla.md. Exit ≠ 0 si algún
FS requerido no se cumple y no está justificado (JUSTIFIED).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import params as P  # noqa: E402

G = 9.81

# Casos aceptados con FS < objetivo, con justificación explícita (se reportan, no fallan)
JUSTIFIED = {
    ("P1-PRP-02", "LC5 fusible"): "Pieza fusible: DEBE romper a F_fusible (diseño intencional, FS≈1 a esa carga).",
}


def allowables(inp):
    m = inp["materials"]["PETG"]
    f = inp["materials"]["design_factors"]
    S = m["sigma_t_xy_mpa"] * f["f_water"] * f["f_temp"] * f["f_process"]
    return {"short": S, "sust": S * f["f_creep"], "fat": S * f["f_fatigue"],
            "lcf": S * f.get("f_fatigue_lcf", f["f_fatigue"]), "fz": f["f_z"], "sigma_xy": m["sigma_t_xy_mpa"]}


def row(rows, part, lc, model, sigma, kind, A, target, extra=""):
    Sa = A[kind] if isinstance(kind, str) else kind
    fs = Sa / sigma if sigma > 0 else math.inf
    ok = fs >= target - 1e-9
    just = JUSTIFIED.get((part, lc))
    rows.append({"part": part, "load_case": lc, "model": model, "sigma_MPa": round(sigma, 3),
                 "allowable": kind if isinstance(kind, str) else "metal", "S_MPa": round(Sa, 2),
                 "FS": round(fs, 2) if fs != math.inf else 999, "target": target,
                 "ok": bool(ok or just), "justification": just or "", "note": extra})


def main():
    p = P.load()
    inp, sz = p.inp, p.sz
    A = allowables(inp)
    T3, T2 = inp["materials"]["fs_target_printed"], inp["materials"]["fs_target_metal"]
    m = sz["mech"]
    rows = []

    # ------------------------- cargas -------------------------
    T_bol = sz["bollard_fwd"]["T_shaft"]                    # corta
    T_cr = sz["cruise"]["design"]["T_shaft"]                # sostenida
    T_rev = sz["bollard_rev"]["T_shaft"]
    F_imp = m["impact"]["F_peak_N"]                          # pico dinámico (impulso)
    F_fuse = p.skeg_fuse_force
    M_rel = m["kickup"]["M_release_running_fwd_Nm"]
    M_grav = m["kickup"]["M_gravity_Nm"]
    W_unit = m["inertia"]["mass_kg"] * G
    slam = inp["mount"]["wave_slam_g"]
    F_hand = inp["mount"]["handling_load_n"]
    lay = p.layout
    amp = inp["architecture"]["blade_rate_amplitude_frac"]   # ±fracción de T a paso de pala
    L_tail = (lay["s_prop_mm"] - p.cradle_u1 / 2) / 1000    # brazo cuna→hélice
    H_imp = 0.5 * F_imp                                      # reacción en el pivote (centro de percusión)
    e = p.e / 1000

    # ------------------------- MNT-01 abrazadera -------------------------
    Tq = inp["mount"]["clamp_screw_torque_nm"]
    d = p.clamp_screw_d / 1000
    F_scr = Tq / (0.2 * d)                                   # [ESTIMADO: K=0.2 rosca seca/lubricada A4]
    F_clamp = F_scr * inp["mount"]["clamp_screws"]
    arm = (abs(p.screw_z[0]) + p.shelf_top_z / 2) / 1000
    Zc = p.clamp_w * p.leg_t**2 / 6                          # mm³ (esquina de la C)
    M_cl = F_clamp * arm
    row(rows, "P1-MNT-01", "Apriete (sostenido)", f"M = F_apriete·brazo = {F_clamp:.0f} N·{arm*1000:.0f} mm; Z = b·t²/6 (esquina de la C)",
        M_cl * 1000 / Zc, "sust", A, T3, f"apriete {Tq} N·m → {F_scr:.0f} N/tornillo")
    h_piv = (p.pivot_z + p.shelf_top_z / 2) / 1000
    M_imp = H_imp * h_piv
    row(rows, "P1-MNT-01", "LC5 impacto + apriete (corta)", f"(M_apriete + H_imp·h) / Z; H_imp = 0.5·F_pico = {H_imp:.0f} N",
        (M_cl + M_imp) * 1000 / Zc, "short", A, T3)
    M_th = (T_bol * math.cos(math.radians(p.theta))) * h_piv
    row(rows, "P1-MNT-01", "LC1 empuje avante (corta)", "(M_apriete + T·h)/Z", (M_cl + M_th) * 1000 / Zc, "short", A, T3)
    p_nut = F_scr / (40 * 40)                                # placa de reparto A4 40×40 tras la tuerca
    row(rows, "P1-MNT-01", "Apriete: apoyo de la placa de reparto (sostenido)", "p = F_tornillo / (40×40 mm)",
        p_nut, "sust", A, T3, "sin placa (solo tuerca M12) sería ~4× peor → placa obligatoria")

    # ------------------------- MNT-02 zapata -------------------------
    row(rows, "P1-MNT-02", "Apriete (sostenido, compresión)", "p = F / (π·D²/4)", F_scr / (math.pi * p.pad_d**2 / 4), "sust", A, T3)

    # ------------------------- MNT-03 base de horquilla -------------------------
    base_top = p.disc_z0 + p.disc_t
    M_ot = H_imp * (p.pivot_z - base_top) / 1000
    F_b = M_ot / (2 * 0.042)                                 # par de pernos por mejilla (42 mm)
    M_loc = F_b * 0.020
    Zb = 40 * p.disc_t**2 / 6
    row(rows, "P1-MNT-03", "LC5 vuelco (corta)", f"M_vuelco={M_ot:.1f} N·m → F_perno={F_b:.0f} N; flexión local brazo 20 mm, b=40, t={p.disc_t}",
        M_loc * 1000 / Zb, "short", A, T3)
    h_nut = 18.0
    row(rows, "P1-MNT-04", "Tuerca cautiva M6 en mejilla: arranque por corte (corta)",
        f"τ = F_perno/(2·t·h), h = {h_nut:.0f} mm; admisible 0.5·S", F_b / (2 * p.cheek_t * h_nut), 0.5 * A["short"], A, T3)

    # ------------------------- MNT-04 mejilla -------------------------
    Lf = 64.0
    hc = (p.pivot_z - base_top) / 1000
    Zin = p.cheek_t * Lf**2 / 6
    row(rows, "P1-MNT-04", "LC5 en el plano (corta)", f"M = (H/2)·h; Z = t·L²/6 (L={Lf:.0f})", (H_imp / 2) * hc * 1000 / Zin, "short", A, T3)
    F_lat = 200.0                                            # [SUPUESTO: golpe lateral en la cola reaccionado por la dirección]
    Zout = Lf * p.cheek_t**2 / 6
    row(rows, "P1-MNT-04", "Golpe lateral 200 N (corta)", "M=(F/2)·h; Z = L·t²/6 (fuera del plano)", (F_lat / 2) * hc * 1000 / Zout, "short", A, T3)
    row(rows, "P1-MNT-04", "Apoyo del perno Ø12 (corta)", "p = (H/2)/(d·t)", (H_imp / 2) / (p.tilt_pin_d * p.cheek_t), "short", A, T3)

    # ------------------------- MNT-05 cuna -------------------------
    Lc = p.cradle_u1 - 5.0
    M_dyn = 0.19 * F_imp * L_tail                            # momento dinámico máx. en barra pivotada
    M_lock = F_fuse * L_tail                                 # cola trabada: limitado por el fusible
    pc_dyn = 6 * M_dyn * 1000 / (p.tube_od * Lc**2)
    pc_lock = 6 * M_lock * 1000 / (p.tube_od * Lc**2)
    row(rows, "P1-MNT-05", "LC5 dinámico (corta)", f"p = 6M/(d·L²), M = 0.19·F·L = {M_dyn:.0f} N·m", pc_dyn, "short", A, T3)
    row(rows, "P1-MNT-05", "LC5 cola trabada (corta)", f"p = 6M/(d·L²), M = F_fus·L = {M_lock:.0f} N·m", pc_lock, "short", A, T3)
    r_stop = math.hypot(30.0, p.cradle_vbot) / 1000
    F_stop = (T_cr * e + M_grav) / r_stop
    Ap = math.pi * p.stop_pad_d**2 / 4
    row(rows, "P1-MNT-05/06", "Tope de marcha (sostenido)", f"F = (T·e + M_grav)/r = {F_stop:.0f} N sobre tope Ø{p.stop_pad_d:.0f}",
        F_stop / Ap, "sust", A, T3)
    F_slam = slam * W_unit * 0.40 / r_stop                   # [ESTIMADO: CG de la unidad ~0.40 m del pivote]
    row(rows, "P1-MNT-05/06", "LC6 golpe de ola 3 g en el tope (corta)", f"F = {F_slam:.0f} N", F_slam / Ap, "short", A, T3)
    F_fat = 1.0 * W_unit * 0.40 / r_stop
    row(rows, "P1-MNT-05/06", "LC6 ola ±1 g (fatiga ~1e6 ciclos)", f"F_a = {F_fat:.0f} N", F_fat / Ap, "lcf", A, T3)
    F_piv = math.hypot(T_bol, F_stop)
    row(rows, "P1-MNT-05", "LC1 apoyo del buje del pivote (corta)", "p = F/(d·w), POM Ø20 × ancho", F_piv / (20 * p.cradle_w), "short", A, T3)
    M_fat = amp * T_cr * L_tail                              # fuerza lateral a paso de pala ±amp·T
    row(rows, "P1-MNT-05", f"LC6 paso de pala ±{amp*100:.0f} % T lateral (fatiga 1e7–1e8)", "p_a = 6M/(d·L²)",
        6 * M_fat * 1000 / (p.tube_od * Lc**2), "fat", A, T3)
    F_tb = T_bol / 4
    row(rows, "P1-MNT-05", "LC1 tuercas cautivas de la placa motriz: arranque por corte (corta)",
        "τ = (T/4)/(2·12·18) (bolsillo a 18 mm de la cara)", F_tb / (2 * 12 * 18), 0.5 * A["short"], A, T3)
    row(rows, "P1-MNT-05", "LC6 tuercas de placa motriz ±amp·T (fatiga 1e7–1e8)", "τ_a = (amp·T_cr/4)/(2·12·18)",
        amp * T_cr / 4 / (2 * 12 * 18), 0.5 * A["fat"], A, T3)
    T_rev_s = sz["bollard_rev"]["T_shaft"]
    A_floor = math.pi * ((p.cart_od / 2) ** 2 - 11.0**2)
    row(rows, "P1-MNT-05", "LC2 marcha atrás: cartucho contra el fondo del rebaje (corta)", "p = T_rev/A_anillo",
        T_rev_s / A_floor, "short", A, T3)

    # ------------------------- MNT-06 tapa (pernos pasantes) -------------------------
    F_end = M_lock / (0.8 * Lc / 1000)
    row(rows, "P1-MNT-06", "LC5 cola trabada: apoyo extremo (corta)", f"p = F_ext/(d·25), F_ext = {F_end:.0f} N", F_end / (p.tube_od * 25), "short", A, T3)
    row(rows, "P1-MNT-06", "LC5: arandela Ø24 de perno pasante (corta)", "p = (F_ext/2)/(π(24²−6.4²)/4)",
        (F_end / 2) / (math.pi * (24**2 - 6.4**2) / 4), "short", A, T3)

    # ------------------------- HSG-01 placa motriz (Al 6082-T6) -------------------------
    Sy_al = 240.0                                            # [ESTIMADO: 6082-T6 chapa ≥ 240–260 MPa]
    Se_al = 60.0                                             # [ESTIMADO: fatiga Al 6082 ~90 MPa a 5e8 ciclos × 0,7 (superficie/agua salina)]
    t_pl = p.plate_t
    Zs = 30 * t_pl**2 / 6
    row(rows, "P1-HSG-01 placa Al", "LC1 empuje bollard", f"franja cartucho→pernos: M = (T/2)·11 mm, Z = 30·t²/6 (t={t_pl:.0f})",
        (T_bol / 2) * 11 / Zs, Sy_al, A, T2)
    row(rows, "P1-HSG-01 placa Al", f"LC6 ±{amp*100:.0f} % empuje (fatiga)", "σ_a = (amp·T/2)·11/Z", (amp * T_cr / 2) * 11 / Zs, Se_al, A, T2)
    Fe_pin = m["belt"]["Fe_at_shear_pin_N"]
    Qm = m["Q_lock_motor_Nm"]
    row(rows, "P1-HSG-01 placa Al", "LC3 torque de rotor trabado en colisos M4", "p = Q/(4·r·d·t)",
        Qm / (4 * p.motor_bc / 2000) / (4 * t_pl), Sy_al, A, T2)
    row(rows, "P1-DRV-08 cartucho Al", "LC1 empuje en el labio (corte)", "τ = T/(π·Ø21·espesor labio)",
        T_bol / (math.pi * 21 * (p.layout["u_boss_aft"] - p.brg_B - 1.0 - p.plate_u_fwd)), 0.577 * Sy_al, A, T2)
    R_A = m["bearing_max"]["R_A_N"]

    # ------------------------- HSG-02 puente -------------------------
    R_B = m["bearing_max"]["R_B_N"]
    row(rows, "P1-HSG-02", "LC3 tracción en el plano (corta)", "σ = R_B/(24·t)", R_B / (24 * p.bridge_t), "short", A, T3)
    RB_pin = 2.5 * Fe_pin * lay["pulley_a_mm"] / lay["bearing_spacing_mm"]
    row(rows, "P1-HSG-02", "LC4 tirón de correa (corta)", "σ = R_B,pin/(24·t)", RB_pin / (24 * p.bridge_t), "short", A, T3)

    # ------------------------- HSG-04/07 caña: abrazaderas impresas + placa Al -------------------------
    u_aft = 85.0 + 50.0                                      # extremo de popa del tubo (HSG-06)
    u_grip = u_aft - p.tiller_len + 60.0                     # centro del puño
    L_till = (57.5 - u_grip) / 1000                          # puño → centroide de abrazaderas
    M_t = F_hand * L_till
    s_cl = (85.0 - 30.0) / 1000
    F_cl = M_t / s_cl                                        # par de fuerzas entre abrazaderas
    rt = p.tiller_tube_od / 2
    row(rows, "P1-HSG-04", "LC7 apoyo del tubo en la abrazadera (corta)", f"M = F·L = {M_t:.0f} N·m → F = M/s = {F_cl:.0f} N; p = F/(d·22)",
        F_cl / (2 * rt * 22), "short", A, T3)
    row(rows, "P1-HSG-04", "LC7 tracción de la abrazadera (2 M6, sección 2×8×22) (corta)", "σ = F/(2·8·22)",
        F_cl / (2 * 8 * 22), "short", A, T3)
    tau_pl = M_t * 1000 / (0.29 * 77 * 10.0**2)              # torsión placa 77×10 (β≈0.29 para b/t≈7.7)
    row(rows, "P1-HSG-07 placa Al", "LC7 torsión de la placa", "τ = M/(β·b·t²)", tau_pl, 0.577 * inp["shaft"]["tube_sy_mpa"], A, T2)
    F_pc = M_t / 0.060                                       # par en pernos u=20/80 → apoyo sobre la cuna
    row(rows, "P1-MNT-05", "LC7 apoyo de la placa de caña sobre la cuna (corta)", f"p = (M/0.06 m)/(20·76) = {F_pc:.0f} N / 1520 mm²",
        F_pc / (20 * p.cradle_w), "short", A, T3)

    # ------------------------- STR-01 carcasa inferior -------------------------
    M_sk = F_fuse * p.skeg_neck_lever / 1000
    row(rows, "P1-STR-01", "LC5 fusible: apoyo del tubo (corta)", "p = 6M/(d·L²), L = 45 mm", 6 * M_sk * 1000 / (p.tube_od * 45**2), "short", A, T3)
    row(rows, "P1-STR-01", "LC5 fusible: pernos del patín (corta)", "p = (F/2)/(6·2·14)", (F_fuse / 2) / (6 * 2 * 14), "short", A, T3)

    # ------------------------- PRP-02 patín (fusible) -------------------------
    Zn = p.skeg_t * p.skeg_neck_len**2 / 6
    row(rows, "P1-PRP-02", "LC5 fusible", f"σ = F_fus·h/Z en la cintura (h={p.skeg_neck_lever:.0f} mm)",
        F_fuse * p.skeg_neck_lever / Zn, p.skeg_sig_break, A, T3, "rompe a F_fusible (resistencia media húmeda)")
    V = 2.5
    F_drag = 0.5 * inp["water"]["density_kg_m3"] * V**2 * 1.2 * (p.skeg_t / 1000) * 0.14
    row(rows, "P1-PRP-02", "Arrastre a 9 km/h (sostenido)", f"F = ½ρV²·Cd·A = {F_drag:.1f} N", F_drag * p.skeg_neck_lever / Zn, "sust", A, T3)
    F_side = 0.5 * inp["water"]["density_kg_m3"] * V**2 * 1.0 * 0.014
    Zw = p.skeg_neck_len * p.skeg_t**2 / 6
    row(rows, "P1-PRP-02", "Fuerza lateral en giro (corta)", f"F = ½ρV²·C_L·A = {F_side:.0f} N, brazo 70 mm, eje débil", F_side * 70 / Zw, "short", A, T3)

    # ------------------------- PRP-01 protector -------------------------
    chord = 2 * (p.guard_ri + p.guard_t) * math.sin(math.radians(30))
    Zg = p.guard_L * p.guard_t**2 / 6
    row(rows, "P1-PRP-01", "Golpe radial 150 N en el anillo (corta)", "M = F·L/8 (arco entre uniones)", 150 * chord / 8 / Zg, "short", A, T3)

    # ------------------------- ELE-01 caja ESC -------------------------
    per = 2 * (p.esc_in[0] + p.esc_in[1] + 2 * 12)
    F_or = 3.0 * per                                         # [ESTIMADO: 3 N/mm de cordón NBR70 2.5 mm al 25 %]
    row(rows, "P1-ELE-01", "Compresión del O-ring en insertos M4 (sostenido)", f"F_total = {F_or:.0f} N / 8 insertos vs 1 kN arranque [ESTIMADO]",
        (F_or / 8) / 1000 * A["sust"], "sust", A, T3, "FS = 1000 N / F_inserto")

    # ------------------------- SAF-01 -------------------------
    row(rows, "P1-SAF-01", "Tirón del cordón 100 N (corta)", "placa 7 mm en voladizo 20 mm", 100 * 20 / (36 * 7**2 / 6), "short", A, T3)

    # ------------------------- metálicas -------------------------
    sh = inp["shaft"]
    Ztube = math.pi * (p.tube_od**4 - (p.tube_od - 2 * p.tube_wall) ** 4) / (32 * p.tube_od)
    row(rows, "P1-STR-02 tubo Al", "LC5 cola trabada (fusible)", f"σ = F_fus·L/Z = {M_lock:.0f} N·m / {Ztube:.0f} mm³",
        M_lock * 1000 / Ztube, sh["tube_sy_mpa"], A, T2)
    row(rows, "P1-STR-02 tubo Al", "LC5 dinámico", f"σ = 0.19·F·L/Z", M_dyn * 1000 / Ztube, sh["tube_sy_mpa"], A, T2)
    Ztil = math.pi * (p.tiller_tube_od**4 - (p.tiller_tube_od - 6) ** 4) / (32 * p.tiller_tube_od)
    row(rows, "P1-HSG-06 caña Al", "LC7 manipulación", "σ = M/Z (Ø30×3)", M_t * 1000 / Ztil, sh["tube_sy_mpa"], A, T2)
    tau_pin = (F_piv / 2) / (math.pi * p.tilt_pin_d**2 / 4)
    row(rows, "P1-MNT-08 perno 316", "LC1+LC5 corte doble", "τ = (F/2)/A", max(tau_pin, (H_imp / 2) / (math.pi * p.tilt_pin_d**2 / 4)),
        0.577 * sh["sy_mpa"], A, T2)
    shf = m["shaft"]
    rows.append({"part": "P1-DRV-01 eje 316", "load_case": "LC3/LC4 torsión+flexión (sizing)", "model": "ver 02_calculos.md §7",
                 "sigma_MPa": None, "allowable": "metal", "S_MPa": None, "FS": round(min(shf["fs_static"], shf["fs_fatigue_goodman"]), 2),
                 "target": T2, "ok": min(shf["fs_static"], shf["fs_fatigue_goodman"]) >= T2, "justification": "", "note": "mín(estático, fatiga)"})

    fails = [r for r in rows if not r["ok"]]
    out = {"allowables_MPa": A, "rows": rows, "n_fail": len(fails),
           "loads": {"T_bollard_N": T_bol, "T_cruise_N": T_cr, "T_rev_N": T_rev, "F_impact_peak_N": F_imp,
                     "F_skeg_fuse_N": F_fuse, "M_release_Nm": M_rel, "W_unit_N": W_unit, "F_handling_N": F_hand,
                     "M_tail_dyn_Nm": M_dyn, "M_tail_locked_Nm": M_lock}}
    (ROOT / "resultados").mkdir(exist_ok=True)
    with open(ROOT / "resultados" / "estructural.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    L = ["| Pieza | Caso de carga | Modelo | σ [MPa] | Admisible | S [MPa] | FS | Obj. | OK |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        s_ = "—" if r["sigma_MPa"] is None else f"{r['sigma_MPa']:.2f}"
        S_ = "—" if r["S_MPa"] is None else f"{r['S_MPa']:.1f}"
        ok = "✔" if r["ok"] and not r["justification"] else ("✔ (justif.)" if r["ok"] else "✘")
        L.append(f"| {r['part']} | {r['load_case']} | {r['model']} | {s_} | {r['allowable']} | {S_} | {r['FS']} | {r['target']} | {ok} |")
    with open(ROOT / "resultados" / "estructural_tabla.md", "w", encoding="utf-8") as f:
        f.write("<!-- generado por 04_diseno/structural.py -->\n" + "\n".join(L) + "\n")
    print(f"structural: {len(rows)} verificaciones, {len(fails)} con FS bajo objetivo")
    for r in fails:
        print(f"  FS BAJO: {r['part']} — {r['load_case']}: FS {r['FS']} < {r['target']}  ({r['model']})")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
