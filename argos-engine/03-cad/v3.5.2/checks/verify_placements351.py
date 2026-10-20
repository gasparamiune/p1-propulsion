"""Check the frozen hub v3.5.1 placements file against a v3.5.1 build (v351 tree, config.V351_ON): T @ part shape vs the neutral posed instance
(bbox < 0.01 mm), lock included; and whether the v3.5.2 transforms of the failing instances reproduce the v3.5.1 instances (pushrod items are
geometrically unchanged in v3.5.2).  Software check.  Mechanical, 2026-10-20."""
import sys, json, hashlib
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import numpy as np
import config, build
from geom import apply
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V351_ON))
inst = build.posed_instances(reg, S, 0.0, 0.0, with_lock=True)
def bb(sh):
    b = sh.BoundingBox(); return np.array([b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax])
ref = {(pn, i): bb(sh) for (pn, i, g, sh, body) in inst}
f1 = "/home/claude/work/shared-fallback/engine/03-cad/v3.5.1/assembly/placements_v3.5.1.json"
f2 = "/home/claude/work/mechanical/v352/engine/03-cad/assembly/placements_v3.5.2.json"
d1, d2 = json.load(open(f1)), json.load(open(f2))
t2 = {(r["pn"], r["idx"]): r["T_4x4_mm"] for r in d2["instances"]}
bad, n = [], 0
for r in d1["instances"]:
    k = (r["pn"], r["idx"])
    if k not in ref:
        bad.append({"inst": f"{k[0]}#{k[1]}", "err": "no neutral instance"}); continue
    e = float(np.abs(bb(apply(reg.parts[r["pn"]].shape, np.array(r["T_4x4_mm"]))) - ref[k]).max()); n += 1
    if e > 0.01:
        rec = {"inst": f"{k[0]}#{k[1]}", "group": r["group"], "bbox_err_mm": round(e, 3)}
        if k in t2:
            rec["with_v352_T_bbox_err_mm"] = round(float(np.abs(bb(apply(reg.parts[r["pn"]].shape, np.array(t2[k]))) - ref[k]).max()), 6)
        bad.append(rec)
out = {"id": "verify_placements351", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "criterion_mm": 0.01,
       "file": {"path": "03-cad/v3.5.1/assembly/placements_v3.5.1.json", "sha256_16": hashlib.sha256(open(f1, "rb").read()).hexdigest()[:16]},
       "n_instances": len(d1["instances"]), "n_checked": n, "n_bad": len(bad), "bad": bad}
s = json.dumps(out, indent=1)
open("/home/claude/work/mechanical/v352/checks/verify_placements351_v1.json", "w").write(s)
print("checked", n, "bad", len(bad)); [print(" ", b) for b in bad]
print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])
