"""P1-CTL-10 — Palanca del bucket (ARRIBA adelante / ABAJO atrás, −60°), Al 6061-T6 8 mm soldada.

Mango desplazado 20 mm hacia babor (no choca con el del acelerador) con el gatillo P1-CTL-14, que tira de los dos
Bowden de liberación de los émbolos P1-REV-04 en la boquilla: apretar → libera las trabas; soltar → trabas en la
otra posición. Placa lateral soldada en la cara +y del mango (Al 6061 4 mm, ronda 4): lleva el pasador Ø5 del gatillo
(doble apoyo con el mango) y la pestaña de tope de las dos vainas (2 roscas M6 de los reguladores) a popa de la barra
igualadora del gatillo; queda fuera de la caja P1-CTL-02 en todo el recorrido (y ≥ 33). La manivela hacia popa (r = 46, φ 150° → 210°) mete 46 mm la varilla del Mach5 de la
consola en su vaina (= carrera en la boquilla): en la boquilla la varilla sale y baja el bucket.
Muescas del enclavamiento en la cara interior (2: ARRIBA, 3: ABAJO). Gira en el eje con buje POM."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_x, cyl_y, prism_xz  # noqa: E402
from _dir_common import circ, hull  # noqa: E402
import _ctl as U  # noqa: E402

META = dict(
    id="P1-CTL-10", name="palanca_bucket", desc="Palanca del bucket Al 6061 8 mm con manivela del Mach5",
    material="Al 6061-T6", process="torneada", qty=1, frame="bucket", group="ele",
    load_case="100 N en el pomo contra el enclavamiento / tope", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Fresado CNC + escalón soldado",
)
STEP_Z = (100.0, 112.0)
PERCH_Y = (33.0, 37.0)        # placa lateral del gatillo (soldada en la cara +y del mango)
PERCH = [(-8.0, 135.0), (8.0, 135.0), (8.0, 96.0), (-6.0, 70.0), (-20.0, 70.0), (-20.0, 103.0), (-8.0, 109.0)]
STOP_X = (-20.0, -15.0)       # pestaña de tope de las vainas (plano yz), y 33–50, z 70–103
STOP_Y1 = 50.0
TOP_Y = (25.0, 33.0)
TOP_Z = 135.0


def build_local(p):
    y0, y1 = U.Y_BKT
    cx, cz = U.crank_pin(U.CRANK_PHI_UP)
    s = prism_xz(circ(0, 0, U.HUB_R, 48), y0, y1) + box(-8, 8, y0, y1, 0, STEP_Z[1])
    s = s + prism_xz(hull(circ(0, 0, 14.0) + circ(cx, cz, 9.0)), y0, y1)
    s = s + box(-8, 8, y1 - 0.01, TOP_Y[1], STEP_Z[0], STEP_Z[1]) + box(-8, 8, TOP_Y[0], TOP_Y[1], STEP_Z[0], TOP_Z)
    s = s + cyl_y(4.0, y1 - 0.01, y1 + 10.0, x=cx, z=cz)                 # perno de la manivela Ø8 (prensado)
    # placa lateral del gatillo + pestaña de tope de las dos vainas (reguladores M6 a la altura de los cables)
    import importlib.util as _ilu
    _sp = _ilu.spec_from_file_location("ctl14", os.path.join(os.path.dirname(__file__), "P1-CTL-14_gatillo.py"))
    G = _ilu.module_from_spec(_sp)
    _sp.loader.exec_module(G)
    s = s + prism_xz(PERCH, PERCH_Y[0] - 0.01, PERCH_Y[1])
    s = s + box(STOP_X[0], STOP_X[1], PERCH_Y[0], STOP_Y1, PERCH[4][1], PERCH[5][1])
    w = G.wire_pt(0.0)
    yc = (G.BAR_Y[0] + G.BAR_Y[1]) / 2
    for dz in (-G.BAR_H, G.BAR_H):
        s = s - cyl_x(3.25, STOP_X[0] - 1, STOP_X[1] + 1, y=yc, z=w[1] + dz)
    s = s - cyl_y(G.PIV_D / 2 + 0.05, TOP_Y[0] - 1, PERCH_Y[1] + 1, x=G.PIV[0], z=G.PIV[1])   # pasador Ø5 del gatillo
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
            ("separación de los pomos (y) [mm]", (TOP_Y[0] + TOP_Y[1]) / 2 - (U.Y_THR[0] + U.Y_THR[1]) / 2, 35.0, ">="),
            ("placa lateral y tope de vainas por fuera de la caja P1-CTL-02 (y) [mm]", PERCH_Y[0] - _box_y_out(), 2.0, ">="),
            ("tope de las vainas a popa de la barra igualadora en reposo (x) [mm]", _bar_x0() - STOP_X[1], 3.0, ">="),
            ("pestaña de tope: borde alrededor de las roscas M6 (z) [mm]", _stop_edge(), 2.5, ">=")]


def _g():
    import importlib.util as _ilu
    sp = _ilu.spec_from_file_location("ctl14", os.path.join(os.path.dirname(__file__), "P1-CTL-14_gatillo.py"))
    G = _ilu.module_from_spec(sp)
    sp.loader.exec_module(G)
    return G


def _box_y_out():
    import importlib.util as _ilu
    sp = _ilu.spec_from_file_location("ctl02", os.path.join(os.path.dirname(__file__), "P1-CTL-02_caja_acel.py"))
    B = _ilu.module_from_spec(sp)
    sp.loader.exec_module(B)
    return B.Y1 + (B.W_OUT - B.W)


def _bar_x0():
    G = _g()
    return G.wire_pt(0.0)[0] - G.BAR_T / 2


def _stop_edge():
    G = _g()
    zc = G.wire_pt(0.0)[1]
    return min((zc - G.BAR_H - 3.25) - PERCH[4][1], PERCH[5][1] - (zc + G.BAR_H + 3.25))
