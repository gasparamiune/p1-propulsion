"""_drv_geom.py — utilidades del grupo TREN Y ELECTRÓNICA (P1-DRV/MOT/ELE).

Marco JET: X a popa a lo largo del eje; estación S (hacia proa desde la cara del impulsor) = −X.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cadlib import cyl_x  # noqa: E402


def cyl_s(r, s0, s1, y=0.0, z=0.0):
    """Cilindro coaxial (marco JET) entre las estaciones s0 < s1 (hacia proa)."""
    return cyl_x(r, -s1, -s0, y=y, z=z)


def tube_s(ro, ri, s0, s1):
    return cyl_s(ro, s0, s1) - cyl_s(ri, s0 - 1, s1 + 1)


def stepped(segs):
    """Sólido de revolución escalonado: segs = [(s0, s1, d), ...] (unión de cilindros)."""
    out = None
    for s0, s1, dd in segs:
        c = cyl_s(dd / 2, s0, s1)
        out = c if out is None else out + c
    return out


def polar_yz(r, ang_deg):
    """Punto (Y, Z) del marco JET a radio r y ángulo (desde +Y hacia +Z)."""
    a = math.radians(ang_deg)
    return r * math.cos(a), r * math.sin(a)


def x_boat(p, S):
    """x del BOTE del punto del eje en la estación S."""
    return p.x_if + S * math.cos(math.radians(p.alpha))


def z_axis(p, S):
    """z del BOTE del eje en la estación S."""
    return p.z_if + S * math.sin(math.radians(p.alpha))


def S_of_x(p, x):
    return (x - p.x_if) / math.cos(math.radians(p.alpha))


def n_crit_rpm(p, m_imp_kg=None):
    """Primera velocidad crítica de flexión del eje (Dunkerley) [CALCULADO: R09 §5.1].

    • Con buje de agua en el estator (p.drv_bush): tramo empotrado (par en O) – apoyado (buje).
      Eje propio: ω = (β·L)²/L²·√(EI/μ), βL = 3,927 (empotrado–apoyado) [ESTIMADO: viga de Euler-
      Bernoulli]; impulsor: masa puntual en viga empotrada–apoyada (k por fórmula de flecha).
    • Sin buje: voladizo desde el par en O; eje: 1,875² (R09 §5.1); impulsor: k = 3EI/a³.
    Devuelve (n_crit_rpm, dict de datos)."""
    E = p.inp["shaft"]["e_gpa"] * 1e9
    rho = p.inp["shaft"]["density_kg_m3"]
    dsh = p.shaft_d / 1000
    I = math.pi * dsh ** 4 / 64
    mu = rho * math.pi * dsh ** 2 / 4
    EI = E * I
    m = m_imp_kg if m_imp_kg is not None else p.drv_imp_m_kg
    X_imp_cg = p.X_imp1 / 2                                       # CG del impulsor (marco JET)
    S_fix = p.drv_S_brgA + 7.0                                    # centro de presión aprox. del aro de popa
    if p.drv_bush:
        X_b = (p.drv_bush[0] + p.drv_bush[1]) / 2
        L = (S_fix + X_b) / 1000
        b = (X_b - X_imp_cg) / 1000                               # impulsor → buje
        a = L - b                                                 # empotramiento → impulsor
        w_sh = 3.927 ** 2 / L ** 2 * math.sqrt(EI / mu)
        # flecha de viga empotrada (x=0) – apoyada (x=L) con carga P en x=a:
        # y(a) = P a³ b² (3L + b) / (12 E I L³)
        k = 12 * EI * L ** 3 / (a ** 3 * b ** 2 * (3 * L + b))
        model = "empotrado (par 7204 en O) – apoyado (buje de agua del estator)"
    else:
        a = (S_fix + X_imp_cg) / 1000
        L = a
        w_sh = 1.875 ** 2 / L ** 2 * math.sqrt(EI / mu)
        k = 3 * EI / a ** 3
        model = "voladizo desde el par 7204 (sin apoyo a popa)"
    w_imp = math.sqrt(k / m)
    w = 1 / math.sqrt(1 / w_sh ** 2 + 1 / w_imp ** 2)
    n = w * 60 / (2 * math.pi)
    return n, {"model": model, "L_m": L, "a_m": a, "m_imp_kg": m,
               "n_shaft_rpm": w_sh * 30 / math.pi, "n_imp_rpm": w_imp * 30 / math.pi}
