"""Line 203 (2): free space for a close-coupled Pc transducer at the head Pc tap (v3.5.1 dev build, neutral pose)."""
import sys, json, math, pickle
from pathlib import Path
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad")
import numpy as np, cadquery as cq
import config, build
from geom import cyl_dir
ov = dict(config.V351_ON)
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True, overrides=ov)
print("pc_port", S.get("pc_port"), "pc_passage", [np.round(np.array(x), 3).tolist() for x in S.get("pc_passage")], "pc_exit", np.round(S.get("pc_exit"), 3).tolist())
print("z_head_mid", P.get("z_head_mid", {}).get("v"), "head_top?", S.get("z_head_top"), [k for k in S if "top" in k or "zt" in k][:20])
inst = build.posed_instances(reg, S, 0.0, 0.0)
pickle.dump({"S_keys": list(S.keys())}, open("/home/claude/work/mechanical/v351/pc/S_keys.pkl", "wb"))
p0, p1 = [np.array(x, float) for x in S["pc_passage"]]
ang, r = S["pc_port"]
# head top: TC-02 top face z in the engine frame
tc02 = [i for i in inst if i[0] == "ENG-TC-02"][0][3]
bb = tc02.BoundingBox()
zt = bb.zmax
print("TC-02 bbox z", round(bb.zmin, 3), round(bb.zmax, 3))
c = np.array([r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang))])
res = {}
for name, (d, h) in {"cyl_d22_h75": (22.0, 75.0), "cyl_d25.4_h75": (25.4, 75.0), "cyl_d19_h60": (19.0, 60.0), "cyl_d12_h30": (12.0, 30.0)}.items():
    s = cq.Solid.makeCylinder(d / 2, h, cq.Vector(c[0], c[1], zt + 0.01), cq.Vector(0, 0, 1))
    hits = []
    for (pn, i, g, sh, body) in inst:
        sb = sh.BoundingBox()
        if sb.xmax < c[0] - d or sb.xmin > c[0] + d or sb.ymax < c[1] - d or sb.ymin > c[1] + d or sb.zmax < zt or sb.zmin > zt + h:
            continue
        try:
            dist = s.distance(sh) if hasattr(s, "distance") else None
        except Exception:
            dist = None
        try:
            v = s.intersect(sh).Volume()
        except Exception:
            v = -1
        hits.append((pn, i, g, round(v, 2), None if dist is None else round(dist, 2)))
    res[name] = hits
    print(name, "near/intersecting:", hits)
json.dump(res, open("/home/claude/work/mechanical/v351/pc/pc_space_v1.json", "w"), indent=1)
