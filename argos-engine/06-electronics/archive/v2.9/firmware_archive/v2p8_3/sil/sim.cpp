// ARGOS engine SIL - closed-loop harness (v2.2: 0-1000 psig Pc transducer, hardware over-pressure trip, ARM switch
// turn-off delay, pintle runaway; v2.5: HV69 pintle servo on the regulated 7.4 V rail, battery current fed to the ECU's
// FM-PWR-01 supply monitor; v2.6: pintle rail current fed to the stall monitor, jam events and no-progress recorded; OI-6:
// transducer-side pressure recorded, Pc disturbance injection; per-axis gimbal notch record loaded at boot and after a watchdog
// reset, as-built 3-D pushrod gimbal with FEA structure compliance; v2.7: torch-pressure transducer, LTC4365 pintle-rail OV
// disconnect with the /FAULT -> MV-latch hardware gate, NvJamRecord HAL emulation (jam, relight lockout, lit session) across
// watchdog resets, test-stand flag, unignited N2O per start, torch N2O-alone counter; v2.8: FC_THRUST, mode strap, state TCs, sensor
// validity, bay temperature, comparator blinded with a failed Pc signal, TLM_RELIGHT received by the FC; v2.8 final: NvJamRecord b3
// vapour segment, tank-wall DS18B20 #1/#2, MV CLOSED-switch and pintle-encoder fault windows; v2.8.2: pintle-encoder bias window, RG-08). See sim.h.
#include "sim.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <limits>

namespace sil {
using namespace ecu;

long Sim::g_n2o_alone_ms = 0;

Sim::Sim(const SimConfig& c)
    : eng(c.eng), pintle(c.pm, c.sv_pintle, c.seed * 7 + 1), gim(c.gim2, c.sv_tvc[0], c.sv_tvc[1], c.seed * 7 + 2),
      pc_line(c.sense), mv_servo(c.sv_mv, c.seed * 7 + 4), C(c), rng_(c.seed), rng2_(c.seed * 7 + 5) {
  pc_line.init(101325.0);
  std::memset(nv_jam, 0xFF, sizeof nv_jam);   // v2.7: blank NvJamRecord (new board)
  // v2.6: the NV record as left by B-TVC-1 (or blank), then the boot path the HAL runs
  std::memset(nv_gcal, 0xFF, sizeof nv_gcal);
  if (!c.nv_gcal_blank) {
    const ecu::NvGimbalCal r = ecu::nvGimbalEncode(c.gcal_auto ? autoNotchCal(c) : c.gcal, 1, 0);
    std::memcpy(nv_gcal, &r, sizeof r);
  }
  boot(0.0);
  vbat = c.vbat0;
  pt_s_ = eng.P_tank;
  pf_s_ = 101325.0;
  ovp_vf = 0.5;   // transducer output at 0 bar g
  // v2.5: the plant's crank-slider must be the hardware the firmware was generated for (engine_params.h)
  const double geo[4][2] = {{c.pm.r_c, eng::kCrankR_m}, {c.pm.L, eng::kLinkL_m}, {c.pm.phi_c, eng::kCrankPhiContact_rad},
                            {c.pm.phi_n, eng::kCrankPhiNeutral_rad}};
  for (const auto& g : geo)
    if (std::fabs(g[0] - g[1]) > 1e-6 * std::max(1.0, std::fabs(g[1])) + 1e-7) {
      std::fprintf(stderr, "SIL: pintle crank geometry differs from engine_params.h (%.7g vs %.7g)\n", g[0], g[1]);
      std::abort();
    }
}

ecu::GimbalNotchCal autoNotchCal(const SimConfig& c) {
  ecu::GimbalNotchCal g;
  for (int k = 0; k < 2; ++k) {
    ServoParams s = c.sv_tvc[k]; s.V = c.gcal_V;
    g.ax[k].enabled = true;
    g.ax[k].f0_Hz = static_cast<float>(rockingModeHz(c.gim2, s, k));
    g.ax[k].q = cfg::kGimbalNotchQ;
    g.ax[k].depth_dB = cfg::kGimbalNotchDepth_dB;
  }
  return g;
}

void Sim::boot(double t0) {
  ecu.init(t0);
  ecu::GimbalNotchCal g;
  const ecu::NvGimbalStatus st = ecu::nvGimbalDecode(nv_gcal, &g);
  nv_gcal_status = static_cast<int>(st);
  if (st == ecu::NvGimbalStatus::VALID) ecu.setGimbalNotchCal(g);   // HAL: evt::GIMBAL_CAL_BAD otherwise (not modelled)
  // v2.7 HAL: jam / lockout / lit-session record -> boot inputs (CORRUPT = pending, fail-safe)
  ecu::NvJamRecord jr; const ecu::NvJamStatus js = ecu::nvJamDecode(nv_jam, &jr);
  nv_jam_in = ecu::nvJamPending(js, jr);
  nv_lockout_in = ecu::nvLockoutPending(js, jr);
  nv_segvap_in = ecu::nvSegVapourAtBoot(js, jr);   // v2.8 final b3 (or b2 at boot: reset during/after a lit burn)
  ++boots;
}

void Sim::run(double t_end) { runUntil(t_end, [](const Sim&) { return false; }); }

void Sim::runUntil(double t_end, const std::function<bool(const Sim&)>& stop) {
  while (t < t_end - 1e-9) {
    tick();
    if (stop(*this)) break;
  }
}

void Sim::tick() {
  std::uniform_real_distribution<double> uni(0.0, 1.0);
  for (Hook& h : hooks) if (!h.done && t >= h.t - 1e-9) { h.done = true; h.f(*this); }   // v2.7 timed scenario actions
  // ------------------------------------------------ 1) FC -> CAN -> decoder
  Commands cmd;
  const bool link = link_up && !(t >= link_down_from && t < link_down_to);
  auto deliver = [&](can::Frame f) {
    ++frames_sent;
    if (crc_corrupt_rate > 0 && uni(rng_) < crc_corrupt_rate) {
      const int bit = static_cast<int>(uni(rng_) * f.len * 8) % (f.len * 8);
      f.d[bit / 8] ^= static_cast<uint8_t>(1u << (bit % 8));
      ++frames_corrupted;
    }
    if (dec.accept(f, cmd)) ++frames_accepted;
  };
  if (link && (ms_ % 2 == 0)) {
    float g[2]; gimbal_cmd(t, g);
    deliver(can::encodeCmdFast(seq_fast_++, static_cast<float>(thrust_cmd(t)), g[0], g[1]));
  }
  if (link && (ms_ % 10 == 0)) deliver(can::encodeCmdAux(seq_aux_++, roll_cmd(t)));   // 100 Hz incl. explicit zeros
  // v2.8 FC_THRUST at 100 Hz (offset 5 ms from CMD_AUX): (v2.8.1 low-pass filtered, optionally delayed) plant thrust x (1 + bias) + noise
  if (link && fc_thr_on && (ms_ % 10 == 5) && t < fc_thr_stale_from) {
    const int lag = static_cast<int>(std::lround(fc_thr_lat * 1e3));
    const double F = thr_hist_.empty() ? 0.0 : thr_hist_[thr_hist_.size() > static_cast<size_t>(lag) ? thr_hist_.size() - 1 - lag : 0];
    const double est = std::max(0.0, F * (1.0 + fc_thr_bias) + fc_thr_noise * nrm_(rng2_));
    deliver(can::encodeFcThrust(seq_fct_++, static_cast<float>(est), t < fc_thr_invalid_from));
  }
  while (sched_idx_ < schedule.size() && schedule[sched_idx_].t <= t + 1e-9) {
    const StateCmd& s = schedule[sched_idx_++];
    if (!link) continue;
    if (s.cmd == Cmd::ABORT) deliver(can::encodeAbort(seq_state_++, 1));
    else deliver(can::encodeCmdState(seq_state_++, s.cmd, s.arg));
  }
  // ------------------------------------------------ 2) sensors -> Inputs (HAL scaling)
  Inputs in;
  in.t_s = t;
  const double pc_avg = pc_n_ ? pc_acc_ / pc_n_ : pc_s2_;
  pc_acc_ = 0; pc_n_ = 0;
  const double pc_gf = t >= pc_gain_at ? pc_gain : 1.0;   // v2.8.1 in-range wrong Pc (gain fault on PC_SIG)
  double pcg = (pc_avg - 101325.0) * (1.0 + C.pc_span_err) * pc_gf + C.pc_zero_err + 0.5 * C.pc_noise * nrm_(rng_);   // 4:1 avg
  if (C.pc_nl_bias != 0.0) pcg += C.pc_nl_bias * std::min(1.0, std::max(0.0, (pc_avg - 101325.0) / C.pc_nl_ref));
  if (t >= pc_spike_at - 1e-9 && t < pc_spike_end) {   // v2.6 OI-6 disturbance injection (EMI / ground shift)
    const double ph = pc_spike_period > 0 ? std::fmod(t - pc_spike_at + 1e-9, pc_spike_period) : t - pc_spike_at + 1e-9;
    if (ph < pc_spike_len) pcg += pc_spike_Pa;
  }
  // v2.6: 0-70 bar g M3200 (070BG; v2.2-v2.5 0-1000 psig); output limited to 0..4.95 V [ASSUMED: behaviour above FS not in the datasheet]
  const double v_pc = std::min(4.95, std::max(0.0, 0.5 + 4.0 * pcg / C.pc_fs));
  pcg = (v_pc - 0.5) / 4.0 * C.pc_fs;
  in.pc_raw_V = static_cast<float>(v_pc);
  if (t >= pc_sensor_fail_at) { in.pc_raw_V = 0.02f; pcg = (0.02 - 0.5) / 4.0 * C.pc_fs; }
  in.pc_Pa = static_cast<float>(pcg);
  in.pfeed_Pa = static_cast<float>(pf_s_ - 101325.0 + C.pfeed_noise * nrm_(rng_));
  in.ptank_Pa = static_cast<float>(pt_s_ - 101325.0 + C.ptank_noise * nrm_(rng_) + (t >= ptank_bias_at ? ptank_bias : 0.0));
  if (t >= tc_hot_at) in.tc_K[tc_hot_idx] = static_cast<float>(tc_hot_K);
  auto q = [&](double a) { return std::round(a / C.enc_lsb) * C.enc_lsb; };
  in.gimbal_meas_rad[0] = static_cast<float>(q(gim.a));   // AS5048A on the outer pin (alpha)
  in.gimbal_meas_rad[1] = static_cast<float>(q(gim.b));   // AS5048A on the inner pin (beta)
  in.pintle_meas_m = linkage::crankToLift(static_cast<float>(q(pintle.crank())));
  in.mv_open_sw = eng.mv_open_sw && t < mv_open_sw_fail_from; in.mv_closed_sw = eng.mv_closed_sw && t < mv_closed_sw_fail_from;
  in.pintle_meas_valid = !(t >= enc_fail_from && t < enc_fail_to);   // v2.8 final
  if (t >= enc_bias_from && t < enc_bias_to) in.pintle_meas_m += static_cast<float>(enc_bias_m);   // v2.8.2 RG-08
  in.vbat_V = static_cast<float>(vbat);
  in.ibat_A = static_cast<float>(i_total + C.ibat_noise * nrm_(rng_));   // v2.5: last ms battery current (A2 shunt)
  in.arm_plug_present = t < arm_plug_pull_at;
  in.arm_bus_on = arm_bus_on;
  in.ovp_ok = ovp_q;                 // v2.2: U331 Q on Teensy pin 29
  in.pintle_i_valid = C.pintle_isense;   // v2.6: rail current (last ms) for the stall monitor current path
  in.pintle_i_A = static_cast<float>(std::max(0.0, pintle.servo.current + C.ipint_noise * nrm_(rng_)));
  // v2.7: load cell only on the test stand (NaN in flight); torch transducer; pintle rail channels (ADC2); NV boot inputs
  in.load_cell_N = C.test_stand ? static_cast<float>(eng.thrust) : std::numeric_limits<float>::quiet_NaN();
  in.ptorch_Pa = static_cast<float>(ptq_s_ - 101325.0 + C.ptorch_noise * nrm_(rng2_));
  in.ptorch_valid = t < ptorch_fail_at;
  in.prail_valid = C.prail_sense;
  in.prail_V = static_cast<float>(std::max(0.0, v_servo + C.prail_noise * nrm_(rng2_)));
  in.preg_V = static_cast<float>(std::max(0.0, v_reg + C.prail_noise * nrm_(rng2_)));
  in.maint_pintle_jam = nv_jam_in;
  in.nv_relight_lockout = nv_lockout_in;
  // v2.8: coded strap, state TCs, sensor validity, bay temperature
  in.mode_strap = static_cast<uint8_t>(strap_override >= 0 ? strap_override : (C.test_stand ? 2 : 1));
  in.tc_mss1_K = static_cast<float>(tc_mss1_K); in.tc_mss1_valid = mss1_valid;
  in.tc_mss2_K = static_cast<float>(tc_mss2_K); in.tc_mss2_valid = mss2_valid;
  in.pfeed_valid = pfeed_valid; in.ptank_valid = ptank_valid;
  in.bay_K = static_cast<float>(bay_K); in.bay_valid = bay_valid;
  in.nv_seg_vapour = nv_segvap_in;   // v2.8 final
  for (int k = 0; k < 2; ++k) {
    in.ttank_wall_K[k] = static_cast<float>(ttank_wall_override_K > 0.0 ? ttank_wall_override_K : eng.T_tank + ttank_wall_bias_K[k]);
    in.ttank_wall_valid[k] = ttank_wall_valid[k];
  }
  // ------------------------------------------------ 3) ECU (or hang / watchdog reset)
  if (t >= hang_at && ecu_alive && reboot_until_ < 0) ecu_alive = false;
  if (ecu_alive) {
    ecu.test_disable_fw_ovp = fw_ovp_disabled; ecu.test_force_fast_prime = force_fast_prime;
    ecu.test_disable_pintle_mon = pintle_mon_disabled;
    ecu.step(in, cmd, out);
    if (out.gimbal_cal_changed) {   // v2.6 HAL: store the new calibration
      const ecu::NvGimbalCal r = ecu::nvGimbalEncode(ecu.gimbalNotchCal(), static_cast<uint16_t>(++nv_gcal_writes + 1), static_cast<uint32_t>(t * 1e3));
      std::memcpy(nv_gcal, &r, sizeof r);
    }
    if (ecu.healthy()) wd_last_kick_ = t;
    if (out.pintle_jam_event) ++jam_events;
    noprog_max = std::max(noprog_max, static_cast<double>(out.pintle_noprog_s));
    if (out.pintle_jam_event || out.maint_clear_jam || out.relight_lockout_event || out.lit_session_event || out.lit_session_close ||
        out.relight_lockout_clear || out.seg_vapour_event || out.seg_vapour_clear) {   // v2.7 HAL: NvJamRecord writes on one-tick events
      ecu::NvJamRecord jr; (void)ecu::nvJamDecode(nv_jam, &jr);   // CORRUPT: rewritten from the copy as read (HAL also raises JAM_RECORD_BAD)
      const uint32_t ms = static_cast<uint32_t>(t * 1e3);
      if (out.pintle_jam_event) jr = ecu::nvJamRecordEvent(jr, out.pintle_jam, ms);
      if (out.maint_clear_jam) { jr = ecu::nvJamClear(jr); nv_jam_in = false; }
      if (out.relight_lockout_event) jr = ecu::nvLockoutSet(jr, ms);
      if (out.lit_session_event) jr = ecu::nvLitSessionSet(jr);
      if (out.lit_session_close) jr = ecu::nvLitSessionClear(jr);
      if (out.relight_lockout_clear) { jr = ecu::nvLockoutClear(jr); nv_lockout_in = false; }
      if (out.seg_vapour_event) jr = ecu::nvSegVapourSet(jr);                                  // v2.8 final b3
      if (out.seg_vapour_clear) { jr = ecu::nvSegVapourClear(jr); nv_segvap_in = false; }
      std::memcpy(nv_jam, &jr, sizeof jr);
      ++nv_jam_writes;
    }
  } else if (reboot_until_ < 0 && t - wd_last_kick_ > cfg::kHwWatchdog_s) {
    out = Outputs();                 // MCU held in reset: pins high-Z -> pulled to off; PWM stops
    reboot_until_ = t + 0.30;        // ASSUMED reset + boot time
  }
  if (reboot_until_ >= 0 && t >= reboot_until_) {
    ecu = EngineEcu(); boot(t); ecu_alive = true; reboot_until_ = -1; hang_at = 1e9; wd_last_kick_ = t;
    dec = can::Decoder();
  }
  const bool mcu_ok = ecu_alive && reboot_until_ < 0;
  if (tlmr_on && mcu_ok && (ms_ % 20 == 0)) {   // v2.8 HAL: TLM_RELIGHT every 20 ms; the FC decodes it (CRC, length)
    can::TlmRelight m;
    if (can::decodeTlmRelight(can::encodeTlmRelight(seq_tlmr_++, out), &m)) tlmr.push_back({t, m});
  }
  const bool wd_ok = (t - wd_last_kick_) <= cfg::kHwWatchdog_s && reboot_until_ < 0;
  // v2.2 ARM chain: U331 latch (cleared while the comparator trips, set by an ARM_REQ rising edge) -> 3-input AND
  // (ARM_REQ, WD_OK, OVP_OK) -> high-side switch with a turn-off delay; the arming plug is a series physical break
  const bool req_rise = out.arm_bus_request && !arm_req_prev_;
  arm_req_prev_ = out.arm_bus_request;
  if (ovp_cmp) ovp_q = false; else if (req_rise) ovp_q = true;
  const bool arm_en = out.arm_bus_request && wd_ok && ovp_q;
  if (arm_en) { sw_on_ = true; arm_en_off_t_ = -1; }
  else { if (arm_en_off_t_ < 0) arm_en_off_t_ = t; if (t - arm_en_off_t_ >= C.arm_off_delay - 1e-9) sw_on_ = false; }
  arm_bus_on = in.arm_plug_present && sw_on_;
  if (ovp_trip_t >= 0 && arm_off_t < 0 && !arm_bus_on) arm_off_t = t;
  // ------------------------------------------------ 4) actuators + plant for one ms
  // v2.7: the pintle servo is powered only through the LTC4365 gate; its /FAULT (low while the gate is off) gates the MV latch
  const bool rail_ok = !C.pintle_rail || ltc_gate;
  pintle.servo.powered = arm_bus_on && t < pintle_unpower_at && rail_ok;
  gim.servo[0].powered = gim.servo[1].powered = out.servo_enable_tvc && wd_ok;
  mv_servo.powered = arm_bus_on;
  const bool latch = out.mv_latch && arm_bus_on && rail_ok;
  const bool ign = out.igniter_enable && arm_bus_on;
  const bool sol1 = out.sol[0] && ign, sol2 = out.sol[1] && ign, spark = out.spark_gate && ign;
  const bool pulses = mcu_ok || (ecu_alive == false && reboot_until_ < 0);   // a hung MCU keeps its last PWM running
  const int n = static_cast<int>(std::lround(1e-3 / C.dt_plant));
  const double dt = 1e-3 / n;
  double i_acc = 0;
  bool cmp_this_ms = false;
  const double v_trip = 0.5 + 4.0 * C.ovp_trip_Pa_g / C.pc_fs;   // comparator trip referred to PC_SIG [V]
  const double jam_th_p = pintle.servo.theta, jam_th_g = gim.servo[0].theta;
  for (int k = 0; k < n; ++k) {
    const double ts = t + k * dt;
    if (pulses) { mv_servo.setPulse(out.servo_us[3]); }
    mv_servo.step(dt, ts, 0.0, 0.0);
    const double us_p = (t >= pintle_runaway_at) ? C.runaway_us : (pulses ? out.servo_us[2] : 1500.0);
    pintle.step(dt, ts, us_p, eng.p_feed, eng.Pc);
    if (t >= pintle_jam_at) { pintle.servo.theta = jam_th_p; pintle.servo.omega = 0; }
    eng.step(dt, pintle.x, latch, mv_servo.powered ? mv_servo.theta : 0.0, sol1, sol2, spark);   // unpowered opener: spring back-drives it
    gim.G.thrust_frac = eng.thrust / 500.0;
    const double us_tvc[2] = {out.servo_us[0], out.servo_us[1]};
    gim.step(dt, ts, us_tvc);
    if (t >= tvc_jam_at) { gim.servo[0].theta = jam_th_g; gim.servo[0].omega = 0; }
    pc_s1_ = pc_line.step(dt, eng.Pc);
    pc_s2_ += (pc_s1_ - pc_s2_) * dt / C.pc_tau;
    pc_xdcr_max = std::max(pc_xdcr_max, pc_s2_);
    pf_s_ += (eng.p_feed - pf_s_) * dt / C.pc_tau;
    pt_s_ += (eng.P_tank - pt_s_) * dt / C.pc_tau;
    ptq_s_ += (eng.P_torch - ptq_s_) * dt / C.ptorch_tau;   // v2.7 torch transducer
    {   // v2.7 unignited N2O through the pintle (liquid + C7 vapour) per start
      const double mfl = eng.mox + eng.mvap;
      vapour_purged_kg += eng.mvap * dt;
      if (!eng.ignited) { ox_unlit_total += mfl * dt; if (ep_open_ && !ox_unlit_starts.empty()) ox_unlit_starts.back() += mfl * dt; }
      else ep_open_ = false;
    }
    if (ts >= next_adc_) { pc_acc_ += pc_s2_; ++pc_n_; next_adc_ += 0.00025; }
    // v2.2 hardware comparator: transducer output (noise not modelled) through the tap RC (C.ovp_tau = ovp::kTau_s 5.28 ms; the
    // v2.2-v2.7 comment said 1.13 ms, the value used was the generated one). v2.8: a failed Pc signal (open wire / dead transducer,
    // pc_sensor_fail_at) blinds the comparator too - same PC_SIG wire (v2.7 kept it seeing the plant pressure: optimistic)
    const double v_sig = (t >= pc_sensor_fail_at) ? 0.02 : std::min(4.95, 0.5 + 4.0 * (pc_s2_ - 101325.0) * (ts >= pc_gain_at ? pc_gain : 1.0) / C.pc_fs);
    ovp_vf += (v_sig - ovp_vf) * dt / C.ovp_tau;
    if (ovp_vf > v_trip) { cmp_this_ms = true; if (ovp_trip_t < 0) ovp_trip_t = ts; }
    // v2.5: the pintle servo draws from the regulated rail; battery side = Vrail I / (eta Vbat)
    const double i_pint_bat = C.pintle_rail ? C.rail_V * pintle.servo.current / (C.rail_eta * std::max(vbat, 3.0))
                                            : pintle.servo.current;
    i_acc += gim.servo[0].current + gim.servo[1].current + i_pint_bat + mv_servo.current;
  }
  ovp_cmp = cmp_this_ms;            // latch update at the next tick (<= 1 ms later than the hardware)
  // power: servos direct on 2S; 12 V boost (eta 0.85 ASSUMED) feeds torch solenoids (2 x 0.8 A COMB) and coil
  const bool sol4 = out.sol[3] && arm_bus_on, sol5 = out.sol[4] && arm_bus_on;   // roll valves on the ARM bus
  const double p12 = (sol1 ? 9.6 : 0.0) + (sol2 ? 9.6 : 0.0) + (ign ? 2.0 : 0.0) + (sol4 ? 9.6 : 0.0) + (sol5 ? 9.6 : 0.0);
  i_total = i_acc / n + C.I_avionics + p12 / 0.85 / std::max(vbat, 5.0) + (latch ? vbat / C.R_latch : 0.0);   // v2.8 MV-P magnet
  vbat = C.vbat0 - C.R_batt * i_total - (t >= vbat_drop_at ? vbat_drop : 0.0);
  if (C.pintle_rail) {   // regulated: holds rail_V up to the current limit (buck-boost: independent of Vbat >= 6 V)
    const double ip = pintle.servo.current;
    double vr = ip <= C.rail_Ilim ? C.rail_V : C.rail_V * C.rail_Ilim / ip;   // crude constant-current fold-back
    // v2.7: soft start from ARM-bus on; injected regulator faults
    if (!arm_bus_on) { t_bus_on = -1; vr = 0.0; }
    else {
      if (t_bus_on < 0) t_bus_on = t;
      vr *= std::min(1.0, (t + 1e-3 - t_bus_on) / C.rail_tss);
      if (t >= preg_fail_at - 1e-9) vr = preg_fail_V;
      if (t >= prail_ov_at - 1e-9 && t < prail_ov_at + std::max(prail_ov_len, 1e-3) - 1e-9) vr = std::max(vr, C.ltc_ov_V + 0.25);
    }
    v_reg = vr;
    // LTC4365: gate off at once outside the UV/OV window (2 us fault delay + 4 us fast turn-off << 1 ms); back on ltc_restart_s
    // after VIN has stayed inside the window
    const bool window = v_reg > C.ltc_uv_V && v_reg < C.ltc_ov_V;
    if (!window) {
      if (ltc_gate && v_reg >= C.ltc_ov_V) { ++ltc_trips; if (ltc_first_trip_t < 0) ltc_first_trip_t = t; }
      ltc_gate = false; ltc_ok_since = -1;
    } else {
      if (ltc_ok_since < 0) ltc_ok_since = t;
      if (t + 1e-3 - ltc_ok_since >= C.ltc_restart_s - 1e-9) ltc_gate = true;
    }
    if (ltc_gate) v_servo = v_reg - C.R_lead_pintle * ip;
    else {   // servo side discharges through the bleed (and any servo draw) - exact over 1 ms for the RC part
      const double tau = C.R_bleed_servo * C.C_servo_side;
      v_servo = std::max(0.0, v_servo * std::exp(-1e-3 / tau) - C.I_servo_off * 1e-3 / C.C_servo_side);
    }
    pintle.servo.P.V = ltc_gate ? v_servo : 0.0;
  } else {
    pintle.servo.P.V = vbat - C.R_lead * pintle.servo.current;
  }
  gim.servo[0].P.V = vbat - C.R_lead * gim.servo[0].current;
  gim.servo[1].P.V = vbat - C.R_lead * gim.servo[1].current;
  if (eng.ignited && first_lit_t < 0) first_lit_t = t;
  if (fc_thr_tau > 0) fc_lp_ += (eng.thrust - fc_lp_) * (1.0 - std::exp(-1e-3 / fc_thr_tau));   // v2.8.1 adopted tau 20 ms estimate
  thr_hist_.push_back(fc_thr_tau > 0 ? fc_lp_ : eng.thrust);   // v2.8 FC estimate latency buffer (v2.8.1: filtered)
  if (thr_hist_.size() > 200) thr_hist_.erase(thr_hist_.begin(), thr_hist_.begin() + 100);
  // v2.7 sequence metrics: torch N2O without propane; IGNITION / RUN entries (a new unignited-N2O episode per IGNITION entry)
  if (sol1 && !sol2) { ++n2o_alone_ms; ++g_n2o_alone_ms; }
  {
    const int st = static_cast<int>(out.state);
    if (st == static_cast<int>(State::IGNITION) && prev_state_ != st) { ox_unlit_starts.push_back(0.0); ep_open_ = !eng.ignited; ign_entry_t.push_back(t); }
    if (st == static_cast<int>(State::RUN) && prev_state_ != st) run_entry_t.push_back(t);
    prev_state_ = st;
  }
  // ------------------------------------------------ record
  if (ms_ % C.record_every_ms == 0) {
    Rec r{};
    r.t = t; r.thr_cmd = thrust_cmd(t); r.F = eng.thrust; r.F_est = out.thrust_est_N; r.Pc = eng.Pc;
    r.Pc_meas = ecu.pcAbsFiltered(); r.Pc_sp = out.pc_sp_active_Pa; r.x = pintle.x; r.x_cmd = out.pintle_cmd_m;
    r.x_ff = ecu.pcc().ff(); r.integ = ecu.pcc().integrator(); r.band = ecu.pcc().freezeBand();
    r.ptank = eng.P_tank; r.pfeed = eng.p_feed; r.mox = eng.mox; r.mf = eng.mf; r.of = eng.of;
    float g[2]; gimbal_cmd(t, g);
    r.ga_cmd = out.gimbal_cmd_shaped_rad[0]; r.ga = gim.a; r.gb_cmd = out.gimbal_cmd_shaped_rad[1]; r.gb = gim.b;
    r.vbat = vbat; r.i_tot = i_total; r.mv = eng.mv_frac; r.crank_deg = pintle.crank() * 180.0 / M_PI;
    r.Fnet_pintle = pintle.F_net; r.Tservo_pintle = pintle.servo.T_motor; r.us_pintle = out.servo_us[2];
    r.state = static_cast<int>(out.state); r.abort = static_cast<int>(out.abort_cause); r.faults = out.fault_bits;
    r.torch = eng.torch_lit; r.ignited = eng.ignited; r.spark = spark; r.sol1 = sol1;
    r.ceiling = 0; r.sol4 = sol4; r.sol5 = sol5; r.arm_bus = arm_bus_on; r.ovp_ok = ovp_q;
    r.gasT = eng.gas_active ? eng.gas_T : 0.0; r.us_mvop = out.servo_us[3];
    r.v_pint = pintle.servo.P.V; r.i_pint = pintle.servo.current;
    r.noprog = out.pintle_noprog_s; r.jam_kind = out.pintle_fault_kind; r.Pc_xdcr = pc_s2_;
    r.ptorch = eng.P_torch; r.ptorch_in = in.ptorch_valid ? in.ptorch_Pa : NAN; r.prail = v_servo; r.preg = v_reg;
    r.mvap = eng.mvap; r.vap_cc = eng.vap_left * 1e6; r.ox_unlit = ox_unlit_starts.empty() ? 0.0 : ox_unlit_starts.back();
    r.sol2 = sol2; r.mv_latch_hw = latch; r.ltc_gate = ltc_gate; r.torch_ok = out.torch_ok; r.lockout = out.relight_lockout;
    r.seat_wait = out.mv_seat_wait; r.ign_check = out.ign_check_s; r.relight_ext = out.relight_ext; r.torch_closed = out.torch_closed;
    r.ign_rule = out.ign_rule; r.relight_direct = out.relight_direct; r.s1_fault = out.s1_fault; r.seg_primed = out.seg_primed;
    r.seg_valid = out.seg_valid; r.relight_block = out.relight_block; r.mode_stand = out.mode_stand;
    r.ign_lift_t = out.ign_lift_t_s; r.relight_worst = 1e-3 * out.relight_worst_ms; r.fc_thr = out.fc_thrust_fresh ? 1.0 : 0.0;
    r.s1_dp = out.s1_dp_Pa;
    r.rstate = out.relight_state; r.segvap = out.seg_vapour; r.tank_hot = out.tank_hot; r.tank_T = out.tank_T_K;
    rec_.push_back(r);
  }
  t += 1e-3; ++ms_;
}

void Sim::writeCsv(const std::string& fn) const {
  std::ofstream f(fn);
  f << "t,thr_cmd,F,F_est,Pc,Pc_meas,Pc_sp,x,x_cmd,x_ff,integ,band,ptank,pfeed,mox,mf,of,ga_cmd,ga,gb_cmd,gb,vbat,i_tot,mv,crank_deg,"
       "Fnet_pintle,Tservo_pintle,us_pintle,state,abort,faults,torch,ignited,spark,sol1,sol4,sol5,arm_bus,ovp_ok,gas_T,us_mv_opener,"
       "v_pintle,i_pintle,noprog,jam_kind,Pc_xdcr,sol2,P_torch,ptorch_in,prail_V,preg_V,mv_latch_hw,ltc_gate,torch_ok,lockout,seat_wait,"
       "mvap,vap_left_cc,ox_unlit_start,ign_rule,ign_lift_t,relight_direct,s1_fault,s1_dp,seg_valid,seg_primed,relight_block,relight_worst,"
       "mode_stand,fc_thr_fresh,relight_state,seg_vapour,tank_hot,tank_T\n";
  char b[1200];
  for (const Rec& r : rec_) {
    std::snprintf(b, sizeof b, "%.4f,%.2f,%.3f,%.3f,%.0f,%.0f,%.0f,%.4e,%.4e,%.4e,%.4e,%.0f,%.0f,%.0f,%.5f,%.5f,%.3f,%.5f,%.5f,%.5f,%.5f,"
                  "%.3f,%.3f,%.3f,%.3f,%.2f,%.4f,%.2f,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.1f,%.1f,%.3f,%.3f,%.4f,%d,%.0f,"
                  "%d,%.0f,%.0f,%.3f,%.3f,%d,%d,%d,%d,%d,%.5f,%.3f,%.6f,%d,%.4f,%d,%d,%.0f,%d,%d,%d,%.3f,%d,%.0f,%d,%d,%d,%.2f\n",
                  r.t, r.thr_cmd, r.F, r.F_est, r.Pc, r.Pc_meas, r.Pc_sp, r.x, r.x_cmd, r.x_ff, r.integ, r.band, r.ptank, r.pfeed,
                  r.mox, r.mf, r.of, r.ga_cmd, r.ga, r.gb_cmd, r.gb, r.vbat, r.i_tot, r.mv, r.crank_deg, r.Fnet_pintle,
                  r.Tservo_pintle, r.us_pintle, r.state, r.abort, r.faults, r.torch, r.ignited, r.spark, r.sol1, r.sol4, r.sol5,
                  r.arm_bus, r.ovp_ok, r.gasT, r.us_mvop, r.v_pint, r.i_pint, r.noprog, r.jam_kind, r.Pc_xdcr,
                  r.sol2, r.ptorch, r.ptorch_in, r.prail, r.preg, r.mv_latch_hw, r.ltc_gate, r.torch_ok, r.lockout, r.seat_wait,
                  r.mvap, r.vap_cc, r.ox_unlit, r.ign_rule, r.ign_lift_t, r.relight_direct, r.s1_fault, r.s1_dp, r.seg_valid, r.seg_primed,
                  r.relight_block, r.relight_worst, r.mode_stand, r.fc_thr, r.rstate, r.segvap, r.tank_hot, r.tank_T);
    f << b;
  }
}

}  // namespace sil
