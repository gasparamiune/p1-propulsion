"""REV-GNC-3 reviewer script (independent of the author): RG-16 random term AT THE DETECTOR OUTPUT (lead line 175 (6)).

Re-evaluates one A1 RG-16 case of m2_rg16_fct_terms v2.1 (200 runs, same draws, same flights, same reconstruction RNG as
m2_mass_est_v2.part_fct) and records, per run, the frame stream that the FC detector sees:
  fa  = 20 ms first-order filtered accelerometer thrust estimate, 100 Hz frames at the run's random phase, 0.1 N steps
  ft  = true thrust through the same filter and frames
  sel = fc window, past the 0.1 s guard, F_true > 300 N  (the author's eps selection)
  nf  = noise-free filtered estimate (same reconstruction, noise off), to split systematic and noise parts
Checks first that the author's stored per-run statistics (held max, eps min / p1 / median, frame count) and pooled
eps quantiles are reproduced, then writes the per-run arrays (npz) for the reviewer's budget analysis (rv_rg16_budget.py).
Usage: rv_rg16_held.py CASE   (CASE = H_cal_comp_path | H_cal_path | ...)  ; writes $RV_OUT/rg16held_<CASE>.npz/.json
"""
import json
import os
import sys
import time
import numpy as np

RUN = os.environ["RV_RUN"]
sys.path.insert(0, RUN)
sys.path.insert(0, os.path.join(RUN, "scripts"))
import m2_rg16_fct_terms_v2 as RG  # noqa: E402
import m2_fc_thrust as FT  # noqa: E402
from gncsim import run6 as R  # noqa: E402

MV = RG.MV
I, PN = MV.I, MV.PN
case = sys.argv[1]
out_dir = os.environ["RV_OUT"]
os.makedirs(out_dir, exist_ok=True)
stored = json.load(open(os.path.join(os.environ["RV_STORED"], f"fct2_A1_{case}.json")))

(_, spec) = RG.cases()[("A1", case)]
jr = json.load(open(RG.F.TG))["j_ref"]
MV.TG_JREF_DEFAULT = float(jr["A1"])
MV.FCT_CASES = {case: spec}
C, _ = FT.cfgs()
cfg = C["A1"]
D = R.draw(np.random.default_rng(101), 500, cfg)
t0 = time.time()
arrs = {}
chk = []
pooled = []
for i in range(MV.NFCT):
    c, disp = RG.run_cfg_case_bias(cfg, D[i], spec, i, "fct")
    c = dict(c, rec_dt=FT.DT)
    par = R.build(c, disp)[0]
    res, rec, _ = R.fly(c, disp, nrec=100000)
    rng = np.random.default_rng(20261019 + i + (0 if case.startswith("H") else 100000))
    Fr = MV.reconstruct_flown(par, rec, rng, "A1", spec.get("comp", 0))
    air, fc, lit, drog = FT.windows(par, res, rec, "A1")
    p0 = int(rng.integers(0, FT.KF))
    fa = np.round(FT.filt(Fr, 0.020)[p0::FT.KF] * 10.0) / 10.0
    ft = FT.filt(rec[:, I["F"]], 0.020)[p0::FT.KF]
    fw = fc[p0::FT.KF]
    fs = (fc & (FT.open_time(fc) >= FT.GUARD))[p0::FT.KF]
    hm, kh = FT.held_max(fa, fw)
    sel = fs & (ft > 300.0)
    eps = fa[sel] / ft[sel] - 1.0
    pooled.append(eps.astype(np.float32))
    Fnf = MV.reconstruct_flown(par, rec, None, "A1", spec.get("comp", 0), noise=False)
    nf = FT.filt(Fnf, 0.020)[p0::FT.KF]
    m_hat = rec[:, I["mex"]] * (1.0 + rec[:, I["mhe"]])
    abz = (par[PN["a_bz"]] * m_hat)[p0::FT.KF]
    r = stored["runs"][i]
    chk.append(dict(run=i, held_max=(float(hm), r["held_max_fc_N"]), n=(int(sel.sum()), r["n_frames"]),
                    eps_min=(float(eps.min()) if len(eps) else None, r["eps_min"]),
                    eps_p01=(float(np.percentile(eps, 1)) if len(eps) else None, r["eps_p01"]),
                    eps_med=(float(np.median(eps)) if len(eps) else None, r["eps_med"])))
    arrs[f"fa_{i}"] = fa
    arrs[f"ft_{i}"] = ft
    arrs[f"nf_{i}"] = nf
    arrs[f"abz_{i}"] = abz
    arrs[f"sel_{i}"] = sel
    arrs[f"fw_{i}"] = fw
allx = np.concatenate(pooled)
qv = [float(np.percentile(allx, q)) for q in MV.EPS_Q]
same_q = qv == stored["eps_pooled"]["values"]
bad = [c_ for c_ in chk if any(a != b for a, b in (c_["held_max"], c_["n"], c_["eps_min"], c_["eps_p01"], c_["eps_med"]))]
np.savez_compressed(os.path.join(out_dir, f"rg16held_{case}.npz"), **arrs)
summ = dict(case=case, n=MV.NFCT, cpu_s=time.time() - t0, eps_pooled_q=qv, stored_q=stored["eps_pooled"]["values"],
            pooled_quantiles_identical=same_q, n_frames=int(len(allx)), stored_n_frames=stored["eps_pooled"]["n_frames"],
            per_run_mismatches=len(bad), first_mismatches=bad[:3])
json.dump(summ, open(os.path.join(out_dir, f"rg16held_{case}.json"), "w"), indent=1)
print(json.dumps(summ)[:1500])
