"""Extract named solids (engine frame, mm) from the CAD v3.5 assembly STEP via OCP XCAF; save one BREP per instance.
Read-only on the Mechanical CAD; outputs under fea3d/geom/<tag>/."""
import sys, json, hashlib, time
from pathlib import Path
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepTools import BRepTools
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.TopLoc import TopLoc_Location
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

def sha16(p):
    h = hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()[:16]

src = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
t0 = time.time()
doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
rd = STEPCAFControl_Reader(); rd.SetNameMode(True)
assert rd.ReadFile(str(src)) == IFSelect_RetDone
rd.Transfer(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
labels = TDF_LabelSequence(); st.GetFreeShapes(labels)
res = {}
def name_of(lab):
    n = TDataStd_Name()
    if lab.FindAttribute(TDataStd_Name.GetID_s(), n):
        return n.Get().ToExtString()
    return ""
def walk(lab, loc):
    comps = TDF_LabelSequence()
    if st.IsAssembly_s(lab):
        st.GetComponents_s(lab, comps)
        for i in range(1, comps.Length() + 1):
            c = comps.Value(i)
            ref = TDF_Label()
            st.GetReferredShape_s(c, ref)
            l2 = loc.Multiplied(st.GetLocation_s(c))
            nm = name_of(c) or name_of(ref)
            if st.IsAssembly_s(ref):
                walk(ref, l2)
            else:
                shp = st.GetShape_s(ref).Moved(l2)
                key = name_of(ref) or nm
                res.setdefault(key, []).append((nm, shp))
for i in range(1, labels.Length() + 1):
    walk(labels.Value(i), TopLoc_Location())
man = {}
for key, lst in res.items():
    for k, (nm, shp) in enumerate(lst):
        inst = key if len(lst) == 1 else f"{key}__{k}"
        nsol = 0; ex = TopExp_Explorer(shp, TopAbs_SOLID)
        while ex.More(): nsol += 1; ex.Next()
        g = GProp_GProps(); BRepGProp.VolumeProperties_s(shp, g)
        bb = Bnd_Box(); BRepBndLib.Add_s(shp, bb, False); b = bb.Get()
        fn = out / f"{inst.replace('#', '_')}.brep"
        BRepTools.Write_s(shp, str(fn))
        c = g.CentreOfMass()
        man[inst] = {"comp_name": nm, "n_solids": nsol, "volume_mm3": g.Mass(), "cg_mm": [c.X(), c.Y(), c.Z()],
                     "bbox_mm": [round(x, 3) for x in b], "brep": fn.name}
json.dump({"source": str(src), "source_sha256_16": sha16(src), "n": len(man), "t_s": round(time.time() - t0, 1), "instances": man},
          open(out / "instances.json", "w"), indent=1)
print(len(man), "instances", round(time.time() - t0, 1), "s")
