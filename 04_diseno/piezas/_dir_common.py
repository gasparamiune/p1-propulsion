"""_dir_common.py — utilidades del grupo DIRECCIÓN/REVERSA/MANDOS (no es una pieza: empieza con "_").

- hull(): envolvente convexa 2D.
- pump_lug_proxy(): oreja de la BOMBA SUPUESTA (interfaz a confirmar) para chequeos propios.
- lug_sweep(): volumen barrido por la oreja (inflada por las luces) al girar la boquilla ±STE_sweep.
- bucket_down_loc()/rot_xz(): cinemática del bucket en el marco de la boquilla.
- jet_cone(): cono del chorro (semiángulo STE_cone_deg) desde la salida de la boquilla.
"""
from __future__ import annotations

import math

from build123d import Pos, Rot, Cone, Location
from cadlib import box, cyl_z, prism_xz, prism_xy


def hull(pts):
    """Envolvente convexa (monotone chain) de una lista de (u, v)."""
    P = sorted(set((round(a, 6), round(b, 6)) for a, b in pts))
    if len(P) <= 2:
        return P

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def circ(cx, cz, r, n=24):
    return [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rot_xz(pt, center, ang_deg):
    """Rota (x, z) alrededor de center con la convención de Rot(0, ang, 0) de build123d
    (giro positivo alrededor de +Y: +X → −Z)."""
    a = math.radians(ang_deg)
    dx, dz = pt[0] - center[0], pt[1] - center[1]
    return (center[0] + dx * math.cos(a) + dz * math.sin(a), center[1] - dx * math.sin(a) + dz * math.cos(a))


def bucket_pivot(p):
    return (p.X_bucket_pivot, p.Z_bucket_pivot)


def bucket_rel_loc(p, ang):
    """Location (marco de la boquilla) que gira ang° alrededor del eje del bucket."""
    Xb, Zb = bucket_pivot(p)
    return Pos(Xb, 0, Zb) * Rot(0, ang, 0) * Pos(-Xb, 0, -Zb)


def pump_lug_proxy(p, sign=1, infl_r=0.0, infl_z=0.0, x0=None):
    """Oreja de la bomba (marco JET, como P1-PMP-08): placa ⟂ Z con |Z| ∈ [Z_steer_lug, Z_steer_lug + t],
    extremo redondo de radio STE_lug_r alrededor del perno y brazo de ancho STE_lug_w hacia la tobera."""
    Xp = p.X_steer_pivot
    r = p.STE_lug_r + infl_r
    w = p.STE_lug_w / 2 + infl_r
    za, zb = p.Z_steer_lug - infl_z, p.Z_steer_lug + p.STE_lug_t + infl_z
    z0, z1 = (za, zb) if sign > 0 else (-zb, -za)
    xa = p.STE_lug_x0 if x0 is None else x0
    s = cyl_z(r, z0, z1, x=Xp) + box(xa, Xp, -w, w, z0, z1)
    return s


def lug_sweep(p, sign=1, step=2.5):
    """Barrido de la oreja inflada por las luces al girar ±STE_sweep alrededor del eje del perno."""
    Xp = p.X_steer_pivot
    base = pump_lug_proxy(p, sign, p.STE_gr, p.STE_gz, x0=p.STE_lug_x0 - 30.0)
    out = None
    n = int(round(2 * p.STE_sweep / step))
    for i in range(n + 1):
        a = -p.STE_sweep + i * step
        s = Pos(Xp, 0, 0) * Rot(0, 0, a) * Pos(-Xp, 0, 0) * base
        out = s if out is None else out + s
    return out


def jet_cone(p, length=900.0):
    """Cono del chorro desde la salida de la boquilla (marco de la boquilla, δ = 0)."""
    r0 = p.STE_rb
    r1 = r0 + length * math.tan(math.radians(p.STE_cone_deg))
    c = Cone(r0, r1, length)                       # eje Z, centrado
    return Pos(p.STE_X_exit + length / 2, 0, 0) * Rot(0, 90, 0) * c


def boat_xmax(part, locs):
    """x_bote máxima de una pieza en varias ubicaciones (para holgura al espejo)."""
    return max(part.moved(L).bounding_box().max.X for L in locs)


def inter_vol(a, b):
    try:
        v = (a & b).volume
        return abs(v)
    except Exception:
        return 0.0
