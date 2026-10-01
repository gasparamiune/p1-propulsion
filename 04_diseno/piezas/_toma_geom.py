"""_toma_geom.py — geometría común del grupo TOMA (conducto, placa base, rejilla, casco de referencia).

Pasaje del agua = loft de secciones en planos ⟂ al eje (marco JET, X = const):
  P_fwd: de la nariz del labio a la tangencia; fondo abierto (la sección baja 30 mm bajo el casco).
  P_aft: de la nariz a la brida X_duct_out; piso = cara superior del labio; pasa de rectángulo
         redondeado (W_open) a círculo Ø toma_D_out.
Todo se construye en el marco JET y se lleva al BOTE con loc_jet().
"""
from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Edge, Solid, Vector, Wire  # noqa: E402

from params import loc_jet  # noqa: E402

N_PTS = 96


def _S(s):
    s = min(max(s, 0.0), 1.0)
    return 3 * s * s - 2 * s ** 3


def Z0(p, X):
    """Z (marco JET) del plano del fondo z = 0 en la estación X."""
    a = math.radians(p.alpha)
    return (X * math.sin(a) - p.z_if) / math.cos(a)


def sec_params(p, X, kind, off=0.0):
    """(Zt, Zb, w, rt, rb) de la sección del pasaje (off = 0) o de la cara exterior (off = t)."""
    W2 = p.W_open / 2
    if kind == "fwd":
        z0 = Z0(p, X)
        Zt = max(float(p.toma_roof_Z(X)), z0) if X > p.toma_X_tan else z0
        Zb = z0 - 30.0
        h_up = Zt - z0
        rt = min(p.toma_r_top, max(0.3, 0.9 * h_up))
        rb = 25.0
        w = W2
    else:
        X0, X1 = p.toma_X_nose, p.toma_X_circ
        lam = _S((X - X0) / (X1 - X0))
        Zt = float(p.toma_roof_Z(X))
        Zb = float(p.toma_floor_Z(X))
        R = p.toma_R_out
        w = W2 + lam * (R - W2)
        rt = p.toma_r_top + lam * (R - p.toma_r_top)
        rb = p.toma_r_bot + lam * (R - p.toma_r_bot)
        if lam >= 1.0 - 1e-9:
            Zt, Zb, w, rt, rb = R, -R, R, R, R
        H = Zt - Zb
        rt, rb = min(rt, w, 0.5 * H), min(rb, w, 0.5 * H)
    return Zt + off, Zb - off, w + off, rt + off, rb + off


def _rr_points(Zt, Zb, w, rt, rb, n=N_PTS):
    """Puntos (Y, Z) de un rectángulo de esquinas redondeadas, muestreado por ángulo desde el centro."""
    Zc = 0.5 * (Zt + Zb)
    pts = []
    m = 40
    # contorno denso antihorario desde (w, Zc)
    pts.append((w, Zc))
    pts.append((w, Zt - rt))
    for i in range(1, m + 1):
        a = 0.5 * math.pi * i / m
        pts.append((w - rt + rt * math.cos(a), Zt - rt + rt * math.sin(a)))
    pts.append((-w + rt, Zt))
    for i in range(1, m + 1):
        a = 0.5 * math.pi + 0.5 * math.pi * i / m
        pts.append((-w + rt + rt * math.cos(a), Zt - rt + rt * math.sin(a)))
    pts.append((-w, Zb + rb))
    for i in range(1, m + 1):
        a = math.pi + 0.5 * math.pi * i / m
        pts.append((-w + rb + rb * math.cos(a), Zb + rb + rb * math.sin(a)))
    pts.append((w - rb, Zb))
    for i in range(1, m + 1):
        a = 1.5 * math.pi + 0.5 * math.pi * i / m
        pts.append((w - rb + rb * math.cos(a), Zb + rb + rb * math.sin(a)))
    P = np.array(pts)
    ang = np.unwrap(np.arctan2(P[:, 1] - Zc, P[:, 0]))
    keep = np.concatenate([[True], np.diff(ang) > 1e-9])
    P, ang = P[keep], ang[keep]
    tgt = np.linspace(0, 2 * math.pi, n, endpoint=False)
    ang = np.concatenate([ang, [ang[0] + 2 * math.pi]])
    Y = np.interp(tgt, ang, np.concatenate([P[:, 0], [P[0, 0]]]))
    Z = np.interp(tgt, ang, np.concatenate([P[:, 1], [P[0, 1]]]))
    return list(zip(Y, Z))


def section_wire(p, X, kind, off=0.0):
    Zt, Zb, w, rt, rb = sec_params(p, X, kind, off)
    pts = [Vector(X, y, z) for y, z in _rr_points(Zt, Zb, w, rt, rb)]
    return Wire([Edge.make_spline(pts, periodic=True)])


def stations_fwd(p, da=0.0):
    Xa, Xb = p.toma_X_nose + da, p.toma_X_tan - 3.0   # popa → proa (X decrece)
    n = 34
    s = np.linspace(0.0, 1.0, n)
    s = 1 - (1 - s) ** 1.6                             # más densas hacia la tangencia
    return [Xa + (Xb - Xa) * t for t in s]


def stations_aft(p, ext=0.0, da=0.0):
    Xa, Xb = p.toma_X_nose - 4.0 - da, p.toma_X_circ
    n = 13
    xs = [Xa + (Xb - Xa) * (0.5 - 0.5 * math.cos(math.pi * i / (n - 1))) for i in range(n)]
    xs += [0.5 * (Xb + p.X_duct_out), p.X_duct_out]
    if ext:
        xs.append(p.X_duct_out + ext)
    return xs


def _loft(p, Xs, kind, off):
    ws = [section_wire(p, X, kind, off) for X in Xs]
    return Solid.make_loft(ws)


def _fwd_prism(p, off, x_aft, x_fwd, z_bot):
    """Tramo de la abertura (marco BOTE): costados planos en ±(W/2 + off), techo = curva C2 del
    techo desplazada off según su normal (chapa curvada en una sola dirección, conformable)."""
    from build123d import Line, Face, extrude
    xs = np.linspace(x_aft, p.x_tan, 90)
    zs = p.toma_roof_z(xs)
    dz = np.gradient(zs, xs)
    nrm = np.sqrt(1 + dz ** 2)
    px, pz = xs - off * dz / nrm, zs + off / nrm
    roof = [Vector(float(a), 0, float(b)) for a, b in zip(px, pz)]
    x_end = float(px[-1])
    e_roof = Edge.make_spline(roof)
    pts_tail = [Vector(x_end, 0, float(pz[-1])), Vector(x_end, 0, z_bot), Vector(float(px[0]), 0, z_bot),
                Vector(float(px[0]), 0, float(pz[0]))]
    edges = [e_roof] + [Edge.make_line(pts_tail[i], pts_tail[i + 1]) for i in range(3)]
    face = Face(Wire(edges))
    w = p.W_open / 2 + off
    sol = extrude(face, amount=2 * w, dir=(0, 1, 0))
    from build123d import Pos
    return Pos(0, -w, 0) * sol


@lru_cache(maxsize=4)
def _cached(key):
    p, what = _REG[key]
    LJ = loc_jet(p)
    if what == "P_fwd":
        return _fwd_prism(p, 0.0, p.toma_x_n + 1.5, p.x_tan, -30.0)
    if what == "O_fwd":
        return _fwd_prism(p, p.toma_t, p.toma_x_n, p.x_tan, -35.0)
    if what == "P_aft":
        s = _loft(p, stations_aft(p, ext=3.0, da=2.0), "aft", 0.0)
    elif what == "O_aft":
        s = _loft(p, stations_aft(p), "aft", p.toma_t)
    return s.moved(LJ)


_REG = {}


def solid(p, what):
    """Sólidos del pasaje (P_fwd, P_aft) y de la cara exterior (O_fwd, O_aft), en el marco BOTE."""
    key = (id(p), what)
    _REG[key] = (p, what)
    return _cached(key)


def passage(p):
    return solid(p, "P_fwd") + solid(p, "P_aft")


def section_area(p, X, kind="aft"):
    Zt, Zb, w, rt, rb = sec_params(p, X, kind)
    H = Zt - Zb
    return 2 * w * H - (4 - math.pi) / 2 * (rt ** 2 + rb ** 2)


def rounded_rect_xy(x0, x1, y0, y1, r, z0, z1):
    """Prisma de planta rectangular con esquinas verticales redondeadas."""
    from build123d import Box, Pos, fillet, Axis
    from cadlib import box
    b = box(x0, x1, y0, y1, z0, z1)
    if r > 0:
        b = fillet(b.edges().filter_by(Axis.Z), radius=r)
    return b
