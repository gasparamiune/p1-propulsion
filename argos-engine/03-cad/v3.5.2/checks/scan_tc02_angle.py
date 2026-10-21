"""S-AX section azimuth for TC-02 / TC-04 in v3.5.2: the v3.5.2 J-FWD taps (10x at 18 + 36k) put a tap at 90 deg, the v3.5.1 S-AX head
section angle (sax.py ANGLE_PART).  Scan the half-plane section area of TC-02 and TC-04 at 60-120 deg (v3.5.2 and v3.5.1): a plateau equal to
the clear value = no non-axisymmetric feature in the plane.  Mechanical, 2026-10-20."""
import sys, json, math
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import cadquery as cq
import config, build
res = {}
for tag, ov in (("v352", config.V352_ON), ("v351", config.V351_ON)):
    P, S, reg, clog = build.build(include=("engine",), iterate_cg=False, overrides=dict(ov))
    inst = {pn: sh for (pn, i, g, sh, b) in build.posed_instances(reg, S, 0.0, 0.0) if pn in ("ENG-TC-02", "ENG-TC-04")}
    zlo, zhi = S["aft_bottom"] - 30.0, S["bonnet_top"] + 30.0
    rows = []
    for ang in list(range(60, 121, 2)) + [77, 78, 79, 81]:
        a = math.radians(ang)
        d = (math.cos(a), math.sin(a))
        pts = [cq.Vector(0, 0, zlo), cq.Vector(150 * d[0], 150 * d[1], zlo), cq.Vector(150 * d[0], 150 * d[1], zhi), cq.Vector(0, 0, zhi)]
        plane = cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True))
        rows.append({"ang": ang, **{pn: round(sum(f.Area() for f in sh.intersect(plane).Faces()), 2) for pn, sh in inst.items()}})
    res[tag] = sorted(rows, key=lambda r: r["ang"])
    print(tag, json.dumps(res[tag]), flush=True)
open("/home/claude/work/mechanical/v352/checks/scan_tc02_angle_v1.json", "w").write(json.dumps(res, indent=1))
