"""Impact of the sim6 v2.4 rotational-integrator fix on the Monte Carlo results (v2.3 -> v2.4, same draws).

For every case present in both run sets: success P in each version, runs whose outcome flipped, and the largest
per-run change of the touchdown metrics. Inputs: GNC_OUT_OLD (v2.3 run CSVs, default the archive) and GNC_OUT (v2.4).
Output: GNC_RES/integrator_change_v23_v24.csv. Run: python scripts/m2_integrator_impact.py
"""
import csv
import os

import numpy as np

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
OLD = os.environ.get("GNC_OUT_OLD", "/home/claude/work/space/out/archive_v2.3/m2")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
KEYS = ("td_vz", "td_vh", "td_tilt", "td_rate", "td_miss", "prop_used", "max_roll_rate", "max_hinge")


def load(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def main():
    rows = []
    pre, post = "mc6_runs_", f"_{SUFFIX}.csv"
    for fn in sorted(os.listdir(OUT)):
        if not (fn.startswith(pre) and fn.endswith(post)):
            continue
        case = fn[len(pre):-len(post)]
        p_old = os.path.join(OLD, fn)
        if not os.path.exists(p_old):
            continue
        a, b = load(p_old), load(os.path.join(OUT, fn))
        if len(a) != len(b):
            rows.append(dict(case=case, note=f"run counts differ {len(a)} vs {len(b)}"))
            continue
        oa = np.array([float(r["ok"]) for r in a]) > 0.5
        ob = np.array([float(r["ok"]) for r in b]) > 0.5
        row = dict(case=case, n=len(a), P_v23=oa.mean(), P_v24=ob.mean(), flipped_ok_to_fail=int(np.sum(oa & ~ob)),
                   flipped_fail_to_ok=int(np.sum(~oa & ob)))
        landed = np.array([float(r["landed"]) > 0.5 and float(s["landed"]) > 0.5 for r, s in zip(a, b)])
        for k in KEYS:
            if k not in a[0] or k not in b[0]:
                continue
            da = np.array([abs(float(r[k]) - float(s[k])) for r, s in zip(a, b)])
            da = da[landed] if k.startswith("td_") else da
            row[f"max_abs_change_{k}"] = float(np.max(da)) if da.size else float("nan")
            row[f"median_abs_change_{k}"] = float(np.median(da)) if da.size else float("nan")
        rows.append(row)
        print(f"{case:24s} P {row['P_v23']:.3f} -> {row['P_v24']:.3f}  flips -{row['flipped_ok_to_fail']} "
              f"+{row['flipped_fail_to_ok']}  max d td_vh {row.get('max_abs_change_td_vh', float('nan')):.3g} "
              f"max d roll rate {row.get('max_abs_change_max_roll_rate', float('nan')):.3g}")
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(RES, "integrator_change_v23_v24.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print("written", os.path.join(RES, "integrator_change_v23_v24.csv"))


if __name__ == "__main__":
    main()
