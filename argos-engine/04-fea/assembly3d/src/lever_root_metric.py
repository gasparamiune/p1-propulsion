"""Lever-root refinement metric (fea3d 2026-10-19, REPORT 4.6): like-for-like stress at the GM-01 / GM-02 lever-root fillet zone.

For each run: envelope von Mises (lc3_env_<run>.npz from post_lc3.py) of the part within 3 mm of the peak point, excluding nodes within
ex = 0.25 / 0.5 / 1.0 mm of a FIXED edge line (the re-entrant-edge nodes that the detector flags on the reference run), so the exclusion
does not change with the mesh; plus the local mean tet edge h and the regular-set MS from the post JSON.
usage: lever_root_metric.py PART X,Y,Z EDGE_RUN RUN[,RUN...] OUT_JSON
"""
import sys, json, numpy as np
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF
from scipy.spatial import cKDTree

part, P, edge_run, runs, outp = sys.argv[1], np.array([float(v) for v in sys.argv[2].split(",")]), sys.argv[3], sys.argv[4].split(","), sys.argv[5]
Me, _ = PF.load_model(edge_run)
_, _, _, Xe = PF.node_arrays(Me, edge_run, "B1_21.65")
_, _, se = PF.singular_sets(Me, Xe, ex_r=1.0)
edge = Xe[se["reentrant_edges"]]
edge = edge[np.linalg.norm(edge - P, axis=1) < 6.0]
tree = cKDTree(edge)
res = {}
for run in runs:
    M, meta = PF.load_model(run)
    names, body, T, X = PF.node_arrays(M, run, "B1_21.65")
    e = np.load(PF.RES / f"lc3_env_{run}.npz")
    b = M.bodies[part]
    nodes = b.noff + np.arange(len(b.X0))
    d = np.linalg.norm(X[nodes] - P, axis=1)
    de, _ = tree.query(X[nodes])
    vm = e["vm"][nodes]
    near = np.nonzero(d < 1.0)[0]
    els = b.T10[np.isin(b.T10[:, :4], near).any(1)]
    ed = [np.linalg.norm(b.X0[t[i]] - b.X0[t[j]]) for t in els for i in range(4) for j in range(i + 1, 4)]
    js = json.loads((PF.RES / f"f1_post_lc3_{run}.json").read_text())
    rr = [m for m in js["margins"] if m["part"] == part and m["set"] == "regular"][0]
    row = {"h_loc_mm": float(np.mean(ed)) if ed else None, "MS_regular": rr["MS"], "MS_ult_regular": rr.get("MS_ult"), "vm_regular_MPa": rr["vm_MPa"],
           "vm_max_3mm_all": float(vm[d < 3.0].max())}
    for ex in (0.25, 0.5, 1.0):
        m = (d < 3.0) & (de > ex)
        row[f"vm_max_3mm_beyond_{ex}mm_of_edge"] = float(vm[m].max())
    res[run] = row
    print(run, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
json.dump({"part": part, "point_mm_posed": P.tolist(), "edge_reference_run": edge_run, "doc": __doc__.split("usage:")[0].strip(), "levels": res},
          open(outp, "w"), indent=1)
