// ARGOS engine ECU - state machine, sequencing, safety monitor (v2.8.2, 2026-10-13: GNC review REV-GNC-1 RG-08 - a pintle-position
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
                            "OVER_THRUST", "MODE_MISMATCH", "BAY_HOT", "TANK_HOT"};
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
  tank_T_K_ = std::numeric_limits<float>::quiet_NaN(); tank_hot_ = true; tank_xcheck_ = false; tank_hot_relight_ = false; ign_refused_tank_ = 0;
  fc_thr_N_ = 0.0f; fc_thr_ok_ = false; t_fc_thr_ = -1e9; overthr_n_ = 0;
  ptorch_zero_ = 0.0f; ptorch_zero_acc_ = 0.0f; ptorch_zero_n_ = 0; torch_low_seen_ = false;
  lockout_ = false; lockout_event_ = false; lockout_clear_ = false; lit_since_boot_ = false; clear_lockout_refused_ = 0;
  lit_session_ = false; lit_session_event_ = false; lit_session_close_ = false;
  mv_seat_wait_ = false; mv_seat_timeout_ = false; seat_n_ = 0; prail_lost_ = false; t_bus_on_ = -1.0;
  p_prail_.reset(); p_pcsens_.reset();
  coast_enc_lost_ = false; coast_pint_open_ = false; coast_open_n_ = 0; coast_anom_event_ = 0;   // v2.8.2 RG-08
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
  if (!chamberVented() && pad_coast) return refuse::NOT_VENTED;
  if (t - t_unlit_ < kRetryVentWait_s && pad_coast) return refuse::VENT_WAIT;
  if (pre && caseHot(in)) return refuse::CASE_HOT;
  if (pre && starts_ == 0 && bayHot(in)) return refuse::BAY_HOT;
  // v2.8 final tank interlock (LEAD 2026-10-13): pad first start and every stand start; a flight relight is flagged only (step())
  if (pre && tank_hot_ && (starts_ == 0 || stand_)) return refuse::TANK_HOT;
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
  tank_hot_ = !any || tmax > kTankIgnMax_K;
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
  if (s == State::ARMED && prev == State::SAFE) {   // new arming session: forget the learned map trim and the S1 zero
    pcc_.clearTrim();
    s1_zero_ok_ = false; s1_n_ = 0; s1_acc_ = 0.0f; p_s1_.reset();   // v2.8
  }
  p_hard_.reset(); p_flame_.reset(); p_band_.reset(); p_gimb_[0].reset(); p_gimb_[1].reset(); p_pcsens_.reset();
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
      torch_ok_ = false; torch_ok_n_ = 0; torch_closed_ = false; torch_low_seen_ = false;
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
    case State::ABORT: case State::SAFE: case State::PURGE:   // v2.7: every abort de-energises the NC valve at once
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
  if (a == Abort::NO_IGNITION || a == Abort::FLAMEOUT || a == Abort::TORCH_FAULT) t_unlit_ = t;   // v2.5 retry vent wait starts
  // v2.7 LEAD 2026-10-13: no automatic in-flight relight retry. Any abort on a relight or after a lit burn in this power cycle
  // (any state: IGNITION, RUN, SHUTDOWN, COAST, PREPRESS ...) locks further ignition out until the keyed ground CLEAR_LOCKOUT;
  // a first-start no-light keeps the ground retry rule above. (v2.7 draft: IGNITION/RUN/SHUTDOWN only - an abort in COAST
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
  if (!in.mv_closed_sw) { *why = Abort::MV_FAULT; return false; }
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
        tank_xcheck_ = false; tank_hot_relight_ = false;   // v2.8 final flags (the vapour-segment flag stays until a confirmed light)
        coast_enc_lost_ = false; coast_pint_open_ = false; coast_open_n_ = 0;   // v2.8.2 RG-08 (new session: the next start is a pad start)
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
      const uint8_t why = startBlock(in, t);
      if (why != refuse::NONE) {
        if (why != refuse::MAX_STARTS) ++ign_refused_;
        if (why == refuse::NOTCH) ++ign_refused_notch_;
        if (why == refuse::CASE_HOT) ++ign_refused_hot_;
        if (why == refuse::BAY_HOT) ++ign_refused_bay_;
        if (why == refuse::R4_SENSOR) ++ign_refused_r4_;
        if (why == refuse::TANK_HOT) ++ign_refused_tank_;
        refuseCmd(why);
        break;
      }
      cmd_refused_ = refuse::NONE;
      // v2.8 final: a flight relight is never refused on the tank interlock (the tank cools in each burn); flagged and logged
      if (tank_hot_ && starts_ >= 1 && !stand_) tank_hot_relight_ = true;
      // MV held open through the coast (only with kMvHoldOpenInCoast): direct 0.3 s relight; otherwise PREPRESS (rule b)
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
      break;
    case Cmd::PURGE:
      if ((st_ == State::COAST || st_ == State::ARMED) && kPurgeTime_s > 0) enter(State::PURGE, t);
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
      if (st_ == State::SAFE && arg == kClearLockoutKey) { lockout_ = false; lockout_clear_ = true; }
      else ++clear_lockout_refused_;
      break;
    case Cmd::SET_TORCH_GATE:        // v2.7 RC-01: ground timing-only start (stand only); any other argument re-arms the gate
      if (st_ == State::SAFE) bypass_armed_ = (arg == kTorchTimingOnlyKey) && stand_;   // v2.8: stand_ in SAFE = strap AND load cell
      break;
    case Cmd::VENT:
      if (st_ == State::SAFE || st_ == State::ARMED || st_ == State::COAST) vent_cmd_ = (arg != 0);
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
  if (st_ != State::SAFE && fw_ovp_on && p_hard_.step(pc_abs > kPcOverPressureAbs_Pa, kPcOverPressureTime_s, dt)) {
    faults_ |= fault::PC_OVERP;
    const bool ign_phase = st_ == State::IGNITION || (st_ == State::RUN && ts < kRunSettle_s);
    doAbort(ign_phase ? Abort::HARD_START : Abort::PC_OVERPRESSURE, t);
    return;
  }
  // --- v2.8.1 over-thrust (LEAD 2026-10-13 ADOPTED, GNC m2_fc_thrust v1.1): flight, RUN, kOverThrustFrames consecutive fresh valid
  //     FC_THRUST frames above kOverThrust_N (counted at frame receipt in step()). Runs with the Pc channel valid or not: with it lost the
  //     firmware check above and the hardware comparator (same PC_SIG) are blind, and an in-range wrong Pc reading blinds them too
  {
    const bool fresh = fc_thr_ok_ && (t - t_fc_thr_) <= kFcThrustStale_s + kTimeEps_s;
    if (!(st_ == State::RUN && !stand_) || !fresh) overthr_n_ = 0;
    if (overthr_n_ >= kOverThrustFrames) { faults_ |= fault::PC_OVERP; doAbort(Abort::OVER_THRUST, t); return; }
  }
  // --- flameout and Pc band (RUN; band after settle)
  if (st_ == State::RUN && pc_sensor_ok_) {
    const float thr = std::fmax(kFlameoutPc_Pa, kFlameoutFrac * (pc_ref_ - pamb_Pa));
    if (p_flame_.step(pc_f_ < thr, kFlameoutTime_s, dt)) { faults_ |= fault::FLAMEOUT; doAbort(Abort::FLAMEOUT, t); return; }
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
  hot |= in.tc_valid[2] && in.tc_K[2] > kNozzleHolderOverTemp_K;
  if (p_otemp_.step(hot, kOverTempTime_s, dt)) {
    faults_ |= fault::OVER_TEMP;
    if (burning || st_ == State::PREPRESS) { doAbort(Abort::OVER_TEMP, t); return; }
  }
  if (p_servo_hot_.step(in.tc_valid[3] && in.tc_K[3] > kServoBracketOverTemp_K, kOverTempTime_s, dt)) faults_ |= fault::OVER_TEMP;
  // --- tank over-pressure: never aborts a burn (draining lowers pressure); safes the pad states. v2.3: with
  //     tank_overp_pad_only (LEAD conditional on a passive tank relief device) a relight PREPRESS in flight is not aborted.
  const bool pad = starts_ == 0;                 // v2.3: no start made yet = on the pad (a relight also passes PREPRESS)
  const bool pad_state = st_ == State::ARMED || st_ == State::PREPRESS;
  if (p_tankp_.step(in.ptank_Pa > kTankOverPressure_Pa, kTankOverPressureTime_s, dt)) {
    faults_ |= fault::TANK_OVERP;
    if (pad_state && (pad || !tank_overp_pad_only)) { doAbort(Abort::TANK_OVERPRESSURE, t); return; }
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
  if (!torch_closed_ && ((lit_ && t - t_lit_ + kTimeEps_s >= kTorchHoldAfterLight_s) ||
                         pc_raw_abs >= eng::kPropaneOffPcAbs_Pa - kPropaneCloseAllow_Pa)) {
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
  if (!pc_sensor_ok_) faults_ |= fault::PC_SENSOR;
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
      else if (pc_zero_n_ > 0) { pc_zero_ = pc_zero_acc_ / pc_zero_n_; pc_zero_n_ = 0; }
      // v2.7: P_torch zero (vented torch) - the 2.0 bar abs gate is only 0.94 x the 070BG TEB above ambient (pc_transducer_v2)
      if (ts < kAutoZeroTime_s) { if (in.ptorch_valid) { ptorch_zero_acc_ += in.ptorch_Pa; ++ptorch_zero_n_; } }
      else if (ptorch_zero_n_ > 0) { ptorch_zero_ = ptorch_zero_acc_ / ptorch_zero_n_; ptorch_zero_n_ = 0; }
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
      if (feedPrimed(in) && ts > t_cock_end) {
        if (auto_ignite_ && chamberVented()) enter(State::IGNITION, t);   // v2.5 OI-12: waits (hold limit) if not vented
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
        // filtered over-pressure check can persist 3 ms); LOW (open/short) stays a sensor fault. Both abort on this tick.
        if (in.pc_raw_V >= kPcSensorMax_V) { faults_ |= fault::PC_OVERP; doAbort(Abort::HARD_START, t); }
        else doAbort(Abort::PC_SENSOR, t);
        break;
      }
      // v2.7 RC-01 torch-flame gate: P_torch above kTorchLitAbs_Pa for kTorchConfirmN ticks while the main chamber is still
      // vented (gauge < 1 bar). Not confirmed by cfg::kTorchGate_s (v2.8: 0.16 s; v2.7: eng::kTorchConfirmBy_s 0.100 s) -> TORCH_FAULT;
      // the pintle stays seated until the confirmation (v2.8: the lift is commanded AT it), so no main N2O is admitted.
      // Invalid P_torch = not confirmed (fail-safe). Ground timing-only start (bypass_start_): gate bypassed, reduced lift.
      if (!torch_ok_) {
        // v2.7: auto-zeroed reading; a reading must first be seen BELOW the threshold in this start (a transducer stuck high or a
        // torch chamber already pressurised cannot confirm a flame)
        const float pt_abs = in.ptorch_Pa - ptorch_zero_ + pamb_Pa;
        if (in.ptorch_valid && pt_abs < kTorchLitAbs_Pa) torch_low_seen_ = true;
        const bool sig = in.ptorch_valid && torch_low_seen_ && pt_abs >= kTorchLitAbs_Pa && pc_f_ < kTorchGateMaxPcG_Pa;
        torch_ok_n_ = sig ? torch_ok_n_ + 1 : 0;
        if (torch_ok_n_ >= kTorchConfirmN) torch_ok_ = true;
      }
      const bool gate = torch_ok_ || bypass_start_;
      if (!gate && ti > kTorchGate_s + kTimeEps_s) { faults_ |= fault::NO_IGNITION; doAbort(Abort::TORCH_FAULT, t); break; }   // v2.8 0.16 s
      {
        // v2.6 OI-6: light confirmed by kIgnitionConfirmN consecutive ticks with the filtered AND the raw Pc above 3.0 bar abs
        // (COMB rule; LEAD rule (a): the pintle stays at the ignition lift until then)
        const float pc_raw_abs = in.pc_Pa - pc_zero_ + pamb_Pa;
        ign_ok_n_ = (pc_abs > kIgnitionDetectAbs_Pa && pc_raw_abs > kIgnitionDetectAbs_Pa) ? ign_ok_n_ + 1 : 0;
      }
      const bool light = ign_ok_n_ >= kIgnitionConfirmN;
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
      if (t_lift_ < 0.0 && (torch_ok_ || (bypass_start_ && ti + kTimeEps_s >= kTimingOnlyLiftAt_s))) t_lift_ = t;
      if (t_lift_ >= 0.0) pintle_target = std::fmin(kPintleUnlitLiftMax_m, ign_lift_m_ * std::fmin(1.0f, 1.0f + pcc_.trim()));
      if (light) enter(State::RUN, t);                                                                     // COMB 3.0 bar abs
      else if (t_lift_ >= 0.0 && t - t_lift_ > ign_w_s_ + kTimeEps_s) { faults_ |= fault::NO_IGNITION; doAbort(Abort::NO_IGNITION, t); }
      break;
    }
    case State::RUN: {
      arm_req = true; tvc_en = true;
      if (relight_direct_ && mv_cocking_) mvOpener(t - t_mv_cmd_);   // v2.8: a fast light (E0->RUN ~0.26 s) before the latch hold ends
      torchStep(in, t, ti, &ign_en, &spark, &torch_n2o, &torch_prop);   // v2.7: normally closed already at the RUN entry tick
      // v2.7: Pc-sensor loss in RUN aborts on the test stand (finite load cell); in flight the burn continues open loop (below)
      if (p_pcsens_.step(stand_ && !pc_sensor_ok_, kPcSensorLossStand_s, dt)) { faults_ |= fault::PC_SENSOR; doAbort(Abort::PC_SENSOR, t); break; }
      // v2.5 start ramp: the thrust command is followed at <= kStartRamp_Nps until it is first reached, then directly
      // (the Pc setpoint slew kPcSpRateLimit_Paps still applies; a pre-MECO throttle-down is an ordinary FC command)
      float thr = thrust_cmd_;
      if (start_ramp_) {
        thr = thr_rl_.step(thrust_cmd_, kStartRamp_Nps, dt);
        if (std::fabs(thr - thrust_cmd_) < 0.5f) start_ramp_ = false;
      }
      float sp = thrust::pcAbsFromThrust(thr, pamb_Pa);
      const float ceiling = pfeed_abs / (1.0f + eng::kDpOverPcMin);   // COMB stability rule dP/Pc >= 0.25
      if (sp > ceiling) { sp = ceiling; ceiling_active_ = true; }
      if (link_lost) {
        if (link_policy == LinkPolicy::SHUTDOWN || age > kLinkLost_s + link_hold_s) { doAbort(Abort::LINK_LOST, t); break; }
        gimbal_target[0] = gimbal_target[1] = 0;
      }
      if (!pc_sensor_ok_) faults_ |= fault::OPEN_LOOP;
      pintle_target = pcc_.step(sp, pc_abs, ptank_abs, dt, pc_sensor_ok_, ts > kRunIntegHold_s);
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
        else if (kPurgeTime_s > 0) enter(State::PURGE, t);
        else enter(starts_ < kMaxStarts ? State::COAST : State::SAFE, t);
      }
      break;
    case State::PURGE:
      arm_req = true; tvc_en = true;
      if (ts > kPurgeTime_s) enter(starts_ < kMaxStarts ? State::COAST : State::SAFE, t);
      break;
    case State::COAST:
      arm_req = true; tvc_en = true;
      if (mv_latch_ && t - t_coast_ > kCoastMvMax_s) { mv_latch_ = false; t_mv_cmd_ = t; }
      break;
  }
  // link loss outside RUN
  if (link_lost && (st_ == State::ARMED || st_ == State::PREPRESS || st_ == State::IGNITION || st_ == State::COAST))
    doAbort(Abort::LINK_LOST, t);

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
  out.mv_latch = mv_latch_ && (st_ == State::PREPRESS || burning || st_ == State::SHUTDOWN || st_ == State::COAST);
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
  out.state = st_; out.abort_cause = abort_; out.fault_bits = faults_;
  out.pc_sp_active_Pa = (st_ == State::RUN) ? pcc_.setpointActive() : 0.0f;
  out.pintle_cmd_m = pintle_cmd_;
  out.gimbal_cmd_shaped_rad[0] = gimbal_shaped_[0]; out.gimbal_cmd_shaped_rad[1] = gimbal_shaped_[1];
  out.thrust_est_N = thrust_est_;
  out.pc_valid = pc_sensor_ok_;   // v2.8.2 RG-15: TLM_FAST / TLM_GIMBAL invalid markers
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
    out.relight_block = st_ == State::COAST ? startBlock(in, t) : refuse::NOT_COAST;
    // v2.8 final (GNC v3 option (c), LEAD 2026-10-13): VALID only after the MECO valve closure (CLOSED seen with OPEN clear and the
    // latch off in this coast, or the closure overdue by kMvCloseConfirm_s: the ECU will then take the prep path). PRIMED exactly when
    // a RELIGHT now takes the direct path; UNKNOWN when P_feed or P_tank is invalid (prep path); UNPRIMED otherwise
    const bool valid = st_ == State::COAST && (meco_closed_ || (!mv_latch_ && t - t_mv_cmd_ > kMvCloseConfirm_s + kTimeEps_s));
    out.meco_closed = valid;
    // v2.8.2 RG-08: a coast encoder loss (latched) is UNKNOWN as well; a coast pintle-open latch is UNPRIMED (directRelightOk false)
    out.relight_state = !valid ? segstate::NONE
                        : ((!(in.pfeed_valid && in.ptank_valid) || coast_enc_lost_) ? segstate::UNKNOWN
                                                                                    : (directRelightOk(in) ? segstate::PRIMED : segstate::UNPRIMED));
    const float w = stand_ ? kIgnWindowRelightStand_s : kIgnWindowRelightLong_s;   // v2.8.1: stand R2 0.35 s (R3 deleted)
    const float prep = directRelightOk(in) ? 0.0f : (kBleedSettle_s + kMvOpenRampSlow_s + kMvCockHold_s);
    out.relight_worst_ms = static_cast<uint16_t>(std::lround(1000.0f * (prep + kTorchGate_s + w)));
  }
  out.cmd_refused_event = cmd_refused_event_;
  // v2.8 final
  out.seg_vapour = seg_vap_now_;
  out.seg_vapour_event = seg_vap_event_;
  out.seg_vapour_clear = seg_vap_clear_;
  out.tank_T_K = tank_T_K_;
  out.tank_hot = tank_hot_;
  out.tank_xcheck = tank_xcheck_;
  out.tank_hot_relight = tank_hot_relight_;
  out.coast_pintle = static_cast<uint8_t>((coast_enc_lost_ ? 1u : 0u) | (coast_pint_open_ ? 2u : 0u));   // v2.8.2 RG-08
  out.coast_pintle_event = coast_anom_event_;
  healthy_ = std::isfinite(pc_f_) && std::isfinite(pintle_cmd_) && std::isfinite(gimbal_shaped_[0]) && std::isfinite(gimbal_shaped_[1]);
}

void EngineEcu::fillLog(const Inputs& in, const Outputs& o, LogRecord& r) {
  r.magic = 0xA7E5; r.version = 9; r.state = static_cast<uint8_t>(o.state);
  r.t_us = static_cast<uint32_t>(in.t_s * 1e6); r.rec_seq = rec_seq_++;
  r.fault_bits = o.fault_bits; r.abort_cause = static_cast<uint8_t>(o.abort_cause); r.starts_used = o.starts_used;
  r.pc_Pa = pc_f_ + pamb_Pa; r.pc_sp_Pa = o.pc_sp_active_Pa; r.pfeed_Pa = in.pfeed_Pa; r.ptank_Pa = in.ptank_Pa;
  r.pintle_cmd_m = o.pintle_cmd_m; r.pintle_meas_m = in.pintle_meas_m;
  r.ga_cmd_rad = o.gimbal_cmd_shaped_rad[0]; r.gb_cmd_rad = o.gimbal_cmd_shaped_rad[1];
  r.ga_meas_rad = in.gimbal_meas_rad[0]; r.gb_meas_rad = in.gimbal_meas_rad[1];
  r.thrust_est_N = o.thrust_est_N; r.load_cell_N = in.load_cell_N;
  for (int k = 0; k < 4; ++k) {
    r.pc_raw4[k] = 0;   // HAL fills the four 4 kSPS ADC codes of this millisecond
    r.servo_us[k] = static_cast<uint16_t>(o.servo_us[k]);
    r.tc_dK[k] = static_cast<int16_t>(std::lround((in.tc_K[k] - 273.15f) * 10.0f));
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
  r.crc16 = crc16_ccitt(reinterpret_cast<const uint8_t*>(&r), sizeof(LogRecord) - 2);
}

}  // namespace ecu
