import sys, math
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import numpy as np, cadquery as cq
import config, build
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True, overrides=dict(config.V351_ON))
inst = build.posed_instances(reg, S, 0.0, 0.0)
tc09 = [i for i in inst if i[0] == "ENG-TC-09"][0][3]
bb = tc09.BoundingBox()
print("TC-09 bbox", [round(x, 2) for x in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)])
# annulus r 34..37 over the socket z range: what touches it?
zt = 169.513
z0, z1 = zt - 336.0, zt - 300.0
ring = cq.Solid.makeCylinder(40.0, z1 - z0, cq.Vector(0, 0, z0)).cut(cq.Solid.makeCylinder(33.9, z1 - z0, cq.Vector(0, 0, z0)))
for (pn, i, g, sh, body) in inst:
    if pn == "ENG-TC-09":
        continue
    sb = sh.BoundingBox()
    if sb.zmax < z0 - 5 or sb.zmin > z1 + 5 or max(abs(sb.xmin), abs(sb.xmax), abs(sb.ymin), abs(sb.ymax)) < 30:
        continue
    try:
        dmin = ring.distance(sh)
    except Exception as e:
        dmin = None
    if dmin is not None and dmin < 3.0:
        print(pn, i, g, "dist to r34-40 band", round(dmin, 3))
print("TC-09 notes:", reg.get("ENG-TC-09").notes[:600])
