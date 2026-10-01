"""P1-DRV-04 — Motor BLDC outrunner (comprado). Envolvente: carcasa + eje."""
from cadlib import *

META = dict(id="P1-DRV-04", name="motor", desc="Motor BLDC outrunner (ver BOM)",
            material="—", process="comprada", qty=1, frame="unit",
            load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    u0 = p.plate_u_aft + 0.2
    m = cyl_x(p.motor_d / 2, u0, u0 + p.motor_l, z=p.motor_v)
    m = m + cyl_x(p.motor_shaft_d / 2, p.layout["u_pulley_c"] - p.pulley_w / 2 - 1, u0, z=p.motor_v)
    return m


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return []
