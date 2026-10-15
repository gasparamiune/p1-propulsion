"""rg01_stats v1 (independent GNC review, 2026-10-13).

Recomputes, from the published run tables only, the statistics quoted in 01-systems-gnc/REPORT-v3.md (C1-C5) and
interfaces/gnc.json v3:
  - P = k/n and the Wilson 95 % interval (own implementation, z = 1.96);
  - the exact two-sided McNemar test on the discordant pairs (own exact integer binomial arithmetic, no scipy);
  - pairing checks: run index identical row by row, and the seed-101 draws identical (wind, thrust_scale, T0, seed-driven
    columns) between every compared pair of cases;
  - the break-even prior q* = dN / (dN + dF) and a joint bootstrap over run indices (the author's seed 20261019 and order,
    to reproduce; and an independent seed, to test the stability of the interval);
  - review additions (not in the report): q* computed on the fault-path SPREAD instead of the fixed 1.37 s worst point,
    and the per-line-state P with the Combustion RC-03 abort fraction at W = 0.65 s folded in (no retry: an abort is a loss).

Inputs (read-only): hub 01-systems-gnc/results/{relight_v28,regband,throat_growth}/*.csv.gz and relight_v28.json;
Combustion work area relight_latency_sup_v2p4.json (RC-03, sha256/16 f0ea1eb9905919ce, the file the author used).
Output: rg01_stats.json next to this script.
Run: /opt/engine-venv/bin/python -I rg01_stats.py
"""
import csv
import gzip
import hashlib
import json
import math
import os
from fractions import Fraction

import numpy as np

HUB = "/home/claude/work/shared-fallback/engine"
RES = f"{HUB}/01-systems-gnc/results"
RC03 = "/home/claude/work/combustion/data/v2/v2p4/relight_latency_sup_v2p4.json"
HERE = os.path.dirname(os.path.abspath(__file__))


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def rows(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:
        return list(csv.DictReader(f))


def wilson(k, n, z=1.96):
    p = k / n
    den = 1.0 + z * z / n
    c = (p + z * z / (2.0 * n)) / den
    h = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar_exact(b, c):
    """Two-sided exact McNemar: 2 x P(X <= min(b, c)), X ~ Bin(b + c, 1/2), capped at 1 (exact rational arithmetic)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1))
    p = Fraction(2 * tail, 2 ** n)
    return float(min(p, Fraction(1)))


SEED_COLS = ("thrust_scale", "isp_scale", "wind", "T0", "rho0", "gust_scale", "m_est_err", "drogue_f")


def pair(a, b):
    ia = [int(r["run"]) for r in a]
    ib = [int(r["run"]) for r in b]
    same_runs = ia == ib
    same_draws = all(all(abs(float(x[c]) - float(y[c])) < 1e-12 for c in SEED_COLS if c in x and c in y) for x, y in zip(a, b))
    oa = np.array([float(r["ok"]) > 0.5 for r in a])
    ob = np.array([float(r["ok"]) > 0.5 for r in b])
    lost = int(np.sum(oa & ~ob))
    gained = int(np.sum(~oa & ob))
    return dict(n=len(a), P_base=float(oa.mean()), P_case=float(ob.mean()), lost=lost, gained=gained,
                p_exact=mcnemar_exact(lost, gained), runs_aligned=same_runs, seed101_draws_identical=same_draws)


def stat(r):
    ok = np.array([float(x["ok"]) > 0.5 for x in r])
    k, n = int(ok.sum()), len(ok)
    lo, hi = wilson(k, n)
    return dict(n=n, k=k, P=k / n, wilson95=[lo, hi])


def main():
    out = dict(script="rg01_stats v1", inputs={})
    rv = f"{RES}/relight_v28"
    pub = json.load(open(f"{rv}/relight_v28.json"))
    out["inputs"]["relight_v28.json"] = sha16(f"{rv}/relight_v28.json")
    out["inputs"]["rc03"] = sha16(RC03)

    def R(name):
        return rows(f"{rv}/mc6_runs_{name}_v28.csv.gz")

    bases = ("A1_none", "A1_pc", "A1J_none", "A1J_pc")
    states = ("liq", "vapU", "vapF")
    # ---- C1: P per base and line state at 0.81 s; and the withdrawn 1.41 s on primed lines
    c1 = {}
    for b in bases:
        for st in states:
            for plan in ("0.81", "1.41"):
                s = stat(R(f"v28_{st}_p{plan}_{b}_k2"))
                c1[f"{b}|{st}|plan{plan}"] = s
    out["C1_P_by_state"] = c1
    # ---- C2: option (c) fault path paired 0.81 -> 1.41
    c2 = {}
    for b in bases:
        c2[b] = pair(R(f"v28_fault_p0.81_{b}_k2"), R(f"v28_fault_p1.41_{b}_k2"))
    out["C2_fault_paired"] = c2
    # fault spread (none bases)
    fs = {}
    for b in ("A1_none", "A1J_none"):
        for st in states:
            fs[f"{b}|{st}"] = pair(R(f"v28_fs{st}_p0.81_{b}_k2"), R(f"v28_fs{st}_p1.41_{b}_k2"))
    out["C2_fault_spread_paired"] = fs
    # ---- C3: false-UNPRIMED cost (primed line planned 1.41 vs 0.81)
    c3 = {}
    for b in bases:
        for st in states:
            c3[f"{b}|{st}"] = pair(R(f"v28_{st}_p0.81_{b}_k2"), R(f"v28_{st}_p1.41_{b}_k2"))
    out["C3_false_unprimed_paired"] = c3

    # ---- q*: reproduce the author's construction exactly (fixed 1.37 s fault point, seed 20261019, author's loop order)
    rng = np.random.default_rng(20261019)
    qs = {}
    for b in bases:
        f0 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_fault_p0.81_{b}_k2")])
        f1 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_fault_p1.41_{b}_k2")])
        for st in states:
            n0 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_{st}_p0.81_{b}_k2")])
            n1 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_{st}_p1.41_{b}_k2")])
            dN, dF = n0.mean() - n1.mean(), f1.mean() - f0.mean()
            q = max(dN, 0.0) / (max(dN, 0.0) + dF)
            N = len(n0)
            bq = []
            for _ in range(2000):
                i = rng.integers(0, N, N)
                dn, df = n0[i].mean() - n1[i].mean(), f1[i].mean() - f0[i].mean()
                if dn + df > 0:
                    bq.append(max(dn, 0.0) / (max(dn, 0.0) + df))
            qs[f"{b}|{st}"] = dict(dN=float(dN), dF=float(dF), q_star=float(q),
                                   ci95_author_seed=[float(np.percentile(bq, 2.5)), float(np.percentile(bq, 97.5))])
    # independent seed for the same bootstrap (interval stability)
    rng2 = np.random.default_rng(777)
    for b in bases:
        f0 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_fault_p0.81_{b}_k2")])
        f1 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_fault_p1.41_{b}_k2")])
        for st in states:
            n0 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_{st}_p0.81_{b}_k2")])
            n1 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_{st}_p1.41_{b}_k2")])
            bq = []
            for _ in range(4000):
                i = rng2.integers(0, len(n0), len(n0))
                dn, df = n0[i].mean() - n1[i].mean(), f1[i].mean() - f0[i].mean()
                bq.append(max(dn, 0.0) / (max(dn, 0.0) + df))
            qs[f"{b}|{st}"]["ci95_reviewer_seed777_n4000"] = [float(np.percentile(bq, 2.5)), float(np.percentile(bq, 97.5))]
    out["q_star_fixed_fault_point"] = qs
    allq = [v["q_star"] for v in qs.values()]
    out["q_star_range"] = [min(allq), max(allq)]
    out["q_star_ci_span_author_seed"] = [min(v["ci95_author_seed"][0] for v in qs.values()),
                                         max(v["ci95_author_seed"][1] for v in qs.values())]
    # author's published values for comparison
    pq = []
    for b, v in pub["option_c"]["by_base"].items():
        for st, x in v.get("break_even_prior", {}).items():
            pq.append(dict(case=f"{b}|{st}", q_star_pub=x["q_star"], ci_pub=x["q_star_ci95_bootstrap"]))
    out["q_star_published"] = pq

    # ---- review addition 1: q* on the fault-path SPREAD (prep re-run 0.56 s + line-state table), none bases only
    qsp = {}
    for b in ("A1_none", "A1J_none"):
        for st in states:
            n0 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_{st}_p0.81_{b}_k2")])
            n1 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_{st}_p1.41_{b}_k2")])
            g0 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_fs{st}_p0.81_{b}_k2")])
            g1 = np.array([float(r["ok"]) > 0.5 for r in R(f"v28_fs{st}_p1.41_{b}_k2")])
            dN, dF = n0.mean() - n1.mean(), g1.mean() - g0.mean()
            qsp[f"{b}|{st}"] = dict(dN=float(dN), dF_spread=float(dF),
                                    q_star_spread=float(max(dN, 0) / (max(dN, 0) + dF)) if (max(dN, 0) + dF) > 0 else None)
    out["review_q_star_on_fault_spread"] = qsp

    # ---- review addition 2: RC-03 abort fraction at the adopted W (no retry: a loss) folded into the per-state P
    rc = json.load(open(RC03))
    key = {"liq": "relight_valve_preopened_liquid|0.125|loopK15", "vapU": "relight_valve_preopened_vapour_U01|0.125|loopK15",
           "vapF": "relight_valve_preopened_full_vapour|0.125|loopK15"}
    fold = {}
    for st in states:
        c = rc["cases"][key[st]]
        p_ab = float(c["false_abort_vs_W_from_E1"]["0.65"])
        e1e2max = float(c["E1_E2_s"]["max"])
        for b in bases:
            P = stat(R(f"v28_{st}_p0.81_{b}_k2"))["P"]
            fold[f"{b}|{st}"] = dict(P_6DOF_conditional_on_light=P, p_abort_W065_RC03=p_ab, E1_E2_max_s=e1e2max,
                                     P_with_abort_folded=P * (1.0 - p_ab))
    out["review_P_with_rc03_abort_W065"] = fold
    # fraction of the GNC-constructed E0->E2 table above the earliest possible abort point E0E1_min + 0.65 (illustration)
    tabs = pub["rc03"]["tables"]
    out["gnc_tables_upper_tail"] = {st: dict(max_s=tabs[st]["quantiles_5pct_s"][-1], p95_s=tabs[st]["quantiles_5pct_s"][19])
                                    for st in states}

    # ---- C5: regband 62 m and 85 m (paired against growth-only)
    rb = f"{RES}/regband"
    c5 = {}
    for case, comp in (("rbl_B1_lead62_pc_k2", "tgl_B1_lead62_pc_k2"), ("rbc_B1_cap_pc_k2", "tgc_B1_cap_pc_k2")):
        a = rows(f"{rb}/mc6_runs_{comp}_rb.csv.gz")
        b = rows(f"{rb}/mc6_runs_{case}_rb.csv.gz")
        c5[case] = dict(stat=stat(b), comparator=stat(a), paired=pair(a, b))
    tg = f"{RES}/throat_growth"
    for case, comp in (("rb_B1_pc_k2", f"{tg}/mc6_runs_tg_B1_pc_k2_tg.csv.gz"), ("rb_B1_none_k2", f"{tg}/mc6_runs_tg_B1_none_k2_tg.csv.gz")):
        a = rows(comp)
        b = rows(f"{rb}/mc6_runs_{case}_rb.csv.gz")
        c5[case] = dict(stat=stat(b), comparator=stat(a), paired=pair(a, b))
    out["C5_regband"] = c5
    with open(os.path.join(HERE, "rg01_stats.json"), "w") as f:
        json.dump(out, f, indent=1)
    # console summary
    for k, v in c2.items():
        print(f"C2 fault {k:9s} {v['P_base']:.3f} -> {v['P_case']:.3f} -{v['lost']}/+{v['gained']} p {v['p_exact']:.3g} "
              f"aligned {v['runs_aligned']} draws {v['seed101_draws_identical']}")
    for k, v in c3.items():
        print(f"C3 FU {k:14s} {v['P_base']:.3f} -> {v['P_case']:.3f} -{v['lost']}/+{v['gained']} p {v['p_exact']:.3g} "
              f"aligned {v['runs_aligned']} draws {v['seed101_draws_identical']}")
    for k, v in fs.items():
        print(f"C2 FS {k:14s} {v['P_base']:.3f} -> {v['P_case']:.3f} -{v['lost']}/+{v['gained']} p {v['p_exact']:.3g}")
    for k, v in qs.items():
        print(f"q* {k:14s} {v['q_star']:.4f} CI(author seed) {v['ci95_author_seed'][0]:.4f}-{v['ci95_author_seed'][1]:.4f} "
              f"CI(seed777) {v['ci95_reviewer_seed777_n4000'][0]:.4f}-{v['ci95_reviewer_seed777_n4000'][1]:.4f}")
    print("q* range", out["q_star_range"], "CI span", out["q_star_ci_span_author_seed"])
    for k, v in qsp.items():
        print(f"q* on SPREAD {k:14s} dN {v['dN']:.3f} dF {v['dF_spread']:.3f} q* {v['q_star_spread']}")
    for k, v in fold.items():
        print(f"fold {k:14s} P|light {v['P_6DOF_conditional_on_light']:.3f} p_abort {v['p_abort_W065_RC03']:.4f} "
              f"-> {v['P_with_abort_folded']:.3f}")
    for k, v in c5.items():
        s, p = v["stat"], v["paired"]
        print(f"C5 {k:22s} P {s['P']:.3f} [{s['wilson95'][0]:.3f}, {s['wilson95'][1]:.3f}] vs {v['comparator']['P']:.3f} "
              f"-{p['lost']}/+{p['gained']} p {p['p_exact']:.3g} aligned {p['runs_aligned']} draws {p['seed101_draws_identical']}")
    for k, v in c1.items():
        if "plan0.81" in k:
            print(f"C1 {k:24s} P {v['P']:.3f} [{v['wilson95'][0]:.3f}, {v['wilson95'][1]:.3f}]")


if __name__ == "__main__":
    main()
