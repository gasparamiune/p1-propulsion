// ARGOS engine ECU - top-level state machine, safety monitor, sequencing (v2.8.2: RG-08 coast pintle-anomaly latches -> prep path,
// TLM_RELIGHT UNKNOWN / UNPRIMED)
// SAFE -> ARMED -> PREPRESS -> IGNITION -> RUN -> SHUTDOWN -> (PURGE) -> COAST --RELIGHT--> IGNITION (v2.8 direct: NC valve opened at
// E0 with the torch, lift at E1) or, with a segment that may hold gas, --RELIGHT--> PREPRESS -> IGNITION (v2.7 slow priming) ...
// Any state --abort--> ABORT (shutdown actions) -> SAFE with the cause latched until DISARM/SAFE ack.
// v2.8 (LEAD 2026-10-13): ignition window W from the lift command (stand R1-R4, flight 0.65 s on relights); torch gate 0.16 s; ignition
// lift from a lift-vs-T_tank table; S1 relief monitor; provisional over-thrust abort (FC_THRUST); explicit mode strap (latched at ARM);
// case over-temperature armed with the MV open; PREPRESS refused in COAST. v2.8 final: normal-shutdown seat timeout 0.30 s; an abort
// makes the next attempt a vapour-segment start (NV b3); tank interlock 24 C (ARM, pad and stand ignitions); TLM_RELIGHT
// PRIMED/UNPRIMED/UNKNOWN valid after the MECO valve closure; RUN-entry Pc reference capped at the map setpoint.
// v2.7 (Combustion review fold-in, LEAD 2026-10-13): every abort de-energises the NC valve at once and commands the pintle closed
// in parallel; normal SHUTDOWN closes the pintle first and unlatches the valve on a confirmed seat or kMvSeatTimeout_s; torch
// valves close on the light-confirmation event (never N2O-only); torch-flame confirmation (P_torch) gates the pintle step
// (TORCH_FAULT); no automatic in-flight relight retry (relight lockout, non-volatile); C7 relight check extension; pintle-rail
// loss -> PINTLE_FAULT; Pc-sensor loss in RUN aborts on the test stand only.
// v2.6 (LEAD 2026-10-12): pintle stall/tracking monitor (lack of progress toward the command, time or current path) ->
// back-off (command closed, latched) + fault::PINTLE + PINTLE_FAULT abort (MV closes) + jam event (non-volatile via the HAL,
// ARM refused with MAINT_JAM until CLEAR_JAM); unlit pintle limited to the ignition lift; MV closed through the MECO coast,
// every MV opening ramped (relights run PREPRESS).
#pragma once
#include <cmath>
#include "config.h"
#include "control.h"
#include "filters.h"
#include "protocol.h"
#include "supply.h"
#include "types.h"

namespace ecu {

class EngineEcu {
 public:
  void init(double t_s);
  // Call exactly once per 1 ms tick. Pure function of inputs/commands/internal state (no I/O):
  // identical code runs on the Teensy (hal_teensy) and natively in the SIL.
  void step(const Inputs& in, const Commands& cmd, Outputs& out);
  void fillLog(const Inputs& in, const Outputs& out, LogRecord& r);

  State state() const { return st_; }
  Abort abortCause() const { return abort_; }
  bool abortLatched() const { return abort_latched_; }
  bool healthy() const { return healthy_; }       // HAL kicks the hardware watchdog only while true
  LinkPolicy link_policy = LinkPolicy::SHUTDOWN;
  float link_hold_s = eng::kLinkHoldLanding_s;     // used by HOLD_THEN_SHUTDOWN (GNC v1: 0.3 s in the landing burn)
  bool gimbal_fault_aborts = true;
  bool tank_overp_pad_only = cfg::kTankOverPAbortPadOnly;   // v2.3 LEAD conditional (passive relief device, Mechanical)
#ifdef ECU_SIL_TEST_HOOKS
  bool test_disable_fw_ovp = false;              // SIL only (absent from the flight build): proves the hardware trip alone
  bool test_force_fast_prime = false;            // SIL only: v2.1 sequence (no bleed, fast MV) for comparison
  bool test_disable_pintle_mon = false;          // SIL only (v2.6): pintle stall monitor off, so the hardware trip is shown alone
#endif
  bool tvc_test_enabled = false;
  bool tvc_test_raw = false;                     // v2.6: TVC_TEST_ENABLE arg 2 (B-TVC-1 FRF): shaping filters bypassed, SAFE only
  float pamb_Pa = eng::kPamb_Pa;                   // ambient for thrust<->Pc (FC may update)
  // v2.6: HV69 pulse calibration (B-PNT-1 sweep). Accepted in SAFE only and only if PintleCal::valid(); returns false otherwise.
  bool setPintleCal(const linkage::PintleCal& c);
  // v2.6 per-axis gimbal notch calibration (B-TVC-1 record): SAFE only, all-or-nothing; the HAL loads it at boot (NvGimbalCal)
  bool setGimbalNotchCal(const GimbalNotchCal& c);
  GimbalNotchCal gimbalNotchCal() const { GimbalNotchCal c; c.ax[0] = tvc_.notchAxis(0); c.ax[1] = tvc_.notchAxis(1); return c; }
  uint16_t ignitionRefusedNotch() const { return ign_refused_notch_; }
  const linkage::PintleCal& pintleCal() const { return pcal_; }
  float pc_zero_Pa() const { return pc_zero_; }
  float pcRef() const { return pc_ref_; }
  float pcAbsFiltered() const { return pc_f_ + pamb_Pa; }
  const PcController& pcc() const { return pcc_; }
  const SupplyMonitor& supply() const { return supply_; }
  bool tvcSupplyDegraded() const { return tvc_sup_deg_; }
  const TvcShaper& tvc() const { return tvc_; }
  float gimbalSatMax() const { return sat_.t_max; }
  uint8_t gimbalSatLong() const { return sat_.n_long; }
  uint16_t ignitionRefused() const { return ign_refused_; }
  bool startRampActive() const { return start_ramp_; }
  bool retryWaitActive() const { return t_now_ - t_unlit_ < cfg::kRetryVentWait_s; }
  // v2.6 pintle monitor / jam record
  const PintleJamEvent& lastJam() const { return jam_ev_; }
  uint16_t jamCount() const { return jam_count_; }
  float pintleNoProgress() const { return pint_noprog_s_; }
  uint16_t clearJamRefused() const { return clear_jam_refused_; }
  // v2.7
  bool relightLockout() const { return lockout_; }
  uint16_t clearLockoutRefused() const { return clear_lockout_refused_; }
  bool torchOk() const { return torch_ok_; }
  bool torchClosed() const { return torch_closed_; }
  float ignitionWindow() const { return ign_w_s_; }          // v2.8: W of the current/last start [s from the lift command]
  double liftCommandTime() const { return t_lift_; }         // v2.8: time of the ignition-lift command (E1); < 0 before it
  uint8_t ignRule() const { return ign_rule_; }              // v2.8: rule:: of the current/last start
  float ignLift() const { return ign_lift_m_; }              // v2.8: ignition lift of the current/last start (table)
  bool superheatProven() const { return superheat_e0_; }     // v2.8: superheat at both state TCs latched at E0 (v2.8.1: telemetry only)
  bool pcSensorOk() const { return pc_sensor_ok_; }          // v2.8.1: Pc channel valid (tests)
  int overThrustFrames() const { return overthr_n_; }        // v2.8.1: consecutive FC_THRUST frames above kOverThrust_N (tests, log)
  bool relightDirect() const { return relight_direct_; }     // v2.8: this start opened the NC valve at E0
  bool s1Fault() const { return s1_fault_; }
  bool s1ZeroOk() const { return s1_zero_ok_; }
  float s1Zero() const { return s1_zero_; }
  bool modeStand() const { return mode_stand_; }
  bool modeMismatch() const { return mode_mismatch_; }
  uint16_t ignRefusedR4() const { return ign_refused_r4_; }
  uint16_t ignRefusedHot() const { return ign_refused_hot_; }
  uint16_t prepressRefused() const { return prepress_refused_; }
  uint16_t ignRefusedBay() const { return ign_refused_bay_; }  // v2.8 bay temperature (pad first start)
  uint16_t ignRefusedTank() const { return ign_refused_tank_; }  // v2.8 final tank interlock (pad first start, stand starts)
  bool segVapour() const { return seg_vap_; }                // v2.8 final: abort since the last light (RAM copy of NV b3)
  float tankTemp() const { return tank_T_K_; }               // v2.8 final: interlock tank temperature [K] (NaN = no valid reading)
  bool tankHot() const { return tank_hot_; }
  bool tankXcheck() const { return tank_xcheck_; }
  bool tankHotRelight() const { return tank_hot_relight_; }
  bool mecoClosed() const { return meco_closed_; }            // v2.8 final: TLM_RELIGHT VALID basis (COAST)
  bool timingOnlyThisStart() const { return bypass_start_; }
  bool prailLost() const { return prail_lost_; }
  bool mvSeatTimeout() const { return mv_seat_timeout_; }
  bool litSinceBoot() const { return lit_since_boot_; }
  float ptorchZero() const { return ptorch_zero_; }         // v2.7: P_torch auto-zero (ARMED) [Pa]
  bool litSession() const { return lit_session_; }          // v2.7: lit since the last commanded DISARM/SAFE (NV b2 mirror)
  bool coastPintleAnomaly() const { return coast_enc_lost_ || coast_pint_open_; }   // v2.8.2 RG-08 (latched; same test for path and TLM)
  bool coastEncLost() const { return coast_enc_lost_; }     // v2.8.2 RG-08: pintle encoder invalid on a COAST tick (latched)
  bool coastPintleOpen() const { return coast_pint_open_; } // v2.8.2 RG-08: lift > kCoastPintleOpen_m for kCoastPintleOpenN COAST ticks (latched)

 private:
  void enter(State s, double t);
  void doAbort(Abort a, double t);
  void handleCommand(Cmd c, uint16_t arg, const Inputs& in, double t);
  bool armChecksOk(const Inputs& in, Abort* why) const;
  bool feedPrimed(const Inputs& in) const;
  bool segmentPrimed(const Inputs& in) const;                 // v2.8: no gas pocket in the valve-to-seat segment (direct relight)
  uint8_t startBlock(const Inputs& in, double t) const;       // v2.8: refuse:: reason an IGNITE/RELIGHT received now would get
  bool directRelightOk(const Inputs& in) const {              // v2.8: direct path = segment primed AND the valve shown closed by both
    return cfg::kRelightDirect && segmentPrimed(in) && in.mv_closed_sw && !in.mv_open_sw &&   //   switches (else PREPRESS, which
           !segVapourPending(in) && !coastPintleAnomaly();    //   checks the valve itself; a stuck OPEN switch must not pass the E0 check)
  }                                                           //   v2.8 final: never after an abort until a light (COMB v2.4 vapour segment)
                                                              //   v2.8.2 RG-08: never after a coast pintle anomaly until a light
  void coastPintleStep(const Inputs& in);                     // v2.8.2 RG-08: anomaly latches (COAST ticks, before the commands)
  bool segVapourPending(const Inputs& in) const { return seg_vap_ || in.nv_seg_vapour; }   // v2.8 final (RAM or NV b3)
  void tankUpdate(const Inputs& in, float ptank_abs);         // v2.8 final tank interlock estimate (every tick)
  bool chamberVented() const { return std::fabs(pc_f_) < cfg::kPcVentedMax_Pa; }   // v2.5 COMB OI-12
  void monitors(const Inputs& in, double t);
  void pintleMonitor(const Inputs& in, double t, bool* aborted);   // v2.6
  void pintleMonReset() { pint_active_ = false; t_pint_i_ = -1.0; pint_noprog_s_ = 0.0f; }
  void pintleJam(uint8_t kind, const Inputs& in, double t);       // v2.6: record one jam event (first kind latched)
  bool maintJamPending(const Inputs& in) const { return in.maint_pintle_jam || jam_since_clear_; }
  bool lockoutPending(const Inputs& in) const { return lockout_ || in.nv_relight_lockout; }   // v2.7
  void setLockout();                                                                            // v2.7
  void torchStep(const Inputs& in, double t, double ti, bool* ign_en, bool* spark, bool* n2o, bool* prop);   // v2.7
  bool mvOpener(double tr);                                   // v2.8: opener ramp/hold profile (t from the ramp start); false = done
  void s1Step(const Inputs& in, double t);                    // v2.8: S1 zero capture and monitor
  bool modeStrapStand(const Inputs& in) const { return in.mode_strap == strap::STAND; }
  bool modeConsistent(const Inputs& in) const {               // v2.8: strap valid and agreeing with the load-cell check
    const bool lc = std::isfinite(in.load_cell_N);
    return (in.mode_strap == strap::STAND && lc) || (in.mode_strap == strap::FLIGHT && !lc);
  }
  bool caseHot(const Inputs& in) const {                      // v2.8: either case TC (valid) above the relight refusal limit
    return (in.tc_valid[0] && in.tc_K[0] > cfg::kCaseRelightMax_K) || (in.tc_valid[1] && in.tc_K[1] > cfg::kCaseRelightMax_K);
  }
  bool bayHot(const Inputs& in) const { return !in.bay_valid || !(in.bay_K <= cfg::kBayArmMax_K); }   // v2.8 launch constraint
  float ignLiftFor(bool ttank_ok, float ttank_K) const;       // v2.8: lift-vs-T_tank table
  void refuseCmd(uint8_t why) { cmd_refused_ = why; cmd_refused_event_ = true; }

  State st_ = State::SAFE;
  Abort abort_ = Abort::NONE;
  bool abort_latched_ = false;
  bool healthy_ = true;
  double t_state_ = 0, t_now_ = 0, last_fast_t_ = -1e9;
  bool auto_ignite_ = false, lit_ = false, prop_closed_ = false;
  int ign_ok_n_ = 0;               // v2.6 OI-6: consecutive ticks with filtered AND raw Pc above the ignition threshold
  uint16_t ign_refused_notch_ = 0; // v2.6 IGNITE/RELIGHT refused: gimbal notch not set on both axes (LEAD: notch REQUIRED)
  bool gcal_changed_ = false;      // v2.6 one-tick: notch calibration changed (HAL stores it)
  bool start_ramp_ = false;       // v2.5 COMB start ramp active (RUN entry until the FC command is first reached)
  RateLimiter thr_rl_;            // v2.5 start-ramp thrust limiter [N]
  uint16_t ign_refused_ = 0;      // v2.5 IGNITE/RELIGHT ignored: chamber not vented (OI-12) or inside the retry vent wait
  double t_unlit_ = -1e9;         // v2.5 time of the last NO_IGNITION/FLAMEOUT abort (COMB v2.2 retry vent wait)
  double t_lit_ = 0, t_arm_req_ = -1e9, t_ign_ = -1e9, t_coast_ = 0;
  uint8_t starts_ = 0;
  uint16_t faults_ = 0;
  // commands latched from FC
  float thrust_cmd_ = 0, gimbal_cmd_[2] = {0, 0};
  bool vent_cmd_ = false, ceiling_active_ = false;
  uint8_t roll_bits_ = 0; double last_aux_t_ = -1e9, roll_on_since_ = -1e9;
  // Pc processing (gauge internally; absolute = gauge + pamb)
  float pc_zero_ = 0, pc_zero_acc_ = 0; int pc_zero_n_ = 0;
  float pc_f_ = 0, pc_ref_ = 0;
  LowPass2 pc_lpf_;               // v2.2: 2nd-order 50 Hz (sense-line resonance)
  LowPass1 pc_ref_lpf_, pfeed_lpf_, ptank_lpf_;
  bool pc_sensor_ok_ = true;
  // actuators
  PcController pcc_;
  TvcShaper tvc_;
  RateLimiter pintle_rl_;
  float pintle_cmd_ = 0;
  linkage::PintleCal pcal_;       // v2.6 HV69 pulse calibration (defaults = config.h until the B-PNT-1 sweep)
  // v2.6 pintle stall/tracking monitor (episode = |cmd - lift| > kPintleStallErr_m; progress mark = lift moved >= 20 um
  // toward the command since the last mark; same definition as calc/pintle_dynamics_v2.py noprog_max)
  bool pint_active_ = false;
  float pint_ref_m_ = 0, pint_noprog_s_ = 0;
  double t_pint_ref_ = 0, t_pint_err_ = 0, t_pint_i_ = -1.0;
  bool pint_backoff_ = false;     // command forced closed after a jam (latched until DISARM in SAFE)
  uint8_t pint_kind_ = 0;         // jam:: kind of the first jam since the last DISARM in SAFE
  bool safe_chk_ = false;         // SAFE entry from a powered state: unpowered spring closing checked after kPintleUnpoweredClose_s
  PintleJamEvent jam_ev_;
  bool jam_event_ = false, jam_since_clear_ = false, maint_clear_ = false;   // one-tick pulses / latched maintenance flag
  uint16_t jam_count_ = 0, clear_jam_refused_ = 0;
  bool mv_ramp_ = false;          // v2.6: this PREPRESS opens the MV with the >= 0.3 s ramp (always, kMvRampEveryOpening)
  float gimbal_shaped_[2] = {0, 0}, gimbal_model_[2] = {0, 0};
  float servo_us_[4] = {1500, 1500, 1500, 1500};
  bool mv_latch_ = false, mv_cocking_ = false;
  bool prime_slow_ = false, bleed_active_ = false, bleed_checked_ = false;   // v2.2 line-priming rule (COMB v2)
  double t_mv_cmd_ = 0;
  // persistence timers
  Persist p_hard_, p_flame_, p_band_, p_gimb_[2], p_otemp_, p_tankp_, p_batt_, p_armlost_, p_servo_hot_, p_hwovp_;
  // v2.3 FM-PWR-01 supply monitor, e-fuse, heater permit (persistence timers are not reset on state changes)
  SupplyMonitor supply_;
  Persist p_sup_set_, p_sup_clr_, p_efuse_;
  bool tvc_sup_deg_ = false, heater_permit_ = false;
  // v2.4 ENG-07b gimbal saturation episodes (statistics reset at each IGNITION entry)
  EpisodeTimer sat_;          // v2.4 ENG-07b actuator-saturation episodes (proxy), statistics per burn / bench run
  uint8_t sat_flags_ = 0;
  bool arm_drop_ = false;         // ABORT: ARM bus released on purpose (pintle not closing progress, Pc still high, hardware trip)
  float thrust_est_ = 0;
  uint16_t rec_seq_ = 0;
  // v2.7 Combustion review fold-in
  bool stand_ = false;            // v2.8: stand mode in force (latched at ARM from the strap; in SAFE: strap AND finite load cell)
  bool torch_ok_ = false;         // torch flame confirmed (P_torch) in this start
  int torch_ok_n_ = 0;
  bool torch_closed_ = false;     // torch valves closed by the event / backstop (this start)
  double t_torch_close_ = 0;
  bool bypass_armed_ = false;     // SET_TORCH_GATE key accepted in SAFE on a stand (cleared by DISARM in SAFE / init)
  bool bypass_start_ = false;     // this start runs timing-only (first start of the arming session, stand, key)
  // v2.8 ignition window / relight path / lift table
  float ign_w_s_ = 0.0f;          // W of this start [s from the lift command]
  uint8_t ign_rule_ = 0;          // rule:: of this start
  double t_lift_ = -1.0;          // ignition-lift command time of this start (E1); < 0 before
  float ign_lift_m_ = 0.0f;       // ignition lift of this start (table, before the trim)
  bool superheat_now_ = false, superheat_e0_ = false;   // R3 condition this tick / latched at E0
  bool r4_ok_now_ = true;         // MSS-1, MSS-2 and P_feed valid this tick
  bool pfeed_ok_ = true, ptank_ok_ = true;              // validity flags of this tick (used in enter())
  bool ttank_ok_ = false; float ttank_K_ = 293.15f;     // Tsat(P_tank) this tick
  bool relight_direct_ = false, mv_open_seen_ = false;  // NC valve opened at E0 in this start; OPEN switch seen since
  bool mode_stand_ = false, mode_mismatch_ = false, mode_mismatch_prev_ = false;
  uint16_t ign_refused_r4_ = 0, ign_refused_hot_ = 0, prepress_refused_ = 0, ign_refused_bay_ = 0;
  uint8_t cmd_refused_ = 0; bool cmd_refused_event_ = false;
  // v2.8 S1 monitor
  bool s1_zero_ok_ = false, s1_fault_ = false, s1_event_ = false;
  float s1_zero_ = 0.0f, s1_acc_ = 0.0f, s1_dp_ = 0.0f; int s1_n_ = 0; double t_mv_open_sw_ = -1.0;
  bool s1_coast_zero_done_ = false;
  Persist p_s1_;
  // v2.8 over-thrust (FC estimate)
  float fc_thr_N_ = 0.0f; bool fc_thr_ok_ = false; double t_fc_thr_ = -1e9;
  int overthr_n_ = 0;            // v2.8.1: consecutive fresh valid FC_THRUST frames above kOverThrust_N in flight RUN
  bool lockout_ = false, lockout_event_ = false, lockout_clear_ = false, lit_since_boot_ = false;
  bool lit_session_ = false, lit_session_event_ = false, lit_session_close_ = false;   // v2.7 NV lit-session marker (b2)
  float ptorch_zero_ = 0.0f, ptorch_zero_acc_ = 0.0f; int ptorch_zero_n_ = 0; bool torch_low_seen_ = false;   // v2.7 P_torch zero / edge
  uint16_t clear_lockout_refused_ = 0;
  bool mv_seat_wait_ = false, mv_seat_timeout_ = false; int seat_n_ = 0;
  bool prail_lost_ = false; double t_bus_on_ = -1.0;
  Persist p_prail_, p_pcsens_;
  // v2.8 final (LEAD 2026-10-13: COMB v2.4, GNC v3)
  bool seg_vap_ = false, seg_vap_event_ = false, seg_vap_clear_ = false;   // abort -> vapour segment (NV b3); one-tick set / clear
  bool seg_vap_e0_ = false;       // the flag at E0 of the current start (stand: R2/R3 logic on a first start)
  bool seg_vap_now_ = false;      // segVapourPending() this tick (RAM or NV b3), used in enter()
  bool meco_closed_ = false;      // COAST: CLOSED switch seen with OPEN clear and the latch off since COAST entry (or closure overdue)
  float tank_T_K_ = 293.15f;      // interlock tank temperature (max of the valid indications); NaN = none valid
  bool tank_hot_ = true, tank_xcheck_ = false, tank_hot_relight_ = false;
  uint16_t ign_refused_tank_ = 0;
  // v2.8.2 (GNC REV-GNC-1 RG-08): coast pintle-position anomaly latches (cleared at RUN entry and by DISARM in SAFE)
  bool coast_enc_lost_ = false, coast_pint_open_ = false;
  int coast_open_n_ = 0;          // consecutive COAST ticks with the encoder lift above kCoastPintleOpen_m
  uint8_t coast_anom_event_ = 0;  // one tick: 1 = encoder-lost latch set, 2 = pintle-open latch set (EVENT COAST_PINTLE)
};

}  // namespace ecu
