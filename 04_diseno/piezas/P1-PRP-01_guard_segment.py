"""P1-PRP-01 — Segmento de aro protector PERFILADO (×6 idénticos, 60°).

Perfil (research/R03): superficie interior cilíndrica con holgura radial 6 mm (2,4 % D) y
exterior con espesor tipo NACA 00xx unilateral (t/c 0,15, L/D ≈ 0,3, borde de ataque hacia
proa), sin barras delante del disco (no peina algas). Unión: en cada extremo una oreja
exterior con agujero TANGENCIAL M4; las orejas de segmentos vecinos se atornillan entre sí.
Arriba (90°) la montura del brazo de STR-01 y abajo (270°) la del patín PRP-02 abrazan el
par de orejas con el mismo tornillo.
"""
import math
from build123d import Axis, Polyline, make_face, revolve
from cadlib import *

META = dict(
    id="P1-PRP-01", name="guard_segment", desc="Segmento de aro protector perfilado (×6)",
    material="PETG", process="impresa", qty=6, frame="unit",
    load_case="Golpes en el aro (LC5 secundario), arrastre", print_rot=(0, -90, 0), solid_frac=1.0,
    orientation="Eje del anillo = Z: impactos radiales y flexión del arco en el plano de capas.",
)


def thickness(p, x):
    """Espesor radial del perfil a la distancia axial x desde el borde de ataque."""
    c, tc = p.guard_L, p.guard_tc
    xc = min(max(x / c, 0.0), 1.0)
    yt = 5 * tc * (0.2969 * math.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1015 * xc**4) * c
    return max(2.0, 2 * yt)


def profile_pts(p, n=24):
    Ri = p.guard_ri
    L = p.guard_L
    xs = [L * (1 - math.cos(math.pi * i / n)) / 2 for i in range(n + 1)]   # densidad en bordes
    outer = [(x - L / 2, Ri + thickness(p, x)) for x in xs]
    inner = [(L / 2, Ri), (-L / 2, Ri)]
    return outer + inner


def lug_center(p):
    """(x axial, r radial) del centro del agujero de la oreja."""
    Ri = p.guard_ri
    x = -p.guard_L / 2 + 0.3 * p.guard_L
    t = thickness(p, 0.3 * p.guard_L)
    return x, Ri + t + p.guard_lug[2] / 2


def build(p):
    pts = profile_pts(p)
    face = make_face(Polyline(*[(x, 0, r) for x, r in pts], close=True))
    seg = Rot(-60, 0, 0) * revolve(face, Axis.X, 60)            # ocupa 30°–90°
    # orejas en ambos extremos (dentro del segmento), agujero tangencial
    lt, la, lr = p.guard_lug
    xl, rl = lug_center(p)
    Ri = p.guard_ri
    for a_end, sgn in ((30.0, -1), (90.0, +1)):           # +1: la tangente local +y apunta al interior del segmento
        a = math.radians(a_end)
        # marco local de la oreja: tangente t̂ = (−sin a, cos a) en (y, z)
        lug = box(-la / 2, la / 2, 0, lt, Ri + 2.0, rl + lr / 2 + 2.0)        # en marco (x, tang, radial)
        hole = cyl_y(2.2, -1, lt + 1, x=0, z=rl)
        lug = lug - hole
        # tang local +y → hacia el interior del segmento: sgn
        lug = Pos(xl, 0, 0) * Rot(a_end - 90.0, 0, 0) * (Rot(0, 0, 0) * (lug if sgn > 0 else Rot(0, 0, 180) * lug))
        seg = seg + lug
    return seg


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    L = loc_unit(p, steer, tilt)
    return [L * Pos(p.s_prop, 0, -p.e) * Rot(60.0 * k, 0, 0) for k in range(6)]


def checks(p, part):
    return [("holgura radial punta–aro [mm]", p.guard_ri - p.prop_D / 2, 5.0, ">="),
            ("espesor máx. del perfil [mm]", max(thickness(p, x) for x in range(0, int(p.guard_L) + 1)), 8.0, ">=")]
