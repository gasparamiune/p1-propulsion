"""m2_csi_v3_mc_eval v1 (2026-10-12): evaluate the ENG-07d FEA-stiffness Monte Carlo (m2_csi_v3_mc.py).
Per case: P (Wilson 95 %), paired exact McNemar vs the same flight software on the baseline stiffness range
(fk_oldK_J1.6, or m2_meco mr_J1.6_fix_td72) and vs the low-pass-only twin of each notch case, ENG-07b (each run's longest
actuator-saturation episode in the landing burn, p99/max), delivered hinge moment p99/max, engine angular acceleration
p99, and where the failures sit in mount stiffness / damping / notch mistune.
Env: GNC_OUT (default out/csi_v3_mc), GNC_SUFFIX (default fk), GNC_MECO_OUT (default out/meco), GNC_MECO_SUFFIX (mr).
Output: <out>/csi_v3_mc_eval_<suf>.json"""
import csv
import json
import os
import sys
import numpy as np
from scipy.stats import binomtest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/csi_v3_mc")
SUF = os.environ.get("GNC_SUFFIX", "fk")
MOUT = os.environ.get("GNC_MECO_OUT", "/home/claude/work/space/out/meco")
MSUF = os.environ.get("GNC_MECO_SUFFIX", "mr")
TWIN = {"fk_J1.6_notch": "fk_J1.6_lpf", "fk_J2.7_notch": "fk_J2.7_lpf", "fk_J1.6_f125_notch": "fk_J1.6_f125_lpf",
        "fk_J1.6_lpf": "fk_oldK_J1.6", "fk_J0_lpf": "fk_oldK_J1.6", "fk_J2.7_lpf": "fk_oldK_J1.6",
        "fk_J1.6_f125_lpf": "fk_oldK_J1.6"}


def rows(path):
    return list(csv.DictReader(open(path))) if os.path.exists(path) else None


def pair(a, b):
    oa = np.array([int(r["ok"]) for r in a]) > 0
    ob = np.array([int(r["ok"]) for r in b]) > 0
    lost, gained = int(np.sum(oa & ~ob)), int(np.sum(~oa & ob))
    p = binomtest(lost, lost + gained, 0.5).pvalue if lost + gained else 1.0
    return dict(lost=lost, gained=gained, p=float(p), loses=bool(ob.mean() < oa.mean() and p < 0.05),
                lost_runs=[int(r["run"]) for r, x, y in zip(a, oa, ob) if x and not y])


def pct(x, q):
    return float(np.percentile(x, q)) if len(x) else float("nan")


def main():
    S = json.load(open(os.path.join(OUT, f"mc6_summary_{SUF}.json")))
    C = S["cases"]
    ref_meco = rows(os.path.join(MOUT, f"mc6_runs_mr_J1.6_fix_td72_{MSUF}.csv"))
    base = rows(os.path.join(MOUT, f"mc6_runs_AD_prov_2kg_{MSUF}.csv"))
    out = dict(version=f"m2_csi_v3_mc_eval v1 {SUF}", sim=S.get("sim"), K_FEA=S.get("K_FEA"), notch=S.get("notch"), cases={})
    for c in C:
        r = rows(os.path.join(OUT, f"mc6_runs_{c}_{SUF}.csv"))
        if r is None:
            continue
        g = lambda k: np.array([float(x[k]) if x.get(k) not in (None, "") else np.nan for x in r])  # noqa: E731
        ok = g("ok") > 0.5
        lo, hi = R.wilson(int(ok.sum()), len(ok))
        rk, rz = g("rock_K"), g("rock_zeta")
        n_m = R.sources()["mech"]["tvc_actuation"]["gear_ratio_n"]["v"]
        fk = (float(C[c]["config"]["act_n"]) / n_m) ** 2 if C[c]["config"].get("act_n") else 1.0
        rec = dict(case=c, note=C[c]["note"], P=float(ok.mean()), ci95=[lo, hi], fail_modes=C[c]["summary"]["fail_modes"],
                   ENG07b_longest_ep_s=dict(p99=pct(g("act_sat_max_dur"), 99), max=float(np.nanmax(g("act_sat_max_dur"))),
                                            frac_gt_0p1=float(np.mean(g("act_sat_max_dur") > 0.1))),
                   hinge_Nm=dict(p99=pct(g("max_hinge"), 99), max=float(np.nanmax(g("max_hinge")))),
                   hinge_demand_Nm=dict(p99=pct(g("max_hinge_dem"), 99), max=float(np.nanmax(g("max_hinge_dem")))),
                   gim_acc_p99_rad_s2=pct(g("max_gim_acc"), 99), gim_max_deg=float(np.nanmax(g("max_gim"))),
                   K_engine_axis_drawn=[float(np.nanmin(rk) * fk), float(np.nanmax(rk) * fk)],
                   failures=[dict(run=int(x["run"]), K=float(x["rock_K"]) * fk, zeta=float(x["rock_zeta"]),
                                  notch_mis=(float(x["notch_mis"]) if x.get("notch_mis") else None),
                                  td_vh=float(x["td_vh"]), td_rate=float(x["td_rate"]), td_tilt=float(x["td_tilt"]),
                                  crash=float(x["crash"]), wind=float(x["wind"]))
                             for x in r if int(x["ok"]) == 0])
        Kf = np.array([f["K"] for f in rec["failures"]])
        if len(Kf):
            rec["failure_K_median_vs_all"] = [float(np.median(Kf)), float(np.median(rk * fk))]
        if "fk_oldK_J1.6" in C and c != "fk_oldK_J1.6":
            ro = rows(os.path.join(OUT, f"mc6_runs_fk_oldK_J1.6_{SUF}.csv"))
            if ro is not None:
                rec["vs_fk_oldK_J1.6"] = pair(ro, r)
        if c in TWIN and TWIN[c] != "fk_oldK_J1.6":
            rt = rows(os.path.join(OUT, f"mc6_runs_{TWIN[c]}_{SUF}.csv"))
            if rt is not None:
                rec["vs_" + TWIN[c]] = pair(rt, r)
        if base is not None:
            rec["vs_AD_prov_2kg"] = pair(base, r)
        if c == "fk_oldK_J1.6" and ref_meco is not None:
            same = all(int(a["ok"]) == int(b["ok"]) and abs(float(a["td_vh"]) - float(b["td_vh"])) < 1e-12
                       for a, b in zip(ref_meco, r))
            rec["identical_to_mr_J1.6_fix_td72"] = bool(same)
        out["cases"][c] = rec
        v1 = rec.get("vs_fk_oldK_J1.6", {})
        vt = rec.get("vs_" + TWIN.get(c, "-"), {})
        print(f"{c:22s} P {rec['P']:.3f} [{lo:.3f},{hi:.3f}] vs oldK -{v1.get('lost', '')}/+{v1.get('gained', '')} "
              f"p {v1.get('p', float('nan')):.2g}{' LOSES' if v1.get('loses') else ''} | vs twin {TWIN.get(c, '-')} "
              f"-{vt.get('lost', '')}/+{vt.get('gained', '')} p {vt.get('p', float('nan')):.2g} | ENG-07b p99 "
              f"{1e3 * rec['ENG07b_longest_ep_s']['p99']:.0f} ms max {1e3 * rec['ENG07b_longest_ep_s']['max']:.0f} ms | hinge "
              f"p99 {rec['hinge_Nm']['p99']:.1f} max {rec['hinge_Nm']['max']:.1f} N m | K {rec['K_engine_axis_drawn'][0]:.0f}-"
              f"{rec['K_engine_axis_drawn'][1]:.0f} | fails {rec['fail_modes']}"
              + (f" | identical to mr_J1.6_fix_td72: {rec['identical_to_mr_J1.6_fix_td72']}" if "identical_to_mr_J1.6_fix_td72" in rec else ""),
              flush=True)
    with open(os.path.join(OUT, f"csi_v3_mc_eval_{SUF}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main()
