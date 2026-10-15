#!/usr/bin/env python3
"""REV-MECH-1, 2026-10-13 - audit of the author's bay-wall check output (own code; no author module imported).

1. From the author's checks_v3.5.json (as it stands when read): per pose, the composition of the 'bay_wall_min' list (12 nearest
   instances): which groups appear, whether any moving-group (engine / ring / horn / pushrod / hose) instance appears, and at what
   distance.  Purpose: test whether the stored list and the log summary line 'wall min 0.0 (ENG-BL-06#0)' can reveal a moving-part
   violation at all.
2. From the author's GLB (ENGINE_v3.5_neutral.glb, frame (x, y, z)_glTF = (x, z, -y)_engine / 1000): for every FIXED-group
   instance, the maximum radius about the airframe axis (vertex based; tessellation sag <= 0.1 mm, so +0 / -0.1 mm) and whether
   it lies beyond r 70.0 mm (inside the airframe wall material) - the author's unsigned min_distance reports 0.0 for touching and
   for penetrating alike.
3. Names and groups from BOM_v3.5.json and assembly_manifest_v3.5.json.
Usage: python -I rm1_wall_top12_audit.py <checks_v3.5.json> <glb> <manifest_json> <bom_json> <out_json>
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import trimesh


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main():
    chk, glb, man, bom, out = (Path(a) for a in sys.argv[1:6])
    C = json.loads(chk.read_text())
    M = json.loads(man.read_text())
    B = {l["pn"]: l for l in json.loads(bom.read_text())["lines"]}
    group = {i["inst"]: i["group"] for i in M["instances"]}
    res = {"who": "REV-MECH-1", "date": "2026-10-13",
           "sources_sha256_16": {"checks": sha16(chk), "glb": sha16(glb), "manifest": sha16(man), "bom": sha16(bom)},
           "poses_in_checks_file": [p["pose"] for p in C["poses"]], "top12": [], "fixed_beyond_wall": []}
    for p in C["poses"]:
        lst = p["bay_wall_min"]
        moving = [{"inst": x["inst"], "group": x["group"], "dist_mm": x["dist_mm"]} for x in lst if x["group"] != "fixed"]
        res["top12"].append({"pose": p["pose"], "alpha_deg": p["alpha_deg"], "beta_deg": p["beta_deg"], "n_listed": len(lst),
                             "groups_listed": sorted({x["group"] for x in lst}), "moving_listed": moving,
                             "n_fixed_at_0": sum(1 for x in lst if x["group"] == "fixed" and x["dist_mm"] == 0.0),
                             "largest_listed_dist_mm": max(x["dist_mm"] for x in lst)})
    sc = trimesh.load(str(glb), force="scene")
    for node in sc.graph.nodes_geometry:
        if group.get(node) != "fixed":
            continue
        T, g = sc.graph[node]
        v = trimesh.transformations.transform_points(sc.geometry[g].vertices, T)
        x, y, z = 1000.0 * v[:, 0], -1000.0 * v[:, 2], 1000.0 * v[:, 1]
        r = np.hypot(x, y)
        j = int(np.argmax(r))
        if r[j] > 69.0:
            pn = node.split("#")[0]
            res["fixed_beyond_wall"].append({"inst": node, "name": B.get(pn, {}).get("name"), "r_max_mm": float(r[j]),
                                             "at_mm": [round(float(x[j]), 2), round(float(y[j]), 2), round(float(z[j]), 2)],
                                             "beyond_r70": bool(r[j] > 70.0 + 1e-6),
                                             "volume_fraction_vertices_beyond_r70": float(np.mean(r > 70.0 + 1e-6))})
    res["fixed_beyond_wall"].sort(key=lambda q: -q["r_max_mm"])
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res["sources_sha256_16"]))
    for t in res["top12"]:
        print(json.dumps(t))
    for f in res["fixed_beyond_wall"]:
        print(json.dumps(f))


if __name__ == "__main__":
    main()
