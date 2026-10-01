"""P1-MNT-06 — Tapa de la cuna: completa la abrazadera del tubo Ø40 (4×M6 a insertos)."""
from cadlib import *

META = dict(
    id="P1-MNT-06", name="cradle_cap", desc="Tapa inferior de la cuna (abrazadera del tubo)",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="LC5 impacto (flexión del tubo) / tope de marcha",
    print_rot=(0, 0, 0), solid_frac=0.9,
    orientation="Cara inferior sobre la cama, media caña hacia arriba (sin soportes).",
)


def build(p):
    W = p.cradle_w / 2
    vs = -p.e
    cap = box(5.0, p.cradle_u1, -W, W, p.cradle_vbot, vs - 0.25)
    cap = cap - cyl_x((p.tube_od + 0.3) / 2, 4, p.cradle_u1 + 1, z=vs)
    for u in (20.0, 80.0):
        for w in (-29.0, 29.0):
            cap = cap - cyl_z(3.2, p.cradle_vbot - 1, vs + 1, x=u, y=w)
            cap = cap - cyl_z(5.6, p.cradle_vbot - 1, p.cradle_vbot + 6.0, x=u, y=w)
    return cap


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [("espesor bajo el tubo [mm]", (-p.e - (p.tube_od + 0.3) / 2) - p.cradle_vbot, 8.0, ">=")]
