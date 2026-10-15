"""m2_bitcheck_v26 v1.2 (v1.2: att_ref_mode key). Bit-identity check: sim6/run6 v2.6 with every v2.6 option at its default (off) against the stored sim6 v2.5 Monte Carlo
runs of the v3a attribution step (out/m3a, iface_v3a: mechanical.json v1, combustion.json v2.1, electronics.json v1).
For each case: rebuild the configuration from mc6_summary_v3a.json (same N2O load, same draws, seed 101), re-fly the
first K runs and every failed run, compare every result field stored in the v2.5 run CSV for exact equality.
Env: GNC_IFACE must be the v3a set. Output: GNC_RES/bitcheck_v26_vs_v25.json. Run: python scripts/m2_bitcheck_v26.py"""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

OUT = os.environ.get("GNC_BIT_REF", "/home/claude/work/space/out/m3a")
SUF = os.environ.get("GNC_BIT_SUF", "v3a")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/v26_checks")
CASES = os.environ.get("GNC_BIT_CASES", "AD_prov_2kg,AD_prov_act_n48_6V6_J1_sagD").split(",")
K = int(os.environ.get("GNC_BIT_K", "8"))
N = 500
V26_KEYS = ("gim_cmd_acc", "gim_aw_thr", "att_ref_rate", "toff_model", "meco_td", "relight_start", "t_ign_add", "gim_notch_f",
            "gim_notch_track", "gim_notch_mis_w", "rock_K_eng", "eng_I_pivot_wet",   # v1.1: run6 v2.6 MC options added
            "att_ref_mode")   # v1.2: reference-governor ratchet


def main():
    os.makedirs(RES, exist_ok=True)
    S = json.load(open(os.path.join(OUT, f"mc6_summary_{SUF}.json")))["cases"]
    out = dict(tool="m2_bitcheck_v26", sim=s6.SIM6_VERSION, reference=f"{OUT} ({SUF})", iface=os.environ.get("GNC_IFACE"), cases={})
    allok = True
    for c in CASES:
        cs = S[c]
        assert "v2.5" in cs["sim"], cs["sim"]
        cfg = {k: v for k, v in cs["config"].items()}
        cfg["m_n2o"] = cs["m_n2o_mc_kg"]
        for k in ("ascent_bias", "w0"):
            if isinstance(cfg.get(k), list):
                cfg[k] = tuple(cfg[k])
        for k in V26_KEYS:
            assert k not in cfg, k
        cfg = R.cfg_of(**cfg)
        rows = list(csv.DictReader(open(os.path.join(OUT, f"mc6_runs_{c}_{SUF}.csv"))))
        D = R.draw(np.random.default_rng(101), N, cfg)
        idx = list(range(K)) + [i for i, r in enumerate(rows) if int(r["ok"]) == 0]
        mism = []
        nf = 0
        for i in idx:
            res = R.run_one(cfg, D[i])
            for k in rows[i]:
                if k in s6.RES_NAMES:
                    nf += 1
                    a = float(rows[i][k]); b = float(res[k])
                    if not (a == b or (np.isnan(a) and np.isnan(b))):
                        mism.append(dict(run=i, field=k, v25=a, v26=b))
        out["cases"][c] = dict(runs_checked=len(idx), failed_runs_included=len(idx) - K, values_compared=nf,
                               mismatches=len(mism), first=mism[:10])
        allok &= not mism
        print(c, "runs", len(idx), "values", nf, "mismatches", len(mism), mism[:3], flush=True)
    out["bit_identical"] = bool(allok)
    with open(os.path.join(RES, "bitcheck_v26_vs_v25.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("bit_identical", allok)


if __name__ == "__main__":
    main()
