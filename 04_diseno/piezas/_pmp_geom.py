"""_pmp_geom.py — geometría común del grupo BOMBA: perfiles de álabe sobre cilindros y loft.

Convenciones (marco JET): X a popa (sentido del flujo), θ desde +Y hacia +Z (giro positivo
alrededor de +X). El impulsor gira en +θ: el flujo relativo va hacia (−θ) → sign = −1. En el
estator el flujo absoluto entra girando hacia +θ → sign = +1.
Ángulos β/α medidos DESDE LA TANGENCIAL (convención de Brennen/p1calc.waterjet, R12 §2.5).
Línea media de arco circular (el ángulo varía linealmente con el arco) y espesor NACA 00xx.
"""
from __future__ import annotations

import math

from build123d import Axis, Cylinder, Pos, Rot, Solid, Spline, Vector, Wire, Align

CEN, MIN = Align.CENTER, Align.MIN


def naca_half(x, t):
    """Semiespesor NACA 4 dígitos (x = s/c ∈ [0, 1], t = espesor relativo) × c aparte."""
    return 5 * t * (0.2969 * math.sqrt(max(x, 0.0)) - 0.1260 * x - 0.3516 * x ** 2
                    + 0.2843 * x ** 3 - 0.1015 * x ** 4)


def camber_line(chord, a1, a2, sign, n=60, x_le=0.0):
    """Línea media en el plano desarrollado (X, T = r·θ). Devuelve [(s/c, X, T, β, nX, nT)]."""
    out = []
    X, T = x_le, 0.0
    ds = chord / n
    prev = None
    for i in range(n + 1):
        f = i / n
        b = math.radians(a1 + (a2 - a1) * f)
        if prev is not None:
            bm = 0.5 * (b + prev)
            X += math.sin(bm) * ds
            T += sign * math.cos(bm) * ds
        prev = b
        tx, tt = math.sin(b), sign * math.cos(b)
        out.append((f, X, T, math.degrees(b), -tt, tx))     # normal = tangente rotada +90°
    return out


def section_pts(r, chord, a1, a2, tc, sign, x_le=0.0, theta0=0.0, n=48):
    """Puntos 3D de un perfil cerrado sobre el cilindro de radio r (BA → extradós → BF → intradós)."""
    cl = camber_line(chord, a1, a2, sign, n=400, x_le=x_le)

    def at(f):
        k = min(int(f * 400), 399)
        a, b = cl[k], cl[k + 1]
        w = f * 400 - k
        return [a[j] + (b[j] - a[j]) * w for j in range(6)]
    xs = [0.5 * (1 - math.cos(math.pi * i / n)) for i in range(n + 1)]      # espaciado coseno
    up, lo = [], []
    for x in xs:
        f, X, T, _, nx, nt = at(x)
        h = naca_half(x, tc) * chord
        if x == 1.0:
            h = max(h, 0.15)
        up.append((X + nx * h, T + nt * h))
        lo.append((X - nx * h, T - nt * h))
    loop = up + lo[::-1][:-1]

    def to3(X, T):
        th = theta0 + T / r
        return Vector(X, r * math.cos(th), r * math.sin(th))
    return [to3(X, T) for X, T in loop]


def section_wire(*a, n=48, **k):
    """Contorno cerrado: extradós (BA→BF, spline) + cierre del BF (recta) + intradós (BF→BA)."""
    from build123d import Line
    pts = section_pts(*a, n=n, **k)
    up = pts[:n + 1]
    lo = pts[n + 1:]
    e1 = Spline(*up)
    lo_pts = [pts[n]] if False else []
    # intradós: del BF inferior al BA (el último punto de 'lo' es contiguo al BA)
    lo_full = [lo[0]] + lo[1:] + [up[0]]
    e2 = Line(up[-1], lo_full[0])
    e3 = Spline(*lo_full)
    return Wire([e1, e2, e3])


def loft_blade(rows, sign, x_le, theta0=0.0):
    """rows: lista de dict(r, chord, a1, a2, tc). Loft suave por las secciones (sobre cilindros, no
    planas) + tapas extremas por superficie de relleno, cosido a sólido."""
    from build123d import Face
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.TopoDS import TopoDS
    wires = [section_wire(rw["r"], rw["chord"], rw["a1"], rw["a2"], rw["tc"], sign, x_le=x_le,
                          theta0=theta0) for rw in rows]
    side = Solid.make_loft(wires, ruled=False)
    faces = list(side.faces()) + [Face.make_surface(wires[0]), Face.make_surface(wires[-1])]
    sew = BRepBuilderAPI_Sewing(1e-3)
    for f in faces:
        sew.Add(f.wrapped)
    sew.Perform()
    sol = Solid(BRepBuilderAPI_MakeSolid(TopoDS.Shell(sew.SewedShape())).Solid())
    if sol.volume < 0:
        sol = Solid(sol.wrapped.Reversed())
    if not sol.is_valid:
        sol = sol.fix()
    return sol


def cyl_x(r, x0, x1, y=0.0, z=0.0):
    return Pos(x0, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0, align=(CEN, CEN, MIN))


def ring_x(ro, ri, x0, x1):
    return cyl_x(ro, x0, x1) - cyl_x(ri, x0 - 1, x1 + 1)


def revolve_profile(pts):
    """Sólido de revolución alrededor del eje X a partir de [(X, r), ...] (polígono cerrado, r ≥ 0)."""
    from build123d import Polyline, make_face, revolve, Plane
    face = make_face(Polyline(*[(x, 0, r) for x, r in pts], close=True))
    return revolve(face, axis=Axis.X, revolution_arc=360)


def max_radius(part, n_edge=24):
    """Máximo radio respecto del eje X (vértices + muestras sobre aristas)."""
    rmax = 0.0
    for e in part.edges():
        for i in range(n_edge + 1):
            v = e.position_at(i / n_edge)
            rmax = max(rmax, math.hypot(v.Y, v.Z))
    return rmax


def bore_radius_at(part, X, r_hi, tol=0.01):
    """Radio libre (sin material) en la estación X (busca por bisección con discos finos)."""
    lo, hi = 0.0, r_hi
    for _ in range(30):
        m = 0.5 * (lo + hi)
        disk = cyl_x(m, X - 0.05, X + 0.05)
        inter = part & disk
        v = 0.0 if inter is None else inter.volume
        if v > 1e-6:
            hi = m
        else:
            lo = m
        if hi - lo < tol:
            break
    return lo
