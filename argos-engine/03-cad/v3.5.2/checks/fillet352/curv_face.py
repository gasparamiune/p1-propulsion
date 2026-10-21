import sys, math
import numpy as np
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepLProp import BRepLProp_SLProps
from OCP.BRepTools import BRepTools
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.gp import gp_Pnt2d
from OCP.TopAbs import TopAbs_IN, TopAbs_REVERSED
step = sys.argv[1]; cx, cy, cz = map(float, sys.argv[2:5])
sh = cq.importers.importStep(step).val()
f = min(sh.Faces(), key=lambda f: (f.Center() - cq.Vector(cx, cy, cz)).Length)
print("face", f.geomType(), "center", f.Center().toTuple(), "area", round(f.Area(), 4))
ad = BRepAdaptor_Surface(f.wrapped); u0, u1, v0, v1 = BRepTools.UVBounds_s(f.wrapped)
rev = f.wrapped.Orientation() == TopAbs_REVERSED
rows = []
N = 41
for u in np.linspace(u0, u1, N):
    for v in np.linspace(v0, v1, N):
        if BRepClass_FaceClassifier(f.wrapped, gp_Pnt2d(u, v), 1e-7).State() != TopAbs_IN:
            continue
        pr = BRepLProp_SLProps(ad, u, v, 2, 1e-7)
        if not pr.IsCurvatureDefined():
            continue
        k = max((-x if rev else x) for x in (pr.MaxCurvature(), pr.MinCurvature()))
        p = pr.Value()
        rows.append((k, p.X(), p.Y(), p.Z(), u, v))
rows.sort(key=lambda r: -r[0])
ks = np.array([r[0] for r in rows])
print("n", len(rows), "fraction with concave R < 1.4 mm:", round(float((ks > 1 / 1.4).mean()), 4), "R < 1.0:", round(float((ks > 1.0).mean()), 4), "R < 0.5:", round(float((ks > 2.0).mean()), 4))
for r in rows[:12]:
    print(f"  R {1/r[0] if r[0]>1e-9 else float('inf'):8.3f} mm at ({r[1]:.3f}, {r[2]:.3f}, {r[3]:.3f}) r {math.hypot(r[1], r[2]):.3f} uv ({r[4]:.4f}, {r[5]:.4f})")
