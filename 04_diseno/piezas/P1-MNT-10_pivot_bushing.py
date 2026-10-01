"""P1-MNT-10 — Buje de basculación de POM (torneado) Ø12/Ø20, a lo ancho de la cuna."""
from cadlib import *

META = dict(id="P1-MNT-10", name="pivot_bushing", desc="Buje POM Ø12×Ø20 (basculación)",
            material="POM-C", process="torneada", qty=1, frame="unit",
            load_case="Apoyo del perno de basculación", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    W = p.cradle_w / 2
    return cyl_y(10.0, -W, W) - cyl_y((p.tilt_pin_d + 0.25) / 2, -W - 1, W + 1)


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return []
