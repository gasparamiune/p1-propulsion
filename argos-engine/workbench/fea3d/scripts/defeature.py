"""Defeature CAD sliver faces (area < A_MAX mm2) with BRepAlgoAPI_Defeaturing before meshing (mesh-quality only; the volume and
bounding-box change is logged and must be negligible).  usage: defeature.py src.brep dst.brep [A_MAX]"""
import sys, json
from pathlib import Path
from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepAlgoAPI import BRepAlgoAPI_Defeaturing
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopTools import TopTools_ListOfShape
def read(p):
    s = TopoDS_Shape(); BRepTools.Read_s(s, str(p), BRep_Builder()); return s
def vol(s):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(s, g); return g.Mass()
def faces(s):
    out = []; ex = TopExp_Explorer(s, TopAbs_FACE)
    while ex.More():
        f = TopoDS.Face_s(ex.Current()); g = GProp_GProps(); BRepGProp.SurfaceProperties_s(f, g)
        c = g.CentreOfMass(); out.append((f, g.Mass(), (round(c.X(),2), round(c.Y(),2), round(c.Z(),2)))); ex.Next()
    return out
src, dst = Path(sys.argv[1]), Path(sys.argv[2]); amax = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
s = read(src); F = faces(s)
tiny = [f for f in F if f[1] < amax]
res = {"src": src.name, "n_faces": len(F), "tiny": [(round(a, 5), c) for _, a, c in tiny], "V_before": vol(s)}
if tiny:
    d = BRepAlgoAPI_Defeaturing(); d.SetShape(s)
    lst = TopTools_ListOfShape()
    for f, a, c in tiny: lst.Append(f)
    d.AddFacesToRemove(lst); d.SetRunParallel(False); d.SetToFillHistory(False); d.Build()
    ok = d.IsDone()
    res["defeaturing_done"] = bool(ok)
    if ok:
        s2 = d.Shape(); F2 = faces(s2)
        res.update({"n_faces_after": len(F2), "V_after": vol(s2), "dV_rel": (vol(s2) - vol(s)) / vol(s),
                    "min_area_after": min(a for _, a, _ in F2)})
        s = s2
    else:
        res["warning"] = "defeaturing failed: original shape kept"
dst.parent.mkdir(parents=True, exist_ok=True)
BRepTools.Write_s(s, str(dst))
print(json.dumps(res))
