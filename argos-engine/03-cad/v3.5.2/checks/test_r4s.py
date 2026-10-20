"""v3.5.2 rev 4 + J-FWD head seat (a) CAD check (lead 07:21Z: d10.5 spot face ADOPTED; config.V352_ON now carries jfwd_od_spot_d 0.0105).
(a) TC-01 new (dev build of V352_ON) vs the published hub TC-01 (rev 4 without the spot face): validity, volume / mass, material removal
    only (hub - new = the 10 pockets, new - hub = 0), STEP / STL sha256/16 of the new part files;
(b) J-FWD head envelopes (ISO 7380-1 M5 dk 9.5 x k 2.75 + 0.1, radially from the flat r_flat) vs every other instance within 3 mm, at
    neutral and at the four combined gimbal extremes of the make_all checks (a, b = +/-4.96, +/-4.94 deg);
(c) the S-AX / thermal TC-01 section at 214 deg: face area of the new TC-01 cut vs the cached rev-4 S-AX geometry (geom_v352r4), i.e. the
    rev-4 thermal / S-AX runs (built without the spot face) have the same TC-01 section.
Software checks, not physical validation.  Mechanical, 2026-10-20."""
import sys, json, hashlib, time, math
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/thermal")
import cadquery as cq
import config, build, engmat, checks
from geom import apply, bbox, cyl_dir
OUT = "/home/claude/work/mechanical/v352/checks/test_r4s_v1.json"
HUB = "/home/claude/work/shared-fallback/engine/03-cad/v3.5.2/parts"
DEV = "/home/claude/work/mechanical/v352/engine/03-cad/parts"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
t0 = time.time()
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V352_ON))
out = {"id": "test_r4s", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "method": __doc__.strip(), "t_build_s": round(time.time() - t0, 1)}
# (a)
new = cq.importers.importStep(f"{DEV}/ENG-TC-01.step").val()
old = cq.importers.importStep(f"{HUB}/ENG-TC-01.step").val()
rho = engmat.rho("AL6061-T6")
vn, vo = sum(s.Volume() for s in new.Solids()), sum(s.Volume() for s in old.Solids())
rem, add = old.cut(new).Volume(), new.cut(old).Volume()
sp = S["jfwd_od_spot"]
out["tc01"] = {"hub_step": {"sha256_16": sha(f"{HUB}/ENG-TC-01.step"), "volume_mm3": round(vo, 3)},
               "new_step": {"path_dev": f"{DEV}/ENG-TC-01.step", "sha256_16": sha(f"{DEV}/ENG-TC-01.step"), "stl_sha256_16": sha(f"{DEV}/ENG-TC-01.stl"),
                            "volume_mm3": round(vn, 3), "valid": bool(new.isValid()), "n_solids": len(new.Solids())},
               "removed_mm3": round(rem, 4), "added_mm3": round(add, 6), "per_pocket_mm3": round(rem / len(S["screw_angles"]), 4),
               "delta_mass_g": round((vn - vo) * 1e-9 * rho * 1e3, 4), "spot": sp, "screw_angles_deg": S["screw_angles"]}
print("TC-01", out["tc01"], flush=True)
# (b)
angs, zb_ = S["screw_angles"], S["bolt_z_fwd"]
heads = []
for a in angs:
    u = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0])
    heads.append(cyl_dir(9.5, 2.75 + 0.1, tuple(u * sp["r_flat_mm"] + np.array([0.0, 0.0, zb_])), tuple(u)))
res = {}
for pose in ((0.0, 0.0), (-4.96, 4.94), (-4.96, -4.94), (4.96, -4.94), (4.96, 4.94)):
    inst = build.posed_instances(reg, S, pose[0], pose[1])
    tc1 = [x for x in inst if x[0] == "ENG-TC-01"][0][3]
    # the heads are engine-frame bodies: posed with the engine group transform (as posed_instances does for the engine parts)
    Tg = build.group_T("engine", pose[0], pose[1])
    hs = [apply(h, Tg) for h in heads]
    recs = []
    for (pn, i, g, sh, body) in inst:
        if pn == "ENG-TC-01":
            continue
        bs = bbox(sh)
        for k, h in enumerate(hs):
            if not checks.bb_overlap(bbox(h), bs, 4.0):
                continue
            dd = checks.min_distance(h, sh)[0]
            if dd < 3.0:
                recs.append({"head_az": angs[k], "other": f"{pn}#{i}", "dist_mm": round(dd, 3)})
    recs.sort(key=lambda r: r["dist_mm"])
    seat = [round(h.intersect(tc1).Volume(), 4) for h in hs]
    res[f"a{pose[0]:+g}_b{pose[1]:+g}"] = {"close_lt_3mm": recs[:24], "min_mm": recs[0]["dist_mm"] if recs else None,
                                           "min_FD04_mm": min((r["dist_mm"] for r in recs if r["other"].startswith("ENG-FD-04")), default=None),
                                           "head_x_tc01_common_mm3_max": max(seat)}
    print("pose", pose, res[f"a{pose[0]:+g}_b{pose[1]:+g}"]["min_mm"], res[f"a{pose[0]:+g}_b{pose[1]:+g}"]["min_FD04_mm"], recs[:3], flush=True)
out["head_envelopes"] = {"envelope": "cyl d 9.5 x 2.85 radially from the flat r_flat (ISO 7380-1 M5 dk 9.5 / k 2.75 + 0.1)", "poses": res,
                         "min_FD04_all_poses_mm": min(v["min_FD04_mm"] for v in res.values() if v["min_FD04_mm"] is not None)}
# (c) TC-01 section at 214 deg vs the cached rev-4 S-AX geometry
import ax_section
zlo, zhi = S["aft_bottom"] - 30.0, S["bonnet_top"] + 30.0
a = math.radians(214.0)
d = (math.cos(a), math.sin(a))
pts = [cq.Vector(0, 0, zlo), cq.Vector(150 * d[0], 150 * d[1], zlo), cq.Vector(150 * d[0], 150 * d[1], zhi), cq.Vector(0, 0, zhi)]
plane = cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True))
inst0 = build.posed_instances(reg, S, 0.0, 0.0)
tc1_0 = [x for x in inst0 if x[0] == "ENG-TC-01"][0][3]
area_new = sum(f.Area() for f in tc1_0.intersect(plane).Faces())
gj = json.load(open("/home/claude/work/mechanical/runs/structural/geom_v352r4/geometry.json"))
area_cache = sum(f["area_mm2"] for f in gj["faces"] if f["pn"] == "ENG-TC-01")
out["sax_section_214"] = {"tc01_area_new_mm2": round(area_new, 4), "tc01_area_geom_v352r4_mm2": round(area_cache, 4),
                          "same": bool(abs(area_new - area_cache) < 1e-3)}
print("section", out["sax_section_214"], flush=True)
out["t_total_s"] = round(time.time() - t0, 1)
s = json.dumps(out, indent=1, default=str)
open(OUT, "w").write(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
