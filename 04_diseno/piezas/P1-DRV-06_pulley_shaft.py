"""P1-DRV-06 — Polea HTD-5M del eje (comprada Dold, aluminio, re-mandrinada a Ø15 H7 en el torno,
2 prisioneros a 90° sobre plano del eje + fijador de retención metal-metal)."""
from cadlib import *

META = dict(id="P1-DRV-06", name="pulley_shaft", desc="Polea HTD-5M eje (aluminio, re-mandrinada Ø15 H7)",
            material="Al", process="comprada", qty=1, frame="unit",
            load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    c, w = p.layout["u_pulley_c"], p.pulley_w
    return cyl_x(p.pd_shaft / 2 + 3, c - w / 2, c + w / 2, z=-p.e) - cyl_x(p.shaft_jd / 2 + 0.01, c - w, c + w, z=-p.e)


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return []
