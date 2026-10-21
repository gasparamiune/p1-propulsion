"""m2_ctrlfix_eval v1.1 (variants of the chosen fix compared with the fix, same J). Evaluate the control-fix cases: P with Wilson interval, paired exact McNemar against the comparators (lead baseline
AD_prov_2kg and the same-J no-fix case), ENG-07b metric (p99 over runs of the longest saturation episode; landing burn),
saturated time, depth. Env GNC_OUT / GNC_SUFFIX as m2_ctrlfix_mc.py. Output: <out>/ctrlfix_eval_<suf>.json/.csv"""
import csv
import json
import os
import sys
import numpy as np
from scipy.stats import binomtest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/ctrlfix")
SUF = os.environ.get("GNC_SUFFIX", "cf")


def rows(c):
    p = os.path.join(OUT, f"mc6_runs_{c}_{SUF}.csv")
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def pair(a, b):
    oa = np.array([int(r["ok"]) for r in a]) > 0
    ob = np.array([int(r["ok"]) for r in b]) > 0
    lost, gained = int(np.sum(oa & ~ob)), int(np.sum(~oa & ob))
    p = binomtest(lost, lost + gained, 0.5).pvalue if lost + gained else 1.0
    return dict(lost=lost, gained=gained, p=float(p), loses=bool(ob.mean() < oa.mean() and p < 0.05))


def main():
    S = json.load(open(os.path.join(OUT, f"mc6_summary_{SUF}.json")))["cases"]
    base = rows("AD_prov_2kg")
    out = {}
    tab = []
    for c in S:
        r = rows(c)
        if r is None:
            continue
        ok = np.array([int(x["ok"]) for x in r]) > 0
        lo, hi = R.wilson(int(ok.sum()), len(ok))
        md = np.array([float(x["act_sat_max_dur"]) for x in r]) if "act_sat_max_dur" in r[0] else np.zeros(len(r))
        st = np.array([float(x["act_sat_time_land"]) for x in r]) if "act_sat_time_land" in r[0] else np.zeros(len(r))
        rec = dict(case=c, P=float(ok.mean()), ci95=[lo, hi], fail_modes=S[c]["summary"]["fail_modes"],
                   longest_ep_p99_s=float(np.percentile(md, 99)), longest_ep_max_s=float(md.max()),
                   longest_ep_p95_s=float(np.percentile(md, 95)),
                   frac_runs_ep_gt_0p1=float(np.mean(md > 0.1)), sat_time_land_p99_s=float(np.percentile(st, 99)),
                   ENG07b_pass=bool(np.percentile(md, 99) <= 0.1))
        if base is not None and c != "AD_prov_2kg":
            rec["vs_baseline"] = pair(base, r)
        if "_" in c and c.startswith("cf_J"):
            nf = "_".join(c.split("_")[:2]) + "_nofix"
            rn = rows(nf)
            if rn is not None and nf != c:
                rec["vs_nofix_same_J"] = pair(rn, r)
        if "_acc2000_ref40_" in c:                       # v1.1: variants of the chosen fix vs the fix itself (same J)
            fx = c.split("_acc2000_ref40_")[0] + "_acc2000_ref40"
            rf = rows(fx)
            if rf is not None:
                rec["vs_fix_same_J"] = pair(rf, r)
        out[c] = rec
        vb = rec.get("vs_baseline", {})
        vn = rec.get("vs_nofix_same_J", {})
        tab.append([c, f"{rec['P']:.3f} [{lo:.3f}, {hi:.3f}]",
                    f"-{vb.get('lost', '')}/+{vb.get('gained', '')} p {vb.get('p', float('nan')):.2g}{' LOSES' if vb.get('loses') else ''}" if vb else "-",
                    (f"-{vn.get('lost', '')}/+{vn.get('gained', '')} p {vn.get('p', float('nan')):.2g}" if vn else "-")
                    + (f" (vs fix: -{rec['vs_fix_same_J']['lost']}/+{rec['vs_fix_same_J']['gained']} p "
                       f"{rec['vs_fix_same_J']['p']:.2g})" if "vs_fix_same_J" in rec else ""),
                    f"{1e3 * rec['longest_ep_p99_s']:.0f}", f"{1e3 * rec['longest_ep_max_s']:.0f}",
                    f"{100 * rec['frac_runs_ep_gt_0p1']:.1f}", "PASS" if rec["ENG07b_pass"] else "FAIL"])
    json.dump(out, open(os.path.join(OUT, f"ctrlfix_eval_{SUF}.json"), "w"), indent=1)
    w = csv.writer(open(os.path.join(OUT, f"ctrlfix_eval_{SUF}.csv"), "w", newline=""))
    w.writerow(["case", "P [Wilson 95 %]", "vs AD_prov_2kg", "vs no-fix same J", "longest ep p99 ms", "max ms",
                "% runs > 100 ms", "ENG-07b"])
    w.writerows(tab)
    for t in tab:
        print(" | ".join(t))


if __name__ == "__main__":
    main()
