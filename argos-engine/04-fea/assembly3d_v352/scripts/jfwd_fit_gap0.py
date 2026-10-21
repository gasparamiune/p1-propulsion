"""Read-only geometric check (CPRESS audit / t1 finding): initial radial gap of every FIT slave node (TC-02 OD) to the master faces
(TC-01 bore) in the UNDEFORMED mesh, for meshes t1 and s4.  Master face = the quadratic 6-node triangle (corners + midside nodes as
meshed), triangulated into its 4 linear sub-triangles; ray along e_r(az) of the slave node."""
import sys, json
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import numpy as np
import jfwd_deck as JD

def gaps(tag):
    m = dict(np.load(JD.OUT / f"model_{tag}.npz"))
    X = m["X"]
    fs, fm = m["fit_s"], m["fit_m"]
    sn = np.unique(np.concatenate([m["fcn"][fs].ravel(), m["fmn"][fs].ravel()]))
    c, mm = m["fcn"][fm], m["fmn"][fm]
    # which slave side is TC-02?  report radii of both sides
    rs = np.hypot(X[sn, 0], X[sn, 1])
    rmn = np.hypot(X[np.unique(c.ravel()), 0], X[np.unique(c.ravel()), 1])
    rmm = np.hypot(X[np.unique(mm.ravel()), 0], X[np.unique(mm.ravel()), 1])
    # sub-triangles: midside order per ccx C3D10 face: m01, m12, m20 (assumed as stored); test both orders by the edge midpoint match
    tris = []
    for k in range(len(c)):
        a, b, d = c[k]
        mids = mm[k]
        # identify which midside belongs to which edge by distance to edge midpoints
        E = {(0, 1): 0.5 * (X[a] + X[b]), (1, 2): 0.5 * (X[b] + X[d]), (2, 0): 0.5 * (X[d] + X[a])}
        lab = {}
        for e, pm in E.items():
            j = int(np.argmin([np.linalg.norm(X[q] - pm) for q in mids]))
            lab[e] = mids[j]
        m01, m12, m20 = lab[(0, 1)], lab[(1, 2)], lab[(2, 0)]
        tris += [(a, m01, m20), (m01, b, m12), (m20, m12, d), (m01, m12, m20)]
    tris = np.array(tris)
    P0, P1, P2 = X[tris[:, 0]], X[tris[:, 1]], X[tris[:, 2]]
    cen = (P0 + P1 + P2) / 3
    out = []
    for n in sn:
        P = X[n]
        az = np.arctan2(P[1], P[0]); er = np.array([np.cos(az), np.sin(az), 0.0])
        near = np.nonzero(np.linalg.norm(cen - P, axis=1) < 6.0)[0]
        best = None
        for t in near:
            p0, p1, p2 = P0[t], P1[t], P2[t]
            e1, e2 = p1 - p0, p2 - p0
            h = np.cross(er, e2); det = e1 @ h
            if abs(det) < 1e-12:
                continue
            s = P - p0; u = (s @ h) / det
            q = np.cross(s, e1); v = (er @ q) / det
            if u < -1e-9 or v < -1e-9 or u + v > 1 + 1e-9:
                continue
            tt = (e2 @ q) / det          # P + tt*er hits the triangle
            if best is None or abs(tt) < abs(best):
                best = tt
        if best is not None:
            out.append(best)
    g = np.array(out)
    # midside-node radial offsets from the corner chord (tells straight-sided vs curved)
    return {"mesh": tag, "slave_nodes": int(len(sn)), "hit": int(len(g)), "slave_r_min_max": [round(float(rs.min()), 4), round(float(rs.max()), 4)],
            "master_corner_r_min_max": [round(float(rmn.min()), 4), round(float(rmn.max()), 4)],
            "master_mid_r_min_max": [round(float(rmm.min()), 4), round(float(rmm.max()), 4)],
            "gap_min_mm": round(float(g.min()), 4), "gap_mean_mm": round(float(g.mean()), 4), "gap_max_mm": round(float(g.max()), 4),
            "n_gap_le_0": int((g <= 0).sum()), "n_gap_lt_0.0125": int((g < 0.0125).sum()),
            "pct": {p: round(float(np.percentile(g, p)), 4) for p in (1, 5, 25, 50, 75, 95, 99)}}

res = {t: gaps(t) for t in ("t1", "s4")}
print(json.dumps(res, indent=1))
json.dump(res, open("/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/audit/fit_gap0.json", "w"), indent=1)
