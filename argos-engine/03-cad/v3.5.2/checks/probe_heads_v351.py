"""J-FWD screw-head envelopes (ISO 7380-1 M5 dk 9.5 x k 2.75, not modelled in CAD) on the FROZEN v3.5.1 build (8x at 22.5 + 45k deg):
distance to FD-04 (riser radiation shield) and every other instance at neutral.  Mechanical, 2026-10-20."""
import sys, json, math
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import config, build, checks
from geom import cyl_dir, bbox
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V351_ON))
angs, zb_ = S["screw_angles"], S["bolt_z_fwd"]
inst = build.posed_instances(reg, S, 0.0, 0.0)
res = []
for a in angs:
    u = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0])
    h = cyl_dir(9.5, 2.85, tuple(u * 31.75 + np.array([0.0, 0.0, zb_])), tuple(u))
    for (pn, i, g, sh, b) in inst:
        if pn == "ENG-TC-01" or not checks.bb_overlap(bbox(h), bbox(sh), 4.0):
            continue
        d, _, _ = checks.min_distance(h, sh)
        if d < 3.0:
            res.append({"head_az": a, "other": f"{pn}#{i}", "dist_mm": round(d, 3), "common_mm3": round(h.intersect(sh).Volume(), 3)})
print(json.dumps({"cad": "v3.5.1 (V351_ON)", "angles": angs, "z": zb_, "close": res}))
