"""Bay-wall sweep of every moving part (lead CHANGELOG 182 (5)), v1, 2026-10-13, Mechanical.

Builds the assembly (config.V351_ON, or config.V34_ON when the first extra argument is BASE=V34, plus optional KEY=VALUE overrides),
runs checks.bay_wall_sweep (every moving instance, 72 directions x tilt 0..stop in 1 deg steps incl. 7 and 8 deg, plus the stop polygon;
signed; rule r <= 69.0 mm) and checks.fixed_wall_check (fixed instances on the bore, whitelist BL-06) and writes the JSON to argv[1].
v2 (2026-10-13): REV-MECH-1 RM1-02 / lead 188 (2).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "src"))   # hub layout: 03-cad/calcs next to 03-cad/src
import config, build, checks          # noqa: E402


def main():
    out = Path(sys.argv[1])
    args = sys.argv[2:]
    ov = dict(config.V351_ON)
    if args and args[0] == "BASE=V34":
        ov = dict(config.V34_ON)
        args = args[1:]
    for a in args:
        k, v = a.split("=", 1)
        try:
            v = json.loads(v)
        except Exception:
            pass
        ov[k] = v
    t0 = time.time()
    P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True, overrides=ov)
    t1 = time.time()
    res = checks.bay_wall_sweep(reg, S, P)
    res["fixed_wall_check"] = checks.fixed_wall_check(reg, S)
    res.update({"id": "bay_wall_sweep", "version": "v2", "date": "2026-10-13", "owner": "mechanical",
                "script": "03-cad/src/calcs/bay_wall_v351.py + checks.bay_wall_sweep", "overrides_extra": sys.argv[2:],
                "t_build_s": round(t1 - t0, 1), "t_sweep_s": round(time.time() - t1, 1)})
    out.write_text(json.dumps(res, indent=1))
    print(f"build {t1 - t0:.0f} s, sweep {time.time() - t1:.0f} s, moving fail {res['fail']}, fixed fail {res['fixed_wall_check']['fail']}")
    for r in res["fixed_wall_check"]["rows"][:8]:
        print(f"  fixed {r['inst']:16s} r_max {r['r_max_mm']:7.3f} into wall {r['into_wall_mm']:+7.3f} ok {r['ok']} {r.get('volume_beyond_bore_mm3', '')}")
    for r in res["rows"][:25]:
        print(f"{r['inst']:16s} {r['group']:8s} r {r['r_max_mm']:7.3f} clear {r['clear_to_bore_mm']:6.3f} ok {r['ok']} "
              f"pose {r['pose']} at {r['at_mm']} {r.get('exact_dist_to_bore_mm', '')}")


if __name__ == "__main__":
    main()
