"""Probe the v3.5.1 lever-root BREP of GM-01/GM-02 near the FEA3D R3 peak (v3.5.2 tree, unchanged root): faces/edges within 2.5 mm of the
refinement-ball centres, fillet log, section data.  Mechanical, 2026-10-19."""
import sys, json, math, time
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import numpy as np
import config, build
t0 = time.time()
P, clog = config.build()
for k, v in config.V352_ON.items():
    P[k] = {"v": v, "tag": "DESIGN", "src": "V352_ON"}
S, reg = build._one_build(P, ("engine", "gimbal"))
print("build s", round(time.time() - t0, 1))
out = {"fillet_log": S.get("collar_root_v351_fillets"), "parts": {}}
balls = {"ENG-GM-02": (-30.15, -12.15, -10.9), "ENG-GM-01": (-30.15, 12.15, -10.9)}
for pn, c in balls.items():
    sh = reg.parts[pn].shape
    c = np.array(c)
    rec = {"volume_mm3": sh.Volume(), "valid": sh.isValid(), "faces": [], "edges": []}
    for f in sh.Faces():
        bb = f.BoundingBox()
        # distance from c to bbox
        d = np.linalg.norm(np.maximum(0, np.maximum(np.array([bb.xmin, bb.ymin, bb.zmin]) - c, c - np.array([bb.xmax, bb.ymax, bb.zmax]))))
        if d < 2.5:
            rec["faces"].append({"type": f.geomType(), "area": round(f.Area(), 4), "bbox": [round(x, 3) for x in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
                                 "bbox_dist": round(float(d), 3)})
    for e in sh.Edges():
        pts = np.array([e.positionAt(t).toTuple() for t in np.linspace(0, 1, 9)])
        d = float(np.min(np.linalg.norm(pts - c, axis=1)))
        if d < 2.0:
            r = np.hypot(pts[:, 0], pts[:, 1])
            az = np.degrees(np.arctan2(pts[:, 1], pts[:, 0]))
            rec["edges"].append({"type": e.geomType(), "len": round(e.Length(), 4), "dmin": round(d, 3),
                                 "r": [round(float(r.min()), 3), round(float(r.max()), 3)], "z": [round(float(pts[:, 2].min()), 3), round(float(pts[:, 2].max()), 3)],
                                 "az": [round(float(az.min()), 3), round(float(az.max()), 3)]})
    out["parts"][pn] = rec
s = json.dumps(out, indent=1, default=float)
open("/home/claude/work/mechanical/v352/gm/probe_root_v351.json", "w").write(s)
print(s[:6000])
