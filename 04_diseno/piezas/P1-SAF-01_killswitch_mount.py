"""P1-SAF-01 — Soporte del interruptor de hombre al agua (kill switch marino con cordón)
en la caña, junto al puño. Collar de apriete + placa con agujero de panel Ø22."""
import importlib.util, math, os
from cadlib import *

META = dict(
    id="P1-SAF-01", name="killswitch_mount", desc="Soporte de kill switch con cordón (en la caña)",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="Tirón del cordón (~100 N) al caer al agua", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Eje del collar = Z; tirón del cordón en el plano de capas de la placa.",
)
L_K = 30.0


def build(p):
    ri = (p.tiller_tube_od + 0.3) / 2
    c = cyl_z(ri + 7, 0, L_K) - cyl_z(ri, -1, L_K + 1)
    plate = box(ri + 2, ri + 42, -18, 18, 0, 7)
    c = c + plate - cyl_z(11.1, -1, 8, x=ri + 22)
    c = c - box(-1.0, 1.0, -ri - 8, -ri + 1, -1, L_K + 1)
    c = c - cyl_x(2.7, -ri - 8, ri + 8, y=-ri - 4, z=L_K / 2)
    return c


def placements(p, steer=0.0, tilt=0.0):
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("g", os.path.join(here, "P1-ELE-03_throttle_grip.py"))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    from params import loc_unit
    return [loc_unit(p, steer, tilt) * g.tiller_loc(p, 550.0 - 18 - g.L_GRIP - 2 - 34.0 - 2 - L_K - 2)]


def checks(p, part):
    return [("agujero de panel Ø22 (+0.2)", 22.2, 22.0, ">=")]
