#!/usr/bin/env python3
"""REV-MECH-1 (independent reviewer), 2026-10-13 - bay-wall sweep of the MOVING engine group, CAD v3.5.

Own code (no author module imported).  Geometry source: the author's published GLB ENGINE_v3.5_neutral.glb (tessellated,
deflection 0.1 mm per its read-back record), instance grouping from assembly_manifest_v3.5.json.  Frame conversion (README):
(x, y, z)_glTF = (x, z, -y)_engine / 1000  ->  engine mm: x_e = 1000 x_g, y_e = -1000 z_g, z_e = 1000 y_g.
Pose convention (as used by the author's poses; reviewer verified against combined045 a -4.962 / b 4.944 deg at 7 deg):
R = Rx(alpha) Ry(beta) about the pivot (origin); engine axis -> (sin b, -sin a cos b, cos a cos b); for cone angle th at azimuth phi:
sin b = sin th cos phi, sin a = -sin th sin phi / cos b.  Ring group: Rx(alpha) only (outer axis +X).  Horn/pushrod groups: not swept
(their kinematics are servo-driven; reported as not covered).
Wall: cylinder r = 70.0 mm about the airframe Z axis (140 mm bay, ICD-AIRFRAME / BOM GM-09 note); requirement used by the lead
(CHANGELOG 182): clearance >= 1.0 mm, i.e. r <= 69.0 mm, over a 72-direction sweep.
Tolerance: vertex-based max r under-estimates the exact surface by <= the tessellation sag (0.1 mm) -> results are +0/-0.1 mm.
Usage: python -I rm1_baywall_sweep.py <glb> <manifest_json> <out_json>
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

R_WALL = 70.0
R_REQ = 69.0


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(b):
    c, s = math.cos(b), math.sin(b)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def pose(th_deg, phi_deg):
    th, ph = math.radians(th_deg), math.radians(phi_deg)
    sb = math.sin(th) * math.cos(ph)
    b = math.asin(sb)
    sa = -math.sin(th) * math.sin(ph) / math.cos(b)
    a = math.asin(sa)
    return a, b


def main():
    glb, man, out = (Path(a) for a in sys.argv[1:4])
    M = json.loads(man.read_text())
    group = {i["inst"]: i["group"] for i in M["instances"]}
    sc = trimesh.load(str(glb), force="scene")
    V = {}
    for node in sc.graph.nodes_geometry:
        T, g = sc.graph[node]
        v = trimesh.transformations.transform_points(sc.geometry[g].vertices, T)
        V[node] = np.column_stack([1000.0 * v[:, 0], -1000.0 * v[:, 2], 1000.0 * v[:, 1]])
    missing = sorted(set(group) - set(V))
    eng = [k for k in V if group.get(k) == "engine"]
    ring = [k for k in V if group.get(k) == "ring"]
    # sanity: manifest bounds vs GLB-derived bounds (frame conversion check)
    bchk = []
    for i in M["instances"]:
        if i["inst"] in V:
            v = V[i["inst"]]
            b = np.r_[v.min(0), v.max(0)]
            bchk.append(float(np.max(np.abs(b - np.array(i["bounds_mm"])))))
    # pose check against the author's combined045
    a45, b45 = pose(7.0, 45.0)
    # verify the axis convention
    ax = rx(a45) @ ry(b45) @ np.array([0, 0, 1.0])
    res = {"who": "REV-MECH-1", "date": "2026-10-13", "glb": str(glb), "manifest": str(manifest_name(man)),
           "n_instances_glb": len(V), "manifest_instances_missing_in_glb": missing,
           "frame_check_max_bounds_err_mm": max(bchk), "pose_check_combined045_deg": [math.degrees(a45), math.degrees(b45)],
           "axis_at_7deg_45deg": ax.tolist(), "n_engine_instances": len(eng), "n_ring_instances": len(ring),
           "wall_r_mm": R_WALL, "required_r_max_mm": R_REQ, "tessellation_tolerance_mm": "+0 / -0.1", "sweeps": {}}
    # neutral
    def worst(insts, Rm):
        best = []
        for k in insts:
            v = V[k] @ Rm.T
            r = np.hypot(v[:, 0], v[:, 1])
            j = int(np.argmax(r))
            best.append((float(r[j]), k, v[j].round(2).tolist()))
        best.sort(reverse=True)
        return best
    res["neutral_top5_moving"] = [{"r_mm": b[0], "inst": b[1], "at": b[2]} for b in worst(eng + ring, np.eye(3))[:5]]
    for th in (7.0, 8.0):
        rows = []
        per_inst = {}
        for phi in np.arange(0.0, 360.0, 5.0):
            a, b = pose(th, phi)
            Re = rx(a) @ ry(b)
            Rr = rx(a)
            w = worst(eng, Re) + worst(ring, Rr)
            w.sort(reverse=True)
            rows.append({"phi_deg": float(phi), "alpha_deg": math.degrees(a), "beta_deg": math.degrees(b), "r_max_mm": w[0][0],
                         "by": w[0][1], "at": w[0][2], "clearance_mm": R_WALL - w[0][0], "meets_1mm": w[0][0] <= R_REQ})
            for (r, k, at) in w:
                if k not in per_inst or r > per_inst[k]["r_max_mm"]:
                    per_inst[k] = {"r_max_mm": r, "phi_deg": float(phi), "at": at}
        worst_row = max(rows, key=lambda q: q["r_max_mm"])
        viol = sorted(((v["r_max_mm"], k, v["phi_deg"]) for k, v in per_inst.items() if v["r_max_mm"] > R_REQ), reverse=True)
        res["sweeps"][f"cone_{th:g}deg"] = {"worst": worst_row,
                                            "n_directions_violating_1mm": sum(1 for q in rows if not q["meets_1mm"]),
                                            "n_directions_beyond_wall": sum(1 for q in rows if q["r_max_mm"] > R_WALL),
                                            "instances_violating_1mm": [{"inst": k, "r_max_mm": r, "phi_deg": p} for (r, k, p) in viol],
                                            "rows": rows}
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "sweeps"}, indent=1))
    for k, s in res["sweeps"].items():
        print(k, "worst", json.dumps(s["worst"]), "dirs<1mm", s["n_directions_violating_1mm"], "dirs beyond wall",
              s["n_directions_beyond_wall"])
        for q in s["instances_violating_1mm"]:
            print("   ", q)


def manifest_name(p):
    return p


if __name__ == "__main__":
    main()
