// [v2.13 2026-10-21: TC4 fault on the seat TC reading (seat_tc_fault_*), EngineEcu v2.13 selections at boot (seat_arm_rule_fw, jfwd_inhibit_fw, seat_step_inhibit_fw)]
// [v2.11 2026-10-13, LEAD CHANGELOG 203/205: Pc chain selector (C1 default), per-sample ADC limit (item 14), ride-through hardware model (switched long RC: DELETED 2026-10-20, LEAD 216 (3) fixed RC), stuck-high Pc, FA-1 replay, chamber metrics, windowed CSV; see sim.h]
// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175: photodiode and fault hooks, ECU clock skip; full list in 06-electronics/REPORT-v2.10-HANDBACK.md] ARGOS engine SIL - closed-loop harness (v2.2: 0-1000 psig Pc transducer, hardware over-pressure trip, ARM switch
// turn-off delay, pintle runaway; v2.5: HV69 pintle servo on the regulated 7.4 V rail, battery current fed to the ECU's
// FM-PWR-01 supply monitor; v2.6: pintle rail current fed to the stall monitor, jam events and no-progress recorded; OI-6:
// transducer-side pressure recorded, Pc disturbance injection; per-axis gimbal notch record loaded at boot and after a watchdog
// reset, as-built 3-D pushrod gimbal with FEA structure compliance; v2.7: torch-pressure transducer, LTC4365 pintle-rail OV
// disconnect with the /FAULT -> MV-latch hardware gate, NvJamRecord HAL emulation (jam, relight lockout, lit session) across
// watchdog resets, test-stand flag, unignited N2O per start, torch N2O-alone counter; v2.8: FC_THRUST, mode strap, state TCs, sensor
// validity, bay temperature, comparator blinded with a failed Pc signal, TLM_RELIGHT received by the FC; v2.8 final: NvJamRecord b3
// vapour segment, tank-wall DS18B20 #1/#2, MV CLOSED-switch and pintle-encoder fault windows; v2.8.2: pintle-encoder bias window, RG-08). See sim.h.
#include "sim.h"
#include "sensor_scale.h"   // v2.10 RE-19 ladder::nominalRatio
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
      pc_line(c.pc_chain == 1 ? c.sense_c1 : c.sense), mv_servo(c.sv_mv, c.seed * 7 + 4), C(c), rng_(c.seed), rng2_(c.seed * 7 + 5),
      rng3_(c.seed * 7 + 6), rng4_(c.seed * 7 + 7) {
  if (c.pc_chain == 1 && ecu::cfg::kPcXdcrSel != 1) {   // v2.11: the HAL scaling (pcFlightCal) must match the modelled transducer
    std::fprintf(stderr, "SIL: pc_chain 1 (C1 XTL-190) needs cfg::kPcXdcrSel == 1\n");
    std::abort();
  }
  ph_s_ = c.photo_dark_V;
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
  if (c.pc_chain == 1) {   // v2.11 C1: PC_SIG = 0.5 V + 4 V x p_abs / FS (absolute) at the sea-level ambient
    ovp_vf = ina_v_ = aaf_v_ = pcv_last_ = 0.5 + 4.0 * 101325.0 / c.pc_fs_abs;
  }
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

// v2.12 (REV-ELEC-3 R3-01 A5) seat drift (sim.h SimConfig seat_*)
double Sim::seatMechT(double t) const {
  if (!std::isfinite(seat_burn0) || t < seat_burn0) return -1.0;
  if (t < C.seat_t_sd) {
    const double f = (t - seat_burn0) / std::max(1e-6, C.seat_t_sd - seat_burn0);
    return 0.001 + f * (C.seat_mech_sd_s - 0.001);
  }
  return C.seat_mech_sd_s + (t - C.seat_t_sd);
}
double Sim::seatInterp(double tm, int col) const {
  const auto& h = C.seat_hist;
  if (h.empty() || tm <= h.front()[0]) return h.empty() ? 0.0 : h.front()[col];
  if (tm >= h.back()[0]) return h.back()[col];
  if (seat_i_ >= h.size() - 1 || h[seat_i_][0] > tm) seat_i_ = 0;
  while (seat_i_ + 1 < h.size() - 1 && h[seat_i_ + 1][0] <= tm) ++seat_i_;
  const auto& a = h[seat_i_]; const auto& b = h[seat_i_ + 1];
  return a[col] + (b[col] - a[col]) * (tm - a[0]) / std::max(1e-12, b[0] - a[0]);
}
double Sim::seatDriftPa(double t) const {
  if (!C.seat_drift) return 0.0;
  const double fT0 = (C.seat_taw_K - C.seat_T0_K) / (C.seat_taw_K - 293.15);
  const double tm = seatMechT(t);
  const double dT = tm < 0.0 ? 0.0 : fT0 * seatInterp(tm, 1);
  return C.seat_s * C.seat_k * C.seat_c_PaK * ((C.seat_T0_K - C.seat_trim_K) + dT);
}

double Sim::pcErrG(double p_abs, double tt) const {   // v2.11 (sim.h)
  const double gf = tt >= pc_gain_at ? pc_gain : 1.0;
  double g = (p_abs - 101325.0) * (1.0 + C.pc_span_err) * gf + C.pc_zero_err;
  if (C.pc_nl_bias != 0.0) g += C.pc_nl_bias * std::min(1.0, std::max(0.0, (p_abs - 101325.0) / C.pc_nl_ref));
  if (C.pc_lin_bias != 0.0) g += C.pc_lin_bias * (p_abs - 101325.0) / C.pc_lin_ref;
  if (tt >= C.pc_off_from) g += C.pc_off;
  g += seatDriftPa(tt);   // v2.12 R3-01 A5
  return g;
}

void Sim::boot(double t0) {
  ecu.init(t0);
  ecu::GimbalNotchCal g;
  const ecu::NvGimbalStatus st = ecu::nvGimbalDecode(nv_gcal, &g);
  nv_gcal_status = static_cast<int>(st);
  if (st == ecu::NvGimbalStatus::VALID) ecu.setGimbalNotchCal(g);   // HAL: evt::GIMBAL_CAL_BAD otherwise (not modelled)
  if (C.seat_coef_cal != 0.0) {   // v2.12 HAL: per-serial B-PC-1 coefficient and its zero temperature (= the SIL trim temperature)
    ecu.setPcSeatCoef(static_cast<float>(C.seat_coef_cal)); ecu.setPcSeatTcal(static_cast<float>(C.seat_trim_K));
  }
  if (C.purge_cal_flow > 0.0) ecu.setPurgeCal(static_cast<float>(C.purge_cal_flow), static_cast<float>(C.purge_cal_cap));   // v2.12
  // v2.7 HAL: jam / lockout / lit-session record -> boot inputs (CORRUPT = pending, fail-safe)
  ecu::NvJamRecord jr; const ecu::NvJamStatus js = ecu::nvJamDecode(nv_jam, &jr);
  nv_jam_in = ecu::nvJamPending(js, jr);
  nv_lockout_in = ecu::nvLockoutPending(js, jr);
  nv_segvap_in = ecu::nvSegVapourAtBoot(js, jr);   // v2.8 final b3 (or b2 at boot: reset during/after a lit burn)
  nv_hold_in = ecu::nvSafingHoldPending(js, jr);    // v2.10 b4
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
  in.t_s = t + (t >= ecu_t_skip_at - 1e-9 ? ecu_t_skip_s : 0.0);   // v2.10 SIL time skip (safing hold; sim.h)
  const bool spike_now = [&] {   // v2.6 OI-6 disturbance injection (EMI / ground shift) on the 1 kHz reading
    if (!(t >= pc_spike_at - 1e-9 && t < pc_spike_end)) return false;
    const double ph = pc_spike_period > 0 ? std::fmod(t - pc_spike_at + 1e-9, pc_spike_period) : t - pc_spike_at + 1e-9;
    return ph < pc_spike_len;
  }();
  if (C.pc_chain == 1 || C.pc_clamp_per_sample_v210) {
    // v2.11: per-ADC-sample limited samples (substep loop below) -> HAL 4:1 average -> spike -> HAL scaling (C1: pcFlightCal(101325),
    // gauge-equivalent; chain 0 per-sample mode: 070BG nominal). LEAD 203 (7) item 14: the limit acts on each sample, before the average
    if (C.pc_off_on_ign && C.pc_off_from > 1e8 && out.state == State::IGNITION) C.pc_off_from = t;
    const double fs = C.pc_chain == 1 ? C.pc_fs_abs : C.pc_fs;
    double v = pc_n_ ? pcv_acc_ / pc_n_ : pcv_last_;
    pcv_acc_ = 0; pc_acc_ = 0; pc_n_ = 0;
    if (spike_now) v += 4.0 * pc_spike_Pa / fs;
    // stuck high: chain 0 per-sample mode only; on C1 the conditioner output itself is forced in the sub-step loop (ADC samples and comparator
    // tap see it physically; the 1 ms read average follows), v2.11 R2-23 (the v2.11 draft also forced this read: a 1 ms glitch looked 2 ms long)
    if (C.pc_chain != 1 && t >= pc_stuck_high_at && t < pc_stuck_high_to) v = 4.95;
    if (t >= pc_sensor_fail_at) v = 0.02;
    v = std::max(0.0, std::min(C.pc_chain == 1 ? C.pc_adc_max_V : 4.95, v));
    in.pc_raw_V = static_cast<float>(v);
    const ecu::xdcr::XdcrCal cal = C.pc_chain == 1 ? ecu::xdcr::pcFlightCal(101325.0f) : ecu::xdcr::cal070BG();
    in.pc_Pa = ecu::xdcr::gaugePa(static_cast<float>(v), 5.0f, cal);
  } else {   // the v2.10 SIL HAL model (chain 0), unchanged: average of the transducer-side pressure, errors, ONE limit after the average
    const double pc_avg = pc_n_ ? pc_acc_ / pc_n_ : pc_s2_;
    pc_acc_ = 0; pc_n_ = 0;
    const double pc_gf = t >= pc_gain_at ? pc_gain : 1.0;   // v2.8.1 in-range wrong Pc (gain fault on PC_SIG)
    double pcg = (pc_avg - 101325.0) * (1.0 + C.pc_span_err) * pc_gf + C.pc_zero_err + 0.5 * C.pc_noise * nrm_(rng_);   // 4:1 avg
    if (C.pc_nl_bias != 0.0) pcg += C.pc_nl_bias * std::min(1.0, std::max(0.0, (pc_avg - 101325.0) / C.pc_nl_ref));
    if (C.pc_lin_bias != 0.0) pcg += C.pc_lin_bias * (pc_avg - 101325.0) / C.pc_lin_ref;   // v2.9 S9 residual shapes
    if (C.pc_off_on_ign && C.pc_off_from > 1e8 && out.state == State::IGNITION) C.pc_off_from = t;
    if (t >= C.pc_off_from) pcg += C.pc_off;
    if (spike_now) pcg += pc_spike_Pa;
    // v2.6: 0-70 bar g M3200 (070BG; v2.2-v2.5 0-1000 psig); output limited to 0..4.95 V [ASSUMED: behaviour above FS not in the datasheet]
    double v_pc = std::min(4.95, std::max(0.0, 0.5 + 4.0 * pcg / C.pc_fs));
    if (t >= pc_stuck_high_at && t < pc_stuck_high_to) v_pc = 4.95;   // v2.11 S6R
    pcg = (v_pc - 0.5) / 4.0 * C.pc_fs;
    in.pc_raw_V = static_cast<float>(v_pc);
    if (t >= pc_sensor_fail_at) { in.pc_raw_V = 0.02f; pcg = (0.02 - 0.5) / 4.0 * C.pc_fs; }
    in.pc_Pa = static_cast<float>(pcg);
  }
  in.pfeed_Pa = static_cast<float>(pf_s_ - 101325.0 + C.pfeed_noise * nrm_(rng_));
  in.ptank_Pa = static_cast<float>(pt_s_ - 101325.0 + C.ptank_noise * nrm_(rng_) + (t >= ptank_bias_at ? ptank_bias : 0.0) + C.ptank_bias0_Pa);
  if (t >= tc_hot_at) in.tc_K[tc_hot_idx] = static_cast<float>(tc_hot_K);
  if (C.seat_tc) {   // v2.12 seat TC (option (b)) on the MAX31856 #4 channel
    const double fT0 = (C.seat_taw_K - C.seat_T0_K) / (C.seat_taw_K - 293.15);
    const double tm = seatMechT(t);
    const double tt = C.seat_T0_K + (tm < 0.0 ? 0.0 : fT0 * seatInterp(tm, 2));
    if (!std::isfinite(seat_tc_f_)) seat_tc_f_ = tt;
    double tau = C.seat_tc_tau;   // v2.13 SIL-only seat time-axis variant: the 0.25 s lag on the Mechanical axis in the compressed burn
    if (C.seat_ts_hook && std::isfinite(seat_burn0) && t >= seat_burn0 && t < C.seat_t_sd)
      tau /= (C.seat_mech_sd_s - 0.001) / std::max(1e-6, C.seat_t_sd - seat_burn0);
    seat_tc_f_ += (tt - seat_tc_f_) * (1.0 - std::exp(-1e-3 / tau));
    double rd = seat_tc_f_ + (t >= C.seat_tc_err_from ? C.seat_tc_err_K : 0.0);
    if (C.seat_tc_fault_K != 0.0 && t >= C.seat_tc_fault_from - 1e-9 &&
        (C.seat_tc_fault_dur <= 0.0 || t < C.seat_tc_fault_from + C.seat_tc_fault_dur - 1e-9)) rd += C.seat_tc_fault_K;   // v2.13
    in.tc_bore_K = static_cast<float>(rd);
    in.tc_bore_valid = true;
  }
  for (int k = 0; k < 2; ++k) in.tc_valid[k] = t < tc_invalid_at[k];   // v2.10 RE-08
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
  in.photo_V = static_cast<float>(std::min(C.photo_sat_V, ph_s_ + C.photo_noise * nrm_(rng3_)));   // v2.10 FA-1
  in.photo_valid = C.photo_fitted && t < photo_fail_at;
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
  in.nv_safing_hold = nv_hold_in;     // v2.10
  {   // v2.9 head-end bleed P_mid: 170BG on the mid tee -> LMV331 comparator (trip / release, gauge) -> MV switch ladder (pin 23)
    const double pm_g = eng.P_mid - 101325.0 + C.pmid_noise * nrm_(rng2_);
    if (pm_g > C.pmid_trip_Pa_g) pmid_cmp = true; else if (pm_g < C.pmid_rel_Pa_g) pmid_cmp = false;
    in.pmid_hi = pmid_cmp && !pmid_dead;
    in.pmid_valid = t < pmid_invalid_from;
    // v2.10 RE-19: raw ladder ratio of the reported code (pad-BIT harness step); ladder_dr = harness leak / resistor error [ASSUMED 0]
    const float nr = ecu::ladder::nominalRatio(in.mv_open_sw, in.mv_closed_sw, in.pmid_hi);
    in.mv_ladder_ratio = (in.pmid_valid && std::isfinite(nr)) ? static_cast<float>(nr + C.ladder_dr + C.ladder_noise * nrm_(rng3_)) : 1.0f;
  }
  for (int k = 0; k < 2; ++k) {
    in.ttank_wall_K[k] = static_cast<float>(ttank_wall_override_K > 0.0 ? ttank_wall_override_K : eng.T_tank + ttank_wall_bias_K[k] + C.ttank_wall_bias0_K[k]);
    in.ttank_wall_valid[k] = ttank_wall_valid[k];
  }
  // ------------------------------------------------ 3) ECU (or hang / watchdog reset)
  if (t >= hang_at && ecu_alive && reboot_until_ < 0) ecu_alive = false;
  if (ecu_alive) {
    ecu.test_disable_fw_ovp = fw_ovp_disabled; ecu.test_force_fast_prime = force_fast_prime;
    ecu.hbleed_fitted = C.eng.hb_fitted; ecu.ign_detect_relative = C.ign_relative; ecu.pc_coast_rezero = C.coast_rezero;   // v2.9
    ecu.ptank_cal_ok = C.ptank_cal;                                                                                          // v2.10
    ecu.test_disable_pintle_mon = pintle_mon_disabled;
    if (C.ride_fw >= 0) ecu.ride_through = C.ride_fw == 1;                                                                   // v2.11
    if (C.seat_arm_rule_fw >= 0) ecu.seat_arm_rule = C.seat_arm_rule_fw == 1;                                                // v2.13
    if (C.jfwd_inhibit_fw >= 0) ecu.jfwd_relight_inhibit = C.jfwd_inhibit_fw == 1;                                           // v2.13
    if (C.seat_step_inhibit_fw >= 0) ecu.seat_step_relight_inhibit = C.seat_step_inhibit_fw == 1;                            // v2.13
    if (C.seat_ts_hook) {   // v2.13 SIL-only disclosed variant: the TC4 slew on the Mechanical time axis while the seat map is compressed
      double ts = 1.0;
      if (std::isfinite(seat_burn0) && t >= seat_burn0 && t < C.seat_t_sd) ts = (C.seat_mech_sd_s - 0.001) / std::max(1e-6, C.seat_t_sd - seat_burn0);
      ecu.sil_seat_ts = static_cast<float>(ts);
    }
    ecu.step(in, cmd, out);
    if (out.gimbal_cal_changed) {   // v2.6 HAL: store the new calibration
      const ecu::NvGimbalCal r = ecu::nvGimbalEncode(ecu.gimbalNotchCal(), static_cast<uint16_t>(++nv_gcal_writes + 1), static_cast<uint32_t>(t * 1e3));
      std::memcpy(nv_gcal, &r, sizeof r);
    }
    if (ecu.healthy()) wd_last_kick_ = t;
    if (out.pintle_jam_event) ++jam_events;
    noprog_max = std::max(noprog_max, static_cast<double>(out.pintle_noprog_s));
    if (out.pintle_jam_event || out.maint_clear_jam || out.relight_lockout_event || out.lit_session_event || out.lit_session_close ||
        out.relight_lockout_clear || out.seg_vapour_event || out.seg_vapour_clear || out.safing_hold_event) {   // v2.7 HAL: NvJamRecord writes on one-tick events
      ecu::NvJamRecord jr; (void)ecu::nvJamDecode(nv_jam, &jr);   // CORRUPT: rewritten from the copy as read (HAL also raises JAM_RECORD_BAD)
      const uint32_t ms = static_cast<uint32_t>(t * 1e3);
      if (out.pintle_jam_event) jr = ecu::nvJamRecordEvent(jr, out.pintle_jam, ms);
      if (out.maint_clear_jam) { jr = ecu::nvJamClear(jr); nv_jam_in = false; }
      if (out.relight_lockout_event) jr = ecu::nvLockoutSet(jr, ms);
      if (out.lit_session_event) jr = ecu::nvLitSessionSet(jr);
      if (out.lit_session_close) jr = ecu::nvLitSessionClear(jr);
      if (out.safing_hold_event) jr = ecu::nvSafingHoldSet(jr);                                // v2.10 b4 (+ b1)
      if (out.relight_lockout_clear) { jr = ecu::nvLockoutClear(jr); nv_lockout_in = false; nv_hold_in = false; }
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
  {   // v2.11 hardware both-commanded-open timer (config.h kHbleedHwBoth*, DESIGN): BOTH = both drives high (ARM bus on); retriggerable
      // one-shot from each rising edge of BOTH; at its end, BOTH still high -> V1's drive is cut until BOTH falls
    const bool both = out.hbleed[0] && out.hbleed[1] && arm_bus_on;
    if (both && !hb_both_prev) hb_both_rise_t = t;
    if (!both) hb_hw_cut = false;
    else if (C.hb_both_timer && !hb_hw_cut && t - hb_both_rise_t >= C.hb_both_timer_s - 1e-9) { hb_hw_cut = true; hb_hw_cut_t = t; ++hb_hw_cuts; }
    hb_both_prev = both;
  }
  for (int k = 0; k < 2; ++k) {   // v2.9 head-end bleed valves on +12V_ARM (J508 / J509), NC
    eng.hb_cmd[k] = out.hbleed[k] && arm_bus_on && !(k == 0 && hb_hw_cut);
    eng.hb_stuck[k] = t >= hb_stuck_open_at[k]; eng.hb_failc[k] = t >= hb_fail_closed_at[k];
  }
  const bool pulses = mcu_ok || (ecu_alive == false && reboot_until_ < 0);   // a hung MCU keeps its last PWM running
  const int n = static_cast<int>(std::lround(1e-3 / C.dt_plant));
  const double dt = 1e-3 / n;
  double i_acc = 0;
  bool cmp_this_ms = false;
  const double v_trip = C.pc_chain == 1 ? 0.5 + 4.0 * C.ovp3_trip_Pa_abs / C.pc_fs_abs
                                         : 0.5 + 4.0 * C.ovp_trip_Pa_g / C.pc_fs;   // comparator trip referred to PC_SIG [V]
  const double tau_cmp = C.pc_chain == 1 ? C.ovp3_tau : C.ovp_tau;   // v2.11 LEAD 216 (3): FIXED (ride variant: ovp3_tau = 12.83 ms)
  const double a_ina = 1.0 - std::exp(-2.0 * M_PI * C.pc_ina_fc * dt), a_aaf = 1.0 - std::exp(-2.0 * M_PI * C.pc_aaf_fc * dt);
  if (fa1_t0 < 0.0 && !fa1_hist.empty() && t >= fa1_after - 1e-9 && eng.ignited) fa1_t0 = t;   // v2.11 S9R replay start (plant light)
  if (gop) {   // v2.11 S6R genuine over-pressure: trigger, then the decay reference at the first abort / ARM-bus loss (sim.h)
    if (gop_t0 < 0.0) {
      if (gop_trig == 1 && t >= gop_after - 1e-9 && eng.ignited) gop_t0 = t + gop_dt;
      else if (gop_trig == 2 && !run_entry_t.empty() && run_entry_t.back() >= gop_after - 1e-9) gop_t0 = run_entry_t.back() + gop_dt;
    }
    if (gop_t0 >= 0.0 && gop_t_ab < 0.0 && t >= gop_t0 - 1e-9 && gop_p0 > 0.0 &&
        (out.state == State::ABORT || out.state == State::SAFE || !arm_bus_on)) {
      gop_t_ab = t; gop_mox_ab = std::max(eng.mox + eng.mvap, 1e-4); gop_pf_ab = eng.p_feed;
    }
  }
  pc_ch_ms_max_ = 0.0;
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
    double p_ch = eng.Pc;   // v2.11: chamber pressure seen by the Pc chain (FA-1 replay, sim.h)
    if (fa1_t0 >= 0.0 && fa1_hist.size() > 1) {
      const double tau = ts - fa1_t0, Th = 1e-4 * static_cast<double>(fa1_hist.size() - 1);
      if (tau >= 0.0 && tau < Th) {
        const size_t j = std::min(fa1_hist.size() - 2, static_cast<size_t>(tau / 1e-4));
        const double f = std::min(1.0, tau / 1e-4 - static_cast<double>(j));
        const double h = (fa1_hist[j] + (fa1_hist[j + 1] - fa1_hist[j]) * f) * 1e5;
        p_ch = std::max(p_ch, 101325.0 + fa1_scale * (h - 101325.0));
      }
    }
    const bool gop_on = gop && gop_t0 >= 0.0 && ts >= gop_t0 - 1e-12;
    if (gop_on) {   // v2.11 S6R (sim.h)
      if (gop_p0 < 0.0) gop_p0 = p_ch;
      const double ff = gop_t_ab < 0.0 ? 1.0 : std::max(0.0, std::min(1.0, (eng.mox + eng.mvap) / gop_mox_ab));
      p_ch = std::max(p_ch, 101325.0 + (gop(ts - gop_t0, gop_p0) - 101325.0) * ff);
      if (gop_t_ab >= 0.0 && gop_p_ab <= 0.0) gop_p_ab = p_ch;   // head pressure at the abort (first plant step after it)
    }
    if (gop_on || (!gop && ts >= ch_from - 1e-12)) {   // v2.11 envelope metrics (LC-TB70, sim.h) from the trigger, or from ch_from
      const double tau = ts - (gop ? gop_t0 : ch_from);
      env_pk = std::max(env_pk, p_ch);
      if (p_ch > 45.0e5) { if (env_t45a < 0.0) env_t45a = ts; env_t45b = ts; env_t45 += dt; }
      if (p_ch > 58.1e5) env_t581 += dt;
      if (p_ch > 60.0e5) env_t60 += dt;
      if (p_ch > 63.1e5) { if (env_t63a < 0.0) env_t63a = ts; env_t63b = ts; env_t631 += dt; }
      if (tau < 0.6 && (tau < 0.05 || (k & 3) == 0)) { gtr_t.push_back(static_cast<float>(tau)); gtr_p.push_back(static_cast<float>(p_ch)); }
    }
    pc_ch_ms_max_ = std::max(pc_ch_ms_max_, p_ch);
    if (ts >= ch_from - 1e-12) { ch_pk = std::max(ch_pk, p_ch); if (p_ch > 45.0e5) ch_t45 += dt; if (p_ch > 30.0e5) ch_t30 += dt; }
    if (!std::isfinite(seat_burn0) && eng.ignited) seat_burn0 = ts;   // v2.12: history anchor at the first plant light
    if (C.trace25 && ts >= C.trace25_from - 1e-12) { tr25_t.push_back(ts); tr25_p.push_back(static_cast<float>(p_ch)); }   // v2.12 R4-02
    pc_s1_ = pc_line.step(dt, p_ch);
    if (C.pc_chain == 1) {   // v2.11 C1: no transducer lag; INA333 pole with its output swing (state limited: no wind-up past the rail)
      pc_s2_ = pc_s1_;
      const double v_lin = 0.5 + 4.0 * (pcErrG(pc_s1_, ts) + 101325.0) / C.pc_fs_abs;
      ina_v_ = std::max(C.pc_vmin, std::min(C.pc_vsat, ina_v_ + (v_lin - ina_v_) * a_ina));
      double v_out = ina_v_;
      if (ts >= pc_stuck_high_at && ts < pc_stuck_high_to) v_out = C.pc_vsat;     // S6R stuck high (conditioner at its rail)
      if (ts >= pc_sensor_fail_at) v_out = 0.02;         // open PC_SIG wire / dead conditioner (as the v2.10 model)
      aaf_v_ += (v_out - aaf_v_) * a_aaf;                // ADC-path anti-alias (12.7k || 4.02k x 22 nF)
      if (ts >= next_adc_) {                             // ADS131M04 sample: per-sample noise and the per-sample range limit (item 14)
        const double vs = std::max(0.0, std::min(C.pc_adc_max_V, aaf_v_ + 4.0 * C.pc_noise / C.pc_fs_abs * nrm_(rng4_)));
        pcv_acc_ += vs; pcv_last_ = vs; ++pc_n_; next_adc_ += 0.00025;
      }
      ovp_vf += (v_out - ovp_vf) * dt / tau_cmp;         // comparator tap RC (fixed; ride-through BOM variant C330 540 nF)
      if (ovp_vf > v_trip) { cmp_this_ms = true; if (ovp_trip_t < 0) ovp_trip_t = ts; }
    } else {
      pc_s2_ += (pc_s1_ - pc_s2_) * dt / C.pc_tau;
    }
    pc_xdcr_max = std::max(pc_xdcr_max, C.pc_chain == 1 ? pc_s1_ : pc_s2_);
    pf_s_ += (eng.p_feed - pf_s_) * dt / C.pc_tau;
    pt_s_ += (eng.P_tank - pt_s_) * dt / C.pc_tau;
    ptq_s_ += (eng.P_torch - ptq_s_) * dt / C.ptorch_tau;   // v2.7 torch transducer
    {   // v2.10 FA-1 photodiode head (ASSUMED levels, see SimConfig)
      const bool dark = t >= photo_dark_from;
      const double tgt = C.photo_dark_V + (dark ? 0.0 : (eng.torch_lit ? C.photo_torch_V : 0.0) +
                         (eng.ignited && C.photo_sees_main ? C.photo_main_V : 0.0) + (spark ? C.photo_spark_V : 0.0));
      ph_s_ += (tgt - ph_s_) * std::min(1.0, dt / C.photo_tau);
    }
    {   // v2.7 unignited N2O through the pintle (liquid + C7 vapour) per start
      const double mfl = eng.mox + eng.mvap;
      vapour_purged_kg += eng.mvap * dt;
      if (!eng.ignited) { ox_unlit_total += mfl * dt; if (ep_open_ && !ox_unlit_starts.empty()) ox_unlit_starts.back() += mfl * dt; }
      else ep_open_ = false;
    }
    if (C.pc_chain != 1) {
      if (ts >= next_adc_) {
        if (C.pc_clamp_per_sample_v210) {   // v2.11 item 14 on the 070BG chain: per-sample errors, noise and limit (0..4.95 V)
          const double vs = std::max(0.0, std::min(4.95, 0.5 + 4.0 * (pcErrG(pc_s2_, ts) + C.pc_noise * nrm_(rng4_)) / C.pc_fs));
          pcv_acc_ += vs; pcv_last_ = vs;
        } else pc_acc_ += pc_s2_;
        ++pc_n_; next_adc_ += 0.00025;
      }
      // v2.2 hardware comparator: transducer output (noise not modelled) through the tap RC (C.ovp_tau = ovp::kTau_s 5.28 ms; the
      // v2.2-v2.7 comment said 1.13 ms, the value used was the generated one). v2.8: a failed Pc signal (open wire / dead transducer,
      // pc_sensor_fail_at) blinds the comparator too - same PC_SIG wire (v2.7 kept it seeing the plant pressure: optimistic)
      double v_sig = (t >= pc_sensor_fail_at) ? 0.02 : std::min(4.95, 0.5 + 4.0 * (pc_s2_ - 101325.0) * (ts >= pc_gain_at ? pc_gain : 1.0) / C.pc_fs);
      if (ts >= pc_stuck_high_at && ts < pc_stuck_high_to && t < pc_sensor_fail_at) v_sig = 4.95;   // v2.11 S6R
      ovp_vf += (v_sig - ovp_vf) * dt / C.ovp_tau;
      if (ovp_vf > v_trip) { cmp_this_ms = true; if (ovp_trip_t < 0) ovp_trip_t = ts; }
    }
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
    // v2.9
    r.pmid = eng.P_mid; r.mdot_hb = eng.mdot_hb; r.mvap_hb = eng.mvap_hb;
    r.ign_ref = out.ign_ref_Pa; r.ign_rise = out.ign_rise_Pa; r.flame_ratio = out.flame_ratio; r.pc_map = out.pc_map_Pa;
    r.hb_io = (out.hbleed[0] ? 1 : 0) | (out.hbleed[1] ? 2 : 0) | (eng.hb_pos[0] > 0.5 ? 4 : 0) | (eng.hb_pos[1] > 0.5 ? 8 : 0) |
              (in.pmid_hi ? 16 : 0) | (in.pmid_valid ? 32 : 0);
    r.ign_det = out.ign_det; r.a7 = out.a7_phase | (out.a7_flag ? 4 : 0) | (out.a7_event ? 8 : 0) | (out.tlm_flags & 0xF0);   // b4-b7 tlmf:: (v2.9 drogue support)
    r.pc_valid = out.pc_valid ? 1 : 0; r.mpool = eng.mpool;   // v2.10
    r.photo_V = in.photo_V; r.fa1 = out.fa1; r.fault2 = out.fault2; r.hbleed2 = out.hbleed2; r.purge_flow_ms = out.purge_flow_ms;   // v2.10
    r.ls_flags = (out.light_spike.open ? 1 : 0) | (out.light_spike.done ? 2 : 0) | (out.light_spike.lit ? 4 : 0) |
                 (out.light_spike_event ? 8 : 0) | (out.light_spike.closed_by_exit ? 16 : 0) |
                 (out.light_spike.overrange ? 32 : 0) | (out.light_spike.abovefs ? 128 : 0);   // v2.11: b5 over-range, b7 above FS (log v12)
    r.pc_raw_V = in.pc_raw_V; r.ovr_flags = out.ovr_flags; r.ovp_vf = ovp_vf; r.Pc_face = pc_s1_;   // v2.11
    r.cmd_refused = out.cmd_refused;
    if (fa1_t0 >= 0.0 && t - fa1_t0 < 0.027) r.Pc = pc_ch_ms_max_;   // v2.11: the replayed chamber pressure (ms maximum) while it runs
    if (gop && gop_t0 >= 0.0 && t >= gop_t0 - 1e-3 && t - gop_t0 < 0.6) r.Pc = pc_ch_ms_max_;   // v2.11 S6R: the event head pressure (ms max)
    rec_.push_back(r);
  }
  t += 1e-3; ++ms_;
}

void Sim::writeCsv(const std::string& fn, double t0, double t1) const {
  // v2.11 disk budget (lead brief 2026-10-20: per-case summaries, raw traces only for failing / bounding cases): SIL_NO_CSV=1 skips
  // every time-history CSV of this process (the JSON summaries and the run log are unchanged)
  if (const char* e = std::getenv("SIL_NO_CSV")) if (e[0] == '1') return;
  std::ofstream f(fn);
  f << "t,thr_cmd,F,F_est,Pc,Pc_meas,Pc_sp,x,x_cmd,x_ff,integ,band,ptank,pfeed,mox,mf,of,ga_cmd,ga,gb_cmd,gb,vbat,i_tot,mv,crank_deg,"
       "Fnet_pintle,Tservo_pintle,us_pintle,state,abort,faults,torch,ignited,spark,sol1,sol4,sol5,arm_bus,ovp_ok,gas_T,us_mv_opener,"
       "v_pintle,i_pintle,noprog,jam_kind,Pc_xdcr,sol2,P_torch,ptorch_in,prail_V,preg_V,mv_latch_hw,ltc_gate,torch_ok,lockout,seat_wait,"
       "mvap,vap_left_cc,ox_unlit_start,ign_rule,ign_lift_t,relight_direct,s1_fault,s1_dp,seg_valid,seg_primed,relight_block,relight_worst,"
       "mode_stand,fc_thr_fresh,relight_state,seg_vapour,tank_hot,tank_T,P_mid,mdot_bleed,mvap_bleed,hb_io,ign_det,ign_ref,ign_rise,"
       "flame_ratio,pc_map,a7_tlmf,pc_valid,ls_flags,mpool,photo_V,fa1,fault2,hbleed2,purge_flow_ms,pc_raw_V,ovr_flags,ovp_vf,Pc_face,cmd_refused\n";   // v2.10 columns appended   // a7_tlmf: b0-b1 a7 phase, b2 A7 flag, b3 A7 event, b4-b7 tlmf::
  char b[1600];
  for (const Rec& r : rec_) {
    if (r.t < t0 - 1e-9 || r.t > t1 + 1e-9) continue;   // v2.11 optional window
    std::snprintf(b, sizeof b, "%.4f,%.2f,%.3f,%.3f,%.0f,%.0f,%.0f,%.4e,%.4e,%.4e,%.4e,%.0f,%.0f,%.0f,%.5f,%.5f,%.3f,%.5f,%.5f,%.5f,%.5f,"
                  "%.3f,%.3f,%.3f,%.3f,%.2f,%.4f,%.2f,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.1f,%.1f,%.3f,%.3f,%.4f,%d,%.0f,"
                  "%d,%.0f,%.0f,%.3f,%.3f,%d,%d,%d,%d,%d,%.5f,%.3f,%.6f,%d,%.4f,%d,%d,%.0f,%d,%d,%d,%.3f,%d,%.0f,%d,%d,%d,%.2f,"
                  "%.0f,%.5f,%.5f,%d,%d,%.0f,%.0f,%.3f,%.0f,%d,%d,%d,%.6f,%.4f,%d,%d,%d,%d,%.4f,%d,%.4f,%.0f,%d\n",
                  r.t, r.thr_cmd, r.F, r.F_est, r.Pc, r.Pc_meas, r.Pc_sp, r.x, r.x_cmd, r.x_ff, r.integ, r.band, r.ptank, r.pfeed,
                  r.mox, r.mf, r.of, r.ga_cmd, r.ga, r.gb_cmd, r.gb, r.vbat, r.i_tot, r.mv, r.crank_deg, r.Fnet_pintle,
                  r.Tservo_pintle, r.us_pintle, r.state, r.abort, r.faults, r.torch, r.ignited, r.spark, r.sol1, r.sol4, r.sol5,
                  r.arm_bus, r.ovp_ok, r.gasT, r.us_mvop, r.v_pint, r.i_pint, r.noprog, r.jam_kind, r.Pc_xdcr,
                  r.sol2, r.ptorch, r.ptorch_in, r.prail, r.preg, r.mv_latch_hw, r.ltc_gate, r.torch_ok, r.lockout, r.seat_wait,
                  r.mvap, r.vap_cc, r.ox_unlit, r.ign_rule, r.ign_lift_t, r.relight_direct, r.s1_fault, r.s1_dp, r.seg_valid, r.seg_primed,
                  r.relight_block, r.relight_worst, r.mode_stand, r.fc_thr, r.rstate, r.segvap, r.tank_hot, r.tank_T,
                  r.pmid, r.mdot_hb, r.mvap_hb, r.hb_io, r.ign_det, r.ign_ref, r.ign_rise, r.flame_ratio, r.pc_map, r.a7,
                  r.pc_valid, r.ls_flags, r.mpool, r.photo_V, r.fa1, r.fault2, r.hbleed2, r.purge_flow_ms,
                  r.pc_raw_V, r.ovr_flags, r.ovp_vf, r.Pc_face, r.cmd_refused);
    f << b;
  }
}

}  // namespace sil
