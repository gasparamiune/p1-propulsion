"""Hole census of every non-COTS CAD part (v3.5.1 dev build, RM1-12): cylindrical faces with fastener-hole radii, their axis, length and
whether they are open at both ends (through) - the basis for the screw grip / engagement lengths in hardware_v351.json.  Mechanical, 2026-10-13."""
import sys, json, math
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import config, build
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_VERTEX
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool
import cadquery as cq
D_OF_INTEREST = {1.6: "M2 tap", 2.05: "M2.5 tap", 2.2: "M2 clr", 2.4: "M2 clr", 2.5: "M3 tap", 2.7: "M2.5 clr", 3.3: "M4 tap", 3.4: "M3 clr",
                 4.0: "dowel 4", 4.2: "M5 tap", 4.3: "M4 clr", 4.5: "M4 clr", 5.0: "M6 tap / 5 bore", 5.5: "M5 clr / M3 DIN7984 cb", 6.0: "M3 cb",
                 8.0: "M4 cb", 9.5: "M5 cb", 3.0: "3 bore", 3.3001: ""}
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V351_ON))
out = {}
for p in reg:
    if p.cots or p.shape is None:
        continue
    sh = p.shape.wrapped if hasattr(p.shape, "wrapped") else p.shape
    ex = TopExp_Explorer(sh, TopAbs_FACE)
    rows = {}
    while ex.More():
        f = TopoDS.Face_s(ex.Current())
        ad = BRepAdaptor_Surface(f)
        if ad.GetType() == GeomAbs_Cylinder:
            cy = ad.Cylinder()
            d = round(2 * cy.Radius(), 3)
            key = min(D_OF_INTEREST, key=lambda k: abs(k - d))
            if abs(key - d) < 0.051:
                ax = cy.Axis()
                o = ax.Location(); dv = ax.Direction()
                o = (o.X(), o.Y(), o.Z()); dv = (dv.X(), dv.Y(), dv.Z())
                # face extent along the axis from its vertices
                tv = []
                vx = TopExp_Explorer(f, TopAbs_VERTEX)
                while vx.More():
                    pnt = BRep_Tool.Pnt_s(TopoDS.Vertex_s(vx.Current()))
                    tv.append((pnt.X() - o[0]) * dv[0] + (pnt.Y() - o[1]) * dv[1] + (pnt.Z() - o[2]) * dv[2])
                    vx.Next()
                if tv:
                    # canonical axis point: projection of the origin onto the axis line
                    t0 = -(o[0] * dv[0] + o[1] * dv[1] + o[2] * dv[2])
                    c = tuple(round(o[i] + t0 * dv[i], 2) for i in range(3))
                    k = (d, c, tuple(round(abs(x), 3) for x in dv))
                    lo, hi = min(tv) - t0, max(tv) - t0
                    r = rows.setdefault(k, [lo, hi])
                    r[0], r[1] = min(r[0], lo), max(r[1], hi)
        ex.Next()
    if rows:
        out[p.pn] = [{"d": k[0], "kind": D_OF_INTEREST[min(D_OF_INTEREST, key=lambda q: abs(q - k[0]))], "axis_pt": k[1], "dir": k[2],
                      "t_range": [round(v[0], 2), round(v[1], 2)], "len": round(v[1] - v[0], 2)} for k, v in sorted(rows.items(), key=lambda kv: (kv[0][0], kv[0][1]))]
json.dump(out, open("/home/claude/work/mechanical/v351/hw/hole_census_v351.json", "w"), indent=1)
bb = {}
for pn in ("ENG-GM-09", "ENG-GM-10", "ENG-GM-08", "ENG-TC-04", "ENG-PD-01", "ENG-FD-08F", "ENG-FD-12F", "ENG-FD-09", "ENG-FS-15", "ENG-FD-01"):
    if pn in reg.parts:
        b = reg.parts[pn].shape.BoundingBox()
        bb[pn] = [round(b.xmin, 2), round(b.ymin, 2), round(b.zmin, 2), round(b.xmax, 2), round(b.ymax, 2), round(b.zmax, 2)]
print(json.dumps(bb))
for pn, rr in out.items():
    print(pn, len(rr), [(r["d"], r["len"]) for r in rr][:14])
