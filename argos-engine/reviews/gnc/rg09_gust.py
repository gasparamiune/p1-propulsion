"""rg09_gust v1 (independent GNC review, 2026-10-13): where the turbulence sensitivity of rg05 sits relative to the GNC
launch-commit proposal (gnc.json v3 launch_commit_wind_evidence: <= 6 m/s mean wind at 10 m, a proposal, not a decision).

The Monte Carlo draws the mean wind U(0, 8) m/s and the Dryden (MIL-F-8785C low altitude) intensity sigma_w = 0.1 W20 x
gust_scale, gust_scale U(0.5, 1.5) (run6.py l.602, l.846; ASSUMED, no site data). The turbulence intensity is therefore tied
to the mean wind. rg05 scaled gust_scale x2 on every run (B1 62 m: P 0.996 -> 0.962; A1 v2.8 liquid: 0.992 -> 0.952).
This script re-flies, on the same draws (seed 101, author's code unchanged, rg05 harness):
  base, gust_scale x2, and gust_scale fixed at 1.5 (top of the MC band)
for B1 62 m (rbl_B1_lead62_pc_k2) and A1 v2.8 liquid line at 0.81 s (v28_liq_p0.81_A1_none_k2), and splits the result at
the 6 m/s proposal (drawn mean wind below / at or above), paired, exact McNemar within each subset.
Output: rg09_gust.json. One process: NUMBA_NUM_THREADS=1 nice -n 10 /opt/engine-venv/bin/python -I rg09_gust.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import rg05_sens as S  # noqa: E402  (sets the author's environment, imports the unchanged simulator copy)
import numpy as np  # noqa: E402

SPLIT = 6.0


def fly_rows(over, gust_mode, n=500):
    over = dict(over)
    m = float(over.pop("m_fixed"))
    cfg = S.R.cfg_of(**dict(over, m_n2o=m))
    D = S.R.draw(np.random.default_rng(101), n, cfg)
    S.AERO_EXTRA.clear()
    rows = []
    for i in range(n):
        d = dict(D[i])
        if gust_mode == "x2":
            d["_gust_scale"] = D[i]["_gust_scale"] * 2.0
        elif gust_mode == "at1.5":
            d["_gust_scale"] = 1.5
        res = S.R.run_one(cfg, d)
        rows.append(dict(ok=bool(S.R.success(res)), wind=float(D[i]["_wind"]), gust_scale=float(d["_gust_scale"]),
                         exhausted=bool(res["exhausted"] > 0.5), crash=bool(res["crash"] > 0.5), landed=bool(res["landed"] > 0.5)))
    return rows


def split_stats(base, case):
    out = {}
    for lab, sel in (("wind_lt_6", lambda r: r["wind"] < SPLIT), ("wind_ge_6", lambda r: r["wind"] >= SPLIT), ("all", lambda r: True)):
        idx = [i for i, r in enumerate(base) if sel(r)]
        kb = sum(base[i]["ok"] for i in idx)
        kc = sum(case[i]["ok"] for i in idx)
        lost = sum(1 for i in idx if base[i]["ok"] and not case[i]["ok"])
        gained = sum(1 for i in idx if (not base[i]["ok"]) and case[i]["ok"])
        n = len(idx)
        out[lab] = dict(n=n, P_base=kb / n, P_case=kc / n, ci95_case=S.wilson(kc, n), lost=lost, gained=gained,
                        p_exact=S.mcnemar(lost, gained))
    return out


def main():
    tabs = S.RV.e0e2_tables()
    bases = {"B1_62m (rbl_B1_lead62_pc_k2)": S.RBM.cases(None)["rbl_B1_lead62_pc_k2"][0],
             "A1_liq_plan0.81 (v28_liq_p0.81_A1_none_k2)": S.RV.case_over("A1_none", "liq", 0.81, tabs)}
    out = dict(script="rg09_gust v1", split_mps=SPLIT, cases={})
    for bname, over in bases.items():
        t0 = time.time()
        base = fly_rows(over, "base")
        out["cases"][bname] = {}
        for mode in ("x2", "at1.5"):
            rows = fly_rows(over, mode)
            st = split_stats(base, rows)
            out["cases"][bname][mode] = st
            print(bname, mode, json.dumps(st), f"{time.time() - t0:.0f}s", flush=True)
            json.dump(out, open(os.path.join(HERE, "rg09_gust.json"), "w"), indent=1)
    json.dump(out, open(os.path.join(HERE, "rg09_gust.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
