"""P1-DRV-07 — Rodamiento 6002-2RS inoxidable (×2, comprado)."""
from cadlib import *

META = dict(id="P1-DRV-07", name="bearing", desc="Rodamiento 6002-2RS inox 15×32×9 (×2)",
            material="AISI 440C", process="comprada", qty=2, frame="unit",
            load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    B = p.brg_B
    return cyl_x(p.brg_D / 2 - 0.02, -B / 2, B / 2) - cyl_x(p.brg_d / 2 + 0.02, -B, B)


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos
    from params import loc_unit
    L = loc_unit(p, steer, tilt)
    lay = p.layout
    return [L * Pos(lay["u_brgA"], 0, -p.e), L * Pos(lay["u_brgB"], 0, -p.e)]


def checks(p, part):
    return []
