"""Bit-identity check: sim6 v2.5 / run6 v2.5 with act_model 0 (default) against the stored sim6 v2.4 Monte Carlo runs.

For each case: rebuild the configuration from mc6_summary_v2.json (same N2O load, same draws, seed 101), re-fly the first
K runs and every failed run, and compare every result field stored in the v2.4 run CSV for exact equality.
Output: GNC_RES/bitcheck_v25_vs_v24.json. Run: python scripts/m2_bitcheck_v25.py
"""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
CASES = os.environ.get("GNC_BIT_CASES", "AD_fins_f20,AD_prov_2kg").split(",")
K = int(os.environ.get("GNC_BIT_K", "8"))
N = 500


def main():
    S = json.load(open(os.path.join(OUT, "mc6_summary_v2.json")))["cases"]
    out = dict(tool="m2_bitcheck_v25", sim=s6.SIM6_VERSION, cases={})
    allok = True
    for c in CASES:
        cs = S[c]
        assert "v2.4" in cs["sim"], cs["sim"]
        cfg = {k: v for k, v in cs["config"].items()}
        cfg["m_n2o"] = cs["m_n2o_mc_kg"]
        if isinstance(cfg.get("ascent_bias"), list):
            cfg["ascent_bias"] = tuple(cfg["ascent_bias"])
        if isinstance(cfg.get("w0"), list):
            cfg["w0"] = tuple(cfg["w0"])
        for k in ("act_model", "servo_V", "act_n", "act_Jint", "supply_chain", "supply_Vrest"):
            assert k not in cfg, k
        cfg = R.cfg_of(**cfg)
        rows = list(csv.DictReader(open(os.path.join(OUT, f"mc6_runs_{c}_v2.csv"))))
        D = R.draw(np.random.default_rng(101), N, cfg)
        idx = list(range(K)) + [i for i, r in enumerate(rows) if int(r["ok"]) == 0]
        mism = []
        for i in idx:
            res = R.run_one(cfg, D[i])
            for k in rows[i]:
                if k in s6.RES_NAMES:
                    a = float(rows[i][k])
                    b = float(res[k])
                    if not (a == b or (np.isnan(a) and np.isnan(b))):
                        mism.append(dict(run=i, field=k, v24=a, v25=b))
        out["cases"][c] = dict(runs_checked=len(idx), failed_runs_included=len(idx) - K, fields=len([k for k in rows[0] if k in s6.RES_NAMES]),
                               mismatches=len(mism), first=mism[:10])
        allok &= not mism
        print(c, "runs", len(idx), "mismatches", len(mism), mism[:3], flush=True)
    out["bit_identical"] = bool(allok)
    with open(os.path.join(RES, "bitcheck_v25_vs_v24.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("bit_identical", allok)


if __name__ == "__main__":
    main()
