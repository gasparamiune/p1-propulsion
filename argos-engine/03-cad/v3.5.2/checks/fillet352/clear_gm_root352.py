"""v3.5.2 lever-root fillet DC (lead 2026-10-20, FEA3D INTERIM 1 item 1): kinematic clearance / interference re-check of GM-01 / GM-02
against every other instance.  Neutral: all pairs (common volume > 0.5 mm3 = interference, checks.py whitelist applied).  All poses of
build.pose_list (neutral, +/- 7 deg per axis, 4 combined 7 deg, 8 stop directions at 8 deg, hose stop): exact minimum distance of every
pair on different rigid bodies whose boxes are within 10 mm (rod end HW-22, pushrod GM-17, stud GM-18, washers GM-19, horn joint GM-20,
servo horn, ring GM-03, ...).  Run once on the source before and once after the change; the diff is the evidence.  Software check, not
physical validation.  Mechanical, 2026-10-20.  Usage: clear_gm_root352.py <03-cad/src dir> <out.json>"""
import sys, json, hashlib, time, itertools
from pathlib import Path
SRC = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(SRC)); sys.path.insert(0, str(SRC.parents[1] / "04-fea" / "src"))
import config, build, checks
from geom import bbox
GM = ("ENG-GM-01", "ENG-GM-02")
t0 = time.time()
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V352_ON))
vols = {p.pn: round(p.shape.Volume(), 3) for p in reg if p.pn in GM}
out = {"id": "clear_gm_root352", "src": str(SRC), "owner": "mechanical", "date": "2026-10-20", "volumes_mm3": vols,
       "root_v352": config.V352_ON["tvc_lever_v34"].get("root_v352"), "t_build_s": round(time.time() - t0, 1), "poses": []}
for nm, a, b in build.pose_list(P, S):
    t1 = time.time()
    inst = build.posed_instances(reg, S, a, b)
    bbs = [bbox(t[3]) for t in inst]
    hits, near = [], []
    for i, j in itertools.combinations(range(len(inst)), 2):
        pa, ia, ga, sa, ba = inst[i]
        pb, ib, gb, sb, bb_ = inst[j]
        if pa not in GM and pb not in GM:
            continue
        moving = ba != bb_
        if (nm == "neutral" or moving) and checks.bb_overlap(bbs[i], bbs[j]):
            v = checks.common_volume(sa, sb)
            if v > 0.5:
                hits.append({"a": f"{pa}#{ia}", "b": f"{pb}#{ib}", "common_mm3": round(v, 2), "whitelisted": checks._wl(pa, pb, v) or ""})
        if moving and checks.bb_overlap(bbs[i], bbs[j], 10.0):
            d, p1, p2 = checks.min_distance(sa, sb)
            if d < 10.0:
                near.append({"a": f"{pa}#{ia}", "b": f"{pb}#{ib}", "dist_mm": round(d, 3), "at": [round(c, 2) for c in p1] if p1 else None,
                             "expected_contact": checks._ec(pa, pb, nm)})
    out["poses"].append({"pose": nm, "alpha": a, "beta": b, "interference": hits, "not_whitelisted": [h for h in hits if not h["whitelisted"]],
                         "near_lt_10mm": sorted(near, key=lambda r: r["dist_mm"]), "t_s": round(time.time() - t1, 1)})
    print(nm, round(a, 2), round(b, 2), "hits", len(hits), "near", [(c["a"], c["b"], c["dist_mm"]) for c in sorted(near, key=lambda r: r["dist_mm"])[:3]],
          round(time.time() - t1, 1), "s", flush=True)
s = json.dumps(out, indent=1, default=str)
Path(sys.argv[2]).write_text(s)
print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])
