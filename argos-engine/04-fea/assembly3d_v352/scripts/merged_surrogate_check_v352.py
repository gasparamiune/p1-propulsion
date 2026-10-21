"""Merged-map surrogate check (fea3d 2026-10-20 ~15:35Z; brief item 5b: "the merged-node field stays the perfect-contact bound").

No LC1 was solved on the v3.5.2 merged NF2b field: the perfect-contact side of item 5b is the interim run lc1v352, which maps the v3.5.1
merged S-AX field L1_thv351_TB1GC_cad351 onto the v3.5.2 model.  This script measures how far that surrogate is from the v3.5.2 merged
field L1_thv352_NF2b_cad352 on the parts item 5b re-posts (TC-02, TC-03; NZ-01 for the record: N-F2b changed the NZ-01 shoulder, so no
surrogate claim is made there): for every node of the part in the v3.5.2 S-AX mesh, T(NF2b merged) minus T(v3.5.1 merged) interpolated at
the same (r, z) on the v3.5.1 S-AX mesh (6-node triangles split in 4 linear ones; nearest v3.5.1 node of the part where the point is
outside the v3.5.1 part), at the four states B1_21.65 / B1_19 / B1_2 / B1_1; plus the two fields at the named points (TC-03 corner r 9.8
z 105.513, TC-02 seat r 6.5 z 107.513, TC-02 seat r 7.98 z 107.513, TC-02 forward-face hot corner r 24.85 z 103.513).
S-AX res.npz T in K.  Read-only on Mechanical's folders.  Evidence: SIM (Mechanical S-AX fields) + DERIVED (interpolation, differences).
usage: python -I -B merged_surrogate_check_v352.py -> results/v352/merged_surrogate_check_v352.json"""
from __future__ import annotations
import json, hashlib, time
from pathlib import Path
import numpy as np
import matplotlib.tri as mtri
from scipy.spatial import cKDTree

BASE = Path("/home/claude/work/mechanical/runs/structural")
NEW, OLD = BASE / "L1_thv352_NF2b_cad352", BASE / "L1_thv351_TB1GC_cad351"
STATES = ["B1_21.65", "B1_19", "B1_2", "B1_1"]
PARTS = ["ENG-TC-03", "ENG-TC-02", "ENG-NZ-01"]
POINTS = {"TC-03 corner (9.8, 105.513)": ("ENG-TC-03", 9.8, 105.5134), "TC-02 seat (6.5, 107.513)": ("ENG-TC-02", 6.5, 107.5134),
          "TC-02 seat (7.98, 107.513)": ("ENG-TC-02", 7.98, 107.5134), "TC-02 forward-face hot corner (24.85, 103.513)": ("ENG-TC-02", 24.85, 103.5134)}
OUT = Path("/home/claude/work/fea3d/results/v352/merged_surrogate_check_v352.json")


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()[:16]


class Sax:
    def __init__(self, d):
        m = np.load(d / "mesh.npz", allow_pickle=True)
        self.X, self.E, self.pn = m["X"], m["E"], m["pn"]
        self.part = {}
        for p in PARTS:
            Ep = self.E[self.pn == p]
            used = np.unique(Ep)
            rm = -np.ones(len(self.X), np.int64)
            rm[used] = np.arange(len(used))
            sub = rm[np.vstack([Ep[:, [0, 3, 5]], Ep[:, [3, 1, 4]], Ep[:, [5, 4, 2]], Ep[:, [3, 4, 5]]])]
            self.part[p] = (used, mtri.Triangulation(self.X[used, 0], self.X[used, 1], sub), cKDTree(self.X[used]))

    def at(self, p, T, r, z):
        used, tri, kd = self.part[p]
        v = mtri.LinearTriInterpolator(tri, T[used])(r, z)
        v = np.asarray(v.filled(np.nan) if hasattr(v, "filled") else v, float)
        miss = ~np.isfinite(v)
        if miss.any():
            _, ii = kd.query(np.column_stack([r[miss], z[miss]]))
            v[miss] = T[used][ii]
        return v, int(miss.sum())


def main():
    A, B = Sax(NEW), Sax(OLD)
    out = {"id": "merged_surrogate_check_v352", "date": time.strftime("%Y-%m-%d"), "owner": "fea3d", "doc": __doc__.split("usage:")[0].strip(),
           "new": {"dir": str(NEW), "mesh_sha16": sha16(NEW / "mesh.npz")}, "old": {"dir": str(OLD), "mesh_sha16": sha16(OLD / "mesh.npz")},
           "states": {}}
    for st in STATES:
        Ta = np.load(NEW / st / "res.npz")["T"]
        Tb = np.load(OLD / st / "res.npz")["T"]
        e = {"res_sha16": {"new": sha16(NEW / st / "res.npz"), "old": sha16(OLD / st / "res.npz")}, "parts": {}, "points": {}}
        for p in PARTS:
            used = A.part[p][0]
            r, z = A.X[used, 0], A.X[used, 1]
            tb, nmiss = B.at(p, Tb, r, z)
            dT = Ta[used] - tb
            i = int(np.argmax(np.abs(dT)))
            e["parts"][p] = {"n_nodes": int(len(used)), "n_outside_old_part": nmiss, "dT_max_abs_K": round(float(np.abs(dT).max()), 2),
                             "dT_at_max_abs_K": round(float(dT[i]), 2), "at_r_z_mm": [round(float(r[i]), 3), round(float(z[i]), 3)],
                             "dT_mean_K": round(float(dT.mean()), 2), "dT_p95_abs_K": round(float(np.percentile(np.abs(dT), 95)), 2),
                             "T_max_new_C": round(float(Ta[used].max()) - 273.15, 2), "T_max_old_C": round(float(Tb[B.part[p][0]].max()) - 273.15, 2)}
        for k, (p, r0, z0) in POINTS.items():
            ta, _ = A.at(p, Ta, np.array([r0]), np.array([z0]))
            tb, _ = B.at(p, Tb, np.array([r0]), np.array([z0]))
            e["points"][k] = {"T_new_C": round(float(ta[0]) - 273.15, 2), "T_old_C": round(float(tb[0]) - 273.15, 2),
                              "dT_K": round(float(ta[0] - tb[0]), 2)}
        out["states"][st] = e
        print(st, {p: (v["dT_max_abs_K"], v["dT_p95_abs_K"], v["at_r_z_mm"]) for p, v in e["parts"].items()}, flush=True)
        print("   ", e["points"], flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT, sha16(OUT))


if __name__ == "__main__":
    main()
