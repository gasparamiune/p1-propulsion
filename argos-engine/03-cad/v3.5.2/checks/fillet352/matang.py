"""Local material angle at sample points of every edge in a region: fraction of IN points on a circle of radius 0.01 mm around the
edge (360 samples, 1 deg); 180 = tangent continuous, 270 = sharp 90 deg re-entrant corner, 90 = sharp convex corner."""
import sys, math, json
import numpy as np
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN, TopAbs_EDGE, TopAbs_FACE
from OCP.TopExp import TopExp
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool
step, az0, daz, rlo, rhi, zlo, zhi = sys.argv[1], *map(float, sys.argv[2:8])
thr = float(sys.argv[8]) if len(sys.argv) > 8 else 186.0
sh = cq.importers.importStep(step).val()
clf = BRepClass3d_SolidClassifier(sh.wrapped)
emap = TopTools_IndexedDataMapOfShapeListOfShape()
TopExp.MapShapesAndAncestors_s(sh.wrapped, TopAbs_EDGE, TopAbs_FACE, emap)
N = 360; eps = 0.01
rows = []
for i in range(1, emap.Extent() + 1):
    e = TopoDS.Edge_s(emap.FindKey(i))
    if BRep_Tool.Degenerated_s(e):
        continue
    ce = cq.Edge(e)
    fl = [cq.Face(TopoDS.Face_s(f)).geomType() for f in emap.FindFromIndex(i)]
    pts = []
    for s in (0.1, 0.3, 0.5, 0.7, 0.9):
        P = np.array(ce.positionAt(s).toTuple())
        r = math.hypot(P[0], P[1]); az = math.degrees(math.atan2(P[1], P[0])) % 360
        if not (rlo <= r <= rhi and zlo <= P[2] <= zhi and abs((az - az0 + 180) % 360 - 180) <= daz):
            continue
        t = np.array(ce.tangentAt(s).toTuple()); t /= np.linalg.norm(t)
        a = np.cross(t, [0, 0, 1.0])
        if np.linalg.norm(a) < 0.2:
            a = np.cross(t, [1.0, 0, 0])
        a /= np.linalg.norm(a); b = np.cross(t, a)
        nin = 0
        for k in range(N):
            th = 2 * math.pi * (k + 0.5) / N
            q = P + eps * (math.cos(th) * a + math.sin(th) * b)
            clf.Perform(gp_Pnt(*q), 1e-9)
            nin += clf.State() == TopAbs_IN
        pts.append((round(360.0 * nin / N, 1), [round(float(x), 3) for x in P], round(r, 3)))
    if pts:
        mx = max(pts, key=lambda v: v[0])
        if mx[0] >= thr:
            rows.append({"edge": i, "type": ce.geomType(), "len": round(ce.Length(), 3), "faces": fl, "mat_max": mx[0], "at": mx[1], "r": mx[2],
                         "mat_along": [v[0] for v in pts]})
rows.sort(key=lambda r: -r["mat_max"])
for r in rows:
    print(json.dumps(r))
print("n", len(rows))
