"""P1-CTL-09 — Palanca del acelerador, Al 6061-T6 8 mm (mecanizada), pomo comprado M8.

0 % en el centro con retorno por 2 resortes de torsión inox (comprados, centrado), avance hasta
+CTL_thr_fwd y reversa hasta −CTL_thr_rev (el firmware escala la reversa a reverse_limit = 50 %,
README de electrónica §5.3). Clavada al eje P1-CTL-11 (pasador Ø4 A4). En la cara interior: ranuras
del enclavamiento (2: reversa, 3: avance), 3 mm de profundidad con chaflán."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_y, prism_xz  # noqa: E402
from _dir_common import circ  # noqa: E402
import _ctl as U  # noqa: E402

META = dict(
    id="P1-CTL-09", name="palanca_acel", desc="Palanca del acelerador Al 6061 8 mm",
    material="Al 6061-T6", process="torneada", qty=1, frame="boat", group="ele",
    load_case="100 N en el pomo (150 mm) [SUPUESTO]", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Fresado CNC de placa",
)
BAR_W = 16.0


def arc_poly(r, a0, a1, w, n=16):
    ro, ri = r + w / 2, r - w / 2
    pts = [(ro * math.cos(math.radians(a0 + (a1 - a0) * i / n)), ro * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(ri * math.cos(math.radians(a1 - (a1 - a0) * i / n)), ri * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return pts


def groove(p, y_face, depth, a0, a1, sign):
    w = p.CTL_ilock_d + 0.4
    y0, y1 = (y_face - depth, y_face + 0.01) if sign < 0 else (y_face - 0.01, y_face + depth)
    g = prism_xz(arc_poly(p.CTL_ilock_r, a0, a1, w), y0, y1)
    for a in (a0, a1):
        g = g + cyl_y(w / 2, y0, y1, x=p.CTL_ilock_r * math.cos(math.radians(a)), z=p.CTL_ilock_r * math.sin(math.radians(a)))
    return g


def build_local(p):
    y0, y1 = U.Y_THR
    L = p.CTL_lever_L
    s = prism_xz(circ(0, 0, U.HUB_R, 48), y0, y1) + box(-BAR_W / 2, BAR_W / 2, y0, y1, 0, L)
    s = s + prism_xz(circ(0, L, 11.0), y0, y1)
    s = s - cyl_y(p.CTL_shaft_d / 2, y0 - 1, y1 + 1) - cyl_y(4.25, y0 - 1, y1 + 1, x=0, z=L)   # eje; M8 del pomo
    for k, (a0, a1) in U.GROOVES_T.items():
        s = s - groove(p, y1, p.CTL_ilock_depth, a0, a1, -1)
    return s


def build(p):
    return U.unit_loc(p) * build_local(p)


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    hub_edge = U.HUB_R - (p.CTL_ilock_r + (p.CTL_ilock_d + 0.4) / 2)
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("borde del cubo fuera de las ranuras [mm]", hub_edge, 3.0, ">="),
            ("recorrido de avance [°]", p.CTL_thr_fwd, 30.0, ">="),
            ("piel bajo las ranuras [mm]", (U.Y_THR[1] - U.Y_THR[0]) - p.CTL_ilock_depth, 4.0, ">="),
            ("distancia pomo ↔ CG del piloto (x) [mm]", p.CTL_axis[0] - p.CTL_x_pilot, 550.0, "<=")]
