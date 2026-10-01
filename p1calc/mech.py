"""Cálculos mecánicos: eje, rodamientos, correa, pasador de corte, retén de basculación,
inercia de la unidad y cargas por caso de carga (sección 4 del PROMPT)."""
from __future__ import annotations

import math

G = 9.81


# ----------------------------------------------------------------------------
# Eje
# ----------------------------------------------------------------------------
def shaft_checks(inp: dict, lay: dict, Q_max: float, Q_pin: float, F_belt_radial: float,
                 T_axial: float, F_side_prop: float, n_max_rpm: float) -> dict:
    """Eje Ø d con muñones Ø d_b (rodamientos) y asiento de hélice Ø min(d, bore).
    Secciones críticas: (1) asiento de la polea entre dos rodamientos (flexión por tiro de
    correa + torsión; Kf por plano de prisionero), (2) asiento de hélice con agujero del
    pasador (torsión al corte del pasador, flexión por fuerza lateral). Velocidad crítica y
    pandeo en el vano más largo."""
    sh = inp["shaft"]
    pr = inp["propeller"]["options"][inp["propeller"]["chosen"]]
    d = sh["d_mm"] / 1000
    d_b = sh["d_bearing_mm"] / 1000
    d_p = min(sh["d_mm"], pr["bore_mm"]) / 1000
    E = sh["E_gpa"] * 1e9
    Sy, Su, Se = sh["sy_mpa"] * 1e6, sh["su_mpa"] * 1e6, sh["se_mpa"] * 1e6
    tau_y = 0.577 * Sy
    Kt_t = 1.6          # [ESTIMADO: Peterson, eje con agujero transversal a/d≈0.2 en torsión]
    Kt_b = 2.1          # [ESTIMADO: idem en flexión]
    Kf_shoulder = sh["kf_shoulder"]
    Se_dry = sh["se_dry_mpa"] * 1e6     # muñón seco (dentro de la placa motriz)

    def Zb(x): return math.pi * x**3 / 32
    def Zt(x): return math.pi * x**3 / 16

    # (1) asiento de la polea conducida (entre rodamientos): M = F·a·b/L, Ø d_b con plano de prisionero
    a_, b_ = lay["pulley_a_mm"] / 1000, lay["pulley_b_mm"] / 1000
    M1 = F_belt_radial * a_ * b_ / (a_ + b_)
    s1 = Kf_shoulder * M1 / Zb(d_b)     # la polea va sobre Ø d_b (pila apretada desde arriba)
    t1 = Q_max / Zt(d_b)
    vm1 = math.sqrt((Kf_shoulder * M1 / Zb(d_b))**2 + 3 * t1**2)
    fs1_static = Sy / vm1
    fs1_fat = 1.0 / (s1 / Se_dry + math.sqrt(3) * t1 / Su)
    # (2) asiento de hélice con pasador
    tau_pin = Kt_t * Q_pin / Zt(d_p)
    fs2_pin = tau_y / tau_pin
    M2 = F_side_prop * lay["prop_overhang_mm"] / 1000
    s2 = Kt_b * M2 / Zb(d_p)
    t2 = Kt_t * Q_max / Zt(d_p)
    fs2_fat = 1.0 / (s2 / Se + math.sqrt(3) * t2 / Su)
    # velocidad crítica (vano simplemente apoyado más largo, eje Ø d)
    I = math.pi * d**4 / 64
    m_lin = sh["density_kg_m3"] * math.pi * d**2 / 4
    Ls = lay["max_span_mm"] / 1000
    n_crit = (math.pi / Ls) ** 2 * math.sqrt(E * I / m_lin) * 60 / (2 * math.pi)
    P_cr = math.pi**2 * E * I / Ls**2
    return {
        "d_mm": sh["d_mm"], "d_bearing_mm": sh["d_bearing_mm"], "d_prop_seat_mm": d_p * 1000,
        "M_pulley_seat_Nm": M1, "sigma_vm_pulley_seat_MPa": vm1 / 1e6,
        "fs_static_pulley_seat": fs1_static, "fs_fatigue_pulley_seat": fs1_fat,
        "tau_at_shear_pin_MPa": tau_pin / 1e6, "fs_torsion_at_shear_pin": fs2_pin,
        "M_prop_seat_Nm": M2, "fs_fatigue_prop_seat": fs2_fat,
        "fs_static": min(fs1_static, fs2_pin), "fs_fatigue_goodman": min(fs1_fat, fs2_fat),
        "max_span_mm": lay["max_span_mm"], "n_crit_rpm": n_crit,
        "n_max_rpm": n_max_rpm, "crit_ratio": n_crit / max(n_max_rpm, 1),
        "P_buckling_N": P_cr, "fs_buckling": P_cr / max(T_axial, 1),
        "mass_kg": m_lin * lay["shaft_length_mm"] / 1000,
    }


# ----------------------------------------------------------------------------
# Rodamientos (par de 6002 inox en la placa motriz, polea en voladizo)
# ----------------------------------------------------------------------------
def bearing_life(inp: dict, lay: dict, F_belt: float, F_a: float, n_rpm: float) -> dict:
    """Polea entre rodamientos: R_A = F·b/L, R_B = F·a/L. El axial lo toma el rodamiento A
    (localizador, en la placa motriz); se evalúa A con su radial + todo el axial."""
    b = inp["bearings"]
    C = b["C_N"] * b["stainless_factor"]
    C0 = b["C0_N"] * b["stainless_factor"]
    a = lay["pulley_a_mm"]
    bb = lay["pulley_b_mm"]
    L = lay["bearing_spacing_mm"]
    RA = F_belt * bb / L
    RB = F_belt * a / L
    Fr, Fa = RA, F_a
    ratio = Fa / C0
    e = 0.22 + 0.2 * min(max(ratio - 0.025, 0), 0.5)   # [ESTIMADO: interpolación ISO 281 simplificada]
    if Fa / max(Fr, 1e-6) > e:
        X, Y = 0.56, max(1.0, 0.44 / e)
    else:
        X, Y = 1.0, 0.0
    P = X * Fr + Y * Fa
    L10 = (C / P) ** 3
    return {"name": b["name"], "C_N": C, "C0_N": C0, "R_A_N": RA, "R_B_N": RB,
            "Fa_N": Fa, "P_N": P, "L10_Mrev": L10,
            "L10_h": L10 * 1e6 / (60 * max(n_rpm, 1)), "static_safety_s0": C0 / max(RA + Fa, 1)}


# ----------------------------------------------------------------------------
# Correa HTD-5M
# ----------------------------------------------------------------------------
def belt_checks(inp: dict, Q_m_max: float, z_m: int, z_s: int, Q_pin: float) -> dict:
    dt = inp["drivetrain"]
    p = dt["belt_pitch_mm"]
    d1 = z_m * p / math.pi
    d2 = z_s * p / math.pi
    Fe = 2 * Q_m_max / (d1 / 1000)
    C = dt["center_distance_mm"]
    L = 2 * C + math.pi * (d1 + d2) / 2 + (d2 - d1) ** 2 / (4 * C)
    # largo comercial: el disponible más cercano (rangos con stock, paso 5 mm); si no hay lista, redondeo
    avail = []
    for lo, hi in dt.get("belt_lengths_available_mm", []):
        avail += list(range(int(lo), int(hi) + 1, 5))
    if avail:
        L_std = float(min(avail, key=lambda x: abs(x - L)))
    else:
        L_std = round(L / p) * p
    teeth = int(round(L_std / p))
    # distancia entre centros real con ese largo (cuadrática en C)
    bq = math.pi * (d1 + d2) / 2 - L_std
    C_act = (-bq + math.sqrt(bq * bq - 8 * (d2 - d1) ** 2 / 4)) / 4
    adj = dt.get("center_adjust_mm", 8.0)
    wrap = math.degrees(math.pi - 2 * math.asin((d2 - d1) / (2 * C)))
    teeth_in_mesh = z_m * wrap / 360
    v_belt = None
    F_radial = 2.5 * Fe          # [ESTIMADO: T1+T2 ≈ 2.5·Fe con pretensión adecuada]
    Fe_pin = 2 * Q_pin / (d2 / 1000)   # tirón si el pasador llega a cortar (tooth-jump antes?)
    return {
        "d1_mm": d1, "d2_mm": d2, "ratio": z_s / z_m, "Fe_N": Fe,
        "Fe_allow_N": dt["belt_allow_tension_n"], "fs_belt": dt["belt_allow_tension_n"] / Fe,
        "length_calc_mm": L, "length_std_mm": L_std, "teeth": teeth,
        "wrap_small_deg": wrap, "teeth_in_mesh": teeth_in_mesh,
        "F_radial_N": F_radial, "Fe_at_shear_pin_N": Fe_pin,
        "pulleys_clear": (d1 + d2) / 2 + 12 < C,
        "center_actual_mm": C_act, "center_shift_mm": C_act - C,
        "length_available": abs(C_act - C) <= adj,
    }


# ----------------------------------------------------------------------------
# Pasador de corte (doble corte a través del eje)
# ----------------------------------------------------------------------------
def shear_pin(inp: dict, Q_target: float) -> dict:
    sp = inp["propeller"]["shear_pin"]
    pr = inp["propeller"]["options"][inp["propeller"]["chosen"]]
    r_s = min(inp["shaft"]["d_mm"], pr["bore_mm"]) / 2 / 1000
    tau = sp["tau_ult_mpa"] * 1e6
    d = math.sqrt(2 * Q_target / (math.pi * tau * r_s))
    # redondeo a medidas comerciales de pasador
    std = [2.0, 2.5, 3.0, 3.18, 3.5, 4.0, 4.76, 5.0]
    d_std = min(std, key=lambda x: abs(x - d * 1000))
    Q_actual = 2 * (math.pi * (d_std / 1000) ** 2 / 4) * tau * r_s
    return {"material": sp["material"], "d_calc_mm": d * 1000, "d_std_mm": d_std,
            "Q_target_Nm": Q_target, "Q_shear_Nm": Q_actual}


# ----------------------------------------------------------------------------
# Retén de basculación (bola con resorte en hoyuelo cónico)
# ----------------------------------------------------------------------------
def detent(inp: dict, M_rel: float, n_plungers: int = 2) -> dict:
    m = inp["mount"]
    R = m["detent_radius_mm"] / 1000
    beta = math.radians(m["detent_notch_flank_deg"])
    rho = math.atan(m["friction_coeff_detent"])
    # fuerza tangencial para sacar la bola: Ft = Fs·tan(β+ρ)
    Ft = M_rel / R
    Fs_total = Ft / math.tan(beta + rho)
    return {"M_release_Nm": M_rel, "radius_mm": R * 1000, "flank_deg": math.degrees(beta),
            "Fs_total_N": Fs_total, "n_plungers": n_plungers,
            "Fs_per_plunger_N": Fs_total / n_plungers}


# ----------------------------------------------------------------------------
# Inercia y CG de la unidad basculante (masas concentradas; refinado post-CAD)
# ----------------------------------------------------------------------------
def unit_inertia(inp: dict, lay: dict, masses: dict) -> dict:
    """masses: {nombre: (m_kg, u_mm, v_mm)} en el marco local; devuelve I_pivot y M_grav."""
    th = lay["theta_rad"]
    I = 0.0
    M_g = 0.0        # momento de gravedad alrededor del pivote (+ = cola abajo / contra el tope)
    m_tot = 0.0
    for name, (m, u, v) in masses.items():
        r2 = (u**2 + v**2) / 1e6
        I += m * r2
        x = (u * math.cos(th) + v * math.sin(th)) / 1000   # brazo horizontal (+ = a popa)
        M_g += m * G * x
        m_tot += m
    return {"I_pivot_kgm2": I, "M_gravity_Nm": M_g, "mass_kg": m_tot}


def impact_force(inp: dict, I_p: float, r_contact_m: float) -> dict:
    """Impulso para acelerar la unidad en rotación al chocar el patín a velocidad v:
    J = I_p·v / r_c² · r_c  →  F_med = J/Δt ; F_pico = k·F_med."""
    m = inp["mount"]
    v = m["impact_speed_m_s"]
    omega = v / r_contact_m
    J = I_p * omega / r_contact_m
    F_avg = J / m["impact_contact_time_s"]
    F_peak = m["impact_peak_factor"] * F_avg
    return {"v_m_s": v, "r_contact_m": r_contact_m, "impulse_Ns": J,
            "F_avg_N": F_avg, "F_peak_N": F_peak}
