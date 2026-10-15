"""m2_gnc_json_v31 v1.1 (GNC, 2026-10-13): gnc.json v3.1 STAGING = the published gnc.json v3 plus explicit patches.

v1.1: relight_vapour_start_fallback (lead request 2026-10-13: cost of planning every relight as a 44 cm3 vapour-segment start,
m2_relight_seg44 v1.2) and the lead decisions of 2026-10-13 on FC_THRUST (adopted: 650 N / 3 frames on the tau 20 ms estimate,
valid flag, provisional FC mass-estimate requirement <= 1 % 1 sigma, founder weighing at ARM, v3.1 to the reviewer as an
addendum) and on the retained vapour. When out/mass_est/mass_est.json exists, the mass_estimator section (m2_mass_est) is added.

gnc.json v3 (interfaces/gnc.json, sha256/16 3e97c378cfebee95) and REPORT-v3.md are frozen while the independent GNC review runs
(lead 2026-10-13). This builder does not rebuild v3: it reads the published v3 bytes (hash checked), adds the v3.1 items and
writes 01-systems-gnc/staging_v3.1/gnc_v3.1_staging.json. Every v3 section is carried unchanged except the summary lists
(status, open_items, requests, answers_to_requests, changes, scripts, lead decisions) where v3.1 lines are appended or replaced
as listed in changes_from_v3.
v3.1 items:
  over_thrust_fc_thrust     closure item 1 (lead 2026-10-13): FC_THRUST accelerometer estimate 3-sigma error and latency,
                            Pc-lost false aborts, stuck-pintle detection, threshold proposal (m2_fc_thrust v1.1) and the
                            FC mass-estimate requirement (m2_fc_thrust_mest v1)
  coast_accel_a1            Combustion data item 1 (lead 2026-10-13): A1 body-axis specific force MECO -> relight command
                            (m2_coast_accel_a1 v1)
  duty_cycles.records_b1_62m_staging  Combustion data item 2: B1 62 m p99 / max duty cycles (m2_dc_b1_62m_record v1)
  t_tank_arm_range          ARM range 15-24 C vs the U(15, 25) C draw (m2_ttank_arm_check v1); lead: recorded, no re-run, the
                            next GNC baseline draws U(15, 24) C
  known_issue_v3_builder    re-running m2_gnc_json_v3 v5 with fc_thrust.json present stops on an undefined fc_thrust_section
                            (v3 was built without FC_THRUST, so the published v3 is not affected)
Env: GNC_HUB (hub root), GNC_GJ31_DEST (default out/gnc_json/gnc_v3.1_staging.json)."""
import copy
import hashlib
import json
import os
import numpy as np

VERSION = "m2_gnc_json_v31 v1.1"
HUBROOT = os.environ.get("GNC_HUB", "/home/claude/work/shared-fallback/engine")
BASE = os.path.join(HUBROOT, "interfaces", "gnc.json")
BASE_SHA16 = "3e97c378cfebee95"
O = "/home/claude/work/space/out"
DEST = os.environ.get("GNC_GJ31_DEST", f"{O}/gnc_json/gnc_v3.1_staging.json")
STG = "01-systems-gnc/staging_v3.1"
MANIFEST = os.path.join(HUBROOT, STG, "MANIFEST_staging_v3.1.sha256")
DATE = "2026-10-13"


def jl(p):
    with open(p) as f:
        return json.load(f)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def P(v, tag, note=None, **kw):
    d = {"v": v, "tag": tag}
    if note:
        d["note"] = note
    d.update(kw)
    return d


def r(x, n=3):
    if x is None:
        return None
    if isinstance(x, (list, tuple)):
        return [r(y, n) for y in x]
    return float(round(float(x), n))


def staged(rel):
    """sha256 of a staged hub file from the staging manifest (path relative to staging_v3.1)."""
    for line in open(MANIFEST):
        if line.startswith("#") or not line.strip():
            continue
        h, p = line.rstrip("\n").split("  ", 1)
        if p == rel:
            return h
    return None


def fref(rel):
    return {"file": f"{STG}/{rel}", "sha256": staged(rel)}


# ------------------------------------------------------------------------------------------------- FC_THRUST (closure item 1)
def fc_thrust_section(F, proposal, M):
    """over_thrust_fc_thrust from m2_fc_thrust v1.1 (fc_thrust.json), the mass-estimate sensitivity (m2_fc_thrust_mest v1,
    fc_thrust_mest.json) and the GNC proposal block (built in main)."""
    br = F["branches"]
    eb = F["error_3sigma_healthy_pooled"]
    lat = F["latency"]
    variants = [v for v in ("raw", "box10ms", "tau10ms", "tau20ms") if v in eb]
    err = {}
    for v in variants:
        x = eb[v]
        dec = F["error_decomposition"]["by_variant"][v]
        err[v] = {"three_sigma_all_burning_frames": r(x["three_sigma"], 4),
                  "three_sigma_F_ge_450N": r(x["three_sigma_F_ge_450N"], 4),
                  "p0135_p99865_all": [r(x["p0135"], 4), r(x["p99865"], 4)],
                  "mean_sd_F_ge_450N": r(x["mean_sd_F_ge_450N"], 4),
                  "abs_error_p0135_p99865_F_ge_450N_N": r(x["errN_p0135_p99865_F_ge_450N"], 1),
                  "per_run_bias_sd_by_branch": {k: r(b[v]["per_run_bias_sd"], 4) for k, b in br.items()},
                  "within_run_sd_median_by_branch": {k: r(b[v]["within_run_sd_median_max"][0], 4) for k, b in br.items()},
                  "without_mass_error_F_ge_450N": {"mean_sd": r(dec["rest_mean_sd_F_ge_450N"], 4),
                                                   "p0135_p99865": r(dec["rest_p0135_p99865_F_ge_450N"], 4)},
                  "frames": x["n_frames"], "frames_F_ge_450N": x["n_frames_F_ge_450N"]}
    late = {v: {"step_delay_50pct_mean_max_s": r(lat[v]["step_delay_50pct_mean_max_s"], 4),
                "step_delay_90pct_mean_max_s": r(lat[v]["step_delay_90pct_mean_max_s"], 4),
                "ramp_lag_s": r(lat[v]["ramp_lag_s"], 4), "frame_staleness_s": r(lat[v]["frame_staleness_s"], 4),
                "abort_decision_delay_step_mean_max_s": r(lat[v]["abort_decision_delay_step_to_2T_mean_max_s"], 4)} for v in variants}
    fa = {}
    for k, b in br.items():
        fa[k] = {v: {"held_max_fc_p50_p99_max_N": r(b[v]["held_max_fc_p50_p99_max_N"], 1),
                     "held_max_air_p50_p99_max_N": r(b[v]["held_max_air_p50_p99_max_N"], 1),
                     "true_thrust_max_fc_p50_max_N": r(b[v]["Ftrue_max_fc_p50_max_N"], 1),
                     "false_aborts_650N_fc": b[v]["false_aborts"]["fc|650"],
                     "false_aborts_650N_air": b[v]["false_aborts"]["air|650"],
                     "false_aborts_by_threshold_fc": {T: b[v]["false_aborts"][f"fc|{T}"]["n"] for T in ("600", "620", "635", "650", "675")}}
                 for v in variants}
        fa[k]["P_landing"] = b["P"]
        fa[k]["k_hat_check_sim"] = b["k_hat_check_sim"]
    sw = F["threshold_sweep_fc"]["by_case"]
    gauss650 = {k.replace("|", " "): r(v["gauss"]["650"], 8) for k, v in sw.items() if "|L|" in k}
    sp = F["stuck_pintle_detection"]["by_case"]
    stuck = {}
    for v in variants:
        for T in ("650", "620"):
            for Ff in ("670", "876"):
                rows = {kk: vv for kk, vv in sp.items() if kk.startswith(f"{v}|T{T}|") and f"|Ff {Ff}|" in kk}
                if not rows:
                    continue
                stuck[f"{v}|T{T}|{Ff}N"] = {
                    "miss": int(sum(x["miss"] for x in rows.values())), "of": int(sum(x["n"] for x in rows.values())),
                    "alarm_before_failure": int(sum(x["alarm_before_failure"] for x in rows.values())),
                    "t_detect_from_onset_p50_p99_max_s_by_case": {kk.split("|", 2)[2]: r(x["t_detect_from_onset_p50_p99_max_s"], 3)
                                                                   for kk, x in rows.items()},
                    "t_detect_from_true_crossing_p50_p99_max_s_by_case": {kk.split("|", 2)[2]: r(x["t_detect_from_true_crossing_p50_p99_max_s"], 3)
                                                                         for kk, x in rows.items()}}
    summ = {k: v for k, v in F["threshold_summary"].items() if k.split("|")[0] in ("tau20ms", "box10ms")
            and float(k.split("|")[1]) in (600.0, 610.0, 620.0, 630.0, 635.0, 640.0, 650.0, 660.0, 675.0)}
    v = {
        "claim": proposal["claim"],
        "configuration": {
            "script": "m2_fc_thrust v1.1 (GNC review of v1 before its first run; v1 kept in 01-systems-gnc/sim/scripts)",
            "sim": F["sim"], "runs_per_branch": F["runs_per_branch"], "profiles": "A1 (v2.8 relight, planning value "
            f"{F['a1_planning_value_s']:g} s, liquid-line start delay) and B1 {F['b1_height_m']:g} m (sizing height; more "
            "high-thrust time than the 62 m cap); FSW v2.7 provisional (k_est_asc 2); pc2 bases; no throat growth",
            "branches": {"H": "healthy, Pc loop valid, thrust_scale ~ N(1, 0.05) as drawn (ASSUMED)",
                         "L": f"Pc lost from ignition at the top of the open-loop band: thrust_scale = {F['cd_top']} on every run "
                              "(lead's Cd band factor), other draws unchanged",
                         "S": "stuck pintle: synthetic ramps 2.5 / 3.6 kN/s from 500 N (ascent) or 150 N (landing) to 670 / 876 N "
                              "through each healthy run's error terms"},
            "estimate": F["estimate"], "variants": F["variants"], "windows": F["windows"], "hold": F["hold"],
            "error_model": "sim6 IMU model per run: scale factor a_sf and bias a_bz (run draws), white noise (IMU class density) + "
                           "thrust-proportional vibration 2.0 m/s2 at F_max (ASSUMED); FSW mass estimate error m_est_err ~ "
                           "N(0, 0.03) per run (ASSUMED); D_model = the sim6 k_est_asc 2 axial-force model on the estimated vz"},
        "error_3sigma": P(err, "SIM m2_fc_thrust v1.1 (healthy branch, A1 + B1 pooled, fc window, true thrust > 0.15 F_max, "
                               "after 0.1 s of each window segment)",
                          "relative error (F_acc / F - 1) against the true thrust through the same filter (the filter delay is "
                          "listed under latency); the per-run bias is dominated by the ASSUMED 3 % sd mass-estimate error"),
        "latency": P(late, "DERIVED noise-free responses through each filter, 100 Hz frames (all 10 phases) and the 20 ms hold",
                     F["latency_note"]),
        "false_aborts_and_held_maxima": P(fa, "SIM m2_fc_thrust v1.1 (500 runs per branch and profile, seed 101)",
                                          "false abort at T <=> per-run held maximum > T; upper95 = one-sided 95 % bound when "
                                          "none is observed; fc = proposed FC_THRUST valid window"),
        "pc_lost_false_abort_650N_normal_fit": P(gauss650, "DERIVED normal fit of the per-run held maxima (tail extrapolation, "
                                                             "model-dependent)"),
        "stuck_pintle_detection": P(stuck, "SIM synthetic ramps through the 1000 healthy runs' error terms",
                                    F["stuck_pintle_detection"]["note"]),
        "threshold_table": P(summ, "SIM + DERIVED (m2_fc_thrust v1.1 threshold_summary)",
                             "false_L_<profile>: Pc-lost runs with held maximum > T (of 500); _gauss: normal fit; miss_<F>: "
                             "stuck-pintle cases without an abort within 2 s (of n_<F>, all F0 / rate combinations; the 4000 cases "
                             "reuse the 1000 healthy-run error sets, so the effective sample for a bias-driven miss is ~1000); "
                             "t99_onset: worst p99 detection time from the failure onset over the combinations"),
        "threshold_window": F["threshold_window"],
        "mass_estimate_sensitivity_normal_model_tau20ms": P(F["error_decomposition"]["sensitivity_to_mass_estimate_sd_tau20ms"],
                                                            "DERIVED per-frame normal model (m2_fc_thrust v1.1); superseded for "
                                                            "decisions by mass_estimate_sensitivity_mc"),
        "mass_estimate_sensitivity_mc": P(mest_block(M), "SIM m2_fc_thrust_mest v1: paired re-evaluation of the same 2000 flights "
                                          "and 4000 stuck cases with the FC mass-estimate error scaled to sd 0.5-3 % (FC estimate "
                                          "only)", M["note"], method=M["method"], checks=M["checks"]),
        "proposal": proposal["proposal"],
        "unknowns": proposal["unknowns"],
        "refutation": proposal["refutation"],
        "finding": proposal["finding"]}
    return {"v": v, "tag": "SIM (m2_fc_thrust v1.1, sim6/run6 v2.7.1-dev) + DERIVED; mass-estimate error and vibration level "
                           "ASSUMED; not a bench or flight validation",
            "files": {"result": fref("results/fc_thrust/fc_thrust.json"), "figure": fref("results/fc_thrust/fc_thrust_v1.1.png"),
                      "script": fref("sim/scripts/m2_fc_thrust.py"), "plot_script": fref("sim/scripts/m2_fc_thrust_plot.py"),
                      "mass_sensitivity_result": fref("results/fc_thrust/fc_thrust_mest.json"),
                      "mass_sensitivity_figure": fref("results/fc_thrust/fc_thrust_mest_v1.png"),
                      "mass_sensitivity_script": fref("sim/scripts/m2_fc_thrust_mest.py")}}


def mest_block(M):
    """MC sensitivity of the over-thrust check to the FC mass-estimate error (m2_fc_thrust_mest v1), tau 20 ms and frame mean."""
    out = {}
    for sd, bys in M["by_sd"].items():
        row = {}
        for v in ("tau20ms", "box10ms"):
            x = bys[v]
            g = x["grid"]
            bt = x["balanced_threshold_normal_fit"]
            row[v] = {
                "three_sigma_F_ge_450N": r(x["err_F_ge_450N"]["three_sigma"], 4),
                "pc_lost_held_max_p99_max_N": {p: r(q[1:], 1) for p, q in x["held_max_L_p50_p99_max_N"].items()},
                "healthy_held_max_max_N": r(x["held_max_H_max_N"], 1),
                "threshold_zero_false_aborts_N": x["threshold_zero_false_aborts_N"],
                "threshold_zero_670_misses_N": x["threshold_zero_670_misses_N"],
                "window_observed": x["window_observed"],
                "balanced_threshold_normal_fit": {"T_N": bt["T_N"], "p_false_abort_Pc_lost": float(f"{bt['p_false_abort_Pc_lost']:.3g}"),
                                                  "p_miss_670": float(f"{bt['p_miss_670']:.3g}")},
                "at_T_N": {T: {"pc_lost_false_aborts_of_1000": g[T]["false_L_pooled"],
                               "healthy_false_aborts_of_1000": g[T]["false_H_pooled"],
                               "pc_lost_false_abort_normal_fit": float(f"{g[T]['false_L_gauss_max']:.3g}"),
                               "missed_670_of_4000": g[T]["miss_670"], "missed_670_normal_fit": float(f"{g[T]['miss_670_gauss']:.3g}"),
                               "missed_876_of_4000": g[T]["miss_876"], "early_alarms": g[T]["early_670"] + g[T]["early_876"]}
                           for T in ("620", "625", "630", "635", "640", "650")},
                "detect_p50_p99_max_s_at_650N": {k.split("|")[1]: r(t, 3) for k, t in x["detection_time_from_onset_p50_p99_max_s"].items()
                                                 if k.startswith("T650|")}}
        out[sd] = row
    return out


TAIL_CRIT = 1.0e-4   # GNC criterion (ASSUMED, the lead may set another): normal-fit tail per Pc-lost flight / per 670 N case


def requirement_sd(M, v="tau20ms", T="650"):
    """(requirement, edge): the largest studied mass-error sd at which T shows no false abort (Pc lost, healthy), no stuck miss
    and no early alarm in the Monte Carlo AND normal-fit tails (Pc-lost false abort, 670 N miss) <= TAIL_CRIT; and the largest
    sd that passes the Monte Carlo part alone (the edge)."""
    keys = ("false_L_pooled", "false_H_pooled", "miss_670", "early_670", "miss_876", "early_876")
    ok = [float(sd) for sd, b in M["by_sd"].items() if all(b[v]["grid"][T][k] == 0 for k in keys)]
    okt = [x for x in ok if M["by_sd"][f"{x:g}"][v]["grid"][T]["false_L_gauss_max"] <= TAIL_CRIT
           and M["by_sd"][f"{x:g}"][v]["grid"][T]["miss_670_gauss"] <= TAIL_CRIT]
    return (max(okt) if okt else None), (max(ok) if ok else None)


def band_top_tolerance(M, sd, v="tau20ms", T=650.0, cd_top=1.143):
    """DERIVED: Pc-lost band top at which the highest Pc-lost held maximum would reach T (held maxima scaled linearly)."""
    hm = max(q[2] for q in M["by_sd"][sd][v]["held_max_L_p50_p99_max_N"].values())
    return cd_top * T / hm


def fc_proposal(F, M):
    """GNC threshold proposal from the computed numbers (criteria stated in the text)."""
    ts = F["threshold_summary"]
    n = F["runs_per_branch"]
    v = "tau20ms"
    t650 = ts[f"{v}|650"]
    b650 = ts["box10ms|650"]
    raw650 = ts["raw|650"]
    eb = F["error_3sigma_healthy_pooled"]
    dec = F["error_decomposition"]["by_variant"]
    br = F["branches"]
    sp = F["stuck_pintle_detection"]["by_case"]
    hmL = {p: br[f"{p}|L"][v]["held_max_fc_p50_p99_max_N"] for p in ("A1", "B1")}
    nL = sum(br[f"{p}|L"][v]["false_aborts"]["fc|650"]["n"] for p in ("A1", "B1"))
    ub = 1.0 - 0.05 ** (1.0 / (2 * n))
    lat = F["latency"][v]
    latraw = F["latency"]["raw"]

    def tc(F0, Ff, rate, key="t_detect_from_onset_p50_p99_max_s"):
        return sp[f"{v}|T650|F0 {F0}|Ff {Ff}|rate {rate}"][key]
    t876_asc = max(tc(500, 876, rt)[1] for rt in (2500, 3600))
    t876_land = max(tc(150, 876, rt)[1] for rt in (2500, 3600))
    t876_max = max(tc(F0, 876, rt)[2] for F0 in (500, 150) for rt in (2500, 3600))
    t876_cross = max(tc(F0, 876, rt, "t_detect_from_true_crossing_p50_p99_max_s")[2] for F0 in (500, 150) for rt in (2500, 3600))
    t670_p99 = max(tc(F0, 670, rt)[1] for F0 in (500, 150) for rt in (2500, 3600))
    miss670 = t650["miss_670"] / t650["n_670"]
    g3 = M["by_sd"]["0.03"][v]["grid"]
    req, edge = requirement_sd(M)
    rq = M["by_sd"][f"{req:g}"][v] if req else None
    re_ = M["by_sd"][f"{edge:g}"][v] if edge else None
    tole = band_top_tolerance(M, f"{edge:g}") if edge else None
    tol3 = band_top_tolerance(M, "0.03")
    tolq = band_top_tolerance(M, f"{req:g}") if req else None
    bal_q = rq["balanced_threshold_normal_fit"] if req else None
    tol_bal = (F["cd_top"] * bal_q["T_N"] / max(q[2] for q in rq["held_max_L_p50_p99_max_N"].values())) if req else None
    claim = (f"FC_THRUST estimate (tau 20 ms, 100 Hz, 0.1 N): healthy 3-sigma error {100 * eb[v]['three_sigma_F_ge_450N']:.1f} % at "
             f"thrust >= 450 N ({100 * eb[v]['three_sigma']:.1f} % over all burning frames), of which "
             f"{100 * max(-dec[v]['rest_p0135_p99865_F_ge_450N'][0], dec[v]['rest_p0135_p99865_F_ge_450N'][1]):.1f} % without the "
             f"ASSUMED 3 % sd mass-estimate error; raw point samples {100 * eb['raw']['three_sigma_F_ge_450N']:.1f} %. Latency (FC side): "
             f"{1e3 * lat['ramp_lag_s']:.0f} ms ramp lag, step 50 % {1e3 * lat['step_delay_50pct_mean_max_s'][0]:.1f} ms mean / "
             f"{1e3 * lat['step_delay_50pct_mean_max_s'][1]:.0f} ms max incl. 0-9 ms frame staleness, abort decision "
             f"{1e3 * lat['abort_decision_delay_step_to_2T_mean_max_s'][0]:.1f} ms mean / "
             f"{1e3 * lat['abort_decision_delay_step_to_2T_mean_max_s'][1]:.0f} ms max after a large step (raw "
             f"{1e3 * latraw['abort_decision_delay_step_to_2T_mean_max_s'][0]:.1f} / "
             f"{1e3 * latraw['abort_decision_delay_step_to_2T_mean_max_s'][1]:.0f} ms); CAN, ECU and IMU filter delays not included. "
             f"Pc lost at the 1.143 band top: {nL} false aborts at 650 N / 20 ms in {2 * n} flights (upper 95 % {100 * ub:.2f} % per "
             f"flight; raw samples {raw650['false_L_A1'] + raw650['false_L_B1']}); held maxima p99/max {hmL['A1'][1]:.0f}/"
             f"{hmL['A1'][2]:.0f} N (A1), {hmL['B1'][1]:.0f}/{hmL['B1'][2]:.0f} N (B1). Stuck full-stroke pintle at 650 N: 876 N "
             f"detected in {t650['n_876'] - t650['miss_876']}/{t650['n_876']} cases, p99 {t876_asc:.3f} s from the onset at 500 N and "
             f"{t876_land:.3f} s from 150 N (max {t876_max:.3f} s; <= {t876_cross:.3f} s after the true thrust crosses 650 N); 670 N "
             f"missed (no abort within 2 s) in {t650['miss_670']}/{t650['n_670']} cases ({100 * miss670:.1f} %) with the ASSUMED 3 % "
             f"mass error, detected ones p99 <= {t670_p99:.2f} s" +
             (f"; with an FC mass-estimate error <= {100 * req:g} % (1 sigma) 650 N misses none ({rq['grid']['650']['miss_670']}/"
              f"{t650['n_670']}, normal-fit tail {rq['grid']['650']['miss_670_gauss']:.0e}) with "
              f"{rq['grid']['650']['false_L_pooled']}/{2 * n} Pc-lost false aborts ({100 * edge:g} % is the edge: 0 missed, fitted "
              f"tail {re_['grid']['650']['miss_670_gauss']:.0e}; 2 %: {M['by_sd']['0.02'][v]['grid']['650']['miss_670']}/"
              f"{t650['n_670']} missed)" if req else ""))
    proposal = {
        "threshold": P("650 N held 20 ms (3 consecutive 100 Hz frames) CONFIRMED, on the tau 20 ms (or frame-mean) estimate",
                       "DESIGN GNC proposal on SIM evidence",
                       f"zero Pc-lost false aborts in {2 * n} flights (normal fit of the held maxima <= "
                       f"{max(g3['650']['false_L_gauss_max'], 0):.1g} per flight), {650 - max(hmL['A1'][2], hmL['B1'][2]):.0f} N above the "
                       f"highest held maximum; the margin tolerates a Pc-lost band top up to {tol3:.3f} (DERIVED, held maxima scaled "
                       "linearly) instead of the ASSUMED 1.143. It does NOT cover the low end of the stuck range with the ASSUMED 3 % "
                       f"mass error ({100 * miss670:.1f} % of the 670 N cases missed): see mass_estimate_requirement"),
        "mass_estimate_requirement": P(
            (f"FC mass-estimate error <= {100 * req:g} % (1 sigma) over the burn (GNC DESIGN requirement on the FSW mass estimate: pad "
             "weighing of the loaded vehicle + consumption model; verification method and data still open)") if req else
            "no studied mass-estimate accuracy closes the 670 N gap at 650 N",
            "DESIGN GNC proposal on SIM evidence (m2_fc_thrust_mest v1, paired re-evaluation of the same 2000 flights)",
            (f"with {100 * req:g} %: 650 N gives {rq['grid']['650']['false_L_pooled']}/{2 * n} Pc-lost and "
             f"{rq['grid']['650']['false_H_pooled']}/{2 * n} healthy false aborts (normal fit "
             f"{rq['grid']['650']['false_L_gauss_max']:.1g} per flight), 670 N missed {rq['grid']['650']['miss_670']}/"
             f"{t650['n_670']} (normal fit of the held level {rq['grid']['650']['miss_670_gauss']:.1g} per case; the 4000 cases "
             "reuse 1000 error sets, effective sample ~1000), 876 N missed "
             f"{rq['grid']['650']['miss_876']}; the margin then tolerates a Pc-lost band top up to {tolq:.3f}. Criterion: no "
             f"false abort and no miss in the Monte Carlo and normal-fit tails <= {TAIL_CRIT:g} (GNC choice). Edge: "
             f"{100 * edge:g} % still shows {re_['grid']['650']['miss_670']}/{t650['n_670']} misses but a fitted tail of "
             f"{re_['grid']['650']['miss_670_gauss']:.1g} (band top up to {tole:.3f}); 2 %: "
             f"{M['by_sd']['0.02'][v]['grid']['650']['miss_670']}/{t650['n_670']} missed; 3 % (ASSUMED today): "
             f"{M['by_sd']['0.03'][v]['grid']['650']['miss_670']}/{t650['n_670']}. Studied grid 0.5 / 1 / 1.5 / 2 / 3 %; the "
             "flights keep their own FSW mass error (the scaling acts on the FC estimate only)") if req else None),
        "lower_thresholds_not_proposed": P(
            {"at_ASSUMED_3pct": {T: {"pc_lost_false_aborts_of_1000": g3[T]["false_L_pooled"], "missed_670_of_4000": g3[T]["miss_670"]}
                                 for T in ("620", "625", "630", "635", "640", "650")},
             "balanced_at_requirement": ({"T_N": bal_q["T_N"], "p_false_abort_Pc_lost_normal_fit": bal_q["p_false_abort_Pc_lost"],
                                          "p_miss_670_normal_fit": bal_q["p_miss_670"],
                                          "band_top_tolerated": float(round(tol_bal, 3))} if req else None)},
            "SIM + DERIVED",
            "with the ASSUMED 3 % mass error a lower threshold only trades 670 N misses for Pc-lost false aborts (no threshold "
            "clears both in the Monte Carlo); with the required mass estimate a lower, balanced threshold would also clear both but "
            "spends the margin that covers the ASSUMED 1.143 band top; research option once Combustion / Electronics confirm the "
            "open-loop band"),
        "filter": P("first-order tau 20 ms at the IMU rate (or the mean of the frame's samples); NOT the raw point sample",
                    "DESIGN GNC proposal on SIM evidence",
                    f"raw point samples carry the vibration noise (ASSUMED 2 m/s2 at F_max): {raw650['false_L_A1'] + raw650['false_L_B1']} "
                    f"Pc-lost false aborts at 650 N in {2 * n} flights (and {raw650['false_H_A1'] + raw650['false_H_B1']} healthy) vs "
                    f"{t650['false_L_A1'] + t650['false_L_B1']} with tau 20 ms and {b650['false_L_A1'] + b650['false_L_B1']} with the "
                    "frame mean; the frame mean detects about 15 ms sooner with slightly more noise (see threshold_table)"),
        "valid_flag": P("FC sets FC_THRUST valid only while airborne (h_est > 1 m, before touchdown), the engine is lit and the drogue "
                        "is not attached (the fc window); the ECU treats invalid as flag-only (lead rule)", "DESIGN GNC proposal",
                        "in sim6 the air window (any engine state) and the fc window give the same held maxima (the maximum always "
                        "occurs while lit: 2000/2000 flights; A1 coast and drogue readings <= 462 N); the fc window is proposed for "
                        "loads sim6 does not model: drogue snatch (quasi-steady drogue model), touchdown impact before the touchdown "
                        "flag, ground reaction on the pad (where F_acc reads the weight, not the thrust)"),
        "decision_owner": "lead (threshold, mass-estimate requirement); Electronics (ECU implementation, CAN timing, whether the "
                          "check also runs with Pc valid); GNC (FSW mass estimate, FC_THRUST frame); Combustion (open-loop band top, "
                          "stuck-pintle range)"}
    unknowns = [
        "FSW mass-estimate error: ASSUMED N(0, 3 %) per run (run6 draw); it sets the per-flight bias and the 670 N miss rate; the "
        "FC mass estimator is not specified yet (GNC)",
        "vibration at the IMU during the burn: ASSUMED 2.0 m/s2 sd at F_max; it sets the raw-sample noise (measure on DC-C / DC-D)",
        "IMU part: internal digital filter and sample delay not known (DATASHEET needed); not in the latency figures",
        "CAN transport, FC task and ECU check timing (Electronics): not in the latency figures",
        "airframe axial dynamics between the engine and the IMU (rigid body in sim6): ringing on the thrust transients not modelled",
        "Pc-lost thrust band: the 1.143 Cd band factor is the lead's ASSUMED value; 650 N tolerates up to "
        f"{tol3:.3f} with the ASSUMED 3 % mass error (DERIVED)",
        "throat growth with Pc lost (not flown in the L branch)",
        "stuck-pintle thrust history: synthetic ramps (2.5 / 3.6 kN/s, 670 / 876 N from the lead relay) through the healthy runs' "
        "error terms, not a 6-DOF failure flight; the vehicle response to a missed 670 N pintle (other monitors) is not evaluated",
        "the mass-estimate sensitivity scales the error in the FC estimate only (the flights keep their FSW mass error)",
        "mass-estimate error model: a constant fraction per run (run6 draw); a pad-weighed, flow-integrating estimate has an error "
        "that grows through the burn (v3 open item on k_est_asc 2); the requirement applies at every instant of the burn",
        "whether the ECU evaluates FC_THRUST only with Pc lost or always (healthy false aborts are 0/1000 at >= 610 N with tau "
        "20 ms, so 650 N costs nothing either way)"]
    refutation = [
        "bench (DC-C tether / DC-D static fire with a load cell): F_acc (as implemented on the FC) vs load-cell thrust at >= 450 N "
        "exceeds the 3-sigma band published here -> error model refuted, threshold re-derived",
        "measured IMU vibration at F_max above 2.0 m/s2 sd -> re-run (raw and filtered noise scale with it)",
        "any false over-thrust abort in a healthy or Pc-lost bench run at <= 571.5 N true thrust -> threshold or filter wrong",
        "a commanded full-stroke pintle on the bench (stand only) not aborted within the published detection time -> refuted",
        (f"FC mass estimate verified worse than {100 * req:g} % (1 sigma) -> the 670 N coverage claim at 650 N is void "
         "(the 3 % figures apply)") if req else "no mass-estimate requirement derived"]
    finding = (claim + ". Proposal: keep 650 N / 20 ms with the tau 20 ms estimate and the fc valid window" +
               (f", and require the FC mass estimate to <= {100 * req:g} % (1 sigma) so that 650 N also covers the 670 N end of the "
                "stuck range; lower thresholds are not proposed while the 1.143 band top is ASSUMED" if req else
                "; the 670 N end of the stuck range stays uncovered"))
    short = (f"650 N / 20 ms confirmed on the tau 20 ms estimate: {nL}/{2 * n} Pc-lost false aborts, 876 N always detected "
             f"(p99 <= {max(t876_asc, t876_land):.2f} s), 670 N missed {100 * miss670:.1f} % with the ASSUMED 3 % mass error" +
             (f", 0/{t650['n_670']} with an FC mass estimate <= {100 * req:g} % (proposed requirement)" if req else ""))
    return dict(claim=claim, short=short, proposal=proposal, unknowns=unknowns, refutation=refutation, finding=finding,
                requirement_sd=req)


# ------------------------------------------------------------------------------------------------- Combustion data items
def coast_section(C):
    d = C["dispersed"]
    pick = ("coast_up_s", "descent_s", "window_s", "fz_seat_coast_up_mean_mps2", "fz_seat_coast_up_min_mps2", "fz_seat_min_mps2",
            "time_fz_below_0g_s", "fz_seat_descent_mean_mps2", "fz_seat_descent_min_mps2", "descent_time_fz_below_0_s",
            "fz_seat_last_1s_mean_mps2", "settled_before_relight_s", "above_half_g_before_relight_s", "adverse_impulse_mps",
            "flat_seat_max_mps2", "lateral_angle_max_deg_when_fz_gt_0p1g", "rate_max_dps", "seat_minus_cg_fz_maxabs_mps2",
            "mv_minus_seat_fz_maxabs_mps2")
    stats = {k: {kk: r(vv, 3) for kk, vv in d[k].items() if kk in ("p01", "p50", "p99", "min", "max")} for k in pick}
    nom = {k: r(C["nominal"][k], 3) for k in pick if C["nominal"].get(k) is not None}
    ext = {lab: {k: (r(x, 3) if isinstance(x, float) else x) for k, x in e.items()
                 if k in ("run", "success", "wind_mps", "drogue_f", "fz_seat_min_mps2", "t_fz_seat_min_s", "t_meco_s", "t_apogee_s",
                          "t_relight_cmd_s", "fz_seat_descent_mean_mps2", "fz_seat_descent_min_mps2", "time_fz_below_0g_s",
                          "settled_before_relight_s", "rate_max_dps")} for lab, e in C["extreme_runs"].items()}
    v = {"request": "lead 2026-10-13 (Combustion): A1 body-axis acceleration from MECO to RELIGHT, nominal and dispersed "
                    "(p01/p50/p99 envelope, plus the min-accel run), to judge whether vapour in the MV-to-seat segment vents "
                    "toward the tank or stays trapped at the engine end during the coast and drogue descent (in flight retained "
                    "vapour <= 19 cm3)",
         "configuration": C["configuration"], "mc_case": C["mc_case"], "n_runs": C["n_runs"], "stations": C["stations"],
         "definitions": C["definitions"], "nominal": nom, "dispersed_p01_p50_p99_min_max": stats, "extreme_runs": ext,
         "checks": C["checks"], "limitations": C["limitations"],
         "summary": (f"coast up (tail-off end to apogee) {d['coast_up_s']['p50']:.2f} s [p01 {d['coast_up_s']['p01']:.2f}, p99 "
                     f"{d['coast_up_s']['p99']:.2f}] with f_z < 0 (vapour driven toward the seat): mean "
                     f"{d['fz_seat_coast_up_mean_mps2']['p50']:.2f} m/s2, minimum {d['fz_seat_coast_up_min_mps2']['p50']:.2f} m/s2 "
                     f"(p01 {d['fz_seat_coast_up_min_mps2']['p01']:.2f}) just after the tail-off; drogue descent "
                     f"{d['descent_s']['p50']:.1f} s, mean {d['fz_seat_descent_mean_mps2']['p50']:.2f} m/s2, last second "
                     f"{d['fz_seat_last_1s_mean_mps2']['p50']:.2f} m/s2; drogue turnover at apogee: f_z <= 0 for "
                     f"{d['descent_time_fz_below_0_s']['p50']:.2f} s (max {d['descent_time_fz_below_0_s']['max']:.2f} s), dips to "
                     f"{d['fz_seat_descent_min_mps2']['min']:.2f} m/s2, rates up to {d['rate_max_dps']['max']:.0f} deg/s "
                     "(quasi-steady drogue model: indicative); continuously f_z > 0 before the relight command "
                     f"{d['settled_before_relight_s']['p50']:.1f} s [p01 {d['settled_before_relight_s']['p01']:.1f}, min "
                     f"{d['settled_before_relight_s']['min']:.1f}]. GNC makes no venting claim: the judgement and the 19 cm3 "
                     "requirement are Combustion's"),
         "files": {k: fref(f"results/a1_coast_accel/{os.path.basename(f)}") for k, f in
                   (("summary", "coast_accel_a1_v1.json"), ("envelope_meco", "coast_accel_a1_envelope_meco_v1.csv"),
                    ("envelope_relight", "coast_accel_a1_envelope_relight_v1.csv"), ("runs", "coast_accel_a1_runs_v1.csv"),
                    ("series", "coast_accel_a1_series_v1.csv"), ("figure", "coast_accel_a1_v1.png"))}}
    v["files"]["script"] = fref("sim/scripts/m2_coast_accel_a1.py")
    return {"v": v, "tag": "SIM (m2_coast_accel_a1 v1, sim6/run6 v2.7.1-dev, 500 runs seed 101) + stations DERIVED/ASSUMED"}


def b62_block(B):
    recs = []
    for x in B["records"]:
        recs.append({"name": x["name"], "file": x["file"], "sha256": x["sha256"], "mc_case": x["mc_case"], "run_index": x["run_index"],
                     "burn_time_thrust_on_s": r(x["burn_time_s"], 2), "engine_on_counter_s": r(x["engine_on_counter_s"], 2),
                     "impulse_Ns": r(x["total_impulse_Ns"], 0), "n2o_burned_kg": r(x["n2o_burned_kg"], 3), "success": x["success"],
                     "vs_85m_sizing_cycle": x["vs_85m_sizing_cycle"]})
    ch = {k: {"runs_reproducing_mc_row": c["runs_reproducing_mc_row"], "n_runs": c["n_runs"],
              "counter_p50_p99_max_s": r(c["counter_p50_p99_max_s"], 2), "thrust_on_p50_p99_max_s": r(c["thrust_on_p50_p99_max_s"], 2),
              "P": c["success_rate"], "same_run_by_counter_and_thrust_on": {k2: v2["same_run"] for k2, v2 in c["selection"].items()},
              "mc_csv_hub": c.get("mc_csv_hub")} for k, c in B["selection_checks"].items()}
    return {"index": fref("duty_cycles/duty_cycles_records_b1_62m_v3.1.json"), "kind": "records (not sizing cases)",
            "request": B["request"], "lead_decision": B["lead_decision"], "records": recs, "cases": ch,
            "note": B["note"] + "; for Combustion's corner a x1.5 / n 0.35 (burn-through at 17.0-17.8 s, Combustion v2.4): 7.2 % of "
                                "the 62 m runs burn longer than 17.0 s and 2.0-2.4 % longer than 17.8 s (engine-on counter)",
            "tag": "SIM (m2_dc_b1_62m_record v1)"}


def ttank_section(T):
    cs = {k: {kk: (r(vv, 3) if isinstance(vv, (float, list)) else vv) for kk, vv in c.items()
              if kk in ("n", "n_above_24C", "P_above_24C", "P_in_arm_range", "P_all", "fisher_exact_p", "counter_p99_all_s",
                        "counter_p99_in_range_s", "spearman_T0_counter", "csv_hub")} for k, c in T["cases"].items() if isinstance(c, dict)}
    return {"v": {"arm_range_C": T["arm_range_C"], "drawn_range_C": T["drawn_range_C"], "draw": T["draw"], "cases": cs,
                  "duty_cycle_runs_above_24C": T["duty_cycle_runs_above_24C"],
                  "finding": ("44 of 500 runs per case are drawn above 24 C. Small, and not conservative for every output: the "
                              "hot slice does not succeed less (Fisher p >= 0.43), B1 hot runs burn slightly shorter (Spearman "
                              "-0.09 to -0.11), the in-range success rate differs by <= 0.3 points and the in-range B1 p99 "
                              "engine-on counter is 0.0-0.2 s higher; every published duty-cycle file stays at or above the "
                              "in-range p99; one published cycle was drawn above 24 C (DC-A1_full_flight_disp_p99_kest2_tg711_v3)"),
                  "lead_decision": "recorded as a small difference, no re-run (lead 2026-10-13); the next GNC baseline draws "
                                   "U(15, 24) C",
                  "file": fref("results/ttank_arm_check/ttank_arm_check_v1.json")},
            "tag": "SIM re-analysis of the published Monte Carlo CSVs (m2_ttank_arm_check v1); REQ lead decisions 2026-10-13"}


# ------------------------------------------------------------------------------------------------- vapour-start fallback
def seg44_section(D):
    """relight_vapour_start_fallback from m2_relight_seg44 v1.2 (relight_seg44.json)."""
    po = D["pooled"]
    ab = D["ecu_abort_probability"]
    tb = D["tables"]
    dec = D["decision"]["by_state"]
    pc = D["plan_curve"]

    def q(st):
        v = tb["tables_E0E2_quantiles_5pct_s"][st]
        return {"min": r(v[0]), "median": r(v[10]), "p95": r(v[19]), "max": r(v[20])}

    def pooled(k):
        x = po[k]
        o = {"P": r(x["P"], 4), "ci95": r(x["ci95"], 4), "n": x["n"]}
        if "lost" in x:
            o.update(vs_v3_baseline_paired={"lost": x["lost"], "gained": x["gained"], "p_exact": float("%.3g" % x["p_exact"]),
                                            "dP": r(x["dP"], 4)})
        return o

    per_base = {}
    for base, bb in D["by_base"].items():
        per_base[base] = {}
        for k, x in bb.items():
            e = {"P": r(x["P"], 3), "ci95": r(x["ci95"], 3),
                 "light_minus_plan_s_min_p50_max": r(x["light_minus_plan_s_min_p50_max"], 2),
                 "engine_on_counter_p99_s": r(x["engine_on_counter_p50_p99_max_s"][1], 2),
                 "runs_over_a1_sizing_counter": x["engine_on_counter_over_a1_sizing"]["n_over"],
                 "usable_left_p01_kg": r(x["usable_left_p01_kg"], 3), "fail_modes": x["fail_modes"]}
            if "vs_baseline_paired" in x:
                vp = x["vs_baseline_paired"]
                e["vs_v3_baseline_paired"] = {"lost": vp["lost"], "gained": vp["gained"], "p_exact": float("%.3g" % vp["p_exact"])}
                e["pairing_check"] = x["pairing_check"]["same_uniform_start_draw"] and x["pairing_check"]["same_wind_draw"]
            per_base[base][k] = e
    curve = {st: {pl: {"P": r(v["P"], 3), "ci95": r(v["ci95"], 3)} for pl, v in cc.items()} for st, cc in pc["curve"].items()}
    paired = {k: {"lost": v["lost"], "gained": v["gained"], "p_exact": float("%.3g" % v["p_exact"]), "dP": r(v["dP"], 4)}
              for k, v in pc["paired_vs_state_reference"].items()}
    best = [{"p_liquid": x["p_liquid"], "best_plan_s": x["best_plan_s"], "expected_P": r(x["P_best"], 4)}
            for x in pc["expected_P_best_plan"]]
    dtab = {st: {"abort_W0.65": r(x["abort_W065"], 3), "abort_W1.05": r(x["abort_W105"], 3),
                 "break_even_p_liquid_v3_vs_b": r(x["break_even_p_liquid_v3_vs_b"], 3),
                 "table": [{k: r(v, 4) for k, v in row.items()} for row in x["table"]]} for st, x in dec.items()}
    n_over = {k: [D["by_base"][b][k]["engine_on_counter_over_a1_sizing"]["n_over"] for b in D["by_base"] if k in D["by_base"][b]]
              for k in ("baseline", "liq_p1.21", "vap44F_p1.21", "vap34F_p1.21", "vap44F_p0.81")}
    liq121, vap121, vap081 = po["liq_p1.21"], po["vap44F_p1.21"], po["vap44F_p0.81"]
    finding = (
        f"Vapour-start fallback (b) (every relight planned at 0.16 + 1.05 = 1.21 s, W 1.05 s), paired on the four A1 bases "
        f"(2000 runs per state, v3 baseline P {po['baseline']['P']:.4f}): 44 cm3 vapour-full start P {vap121['P']:.4f} "
        f"(-{vap121['lost']}/+{vap121['gained']}, p {vap121['p_exact']:.2g}: lights 0.08-0.44 s before the plan, closer than "
        f"the v3 liquid start lights before 0.81 s); 34 cm3 P {po['vap34F_p1.21']['P']:.4f} (n.s.); 0.69 s purge (2 bases) "
        f"0.990 / 0.992; a LIQUID line planned at 1.21 s P {liq121['P']:.4f} (-{liq121['lost']}/+{liq121['gained']}, p "
        f"{liq121['p_exact']:.2g}; lights 0.71-1.08 s early; engine-on p99 8.65-8.80 s against the 8.26 s A1 sizing cycle, "
        f"{min(n_over['liq_p1.21'])}-{max(n_over['liq_p1.21'])}/500 runs over it vs "
        f"{min(n_over['baseline'])}-{max(n_over['baseline'])} in v3). Under v3 (W 0.65 s) Combustion's tables abort "
        f"{100 * ab['vap44F']['W0.65']:.0f} % of 44 cm3 vapour-full relights ({100 * ab['vap34F']['W0.65']:.0f} % at 34 cm3, "
        f"DERIVED); with an aborted relight counted as a lost landing (ASSUMED), (b) beats v3 unless P(liquid at RELIGHT) > "
        f"{dec['vap44F']['break_even_p_liquid_v3_vs_b']:.3f} (44 cm3) / {dec['vap34F']['break_even_p_liquid_v3_vs_b']:.3f} "
        f"(34 cm3). GNC addition: the window and the planning value are separable. With W 1.05 s, a vapour-full start planned "
        f"at 0.81 s lights late (+0.15 s median) and P falls to {vap081['P']:.4f}; the planning-value sweep (A1_none + A1J_none, "
        f"1000 paired runs per point) gives liquid 0.990 / 0.989 / 0.975 / 0.966 / 0.953 and vapour-full 0.954 / 0.979 / 0.993 "
        f"/ 0.993 / 0.995 at 0.81 / 0.91 / 1.01 / 1.11 / 1.21 s: 0.91 s is the maximin plan (liquid -7/+6 vs 0.81 s, n.s.; "
        f"vapour-full -16/+0 vs 1.21 s, p 3e-5).")
    proposal = {
        "v": [
            "Do not plan every relight at 1.21 s while the segment state at RELIGHT is unknown: a liquid line then loses ~3 points "
            "and burns past the A1 sizing cycle.",
            "Any relight that may start with a vapour-full 44 cm3 segment needs an ECU window W >= 1.00 s from E1 (Combustion: "
            "0 % abort at W >= 1.00 s, 100 % at 0.65 s); this is set by the ECU independently of the FC planning value.",
            "With W 1.05 s: planning value 0.91 s while the state is unknown (maximin: >= 0.979 in both states); 0.81 s if "
            "Combustion's buoyant-venting check or fix (a) / (d) keeps the segment liquid; 1.21 s (or 1.01-1.11 s, equal within "
            "0.2 points) only if a vapour-full segment is certain.",
            "Preferred if the state is observable before RELIGHT: a state-dependent plan (0.81 s liquid, 1.21 s vapour, e.g. "
            "the Electronics PRIMED/UNPRIMED flag extended with a VAPOUR state from the segment TC / P_feed): 0.987-0.990 on "
            "liquid and 0.994-0.995 on vapour-full (SIM)."],
        "tag": "GNC PROPOSAL for the lead (SIM evidence; the vapour state at RELIGHT and the abort path are not modelled)"}
    return {"v": {
        "request": D["request"],
        "configuration": {
            "sim": D["sim"], "fsw": "v2.7 PROVISIONAL (k_est_asc 2, Pc ratchet), relight design v2.8 (torch gate 0.16 s)",
            "iface": D["iface"], "bases": ["A1_none", "A1_pc", "A1J_none", "A1J_pc"], "load_kg": 2.0, "runs_per_case": 500,
            "cases": 36, "seeds": {"draws": 101, "start_delay_generator": 20261018, "pairing": "run by run with the v3 "
                                   "baseline v28_liq_p0.81 (same uniform start-delay draw and same wind per run, checked)"},
            "start_delay_model": "sim6 lights at the drawn E0->E2 delay after the relight command (no ECU deadline model); "
                                 "thrust rise by its own loop"},
        "tables_E0E2_s": {st: q(st) for st in ("liq", "vap34F", "vap44F", "vap44F69")},
        "table_sources": {
            "vap44F": {"file": tb["seg44_file"]["path"], "sha256_16": tb["seg44_file"]["sha256_16"], "in_hub": tb["seg44_file"]["in_hub"],
                       "case": tb["seg44_file"]["case"], "segment_cm3": tb["seg44_file"]["segment_cm3"],
                       "t_purge_segment_s": r(tb["seg44_file"]["t_purge_segment_s"], 4),
                       "check": f"equals the v2p4 full-vapour table + {tb['check_seg44_equals_v2p4_full_shifted']['shift_s']:.4f} s "
                                f"within {1000 * tb['check_seg44_equals_v2p4_full_shifted']['max_abs_diff_s']:.2f} ms (the lead's "
                                "alternative construction at the 0.64 s end of the purge range)"},
            "vap34F": "v2p4 full-vapour table + (0.6368 x 34 / 44 - 0.31) s (DERIVED, Combustion's linear volume scaling)",
            "vap44F69": "v2p4 full-vapour table + (0.69 - 0.31) s (lead's alternative at the 0.69 s purge end; ASSUMED shift)",
            "liq": "v2p4 liquid-line table of gnc.json v3",
            "max_below_1.21_s": tb["max_below_plan_fb"]},
        "ecu_abort_probability_from_E1": {k: v for k, v in ab.items() if k != "source"},
        "ecu_abort_sources": ab["source"],
        "e0_referenced_share_after_0.81_s": {k: r(v, 3) for k, v in tb["share_E0E2_after_0p81s_from_E0"].items()},
        "pooled_four_bases": {k: pooled(k) for k in po},
        "per_base": per_base,
        "bprime_vs_b_paired": {k: {kk: (float("%.3g" % vv) if kk == "p_exact" else vv) for kk, vv in v.items()}
                               for k, v in D["bprime_vs_b_paired"].items()},
        "decision_table_vs_p_liquid": dtab,
        "planning_value_sweep_two_bases": {"curve": curve, "paired_vs_state_reference": paired, "expected_P_best_plan": best,
                                           "maximin_plan_s": pc["maximin_plan_s"], "W_s": pc["W_s"], "note": pc["note"]},
        "a1_sizing_counter_s": r(D["a1_sizing_counter_s"], 3),
        "runs_over_a1_sizing_counter_by_base": n_over,
        "context_v28_published": {k: {b: r(x["P"], 3) for b, x in v.items()} for k, v in D["context_v28"].items()},
        "finding": finding,
        "proposal": proposal,
        "unknowns": [
            "the vapour state at RELIGHT (Combustion's buoyant-venting check pending): the expected P of every option depends on it",
            "the abort path: an aborted relight is counted as a lost landing (ASSUMED); retry or drogue landing not modelled",
            "W 1.05 s on a liquid line admits N2O up to 0.40 s longer before the abort of a failed ignition (hard start / "
            "accumulation: Combustion)",
            "engine-on time above the A1 sizing cycle when a liquid line is planned late (thermal / erosion duty: Combustion, "
            "Mechanical)",
            "the start-latency distributions are Combustion's ASSUMED models (start_latency_v2p4, no hot-fire data); 34 cm3 abort "
            "probability interpolated (DERIVED); 0.69 s purge sensitivity on two bases only",
            "the early / late-light sensitivity belongs to FSW v2.7's relight guidance; a guidance that re-plans at the actual "
            "light time could change the trade (research item, not done)",
            "T_tank drawn U(15, 25) C as in v3 (next baseline U(15, 24) C)"],
        "refutation": [
            "Combustion shows the segment re-primes before T_fire (vapour <= 19 cm3): v3 (0.81 s, W 0.65 s) stands, (b) is not needed",
            "cold-flow / hot-fire relight tests give E1->E2 > 1.0 s for a vapour-full segment: W 1.05 s is not enough",
            "a re-planning landing guidance removes the early/late-light loss: the planning-value trade is re-run"],
        "not_modelled": D["not_modelled"],
        "files": {"results": fref("results/relight_seg44/relight_seg44.json"),
                  "figure": fref("results/relight_seg44/relight_seg44_v1.png"),
                  "monte_carlo": f"{STG}/results/relight_seg44/mc/ (36 gzipped run CSVs and case files)",
                  "scripts": [f"{STG}/sim/scripts/m2_relight_seg44.py", f"{STG}/sim/scripts/m2_relight_seg44_plot.py"]}},
        "tag": "SIM (sim6 6-DOF Monte Carlo, paired) on Combustion's ASSUMED start-latency tables; DERIVED decision table; "
               "REQ lead request 2026-10-13"}


# ------------------------------------------------------------------------------------------------- main
def main():
    raw = open(BASE, "rb").read()
    h = hashlib.sha256(raw).hexdigest()
    if not h.startswith(BASE_SHA16):
        raise SystemExit(f"interfaces/gnc.json is not the published v3 ({h[:16]} != {BASE_SHA16})")
    g = copy.deepcopy(json.loads(raw))
    F = jl(f"{O}/fc_thrust/fc_thrust.json")
    M = jl(f"{O}/fc_thrust/fc_thrust_mest.json")
    C = jl(f"{O}/coast_accel_a1/coast_accel_a1_v1.json")
    B = jl(f"{O}/duty_cycles_v3_1/duty_cycles_records_b1_62m_v3.1.json")
    T = jl(f"{O}/ttank_arm_check/ttank_arm_check_v1.json")
    D44 = jl(f"{O}/relight_seg44/relight_seg44.json")
    prop = fc_proposal(F, M)
    g["version"] = "v3.1-staging"
    g["date"] = DATE
    g["staging"] = {"status": "STAGING, NOT PUBLISHED: gnc.json v3 (interfaces/gnc.json) is under the independent GNC review; this "
                              "file is v3 plus the v3.1 items listed in changes_from_v3; interfaces/gnc.json stays v3 until the "
                              "lead publishes", "base": {"file": "interfaces/gnc.json", "version": "v3", "sha256": h},
                    "builder": VERSION, "staging_folder": STG}
    g["supersedes"] = "nothing yet (staging); on publication it would supersede gnc.json v3"
    g["status"] = ("v3.1 STAGING (2026-10-13): v3 unchanged plus FC_THRUST (over_thrust_fc_thrust: " + prop["short"]
                   + "; ADOPTED by the lead 2026-10-13), Combustion data items (coast_accel_a1; duty_cycles.v.records_b1_62m_staging), "
                   "the T_tank ARM-range note (t_tank_arm_range) and the vapour-start fallback cost "
                   "(relight_vapour_start_fallback). v3 status follows. " + g["status"])
    ld = g["lead_decisions_2026-10-13"]["v"]
    ld["stale_flag_rule_accepted"] = ("STALE-FLAG RULE ACCEPTED as GNC proposed (fresh <= 0.3 s ASSUMED; stale -> hold the last valid "
                                      "flag since MECO; none -> 0.81 s; UNKNOWN treated as UNPRIMED); re-examined if a seat leak "
                                      "can empty the segment within the staleness limit; leak acceptance adopted, drain >= 6 min "
                                      ">> 0.3 s: the rule stands")
    ld["fc_thrust_closure_item_1"] = ("GNC reviews and runs m2_fc_thrust, publishes the 3-sigma error and latency of the "
                                      "accelerometer thrust estimate (raw, tau <= 20 ms), the Pc-lost false-abort rate at 650 N / "
                                      "20 ms and the detection time of a stuck full-stroke pintle (670-876 N), and proposes a "
                                      "threshold, as gnc.json v3.1 staging")
    ld["combustion_data_items"] = ("A1 body-axis acceleration MECO -> RELIGHT (nominal and dispersed, p01/p50/p99 and the "
                                   "min-accel run) and the B1 62 m p99 / max duty-cycle CSVs, as hub files (gnc.json v3 frozen)")
    ld["t_tank_arm_range"] = ("tank ARM range 15-24 C, ignition interlock at 24 C (at ARM and at ignition); GNC records its "
                              "U(15, 25) C draw as a small difference, no re-run; the next GNC baseline draws U(15, 24) C")
    ld["flight_retained_vapour"] = ("in flight, retained vapour in the MV-to-seat segment <= 19 cm3 (design requirement, owner "
                                    "Combustion with Mechanical's segment heat input)")
    ld["fc_thrust_adopted"] = ("FC_THRUST ADOPTED (CHANGELOG 2026-10-13): over-thrust abort 650 N held 3 frames (20 ms) on a "
                               "first-order tau 20 ms estimate (raw samples rejected: 29/1000 false aborts); valid flag only when "
                               "airborne, engine lit and drogue released; NEW REQUIREMENT (provisional) FC mass-estimate error <= "
                               "1 % (1 sigma) throughout the burn; GNC specifies the mass estimator; founder action: weigh the "
                               "loaded vehicle at ARM (scale range / resolution TO-DEFINE); v3.1 staging goes to the independent "
                               "GNC reviewer as an addendum")
    ld["retained_vapour_option_b_cost"] = ("RETAINED VAPOUR (2026-10-13): the governing quantity is the vapour between the liquid "
                                           "and the pintle at RELIGHT; Combustion assesses buoyant migration in the drogue "
                                           "descent; GNC computes the P cost of option (b), every relight planned as a "
                                           "vapour-segment start (0.16 + 1.05 s); fixes (a) head-end prime bleed and (d) MV "
                                           "opened early under the drogue held until that result; option (c) rejected")
    g["over_thrust_fc_thrust"] = fc_thrust_section(F, prop, M)
    g["relight_vapour_start_fallback"] = seg44_section(D44)
    g["coast_accel_a1"] = coast_section(C)
    g["duty_cycles"]["v"]["records_b1_62m_staging"] = b62_block(B)
    g["t_tank_arm_range"] = ttank_section(T)
    g["known_issue_v3_builder"] = {"v": "re-running m2_gnc_json_v3 v5 with out/fc_thrust/fc_thrust.json present stops with a "
                                        "NameError (fc_thrust_section is called but not defined in v5). gnc.json v3 was built "
                                        "without FC_THRUST, so the published v3 is not affected; v3.1 is built by "
                                        "m2_gnc_json_v31 from the published v3 bytes", "tag": "GNC self-review 2026-10-13"}
    ans = g["answers_to_requests"]
    ans["lead_fc_thrust_closure_item_1_2026-10-13"] = prop["finding"]
    ans["lead_combustion_a1_coast_accel_2026-10-13"] = g["coast_accel_a1"]["v"]["summary"]
    ans["lead_combustion_b1_62m_duty_cycles_2026-10-13"] = (
        "staging_v3.1/duty_cycles: " + "; ".join(f"{x['name']} {x['burn_time_thrust_on_s']} s thrust-on (run {x['run_index']}, "
                                                  f"{'lands' if x['success'] else 'fails landing'})"
                                                  for x in g["duty_cycles"]["v"]["records_b1_62m_staging"]["records"])
        + "; all inside the 85 m sizing cycles")
    ans["lead_t_tank_2026-10-13"] = g["t_tank_arm_range"]["v"]["finding"]
    ans["lead_vapour_start_fallback_2026-10-13"] = g["relight_vapour_start_fallback"]["v"]["finding"]
    oi = []
    for x in g["open_items"]:
        if x.startswith("accelerometer over-thrust abort (FC_THRUST"):
            x = ("accelerometer over-thrust abort (FC_THRUST): GNC evidence in over_thrust_fc_thrust (v3.1 staging; simulation, "
                 "mass-estimate error and vibration ASSUMED); GNC proposes 650 N / 20 ms with the tau 20 ms estimate and the fc "
                 "valid window, plus an FC mass-estimate requirement" + (f" <= {100 * prop['requirement_sd']:g} % (1 sigma)"
                                                                       if prop["requirement_sd"] else "") +
                 " for the 670 N end of the stuck range (missed in "
                 f"{100 * F['threshold_summary']['tau20ms|650']['miss_670'] / F['threshold_summary']['tau20ms|650']['n_670']:.1f} % "
                 "with 3 %); lead decides; ECU implementation and CAN timing owner Electronics; bench check of F_acc vs load cell "
                 "(DC-C / DC-D, founders)")
        oi.append(x)
    oi += ["T_tank draw: the next GNC baseline draws U(15, 24) C (lead 2026-10-13); v3 / v3.1 Monte Carlo draw U(15, 25) C "
           "(t_tank_arm_range)",
           "FSW mass estimate: GNC to specify the FC mass estimator (pad weighing + consumption model) and its error budget; "
           "the 650 N over-thrust check covers 670 N only with <= " + (f"{100 * prop['requirement_sd']:g}" if prop["requirement_sd"]
                                                                      else "?") +
           " % (1 sigma) (over_thrust_fc_thrust.proposal.mass_estimate_requirement)",
           "A1 relight with a vapour segment: v3 (W 0.65 s) aborts every 44 cm3 vapour-full relight (Combustion); GNC proposes W "
           ">= 1.00 s with the planning value 0.91 s while the state at RELIGHT is unknown, 0.81 s if the segment is shown to "
           "stay liquid, and a state-dependent plan if the state can be indicated (relight_vapour_start_fallback.proposal); "
           "lead decides after Combustion's buoyant-venting check",
           "A1 coast acceleration: the drogue opening / snatch load is not modelled (UNKNOWN); the isolation-valve station is "
           "ASSUMED (no station in mechanical.json v2): Mechanical to give it with the hose routing if Combustion needs the "
           "valve-end values refined (coast_accel_a1)"]
    g["open_items"] = oi
    g["requests"] = list(g["requests"]) + [
        "REQUEST Electronics: FC_THRUST on the ECU: check rate and scheduling, CAN latency budget FC -> ECU, and the valid-flag "
        "semantics proposed in over_thrust_fc_thrust.proposal.valid_flag; the IMU part's internal filter delay (DATASHEET) when "
        "chosen",
        "REQUEST founders (bench): log the FC accelerometer thrust estimate against the load cell on DC-C / DC-D and the IMU "
        "vibration at full thrust (refutation tests in over_thrust_fc_thrust.refutation)",
        "REQUEST founders: can the loaded vehicle be weighed at ARM, and with which scale (range, resolution, accuracy)? Input to "
        "the FC mass-estimate specification (over_thrust_fc_thrust.proposal.mass_estimate_requirement)",
        "REQUEST Combustion: (1) hard-start / accumulation consequence of an ECU window W 1.05 s from E1 on a LIQUID line (a "
        "failed ignition flows up to 0.40 s longer than with W 0.65 s); (2) whether a relight engine-on time of p99 8.5-8.8 s "
        "(planning value 0.91-1.21 s on a liquid line, against the 8.26 s A1 sizing counter) changes the A1 thermal / erosion "
        "duty (relight_vapour_start_fallback.runs_over_a1_sizing_counter_by_base)",
        "REQUEST Electronics: can the ECU set the relight window per start (W 0.65 s primed liquid, W 1.05 s vapour or "
        "unknown), and can the PRIMED/UNPRIMED flag carry a VAPOUR state (segment TC / P_feed) before RELIGHT so the FC can "
        "plan 0.81 s or 1.21 s (relight_vapour_start_fallback.proposal)?"]
    g["scripts"] = sorted(set(g["scripts"] + [f"{STG}/sim/scripts/{s}" for s in (
        "m2_fc_thrust.py", "m2_fc_thrust_plot.py", "m2_fc_thrust_mest.py", "m2_coast_accel_a1.py", "m2_coast_accel_plot.py", "m2_dc_b1_62m_record.py",
        "m2_ttank_arm_check.py", "m2_stage_hub_v31.py", "m2_gnc_json_v31.py", "m2_relight_seg44.py", "m2_relight_seg44_plot.py")]))
    g["changes_from_v3"] = [
        "over_thrust_fc_thrust (new): m2_fc_thrust v1.1 run (v1 reviewed before its first run: planning value 0.81 s, D_model on "
        "the estimated vz, fc valid window, filter variants, held maxima, latency, 500 runs per branch) and the FC "
        "mass-estimate sensitivity m2_fc_thrust_mest v1 (paired, same flights)",
        "coast_accel_a1 (new): Combustion data item 1",
        "duty_cycles.v.records_b1_62m_staging (new): Combustion data item 2 (index revision of v3 unchanged: rev d)",
        "t_tank_arm_range (new) and lead_decisions_2026-10-13: stale_flag_rule_accepted, fc_thrust_closure_item_1, "
        "combustion_data_items, t_tank_arm_range, flight_retained_vapour",
        "known_issue_v3_builder (new)",
        "relight_vapour_start_fallback (new, builder v1.1): m2_relight_seg44 v1.2, 36 paired cases (fallback (b), liquid at "
        "1.21 s, 34 cm3, 0.69 s purge, (b') plan 0.81 s with W 1.05 s, planning-value sweep), ECU abort probabilities from "
        "Combustion, decision table",
        "lead_decisions_2026-10-13 (builder v1.1): fc_thrust_adopted, retained_vapour_option_b_cost",
        "status, answers_to_requests, open_items (FC_THRUST item replaced; T_tank draw, FSW mass estimate, vapour-segment relight, "
        "coast-acceleration limits added), requests (+5), scripts (+11)"]
    first = ["id", "version", "date", "owner", "staging", "supersedes", "status", "publication_note", "changes_from_v3",
             "lead_decisions_2026-10-13", "lead_decisions_2026-10-12", "units", "conventions", "inputs_read", "scripts",
             "changes_from_v2", "carried_from_v2"]
    g = {**{k: g[k] for k in first if k in g}, **{k: v for k, v in g.items() if k not in first}}
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, "w") as f:
        json.dump(g, f, indent=1, default=float)
    print("written", DEST, os.path.getsize(DEST), sha(DEST)[:16])
    print("claim:", prop["claim"])


if __name__ == "__main__":
    main()
