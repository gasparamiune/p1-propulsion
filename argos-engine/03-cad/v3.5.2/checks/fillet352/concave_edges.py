"""Concave edge audit of a part STEP: material angle by solid classification on a small circle around the edge (36 samples) at 3
points per edge; lists edges with material angle > 200 deg, their two adjacent face types and location (r, az, z)."""
import sys, math, json
import numpy as np
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN, TopAbs_ON
from OCP.TopExp import TopExp
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRep import BRep_Tool
from OCP.TopoDS import TopoDS

def load(p):
    return cq.importers.importStep(p).val()

def audit(shape, region=None, eps=0.02, nang=36, fmin=200.0):
    sol = shape.wrapped
    clf = BRepClass3d_SolidClassifier(sol)
    emap = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(sol, TopAbs_EDGE, TopAbs_FACE, emap)
    out = []
    for i in range(1, emap.Extent() + 1):
        e = TopoDS.Edge_s(emap.FindKey(i))
        faces = emap.FindFromIndex(i)
        fl = [cq.Face(f) for f in faces]
        ce = cq.Edge(e)
        if BRep_Tool.Degenerated_s(e):
            continue
        L = ce.Length()
        if L < 1e-4:
            continue
        mids = []
        angs = []
        for s in (0.2, 0.5, 0.8):
            p = ce.positionAt(s); t = ce.tangentAt(s)
            P = np.array([p.x, p.y, p.z]); T = np.array([t.x, t.y, t.z]); T /= np.linalg.norm(T)
            if region and not region(P):
                continue
            a = np.cross(T, [0, 0, 1.0]);
            if np.linalg.norm(a) < 0.1:
                a = np.cross(T, [1.0, 0, 0])
            a /= np.linalg.norm(a); b = np.cross(T, a)
            n_in = 0
            for k in range(nang):
                th = 2 * math.pi * k / nang
                q = P + eps * (math.cos(th) * a + math.sin(th) * b)
                clf.Perform(gp_Pnt(*q), 1e-7)
                if clf.State() == TopAbs_IN:
                    n_in += 1
            angs.append(360.0 * n_in / nang); mids.append(P)
        if not angs:
            continue
        mx = max(angs)
        if mx >= fmin:
            P = mids[int(np.argmax(angs))]
            out.append({"edge_index_TopExp": i, "len_mm": round(L, 3), "type": ce.geomType(), "mat_angle_deg": [round(x) for x in angs],
                        "faces": [f.geomType() for f in fl], "p": [round(float(x), 3) for x in P],
                        "r": round(float(math.hypot(P[0], P[1])), 3), "az_deg": round(math.degrees(math.atan2(P[1], P[0])) % 360, 2)})
    return out

if __name__ == "__main__":
    step = sys.argv[1]; az0 = float(sys.argv[2]); daz = float(sys.argv[3])
    def region(P):
        az = math.degrees(math.atan2(P[1], P[0])) % 360
        d = (az - az0 + 180) % 360 - 180
        return abs(d) <= daz and -40 <= P[2] <= 12 and 30 <= math.hypot(P[0], P[1]) <= 70
    sh = load(step)
    res = audit(sh, region)
    res.sort(key=lambda r: (r["r"], r["p"][2]))
    for r in res:
        print(json.dumps(r))
    print("n concave edges in region:", len(res))
