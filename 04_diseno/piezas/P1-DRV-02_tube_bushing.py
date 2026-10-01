"""P1-DRV-02 — Buje de agua de POM-C (torneado) Ø16.3/Ø34 × 40 (×3: arriba, medio, abajo).
Lubricado por agua; ranuras longitudinales para flujo/arena."""
from cadlib import *

META = dict(id="P1-DRV-02", name="tube_bushing", desc="Buje POM Ø16.3×Ø34×40 (×3)",
            material="POM-C", process="torneada", qty=3, frame="unit",
            load_case="Reacciones radiales del eje", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    L = p.bush_len
    od = p.tube_od - 2 * p.tube_wall - 0.1       # deslizante en el tubo; se fija con pasador/epoxi
    b = cyl_x(od / 2, -L / 2, L / 2) - cyl_x((p.shaft_d + 0.3) / 2, -L / 2 - 1, L / 2 + 1)
    return b


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos
    from params import loc_unit
    L = loc_unit(p, steer, tilt)
    return [L * Pos(u, 0, -p.e) for u in p.u_bush]


def checks(p, part):
    return []
