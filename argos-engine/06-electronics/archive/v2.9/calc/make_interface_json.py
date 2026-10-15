"""Builds interfaces/electronics.json from parts_db.py + results/first_pass_v1.json (+ SIL summary if present).
v1 2026-10-11 (M1). Usage: python make_interface_json.py --version v1 --out ../results/electronics_v1.json
All lengths in envelope blocks are mm (key says _mm); everything else SI unless the key names the unit."""
import json, os, sys, argparse, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_db as P

ap = argparse.ArgumentParser()
ap.add_argument("--version", default="v1")
ap.add_argument("--date", default="2026-10-11")
ap.add_argument("--fp", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "first_pass_v1.json"))
ap.add_argument("--sil", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "sil_summary.json"))
ap.add_argument("--out", required=True)
a = ap.parse_args()
fp = json.load(open(a.fp))
sil = json.load(open(a.sil)) if os.path.exists(a.sil) else None
s = P.SB2292SG
tvc = fp["tvc_actuator"]; pin = fp["pintle_actuator"]; pw = fp["power"]; pc = fp["pc_plant"]
T74 = s["torque_kgcm"]["v"]["7.4"] * P.KGCM_TO_NM
w74 = math.radians(60) / s["speed_s_per_60deg"]["v"]["7.4"]
n = tvc["lever_ratio_proposal"]["v"]

def V(v, tag, **kw):
    d = {"v": v, "tag": tag}; d.update(kw); return d

servo_common = {
    "model": "Savox SB-2292SG", "supplier": "Lindinger (AT) item 9738546, 119.99 EUR incl. VAT (alt: rc-modelshop EE 135 EUR, RC Team FR 129.90 EUR)",
    "type": "rotary HV brushless digital servo, steel gears, aluminium case, PWM 333 Hz, 12-bit",
    "body_LxWxH_mm": V([40.3, 20.2, 38.7], "DATASHEET vendor listing", note="Lindinger table gives H 40.3; reserve 40.3"),
    "envelope_reservation_mm": V([58.0, 22.0, 46.0], "ASSUMED space reservation incl. flanges and horn hub; excludes horn sweep"),
    "mounting_pattern": V("standard-size servo flange, 4 x ~Ø4.5 mm on ~49.5 x 10 mm", "ASSUMED class value - VERIFY on received unit before machining"),
    "output": V("25-tooth spline, 6.0 mm (Futaba-type); use aluminium clamping horn", "DATASHEET Lindinger listing"),
    "mass_kg": V(0.081, "DATASHEET", note="Lindinger table 0.079"),
    "voltage_V": V([6.0, 8.4], "DATASHEET", note="fed directly from 2S LiPo; ARM inhibited below 7.8 V resting"),
    "stall_torque_Nm": V({"6.0V": round(22 * P.KGCM_TO_NM, 3), "7.4V": round(31 * P.KGCM_TO_NM, 3), "8.4V": round(45 * P.KGCM_TO_NM, 3)},
                         "DATASHEET (22/31/45 kg-cm; lower of two conflicting vendor sets)"),
    "noload_speed_dps": V({"6.0V": round(60 / 0.085), "7.4V": round(60 / 0.07), "8.4V": round(60 / 0.055)}, "DATASHEET (0.085/0.07/0.055 s/60deg)"),
    "torque_speed_model": V("linear: T = T_stall*(1 - w/w_noload)", "ASSUMED (not published)"),
    "stall_current_A": V({"6.0V": 7.5, "7.4V": 9.2, "8.4V": round(9.2 * 8.4 / 7.4, 1)}, "DATASHEET 6.0/7.4 V; 8.4 V ASSUMED linear scaling"),
    "idle_current_A": V(0.005, "DATASHEET"),
    "deadband": V({"us": 1.0, "deg_output": 0.10}, "ASSUMED (not published; range 0.5-3 us) - bench measure"),
    "cmd_resolution_deg_output": V(round(1400 / 4096 * 0.1, 4), "DERIVED 12-bit over 800-2200 us, 0.1 deg/us"),
    "backlash_deg_output": V(0.2, "ASSUMED", range=[0.05, 0.5]),
    "op_temp_C": V([-10, 50], "DATASHEET"),
    "update_rate_Hz": V(333, "DATASHEET"),
    "operating_travel_deg": V(100, "DATASHEET (1000-2000 us)"), "max_travel_deg": V(130, "DATASHEET (900-2100 us)"),
}

def tvc_axis(name):
    d = dict(servo_common)
    d.update({
        "function": f"TVC gimbal actuator, axis {name}",
        "mount": "fixed side (thrust structure); pushrod with ball links to gimballed engine",
        "linkage_proposal": V({"lever_ratio_n": n, "servo_horn_radius_mm": 15.0, "engine_arm_radius_mm": 105.0,
                               "horn_angle_at_7deg_deg": round(tvc["servo_horn_travel_deg_for_7deg"], 1),
                               "note": "n = engine-arm/horn; n 6-7.25 optimal (first_pass_v1). n=6 keeps horn within +/-47 deg; Mechanical owns geometry"},
                              "DERIVED first_pass_v1.py"),
        "engine_side_at_n7_7V4": V({"stall_torque_Nm": round(n * 0.9 * T74, 2), "noload_rate_dps": round(math.degrees(w74) / n, 1),
                                    "torque_at_60dps_Nm": round(n * 0.9 * T74 * (1 - math.radians(60) * n / w74), 2)},
                                   "DERIVED (eta_link 0.9 ASSUMED, linear torque-speed ASSUMED)"),
        "hinge_moment_assumed_Nm": V({"peak": round(tvc["M_peak_Nm"], 2), "constant_slew": round(tvc["M_slew_Nm"], 2),
                                      "breakdown": {k: round(v, 3) for k, v in tvc["hinge_moments_Nm"].items()}},
                                     "ASSUMED until mechanical.json (forward pivot, I=0.114 kg m2, conservative linear sum)"),
        "margins_7V4": V({"peak": round(tvc["per_voltage_best"]["7.4"]["margin_peak"], 2), "slew_60dps": round(tvc["per_voltage_best"]["7.4"]["margin_slew"], 2),
                          "at_7V0": {"peak": round(tvc["per_voltage_best"]["7.0"]["margin_peak"], 2), "slew": round(tvc["per_voltage_best"]["7.0"]["margin_slew"], 2)}},
                         "DERIVED first_pass_v1.py; < 1.5 at 7.0 V -> ARM inhibit below 7.8 V"),
        "resolution_deg_engine": V(round(tvc["resolution_deg"]["deadband"], 4), "DERIVED (ASSUMED 1 us deadband / n)"),
        "backlash_deg_engine": V(round(0.2 / n, 3), "DERIVED from ASSUMED 0.2 deg servo backlash; pushrod preload recommended"),
        "stiffness": V({"servo_output_Nm_per_rad": [round(x) for x in tvc["stiffness"]["servo_output_Nm_per_rad"]],
                        "at_engine_Nm_per_rad": [round(x) for x in tvc["stiffness"]["engine_Nm_per_rad"]],
                        "method": "K_out = T_stall/proportional band (1-3 deg ASSUMED); K_eng = eta*n^2*K_out; series linkage compliance NOT included"},
                       "ASSUMED - bench measurement required (torque vs deflection, powered servo)"),
        "dynamics_for_GNC": V({"model": "rate-limited 2nd order + delay + deadband + backlash",
                               "omega_n_rad_s": round(2 * math.pi * 15, 1), "omega_n_range_rad_s": [round(2 * math.pi * 10, 1), round(2 * math.pi * 25, 1)],
                               "zeta": 0.7, "transport_delay_s": 0.0045,
                               "rate_limit_engine_dps_7V4_noload": round(math.degrees(w74) / n, 1),
                               "deadband_deg_engine": round(0.1 / n, 4), "backlash_deg_engine": round(0.2 / n, 3),
                               "bandwidth_small_signal_Hz_estimate": [10, 15]},
                              "ASSUMED (servo internal loop unpublished); delay = 3.0 ms PWM frame + 1.5 ms internal; refine by SIL then bench sweep"),
        "feedback": "independent AS5048A 14-bit magnetic encoder on the gimbal pivot of this axis (not the servo pot)",
    })
    return d

pint_v = pin["per_voltage"]
pintle = dict(servo_common)
pintle.update({
    "function": "throttle actuator driving the variable-area pintle injector (ENG-02 rev 1), rides on the gimballed engine head",
    "mechanism_proposal": V({"type": "rotary servo + crank/slider (or eccentric) on pintle stem", "crank_radius_mm": round(pin["crank_radius_m"]["v"] * 1e3, 2),
                             "crank_swing_deg": [-25, 25], "stroke_mm": 4.0, "note": "Mechanical owns geometry; force direction: N2O pressure should push the pintle CLOSED"},
                            "DERIVED first_pass_v1.py with ASSUMED 4 mm stroke"),
    "force_assumed_N": V({"nominal": 60, "max": 120}, "ASSUMED until combustion.json (lead: tens of N)", range=[20, 150]),
    "full_stroke_time_s": V({k + "V": round(v["t_full_stroke_s"], 3) for k, v in pint_v.items()},
                            "DERIVED (linear torque-speed + 10 ms accel overhead, ASSUMED); requirement <= 0.100 s"),
    "stroke_resolution_um": V({"deadband": round(pin["floor_resolution"]["dx_deadband_m"] * 1e6, 1),
                               "cmd_quant": round(pin["floor_resolution"]["dx_quant_m"] * 1e6, 2)},
                              "DERIVED at the 12.5 % floor (crank angle -18.7 deg)"),
    "thrust_resolution_at_floor_N": V(round(pin["floor_resolution"]["dF_deadband_N"], 2),
                                      "DERIVED with ASSUMED linear pintle area law (first_pass_v1)", note="req: <= 10 N (2 % of 500 N)"),
    "thermal": "servo rated -10..50 C: needs heat shield/standoff from chamber head; bracket thermistor logged",
    "feedback": "AS5048A on crank shaft (14-bit, 0.022 deg/LSB -> ~1.7 um stroke at mid-stroke)",
    "harness": "crosses gimbal in service loop (3 x AWG20 + encoder 4 x AWG26 shielded)",
})

mv = {
    "function": "normally-closed main isolation valve actuator (upstream of flex hose, fixed side)",
    "concept": V("spring-return quarter-turn: torsion spring closes the ball valve; servo cocks it open through a one-way dog; "
                 "a holding electromagnet latches it open; de-energising the latch (disarm, abort, watchdog, power loss) closes it",
                 "DERIVED trade (REPORT 'Main valve'): NC solenoid with >=5 mm port at 70 bar MOPD not found as cheap COTS"),
    "opener_servo": "Savox SB-2292SG (commonality; only loaded ~0.3 s per opening)",
    "latch_coil": V({"voltage_V": "battery 2S (6.6-8.4)", "power_W_max": 4.0, "holding_force_N_min": "2 x spring force at latch radius"},
                    "ASSUMED requirement; part chosen after Mechanical sizes the spring"),
    "close_time_s": V(0.1, "ASSUMED requirement on spring design (Mechanical)"),
    "position_switches": "2 microswitches (OPEN, CLOSED), read by ECU",
    "valve_body": "per combustion.json (full-port 1/4-3/8 in ball valve, PTFE seats, oxygen-clean ASSUMED)",
    "fallback": "servo-direct ball valve + dump/vent NO solenoid + supercap-backed close (not fail-safe by spring)",
}

igniter = {
    "status": "ASSUMED until combustion.json selects the igniter; ECU provides channels for arc, spark-coil or pyro types",
    "IGN_HV": V({"supply": "12.0 V +/-5 % boost rail from ARM bus", "max_current_A": 3.0, "max_power_W": 36,
                 "max_on_time_per_start_s": 2.0, "starts_per_flight": ">= 5 (battery margin x7)",
                 "switch": "low-side ignition IGBT, current-sensed; enable needs ARM bus + 2-key + dynamic (charge-pump) gate",
                 "modes": ["DC enable of an HV arc module (Whitmore/USU type: <=10 kV, ~14.5 mA limit, 2-10 W, 2-5 J/start)",
                           "inductive coil drive: dwell 0.5-5 ms, up to 200 Hz spark rate"],
                 "hv_lead": "silicone 7 mm >= 25 kV lead, own service loop, >= 50 mm from sensor wiring, return to engine star point"},
                "DERIVED capability; arc numbers LITERATURE Whitmore et al. SSC14-X-7 (2014)"),
    "PYRO_1_2": V({"fire_current_A": 2.0, "pulse_s": 0.05, "continuity_sense_A": 0.001, "bridgewire_ohm_ok": [0.5, 5.0],
                   "use": "backup single-shot igniter or e-match for static fire"}, "DERIVED design value"),
    "torch_valves": "2 x NC solenoid low-side drivers (SOL1/SOL2: 2 A, battery voltage) reserved for a torch igniter or flight vent",
}

sensors = {
    "Pc": {"model": "TE M3234-000005-500PG (0-500 psig = 0-34.5 bar, 0.5-4.5 V ratiometric, Packard A, 1/4-18 NPT)",
           "range_Pa": V([0, 3.447e6], "DATASHEET TE M3200 08/2018"), "rise_time_s": V(0.002, "DATASHEET (<2 ms 10-90 %)"),
           "accuracy": V("BFSL 0.25 %FS; TEB 1.5 %FS (-20..85 C); auto-zero before each start", "DATASHEET"),
           "fitting": "1/4-18 NPT male (no O-ring)", "thermal_protection": "1/8 in OD SS standoff tube 150 mm with one coil, at the cool injector end; sensor body < 85 C",
           "sampling_Hz": V(4000, "DESIGN (ADS131M04, decimated to 1 kHz for control/log)"),
           "envelope_reservation_mm": V([30, 30, 80], "ASSUMED reservation incl. mated connector"), "mass_kg": V(0.05, "ASSUMED, weigh")},
    "P_feed": {"model": "TE M3234-000005-01KPG (0-1000 psig = 0-68.9 bar)", "range_Pa": V([0, 6.895e6], "DATASHEET"),
               "location": "injector manifold upstream of pintle (gimballed side; cable crosses gimbal)", "fitting": "1/4-18 NPT male",
               "sampling_Hz": V(4000, "DESIGN"), "envelope_reservation_mm": V([30, 30, 80], "ASSUMED"), "mass_kg": V(0.05, "ASSUMED")},
    "P_tank": {"model": "TE M3234-000005-01KPG (0-68.9 bar)", "range_Pa": V([0, 6.895e6], "DATASHEET"),
               "note": "saturates above 68.9 bar (relief ~75 bar per baseline); over-pressure warning at 65 bar", "fitting": "1/4-18 NPT male",
               "sampling_Hz": V(1000, "DESIGN"), "envelope_reservation_mm": V([30, 30, 80], "ASSUMED"), "mass_kg": V(0.05, "ASSUMED")},
    "T_tank": {"model": "2 x Maxim DS18B20 (wall, under insulation) + optional K-type probe in thermowell", "range_K": V([233, 398], "DATASHEET (to verify)"),
               "rate_Hz": 1, "fitting": "bonded to wall / 1/8 NPT thermowell (Mechanical)"},
    "TC": {"model": "4 x K-type (glass-braid or 1.5 mm MI sheath) via MAX31856 (Adafruit 3263 breakout or on-board)",
           "locations": ["case forward", "case aft", "nozzle holder", "spare (tank/servo bracket)"], "rate_Hz": V(10, "DESIGN"),
           "attachment": "spot-weld or hose-clamp pad (Mechanical)", "range_K": V([73, 1573], "K-type")},
    "gimbal_angle": {"model": "2 x ams AS5048A 14-bit (rev 1-11), SPI, 5 V mode", "resolution_deg": V(0.022, "DATASHEET"),
                     "accuracy_deg": V(1.0, "DATASHEET INL +/-0.8..1.2 deg -> bench-calibrate to <0.1 deg with lookup"),
                     "magnet": V("diametric NdFeB Ø6 x 2.5-3 mm on pivot pin end; air gap 0.5-2.5 mm; lateral misalignment <= 0.25 mm", "DATASHEET AS5048 rev 1-11"),
                     "envelope_reservation_mm": V([25, 25, 10], "ASSUMED sensor PCB + connector"), "rate_Hz": 1000, "supply_A": V(0.015, "DATASHEET")},
    "pintle_position": {"model": "ams AS5048A on crank shaft", "rate_Hz": 1000, "envelope_reservation_mm": V([25, 25, 10], "ASSUMED")},
    "mv_position": {"model": "2 x sealed microswitch (OPEN/CLOSED)", "note": "part chosen with Mechanical"},
    "accel_stability_optional": {"model": "Analog Devices ADXL1002 (analog, +/-50 g) on engine head - optional, TO-VERIFY", "rate_Hz": 4000},
    "load_cell_test_stand": {"model": "1 kN S-type or compression load cell, 2 mV/V (TO-QUOTE)", "adc": "ADS131M04 on ECU ADC2, PGA 64-128, 1-4 kSPS, 24-bit",
                             "note": "HX711 rejected: 10/80 SPS max"},
}

ecu = {
    "architecture": V("separate engine ECU (Teensy 4.1) on the fixed thrust structure, CAN link to flight computer", "DERIVED trade (REPORT Architecture)"),
    "mcu": "PJRC Teensy 4.1 (i.MX RT1062 600 MHz, native SDIO microSD, 3 CAN incl. 1 CAN-FD)",
    "pcb_outline_mm": V([120.0, 60.0, 1.6], "DESIGN v1 (4-layer, hand-solderable)"),
    "mount_holes": V({"dia_mm": 3.2, "screw": "M3", "xy_mm": [[4, 4], [116, 4], [4, 56], [116, 56]], "datum": "PCB lower-left corner, top view"}, "DESIGN v1"),
    "enclosure_envelope_mm": V([128.0, 68.0, 32.0], "DESIGN v1 reservation (PETG or 1 mm Al); +25 mm connector/cable clearance on both long sides"),
    "mass_kg": V(0.16, "ASSUMED (PCB+Teensy+connectors 0.11, enclosure 0.05)", range=[0.12, 0.22]),
    "connector_edges": V({"edge_y0 (long side A)": ["BATT XT60", "ARM plug", "SERVO TVC-A", "SERVO TVC-B", "SERVO PINTLE", "SERVO MV", "MV LATCH", "IGN/PYRO", "SOL1/SOL2"],
                          "edge_y60 (long side B)": ["P_C", "P_FEED", "P_TANK", "TC x4", "ENC x3", "CAN-FC", "CAN-GSE/umbilical", "1-wire T_tank"],
                          "short edge x0": ["Teensy USB (service)", "microSD (service)"]}, "DESIGN v1"),
    "placement_constraints": "fixed (non-gimballed) structure, >= 100 mm from igniter HV lead path, not on the tank wall; keep feed-line axis free",
    "battery": {"type": "LiPo 2S1P 2.2 Ah 25C+ (part TO-QUOTE)", "envelope_reservation_mm": V([110, 36, 20], "ASSUMED"), "mass_kg": V(0.125, "ASSUMED")},
}

loops = {
    "pc_control_Hz": V(1000, "DESIGN"), "pc_adc_Hz": V(4000, "DESIGN"), "tvc_shaping_Hz": V(1000, "DESIGN"),
    "servo_pwm_Hz": V(333, "DATASHEET servo"), "fc_command_Hz": V(500, "DESIGN (>= 500 Hz brief)"),
    "telemetry_fast_Hz": V(500, "DESIGN"), "telemetry_slow_Hz": V(50, "DESIGN"), "sd_log_Hz": V(1000, "DESIGN (+4 kHz raw Pc block)"),
    "safety_monitor_Hz": V(1000, "DESIGN"), "hw_watchdog_timeout_s": V(0.05, "DESIGN"),
    "latency_s": V({"fc_cmd_to_ecu_tick_max": 0.0012, "ecu_to_servo_pwm_max": 0.005, "servo_internal_assumed": 0.0015,
                    "fc_cmd_to_servo_motion_typ": 0.0045, "fc_cmd_to_servo_motion_max": 0.0077,
                    "pc_sensor_to_controller": 0.0023, "ecu_tlm_to_fc_max": 0.0022},
                   "DERIVED budget (CAN 1 Mbit/s 8-byte frame <= 0.135 ms; PWM frame 3 ms; transducer tau 0.9 ms; sinc3+decimation ~1.4 ms)"),
}

can_if = {
    "physical": V("ISO 11898-2 CAN, classic 2.0B 1 Mbit/s, 11-bit IDs; CAN-FD-capable transceivers so FD is a firmware upgrade", "DESIGN"),
    "bus": "2-node point-to-point FC<->ECU, 120 ohm at both ends, twisted pair + GND + shield, <= 2 m",
    "e2e": "every safety frame: 8-bit rolling sequence + CRC-8 (SAE J1850 poly 0x1D) in payload; ARM/IGNITE need key = cmd XOR 0xA5 and confirm within 1 s",
    "frames": {
        "0x010 FC->ECU ABORT": "event (sent 3x); [0xA5 0x5A][abort_code][seq][crc8]",
        "0x020 FC->ECU CMD_FAST 500 Hz": "[seq u8][pc_sp u16 1 kPa/LSB][gimbal_a i16 0.001 deg][gimbal_b i16 0.001 deg][crc8]",
        "0x030 FC->ECU CMD_STATE event+10 Hz": "[seq][cmd u8][arg u16][key u16][crc8]  cmd: ARM, DISARM, PREPRESS, IGNITE, SHUTDOWN, PURGE, SAFE, RELIGHT, SET_POLICY",
        "0x100 ECU->FC TLM_FAST 500 Hz": "[seq][state u8][pc u16 1 kPa][pintle_pos u16 1 um][fault_bits u16]",
        "0x101 ECU->FC TLM_GIMBAL 500 Hz": "[seq][flags][gimbal_a_meas i16][gimbal_b_meas i16][thrust_est u16 0.1 N]",
        "0x110 ECU->FC TLM_SLOW 50 Hz": "[page u8][7 bytes]: p_tank, p_feed, T_tank, TCs, V_bat, I_servo, counters",
        "0x120 ECU->FC EVENT": "[code u8][state u8][t_ms u32][arg u16]: state transitions, abort causes",
    },
    "bus_load": V(0.20, "DERIVED (~1560 frames/s x ~130 bit at 1 Mbit/s)"),
    "flight_computer_side": "any Teensy 4.x CAN1 (pins 22/23) or CAN2 (0/1) + 3.3 V transceiver; CAN-FD only on CAN3",
}

link_loss = {
    "degraded_after_s": V(0.02, "DESIGN: hold last valid Pc setpoint and gimbal angles, flag LINK_DEGRADED"),
    "lost_after_s": V(0.10, "DESIGN"),
    "action_on_lost": {"SAFE/ARMED/PREPRESS": "-> SAFE (main valve closes, igniter disarmed)", "IGNITION": "-> ABORT/SHUTDOWN",
                       "RUN": "default SHUTDOWN (range safety: no unguided powered flight); policy HOLD_N_S selectable by GNC (REQUEST)",
                       "gimbal": "centre at <= 60 deg/s, then hold"},
}

fail_safe = {
    "ECU power loss": "latch drops -> spring closes main valve (<=0.1 s ASSUMED); pintle/TVC servos limp; igniter dead",
    "MCU hang": "hardware watchdog (50 ms) resets MCU and drops ARM bus -> same as above; reboot lands in SAFE, never resumes RUN",
    "link loss": "see link_loss",
    "Pc sensor fault": "RUN: open-loop feed-forward map on P_feed + fault flag; IGNITION: abort",
    "gimbal encoder fault": "flag; RUN: continue on servo commands (default) unless mismatch abort criterion met",
    "arming plug removed": "ARM bus dead: igniter, pintle and main valve power removed regardless of firmware",
}

doc = {
    "id": "electronics", "version": a.version, "date": a.date, "owner": "electronics (06-electronics)",
    "status": "M1 first pass. gnc.json, combustion.json, mechanical.json ABSENT at publication -> their inputs are ASSUMED and tagged. "
              "Simulation and datasheet values are predictions, not hardware validation.",
    "units": "SI unless the key names another unit (mm in *_mm envelopes, deg in *_deg, kg-cm never used in keys)",
    "scripts": ["06-electronics/calc/parts_db.py", "06-electronics/calc/first_pass_v1.py", "06-electronics/calc/make_interface_json.py"],
    "inputs": fp["inputs"],
    "actuators": {"tvc_A": tvc_axis("A (pitch)"), "tvc_B": tvc_axis("B (yaw)"), "pintle_throttle": pintle, "main_valve": mv},
    "igniter": igniter, "sensors": sensors, "ecu": ecu,
    "power_budget": {"battery": "LiPo 2S 2.2 Ah (16.3 Wh), usable 13 Wh", "logic_W": V({k: round(v, 2) for k, v in pw["P_logic_W"].items()}, "DERIVED"),
                     "flight_day_Wh": V(round(pw["E_flight_day_Wh"], 2), "DERIVED (30 min pad hold + 60 s flight + 3 starts)"),
                     "static_fire_session_Wh": V(round(pw["E_static_session_Wh"], 2), "DERIVED"),
                     "peak_current_A": V(round(pw["I_peak_A"], 1), "DERIVED worst case: 3 servos stalled"),
                     "min_voltage_at_ECU_V": V(round(pw["V_min_at_ECU_V"], 2), "DERIVED at 3.5 V/cell OCV, ASSUMED 10 mOhm pack"),
                     "rails": {"VBAT_SERVO": "6.6-8.4 V direct (TVC, pintle, MV opener)", "ARM_BUS": "VBAT via arming plug + watchdog-gated high-side switch",
                               "IGN_12V": "boost 12 V from ARM bus", "5V_LOGIC": "buck from VBAT via ideal diode + 1 mF hold-up", "5V_SNS": "precision LDO for transducers",
                               "3V3": "LDO from 5V_LOGIC"},
                     "fusing": {"main": "25 A mini-blade slow", "logic": "1 A", "IGN": "5 A", "SOL": "3 A"},
                     "ground_power": "umbilical 12 V via ideal-diode OR keeps flight pack full during pad hold (GSE)"},
    "loop_rates_and_latency": loops, "can_interface": can_if, "link_loss": link_loss, "fail_safe_states": fail_safe,
    "harness_across_gimbal": {"bundle": "P_feed (3+shield), Pc (3+shield), pintle servo (3 x AWG20), pintle encoder (4+shield), TC x2-3 (K extension), accel (optional)",
                              "igniter": "separate HV/pyro loop", "service_loop": "route near pivot axis, >= 100 mm free length, bend radius >= 10 x OD, clamp both ends, PTFE/FEP insulation + glass sleeve near chamber"},
    "requests": [
        "combustion.json: pintle stroke, force (pressure + seal friction), speed, area-vs-stroke law, valve->Pc plant; igniter type and electrical need; Pc tap location",
        "mechanical.json: gimballed mass/CG/inertia about pivot, pivot location, actuator lever arms and pushrod geometry, hose stiffness; confirm ECU placement and servo flange pattern",
        "gnc.json: gimbal range, rate, bandwidth, resolution; throttle response/resolution; link-loss policy in RUN; GNC loop rate (CAN command rate 500 Hz assumed)",
    ],
}
if sil:
    doc["sil_summary"] = sil
with open(a.out, "w") as f:
    json.dump(doc, f, indent=1)
print("wrote", a.out, "bytes", os.path.getsize(a.out))
