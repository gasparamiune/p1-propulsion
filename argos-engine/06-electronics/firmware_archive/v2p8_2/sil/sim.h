// ARGOS engine SIL - closed-loop harness: FC command generator -> CAN frames -> ECU core (unchanged flight code)
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
  double arm_off_delay = 0.006;            // [s] DERIVED estimate: ARM switch turn-off (C301 Miller, bench verify)
  double runaway_us = 2100.0;              // [DATASHEET] servo maximum travel pulse (pintle runaway target)
  double pc_span_err = 0.0, pc_zero_err = 0.2e5;   // span fraction; zero offset [Pa] (removed by auto-zero)
  double pc_nl_bias = 0.0, pc_nl_ref = 1.0e5;      // v2.6 OI-6: error that survives the auto-zero (BFSL/TEB terms at pressure):
                                                   //   + pc_nl_bias * min(1, p_gauge / pc_nl_ref) [Pa] (zero at 0 bar g)
  double enc_lsb = 2.0 * M_PI / 16384.0;          // AS5048A 14-bit
  // power
  double vbat0 = 8.3, R_batt = 0.015, R_lead = 0.020, I_avionics = 0.35;   // [V, ohm, ohm, A] ASSUMED (v2.2: 8.3 V charged
                                                                             // pack; arm permit 8.1 V)
  // v2.5 regulated pintle servo rail (LEAD 2026-10-12; TPS552882 buck-boost, EN from the ARM bus). v2.6: rail v2 (LEAD: setpoint
  // +1 %, FB 100k/19.1k 0.1 %; calc/pintle_rail_v2.py)
  bool pintle_rail = true;                 // false = v2.4 wiring (pintle servo on the 2S bus)
  double rail_V = 7.483;                   // [DERIVED] typ output (7.395-7.570 V, rail v2; v1 was 7.418 V)
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
  double prail_noise = 0.005;              // [V rms] ASSUMED ADC2 + /10.1 divider
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
                                                   //   (needle held off the seat by debris, or an encoder offset; the plant needle is unaffected)
  // v2.8 TLM_RELIGHT as received by the FC (HAL sends every 20 ms)
  struct TlmrRx { double t; ecu::can::TlmRelight m; };
  std::vector<TlmrRx> tlmr;
  bool tlmr_on = true;

  void run(double t_end);
  void runUntil(double t_end, const std::function<bool(const Sim&)>& stop);
  const std::vector<Rec>& rec() const { return rec_; }
  void writeCsv(const std::string& fn) const;

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
  std::mt19937 rng_, rng2_;          // v2.7: rng2_ for the new channels (keeps the v2.6 noise sequence of the existing ones)
  std::normal_distribution<double> nrm_{0.0, 1.0};
  double pc_s1_ = 101325.0, pc_s2_ = 101325.0, pf_s_ = 101325.0, pt_s_ = 0, ptq_s_ = 101325.0;
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
