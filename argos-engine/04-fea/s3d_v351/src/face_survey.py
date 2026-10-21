import sys, math
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane, GeomAbs_Cone, GeomAbs_Torus, GeomAbs_Sphere
TY = {GeomAbs_Cylinder: "CYL", GeomAbs_Plane: "PLN", GeomAbs_Cone: "CON", GeomAbs_Torus: "TOR", GeomAbs_Sphere: "SPH"}
s = cq.Shape.importBrep(sys.argv[1])
minA = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
for k, f in enumerate(s.Faces()):
    ad = BRepAdaptor_Surface(f.wrapped); t = ad.GetType(); ty = TY.get(t, str(t))
    c = f.Center(); A = f.Area()
    if A < minA: continue
    extra = ""
    if t == GeomAbs_Cylinder:
        cy = ad.Cylinder(); ax = cy.Axis(); d = ax.Direction(); p = ax.Location()
        extra = f"R {cy.Radius():.3f} axis ({d.X():.2f},{d.Y():.2f},{d.Z():.2f}) at ({p.X():.2f},{p.Y():.2f},{p.Z():.2f})"
    elif t == GeomAbs_Plane:
        n = f.normalAt(c); extra = f"n ({n.x:.2f},{n.y:.2f},{n.z:.2f})"
    elif t == GeomAbs_Cone:
        co = ad.Cone(); extra = f"semiangle {math.degrees(co.SemiAngle()):.2f} refR {co.RefRadius():.3f}"
    r = math.hypot(c.x, c.y); az = math.degrees(math.atan2(c.y, c.x))
    bb = f.BoundingBox()
    print(f"{k:3d} {ty:4s} A {A:9.2f} c ({c.x:7.2f},{c.y:7.2f},{c.z:8.2f}) r {r:6.2f} az {az:7.1f} z[{bb.zmin:7.2f},{bb.zmax:7.2f}] {extra}")
