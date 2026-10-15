"""Small FE utilities for the CalculiX stiffness models (04-fea/stiffness, v1 2026-10-12, Mechanical).

* mesh_shape(): CadQuery solid -> BREP -> gmsh (OCC) -> 10-node tetrahedra (C3D10), coordinates in mm.
* surface_faces(): boundary faces of a tet10 mesh (element id, CalculiX face label) whose corner nodes satisfy a predicate.
* parse_dat(): node/element results printed by *NODE PRINT / *EL PRINT, per step.

Node order: gmsh tet10 (corners 0-3; edges 01,12,20,30,32,31) -> CalculiX C3D10 (edges 12,23,31,14,24,34) is
[0,1,2,3,4,5,6,7,9,8]; verified on a 100 x 10 x 10 mm cantilever (tip deflection 0.05715 mm vs Euler-Bernoulli
0.05714 mm, torsion 2.626e-3 rad vs 2.634e-3 rad) in runs/stiff/test (2026-10-12).
"""
from __future__ import annotations
import os, re, subprocess, tempfile, time
from pathlib import Path
import numpy as np

PERM_TET10 = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]
TET_FACES = {1: (0, 1, 2), 2: (0, 3, 1), 3: (1, 3, 2), 4: (2, 3, 0)}     # CalculiX C3D10 face -> corner indices


def mesh_shape(shape, h, hmin=None, name="body", curv_n=10, workdir=None, verbose=False):
    """Tet10 mesh of a CadQuery shape.  h: max element size (mm); hmin: min size; curv_n: elements per 2*pi of curvature."""
    import gmsh
    workdir = Path(workdir or tempfile.mkdtemp())
    brep = workdir / f"{name}.brep"
    shape.exportBrep(str(brep))
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
    gmsh.option.setNumber("General.NumThreads", 2)
    gmsh.model.add(name)
    gmsh.model.occ.importShapes(str(brep))
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeMin", hmin if hmin else h / 6.0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", curv_n)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)
    gmsh.option.setNumber("Mesh.HighOrderOptimize", 0)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)          # Delaunay
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.model.mesh.generate(3)
    tags, coords, _ = gmsh.model.mesh.getNodes()
    X = coords.reshape(-1, 3)
    etypes, etags, enodes = gmsh.model.mesh.getElements(3)
    conn = None
    for et, en in zip(etypes, enodes):
        if et == 11:                                     # 10-node tetrahedron
            conn = np.array(en, dtype=np.int64).reshape(-1, 10)
    gmsh.finalize()
    if conn is None:
        raise RuntimeError(f"no tet10 elements for {name}")
    # compact numbering 0..N-1
    used = np.unique(conn)
    idx = -np.ones(int(tags.max()) + 1, dtype=np.int64)
    idx[tags.astype(np.int64)] = np.arange(len(tags))
    Xc = X[idx[used]]
    remap = -np.ones(int(tags.max()) + 1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    conn = remap[conn][:, PERM_TET10]
    return Xc, conn


def mesh_multi(shapes, h, hmin=None, name="multi", curv_n=10, workdir=None, verbose=False, ho_opt=2):
    """Conforming tet10 mesh of several touching CadQuery solids (gmsh OCC fragment -> shared interface nodes = bonded).
    Returns X (mm), conn (CalculiX order), body (index into shapes per element, by the centroid of each gmsh volume)."""
    import gmsh
    import cadquery as cq
    workdir = Path(workdir or tempfile.mkdtemp())
    brep = workdir / f"{name}.brep"
    cq.Compound.makeCompound(list(shapes)).exportBrep(str(brep))
    cents = [np.array(s.Center().toTuple()) for s in shapes]
    vols = [s.Volume() for s in shapes]
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
    gmsh.option.setNumber("General.NumThreads", 2)
    gmsh.model.add(name)
    gmsh.model.occ.importShapes(str(brep))
    gmsh.model.occ.synchronize()
    ents = gmsh.model.getEntities(3)
    if len(ents) > 1:
        gmsh.model.occ.fragment(ents[:1], ents[1:])
        gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeMin", hmin if hmin else h / 6.0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", curv_n)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.option.setNumber("Mesh.HighOrderOptimize", ho_opt)       # 2: elastic + optimisation (untangles curved tet10 on small radii)
    gmsh.model.mesh.generate(3)
    tags, coords, _ = gmsh.model.mesh.getNodes()
    X = coords.reshape(-1, 3)
    conns, bodies = [], []
    for dim, tag in gmsh.model.getEntities(3):
        c = np.array(gmsh.model.occ.getCenterOfMass(dim, tag))
        v = gmsh.model.occ.getMass(dim, tag)
        k = int(np.argmin([np.linalg.norm(c - cc) + abs(v - vv) / max(vv, 1e-9) for cc, vv in zip(cents, vols)]))
        etypes, etags, enodes = gmsh.model.mesh.getElements(3, tag)
        for et, en in zip(etypes, enodes):
            if et == 11:
                cc_ = np.array(en, dtype=np.int64).reshape(-1, 10)
                conns.append(cc_)
                bodies.append(np.full(len(cc_), k))
    gmsh.finalize()
    conn = np.vstack(conns)
    body = np.concatenate(bodies)
    used = np.unique(conn)
    idx = -np.ones(int(tags.max()) + 1, dtype=np.int64)
    idx[tags.astype(np.int64)] = np.arange(len(tags))
    Xc = X[idx[used]]
    remap = -np.ones(int(tags.max()) + 1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    conn = remap[conn][:, PERM_TET10]
    return Xc, conn, body


FACE_MID = {1: (4, 5, 6), 2: (7, 8, 4), 3: (8, 9, 5), 4: (9, 7, 6)}   # C3D10 face -> mid-side node indices (edges in face order)


def face_vector_area(X, conn, e, f):
    """Exact vector area of a 6-node (quadratic) triangular face: integral of x_xi x x_eta (3-point rule, degree 2)."""
    c = [conn[e, k] for k in TET_FACES[f]] + [conn[e, k] for k in FACE_MID[f]]
    P = X[c]                                         # corners 0,1,2 ; mids 01, 12, 20
    out = np.zeros(3)
    for (xi, eta) in ((1 / 6, 1 / 6), (2 / 3, 1 / 6), (1 / 6, 2 / 3)):
        L0 = 1 - xi - eta
        dN_dxi = np.array([-(4 * L0 - 1), 4 * xi - 1, 0.0, 4 * (L0 - xi), 4 * eta, -4 * eta])
        dN_deta = np.array([-(4 * L0 - 1), 0.0, 4 * eta - 1, -4 * xi, 4 * xi, 4 * (L0 - eta)])
        out += np.cross(dN_dxi @ P, dN_deta @ P) / 6.0
    return out


def components(conn, n_nodes):
    """Number of connected element groups (shared corner nodes) and the element label per group."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    c = conn[:, :4]
    rows = np.repeat(np.arange(len(c)), 4)
    A = coo_matrix((np.ones(rows.size), (rows, c.ravel())), shape=(len(c), n_nodes)).tocsr()
    G = A @ A.T
    nc, lab = connected_components(G, directed=False)
    return nc, lab


def tet_volumes(X, conn):
    a, b, c, d = (X[conn[:, k]] for k in range(4))
    return np.einsum("ij,ij->i", np.cross(b - a, c - a), d - a) / 6.0


def surface_faces(conn, pred_nodes):
    """Boundary faces (elem index, face label) whose 3 corner nodes all satisfy pred_nodes (bool array over nodes)."""
    keys = {}
    for e in range(conn.shape[0]):
        for f, (i, j, k) in TET_FACES.items():
            key = tuple(sorted((conn[e, i], conn[e, j], conn[e, k])))
            keys.setdefault(key, []).append((e, f))
    out = []
    for key, lst in keys.items():
        if len(lst) == 1 and all(pred_nodes[n] for n in key):
            out.append(lst[0])
    return out


def boundary_nodes(conn):
    keys = {}
    for e in range(conn.shape[0]):
        for f, (i, j, k) in TET_FACES.items():
            key = tuple(sorted((conn[e, i], conn[e, j], conn[e, k])))
            keys[key] = keys.get(key, 0) + 1
    nodes = set()
    for key, c in keys.items():
        if c == 1:
            nodes.update(key)
    # add mid-side nodes of boundary faces
    return np.array(sorted(nodes), dtype=np.int64)


def write_lines(f, ids, per=12):
    ids = list(ids)
    for i in range(0, len(ids), per):
        f.write(", ".join(str(int(x)) for x in ids[i:i + per]) + "\n")


def run_ccx(job, workdir, threads=2, timeout=7200):
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), CCX_NPROC_EQUATION_SOLVER=str(threads), CCX_NPROC_STIFFNESS=str(threads))
    t0 = time.time()
    r = subprocess.run(["ccx", "-i", job], cwd=str(workdir), env=env, capture_output=True, text=True, timeout=timeout)
    (Path(workdir) / f"{job}.log").write_text(r.stdout + "\n" + r.stderr)
    err = [l for l in r.stdout.splitlines() if "*ERROR" in l]
    return {"seconds": round(time.time() - t0, 1), "errors": err, "returncode": r.returncode}


def parse_dat(path):
    """{time: {"U": {node: [ux,uy,uz]}, "NT": {node: T}, "ETOT": {set: energy}}} from a CalculiX .dat file
    (*NODE PRINT U/NT and *EL PRINT ..., TOTALS=ONLY with ELSE)."""
    out = {}
    lines = Path(path).read_text().splitlines()
    kind, key, cur = None, None, None
    pend_set = None
    for line in lines:
        m = re.search(r"(total internal energy|displacements|temperatures)\s.*for set\s+(\S+)\s+and time\s+([0-9.E+-]+)", line)
        if m:
            t = float(m.group(3))
            cur = out.setdefault(t, {})
            if m.group(1) == "total internal energy":
                kind, pend_set = "ETOT", m.group(2)
                key = cur.setdefault("ETOT", {})
            else:
                kind = {"displacements": "U", "temperatures": "NT"}[m.group(1)]
                key = cur.setdefault(kind, {})
            continue
        p = line.split()
        if not p or key is None:
            continue
        try:
            vals = [float(x) for x in p]
        except ValueError:
            kind, key = None, None
            continue
        if kind == "ETOT":
            if len(vals) == 1 and pend_set is not None:
                key[pend_set] = vals[0]
                pend_set = None
        elif kind in ("U", "NT") and float(p[0]).is_integer():
            key[int(p[0])] = vals[1:] if len(vals) > 2 else vals[1]
    return out
