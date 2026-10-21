"""m2_kest2_forensics v1.1 (2026-10-13; v1.1 corrects the estimator-error metric and the attribution rule. v1 measured
k_hat against k_true = F / F_pc and called 5 of 6 lost B1 runs 'estimator-driven'. That was wrong: sim6 gives the flight
software m_est = m_true (1 + m_est_err), so the quantity the accelerometer estimator measures BY DESIGN is
k* = (F / F_pc)(1 + m_est_err). It absorbs the mass-knowledge error, and that is what makes the delivered acceleration
equal the guidance model. The v1 'errors' tracked m_est_err run by run (e.g. run 428: +0.084 drawn, mean ratio 1.085).
v1 output kept as kest2_forensics_v1.json. v1.1 measures the error against k*, skips the first 1.0 s of the estimator
window (filter convergence from k_hat = 1), and attributes with the rule below): run-by-run forensics of the paired Monte Carlo comparison of the provisional FSW
baseline k_est_asc 2 against k_est_asc 0 (lead 2026-10-13: document the estimator failure modes - accelerometer bias,
drag-model error, wind gusts, low-thrust start - and the paired counts).

For every DISCORDANT run of the no-growth k_est_asc 2 cases (tg_B1_none_k2 vs pc_B1_h85_2kg; tg_A1_none_k2 vs
rs_A1_seq+0.3_planned; m2_throat_mc v1.1) the run is re-flown with the recorder on, once with k_est_asc 2 and once with
k_est_asc 0 (same configuration, same draw seed 101 / run index, sim6/run6 v2.7-dev). Each re-flight is checked against
its Monte Carlo CSV row (every stored result field except the record count), so the forensic flight IS the Monte Carlo run.
Reported per run: failure reasons (run6 summary criteria), the drawn wind / gust scale / thrust scale / accelerometer
bias and scale factor / tail-first drag factors, the estimator ratio k_hat / k_true (k_true = F / F_pc, the thrust per
Pc-map thrust) over the estimator window (B: phases 1-3 after the gates; A: landing burn, F > 75 N), the floor-command
range, whether the [0.8, 1.25] clamp was reached, and the largest tilt before the landing burn.
Attribution rule v1.1 (DERIVED; v1 rule kept in the v1 output as evidence of the wrong metric), in order:
  'wind / attitude limit'  B only: the k_est_asc 2 flight tilts > 20 deg in phases 1-3 (before the landing burn): the
                           drag model and the floor authority no longer apply (the comparator is classed the same way). Not
                           applied to A: the nominal DC-A1 v3 landing burn tilts up to 28 deg (lateral divert) - the first
                           v1.1 run applied it to A and mislabelled the A1 runs; corrected before publication;
  'estimator error'        else, |k_hat / k* - 1| > 5 % after the first 1.0 s of the estimator window with tilt < 20 deg;
  'propellant-limited, estimator as designed'  else, if the k_est_asc 2 failure includes propellant exhaustion;
  'landing divergence'     otherwise (no estimator, propellant or pre-landing attitude cause found).
Env: GNC_IFACE, GNC_ACT_RATE, GNC_KF_OUT (default out/v27_checks). Output: <out>/kest2_forensics.json"""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("GNC_PC_RATCHET", "1")
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_throat_mc as TG  # noqa: E402
import m2_duty_cycles_disp as DD  # noqa: E402

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_KF_OUT", f"{S}/v27_checks")
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
N, SEED = 500, 101
CASES = [("tg_B1_none_k2", f"{S}/throat_growth/throat_growth.json", "B"),
         ("tg_A1_none_k2", f"{S}/throat_growth_a1k2/throat_growth.json", "A")]


def why(r):
    w = []
    if r["landed"] < 0.5 or r["crash"] > 0.5:
        w.append("no_touchdown_or_crash")
    if abs(r["td_vz"]) > R.CRIT["vz"]:
        w.append("vz")
    if r["td_vh"] > R.CRIT["vh"]:
        w.append("vh")
    if r["td_tilt"] > R.CRIT["tilt"]:
        w.append("tilt")
    if r["td_rate"] > R.CRIT["rate"]:
        w.append("rate")
    if r["exhausted"] > 0.5:
        w.append("exhausted")
    if r["tipover"] > 0.5:
        w.append("tipover")
    return w


def fly_run(over, i, k):
    over = dict(over, k_est_asc=k)
    m = over.pop("m_fixed")
    cfg = R.cfg_of(**dict(over, m_n2o=float(m)))
    D = R.draw(np.random.default_rng(SEED), N, cfg)
    c, disp = R.run_cfg(cfg, D[i])
    res, rec, info = R.fly(dict(c, rec_dt=0.01), disp, nrec=8000)
    return res, rec, D[i], c


def est_stats(rec, prof, mest):
    """estimator statistics against k* = (F / F_pc)(1 + m_est_err) (v1.1) and, for continuity, against k_true = F / F_pc."""
    ph, F, Fpc, kh, tilt = (rec[:, I[n]] for n in ("phase", "F", "Fpc", "keff", "tilt"))
    t, hest = rec[:, I["t"]], rec[:, I["hest"]]
    if prof == "B":
        m = (ph >= 1) & (ph <= 3) & (t > 1.0) & (hest > 1.0) & (F > 1.0)
    else:
        m = (ph >= 5) & (ph <= 6) & (F > 75.0)
    # attitude window: B = phases 1-3 (upright flight before the landing burn); A = the landing burn itself (phases 5-6),
    # because the A coast and descent are tilted by design (turn-over at apogee, drogue)
    pre = ((ph >= 5) & (ph <= 6)) if prof == "A" else ((ph >= 1) & (ph <= 3))
    tmax = float(np.max(tilt[pre])) if pre.any() else float("nan")
    if not m.any():
        return dict(n=0, max_tilt_before_landing_burn_deg=tmax)
    kt = F[m] / np.maximum(Fpc[m], 1e-9)
    ks = kt * (1.0 + mest)
    e_t, e_s = kh[m] / kt - 1.0, kh[m] / ks - 1.0
    t0 = t[m][0]
    conv = m.copy()
    conv[m] = (t[m] >= t0 + 1.0) & (tilt[m] < 20.0)
    e_c = (kh[conv] / ((F[conv] / np.maximum(Fpc[conv], 1e-9)) * (1.0 + mest)) - 1.0) if conv.any() else np.array([0.0])
    out = dict(n=int(m.sum()), vs_k_star=dict(min=float(1 + e_s.min()), max=float(1 + e_s.max()), mean=float(1 + e_s.mean()),
                                               max_abs_err_converged_tilt_below_20deg=float(np.max(np.abs(e_c)))),
               vs_k_true_v1=dict(min=float(1 + e_t.min()), max=float(1 + e_t.max()), mean=float(1 + e_t.mean())),
               k_hat_min=float(kh[m].min()), k_hat_max=float(kh[m].max()),
               clamp_reached=bool(kh[m].min() <= 0.8 or kh[m].max() >= 1.25),
               Fcmd_floor_min_max=([float(rec[(ph == 3), I["Fcmd"]].min()), float(rec[(ph == 3), I["Fcmd"]].max())]
                                   if prof == "B" and (ph == 3).any() else None),
               max_tilt_before_landing_burn_deg=tmax)
    if prof == "B" and (ph == 3).any():
        p3 = np.where(ph == 3)[0]
        w = p3[t[p3] >= t[p3[-1]] - 2.0]
        out["floor_last2s_mean_err_vs_k_star"] = float(np.mean(kh[w] / ((F[w] / np.maximum(Fpc[w], 1e-9)) * (1.0 + mest)) - 1.0))
    return out


def attribute(r2, e2, prof):
    # the attitude rule applies to B only: the A landing burn tilts up to 28 deg in the nominal DC-A1 v3 flight (lateral
    # divert), so a tilt threshold there would mislabel normal landings (found on the first v1.1 run, A runs re-classed)
    if prof == "B" and e2.get("max_tilt_before_landing_burn_deg", 0.0) > 20.0:
        return "wind / attitude limit"
    if e2.get("vs_k_star", {}).get("max_abs_err_converged_tilt_below_20deg", 0.0) > 0.05:
        return "estimator error"
    if "exhausted" in why(r2):
        return "propellant-limited, estimator as designed"
    return "landing divergence (no estimator, propellant or pre-landing attitude cause found)"


def check_row(res, row):
    return [k for k in row if k in s6.RES_NAMES and k != "nrec" and not (
        float(row[k]) == float(res[k]) or (np.isnan(float(row[k])) and np.isnan(float(res[k]))))]


def main():
    os.makedirs(OUT, exist_ok=True)
    cases, jr = DD.case_over()
    out = dict(version="m2_kest2_forensics v1.1", date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE,
               attribution_rule=("v1.1, in order: wind / attitude limit (B only: k_est_asc 2 flight tilts > 20 deg in phases 1-3; "
                                 "not applied to A, whose nominal landing burn tilts up to 28 deg); estimator error (|k_hat / k* - 1| "
                                 "> 5 % after the first 1.0 s of the estimator window, tilt < 20 deg; k* = (F / F_pc)(1 + "
                                 "m_est_err)); propellant-limited, estimator as designed (exhausted); landing divergence. The v1 "
                                 "rule (|k_hat / k_true - 1| > 5 %) was wrong: it counted the designed absorption of the "
                                 "mass-knowledge error as estimator error (kest2_forensics_v1.json)"),
               sim_assumption=("sim6 gives the FSW m_est = m_true (1 + m_est_err), a constant fractional error; a real FSW "
                               "integrates modelled propellant flow, so an Isp / flow dispersion would add a drifting mass error "
                               "that this Monte Carlo does not contain (ASSUMED; open item for the independent review)"), cases={})
    for case, tgp, prof in CASES:
        tg = json.load(open(tgp))["monte_carlo"][case]
        pr = tg["vs_base"]
        over, csv_k2 = cases[case]
        rows_k2 = list(csv.DictReader(open(csv_k2)))
        rows_k0 = list(csv.DictReader(open(tg["base_csv"])))
        runs = []
        for lab, idx in (("lost", pr["lost_runs"]), ("gained", pr["gained_runs"])):
            for i in idx:
                r2, rec2, dr, c = fly_run(over, i, 2)
                r0, rec0, _, _ = fly_run(over, i, 0)
                mm2, mm0 = check_row(r2, rows_k2[i]), check_row(r0, rows_k0[i])
                mest = float(dr["m_est_err"])
                e2, e0 = est_stats(rec2, prof, mest), est_stats(rec0, prof, mest)
                attrib = attribute(r2, e2, prof) if lab == "lost" else None
                why_k0 = (("wind / attitude limit" if prof == "B" and e0.get("max_tilt_before_landing_burn_deg", 0.0) > 20.0 else
                           ("propellant exhausted" if "exhausted" in why(r0) else "other")) if lab == "gained" else None)
                runs.append(dict(run=i, kind=lab, reproduces_k2=not mm2, reproduces_k0=not mm0, mismatch_k2=mm2[:5],
                                 mismatch_k0=mm0[:5], attribution=attrib, comparator_failure_class=why_k0,
                                 k2=dict(ok=R.success(r2), why=why(r2), td_vz=float(r2["td_vz"]), td_vh=float(r2["td_vh"]),
                                         td_tilt=float(r2["td_tilt"]), h_max=float(r2["h_max"]), burn_s=float(r2["burn_time"]),
                                         liq_left=float(r2["liq_left"]), estimator=e2),
                                 k0=dict(ok=R.success(r0), why=why(r0), td_vz=float(r0["td_vz"]), td_vh=float(r0["td_vh"]),
                                         td_tilt=float(r0["td_tilt"]), h_max=float(r0["h_max"]), burn_s=float(r0["burn_time"]),
                                         liq_left=float(r0["liq_left"]), estimator=e0),
                                 draw=dict(wind=float(c["wind"]), gust_scale=float(c["gust_scale"]),
                                           thrust_scale=float(dr["thrust_scale"]), isp_scale=float(dr["isp_scale"]),
                                           a_bias_z=float(dr["a_b"][2]), a_sf=float(dr["a_sf"]), m_est_err=float(dr["m_est_err"]),
                                           ca_tf=float(c["aero_unc"]["ca_tf"]), k_retro=float(c["aero_unc"]["k_retro"]),
                                           dry_scale=float(dr["dry_scale"]))))
                x = runs[-1]
                ks_ = e2.get("vs_k_star", {})
                print(f"{case} run {i:3d} {lab:6s} rep {x['reproduces_k2']}/{x['reproduces_k0']} | k2 ok {x['k2']['ok']} "
                      f"{x['k2']['why']} apex {x['k2']['h_max']:.1f} | k0 ok {x['k0']['ok']} {x['k0']['why']} apex "
                      f"{x['k0']['h_max']:.1f} | wind {x['draw']['wind']:.2f} gust {x['draw']['gust_scale']:.2f} ts "
                      f"{x['draw']['thrust_scale']:.3f} isp {x['draw']['isp_scale']:.3f} mest {mest:+.3f} | k_hat/k* "
                      f"{ks_.get('min', float('nan')):.3f}-{ks_.get('max', float('nan')):.3f} (conv |err| "
                      f"{ks_.get('max_abs_err_converged_tilt_below_20deg', float('nan')):.3f}), max tilt pre-landing "
                      f"{e2.get('max_tilt_before_landing_burn_deg', float('nan')):.1f} | {attrib or why_k0}", flush=True)
        lost = [r for r in runs if r["kind"] == "lost"]
        gained = [r for r in runs if r["kind"] == "gained"]
        cls = {}
        for r in lost:
            cls.setdefault(r["attribution"], []).append(r["run"])
        clg = {}
        for r in gained:
            clg.setdefault(r["comparator_failure_class"], []).append(r["run"])
        out["cases"][case] = dict(
            pair=dict(lost=pr["lost"], gained=pr["gained"], p_exact_mcnemar=pr["p"], P_base=pr["P_base"], P_k2=pr["P_case"]),
            all_reproduce=all(r["reproduces_k2"] and r["reproduces_k0"] for r in runs),
            lost_by_attribution=cls, gained_by_comparator_failure=clg,
            max_converged_estimator_error_vs_k_star=max(r["k2"]["estimator"].get("vs_k_star", {}).get(
                "max_abs_err_converged_tilt_below_20deg", 0.0) for r in runs),
            max_converged_estimator_error_vs_k_star_excl_attitude_limit=max(
                [r["k2"]["estimator"].get("vs_k_star", {}).get("max_abs_err_converged_tilt_below_20deg", 0.0) for r in runs
                 if not (prof == "B" and r["k2"]["estimator"].get("max_tilt_before_landing_burn_deg", 0.0) > 20.0)] or [0.0]),
            runs=runs)
    with open(os.path.join(OUT, "kest2_forensics.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "kest2_forensics.json"))


if __name__ == "__main__":
    main()
