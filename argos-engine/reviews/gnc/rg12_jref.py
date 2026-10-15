"""rg12_jref v1 (independent GNC review, 2026-10-13): how often the published dispersed B1 runs exceed the throat-growth
reference J_ref, beyond which sim6 holds the growth at the drawn band value (sim6.py l.688:
g = throat_g * min(1, J / J_ref), J = int (Pc/Pc_max)^0.68 dt).

J_ref from the author's own function (m2_throat_mc.j_ref, nominal flight without growth) for B1 62 m and 85 m; run tables:
rbl_B1_lead62_pc_k2 (62 m band + growth) and tg_B1_pc_k2 (85 m growth). Reports the fraction of runs with J > J_ref and
J / J_ref at p99 and max, i.e. the growth a J-proportional law would give at the drawn band value g (U(0.07, 0.11)):
g x J / J_ref. Interpretation (HYPOTHESIS): if erosion keeps growing with J, the Monte Carlo under-represents the growth of
the long dispersed burns, which are the ones close to exhaustion.
Output: rg12_jref.json
"""
import csv
import gzip
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import rg05_sens as S  # noqa: E402

RES = "/home/claude/work/shared-fallback/engine/01-systems-gnc/results"


def col(fn, k):
    with gzip.open(os.path.join(RES, fn), "rt") as f:
        return np.array([float(r[k]) for r in csv.DictReader(f)])


def main():
    out = dict(script="rg12_jref v1", cases={})
    for nm, h, fn in (("B1 62 m band+growth (rbl_B1_lead62_pc_k2)", 62.0, "regband/mc6_runs_rbl_B1_lead62_pc_k2_rb.csv.gz"),
                      ("B1 85 m growth (tg_B1_pc_k2)", 85.0, "throat_growth/mc6_runs_tg_B1_pc_k2_tg.csv.gz")):
        jref = float(S.TG.j_ref(dict(S.PC.DC["B1"], h_target=h, k_est_asc=2))[0])
        J = col(fn, "throat_J")
        g_end = col(fn, "throat_g_end")
        r = J / jref
        out["cases"][nm] = dict(J_ref=jref, n=int(J.size), frac_J_over_Jref=float(np.mean(r > 1.0)),
                                J_over_Jref_p50=float(np.percentile(r, 50)), J_over_Jref_p99=float(np.percentile(r, 99)),
                                J_over_Jref_max=float(r.max()), g_end_max=float(g_end.max()),
                                implied_growth_if_J_proportional_max=float(np.max(g_end * np.maximum(r, 1.0))))
        print(nm, json.dumps(out["cases"][nm]), flush=True)
    json.dump(out, open(os.path.join(HERE, "rg12_jref.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
