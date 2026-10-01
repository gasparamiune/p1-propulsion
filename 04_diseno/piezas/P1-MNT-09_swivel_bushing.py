"""P1-MNT-09 — Buje de dirección de POM (torneado) Ø16/Ø24 en MNT-01."""
from cadlib import *

META = dict(id="P1-MNT-09", name="swivel_bushing", desc="Buje POM Ø16×Ø24 (dirección)",
            material="POM-C", process="torneada", qty=1, frame="boat",
            load_case="Apoyo del perno de dirección", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    b = cyl_z(p.swivel_bush_od / 2, p.boss_bot_z, p.shelf_top_z, x=p.swivel_x)
    return b - cyl_z((p.swivel_pin_d + 0.2) / 2, p.boss_bot_z - 1, p.shelf_top_z + 1, x=p.swivel_x)


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    return []
