"""P1-DRV-02 — Portabuje impreso (PETG) para 2 bujes igus iglidur H370SM-1618-20 (×3 portabujes:
arriba, medio, abajo del tubo). Deslizante en el tubo de Al y fijado con un tornillo radial
M5 A4 (Tef-Gel + vaina aislante); 4 ranuras axiales en el exterior dejan circular agua y
arena. Los bujes H370 (comprados, aptos bajo agua según igus, research/R08b) se prensan en
el alojamiento Ø18; el eje Ø16 gira en ellos."""
import math
from cadlib import *

META = dict(id="P1-DRV-02", name="tube_bushing", desc="Portabuje PETG + 2 bujes igus H370 Ø16×Ø18×20 (×3)",
            material="PETG", process="impresa", qty=3, frame="unit",
            load_case="Reacciones radiales del eje (p = F/(d·L) en el portabuje)", print_rot=(0, 90, 0),
            solid_frac=1.0,
            orientation="Eje vertical (de pie): alojamiento del buje redondo y preciso en XY.")

GROOVE_W, GROOVE_D = 4.0, 2.0      # ranuras axiales de lavado


def build(p):
    L = p.bush_len
    od = p.tube_od - 2 * p.tube_wall - 0.1       # deslizante en el tubo
    b = cyl_x(od / 2, -L / 2, L / 2) - cyl_x((p.bush_od + p.press) / 2, -L / 2 - 1, L / 2 + 1)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        r = od / 2 - GROOVE_D / 2
        b = b - box(-L / 2 - 1, L / 2 + 1, -GROOVE_W / 2, GROOVE_W / 2, -GROOVE_D / 2, GROOVE_D / 2).moved(
            _rot_x(a) * _pos(0, 0, r))
    # agujero radial del tornillo de fijación M5 (rosca en el portabuje: inserto/rosca formada)
    b = b - cyl_z(2.1, 0, od / 2 + 1)
    return b


def _rot_x(a):
    from build123d import Rot
    return Rot(math.degrees(a), 0, 0)


def _pos(x, y, z):
    from build123d import Pos
    return Pos(x, y, z)


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos
    from params import loc_unit
    L = loc_unit(p, steer, tilt)
    return [L * Pos(u, 0, -p.e) for u in p.u_bush]


def checks(p, part):
    od = p.tube_od - 2 * p.tube_wall - 0.1
    wall = (od - p.bush_od) / 2 - GROOVE_D
    return [("pared del portabuje bajo la ranura [mm]", wall, 3.0, ">="),
            ("largo ≥ 2 bujes de 20 mm [mm]", p.bush_len, 40.0, ">=")]
