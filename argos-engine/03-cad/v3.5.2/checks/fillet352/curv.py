"""Smallest concave radius on the faces of the arm / root junction (r 37.5-41.5, z -35..-11, az window): principal curvatures on a UV
grid (BRepLProp_SLProps); a face is 'concave' in a direction when the material lies on the centre side (curvature centre outside)."""
import sys, math, json
import numpy as np
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepLProp import BRepLProp_SLProps
from OCP.BRepTools import BRepTools
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.gp import gp_Pnt2d
from OCP.TopAbs import TopAbs_IN, TopAbs_REVERSED
step, az0, daz = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
sh = cq.importers.importStep(step).val()
res = []
for f in sh.Faces():
    gt = f.geomType()
    if gt == "PLANE":
        continue
    bb = f.BoundingBox()
    c = f.Center()
    r = math.hypot(c.x, c.y); az = math.degrees(math.atan2(c.y, c.x)) % 360
    if not (37.0 <= r <= 42.0 and -35.5 <= c.z <= -10.5 and abs((az - az0 + 180) % 360 - 180) <= daz):
        continue
    ad = BRepAdaptor_Surface(f.wrapped)
    u0, u1, v0, v1 = BRepTools.UVBounds_s(f.wrapped)
    rev = f.wrapped.Orientation() == TopAbs_REVERSED
    kmax = 0.0; at = None; n_in = 0
    for u in np.linspace(u0, u1, 25):
        for v in np.linspace(v0, v1, 25):
            cl = BRepClass_FaceClassifier(f.wrapped, gp_Pnt2d(u, v), 1e-7)
            if cl.State() != TopAbs_IN:
                continue
            n_in += 1
            pr = BRepLProp_SLProps(ad, u, v, 2, 1e-7)
            if not pr.IsCurvatureDefined():
                continue
            k1, k2 = pr.MaxCurvature(), pr.MinCurvature()
            # OCC curvature sign is w.r.t. the surface normal (not the face orientation); outward normal = -N if reversed.
            # concave (material side contains the centre... ) : with outward normal n_out, a concave fillet has its centre in AIR,
            # i.e. curvature vector points along +n_out -> signed curvature (w.r.t. n_out) > 0 in OCC's convention k = (d2P . N)
            for k in (k1, k2):
                ks = -k if rev else k
                if ks > kmax:
                    kmax = ks; p = pr.Value(); at = (round(p.X(), 3), round(p.Y(), 3), round(p.Z(), 3))
    if n_in:
        res.append({"type": gt, "center": [round(c.x, 2), round(c.y, 2), round(c.z, 2)], "r": round(r, 2), "max_signed_curv_1pmm": round(kmax, 4),
                    "min_radius_mm": (round(1.0 / kmax, 3) if kmax > 1e-6 else None), "at": at, "n_pts": n_in})
res.sort(key=lambda d: -(d["max_signed_curv_1pmm"]))
for d in res: print(json.dumps(d))
