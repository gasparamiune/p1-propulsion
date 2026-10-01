"""P1-ELE-04 — Collar fijo con el sensor hall lineal (SS49E/A1324) enfrentado al imán del
puño, alojamiento de 2 resortes de retorno al centro y salida del cable por prensaestopas
M12. Sensor encapsulado en epoxi (estanco)."""
import importlib.util, math, os
from cadlib import *

META = dict(
    id="P1-ELE-04", name="hall_housing", desc="Collar del sensor hall (fijo a la caña)",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="Reacción de resortes, golpes", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Eje vertical (Z).",
)
L_H = 34.0


def build(p):
    ri = (p.tiller_tube_od + 0.3) / 2
    h = cyl_z(ri + 13, 0, L_H) - cyl_z(ri, -1, L_H + 1)
    h = h - box(ri + 2, ri + 11, -7, 7, L_H - 10, L_H + 1)            # bolsillo PCB sensor
    h = h - box(-1.0, 1.0, -ri - 14, -ri + 1, 6, L_H + 1)             # ranura de apriete
    h = h - cyl_x(2.7, -ri - 14, ri + 14, y=-ri - 7, z=L_H / 2)        # M5 de apriete
    h = h - cyl_x(6.2, -ri - 14, -ri - 2, y=0, z=10)                    # prensaestopas M12
    return h


def placements(p, steer=0.0, tilt=0.0):
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("g", os.path.join(here, "P1-ELE-03_throttle_grip.py"))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    from params import loc_unit
    return [loc_unit(p, steer, tilt) * g.tiller_loc(p, 550.0 - 18 - g.L_GRIP - 2 - L_H - 1)]


def checks(p, part):
    return []
