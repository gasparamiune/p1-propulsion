"""P1-MNT-05 — Cuna basculante: une perno de basculación, tubo de cola, placa motriz.

Marco: UNIDAD (X=u a lo largo del eje, Y=w, Z=v; origen en el pivote). El tubo Ø40
queda apretado entre la cuna y su tapa (MNT-06, 4×M6). La placa motriz (HSG-01) atornilla
a la cara delantera (u=u0) con 4×M6 a tuercas cautivas; el buje del rodamiento A entra en
un rebaje. Retén: hoyuelos cónicos en ambas caras laterales (marcha y basculada).
"""
import math
from build123d import Cone
from cadlib import *

META = dict(
    id="P1-MNT-05", name="cradle", desc="Cuna basculante (pivote + abrazadera del tubo + base de placa motriz)",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="LC5 impacto (momento del tubo) / LC1 empuje / retén",
    print_rot=(90, 0, 0), solid_frac=0.9,
    orientation="De canto (w = Z): flexión del tubo y empuje en el plano u–v = plano de capas.",
)

R_TRIM = None


def trim_radius(p):
    """Radio máximo de la cuna delante del pivote para no tocar la base de la horquilla
    al bascular (base a z = disc_z0 + disc_t, pivote a z = pivot_z)."""
    return p.pivot_z - (p.disc_z0 + p.disc_t) - 4.0


def detent_locals(p):
    """Posiciones (u, v) de los hoyuelos: marcha (φ=0) y basculada (φ=tilt_range)."""
    r = p.inp["mount"]["detent_radius_mm"]
    th = math.radians(p.theta)
    out = []
    for phi in (0.0, p.tilt_range):
        a = math.radians(-120.0) - math.radians(phi)       # ángulo en el bote a φ=0
        dx, dz = r * math.cos(a), r * math.sin(a)
        u = dx * math.cos(th) - dz * math.sin(th)
        v = dx * math.sin(th) + dz * math.cos(th)
        out.append((u, v))
    return out


def build(p):
    u0, u1 = p.cradle_u0, p.cradle_u1
    W = p.cradle_w / 2
    vs = -p.e                                   # línea del eje
    vb = p.cradle_vbot
    split_u = 5.0
    upper = box(u0, u1, -W, W, vs + 0.25, p.cradle_vtop)
    front_low = box(u0, split_u, -W, W, vb, vs + 0.5)
    body = upper + front_low
    # recorte circular delante del pivote (despeje de basculación)
    R = trim_radius(p)
    keep = cyl_y(R, -W - 1, W + 1) + box(0, u1 + 1, -W - 1, W + 1, vb - 1, p.cradle_vtop + 1)
    body = body & keep
    # perno de basculación: buje de POM Ø20
    body = body - cyl_y(10.15, -W - 1, W + 1)
    # tubo Ø40 y paso de eje
    rt = (p.tube_od + 0.3) / 2
    body = body - cyl_x(rt, p.u_tube_top, u1 + 1, z=vs)
    body = body - cyl_x(11.0, u0 - 1, p.u_tube_top + 0.1, z=vs)
    # rebaje escalonado para el cartucho del rodamiento A (brida + cuerpo)
    lay = p.layout
    body = body - cyl_x(p.cart_fl_d / 2 + 0.3, u0 - 1, u0 + p.cart_fl_t + 0.2, z=vs)
    body = body - cyl_x(p.cart_od / 2 + 0.25, u0 - 1, lay["u_boss_aft"] + 0.3, z=vs)
    # drenaje del paso de eje hacia abajo (agua que suba por el tubo)
    body = body - cyl_z(3.0, p.cradle_vbot - 1, vs, x=lay["u_boss_aft"] + 4.0)
    # 4×M6 placa motriz → tuercas cautivas abiertas a los lados
    for v in (vb + 12, 18.0):
        for w in (-26.0, 26.0):
            body = body - cyl_x(3.2, u0 - 1, u0 + 30, y=w, z=v)
            h = (NUT_AF[6] + 0.3) / 2
            y0, y1 = (w - h, W + 1) if w > 0 else (-W - 1, w + h)
            body = body - box(u0 + 18, u0 + 18 + NUT_M[6] + 0.6, y0, y1, v - h, v + h)
    # 4×M6 pasantes para la tapa (cabeza abajo, arandela Ø24 + nyloc arriba)
    for u in (20.0, 80.0):
        for w in (-29.0, 29.0):
            body = body - cyl_z(3.25, vs - 1, p.cradle_vtop + 1, x=u, y=w)
    # ojal de cabo de seguridad: inserto M8 para cáncamo A4 (arriba, atrás)
    body = body - cyl_z(INSERT_HOLE[6] / 2 + 0.6, p.cradle_vtop - 16, p.cradle_vtop + 1, x=70.0, y=0)
    # hoyuelos del retén (cono 2·40°) en ambas caras
    for (u, v) in detent_locals(p):
        for side in (-1, 1):
            c = Cone(4.5, 0.5, 3.0, align=(CEN, CEN, MIN))
            c = Pos(u, side * (W + 0.01), v) * Rot(90 if side > 0 else -90, 0, 0) * c
            body = body - c
    return body


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [
        ("Ø alojamiento del tubo", (p.tube_od + 0.3), p.tube_od + 0.3, "≈"),
        ("pared entre buje del pivote y tubo [mm]", p.e - 10.15 - (p.tube_od + 0.3) / 2, 15.0, ">="),
        ("radio de recorte delantero ≥ 80 mm", trim_radius(p), 80.0, ">="),
    ]
