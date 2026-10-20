"""Verify assembly/placements_v3.5.2.json (make_all stage_placements, new in v3.5.2): for every instance, T @ (part STEP shape, part local frame)
must reproduce the neutral posed instance (build.posed_instances at alpha = beta = 0): bbox difference < 0.01 mm.  The hub v3.5.1 placements
file is checked the same way against the same build for the parts whose geometry is unchanged (it is not regenerated).  Software check.
Mechanical, 2026-10-20."""
import sys, json, hashlib
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import numpy as np
import config, build
from geom import apply
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V352_ON))
inst = build.posed_instances(reg, S, 0.0, 0.0)
def bb(sh):
    b = sh.BoundingBox(); return np.array([b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax])
ref = {(pn, i): bb(sh) for (pn, i, g, sh, body) in inst}
f2 = "/home/claude/work/mechanical/v352/engine/03-cad/assembly/placements_v3.5.2.json"
f1 = "/home/claude/work/shared-fallback/engine/03-cad/v3.5.1/assembly/placements_v3.5.1.json"
CHG = {"ENG-FD-01", "ENG-FD-02", "ENG-FD-04", "ENG-GM-01", "ENG-GM-02", "ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-06", "ENG-TC-01", "ENG-TC-02", "ENG-TC-09"}
out = {"id": "verify_placements352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "criterion_mm": 0.01, "files": {}}
for tag, f in (("v352", f2), ("v351_hub", f1)):
    d = json.load(open(f))
    bad, n = [], 0
    for r in d["instances"]:
        k = (r["pn"], r["idx"])
        if tag == "v351_hub" and r["pn"] in CHG:
            continue
        if k not in ref:
            bad.append({"inst": f"{k[0]}#{k[1]}", "err": "no neutral instance"}); continue
        sh = apply(reg.parts[r["pn"]].shape, np.array(r["T_4x4_mm"]))
        e = float(np.abs(bb(sh) - ref[k]).max()); n += 1
        if e > 0.01:
            bad.append({"inst": f"{k[0]}#{k[1]}", "group": r["group"], "bbox_err_mm": round(e, 3)})
    out["files"][tag] = {"path": f, "sha256_16": hashlib.sha256(open(f, "rb").read()).hexdigest()[:16], "n_checked": n, "n_bad": len(bad), "bad": bad}
    print(tag, "checked", n, "bad", len(bad), [b["inst"] for b in bad][:30])
s = json.dumps(out, indent=1)
open("/home/claude/work/mechanical/v352/checks/verify_placements352_v1.json", "w").write(s)
print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])
