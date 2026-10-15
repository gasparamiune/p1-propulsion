"""Reviewer probe: K mechanism on single runs of A1_none pcllo_re_comp (record keff, F/tsc, failure criterion)."""
import os, sys, json
import numpy as np
RUN = os.environ["RV_RUN"]
sys.path.insert(0, RUN); sys.path.insert(0, os.path.join(RUN, "scripts"))
import m2_mass_est_v2 as MV
from gncsim import run6 as R, sim6 as s6
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
print("rec names with k/F:", [n for n in s6.REC_NAMES if n in ("keff", "F", "tsc", "Fcmd", "phase", "t", "vz", "h") or "k" in n][:30])
base, spec = "A1_none", "pcllo_re_comp"
MV.COMB = MV.comb_draws(max(MV.NR, 500))
jr = json.load(open(f"{MV.S}/throat_growth/throat_growth.json"))["j_ref"]
MV.TG_JREF_DEFAULT = float(jr["A1"])
cfg = MV.base_cfg(base)
D = R.draw(np.random.default_rng(101), 500, cfg)
specs = dict(MV.case_specs(), **MV.pcl_specs())
for i in [int(x) for x in sys.argv[1:]]:
    for kon in (0, 1):
        c, disp = MV.run_cfg_case(cfg, D[i], specs[spec], i, "comb")
        res, rec, info = R.fly(dict(c, kfz_on=kon, rec_dt=0.01), disp, nrec=20000)
        n = int(res["nrec"]); t = rec[:n, I["t"]]; ph = rec[:n, I["phase"]]; ke = rec[:n, I["keff"]]
        crit = {k: round(float(res[k]), 3) for k in ("td_vz", "td_vh", "td_tilt", "td_rate", "exhausted", "tipover", "crash", "landed", "liq_left")}
        land = ph >= 5
        print(f"run {i} K{'on' if kon else 'off'} ok {R.success(res)} {crit} keff[asc end] {ke[np.argmax(ph>=2)]:.4f} keff[land start] {ke[np.argmax(land)] if land.any() else float('nan'):.4f} keff[end] {ke[n-1]:.4f} keff range landing {ke[land].min() if land.any() else 0:.4f}-{ke[land].max() if land.any() else 0:.4f}")
