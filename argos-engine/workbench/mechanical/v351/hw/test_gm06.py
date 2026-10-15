import sys, json, math
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import config, build
P, S, reg, clog = build.build(include=("engine", "gimbal"), iterate_cg=False, overrides=config.V351_ON)
inst = {f"{pn}#{i}": shp for pn, i, grp, shp, body in build.posed_instances(reg, S, 0, 0)}
for b in ("ENG-GM-06#0", "ENG-GM-06#1"):
    c = inst["ENG-GM-03#0"].intersect(inst[b])
    for so in c.Solids():
        bb = so.BoundingBox()
        print(b, round(so.Volume(), 4), "bbox x", round(bb.xmin, 3), round(bb.xmax, 3), "y", round(bb.ymin, 3), round(bb.ymax, 3), "z", round(bb.zmin, 3), round(bb.zmax, 3))
    bb = inst[b].BoundingBox()
    print(" washer bbox", [round(v, 3) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)])
print("ring_band_z", S.get("ring_band_z"), "gimbal_brg", S.get("gimbal_brg"))
