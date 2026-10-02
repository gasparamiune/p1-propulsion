"""P1-CTL-13 — Varilla del Mach5 en la consola con rótula hembra M6 (comprada con el cable).

Vertical (la manivela barre una cuerda vertical): baja CRANK_R al bajar el bucket. Placements según el
estado del bucket."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_y, cyl_z  # noqa: E402
import _ctl as U  # noqa: E402

META = dict(
    id="P1-CTL-13", name="varilla_consola", desc="Varilla Ø6,4 + rótula M6 del Mach5 en la consola (comprada)",
    material="AISI 316", process="comprada", qty=1, frame="bucket", group="ele",
    load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—", mass_g=40.0,   # [ESTIMADO]
)


def build_local(p):
    cx, cz = U.crank_pin(U.CRANK_PHI_UP)
    y0 = U.Y_BKT[1] + 0.5
    eye = cyl_y(9.0, y0, y0 + 8.0, x=cx, z=cz) - cyl_y(4.1, y0 - 1, y0 + 9, x=cx, z=cz)
    rod = cyl_z(3.2, U.SLEEVE_TOP_Z - 60.0, cz - 8.0, x=cx, y=U.ROD_Y)
    return eye + rod


def build(p):
    return U.unit_loc(p) * build_local(p)


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos
    up = U.crank_pin(U.CRANK_PHI_UP)
    dn = U.crank_pin(U.CRANK_PHI_UP + p.CTL_bkt_travel)
    return [Pos(0, 0, (dn[1] - up[1]) if bucket else 0.0)]


def checks(p, part):
    up = U.crank_pin(U.CRANK_PHI_UP)
    dn = U.crank_pin(U.CRANK_PHI_UP + p.CTL_bkt_travel)
    bot = U.SLEEVE_TOP_Z - 60.0
    bots = (bot, bot + (dn[1] - up[1]))
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("varilla dentro de la vaina (mínimo) [mm]", U.SLEEVE_TOP_Z - max(bots), 10.0, ">="),
            ("varilla expuesta mínima [mm]", (min(up[1], dn[1]) - 9.0) - U.SLEEVE_TOP_Z, 5.0, ">=")]
