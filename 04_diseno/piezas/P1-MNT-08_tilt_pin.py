"""P1-MNT-08 — Perno de basculación Ø12 (AISI 316, torneado) con ranuras para anillos
de retención DIN 471 en ambos extremos."""
from cadlib import *

META = dict(id="P1-MNT-08", name="tilt_pin", desc="Perno de basculación Ø12 (316 torneado, 2 ranuras DIN 471)",
            material="AISI 316", process="torneada", qty=1, frame="yoke",
            load_case="LC5/LC1 corte doble", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    L = 2 * (p.cheek_y + p.cheek_t / 2) + 8
    return cyl_y(p.tilt_pin_d / 2, -L / 2, L / 2, x=p.pivot_x, z=p.pivot_z)


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_yoke
    return [loc_yoke(p, steer)]


def checks(p, part):
    return []
