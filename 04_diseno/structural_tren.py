"""structural_tren.py — casos estructurales del grupo TREN Y ELECTRÓNICA (P1-DRV/MOT/ELE).

Cálculo a mano (modelos en cada fila). Cargas de sizing.json (mech, loads) y geometría de params_tren.
Metales: FS ≥ 2 (objetivo T2); PETG: FS ≥ 3 con admisibles de R05 (A). Admisibles de metales:
  AISI 316 recocido: σ_y = inputs shaft.sy_mpa, σ_u = su_mpa, S_e (corrosión) = se_mpa; τ = 0,577·σ.
  Al 6082-T651: R_p0,2 = 240 MPa [ESTIMADO: EN 485-2, placa 12,5–60 mm]; soldado (ZAT): 115 MPa
    [ESTIMADO: EN 1999-1-1 ρ_haz ≈ 0,48 para 6082-T6] — se usa el de ZAT en el soporte soldado.
  Bulonería A4-70: R_p0,2 = 450 MPa [ESTIMADO: ISO 3506-1]. A_s M5/M6/M8 = 14,2 / 20,1 / 36,6 mm²
    [ESTIMADO: ISO 898-1].
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "piezas"))

G = 9.81
AS = {5: 14.2, 6: 20.1, 8: 36.6}
SY_A4 = 450.0
SY_6082 = 240.0
SY_6082_HAZ = 115.0
KTS_HOLE = 2.0      # [ESTIMADO: Peterson — eje con agujero transversal en torsión, d/D 0,15–0,2: K_ts ≈ 1,7–2,0 (bruto)]
KTS_GROOVE = 3.0    # [ESTIMADO: Peterson — ranura de anillo de retención en torsión ≈ 2,5–3,0]
KT_GROOVE_AX = 4.0  # [ESTIMADO: ranura de anillo, tracción/flexión ≈ 3–5]
P_KEY_ADM = 100.0   # [ESTIMADO: presión admisible en chaveta con cubo de acero (DIN 6892, carga con choques leves)]
# rizado de par: inputs shaft.torque_ripple_frac (el mismo que sizing.mechanical y structural_bomba)
SPRING_SEAL_N = 150.0  # [ESTIMADO: fuerza de resorte de un MG1 Ø20 + pretensado de la copa]

DK_M8 = 16.0        # [ESTIMADO: ISO 10642 M8, Ø de cabeza real máx. 16,0 (teórico 17,9)]

JUSTIFIED = {
    ("P1-DRV-08", "Chaveta 5×5 del eje del motor Ø15 en el cubo del acople: aplastamiento a T_max"):
        "Hallazgo abierto (auditoría Pass 3 H13): FS < 2 contra p_adm = 100 MPa (DIN 6892, choques leves, el valor "
        "conservador de este archivo). El encastre lo fija el eje del motor (Ø15 × 30, R11) y la luz al centrador; "
        "no se puede alargar. Mitigación: cubo Rotex del lado del motor en ACERO (no Al-D), ajuste sin juego + "
        "Loctite 648 en el asiento además de la chaveta, y medir el chavetero del motor recibido; con cubo y eje de "
        "acero (R_e ≥ 300 [SUPUESTO]) el aplastamiento plástico queda ≥ 2,5 × la presión calculada.",
}


def stud_loads(p):
    """Carga de servicio de cada espárrago M8 del pórtico (F_t tracción, F_s corte) — la usa también
    structural_toma (placa base): vuelco por Fa a la altura del eje + 3 g vertical del tren."""
    import importlib.util
    m, L = p.sz["mech"], p.sz["loads"]
    from _drv_geom import z_axis
    S_mid = (p.drv_S_brgA + p.drv_S_brgB) / 2
    h_ax = z_axis(p, S_mid) - (p.base_top_z + p.drv_bracket_base_t)
    m_rot = p.drv_imp_m_kg + p.drv_shaft_L * 1e-3 * 2.47 + p.drv_coupling["mass_g"] / 2e3 + 0.3
    Fv = 3 * G * m_rot + m["Fr_N"]
    dx = abs(p.brg_bracket_holes[2][0] - p.brg_bracket_holes[0][0])
    Ft = m["Fa_max_N"] * (h_ax + p.drv_bracket_base_t) / dx / 2 + Fv / 4
    Fs = math.hypot(m["Fa_max_N"], m["Fr_N"]) / 4
    return Ft, Fs


def cases(p, A, row, rows, T3, T2):
    sh = p.inp["shaft"]
    m = p.sz["mech"]
    L = p.sz["loads"]
    Sy, Su, Se = sh["sy_mpa"], sh["su_mpa"], sh["se_mpa"]
    tau_y, tau_u, tau_e = 0.577 * Sy, 0.577 * Su, 0.577 * Se
    d = p.shaft_d
    T_max, T_top = m["T_max_Nm"] * 1e3, m["T_top_Nm"] * 1e3          # N·mm
    T_cut = m.get("shear_pin", {}).get("T_cut_Nm", m["T_max_Nm"] * 1.8) * 1e3
    Fa, Fr = m["Fa_max_N"], m["Fr_N"]

    # ------------------------------------------------------------------ P1-DRV-01 eje
    dh = p.drv_pin_hole
    Zp_net = math.pi * d ** 3 / 16 - dh * d ** 2 / 6      # [ESTIMADO: módulo torsional neto con agujero transversal (Peterson)]
    tau = T_cut / Zp_net
    row(rows, "P1-DRV-01", "Agujero del pasador: par de corte del pasador (traba con piedra)",
        f"τ = T_corte/(πd³/16 − d_h·d²/6), T_corte {T_cut/1e3:.1f} N·m, sección neta, K_t = 1 (dúctil, estático)",
        tau, tau_y, A, T2)
    tn = T_top / Zp_net
    T_RIPPLE = sh["torque_ripple_frac"]
    tm, ta = KTS_HOLE * tn, KTS_HOLE * T_RIPPLE * tn
    s_eq = ta * tau_u / tau_e + tm                         # Goodman en corte expresado contra τ_u
    row(rows, "P1-DRV-01", f"Agujero del pasador: fatiga en V máx. (T_top ± {T_RIPPLE:.0%})",
        f"Goodman τ_a/τ_e + τ_m/τ_u, K_ts {KTS_HOLE} (Peterson), S_e corrosión {Se:.0f} MPa; σ_eq = τ_a·τ_u/τ_e + τ_m",
        s_eq, tau_u, A, T2)
    d2 = p.drv_circlip["d2"]
    Zg = math.pi * d2 ** 3 / 16
    Ag = math.pi * d2 ** 2 / 4
    tau_g = T_cut / Zg
    sig_g = Fa / Ag
    row(rows, "P1-DRV-01", "Ranura DIN 471 de empuje: par de corte del pasador + Fa",
        f"von Mises √(σ² + 3τ²), τ = T_corte/(π·{d2:g}³/16), σ = Fa/A_fondo, K_t = 1 (dúctil, estático)",
        math.sqrt(sig_g ** 2 + 3 * tau_g ** 2), Sy, A, T2)
    tg_m, tg_a = KTS_GROOVE * T_top / Zg, KTS_GROOVE * T_RIPPLE * T_top / Zg
    sg_m = KT_GROOVE_AX * Fa / Ag * (L["T_top_N"] / max(L["T_bollard_N"], 1))
    s_m = math.sqrt(sg_m ** 2 + 3 * tg_m ** 2)
    s_a = math.sqrt(3) * tg_a
    row(rows, "P1-DRV-01", "Ranura DIN 471 de empuje: fatiga en V máx.",
        f"Goodman von Mises σ_a/S_e + σ_m/S_u; K_ts {KTS_GROOVE}, K_t ax {KT_GROOVE_AX}; empuje en V máx. ∝ T_top",
        s_a * Su / Se + s_m, Su, A, T2)
    k = p.drv_key
    l_eff = p.drv_cpl_key_l - k["b"]
    pk = 2 * T_max / (d * (k["h"] - k["t1"]) * l_eff)
    row(rows, "P1-DRV-01", "Chaveta 6×6 del acople: aplastamiento a T_max",
        f"p = 2T/(d·(h − t1)·(l − b)), l = {p.drv_cpl_key_l:g} mm, cubo de acero",
        pk, P_KEY_ADM, A, T2)
    # chaveta del lado del MOTOR (auditoría Pass 3 H13): eje del motor Ø mot.shaft_d con chaveta mot_keyd, encastre
    # = solape del eje del motor con el cubo del Rotex (mot.shaft_l − luz a la cara del motor, ≤ l_hub)
    mk, ms = p.mot_keyd, p.mot
    l_eng = min(ms["shaft_l"] - p.mot_flange_gap, p.drv_coupling["l_hub"])
    l_effm = l_eng - mk["b"]
    pkm = 2 * T_max / (ms["shaft_d"] * (mk["h"] - mk["t1"]) * l_effm)
    row(rows, "P1-DRV-08", f"Chaveta {mk['b']:g}×{mk['h']:g} del eje del motor Ø{ms['shaft_d']:g} en el cubo del acople: aplastamiento a T_max",
        f"p = 2T/(d·(h − t1)·(l − b)), encastre l = {l_eng:.1f} mm, T_max {T_max/1e3:.1f} N·m (sizing), cubo de acero",
        pkm, P_KEY_ADM, A, T2)
    tau_km = 16 * T_max / (math.pi * (ms["shaft_d"] - mk["t1"]) ** 3)
    row(rows, "P1-DRV-08", f"Eje del motor Ø{ms['shaft_d']:g} con chavetero: torsión a T_max",
        f"τ = 16T/(π·(d − t1)³) (sección neta conservadora), acero del motor [SUPUESTO: S_y ≥ 300 MPa, no publicado]",
        math.sqrt(3) * tau_km, 300.0, A, T2)
    # rosca M20×1 bajo la KM4 (empuje en reversa ≤ Fa)
    A_m20 = math.pi / 4 * (d - 1.083) ** 2               # [ESTIMADO: d3 ≈ d − 1,083·P]
    row(rows, "P1-DRV-01", "Rosca M20×1 (KM4): Fa en reversa + par T_max",
        "von Mises en el núcleo (d − 1,083·P), σ = Fa/A, τ = 16T/(π d3³)",
        math.sqrt((Fa / A_m20) ** 2 + 3 * (16 * T_max / (math.pi * (d - 1.083) ** 3)) ** 2), Sy, A, T2)

    # ------------------------------------------------------------------ P1-DRV-02 caja del sello
    pd = max(200e3, getattr(p, "pmp_p_design_Pa", 0) or 0, 2 * L["p_pump_max_Pa"]) / 1e6   # MPa
    r_in = p.drv_chamber_d / 2
    t_sp = (p.seal_spigot_d - p.drv_chamber_d) / 2
    row(rows, "P1-DRV-02", f"Presión de diseño {pd:.2f} MPa en la cámara mojada (espigón)",
        "anillo de pared delgada σ = p·r/t (espigón, la sección más delgada)", pd * r_in / t_sp, Sy, A, T2)
    F_ax = pd * math.pi / 4 * p.seal_spigot_d ** 2 + SPRING_SEAL_N
    row(rows, "P1-DRV-02", "Bulones 4 × M6 A4-70 al buje de la toma: presión + resorte del sello",
        f"σ = F/(4·A_s), F = p·π/4·Ø{p.seal_spigot_d:g}² + {SPRING_SEAL_N:.0f} N (sin precarga)",
        F_ax / (4 * AS[6]), SY_A4, A, T2)
    t_fl = p.drv_flange_t
    lev = p.seal_bc / 2 - p.seal_spigot_d / 2
    Mfl = F_ax * lev / (math.pi * p.seal_bc)              # N·mm/mm de circunferencia
    row(rows, "P1-DRV-02", "Brida de 8 mm: flexión entre espigón y bulones",
        "placa anular como viga por unidad de perímetro: σ = 6·F·e/(π·BC·t²)", 6 * Mfl / t_fl ** 2, Sy, A, T2)

    # ------------------------------------------------------------------ P1-DRV-03 soporte (pórtico)
    import importlib.util
    spec = importlib.util.spec_from_file_location("_b3", str(Path(__file__).resolve().parent / "piezas" / "P1-DRV-03_bearing_bracket.py"))
    b3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b3)
    g = b3.geom(p)
    from _drv_geom import z_axis
    S_mid = (p.drv_S_brgA + p.drv_S_brgB) / 2
    h_ax = z_axis(p, S_mid) - (p.base_top_z + p.drv_bracket_base_t)
    m_rot = p.drv_imp_m_kg + p.drv_shaft_L * 1e-3 * 2.47 + p.drv_coupling["mass_g"] / 2e3 + 0.3   # [CALCULADO: impulsor + eje (2,47 kg/m, R11) + ½ acople + rodamientos]
    Fv = 3 * G * m_rot + Fr
    Lb = p.brg_bracket_x1 - p.brg_bracket_x0
    tw = p.drv_bracket_web_t
    Mch = Fa / 2 * h_ax
    row(rows, "P1-DRV-03", "Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa)",
        f"flexión en su plano σ = M/(t·L²/6), M = Fa/2 · {h_ax:.0f} mm, L = {Lb:.0f} mm, ZAT soldada",
        Mch / (tw * Lb ** 2 / 6), SY_6082_HAZ, A, T2)
    span = 2 * p.drv_cheek_y[0]
    Ld = g["xh1"] - g["xh0"]
    Md = Fv * span / 4
    e_d = g["zd0"] + p.drv_deck_t / 2 - z_axis(p, S_mid)
    sig_d = Md / (Ld * p.drv_deck_t ** 2 / 6) + Fa * e_d / (p.drv_deck_t * Ld ** 2 / 6) / 2
    row(rows, "P1-DRV-03", "Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico",
        f"σ = P·L/4/(b t²/6) + Fa·e/(t·b²/6)/2, L = {span:.0f}, b = {Ld:.0f}, e = {e_d:.0f} mm, ZAT",
        sig_d, SY_6082_HAZ, A, T2)
    dx = abs(p.brg_bracket_holes[2][0] - p.brg_bracket_holes[0][0])
    Ft, Fs = stud_loads(p)
    sb = math.sqrt((Ft / AS[8]) ** 2 + 3 * (Fs / AS[8]) ** 2)
    row(rows, "P1-DRV-03", "Espárragos 4 × ISO 10642 M8 A4-70: vuelco por Fa + corte (servicio)",
        f"F_t = Fa·h/Δx/2 + 3g/4, F_s = Fa/4; von Mises sobre A_s (carga de servicio; Δx = {dx:.0f})",
        sb, SY_A4, A, T2)
    F_pre = p.drv_nut_Fpre_N
    F_nut = F_pre + Ft
    row(rows, "P1-DRV-03", f"Espárrago M8 A4-70: precarga ({p.drv_nut_torque_Nm:g} N·m, F_v {F_pre:.0f} N) + F_t",
        "σ = (F_v + F_t)/A_s (conservador: Φ = 1) vs R_p0,2 A4-70",
        F_nut / AS[8], SY_A4, A, T2)
    row(rows, "P1-DRV-03", f"Tuerca ISO 4032 A4 sobre espárrago A4: precarga ({p.drv_nut_torque_Nm:g} N·m) + F_t",
        f"barrido de filetes τ = F/(π·d·m·0,6), m = {p.drv_nut_m:g}, F = T/(K·d) + F_t (K {p.drv_nut_K:g}) vs 0,58·R_p0,2 A4-70",
        F_nut / (math.pi * 8 * p.drv_nut_m * 0.6), 0.58 * SY_A4, A, T2)
    # arandela ancha ISO 7093 sobre la zapata RANURADA (6082 soldado): área del anillo menos la ranura
    import numpy as _np
    ro_w, ri_w, hw_s = p.drv_washer_od / 2, 4.2, p.drv_bracket_hole / 2
    yy = _np.linspace(-ro_w, ro_w, 4001)
    chord = 2 * _np.sqrt(_np.clip(ro_w ** 2 - yy ** 2, 0, None)) - 2 * _np.sqrt(_np.clip(ri_w ** 2 - yy ** 2, 0, None))
    A_w = float(getattr(_np, "trapezoid", getattr(_np, "trapz", None))(_np.where(_np.abs(yy) > hw_s, chord, 0.0), yy))
    row(rows, "P1-DRV-03", "Zapata ranurada: aplastamiento bajo la arandela ISO 7093 (precarga + F_t)",
        f"σ = F/A, A = anillo Ø{p.drv_washer_od:g}/Ø8,4 fuera de la ranura de {p.drv_bracket_hole:g} mm = {A_w:.0f} mm², ZAT",
        F_nut / A_w, SY_6082_HAZ, A, T2)
    # pasadores Ø6 escariados: toman el corte en x (la ranura abierta no lo toma)
    A_dw = math.pi / 4 * p.drv_dowel_d ** 2
    row(rows, "P1-DRV-03", "Pasadores ISO 8735 Ø6 A4 (2 por zapata): corte por Fa (sin contar fricción)",
        "τ = Fa/(4·A), σ_eq = √3·τ vs R_p0,2 A4-70", math.sqrt(3) * Fa / (4 * A_dw), SY_A4, A, T2)
    row(rows, "P1-INT-02", f"Agujero ciego de los pasadores Ø6 ({p.drv_dowel_plate_depth:g} mm) en el 5083: aplastamiento por Fa",
        "σ_b = (Fa/4)/(d·h) vs R_p0,2 5083-H111 125 MPa [ESTIMADO]",
        Fa / 4 / (p.drv_dowel_d * p.drv_dowel_plate_depth), 125.0, A, T2)
    row(rows, "P1-DRV-03", "Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo",
        "corte del resalte τ = Fa/(π·D·t_resalte), σ_eq = √3·τ", math.sqrt(3) * Fa / (math.pi * p.drv_bearing["D"] * p.drv_brg_shoulder_t),
        SY_6082, A, T2)

    # ------------------------------------------------------------------ P1-DRV-06 tapa
    r_b = p.drv_cover_bc / 2
    r_c = (p.drv_bearing["Da_max"] + p.drv_bearing["D"]) / 4
    Mc = Fa * (r_b - r_c) / (2 * math.pi * (r_b + r_c) / 2)
    row(rows, "P1-DRV-06", "Tapa: empuje Fa hacia proa entre el aro exterior y los M5",
        "placa anular por unidad de perímetro σ = 6·Fa·e/(2π r_m t²)", 6 * Mc / p.drv_cover_t ** 2, SY_6082, A, T2)
    row(rows, "P1-DRV-06", "Bulones 4 × M5 A4-70 de la tapa: Fa",
        "σ = Fa/(4·A_s) (sin precarga)", Fa / (4 * AS[5]), SY_A4, A, T2)

    # ------------------------------------------------------------------ P1-MOT-02 soporte del motor
    mo_kg = p.inp["motor"]["options"][p.sz["selection"]["motor"]]["mass_kg"]
    W3 = 3 * G * mo_kg
    e_m = p.motor_l / 2 + p.mot_plate_t / 2
    hw = p.mot_foot_y[1]
    t = p.mot_plate_t
    W_pl = (2 * hw - p.mot_hole_d) * t ** 2 / 6            # sección horizontal por el agujero
    row(rows, "P1-MOT-02", "Placa: 3 g vertical del motor en voladizo (sin cartelas)",
        f"σ = W·e/(b t²/6), W = 3 g × {mo_kg:g} kg, e = {e_m:.0f} mm, b = 2·{hw:.0f} − Ø{p.mot_hole_d:g}",
        W3 * e_m / W_pl, SY_6082_HAZ, A, T2)
    yb = (p.mot_foot_y[0] + p.mot_foot_y[1]) / 2
    F_T = T_max / (2 * yb)
    zf = p.mot_axis_z0 - p.mot_foot_z
    row(rows, "P1-MOT-02", "Placa: par de reacción T_max (en su plano) + 3 g",
        f"corte en la sección por el agujero τ = (T/ (2·y_pie) + W/2)/(b·t) , σ_eq = √3·τ",
        math.sqrt(3) * (F_T + W3 / 2) / ((2 * hw - p.mot_hole_d) * t), SY_6082_HAZ, A, T2)
    mm = p.mot
    nb = mm["mount_n"]
    Fb = T_max / (nb * mm["mount_pcd"] / 2) + W3 / nb
    row(rows, "P1-MOT-02", f"Bulones {nb} × M{mm['mount_bolt']} a la cara del motor: T_max + 3 g (corte)",
        "τ = (T/(n·r) + W/n)/A_s, σ_eq = √3·τ (sin fricción por precarga)",
        math.sqrt(3) * Fb / AS.get(mm["mount_bolt"], 20.1), SY_A4, A, T2)
    Ff = W3 * e_m / (p.mot_foot_l - 27.0) / 2 + F_T
    row(rows, "P1-MOT-02", "Bulones 4 × M8 de los pies al casco: vuelco 3 g + par",
        "F_t = W·e/Δx/2 + T/(2·y_pie) sobre A_s", Ff / AS[8], SY_A4, A, T2)

    # ------------------------------------------------------------------ P1-ELE (PETG)
    esc_kg = p.ele_esc_mass_kg
    L_, W_, H_ = p.ele_esc_size
    F_pad = 2 * L_ * p.ele_pad_w * p.ele_pad_p_mpa
    F_up = 3 * G * (esc_kg + 0.25)
    Fi = max(F_pad, F_up) / 4
    from cadlib import INSERT_HOLE, INSERT_LEN
    tau_i = Fi / (math.pi * INSERT_HOLE[5] * INSERT_LEN[5])
    row(rows, "P1-ELE-01", "Insertos M5 de la capota: apriete de las tiras de EPDM (sostenido)",
        f"arranque τ = F/(π·Ø·L) del inserto, F = máx(EPDM {F_pad:.0f} N, 3 g arriba {F_up:.0f} N)/4; cruza capas (×f_Z)",
        tau_i / A["fz"], "sust", A, T3)
    Lo, Wo = p.ele_out
    w = p.ele_wall
    A_w = 2 * (Lo + Wo) * w
    row(rows, "P1-ELE-01", "Paredes del pedestal: 3 g vertical de ESC + capota (compresión sostenida)",
        "σ = 3 g·m/A_paredes (pandeo despreciable: h/t = 19)", 3 * G * (esc_kg + 0.3) / A_w, "sust", A, T3)
    row(rows, "P1-ELE-01", "Orejas M6 al piso: 2 g lateral (golpe) del conjunto a la altura del CG",
        "vuelco: F_t = m·2g·h_CG/(ancho)/2 sobre el anillo de la oreja (7 mm, cruza capas)",
        (esc_kg + 0.5) * 2 * G * (p.ele_raise + H_ / 2) / (Wo + 16) / 2 / (math.pi * 12.8 * 7.0) / A["fz"],
        "short", A, T3)
    q = p.ele_pad_p_mpa
    b_ = p.ele_pad_w
    # techo de la capota: las tiras cargan a ≤ pad_w de las paredes → voladizo corto desde la pared
    import importlib.util as iu
    sp = iu.spec_from_file_location("_e2", str(Path(__file__).resolve().parent / "piezas" / "P1-ELE-02_esc_hood.py"))
    e2 = iu.module_from_spec(sp)
    sp.loader.exec_module(e2)
    tt = e2.TOP_T
    M_top = q * b_ * (b_ / 2 + p.ele_clr)                  # N·mm/mm
    row(rows, "P1-ELE-02", "Techo de la capota: reacción de las tiras de EPDM (sostenida)",
        "voladizo desde la pared por unidad de largo σ = 6·q·b·(b/2 + c)/t²", 6 * M_top / tt ** 2, "sust", A, T3)
    return {"Fa_N": Fa, "Fr_N": Fr, "T_max_Nm": T_max / 1e3, "T_top_Nm": T_top / 1e3, "T_cut_pin_Nm": T_cut / 1e3,
            "p_design_MPa": pd, "m_rotor_kg": m_rot, "motor_kg": mo_kg, "esc_kg": esc_kg,
            "h_axis_over_base_mm": h_ax}
