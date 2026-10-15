"""m2_gnc_json_v3 v5 (2026-10-13): assemble interfaces/gnc.json v3 (GNC re-baseline on mechanical.json v2).
v5 (2026-10-13 afternoon and evening, the first published build) adds on top of v4: sim6/run6 v2.7.1-dev (regression-law band,
start-delay quantile option; verification_v271), the B1 regression band with the GNC cap computation and the lead's 62 m
provisional cap (b1_regression_band.lead_cap; the 85 m dispersed cycles stay the sizing cases), the v2.8 relight with the
planning value 0.81 s adopted by the lead and option (c) adopted provisionally (relight_planning_v28 with the paired option (c)
verification and the GNC stale / missing-flag rule), and the summary-field patch apply_1013b; FC_THRUST is written only when its
result file exists (over_thrust_fc_thrust), otherwise it is listed as open.
v4 adds the work on the lead's decisions of 2026-10-13 on top of v3 (2026-10-12, never published): sim6/run6 v2.7-dev
(in-flight throat growth, thrust-effectiveness estimator k_est_asc 2 = provisional flight-software baseline for both profiles),
throat growth 7-11 % in the Monte Carlo with P with and without, the dispersed duty cycles (sizing cases) and the corrected
burn-time definition of their index, the abort shutdown law and its tail-off bracket, no in-flight relight retry with the
no-light accounting, the relight placeholder 0.8 + 0.3 s, the estimator failure modes (tests T10-T13 and the Monte Carlo
forensics), verification v2.7, the Q2 notch research proposal and the updated icd_inputs_for_airframe.

gnc.json v3 = gnc.json v2 (published 2026-10-12 20:34Z) + the work on the lead's requests of 2026-10-12, in the lead's order:
  (1) propellant closure OI-1 on combustion.json v2.3 + mechanical.json v2 (lead decision: option (a); A1 baseline, B1 85 m,
      B2 unchanged, A2 removed from the 2.00 kg plan, 2.20 kg / 3.49 L fallback) and the reference-governor ratchet;
  (2) the mechanical.json v2 re-baseline: reading checks, the ENG-07d Monte Carlo set (J_int, notch, stiffness target,
      landing bandwidth x 0.75 fallback, 12.5 % floor), the CSI frequency target on the v2 mass properties, the lead-adopted
      stiffness target, the linkage-ratio sweep, the hose in the hinge-moment budget;
  (3) flight software v2.6 (tracker + governor + ratchet, pre-MECO throttle-down, relight start rule, NC-closed relight with
      the ENG-04 torch timeline, anti-windup evidence), duty cycles v3 (DC-A1, DC-B1 85 m; DC-B1 v2 kept as the conservative
      thermal envelope), reference vehicle v3d and a self-contained icd_inputs_for_airframe.
Interface sets: iface_v3c (combustion.json v2.3, mechanical.json v2, electronics.json v1) is the basis of every mechanical.json
v2 item; iface_v3b (combustion.json v2.2 = v2.3 in every section GNC reads, mechanical.json v1) carries the paired flight-software
evidence produced before mechanical.json v2 was published; iface_v3a the attribution and bit-identity checks.
Every number is read from a result or interface file; GNC design values and lead decisions are the named constants below.
Env: GNC_V2_PUB, GNC_IFACE (v3c), GNC_IFACE_B (v3b), GNC_* result folders (see the constants). Run: python scripts/m2_gnc_json_v3.py
v2 of this script (v3 on iface_v3b with mechanical.json v2 deferred) is kept as m2_gnc_json_v3_v2_backup.py in the GNC work area;
it produced no published file. v3 of this script (2026-10-12, built gnc.json v3 without the 2026-10-13 work, never
published) is kept as scratch/m2_gnc_json_v3_v3_backup_pre1013.py in the GNC work area."""
import copy
import csv
import hashlib
import json
import os
import sys
import numpy as np
from scipy.optimize import brentq
from scipy.stats import binomtest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

W = "/home/claude/work/space"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = f"{W}/out"
V2PUB = os.environ.get("GNC_V2_PUB", f"{O}/gnc_json/gnc_v2_published.json")
IFACE = os.environ.get("GNC_IFACE", f"{W}/iface_v3c")
IFACE_B = os.environ.get("GNC_IFACE_B", f"{W}/iface_v3b")
IFACE_A = os.environ.get("GNC_IFACE_A", f"{W}/iface_v3a")
MECO = os.environ.get("GNC_MECO_OUT", f"{O}/meco")
CF = os.environ.get("GNC_CF_OUT", f"{O}/ctrlfix")
CSI_FEA = os.environ.get("GNC_CSI_OUT", f"{O}/csi_v3")
CSI_M2 = os.environ.get("GNC_CSI_M2_OUT", f"{O}/csi_v3c")
V3A_RES = os.environ.get("GNC_V3A_RES", f"{O}/results_v3a")
PC_OUT = os.environ.get("GNC_PC_OUT", f"{O}/prop_closure")
PC2_OUT = os.environ.get("GNC_PC2_OUT", f"{O}/prop_closure_m2")
PCE_OUT = os.environ.get("GNC_PCE_OUT", f"{O}/prop_closure_eval")
MV2C = os.environ.get("GNC_MV2C_OUT", f"{O}/mech_v2_check")
MV2MC = os.environ.get("GNC_MV2MC_OUT", f"{O}/mechv2_mc")
NSW = os.environ.get("GNC_NSW_OUT", f"{O}/n_sweep")
DC3 = os.environ.get("GNC_DC3_OUT", f"{O}/duty_cycles_v3")
VEH3 = os.environ.get("GNC_VEH3_OUT", f"{O}/vehicle_v3d")
RES2 = os.environ.get("GNC_RES_V2", f"{O}/results_v2")
CHK26 = os.environ.get("GNC_CHK26", f"{O}/v26_checks")
REPRO = os.environ.get("GNC_REPRO_OUT", f"{O}/repro_v26")
CHK26C = os.environ.get("GNC_CHK26C", f"{O}/v26_checks_v3c")
RSS = os.environ.get("GNC_RSS_OUT", f"{O}/relight_seq_sens")
TGO = os.environ.get("GNC_TG_OUT", f"{O}/throat_growth")
TGA = os.environ.get("GNC_TGA_OUT", f"{O}/throat_growth_a1k2")
ABO = os.environ.get("GNC_AB_OUT", f"{O}/abort_tailoff")
V27 = os.environ.get("GNC_V27_OUT", f"{O}/v27_checks")
RL181_OUT = os.environ.get("GNC_RL181_OUT", f"{O}/relight_181")
RBO = os.environ.get("GNC_RB_OUT", f"{O}/regband")
V271 = os.environ.get("GNC_V271_OUT", f"{O}/v271_checks")
RV28 = os.environ.get("GNC_V28_OUT", f"{O}/relight_v28")
FCTO = os.environ.get("GNC_FCT_OUT", f"{O}/fc_thrust")
# 2026-10-13 afternoon values (the SIM evidence is in relight_planning_v28 / b1_regression_band)
PLAN_V28_GNC = 0.81     # REQ lead decision 2026-10-13 (GNC rule adopted): planning value = flight Pc-confirm deadline 0.16 + 0.65 s
PLAN_V28_FAULT = 1.41   # REQ lead decision 2026-10-13, option (c) PROVISIONAL: planning value on an ECU UNPRIMED flag
B1_CAP_LEAD = 62.0      # REQ lead decision 2026-10-13: B1 hop cap 62 m PROVISIONAL (the GNC 62.9 m rounded down) until T1-T4
B1_SIZING_H = 85.0      # REQ lead decision 2026-10-13: the B1 85 m dispersed cycles stay the conservative thermal / erosion sizing
DEST = os.environ.get("GNC_GJ3_DEST", f"{O}/gnc_json/gnc_v3.json")
RELAY = os.path.join(HERE, "data", "relay", "lead_relay_mech_fea_k_20261012.json")
TOFF_FIT = os.path.join(HERE, "data", "tailoff", "tailoff_fit_v1.json")
FW = "/home/claude/work/electronics/firmware/src/core"
DATE = "2026-10-13"
LEAD = "AD_prov_2kg"
HUB = "01-systems-gnc"
# GNC design values of flight software v2.6 (DESIGN; the SIM evidence is written next to each one in the file)
FSW = dict(gim_cmd_rate_dps=100.0, gim_cmd_acc_dps2=2000.0, att_ref_rate_dps=40.0, att_ref_mode=1, meco_td_cmd=0.72,
           meco_td_gate=0.75, meco_td_hold_s=0.25, relight_start_frac=0.20)
# lead decisions 2026-10-12 (interfaces/CHANGELOG.md + lead messages to GNC)
LEAD3 = {"linkage_ratio_n": 4.8, "V_val_V": 6.6, "arm_rest_min_V": 8.1, "eng07b_max_episode_s": 0.1, "eng07c_J_int_max_kgm2_v2": 1e-3,
         "eng07d_flex_gm_min_dB": 6.0, "design_load_Nm": 35.3, "eng07_min_slew_dps_at_7V4": 100.0,
         "source": "lead decisions 2026-10-12 on the GNC n 4.8 actuator study (interfaces/CHANGELOG.md)"}
# lead decisions 2026-10-13 (interfaces/CHANGELOG.md + lead messages to GNC); numbers GNC applies are named here
LEAD_1013 = {"relight_seq_add_s": 0.3, "growth_band": (0.07, 0.11), "line_volume_cm3_relayed": 21.4,
             "p_nl_placeholders": (0.005, 0.01, 0.02, 0.05), "demo_confidence": 0.95,
             "source": "lead decisions and messages to GNC 2026-10-13 (interfaces/CHANGELOG.md)"}
LEAD_V3 = {"K_struct_min_Nm_per_rad": 3100.0, "K_struct_goal_Nm_per_rad": 5200.0, "btvc1_Ks_gate_Nm_per_rad": 100.0,
           "hose_K_max_Nm_per_rad": 20.0, "n2o_kg": 2.00, "tank_L": 3.17, "B1_h_m": 85.0, "B2_h_m": 50.0, "A1_h_m": 300.0,
           "source": "lead messages to GNC 2026-10-12 (CSI target adopted; OI-1 option (a); hose routing rule) + interfaces/CHANGELOG.md"}


def P(v, tag, note=None, **kw):
    d = {"v": v, "tag": tag}
    if note:
        d["note"] = note
    d.update(kw)
    return d


def rnd(x, n=3):
    if isinstance(x, dict):
        return {k: rnd(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [rnd(y, n) for y in x]
    if isinstance(x, (float, np.floating)):
        return float(round(float(x), n)) if np.isfinite(x) else None
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def jl(p):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return None


def rcsv(p):
    try:
        with open(p) as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def sha(p):
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()
    except OSError:
        return None


HUB_ROOT = os.environ.get("GNC_HUB_ROOT", "/home/claude/work/shared-fallback/engine")


def hubrel(p):
    """Hub-relative name of a file used by GNC: a hub file loses the hub root; a file of a GNC interface snapshot (iface_v3*)
    is replaced by the hub file with the same basename AND the same sha256 (searched in the hub), else kept with a note."""
    if not isinstance(p, str) or not p.startswith("/"):
        return p
    if p.startswith(HUB_ROOT.rstrip("/") + "/"):
        return p[len(HUB_ROOT.rstrip("/")) + 1:]
    h, base = sha(p), os.path.basename(p)
    if h:
        for root, _, files in os.walk(HUB_ROOT):
            if base in files and sha(os.path.join(root, base)) == h:
                return os.path.relpath(os.path.join(root, base), HUB_ROOT) + f" (sha256/16 {h[:16]}, identical to the GNC input snapshot copy)"
    return f"{base} (GNC work-area copy, sha256/16 {(h or 'unreadable')[:16]}; no identical file found in the hub)"


def dci_rev(DCI):
    """Revision label of the duty-cycle index as written in the index itself."""
    return ((DCI or {}).get("index_revision") or {}).get("revision", "not recorded in the index")


def col(rows, k):
    return np.array([float(r[k]) if r.get(k) not in (None, "") else np.nan for r in rows])


def pr(d, comp):
    if not d:
        return None
    return f"{d['lost']} lost / {d['gained']} gained vs {comp}, McNemar p = {d['p']:.2g}" + (" (LOSES)" if d.get("loses") else "")


def pair(a, b):
    """paired exact McNemar of case b against case a (same draws)."""
    oa = col(a, "ok") > 0
    ob = col(b, "ok") > 0
    lost, gained = int(np.sum(oa & ~ob)), int(np.sum(~oa & ob))
    p = binomtest(lost, lost + gained, 0.5).pvalue if lost + gained else 1.0
    return dict(lost=lost, gained=gained, p=float(p), loses=bool(p < 0.05 and lost > gained))


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, c - hw), min(1.0, c + hw)]


def hinge(path):
    r = rcsv(path)
    if not r:
        return None
    h = col(r, "max_hinge")
    return dict(p99_Nm=float(np.percentile(h, 99)), max_Nm=float(np.nanmax(h)))


def mc_case(rows):
    ok = col(rows, "ok") > 0
    out = dict(n=len(rows), P=float(ok.mean()), ci95=wilson(int(ok.sum()), len(ok)))
    for k, lab in (("max_hinge", "hinge_Nm"), ("act_sat_max_dur", "sat_episode_max_s"), ("td_rate", "td_rate_dps"),
                   ("td_vh", "td_vh_mps"), ("max_gim_rate", "gimbal_rate_dps"), ("max_axial_g", "axial_g"),
                   ("peak_leg_force", "leg_force_N"), ("max_gim", "gimbal_deg"), ("max_lat_g_eng", "engine_lateral_g")):
        if rows and k in rows[0]:
            a = col(rows, k)
            out[lab] = dict(p50=float(np.nanpercentile(a, 50)), p99=float(np.nanpercentile(a, 99)), max=float(np.nanmax(a)))
    return out


# ---------------------------------------------------------------------------------------------------------- flight software
def fsw_section(CFE, MEV, MNOM, hinge_tab):
    f = {}
    rows = []
    for J in ("0", "1", "1.6", "2", "2.7", "4", "5", "8"):
        for fx in ("nofix", "acc2000_ref40"):
            c = f"cf_J{J}_{fx}"
            e = CFE.get(c)
            if not e:
                continue
            rows.append(dict(case=c, J_int_kgm2=float(J) * 1e-3, fix=fx, P=e["P"], ci95=e["ci95"],
                             vs_lead_baseline=pr(e.get("vs_baseline"), LEAD),
                             ENG07b_longest_episode_p99_s=e["longest_ep_p99_s"], longest_episode_max_s=e["longest_ep_max_s"],
                             frac_runs_episode_gt_0p1s=e["frac_runs_ep_gt_0p1"], ENG07b_pass=e["ENG07b_pass"],
                             hinge=hinge_tab.get(c)))
    alts = []
    for c, e in CFE.items():
        if c.startswith("cf_J2.7_") and c not in ("cf_J2.7_nofix", "cf_J2.7_acc2000_ref40") and "_aw" not in c:
            alts.append(dict(case=c, P=e["P"], ci95=e["ci95"], vs_lead_baseline=pr(e.get("vs_baseline"), LEAD),
                             vs_nofix_same_J=pr(e.get("vs_nofix_same_J"), "cf_J2.7_nofix"),
                             ENG07b_longest_episode_p99_s=e["longest_ep_p99_s"], longest_episode_max_s=e["longest_ep_max_s"],
                             ENG07b_pass=e["ENG07b_pass"]))
    ok = [r["J_int_kgm2"] for r in rows if r["fix"] == "acc2000_ref40" and r["ENG07b_pass"] and "LOSES" not in str(r["vs_lead_baseline"])]
    bad = [r["J_int_kgm2"] for r in rows if r["fix"] == "acc2000_ref40" and not (r["ENG07b_pass"] and "LOSES" not in str(r["vs_lead_baseline"]))]
    f["version"] = ("flight software v2.6 (GNC reference implementation sim6 v2.6; FC items owned by GNC, ECU items implemented by "
                    "Electronics)")
    f["gimbal_command_tracker"] = P(
        {"rate_limit_dps": FSW["gim_cmd_rate_dps"], "accel_limit_dps2": FSW["gim_cmd_acc_dps2"],
         "accel_limit_rad_s2": rnd(np.radians(FSW["gim_cmd_acc_dps2"]), 2),
         "law": "per axis, time-optimal braking toward the raw attitude-law command: v_d = sign(e) min(sqrt(2 a_max |e|), |e|/dt, v_max), "
                "then |dv| <= a_max dt; ahead of the 2nd-order 50 rad/s low-pass and the ENG-07d notch",
         "where": "ECU TvcShaper (replaces the plain 100 deg/s slew limiter), 1 kHz"},
        "DESIGN GNC (sim6 v2.6) + SIM m2_ctrlfix (500 runs per case, same draws, seed 101)",
        "the commanded engine acceleration never exceeds what the servo pair can deliver on the engine plus reflected rotor "
        "inertia, so the shaping chain no longer runs ahead of the engine (the v2.5 saturated limit cycle)")
    f["attitude_reference_governor"] = P(
        {"slew_dps": FSW["att_ref_rate_dps"], "mode": FSW["att_ref_mode"],
         "law": "the commanded thrust direction moves toward the guidance demand on a great circle at <= 40 deg/s; at every "
                "attitude-loop activation (relight, loop hand-over) it starts from the estimated body axis; RATCHET (mode 1, "
                "adopted by the lead 2026-10-12): whenever the estimated body axis is closer to the guidance demand than the "
                "reference, the reference restarts from the body axis",
         "where": "FC attitude loop (GNC flight software)"},
        "DESIGN GNC (sim6 v2.6) + SIM m2_ctrlfix / m2_prop_closure / m2_meco",
        "removes the step demand at relight that drove the actuator into long saturation; the ratchet stops the reference from "
        "pulling a vehicle that is still rotating out of the free-fall tumble back toward the attitude it had when the governor "
        "started (evidence: propellant_closure_v3.ratchet_effect (v3b), propellant_closure_v3.ratchet_effect_mech_v2 (v3c) and "
        "verification_v26 test T9)")
    f["control_fix_evidence"] = P(
        {"by_J_int": rnd(rows, 4), "alternatives_at_J_2.7e-3": rnd(alts, 4),
         "ENG07b_and_P_met_up_to_J_int_kgm2": max(ok) if ok else None, "first_J_int_failing_kgm2": min(bad) if bad else None},
        "SIM m2_ctrlfix cf (sim6 v2.6 on iface_v3b, n 4.8, 6.6 V both-stall plug voltage, as-drawn chain with sag, 500 runs, seed 101)",
        "chosen: acceleration limit 2000 deg/s2 + reference governor 40 deg/s. Rejected with evidence: acceleration limit alone "
        "(ENG-07b fails at J 2.7e-3), governor alone (passes at 2.7e-3, longest episode 0.40 s), governor 20/30 deg/s (P loses: "
        "slow re-orientation), governor 60 deg/s (ENG-07b fails), windowed governor (no gain), encoder re-initialisation "
        "anti-windup (anti_windup_encoder_reinit). mechanical.json v2 re-check: mech_v2_rebaseline.monte_carlo")
    awmc = {c: dict(P=e["P"], ci95=e["ci95"], vs_lead_baseline=pr(e.get("vs_baseline"), LEAD),
                    vs_same_J_without=pr(e.get("vs_nofix_same_J"), "same J, no fix"),
                    ENG07b_longest_episode_p99_s=e["longest_ep_p99_s"], longest_episode_max_s=e["longest_ep_max_s"],
                    ENG07b_pass=e["ENG07b_pass"])
            for c, e in CFE.items() if "_aw" in c}
    f["anti_windup_encoder_reinit"] = P(
        "REJECTED: re-initialising the shaping states to the measured engine angle when the command leads it by more than "
        "2 deg turned the long saturation into a sawtooth command and a limit cycle near the 7 deg limit; on the worst run of "
        "the J 2.7e-3 case (run 323) the vehicle crashed (tilt 102 deg). The Monte Carlo confirms it on every run type: the "
        "2 deg threshold sits inside the normal tracking lag of a 100 deg/s command (~20 ms x 100 deg/s), so the "
        "re-initialisation also fires in ordinary manoeuvres; larger thresholds were not explored",
        "SIM single-run diagnostic (sim6 v2.6 gim_aw_thr 2 deg, run 323, J_int 2.7e-3, 6.6 V)" + (" + SIM m2_ctrlfix Monte Carlo" if awmc else ""),
        "evidence kept: 01-systems-gnc/results/ctrlfix/sat_run323_J0.0027_acc2000_aw2.png (and the same run without the "
        "re-initialisation); the option stays in the code, off", monte_carlo=(rnd(awmc, 4) if awmc else "not run as a Monte Carlo"))
    td = MEV.get("mr_td72", {})
    toff = MEV.get("mr_toff", {})
    f["meco_throttle_down"] = P(
        {"command_frac_Fmax": FSW["meco_td_cmd"], "meco_gate_measured_frac_Fmax": FSW["meco_td_gate"],
         "predictor_hold_s": FSW["meco_td_hold_s"],
         "law": "near the predicted apogee guidance commands 72 % F_max; the apogee predictor holds that level 0.25 s and adds "
                "the lift-ramp tail-off impulse from it; MECO when the predicted apogee reaches the target AND the measured "
                "thrust is <= 75 % F_max (the gate is waived 2 x hold after the throttle-down command)",
         "where": "FC guidance (GNC flight software); the ECU closes the pintle at the HV69 speed"},
        "DESIGN GNC (sim6 v2.6) + SIM m2_meco (500 runs)",
        f"ENG-05 at the 0.25 s stroke: reduced-model time to 10 % max {td.get('ENG05_t10_s', {}).get('max', float('nan')):.3f} s "
        f"(every run <= 0.100 s), MECO thrust <= {100 * td.get('meco_thrust_frac', {}).get('max', float('nan')):.1f} % F_max; "
        f"from 100 % the same model gives {toff.get('ENG05_t10_s', {}).get('max', float('nan')):.3f} s (fails; Mechanical: "
        "0.124 s at 3.5 MPa tank). REQUIRED (lead 2026-10-12)")
    f["meco_throttle_down_cost"] = P(rnd({
        "P": {c: dict(P=MEV[c]["P"], ci95=MEV[c]["ci95"]) for c in (LEAD, "mr_toff", "mr_td72", "mr_td70") if c in MEV},
        "mr_td72_vs_mr_toff": pr(td.get("vs_mr_toff"), "mr_toff"),
        "apogee_p01_p50_p99_m": {c: [MEV[c]["h_max"]["p01"], MEV[c]["h_max"]["p50"], MEV[c]["h_max"]["p99"]]
                                 for c in (LEAD, "mr_toff", "mr_td72", "mr_td70") if c in MEV and "h_max" in MEV[c]},
        "propellant_used_mean_kg": {c: MEV[c]["prop_used"]["mean"] for c in (LEAD, "mr_toff", "mr_td72") if c in MEV},
        "sized_load_kg": {c: MEV[c]["m_n2o_sized_kg"] for c in (LEAD, "mr_toff", "mr_td72", "mr_td70") if c in MEV},
        "tailoff_impulse_mean_Ns": {c: MEV[c].get("tailoff_imp_Ns", {}).get("mean") for c in ("mr_toff", "mr_td72") if c in MEV}}, 4),
        "SIM m2_meco mr (same 500 draws, iface_v3b) + m2_meco_eval",
        "no measurable cost: apogee median within 1 m of MECO from 100 % on the same shutdown model, tighter apogee spread, same "
        "propellant; the realistic lift-ramp shutdown itself lowers the apogee by ~5-6 m vs the v2.5 first-order 35 ms model")
    if MNOM:
        f["meco_nominal_flights"] = P(rnd(MNOM.get("rows"), 4), "SIM m2_meco_nominal (no wind, no noise, lead tank, iface_v3b)",
                                      "toff_td75_evidence: a 75 % command never satisfies the 75 % gate with a first-order thrust "
                                      "response; MECO waits for the waiver and the apogee overshoots: kept as the evidence for "
                                      "the 72 % command / 75 % gate split")
    t9 = td.get("t90_relight_s", {})
    f["relight_start_rule"] = P(
        {"start_level_frac_Fmax": f"max(floor, {FSW['relight_start_frac']:.2f})",
         "law": "the relight starts at the start level and holds it until the thrust reaches 90 % of it; then guidance throttles",
         "with_20pct_floor": "the rule is the floor start (no change)", "with_12.5pct_floor": "start at 20 %, not at the floor"},
        "DESIGN GNC (sim6 v2.6) + SIM m2_meco", "Combustion: step start to the 12.5 % floor 0.52-0.53 s to 90 %, 20 % start "
        "0.43-0.44 s (ENG-04 <= 0.5 s); the rule keeps ENG-04 at either floor")
    rel = {}
    for c in ("mr_td72", "mr_td72_tign10", "mr_td72_tign20", "mr_td72_tign30", "mr_f125", "mr_f125_td72_floorstart", "mr_f125_td72_rs20"):
        if c in MEV:
            e = MEV[c]
            comp = [k for k in e if k.startswith("vs_") and k != "vs_baseline"]
            rel[c] = dict(note=e["note"], P=e["P"], ci95=e["ci95"],
                          t90_p01_p50_max_s=[e.get("t90_relight_s", {}).get(k) for k in ("p01", "p50", "max")],
                          frac_t90_ge_0p53=e.get("t90_relight_s", {}).get("frac_ge_0p53"),
                          vs=(pr(e[comp[0]], comp[0][3:]) if comp else None), vs_lead_baseline=pr(e.get("vs_baseline"), LEAD))
    f["relight_start_delay_coverage"] = P(rnd(rel, 4), "SIM m2_meco mr (start-delay draw U(0.2, 0.6) s shifted by t_ign_add)",
                                          f"the MC start delay gives t90 {t9.get('p01', float('nan')):.2f}-{t9.get('max', float('nan')):.2f} s "
                                          f"({100 * t9.get('frac_ge_0p53', float('nan')):.0f} % of runs >= 0.53 s); +0.2 s on every run "
                                          "(t90 up to 0.83 s) loses nothing; +0.3 s (t90 up to 0.93 s) loses landings unless the "
                                          "planning value carries it (relight_nc_valve_closed)")
    return f


def nc_relight(MEV):
    """Relight with the NC isolation valve closed through the MECO coast (lead 2026-10-12)."""
    cs = ["mr_td72", "mr_td72_ncmin", "mr_td72_nc", "mr_td72_nc_ecu", "mr_td72_nc_unplanned", "mr_td72_nc_m10", "mr_td72_nc_m20",
          "mr_td72_nc_m30", "mr_fsw_J1.6", "mr_fsw_J1.6_nc", "mr_fsw_J1.6_nc_rat", "mr_f125_td72_rs20", "mr_f125_rs20_nc",
          "mr_AF_fix_td72", "mr_AF_fix_td72_nc", "mr_AF_fix_td72_nc_rat", "mr_B_fix_toff", "mr_B_fix_toff_rat"]
    tab = {}
    for c in cs:
        e = MEV.get(c)
        if not e:
            continue
        comp = [k for k in e if k.startswith("vs_") and k != "vs_baseline"]
        tab[c] = dict(note=e["note"], P=e["P"], ci95=e["ci95"], planning_value_s=e.get("t_ign_est_s"),
                      start_delay_draw_s=[e["t_ign_draw_s"]["min"], e["t_ign_draw_s"]["max"]] if "t_ign_draw_s" in e else None,
                      t90_p01_p50_max_s=[e.get("t90_relight_s", {}).get(k) for k in ("p01", "p50", "max")],
                      relight_cmd_h_p01_p50_m=[e.get("relight_cmd_h_m", {}).get(k) for k in ("p01", "p50")],
                      h_at_t90_p01_min_m=[e.get("h_at_t90_est_m", {}).get(k) for k in ("p01", "min")],
                      propellant_mean_kg=e["prop_used"]["mean"], liq_left_min_kg=e["liq_left"]["min"],
                      vs=(pr(e[comp[0]], comp[0][3:]) if comp else None), vs_lead_baseline=pr(e.get("vs_baseline"), LEAD))
    return tab


# ---------------------------------------------------------------------------------------------------------- propellant
def a2_tumble(folder, suf, case):
    r = rcsv(os.path.join(folder, f"mc6_runs_{case}_{suf}.csv"))
    if not r:
        return None
    hm, hi, tb, rc = col(r, "h_max"), col(r, "h_ign"), col(r, "tumble_coast"), col(r, "max_rate_coast")
    return dict(n=len(r), tumble_frac=float(np.mean(tb > 0.5)), coast_rate_min_dps=float(np.min(rc)),
                coast_rate_p05_p95_dps=[float(np.percentile(rc, 5)), float(np.percentile(rc, 95))],
                apex_min_p50_max_m=[float(hm.min()), float(np.median(hm)), float(hm.max())],
                relight_h_p05_p50_p95_m=[float(np.percentile(hi, q)) for q in (5, 50, 95)])


def prop_closure_v3(PC2, PCE, PC1):
    if not PC2:
        return {"status": "not run"}
    cl = PC2["closure"]
    tab = {}
    for k in ("A1", "A2", "B1", "B2"):
        c = cl.get(k)
        if not c:
            continue
        a = c["at_2kg"]
        tab[f"DC-{k}"] = dict(
            profile=c["config"].get("profile"), h_target_m=c["config"].get("h_target", 100.0 if c["config"].get("profile") == "B" else 300.0),
            n2o_burned_kg=a["n2o_burned"], fuel_burned_kg=a["fuel_burned"], liquid_left_kg=a["liquid_left"],
            vapour_left_kg=a["vapour_left"], trapped_kg=a["trapped"], usable_left_at_2kg_kg=a["usable_left"],
            reserve_at_2kg_frac=a["reserve_frac"], closes_at_2kg=a["closes"], n2o_needed_25pct_kg=c["needed_kg"],
            tank_V_needed_L=(c["at_needed"] or {}).get("tank_V_L"), v2_rule_load_kg=c["v2_rule_kg"],
            delivered_isp_s=a["isp_delivered_s"], impulse_Ns=a["impulse_Ns"], burn_time_s=a["burn_time_s"],
            m_liftoff_kg=a["m_liftoff"], TW_liftoff=a["TW_liftoff"], apogee_m=a["h_max"], relight_h_m=a["h_ign"],
            relight_v_mps=a["v_ign"], starts=a["starts"])
    tr = PC2.get("trades", {})
    pce2 = ((PCE or {}).get("bases") or {}).get("pc2", {}).get("cases", {})
    mc = {c: dict(note=v.get("note"), m_n2o_kg=v.get("m_n2o_kg"), m_liftoff_kg=v.get("m_liftoff_kg"), tank_V_L=v.get("tank_V_L"),
                  P=v["P"], ci95=v["ci95"], fail_modes=v.get("fail_modes"), n_fail=v.get("n_fail"),
                  n_fail_propellant_limited=v.get("n_fail_propellant_limited"), n_exhausted=v.get("n_exhausted"),
                  liq_left_p01_kg=v.get("liq_left_p01"),
                  vs_same_cycle_at_2kg=next((pr(x, k[3:]) for k, x in v.items() if k.startswith("vs_")), None))
          for c, v in pce2.items()}
    cross = (PCE or {}).get("cross", {})
    rat = {k.split("|")[1]: dict(P_without=v["P_a"], P_with=v["P_b"], paired=pr(v, "without the ratchet"))
           for k, v in cross.items() if k.startswith("pcr_vs_pc|")}
    m2e = {k.split("|")[1]: dict(P_mech_v1=v["P_a"], P_mech_v2=v["P_b"], paired=pr(v, "mechanical.json v1 (same FSW)"))
           for k, v in cross.items() if k.startswith("pc2_vs_pcr|")}
    rat2 = {k.split("|")[1]: dict(P_without=v["P_a"], P_with=v["P_b"], paired=pr(v, "without the ratchet"))
            for k, v in cross.items() if k.startswith("pc2_vs_pc2n|")}
    lt = {k: dict(closing_load_kg=v["closing_load_kg"], tank_V_L=v["at_load"]["tank_V_L"], m_liftoff_kg=v["at_load"]["m_liftoff"],
                  TW_liftoff=v["at_load"]["TW_liftoff"], reserve_of_each_cycle_at_this_load=v["other_cycles_at_this_load"])
          for k, v in (tr.get("larger_tank") or {}).items()}
    a2 = {c: a2_tumble(PC2_OUT, "pc2", c) for c in ("pc_A2_2kg", "pc_A2_h240_2kg", "pc_A2_m2.20")}
    fb = mc.get("pc_A2_m2.20") or {}
    out = dict(
        what="N2O closure of the flight duty cycles on combustion.json v2.3 + mechanical.json v2 with the v3 flight software",
        rule=PC2["rule"], lead_tank=PC2["lead_tank"], interfaces=PC2["interfaces"], sim=PC2.get("sim"),
        nc_relight=PC2.get("nc_relight"), flight_software=PC2.get("flight_software"), table=rnd(tab, 3),
        trades=rnd({"B1_max_hop_height_closing_at_2kg_m": tr.get("B1_max_h_target_closing_at_2kg_m"),
                    "A2_max_apogee_closing_at_2kg_m": tr.get("A2_max_h_target_closing_at_2kg_m"),
                    "A1_max_apogee_closing_at_2kg_m": tr.get("A1_max_h_target_closing_at_2kg_m"),
                    "sweeps": tr.get("sweeps"), "floors": tr.get("floors"), "larger_tank": lt}, 3),
        monte_carlo=rnd(mc, 4),
        ratchet_effect=rnd(dict(cases=rat, basis="same draws, iface_v3b (mechanical.json v1), v3 FSW with vs without att_ref_mode 1"), 4),
        ratchet_effect_mech_v2=rnd(dict(cases=rat2, basis="same draws, iface_v3c (mechanical.json v2), pc2 (with) vs pc2n (without "
                                                          "att_ref_mode 1); plan cycles A1 and B1 85 m and the A2 stress case"), 4),
        mech_v2_effect=rnd(dict(cases=m2e, basis="same draws and FSW (with the ratchet); mechanical.json v1 + S230 growth (v3b) vs "
                                                 "mechanical.json v2 (v3c)"), 4),
        A2_dispersed_flight=rnd(dict(
            cases=a2, finding="every dispersed A2 flight tumbles end over end in the coast (finless, statically unstable "
                              "nose-first) and its apex falls short of the 300 m target: the tumble drag costs ~65 m; the "
                              "undisturbed nominal flight stays nose-up to ~304 m, so the nominal closure number of A2 is "
                              "optimistic in apex. Lowering the target to 240 m removes the propellant-limited failures but "
                              "the relight starts lower and tumble-recovery failures replace them (P unchanged)"), 2),
        decision=P({"option": "(a) mission change, no hardware change", "tank": "2.00 kg N2O / 3.17 L (unchanged)",
                    "A1": "BASELINE flight: A-D 300 m, nose drogue + aft fins", "B1": "development hop capped at 85 m",
                    "B2": "50 m hop, unchanged", "A2": "removed from the 2.00 kg plan",
                    "ratchet": "attitude reference governor ratchet (att_ref_mode 1) adopted"},
                   "REQ lead decision 2026-10-12 (OI-1), on this GNC trade", LEAD_V3["source"]),
        fallback_documented=P(rnd({"tank_n2o_kg": lt.get("A2", {}).get("closing_load_kg"), "tank_V_L": lt.get("A2", {}).get("tank_V_L"),
                                   "closes": "A1, A2 and B1 (100 m) under the +25 % rule",
                                   "m_liftoff_kg": {"A1": (mc.get("pc_A1_m2.20") or {}).get("m_liftoff_kg"), "A2_B": fb.get("m_liftoff_kg")},
                                   "P_landing": {c: (mc.get(c) or {}).get("P") for c in ("pc_A1_m2.20", "pc_A2_m2.20", "pc_B1_m2.20")},
                                   "tube_length_increase_m": None}, 4),
                              "SIM m2_prop_closure pc2 + DERIVED", "FALLBACK only (lead): use if A2 (finless free-fall 300 m) must fly; "
                              "tube length increase computed below from the published tank tube"))
    tube = (PC2.get("tank_tube") or {})
    out["decision"]["evidence"] = "table, trades, monte_carlo, A2_dispersed_flight"
    if PC1:
        out["history_mech_v1"] = dict(note="pc / pcr bases on iface_v3b (mechanical.json v1) without / with the ratchet: "
                                           "see 01-systems-gnc/results/prop_closure", interfaces=PC1.get("interfaces"))
    return out, tube


# ---------------------------------------------------------------------------------------------------------- mechanical.json v2
def slew_vs_load(NS, M):
    c = NS["calibration"]
    ne, Ts, wnl = c["n_eff0"], c["Ts_7V4"], c["wnl_7V4"]
    return wnl * (1.0 - M / (ne * Ts)) / ne


def mech_v2_rebaseline(MV2, MS, MCD, CSI3, NS, CFE, mechB, mech, el, relay):
    out = {}
    if MV2:
        out["reading_checks"] = P(rnd({"n_fail": MV2["n_fail"], "checks": [dict(check=c["check"], result=c["result"], detail=c["detail"])
                                                                          for c in MV2["checks"]],
                                       "engine_states": MV2["C1"]["states"], "rocking_band": MV2["C2"],
                                       "ledger_change": {k: MV2["C3"].get(k) for k in ("published", "changed_items")},
                                       "nominal_flights": MV2["C4"]}, 4),
                                  "SIM m2_mech_v2_check (run6 v2.6 on iface_v3c; reference numbers read from mechanical.json v2)",
                                  "C2 first definition (wet / grain-burnt inertia at the two ends) failed by 0.57 Hz: a check-definition "
                                  "error, kept in the file; the published band is reproduced with the mid-burn inertia")
    # Monte Carlo set
    if MS:
        cs = MS["cases"]
        rows = {c: rcsv(os.path.join(MV2MC, f"mc6_runs_{c}_m2.csv")) for c in cs}
        base = rows.get("m2_J1.6")
        tab = {}
        for c, e in cs.items():
            r = rows.get(c) or []
            st = mc_case(r) if r else {}
            st.update(note=e.get("note"), fail_modes=e["summary"]["fail_modes"])
            if base and c != "m2_J1.6" and r:
                st["vs_m2_J1.6"] = pr(pair(base, r), "m2_J1.6")
            if r:
                sat = col(r, "act_sat_max_dur")
                st["ENG07b_pass"] = bool(np.nanmax(sat) <= LEAD3["eng07b_max_episode_s"] + 1e-9)
            tab[c] = st
        out["monte_carlo"] = P(rnd(tab, 4), "SIM m2_mechv2_mc (sim6 v2.6 on iface_v3c, 500 runs, seed 101, A-D 300 m, N2O 2.00 kg, "
                                             "v3 FSW with the ratchet, NC-closed relight, 6.6 V as-drawn chain, n 4.8)",
                               "mechanical.json v2 axis stiffness drawn U(552.5, 1681) N m/rad (FEA structure + rods in series with the "
                               "ASSUMED servo), hose U(1.73, 17.48) N m/rad, mount damping U(0.02, 0.10); notch Q1 -12 dB centred on the "
                               "run's landing-burn rocking mode x mistune U(1 -/+ w); 'tgt' = structure at the lead target 3,100-5,200 in "
                               "series with the servo range", K_s_engine_axis=MS.get("K_s_engine_axis"), K_target_series=MS.get("K_target_series"),
                               J_central=MS.get("J_central"), J_upper=MS.get("J_upper"))
    # CSI frequency target on the mechanical.json v2 mass properties
    ft = (CSI3 or {}).get("ftarget")
    if ft:
        pat = lambda rows, key: "".join("+" if r[key]["pass_6dB"] else "-" for r in rows)  # noqa: E731
        cases = {k: dict(f_min_floor20_Hz=v["f_min_Hz"]["floor20"], f_min_all_Hz=v["f_min_Hz"]["all"], f_min_62N_only_Hz=v["f_min_Hz"]["f62"],
                         pattern_floor20=pat(v["rows"], "floor20"), pattern_all=pat(v["rows"], "all"),
                         unstable_corners_floor20=[r["floor20"]["n_unstable"] for r in v["rows"]],
                         gm_min_floor20_dB=[r["floor20"]["gm_up_min_dB"] for r in v["rows"]])
                 for k, v in ft["cases"].items()}
        out["csi_frequency_target"] = P(rnd({"f_grid_Hz": ft["f_grid_Hz"], "zeta": ft["zeta"], "variants": ft["variants"],
                                             "rigid_pm_min_deg": {k: v["pm_min_deg"] for k, v in ft["rigid"].items()},
                                             "cases": cases, "stiffness_for_floor20_f_min": ft.get("stiffness_for_floor20_f_min"),
                                             "I_piv_landing_kgm2": ft.get("I_piv_landing_kgm2")}, 3),
                                        "SIM m2_csi_v3 v1.3 ftarget on iface_v3c (python-control; mechanical.json v2 mass properties)",
                                        "lowest rocking-mode frequency (engine on its powered servos, rotor included) above which every "
                                        "corner keeps >= 6 dB; 'floor20' = corners at the 20 % floor and above, 'all' adds the 12.5 % "
                                        "floor; pattern: one character per grid frequency (+ = all corners >= 6 dB); wn0.75 = landing "
                                        "attitude bandwidth x 0.75")
    # lead-adopted structure target reproduced on mechanical.json v2
    ta = mech["tvc_actuation"]
    n = ta["gear_ratio_n"]["v"]
    Ks = el["actuators"]["tvc_A"]["stiffness"]["v"]["servo_output_Nm_per_rad"]
    J = relay["J_int_servo_output_kgm2"]["v"]["central"]
    Ipl = mech["gimballed_mass_properties"]["end_of_max_thrust_case"]["I_pivot_kgm2"]["v"][0][0]
    kt = {}
    for lab, f in (("22 Hz (notch tuned +/-5 % on the B-TVC-1 mode)", 22.0), ("25 Hz (fixed per-axis notch +/-15 %, or low-pass with "
                                                                             "mount damping >= 0.05)", 25.0)):
        Kt = (2 * np.pi * f) ** 2 * (Ipl + J * n * n)
        kt[lab] = dict(K_total_Nm_per_rad=Kt, **{f"K_struct_at_K_s_{k:g}": (None if Kt >= k * n * n else 1.0 / (1.0 / Kt - 1.0 / (k * n * n)))
                                                for k in (Ks[0], 0.5 * (Ks[0] + Ks[1]), Ks[1])})
    hose_frac = LEAD_V3["hose_K_max_Nm_per_rad"] / kt[list(kt)[0]]["K_total_Nm_per_rad"]
    out["stiffness_target"] = P(rnd({"adopted_Nm_per_rad": {"hard_minimum_every_pose": LEAD_V3["K_struct_min_Nm_per_rad"],
                                                            "goal": LEAD_V3["K_struct_goal_Nm_per_rad"]},
                                     "recomputed_on_mechanical_v2": kt, "I_pivot_landing_kgm2": Ipl, "J_int_kgm2": J, "n": n,
                                     "K_s_output_Nm_per_rad": Ks,
                                     "mechanical_v2_published_total_Nm_per_rad": ta["axis_stiffness_Nm_per_rad"]["v"],
                                     "mechanical_v2_rocking_Hz_excl_J": ta["rocking_mode_Hz"]["v"],
                                     "mechanical_v2_rocking_Hz_with_J_lumped": [float(np.sqrt(k / (Ipl + J * n * n)) / (2 * np.pi))
                                                                                for k in ta["axis_stiffness_Nm_per_rad"]["v"]],
                                     "hose_parallel_effect": {"K_max_Nm_per_rad": LEAD_V3["hose_K_max_Nm_per_rad"],
                                                              "fraction_of_K_total_at_22Hz": hose_frac,
                                                              "frequency_raise_frac": float(np.sqrt(1 + hose_frac) - 1)}}, 4),
                                "REQ lead 2026-10-12 (adopted GNC target) + DERIVED here on mechanical.json v2",
                                "K_total = (2 pi f)^2 (I_piv + J n^2), 1/K_struct = 1/K_total - 1/(K_s n^2), rotor lumped on the engine "
                                "(conservative; a 2-mass rotor needs ~0.46 x the structure K at J 1.6e-3, K_s 174, 25 Hz). The hard "
                                "minimum is the 22 Hz case at K_s 174 (top of the ASSUMED servo range), the goal the 25 Hz case; at "
                                "K_s 58 neither frequency is reachable at any structure K (servo alone too soft): B-TVC-1 gate. The "
                                "hose (<= 20 N m/rad, parallel) raises the mode by < 1 % and is left out of the target (conservative)")
    if NS:
        rows_ = []
        for r in NS["rows"]:
            k22 = r["K_struct_min"]["22 Hz (notch tuned +/-5 %)"]
            k25 = r["K_struct_min"]["25 Hz (notch +/-15 % or LPF zeta >= 0.05)"]
            rows_.append(dict(n=r["n"], slew_7deg_7V4_dps=r["slew_7deg_7V4_dps"],
                              ENG07_pass=bool(r["slew_7deg_7V4_dps"] >= LEAD3["eng07_min_slew_dps_at_7V4"]),
                              K_struct_22Hz_at_K_s_58_116_174=[k22["K_s_58"], k22["K_s_116"], k22["K_s_174"]],
                              K_struct_25Hz_at_K_s_58_116_174=[k25["K_s_58"], k25["K_s_116"], k25["K_s_174"]],
                              K_s_min_rigid_structure_22_25Hz=[k22["K_s_min_rigid_structure"], k25["K_s_min_rigid_structure"]]))
        out["linkage_ratio_sweep"] = P(rnd(rows_, 1), "DERIVED m2_n_sweep v1 (CSI-only, lumped rotor, J 1.6e-3; slew extrapolated "
                                                         "from the as-built n 4.8 kinematics)",
                                       "lead request (low priority): a higher n barely lowers the structure K needed at K_s >= 116 "
                                       "(the rotor term J n^2 grows with n), lowers the servo-stiffness floor ~20 % at n 6, and "
                                       "fails ENG-07 above n ~5.2: n 4.8 confirmed (lead 2026-10-12). Mechanical's exact kinematics "
                                       "supersede the slew extrapolation")
    # landing bandwidth x 0.75 (fallback branch at the B-TVC-1 gate) on both bases
    wn = {}
    if MS:
        rows_b = rcsv(os.path.join(MV2MC, "mc6_runs_m2_J1.6_m2.csv"))
        for c in ("m2_J1.6_wn4.5", "m2_J1.6_wn4.5_n15", "m2_J1.6_wn4.5_rt", "m2_J1.6_wn4.5_rt_n15"):
            r = rcsv(os.path.join(MV2MC, f"mc6_runs_{c}_m2.csv"))
            if r and rows_b:
                st = mc_case(r)
                st["vs_m2_J1.6"] = pr(pair(rows_b, r), "m2_J1.6 (wn 6.0)")
                st["note"] = MS["cases"].get(c, {}).get("note")
                wn[f"mech_v2|{c}"] = st
    rb = rcsv(os.path.join(CF, "mc6_runs_cf_J1.6_acc2000_ref40_cf.csv"))
    for c in ("cf_J1.6_acc2000_ref40_wn4.5", "cf_J1.6_acc2000_ref40_wn5"):
        r = rcsv(os.path.join(CF, f"mc6_runs_{c}_cf.csv"))
        if r and rb:
            st = mc_case(r)
            st["vs_cf_J1.6_acc2000_ref40"] = pr(pair(rb, r), "cf_J1.6_acc2000_ref40 (wn 6.0)")
            wn[f"mech_v1|{c}"] = st
    if wn:
        ft_ = (CSI3 or {}).get("ftarget", {}).get("cases", {})
        fmn = lambda k: (ft_.get(k, {}).get("f_min_Hz") or {}).get("floor20")  # noqa: E731
        wn["linear_frequency_target_floor20_Hz"] = {
            "low_pass_only_zeta_0.02_0.05_0.10": {"wn_6.0": [fmn(f"lpf50|z{z}") for z in ("0.02", "0.05", "0.1")],
                                                  "wn_4.5": [fmn(f"lpf50_wn0.75|z{z}") for z in ("0.02", "0.05", "0.1")]},
            "notch_tuned_5pct": {"wn_6.0": fmn("lpf50+notchQ1-12_mis5|z0.02"), "wn_4.5": fmn("lpf50+notchQ1-12_mis5_wn0.75|z0.02")},
            "notch_fixed_15pct": {"wn_6.0": fmn("lpf50+notchQ1-12_mis15|z0.02"), "wn_4.5": fmn("lpf50+notchQ1-12_mis15_wn0.75|z0.02")}}
        out["reduced_bandwidth_fallback"] = P(rnd(wn, 4), "SIM m2_mechv2_mc v1.1 (v3c) + m2_ctrlfix (v3b), same 500 draws; DERIVED "
                                                         "m2_csi_v3 ftarget (v3c)",
                                              "(1) gain change only: landing attitude bandwidth 6.0 -> 4.5 rad/s (x 0.75) or 5.0 rad/s "
                                              "with every other gain unchanged loses landings (touchdown angular rate > 10 deg/s, "
                                              "lateral speed): the outer lateral loops are then too close to the slower attitude loop. "
                                              "(2) '_rt' = the lateral PD bandwidth and the terminal lateral-velocity gain re-tuned by "
                                              "the same 0.75: most of the loss is recovered (residual failures: lateral speed at "
                                              "touchdown). (3) The linear frequency target is unchanged with the notch (22 / 25 Hz) and "
                                              "relaxes only for the low-pass-only case at mount damping 0.10. Reduced bandwidth is a "
                                              "degraded landing mode, not a closure of ENG-07d: with a servo below the B-TVC-1 gate "
                                              "(K_s 58 N m/rad: rocking mode <= ~19 Hz even on a rigid structure, rotor lumped) no "
                                              "variant reaches its target; the actuator contingency is the gate fallback")
    out["eng07_slew_load_check"] = eng07_load(mech, mechB, NS)
    return out


def hinge_terms(m):
    ta = m.get("tvc_actuation") or {}
    t = ta.get("hinge_moment_terms_Nm")
    if t is None:
        for v in m.values():
            if isinstance(v, dict) and "hinge_moment_terms_Nm" in v:
                t = v["hinge_moment_terms_Nm"]
    out = {}
    for k, v in (t or {}).items():
        x = v["v"]
        out[k] = max(x) if isinstance(x, list) else x
    return out


def eng07_load(mech, mechB, NS):
    t2 = hinge_terms(mech)
    t1 = hinge_terms(mechB) if mechB else {}
    s2 = sum(abs(v) for k, v in t2.items() if not k.startswith("inertia_"))
    s1 = sum(abs(v) for k, v in t1.items() if not k.startswith("inertia_")) if t1 else None
    hose2 = max((v for k, v in t2.items() if k.startswith("hose")), default=0.0)
    hose_rule = LEAD_V3["hose_K_max_Nm_per_rad"] * np.radians(7.0)
    s_rule = s2 - hose2 + hose_rule
    d = {"non_inertial_sum_mech_v1_Nm": s1, "non_inertial_sum_mech_v2_Nm": s2, "hose_term_mech_v2_upper_Nm": hose2,
         "hose_at_routing_limit_7deg_Nm": hose_rule, "non_inertial_sum_with_hose_at_limit_Nm": s_rule,
         "mechanical_v2_rate_table_load_Nm": 3.19 if "rate_engine_dps_under_3.19Nm" in mech["tvc_actuation"] else None}
    if NS:
        d["slew_7deg_7V4_worst_dps"] = {"under_3.19_Nm (mechanical.json v2 table)": slew_vs_load(NS, 3.19),
                                         "under_mech_v2_sum": slew_vs_load(NS, s2), "under_sum_with_hose_at_limit": slew_vs_load(NS, s_rule),
                                         "sensitivity_dps_per_Nm": slew_vs_load(NS, 1.0) - slew_vs_load(NS, 0.0)}
    return P(rnd(d, 3), "DERIVED from mechanical.json v1/v2 hinge_moment_terms_Nm + the m2_n_sweep torque-speed calibration",
             "mechanical.json v2 rate table is computed under 3.19 N m = the v1 non-inertial sum (Electronics tvc_slew_check_v1); the "
             "v2 terms sum to more (hose upper term 0.24 -> 2.14 N m). GNC's linear torque-speed extrapolation puts the worst-direction "
             "slew at 7 deg / 7.4 V on the ENG-07 line with the v2 sum and below it with the hose at the 20 N m/rad routing limit. "
             "The conservative linear sum (all terms at their maxima together) is Mechanical's/Electronics' check to redo with "
             "the exact kinematics; the 6-DOF flies the hose stiffness U(1.73, 17.48) N m/rad at 6.6 V and keeps P (monte_carlo)")


# ---------------------------------------------------------------------------------------------------------- vehicle and ICD
def vehicle_v3d(VH, TWD, v2rv):
    if not VH:
        return v2rv, None
    rv = copy.deepcopy(v2rv)
    rv["name"] = ("RV-1c (GNC reference vehicle on mechanical.json v2, ledger v3d, parametric; real airframe owner: Lauty): CAD v3.3 "
                  "engine module + fixed TVC module, uniform 146 mm body")
    rv["mass_ledger_csv"] = f"{HUB}/vehicle/mass_ledger_v3d.csv"
    s = VH["sums"]
    rv["dry_mass_kg"] = P(rnd(s["dry_kg"], 3), "DERIVED mass ledger v3d (mechanical.json v2 engine + fixed TVC module; ASSUMED airframe, "
                                               "legs, avionics, recovery)",
                          f"range {s['dry_min_kg']:.2f}-{s['dry_max_kg']:.2f} kg (item min/max); propulsion {s['propulsion_kg']:.2f} kg, "
                          f"airframe {s['airframe_kg']:.2f} kg; MC disperses dry mass N(1, 0.05)")
    rv["fuel_grain_mass_kg"] = P(rnd(VH["grain_kg_in_tables"], 4), f"combustion.json {VH.get('combustion_json')} grain")
    rv["n2o_load_kg"] = P(VH["n2o_load_kg"], "REQ lead decision 2026-10-12 (tank 2.00 kg / 3.17 L; OI-1 option (a))")
    rv["tank_volume_L"] = P(rnd(VH["tank_V_L"], 3), "REQ lead decision 2026-10-12", f"internal length {VH['tank_internal_length_m']:.3f} m")
    rv["liftoff_mass_kg"] = P(rnd(VH["m_liftoff_kg"], 3), "SIM nominal A1 flight (ledger v3d + 2.00 kg, roll RCS provision only)",
                              "A1 with nose drogue + fins; the finless B hops lift off 0.65 kg lighter (propellant_closure_v3.table)")
    rv["landing_mass_kg"] = P(rnd(VH["m_land_nominal_kg"], 3), "SIM nominal A1 flight")
    rv["mass_properties_vs_time"] = {"events": rnd(VH["events"], 4), "vs_propellant_state_csv": f"{HUB}/vehicle/massprops_vs_propellant_v3d.csv",
                                     "full_histories": "every duty-cycle CSV v3 carries m_kg, z_cg_m, I_transverse_kgm2, I_roll_kgm2",
                                     "tag": f"SIM {VH.get('sim')} nominal A1 flight (no wind) + DERIVED vehicle.massprops"}
    rv["liquid_level_cg_shift"] = P(rnd({"full_load_forward_minus_aft_m": VH["cg"]["liquid_forward_excursion_full_m"],
                                         "at_MECO_m": VH["cg"]["liquid_forward_excursion_meco_m"],
                                         "liquid_at_MECO_kg": VH["cg"]["meco_liquid_kg"]}, 4),
                                    "DERIVED vehicle.massprops (liquid column forward vs settled aft)")
    tw = {f"{r['state']}|{r['F_label']}": r for r in TWD}
    td20 = tw.get("touchdown|20.0 %") or {}
    rv["gimballed_subassembly"] = P({"pivot": "mechanical.json v2 RV-1 station of the pivot (CAD v3.3)", "z_pivot_m": VH["z_pivot_m"],
                                     "touchdown_state": {k: rnd(float(td20[k]), 5) for k in ("m_e_kg", "z_e_m", "l_e_m", "I_e_own_kgm2",
                                                                                            "J_twd_kgm2", "l_p_m", "I_transverse_kgm2") if k in td20},
                                     "tail_wags_dog_zero_rad_s": {k: rnd(float(r["w_twd_rad_s"]), 2) for k, r in tw.items()},
                                     "control_moment_per_deg_Nm": {k: rnd(float(r["Mc_per_deg_Nm"]), 3) for k, r in tw.items()},
                                     "table_csv": f"{HUB}/vehicle/twd_table_v3d.csv"},
                                    "DERIVED vehicle.massprops + mechanical.json v2 (gimballed mass/inertia, grain from combustion.json)",
                                    "l_p = z_cg - z_pivot; l_e = z_pivot - z_e; J_twd = I_e + m_e l_e (l_e + l_p); w_twd = sqrt(F l_p / J_twd)")
    ae = VH.get("aero", {})
    if ae:
        a = rv.get("aero", {})
        a["static_table_csv"] = f"{HUB}/vehicle/aero_static_v3d.csv"
        nf = ae.get("fins1_nominal_legs0", {})
        a["nose_first_fins"] = P({k: nf.get(k) for k in ("CNa_nose_first_per_rad", "z_cp_nose_first_2deg_m", "static_margin_nose_first_cal")},
                                 "DERIVED aero.py (2 deg, v3d liftoff CG)")
        n0 = ae.get("fins0_nominal_legs0", {})
        a["nose_first_finless"] = P({k: n0.get(k) for k in ("CNa_nose_first_per_rad", "z_cp_nose_first_2deg_m", "static_margin_nose_first_cal")},
                                    "DERIVED aero.py", "finless body is statically UNSTABLE nose-first (A2 tumbles)")
        rv["aero"] = a
    rv["geometry_v3d"] = P({"z_pivot_m": VH["z_pivot_m"], "d_body_m": VH["d_body_m"], "tank_internal_length_m": VH["tank_internal_length_m"]},
                           "DERIVED ledger v3d (mechanical.json v2 pivot; ASSUMED airframe)")
    return rv, tw


def lp_min(tw_row, w_min, F):
    """smallest CG height above the pivot that keeps the tail-wags-dog zero >= w_min at thrust F (engine state of the row)."""
    m_e, l_e, I_e = float(tw_row["m_e_kg"]), float(tw_row["l_e_m"]), float(tw_row["I_e_own_kgm2"])
    den = F - w_min ** 2 * m_e * l_e
    return w_min ** 2 * (I_e + m_e * l_e * l_e) / den if den > 0 else None


def plume_cone(comb):
    """DERIVED near-field jet-boundary angle at max thrust from combustion.json (frozen-gamma isentropic + Prandtl-Meyer)."""
    g = comb["operating_points"]["max_thrust"]["gamma_chamber"]["v"]
    eps = comb["gas_path"]["nozzle"]["expansion_ratio"]["v"]
    pe_pa = comb["gas_path"]["nozzle"]["pe_over_pa_at_max"]["v"]
    re = 0.5 * comb["gas_path"]["nozzle"]["exit_diameter_m"]["v"]
    cpath = comb["gas_path"]["nozzle"].get("contour_csv")
    th_e = None
    if cpath and os.path.exists(cpath):
        rows = [r for r in csv.reader(open(cpath)) if r and not r[0].startswith("#")][1:]
        cone = [(float(r[0]), float(r[2])) for r in rows if r[3].startswith("div")]
        if len(cone) >= 2:
            th_e = float(np.degrees(np.arctan((cone[-1][1] - cone[-2][1]) / (cone[-1][0] - cone[-2][0]))))

    def ar(M):
        return (1.0 / M) * ((2.0 / (g + 1.0)) * (1.0 + 0.5 * (g - 1.0) * M * M)) ** ((g + 1.0) / (2.0 * (g - 1.0)))

    def nu(M):
        a = np.sqrt((g + 1.0) / (g - 1.0))
        return a * np.arctan(np.sqrt((M * M - 1.0) / (a * a))) - np.arctan(np.sqrt(M * M - 1.0))
    Me = brentq(lambda M: ar(M) - eps, 1.0001, 10.0)
    p0_pe = (1.0 + 0.5 * (g - 1.0) * Me * Me) ** (g / (g - 1.0))
    p0_pa = p0_pe * pe_pa
    Mj = np.sqrt(2.0 / (g - 1.0) * (p0_pa ** ((g - 1.0) / g) - 1.0))
    dnu = float(np.degrees(nu(Mj) - nu(Me)))
    return dict(gamma=g, expansion_ratio=eps, pe_over_pa=pe_pa, Me=float(Me), Mj=float(Mj), turning_deg=dnu,
                nozzle_half_angle_deg=th_e, boundary_angle_deg=(th_e or 0.0) + dnu, exit_radius_m=re)


def icd_v3(VH, tw, g2icd, PC2, MS, DCI, comb, mech, cfe_note, planning_v=None, ABS=None, RSSJ=None, RL=None):
    icd = {}
    icd["about"] = ("GNC inputs to the airframe ICD (ICD-AIRFRAME.md, compiled by the lead with Mechanical's section). Self-contained: "
                    "every entry carries its value, tag and source. Airframe values that GNC ASSUMED for its reference vehicle RV-1c are "
                    "listed so the real airframe (owner: Lauty) can be checked against them; where it differs GNC re-runs the affected "
                    "checks. Nothing here is a fabrication drawing or a tolerance stack.")
    icd["frames_and_units"] = P("SI (m, kg, s, N, Pa); stations z [m] from the airframe aft datum (base plane), +z toward the nose; body "
                                "x_b, y_b = gimbal axes; CAD +Z up with STEP in mm; GLB +Y up in m (visualisation only)",
                                "REQ project conventions (AGENTS.md)")
    if VH:
        geo = VH
        icd["reference_vehicle_assumed"] = P({"length_overall_m": 2.03, "body_diameter_m": geo["d_body_m"], "body_inner_diameter_m": geo.get("d_id_m"),
                                              "nose": "tangent ogive, L 0.30 m", "body": "uniform diameter (a stepped 146/126 mm airframe is "
                                              "Lauty's option: mass and aero change)", "pivot_station_m": geo["z_pivot_m"],
                                              "tank_internal_length_m": geo["tank_internal_length_m"]},
                                             "ASSUMED airframe (length, nose, uniform body) + DERIVED (body from the >= 140 mm engine bay "
                                             "+ 2 x 3 mm wall; pivot from mechanical.json v2)",
                                             "REQUIREMENTS reference vehicle ~2.0 m + 0.03 m nozzle protrusion")
        ev = {e["event"]: e for e in VH["events"]}
        icd["mass_and_cg"] = P(rnd({
            "liftoff_mass_kg": {"A1_drogue_fins": VH["m_liftoff_kg"],
                                "B_hops_no_drogue_no_fins": (PC2 or {}).get("closure", {}).get("B1", {}).get("at_2kg", {}).get("m_liftoff")},
            "dry_mass_kg": VH["sums"]["dry_kg"], "n2o_kg": VH["n2o_load_kg"], "fuel_grain_kg": VH["grain_kg_in_tables"],
            "landing_mass_nominal_A1_kg": VH["m_land_nominal_kg"],
            "cg_z_at_events_m": {k: ev[k]["z_cg_m"] for k in ev},
            "cg_z_flight_range_m": VH["cg"]["flight_history_m"], "cg_z_dry_nominal_m": VH["cg"]["dry_nominal_m"],
            "cg_z_dry_ledger_extremes_m": VH["cg"]["ledger_extremes_dry_m"],
            "liquid_forward_excursion_m": VH["cg"]["liquid_forward_excursion_full_m"],
            "I_transverse_at_events_kgm2": {k: ev[k]["I_transverse_kgm2"] for k in ev}}, 4),
            "SIM nominal A1 flight (ledger v3d, 2.00 kg) + DERIVED ledger", "full mass history in the duty-cycle CSVs v3")
        m_air = VH["sums"]["airframe_kg"]
        sig_cg = 0.03 * m_air / VH["m_liftoff_kg"]
        lp = {}
        for st, F in (("touchdown|12.5 %", 62.5), ("touchdown|20.0 %", 100.0)):
            r = (tw or {}).get(st)
            if r:
                lp[st] = dict(l_p_min_m=lp_min(r, 20.0, F), l_p_flown_m=float(r["l_p_m"]), z_cg_min_m=(lp_min(r, 20.0, F) or 0.0) + VH["z_pivot_m"])
        icd["cg_and_length_limits"] = P(rnd({
            "cg_height_above_pivot_min_m": lp,
            "rule_cg_above_pivot": "tail-wags-dog zero >= 20 rad/s at the lowest flown thrust (requirements.structure."
                                   "tail_wags_dog_zero_min_rad_s): l_p >= w^2 (I_e + m_e l_e^2) / (F - w^2 m_e l_e)",
            "axial_cg_band_verified_m": [VH["cg"]["liftoff_m"] - 3 * sig_cg, VH["cg"]["liftoff_m"] + 3 * sig_cg],
            "axial_cg_1sigma_flown_m": sig_cg,
            "lateral_cg_offset_max_m": 0.006, "thrust_axis_misalignment_max_deg": 0.25, "dry_mass_band_verified_frac": [0.85, 1.15],
            "transverse_inertia_band_verified_frac": [0.85, 1.15],
            "length_overall_m": 2.03, "airframe_first_bending_min_Hz": 10.0, "airframe_first_bending_goal_Hz": 15.0}, 4),
            "DERIVED from the requirements and the MC dispersions GNC has flown (3 sigma): airframe items shifted N(0, 30 mm), "
            "lateral CG N(0, 2 mm) per axis, thrust misalignment U(-0.25, 0.25) deg per axis, dry mass N(1, 0.05)",
            "an airframe outside these bands is not necessarily unflyable: GNC re-runs the Monte Carlo on it. Length 2.03 m is the "
            "ASSUMED reference; the limits that matter are the CG band, the inertia band and the first bending mode")
    icd["landing_mass_window_kg"] = g2icd.get("landing_mass_window_kg")
    icd["touchdown_envelope"] = P({"vertical_speed_max_mps": 2.0, "lateral_speed_max_mps": 0.5, "tilt_max_deg": 5.0, "tilt_rate_max_dps": 10.0},
                                  "REQ brief", "MC p99 of the v3 baseline in landing_closure_v3; legs and feet are designed to this "
                                               "envelope (+ the leg design values below)")
    icd["leg_design_values"] = P({"n_legs": 4, "stroke_min_m": 0.10, "k_per_leg_N_m": 2500.0, "c_per_leg_N_s_m": 120.0,
                                  "foot_radius_m": 0.40, "ground_friction_mu": [0.3, 0.7], "deploy": "at relight command (A) / fixed (B)"},
                                 "ASSUMED (as simulated; MC disperses k, c x U(0.8, 1.2))",
                                 "peak total leg force: landing_closure_v3 (MC p99/max); Lauty designs the legs")
    led = {r["item"]: r for r in rcsv(os.path.join(VEH3, "mass_ledger_v3d.csv"))} if VH else {}
    led_d = next((r for k, r in led.items() if k.startswith("A09")), None)
    led_b = next((r for k, r in led.items() if k.startswith("A07")), None)
    a1n = ((PC2 or {}).get("closure", {}).get("A1", {}).get("at_2kg") or {})
    evd = {e["event"]: e for e in (VH or {}).get("events", [])}
    m_apo = (evd.get("apogee") or {}).get("m_kg")
    m_lo = a1n.get("m_liftoff") or (VH or {}).get("m_liftoff_kg")
    g0 = 9.80665
    icd["drogue"] = P(rnd({
        "CdA_m2": 0.5, "CdA_band_verified_m2": [0.5 * 0.85, 0.5 * 1.15],
        "canopy": "ASSUMED 0.9 m drogue class (Cd x area = 0.5 m2); canopy type, Cd, material and packing are the recovery "
                  "designer's",
        "bay": {"location": "nose bay, forward of the avionics; ejection forward along the vehicle axis",
                "ledger_station_z_m": float(led_d["z_m"]) if led_d and led_d.get("z_m") else None,
                "ledger_mass_kg": [float(led_d[k]) for k in ("m_kg", "m_min_kg", "m_max_kg")] if led_d and led_d.get("m_kg") else 0.35,
                "volume": "NOT a GNC number: sized by recovery / airframe for the chosen canopy and line"},
        "ejection": {"command": "FC at apogee (navigation vertical velocity changes sign in the coast, A1 only)",
                     "gnc_model": "line taut and canopy at its CdA at the apogee instant (quasi-steady, massless canopy, no "
                                  "inflation time); the deploy-to-inflation delay is NOT modelled (open item)",
                     "method": "spring / gas / pyro: airframe and recovery choice (no GNC constraint beyond timing)"},
        "line_and_swivel": {"attachment": "single line at the nose tip on the vehicle axis",
                            "swivel": "REQUIRED between line and vehicle: the 6-DOF assumes the line carries no roll torque",
                            "routing": "no bridle leg, line or lanyard along the body toward the engine bay (plume_line_clearance_rule)"},
        "release": {"command": "on Pc-confirmed relight: model releases when thrust > 50 % of the floor thrust; flight software "
                               "rule Pc >= 50 % of the floor Pc",
                    "load_case": "opens under the full steady line load (below)",
                    "released_mass_max_kg": "0.78 at CdA 0.5 m2 (terminal speed <= 5 m/s; plume_line_clearance_rule)"},
        "descent_speed_at_relight_mps": abs(a1n.get("v_ign")) if a1n.get("v_ign") is not None else None,
        "steady_line_load_N": {"at_apogee_mass": g0 * m_apo if m_apo else None, "upper_bound_liftoff_mass": g0 * m_lo if m_lo else None},
        "opening_load": "NOT computed by GNC (inflation not modelled; deployment at apogee at low airspeed): recovery designer",
        "backup_recovery_parachute": {"ledger_mass_kg": [float(led_b[k]) for k in ("m_kg", "m_min_kg", "m_max_kg")] if led_b and led_b.get("m_kg") else 0.75,
                                      "ledger_station_z_m": float(led_b["z_m"]) if led_b and led_b.get("z_m") else None,
                                      "note": "ASSUMED ledger item (deployment logic and canopy not designed by GNC)"}}, 3),
        "DERIVED descent ~22 m/s at the A1 relight (SIM nominal A1, MC x U(0.85, 1.15) on CdA) + REQ sequence + ASSUMED ledger v3d",
        "steady line load = descent weight; snatch / opening load, canopy selection, bay volume and the ejection method are "
        "recovery / airframe (Lauty) items")
    pc = plume_cone(comb)
    icd["plume_line_clearance_rule"] = P(rnd({
        "drogue_line": ["the line attaches only at the nose tip on the vehicle axis (swivel + release); no bridle leg, line or "
                        "release lanyard runs along the body toward the engine bay",
                        "release only on Pc-confirmed relight: the vehicle then decelerates away from the released drogue "
                        "(relative speed ~ the 20 m/s descent speed), so the line never crosses the plume while attached",
                        "released parts (canopy + line + released fitting) must descend slower than the vehicle: terminal speed "
                        "<= 5 m/s, i.e. released mass <= rho CdA v^2 / (2 g) = 0.78 kg at CdA 0.5 m2 (0.35 kg budgeted)",
                        "release failure: the canopy stays attached; in the last seconds the vehicle descends slower than the "
                        "canopy's own terminal speed and the canopy can fall back toward the vehicle: verify the release on the T4 "
                        "drop tests and the T0 bench (open item)"],
        "aft_structure_keep_out": {"rule": "no leg, foot, fin, line or antenna inside the cone r(x) = r_e + x tan(theta) aft of the "
                                           "nozzle exit plane, theta = jet-boundary angle + 7 deg gimbal, for x <= 10 exit diameters",
                                   "theta_deg": pc["boundary_angle_deg"] + 7.0, "r_e_m": pc["exit_radius_m"],
                                   "x_max_m": 10.0 * 2.0 * pc["exit_radius_m"], "derivation": pc},
        "ground_impingement": "NOT covered: the hover and touchdown plume on the ground (radial wall jet onto the feet) has no "
                              "GNC or 05-plume-cfd source (no ground-plane case); request to Combustion/plume CFD"}, 3),
        "DERIVED GNC (flight sequence + combustion.json v2.3 nozzle: frozen-gamma isentropic expansion and Prandtl-Meyer "
        "turning at the lip) - not validated", "the jet-boundary angle is the initial turning at the lip at max thrust (sea "
        "level, under-expanded); the boundary curves back downstream, so the cone over-covers the near field; it is a keep-out "
        "for layout, not a thermal or load result")
    icd["fins"] = P({"count": 4, "span_m": 0.12, "root_chord_m": 0.20, "tip_chord_m": 0.10, "location": "aft end", "material_mass": "3 mm GF/PETG, 0.30 kg",
                     "static_margin_nose_first_cal_verified": (VH or {}).get("aero", {}).get("fins1_nominal_legs0", {}).get("static_margin_nose_first_cal")},
                    "DERIVED descent/coast trade (gnc.json v2) + aero.py at the v3d liftoff CG",
                    "rule: Lauty's fins must give at least the verified nose-first static margin at the liftoff CG, or GNC re-checks "
                    "the coast; the finless body is unstable nose-first (A2 tumbles); fins are destabilising tail-first (the drogue "
                    "sets the descent attitude)")
    icd["fin_alignment_cant_max_deg"] = g2icd.get("fin_alignment_cant_max_deg")
    icd["roll_rcs_mounting"] = g2icd.get("roll_rcs_mounting")
    rsp = ((RL or {}).get("monte_carlo") or {}).get("rl181_A1_none_k2") or ((RSSJ or {}).get("monte_carlo") or {}).get("rs_A1_seq+0.3_planned") or {}
    hcmd = rsp.get("relight_cmd_h_p01_p50_m") or [None, None]
    sq_ = (RL or {}).get("sequence") or {}
    ab = (ABS or {}).get("v", {})
    ab100 = next((r for r in ab.get("bracket", []) if abs(r["level_frac_Fmax"] - 1.0) < 1e-9), None)
    stuck = (ab.get("pintle_not_moving_bound") or {}).get("by_valve_close_time", {})
    stuck_rng = [min(v["impulse_upper_Ns_line_21cm3"] for v in stuck.values()), max(v["impulse_upper_Ns_line_21cm3"] for v in stuck.values())] if stuck else None
    icd["sequence_events_for_airframe"] = P(rnd({
        "liftoff_to_MECO": "full thrust under TVC, pre-MECO throttle-down to 72 %, MECO near 100 m at ~64 m/s (A1)",
        "coast": "nose-first, fins; NC isolation valve closed through the coast; drogue deploy at apogee",
        "descent": "under drogue, engine-down, ~22 m/s",
        "relight": (f"NC valve opened by the relight sequence (worst case {sq_.get('worst_s')} s valve command to Pc confirm, SIL "
                    f"nominal {sq_.get('sil_nominal_s')} s, Electronics firmware v2.7; planning value {planning_v} s = "
                    f"{R.DEF['t_ign_est']:g} s + worst case; an early light is an open GNC item), torch, start at max(floor, "
                    f"20 %); relight command at {hcmd[0]:.0f} m (MC p01) / {hcmd[1]:.0f} m (p50); drogue release on Pc confirmation; legs "
                    "deploy at the relight command; NO retry: a no-light is a mission loss and the drogue stays attached")
        if hcmd[0] is not None and planning_v else "NC valve opened by the relight sequence, torch, start at max(floor, 20 %)",
        "landing": "throttled TVC burn, 8 m terminal gate, touchdown ~1 m/s, engine cut on contact",
        "abort_any_phase": ("NC valve de-energised at once (spring closes the ball valve) + pintle closed in parallel + torch "
                            "solenoids closed (lead 2026-10-13)" + (f"; thrust tail-off from 100 %: <= {ab100['pintle_only_upper']['impulse_Ns']:.1f} N s, "
                                                                   f"10 % at {ab100['pintle_only_upper']['t10_s']:.2f} s with the pintle closing at the "
                                                                   "drive speed" if ab100 else "")
                            + (f"; if the pintle does not move (PINTLE_FAULT, servo unpowered): <= {stuck_rng[0]:.0f}-{stuck_rng[1]:.0f} N s "
                               "(valve close 0.10-0.15 s + the 21.4 cm3 line burned; flight_software.abort_shutdown)" if stuck_rng else ""))}, 3),
        "DESIGN GNC flight software v2.7 (provisional) + REQ lead decisions 2026-10-13 (flight_profile, flight_software)")
    rho0, g0_ = 1.225, 9.80665
    icd["upper_bay_venting"] = P({
        "status": "RECOMMENDED airframe feature (lead decision 2026-10-13, from Mechanical's servo-mount thermal network: the "
                  "stratified upper-bay air sets the servo soak; venting adds margin)",
        "owner": "airframe (Lauty) with Mechanical (vent area and location); GNC has no thermal model of the bay",
        "gnc_conditions": [f"barometer static ports outside the vent outflow and its wake: vent-induced static-pressure error at the "
                           f"ports <= {rho0 * g0_ * 1.0:.0f} Pa (= rho0 g x 1 m, the 1-sigma barometer error the 6-DOF flies: run6 "
                           "baro_bias N(0, 1 m), ASSUMED)",
                           "no vent inside the aft keep-out cone (plume_line_clearance_rule.aft_structure_keep_out); no drogue line "
                           "or lanyard across a vent",
                           "report the vent area and station: GNC re-checks the barometer error budget if the ports cannot be "
                           "placed clear of it"]},
        "REQ lead decision 2026-10-13 + DERIVED GNC conditions (rho0 1.225 kg/m3 ISA sea level, LITERATURE)")
    if DCI:
        icd["duty_cycles"] = P({"index": f"{HUB}/duty_cycles/duty_cycles_index_v3.json",
                                "current": [c["name"] for c in DCI.get("cycles", [])],
                                "sizing_cases_lead_2026-10-13": DCI.get("sizing_cases_lead_2026-10-13"),
                                "burn_time_definition": DCI.get("burn_time_definition"),
                                "max_axial_definition": DCI.get("max_axial_definition"),
                                "conservative_thermal_envelope_history": [c["name"] for c in DCI.get("retained_v2", []) if c["name"].startswith("DC-B1")]},
                               f"SIM duty cycles v3 (index revision {dci_rev(DCI)})", "thrust, mass, CG, inertia and gimbal histories for loads and thermal; "
                               "the dispersed p99 cycles are the sizing cases (DC-B1 v2 19 s is no longer conservative)")
    icd["open"] = ["airframe first bending mode and damping (Lauty FE model or tap test) replace the ASSUMED 10 Hz minimum",
                   "drogue opening load, canopy, release mechanism and swivel: recovery/airframe design; release verified in T0/T4",
                   "ground-plane plume case (feet and legs at touchdown): Combustion / 05-plume-cfd",
                   "tail-first aero (CNa, CP, base/plume interaction) unknown to ~x2: CFD, tunnel or drop data",
                   "upper-bay vent area and station (Mechanical / airframe) against the barometer static ports (upper_bay_venting)",
                   "relight sequence time: placeholder 0.8 + 0.3 s until Electronics publishes the worst-case value (the planning "
                   "value moves with it in the same release)"]
    return icd


# ---------------------------------------------------------------------------------------------------------- ENG-07d text
def eng07d_v3(MS, CSI3, NS, mech, el, relay, mvb, RL=None):
    cs = (MS or {}).get("cases", {})
    mc = (mvb or {}).get("monte_carlo", {}).get("v", {})
    stt = (mvb or {}).get("stiffness_target", {}).get("v", {})
    ft = (CSI3 or {}).get("ftarget", {})
    fm = lambda k: (ft.get("cases", {}).get(k, {}).get("f_min_Hz", {}) or {}).get("floor20")  # noqa: E731
    f_with_J = stt.get("mechanical_v2_rocking_Hz_with_J_lumped") or [None, None]
    Pm = lambda c: (mc.get(c) or {}).get("P")  # noqa: E731
    wn = (mvb or {}).get("reduced_bandwidth_fallback", {}).get("v", {})
    wn45 = wn.get("mech_v2|m2_J1.6_wn4.5", {})
    wn45rt = wn.get("mech_v2|m2_J1.6_wn4.5_rt", {})
    e = {}
    e["status"] = (
        "M2 v3 (2026-10-12): 6-DOF Monte Carlo (sim6/run6 v2.6, 500 runs per case, same draws) re-baselined on mechanical.json v2 + "
        "combustion.json v2.3 (iface_v3c) with flight software v2.6 (tracker, governor with ratchet, pre-MECO throttle-down, relight "
        "start rule, NC-closed relight). Lead decisions applied: OI-1 option (a) (tank 2.00 kg / 3.17 L; A1 300 m baseline; B1 85 m; "
        "B2 50 m; A2 removed, 2.20 kg / 3.49 L fallback documented), ratchet adopted, n 4.8 confirmed, ENG-07d structure target "
        "3,100 / 5,200 N m/rad with a REQUIRED per-axis notch and the B-TVC-1 gate. Paired flight-software evidence produced on "
        "iface_v3b (mechanical.json v1) is kept where it was produced and re-checked on v2 where it matters.")
    e["notch_spec"] = {"required": True, "per_axis": True,
                       "centre": "each axis on its own B-TVC-1 measured rocking mode (alpha and beta differ 8-15 %), engine on its powered "
                                 "servos with the rotor; re-measured after any linkage or servo change",
                       "Q": 1.0, "depth_dB": -12.0,
                       "tuning_tolerance": "within +/-5 % of the measured mode -> mode floor 22 Hz; a fixed centre known only to "
                                           "+/-15 % -> 25 Hz",
                       "placement": "ECU TvcShaper after the 50 rad/s 2nd-order low-pass, 1 kHz, RBJ peaking-EQ with finite depth",
                       "interlock": "IGNITE / RELIGHT refused unless both axes carry an enabled notch (Electronics firmware v2.6)"}
    e["notch_note"] = (f"6-DOF on mechanical.json v2 (J 1.6e-3): P {Pm('m2_J1.6')} without, {Pm('m2_J1.6_n15')} with the notch at "
                       f"+/-15 % and {Pm('m2_J1.6_n5')} at +/-5 % (identical outcomes): the published stiffness does not lose landings "
                       "in the 6-DOF; the notch is required by ENG-07d (linear margin) and lowers the delivered hinge moment")
    e["mode_req"] = P({"with_notch_tuned_5pct_Hz": fm("lpf50+notchQ1-12_mis5|z0.02"), "with_notch_fixed_15pct_Hz": fm("lpf50+notchQ1-12_mis15|z0.02"),
                       "low_pass_only_zeta_0.02_0.05_0.10_Hz": [fm("lpf50|z0.02"), fm("lpf50|z0.05"), fm("lpf50|z0.1")]},
                      "DERIVED SIM m2_csi_v3 ftarget on mechanical.json v2 (iface_v3c)",
                      "rocking mode of the engine on its powered servos INCLUDING the reflected rotor; the 12.5 % floor corners need "
                      "the low-pass-only value at zeta 0.02 in every variant (see mech_v2_rebaseline.csi_frequency_target)")
    e["k_target"] = P({"hard_minimum_every_pose": LEAD_V3["K_struct_min_Nm_per_rad"], "goal": LEAD_V3["K_struct_goal_Nm_per_rad"]},
                      "REQ lead 2026-10-12 (GNC target, structure + rods per axis, servo excluded)",
                      "22 Hz (notch tuned +/-5 %) and 25 Hz at K_s 174 N m/rad with J 1.6e-3 lumped (mech_v2_rebaseline.stiffness_target); "
                      "mechanical.json v2 publishes the total incl. the ASSUMED servo: 552.5-1681 N m/rad, i.e. "
                      f"{f_with_J[0]:.1f}-{f_with_J[1]:.1f} Hz with the rotor" if f_with_J[0] else "")
    e["damping"] = P(0.05, "DERIVED m2_csi_v3 ftarget (low-pass-only 25 Hz case) + SIM range flown U(0.02, 0.10)",
                     "B-TVC-1 measures it; below 0.05 the notch case applies")
    e["csi_summary"] = {"model": "m2_csi_v3 (python-control) pitch-plane loop with the rocking mode in the actuator path",
                        "f_target_m2": {k: fm(k) for k in ft.get("cases", {})}}
    e["eng07d_note"] = (
        "NOT MET by mechanical.json v2 as published (total K 552.5-1681 N m/rad with the ASSUMED servo: "
        + (f"{f_with_J[0]:.1f}-{f_with_J[1]:.1f} Hz with J 1.6e-3" if f_with_J[0] else "below the target")
        + "). Closure path adopted by the lead: structure + rods >= 3,100 N m/rad at every pose (5,200 goal), notch REQUIRED per "
          "axis, B-TVC-1 gate. The 6-DOF Monte Carlo on the published stiffness keeps P with or without the notch and ENG-07b; the "
          "linear model predicts margins below 6 dB and, at mount damping 0.02 without the notch, unstable corners below ~20 Hz: "
          "the 6-DOF does not reproduce that instability (kept as an open contradiction, csi_vs_6dof)")
    e["verdict"] = e["eng07d_note"]
    e["btvc1"] = {"measure": ["servo output stiffness K_s per servo (gate: >= ~100 N m/rad at the output, else the actuator "
                              "contingency)", "axis rocking mode and damping per axis on the powered servos with the engine "
                              "dummy (sets the notch centres)", "rotor inertia J_int and its split (lumped vs 2-mass: the 2-mass "
                              "rotor needs ~0.46 x the structure K)", "delivered angular acceleration and slew at 7 deg (6.6 / 7.4 V)",
                              "saturation episodes (ENG-07b)", "hose parallel stiffness (routing rule <= 20 N m/rad)"],
                  "gate_outcomes": {"K_s >= ~100 and mode >= 22 Hz with the tuned notch": "proceed",
                                    "K_s < ~100 N m/rad": "actuator contingency (stiffer servo; maxon ECX 22 M class, TO-QUOTE)",
                                    "reduced bandwidth": f"degraded mode only, not a gate fallback for a soft servo: x 0.75 as a gain "
                                                         f"change gives P {wn45.get('P')} ({wn45.get('vs_m2_J1.6')}); re-tuned with the "
                                                         f"lateral loops P {wn45rt.get('P')} ({wn45rt.get('vs_m2_J1.6')}); the linear "
                                                         "frequency target does not move with the notch (22 / 25 Hz) and the soft servo "
                                                         "alone caps the mode below it"}}
    slots = __import__("m2_meco_mc").NCS["slots"]
    t0 = R.DEF["t_ign_est"]
    add = LEAD_1013["relight_seq_add_s"]
    if RL:
        sq = RL["sequence"]
        e["planning_value"] = P(round(t0 + sq["worst_s"], 3),
                                "REQ lead decision 2026-10-13 (2): planning value = 0.6 s latest start delay + Electronics' worst-case "
                                "relight sequence (firmware v2.7 SIL, valve command -> Pc confirm)",
                                f"= {t0:g} s + {sq['worst_s']:g} s (1.15 s primed + 0.06 s bleed; SIL nominal {sq['sil_nominal_s']:g} s); "
                                f"replaces the {t0 + slots + add:g} s placeholder (0.6 + {slots:g} s NC-closed slots + {add:g} s) and the "
                                f"{t0 + slots:g} s of 2026-10-12; the planning value and the sequence time change together in one FSW / "
                                "ECU release (relight_planning_181)",
                                previous_placeholder_s=round(t0 + slots + add, 3), source=sq.get("source"))
    else:
        e["planning_value"] = P(round(t0 + slots + add, 3),
                                "REQ lead rule 2026-10-13 (planning value = latest start delay + Electronics' worst-case relight sequence "
                                "time) with the PLACEHOLDER sequence time (NC-closed sequence slots + lead placeholder) until Electronics "
                                "publishes it",
                                f"= {t0:g} s latest start delay + {slots:g} s combustion.json NC-closed sequence slots + {add:g} s lead placeholder; "
                                f"the MC draws U(0.2, 0.6) s + {slots + add:g} s. v3 of 2026-10-12 used {t0 + slots:g} s; the "
                                "planning value and the sequence time change together in one FSW / ECU release "
                                "(flight_software.relight_sequence_placeholder)")
    e["nc_note"] = (f"relight with the NC isolation valve closed through the coast: combustion.json sequence slots {slots:.2f} s + the lead's "
                    f"{add:g} s placeholder (2026-10-13) added to the start delay and to the planning value; Combustion ENG-04 torch "
                    "10 % / 90 % at 0.10 / 0.29 s holding the ignition lift until Pc > 3 bar; ECU PREPRESS unprimed 0.56 s fits inside "
                    "the 0.80 s slot (request: publish the worst-case sequence time). Cases in relight_nc_valve_closed were flown "
                    "on 2026-10-12 with the 0.8 s sequence (planning 1.4 s); the +0.3 s evidence is relight_sequence_placeholder")
    return e


# ---------------------------------------------------------------------------------------------------------- 2026-10-13 (v4)
def lead_decisions_1013():
    return P({
        "relight_planning_rule": "FSW relight planning value = 0.6 s (latest start delay) + Electronics' worst-case relight "
                                 "sequence time; the first placeholder 0.8 + 0.3 s (t_ign_add 1.1 s, t_ign_est 1.7 s) is superseded "
                                 "by decision (2) below and kept as evidence (relight_sequence_placeholder). WITHDRAWN by the lead "
                                 "later on 2026-10-13 for the v2.8 sequence (relight_planning_value_v2.8)",
        "relight_planning_value_1.81s": "decision (2): planning value 0.6 + 1.21 = 1.81 s (Electronics' worst-case relight sequence, "
                                        "firmware v2.7 SIL); re-run A1 paired at 1.81 s; the SIL nominal relight 0.76 s may serve as the "
                                        "lower end of the latency until Combustion's RC-03 distribution arrives (relight_planning_181)",
        "early_light_finding": "accepted and logged: lights earlier than planned lose P. Test (a) GNC hold-to-planned-light, paired on "
                               "the four bases, refuted if P is not restored or the reserve falls below 25 %; Electronics asked about "
                               "(b) a deterministic ignition instant (if feasible, test the 0.26-0.50 s Pc-confirm spread); adopt "
                               "whichever restores P, (b) preferred if both do. Superseded the same day by relight_v2.8_design ((b) "
                               "accepted; (a) research only if (b) restores P)",
        "early_light_sizing": "B1 governs thermal and erosion (21.8 s vs at most 9.12 s; head-end heat 31.9 vs 18.0 MJ/m2, lead "
                              "figures); no A1 thermal re-run for early lights; GNC publishes the early-light A1 p99 cycle as a record "
                              "once the fix is chosen",
        "over_thrust_abort": "firmware v2.7 flies open loop on Pc loss; an accelerometer over-thrust abort is added on the CAN frame "
                             "FC_THRUST (ID 0x024, >= 100 Hz, sequence, accelerometer thrust in 0.1 N steps, valid flag, CRC-8, raw "
                             "or lightly filtered, tau <= 20 ms); provisional threshold 650 N held 20 ms (500 N x 1.143 Cd band x "
                             "1.10 estimate error, ASSUMED); a stale (> 50 ms) or invalid estimate only raises a flag; GNC publishes "
                             "the estimate's 3-sigma error and latency, the false-abort rate and the stuck-pintle detection time, "
                             "and confirms or proposes the threshold",
        "relight_v2.8_design": "Finding A = option (b) ACCEPTED as one design: the FC sends RELIGHT at the planned T_fire; NC valve "
                               "and torch at E0, lift at E1 on torch confirmation; torch gate 0.16 s adopted as ECU design value, "
                               "PROVISIONAL until Combustion confirms it; flight worst sequence E0 -> Pc-confirm deadline 0.81 s; GNC "
                               "re-derives the planning value (0.6 + 0.81 = 1.41 s, or a better rule) and treats the 1.37 s unprimed "
                               "path as a fault case; option (a) stays a research option if (b) restores P (relight_planning_v28)",
        "flight_relight_window": "W 0.65 s on every flight relight, sensors as telemetry only; the v2.8 Tsat - 5 K vapour criterion is "
                                 "withdrawn; S1 flag in flight: flag and log, the relight proceeds (stand: lockout); stand rules R1-R4 "
                                 "adopted for IGN-1, T1-T4 and CF (not flown by GNC)",
        "b1_hop_cap": "85 m PROVISIONAL: GNC adds the regression band (a x 0.6-1.5, n 0.35-0.68, Combustion's recommended "
                      "distribution or uniform) to the B1 dispersion with throat growth and reports P at 85 m and the apex cap that "
                      "closes the 25 % reserve rule; the final B1 cap is set after the T1-T4 regression data (b1_regression_band). "
                      "Superseded by b1_hop_cap_62m",
        "relight_planning_value_v2.8": f"(correction) the earlier rule 'planning value = 0.6 s + worst sequence' is WITHDRAWN (it "
                                       f"double-counted the ignition latency once the sequence ends at Pc confirmation); PLANNING "
                                       f"VALUE = {PLAN_V28_GNC:g} s (the flight Pc-confirm deadline, the GNC rule) (relight_planning_v28)",
        "relight_option_c": f"ADOPTED PROVISIONALLY: Electronics publishes a PRIMED / UNPRIMED flag ECU -> FC at >= 10 Hz during the "
                            f"coast; the FC plans {PLAN_V28_FAULT:g} s on UNPRIMED; GNC verifies it paired and decides the plan for a "
                            "stale or missing flag (relight_planning_v28.option_c_fault_aware_plan)",
        "relight_option_a": "hold-to-planned-light stays a research option (not flown)",
        "b1_hop_cap_62m": f"B1 HOP CAP {B1_CAP_LEAD:g} m PROVISIONAL (the GNC 62.9 m rounded down) until the T1-T4 regression data; "
                          f"the B1 {B1_SIZING_H:g} m dispersed thermal and erosion cycles remain the conservative sizing cases "
                          "(b1_regression_band.lead_cap)",
        "pad_prepurge": "none (no pad pre-purge)",
        "reduced_bandwidth_x0.75": "degraded mode only (not a closure of ENG-07d, not the B-TVC-1 gate fallback)",
        "relight_retry": "NO in-flight relight retry: a no-light is a mission loss; GNC reports the no-light probability assumed and "
                         "its source (no_light_accounting)",
        "abort_law": "every abort de-energises the NC isolation valve at once and closes the pintle in parallel; normal shutdowns "
                     "keep the pintle-first sequence",
        "abort_tailoff": "keep the bracket; valve-to-pintle-seat line volume 21.4 cm3 (Combustion low_inlet_check_v2p3, relayed by "
                         "the lead; Mechanical re-measures it on CAD v3.4)",
        "throat_growth": "7-11 % throat-area growth per flight in the Monte Carlo dispersion; P reported with and without",
        "no_light_accounting": "P_total = P_6DOF x (1 - p_nl) with the ASSUMED placeholder table and the 3/N demonstration rule: accepted",
        "k_est_asc_2": "provisional flight-software baseline; one FSW for both profiles accepted; final only if the independent GNC "
                       "review accepts it. A1 0.984 vs 0.988 means 'no significant difference at 500 runs', not 'does not degrade'",
        "dispersed_duty_cycles": "DC-B1 disp p99 (k_est_asc 2) = B1 thermal and erosion sizing case; DC-B1 disp max = no-failure check; "
                                 "DC-A1 disp p99 = A1 sizing; growth variants alongside; they gate the Combustion head-end BC files "
                                 "and the Mechanical thermal re-runs",
        "combustion_retry_key": "the relight-retry key in combustion.json v2.3 goes to Combustion for v2.4",
        "upper_bay_venting": "recommended airframe feature in ICD-AIRFRAME (Mechanical servo-mount thermal)"},
        "REQ lead decisions 2026-10-13", LEAD_1013["source"])


def _tg_rows(folder, case):
    return rcsv(os.path.join(folder, f"mc6_runs_{case}_tg.csv"))


def throat_growth_section(TG_, TGA_):
    mc = dict(TG_["monte_carlo"])
    mc.update((TGA_ or {}).get("monte_carlo", {}))
    fold = {c: (TGA if c in (TGA_ or {}).get("monte_carlo", {}) else TGO) for c in mc}
    tab = {}
    for c, v in mc.items():
        vb = v.get("vs_base", {})
        tab[c] = dict(note=v.get("note"), n=v.get("n"), P=v["P"], ci95=v["ci95"], baseline=v.get("base"),
                      baseline_csv=os.path.basename(v.get("base_csv") or ""),
                      P_baseline=vb.get("P_base"), paired_vs_baseline=pr(vb, f"baseline {v.get('base')} (k_est_asc 0, no growth)"),
                      fail_modes=v.get("fail_modes"), n_exhausted=v.get("n_exhausted"),
                      burn_engine_on_counter_p50_p99_max_s=v.get("burn_time_p50_p99_max_s"),
                      n_counter_over_DC_B1_v2_counter=v.get("n_burn_over_envelope"), apex_p50_p99_m=v.get("h_max_p50_p99_m"),
                      throat_g_end_p01_p50_p99=v.get("throat_g_end_p01_p50_p99"), P_by_drawn_g_tercile=v.get("P_by_drawn_g_tercile"))
    # P with and without growth for the same flight software (paired, same draws)
    ww = {}
    for lab, a, b in (("A1 pc2 basis, FSW v2.6 (k_est_asc 0)", None, "tg_A1_pc"),
                      ("A1 ENG-07d basis, FSW v2.6 (k_est_asc 0)", None, "tg_A1J_pc"),
                      ("B1 85 m, FSW v2.6 (k_est_asc 0), ECU Pc loop", None, "tg_B1_pc"),
                      ("B1 85 m, FSW v2.6, throat-compensated loop (bound)", None, "tg_B1_comp"),
                      ("A1 pc2 basis, FSW v2.7 (k_est_asc 2)", "tg_A1_none_k2", "tg_A1_pc_k2"),
                      ("A1 ENG-07d basis, FSW v2.7 (k_est_asc 2)", "tg_A1J_none_k2", "tg_A1J_pc_k2"),
                      ("B1 85 m, FSW v2.7 (k_est_asc 2), ECU Pc loop", "tg_B1_none_k2", "tg_B1_pc_k2")):
        if b not in mc:
            continue
        if a is None:
            vb = mc[b]["vs_base"]
            ww[lab] = dict(P_without=vb["P_base"], P_with=mc[b]["P"], without_case=mc[b].get("base"), with_case=b,
                           paired=pr(vb, "without growth"))
        elif a in mc:
            ra, rb = _tg_rows(fold[a], a), _tg_rows(fold[b], b)
            ww[lab] = dict(P_without=mc[a]["P"], P_with=mc[b]["P"], without_case=a, with_case=b,
                           paired=pr(pair(ra, rb), "without growth") if ra and rb else None)
    # FSW effect at equal growth state (k_est_asc 2 vs 0)
    fx = {}
    for lab, a, b in (("B1 with growth: k_est_asc 2 vs 0", "tg_B1_pc", "tg_B1_pc_k2"),
                      ("A1 pc2 with growth: k_est_asc 2 vs 0", "tg_A1_pc", "tg_A1_pc_k2"),
                      ("A1 ENG-07d with growth: k_est_asc 2 vs 0", "tg_A1J_pc", "tg_A1J_pc_k2")):
        if a in mc and b in mc:
            ra, rb = _tg_rows(fold[a], a), _tg_rows(fold[b], b)
            fx[lab] = dict(P_k0=mc[a]["P"], P_k2=mc[b]["P"], paired=pr(pair(ra, rb), "k_est_asc 0") if ra and rb else None)
    for lab, c in (("B1 no growth: k_est_asc 2 vs 0", "tg_B1_none_k2"), ("A1 pc2 no growth: k_est_asc 2 vs 0", "tg_A1_none_k2"),
                   ("A1 ENG-07d no growth: k_est_asc 2 vs 0", "tg_A1J_none_k2")):
        if c in mc:
            vb = mc[c]["vs_base"]
            fx[lab] = dict(P_k0=vb["P_base"], P_k2=mc[c]["P"], paired=pr(vb, "k_est_asc 0"))
    nom = {k: dict(landed_ok=v.get("landed_ok"), closes=v.get("closes"), reserve_frac=v.get("reserve_frac"),
                   burn_time_engine_on_s=v.get("burn_time_s"), apex_m=v.get("h_max"), n2o_burned_kg=v.get("n2o_burned"),
                   isp_delivered_s=v.get("isp_delivered_s"), burn_over_19s_envelope=v.get("burn_over_thermal_envelope"))
           for k, v in TG_["nominal"].items()}
    b0 = mc.get("tg_B1_pc", {})
    vb0 = b0.get("vs_base", {})
    bc = mc.get("tg_B1_comp", {})
    bk = mc.get("tg_B1_pc_k2", {})
    rs = [TG_["nominal"].get(f"B1|g{g}|pc_loop", {}).get("reserve_frac") for g in ("0.07", "0.09", "0.11")]
    fa = {lab: v for lab, v in ww.items() if lab.startswith("A1")}
    finding = (
        f"B1 85 m with flight software v2.6 and the ECU holding Pc on the nominal map: growth lowers P from {vb0.get('P_base')} to "
        f"{b0.get('P')} ({pr(vb0, 'no growth')}); the nominal flight no longer closes the propellant rule (reserve "
        + " / ".join(f"{100 * r:.1f} %" for r in rs if r is not None)
        + " at g 0.07 / 0.09 / 0.11 vs 25 %): at a fixed Pc the eroded throat delivers more thrust per command, the open-loop floor "
        f"and the apex overshoot, the burn lengthens ({b0.get('n_exhausted')} of {b0.get('n')} runs exhaust the liquid). The "
        f"throat-compensated loop bound gives P {bc.get('P')} and the k_est_asc 2 estimator P {bk.get('P')} with growth. The A1 "
        "cases do not lose P with growth (" + "; ".join(f"{k}: {v['P_without']} -> {v['P_with']}" for k, v in fa.items())
        + "): short burns, closed-loop apogee and landing guidance. The compensated loop needs throat knowledge the ECU does not "
        "have: it is a bound, not a design")
    return P(rnd({
        "requirement": "ENG-06 rev 2 / lead 2026-10-13: the Pc / thrust loop must tolerate 7-11 % throat-area growth within a flight",
        "model": {"law": "At = At0 (1 + g(t)); g(t) = g_end min(1, J(t) / J_ref); J = int (F / F_max)^0.68 dt (thrust as the Pc proxy); "
                         "J_ref = J of the cycle's nominal flight (computed, not typed in)",
                  "loop_modes": {"throat_loop 1 (ECU as specified: Pc held on the nominal map)": "thrust per command x (1 + g)(1 + k_cf g), "
                                 "propellant flow x (1 + g), flow-limited ceiling x (1 + k_cf g); the FSW does not know g",
                                 "throat_loop 0 (bound of a throat-compensated thrust loop)": "thrust per command unchanged, flow per thrust "
                                 "/ (1 + k_cf g)"},
                  "k_cf": TG_["k_cf"], "J_ref": TG_["j_ref"], "growth_band": TG_["growth_band"], "growth_band_tag": TG_["growth_band_tag"],
                  "draw": "g_end ~ U(0.07, 0.11) per run from its own generator (seed 20261013): the other draws (seed 101) are "
                          "unchanged, so every case pairs run by run with its no-growth baseline",
                  "hypotheses": ["c* and O/F unchanged by the growth (ASSUMED)", "erosion-rate exponent 0.68 on Pc (LITERATURE-scaled, "
                                 "review RC-06)", "no onset delay: growth starts with the burn (conservative for the ascent)",
                                 "uniform growth of a circular throat; the expansion ratio falls accordingly (k_cf from the 1-D nozzle)"]},
        "with_and_without_growth": ww, "flight_software_effect": fx, "monte_carlo": tab, "nominal": nom,
        "B1_max_closing_hop_under_growth": TG_.get("B1_max_closing_hop"),
        "finding": finding,
        "unknowns": ["actual erosion rate of the throat insert (no measurement; literature-scaled band)", "onset delay and "
                     "non-uniform (non-circular) erosion", "Pc-map recalibration between flights", "interaction with the "
                     "head-end thermal state (Combustion)"]}, 4),
        "SIM m2_throat_mc v1 / v1.1 (sim6/run6 v2.7-dev on iface_v3c, 500 runs per case, seed 101 + growth seed 20261013)",
        "REQ band from the lead; model DERIVED by GNC; not a combustion model of erosion")


def kest2_section(TG_, TGA_, T27, KF, KF1):
    mc = dict(TG_["monte_carlo"])
    mc.update((TGA_ or {}).get("monte_carlo", {}))
    ck = {c["test"]: c for c in (T27 or {}).get("checks", [])}
    t12 = (T27 or {}).get("t12_rows", [])
    fm = []
    for r in t12:
        c0 = r.get("comparator_k0", {})
        fm.append(dict(case=r["case"], k_err_floor_pct=100 * r["k_err_floor"] if r.get("k_err_floor") is not None else None,
                       analytic_pct=(100 * r["analytic"]) if r.get("analytic") is not None else None,
                       k_ratio_min_max_phases_2_3=r.get("k_ratio_min_max_floor_ascent_descent"),
                       max_tilt_deg=r.get("max_tilt_phase23_deg"), apex_m=r["apex_m"], burn_engine_on_s=r["burn_s"],
                       landed_ok=r["landed_ok"], comparator_k0=dict(landed_ok=c0.get("landed_ok"), apex_m=c0.get("apex_m"),
                                                                    burn_engine_on_s=c0.get("burn_s"))))
    kfc = (KF or {}).get("cases", {})
    fr = {}
    for c, v in kfc.items():
        fr[c] = dict(pair=v["pair"], all_runs_reproduce_the_MC=v["all_reproduce"], lost_by_attribution=v["lost_by_attribution"],
                     gained_by_comparator_failure=v["gained_by_comparator_failure"],
                     max_converged_estimator_error_vs_k_star=v["max_converged_estimator_error_vs_k_star"],
                     max_converged_estimator_error_vs_k_star_excl_attitude_loss=v.get("max_converged_estimator_error_vs_k_star_excl_attitude_limit"),
                     runs=[dict(run=r["run"], kind=r["kind"], attribution=r.get("attribution") or r.get("comparator_failure_class"),
                                k2=dict(ok=r["k2"]["ok"], why=r["k2"]["why"], apex_m=r["k2"]["h_max"]),
                                k0=dict(ok=r["k0"]["ok"], why=r["k0"]["why"], apex_m=r["k0"]["h_max"]),
                                wind_mps=r["draw"]["wind"], gust_scale=r["draw"]["gust_scale"], thrust_scale=r["draw"]["thrust_scale"],
                                isp_scale=r["draw"]["isp_scale"], m_est_err=r["draw"]["m_est_err"]) for r in v["runs"]])
    gA = mc.get("tg_A1_none_k2", {}).get("vs_base", {})
    gAJ = mc.get("tg_A1J_none_k2", {}).get("vs_base", {})
    gB = mc.get("tg_B1_none_k2", {}).get("vs_base", {})
    det = lambda n: (ck.get(n) or {}).get("detail")  # noqa: E731
    res = lambda n: (ck.get(n) or {}).get("result")  # noqa: E731
    fp_ = lambda p: "n/a" if p is None else ("1.0" if p >= 0.995 else f"{p:.2f}")  # noqa: E731
    # failure-mode summaries computed from the T12 rows (no typed numbers)
    sel = lambda pre: [r for r in t12 if r["case"].startswith(pre)]  # noqa: E731
    bias = sel("accel bias")
    drag = sel("truth CA_tf") + sel("truth k_retro")
    wind_ok = [r for r in sel("wind") if r["landed_ok"] or r["comparator_k0"].get("landed_ok")]
    wind_bad = [r for r in sel("wind") if not r["landed_ok"] and not r["comparator_k0"].get("landed_ok")]
    pct = lambda x: f"{100 * x:+.2f} %"  # noqa: E731
    fm_bias = (f"k error ~ da m / F (analytic {100 * bias[0]['analytic']:.2f} % for 0.05 m/s2 at the floor); flown "
               + " / ".join(pct(r["k_err_floor"]) for r in bias)) if bias else None
    fm_drag = (f"tail-first CA x 0.7 / 1.3 and retro factor 0.25 / 0.75: |k error| <= {100 * max(abs(r['k_err_floor']) for r in drag):.2f} % "
               "on the floor") if drag else None
    fm_wind = ((f"{', '.join(r['case'] for r in wind_ok)}: |k error| <= {100 * max(abs(r['k_err_floor']) for r in wind_ok):.2f} %"
                if wind_ok else "") + "".join(
        f"; {r['case']}: the flight loses its attitude at floor thrust (max tilt {r['max_tilt_phase23_deg']:.0f} deg) with BOTH flight-"
        f"software forms (comparator max tilt {r['comparator_k0'].get('max_tilt_phase23_deg', float('nan')):.0f} deg); after that the "
        f"drag model is meaningless and k_hat reaches its 0.8 clamp (k_hat / k_true down to {r['k_ratio_min_max_floor_ascent_descent'][0]:.3f})"
        for r in wind_bad))
    b1f = (KF or {}).get("cases", {}).get("tg_B1_none_k2", {}).get("runs", [])
    lostp = [r for r in b1f if r["kind"] == "lost" and str(r.get("attribution", "")).startswith("propellant")]
    gainp = [r for r in b1f if r["kind"] == "gained" and r.get("comparator_failure_class") == "propellant exhausted"]
    rng_ = lambda xs: f"{min(xs):.0f}-{max(xs):.0f} m" if xs else "n/a"  # noqa: E731
    mech_txt = (f"k_est_asc 2 flies low-thrust / low-Isp engines to the full apex ({rng_([r['k2']['h_max'] for r in lostp])}; k_est_asc 0 "
                f"under-flies them to {rng_([r['k0']['h_max'] for r in lostp])} and keeps reserve: {len(lostp)} runs lost, propellant-"
                f"limited) and holds high-thrust engines at {rng_([r['k2']['h_max'] for r in gainp])} (k_est_asc 0 over-flies them to "
                f"{rng_([r['k0']['h_max'] for r in gainp])} and runs dry: {len(gainp)} runs gained)")
    return P(rnd({
        "status": "PROVISIONAL flight-software baseline for both profiles (lead 2026-10-13); final only after the independent GNC "
                  "review; not yet in electronics.json or the ECU firmware",
        "law": {"estimate": "k_raw = (f_z m_est + s D) / F_pc: f_z = axial specific force (accelerometer), m_est = FSW mass estimate, "
                            "F_pc = thrust of the published map at the Pc the loop holds, D = 0.5 rho CdA v_z^2 with the nose-first CdA "
                            "(body + engine-on base) when climbing (s = +1) and the tail-first CdA (base, retro factor) when descending "
                            "(s = -1), + the leg CdA once the legs are out; filtered (tau 0.1 s)",
                "gates": "B profile: phases 1-3 only when t > 1 s AND h_est > 1 m (airborne gate), and the landing burn; A profile: "
                         "the landing burn only (as v2.6)",
                "use": "B profile: the open-loop floor and top-up thrust commands are divided by k_hat clamped to [0.8, 1.25]; the "
                       "compensated floor is kept >= 12.5 % F_max; the phase-1 apex predictor keeps k = 1. A profile: the landing "
                       "guidance thrust model (as v2.6) with the signed drag model",
                "where": "FC (GNC flight software); needs Pc and the accelerometer at >= 100 Hz in the FC"},
        "hypothesis": "dividing the B hop's open-loop floor and top-up commands by the measured thrust effectiveness removes the apex "
                      "and propellant errors caused by engine thrust dispersion and in-flight throat growth",
        "comparator": "k_est_asc 0 (flight software v2.6) on the same 500 draws, paired exact McNemar",
        "evidence": {"B1_no_growth": dict(P_k0=gB.get("P_base"), P_k2=gB.get("P_case"), paired=pr(gB, "k_est_asc 0")),
                     "A1_no_growth_pc2_basis": dict(P_k0=gA.get("P_base"), P_k2=gA.get("P_case"), paired=pr(gA, "k_est_asc 0")),
                     "A1_no_growth_ENG07d_basis": dict(P_k0=gAJ.get("P_base"), P_k2=gAJ.get("P_case"), paired=pr(gAJ, "k_est_asc 0")),
                     "A1_wording": (f"no significant difference at 500 runs (pc2 basis {gA.get('lost')} lost / {gA.get('gained')} gained, "
                                    f"P {gA.get('P_case')} vs {gA.get('P_base')}, exact McNemar p {fp_(gA.get('p'))}; ENG-07d basis "
                                    f"{gAJ.get('lost')} / {gAJ.get('gained')}, P {gAJ.get('P_case')} vs {gAJ.get('P_base')}, p "
                                    f"{fp_(gAJ.get('p'))}); this does not show that A1 is not degraded"),
                     "with_growth": "throat_growth.flight_software_effect",
                     "tests": {n: dict(result=res(n), detail=det(n)) for n in ck if n.startswith(("T11", "T13"))}},
        "refutation_criterion": "refuted if, on the review basis, a paired 500-run comparison with k_est_asc 0 shows a significant "
                                "loss (exact McNemar p < 0.05 with more lost than gained) on any plan cycle, or a T11 / T12 check "
                                "fails, or hot-fire / B-TVC data put the accelerometer-to-thrust relation outside the modelled "
                                "errors (axial bias > 0.05 m/s2, scale factor > 0.5 %, tail-first drag x 0.7-1.3)",
        "rejected_first_form": {"k_est_asc": 1, "what": "drag subtracted in the ascent with the tail-first model (bias -2 D / F); "
                                "kept in the code as evidence",
                                "evidence": det("T11e rejected first form (k_est_asc 1)")},
        "failure_modes": {"perturbations_T12": fm,
                          "accelerometer_bias": fm_bias,
                          "drag_model_error": fm_drag,
                          "wind_gusts": fm_wind,
                          "low_thrust_start": "not flown: on the pad the accelerometer reads the ground reaction, so a slow start would "
                                              "bias the estimate; the airborne gate (h_est > 1 m, v2.7) prevents it and changes no Monte "
                                              "Carlo run",
                          "mass_knowledge": "by construction the estimator measures k* = (F / F_pc)(m_est / m_true): it absorbs the "
                                            "mass-estimate error, which makes the delivered acceleration equal to the guidance model. "
                                            "sim6 gives the FSW m_est = m_true (1 + e) with a constant e ~ N(0, 0.03) (ASSUMED, run6 "
                                            "dispersion 'm_est_err'); a real FSW integrates modelled propellant flow, so an Isp / flow "
                                            "dispersion adds a drifting mass error this Monte Carlo does not contain: open item for the "
                                            "review"},
        "monte_carlo_forensics": fr,
        "forensics_note": ("v1 of the forensics measured k_hat against F / F_pc and called " + "; ".join(
                               f"{len(v1.get('lost_estimator_driven') or [])} of {len([r for r in v1.get('runs', []) if r['kind'] == 'lost'])} "
                               f"lost {c} runs" for c, v1 in ((KF1 or {}).get("cases") or {}).items()) + " 'estimator-driven': "
                           "wrong metric (it counted the designed absorption of the mass error); v1.1 measures against k* and is the "
                           "one quoted; v1 kept (kest2_forensics_v1.json). Mechanism found on B1 85 m: " + mech_txt + ": the "
                           "propellant risk moves from one engine population to the other; both sit on the thin B1 85 m closure "
                           "margin (b1_dispersed_burn)"),
        "proposal_next": "RESEARCH PROPOSAL (not flown): a propellant-aware apex target for the B hop (lower h_target in flight when "
                         "the predicted touchdown reserve falls below the +25 % rule). Hypothesis: removes the low-Isp exhaustion "
                         "losses without giving back the apex control; comparator k_est_asc 2; evidence needed: paired 500-run MC "
                         "with a drifting mass estimate; refuted if no reduction in exhausted runs or new failures"}, 4),
        "DESIGN GNC (sim6 v2.7-dev) + SIM m2_throat_mc / m2_v27_tests v1.1 / m2_kest2_forensics v1.1",
        "provisional; the independent GNC review decides")


def no_light_section(Pcases):
    pnl = LEAD_1013["p_nl_placeholders"]
    tab = {c: dict(P_6DOF=Pv, **{f"P_total_p_nl_{p:g}": Pv * (1.0 - p) for p in pnl}) for c, Pv in Pcases.items()}
    demo = {f"p_nl <= {p:g}": int(np.ceil(3.0 / p)) for p in pnl}
    return P(rnd({
        "rule": "P_total = P_6DOF x (1 - p_nl), p_nl = probability that the in-flight relight does not light (no retry: mission loss)",
        "applies_to": "A1 (the only plan cycle with an in-flight relight); the B hops have one pad start (a pad no-light is a pad "
                      "abort, not a flight)",
        "p_nl_placeholders": list(pnl), "p_nl_tag": "ASSUMED placeholder table: NO source exists for this engine (igniter IGN-1, "
                                                    "T1 relight tests and T4 drop tests produce the data)",
        "table": tab,
        "demonstration_rule": {"rule": "0 no-lights in N independent relight attempts bounds p_nl <= 3 / N at 95 % confidence "
                                       "(rule of three, exact binomial: (1 - p)^N = 0.05)",
                               "N_needed_with_zero_failures": demo,
                               "condition": "attempts representative of the flight relight (NC-closed sequence, cold soak, "
                                            "settled liquid under the drogue)"}}, 4),
        "DERIVED (arithmetic on SIM P and ASSUMED p_nl)", "accepted by the lead 2026-10-13")


def abort_stuck_bound(AB, tab):
    """DERIVED impulse bound of an abort in which the pintle does not move (servo unpowered by the OV disconnect with a
    spring closure slower than the drive, or a jam): only the NC valve ends the flow."""
    Fg, mox = np.array(tab["Fg"], float), np.array(tab["mox"], float)
    with np.errstate(divide="ignore", invalid="ignore"):
        c = Fg[:, None] / mox
    c_max = float(np.nanmax(c[Fg > 1.0]))
    lv = AB["line_volume"]
    m_coil = max(v["valve_at_coil"] for v in lv["liquid_mass_g"].values()) / 1e3
    m_top = max(v["valve_at_top"] for v in lv["liquid_mass_g"].values()) / 1e3
    r100 = next(r for r in AB["rows"] if abs(r["level_frac_Fmax"] - 1.0) < 1e-9)
    F0 = r100["F0_N"]
    out = {}
    for lab in ("valve_electronics", "valve_combustion_max"):
        tv = float(r100[lab]["valve_close_s"])
        out[lab] = dict(valve_close_s=tv, valve_close_tag=r100[lab]["valve_close_tag"],
                        impulse_upper_Ns_line_21cm3=F0 * tv + m_coil * c_max,
                        impulse_upper_Ns_line_33cm3=F0 * tv + m_top * c_max)
    return dict(
        case="abort from 100 % in which the pintle does not move (PINTLE_FAULT with the servo unpowered by the OV disconnect "
             "and a spring closure slower than the drive, or a jam): only the NC valve ends the injector flow",
        bound="I <= F0 t_valve + m_line max(F / mdot_ox): full thrust until the valve is closed, then every gram of N2O in the "
              "valve-to-seat line burned at the best thrust per unit oxidiser flow of the published map",
        F0_N=F0, max_thrust_per_ox_flow_Ns_per_kg=c_max, line_liquid_max_g={"21.4 cm3 (valve at the coil fixed end)": 1e3 * m_coil,
                                                                          "33.0 cm3 (valve at the zone top)": 1e3 * m_top},
        by_valve_close_time=out,
        pintle_only_impulse_Ns=r100["pintle_only"]["impulse_Ns"],
        not_bounded="the duration (line blowdown through a stationary pintle at falling pressure) and the spring-closed pintle "
                    "speed: B-PNT-1 measures the unpowered HV69 back-drive torque against the closing spring (lead 2026-10-13)")


def abort_section(AB, tab=None):
    rows = []
    for r in AB["rows"]:
        rows.append(dict(level_frac_Fmax=r["level_frac_Fmax"], F0_N=r["F0_N"], pintle_only_upper=dict(t10_s=r["pintle_only"]["t10_s"],
                         impulse_Ns=r["pintle_only"]["impulse_Ns"]),
                         valve_cut_lower={k: dict(valve_close_s=r[k]["valve_close_s"], valve_close_tag=r[k]["valve_close_tag"],
                                                  t10_s=r[k]["t10_s"], impulse_Ns=r[k]["impulse_Ns"],
                                                  n2o_passed_after_valve_closed_g=r[k].get("n2o_after_valve_closed_g"),
                                                  line_liquid_min_g=r[k].get("line_liquid_min_g"))
                                         for k in ("valve_electronics", "valve_combustion_max")},
                         abort_tailoff=r["abort_tailoff_bound"]))
    lv = dict(AB["line_volume"])
    if "file" in lv:
        lv["file"] = hubrel(lv["file"])
    d = {"law": AB["law"], "bracket": rows, "line_volume": lv, "finding": AB["finding"],
         "unknowns": AB["unknowns"], "model_fit": AB["fit"], "source_file": hubrel(AB.get("speed_check_file"))}
    if tab is not None:
        d["pintle_not_moving_bound"] = abort_stuck_bound(AB, tab)
        d["unknowns"] = list(AB["unknowns"]) + [
            "closing speed of the pintle under its spring with the servo unpowered (PINTLE_FAULT after the OV disconnect, lead "
            "2026-10-13): the bracket above assumes the drive speed; pintle_not_moving_bound is the limit if it does not move"]
    return P(rnd(d, 4),
             "DESIGN lead rule 2026-10-13 + DERIVED GNC bracket (m2_abort_tailoff v1.1 on the sim6 lift-ramp shutdown fit)",
             "ENG-05 (< 10 % in 0.10 s) applies to MECO, which keeps the 72 % throttle-down; an abort from 100 % takes 0.12 s to "
             "10 % on the pintle (the valve does not shorten it with the 21.4 cm3 line)")


def b1_burn_section(TG_, DCI, DCB):
    mc = TG_["monte_carlo"]
    bs = mc.get("tg_B1_pc", {}).get("base_stats", {})
    env_c = DCI.get("conservative_thermal_envelope_engine_on_counter_s")
    kn = f"n_counter_over_DC_B1_v2_counter_{env_c:.2f}s" if env_c else "n_over_envelope"
    rows = {"pc_B1_h85_2kg (FSW v2.6, no growth)": {"burn_engine_on_counter_p50_p99_max_s": bs.get("burn_time_p50_p99_max_s"),
                                                     kn: bs.get("n_burn_over_envelope"), "n": bs.get("n"),
                                                     "apex_p50_p99_m": bs.get("h_max_p50_p99_m"), "n_exhausted": bs.get("n_exhausted"),
                                                     "P": bs.get("P")}}
    for c, lab in (("tg_B1_pc", "FSW v2.6, growth, Pc loop"), ("tg_B1_comp", "FSW v2.6, growth, compensated bound"),
                   ("tg_B1_none_k2", "FSW v2.7 k_est_asc 2, no growth"), ("tg_B1_pc_k2", "FSW v2.7 k_est_asc 2, growth, Pc loop")):
        v = mc.get(c)
        if v:
            rows[f"{c} ({lab})"] = {"burn_engine_on_counter_p50_p99_max_s": v.get("burn_time_p50_p99_max_s"),
                                    kn: v.get("n_burn_over_envelope"), "n": v.get("n"), "apex_p50_p99_m": v.get("h_max_p50_p99_m"),
                                    "n_exhausted": v.get("n_exhausted"), "P": v.get("P")}
    ton = {c: v.get("thrust_on_p50_p99_max_s") for c, v in (DCB or {}).get("cases", {}).items()}
    r0 = rows["pc_B1_h85_2kg (FSW v2.6, no growth)"]
    rg = rows.get("tg_B1_pc (FSW v2.6, growth, Pc loop)", {})
    rk = [rows[k] for k in rows if "k_est_asc 2" in k]
    finding = (f"dispersed B1 85 m flights burn past the DC-B1 v2 envelope ({env_c:.2f} s engine-on counter): {r0[kn]} of {r0['n']} "
               f"runs with flight software v2.6 (counter p99 {r0['burn_engine_on_counter_p50_p99_max_s'][1]:.1f} s, max "
               f"{r0['burn_engine_on_counter_p50_p99_max_s'][2]:.1f} s), {rg.get(kn)} with growth (max "
               f"{(rg.get('burn_engine_on_counter_p50_p99_max_s') or [0, 0, float('nan')])[2]:.1f} s); with k_est_asc 2 "
               + " / ".join(f"{r[kn]}" for r in rk) + " runs, counter max " + " / ".join(
                   f"{r['burn_engine_on_counter_p50_p99_max_s'][2]:.1f}" for r in rk)
               + " s (no growth / growth): the estimator removes the long tail (over-flown apex of high-thrust engines) but not "
               "the excess over 19 s. The dispersed duty cycles replace DC-B1 v2 as the thermal input (lead 2026-10-13)") if env_c else None
    return P(rnd({"cases": rows, "thrust_on_p50_p99_max_s_all_runs_reflown": ton,
                  "envelope_s": {"DC-B1 v2 thrust-on": DCI.get("conservative_thermal_envelope_burn_s"),
                                 "DC-B1 v2 engine-on counter": env_c},
                  "finding": finding,
                  "definition": DCI.get("burn_time_definition")}, 3),
             "SIM m2_throat_mc (500 runs) + m2_dc_burn_check v1 (all runs re-flown, thrust-on time)",
             "Monte Carlo burn statistics are engine-on counters unless labelled thrust-on")


def duty_cycles_v3_section(DCI, kNom):
    cyc = {}
    for c in DCI["cycles"]:
        cyc[c["name"]] = dict(file=c["file"], sha256=c["sha256"], kind=c.get("kind", "nominal_seeded"),
                              burn_thrust_on_s=rnd(c["burn_time_s"], 3), engine_on_counter_s=rnd(c.get("engine_on_counter_s"), 3),
                              burns_s=rnd(c.get("burns_s"), 3), impulse_Ns=rnd(c["total_impulse_Ns"], 0), starts=c["starts"],
                              apex_m=rnd(c["summary"]["h_max"], 1), m_n2o_kg=c["m_n2o_kg"], success=c["success"],
                              run_index=c.get("run_index"), run_seed=c.get("run_seed"), mc_case=c.get("mc_case"),
                              max_axial_specific_mps2=rnd(c.get("max_axial_specific_mps2"), 2),
                              max_axial_specific_airborne_mps2=rnd(c.get("max_axial_specific_airborne_mps2"), 2),
                              max_axial_specific_leg_contact_mps2=rnd(c.get("max_axial_specific_leg_contact_mps2"), 2),
                              max_gimbal_deg=rnd(c.get("max_gimbal_deg"), 2),
                              max_hinge_est_Nm=rnd(c.get("max_hinge_est_Nm"), 2), note=c["note"])
    return P({"index": f"{HUB}/duty_cycles/duty_cycles_index_v3.json", "index_generator": DCI.get("generator"),
              "index_revision": DCI.get("index_revision"),
              "burn_time_definition": DCI.get("burn_time_definition"), "max_axial_definition": DCI.get("max_axial_definition"),
              "current": cyc,
              "sizing_cases_lead_2026-10-13": DCI.get("sizing_cases_lead_2026-10-13"),
              "dispersed_envelope": rnd(DCI.get("dispersed_envelope"), 3),
              "retained_v2": {c["name"]: dict(file=c["file"], sha256=c["sha256"], burn_thrust_on_s=rnd(c["burn_time_s"], 2),
                                              burn_v2_index_engine_on_s=rnd(c.get("burn_time_s_v2_index"), 2), status=c["status"])
                              for c in DCI["retained_v2"]},
              "columns": DCI["columns"], "longest_flight_burn_current_plan_s": rnd(DCI["longest_flight_burn_current_plan_s"], 2),
              "conservative_thermal_envelope_burn_s": rnd(DCI["conservative_thermal_envelope_burn_s"], 2),
              "qualification_check": rnd(DCI["qualification_check"], 3),
              "nominal_cycles_fsw": ("DC-A1 v3 and DC-B1 85 m v3 (nominal seeded) were flown with flight software v2.6 (k_est_asc 0); "
                                     "on the nominal engine k_est_asc 2 changes the nominal flights by: " + kNom)},
             "SIM duty cycles v3 (sim6 v2.6 nominal / v2.7-dev dispersed, iface_v3c) + v2 files retained by the lead's decision",
             "index revision 2026-10-13b: burn_time_s = thrust-on time of the file (it was the engine-on counter); revision "
             "2026-10-13c: airborne / leg-contact axial maxima (the overall maximum of the failed max runs is the crash impact)")


def verification_v27(T27, T27v1, B27, B26b, T26on27, KF, KF1, DCB, DCI, DCX=None):
    return P(rnd({
        "tests_v27": {"version": (T27 or {}).get("version"), "n_fail": (T27 or {}).get("n_fail"),
                      "checks": [dict(test=c["test"], result=c["result"], detail=c["detail"]) for c in (T27 or {}).get("checks", [])]},
        "tests_v27_first_run_kept": {"version": (T27v1 or {}).get("version"), "failures": (T27v1 or {}).get("failures"),
                                     "why": "v1 required every perturbed B1 flight to land; wind 8 m/s + gusts (seed 7) does not land "
                                            "with either FSW form (loss of attitude at floor thrust): a wind-limit case, not an "
                                            "estimator effect; v1.1 pairs every perturbation with the comparator k_est_asc 0"},
        "bit_identity_v27_defaults": {"vs_v26_runs_iface_v3c": (B27 or {}).get("bit_identical"),
                                      "values": {c: v["values_compared"] for c, v in ((B27 or {}).get("cases") or {}).items()},
                                      "vs_v25_runs_iface_v3a_with_v27_code": (B26b or {}).get("bit_identical"),
                                      "values_v25": {c: v["values_compared"] for c, v in ((B26b or {}).get("cases") or {}).items()}},
        "v26_tests_rerun_on_v27_code": {"n_fail": (T26on27 or {}).get("n_fail"), "sim": (T26on27 or {}).get("sim"),
                                        "note": "m2_v26_tests v1.3 on iface_v3c with sim6 v2.7-dev: every check detail identical to the "
                                                "v2.6 run"},
        "kest2_forensics": {"version": (KF or {}).get("version"), "attribution_rule": (KF or {}).get("attribution_rule"),
                            "first_version_kept": (KF1 or {}).get("version")},
        "dispersed_duty_cycles": {"each_file_reproduces_its_MC_row": all(c.get("reproduces_mc_row", True) for c in DCI["cycles"]),
                                  "selection_rerun_all_runs_reproduce": {c: v.get("reproduces_mc_csv") for c, v in ((DCB or {}).get("cases") or {}).items()},
                                  "index_rev_c_regenerated_files_identical": (DCX or {}).get("all_files_identical"),
                                  "index_rev_c_changes": {"added_fields": (DCX or {}).get("n_added"), "changed": (DCX or {}).get("changed"),
                                                          "check": "m2_dc_index_diff v1 (both generators re-run into a clean folder; every CSV "
                                                                   "sha256 equal to rev b and to the file on disk)"}},
        "not_physical_acceptance": "simulation checks only"}, 4),
        "SIM m2_v27_tests v1.1 + m2_bitcheck_v27 + m2_bitcheck_v26 (v2.7 code) + m2_v26_tests v1.3 (v2.7 code) + m2_kest2_forensics "
        f"v1.1 + {DCI.get('generator')} + m2_dc_burn_check v1")


def notch_q2_proposal(CSI3):
    ft = (CSI3 or {}).get("ftarget", {})
    cs = ft.get("cases", {})
    if "lpf50+notchQ2-12_mis5|z0.02" not in cs:
        return None
    st = ft.get("stiffness_for_floor20_f_min", {})
    def rig(k):
        pm = [r.get("rigid_with_notch", {}).get("pm_min_deg") for r in cs[k]["rows"]]
        pm = [x for x in pm if x is not None]
        return [min(pm), max(pm)] if pm else None
    q = {}
    for z in ("0.02", "0.05", "0.1"):
        for nm, k in (("Q1 (adopted)", f"lpf50+notchQ1-12_mis5|z{z}"), ("Q2 (proposal)", f"lpf50+notchQ2-12_mis5|z{z}")):
            s_ = st.get(k, {}).get("J1.6", {})
            q[f"{nm} zeta {z}"] = dict(f_min_Hz=cs[k]["f_min_Hz"], K_struct_min_at_K_s_174=s_.get("K_struct_min_at_K_s_174"),
                                      K_struct_min_at_K_s_58=s_.get("K_struct_min_at_K_s_58"), rigid_pm_with_notch_min_max_deg=rig(k))
    a, b, b5 = q["Q1 (adopted) zeta 0.02"], q["Q2 (proposal) zeta 0.02"], q["Q2 (proposal) zeta 0.05"]
    k58 = lambda x: "no solution (servo alone too soft)" if x is None else f"{x:,.0f} N m/rad"  # noqa: E731
    reading = (f"floor20 target {b['f_min_Hz']['floor20']:g} Hz (zeta 0.02) / {b5['f_min_Hz']['floor20']:g} Hz (zeta 0.05) with Q 2 vs "
               f"{a['f_min_Hz']['floor20']:g} Hz with Q 1; structure needed at K_s 174 and J 1.6e-3: {b['K_struct_min_at_K_s_174']:,.0f} vs "
               f"{a['K_struct_min_at_K_s_174']:,.0f} N m/rad (zeta 0.02); at K_s 58 (B-TVC-1 gate case): Q 2 {k58(b['K_struct_min_at_K_s_58'])} "
               f"(zeta 0.02) / {k58(b5['K_struct_min_at_K_s_58'])} (zeta 0.05), Q 1 {k58(a['K_struct_min_at_K_s_58'])}; rigid-body phase "
               f"margin with the notch {b['rigid_pm_with_notch_min_max_deg'][0]:.1f}-{b['rigid_pm_with_notch_min_max_deg'][1]:.1f} deg vs "
               f"{a['rigid_pm_with_notch_min_max_deg'][0]:.1f}-{a['rigid_pm_with_notch_min_max_deg'][1]:.1f} deg. BUT the corners that include "
               f"the 12.5 % floor ('all') need {b['f_min_Hz']['all']:g} Hz (Q 1: {a['f_min_Hz']['all']:g}) and the 62.5 N-only corners "
               f"{b['f_min_Hz']['f62']:g} Hz (Q 1: {a['f_min_Hz']['f62']:g}): acceptable only while no flight phase runs below 20 % (the "
               "plan uses the 20 % floor and the 20 % relight start)")
    return P(rnd({
        "what": "RESEARCH PROPOSAL (not adopted, not flown in the 6-DOF): ENG-07d notch with Q 2 (narrower) instead of Q 1, same "
                "-12 dB depth, tuned within +/-5 % of the B-TVC-1 measured mode",
        "hypothesis": "the narrower notch costs less phase at the rigid-body crossover, so the lowest rocking-mode frequency that "
                      "keeps 6 dB on the corners at the 20 % floor and above falls, and the structure stiffness target falls with it",
        "comparator": "the adopted Q 1 notch (same model, same corners)",
        "evidence_linear": q,
        "reading": reading,
        "refutation_criterion": "refuted if a paired 6-DOF Monte Carlo (ENG-07d basis) with Q 2 loses P against Q 1, if the B-TVC-1 "
                                "mode is not known to +/-5 % per axis, or if any planned phase needs thrust below 20 %",
        "status": "proposal for the independent review; the adopted ENG-07d targets (3,100 / 5,200 N m/rad, Q 1) stand"}, 1),
        "SIM m2_csi_v3 v1.3 ftarget on iface_v3c (linear only)", "innovation labelled as research: no superiority claimed")


def wind_evidence(cases, w_split=6.0):
    """Landing outcome against the drawn wind (post-processing of the 500-run CSVs: columns ok, wind, exhausted)."""
    bins = ((0.0, 2.0), (2.0, 4.0), (4.0, 6.0), (6.0, 7.0), (7.0, 8.0))
    out = {}
    for lab, p in cases.items():
        r = rcsv(p) if p else []
        if not r:
            continue
        ok = col(r, "ok") > 0
        w = col(r, "wind")
        ex = col(r, "exhausted") > 0.5 if "exhausted" in r[0] else np.zeros(len(r), bool)
        lo_ = w < w_split
        out[lab] = dict(
            by_wind_bin_mps={f"{a:g}-{b:g}": dict(n=int(((w >= a) & (w < b)).sum()), fail=int((~ok & (w >= a) & (w < b)).sum()),
                                                  P=float(ok[(w >= a) & (w < b)].mean()) if ((w >= a) & (w < b)).any() else None)
                             for a, b in bins},
            below_split=dict(n=int(lo_.sum()), fail=int((~ok & lo_).sum()), P=float(ok[lo_].mean()),
                             ci95=wilson(int(ok[lo_].sum()), int(lo_.sum())), fail_propellant_limited=int((~ok & lo_ & ex).sum())),
            at_or_above_split=dict(n=int((~lo_).sum()), fail=int((~ok & ~lo_).sum()), P=float(ok[~lo_].mean()),
                                   ci95=wilson(int(ok[~lo_].sum()), int((~lo_).sum()))),
            non_propellant_failures=dict(total=int((~ok & ~ex).sum()), at_or_above_split=int((~ok & ~ex & ~lo_).sum())),
            csv=os.path.basename(p))
    reading = (f"landing failures that are not propellant-limited at a drawn wind >= {w_split:g} m/s: " + "; ".join(
        f"{lab} {v['non_propellant_failures']['at_or_above_split']} of {v['non_propellant_failures']['total']}" for lab, v in out.items())
        + f". P below {w_split:g} m/s: " + "; ".join(f"{lab} {v['below_split']['P']:.3f} ({v['below_split']['fail']} fail in "
                                                      f"{v['below_split']['n']}, {v['below_split']['fail_propellant_limited']} "
                                                      "propellant-limited)" for lab, v in out.items()))
    return P(rnd({"split_mps_at_10m": w_split, "cases": out,
                  "reading": reading,
                  "proposal": f"GNC PROPOSAL for the lead (launch commit, not a decision): mean wind <= {w_split:g} m/s at 10 m for B1 "
                              "and A1 until the gust model and the B1 floor-phase attitude limit are re-examined; the drawn wind is "
                              "U(0, 8) m/s at 10 m with gust scale U(0.5, 1.5) and shear exponent 0.14 (ASSUMED brief distribution, "
                              "not site data for the launch field)"}, 4),
             "SIM post-processing of the 500-run Monte Carlo CSVs (seed 101 draws)",
             "the wind bins hold 68-128 runs each: the per-bin P carries a wide interval; the split value is read from the bins, "
             "not optimised")


def relight_placeholder_section(RSSJ, TG_, planning_v):
    mc = (RSSJ or {}).get("monte_carlo", {})
    nom = (RSSJ or {}).get("nominal", {})
    rows = {}
    for c, v in mc.items():
        vb = v.get("vs_base", {})
        rows[c] = dict(note=v.get("note"), P=v["P"], ci95=v["ci95"], baseline=v.get("base"), P_baseline=vb.get("P_base"),
                       paired=pr(vb, f"{v.get('base')} (sequence 0.8 s, planning 1.4 s)"),
                       planning_value_s=v.get("config_t_ign_est_s"), start_delay_add_s=v.get("config_t_ign_add_s"),
                       t90_relight_p50_max_s=v.get("t90_relight_p50_max_s"), relight_cmd_h_p01_p50_m=v.get("relight_cmd_h_p01_p50_m"),
                       relight_cmd_h_p01_p50_m_baseline=(v.get("base_stats") or {}).get("relight_cmd_h_p01_p50_m"),
                       fail_modes=v.get("fail_modes"), identical_to_baseline=v.get("identical_to_base"))
    nm = {k: dict(landed_ok=v.get("landed_ok"), closes=v.get("closes"), reserve_frac=v.get("reserve_frac"),
                  reserve_frac_minus_purge_bound=v.get("reserve_frac_minus_purge_bound"), relight_h_m=v.get("h_ign"))
          for k, v in nom.items()}
    ph = (TG_ or {}).get("relight_placeholder", {})
    vb = lambda c: (mc.get(c) or {}).get("vs_base") or {}  # noqa: E731
    fmt = lambda c: (f"P {mc[c]['P']} vs {vb(c).get('P_base')}, {vb(c).get('lost')} lost / {vb(c).get('gained')} gained, "  # noqa: E731
                     f"p {vb(c).get('p', float('nan')):.2g}") if c in mc else "not run"
    finding = (f"the +0.3 s sequence with the planning value moved to 1.7 s: A1 {fmt('rs_A1_seq+0.3_planned')}; ENG-07d basis "
               f"{fmt('rs_A1J_seq+0.3_planned')}; with the planning value left at 1.4 s: A1 {fmt('rs_A1_seq+0.3_unplanned')}; ENG-07d "
               f"basis {fmt('rs_A1J_seq+0.3_unplanned')}: the planning value and the sequence must move together. B1 (one pad start, "
               f"no in-flight relight) identical run by run: {(mc.get('rs_B1_85m_seq+0.3') or {}).get('identical_to_base')}")
    return P(rnd({
        "rule": "planning value = 0.6 s (latest start delay of the Monte Carlo draw) + Electronics' published worst-case relight "
                "sequence time (valve command to Pc confirmation), changed in the same FSW / ECU release as any sequence change; "
                "a release that changes one without the other is not flyable (lead 2026-10-13)",
        "placeholder_now": {"start_delay_add_s": ph.get("t_ign_add_s"), "planning_value_s": ph.get("t_ign_est_s"),
                            "composition": "0.8 s combustion.json NC-closed sequence slots + 0.3 s lead placeholder",
                            "planning_value_check_s": planning_v, "tag": ph.get("tag")},
        "replaced_by": "Electronics' worst-case sequence time (electronics.json) and Combustion's RC-03 latency distribution",
        "evidence_monte_carlo": rows, "evidence_nominal": nm,
        "purge_bound": (RSSJ or {}).get("purge_bound"),
        "finding": finding},
        4), "SIM m2_relight_seq_sens v1 (sim6 v2.6-dev on iface_v3c, 500 runs, seed 101) + REQ lead rule 2026-10-13",
        "the Monte Carlo of throat_growth and of the dispersed duty cycles carries the 1.1 / 1.7 s placeholder; SUPERSEDED as the "
        "current planning value by relight_planning_181 (1.81 s, lead decision 2026-10-13 (2)); kept as evidence")


def relight_181_section(RL, rl_dir, DCI):
    """A1 at the relight planning value 1.81 s (lead decision 2026-10-13 (2)): LATE / EARLY brackets and the UNPLANNED
    sensitivity (m2_relight_181 v1); mechanism statistics read from the Monte Carlo CSVs."""
    mc, nom = RL.get("monte_carlo", {}), RL.get("nominal", {})
    seq, mp = RL["sequence"], RL["mapping"]
    rows = {}
    for c, v in mc.items():
        vc, v17 = v.get("vs_comparator") or {}, v.get("vs_1.7s") or {}
        rows[c] = dict(note=v.get("note"), P=v["P"], ci95=v["ci95"], fail_modes=v.get("fail_modes"),
                       paired_vs_comparator=pr(vc, vc.get("comparator")) if vc else None,
                       paired_vs_1p7s=pr(v17, v17.get("comparator")) if v17 else None,
                       start_delay_drawn_min_max_s=v.get("start_delay_drawn_min_max_s"),
                       relight_cmd_h_p01_p50_m=v.get("relight_cmd_h_p01_p50_m"), usable_left_p01_kg=v.get("usable_left_p01_kg"),
                       n_usable_below_zero=v.get("n_usable_below_zero"), n_exhausted=v.get("n_exhausted"),
                       engine_on_counter_vs_a1_sizing=v.get("engine_on_counter_over_a1_sizing_cycle"))
    # mechanism: landing-burn attitude statistics, LATE vs EARLY on the same draws
    mech = {}
    for base in ("A1_none", "A1_pc", "A1J_none", "A1J_pc"):
        a = rcsv(os.path.join(rl_dir, f"mc6_runs_rl181_{base}_k2_rl181.csv"))
        b = rcsv(os.path.join(rl_dir, f"mc6_runs_rl181e_{base}_k2_rl181.csv"))
        if not a or not b:
            continue
        ra, rb = col(a, "max_rate_land"), col(b, "max_rate_land")
        ta, tb = col(a, "max_tilt_land"), col(b, "max_tilt_land")
        oka, okb = col(a, "ok") > 0.5, col(b, "ok") > 0.5
        lost = oka & ~okb
        mech[base] = dict(max_rate_land_median_dps=[float(np.median(ra)), float(np.median(rb))],
                          max_tilt_land_median_deg=[float(np.median(ta)), float(np.median(tb))],
                          n_lost_early=int(lost.sum()), lost_with_td_rate_over_10dps=int(np.sum(lost & (col(b, "td_rate") > 10.0))),
                          lost_with_td_vh_over_0p5mps=int(np.sum(lost & (col(b, "td_vh") > 0.5))),
                          order="[LATE, EARLY]")
    # nominal light altitude (DERIVED: relight command altitude - descent speed x nominal start delay, speed ~constant under drogue)
    light = {}
    for lab in ("ref_1.7s", "late_1.81s", "early_1.81s", "unplanned_1.7s"):
        r_ = nom.get(f"A1|{lab}|k2")
        if r_:
            light[lab] = dict(relight_cmd_h_m=r_["h_ign"], v_ign_mps=r_["v_ign"], nominal_start_delay_s=r_["nominal_start_delay_s"],
                              light_h_m_derived=r_["h_ign"] + r_["v_ign"] * r_["nominal_start_delay_s"],
                              reserve_frac=r_["reserve_frac"], burn_time_s=r_["burn_time_s"], landed_ok=r_["landed_ok"],
                              closes=r_["closes"],
                              reserve_frac_minus_sil_successful_relight=r_.get("reserve_frac_minus_successful_relight_sil"),
                              reserve_frac_minus_sil_no_light_inventory=r_.get("reserve_frac_minus_no_light_inventory_sil"))
    # recorded flights of selected draws (m2_rl181_trace): they must reproduce their Monte Carlo rows
    TR = jl(os.path.join(rl_dir, "rl181_trace.json")) or {}
    trace = {}
    for r_, vv in (TR.get("runs") or {}).items():
        trace[r_] = {lab: {k: x.get(k) for k in ("ok", "h_at_light_m", "vh_at_light_mps", "max_tilt_landing_burn_deg",
                                                 "max_rate_landing_burn_dps", "td_rate_dps", "td_vh_mps", "mc_row_check")}
                     for lab, x in vv.items()}
    trace_txt = ""
    if trace and all((x.get("mc_row_check") or {}).get("same") for vv in trace.values() for x in vv.values()):
        rng_ = lambda lab, k: [vv[lab][k] for vv in trace.values() if lab in vv]  # noqa: E731
        lost_ = [f"{r_} ({vv['early']['td_rate_dps']:.1f} deg/s)" for r_, vv in trace.items()
                 if "early" in vv and vv["late"]["ok"] and not vv["early"]["ok"]]
        trace_txt = (f". Recorded flights of draws {', '.join(trace)} (each reproduces its Monte Carlo row, m2_rl181_trace): light at "
                     f"{min(rng_('late', 'h_at_light_m')):.1f}-{max(rng_('late', 'h_at_light_m')):.1f} m LATE vs "
                     f"{min(rng_('early', 'h_at_light_m')):.1f}-{max(rng_('early', 'h_at_light_m')):.1f} m EARLY, peak landing-burn "
                     f"tilt {min(rng_('late', 'max_tilt_landing_burn_deg')):.0f}-{max(rng_('late', 'max_tilt_landing_burn_deg')):.0f} vs "
                     f"{min(rng_('early', 'max_tilt_landing_burn_deg')):.0f}-{max(rng_('early', 'max_tilt_landing_burn_deg')):.0f} deg and "
                     f"rate {min(rng_('late', 'max_rate_landing_burn_dps')):.0f}-{max(rng_('late', 'max_rate_landing_burn_dps')):.0f} vs "
                     f"{min(rng_('early', 'max_rate_landing_burn_dps')):.0f}-{max(rng_('early', 'max_rate_landing_burn_dps')):.0f} deg/s"
                     + (f"; lost EARLY on the touchdown rate: draw {', '.join(lost_)}" if lost_ else ""))
    f_ = lambda c: (f"{mc[c]['P']:.3f}") if c in mc else "not run"  # noqa: E731
    pv = lambda c, k: (mc.get(c, {}).get(k) or {})  # noqa: E731
    late = "; ".join(f"{b_} {f_(f'rl181_{b_}_k2')} ({pr(pv(f'rl181_{b_}_k2', 'vs_comparator'), '1.7 s')})"
                     for b_ in ("A1_none", "A1_pc", "A1J_none", "A1J_pc"))
    early = "; ".join(f"{b_} {f_(f'rl181e_{b_}_k2')} ({pr(pv(f'rl181e_{b_}_k2', 'vs_comparator'), 'LATE')})"
                      for b_ in ("A1_none", "A1_pc", "A1J_none", "A1J_pc"))
    m0 = mech.get("A1_none", {})
    lt, et = light.get("late_1.81s", {}), light.get("early_1.81s", {})
    a1s = RL.get("a1_sizing_cycles", {})
    cnt = {c: (v.get("engine_on_counter_over_a1_sizing_cycle") or {}) for c, v in mc.items()}
    e_p99 = [cnt[c]["p99_s"] for c in cnt if c.startswith("rl181e_") and cnt[c]]
    l_p99 = [cnt[c]["p99_s"] for c in cnt if c.startswith("rl181_") and cnt[c]]
    e_max = [cnt[c]["max_s"] for c in cnt if c.startswith("rl181e_") and cnt[c]]
    sizing_c = max((v.get("engine_on_counter_s") or 0.0) for v in a1s.values()) if a1s else None
    finding = (f"LATE (sequence {mp['late']['t_ign_add_s']:g} s, start delay {mp['late']['start_delay_range_s'][0]:.2f}-"
               f"{mp['late']['start_delay_range_s'][1]:.2f} s, planning value {mp['late']['t_ign_est_s']:g} s), paired against the 1.7 s "
               f"placeholder runs: {late}: no significant difference at 500 runs. EARLY (start delay "
               f"{mp['early']['start_delay_range_s'][0]:.2f}-{mp['early']['start_delay_range_s'][1]:.2f} s, bottom = SIL nominal "
               f"{seq['sil_nominal_s']:g} s, same planning value), paired against LATE: {early}. UNPLANNED (sequence "
               f"{mp['unplanned']['t_ign_add_s']:g} s, planning value left at {mp['unplanned']['t_ign_est_s']:g} s): "
               f"{f_('rl181u_A1_none_k2')} ({pr(pv('rl181u_A1_none_k2', 'vs_comparator'), 'LATE')}): a light slightly later than "
               "planned is harmless; the loss comes from lights EARLIER than planned")
    mechanism = (f"an early light starts the landing burn higher than planned (nominal light at ~{et.get('light_h_m_derived', float('nan')):.0f} m "
                 f"vs ~{lt.get('light_h_m_derived', float('nan')):.0f} m, DERIVED) at the drogue descent speed with the drift still to "
                 "cancel; the burn begins at low thrust and the lateral correction tilts the vehicle further: median max landing-burn "
                 f"rate {m0.get('max_rate_land_median_dps', [0, 0])[0]:.0f} -> {m0.get('max_rate_land_median_dps', [0, 0])[1]:.0f} deg/s and "
                 f"median max tilt {m0.get('max_tilt_land_median_deg', [0, 0])[0]:.0f} -> {m0.get('max_tilt_land_median_deg', [0, 0])[1]:.0f} deg "
                 f"(A1 pc2 basis, all 500 runs); of the {m0.get('n_lost_early')} runs lost, {m0.get('lost_with_td_rate_over_10dps')} touch "
                 f"down above 10 deg/s and {m0.get('lost_with_td_vh_over_0p5mps')} above 0.5 m/s horizontal; one run per early case "
                 "exhausts the propellant" + trace_txt)
    sizing = (f"A1 engine-on counter p99 LATE {min(l_p99):.2f}-{max(l_p99):.2f} s, EARLY {min(e_p99):.2f}-{max(e_p99):.2f} s (max "
              f"{max(e_max):.2f} s) against the published A1 sizing cycle counter {sizing_c:.2f} s: the A1 sizing cycle does not bound "
              "early lights. Lead 2026-10-13: B1 governs thermal and erosion (DC-B1 disp p99 ~21.8 s thrust-on), no A1 thermal "
              "re-run for early lights; GNC publishes the early-light A1 p99 cycle as a record once the fix is chosen"
              ) if (e_p99 and l_p99 and sizing_c) else None
    return P(rnd({
        "rule": "planning value = 0.6 s latest start delay + Electronics' worst-case relight sequence time (lead decision 2026-10-13 (2))",
        "sequence_times": {"worst_s": seq["worst_s"], "sil_nominal_s": seq["sil_nominal_s"], "planning_value_s": seq["planning_value_s"],
                           "source": seq["source"], "tag": "SIL (Electronics firmware v2.7 plant model; not measured) + REQ lead"},
        "mapping_on_the_6dof": mp,
        "j_ref_fixed": RL.get("j_ref_fixed"),
        "evidence_monte_carlo": rows,
        "evidence_nominal": light,
        "sil_unignited_n2o": RL.get("sil_unignited"),
        "finding": finding,
        "mechanism": mechanism,
        "landing_attitude_late_vs_early": mech,
        "recorded_flights": dict(file=f"{HUB}/results/relight_181/rl181_trace.json", runs=trace) if trace else None,
        "a1_sizing_cycle": sizing,
        "proposals": {
            "a_hold_to_planned_light": ("RESEARCH FSW option (lead 2026-10-13: test paired on the four bases): after an early light, "
                                        "hold the relight start thrust until the planned light time, then release the landing guidance. "
                                        "Hypothesis: the burn then starts at the planned geometry and P returns to the LATE level. "
                                        "Comparator: the EARLY cases above (same draws). Refutation: P not restored (paired loss vs "
                                        "LATE) or nominal reserve below the +25 % rule"),
            "b_deterministic_ignition_instant": ("Electronics feasibility asked by the lead: prepare the relight with a bounded pre-light "
                                                 "window, then fire at the GNC-planned instant; the remaining spread is the SIL Pc-confirm "
                                                 "time 0.26-0.50 s (liquid / vapour line). If feasible, GNC flies that spread; the lead "
                                                 "prefers (b) if both restore P")},
        "status": "OPEN: early-light P loss accepted by the lead as a finding (CHANGELOG 2026-10-13); fix under test"}, 4),
        "SIM m2_relight_181 v1 (sim6/run6 v2.7-dev, iface_v3c, 500 runs, seed 101, FSW v2.7 k_est_asc 2) + REQ lead decision "
        "2026-10-13 (2) + SIL Electronics firmware v2.7 sequence times",
        "start delay = U(0.2, 0.6) s ignition draw + sequence time: adding the draw to a sequence that already contains the 0.35 s "
        "check is the lead's planning rule (conservative for the late end); it is not a latency model (RC-03 pending)")


def lead_cap_block(RBM, DCI):
    """the lead's provisional B1 cap (62 m, decision 2026-10-13): nominal closure at the worst corner (0.25 m scan rows), the
    500-run Monte Carlo at 62 m with band + growth vs growth only (m2_regband_mc v1.1), and the engine-on counters against the
    B1 85 m dispersed sizing cycles that stay the conservative thermal / erosion cases."""
    mc, nom, cs = RBM["monte_carlo"], RBM["nominal"], RBM["cap_scan"]
    rl, tl = mc.get("rbl_B1_lead62_pc_k2"), mc.get("tgl_B1_lead62_pc_k2")
    if not rl or not tl:
        return None
    srow = {}
    for gk, sc in (cs.get("scans") or {}).items():
        r = next((x for x in sc["rows"] if abs(x["h_m"] - B1_CAP_LEAD) < 1e-6), None)
        if r:
            srow[gk] = dict(closes=r["closes"], reserve_frac=r["reserve_frac"], landed=r["landed"])
    corner_caps = {k.split("|g")[0]: v["h_cap_m"] for k, v in nom["caps"].items() if k.endswith("|g0.11|flight")}
    szc = {c["name"]: c.get("engine_on_counter_s") for c in (DCI or {}).get("cycles", []) if c["name"].startswith("DC-B1_hop_85m_disp")}
    rr = rcsv(os.path.join(RBO, "mc6_runs_rbl_B1_lead62_pc_k2_rb.csv")) or []
    bt = np.array([float(r["burn_time"]) for r in rr]) if rr else np.array([])
    over = {k: int(np.sum(bt > v)) for k, v in szc.items() if v}
    vc = rl.get("vs_comparator") or {}
    finding = (f"B1 at the lead's {B1_CAP_LEAD:g} m cap: the nominal flight closes the +25 % rule at the worst band corner "
               f"({gov_case(nom)}) with g 0.11 (reserve {100 * srow.get('g0.11', {}).get('reserve_frac', float('nan')):.1f} %) and at every "
               f"other corner (corner caps {min(v for v in corner_caps.values() if v):.1f} m to >= {max(v for v in corner_caps.values() if v):.0f} m, "
               f"the search bound); "
               f"500 runs with band + growth: P {rl['P']:.3f} [{rl['ci95'][0]:.3f}, {rl['ci95'][1]:.3f}] vs growth only "
               f"{tl['P']:.3f} ({pr(vc, 'growth only at 62 m')}), {rl.get('n_exhausted')} runs exhaust the liquid, usable liquid p01 "
               f"{rl.get('usable_left_p01_kg', float('nan')):.3f} kg (growth only {tl.get('usable_left_p01_kg', float('nan')):.3f} kg). "
               f"Engine-on counter p99 / max at 62 m with the band {rl['burn_time_p50_p99_max_s'][1]:.2f} / "
               f"{rl['burn_time_p50_p99_max_s'][2]:.2f} s vs the 85 m dispersed sizing cycles "
               + ", ".join(f"{k} {v:.2f} s" for k, v in szc.items() if v)
               + f" ({len(bt)} runs at 62 m; runs above each: " + " / ".join(str(v) for v in over.values()) + ")")
    return {"h_m": B1_CAP_LEAD,
            "decision": f"REQ lead 2026-10-13: B1 hop cap {B1_CAP_LEAD:g} m PROVISIONAL (the GNC 62.9 m rounded down) until the T1-T4 "
                        f"regression data; the B1 {B1_SIZING_H:g} m dispersed cycles remain the conservative thermal and erosion "
                        "sizing cases",
            "nominal_worst_corner_scan_rows": srow, "corner_caps_g0.11_flight_m": corner_caps,
            "monte_carlo": {"band_growth": "rbl_B1_lead62_pc_k2", "growth_only": "tgl_B1_lead62_pc_k2",
                            "j_ref": "J of the no-band B1 flight at 62 m (full growth g_end on every 62 m flight; the convention of "
                                     "rb_B1_pc_k2 at 85 m)"},
            "engine_on_counter_vs_85m_sizing": dict(sizing_counters_s=szc, n_runs_above=over,
                                                    p50_p99_max_62m_band_growth_s=rl["burn_time_p50_p99_max_s"]),
            "finding": finding}


def _workarea_rel(src):
    """another discipline's work-area path (not in the hub) -> 'Combustion work area: <relative path> (not in the hub ...)'."""
    if not isinstance(src, dict):
        return src
    out = dict(src)
    f = out.get("folder")
    if isinstance(f, str) and f.startswith("/home/claude/work/"):
        disc, rel = f[len("/home/claude/work/"):].split("/", 1)
        out["folder"] = f"{disc.capitalize()} work area: {rel} (not in the hub when GNC read it)"
    return out


def gov_case(nom):
    return nom["governing_cap"]["case"].split("|g")[0]


def regband_section(RBM, RBMOD, DCI=None):
    """B1 with the regression-law band in the Monte Carlo (lead decision 2026-10-13, interfaces/CHANGELOG.md: add (a, n) to the
    B1 dispersion with throat growth, report P at 85 m and the apex cap that closes the 25 % reserve rule; 85 m PROVISIONAL, the
    final cap after the T1-T4 regression data; later the same day: cap 62 m PROVISIONAL, lead_cap). Read from m2_regband_mc
    v1.1 / m2_regband_model v1 results."""
    mc, nom, cs = RBM["monte_carlo"], RBM["nominal"], RBM["cap_scan"]
    rows = {}
    for c, v in mc.items():
        vc = v.get("vs_comparator") or {}
        rows[c] = dict(note=v.get("note"), h_target_m=(v.get("config") or {}).get("h_target"), P=v["P"], ci95=v["ci95"],
                       fail_modes=v.get("fail_modes"), paired=pr(vc, vc.get("comparator")) if vc else None,
                       n_exhausted=v.get("n_exhausted"), n_usable_below_zero=v.get("n_usable_below_zero"),
                       usable_left_p01_kg=v.get("usable_left_p01_kg"), liq_left_min_kg=v.get("liq_left_min_kg"),
                       burn_time_p50_p99_max_s=v.get("burn_time_p50_p99_max_s"), h_max_p50_p99_m=v.get("h_max_p50_p99_m"),
                       P_by_band_region=v.get("by_band_region"),
                       runs_in_combustion_web_below_1mm_region=v.get("runs_in_combustion_web_below_1mm_region"),
                       runs_in_combustion_burnthrough_region=v.get("runs_in_combustion_burnthrough_region"))
    gov = nom["governing_cap"]
    caps = {k: v["h_cap_m"] for k, v in nom["caps"].items()}
    up = max(caps.values())
    n85 = {k: dict(reserve_frac=v["reserve_frac"], closes=v["closes"], landed_ok=v["landed_ok"], usable_left_kg=v["usable_left"])
           for k, v in nom["nominal_85m"].items()}
    scan = {k: dict(highest_closing_m=v["highest_closing_m"], lowest_not_closing_m=v["lowest_not_closing_m"], monotone=v["monotone"])
            for k, v in cs["scans"].items()}
    r85, r85g, rc = (mc.get(k, {}) for k in ("rb_B1_none_k2", "rb_B1_pc_k2", "rbc_B1_cap_pc_k2"))
    reg_ = (r85g.get("by_band_region") or {}).get("a<0.8 & n>=0.57") or {}
    web = RBM.get("combustion_web_region") or {}
    finding = (
        f"B1 85 m with the band and throat growth: P {r85g.get('P')} {[round(x, 3) for x in r85g.get('ci95', [])]} "
        f"({pr(r85g.get('vs_comparator'), 'growth only')}); band without growth P {r85.get('P')} "
        f"({pr(r85.get('vs_comparator'), 'no band, no growth')}). The P difference is not significant at 500 runs, but the "
        f"propellant rule fails: {r85g.get('n_exhausted')} runs exhaust the liquid and the usable liquid p01 is "
        f"{r85g.get('usable_left_p01_kg', float('nan')):.3f} kg; the failures concentrate at slow regression with high n "
        f"(a < 0.8 and n >= 0.57: P {reg_.get('P', float('nan')):.2f} over {reg_.get('n')} runs). The nominal B1 85 m flight closes "
        "the +25 % rule only at the corners with a >= 1.0 and n <= 0.5 or a = 1.5 (nominal_85m). Apex cap that closes the rule at "
        f"every corner with 11 % growth on the flight: {gov['h_m']:.1f} m (worst corner {gov['case'].split('|g')[0]}; the 0.25 m scan "
        f"confirms: {scan.get('g0.11', {}).get('highest_closing_m')} m closes, {scan.get('g0.11', {}).get('lowest_not_closing_m')} m does "
        f"not). At the cap with band and growth: P {rc.get('P')} ({pr(rc.get('vs_comparator'), 'growth only at the cap')}), "
        f"{rc.get('n_exhausted')} exhausted, usable liquid p01 {rc.get('usable_left_p01_kg', float('nan')):.3f} kg")
    return P(rnd({
        "rule": "lead 2026-10-13: regression band a x 0.6-1.5, n 0.35-0.68 in the B1 dispersion with throat growth 7-11 %; P at 85 m "
                "and the apex cap closing the +25 % reserve rule (usable liquid >= 25 % of the liquid burned, 3 % trapped); 85 m "
                "PROVISIONAL, final cap after T1-T4",
        "band": RBM["band"], "growth_band": RBM["growth_band"],
        "model": {"module": "gncsim.regband v1 (sim6/run6 v2.7.1-dev option reg_band, own generator seed 20261017)",
                  "law": "oxidiser and fuel flow per delivered thrust multiplied by phi(a, n, X), X = oxidiser burned at map flow; "
                         "phi tables = Combustion's RC-07 corner runs of DC-B1 v3 p99 / nominal (bilinear in a, n between the 9 "
                         "corners); thrust unchanged (the ECU Pc loop holds Pc; Pc ratio at the corners "
                         f"{[round(x, 4) for x in ((RBMOD or {}).get('pc_ratio_median_range') or [])]})",
                  "file": f"{HUB}/sim/data/regband/regband_model_v1.json",
                  "source": _workarea_rel((RBMOD or {}).get("source")),
                  "hypotheses": (RBMOD or {}).get("hypotheses"),
                  "validation": "corner self-check on the calibration cycle within 0.02 % (oxidiser), T-RB1 nominal corner bit-identical, "
                                "T-RB2 6-DOF vs model within 0.5 % (verification_v271)"},
        "nominal_85m": n85,
        "caps_m": caps,
        "cap_search_upper_bound_m": up,
        "governing_cap": gov,
        "cap_scan_0p25m": scan,
        "monte_carlo": rows,
        "combustion_web": web,
        "finding": finding,
        "proposal": (f"(history) GNC PROPOSAL for the lead: B1 cap {gov['h_m']:.1f} m (provisional, on the ASSUMED band) until T1-T4 "
                     "measure the regression law; 85 m keeps P within the 500-run resolution but not the propellant rule at the slow-"
                     "regression corners. The B1 duty cycles (thermal and erosion sizing) were flown at 85 m: a lower cap shortens "
                     "the B1 burn; Combustion's web check at the high-a corners (web below 1 mm over "
                     f"{100 * (web.get('fraction_below_1mm') or 0):.1f} % of the band area at 85 m) is not re-run at the lower cap"),
        "decision": (f"REQ lead 2026-10-13: B1 cap {B1_CAP_LEAD:g} m PROVISIONAL (the GNC {gov['h_m']:.1f} m rounded down) until the "
                     f"T1-T4 regression data; the {B1_SIZING_H:g} m dispersed thermal and erosion cycles remain the conservative sizing "
                     "cases (no B1 duty-cycle re-run at 62 m)"),
        "lead_cap": lead_cap_block(RBM, DCI),
        "limits": ["band distribution uniform x uniform (no recommended distribution published); the corner effect is a function of "
                   "the oxidiser burned (B1-like hops only, not A1)", "liquid depletion cuts the thrust in the 6-DOF (no vapour-phase "
                   "burn): conservative", "the band and the isp_scale N(1, 0.05) draw may double count: conservative",
                   "the regression law itself is ASSUMED (Combustion RC-07); T1-T4 data replace it"]}, 4),
        "SIM m2_regband_mc v1.1 + m2_regband_model v1 (sim6/run6 v2.7.1-dev, iface_v3c, 500 runs, seed 101 + growth 20261013 + band "
        "20261017) on SIM Combustion RC-07 band runs (ASSUMED regression law) + REQ lead decisions 2026-10-13",
        "simulation only; the 62 m cap is the lead's provisional decision, the 62.9 m value the GNC computation it rounds")


def _v28_parse(name):
    """v28_{state}_p{plan}_{base}_k2 -> (state, plan, base)."""
    st, rest = name[len("v28_"):].split("_p", 1)
    pl = rest.split("_")[0]
    return st, float(pl), rest[len(pl) + 1:-len("_k2")]


def option_c_block(OC, plan_gnc, plan_fault):
    """option (c) verification (m2_relight_v28 v1.2 option_c): paired fault path, fault spread, false-UNPRIMED cost, break-even
    prior and the GNC stale / missing-flag rule."""
    if not OC:
        return None
    bb = copy.deepcopy(OC.get("by_base", {}))
    for b_ in bb.values():   # McNemar p to 2 significant digits as text: the section rounds numbers to 4 decimals (p < 5e-5 -> 0)
        for grp in ("fault_paired",):
            if grp in b_:
                b_[grp]["p_2sig"] = f"{b_[grp]['p']:.2g}"
        for grp in ("fault_spread_paired", "false_unprimed_paired"):
            for d_ in (b_.get(grp) or {}).values():
                d_["p_2sig"] = f"{d_['p']:.2g}"
    order = ("A1_none", "A1_pc", "A1J_none", "A1J_pc")
    lab = {"A1_none": "A1", "A1_pc": "A1 growth", "A1J_none": "ENG-07d", "A1J_pc": "ENG-07d growth"}

    def ptxt(d):
        return f"{d['P_base']:.3f} -> {d['P_case']:.3f} (-{d['lost']}/+{d['gained']}, p {d['p']:.2g})"
    fp = "; ".join(f"{lab[b]} {ptxt(bb[b]['fault_paired'])}" for b in order if b in bb and "fault_paired" in bb[b])
    fs = "; ".join(f"{lab[b]} " + ", ".join(f"{st} {ptxt(d)}" for st, d in bb[b]["fault_spread_paired"].items())
                   for b in order if b in bb and bb[b].get("fault_spread_paired"))
    fu = "; ".join(f"{lab[b]} " + ", ".join(f"{st} {ptxt(d)}" for st, d in bb[b]["false_unprimed_paired"].items())
                   for b in order if b in bb and bb[b].get("false_unprimed_paired"))
    mm = "; ".join(f"{lab[b]} " + ", ".join(f"plan {k} s {v['worst_P']:.3f}" for k, v in bb[b]["maximin"].items())
                   for b in order if b in bb and "maximin" in bb[b])
    qr = OC.get("q_star_range")
    rule = OC.get("stale_flag_rule_gnc", {})
    finding = (f"Paired on the same draws, plan {plan_gnc:g} s -> {plan_fault:g} s on the 1.37 s fault path: {fp}. Fault-path spread "
               f"(delay = line-state E0->E2 + the 0.56 s prep re-run, 0.69-1.37 s; none bases): {fs}. Cost of a wrong UNPRIMED "
               f"flag (a primed line planned at {plan_fault:g} s): {fu}. Worst P over the three primed states and the fault path "
               f"(maximin): {mm}. Break-even prior of an unreported UNPRIMED line q* = "
               + (f"{qr[0]:.3f}-{qr[1]:.3f}" if qr else "n/a") + " over the bases and line states")
    return {"status": f"ADOPTED PROVISIONALLY by the lead (2026-10-13): Electronics publishes PRIMED / UNPRIMED to the FC at >= 10 Hz "
                      f"during the coast; the FC plans {plan_fault:g} s on UNPRIMED and {plan_gnc:g} s otherwise; GNC verification "
                      "below (simulation)",
            "research_framing": (f"hypothesis: planning {plan_fault:g} s on UNPRIMED lands the fault path like the primed path; "
                                 f"comparator: the same fault runs at {plan_gnc:g} s; evidence: fault_paired and fault_spread_paired; "
                                 "refutation: no paired gain, a loss on the primed line larger than the fault-path gain at the "
                                 "credible fault probability, or a flag not available to the FC before T_fire"),
            "finding": finding,
            "verification_by_base": bb,
            "q_star_range": qr,
            "stale_or_missing_flag": rule,
            "method": OC.get("method")}


def relight_v28_section(V28, plan_gnc, plan_fault):
    """A1 relight on the v2.8 relight design (lead decisions 2026-10-13: Finding A = option (b) accepted as one design; flight
    worst sequence E0 -> Pc-confirm deadline 0.81 s; fault path 1.37 s; GNC re-derives the planning value; later the same day:
    planning value 0.81 s adopted, option (c) adopted provisionally). m2_relight_v28 v1.2."""
    mc, nom, tabs = V28.get("monte_carlo", {}), V28.get("nominal") or {}, V28["rc03"]["tables"]
    seq = V28["sequence"]
    grid = {}
    for name, v in mc.items():
        st, pl, base = _v28_parse(name)
        vl = v.get("vs_late_1p81") or {}
        grid.setdefault(base, {}).setdefault(f"{pl:.2f}", {})[st] = dict(
            P=v["P"], ci95=v["ci95"], fail_modes=v.get("fail_modes"), paired_vs_late_1p81=pr(vl, vl.get("comparator")) if vl else None,
            light_minus_plan_s=v.get("light_minus_plan_s_min_max"), start_delay_min_p50_max_s=v.get("start_delay_min_p50_max_s"),
            P_by_light_minus_plan=v.get("P_by_light_minus_plan"), engine_on_counter_p99_max_s=v.get("engine_on_counter_p99_max_s"),
            engine_on_counter_over_a1_sizing=v.get("engine_on_counter_over_a1_sizing"), usable_left_p01_kg=v.get("usable_left_p01_kg"),
            n_exhausted=v.get("n_exhausted"))
    summ = {}
    for base, g_ in grid.items():
        for pl, d_ in g_.items():
            ps = {st: x["P"] for st, x in d_.items() if st != "fault" and not st.startswith("fs")}
            fsp = {st[2:]: x["P"] for st, x in d_.items() if st.startswith("fs")}
            summ.setdefault(base, {})[pl] = dict(P_min_over_line_states=min(ps.values()) if ps else None, P_by_state=ps,
                                                 P_fault_1p37=(d_.get("fault") or {}).get("P"))
            if fsp:
                summ[base][pl]["P_fault_spread_by_state"] = fsp
    pg, pl_ = f"{plan_gnc:.2f}", f"{seq['lead_planning_value_s']:.2f}"
    rowtxt = lambda pk: "; ".join(  # noqa: E731
        f"{b_} " + ", ".join(f"{st} {summ[b_][pk]['P_by_state'][st]:.3f}" for st in ("liq", "vapU", "vapF") if st in summ[b_][pk]['P_by_state'])
        for b_ in ("A1_none", "A1_pc", "A1J_none", "A1J_pc") if b_ in summ and pk in summ[b_])
    lost_txt = lambda pk: "; ".join(  # noqa: E731
        f"{b_} {st} {grid[b_][pk][st]['paired_vs_late_1p81']}" for b_ in ("A1_none", "A1_pc", "A1J_none", "A1J_pc")
        for st in ("liq", "vapU", "vapF") if b_ in grid and pk in grid[b_] and st in grid[b_][pk])
    fault_txt = "; ".join(f"plan {pk} s: " + ", ".join(f"{b_} {summ[b_][pk]['P_fault_1p37']:.3f}" for b_ in summ
                                                         if pk in summ[b_] and summ[b_][pk]['P_fault_1p37'] is not None)
                          for pk in sorted({k for b_ in summ for k in summ[b_]}, key=float)
                          if any(pk in summ[b_] and summ[b_][pk]['P_fault_1p37'] is not None for b_ in summ))
    nom_fault = {k: dict(landed_ok=v["landed_ok"], reserve_frac=v["reserve_frac"]) for k, v in nom.items() if "|fault|" in k}
    finding = (f"Planning value {pl_} s (lead: 0.6 + 0.81): {rowtxt(pl_)} (paired vs the 1.81 s LATE runs: {lost_txt(pl_)}). "
               f"Planning value {pg} s (GNC rule): {rowtxt(pg)} (paired vs the 1.81 s LATE runs: {lost_txt(pg)}). Fault path "
               f"(start delay fixed at {seq['fault_s']:g} s): {fault_txt}")
    return P(rnd({
        "design": "v2.8 relight (lead 2026-10-13, Finding A = option (b), one design): the FC sends RELIGHT at the planned T_fire; "
                  "NC valve latched with the opener ramp and torch at E0, lift at E1 on torch confirmation (gate 0.16 s, "
                  f"PROVISIONAL); W 0.65 s from the lift on every flight relight; flight worst E0 -> Pc-confirm deadline {seq['worst_s']:g} s; "
                  f"unprimed fault path (segment emptied by a seat leak, v2.7 prep re-run) {seq['fault_s']:g} s",
        "start_delay_model": {"mapping": V28.get("mapping"), "line_states": {k: dict(case=v["case"], quantiles_5pct_s=v["quantiles_5pct_s"],
                                                                                    check=v["check"]) for k, v in tabs.items()},
                              "source": dict(file=hubrel(V28["rc03"]["file"]), sha256_16=V28["rc03"]["sha256_16"],
                                             tag="SIM Combustion RC-03 (ASSUMED delay distributions, 200k samples)"),
                              "construction": "E0->E2 quantiles = Combustion E0->E3 5 % quantiles - (median E0->E3 - median E0->E2); "
                                              "reproduces Combustion's E0->E2 p95 and max within 3 ms"},
        "planning_rule_gnc": (f"planning value = the Pc-confirm deadline of the flight worst sequence ({seq['worst_s']:g} s = torch gate "
                              "0.16 + W 0.65): RELIGHT is sent at a deterministic instant and every light that is not aborted happens "
                              "at or before the deadline, so no light is later than planned; the earliest physical light (E0->E2 "
                              f"minimum {min(v['quantiles_5pct_s'][0] for v in tabs.values()):.3f} s, liquid line) is "
                              f"{seq['worst_s'] - min(v['quantiles_5pct_s'][0] for v in tabs.values()):.2f} s early, inside the "
                              "tolerance the sweep shows"),
        "lead_rule_0p6_plus_0p81": ("0.6 + 0.81 = 1.41 s counts the ignition latency twice: 0.6 s was the top of the U(0.2, 0.6) s "
                                    "ignition draw that the old model added to a sequence without ignition; the 0.81 s v2.8 sequence "
                                    "already ends at Pc confirmation (E2), so at 1.41 s every physical light is at least 0.6 s earlier "
                                    "than planned (the early-light loss of relight_planning_181). WITHDRAWN by the lead (2026-10-13)"),
        "planning_value_s": P(plan_gnc, "REQ lead decision 2026-10-13 (the GNC rule adopted)",
                              "flight Pc-confirm deadline: torch gate 0.16 s (PROVISIONAL) + W 0.65 s"),
        "planning_value_gnc_s": plan_gnc,
        "planning_value_fault_path_s": P(plan_fault, "REQ lead decision 2026-10-13, option (c) PROVISIONAL",
                                         "planning value when the ECU flag reports UNPRIMED (>= the 1.37 s fault path)"),
        "sweep_and_full_by_base": summ,
        "monte_carlo": grid,
        "nominal": nom,
        "nominal_fault_path": nom_fault,
        "finding": finding,
        "option_a_hold_to_planned_light": "RESEARCH option (lead 2026-10-13: stays research); not flown",
        "option_c_fault_aware_plan": option_c_block(V28.get("option_c"), plan_gnc, plan_fault),
        "status": (f"planning value {plan_gnc:g} s ADOPTED by the lead (2026-10-13, the GNC rule; the 0.6 s + sequence rule withdrawn); "
                   f"option (c) ({plan_fault:g} s on an ECU UNPRIMED flag) ADOPTED PROVISIONALLY and verified paired here; the "
                   "stale / missing-flag plan is the GNC decision the lead asked for (option_c_fault_aware_plan.stale_or_missing_flag)")}, 4),
        "SIM m2_relight_v28 v1.2 (sim6/run6 v2.7.1-dev start-delay quantile option, iface_v3c, 500 runs, seed 101 + start-delay seed "
        "20261018, FSW v2.7 k_est_asc 2) on SIM Combustion RC-03 E0->E2 + SIL/DESIGN Electronics v2.8 sequence + REQ lead decisions "
        "2026-10-13",
        "6-DOF thrust onset at the drawn E0->E2 (Pc confirmation) delay; the build-up to 90 % is the 6-DOF's own closed-loop lag "
        "(~0.1 s, Combustion E2->E3 0.092 s); simulation only")


def verification_v271(BC, BC0):
    """sim6/run6 v2.7.1-dev checks (m2_bitcheck_v271 v2; v1 result kept)."""
    if not BC:
        return None
    pa = BC.get("parts", {})
    sm = lambda d: {c: {k: v.get(k) for k in ("runs_checked", "failed_runs_included", "values_compared", "mismatches")}  # noqa: E731
                    for c, v in (d or {}).items()}
    E = pa.get("E_T-TQ_start_delay_quantile_option") or {}
    e3 = (E.get("E3_cmd_to_onset_equals_draw") or {}).get("runs") or []
    return P(rnd({
        "tool": BC.get("tool"), "sim": BC.get("sim"),
        "A_options_off_vs_v2.6": sm(pa.get("A_options_off_vs_v2.6")),
        "B_v27_options_on_band_off_vs_v2.7-dev": sm(pa.get("B_v27_options_on_band_off_vs_v2.7-dev")),
        "C_T-RB1_band_at_nominal_corner": {k: (pa.get("C_T-RB1_nominal_corner_identity") or {}).get(k)
                                          for k in ("runs_checked", "values_compared", "mismatches")},
        "D_T-RB2_6dof_vs_model_max_abs_diff": (pa.get("D_T-RB2_corner_effect_on_nominal_B1") or {}).get("max_abs_diff"),
        "E_T-TQ_start_delay_option": {"E1_main_draws_unchanged": (E.get("E1_main_draws_unchanged") or {}).get("ok"),
                                      "E2_constant_table": (E.get("E2_constant_table") or {}).get("ok"),
                                      "E3_cmd_to_onset_minus_draw_ms": [min(1e3 * r["err_s"] for r in e3),
                                                                        max(1e3 * r["err_s"] for r in e3)] if e3 else None,
                                      "E3_ok": (E.get("E3_cmd_to_onset_equals_draw") or {}).get("ok"),
                                      "E4_nominal_uses_table_median": (E.get("E4_nominal_uses_table_median") or {}).get("ok")},
        "all_identical_and_E_passed": BC.get("bit_identical_A_B_C"),
        "history": ("m2_bitcheck_v271 v1 (before the t_ign_q option) passed A-C the same way: "
                    f"{(BC0 or {}).get('bit_identical_A_B_C')}; kept as bitcheck_v271_pre_tq.json") if BC0 else None,
        "file": f"{HUB}/results/v271_checks/bitcheck_v271.json"}, 4),
        "SIM m2_bitcheck_v271 v2 (stored Monte Carlo rows re-flown field by field)",
        "D is not gated (the guidance closes the loop on the changed thrust history); E3 tolerance = one 1 ms integration step")


def no_retry_section(comb):
    seq = ((comb or {}).get("igniter", {}).get("sequence", {}) or {}).get("v", {})
    ab = seq.get("abort_if_no_ignition", [])
    rel = seq.get("relight", [])
    rk = [x for x in ab if "retry" in x.lower()]
    vo = [x for x in rel if "isolation valve" in x.lower()]
    return P({
        "rule": "NO in-flight relight retry: the flight software declares a no-light when Pc does not reach the ignition-check "
                "level in the sequence window, aborts (abort law: NC valve de-energised at once, pintle closed in parallel, torch "
                "solenoids closed) and the flight is lost; the drogue stays attached (release only on Pc confirmation)",
        "accounting": "no_light_accounting (P_total = P_6DOF (1 - p_nl), p_nl ASSUMED placeholder table, no source)",
        "interface_contradictions_kept": {"combustion.json igniter.sequence.abort_if_no_ignition": rk,
                                          "combustion.json igniter.sequence.relight": vo,
                                          "gnc.json v2 requirements.ignition.starts_per_flight_required": "3, 'one spare relight'",
                                          "resolution": "the lead rules govern (no retry; NC valve closed through the coast); the "
                                                        "retry key goes to Combustion for combustion.json v2.4; ENG-04 starts per "
                                                        "flight stays an igniter capacity (>= 3), not a flown retry"}},
        "REQ lead decision 2026-10-13", "GNC flies no retry in any Monte Carlo case")


def apply_1013b(g, FCT):
    """2026-10-13 afternoon and evening: v2.8 relight planning value (0.81 s ADOPTED by the lead), option (c) (adopted
    provisionally; GNC paired verification and stale / missing-flag rule), B1 regression band and the lead's 62 m provisional cap
    (the 85 m dispersed cycles stay the conservative sizing cases), sim6 v2.7.1-dev, FC_THRUST (open unless run): patch the
    summary fields of the file (status, mission plan, baseline note, FSW version, ignition requirement, tank closure, ICD relight
    text, scripts, answers, requests, open issues, open items, changes)."""
    v28 = g["relight_planning_v28"]["v"]
    sm = v28["sweep_and_full_by_base"]
    oc = v28.get("option_c_fault_aware_plan") or {}
    pg, pf = f"{PLAN_V28_GNC:.2f}", f"{PLAN_V28_FAULT:.2f}"
    rb = g["b1_regression_band"]["v"]
    cap = rb["governing_cap"]["h_m"]
    lc = rb.get("lead_cap") or {}
    mc85 = rb["monte_carlo"].get("rb_B1_pc_k2", {})
    mcc = rb["monte_carlo"].get("rbc_B1_cap_pc_k2", {})
    mcl = rb["monte_carlo"].get("rbl_B1_lead62_pc_k2", {})
    mcl0 = rb["monte_carlo"].get("tgl_B1_lead62_pc_k2", {})
    stale = (oc.get("stale_or_missing_flag") or {})
    stale_rule = stale.get("rule", "not evaluated")
    qr = oc.get("q_star_range")

    def prow(pk):
        out = []
        for b_ in ("A1_none", "A1_pc", "A1J_none", "A1J_pc"):
            x = (sm.get(b_) or {}).get(pk)
            if x and x["P_by_state"]:
                out.append(f"{b_} {min(x['P_by_state'].values()):.3f}-{max(x['P_by_state'].values()):.3f}")
        return "; ".join(out)

    def frow(pk):
        return "; ".join(f"{b_} {sm[b_][pk]['P_fault_1p37']:.3f}" for b_ in ("A1_none", "A1_pc", "A1J_none", "A1J_pc")
                         if b_ in sm and pk in sm[b_] and sm[b_][pk].get("P_fault_1p37") is not None)
    qtxt = f"{qr[0]:.3f}-{qr[1]:.3f}" if qr else "n/a"
    g["status"] += (
        f" v2.8 relight design (lead 2026-10-13, Finding A = option (b)): planning value {PLAN_V28_GNC:g} s ADOPTED by the lead (the "
        f"GNC Pc-confirm-deadline rule; P over the three line states {prow(pg)}; the withdrawn 0.6 + 0.81 = 1.41 s rule lost P: "
        f"{prow(pf)}); option (c) ADOPTED PROVISIONALLY: {PLAN_V28_FAULT:g} s on an ECU UNPRIMED flag lands the 1.37 s fault path "
        f"(P {frow(pf)} vs {frow(pg)} at {PLAN_V28_GNC:g} s, paired); stale or missing flag: hold the last valid flag, default "
        f"{PLAN_V28_GNC:g} s (GNC decision, break-even prior {qtxt}): relight_planning_v28. B1 cap {B1_CAP_LEAD:g} m PROVISIONAL (lead; "
        f"GNC {cap:.1f} m rounded down): with the regression band and growth P {mcl.get('P')}, {mcl.get('n_exhausted')} runs "
        f"exhaust the liquid (85 m: P {mc85.get('P')}, {mc85.get('n_exhausted')} exhausted); the {B1_SIZING_H:g} m dispersed cycles "
        f"stay the conservative thermal and erosion sizing cases: b1_regression_band. Reference implementation {s6.SIM6_VERSION} "
        "(verification_v271). FC_THRUST over-thrust error budget: "
        + ("over_thrust_fc_thrust." if FCT else "OPEN (script staged, not run)."))
    fp = g["flight_profile"]["mission_plan_v3"]["v"]
    fp["A1"]["relight_v2.8"] = {
        "planning_value_s": P(PLAN_V28_GNC, "REQ lead decision 2026-10-13 (GNC rule adopted)"),
        "planning_value_unprimed_s": P(PLAN_V28_FAULT, "REQ lead decision 2026-10-13, option (c) PROVISIONAL"),
        "stale_or_missing_flag": P(stale_rule, "DESIGN GNC decision (lead request 2026-10-13)"),
        "P_by_line_state_at_planning_value": {b_: (sm.get(b_) or {}).get(pg) for b_ in sm},
        "P_fault_path_1.37s": {f"plan_{pg}s": {b_: (sm.get(b_) or {}).get(pg, {}).get("P_fault_1p37") for b_ in sm},
                               f"plan_{pf}s": {b_: (sm.get(b_) or {}).get(pf, {}).get("P_fault_1p37") for b_ in sm}},
        "P_at_withdrawn_1.41s_rule_primed_line": {b_: (sm.get(b_) or {}).get(pf, {}).get("P_by_state") for b_ in sm},
        "section": "relight_planning_v28"}
    fp["B1"]["h_target_m"] = P(B1_CAP_LEAD, "REQ lead decision 2026-10-13 (cap PROVISIONAL until T1-T4)",
                               f"the GNC cap {cap:.1f} m rounded down (b1_regression_band); the v3 planning value 85 m is kept as "
                               "h_sizing_m", )
    fp["B1"]["h_sizing_m"] = P(B1_SIZING_H, "REQ lead decision 2026-10-13",
                               "the B1 85 m dispersed duty cycles remain the conservative thermal and erosion sizing cases; the "
                               "P_landing_MC entries at 85 m are the 85 m evidence")
    fp["B1"]["h_target_status"] = (f"{B1_CAP_LEAD:g} m PROVISIONAL (lead 2026-10-13: the GNC {cap:.1f} m rounded down) until the T1-T4 "
                                   "regression data; 85 m (v3 planning value) kept for sizing (b1_regression_band.lead_cap)")
    fp["B1"]["P_landing_MC_regression_band"] = {"85m_band_growth": mc85.get("P"), "gnc_cap_band_growth": mcc.get("P"),
                                                "gnc_cap_m": cap, f"{B1_CAP_LEAD:g}m_band_growth": mcl.get("P"),
                                                f"{B1_CAP_LEAD:g}m_growth_only": mcl0.get("P"),
                                                f"{B1_CAP_LEAD:g}m_band_growth_n_exhausted": mcl.get("n_exhausted"),
                                                f"{B1_CAP_LEAD:g}m_band_growth_usable_left_p01_kg": mcl.get("usable_left_p01_kg")}
    rb_ = g["flight_profile"]["recommended_baseline"]
    rb_["note_v2.8"] = (f"relight on the v2.8 design: RELIGHT at the planned T_fire, NC valve and torch at E0, lift on torch "
                        f"confirmation, W 0.65 s; FSW planning value {PLAN_V28_GNC:g} s (lead decision 2026-10-13), {PLAN_V28_FAULT:g} s "
                        "on an ECU UNPRIMED flag (option (c), provisional) (relight_planning_v28; the 1.81 s of note_v3 belonged to "
                        f"the v2.7 sequence); B1 cap {B1_CAP_LEAD:g} m provisional (b1_regression_band)")
    g["flight_software"]["version"] += (
        f". v2.8 relight (lead 2026-10-13): planning value {PLAN_V28_GNC:g} s ADOPTED (Pc-confirm deadline rule), {PLAN_V28_FAULT:g} s on "
        "an ECU UNPRIMED flag (option (c), PROVISIONAL; stale or missing flag: hold the last valid flag, default "
        f"{PLAN_V28_GNC:g} s) (relight_planning_v28); reference implementation now {s6.SIM6_VERSION} (bit-identical with the new "
        "options off: verification_v271)")
    ig = g["requirements"]["ignition"]
    old_pv = ig.get("relight_planning_value_s")
    if isinstance(old_pv, dict) and "superseded_v2_7_sequence" in old_pv:   # idempotent on a rebuilt file
        old_pv = old_pv["superseded_v2_7_sequence"]
    ig["relight_planning_value_s"] = P(PLAN_V28_GNC, "REQ lead decision 2026-10-13 (the GNC rule adopted)",
                                       f"v2.8 relight: planning value = the flight Pc-confirm deadline (torch gate 0.16 s PROVISIONAL + "
                                       f"W 0.65 s = 0.81 s); P over the line states {prow(pg)}; the withdrawn 1.41 s rule: {prow(pf)} "
                                       "(relight_planning_v28)",
                                       superseded_v2_7_sequence=old_pv,
                                       option_c_unprimed_s=P(PLAN_V28_FAULT, "REQ lead decision 2026-10-13, option (c) PROVISIONAL",
                                                             "planning value while the ECU flag reports UNPRIMED"),
                                       stale_or_missing_flag=P(stale_rule, "DESIGN GNC decision (lead request 2026-10-13)",
                                                               stale.get("decision")))
    tk = g["requirements"]["tank"]["n2o_load_and_closure_v3"]
    tk["note_regression_band"] = (f"with the regression band (ASSUMED, Combustion RC-07) B1 closes the +25 % rule at every corner only "
                                  f"up to {cap:.1f} m; B1 cap {B1_CAP_LEAD:g} m PROVISIONAL (lead 2026-10-13) until T1-T4; the 'closes' "
                                  "entry above is the no-band nominal closure (b1_regression_band)")
    icd = g.get("icd_inputs_for_airframe", {})
    se = (icd.get("sequence_events_for_airframe") or {}).get("v")
    if se:
        se["relight_v2.8"] = (f"v2.8 (lead 2026-10-13): RELIGHT at the planned T_fire (FSW planning value {PLAN_V28_GNC:g} s, "
                              f"{PLAN_V28_FAULT:g} s on an ECU UNPRIMED flag), NC valve latched with the opener ramp and torch at E0, "
                              "lift at E1 on torch confirmation (gate 0.16 s provisional), Pc confirmation by E1 + 0.65 s; no retry; "
                              "legs deploy at the relight command; drogue release on Pc confirmation")
    if isinstance(icd.get("open"), list):
        icd["open"] = [x for x in icd["open"] if not x.startswith("relight sequence time: placeholder")
                       and not x.startswith("relight: v2.8 sequence times")] + [
            "relight: v2.8 sequence times are Electronics SIL/design values (torch gate provisional); option (c) needs the ECU "
            "PRIMED / UNPRIMED flag on the ECU -> FC link (Electronics, not yet in electronics.json)"]
    g["scripts"] = sorted(set(g["scripts"] + [f"{HUB}/sim/scripts/{s}" for s in (
        "m2_regband_model.py", "m2_regband_mc.py", "m2_bitcheck_v271.py", "m2_relight_v28.py", "m2_fc_thrust.py",
        "m2_dc_a1_v28_record.py", "m2_stage_hub_v3.py")] + [f"{HUB}/sim/gncsim/regband.py"]))
    ans = g["answers_to_requests"]
    ans["lead_regression_band_2026-10-13"] = rb["finding"]
    ans["lead_b1_cap_2026-10-13"] = rb["proposal"]
    if lc:
        ans["lead_b1_cap_62m_2026-10-13"] = lc.get("finding")
    ans["lead_relight_v28_2026-10-13"] = v28["finding"] + ". " + v28["planning_rule_gnc"] + ". " + v28["lead_rule_0p6_plus_0p81"]
    ans["lead_option_a_2026-10-13"] = ("(b) restores P at the planning value 0.81 s on every base and line state (relight_planning_v28): "
                                       "(a) hold-to-planned-light stays a research option and was not flown")
    if oc:
        ans["lead_option_c_2026-10-13"] = oc.get("finding", "") + ". STALE OR MISSING FLAG (GNC decision): " + stale.get("decision", "")
    ans["lead_early_light_2026-10-13"] = ("closed by the v2.8 design at the planning value 0.81 s (relight_planning_v28); the A1 p99 "
                                          "cycle of the earliest (liquid-line) lights is published as a record (duty_cycles index "
                                          "'records')")
    if FCT:
        ans["lead_over_thrust_fc_thrust_2026-10-13"] = g.get("over_thrust_fc_thrust", {}).get("v", {}).get("finding")
    g["requests"] = [r for r in g["requests"] if not r.startswith("REQUEST Electronics: publish in electronics.json the relight sequence")
                     and not r.startswith("REQUEST Electronics: publish the v2.8 relight sequence")
                     and not r.startswith("REQUEST Combustion: a recommended distribution for the regression band")
                     and not r.startswith("REQUEST lead: decide the relight planning value")] + [
        "REQUEST Electronics: publish the v2.8 relight sequence in electronics.json (flight worst E0 -> Pc-confirm deadline 0.81 s = "
        "torch gate 0.16 + W 0.65; unprimed fault path 1.37 s; SIL E0 -> RUN 0.26 / 0.50 s) with the firmware version, and the "
        "option (c) flag: PRIMED / UNPRIMED from the MECO valve closure to RELIGHT at >= 10 Hz, its staleness limit (GNC assumes "
        "0.3 s = 3 frames), and the ECU action at RELIGHT when P_feed is invalid (GNC asks for a distinct UNKNOWN state, or "
        "UNPRIMED whenever the ECU will run the prep; the FC treats UNKNOWN as UNPRIMED)",
        "REQUEST Electronics + Mechanical: the time a worst credible NC-valve seat leak needs to empty the primed segment (it bounds "
        "the GNC stale-flag rule: an emptying that starts and ends inside the staleness limit is not reported)",
        "REQUEST Combustion: a recommended distribution for the regression band (a, n) (GNC flies uniform x uniform); measured RC-03 "
        "latency (the E0 -> E2 distributions GNC flies are ASSUMED delay distributions); confirm the torch gate 0.16 s; the band "
        "web result at 85 m (< 1 mm at the high-a corners) stays a Combustion item (62 m burns are shorter)"]
    g["open_interface_issues"] = [x for x in g["open_interface_issues"] if not x.startswith("electronics.json v1 has no relight sequence")] + [
        "electronics.json v1 has no relight sequence and no PRIMED / UNPRIMED flag: GNC flies the v2.8 values relayed in "
        "interfaces/CHANGELOG.md (flight worst 0.81 s, fault path 1.37 s, torch gate 0.16 s PROVISIONAL), option (c) on the lead's "
        "provisional decision, and Combustion RC-03 E0 -> E2 (work-area file, ASSUMED delays)"]
    oi = []
    for x in g["open_items"]:
        if x.startswith("early relight lights (start delay below the 1.81 s planning value"):
            x = ("CLOSED in simulation by the v2.8 relight design at the planning value 0.81 s (lead decision 2026-10-13; "
                 "relight_planning_v28): early relight lights of the v2.7 sequence lost P")
        elif x.startswith("A1 sizing cycle (engine-on counter 8.26 s) does not bound early lights"):
            x += "; v2.8: the liquid-line A1 p99 cycle at 0.81 s is published as a record (duty_cycles index 'records')"
        elif x.startswith("relight latency: no measured distribution"):
            x = ("relight latency: Combustion RC-03 E0 -> E2 distributions are SIM on ASSUMED delay distributions (owner Combustion; "
                 "measure at IGN-1 / T1); the v2.8 sequence times are Electronics SIL / design values (owner Electronics)")
        elif x.startswith("accelerometer over-thrust abort (FC_THRUST"):
            x = ("accelerometer over-thrust abort (FC_THRUST): GNC error budget, Pc-lost branch and threshold proposal in "
                 "over_thrust_fc_thrust (simulation; the mass-estimate error is ASSUMED); firmware implementation and CAN latency "
                 "(owner Electronics); lead decides the threshold") if FCT else (
                "accelerometer over-thrust abort (FC_THRUST, 650 N / 20 ms provisional): OPEN, owner GNC. Not run in this "
                "release: the error budget script m2_fc_thrust.py v1 is staged in 01-systems-gnc/sim/scripts but was not run or "
                "reviewed, so no 3-sigma error, latency, false-abort rate, stuck-pintle detection time or threshold is published. "
                "Firmware implementation and CAN latency: owner Electronics")
        oi.append(x)
    g["open_items"] = [x for x in oi if not x.startswith("relight fault path (unprimed segment")
                       and not x.startswith("B1 cap:") and not x.startswith("B1 duty cycles (thermal and erosion sizing)")] + [
        f"relight fault path (unprimed segment, 1.37 s): lands only when planned on; option (c) ({PLAN_V28_FAULT:g} s on UNPRIMED) "
        "is provisional and needs the ECU flag (owner Electronics); its in-flight probability is unknown (seat leak rate, owner "
        "Mechanical / B-PNT-1)",
        f"stale or missing ECU flag: GNC rule = hold the last valid flag, default {PLAN_V28_GNC:g} s (single-fault argument); the "
        f"break-even prior of an unreported emptying is {qtxt}; owners: Electronics (staleness limit, UNKNOWN state), Mechanical / "
        "Electronics (segment drain time under a seat leak)",
        f"B1 cap: {B1_CAP_LEAD:g} m PROVISIONAL (lead 2026-10-13, GNC {cap:.1f} m rounded down) on the ASSUMED regression band "
        "(uniform x uniform); final after T1-T4 (owner lead / Combustion data)",
        f"B1 duty cycles: the {B1_SIZING_H:g} m dispersed cycles remain the conservative thermal and erosion sizing cases (lead "
        "2026-10-13); they were flown without the regression band; the 62 m runs with the band stay below them "
        "(b1_regression_band.lead_cap.engine_on_counter_vs_85m_sizing)",
        "NEW INPUT after these runs (lead decision 2026-10-13, MV-P/FS-01 Option A): the MV-to-seat segment becomes ~44 cm3 (to be "
        "measured on the v3.4 solids) instead of the 21.4 cm3 GNC flies in the abort tail-off bracket "
        "(flight_software.abort_shutdown); the relight fault path 1.37 s (prep re-run 0.56 s) and the RC-03 E0 -> E2 tables were "
        "derived on the old segment, and option (c) plans 1.41 s, only 0.04 s above 1.37 s. Owners: Combustion re-check on the "
        "44 cm3 segment, Electronics re-states the fault path; GNC re-runs the tail-off bracket and the option (c) fault cases on "
        "the new values"]
    g["changes_from_v2"] = [x for x in g["changes_from_v2"] if not x.startswith("2026-10-13: v2.8 relight")
                            and not x.startswith("2026-10-13: requirements.ignition.relight_planning_value_s")
                            and not x.startswith("2026-10-13: B1 regression band")
                            and not x.startswith(f"2026-10-13: {s6.SIM6_VERSION}")] + [
        f"2026-10-13: {s6.SIM6_VERSION}: regression-law band option (gncsim.regband) and start-delay quantile option; bit-identical "
        "with the options off (verification_v271)",
        f"2026-10-13: B1 regression band with throat growth (b1_regression_band): 85 m keeps P within the 500-run resolution but not "
        f"the propellant rule; GNC computed the cap {cap:.1f} m; the lead set {B1_CAP_LEAD:g} m provisional (Monte Carlo at "
        f"{B1_CAP_LEAD:g} m in lead_cap); the 85 m dispersed cycles stay the sizing cases",
        f"2026-10-13: v2.8 relight (relight_planning_v28): planning value {PLAN_V28_GNC:g} s (GNC deadline rule) adopted by the lead; "
        f"the 0.6 + 0.81 = 1.41 s rule withdrawn; option (c) ({PLAN_V28_FAULT:g} s on an ECU UNPRIMED flag) adopted provisionally "
        "and verified paired (fault path, fault spread, false-UNPRIMED cost); GNC stale / missing-flag rule",
        f"2026-10-13: requirements.ignition.relight_planning_value_s = {PLAN_V28_GNC:g} s (lead decision; the v2.7 1.81 s kept as "
        "superseded_v2_7_sequence; option_c_unprimed_s and stale_or_missing_flag added)",
        f"2026-10-13: flight_profile.mission_plan_v3.B1.h_target_m = {B1_CAP_LEAD:g} m (lead cap, provisional); h_sizing_m = 85 m"] + (
        ["2026-10-13: over_thrust_fc_thrust (FC_THRUST estimate error, latency, false aborts, stuck-pintle detection, threshold "
         "proposal)"] if FCT else [])
    if "the 2026-10-13 afternoon items" not in g["publication_note"]["built_on"]:
        g["publication_note"]["built_on"] += f"; the 2026-10-13 afternoon items on {s6.SIM6_VERSION} (verification_v271)"

# ---------------------------------------------------------------------------------------------------------- main
def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    v2 = jl(V2PUB)
    relay = jl(RELAY)
    src = R.sources()
    comb, el, mech = src["comb"], src["el"], src["mech"]
    if str(mech.get("version")) == "v1":
        raise SystemExit("gnc.json v3 is built on mechanical.json v2 (GNC_IFACE = iface_v3c)")
    mechB = jl(os.path.join(IFACE_B, "mechanical.json"))
    CFE = jl(os.path.join(CF, "ctrlfix_eval_cf.json")) or {}
    MEV = (jl(os.path.join(MECO, "meco_eval_mr.json")) or {}).get("cases", {})
    MNOM = jl(os.path.join(MECO, "meco_nominal_mr.json"))
    C3 = jl(os.path.join(CSI_FEA, "csi_v3_fea.json"))
    CSI3 = jl(os.path.join(CSI_M2, "csi_v3_m2.json"))
    RB = jl(os.path.join(V3A_RES, "rebaseline_v2_v3a.json")) or {}
    AS2 = jl(os.path.join(RES2, "actuator_study_v2.json")) or {}
    T26 = jl(os.path.join(CHK26, "v26_tests.json"))
    B26 = jl(os.path.join(CHK26, "bitcheck_v26_vs_v25.json"))
    PC2 = jl(os.path.join(PC2_OUT, "prop_closure_pc2.json"))
    PC1 = jl(os.path.join(PC_OUT, "prop_closure_pc.json"))
    PCE = jl(os.path.join(PCE_OUT, "prop_closure_eval.json"))
    MV2 = jl(os.path.join(MV2C, "mech_v2_check.json"))
    MS = jl(os.path.join(MV2MC, "mc6_summary_m2.json"))
    NS = jl(os.path.join(NSW, "n_sweep.json"))
    DCI = jl(os.path.join(DC3, "duty_cycles_index_v3.json"))
    VH = jl(os.path.join(VEH3, "vehicle_v3d.json"))
    TWD = rcsv(os.path.join(VEH3, "twd_table_v3d.csv"))
    RP = jl(os.path.join(REPRO, "repro_check_v26.json"))
    RF = jl(os.path.join(MECO, "history_before_nominal_tign_fix", "refly_mc_identical.json"))
    # 2026-10-13 results (v4 of this script)
    TG_ = jl(os.path.join(TGO, "throat_growth.json"))
    TGA_ = jl(os.path.join(TGA, "throat_growth.json"))
    AB = jl(os.path.join(ABO, "abort_tailoff.json"))
    T27 = jl(os.path.join(V27, "v27_tests.json"))
    T27v1 = jl(os.path.join(V27, "v27_tests_v1.json"))
    B27 = jl(os.path.join(V27, "bitcheck_v27_vs_v26.json"))
    B26b = jl(os.path.join(V27, "bitcheck_v26_vs_v25.json"))
    T26on27 = jl(os.path.join(V27, "v26_tests_on_v27_v3c", "v26_tests.json"))
    KF = jl(os.path.join(V27, "kest2_forensics.json"))
    KF1 = jl(os.path.join(V27, "kest2_forensics_v1.json"))
    DCB = jl(os.path.join(DC3, "dc_burn_check.json"))
    RSSJ = jl(os.path.join(RSS, "relight_seq_sens.json"))
    RL = jl(os.path.join(RL181_OUT, "relight_181.json"))
    RBM = jl(os.path.join(RBO, "regband_mc.json"))
    RBMOD = jl(os.path.join(RBO, "regband_model_v1.json"))
    BC271 = jl(os.path.join(V271, "bitcheck_v271.json"))
    BC271_0 = jl(os.path.join(V271, "bitcheck_v271_pre_tq.json"))
    V28 = jl(os.path.join(RV28, "relight_v28.json"))
    FCT = jl(os.path.join(FCTO, "fc_thrust.json"))
    for nm, x in (("prop_closure_pc2", PC2), ("mech_v2_check", MV2), ("mechv2_mc", MS), ("csi_v3_m2", CSI3), ("n_sweep", NS),
                  ("duty_cycles_v3", DCI), ("vehicle_v3d", VH), ("ctrlfix_eval", CFE), ("meco_eval", MEV),
                  ("throat_growth", TG_), ("throat_growth_a1k2", TGA_), ("abort_tailoff", AB), ("v27_tests", T27),
                  ("v27_tests_v1", T27v1), ("bitcheck_v27", B27), ("bitcheck_v26_on_v27", B26b), ("v26_tests_on_v27", T26on27),
                  ("kest2_forensics", KF), ("kest2_forensics_v1", KF1), ("dc_burn_check", DCB), ("relight_seq_sens", RSSJ),
                  ("relight_181", RL), ("regband_mc", RBM), ("regband_model", RBMOD), ("bitcheck_v271", BC271), ("relight_v28", V28)):
        if not x:
            raise SystemExit(f"missing result: {nm}")
    if "burn_time_definition" not in DCI:
        raise SystemExit("duty_cycles_index_v3.json is not revision b (burn_time_definition missing)")
    if (T27 or {}).get("n_fail") != 0 or (T26on27 or {}).get("n_fail") != 0 or not (B27 or {}).get("bit_identical"):
        print("WARNING: v2.7 verification not clean:", (T27 or {}).get("n_fail"), (T26on27 or {}).get("n_fail"), (B27 or {}).get("bit_identical"))
    hinge_tab = {c: hinge(os.path.join(CF, f"mc6_runs_{c}_cf.csv")) for c in CFE}
    for c in ("mr_J2.7_fix_td72", "mr_J1.6_fix_td72"):
        hinge_tab[c] = hinge(os.path.join(MECO, f"mc6_runs_{c}_mr.csv"))

    g = copy.deepcopy(v2)
    g.pop("publication_note", None)
    g["version"] = "v3"
    g["date"] = DATE
    g["supersedes"] = "gnc.json v2 (2026-10-12, published to the hub 20:34Z; sim6 v2.4, v1 interface snapshot)"
    mvb = mech_v2_rebaseline(MV2, MS, None, CSI3, NS, CFE, mechB, mech, el, relay)
    E = eng07d_v3(MS, CSI3, NS, mech, el, relay, mvb, RL=RL)
    planning_v = E["planning_value"]["v"]
    pl_mc = float(RL["mapping"]["late"]["t_ign_est_s"])
    if abs(planning_v - pl_mc) > 1e-9:
        raise SystemExit(f"planning value {planning_v} differs from the Monte Carlo planning value {pl_mc}")
    mcA = dict(TG_["monte_carlo"], **TGA_["monte_carlo"])
    mcA.update(RL["monte_carlo"])
    cur = {"A1 pc2 basis, no growth (rl181_A1_none_k2)": "rl181_A1_none_k2", "A1 pc2 basis, growth 7-11 % (rl181_A1_pc_k2)": "rl181_A1_pc_k2",
           "A1 ENG-07d basis, no growth (rl181_A1J_none_k2)": "rl181_A1J_none_k2",
           "A1 ENG-07d basis, growth 7-11 % (rl181_A1J_pc_k2)": "rl181_A1J_pc_k2",
           "B1 85 m pc2 basis, no growth (tg_B1_none_k2)": "tg_B1_none_k2", "B1 85 m pc2 basis, growth 7-11 % (tg_B1_pc_k2)": "tg_B1_pc_k2"}
    P_cur = {lab: dict(P=mcA[c]["P"], ci95=mcA[c]["ci95"], fail_modes=mcA[c].get("fail_modes")) for lab, c in cur.items() if c in mcA}
    prev17 = {"A1 pc2 basis, no growth (tg_A1_none_k2)": "tg_A1_none_k2", "A1 pc2 basis, growth 7-11 % (tg_A1_pc_k2)": "tg_A1_pc_k2",
              "A1 ENG-07d basis, no growth (tg_A1J_none_k2)": "tg_A1J_none_k2", "A1 ENG-07d basis, growth 7-11 % (tg_A1J_pc_k2)": "tg_A1J_pc_k2"}
    P_prev17 = {lab: dict(P=mcA[c]["P"], ci95=mcA[c]["ci95"]) for lab, c in prev17.items() if c in mcA}
    early = {"A1 pc2 basis, no growth (rl181e_A1_none_k2)": "rl181e_A1_none_k2", "A1 pc2 basis, growth (rl181e_A1_pc_k2)": "rl181e_A1_pc_k2",
             "A1 ENG-07d basis, no growth (rl181e_A1J_none_k2)": "rl181e_A1J_none_k2",
             "A1 ENG-07d basis, growth (rl181e_A1J_pc_k2)": "rl181e_A1J_pc_k2"}
    P_early = {lab: dict(P=mcA[c]["P"], ci95=mcA[c]["ci95"], fail_modes=mcA[c].get("fail_modes")) for lab, c in early.items() if c in mcA}
    g["status"] = (
        E["status"] + " M2 v4 (2026-10-13), lead decisions of 2026-10-13: flight software v2.7 PROVISIONAL (k_est_asc 2 thrust-"
        "effectiveness estimator on both profiles until the independent GNC review; reference implementation sim6/run6 v2.7-dev, "
        "bit-identical to v2.6 with the new options off), throat growth 7-11 % flown with P with and without, relight planning "
        f"value {planning_v:g} s (0.6 s + Electronics' worst-case sequence 1.21 s, lead decision (2); lights EARLIER than planned "
        "lose P: relight_planning_181; superseded later the same day by the v2.8 design below), no in-flight relight retry with the no-light accounting, abort law (NC valve "
        "de-energised at once, pintle closed in parallel), dispersed duty cycles as the sizing cases (index revision "
        f"{dci_rev(DCI)}: thrust-on burn time since 2026-10-13b, airborne / leg-contact axial maxima since 2026-10-13c). P on the v2.7 relight sequence (500 runs; A1 at the 1.81 s planning value, LATE bracket): " + "; ".join(f"{k} {v['P']}" for k, v in P_cur.items())
        + "; A1 EARLY-light bracket: " + "; ".join(f"{k} {v['P']}" for k, v in P_early.items())
        + ". B1 is flown on the pc2 basis only.")
    files = {}
    for lab, d_ in (("iface_v3c", IFACE), ("iface_v3b", IFACE_B), ("iface_v3a", IFACE_A)):
        fs = {}
        for fn in ("combustion.json", "electronics.json", "mechanical.json", "ENGINE-BASELINE-v0.json", "throttle_map_v2.csv",
                   "actuator_rate_check_v2.json"):
            p = os.path.join(d_, fn)
            if os.path.exists(p):
                fs[fn] = dict(version=(jl(p) or {}).get("version") if fn.endswith(".json") else None, sha256=sha(p))
        files[lab] = fs
    g["publication_note"] = {
        "built_on": (f"sim6/run6 v2.6 for the 2026-10-12 evidence and {s6.SIM6_VERSION} for the 2026-10-13 evidence (v2.7 with its new "
                     "options off reproduces v2.6 and v2.5 runs bit for bit: verification_v27); primary interface set iface_v3c = "
                     f"combustion.json {comb.get('version')}, mechanical.json {mech.get('version')}, electronics.json "
                     f"{el.get('version')} (sha256 in inputs_read)"),
        "bases": {"iface_v3c": "propellant closure, mechanical.json v2 checks and Monte Carlo, CSI frequency target, stiffness "
                               "target, linkage-ratio sweep, duty cycles v3, vehicle v3d, icd_inputs_for_airframe, and every "
                               "2026-10-13 item (throat growth, k_est_asc 2, relight placeholder, abort tail-off, dispersed duty "
                               "cycles, verification_v27)",
                  "iface_v3b": "paired flight-software evidence (control fix, MECO throttle-down, relight start rule, NC-closed relight, "
                               "anti-windup, reduced bandwidth on v1): combustion.json v2.2 is identical to v2.3 in every section GNC "
                               "reads (operating points, igniter, pintle speed checks, full stroke, isolation valve)",
                  "iface_v3a": "attribution of the engine model and the v2.6 bit-identity check"},
        "carried_from_v2": "sections not re-run keep their v2 content (carried_from_v2)",
        "not_physical_acceptance": "simulation and analysis only; no item here is a bench or flight validation"}
    g["inputs_read"] = dict(v2["inputs_read"], **{
        "interface_sets": files,
        "lead_relay_mech_fea_k_20261012.json": dict(sha256=sha(RELAY), note="lead relay of Mechanical FEA (CAD v3.3), Electronics J_int; "
                                                    "the FEA stiffness is superseded by mechanical.json v2; J_int still read from it"),
        "tailoff_fit_v1.json": dict(sha256=sha(TOFF_FIT), note="GNC fit of the reduced shutdown model to Combustion's runs"),
        "gnc.json_v2": dict(sha256=sha(V2PUB), note="published 2026-10-12 20:34Z; base of this file"),
        "electronics_firmware_v2.6_notch": dict(files={k: sha(os.path.join(FW, k)) for k in ("config.h", "filters.h", "engine_ecu.cpp")},
                                                note="Electronics firmware work area (read-only for GNC): per-axis notch set from B-TVC-1, "
                                                     "required for ignition; the 2000 deg/s2 tracker and the governor are not yet in it")})
    for k in ("throttle_map_initial_port_v1.csv", "lead_relay_combustion_v2_20261012.json", "engine_correction_v2.json"):
        if k in g["inputs_read"]:
            x = g["inputs_read"][k]
            g["inputs_read"][k] = dict(x if isinstance(x, dict) else {"v": x}, status="v2 only (superseded by combustion.json v2.x)")
    g["scripts"] = sorted(set(v2.get("scripts", []) + [f"{HUB}/sim/scripts/{s}" for s in (
        "m2_ctrlfix_mc.py", "m2_ctrlfix_eval.py", "m2_meco_mc.py", "m2_meco_eval.py", "m2_meco_nominal.py", "m2_tailoff_fit.py",
        "m2_csi_v3.py", "m2_v26_tests.py", "m2_bitcheck_v26.py", "m2_rebaseline_compare.py", "m2_repro_check.py",
        "m2_prop_closure.py", "m2_prop_closure_eval.py", "m2_mech_v2_check.py", "m2_mechv2_mc.py", "m2_n_sweep.py",
        "m2_duty_cycles_v3.py", "m2_vehicle.py", "m2_gnc_json_v3.py", "m2_throat_mc.py", "m2_bitcheck_v27.py", "m2_v27_tests.py",
        "m2_kest2_forensics.py", "m2_abort_tailoff.py", "m2_duty_cycles_disp.py", "m2_dc_burn_check.py", "m2_relight_seq_sens.py",
        "m2_dc_index_diff.py", "m2_relight_181.py", "m2_rl181_trace.py")]))
    g["lead_decisions_2026-10-13"] = lead_decisions_1013()

    # ------------------------------------------------------------------ lead decisions recorded
    ld = g.get("lead_decisions_2026-10-12", {})
    ld["tvc_actuator"] = P({k: v for k, v in LEAD3.items() if k != "source"}, "REQ lead decisions 2026-10-12", LEAD3["source"])
    ld["pintle_drive_and_engine_rules"] = P(
        "MKS HV69 in-line pintle drive (~0.25 s full stroke); ENG-05 met by the pre-MECO throttle-down to <= 75 % (REQUIRED); "
        "NC isolation valve closed through the MECO coast until B-PNT-1 measures the pintle seat leak-tightness",
        "REQ lead decisions 2026-10-12 (interfaces/CHANGELOG.md + lead messages)")
    ld["servo_J_int"] = P({"central_kgm2": relay["J_int_servo_output_kgm2"]["v"]["central"], "range_kgm2": relay["J_int_servo_output_kgm2"]["v"]["range"]},
                          "lead relay of the Electronics estimate (servo_jint_estimate_v1)",
                          "lumping on the engine side is the conservative simplification; keep SB-2292SG, control-side fix first, "
                          "maxon ECX 22 M contingency (TO-QUOTE)")
    ld["eng07d_closure"] = P({"K_struct_min_Nm_per_rad": LEAD_V3["K_struct_min_Nm_per_rad"], "K_struct_goal_Nm_per_rad": LEAD_V3["K_struct_goal_Nm_per_rad"],
                              "notch": "REQUIRED, separate alpha / beta centres (Electronics implements)",
                              "btvc1_gate": f"gating early test; K_s at the output below ~{LEAD_V3['btvc1_Ks_gate_Nm_per_rad']:g} N m/rad -> "
                                            "actuator contingency or reduced bandwidth (GNC v3: reduced bandwidth re-tuned flies at a P "
                                            "cost but does not lower the frequency target with the notch; actuator contingency is the "
                                            "fallback, mech_v2_rebaseline.reduced_bandwidth_fallback)",
                              "eng07_wording": "slew >= 100 deg/s at the 7.4 V nominal plug; the 6.6 V case accepted on the GNC MC",
                              "hose_routing_rule_K_max_Nm_per_rad": LEAD_V3["hose_K_max_Nm_per_rad"]},
                             "REQ lead decisions 2026-10-12", LEAD_V3["source"])
    ld["oi1_propellant"] = P({"option": "(a)", "tank": "2.00 kg / 3.17 L", "A1": "baseline flight (nose drogue + fins, 300 m)",
                              "B1": "capped at 85 m", "B2": "unchanged (50 m)", "A2": "removed from the 2.00 kg plan; 2.20 kg / 3.49 L "
                              "fallback documented", "ratchet": "adopted", "n": "4.8 confirmed by the n sweep"},
                             "REQ lead decision 2026-10-12 (logged in interfaces/CHANGELOG.md)", LEAD_V3["source"])
    if "gimbal_stiffness_fea" in ld:
        ld["gimbal_stiffness_fea"]["status"] = "superseded by mechanical.json v2 (published) for the stiffness; kept as history"
    g["lead_decisions_2026-10-12"] = ld

    # ------------------------------------------------------------------ engine model and attribution
    em = g["engine_model"]
    em["v3_engine"] = P(f"combustion.json {comb.get('version')} published throttle map (S230 grain) on mechanical.json {mech.get('version')} "
                        "(run6 v2.6)", f"combustion.json {comb.get('version')} + DERIVED", "replaces the v1 map x relay factors of gnc.json v2")
    em["shutdown_model_v3"] = P("lift-ramp tail-off: lift command closes at the HV69 speed from the lift of the pre-shutdown thrust "
                                "on Combustion's static table; actuator lag and chamber lag fitted by GNC to Combustion's t10 and "
                                "tail-off impulse (gncsim.tailoff, sim6 toff_model 1)",
                                "DERIVED GNC fit to SIM Combustion grain_q1d v2 (actuator_rate_check_v2.json)",
                                f"fit file {HUB}/sim/data/tailoff/tailoff_fit_v1.json; residuals t10 within 2 ms, impulse within 7 %")
    rbm = RB.get("cases", {})
    g["attribution_v3a"] = P(rnd({
        "what": "the v2 vehicle (mechanical.json v1) with only the engine model changed to combustion.json v2.x (published map)",
        "cases": {c: dict(P_old=r["P_old"], P_new=r["P_new"], lost=r["lost"], gained=r["gained"], mcnemar_exact_p=r["mcnemar_exact_p"],
                          loses=r["loses"], m_liftoff_old=r["m_liftoff_old"], m_liftoff_new=r["m_liftoff_new"]) for c, r in rbm.items()},
        "material_by_rule": RB.get("material"), "rule": RB.get("rule")}, 4),
        "SIM m2_mc6 v3a vs v2 (same 500 draws) + DERIVED m2_rebaseline_compare", "no case loses P")

    # ------------------------------------------------------------------ reference vehicle v3d
    rv, tw = vehicle_v3d(VH, TWD, g["reference_vehicle"])
    g["reference_vehicle"] = rv

    # ------------------------------------------------------------------ flight profile / mission plan
    fp = g["flight_profile"]
    clA1 = PC2["closure"]["A1"]["at_2kg"]
    fp["mission_plan_v3"] = P(rnd({
        "A1": {"role": "BASELINE flight", "profile": "A-D: TVC ascent, pre-MECO throttle-down, nose-first coast with aft fins, nose "
               "drogue at apogee, NC-closed relight, throttled TVC landing", "apogee_target_m": LEAD_V3["A1_h_m"],
               "nominal_fsw_v2.6_planning_1.4s": {k: clA1[k] for k in ("h_max", "h_ign", "v_ign", "burn_time_s", "n2o_burned", "reserve_frac",
                                                                     "m_liftoff", "TW_liftoff")},
               "nominal_relight_placeholder_planning_1.7s": {k: ((RSSJ.get("nominal") or {}).get("A1|+0.3s|planned") or {}).get(k)
                                                             for k in ("h_max", "h_ign", "v_ign", "burn_time_s", "n2o_burned",
                                                                       "reserve_frac", "reserve_frac_minus_purge_bound")},
               "P_landing_MC_ENG07d_basis_fsw_v2.6_planning_1.4s": (mvb.get("monte_carlo", {}).get("v", {}).get("m2_J1.6_n15") or {}).get("P"),
               "nominal_relight_planning_1.81s": {k: ((RL.get("nominal") or {}).get("A1|late_1.81s|k2") or {}).get(k)
                                                  for k in ("h_max", "h_ign", "v_ign", "burn_time_s", "n2o_burned", "reserve_frac",
                                                            "reserve_frac_minus_successful_relight_sil",
                                                            "reserve_frac_minus_no_light_inventory_sil", "nominal_start_delay_s")},
               "nominal_early_light_planning_1.81s": {k: ((RL.get("nominal") or {}).get("A1|early_1.81s|k2") or {}).get(k)
                                                      for k in ("h_ign", "burn_time_s", "n2o_burned", "reserve_frac",
                                                                "reserve_frac_minus_no_light_inventory_sil", "nominal_start_delay_s")},
               "P_landing_MC_current_fsw_v2.7": {k: v for k, v in P_cur.items() if k.startswith("A1")},
               "P_landing_MC_early_light_bracket": P_early,
               "P_landing_MC_previous_placeholder_1.7s": P_prev17,
               "P_total_with_no_light": "no_light_accounting (P_6DOF x (1 - p_nl), p_nl ASSUMED placeholder table)"},
        "B1": {"role": "development hop (continuous burn, 20 % floor)", "h_target_m": LEAD_V3["B1_h_m"],
               "P_landing_MC_fsw_v2.6": ((PCE or {}).get("bases", {}).get("pc2", {}).get("cases", {}).get("pc_B1_h85_2kg") or {}).get("P"),
               "P_landing_MC_current_fsw_v2.7": {k: v for k, v in P_cur.items() if k.startswith("B1")},
               "basis_note": "B1 is flown on the pc2 basis only (v3 FSW with the ratchet, mechanical.json v2, no ENG-07d servo-pair "
                             "case); the B1 85 m propellant margin is thin (b1_dispersed_burn) and its 7-8 m/s gust cases are a "
                             "launch-commit wind item (requests)"},
        "B2": {"role": "development hop (unchanged)", "h_target_m": LEAD_V3["B2_h_m"]},
        "A2": {"role": "REMOVED from the 2.00 kg plan (finless free-fall 300 m); 2.20 kg / 3.49 L fallback in propellant_closure_v3"},
        "first_flights": "30-100 m (charter): B2 then B1, before A1"}, 4),
        "REQ lead decisions 2026-10-12 (OI-1 option (a)) and 2026-10-13 (FSW v2.7 provisional, relight planning value 1.81 s) + SIM")
    rb_ = fp.get("recommended_baseline", {})
    rsp_ = (RL.get("monte_carlo") or {}).get("rl181_A1_none_k2") or {}
    hc_ = rsp_.get("relight_cmd_h_p01_p50_m") or [float("nan"), float("nan")]
    rb_["note_v3"] = ("v3 sequence: full-thrust ascent under TVC -> 72 % throttle-down near the predicted apogee -> MECO (lift-ramp "
                      "tail-off, NC valve closed) -> nose-first coast with fins -> nose drogue at apogee -> NC-closed relight planned on "
                      f"{planning_v:g} s (0.6 s + Electronics' worst-case sequence 1.21 s) at ~{hc_[0]:.0f}-{hc_[1]:.0f} m (MC p01-p50 "
                      "of the command altitude, relight_planning_181; early lights are an open item) and ~22 m/s -> drogue released on Pc "
                      "confirmation (no retry: a no-light is a mission loss) -> throttled TVC landing (governor with ratchet, k_est_asc 2 "
                      "landing-burn estimator) -> 8 m gate -> touchdown ~1 m/s -> engine cut on contact")
    fp["recommended_baseline"] = rb_
    g["flight_profile"] = fp

    # ------------------------------------------------------------------ flight software v2.6 -> v2.7 (provisional)
    g["flight_software"] = fsw_section(CFE, MEV, MNOM, hinge_tab)
    g["flight_software"]["version"] = (
        "flight software v2.7 PROVISIONAL (lead 2026-10-13) = v2.6 (tracker, governor with ratchet, pre-MECO throttle-down, relight "
        "start rule, NC-closed relight) + k_est_asc 2 thrust-effectiveness estimator on both profiles + relight planning value "
        f"{planning_v:g} s on the v2.7 sequence (lead decision (2); superseded by the v2.8 relight, below) + abort law + no in-flight relight retry; GNC reference implementation {s6.SIM6_VERSION}; FC "
        "items owned by GNC, ECU items implemented by Electronics; final only after the independent GNC review")
    g["flight_software"]["relight_nc_valve_closed"] = P(rnd({"sequence_times_s": __import__("m2_meco_mc").NCS, "cases": nc_relight(MEV)}, 4),
                                                        "SIM m2_meco mr (same 500 draws, iface_v3b) + m2_meco_eval; sequence times from "
                                                        "combustion.json", E["nc_note"])
    g["flight_software"]["eng07d_notch"] = P(E["notch_spec"], "DESIGN GNC from SIM m2_csi_v3 (mech_v2_rebaseline) + REQ lead", E["notch_note"])
    g["flight_software"]["thrust_effectiveness_estimator_k_est_asc_2"] = kest2_section(TG_, TGA_, T27, KF, KF1)
    g["flight_software"]["relight_sequence_placeholder"] = relight_placeholder_section(RSSJ, TG_, planning_v)
    g["relight_planning_181"] = relight_181_section(RL, RL181_OUT, DCI)
    g["relight_planning_v28"] = relight_v28_section(V28, PLAN_V28_GNC, PLAN_V28_FAULT)
    g["b1_regression_band"] = regband_section(RBM, RBMOD, DCI)
    g["verification_v271"] = verification_v271(BC271, BC271_0)
    if FCT:
        g["over_thrust_fc_thrust"] = fc_thrust_section(FCT)
    g["flight_software"]["relight_no_retry"] = no_retry_section(comb)
    ABS = abort_section(AB, src["tab"])
    g["flight_software"]["abort_shutdown"] = ABS

    # ------------------------------------------------------------------ requirements
    rq = g["requirements"]
    gm = rq["gimbal"]
    gm["angular_accel_min_rad_s2"] = P(rnd(np.radians(FSW["gim_cmd_acc_dps2"]), 1),
                                       "REQ-derived from SIM m2_ctrlfix: flight software v2.6 commands at most 2000 deg/s2",
                                       "v2 value 87.3 rad/s2 superseded (mechanical.json v2 hinge terms still quote it: conservative). "
                                       "B-TVC-1 verifies the delivered acceleration on the engine-inertia dummy")
    cases2 = AS2.get("cases") or {}
    h48 = sorted(((r["saturation"]["delivered_hinge_moment_Nm"]["max"], c, r["J_int_servo_kgm2"], r["servo_V"])
                  for c, r in cases2.items() if r["n"] == 4.8 and r["J_int_servo_kgm2"] <= 4e-3), reverse=True)
    mcv = mvb.get("monte_carlo", {}).get("v", {})
    hm = gm.get("hinge_moment", {})
    hose_rng = mech["feed_across_gimbal"]["hinge_stiffness_Nm_per_rad"]["v"]
    gm["hinge_moment"] = P(rnd({
        "design_load_engine_moment_Nm": LEAD3["design_load_Nm"],
        "mechanical_v2_structural_design_load_Nm": mech["tvc_actuation"].get("hinge_moment_design_Nm", {}).get("v"),
        "delivered_mech_v2_MC_p99_max_Nm": {c: [mcv[c]["hinge_Nm"]["p99"], mcv[c]["hinge_Nm"]["max"]] for c in mcv if "hinge_Nm" in mcv[c]},
        "n48_actuator_study_delivered_max_Nm": h48[0][0] if h48 else None,
        "n48_actuator_study_max_case": (f"{h48[0][1]} (J_int {h48[0][2]:g} kg m2, {h48[0][3]:g} V)" if h48 else None),
        "fsw_v2_6_delivered_p99_max_Nm_v3b": {c: [hinge_tab[c]["p99_Nm"], hinge_tab[c]["max_Nm"]] for c in
                                              ("cf_J1.6_acc2000_ref40", "cf_J2.7_acc2000_ref40", "cf_J4_acc2000_ref40", "mr_J2.7_fix_td72")
                                              if hinge_tab.get(c)},
        "hose_budget": {"routing_rule_K_max_Nm_per_rad": LEAD_V3["hose_K_max_Nm_per_rad"],
                        "moment_at_7deg_Nm": LEAD_V3["hose_K_max_Nm_per_rad"] * np.radians(7.0),
                        "mechanical_v2_range_Nm_per_rad": hose_rng,
                        "in_6dof": f"parallel spring on the engine, drawn U({hose_rng[0]}, {hose_rng[1]}) N m/rad (mechanical.json "
                                   f"{mech.get('version')} feed_across_gimbal, ASSUMED there); inside the delivered moments above"},
        "v2_reference_servo_flight_p99_max_Nm": [hm.get("v", {}).get("flight_p99_Nm"), hm.get("v", {}).get("flight_max_Nm")]}, 2),
        "REQ lead decision 2026-10-12 (design load) + SIM m2_mechv2_mc / m2_ctrlfix / m2_actuator_study (delivered per-axis moment)",
        "the 35.3 N m design load (Mechanical as-built 37.95 N m governs the structure) covers every Monte Carlo case with margin "
        ">= 1.9; CORRECTION kept from the v3 draft: the n 4.8 actuator-study maximum is 28.5 N m (7.6 V, J 4e-3), not 26.8 N m")
    tvc = gm.get("tvc_actuator", {})
    tvc["linkage_ratio_n"] = P(LEAD3["linkage_ratio_n"], "REQ lead decision 2026-10-12 (FINAL; confirmed by the n sweep)")
    tvc["validated_plug_voltage_V_val_V"] = P(LEAD3["V_val_V"], "REQ lead decision 2026-10-12, from SIM (both-stall plug voltage)")
    tvc["arm_rule"] = P(f"predicted both-stall plug voltage >= {LEAD3['V_val_V']} V AND rest voltage >= {LEAD3['arm_rest_min_V']} V",
                        "REQ lead decision 2026-10-12 (ECU pad ARM permit; abort cause TVC_SUPPLY)")
    ld07 = mvb["eng07_slew_load_check"]["v"]
    tvc["ENG-07_slew"] = P(f">= {LEAD3['eng07_min_slew_dps_at_7V4']:g} deg/s worst direction at 7 deg at the 7.4 V nominal plug; the "
                           "6.6 V case is accepted on the GNC Monte Carlo",
                           "REQ lead decision 2026-10-12",
                           f"mechanical.json v2: 111.2 deg/s at 7.4 V under 3.19 N m (the v1 non-inertial sum); with the v2 terms "
                           f"({ld07['non_inertial_sum_mech_v2_Nm']} N m) GNC's extrapolation gives "
                           f"{ld07.get('slew_7deg_7V4_worst_dps', {}).get('under_mech_v2_sum')} deg/s and with the hose at the 20 N m/rad "
                           f"limit {ld07.get('slew_7deg_7V4_worst_dps', {}).get('under_sum_with_hose_at_limit')} deg/s: request to "
                           "Mechanical to recompute with the exact kinematics (mech_v2_rebaseline.eng07_slew_load_check)")
    cfx = g["flight_software"]["control_fix_evidence"]["v"]
    tvc["ENG-07b_max_saturation_episode_s"] = P(LEAD3["eng07b_max_episode_s"], "REQ lead decision 2026-10-12",
                                                f"MET with flight software v2.6 up to J_int {cfx['ENG07b_and_P_met_up_to_J_int_kgm2']} kg m2 "
                                                f"on v3b; on mechanical.json v2 every case keeps the longest episode <= 0.1 s "
                                                "(mech_v2_rebaseline.monte_carlo)", evidence="flight_software.control_fix_evidence")
    tvc["ENG-07c_J_int_check_value_kgm2"] = P(cfx["ENG07b_and_P_met_up_to_J_int_kgm2"], "SIM m2_ctrlfix (check value, flight software v2.6)",
                                              f"was a provisional requirement (<= {LEAD3['eng07c_J_int_max_kgm2_v2']} kg m2); with the v2.6 tracker "
                                              f"it is a check value: the Electronics estimate {relay['J_int_servo_output_kgm2']['v']['central']} kg m2 "
                                              f"(range {relay['J_int_servo_output_kgm2']['v']['range']}) is inside it; B-TVC-1 measures J_int")
    tvc["ENG-07d_flex_gain_margin_min_dB"] = P(LEAD3["eng07d_flex_gm_min_dB"], "REQ lead decision 2026-10-12", E["eng07d_note"],
                                               evidence="mech_v2_rebaseline")
    tvc["B-TVC-1"] = P(E["btvc1"], "REQ lead decision 2026-10-12 (gating early test for ENG-07b/c/d), scope by GNC v3")
    gm["tvc_actuator"] = tvc
    cs_ = gm.get("command_shaping_in_ecu", {})
    cs_["v"] = dict(cs_.get("v", {}), accel_limit_dps2=FSW["gim_cmd_acc_dps2"],
                    tracker="rate- and acceleration-limited (flight_software.gimbal_command_tracker)", eng07d_notch=E["notch_spec"])
    cs_["note"] = (cs_.get("note", "") + " v3: the plain slew limiter becomes the rate- and acceleration-limited tracker (2000 deg/s2); "
                   "ENG-07d notch REQUIRED per axis (flight_software.eng07d_notch).")
    gm["command_shaping_in_ecu"] = cs_
    rq["gimbal"] = gm
    st = rq["structure"]
    st["gimballed_engine_first_mode_min_Hz"] = P(E["mode_req"]["v"], E["mode_req"]["tag"], E["mode_req"]["note"])
    st["axis_stiffness_min_Nm_per_rad"] = P(E["k_target"]["v"], E["k_target"]["tag"], E["k_target"]["note"])
    st["rocking_mode_damping_min"] = P(E["damping"]["v"], E["damping"]["tag"], E["damping"]["note"])
    st["csi_margins_with_filter"] = P(E["csi_summary"], "SIM m2_csi_v3 (python-control, Pade-3 delay) on mechanical.json v2",
                                      "see mech_v2_rebaseline.csi_frequency_target")
    if tw:
        st["tail_wags_dog_zero_min_rad_s"]["note_v3"] = ("v3d (mechanical.json v2) at touchdown: 12.5 % "
                                                          f"{float(tw['touchdown|12.5 %']['w_twd_rad_s']):.2f} rad/s, 20 % "
                                                          f"{float(tw['touchdown|20.0 %']['w_twd_rad_s']):.2f} rad/s, hover "
                                                          f"{float(tw['touchdown|hover (T=W)']['w_twd_rad_s']):.2f} rad/s")
    rq["structure"] = st
    ig = rq["ignition"]
    tdm = MEV.get("mr_td72_nc", {})
    ig["latency_cmd_to_90pct_max_s"]["note"] = (
        f"v3: start rule (start at max(floor, 20 %), hold to 90 %); NC-closed relight (+0.80 s sequence): t90 "
        f"{tdm.get('t90_relight_s', {}).get('p01', float('nan')):.2f}-{tdm.get('t90_relight_s', {}).get('max', float('nan')):.2f} s from "
        "the relight command in the MC (flight_software.relight_nc_valve_closed)")
    ig["relight_planning_value_s"] = P(E["planning_value"]["v"], E["planning_value"]["tag"], E["planning_value"]["note"])
    ab100 = next((r for r in ABS["v"]["bracket"] if abs(r["level_frac_Fmax"] - 1.0) < 1e-9), {})
    ig["shutdown_tail_off"] = P("< 10 % thrust within 0.10 s", "REQ ENG-05",
                                "v3: met by the pre-MECO throttle-down (flight_software.meco_throttle_down) on Combustion's lift-ramp "
                                "shutdown at the HV69 0.25 s stroke; from 100 % it fails (0.12 s). An ABORT from 100 % (lead law "
                                "2026-10-13: NC valve de-energised at once, pintle closed in parallel) reaches 10 % at "
                                f"{(ab100.get('pintle_only_upper') or {}).get('t10_s', float('nan')):.2f} s with "
                                f"{(ab100.get('pintle_only_upper') or {}).get('impulse_Ns', float('nan')):.1f} N s: the 21.4 cm3 line feeds the closing "
                                "pintle after the valve shuts, so the valve does not shorten it (flight_software.abort_shutdown); "
                                "ENG-05 is a MECO requirement, an abort is not held to it")
    if "starts_per_flight_required" in ig:
        ig["starts_per_flight_required"]["note_v3"] = (
            "lead 2026-10-13: NO in-flight relight retry (a no-light is a mission loss); the >= 3 starts stay an igniter capacity "
            "(propane / N2O torch budget), not a flown spare relight (flight_software.relight_no_retry)")
    if "relight_conditions" in ig:
        ig["relight_conditions"]["note_v3"] = (
            "v3: NC isolation valve closed through the coast and opened by the relight sequence; no pad pre-purge (lead "
            "2026-10-13: B1 closes either way, relight_sequence_placeholder.evidence_nominal); no retry")
    rq["ignition"] = ig
    th = rq.get("throttle", {})
    tee = th.get("thrust_effectiveness_estimation", {})
    th["thrust_effectiveness_estimation"] = P(
        "k_est_asc 2 (flight software v2.7, PROVISIONAL): FC estimates k = delivered / Pc-map thrust from the accelerometer, the FSW "
        "mass estimate and a signed drag model (tau 0.1 s); B profile: gated t > 1 s and h_est > 1 m, floor and top-up commands "
        "divided by k_hat in [0.8, 1.25]; both profiles: landing guidance",
        "DESIGN GNC (sim6 v2.7-dev) + SIM m2_throat_mc / m2_v27_tests / m2_kest2_forensics",
        "needs Pc and the accelerometer at >= 100 Hz in the FC; flight_software.thrust_effectiveness_estimator_k_est_asc_2",
        v2_value=tee.get("v"))
    tgw = mcA.get("tg_B1_pc", {})
    th["throat_growth_tolerance"] = P(
        {"growth_band_frac": list(LEAD_1013["growth_band"]),
         "requirement": "the thrust loop and flight software keep P and the propellant rule with 7-11 % throat-area growth per flight",
         "status": (f"NOT met by flight software v2.6 with the ECU Pc loop on B1 85 m (P {tgw.get('P')}, {pr(tgw.get('vs_base'), 'no growth')}); "
                    f"met in simulation with k_est_asc 2 (B1 P {mcA.get('tg_B1_pc_k2', {}).get('P')}, A1 P {mcA.get('tg_A1_pc_k2', {}).get('P')} / "
                    f"{mcA.get('tg_A1J_pc_k2', {}).get('P')} ENG-07d basis; nominal B1 at g 0.11 closes the +25 % rule: "
                    "verification_v27 T11d); the erosion band itself is literature-scaled, not measured")},
        "REQ ENG-06 rev 2 / lead 2026-10-13 + SIM m2_throat_mc", "throat_growth")
    rq["throttle"] = th
    tk = rq.get("tank", {})
    tk["n2o_load_and_closure_v3"] = P({"n2o_kg": LEAD_V3["n2o_kg"], "tank_L": LEAD_V3["tank_L"], "rule": PC2["rule"]["text"],
                                       "closes": "A1 (40 % reserve), B1 at 85 m (closing limit 86.9 m), B2", "fallback": "2.20 kg / 3.49 L"},
                                      "REQ lead decision 2026-10-12 + SIM m2_prop_closure pc2", "propellant_closure_v3")
    rq["tank"] = tk
    g["requirements"] = rq

    # ------------------------------------------------------------------ new sections
    pcv3, _ = prop_closure_v3(PC2, PCE, PC1)
    tank = mech.get("fixed_module", {}).get("tank", {})
    if tank and pcv3.get("fallback_documented"):
        V0 = tank["internal_volume_L"]["v"]
        L0 = tank["internal_cyl_length_m"]["v"]
        Vf = pcv3["fallback_documented"]["v"]["tank_V_L"]
        mt = tank["tube_mass_kg"]["v"]
        pcv3["fallback_documented"]["v"]["tube_length_increase_m"] = rnd(L0 * (Vf / V0 - 1.0), 4)
        pcv3["fallback_documented"]["v"]["tube_mass_increase_kg"] = rnd(mt * (Vf / V0 - 1.0), 3)
        pcv3["fallback_documented"]["v"]["tube"] = tank["concept"]["v"]
    g["propellant_closure_v3"] = pcv3
    g["mech_v2_rebaseline"] = mvb
    g["csi_vs_6dof"] = P({"linear": "m2_csi_v3 on mechanical.json v2: margins below 6 dB below the frequency target; at mount damping "
                                    "0.02 without the notch some corners are unstable below ~20 Hz (unstable_corners_floor20 in "
                                    "mech_v2_rebaseline.csi_frequency_target)",
                          "6dof": f"m2_mechv2_mc on the published stiffness (12-22 Hz with J 1.6e-3): P {E['notch_note']}",
                          "candidate_reasons": ["the 6-DOF flies the torque/speed-limited servo pair (act_model 1), the linear model "
                                                "a 2nd-order servo with slow/fast/+3.2 ms corners",
                                                "the 6-DOF draws one stiffness and one damping for both axes per run",
                                                "the linear model includes an ASSUMED first airframe bending mode the 6-DOF does not",
                                                "the linear corners combine worst cases (12.5 % floor, slow servo, +3.2 ms) that "
                                                "the MC draws independently"],
                          "position": "ENG-07d stays a linear-margin requirement; the 6-DOF result is evidence, not a waiver. "
                                      "B-TVC-1 data decide"},
                         "SIM both models (kept as an open contradiction)")
    if C3:
        g["csi_v3_relay_fea"] = P({"status": "history: the first ENG-07d check on the lead-relayed FEA stiffness with mechanical.json v1 "
                                             "mass properties (I_pivot scaled to 0.052 kg m2); superseded by mech_v2_rebaseline",
                                   "file": f"{HUB}/results/csi_v3/csi_v3_fea.json",
                                   "f_target_relay_basis_Hz": {k: v["f_min_Hz"]["floor20"] for k, v in (C3.get("ftarget") or {}).get("cases", {}).items()}},
                                  "SIM m2_csi_v3 (relay basis)")
    g.pop("csi_v3_fea", None)
    # nominal-flight effect of k_est_asc 2 (the nominal duty cycles were flown with k_est_asc 0)
    nm_ = TG_["nominal"]
    kNom = "; ".join(
        f"{p}: burn (engine-on counter) {nm_[f'{p}|none']['burn_time_s']:.3f} -> {nm_[f'{p}|none|fsw_k2']['burn_time_s']:.3f} s, apex "
        f"{nm_[f'{p}|none']['h_max']:.2f} -> {nm_[f'{p}|none|fsw_k2']['h_max']:.2f} m, reserve {100 * nm_[f'{p}|none']['reserve_frac']:.2f} -> "
        f"{100 * nm_[f'{p}|none|fsw_k2']['reserve_frac']:.2f} %, N2O {nm_[f'{p}|none']['n2o_burned']:.4f} -> "
        f"{nm_[f'{p}|none|fsw_k2']['n2o_burned']:.4f} kg" for p in ("A1", "B1") if f"{p}|none" in nm_ and f"{p}|none|fsw_k2" in nm_) + (
        " (m2_throat_mc nominal flights, no dispersion): not re-flown, the difference is below the dispersed-case spread")
    g["duty_cycles"] = duty_cycles_v3_section(DCI, kNom)
    _rc = {c: (v.get("engine_on_counter_over_a1_sizing_cycle") or {}) for c, v in (RL.get("monte_carlo") or {}).items()}
    _lp = [v["p99_s"] for c, v in _rc.items() if c.startswith("rl181_") and v]
    _ep = [v["p99_s"] for c, v in _rc.items() if c.startswith("rl181e_") and v]
    _sz = next(iter(_rc.values()), {}).get("sizing_counter_s")
    g["duty_cycles"]["v"]["relight_planning_1.81s"] = (
        "the dispersed and nominal cycles were flown with the 1.7 s relight placeholder (t_ign_add 1.1 s). At the 1.81 s planning "
        f"value, planned (LATE) lights give an A1 engine-on counter p99 of {min(_lp):.2f}-{max(_lp):.2f} s, inside the A1 sizing "
        f"cycle ({_sz:.2f} s); early lights reach {min(_ep):.2f}-{max(_ep):.2f} s (relight_planning_181.a1_sizing_cycle). B1 (one pad "
        "start) does not depend on the relight timing and governs thermal and erosion (lead 2026-10-13)") if (_lp and _ep and _sz) else None
    g["throat_growth"] = throat_growth_section(TG_, TGA_)
    g["b1_dispersed_burn"] = b1_burn_section(TG_, DCI, DCB)
    g["no_light_accounting"] = no_light_section({k: v["P"] for k, v in P_cur.items() if k.startswith("A1")})
    q2 = notch_q2_proposal(CSI3)
    if q2:
        g["notch_q2_research_proposal"] = q2
    lc_rows = {}
    for c, s_ in mcv.items():
        lc_rows[f"mech_v2|{c}"] = dict(P=s_["P"], ci95=s_["ci95"], fail_modes=s_.get("fail_modes"),
                                       td_vz_p99=None, td_vh_p99=(s_.get("td_vh_mps") or {}).get("p99"),
                                       td_rate_p99=(s_.get("td_rate_dps") or {}).get("p99"), leg_force_p99_N=(s_.get("leg_force_N") or {}).get("p99"))
    for c, s_ in (pcv3.get("monte_carlo") or {}).items():
        lc_rows[f"closure|{c}"] = dict(P=s_["P"], ci95=s_["ci95"], fail_modes=s_.get("fail_modes"), note=s_.get("note"))
    g["landing_closure_v3"] = P(rnd(lc_rows, 4), "SIM m2_mechv2_mc + m2_prop_closure (iface_v3c, 500 runs each, same draws)",
                                "v2 landing_closure is kept below as history (sim6 v2.4, mechanical.json v1)")
    dl = g.get("design_limit_loads", {})
    base_rows = rcsv(os.path.join(MV2MC, "mc6_runs_m2_J1.6_n15_m2.csv"))
    if base_rows:
        dl["v3_check"] = P(rnd(mc_case(base_rows), 3), "SIM m2_mechv2_mc m2_J1.6_n15 (v3 baseline-like case)",
                           "compare with the v2 limit loads above; the v2 values stay the published limits until the airframe is known")
    g["design_limit_loads"] = dl
    g["icd_inputs_for_airframe"] = icd_v3(VH, tw, v2["icd_inputs_for_airframe"], PC2, MS, DCI, comb, mech, None,
                                          planning_v=planning_v, ABS=ABS, RSSJ=RSSJ, RL=RL)

    # ------------------------------------------------------------------ verification
    g["verification_v26"] = P({"tests": (T26 or {}).get("checks"), "n_fail": (T26 or {}).get("n_fail"),
                               "bit_identity_v26_defaults_vs_v25": (B26 or {}).get("bit_identical"),
                               "bit_identity_cases": {c: {k: v[k] for k in ("runs_checked", "values_compared", "mismatches")}
                                                      for c, v in ((B26 or {}).get("cases") or {}).items()},
                               "mech_v2_reading": {"n_fail": MV2.get("n_fail")},
                               "reproducibility": {"refly_shifted_cases_identical_mc": (RF or {}).get("identical") if RF else "pending",
                                                   "repro_v26": (RP or {}).get("identical") if RP else "pending"}},
                              "SIM m2_v26_tests + m2_bitcheck_v26 + m2_mech_v2_check + m2_repro_check")
    g["verification_v27"] = verification_v27(T27, T27v1, B27, B26b, T26on27, KF, KF1, DCB, DCI,
                                               jl(os.path.join(DC3, "dc_index_revc_check.json")))
    wcases = {"B1 85 m, FSW v2.6 (pc_B1_h85_2kg)": mcA["tg_B1_pc"].get("base_csv"),
              "B1 85 m, FSW v2.7 k_est_asc 2, no growth": os.path.join(TGO, "mc6_runs_tg_B1_none_k2_tg.csv"),
              "B1 85 m, FSW v2.7 k_est_asc 2, growth": os.path.join(TGO, "mc6_runs_tg_B1_pc_k2_tg.csv"),
              "A1 pc2, FSW v2.7 k_est_asc 2, no growth": os.path.join(TGA, "mc6_runs_tg_A1_none_k2_tg.csv"),
              "A1 ENG-07d, FSW v2.7 k_est_asc 2, no growth": os.path.join(TGA, "mc6_runs_tg_A1J_none_k2_tg.csv")}
    g["launch_commit_wind_evidence"] = wind_evidence(wcases)
    # ------------------------------------------------------------------ answers, requests, issues
    ans = g.get("answers_to_requests", {})
    rbf = mvb.get("reduced_bandwidth_fallback", {}).get("v", {})
    wn45_ = rbf.get("mech_v2|m2_J1.6_wn4.5", {})
    wn45rt_ = rbf.get("mech_v2|m2_J1.6_wn4.5_rt", {})
    ans.update({
        "lead_oi1_propellant_closure": "propellant_closure_v3 (A1 closes at 2.00 kg with 40 %; A2 needs 2.20 kg, B1 2.14 kg; option (a) "
                                       "adopted by the lead)",
        "lead_csi_target_K": "3,100 N m/rad hard minimum / 5,200 goal (adopted); recomputed on mechanical.json v2 in "
                             "mech_v2_rebaseline.stiffness_target",
        "lead_wn_x0.75_p_cost": (f"landing bandwidth x 0.75 as a gain change: P {wn45_.get('P')} on mechanical.json v2 "
                                 f"({wn45_.get('vs_m2_J1.6')}); re-tuned with the lateral loops x 0.75: P {wn45rt_.get('P')} "
                                 f"({wn45rt_.get('vs_m2_J1.6')}); the linear target with the notch does not move: degraded mode, not "
                                 "the B-TVC-1 gate fallback (actuator contingency)"),
        "lead_n_sweep": "mech_v2_rebaseline.linkage_ratio_sweep: n 4.8 confirmed",
        "lead_hose": "hose <= 20 N m/rad in the hinge budget (requirements.gimbal.hinge_moment.hose_budget), in the 6-DOF U(1.73, 17.48), "
                     "and in the CSI target as a < 1 % effect (left out, conservative); ENG-07 load sum: eng07_slew_load_check",
        "lead_relight_timing": (f"relight_planning_181: planning value {planning_v:g} s (0.6 s + Electronics' worst-case sequence "
                                "1.21 s); the 1.7 s placeholder results (flight_software.relight_sequence_placeholder) and the "
                                "2026-10-12 1.4 s cases (relight_nc_valve_closed) are kept as evidence"),
        "lead_relight_1.81s_2026-10-13": g["relight_planning_181"]["v"]["finding"],
        "lead_early_light_2026-10-13": ("relight_planning_181.mechanism and .proposals: (a) hold-to-planned-light under test by GNC "
                                        "(paired on the four bases, refutation: P not restored or reserve below 25 %); (b) with "
                                        "Electronics; status OPEN until one is chosen"),
        "lead_icd": ("icd_inputs_for_airframe (self-contained; 2026-10-13: abort and no-retry events, relight placeholder, "
                     "upper_bay_venting with the barometer condition, the sizing duty cycles)"),
        "lead_kest2_A1_paired_2026-10-13": g["flight_software"]["thrust_effectiveness_estimator_k_est_asc_2"]["v"]["evidence"]["A1_wording"],
        "lead_throat_growth_P_with_without_2026-10-13": "throat_growth.with_and_without_growth and throat_growth.flight_software_effect",
        "lead_no_light_2026-10-13": "no_light_accounting (P_total = P_6DOF (1 - p_nl); p_nl ASSUMED placeholders with no source; 3/N rule)",
        "lead_abort_2026-10-13": "flight_software.abort_shutdown (bracket with the 21.4 cm3 line; pintle-not-moving bound)",
        "lead_dc_burn_definition_2026-10-13": ("duty_cycles.burn_time_definition: the Combustion query was right (DC-B1 disp max thrust "
                                               "ends at liquid depletion, 23.58-23.59 s); the index gave the engine-on counter "
                                               "(24.09 s); index rev b publishes the thrust-on time and keeps the counter"),
        "lead_launch_commit_wind": "launch_commit_wind_evidence (proposal for the lead, not a decision)"})
    g["answers_to_requests"] = ans
    g["requests"] = [
        "REQUEST Mechanical: structure + rods >= 3,100 N m/rad per axis at every pose (goal 5,200), servo excluded; publish the per-pose "
        "structure-only values so GNC can recompute the rocking band with the measured servo",
        "REQUEST Mechanical: recompute rate_engine_dps with the mechanical.json v2 non-inertial hinge terms (sum 4.87 N m incl. the hose "
        "upper term 2.14 N m; 5.17 N m with the hose at the 20 N m/rad routing limit) instead of the v1 sum 3.19 N m; GNC's linear "
        "extrapolation gives ~100 / ~98 deg/s at 7 deg / 7.4 V (ENG-07 >= 100)",
        "REQUEST Electronics: implement the v2.6 gimbal command tracker (100 deg/s, 2000 deg/s2) in the ECU TvcShaper ahead of the low-pass "
        "and the per-axis notch; GNC owns the governor (with the ratchet) in the FC attitude loop",
        "REQUEST Electronics: publish in electronics.json the relight sequence times GNC now flies from the firmware v2.7 SIL "
        "(worst case 1.21 s valve command to Pc confirmation, SIL nominal 0.76 s, Pc confirmation 0.26 / 0.50 s after IGNITION entry "
        f"for a liquid / vapour line) with the firmware version, so the FSW planning value {planning_v:g} s cites a published "
        "interface; feasibility of (b), a deterministic ignition instant (relight_planning_181.proposals)",
        "REQUEST Electronics: implement the abort law in the ECU (every abort: NC latch de-energised at once, pintle commanded closed "
        "in parallel, torch solenoids closed; normal MECO / touchdown cuts keep the pintle-first sequence) and no in-flight relight "
        "retry; publish the sized NC valve close time (now 0.10 s ASSUMED requirement; combustion.json 0.15 s DERIVED maximum)",
        "REQUEST Electronics (if the independent review accepts k_est_asc 2): Pc and the axial accelerometer in the FC at >= 100 Hz "
        "with a common time base; the FSW mass estimate interface (integrated flow from the ECU map); GNC supplies the estimator "
        "law and gates (flight_software.thrust_effectiveness_estimator_k_est_asc_2)",
        "REQUEST Electronics / bench: B-TVC-1 scope in requirements.gimbal.tvc_actuator.B-TVC-1 (K_s gate, per-axis mode and damping, "
        "J_int split, slew and acceleration at 6.6 / 7.4 V, ENG-07b episodes, hose stiffness)",
        "REQUEST Combustion (combustion.json v2.4): remove the in-flight retry from igniter.sequence.abort_if_no_ignition and the "
        "'isolation valve may stay open between burns' from igniter.sequence.relight (lead rules); the RC-03 ignition latency "
        "distribution (replaces the 0.3 s placeholder); throat erosion data for the 7-11 % band (RC-06; onset, uniformity); head-end "
        "BC files for the dispersed duty cycles (sizing cases and growth variants)",
        "REQUEST Combustion / 05-plume-cfd: ground-plane plume case at hover and touchdown thrust (feet and legs), and the jet boundary "
        "at max thrust to replace GNC's Prandtl-Meyer keep-out estimate",
        "REQUEST Mechanical: re-measure the valve-to-pintle-seat line volume on CAD v3.4 (21.4 cm3 relayed) and estimate its vapour "
        "fraction at an abort; B-PNT-1: unpowered HV69 back-drive torque vs the closing spring and the spring-closed pintle time "
        "(abort tail-off with the servo unpowered); upper-bay vent area and station (icd_inputs_for_airframe.upper_bay_venting)",
        "REQUEST lead: B1 / A1 launch-commit wind (GNC proposal <= 6 m/s mean at 10 m, launch_commit_wind_evidence); the "
        "independent GNC review of k_est_asc 2 (with a flow-integrating mass estimate); a source for the relight no-light "
        "probability (IGN-1 / T1 / T4 attempt counts against the 3/N rule)",
        "REQUEST lead / airframe (Lauty): icd_inputs_for_airframe (fins, drogue + release + swivel at the nose, plume-line clearance, "
        "CG band and CG height above the pivot, first bending >= 10 Hz, legs to the touchdown envelope, roll-RCS provision, upper-bay "
        "venting clear of the barometer ports)"]
    oi = [x for x in g.get("open_interface_issues", []) if not any(s in x for s in (
        "combustion.json v2 not yet published", "engine v2 growth (+0.11 kg", "hinge moment: mechanical.json v1 design",
        "rocking-mode damping and servo stiffness are unpublished", "tank: the lead fixed 2.00 kg"))]
    g["open_interface_issues"] = oi + [
        "ENG-07d: mechanical.json v2 total stiffness 552.5-1681 N m/rad (ASSUMED servo) is below the GNC target; Mechanical stiffening "
        "in work; K_s, damping and the rotor split unknown until B-TVC-1",
        "ENG-07 slew table in mechanical.json v2 uses the v1 load sum (3.19 N m); the v2 terms sum to 4.87 N m",
        "combustion.json v2.3 igniter.sequence.relight allows the isolation valve open between burns; the LEAD rule (NC valve closed "
        "through the coast) governs and is what GNC flies",
        "combustion.json v2.3 igniter.sequence.abort_if_no_ignition allows one automatic in-flight retry; the LEAD rule (no in-flight "
        "retry, 2026-10-13) governs; the key goes to Combustion for v2.4 (flight_software.relight_no_retry)",
        "gnc.json v2 requirements.ignition.starts_per_flight_required ('3, one spare relight') vs the no-retry rule: v3 keeps the 3 "
        "starts as igniter capacity only (note_v3)",
        "electronics.json v1 has no relight sequence time: GNC flies the firmware v2.7 SIL times relayed by the lead (worst 1.21 s, "
        "nominal 0.76 s; not measured, not yet in electronics.json); main_valve.close_time_s 0.10 s is an ASSUMED requirement "
        "(spring not sized)",
        "electronics.json v1 does not yet carry the v2.6 tracker, the per-axis notch interface, the abort law or k_est_asc 2; the "
        "firmware work area carries the notch"]
    g["open_items"] = list(g.get("open_items", [])) + [
        "linear CSI vs 6-DOF contradiction at the published stiffness (csi_vs_6dof)",
        "A2 finless free-fall: tumble-recovery failures set its P (removed from the 2.00 kg plan)",
        "reduced-bandwidth landing mode (all landing loops x 0.75) flies at a P cost; it is not designed as a flight mode and "
        "does not close ENG-07d (mech_v2_rebaseline.reduced_bandwidth_fallback)",
        "drogue release failure (canopy fall-back near touchdown) not modelled; release to be verified in T0/T4",
        "ground-plane plume (feet, legs) not modelled",
        "k_est_asc 2 is PROVISIONAL: the Monte Carlo gives the FSW a constant mass-estimate error (ASSUMED); a flow-integrating mass "
        "estimate with Isp / flow dispersion (drifting error) is not flown: independent-review item",
        "B1 85 m propellant margin is thin under dispersion: k_est_asc 2 moves the exhaustion risk from high-thrust to low-Isp "
        "engines (research proposal: propellant-aware apex target, not flown)",
        "wind: non-propellant landing failures concentrate at >= 6 m/s with gusts; B1 floor-phase attitude loss at 7-8 m/s with "
        "either FSW form (launch_commit_wind_evidence; lead decision pending)",
        "relight no-light probability has no source: P_total uses the ASSUMED placeholder table (no_light_accounting)",
        "throat erosion: rate, onset delay and non-uniformity unknown (literature-scaled 7-11 % band)",
        "abort tail-off: line vapour fraction at the abort instant, spring-closed pintle speed with the servo unpowered, valve "
        "close time (ASSUMED / DERIVED)",
        "nominal duty cycles DC-A1 v3 and DC-B1 85 m v3 were flown with k_est_asc 0 (difference in duty_cycles.nominal_cycles_fsw)",
        "Q2 notch research proposal: linear evidence only, not flown in the 6-DOF (notch_q2_research_proposal)",
        "early relight lights (start delay below the 1.81 s planning value, down to the SIL nominal) lose P: significant on 3 of 4 "
        "A1 bases (relight_planning_181). Owners: GNC tests (a) hold-to-planned-light; Electronics answers (b) deterministic "
        "ignition instant; the lead chooses ((b) preferred if both restore P)",
        "A1 sizing cycle (engine-on counter 8.26 s) does not bound early lights (p99 8.61-8.78 s, max 9.12 s): B1 governs thermal "
        "(lead); GNC publishes the early-light A1 p99 cycle as a record once the fix is chosen (owner GNC)",
        "relight latency: no measured distribution (RC-03, owner Combustion); the 1.21 s / 0.76 s sequence times are SIL values "
        "(owner Electronics); the U(0.2, 0.6) s draw on top of the sequence is the lead's planning rule, not a latency model",
        "accelerometer over-thrust abort (FC_THRUST, 650 N / 20 ms provisional): GNC error budget, Pc-lost Monte Carlo branch and "
        "threshold (owner GNC, in work); firmware implementation (owner Electronics)"]
    g["carried_from_v2"] = ["flight_profile (descent trade, test campaign, baseline numbers; mission_plan_v3 added)",
                            "design_limit_loads (v3_check added)", "landing_closure (v2 history; landing_closure_v3 added)",
                            "verification_6dof", "csi_time_domain (v2 vehicle)", "lift_capability",
                            "answers_to_lead_relay_combustion_v2",
                            "requirements other than gimbal / structure / ignition / tank / throttle.thrust_effectiveness_estimation / "
                            "throttle.throat_growth_tolerance"]
    g["changes_from_v2"] = [
        "propellant closure on combustion.json v2.3 + mechanical.json v2 with the +25 % rule; lead decision option (a)",
        "reference-governor ratchet (att_ref_mode 1) in the flight software (A2 P 0.838 -> 0.918 on v3b, A1/B unchanged)",
        "mechanical.json v2 re-baseline (reading checks 0 failures; liftoff +0.17 kg; pivot 0.203 m)",
        "ENG-07d: frequency target re-derived on v2 mass properties, structure target 3,100 / 5,200 N m/rad adopted, notch REQUIRED "
        "per axis, B-TVC-1 gate; reduced bandwidth: a gain change alone loses landings, a x 0.75 re-tune of all landing loops "
        "recovers most of P but leaves the notch-case frequency target unchanged (actuator contingency is the gate fallback)",
        "NC-closed relight timeline (+0.80 s, planning value 1.4 s) with the ENG-04 torch numbers",
        "hose (<= 20 N m/rad) in the hinge-moment budget and the CSI target; ENG-07 load-sum inconsistency flagged",
        "duty cycles v3 (DC-A1, DC-B1 85 m) on the current interfaces; DC-B1 v2 kept as the conservative thermal envelope",
        "reference vehicle v3d and a self-contained icd_inputs_for_airframe (CG band, CG height above the pivot, plume-line clearance)",
        "CORRECTION: n 4.8 actuator-study maximum delivered hinge moment 28.5 N m (logged as 26.8 N m)",
        "run6 v2.6 fix: the relight start-delay shift (t_ign_add) also applied to the nominal / sizing flight",
        "linkage-ratio sweep n 4.8-6.0 (n 4.8 confirmed)",
        "2026-10-13: flight software v2.7 PROVISIONAL with the k_est_asc 2 thrust-effectiveness estimator on both profiles (first "
        "form k_est_asc 1 rejected, kept as evidence); sim6/run6 v2.7-dev bit-identical to v2.6 with the new options off",
        "2026-10-13: throat growth 7-11 % in the Monte Carlo with P with and without (throat_growth): FSW v2.6 loses B1 85 m with "
        "the ECU Pc loop, k_est_asc 2 restores it; A1 does not lose P",
        f"2026-10-13: relight placeholder 0.8 + 0.3 s: planning value 1.4 -> {planning_v:g} s (relight_sequence_placeholder); no pad "
        "pre-purge",
        "2026-10-13: relight planning value 1.81 s (0.6 s + Electronics' worst-case sequence 1.21 s, lead decision (2)): A1 re-run "
        "paired (relight_planning_181): planned lights show no significant difference vs the 1.7 s placeholder at 500 runs; lights "
        "EARLIER than planned (down to the SIL nominal 0.76 s) lose P, significant on 3 of 4 bases: open, fix under test",
        "2026-10-13: no in-flight relight retry; no_light_accounting with the ASSUMED p_nl table and the 3/N rule",
        "2026-10-13: abort law (NC valve de-energised at once, pintle closed in parallel) with the tail-off bracket on the 21.4 cm3 "
        "line and the pintle-not-moving bound (flight_software.abort_shutdown)",
        "2026-10-13: dispersed duty cycles are the sizing cases; duty-cycle index rev b: burn_time_s = thrust-on time (it was the "
        "engine-on counter; Combustion query); rev c: airborne / leg-contact axial maxima (the overall maximum of the failed max "
        "runs is the crash impact, not a design load); DC-B1 v2 is no longer a conservative envelope (b1_dispersed_burn)",
        "2026-10-13: verification_v27 (T10-T13, bit identity, v2.6 tests on v2.7 code, Monte Carlo forensics v1.1 with v1 kept)",
        "2026-10-13: icd_inputs_for_airframe: abort / no-retry events, relight placeholder, upper_bay_venting with the barometer "
        "condition, sizing duty cycles",
        "2026-10-13: launch_commit_wind_evidence (proposal) and notch_q2_research_proposal (linear only)",
        "WORDING (lead 2026-10-13): A1 with k_est_asc 2 vs 0 shows no significant difference at 500 runs; it is not shown that A1 "
        "is not degraded"]
    apply_1013b(g, FCT)
    first = ["id", "version", "date", "owner", "supersedes", "status", "publication_note", "lead_decisions_2026-10-13",
             "lead_decisions_2026-10-12", "units", "conventions", "inputs_read", "scripts", "changes_from_v2", "carried_from_v2"]
    g = {**{k: g[k] for k in first if k in g}, **{k: v for k, v in g.items() if k not in first}}
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, "w") as f:
        json.dump(g, f, indent=1, default=float)
    print("written", DEST, os.path.getsize(DEST))


if __name__ == "__main__":
    main()
