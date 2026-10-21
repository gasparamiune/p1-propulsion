"""REV-GNC-7 (h)(ii): the vented mass at which the liq line-208 test (h4 method) first fails, 0.1 g steps from 80.0 to 83.0 g
(flown G80 per-run liquid shifted by -(m - 80) g, ESTIMATE)."""
import json, sys, math, importlib.util
import numpy as np
spec = importlib.util.spec_from_file_location("h4", "/dev/shm/rev_gnc7/scripts/h4_l208_ub95.py")
H = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1"
import csv, gzip
def load(path):
    rows = list(csv.DictReader(gzip.open(path, "rt")))
    return (np.array([int(r["run"]) for r in rows]), np.array([float(r["ok"]) for r in rows]) > 0.5, 1e3 * np.array([float(r["liq_left"]) for r in rows]))
ON = 80.0; res = []
data = {b: (load(f"{H}/rev3/tables/fly/rf_{b}_liq_G73_h285.csv.gz"), load(f"{H}/rev4/out_rev4/p2/rf_{b}_liq_G80_v351_h210.csv.gz")) for b in ("A1_none", "A1J_pc")}
for i in range(0, 31):
    m = 80.0 + 0.1 * i; lost = gained = n = 0
    for b, ((rr, okr, lr), (rc, okc, lc)) in data.items():
        k = 500; sref = okr[:k] & (lr[:k] >= ON); scase = okc[:k] & ((lc[:k] - (m - 80.0)) >= ON)
        lost += int((sref & ~scase).sum()); gained += int((~sref & scase).sum()); n += k
    d = (lost - gained) / n; ub = d + 1.645 * math.sqrt(max(((lost + gained) - (lost - gained) ** 2 / n) / n ** 2, 0))
    res.append(dict(m_g=round(m, 1), lost=lost, gained=gained, ub95_pp=round(100 * ub, 3), pass_=bool(100 * ub <= 1.0)))
first_fail = next((r["m_g"] for r in res if not r["pass_"]), None)
json.dump(dict(method=__doc__, rows=res, first_fail_g=first_fail), open(sys.argv[1], "w"), indent=1)
print("first fail at", first_fail); print([ (r["m_g"], r["lost"], r["ub95_pp"]) for r in res if r["lost"] != res[0]["lost"] or r["m_g"] in (80.0, 83.0)][:12])
