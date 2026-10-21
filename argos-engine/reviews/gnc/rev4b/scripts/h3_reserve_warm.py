"""REV-GNC-7 (h)(ii) extension: the 80.5 g of line 256 (2) is the 289.5 K average-rate estimate (2.43 s x 33.13 g/s, REV-COMB-4
section 3). At the 297.15 K warm end the same Cd 0.80 / Cd 0.70 flow ratio (33.13 / 29.25 = 1.1326 at 289.5 K, ASSUMED to hold
at 297.15 K) on 31.06 g/s gives 35.18 g/s: 85.5 g at 2.43 s of flow, 85.8 g at the 2.39 s cap (2.44 s of flow) [ESTIMATE].
Line-208 dip rule (success = ok and liq_left >= 80 g), per-run liquid of the flown G80 shifted by -(m - 80) g (ESTIMATE: a linear
extension 5.8 g beyond the flown G80; the paired G80 - G73 shift is 7.07 g median for 7 g booked)."""
import csv, gzip, json, sys
import numpy as np
D = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev4/out_rev4/p2"
ON = 80.0
def load(fn):
    rows = list(csv.DictReader(gzip.open(f"{D}/{fn}", "rt")))
    return (np.array([int(r["run"]) for r in rows]), np.array([float(r["ok"]) for r in rows]) > 0.5,
            1e3 * np.array([float(r["liq_left"]) for r in rows]))
r = 33.13 / 29.25
warm = dict(flow_ratio_cd080_cd070=round(r, 4), mdot_warm_cd080_g_s=round(31.06 * r, 2), m_243s_g=round(2.43 * 31.06 * r, 1),
            m_244s_g=round(2.44 * 31.06 * r, 1), m_cold_243s_g=round(2.43 * 27.58 * r, 1))
out = {}; tot = {}
for st in ("liq", "pw"):
    for base in ("A1_none", "A1J_pc"):
        r73, ok73, l73 = load(f"rf_{base}_{st}_G73_v351_h210.csv.gz")
        r80, ok80, l80 = load(f"rf_{base}_{st}_G80_v351_h210.csv.gz")
        assert (r73 == r80).all()
        ref = ok73 & (l73 >= ON)
        res = {}
        for m in (80.5, 83.0, 85.5, 85.8):
            l = l80 - (m - 80.0); s = ok80 & (l >= ON); u = l[s] - ON
            res[f"{m} g"] = dict(P_adj=round(float(s.mean()), 4), n_ok_below_onset=int((ok80 & (l < ON)).sum()), usable_min_g=round(float(u.min()), 1),
                                 usable_p01_g=round(float(np.percentile(u, 1)), 1), lost_vs_G73=int((ref & ~s).sum()), gained_vs_G73=int((~ref & s).sum()))
            t = tot.setdefault((st, m), [0, 0, 0]); t[0] += int(s.sum()); t[1] += len(s); t[2] += res[f"{m} g"]["lost_vs_G73"]
        out[f"{base}|{st}"] = res
pooled = {f"{st}|{m} g": dict(P_adj=round(v[0] / v[1], 4), N=v[1], lost_vs_G73=v[2]) for (st, m), v in tot.items()}
json.dump(dict(warm_end_estimate=warm, onset_g=ON, per_base=out, pooled=pooled), open(sys.argv[1], "w"), indent=1)
print(json.dumps(warm)); print(json.dumps(out, indent=0)); print(json.dumps(pooled, indent=0))
