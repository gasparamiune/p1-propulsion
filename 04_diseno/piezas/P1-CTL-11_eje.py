"""P1-CTL-11 — Eje de palancas Ø12 h7 con cabeza Ø18 portaimán, AISI 316 torneado.

Gira con la palanca del acelerador (pasador Ø4 A4); el imán NdFeB Ø10×3 diametral (README de
electrónica §4) va pegado en la cabeza, frente al sensor A1324 alojado en la pared de la caja PETG
(entrehierro CTL_hall_gap). Anillo E DIN 6799 del lado de la palanca del bucket."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_y  # noqa: E402
import _ctl as U  # noqa: E402

META = dict(
    id="P1-CTL-11", name="eje_palancas", desc="Eje Ø12 con cabeza portaimán (316)",
    material="AISI 316", process="torneada", qty=1, frame="boat", group="ele",
    load_case="Flexión y torsión: 100 N en el pomo del acelerador", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="—", allow={"P1-CTL-09": 20.0},
)


def build_local(p):
    h0, h1 = U.Y_HEAD
    d, t = p.CTL_magnet
    s = cyl_y(p.CTL_shaft_d / 2, h1 - 0.01, U.Y_BKT[1] + 3.0) + cyl_y(9.0, h0, h1)
    return s - cyl_y(d / 2 + 0.1, h0 - 1, h0 + t)


def build(p):
    return U.unit_loc(p) * build_local(p)


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    d, t = p.CTL_magnet
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("pared del alojamiento del imán [mm]", 9.0 - (d / 2 + 0.1), 3.0, ">="),
            ("fondo del alojamiento del imán [mm]", (U.Y_HEAD[1] - U.Y_HEAD[0]) - t, 2.0, ">=")]
