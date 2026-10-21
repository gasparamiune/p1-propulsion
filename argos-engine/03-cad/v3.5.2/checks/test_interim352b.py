"""v3.5.2 INTERIM CAD check v2 (after lead CHANGELOG 231: J-FWD = 10x ISO 7380-1 M5 x 10 A4-80 at az 18 + 36k deg, no case land; FD-01 +y lower
ear relieved round BL-03E).  (a) changed parts vs v3.5.1: validity, solids, volume / mass, STEP round-trip (make_all criterion); (b) BL-03E x
FD-01; (c) TC-02 J-FWD taps: min wall from the M5 major diameter to any other cavity of TC-02 (probe bisection, as wall_jfd01.py); (d) FD-01 wall
between the +y lower M4 clearance hole and the BL-03E relief; (e) J-FWD screw-head envelopes (ISO 7380-1 M5: dk 9.5 x k 2.75 from the OD
r 31.75; not modelled in CAD) against every other instance at neutral and the relatively moving ones at all 18 poses.  Software checks, not
physical validation.  Mechanical, 2026-10-20."""
import sys, json, hashlib, time, csv, math
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import cadquery as cq
import config, build, engmat, checks, parts_inlet
from geom import apply, bbox, cyl_dir, cyl, box, radial_hole
t0 = time.time()
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V352_ON))
out = {"id": "test_interim352b", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "cad": "v3.5.2 interim v2 (config.V352_ON)",
       "t_build_s": round(time.time() - t0, 1), "method": __doc__.strip()}
bom351 = {r["pn"]: r for r in csv.DictReader(open("/home/claude/work/shared-fallback/engine/03-cad/v3.5.1/BOM_v3.5.1.csv"))}


def rt(shape, path):
    cq.exporters.export(shape, path)
    imp = cq.importers.importStep(path).val()
    v0 = sum(s.Volume() for s in shape.Solids()); v1 = sum(s.Volume() for s in imp.Solids())
    from make_all import bounds_of
    b0, b1 = bounds_of(shape), bounds_of(imp)
    berr = max(abs(a - b) for a, b in zip(b0, b1))
    ok = imp.isValid() and len(imp.Solids()) == len(shape.Solids()) and abs(v1 - v0) / v0 < 1e-5 and berr < 0.01
    return {"passed": bool(ok), "dV_rel": abs(v1 - v0) / v0, "bbox_err_mm": berr, "n_solids": len(imp.Solids()),
            "sha256_16": hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]}


PNS = ("ENG-GM-01", "ENG-GM-02", "ENG-TC-01", "ENG-TC-02", "ENG-FD-01", "ENG-NZ-01", "ENG-NZ-06", "ENG-TC-09", "ENG-BL-03E")
out["parts"] = {}
for pn in PNS:
    if pn not in reg.parts:
        out["parts"][pn] = "absent"
        continue
    p = reg.parts[pn]
    sh = p.shape
    V = sum(s.Volume() for s in sh.Solids())
    rho = engmat.rho(p.material)
    m = round(V * 1e-9 * rho * 1e3, 3) if (rho and p.mass_each_kg is None) else (round(p.mass_each_kg * 1e3, 3) if p.mass_each_kg else None)
    m351 = float(bom351[pn]["unit_mass_kg"]) * 1e3 if pn in bom351 and bom351[pn]["unit_mass_kg"] else None
    out["parts"][pn] = {"material": p.material, "valid": bool(sh.isValid()), "n_solids": len(sh.Solids()), "volume_mm3": round(V, 3), "mass_g": m,
                        "mass_v351_g": (round(m351, 3) if m351 else None), "delta_g": (round(m - m351, 3) if (m is not None and m351) else None),
                        "roundtrip": rt(sh, f"/home/claude/work/mechanical/v352/checks/rt352/{pn}.step")}
    print(pn, json.dumps(out["parts"][pn]), flush=True)
out["delta_total_g"] = round(sum(v["delta_g"] for v in out["parts"].values() if isinstance(v, dict) and v["delta_g"] is not None), 3)
inst = build.posed_instances(reg, S, 0.0, 0.0)
I0 = {f"{pn}#{i}": sh for (pn, i, g, sh, b) in inst}
# (b)
c = I0["ENG-BL-03E#0"].intersect(I0["ENG-FD-01#0"])
d, p1, p2 = checks.min_distance(I0["ENG-BL-03E#0"], I0["ENG-FD-01#0"])
out["bl03e_fd01"] = {"common_mm3": round(c.Volume(), 4), "min_dist_mm": round(d, 3), "relief": S.get("fd01_ear_relief")}
print("bl03e_fd01", out["bl03e_fd01"], flush=True)
# (c) TC-02 J-FWD tap walls
tc = I0["ENG-TC-02#0"]
angs = S["screw_angles"]
zb_ = S["bolt_z_fwd"]
plug_r, jd = 57.20 / 2.0, S["jfwd_tap_drill_mm"]
taps = [radial_hole(4.2, a, zb_, plug_r - jd, plug_r + 1.0) for a in angs]
filled = tc
for t_ in taps:
    filled = filled.fuse(t_)
filled = filled.clean()
env = cyl(2 * (plug_r - 0.01), S["inj_face"] + 0.5, S["head_bot"] - 0.5)


def extra(pr):
    return pr.intersect(env).cut(filled).Volume()


def bis(mk, hi=4.0):
    if extra(mk(hi)) <= 0.01:
        return f">{hi}"
    lo = 0.0
    for _ in range(7):
        mid = 0.5 * (lo + hi)
        if extra(mk(mid)) > 0.01:
            hi = mid
        else:
            lo = mid
    return round(lo, 3)


walls = []
for a in angs:
    mk = lambda w, a=a: radial_hole(5.0 + 2 * w, a, zb_, plug_r - jd - w, plug_r - 0.2)
    walls.append({"az_deg": a, "min_wall_mm_from_M5_major": bis(mk)})
ref = []
for a in (22.5, 157.5, 337.5):                       # the frozen v3.5.1 tap azimuths probed in the same TC-02 (wall to the same cavities)
    mk = lambda w, a=a: radial_hole(5.0 + 2 * w, a, zb_, plug_r - jd - w, plug_r - 0.2)
    ref.append({"az_deg": a, "min_wall_mm_from_M5_major": bis(mk)})
out["tc02_jfwd_tap_walls"] = {"z_mm": round(zb_, 3), "tap": "drill 4.2 x 9.0, M5-6H 8.0 full thread", "taps": walls, "v351_azimuth_reference": ref,
                              "Pc_port": S.get("pc_port"), "note": "probe d 5.0 + 2w from r 28.6 - 9.0 - w to r 28.4, inside the plug envelope"}
print("tap walls", walls, "v351 ref", ref, flush=True)
# (d) FD-01 +y lower clearance hole to the BL-03E relief
sc = [q for q in parts_inlet.JFD01_V352["screws"] if q["y"] > 0][0]
zs = S["head_bot"] + sc["z_rel"]
hole = cyl_dir(4.5, 49.0 - parts_inlet.JFD01_V352["flat_r"] + 0.5, (-49.0, sc["y"], zs), (1.0, 0.0, 0.0))
fd = I0["ENG-FD-01#0"]
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
# wall = distance from the hole surface to the FD-01 outer boundary on the +y side within the ear: probe bisection on the hole
envfd = box((-41.0, sc["y"], zs - 6.0), (-29.6, 20.0, zs + 6.0))
def extra_fd(w):
    pr = cyl_dir(4.5 + 2 * w, 49.0 - 29.5, (-49.0, sc["y"], zs), (1.0, 0.0, 0.0)).intersect(envfd)
    return pr.cut(fd.fuse(hole)).Volume()
lo, hi = 0.0, 4.0
if extra_fd(hi) > 0.01:
    for _ in range(8):
        mid = 0.5 * (lo + hi)
        if extra_fd(mid) > 0.01:
            hi = mid
        else:
            lo = mid
    wfd = round(lo, 3)
else:
    wfd = ">4.0"
out["fd01_ear_wall_plus_y"] = {"screw_y": sc["y"], "z": round(zs, 3), "hole_d": 4.5, "min_wall_mm_to_relief_or_face": wfd,
                               "region": "x -41 (cbore floor) .. -29.6 (flat), +y side"}
print("fd01 ear wall", out["fd01_ear_wall_plus_y"], flush=True)
# (e) head envelopes
heads = []
for a in angs:
    u = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0])
    st = u * 31.75 + np.array([0.0, 0.0, zb_])
    heads.append(cyl_dir(9.5, 2.75 + 0.1, tuple(st), tuple(u)))
recs = []
for nm, al, be in build.pose_list(P, S):
    Te = build.group_T("engine", al, be)
    H = [apply(h, Te) for h in heads]
    insts = build.posed_instances(reg, S, al, be)
    for k, h in enumerate(H):
        bh = bbox(h)
        for (pn, i, g, sh, body) in insts:
            if pn == "ENG-TC-01":
                continue
            if nm != "neutral" and g == "engine" and body == "engine":
                continue
            bs = bbox(sh)
            if not checks.bb_overlap(bh, bs, 4.0):
                continue
            dd, q1, q2 = checks.min_distance(h, sh)
            if dd < 3.0:
                recs.append({"pose": nm, "head_az": angs[k], "other": f"{pn}#{i}", "group": g, "dist_mm": round(dd, 3)})
recs.sort(key=lambda r: r["dist_mm"])
out["jfwd_head_envelopes"] = {"envelope": "cyl d 9.5 x 2.85 radially from r 31.75 at each screw axis (ISO 7380-1 M5 dk 9.5 / k 2.75 + 0.1)",
                              "close_lt_3mm": recs[:60], "min_mm": (recs[0]["dist_mm"] if recs else None), "n_close": len(recs)}
print("heads min", out["jfwd_head_envelopes"]["min_mm"], recs[:8], flush=True)
s = json.dumps(out, indent=1, default=str)
open("/home/claude/work/mechanical/v352/checks/test_interim352b_v1.json", "w").write(s)
print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16], "t", round(time.time() - t0, 1))
