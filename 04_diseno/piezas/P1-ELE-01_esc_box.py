"""P1-ELE-01 — Caja estanca del ESC con ranura de O-ring axial (cordón 2.5 mm NBR70),
4 insertos M4 para la tapa-disipador de aluminio (ELE-02) y 6 prensaestopas.
Se monta dentro del bote, alto, cerca de la batería (cables DC cortos, fases largas)."""
from cadlib import *

META = dict(
    id="P1-ELE-01", name="esc_box", desc="Caja estanca del ESC (O-ring + prensaestopas)",
    material="PETG", process="impresa", qty=1, frame="boat_free",
    load_case="Estanqueidad (IP67 objetivo), compresión del O-ring", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Fondo sobre la cama; la cara del O-ring queda arriba, lisa (última capa + lijado).",
)


def gland_groove(p):
    """Ranura axial: profundidad = cs·(1−squeeze); ancho para llenado ≤ fill."""
    import math
    cs = p.oring_cs
    depth = cs * (1 - p.oring_sq)
    area = math.pi / 4 * cs**2
    width = area / (p.oring_fill * depth)
    return depth, width


def lid_holes(p):
    Li, Wi, Hi = p.esc_in
    rim = 12.0
    Lo, Wo = Li + 2 * rim, Wi + 2 * rim
    xs = (-Lo / 2 + 4.5, 0.0, Lo / 2 - 4.5)
    ys = (-Wo / 2 + 4.5, Wo / 2 - 4.5)
    pts = [(x, y) for x in xs for y in ys] + [(-Lo / 2 + 4.5, 0.0), (Lo / 2 - 4.5, 0.0)]
    return pts


def build(p):
    Li, Wi, Hi = p.esc_in
    t, tf, rim = 3.2, 3.2, 12.0
    Lo, Wo = Li + 2 * rim, Wi + 2 * rim
    box_ = box(-Lo / 2, Lo / 2, -Wo / 2, Wo / 2, 0, tf + Hi)
    box_ = box_ - box(-Li / 2, Li / 2, -Wi / 2, Wi / 2, tf, tf + Hi + 1)
    depth, width = gland_groove(p)
    z1 = tf + Hi
    c = rim / 2 - 0.5                     # centro de la ranura respecto del interior
    outer = box(-Li / 2 - c - width / 2, Li / 2 + c + width / 2, -Wi / 2 - c - width / 2, Wi / 2 + c + width / 2, z1 - depth, z1 + 1)
    inner = box(-Li / 2 - c + width / 2, Li / 2 + c - width / 2, -Wi / 2 - c + width / 2, Wi / 2 + c - width / 2, z1 - depth - 1, z1 + 2)
    box_ = box_ - (outer - inner)
    # 8 insertos M4 en el reborde, por fuera de la ranura (compresión uniforme del O-ring)
    for (x, y_) in lid_holes(p):
        box_ = box_ - cyl_z(INSERT_HOLE[4] / 2, z1 - INSERT_LEN[4] - 1, z1 + 1, x=x, y=y_)
    # prensaestopas: 3×M16 (fases) en un extremo, 2×M16 (batería) + 1×M12 (señal) en el otro
    zc = tf + Hi / 2
    for y in (-25.0, 0.0, 25.0):
        box_ = box_ - cyl_x(8.2, Lo / 2 - rim - 1, Lo / 2 + 1, y=y, z=zc)
    for y, r in ((-25.0, 8.2), (0.0, 6.2), (25.0, 8.2)):
        box_ = box_ - cyl_x(r, -Lo / 2 - 1, -Lo / 2 + rim + 1, y=y, z=zc)
    # orejas de montaje M5
    for sx in (-1, 1):
        ear = box(sx * Lo / 2 - (0 if sx > 0 else 14), sx * Lo / 2 + (14 if sx > 0 else 0), -12, 12, 0, 6)
        box_ = box_ + ear - cyl_z(2.75, -1, 7, x=sx * (Lo / 2 + 7))
    return box_


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos
    return [Pos(-700, 150, -300)]


def checks(p, part):
    depth, width = gland_groove(p)
    return [("profundidad de ranura O-ring [mm]", depth, p.oring_cs * 0.70, ">="),
            ("ancho de ranura O-ring [mm]", width, p.oring_cs * 1.2, ">=")]
