"""v3.5.2 (lead 206 (2d)) BL-07 pocketing feasibility: manifold volume split and the pocket volume that is free WITHOUT the valve sub-base
pattern and the P_mid transducer port thread (both TO-SELECT).  Mechanical 2026-10-13.  CALC on the v3.5.1 CAD solid."""
import sys, json, math
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import numpy as np, cadquery as cq
import config, build, parts_bleed
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V351_ON))
man = [x for x in reg if x.pn == "ENG-BL-07"][0].shape
B = parts_bleed.BLEED; V = B["valve"]; M = B["manifold"]
rho = 2700.0
def pol(r, az, z):
    a = math.radians(az); return np.array([r * math.cos(a), r * math.sin(a), z])
C1, C2 = pol(V["r"], V["az"][0], 0)[:2], pol(V["r"], V["az"][1], 0)[:2]
Mxy = 0.5 * (C1 + C2); u12 = (C2 - C1) / np.linalg.norm(C2 - C1); n12 = np.array([-u12[1], u12[0]])
Lc = float(np.linalg.norm(C2 - C1))
Vt = man.Volume()
pads = cq.Solid.makeCylinder(M["pad_d"] / 2, M["z1"] - M["z0"], cq.Vector(*C1, M["z0"])).fuse(cq.Solid.makeCylinder(M["pad_d"] / 2, M["z1"] - M["z0"], cq.Vector(*C2, M["z0"])))
V_pads = man.intersect(pads).Volume()
boss = cq.Solid.makeCylinder(M["boss_d"] / 2, M["boss_h"], cq.Vector(*Mxy, M["z1"]))
V_boss = man.intersect(boss).Volume()
# feasible pockets: underside strips 3.0-7.0 mm either side of the bar axis, 8.0 deep (2.0 roof), from 1.0 mm outside each pad
# (along-axis 20.0 from the pad centre) to 7.0 mm from the P_mid port axis (1/8 NPT tap 8.7 + 2 mm wall)
def strip(s0, s1, y0, y1, z0, z1):
    pts = [C1 + s0 * u12 + y0 * n12, C1 + s1 * u12 + y0 * n12, C1 + s1 * u12 + y1 * n12, C1 + s0 * u12 + y1 * n12]
    w = cq.Wire.makePolygon([cq.Vector(p[0], p[1], z0) for p in pts], close=True)
    return cq.Solid.extrudeLinear(cq.Face.makeFromWires(w), cq.Vector(0, 0, z1 - z0))
pk = []
for (s0, s1) in ((M["pad_d"] / 2 + 1.0, Lc / 2 - 7.0), (Lc / 2 + 7.0, Lc - M["pad_d"] / 2 - 1.0)):
    for (y0, y1) in ((3.0, 7.0), (-7.0, -3.0)):
        if s1 > s0:
            pk.append(strip(s0, s1, y0, y1, M["z0"] - 0.1, M["z1"] - 2.0))
V_pk = sum(man.intersect(p).Volume() for p in pk)
out = {"id": "bl07_pockets", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "evidence": "CALC (v3.5.1 CAD solid, 6061-T6 2.70 g/cm3)",
       "manifold_g": round(Vt * 1e-9 * rho * 1e3, 2), "pads_g": round(V_pads * 1e-9 * rho * 1e3, 2), "boss_g": round(V_boss * 1e-9 * rho * 1e3, 2),
       "bar_free_g": round((Vt - V_pads - V_boss) * 1e-9 * rho * 1e3, 2), "Lc_mm": round(Lc, 2),
       "pockets_feasible_now": {"n": len(pk), "description": "underside strips 3-7 mm either side of the mid passage, 8 mm deep (2 mm roof), "
                                "1 mm outside the pads to 7 mm from the P_mid port axis", "saving_g": round(V_pk * 1e-9 * rho * 1e3, 2)},
       "blocked_by": ["valve sub-base screw pattern and port positions (BL-05 TO-SELECT, lead 206 (4))",
                      "P_mid transducer port thread (BL-08, Electronics TO-SELECT)", "side ports BL-10 / BL-06 at mid-height need the 10 mm pad"]}
print(json.dumps(out, indent=1))
json.dump(out, open("/home/claude/work/mechanical/v352/checks/bl07_pockets_v1.json", "w"), indent=1)
