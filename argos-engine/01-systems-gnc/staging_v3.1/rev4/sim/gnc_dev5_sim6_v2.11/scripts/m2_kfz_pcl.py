"""m2_kfz_pcl v1.0 (GNC rev2, 2026-10-13): amendment (b) / RG-15 - re-fly of the Pc-lost arms of m2_mass_est v2 (Pc lost from
t = 0, open-loop flow factor CD_BAND or 1/CD_BAND, RE and commanded-thrust mass rules, comp variant) with the v2.9-dev
amendment K ON (kfz_on 1: k_hat and the B apex-predictor thrust frozen while Pc is invalid), paired run by run with the stored
rev1 tables (out/mass_est_v2/mest2_<base>_<spec>.csv, sim6 v2.8-dev = v2.9-dev with K off, m2_bitcheck_v29 A1/K1).
Hypothesis (K): with Pc invalid the thrust-effectiveness estimate k_hat = (m_hat a + drag) / F_model learns the open-loop flow
error and the burn-limit / apex predictors use it; freezing it removes that coupling. Comparator: the same arm with K off
(stored). Evidence: success P per arm (exact McNemar), touchdown speed, mass-estimate error at the end. Refutation: K loses
(P lower, p < 0.05) on any arm.
Env: m2r2_env.sh; GNC_KFZ_OUT (out/rev2/kfz_pcl), GNC_KFZ_SPLIT (0/1), GNC_KFZ_PARTS (mc,eval)."""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402
import m2_rg01_refly as F  # noqa: E402

VERSION = "m2_kfz_pcl v1.0"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_KFZ_OUT", f"{S}/rev2/kfz_pcl")
REF = f"{S}/mass_est_v2"
PARTS = os.environ.get("GNC_KFZ_PARTS", "mc,eval").split(",")
_ORIG = MV.run_cfg_case


def with_kfz(cfg, dr, spec, i, prior):
    c, disp = _ORIG(cfg, dr, spec, i, prior)
    return dict(c, kfz_on=1), disp


def part_mc():
    MV.run_cfg_case = with_kfz
    MV.OUT = OUT
    MV.SPLIT = os.environ.get("GNC_KFZ_SPLIT", "0/1")
    MV.jobs = lambda: [(b, n) for b in MV.PCL_BASES for n in MV.pcl_specs() if not n.startswith("mode0")]
    MV.part_mc()


def part_eval():
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n")[0], arms={})
    for b in MV.PCL_BASES:
        for n in MV.pcl_specs():
            if n.startswith("mode0"):
                continue
            p, q = os.path.join(OUT, f"mest2_{b}_{n}.csv"), os.path.join(REF, f"mest2_{b}_{n}.csv")
            if not (os.path.exists(p) and os.path.exists(q)):
                continue
            a, r = list(csv.DictReader(open(q))), list(csv.DictReader(open(p)))
            ok0, ok1 = F.col(a, "ok") > 0.5, F.col(r, "ok") > 0.5
            e = dict(F.mcnemar(ok0, ok1), ref=f"{q} (sha256/16 {F.sha16(q)})",
                     td_vz_ref=F.pct(F.col(a, "td_vz"), (1, 50)), td_vz=F.pct(F.col(r, "td_vz"), (1, 50)),
                     e_end_ref=F.pct(F.col(a, "mest_e_end"), (1, 50, 99)), e_end=F.pct(F.col(r, "mest_e_end"), (1, 50, 99)))
            out["arms"][f"{b}|{n}"] = e
            print(f"{b:12s} {n:16s} P K-off {e['P_ref']:.3f} K-on {e['P_case']:.3f} -{e['lost']}/+{e['gained']} p {e['p_exact']:.3g}"
                  f"{' LOSES' if e['loses'] else ''}", flush=True)
    with open(os.path.join(OUT, "kfz_pcl.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "kfz_pcl.json"), flush=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()
