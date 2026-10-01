#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
croquis_toma_waterjet.py — Toma (succión) del waterjet de Jorge: plano 2026-09-26 vs toma corregida.

Qué hace (todo en un solo script, ejecutable y reproducible):
  1. Convierte a mm las posiciones leídas en píxeles sobre
     referencias/2026-09-26_plano_preliminar_waterjet_jorge.png (dos escalas,
     porque el dibujo no es coherente con sus propias cotas).
  2. Calcula el calado estático de 150 kg en un casco 2,30 × 0,80 m.
  3. Genera la geometría PARAMETRIZADA de una toma enrasada ("flush intake") con
     rampa: techo arco-recta-arco, labio redondeado, pared inferior, rejilla de
     barras longitudinales, eje inclinado, sello/cojinetes en seco y motor.
  4. Puntos de operación del jet (modelo de cantidad de movimiento + energía de
     Bulten 2006, ec. 2.56) → caudal, IVR, empuje.
  5. Chequeo de cavitación a 4500 rpm: NPSH disponible (Bulten ec. 2.64) contra
     NPSH requerido por velocidad específica de succión (Bulten ec. 2.29).
  6. Dibuja referencias/croquis_toma_waterjet.svg: (a) plano de Jorge, (b) corregido.

Uso:   python referencias/croquis_toma_waterjet.py [--out ruta.svg] [--json ruta.json]
No escribe nada fuera de --out / --json. Lee (solo lectura) inputs.yaml del repo
para ρ, p_atm y p_v del agua del Als Fjord; si no lo encuentra usa los mismos valores.

Convenciones: geometría en mm. xf = distancia hacia PROA medida desde la cara
exterior del espejo (xf = 0 en el espejo). y = altura sobre la cara exterior del
fondo (y = 0). En el dibujo la proa queda a la izquierda (X = −xf), como en el plano.
IVR (ITTC) = V_garganta / V_barco; IVR_Bulten = 1/IVR (Bulten 2006 usa la recíproca).
Etiquetas: [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO].
Fuentes: research/R10a_toma_waterjet.md §Fuentes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon, Rectangle, FancyArrowPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
G = 9.81

# =============================================================================
# 1. Medidas leídas en el PNG (px de la imagen original 1320×1023)
#    Método: recorte ampliado con grilla + barrido de columnas/filas oscuras.
# =============================================================================
PX = {
    "dim2300_ext": (126.5, 849.0),   # líneas de referencia de la cota 2300 (proa → punta de la boquilla)
    "chain_ticks": (121.0, 355.0, 573.0, 752.0),  # cotas 850 / 750 / 700 (terminan en la rejilla)
    "y_bottom": 219.5,       # cara exterior del fondo (línea inferior de las cotas 280 y 420)
    "y_dim280_top": 139.0,   # extremo superior de la cota 280 (popa)
    "y_dim420_top": 110.0,   # extremo superior de la cota 420 (popa)
    "x_transom": 790.0,      # cara exterior del espejo (doble línea 779–796 px)
    "x_grille_fwd": 727.0,   # barras de la rejilla, extremo hacia proa
    "x_grille_aft": 765.0,   # barras de la rejilla, extremo hacia popa
    "y_grille": (207.0, 216.0),  # la rejilla está dibujada DENTRO de un rebaje, sobre la línea del fondo
    "x_housing": (677.0, 721.0),  # cilindro de la bomba (impulsor + estator, tramo "120" del detalle)
    "y_housing": (141.0, 182.0),
    "x_motor": (537.0, 637.0),
    "y_motor": (122.0, 182.0),
    "y_floor": 199.0,        # piso interior dibujado
}


def drawing_scales():
    """Escalas mm/px que implican las propias cotas del plano (no coinciden entre sí)."""
    a, b = PX["dim2300_ext"]
    t = PX["chain_ticks"]
    sx_total = 2300.0 / (b - a)                      # [CALCULADO] cota 2300
    sx_chain = 2300.0 / (t[-1] - t[0])               # [CALCULADO] cadena 850+750+700
    sx_parts = [850 / (t[1] - t[0]), 750 / (t[2] - t[1]), 700 / (t[3] - t[2])]
    sy_280 = 280.0 / (PX["y_bottom"] - PX["y_dim280_top"])
    sy_420 = 420.0 / (PX["y_bottom"] - PX["y_dim420_top"])
    return dict(sx=(sx_total, sx_chain), sx_parts=sx_parts, sy=(sy_280, sy_420))


def jorge_layout():
    """Posiciones del plano de Jorge en mm (rango con las dos escalas)."""
    s = drawing_scales()
    sx_lo, sx_hi = sorted(s["sx"])
    sy_lo, sy_hi = sorted(s["sy"])
    xt = PX["x_transom"]
    yb = PX["y_bottom"]

    def fx(px):  # distancia a proa desde el espejo
        return ((xt - px) * sx_lo, (xt - px) * sx_hi)

    def fy(py):
        return ((yb - py) * sy_lo, (yb - py) * sy_hi)

    hy = 0.5 * (PX["y_housing"][0] + PX["y_housing"][1])
    my = 0.5 * (PX["y_motor"][0] + PX["y_motor"][1])
    out = {
        "grille_fwd_from_transom": fx(PX["x_grille_fwd"]),
        "grille_aft_from_transom": fx(PX["x_grille_aft"]),
        "grille_len_side_view": ((PX["x_grille_aft"] - PX["x_grille_fwd"]) * sx_lo,
                                 (PX["x_grille_aft"] - PX["x_grille_fwd"]) * sx_hi),
        "impeller_face_from_transom": fx(PX["x_housing"][0]),
        "housing_aft_from_transom": fx(PX["x_housing"][1]),
        "grille_center_aft_of_impeller": tuple(
            (0.5 * (PX["x_grille_fwd"] + PX["x_grille_aft"]) - PX["x_housing"][0]) * k for k in (sx_lo, sx_hi)),
        "shaft_height_pump": fy(hy),
        "motor_axis_height": fy(my),
        "motor_from_transom": (fx(PX["x_motor"][1])[0], fx(PX["x_motor"][0])[1]),
        "grille_above_bottom": (fy(PX["y_grille"][1])[0], fy(PX["y_grille"][0])[1]),
        "floor_height": fy(PX["y_floor"]),
    }
    # valores para el dibujo (escala media) — el motor del lateral no coincide con el "180" del detalle
    sxm, sym = 0.5 * (sx_lo + sx_hi), 0.5 * (sy_lo + sy_hi)
    out["_mid"] = {
        "motor_x": ((xt - PX["x_motor"][1]) * sxm, (xt - PX["x_motor"][0]) * sxm),
        "motor_diam": (PX["y_motor"][1] - PX["y_motor"][0]) * sym,
        "motor_axis": (yb - my) * sym,
        "shaft": (yb - hy) * sym,
        "imp_face": (xt - PX["x_housing"][0]) * sxm,
        "grille": ((xt - PX["x_grille_aft"]) * sxm, (xt - PX["x_grille_fwd"]) * sxm),
    }
    return out


# =============================================================================
# 2. Parámetros (todo lo que define la toma corregida; cambiar acá)
# =============================================================================
def load_water():
    """ρ, p_atm, p_v del agua del Als Fjord desde inputs.yaml (solo lectura)."""
    w = {"rho": 1013.0, "p_atm": 101325.0, "p_v": 2984.0, "src": "valores por defecto (= inputs.yaml)"}
    try:
        import yaml  # noqa: WPS433

        with open(os.path.join(REPO, "inputs.yaml"), encoding="utf-8") as fh:
            d = yaml.safe_load(fh)["water"]
        w.update(rho=float(d["density_kg_m3"]), p_atm=float(d["p_atm_pa"]),
                 p_v=float(d["vapor_pressure_pa"]), src="inputs.yaml")
    except Exception:  # noqa: BLE001
        pass
    return w


P = {
    # --- del plano de Jorge -------------------------------------------------
    "D_imp": 108.0,        # [VERIFICADO: plano Jorge, "IMPULSOR Ø108 mm (4 ÁLABES)"]
    "D_throat": 120.0,     # [VERIFICADO: plano Jorge, "TOMA (garganta) 120 mm (aprox.)"]
    "D_nozzle": 72.0,      # [VERIFICADO: plano Jorge, "TOBERA Ø salida 72 mm"]
    "d_shaft": 20.0,       # [VERIFICADO: plano Jorge, "EJE Ø20 mm (RECTO)"]
    "rpm": 4500.0,         # [VERIFICADO: plano Jorge, "RÉGIMEN MOTOR 4500 rpm"] (acople directo)
    "P_elec_design": 5000.0,  # [VERIFICADO: plano Jorge, "POTENCIA ELÉCTRICA (DISEÑO) 5 kW"]
    "P_elec_max": 7200.0,     # [VERIFICADO: plano Jorge, "POTENCIA ELÉCTRICA MÁX. 7.2 kW"]
    "mass": 150.0,         # [VERIFICADO: plano Jorge, "MASA TOTAL (emb. + piloto + baterías) 150 kg"]
    "LOA": 2300.0,         # [VERIFICADO: plano Jorge, cota 2300]
    "B_max": 800.0,        # [VERIFICADO: plano Jorge, cota 800]
    "pump_stack_aft_of_impeller": 220.0,  # [CALCULADO: detalle, tramos 120 (impulsor+estator) + 100 (tobera)]
    "steer_len": 120.0,    # [VERIFICADO: plano Jorge, último tramo "120" (boquilla)]
    "bearing_housing_len": 80.0,  # [VERIFICADO: plano Jorge, tramo "80" (cojinetes 8 + sello 9)]
    "motor_len": 180.0,    # [VERIFICADO: plano Jorge, tramo "180" (motor 7)]
    "motor_diam": 170.0,   # [ESTIMADO: medido en el detalle con la cota 108 como escala, ±15 %]
    "grille_jorge": (90.0, 120.0),  # largo × ancho [VERIFICADO: plano, "120 x 90 mm (aprox.)" + "ANCHO 120"]
    # --- casco (calado estático) ---------------------------------------------
    "L_wl": 2000.0,        # [ESTIMADO: 2300 menos ~0,3 m de proa lanzada del lateral; rango 1900–2300]
    "B_wl": 750.0,         # [ESTIMADO: manga máx 800 menos abanico de costados; rango 650–800]
    "Cb": 0.72,            # [ESTIMADO: igual que inputs.yaml (caja con proa lanzada), rango 0.65–0.80]
    "L_wl_range": (1900.0, 2300.0),
    "B_wl_range": (650.0, 800.0),
    "Cb_range": (0.65, 0.80),
    # --- toma corregida ------------------------------------------------------
    "theta_ramp_deg": 27.0,   # [ESTIMADO: 25° (Sci Rep 2025, S5) – <30° (US 5439402, S6)]
    "alpha_shaft_deg": 5.0,   # [VERIFICADO como práctica: bloque de toma estándar 5° de HamiltonJet (S3)]; adoptado [SUPUESTO]
    "h_shaft": 115.0,      # eje sobre el fondo en la cara del impulsor [CALCULADO: calado nominal − ~20 mm; ver regla]
    "R_ramp_top": 120.0,   # radio del arco del techo junto a la garganta [ESTIMADO: ~1,1 D]
    "R_ramp_tan": 120.0,   # radio del arco de tangencia con el fondo [ESTIMADO: ~1,1 D]
    "R_lower": 60.0,       # radio de la pared inferior junto a la garganta [ESTIMADO: ~0,5 D]
    "r_lip": 12.0,         # radio de nariz del labio [ESTIMADO: ~0,1 D_garganta, memoria técnica]
    "W_open": 130.0,       # ancho de la abertura [ESTIMADO: 1,2 D; HJ212 ≈ 1,24 D (S9, foro)]
    "bar_t": 4.0,          # espesor de barra de rejilla [ESTIMADO]
    "bar_gap": 12.0,       # luz entre barras [ESTIMADO: < pasajes de la bomba; ver R10a]
    "K_grille": (0.2, 0.6),  # pérdida de la rejilla perfilada/rectangular [ESTIMADO: Kirschmer, memoria técnica]
    "wall": 6.0,           # pared del conducto/carcasa [SUPUESTO]
    "clear_dry": 10.0,     # holgura mínima carcasa seca ↔ techo del conducto [SUPUESTO]
    "coupling_len": 40.0,  # acople motor-eje [SUPUESTO]
    # --- jet (puntos de operación) -------------------------------------------
    "eta_drive": 0.85,     # motor + ESC [ESTIMADO: BLDC 5 kW, sin ficha]
    "eta_pump": 0.65,      # bomba chica [ESTIMADO: rango 0.5–0.8; Bulten usa 0.90 en jets grandes]
    "eps_in": 0.20,        # pérdida de toma ε [VERIFICADO como rango típico: Bulten 2006 usa 0.10–0.30]
    "K_in_static": 0.20,   # pérdida de conducto a V=0, sobre V_bomba²/2g [ESTIMADO]
    "phi_noz": 0.02,       # pérdida de tobera φ [VERIFICADO: valor del ejemplo de Bulten 2006]
    "wake": 0.05,          # fracción de estela w [ESTIMADO: casco chico; Bulten ejemplo 0.12]
    "nws": (3.5, 4.0),     # vel. específica de succión adim. [VERIFICADO: Bulten 2006 §2.2.3: ~4,0 común, 3,5 diseño]
    "speeds_kmh": (0.0, 5.0, 9.26, 10.0, 20.0, 30.0),
}


# =============================================================================
# 3. Cálculos
# =============================================================================
def static_draft(mass, rho, L_mm, B_mm, Cb):
    """T = m / (ρ·Cb·L·B)  [m] — caja equivalente."""
    return mass / (rho * Cb * (L_mm / 1e3) * (B_mm / 1e3))


def _arc(p0, phi0, phi1, R, n=24):
    """Arco tangente: arranca en p0 con rumbo phi0 (rad, desde +xf) y termina con rumbo phi1."""
    x0, y0 = p0
    phis = np.linspace(phi0, phi1, n)
    if phi1 < phi0:   # giro horario: centro a la derecha del avance
        cx, cy = x0 + R * math.sin(phi0), y0 - R * math.cos(phi0)
        pts = [(cx - R * math.sin(p), cy + R * math.cos(p)) for p in phis]
    else:             # giro antihorario
        cx, cy = x0 - R * math.sin(phi0), y0 + R * math.cos(phi0)
        pts = [(cx + R * math.sin(p), cy - R * math.cos(p)) for p in phis]
    return np.array(pts)


def intake_geometry(p, T_static_mm):
    """Geometría de la toma enrasada corregida (xf hacia proa desde el espejo, y sobre el fondo)."""
    th = math.radians(p["theta_ramp_deg"])
    al = math.radians(p["alpha_shaft_deg"])
    Rt = p["D_throat"] / 2
    x_imp = p["pump_stack_aft_of_impeller"] * math.cos(al)  # cara del impulsor (xf)
    h = p["h_shaft"]
    n_ax = np.array([-math.sin(al), math.cos(al)])            # normal "arriba" al eje
    c_imp = np.array([x_imp, h])
    top = c_imp + Rt * n_ax
    bot = c_imp - Rt * n_ax

    # Techo (rampa): arco R2 (α → −θ), recta a −θ, arco R1 (−θ → 0) tangente al fondo.
    a2 = _arc(tuple(top), al, -th, p["R_ramp_top"])
    y_after_a2 = a2[-1, 1]
    y_end_straight = p["R_ramp_tan"] * (1 - math.cos(th))
    dy = y_after_a2 - y_end_straight
    if dy <= 0:
        raise ValueError("rampa imposible: bajar R_ramp_* o subir h_shaft")
    p_s1 = a2[-1] + np.array([dy / math.tan(th), -dy])
    a1 = _arc(tuple(p_s1), -th, 0.0, p["R_ramp_tan"])
    roof = np.vstack([a2, p_s1, a1])
    x_tan = a1[-1, 0]

    # Pared inferior: arco R3 desde el fondo de la garganta (α → −θ) y recta paralela al techo.
    nu = np.array([math.sin(th), math.cos(th)])
    c_roof = float(nu @ a2[-1])
    R3 = p["R_lower"]
    c_low = float(nu @ bot) + R3 * (1 - math.cos(th + al))
    k_perp = (c_roof - c_low) / p["D_throat"]          # ancho normal del tramo inclinado / D_garganta
    A_incl = k_perp * p["D_throat"] * p["W_open"] * 0.9   # sección inclinada (rect. redondeado, factor 0,9 [ESTIMADO])
    R3_note = "" if k_perp * p["W_open"] * 0.9 >= p["D_throat"] * math.pi / 4 else \
        "sección inclinada menor que la garganta: subir h_shaft o bajar R_lower"
    a3 = _arc(tuple(bot), al, -th, R3)
    # nariz del labio: círculo de radio r tangente a y=0 y a la recta inferior
    r = p["r_lip"]
    x_c = (c_low - r * (1 + math.cos(th))) / math.sin(th)
    nose_t_line = np.array([x_c, r]) + r * nu
    angs = np.linspace(math.pi / 2 - th, -math.pi / 2, 20)
    nose = np.array([(x_c + r * math.cos(a), r + r * math.sin(a)) for a in angs])
    lower = np.vstack([a3, nose_t_line, nose])
    x_lip = x_c + r                         # punta del labio (extremo hacia proa)
    x_lip_sharp = c_low / math.sin(th)      # intersección geométrica sin redondeo

    # Abertura en planta: tramo rectangular + extremo de proa semielíptico (semieje = W)
    L_open = x_tan - x_lip
    W = p["W_open"]
    a_ell = min(W, L_open)
    A_open = W * (L_open - a_ell) + math.pi * a_ell * W / 4
    n_bars = int((W - p["bar_gap"]) // (p["bar_t"] + p["bar_gap"]))
    open_frac = (W - n_bars * p["bar_t"]) / W
    A_imp = math.pi * p["D_imp"] ** 2 / 4
    A_thr = math.pi * p["D_throat"] ** 2 / 4

    # Eje: recta por el centro del impulsor con pendiente α (sube hacia proa).
    def y_shaft(xf):
        return h + (xf - x_imp) * math.tan(al)

    def roof_y(xf):
        xs, ys = roof[:, 0], roof[:, 1]
        if xf >= x_tan:
            return 0.0
        return float(np.interp(xf, xs, ys))

    # Cruce eje ↔ techo (donde va el sello)
    xs = np.linspace(x_imp, x_tan, 4000)
    diff = np.array([y_shaft(x) - roof_y(x) for x in xs])
    idx = np.where(diff > 0)[0]
    x_cross = float(xs[idx[0]]) if len(idx) else float("nan")

    def first_clear_x(radius, x_from, length):
        """Primer xf ≥ x_from donde un cilindro coaxial al eje (radio, largo) libra el techo."""
        need = radius + p["wall"] + p["clear_dry"]
        for x0 in np.arange(x_from, x_from + 1500, 2.0):
            ok = all(y_shaft(x) - need / math.cos(al) >= roof_y(x)
                     for x in np.linspace(x0, x0 + length, 30))
            if ok:
                return float(x0)
        return float("nan")

    x_seal = x_cross                     # sello en el techo (cara mojada)
    x_bh0 = first_clear_x(35.0, x_seal, p["bearing_housing_len"])  # caja de cojinetes Ø70 [SUPUESTO]
    x_cp0 = x_bh0 + p["bearing_housing_len"]
    x_m0 = first_clear_x(p["motor_diam"] / 2, x_cp0 + p["coupling_len"], p["motor_len"])
    x_m1 = x_m0 + p["motor_len"]
    x_mc = 0.5 * (x_m0 + x_m1)

    g = {
        "x_imp": x_imp, "x_lip": x_lip, "x_lip_sharp": x_lip_sharp, "x_tan": x_tan,
        "lip_from_imp": x_lip - x_imp, "tan_from_imp": x_tan - x_imp,
        "L_open": L_open, "W_open": W, "A_open_gross": A_open, "n_bars": n_bars,
        "open_frac": open_frac, "A_open_eff": A_open * open_frac,
        "A_imp": A_imp, "A_throat": A_thr,
        "A_open_over_imp": A_open / A_imp, "A_eff_over_imp": A_open * open_frac / A_imp,
        "R3": R3, "R3_note": R3_note, "k_perp": k_perp, "A_incl": A_incl,
        "A_incl_over_throat": A_incl / A_thr,
        "y_throat_top": float(top[1]), "y_throat_bot": float(bot[1]),
        "roof_rise": float(top[1]),
        "x_shaft_exits_roof": x_cross, "shaft_wet_len": (x_cross - x_imp) / math.cos(al),
        "x_bearing_housing": (x_bh0, x_cp0), "x_motor": (x_m0, x_m1),
        "motor_axis_height_center": y_shaft(x_mc),
        "motor_bottom_height": y_shaft(x_mc) - p["motor_diam"] / 2 / math.cos(al),
        "nozzle_axis_height_transom": y_shaft(0.0),
        "h_shaft": h, "T_static": T_static_mm,
        "shaft_minus_T": h - T_static_mm,
        "shaft_underside_minus_T": h - p["d_shaft"] / 2 - T_static_mm,
        "imp_top_minus_T": h + p["D_imp"] / 2 - T_static_mm,
        "roof": roof, "lower": lower, "y_shaft": y_shaft, "c_imp": c_imp, "n_ax": n_ax,
    }
    return g


def jet_point(V_kmh, P_elec, p, w):
    """Punto de operación: η_p·P_eje = ρgQ·H_R, H_R = (1+φ)Vj²/2g − (1−ε)Vin²/2g (Bulten ec. 2.56, h_j≈0)."""
    rho = w["rho"]
    V = V_kmh / 3.6
    Vin = (1 - p["wake"]) * V
    An = math.pi * (p["D_nozzle"] / 1e3) ** 2 / 4
    Php = p["eta_pump"] * p["eta_drive"] * P_elec

    def f(vj):
        return rho * An * vj * ((1 + p["phi_noz"]) * vj ** 2 / 2 - (1 - p["eps_in"]) * Vin ** 2 / 2) - Php

    lo = Vin * math.sqrt((1 - p["eps_in"]) / (1 + p["phi_noz"])) + 1e-6
    hi = 100.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    Vj = 0.5 * (lo + hi)
    Q = An * Vj
    A_thr = math.pi * (p["D_throat"] / 1e3) ** 2 / 4
    Vp = Q / A_thr
    return {"V_kmh": V_kmh, "V": V, "Vin": Vin, "Vj": Vj, "Q": Q, "V_pump": Vp,
            "IVR": (Vp / V) if V > 0 else float("inf"),
            "IVR_Bulten": V / Vp, "T_N": rho * Q * (Vj - Vin), "P_hyd": Php}


def npsh(pt, p, w, h_imp_top_above_fs_m, A_grille_eff_mm2, K_grille):
    """NPSH_A (Bulten ec. 2.64 + pérdida de rejilla) y NPSH_R por n_ωs (Bulten ec. 2.29)."""
    rho = w["rho"]
    head_atm = (w["p_atm"] - w["p_v"]) / (rho * G)
    dyn = (1 - p["eps_in"]) * pt["Vin"] ** 2 / (2 * G)
    loss_static = p["K_in_static"] * pt["V_pump"] ** 2 / (2 * G) if pt["V"] < 0.5 * pt["V_pump"] else 0.0
    Vg = pt["Q"] / (A_grille_eff_mm2 / 1e6)
    loss_grille = K_grille * Vg ** 2 / (2 * G)
    NA = head_atm + dyn - loss_static - loss_grille - h_imp_top_above_fs_m
    Om = p["rpm"] * 2 * math.pi / 60
    NR = {n: (Om * math.sqrt(pt["Q"]) / n) ** (4 / 3) / G for n in p["nws"]}
    Qmax = {n: (n * (G * NA) ** 0.75 / Om) ** 2 for n in p["nws"]}
    return {"NPSH_A": NA, "NPSH_R": NR, "ratio": {n: NA / NR[n] for n in NR}, "Q_max": Qmax,
            "V_grille": Vg, "loss_grille": loss_grille, "loss_static": loss_static, "head_atm": head_atm}


def compute():
    w = load_water()
    p = P
    out = {"water": w, "scales": drawing_scales(), "jorge": jorge_layout()}
    T_nom = static_draft(p["mass"], w["rho"], p["L_wl"], p["B_wl"], p["Cb"]) * 1e3
    T_min = static_draft(p["mass"], w["rho"], p["L_wl_range"][1], p["B_wl_range"][1], p["Cb_range"][1]) * 1e3
    T_max = static_draft(p["mass"], w["rho"], p["L_wl_range"][0], p["B_wl_range"][0], p["Cb_range"][0]) * 1e3
    out["draft_mm"] = {"nominal": T_nom, "min": T_min, "max": T_max}
    g = intake_geometry(p, T_nom)
    out["geom"] = {k: v for k, v in g.items() if not callable(v) and not isinstance(v, np.ndarray)}
    out["tip_speed"] = math.pi * p["D_imp"] / 1e3 * p["rpm"] / 60

    # Áreas de la rejilla de Jorge
    Lj, Wj = p["grille_jorge"]
    nbj = int((Wj - p["bar_gap"]) // (p["bar_t"] + p["bar_gap"]))
    A_j = Lj * Wj
    A_j_eff = A_j * (Wj - nbj * p["bar_t"]) / Wj
    out["jorge_grille"] = {"A_gross": A_j, "n_bars": nbj, "A_eff": A_j_eff,
                           "A_gross_over_imp": A_j / g["A_imp"], "A_eff_over_imp": A_j_eff / g["A_imp"],
                           "len_needed_for_throat_at_theta": p["D_throat"] / math.sin(math.radians(p["theta_ramp_deg"]))}

    # Puntos de operación y cavitación
    jl = out["jorge"]
    h_j_jorge_shaft = 0.5 * (jl["shaft_height_pump"][0] + jl["shaft_height_pump"][1])
    rows = []
    for Pel, tag in ((p["P_elec_design"], "diseño 5 kW"), (p["P_elec_max"], "máx 7,2 kW")):
        for v in p["speeds_kmh"]:
            pt = jet_point(v, Pel, p, w)
            # superficie libre en la popa: en reposo/baja velocidad = calado; planeando (≥ 20 km/h) ≈ fondo
            fs = T_nom if v < 15 else 0.0
            h_top_corr = (p["h_shaft"] + p["D_imp"] / 2 - fs) / 1e3
            h_top_jorge = (h_j_jorge_shaft + p["D_imp"] / 2 - fs) / 1e3
            r = {"caso": tag, **pt}
            for K in p["K_grille"]:
                r[f"corr_K{K}"] = npsh(pt, p, w, h_top_corr, g["A_open_eff"], K)
                r[f"jorge_K{K}"] = npsh(pt, p, w, h_top_jorge, A_j_eff, K)
            rows.append(r)
    out["points"] = rows
    return out, g


# =============================================================================
# 4. Dibujo
# =============================================================================
C_HULL = "#1f2a36"
C_WATER = "#2a7fd4"
C_BAD = "#c0392b"
C_OK = "#1e8449"
C_DUCT = "#5d6d7e"
C_MOTOR = "#7f8c8d"


def X(xf):
    """xf (hacia proa desde el espejo) → coordenada de dibujo (proa a la izquierda)."""
    return -np.asarray(xf)


def dim_h(ax, x1, x2, y, text, color="k", fs=7.5, above=True):
    ax.add_patch(FancyArrowPatch((X(x1), y), (X(x2), y), arrowstyle="<|-|>", mutation_scale=7,
                                 color=color, lw=0.7, shrinkA=0, shrinkB=0))
    ax.text(0.5 * (X(x1) + X(x2)), y + (5 if above else -5), text, ha="center",
            va="bottom" if above else "top", fontsize=fs, color=color)


def dim_v(ax, xf, y1, y2, text, color="k", fs=7.5, side="right"):
    ax.add_patch(FancyArrowPatch((X(xf), y1), (X(xf), y2), arrowstyle="<|-|>", mutation_scale=7,
                                 color=color, lw=0.7, shrinkA=0, shrinkB=0))
    dx = 6 if side == "right" else -6
    ax.text(X(xf) + dx, 0.5 * (y1 + y2), text, ha="left" if side == "right" else "right",
            va="center", fontsize=fs, color=color, rotation=0)


def note(ax, xy, xytext, text, color="k", fs=7.5):
    ax.annotate(text, xy=(X(xy[0]), xy[1]), xytext=(X(xytext[0]), xytext[1]), fontsize=fs, color=color,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=0.7, mutation_scale=7),
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, lw=0.6, alpha=0.95))


def waterline(ax, d, x_from=1150, x_to=-420):
    ax.fill_between([X(x_from), X(x_to)], d["min"], d["max"], color=C_WATER, alpha=0.10, lw=0)
    ax.plot([X(x_from), X(x_to)], [d["nominal"]] * 2, color=C_WATER, lw=1.1, ls="--")
    ax.text(X(x_from) + 8, d["nominal"] + 4,
            f"flotación estática 150 kg: T ≈ {d['nominal']:.0f} mm (banda {d['min']:.0f}–{d['max']:.0f}) [CALCULADO]",
            fontsize=7.5, color=C_WATER, va="bottom")


def hull(ax, x_from=1150, top=420, gap=None):
    """Fondo (y=0) y espejo (xf=0). gap=(x_aft, x_fwd) deja abierta la abertura."""
    if gap:
        ax.plot([X(x_from), X(gap[1])], [0, 0], color=C_HULL, lw=2.0)
        ax.plot([X(gap[0]), 0], [0, 0], color=C_HULL, lw=2.0)
    else:
        ax.plot([X(x_from), 0], [0, 0], color=C_HULL, lw=2.0)
    ax.plot([0, 0], [0, top], color=C_HULL, lw=2.0)
    ax.text(4, top - 6, "espejo", fontsize=7.5, color=C_HULL, va="top")
    ax.text(X(x_from) + 8, -8, "fondo (cara exterior, y = 0)", fontsize=7.5, color=C_HULL, va="top")


def pump_local(c, n_ax, al, pts_sr):
    """(s hacia popa a lo largo del eje, r radial) → (xf, y)."""
    d = np.array([-math.cos(al), -math.sin(al)])
    return np.array([c + s * d + r * n_ax for s, r in pts_sr])


def draw_pump(ax, c, al, p, steer=True, label=True):
    n_ax = np.array([-math.sin(al), math.cos(al)])
    Ri = p["D_imp"] / 2 + 0.7
    wl = p["wall"]
    Rn = p["D_nozzle"] / 2
    prof = [(0, Ri), (50, Ri), (120, Ri - 4), (220, Rn)]
    outer = [(s, r + wl) for s, r in prof]
    for sgn in (1, -1):
        pts_in = pump_local(c, n_ax, al, [(s, sgn * r) for s, r in prof])
        pts_out = pump_local(c, n_ax, al, [(s, sgn * r) for s, r in outer])
        poly = np.vstack([pts_in, pts_out[::-1]])
        ax.add_patch(Polygon(np.c_[X(poly[:, 0]), poly[:, 1]], closed=True, fc="#d5dbdb", ec=C_HULL, lw=0.8))
    imp = pump_local(c, n_ax, al, [(6, -p["D_imp"] / 2), (44, -p["D_imp"] / 2),
                                   (44, p["D_imp"] / 2), (6, p["D_imp"] / 2)])
    ax.add_patch(Polygon(np.c_[X(imp[:, 0]), imp[:, 1]], closed=True, fc="#f5b041", ec=C_HULL, lw=0.8,
                         hatch="////", alpha=0.9))
    hub = pump_local(c, n_ax, al, [(50, 22), (120, 8), (120, -8), (50, -22)])
    ax.add_patch(Polygon(np.c_[X(hub[:, 0]), hub[:, 1]], closed=True, fc="#aab7b8", ec=C_HULL, lw=0.6))
    for s in (60, 80, 100):  # álabes del estator (esquema)
        seg = pump_local(c, n_ax, al, [(s, -Ri + 3), (s + 12, Ri - 3)])
        ax.plot(X(seg[:, 0]), seg[:, 1], color=C_HULL, lw=0.6)
    if steer:
        st = pump_local(c, n_ax, al, [(220, Rn + wl), (220 + p["steer_len"], Rn - 2 + wl),
                                      (220 + p["steer_len"], -Rn + 2 - wl), (220, -Rn - wl)])
        ax.add_patch(Polygon(np.c_[X(st[:, 0]), st[:, 1]], closed=True, fc="#e5e8e8", ec=C_HULL, lw=0.8))
    if label:
        for s_, txt in ((25, "impulsor"), (85, "estator"), (190, "tobera Ø72")):
            q = pump_local(c, n_ax, al, [(s_, -p["D_imp"] / 2 - wl - 4)])[0]
            ax.text(X(q[0]), q[1], txt, fontsize=6.5, ha="center", va="top", color=C_HULL)
    return None


def draw_motor(ax, x0, x1, ycen_fn, D, color=C_MOTOR, lbl="motor"):
    xs = np.array([x0, x1, x1, x0])
    ys = np.array([ycen_fn(x0) - D / 2, ycen_fn(x1) - D / 2, ycen_fn(x1) + D / 2, ycen_fn(x0) + D / 2])
    ax.add_patch(Polygon(np.c_[X(xs), ys], closed=True, fc=color, ec=C_HULL, lw=0.8, alpha=0.85))
    ax.text(X(0.5 * (x0 + x1)), ycen_fn(0.5 * (x0 + x1)), lbl, ha="center", va="center", fontsize=7.5,
            color="white", weight="bold")


def plot(res, g, out_svg):
    p = P
    d = res["draft_mm"]
    jl = res["jorge"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    fig, axes = plt.subplots(2, 1, figsize=(16, 13.2))
    for ax in axes:
        ax.set_aspect("equal")
        ax.set_xlim(-1160, 430)
        ax.set_ylim(-118, 470)
        ax.set_xticks(np.arange(-1100, 401, 100))
        ax.set_xticklabels([f"{-t:d}" for t in np.arange(-1100, 401, 100)], fontsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.grid(True, color="#ecf0f1", lw=0.5)
        ax.set_xlabel("distancia hacia proa desde el espejo, mm (negativo = fuera, a popa del espejo)", fontsize=8)
        ax.set_ylabel("altura sobre el fondo, mm", fontsize=8)

    # ---------------------------------------------------------------- (a) Jorge
    ax = axes[0]
    ax.set_title("(a) Plano de Jorge 26/09/2026 — posiciones medidas en la imagen (±15 %: el dibujo no respeta sus cotas)",
                 fontsize=10, loc="left", color=C_BAD)
    hull(ax)
    floor_h = 0.5 * sum(jl["floor_height"])
    ax.plot([X(1150), X(0)], [floor_h, floor_h], color=C_HULL, lw=0.6, ls=":")
    ax.text(X(1140), floor_h + 3, "piso interior dibujado", fontsize=7, color=C_HULL)
    waterline(ax, d)
    hs_j = 0.5 * sum(jl["shaft_height_pump"])
    hm_j = 0.5 * sum(jl["motor_axis_height"])
    x_imp_j = 0.5 * sum(jl["impeller_face_from_transom"])
    c = np.array([x_imp_j, hs_j])
    # bomba horizontal (como en el plano), estirada hasta el espejo
    pj = dict(p)
    draw_pump(ax, c, 0.0, pj, steer=False)
    # tubo hasta el espejo + boquilla fuera
    ax.add_patch(Rectangle((X(x_imp_j - 220), hs_j - 42), (x_imp_j - 220), 84, fc="#e5e8e8", ec=C_HULL, lw=0.6))
    ax.add_patch(Rectangle((0, hs_j - 40), 120, 80, fc="#e5e8e8", ec=C_HULL, lw=0.8))
    # cojinetes/sello y motor
    xm0, xm1 = jl["_mid"]["motor_x"]
    ax.add_patch(Rectangle((X(x_imp_j + 120), hs_j - 35), 120, 70, fc="#d6eaf8", ec=C_HULL, lw=0.8))
    ax.text(X(x_imp_j + 60), hs_j + 42, "cojinetes 8 + sello 9\n(\"fuera de la cámara húmeda\")",
            fontsize=7, ha="center", va="bottom")
    draw_motor(ax, xm0, xm1, lambda x: hm_j, jl["_mid"]["motor_diam"], lbl="motor 7")
    ax.text(X(0.5 * (xm0 + xm1)), hm_j - jl["_mid"]["motor_diam"] / 2 - 6,
            f"eje del motor {jl['motor_axis_height'][0]:.0f}–{jl['motor_axis_height'][1]:.0f} (no coaxial con la bomba)",
            ha="center", va="top", fontsize=7, color=C_BAD)
    ax.plot([X(xm1 + 30), X(-60)], [hs_j, hs_j], color="k", lw=0.6, ls="-.")
    # rejilla (en el fondo, a popa del impulsor)
    gf = 0.5 * sum(jl["grille_fwd_from_transom"])
    ga = 0.5 * sum(jl["grille_aft_from_transom"])
    ax.add_patch(Rectangle((X(gf), 4), gf - ga, 12, fc="white", ec=C_BAD, lw=1.2, hatch="||||"))
    # nada conecta la rejilla con la bomba
    ax.plot([X(0.5 * (gf + ga)), X(0.5 * (gf + ga))], [18, hs_j - 50], color=C_BAD, lw=1.0, ls=(0, (3, 3)))
    ax.text(X(0.5 * (gf + ga)) + 6, 0.5 * (18 + hs_j - 50), "✕ sin conducto", color=C_BAD, fontsize=8,
            va="center", weight="bold")
    note(ax, (0.5 * (gf + ga), 10), (520, -55),
         f"rejilla 120×90 a ≈{ga:.0f}–{gf:.0f} mm del espejo:\nqueda {res['jorge']['grille_center_aft_of_impeller'][0]:.0f}–"
         f"{res['jorge']['grille_center_aft_of_impeller'][1]:.0f} mm A POPA del impulsor (bajo la tobera)",
         color=C_BAD)
    note(ax, (x_imp_j - 25, hs_j + 55), (x_imp_j + 160, 330),
         "impulsor Ø108: la entrada axial \"Ø inicial toma 120\"\nno tiene conducto; la carcasa está cerrada",
         color=C_BAD)
    dim_v(ax, -150, 0, hs_j, f"eje {jl['shaft_height_pump'][0]:.0f}–{jl['shaft_height_pump'][1]:.0f}", color=C_BAD,
          side="right")
    ax.plot([X(-150), X(-40)], [hs_j, hs_j], color=C_BAD, lw=0.5, ls=":")
    dim_v(ax, -230, d["nominal"], hs_j + p["D_imp"] / 2,
          f"impulsor entero\n{hs_j - p['D_imp'] / 2 - d['nominal']:.0f}–{hs_j + p['D_imp'] / 2 - d['nominal']:.0f} mm\n"
          "SOBRE la flotación\n→ no ceba", color=C_BAD, side="right")
    ax.text(X(1140), 440,
            "Lectura: el agua tendría que entrar por la rejilla, que está a popa del impulsor y debajo de la tobera, "
            "y subir sin conducto hasta una bomba cerrada\ncuyo impulsor está por encima de la flotación. "
            "Así como está dibujado no bombea: Jorge tiene razón, la toma está muy atrás (y además le falta la rampa).",
            fontsize=8, va="top", color=C_BAD)

    # ---------------------------------------------------------------- (b) corregido
    ax = axes[1]
    al = math.radians(p["alpha_shaft_deg"])
    ax.set_title("(b) Toma corregida (parametrizada): rampa enrasada adelante del impulsor, eje bajo la flotación, "
                 "sello y cojinetes en seco sobre la rampa", fontsize=10, loc="left", color=C_OK)
    hull(ax, gap=(g["x_lip"], g["x_tan"]))
    waterline(ax, d)
    roof, lower = g["roof"], g["lower"]
    ax.plot(X(roof[:, 0]), roof[:, 1], color=C_DUCT, lw=2.0)
    ax.plot(X(lower[:, 0]), lower[:, 1], color=C_DUCT, lw=2.0)
    # bloque de toma (sólido entre pared inferior y fondo, hasta la carcasa)
    blk = np.vstack([lower[::-1], [[g["x_imp"] - 30, 0.0]]])
    blk = np.vstack([[[g["x_imp"] - 30, g["y_throat_bot"] - 2]], lower, [[g["x_imp"] - 30, 0.0]]])
    ax.add_patch(Polygon(np.c_[X(blk[:, 0]), blk[:, 1]], closed=True, fc="#eaeded", ec="none", alpha=0.9))
    # rejilla en el plano del fondo
    ax.add_patch(Rectangle((X(g["x_tan"] - 20), -6), (g["x_tan"] - 20) - g["x_lip"], 6, fc="white", ec=C_OK,
                           lw=1.0, hatch="----"))
    # bomba inclinada α
    c = g["c_imp"]
    draw_pump(ax, c, al, p, steer=True)
    # eje Ø20 desde el impulsor hasta el motor
    x_m0, x_m1 = g["x_motor"]
    ys = g["y_shaft"]
    xx = np.array([g["x_imp"], x_m0])
    for sgn in (1, -1):
        ax.plot(X(xx), ys(xx) + sgn * p["d_shaft"] / 2, color=C_HULL, lw=0.8)
    ax.plot(X(np.array([-150, x_m1 + 40])), ys(np.array([-150, x_m1 + 40])), color="k", lw=0.6, ls="-.")
    # sello en el techo, caja de cojinetes, acople, motor
    xs0 = g["x_shaft_exits_roof"]
    ax.add_patch(Polygon(np.c_[X([xs0 - 6, xs0 + 14, xs0 + 14, xs0 - 6]),
                               [ys(xs0) - 22, ys(xs0 + 14) - 22, ys(xs0 + 14) + 22, ys(xs0) + 22]],
                         closed=True, fc="#f9e79f", ec=C_HULL, lw=0.8))
    b0, b1 = g["x_bearing_housing"]
    ax.add_patch(Polygon(np.c_[X([b0, b1, b1, b0]), [ys(b0) - 35, ys(b1) - 35, ys(b1) + 35, ys(b0) + 35]],
                         closed=True, fc="#d6eaf8", ec=C_HULL, lw=0.8))
    draw_motor(ax, x_m0, x_m1, ys, p["motor_diam"], lbl="motor 5 kW")
    # cotas horizontales
    yd = -40
    dim_h(ax, 0, g["x_imp"], yd, f"{g['x_imp']:.0f}", fs=7)
    dim_h(ax, g["x_imp"], g["x_lip"], yd, f"{g['lip_from_imp']:.0f}", fs=7)
    dim_h(ax, g["x_lip"], g["x_tan"], yd, f"abertura {g['L_open']:.0f} × {g['W_open']:.0f}", fs=7, color=C_OK)
    dim_h(ax, 0, g["x_lip"], -66, f"labio a {g['x_lip']:.0f} del espejo", fs=7, above=False)
    dim_h(ax, 0, g["x_tan"], -84, f"tangencia de la rampa a {g['x_tan']:.0f} del espejo "
                                   f"({g['tan_from_imp']:.0f} de la cara del impulsor)", fs=7, above=False)
    for xv in (g["x_imp"], g["x_lip"], g["x_tan"]):
        ax.plot([X(xv)] * 2, [0, yd - 2], color="k", lw=0.4, ls=":")
    # cotas verticales
    dim_v(ax, -175, 0, ys(0.0), "", side="right")
    dim_v(ax, g["x_imp"] - 2, 0, g["h_shaft"], f"eje en el impulsor\n{g['h_shaft']:.0f}", side="left")
    ax.plot([X(-175), X(-40)], [ys(0.0)] * 2, color="k", lw=0.4, ls=":")
    ax.text(X(-175) + 6, ys(0.0) / 2, f"{ys(0.0):.0f} (eje en el espejo)", fontsize=7, va="center")
    xmc = 0.5 * (x_m0 + x_m1)
    dim_v(ax, x_m1 + 25, 0, ys(xmc), f"eje del motor\n≈ {ys(xmc):.0f}", side="left", color=C_OK)
    # ángulo de rampa
    th = p["theta_ramp_deg"]
    k_mid = int(np.argmin(np.abs(roof[:, 1] - 0.40 * g["y_throat_top"])))
    mid = roof[k_mid]
    ax.text(X(mid[0]) - 22, mid[1] + 14, f"techo / rampa θ = {th:.0f}°", fontsize=8, color=C_DUCT, ha="center",
            va="bottom", rotation=th, rotation_mode="anchor")
    note(ax, (g["x_lip"] + 3, 4), (g["x_lip"] - 140, 280 + 0),
         f"labio redondeado r ≈ {p['r_lip']:.0f}\n(IVR alta a baja velocidad:\nseparación en la cara interna)", color=C_DUCT)
    note(ax, (0.5 * (g["x_lip"] + g["x_tan"]), -3), (0.5 * (g["x_lip"] + g["x_tan"]) + 260, -50),
         f"rejilla enrasada: {g['n_bars']} barras longitudinales {p['bar_t']:.0f} mm, luz {p['bar_gap']:.0f} mm\n"
         f"área bruta {g['A_open_gross'] / 1e3:.1f}·10³ mm² = {g['A_open_over_imp']:.1f}× A_impulsor; "
         f"efectiva {g['A_eff_over_imp']:.1f}×", color=C_OK)
    note(ax, (xs0 + 4, ys(xs0) + 22), (xs0 + 40, 330),
         "sello (cara mojada) donde el eje\nsale por el techo; cojinetes en seco", color=C_HULL)
    note(ax, (g["x_imp"] - 25, g["h_shaft"] + p["D_imp"] / 2), (g["x_imp"] - 120, 330),
         f"impulsor Ø108: eje {g['shaft_minus_T']:+.0f} mm respecto\nde la flotación nominal → ceba solo", color=C_OK)
    ax.text(X(1140), 440,
            f"Regla: eje en el impulsor ≤ flotación estática medida en popa (HamiltonJet). Abertura entera A PROA del "
            f"impulsor: labio {g['lip_from_imp']:.0f} mm y tangencia {g['tan_from_imp']:.0f} mm\nadelante de su cara; "
            f"rampa {th:.0f}°, eje {p['alpha_shaft_deg']:.0f}° (sube hacia proa). Fondo liso, sin escalones > 2 mm ni "
            "apéndices delante de la toma. Cotas en mm; ver research/R10a_toma_waterjet.md.",
            fontsize=8, va="top", color=C_OK)

    # Insets: planta de las aberturas
    for ax_, kind in ((axes[0], "jorge"), (axes[1], "corr")):
        ins = ax_.inset_axes([0.865, 0.04, 0.13, 0.36] if kind == "jorge" else [0.865, 0.56, 0.13, 0.36])
        ins.set_aspect("equal")
        ins.set_xticks([])
        ins.set_yticks([])
        ins.set_title("vista inferior (mismas escalas)", fontsize=6.5)
        if kind == "jorge":
            Lj, Wj = p["grille_jorge"]
            ins.add_patch(Rectangle((-Lj / 2, -Wj / 2), Lj, Wj, fc="white", ec=C_BAD, lw=1.0))
            nb = res["jorge_grille"]["n_bars"]
            for k in range(nb):
                yb = -Wj / 2 + p["bar_gap"] + k * (p["bar_t"] + p["bar_gap"]) + p["bar_t"] / 2
                ins.plot([-Lj / 2, Lj / 2], [yb, yb], color=C_BAD, lw=1.0)
            ins.text(0, -Wj / 2 - 12, f"120 × 90\n{res['jorge_grille']['A_eff_over_imp']:.2f}× A_imp efectiva",
                     ha="center", va="top", fontsize=6.5, color=C_BAD)
            circ = plt.Circle((0, 0), p["D_imp"] / 2, fill=False, ls=":", color="k", lw=0.6)
            ins.add_patch(circ)
            ins.set_xlim(-170, 170)
            ins.set_ylim(-140, 100)
        else:
            Lo, Wo = g["L_open"], g["W_open"]
            a = min(Wo, Lo)
            t = np.linspace(-math.pi / 2, math.pi / 2, 40)
            xs_ = list(-Lo / 2 + (Lo - a) + a * np.cos(t))
            ys_ = list(Wo / 2 * np.sin(t))
            poly = np.array([(-Lo / 2, -Wo / 2)] + list(zip(xs_, ys_)) + [(-Lo / 2, Wo / 2)])
            poly[:, 0] *= -1   # proa (extremo semielíptico, tangencia de la rampa) a la izquierda
            ins.add_patch(Polygon(poly, closed=True, fc="white", ec=C_OK, lw=1.0))
            for k in range(g["n_bars"]):
                yb = -Wo / 2 + p["bar_gap"] + k * (p["bar_t"] + p["bar_gap"]) + p["bar_t"] / 2
                ins.plot([-(Lo / 2 - 0.15 * Lo), Lo / 2], [yb, yb], color=C_OK, lw=1.0)
            ins.text(Lo / 2 + 4, 0, "labio", rotation=90, fontsize=6, va="center", ha="left", color=C_OK)
            ins.text(0, -Wo / 2 - 12, f"proa ← {Lo:.0f} × {Wo:.0f}\n{g['A_eff_over_imp']:.1f}× A_imp efectiva",
                     ha="center", va="top", fontsize=6.5, color=C_OK)
            circ = plt.Circle((0, 0), p["D_imp"] / 2, fill=False, ls=":", color="k", lw=0.6)
            ins.add_patch(circ)
            ins.set_xlim(-185, 185)
            ins.set_ylim(-140, 100)
        ins.text(0, 92, "··· = Ø108 impulsor", ha="center", fontsize=6, va="top")

    fig.suptitle("Toma de agua del waterjet de Jorge (jet boat 2,30 m): plano 26/09/2026 vs corrección — corte lateral "
                 "esquemático por crujía, cotas en mm", fontsize=12, x=0.01, ha="left")
    fig.text(0.01, 0.005, "Generado por referencias/croquis_toma_waterjet.py (P1, 2026-10-01). Esquema, no plano de "
             "fabricación. Números etiquetados en research/R10a_toma_waterjet.md.", fontsize=7, color="#555")
    fig.tight_layout(rect=(0, 0.01, 1, 0.97))
    fig.savefig(out_svg, format="svg")
    fig.savefig(str(out_svg).replace(".svg", ".png"), format="png", dpi=110)
    plt.close(fig)


# =============================================================================
# 5. Salida por consola
# =============================================================================
def report(res):
    s = res["scales"]
    jl = res["jorge"]
    g = res["geom"]
    d = res["draft_mm"]
    w = res["water"]
    L = []
    L.append(f"Agua: ρ = {w['rho']:.0f} kg/m³, p_atm = {w['p_atm']:.0f} Pa, p_v = {w['p_v']:.0f} Pa ({w['src']})")
    L.append("== 1. Escalas implícitas del plano (mm/px) ==")
    L.append(f"  horizontal: cota 2300 → {s['sx'][0]:.3f}; cadena 850+750+700 → {s['sx'][1]:.3f} "
             f"(tramos {', '.join(f'{v:.2f}' for v in s['sx_parts'])})")
    L.append(f"  vertical: cota 280 → {s['sy'][0]:.3f}; cota 420 → {s['sy'][1]:.3f}")
    L.append("== 2. Plano de Jorge, medido (mm, rango por escala) ==")
    for k, v in jl.items():
        if k.startswith("_"):
            continue
        L.append(f"  {k:32s} {v[0]:7.0f} – {v[1]:7.0f}")
    jg = res["jorge_grille"]
    L.append(f"  rejilla 120×90: bruta {jg['A_gross']:.0f} mm² = {jg['A_gross_over_imp']:.2f}× A_imp; "
             f"{jg['n_bars']} barras → efectiva {jg['A_eff']:.0f} mm² = {jg['A_eff_over_imp']:.2f}× A_imp")
    L.append(f"  largo de abertura que exige un conducto Ø120 a θ = {P['theta_ramp_deg']:.0f}°: "
             f"D/sinθ = {jg['len_needed_for_throat_at_theta']:.0f} mm (el plano da 90)")
    L.append("== 3. Calado estático 150 kg ==")
    L.append(f"  nominal {d['nominal']:.0f} mm (L_wl {P['L_wl']:.0f}, B_wl {P['B_wl']:.0f}, Cb {P['Cb']}); "
             f"mín {d['min']:.0f}; máx {d['max']:.0f}")
    L.append("== 4. Toma corregida ==")
    keys = ["x_imp", "x_lip", "x_lip_sharp", "x_tan", "lip_from_imp", "tan_from_imp", "L_open", "W_open",
            "A_open_gross", "n_bars", "open_frac", "A_open_eff", "A_imp", "A_throat", "A_open_over_imp",
            "A_eff_over_imp", "R3", "k_perp", "A_incl", "A_incl_over_throat", "y_throat_top", "y_throat_bot", "x_shaft_exits_roof", "shaft_wet_len",
            "x_bearing_housing", "x_motor", "motor_axis_height_center", "motor_bottom_height",
            "nozzle_axis_height_transom", "h_shaft", "T_static", "shaft_minus_T", "shaft_underside_minus_T",
            "imp_top_minus_T"]
    for k in keys:
        v = g[k]
        if isinstance(v, tuple):
            L.append(f"  {k:28s} {v[0]:8.1f} – {v[1]:8.1f}")
        elif isinstance(v, float):
            L.append(f"  {k:28s} {v:10.2f}")
        else:
            L.append(f"  {k:28s} {v}")
    if g["R3_note"]:
        L.append("  AVISO: " + g["R3_note"])
    L.append(f"  velocidad de punta del impulsor a {P['rpm']:.0f} rpm: {res['tip_speed']:.1f} m/s")
    L.append("== 5. Puntos de operación (η_p·η_drive·P_el → Q) e IVR; NPSH a 4500 rpm ==")
    hdr = ("caso         V km/h  Q L/s  Vj m/s  Vgarg m/s  IVR(ITTC)  T N | corr: NPSHA  NPSHR3.5/4.0  "
           "margen3.5/4.0 | Jorge(si cebara): NPSHA margen3.5/4.0")
    L.append(hdr)
    for r in res["points"]:
        c = r["corr_K0.6"]
        j = r["jorge_K0.6"]
        ivr = "∞" if math.isinf(r["IVR"]) else f"{r['IVR']:.2f}"
        L.append(f"{r['caso']:12s} {r['V_kmh']:6.2f} {r['Q'] * 1e3:6.1f} {r['Vj']:7.2f} {r['V_pump']:9.2f} "
                 f"{ivr:>9s} {r['T_N']:6.0f} | {c['NPSH_A']:6.2f}  {c['NPSH_R'][3.5]:5.2f}/{c['NPSH_R'][4.0]:5.2f}  "
                 f"{c['ratio'][3.5]:5.2f}/{c['ratio'][4.0]:5.2f} | {j['NPSH_A']:6.2f} "
                 f"{j['ratio'][3.5]:5.2f}/{j['ratio'][4.0]:5.2f}")
    L.append("  (NPSH con rejilla de barra rectangular K = 0,6; margen = NPSH_A/NPSH_R; < 1,0 = cavita)")
    r0 = [r for r in res["points"] if r["V_kmh"] == 0.0]
    for r in r0:
        L.append(f"  {r['caso']}: V en la rejilla corregida {r['corr_K0.6']['V_grille']:.2f} m/s "
                 f"(pérdida {r['corr_K0.2']['loss_grille']:.2f}–{r['corr_K0.6']['loss_grille']:.2f} m); "
                 f"rejilla de Jorge {r['jorge_K0.6']['V_grille']:.2f} m/s "
                 f"(pérdida {r['jorge_K0.2']['loss_grille']:.2f}–{r['jorge_K0.6']['loss_grille']:.2f} m); "
                 f"Q_max sin cavitar (n_ωs 3,5) corr {r['corr_K0.6']['Q_max'][3.5] * 1e3:.1f} L/s")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--out", default=os.path.join(HERE, "croquis_toma_waterjet.svg"))
    ap.add_argument("--json", default=None, help="opcional: volcar resultados numéricos a JSON")
    a = ap.parse_args(argv)
    res, g = compute()
    print(report(res))
    plot(res, g, a.out)
    print(f"SVG: {a.out}")
    if a.json:
        def clean(o):
            if isinstance(o, dict):
                return {str(k): clean(v) for k, v in o.items()}
            if isinstance(o, (list, tuple)):
                return [clean(v) for v in o]
            if isinstance(o, float) and math.isinf(o):
                return None
            return o
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(clean(res), fh, indent=1, ensure_ascii=False)
        print(f"JSON: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
