"""Test build of the v3.5.1 collar root (GM-01/02): validity, volume, fillet log, clearances to GM-03 / TC-01 at poses."""
import sys, json, math, time
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import numpy as np
import config, build
from geom import apply
RV = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"half_ang": 16.0}
ov = dict(config.V34_ON)
lv = dict(ov["tvc_lever_v34"]); lv["root_v351"] = RV
ov["tvc_lever_v34"] = lv
ov["gimbal_bearing"] = "HK0808"
t0 = time.time()
P, S, reg, clog = build.build(include=("engine", "gimbal"), iterate_cg=False, overrides=ov)
print("build", round(time.time() - t0, 1), "s")
for pn in ("ENG-GM-01", "ENG-GM-02"):
    sh = reg.parts[pn].shape
    print(pn, "valid", sh.isValid(), "solids", len(sh.Solids()), "V", round(sh.Volume(), 1), "mm3 (v3.5: 22503.064 / 22960.662)")
print(json.dumps(S.get("collar_root_v351_fillets"), indent=0))
# clearances GM-01/02 vs GM-03 (ring) and TC-01 (case) and GM-16/17 at poses
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
def dmin(a, b):
    e = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped); e.Perform(); return e.Value()
poses = [(0, 0), (0, 8), (0, -8), (8, 0), (-8, 0), (-5.68, 5.65), (5.68, 5.65), (-5.68, -5.65), (5.68, -5.65)]
for a, b in poses:
    inst = {(pn, i): sh for pn, i, grp, sh, body in build.posed_instances(reg, S, a, b)}
    for pn in ("ENG-GM-01", "ENG-GM-02"):
        c = inst[(pn, 0)]
        row = []
        for other in ("ENG-GM-03", "ENG-TC-01", "ENG-GM-08", "ENG-GM-10"):
            ds = [dmin(c, sh) for (q, i), sh in inst.items() if q == other]
            row.append(f"{other} {min(ds):.3f}")
        print(f"pose a {a:6.2f} b {b:6.2f} {pn}: " + ", ".join(row))
