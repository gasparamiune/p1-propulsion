"""REV-GNC-3: B1 default grain gate - re-execute the author's measurement draws (WL code; no flights) for the kept set,
then independent statistics on the stored B1 tables (rvlib)."""
import os, sys, gzip, csv
RUN = os.environ["RV_RUN"]; sys.path.insert(0, RUN); sys.path.insert(0, os.path.join(RUN, "scripts")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from rvlib import mcnemar, fmt, wilson, ok
import m2_web_limit as WL
from gncsim import run6 as R
N = 500
cfg = WL.base_cfg()[0]
D = R.draw(np.random.default_rng(WL.SEED), N, cfg)
Z = WL.meas_draws(N)
jref = float(cfg.get("throat_jref") or 0.0)
w = [WL.web_over(D[i], Z[i], WL.CASES["W1p"], jref) for i in range(N)]
am = np.array([x[1] for x in w]); nm = np.array([x[2] for x in w])
kept = ~(((am >= 1.25) & (nm <= 0.40)) | (am >= 1.25))
print("kept", int(kept.sum()), "| lead-rule-only grain changes", int(((am >= 1.25) & (nm <= 0.40)).sum()), "| a_meas>=1.25", int((am >= 1.25).sum()))
DB = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev2/results/b1_m60"
def rb(n):
    with gzip.open(f"{DB}/b1_{n}.csv.gz", "rt") as f: return list(csv.DictReader(f))
ref, m60 = rb("ref"), rb("m60")
K = [i for i in range(N) if kept[i]]
assert all(int(float(ref[i]["run"])) == i for i in range(N))
rk, mk = [ref[i] for i in K], [m60[i] for i in K]
k = sum(ok(rk)); print("ref kept P", k / len(rk), wilson(k, len(rk)), "exhausted", sum(float(r["exhausted"]) > 0.5 for r in rk))
print("m60 vs ref (kept):", fmt(mcnemar(ok(rk), ok(mk))), "exhausted", sum(float(r["exhausted"]) > 0.5 for r in mk))
for n, rr in (("ref", rk), ("m60", mk)):
    we = [1e3 * float(r["web_t_end"]) for r in rr]
    print(f"{n} kept: web_end min {min(we):.3f} mm, <1 mm {sum(v < 1.0 for v in we)}, limit acted {sum(float(r['web_tL']) >= 0 for r in rr)}")
