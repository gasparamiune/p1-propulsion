"""P1-STR-01 — Carcasa inferior: encastra el extremo del tubo (45 mm, perno M6 A4 pasante
con vaina aislante que traba también el buje inferior), labio con paso de eje y drenaje,
aleta superior y brazo con MONTURA que abraza el par de orejas superiores del protector
(mismo tornillo tangencial M4); sobre el brazo se atornilla la placa antiventilación PRP-05. Ranura inferior para la lengüeta del patín."""
import importlib.util
import os
from cadlib import *

LH_BOTTOM = 42.0     # = params lh_bottom (profundidad de la carcasa bajo el eje)
TONGUE = 14.0        # = params skeg_tongue

META = dict(
    id="P1-STR-01", name="lower_housing", desc="Carcasa inferior + aleta/brazo/montura del protector",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="LC5 impacto en patín/protector, LC6 vibración", print_rot=(90, 0, 0), solid_frac=0.95,
    orientation="De canto (w = Z): fuerzas del patín y del protector en el plano de capas.",
)


def _lug(p):
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("gg", os.path.join(here, "_guard_geom.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.lug_geom(p)


def build(p):
    vs = -p.e
    u0, u1 = p.u_lh_fwd, p.u_lh_aft
    R = 28.0
    Rb = LH_BOTTOM
    h = box(u0, u1, -R, R, vs - Rb, vs + R)
    rt = (p.tube_od + 0.3) / 2
    h = h - cyl_x(rt, u0 - 1, p.u_tube_bot + 0.2, z=vs)
    h = h - cyl_x(9.0, u0, u1 + 1, z=vs)                                  # paso de eje + agua
    h = h - cyl_y(3.2, -R - 1, R + 1, x=u0 + 15, z=vs + 13)              # perno transversal M6
    h = h - box(u0 + 8, u1 - 8, -p.skeg_t / 2 - 0.2, p.skeg_t / 2 + 0.2, vs - Rb - 1, vs - Rb + TONGUE + 0.5)
    for u in (u0 + 18, u1 - 18):
        h = h - cyl_y(3.2, -R - 1, R + 1, x=u, z=vs - Rb + TONGUE / 2)
    # --- aleta, brazo, montura y placa antiventilación ---
    u_hole, r_hole, r_top, lt, la2, r_prof = _lug(p)
    u_le = p.s_prop - p.guard_L / 2                                       # borde de ataque del aro
    fin_aft = min(u1, u_le - 2.0)
    arm0, arm1 = vs + r_top + 1.5, vs + r_top + 9.5
    fin = box(u0 + 5, fin_aft, -5, 5, vs + R - 1, arm1)
    arm = box(u0 + 5, u_hole + la2 + 3, -9, 9, arm0, arm1)
    cw = 5.0
    cheeks = None
    for sgn in (-1, 1):
        y0, y1 = sorted((sgn * (lt + 0.3), sgn * (lt + 0.3 + cw)))
        c = box(u_hole - la2, u_hole + la2, y0, y1, vs + r_prof + 1.0, arm1)
        cheeks = c if cheeks is None else cheeks + c
    h = h + fin + arm + cheeks
    for u in (u_le - 2.0, u_hole + la2 - 2.0):                           # 2×M4 de la placa antiventilación (PRP-05)
        h = h - cyl_z(2.2, arm0 - 1, arm1 + 1, x=u)
        h = h - hex_prism_z(NUT_AF[4] + 0.3, arm0 - 0.1, arm0 + 3.5, x=u)
    h = h - box(u_hole - la2 - 0.3, u_hole + la2 + 0.3, -lt - 0.3, lt + 0.3, vs + r_prof - 1, arm0 + 0.01)  # hueco de las orejas
    h = h - cyl_y(2.2, -lt - cw - 2, lt + cw + 2, x=u_hole, z=vs + r_hole)                                  # tornillo tangencial M4
    return h


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [("encastre del tubo [mm]", p.u_tube_bot - p.u_lh_fwd, 40.0, ">="),
            ("luz carcasa–cubo de hélice [mm]", (p.s_prop - p.prop_hub_L / 2) - p.u_lh_aft, 4.0, ">=")]
