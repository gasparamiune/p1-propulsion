"""REV-GNC-7 (f) row 10: paired line-208 comparison of the +1 kg / 2.20 kg arm against the 0 kg payload-study vehicle
(pl0, tank at 0.58 m, h210), dip onset 80 g, paired by run index, p2_rev4 'ub95_pp' form."""
import csv, gzip, json, math, sys
import numpy as np
P = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev4/out_rev4/payload_n500/tables"
def load(fn):
    rows = list(csv.DictReader(gzip.open(f"{P}/{fn}", "rt")))
    return np.array([int(r["run"]) for r in rows]), (np.array([float(r["ok"]) for r in rows]) > 0.5) & (1e3 * np.array([float(r["liq_left"]) for r in rows]) >= 80.0)
lost = gained = n = 0; per = {}
for b in ("A1_none", "A1J_pc"):
    r0, s0 = load(f"rf_{b}_liq_G73_v351_pl0_tz58_h210_n500.csv.gz"); r1, s1 = load(f"rf_{b}_liq_G73_v351_pl1_tz58_h210_m2.20_n500.csv.gz")
    assert (r0 == r1).all()
    l, g = int((s0 & ~s1).sum()), int((~s0 & s1).sum()); per[b] = dict(P0=float(s0.mean()), P1=float(s1.mean()), lost=l, gained=g)
    lost += l; gained += g; n += len(r0)
d = (lost - gained) / n; ub = 100 * (d + 1.645 * math.sqrt(max(((lost + gained) - (lost - gained) ** 2 / n) / n ** 2, 0)))
out = dict(method=__doc__, per_base=per, lost=lost, gained=gained, n=n, ub95_pp=round(ub, 3))
json.dump(out, open(sys.argv[1], "w"), indent=1); print(json.dumps(out))
