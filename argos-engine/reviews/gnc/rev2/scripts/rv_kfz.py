"""Reviewer driver: fly one m2_mass_est_v2 Pc-lost arm on the staged v2.9-dev sim with K off or on (500 runs), output to scratch."""
import os, sys
RUN = os.environ["RV_RUN"]
sys.path.insert(0, RUN); sys.path.insert(0, os.path.join(RUN, "scripts"))
import m2_mass_est_v2 as MV
mode, base, spec = sys.argv[1], sys.argv[2], sys.argv[3]
MV.OUT = os.path.join(os.environ["RV_OUT"], "kfz_" + mode)
MV.SPLIT = "0/1"
MV.jobs = lambda: [(base, spec)]
if mode == "on":
    _orig = MV.run_cfg_case
    def with_kfz(cfg, dr, sp, i, prior):
        c, disp = _orig(cfg, dr, sp, i, prior)
        return dict(c, kfz_on=1), disp
    MV.run_cfg_case = with_kfz
MV.part_mc()
