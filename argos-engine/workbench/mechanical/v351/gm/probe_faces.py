"""Which collar faces meet at the LC3 hot spots (engine-local points)?  v3.5 geometry (config.V34_ON)."""
import sys, math, json
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import numpy as np, cadquery as cq
import config, build
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.gp import gp_Pnt
ov = dict(config.V34_ON)
for a in sys.argv[1:]:
    k, v = a.split("=", 1)
    try: v = json.loads(v)
    except Exception: pass
    ov[k] = v
P, S, reg, clog = build.build(include=("engine", "gimbal"), iterate_cg=False, overrides=ov)
g = S["tvc"]
for sv in g["servos"]:
    print("servo", sv["i"], "phi", round(sv["phi"], 2), "s", sv["s"])
shp = reg.parts["ENG-GM-01"].shape
pts = {"H1": (-28.0, 26.69, -13.0), "H2": (-29.82, 13.73, -10.38), "H2b": (-31.55, 12.43, -10.41), "H3": (-31.89, 21.76, -13.98)}
for nm, p in pts.items():
    v = cq.Vertex.makeVertex(*p)
    near = []
    for f in shp.Faces():
        d = f.distance(v) if hasattr(f, "distance") else None
        if d is None:
            ext = BRepExtrema_DistShapeShape(f.wrapped, v.wrapped); ext.Perform(); d = ext.Value()
        if d < 0.6:
            c = f.Center(); n = f.normalAt(f.Center())
            near.append((round(d, 3), f.geomType(), [round(x, 2) for x in c.toTuple()], [round(x, 3) for x in n.toTuple()], round(f.Area(), 2)))
    print(nm, p, "r", round(math.hypot(p[0], p[1]), 2), "az", round(math.degrees(math.atan2(p[1], p[0])), 2))
    for q in sorted(near):
        print("   ", q)
