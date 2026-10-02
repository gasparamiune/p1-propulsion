"""Casco del jet boat: masas, hidrostática, estabilidad inicial, capacidad y cebado de la bomba.

Sección transversal (vista trasera del plano de Jorge, R10b §4.3): fondo con astilla muerta β
y ancho de fondo b_b hasta el pantoque (a z_ch), costado abierto hasta la manga B en la borda
(a z_g). Longitudinalmente se usa un coeficiente de bloque y de flotación.

    ∇ = m/ρ ;  ∇ = C_b·L·A_sec(T)      → T por bisección
    KB ≈ T·(1 − ⅓·…) (sección real, centroide numérico) ;  BM = C_I·L·B_wl³/∇
    GM = KB + BM − KG                   (estabilidad inicial, ángulo chico)
    Capacidad 33 CFR 183.33 (motor interior, referencia):
        W = máx[ Δmax/5 − m_casco/5 − 4·m_máquinas/5 ;  (Δmax − m_casco)/7 ]
"""
from __future__ import annotations

import math

import numpy as np

G = 9.81


# ----------------------------------------------------------------------------- masas
def mass_items(inp: dict, sel: dict) -> list[dict]:
    """Lista de masas con posición (x desde el espejo hacia proa, z desde la quilla).
    `sel` aporta las masas que dependen de la selección (motor, batería, jet)."""
    out = []
    for k, it in inp["masses"]["items"].items():
        m = it["kg"]
        if isinstance(m, str) and m.startswith("sel:"):
            m = sel[m[4:]]
        elif isinstance(m, str) and m.startswith("inp:"):          # referencia a otra entrada (una sola fuente)
            m = inp
            for kk in it["kg"][4:].split("."):
                m = m[kk]
        out.append({"id": k, "desc": it["desc"], "kg": float(m), "x_m": it["x_m"], "z_m": it["z_m"],
                    "machinery": bool(it.get("machinery", False)), "tag": it.get("tag", "")})
    return out


def mass_summary(items: list[dict]) -> dict:
    m = sum(i["kg"] for i in items)
    lcg = sum(i["kg"] * i["x_m"] for i in items) / m
    vcg = sum(i["kg"] * i["z_m"] for i in items) / m
    return {"total_kg": m, "lcg_m": lcg, "vcg_m": vcg,
            "machinery_kg": sum(i["kg"] for i in items if i["machinery"]),
            "items": items}


# ----------------------------------------------------------------------------- sección
def _half_width(z: float, h: dict) -> float:
    """Semi-manga a la altura z sobre la quilla."""
    bb, beta, zch, B, zg = h["bottom_beam_m"], math.radians(h["deadrise_deg"]), h["chine_height_m"], h["beam_m"], h["gunwale_height_m"]
    z_keel_to_chine_edge = 0.5 * bb * math.tan(beta)        # el fondo en V sube hasta el pantoque
    if z <= z_keel_to_chine_edge:
        return z / math.tan(beta) if beta > 1e-6 else 0.5 * bb
    if z <= zch:
        bch = h.get("chine_beam_m", bb)
        f = (z - z_keel_to_chine_edge) / max(zch - z_keel_to_chine_edge, 1e-9)
        return 0.5 * (bb + f * (bch - bb))
    bch = h.get("chine_beam_m", bb)
    f = min((z - zch) / (zg - zch), 1.0)
    return 0.5 * (bch + f * (B - bch))


def section(h: dict, T: float, n: int = 120) -> dict:
    zs = np.linspace(0.0, T, n)
    hw = np.array([_half_width(z, h) for z in zs])
    A = np.trapz(2 * hw, zs)
    zc = np.trapz(2 * hw * zs, zs) / A if A > 0 else 0.0
    return {"A": A, "zc": zc, "Bwl": 2 * hw[-1]}


def hydrostatics(inp: dict, mass_kg: float, vcg_m: float) -> dict:
    h = inp["boat"]
    rho = inp["water"]["density_kg_m3"]
    vol = mass_kg / rho
    L, Cb = h["lwl_m"], h["block_coeff"]
    lo, hi = 1e-4, h["gunwale_height_m"]
    for _ in range(60):
        T = 0.5 * (lo + hi)
        if Cb * L * section(h, T)["A"] < vol:
            lo = T
        else:
            hi = T
    s = section(h, T)
    BM = h["waterplane_inertia_coeff"] * L * s["Bwl"] ** 3 / vol
    KB = s["zc"]
    GM = KB + BM - vcg_m
    # desplazamiento máximo con el agua al borde del espejo (referencia de capacidad)
    T_max = h["transom_height_m"]
    disp_max = rho * Cb * L * section(h, T_max)["A"]
    return {"volume_m3": vol, "draft_m": T, "bwl_m": s["Bwl"], "KB_m": KB, "BM_m": BM,
            "KG_m": vcg_m, "GM_m": GM, "freeboard_transom_m": h["transom_height_m"] - T,
            "disp_max_kg": disp_max}


def capacity_uscg(inp: dict, disp_max_kg: float, machinery_kg: float) -> dict:
    """33 CFR 183.33 (motor interior). Referencia, no obligatoria en DK (R10b §4.3)."""
    hull = inp["boat"]["hull_mass_kg"]
    W1 = disp_max_kg / 5 - hull / 5 - 4 * machinery_kg / 5
    W2 = (disp_max_kg - hull) / 7
    return {"W1_kg": W1, "W2_kg": W2, "persons_gear_kg": max(W1, W2)}


def heel_for_offset(mass_kg: float, GM: float, m_offset_kg: float, d_m: float) -> float:
    """Escora [°] por desplazar m_offset una distancia d (lineal, ángulo chico)."""
    if GM <= 0:
        return math.inf
    return math.degrees(math.atan(m_offset_kg * d_m / (mass_kg * GM)))
