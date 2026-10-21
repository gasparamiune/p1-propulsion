"""FEA3D mesher: one CAD instance (BREP, engine frame, mm) -> straight-sided C3D10 mesh + boundary faces tagged by CAD surface.

Author: fea3d (Senior FEA analyst 3D), 2026-10-13.  Independent of Mechanical's fe_util (ideas reused, code rewritten).
Output npz per body: X (n,3) mm; T10 (e,10) CalculiX C3D10 order; boundary faces bf_e (element index), bf_f (ccx face 1..4),
bf_ent (gmsh/OCC surface tag), bf_n (6 nodes: 3 corners in ccx face order + 3 mid nodes); ent (json: per surface tag type, area,
centroid, bbox, cylinder radius/axis when the surface is a cylinder); quality (gmsh minSICN).
Second-order nodes are straight-sided (Mesh.SecondOrderLinear = 1): the exact barycentric load integrals of fea3d use it.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

PERM_TET10 = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]          # gmsh tet10 -> ccx C3D10 (verified by Mechanical's cantilever, fe_util)
TET_FACES = {1: (0, 1, 2), 2: (0, 3, 1), 3: (1, 3, 2), 4: (2, 3, 0)}
FACE_MID = {1: (4, 5, 6), 2: (7, 8, 4), 3: (8, 9, 5), 4: (9, 7, 6)}


def mesh_brep(brep, hmax, hmin, curv_n=12, solid_index=None, verbose=False, threads=2, opt_netgen=False, ext=0, balls=None, surf=None):
    import gmsh
    t0 = time.time()
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
    gmsh.option.setNumber("General.NumThreads", threads)
    gmsh.model.add("b")
    gmsh.model.occ.importShapes(str(brep))
    gmsh.model.occ.synchronize()
    vols = gmsh.model.getEntities(3)
    if solid_index is not None:
        keep = [vols[solid_index]]
        rem = [v for v in vols if v not in keep]
        if rem:
            gmsh.model.occ.remove(rem, recursive=True)
            gmsh.model.occ.synchronize()
        vols = gmsh.model.getEntities(3)
    gmsh.option.setNumber("Mesh.MeshSizeMax", hmax)
    surf_spec = list(surf or [])          # (the name 'surf' is reused below for the surface-triangle dict)
    hloc = [b[4] for b in (balls or [])] + [float(sd["h"]) for sd in surf_spec]
    gmsh.option.setNumber("Mesh.MeshSizeMin", hmin if not hloc else min(hmin, min(hloc)))
    fids, surf_rec = [], []
    if balls:   # local refinement (convergence study): Ball fields (centre x y z, radius r, size h) with a transition of r
        for (bx, by, bz, br, bh) in balls:
            f = gmsh.model.mesh.field.add("Ball")
            for k, v in (("XCenter", bx), ("YCenter", by), ("ZCenter", bz), ("Radius", br), ("VIn", bh), ("VOut", 1e22), ("Thickness", br)):
                gmsh.model.mesh.field.setNumber(f, k, v)
            fids.append(f)
    if surf_spec:    # 2026-10-20 (v3.5.2 rev 3 lever roots): size h on selected CAD faces (matched by centre of mass within tol), growing
        # linearly to hout between the distances dmin and dmax (gmsh Distance + Threshold, no constraint beyond dmax)
        coms = {int(t): np.asarray(gmsh.model.occ.getCenterOfMass(2, t)) for _, t in gmsh.model.getEntities(2)}
        for sd in surf_spec:
            tags, errs = [], []
            for c in sd["faces_c"]:
                t = min(coms, key=lambda q: float(np.linalg.norm(coms[q] - np.asarray(c, float))))
                e = float(np.linalg.norm(coms[t] - np.asarray(c, float)))
                if e > float(sd.get("tol", 0.05)):
                    gmsh.finalize()
                    raise RuntimeError(f"surf refinement: no CAD face with centre of mass at {c} (closest {e:.3f} mm)")
                tags.append(t)
                errs.append(round(e, 5))
            fd = gmsh.model.mesh.field.add("Distance")
            gmsh.model.mesh.field.setNumbers(fd, "SurfacesList", tags)
            gmsh.model.mesh.field.setNumber(fd, "Sampling", int(sd.get("sampling", 150)))
            ft = gmsh.model.mesh.field.add("Threshold")
            for k, v in (("InField", fd), ("SizeMin", float(sd["h"])), ("SizeMax", float(sd["hout"])), ("DistMin", float(sd["dmin"])),
                         ("DistMax", float(sd["dmax"])), ("StopAtDistMax", 1)):
                gmsh.model.mesh.field.setNumber(ft, k, v)
            fids.append(ft)
            surf_rec.append({"tags": tags, "com_err_mm": errs})
    if fids:
        fm = gmsh.model.mesh.field.add("Min")
        gmsh.model.mesh.field.setNumbers(fm, "FieldsList", fids)
        gmsh.model.mesh.field.setAsBackgroundMesh(fm)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", curv_n)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", ext)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 1 if opt_netgen else 0)
    alg_used = None
    for a2, a3 in ((6, 10), (6, 1), (1, 10), (1, 1), (5, 1), (8, 1)):   # HXT fails on some BREPs (intersecting PLC segments)
        gmsh.model.mesh.clear()
        gmsh.option.setNumber("Mesh.Algorithm", a2)
        gmsh.option.setNumber("Mesh.Algorithm3D", a3)
        try:
            gmsh.model.mesh.generate(3)
        except Exception:
            continue
        ok = any(len(gmsh.model.mesh.getElements(3, t)[0]) for _, t in vols)
        if ok:
            alg_used = (a2, a3)
            break
    if alg_used is None:
        gmsh.finalize()
        raise RuntimeError(f"gmsh failed on {brep} with every algorithm pair")
    ntag, xyz, _ = gmsh.model.mesh.getNodes()
    X = xyz.reshape(-1, 3)
    conn = []
    for dim, tag in vols:
        et, el, en = gmsh.model.mesh.getElements(3, tag)
        for a, b in zip(et, en):
            if a == 11:
                conn.append(np.asarray(b, dtype=np.int64).reshape(-1, 10))
    conn = np.vstack(conn)
    # quality
    etags = []
    for dim, tag in vols:
        et, el, en = gmsh.model.mesh.getElements(3, tag)
        for a, b in zip(et, el):
            if a == 11:
                etags.append(np.asarray(b))
    etags = np.concatenate(etags)
    q = np.asarray(gmsh.model.mesh.getElementQualities(etags, "minSICN"))
    # surfaces
    surf = {}
    for dim, tag in gmsh.model.getEntities(2):
        et, el, en = gmsh.model.mesh.getElements(2, tag)
        tri = None
        for a, b in zip(et, en):
            if a == 9:
                tri = np.asarray(b, dtype=np.int64).reshape(-1, 6)
        if tri is None:
            continue
        info = {"type": gmsh.model.getType(2, tag), "area": float(gmsh.model.occ.getMass(2, tag)),
                "centroid": [float(c) for c in gmsh.model.occ.getCenterOfMass(2, tag)],
                "bbox": [float(c) for c in gmsh.model.getBoundingBox(2, tag)]}
        if info["type"] in ("Cylinder", "Cone", "Plane", "Torus", "Sphere"):
            try:
                pb = gmsh.model.getParametrizationBounds(2, tag)
                uv = [0.5 * (pb[0][0] + pb[1][0]), 0.5 * (pb[0][1] + pb[1][1])]
                p = np.asarray(gmsh.model.getValue(2, tag, uv))
                nrm = np.asarray(gmsh.model.getNormal(tag, uv))
                kmax, kmin, dmax, dmin = gmsh.model.getPrincipalCurvatures(tag, uv)
                info["normal_mid"] = [float(c) for c in nrm]
                info["kmax"], info["kmin"] = float(kmax[0]), float(kmin[0])
                if info["type"] == "Cylinder":
                    k = max(abs(kmax[0]), abs(kmin[0]))
                    R = 1.0 / k if k > 1e-12 else float("inf")
                    # axis = direction of the zero principal curvature
                    dmx, dmn = np.asarray(dmax), np.asarray(dmin)
                    ax = dmn if abs(kmin[0]) < abs(kmax[0]) else dmx
                    ax = ax / np.linalg.norm(ax)
                    # point on the axis: p - R * n_outward_of_cylinder; use the sign that lands on the axis
                    n_ = nrm / np.linalg.norm(nrm)
                    c1, c2 = p - R * n_, p + R * n_
                    # pick the one equidistant from 3 surface nodes
                    info["R"] = float(R)
                    info["axis"] = [float(c) for c in ax]
                    info["axis_pt_cand"] = [[float(c) for c in c1], [float(c) for c in c2]]
            except Exception as ex:  # noqa: BLE001
                info["param_error"] = str(ex)
        surf[int(tag)] = (tri, info)
    gmsh.finalize()
    # compact numbering
    used = np.unique(conn)
    idx = -np.ones(int(ntag.max()) + 1, dtype=np.int64)
    idx[ntag.astype(np.int64)] = np.arange(len(ntag))
    Xc = X[idx[used]]
    remap = -np.ones(int(ntag.max()) + 1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    T10 = remap[conn][:, PERM_TET10]
    # boundary faces of the tet mesh
    F = []
    for f, (i, j, k) in TET_FACES.items():
        F.append(np.stack([T10[:, i], T10[:, j], T10[:, k], np.arange(len(T10)), np.full(len(T10), f)], axis=1))
    F = np.vstack(F)
    key = np.sort(F[:, :3], axis=1)
    order = np.lexsort(key.T[::-1])
    ks = key[order]
    same_next = np.all(ks[1:] == ks[:-1], axis=1)
    cnt = np.ones(len(ks), dtype=np.int64)
    dup = np.zeros(len(ks), bool)
    dup[1:] |= same_next
    dup[:-1] |= same_next
    bnd = order[~dup]
    bkey = {tuple(key[i]): (int(F[i, 3]), int(F[i, 4])) for i in bnd}
    bf_e, bf_f, bf_ent, bf_n = [], [], [], []
    ent_out = {}
    missing = 0
    for tag, (tri, info) in surf.items():
        tri_c = remap[tri]
        ent_out[tag] = info
        for t in tri_c:
            kk = tuple(sorted(t[:3]))
            if kk not in bkey:
                missing += 1
                continue
            e, f = bkey[kk]
            bf_e.append(e)
            bf_f.append(f)
            bf_ent.append(tag)
            bf_n.append([T10[e, c] for c in TET_FACES[f]] + [T10[e, c] for c in FACE_MID[f]])
    # resolve cylinder axis points with the mesh nodes
    bf_ent_a = np.asarray(bf_ent)
    bf_n_a = np.asarray(bf_n, dtype=np.int64)
    for tag, info in ent_out.items():
        if "axis_pt_cand" in info:
            nodes = np.unique(bf_n_a[bf_ent_a == tag][:, :3])
            P = Xc[nodes]
            ax = np.asarray(info["axis"])
            best = None
            for c in info["axis_pt_cand"]:
                v = P - np.asarray(c)
                d = np.linalg.norm(v - np.outer(v @ ax, ax), axis=1)
                err = float(np.abs(d - info["R"]).max())
                if best is None or err < best[0]:
                    best = (err, c)
            info["axis_pt"] = best[1]
            info["fit_err"] = best[0]
            s = (P - np.asarray(best[1])) @ ax
            info["s_range"] = [float(s.min()), float(s.max())]
            del info["axis_pt_cand"]
    meta = {"brep": str(brep), "hmax": hmax, "hmin": hmin, "curv_n": curv_n, "solid_index": solid_index, "ext": ext, "alg3d": alg_used, "netgen": bool(opt_netgen),
            "balls": [list(map(float, b)) for b in (balls or [])],
            "surf": [dict(sd, **rec) for sd, rec in zip(surf_spec, surf_rec)],
            "n_nodes": int(len(Xc)), "n_tets": int(len(T10)), "n_bfaces": int(len(bf_e)), "unmatched_surface_tris": int(missing),
            "n_boundary_faces_tet": int(len(bnd)), "q_min": float(q.min()), "q_p01": float(np.percentile(q, 1)),
            "n_q_below_0.1": int((q < 0.1).sum()), "t_s": round(time.time() - t0, 1)}
    return dict(X=Xc, T10=T10.astype(np.int64), bf_e=np.asarray(bf_e, np.int64), bf_f=np.asarray(bf_f, np.int64),
                bf_ent=bf_ent_a.astype(np.int64), bf_n=bf_n_a, ent=json.dumps({str(k): v for k, v in ent_out.items()}),
                meta=json.dumps(meta))


def tet_volumes(X, T10):
    a, b, c, d = (X[T10[:, k]] for k in range(4))
    return np.einsum("ij,ij->i", np.cross(b - a, c - a), d - a) / 6.0


def cached_mesh(brep, out, hmax, hmin, curv_n=12, solid_index=None, force=False, ext=0, **kw):
    out = Path(out)
    if out.exists() and not force:
        z = np.load(out, allow_pickle=False)
        m = json.loads(str(z["meta"]))
        same_balls = m.get("balls", []) == [list(map(float, b)) for b in (kw.get("balls") or [])]
        same_surf = [{k: v for k, v in sd.items() if k not in ("tags", "com_err_mm")} for sd in m.get("surf", [])] == \
            json.loads(json.dumps(kw.get("surf") or []))
        if m["hmax"] == hmax and m["hmin"] == hmin and m["curv_n"] == curv_n and m["solid_index"] == solid_index and m.get("ext", 1) == ext \
                and same_balls and same_surf:
            return {k: z[k] for k in z.files}
    d = mesh_brep(brep, hmax, hmin, curv_n, solid_index, ext=ext, **kw)
    v = tet_volumes(d["X"], d["T10"])
    m = json.loads(d["meta"])
    m["volume_mm3"] = float(v.sum())
    m["n_inverted"] = int((v <= 0).sum())
    d["meta"] = json.dumps(m)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, **d)
    return d


if __name__ == "__main__":
    brep, out, hmax, hmin = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    curv = int(sys.argv[5]) if len(sys.argv) > 5 else 12
    si = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] != "-" else None
    d = cached_mesh(brep, out, hmax, hmin, curv, si, force=True)
    print(d["meta"])
