"""REV-GNC-7 (h)(ii): A1 210 m usable N2O reserve with the line-208 dip onset (80 g): success = ok and liq_left >= onset
(m2_rev3_reserve_dip v1.1 definition).  76 g and 80.5 g are DERIVED by shifting the flown G73 / G80 per-run liquid by
-(76 - 73) g and -(80.5 - 80) g (paired shift G80 - G73 is 7.07 g median for 7 g booked)."""
import csv, gzip, json, sys
import numpy as np
D = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev4/out_rev4/p2"
ON = 80.0
def load(fn):
    rows = list(csv.DictReader(gzip.open(f"{D}/{fn}", "rt")))
    return (np.array([int(r["run"]) for r in rows]), np.array([float(r["ok"]) for r in rows]) > 0.5,
            1e3 * np.array([float(r["liq_left"]) for r in rows]))
out = {}
tot = {}
for st in ("liq", "pw"):
    for base in ("A1_none", "A1J_pc"):
        r73, ok73, l73 = load(f"rf_{base}_{st}_G73_v351_h210.csv.gz")
        r80, ok80, l80 = load(f"rf_{base}_{st}_G80_v351_h210.csv.gz")
        assert (r73 == r80).all()
        cases = {"G73 flown": (ok73, l73), "76 g (G73 - 3 g)": (ok73, l73 - 3.0), "G80 flown": (ok80, l80), "80.5 g (G80 - 0.5 g)": (ok80, l80 - 0.5)}
        res = {}
        ref = ok73 & (l73 >= ON)
        for k, (ok, l) in cases.items():
            s = ok & (l >= ON)
            u = l[s] - ON
            res[k] = dict(N=int(len(s)), P_adj=round(float(s.mean()), 4), n_ok_raw=int(ok.sum()), n_ok_below_onset=int((ok & (l < ON)).sum()),
                          usable_min_g=round(float(u.min()), 1), usable_p01_g=round(float(np.percentile(u, 1)), 1),
                          n_usable_lt_5g=int((u < 5).sum()), lost_vs_G73=int((ref & ~s).sum()), gained_vs_G73=int((~ref & s).sum()))
            t = tot.setdefault((st, k), [0, 0, 0, 0])
            t[0] += int(s.sum()); t[1] += len(s); t[2] += res[k]["lost_vs_G73"]; t[3] += res[k]["gained_vs_G73"]
        out[f"{base}|{st}"] = res
pooled = {f"{st}|{k}": dict(P_adj=round(v[0] / v[1], 4), N=v[1], lost_vs_G73=v[2], gained_vs_G73=v[3]) for (st, k), v in tot.items()}
json.dump(dict(onset_g=ON, per_base=out, pooled=pooled), open(sys.argv[1], "w"), indent=1)
for k, v in out.items():
    print(k)
    for c, x in v.items():
        print(f"   {c:22s} P {x['P_adj']:.4f} ok_raw {x['n_ok_raw']} ok<onset {x['n_ok_below_onset']} usable min {x['usable_min_g']} p01 {x['usable_p01_g']} n<5g {x['n_usable_lt_5g']} vsG73 -{x['lost_vs_G73']}/+{x['gained_vs_G73']}")
print("pooled", json.dumps(pooled, indent=0))
