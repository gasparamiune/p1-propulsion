"""Thermal-mesh geometry per part in the head-top-aligned frame (z - TC-02 top), for every thermal run used by an S-AX table, against the
structural meshes (v3.5 cache mesh L1 and v3.5.1 mesh).  Tells whether a thermal run was built on a different geometry generation."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/04-fea/structural")
RT = Path("/home/claude/work/mechanical/runs/thermal")
RS = Path("/home/claude/work/mechanical/runs/structural")
def tri_props(X, E):
    # CAX6: corner nodes 0..2; area/centroid from the 4 linear sub-triangles
    out = {}
    sub = np.vstack([E[:, [0, 3, 5]], E[:, [3, 1, 4]], E[:, [5, 4, 2]], E[:, [3, 4, 5]]])
    a, b, c = X[sub[:, 0]], X[sub[:, 1]], X[sub[:, 2]]
    A = 0.5 * np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1]))
    C = (a + b + c) / 3.0
    return float(A.sum()), (A[:, None] * C).sum(0) / A.sum()
def per_part(X, E, pn, parts, ztop):
    res = {}
    for p in parts:
        Ep = E[pn == p]
        if not len(Ep):
            continue
        nodes = np.unique(Ep)
        A, c = tri_props(X, Ep)
        res[p] = {"area": round(A, 3), "r_c": round(c[0], 4), "z_c_rel": round(c[1] - ztop, 4),
                  "z_min_rel": round(X[nodes, 1].min() - ztop, 4), "z_max_rel": round(X[nodes, 1].max() - ztop, 4),
                  "r_min": round(X[nodes, 0].min(), 4), "r_max": round(X[nodes, 0].max(), 4)}
    return res
PARTS = ["ENG-TC-01", "ENG-TC-02", "ENG-TC-03", "ENG-TC-04", "ENG-TC-09", "ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-03", "ENG-NZ-04"]
out = {}
for k, f in {"struct_v3.5_L1": RS / "L1" / "mesh.npz", "struct_v3.5.1": RS / "L1_thv351_TB1GC_cad351" / "mesh.npz"}.items():
    z = np.load(f, allow_pickle=True)
    X, E, pn = z["X"], z["E"], z["pn"]
    ztop = X[np.unique(E[pn == "ENG-TC-02"]), 1].max()
    out[k] = per_part(X, E, pn, PARTS, ztop)
for t in ["DC-B1v3p99_tg711_hi_SS316L_L2.5_v13pre36IN_J1revB", "DC-A1dispp99_tg711_hi_SS316L_L2.5_v13pre36IN_J1revB",
          "DC-B1v3p99_tg711_hi_SS316L_L2.5_v13pre36IN_J1revB_TC09IN", "DC-A1dispp99_tg711_hi_SS316L_L2.5_v13pre36IN_J1revB_TC09IN",
          "DC-B1v3p99_tg711_hi_SS316L_L2.5_v13pre36IN_J2revB", "DC-A1dispp99_tg711_hi_SS316L_L2.5_v13pre36IN_J2revB",
          "DC-B1v3p99_tg711_hi_SS316L_L2.5_v351_TB1GC", "DC-A1dispp99_tg711_hi_SS316L_L2.5_v351_TB1GC"]:
    z = np.load(RT / t / "envelope_nodes.npz", allow_pickle=True)
    X, E, pn = z["X"], z["E"], z["pn"]
    ztop = X[np.unique(E[pn == "ENG-TC-02"]), 1].max()
    out[t] = per_part(X, E, pn, PARTS, ztop)
    out[t]["_nodes"] = int(len(X)); out[t]["_elements"] = int(len(E)); out[t]["_ztop"] = round(float(ztop), 4)
json.dump(out, open("/home/claude/work/mechanical/v351/prov/thermal_geom_compare_v1.json", "w"), indent=1)
ref = out["struct_v3.5_L1"]
for k, v in out.items():
    print("==", k, v.get("_nodes"), v.get("_elements"), v.get("_ztop"))
    for p in PARTS:
        a, r = v.get(p), ref[p]
        if not a:
            continue
        print(f"  {p:10s} A {a['area']:9.3f} (d {a['area']-r['area']:+7.3f}) rc {a['r_c']:7.3f} (d {a['r_c']-r['r_c']:+6.3f}) zc {a['z_c_rel']:9.3f} (d {a['z_c_rel']-r['z_c_rel']:+6.3f})"
              f" zmin {a['z_min_rel']:9.3f} (d {a['z_min_rel']-r['z_min_rel']:+6.3f}) zmax {a['z_max_rel']:9.3f} (d {a['z_max_rel']-r['z_max_rel']:+6.3f}) rmax d {a['r_max']-r['r_max']:+6.3f}")
