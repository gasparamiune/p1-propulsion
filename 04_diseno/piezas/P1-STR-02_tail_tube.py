"""P1-STR-02 — Tubo de cola Al 6061-T6 Ø40×3 (comprado, cortado a largo, 2 agujeros Ø6.4
para el perno de la carcasa inferior + 2 de drenaje Ø6)."""
from cadlib import *

META = dict(id="P1-STR-02", name="tail_tube", desc="Tubo de cola Al 6061-T6 Ø40×3",
            material="Al 6061-T6", process="comprada", qty=1, frame="unit",
            load_case="LC5 impacto (flexión), LC6", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    r = p.tube_od / 2
    return cyl_x(r, p.u_tube_top, p.u_tube_bot, z=-p.e) - cyl_x(r - p.tube_wall, p.u_tube_top - 1, p.u_tube_bot + 1, z=-p.e)


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [("largo del tubo", p.u_tube_bot - p.u_tube_top, p.layout["tube_length_mm"], "≈")]
