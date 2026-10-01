"""P1-DRV-05 — Polea HTD-5M del motor (comprada, aluminio, bore 8 mm)."""
from cadlib import *

META = dict(id="P1-DRV-05", name="pulley_motor", desc="Polea HTD-5M motor (aluminio, bore 8)",
            material="Al", process="comprada", qty=1, frame="unit",
            load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    c, w = p.layout["u_pulley_c"], p.pulley_w
    return cyl_x(p.pd_motor / 2 + 3, c - w / 2, c + w / 2, z=p.motor_v) - cyl_x(p.motor_shaft_d / 2 + 0.05, c - w, c + w, z=p.motor_v)


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return []
