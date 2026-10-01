"""P1-MNT-03 — Base de la horquilla (plato giratorio de dirección).

Marco: HORQUILLA (= BOTE con ψ=0). Gira sobre el plano superior de MNT-01 con una
arandela UHMW/PTFE intermedia, alrededor del perno de dirección (MNT-07). Recibe las dos
mejillas (MNT-04, 2×M6 c/u a tuercas cautivas) y el tornillo de trimado/tope de marcha (M8 A4).
"""
import math
from cadlib import *

META = dict(
    id="P1-MNT-03", name="yoke_base", desc="Base de horquilla / plato de dirección",
    material="PETG", process="impresa", qty=1, frame="yoke",
    load_case="LC5 impacto / LC1 empuje (momento de vuelco sobre el perno)",
    print_rot=(0, 0, 0), solid_frac=0.9,
    orientation="Plana: momentos de vuelco en el plano de capas.",
)


def stop_point(p):
    """Punto de apoyo del tope de marcha (cara inferior de la tapa de cuna) en marco BOTE."""
    th = math.radians(p.theta)
    u, v = 30.0, p.cradle_vbot
    x = p.pivot_x + u * math.cos(th) + v * math.sin(th)
    z = p.pivot_z - u * math.sin(th) + v * math.cos(th)
    return x, z


def build(p):
    z0, z1 = p.disc_z0, p.disc_z0 + p.disc_t
    x0, x1 = p.swivel_x - 32, p.swivel_x + 43        # recortada adelante: despeje del cubrecorrea al bascular
    yw = p.cheek_y + p.cheek_t / 2 + 3
    base = box(x0, x1, -yw, yw, z0, z1)
    base = base - cyl_z((p.swivel_pin_d + 0.4) / 2, z0 - 1, z1 + 1, x=p.swivel_x)
    # pernos de mejilla M6 (cabeza abajo, avellanado)
    for y in (-p.cheek_y, p.cheek_y):
        for x in (p.swivel_x - 18, p.swivel_x + 24):
            base = base - cyl_z(3.2, z0 - 1, z1 + 1, x=x, y=y)
            base = base - cyl_z(5.6, z0 - 1, z0 + 6.5, x=x, y=y)
    # tornillo de trimado M8 (tuerca cautiva desde abajo)
    xs, zs = stop_point(p)
    xs = min(xs, x1 - 8)
    base = base - cyl_z(4.2, z0 - 1, z1 + 1, x=xs, y=0)
    base = base - hex_prism_z(NUT_AF[8] + 0.3, z0 - 0.1, z0 + NUT_M[8] + 0.5, x=xs, y=0)
    return base


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_yoke
    return [loc_yoke(p, steer)]


def checks(p, part):
    xs, zs = stop_point(p)
    return [("altura del tope de marcha sobre la base [mm] (largo libre del tornillo M8)",
             zs - (p.disc_z0 + p.disc_t), 2.0, ">=")]
