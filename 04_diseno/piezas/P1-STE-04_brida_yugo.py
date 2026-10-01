"""P1-STE-04 — Brida del yugo de dirección, Al 5083 20 mm (corte por agua/láser + taladrado).

Apoya sobre la torre de la boquilla (detrás del extremo de la oreja de la bomba) y lleva el par de
dirección del poste (P1-STE-06) al cuerpo con 4 × M8 A4 (Tef-Gel). 20 mm: el momento del poste
entra en la brida como torsión (ver structural_direccion). Cruza el plano de los brazos del bucket por delante del cuerno (X' 16–30, fuera de su barrido) y
termina en el poste a (X', Y) = (STE_post_x, STE_post_y), fuera del barrido del bucket (|Y| > 63,8)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_z, prism_xy  # noqa: E402
from _dir_common import hull  # noqa: E402

META = dict(
    id="P1-STE-04", name="brida_yugo", desc="Brida del yugo de dirección (Al 5083 20 mm)",
    material="Al 5083", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Par de dirección + flexión del poste (biela M66)", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Placa plana; plano en planos_direccion",
)


def outline_parts(p):
    import math
    px, py = p.STE_post_x, p.STE_post_y
    c = lambda cx, cy, r, n=24: [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    x0, x1 = p.STE_riser_x
    ry = p.STE_riser_y
    root = [(x0, -ry), (x1, -ry), (x1, ry), (x0, ry)]
    # banda X' 16–30 (delante de la oreja/refuerzo del bucket, X' ≥ 34) hasta el poste
    band = [(16.0, -ry + 0.5), (30.0, -ry + 0.5), (30.0, py + 10.0), (16.0, py + 10.0)]
    end = hull(c(px, py, 13) + [(16.0, py + 10.0), (30.0, py + 10.0)])
    return root, band, end


def build(p):
    Xp = p.X_steer_pivot
    z0 = p.STE_zc_top
    z1 = z0 + p.STE_yoke_t
    s = None
    for poly in outline_parts(p):
        q = prism_xy([(Xp + u, v) for u, v in poly], z0, z1)
        s = q if s is None else s + q
    for (xx, yy) in p.STE_riser_bolts:
        s = s - cyl_z(4.5, z0 - 1, z1 + 1, x=Xp + xx, y=yy)                 # M8 pasante a la torre
    s = s - cyl_z(8.25, z0 - 1, z1 + 1, x=Xp + p.STE_post_x, y=p.STE_post_y)   # M16 del poste
    return s


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def checks(p, part):
    import math
    import params as P
    xs = []
    for s in (-p.steer_max, 0.0, p.steer_max):
        xs.append(part.moved(P.loc_steer(p, s)).bounding_box().max.X)
    # borde del círculo de la brida del poste vs cabeza del perno del bucket (X', |Y|)
    head_x0 = p.X_bucket_pivot - p.X_steer_pivot - p.REV_head_d / 2
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("luz al espejo (−x_bote máx. en ±δmax) [mm]", -max(xs), 5.0, ">="),
            ("banda ↔ refuerzo del pivote del bucket (X') [mm]", (p.X_bucket_pivot - p.X_steer_pivot - p.REV_boss_r) - 30.0, 3.0, ">="),
            ("brida del poste fuera de la cabeza del perno del bucket (|Y|) [mm]",
             abs(p.STE_post_y) - 13 - (p.REV_y_in + 2 * p.REV_t + 0.3 + p.REV_head_t), 1.0, ">=")]
