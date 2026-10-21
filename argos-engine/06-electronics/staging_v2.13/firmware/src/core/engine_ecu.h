// [v2.13 2026-10-21, REV-ELEC-4 E4-01 / E4-03 / E4-N02: seat_arm_rule build selection, light-window hold / TC4 step / rate state (seat_Tc_K_ ...), pcSeatHold / pcSeatStep / pcSeatTcompK / pcSeatHoldGapMaxK; full list in the ELEC-V213 handback]
// [v2.11 2026-10-20, LEAD CHANGELOG 216: baseLowNow() (pad / stand BASE_AMB lift refusal), R2 backstop / hold-lift state, prepressExits(); full list in the ELEC-V211 handback]
// [v2.11 2026-10-13, LEAD CHANGELOG 203/205: ride_through option, over-range / ride-through state, unpurgedGuard(); full list in the ELEC-V211 handback]
// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175/181/186: state machine and monitors for the v2.10 rules; R2 command hold state (186 (2)); full list in 06-electronics/REPORT-v2.10-HANDBACK.md] ARGOS engine ECU - top-level state machine, safety monitor, sequencing (v2.9: LEAD-adopted relative light detection (pre-lift baseline,
// +0.8 bar, 10 ms, floor 1.8 bar abs); A3 relative flame-out on the lift map; A5 ignition-hold over-pressure; A7 map criterion with the
// lit-start band E1->E3; CF-3 ignition-lift table (37.4 g/s); head-end bleed provision - pad BIT in PREPRESS, PURGE = relight forced
// purge (COAST -> PURGE -> IGNITION), V1 closure confirmed before the lift, leak monitor, BLEED_FAULT; coast Pc/P_torch re-zero. v2.8.2: RG-08 coast pintle-anomaly latches -> prep path, TLM_RELIGHT UNKNOWN / UNPRIMED)
// SAFE -> ARMED -> PREPRESS -> IGNITION -> RUN -> SHUTDOWN -> COAST --RELIGHT--> IGNITION (v2.8 direct: NC valve opened at
// E0 with the torch, lift at E1); v2.9 with the head-end bleed fitted: COAST --PURGE or RELIGHT--> PURGE --(t_purge)--> IGNITION;
// with a segment that may hold gas, --RELIGHT--> PREPRESS -> IGNITION (v2.7 slow priming) ...
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
  float sil_seat_ts = 1.0f;                      // SIL only (v2.13, disclosed S13T variant): d(Mechanical time)/d(SIL time) of the seat
                                                 //   history map (S13T compressed burn: stand 25x, A1 4.1x; 1 = off): scales the TC4 slew /
                                                 //   catch-up bound so T_c can follow a time-compressed seat, and the post-E2 hold
                                                 //   (kPcSeatHoldPostE2_s / the value at E2: 0.45 s on the Mechanical axis); no other use
                                                 //   (the SIL also runs the seat TC lag on the Mechanical axis in that variant)
  float sil_ts_e2_ = 1.0f;                       // SIL only (v2.13): sil_seat_ts latched at the RUN entry (E2)
  bool test_disable_fw_ovp = false;              // SIL only (absent from the flight build): proves the hardware trip alone
  bool test_force_fast_prime = false;            // SIL only: v2.1 sequence (no bleed, fast MV) for comparison
  bool test_disable_pintle_mon = false;          // SIL only (v2.6): pintle stall monitor off, so the hardware trip is shown alone
  bool test_inhibit_purge_close = false;         // SIL / unit test only (v2.10): the purge schedule never closes V1 -> proves the cap
  bool test_disable_hb_cap = false;              // SIL only (v2.11): firmware both-open cap off -> the hardware timer is shown alone
#endif
  // v2.9 build selections (the HAL leaves the cfg:: values; the SIL and the unit tests set them per case)
  bool ign_detect_relative = cfg::kIgnDetectRelative;   // relative light detection; false = legacy absolute 3.0 bar abs rule (comparison)
  bool hbleed_fitted = cfg::kHbleedFitted;               // head-end bleed provision fitted (A1 build)
  bool ptank_cal_ok = cfg::kPtankCalibratedDefault;      // v2.10 guard band: P_tank channel calibrated (B-PT-1 record valid) ->
                                                         //   threshold kTankIgnMaxPCal_Pa, else kTankIgnMaxP_Pa (config.h)
  bool pc_coast_rezero = cfg::kPcCoastRezero;            // coast re-zero of Pc and P_torch
  bool ride_through = cfg::kRideThroughBuild;            // v2.11 FA-1 ride-through CANDIDATE (LEAD 203 (1)(b); default OFF, flight relight only)
  bool seat_arm_rule = cfg::kSeatArmRuleBuild;           // v2.13 LEAD 264 (2) A1 pad rule (A1 flight build TRUE; stand builds / legacy SIL FALSE)
  bool jfwd_relight_inhibit = cfg::kJfwdLsRelightInhibit;        // v2.13 LEAD 264 (7) PROVISIONAL flight relight inhibit after f3::JFWD_LS
  bool seat_step_relight_inhibit = cfg::kSeatStepRelightInhibit; // v2.13 A5 (lead decision): flight relight refused while f3::SEAT_STEP
  bool tvc_test_enabled = false;
  // v2.12 (REV-ELEC-3 R3-01 option (b), LEAD 2026-10-21T11:25Z working basis): C1 seat-temperature compensation of the Pc reading.
  // coef = the per-serial B-PC-1 thermal-zero coefficient [Pa/K] (calibration: SAFE only, finite, |coef| <= cfg::kPcSeatCoefMax_PaPerK);
  // 0 = compensation OFF (the v2.11 behaviour; f3::SEAT_COMP clear). Returns false (unchanged) otherwise. The HAL loads it at boot.
  bool setPcSeatCoef(float coef_Pa_per_K);
  float pcSeatCoef() const { return seat_coef_; }
  // v2.12: the B-PC-1 zero temperature T_cal [K] for the ARM sanity static term (SAFE only, cfg::kPcSeatTcalMin_K..Max_K; false = unchanged)
  bool setPcSeatTcal(float tcal_K);
  float pcSeatTcal() const { return seat_tcal_K_; }
  float pcSeatComp() const { return seat_comp_; }              // compensation subtracted this tick [Pa]
  bool pcSeatCompActive() const { return seat_ref_ok_ && seat_coef_ != 0.0f; }
  float pcSeatRefK() const { return seat_ref_K_; }
  // v2.13 (REV-ELEC-4 E4-01): light-window hold and TC4 step / rate checks (config.h)
  bool pcSeatHold() const { return seat_hold_; }               // this tick: compensation temperature frozen (IGNITION entry .. E2 + 0.45 s)
  bool pcSeatStep() const { return seat_step_; }               // latched until the next ARM: TC4 step / rate trip (f3::SEAT_STEP)
  float pcSeatTcompK() const { return seat_Tc_K_; }            // compensation temperature T_c [K] (comp = coef x (T_c - T_seat,ARM))
  float pcSeatHoldGapMaxK() const { return seat_gap_max_K_; }  // largest |reading - T_c| seen at a hold end in this arming [K] (SIL record)
  bool pcSeatCatch() const { return seat_catch_; }             // v2.13 ITEM 2: catch-up after the hold active this tick
  uint8_t buildBits() const;                                   // v2.13 EVENT BUILD arg (evt::BUILD_*)
  bool tbState() const { return tb_state_; }                   // f3::TB_STATE (bench plan v5 F-14)
  uint8_t f3Flags() const;
  // v2.12 (LEAD CHANGELOG 256 (2), 257 (2), 258 (2)): purge FLOW time and both-open cap are CALIBRATION constants: defaults and maxima
  // cfg::kPurgeFlow_s 2.43 s / cfg::kHbleedCap_s 2.39 s; re-set after CF-4 / B-BLEED-1 by rule (d) (config.h). SAFE only, all-or-nothing:
  // cfg::kPurgeFlowCalMin_s <= flow <= cfg::kPurgeFlow_s, cap <= cfg::kHbleedCap_s, flow + t_o - t_c + 2 ticks < cap. false = unchanged.
  bool setPurgeCal(float flow_s, float cap_s);
  float purgeFlow_s() const { return purge_flow_s_; }
  float hbleedCap_s() const { return hb_cap_s_; }
  float purgeFlowStart_s() const { return cfg::kPurgeRelight_s - cfg::kPurgeFlowEndLead_s - purge_flow_s_; }   // after PURGE
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
  bool drogueAttached() const { return drogue_attached_; }   // v2.10 LEAD 186 (2)
  bool r2Hold() const { return r2_hold_; }                   // v2.10 LEAD 186 (2)
  bool r2Backstop() const { return r2_backstop_; }           // v2.11 LEAD 216 (2)(b): backstop fired in this start
  // v2.10 (LEAD 172 (1)) ground no-light safing hold (replaces the v2.5 retryWaitActive / 5 s wait)
  bool safingHoldOpen() const { return sh_open_; }
  double safingHoldLeft_s() const { return sh_open_ ? std::fmax(0.0, cfg::kNoLightSafingMin_s - (t_now_ - t_sh_)) : 0.0; }
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
  float ignLiftTable(bool ttank_ok, float T_K) const { return ignLiftFor(ttank_ok, T_K); }   // v2.9: CF-3 table lookup (tests, HAL)
  bool ttankSatOk() const { return ttank_ok_; }              // v2.9: Tsat(P_tank) valid this tick
  float ttankSatK() const { return ttank_K_; }               // v2.9: Tsat(P_tank) this tick [K]
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
  bool tankCold() const { return tank_cold_; }
  bool tankColdRelight() const { return tank_cold_relight_; }
  float tankTminK() const { return tank_tmin_K_; }            // v2.11: coldest valid tank estimate [K] (NaN: none)
  int prepressExits() const { return prepress_exit_n_; }      // v2.11 LEAD 216 (7): PREPRESS ended by an IGNITE refusal
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
  // v2.9
  float ignRef() const { return ign_ref_f_; }                // P0 pre-lift baseline of the current/last start (filtered gauge)
  uint8_t ignDet() const { return ign_det_; }                // det:: flags of the current/last start
  double tLit() const { return t_lit_; }                     // E2 (light confirmed) of the last lit start
  double tE3() const { return t_e3_; }                       // E3 of the current/last burn (-1 before)
  float flameRatio() const { return flame_ratio_; }          // A3 ratio this tick (NaN outside RUN)
  float pcMapLag() const { return pc_map_f_; }               // lagged lit-map Pc at the lift (absolute)
  float pcMapLo() const { return pc_map_lo_; }               // A3 reference: min(lagged, instantaneous) lit-map Pc (absolute)
  bool a7Flag() const { return a7_flag_; }                   // A7 map criterion tripped in flight RUN (this burn)
  const LightSpikeRec& lightSpike() const { return ls_; }    // v2.10 LIGHT_SPIKE record of the current/last start
  bool purgeStart() const { return purge_start_; }           // this start came from PURGE (head-end bleed)
  bool hbleedCmd(int k) const { return hb_cmd_[k]; }
  uint8_t hbleedBit() const { return hb_bit_; }
  bool hbleedV1Closed() const { return hb_v1_closed_; }
  bool hbleedPath() const { return hb_path_; }
  bool hbleedLeak() const { return hb_leak_; }
  float pcZeroArm() const { return pc_zero_arm_; }           // the ARM auto-zero (before any coast re-zero)
  bool rezeroApplied() const { return rz_applied_; }
  float rezeroShift() const { return rz_shift_; }
  bool rezeroRejected() const { return rz_rejected_; }
  // v2.11 (LEAD CHANGELOG 203 (1), (7))
  bool pcOverrange() const { return pc_overrange_; }         // HIGH over-range this tick (non-sticky)
  bool pcAboveFs() const { return pc_above_fs_; }            // above the transducer full scale this tick (flag)
  bool rideWindow() const { return ride_win_; }              // ride-through window open this tick (implies ride_through)
  int rideTolTicks() const { return ride_tol_n_; }           // ticks of this start with a 30 bar episode past the as-built persistence
  int rideOvrTolTicks() const { return ride_ovr_tol_n_; }    // v2.11: IGNITION HIGH over-range ticks of this start tolerated (N >= 2)
  bool unpurgedGuard() const { return cfg::kUnpurgedRelightGuard && hbleed_fitted && !stand_; }   // flight, bleed fitted

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
    if (!in.tc_valid[0] && !in.tc_valid[1]) return true;      // v2.10 RE-08 (LEAD): both case TCs invalid = hot (relight refused)
    return (in.tc_valid[0] && in.tc_K[0] > cfg::kCaseRelightMax_K) || (in.tc_valid[1] && in.tc_K[1] > cfg::kCaseRelightMax_K);
  }
  bool bayHot(const Inputs& in) const { return !in.bay_valid || !(in.bay_K <= cfg::kBayArmMax_K); }   // v2.8 launch constraint
  float ignLiftFor(bool ttank_ok, float ttank_K) const;       // v2.8: lift-vs-T_tank table
  void refuseCmd(uint8_t why) { cmd_refused_ = why; cmd_refused_event_ = true; }
  // v2.9 light detection (LEAD-adopted relative rule): returns the confirmed-light decision of this tick (IGNITION only)
  bool ignDetect(const Inputs& in, double t);
  void ignDetReset();
  // v2.9 A3 / A7 / E3: Pc_map at the lift (lagged), relative flame-out, map criterion
  void startMonitors(const Inputs& in, double t, bool* aborted);
  // v2.9 head-end bleed
  void enterPurge(double t, bool auto_ign);                   // COAST -> PURGE (MV latch + opener ramp, both bleeds open)
  void hbClose(double t);                                     // start the V1-first closure step (V2 held open until confirmed)
  void hbleedStep(const Inputs& in, double t, bool* aborted); // closure step, leak monitor (every tick, from monitors())
  bool hbleedBitStep(const Inputs& in, double t, bool* failed);   // pad BIT in PREPRESS; true while running
  // v2.10 (LEAD RE-05): a start from PURGE lifts once the closure step has ENDED (confirmed or not; the deadline in IGNITION forces
  // the end), and never while a bleed valve is commanded open (sequence check)
  bool hbLiftClear() const { return !hb_cmd_[0] && !hb_cmd_[1] && (!purge_start_ || hb_close_done_); }
  void hbCloseResult(double t, bool forced, bool* aborted);   // v2.10 closure step result (CONFIRMED / NOT CONFIRMED)
  void hbFlowEnd(double t);                                   // v2.10 flow accounting at the V1 close command
  double purgeE0Est(double t) const;                          // v2.10 scheduled E0 of the running purge (ECU time)
  bool baseHighNow() const;                                   // v2.10 RE-02 P0 above +check (ring mean, as the next tick's P0)
  bool baseLowNow() const;                                    // v2.11 LEAD 216 (4) the BASE_AMB case (P0 below -check, none, not finite)
  bool photoValid(const Inputs& in) const;                    // v2.10 FA-1 photodiode in range
  bool photoLit(const Inputs& in) const;                      // v2.10 FA-1 photodiode reads flame (valid, rise over dark)
  void hbEvent(uint8_t ev) { if (hb_event_ == hb::EV_NONE) hb_event_ = ev; }
  // v2.9 coast re-zero
  void rezeroStep(const Inputs& in, double t);
  void stepCore(const Inputs& in, const Commands& cmd, Outputs& out);   // v2.12: step() on the seat-compensated input copy
  void seatCompStep(const Inputs& in);   // v2.12 R3-01 option (b)
  void seatLatch();                      // v2.12: seat reference at the end of the ARM auto-zero window
  void tbMark(bool pc_high);             // v2.12: TB-state latch (LC-TB70 v2 F4 abort set)
  void rezero2Apply(double t);          // v2.10 RE-07 second re-zero at the PURGE / RELIGHT command
  bool ventGate();                      // v2.10 RE-07 vented wait: stand / pad first start wait; flight flags NOT_VENTED and proceeds
  void riseTrack(const Inputs& in, double t);   // v2.9 drogue-release support terms (tlmf::)
  void lightSpikeTrack(const Inputs& in, double t);   // v2.10 LIGHT_SPIKE record (A5 deleted)

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
  bool drogue_attached_ = false;  // v2.10 LEAD 186 (2): FC drogue state (Cmd::DROGUE); reset at power-up and at an accepted ARM
  bool r2_hold_ = false;          // v2.10 LEAD 186 (2): R2 command hold active this tick (RUN, flight, attached, Pc invalid)
  bool r2_backstop_ = false, r2_backstop_event_ = false;   // v2.11 LEAD 216 (2)(b): hold ended by the E2 + kR2HoldBackstop_s backstop
  int r2_hold_ticks_ = 0;         // v2.11: hold ticks in this start (telemetry / log)
  bool hold_ramp_ = false;        // v2.10: after a hold the command returns at <= kStartRamp_Nps (like the start ramp)
  uint16_t ign_refused_ = 0;      // v2.5 IGNITE/RELIGHT ignored (v2.8+: with a refuse:: reason)
  bool sh_open_ = false, sh_event_ = false, sh_boot_seen_ = false;   // v2.10 ground no-light safing hold (LEAD 172 (1))
  double t_sh_ = -1e9;            // v2.10 hold start (the no-light abort, or the boot with NV b4)
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
  bool pc_overrange_ = false, pc_above_fs_ = false;   // v2.11 (LEAD 203 (1)(a)): this tick
  // v2.11 FA-1 ride-through CANDIDATE (LEAD 203 (1)(b)): window, tolerated ticks, T45 guard
  bool ride_win_ = false, ride_tol_ = false, ride_t45_ = false;
  int ride_tol_n_ = 0;
  int prepress_exit_n_ = 0;    // v2.11 LEAD 216 (7): PREPRESS -> ARMED exits on an IGNITE refusal (this arming session)
  int ign_ovr_n_ = 0;          // v2.11 LEAD 216 (3): consecutive HIGH over-range ticks in IGNITION (rule N = kRideOverrangeN in the window)
  bool ride_ovr_tol_ = false;  // v2.11: this tick's HIGH over-range was tolerated by the window (count < N; ovr::RIDE_TOL)
  int ride_ovr_tol_n_ = 0;     // v2.11: tolerated over-range ticks of this start
  Persist p_t45_;
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
  Persist p_mvconf_;                 // v2.10 RE-19 ladder OPEN+CLOSED persistence
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
  bool tank_cold_ = true, tank_cold_relight_ = false;   // v2.10 RE-17
  float tank_tmin_K_ = 0.0f;   // v2.11 LEAD 216 (7): coldest valid tank estimate (NaN: none) for the ARM margin
  uint16_t ign_refused_tank_ = 0;
  // v2.8.2 (GNC REV-GNC-1 RG-08): coast pintle-position anomaly latches (cleared at RUN entry and by DISARM in SAFE)
  bool coast_enc_lost_ = false, coast_pint_open_ = false;
  int coast_open_n_ = 0;          // consecutive COAST ticks with the encoder lift above kCoastPintleOpen_m
  uint8_t coast_anom_event_ = 0;  // one tick: 1 = encoder-lost latch set, 2 = pintle-open latch set (EVENT COAST_PINTLE)
  // v2.9 light detection (per start; reset at IGNITION entry)
  float ign_pre_f_[cfg::kIgnPreN] = {}, ign_pre_r_[cfg::kIgnPreN] = {};   // ring of the last kIgnPreN filtered / raw gauge Pc up to E1
  int ign_pre_i_ = 0, ign_pre_n_ = 0;
  float ign_ref_f_ = 0.0f, ign_ref_r_ = 0.0f;                 // P0 (NaN before E1)
  float ign_rise_f_ = 0.0f;                                   // filtered rise over P0 this tick (NaN before E1)
  uint8_t ign_det_ = 0;
  bool rise_now_ = false, rise_held_ = false, rise_held_t_ = false, rise_seen_lit_ = false;   // tlmf:: terms of this start
  bool rise_f_now_ = false;        // v2.10 (LEAD CHANGELOG 156): filtered-only rise term, drives RISE_HELD / RISE_HELD_T (b6, b7)
  // v2.9 A3 / A7 / E3 (v2.10: A5 deleted)
  LowPass1 pc_map_lpf_;
  float pc_map_f_ = 0.0f, pc_map_lo_ = 0.0f, flame_ratio_ = 0.0f;
  float pc_map_now_ = 0.0f;        // v2.10: instantaneous lit-map Pc at the (encoder) lift, absolute (LIGHT_SPIKE 8 bar mask)
  double t_e3_ = -1.0;
  bool a7_flag_ = false, a7_event_ = false;
  uint8_t a7_phase_ = 0;
  Persist p_a7_;
  // v2.10 LIGHT_SPIKE record (A5 deleted; config.h kLightSpike*, types.h LightSpikeRec)
  LightSpikeRec ls_;
  bool ls_event_ = false;          // ONE tick: the record of this start closed (EVENT LIGHT_SPIKE)
  double ls_t_pk_raw_ = -1.0, ls_t_pk_filt_ = -1.0;   // ECU time of the raw / filtered peak of the open record
  // v2.9 head-end bleed
  bool hb_cmd_[2] = {false, false};
  bool hb_path_ = false, hb_path_checked_ = false;   // this purge: P_mid read high with V1 open / the path check is done
  bool hb_closing_ = false; double t_hb_close_ = 0.0; int hb_conf_n_ = 0;   // V1-first closure step in progress
  bool hb_v1_closed_ = false;      // this start (purge): V1 confirmed closed
  bool hb_mid_vented_ = false;     // the mid was last seen vented with V1 closed (leak monitor armed)
  bool hb_leak_ = false, hb_path_flag_ = false, hb_hold_to_ = false, hb_purge_enc_ = false;   // latched flags (DISARM in SAFE)
  bool hb_bit_pass_ = false;       // pad BIT passed in this arming session
  uint8_t hb_bit_ = 0, hb_event_ = 0;
  double t_hb_bit_ = -1.0; int hb_bit_match_n_ = 0, hb_bit_step_ = -1;
  Persist p_hb_leak_;
  bool purge_start_ = false;       // this start came from PURGE
  bool purge_ign_ = false;         // PURGE: a RELIGHT was received during the purge (v2.10 LEAD 175: the integrated mode is deleted)
  int purge_open_n_ = 0;           // PURGE: consecutive ticks with the needle off the seat
  bool purge_filled_ = false;      // PURGE: the segment has shown primed (P_feed check) in this purge
  // v2.10 purge schedule on FLOW time and closure confirmation (config.h 'head-end bleed' block)
  double t_hb_ready_ = -1.0, t_hb_v2open_ = -1.0, t_hb_flow0_ = -1.0, t_hb_v1c_ = -1.0, t_hb_v2c_ = -1.0, t_hb_both_ = -1.0;
  int hb_path_n_ = 0, hb_hold_n_ = 0;
  bool hb_vent_ok_ = false, hb_hold_ok_ = false, hb_close_done_ = false, hb_bleed_fault_ = false, hb_flow_event_ = false;
  float hb_flow_s_ = -1.0f;        // achieved flow time of the last purge [s] (< 0: none)
  uint8_t hb2_ = 0;                // hb2:: flags
  State st_out_prev_ = State::SAFE; uint32_t t_state_ms_ = 0;   // v2.10 state-change event (Outputs::state_event)
  uint8_t f2_ = 0, f2_prev_ = 0;   // v2.10 latched f2:: flags (DISARM in SAFE clears) and the value at the previous output
  bool lift_clamp_now_ = false;    // v2.10 RE-04 lift clamp active this tick
  // v2.10 FA-1 flame sensing
  float photo_dark_ = 0.0f; bool photo_dark_init_ = false, photo_dark_seen_ = false;
  int both_ok_n_ = 0;              // consecutive ticks with P_torch AND photodiode lit (E1 2oo2)
  int prop_bs_n_ = 0;              // v2.10 RE-18: consecutive raw samples at/above the propane backstop level
  Persist p_torch_loss_;           // E1 -> E2: both sensors no flame
  bool fa1_super_ = false, fa1_both_dark_ = false, fa1_pt_lit_ = false, fa1_ph_lit_ = false;
  float photo_run_ref_ = 0.0f; bool photo_run_ref_ok_ = false; Persist p_photo_fo_;   // REV-GNC-2 (2) optical flame-out (RUN, Pc invalid)
  bool fo_opt_armed_ = false; int fo_view_n_ = 0;   // photo_run_ref_ok_ = main-chamber view proven in this burn
  // v2.9 coast re-zero
  float pc_zero_arm_ = 0.0f, ptorch_zero_arm_ = 0.0f;   // ARM auto-zeros (the coast re-zero limit is taken from them)
  double rz_acc_ = 0.0, rz_acc_t_ = 0.0; int rz_n_ = 0, rz_n_t_ = 0; float rz_min_ = 0.0f, rz_max_ = 0.0f;
  bool rz_done_ = false, rz_applied_ = false, rz_event_ = false, rz_rejected_ = false;
  float rz_shift_ = 0.0f;
  // v2.10 RE-07 rolling second re-zero block
  double rz2_acc_ = 0.0, rz2_acc_t_ = 0.0, t_rz2_end_ = -1.0; int rz2_n_ = 0, rz2_n_t_ = 0;
  float rz2_min_ = 0.0f, rz2_max_ = 0.0f, rz2_z_ = 0.0f, rz2_span_ = 0.0f, rz2_zt_ = 0.0f; bool rz2_have_ = false, rz2_zt_ok_ = false;
  // v2.12 R3-01 option (b) seat compensation; TB-state; J-FWD indication; torch re-zero flag; purge calibration
  Inputs in_c_;                    // compensated copy of the inputs (pc_Pa - seat_comp_)
  float seat_coef_ = 0.0f, seat_comp_ = 0.0f, seat_ref_K_ = 0.0f, seat_tcal_K_ = cfg::kPcSeatTcalDefault_K;
  double sref_acc_ = 0.0; int sref_n_ = 0, sref_win_n_ = 0;   // seat-reference accumulator over the ARM window
  bool seat_ref_ok_ = false, seat_frozen_ = false, seat_noref_ = false, seat_tc_ok_ = false;
  // v2.13 (REV-ELEC-4 E4-01 / Q2): compensation temperature T_c, light-window hold, TC4 step / rate checks
  float seat_Tc_K_ = 0.0f;         // compensation temperature (slewed toward the reading outside the hold; frozen in the hold / after a trip)
  float seat_Tprev_K_ = 0.0f;      // previous valid finite TC4 reading (step check)
  bool seat_prev_ok_ = false;      // seat_Tprev_K_ holds a reading
  bool seat_hold_ = false;         // this tick: light-window hold active
  bool seat_step_ = false;         // f3::SEAT_STEP (latched until the next ARM)
  bool seat_hold_prev_ = false;    // hold state of the previous tick (hold-end gap record)
  double t_e2_seat_ = -1.0;        // E2 time of this start for the hold end (-1 = no E2 in this start)
  float seat_gap_max_K_ = 0.0f;    // largest |reading - T_c| at a hold end in this arming (SIL / log record; no action)
  // v2.13 (LEAD 16:11Z ITEM 2, accepted 16:27Z) catch-up after the hold (config.h (3a))
  double t_seat_hold0_ = -1.0;     // hold start (first tick with the hold on)
  bool seat_catch_ = false;        // catch-up active: rate trip replaced by the growth / time-cap trips
  float seat_catch_lim_K_ = 0.0f;  // growth limit: lowest gap since the hold end + kPcSeatStepMax_K
  double t_seat_catch_cap_ = -1.0; // catch-up time cap (hold end + kPcSeatCatchCapX x hold duration)
  bool build_event_ = false, build_boot_seen_ = false;   // v2.13 EVENT BUILD pulse (boot, every ARM command)
  bool tb_state_ = false, tb_pcs_high_ = false, jfwd_ls_ = false, pt_rz_rej_ = false;
  float purge_flow_s_ = cfg::kPurgeFlow_s, hb_cap_s_ = cfg::kHbleedCap_s;
};

}  // namespace ecu
