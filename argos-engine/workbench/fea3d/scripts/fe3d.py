"""FEA3D core utilities: boundary-face geometry, closest-point projection on straight-sided tet10 faces, tie (MPC) generation with
a dependency registry, exact consistent loads for linear acceleration fields, frd/dat readers.  fea3d, 2026-10-13."""
from __future__ import annotations
import re
import numpy as np
from scipy.spatial import cKDTree

TET_FACES = {1: (0, 1, 2), 2: (0, 3, 1), 3: (1, 3, 2), 4: (2, 3, 0)}
FACE_MID = {1: (4, 5, 6), 2: (7, 8, 4), 3: (8, 9, 5), 4: (9, 7, 6)}
EDGES = [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]        # C3D10 mid nodes 4..9


# ----------------------------------------------------------------------------------------------- face geometry
def face_geom(X, T10, bf_e, bf_f, bf_n):
    """centroid (m,3), unit outward normal (m,3), area (m,) of straight-sided boundary faces."""
    P0, P1, P2 = X[bf_n[:, 0]], X[bf_n[:, 1]], X[bf_n[:, 2]]
    n = np.cross(P1 - P0, P2 - P0)
    A = 0.5 * np.linalg.norm(n, axis=1)
    n = n / np.maximum(2 * A, 1e-30)[:, None]
    c = (P0 + P1 + P2) / 3.0
    ct = X[T10[bf_e, :4]].mean(axis=1)
    s = np.sign(np.einsum("ij,ij->i", n, c - ct))
    s[s == 0] = 1.0
    return c, n * s[:, None], A


def closest_on_tris(P, A, B, C):
    """Closest points on triangles (A,B,C) (k,3) to points P (k,3) (Ericson, vectorised).  Returns Q (k,3) and barycentric (k,3)."""
    ab, ac, ap = B - A, C - A, P - A
    d1, d2 = np.einsum("ij,ij->i", ab, ap), np.einsum("ij,ij->i", ac, ap)
    bp = P - B
    d3, d4 = np.einsum("ij,ij->i", ab, bp), np.einsum("ij,ij->i", ac, bp)
    cp = P - C
    d5, d6 = np.einsum("ij,ij->i", ab, cp), np.einsum("ij,ij->i", ac, cp)
    k = len(P)
    bary = np.zeros((k, 3))
    done = np.zeros(k, bool)
    # vertex A
    m = (d1 <= 0) & (d2 <= 0)
    bary[m] = [1, 0, 0]; done |= m
    m = ~done & (d3 >= 0) & (d4 <= d3)
    bary[m] = [0, 1, 0]; done |= m
    vc = d1 * d4 - d3 * d2
    m = ~done & (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    v = d1 / np.where(d1 - d3 == 0, 1e-30, d1 - d3)
    bary[m] = np.stack([1 - v[m], v[m], np.zeros(m.sum())], 1); done |= m
    m = ~done & (d6 >= 0) & (d5 <= d6)
    bary[m] = [0, 0, 1]; done |= m
    vb = d5 * d2 - d1 * d6
    m = ~done & (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    w = d2 / np.where(d2 - d6 == 0, 1e-30, d2 - d6)
    bary[m] = np.stack([1 - w[m], np.zeros(m.sum()), w[m]], 1); done |= m
    va = d3 * d6 - d5 * d4
    m = ~done & (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    w = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-30, (d4 - d3) + (d5 - d6))
    bary[m] = np.stack([np.zeros(m.sum()), 1 - w[m], w[m]], 1); done |= m
    m = ~done
    den = 1.0 / np.where(va + vb + vc == 0, 1e-30, va + vb + vc)
    v = vb * den
    w = vc * den
    bary[m] = np.stack([1 - v[m] - w[m], v[m], w[m]], 1)
    Q = bary[:, :1] * A + bary[:, 1:2] * B + bary[:, 2:3] * C
    return Q, bary


def tri6_N(bary):
    """Quadratic triangle shape functions at barycentric (L0, L1, L2) for nodes [c0, c1, c2, m01, m12, m20]."""
    L0, L1, L2 = bary[:, 0], bary[:, 1], bary[:, 2]
    return np.stack([L0 * (2 * L0 - 1), L1 * (2 * L1 - 1), L2 * (2 * L2 - 1), 4 * L0 * L1, 4 * L1 * L2, 4 * L2 * L0], axis=1)


def project_points(P, X, tri_nodes, tri_c, k=12):
    """Closest point of each P on a set of straight 6-node triangles (corners X[tri_nodes[:, :3]]).
    Returns (dist, tri index, bary)."""
    tree = cKDTree(tri_c)
    kk = min(k, len(tri_c))
    _, cand = tree.query(P, k=kk)
    if kk == 1:
        cand = cand[:, None]
    best_d = np.full(len(P), np.inf)
    best_t = np.zeros(len(P), np.int64)
    best_b = np.zeros((len(P), 3))
    for j in range(kk):
        t = cand[:, j]
        A, B, C = X[tri_nodes[t, 0]], X[tri_nodes[t, 1]], X[tri_nodes[t, 2]]
        Q, b = closest_on_tris(P, A, B, C)
        d = np.linalg.norm(P - Q, axis=1)
        m = d < best_d - 1e-12
        best_d[m], best_t[m], best_b[m] = d[m], t[m], b[m]
    return best_d, best_t, best_b


# ----------------------------------------------------------------------------------------------- MPC registry
class Constraints:
    """Linear MPCs (ccx *EQUATION).  terms: list of (node, dof, coef); the first term is the dependent DOF."""

    def __init__(self):
        self.eqs = []                 # (label, terms)
        self.dep = set()              # (node, dof) already dependent
        self.protected = set()        # nodes that may not be dependent (BC, rigid body, coupling nodes)
        self.skipped = {}

    def add(self, label, dep_node, dirv, ind_nodes, ind_w, tol_w=1e-7):
        """sum_d dirv_d u(dep_node, d) - sum_i w_i sum_d dirv_d u(ind_i, d) = 0.  The dependent DOF is the largest |dirv_d|
        not yet dependent at dep_node.  Returns True if written."""
        if dep_node in self.protected:
            self.skipped[label] = self.skipped.get(label, 0) + 1
            return False
        order = np.argsort(-np.abs(dirv))
        ddof = None
        for d in order:
            if abs(dirv[d]) < 0.3:
                break
            if (dep_node, d + 1) not in self.dep:
                ddof = d + 1
                break
        if ddof is None:
            self.skipped[label] = self.skipped.get(label, 0) + 1
            return False
        terms = [(dep_node, ddof, float(dirv[ddof - 1]))]
        for d in range(3):
            if d + 1 != ddof and abs(dirv[d]) > 1e-9:
                terms.append((dep_node, d + 1, float(dirv[d])))
        for n, w in zip(ind_nodes, ind_w):
            if abs(w) < tol_w:
                continue
            for d in range(3):
                if abs(dirv[d]) > 1e-9:
                    terms.append((int(n), d + 1, -float(w * dirv[d])))
        self.dep.add((dep_node, ddof))
        self.eqs.append((label, terms))
        return True

    def add_raw(self, label, terms):
        n, d, _ = terms[0]
        if (n, d) in self.dep or n in self.protected:
            self.skipped[label] = self.skipped.get(label, 0) + 1
            return False
        self.dep.add((n, d))
        self.eqs.append((label, terms))
        return True

    def write(self, f):
        for label, terms in self.eqs:
            f.write(f"*EQUATION\n{len(terms)}\n")
            for i in range(0, len(terms), 4):
                f.write(", ".join(f"{n}, {d}, {c:.9e}" for n, d, c in terms[i:i + 4]) + "\n")


# ----------------------------------------------------------------------------------------------- consistent inertial loads
def tet_vol(X, T10):
    a, b, c, d = (X[T10[:, k]] for k in range(4))
    return np.einsum("ij,ij->i", np.cross(b - a, c - a), d - a) / 6.0


def consistent_linear_field(X, T10, rho, acc_corner):
    """Exact consistent nodal 'mass x acceleration' (sum rho int N_i a dV) for an acceleration field that is linear in space
    (uniform translation + angular acceleration x r), on straight-sided tet10.  acc_corner: (e,4,3) field at the 4 corners.
    corners: -rho V/60 (S - a_i); mid kl: rho V (a_k + a_l)/15 + rho V (S - a_k - a_l)/30, S = sum of the 4 corner values."""
    V = tet_vol(X, T10)
    w = (rho * V)[:, None]
    S = acc_corner.sum(axis=1)
    F = np.zeros((X.shape[0], 3))
    for i in range(4):
        np.add.at(F, T10[:, i], -w / 60.0 * (S - acc_corner[:, i]))
    for m, (k, l) in enumerate(EDGES):
        ak, al = acc_corner[:, k], acc_corner[:, l]
        np.add.at(F, T10[:, 4 + m], w * ((ak + al) / 15.0 + (S - ak - al) / 30.0))
    return F


# ----------------------------------------------------------------------------------------------- readers
def read_frd(path, n_nodes_max):
    """{step_index: {"DISP": (N,3), "STRESS": (N,6), "NDTEMP": (N,)}} (blocks in file order; step index from the frd block counter).
    Node ids are 1-based in the frd; arrays are indexed by node id (row 0 unused)."""
    out = []
    cur = None
    with open(path, "r", errors="replace") as fh:
        lines = fh.readlines()
    i = 0
    n = len(lines)
    while i < n:
        L = lines[i]
        if L.startswith("    1PSTEP"):
            i += 1
            continue
        if L.startswith(" -4  "):
            name = L.split()[1]
            ncomp = int(L.split()[2])
            i += 1
            while lines[i].startswith(" -5"):
                i += 1
            ids, vals = [], []
            while not lines[i].startswith(" -3"):
                s = lines[i]
                if s.startswith(" -1"):
                    ids.append(int(s[3:13]))
                    s = s.rstrip("\r\n")
                    nf = min((len(s) - 13) // 12, ncomp, 6)      # DISP declares 4 components (D1-D3 + ALL) but lists 3
                    v = [float(s[13 + 12 * k: 25 + 12 * k]) for k in range(nf)]
                    vals.append(v + [0.0] * (min(ncomp, 6) - nf))
                i += 1
            ids = np.asarray(ids)
            arr = np.zeros((n_nodes_max + 1, min(ncomp, 6)))
            arr[ids] = np.asarray(vals)
            out.append((name, arr))
            i += 1
            continue
        i += 1
    # group per step: a new step starts at each DISP block
    steps = []
    for name, arr in out:
        if name == "DISP" or not steps:
            steps.append({})
        steps[-1][name] = arr
    return steps


def read_dat_totals(path):
    """Totals of *NODE PRINT ... TOTALS=ONLY blocks: list per step of {set: (label, vector)}."""
    txt = open(path, errors="replace").read().splitlines()
    res = []
    cur = None
    k = 0
    while k < len(txt):
        L = txt[k]
        m = re.match(r"\s*total force \(fx,fy,fz\) for set (\S+) and time\s+([0-9.Ee+-]+)", L)
        if m:
            st, t = m.group(1), float(m.group(2))
            v = [float(x) for x in txt[k + 2].split()]
            res.append((t, st, np.asarray(v)))
            k += 3
            continue
        k += 1
    return res
