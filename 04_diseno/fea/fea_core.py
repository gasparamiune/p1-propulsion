"""fea_core.py — Núcleo FEA lineal elástico 3D para piezas de P1 (gmsh + numpy/scipy).

- Malla: gmsh importa el STEP (OCC) y genera tetraedros lineales; la interpolación es
  P2 (10 nodos, aristas rectas) — buena en flexión con 2–3 elementos en el espesor.
- Ensamble P2 vectorizado (numpy).  scikit-fem se usa en tests/test_fea.py como
  verificación cruzada del ensamble (ElementTetP2); para mallas de 10⁵ grados de libertad
  su ensamble genérico y SuperLU son demasiado lentos (medido: >90 s por factorización).
- Solver: gradiente conjugado con precondicionador de dos niveles (P2 → P1 en la misma
  malla; suavizado Chebyshev–Jacobi; nivel grueso P1 por factorización dispersa).
- Apoyos: Dirichlet, resortes de superficie tipo Winkler (normal / tangencial), unión con
  cuerpos rígidos (tubo, perno) por resortes normales, resortes entre promedios de parche
  (pernos) y contacto unilateral (solo compresión) por iteración de conjunto activo.
Unidades: mm, N, MPa.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# ---------------------------------------------------------------------------
# Malla con gmsh
# ---------------------------------------------------------------------------


def mesh_step(step_path, h, curv_n=10, hmin=1.0, stl_fallback=None, algo3d=1, refine=None, netgen=False):
    """Importa un STEP (o, si falla, volumetriza un STL) y devuelve (X (N,3), T (Ne,4), info).
    refine: lista de esferas (cx, cy, cz, radio, h_local) con tamaño de malla reducido.
    netgen: optimización adicional de Netgen (reduce las astillas en paredes finas del CAD)."""
    import gmsh
    info = {"source": "step", "h_mm": h, "curv_n": curv_n}
    gmsh.initialize(interruptible=False)
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("pieza")
        ok = False
        try:
            gmsh.model.occ.importShapes(str(step_path))
            gmsh.model.occ.synchronize()
            ok = len(gmsh.model.getEntities(3)) >= 1
        except Exception as e:  # pragma: no cover
            info["step_error"] = str(e)
        if not ok:
            if stl_fallback is None:
                raise RuntimeError(f"gmsh no pudo importar {step_path} y no hay STL de respaldo")
            gmsh.clear()
            gmsh.merge(str(stl_fallback))
            gmsh.model.mesh.classifySurfaces(40 * np.pi / 180, True, True, np.pi)
            gmsh.model.mesh.createGeometry()
            s = gmsh.model.getEntities(2)
            sl = gmsh.model.geo.addSurfaceLoop([e[1] for e in s])
            gmsh.model.geo.addVolume([sl])
            gmsh.model.geo.synchronize()
            info["source"] = "stl"
        gmsh.option.setNumber("Mesh.MeshSizeMax", h)
        gmsh.option.setNumber("Mesh.MeshSizeMin", min(hmin, h))
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", curv_n)
        gmsh.option.setNumber("Mesh.Algorithm", 6)
        gmsh.option.setNumber("Mesh.Algorithm3D", algo3d)
        gmsh.option.setNumber("Mesh.Optimize", 1)
        gmsh.option.setNumber("Mesh.OptimizeNetgen", 1 if netgen else 0)
        info["netgen"] = bool(netgen)
        if refine:
            tags = []
            for (cx, cy, cz, rr, hl) in refine:
                ft = gmsh.model.mesh.field.add("Ball")
                for k, v in (("XCenter", cx), ("YCenter", cy), ("ZCenter", cz), ("Radius", rr),
                             ("VIn", hl), ("VOut", 1e3 * h), ("Thickness", rr / 2)):
                    gmsh.model.mesh.field.setNumber(ft, k, v)
                tags.append(ft)
            fm = gmsh.model.mesh.field.add("Min")
            gmsh.model.mesh.field.setNumbers(fm, "FieldsList", tags)
            gmsh.model.mesh.field.setAsBackgroundMesh(fm)
            info["refine"] = [list(map(float, r)) for r in refine]
        gmsh.model.mesh.generate(3)
        nt, xyz, _ = gmsh.model.mesh.getNodes()
        et, _, conn = gmsh.model.mesh.getElements(3)
        k = list(et).index(4)
        xyz = xyz.reshape(-1, 3)
        lut = np.zeros(int(nt.max()) + 1, dtype=np.int64)
        lut[nt.astype(np.int64)] = np.arange(len(nt))
        T = lut[conn[k].astype(np.int64)].reshape(-1, 4)
    finally:
        gmsh.finalize()
    used = np.unique(T)
    remap = -np.ones(len(xyz), dtype=np.int64)
    remap[used] = np.arange(len(used))
    X = np.ascontiguousarray(xyz[used])
    T = np.ascontiguousarray(remap[T])
    # orientación positiva
    x0 = X[T[:, 0]]
    det = np.einsum("ij,ij->i", np.cross(X[T[:, 1]] - x0, X[T[:, 2]] - x0), X[T[:, 3]] - x0)
    neg = det < 0
    T[neg, 1], T[neg, 2] = T[neg, 2].copy(), T[neg, 1].copy()
    return X, T, info


def merge_meshes(meshes):
    """Une varias mallas (X, T) sin nodos compartidos. Devuelve X, T, body (Ne,) y offsets."""
    Xs, Ts, body, off = [], [], [], 0
    for b, (X, T) in enumerate(meshes):
        Xs.append(X)
        Ts.append(T + off)
        body.append(np.full(len(T), b))
        off += len(X)
    return np.vstack(Xs), np.vstack(Ts), np.concatenate(body)


# ---------------------------------------------------------------------------
# Espacio P2 sobre tetraedros
# ---------------------------------------------------------------------------
EDGES = np.array([[0, 1], [1, 2], [0, 2], [0, 3], [1, 3], [2, 3]])
FACES = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])      # cara opuesta al vértice i
_a, _b = 0.5854101966249685, 0.1381966011250105
QP_TET = np.array([[_a, _b, _b, _b], [_b, _a, _b, _b], [_b, _b, _a, _b], [_b, _b, _b, _a]])   # grado 2, w=1/4
_tri = [(0.108103018168070, 0.445948490915965, 0.445948490915965, 0.223381589678011),
        (0.816847572980459, 0.091576213509771, 0.091576213509771, 0.109951743655322)]
QP_TRI, QW_TRI = [], []
for l0, l1, l2, w in _tri:                                           # Dunavant grado 4 (6 puntos)
    for perm in ((l0, l1, l2), (l1, l2, l0), (l2, l0, l1)):
        QP_TRI.append(perm)
        QW_TRI.append(w)
QP_TRI, QW_TRI = np.array(QP_TRI), np.array(QW_TRI)


def tri_p2_shape(L):
    """Funciones P2 del triángulo en baricéntricas L (...,3) → (...,6): v0,v1,v2,e01,e12,e20."""
    l0, l1, l2 = L[..., 0], L[..., 1], L[..., 2]
    return np.stack([l0 * (2 * l0 - 1), l1 * (2 * l1 - 1), l2 * (2 * l2 - 1),
                     4 * l0 * l1, 4 * l1 * l2, 4 * l2 * l0], axis=-1)


def lame(E, nu):
    return E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))


@dataclass
class P2Space:
    X: np.ndarray
    T: np.ndarray
    body: np.ndarray | None = None
    n_extra: int = 0                       # gdl adicionales (cuerpos rígidos), al final
    _cache: dict = field(default_factory=dict)

    def __post_init__(self):
        X, T = self.X, self.T
        N = len(X)
        self.N = N
        pairs = np.sort(T[:, EDGES], axis=2)                    # (Ne,6,2)
        keys = pairs[..., 0].astype(np.int64) * N + pairs[..., 1]
        ukeys, inv = np.unique(keys.ravel(), return_inverse=True)
        self.edge_keys = ukeys
        self.edges = np.stack([ukeys // N, ukeys % N], axis=1)
        self.E = len(ukeys)
        self.T10 = np.hstack([T, N + inv.reshape(-1, 6)])       # (Ne,10)
        self.nnodes = N + self.E
        self.Xall = np.vstack([X, 0.5 * (X[self.edges[:, 0]] + X[self.edges[:, 1]])])
        self.ndof_fem = 3 * self.nnodes
        # gradientes de baricéntricas y volúmenes
        x0 = X[T[:, 0]]
        J = np.stack([X[T[:, 1]] - x0, X[T[:, 2]] - x0, X[T[:, 3]] - x0], axis=2)
        det = np.linalg.det(J)
        invJ = np.linalg.inv(J)
        gl = np.empty((len(T), 4, 3))
        gl[:, 1:, :] = invJ
        gl[:, 0, :] = -invJ.sum(axis=1)
        self.gl = gl
        self.vol = det / 6.0
        if (self.vol <= 0).any():
            raise ValueError("tetraedros degenerados o invertidos en la malla")
        self._boundary()

    @property
    def ndof(self):
        return self.ndof_fem + self.n_extra

    def add_extra(self, n):
        i0 = self.ndof
        self.n_extra += n
        return np.arange(i0, i0 + n)

    # --- funciones de forma ---
    def grads_at(self, L, elems=None):
        """∇N (ne,10,3) de las 10 funciones P2 en el punto baricéntrico L (4,)."""
        gl = self.gl if elems is None else self.gl[elems]
        G = np.empty((gl.shape[0], 10, 3))
        for i in range(4):
            G[:, i] = (4 * L[i] - 1) * gl[:, i]
        for k, (a, b) in enumerate(EDGES):
            G[:, 4 + k] = 4 * (L[a] * gl[:, b] + L[b] * gl[:, a])
        return G

    def elem_dofs(self, elems=None):
        T10 = self.T10 if elems is None else self.T10[elems]
        return (3 * T10[:, :, None] + np.arange(3)).reshape(len(T10), 30)

    # --- rigidez ---
    def stiffness(self, E, nu, chunk=8000):
        lam, mu = lame(E, nu)
        ne = len(self.T)
        n = self.ndof
        mats = []
        for c0 in range(0, ne, chunk):
            el = np.arange(c0, min(ne, c0 + chunk))
            nc = len(el)
            Gq = np.stack([self.grads_at(QP_TET[q], el) for q in range(4)], axis=1)   # (nc,4,10,3)
            Gf = Gq.reshape(nc, 4, 30) * np.sqrt(self.vol[el] / 4.0)[:, None, None]
            M1 = np.matmul(Gf.transpose(0, 2, 1), Gf)                                 # (nc,30,30)
            M5 = M1.reshape(nc, 10, 3, 10, 3)
            S = np.einsum("eacbc->eab", M5)
            Ke = lam * M5 + mu * M5.transpose(0, 1, 4, 3, 2)
            Ke = Ke.reshape(nc, 30, 30) + mu * np.einsum("eab,cd->eacbd", S, np.eye(3)).reshape(nc, 30, 30)
            d = self.elem_dofs(el)
            r = np.broadcast_to(d[:, :, None], (nc, 30, 30)).ravel()
            c = np.broadcast_to(d[:, None, :], (nc, 30, 30)).ravel()
            mats.append(sp.csr_matrix((Ke.ravel(), (r, c)), shape=(n, n)))
        K = mats[0]
        for m in mats[1:]:
            K = K + m
        return K

    def resize(self, A):
        """Agranda una matriz/vector al número actual de gdl (tras add_extra)."""
        n = self.ndof
        if sp.issparse(A):
            A = A.tocoo()
            return sp.csr_matrix((A.data, (A.row, A.col)), shape=(n, n))
        out = np.zeros(n)
        out[:len(A)] = A
        return out

    # --- frontera ---
    def _boundary(self):
        T, N, X = self.T, self.N, self.X
        F = T[:, FACES]                                           # (Ne,4,3)
        Fs = np.sort(F, axis=2).reshape(-1, 3).astype(np.int64)
        keys = (Fs[:, 0] * N + Fs[:, 1]) * N + Fs[:, 2]
        _, idx, cnt = np.unique(keys, return_index=True, return_counts=True)
        bidx = idx[cnt == 1]
        tet, lf = bidx // 4, bidx % 4
        tri = F[tet, lf].copy()
        opp = T[tet, lf]
        n = np.cross(X[tri[:, 1]] - X[tri[:, 0]], X[tri[:, 2]] - X[tri[:, 0]])
        flip = np.einsum("ij,ij->i", n, X[opp] - X[tri[:, 0]]) > 0
        tri[flip, 1], tri[flip, 2] = tri[flip, 2].copy(), tri[flip, 1].copy()
        n[flip] *= -1
        area2 = np.linalg.norm(n, axis=1)
        self.ftri = tri
        self.fnormal = n / area2[:, None]
        self.farea = 0.5 * area2
        self.fcent = X[tri].mean(axis=1)
        self.ftet = tet
        ek = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            s = np.sort(tri[:, [a, b]], axis=1)
            ek.append(np.searchsorted(self.edge_keys, s[:, 0] * N + s[:, 1]))
        self.f6 = np.hstack([tri, N + np.stack(ek, axis=1)])        # (Nf,6)
        self.fbody = None if self.body is None else self.body[tet]

    def facet_quad(self, fsel):
        """Puntos (nf,6,3), pesos·área (nf,6), funciones (6q,6n) de las facetas fsel."""
        Xt = self.X[self.ftri[fsel]]                                 # (nf,3,3)
        Xq = np.einsum("qk,fkd->fqd", QP_TRI, Xt)
        W = QW_TRI[None, :] * self.farea[fsel][:, None]
        return Xq, W, tri_p2_shape(QP_TRI)

    def facet_dofs(self, fsel):
        return (3 * self.f6[fsel][:, :, None] + np.arange(3)).reshape(len(fsel), 18)

    def facet_nodes(self, fsel):
        return np.unique(self.f6[fsel])

    # --- cargas y resortes de superficie ---
    def traction_load(self, fsel, tfun):
        """f = ∫ N·t dA;  tfun(Xq (nf,6,3), n (nf,3)) → t (nf,6,3) [MPa]."""
        fsel = np.asarray(fsel)
        f = np.zeros(self.ndof)
        if len(fsel) == 0:
            return f
        Xq, W, Nq = self.facet_quad(fsel)
        t = tfun(Xq, self.fnormal[fsel])
        fe = np.einsum("fq,qi,fqc->fic", W, Nq, t).reshape(len(fsel), 18)
        np.add.at(f, self.facet_dofs(fsel).ravel(), fe.ravel())
        return f

    def _projector(self, fsel, Xq, kf, k_t=0.0, mode="normal", direction=None, axis=None):
        """Proyector por punto de cuadratura P (nf,nq,3,3): n nᵀ (+ (k_t/k)(I − n nᵀ)).
        axis=(punto, dirección): normal radial exacta hacia el eje (agujeros) — evita que un
        agujero facetado transmita par alrededor de su eje (articulación sin fricción)."""
        nf, nq = Xq.shape[:2]
        if mode == "dir":
            d = np.asarray(direction, float) / np.linalg.norm(direction)
            n = np.broadcast_to(d, (nf, nq, 3))
        elif axis is not None:
            pt, ax = np.asarray(axis[0], float), np.asarray(axis[1], float) / np.linalg.norm(axis[1])
            v = Xq - pt
            v = v - (v @ ax)[..., None] * ax
            n = -v / np.linalg.norm(v, axis=-1, keepdims=True)
            if np.einsum("fqc,fc->f", n, self.fnormal[fsel]).mean() < 0:      # superficie convexa
                n = -n
        else:
            n = np.broadcast_to(self.fnormal[fsel][:, None, :], (nf, nq, 3))
        P = np.einsum("fqc,fqd->fqcd", n, n)
        if k_t and mode != "dir":
            P = P + (k_t / np.maximum(kf, 1e-30))[:, None, None, None] * (np.eye(3)[None, None] - P)
        return P

    def spring_matrix(self, fsel, k, mode="normal", direction=None, k_t=0.0, axis=None):
        """∫ k (u·n)(v·n) dA  (+ k_t tangencial).  mode='dir': dirección fija `direction`.
        k puede ser escalar o array por faceta [N/mm³]."""
        fsel = np.asarray(fsel)
        n = self.ndof
        if len(fsel) == 0:
            return sp.csr_matrix((n, n))
        Xq, W, Nq = self.facet_quad(fsel)
        kf = np.broadcast_to(np.asarray(k, float), (len(fsel),))
        P = self._projector(fsel, Xq, kf, k_t, mode, direction, axis)
        kw = W * kf[:, None]
        Ke = np.einsum("fq,qi,qj,fqcd->ficjd", kw, Nq, Nq, P).reshape(len(fsel), 18, 18)
        d = self.facet_dofs(fsel)
        r = np.broadcast_to(d[:, :, None], Ke.shape).ravel()
        c = np.broadcast_to(d[:, None, :], Ke.shape).ravel()
        return sp.csr_matrix((Ke.ravel(), (r, c)), shape=(n, n))

    def rigid_coupling(self, fsel, k, rdofs, xref, k_t=0.0, axis=None):
        """Resortes normales (y tangenciales k_t) entre facetas y un cuerpo rígido de 6 gdl
        (U, Θ alrededor de xref) en los índices rdofs. Devuelve la matriz completa."""
        fsel = np.asarray(fsel)
        n = self.ndof
        if len(fsel) == 0:
            return sp.csr_matrix((n, n))
        Xq, W, Nq = self.facet_quad(fsel)
        nf = len(fsel)
        kf = np.broadcast_to(np.asarray(k, float), (nf,))
        P = self._projector(fsel, Xq, kf, k_t, "normal", None, axis)          # (nf,q,3,3)
        # R(x) (3×6): u = U - [r]× Θ
        r = Xq - np.asarray(xref)[None, None, :]
        R = np.zeros((nf, 6, 3, 6))
        R[:, :, 0, 0] = R[:, :, 1, 1] = R[:, :, 2, 2] = 1.0
        R[:, :, 0, 4], R[:, :, 0, 5] = r[..., 2], -r[..., 1]
        R[:, :, 1, 3], R[:, :, 1, 5] = -r[..., 2], r[..., 0]
        R[:, :, 2, 3], R[:, :, 2, 4] = r[..., 1], -r[..., 0]
        kw = W * kf[:, None]                                           # (nf,q)
        Kuu = np.einsum("fq,qi,qj,fqcd->ficjd", kw, Nq, Nq, P).reshape(nf, 18, 18)
        PR = np.einsum("fqcd,fqda->fqca", P, R)                         # (nf,q,3,6)
        Kur = -np.einsum("fq,qi,fqca->fica", kw, Nq, PR).reshape(nf, 18, 6)
        Krr = np.einsum("fq,fqca,fqcb->ab", kw, R, PR)
        d = self.facet_dofs(fsel)
        rows = [np.broadcast_to(d[:, :, None], Kuu.shape).ravel(),
                np.broadcast_to(d[:, :, None], Kur.shape).ravel(),
                np.broadcast_to(np.asarray(rdofs)[None, :, None], (nf, 6, 18)).ravel(),
                np.repeat(rdofs, 6)]
        cols = [np.broadcast_to(d[:, None, :], Kuu.shape).ravel(),
                np.broadcast_to(np.asarray(rdofs)[None, None, :], Kur.shape).ravel(),
                np.broadcast_to(d[:, None, :], (nf, 6, 18)).ravel(),
                np.tile(rdofs, 6)]
        data = [Kuu.ravel(), Kur.ravel(), Kur.transpose(0, 2, 1).ravel(), Krr.ravel()]
        return sp.csr_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n))

    def patch_average(self, fsel, direction):
        """Vector a tal que a·u = promedio (por área) del desplazamiento en `direction`."""
        fsel = np.asarray(fsel)
        Xq, W, Nq = self.facet_quad(fsel)
        d = np.asarray(direction, float) / np.linalg.norm(direction)
        fe = np.einsum("fq,qi,c->fic", W, Nq, d).reshape(len(fsel), 18) / W.sum()
        a = np.zeros(self.ndof)
        np.add.at(a, self.facet_dofs(fsel).ravel(), fe.ravel())
        return a

    def facet_values(self, u, fsel):
        """Desplazamiento en el centroide de cada faceta (nf,3)."""
        U = u[:self.ndof_fem].reshape(-1, 3)
        Nc = tri_p2_shape(np.array([1 / 3, 1 / 3, 1 / 3]))
        return np.einsum("i,fic->fc", Nc, U[self.f6[fsel]])

    # --- tensiones ---
    def vertex_stress(self, u, E, nu):
        """Tensión (Ne,4,3,3) en los 4 vértices de cada elemento (campo lineal exacto P2)."""
        lam, mu = lame(E, nu)
        U = u[:self.ndof_fem].reshape(-1, 3)[self.T10]                  # (Ne,10,3)
        out = np.empty((len(self.T), 4, 3, 3))
        for k in range(4):
            L = np.zeros(4)
            L[k] = 1.0
            G = self.grads_at(L)
            Du = np.einsum("eac,ead->ecd", U, G)                        # ∂u_c/∂x_d
            eps = 0.5 * (Du + Du.transpose(0, 2, 1))
            tr = np.trace(eps, axis1=1, axis2=2)
            out[:, k] = 2 * mu * eps + lam * tr[:, None, None] * np.eye(3)
        return out

    def nodal_average(self, Sv):
        """Promedio nodal ponderado por volumen de un campo por vértice (Ne,4,...)."""
        w = np.repeat(self.vol, 4)
        idx = self.T.ravel()
        shp = Sv.shape[2:]
        flat = Sv.reshape(len(self.T) * 4, -1) * w[:, None]
        acc = np.zeros((self.N, flat.shape[1]))
        np.add.at(acc, idx, flat)
        ws = np.bincount(idx, weights=w, minlength=self.N)
        return (acc / ws[:, None]).reshape((self.N,) + shp)

    def node_volume(self):
        return np.bincount(self.T.ravel(), weights=np.repeat(self.vol / 4, 4), minlength=self.N)

    def coarse_prolongation(self):
        """P: gdl P1 de vértices (+ extra) → gdl P2 (+ extra)."""
        N, E = self.N, self.E
        rows = [np.arange(3 * N)]
        cols = [np.arange(3 * N)]
        vals = [np.ones(3 * N)]
        for side in (0, 1):
            v = self.edges[:, side]
            rows.append((3 * (N + np.arange(E))[:, None] + np.arange(3)).ravel())
            cols.append((3 * v[:, None] + np.arange(3)).ravel())
            vals.append(np.full(3 * E, 0.5))
        ne = self.n_extra
        rows.append(self.ndof_fem + np.arange(ne))
        cols.append(3 * N + np.arange(ne))
        vals.append(np.ones(ne))
        return sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                             shape=(self.ndof, 3 * N + ne))


# ---------------------------------------------------------------------------
# Post-proceso
# ---------------------------------------------------------------------------

def von_mises(S):
    s = S
    return np.sqrt(0.5 * ((s[..., 0, 0] - s[..., 1, 1]) ** 2 + (s[..., 1, 1] - s[..., 2, 2]) ** 2
                          + (s[..., 2, 2] - s[..., 0, 0]) ** 2)
                   + 3 * (s[..., 0, 1] ** 2 + s[..., 1, 2] ** 2 + s[..., 0, 2] ** 2))


def principal_max(S):
    sh = S.shape[:-2]
    return np.linalg.eigvalsh(S.reshape(-1, 3, 3))[:, -1].reshape(sh)


def normal_stress(S, n):
    n = np.asarray(n, float) / np.linalg.norm(n)
    return np.einsum("...ij,i,j->...", S, n, n)


def weighted_percentile(vals, weights, q):
    o = np.argsort(vals)
    cw = np.cumsum(weights[o])
    return float(vals[o][np.searchsorted(cw, q / 100.0 * cw[-1])])


# ---------------------------------------------------------------------------
# Solver: PCG con precondicionador de dos niveles (P2 → P1)
# ---------------------------------------------------------------------------

class TwoLevel:
    def __init__(self, K, P, cheb_deg=3, verbose=False):
        t0 = time.time()
        self.K = K
        d = K.diagonal()
        self.Dinv = 1.0 / d
        keep = np.flatnonzero(np.asarray(abs(P).sum(axis=0)).ravel() > 0)
        self.P = P[:, keep].tocsr()
        self.PT = self.P.T.tocsr()
        Ac = (self.PT @ K @ self.P).tocsc()
        Ac = 0.5 * (Ac + Ac.T)
        self.lu = spla.splu(Ac.tocsc(), permc_spec="MMD_AT_PLUS_A", diag_pivot_thresh=0.0,
                            options=dict(SymmetricMode=True))
        # λmax(D⁻¹K) por potencia
        rng = np.random.default_rng(0)
        x = rng.standard_normal(K.shape[0])
        lam = 1.0
        for _ in range(15):
            y = self.Dinv * (K @ x)
            lam = np.linalg.norm(y) / np.linalg.norm(x)
            x = y / np.linalg.norm(y)
        self.b = 1.2 * lam
        self.a = self.b / 25.0
        self.deg = cheb_deg
        self.setup_s = time.time() - t0
        self.nc = Ac.shape[0]

    def smooth(self, r):
        K, Dinv = self.K, self.Dinv
        theta, delta = (self.b + self.a) / 2, (self.b - self.a) / 2
        sigma = theta / delta
        rho = 1 / sigma
        x = np.zeros_like(r)
        d = Dinv * r / theta
        res = r
        for k in range(self.deg):
            x = x + d
            if k == self.deg - 1:
                break
            res = res - K @ d
            rho_n = 1 / (2 * sigma - rho)
            d = rho_n * rho * d + 2 * rho_n / delta * Dinv * res
            rho = rho_n
        return x

    def __call__(self, r):
        x = self.smooth(r)
        res = r - self.K @ x
        x = x + self.P @ self.lu.solve(self.PT @ res)
        res = r - self.K @ x
        return x + self.smooth(res)


def solve_spd(K, f, fixed=None, P=None, x0=None, rtol=1e-8, maxiter=2000, pre=None):
    """Resuelve K u = f con gdl fijos (=0). Devuelve u (completo), info, precondicionador."""
    n = K.shape[0]
    free = np.ones(n, bool)
    if fixed is not None and len(fixed):
        free[np.asarray(fixed)] = False
    fi = np.flatnonzero(free)
    Kff = K[fi][:, fi].tocsr()
    ff = f[fi]
    if pre is None:
        pre = TwoLevel(Kff, P[fi] if P is not None else sp.identity(len(fi), format="csr"))
    M = spla.LinearOperator(Kff.shape, matvec=pre, dtype=float)
    it = [0]

    def cb(_):
        it[0] += 1
    t0 = time.time()
    xf, flag = spla.cg(Kff, ff, x0=None if x0 is None else x0[fi], rtol=rtol, atol=0.0,
                       maxiter=maxiter, M=M, callback=cb)
    res = np.linalg.norm(Kff @ xf - ff) / max(np.linalg.norm(ff), 1e-30)
    u = np.zeros(n)
    u[fi] = xf
    return u, {"cg_iters": it[0], "cg_flag": int(flag), "rel_res": float(res),
               "solve_s": time.time() - t0, "setup_s": pre.setup_s, "n_coarse": pre.nc}, pre
