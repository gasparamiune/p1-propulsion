// [v2.11 2026-10-13, LEAD CHANGELOG 203/205: non-sticky flight HIGH over-range + above-FS flag, FA-1 ride-through CANDIDATE (default OFF), unpurged flight RELIGHT guard (UNPURGED), log v12; full list in the ELEC-V211 handback]
// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175/181/186: state machine and monitors for the v2.10 rules; unpurged RELIGHT (integrated purge deleted); PC_VALID and encoder outputs; R2 command hold + Cmd::DROGUE (186 (2)); full list in 06-electronics/REPORT-v2.10-HANDBACK.md] ARGOS engine ECU - state machine, sequencing, safety monitor (v2.9, 2026-10-13: LEAD decisions - light detection by the ADOPTED
// relative rule (Combustion ignition_detect_v2p4: pre-lift baseline P0 over [E1 - 20 ms, E1] checked against the auto-zero ambient,
// rise >= 0.8 bar on filtered AND raw for 10 ms, floor 1.8 bar abs; kIgnitionPcAbs withdrawn); A3 flame-out relative to P0 on the lift
// map (k 0.40, 20 ms); A5 ignition-hold over-pressure 8.0 bar abs / 5 ms; A7 map criterion armed from E1 with the lit-start band to E3;
// CF-3 temperature-dependent ignition-lift table (37.4 g/s); head-end bleed provision for A1 (pad BIT in PREPRESS, PURGE = relight
// forced purge with the pintle seated and both bleed valves open, V1 confirmed closed by P_mid before the lift, leak monitor,
// Abort::BLEED_FAULT); coast re-zero of Pc and P_torch. v2.8.2: GNC review REV-GNC-1 RG-08 - a pintle-position
// anomaly in the coast (encoder invalid on any COAST tick, or encoder lift above 0.10 mm for 20 consecutive ticks) latches TLM_RELIGHT
// UNKNOWN / UNPRIMED and the prep path until the next confirmed light or DISARM in SAFE (EVENT COAST_PINTLE, log v9 seq3_flags b7).
// v2.8.1: stand windows R1 = R2 = 0.35 s strap-keyed, over-thrust frame rule adopted, ABORT exit needs a valid Pc.
// v2.8, 2026-10-13, LEAD decisions of the day: relight = RELIGHT at
// T_fire with the NC valve opened at E0 together with the torch and the ignition lift at E1 (torch confirmation), no PREPRESS on a
// primed segment; ignition window W from the lift command (stand R1-R4, flight 0.65 s on every relight); torch gate 0.16 s; lift from
// a lift-vs-T_tank table; S1 relief monitor with an in-situ zero; provisional OVER_THRUST abort on the FC estimate (Pc sensor lost,
// flight); explicit mode strap (MODE_MISMATCH inhibit); case over-temperature 448.15 K armed with the MV open (start refused above
// 433.15 K); bay-temperature ARM inhibit; TLM_RELIGHT status; PREPRESS refused in COAST. v2.8 final (LEAD decisions of 2026-10-13 on
// COMB v2.4 / GNC v3 / MECH): seat timeout 0.30 s; any abort -> next attempt is a vapour-segment start (NV b3: TLM never PRIMED, prep
// path, stand R2/R3 logic); tank interlock 24 C (wall DS18B20 + Tsat(P_tank)); TLM_RELIGHT PRIMED/UNPRIMED/UNKNOWN valid only after the
// MECO valve closure; RUN-entry Pc reference capped at the map setpoint (SIL v2.8 S6: a late light with a 20-28 bar spike gave a false
// FLAMEOUT). v2.7, 2026-10-13: Combustion review fold-in (RC-01/RC-03/C7, LEAD
// decisions 2026-10-13) - torch-flame gate on P_torch, torch valves closed on the light-confirmation event, abort matrix (every abort
// drops the NC valve at once, pintle closed in parallel), seat-confirmed normal shutdown, relight lockout (no in-flight retry), C7
// check extension, pintle-rail loss -> PINTLE_FAULT, Pc-sensor loss aborts RUN on the stand only; v2.6, 2026-10-12: pintle
// stall/tracking monitor with back-off,
// jam events and the MAINT_JAM inhibit, HV69 pulse calibration as a parameter, unlit pintle capped at the ignition lift, MV
// closed through the MECO coast and ramped on every opening (LEAD rules); v2.5: Combustion v2.1 start sequence - propane off
// at 0.40 s or Pc, ignition check 3.0 bar abs at 0.35 s, 2500 N/s start ramp, vented-chamber check before the torch;
// v2.2: chamber over-pressure, firmware + hardware)
#include "engine_ecu.h"
#include "n2o_sat_table.h"
#include "sensor_scale.h"   // v2.10 RE-19 ladder::nominalRatio (pad-BIT harness step)
#include <climits>
#include <cmath>
#include <limits>

namespace ecu {

const char* stateName(State s) {
  switch (s) {
    case State::SAFE: return "SAFE"; case State::ARMED: return "ARMED"; case State::PREPRESS: return "PREPRESS";
    case State::IGNITION: return "IGNITION"; case State::RUN: return "RUN"; case State::SHUTDOWN: return "SHUTDOWN";
    case State::PURGE: return "PURGE"; case State::COAST: return "COAST"; case State::ABORT: return "ABORT";
  }
  return "?";
}
const char* abortName(Abort a) {
  static const char* n[] = {"NONE", "CMD", "HARD_START", "NO_IGNITION", "FLAMEOUT", "PC_BAND", "OVER_TEMP",
                            "TANK_OVERPRESSURE", "GIMBAL_FAULT", "PINTLE_FAULT", "LINK_LOST", "PREPRESS_FAIL",
                            "PC_SENSOR", "BATT_LOW", "MV_FAULT", "ARM_LOST", "WATCHDOG", "PC_OVERPRESSURE",
                            "HW_OVERPRESSURE", "TVC_SUPPLY", "OVERCURRENT", "MAINT_JAM", "TORCH_FAULT", "RELIGHT_LOCKOUT",
                            "OVER_THRUST", "MODE_MISMATCH", "BAY_HOT", "TANK_HOT", "BLEED_FAULT", "TORCH_LOST",
                            "TANK_COLD"};
  const unsigned i = static_cast<unsigned>(a);
  return i < sizeof(n) / sizeof(n[0]) ? n[i] : "?";
}

using namespace cfg;

void EngineEcu::init(double t) {
  st_ = State::SAFE; t_state_ = t; t_now_ = t; abort_ = Abort::NONE; abort_latched_ = false;
  pc_lpf_.setup(kPcFilterFc_Hz, kDt_s);
  pc_ref_lpf_.setup(4.0f, kDt_s);   // expected closed-loop Pc response (~40 ms) for band/flameout checks
  pfeed_lpf_.setup(50.0f, kDt_s);
  ptank_lpf_.setup(5.0f, kDt_s);
  pintle_rl_.reset(0); pintle_cmd_ = 0;
  pintleMonReset(); pint_backoff_ = false; pint_kind_ = jam::NONE; safe_chk_ = false;   // v2.6 (the NV jam flag arrives as an input)
  jam_ev_ = PintleJamEvent(); jam_event_ = false; jam_since_clear_ = false; maint_clear_ = false; jam_count_ = 0; clear_jam_refused_ = 0;
  const float z[2] = {0, 0};
  tvc_.reset(z);
  tvc_.setNotch(kGimbalNotchEnabled, kGimbalNotchHz, kGimbalNotchQ, kGimbalNotchDepth_dB, kDt_s);   // v2.4 ENG-07d
  sat_.reset(); sat_flags_ = 0;
  starts_ = 0; faults_ = 0; mv_latch_ = false; mv_cocking_ = false; vent_cmd_ = false;
  supply_.reset(); p_sup_set_.reset(); p_sup_clr_.reset(); p_efuse_.reset(); tvc_sup_deg_ = false; heater_permit_ = false;
  // v2.7 (the non-volatile relight lockout arrives as an input; the RAM copy starts clear)
  torch_ok_ = false; torch_ok_n_ = 0; torch_closed_ = false; bypass_armed_ = false; bypass_start_ = false;
  // v2.8
  ign_w_s_ = 0.0f; ign_rule_ = rule::NONE; t_lift_ = -1.0; ign_lift_m_ = 0.0f; superheat_now_ = superheat_e0_ = false; r4_ok_now_ = true;
  ttank_ok_ = false; ttank_K_ = 293.15f; relight_direct_ = false; mv_open_seen_ = false;
  mode_stand_ = false; mode_mismatch_ = false; mode_mismatch_prev_ = false; stand_ = false;
  ign_refused_r4_ = 0; ign_refused_hot_ = 0; prepress_refused_ = 0; ign_refused_bay_ = 0; cmd_refused_ = refuse::NONE; cmd_refused_event_ = false;
  s1_zero_ok_ = false; s1_fault_ = false; s1_event_ = false; s1_zero_ = 0.0f; s1_acc_ = 0.0f; s1_dp_ = 0.0f; s1_n_ = 0;
  t_mv_open_sw_ = -1.0; s1_coast_zero_done_ = false; p_s1_.reset();
  // v2.8 final (the non-volatile vapour-segment flag b3 arrives as an input; the RAM copy starts clear)
  seg_vap_ = false; seg_vap_event_ = false; seg_vap_clear_ = false; seg_vap_e0_ = false; seg_vap_now_ = false; meco_closed_ = false;
  tank_T_K_ = std::numeric_limits<float>::quiet_NaN(); tank_hot_ = true; tank_cold_ = true; tank_cold_relight_ = false; tank_xcheck_ = false; tank_hot_relight_ = false; ign_refused_tank_ = 0;
  fc_thr_N_ = 0.0f; fc_thr_ok_ = false; t_fc_thr_ = -1e9; overthr_n_ = 0;
  ptorch_zero_ = 0.0f; ptorch_zero_acc_ = 0.0f; ptorch_zero_n_ = 0; torch_low_seen_ = false;
  lockout_ = false; lockout_event_ = false; lockout_clear_ = false; lit_since_boot_ = false; clear_lockout_refused_ = 0;
  sh_open_ = false; sh_event_ = false; sh_boot_seen_ = false; t_sh_ = -1e9;   // v2.10 safing hold (NV b4 read at the first step)
  lit_session_ = false; lit_session_event_ = false; lit_session_close_ = false;
  mv_seat_wait_ = false; mv_seat_timeout_ = false; seat_n_ = 0; prail_lost_ = false; t_bus_on_ = -1.0;
  p_prail_.reset(); p_pcsens_.reset();
  coast_enc_lost_ = false; coast_pint_open_ = false; coast_open_n_ = 0; coast_anom_event_ = 0;   // v2.8.2 RG-08
  // v2.9
  ign_ok_n_ = 0; ignDetReset();
  pc_map_lpf_.setup(1.0f / (6.2831853f * kFlameoutMapTau_s), kDt_s); pc_map_lpf_.reset(ValveMap::pcForLift(0.0f, 45.0e5f));
  pc_map_f_ = std::numeric_limits<float>::quiet_NaN(); pc_map_lo_ = pc_map_f_; flame_ratio_ = std::numeric_limits<float>::quiet_NaN();
  t_e3_ = -1.0; a7_flag_ = false; a7_event_ = false; a7_phase_ = a7::OFF; p_a7_.reset();
  ls_ = LightSpikeRec{}; ls_event_ = false; ls_t_pk_raw_ = ls_t_pk_filt_ = -1.0;   // v2.10 (A5 p_ihold_ deleted)
  hb_cmd_[0] = hb_cmd_[1] = false; hb_path_ = hb_path_checked_ = hb_closing_ = hb_v1_closed_ = hb_mid_vented_ = false;
  hb_leak_ = hb_path_flag_ = hb_hold_to_ = hb_purge_enc_ = hb_bit_pass_ = false; hb_bit_ = hb::BIT_NONE; hb_event_ = hb::EV_NONE;
  t_hb_bit_ = -1.0; hb_bit_match_n_ = 0; hb_bit_step_ = -1; hb_conf_n_ = 0; p_hb_leak_.reset();
  purge_start_ = purge_ign_ = false; purge_open_n_ = 0;
  t_hb_ready_ = t_hb_v2open_ = t_hb_flow0_ = t_hb_v1c_ = t_hb_v2c_ = t_hb_both_ = -1.0; hb_path_n_ = hb_hold_n_ = 0;   // v2.10 purge
  hb_vent_ok_ = hb_hold_ok_ = hb_close_done_ = hb_bleed_fault_ = hb_flow_event_ = false; hb_flow_s_ = -1.0f; hb2_ = 0;
  photo_dark_ = 0.0f; photo_dark_init_ = photo_dark_seen_ = false; both_ok_n_ = 0; p_torch_loss_.reset();   // v2.10 FA-1
  fa1_super_ = fa1_both_dark_ = fa1_pt_lit_ = fa1_ph_lit_ = false; photo_run_ref_ = 0.0f; photo_run_ref_ok_ = false;
  p_photo_fo_.reset(); fo_opt_armed_ = false; fo_view_n_ = 0; prop_bs_n_ = 0; f2_ = f2_prev_ = 0; lift_clamp_now_ = false;
  st_out_prev_ = State::SAFE; t_state_ms_ = 0;
  pc_zero_arm_ = 0.0f; ptorch_zero_arm_ = 0.0f; rz_acc_ = rz_acc_t_ = 0.0; rz_n_ = rz_n_t_ = 0;
  rz_done_ = rz_applied_ = rz_event_ = rz_rejected_ = false; rz_shift_ = 0.0f;
  rz2_n_ = rz2_n_t_ = 0; rz2_acc_ = rz2_acc_t_ = 0.0; rz2_have_ = false; t_rz2_end_ = -1.0;   // v2.10 RE-07
}

// v2.9 light detection, LEAD-adopted relative rule (config.h 'light detection' block). ignDetect() runs once per IGNITION tick BEFORE the
// lift decision of that tick, so the ring holds the ticks up to and including the lift-command tick E1 (the pintle has not moved yet in the
// measured Pc): P0 = mean over [E1 - 20 ms, E1]. P0 is fixed on the first tick after E1 and checked against the auto-zero ambient. The
// legacy absolute rule (v2.6-v2.8.3: filtered AND raw above kIgnitionDetectAbs_Pa, 5 ticks) runs only when ign_detect_relative is false.
void EngineEcu::ignDetReset() {
  const float nan = std::numeric_limits<float>::quiet_NaN();
  ign_pre_i_ = 0; ign_pre_n_ = 0; ign_ref_f_ = nan; ign_ref_r_ = nan; ign_rise_f_ = nan;
  rise_now_ = rise_held_ = rise_held_t_ = rise_seen_lit_ = false;
  ign_det_ = static_cast<uint8_t>((ign_detect_relative ? det::RELATIVE : 0u) | (rz_applied_ ? det::REZERO : 0u));
}

bool EngineEcu::ignDetect(const Inputs& in, double t) {
  const float pc_raw_g = in.pc_Pa - pc_zero_;     // raw (1 kHz decimated) gauge, zeroed
  const float pc_abs = pc_f_ + pamb_Pa;
  if (!ign_detect_relative) {                     // legacy rule (comparison runs only; kIgnitionPcAbs WITHDRAWN, LEAD 2026-10-13)
    ign_ok_n_ = (pc_abs > kIgnitionDetectAbs_Pa && pc_raw_g + pamb_Pa > kIgnitionDetectAbs_Pa) ? ign_ok_n_ + 1 : 0;
    return ign_ok_n_ >= kIgnitionConfirmN;
  }
  if (t_lift_ < 0.0) {                            // up to E1: collect P0 (pintle seated, no main N2O: no light possible)
    ign_pre_f_[ign_pre_i_] = pc_f_; ign_pre_r_[ign_pre_i_] = pc_raw_g;
    ign_pre_i_ = (ign_pre_i_ + 1) % kIgnPreN;
    if (ign_pre_n_ < kIgnPreN) ++ign_pre_n_;
    ign_ok_n_ = 0;
    return false;
  }
  if (!(ign_det_ & det::PRE_REF)) {
    double sf = 0.0, sr = 0.0;
    for (int k = 0; k < ign_pre_n_; ++k) { sf += ign_pre_f_[k]; sr += ign_pre_r_[k]; }
    const float f0 = ign_pre_n_ > 0 ? static_cast<float>(sf / ign_pre_n_) : 0.0f;
    const float r0 = ign_pre_n_ > 0 ? static_cast<float>(sr / ign_pre_n_) : 0.0f;
    // LEAD: baseline checked against the auto-zero ambient within residual + 0.1 bar. v2.10 (LEAD REV-ELEC-1 RE-02): one-sided -
    // HIGH side keeps the MEASURED P0 (never ambient: zeroing a positive offset lowered the bar for a false light) and flags BASE_HIGH
    // (the pad / stand lift was already refused in IGNITION; the A1 relight proceeds on the measured P0); LOW side P0 := 0 (ambient)
    if (ign_pre_n_ == 0 || !std::isfinite(f0)) { ign_ref_f_ = 0.0f; ign_ref_r_ = 0.0f; ign_det_ |= det::BASE_AMB; }
    else if (f0 > kIgnBaseCheck_Pa) { ign_ref_f_ = f0; ign_ref_r_ = r0; f2_ |= f2::BASE_HIGH; }
    else if (f0 < -kIgnBaseCheck_Pa) { ign_ref_f_ = 0.0f; ign_ref_r_ = 0.0f; ign_det_ |= det::BASE_AMB; }
    else { ign_ref_f_ = f0; ign_ref_r_ = r0; }
    ign_det_ |= det::PRE_REF;
  }
  ign_rise_f_ = pc_f_ - ign_ref_f_;
  const bool floor_ok = pc_abs >= kIgnFloorAbs_Pa && pc_raw_g + pamb_Pa >= kIgnFloorAbs_Pa;
  const bool rise = ign_rise_f_ >= kIgnRise_Pa && (pc_raw_g - ign_ref_r_) >= kIgnRise_Pa;
  ign_det_ = static_cast<uint8_t>((ign_det_ & ~(det::FLOOR | det::RISE)) | (floor_ok ? det::FLOOR : 0u) | (rise ? det::RISE : 0u));
  ign_ok_n_ = (floor_ok && rise) ? ign_ok_n_ + 1 : 0;
  if (ign_ok_n_ >= kIgnConfirmRelN) { ign_det_ |= det::LIT; return true; }
  return false;
}

// v2.9 drogue-release support (config.h kDrogueRiseHold_s, types.h tlmf::). Called once per tick after the state logic. RISE_NOW (b5)
// is the light rule's term (filtered AND raw over P0), evaluated in IGNITION after E1 and in RUN. v2.10 (LEAD CHANGELOG 156): RISE_HELD
// (b6) and RISE_HELD_T (b7) run on the FILTERED-ONLY rise term rise_f_now_, so a raw-channel roughness dip cannot clear the hold (E2 itself
// keeps filtered AND raw); RISE_HELD starts at E2 (where both terms hold by construction) and clears at the first tick without the
// filtered rise; RISE_HELD_T latches when it is still held at E2 + kDrogueRiseHold_s. Pc channel invalid (pc_sensor_ok_ false): both
// terms false on that tick (RISE_HELD clears, RISE_HELD_T cannot latch afterwards; the FC interim rule covers that case, CHANGELOG 161).
void EngineEcu::riseTrack(const Inputs& in, double t) {
  const bool active = (st_ == State::IGNITION || st_ == State::RUN) && (ign_det_ & det::PRE_REF) && pc_sensor_ok_ &&
                      std::isfinite(pc_f_) && std::isfinite(ign_ref_f_);
  if (!active) { rise_now_ = false; rise_f_now_ = false; }
  else {
    const float raw_g = in.pc_Pa - pc_zero_;
    rise_f_now_ = (pc_f_ - ign_ref_f_) >= kIgnRise_Pa;                      // v2.10: filtered only (b6, b7)
    rise_now_ = rise_f_now_ && (raw_g - ign_ref_r_) >= kIgnRise_Pa;         // light-rule term, filtered AND raw (b5)
  }
  if (!(ign_det_ & det::LIT)) return;
  if (!rise_seen_lit_) { rise_seen_lit_ = true; rise_held_ = rise_f_now_; }        // E2 tick
  else if (!rise_f_now_) rise_held_ = false;
  if (rise_held_ && t - t_lit_ + kTimeEps_s >= kDrogueRiseHold_s) rise_held_t_ = true;
}

// v2.10 LIGHT_SPIKE record (config.h kLightSpike*, types.h LightSpikeRec; replaces the deleted A5 abort). Called once per tick after the
// state logic (after riseTrack). Opens at E1 of this start; samples every tick while open (the closing tick included); closes at
// E2 + kLightSpikeWin_s or on the first tick outside IGNITION/RUN, with a one-tick EVENT pulse. No action is attached to the record.
void EngineEcu::lightSpikeTrack(const Inputs& in, double t) {
  if (!ls_.open) {
    if (ls_.done || st_ != State::IGNITION || t_lift_ < 0.0) return;
    ls_.open = true; ls_t_pk_raw_ = ls_t_pk_filt_ = -1.0;
  }
  if ((ign_det_ & det::LIT) && !ls_.lit) {
    ls_.lit = true;
    ls_.t_light_s = static_cast<float>(t_lit_ - (kIgnConfirmRelN - 1) * static_cast<double>(kDt_s) - t_lift_);
  }
  if (in.pc_raw_V > kPcSensorMin_V && std::isfinite(in.pc_Pa) && std::isfinite(pc_f_)) {   // LOW invalid skipped; HIGH over-range counts
    const float raw_abs = in.pc_Pa - pc_zero_ + pamb_Pa, filt_abs = pc_f_ + pamb_Pa;
    if (in.pc_raw_V >= kPcSensorMax_V) ls_.overrange = true;
    if (in.pc_raw_V >= kPcAboveFs_V) ls_.abovefs = true;                                    // v2.11 (LEAD 203 (1)(a)) above full scale
    if (!(raw_abs <= ls_.peak_raw_Pa)) { ls_.peak_raw_Pa = raw_abs; ls_t_pk_raw_ = t; }     // NaN-safe: the first sample sets it
    if (!(filt_abs <= ls_.peak_filt_Pa)) { ls_.peak_filt_Pa = filt_abs; ls_t_pk_filt_ = t; }
    const bool explained = pc_map_now_ >= kLightSpikeLoAbs_Pa;   // the lit map at the lift reaches 8 bar (start ramp): not a spike
    const float dt = kDt_s;
    if (raw_abs > kLightSpikeLoAbs_Pa || filt_abs > kLightSpikeLoAbs_Pa) {
      if (explained) ls_.masked = true;
      else { if (raw_abs > kLightSpikeLoAbs_Pa) ls_.t8_raw_s += dt; if (filt_abs > kLightSpikeLoAbs_Pa) ls_.t8_filt_s += dt; }
    }
    if (raw_abs > kLightSpikeHiAbs_Pa) ls_.t30_raw_s += dt;
    if (filt_abs > kLightSpikeHiAbs_Pa) ls_.t30_filt_s += dt;
  }
  const bool burning = st_ == State::IGNITION || st_ == State::RUN;
  const bool win_end = ls_.lit && t - t_lit_ + kTimeEps_s >= kLightSpikeWin_s;
  if (burning && !win_end) return;
  ls_.open = false; ls_.done = true; ls_.closed_by_exit = !win_end; ls_event_ = true;
  const double t0 = ls_.lit ? t_lit_ - (kIgnConfirmRelN - 1) * static_cast<double>(kDt_s) : t_lift_;
  if (ls_t_pk_raw_ >= 0.0) ls_.t_peak_raw_s = static_cast<float>(ls_t_pk_raw_ - t0);
  if (ls_t_pk_filt_ >= 0.0) ls_.t_peak_filt_s = static_cast<float>(ls_t_pk_filt_ - t0);
}

// v2.9 A3 relative flame-out, A7 map criterion and E3 (config.h blocks 'A3' / 'A7'); called from monitors() with the Pc channel valid.
// Pc_map = lit-map Pc at the encoder lift (commanded lift if the encoder is invalid), lagged by kFlameoutMapTau_s. Baseline = P0 of the
// light rule of this start (absolute: P0 + ambient).
void EngineEcu::startMonitors(const Inputs& in, double t, bool* aborted) {
  *aborted = false;
  const float nan = std::numeric_limits<float>::quiet_NaN();
  const float pc_abs = pc_f_ + pamb_Pa;
  const bool run = st_ == State::RUN, hold = st_ == State::IGNITION && t_lift_ >= 0.0;
  const float lift = in.pintle_meas_valid ? in.pintle_meas_m : pintle_cmd_;
  const float map_now = ValveMap::pcForLift(std::fmax(lift, 0.0f), ptank_lpf_.y + pamb_Pa);
  pc_map_f_ = pc_map_lpf_.step(map_now);
  // Expected-Pc envelope [mlo, mhi] = [min, max] of the lagged and the instantaneous map. A healthy chamber follows the lift with the
  // fill lag, so on a throttle-up it lies between the lagged and the instantaneous map, and on a throttle-down (setpoint slew 250 bar/s)
  // it follows the instantaneous map while the 40 ms lagged map stays up to ~10 bar higher: an A3 denominator on the lagged map alone
  // reads a healthy 500 -> 62.5 N step as a flame-out (ratio ~0.2; test_core RigP follower, v2.9 development finding). A3 therefore
  // divides by mlo (the lower expectation: identical at a steady lift, never trips on the transient of either direction) and the A7
  // band spans [mlo, mhi]. A flame-out with the lift held or opening still trips (mlo = the map before the loss).
  const float mlo = std::fmin(pc_map_f_, map_now), mhi = std::fmax(pc_map_f_, map_now);
  pc_map_lo_ = mlo; pc_map_now_ = map_now;
  flame_ratio_ = nan; a7_phase_ = a7::OFF;
  if (!(run || hold) || !pc_sensor_ok_) { p_flame_.reset(); p_a7_.reset(); return; }
  const float p0 = (std::isfinite(ign_ref_f_) ? ign_ref_f_ : 0.0f) + pamb_Pa;   // baseline, absolute
  float lo = -1e12f, hi = 1e12f;
  if (run) {
    // A3: (Pc - P0) / (Pc_map - P0) < k for kFlameoutTime_s
    const float den = std::fmax(mlo - p0, 0.5e5f);
    flame_ratio_ = (pc_abs - p0) / den;
    if (p_flame_.step(flame_ratio_ < kFlameoutRel, kFlameoutTime_s, kDt_s)) {
      faults_ |= fault::FLAMEOUT; doAbort(Abort::FLAMEOUT, t); *aborted = true; return;
    }
    // E3: start ramp done and Pc within 90 % of the setpoint above P0, or E2 + kE3Max_s
    if (t_e3_ < 0.0) {
      const float sp = pcc_.setpointActive();
      if ((!start_ramp_ && pc_abs >= p0 + 0.9f * (sp - p0)) || t - t_lit_ + kTimeEps_s >= kE3Max_s) { t_e3_ = t; ign_det_ |= det::E3; }
    }
    if (t_e3_ < 0.0) {   // E2 -> E3: lit-start band (low edge = the A3 threshold; top = the start band top or the map, +30 %)
      a7_phase_ = a7::START;
      lo = p0 + kFlameoutRel * (mlo - p0);
      hi = (1.0f + kA7Frac) * std::fmax(mhi, kA7StartHiAbs_Pa);
    } else {             // after E3: lit map band +/-30 % around the [lagged, instantaneous] map envelope
      a7_phase_ = a7::RUN_MAP;
      lo = (1.0f - kA7Frac) * mlo;
      hi = (1.0f + kA7Frac) * mhi;
    }
    // v2.10 RE-12 (LEAD CHANGELOG 166 (7); SIL S15: stand A7 trip rate far above 1 %): high side blanked from E2 to E2 + 0.45 s, stand
    // AND flight, whatever the phase (the pool pushes Pc past 90 % of the setpoint, so E3 and the map band come at E2 + 15-20 ms; a
    // START-only blank left 14 of 38 stand starts tripping). Flight: avoids spending the once-per-burn A7 flag on the pool. Low side (A3
    // and the map low edge), the 30 bar abort and the comparator stay armed.
    if (t - t_lit_ + kTimeEps_s < kA7StartHiBlank_s) hi = 1.0e12f;
  } else {               // E1 -> E2: not below the pre-lift chamber pressure (high side = A5)
    a7_phase_ = a7::HOLD;
    lo = p0 - kA7HoldLow_Pa;
  }
  if (a7_flag_) return;  // flight: flagged once per burn
  if (p_a7_.step(pc_abs < lo || pc_abs > hi, kA7Time_s, kDt_s)) {
    faults_ |= fault::PC_SENSOR; a7_event_ = true;
    if (hold || stand_) { doAbort(Abort::PC_SENSOR, t); *aborted = true; return; }
    a7_flag_ = true;     // flight RUN: flag, burn continues closed loop (LEAD decision pending on an open-loop switch)
  }
}

// v2.9 head-end bleed (LEAD 2026-10-13; config.h 'head-end bleed' block). v2.10: schedule on FLOW time (LEAD CHANGELOG 164)
void EngineEcu::enterPurge(double t, bool auto_ign) {
  // NC valve latch + opener ramp (rule b) from entry, pintle commanded seated. v2.10 FILL STEP: V1 open, V2 closed (no flow; P_mid =
  // P_feed whatever the restriction position); V2 opens on the schedule in State::PURGE
  relight_direct_ = false; mv_latch_ = true; mv_cocking_ = true; mv_ramp_ = kMvRampEveryOpening; t_mv_cmd_ = t;
  mv_open_seen_ = false; prime_slow_ = false; bleed_active_ = false; bleed_checked_ = true;
  purge_ign_ = auto_ign; purge_open_n_ = 0; purge_filled_ = false;
  hb_cmd_[0] = true; hb_cmd_[1] = false; hb_path_ = false; hb_path_checked_ = false; hb_closing_ = false; hb_v1_closed_ = false;
  hb_mid_vented_ = false; p_hb_leak_.reset(); hb_path_n_ = 0; hb_hold_n_ = 0; hb_conf_n_ = 0;
  t_hb_ready_ = t_hb_v2open_ = t_hb_flow0_ = t_hb_v1c_ = t_hb_v2c_ = t_hb_both_ = -1.0;
  hb_vent_ok_ = hb_hold_ok_ = hb_close_done_ = false; hb_flow_s_ = -1.0f; hb2_ = hb2::FILL;
  enter(State::PURGE, t);
}

// v2.10 flow accounting at the V1 close command: flow end = command + kHbleedCloseTime_s; flow start = V2 open command +
// kHbleedOpenTime_s (DERIVED from command times and the measured valve times, not a flow measurement)
void EngineEcu::hbFlowEnd(double t) {
  if (t_hb_flow0_ < 0.0 || t_hb_v1c_ >= 0.0) return;
  t_hb_v1c_ = t;
  hb_flow_s_ = static_cast<float>(std::fmax(0.0, t + kHbleedCloseTime_s - t_hb_flow0_));
  hb2_ |= hb2::FLOW_DONE; hb_flow_event_ = true;
}

// V1 first; V2 stays open so the mid volume vents if (and only if) V1 has closed. v2.10 closure step (vent, then hold test) in
// hbleedStep(); a V2 that is not open (fill step) has nothing to vent: no closure step, the leak monitor stays disarmed
void EngineEcu::hbClose(double t) {
  hbFlowEnd(t);
  hb_cmd_[0] = false;
  hb_closing_ = hb_cmd_[1];
  if (hb_closing_) { t_hb_close_ = t; hb_conf_n_ = 0; hb_hold_n_ = 0; t_hb_v2c_ = -1.0; hb_vent_ok_ = false; hb_hold_ok_ = true; }
}

// v2.10 closure result. CONFIRMED iff the P_mid chain was proven in this purge's fill step, the mid vented through the open V2 and
// stayed low and valid through the hold test after the V2 close command. NOT CONFIRMED: BLEED_FAULT to the FC (flag), the flight
// relight proceeds (LEAD RE-05); the stand aborts BLEED_FAULT. 'forced' = cap or lift deadline ended the step.
void EngineEcu::hbCloseResult(double t, bool forced, bool* aborted) {
  hb_closing_ = false; hb_close_done_ = true; hb_cmd_[1] = false;
  const bool ok = !forced && hb_path_ && hb_vent_ok_ && hb_hold_ok_;
  if (ok) {
    hb_v1_closed_ = true; hb_mid_vented_ = true; p_hb_leak_.reset(); hb2_ |= hb2::CONFIRMED; hbEvent(hb::EV_V1_CLOSED);
    return;
  }
  hb_v1_closed_ = false; hb_mid_vented_ = hb_vent_ok_ && hb_hold_ok_ && !forced; p_hb_leak_.reset();
  hb2_ |= hb2::NOT_CONFIRMED | (!hb_path_ ? hb2::R_CHAIN : 0u) | (!hb_vent_ok_ ? hb2::R_VENT : 0u) |
          ((!hb_hold_ok_ || forced) ? hb2::R_HOLD : 0u);
  faults_ |= fault::MV; hb_bleed_fault_ = true; hbEvent(hb::EV_NOT_CLOSED);
  if (stand_ && st_ != State::ABORT && st_ != State::SAFE) { doAbort(Abort::BLEED_FAULT, t); if (aborted) *aborted = true; }
}

void EngineEcu::hbleedStep(const Inputs& in, double t, bool* aborted) {
  *aborted = false;
  if (!hbleed_fitted) { hb_cmd_[0] = hb_cmd_[1] = false; hb_closing_ = false; return; }
  // v2.10 fill-step path proof: V1 commanded open, V2 commanded closed (no flow): P_mid high and valid for kHbleedConfirmN ticks
  if (st_ == State::PURGE && hb_cmd_[0] && !hb_cmd_[1] && !hb_path_) {
    hb_path_n_ = (in.pmid_valid && in.pmid_hi) ? hb_path_n_ + 1 : 0;
    if (hb_path_n_ >= kHbleedConfirmN) hb_path_ = true;
  }
  // v2.10 hard cap (LEAD CHANGELOG 164 (2)): both valves commanded open together longer than kHbleedCap_s -> both close at once
  if (hb_cmd_[0] && hb_cmd_[1] && hb_bit_step_ < 0) {
    if (t_hb_both_ < 0.0) t_hb_both_ = t;
    else if (t - t_hb_both_ > kHbleedCap_s + kTimeEps_s) {
      hbFlowEnd(t); hb_cmd_[0] = false; hb2_ |= hb2::R_HOLD; hbEvent(hb::EV_CAP);
      hbCloseResult(t, true, aborted);
      return;
    }
  } else t_hb_both_ = -1.0;
  if (hb_closing_) {
    if (hb_cmd_[1]) {   // (1) VENT: V2 open; it closes once V1 had its closing time and the mid reads low, or at the vent limit
      hb_conf_n_ = (in.pmid_valid && !in.pmid_hi) ? hb_conf_n_ + 1 : 0;
      const double tc = t - t_hb_close_;
      const bool vented = hb_conf_n_ >= kHbleedConfirmN;
      if ((vented && tc + kTimeEps_s >= kHbleedCloseTime_s) || tc > kHbleedCloseTime_s + kHbleedVentMax_s + kTimeEps_s) {
        hb_vent_ok_ = vented; hb_cmd_[1] = false; t_hb_v2c_ = t; hb_hold_n_ = 0; hb_hold_ok_ = true;
      }
    } else {            // (2) HOLD TEST: V2 commanded closed; the trapped mid must stay low and valid
      hb_hold_n_ = (!in.pmid_valid || in.pmid_hi) ? hb_hold_n_ + 1 : 0;
      if (hb_hold_n_ >= kHbleedConfirmN) hb_hold_ok_ = false;
      if (!hb_hold_ok_ || t - t_hb_v2c_ + kTimeEps_s >= kHbleedHoldTest_s) hbCloseResult(t, false, aborted);
    }
    return;
  }
  // leak monitor: both commanded closed, the mid last seen vented, not in the pad BIT, valves powered (not SAFE)
  const bool watch = st_ != State::SAFE && !hb_cmd_[0] && !hb_cmd_[1] && hb_mid_vented_ && hb_bit_step_ < 0 && in.pmid_valid;
  if (p_hb_leak_.step(watch && in.pmid_hi, kHbleedLeakTime_s, kDt_s)) {
    faults_ |= fault::MV;
    if (!hb_leak_) { hb_leak_ = true; hbEvent(hb::EV_LEAK); }
    if (stand_ && st_ != State::ABORT) { doAbort(Abort::BLEED_FAULT, t); *aborted = true; }
  }
}

// v2.10 scheduled E0 of the running purge: flow end + kPurgeFlowEndLead_s once the flow timing is known, else the PURGE schedule
double EngineEcu::purgeE0Est(double t) const {
  if (st_ != State::PURGE) return t;
  if (t_hb_v1c_ >= 0.0) return t_hb_v1c_ + kHbleedCloseTime_s + kPurgeFlowEndLead_s;
  if (t_hb_flow0_ >= 0.0) return t_hb_flow0_ + kPurgeFlow_s + kPurgeFlowEndLead_s;
  return std::fmax(t_state_ + kPurgeRelight_s, t + kHbleedOpenTime_s + kPurgeFlow_s + kPurgeFlowEndLead_s);
}

// v2.10 RE-02: the P0 the next tick would compute (same ring, same mean) is above +kIgnBaseCheck_Pa
bool EngineEcu::baseHighNow() const {
  if (ign_pre_n_ == 0) return false;
  double sf = 0.0;
  for (int k = 0; k < ign_pre_n_; ++k) sf += ign_pre_f_[k];
  const float f0 = static_cast<float>(sf / ign_pre_n_);
  return std::isfinite(f0) && f0 > kIgnBaseCheck_Pa;
}

// v2.10 FA-1 photodiode
bool EngineEcu::photoValid(const Inputs& in) const {
  return in.photo_valid && std::isfinite(in.photo_V) && in.photo_V > kPhotoMin_V && in.photo_V < kPhotoMax_V;
}
bool EngineEcu::photoLit(const Inputs& in) const {
  return photoValid(in) && photo_dark_init_ && in.photo_V - photo_dark_ >= kPhotoLitRise_V;
}

// pad BIT (PREPRESS, first start, feed primed, before IGNITION): true while running; *failed -> the caller aborts BLEED_FAULT.
// Step k (kHbleedBitStep_s each) commands (V1, V2) and expects P_mid: S0 (0,1) low, S1 (0,0) low, S2 (1,0) high, S3 (0,0) high,
// S4 (0,1) low; a step passes if the comparator read the expected level (valid) for its last kHbleedBitSettleN ticks.
bool EngineEcu::hbleedBitStep(const Inputs& in, double t, bool* failed) {
  static constexpr bool kV1[5] = {false, false, true, false, false};
  static constexpr bool kV2[5] = {true, false, false, false, true};
  static constexpr bool kHi[5] = {false, false, true, true, false};
  *failed = false;
  if (t_hb_bit_ < 0.0) { t_hb_bit_ = t; hb_bit_step_ = 0; hb_bit_match_n_ = 0; }
  const int k = static_cast<int>((t - t_hb_bit_ + kTimeEps_s) / kHbleedBitStep_s);
  if (k != hb_bit_step_) {   // boundary: judge the step that just ended
    if (hb_bit_match_n_ < kHbleedBitSettleN) {
      hb_bit_ = static_cast<uint8_t>(hb::BIT_FAIL | hb_bit_step_);
      hb_cmd_[0] = hb_cmd_[1] = false; hb_bit_step_ = -1; hb_mid_vented_ = false;
      hbEvent(hb::EV_BIT_FAIL); *failed = true;
      return false;
    }
    hb_bit_match_n_ = 0; hb_bit_step_ = k;
    if (k >= 5) {
      hb_bit_ = hb::BIT_PASS; hb_bit_pass_ = true; hb_cmd_[0] = hb_cmd_[1] = false; hb_bit_step_ = -1; hb_mid_vented_ = true;
      p_hb_leak_.reset(); hbEvent(hb::EV_BIT_PASS);
      return false;
    }
  }
  hb_bit_ = static_cast<uint8_t>(1 + hb_bit_step_);
  hb_cmd_[0] = kV1[hb_bit_step_]; hb_cmd_[1] = kV2[hb_bit_step_];
  // v2.10 RE-19 harness-resistance step: the raw ladder ratio within kLadderBitTol of the nominal ratio of the expected code
  const float nom = ladder::nominalRatio(in.mv_open_sw, in.mv_closed_sw, kHi[hb_bit_step_]);
  const bool harness = std::isfinite(in.mv_ladder_ratio) && std::isfinite(nom) && std::fabs(in.mv_ladder_ratio - nom) <= kLadderBitTol;
  hb_bit_match_n_ = (in.pmid_valid && in.pmid_hi == kHi[hb_bit_step_] && harness) ? hb_bit_match_n_ + 1 : 0;
  return true;
}

// v2.9 coast re-zero (config.h 'coast re-zero' block): one block per coast, from kPcRezeroFrom_s after COAST entry, while the chamber
// can only be vented (NC valve shown closed and unlatched, pintle commanded and read seated, bleed valves closed, Pc channel valid).
void EngineEcu::rezeroStep(const Inputs& in, double t) {
  if (st_ != State::COAST) {
    rz_done_ = false; rz_n_ = rz_n_t_ = 0; rz_acc_ = rz_acc_t_ = 0.0;
    rz2_n_ = rz2_n_t_ = 0; rz2_acc_ = rz2_acc_t_ = 0.0; rz2_have_ = false; t_rz2_end_ = -1.0;
    return;
  }
  if (!pc_coast_rezero || t - t_coast_ + kTimeEps_s < kPcRezeroFrom_s) return;
  const bool quiet = pc_sensor_ok_ && !mv_latch_ && in.mv_closed_sw && !in.mv_open_sw && pintle_cmd_ <= 0.0f && in.pintle_meas_valid &&
                     in.pintle_meas_m <= kPintleSeatConfirm_m && !hb_cmd_[0] && !hb_cmd_[1];
  if (rz_done_) {   // v2.10 RE-07: consecutive quiet blocks for the second re-zero (applied by rezero2Apply at the command)
    if (!quiet) { rz2_n_ = rz2_n_t_ = 0; rz2_acc_ = rz2_acc_t_ = 0.0; return; }
    if (rz2_n_ == 0) { rz2_min_ = pc_f_; rz2_max_ = pc_f_; }
    rz2_acc_ += in.pc_Pa; ++rz2_n_;
    rz2_min_ = std::fmin(rz2_min_, pc_f_); rz2_max_ = std::fmax(rz2_max_, pc_f_);
    if (in.ptorch_valid) { rz2_acc_t_ += in.ptorch_Pa; ++rz2_n_t_; }
    if (rz2_n_ >= kPcRezeroN) {
      rz2_have_ = true; t_rz2_end_ = t;
      rz2_z_ = static_cast<float>(rz2_acc_ / rz2_n_); rz2_span_ = rz2_max_ - rz2_min_;
      rz2_zt_ok_ = rz2_n_t_ >= kPcRezeroN / 2; rz2_zt_ = rz2_zt_ok_ ? static_cast<float>(rz2_acc_t_ / rz2_n_t_) : 0.0f;
      rz2_n_ = rz2_n_t_ = 0; rz2_acc_ = rz2_acc_t_ = 0.0;
    }
    return;
  }
  if (!quiet) { rz_n_ = rz_n_t_ = 0; rz_acc_ = rz_acc_t_ = 0.0; return; }   // restart the block
  if (rz_n_ == 0) { rz_min_ = pc_f_; rz_max_ = pc_f_; }
  rz_acc_ += in.pc_Pa; ++rz_n_;
  rz_min_ = std::fmin(rz_min_, pc_f_); rz_max_ = std::fmax(rz_max_, pc_f_);
  if (in.ptorch_valid) { rz_acc_t_ += in.ptorch_Pa; ++rz_n_t_; }
  if (rz_n_ < kPcRezeroN) return;
  rz_done_ = true;
  const float z = static_cast<float>(rz_acc_ / rz_n_);
  rz_shift_ = z - pc_zero_;
  if (rz_max_ - rz_min_ <= kPcRezeroSpan_Pa && std::fabs(z - pc_zero_arm_) <= kPcRezeroMax_Pa) {
    pc_zero_ = z; pc_f_ -= rz_shift_; pc_lpf_.reset(pc_f_);   // filter restarted at the re-zeroed steady value
    rz_applied_ = true; rz_event_ = true; rz_rejected_ = false;
  } else {
    rz_rejected_ = true;
  }
  if (rz_n_t_ >= kPcRezeroN / 2) {
    const float zt = static_cast<float>(rz_acc_t_ / rz_n_t_);
    if (std::fabs(zt - ptorch_zero_arm_) <= kPcRezeroMax_Pa) ptorch_zero_ = zt;
  }
}

// v2.10 RE-07 (LEAD CHANGELOG 166 (5)): second re-zero, applied at an accepted-path PURGE / RELIGHT command in COAST before its vented
// check: the latest complete quiet block (ended within kPcRezero2MaxAge_s), steady and within kPcRezeroMax_Pa of the pad (ARM) zero
void EngineEcu::rezero2Apply(double t) {
  if (st_ != State::COAST || !pc_coast_rezero || !rz2_have_ || t - t_rz2_end_ > kPcRezero2MaxAge_s + kTimeEps_s) return;
  rz2_have_ = false;
  const float shift = rz2_z_ - pc_zero_;
  if (rz2_span_ <= kPcRezeroSpan_Pa && std::fabs(rz2_z_ - pc_zero_arm_) <= kPcRezeroMax_Pa) {
    pc_zero_ = rz2_z_; pc_f_ -= shift; pc_lpf_.reset(pc_f_);
    rz_shift_ = shift; rz_applied_ = true; rz_event_ = true; rz_rejected_ = false; f2_ |= f2::REZERO2;
    if (rz2_zt_ok_ && std::fabs(rz2_zt_ - ptorch_zero_arm_) <= kPcRezeroMax_Pa) ptorch_zero_ = rz2_zt_;
  } else {
    rz_rejected_ = true; f2_ |= f2::REZERO2_REJ;
  }
}

// v2.10 RE-07: vented wait (PREPRESS auto-ignite, PURGE -> IGNITION). Stand and pad first start: wait (refusal path unchanged);
// flight relight: flag NOT_VENTED to the FC and proceed
bool EngineEcu::ventGate() {
  if (chamberVented()) return true;
  if (stand_ || starts_ == 0) return false;
  f2_ |= f2::NOT_VENTED;
  return true;
}

// v2.8.2 (GNC REV-GNC-1 RG-08) coast pintle-position anomaly, evaluated on every COAST tick before the commands so that a RELIGHT on
// the same tick and the TLM_RELIGHT status of that tick use the same latches. With the NC valve closed the segment can lose liquid only
// through the pintle seat; a needle off the seat drains it into the vented chamber while P_feed stays near P_sat (saturated vapour
// passes the pressure rule, RG-01). Encoder invalid on a COAST tick: position unknown -> UNKNOWN latch (no persistence: the HAL validity
// is the debounce). Encoder lift above kCoastPintleOpen_m for kCoastPintleOpenN consecutive ticks -> UNPRIMED latch. A larger error
// (above kPintleStallErr_m, 0.15 mm) also trips the stall monitor (PINTLE_FAULT abort after 0.10 s without progress).
void EngineEcu::coastPintleStep(const Inputs& in) {
  if (st_ != State::COAST) { coast_open_n_ = 0; return; }
  if (!in.pintle_meas_valid) {
    coast_open_n_ = 0;
    if (!coast_enc_lost_) { coast_enc_lost_ = true; coast_anom_event_ = 1; }
    return;
  }
  coast_open_n_ = in.pintle_meas_m > kCoastPintleOpen_m ? coast_open_n_ + 1 : 0;
  if (coast_open_n_ >= kCoastPintleOpenN && !coast_pint_open_) { coast_pint_open_ = true; coast_anom_event_ = 2; }
}

// v2.7 relight lockout (LEAD 2026-10-13: no automatic in-flight retry); one-tick event for the HAL's non-volatile copy
void EngineEcu::setLockout() {
  if (!lockout_) { lockout_ = true; lockout_event_ = true; }
}

bool EngineEcu::feedPrimed(const Inputs& in) const {
  if (!in.mv_open_sw) return false;
  // v2.8: an invalid P_feed or P_tank cannot show priming. Only a FLIGHT relight then proceeds on the OPEN switch and the cock time
  // (an abort in flight loses the vehicle); a pad start or a stand relight waits and ends in PREPRESS_FAIL (stand R4 refuses earlier)
  if (!in.pfeed_valid || !in.ptank_valid) return starts_ >= 1 && !stand_;
  return pfeed_lpf_.y > kFeedPrimedFrac * ptank_lpf_.y && ptank_lpf_.y > 5.0e5f;
}

// v2.8 direct relight condition: the valve-to-seat segment holds no gas pocket the opening valve could compress (COMB priming rule:
// P_feed >= kPrimeSlowFrac P_tank, absolute), judged on valid readings only
bool EngineEcu::segmentPrimed(const Inputs& in) const {
  return in.pfeed_valid && in.ptank_valid && ptank_lpf_.y > 5.0e5f &&
         (pfeed_lpf_.y + pamb_Pa) >= kPrimeSlowFrac * (ptank_lpf_.y + pamb_Pa);
}

// v2.8: why an IGNITE/RELIGHT received now would be refused (refuse::NONE = accepted). One function for the command handler and the
// relight-planning status (TLM_RELIGHT), so the FC sees exactly the rule the ECU applies. Order = v2.7 check order.
uint8_t EngineEcu::startBlock(const Inputs& in, double t) const {
  const bool pad_coast = st_ == State::COAST || st_ == State::ARMED;
  const bool pre = pad_coast || st_ == State::PREPRESS;
  if (starts_ >= kMaxStarts) return refuse::MAX_STARTS;
  if (lockoutPending(in)) return refuse::LOCKOUT;
  if (kIgnitionRequiresGimbalNotch && !(tvc_.notchEnabled(0) && tvc_.notchEnabled(1)) && pre) return refuse::NOTCH;
  if (!chamberVented() && pad_coast && (stand_ || starts_ == 0)) return refuse::NOT_VENTED;   // v2.10 RE-07: flight = flag
  if (pre && caseHot(in)) return refuse::CASE_HOT;
  if (pre && starts_ == 0 && bayHot(in)) return refuse::BAY_HOT;
  // v2.8 final tank interlock (LEAD 2026-10-13): pad first start and every stand start; a flight relight is flagged only (step())
  if (pre && tank_hot_ && (starts_ == 0 || stand_)) return refuse::TANK_HOT;
  if (pre && tank_cold_ && (starts_ == 0 || stand_)) return refuse::TANK_COLD;   // v2.10 RE-17
  // R4: stand relights, and (v2.8 final) a stand start after an abort (a vapour-segment start uses the R2/R3 logic)
  if (pre && stand_ && (starts_ >= 1 || segVapourPending(in)) && !r4_ok_now_) return refuse::R4_SENSOR;
  return refuse::NONE;
}

// v2.8 final tank interlock estimate (LEAD 2026-10-13, ENG-12 15-24 C): max of the valid tank-wall DS18B20 and Tsat(P_tank); a valid
// P_tank beyond the saturation table (> 72.0 bar abs) counts as the table's last temperature (309 K, hot). The cross-check flag latches
// when the wall mean and Tsat(P_tank) differ by more than kTankXcheckMax_K (both available).
void EngineEcu::tankUpdate(const Inputs& in, float ptank_abs) {
  float tmax = -1.0f, wsum = 0.0f; int nw = 0;
  for (int k = 0; k < 2; ++k)
    if (in.ttank_wall_valid[k] && std::isfinite(in.ttank_wall_K[k])) { tmax = std::fmax(tmax, in.ttank_wall_K[k]); wsum += in.ttank_wall_K[k]; ++nw; }
  float tsat = 0.0f; bool sat_ok = false;
  if (in.ptank_valid) {
    if (ptank_abs > n2o::kSatPLast_Pa) { tsat = n2o::kTsat_K[n2o::kSatN - 1]; sat_ok = true; }
    else sat_ok = n2o::tsatK(ptank_abs, &tsat);
  }
  if (sat_ok) tmax = std::fmax(tmax, tsat);
  const bool any = nw > 0 || sat_ok;
  tank_T_K_ = any ? tmax : std::numeric_limits<float>::quiet_NaN();
  // v2.10 (LEAD CHANGELOG 172 (4)) guard band: wall and pressure each against their own threshold (config.h: 24 C and 55.277 bar abs
  // minus the channel uncertainty); tmax (telemetry, cross-check) is unchanged
  float wmax = -1.0f;
  for (int k = 0; k < 2; ++k) if (in.ttank_wall_valid[k] && std::isfinite(in.ttank_wall_K[k])) wmax = std::fmax(wmax, in.ttank_wall_K[k]);
  const bool hot_wall = nw > 0 && wmax > kTankIgnMaxWall_K;
  const float p_thr = ptank_cal_ok ? kTankIgnMaxPCal_Pa : kTankIgnMaxP_Pa;
  const bool hot_p = in.ptank_valid && std::isfinite(ptank_abs) && ptank_abs > p_thr;
  tank_hot_ = !any || hot_wall || hot_p;
  // v2.10 RE-17: lower bound with the same validity logic (no valid reading = out of range); the coldest valid estimate decides
  float tmin = 1.0e9f;
  for (int k = 0; k < 2; ++k) if (in.ttank_wall_valid[k] && std::isfinite(in.ttank_wall_K[k])) tmin = std::fmin(tmin, in.ttank_wall_K[k]);
  if (sat_ok) tmin = std::fmin(tmin, tsat);
  tank_cold_ = !any || tmin < kTankIgnMin_K;
  if (nw > 0 && sat_ok && std::fabs(wsum / static_cast<float>(nw) - tsat) > kTankXcheckMax_K) tank_xcheck_ = true;
}

// v2.8 MV opener profile shared by PREPRESS and the direct relight: tr = time from the ramp start (negative = still at rest);
// ramp kMvOpenRampSlow_s (rule b) then hold kMvCockHold_s for the holding magnet, then rest (the latch holds the valve)
bool EngineEcu::mvOpener(double tr) {
  const double t_ramp = mv_ramp_ ? kMvOpenRampSlow_s : 0.0;
  const double t_end = t_ramp + (mv_ramp_ ? kMvCockHold_s : kMvCockTime_s);
  if (!mv_cocking_ || tr >= t_end) { mv_cocking_ = false; return false; }
  if (tr < 0.0) servo_us_[3] = kMvOpenerRest_us;
  else if (tr < t_ramp) servo_us_[3] = kMvOpenerRest_us + (kMvOpenerCock_us - kMvOpenerRest_us) * static_cast<float>(tr / t_ramp);
  else servo_us_[3] = kMvOpenerCock_us;
  return true;
}

// v2.8 ignition-lift table (build-time, CF-3): linear in T_tank between rows, clamped outside; no valid T_tank -> smallest lift
float EngineEcu::ignLiftFor(bool ttank_ok, float T) const {
  if (!ttank_ok) return ignLiftTabMin();
  if (T <= kIgnLiftT_K[0]) return kIgnLiftTab_m[0];
  for (int i = 1; i < kIgnLiftN; ++i)
    if (T <= kIgnLiftT_K[i]) {
      const float f = (T - kIgnLiftT_K[i - 1]) / (kIgnLiftT_K[i] - kIgnLiftT_K[i - 1]);
      return kIgnLiftTab_m[i - 1] + f * (kIgnLiftTab_m[i] - kIgnLiftTab_m[i - 1]);
    }
  return kIgnLiftTab_m[kIgnLiftN - 1];
}

void EngineEcu::enter(State s, double t) {
  const State prev = st_;
  st_ = s; t_state_ = t;
  r2_hold_ = false;   // v2.10 LEAD 186 (2): the R2 command hold exists only in RUN (re-evaluated every RUN tick)
  if (s == State::ARMED && prev == State::SAFE) {   // new arming session: forget the learned map trim and the S1 zero
    pcc_.clearTrim();
    drogue_attached_ = false;   // v2.10 LEAD 186 (2): the FC reports the drogue state again in each arming session
    s1_zero_ok_ = false; s1_n_ = 0; s1_acc_ = 0.0f; p_s1_.reset();   // v2.8
    hb_bit_pass_ = false; hb_bit_ = hb::BIT_NONE; rz_applied_ = false; rz_rejected_ = false; rz_shift_ = 0.0f;   // v2.9
  }
  // v2.9 head-end bleed: every state change outside PURGE/IGNITION/RUN/SHUTDOWN/COAST closes both valves at once (ABORT, SAFE, ARMED,
  // PREPRESS); a pad BIT in progress is cancelled. PURGE -> IGNITION / COAST run the V1-first closure step (hbClose) instead.
  if (s == State::ABORT || s == State::SAFE || s == State::ARMED || s == State::PREPRESS) {
    if (hb_cmd_[0] || hb_cmd_[1] || hb_closing_) hb_mid_vented_ = false;   // the mid may be trapped high: leak monitor disarmed
    hb_cmd_[0] = hb_cmd_[1] = false; hb_closing_ = false; t_hb_bit_ = -1.0; hb_bit_step_ = -1;
  }
  // v2.10 (RE-20 follow-up): the 30 bar persistence is NOT restarted by the IGNITION -> RUN transition (the over-pressure condition is
  // continuous across E2; v2.2-v2.9 restarted it, delaying the abort by up to the persistence time)
  if (s != State::RUN) p_hard_.reset();
  p_flame_.reset(); p_band_.reset(); p_gimb_[0].reset(); p_gimb_[1].reset(); p_pcsens_.reset();
  p_a7_.reset();   // v2.9 (v2.10: the A5 persistence p_ihold_ is deleted with A5)
  // v2.6: the pintle monitor episode is NOT reset on state changes (a jam spanning RUN -> SHUTDOWN -> COAST keeps its timer);
  // SAFE entry from a powered state arms the one-off unpowered spring-closing check
  if (s == State::SAFE) safe_chk_ = prev != State::SAFE;
  if (s == State::SAFE || s == State::ARMED) arm_drop_ = false;
  bleed_active_ = false;
  const bool hold_mv = kMvHoldOpenInCoast && starts_ < kMaxStarts;
  switch (s) {
    case State::ARMED: pc_zero_acc_ = 0; pc_zero_n_ = 0; t_arm_req_ = t; mv_latch_ = false; mv_cocking_ = false; t_mv_cmd_ = t;
      ptorch_zero_acc_ = 0.0f; ptorch_zero_n_ = 0; break;   // v2.7 P_torch auto-zero with the Pc one
    case State::PREPRESS: {
      mv_latch_ = true; mv_cocking_ = true; t_mv_cmd_ = t; relight_direct_ = false;   // v2.8: the PREPRESS path (pad, gas in the segment)
      // v2.2 COMB line-priming rule: a line below half the tank pressure holds gas that the opening valve would compress
      prime_slow_ = (pfeed_lpf_.y + pamb_Pa) < kPrimeSlowFrac * (ptank_lpf_.y + pamb_Pa);
      if (!pfeed_ok_ || !ptank_ok_) prime_slow_ = true;   // v2.8: an invalid reading cannot exclude a gas pocket -> slow priming
#ifdef ECU_SIL_TEST_HOOKS
      if (test_force_fast_prime) prime_slow_ = false;
#endif
      bleed_active_ = prime_slow_; bleed_checked_ = !prime_slow_;
      mv_ramp_ = prime_slow_ || kMvRampEveryOpening;   // v2.6 LEAD rule (b): every MV opening (relights too) ramps >= 0.3 s
#ifdef ECU_SIL_TEST_HOOKS
      if (test_force_fast_prime) mv_ramp_ = false;
#endif
      break;
    }
    case State::IGNITION:
      // v2.7: ground timing-only start = key armed in SAFE + test stand + first start of this arming session
      bypass_start_ = bypass_armed_ && stand_ && starts_ == 0;
      lit_ = false; ign_ok_n_ = 0; ++starts_; t_ign_ = t; mv_latch_ = true; prop_closed_ = false;
      torch_ok_ = false; torch_ok_n_ = 0; torch_closed_ = false; torch_low_seen_ = false; prop_bs_n_ = 0;
      ignDetReset();                              // v2.9 light-rule baseline of this start
      t_e3_ = -1.0; a7_flag_ = false;             // v2.9 A7 / E3 per burn
      ls_ = LightSpikeRec{}; ls_t_pk_raw_ = ls_t_pk_filt_ = -1.0;   // v2.10 LIGHT_SPIKE record of this start
      ride_tol_n_ = 0; p_t45_.reset();                              // v2.11 ride-through CANDIDATE: per start
      // v2.9 head-end bleed: a start from PURGE. v2.10: the closure step started in PURGE (V1 close command kPurgeFlowEndLead_s +
      // kHbleedCloseTime_s before E0) and ends in IGNITION; the lift waits for its end up to kTorchGate_s (LEAD RE-05)
      purge_start_ = prev == State::PURGE;
      // v2.10 FA-1: per-start flame-sensing state; the photodiode dark level is frozen here (tracked before E0)
      both_ok_n_ = 0; p_torch_loss_.reset(); fa1_super_ = fa1_both_dark_ = fa1_pt_lit_ = fa1_ph_lit_ = false; photo_dark_seen_ = false;
      photo_run_ref_ok_ = false; p_photo_fo_.reset(); fo_opt_armed_ = false; fo_view_n_ = 0;
      // v2.8 ignition window W from the lift command (LEAD 2026-10-13; v2.7 C7 extension from E0 retired). v2.8.1 (LEAD stand fallback
      // (b)): the stand windows exist ONLY in the stand_ branch (mode strap STAND latched at ARM, load cell consistent): R1 0.35 s first
      // start, R2 0.35 s every other stand start (relights and a start after an abort; R3 deleted, R4 refused earlier). Flight: R1 0.40 s
      // first start (a pad retry after an abort keeps R1), 0.65 s every relight
      t_lift_ = -1.0;
      superheat_e0_ = stand_ && superheat_now_;   // v2.8.1: telemetry only (log seq2_flags b1); no window effect since the R3 deletion
      seg_vap_e0_ = seg_vap_now_;                 // v2.8 final (COMB v2.4): a stand start after an abort is a vapour-segment start -> R2
      if (stand_) {
        if (starts_ <= 1 && !seg_vap_e0_) { ign_rule_ = rule::FIRST; ign_w_s_ = kIgnWindowFirstStand_s; }
        else { ign_rule_ = rule::STAND_DEFAULT; ign_w_s_ = kIgnWindowRelightStand_s; }
      } else {
        if (starts_ <= 1) { ign_rule_ = rule::FIRST; ign_w_s_ = kIgnWindowFirst_s; }
        else { ign_rule_ = rule::FLIGHT_RELIGHT; ign_w_s_ = kIgnWindowRelightLong_s; }
      }
      // v2.8 ignition lift from the lift-vs-T_tank table at E0 (T_tank = Tsat(P_tank)); timing-only start: the smallest lift
      ign_lift_m_ = bypass_start_ ? kTimingOnlyLift_m : ignLiftFor(ttank_ok_, ttank_K_);
      if (!relight_direct_) mv_open_seen_ = true;   // PREPRESS path: the valve was confirmed open before E0
      sat_.resetStats();   // v2.4 ENG-07b: statistics per burn
      break;
    case State::RUN:
      // v2.8 final: the band/flameout reference starts at the measured Pc but never above the map Pc of the ignition lift (the bumpless
      // setpoint): a late light confirmed during its pressure spike set it at the spike (SIL v2.8 S6 hard_start cases: reference ~20 bar,
      // flameout threshold 0.35 x 19 bar, false FLAMEOUT 47 ms later with the chamber lit). A normal light (measured ~3.2 bar abs < map
      // ~4.3 bar abs) is unchanged
      pcc_.reset(pintle_cmd_, ptank_lpf_.y + pamb_Pa); pc_ref_lpf_.reset(std::fmin(pc_f_ + pamb_Pa, pcc_.setpointActive()));
      // v2.8 final: a confirmed light ends the vapour-segment condition of the last abort (the segment has flowed liquid)
      if (seg_vap_now_ || seg_vap_) seg_vap_clear_ = true;
      seg_vap_ = false; seg_vap_now_ = false;
      coast_enc_lost_ = false; coast_pint_open_ = false; coast_open_n_ = 0;   // v2.8.2 RG-08: the segment has flowed liquid again
      // v2.5 COMB v2.1 start ramp (<= 2500 N/s) from the thrust of the map Pc at the ignition lift (bumpless)
      thr_rl_.init = false; thr_rl_.step(thrust::thrustFromPcAbs(pcc_.setpointActive(), pamb_Pa), 0.0f, kDt_s); start_ramp_ = true;
      hold_ramp_ = false;   // v2.10 LEAD 186 (2)
      break;
    case State::SHUTDOWN:   // v2.7 RC-01: pintle first; the NC valve stays latched until the seat is confirmed or kMvSeatTimeout_s
      if (!hold_mv && mv_latch_) { mv_seat_wait_ = true; seat_n_ = 0; mv_seat_timeout_ = false; }
      mv_cocking_ = false;   // v2.8: a direct relight still opening: the opener returns to rest (never pushes against the closing)
      break;
    case State::COAST:
      t_coast_ = t; mv_seat_wait_ = false; mv_cocking_ = false; meco_closed_ = false;   // v2.8 final: TLM VALID re-earned in each coast
      if (!hold_mv) { if (mv_latch_) t_mv_cmd_ = t; mv_latch_ = false; }   // v2.8 final: an earlier unlatch (seat confirmed) keeps its time
      s1_coast_zero_done_ = false; s1_n_ = 0; s1_acc_ = 0.0f;   // v2.8: a fresh S1 zero 0.2-0.4 s into this coast
      break;
    case State::PURGE:   // v2.9: set up by enterPurge() (NC valve latch + opener ramp, both bleed valves open, pintle seated)
      break;
    case State::ABORT: case State::SAFE:   // v2.7: every abort de-energises the NC valve at once (v2.2-v2.8.3 grouped PURGE here)
      mv_latch_ = false; mv_cocking_ = false; mv_seat_wait_ = false; t_mv_cmd_ = t; break;
  }
}

void EngineEcu::doAbort(Abort a, double t) {
  if (st_ == State::SAFE) {         // nothing energised: record an inhibit and stay safe
    if (abort_ == Abort::NONE) abort_ = a;
    abort_latched_ = true;
    return;
  }
  if (st_ == State::ABORT) return;  // first cause wins
  abort_ = a; abort_latched_ = true;
  // v2.8 final (COMB v2.4, LEAD 2026-10-13): after ANY abort the next attempt is a vapour-segment start (the 30 ms MV-P closes before
  // the pintle; the segment drains to ~50 % vapour). RAM + NvJamRecord b3 until a light is confirmed (RUN entry)
  if (!seg_vap_) { seg_vap_ = true; seg_vap_event_ = true; }
  seg_vap_now_ = true;
  // v2.10 (LEAD 172 (1)): a GROUND no-light opens the safing hold and sets the lockout (the v2.5 5 s retry wait is withdrawn). No-light =
  // abort in IGNITION (no confirmed light) or NO_IGNITION / TORCH_FAULT / TORCH_LOST / FLAMEOUT; ground = stand, or the pad first start
  const bool nolight = st_ == State::IGNITION || a == Abort::NO_IGNITION || a == Abort::TORCH_FAULT || a == Abort::TORCH_LOST ||
                       a == Abort::FLAMEOUT;
  if (nolight && (stand_ || starts_ <= 1)) { setLockout(); if (!sh_open_) sh_event_ = true; sh_open_ = true; t_sh_ = t; }
  // v2.7 LEAD 2026-10-13: no automatic in-flight relight retry. Any abort on a relight or after a lit burn in this power cycle
  // (any state: IGNITION, RUN, SHUTDOWN, COAST, PREPRESS ...) locks further ignition out until the keyed ground CLEAR_LOCKOUT;
  // a ground no-light is handled above (v2.10). (v2.7 draft: IGNITION/RUN/SHUTDOWN only - an abort in COAST
  // followed by DISARM, ARM, IGNITE would have been a new in-flight start.)
  if (starts_ >= 2 || lit_since_boot_) setLockout();
  enter(State::ABORT, t);
}

bool EngineEcu::armChecksOk(const Inputs& in, Abort* why) const {
  if (maintJamPending(in)) { *why = Abort::MAINT_JAM; return false; }   // v2.6: recorded pintle jam -> bearing A first (CLEAR_JAM)
  if (lockoutPending(in)) { *why = Abort::RELIGHT_LOCKOUT; return false; }   // v2.7: no further starts after an in-flight abort
  // v2.8 (LEAD 2026-10-13): stand vs flight must not rest on the load cell alone - coded strap valid AND agreeing with the load cell
  if (!modeConsistent(in)) { *why = Abort::MODE_MISMATCH; return false; }
  // v2.8 (LEAD 2026-10-13 launch constraint): SB-2292SG servos within rating in flight only if the bay is <= ~45 C at ARM
  if (bayHot(in)) { *why = Abort::BAY_HOT; return false; }
  // v2.8 final (LEAD 2026-10-13, ENG-12 15-24 C): tank above 24 C (max of the wall DS18B20 and Tsat(P_tank)) or no valid reading
  if (tank_hot_) { *why = Abort::TANK_HOT; return false; }
  if (tank_cold_) { *why = Abort::TANK_COLD; return false; }   // v2.10 RE-17 (ENG-12 15-24 C lower bound)
  if (!in.arm_plug_present) { *why = Abort::ARM_LOST; return false; }
  if (t_now_ - last_fast_t_ > kLinkDegraded_s) { *why = Abort::LINK_LOST; return false; }   // FC heartbeat (CMD_FAST) required
  if (in.vbat_V < kBattArmMin_V) { *why = Abort::BATT_LOW; return false; }
  if (!(supply_.vplugPred() >= kTvcSupplyMin_V)) { *why = Abort::TVC_SUPPLY; return false; }   // v2.3 FM-PWR-01 (LEAD ARM rule;
                                                                                                //   no valid prediction = refused)
  // v2.6 OI-6: zero sanity on the 50 Hz filtered gauge reading (before the auto-zero), not on one raw sample
  if (!pc_sensor_ok_ || std::fabs(pc_f_ + pc_zero_) > kPcArmZeroMax_Pa) { *why = Abort::PC_SENSOR; return false; }
  // v2.7: the flame gate needs a plausible torch transducer on the vented torch (TEB band) unless the stand timing-only key is armed
  if (!bypass_armed_ && (!in.ptorch_valid || std::fabs(in.ptorch_Pa) > kTorchArmZeroMax_Pa)) { *why = Abort::TORCH_FAULT; return false; }
  if (in.ptank_Pa > kTankOverPressure_Pa) { *why = Abort::TANK_OVERPRESSURE; return false; }
  for (int k = 0; k < 3; ++k)
    if (in.tc_valid[k] && in.tc_K[k] > kCaseOverTemp_K) { *why = Abort::OVER_TEMP; return false; }
  // v2.10 RE-08 (LEAD CHANGELOG 166 (6)): both case TCs valid at ARM (an invalid case TC counts as hot, like bay and tank)
  if (!in.tc_valid[0] || !in.tc_valid[1]) { *why = Abort::OVER_TEMP; return false; }
  if (!in.mv_closed_sw || in.mv_sw_conflict) { *why = Abort::MV_FAULT; return false; }   // v2.10 RE-19: + ladder OPEN+CLOSED
  if (kArmRequiresPintleEncoder && !in.pintle_meas_valid) { *why = Abort::PINTLE_FAULT; return false; }   // v2.6
  if (in.pintle_meas_valid && in.pintle_meas_m > kPintleStallErr_m) { *why = Abort::PINTLE_FAULT; return false; }   // v2.6: not seated
  return true;
}

bool EngineEcu::setGimbalNotchCal(const GimbalNotchCal& c) {
  if (st_ != State::SAFE || !c.valid(kDt_s)) return false;
  tvc_.setNotchAxis(0, c.ax[0], kDt_s);
  tvc_.setNotchAxis(1, c.ax[1], kDt_s);
  return true;
}

bool EngineEcu::setPintleCal(const linkage::PintleCal& c) {
  if (st_ != State::SAFE || !c.valid()) return false;
  // the closed command and the 4 mm command must lie inside the clamps (unclamped pulses), else the stroke would be cut
  auto raw = [&](float x) { return c.center_us + c.trim_us + c.dir * (linkage::liftToCrank(x) - eng::kCrankPhiNeutral_rad) * 57.29578f * c.us_per_deg; };
  const float a = raw(0.0f), b = raw(kPintleLiftMaxCmd_m);
  if (std::fmin(a, b) < c.min_us || std::fmax(a, b) > c.max_us) return false;
  pcal_ = c;
  return true;
}

void EngineEcu::handleCommand(Cmd c, uint16_t arg, const Inputs& in, double t) {
  switch (c) {
    case Cmd::ARM:
      if (st_ == State::SAFE && !abort_latched_) {
        Abort why = Abort::NONE;
        if (armChecksOk(in, &why)) {
          starts_ = 0;
          mode_stand_ = modeStrapStand(in); stand_ = mode_stand_; mode_mismatch_ = false;   // v2.8: mode latched for the session
          enter(State::ARMED, t);
        }
        else { abort_ = why; abort_latched_ = true; }     // inhibit recorded; DISARM clears it
      }
      break;
    case Cmd::DISARM: case Cmd::SAFE:
      if (st_ == State::SAFE) {
        abort_latched_ = false; abort_ = Abort::NONE; faults_ = 0;
        pint_backoff_ = false; pint_kind_ = jam::NONE;   // v2.6: the maintenance flag (jam record) stays until CLEAR_JAM
        prail_lost_ = false; bypass_armed_ = false;      // v2.7 (the relight lockout stays until CLEAR_LOCKOUT)
        s1_fault_ = false; mode_mismatch_ = false; cmd_refused_ = refuse::NONE;   // v2.8 (an S1 lockout stays until CLEAR_LOCKOUT)
        tank_xcheck_ = false; tank_hot_relight_ = false; tank_cold_relight_ = false;   // v2.8 final flags (the vapour-segment flag stays until a confirmed light)
        coast_enc_lost_ = false; coast_pint_open_ = false; coast_open_n_ = 0;   // v2.8.2 RG-08 (new session: the next start is a pad start)
        hb_leak_ = hb_path_flag_ = hb_hold_to_ = hb_purge_enc_ = false; hb_bit_ = hb::BIT_NONE;   // v2.9 head-end bleed flags
        hb_bleed_fault_ = false; hb2_ = 0; hb_flow_s_ = -1.0f; f2_ = f2_prev_ = 0;                 // v2.10
        enter(State::SAFE, t);
        safe_chk_ = false;
      }
      else if (st_ == State::ARMED || st_ == State::COAST || st_ == State::PREPRESS || st_ == State::PURGE) enter(State::SAFE, t);
      // v2.7: a commanded DISARM/SAFE (not an abort) ends a lit session normally -> the HAL clears NvJamRecord b2
      if (st_ == State::SAFE && lit_session_) { lit_session_ = false; lit_session_close_ = true; }
      else if (st_ == State::IGNITION || st_ == State::RUN || st_ == State::SHUTDOWN) doAbort(Abort::CMD, t);
      break;
    case Cmd::PREPRESS:
      // v2.8 (LEAD 2026-10-13): PREPRESS only on the pad. In COAST it is refused: v2.7 accepted it with no lockout checks and a 60 s
      // hold of an open valve on a seated pintle (a rule (b) gap); a relight opens the valve itself at E0
      if (st_ == State::ARMED) { auto_ignite_ = false; enter(State::PREPRESS, t); }
      else if (st_ == State::COAST) { ++prepress_refused_; refuseCmd(refuse::PREPRESS_IN_COAST); }
      break;
    case Cmd::IGNITE: case Cmd::RELIGHT: {
      // v2.8: the refusal rules live in startBlock() (shared with the TLM_RELIGHT status); counters as in v2.7; every refusal now
      // reports its reason (EVENT CMD_REFUSED). v2.7 rules kept: start limit; relight lockout (no automatic in-flight retry, LEAD);
      // ENG-07d notch on both axes (GNC csi_v3); vented chamber (COMB OI-12, the FC repeats the command); 5 s vent wait after a
      // no-light or flameout (COMB v2.2); v2.8: case hot (MECH), bay hot (pad first start), stand R4 (state sensors invalid)
      if (st_ == State::COAST) rezero2Apply(t);   // v2.10 RE-07: second re-zero before the vented check
      const uint8_t why = startBlock(in, t);
      if (why != refuse::NONE) {
        if (why != refuse::MAX_STARTS) ++ign_refused_;
        if (why == refuse::NOTCH) ++ign_refused_notch_;
        if (why == refuse::CASE_HOT) ++ign_refused_hot_;
        if (why == refuse::BAY_HOT) ++ign_refused_bay_;
        if (why == refuse::R4_SENSOR) ++ign_refused_r4_;
        if (why == refuse::TANK_HOT || why == refuse::TANK_COLD) ++ign_refused_tank_;
        refuseCmd(why);
        break;
      }
      // v2.11 (LEAD CHANGELOG 203 (7) ADOPTED; 186 (1), 204 (2)): FLIGHT with the head-end bleed fitted, a RELIGHT/IGNITE from COAST
      // (no purge running) is an UNPURGED relight -> REFUSED. The accepted flight relight is the RELIGHT received during PURGE (below).
      // Consequence: the COAST relight paths below (kMvHoldOpenInCoast, direct, prep) are reachable in flight only without the bleed
      // fitted, and a flight relight on a state the purge does not cover (UNPRIMED / UNKNOWN segment: PURGE is refused PURGE_PATH) has
      // no accepted path (Electronics v2.11 report, LEAD to rule). The stand keeps the unpurged start (CF-4 / T4).
      if (st_ == State::COAST && unpurgedGuard()) { ++ign_refused_; refuseCmd(refuse::UNPURGED); break; }
      cmd_refused_ = refuse::NONE;
      if (st_ == State::COAST && !chamberVented()) f2_ |= f2::NOT_VENTED;   // v2.10 RE-07: flight relight not vented -> flag, proceeds
      // v2.8 final: a flight relight is never refused on the tank interlock (the tank cools in each burn); flagged and logged
      if (tank_hot_ && starts_ >= 1 && !stand_) tank_hot_relight_ = true;
      if (tank_cold_ && starts_ >= 1 && !stand_) { tank_cold_relight_ = true; f2_ |= f2::TANK_COLD_RELIGHT; }   // v2.10 RE-17: flag only
      // v2.9 RELIGHT during a (pre-scheduled) purge. v2.10 (LEAD CHANGELOG 164): the purge is never truncated - IGNITION follows in
      // State::PURGE once the flow has ended kPurgeFlowEndLead_s before (at once if it already has)
      if (st_ == State::PURGE) {
        purge_ign_ = true;
        break;
      }
      // MV held open through the coast (only with kMvHoldOpenInCoast): direct 0.3 s relight; otherwise PREPRESS (rule b)
      // v2.10 (LEAD CHANGELOG 175 (3)-(4), PURGE commit rule): a RELIGHT with NO preceding PURGE is an UNPURGED relight; path chosen from
      // the line state (PRIMED -> direct, UNPRIMED/UNKNOWN -> prep). The v2.9 sequence-integrated purge (RELIGHT in COAST -> PURGE,
      // + 2.90 s) is DELETED. The FC alone decides a purge (Cmd::PURGE). LEAD 186 (1): the FC commits iff the lead to the plain trigger
      // is >= L* = 1.3 s (FC parameter), else no purge AND no relight on that pass. v2.11 (LEAD 203 (7)): the ECU now REFUSES the
      // unpurged RELIGHT in flight with the bleed fitted (guard above; GNC's held-release alternative NOT ADOPTED, 204 (2)); the paths
      // below remain for the stand and for a build without the bleed
      if (kMvHoldOpenInCoast && st_ == State::COAST && mv_latch_ && feedPrimed(in)) enter(State::IGNITION, t);
      else if (st_ == State::COAST && directRelightOk(in)) {
        // v2.8 Finding A (LEAD 2026-10-13): NC valve latch + opener ramp (rule b) and torch on this tick (E0); lift at E1
        relight_direct_ = true; mv_latch_ = true; mv_cocking_ = true; mv_ramp_ = kMvRampEveryOpening; t_mv_cmd_ = t;
        mv_open_seen_ = false; prime_slow_ = false; bleed_active_ = false; bleed_checked_ = true;
        enter(State::IGNITION, t);
      }
      else if (st_ == State::ARMED || st_ == State::COAST) { auto_ignite_ = true; enter(State::PREPRESS, t); }
      else if (st_ == State::PREPRESS) auto_ignite_ = true;
      break;
    }
    case Cmd::SHUTDOWN:
      if (st_ == State::IGNITION || st_ == State::RUN) enter(State::SHUTDOWN, t);
      else if (st_ == State::PREPRESS) enter(State::ARMED, t);
      else if (st_ == State::PURGE) { hbClose(t); enter(State::COAST, t); }   // v2.9: purge cancelled (V1-first closure, MV unlatched)
      break;
    case Cmd::PURGE:
      // v2.9 (LEAD 2026-10-13): the FC pre-schedules the forced purge at T_fire - kPurgeRelight_s so its RELIGHT keeps the 0.81 s plan.
      // COAST only, bleed fitted, same refusals as a RELIGHT, and only on the direct path (the prep path does not use the purge)
      if (st_ != State::COAST) { if (st_ != State::PURGE) refuseCmd(refuse::NOT_COAST); break; }
      if (!hbleed_fitted) { refuseCmd(refuse::NO_HBLEED); break; }
      rezero2Apply(t);   // v2.10 RE-07: the second re-zero ends before the PURGE command
      {
        const uint8_t why = startBlock(in, t);
        if (why != refuse::NONE) { refuseCmd(why); break; }
      }
      if (!directRelightOk(in)) { refuseCmd(refuse::PURGE_PATH); break; }
      cmd_refused_ = refuse::NONE;
      if (!chamberVented()) f2_ |= f2::NOT_VENTED;   // v2.10 RE-07 (startBlock refused it on the stand)
      enterPurge(t, false);
      break;
    case Cmd::ABORT: doAbort(Abort::CMD, t); break;
    case Cmd::SET_LINK_POLICY:
      link_policy = (arg & 0xFF) ? LinkPolicy::HOLD_THEN_SHUTDOWN : LinkPolicy::SHUTDOWN;
      link_hold_s = 0.1f * static_cast<float>(arg >> 8);
      break;
    case Cmd::TVC_TEST_ENABLE:
      if (st_ == State::SAFE) {
        if (arg != 0 && !tvc_test_enabled) sat_.reset();   // v2.4: statistics per bench run
        tvc_test_enabled = (arg != 0);
        tvc_test_raw = (arg == 2);                          // v2.6 B-TVC-1 frequency response (filters bypassed)
      }
      break;
    case Cmd::CLEAR_JAM:             // v2.6: "bearing A replaced" (MECH/LEAD maintenance rule); SAFE only, keyed argument
      if (st_ == State::SAFE && arg == kClearJamKey) {
        jam_since_clear_ = false; maint_clear_ = true; pint_kind_ = jam::NONE; pint_backoff_ = false;
      } else {
        ++clear_jam_refused_;
      }
      break;
    case Cmd::CLEAR_LOCKOUT:         // v2.7: ground action after the post-test / post-landing safing; SAFE only, keyed argument
      // v2.10 (LEAD 172 (1)): refused inside the ground no-light safing hold (reason SAFING_HOLD, EVENT CMD_REFUSED)
      if (st_ == State::SAFE && arg == kClearLockoutKey && safingHoldLeft_s() <= 0.0) { lockout_ = false; lockout_clear_ = true; sh_open_ = false; }
      else { ++clear_lockout_refused_; if (st_ == State::SAFE && arg == kClearLockoutKey) refuseCmd(refuse::SAFING_HOLD); }
      break;
    case Cmd::SET_TORCH_GATE:        // v2.7 RC-01: ground timing-only start (stand only); any other argument re-arms the gate
      if (st_ == State::SAFE) bypass_armed_ = (arg == kTorchTimingOnlyKey) && stand_;   // v2.8: stand_ in SAFE = strap AND load cell
      break;
    case Cmd::VENT:
      if (st_ == State::SAFE || st_ == State::ARMED || st_ == State::COAST) vent_cmd_ = (arg != 0);
      break;
    case Cmd::DROGUE:                // v2.10 LEAD 186 (2): FC drogue state (1 attached, 0 released), any state; other values ignored
      if (arg == 0u || arg == 1u) drogue_attached_ = (arg == 1u);
      break;
    case Cmd::SET_GIMBAL_NOTCH:      // v2.4 ENG-07d: bench/pad setting from the B-TVC-1 rocking mode; SAFE only (v2.6 per axis)
      if (st_ == State::SAFE) {
        const bool per_axis = (arg & 0x8000u) != 0;
        const int a0 = per_axis ? ((arg >> 14) & 1) : 0, a1 = per_axis ? a0 : 1;
        const uint16_t f = per_axis ? (arg & 0x3FFFu) : (arg & 0x7FFFu);
        NotchAxis n[2] = {tvc_.notchAxis(0), tvc_.notchAxis(1)};
        bool ok = true;
        for (int k = a0; k <= a1; ++k) { n[k].enabled = f != 0; if (f != 0) n[k].f0_Hz = 0.1f * static_cast<float>(f); ok = ok && n[k].valid(kDt_s); }
        if (ok) { for (int k = a0; k <= a1; ++k) tvc_.setNotchAxis(k, n[k], kDt_s); gcal_changed_ = true; }   // out of range: ignored
      }
      break;
    case Cmd::SET_GIMBAL_NOTCH_QD:   // v2.6 per-axis Q and depth (B-TVC-1), SAFE only; the axis keeps its centre and on/off state
      if (st_ == State::SAFE) {
        const int k = (arg >> 15) & 1;
        NotchAxis n = tvc_.notchAxis(k);
        n.depth_dB = -static_cast<float>((arg >> 8) & 0x7Fu);
        n.q = static_cast<float>(arg & 0xFFu) / 20.0f;
        NotchAxis chk = n; chk.enabled = true;   // Q/depth are validated even while the axis is disabled (then stored, still off)
        if (chk.valid(kDt_s)) { tvc_.setNotchAxis(k, n, kDt_s); gcal_changed_ = true; }
      }
      break;
    default: break;
  }
}

void EngineEcu::monitors(const Inputs& in, double t) {
  const float dt = kDt_s;
  const double ts = t - t_state_;
  const bool burning = (st_ == State::IGNITION || st_ == State::RUN);
  const float pc_abs = pc_f_ + pamb_Pa;
  // --- chamber over-pressure [LEAD 2026-10-12: MEOP 45 bar, ECU abort ~30 bar]. Every state except SAFE and not gated by
  //     the sensor-valid flag: a reading saturated high (> 4.75 V = 73 bar) also aborts. Cause HARD_START during ignition.
#ifdef ECU_SIL_TEST_HOOKS
  const bool fw_ovp_on = !test_disable_fw_ovp;
#else
  constexpr bool fw_ovp_on = true;
#endif
  // v2.11 FA-1 RIDE-THROUGH (LEAD CHANGELOG 203 (1)(b) CANDIDATE, config.h kRide*; default OFF): flight relight only (rule FLIGHT_RELIGHT,
  //     never the stand or the pad first start), from the ignition-lift command of this start to E2 + kRideWinPostE2_s. Inside it the
  //     filtered 30 bar persistence is kRideOvpTime_s, a raw reading above the 45 bar MEOP for kRideT45_s aborts HARD_START, and the
  //     hardware is asked for the long comparator RC (Outputs::ovp_long_rc). The same persistence timer runs through: an episode still
  //     above 30 bar when the window closes trips at once on the as-built 5 ms.
  ride_win_ = false; ride_tol_ = false; ride_t45_ = false;
  if (ride_through && !stand_ && ign_rule_ == rule::FLIGHT_RELIGHT && t_lift_ >= 0.0) {
    if (st_ == State::IGNITION) ride_win_ = true;
    else if (st_ == State::RUN && t_lit_ >= t_lift_ && t - t_lit_ + kTimeEps_s < kRideWinPostE2_s) ride_win_ = true;
  }
  const float ovp_time = ride_win_ ? kRideOvpTime_s : kPcOverPressureTime_s;
  const bool ovp_trip = st_ != State::SAFE && fw_ovp_on && p_hard_.step(pc_abs > kPcOverPressureAbs_Pa, ovp_time, dt);
  if (ride_win_ && p_hard_.t >= kPcOverPressureTime_s) { ride_tol_ = true; ++ride_tol_n_; }   // as built would have tripped here
  if (ovp_trip) {
    faults_ |= fault::PC_OVERP;
    const bool ign_phase = st_ == State::IGNITION || (st_ == State::RUN && ts < kRunSettle_s);
    doAbort(ign_phase ? Abort::HARD_START : Abort::PC_OVERPRESSURE, t);
    return;
  }
  if (ride_win_) {
    const float raw_abs = in.pc_Pa - pc_zero_ + pamb_Pa;
    ride_t45_ = std::isfinite(raw_abs) && raw_abs > kPcMeopLeadAbs_Pa;
    if (fw_ovp_on && p_t45_.step(ride_t45_, kRideT45_s, dt)) {
      faults_ |= fault::PC_OVERP;
      doAbort(Abort::HARD_START, t);   // inside the window the state is IGNITION or RUN before kRunSettle_s
      return;
    }
  } else p_t45_.reset();
  // --- v2.8.1 over-thrust (LEAD 2026-10-13 ADOPTED, GNC m2_fc_thrust v1.1): flight, RUN, kOverThrustFrames consecutive fresh valid
  //     FC_THRUST frames above kOverThrust_N (counted at frame receipt in step()). Runs with the Pc channel valid or not: with it lost the
  //     firmware check above and the hardware comparator (same PC_SIG) are blind, and an in-range wrong Pc reading blinds them too
  {
    const bool fresh = fc_thr_ok_ && (t - t_fc_thr_) <= kFcThrustStale_s + kTimeEps_s;
    if (!(st_ == State::RUN && !stand_) || !fresh) overthr_n_ = 0;
    if (overthr_n_ >= kOverThrustFrames) { faults_ |= fault::PC_OVERP; doAbort(Abort::OVER_THRUST, t); return; }
  }
  // --- v2.10: the v2.9 A5 ignition-hold over-pressure abort (filtered Pc > 8.0 bar abs for 5 ms from E1 to E2 -> HARD_START) is DELETED,
  //     flight and stand (LEAD CHANGELOG 160 (1)); the late-light spike is recorded by lightSpikeTrack() (LIGHT_SPIKE, no action). The
  //     remaining ignition-phase HARD_START sources: the 30 bar abort above (filtered, 5 ms) and the HIGH over-range in IGNITION (step()).
  // --- v2.9 A3 relative flame-out (RUN), A7 map criterion (E1 onwards), E3; the lagged Pc_map runs on every tick
  {
    bool aborted = false;
    startMonitors(in, t, &aborted);
    if (aborted) return;
  }
  // --- Pc band (RUN, after settle): closed-loop tracking against the reference (v2.2; the v2.2-v2.8.3 absolute flameout is replaced by A3)
  if (st_ == State::RUN && pc_sensor_ok_) {
    if (ts > kRunSettle_s) {
      const float band = std::fmax(kPcBandFrac * (pc_ref_ - pamb_Pa), kPcBandMin_Pa);
      if (p_band_.step(std::fabs(pc_abs - pc_ref_) > band, kPcBandTime_s, dt)) { faults_ |= fault::PC_BAND; doAbort(Abort::PC_BAND, t); return; }
    }
  }
  // --- v2.6 pintle stall / tracking monitor (replaces the v2.5 command-model check, which tripped on large HV69 steps)
  {
    bool aborted = false;
    pintleMonitor(in, t, &aborted);
    if (aborted) return;
  }
  // --- v2.7 pintle rail (LEAD 2026-10-13): LTC4365 OV-disconnect trip or regulator failure = the servo-side rail collapses while
  //     the servo should be powered -> PINTLE_FAULT abort (the NC valve is de-energised at once; the hardware /FAULT gate has
  //     already cut the holding magnet). The unpowered needle is closed by the spring back-driving the HV69 (B-PNT-1 item);
  //     the stall monitor still supervises that closing in ABORT. Not recorded as a jam.
  {
    const bool pwr = st_ != State::SAFE && in.arm_bus_on && !arm_drop_;
    if (!pwr) t_bus_on_ = -1.0;
    else if (t_bus_on_ < 0.0) t_bus_on_ = t;
    const bool watch = pwr && in.prail_valid && t - t_bus_on_ + kTimeEps_s >= kPrailSettle_s;
    if (p_prail_.step(watch && in.prail_V < kPrailLost_V, kPrailLostTime_s, dt)) {
      faults_ |= fault::PINTLE;
      prail_lost_ = true;
      if (st_ != State::ABORT) { doAbort(Abort::PINTLE_FAULT, t); return; }
    }
  }
  // --- gimbal tracking
  const bool tvc_active = burning || st_ == State::COAST || st_ == State::SHUTDOWN || tvc_test_enabled;
  // --- v2.4 ENG-07b actuator saturation episodes (LEAD 2026-10-12: none longer than 0.1 s in the landing burn). Episode =
  //     actuator-saturation proxy on either axis (b2 A, b3 B: encoder off the linear expected-response model by more than
  //     kGimbalSatErr_rad). Command limiting in this ECU (b0 7 deg limit, b1 100 deg/s shaping) is recorded in the flags
  //     as context but does not start an episode. Counted only while TVC is active; logged (v4) and flagged (TLM b7).
  {
    uint8_t sf = tvc_.limitFlags() & 0x03u;
    for (int k = 0; k < 2; ++k) {
      const float model_rate = (gimbal_shaped_[k] - gimbal_model_[k]) / kGimbalModelTau_s;
      if (in.gimbal_meas_valid[k] && satProxyAxis(gimbal_model_[k], model_rate, in.gimbal_meas_rad[k])) sf |= (k == 0 ? 4u : 8u);
    }
    if (!tvc_active) sf = 0;
    sat_.step((sf & 0x0Cu) != 0, dt, kSatEpisodeMax_s);
    sat_flags_ = sf;
  }
  for (int k = 0; k < 2; ++k) {
    if (!in.gimbal_meas_valid[k]) { faults_ |= fault::ENCODER; p_gimb_[k].reset(); continue; }
    // v2.2: allowance widened by the model's own rate (|shaped - model| / tau) so full-deflection slews near the actuator's
    // rate limit do not trip; a jammed gimbal still trips once the command settles (threshold back to 1.5 deg)
    const float thr = kGimbalFaultErr_rad + kGimbalFaultRateWin_s * std::fabs(gimbal_shaped_[k] - gimbal_model_[k]) / kGimbalModelTau_s;
    if (tvc_active && p_gimb_[k].step(std::fabs(gimbal_model_[k] - in.gimbal_meas_rad[k]) > thr, kGimbalFaultTime_s, dt)) {
      faults_ |= fault::GIMBAL;
      if (burning && gimbal_fault_aborts) { doAbort(Abort::GIMBAL_FAULT, t); return; }
    }
  }
  // --- over-temperature (case, nozzle holder abort a burn; servo bracket only flags). v2.8 (MECH 2026-10-13): the case TCs (az 90 /
  //     az 270) are armed only while the MV is latched or OPEN (pressurised case); the post-burn soak (165.9 C, unpressurised) exceeds
  //     the in-burn peak and must not trip with the valve closed. Nozzle holder unchanged (always armed).
  bool hot = false;
  const bool mv_open_now = mv_latch_ || in.mv_open_sw;
  for (int k = 0; k < 2; ++k) hot |= mv_open_now && in.tc_valid[k] && in.tc_K[k] > kCaseOverTemp_K;
  // v2.10 RE-08 (LEAD CHANGELOG 166 (6)): one case TC lost -> the other carries the monitor (f2::CASE_TC_DEGRADED to the FC); both
  // lost -> stand: treated as hot (abort through the same persistence); flight: the burn continues, the relight is refused (caseHot)
  // and the FC keeps the drogue
  if (st_ != State::SAFE && (!in.tc_valid[0] || !in.tc_valid[1])) f2_ |= f2::CASE_TC_DEGRADED;
  hot |= mv_open_now && stand_ && !in.tc_valid[0] && !in.tc_valid[1];
  hot |= in.tc_valid[2] && in.tc_K[2] > kNozzleHolderOverTemp_K;
  if (p_otemp_.step(hot, kOverTempTime_s, dt)) {
    faults_ |= fault::OVER_TEMP;
    if (burning || st_ == State::PREPRESS || st_ == State::PURGE) { doAbort(Abort::OVER_TEMP, t); return; }   // v2.9: + PURGE (MV open)
  }
  if (p_servo_hot_.step(in.tc_valid[3] && in.tc_K[3] > kServoBracketOverTemp_K, kOverTempTime_s, dt)) faults_ |= fault::OVER_TEMP;
  // --- tank over-pressure: never aborts a burn (draining lowers pressure); safes the pad states. v2.3: with
  //     tank_overp_pad_only (LEAD conditional on a passive tank relief device) a relight PREPRESS in flight is not aborted.
  const bool pad = starts_ == 0;                 // v2.3: no start made yet = on the pad (a relight also passes PREPRESS)
  const bool pad_state = st_ == State::ARMED || st_ == State::PREPRESS;
  if (p_tankp_.step(in.ptank_Pa > kTankOverPressure_Pa, kTankOverPressureTime_s, dt)) {
    faults_ |= fault::TANK_OVERP;
    // v2.9: a flight PURGE is treated like the relight PREPRESS it replaces on the direct path
    if ((pad_state || st_ == State::PURGE) && (pad || !tank_overp_pad_only)) { doAbort(Abort::TANK_OVERPRESSURE, t); return; }
  }
  // --- battery (v2.3 LEAD: aborts only before the first start; in flight the fault bit is the indication)
  if (p_batt_.step(in.vbat_V < kBattLow_V, kBattLowTime_s, dt)) {
    faults_ |= fault::BATT_LOW;
    if (pad && pad_state) { doAbort(Abort::BATT_LOW, t); return; }
  }
  // --- v2.3 FM-PWR-01 TVC supply: predicted servo plug voltage with both TVC servos at stall (supply.h; the estimator is
  //     stepped with the sensors at the top of step(), before commands, so the ARM check and an early return never miss it)
  const float vplug = supply_.vplugPred();
  if (!tvc_sup_deg_) {
    if (p_sup_set_.step(vplug < kTvcSupplyMin_V, kTvcSupplyTime_s, dt)) { tvc_sup_deg_ = true; p_sup_clr_.reset(); }
  } else if (p_sup_clr_.step(vplug > kTvcSupplyMin_V + kTvcSupplyHyst_V, kTvcSupplyClearTime_s, dt)) {
    tvc_sup_deg_ = false; p_sup_set_.reset();
  }
  if (tvc_sup_deg_ && pad && pad_state) { doAbort(Abort::TVC_SUPPLY, t); return; }
  // --- v2.3 firmware e-fuse (F401 deleted): before the first start only; in flight losing TVC power loses the vehicle
  if (p_efuse_.step(pad && in.ibat_A > kEfuse_A, kEfuseTime_s, dt)) {
    if (st_ == State::SAFE) { if (tvc_test_enabled) { tvc_test_enabled = false; doAbort(Abort::OVERCURRENT, t); } }
    else if (pad_state) { doAbort(Abort::OVERCURRENT, t); return; }
  }
  // --- hardware over-pressure latch (U330 comparator -> U331 latch -> ARM AND gate, independent of this code): the ARM
  //     bus is already off; record the cause before ARM_LOST (10 ms) and stop requesting the bus
  if (st_ != State::SAFE && t - t_arm_req_ > kHwOvpArmSettle_s && p_hwovp_.step(!in.ovp_ok, kHwOvpTime_s, dt)) {
    faults_ |= fault::PC_OVERP;
    if (st_ != State::ABORT) { arm_drop_ = true; doAbort(Abort::HW_OVERPRESSURE, t); return; }
  }
  // --- arming chain (hardware already removed power; firmware follows)
  const bool armed_state = st_ != State::SAFE && !arm_drop_;
  if (armed_state && p_armlost_.step(!in.arm_plug_present || (t - t_arm_req_ > 0.05 && !in.arm_bus_on), 0.01f, dt)) {
    faults_ |= fault::ARM_PLUG;
    if (st_ != State::ABORT) { doAbort(Abort::ARM_LOST, t); return; }
  }
  // --- main valve position when it should be closed
  if (!mv_latch_ && t - t_mv_cmd_ > kMvCloseConfirm_s && !in.mv_closed_sw) faults_ |= fault::MV;
  // --- v2.10 RE-19: ladder decoded OPEN+CLOSED (impossible state) -> fault MV; stand -> MV_FAULT abort (flight: flag, like the other
  //     MV-switch anomalies; ARM refuses it in armChecksOk)
  if (p_mvconf_.step(in.mv_sw_conflict, kMvSwConflictTime_s, dt)) {
    faults_ |= fault::MV;
    if (stand_ && st_ != State::SAFE && st_ != State::ABORT) { doAbort(Abort::MV_FAULT, t); return; }
  }
  // --- v2.8 direct relight: the NC valve should show its OPEN switch within kMvOpenBy_s of E0 (PREPRESS checks it before E0
  //     otherwise). Not seen: fault MV. A valve that never opens gives NO_IGNITION at E1 + W (<= 0.81 s, before kMvOpenBy_s), so
  //     the deadline is reached only in RUN, i.e. with the chamber lit and the valve passing flow: stand -> MV_FAULT abort (switch
  //     or latch to be inspected); flight -> flag only (an abort in flight loses the vehicle; the Pc loop and the flameout monitor
  //     remain the protection). The v2.8 draft aborted in flight too (test_v28 group (4) keeps the case).
  if (burning && relight_direct_) {
    if (in.mv_open_sw) mv_open_seen_ = true;
    if (!mv_open_seen_ && t - t_mv_cmd_ > kMvOpenBy_s + kTimeEps_s) {
      faults_ |= fault::MV;
      if (stand_) { doAbort(Abort::MV_FAULT, t); return; }
    }
  }
  // --- v2.9 head-end bleed: V1-first closure confirmation and the leak monitor
  {
    bool aborted = false;
    hbleedStep(in, t, &aborted);
    if (aborted) return;
  }
  // --- v2.8 S1 relief supervision (zero capture + monitor)
  s1Step(in, t);
}

// v2.8 S1 trapped-liquid relief supervision (LEAD 2026-10-13). Zero of (P_feed - P_tank) captured with no flow: PREPRESS with the OPEN
// switch made >= kS1ZeroMvOpen_s and the pintle seated (blocks of kS1ZeroN ticks, the latest block wins), and once per coast from
// kS1CoastZeroFrom_s to kS1CoastZeroTo_s after COAST entry with the CLOSED switch made and the pintle seated (segment still at P_tank).
// Monitor: ARMED or COAST, CLOSED switch made, zero captured, both readings valid: dp - zero > kS1DpMax_Pa for kS1Time_s -> s1_fault_
// (fault MV bit, EVENT S1_FAULT); stand: relight lockout; flight: flag and log only (the relight opens the MV at E0 and relieves it).
void EngineEcu::s1Step(const Inputs& in, double t) {
  const float dp = pfeed_lpf_.y - ptank_lpf_.y;
  const bool both = in.pfeed_valid && in.ptank_valid;
  const bool seated = pintle_cmd_ <= 0.0f && (!in.pintle_meas_valid || in.pintle_meas_m <= kPintleSeatConfirm_m);
  if (in.mv_open_sw) { if (t_mv_open_sw_ < 0.0) t_mv_open_sw_ = t; } else t_mv_open_sw_ = -1.0;
  bool sample = false;
  if (st_ == State::PREPRESS) sample = both && seated && !bleed_active_ && t_mv_open_sw_ >= 0.0 && t - t_mv_open_sw_ >= kS1ZeroMvOpen_s;
  else if (st_ == State::COAST && !s1_coast_zero_done_) {
    const double tc = t - t_coast_;
    sample = both && seated && in.mv_closed_sw && tc >= kS1CoastZeroFrom_s && tc <= kS1CoastZeroTo_s;
    if (tc > kS1CoastZeroTo_s) s1_coast_zero_done_ = true;   // window over (with or without a complete block)
  }
  if (sample) {
    s1_acc_ += dp; ++s1_n_;
    if (s1_n_ >= kS1ZeroN) {
      const float z = s1_acc_ / static_cast<float>(s1_n_);
      if (std::fabs(z) <= kS1ZeroMax_Pa) { s1_zero_ = z; s1_zero_ok_ = true; }   // larger = transducer fault: keep the previous zero
      s1_acc_ = 0.0f; s1_n_ = 0;
      if (st_ == State::COAST) s1_coast_zero_done_ = true;   // one block per coast
    }
  } else if (st_ != State::PREPRESS) { s1_acc_ = 0.0f; s1_n_ = 0; }
  const bool watch = (st_ == State::ARMED || st_ == State::COAST) && in.mv_closed_sw && s1_zero_ok_ && both &&
                     !(st_ == State::COAST && !s1_coast_zero_done_);   // COAST: after this coast's zero window
  s1_dp_ = watch ? dp - s1_zero_ : std::numeric_limits<float>::quiet_NaN();
  if (p_s1_.step(watch && s1_dp_ > kS1DpMax_Pa, kS1Time_s, kDt_s) && !s1_fault_) {
    s1_fault_ = true; s1_event_ = true; faults_ |= fault::MV;
    if (stand_ ? kS1LockoutStand : kS1LockoutFlight) setLockout();
  }
  if (s1_fault_) faults_ |= fault::MV;
}

// v2.6 pintle stall / tracking monitor (LEAD 2026-10-12: position error plus current or time -> back off the command, fault
// flag, the PINTLE_FAULT abort of the throttle path (MV unlatched = backstop); log every jam: bearing A is replaced before the
// next flight). Runs while the pintle servo is powered (ARM bus on and not released on purpose) in every state but SAFE.
// Episode: |cmd - lift| > kPintleStallErr_m. Progress mark: the lift moved >= kPintleProgMin_m toward the command since the
// last mark (same definition as calc/pintle_dynamics_v2.py noprog_max; normal operation <= 24 ms). Trips:
//   time path     no progress mark for kPintleStallTime_s (0.10 s)
//   current path  rail current > kPintleStallI_A with no mark for kPintleProgWin_s, continuously for kPintleStallTimeI_s (0.05 s)
//   tracking      episode longer than kPintleTrackTime_s (0.6 s) while creeping
// RUNAWAY when the lift moved away from the command. Action: jam event (first per DISARM cycle), back-off, fault::PINTLE,
// PINTLE_FAULT abort; in ABORT (already closing) the ARM bus is released so the spring back-drives the unpowered servo.
// The episode is not restarted after a trip: a needle that still makes no closing progress in ABORT releases the bus at once.
// SAFE: one check after power removal that the spring closed the needle (jam NOT_CLOSED otherwise).
void EngineEcu::pintleMonitor(const Inputs& in, double t, bool* aborted) {
  *aborted = false;
  if (st_ == State::SAFE) {
    pintleMonReset();
    if (safe_chk_ && t - t_state_ + 1e-6 >= kPintleUnpoweredClose_s) {
      safe_chk_ = false;
      if (in.pintle_meas_valid && in.pintle_meas_m > kPintleStallErr_m) {
        faults_ |= fault::PINTLE;
        if (pint_kind_ == jam::NONE) pintleJam(jam::NOT_CLOSED, in, t);
      }
    }
    return;
  }
  if (!in.pintle_meas_valid) { faults_ |= fault::ENCODER; pintleMonReset(); return; }
  if (!in.arm_bus_on || arm_drop_) { pintleMonReset(); return; }   // servo unpowered: nothing to supervise
#ifdef ECU_SIL_TEST_HOOKS
  if (test_disable_pintle_mon) { pintleMonReset(); return; }
#endif
  const float e = pintle_cmd_ - in.pintle_meas_m;
  if (std::fabs(e) <= kPintleStallErr_m) { pintleMonReset(); return; }
  const float dir = e > 0.0f ? 1.0f : -1.0f;
  if (!pint_active_) { pint_active_ = true; t_pint_err_ = t; pint_ref_m_ = in.pintle_meas_m; t_pint_ref_ = t; }
  else if ((in.pintle_meas_m - pint_ref_m_) * dir >= kPintleProgMin_m) { pint_ref_m_ = in.pintle_meas_m; t_pint_ref_ = t; }
  const double noprog = t - t_pint_ref_;
  pint_noprog_s_ = static_cast<float>(noprog);
  const bool cur = in.pintle_i_valid && in.pintle_i_A > kPintleStallI_A && noprog + 1e-6 >= kPintleProgWin_s;
  if (!cur) t_pint_i_ = -1.0;
  else if (t_pint_i_ < 0.0) t_pint_i_ = t;
  uint8_t kind = jam::NONE;
  if (noprog + 1e-6 >= kPintleStallTime_s) kind = jam::STALL_TIME;
  else if (t_pint_i_ >= 0.0 && t - t_pint_i_ + 1e-6 >= kPintleStallTimeI_s) kind = jam::STALL_CURRENT;
  else if (t - t_pint_err_ + 1e-6 >= kPintleTrackTime_s) kind = jam::TRACK_TIMEOUT;
  if (kind == jam::NONE) return;
  if ((in.pintle_meas_m - pint_ref_m_) * dir <= -kPintleProgMin_m) kind = jam::RUNAWAY;
  faults_ |= fault::PINTLE;
  if (pint_kind_ == jam::NONE) pintleJam(kind, in, t);
  pint_backoff_ = true;
  if (st_ == State::ABORT) { arm_drop_ = true; return; }
  doAbort(Abort::PINTLE_FAULT, t);
  *aborted = true;
}

void EngineEcu::pintleJam(uint8_t kind, const Inputs& in, double t) {
  if (pint_kind_ == jam::NONE) pint_kind_ = kind;
  pint_backoff_ = true;
  jam_ev_.t_s = t; jam_ev_.state = static_cast<uint8_t>(st_); jam_ev_.kind = kind;
  jam_ev_.cmd_m = pintle_cmd_; jam_ev_.meas_m = in.pintle_meas_m;
  jam_ev_.i_A = in.pintle_i_valid ? in.pintle_i_A : -1.0f;
  jam_ev_.noprog_s = pint_active_ ? static_cast<float>(t - t_pint_ref_) : 0.0f;
  if (jam_count_ < 0xFFFFu) ++jam_count_;
  jam_ev_.count = jam_count_;
  jam_event_ = true; jam_since_clear_ = true;
}

// v2.7 torch valves (Combustion review RC-01): open from IGNITION entry (COMB t 0); BOTH close on the light-confirmation event
// (+ kTorchHoldAfterLight_s) or at once when the raw Pc reaches the propane limit less the allowance (propane would stop
// flowing), latched per start; an abort closes them with everything else (igniter_enable off). The N2O torch valve is never open
// without the propane valve (prop = n2o, optionally lagging after the N2O close). Spark train only while the valves are open.
void EngineEcu::torchStep(const Inputs& in, double t, double ti, bool* ign_en, bool* spark, bool* n2o, bool* prop) {
  const float pc_raw_abs = in.pc_Pa - pc_zero_ + pamb_Pa;
  prop_bs_n_ = pc_raw_abs >= eng::kPropaneOffPcAbs_Pa - kPropaneCloseAllow_Pa ? prop_bs_n_ + 1 : 0;   // v2.10 RE-18 persistence
  if (!torch_closed_ && ((lit_ && t - t_lit_ + kTimeEps_s >= kTorchHoldAfterLight_s) || prop_bs_n_ >= kPropaneBackstopN)) {
    torch_closed_ = true; t_torch_close_ = t; prop_closed_ = true;
  }
  *n2o = !torch_closed_ && ti >= eng::kTorchSolOpen_s;
  *prop = *n2o || (torch_closed_ && t - t_torch_close_ < kTorchPropaneLag_s);
  *spark = false;
  if (*n2o && ti >= eng::kSparkStart_s && ti < eng::kSparkStart_s + eng::kSparkTrain_s) {
    const double ph = std::fmod(ti - eng::kSparkStart_s, 1.0 / eng::kSparkRate_Hz);
    *spark = ph < kSparkDwell_s;
  }
  *ign_en = *prop || *spark;
}

void EngineEcu::step(const Inputs& in, const Commands& cmd, Outputs& out) {
  const float dt = kDt_s;
  const double t = in.t_s;
  t_now_ = t;
  faults_ &= static_cast<uint16_t>(~(fault::LINK_DEGRADED | fault::LINK_LOST | fault::OPEN_LOOP));
  jam_event_ = false; maint_clear_ = false; gcal_changed_ = false;     // v2.6 one-tick pulses
  lockout_event_ = false; lockout_clear_ = false;                      // v2.7 one-tick pulses
  lit_session_event_ = false; lit_session_close_ = false;
  cmd_refused_event_ = false; s1_event_ = false;                       // v2.8 one-tick pulses
  seg_vap_event_ = false; seg_vap_clear_ = false;                      // v2.8 final one-tick pulses
  coast_anom_event_ = 0;                                               // v2.8.2 one-tick pulse
  hb_event_ = hb::EV_NONE; rz_event_ = false; a7_event_ = false; hb_flow_event_ = false;                          // v2.9 one-tick pulses
  ls_event_ = false;                                                                      // v2.10 one-tick pulse
  sh_event_ = false;                                                                      // v2.10 one-tick pulse
  if (!sh_boot_seen_) {   // v2.10 (LEAD 172 (1)): a safing hold open at a reset (NV b4) restarts at boot - the elapsed time is unknown
    sh_boot_seen_ = true;
    if (in.nv_safing_hold) { sh_open_ = true; sh_event_ = true; t_sh_ = t; }
  }
  // v2.8 mode (LEAD 2026-10-13): latched at ARM from the strap; in SAFE the live strap AND the load-cell check (timing-only key);
  // a strap / load-cell disagreement after ARM is a flag only (no abort: in flight the mode cannot change)
  if (st_ == State::SAFE) stand_ = modeStrapStand(in) && modeConsistent(in);
  else {
    stand_ = mode_stand_;
    if (!modeConsistent(in) || modeStrapStand(in) != mode_stand_) mode_mismatch_ = true;
  }
  pfeed_ok_ = in.pfeed_valid; ptank_ok_ = in.ptank_valid;
  if (cmd.fc_thrust_valid) {   // v2.8 FC_THRUST; v2.8.1: consecutive-frame count of the over-thrust rule (frames received in flight RUN)
    const bool gap = (t - t_fc_thr_) > kFcThrustStale_s + kTimeEps_s;   // the previous frame is stale: the run of frames restarts
    fc_thr_N_ = cmd.fc_thrust_N; fc_thr_ok_ = cmd.fc_thrust_ok; t_fc_thr_ = t;
    const bool above = st_ == State::RUN && !stand_ && fc_thr_ok_ && fc_thr_N_ > kOverThrust_N;
    overthr_n_ = above ? (gap ? 1 : overthr_n_ + 1) : 0;
  }

  // ---------------- link supervision (CMD_FAST carries thrust + gimbal at 500 Hz)
  if (cmd.aux_valid) {
    const uint8_t nb = (cmd.roll_bits == 0x03) ? 0 : cmd.roll_bits;   // both directions = invalid -> off
    if (nb != roll_bits_) roll_on_since_ = t;
    roll_bits_ = nb; last_aux_t_ = t;
  }
  if (cmd.fast_valid) { last_fast_t_ = t; thrust_cmd_ = cmd.thrust_sp_N; gimbal_cmd_[0] = cmd.gimbal_cmd_rad[0]; gimbal_cmd_[1] = cmd.gimbal_cmd_rad[1]; }
  const double age = t - last_fast_t_;
  const bool link_degraded = age > kLinkDegraded_s, link_lost = age > kLinkLost_s;
  if (link_degraded) faults_ |= fault::LINK_DEGRADED;
  if (link_lost) faults_ |= fault::LINK_LOST;

  // ---------------- sensors (gauge in; absolute for control)
  pc_sensor_ok_ = in.pc_raw_V > kPcSensorMin_V && in.pc_raw_V < kPcSensorMax_V;
  // v2.11 (LEAD CHANGELOG 203 (1)(a) ADOPTED): the HIGH over-range is its own non-sticky bit; PC_VALID (pc_sensor_ok_) is 0 only while it
  // lasts. Flight: it no longer latches fault::PC_SENSOR (pressure, not a sensor fault); LOW / NaN still latch. Stand: as built
  pc_overrange_ = in.pc_raw_V >= kPcSensorMax_V;
  pc_above_fs_ = in.pc_raw_V >= kPcAboveFs_V;
  if (!pc_sensor_ok_ && !(kPcOverrangeNonSticky && !stand_ && pc_overrange_)) faults_ |= fault::PC_SENSOR;
  pc_f_ = pc_lpf_.step(in.pc_Pa - pc_zero_);
  pfeed_lpf_.step(in.pfeed_Pa);
  ptank_lpf_.step(in.ptank_Pa);
  supply_.step(in.vbat_V, in.ibat_A, dt);        // v2.3 FM-PWR-01
  const float pc_abs = pc_f_ + pamb_Pa, pfeed_abs = pfeed_lpf_.y + pamb_Pa, ptank_abs = ptank_lpf_.y + pamb_Pa;
  thrust_est_ = pc_f_ > 1.0e5f ? std::fmax(0.0f, thrust::thrustFromPcAbs(pc_abs, pamb_Pa)) : 0.0f;
  {   // v2.8 state-sensor rule inputs, every tick (latched at E0): R4 validity, R3 superheat at both ends, T_tank for the lift table
    float tsat_feed = 0.0f;
    const bool tsat_ok = in.pfeed_valid && n2o::tsatK(pfeed_abs, &tsat_feed);
    r4_ok_now_ = in.tc_mss1_valid && in.tc_mss2_valid && in.pfeed_valid;
    superheat_now_ = r4_ok_now_ && tsat_ok && in.tc_mss1_K >= tsat_feed + kSuperheatMargin_K && in.tc_mss2_K >= tsat_feed + kSuperheatMargin_K;
    float tt = 0.0f;
    ttank_ok_ = in.ptank_valid && n2o::tsatK(ptank_abs, &tt);
    if (ttank_ok_) ttank_K_ = tt;
  }
  tankUpdate(in, ptank_abs);                       // v2.8 final tank interlock (ARM check and startBlock below use it)
  seg_vap_now_ = segVapourPending(in);             // v2.8 final abort -> vapour segment (RAM or NV b3)
  // v2.8 final TLM VALID basis: the MECO valve closure seen in this coast (CLOSED switch, OPEN clear, latch off)
  if (st_ == State::COAST && !mv_latch_ && in.mv_closed_sw && !in.mv_open_sw) meco_closed_ = true;
  coastPintleStep(in);                             // v2.8.2 RG-08 coast pintle anomaly (before the RELIGHT handling of this tick)
  rezeroStep(in, t);                               // v2.9 coast re-zero (before the commands: a RELIGHT this tick sees the new zero)

  // ---------------- commands
  if (cmd.abort_frame) doAbort(Abort::CMD, t);
  else if (cmd.state_valid) handleCommand(cmd.cmd, cmd.arg, in, t);

  const double ts = t - t_state_;
  bool ign_en = false, spark = false, arm_req = false, tvc_en = false;
  float gimbal_target[2] = {gimbal_cmd_[0], gimbal_cmd_[1]};
  float pintle_target = 0.0f;
  bool ran_controller = false;
  servo_us_[3] = kMvOpenerRest_us;
  ceiling_active_ = false;
  const double ti = t - t_ign_;     // time since IGNITION entry (torch sequence clock)
  bool torch_n2o = false, torch_prop = false;   // v2.7 SOL1 torch N2O, SOL2 torch propane (torchStep)
  switch (st_) {
    case State::SAFE:
      tvc_en = tvc_test_enabled;
      if (!tvc_test_enabled) { gimbal_target[0] = gimbal_target[1] = 0; }
      break;
    case State::ARMED:
      arm_req = true; tvc_en = true;
      if (ts < kAutoZeroTime_s) { pc_zero_acc_ += in.pc_Pa; ++pc_zero_n_; }
      else if (pc_zero_n_ > 0) { pc_zero_ = pc_zero_acc_ / pc_zero_n_; pc_zero_n_ = 0; pc_zero_arm_ = pc_zero_; }   // v2.9: ARM zero kept
      // v2.7: P_torch zero (vented torch) - the 2.0 bar abs gate is only 0.94 x the 070BG TEB above ambient (pc_transducer_v2)
      if (ts < kAutoZeroTime_s) { if (in.ptorch_valid) { ptorch_zero_acc_ += in.ptorch_Pa; ++ptorch_zero_n_; } }
      else if (ptorch_zero_n_ > 0) { ptorch_zero_ = ptorch_zero_acc_ / ptorch_zero_n_; ptorch_zero_n_ = 0; ptorch_zero_arm_ = ptorch_zero_; }
      break;
    case State::PREPRESS: {
      arm_req = true; tvc_en = true;
      // normal: opener steps to cock (servo speed) and holds kMvCockTime_s. Slow priming (v2.2, COMB v2): pintle to the
      // bleed lift, confirm it, then ramp the opener over kMvOpenRampSlow_s, hold kMvCockHold_s; bleed until then.
      // v2.6 LEAD rule (b): every opening ramps (mv_ramp_), relights included; the bleed follows the COMB priming rule.
      const double t_open0 = prime_slow_ ? kBleedSettle_s : 0.0;
      const double t_ramp = mv_ramp_ ? kMvOpenRampSlow_s : 0.0;
      const double t_cock_end = t_open0 + t_ramp + (mv_ramp_ ? kMvCockHold_s : kMvCockTime_s);
      // v2.6: checked only while the bleed is still active (a line already primed has no dead end; v2.2-v2.5 checked it
      // after the bleed had ended, which no test exercised because the rigs had no pintle encoder)
      if (prime_slow_ && bleed_active_ && !bleed_checked_ && ts >= kBleedSettle_s) {
        bleed_checked_ = true;   // the valve must not open into a dead end: no bleed lift on the encoder -> abort
        if (in.pintle_meas_valid && in.pintle_meas_m < kBleedConfirm_m) {
          faults_ |= fault::PINTLE;
          if (pint_kind_ == jam::NONE) pintleJam(jam::BLEED_NOT_CONFIRMED, in, t);   // v2.6: suspected jam (seat break-out)
          doAbort(Abort::PREPRESS_FAIL, t); break;
        }
        // v2.6: no encoder at the bleed check -> on the pad (no start yet) abort; in flight (relight) continue with the flag
        if (!in.pintle_meas_valid && starts_ == 0) { faults_ |= fault::ENCODER; doAbort(Abort::PREPRESS_FAIL, t); break; }
      }
      if (mv_cocking_) mvOpener(ts - t_open0);   // v2.8: shared profile (rest while the bleed settles, ramp, hold, rest)
      bleed_active_ = prime_slow_ && ts < t_cock_end && !feedPrimed(in);
      if (bleed_active_) pintle_target = kBleedLift_m;
      const double t_open_expect = t_open0 + t_ramp;
      // v2.9 head-end bleed pad BIT (first start of the arming session, feed primed, valve cocking done): runs to completion before the
      // ignition entry (adds 5 x kHbleedBitStep_s); a failed step -> BLEED_FAULT (the NC valve closes with the abort)
      if (hbleed_fitted && starts_ == 0 && !hb_bit_pass_ && (t_hb_bit_ >= 0.0 || (feedPrimed(in) && ts > t_cock_end))) {
        bool failed = false;
        hbleedBitStep(in, t, &failed);
        if (failed) { faults_ |= fault::MV; doAbort(Abort::BLEED_FAULT, t); }
        break;
      }
      if (feedPrimed(in) && ts > t_cock_end) {
        if (auto_ignite_ && ventGate()) enter(State::IGNITION, t);   // v2.5 OI-12: waits (hold limit) if not vented; v2.10 RE-07 flight flag
        else if (ts > kPrepressHoldMax_s) enter(State::ARMED, t);
      } else if (ts > t_open_expect + kPrepressTimeout_s && !in.mv_open_sw) {
        faults_ |= fault::MV; doAbort(Abort::PREPRESS_FAIL, t);
      } else if (ts > t_open_expect + 2.0 * kPrepressTimeout_s) {
        doAbort(Abort::PREPRESS_FAIL, t);     // valve open but feed never primed
      }
      break;
    }
    case State::IGNITION: {
      arm_req = true; tvc_en = true;
      if (relight_direct_ && mv_cocking_) mvOpener(t - t_mv_cmd_);   // v2.8 direct relight: the valve opens during the torch phase
      if (!pc_sensor_ok_) {
        // v2.6 OI-6: a HIGH over-range is treated as real pressure (the sense line rings a hard start above the range before the
        // filtered over-pressure check can persist 5 ms, v2.2-v2.9: 3 ms); LOW (open/short) stays a sensor fault. Both abort on this tick.
        if (in.pc_raw_V >= kPcSensorMax_V) { faults_ |= fault::PC_OVERP; doAbort(Abort::HARD_START, t); }
        else doAbort(Abort::PC_SENSOR, t);
        break;
      }
      // v2.7 RC-01 torch-flame gate: P_torch above kTorchLitAbs_Pa for kTorchConfirmN ticks while the main chamber is still
      // vented (gauge < 1 bar). Not confirmed by cfg::kTorchGate_s (v2.8: 0.16 s; v2.7: eng::kTorchConfirmBy_s 0.100 s) -> TORCH_FAULT;
      // the pintle stays seated until the confirmation (v2.8: the lift is commanded AT it), so no main N2O is admitted.
      // Invalid P_torch = not confirmed (fail-safe). Ground timing-only start (bypass_start_): gate bypassed, reduced lift.
      // v2.10 FMEA FA-1 (a) (LEAD CHANGELOG 164 (8)): E1 needs P_torch AND the photodiode lit on the same kTorchConfirmN consecutive
      // ticks (2oo2); each sensor must first be seen dark in this start (stuck high cannot confirm)
      const float pt_abs = in.ptorch_Pa - ptorch_zero_ + pamb_Pa;
      fa1_pt_lit_ = in.ptorch_valid && pt_abs >= kTorchLitAbs_Pa;
      fa1_ph_lit_ = photoLit(in);
      if (photoValid(in) && photo_dark_init_ && in.photo_V - photo_dark_ < 0.5f * kPhotoLitRise_V) photo_dark_seen_ = true;
      if (!torch_ok_) {
        // v2.7: auto-zeroed reading; a reading must first be seen BELOW the threshold in this start (a transducer stuck high or a
        // torch chamber already pressurised cannot confirm a flame)
        if (in.ptorch_valid && pt_abs < kTorchLitAbs_Pa) torch_low_seen_ = true;
        const bool sig = in.ptorch_valid && torch_low_seen_ && pt_abs >= kTorchLitAbs_Pa && pc_f_ < kTorchGateMaxPcG_Pa;
        torch_ok_n_ = sig ? torch_ok_n_ + 1 : 0;                       // P_torch alone (log / diagnosis)
        both_ok_n_ = (sig && photo_dark_seen_ && fa1_ph_lit_) ? both_ok_n_ + 1 : 0;
        if (both_ok_n_ >= kPhotoConfirmN && torch_ok_n_ >= kTorchConfirmN) torch_ok_ = true;   // E1 2oo2 (torch confirmed)
      }
      const bool gate = torch_ok_ || bypass_start_;
      if (!gate && ti > kTorchGate_s + kTimeEps_s) { faults_ |= fault::NO_IGNITION; doAbort(Abort::TORCH_FAULT, t); break; }   // v2.8 0.16 s
      // v2.10 FA-1 (b): torch supervision from the 2oo2 confirmation to E2 (covers a lift held for the closure step): BOTH sensors no
      // flame (an invalid sensor counts as no flame) for kTorchLossTime_s -> TORCH_LOST (pintle and NC valve close; flight: accepted
      // mission loss). Not on a ground timing-only start (no confirmation by design).
      fa1_super_ = torch_ok_ && !lit_;
      fa1_both_dark_ = fa1_super_ && !fa1_pt_lit_ && !fa1_ph_lit_;
      if (p_torch_loss_.step(fa1_both_dark_, kTorchLossTime_s, dt)) { faults_ |= fault::NO_IGNITION; doAbort(Abort::TORCH_LOST, t); break; }
      // v2.10 (LEAD RE-05): a start from PURGE whose closure step has not ended by the deadline (= kTorchGate_s from E0, <= the torch
      // gate): the step is forced to NOT CONFIRMED (V2 commanded closed, BLEED_FAULT to the FC; stand abort) and the lift may follow
      if (purge_start_ && !hb_close_done_ && ti + kTimeEps_s >= kTorchGate_s) {
        bool ab = false;
        hb_cmd_[0] = false; hbCloseResult(t, true, &ab);
        if (ab) break;
      }
      // v2.9 light (E2) by the LEAD-adopted relative rule (ignDetect; v2.6-v2.8.3: filtered AND raw above 3.0 bar abs for 5 ticks).
      // LEAD rule (a): the pintle stays at the ignition lift until then
      const bool light = ignDetect(in, t);
      if (light) {
        lit_ = true; lit_since_boot_ = true; t_lit_ = t;
        if (!lit_session_) { lit_session_ = true; lit_session_event_ = true; }   // v2.7: HAL sets NvJamRecord b2 (one write)
      }
      torchStep(in, t, ti, &ign_en, &spark, &torch_n2o, &torch_prop);   // v2.7: closes both torch valves on this tick if lit
      // v2.8 (LEAD 2026-10-13): the ignition-lift command is issued AT the torch confirmation (E1; v2.7: at max(E1, 0.12 s)); a
      // ground timing-only start lifts at the COMB 0.12 s slot. Lift = the lift-vs-T_tank table at E0 (cold-flow defined, CF-3;
      // v2.5-v2.7: Combustion's 20 % lift) scaled by the map trim learned in earlier burns of this arming session. LEAD rule (a):
      // never past the ignition lift before Pc confirms light - a positive trim is not applied, a negative one reduces the lift.
      // The ignition window W counts from the lift command: no light by t_lift + W -> NO_IGNITION.
      // v2.10 (LEAD RE-05): E1 = torch confirmed 2oo2 AND the closure step ended (confirmed, or not confirmed by the deadline), and
      // never with a bleed valve commanded open (hbLiftClear); the 2oo2 state must not be 'both dark' on the lift tick
      if (t_lift_ < 0.0 && ((torch_ok_ && !fa1_both_dark_) || (bypass_start_ && ti + kTimeEps_s >= kTimingOnlyLiftAt_s)) && hbLiftClear()) {
        // v2.10 RE-02 (LEAD): P0 above +check on the pad (no light yet this power cycle) or the stand -> the lift is REFUSED (PC_SENSOR)
        if (ign_detect_relative && (stand_ || !lit_since_boot_) && baseHighNow()) {
          f2_ |= f2::BASE_HIGH; faults_ |= fault::PC_SENSOR; doAbort(Abort::PC_SENSOR, t); break;
        }
        t_lift_ = t;
      }
      if (t_lift_ >= 0.0) pintle_target = std::fmin(kPintleUnlitLiftMax_m, ign_lift_m_ * std::fmin(1.0f, 1.0f + pcc_.trim()));
      if (light) enter(State::RUN, t);                                                         // E2 (v2.9 relative rule)
      else if (t_lift_ >= 0.0 && t - t_lift_ > ign_w_s_ + kTimeEps_s) { faults_ |= fault::NO_IGNITION; doAbort(Abort::NO_IGNITION, t); }
      break;
    }
    case State::RUN: {
      arm_req = true; tvc_en = true;
      if (relight_direct_ && mv_cocking_) mvOpener(t - t_mv_cmd_);   // v2.8: a fast light (E0->RUN ~0.26 s) before the latch hold ends
      torchStep(in, t, ti, &ign_en, &spark, &torch_n2o, &torch_prop);   // v2.7: normally closed already at the RUN entry tick
      // v2.10 REV-GNC-2 (2) FLAMEOUT_OPT: the main-chamber view is proven (lit kPhotoViewProveN ticks after the torch closed); with the Pc
      // channel invalid the photodiode reading no flame for kPhotoFlameoutTime_s aborts FLAMEOUT (A3 is suspended without Pc)
      if (kPhotoFlameoutOpt) {
        if (!photo_run_ref_ok_) {
          fo_view_n_ = (torch_closed_ && photoLit(in)) ? fo_view_n_ + 1 : 0;
          if (fo_view_n_ >= kPhotoViewProveN) photo_run_ref_ok_ = true;
        }
        fo_opt_armed_ = photo_run_ref_ok_ && !pc_sensor_ok_ && photoValid(in);
        if (p_photo_fo_.step(fo_opt_armed_ && !photoLit(in), kPhotoFlameoutTime_s, dt)) {
          faults_ |= fault::FLAMEOUT; doAbort(Abort::FLAMEOUT, t); break;
        }
      }
      // v2.7: Pc-sensor loss in RUN aborts on the test stand (finite load cell); in flight the burn continues open loop (below)
      if (p_pcsens_.step(stand_ && !pc_sensor_ok_, kPcSensorLossStand_s, dt)) { faults_ |= fault::PC_SENSOR; doAbort(Abort::PC_SENSOR, t); break; }
      // v2.5 start ramp: the thrust command is followed at <= kStartRamp_Nps until it is first reached, then directly
      // (the Pc setpoint slew kPcSpRateLimit_Paps still applies; a pre-MECO throttle-down is an ordinary FC command)
      float thr = thrust_cmd_;
      // v2.10 LEAD CHANGELOG 186 (2) R2 command hold (config.h): flight, drogue attached, Pc invalid -> open-loop command held at the start
      // level at once; the start-ramp limiter is parked at the held value so the command returns at <= kStartRamp_Nps after the release
      r2_hold_ = !stand_ && drogue_attached_ && !pc_sensor_ok_;
      if (r2_hold_) {
        thr = std::fmin(thrust_cmd_, kR2HoldThrust_N);
        thr_rl_.reset(thr); hold_ramp_ = true;
      } else if (start_ramp_ || hold_ramp_) {
        thr = thr_rl_.step(thrust_cmd_, kStartRamp_Nps, dt);
        if (std::fabs(thr - thrust_cmd_) < 0.5f) { start_ramp_ = false; hold_ramp_ = false; }
      }
      float sp = thrust::pcAbsFromThrust(thr, pamb_Pa);
      const float ceiling = pfeed_abs / (1.0f + eng::kDpOverPcMin);   // COMB stability rule dP/Pc >= 0.25
      if (sp > ceiling) { sp = ceiling; ceiling_active_ = true; }
      if (link_lost) {
        if (link_policy == LinkPolicy::SHUTDOWN || age > kLinkLost_s + link_hold_s) { doAbort(Abort::LINK_LOST, t); break; }
        gimbal_target[0] = gimbal_target[1] = 0;
      }
      if (!pc_sensor_ok_) faults_ |= fault::OPEN_LOOP;
      pintle_target = pcc_.step(sp, pc_abs, ptank_abs, dt, pc_sensor_ok_, ts > kRunIntegHold_s,
                                in.pintle_meas_valid ? in.pintle_meas_m : std::numeric_limits<float>::quiet_NaN());
      lift_clamp_now_ = pcc_.liftClamped();   // v2.10 RE-04 travel clamp (f2::LIFT_CLAMP, per tick, RUN only)
      ran_controller = true;   // controller already rate-limits
      pc_ref_ = pc_ref_lpf_.step(pcc_.setpointActive());
      break;
    }
    case State::SHUTDOWN: case State::ABORT:
      arm_req = true; tvc_en = true;
      if (st_ == State::ABORT) {
        gimbal_target[0] = gimbal_target[1] = 0;
        // the pintle is driven shut under power (the servo retracts, the spring and the pressure close the needle). v2.2 Pc
        // check kept: Pc still above the over-pressure limit after kAbortPcCheck_s -> release the ARM bus (the MV is already
        // unlatched). v2.6: the 40 ms 'still open' check is retired (config.h); the progress monitor releases the bus when
        // the needle makes no closing progress for kPintleStallTime_s (runaway or jam).
        if (!arm_drop_ && ts > kAbortPcCheck_s && pc_abs > kPcOverPressureAbs_Pa) arm_drop_ = true;
        if (arm_drop_) arm_req = false;
      }
      // v2.7 RC-01 normal shutdown: the NC valve is unlatched once the encoder shows the needle seated (kSeatConfirmN ticks at or
      // below kPintleSeatConfirm_m) or after kMvSeatTimeout_s regardless (flagged; fault PINTLE if the encoder was valid)
      if (st_ == State::SHUTDOWN && mv_seat_wait_) {
        seat_n_ = (in.pintle_meas_valid && in.pintle_meas_m <= kPintleSeatConfirm_m) ? seat_n_ + 1 : 0;
        const bool seated = seat_n_ >= kSeatConfirmN;
        if (seated || ts + kTimeEps_s >= kMvSeatTimeout_s) {
          mv_seat_wait_ = false; mv_latch_ = false; t_mv_cmd_ = t; mv_seat_timeout_ = !seated;
          if (!seated && in.pintle_meas_valid) faults_ |= fault::PINTLE;
        }
      }
      // v2.8.1: the 'chamber vented' exit needs a VALID Pc channel; an invalid reading (failed low) cannot end ABORT/SHUTDOWN early: the
      // pintle stays powered and driven closed until kShutdownTimeout_s (v2.8: an invalid reading below 1.5 bar ended ABORT at 50 ms and
      // dropped the ARM bus, ending the powered pintle closing with the flow cut resting on the NC valve alone)
      if (((pc_sensor_ok_ && pc_f_ < kShutdownPcDone_Pa && ts > 0.05) || ts > kShutdownTimeout_s) && !mv_seat_wait_) {
        if (st_ == State::ABORT) enter(State::SAFE, t);
        else enter(starts_ < kMaxStarts ? State::COAST : State::SAFE, t);   // v2.9: the v2.2 post-shutdown PURGE placeholder is retired
      }
      break;
    case State::PURGE: {
      // v2.9 head-end bleed forced purge (config.h 'head-end bleed' block; set up by enterPurge): NC valve latched with the opener ramp,
      // pintle commanded seated (pintle_target stays 0), V1 and V2 open. The stall monitor stays active (monitors()).
      arm_req = true; tvc_en = true;
      if (mv_cocking_) mvOpener(ts);
      if (in.mv_open_sw) mv_open_seen_ = true;
      // pintle held seated (LEAD: PINTLE_FAULT and the lift-encoder aborts stay active). Encoder invalid: stand PINTLE_FAULT; flight flag +
      // RG-08 UNKNOWN latch (the relight from this purge continues: an abort in flight loses the vehicle). Needle off the seat -> PINTLE_FAULT
      if (!in.pintle_meas_valid) {
        purge_open_n_ = 0;
        if (stand_) { faults_ |= fault::ENCODER; doAbort(Abort::PINTLE_FAULT, t); break; }
        faults_ |= fault::ENCODER;
        if (!hb_purge_enc_) { hb_purge_enc_ = true; hbEvent(hb::EV_PURGE_ENC); }
        if (!coast_enc_lost_) { coast_enc_lost_ = true; coast_anom_event_ = 1; }
      } else {
        purge_open_n_ = in.pintle_meas_m > kCoastPintleOpen_m ? purge_open_n_ + 1 : 0;
        if (purge_open_n_ >= kCoastPintleOpenN) { faults_ |= fault::PINTLE; doAbort(Abort::PINTLE_FAULT, t); break; }
      }
      // NC valve open and the segment filling (LEAD: P_feed check), deadlines as in PREPRESS
      const double t_open_expect = mv_ramp_ ? kMvOpenRampSlow_s : 0.0;
      const bool primed = feedPrimed(in);
      if (primed) purge_filled_ = true;
      if (!mv_open_seen_ && ts > t_open_expect + kPrepressTimeout_s) { faults_ |= fault::MV; doAbort(Abort::PREPRESS_FAIL, t); break; }
      if (!purge_filled_ && ts > t_open_expect + 2.0 * kPrepressTimeout_s) { doAbort(Abort::PREPRESS_FAIL, t); break; }
      // v2.10 schedule on FLOW time (LEAD CHANGELOG 164; config.h 'head-end bleed' block)
      if (t_hb_v2open_ < 0.0) {
        // FILL STEP (V1 open, V2 closed): V2 opens at kPurgeFlowStart_s - kHbleedOpenTime_s once the NC valve OPEN switch was seen and
        // the segment showed primed, with the path proven (P_mid high kHbleedConfirmN ticks); not proven -> kHbleedPathBy_s later with
        // the flag (flight) / BLEED_FAULT abort (stand)
        const bool ready = ts + kTimeEps_s >= kPurgeFlowStart_s - kHbleedOpenTime_s && mv_open_seen_ && purge_filled_;
        if (ready && t_hb_ready_ < 0.0) t_hb_ready_ = t;
        if (ready && (hb_path_ || t - t_hb_ready_ + kTimeEps_s >= kHbleedPathBy_s)) {
          hb_path_checked_ = true;
          if (!hb_path_) {
            hb_path_flag_ = true; hbEvent(hb::EV_PATH_NOT_PROVEN);
            if (stand_) { faults_ |= fault::MV; doAbort(Abort::BLEED_FAULT, t); break; }
          }
          hb_cmd_[1] = true; t_hb_v2open_ = t; t_hb_flow0_ = t + kHbleedOpenTime_s; hb2_ |= hb2::FLOW;
          if (hb_event_ == hb::EV_NONE) hbEvent(hb::EV_FLOW_START);
        }
      } else if (t_hb_v1c_ < 0.0 && hb_cmd_[0] && t + kTimeEps_s >= t_hb_flow0_ + kPurgeFlow_s - kHbleedCloseTime_s
#ifdef ECU_SIL_TEST_HOOKS
                 && !test_inhibit_purge_close
#endif
                 ) {
        hbClose(t);   // V1 close command: the flow ends kHbleedCloseTime_s later; the closure step (vent, hold test) runs in hbleedStep
      }
      // IGNITION (RELIGHT received during the purge; v2.10 LEAD 175: no sequence-integrated purge) once the flow has ended kPurgeFlowEndLead_s before and both valves are
      // commanded closed; never earlier (no truncation for T_fire). The lift then waits for the end of the closure step (IGNITION).
      const bool flow_over = t_hb_v1c_ >= 0.0 && !hb_cmd_[0] && !hb_cmd_[1] &&
                             t + kTimeEps_s >= t_hb_v1c_ + kHbleedCloseTime_s + kPurgeFlowEndLead_s;
      if (purge_ign_ && flow_over && primed && ventGate()) { enter(State::IGNITION, t); break; }   // v2.10 RE-07 flight flag
      // post-flow hold with the bleed CLOSED (v2.10; the v2.9 open-valve hold is deleted, LEAD RE-05): no RELIGHT by the scheduled
      // E0 + kPurgeHoldMax_s -> the purge expires (flagged), COAST
      if (flow_over && t > t_hb_v1c_ + kHbleedCloseTime_s + kPurgeFlowEndLead_s + kPurgeHoldMax_s + kTimeEps_s) {
        hb_hold_to_ = true; hbEvent(hb::EV_HOLD_TIMEOUT);
        enter(State::COAST, t);
      }
      break;
    }
    case State::COAST:
      arm_req = true; tvc_en = true;
      if (mv_latch_ && t - t_coast_ > kCoastMvMax_s) { mv_latch_ = false; t_mv_cmd_ = t; }
      break;
  }
  // link loss outside RUN
  if (link_lost && (st_ == State::ARMED || st_ == State::PREPRESS || st_ == State::IGNITION || st_ == State::COAST || st_ == State::PURGE))
    doAbort(Abort::LINK_LOST, t);

  // v2.10 FA-1 sequence check (LEAD CHANGELOG 164 (8)): in IGNITION no pintle opening without the lift command, and the lift command
  // only after E1 (2oo2) or on the ground timing-only start; by construction never true - an invariant against future edits
  if (st_ == State::IGNITION && pintle_target > 0.0f && !(t_lift_ >= 0.0 && (torch_ok_ || bypass_start_))) pintle_target = 0.0f;
  // ---------------- actuator commands
  if (st_ == State::RUN && ran_controller && !pint_backoff_) {
    pintle_cmd_ = pintle_target;
    pintle_rl_.reset(pintle_cmd_);
  } else {
    const bool opening = ((st_ == State::IGNITION) || (st_ == State::RUN)) && !pint_backoff_;   // RUN entered this tick
    const bool bleed = st_ == State::PREPRESS && bleed_active_ && !pint_backoff_;              // v2.2 priming bleed lift
    if (!opening && !bleed) pintle_target = 0.0f;                                            // v2.6 back-off: closed
    pintle_cmd_ = pintle_rl_.step(pintle_target, (opening || bleed) ? kPintleRateCmd_mps : kPintleCloseRate_mps, dt);
  }
  tvc_.bypass_filters = tvc_test_raw && tvc_test_enabled && st_ == State::SAFE;   // v2.6: never outside the SAFE bench mode
  tvc_.step(gimbal_target, dt, gimbal_shaped_, servo_us_);
  for (int k = 0; k < 2; ++k) gimbal_model_[k] += (gimbal_shaped_[k] - gimbal_model_[k]) * (dt / kGimbalModelTau_s);
  servo_us_[2] = linkage::liftToUs(pintle_cmd_, pcal_);

  const State st_before_mon = st_;
  monitors(in, t);
  if (st_ == State::ABORT && st_before_mon != State::ABORT) {
    // v2.7 abort matrix: an abort raised by a monitor (over-pressure, flameout, rail loss, stall ...) closes the pintle on THIS tick,
    // in parallel with the NC valve (unlatched in enter(ABORT)); the command was computed above for the previous state
    pintle_cmd_ = pintle_rl_.step(0.0f, kPintleCloseRate_mps, dt);
    servo_us_[2] = linkage::liftToUs(pintle_cmd_, pcal_);
  }

  // ---------------- outputs
  const bool burning = st_ == State::IGNITION || st_ == State::RUN;
  for (int k = 0; k < 4; ++k) out.servo_us[k] = servo_us_[k];
  out.servo_enable_tvc = tvc_en;
  out.arm_bus_request = arm_req && st_ != State::SAFE && !arm_drop_;   // arm_drop_ may be set by this tick's monitors
  out.mv_latch = mv_latch_ && (st_ == State::PREPRESS || burning || st_ == State::SHUTDOWN || st_ == State::COAST || st_ == State::PURGE);
  out.igniter_enable = ign_en && burning;
  out.spark_gate = spark && out.igniter_enable;
  out.sol[0] = torch_n2o && out.igniter_enable;      // SOL1 torch N2O (v2.7: closed on the light-confirmation event)
  out.sol[1] = torch_prop && out.igniter_enable;     // SOL2 torch propane (v2.7: with SOL1, or kTorchPropaneLag_s after it)
  out.sol[2] = vent_cmd_;
  // roll couples: only in flight states, dead-man on CMD_AUX, on-time limit; the ARM bus gates them in hardware
  const bool roll_ok = (st_ == State::IGNITION || st_ == State::RUN || st_ == State::SHUTDOWN || st_ == State::COAST) &&
                       (t - last_aux_t_) <= kRollDeadman_s && (t - roll_on_since_) <= kRollMaxPulse_s;
  out.sol[3] = roll_ok && (roll_bits_ & 1u);
  out.sol[4] = roll_ok && (roll_bits_ & 2u);
  // v2.10 FA-1: photodiode dark level, tracked while no start is running (frozen from the IGNITION entry tick through RUN)
  if (st_ != State::IGNITION && st_ != State::RUN && photoValid(in)) {
    if (!photo_dark_init_) { photo_dark_ = in.photo_V; photo_dark_init_ = true; }
    else photo_dark_ += (in.photo_V - photo_dark_) * (kDt_s / kPhotoDarkTau_s);
  }
  riseTrack(in, t);                                  // v2.9 drogue-release support terms (after the state logic of this tick)
  lightSpikeTrack(in, t);                            // v2.10 LIGHT_SPIKE record (A5 deleted)
  out.state = st_; out.abort_cause = abort_; out.fault_bits = faults_;
  out.state_event = st_ != st_out_prev_;   // v2.10 REV-GNC-2 (1): EVENT STATE source (E2 = change to RUN, t_ms = this tick)
  if (out.state_event) t_state_ms_ = static_cast<uint32_t>(std::llround(t * 1000.0));
  out.state_t_ms = t_state_ms_; st_out_prev_ = st_;
  out.tlm_flags = static_cast<uint8_t>(((ign_det_ & det::LIT) ? tlmf::E2 : 0u) | (rise_now_ ? tlmf::RISE_NOW : 0u) |
                                       (rise_held_ ? tlmf::RISE_HELD : 0u) | (rise_held_t_ ? tlmf::RISE_HELD_T : 0u) |
                                       (r2_hold_ ? tlmf::R2_HOLD : 0u) | (drogue_attached_ ? tlmf::DROGUE : 0u));   // b0-b1 log only
  out.drogue_attached = drogue_attached_; out.r2_hold = r2_hold_;   // v2.10 LEAD 186 (2)
  out.pc_sp_active_Pa = (st_ == State::RUN) ? pcc_.setpointActive() : 0.0f;
  out.pintle_cmd_m = pintle_cmd_;
  out.gimbal_cmd_shaped_rad[0] = gimbal_shaped_[0]; out.gimbal_cmd_shaped_rad[1] = gimbal_shaped_[1];
  out.thrust_est_N = thrust_est_;
  out.pc_valid = pc_sensor_ok_;   // v2.8.2 RG-15: TLM_FAST / TLM_GIMBAL invalid markers
  // v2.11 (LEAD CHANGELOG 203 (1)): non-sticky over-range / above-FS bits and the ride-through CANDIDATE (log v12 ovr_flags)
  out.pc_overrange = pc_overrange_; out.pc_above_fs = pc_above_fs_;
  out.ovp_long_rc = ride_win_ && st_ != State::SAFE;   // HAL: SPI-latched long-RC request (hardware bound 0.75 s, ARM_REQ clear)
  out.ovr_flags = static_cast<uint8_t>((pc_overrange_ ? ovr::OVERRANGE : 0u) | (pc_above_fs_ ? ovr::ABOVE_FS : 0u) |
                                       (ride_win_ ? ovr::RIDE_WIN : 0u) | (ride_tol_ ? ovr::RIDE_TOL : 0u) |
                                       (out.ovp_long_rc ? ovr::LONG_RC : 0u) | (ride_t45_ ? ovr::T45 : 0u) |
                                       (ride_through ? ovr::RIDE_BUILD : 0u));
  // v2.10 (LEAD CHANGELOG 175 (4)): pad launch-commit bit (TLM_RELIGHT d6 b7); (3): encoder lift for TLM_FAST d4-d5 (0xFFFF invalid)
  out.pc_commit_valid = pc_sensor_ok_ && !(faults_ & fault::PC_SENSOR) && !(abort_latched_ && abort_ == Abort::PC_SENSOR);
  out.pintle_meas_m = in.pintle_meas_m; out.pintle_meas_valid = in.pintle_meas_valid;
  out.starts_used = starts_;
  // v2.3 FM-PWR-01 and tank heater permit (firmware layer; the hardware interlock also opens on ARM plug, ARM bus, watchdog)
  heater_permit_ = st_ == State::SAFE && !abort_latched_ && in.ptank_Pa < kHeaterCutPtank_Pa && !in.arm_plug_present &&
                   !(faults_ & (fault::TANK_OVERP | fault::OVER_TEMP));
  out.heater_permit = heater_permit_;
  out.tvc_supply_degraded = tvc_sup_deg_;
  out.vplug_pred_V = supply_.vplugPred();
  out.rsrc_ohm = supply_.rsrcUsed();
  out.rsrc_measured = supply_.measured();
  out.gimbal_flags = static_cast<uint8_t>((out.servo_enable_tvc ? tlmg::TVC_PWR : 0u) | (in.gimbal_meas_valid[0] ? tlmg::ENC_A_OK : 0u) |
                                          (in.gimbal_meas_valid[1] ? tlmg::ENC_B_OK : 0u) | (tvc_sup_deg_ ? tlmg::SUPPLY_DEGRADED : 0u) |
                                          ((faults_ & fault::GIMBAL) ? tlmg::GIMBAL_FAULT : 0u) | (supply_.measured() ? tlmg::RSRC_MEASURED : 0u) |
                                          (heater_permit_ ? tlmg::HEATER_PERMIT : 0u) | (sat_.n_long ? tlmg::SAT_LONG : 0u));
  out.gimbal_sat_flags = sat_flags_;
  out.gimbal_sat_episode_s = sat_.t;
  out.gimbal_sat_max_s = sat_.t_max;
  out.gimbal_sat_long = sat_.n_long;
  out.gimbal_sat_count = sat_.count;
  out.gimbal_notch_on = tvc_.notchEnabled();
  out.gimbal_notch_axes = static_cast<uint8_t>((tvc_.notchEnabled(0) ? 1u : 0u) | (tvc_.notchEnabled(1) ? 2u : 0u));
  out.gimbal_cal_changed = gcal_changed_;
  // v2.6 pintle monitor / jam record
  out.pintle_fault_kind = pint_kind_;
  out.pintle_backoff = pint_backoff_;
  out.pintle_jam_event = jam_event_;
  out.pintle_jam = jam_ev_;
  out.maint_jam_pending = maintJamPending(in);
  out.maint_clear_jam = maint_clear_;
  out.pintle_noprog_s = pint_active_ ? pint_noprog_s_ : 0.0f;
  // v2.7 sequence flags
  const bool start_ctx = st_ == State::IGNITION || st_ == State::RUN;
  out.torch_ok = torch_ok_ && start_ctx;
  out.torch_gate_bypass = bypass_armed_ || (bypass_start_ && start_ctx);
  out.torch_closed = torch_closed_ && start_ctx;
  out.relight_ext = start_ctx && ign_rule_ == rule::FLIGHT_RELIGHT;   // v2.8: W 0.65 s (v2.8.1: flight relights only, stand R3 deleted)
  out.relight_lockout = lockoutPending(in);
  out.relight_lockout_event = lockout_event_;
  out.relight_lockout_clear = lockout_clear_;
  out.safing_hold = sh_open_; out.safing_hold_left_s = static_cast<float>(safingHoldLeft_s()); out.safing_hold_event = sh_event_;
  out.lit_session_event = lit_session_event_;
  out.lit_session_close = lit_session_close_;
  out.mv_seat_wait = mv_seat_wait_;
  out.mv_seat_timeout = mv_seat_timeout_;
  out.prail_lost = prail_lost_;
  out.ign_check_s = st_ == State::IGNITION ? ign_w_s_ : 0.0f;   // v2.8: W from the lift command
  // v2.8
  out.ign_rule = ign_rule_;
  out.ign_lift_t_s = (start_ctx && t_lift_ >= 0.0) ? static_cast<float>(t_lift_ - t_ign_) : -1.0f;
  out.ign_lift_m = ign_lift_m_;
  out.superheat_proven = superheat_e0_ && start_ctx;
  out.relight_direct = relight_direct_ && start_ctx;
  out.s1_zero_ok = s1_zero_ok_;
  out.s1_fault = s1_fault_;
  out.s1_event = s1_event_;
  out.s1_dp_Pa = s1_dp_;
  out.mode_stand = stand_;
  out.mode_mismatch = mode_mismatch_;
  out.fc_thrust_fresh = fc_thr_ok_ && (t - t_fc_thr_) <= kFcThrustStale_s + kTimeEps_s;
  out.cmd_refused = cmd_refused_;
  // v2.8 relight-planning status (TLM_RELIGHT)
  {
    const float pf_abs = pfeed_lpf_.y + pamb_Pa, pt_abs = ptank_lpf_.y + pamb_Pa;
    out.seg_valid = in.pfeed_valid && in.ptank_valid;
    out.seg_primed = segmentPrimed(in);
    out.seg_ratio = (out.seg_valid && pt_abs > 0.0f) ? pf_abs / pt_abs : std::numeric_limits<float>::quiet_NaN();
    const bool in_purge = st_ == State::PURGE;   // v2.9: a RELIGHT is accepted in PURGE (ignition at t_purge, or at once after it)
    out.relight_block = (st_ == State::COAST || in_purge) ? startBlock(in, t) : refuse::NOT_COAST;
    // v2.11 (LEAD 203 (7)): flight, bleed fitted - in COAST a RELIGHT would be refused UNPURGED when nothing else blocks it (READY 0;
    // the FC reads UNPURGED as 'PURGE first': the same startBlock() reasons apply to Cmd::PURGE, which also needs the direct path)
    if (st_ == State::COAST && out.relight_block == refuse::NONE && unpurgedGuard()) out.relight_block = refuse::UNPURGED;
    // v2.8 final (GNC v3 option (c), LEAD 2026-10-13): VALID only after the MECO valve closure (CLOSED seen with OPEN clear and the
    // latch off in this coast, or the closure overdue by kMvCloseConfirm_s: the ECU will then take the prep path). PRIMED exactly when
    // a RELIGHT now takes the direct path; UNKNOWN when P_feed or P_tank is invalid (prep path); UNPRIMED otherwise
    const bool valid = in_purge || (st_ == State::COAST && (meco_closed_ || (!mv_latch_ && t - t_mv_cmd_ > kMvCloseConfirm_s + kTimeEps_s)));
    out.meco_closed = valid;   // v2.9: VALID through a purge too (state PRIMED: the purge runs on the direct path only)
    // v2.8.2 RG-08: a coast encoder loss (latched) is UNKNOWN as well; a coast pintle-open latch is UNPRIMED (directRelightOk false)
    out.relight_state = !valid ? segstate::NONE
                        : (in_purge ? segstate::PRIMED
                           : ((!(in.pfeed_valid && in.ptank_valid) || coast_enc_lost_) ? segstate::UNKNOWN
                                                                                       : (directRelightOk(in) ? segstate::PRIMED : segstate::UNPRIMED)));
    const float w = stand_ ? kIgnWindowRelightStand_s : kIgnWindowRelightLong_s;   // v2.8.1: stand R2 0.35 s (R3 deleted)
    // v2.9: in PURGE the remaining purge time. v2.10 (LEAD 175 (3)): in COAST a RELIGHT is unpurged (no integrated purge), so the
    // direct path has no prep time whether or not the bleed is fitted (810 ms flight); the prep path keeps its prep time (1370 ms)
    float prep = kBleedSettle_s + kMvOpenRampSlow_s + kMvCockHold_s;
    if (in_purge) prep = std::fmax(0.0f, static_cast<float>(purgeE0Est(t) - t));   // v2.10: to the scheduled E0 (flow time)
    else if (unpurgedGuard()) prep = kPurgeRelight_s;   // v2.11 (LEAD 203 (7)): a PURGE must come first (E0 at PURGE + 2.90 s)
    else if (directRelightOk(in)) prep = 0.0f;
    out.relight_worst_ms = static_cast<uint16_t>(std::lround(1000.0f * (prep + kTorchGate_s + w)));
  }
  out.cmd_refused_event = cmd_refused_event_;
  // v2.8 final
  out.seg_vapour = seg_vap_now_;
  out.seg_vapour_event = seg_vap_event_;
  out.seg_vapour_clear = seg_vap_clear_;
  out.tank_T_K = tank_T_K_;
  out.tank_hot = tank_hot_;
  out.tank_cold = tank_cold_;
  out.tank_xcheck = tank_xcheck_;
  out.tank_hot_relight = tank_hot_relight_;
  out.coast_pintle = static_cast<uint8_t>((coast_enc_lost_ ? 1u : 0u) | (coast_pint_open_ ? 2u : 0u));   // v2.8.2 RG-08
  out.coast_pintle_event = coast_anom_event_;
  // v2.9 head-end bleed
  out.hbleed[0] = hb_cmd_[0] && st_ != State::SAFE && hbleed_fitted;
  out.hbleed[1] = hb_cmd_[1] && st_ != State::SAFE && hbleed_fitted;
  out.hbleed_flags = static_cast<uint8_t>((hbleed_fitted ? hb::F_FITTED : 0u) | (hb_path_ ? hb::F_PATH : 0u) | (hb_v1_closed_ ? hb::F_V1_CLOSED : 0u) |
                                          (hb_leak_ ? hb::F_LEAK : 0u) | (hb_bit_pass_ ? hb::F_BIT_PASS : 0u) | (hb_path_flag_ ? hb::F_PATH_FLAG : 0u) |
                                          (hb_hold_to_ ? hb::F_HOLD_TIMEOUT : 0u) | (hb_purge_enc_ ? hb::F_PURGE_ENC : 0u));
  out.hbleed_bit = hb_bit_;
  out.hbleed_event = hb_event_;
  out.purge_left_s = st_ == State::PURGE ? std::fmax(0.0f, static_cast<float>(purgeE0Est(t) - t)) : 0.0f;   // v2.10
  out.hbleed2 = hb2_;
  out.purge_flow_ms = hb_flow_s_ < 0.0f ? 0xFFFFu : static_cast<uint16_t>(std::min(65534L, std::lround(1000.0f * hb_flow_s_)));
  out.purge_flow_event = hb_flow_event_;
  out.bleed_fault = hb_bleed_fault_;
  if (hb_bleed_fault_) f2_ |= f2::BLEED_FAULT;
  out.fault2 = static_cast<uint8_t>(f2_ | (st_ == State::RUN && lift_clamp_now_ ? f2::LIFT_CLAMP : 0u));
  out.fault2_new = static_cast<uint8_t>(f2_ & ~f2_prev_);
  out.fault2_event = out.fault2_new != 0;
  f2_prev_ = f2_;
  // v2.10 FA-1
  out.photo_V = in.photo_V; out.photo_dark_V = photo_dark_;
  out.fa1 = static_cast<uint8_t>((photoValid(in) ? fa1::PHOTO_VALID : 0u) | (photoLit(in) ? fa1::PHOTO_LIT : 0u) |
                                 (fa1_pt_lit_ ? fa1::PT_LIT : 0u) | (torch_ok_ ? fa1::E1_2OO2 : 0u) | (fa1_super_ ? fa1::SUPERVISING : 0u) |
                                 (fa1_both_dark_ ? fa1::BOTH_DARK : 0u) | (photo_dark_seen_ ? fa1::PHOTO_DARK_SEEN : 0u) |
                                 (fo_opt_armed_ ? fa1::FLAMEOUT_OPT : 0u));
  // v2.9 light rule, A3 / A7 diagnostics, coast re-zero
  out.ign_det = static_cast<uint8_t>(ign_det_ | (rz_applied_ ? det::REZERO : 0u));
  out.ign_ref_Pa = (ign_det_ & det::PRE_REF) ? ign_ref_f_ : std::numeric_limits<float>::quiet_NaN();
  out.ign_rise_Pa = (st_ == State::IGNITION && (ign_det_ & det::PRE_REF)) ? ign_rise_f_ : std::numeric_limits<float>::quiet_NaN();
  out.flame_ratio = st_ == State::RUN ? flame_ratio_ : std::numeric_limits<float>::quiet_NaN();
  out.pc_map_Pa = (st_ == State::RUN || st_ == State::IGNITION) ? pc_map_lo_ : std::numeric_limits<float>::quiet_NaN();
  out.a7_phase = a7_phase_;
  out.a7_flag = a7_flag_;
  out.a7_event = a7_event_;
  out.rezero_event = rz_event_;
  out.rezero_shift_Pa = rz_shift_;
  out.rezero_rejected = rz_rejected_;
  out.light_spike = ls_;                             // v2.10
  out.light_spike_event = ls_event_;
  healthy_ = std::isfinite(pc_f_) && std::isfinite(pintle_cmd_) && std::isfinite(gimbal_shaped_[0]) && std::isfinite(gimbal_shaped_[1]);
}

void EngineEcu::fillLog(const Inputs& in, const Outputs& o, LogRecord& r) {
  r.magic = 0xA7E5; r.version = kLogVersion; r.state = static_cast<uint8_t>(o.state);   // v2.11: 12
  {   // v2.10 RE-25: t_us wraps every 71.6 min; the wrap count is logged
    const double tus = in.t_s * 1e6;
    r.t_us = static_cast<uint32_t>(std::fmod(tus, 4294967296.0));
    r.t_us_wraps = static_cast<uint8_t>(std::fmin(255.0, std::floor(tus / 4294967296.0)));
    r.safing_left_s = static_cast<uint16_t>(std::ceil(std::fmin(65535.0, static_cast<double>(o.safing_hold_left_s))));
  }
  r.rec_seq = rec_seq_++;
  r.fault_bits = o.fault_bits; r.abort_cause = static_cast<uint8_t>(o.abort_cause); r.starts_used = o.starts_used;
  r.pc_Pa = pc_f_ + pamb_Pa; r.pc_sp_Pa = o.pc_sp_active_Pa; r.pfeed_Pa = in.pfeed_Pa; r.ptank_Pa = in.ptank_Pa;
  r.pintle_cmd_m = o.pintle_cmd_m; r.pintle_meas_m = in.pintle_meas_m;
  r.ga_cmd_rad = o.gimbal_cmd_shaped_rad[0]; r.gb_cmd_rad = o.gimbal_cmd_shaped_rad[1];
  r.ga_meas_rad = in.gimbal_meas_rad[0]; r.gb_meas_rad = in.gimbal_meas_rad[1];
  r.thrust_est_N = o.thrust_est_N; r.load_cell_N = in.load_cell_N;
  for (int k = 0; k < 4; ++k) {
    r.pc_raw4[k] = 0;   // HAL fills the four 4 kSPS ADC codes of this millisecond
    r.servo_us[k] = static_cast<uint16_t>(o.servo_us[k]);
    r.tc_dK[k] = in.tc_valid[k] ? static_cast<int16_t>(std::lround(clampf((in.tc_K[k] - 273.15f) * 10.0f, -32767.0f, 32767.0f)))
                                : static_cast<int16_t>(INT16_MIN);   // v2.10 RE-25: invalid marker as the other TC fields
  }
  r.vbat_mV = static_cast<uint16_t>(clampf(in.vbat_V, 0.0f, 65.0f) * 1000.0f);
  r.ibat_cA = static_cast<int16_t>(std::lround(clampf(in.ibat_A, -327.0f, 327.0f) * 100.0f));            // v3
  r.vplug_pred_mV = static_cast<uint16_t>(clampf(o.vplug_pred_V, 0.0f, 65.0f) * 1000.0f);                // v3
  r.flags = static_cast<uint16_t>((o.mv_latch ? 1u : 0u) | (o.igniter_enable ? 2u : 0u) | (o.spark_gate ? 4u : 0u) |
                                  (o.arm_bus_request ? 8u : 0u) | (in.arm_bus_on ? 16u : 0u) |
                                  ((o.fault_bits & fault::LINK_LOST) ? 0u : 32u) | (o.sol[0] ? 64u : 0u) | (o.sol[1] ? 128u : 0u) |
                                  (o.sol[2] ? 256u : 0u) | (in.mv_open_sw ? 512u : 0u) | (in.mv_closed_sw ? 1024u : 0u) |
                                  (ceiling_active_ ? 2048u : 0u) | (o.sol[3] ? 4096u : 0u) | (o.sol[4] ? 8192u : 0u) |
                                  (o.tvc_supply_degraded ? 16384u : 0u) | (o.heater_permit ? 32768u : 0u));
  r.sat_ms = static_cast<uint16_t>(clampf(o.gimbal_sat_episode_s * 1000.0f, 0.0f, 65535.0f));             // v4
  r.sat_flags = static_cast<uint8_t>((o.gimbal_sat_flags & 0x0Fu) | (o.gimbal_notch_axes == 3u ? 0x10u : 0u) |   // v4; v5 b4 = both axes
                                     (o.pintle_backoff ? 0x20u : 0u) |                                      // v5: pintle back-off
                                     (o.pintle_noprog_s >= kPintleProgWin_s ? 0x40u : 0u) |                 // v5: no progress > 20 ms
                                     (o.maint_jam_pending ? 0x80u : 0u));                                   // v5: jam record pending
  r.sat_long = o.gimbal_sat_long;                                                                         // v4
  // v6 (v2.7)
  r.ptorch_Pa = in.ptorch_valid ? in.ptorch_Pa : std::numeric_limits<float>::quiet_NaN();
  r.prail_mV = in.prail_valid ? static_cast<uint16_t>(std::lround(clampf(in.prail_V, 0.0f, 65.0f) * 1000.0f)) : static_cast<uint16_t>(0xFFFFu);
  r.pintle_i_mA = in.pintle_i_valid ? static_cast<int16_t>(std::lround(clampf(in.pintle_i_A, -32.0f, 32.0f) * 1000.0f)) : INT16_MIN;
  r.tcb_dK = in.tc_bore_valid ? static_cast<int16_t>(std::lround(clampf((in.tc_bore_K - 273.15f) * 10.0f, -32767.0f, 32767.0f))) : INT16_MIN;
  r.seq_flags = static_cast<uint8_t>((o.torch_ok ? 1u : 0u) | (o.torch_gate_bypass ? 2u : 0u) | (o.relight_ext ? 4u : 0u) |
                                     (o.relight_lockout ? 8u : 0u) | (o.mv_seat_wait ? 16u : 0u) | (o.prail_lost ? 32u : 0u) |
                                     (o.torch_closed ? 64u : 0u) | (o.mv_seat_timeout ? 128u : 0u));
  r.ign_check_cs = static_cast<uint8_t>(clampf(o.ign_check_s * 100.0f + 0.5f, 0.0f, 255.0f));   // v7: W from the lift command
  // v7 (v2.8)
  auto tcd = [](bool v, float K) { return v ? static_cast<int16_t>(std::lround(clampf((K - 273.15f) * 10.0f, -32767.0f, 32767.0f))) : static_cast<int16_t>(INT16_MIN); };
  r.tcm1_dK = tcd(in.tc_mss1_valid, in.tc_mss1_K);
  r.tcm2_dK = tcd(in.tc_mss2_valid, in.tc_mss2_K);
  r.fc_thr_dN = o.fc_thrust_fresh ? static_cast<uint16_t>(clampf(fc_thr_N_ * 10.0f + 0.5f, 0.0f, 65534.0f)) : static_cast<uint16_t>(0xFFFFu);
  r.s1_dp_hPa = std::isfinite(o.s1_dp_Pa) ? static_cast<int16_t>(std::lround(clampf(o.s1_dp_Pa * 0.01f, -32767.0f, 32767.0f))) : static_cast<int16_t>(INT16_MIN);
  r.seq2_flags = static_cast<uint8_t>((o.relight_direct ? 1u : 0u) | (o.superheat_proven ? 2u : 0u) | (o.s1_zero_ok ? 4u : 0u) |
                                      (o.s1_fault ? 8u : 0u) | (o.fc_thrust_fresh ? 16u : 0u) | (o.mode_stand ? 32u : 0u) |
                                      (o.mode_mismatch ? 64u : 0u) | (in.mode_strap == strap::INVALID ? 128u : 0u));
  r.ign_rule = o.ign_rule;
  r.ign_lift_ms = o.ign_lift_t_s < 0.0f ? static_cast<uint8_t>(0xFFu) : static_cast<uint8_t>(clampf(o.ign_lift_t_s * 1000.0f + 0.5f, 0.0f, 254.0f));
  r.cmd_refused = o.cmd_refused;
  r.bay_dK = tcd(in.bay_valid, in.bay_K);   // v7: bay temperature (launch constraint)
  // v8 (v2.8 final): interlock tank temperature and the relight-state / vapour-segment / tank flags
  r.ttank_dK = tcd(std::isfinite(o.tank_T_K), o.tank_T_K);
  r.seq3_flags = static_cast<uint8_t>((o.relight_state & 3u) | (o.seg_vapour ? 4u : 0u) | (o.tank_hot ? 8u : 0u) | (o.tank_xcheck ? 16u : 0u) |
                                      (o.tank_hot_relight ? 32u : 0u) | (o.meco_closed ? 64u : 0u) |
                                      (o.coast_pintle ? 128u : 0u));   // v9 (v2.8.2): b7 coast pintle anomaly latched (RG-08)
  // v10 (v2.9)
  r.hbleed_flags = o.hbleed_flags;
  r.hbleed_io = static_cast<uint8_t>((o.hbleed[0] ? 1u : 0u) | (o.hbleed[1] ? 2u : 0u) | (in.pmid_hi ? 4u : 0u) | (in.pmid_valid ? 8u : 0u) |
                                     ((o.hbleed_event & 0x0Fu) << 4));
  r.hbleed_bit = o.hbleed_bit;
  auto hpa = [](float p) { return std::isfinite(p) ? static_cast<int16_t>(std::lround(clampf(p * 0.01f, -32767.0f, 32767.0f))) : static_cast<int16_t>(INT16_MIN); };
  r.ign_ref_hPa = hpa(o.ign_ref_Pa);
  r.ign_rise_hPa = hpa(o.ign_rise_Pa);
  r.ign_det = o.ign_det;
  r.flame_ratio_pc = std::isfinite(o.flame_ratio) ? static_cast<uint8_t>(clampf(o.flame_ratio * 100.0f + 0.5f, 0.0f, 254.0f)) : static_cast<uint8_t>(0xFFu);
  r.pc_map_hPa = std::isfinite(o.pc_map_Pa) ? static_cast<uint16_t>(clampf(o.pc_map_Pa * 0.01f + 0.5f, 0.0f, 65534.0f)) : static_cast<uint16_t>(0xFFFFu);
  r.seq4_flags = static_cast<uint8_t>((o.a7_phase & 3u) | (o.a7_flag ? 4u : 0u) | (o.a7_event ? 8u : 0u) | ((o.ign_det & det::E3) ? 16u : 0u) |
                                      (o.rezero_event ? 32u : 0u) | (o.rezero_rejected ? 64u : 0u) | (purge_start_ ? 128u : 0u));
  r.tlm_flags = o.tlm_flags;
  // v11 (v2.10): LIGHT_SPIKE record
  {
    const LightSpikeRec& L = o.light_spike;
    auto hpa_u = [](float p) { return std::isfinite(p) ? static_cast<uint16_t>(clampf(p * 0.01f + 0.5f, 0.0f, 65534.0f)) : static_cast<uint16_t>(0xFFFFu); };
    auto ms_i = [](float s) { return std::isfinite(s) ? static_cast<int16_t>(std::lround(clampf(s * 1000.0f, -32767.0f, 32767.0f))) : static_cast<int16_t>(INT16_MIN); };
    auto ms_u16 = [](float s) { return static_cast<uint16_t>(clampf(s * 1000.0f + 0.5f, 0.0f, 65534.0f)); };
    auto ms_u8 = [](float s) { return static_cast<uint8_t>(clampf(s * 1000.0f + 0.5f, 0.0f, 255.0f)); };
    r.ls_raw_hPa = hpa_u(L.peak_raw_Pa);
    r.ls_filt_hPa = hpa_u(L.peak_filt_Pa);
    r.ls_tpk_raw_ms = ms_i(L.t_peak_raw_s);
    r.ls_tpk_filt_ms = ms_i(L.t_peak_filt_s);
    r.ls_tlight_ms = std::isfinite(L.t_light_s) ? ms_u16(L.t_light_s) : static_cast<uint16_t>(0xFFFFu);
    r.ls_t8r_ms = ms_u16(L.t8_raw_s); r.ls_t8f_ms = ms_u16(L.t8_filt_s);
    r.ls_t30r_ms = ms_u8(L.t30_raw_s); r.ls_t30f_ms = ms_u8(L.t30_filt_s);
    r.ls_flags = static_cast<uint8_t>((L.open ? 1u : 0u) | (L.done ? 2u : 0u) | (L.lit ? 4u : 0u) | (o.light_spike_event ? 8u : 0u) |
                                      (L.closed_by_exit ? 16u : 0u) | (L.masked ? 32u : 0u) | (L.overrange ? 64u : 0u) |
                                      (L.abovefs ? 128u : 0u));   // v12 b7 above full scale (LEAD 203 (1)(a))
  }
  r.hb2_flags = o.hbleed2; r.purge_flow_ms = o.purge_flow_ms; r.fa1_flags = o.fa1;   // v2.10 purge, FA-1, f2 flags
  r.photo_mV = (in.photo_valid && std::isfinite(in.photo_V)) ? static_cast<uint16_t>(std::lround(std::fmin(65.534f, std::fmax(0.0f, in.photo_V)) * 1000.0f)) : 0xFFFFu;
  r.photo_dark_mV = static_cast<uint16_t>(std::lround(std::fmin(65.534f, std::fmax(0.0f, o.photo_dark_V)) * 1000.0f));
  r.fault2 = o.fault2;
  r.ovr_flags = o.ovr_flags;   // v12 (v2.11, LEAD 203 (1))
  r.crc16 = crc16_ccitt(reinterpret_cast<const uint8_t*>(&r), sizeof(LogRecord) - 2);
}

}  // namespace ecu
