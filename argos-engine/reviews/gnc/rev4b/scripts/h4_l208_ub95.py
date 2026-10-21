"""REV-GNC-7 (h)(ii): line-208 rule test of the vented-N2O cases against the v3d reference st|G73|h285 (rev3 fly files, hub copies
01-systems-gnc/staging_v3.1/rev3/tables/fly, sha16 as in p2_rev4.json references), dip onset 80 g on both arms, paired by run index
(first 500 runs per base), one-sided 95 % normal-approximation upper bound on the pooled deficit (the p2_rev4 'ub95_pp' form).
Check: G80 flown must reproduce p2_rev4 'G80_vs_v3d_ref' (liq: lost 12, gained 10, ub95 0.972 pp).
Cases above G80 are the flown G80 per-run liquid shifted by -(m - 80) g (ESTIMATE, linear)."""
import csv, gzip, json, sys, math
import numpy as np
H = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1"
REF = f"{H}/rev3/tables/fly"; CASE = f"{H}/rev4/out_rev4/p2"; ON = 80.0
def load(path):
    rows = list(csv.DictReader(gzip.open(path, "rt")))
    return (np.array([int(r["run"]) for r in rows]), np.array([float(r["ok"]) for r in rows]) > 0.5, 1e3 * np.array([float(r["liq_left"]) for r in rows]))
out = {}
for st in ("liq", "pw"):
    cases = {}
    for m in ("G73 flown", "76.0", "G80 flown", "80.5", "83.0", "85.5", "85.8"):
        lost = gained = n = 0; sr = sc = 0
        for base in ("A1_none", "A1J_pc"):
            rr, okr, lr = load(f"{REF}/rf_{base}_{st}_G73_h285.csv.gz")
            src = "G73" if m in ("G73 flown", "76.0") else "G80"
            rc, okc, lc = load(f"{CASE}/rf_{base}_{st}_{src}_v351_h210.csv.gz")
            k = min(len(rr), len(rc), 500); assert (rr[:k] == rc[:k]).all()
            shift = {"G73 flown": 0.0, "76.0": 3.0, "G80 flown": 0.0}.get(m, None)
            if shift is None: shift = float(m) - 80.0
            sref = okr[:k] & (lr[:k] >= ON); scase = okc[:k] & ((lc[:k] - shift) >= ON)
            lost += int((sref & ~scase).sum()); gained += int((~sref & scase).sum()); n += k; sr += int(sref.sum()); sc += int(scase.sum())
        d = (lost - gained) / n
        var = ((lost + gained) - (lost - gained) ** 2 / n) / n ** 2
        cases[m] = dict(n=n, P_ref=round(sr / n, 4), P_case=round(sc / n, 4), lost=lost, gained=gained, deficit_pp=round(100 * d, 2),
                        ub95_pp=round(100 * (d + 1.645 * math.sqrt(max(var, 0.0))), 3), rule_l208_ub_le_1pp=bool(100 * (d + 1.645 * math.sqrt(max(var, 0.0))) <= 1.0))
    out[st] = cases
json.dump(dict(method=__doc__, onset_g=ON, results=out), open(sys.argv[1], "w"), indent=1)
for st, c in out.items():
    for m, x in c.items(): print(st, f"{m:10s}", x)
