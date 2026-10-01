"""P1-CTL-03 — Soporte del corta-corriente con cordón (kill switch) y de la seta de emergencia, PETG.

Cuña sobre la tapa de la consola, a la izquierda de la unidad de palancas, con la cara inclinada 45°
hacia el piloto: interruptor de cordón (Watski 'Dødmands kontakt universal' / Sea Dog SD-420487-1,
README de electrónica §4) con el clip hacia popa (cordón → chaleco del piloto) y seta NC Ø22 al lado.
Cableado por el pasacables Ø20 hacia el interior de la consola (conector J2 IP68). Agujeros de panel
[ESTIMADO: Ø22 ambos; buscar fichas]. Tirón del cordón: el clip sale antes de CTL_cord_F [SUPUESTO]."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from build123d import Pos, Rot  # noqa: E402
from cadlib import box, cyl_z, prism_xz  # noqa: E402

META = dict(
    id="P1-CTL-03", name="soporte_kill", desc="Soporte PETG del kill switch con cordón y de la seta",
    material="PETG", process="impresa", qty=1, frame="boat", group="ele",
    load_case="Tirón del cordón 150 N [SUPUESTO] + golpe de mano sobre la seta 200 N [SUPUESTO]",
    print_rot=(0, 0, 0), solid_frac=0.6,
    orientation="Base sobre la cama; la cara inclinada a 45° no necesita soportes. 0,2 mm, 5 perímetros",
)
L, B, H = 80.0, 110.0, 55.0
T = 6.0
X_POD, Y_POD = 1760.0, 30.0


def holes():
    """Centros (y) de los agujeros en la cara inclinada."""
    return [-27.0, 27.0]


def build(p):
    z0 = p.CTL_console_top + p.CTL_ply_t
    outer = [(0, 0), (L, 0), (L, H), (H, H)] if False else [(0, 0), (L, 0), (L, H), (L - 15, H), (0, 15)]
    inner = [(T, -1), (L - T, -1), (L - T, H - T), (L - 15 - 0.6 * T, H - T), (T, 15 - 0.4 * T)]
    s = prism_xz(outer, -B / 2, B / 2) - prism_xz(inner, -B / 2 + T, B / 2 - T)
    # ala de fijación
    s = s + (box(-10, L + 10, -B / 2 - 10, B / 2 + 10, 0, 4) - box(T, L - T, -B / 2 + T, B / 2 - T, -1, 5))
    for xx in (-5, L + 5):
        for yy in (-B / 2 - 5, B / 2 + 5):
            s = s - cyl_z(2.75, -1, 5, x=xx, y=yy)
    # agujeros en la cara inclinada: normal (−sin a, 0, cos a), a = ángulo de la cara
    a = math.degrees(math.atan2(H - 15, L - 15))
    xm, zm = (0 + L - 15) / 2, (15 + H) / 2
    for yy, d in zip(holes(), (p.CTL_kill_hole, p.CTL_estop_hole)):
        h = Pos(xm, yy, zm) * Rot(0, -a, 0) * cyl_z(d / 2, -15, 15)
        s = s - h
    return Pos(X_POD - L / 2, Y_POD, z0) * s


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    import importlib.util
    a = math.degrees(math.atan2(H - 15, L - 15))
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("inclinación de la cara hacia el piloto [°]", a, 30.0, ">="),
            ("separación entre centros de agujeros − Ø [mm]", (holes()[1] - holes()[0]) - p.CTL_kill_hole, 25.0, ">="),
            ("pared [mm]", T, p.wall, ">="),
            ("distancia al piloto (x) [mm]", X_POD - p.CTL_x_pilot, 450.0, "<=")]
