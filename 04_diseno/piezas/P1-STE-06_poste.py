"""P1-STE-06 — Poste del yugo de dirección, Al 6061-T6 torneado: brida Ø44 × 8 (4 × M8 A4 a la brida
del yugo P1-STE-04, centrador Ø16), caña Ø22 y extremo M16 con doble plano 17 para el brazo P1-STE-07.

Desplazado a babor del eje de giro para quedar fuera del barrido del bucket: la rótula del cable de
dirección queda por ENCIMA de la flotación estática y con lugar para la biela detrás del espejo."""
from cadlib import cyl_z

META = dict(
    id="P1-STE-06", name="poste", desc="Poste del yugo Ø22 con brida Ø44 y M16 (6061-T6)",
    material="Al 6061-T6", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Flexión + torsión por la fuerza de la biela del M66", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="—",
)


def geom(p):
    zb = p.STE_zc_top + p.STE_yoke_t          # apoyo sobre la brida
    zt = p.STE_post_z1 - p.STE_arm_t          # apoyo del brazo
    return zb, zt


def build(p):
    zb, zt = geom(p)
    x, y = p.X_steer_pivot + p.STE_post_x, p.STE_post_y
    s = cyl_z(22.0, zb, zb + 8.0, x=x, y=y) + cyl_z(p.STE_post_d / 2, zb + 7.99, zt, x=x, y=y)
    s = s + cyl_z(7.9, zb - 4.0, zb + 0.01, x=x, y=y)                      # centrador Ø16 (modelado Ø15,8)
    import math
    for k in range(4):
        a = math.radians(45 + 90 * k)
        s = s - cyl_z(4.5, zb - 1, zb + 9, x=x + 16 * math.cos(a), y=y + 16 * math.sin(a))
    s = s + cyl_z(7.9, zt - 0.01, zt + p.STE_arm_t + 10, x=x, y=y)         # M16 superior
    return s


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def checks(p, part):
    import params as P
    xs = [part.moved(P.loc_steer(p, s)).bounding_box().max.X for s in (-p.steer_max, 0.0, p.steer_max)]
    zb, zt = geom(p)
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("luz al espejo (±δmax) [mm]", -max(xs), 5.0, ">="),
            ("largo libre del poste [mm]", zt - zb, 100.0, ">=")]
