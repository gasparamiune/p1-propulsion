"""Writes interfaces/mechanical.json v1 (M1, 2026-10-12) from the pivot trade and the M1 mass estimate.
v2 is generated from the CAD v3 ledger by make_all.py.  Every number carries a tag."""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import config


def t(v, tag, src="", unit="", **kw):
    d = {"v": v, "tag": tag}
    if unit: d["unit"] = unit
    if src: d["src"] = src
    d.update(kw)
    return d


def main(out_path, trade_path, est_path):
    P, _ = config.build()
    TR = json.loads(Path(trade_path).read_text())
    ES = json.loads(Path(est_path).read_text())
    cand = {c["candidate"].split(" (")[0].split(" ")[0] + ("+90" if "+90" in c["candidate"] else ""): c for c in TR["candidates"]}
    fwd, cgp, aft = cand["forward"], cand["CG"], cand["aft"]
    g0 = 9.80665
    m_w, m_d = ES["wet"]["m_kg"], ES["dry_grain_burnt_out"]["m_kg"]
    I_w = np.array(ES["wet"]["I_about_pivot_kgm2"]); I_d = np.array(ES["dry_grain_burnt_out"]["I_about_pivot_kgm2"])
    Ip = float(max(I_w[0, 0], I_w[1, 1]))
    st = ES["stations_from_pivot_mm"]
    z_exit = st["exit"]
    piv_station = -0.03 - z_exit / 1e3                      # RV-1: nozzle exit at -0.03 m
    # ---------------- TVC geometry (M1 values; CAD v3 refines) ----------------
    r_e, r_h, z_lever, L_rod = 48.0, 8.0, -22.0, 28.0
    phi = [64.5, 154.5]
    n = r_e / r_h
    th7, th8 = math.radians(P["gimbal_range_deg"]["v"]), math.radians(P["gimbal_stop_deg"]["v"])
    psi7 = math.degrees(math.asin(r_e * math.sin(th7) / r_h)); psi8 = math.degrees(math.asin(r_e * math.sin(th8) / r_h))
    # ---------------- hinge moment budget at the CG pivot ----------------
    l_e = abs(ES["wet"]["cg_from_pivot_mm"][2]) / 1e3
    h_in, L_hose = (st["head_top"] + 20.0) / 1e3, 0.26
    x = h_in / L_hose
    Kh = [4 * EI / L_hose * (3 * x * x - 3 * x + 1) for EI in P["hose_EI"]["v"]]
    arm_exit = abs(z_exit) / 1e3
    terms = {
        "inertia_Ipivot_x_gimbal_accel": (Ip * P["gimbal_accel"]["v"], f"I {Ip:.4f} x {P['gimbal_accel']['v']} rad/s2 (gnc.json)"),
        "vehicle_angular_accel_Ipivot_x_omegadot": (Ip * P["omega_dot_max"]["v"], f"I x {P['omega_dot_max']['v']} rad/s2 (gnc.json limit)"),
        "axial_accel_m_a_le_sin7": (m_w * P["a_axial_max"]["v"] * l_e * math.sin(th7), f"l_e {l_e*1e3:.1f} mm (CG offset, wet)"),
        "lateral_accel_m_alat_le": (m_w * P["a_lateral_max"]["v"] * l_e, "1.5 g flight (gnc.json)"),
        "hose_K_x_7deg_upper": (Kh[1] * th7, f"K_hose {Kh[0]:.2f}-{Kh[1]:.2f} N m/rad (EI {P['hose_EI']['v']} N m2 ASSUMED, straight-hose model, L {L_hose} m, inlet {h_in*1e3:.0f} mm above pivot)"),
        "bearing_seal_friction": (0.04, "2 x 608-2RS contact-seal drag ~0.02 N m each (ASSUMED, SKF model class); rolling friction 0.003 N m"),
        "thrust_misalignment": (500 * (0.0005 + arm_exit * math.sin(math.radians(0.25))), "500 N x (0.5 mm + 0.25 deg x pivot-exit arm) ASSUMED tolerances"),
        "nozzle_side_load_floor": (1.3 * arm_exit / 0.2346, "gnc.json v1 1.3 N m (mid pivot) scaled to the pivot-exit arm"),
    }
    Mtot = sum(v for v, _ in terms.values())
    F_rod = Mtot / (r_e / 1e3)
    T_servo = F_rod * r_h / 1e3
    stall = P["tvc_servo_stall"]["v"]; speed = P["tvc_servo_speed"]["v"]
    w_need = P["gimbal_rate_dps"]["v"] * n / math.cos(math.radians(psi7))
    T_at_ext = F_rod * r_h / 1e3 * math.cos(math.radians(psi7))
    kserv = P["tvc_servo_stiffness"]["v"]
    K_ax = [k * n * n for k in kserv]
    f_rigid = [math.sqrt(K / (Ip + ES["ring_alpha_axis_only"]["I_xx"])) / (2 * math.pi) for K in K_ax]
    tank_A = math.pi / 4 * (P["tank_OD"]["v"] - 2 * P["tank_t"]["v"]) ** 2
    L_tank_AD = P["tank_volume"]["v"] / tank_A
    V_hop = P["n2o_load_hop"]["v"] / (0.85 * P["n2o_load"]["v"] / (0.85 * P["tank_volume"]["v"]) * 0.85) if False else P["n2o_load_hop"]["v"] / (P["n2o_load"]["v"] / P["tank_volume"]["v"])
    doc = {
        "id": "mechanical", "version": "v1", "date": "2026-10-12", "owner": "Mechanical (03-cad / 04-fea)",
        "status": ("M1 FIRST PASS. Gimbal architecture decided (pivot at the gimballed CG, Cardan ring, TVC servos on the fixed thrust frame "
                   "beside the gimbal). Engine solids from CAD v2 give the mass properties; gimbal/TVC/feed items added in CAD v3 are itemised "
                   "estimates (+/-30 % each) in this version. v2 replaces them with the CAD v3 ledger and adds FEA modes."),
        "units": "SI (m, kg, s, N, Pa, rad) unless the key says _mm/_deg/_Hz/_g",
        "written_to": "fallback hub /home/claude/work/shared-fallback/engine/interfaces (shared mount I/O errors since ~17:10Z, lead notice)",
        "inputs_read": {"combustion.json": "v1", "electronics.json": "v1", "gnc.json": "v1", "ENGINE-BASELINE-v0.json": "v0"},
        "frames": {
            "engine_frame": "origin = gimbal pivot (intersection of both gimbal axes) at neutral; +Z = engine axis toward the injector (forward); +X = outer gimbal axis (ring pins in the fixed yoke lugs); +Y = inner axis (engine collar pins in the ring); right-handed",
            "pose": "R = Rx(alpha) * Ry(beta): alpha about the fixed X axis (outer), beta about the ring Y axis (inner); thrust direction = R * (0,0,1)",
            "cad": "STEP in mm, +Z forward; GLB in metres, +Y up (glTF)",
            "rv1_station_of_pivot_m": t(round(piv_station, 4), "DERIVED", "RV-1 convention: nozzle exit at z = -0.03 m; z_station = pivot_station + z_engine"),
        },
        "gimbal": {
            "architecture": t("two-axis Cardan gimbal of the whole thrust chamber; split engine collar clamped in a 0.5 mm groove of the case at the pivot plane carries the inner pins (+/-Y); gimbal ring carries the outer pins (+/-X) running in 608-2RS bearings in two fixed yoke lugs on the thrust frame", "DERIVED", "calcs/gimbal_trade.py v1"),
            "pivot_location": t("at the mid-burn CG of the gimballed engine (wet CG 6 mm aft, dry CG 6 mm forward of the pivot)", "DERIVED", "calcs/m1_massprops_estimate.py"),
            "pivot_from_injector_face_m": t(round(st["inj_face"] / 1e3, 4), "DERIVED", "injector face is forward of the pivot"),
            "pivot_from_nozzle_exit_m": t(round(-z_exit / 1e3, 4), "DERIVED"),
            "reason": "pivot trade (calcs/gimbal_trade.py v1, same engine, gnc.json v1 vehicle): the forward (injector-end) pivot gives a tail-wags-dog zero of "
                      f"{fwd['w_twd_touchdown_20 %_rad_s']} rad/s at 20 % thrust against the gnc.json requirement >= {P['twd_min_rad_s']['v']} rad/s, needs ~{fwd['GNC_range_req_deg_interp']} deg of range "
                      f"and a linear hinge-moment sum of {fwd['hinge_total_linear_sum_Nm_EI_hi']} N m (lateral acceleration alone {fwd['hinge_terms_Nm']['lateral_accel_m_alat_le']} N m); "
                      f"the CG pivot gives {cgp['w_twd_touchdown_20 %_rad_s']} rad/s ({cgp['w_twd_touchdown_12.5 %_rad_s']} at 12.5 %), {cgp['GNC_range_req_deg_interp']} deg range need and {cgp['hinge_total_linear_sum_Nm_EI_hi']} N m. "
                      "Cost of the CG pivot: the head (pintle actuator, torch, ports) sweeps the airframe and the actuators need an annulus beside the engine -> engine-bay ID 140 mm instead of 120 (see envelope) and a long feed hose.",
            "trade_table": {k: {kk: c[kk] for kk in ("z_pivot_RV1_station_m", "l_e_m", "I_pivot_kgm2", "w_twd_touchdown_12.5 %_rad_s", "w_twd_touchdown_20 %_rad_s", "w_twd_touchdown_100 %_rad_s",
                                                      "GNC_range_req_deg_interp", "hinge_total_linear_sum_Nm_EI_hi", "required_ID_enclosed_mm", "protrusion_below_120ID_airframe_mm") if kk in c}
                            for k, c in (("forward_injector_end", fwd), ("CG", cgp), ("aft", aft))},
            "trade_tag": "DERIVED calcs/gimbal_trade.py v1 (CAD v2 engine solids; head hardware layout of CAD v2, compacted in v3)",
            "range_deg": t(P["gimbal_range_deg"]["v"], "REQ", "gnc.json v1 / ENG-07", note="commanded limit applies to the VECTOR norm sqrt(alpha^2+beta^2) <= 7 deg (request to GNC)"),
            "mechanical_stop_deg": t(P["gimbal_stop_deg"]["v"], "DERIVED", "conical stop: polyurethane bumper ring in the thrust-frame bore contacts the case 89 mm aft of the pivot"),
            "bearings": t("4 x 608-2RS (8x22x7), C0 1.37 kN, C 3.45 kN per SKF 608-2RSH (verify); pins 8 h6 17-4PH H1150", "DATASHEET", "config bearing_* "),
            "transport_lock": t("split 6061 lock ring pushed into the thrust-frame bore around the case (locks both axes at neutral) + red REMOVE-BEFORE-FLIGHT streamer; servos unpowered; 3 g any axis on the pins", "DERIVED"),
        },
        "gimballed_mass_properties": {
            "about": "pivot, engine frame; includes engine, collar + TVC levers, inner pins, half pushrods/ball studs, pintle actuator + bracket, gimballed hose share, line shares",
            "wet_full_grain": {"m_kg": t(m_w, "DERIVED+ASSUMED", "CAD v2 solids + itemised estimates"), "cg_m": t([round(x / 1e3, 4) for x in ES["wet"]["cg_from_pivot_mm"]], "DERIVED+ASSUMED"),
                               "I_pivot_kgm2": t(np.round(I_w, 5).tolist(), "DERIVED+ASSUMED", "tensor about the pivot, engine axes")},
            "dry_grain_burnt": {"m_kg": t(m_d, "DERIVED+ASSUMED"), "cg_m": t([round(x / 1e3, 4) for x in ES["dry_grain_burnt_out"]["cg_from_pivot_mm"]], "DERIVED+ASSUMED"),
                                "I_pivot_kgm2": t(np.round(I_d, 5).tolist(), "DERIVED+ASSUMED")},
            "ring_alpha_axis_only": {"m_kg": t(round(ES["ring_alpha_axis_only"]["m"], 3), "ASSUMED"), "I_xx_kgm2": t(round(ES["ring_alpha_axis_only"]["I_xx"], 5), "ASSUMED")},
            "grain_mass_kg": t(0.369, "DERIVED", "CAD v2 grain solid at 1000 kg/m3 (combustion.json density ASSUMED)"),
            "uncertainty": "added items +/-30 % (about +/-0.10 kg, +/-0.004 kg m2)",
            "for_gnc_ledger": "fixed propulsion-module items (thrust frame, servos, tank, valves) are listed under fixed_module",
        },
        "tvc_actuation": {
            "concept": t("2 x Savox SB-2292SG (electronics.json) on the fixed thrust frame below the gimbal ring, shafts tangential; aluminium clamp horns r_h; short vertical pushrods with ball links to two levers on the engine collar", "DERIVED"),
            "lever_azimuth_deg": t(phi, "DERIVED", "90 deg apart -> orthogonal, equal authority; between the yoke lugs (0/180) and the inner pins (90/270)"),
            "lever_radius_m": t(r_e / 1e3, "DERIVED"), "lever_ball_z_m": t(z_lever / 1e3, "DERIVED"),
            "horn_radius_m": t(r_h / 1e3, "DERIVED"), "pushrod_length_m": t(L_rod / 1e3, "DERIVED", "ball centre to ball centre"),
            "gear_ratio_n": t(round(n, 3), "DERIVED", "r_e / r_h (electronics.json proposed 7)"),
            "kinematics_linear": "lever-ball vertical displacement dz_i = r_e*(sin(phi_i)*alpha - cos(phi_i)*beta); servo angle psi_i = asin(dz_i / r_h) (rod-tilt correction < 2 % at 7 deg; exact map in calcs/tvc_kinematics.py with CAD v3)",
            "mixing_matrix_dz_per_rad": t(np.round(np.array([[math.sin(math.radians(p)), -math.cos(math.radians(p))] for p in phi]) * r_e / 1e3, 5).tolist(), "DERIVED", "rows servo 1,2; columns alpha, beta; m/rad"),
            "servo_angle_at_7deg_vector_worst_deg": t(round(psi7, 1), "DERIVED", "<= 50 deg operating half-travel (electronics.json 100 deg)"),
            "servo_angle_at_8deg_stop_deg": t(round(psi8, 1), "DERIVED", "<= 65 deg max half-travel (130 deg)"),
            "hinge_moment_terms_Nm": {k: t(round(v, 3), "DERIVED" if k not in ("bearing_seal_friction",) else "ASSUMED", s) for k, (v, s) in terms.items()},
            "hinge_moment_design_Nm": t(round(Mtot, 2), "DERIVED", "linear worst-case sum (gnc.json method), CG pivot"),
            "pushrod_force_design_N": t(round(F_rod, 1), "DERIVED", "|M|/r_e: worst direction loads one pushrod"),
            "servo_torque_design_Nm": t(round(T_servo, 3), "DERIVED"),
            "servo_torque_margin_7V4": t(round(stall["7.4V"] / T_servo, 2), "DERIVED", "stall / design torque"),
            "servo_speed_needed_dps_at_7deg": t(round(w_need, 0), "DERIVED", "60 deg/s engine at the 7 deg extreme (horn at psi7)"),
            "servo_speed_available_dps_7V4": t(round(speed["7.4V"] * (1 - T_at_ext / stall["7.4V"]), 0), "DERIVED", "linear torque-speed model (electronics.json)"),
            "stall_load_on_structure": {"pushrod_N_8V4": t(round(stall["8.4V"] / (r_h / 1e3), 0), "DERIVED"), "engine_moment_Nm_8V4": t(round(stall["8.4V"] / (r_h / 1e3) * r_e / 1e3, 1), "DERIVED")},
            "resolution_deg_engine": t(round(0.1 / n, 4), "DERIVED", "0.1 deg servo deadband (electronics.json ASSUMED)"),
            "backlash_deg_engine": t(round(P["tvc_servo_backlash_deg"]["v"] / n, 4), "DERIVED", "servo 0.2 deg (ASSUMED) / n; ball links preloaded"),
            "axis_stiffness_Nm_per_rad": t([round(k, 0) for k in K_ax], "DERIVED", "k_servo (electronics.json 58-174) x n^2; structure compliance not included"),
            "rocking_mode_Hz_rigid_structure": t([round(f, 1) for f in f_rigid], "DERIVED", f"sqrt(K/I)/2pi vs requirement {P['f_first_mode_min']['v']} Hz; FEA MODAL in v2 adds pushrod/lever/frame compliance"),
        },
        "feed_across_gimbal": {
            "hose": t("-6 PTFE-lined stainless-braided hose (oxygen-cleaned, Krytox only), JIC-37 ends: fixed end at the isolation-valve outlet above the engine, engine end on a JIC 90 deg elbow at the bonnet -6 ORB inlet", "DERIVED"),
            "free_length_m": t(L_hose, "DERIVED"),
            "hinge_stiffness_Nm_per_rad": t([round(k, 2) for k in Kh], "ASSUMED", "EI range 0.05-0.5 N m2 must be bench-measured pressurised; 3-D frame model of the routed hose in v2"),
            "flow_velocity_mps": t(5.8, "DERIVED", "0.227 kg/s liquid N2O in 7.9 mm ID (combustion guideline 5 m/s -> request)"),
            "other_lines_across_gimbal": "1/8 in PTFE Pc sense line (transducer on the fixed side), 1/8 in PTFE N2O and propane torch lines (solenoids fixed side, check valves on the engine), harness for pintle servo/encoder/spark",
        },
        "envelope": {
            "stations_from_pivot_m": {k: t(round(v / 1e3, 4), "DERIVED") for k, v in st.items()},
            "head_stack_top_m": t(round(ES["head_stack_top_from_pivot_mm"] / 1e3, 4), "DERIVED", "pintle servo bracket top (CAD v3 layout)"),
            "overall_gimballed_length_m": t(round((ES["head_stack_top_from_pivot_mm"] - st["aft_bottom"]) / 1e3, 4), "DERIVED"),
            "required_engine_bay_ID_m": t(0.140, "DERIVED", "TBC by the CAD v3 sweep check: TVC servo bodies r 46-66 mm beside the case (fixed), aft closure sweep 67.5 mm if enclosed to the RV-1 base plane, torch 61.6 mm; 3 mm clearance"),
            "engine_bay_zone_m": t([-0.26, 0.24], "DERIVED", "z range (engine frame) where the 140 mm ID is needed; 120 mm is enough above the head stack"),
            "nozzle_exit_below_pivot_m": t(round(-z_exit / 1e3, 4), "DERIVED"),
        },
        "fixed_module": {
            "thrust_frame": t("6061 annular plate below the gimbal (z ~ -0.09 m) with 2 yoke lugs, 2 servo cheeks and the stop bumper; 8 x M5 radial screws into the airframe wall (ICD-AIRFRAME)", "DERIVED"),
            "tank": {"material": "6061-T6 tube 101.6 x 3.175 + 2 bolted bulkheads (24 x M6 radial, 2 FKM O-rings each)",
                     "internal_cyl_length_for_2.06L_m": t(round(L_tank_AD, 3), "DERIVED", "gnc.json v1 2.059 L (1.30 kg at 0.85 liquid fraction, 25 C)"),
                     "internal_cyl_length_for_hop_B_m": t(round(V_hop / tank_A, 3), "DERIVED", "2.35 kg at the same fill density"),
                     "hoop_stress_MEOP_MPa": t(round(7.0e6 * (P['tank_OD']['v'] / 2 - P['tank_t']['v']) / P['tank_t']['v'] / 1e6, 1), "DERIVED", "7.0 MPa MEOP"),
                     },
            "isolation_valve": t("NC full-port ball valve >= 8 mm bore, Cv >= 1.5 (combustion.json) on the tank aft bulkhead outlet, spring-return/latch actuator per electronics.json main_valve; tee to the torch N2O line; trapped-liquid relief <= 7.5 MPa", "REQ"),
        },
        "materials": t(["6061-T6 (case, head, closures, collar, ring, frame, tank)", "17-4PH H1150 (pins, pintle needle/seat, link)", "isomolded graphite (throat)",
                         "paper/glass phenolic (liner, insulators)", "ABS (grain)", "PTFE/FKM/Krytox (seals, lubricant)", "flexible graphite (insert gasket)",
                         "polyurethane 90A (stop bumper)", "steel 12.9 zinc-flake / A4-70 (fasteners)"], "DERIVED", "04-fea/materials/materials_v1.json"),
        "part_list": t({"TC": "01 case, 02 head, 03 seat insert, 04 bonnet, 05 needle, 06 pre-chamber insulator, 07 liner, 08 post-chamber insulator, 09 aft closure, 10 face disc, 11 guide bushing, 12 pintle bracket, 13 pintle servo, 14 crank, 15 link, 16 carriage, 17 guide pin",
                        "NZ": "01 graphite insert, 02 sleeve, 03 gasket", "GR": "01 ABS grain", "IG": "01 torch (combustion envelope), 02 check valves",
                        "GM": "01 collar + levers, 02 inner pins, 03 ring, 04 outer pins, 05 thrust frame, 07 stop bumper, 09 transport lock, 12 ball studs, 13 pushrods, 14 ball links, 15 TVC servos, 16 horns, bearings/clips",
                        "FD": "tank, bulkheads, isolation valve, tee, filter, hose, fittings, relief, fill/vent, lines",
                        "EL": "03/04 gimbal encoders, 05 pintle encoder, Pc/tank/feed transducers, ECU, harness clips", "HW": "O-rings, fasteners", "GS": "test-stand adapter"},
                       "DERIVED", "ENG-<SUB>-<NN>; full BOM in 03-cad/BOM.csv (CAD v3)"),
        "requests": [
            "REQUEST Space/GNC: (1) limit the commanded gimbal VECTOR norm to 7 deg (the 8 deg stop is conical); (2) confirm the CG pivot with these numbers (pivot station %.3f m, l_e within +/-6 mm, I_pivot 0.044-0.047 kg m2) and re-run the TWD/range check; (3) give the limit loads AT the engine mount for landing with the gimbal unlocked." % piv_station,
            "REQUEST Electronics: (1) Pc transducer moves to the fixed side on a 1/8 in sense line (no room on the swept head); (2) pintle servo now stands on the engine axis (body vertical, shaft along +Y, 28 mm link) - confirm the ear plane 11 mm below the spline face; (3) TVC horns r 8 mm (n = 6.0, not 7); servo stiffness 58-174 N m/rad basis and a bench test of it; (4) AS5048A encoders on the outer pin (lug at 180 deg) and inner pin (ring boss at 90 deg).",
            "REQUEST Combustion: (1) the 20 x 70 mm torch envelope standing on the head sets 61.6 mm of sweep radius; a shorter (<= 45 mm) or inward-inclined torch body keeps the head inside 120 mm; (2) Pc tap stays on the head top (sense line); (3) -6 hose at 5.8 m/s vs 5 m/s guideline - accept or ask for -8 (stiffer hose).",
            "REQUEST Airframe (Lauty) via lead: engine-bay ID 140 mm over the gimbal zone (pivot -0.26 m to +0.24 m), thrust-frame 8 x M5 radial screws; details in interfaces/ICD-AIRFRAME.md (to follow with CAD v3).",
        ],
        "open_items": ["CAD v3 (collar, ring, frame, TVC, pintle bracket, feed) replaces all ASSUMED masses (mechanical.json v2)",
                       "hose bending stiffness EI must be bench-measured pressurised (largest hinge-moment uncertainty after inertia)",
                       "FEA MODAL with pushrod/lever/frame compliance against 25 Hz",
                       "thermal FEA: case under the collar, aft closure, O-ring temperatures"],
    }
    Path(out_path).write_text(json.dumps(doc, indent=1, default=float))
    return doc


if __name__ == "__main__":
    d = main(*sys.argv[1:4])
    tv = d["tvc_actuation"]
    print("hinge", tv["hinge_moment_design_Nm"], "\nF", tv["pushrod_force_design_N"], "\nT", tv["servo_torque_design_Nm"], tv["servo_torque_margin_7V4"],
          "\nspeed", tv["servo_speed_needed_dps_at_7deg"], tv["servo_speed_available_dps_7V4"], "\nK", tv["axis_stiffness_Nm_per_rad"], "\nf", tv["rocking_mode_Hz_rigid_structure"],
          "\npsi", tv["servo_angle_at_7deg_vector_worst_deg"], tv["servo_angle_at_8deg_stop_deg"], "\ntank", d["fixed_module"]["tank"], "\nstation", d["frames"]["rv1_station_of_pivot_m"],
          "\nhose K", d["feed_across_gimbal"]["hinge_stiffness_Nm_per_rad"])
    for k, v in tv["hinge_moment_terms_Nm"].items(): print("  ", k, v["v"])
