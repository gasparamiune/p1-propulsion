"""Pre-check before make_all v3.5 (run 6): build, then interference (all pairs at neutral) and < 3 mm clearances (different rigid bodies)
for every pair that involves an ENG-BL part, at neutral and at every pose of build.pose_list.  Mechanical 2026-10-13.  Writes
precheck_bleed_v35_v1.json next to this script.  Not a substitute for checks.py in make_all (which covers every pair)."""
import sys, json, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build, config, checks
from geom import bbox
t0 = time.time()
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True, overrides=config.V34_ON)
out = {"version": "v1", "t_build_s": round(time.time() - t0, 1), "bleed": S.get("bleed"), "poses": {}}
poses = [("neutral", 0.0, 0.0)] + [(n, a, b) for n, a, b in [(q[0], q[1], q[2]) for q in build.pose_list(P, S)]]
import os
if os.environ.get("PRECHECK_POSES"):
    poses = [x for x in poses if x[0] in os.environ["PRECHECK_POSES"].split(",")]
for name, a, b in poses:
    inst = build.posed_instances(reg, S, a, b)
    bl = [t for t in inst if t[0].startswith("ENG-BL")]
    bbl = [bbox(t[3]) for t in bl]
    near = [t for t in inst if not t[0].startswith("ENG-BL") and any(checks.bb_overlap(bbox(t[3]), q, 6.0) for q in bbl)]
    sub = bl + near
    hits, close = [], []
    bbs = [bbox(t[3]) for t in sub]
    for i, (pa, ia, ga, sa, ba) in enumerate(sub):
        for j in range(i + 1, len(sub)):
            pb, ib, gb, sb, bb_ = sub[j]
            if not (pa.startswith("ENG-BL") or pb.startswith("ENG-BL")):
                continue                                   # pairs without a bleed part are covered by make_all checks
            if not checks.bb_overlap(bbs[i], bbs[j], 6.0):
                continue
            if checks.bb_overlap(bbs[i], bbs[j]) and (name == "neutral" or ba != bb_):
                v = checks.common_volume(sa, sb)
                if v > 0.5:
                    hits.append({"a": f"{pa}#{ia}", "b": f"{pb}#{ib}", "common_mm3": round(v, 2), "whitelisted": checks._wl(pa, pb, v) or ""})
            if ba != bb_ and not checks._wl(pa, pb):
                d, p1, p2 = checks.min_distance(sa, sb)
                if d < 3.0:
                    close.append({"a": f"{pa}#{ia}", "b": f"{pb}#{ib}", "dist_mm": round(d, 3), "at": [round(c, 1) for c in p1] if p1 else None,
                                  "expected_contact": checks._ec(pa, pb, name)})
    out["poses"][name] = {"alpha": a, "beta": b, "n_sub": len(sub), "interference": hits,
                          "close_unexpected": [c for c in close if not c["expected_contact"]], "n_close_expected": sum(1 for c in close if c["expected_contact"])}
    print(name, len(sub), "interf", [(h["a"], h["b"], h["common_mm3"], h["whitelisted"] != "") for h in hits],
          "close", [(c["a"], c["b"], c["dist_mm"]) for c in close if not c["expected_contact"]], round(time.time() - t0), flush=True)
out["t_s"] = round(time.time() - t0, 1)
(HERE / f"precheck_bleed_v35_v1{os.environ.get('PRECHECK_TAG', '')}.json").write_text(json.dumps(out, indent=1, default=str))
print("done", out["t_s"])
