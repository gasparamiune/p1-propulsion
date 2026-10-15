"""CadQuery geometry helpers (mm) and 4x4 placement transforms."""
from __future__ import annotations
import math
import numpy as np
import cadquery as cq
from OCP.gp import gp_Trsf, gp_Pnt, gp_Ax2, gp_Dir
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib


# ----------------------------------------------------------------------------------- primitives
def revolve(pts):
    """Closed (r, z) polygon (mm) revolved 360 deg about +Z.  r >= 0."""
    clean = []
    for r, z in pts:
        q = (float(r), float(z))
        if not clean or abs(q[0] - clean[-1][0]) + abs(q[1] - clean[-1][1]) > 1e-6:
            clean.append(q)
    if len(clean) > 2 and abs(clean[0][0] - clean[-1][0]) + abs(clean[0][1] - clean[-1][1]) < 1e-6:
        clean.pop()
    # drop collinear intermediate vertices (closed polygon): consecutive collinear segments make OCC merge the
    # faces with an inflated tolerance (v3.2 check: 3.5 mm on TC-08 -> false interference)
    changed = True
    while changed and len(clean) > 3:
        changed = False
        n = len(clean)
        for i in range(n):
            a, b, c = clean[i - 1], clean[i], clean[(i + 1) % n]
            abx, aby, acx, acy = b[0] - a[0], b[1] - a[1], c[0] - a[0], c[1] - a[1]
            L = math.hypot(acx, acy)
            if L > 0 and abs(abx * acy - aby * acx) / L < 2e-3 and (abx * acx + aby * acy) > 0 and math.hypot(abx, aby) < L:
                clean.pop(i)
                changed = True
                break
    wp = cq.Workplane("XZ").polyline(clean).close()
    return wp.revolve(360.0, (0, 0, 0), (0, 1, 0)).val()


def cyl(d, z0, z1, x=0.0, y=0.0):
    return cq.Solid.makeCylinder(d / 2.0, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def cyl_dir(d, length, start, direction):
    dvec = np.array(direction, float)
    dvec /= np.linalg.norm(dvec)
    return cq.Solid.makeCylinder(d / 2.0, length, cq.Vector(*map(float, start)), cq.Vector(*map(float, dvec)))


def tube(od, id_, z0, z1):
    return cyl(od, z0, z1).cut(cyl(id_, z0 - 1, z1 + 1))


def box(lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float)
    return cq.Solid.makeBox(*(hi - lo), cq.Vector(*lo))


def radial_hole(d, angle_deg, z, r_in, r_out):
    """Cylinder along the radial direction at polar angle `angle_deg`, from radius r_in to r_out."""
    a = math.radians(angle_deg)
    u = np.array([math.cos(a), math.sin(a), 0.0])
    start = u * r_in + np.array([0, 0, z])
    return cyl_dir(d, r_out - r_in, start, u)


def union_all(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.clean()


def cut_all(base, tools):
    for t in tools:
        base = base.cut(t)
    return base.clean()


# ----------------------------------------------------------------------------------- transforms
def T_id():
    return np.eye(4)


def T_trans(x=0.0, y=0.0, z=0.0):
    T = np.eye(4)
    T[:3, 3] = [x, y, z]
    return T


def T_rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        R = [[1, 0, 0], [0, c, -s], [0, s, c]]
    elif axis == "y":
        R = [[c, 0, s], [0, 1, 0], [-s, 0, c]]
    else:
        R = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    T = np.eye(4)
    T[:3, :3] = R
    return T


def T_axis_to(vec):
    """Rotation taking +Z to unit vector vec."""
    v = np.array(vec, float)
    v /= np.linalg.norm(v)
    z = np.array([0, 0, 1.0])
    c = float(np.dot(z, v))
    if c > 1 - 1e-12:
        return np.eye(4)
    if c < -1 + 1e-12:
        return T_rot("x", 180)
    k = np.cross(z, v)
    s = np.linalg.norm(k)
    k /= s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    R = np.eye(3) + s * K + (1 - c) * K @ K
    T = np.eye(4)
    T[:3, :3] = R
    return T


def gimbal_T(alpha_deg, beta_deg):
    """Engine pose: outer rotation about X by alpha, then inner about the ring's Y by beta."""
    return T_rot("x", alpha_deg) @ T_rot("y", beta_deg)


def apply(shape, T):
    tr = gp_Trsf()
    tr.SetValues(*[float(T[r][c]) for r in range(3) for c in range(4)])
    return shape.moved(cq.Location(tr))


# ----------------------------------------------------------------------------------- properties
def mass_props(shape, rho_kg_m3):
    """Volume (m3), mass (kg), CG (m), inertia tensor about CG (kg m2) of a mm-shape."""
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, props)
    V = props.Mass() * 1e-9
    if V <= 0:
        return dict(V=0.0, m=0.0, cg=[0, 0, 0], I_cg=np.zeros((3, 3)).tolist())
    c = props.CentreOfMass()
    cg = np.array([c.X(), c.Y(), c.Z()]) * 1e-3
    M = props.MatrixOfInertia()  # about CG, volume-weighted, mm^5
    I = np.array([[M.Value(i, j) for j in (1, 2, 3)] for i in (1, 2, 3)]) * 1e-15 * rho_kg_m3
    return dict(V=V, m=V * rho_kg_m3, cg=cg.tolist(), I_cg=I.tolist())


def bbox(shape):
    b = Bnd_Box()
    BRepBndLib.Add_s(shape.wrapped, b, True)
    return list(b.Get())


def parallel_axis(I_cg, m, r):
    r = np.array(r, float)
    return np.array(I_cg) + m * (np.dot(r, r) * np.eye(3) - np.outer(r, r))


def T_basis(origin, ex, ey, ez):
    """Transform mapping local axes to the given global unit vectors, local origin to `origin`."""
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2] = ex, ey, ez
    T[:3, 3] = origin
    return T
