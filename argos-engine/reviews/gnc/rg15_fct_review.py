"""rg15_fct_review v1 (independent GNC review, 2026-10-13; addendum on the v3.1 STAGING set, FC_THRUST over-thrust abort).

Inputs (read only):
  - GNC work area /home/claude/work/space/out/fc_thrust/fc_thrust_runs_{A1,B1}.npy (m2_fc_thrust v1.1 per-run stores, the source
    of staging_v3.1/results/fc_thrust/fc_thrust.json);
  - staging_v3.1/results/fc_thrust/fc_thrust.json and fc_thrust_mest.json (published counts, for the reproduction checks);
  - reviews/gnc/rg05_sens.json 'nominal' (the author's nominal A1 and B1 85 m records, 0.1 s) for the flow-integration term.
Checks:
  1. Shared draws: are the per-run bias terms (m_est_err, a_sf, a_bz) of A1 run i and B1 run i identical? (seed 101 for both)
  2. Pc-lost branch: run-by-run correlation of the A1 and B1 held maxima (tau 20 ms, fc window), and their dependence on the
     bias factor (1 + e)(1 + a_sf); effective sample of the pooled 1000 flights for a bias-driven tail.
  3. Stuck pintle: re-implementation of v1.1's synthetic ramp loop (same generator 20261020 and loop order, so the same noise
     samples), counting the 670 N misses at 650 N (tau 20 ms) per error set; check against the published 252/4000; how many
     distinct error sets produce them.
  4. Flow-integrating mass estimate in the Pc-lost condition (HYPOTHESIS of the estimator form, gnc.json v3 request 'integrated
     flow from the ECU map'): if the open-loop band top 1.143 is a flow (Cd) excess and the FC integrates the map flow, the
     estimate over-reads mass by (m0 - b) / (m0 - 1.143 b) - 1 at burned map propellant b. Evaluated on the nominal records.
Output: rg15_fct_review.json
"""
import json
import os

import numpy as np
from scipy.signal import lfilter

HERE = os.path.dirname(os.path.abspath(__file__))
WA = "/home/claude/work/space/out/fc_thrust"
STG = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/results/fc_thrust"
DT, KF, NH = 1.0e-3, 10, 2
VARS = (("raw", 0.0), ("box10ms", -1.0), ("tau10ms", 0.010), ("tau20ms", 0.020))
STUCK = dict(F_final_N=(670.0, 876.0), rate_N_s=(2500.0, 3600.0), F0_N=(500.0, 150.0))


def lp(x, tau):
    if tau <= 0.0:
        return x.copy()
    a = DT / (tau + DT)
    y, _ = lfilter([a], [1.0, -(1.0 - a)], x, zi=[(1.0 - a) * x[0]])
    return y


def filt(x, tau):
    if tau < 0.0:
        c = np.cumsum(np.concatenate([[0.0], x]))
        y = np.empty_like(x)
        y[KF - 1:] = (c[KF:] - c[:-KF]) / KF
        y[:KF - 1] = c[1:KF] / np.arange(1, KF)
        return y
    return lp(x, tau)


def held_series(fa):
    out = np.full(len(fa), -np.inf)
    if len(fa) > NH:
        out[NH:] = np.lib.stride_tricks.sliding_window_view(fa, NH + 1).min(axis=1)
    return out


def stuck_series(bf, a_bz_N, mm, a_vrw, vib, Fmax, F0, Ff, rate, tau, rng):
    n = int(2.5 / DT)
    tt = np.arange(n) * DT - 0.5
    Ft = np.where(tt < 0.0, F0, np.minimum(F0 + rate * np.maximum(tt, 0.0), Ff))
    x = bf * Ft + a_bz_N + mm * (a_vrw / np.sqrt(DT) + vib * Ft / Fmax) * rng.standard_normal(n)
    p0 = int(rng.integers(0, KF))
    fy = np.round(filt(x, tau)[p0::KF] * 10.0) / 10.0
    return tt[p0::KF], held_series(fy)


def upper95_zero(n):
    return float(1.0 - 0.05 ** (1.0 / n))


def main():
    store = {}
    for p in ("A1", "B1"):
        store.update(np.load(os.path.join(WA, f"fc_thrust_runs_{p}.npy"), allow_pickle=True)[0])
    out = dict(script="rg15_fct_review v1", inputs=dict(work_area=WA, staging=STG))
    # 1. shared draws
    keys = ("m_est_err", "a_sf", "a_bz")
    same = {k: bool(all(store["A1|H"][i]["bias_terms"][k] == store["B1|H"][i]["bias_terms"][k] for i in range(500))) for k in keys}
    out["shared_bias_terms_A1_B1_per_run"] = same
    # 2. Pc-lost held maxima
    hA = np.array([r["tau20ms"]["held_max_fc_N"] for r in store["A1|L"]])
    hB = np.array([r["tau20ms"]["held_max_fc_N"] for r in store["B1|L"]])
    bfA = np.array([(1 + r["bias_terms"]["m_est_err"]) * (1 + r["bias_terms"]["a_sf"]) for r in store["A1|L"]])
    rho = float(np.corrcoef(hA, hB)[0, 1])
    r2A = float(np.corrcoef(hA, bfA)[0, 1] ** 2)
    r2B = float(np.corrcoef(hB, bfA)[0, 1] ** 2)
    n_eff = 1000.0 / (1.0 + rho)
    out["pc_lost_tau20"] = dict(held_max_max_N=[float(hA.max()), float(hB.max())], corr_A1_B1_run_by_run=rho,
                                R2_on_bias_factor=[r2A, r2B], n_eff_pooled=n_eff,
                                upper95_zero_events=dict(n_1000=upper95_zero(1000), n_eff=upper95_zero(int(n_eff)),
                                                         n_500=upper95_zero(500)))
    # 3. stuck ramps (same generator and loop order as m2_fc_thrust v1.1 part_eval)
    Hrows = store["A1|H"] + store["B1|H"]
    rng = np.random.default_rng(20261020)
    miss = {}
    for v, tau in VARS:
        for F0 in STUCK["F0_N"]:
            for Ff in STUCK["F_final_N"]:
                for rate in STUCK["rate_N_s"]:
                    mlist = []
                    for j, r in enumerate(Hrows):
                        bt = r["bias_terms"]
                        bf = (1.0 + bt["m_est_err"]) * (1.0 + bt["a_sf"])
                        mm = r["m_mean_burn_kg"] * (1.0 + bt["m_est_err"])
                        tf, hs = stuck_series(bf, mm * bt["a_bz"], mm, r["a_vrw"], r["vib_sigma"], r["Fmax"], F0, Ff, rate, tau, rng)
                        if v == "tau20ms" and Ff == 670.0:
                            pre = bool((hs[tf < 0.0] > 650.0).any())
                            post = bool((hs[tf >= 0.0] > 650.0).any())
                            if (not pre) and (not post):
                                mlist.append(j)
                    if v == "tau20ms" and Ff == 670.0:
                        miss[(F0, rate)] = mlist
    tot = sum(len(x) for x in miss.values())
    rows_with_miss = sorted(set(j for x in miss.values() for j in x))
    runs_with_miss = sorted(set(j % 500 for j in rows_with_miss))
    e_of = {j: Hrows[j]["bias_terms"]["m_est_err"] for j in rows_with_miss}
    bf_of = {j: (1 + Hrows[j]["bias_terms"]["m_est_err"]) * (1 + Hrows[j]["bias_terms"]["a_sf"]) for j in rows_with_miss}
    pub = json.load(open(os.path.join(STG, "fc_thrust.json")))["stuck_pintle_detection"]["by_case"]
    pub_tot = sum(pub[f"tau20ms|T650|F0 {F0:g}|Ff 670|rate {rt:g}"]["miss"] for F0 in STUCK["F0_N"] for rt in STUCK["rate_N_s"])
    per_run_cases = {}
    for x in miss.values():
        for j in x:
            per_run_cases[j % 500] = per_run_cases.get(j % 500, 0) + 1
    out["stuck_670N_tau20_T650"] = dict(misses_reproduced=tot, misses_published=pub_tot, distinct_rows=len(rows_with_miss),
                                        distinct_error_sets=len(runs_with_miss),
                                        cases_per_error_set_hist={str(k): int(sum(1 for v in per_run_cases.values() if v == k))
                                                                  for k in range(1, 9)},
                                        bias_factor_of_missing_rows_max=float(max(bf_of.values())) if bf_of else None,
                                        m_est_err_of_missing_rows_max=float(max(e_of.values())) if e_of else None,
                                        population_distinct_error_sets=500, cases_total=4000,
                                        upper95_zero=dict(as_published_n_1000=upper95_zero(1000), distinct_sets_n_500=upper95_zero(500)))
    # 4. flow-integration term (nominal records)
    nom = json.load(open(os.path.join(HERE, "rg05_sens.json")))["nominal"]
    fi = {}
    for nm, m0 in (("A1_plan0.81_liq_med", 16.0746), ("B1_85m", 15.4246)):
        h = np.array(nom[nm]["hist"])
        c = {k: h[:, i] for i, k in enumerate(nom[nm]["hist_cols"])}
        t = c["t"]
        md = c["mox"] + c["mf"]
        b = np.concatenate([[0.0], np.cumsum(0.5 * (md[1:] + md[:-1]) * np.diff(t))])
        ratio = (m0 - b) / (m0 - 1.143 * b) - 1.0
        F = c["F"]
        hi = F >= 0.9 * 500.0
        fi[nm] = dict(over_read_at_full_thrust_max=float(ratio[hi].max()) if hi.any() else None,
                      over_read_end_of_burn=float(ratio[np.where(F > 1.0)[0][-1]]),
                      burned_map_kg_end=float(b[np.where(F > 1.0)[0][-1]]),
                      over_read_N_at_571p5N_full_thrust_max=float(571.5 * ratio[hi].max()) if hi.any() else None)
    out["flow_integration_bias_pc_lost_hypothesis"] = fi
    print(json.dumps(out, indent=1))
    json.dump(out, open(os.path.join(HERE, "rg15_fct_review.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
