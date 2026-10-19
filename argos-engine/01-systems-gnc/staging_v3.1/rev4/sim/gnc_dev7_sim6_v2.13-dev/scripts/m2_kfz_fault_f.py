"""m2_kfz_fault_f v1.0 (GNC rev2, 2026-10-13): amendment (b) / RG-15, RG-18 gate - re-fly of the Pc-lost fault arms of m2_fault_f
v1.1 (stuck pintle at 670 / 876 N from ascent, floor and landing; Pc lost with open-loop flow x 1.143 or x 0.875; branches
Lhi_blind, Llo_blind, Llo_enc; MISS and GEO arms = Lhi_blind with the detectors off / geofence only) with the v2.9-dev amendment
K ON (kfz_on 1), paired run by run with the stored rev1 tables (out/fault_f, same draws and onsets; flown on sim6 v2.8-dev =
v2.9-dev with K off, m2_bitcheck_v29 A1).
Hypothesis: freezing k_hat while Pc is invalid does not reduce detection (FC_THRUST, PINTLE_FAULT) nor the miss consequence
bounds; it removes the k_est update from F/tsc without a Pc validity check (reviewer RG-18 gate). Comparator: stored K-off
arm. Evidence: detected faults, false decisions, success P (exact McNemar), apex and touchdown of the MISS / GEO arms.
Refutation: any arm with fewer detections, more false decisions or a McNemar loss.
Env: m2r2_env.sh; GNC_KFF_OUT (out/rev2/kfz_fault_f), GNC_FF_SPLIT (k/n), GNC_KFF_PARTS (mc,eval)."""
import json
import os
import sys
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_KFF_OUT", f"{S}/rev2/kfz_fault_f")
os.environ["GNC_FF_OUT"] = OUT
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import sim6 as s6  # noqa: E402
import m2_fault_f as FF  # noqa: E402
import m2_rg01_refly as F  # noqa: E402

VERSION = "m2_kfz_fault_f v1.0"
REF = f"{S}/fault_f"
PARTS = os.environ.get("GNC_KFF_PARTS", "mc,eval").split(",")
_ORIG = FF.MV.run_cfg_case
_ARMS = FF.arms


def with_kfz(cfg, dr, spec, i, prior):
    c, disp = _ORIG(cfg, dr, spec, i, prior)
    return dict(c, kfz_on=1), disp


def pcl_arms():
    return {k: v for k, v in _ARMS().items() if FF.BR[v["br"]][1] == 1}


def part_mc():
    FF.MV.run_cfg_case = with_kfz
    FF.OUT = OUT
    FF.arms = pcl_arms
    FF.part_mc()


def det(rows):
    return np.array([float(r["flt_tdec"]) >= float(r["flt_t0"]) >= 0.0 for r in rows])


def part_eval():
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n")[0], arms={}, totals={})
    tot = dict(det_ref=0, det_new=0, fault_ref=0, fault_new=0, false_ref=0, false_new=0, n=0, lost=0, gained=0)
    for name, a in pcl_arms().items():
        p, q = FF.fname(name), os.path.join(REF, "fault_" + name.replace("|", "_") + ".csv")
        r, s = FF.rows_csv(p), FF.rows_csv(q)
        if not (r and s):
            continue
        f_r, f_s = F.col(r, "flt_t0") >= 0.0, F.col(s, "flt_t0") >= 0.0
        e = dict(kind=a["kind"], n=len(r), faults_ref=int(f_s.sum()), faults_new=int(f_r.sum()),
                 detected_ref=int(det(s).sum()), detected_new=int(det(r).sum()),
                 false_ref=int(np.sum(F.col(s, "flt_false") > 0.5)), false_new=int(np.sum(F.col(r, "flt_false") > 0.5)),
                 paired=F.mcnemar(F.col(s, "ok") > 0.5, F.col(r, "ok") > 0.5), ref=f"{q} (sha256/16 {F.sha16(q)})")
        if a["kind"] in ("miss", "geo"):
            e.update(h_max_ref=F.pct(F.col(s, "h_max"), (50, 99)), h_max_new=F.pct(F.col(r, "h_max"), (50, 99)),
                     td_vz_ref=F.pct(F.col(s, "td_vz"), (1, 50)), td_vz_new=F.pct(F.col(r, "td_vz"), (1, 50)))
        out["arms"][name] = e
        if a["kind"] == "det":
            for k_, v_ in (("det_ref", e["detected_ref"]), ("det_new", e["detected_new"]), ("fault_ref", e["faults_ref"]),
                           ("fault_new", e["faults_new"]), ("false_ref", e["false_ref"]), ("false_new", e["false_new"]),
                           ("n", e["n"]), ("lost", e["paired"]["lost"]), ("gained", e["paired"]["gained"])):
                tot[k_] += v_
        print(f"{name:26s} faults {e['faults_ref']}->{e['faults_new']} detected {e['detected_ref']}->{e['detected_new']} "
              f"false {e['false_ref']}->{e['false_new']} P {e['paired']['P_ref']:.3f}->{e['paired']['P_case']:.3f} "
              f"-{e['paired']['lost']}/+{e['paired']['gained']}", flush=True)
    out["totals"] = tot
    with open(os.path.join(OUT, "kfz_fault_f.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("totals", tot, "wrote", os.path.join(OUT, "kfz_fault_f.json"), flush=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()
