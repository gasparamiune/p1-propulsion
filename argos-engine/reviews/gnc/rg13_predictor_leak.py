"""rg13_predictor_leak v1 (independent GNC review, 2026-10-13): effect of a truth leak in the B-profile apex predictor.

Finding: in sim6 v2.7.1-dev the B-profile MECO / apex predictor (sim6.py l.886-889) uses the TRUE delivered thrust F in the
ramp-down term (Fsw, t_ramp, dv1), whereas the A-profile MECO predictor uses the Pc-based estimate F / tsc (l.856, l.871),
which is what the flight computer can know. With the run's thrust_scale draw N(1, 0.05) (and throat growth), the simulated
B predictor therefore knows the delivered thrust that the real FSW does not; the k_est_asc 2 estimator is gated t > 1 s,
and B1 at 62 m reaches MECO at t ~ 0.88-0.90 s, before the estimator runs.
Variant (reviewer, scratch copy simcopy_rg13, NOT a proposal of code): the three lines use Fp_ = F / tsc. Everything else is
byte-identical to the hub copy. Same draws (seed 101), B1 62 m band + growth (rbl_B1_lead62_pc_k2), 500 runs, paired
against the published run table (exact McNemar).
Output: rg13_predictor_leak.json. One process.
"""
import csv
import gzip
import json
import os
import sys
import time

SCR = "/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad"
os.environ["RG_SIMCOPY"] = f"{SCR}/simcopy_rg13"
os.environ["NUMBA_CACHE_DIR"] = f"{SCR}/numba_cache_rg13"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import rg05_sens as S  # noqa: E402
import numpy as np  # noqa: E402

PUB = "/home/claude/work/shared-fallback/engine/01-systems-gnc/results/regband/mc6_runs_rbl_B1_lead62_pc_k2_rb.csv.gz"


def main():
    assert S.COPY.endswith("simcopy_rg13"), S.COPY
    t0 = time.time()
    over = S.RBM.cases(None)["rbl_B1_lead62_pc_k2"][0]
    rows = S.fly_case(over, {})
    with gzip.open(PUB, "rt") as f:
        pub = list(csv.DictReader(f))
    pub_ok = [bool(int(float(r["ok"]))) for r in pub]
    pub_h = np.array([float(r["h_max"]) for r in pub])
    ok = [r["ok"] for r in rows]
    lost = sum(1 for a, b in zip(pub_ok, ok) if a and not b)
    gained = sum(1 for a, b in zip(pub_ok, ok) if (not a) and b)
    hv = np.array([r["h_max"] for r in rows])
    s = S.summ(rows)
    out = dict(script="rg13_predictor_leak v1", variant_copy=S.COPY, case="rbl_B1_lead62_pc_k2", n=len(rows),
               P_published=sum(pub_ok) / len(pub_ok), P_variant=s["P"], ci95_variant=s["ci95"], lost=lost, gained=gained,
               p_exact=S.mcnemar(lost, gained), n_exhausted=s["n_exhausted"], usable_p01=s["usable_p01"],
               usable_min=s["usable_min"], burn_p50_p99_max=s["burn_p50_p99_max"], fail_modes=s["fail_modes"],
               h_max_published=dict(p50=float(np.percentile(pub_h, 50)), p99=float(np.percentile(pub_h, 99)), max=float(pub_h.max())),
               h_max_variant=dict(p50=float(np.percentile(hv, 50)), p99=float(np.percentile(hv, 99)), max=float(hv.max())),
               h_max_diff=dict(mean=float(np.mean(hv - pub_h)), sd=float(np.std(hv - pub_h)), min=float(np.min(hv - pub_h)),
                               max=float(np.max(hv - pub_h))), cpu_s=time.time() - t0)
    print(json.dumps(out, indent=1), flush=True)
    json.dump(out, open(os.path.join(HERE, "rg13_predictor_leak.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
