"""Hidrostática y resistencia al avance R(v) de un jon boat chico de fondo plano.

Modelo por componentes (ver 02_calculos.md §2):

    R = R_F·(1+k) + R_TR + R_W + R_air            [N]

    R_F   fricción ITTC-1957:  C_F = 0.075 / (log10 Re − 2)²  (+ ΔC_F rugosidad)
    R_TR  espejo sumergido (Holtrop & Mennen 1982):
              R_TR = ½ ρ V² A_T c6 ;  c6 = 0.2·(1 − 0.2·F_nT) si F_nT < 5, si no 0
              F_nT = V / sqrt( 2 g A_T / (B + B·C_WP) )
    R_W   formación de olas + joroba de transición (régimen de desplazamiento →
          semi-planeo), forma semi-empírica calibrable:
              R_W = W · c_w · Fr⁴ / (1 + (Fr/Fr_h)⁴)
          ~Fr⁴ por debajo de la velocidad de casco (crecimiento rápido de las olas)
          y meseta (joroba) por encima de Fr_h. c_w y Fr_h se calibran con el
          ensayo de remolque con dinamómetro (PENDIENTES_GASPAR.md).
    R_air arrastre aerodinámico ½ ρ_a Cd A (V + V_viento)²

Ninguna serie sistemática cubre un casco tan corto y lleno (L/∇^(1/3) ≈ 3), por eso
el modelo se presenta con banda de incertidumbre [band_low, band_high] y se
dimensiona con la banda alta.
"""
from __future__ import annotations

import math

import numpy as np

G = 9.81


def masses(inp: dict, battery_mass_kg: float, unit_mass_kg: float) -> dict:
    """Masa total de diseño (desplazamiento) y carga útil sobre la placa de capacidad."""
    b, ld = inp["boat"], inp["load"]
    persons = ld["n_persons"] * ld["mass_per_person_kg"]
    payload = persons + ld["safety_gear_kg"] + ld["misc_kg"] + battery_mass_kg + unit_mass_kg
    total = b["hull_mass_kg"] + payload
    return {
        "persons_kg": persons,
        "payload_kg": payload,           # lo que cuenta contra la placa de capacidad
        "total_kg": total,
        "capacity_kg": b["max_capacity_kg"],
        "capacity_ratio": payload / b["max_capacity_kg"],
    }


def hydrostatics(inp: dict, total_mass_kg: float) -> dict:
    """Calado con costados abiertos (flare) a partir del ancho de fondo y la manga."""
    b = inp["boat"]
    rho = inp["water"]["density_kg_m3"]
    vol = total_mass_kg / rho
    L, Bc, H = b["lwl_m"], b["chine_beam_m"], b["side_height_m"]
    tan_f = (b["beam_m"] - Bc) / 2.0 / H        # pendiente del costado
    Leff = L * b["block_coeff"]
    # vol = Leff·(Bc·T + tan_f·T²)  → cuadrática en T
    a, bb, c = Leff * tan_f, Leff * Bc, -vol
    T = (-bb + math.sqrt(bb * bb - 4 * a * c)) / (2 * a)
    Bwl = Bc + 2 * T * tan_f
    # superficie mojada: fondo + 2 costados (inclinados)
    side_len = T / math.cos(math.atan(tan_f))
    S = L * Bc * b["waterplane_coeff"] + 2 * L * side_len * 0.90
    # área de espejo sumergida (trapecio) con ancho de espejo de diseño
    Bt_bot = min(b["transom_beam_m"], Bc)
    Bt_top = Bt_bot + 2 * T * tan_f
    A_T = 0.5 * (Bt_bot + Bt_top) * T
    freeboard = H - T
    return {
        "volume_m3": vol,
        "draft_m": T,
        "bwl_m": Bwl,
        "wetted_area_m2": S,
        "transom_area_m2": A_T,
        "freeboard_m": freeboard,
        "slenderness_L_over_vol13": L / vol ** (1 / 3),
    }


def hull_speed(inp: dict) -> dict:
    """Velocidad de casco clásica (1.34·√LWL[ft] kn ≡ Fr_L ≈ 0.40)."""
    L = inp["boat"]["lwl_m"]
    v_kn = 1.34 * math.sqrt(L / 0.3048)
    v_ms = v_kn * 0.514444
    return {"v_hull_kn": v_kn, "v_hull_ms": v_ms, "v_hull_kmh": v_ms * 3.6,
            "fr_hull": v_ms / math.sqrt(G * L)}


def resistance(inp: dict, total_mass_kg: float, v_ms, wind_ms: float = 0.0,
               waves: bool = False) -> dict:
    """Resistancia por componentes (banda nominal) para un vector de velocidades [m/s]."""
    v = np.atleast_1d(np.asarray(v_ms, dtype=float))
    w, r, b = inp["water"], inp["resistance"], inp["boat"]
    rho, nu = w["density_kg_m3"], w["kinematic_viscosity_m2_s"]
    hs = hydrostatics(inp, total_mass_kg)
    L = b["lwl_m"]
    W = total_mass_kg * G

    vv = np.maximum(v, 1e-3)
    Re = vv * L / nu
    Cf = 0.075 / (np.log10(Re) - 2.0) ** 2 + r["delta_cf"]
    RF = 0.5 * rho * v**2 * hs["wetted_area_m2"] * Cf * (1.0 + r["form_factor_k"])

    A_T = hs["transom_area_m2"]
    Bw = hs["bwl_m"]
    FnT = vv / np.sqrt(2 * G * A_T / (Bw + Bw * b["waterplane_coeff"]))
    c6 = np.where(FnT < 5.0, 0.2 * (1.0 - 0.2 * FnT), 0.0)
    RTR = 0.5 * rho * v**2 * A_T * c6

    Fr = vv / math.sqrt(G * L)
    RW = W * r["wave_cw"] * Fr**4 / (1.0 + (Fr / r["wave_fr_hump"]) ** 4)

    a = inp["air"]
    Rair = 0.5 * a["density_kg_m3"] * r["air_cd"] * r["air_frontal_area_m2"] * (v + wind_ms) ** 2

    Rhydro = RF + RTR + RW
    if waves:
        Rhydro = Rhydro * (1.0 + inp["operation"]["wave_added_frac"])
    R = Rhydro + Rair
    return {
        "v_ms": v, "Fr_L": Fr, "Re": Re, "FnT": FnT,
        "RF": RF, "RTR": RTR, "RW": RW, "Rair": Rair, "R": R,
        "R_low": R * r["band_low"], "R_high": R * r["band_high"],
        "R_over_W": R / W,
    }


def design_resistance(inp: dict, total_mass_kg: float, v_ms, **kw):
    """Resistencia de la banda de diseño (alta por defecto)."""
    res = resistance(inp, total_mass_kg, v_ms, **kw)
    band = inp["resistance"]["design_band"]
    key = {"high": "R_high", "low": "R_low", "nominal": "R"}[band]
    return res[key], res


def gerr_power_w(inp: dict, total_mass_kg: float, v_ms) -> np.ndarray:
    """Contraste empírico (Gerr, Propeller Handbook): SLR = 10.665/(LB/SHP)^(1/3).
    Devuelve potencia al eje [W]. Válido para desplazamiento/semi-desplazamiento de
    barcos de tamaño normal; aquí solo como orden de magnitud.  [ESTIMADO]"""
    v = np.atleast_1d(np.asarray(v_ms, dtype=float))
    L_ft = inp["boat"]["lwl_m"] / 0.3048
    slr = (v / 0.514444) / math.sqrt(L_ft)
    lb = total_mass_kg / 0.45359237
    shp = lb / (10.665 / np.maximum(slr, 1e-6)) ** 3
    return shp * 745.7
