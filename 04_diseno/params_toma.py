"""params_toma.py — parámetros del grupo TOMA (P1-INT-*, P1-REF-*).

Geometría de la toma enrasada (marco BOTE salvo indicación):
  • Techo (rampa) en el plano de crujía: curva C2 (curvatura continua) definida por el ángulo
    θ(u), u = x_tan − x (distancia hacia popa desde la tangencia):
      θ = θm·S(u/L1)                        (arranque tangente al fondo, curvatura 0 → máx → 0)
      θ = θm                                (tramo de rampa)
      θ = θm + (−α − θm)·S((u−L1−Lp)/L2)     (giro hasta quedar paralelo al eje en la brida)
    con S(s) = 3s² − 2s³ (θ' continua ⇒ curvatura continua, R10a §4 "polinomio sin saltos").
    Se resuelven L1 y Lp para que el techo termine EXACTAMENTE en lo alto de la sección circular de
    salida (Ø toma_D_out, plano X_duct_out del marco JET) con pendiente paralela al eje.
  • Sección de salida Ø toma_D_out = D_bore: la brida de P1-PMP-01 tiene labio Ø D_bore y su O-ring
    de cara en r = pmp_gl_r_in (71,7 mm). Con Ø D_throat (146,5) en la brida, el O-ring de la bomba
    quedaría medio sobre el agujero y habría un escalón de 6,6 mm delante del anillo de desgaste.
    El conducto converge suavemente hasta Ø D_bore dentro del codo (ver checks: dónde el área de la
    sección es la de la garganta Ø D_throat).
  • Piso (cara superior del labio): Hermite cúbica desde lo alto de la nariz del labio (radio r_lip,
    punta en x_lip) hasta lo bajo de la sección de salida, paralela al eje.
  • Secciones transversales (planos ⟂ al eje, marco JET): rectángulo con esquinas redondeadas que
    pasa a círculo con λ(X) = S(...) entre la nariz del labio y la brida.
"""
from __future__ import annotations

import math

import numpy as np


def _S(s):
    s = np.clip(s, 0.0, 1.0)
    return 3 * s * s - 2 * s ** 3


def _roof(th_m, L1, Lp, L2, alpha, n=3000):
    """Perfil del techo: devuelve (u, z) desde la tangencia."""
    tot = L1 + Lp + L2
    u = np.linspace(0.0, tot, n)
    th = np.where(u < L1, th_m * _S(u / L1),
                  np.where(u < L1 + Lp, th_m, th_m + (-alpha - th_m) * _S((u - L1 - Lp) / max(L2, 1e-9))))
    tz = np.tan(np.radians(th))
    z = np.concatenate([[0.0], np.cumsum(0.5 * (tz[1:] + tz[:-1]) * np.diff(u))])
    return u, z, th


def extend(d):
    a = math.radians(d["alpha"])
    ca, sa = math.cos(a), math.sin(a)
    x_if, z_if = d["x_if"], d["z_if"]

    def j2b(X, Z):        # JET (X, Z) en crujía → BOTE (x, z)
        return (x_if - X * ca - Z * sa, z_if - X * sa + Z * ca)

    def b2j(x, z):        # BOTE → JET
        dx, dz = x - x_if, z - z_if
        return (-(dx * ca + dz * sa), -dx * sa + dz * ca)

    d["toma_j2b"], d["toma_b2j"] = j2b, b2j

    # ------------------------------------------------------------------ materiales y espesores
    d["toma_t"] = 5.0                 # pared del conducto Al 5083 soldado [CALCULADO: structural_toma (FS ≥ 2 a fatiga de soldadura con 5 mm)]
    d["toma_D_out"] = d["D_bore"]     # Ø de salida = labio de P1-PMP-01 [CALCULADO: ver docstring]
    d["toma_R_out"] = d["toma_D_out"] / 2
    d["toma_f_t"] = 12.0              # brida toma ↔ bomba [ESTIMADO: igual a pmp_f1_t; rigidez para 8 × M6]
    d["toma_base_t"] = d["base_top_z"]   # placa base de 0 (enrasada) a base_top_z = 10 mm [CALCULADO: interfaz]
    d["toma_rim_z0"] = d["bottom_t"] + 0.5   # el ala de la placa apoya sobre el casco con 0,5 mm de Sikaflex [ESTIMADO: R05 S36 291i, junta 0,5–1 mm]
    d["toma_seal_gap"] = 0.5          # luz lateral placa ↔ recorte del casco y bloque del labio ↔ placa (sellador) [SUPUESTO]

    d["toma_cyl_L"] = 20.0            # tramo circular antes de la brida: deja lugar a las tuercas M6 de la brida de la bomba [CALCULADO: checks]
    d["toma_X_circ"] = d["X_duct_out"] - d["toma_cyl_L"]

    # ------------------------------------------------------------------ techo (rampa)
    th_m = d["ramp"]                  # [ESTIMADO: research/R10a §4 — 27°]
    L2 = 84.0                         # giro final rampa → eje [CALCULADO: el menor que deja R_mín ≥ 100 mm (R10a usa R120) y el techo libre de la caja del sello en S_seal]
    XE, ZE = d["toma_X_circ"], d["toma_R_out"]
    xE, zE = j2b(XE, ZE)              # lo alto de la sección de salida
    U = d["x_tan"] - xE

    def zend(L1):
        _, z, _ = _roof(th_m, L1, U - L1 - L2, L2, d["alpha"])
        return z[-1]
    lo, hi = 5.0, U - L2 - 1.0
    if zend(lo) < zE:
        raise ValueError("params_toma: con ramp = %.1f° el techo no llega a la brida; subir ramp" % th_m)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if zend(mid) > zE:
            lo = mid
        else:
            hi = mid
    L1 = 0.5 * (lo + hi)
    Lp = U - L1 - L2
    u, z, th = _roof(th_m, L1, Lp, L2, d["alpha"])
    xr = d["x_tan"] - u
    d["toma_roof_L"] = (round(L1, 1), round(Lp, 1), L2)   # [CALCULADO]
    d["toma_ramp_max"] = float(th.max())                    # [CALCULADO]
    xs, zs = xr[::-1].copy(), z[::-1].copy()                # x creciente

    def roof_z(x):
        x = np.asarray(x, dtype=float)
        return np.where(x >= d["x_tan"], 0.0, np.interp(x, xs, zs))
    d["toma_roof_z"] = roof_z
    # radio de curvatura mínimo del techo
    dth = np.gradient(np.radians(th), u)
    d["toma_roof_Rmin"] = float(1.0 / np.max(np.abs(dth) * np.cos(np.radians(th)) + 1e-12))   # [CALCULADO]
    # techo en el marco JET: Z_t(X)
    XJ, ZJ = b2j(xr, z)
    order = np.argsort(XJ)
    XJs, ZJs = XJ[order], ZJ[order]

    def roof_Z(X):
        return np.interp(X, XJs, ZJs)
    d["toma_roof_Z"] = roof_Z
    d["toma_X_tan"] = float(b2j(d["x_tan"], 0.0)[0])

    # cruce del techo con el eje (salida del eje del conducto) y estación mínima del sello
    zax = z_if + (xr - x_if) * math.tan(a)
    i = int(np.argmin(np.abs(z - zax)))
    d["toma_x_cross"] = float(xr[i])
    d["toma_S_cross"] = float((xr[i] - x_if) / ca)                               # [CALCULADO]
    # x desde el cual el techo (cara exterior) libra un cuerpo coaxial de radio r_clear
    d["toma_seal_r_clear"] = 35.0 + 2.0   # brida Ø70 de la caja del sello (TREN) + 2 mm [SUPUESTO: drv_flange_od = 70]

    def S_min(r_clear):
        tz = d["toma_t"] / np.cos(np.radians(th))
        ok = (z + tz) <= zax - r_clear / ca
        # el techo baja hacia proa: primer x (desde popa) a partir del cual todo cumple
        xs_ok = xr[ok]
        return float((xs_ok.min() - x_if) / ca) if len(xs_ok) else 1e9
    d["toma_S_min_fn"] = S_min
    d["toma_S_seal_min"] = S_min(d["toma_seal_r_clear"])                          # [CALCULADO]

    # ------------------------------------------------------------------ labio y piso
    d["toma_x_n"] = d["x_lip"] - d["r_lip"]          # centro de la nariz del labio
    d["toma_lip_top"] = 2 * d["r_lip"]
    xF, zF = j2b(XE, -ZE)                              # lo bajo de la sección de salida
    x0, z0 = d["toma_x_n"], d["toma_lip_top"]
    dx = xF - x0
    m0, m1 = 0.0, math.tan(a) * dx                      # dz/dt (t ∈ [0,1])

    def floor_z(x):
        t = np.clip((np.asarray(x, dtype=float) - x0) / dx, 0.0, 1.0)
        h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
        return h00 * z0 + h10 * m0 + h01 * zF + h11 * m1
    d["toma_floor_z"] = floor_z
    xf = np.linspace(x0, xF, 400)
    XF, ZF = b2j(xf, floor_z(xf))
    o = np.argsort(XF)
    XFs, ZFs = XF[o], ZF[o]
    d["toma_floor_Z"] = lambda X: np.interp(X, XFs, ZFs)
    d["toma_X_nose"] = float(b2j(x0, d["r_lip"])[0])     # estación (JET) de la nariz
    d["toma_X_floor0"] = float(XFs[0])                   # estación (JET) donde arranca el piso
    d["toma_lb_len"] = 45.0           # bloque macizo del labio a popa de la nariz [ESTIMADO: apoyo de la nariz + pasos de la rejilla]
    d["toma_x_lb_aft"] = d["toma_x_n"] - d["toma_lb_len"]

    # ------------------------------------------------------------------ sección transversal
    d["toma_r_top"] = 3.0             # esquinas techo–costado en la abertura (chapa soldada; crecen hasta el círculo en el codo) [SUPUESTO]
    d["toma_r_bot"] = 3.0             # esquinas piso–costado junto al labio [SUPUESTO]

    # ------------------------------------------------------------------ unión placa ↔ conducto
    xx = np.linspace(d["x_lip"], d["x_tan"], 4000)
    zz = roof_z(xx)
    d["toma_x_j"] = float(xx[np.argmin(np.abs(zz - (d["base_top_z"] - 1.0)))])   # techo a 1 mm bajo la cara de la placa: fin de la cuña mecanizada
    d["toma_ffw"] = 25.0              # barra delantera de la brida del conducto (x) [SUPUESTO]
    d["toma_ff_t"] = 10.0             # espesor de la barra delantera (rigidez para el cordón) [CALCULADO: structural_toma]
    d["toma_bf_t"] = 8.0              # brida inferior (lados) [ESTIMADO]
    d["toma_bf_y"] = 99.0             # semiancho de la brida: libra las zapatas del soporte (|y| ≥ brg_bracket_y − 24,2 = 100)
    d["toma_bf_aft"] = 26.0           # tira de popa de la brida, a popa del bloque del labio
    d["toma_bolt_y"] = 94.0           # bulones M6 brida ↔ placa
    d["toma_groove_y"] = 86.5         # eje del cordón NBR en la cara inferior de la brida
    d["toma_cord_d"] = d["oring_cs"]  # cordón NBR Ø3,53 (inputs geometry.oring_cs_mm)
    d["toma_gl_depth"] = round(d["oring_cs"] * (1 - d["oring_sq"]), 2)
    d["toma_gl_width"] = round(math.pi * d["oring_cs"] ** 2 / 4 / (d["oring_fill"] * d["toma_gl_depth"]), 2)

    # ------------------------------------------------------------------ placa base
    d["toma_plate_x0"] = d["toma_x_lb_aft"] - d["toma_bf_aft"] - 14.0
    d["toma_plate_x1"] = d["x_tan"] + 35.0
    d["toma_plate_y"] = 150.0         # semiancho del cuerpo enrasado (cubre las zapatas en |y| ≤ 148) [CALCULADO]
    d["toma_rim_w"] = 25.0            # ala sobre el casco alrededor del recorte [ESTIMADO: 2,5 d del bulón + borde]
    d["toma_plate_r"] = 20.0          # radio de esquinas en planta [SUPUESTO: fresa Ø40]
    d["toma_hull_bolt"] = 6           # M6 ISO 10642 A4-70 (avellanado por fuera) + tuerca autofrenante A4 por dentro
    d["toma_hull_pitch"] = 70.0       # paso máx. entre bulones del ala [ESTIMADO: ≤ 12–15 t de la placa para estanqueidad con sellador]

    # ------------------------------------------------------------------ rejilla
    d["grille_bars"] = 7              # [CALCULADO: R12 §4.3 — luz 15–20 mm; con 7 × 4 mm en W_open = 158,4 → 16,3 mm (con 8 daba 14,0)]
    d["toma_bar_h"] = 21.0            # alto de la pletina 316 [CALCULADO: structural_toma, rejilla tapada a la presión de cierre]
    d["toma_bar_clr"] = 2.0           # luz barra ↔ techo
    n, b = d["grille_bars"], d["grille_bar_d"]
    d["toma_bar_gap"] = (d["W_open"] - n * b) / (n + 1)
    d["toma_bar_y"] = [-d["W_open"] / 2 + d["toma_bar_gap"] * (i + 1) + b * (i + 0.5) for i in range(n)]
    # tirante delantero: donde el techo está a 8 mm (por delante, el pasaje mide < 8 mm < luz)
    d["toma_x_bf"] = float(xx[np.argmin(np.abs(zz - 8.0))])
    d["toma_tie_w"] = 12.0            # pletina transversal 316 3 × 12 [ESTIMADO]
    d["toma_strap_t"] = 3.0
    d["toma_strap_x"] = (d["toma_x_n"] - 32.0, d["toma_x_n"] - 6.0)   # pletina de popa bajo el bloque del labio

    # ------------------------------------------------------------------ buje del sello (interfaz TREN)
    d["tom_seal_bolt_ang0"] = 45.0    # 4 × M6 a 45° (±Y, ±Z libres) — la lee P1-DRV-02
    d["toma_boss_L"] = 22.0           # largo del buje Ø seal_boss_od [ESTIMADO: 2 d de rosca M6 + chaflán]
    d["toma_tube_od"] = 44.0          # tubo mojado alrededor del eje entre el techo y el buje [ESTIMADO]
    d["toma_tube_id"] = 34.0          # pasaje del eje Ø20 (+ anillo DIN 471 Ø27 libre) [CALCULADO]
    d["toma_cbore_L"] = 8.0           # alojamiento Ø seal_spigot_d H8 (espigón de 6 mm de TREN + 2)

    # ------------------------------------------------------------------ chimenea de inspección
    draft = d["sz"]["hydrostatics"]["draft_m"] * 1000.0
    d["toma_draft"] = draft
    d["toma_chim_top"] = math.ceil((draft + 60.0) / 5.0) * 5.0   # tapa ≥ 60 mm sobre la flotación estática [CALCULADO: sizing draft + 60; R10a §0.3]
    d["toma_chim_id"] = 100.0         # entra una mano [ESTIMADO]
    d["toma_chim_x"] = 360.0          # entre las tuercas de la brida de la bomba y el tubo del eje [CALCULADO: checks]
    d["toma_chim_fl_od"] = 160.0
    d["toma_chim_fl_t"] = 10.0
    d["toma_chim_bc"] = 140.0         # 4 × M6 roscados en la brida
    d["toma_cover_t"] = 13.0          # tapa PETG [CALCULADO: structural_toma]

    # ------------------------------------------------------------------ cargas (structural_toma)
    d["toma_p_slam_Pa"] = 50.0e3      # [ESTIMADO: ISO 12215-5 (presión de fondo de planeo, categoría C/D) con m = 200 kg, L_WL 1,75 m, B 0,6 m, 30 km/h, β = 8° → ~45–55 kPa; fórmula no verificada en esta sesión — buscar: "ISO 12215-5 bottom pressure planing P_BMP"]
    d["toma_p_ram_Pa"] = 0.5 * d["inp"]["water"]["density_kg_m3"] * (30 / 3.6) ** 2 * d["inp"]["waterjet"]["intake_eta"]   # [CALCULADO: recuperación de presión dinámica a 30 km/h]
