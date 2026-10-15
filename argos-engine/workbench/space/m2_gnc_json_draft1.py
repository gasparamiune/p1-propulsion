"""Assemble interfaces/gnc.json v2 (M2) from the 6-DOF results.

Reads (GNC_OUT, GNC_RES, GNC_DC_OUT, GNC_VEH_OUT; see README): mc6_summary_v2.json, results_v2/*.json|csv,
verify6_v2.json, csi_v2.json, csi_timedomain_v2.json, duty_cycles_index_v2.json, vehicle_v3c.json, twd_table_v2.csv,
trade_descent_v2.json, imu_sweep_v2.json, mc6_failure_forensics_v2.json, the interface files (versions + sha256)
and gnc.json v1 (kept items: 1-D throttle/ignition sweeps, lift capability).
Writes GNC_OUT/../gnc_json/gnc_v2.json. Every number carries a tag and a rationale.
"""
import csv
import hashlib
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6, vehicle as veh  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
DCO = os.environ.get("GNC_DC_OUT", "/home/claude/work/space/out/duty_cycles_v2")
VEH = os.environ.get("GNC_VEH_OUT", "/home/claude/work/space/out/vehicle")
IFACE = os.environ.get("GNC_IFACE", "/home/claude/work/shared-fallback/engine/interfaces")
V1 = os.environ.get("GNC_V1", "/home/claude/work/space/out/gnc_json/gnc_v1.json")
DEST = os.path.join(os.path.dirname(OUT), "gnc_json", "gnc_v2.json")
DATE = "2026-10-12"
BASE = "AD_fins_f20"
MC = "SIM m2_mc6 v2 (sim6 v2.2, 500 dispersed runs, brief C.7 dispersions)"


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
        if not np.isfinite(x):
            return None
        return float(round(float(x), n))
    return x


def jload(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return None


def rcsv(path):
    try:
        with open(path) as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def sha(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return None


def main():
    S = jload(os.path.join(OUT, "mc6_summary_v2.json"))
    T = {r["case"]: r for r in jload(os.path.join(RES, "mc6_cases_summary_v2.json"))["cases"]}
    PR = {r["case"]: r for r in rcsv(os.path.join(RES, "mc6_paired_v2.csv"))}
    VF = jload(os.path.join(OUT, "verify6_v2.json"))
    CSI = jload(os.path.join(OUT, "csi_v2.json"))
    CTD = jload(os.path.join(OUT, "csi_timedomain_v2.json"))
    DCI = jload(os.path.join(DCO, "duty_cycles_index_v2.json"))
    VH = jload(os.path.join(VEH, "vehicle_v3c.json"))
    TWD = rcsv(os.path.join(VEH, "twd_table_v2.csv"))
    TR = jload(os.path.join(RES, "trade_descent_v2.json"))
    IMU = jload(os.path.join(RES, "imu_sweep_v2.json"))
    FX = jload(os.path.join(RES, "mc6_failure_forensics_v2.json"))
    DRV = rcsv(os.path.join(RES, "mc6_failure_drivers_v2.csv"))
    g1 = jload(V1)
    src = R.sources()
    comb, el, mech = src["comb"], src["el"], src["mech"]
    cs = S["cases"]
    b = cs[BASE]
    bs = b["summary"]
    bt = T[BASE]

    def Pc(c):
        t = T[c]
        return f"P {t['success']:.3f} [{t['ci95_lo']:.3f}, {t['ci95_hi']:.3f}]"

    def mcn(c):
        p = PR.get(c)
        if not p:
            return ""
        return (f"; paired vs baseline: {int(p['base_ok_case_fail'])} runs lost / {int(p['base_fail_case_ok'])} gained, "
                f"McNemar p = {float(p['mcnemar_exact_p']):.2g}")
    g = {}
    g["id"] = "gnc"
    g["version"] = "v2"
    g["date"] = DATE
    g["owner"] = "Space/GNC (01-systems-gnc)"
    g["supersedes"] = "gnc.json v1 (2026-10-11; 1-D + analytic first pass)"
    g["status"] = ("M2. 6-DOF Monte Carlo (sim6 v2.2, 500 runs per case, 27 cases) on reference vehicle RV-1c, which "
                   "uses the mechanical.json v1 engine module (CG pivot, 146 mm body for the 140 mm engine-bay ID of the "
                   "provisional lead decision), the combustion.json v1 throttle map and ignition timing, and the "
                   "electronics.json v1 servo/latency data. Requirements below supersede v1 where restated; the 1-D "
                   "v1 sweeps are kept where the 6-DOF does not replace them. Everything here is a prediction: no "
                   "hardware has been tested. Written to the lead's fallback hub during the /mnt outage.")
    g["units"] = "SI (m, kg, s, N, Pa, K, rad) unless the key names another unit (_deg, _dps, _Hz, _g, _L, _cal)"
    g["conventions"] = {
        "body_frame": "z_b along the vehicle axis toward the nose; x_b, y_b = gimbal axes (pitch/yaw)",
        "stations": "z [m] from the airframe aft datum (base plane), +z toward the nose (RV-1c: pivot at 0.2223 m = "
                    "mechanical.json frames.rv1_station_of_pivot_m)",
        "world_frame_6dof": "ENU, flat Earth, ISA density (site density dispersed 1.10-1.25 kg/m3)",
        "throttle_frac": "F / 500 N (F_max)",
        "gimbal_angle": "engine axis relative to the body axis; the LIMIT applies to the vector norm sqrt(dx^2+dy^2)",
        "success_criteria": f"touchdown |vz| <= {R.CRIT['vz']} m/s, v_h <= {R.CRIT['vh']} m/s, tilt <= {R.CRIT['tilt']} deg, "
                            f"tilt rate <= {R.CRIT['rate']} deg/s, no propellant exhaustion, no tip-over (REQ brief)",
        "statistics": "success P with Wilson 95 % interval; p99 = 99th percentile over landed runs; paired McNemar exact "
                      "test against the baseline where the dispersion draws are identical (same seed and sequence)",
    }
    files = {}
    for fn in ("combustion.json", "electronics.json", "mechanical.json", "ENGINE-BASELINE-v0.json"):
        p = os.path.join(IFACE, fn)
        j = jload(p)
        files[fn] = dict(version=(j or {}).get("version"), sha256=sha(p))
    snap = jload(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "iface_snapshot",
                              "manifest.json")) or {}
    files["throttle_map_initial_port_v1.csv"] = dict(sha256=(snap.get("throttle_map_initial_port_v1.csv") or {}).get("sha256"),
                                                     source="02-combustion/data (via the Mechanical mirror during the outage)")
    files["REQUIREMENTS.md"] = "rev 1 (ENG-01..16)"
    files["lead_decision_2026-10-12"] = "gimbal pivot at the engine CG, engine-bay ID >= 140 mm (provisional, founder confirmation pending)"
    g["inputs_read"] = files
    g["scripts"] = ["01-systems-gnc/sim/gncsim/*.py", "01-systems-gnc/sim/scripts/m2_mc6.py", "01-systems-gnc/sim/scripts/m2_verify6.py",
                    "01-systems-gnc/sim/scripts/m2_csi.py", "01-systems-gnc/sim/scripts/m2_csi_timedomain.py",
                    "01-systems-gnc/sim/scripts/m2_duty_cycles.py", "01-systems-gnc/sim/scripts/m2_vehicle.py",
                    "01-systems-gnc/sim/scripts/m2_trade.py", "01-systems-gnc/sim/scripts/m2_imu_sweep.py",
                    "01-systems-gnc/sim/scripts/m2_failure_forensics.py", "01-systems-gnc/sim/scripts/m2_analysis.py",
                    "01-systems-gnc/sim/scripts/m2_gnc_json.py"]

    # ------------------------------------------------------------------ reference vehicle
    ev = {e["event"]: e for e in VH["events"]}
    a = VH["aero"]
    twd_rows = [r for r in TWD if r["state"] == "touchdown"]

    def twd(state, label):
        for r in TWD:
            if r["state"] == state and r["F_label"] == label:
                return r
        return None
    tw125, tw20, twh = twd("touchdown", "12.5 %"), twd("touchdown", "20.0 %"), twd("touchdown", "hover (T=W)")
    twl = twd("liftoff", "100.0 %")
    rv = {}
    rv["name"] = ("RV-1c (GNC reference vehicle v3c, parametric; real airframe owner: Lauty). RV-1b + mechanical.json v1 "
                  "engine module + uniform 146 mm body")
    rv["length_overall_m"] = P(2.03, "ASSUMED REQUIREMENTS ref. vehicle ~2.0 m + 0.03 m nozzle protrusion")
    rv["body_diameter_m"] = P(rnd(VH["d_body_m"]), "DERIVED engine-bay ID 0.140 m (mechanical.json v1 required_engine_bay_ID_m, "
                              "lead decision 2026-10-12 provisional) + 2 x 3 mm PETG wall ASSUMED",
                              "uniform body assumed; a stepped 146/126 mm airframe is Lauty's option (mass and aero change)")
    rv["nose"] = P("tangent ogive, L 0.30 m", "ASSUMED")
    rv["fins"] = P("4 aft fins, span 0.12 m, root/tip chord 0.20/0.10 m, 3 mm GF/PETG, 0.30 kg", "DERIVED descent/coast trade (REPORT B)",
                   "fins stabilise the nose-first coast and are DE-stabilising tail-first (they lead in the engine-first "
                   "descent): the drogue sets the descent attitude; finless flight closes too (see landing_closure)")
    rv["landing_legs"] = P({"n": 4, "foot_radius_m": 0.40, "stroke_m": 0.10, "k_per_leg_N_m": 2500.0, "c_per_leg_N_s_m": 120.0,
                            "deploy": "at relight command (A) / fixed (B)"}, "ASSUMED (Lauty to design; MC disperses k, c x U(0.8, 1.2), mu U(0.3, 0.7))")
    rv["mass_ledger_csv"] = "01-systems-gnc/vehicle/mass_ledger_v3c.csv"
    sm = VH["sums"]
    rv["dry_mass_kg"] = P(rnd(sm["dry_kg"]), "DERIVED mass ledger v3c (mechanical.json v1 gimballed engine + ring; ASSUMED fixed "
                          "propulsion items, airframe, legs, avionics, recovery)",
                          f"range {sm['dry_min_kg']:.2f}-{sm['dry_max_kg']:.2f} kg (item min/max); propulsion {sm['propulsion_kg']:.2f} kg, "
                          f"airframe {sm['airframe_kg']:.2f} kg; MC disperses dry mass N(1, 0.05)")
    rv["fuel_grain_mass_kg"] = P(comb["gas_path"]["grain"]["mass_kg"]["v"], f"combustion.json {comb.get('version')} grain mass_kg (DERIVED there)")
    rv["n2o_load_kg"] = P(rnd(b["m_n2o_mc_kg"]), f"SIM 6-DOF sizing of the nominal A-D flight ({b['m_n2o_sized_kg']:.3f} kg with 20 % "
                          "usable-liquid reserve) x 1.15 MC load margin", "was 1.30 kg in v1 (RV-1, placeholder map)")
    rv["tank_volume_L"] = P(rnd(b["tank_V_L"]), "DERIVED load / (0.85 rho_l(25 C)): 15 % ullage at 25 C (ASSUMED fill rule)",
                            f"internal length {VH['tank_internal_length_m']:.3f} m in the 101.6 x 3.175 mm tube "
                            "(mechanical.json v1 sized 289 mm for 2.06 L)")
    rv["liftoff_mass_kg"] = P(rnd(VH["m_liftoff_kg"]), "SIM nominal A-D flight (ledger v3c + load)")
    rv["landing_mass_kg"] = P(rnd(VH["m_land_nominal_kg"]), "SIM nominal A-D flight",
                              f"MC: dry +/-5 % 1 sigma; landing-mass window in icd_inputs_for_airframe")
    rv["mass_properties_vs_time"] = {
        "events": [{k: rnd(v, 4) for k, v in e.items()} for e in VH["events"]],
        "vs_propellant_state_csv": "01-systems-gnc/vehicle/massprops_vs_propellant_v3c.csv",
        "full_histories": "every duty-cycle CSV v2 carries m_kg, z_cg_m, I_transverse_kgm2, I_roll_kgm2",
        "tag": "SIM sim6 v2.2 nominal A-D flight (no wind) + DERIVED vehicle.massprops (liquid settled aft, rigid in pitch, "
               "excluded from roll; grain from combustion.json)"}
    cg = VH["cg"]
    rv["liquid_level_cg_shift"] = P({"full_load_forward_minus_aft_m": cg["liquid_forward_excursion_full_m"],
                                     "at_MECO_m": cg["liquid_forward_excursion_meco_m"], "liquid_at_MECO_kg": cg["meco_liquid_kg"]},
                                    "DERIVED vehicle.massprops: liquid column at the forward end (drag deceleration in the "
                                    "nose-first coast) vs settled aft")
    rv["gimballed_subassembly"] = P({
        "pivot": "at the engine CG (mechanical.json v1 gimbal.pivot_location)", "z_pivot_m": VH["z_pivot_m"],
        "touchdown_state": {k: rnd(float(tw20[k]), 5) for k in ("m_e_kg", "z_e_m", "l_e_m", "I_e_own_kgm2", "J_twd_kgm2",
                                                                "l_p_m", "I_transverse_kgm2")} if tw20 else None,
        "tail_wags_dog_zero_rad_s": {f"{r['state']}|{r['F_label']}": rnd(float(r["w_twd_rad_s"]), 2) for r in TWD
                                     if r["F_label"] in ("12.5 %", "20.0 %", "hover (T=W)", "100.0 %")},
        "control_moment_per_deg_Nm": {f"{r['state']}|{r['F_label']}": rnd(float(r["Mc_per_deg_Nm"]), 3) for r in TWD
                                      if r["F_label"] in ("12.5 %", "20.0 %", "hover (T=W)", "100.0 %")},
        "table_csv": "01-systems-gnc/vehicle/twd_table_v2.csv"},
        "DERIVED vehicle.massprops + mechanical.json v1 (gimballed dry mass/inertia, grain from combustion.json)",
        "l_p = z_cg - z_pivot; l_e = z_pivot - z_e; J_twd = I_e + m_e l_e (l_e + l_p); w_twd = sqrt(F l_p / J_twd)")
    rv["aero"] = {
        "method": "component build-up (Barrowman nose, blunt-base leading term, Allen-Perkins/Jorgensen crossflow, legs, "
                  "Barrowman fins with interference); evaluated at the local velocity incl. omega x r",
        "static_table_csv": "01-systems-gnc/vehicle/aero_static_v2.csv",
        "uncertainty_sets": {"nominal": "k_base_lead 0.75, k_nose_trail 0.25, crossflow x1.0, CA x1.0",
                             "benign_tail_first": "k_base_lead 0.5, k_nose_trail 0.0, crossflow x1.25, CA x0.7",
                             "adverse_tail_first": "k_base_lead 1.0, k_nose_trail 0.5, crossflow x0.75, CA x1.3",
                             "MC": "each run draws k_base_lead U(0.5,1), k_nose_trail U(0,0.5), crossflow U(0.75,1.25), "
                                   "CA_tf U(0.7,1.3), retro factor U(0.25,0.75)"},
        "nose_first_fins": P({k: a["fins1_nominal_legs0"][k] for k in ("CNa_nose_first_per_rad", "z_cp_nose_first_2deg_m",
                                                                        "static_margin_nose_first_cal")},
                             "DERIVED aero.py (2 deg, liftoff CG)"),
        "nose_first_finless": P({k: a["fins0_nominal_legs0"][k] for k in ("CNa_nose_first_per_rad", "z_cp_nose_first_2deg_m",
                                                                           "static_margin_nose_first_cal")},
                                "DERIVED aero.py", "finless body is statically UNSTABLE nose-first"),
        "tail_first_by_set": P({k: {kk: v[kk] for kk in ("CNa_tail_first_per_rad", "z_cp_tail_first_2deg_m",
                                                         "static_margin_tail_first_cal", "static_margin_tail_first_10deg_cal")}
                                for k, v in a.items()}, "ASSUMED sets (unvalidated tail-first terms) evaluated with aero.py",
                               "negative margin = unstable engine-first; the drogue (A-D) or the TVC in the burn provides the attitude"),
        "CA": P({"nose_first": a["fins1_nominal_legs0"]["CA_nose_first"], "tail_first": a["fins1_nominal_legs0"]["CA_tail_first"],
                 "legs_deployed_increment": a["fins1_nominal_legs1"]["CA_legs_increment"]},
                "ASSUMED (+/-30 %); tail-first retropropulsion factor 0.5-1.0 with the engine on (ASSUMED)"),
        "unknowns": "Tail-first aero (CNa, CP, base/plume interaction) is UNKNOWN to better than ~x2: only CFD (05-plume-cfd), "
                    "a wind tunnel or flight data close it. The MC draws the whole band."}
    g["reference_vehicle"] = rv

    # ------------------------------------------------------------------ flight profile and descent trade
    nom = b["nominal"]
    af, bf = T.get("AF_nofins_f20"), T.get("B_f20")
    fp = {}
    fp["recommended_baseline"] = P("A-D", "DERIVED descent-attitude trade + 6-DOF MC (REPORT B, landing_closure)",
                                   "Full-thrust ascent under TVC (aft fins) -> MECO on predicted apogee (300 m) -> nose-first coast "
                                   "-> nose drogue at apogee (engine-down, liquid settled aft) -> relight planned on the latest "
                                   "ignition (0.6 s) at ~35-45 m and ~22 m/s -> drogue released on Pc-confirmed ignition -> "
                                   "throttled TVC landing burn (velocity-tracking reference + PI, PD lateral to the reachable pad "
                                   "target, disturbance feed-forward) -> 8 m terminal gate -> touchdown ~1.1 m/s -> engine cut on "
                                   "contact. Roll by N2O-vapour RCS couple throughout.")
    fp["why"] = [f"best landing closure of the full-profile options: {Pc(BASE)} vs A-F free fall {Pc('AF_nofins_f20')}",
                 f"lowest N2O load of the full profiles: {b['m_n2o_sized_kg']:.2f} kg sized vs A-F {cs['AF_nofins_f20']['m_n2o_sized_kg']:.2f} kg",
                 "drogue gives a passive engine-down attitude and settles the liquid for the relight; relight at ~22 m/s instead of ~50 m/s",
                 "drogue is also a degraded recovery path if the relight fails (vehicle loss, low-energy impact)",
                 "2 starts per flight; ENG-04 >= 3 keeps one spare"]
    fp["costs_and_risks"] = [
        f"drift under the drogue: median miss {bt['td_miss_p50']:.0f} m, p95 {bt['td_miss_p95']:.0f} m (wind U(0,8) m/s); "
        f"an upwind ascent bias from the pad wind measurement cuts the median to {T['AD_fins_f20_upwind']['td_miss_p50']:.0f} m",
        "relight at ~35-45 m leaves no time for a backup main parachute: ignition reliability is mission-critical",
        "drogue release and line/plume clearance at relight (Lauty: release + swivel at the nose)",
        "the passive drogue phase is the least modelled part (quasi-steady tension, no inflation transient)"]
    fp["baseline_numbers"] = P({"apogee_m": rnd(nom["h_max"], 1), "t_meco_s": rnd(nom["t_meco"], 2), "v_meco_mps": rnd(nom["v_meco"], 1),
                                "relight_height_m": rnd(nom["h_ign"], 1), "relight_speed_mps": rnd(nom["v_ign"], 2),
                                "total_burn_s": rnd(nom["burn_time"], 2), "propellant_used_kg": rnd(nom["prop_used"], 3),
                                "touchdown_vz_mps": rnd(nom["td_vz"], 2), "starts": int(nom["starts"]), "landing_mass_kg": rnd(nom["m_land"], 2),
                                "MC_apogee_p01_p50_p99_m": rnd([bt["h_max_p01"], bt["h_max_p50"], bt["h_max_p99"]], 1)},
                               "SIM sim6 v2.2 nominal A-D (no wind, no noise) at the MC load; MC percentiles from the baseline case")
    tr = TR or {}
    hop300 = {f"{r['floor']:.3f}": (rnd(r["m_n2o_sized_kg"]) if r["closes"] else "no closure <= 6 kg") for r in tr.get("option1_hop_300m", [])}
    o2 = tr.get("option2_flaps", {})
    o3 = tr.get("option3_rcs", {}).get("cases", {})
    fp["descent_attitude_trade"] = {
        "1_continuous_burn_hop": {
            "propellant": f"100 m hop N2O sized: 12.5 % {cs['B_f125']['m_n2o_sized_kg']:.2f} kg, 20 % {cs['B_f20']['m_n2o_sized_kg']:.2f} kg, "
                          f"25 % {cs['B_f25']['m_n2o_sized_kg']:.2f} kg; 300 m apex: {hop300}",
            "landing_P": f"B 100 m: 20 % {Pc('B_f20')}, 25 % {Pc('B_f25')}, 12.5 % {Pc('B_f125')}",
            "added_mass": "none (no drogue); larger tank", "authority": "TVC always available (>= floor thrust)",
            "failure_modes": "long burn (grain/thermal, ENG-06 15 s exceeded), propellant-limited apex, floor-coast "
                              "controllability at low floor thrust",
            "airframe_needs": "legs fixed from liftoff; none else", "verdict": "test-campaign profile (tethered/low hops) and fallback; not for 300 m"},
        "2_tvc_flip_tail_first_aero": {
            "propellant": f"A-F free fall relight at ~{abs(af['v_ign_p50']):.0f} m/s: N2O sized {cs['AF_nofins_f20']['m_n2o_sized_kg']:.2f} kg "
                          f"(+{cs['AF_nofins_f20']['m_n2o_sized_kg'] - b['m_n2o_sized_kg']:.2f} kg vs A-D)",
            "flap_area_for_tail_first_stability_m2": o2.get("min_area_restoring_2_5_10deg_m2"),
            "added_mass": "flaps/grid fins + deployment ~0.4-0.8 kg ASSUMED",
            "authority": "aero restoring moment only with sufficient flap area (sweep in trade_flaps_v2.csv); none at low speed",
            "failure_modes": "flap deployment failure, tail-first aero unknown to ~x2, high-speed relight (TVC flip at ignition)",
            "airframe_needs": "hinged flaps/grid fins and actuators at the nose; flap loads", "landing_P_finless_free_fall": Pc("AF_nofins_f20")},
        "3_n2o_cold_gas_attitude_rcs": {
            "control_moment_and_impulse": {k: rnd({kk: v[kk] for kk in ("M_aero_max_Nm", "thruster_force_with_margin_2_N",
                                                                        "thruster_impulse_Ns", "vapour_kg_isp50", "tank_dT_K")}, 3)
                                           for k, v in o3.items()},
            "added_mass": "6 valves + nozzles + lines ~0.6 kg ASSUMED (P13)", "valve_count": "4 pitch/yaw + 2 roll (6 NC solenoids)",
            "failure_modes": "valve stuck open, icing/two-phase flow in the lines, tank cooling (lower thrust ceiling), "
                              "insufficient thrust at high descent speed",
            "airframe_needs": "nozzle ports at the nose, lines along the body, valve bay", "verdict": "not baseline for pitch/yaw; roll-only RCS is baseline"},
        "4_nose_drogue": {
            "propellant": f"N2O sized {b['m_n2o_sized_kg']:.2f} kg (lowest of the full profiles)", "added_mass": "0.35 kg (drogue, ejection, release, swivel)",
            "authority": "passive engine-down attitude; liquid settled", "landing_P": Pc(BASE),
            "failure_modes": "deployment/tangling, release failure, plume-line interaction at relight, drift with wind, "
                              "failed relight -> impact at ~22 m/s",
            "airframe_needs": "nose drogue bay + ejection + release + swivel, line clearance from the plume", "verdict": "BASELINE"},
        "5_research_proposals": "REPORT section B.5 (hypothesis, comparator, evidence, refutation criterion for each)",
        "tag": "SIM m2_mc6 v2 / m2_trade v2 (sim6 v2.2, aero.py) + DERIVED"}
    fp["test_campaign"] = [
        "T0 bench: gimbal + servos (stiffness, rocking mode and damping, backlash, hinge torque, slew vs angle), IMU bias/temperature, "
        "LiDAR/GNSS, structural command filter in the ECU, drogue-release actuator",
        "T1 static fires (DC-D): ignition latency distribution (>= 30 starts), throttle map and Pc loop (t10-90, slew, resolution, "
        "floor stability), 3 starts per run, gimbal sweeps under thrust, thrust-vector alignment, ENGINE ROLL TORQUE, rocking mode under thrust",
        "T2 tethered hover (DC-C): 0.5-2 m; hover, doublets, TVC attitude hold, estimator and thrust-effectiveness estimator, roll RCS",
        "T3 low hops (B, 5-50 m then 100 m) with the hover-capable floor; legs fixed; landing guidance and lateral divert",
        "T4 drogue drop tests (no engine, dummy mass): deployment, swing, drift, release",
        "T5 relight hop (A-D mini: MECO ~60-100 m, drogue, relight ~30-40 m)",
        "T6 full profile A-D 300 m (ACEMA 2027-09-01)"]
    g["flight_profile"] = fp

    # ------------------------------------------------------------------ requirements
    rq = {}
    m_land = VH["m_land_nominal_kg"]
    win = {f"{fl*100:.1f}%": rnd(fl * 500.0 / (0.9 * R.G0), 2) for fl in (0.125, 0.20, 0.25, 0.40)}
    floorP = {f: Pc(c) for f, c in (("12.5%", "AD_fins_f125"), ("20%", BASE), ("25%", "AD_fins_f25"), ("40%", "AD_fins_f40"))}
    rq["throttle"] = {
        "floor_frac_required_max": P(0.20, "DERIVED 6-DOF MC (landing closure by floor) + hover rule",
                                     f"RV-1c landing mass {m_land:.2f} kg nominal: hover rule T_floor <= 0.9 W gives floor <= "
                                     f"{0.9 * m_land * R.G0 / 500:.3f}; MC A-D: {floorP}{mcn('AD_fins_f25')} (25 % vs 20 %). "
                                     "20 % keeps the hover window over the dry-mass dispersion; 25 % sits on the boundary "
                                     "(about half the runs switch to hoverslam)."),
        "floor_frac_acceptable_flight": P(0.25, "SIM m2_mc6 v2 AD_fins_f25 / AD_fins_f25_ballast",
                                          f"25 % flies at {Pc('AD_fins_f25')}; with {T['AD_fins_f25_ballast']['ballast_kg']:.1f} kg ballast "
                                          f"{Pc('AD_fins_f25_ballast')}. 40 % FAILS without ballast ({Pc('AD_fins_f40')}: hoverslam "
                                          f"lateral/rate failures) and needs {T['AD_fins_f40_ballast']['ballast_kg']:.1f} kg ballast and "
                                          f"{T['AD_fins_f40_ballast']['m_n2o_mc_kg']:.2f} kg N2O ({Pc('AD_fins_f40_ballast')})"),
        "floor_frac_goal": P(0.125, "REQ ENG-02 rev1 stretch (8:1)", f"A-D at 12.5 %: {Pc('AD_fins_f125')}; hop B at 12.5 %: {Pc('B_f125')}"),
        "hover_rule": P("hover-capable if T_floor <= 0.9 W_land(estimated); otherwise the flight software selects the hoverslam",
                        "DERIVED (lead update 2026-10-11)", f"forced hoverslam at 20 %: {Pc('AD_fins_f20_hslam')}"),
        "landing_mass_window_min_kg_by_floor": P(win, "DERIVED m_land >= F_floor / (0.9 g0)",
                                                 f"RV-1c nominal landing mass {m_land:.2f} kg"),
        "t10_90_s": P(0.15, "REQ ENG-03 (target 0.10 s); SIM 6-DOF MC disperses the thrust lag x U(0.7, 1.5) around 0.10 s -> "
                      "0.07-0.15 s, closure above", "1-D v1 sweep: P >= 0.99 up to 0.30 s"),
        "pc_loop_bandwidth_Hz": P(2.3, "DERIVED first-order equivalent of t10-90 0.15 s"),
        "slew_min_Fmax_per_s": P(2.0, "SIM mc1d v1p2 slew sweep (6-DOF runs at 5 F_max/s)", "target 5 F_max/s"),
        "resolution_frac": P(0.02, "REQ ENG-03", "6-DOF runs with 1 % quantisation; 2 % from the 1-D sweep (6-DOF check at 2 % open)"),
        "overshoot_max_frac": P(0.10, "ASSUMED (not exercised by the first-order plant; combustion.json plant phi 0.1 open-loop "
                                "case flies at " + Pc("AD_fins_f20_openloop") + ")"),
        "pc_closed_loop_required": P(True, "SIM AD_fins_f20_openloop", f"open-loop pintle with the fuel lag: {Pc('AD_fins_f20_openloop')} "
                                     f"vs {Pc(BASE)}{mcn('AD_fins_f20_openloop')}; Pc closed loop kept (ENG-03)"),
        "deadband_max_frac": P(0.005, "ASSUMED (as simulated)"),
        "ceiling_at_landing_min_N": P(rnd(1.5 * m_land * R.G0, 1), "DERIVED 1.5 x landing weight (RV-1c)"),
        "thrust_effectiveness_estimation": P("FC estimates delivered/commanded thrust from the accelerometer (tau 0.1 s) in the landing burn, "
                                             "nominal drag model", "SIM (all 6-DOF cases)", "needs Pc and accelerometer >= 100 Hz in the FC"),
    }
    rq["ignition"] = {
        "latency_cmd_to_90pct_max_s": P(0.5, "REQ ENG-04 (target 0.3 s)",
                                        f"6-DOF MC draws U(0.2, 0.6) s with the relight planned on 0.6 s: {Pc(BASE)}; latency is the top "
                                        "driver of |vz| at touchdown (Spearman ~0.47) but not of failure"),
        "relight_planning_value_s": P(0.6, "DESIGN flight software plans the relight on the latest ignition"),
        "repeatability_s": P(0.05, "REQ ENG-04 (+/-50 ms)", "6-DOF closes with a 0.4 s spread when planning on the latest; tighter "
                             "spread lowers the relight height and propellant"),
        "latency_sweep_1d": P((g1 or {}).get("requirements", {}).get("ignition", {}).get("latency_sweep", {}).get("v"),
                              "SIM mc1d v1p2 (gnc.json v1, RV-1) kept"),
        "starts_per_flight_used": P({"A-D": 2, "A-F": 2, "B": 1, "tethered_hover": 1}, "SIM profiles"),
        "starts_per_flight_required": P(3, "REQ ENG-04", "one spare relight"),
        "relight_conditions": P("liquid settled aft by the drogue (~1 g); tank P >= 3.5 MPa; chamber purged; ignition at the floor; "
                                "drogue release only on Pc >= 50 % of floor Pc", "DERIVED CONOPS"),
        "shutdown_tail_off": P("< 10 % thrust within 0.10 s", "REQ ENG-05", "simulated tau_off 35 ms"),
    }
    gm = {}
    gm["range_deg"] = P(7.0, "SIM m2_mc6 v2 gimbal-limit cases + DERIVED", (
        f"commanded limit on the VECTOR norm (mechanical.json v1 REQUEST): CONFIRMED. 7 deg: {Pc(BASE)}; 6 deg: {Pc('AD_fins_f20_gim6')}"
        f"{mcn('AD_fins_f20_gim6')}; 5 deg: {Pc('AD_fins_f20_gim5')}{mcn('AD_fins_f20_gim5')}. Engine angle p99 {bt['max_gim_p99']:.2f} deg, "
        f"max {bt['max_gim_max'] if 'max_gim_max' in bt else T[BASE].get('max_gim_p99')} deg (flexible-mount overshoot beyond the 7 deg command, "
        f"inside the 8 deg conical stop); saturated fraction of burn p99 {bt['gim_sat_frac_p99']:.3f}"))
    gm["mechanical_stop_deg"] = P(mech["gimbal"]["mechanical_stop_deg"]["v"], f"mechanical.json {mech.get('version')} (accepted)")
    gm["rate_min_dps"] = P(100.0, "SIM m2_mc6 v2 (command slew limit 100 deg/s in every baseline run) + AD_fins_f20_rate60",
                           f"engine-side slew under load within +/-5 deg; 60 deg/s command limit: {Pc('AD_fins_f20_rate60') if 'AD_fins_f20_rate60' in T else 'see REPORT'}"
                           f"{mcn('AD_fins_f20_rate60')}. At the 7 deg extreme the crank (psi ~47 deg) cuts the no-load engine rate to "
                           f"~{857 / 6 * np.cos(np.radians(47)):.0f} deg/s: >= 60 deg/s there. Raises ENG-07 60 deg/s.")
    gm["angular_accel_min_rad_s2"] = P(rnd(np.radians(100.0) / 0.02, 1), "DERIVED reach 100 deg/s within 20 ms",
                                       f"MC engine angular acceleration p99 {bt['max_gim_acc_p99']:.0f} rad/s2 (includes rocking-mode ringing)")
    gm["bandwidth_min_Hz"] = P(10.0, "SIM: MC disperses the actuator natural frequency U(62.8, 157.1) rad/s (10-25 Hz, zeta 0.7, "
                               "electronics.json v1 range) + up to 3.2 ms extra delay; CSI worst actuator 62.8 rad/s",
                               "ENG-07 8 Hz is NOT demonstrated; 10 Hz is the lowest value flown")
    gm["resolution_max_deg"] = P(0.1, "REQ ENG-07", f"mechanical.json v1: {mech['tvc_actuation']['resolution_deg_engine']['v']} deg (as simulated)")
    gm["backlash_max_deg"] = P(0.1, "DERIVED limit-cycle allowance", f"mechanical.json v1: {mech['tvc_actuation']['backlash_deg_engine']['v']} deg (as simulated)")
    gm["latency_cmd_to_motion_max_s"] = P(0.010, "SIM MC up to 7.7 ms + 3.2 ms", "electronics.json v1: 7.7 ms max")
    gm["hinge_moment"] = P({"flight_p99_Nm": rnd(bt["max_hinge_p99"], 2), "flight_max_Nm": rnd(bt["max_hinge_max"], 2),
                            "after_touchdown_p99_Nm": rnd(bt["max_hinge_td_p99"], 2), "after_touchdown_max_Nm": rnd(bt["max_hinge_td_max"], 2),
                            "mechanical_linear_sum_Nm": mech["tvc_actuation"]["hinge_moment_design_Nm"]["v"],
                            "servo_stall_at_engine_neutral_7V4_Nm": rnd(0.9 * 6.0 * el["actuators"]["tvc_A"]["stall_torque_Nm"]["v"]["7.4V"], 2)},
                           "SIM sim6 v2.2 mount torque K(d_link - d_engine) + c(..) with base excitation (baseline MC)",
                           "transient peaks (relight and attitude manoeuvres with the rocking mode ringing) exceed the 5.6 N m "
                           "linear-sum design value and approach the servo stall; the actuator saturates in torque at times "
                           "(closure above includes this). Design the gimbal parts for the actuator stall load "
                           f"({mech['tvc_actuation']['stall_load_on_structure']['engine_moment_Nm_8V4']['v']} N m at 8.4 V, mechanical.json).")
    gm["command_shaping_in_ecu"] = P({"slew_limit_dps": R.DEF["gim_cmd_rate"], "lowpass_2nd_order_w_rad_s": R.DEF["gim_lpf_w"],
                                      "lowpass_zeta": R.DEF["gim_lpf_z"], "rate_Hz": ">= 500 (ECU tvc_shaping task 1000 Hz)"},
                                     "DERIVED CSI (m2_csi v2) + SIM", "MANDATORY: without it the rocking mode destabilises the loop in the "
                                     "linear model and the 6-DOF linkage torque reaches " +
                                     (f"{T['AD_fins_f20_nolpf']['max_hinge_p99']:.0f} N m p99" if 'AD_fins_f20_nolpf' in T else "far above stall"))
    rq["gimbal"] = gm
    # structure
    csum = (CSI or {}).get("summary", {})
    rock = (CSI or {}).get("rocking_landing", {})
    bend = (CSI or {}).get("bending_landing", {})
    rq["structure"] = {
        "gimballed_engine_first_mode_min_Hz": P(25.0, "DERIVED ENG-11 (>= 3 x actuator 8 Hz) + CSI m2_csi v2",
                                                f"mechanical.json v1 rocking mode {rock.get('f_rock_Hz')} Hz (rigid structure) PASSES with "
                                                "the structural command filter; FEA with pushrod/lever/frame compliance must stay >= 25 Hz"),
        "rocking_mode_damping_min": P(0.02, "SIM range flown U(0.02, 0.10) (ASSUMED, unpublished)", "bench-measure"),
        "csi_margins_with_filter": P({k: csum.get("lpf", {}).get(k) for k in ("n_cases", "n_unstable", "rigid_pm_min_deg",
                                                                              "rigid_gm_up_min_dB", "flex_gm_up_min_dB")},
                                     "SIM m2_csi v2 (python-control, Pade-3 delay)",
                                     f"without filter: {csum.get('nofilt', {}).get('n_unstable')} of {csum.get('nofilt', {}).get('n_cases')} "
                                     "linear cases unstable (rocking mode in the loop)"),
        "airframe_first_bending_min_Hz": P(10.0, "DERIVED >= 5 x attitude crossover; goal 15 Hz",
                                           f"uniform PETG tube estimate {bend.get('f_b_Hz')} Hz (ASSUMED E 2 GPa); Lauty's FE model replaces it"),
        "tail_wags_dog_zero_min_rad_s": P(20.0, "DERIVED >= ~3 x attitude bandwidth (6 rad/s) at the floor thrust; SIM evidence",
                                          (f"RV-1c CG pivot at touchdown: 12.5 % {tw125['w_twd_rad_s'] if tw125 else '?'} rad/s, 20 % "
                                           f"{tw20['w_twd_rad_s'] if tw20 else '?'} rad/s, hover {twh['w_twd_rad_s'] if twh else '?'} rad/s. "
                                           "v1 asked >= 25 rad/s: 12.5 % FAILS that number, yet the MC closes at 12.5 % "
                                           f"({Pc('AD_fins_f125')}) and the CSI floor62N cases are stable with the filter -> requirement "
                                           "restated as >= 20 rad/s at the lowest flown thrust")),
    }
    # roll
    rq["roll"] = {
        "decision": P("roll control REQUIRED", f"{MC}: no RCS {Pc('AD_fins_f20_norcs')} vs RCS {Pc(BASE)}{mcn('AD_fins_f20_norcs')}",
                      "engine roll torque drawn U(-0.1, 0.1) N m at F_max (ASSUMED helical-port estimate; to be measured in T1)"),
        "provider": P("propulsion: N2O-vapour cold-gas couple from the tank ullage, 2 NC solenoids, 4 nozzles (2 couples), "
                      "0.5 N per nozzle (ASSUMED), on the body wall", "DERIVED (REPORT option 3, roll only)"),
        "torque_Nm": P(rnd(2 * 0.5 * VH["d_body_m"] / 2, 4), "DERIVED 2 x 0.5 N x body radius", "simulated, bang-bang, deadband 5 deg/s"),
        "firing_time_p99_s": P(rnd(bt["rcs_time_p99_s"], 2), MC),
        "n2o_vapour_p99_kg": P(rnd(bt["rcs_n2o_p99_kg"], 4), "DERIVED firing time x 1 N / (Isp 50 s ASSUMED x g0)",
                               f"Isp 40 s: {bt['rcs_n2o_p99_kg_isp_low']:.4f} kg; not removed from the tank in the sim (< 1 % of the load)"),
        "added_mass_kg": P(0.25, "ASSUMED ledger P14 (0.15-0.40)"),
        "touchdown_roll_rate_p99_dps": P(rnd(bt["td_roll_rate_p99"], 2), MC),
        "roll_rate_max_p99_dps": P(rnd(bt["max_roll_rate_p99"], 1), MC),
    }
    # tank
    rq["tank"] = {
        "temperature_at_liftoff_C": P([17.0, 23.0], "REQ ENG-12 (20 +/- 3 C)", "6-DOF MC spans 15-25 C"),
        "n2o_load_A_D_kg": P(rnd(b["m_n2o_mc_kg"]), "SIM sizing x 1.15 (see reference_vehicle)"),
        "tank_volume_L": P(rnd(b["tank_V_L"]), "DERIVED 85 % liquid fill at 25 C"),
        "usable_liquid_left_p01_kg": P(rnd(bt["liq_left_p01"]), MC, "1st percentile of liquid left at touchdown (incl. 3 % residual)"),
        "n2o_load_B_hop100_floor20_kg": P(rnd(cs["B_f20"]["m_n2o_mc_kg"]), "SIM sizing x 1.15"),
        "fill_rule": P("liquid fraction <= 0.85 at 25 C", "ASSUMED"),
        "usable_liquid_reserve": P(0.20, "DERIVED sizing rule"),
        "residual_liquid_frac": P(0.03, "ASSUMED"),
    }
    # navigation
    imu_rows = (IMU or {}).get("rows", [])
    rq["navigation_and_loop_rates"] = {
        "imu_class": P("ADIS16470 class (gyro residual bias <= 0.03 deg/s after pad calibration) with the baseline gyro-propagated attitude",
                       MC, f"ADIS16470 {Pc(BASE)}; BMI088 class {Pc('AD_fins_f20_BMI088')}; ICM-42688 class {Pc('AD_fins_f20_ICM42688')} "
                       "(gyro-bias attitude drift over the ~30 s flight -> lateral-speed and crash failures). Cheaper MEMS need an "
                       "aided attitude estimator (GNSS/INS EKF), not modelled -> research item."),
        "gyro_residual_bias_sweep": P([{k: rnd(r[k], 3) for k in ("gyro_residual_bias_dps", "success", "ci95_lo", "ci95_hi", "crashes")}
                                       for r in imu_rows], "SIM m2_imu_sweep v2 (300 runs per point, ADIS16470 class otherwise)"),
        "gnss": P("standalone (u-blox M9/M10 class) sufficient", MC, f"RTK {Pc('AD_fins_f20_rtk')} vs standalone {Pc(BASE)}{mcn('AD_fins_f20_rtk')}"),
        "lidar_range_min_m": P(40.0, MC, f"12 m LiDAR {Pc('AD_fins_f20_lidar12')}{mcn('AD_fins_f20_lidar12')}"),
        "fc_to_ecu_command_rate_Hz": P(500, "DERIVED/accepted electronics.json v1"),
        "attitude_loop_rate_Hz": P(1000, "SIM (sim6 integrates the control law every 1 ms step)", "250 Hz ASSUMED in v1; 6-DOF flown at 1 kHz"),
        "nav_filter_rate_Hz": P(100, "SIM sim6 estimator"),
        "link_loss_policy_in_RUN": P("ascent: SHUTDOWN after 0.1 s (backup chute); landing burn: HOLD last Pc setpoint and gimbal 0.3 s, then SHUTDOWN",
                                     "DERIVED (unchanged from v1)"),
    }
    # guidance comparison
    rq["guidance"] = {
        "baseline": P("vertical: velocity-tracking reference + PI with thrust-effectiveness estimator; lateral: PD to the reachable target "
                      "+ disturbance feed-forward; 8 m terminal gate", MC, Pc(BASE)),
        "convex_lite_lateral": P(Pc("AD_fins_f20_cvx"), MC, mcn("AD_fins_f20_cvx").lstrip("; ")),
        "zem_zev_vertical_and_lateral": P(Pc("AD_fins_f20_zemzev"), MC, f"sized N2O {cs['AD_fins_f20_zemzev']['m_n2o_sized_kg']:.2f} kg; see REPORT"),
        "hoverslam_forced_20pct": P(Pc("AD_fins_f20_hslam"), MC),
        "upwind_ascent_bias": P(f"k = {1.5} m/s per m/s of measured pad wind", MC,
                                f"{Pc('AD_fins_f20_upwind')}, median miss {T['AD_fins_f20_upwind']['td_miss_p50']:.0f} m vs {bt['td_miss_p50']:.0f} m"),
    }
    g["requirements"] = rq

    # ------------------------------------------------------------------ limit loads (engine mount)
    def mx(key):
        return rnd(bt.get(key), 2)
    g["design_limit_loads"] = {
        "note": "LIMIT loads = maxima over the 500 dispersed baseline runs (p99 given for reference), engine-mount station unless "
                "stated. Mechanical applies ENG-10 factors (1.5 yield, 2.0 ultimate). Touchdown values depend on the ASSUMED legs "
                "(k 2500 N/m per leg, c 120 N s/m, stroke 0.10 m, mu 0.3-0.7) and are only as good as that assumption.",
        "axial_accel_flight_g": P(mx("max_axial_g_flt_max"), MC + " max (flight, before touchdown)", f"p99 {mx('max_axial_g_flt_p99')} g; MECO at full thrust"),
        "axial_accel_touchdown_g": P(mx("max_axial_g_td_max"), MC + " max (after first contact, rigid body at the CG)",
                                     f"p99 {mx('max_axial_g_td_p99')} g; v1 design value 10 g (3 m/s off-nominal, 0.1 m stroke) is kept as the "
                                     "envelope for a hard landing"),
        "axial_accel_landing_shock_envelope_g": P(10.0, "DERIVED v1: 3 m/s touchdown, 0.10 m stroke, 50 % efficiency"),
        "lateral_accel_at_pivot_flight_g": P(mx("max_lat_g_eng_flt_max"), MC + " max", f"p99 {mx('max_lat_g_eng_flt_p99')} g"),
        "lateral_accel_at_pivot_touchdown_g": P(mx("max_lat_g_eng_td_max"), MC + " max", f"p99 {mx('max_lat_g_eng_td_p99')} g"),
        "body_angular_rate_max_rad_s": P(rnd(np.radians(max(bt["max_rate_coast_p99"], 1e-9)), 3), MC + " p99 coast rate (fins)",
                                         "finless coast tumbles (see landing_closure AD_nofins_f20)"),
        "body_angular_accel_flight_rad_s2": P(mx("max_alpha_flt_max"), MC + " max", f"p99 {mx('max_alpha_flt_p99')}"),
        "body_angular_accel_touchdown_rad_s2": P(mx("max_alpha_td_max"), MC + " max", f"p99 {mx('max_alpha_td_p99')}"),
        "hinge_moment_flight_Nm": P(mx("max_hinge_max"), MC + " max", f"p99 {mx('max_hinge_p99')}"),
        "hinge_moment_touchdown_gimbal_unlocked_Nm": P(mx("max_hinge_td_max"), MC + " max (actuator holds/returns the engine after "
                                                       "touchdown; base excitation incl.)", f"p99 {mx('max_hinge_td_p99')}"),
        "peak_total_leg_force_N": P(mx("peak_leg_force_max"), MC + " max", f"p99 {mx('peak_leg_force_p99')}; Lauty's legs"),
        "gimbal_angular_accel_actuator_max_rad_s2": P(rnd(bt["max_gim_acc_p99"], 0), MC + " p99"),
        "transport_handling_g": P(3.0, "ASSUMED any axis, gimbal locked (mechanical.json transport lock)"),
        "duty_cycle_loads": "time histories of F, a_axial, m, CG, inertia, gimbal angles and hinge estimate in every duty-cycle CSV v2"}

    # ------------------------------------------------------------------ duty cycles
    dc = {}
    for c in (DCI or {}).get("cycles", []):
        dc[c["name"]] = {"file": f"01-systems-gnc/duty_cycles/{c['file']}", "burn_s": rnd(c["burn_time_s"], 2),
                         "impulse_Ns": rnd(c["total_impulse_Ns"], 0), "starts": c.get("starts"),
                         "max_axial_specific_mps2": rnd(c.get("max_axial_specific_mps2"), 2),
                         "max_gimbal_deg": rnd(c.get("max_gimbal_deg"), 2), "success": c.get("success")}
    g["duty_cycles"] = {"index": "01-systems-gnc/duty_cycles/duty_cycles_index_v2.json", "files": dc,
                        "columns": (DCI or {}).get("cycles", [{}])[0].get("columns"),
                        "tag": "SIM sim6 v2.2 (flights, combustion.json v1 map) / DERIVED commanded test sequences",
                        "note": f"longest flight burn {(DCI or {}).get('longest_flight_burn_s', float('nan')):.1f} s; DC-D qualification "
                                f"ratio to it {((DCI or {}).get('qualification_check') or {}).get('ratio_to_longest_flight', float('nan')):.2f}"}
    # ------------------------------------------------------------------ landing closure table
    keep = ["case", "note", "vehicle", "success", "ci95_lo", "ci95_hi", "fail_modes", "m_n2o_sized_kg", "m_n2o_mc_kg", "tank_V_L",
            "m_liftoff_kg", "ballast_kg", "td_vz_p99", "td_vh_p99", "td_tilt_p99", "td_rate_p99", "td_miss_p50", "td_miss_p95",
            "prop_used_p50", "liq_left_p01", "max_gim_p99", "gim_sat_frac_p99", "max_hinge_p99", "max_rate_coast_p99",
            "hslam_frac", "paired_delta_vs_base", "mcnemar_p_vs_base"]
    g["landing_closure"] = {"cases": [{k: rnd(T[c].get(k), 4) for k in keep if k in T[c]} for c in T],
                            "table_csv": "01-systems-gnc/results/mc6_cases_summary_v2.csv",
                            "tag": MC, "criteria": S["criteria"], "load_margin": S["load_margin"],
                            "failure_drivers_csv": "01-systems-gnc/results/mc6_failure_drivers_v2.csv",
                            "failure_forensics": "01-systems-gnc/results/mc6_failure_forensics_v2.csv",
                            "sensitivity_baseline": b["sensitivity"],
                            "v1_1d_reference": "gnc.json v1 landing_closure (1-D, RV-1) superseded"}
    # ------------------------------------------------------------------ verification summary
    if VF:
        g["verification_6dof"] = {
            "torque_free": [rnd({k: r[k] for k in ("dt", "H_rel_drift_max", "Ek_rel_drift_max", "qnorm_err_max")}, 8) for r in VF["torque_free"]],
            "vacuum_ballistic": [rnd({k: r[k] for k in ("dt", "E_rel_drift_max", "z_err_max_m")}, 8) for r in VF["vacuum_ballistic"]],
            "dt_convergence": [rnd({k: r[k] for k in ("profile", "dt", "wind", "td_vz", "td_vh", "h_max", "prop_used", "td_t")}, 4)
                               for r in VF["dt_convergence"]],
            "zero_dispersion": [rnd({k: r[k] for k in ("profile", "fins", "success", "td_vz", "prop_used", "h_max")}, 4) for r in VF["zero_dispersion"]],
            "vs_sim1d": [{"profile": c["profile"], "sim6": rnd({k: c["sim6"][k] for k in ("h_max", "prop_used", "h_ign", "v_ign", "td_vz")}, 3),
                          "sim1d": rnd({k: c["sim1d"][k] for k in ("h_max", "prop_used", "h_ign", "v_ign", "td_v")}, 3)} for c in VF["compare_sim1d"]],
            "vs_lead_seed": rnd({"seed": {k: v for k, v in VF["compare_lead_seed"]["seed"].items() if k != "seed_file"},
                                 "sim6_AF": {k: VF["compare_lead_seed"]["sim6_AF"][k] for k in ("prop_used", "h_ign", "v_ign", "h_max", "m_land")}}, 4),
            "file": "01-systems-gnc/results/verify6_v2.json", "tag": "SIM m2_verify6 v2"}
    if CTD:
        rows = CTD["rows"]
        g["csi_time_domain"] = {"rows": [rnd(r, 3) for r in rows], "tag": "SIM m2_csi_timedomain v2",
                                "summary": {"lpf_on_max_hinge_Nm": rnd(max(r["max_hinge_Nm"] for r in rows if r["lpf_rad_s"] > 0), 2),
                                            "lpf_off_max_hinge_Nm": rnd(max(r["max_hinge_Nm"] for r in rows if r["lpf_rad_s"] == 0), 2),
                                            "lpf_on_max_hf_rms_deg": rnd(max(r["hf_rms_deg"] for r in rows if r["lpf_rad_s"] > 0), 3),
                                            "lpf_off_max_hf_rms_deg": rnd(max(r["hf_rms_deg"] for r in rows if r["lpf_rad_s"] == 0), 3)}}

    # ------------------------------------------------------------------ answers, requests, open interface issues
    g["answers_to_requests"] = {
        "mechanical_7deg_vector_norm": f"CONFIRMED (7 deg {Pc(BASE)}; 6 deg {Pc('AD_fins_f20_gim6')}; 5 deg {Pc('AD_fins_f20_gim5')}); "
                                       "sim6 applies the limit to the vector norm with the 8 deg conical stop behind it",
        "mechanical_cg_pivot": (f"CONFIRMED with a caveat: TWD zero at touchdown 20 % {tw20['w_twd_rad_s'] if tw20 else '?'} rad/s, 12.5 % "
                                f"{tw125['w_twd_rad_s'] if tw125 else '?'} rad/s (below the v1 25 rad/s number; requirement restated to >= 20 rad/s "
                                "with MC/CSI evidence). Keep the pivot at or slightly aft of the wet engine CG: J_twd grows with l_e; "
                                "each mm of l_e changes J_twd by ~2 %."),
        "mechanical_limit_loads_engine_mount_landing_gimbal_unlocked": "design_limit_loads *_touchdown_* and hinge_moment_touchdown_gimbal_unlocked_Nm",
        "electronics_v1_requests": "gimbal range/rate/bandwidth/resolution, throttle response/resolution, link-loss policy, GNC loop rate: requirements above",
    }
    g["requests"] = [
        "REQUEST mechanical: (1) design the gimbal/linkage for the actuator stall load and the SIM hinge peaks (design_limit_loads); "
        "(2) bench-measure the rocking mode and its damping (flown 0.02-0.10) and the servo stiffness; (3) list masses of the fixed "
        "module (thrust frame, servos, valve, feed) - GNC ledger ASSUMES 1.37 kg; (4) tank length for "
        f"{b['tank_V_L']:.2f} L ({b['m_n2o_mc_kg']:.2f} kg N2O); (5) grain mass basis (mechanical 0.369 kg vs combustion 0.351 kg)",
        "REQUEST electronics: (1) structural command filter + 100 deg/s slew limit in the ECU TVC shaping task; (2) IMU ADIS16470 "
        "class or an aided estimator for cheaper MEMS; (3) gimbal engine-side slew >= 100 deg/s within +/-5 deg; (4) 2 NC "
        "solenoid drivers for the roll RCS; (5) Pc and accelerometer >= 100 Hz to the FC",
        "REQUEST combustion: (1) engine roll torque vs throttle (helical port) - roll RCS sized for |0.1| N m; (2) ignition-latency "
        "distribution of the torch (MC U(0.2, 0.6) s); (3) throttle map at the v2 tank load and the 15-25 C tank range; "
        "(4) duty cycles v2 for the grain/thermal design (longest flight burn above)",
        "REQUEST lead/airframe (Lauty): fins (span 0.12 m, 0.3 kg) or a finless coast with tumbling; drogue CdA 0.5 m2 + release + "
        "swivel; legs (stroke >= 0.10 m, k/c as simulated); CG range and landing-mass window below; body 146 mm; first bending >= 10 Hz",
        "REQUEST lead: confirm A-D baseline, launch-commit wind (MC success drops above ~7 m/s), landing-zone radius (median miss "
        f"{bt['td_miss_p50']:.0f} m, p95 {bt['td_miss_p95']:.0f} m without upwind bias)"]
    g["open_interface_issues"] = [
        f"tank: gnc.json v2 load {b['m_n2o_mc_kg']:.2f} kg / {b['tank_V_L']:.2f} L vs mechanical.json v1 tank 2.06 L (289 mm) vs combustion.json v1 "
        "placeholder 2.5 L / 1.6 kg",
        "grain mass: mechanical.json v1 gimballed wet-dry difference 0.369 kg vs combustion.json v1 grain 0.351 kg (GNC uses combustion)",
        "mechanical.json v1 fixed module (thrust frame, servos, NC valve, feed) has no masses: GNC ledger ASSUMES them",
        f"hinge moment: mechanical.json v1 design 5.63 N m (linear sum) vs SIM peaks {bt['max_hinge_p99']:.1f} N m p99 (transients)",
        "gimbal rate: ENG-07 / gnc.json v1 60 deg/s raised to 100 deg/s (command slew limit); at the 7 deg extreme the crank allows ~97 deg/s no-load",
        "rocking-mode damping and servo stiffness are unpublished (electronics.json ASSUMED); CSI depends on them",
        "engine-bay ID 140 mm / 146 mm body is a provisional lead decision; RV-1b (126 mm) comparator: " + Pc("AD_fins_f20_RV1b"),
        "IMU: electronics.json v1 has no FC IMU selection yet; ADIS16470 class required by this analysis",
        "engine roll torque unknown (U(-0.1, 0.1) N m assumed); roll RCS hardware not yet in any propulsion interface file",
        "duty cycles: combustion.json v1 says 'duty cycles from gnc.json not yet available' - v2 CSVs published here"]
    g["icd_inputs_for_airframe"] = {
        "body_diameter_m": P(rnd(VH["d_body_m"]), "DERIVED (see reference_vehicle)"),
        "landing_mass_window_kg": P({"floor_12.5%": [win["12.5%"], 16.0], "floor_20%": [win["20.0%"], 16.0],
                                     "floor_25%": [win["25.0%"], 16.0], "floor_40%": "none below 22.7 kg (ballast)"},
                                    "DERIVED hover rule; upper bound REQ ref. vehicle 16 kg", f"RV-1c nominal {m_land:.2f} kg"),
        "cg_range_z_m": P({"flight_history": cg["flight_history_m"], "ledger_extremes_dry": cg["ledger_extremes_dry_m"],
                           "liquid_forward_excursion_m": cg["liquid_forward_excursion_full_m"]}, "SIM nominal flight + DERIVED ledger extremes"),
        "touchdown_vertical_speed_max_mps": P(2.0, "REQ", f"MC p99 {bt['td_vz_p99']:.2f} m/s"),
        "touchdown_lateral_speed_max_mps": P(0.5, "REQ", f"MC p99 {bt['td_vh_p99']:.2f} m/s"),
        "touchdown_tilt_max_deg": P(5.0, "REQ brief", f"MC p99 {bt['td_tilt_p99']:.2f} deg"),
        "touchdown_tilt_rate_max_dps": P(10.0, "REQ brief", f"MC p99 {bt['td_rate_p99']:.2f} deg/s"),
        "leg_stroke_min_m": P(0.10, "ASSUMED (as simulated)"),
        "leg_design_values": P({"k_per_leg_N_m": 2500.0, "c_per_leg_N_s_m": 120.0, "foot_radius_m": 0.40, "mu": [0.3, 0.7]},
                               "ASSUMED (as simulated)", f"peak total leg force p99 {bt['peak_leg_force_p99']:.0f} N"),
        "drogue_CdA_m2": P(0.5, "DERIVED descent ~22 m/s at ~14.4 kg", "MC x U(0.85, 1.15)"),
        "fins": P("4 x span 0.12 m, chords 0.20/0.10 m at the aft end", "DERIVED trade", f"coast rate p99 {bt['max_rate_coast_p99']:.0f} deg/s"),
        "roll_rcs_mounting": P("4 nozzles on the body wall (2 tangential couples), lines from the tank ullage", "DERIVED"),
    }
    g["open_items"] = [
        "Tail-first aero unknown to ~x2 (CFD/tunnel/drop test); drogue inflation and swing dynamics not modelled",
        "Ignition reliability at relight is mission-critical (no backup chute window below ~40 m)",
        "Aided attitude estimator (GNSS/INS) would relax the IMU requirement - research item",
        "Rocking-mode damping, servo stiffness, hose stiffness, legs: bench data replace the ASSUMED ranges",
        "ZEM/ZEV vertical comparator needs a tgo-update fix (REPORT)" if T.get("AD_fins_f20_zemzev", {}).get("success", 1) < 0.95 else "",
        "Throttle resolution 2 % not yet flown in the 6-DOF (1 % flown)"]
    g["open_items"] = [x for x in g["open_items"] if x]
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    json.dump(g, open(DEST, "w"), indent=1, default=float, allow_nan=False)
    print("written", DEST, os.path.getsize(DEST))


if __name__ == "__main__":
    main()
