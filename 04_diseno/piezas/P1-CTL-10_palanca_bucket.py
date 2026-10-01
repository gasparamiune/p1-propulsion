"""P1-CTL-10 — Palanca del bucket (ARRIBA adelante / ABAJO atrás, −60°), Al 6061-T6 8 mm soldada.

Mango desplazado 20 mm hacia babor (no choca con el del acelerador) con gatillo (no modelado) que tira
del Bowden de liberación del émbolo P1-REV-04 en la boquilla: apretar → libera la traba; soltar → traba
en la otra posición. La manivela hacia popa (r = 46, φ 150° → 210°) mete 46 mm la varilla del Mach5 de la
consola en su vaina (= carrera en la boquilla): en la boquilla la varilla sale y baja el bucket.
Muescas del enclavamiento en la cara interior (2: ARRIBA, 3: ABAJO). Gira en el eje con buje POM."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_y, prism_xz  # noqa: E402
from _dir_common import circ, hull  # noqa: E402
import _ctl as U  # noqa: E402

META = dict(
    id="P1-CTL-10", name="palanca_bucket", desc="Palanca del bucket Al 6061 8 mm con manivela del Mach5",
    material="Al 6061-T6", process="torneada", qty=1, frame="bucket", group="ele",
    load_case="100 N en el pomo contra el enclavamiento / tope", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Fresado CNC + escalón soldado",
)
STEP_Z = (100.0, 112.0)
TOP_Y = (25.0, 33.0)
TOP_Z = 135.0


def build_local(p):
    y0, y1 = U.Y_BKT
    cx, cz = U.crank_pin(U.CRANK_PHI_UP)
    s = prism_xz(circ(0, 0, U.HUB_R, 48), y0, y1) + box(-8, 8, y0, y1, 0, STEP_Z[1])
    s = s + prism_xz(hull(circ(0, 0, 14.0) + circ(cx, cz, 9.0)), y0, y1)
    s = s + box(-8, 8, y1 - 0.01, TOP_Y[1], STEP_Z[0], STEP_Z[1]) + box(-8, 8, TOP_Y[0], TOP_Y[1], STEP_Z[0], TOP_Z)
    s = s + cyl_y(4.0, y1 - 0.01, y1 + 10.0, x=cx, z=cz)                 # perno de la manivela Ø8 (prensado)
    s = s - cyl_y(p.CTL_shaft_d / 2 + 0.1, y0 - 1, y1 + 1)
    for k, a in U.NOTCHES_B.items():
        r = p.CTL_ilock_r
        s = s - cyl_y((p.CTL_ilock_d + 0.4) / 2, y0 - 0.01, y0 + p.CTL_ilock_depth,
                      x=r * math.cos(math.radians(a)), z=r * math.sin(math.radians(a)))
    return s


def build(p):
    return U.unit_loc(p) * build_local(p)


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos
    th = -p.CTL_bkt_travel if bucket else 0.0
    x, y, z = p.CTL_axis
    # build() ya está en el BOTE: girar alrededor del eje de palancas
    from build123d import Rot
    return [Pos(x, y, z) * Rot(0, th, 0) * Pos(-x, -y, -z)]


def checks(p, part):
    cu = U.crank_pin(U.CRANK_PHI_UP)
    cd = U.crank_pin(U.CRANK_PHI_UP + p.CTL_bkt_travel)
    import _mach5 as M5
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("carrera de la manivela (vertical) [mm]", abs(cd[1] - cu[1]), abs(M5.dz(p)), "="),
            ("cuerda vertical de la manivela |Δx| [mm]", abs(cd[0] - cu[0]), 0.5, "<="),
            ("escalón del mango sobre la caja con el bucket abajo [mm]",
             STEP_Z[0] * math.cos(math.radians(p.CTL_bkt_travel)) - 8.0 * math.sin(math.radians(p.CTL_bkt_travel)) - 40.0, 2.0, ">="),
            ("separación de los pomos (y) [mm]", (TOP_Y[0] + TOP_Y[1]) / 2 - (U.Y_THR[0] + U.Y_THR[1]) / 2, 35.0, ">=")]
