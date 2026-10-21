// [v2.11 2026-10-13, LEAD CHANGELOG 203/205: Pc chain selector (C1 XTL-190 seat-mounted default, v2.10 070BG line kept), per-sample ADC limit (item 14), ride-through hardware model (switched long RC DELETED 2026-10-20, LEAD 216 (3): fixed RC), stuck-high Pc, FA-1 replay, chamber metrics, windowed CSV]
// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175: photodiode and fault hooks, ECU clock skip; full list in 06-electronics/REPORT-v2.10-HANDBACK.md] ARGOS engine SIL - closed-loop harness: FC command generator -> CAN frames -> ECU core (unchanged flight code)
// -> actuator/plant models -> sensor models -> ECU. 1 kHz ECU tick, plant sub-steps (default 25 us).
// v2.7 (2026-10-13 Combustion review fold-in): torch-pressure transducer (P_torch, flame gate), LTC4365 OV disconnect between the
// pintle rail and the servo (/FAULT gates the MV holding magnet in hardware; servo-side rail sensed by ADC2), HAL emulation of the
// non-volatile NvJamRecord (jam b0, relight lockout b1, lit session b2) across watchdog resets, test-stand flag (load cell),
// unignited-N2O inventory per start, torch N2O-without-propane counter.
// v2.8 (2026-10-13 lead decisions): FC_THRUST frames (FC thrust estimate with bias / latency / noise / stale / invalid injection), coded
// mode strap (stand vs flight), state thermocouples MSS-1/MSS-2, P_feed/P_tank validity, bay temperature, comparator blinded when the Pc
// signal fails (same PC_SIG wire), TLM_RELIGHT frames decoded on the FC side (relight-planning status), MV-P poppet plant (plant.h).
// v2.8 final (2026-10-13, COMB v2.4 / GNC v3 / MECH): NvJamRecord b3 (vapour segment after an abort) across resets, tank-wall
// DS18B20 #1/#2 (plant tank temperature + bias, or an override), MV CLOSED-switch failure and pintle-encoder loss windows, vapour
// volume override (plant.h V_vap), Rec + CSV columns relight_state / seg_vapour / tank_hot / tank_T.
// v2.8.2 (GNC REV-GNC-1 RG-08): pintle-encoder bias window (reads a lift the plant needle does not have).
#pragma once
#include <cstdint>
#include <functional>
#include <random>
#include <string>
#include <vector>
#include "engine_ecu.h"
#include "ovp_hw_params.h"
#include "plant.h"
#include "protocol.h"

namespace sil {

struct SimConfig {
  EngineParams eng;
  ServoParams sv_tvc[2], sv_pintle = ServoParams::hv69(), sv_mv;   // v2.5: pintle = MKS HV69 (LEAD 2026-10-12)
  Gimbal2Params gim2;              // v2.6: 2-axis Cardan gimbal, as-built linkage + FEA structure (mechanical.json v2)
  SenseLineParams sense;           // v2.1: Pc sense line to the fixed-side transducer (mechanical.json v1)
  PintleMechParams pm;
  double dt_plant = 25e-6;
  // sensors (M3200 + ADS131M04): first-order transducer + standoff tube, noise, span/zero errors
  double pc_tau = 0.0009;          // [s] transducer (DATASHEET M3200 < 2 ms 10-90 %); the line is SenseLine
  double pc_fs = ovp::kPcFs_Pa;    // [DATASHEET] v2.6 Pc transducer 070BG 0-70 bar g (v2.2-v2.5 01KPG 68.95e5; v2.1 0-500 psig 34.47e5)
  double pc_noise = 3450.0, pfeed_noise = 3400.0, ptank_noise = 3400.0;   // [Pa rms] ASSUMED ~0.05 % FS (0.049 % of the 070BG 70 bar)
                                   // Pc: rms per 4 kSPS ADC frame; the HAL's 4:1 average halves white noise, so the ECU
                                   //   sees 0.5 x pc_noise = 1725 Pa rms at 1 kHz (sim.cpp); pfeed/ptank: at 1 kHz
  // v2.2 hardware over-pressure trip (U330/U331, values generated from the schematic by calc/ovp_threshold_v1.py)
  double ovp_trip_Pa_g = ovp::kTripPa_g;   // comparator trip (gauge); shift by +/- ovp::kBandPa for tolerance cases
  double ovp_tau = ovp::kTau_s;            // input RC
  // v2.11 (LEAD CHANGELOG 205) Pc measurement chain. pc_chain 0 = the v2.10 chain, kept for the v2.10 comparison arms: TE 070BG 0-70 bar g
  // at the end of the 0.30 m sense line (sense), lag pc_tau, output limit 4.95 V, HAL limit applied AFTER the 4:1 average (the v2.10 SIL
  // model, LEAD 203 (7) item 14 defect kept so v2.10 runs reproduce; pc_clamp_per_sample_v210 = true applies the per-sample limit),
  // comparator ovp:: (gauge trip ovp_trip_Pa_g, ovp_tau). pc_chain 1 (DEFAULT) = the v2.11 flight proposal C1: Kulite XTL-190SM-2000A
  // 0-137.9 bar ABSOLUTE seat-mounted on the head passage (sense_c1), no transducer lag (DATASHEET-class natural frequency >> 10 kHz),
  // INA333 pole + output swing (DATASHEET-derived) feeding the comparator, anti-alias pole on the ADC path (DESIGN), per-ADC-sample limit
  // (item 14) before the 4:1 average, HAL scaling through xdcr::pcFlightCal(101325) (gauge-equivalent reading), comparator ovp3::
  // (ABSOLUTE trip ovp3_trip_Pa_abs, ovp3_tau). The error terms below (span, zero, nl/lin bias, offsets, gain fault) are applied as
  // gauge-equivalent pressure errors in both chains; chain 1 applies them to PC_SIG (comparator and ADC see them, as in hardware).
  int pc_chain = 1;
  SenseLineParams sense_c1 = seatPassage(0.032, 222.0, 6.0);   // CC-2 (passage 30 mm + 2 mm disc), c 222 m/s (MISSING; N2O vapour
                                                               //   200 K bracket end), V_end 6 mm3 [ASSUMED; LEAD 205 bound 20 / 60]
  double pc_fs_abs = ovp3::kPcFsAbs_Pa;                        // [DATASHEET] 2000 psia
  double pc_ina_fc = ovp3::kInaFc_Hz, pc_aaf_fc = ovp3::kAafFc_Hz;   // [DERIVED / DESIGN]
  double pc_vsat = ovp3::kVsat_V, pc_vmin = 0.05;              // [DATASHEET INA333] output swing 50 mV from the rails at 5 V
  double pc_adc_max_V = 1.2 / 0.238215;                        // [DERIVED] ADS131M04 +/-1.2 V FS through the 12.7k/4.02k divider (loaded)
  double ovp3_trip_Pa_abs = ovp3::kTripPaAbs;                  // shift by +/- ovp3::kBandPa for tolerance cases
  double ovp3_tau = ovp3::kTau_s;
  bool pc_clamp_per_sample_v210 = false;
  // v2.11 ride-through (LEAD 216 (3)): the comparator RC is FIXED (no firmware-switched long RC; the v2.11 draft's R334 / TMUX1102 /
  // U335 / U336 model is deleted). The ride-through BOM variant is ovp3_tau = cfg::kRideCmpTauNom_s (C330 2 x 270 nF C0G, 12.83 ms) over
  // the whole burn; cfg::kRideCmpTauMin_s 12.10 ms / kRideCmpTauMax_s 13.55 ms are the tolerance ends.
  // v2.11 hardware both-commanded-open timer (config.h kHbleedHwBoth*, LEAD 166 (3) / 216 (5); DESIGN): V1's drive drops once both
  // bleed drives have been high for hb_both_timer_s since the last rising edge of BOTH (retriggerable), until BOTH falls
  bool hb_both_timer = true; double hb_both_timer_s = ecu::cfg::kHbleedHwBothNom_s;
  int ride_fw = -1;                        // firmware EngineEcu::ride_through: -1 = build default (cfg::kRideThroughBuild), 0 off, 1 on
  double arm_off_delay = 0.006;            // [s] DERIVED estimate: ARM switch turn-off (C301 Miller, bench verify)
  double runaway_us = 2100.0;              // [DATASHEET] servo maximum travel pulse (pintle runaway target)
  double pc_span_err = 0.0, pc_zero_err = 0.2e5;   // span fraction; zero offset [Pa] (removed by auto-zero)
  // v2.9 S9 (LEAD 2026-10-13 residual corners +/-0.3 / +/-0.6 bar) residual shapes that survive the ARM auto-zero, besides pc_nl_bias:
  // constant offset switched on at the first IGNITION entry (pc_off_on_ign) or at pc_off_from (e.g. thermal drift in a burn; the coast
  // re-zero then sees it), and a linear pressure-proportional error pc_lin_bias x (p_g / pc_lin_ref), unclamped
  double pc_off = 0.0, pc_off_from = 1e9; bool pc_off_on_ign = false;
  double pc_lin_bias = 0.0, pc_lin_ref = 1.5e5;
  bool ign_relative = true;                 // v2.9: ECU light rule (false = legacy absolute 3.0 bar rule, comparison only)
  bool coast_rezero = true;                 // v2.9: ECU coast re-zero of Pc / P_torch
  double ptank_bias0_Pa = 0.0;              // v2.10 guard band: constant P_tank reading error from t = 0 [Pa] (hot-corner design point, MC)
  double ttank_wall_bias0_K[2] = {0.0, 0.0};  // v2.10: constant tank-wall DS18B20 reading errors [K]
  bool ptank_cal = true;                    // v2.10 guard band: SIL default = campaign configuration (B-PT-1 record valid);
                                            //   false = uncalibrated threshold 50.34 bar abs (Tsat 19.8 C)
  double pmid_trip_Pa_g = 10.0e5, pmid_rel_Pa_g = 9.0e5;   // v2.9 [DESIGN] P_mid comparator trip / release (gauge), calc/hbleed_provision_v1
  double pmid_noise = 3400.0;               // [ASSUMED] P_mid transducer noise as P_feed (170BG, 0.05 % FS order)
  double ladder_dr = 0.0;                  // v2.10 RE-19 ladder ratio error (leak / resistor drift) [-]
  double ladder_noise = 0.0005;             // v2.10 [ASSUMED] ladder ratio noise (12-bit ADC + divider) [-]
  double pc_nl_bias = 0.0, pc_nl_ref = 1.0e5;      // v2.6 OI-6: error that survives the auto-zero (BFSL/TEB terms at pressure):
                                                   //   + pc_nl_bias * min(1, p_gauge / pc_nl_ref) [Pa] (zero at 0 bar g)
  double enc_lsb = 2.0 * M_PI / 16384.0;          // AS5048A 14-bit
  // power
  double vbat0 = 8.3, R_batt = 0.015, R_lead = 0.020, I_avionics = 0.35;   // [V, ohm, ohm, A] ASSUMED (v2.2: 8.3 V charged
                                                                             // pack; arm permit 8.1 V)
  // v2.5 regulated pintle servo rail (LEAD 2026-10-12; TPS552882 buck-boost, EN from the ARM bus). v2.10 (RE-25): divider as built in
  // KiCad v2.4 (ecu_design.py R808 24.9k / R809 4.75k, 0.1 %): 1.200 V x (1 + 24.9/4.75) = 7.4905 V typ, VREF 1.188-1.212 V DATASHEET
  // (the v2.6 comment "100k/19.1k" and 7.483 V were stale)
  bool pintle_rail = true;                 // false = v2.4 wiring (pintle servo on the 2S bus)
  double rail_V = 7.4905;                  // [DERIVED] typ output from R808/R809 (7.416-7.565 V over VREF; v2.9 SIL used 7.483 V)
  double rail_eta = 0.90;                  // [DERIVED] 0.90-0.92 at 0.4-1.7 A (pintle_rail_v1 loss table)
  double rail_Ilim = 4.0;                  // [DERIVED] output current limit 4.00-4.33 A (lower end)
  double R_lead_pintle = 0.030;            // [ASSUMED] rail -> servo plug (AWG22 ~0.4 m + connector)
  double ibat_noise = 0.02;                // [ASSUMED] A rms, INA181A1 x20 on 2 mOhm + ADC (v2.5: I_bat now fed to the ECU)
  // v2.6 optional pintle rail current sense (INA181 on the TPS552882 output sense resistor) -> stall monitor current path
  bool pintle_isense = true;               // [DESIGN option] on in the SIL so the current path is exercised (worst case for false trips)
  double ipint_noise = 0.02;               // [ASSUMED] A rms
  // v2.6 ENG-07d per-axis notch (REQUIRED for IGNITE/RELIGHT, LEAD 2026-10-12): the HAL keeps an NvGimbalCal record and applies it
  // at boot (also after a watchdog reset). gcal_auto: the record holds the "B-TVC-1 measurement" = the plant's own linearised
  // rocking mode per axis (sil::rockingModeHz) at gcal_V servo voltage, with the config Q / depth; otherwise gcal is stored.
  bool gcal_auto = true;
  double gcal_V = 7.4;                     // servo voltage of the B-TVC-1 measurement (ENG-07 nominal plug)
  ecu::GimbalNotchCal gcal;                // used when gcal_auto = false
  bool nv_gcal_blank = false;              // true: new board, no record (IGNITE refused)
  // v2.7 (2026-10-13 Combustion review fold-in)
  bool test_stand = false;                 // true: load cell wired -> finite Inputs::load_cell_N (ground-only rules); false = flight (NaN)
  double ptorch_tau = 0.0009;              // [s] torch transducer (M3200 070BG, as Pc); torch-body port / standoff NOT modelled (TO-DEFINE)
  double ptorch_noise = 3450.0;            // [Pa rms] ASSUMED as the Pc channel (0.05 % FS of the 070BG)
  bool prail_sense = true;                 // ADC2 rail channels (PRAIL servo side, PREG regulator side) fitted
  double prail_noise = 0.005;              // [V rms] ASSUMED ADC2 + rail divider (KiCad v2.4 values; see ecu_design.py)
  // v2.10 FA-1 photodiode head (ADC2 CH3, replaces the PREG divider; log TIA proposed, part TO-VERIFY). All levels ASSUMED: no datasheet,
  // window geometry or rig data yet (IGN-1 measures them). The ECU thresholds (cfg::kPhoto*) are placeholders of the same status.
  bool photo_fitted = true;                // false: photo_valid false -> FA-1 2oo2 cannot confirm (TORCH_FAULT by design)
  double photo_dark_V = 0.10;              // [ASSUMED] dark output
  double photo_torch_V = 1.0;              // [ASSUMED] added by a lit torch (window views the torch exit)
  double photo_main_V = 2.0;               // [ASSUMED] added by main-chamber combustion when photo_sees_main (FLAMEOUT_OPT view)
  bool photo_sees_main = true;             // false: torch-only view (FLAMEOUT_OPT never arms; FMEA case)
  double photo_spark_V = 0.0;              // [ASSUMED] added while the spark fires (0: no spark light at the head; IGN-1 measures)
  double photo_tau = 0.001;                // [s, ASSUMED] head + TIA response
  double photo_sat_V = 4.95;               // [ASSUMED] output saturation (above cfg::kPhotoMax_V = invalid reading)
  double photo_noise = 0.005;              // [V rms, ASSUMED]
  double ltc_restart_s = 0.036;            // [DATASHEET LTC4365 Rev B: 26/36/49 ms] gate turn-on delay after VIN re-enters the UV/OV window
                                           //   (also at power-up); /FAULT modelled low while the gate is off (conservative for the MV gate)
  double ltc_ov_V = 8.20, ltc_uv_V = 5.0;  // [DESIGN] OV 154k/10.0k (8.06-8.34 V); UV ~5 V (divider TO-DESIGN in KiCad v2.3)
  double rail_tss = 0.004;                 // [DATASHEET TPS552882 tSS 3-5 ms] regulator soft start from ARM-bus on
  double C_servo_side = 10e-6;             // [ASSUMED] capacitance on the servo side of the disconnect FET (local decoupling + servo
                                           //   input; the bulk polymers sit on the regulator side, as pintle_rail_ovtrip_v1 models them)
  double R_bleed_servo = 1000.0;           // [DESIGN v2.3] servo-side bleed: defined decay with an idle servo (56 mW at 7.5 V)
  double I_servo_off = 0.0;                // [ASSUMED worst case for detection] servo draw once its supply is disconnected
  double R_latch = 20.11;                  // [DERIVED calc/mv_latch_magnet_v1] v2.8 MV-P holding magnet: 19.89 ohm coil at 20 C + FET + harness
                                           //   (battery current vbat / R_latch while latched; v2.7: 0.20 A ASSUMED)
  uint32_t seed = 1;
  int record_every_ms = 1;
};
// the auto calibration above (f0 per axis from the plant, Q / depth = firmware defaults)
ecu::GimbalNotchCal autoNotchCal(const SimConfig& c);

struct Rec {
  double t, thr_cmd, F, F_est, Pc, Pc_meas, Pc_sp, x, x_cmd, x_ff, integ, band, ptank, pfeed, mox, mf, of;
  double ga_cmd, ga, gb_cmd, gb, vbat, i_tot, mv, crank_deg, Fnet_pintle, Tservo_pintle, us_pintle, gasT, us_mvop;
  double v_pint, i_pint;   // v2.5 pintle servo plug voltage and current
  double noprog;           // v2.6 stall monitor: time since the last progress mark in the current episode [s]
  double pmid, mdot_hb, mvap_hb, ign_ref, ign_rise, flame_ratio, pc_map;   // v2.9: plant P_mid [Pa abs], bleed flows [kg/s], light-rule
  int hb_io, ign_det, a7;                                                  //   P0 / rise [Pa g], A3 ratio, A3 map [Pa abs]; bleed io bits,
                                                                           //   det:: flags, A7 phase + 4 x flag + 8 x event
  double ptorch, ptorch_in, prail, preg, mvap, vap_cc, ox_unlit;   // v2.7: plant P_torch [Pa abs]; ECU torch input [Pa g]; servo-side and
                                                                     //   regulator rail [V]; vapour flow [kg/s]; vapour left [cm3]; this
                                                                     //   start's unignited N2O so far [kg]
  int sol2, mv_latch_hw, ltc_gate, torch_ok, lockout, seat_wait;   // v2.7
  double ign_check;        // v2.8: ignition window W of the current start [s from the lift command] (v2.7: deadline from IGNITION entry)
  int relight_ext, torch_closed;
  int ign_rule, relight_direct, s1_fault, seg_primed, seg_valid, relight_block, mode_stand;   // v2.8
  int rstate, segvap, tank_hot;    // v2.8 final: segstate::, vapour segment after an abort, tank interlock condition
  double tank_T;                   // v2.8 final: interlock tank temperature [K]
  double ign_lift_t, relight_worst, fc_thr, s1_dp;                                         // v2.8 [s, s, FC estimate fresh 1/0, Pa]
  double Pc_xdcr;          // v2.6 OI-6: absolute pressure at the transducer diaphragm (after the sense line, before the
                           //   output clip) [Pa]
  int state, abort, faults, torch, ignited, spark, sol1, ceiling, sol4, sol5, arm_bus, ovp_ok, jam_kind;
  int pc_valid, ls_flags;  // v2.10: Outputs::pc_valid (TLM 0xFFFF marker when 0); LIGHT_SPIKE b0 open b1 done b2 lit b3 event b4 exit
  double mpool;            // v2.10: plant pool-burn evaporation [kg/s]
  double photo_V;          // v2.10 FA-1: photodiode input to the ECU [V]
  int fa1, fault2, hbleed2, purge_flow_ms;   // v2.10 Outputs: fa1:: flags, f2:: flags, hb2:: flags, achieved purge flow [ms] (65535 = none)
  double pc_raw_V, ovp_vf, Pc_face;            // v2.11: Inputs::pc_raw_V; comparator node [V at PC_SIG]; pressure at the diaphragm [Pa abs]
  int ovr_flags, cmd_refused;    // v2.11: Outputs::ovr_flags (ovr::); refuse:: code
};

struct StateCmd { double t; ecu::Cmd cmd; uint16_t arg; };

class Sim {
 public:
  explicit Sim(const SimConfig& c);
  // FC side
  std::function<double(double)> thrust_cmd = [](double) { return 0.0; };
  std::function<void(double, float*)> gimbal_cmd = [](double, float* g) { g[0] = g[1] = 0; };
  std::function<uint8_t(double)> roll_cmd = [](double) { return static_cast<uint8_t>(0); };   // CMD_AUX bits, sent at 100 Hz (explicit zeros close the valves; the 50 ms dead-man covers a lost link)
  std::vector<StateCmd> schedule;
  bool link_up = true;
  double link_down_from = 1e9, link_down_to = 1e9;
  // fault injection
  double hang_at = 1e9;               // ECU stops stepping (watchdog then resets it after 50 ms)
  double arm_plug_pull_at = 1e9;
  double pc_sensor_fail_at = 1e9;
  double tc_hot_at = 1e9; int tc_hot_idx = 0; double tc_hot_K = 450.0;
  double tc_invalid_at[2] = {1e9, 1e9};   // v2.10 RE-08: case TC k reads invalid (open TC / MAX31855 fault) from this time
  double ptank_bias_at = 1e9; double ptank_bias = 0.0;
  double vbat_drop_at = 1e9; double vbat_drop = 0.0;
  double pintle_jam_at = 1e9;         // pintle servo output locks
  double pintle_unpower_at = 1e9;     // pintle servo loses drive (back-driven by spring)
  double tvc_jam_at = 1e9;            // TVC A output locks
  double pintle_runaway_at = 1e9;     // v2.2: pintle servo drives to full travel regardless of command (needs power)
  bool fw_ovp_disabled = false;       // v2.2: firmware over-pressure check off (SIL hook) -> hardware trip alone
  bool force_fast_prime = false;      // v2.2: v2.1 priming sequence (no bleed, fast MV) for comparison (SIL hook)
  bool pintle_mon_disabled = false;   // v2.6: firmware pintle stall monitor off (SIL hook) -> hardware over-pressure trip alone
  // v2.6 OI-6: additive Pc disturbance on the 1 kHz decimated sample and the PC_SIG voltage (spark EMI / ground shift):
  // pc_spike_Pa during pc_spike_len from pc_spike_at, repeated every pc_spike_period (0 = once) until pc_spike_end
  double pc_spike_at = 1e9, pc_spike_Pa = 0.0, pc_spike_len = 0.001, pc_spike_period = 0.0, pc_spike_end = 1e9;
  double crc_corrupt_rate = 0.0;      // probability per frame of a random bit flip (CAN CRC assumed bypassed)
  bool tvc_test = false;
  // v2.7 generic timed hooks (scenario actions at a time: plant failures, sensor values ...), run at the start of the tick
  struct Hook { double t; std::function<void(Sim&)> f; bool done = false; };
  std::vector<Hook> hooks;
  // v2.7 fault injection
  double ptorch_fail_at = 1e9;        // torch transducer reading invalid (open wire / ADC2 range check) from this time
  double photo_fail_at = 1e9;         // v2.10 photodiode reading invalid from this time
  double photo_dark_from = 1e9;       // v2.10 photodiode reads dark (e.g. sooted window) from this time while still valid
  double prail_ov_at = 1e9, prail_ov_len = 0.0005;   // regulator-side rail above the OV trip for prail_ov_len (a transient, e.g. a
                                                    //   load-release overshoot beyond the analysis); the LTC4365 then restarts
  double preg_fail_at = 1e9, preg_fail_V = 8.6;      // regulator fails high (FB open) and stays at preg_fail_V [ASSUMED level]
  // v2.8 FC thrust estimate (FC_THRUST 0x024 at 100 Hz): stale (no frames) or invalid (flag b0 = 0) from the given times.
  // v2.8.1 (LEAD 2026-10-13 ADOPTED, GNC m2_fc_thrust v1.1): first-order low-pass tau fc_thr_tau = 20 ms on the plant thrust (1 kHz,
  // exact discretisation), x (1 + bias), + noise, sampled at the frame instant; fc_thr_lat = an extra pure delay standing for the IMU
  // internal filter + sample delay and the FC scheduling, which are UNKNOWN (ADIS16470 datasheet not read): 0 by default, 10 ms
  // [ASSUMED] in the sensitivity case. fc_thr_tau <= 0 gives the v2.8 model (pure delay fc_thr_lat, v2.8 used 20 ms).
  bool fc_thr_on = true;
  double fc_thr_bias = 0.0, fc_thr_lat = 0.0, fc_thr_noise = 5.0, fc_thr_tau = 0.020;   // fraction, s, N rms [ASSUMED], s [LEAD]
  // v2.8.1 in-range wrong Pc: transducer gain fault (reads pc_gain x the true gauge pressure, e.g. a ratiometric excitation / reference
  // error) on the single PC_SIG signal from pc_gain_at: firmware sample AND hardware comparator see it (same wire)
  double pc_gain_at = 1e9, pc_gain = 1.0;
  // v2.11 S6R: PC_SIG stuck high (conditioner output at its rail: shorted input / failed amplifier) from this time; firmware AND comparator
  double pc_stuck_high_at = 1e9, pc_stuck_high_to = 1e18;   // v2.11: [at, to) in plant time (a glitch when 'to' is set; R2-23 S17 evidence).
                                                             //   C1: the conditioner output is at its rail (ADC samples + comparator tap)
  // v2.11 S9R FA-1 replay: the chamber pressure seen by the Pc chain (and recorded as Rec::Pc, metrics below) is max(plant Pc, p_amb +
  // fa1_scale x (h(t - fa1_t0) - p_amb)) for the 25 ms history h [bar abs, 0.1 ms grid], from the first plant light at or after fa1_after
  std::vector<double> fa1_hist; double fa1_scale = 1.0, fa1_after = 1e9, fa1_t0 = -1;
  // v2.11 chamber metrics at the plant step (25 us) from ch_from: peak, time above 45 / 30 bar abs
  double ch_from = 1e9, ch_pk = 0, ch_t45 = 0, ch_t30 = 0;
  // v2.11 S6R genuine over-pressure (LEAD 216 (3), Mechanical lc_tb70_envelope_v1): from the trigger gop_t0 the head pressure seen by the Pc
  // chain is max(plant / replay Pc, p_amb + (gop(tau, p0) - p_amb) x ff), tau = t - gop_t0, p0 = the head pressure at the trigger. ff = 1 until
  // the first ECU ABORT / SAFE or ARM-bus loss after the trigger, then the plant injector-flow ratio (mox + mvap) / (that at the abort),
  // clamped to [0, 1] [ASSUMED: the event's excess head pressure decays with the plant's own post-abort flow; no feedback of the event on the
  // plant flow]. Trigger: gop_trig 1 = first plant light at or after gop_after, + gop_dt; 2 = first ECU RUN entry (E2) at or after gop_after,
  // + gop_dt. Envelope metrics at the plant step (25 us) from the trigger; trace (25 us to 50 ms, then 0.1 ms, to 0.6 s) for the rise check
  std::function<double(double, double)> gop;
  int gop_trig = 0; double gop_after = 1e9, gop_dt = 0.0;
  double gop_t0 = -1, gop_p0 = -1, gop_t_ab = -1, gop_mox_ab = 0, gop_p_ab = 0, gop_pf_ab = 0;
  double env_pk = 0, env_t45a = -1, env_t45b = -1, env_t63a = -1, env_t63b = -1, env_t45 = 0, env_t581 = 0, env_t60 = 0, env_t631 = 0;
  std::vector<float> gtr_t, gtr_p;
  double fc_thr_stale_from = 1e9, fc_thr_invalid_from = 1e9;
  // v2.8 sensors / harness (hooks may change them during a run)
  int strap_override = -1;            // -1: strap from C.test_stand (2 stand, 1 flight); else the raw decoded value (0 invalid)
  double tc_mss1_K = 293.15, tc_mss2_K = 293.15;   // MSS-1 inlet block, MSS-2 NC-valve outlet (Type T)
  bool mss1_valid = true, mss2_valid = true, pfeed_valid = true, ptank_valid = true;
  double bay_K = 293.15; bool bay_valid = true;    // bay temperature (DS18B20 #3)
  // v2.8 final tank-wall DS18B20 #1/#2: read the plant tank temperature + bias (ASSUMED wall = bulk), or a fixed override when > 0
  double ttank_wall_bias_K[2] = {0.0, 0.0}; double ttank_wall_override_K = -1.0; bool ttank_wall_valid[2] = {true, true};
  double mv_open_sw_fail_from = 1e9;  // MV OPEN switch reads not-made from this time (switch / cam-follower fault; valve unaffected)
  double mv_closed_sw_fail_from = 1e9;   // v2.8 final: MV CLOSED switch reads not-made from this time (switch fault; valve unaffected)
  double enc_fail_from = 1e9, enc_fail_to = 1e9;   // v2.8 final: pintle encoder invalid in [from, to) (AS5048A fault / magnet)
  double enc_bias_from = 1e9, enc_bias_to = 1e9, enc_bias_m = 0.0;   // v2.8.2 RG-08: pintle encoder lift reads + enc_bias_m in [from, to)
  // v2.9 head-end bleed fault injection: valve k stuck open / failed closed from these times; P_mid comparator stuck low (chain dead);
  // ladder code invalid from this time. The valves are driven from +12V_ARM (J508/J509): commanded open only with the ARM bus on
  double hb_stuck_open_at[2] = {1e9, 1e9}, hb_fail_closed_at[2] = {1e9, 1e9};
  bool pmid_dead = false; double pmid_invalid_from = 1e9;
  bool pmid_cmp = false;                    // comparator state (true = P_mid above the trip)
  bool hb_both_prev = false, hb_hw_cut = false; double hb_both_rise_t = -1.0, hb_hw_cut_t = -1.0;   // v2.11 hardware both-open timer state
  int hb_hw_cuts = 0;                       // v2.11: number of hardware V1 cuts in this run
                                                   //   (needle held off the seat by debris, or an encoder offset; the plant needle is unaffected)
  // v2.8 TLM_RELIGHT as received by the FC (HAL sends every 20 ms)
  struct TlmrRx { double t; ecu::can::TlmRelight m; };
  std::vector<TlmrRx> tlmr;
  bool tlmr_on = true;

  void run(double t_end);
  void runUntil(double t_end, const std::function<bool(const Sim&)>& stop);
  const std::vector<Rec>& rec() const { return rec_; }
  void writeCsv(const std::string& fn, double t0 = -1e9, double t1 = 1e9) const;   // v2.11: optional time window

  EnginePlant eng;
  PintleDrive pintle;
  GimbalPlant2 gim;
  SenseLine pc_line;
  HobbyServo mv_servo;
  ecu::EngineEcu ecu;
  ecu::can::Decoder dec;
  ecu::Outputs out;
  SimConfig C;
  double t = 0;
  // v2.10 SIL time skip (LEAD 172 (1) safing hold, 960 s): from ecu_t_skip_at [plant s] the ECU clock (Inputs::t_s) runs ahead by
  // ecu_t_skip_s. Use ONLY while the ECU is in SAFE with nothing commanded: the plant is FROZEN over the skipped time (ASSUMED; the
  // physical N2 purge / hold is a GSE procedure, B-SAFE-1), so the test proves the ECU timing, not the chamber state after the hold
  double ecu_t_skip_at = 1e18, ecu_t_skip_s = 0.0;
  bool arm_bus_on = false, ecu_alive = true;
  double vbat = 8.2, i_total = 0;
  double first_lit_t = -1;
  int jam_events = 0;                // v2.6 one-tick jam events seen (Outputs::pintle_jam_event)
  double noprog_max = 0;             // v2.6 longest no-progress interval of the stall monitor in this run [s]
  double pc_xdcr_max = 0;            // v2.6 OI-6: highest absolute pressure at the transducer diaphragm in this run [Pa]
  bool ovp_q = false, ovp_cmp = false; // v2.2 hardware latch output (OVP_OK) and comparator state (true = over-pressure)
  double ovp_vf = 0.0, ovp_trip_t = -1, arm_off_t = -1;   // comparator filtered input [V]; first trip; first ARM-bus-off after a trip
  uint32_t frames_sent = 0, frames_corrupted = 0, frames_accepted = 0;
  uint8_t nv_gcal[32];               // v2.6 HAL EEPROM image of NvGimbalCal (written on Outputs::gimbal_cal_changed)
  int nv_gcal_status = -1;           // last boot decode (ecu::NvGimbalStatus)
  int nv_gcal_writes = 0;
  // v2.7 HAL non-volatile NvJamRecord image (b0 jam, b1 relight lockout, b2 lit session): written on the core's one-tick events,
  // decoded at boot into Inputs::maint_pintle_jam / nv_relight_lockout (CORRUPT = pending)
  uint8_t nv_jam[32];
  int nv_jam_writes = 0, boots = 0;
  bool nv_jam_in = false, nv_lockout_in = false, nv_segvap_in = false;   // v2.8 final: b3 vapour segment after an abort
  bool nv_hold_in = false;                                                // v2.10: b4 ground no-light safing hold
  // v2.7 pintle rail disconnect state
  bool ltc_gate = false; double ltc_ok_since = -1, t_bus_on = -1, v_servo = 0, v_reg = 0, ltc_first_trip_t = -1;
  int ltc_trips = 0;
  // v2.7 metrics
  long n2o_alone_ms = 0;              // ms with the torch N2O solenoid energised and the propane solenoid not (must stay 0)
  static long g_n2o_alone_ms;         // all Sims in this process
  std::vector<double> ox_unlit_starts;   // unignited N2O admitted through the pintle per IGNITION entry, until light or the run end [kg]
  double ox_unlit_total = 0;          // all unignited pintle N2O in the run (incl. the PREPRESS bleed lift) [kg]
  double vapour_purged_kg = 0;        // C7 vapour pushed through the pintle [kg]
  std::vector<double> ign_entry_t, run_entry_t;   // state-entry times seen
 private:
  void tick();
  void boot(double t0);              // v2.6 ECU init + HAL record load
  std::mt19937 rng_, rng2_, rng3_;   // v2.10: rng3_ for the photodiode (keeps the earlier noise sequences)
  std::mt19937 rng4_;                // v2.11: per-ADC-sample Pc noise (chain 1 / per-sample mode; keeps the other channels' sequences)
  double pcErrG(double p_abs, double tt) const;   // v2.11: gauge-equivalent reading with the configured error terms (no noise / spike)
  double pc_ch_ms_max_ = 0.0;        // v2.11: chamber pressure seen by the chain, max over the last ms (Rec::Pc while a replay runs)
  double ph_s_ = 0.10;               // v2.10 photodiode head state [V]
  std::normal_distribution<double> nrm_{0.0, 1.0};
  double pc_s1_ = 101325.0, pc_s2_ = 101325.0, pf_s_ = 101325.0, pt_s_ = 0, ptq_s_ = 101325.0;
  double ina_v_ = 0.0, aaf_v_ = 0.0, pcv_acc_ = 0.0, pcv_last_ = 0.0;   // v2.11 chain 1: INA333 output, anti-alias node, ADC sample sum [V]
  bool ep_open_ = false; int prev_state_ = -1;
  double pc_acc_ = 0; int pc_n_ = 0; double next_adc_ = 0;
  uint8_t seq_fast_ = 0, seq_state_ = 0, seq_aux_ = 0, seq_fct_ = 0, seq_tlmr_ = 0;
  std::vector<double> thr_hist_;     // v2.8 FC estimate history (1 ms) for the extra delay; v2.8.1: low-pass filtered plant thrust
  double fc_lp_ = 0.0;               // v2.8.1 first-order FC estimate state [N]
  size_t sched_idx_ = 0;
  double wd_last_kick_ = 0, reboot_until_ = -1;
  bool arm_req_prev_ = false, sw_on_ = false; double arm_en_off_t_ = -1;
  std::vector<Rec> rec_;
  int ms_ = 0;
};

}  // namespace sil
