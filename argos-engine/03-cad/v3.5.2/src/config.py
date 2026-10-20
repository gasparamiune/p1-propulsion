"""Design parameters for the ENG engine CAD/FEA (Mechanical).  SI units (m, kg, s, N, Pa; angles in deg).

Resolution order for every parameter:
  1. a teammate interface file (combustion.json / gnc.json / electronics.json) via the key maps below
     (first matching dotted path wins; values converted to SI)
  2. ENGINE-BASELINE-v0.json (lead seed)
  3. a Mechanical default, tagged DERIVED (hand calc, script named) or ASSUMED (with a range)

`build()` returns (P, log): P[key] = {"v", "tag", "src"}; the log lists every interface override applied and
every key looked for and not found (written by make_all.py to 03-cad/checks/config_resolution.json), so
interface mismatches stay visible instead of being silently filled.
"""
from __future__ import annotations
import json, os
from pathlib import Path

MOUNT_ROOT = Path("/mnt/project-files/engine")
FALLBACK_ROOT = Path("/home/claude/work/shared-fallback/engine")     # lead notice 2026-10-12: mount I/O errors
USE_FALLBACK = os.environ.get("ENGINE_USE_FALLBACK", "1") == "1"      # set 0 when the lead says the mount is back
SHARED_ROOT = FALLBACK_ROOT if USE_FALLBACK else MOUNT_ROOT
INTERFACES = Path(os.environ.get("ENGINE_INTERFACES", str(SHARED_ROOT / "interfaces")))
CONFIG_VERSION = "v3.3"   # v1: baseline-v0 gas path; v2: combustion.json v1 + electronics.json v1 keys; v3.2: lead relays (grain S230, torch, aft section)


# Local snapshot of the shared interfaces (refreshed on every successful read).  The shared folder is a
# network mount that can return I/O errors; when it does, the last good copy is used and the fact is logged
# in LOAD_LOG (written to checks/config_resolution.json by make_all.py).
SNAPSHOT = Path(os.environ.get("ENGINE_IFACE_SNAPSHOT", "/home/claude/work/mechanical/iface_snapshot"))
LOAD_LOG: dict = {}


def _load(name):
    p = INTERFACES / name
    try:
        if p.exists():
            txt = p.read_text()
            d = json.loads(txt)
            try:
                SNAPSHOT.mkdir(parents=True, exist_ok=True)
                (SNAPSHOT / name).write_text(txt)
            except OSError:
                pass
            LOAD_LOG[name] = f"read from {p}"
            return d
        LOAD_LOG[name] = f"absent at {p}"
        return None
    except OSError as e:                       # mount unavailable -> last good snapshot
        q = SNAPSHOT / name
        if q.exists():
            LOAD_LOG[name] = f"MOUNT ERROR ({type(e).__name__}: {e}); used snapshot {q} (mtime {os.path.getmtime(q):.0f})"
            return json.loads(q.read_text())
        LOAD_LOG[name] = f"MOUNT ERROR and no snapshot: {e}"
        return None
    except Exception as e:  # keep going, but record
        LOAD_LOG[name] = f"load error {type(e).__name__}: {e}"
        return {"__load_error__": f"{type(e).__name__}: {e}"}


def shared(path):
    """Readable path for a file on the shared mount: the mount itself when it answers (and the file is then
    mirrored to SNAPSHOT/mirror), else the last mirrored copy.  Logged in LOAD_LOG."""
    path = str(path)
    rel = path.split("/mnt/project-files/", 1)[-1] if "/mnt/project-files/" in path else None
    if rel is None and "/shared-fallback/" in path:              # combustion.json v2 (19:58Z) cites hub paths directly
        rel = path.split("/shared-fallback/", 1)[-1]
    mirror = SNAPSHOT / "mirror" / rel if rel else None
    if USE_FALLBACK and rel is not None:
        fb = FALLBACK_ROOT.parent / rel                         # .../shared-fallback/engine/<...>
        if fb.exists():
            LOAD_LOG[path] = f"fallback hub {fb}"
            return str(fb)
        if mirror is not None and mirror.exists():
            LOAD_LOG[path] = f"fallback hub lacks it; used mirror {mirror}"
            return str(mirror)
        raise FileNotFoundError(f"{path}: not in fallback hub {fb} nor mirror {mirror}")
    try:
        with open(path, "rb") as f:
            data = f.read()
        if mirror is not None:
            try:
                mirror.parent.mkdir(parents=True, exist_ok=True)
                mirror.write_bytes(data)
            except OSError:
                pass
        LOAD_LOG[path] = "read from mount"
        return path
    except OSError as e:
        if mirror is not None and mirror.exists():
            LOAD_LOG[path] = f"MOUNT ERROR ({e}); used mirror {mirror}"
            return str(mirror)
        raise


def _get(d, dotted):
    cur = d
    for k in dotted.split("."):
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        elif isinstance(cur, dict) and isinstance(cur.get("v"), dict) and k in cur["v"]:
            cur = cur["v"][k]          # tagged value whose payload is a dict: {"v": {...}, "tag": ...}
        else:
            return None
    if isinstance(cur, dict) and "v" in cur:
        return cur["v"]
    return cur


MM = 1e-3
# --- interface key maps: param -> list of (dotted path, scale to SI).  Keys verified against
#     combustion.json v1 and electronics.json v1 (2026-10-11).  gnc.json keys are guesses until it exists.
COMB_MAP = {
    "Pc_max": [("operating_points.max_thrust.Pc_Pa", 1.0)],
    "MEOP_chamber": [("operating_points.chamber_MEOP_Pa", 1.0), ("operating_points.pressure_limits.chamber_MEOP_Pa", 1.0)],
    "MEOP_tank": [("operating_points.tank_MEOP_Pa", 1.0)],
    "F_max_sim": [("operating_points.max_thrust.F_N", 1.0)],
    "mdot_ox_max": [("operating_points.max_thrust.mdot_ox_kg_s", 1.0)],
    "mdot_max": [("operating_points.max_thrust.mdot_total_kg_s", 1.0)],
    "Dt": [("gas_path.nozzle.throat_diameter_m", 1.0)],
    "De": [("gas_path.nozzle.exit_diameter_m", 1.0)],
    "eps": [("gas_path.nozzle.expansion_ratio", 1.0)],
    "x_face_throat": [("gas_path.nozzle.x_face_throat_m", 1.0)],
    "x_face_exit": [("gas_path.nozzle.x_face_exit_m", 1.0)],
    "conv_half_angle_deg": [("gas_path.nozzle.convergent_half_angle_deg", 1.0)],
    "div_half_angle_deg": [("gas_path.nozzle.divergent_half_angle_deg", 1.0)],
    "contour_csv": [("gas_path.nozzle.contour_csv", 1.0)],
    "D_chamber_gas": [("gas_path.chamber_inner_diameter_m", 1.0), ("gas_path.chamber_gas_diameter_m", 1.0)],
    "D_pre": [("gas_path.pre_chamber.diameter_m", 1.0)],
    "D_post": [("gas_path.post_chamber.diameter_m", 1.0)],
    "liner_t_comb": [("gas_path.liner.thickness_m", 1.0), ("gas_path.liner_grain_zone.thickness_m", 1.0)],
    "liner_ID": [("gas_path.liner.ID_m", 1.0), ("gas_path.liner_grain_zone.ID_m", 1.0)],
    "D_grain_outer": [("gas_path.grain.outer_diameter_m", 1.0)],
    "L_grain": [("gas_path.grain.length_m", 1.0)],
    "D_port0": [("gas_path.grain.port.initial_diameter_m", 1.0)],
    "port_helix_r": [("gas_path.grain.port.helix_centreline_radius_m", 1.0)],
    "port_helix_pitch": [("gas_path.grain.port.helix_pitch_m", 1.0)],
    "grain_density": [("gas_path.grain.density_kg_m3", 1.0)],
    "grain_mass": [("gas_path.grain.mass_kg", 1.0)],
    "x_grain_start": [("gas_path.grain.x_face_start_m", 1.0)],
    "x_grain_end": [("gas_path.grain.x_face_end_m", 1.0)],
    "L_pre": [("gas_path.pre_chamber.length_m", 1.0)],
    "L_post": [("gas_path.post_chamber.length_m", 1.0)],
    "pintle_seat_d": [("gas_path.injector.seat_diameter_m", 1.0)],
    "pintle_cone_half_deg": [("gas_path.injector.needle_metering_cone_half_angle_deg", 1.0)],
    "pintle_stroke": [("gas_path.injector.stroke_m", 1.0)],
    "pintle_stem_d": [("gas_path.injector.stem_diameter_through_seal_m", 1.0)],
    "manifold_vol_target": [("gas_path.injector.manifold_volume_m3", 1.0)],
    "inj_plate_t": [("gas_path.injector.plate_thickness_m", 1.0)],
    "insert_OD": [("gas_path.graphite_throat_insert_envelope.outer_diameter_m", 1.0)],
    "insert_L_env": [("gas_path.graphite_throat_insert_envelope.length_m", 1.0)],
    "insert_r_start": [("gas_path.graphite_throat_insert_envelope.gas_side_from_radius_m", 1.0)],
    "torch_env": [("gas_path.igniter_port.torch_envelope_outside_chamber_m", 1.0)],
    "pintle_force_env": [("valves_and_actuators.pintle_actuator_requirements.force_pressure_envelope_N", 1.0)],
    "pintle_friction": [("valves_and_actuators.pintle_actuator_requirements.seal_friction_N", 1.0)],
    "pintle_design_force": [("valves_and_actuators.pintle_actuator_requirements.design_force_N", 1.0)],
    "pintle_rated_force": [("valves_and_actuators.pintle_actuator_requirements.actuator_rated_force_N", 1.0)],
    "iso_bore_min": [("valves_and_actuators.isolation_valve_requirements.bore_min_m", 1.0)],
    "iso_Cv_min": [("valves_and_actuators.isolation_valve_requirements.Cv_min", 1.0), ("valves_and_actuators.isolation_valve.Cv_min", 1.0)],
    "thermal_bc_max_csv": [("thermal_and_loads.thermal_bc_csv.max_thrust", 1.0), ("thermal_and_loads.thermal_bc_csv.max", 1.0)],
    "thermal_bc_75_csv": [("thermal_and_loads.thermal_bc_csv.75pct", 1.0)],
    "thermal_bc_50_csv": [("thermal_and_loads.thermal_bc_csv.throttle_50pct", 1.0), ("thermal_and_loads.thermal_bc_csv.50pct", 1.0)],
    "thermal_bc_20_csv": [("thermal_and_loads.thermal_bc_csv.20pct", 1.0)],
    "thermal_bc_floor_csv": [("thermal_and_loads.thermal_bc_csv.floor_12p5pct", 1.0), ("thermal_and_loads.thermal_bc_csv.floor12p5", 1.0)],
    "max_thrust_case_csv": [("thermal_and_loads.max_thrust_case_csv", 1.0)],
    "burn_max_s": [("thermal_and_loads.max_thrust_case_summary.burn_to_liquid_depletion_s", 1.0),
                   ("operating_points.max_thrust_hold_baseline_tank.t_liquid_depletion_s", 1.0)],   # v2: [min, max] list -> max (below)
    "torch_D_v2": [("igniter.envelope.body_max_diameter_m", 1.0)],
    "torch_L_v2": [("igniter.envelope.body_max_length_m", 1.0)],
    "fuel_burnt_max": [("thermal_and_loads.max_thrust_case_summary.fuel_burnt_kg", 1.0)],
    "duty_assumption": [("thermal_and_loads.duty_assumptions", 1.0)],
}
GNC_MAP = {   # gnc.json v1 keys (2026-10-11); g-values converted to m/s2 with g0 = 9.80665
    "gimbal_range_deg": [("requirements.gimbal.range_deg", 1.0)],
    "gimbal_rate_dps": [("requirements.gimbal.rate_min_dps", 1.0)],
    "gimbal_accel": [("requirements.gimbal.angular_accel_min_rad_s2", 1.0)],
    "gimbal_bw_Hz": [("requirements.gimbal.bandwidth_min_Hz", 1.0)],
    "gimbal_resolution_deg": [("requirements.gimbal.resolution_max_deg", 1.0)],
    "gimbal_backlash_max_deg": [("requirements.gimbal.backlash_max_deg", 1.0)],
    "f_first_mode_min": [("requirements.structure.gimballed_engine_first_mode_min_Hz", 1.0)],
    "twd_min_rad_s": [("requirements.structure.tail_wags_dog_zero_min_rad_s", 1.0)],
    "a_axial_max": [("design_limit_loads.axial_accel_flight_g", 9.80665)],
    "a_lateral_max": [("design_limit_loads.lateral_accel_flight_g", 9.80665)],
    "a_lateral_landing": [("design_limit_loads.lateral_accel_landing_g", 9.80665)],
    "omega_dot_max": [("design_limit_loads.body_angular_accel_max_rad_s2", 1.0)],
    "omega_max": [("design_limit_loads.body_angular_rate_max_rad_s", 1.0)],
    "landing_shock_g": [("design_limit_loads.axial_accel_landing_shock_g", 1.0)],
    "transport_g": [("design_limit_loads.transport_handling_g", 1.0)],
    "gimbal_accel_actuator_max": [("design_limit_loads.gimbal_angular_accel_actuator_max_rad_s2", 1.0)],
    "n2o_load": [("requirements.tank.n2o_load_A_D_kg", 1.0)],
    "n2o_load_hop": [("requirements.tank.n2o_load_B_hop100_floor20_kg", 1.0)],
    "tank_volume": [("reference_vehicle.tank_volume_L", 1e-3)],
    "hinge_moment_gnc_mid": [("requirements.gimbal.hinge_moment_design_Nm.mid_pivot", 1.0)],
}
ELEC_MAP = {
    "tvc_servo_body_mm": [("actuators.tvc_A.body_LxWxH_mm", 1.0)],
    "tvc_servo_env_mm": [("actuators.tvc_A.envelope_reservation_mm", 1.0)],
    "tvc_servo_mass": [("actuators.tvc_A.mass_kg", 1.0)],
    "tvc_servo_model": [("actuators.tvc_A.model", 1.0)],
    "tvc_servo_stall": [("actuators.tvc_A.stall_torque_Nm", 1.0)],
    "tvc_servo_speed": [("actuators.tvc_A.noload_speed_dps", 1.0)],
    "tvc_servo_stiffness": [("actuators.tvc_A.stiffness.servo_output_Nm_per_rad", 1.0)],
    "tvc_servo_travel_deg": [("actuators.tvc_A.operating_travel_deg", 1.0)],
    "tvc_servo_maxtravel_deg": [("actuators.tvc_A.max_travel_deg", 1.0)],
    "tvc_servo_backlash_deg": [("actuators.tvc_A.backlash_deg_output", 1.0)],
    "tvc_lever_ratio_proposed": [("actuators.tvc_A.linkage_proposal.lever_ratio_n", 1.0)],
    "pintle_servo_body_mm": [("actuators.pintle_throttle.body_LxWxH_mm", 1.0)],
    "pintle_servo_mass": [("actuators.pintle_throttle.mass_kg", 1.0)],
    "pintle_crank_r_mm": [("actuators.pintle_throttle.mechanism_proposal.crank_radius_mm", 1.0)],
    "pc_sensor_env_mm": [("sensors.Pc.envelope_reservation_mm", 1.0)],
    "pc_sensor_mass": [("sensors.Pc.mass_kg", 1.0)],
    "enc_env_mm": [("sensors.gimbal_angle.envelope_reservation_mm", 1.0)],
    "ecu_env_mm": [("ecu.enclosure_envelope_mm", 1.0)],
    "ecu_mass": [("ecu.mass_kg", 1.0)],
    "batt_env_mm": [("ecu.battery.envelope_reservation_mm", 1.0)],
    "batt_mass": [("ecu.battery.mass_kg", 1.0)],
}


def build():
    base = _load("ENGINE-BASELINE-v0.json") or {}
    comb, gnc, elec = _load("combustion.json"), _load("gnc.json"), _load("electronics.json")
    P, log = {}, {"config_version": CONFIG_VERSION, "files": {}, "overrides": [], "not_found": []}
    for n, d in [("ENGINE-BASELINE-v0.json", base), ("combustion.json", comb), ("gnc.json", gnc), ("electronics.json", elec)]:
        log["files"][n] = None if d is None else {"version": d.get("version"), "date": d.get("date")}

    def put(k, v, tag, src=""):
        P[k] = {"v": v, "tag": tag, "src": src}

    B = lambda path: _get(base, path)
    # ---------------- requirements / loads ----------------
    put("F_max", B("requirements.F_max_SL_N") or 500.0, "REQ", "ENGINE-BASELINE v0 requirements.F_max_SL_N (ENG-01)")
    put("gimbal_range_deg", B("requirements.tvc_range_deg_per_axis") or 7.0, "ASSUMED", "baseline v0 / ENG-07 (Space/GNC finalises)")
    put("gimbal_stop_margin_deg", 1.0, "ASSUMED", "mechanical stop = range + 1 deg (brief: hard stops at +/-(range+margin))")
    put("gimbal_rate_dps", 60.0, "ASSUMED", "ENG-07 slew >= 60 deg/s")
    put("gimbal_accel", 50.0, "ASSUMED", "rad/s2 design value, range 20-60: 60 deg/s reached in 21 ms; 8 Hz x 0.5 deg sine = 22 rad/s2")
    put("f_bw_Hz", 8.0, "ASSUMED", "ENG-07 small-signal bandwidth")
    put("f_first_mode_min", 24.0, "DERIVED", "ENG-11: 3 x 8 Hz (ENG-07 bandwidth); GNC may set a different loop bandwidth")
    put("a_axial_max", 5.0 * 9.80665, "ASSUMED", "m/s2: 500 N / 11 kg landing mass = 4.6 g -> 5 g; replace with gnc.json design limit loads")
    put("a_lateral_max", 0.5 * 9.80665, "ASSUMED", "m/s2: F sin7deg / 13 kg = 0.48 g")
    put("omega_dot_max", 5.0, "ASSUMED", "rad/s2 vehicle angular acceleration (range 2-10)")
    put("r_pivot_vehicle_cg", 0.8, "ASSUMED", "m, gimbal pivot to vehicle CG (2 m vehicle, range 0.6-1.0)")
    put("landing_shock_g", 10.0, "ASSUMED", "g axial at touchdown reaching the engine (legs 3 m/s, 0.05 m stroke ~ 9 g); replace with gnc.json")
    put("transport_g", 3.0, "ASSUMED", "g any direction, handling/transport")
    put("gimbal_bw_Hz", 8.0, "REQ", "ENG-07")
    put("gimbal_resolution_deg", 0.1, "REQ", "ENG-07")
    put("gimbal_backlash_max_deg", 0.1, "ASSUMED", "= resolution")
    put("twd_min_rad_s", 25.0, "ASSUMED", "tail-wags-dog zero >= 3 x attitude crossover (gnc.json sets it)")
    put("a_lateral_landing", 3.0 * 9.80665, "ASSUMED", "m/s2")
    put("omega_max", 1.0, "ASSUMED", "rad/s vehicle body rate")
    put("gimbal_accel_actuator_max", 500.0, "ASSUMED", "rad/s2 actuator-stall transient")
    put("n2o_load_hop", 2.35, "ASSUMED", "kg")
    put("hinge_moment_gnc_mid", 5.0, "ASSUMED", "N m")
    put("misalign_deg", 0.25, "ASSUMED", "thrust vector angular misalignment (range 0.1-0.5)")
    put("misalign_offset", 0.5e-3, "ASSUMED", "m lateral thrust-line offset at the pivot (range 0.2-1.0 mm)")
    # ---------------- pressures / margins ----------------
    put("Pc_max", B("gas_path_v0.Pc_max_Pa") or 2.5e6, "ASSUMED", "baseline v0 gas_path_v0.Pc_max_Pa")
    put("MEOP_chamber", B("pressure_and_margins.chamber_MEOP_Pa") or 3.1e6, "ASSUMED", "baseline v0 (1.25 x Pc max)")
    put("MEOP_tank", B("pressure_and_margins.tank_MEOP_Pa") or 7.0e6, "ASSUMED", "baseline v0 (N2O vapour pressure 35 C + margin)")
    put("relief_set", 7.5e6, "ASSUMED", "baseline v0 note: relief ~7.5 MPa")
    put("P_manifold_max", 7.0e6, "DERIVED", "injector manifold sees tank MEOP when the isolation valve is open and the pintle closed")
    put("mdot_ox_max", 0.2079, "ASSUMED", "baseline v0")
    put("mdot_max", 0.2425, "ASSUMED", "baseline v0")
    for k, d in [("SF_yield", 1.5), ("SF_ult", 2.0), ("proof_factor", 1.5)]:
        put(k, d, "REQ", "ENG-09/ENG-10")
    # ---------------- gas path (baseline v0 until combustion.json) ----------------
    put("Dt", B("gas_path_v0.Dt_m") or 0.01348, "ASSUMED", "baseline v0")
    put("De", B("gas_path_v0.De_m") or 0.02334, "ASSUMED", "baseline v0")
    put("eps", 3.0, "ASSUMED", "baseline v0")
    put("x_face_throat", None, "ASSUMED", "from contour")
    put("x_face_exit", None, "ASSUMED", "from contour")
    put("contour_csv", None, "ASSUMED", "none until combustion.json: conical placeholder")
    put("D_chamber_gas", 0.0539, "ASSUMED", "chamber gas-side diameter")
    put("D_pre", 0.0539, "ASSUMED", "pre-chamber gas-side diameter")
    put("D_post", 0.0539, "ASSUMED", "post-chamber gas-side diameter")
    put("liner_t_comb", 0.0016, "ASSUMED", "phenolic liner")
    put("liner_ID", 0.05395, "ASSUMED", "liner ID")
    put("D_grain_outer", B("grain_v0_placeholder.D_grain_outer_m") or 0.052, "ASSUMED", "baseline v0 placeholder")
    put("D_port0", B("grain_v0_placeholder.Dport0_m") or 0.030, "ASSUMED", "baseline v0 placeholder (single round port)")
    put("port_helix_r", 0.0, "ASSUMED", "straight port")
    put("port_helix_pitch", 0.05, "ASSUMED", "n/a for straight port")
    put("L_grain", B("grain_v0_placeholder.L_grain_m") or 0.354, "ASSUMED", "baseline v0 placeholder")
    put("grain_density", 1050.0, "ASSUMED", "baseline v0 rho_f")
    put("grain_mass", None, "ASSUMED", "from CAD volume")
    put("fuel_burnt_max", 0.166, "DERIVED", "kg fuel burnt in the S230 max-thrust case to liquid depletion (1 % liquid left), 15 C neq tank: "
        "Combustion data/v2/engine_S230_BL/maxthrust_BLtank_neqE1e+03_T15C.csv integrated (20 C 0.162, 25 C 0.157; v1 L200 helix 0.178); "
        "sets the 'mid' (half burnt) state of the CG pivot; flight cycles: A1 0.101 (x1.5 0.148), A2 0.138, B1 0.251 kg (combustion.json v2)")
    put("L_pre", 0.025, "ASSUMED", "pre-combustion chamber length, range 0.02-0.05 m")
    put("L_post", 0.040, "ASSUMED", "post-combustion chamber length, range 0.03-0.06 m")
    put("x_grain_start", None, "ASSUMED", "= L_pre")
    put("x_grain_end", None, "ASSUMED", "= L_pre + L_grain")
    put("conv_half_angle_deg", 30.0, "ASSUMED", "range 25-45 deg until combustion.json contour")
    put("div_half_angle_deg", 15.0, "ASSUMED", "baseline eta_cf 0.975 assumes a 15 deg cone")
    put("rc_up_over_rt", 1.5, "LITERATURE", "Huzel & Huang (NASA SP-125) typical upstream throat radius 1.5 rt")
    put("rc_dn_over_rt", 0.382, "LITERATURE", "Rao/Huzel & Huang downstream throat radius 0.382 rt")
    # v3.3: combustion.json v2 dropped gas_path.graphite_throat_insert_envelope (v1: OD 0.044, L 0.032, graphite from r 0.016) and
    # records 'Mechanical CAD v3.1: 44 mm OD + 30 x 6.5 mm aft spigot ... gas side unchanged' (gas_path.nozzle.insert_envelope_note):
    # the envelope is Mechanical-owned; the v1 values are kept (the v3.3 build first fell back to the 0.032/0.013 placeholders - caught
    # in checks/config_resolution.json not_found and fixed here)
    put("insert_OD", 0.044, "DERIVED", "Mechanical CAD v3.1 insert OD 44 h9 = combustion.json v1 envelope; v2 insert_envelope_note acknowledges it")
    put("insert_L_env", 0.032, "DERIVED", "combustion.json v1 envelope length (r 16 mm to exit + 3 mm); v3.1 adds the 30 x 6.5 aft spigot")
    put("insert_r_start", 0.016, "DERIVED", "graphite from convergent r = 16 mm (combustion.json v1 gas_side_from_radius_m; v2: gas side unchanged)")
    put("torch_env", [0.02, 0.07], "ASSUMED", "igniter torch body diameter, length")
    put("thermal_bc_max_csv", None, "ASSUMED", "none")
    put("thermal_bc_75_csv", None, "ASSUMED", "none")
    put("thermal_bc_50_csv", None, "ASSUMED", "none")
    put("thermal_bc_20_csv", None, "ASSUMED", "none")
    put("torch_D_v2", None, "ASSUMED", "none")
    put("torch_L_v2", None, "ASSUMED", "none")
    put("thermal_bc_floor_csv", None, "ASSUMED", "none")
    put("max_thrust_case_csv", None, "ASSUMED", "none")
    put("burn_max_s", 6.0, "ASSUMED", "max-thrust burn duration")
    put("duty_assumption", "", "ASSUMED", "")
    # ---------------- injector: pintle (ENG-02 rev 1) ----------------
    put("pintle_seat_d", 0.0055, "ASSUMED", "until combustion.json")
    put("pintle_cone_half_deg", 15.0, "INTERFACE combustion.json v1", "v1 needle_metering_cone_half_angle_deg (v2: injector 'unchanged from v1')")
    put("pintle_stem_d", 0.004, "INTERFACE combustion.json v1", "v1 stem_diameter_through_seal_m (v2: injector 'unchanged from v1')")
    put("pintle_stroke", 0.004, "ASSUMED", "4 mm full stroke (range 2-6 mm)")
    put("manifold_vol_target", 3e-6, "INTERFACE combustion.json v1", "v1 manifold_volume_m3 target 3 cm3 (keep <= 5 cm3)")
    put("inj_plate_t", 0.012, "INTERFACE combustion.json v1", "v1 plate_thickness_m first estimate at the seat")
    put("pintle_force_env", [-86.7, 77.2], "INTERFACE combustion.json v1", "N, + closing, at tank MEOP 7.0 MPa, seat 5.5 / stem 4.0 (v2 force_basis_note: "
        "re-check at chamber MEOP 45 bar - the needle force is set by the feed pressure, tank MEOP 7.0 MPa unchanged)")
    put("pintle_friction", 25.0, "INTERFACE combustion.json v1", "N stem seal friction, ASSUMED upper bound (vendor data to confirm)")
    put("pintle_design_force", 115.0, "INTERFACE combustion.json v1", "N = max |pressure| + friction")
    put("pintle_rated_force", 170.0, "INTERFACE combustion.json v1", "N = 1.5 x design")
    put("iso_bore_min", 0.008, "ASSUMED", "m")
    put("iso_Cv_min", 1.5, "ASSUMED", "-")
    put("pintle_servo_body_mm", [40.5, 20.5, 40.0], "ASSUMED", "standard-size servo envelope LxWxH")
    put("pintle_servo_mass", 0.075, "ASSUMED", "kg, standard-size HV servo 55-85 g")
    put("pintle_crank_r_mm", 4.73, "ASSUMED", "crank radius for 4 mm stroke over +/-25 deg")
    put("pintle_guide_note", "17-4PH needle guided in the seat insert bore and the bonnet bushing", "DERIVED", "parts_engine.py")
    # ---------------- case / chamber structure (Mechanical) ----------------
    put("case_OD", 0.0635, "ASSUMED", "baseline v0 case_v0: 6061-T6 2.5 x 0.125 in tube")
    put("case_t", 0.003175, "ASSUMED", "baseline v0 case_v0")
    put("case_bore_seal", 0.05725, "DERIVED", "forward seal land bored to 57.25 H8 to clean up the tube ID (calcs/hand_calcs.py)")
    put("case_aft_land_d", 0.0610, "DERIVED", "aft end turned to 61.0 f7 seal land below the M63x1.5 thread (aft closure is a threaded socket)")
    put("case_aft_thread", "M63x1.5-6g", "DERIVED", "aft closure thread (calcs/hand_calcs.py threaded_closure())")
    put("insert_sleeve_t", 0.002, "ASSUMED", "phenolic sleeve between graphite insert and aluminium holder (range 1.5-3 mm)")
    put("insert_ext_below_exit", 0.003, "DERIVED", "graphite extends 3 mm below the exit plane at the exit diameter (combustion envelope '+3 mm margin'); v3.1: the insert "
        "bottom face is the aft-most face of the engine, flush with the closure lip")
    put("face_insul_t", 0.002, "ASSUMED", "phenolic injector-face insulator disc (range 1.5-3 mm)")
    put("prechamber_lip", 0.002, "DERIVED", "pre/post insulator lips (ID 50 mm, 2 mm high) give the grain an axial seat")
    put("lip_ID", 0.050, "DERIVED", "lip ID 50 mm: 1.75 mm radial seat on the 53.5 mm grain")
    put("z_head_mid", 0.1083, "DERIVED", "head mid-plane above the pivot; build.py iterates it so the pivot sits at the mid-burn CG of the gimballed engine")
    put("collar_groove_depth", 0.0005, "DERIVED", "case OD groove under the engine collar (calcs/hand_calcs.py collar_groove)")
    put("collar_w", 0.020, "DERIVED", "engine collar axial width")
    put("tvc_lever_phi_deg", [135.0, 225.0], "DERIVED", "lever-eye azimuths 90 deg apart (orthogonal, equal authority), clear of the yoke posts (0/180) and the inner-axis ring bosses (90/270); servo 2 = mirror of servo 1 (tvc_kinematics.py)")
    put("tvc_lever_z", -0.028, "DERIVED", "lever eye (pushrod upper bearing) height: eye top 1 mm under the lever arm, arm 1 mm under the ring band at the worst relative pose")
    put("tvc_shaft_z", -0.0703, "DERIVED", "TVC servo shaft height: shaft 10 mm above the body bottom; v3.1: lowered 6 mm from -64.3 so the lever-joint stud flange clears the servo body edge at the 8 deg stop (checks/interference v3.0 failure at stop180)")
    put("tvc_wall_gap_mm", 1.25, "DERIVED", "static radial gap servo-body corner to the engine-bay wall (servo and wall are both fixed); sets u_in so the bottom ear clears the 8 deg case sweep by 2 mm")
    put("tvc_eye_offset_mm", 9.5, "DERIVED", "pushrod eye mid-plane beyond the servo spline face: horn face 5.0 + spacer washer 1.5 + half GE 5 E inner ring 3.0 (v3.1; washers give 2.5 mm eye-face clearance = 16 deg tilt with an 18 mm eye)")
    put("frame_upper_z", [0.022, 0.032], "DERIVED", "upper thrust ring (z range): above the tilted ring bosses and the inner-axis encoder (z <= 17.9 mm)")
    put("pintle_link_L", 0.018, "DERIVED", "pintle crank-slider link length (servo standing on the engine axis)")
    put("engine_bay_ID", 0.140, "DERIVED", "required airframe ID over the gimbal zone (CG pivot; checks/sweep)")
    put("head_h", 0.028, "DERIVED", "forward-closure head height: plug glands below, M14x1 seat-insert bore and 10 mm manifold bore, 1/4 NPT Pc tap depth 12 mm")
    put("head_gap", 0.002, "ASSUMED", "gap head shoulder to case end (tube rests on the head shoulder, unloaded under pressure)")
    put("plug_len_fwd", 0.036, "DERIVED", "2 O-ring glands + bolt row + edge distance (calcs/hand_calcs.py)")
    put("n_bolts_chamber", 8, "DERIVED", "calcs/hand_calcs.py closure_bolts()")
    put("bolt_d_chamber", 0.005, "DERIVED", "M5 radial screws, ISO 7380 button head, A4-70 (calcs/hand_calcs.py)")
    put("bolt_edge_chamber", 0.012, "DERIVED", "bolt row 12 mm from tube end (e/D = 2.4)")
    put("aft_thread_len", 0.014, "DERIVED", "M63x1.5 engagement length (calcs/hand_calcs.py threaded_closure())")
    put("aft_land_len", 0.009, "DERIVED", "aft seal land length (1 AS568-233 gland)")
    put("aft_lip_t", 0.006, "DERIVED", "aft closure retaining lip (v3.1): 6 mm bearing on the insert shoulder; hand_calcs v2 lip trade at MEOP 45 bar / BN 63.1 bar "
        "(upper bound 36/51 MPa, T_allow 235/240 C) - was 4 mm with a 22 mm ID (153 MPa at BN, plume-wetted edge)")
    put("insert_spigot_d", 0.030, "DERIVED", "graphite insert aft spigot 30 h9 through the lip (v3.1): the lip bears on the insert shoulder, ID 30.5 keeps the "
        "aluminium out of the plume and shortens the lip span 13 -> 8.75 mm")
    put("lip_bore_d", 0.0305, "DERIVED", "aft closure lip bore 30.5 H11 around the 30 h9 insert spigot")
    # gimbal
    put("pivot", "mid-burn CG of the gimballed engine", "DERIVED", "calcs/gimbal_trade.py v1 (forward pivot fails the gnc.json tail-wags-dog zero); lead decision 2026-10-12 (provisional)")
    put("pin_d", 0.008, "DERIVED", "8 h6 17-4PH H1150 pins (calcs/hand_calcs.py)")
    put("bearing", "608-2RS", "DATASHEET", "SKF 608-2RSH: d 8, D 22, B 7 mm, C 3.45 kN, C0 1.37 kN, 0.012 kg (verify)")
    put("bearing_D", 0.022, "DATASHEET", "608: D 22 mm")
    put("bearing_B", 0.007, "DATASHEET", "608: B 7 mm")
    put("bearing_C0", 1370.0, "DATASHEET", "SKF 608-2RSH static load rating 1.37 kN (verify)")
    put("bearing_C", 3450.0, "DATASHEET", "SKF 608-2RSH dynamic load rating 3.45 kN (verify)")
    put("ring_r", [0.041, 0.049], "DERIVED", "gimbal ring band radii: collar clamp bosses (r 38.5) clear by >= 1 mm at 8 deg; outer face 1 mm inside the yoke posts")
    put("ring_band_h", 0.014, "DERIVED", "ring band height (+/-7 mm); bosses 27 mm (608 seat 22 K7 + 2.5 mm walls) at +/-Y, 18 mm at +/-X")
    put("collar_r", [0.03125, 0.037], "DERIVED", "engine collar bore (in the 0.5 mm case groove) and OD")
    put("tvc_horn_r", 0.011139, "LEAD-DECISION", "lead 2026-10-12 (Electronics tvc_slew_check_v1: n 6 fails ENG-07 >= 100 deg/s at 7 deg in the worst direction): n = r_e/r_h = 4.80; with the v3 servo position (u_sh 55.63, t_eye 29.65) r_h 11.139 gives r_e 53.47 mm (Electronics assumed r_e 48 / r_h 10); calcs/actuator_loads.py")
    put("tvc_servo_body_mm", [40.5, 20.5, 40.0], "ASSUMED", "standard-size servo envelope until electronics.json")
    put("tvc_servo_env_mm", [58.0, 22.0, 46.0], "ASSUMED", "reservation incl. flanges")
    put("tvc_servo_mass", 0.075, "ASSUMED", "kg, standard-size HV servo 60-85 g")
    put("tvc_servo_model", "standard-size HV servo (ASSUMED)", "ASSUMED", "")
    put("tvc_servo_stall", {"7.4V": 2.5}, "ASSUMED", "N m")
    put("tvc_servo_speed", {"7.4V": 600}, "ASSUMED", "deg/s")
    put("tvc_servo_stiffness", [50.0, 300.0], "ASSUMED", "N*m/rad at servo output (stall torque / position error at stall); range")
    put("tvc_servo_travel_deg", 100.0, "ASSUMED", "operating travel")
    put("tvc_servo_maxtravel_deg", 130.0, "ASSUMED", "max travel")
    put("tvc_servo_backlash_deg", 0.2, "ASSUMED", "deg at servo output")
    put("tvc_lever_ratio_proposed", None, "ASSUMED", "")
    put("pc_sensor_env_mm", [30, 30, 80], "ASSUMED", "transducer reservation")
    put("pc_sensor_mass", 0.05, "ASSUMED", "kg")
    put("enc_env_mm", [25, 25, 10], "ASSUMED", "encoder PCB reservation")
    put("ecu_env_mm", [128.0, 68.0, 32.0], "ASSUMED", "ECU enclosure")
    put("ecu_mass", 0.16, "ASSUMED", "kg")
    put("batt_env_mm", [110, 36, 20], "ASSUMED", "battery")
    put("batt_mass", 0.125, "ASSUMED", "kg")
    put("hose_dash", 6, "DERIVED", "-6 (3/8 in class) PTFE-lined SS-braided hose, ID ~7.9 mm: 5.8 m/s at 0.227 kg/s liquid N2O (combustion guideline 5 m/s, see calcs/feed_line.py)")
    put("hose_ID", 0.0079, "ASSUMED", "m, -6 PTFE smooth-bore ID 7.9 mm (vendor range 7.7-8.1)")
    put("hose_OD", 0.0125, "ASSUMED", "m, -6 PTFE SS-braided hose OD ~12.5 mm (vendor range 11.5-13)")
    put("hose_min_bend_r", 0.064, "ASSUMED", "m; -6 PTFE braided hose min bend radius 50-100 mm by vendor; 64 used until datasheet")
    put("hose_EI", [0.05, 0.5], "ASSUMED", "N*m2 effective bending stiffness of pressurised -6 PTFE hose; range, must be bench-measured")
    put("hose_mass_per_m", 0.13, "ASSUMED", "kg/m, -6 PTFE SS-braided hose 0.10-0.16 kg/m")
    put("airframe_ID", B("reference_vehicle.airframe_ID_m") or 0.120, "ASSUMED", "baseline v0 (to be agreed with Lauty via ICD)")
    put("airframe_clear", 0.003, "ASSUMED", "min radial clearance to airframe ID")
    # tank
    put("tank_OD", 0.1016, "ASSUMED", "baseline v0 tank_v0 (4 in x 0.125 in 6061-T6)")
    put("tank_t", 0.003175, "ASSUMED", "baseline v0")
    put("tank_volume", B("tank_v0.volume_m3") or 2.5e-3, "ASSUMED", "baseline v0 (Combustion owns the tank thermodynamics)")
    put("n2o_load", B("tank_v0.N2O_load_kg") or 1.6, "ASSUMED", "baseline v0")
    put("tank_bore_seal", 0.09535, "DERIVED", "tank seal lands bored to 95.35 H8")
    put("n_bolts_tank", 24, "DERIVED", "calcs/hand_calcs.py tank_bolts(): 2 rows x 12")
    put("bolt_d_tank", 0.006, "DERIVED", "M6 radial, ISO 7380 button head, 12.9 zinc-flake (dry side)")
    put("bulkhead_t", 0.014, "DERIVED", "calcs/hand_calcs.py bulkhead plate")
    put("max_print_height", 0.200, "ASSUMED", "hobby FDM Z height (Prusa MK4 220 mm, Bambu X1 256 mm) -> grain segments <= 200 mm")

    # ---------------- interface overrides ----------------
    def apply(src_name, data, mapping):
        if data is None:
            log["not_found"].append(f"{src_name} absent: {sorted(mapping)}")
            return
        for k, cands in mapping.items():
            for path, sc in cands:
                val = _get(data, path)
                if val is not None:
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        val = val * sc
                    old = P.get(k, {}).get("v")
                    put(k, val, f"INTERFACE {src_name} {data.get('version','?')}", path)
                    log["overrides"].append({"param": k, "from": src_name, "path": path, "old": old, "new": val})
                    break
            else:
                log["not_found"].append(f"{src_name}: {k} (looked for {[c[0] for c in cands]})")

    apply("combustion.json", comb, COMB_MAP)
    apply("gnc.json", gnc, GNC_MAP)
    apply("electronics.json", elec, ELEC_MAP)
    # combustion.json v2 shapes: burn time given as a [min, max] band; torch envelope as two keys
    if isinstance(P["burn_max_s"]["v"], list):
        put("burn_max_s", max(P["burn_max_s"]["v"]), P["burn_max_s"]["tag"], P["burn_max_s"]["src"] + " (max of the band)")
    if P["torch_D_v2"]["v"] and P["torch_L_v2"]["v"]:
        put("torch_env", [P["torch_D_v2"]["v"], P["torch_L_v2"]["v"]], P["torch_D_v2"]["tag"], "igniter.envelope body_max_diameter_m, body_max_length_m")

    # ---------------- lead decisions (applied after the interfaces; a disagreeing interface value is logged) ----------
    def lead(k, v, src):
        old = P.get(k, {})
        if old.get("v") is not None and old.get("v") != v:
            log["overrides"].append({"param": k, "from": "LEAD", "old": old.get("v"), "old_tag": old.get("tag"), "new": v, "why": src})
        put(k, v, "LEAD", src)

    lead("MEOP_chamber", 4.5e6, "lead decision 2026-10-12: chamber MEOP 45 bar from Combustion pintle full-stroke failure case "
         "(data/v2/full_stroke_failure_case_v2.json: 30 C tank, Cd 0.8 -> 44.3 bar v1 helix, 43.5 S260, 42.6 S200); replaces 31 bar (1.25 x Pc max)")
    put("P_blocked_nozzle", 6.308e6, "DERIVED", "blocked-nozzle bound (lead 2026-10-12): chamber at tank pressure = N2O vapour pressure at 30 C, "
        "63.08 bar (Pv_bar in Combustion data/v2/full_stroke_failure_case_v2.json); criterion: stress below yield (SF 1.0) at temperature")
    put("T_tank_bound_C", 30.0, "DERIVED", "tank temperature of the MEOP and blocked-nozzle bounds (same file)")

    # ---------------- lead relays of Combustion v2 (applied only while the published combustion.json is < v2) ----------
    # Lead message 2026-10-12 (grain v2 S230, torch, feed) and lead relay 2026-10-12 (soak-back, post-chamber wall,
    # feed Cv).  Source files mirrored read-only with sha256 in iface_snapshot/mirror/engine/02-combustion/data/
    # PROVENANCE.txt.  When combustion.json v2 is published its values win (apply() above) and these are skipped.
    comb_ver = (comb or {}).get("version") or "v0"
    try:
        comb_major = int(str(comb_ver).lstrip("vV").split(".")[0])
    except ValueError:
        comb_major = 0
    log["relay_active"] = comb_major < 2

    def relay(k, v, src):
        if comb_major >= 2:
            return
        old = P.get(k, {})
        log["overrides"].append({"param": k, "from": "LEAD relay (Combustion v2)", "old": old.get("v"), "old_tag": old.get("tag"), "new": v, "why": src})
        put(k, v, "LEAD-RELAY Combustion v2", src)

    S230 = "lead 2026-10-12 relay of Combustion grain v2 S230 (data/v2/full_stroke_failure_case_v2.json grain 'v2_S230_straight_L230')"
    relay("L_grain", 0.230, S230 + ": length 0.230 m (was 0.200)")
    relay("D_port0", 0.025, S230 + ": straight centred port 25 mm")
    relay("port_helix_r", 0.0, S230 + ": centred straight port (removes the helical roll torque)")
    relay("D_grain_outer", 0.0535, S230 + ": OD 53.5 mm")
    relay("grain_mass", 0.404, S230 + ": mass 0.404 kg")
    relay("L_pre", 0.030, S230 + ": pre-chamber 30 mm unchanged")
    relay("L_post", 0.040, S230 + ": post-chamber 40 mm unchanged")
    relay("x_grain_start", 0.030, S230 + ": grain from x_face 0.030")
    relay("x_grain_end", 0.260, S230 + ": grain to x_face 0.260")
    relay("Dt", 0.01372, S230 + ": throat 13.72 mm unchanged")
    relay("De", 0.01941, S230 + ": exit 19.41 mm unchanged (eps 2.0)")
    relay("contour_csv", "/mnt/project-files/engine/02-combustion/data/v2/nozzle_contour_v2.csv",
          "Combustion nozzle_contour_v2.csv (v1 nozzle shape, all x_face +30 mm; face-to-exit 0.3386 m); mirrored sha256 b00aed4f...")
    relay("x_face_throat", 0.3276652, "nozzle_contour_v2.csv / thermal_bc_summary_v2.json x_face_throat_m")
    relay("x_face_exit", 0.3386180, "nozzle_contour_v2.csv / thermal_bc_summary_v2.json x_face_exit_m (lead: face to exit 0.309 -> 0.339 m)")
    relay("torch_env", [0.020, 0.045], "Combustion ignition_v2.json torch.envelope: body <= 0.045 m long x 0.020 m diameter (lead relay)")
    relay("thermal_bc_max_csv", "/mnt/project-files/engine/02-combustion/data/v2/thermal_bc_max_v2.csv", "Combustion thermal_bc_max_v2.csv (S230, contour +30 mm)")
    relay("thermal_bc_50_csv", "/mnt/project-files/engine/02-combustion/data/v2/thermal_bc_50pct_v2.csv", "Combustion thermal_bc_50pct_v2.csv")
    relay("thermal_bc_floor_csv", "/mnt/project-files/engine/02-combustion/data/v2/thermal_bc_floor12p5_v2.csv", "Combustion thermal_bc_floor12p5_v2.csv")
    relay("iso_Cv_min", 3.0, "lead relay 2026-10-12 (Combustion feed_line_checks_v2.json budget_verdict): isolation valve Cv >= 3 (was 1.5) "
          "keeps the line inside the 2.5 bar budget at 0.25-0.26 kg/s")
    put("filter_rating_um", 15.0, "LEAD", "lead 2026-10-12: feed filter <= 15 um (27 um pintle seat gap at the floor)")
    put("filter_Cv_min", 2.2, "LEAD", "lead relay 2026-10-12 (Combustion feed_line_checks_v2.json): 15 um filter Cv >= 2.2")
    put("pc_sense_line_max_len", 0.30, "LEAD", "lead 2026-10-12: Pc tap on the head top, 1/8 in sense line < 0.3 m")
    put("torch_mass_engine", 0.060, "ASSUMED", "torch body 50 g + plug 10 g on the engine (Combustion ignition_v2.json mass_estimate_kg tag); "
        "solenoids (60-120 g) and the propane cylinder (50 g) on the fixed thrust frame; lines/fittings 50 g split")
    put("torch_mount_combustion", "radial boss on the head section at x_face 0.015 m, axis inclined 30 deg inward/aft", "LEAD-RELAY Combustion v2",
        "ignition_v2.json torch.envelope.mount (lead relay 2026-10-12); Mechanical v3.2 counter-proposal in parts_engine.py (head-top seat, 30 deg outlet)")
    put("insert_heat_B1_kJ", 120.0, "LEAD-RELAY Combustion v2", "graphite insert (0.081 kg) stores ~120 kJ after DC-B1 (soakback_v2.json); bare Al retainer 920 K")

    # ---------------- aft section v3.2 (lead relay 2026-10-12: soak-back + post-chamber wall) ----------------
    # Combustion: 3 mm phenolic on 6061 -> case 557-595 K after A1, 860-905 K B1 bounding; 'liner >= 5 mm in the
    # post-chamber and aft closure, or a steel aft section'.  The aft section screws onto the case's 61.0 mm land, so
    # anything inserted from the forward end is <= 61 mm OD (post-chamber insulator <= 3.5 mm): a 5 mm liner needs an
    # extra bolted joint (README aft-section trade).  v3.2 takes the steel route; the FEA (04-fea LC5) decides.
    put("aft_section_material", "SS316L", "DERIVED", "v3.2 aft section (post-chamber + nozzle holder) in 1.4404; alternatives TI6AL4V (-0.2 kg), "
        "AL6061-T6 (fails Combustion 1-D wall stack); 04-fea/thermal LC5 decides")
    put("aft_bore_d", 0.0610, "DERIVED", "aft-section post-chamber bore = case aft land 61.0 (insulator inserted from the forward end)")
    put("aft_wall_t", 0.0025, "DERIVED", "aft-section barrel wall (316L): hoop 57 MPa at MEOP 45 bar (hand_calcs v3)")
    put("post_insul_min_t", 0.0030, "DERIVED", "minimum post-chamber/convergent insulator thickness over the steel (3.5 mm in the post-chamber)")
    put("insert_sleeve_t", 0.003, "DERIVED", "v3.2: phenolic insert sleeve 3 mm (was 2): soak-back insulation (lead relay 2026-10-12)")
    put("shoulder_gasket_t", 0.0010, "DERIVED", "v3.2: insert-shoulder gasket = 1.0 mm mica/vermiculite ring (was 0.5 mm Grafoil, k ~5 W/m/K through, which "
        "short-circuited the insert to the lip)")
    # ---------------- v3.4.1 (2026-10-13) nozzle joint, sleeve and seat-insert materials (off here = v3.4; on through V34_ON) ----------------
    put("nozzle_joint", "MICA", "DESIGN", "v3.2-v3.4: NZ-03 1.0 mm mica/vermiculite ring on the lip (S14 FAILS: 1595 C vs 900 C class, seal_table_v1); "
        "'J1' = 2.0 mm carbon-phenolic hot layer (NZ-03) + 0.5 mm oxidation-inhibited flexible graphite lip-face seal (NZ-04): lead decision "
        "2026-10-13 on Combustion nozzle_joint_v2p4.json b5f396c7155c06c4 (J2 stabilised zirconia = alternative)")
    put("nz_hot_layer_t", 0.0020, "LEAD", "J1 hot layer (bearing thermal break on the insert shoulder): carbon-phenolic 2.0 mm, Combustion nozzle_joint_v2p4")
    put("nz_seal_t", 0.0005, "LEAD", "J1 lip-face seal: oxidation-inhibited flexible graphite 0.5 mm, Combustion nozzle_joint_v2p4")
    put("nz_mica_t", 0.0005, "SCREEN", "J1b screen only (coordinator 2026-10-13): mica/vermiculite insulating layer 0.5-1.0 mm between the J1 hot layer "
        "and the lip-face seal (nozzle_joint='J1B'); not in the v3.4.1 baseline")
    put("insert_sleeve_material", "PHENOLIC", "DESIGN", "v3.2-v3.4 NZ-02 glass/silica phenolic; v3.4.1 CARBON-PHENOLIC (NZ-02 peaks 1551 C in the B1 p99 soak: "
        "E-glass softens far below that, silica reacts with graphite above ~1500 C; Combustion nozzle_joint_v2p4 side finding, AS RECALLED)")
    put("tc03_material", "SS17-4PH-H1150", "DESIGN", "v3.3/v3.4 seat insert; v3.4.1 IN718 (lead decision 2026-10-13, Combustion v2.4 item 7; tc03_in718_check_v1.json)")

    # ---------------- derived ----------------
    v = lambda k: P[k]["v"]
    ptype = _get(comb, "gas_path.grain.port.type") if comb else None
    if isinstance(ptype, dict):
        ptype = ptype.get("v")
    if isinstance(ptype, str) and ("straight" in ptype.lower() or "centred" in ptype.lower() or "centered" in ptype.lower()) and (v("port_helix_r") or 0) > 0:
        log["overrides"].append({"param": "port_helix_r", "from": "combustion.json port.type", "old": v("port_helix_r"), "new": 0.0, "why": ptype})
        put("port_helix_r", 0.0, "DERIVED", f"combustion.json port.type '{ptype}' (straight port)")
    case_ID = v("case_OD") - 2 * v("case_t")
    put("case_ID", case_ID, "DERIVED", "case_OD - 2 t")
    put("liner_OD", case_ID - 0.00005, "DERIVED", "slip fit in the case ID (57.10 mm)")
    put("liner_t", (case_ID - 0.00005 - v("liner_ID")) / 2, "DERIVED", "(liner OD - liner ID)/2")
    if v("x_grain_start") is None:
        put("x_grain_start", v("L_pre"), "DERIVED", "= L_pre")
    if v("x_grain_end") is None:
        put("x_grain_end", v("L_pre") + v("L_grain"), "DERIVED", "= L_pre + L_grain")
    put("gimbal_stop_deg", v("gimbal_range_deg") + v("gimbal_stop_margin_deg"), "DERIVED", "range + margin (conical stop)")
    if isinstance(v("tvc_servo_body_mm"), list) and len(v("tvc_servo_body_mm")) == 3:
        b = list(v("tvc_servo_body_mm"))
        b[2] = max(b[2], 40.3)  # electronics note: 'Lindinger table gives H 40.3; reserve 40.3'
        put("tvc_servo_box", [x * MM for x in b], "DERIVED", "electronics body LxWxH, H reserved 40.3 mm per electronics note")
    put("pintle_servo_box", [x * MM for x in (v("pintle_servo_body_mm")[:2] + [max(v("pintle_servo_body_mm")[2], 40.3)])],
        "DERIVED", "electronics body LxWxH (H reserved 40.3)")
    # ---------------- CAD v3.4 feature switches (2026-10-13): off = v3.3 geometry (reproduces the v3.3 checks and the stiffness/thermal
    # runs made on it); the v3.4 build (make_all / exports) switches them on through build(overrides=V34_ON)
    put("v34_inlet_e1m", False, "DESIGN", "E1-M oxidiser inlet (calcs/inlet_e1m.py, parts_inlet.py): head filter bore, block, riser, shield")
    put("v34_pintle_hv69", False, "DESIGN", "HV69 in-line pintle stack (calcs/pintle_v2p4.py, parts_pintle.py) with servo mount V3")
    put("v34_feed_o3b", False, "DESIGN", "O3b hose coil + fixed-side feed parts (parts_feed.py)")
    put("pintle_stem_d_v34", 0.003, "DESIGN", "pintle_v2p4: 3 mm stem, M3 into the PD-07 carriage (HV69 drive; combustion.json stem 4 mm is the v3.3 value)")
    put("pintle_stroke_v34", 0.0042, "DESIGN", "pintle_v2p3: crank stop 113.09 deg = 4.2 mm full stroke (HV69 drive)")
    return P, log


# ENG-11 lever/ring stiffening V5c, ACCEPTED 2026-10-13 into the v3.4 baseline: structure + rods >= 3,100 N m/rad (GNC hard minimum)
# at all 9 poses incl. the low chain stiffness (min 3,133 chain-low / 3,239 nominal, beta-7; 04-fea/stiffness/gimbal_k_summary_V5c_v1.json,
# h 3 / hf 4 converged mesh), moving clearance min 0.503 mm at stop000 (runs/stiff/clear/lever_clear_V5c.json), +153 g vs v3.3.
V5C_LEVER = {"cheek_t": 8.0, "cheek_half_u": 7.0, "cheek_below_eye": 7.0, "web": {"rho": [32.5, 38.5, 46.0], "z_bot": -34.0, "half_w": 4.5},
             "cheek_rib": {"u0": 36.0, "t": 6.0}, "arm_chamfer": 3.0, "cheek_ext_lo": 15.0, "cheek_ext_ztop": -14.0,
             "root_flare": {"half_w": 10.0, "r1": 38.5, "z0": -34.0},
             "back_web": {"az_off": 8.1, "t": 6.0, "z_bot": -36.0, "z_top": -14.0, "r_fin": 51.5, "z_fin": 2.0, "r1": 64.0}}
V34_ON = {"v35_bleed": True, "aft_section_material": "IN718",   # v3.5 run 6: bleed modelled; TC-09 IN718 (FA-1 90 bar: 316L yield MS -0.40)
          "v34_inlet_e1m": True, "v34_pintle_hv69": True, "v34_feed_o3b": True,
          "tvc_lever_v34": V5C_LEVER, "ring_band_z": [-7.0, 24.0], "ring_lip": {"z0": 18.0, "r_in": 38.5},
          # v3.4.1 (2026-10-13): TC-06 3.6 mm (lead decision; Combustion v2.4 item 6 accepted D_pre 49.9 mm, L* -3.3 %), TC-03 Inconel 718,
          # nozzle joint J1 and a carbon-phenolic NZ-02 (lead decision 'A1 RELIGHT CONFIGURATION' (6), CHANGELOG 2026-10-13)
          "D_pre": 0.0499, "tc03_material": "IN718", "nozzle_joint": "J1", "insert_sleeve_material": "CARBON-PHENOLIC",
          # v3.4.1 rev B (2026-10-13): TC-09 step-wall fix adds ~34 g at the nozzle end.  The pivot is FROZEN at the v3.4.1 value (mid-burn CG
          # of rev A) so that every station, the feed route and the retained-vapour geometry of the integrated trade stay unchanged; the
          # rev B mid-burn CG sits ~2-3 mm aft of the pivot (reported by make_all mass stage; re-centre at the next CAD version if wanted).
          "z_head_mid": 0.15551342601773104, "pivot_frozen": True}


# v3.5.1 (2026-10-13, Mechanical successor; lead CHANGELOG 182 / 183 / 188): on top of V34_ON
#  - bleed_tap_v351: ENG-BL-02 turned inward (inclined 30 deg, x -39) and BL-03A/E re-routed (REV-MECH-1 RM1-01 BLOCKING; bay sweep r <= 69.0)
#  - gimbal_bearing HK0808: drawn-cup needle bearings (C0r 2.60 kN INA / 2.73 kN Koyo >= 1.80 kN, 182 (2)) on hardened 440C pins
#  - fd11_tab_on_bore: FD-11 P-clip tabs formed to the 140 mm bore (RM1-02: flat tab reached r 71.80)
#  - tvc_lever_v34.root_v351: GM-01/02 lever root = one annular sector + fillets (183 (4), RM1-07; v3.5 LC3 peaks at slivers)
#  - tc03_face TB1 + tc03_material GLIDCOP-AL15: TC-03 flange recessed under the TC-10 insulator, insert in dispersion-strengthened
#    copper (182 (1) head fix; A1 screens: TC-02 119.7 C / TC-03 189.3 C vs BASE IN718 247.9 / 819.5 C; full B1/A1 runs v351_TB1GC)
#  - jfwd_tap_drill_mm 9.0: TC-02 J-FWD taps drilled 4.2 x 9.0 / M5-6H full thread 8.0 so the ISO 7380-1 M5 x 10 A4-80 screw engages
#    6.83 mm (v3.5 6.5 deep: M5 x 10 bottomed, M5 x 8 gave 4.84 mm vs joints.py LE 6.0; RM1-12 hardware census)
# R_side 1.2 on both halves (make_all v3.5.1 run A: GM-01 took R 1.5 -> invalid -> retry R 1.2, and that retry solid failed the STEP
# round-trip (dV/V 1.7e-4, 3.9 mm3) although BRepCheck-valid; a direct R 1.2 passes on both halves (2.8e-8 / 6.4e-9, v351/gm/test_rt_gm01.py))
V5C_LEVER_V351 = dict(V5C_LEVER, root_v351={"half_ang": 16.0, "r_in": 32.5, "r_out": 38.5, "z0": -34.0,
                                             "R_side": 1.2, "R_in": 0.5, "R_od": 1.0, "R_arm": 1.5})
V351_ON = dict(V34_ON, jfwd_tap_drill_mm=9.0, bleed_tap_v351=True, gimbal_bearing="HK0808", fd11_tab_on_bore=True, tvc_lever_v34=V5C_LEVER_V351,
               tc03_face="TB1", tc03_material="GLIDCOP-AL15")


# v3.5.2 (lead CHANGELOG 206 (2), 2026-10-13, Mechanical; conditions in the comments, evidence in 04-fea v352 runs):
#  - (a) TC-09 thinning: barrel radial wall 1.80 mm (v3.5.1 2.47) and socket OD 69.0 above the gland band (v3.5.1 72.0); accepted only if
#        the thermal + S-AX re-run meets 183 (1) with the 194 period domain (not 1/t scaling)
#  - (d) BL-07 pocketing NOT implemented: without the valve sub-base pattern and the P_mid port thread only 1.98 g is free (CALC,
#        v352/checks/bl07_pockets_v1.json; manifold 74.9 g of which pads 60.7 g); re-assessed at valve selection (lead 206 (4))
#  - (b) Ti-6Al-4V screws at non-wetted locations are a hardware-list change (data/hardware_v352.json), not a geometry key
#  - N-F2 (lead CHANGELOG 212, 2026-10-13): NZ-03 bearing load spreader = R 1.0 on the NZ-01 shoulder outer edge (nz01_shoulder_R, m) +
#        a 0.25 mm flexible-graphite foil NZ-06 between the insert shoulder and the J1 hot layer NZ-03 (nz_foil_t, m).  Stack shift: the
#        foil adds 0.25 mm to the J1 stack, the insert shoulder rises 0.25 mm (spigot +0.25, insert body and NZ-02 -0.25); the insert
#        bottom stays flush with the lip bottom and the 2.0 mm hot layer keeps its thickness (Combustion J1 value).  Evidence: v352 thermal +
#        S-AX re-run (tag v352_NF2); NZ-03 stays SHOWN AS FOUND until cleared there or by N-F1 (founder char test).
#  - lever root (lead 2026-10-19 item 1; FEA3D REPORT 4.6 / 9B: GM-01/02 R3 LC3 -0.27/-0.38, F2 GS -0.21/-0.33): tvc_lever_v34.root_v352 =
#        through-band root sector r 33.25..38.5 x a_ch +/- 22 deg from z -34 to the band top (r 37..38.5 = band-OD boss, so the junction at the band
#        bottom spans r 33.25..38.5 instead of 32.5..37.0), inner vertical corners R2.5, ONE junction fillet R1.25 round the footprint (tangent line
#        r 32.0 = 0.25 mm to the case OD, as v3.5.1), boss sides R1.0, arm R1.5; v3.5.1 sharp fillet-to-face edge removed.  Hand calc
#        v352/gm/lever_root_sizing_v1.json: SR 435 -> ~202 MPa cold (MS_u ~+0.34; +0.11 with Kt +15 % and hot x1.05); FEA3D re-checks (F1 LC3 + F2 GS at R3)
#  - J-FWD land (lead CHANGELOG 230 (1), item 11; FEA3D FA1S TC-01 hole -0.221 / -0.160): TC-01 OD 66.9 land from 11 mm aft of the screw axis
#        to the fwd end (30 deg taper), flat spot faces d10.5 so the wall at the 5.5 hole is 4.40 mm (v3.5.1 3.125): stress at the hole x ~0.71
#        (lug / bearing scale 1/t); screws ISO 7380-1 M5 x 12 A4-80 (engagement 7.58 in the 8.0 full thread)
#        -> WITHDRAWN 2026-10-20 by lead CHANGELOG 231 (1) (RM2-01: the -0.221 was a non-converging RBE3 node value; size the joint on SCL Pm /
#        Pm+Pb, joint checks and Neuber at FA1S SF 1.0, fastener before case wall).  v3.5.2 J-FWD = 10x ISO 7380-1 M5 x 10 A4-80 at
#        az 18 + 36k deg (clear of the Pc passage at 142 deg and the torch passage at 0 deg), no spot face, v3.5.1 case wall 3.125:
#        v352/jfwd/jfwd_v352_v1.json min MS +0.077 (screw shear yield on the minor area, 45 C; +0.137 at 20 C)
#  - FD-04 riser shield (fd04_clear_jfwd): the J-FWD screw heads (not modelled) cut the foil top at z 122.8-126 in the frozen v3.5.1 too
#        (v352/checks/probe_heads_v351.py: 1.6 mm3 at 157.5 / 202.5 deg); v3.5.2 foil + upper clip end 1 mm below the head edge
#  - FD-01 +y lower ear relieved round the BL-03E bleed line (clear_interim352: 33.7 mm3), parts_bleed.py, 0.4 mm clearance
#  - J-FD01 (lead item 2; FEA3D F4 -0.41 / -0.20; v3.5.1 lower M3 ran through the FD-01 riser socket and the FD-03 riser): TC-02 flat r 29.5
#        (+/-11.69 wide), FD-01 lower ears +/-13.5, 3x M4 DIN 7984 A4-80 (2 lower at y +/-8.5 / zb+5, x 20; 1 upper at y 0 / zb+24, x 16),
#        1.8 N m (v352/jfd/joints_v352_v1.json: bounding R7 +0.12, groove-OD area +0.25, Phi 0.2 +0.40; nu 0.55 / 0.69)
V5C_LEVER_V352 = dict(V5C_LEVER, root_v352={"half_ang": 22.0, "r_in": 33.25, "r_out": 38.5, "z0": -34.0, "R_v": 2.5, "R_j": 1.25, "R_b": 1.0,
                                             "R_arm": 1.5})
V352_ON = dict(V351_ON, tc09_barrel_wall=0.0018, tc09_socket_R2=0.0345, nz_foil_t=0.00025, nz01_shoulder_R=0.0010,
               tvc_lever_v34=V5C_LEVER_V352, n_bolts_chamber=10, jfwd_ang0_deg=18.0, jfwd_screw_len_mm=10.0, jfd01_v352=True,
               fd04_clear_jfwd=True, jfd09_v352=True)          # jfd09_v352: FD-09 note only (HW-127 A4-80 1.8 N m), no geometry
# J-FWD land (line 230 (1) FA1S option, +21.7 g) WITHDRAWN by lead CHANGELOG 231 (1): kept as a trade key set for the record only
V352_JFWD_LAND_TRADE = dict(jfwd_land_t=0.0044, jfwd_land_od=0.0669, jfwd_land_aft=0.011, jfwd_spot_d=0.0105, jfwd_screw_len_mm=12.0)
V352_TC09_ON = dict(V351_ON, tc09_barrel_wall=0.0018, tc09_socket_R2=0.0345)     # TC-09-only sensitivity (thermal tag v352_TC09, mass file)
V352_NF2_ON = dict(V351_ON, tc09_barrel_wall=0.0018, tc09_socket_R2=0.0345, nz_foil_t=0.00025, nz01_shoulder_R=0.0010)   # 2026-10-13 N-F2 state (test_nf2)

def val(P, k):
    return P[k]["v"]


if __name__ == "__main__":
    P, log = build()
    for k, d in P.items():
        print(f"{k:26s} {str(d['v'])[:44]:46s} {d['tag']}")
    print(json.dumps(log, indent=1)[:3000])
