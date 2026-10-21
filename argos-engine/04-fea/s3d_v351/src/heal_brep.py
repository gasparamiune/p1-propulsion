"""Remove CAD sliver faces (boolean residue) before meshing: ShapeUpgrade_UnifySameDomain (merge faces on the same surface),
then report remaining tiny faces.  Writes geom/v35_neutral_healed/<stem>.brep; the volume change is logged (must be ~0)."""
import sys, json
from pathlib import Path
from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
def read(p):
    s = TopoDS_Shape(); BRepTools.Read_s(s, str(p), BRep_Builder()); return s
def vol(s):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(s, g); return g.Mass()
def faces(s):
    out = []; ex = TopExp_Explorer(s, TopAbs_FACE)
    while ex.More():
        g = GProp_GProps(); BRepGProp.SurfaceProperties_s(TopoDS.Face_s(ex.Current()), g)
        c = g.CentreOfMass(); out.append((g.Mass(), (round(c.X(),2), round(c.Y(),2), round(c.Z(),2)))); ex.Next()
    return out
src = Path(sys.argv[1]); dst = Path(sys.argv[2]); dst.parent.mkdir(parents=True, exist_ok=True)
s = read(src)
u = ShapeUpgrade_UnifySameDomain(s, True, True, True); u.Build(); s2 = u.Shape()
f1, f2 = faces(s), faces(s2)
BRepTools.Write_s(s2, str(dst))
print(json.dumps({"src": src.name, "faces_before": len(f1), "faces_after": len(f2), "V_before": vol(s), "V_after": vol(s2),
                  "min_area_before": min(a for a, _ in f1), "min_area_after": min(a for a, _ in f2),
                  "tiny_after": [x for x in f2 if x[0] < 0.5]}))
