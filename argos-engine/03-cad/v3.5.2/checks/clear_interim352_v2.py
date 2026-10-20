"""v2 (2026-10-20, after lead CHANGELOG 231: J-FWD 10x M5 at az 18 + 36k, no case land; FD-01 +y lower ear relieved round BL-03E; FD-04 top
trimmed 1 mm below the J-FWD screw heads): changed-part list extended to every part whose geometry differs from v3.5.1 (GM-01, GM-02, TC-01,
TC-02, FD-01, FD-02 (moved 1 mm with the TC-02 flat), FD-04, NZ-01, NZ-02, NZ-06 new, TC-09; make_all v3.5.2 part STL/volume diff).  v1 (pre-fix, 2 non-whitelisted hits) kept as clear_interim352_v1.json.
v3.5.2 INTERIM targeted interference / clearance check for the changed parts (GM-01, GM-02, TC-01, TC-02, FD-01) against every other
instance: all pairs at neutral (static, same as make_all 'checks' at neutral) and relatively moving pairs at all 18 poses of build.pose_list
(common volume > 0.5 mm3 = interference, whitelist of checks.py applied; exact min distance < 3 mm listed).  Software check, not physical
validation.  Mechanical, 2026-10-19."""
import sys, json, hashlib, time, itertools
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import config, build, checks
from geom import bbox
CHG = ("ENG-GM-01", "ENG-GM-02", "ENG-TC-01", "ENG-TC-02", "ENG-FD-01", "ENG-FD-02", "ENG-FD-04", "ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-06",
       "ENG-TC-09")
t0 = time.time()
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V352_ON))
out = {"id": "clear_interim352", "version": "v2", "date": "2026-10-20", "owner": "mechanical", "cad": "v3.5.2 interim v2 (config.V352_ON after lead 231)",
       "changed": CHG, "t_build_s": round(time.time() - t0, 1), "poses": []}
for nm, a, b in build.pose_list(P, S):
    t1 = time.time()
    inst = build.posed_instances(reg, S, a, b)
    bbs = [bbox(t[3]) for t in inst]
    hits, close = [], []
    for i, j in itertools.combinations(range(len(inst)), 2):
        pa, ia, ga, sa, ba = inst[i]
        pb, ib, gb, sb, bb_ = inst[j]
        if pa not in CHG and pb not in CHG:
            continue
        moving = ba != bb_
        if nm != "neutral" and not moving:
            continue
        if checks.bb_overlap(bbs[i], bbs[j]):
            v = checks.common_volume(sa, sb)
            if v > 0.5:
                hits.append({"a": f"{pa}#{ia}", "b": f"{pb}#{ib}", "common_mm3": round(v, 2), "whitelisted": checks._wl(pa, pb, v) or ""})
        if moving and checks.bb_overlap(bbs[i], bbs[j], 6.0) and not checks._wl(pa, pb):
            d, p1, p2 = checks.min_distance(sa, sb)
            if d < 3.0:
                close.append({"a": f"{pa}#{ia}", "b": f"{pb}#{ib}", "dist_mm": round(d, 3), "at": [round(c, 1) for c in p1] if p1 else None,
                              "expected_contact": checks._ec(pa, pb, nm)})
    rec = {"pose": nm, "alpha": a, "beta": b, "interference": hits, "not_whitelisted": [h for h in hits if not h["whitelisted"]],
           "close_lt_3mm": sorted(close, key=lambda r: r["dist_mm"]), "t_s": round(time.time() - t1, 1)}
    out["poses"].append(rec)
    print(nm, round(a, 2), round(b, 2), "hits", len(hits), "not-wl", len(rec["not_whitelisted"]), "close<3", [(c["a"], c["b"], c["dist_mm"]) for c in rec["close_lt_3mm"][:4]], rec["t_s"], "s", flush=True)
out["summary"] = {"n_not_whitelisted": sum(len(r["not_whitelisted"]) for r in out["poses"]),
                  "min_moving_clearance_mm": min([c["dist_mm"] for r in out["poses"] for c in r["close_lt_3mm"] if not c["expected_contact"]] or [None])}
s = json.dumps(out, indent=1, default=str)
open("/home/claude/work/mechanical/v352/checks/clear_interim352_v2.json", "w").write(s)
print(json.dumps(out["summary"])); print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])
