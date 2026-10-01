"""cadlib.py — utilidades comunes para las piezas build123d de P1."""
from __future__ import annotations

import math

from build123d import (Align, Axis, Box, Cylinder, GeomType, Part, Polyline, Pos, Rot,
                       extrude, make_face, Plane, Sketch, Circle, Rectangle, RegularPolygon)

MIN = Align.MIN
CEN = Align.CENTER
MAX = Align.MAX


def box(x0, x1, y0, y1, z0, z1) -> Part:
    """Caja por límites (mm)."""
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(MIN, MIN, MIN))


def cyl_x(r, x0, x1, y=0.0, z=0.0) -> Part:
    return Pos(x0, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0, align=(CEN, CEN, MIN))


def cyl_y(r, y0, y1, x=0.0, z=0.0) -> Part:
    return Pos(x, y0, z) * Rot(-90, 0, 0) * Cylinder(r, y1 - y0, align=(CEN, CEN, MIN))


def cyl_z(r, z0, z1, x=0.0, y=0.0) -> Part:
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=(CEN, CEN, MIN))


def hex_prism_y(s_af, y0, y1, x=0.0, z=0.0) -> Part:
    """Prisma hexagonal (alojamiento de tuerca) a lo largo de Y. s_af = entrecaras."""
    r = s_af / math.sqrt(3)          # radio circunscrito
    sk = Plane.XZ.offset(-y0) * RegularPolygon(r, 6)
    p = extrude(sk, amount=-(y1 - y0))
    return Pos(x, 0, z) * p


def hex_prism_x(s_af, x0, x1, y=0.0, z=0.0) -> Part:
    r = s_af / math.sqrt(3)
    sk = Plane.YZ.offset(x0) * RegularPolygon(r, 6)
    p = extrude(sk, amount=(x1 - x0))
    return Pos(0, y, z) * p


def hex_prism_z(s_af, z0, z1, x=0.0, y=0.0) -> Part:
    r = s_af / math.sqrt(3)
    sk = Plane.XY.offset(z0) * RegularPolygon(r, 6)
    p = extrude(sk, amount=(z1 - z0))
    return Pos(x, y, 0) * p


def prism_xz(points, y0, y1) -> Part:
    """Extruye un polígono definido en el plano XZ (lista de (x, z)) entre y0 e y1."""
    pts = [(x, z) for x, z in points]
    face = make_face(Polyline(*[(x, 0, z) for x, z in pts], close=True))
    sol = extrude(face, amount=y1 - y0, dir=(0, 1, 0))
    return Pos(0, y0, 0) * sol


def prism_yz(points, x0, x1) -> Part:
    """Extruye un polígono del plano YZ (lista de (y, z)) entre x0 y x1."""
    face = make_face(Polyline(*[(0, y, z) for y, z in points], close=True))
    sol = extrude(face, amount=x1 - x0, dir=(1, 0, 0))
    return Pos(x0, 0, 0) * sol


def polar_pts(r, a0, a1, n=12):
    """Puntos (y, z) de un arco de radio r entre ángulos a0→a1 (grados, desde +Y hacia +Z)."""
    return [(r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def prism_xy(points, z0, z1) -> Part:
    face = make_face(Polyline(*[(x, y, 0) for x, y in points], close=True))
    sol = extrude(face, amount=z1 - z0)
    return Pos(0, 0, z0) * sol


def arc_pts(cx, cz, r, a0, a1, n=24):
    """Puntos de un arco (grados) en el plano XZ."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


# tamaños de tuerca/inserto (mm) — ISO 4032 entrecaras [VERIFICADO: norma ISO 4032 (M5=8, M6=10, M8=13, M10=16, M12=18)]
NUT_AF = {4: 7.0, 5: 8.0, 6: 10.0, 8: 13.0, 10: 16.0, 12: 18.0, 16: 24.0}
NUT_M = {4: 3.2, 5: 4.7, 6: 5.2, 8: 6.8, 10: 8.4, 12: 10.8, 16: 14.8}
# insertos térmicos M5/M6: agujero recomendado típico [ESTIMADO: catálogos de insertos, confirmar con probeta]
INSERT_HOLE = {3: 4.0, 4: 5.6, 5: 6.4, 6: 8.0}
INSERT_LEN = {3: 5.7, 4: 8.1, 5: 9.5, 6: 12.7}


def to_print(part: Part, rot=(0, 0, 0)) -> Part:
    """Orienta la pieza para impresión y la apoya en z=0 centrada en XY."""
    q = Rot(*rot) * part
    bb = q.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * q


def cyl_radii(part: Part, tol=0.01):
    """Radios de todas las caras cilíndricas (para verificar cotas de agujeros)."""
    out = []
    for f in part.faces():
        if f.geom_type == GeomType.CYLINDER:
            try:
                out.append(round(f.radius, 3))
            except Exception:
                pass
    return sorted(set(out))


def has_radius(part: Part, r: float, tol=0.02) -> bool:
    return any(abs(x - r) <= tol for x in cyl_radii(part))
