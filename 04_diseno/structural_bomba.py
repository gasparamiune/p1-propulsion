"""structural_bomba.py — casos estructurales del grupo BOMBA (P1-PMP-*), llamados por structural.py.

Metales: admisible = S_y (estático) o S_e/K_f (fatiga, amplitud) de p.pmp_mat [ESTIMADO allí];
objetivo FS ≥ T2 (2). Cargas: p.sz["loads"], p.sz["mech"], p.pmp_p_design_Pa (R12 §7.2).
Módulos resistentes de los álabes calculados numéricamente sobre el perfil real (arco + NACA 00xx)
en la raíz (sección del cubo), respecto del eje principal débil (conservador: todo el momento
resultante sobre el eje débil).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "piezas"))

from _pmp_geom import camber_line, naca_half  # noqa: E402

# fusibles mecánicos intencionales (se reportan, no fallan)
JUSTIFIED = {
    ("P1-PMP-05", "Par máx. del controlador (margen contra corte intempestivo)"):
        "Fusible intencional (R12 §7.6): el criterio es T_corte ≥ 1,5·T_máx del ESC y ≤ 0,6·T_fluencia del eje; "
        "FS ≥ 2 no aplica a un fusible.",
    ("P1-PMP-05", "Fatiga a par de crucero (Goodman en corte)"):
        "Fusible intencional: el pasador de Al se reemplaza por mantenimiento (cada temporada o 50 h, y "
        "siempre tras un golpe) [ESTIMADO]; llevar 3 de repuesto.",
}


def section_props(chord, a1, a2, tc, n=120):
    """Área, I_min (eje principal débil) y W_min = I_min / c_max del perfil plano (mm)."""
    cl = camber_line(chord, a1, a2, +1, n=n)
    up, lo = [], []
    for (f, X, T, _, nx, nt) in cl:
        h = naca_half(f, tc) * chord
        up.append((X + nx * h, T + nt * h))
        lo.append((X - nx * h, T - nt * h))
    poly = up + lo[::-1]

    def props(pts):
        A = cx = cy = 0.0
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            c = x0 * y1 - x1 * y0
            A += c
            cx += (x0 + x1) * c
            cy += (y0 + y1) * c
        A /= 2
        return A, cx / (6 * A), cy / (6 * A)

    Ar, cx, cy = props(poly)
    best = None
    for k in range(180):                     # eje neutro a φ (barrido de 1°): I_φ y fibra extrema
        ph = math.radians(k)
        c, s_ = math.cos(ph), math.sin(ph)
        rot = [((x - cx) * c + (y - cy) * s_, -(x - cx) * s_ + (y - cy) * c) for x, y in poly]
        I = 0.0
        for (x0, y0), (x1, y1) in zip(rot, rot[1:] + rot[:1]):
            I += (y0 ** 2 + y0 * y1 + y1 ** 2) * (x0 * y1 - x1 * y0)
        I = abs(I / 12)
        if best is None or I < best[0]:
            best = (I, max(abs(v) for _, v in rot))
    Imin, cmax = best
    return abs(Ar), Imin, Imin / cmax


def cases(p, A, row, rows, T3, T2):
    L, M = p.sz["loads"], p.sz["mech"]
    mat = p.pmp_mat
    Al, SS, Al5 = mat["Al 6061-T6"], mat["AISI 316"], mat["Al 5083"]
    Kf = 1.5                       # concentración en la raíz con radio de acuerdo R ≥ 2 mm [ESTIMADO]
    f_anod = 0.6                   # anodizado duro: baja la resistencia a fatiga del Al [ESTIMADO: 30–50 %]
    alt_blade = 0.30               # amplitud/medio de la carga de álabe (paso de álabes + toma) [ESTIMADO]
    alt_torque = p.inp["shaft"]["torque_ripple_frac"]   # ondulación del par total (eje, pasador) [ESTIMADO, inputs; la misma que sizing]
    used = {}

    rh, rt = p.D_hub / 2, p.D / 2
    span = rt - rh
    r_m = (rh + rt) / 2 / 1000.0
    A_ann = math.pi / 4 * (p.D_bore ** 2 - p.D_hub ** 2) / 1e6
    Fa_rot = max(M["Fa_max_N"], L["p_pump_max_Pa"] * A_ann)       # empuje axial del rotor (N)
    r_bar = 2 / 3 * (rt ** 3 - rh ** 3) / (rt ** 2 - rh ** 2)     # centroide de carga axial uniforme
    hub = p.pmp_imp_table["cubo"]
    Ab, Ib, Wb = section_props(hub["chord"], hub["bb1"], hub["bb2"], hub["tc"])
    used.update(imp_root_W_mm3=Wb, imp_root_I_mm4=Ib, Fa_rotor_N=Fa_rot, imp_span_mm=span)

    def blade(T, label, kind_s, fat=True):
        Ft = T / (p.blades * r_m)
        Fa = Fa_rot / p.blades
        Mt = Ft * span / 2
        Ma = Fa * (r_bar - rh)
        Mr = math.hypot(Mt, Ma)
        s = Mr / Wb
        row(rows, "P1-PMP-03", f"Álabe en la raíz: {label}",
            f"voladizo: F_t=T/(Z·r_m)={Ft:.0f} N a span/2 + F_a={Fa:.0f} N/álabe en r̄; M={Mr/1000:.2f} N·m; "
            f"W_mín perfil cubo={Wb:.0f} mm³ (c={hub['chord']:.1f}, t={hub['tmax']:.2f})", s, SS["Sy"], A, T2)
        if fat:
            row(rows, "P1-PMP-03", f"Álabe en la raíz, fatiga: {label}",
                f"σ_a = {alt_blade:.2f}·σ_m (paso por {p.vanes} álabes del estator, toma); K_f {Kf}; S_e 316",
                alt_blade * s, SS["Se"] / Kf, A, T2)
        return s
    s_d = blade(L["torque_max_Nm"], f"par de diseño {L['torque_max_Nm']:.1f} N·m + empuje", "Sy")
    s_m = blade(M["T_max_Nm"], f"par máx. del controlador {M['T_max_Nm']:.1f} N·m + empuje", "Sy")
    s_c = blade(p.pmp_pin_T_cut, f"par de corte del pasador {p.pmp_pin_T_cut:.1f} N·m (traba repartida)", "Sy",
                fat=False)
    # golpe en la punta de UN álabe con el par de corte (informativo, no es caso de diseño: rejilla)
    F_tip = p.pmp_pin_T_cut / (rt / 1000)
    used["imp_tip_rock_sigma_MPa"] = F_tip * span / Wb
    used["imp_blade_sigma_MPa"] = dict(diseno=s_d, ctrl=s_m, corte=s_c)

    # cubo del impulsor: aplastamiento del pasador sobre el cubo al par de corte
    r_in, r_out = p.shaft_d / 2, p.pmp_land_r
    F_b = p.pmp_pin_T_cut / (2 * (r_in + r_out) / 2 / 1000)
    sb = F_b / (p.pmp_pin_d * (r_out - r_in))
    row(rows, "P1-PMP-03", "Cubo: aplastamiento del pasador al par de corte",
        f"F={F_b:.0f} N por lado sobre {p.pmp_pin_d}×{r_out - r_in:.0f} mm (r medio)", sb, 1.5 * SS["Sy"], A, T2)

    # pasador de corte (fusible)
    Ap = math.pi / 4 * p.pmp_pin_d ** 2
    tau_u = 0.6 * Al["Su"]
    tau_ctrl = M["T_max_Nm"] * 1000 / (p.shaft_d * Ap)
    row(rows, "P1-PMP-05", "Par máx. del controlador (margen contra corte intempestivo)",
        f"corte doble τ=T/(d_eje·A)={tau_ctrl:.1f} MPa; τ_u=0,6·S_u={tau_u:.0f} MPa; T_corte/T_máx="
        f"{p.pmp_pin_T_cut / M['T_max_Nm']:.2f} (criterio R12 ≥ 1,5)", tau_ctrl, tau_u, A, T2)
    tau_m = M["T_top_Nm"] * 1000 / (p.shaft_d * Ap)
    tau_a = alt_torque * tau_m
    Se_s = 0.577 * Al["Se"]
    good = tau_a / Se_s + tau_m / tau_u
    row(rows, "P1-PMP-05", "Fatiga a par de crucero (Goodman en corte)",
        f"τ_m={tau_m:.1f}, τ_a={tau_a:.1f} MPa (T_top {M['T_top_Nm']:.1f} N·m, ±{alt_torque:.0%}); "
        f"S_e,τ=0,577·S_e; índice Goodman {good:.2f}", good, 1.0, A, T2)

    # estator: álabes (reacción del par) + carga radial del buje
    st = p.pmp_st_table["cubo"]
    As_, Is_, Ws = section_props(st["chord"], st["alpha_in"], st["alpha_out"], st["tc"])
    span_s = p.D_bore / 2 - rh
    dp_st = 0.5 * 1013 * p.pump_sections["cubo"]["cu2"] ** 2           # recuperación de presión del giro
    Fa_v = dp_st * A_ann / p.vanes
    Fr_v = M["Fr_N"] / 2                                                # 2 álabes toman la carga radial del buje
    for T, lab in ((L["torque_max_Nm"], "par de diseño"), (M["T_max_Nm"], "par máx. del controlador")):
        Ft = T / (p.vanes * r_m)
        Mv = math.hypot(Ft * span_s / 2, Fa_v * span_s / 2) + Fr_v * span_s
        s = Mv / Ws
        row(rows, "P1-PMP-06", f"Álabe del estator en la raíz: {lab} {T:.1f} N·m",
            f"voladizo (conservador, en realidad empotrado en camisa y cubo): F_t={Ft:.0f} N, F_a={Fa_v:.0f} N, "
            f"F_r buje={Fr_v:.0f} N; W_mín={Ws:.0f} mm³ (c={st['chord']:.1f}, t={st['tmax']:.2f})", s, Al["Sy"], A, T2)
        row(rows, "P1-PMP-06", f"Álabe del estator, fatiga: {lab}",
            f"σ_a={alt_blade:.2f}·σ_m (estelas de {p.blades} álabes); S_e Al anodizado = {f_anod}·S_e; K_f {Kf}",
            alt_blade * s, Al["Se"] * f_anod / Kf, A, T2)
        if lab.startswith("par máx"):
            used["stator_vane_sigma_MPa"] = s
            # comparación con PETG (decisión de material), no es fila
            used["stator_PETG_FS_sust"] = A["sust"] / s
            used["stator_PETG_FS_fat"] = A["fat"] / (alt_blade * s)
            used["stator_PETG_t_needed_mm"] = st["tmax"] * math.sqrt(3 * alt_blade * s / A["fat"])

    # presión interna: carcasa (asiento) y tobera (Ø D_bore) a p_diseño
    pd = p.pmp_p_design_Pa / 1e6
    r_h = p.pmp_D_seat / 2 + p.pmp_h_wall / 2
    row(rows, "P1-PMP-01", f"Presión interna {pd:.2f} MPa (R12 §7.2)", f"aro delgado σ=p·r/t, r={r_h:.1f}, t={p.pmp_h_wall}",
        pd * r_h / p.pmp_h_wall, Al["Sy"], A, T2)
    r_n = p.D_bore / 2 + p.pmp_noz_wall / 2
    row(rows, "P1-PMP-08", f"Presión interna {pd:.2f} MPa (R12 §7.2)", f"aro delgado σ=p·r/t, r={r_n:.1f}, t={p.pmp_noz_wall}",
        pd * r_n / p.pmp_noz_wall, Al["Sy"], A, T2)

    # bulones de bridas (reacción: presión sobre la contracción + bucket + momentos de boquilla/bucket + peso)
    F_p = p.pmp_p_design_Pa * math.pi / 4 * (p.D_bore ** 2 - p.D_noz ** 2) / 1e6
    Fb, Fs = L["F_bucket_N"], L["F_steer_side_N"]
    W_pump = 9.0 * 9.81                      # [ESTIMADO: bomba ≈ 9 kg (manifest PMP)]
    As_M6 = 20.1                             # área resistente M6 [ESTIMADO: ISO 898 tabla]
    A4 = mat["A4-70"]["Sy"]
    for pid, lab, X0, bc in (("P1-PMP-01", "Bulones brida toma (8×M6)", p.X_duct_out, p.pump_flange_bc),
                             ("P1-PMP-08", "Bulones brida carcasa–tobera (8×M6)", p.X_st1, p.pmp_f2_bc)):
        Mm = Fs * (p.X_steer_pivot - X0) / 1000 + Fb * p.Z_bucket_pivot / 1000 + W_pump * 0.15
        n = p.pmp_f2_n
        Fbolt = (F_p + Fb) / n + Mm * 1000 * 2 / (n * bc / 2)
        row(rows, pid, f"{lab}: presión + bucket + momentos",
            f"F_ax={F_p + Fb:.0f} N, M={Mm:.1f} N·m (boquilla {Fs:.0f} N, bucket {Fb:.0f} N, peso) → "
            f"F_bulón={Fbolt:.0f} N sobre A_s={As_M6} mm² (sin precarga)", Fbolt / As_M6, A4, A, T2)
        used[f"{pid}_bolt_N"] = Fbolt

    # anti-rotación del estator: 2 × M5 al corte con el par máx.
    Fsc = M["T_max_Nm"] / (2 * p.pmp_D_seat / 2 / 1000)
    row(rows, "P1-PMP-01", "Tornillos anti-rotación del estator (2×M5) al corte",
        f"F={Fsc:.0f} N por tornillo (T_max {M['T_max_Nm']:.1f} N·m, r={p.pmp_D_seat/2:.1f})", Fsc / 14.2,
        0.577 * A4, A, T2)

    # orejas de pivote (en la placa de espejo, Al 5083): un solo lado toma toda la carga (conservador)
    d, t, w = p.pmp_lug_hole, p.pmp_lug_t, p.pmp_lug_w
    e = w / 2                                # distancia del centro del agujero al borde (extremo redondeado)
    lever = p.X_steer_pivot - p.pmp_land_X1 + 5.0
    S_pom = 25.0                             # POM-C: presión admisible estática en buje [ESTIMADO: catálogos POM-C, verificar]
    for F, lab in ((Fs, f"F lateral de la boquilla {Fs:.0f} N"), (Fb, f"F del bucket {Fb:.0f} N")):
        row(rows, "P1-PMP-09", f"Oreja: aplastamiento del alojamiento del buje — {lab}", f"σ_b=F/(d·t), d={d}, t={t:.1f}",
            F / (d * t), 1.5 * Al5["Sy"], A, T2)
        row(rows, "P1-PMP-09", f"Oreja: sección neta y desgarro — {lab}",
            f"máx(F/((w−d)·t), F/(2·(e−d/2)·t)·√3), w={w}, e={e}", max(F / ((w - d) * t), math.sqrt(3) * F / (2 * (e - d / 2) * t)),
            Al5["Sy"], A, T2)
        row(rows, "P1-PMP-09", f"Oreja: flexión en el arranque — {lab}",
            f"M=F·{lever:.1f} mm, W=w·t²/6 (eje débil)", F * lever / (w * t ** 2 / 6), Al5["Sy"], A, T2)
        row(rows, "P1-PMP-09", f"Oreja: fatiga — {lab}",
            f"σ_a = σ flexión (maniobras, ~1e5–1e6 ciclos); S_e 5083; K_f {Kf}",
            F * lever / (w * t ** 2 / 6), Al5["Se"] / Kf, A, T2)
        row(rows, "P1-PMP-11", f"Buje de pivote POM: presión — {lab}",
            f"p=F/(d·L), d={p.steer_pin_d}, L={p.pmp_lug_bush_L:.1f} (un solo buje)", F / (p.steer_pin_d * p.pmp_lug_bush_L),
            S_pom, A, T2)
    # bulones de la placa al espejo: fuerza del bucket con brazo hasta el espejo
    arm = (p.X_steer_pivot - p.X_noz1) / 1000 + 0.010
    nb = len(p.pmp_tp_bolt_ang)
    Fbt = Fb / nb + Fb * arm * 1000 * 2 / (nb * p.pmp_tp_bc_R)
    row(rows, "P1-PMP-09", f"Bulones placa–espejo ({nb}×M6): F del bucket {Fb:.0f} N + momento",
        f"brazo {arm*1000:.0f} mm al espejo; F_bulón={Fbt:.0f} N sobre A_s={As_M6} mm²", Fbt / As_M6, A4, A, T2)

    # placa de espejo: el cuello toma la carga lateral si la tobera se apoya (O-ring a tope)
    Mc = Fs * (p.pmp_collar_X1 - p.X_noz1) / 1000
    Wc = math.pi * (p.pmp_collar_R ** 4 - p.pmp_tp_bore_R ** 4) / (4 * p.pmp_collar_R)
    row(rows, "P1-PMP-09", "Cuello: F lateral de la boquilla con el O-ring a tope",
        f"voladizo del cuello M=F·L={Mc:.1f} N·m, W anillo={Wc:.0f} mm³", Mc * 1000 / Wc, Al5["Sy"], A, T2)
    used["loads_used"] = dict(T_design=L["torque_max_Nm"], T_ctrl=M["T_max_Nm"], T_cut=p.pmp_pin_T_cut,
                              p_design_Pa=p.pmp_p_design_Pa, F_steer=Fs, F_bucket=Fb, Fa_rotor=Fa_rot)
    return used
