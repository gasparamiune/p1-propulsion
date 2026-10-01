"""P1-STE-08 — Topes mecánicos de dirección a ±STE_stop_deg, Al 5083 8 mm (fijo al espejo, por fuera).

Placa horizontal (en el plano ⟂ al eje de giro) a Z = STE_stop_z, en arco alrededor del eje de giro,
con una ranura por la que pasa el poste del yugo (P1-STE-06): los extremos de la ranura (con taco de
POM 3 mm pegado, no modelado) paran el poste a ±STE_stop_deg, antes de que la timonería T85 / cable M66
(carrera ≈ 230 mm, solo se usan ≈ 70) lleve la boquilla contra la tobera fija. Ala a 90° abulonada al
espejo con 2 × M6 A4 (por debajo de la placa interior P1-CTL-01)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from build123d import Polyline, make_face, extrude, Pos  # noqa: E402
from cadlib import box, cyl_x  # noqa: E402

META = dict(
    id="P1-STE-08", name="tope_direccion", desc="Topes de dirección ±δmax+1,5° (Al 5083 8 mm)",
    material="Al 5083", process="torneada", qty=1, frame="boat", group="jet",
    load_case="Timón forzado contra el tope: 2 × fuerza de la biela del M66 [SUPUESTO]", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="Corte láser, ala doblada 90°",
)
W_RAIL = 4.0      # ancho de cada riel
SLOT_HALF = 12.0  # medio ancho de la ranura (poste Ø22 + 1)


def geom(p):
    Rp = math.hypot(p.STE_post_x, p.STE_post_y)
    th0 = math.degrees(math.atan2(p.STE_post_y, p.STE_post_x))
    dlt = math.degrees((p.STE_post_d / 2 + 0.5) / Rp)          # medio ancho angular del poste
    return Rp, th0, dlt


def _ring(cx, r0, r1, a0, a1, n=48):
    pts = [(cx + r1 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r1 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(cx + r0 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), r0 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return pts


def build(p):
    from params import loc_jet
    Xp = p.X_steer_pivot
    Rp, th0, dlt = geom(p)
    s_ = p.STE_stop_deg
    z0, z1 = p.STE_stop_z
    a_end0, a_end1 = th0 - s_ - dlt, th0 + s_ + dlt                # extremos de la ranura (caras de tope)
    r0, r1 = Rp - SLOT_HALF - W_RAIL, Rp + SLOT_HALF + W_RAIL
    poly = _ring(Xp, r0, r1, a_end0 - 14.0, a_end1 + 10.0)
    face = make_face(Polyline(*[(x, y, 0) for x, y in poly], close=True))
    plate = Pos(0, 0, z0) * extrude(face, amount=z1 - z0)
    slot = _ring(Xp, Rp - SLOT_HALF, Rp + SLOT_HALF, a_end0, a_end1)
    plate = plate - Pos(0, 0, z0 - 1) * extrude(make_face(Polyline(*[(x, y, 0) for x, y in slot], close=True)), amount=z1 - z0 + 2)
    # lengüeta hacia el espejo desde el extremo delantero
    am = math.radians(a_end0 - 7.0)
    xc, yc = Xp + Rp * math.cos(am), Rp * math.sin(am)
    plate = plate + box(xc - 60.0, xc + 2.0, yc - 15.0, yc + 15.0, z0, z1)
    b = plate.moved(loc_jet(p))
    b = b & box(-1000, -6.0, -1000, 1000, -1000, 2000)                    # a popa del ala
    bb = b.bounding_box()
    ym, zm = (bb.min.Y + bb.max.Y) / 2, bb.min.Z + 4.0
    fl = box(-6.5, -0.01, ym - 32.0, ym + 32.0, zm - 26.0, zm + 6.0)
    for dy in (-20.0, 20.0):
        fl = fl - cyl_x(3.3, -7.0, 1.0, y=ym + dy, z=zm - 14.0)
    return b + fl


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    Rp, th0, dlt = geom(p)
    zf = part.bounding_box().max.Z
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("tope − δmax [°]", p.STE_stop_deg - p.steer_max, 1.0, ">="),
            ("tope antes del giro libre contra la bomba (STE_sweep − 2,5) [°]", p.STE_stop_deg, p.STE_sweep - 2.5, "<="),
            ("luz poste ↔ tope con δmax (arco) [mm]", math.radians(p.STE_stop_deg - p.steer_max) * Rp, 2.0, ">="),
            ("placa bajo el brazo del yugo (Z) [mm]", (p.STE_post_z1 - p.STE_arm_t) - p.STE_stop_z[1], 3.0, ">="),
            ("ala bajo la placa interior P1-CTL-01 (z_bote) [mm]", 322.0 - zf, 0.0, ">=")]
