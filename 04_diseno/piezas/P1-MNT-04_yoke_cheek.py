"""P1-MNT-04 — Mejilla de la horquilla (×2, idénticas). Lleva el perno de basculación
(MNT-08, Ø12) y el retén de bola con resorte (2 posiciones: marcha y basculada)."""
import math
from cadlib import *

META = dict(
    id="P1-MNT-04", name="yoke_cheek", desc="Mejilla de horquilla con perno de basculación y retén",
    material="PETG", process="impresa", qty=2, frame="yoke",
    load_case="LC5 impacto (reacción en el pivote) / LC1–LC2 empuje",
    print_rot=(90, 0, 0), solid_frac=0.9,
    orientation="Plana (espesor = Z): flexión de la mejilla en el plano de capas.",
)


def detent_point(p):
    r = p.inp["mount"]["detent_radius_mm"]
    a = math.radians(-120.0)
    return p.pivot_x + r * math.cos(a), p.pivot_z + r * math.sin(a)


def build(p):
    """Mejilla de babor (y>0); la de estribor es la misma pieza trasladada (simétrica)."""
    z0 = p.disc_z0 + p.disc_t
    px, pz, R = p.pivot_x, p.pivot_z, p.pivot_boss_r
    pts = [(p.swivel_x - 30, z0), (p.swivel_x + 34, z0)]
    pts += arc_pts(px, pz, R, -20, 200, 22)
    pts += [(p.swivel_x - 30, z0 + 40)]
    y0 = p.cheek_y - p.cheek_t / 2
    ch = prism_xz(pts, y0, y0 + p.cheek_t)
    # perno de basculación (ajuste deslizante justo)
    ch = ch - cyl_y((p.tilt_pin_d + 0.1) / 2, y0 - 1, y0 + p.cheek_t + 1, x=px, z=pz)
    # retén: émbolo de bola M12 + tuerca de bloqueo en cara exterior
    dx, dz = detent_point(p)
    ch = ch - cyl_y(6.25, y0 - 1, y0 + p.cheek_t + 1, x=dx, z=dz)
    ch = ch - hex_prism_y(NUT_AF[12] + 0.3, y0 + p.cheek_t - NUT_M[12] - 0.5, y0 + p.cheek_t + 0.1, x=dx, z=dz)
    # pernos M6 desde la base con TUERCA CAUTIVA transversal (arranque por corte de ~2·t·20 mm)
    for x in (p.swivel_x - 18, p.swivel_x + 24):
        ch = ch - cyl_z(3.3, z0 - 1, z0 + 30, x=x, y=p.cheek_y)
        ch = ch - box(x - (NUT_AF[6] + 0.4) / 2, x + (NUT_AF[6] + 0.4) / 2, y0 - 1, y0 + p.cheek_t + 1,
                      z0 + 18, z0 + 18 + NUT_M[6] + 0.6)
    return ch


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos
    from params import loc_yoke
    L = loc_yoke(p, steer)
    return [L, L * Pos(0, -2 * p.cheek_y, 0)]


def checks(p, part):
    return [("luz entre mejillas ≥ ancho de cuna + 2 mm", 2 * (p.cheek_y - p.cheek_t / 2), p.cradle_w + 2, ">=")]
