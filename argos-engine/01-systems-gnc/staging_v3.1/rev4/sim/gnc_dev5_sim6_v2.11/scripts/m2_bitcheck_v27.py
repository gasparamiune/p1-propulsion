"""m2_bitcheck_v27 v1 (2026-10-13). Bit-identity check of sim6/run6 v2.7-dev with every v2.7 option at its default
(throat_g 0 = no throat growth, throat_loop unused, k_est_asc 0, floor_comp_min unused) against stored sim6 v2.6 Monte Carlo
runs on the current interface set (iface_v3c: combustion.json v2.3, mechanical.json v2, electronics.json v1). These v2.6 runs
already fly the v2.6 options that are ON in the baselines (tracker, governor + ratchet, lift-ramp shutdown, 72 % throttle-
down, relight start rule, NC-closed relight timeline, notch with mistune), which the v2.5 comparison (m2_bitcheck_v26 on
iface_v3a) cannot cover.
For each case: rebuild the configuration from the v2.6 summary (same N2O load, same draws, seed 101), re-fly the first K runs
and every failed run, compare every result field stored in the v2.6 run CSV for exact equality.
Env: GNC_IFACE must be the v3c set; GNC_RES (default out/v27_checks); GNC_BIT_K (8).
Output: GNC_RES/bitcheck_v27_vs_v26.json"""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

S = "/home/claude/work/space/out"
RES = os.environ.get("GNC_RES", f"{S}/v27_checks")
K = int(os.environ.get("GNC_BIT_K", "8"))
N = 500
REFS = [(f"{S}/prop_closure_m2/mc6_summary_pc2.json", f"{S}/prop_closure_m2/mc6_runs_%s_pc2.csv", "pc_A1_2kg"),
        (f"{S}/prop_closure_m2/mc6_summary_pc2.json", f"{S}/prop_closure_m2/mc6_runs_%s_pc2.csv", "pc_B1_h85_2kg"),
        (f"{S}/mechv2_mc/mc6_summary_m2.json", f"{S}/mechv2_mc/mc6_runs_%s_m2.csv", "m2_J1.6_n15")]
V27_KEYS = ("throat_g", "throat_jref", "throat_g_band", "throat_loop", "k_est_asc", "floor_comp_min")


def main():
    os.makedirs(RES, exist_ok=True)
    out = dict(tool="m2_bitcheck_v27 v1", sim=s6.SIM6_VERSION, iface=os.environ.get("GNC_IFACE"), cases={})
    allok = True
    for summ, pat, c in REFS:
        cs = json.load(open(summ))["cases"][c]
        assert "v2.6" in cs["sim"], cs["sim"]
        cfg = {k: v for k, v in cs["config"].items()}
        cfg["m_n2o"] = cs["m_n2o_mc_kg"]
        for k in list(cfg):
            if isinstance(cfg[k], list):
                cfg[k] = tuple(cfg[k])
        for k in V27_KEYS:
            assert k not in cfg, k
        cfg = R.cfg_of(**cfg)
        rows = list(csv.DictReader(open(pat % c)))
        D = R.draw(np.random.default_rng(101), N, cfg)
        idx = list(range(K)) + [i for i, r in enumerate(rows) if int(r["ok"]) == 0 and i >= K]
        mism = []
        nf = 0
        for i in idx:
            res = R.run_one(cfg, D[i])
            for k in rows[i]:
                if k in s6.RES_NAMES:
                    nf += 1
                    a = float(rows[i][k]); b = float(res[k])
                    if not (a == b or (np.isnan(a) and np.isnan(b))):
                        mism.append(dict(run=i, field=k, v26=a, v27=b))
        out["cases"][c] = dict(reference=pat % c, runs_checked=len(idx), failed_runs_included=len(idx) - K, values_compared=nf,
                               mismatches=len(mism), first=mism[:10])
        allok &= not mism
        print(c, "runs", len(idx), "values", nf, "mismatches", len(mism), mism[:3], flush=True)
    out["bit_identical"] = bool(allok)
    with open(os.path.join(RES, "bitcheck_v27_vs_v26.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("bit_identical", allok)


if __name__ == "__main__":
    main()
