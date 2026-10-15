"""Assemble interfaces/gnc.json v3 from gnc.json v2 (published) + the v3 re-baseline + the TVC actuator study.

v3 = v2 with these sections replaced or added (every number read from a result file, tagged):
  * re-baseline on mechanical.json v2 and combustion.json v2.x (GNC_IFACE = iface_v3): rebaseline_v3, reference_vehicle
    (vehicle v3d: masses, gimballed subassembly, tail-wags-dog), engine_model, flight_profile.lead_baseline_numbers_v3;
  * TVC actuator study (sim6 v2.5 act_model 1, lead requests 2026-10-12): requirements.gimbal (linkage ratio, V_val,
    ARM rule, ENG-07b/c/d, B-TVC-1, hinge moments), requirements.structure (rocking mode, CSI);
  * combustion.json v2 open interface issues answered (OI-1, OI-2, OI-9, OI-10), requests and open items updated.
Sections not re-run keep their v2 content and carry basis = "gnc.json v2" (listed in carried_from_v2).
Inputs: GNC_V2_PUB, GNC_OUT (m3), GNC_RES (results_v3), GNC_RES_V2, GNC_OUT_V2, GNC_VEH_OUT, GNC_VEH_TAG, GNC_IFACE.
Output: <GNC_OUT>/../gnc_json/gnc_v3.json. Run: python scripts/m2_gnc_json_v3.py
"""
import copy
import csv
import hashlib
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

W = "/home/claude/work/space"
V2PUB = os.environ.get("GNC_V2_PUB", f"{W}/out/gnc_json/gnc_v2_published.json")
OUT = os.environ.get("GNC_OUT", f"{W}/out/m3")
RES = os.environ.get("GNC_RES", f"{W}/out/results_v3")
RES2 = os.environ.get("GNC_RES_V2", f"{W}/out/results_v2")
OUT2 = os.environ.get("GNC_OUT_V2", f"{W}/out/m2")
VEH = os.environ.get("GNC_VEH_OUT", f"{W}/out/vehicle_v3")
VTAG = os.environ.get("GNC_VEH_TAG", "v3d")
SUF = os.environ.get("GNC_SUFFIX", "v3")
IFACE = os.environ.get("GNC_IFACE", f"{W}/iface_v3")
CHK = os.environ.get("GNC_CHECKS", f"{W}/out/check_comb2")
DEST = os.environ.get("GNC_GJ3_DEST", os.path.join(os.path.dirname(OUT), "gnc_json", "gnc_v3.json"))
DATE = "2026-10-12"
BASE, LEAD, ACT = "AD_fins_f20", "AD_prov_2kg", "AD_prov_act_nmech_6V6_sagD"
LEAD3 = {   # lead decisions 2026-10-12 on the GNC actuator study (interfaces/CHANGELOG.md)
    "linkage_ratio_n": 4.8, "V_val_V": 6.6, "arm_rest_min_V": 8.1, "eng07b_max_episode_s": 0.1, "eng07c_J_int_max_kgm2": 1e-3,
    "eng07d_flex_gm_min_dB": 6.0, "design_load_Nm": 35.3,
    "source": "lead decisions 2026-10-12 on the GNC n 4.8 actuator study (interfaces/CHANGELOG.md)"}


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


def wil(c, S):
    s = S[c]["summary"]
    return f"P {s['success']:.3f} [{s['ci95'][0]:.3f}, {s['ci95'][1]:.3f}]"


def main():
    v2 = jl(V2PUB)
    S3 = jl(os.path.join(OUT, f"mc6_summary_{SUF}.json"))["cases"]
    RB = jl(os.path.join(RES, f"rebaseline_v2_{SUF}.json")) or {}
    AS3 = jl(os.path.join(RES, f"actuator_study_{SUF}.json")) or {}
    AS2 = jl(os.path.join(RES2, "actuator_study_v2.json")) or {}
    VH = jl(os.path.join(VEH, f"vehicle_{VTAG}.json")) or {}
    TWD = rcsv(os.path.join(VEH, f"twd_table_{SUF}.csv"))
    PR = {r["case"]: r for r in rcsv(os.path.join(RES, f"mc6_paired_{SUF}.csv"))}
    CSI3 = jl(os.path.join(OUT, f"csi_{SUF}.json"))
    CSI3J = jl(os.path.join(OUT, f"csi_{SUF}_J1.json"))
    CSI2 = {t: jl(os.path.join(OUT2, f"csi_{t}.json")) for t in ("v2", "v2_n48", "v2_n48_J2", "v2_n60_J2")}
    ENG = jl(os.path.join(CHK, "engine_v2map_vs_relay.json")) or {}
    BIT1 = jl(os.path.join(RES2, "bitcheck_v25_vs_v24.json")) or {}
    BIT2 = jl(os.path.join(CHK, "bitcheck_v25_vs_v24.json")) or {}
    src = R.sources()
    comb, el, mech = src["comb"], src["el"], src["mech"]
    sup, sup_src = R.supply_sources()
    sv3 = sorted(set(str(c.get("sim")).split(" (")[0] for c in S3.values()))

    g = copy.deepcopy(v2)
    g.pop("publication_note", None)
    g["version"] = "v3"
    g["date"] = DATE
    g["supersedes"] = "gnc.json v2 (2026-10-12, published to the hub 20:34Z; built on sim6 v2.4 with the v1 interface snapshot)"
    mv, cv = mech.get("version"), comb.get("version")
    b3, l3 = S3.get(BASE), S3.get(LEAD)
    g["status"] = (
        f"M2 revision. (1) Re-baseline of the 6-DOF Monte Carlo ({', '.join(sv3)}, 500 runs per case, same draws as v2) on "
        f"mechanical.json {mv} (engine-group mass properties, pivot, as-built n 4.8 TVC linkage) and combustion.json {cv} "
        f"(published throttle map; the v2 relay correction no longer applies): see rebaseline_v3. (2) TVC actuator study "
        f"(sim6 v2.5 act_model 1: SB-2292SG torque-speed lines through the exact Cardan kinematics, supply sag from "
        f"Electronics' resistive chain) and the lead decisions taken on it: n 4.8 FINAL, V_val 6.6 V, ENG-07b/c/d, B-TVC-1 "
        f"(requirements.gimbal). (3) combustion.json v2 open interface issues answered. Sections not re-run keep the v2 "
        f"content (carried_from_v2). Everything here is a prediction: no hardware has been tested.")
    # ------------------------------------------------------------------ inputs
    files = {}
    for fn in ("combustion.json", "electronics.json", "mechanical.json", "ENGINE-BASELINE-v0.json"):
        p = os.path.join(IFACE, fn)
        j = jl(p)
        files[fn] = dict(version=(j or {}).get("version"), sha256=sha(p))
    mp_ = (comb.get("operating_points") or {}).get("throttle_map_csv")
    files["throttle_map_v2.csv"] = dict(sha256=sha(os.path.join(IFACE, "throttle_map_v2.csv")), published_path=mp_)
    files["electronics_tvc_supply_budget_v1.json"] = dict(
        sha256=sha(R.SUPPLY_FILE) if os.path.exists(R.SUPPLY_FILE) else sha(os.path.join(R.SNAP, os.path.basename(R.SUPPLY_FILE))),
        source=sup_src, note="Electronics calc/tvc_supply_budget_v1 (work file, read-only for GNC): supply chains and servo currents")
    files["gnc.json_v2"] = dict(sha256=sha(V2PUB), note="published 2026-10-12; base of this file")
    files["lead_decisions_2026-10-12_actuator"] = ("n 4.8 FINAL on the as-drawn supply, V_val 6.6 V, ARM rule, ENG-07b/c/d, "
                                                  "B-TVC-1, design load 35.3 N m (interfaces/CHANGELOG.md)")
    files["lead_decisions_2026-10-12_cad_v32"] = "CAD v3.2 status: pivot 164.5 mm aft of the head mid-plane (316L aft section); n 4.80 as built"
    g["inputs_read"] = dict(v2["inputs_read"], **files)
    g["inputs_read"]["combustion.json"] = files["combustion.json"]
    g["inputs_read"]["mechanical.json"] = files["mechanical.json"]
    g["inputs_read"]["electronics.json"] = files["electronics.json"]
    for k in ("throttle_map_initial_port_v1.csv", "lead_relay_combustion_v2_20261012.json", "engine_correction_v2.json"):
        if k in g["inputs_read"]:
            g["inputs_read"][k] = dict(g["inputs_read"][k] if isinstance(g["inputs_read"][k], dict) else {"v": g["inputs_read"][k]},
                                       status="v2 only (superseded by combustion.json v2.x in v3)")
    g["scripts"] = sorted(set(v2.get("scripts", []) + [
        "01-systems-gnc/sim/scripts/m2_actuator_study.py", "01-systems-gnc/sim/scripts/m2_bitcheck_v25.py",
        "01-systems-gnc/sim/scripts/m2_engine_v2_check.py", "01-systems-gnc/sim/scripts/m2_rebaseline_compare.py",
        "01-systems-gnc/sim/scripts/m2_gnc_json_v3.py", "01-systems-gnc/sim/run_v3_rebaseline.sh"]))

    # ------------------------------------------------------------------ engine model
    pts = ENG.get("points") or []
    eng_sum = {"max_abs_mdot_change_frac": max((abs(r["dmdot_rel"]) for r in pts), default=None),
               "max_abs_Isp_change_s": max((abs(r["dIsp_s"]) for r in pts), default=None),
               "thrust_points_N": [r["F_N"] for r in pts], "ceiling_vs_P_tank": ENG.get("ceiling"),
               "map_performance_spread_across_P_tank": ((ENG.get("v2map") or {}).get("map_meta") or {}).get("performance_spread_across_P_tank"),
               "map_performance_spread_across_D_port": ((ENG.get("v2map") or {}).get("map_meta") or {}).get("performance_spread_across_D_port")}
    em = {"model": P(f"combustion.json {cv} throttle map (P_tank x D_port x thrust fraction): performance from the tank-pressure "
                     "block nearest P_sat(20 C), published thrust ceiling F_ceiling_N linear in P_tank (DERIVED extrapolation "
                     "outside the levels); S230 grain from combustion.json", f"combustion.json {cv} + DERIVED engine_v2.combustion_tables_v2map"),
          "ignition_nominal_s": P(0.29, f"combustion.json {cv} igniter.model_transients (relight 90 % at 0.28-0.29 s)",
                                  "nominal flight only; the MC draws U(0.2, 0.6) s per the brief"),
          "dynamics": P("first-order thrust lag tau 45.5 ms x U(0.7, 1.5) (valve + chamber, ENG-03 t10-90 0.10 s nominal), "
                        "slew 5 F_max/s, 1 % quantisation", "ASSUMED (unchanged from v2)",
                        "combustion v2 plant: chamber tau_c 4 ms (the valve dominates), slow fuel mode phi 0.05-0.09 / "
                        "tau_f 0.11-0.53 s: see requirements.throttle.combustion_v2_plant"),
          "change_vs_v2_relay": P(rnd(eng_sum, 4), "DERIVED m2_engine_v2_check.py (01-systems-gnc/results/checks_combustion_v2)",
                                  "the v2 relay model and the published v2 map agree to about 1 % in mass flow; v3 flies the map")}
    g["engine_model"] = em

    # ------------------------------------------------------------------ re-baseline
    rb = {"rule": RB.get("rule"), "material_changes": RB.get("material") or [],
          "cases": {c: rnd({k: v for k, v in r.items() if k not in ("engine_old", "engine_new")}, 4)
                    for c, r in (RB.get("cases") or {}).items()},
          "vehicle": rnd(RB.get("vehicle"), 4), "tail_wags_dog": rnd(RB.get("twd"), 4),
          "tag": f"SIM m2_mc6 {SUF} vs v2 (same 500 draws, seed 101) + DERIVED m2_rebaseline_compare.py",
          "table_csv": f"01-systems-gnc/results/rebaseline_v2_{SUF}.csv"}
    g["rebaseline_v3"] = rb

    # ------------------------------------------------------------------ reference vehicle (v3d)
    rv = g["reference_vehicle"]
    rv["name"] = (f"RV-1c (ledger {VTAG}): RV-1b + mechanical.json {mv} engine module + uniform 146 mm body (real airframe owner: "
                  "Lauty)")
    rv["mass_ledger_csv"] = f"01-systems-gnc/vehicle/mass_ledger_{VTAG}.csv"
    sm = VH.get("sums") or {}
    if sm:
        rv["dry_mass_kg"] = P(rnd(sm["dry_kg"]), f"DERIVED mass ledger {VTAG} (mechanical.json {mv} gimballed engine; ASSUMED fixed "
                              "propulsion items, airframe, legs, avionics, recovery)",
                              f"range {sm['dry_min_kg']:.2f}-{sm['dry_max_kg']:.2f} kg; propulsion {sm['propulsion_kg']:.2f} kg, "
                              f"airframe {sm['airframe_kg']:.2f} kg, gimballed dry {sm['gimballed_dry_kg']:.3f} kg")
        rv["fuel_grain_mass_kg"] = P(rnd(VH.get("grain_kg_in_tables"), 4), f"combustion.json {cv} gas_path.grain.mass_kg")
    if VH:
        rv["liftoff_mass_kg"] = P(rnd(VH["m_liftoff_kg"]), f"SIM nominal A-D flight (ledger {VTAG} + load, roll RCS fitted)",
                                  (f"lead baseline (RCS provision only, 2.00 kg): {l3['m_liftoff_kg']:.3f} kg" if l3 else None))
        rv["landing_mass_kg"] = P(rnd(VH["m_land_nominal_kg"]), "SIM nominal A-D flight")
        rv["mass_properties_vs_time"] = {"events": [{k: rnd(v, 4) for k, v in e.items()} for e in VH.get("events", [])],
                                         "vs_propellant_state_csv": f"01-systems-gnc/vehicle/massprops_vs_propellant_{VTAG}.csv",
                                         "tag": f"SIM {sv3[-1]} nominal A-D flight + DERIVED vehicle.massprops"}
    tw = {f"{r['state']}|{r['F_label']}": r for r in TWD}
    if TWD:
        rv["gimballed_subassembly"] = P({
            "pivot": f"engine-group mid-burn CG (mechanical.json {mv})", "z_pivot_m": VH.get("z_pivot_m"),
            "touchdown_state": {k: rnd(float(tw["touchdown|20.0 %"][k]), 5) for k in ("m_e_kg", "z_e_m", "l_e_m", "I_e_own_kgm2",
                                                                                      "J_twd_kgm2", "l_p_m", "I_transverse_kgm2")},
            "tail_wags_dog_zero_rad_s": {k: rnd(float(r["w_twd_rad_s"]), 2) for k, r in tw.items()
                                         if r["F_label"] in ("12.5 %", "20.0 %", "hover (T=W)", "100.0 %")},
            "control_moment_per_deg_Nm": {k: rnd(float(r["Mc_per_deg_Nm"]), 3) for k, r in tw.items()
                                          if r["F_label"] in ("12.5 %", "20.0 %", "hover (T=W)", "100.0 %")},
            "table_csv": f"01-systems-gnc/vehicle/twd_table_{SUF}.csv"},
            f"DERIVED vehicle.massprops + mechanical.json {mv} (gimballed mass/inertia) + combustion.json {cv} grain",
            "l_p = z_cg - z_pivot; l_e = z_pivot - z_e; J_twd = I_e + m_e l_e (l_e + l_p); w_twd = sqrt(F l_p / J_twd)")
    rv["basis"] = (f"masses, mass properties and tail-wags-dog: vehicle {VTAG} (mechanical.json {mv}); aero, legs, fins and nose: "
                   "unchanged from v2")
    g["reference_vehicle"] = rv

    # ------------------------------------------------------------------ flight profile numbers on v3
    fp = g["flight_profile"]
    if l3:
        nm = l3["nominal"]
        fp["lead_baseline_numbers_v3"] = P(rnd({"apogee_m": nm.get("h_max"), "relight_height_m": nm.get("h_ign"),
                                                "relight_speed_mps": nm.get("v_ign"), "total_burn_s": nm.get("burn_time"),
                                                "propellant_used_kg": nm.get("prop_used"), "landing_mass_kg": nm.get("m_land"),
                                                "m_liftoff_kg": l3.get("m_liftoff_kg"), "MC_P": wil(LEAD, S3)}, 3),
                                           f"SIM {str(l3.get('sim')).split(' (')[0]} {LEAD} on the v3 interface set (mechanical.json {mv}, "
                                           f"combustion.json {cv}): roll RCS not fitted, N2O fixed 2.00 kg")
    fp["basis"] = "descent-attitude trade, costs and risks, test campaign and baseline_numbers: gnc.json v2 (sim6 v2.4, v2 vehicle)"

    # ------------------------------------------------------------------ requirements: gimbal / TVC actuator
    rq = g["requirements"]
    gm = rq["gimbal"]
    cases2 = AS2.get("cases") or {}
    cases3 = AS3.get("cases") or {}

    def ac(c, d=None):
        d = d if d is not None else cases2
        return d.get(c)
    gov = ac("AD_prov_act_n48_6V6_sagD")
    gov3 = ac(ACT, cases3)
    br = []
    for c, r in sorted(cases2.items(), key=lambda kv: kv[1]["J_int_servo_kgm2"]):
        if r["n"] == 4.8 and r["supply_chain"] == "v2.2_as_drawn/typ/15" and r["servo_V"] == 6.6 and r.get("supply_Vrest") is None:
            pr = r["paired"].get(LEAD, {})
            br.append(dict(J_int_kgm2=r["J_int_servo_kgm2"], P=r["P"], ci95=rnd(r["ci95"], 3),
                           lost_vs_lead_baseline=pr.get("lost"), gained=pr.get("gained"), mcnemar_p=rnd(pr.get("mcnemar_exact_p"), 4),
                           loses=pr.get("loses"), longest_episode_p99_s=rnd(r["saturation"]["longest_episode_s"]["p99"], 3),
                           longest_episode_max_s=rnd(r["saturation"]["longest_episode_s"]["max"], 3),
                           eng07b_pass=bool(r["saturation"]["longest_episode_s"]["p99"] <= LEAD3["eng07b_max_episode_s"])))
    j_ok = [b["J_int_kgm2"] for b in br if b["eng07b_pass"]]
    j_bad = [b["J_int_kgm2"] for b in br if not b["eng07b_pass"]]
    p_ok = [b["J_int_kgm2"] for b in br if not b["loses"]]
    p_bad = [b["J_int_kgm2"] for b in br if b["loses"]]

    def vs(c, comp):
        r = cases2.get(c) or cases3.get(c)
        if not r or comp not in r["paired"]:
            return None
        q = r["paired"][comp]
        return f"P {r['P']:.3f}; {q['lost']} lost / {q['gained']} gained vs {comp}, McNemar p = {q['mcnemar_exact_p']:.2g}"
    tvc = {}
    tvc["linkage_ratio_n"] = P(LEAD3["linkage_ratio_n"], "REQ lead decision 2026-10-12 (FINAL), from SIM m2_actuator_study v2",
                               f"mechanical.json {mv}: gear_ratio_n {((mech.get('tvc_actuation') or {}).get('gear_ratio_n') or {}).get('v')}; "
                               f"n 4.8 at the governing 6.6 V: {vs('AD_prov_act_n48_6V6_sagD', LEAD)}; n 6 twin on the same supply: "
                               f"{vs('AD_prov_act_n60_6V6_sagD', LEAD)}")
    tvc["validated_plug_voltage_V_val_V"] = P(LEAD3["V_val_V"], "REQ lead decision 2026-10-12, from SIM (both-stall plug voltage)",
                                              "lowest plug voltage validated with both servos stalled; 6.0 V probes (fixed and sag) "
                                              f"also keep P: {vs('AD_prov_act_n48_6V0_sagD', LEAD)}, but fixed 6.0 V fails ENG-07b "
                                              f"(longest episode p99 {cases2.get('AD_prov_act_n48_6V0', {}).get('saturation', {}).get('longest_episode_s', {}).get('p99', float('nan')):.3f} s)")
    tvc["arm_rule"] = P(f"predicted both-stall plug voltage >= {LEAD3['V_val_V']} V AND rest voltage >= {LEAD3['arm_rest_min_V']} V",
                        "REQ lead decision 2026-10-12 (ECU pad ARM permit; abort cause TVC_SUPPLY)", "no low-IR pack required")
    tvc["servo_model"] = P({"servo": "2 x Savox SB-2292SG (electronics.json)", "torque_speed_lines": "DATASHEET 6.0/7.4/8.4 V, linear in V",
                            "kinematics": "exact Cardan, lever azimuths/radius/ball height and horn radius from mechanical.json",
                            "braking": "full stall torque", "supply": "Electronics tvc_supply_budget_v1 chain v2.2 as drawn, typ, 15 mOhm pack",
                            "current": "I = 0.22 A + (I_stall(V) - 0.22) |T| / Ts, I_stall 7.5 A @ 6.0 V, 9.2 A @ 7.4 V (DATASHEET)"},
                           "SIM sim6 v2.5 act_model 1 (hypotheses in 01-systems-gnc/sim/README.md)")
    if gov:
        sat = gov["saturation"]
        tvc["saturation_at_governing_supply"] = P(rnd({
            "frac_runs_saturated": sat["frac_runs_saturated"], "phase": "landing burn only; none after touchdown",
            "total_time_per_run_s_p99_max": [sat["sat_time_s_all_runs"]["p99"], sat["sat_time_s_all_runs"]["max"]],
            "longest_episode_s_p99_max": [sat["longest_episode_s"]["p99"], sat["longest_episode_s"]["max"]],
            "episodes_per_run_p99": sat["episodes_per_run"]["p99"],
            "stall_torque_limited_frac_runs": (sat.get("torque_limited") or {}).get("frac_runs"),
            "stall_torque_limited_max_s": ((sat.get("torque_limited") or {}).get("time_s") or {}).get("max"),
            "plug_voltage_min_V": (sat.get("plug_voltage_min_V") or {}).get("min"),
            "servo_current_max_A": (sat.get("servo_current_max_A") or {}).get("max")}, 3),
            "SIM m2_actuator_study v2 (AD_prov_act_n48_6V6_sagD, 500 runs)", "speed, not holding torque, is the binding limit")
    tvc["ENG-07b_max_saturation_episode_s"] = P(LEAD3["eng07b_max_episode_s"], "REQ lead decision 2026-10-12 (GNC proposal)",
                                                "no actuator saturation episode longer than 0.1 s in the landing burn; verified as the "
                                                "p99 over the 500-run MC of each run's longest episode")
    tvc["ENG-07c_J_int_max_kgm2"] = P(LEAD3["eng07c_J_int_max_kgm2"], "REQ lead decision 2026-10-12 (provisional) + SIM bracket",
                                      f"servo rotor inertia referred to the servo output. Bracket at n 4.8 / 6.6 V (as-drawn chain): "
                                      f"ENG-07b passes up to {max(j_ok) if j_ok else 'n/a'} kg m2 and fails from {min(j_bad) if j_bad else 'n/a'}; "
                                      f"P(landing) holds up to {max(p_ok) if p_ok else 'n/a'} and loses from {min(p_bad) if p_bad else 'n/a'} kg m2. "
                                      "The value is set by ENG-07b. SB-2292SG value unknown (Electronics to estimate; B-TVC-1 measures). "
                                      "Model caveat: J_int n^2 is added on the engine side of the servo-stiffness spring; if the servo's "
                                      "quoted response already contains its rotor, this double-counts (conservative).",
                                      bracket=br)
    csi_n48 = (CSI2.get("v2_n48") or {}).get("summary", {}).get("lpf", {})
    csi_v2 = (CSI2.get("v2") or {}).get("summary", {}).get("lpf", {})
    csi_v3 = (CSI3 or {}).get("summary", {}).get("lpf", {})
    csi_v3j = (CSI3J or {}).get("summary", {}).get("lpf", {})
    tvc["ENG-07d_flex_gain_margin_min_dB"] = P(LEAD3["eng07d_flex_gm_min_dB"], "REQ lead decision 2026-10-12 (GNC proposal)",
                                               "flex (rocking-mode) gain margin with the ECU command shaping; otherwise an ECU notch at "
                                               "the measured rocking mode", evidence=rnd({
                                                   "v2_n6": {k: csi_v2.get(k) for k in ("n_cases", "n_unstable", "flex_gm_up_min_dB")},
                                                   "v2_n4.8_scaled_stiffness": {k: csi_n48.get(k) for k in ("n_cases", "n_unstable", "flex_gm_up_min_dB", "flex_unstable")},
                                                   f"{SUF}_mechanical_{mv}": {k: csi_v3.get(k) for k in ("n_cases", "n_unstable", "flex_gm_up_min_dB", "flex_unstable")} if csi_v3 else "not run",
                                                   f"{SUF}_mechanical_{mv}_J_int_1e-3": {k: csi_v3j.get(k) for k in ("n_cases", "n_unstable", "flex_gm_up_min_dB", "flex_unstable")} if csi_v3j else "not run",
                                                   "rocking_Hz_v3": (CSI3 or {}).get("rocking_landing", {}).get("f_rock_Hz"),
                                                   "stiffness_source_v3": (CSI3 or {}).get("rocking_landing", {}).get("source")}, 2))
    tvc["B-TVC-1"] = P("loaded servo pair through the n 4.8 linkage on an engine-inertia dummy (about pivot = the published wet "
                       "engine inertia) at 6.6 V plug: step and sine sweep; measure J_int, axis stiffness, rocking frequency and damping, "
                       "saturation behaviour", "REQ lead decision 2026-10-12 (close-out test for ENG-07b/c/d)")
    gm["tvc_actuator"] = tvc
    hm = gm.get("hinge_moment", {})
    gm["hinge_moment"] = P({"design_load_engine_moment_Nm": LEAD3["design_load_Nm"],
                            "n48_6V6_delivered_p99_Nm": rnd(gov["saturation"]["delivered_hinge_moment_Nm"]["p99"], 2) if gov else None,
                            "n48_6V6_delivered_max_Nm": rnd(gov["saturation"]["delivered_hinge_moment_Nm"]["max"], 2) if gov else None,
                            "n48_all_cases_delivered_max_Nm": rnd(max((r["saturation"]["delivered_hinge_moment_Nm"]["max"] for r in cases2.values()
                                                                       if r["n"] == 4.8 and r["J_int_servo_kgm2"] <= 4e-3), default=None), 2),
                            f"{SUF}_as_built_delivered_p99_max_Nm": (rnd([gov3["saturation"]["delivered_hinge_moment_Nm"]["p99"],
                                                                          gov3["saturation"]["delivered_hinge_moment_Nm"]["max"]], 2) if gov3 else None),
                            "v2_reference_servo_flight_p99_max_Nm": [hm.get("v", {}).get("flight_p99_Nm"), hm.get("v", {}).get("flight_max_Nm")]},
                           "REQ lead decision 2026-10-12 (design load) + SIM m2_actuator_study (delivered per-axis linkage moment)",
                           "the 35.3 N m design load (both servos at 8.4 V stall, n 4.8) covers every simulated n 4.8 case with J_int <= 4e-3; "
                           "n 6 with J_int >= 2e-3 reached 45 N m (not the baseline)")
    gm["rate_min_dps"]["note"] = (gm["rate_min_dps"].get("note", "") + " v3: n 4.8 gives 120.6 deg/s worst case at 7.6 V and 97 deg/s at "
                                  "6.6 V no-load at the 7 deg extreme (lead/Electronics slew check); the 6.6 V MC keeps P (see tvc_actuator).")
    rq["gimbal"] = gm
    st = rq["structure"]
    f3 = (CSI3 or {}).get("rocking_landing", {})
    st["gimballed_engine_first_mode_min_Hz"]["note"] = (
        f"v3: rocking mode with mechanical.json {mv} stiffness {rnd(f3.get('f_rock_Hz'), 1)} Hz ({f3.get('source')}); "
        "with J_int at the ENG-07c limit the low end drops further. ENG-07d (flex gain margin >= 6 dB or ECU notch) is the governing "
        "criterion; the 25 Hz figure is kept as a design target") if f3 else st["gimballed_engine_first_mode_min_Hz"].get("note")
    st["csi_margins_with_filter"] = P({"v2_n6": rnd(csi_v2, 2), "v3": rnd(csi_v3, 2) if csi_v3 else "not run",
                                       "v3_J_int_1e-3": rnd(csi_v3j, 2) if csi_v3j else "not run"},
                                      "SIM m2_csi (python-control, Pade-3 delay)", "see requirements.gimbal.tvc_actuator.ENG-07d")
    rq["structure"] = st
    # throttle: combustion v2 plant
    pl = S3.get("AD_prov_plant2")
    if pl:
        pr = PR.get("AD_prov_plant2") or {}
        rq["throttle"]["combustion_v2_plant"] = P(
            {"slow_fuel_mode_phi_max": 0.09, "tau_f_max_s": 0.53, "MC": wil("AD_prov_plant2", S3),
             "paired_vs_baseline": ({k: pr.get(k) for k in ("base_ok_case_fail", "base_fail_case_ok", "mcnemar_exact_p")} if pr else None)},
            f"SIM m2_mc6 {SUF} AD_prov_plant2 (combustion.json {cv} plant fit, upper corner held for the whole flight)",
            f"compare {LEAD} on the same draws: {wil(LEAD, S3)}; the outer loop (Pc closed loop, ENG-03) rejects the slow mode; "
            "the inner Pc loop must handle the K_h x2.7 gain change from 100 % to 12.5 % (gain schedule in the ECU)")
    ig = rq.get("ignition", {}).get("relight_conditions")
    if isinstance(ig, dict) and isinstance(ig.get("v"), str):
        ig["v"] = ig["v"].replace("chamber purged", "chamber vented (Pc within 0.1 bar of ambient, ECU precondition before the "
                                  "torch fires; no purge gas in flight)")
        ig["note"] = ((ig.get("note") or "") + " v3: 'purged' read as 'vented' (combustion.json OI-12; N2 purge is a ground procedure)").strip()
    g["requirements"] = rq

    # ------------------------------------------------------------------ lead decisions
    ld = g.get("lead_decisions_2026-10-12", {})
    ld["gimbal_parts_design_load"] = P(LEAD3["design_load_Nm"], "REQ lead decision 2026-10-12 (replaces 26.5 N m)",
                                       "engine moment with both servos at 8.4 V stall, n 4.8; rods 441 N centre / 552 N at 7 deg / 609 N "
                                       "servo runaway into the 8 deg stop (lead/Electronics)")
    ld["tvc_actuator"] = P({k: v for k, v in LEAD3.items() if k != "source"}, "REQ lead decisions 2026-10-12", LEAD3["source"])
    g["lead_decisions_2026-10-12"] = ld

    # ------------------------------------------------------------------ answers to combustion.json v2 open interface issues
    ans = g.get("answers_to_requests", {})

    def cs(c):
        return wil(c, S3) if c in S3 and S3[c].get("closes", True) else f"{c}: not run"
    ans["combustion_OI-1_tank_A2_B1"] = (
        f"The 3.17 L / 2.00 kg tank flies the A-D baseline ({cs(LEAD)}) and the 50 m hop ({cs('B_prov_2kg_h50')}). "
        f"A2 (A-F free fall) on 2.00 kg: {cs('AF_prov_2kg')}; B1 (100 m hop) on 2.00 kg: {cs('B_prov_2kg_h100')}. "
        "A2 and B1 stay envelope cycles for engine loads; they are not flight profiles on this tank (lead keeps 2.00 kg).")
    ans["combustion_OI-2_plant"] = (
        f"v3 flies the published v2 map (mass flows within about 1 % of the v2 relay; Isp within 2 s) and the v2 ignition time "
        f"(0.29 s nominal, MC U(0.2, 0.6) s). Slow fuel mode at the upper corner (phi 0.09, tau_f 0.53 s) for the whole flight: "
        f"{cs('AD_prov_plant2')} vs {cs(LEAD)} on the same draws. The ECU Pc loop handles the K_h change (gain schedule).")
    ans["combustion_OI-9_roll_limit"] = (
        "The lead's 0.02 N m rule applies (the v1 0.007 N m figure came from the 1-D/analytic M1 and is superseded): without "
        "roll RCS the 6-DOF keeps P to 0.02-0.03 N m and loses at 0.04 N m (gnc.json v2 lead_decisions roll sweep).")
    ans["combustion_OI-10_B1_web"] = (
        "B1 (100 m hop, 19.0 s burn in DC-B1 v2) is not flown on the 2.00 kg tank; the flown hop is 50 m (14.4 s in DC-B2 v2). "
        "Keep the 19 s burn limit for B1 as an engine qualification case.")
    ans["combustion_OI-12_vented"] = ("Accepted: relight precondition reads 'chamber vented, Pc within 0.1 bar of ambient' "
                                      "(requirements.ignition.relight_conditions); purge is a ground procedure.")
    ans["combustion_OI-13_deadband_resolution"] = ("GNC requirement values are the simulated ones: deadband <= 0.5 % F_max, command "
                                                   "resolution <= 2 % F_max (2 % flown: no loss), Pc closed loop; the Pc noise and "
                                                   "pintle backlash allocation is Electronics + Mechanical.")
    g["answers_to_requests"] = ans

    # ------------------------------------------------------------------ requests, issues, open items
    g["requests"] = [
        f"REQUEST electronics: (1) SB-2292SG output-side rotor inertia J_int with its basis (ENG-07c <= {LEAD3['eng07c_J_int_max_kgm2']} kg m2 "
        "provisional); whether the quoted speed/bandwidth includes the rotor; (2) ECU notch provision at the rocking mode (ENG-07d) "
        "and the command shaping (100 deg/s + 50 rad/s 2nd-order low-pass); (3) servo stall-current thermal limit (A, s); "
        "(4) ARM permit: predicted both-stall plug voltage >= 6.6 V and rest >= 8.1 V; (5) B-TVC-1 rig and data.",
        "REQUEST mechanical: (1) axis stiffness with linkage/frame compliance from FEA (replaces the ASSUMED servo-stiffness range) "
        "and the rocking-mode damping; (2) parts to the 35.3 N m design load and the 441-609 N rod cases; (3) fixed-module masses "
        "(thrust frame, servos + horns, NC valve, feed) - GNC ledger still ASSUMES them; (4) engine-inertia dummy for B-TVC-1.",
        "REQUEST combustion: (1) residual roll torque vs throttle in the static fires to +/-0.005 N m (RCS provision rule 0.02 N m); "
        "(2) ignition-latency distribution (MC U(0.2, 0.6) s); (3) duty cycles: GNC v2 cycles remain valid within the v3 re-baseline "
        "change (rebaseline_v3); re-run only the A1 cycle if the lead asks.",
        "REQUEST lead/airframe (Lauty): ICD values below (body 146 mm, CG range, landing-mass window, legs, drogue, fins, first bending "
        ">= 10 Hz); engine-bay zone length from mechanical.json v2.",
    ]
    oi = [x for x in g.get("open_interface_issues", []) if not any(s in x for s in (
        "combustion.json v2 not yet published", "engine v2 growth (+0.11 kg", "hinge moment: mechanical.json v1 design"))]
    oi.append(f"J_int of the SB-2292SG unknown: ENG-07c {LEAD3['eng07c_J_int_max_kgm2']} kg m2 is provisional (B-TVC-1)")
    oi.append("axis stiffness and rocking damping still ASSUMED ranges until Mechanical's FEA and B-TVC-1 (CSI ENG-07d)")
    g["open_interface_issues"] = oi
    g["open_items"] = list(g.get("open_items", [])) + [
        "Actuator model hypotheses (sim6 v2.5): rotor inertia lumped on the engine axis, no servo thermal model, current linear in |T|",
        "Duty cycles, design limit loads, CSI time domain, verification and the descent trade are v2 results (v2 vehicle)"]
    g["carried_from_v2"] = ["flight_profile (except lead_baseline_numbers_v3)", "design_limit_loads (hinge: see requirements.gimbal)",
                            "duty_cycles", "landing_closure", "verification_6dof", "csi_time_domain", "icd_inputs_for_airframe",
                            "lift_capability", "answers_to_lead_relay_combustion_v2", "requirements other than gimbal/structure/throttle additions"]
    g["verification_v25"] = P({"bit_identity_act_model_0": BIT1.get("bit_identical"),
                               "bit_identity_after_combustion_v2_reader": BIT2.get("bit_identical"),
                               "runs_checked": {c: (BIT2.get("cases") or {}).get(c, {}).get("runs_checked") for c in (BASE, LEAD)}},
                              "SIM m2_bitcheck_v25 (stored v2.4 runs re-flown, every result field compared for equality)")
    g["changes_from_v2"] = [
        f"re-baseline on mechanical.json {mv} + combustion.json {cv}: " + ("; ".join(RB.get("material") or []) or "no material change "
                                                                           "(P, liftoff mass, TWD within the thresholds of rebaseline_v3.rule)"),
        "TVC: n 4.8 final, V_val 6.6 V, ARM rule, ENG-07b/c/d, B-TVC-1, design load 35.3 N m (requirements.gimbal.tvc_actuator)",
        "engine: combustion.json v2.x map replaces the v1 map x relay; ignition 0.29 s nominal",
        "vehicle: ledger v3d (mechanical.json v2 engine module; relayed +0.11 kg growth removed); v3c liftoff TWD row used the v1 grain "
        "(0.351 kg) instead of the flown 0.404 kg: 22.43 -> 21.87 rad/s at 12.5 % (liftoff only), fixed",
        "combustion.json v2 open interface issues OI-1/2/9/10 answered"]
    with open(DEST, "w") as f:
        json.dump(g, f, indent=1, default=float)
    print("written", DEST, os.path.getsize(DEST))


if __name__ == "__main__":
    main()
