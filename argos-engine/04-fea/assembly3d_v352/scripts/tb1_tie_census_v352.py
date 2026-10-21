"""TB1 (TC-03 / TC-02) tie census on the v3.5.2 production model (fea3d 2026-10-20, item 5b / RM2-13 / CHANGELOG 234 (7)).
Builds the LC1 model exactly as lc1v352g (level 1, neutral pose, 'design' ties, TB1 'thread', tiex, conn v12; no deck, no solve) and lists,
for every tie between TC-03 and TC-02, the dependent nodes by location: shoulder plane, flange OD (r > 9.9 mm, across the 0.10 mm design
gap to the r 10.1 counterbore), end face (z 117.51), thread engagement (r 7.0).  Same census for the v3.5.1 'faces' variant
(TC03_TC02_seat) is RM2-13 (c): 183 shoulder + 46 OD + 71 end-face nodes.  [SIM model data; no FE result]
usage: FEA3D_CAD=v352 python -I -B tb1_tie_census_v352.py OUT.json"""
import os, sys, json, time, math
import numpy as np
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
os.environ.setdefault("FEA3D_CAD", "v352")
import asm_build as AB, asm3d as A3

t0 = time.time()
variant = {"conn": "v12", "ties": "design", "tb1": "thread", "tiex": True}
M = AB.Asm(level=1.0, variant=variant)
AB.define(M)
nn = M.next_n
X = np.zeros((nn + 1, 3))
for nm, b in M.bodies.items():
    X[b.noff:b.noff + len(b.X0)] = M.Xp[nm]
out = {"doc": __doc__.split("usage:")[0].strip(), "cad": A3.CAD, "variant": variant, "build_s": None, "ties": {}}
labs = [t["label"] for t in M.ties if t["dep"] == "TC-03" and t["ind"] == "TC-02"]
dep_nodes = {lab: set() for lab in labs}
for lab, terms in M.C.eqs:
    if lab in dep_nodes:
        dep_nodes[lab].add(int(terms[0][0]))
for lab in labs:
    nd = np.array(sorted(dep_nodes[lab]))
    P = X[nd]
    r = np.hypot(P[:, 0], P[:, 1])
    z = P[:, 2]
    rec = next(t for t in M.ties if t["label"] == lab)
    cls = {"flange_OD_r_gt_9.9": int((r > 9.9).sum()),
           "end_face_z_117.51": int((np.abs(z - 117.51) < 0.05).sum()),
           "thread_r_6.9_7.1": int(((r > 6.9) & (r < 7.1)).sum())}
    zs = sorted(set(np.round(z, 2).tolist()))
    out["ties"][lab] = {"record": rec, "n_dep_nodes_with_eq": int(len(nd)), "r_range_mm": [float(r.min()), float(r.max())],
                        "z_range_mm": [float(z.min()), float(z.max())], "n_distinct_z": len(zs), "z_levels_first": zs[:12], "classes": cls,
                        "r_hist_mm": {f"{a:.1f}-{b:.1f}": int(((r >= a) & (r < b)).sum()) for a, b in
                                      ((0, 6.9), (6.9, 7.1), (7.1, 9.0), (9.0, 9.9), (9.9, 10.2), (10.2, 99))}}
    print(lab, out["ties"][lab]["n_dep_nodes_with_eq"], "r", out["ties"][lab]["r_range_mm"], "z", out["ties"][lab]["z_range_mm"], cls, flush=True)
out["build_s"] = round(time.time() - t0, 1)
json.dump(out, open(sys.argv[1], "w"), indent=1, default=float)
print("wrote", sys.argv[1], out["build_s"], "s")
