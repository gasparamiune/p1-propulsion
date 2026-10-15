import sys, json
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import numpy as np, config, build
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V351_ON))
inst = build.posed_instances(reg, S, 0.0, 0.0)
for (pn, i, grp, shp, body) in inst:
    if pn in ("ENG-TC-02", "ENG-GM-02", "ENG-GM-01", "ENG-GM-09", "ENG-GM-10", "ENG-FD-05", "ENG-TC-01", "ENG-GM-03"):
        b = shp.BoundingBox()
        print(pn, i, grp, [round(x, 1) for x in (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)])
for pn in ("ENG-GM-02", "ENG-GM-09"):
    p = reg.parts[pn]
    print(pn, "placements", [(np.round(T[:3, 3], 2).tolist(), g) for T, g in p.placements])
    b = p.shape.BoundingBox(); print(" local bbox", [round(x, 1) for x in (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)])
print("z_head_mid", P["z_head_mid"]["v"])
