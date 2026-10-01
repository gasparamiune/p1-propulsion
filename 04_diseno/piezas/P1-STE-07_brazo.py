"""P1-STE-07 — Brazo superior del yugo de dirección, Al 5083 10 mm.

Une el poste (P1-STE-06) con la rótula angular M8 (DIN 71802, comprada) de la biela del cable
Ultraflex M66 (R11 §7). La rótula queda en (X', Y) = (STE_stud_x, STE_post_y): con la biela de
STE_link_L la barra del M66 recorre ±29,6 mm casi simétricos para ±δmax [CALCULADO en checks]."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_z, prism_xy  # noqa: E402
from _dir_common import hull  # noqa: E402

META = dict(
    id="P1-STE-07", name="brazo", desc="Brazo del yugo con rótula M8 (Al 5083 10 mm)",
    material="Al 5083", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Fuerza de la biela del M66 (momento de dirección / brazo)", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="Placa plana; plano en planos_direccion",
)


def ram_positions(p):
    """Posición X' (desde el eje de giro) del extremo de la barra del M66 para δ = −δmax, 0, +δmax."""
    a, b = p.STE_stud_x, p.STE_post_y
    out = []
    for s in (-p.steer_max, 0.0, p.steer_max):
        r = math.radians(s)
        X = a * math.cos(r) - b * math.sin(r)
        Y = a * math.sin(r) + b * math.cos(r)
        dy = Y - p.STE_ram_y
        out.append(X - math.sqrt(p.STE_link_L ** 2 - dy ** 2))
    return out


def build(p):
    Xp = p.X_steer_pivot
    z1 = p.STE_post_z1
    z0 = z1 - p.STE_arm_t
    c = lambda cx, cy, r, n=24: [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    poly = hull(c(Xp + p.STE_post_x, p.STE_post_y, 16) + c(Xp + p.STE_stud_x, p.STE_post_y, 12))
    s = prism_xy(poly, z0, z1)
    s = s - cyl_z(8.25, z0 - 1, z1 + 1, x=Xp + p.STE_post_x, y=p.STE_post_y)
    s = s - cyl_z(p.STE_stud_hole / 2, z0 - 1, z1 + 1, x=Xp + p.STE_stud_x, y=p.STE_post_y)
    return s


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def checks(p, part):
    import params as P
    xs = [part.moved(P.loc_steer(p, s)).bounding_box().max.X for s in (-p.steer_max, 0.0, p.steer_max)]
    rm = ram_positions(p)
    xtr = (p.x_if - p.STE_ram_z * math.sin(math.radians(p.alpha))) / math.cos(math.radians(p.alpha)) - p.X_steer_pivot
    ball_r = 10.0     # [ESTIMADO: rótula DIN 71802 M8, radio de la caja]
    gland = 6.0       # [ESTIMADO: saliente del pasamuros P1-CTL-04]
    asym = abs((rm[2] - rm[1]) - (rm[1] - rm[0]))
    zb = P.jet_to_boat(p, p.X_steer_pivot, p.STE_ram_y, p.STE_ram_z)[2]
    wl = p.sz["hydrostatics"]["draft_m"] * 1000
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("luz al espejo (±δmax) [mm]", -max(xs), 5.0, ">="),
            ("carrera de la barra del M66 [mm]", rm[2] - rm[0], 40.0, ">="),
            ("asimetría babor/estribor de la carrera [mm]", asym, 3.0, "<="),
            ("extremo de barra ↔ espejo + pasamuros en δ extremo [mm]", (min(rm) - ball_r) - (xtr + gland), 2.0, ">="),
            ("rótula sobre la flotación estática (z_bote − calado) [mm]", zb - wl, 30.0, ">=")]
