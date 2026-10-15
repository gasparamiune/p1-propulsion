"""rv09_stats_recompute v1.0 (REV-GNC-R1, independent reviewer, 2026-10-13).

Recomputes, with the reviewer's own exact McNemar (two-sided, p = min(1, 2 P[X <= min(lost, gained)]), X ~ Bin(n, 1/2)), the
paired lost/gained/p and exhausted counts GNC publishes for the purge-cost and the 1.0 mm stuck-open bleed arms, from the
hub-published run tables only (statistics check; these arms were NOT re-flown by the reviewer):
  purge_cost: pc_<base>_{PS10,PS08,PS10_L400} against release_rule/rel_<base>_rel1 (stored v2.8 FSW, decided rule)
  purge_bleed_1mm: pb_A1_{PS10_nojet,S313_0_nojet,S313_1_nojet} against pb_A1_ref; pb_B1_{B313_0,B313_1}_nojet against pb_B1_ref
    (flown-mass-estimator FSW without fct_comp)
Output: rv09_stats_recompute.json. Reads only.
"""
import csv
import gzip
import io
import json
import math
import os

R = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev1/results"
HERE = os.path.dirname(os.path.abspath(__file__))


def rows(p):
    return list(csv.DictReader(io.StringIO(gzip.open(p).read().decode())))


def flag(r, k):
    return [float(x[k]) > 0.5 for x in r]


def mcnemar(ref, case):
    lost = sum(1 for a, b in zip(ref, case) if a and not b)
    gained = sum(1 for a, b in zip(ref, case) if b and not a)
    n, k = lost + gained, min(lost, gained)
    p = min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return dict(P_ref=sum(ref) / len(ref), P_case=sum(case) / len(case), lost=lost, gained=gained, p_exact=p, n=len(ref))


def main():
    out = dict(version="rv09_stats_recompute v1.0", date="2026-10-13", purge_cost={}, purge_bleed_1mm={})
    for arm in ("PS10", "PS08", "PS10_L400"):
        A, B = [], []
        for base in ("A1_none", "A1J_pc"):
            ref = flag(rows(f"{R}/release_rule/rel_{base}_rel1.csv.gz"), "ok")
            r = rows(f"{R}/purge_cost/pc_{base}_{arm}.csv.gz")
            c = flag(r, "ok")
            out["purge_cost"][f"{base}|{arm}"] = dict(mcnemar(ref, c), exhausted=sum(flag(r, "exhausted")))
            A += ref
            B += c
        out["purge_cost"][f"pooled|{arm}"] = mcnemar(A, B)
    for prof, arms in (("A1", ("PS10_nojet", "S313_0_nojet", "S313_1_nojet")), ("B1", ("B313_0_nojet", "B313_1_nojet"))):
        ref = flag(rows(f"{R}/purge_bleed_1mm/pb_{prof}_ref.csv.gz"), "ok")
        for a in arms:
            r = rows(f"{R}/purge_bleed_1mm/pb_{prof}_{a}.csv.gz")
            out["purge_bleed_1mm"][f"{prof}|{a}"] = dict(mcnemar(ref, flag(r, "ok")), exhausted=sum(flag(r, "exhausted")))
    with open(os.path.join(HERE, "rv09_stats_recompute.json"), "w") as f:
        json.dump(out, f, indent=1)
    for part in ("purge_cost", "purge_bleed_1mm"):
        for k, v in out[part].items():
            print(f"{part:16s} {k:22s} P {v['P_case']:.3f} vs {v['P_ref']:.3f}  -{v['lost']}/+{v['gained']}  p {v['p_exact']:.3g}"
                  + (f"  exhausted {v['exhausted']}" if "exhausted" in v else ""))


if __name__ == "__main__":
    main()
