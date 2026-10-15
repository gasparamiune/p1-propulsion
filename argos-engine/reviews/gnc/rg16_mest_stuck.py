"""rg16_mest_stuck v1.1 (independent GNC review, 2026-10-13; addendum on the v3.1 STAGING set).
v1.1 adds part 2 (reviewer question, not in the author's set): a common systematic mass-estimate bias b added to c e at sd 1 %
(e -> c e + b, b < 0 = under-read of mass and thrust, the detection side); part 1 results unchanged from v1.

Re-implements the stuck-pintle part of m2_fc_thrust_mest v1 (staging_v3.1/sim/scripts) with the reviewer's rg15 functions:
the run's mass-estimate error e becomes c e in the synthetic ramps (bias factor (1 + c e)(1 + a_sf), noise and accelerometer
bias scaled by m (1 + c e)), with generator 20261020 re-created for each scale and the v1.1 loop order (VARS -> F0 -> Ff ->
rate -> 1000 healthy rows), so the noise samples are the same as v1.1 and as the author's scales.
Reports, for tau 20 ms and the 670 N final thrust: misses at 650 N (no held 3-frame value > 650 N before or after the onset),
the minimum post-onset held maximum, and the number of distinct error sets (seed-101 draws shared by A1 run i and B1 run i)
behind the misses; compared with staging fc_thrust_mest.json (by_sd.<sd>.tau20ms.stuck670_held_post_mean_sd_min_N and grid).
Inputs (read only): GNC work area fc_thrust_runs_{A1,B1}.npy; staging fc_thrust_mest.json. Output: rg16_mest_stuck.json.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import rg15_fct_review as Q  # noqa: E402

SDS = (0.005, 0.01, 0.015, 0.02, 0.03)
SD0 = 0.03
BIAS = (-0.005, -0.01, -0.015, -0.02)


def stuck_count(Hrows, c, b):
    rng = np.random.default_rng(20261020)
    misses, post_min, rows_m = 0, np.inf, set()
    for v, tau in Q.VARS:
        for F0 in Q.STUCK["F0_N"]:
            for Ff in Q.STUCK["F_final_N"]:
                for rate in Q.STUCK["rate_N_s"]:
                    for j, r in enumerate(Hrows):
                        bt = r["bias_terms"]
                        ec = c * bt["m_est_err"] + b
                        bf = (1.0 + ec) * (1.0 + bt["a_sf"])
                        mm = r["m_mean_burn_kg"] * (1.0 + ec)
                        tf, hs = Q.stuck_series(bf, mm * bt["a_bz"], mm, r["a_vrw"], r["vib_sigma"], r["Fmax"], F0, Ff,
                                                rate, tau, rng)
                        if v == "tau20ms" and Ff == 670.0:
                            hpre = hs[tf < 0.0].max()
                            hpost = hs[tf >= 0.0].max()
                            post_min = min(post_min, hpost)
                            if hpre <= 650.0 and hpost <= 650.0:
                                misses += 1
                                rows_m.add(j)
    return misses, post_min, rows_m


def main():
    store = {}
    for p in ("A1", "B1"):
        store.update(np.load(os.path.join(Q.WA, f"fc_thrust_runs_{p}.npy"), allow_pickle=True)[0])
    Hrows = store["A1|H"] + store["B1|H"]
    pub = json.load(open(os.path.join(Q.STG, "fc_thrust_mest.json")))["by_sd"]
    out = dict(script="rg16_mest_stuck v1.1", by_sd={})
    for sd in SDS:
        c = sd / SD0
        rng = np.random.default_rng(20261020)
        misses, post_min, rows_m = 0, np.inf, set()
        for v, tau in Q.VARS:
            for F0 in Q.STUCK["F0_N"]:
                for Ff in Q.STUCK["F_final_N"]:
                    for rate in Q.STUCK["rate_N_s"]:
                        for j, r in enumerate(Hrows):
                            bt = r["bias_terms"]
                            ec = c * bt["m_est_err"]
                            bf = (1.0 + ec) * (1.0 + bt["a_sf"])
                            mm = r["m_mean_burn_kg"] * (1.0 + ec)
                            tf, hs = Q.stuck_series(bf, mm * bt["a_bz"], mm, r["a_vrw"], r["vib_sigma"], r["Fmax"], F0, Ff,
                                                    rate, tau, rng)
                            if v == "tau20ms" and Ff == 670.0:
                                hpre = hs[tf < 0.0].max()
                                hpost = hs[tf >= 0.0].max()
                                post_min = min(post_min, hpost)
                                if hpre <= 650.0 and hpost <= 650.0:
                                    misses += 1
                                    rows_m.add(j)
        p = pub[f"{sd:g}"]["tau20ms"]
        out["by_sd"][f"{sd:g}"] = dict(misses_670_at_650=misses, post_min_N=float(post_min),
                                       distinct_rows=len(rows_m), distinct_error_sets=len(set(j % 500 for j in rows_m)),
                                       published_post_min_N=float(p["stuck670_held_post_mean_sd_min_N"][2]),
                                       published_miss_670_at_650=int(p["grid"]["650"]["miss_670"]))
        print(sd, json.dumps(out["by_sd"][f"{sd:g}"]), flush=True)
    out["bias_at_sd_1pct"] = {}
    for b in BIAS:
        m, pm, rows_m = stuck_count(Hrows, 0.01 / SD0, b)
        out["bias_at_sd_1pct"][f"{b:+g}"] = dict(misses_670_at_650=m, of_cases=4000, post_min_N=float(pm),
                                                 distinct_error_sets=len(set(j % 500 for j in rows_m)))
        print("bias", b, json.dumps(out["bias_at_sd_1pct"][f"{b:+g}"]), flush=True)
    json.dump(out, open(os.path.join(HERE, "rg16_mest_stuck.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
