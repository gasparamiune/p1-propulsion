"""m2_mest_budget v1 (GNC, 2026-10-13): review REV-GNC-1 RG-16 item 1, the mass-estimate requirement restated as a total budget
over the burn, bias and random parts separated, from the flown-estimator Monte Carlo of m2_mass_est v2 (sim6 v2.8-dev amendment
M, 500 runs per case, seed 101; same draws in every case).

Method (corrects the budget_calibrated block of mass_est_v2.json, which took each source case's own error and so counted the
regression-band model-form term once per source on the band base): the contribution of source s on run i is
    c_s,i = e_s,i - e_ideal,i
(e = m_hat / m_exact - 1 at the end of the first burn, at the last lit step, and the largest |e| in the FC_THRUST window;
"ideal" = the flown estimator with every error source zero on the same run). On a base with the regression band the "ideal"
error IS the band term (the flight software integrates the map flow; the truth flow is the map x phi(a, n, X)).
RANDOM sources (per flight): weighing at ARM (w 20 g 1 sigma), Pc transducer offset after auto-zero (pccal 0.1 %FS; pcteb
TEB 1.5 %FS as 3 sigma shown as the alternative), start transients (U(0, 8.7 g) truth vs 4.35 g allowance): 1 sigma = std over
runs; combined by RSS (independent).
BIAS sources (per engine or per condition): static-fire flow calibration residual (cal15 1.5 %), growth model (g_hat 0.09 vs
truth U(0.07, 0.11); bracket: no growth with the model on, and growth with the model off), regression band (B1 band base: the
ideal case), Pc-lost flow excess / deficit (k 1.143 / 0.875; RE rule in the FC window, commanded-thrust model elsewhere):
bound = the largest |c_s,i| over the 500 runs (p99.8 shown too); combined LINEARLY (they can align).
Budget line: 3 sigma_random (RSS) + sum of bias bounds, at the end of the first burn, at the end, and in the FC window.
The Monte Carlo totals (tot_cal: all calibrated sources together on the same run) are given as the realised check.
Output: <out>/mest_budget_v1.json"""
import csv
import json
import os
import numpy as np

S = "/home/claude/work/space/out"
D = os.environ.get("GNC_MEST2_OUT", f"{S}/mass_est_v2")
OUT = os.environ.get("GNC_MEST2_OUT", f"{S}/mass_est_v2")
VERSION = "m2_mest_budget v1"
KEYS = {"b1end": "mest_e_b1end", "end": "mest_e_end", "fc": "mest_e_maxabs_fc"}
RANDOM = ("src_w20", "src_pccal", "src_starts")
RANDOM_ALT = ("src_pcteb",)
BIAS = ("src_cal15", "src_gmodel")
BRACKET = ("src_gnone", "src_uncal")


def rows(base, case):
    p = os.path.join(D, f"mest2_{base}_{case}.csv")
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def col(r, k):
    return np.array([float(x[k]) for x in r])


def contrib(base, case, ref="ideal"):
    a, b = rows(base, ref), rows(base, case)
    if a is None or b is None:
        return None
    out = {}
    for lab, k in KEYS.items():
        c = col(b, k) - col(a, k)
        out[lab] = dict(mean=float(c.mean()), sd=float(c.std(ddof=1)), max_abs=float(np.max(np.abs(c))),
                        p998_abs=float(np.percentile(np.abs(c), 99.8)), min=float(c.min()), max=float(c.max()))
    return out


def own(base, case):
    b = rows(base, case)
    if b is None:
        return None
    out = {}
    for lab, k in KEYS.items():
        c = col(b, k)
        out[lab] = dict(mean=float(c.mean()), sd=float(c.std(ddof=1)), max_abs=float(np.max(np.abs(c))),
                        p998_abs=float(np.percentile(np.abs(c), 99.8)), min=float(c.min()), max=float(c.max()))
    return out


def budget(base, band=False):
    res = dict(random={}, bias={}, brackets={})
    for s in RANDOM + RANDOM_ALT:
        res["random"][s] = contrib(base, s)
    for s in BIAS + BRACKET:
        (res["bias"] if s in BIAS else res["brackets"])[s] = contrib(base, s)
    if band:
        res["bias"]["regression_band (ideal case)"] = own(base, "ideal")
    line = {}
    for lab in KEYS:
        sig = float(np.sqrt(sum(res["random"][s][lab]["sd"] ** 2 for s in RANDOM if res["random"][s])))
        bias = float(sum(v[lab]["max_abs"] for v in res["bias"].values() if v))
        line[lab] = dict(random_rss_1sigma=sig, bias_linear_bound=bias, total_3sigma_plus_bias=3.0 * sig + bias)
    res["line"] = line
    tot = own(base, "tot_cal")
    res["mc_total_tot_cal"] = tot
    res["mc_total_tot_cal_comp"] = own(base, "tot_cal_comp")
    res["mc_total_tot_uncal"] = own(base, "tot_uncal")
    return res


def pcl(base):
    out = {}
    for side in ("hi", "lo"):
        for rule in ("re", "cmd", "re_comp"):
            c = contrib(base, f"pcl{side}_{rule}", ref=f"mode0_pcl{side}") if False else own(base, f"pcl{side}_{rule}")
            out[f"pcl{side}_{rule}"] = c
    return out


def main():
    out = dict(version=VERSION, date="2026-10-13", source=D, method=__doc__.split("\n\n")[1].strip(), bases={})
    for base, band in (("A1_pc", False), ("A1_none", False), ("tgl_B1_lead62_pc_k2", False), ("rbl_B1_lead62_pc_k2", True)):
        out["bases"][base] = budget(base, band)
    out["pc_lost"] = {b: pcl(b) for b in ("A1_none", "B1_62_none")}
    out["pc_lost_note"] = ("errors of the whole estimate with Pc lost from t = 0 (weighing 20 g, starts, cal15; growth model "
                           "off), flow excess k 1.143 (hi) / deficit 0.875 (lo) applied to the delivered thrust and flow "
                           "together; re = rocket equation on the accelerometer thrust inside the FC window, commanded-thrust "
                           "model elsewhere; cmd = commanded-thrust model everywhere; comp = with the lever-arm / direction "
                           "compensation")
    p = os.path.join(OUT, "mest_budget_v1.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1, default=float)
    for b, v in out["bases"].items():
        print("==", b)
        for lab, L in v["line"].items():
            t = v["mc_total_tot_cal"][lab] if v["mc_total_tot_cal"] else None
            print(f"   {lab:6s} random 1s {100 * L['random_rss_1sigma']:.3f} %  bias {100 * L['bias_linear_bound']:.3f} %  "
                  f"3s+bias {100 * L['total_3sigma_plus_bias']:.3f} %  | MC tot_cal mean {100 * t['mean']:+.3f} sd "
                  f"{100 * t['sd']:.3f} max|e| {100 * t['max_abs']:.3f} %")
        for grp in ("random", "bias", "brackets"):
            for s, c in v[grp].items():
                if c:
                    print(f"      {grp:8s} {s:30s} end mean {100 * c['end']['mean']:+.3f} sd {100 * c['end']['sd']:.3f} max|c| "
                          f"{100 * c['end']['max_abs']:.3f} | fc max|c| {100 * c['fc']['max_abs']:.3f} %")
    for b, v in out["pc_lost"].items():
        for k, c in v.items():
            if c:
                print(f"   PCL {b:10s} {k:12s} end mean {100 * c['end']['mean']:+.3f} sd {100 * c['end']['sd']:.3f} max|e| "
                      f"{100 * c['end']['max_abs']:.3f} | fc max|e| {100 * c['fc']['max_abs']:.3f} % (min {100 * c['fc']['min']:+.3f}, "
                      f"max {100 * c['fc']['max']:+.3f})")
    print("wrote", p)


if __name__ == "__main__":
    main()
