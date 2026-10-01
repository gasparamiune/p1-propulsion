"""P1-STR-01 — Carcasa inferior: encastra el extremo del tubo (45 mm, perno M6 A4 pasante
con vaina aislante que traba también el buje inferior), labio con paso de eje, aleta
superior y brazo que sostiene el protector de hélice por arriba; ranura para el patín."""
from cadlib import *

LH_BOTTOM = 42.0     # profundidad de la carcasa bajo el eje [mm]
TONGUE = 14.0        # alto de la lengüeta del patín [mm]

META = dict(
    id="P1-STR-01", name="lower_housing", desc="Carcasa inferior + aleta/brazo del protector",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="LC5 impacto en patín/protector, LC6 vibración", print_rot=(90, 0, 0), solid_frac=0.95,
    orientation="De canto (w = Z): fuerzas del patín y del protector en el plano de capas.",
)


def build(p):
    vs = -p.e
    u0, u1 = p.u_lh_fwd, p.u_lh_aft
    R = 28.0
    Rb = LH_BOTTOM
    h = box(u0, u1, -R, R, vs - Rb, vs + R)
    rt = (p.tube_od + 0.3) / 2
    h = h - cyl_x(rt, u0 - 1, p.u_tube_bot + 0.2, z=vs)
    h = h - cyl_x(9.0, u0, u1 + 1, z=vs)                                  # paso de eje + agua
    # perno transversal M6 (traba tubo y buje) desplazado 13 mm del eje
    h = h - cyl_y(3.2, -R - 1, R + 1, x=u0 + 15, z=vs + 13)
    # ranura del patín (abajo) + 2 pernos M6
    h = h - box(u0 + 8, u1 - 8, -p.skeg_t / 2 - 0.2, p.skeg_t / 2 + 0.2, vs - Rb - 1, vs - Rb + TONGUE + 0.5)
    for u in (u0 + 18, u1 - 18):
        h = h - cyl_y(3.2, -R - 1, R + 1, x=u, z=vs - Rb + TONGUE / 2)
    # aleta superior + brazo sobre el anillo del protector
    Ro = p.guard_ri + p.guard_t
    fin = box(u0 + 5, u1, -5, 5, vs + R - 1, vs + Ro + 9)
    arm = box(u0 + 5, p.s_prop + p.guard_L / 2, -9, 9, vs + Ro + 0.3, vs + Ro + 9)
    h = h + fin + arm
    # tornillo avellanado M5 desde el interior del anillo + tuerca cautiva en el brazo
    h = h - cyl_z(2.75, vs + Ro - 1, vs + Ro + 10, x=p.s_prop)
    h = h - hex_prism_z(NUT_AF[5] + 0.3, vs + Ro + 4, vs + Ro + 9.1, x=p.s_prop)
    return h


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [("encastre del tubo [mm]", p.u_tube_bot - p.u_lh_fwd, 40.0, ">="),
            ("luz carcasa–cubo de hélice [mm]", (p.s_prop - p.prop_hub_L / 2) - p.u_lh_aft, 4.0, ">=")]
