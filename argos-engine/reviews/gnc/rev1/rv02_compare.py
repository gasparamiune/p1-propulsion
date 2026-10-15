"""rv02_compare v1.0 (REV-GNC-R1, independent reviewer, 2026-10-13).

Compares the reviewer's re-flown Monte Carlo tables (rv01_rerun.sh, scratch copy of the rev1 staging) with the tables GNC
published in the hub, field by field, and recomputes the paired statistics from the PUBLISHED tables with the reviewer's own
exact McNemar code (no scipy): two-sided p = min(1, 2 P[X <= min(lost, gained)]), X ~ Bin(lost + gained, 1/2).

Arms re-flown (seed 101, 500 runs per base):
  st_<base>_L400_te   start plateau 2.4 bar abs x 0.4 s, persistence branch on, relight planner t_ign_est + 0.3 s
                      (m2_start_transient; bases A1_none, A1J_pc)
  mc6_runs_<base>_RR66_EI05   ENG-07 re-routed coil, 6.6 V, EI 0.5 (hose_K 46.74 N m/rad, command limit 44.60 deg/s)
                      (m2_eng07_6v6; bases A1_none, rbl_B1_lead62_pc_k2)
Comparators (hub-published, gz): the decided release rule without plateau (rev1 results/release_rule/rel_<base>_rel1),
the stored v2.8 / regband base tables (01-systems-gnc/results/relight_v28, regband), and the L400 arm (same plateau, planner
unchanged) for the planner question.
Output: rv02_compare.json (this folder). Reads only; writes only rv02_compare.json.
"""
import csv
import gzip
import hashlib
import io
import json
import math
import os

HUB = "/home/claude/work/shared-fallback/engine"
REV1 = f"{HUB}/01-systems-gnc/staging_v3.1/rev1"
SCR = "/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv_out"
HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "rv02_compare v1.0"


def sha16_bytes(b):
    return hashlib.sha256(b).hexdigest()[:16]


def read(p):
    b = gzip.open(p).read() if p.endswith(".gz") else open(p, "rb").read()
    return list(csv.DictReader(io.StringIO(b.decode()))), sha16_bytes(b), b


def ok_of(rows):
    return [float(r["ok"]) > 0.5 for r in rows]


def exact_mcnemar(a, b):
    lost = sum(1 for x, y in zip(a, b) if x and not y)
    gained = sum(1 for x, y in zip(a, b) if (not x) and y)
    n = lost + gained
    if n == 0:
        p = 1.0
    else:
        k = min(lost, gained)
        tail = sum(math.comb(n, i) for i in range(k + 1)) / 2.0 ** n
        p = min(1.0, 2.0 * tail)
    return dict(P_ref=sum(a) / len(a), P_case=sum(b) / len(b), lost=lost, gained=gained, p_exact=p, n=len(a))


def compare_rows(mine, pub):
    """Every column of every row; numeric fields equal to 1e-12 relative or both NaN; text fields exactly."""
    cols = list(pub[0].keys())
    mism, nvals = [], 0
    if list(mine[0].keys()) != cols:
        mism.append(("header", list(mine[0].keys())[:5], cols[:5]))
    for i, (r, s) in enumerate(zip(mine, pub)):
        for k in cols:
            nvals += 1
            x, y = r.get(k), s.get(k)
            if x == y:
                continue
            try:
                fx, fy = float(x), float(y)
                if (math.isnan(fx) and math.isnan(fy)) or abs(fx - fy) <= 1e-12 * max(1.0, abs(fy)):
                    continue
            except (TypeError, ValueError):
                pass
            mism.append((i, k, x, y))
    return dict(rows_mine=len(mine), rows_pub=len(pub), values_compared=nvals, mismatches=len(mism), first=mism[:5])


def main():
    out = dict(version=VERSION, date="2026-10-13", st={}, e7={})
    # ---- start transient L400_te ----
    st_pub = json.load(open(f"{REV1}/results/start_transient/start_transient.json"))
    a_ref, b_case, a_v28, b_l400 = [], [], [], []
    for base in ("A1_none", "A1J_pc"):
        mine, h_m, bm = read(f"{SCR}/start_transient/st_{base}_L400_te.csv")
        pub, h_p, bp = read(f"{REV1}/results/start_transient/st_{base}_L400_te.csv.gz")
        rel, h_r, _ = read(f"{REV1}/results/release_rule/rel_{base}_rel1.csv.gz")
        v28, h_v, _ = read(f"{HUB}/01-systems-gnc/results/relight_v28/mc6_runs_v28_liq_p0.81_{base}_k2_v28.csv.gz")
        l400, h_l, _ = read(f"{REV1}/results/start_transient/st_{base}_L400.csv.gz")
        cmp_ = compare_rows(mine, pub)
        okm, okp, okr, okv, okl = ok_of(mine), ok_of(pub), ok_of(rel), ok_of(v28), ok_of(l400)
        te = sorted({round(float(r.get("t_ign_est", "nan")), 6) for r in pub}) if "t_ign_est" in pub[0] else "column absent"
        e = dict(bytes_identical=(bm == bp), sha16_mine=h_m, sha16_published_decompressed=h_p, field_compare=cmp_,
                 P_mine=sum(okm) / len(okm), P_published=sum(okp) / len(okp),
                 vs_decided_rule_no_plateau=exact_mcnemar(okr, okp), vs_stored_v28=exact_mcnemar(okv, okp),
                 vs_L400_same_plateau_planner_unchanged=exact_mcnemar(okl, okp),
                 published_json=dict((k, st_pub["cases"][f"{base}|L400_te"][k]) for k in
                                     ("vs_decided_rule_no_plateau", "vs_stored_v28", "t_ign_est_s")),
                 t_ign_est_in_rows=te, sources=dict(rel1=h_r, v28=h_v, L400=h_l))
        out["st"][base] = e
        a_ref += okr
        b_case += okp
        a_v28 += okv
        b_l400 += okl
    out["st"]["pooled_vs_decided_rule"] = exact_mcnemar(a_ref, b_case)
    out["st"]["pooled_vs_decided_rule_published"] = st_pub["pooled_vs_decided_rule"]["L400_te"]
    out["st"]["pooled_vs_L400"] = exact_mcnemar(b_l400, b_case)
    # ---- ENG-07 RR66 EI 0.5 ----
    e7_pub = json.load(open(f"{REV1}/results/eng07_6v6/eng07_6v6.json"))
    refs = {"A1_none": f"{HUB}/01-systems-gnc/results/relight_v28/mc6_runs_v28_liq_p0.81_A1_none_k2_v28.csv.gz",
            "rbl_B1_lead62_pc_k2": f"{HUB}/01-systems-gnc/results/regband/mc6_runs_rbl_B1_lead62_pc_k2_rb.csv.gz"}
    A, B = [], []
    for base, refp in refs.items():
        p_m = f"{SCR}/eng07/mc6_runs_{base}_RR66_EI05.csv"
        if not os.path.exists(p_m):
            out["e7"][base] = "not re-flown"
            continue
        mine, h_m, bm = read(p_m)
        pub, h_p, bp = read(f"{REV1}/results/eng07_6v6/mc6_runs_{base}_RR66_EI05.csv.gz")
        ref, h_r, _ = read(refp)
        okm, okp, okr = ok_of(mine), ok_of(pub), ok_of(ref)
        hk = sorted({float(r["hose_K"]) for r in pub}) if "hose_K" in pub[0] else "column absent"
        out["e7"][base] = dict(bytes_identical=(bm == bp), sha16_mine=h_m, sha16_published_decompressed=h_p,
                               field_compare=compare_rows(mine, pub), P_mine=sum(okm) / len(okm),
                               P_published=sum(okp) / len(okp), vs_baseline=exact_mcnemar(okr, okp),
                               published_json=e7_pub["by_base"][base]["RR66_EI05"]["paired_vs_baseline"],
                               hose_K_in_rows=hk, baseline_sha16=h_r)
        A += okr
        B += okp
    if A:
        out["e7"]["pooled"] = exact_mcnemar(A, B)
        out["e7"]["pooled_published"] = e7_pub["pooled"]["RR66_EI05"]
    with open(os.path.join(HERE, "rv02_compare.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    for k, v in out["st"].items():
        if isinstance(v, dict) and "field_compare" in v:
            print("st", k, "bytes_identical", v["bytes_identical"], "mism", v["field_compare"]["mismatches"], "P", v["P_mine"],
                  v["P_published"], "vs rel1", v["vs_decided_rule_no_plateau"], "vs L400", v["vs_L400_same_plateau_planner_unchanged"],
                  "t_ign_est rows", v["t_ign_est_in_rows"])
    print("st pooled", out["st"]["pooled_vs_decided_rule"], "| published", out["st"]["pooled_vs_decided_rule_published"])
    print("st pooled vs L400", out["st"]["pooled_vs_L400"])
    for k, v in out["e7"].items():
        print("e7", k, json.dumps(v, default=str)[:600])


if __name__ == "__main__":
    main()
