"""P1-HSG-04 — Soporte lateral de caña, atornillado al costado de babor de la cuna (parte
trasera, fuera de las mejillas) con 2 pernos M8 A4 pasantes. Sujeta el tubo de caña Al
Ø30×3 (HSG-06) desplazado 60 mm a babor, que avanza por fuera de mejillas, capó y
cubrecorrea. La caña es el brazo con el que se levanta la cola (kick-up manual)."""
import math
from cadlib import *

META = dict(
    id="P1-HSG-04", name="tiller_mount", desc="Soporte lateral de caña (en la cuna)",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="LC7 manipulación 300 N en el extremo de la caña; dirección; izado manual de la cola",
    print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Plano u–v sobre la cama (w = Z): flexión de la caña en el plano de capas.",
)

W_OFF = 80.0        # eje de la caña respecto de crujía (w): bloque (r≈22) fuera de las mejillas (|y| ≤ 53)


def tiller_dir(p):
    th = math.radians(p.theta)
    ang = math.radians(p.tiller_angle)
    wx, wz = -math.cos(ang), math.sin(ang)
    du = wx * math.cos(th) - wz * math.sin(th)
    dv = wx * math.sin(th) + wz * math.cos(th)
    return du, dv


def tiller_origin(p):
    return 76.0, 12.0          # (u, v) del eje de la caña en la sección del soporte


def build(p):
    W = p.cradle_w / 2
    u_c, v_c = tiller_origin(p)
    du, dv = tiller_dir(p)
    beta = math.degrees(math.atan2(dv, du))
    rt = (p.tiller_tube_od + 0.3) / 2
    # placa de apoyo contra el costado de la cuna (w de W a W+12) y bloque porta-tubo
    plate = box(55, 95, W, W + 12, -20, 28)
    blockL = 80.0
    blk = Pos(u_c, W_OFF, v_c) * Rot(0, -beta, 0) * box(-18, blockL - 18, -rt - 7, rt + 7, -rt - 7, rt + 7)
    web = box(55, 95, W + 11, W_OFF, -12, 26)
    part = plate + blk + web
    hole = Pos(u_c, W_OFF, v_c) * Rot(0, -beta, 0) * cyl_x(rt, -21, blockL)
    part = part - hole
    for u in (63.0, 87.0):
        part = part - cyl_y(4.2, W - 1, W + 30, x=u, z=4.0)        # 2×M8 pasantes por la cuna
    # 2×M6 transversales que traban el tubo de caña
    for x in (5.0, 40.0):
        part = part - Pos(u_c, W_OFF, v_c) * Rot(0, -beta, 0) * cyl_y(3.2, -rt - 8, rt + 8, x=x)
    return part


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [("separación caña–mejilla exterior [mm]", W_OFF - (p.tiller_tube_od / 2) - (p.cheek_y + p.cheek_t / 2), 3.0, ">=")]
