"""P1-ELE-01 — Caja estanca del ESC + antichispa con ranura de O-ring axial (cordón 3.53 mm
NBR70), 8 insertos M4 para la tapa-disipador de aluminio (ELE-02) y 6 prensaestopas IP68
(5 × M20 para DC 16 mm² y fases 10 mm², 2 × M16 para señales: acelerador y cordón/seta) + respiradero M12.
Los prensaestopas atraviesan una pared de GLAND_WALL mm en el fondo de un rebaje exterior
(la pared de 18 mm del reborde es más larga que la rosca del prensaestopas) y se fijan con
contratuerca por dentro. Se monta dentro del bote, alto y a la sombra, cerca de la batería."""
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


RIM = 18.0          # reborde: ranura del O-ring cerca del interior, insertos cerca del exterior
INS_EDGE = 5.0      # centro de inserto a 5 mm del borde exterior
GLAND_WALL = 5.0    # pared que atraviesa el prensaestopas (rosca M20 ~ 10–15 mm = pared + contratuerca)
GLAND_ZC = 22.0     # altura del eje de los prensaestopas sobre la base [mm]
GLAND_Y = 36.0      # separación entre prensaestopas (hex. M20 ~24 mm entre caras + holgura de llave)
GLANDS = {          # extremo: [(y, Ø agujero, Ø rebaje)]  — fases a un lado, DC + señal al otro
    "+x": [(-GLAND_Y, 20.5, 32.0), (0.0, 20.5, 32.0), (GLAND_Y, 20.5, 32.0)],
    "-x": [(-GLAND_Y, 20.5, 32.0), (0.0, 20.5, 32.0), (GLAND_Y, 16.5, 28.0)],
}
VENT = (12.5, 22.0)  # respiradero M12 en la pared lateral +y: Ø agujero, Ø rebaje
SIG2 = (16.5, 28.0)  # 2.º paso de señal M16 (cordón/seta → MCU) en la pared lateral −y


def groove_center_offset(p):
    """Distancia del centro de la ranura a la pared interior."""
    depth, width = gland_groove(p)
    return 1.0 + width / 2 + 1.5


def lid_holes(p):
    Li, Wi, Hi = p.esc_in
    Lo, Wo = Li + 2 * RIM, Wi + 2 * RIM
    e = INS_EDGE
    xs = (-Lo / 2 + e, 0.0, Lo / 2 - e)
    ys = (-Wo / 2 + e, Wo / 2 - e)
    # en los extremos el inserto central va entre prensaestopas (y = ±GLAND_Y/2 queda libre)
    pts = [(x, y) for x in xs for y in ys] + [(-Lo / 2 + e, GLAND_Y / 2), (Lo / 2 - e, -GLAND_Y / 2)]
    return pts


def build(p):
    Li, Wi, Hi = p.esc_in
    t, tf, rim = 3.2, 3.2, RIM
    Lo, Wo = Li + 2 * rim, Wi + 2 * rim
    box_ = box(-Lo / 2, Lo / 2, -Wo / 2, Wo / 2, 0, tf + Hi)
    box_ = box_ - box(-Li / 2, Li / 2, -Wi / 2, Wi / 2, tf, tf + Hi + 1)
    depth, width = gland_groove(p)
    z1 = tf + Hi
    c = groove_center_offset(p)            # centro de la ranura respecto del interior
    outer = box(-Li / 2 - c - width / 2, Li / 2 + c + width / 2, -Wi / 2 - c - width / 2, Wi / 2 + c + width / 2, z1 - depth, z1 + 1)
    inner = box(-Li / 2 - c + width / 2, Li / 2 + c - width / 2, -Wi / 2 - c + width / 2, Wi / 2 + c - width / 2, z1 - depth - 1, z1 + 2)
    box_ = box_ - (outer - inner)
    # 8 insertos M4 en el reborde, por fuera de la ranura (compresión uniforme del O-ring)
    for (x, y_) in lid_holes(p):
        box_ = box_ - cyl_z(INSERT_HOLE[4] / 2, z1 - INSERT_LEN[4] - 1, z1 + 1, x=x, y=y_)
    # prensaestopas: agujero pasante + rebaje exterior hasta dejar GLAND_WALL de pared
    zc = GLAND_ZC
    for end, sx in (("+x", 1), ("-x", -1)):
        for y, dh, dc in GLANDS[end]:
            x_out, x_in = sx * Lo / 2, sx * Li / 2
            box_ = box_ - cyl_x(dh / 2, min(x_in, x_out) - 1, max(x_in, x_out) + 1, y=y, z=zc)
            x_cb = x_in + sx * GLAND_WALL
            box_ = box_ - cyl_x(dc / 2, min(x_cb, x_out + sx), max(x_cb, x_out + sx), y=y, z=zc)
    # respiradero de membrana en la pared lateral +y
    box_ = box_ - cyl_y(VENT[0] / 2, Wi / 2 - 1, Wo / 2 + 1, x=0.0, z=zc)
    box_ = box_ - cyl_y(VENT[1] / 2, Wi / 2 + GLAND_WALL, Wo / 2 + 1, x=0.0, z=zc)
    # segundo paso de señal M16 (cordón + seta hacia el MCU) en la pared lateral −y
    box_ = box_ - cyl_y(SIG2[0] / 2, -Wo / 2 - 1, -Wi / 2 + 1, x=0.0, z=zc)
    box_ = box_ - cyl_y(SIG2[1] / 2, -Wo / 2 - 1, -Wi / 2 - GLAND_WALL, x=0.0, z=zc)
    # 4 orejas de montaje M5 en los lados largos (la huella entra en la cama de 210 mm)
    for sy in (-1, 1):
        for xe in (-Lo / 2 + 30, Lo / 2 - 30):
            y0, y1 = (Wo / 2, Wo / 2 + 14) if sy > 0 else (-Wo / 2 - 14, -Wo / 2)
            ear = box(xe - 12, xe + 12, y0, y1, 0, 6)
            box_ = box_ + ear - cyl_z(2.75, -1, 7, x=xe, y=sy * (Wo / 2 + 7))
    return box_


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos
    return [Pos(-700, 150, -300)]


def checks(p, part):
    depth, width = gland_groove(p)
    sep = (RIM - INS_EDGE - INSERT_HOLE[4] / 2) - (groove_center_offset(p) + width / 2)
    Li, Wi, Hi = p.esc_in
    tf = 3.2
    z1 = tf + Hi
    esc = p.esc_size                      # ESC (comprado) + antichispa lado a lado
    asw = p.asw_size
    top_cb = GLAND_ZC + max(dc for g in GLANDS.values() for _, _, dc in g) / 2
    nut_r = 27.7 / 2                      # contratuerca M20 (24 mm entre caras → 27,7 entre vértices)
    return [("profundidad de ranura O-ring [mm]", depth, p.oring_cs * 0.70, ">="),
            ("ancho de ranura O-ring [mm]", width, p.oring_cs * 1.2, ">="),
            ("pared entre ranura de O-ring e inserto [mm]", sep, 2.0, ">="),
            ("largo interior − ESC − 2×(contratuerca + curva de cable) [mm]", Li - esc[0] - 2 * 25, 0.0, ">="),
            ("ancho interior − (ESC + antichispa + 5) [mm]", Wi - (esc[1] + asw[1] + 5), 0.0, ">="),
            ("alto interior − (ESC + 15 de cables) [mm]", Hi - (esc[2] + 15), 0.0, ">="),
            ("margen rebaje de prensaestopas → inserto de la tapa [mm]", (z1 - INSERT_LEN[4] - 1) - top_cb, 1.0, ">="),
            ("margen contratuerca interior → piso [mm]", (GLAND_ZC - nut_r) - tf, 1.0, ">="),
            ("separación entre prensaestopas − hex. M20 entre vértices [mm]", GLAND_Y - 27.7, 4.0, ">="),
            ("contratuerca lateral dentro del ancho interior [mm]", Wi / 2 - (GLAND_Y + nut_r), 0.0, ">=")]
