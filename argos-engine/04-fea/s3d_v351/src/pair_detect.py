"""Touching/near instance pairs in the neutral v3.5 assembly (B-rep min distance <= tol), with the shared surface area estimate
(faces of A within tol of B, sampled).  Output: geom/v35_neutral/pairs.json"""
import json, sys, time, itertools
from pathlib import Path
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
G = Path(sys.argv[1]); tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2
inst = json.load(open(G / "instances.json"))["instances"]
skip = ("ENG-GR-", "ENG-TC-06", "ENG-TC-07", "ENG-TC-08", "ENG-TC-10")   # non-structural (still listed separately below)
names = [k for k in inst]
S = {k: cq.Shape.importBrep(str(G / inst[k]["brep"])) for k in names}
bb = {}
for k, s in S.items():
    b = s.BoundingBox(); bb[k] = (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)
def overlap(a, b, t):
    return all(a[i] - t <= b[i + 3] and b[i] - t <= a[i + 3] for i in range(3))
out = []
t0 = time.time()
for a, b in itertools.combinations(names, 2):
    if not overlap(bb[a], bb[b], tol):
        continue
    d = BRepExtrema_DistShapeShape(S[a].wrapped, S[b].wrapped)
    if not d.IsDone():
        continue
    dist = d.Value()
    if dist <= tol:
        # face-level: faces of a within tol of b
        fa = []
        for i, f in enumerate(S[a].Faces()):
            dd = BRepExtrema_DistShapeShape(f.wrapped, S[b].wrapped)
            if dd.IsDone() and dd.Value() <= tol:
                c = f.Center(); fa.append([i, round(f.Area(), 2), [round(c.x, 2), round(c.y, 2), round(c.z, 2)], round(dd.Value(), 4)])
        out.append({"a": a, "b": b, "min_dist_mm": round(dist, 4), "faces_a_near_b": fa})
json.dump({"tol_mm": tol, "pairs": out, "t_s": round(time.time() - t0, 1)}, open(G / "pairs.json", "w"), indent=1)
print(len(out), "pairs", round(time.time() - t0, 1), "s")
