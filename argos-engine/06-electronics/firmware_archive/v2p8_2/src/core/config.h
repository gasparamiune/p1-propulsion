// ARGOS engine ECU firmware - tunable configuration (v2.8.2, 2026-10-13: GNC review REV-GNC-1 RG-08 - a pintle-position anomaly in the
// coast (encoder invalid, or lift above kCoastPintleOpen_m for kCoastPintleOpenN ticks) latches the relight state UNKNOWN / UNPRIMED and
// forces the prep path until a confirmed light or DISARM. v2.8.1: LEAD stand fallback (b) windows R1 = R2 = 0.35 s, R3 deleted,
// strap-keyed; over-thrust 650 N on 3 consecutive FC_THRUST frames ADOPTED, also with a valid Pc; ABORT/SHUTDOWN exit never on an invalid
// Pc reading. v2.8, relight = RELIGHT at T_fire with the NC valve opened at E0
// and the ignition lift at E1 (LEAD Finding A = option (b)), ignition window W counted from the lift command (stand R1 0.40 s / R2
// 0.50 s / R3 0.65 s with superheat proven at both state TCs / R4 no relight on an invalid sensor; flight 0.65 s on every relight),
// torch gate 0.16 s (provisional), ignition lift from a lift-vs-T_tank table (default 0.2039 mm, CF-3 calibrates), S1 relief
// monitor (stand lockout, flight flag), provisional over-thrust abort, mode strap, case over-temperature 448.15 K armed with the MV
// open (start refused above 433.15 K), bay-temperature ARM inhibit, TLM_RELIGHT relight-planning status; v2.8 final (LEAD decisions
// of 2026-10-13 from COMB v2.4 / GNC v3 / MECH): seat timeout 0.30 s, abort -> vapour-segment start (NV b3), tank interlock 24 C with
// P_tank cross-check, TLM_RELIGHT PRIMED/UNPRIMED/UNKNOWN valid after the MECO valve closure (FC staleness 0.3 s), torch gate 0.16 s
// confirmed by Combustion, RUN-entry Pc reference capped at the map setpoint (no false FLAMEOUT after a late-light spike); v2.7, 2026-10-13: Combustion review fold-in - torch-flame gate on P_torch,
// torch valves closed on the light-confirmation event, abort matrix (every abort drops the NC valve at once), pintle-then-valve
// normal shutdown with a seat-confirmation timeout, no in-flight relight retry (lockout), C7 relight check extension, pintle-rail
// loss (LTC4365 OV disconnect) -> PINTLE_FAULT; v2.6, 2026-10-12: pintle tracking/stall monitor with back-off, jam events
// recorded non-volatile (MAINT_JAM inhibit), HV69 pulse calibration as a parameter, unlit pintle limited to the ignition lift,
// MV closed through the coast and ramped on every opening (LEAD rules); v2.5: M2 re-read of combustion.json v2.1 / gnc.json v2 -
// HV69 pintle on the in-line crank-slider and the regulated 7.4 V rail, Combustion v2 start sequence (propane off at 0.40 s,
// ignition check 3.0 bar abs at 0.35 s, 2500 N/s start ramp, vented-chamber check), ECU map from Combustion's map v2;
// v2.4 GNC V_val 6.6 V ARM rule, ENG-07d gimbal notch, ENG-07b saturation episodes; v2.3 FM-PWR-01 supply monitor,
// e-fuse, heater permit; v2.2 chamber over-pressure, lead decision MEOP 45 bar; v2.1: TVC from mechanical.json v1)
// Every number carries its unit in the name and a source tag in the comment:
//   [REQ] requirement, [DS] datasheet, [ASSUMED] placeholder (range), [DERIVED] computed (script),
//   [DESIGN] chosen here (Electronics), [COMB] from combustion.json via the generated engine_params.h.
// SI units: Pa, s, m, rad unless the suffix says otherwise (_deg, _us, _mm, _bar).
// Pressure convention: transducers are read as GAUGE pressure (HAL); the Pc loop, the valve map and the
// thrust model work in ABSOLUTE pressure = gauge + eng::kPamb_Pa. Names end in Abs_Pa when absolute.
#pragma once
#include <cstdint>
#include "engine_params.h"
#include "mech_params.h"

namespace ecu {
namespace cfg {

// ---------------------------------------------------------------- timing
constexpr float kDt_s = 0.001f;                 // [DESIGN] 1 kHz control/safety tick
constexpr double kTimeEps_s = 1.0e-6;          // [DESIGN v2.8] slack of the deadline comparisons against float time constants: float
                                                //   rounding of e.g. 0.160f (-3.6e-9 s) exceeded the v2.7 1e-9 slack, so the torch gate fired one
                                                //   tick earlier (0.160 s) than the 0.65 s window rule (0.651 s); 1e-6 s >> float ulp, << 1 ms tick
constexpr float kFcCmdPeriod_s = 0.002f;        // [DESIGN] FC sends CMD_FAST at 500 Hz
constexpr float kLinkDegraded_s = 0.020f;       // [DESIGN] hold last command after 20 ms silence
constexpr float kLinkLost_s = 0.100f;           // [DESIGN] act on link loss after 100 ms
constexpr float kHwWatchdog_s = 0.050f;         // [DESIGN] external watchdog timeout (hardware)

// ---------------------------------------------------------------- pintle actuator (v2.5: MKS HV69 + in-line crank-slider)
// LEAD 2026-10-12 provisional baseline (fallback: jackshaft layout). Regulated 7.4 V rail (TPS552882, calc/pintle_rail_v1.py),
// so the pintle speed does not sag with the TVC servos. HV69 data are retailer copies of MKS data: TO-CONFIRM with MKS and
// at bench test B-PNT-1 (item 1, gating: travel >= 103.1 deg commanded 10 -> 113.09 deg crank and the pulse range, from a
// 800-2200 us sweep in 10 us steps at a 1 A limit; then speed, stall current, case temperature, closing time, back-drive).
// v2.6 (LEAD): the pulse calibration (centre, us/deg, clamps) is a run-time parameter (linkage::PintleCal, EngineEcu::pintle_cal)
// set from the sweep; the values below are the defaults until then. Rail: TPS552882 7.483 V typ (calc/pintle_rail_v2.py).
constexpr float kPintleLiftMaxCmd_m = eng::kPintleStroke_m;   // [COMB] 4 mm
constexpr float kPintleRateCmd_mps = 0.060f;    // [DESIGN] command slew; above the HV69 + crank capability (~20-28 mm/s
                                                //   mid-stroke), so the servo, not this limit, sets the stroke time
constexpr float kPintleCloseRate_mps = 0.200f;  // [DESIGN] shutdown/abort: above the drive's own speed, so the HV69 and the spring
                                                //   set the closing time (COMB v2.2 retired the '<= 50 mm/s (80 ms)' item;
                                                //   ENG-05 from 75 %: 0.059-0.083 s, calc/pintle_dynamics_v2.py, MECH v2.2)
constexpr float kPintleCenter_us = 1520.0f;     // [DS HV69, retailer copies of MKS data] neutral pulse (default; B-PNT-1 sets it)
constexpr float kPintleUsPerDeg = 10.0f;        // [ASSUMED] travel/pulse not published -> B-PNT-1 sweep (TO-CONFIRM with MKS)
constexpr float kPintleMin_us = 900.0f;         // [ASSUMED, LEAD default] pulse clamps until the B-PNT-1 sweep; whether the HV69
constexpr float kPintleMax_us = 2100.0f;        //   accepts 800-2200 us is TO-CONFIRM (MKS/Lindinger publish no range)
constexpr float kPintleCalMin_us = 800.0f;      // [DESIGN] widest clamps a calibration may set (sweep range)
constexpr float kPintleCalMax_us = 2200.0f;
constexpr float kPintleDeadband_us = 1.0f;      // [DS HV69] sets the integrator freeze band
// v2.6 pintle tracking / stall monitor (LEAD 2026-10-12: position error plus current or time, back off the command, fault flag,
// the PINTLE_FAULT abort of the throttle path (MV closes = the safety backstop); every jam is recorded non-volatile because a
// jam means bearing A must be replaced before the next flight). The HV69 moves ~28 mm/s mid-stroke against a 60 mm/s command,
// so the v2.5 command-model monitor (15 ms lag) tripped on large steps; v2.6 trips on LACK OF PROGRESS. Thresholds approved by
// the lead 2026-10-12. calc/pintle_dynamics_v2.py (MECH v2.2, 271 simulated records): longest normal interval without a 20 um
// progress mark 24 ms; slowest normal full stroke t99 0.38 s (bench, +10 % spring, mu 0.20).
constexpr float kPintleStallErr_m = 0.15e-3f;   // [DESIGN] |lift cmd - encoder lift| above this = tracking episode (P-band
                                                //   droop of the servo <= 0.054 mm at 4 mm on the bench)
constexpr float kPintleProgMin_m = 0.02e-3f;    // [DESIGN] progress mark: encoder lift moved >= 20 um toward the command
constexpr float kPintleProgWin_s = 0.020f;      // [DESIGN] 'no progress' flag (log, current path) after 20 ms without a mark
constexpr float kPintleStallTime_s = 0.100f;    // [DESIGN, LEAD approved] time path: no progress mark for 100 ms -> stall
constexpr float kPintleStallI_A = 1.0f;         // [DESIGN] current path: rail current above 1.0 A (HV69 stall 1.2-1.7 A DERIVED,
                                                //   unpublished -> B-PNT-1) with no progress mark for 20 ms ...
constexpr float kPintleStallTimeI_s = 0.050f;   // [DESIGN, LEAD approved]  ... continuously for 50 ms -> stall
constexpr float kPintleTrackTime_s = 0.60f;     // [DESIGN] tracking timeout: error above kPintleStallErr_m for 0.6 s while creeping
constexpr float kPintleNoProgNormal_s = 0.0242f;   // [DERIVED calc/pintle_dynamics_v2.py] normal-operation maximum (checked)
constexpr float kPintleFullStrokeSlow_s = 0.383f;  // [DERIVED same] slowest normal full stroke t99 (bench, +10 % spring, mu 0.20)
static_assert(kPintleStallTime_s >= 4.0f * kPintleNoProgNormal_s, "stall time path too close to normal operation");
static_assert(kPintleTrackTime_s >= 1.5f * kPintleFullStrokeSlow_s, "tracking timeout too close to the slowest full stroke");
constexpr uint16_t kClearJamKey = 0xBEA1;       // [DESIGN] CLEAR_JAM argument ("bearing A replaced"), accepted in SAFE only
// LEAD 2026-10-12 rule (a): the ignition sequence never opens the pintle past the ignition lift until Pc confirms light (an
// unlit opening has < 1.5 torque margin in every configuration, COMB needle_force_bounds_v2p3); no light -> close and abort.
// v2.8 ignition lift (LEAD 2026-10-13): defined by cold flow (<= 37.4 g/s at the A1 relight state, <= 37.1 g/s at 20 C), calibrated
// at CF-3 as a lift-vs-T_tank table; T_tank = Tsat(P_tank) at E0 (n2o_sat_table.h). BUILD-TIME table (v2.9 takes the CF-3 rows):
// linear between rows, clamped outside; P_tank invalid or outside the saturation table -> the smallest lift of the table. Default
// (LEAD accepted): flat 0.2039 mm = 37.1 g/s at 20 C, Pc 1 bar in the SIL plant flow model (sil/ign_lift_cal.cpp ->
// results/ignition_lift_v1.json; 35.0 g/s at the A1 relight state 286.7 K; same Dyer k-blend, Cd 0.70, frustum area as Combustion).
// At a fixed lift the flow rises with T_tank (0.2048 mm: 34.0 / 37.3 / 39.6 g/s at 283 / 293 / 303 K): CF-3 records the N2O
// temperature of every point. v2.5-v2.7 used Combustion's 20 % point (0.301 mm, 51.6 g/s in the SIL).
constexpr int kIgnLiftN = 2;
constexpr float kIgnLiftT_K[kIgnLiftN] = {273.15f, 313.15f};       // [DESIGN] table temperatures, ascending
constexpr float kIgnLiftTab_m[kIgnLiftN] = {0.2039e-3f, 0.2039e-3f};   // [DERIVED SIL flow model; LEAD default 2026-10-13]
constexpr float ignLiftTabMax() { float m = kIgnLiftTab_m[0]; for (int i = 1; i < kIgnLiftN; ++i) m = kIgnLiftTab_m[i] > m ? kIgnLiftTab_m[i] : m; return m; }
constexpr float ignLiftTabMin() { float m = kIgnLiftTab_m[0]; for (int i = 1; i < kIgnLiftN; ++i) m = kIgnLiftTab_m[i] < m ? kIgnLiftTab_m[i] : m; return m; }
constexpr bool ignLiftTabAscending() { for (int i = 1; i < kIgnLiftN; ++i) if (!(kIgnLiftT_K[i] > kIgnLiftT_K[i - 1])) return false; return true; }
static_assert(ignLiftTabAscending(), "ignition-lift table temperatures must ascend");
static_assert(ignLiftTabMin() > 0.0f, "ignition-lift table entry not positive");
constexpr float kPintleUnlitLiftMax_m = ignLiftTabMax();   // [LEAD rule (a)] cap on the trim-scaled ignition lift (v2.7: 20 % lift)
static_assert(kPintleUnlitLiftMax_m <= eng::kPintleIgnitionLift_m, "ignition-lift table above Combustion's 20 % ignition lift");

// ---------------------------------------------------------------- main valve (spring-return, latched)
// v2.8 (LEAD 2026-10-13 MV concept change, MECH mv_actuator_v1 sha256 a2d8cdd3): the SB-2292SG cannot open the Swagelok 62-series ball
// (15.2 N m needed vs 1.08 N m allowed). Baseline = MV-P balanced poppet: seat 11 mm, lift 2.75 mm, Cv 3.64 (Cd 0.65 ASSUMED), 45.7 N
// closing bias at 6.5 MPa, constant-rise cam on the opener (0.60 N m avg / 0.64 N m peak = 30 % of 2.16 N m), over-centre latch 10:1
// (holding magnet 30.5 N incl. 2x, calc/mv_latch_magnet_v1.py), dashpot-damped closing ~30 ms, OPEN/CLOSED switches on the cam follower.
// The opener pulse profile, the latch logic and the switch checks below are unchanged (the cam replaces the one-way dog). Fallback if
// B-MV-1 fails: the Swagelok ball with a pneumatic spring-return actuator (then this section changes).
constexpr float kMvOpenerRest_us = 1500.0f;     // [DESIGN] dog disengaged
constexpr float kMvOpenerCock_us = 1950.0f;     // [DESIGN] +45 deg horn: drives the valve open against its spring (v2.8: cam
                                                //   rise must end <= 40 deg of the stroke, latch-engagement margin, MECH/B-MV-1)
constexpr float kMvCockTime_s = 0.35f;          // [DESIGN] hold cock position, then return to rest (latch holds)
constexpr float kMvCloseConfirm_s = 0.50f;      // [DESIGN] CLOSED switch expected within 0.5 s of latch drop (fault flag only;
                                                //   v2.8 MV-P closes in ~0.03 s + latch release, B-MV-1 measures both)
// line priming (v2.2, COMB v2 via lead 2026-10-12): opening the MV into a dead-ended gas-filled line compresses the gas to
// 600-900 K (N2O decomposition risk). If P_feed < 0.5 P_tank at PREPRESS entry: pintle to a 0.10 mm bleed lift first,
// then open the MV over >= 0.3 s. A primed line (relight) keeps the normal sequence.
constexpr float kPrimeSlowFrac = eng::kPrimeSlowFrac;   // [COMB v2.1] P_feed / P_tank (absolute) below this -> slow priming
constexpr float kBleedLift_m = eng::kBleedLift_m;       // [COMB v2.1] pintle bleed lift during slow priming
constexpr float kBleedSettle_s = 0.060f;         // [DESIGN] pintle at the bleed lift before the MV starts to open
constexpr float kBleedConfirm_m = 0.05e-3f;      // [DESIGN] encoder (when valid) must show >= this lift, else PREPRESS_FAIL
constexpr float kMvOpenRampSlow_s = 0.35f;       // [DESIGN] opener rest -> cock ramp (COMB v2.1: >= eng::kMvOpenRampMin_s)
static_assert(kMvOpenRampSlow_s >= eng::kMvOpenRampMin_s, "isolation-valve opening ramp shorter than Combustion's minimum");
constexpr float kMvCockHold_s = 0.15f;           // [DESIGN] hold at cock after the ramp so the holding magnet engages
constexpr bool kMvHoldOpenInCoast = false;      // [LEAD 2026-10-12 rule (b)] the NC main valve stays CLOSED through the MECO coast
                                                //   until the pintle seat leak-tightness is measured (B-PNT-1 N2 leak test);
                                                //   a relight then runs PREPRESS (v2.5 'true' = MV held open, 0.3 s relights)
constexpr bool kMvRampEveryOpening = true;      // [LEAD 2026-10-12 rule (b)] every MV opening, relights included, uses the
                                                //   >= 0.3 s opener ramp; the line-priming bleed follows the COMB start rule
constexpr float kCoastMvMax_s = 30.0f;          // [DESIGN] after this coast time the MV closes (relight then needs PREPRESS)
constexpr float kPrepressHoldMax_s = 60.0f;     // [DESIGN] primed-and-waiting limit, then back to ARMED (MV closes)

// ---------------------------------------------------------------- TVC servo PWM (Savox SB-2292SG, DS)
constexpr float kServoCenter_us = 1500.0f;      // [DS] neutral
constexpr float kServoUsPerDeg = 10.0f;         // [DS] 100 deg over 1000 us
constexpr float kServoMin_us = 900.0f;          // [DS] max travel 900-2100 us
constexpr float kServoMax_us = 2100.0f;
constexpr float kServoFrame_s = 0.003003f;      // [DS] 333 Hz

// ---------------------------------------------------------------- TVC (geometry from mechanical.json v1 via mech_params.h)
constexpr float kGimbalSoftLimit_rad = mech::kRangeVec_rad;    // [MECH/GNC] 7.0 deg per axis
constexpr float kGimbalRadialLimit_rad = mech::kRangeVec_rad;  // [MECH request] 7.0 deg on the VECTOR norm (8 deg conical stop)
// v2.4: ECU command shaping = GNC gnc.json v2 requirements.gimbal.command_shaping_in_ecu (MANDATORY: without it the rocking
// mode destabilises the loop, 6-DOF linkage torque 154 N m p99). Chain per axis, as GNC sim6 v2.5: pre-limit (vector norm
// <= 2 x range) -> slew limit 100 deg/s -> 2nd-order low-pass 50 rad/s, zeta 0.5 -> [optional ENG-07d notch] -> axis and
// vector limits 7 deg. v2.2-v2.3 had a 150 deg/s limit only and assumed the FC shaped its commands (superseded).
constexpr float kGimbalRateLimit_radps = eng::kGncShapeSlew_radps;  // [GNC gnc.json v2] 100 deg/s per-axis command slew limit
constexpr float kGimbalCmdLpfW_radps = eng::kGncShapeW_radps;       // [GNC gnc.json v2] structural low-pass natural frequency
constexpr float kGimbalCmdLpfZeta = eng::kGncShapeZeta;             // [GNC gnc.json v2]
constexpr float kGimbalPreLimitFactor = 2.0f;        // [GNC sim6 v2.5] raw command pre-limited at 2 x range (bounded states)
// v2.6 (mechanical.json v2, as-built n 4.8): the horn clamp is per sense - the eye-below-pivot geometry makes the servo angle
// asymmetric (7 deg cone -32.4 / +37.4 deg, 8 deg stop -36.8 / +44.2 deg). Clamp = extremes on the 7.5 deg cone (generated).
constexpr float kTvcPsiMin_rad = mech::kPsiClamp_rad[0];   // [DERIVED gen_mech_params v2] -34.6 deg
constexpr float kTvcPsiMax_rad = mech::kPsiClamp_rad[1];   // [DERIVED gen_mech_params v2] +40.7 deg
constexpr float kGimbalFaultErr_rad = 0.026180f;    // [DESIGN] 1.5 deg cmd-vs-encoder mismatch
constexpr float kGimbalFaultTime_s = 0.050f;        // [DESIGN]
constexpr float kGimbalModelTau_s = 0.020f;         // [DESIGN] expected-response lag used by fault monitor
constexpr float kGimbalFaultRateWin_s = 0.040f;     // [DESIGN v2.2] mismatch allowance grows by 40 ms x model rate during
                                                    //   slews (actuator near its rate limit at full deflection, S7)
// v2.4 ENG-07d (LEAD 2026-10-12, provisional): flex gain margin >= 6 dB at the gimbal rocking mode (GNC: 26.4-45.7 Hz).
// Configurable second-order notch on the engine-angle command (TvcShaper, ahead of the limits). DISABLED until calibrated;
// v2.6: per axis (alpha/beta modes differ 8-15 %, GNC csi_v3), set from B-TVC-1 (GimbalNotchCal, NvGimbalCal, or
// Cmd::SET_GIMBAL_NOTCH / SET_GIMBAL_NOTCH_QD in SAFE) and REQUIRED for ignition (kIgnitionRequiresGimbalNotch).
constexpr bool kGimbalNotchEnabled = false;         // [DESIGN] off until B-TVC-1 measures the mode
constexpr float kGimbalNotchHz = 35.0f;             // [DESIGN placeholder] centre of the GNC band; replace with B-TVC-1
constexpr float kGimbalNotchQ = 1.0f;               // [DESIGN] wide (-3 dB points ~ +/-50 % of f0) until the mode is measured
constexpr float kGimbalNotchDepth_dB = -12.0f;      // [DESIGN] 6 dB margin target + 6 dB allowance for the mode scatter
constexpr float kGimbalNotchMinHz = 5.0f;           // [DESIGN] accepted range for the SAFE-only setter
constexpr float kGimbalNotchMaxHz = 200.0f;
constexpr float kGimbalNotchQMin = 0.3f;            // [DESIGN v2.6] accepted Q range (per axis)
constexpr float kGimbalNotchQMax = 10.0f;
constexpr float kGimbalNotchDepthMin_dB = -40.0f;   // [DESIGN v2.6] accepted depth range (per axis)
constexpr float kGimbalNotchDepthMax_dB = -1.0f;
// v2.6 LEAD 2026-10-12 (GNC csi_v3): the notch is REQUIRED - IGNITE/RELIGHT are refused unless both axes carry an enabled
// notch (the B-TVC-1 record loaded at boot or set in SAFE). ARM is not affected (B-PNT-1 runs before B-TVC-1 on the ARM bus).
constexpr bool kIgnitionRequiresGimbalNotch = true;
// v2.4 ENG-07b (LEAD 2026-10-12): no ACTUATOR saturation episode longer than 0.1 s in the landing burn (GNC sim6 v2.5:
// servo torque- or speed-limited, moment scale factor < 1). The ECU cannot see servo torque, so the episode timer runs on a
// proxy: encoder off the linear expected-response model (first order, kGimbalModelTau_s) by more than kGimbalSatErr_rad on
// either axis. Command limiting in this ECU (7 deg axis/vector limit b0, 100 deg/s shaping b1) is logged as context only
// (it is GNC's anti-windup saturation, not ENG-07b). Logged (v4: sat_ms, sat_flags, sat_long) and flagged (TLM_GIMBAL b7).
constexpr float kGimbalSatErr_rad = 0.0087266f;     // [DESIGN] 0.5 deg engine (servo proportional band ~2 deg / n 4.8 = 0.4
                                                    //   deg, ASSUMED); calibrate against servo current/duty at B-TVC-1
constexpr float kGimbalSatRateWin_s = 0.012f;       // [DESIGN] lag allowance during slews: 10-25 Hz actuator (GNC MC range,
                                                    //   zeta 0.7) lags 9-22 ms vs the 20 ms model -> +/-12 ms x model rate
constexpr float kSatEpisodeMax_s = 0.100f;          // [REQ ENG-07b, LEAD 2026-10-12 provisional]

// ---------------------------------------------------------------- thrust / Pc command
constexpr float kPcSpMinAbs_Pa = 0.95f * eng::kPcFloorAbs_Pa;  // [DESIGN] 95 % of COMB 12.5 % floor Pc; raise to the qualified floor
constexpr float kPcCmdCapAbs_Pa = eng::kPcNormalCapAbs_Pa;    // [LEAD 2026-10-12 via COMB v2.1] normal command cap Pc <= 25 bar
constexpr float kPcSpMaxAbs_Pa = (1.04f * eng::kPcMaxAbs_Pa < kPcCmdCapAbs_Pa) ? 1.04f * eng::kPcMaxAbs_Pa : kPcCmdCapAbs_Pa;
                                                              // [DESIGN] 104 % of the 500 N Pc, never above the lead cap
constexpr float kPcSpRateLimit_Paps = 250.0e5f;     // [DESIGN, SIL-tuned] setpoint slew ~5300 N/s (GNC >= 1000 N/s; 100->500 N in 80 ms)
constexpr float kRefModelDelay_s = 0.012f;          // [DESIGN, SIL-tuned v2.2: +3 ms = group delay of the 50 Hz 2nd-order Pc filter;
                                                    //  S2 small-step overshoot 8.7 % at 9 ms, 5.1 % at 12 ms, 3.4 % at 15 ms (slower settle)] lift->measured Pc
constexpr float kRefModelTau_s = 0.015f;            // [DESIGN, SIL-tuned] reference model lag (servo + chamber + transducer)
constexpr float kLiftMinRunFrac = 0.85f;            // [DESIGN] RUN lower lift clamp = map lift at 0.85 x minimum Pc setpoint (anti-flameout)
constexpr float kKpNorm = 0.30f;                    // [DESIGN, SIL-tuned] loop-gain normalised P (Kp*g, dimensionless)
constexpr float kKiNorm_ps = 20.0f;                 // [DESIGN, SIL-tuned] Ki*g [1/s]
constexpr float kFreezeBandMin_Pa = 0.03e5f;        // [DESIGN] integrator freeze band floor
constexpr float kFreezeBandFrac = 0.6f;             // [DESIGN] band = max(min, frac * one-deadband Pc step)
constexpr float kPcFilterFc_Hz = 50.0f;             // [COMB v2 via lead 2026-10-12] ~50 Hz low-pass against the 144-188 Hz, zeta < 0.03
                                                    // sense-line resonance; [DESIGN] 2nd-order Butterworth on the 1 kHz decimated Pc
                                                    // (v2.1: 1st-order 120 Hz). Lag at 20 Hz is 34 deg, not < 1 deg (see REPORT)
constexpr float kTrimLimit = 0.40f;                 // [DESIGN] multiplicative map trim authority +/-40 % (Cd 0.6-0.8, regression x0.6-1.5, eta_c* band)
constexpr float kRunIntegHold_s = 0.15f;            // [DESIGN, SIL-tuned] no integration right after ignition (fuel thermal lag)
constexpr float kIntegRefTolFrac = 0.05f;            // [DESIGN, SIL-tuned] integrate only while |sp - ref| < frac*sp (reference model settled); 1 = always

// ---------------------------------------------------------------- roll thrusters (GNC v1 proposal: N2O-vapour couples on 2 NC solenoids)
constexpr float kRollDeadman_s = 0.050f;            // [DESIGN] roll valve closes 50 ms after the last valid CMD_AUX frame
constexpr float kRollMaxPulse_s = 1.0f;             // [DESIGN] continuous on-time limit per valve (stuck-command guard)

// ---------------------------------------------------------------- sequencing
constexpr float kPrepressTimeout_s = 0.60f;         // [DESIGN] MV open + feed fill
constexpr float kFeedPrimedFrac = 0.80f;            // [DESIGN] p_feed > 0.8 p_tank -> primed
constexpr float kIgnitionDetectAbs_Pa = eng::kIgnitionPcAbs_Pa;   // [COMB v2.1] Pc above 3.0 bar ABSOLUTE -> lit (v2.4: 3 bar gauge)
                                                    // ignition check time eng::kIgnitionCheck_s (0.35 s from IGNITION entry;
                                                    // v2.4: 0.12 + 0.40 s): not lit by then -> ABORT NO_IGNITION
constexpr int kIgnitionConfirmN = 5;                // [DESIGN v2.6, OI-6] light is confirmed only when the FILTERED and the RAW
                                                    //   (1 kHz decimated, auto-zeroed) Pc are both above kIgnitionDetectAbs_Pa
                                                    //   for 5 consecutive ticks, so a spark-EMI spike or one bad ADC frame cannot
                                                    //   release the pintle past the ignition lift (LEAD rule (a)); cost <= 5 ms
                                                    //   at the ~0.1 bar/ms ignition rise
constexpr float kPcVentedMax_Pa = 0.10e5f;          // [COMB OI-12] torch fires only with |Pc gauge| below this (chamber vented)
constexpr float kStartRamp_Nps = eng::kStartRamp_Nps;   // [COMB v2.1 / GNC] thrust ramp after ignition until the command is met
constexpr float kPropaneCloseAllow_Pa = 1.0e5f;     // [DESIGN] propane closes at raw Pc >= (5.0 - 1.0) bar abs: 1 bar allowance for the
                                                    //   solenoid closing time (~10-15 ms ASSUMED) at the ignition Pc rise (~0.1 bar/ms)
constexpr double kRetryVentWait_s = 5.0;            // [COMB v2.2 igniter.sequence.abort_if_no_ignition] wait >= 5 s for the
                                                    //   chamber to vent N2O before a retry; ELEC applies it after FLAMEOUT too
constexpr float kSparkDwell_s = 0.003f;             // [ASSUMED] coil dwell (hardware limits primary to 3 A)
constexpr float kShutdownPcDone_Pa = 1.5e5f;        // [DESIGN] gauge Pc below 1.5 bar -> out
constexpr float kShutdownTimeout_s = 0.50f;         // [DESIGN]
constexpr float kPurgeTime_s = 0.0f;                // [ASSUMED] 0 = no purge in flight (Combustion to set)
constexpr int kMaxStarts = 4;                       // [REQ ENG-04] >= 3 per flight + 1 margin
constexpr float kAutoZeroTime_s = 0.5f;             // [DESIGN] Pc auto-zero averaging on entering ARMED
constexpr float kPcArmZeroMax_Pa = 0.5e5f;          // [DESIGN] ARM sanity: |filtered gauge Pc| below this before the auto-zero
                                                    //   (v2.6 OI-6: on the 50 Hz filtered value, v2.2-v2.5 used one raw sample).
                                                    //   0.5 bar = 0.73 % FS: needs the B-PC-1 bench zero (XdcrCal::offset_Pa);
                                                    //   the datasheet bounds the uncalibrated zero only by the 1.5 % FS TEB
                                                    //   (1.03 bar over -20..85 C), so the thermal zero shift is TO-MEASURE
constexpr float kRunSettle_s = 0.30f;               // [DESIGN] band checks start after settling

// ---------------------------------------------------------------- abort thresholds
// chamber over-pressure (v2.2; v2.5 values read from combustion.json v2.1 pressure_limits, lead decisions 2026-10-12).
// Firmware trip below; independent hardware trip ~31 bar g (32 bar abs) on U330/U331 (calc/ovp_threshold_v1.py) -> ovp_ok.
constexpr float kPcMeopLeadAbs_Pa = eng::kPcMeopAbs_Pa;       // [LEAD via COMB] chamber MEOP 45 bar (proof 67.5 bar)
constexpr float kPcOverPressureAbs_Pa = eng::kPcAbortAbs_Pa;  // [LEAD via COMB] ECU over-pressure abort ~30 bar, all states but SAFE
static_assert(kPcCmdCapAbs_Pa < kPcOverPressureAbs_Pa && kPcOverPressureAbs_Pa < kPcMeopLeadAbs_Pa, "cap < abort < MEOP");
constexpr float kPcOverPressureTime_s = 0.003f;     // [DESIGN] persistence (filtered 1 kHz Pc); HARD_START if during ignition
constexpr float kHwOvpTime_s = 0.002f;              // [DESIGN] OVP_OK low this long -> HW_OVERPRESSURE abort
constexpr float kHwOvpArmSettle_s = 0.005f;         // [DESIGN] OVP_OK ignored for 5 ms after ARM_REQ rises (latch set on the edge)
// v2.6: the v2.2-v2.5 ABORT check 'pintle still open (> 0.5 mm) 40 ms after the abort -> drop the ARM bus' is RETIRED. It was
// sized for the v2.2 pintle; the HV69 crank-slider needs 0.13-0.17 s from 4 mm to the seat (calc/pintle_dynamics_v2.py, MECH
// v2.2), so the 40 ms check dropped the bus in every abort from above ~1.5 mm. In ABORT the progress monitor now runs on the
// closing command (no closing progress for kPintleStallTime_s -> ARM bus released, the spring back-drives the unpowered servo);
// after SAFE entry the unpowered spring closing is checked once (below).
constexpr float kPintleCloseSlow_s = 0.170f;        // [DERIVED calc/pintle_dynamics_v2.py] slowest powered closing 4 mm -> seat,
                                                    //   MEOP-equivalent needle load, spring -10 %, guide mu 0.20 (MECH v2.2)
constexpr float kPintleUnpoweredClose_s = 1.0f;     // [ASSUMED] unpowered spring closing (back-driving the HV69) is complete 1 s after
                                                    //   SAFE entry; lift above kPintleStallErr_m then = jam NOT_CLOSED (B-PNT-1 item 4)
static_assert(kPintleUnpoweredClose_s >= 3.0f * kPintleCloseSlow_s, "unpowered closing check too close to the powered closing time");
constexpr bool kArmRequiresPintleEncoder = true;    // [DESIGN v2.6] ARM refused (PINTLE_FAULT) without a valid pintle encoder: the
                                                    //   stall monitor, the bleed confirmation and the closing checks need it
constexpr float kAbortPcCheck_s = 0.060f;           // [DESIGN] ABORT: Pc still above the over-pressure limit after 60 ms -> drop ARM
constexpr float kFlameoutPc_Pa = 1.5e5f;            // [DESIGN] gauge Pc below 1.5 bar in RUN
constexpr float kFlameoutFrac = 0.35f;              // [DESIGN] or below 35 % of the expected Pc
constexpr float kFlameoutTime_s = 0.030f;           // [DESIGN]
constexpr float kPcBandFrac = 0.30f;                // [DESIGN] |Pc - Pc_ref| > 30 % of ref ...
constexpr float kPcBandMin_Pa = 2.0e5f;             // [DESIGN] ... and > 2 bar
constexpr float kPcBandTime_s = 0.150f;             // [DESIGN]
constexpr float kCaseOverTemp_K = 448.15f;          // [LEAD 2026-10-13 correction, MECH pre36 final] 175 C on the case TCs (az 90 / az 270,
                                                    //   OD 12.6-17.6 mm below the injector face), hold kOverTempTime_s; ARMED ONLY while the
                                                    //   MV is latched or OPEN (post-burn soak 165.9 C unpressurised exceeds the in-burn
                                                    //   peak). Basis: B1 max in-burn peak 151.8 C (MECH pre36) -> 23.2 K margin; the
                                                    //   provisional 160 C risked nuisance aborts. History: v2.7 423.15 K ASSUMED; v2.8 draft
                                                    //   433.15 K MECH provisional
constexpr float kCaseRelightMax_K = 433.15f;        // [LEAD 2026-10-13] a start command with a case TC above 160 C is refused (no valve
                                                    //   cycle, refuse::CASE_HOT); MECH: A1 case at relight 77.1 C
static_assert(kCaseRelightMax_K <= kCaseOverTemp_K, "relight refusal must not be above the case abort threshold");
constexpr float kNozzleHolderOverTemp_K = 523.15f;  // [ASSUMED] 250 C
constexpr float kServoBracketOverTemp_K = 333.15f;  // [DS-derived] pintle servo MKS HV69 rated -10..60 C (retailer copies of
                                                    //   MKS data, TO-CONFIRM): flag at 60 C on the bracket NTC; MECH mount limit
                                                    //   50 C in flight incl. relight (thermal FEA open, B-PNT-1 case temperature)
constexpr float kOverTempTime_s = 0.20f;            // [MECH 2026-10-13: 0.2 s hold] (v2.7 DESIGN, same value)
constexpr float kTankOverPressure_Pa = 65.0e5f;     // [DESIGN] gauge, below tank MEOP 70 bar / relief ~75 bar
constexpr float kTankOverPressureTime_s = 0.20f;    // [DESIGN]
constexpr float kBattArmMin_V = 8.1f;               // [LEAD 2026-10-12 ARM rule, rest voltage] (v2.2 basis: >= 7.6 V at the TVC
                                                    //   servos under peak load, calc/tvc_slew_check_v1.py; v2.1 was 7.8 V)
// v2.8 (LEAD 2026-10-13, launch constraint): the SB-2292SG servos (TVC A/B, MV opener; DATASHEET -10..50 C) stay within their rating
// in flight only if the bay is at or below about 45 C at ARM (MECH). ARM is refused (Abort::BAY_HOT) and a pad first start is refused
// (refuse::BAY_HOT) above this or with no valid reading (DS18B20 #3 on the existing 1-Wire bus, at the TVC servo bracket). Relights in
// flight are never refused on it. VALUE TO-DEFINE: the final limit must subtract the sensor (+/-0.5 K, DATASHEET -10..85 C) and the
// placement error (sensor vs servo case, bench/thermal test)
constexpr float kBayArmMax_K = 318.15f;             // [LEAD approx 45 C, TO-DEFINE]
// v2.8 final tank interlock (LEAD 2026-10-13: ENG-12 conditioning range now 15-24 C; COMB v2.4: MEOP 45 bar kept with the worst band
// corner at 44.33 bar abs for a 24 C tank, 45.06 at 25 C, 48.46 at 30 C at Cv 3.6). Tank temperature = max of the valid tank-wall
// DS18B20 #1/#2 (J608, existing heater-control sensors) and Tsat(P_tank) (P_tank 170BG; the cross-check). Above kTankIgnMax_K, or no
// valid reading at all: ARM refused (Abort::TANK_HOT); IGNITE refused on the pad (first start) and every stand start (refuse::TANK_HOT).
// Flight relights are NOT refused (flag Outputs::tank_hot_relight): the tank cools during each burn, so a hot reading at a relight can
// only be a sensor fault, and a refusal in flight loses the vehicle (same rule as the bay inhibit; for the lead to confirm).
constexpr float kTankIgnMax_K = 297.15f;            // [LEAD 2026-10-13] 24 C
constexpr float kTankXcheckMax_K = 3.0f;            // [ASSUMED] |mean wall - Tsat(P_tank)| above this = flag (TANK cross-check): DS18B20
                                                    //   +/-0.5 K (DATASHEET -10..85 C) + 170BG via Tsat (~0.4 K at 55 bar) + wall vs bulk
                                                    //   stratification (unknown); TO-VERIFY in the tank conditioning tests. The interlock
                                                    //   itself uses the maximum, so a disagreement can only make it more conservative
constexpr float kBattLow_V = 6.6f;                  // [DESIGN] 3.3 V/cell under load
constexpr float kBattLowTime_s = 0.200f;            // [DESIGN] v2.3: aborts only before the first start (LEAD 2026-10-12)

// ---------------------------------------------------------------- v2.7 Combustion review fold-in (LEAD 2026-10-13: RC-01, RC-03, C7)
// Torch (RC-01): the torch valves open at IGNITION entry (COMB t 0) and BOTH close on the light-confirmation event (+ an optional
// hold), never on a clock; never N2O-only flow through a hot torch. The COMB v2.3 fixed times eng::kPropaneOff_s (0.40 s) and
// eng::kTorchOff_s (0.60 s) are NOT used from v2.7 (combustion.json v2.4 to replace them); the propane Pc limit is kept as a
// backstop that closes BOTH valves. Torch-flame confirmation (P_torch, M3200 070BG on the torch body port) is a HARD gate for the
// pintle step: not confirmed by eng::kTorchConfirmBy_s -> TORCH_FAULT abort before any pintle opening. Timing-only only on the
// ground: SET_TORCH_GATE key in SAFE, test stand detected (finite load-cell reading), first start of the arming session, reduced
// ignition lift (Combustion's 12.5 % point).
constexpr float kTorchArmZeroMax_Pa = 1.05e5f;     // [DERIVED: M3200 TEB 1.5 % of the 070BG 70 bar FS] vented torch reading beyond this at ARM =
                                                   //   transducer fault -> ARM refused (TORCH_FAULT) unless the stand timing-only key is
                                                   //   armed; the ARMED auto-zero then removes the offset (calc/pc_transducer_v2.py: the
                                                   //   gate threshold is only 0.94 x the TEB above ambient)
constexpr float kTorchLitAbs_Pa = 2.0e5f;          // [DESIGN, ESTIMATE] torch chamber above 2.0 bar abs = lit. Basis (ESTIMATE, not
                                                   //   a measurement): lit ~3 bar abs, unlit N2O + propane cold flow ~1.0-1.2 bar abs
                                                   //   (torch flows and outlet from the COMB igniter data); IGN-1 measures both and
                                                   //   sets this threshold (B-IGN item in the bench plan)
constexpr int kTorchConfirmN = 3;                  // [DESIGN] consecutive 1 ms ticks above the threshold
constexpr float kTorchGateMaxPcG_Pa = 1.0e5f;      // [DESIGN] the confirmation counts only while the main Pc gauge is below 1 bar
                                                   //   (the torch exhausts into the chamber: chamber pressure must not fake a flame)
constexpr float kTorchHoldAfterLight_s = 0.0f;     // [COMB RC-01: close on the Pc-confirmation event] torch kept this long after
                                                   //   light confirmation (IGN-1 may raise it); the propane backstop still applies
constexpr float kTorchPropaneLag_s = 0.0f;         // [COMB RC-01: 'N2O first or both together, choose by IGN-1'] propane closes this
                                                   //   long AFTER the torch N2O valve (0 = together). Never negative:
static_assert(kTorchPropaneLag_s >= 0.0f, "propane must never close before the torch N2O valve (N2O-only flow through a hot torch)");
// v2.8: the pintle goes to the ignition lift ON the confirmation (E1), so the gate deadline no longer bounds main N2O (none is admitted
// before E1); it bounds the torch-only phase and sets the false-abort rate.
constexpr float kTorchGate_s = 0.160f;             // [DESIGN; COMB v2.4 CONFIRMED 2026-10-13: E0->E1 max 0.1494 s over 1e6 samples,
                                                   //   conditional on IGN-1 p99.9 <= 0.15 s] flame confirmed by this time from E0 or
                                                   //   TORCH_FAULT. Basis: Combustion start_latency_v2p4 E0->E1 (ASSUMED U(0.005,0.02)
                                                   //   + U(0.02,0.10) + U(0.005,0.03)): median 0.090, p99 0.138, max 0.1496 s;
                                                   //   P(> 0.100 s) = 37 %: the interface 0.100 s would abort one start in three.
                                                   //   Combustion to publish it in combustion.json v2.4 (then generated)
static_assert(kTorchGate_s >= eng::kTorchConfirmBy_s, "ECU torch gate shorter than the interface value");
constexpr uint16_t kTorchTimingOnlyKey = 0x7A11;   // [DESIGN] SET_TORCH_GATE argument for a GROUND timing-only start
constexpr float kTimingOnlyLift_m = ignLiftTabMin();   // [DESIGN v2.8] lift of a timing-only (ground) start: the smallest table lift
                                                   //   (v2.7: Combustion's 12.5 % point 0.207 mm; the v2.8 default 0.2039 mm is below it)
static_assert(kTimingOnlyLift_m <= eng::kPintleIgnitionLiftLow_m, "timing-only lift above Combustion's 12.5 % point");
constexpr float kTimingOnlyLiftAt_s = eng::kPintleToIgnitionLift_s;   // [COMB slot 0.12 s] timing-only start: lift at this time from E0
                                                   //   (no flame confirmation to wait for); W counts from it
// v2.8 ignition window W, counted from the ignition-lift command E1 (LEAD 2026-10-13: epoch = lift command; Combustion
// relight_window_rule_v2p4). v2.7 counted 0.35 s (+0.30 s C7) from IGNITION entry E0, i.e. only 0.23 s after its 0.12 s lift.
// v2.8.1 (LEAD 2026-10-13, stand relief fallback (b) ADOPTED: rounded grain port entrance r >= 4 mm, aft TC-09S DN32 burst disc, gimbal
// locked, discharge ducted out of the cell; the head-end stand disc is dropped): STAND (mode strap STAND, latched at ARM and consistent
// with the load cell) R1 first start 0.35 s; R2 every stand relight 0.35 s, including a start after an abort; R3 (0.65 s with superheat
// proven at both state TCs) DELETED - there is no extended stand window; R4 unchanged (any of MSS-1, MSS-2, P_feed invalid -> RELIGHT
// refused). The stand values are selected ONLY through the latched strap mode (EngineEcu::stand_): a FLIGHT strap (or a strap and load
// cell that disagree: ARM refused, MODE_MISMATCH) can never load them. FLIGHT (unchanged): first start 0.40 s, 0.65 s on every relight,
// the state TCs are telemetry only (TC/P_feed cannot prove liquid vs vapour at saturation; an abort in flight loses the vehicle).
// Inventories per no-light (Combustion v2p4, liquid line / whole-line vapour, Combustion flow / SIL-scaled): 0.40 s 15.2/13.7 and
// 7.0/5.9 g; 0.50 s 18.9/18.9 and 10.7/10.9 g; 0.65 s 24.6/26.6 and 16.3/18.4 g; flight up to 26.6 g accepted on the
// inventory-independent credible peak. (v2.8 final: stand R1 0.40 / R2 0.50 / R3 0.65 s.)
constexpr float kIgnWindowFirst_s = 0.40f;         // [LEAD 2026-10-13] FLIGHT first start (pad), unchanged
constexpr float kIgnWindowFirstStand_s = 0.35f;    // [LEAD 2026-10-13 fallback (b)] STAND R1 first start (v2.8 final: 0.40 s)
constexpr float kIgnWindowRelightStand_s = 0.35f;  // [LEAD 2026-10-13 fallback (b)] STAND R2 every relight (v2.8 final: 0.50 s)
#if defined(SIL_WHATIF_RELIGHT_W) && !defined(ECU_SIL_TEST_HOOKS)
#error "SIL_WHATIF_RELIGHT_W is a SIL what-if only (needs ECU_SIL_TEST_HOOKS): never in a flight, Teensy or test_core build"
#endif
#ifdef SIL_WHATIF_RELIGHT_W   // v2.8.1 SIL WHAT-IF ONLY (REV-GNC-1 RG-01: time to light a vapour segment if W were longer); not a design value
constexpr float kIgnWindowRelightLong_s = SIL_WHATIF_RELIGHT_W;
#else
constexpr float kIgnWindowRelightLong_s = 0.65f;   // [LEAD 2026-10-13] every FLIGHT relight (v2.8 final: also stand R3, deleted)
#endif
constexpr float kSuperheatMargin_K = 5.0f;         // [LEAD/COMB 2026-10-13] superheat flag margin, TELEMETRY ONLY since the R3 deletion
                                                   //   (log seq2_flags b1); sensor error sum 4.0-4.9 K at 40-65 bar abs (manifold_state_v1)
static_assert(kIgnWindowFirstStand_s <= kIgnWindowFirst_s && kIgnWindowRelightStand_s <= kIgnWindowRelightLong_s &&
              kIgnWindowFirst_s <= kIgnWindowRelightLong_s, "window order: stand <= flight, first <= relight");
// v2.8 relight path (LEAD 2026-10-13, Finding A = option (b), one design): the FC sends RELIGHT at the planned instant T_fire. In COAST
// with a primed segment (P_feed and P_tank valid, P_feed >= kPrimeSlowFrac P_tank: no gas pocket to compress) the ECU enters IGNITION
// at once: NC-valve latch and opener ramp (rule b, kMvOpenRampSlow_s + kMvCockHold_s) start on the same tick as the torch (E0); the
// pintle stays seated until E1. A segment that may hold gas (P_feed low or a pressure invalid) keeps the v2.7 PREPRESS slow priming
// (bleed + ramp + hold) before E0. Worst valve command -> Pc-confirm deadline: 0.16 + 0.65 = 0.81 s (primed); 1.37 s (gas path).
constexpr bool kRelightDirect = true;              // [LEAD 2026-10-13]
// v2.8 final (COMB v2.4, LEAD 2026-10-13): after ANY abort the next attempt is a vapour-segment start (the 30 ms MV-P closes before the
// pintle, the segment drains to ~50 % vapour). Latched in RAM and NvJamRecord b3 until a light is confirmed (RUN entry): a RELIGHT takes
// the prep path, TLM_RELIGHT never shows PRIMED (b6 POST_ABORT), and on the stand the next start uses the R2 rule (0.35 s since v2.8.1,
// R4 refusal included) instead of R1; it can only follow the SAFE state and a new ARM (no immediate retry).
// TLM_RELIGHT VALID (GNC v3): only after the MECO valve closure - in COAST once the CLOSED switch is seen with OPEN clear and the latch
// off, or once the closure is overdue (kMvCloseConfirm_s after the unlatch, fault MV): the ECU will then take the prep path (UNPRIMED).
constexpr float kMvOpenBy_s = kMvOpenRampSlow_s + kPrepressTimeout_s;   // [DESIGN] direct path: OPEN switch by this time from E0,
                                                   //   else fault MV; stand -> MV_FAULT abort, flight -> flag only (same allowance
                                                   //   as PREPRESS)
#ifndef SIL_WHATIF_RELIGHT_W   // the what-if lets the OPEN-switch deadline (flight: flag only) come first; the MV opens in its cases
static_assert(kTorchGate_s + kIgnWindowRelightLong_s < kMvOpenBy_s,
              "a valve that never opens must end in NO_IGNITION before the OPEN-switch deadline (only a lit burn reaches it)");
#endif
// v2.8 S1 trapped-liquid relief supervision (Combustion RC-04 proposal, LEAD 2026-10-13): with the MV closed the segment sits at P_tank
// + the S1 crack (0.03-0.07 MPa). P_feed - P_tank - zero > 2.0 bar for 1 s = S1 suspected failed (trapped liquid warming toward the
// isochore). Stand: relight lockout (crew vents remotely); flight: flag and log, the relight proceeds (the MV opening at E0 relieves
// the segment). Two 170BG at TEB 2.55 bar make the raw difference uncertain by +/-5.1 bar (RSS 3.6), so the zero is captured in situ
// with no flow: PREPRESS (MV OPEN, pintle seated) and COAST 0.2-0.4 s after entry (MV just closed, segment still at P_tank).
constexpr float kS1DpMax_Pa = 2.0e5f;              // [COMB/LEAD 2026-10-13]
constexpr float kS1Time_s = 1.0f;                  // [COMB/LEAD 2026-10-13]
constexpr float kS1ZeroMax_Pa = 5.1e5f;            // [DERIVED 2 x TEB 2.55 bar] a larger zero = transducer fault (not accepted)
constexpr int kS1ZeroN = 20;                       // [DESIGN] samples per zero block (1 kHz, filtered pressures)
constexpr float kS1ZeroMvOpen_s = 0.050f;          // [DESIGN] PREPRESS: OPEN switch made this long before sampling
constexpr float kS1CoastZeroFrom_s = 0.20f;        // [DESIGN] COAST zero window start (from COAST entry) ...
constexpr float kS1CoastZeroTo_s = 0.40f;          // [DESIGN] ... and end
constexpr bool kS1LockoutStand = true;             // [LEAD 2026-10-13] stand: S1 fault -> relight lockout
constexpr bool kS1LockoutFlight = false;           // [LEAD 2026-10-13] flight: flag and log only, the relight proceeds
// v2.8.1 over-thrust (LEAD 2026-10-13 ADOPTED on GNC m2_fc_thrust v1.1, gnc_v3.1_staging.json 695a069e8fc8dc53): the FC sends its
// first-order (tau 20 ms) accelerometer thrust estimate in FC_THRUST at kFcThrustRate_Hz; the frame's valid flag is set by the FC only
// when airborne, engine lit and drogue released. ECU rule: flight mode, state RUN, kOverThrustFrames CONSECUTIVE fresh frames with the
// valid flag above kOverThrust_N -> OVER_THRUST (3 frames = a 20 ms span at 100 Hz, GNC's rule; a frame at or below the threshold, an
// invalid frame, a gap above kFcThrustStale_s or leaving RUN restarts the count). v2.8.1: the check runs whether or not the Pc channel
// is valid (v2.8: Pc lost only) - it also covers an in-range but wrong Pc reading in closed loop (sense-line blockage, zero shift),
// which the Pc-based over-pressure checks cannot see; GNC: 0/1000 healthy false aborts at >= 610 N (SIM). Basis 500 N x (Cd 0.8/0.7 =
// 1.143) x 1.10 = 628 N -> 650 N (~32.1 bar abs equivalent). Blind to throat blockage (thrust falls while Pc rises). Stale or invalid
// estimate: no check (flag only: log seq2_flags b4 clear, fc_thr_dN 0xFFFF).
constexpr float kOverThrust_N = 650.0f;            // [LEAD 2026-10-13 ADOPTED]
constexpr int kOverThrustFrames = 3;               // [LEAD 2026-10-13 ADOPTED] consecutive frames above the threshold
constexpr float kFcThrustRate_Hz = 100.0f;         // [GNC m2_fc_thrust v1.1 / LEAD] FC_THRUST frame rate (interface requirement)
constexpr float kOverThrustTime_s = 0.020f;        // [LEAD 2026-10-13] hold span of the frame rule at kFcThrustRate_Hz (documentation;
                                                   //   the ECU counts frames; calc/over_thrust_v2.py reads it)
static_assert((kOverThrustFrames - 1) / kFcThrustRate_Hz > kOverThrustTime_s - 1e-4f && (kOverThrustFrames - 1) / kFcThrustRate_Hz < kOverThrustTime_s + 1e-4f,
              "frame count and hold span disagree at the FC_THRUST rate");
constexpr float kFcThrustStale_s = 0.050f;         // [GNC decision 2026-10-13] older estimate = not fresh (5 frame periods at 100 Hz)
// Normal shutdown (RC-01 abort matrix): pintle first, NC valve after the seat is confirmed or the timeout, whichever first. Every
// ABORT de-energises the NC valve at once (enter(ABORT)) with the pintle commanded closed in parallel.
constexpr float kPintleSeatConfirm_m = 0.05e-3f;   // [DESIGN] encoder lift at or below this ...
constexpr int kSeatConfirmN = 5;                   // [DESIGN] ... for 5 consecutive ticks = seated
// v2.8.2 (GNC REV-GNC-1 RG-08): pintle-position anomaly in COAST. With the NC valve closed the valve-to-seat segment can only lose its
// liquid through the pintle seat; a needle off the seat lets it flash into the vented chamber while P_feed stays near P_sat (the pressure
// rule cannot see saturated vapour: RG-01). Encoder invalid on any COAST tick -> UNKNOWN; encoder lift above kCoastPintleOpen_m for
// kCoastPintleOpenN consecutive COAST ticks -> UNPRIMED. Both latch (RAM) until the next confirmed light (RUN entry) or DISARM in SAFE
// and force the prep path; the path and TLM_RELIGHT use the same latches. Values to be set at B-PNT-1 (encoder noise, zero drift over
// the coast soak-back, needle bounce at the drogue shock).
constexpr float kCoastPintleOpen_m = 2.0f * kPintleSeatConfirm_m;   // [DESIGN] 0.10 mm: 2 x the seat-confirm lift (encoder noise margin)
constexpr int kCoastPintleOpenN = 20;              // [DESIGN] 20 consecutive 1 ms ticks (rejects a shock bounce of a few ms)
static_assert(kCoastPintleOpen_m < kPintleStallErr_m, "the coast anomaly must flag below the stall-monitor error (which aborts)");
constexpr float kMvSeatTimeout_s = 0.30f;          // [COMB v2.4 / LEAD 2026-10-13; v2.7-v2.8 draft 0.25 DESIGN] NC valve unlatched regardless
                                                   //   this long after SHUTDOWN entry (fault PINTLE if the encoder was valid). A planned
                                                   //   cut-off (MECO, landing cut = Cmd::SHUTDOWN) never calls the abort path: only a
                                                   //   fault monitor (over-pressure, pintle stall / rail loss, ARM chain) or an FC ABORT /
                                                   //   DISARM does (test_v28 group 16). An abort with the 30 ms MV-P leaves the segment
                                                   //   about 50 % vapour (COMB v2.4), the pintle-first shutdown keeps it liquid
static_assert(kMvSeatTimeout_s >= 1.4f * kPintleCloseSlow_s, "seat timeout too close to the slowest powered closing");
static_assert(kMvSeatTimeout_s < kShutdownTimeout_s, "the valve must be unlatched before SHUTDOWN can time out");
// No automatic in-flight relight retry (LEAD 2026-10-13): an abort from IGNITION, RUN or SHUTDOWN after a lit burn in this power
// cycle or on a relight (start >= 2) sets the relight lockout: ARM, IGNITE and RELIGHT are refused (RELIGHT_LOCKOUT) until a keyed
// CLEAR_LOCKOUT in SAFE (ground). The HAL keeps it non-volatile (NvJamRecord flags b1) so an ECU reset in flight cannot clear it.
// A first-start no-light (nothing lit since power-up) keeps the ground rule: retry after kRetryVentWait_s.
constexpr uint16_t kClearLockoutKey = 0x10C7;      // [DESIGN] CLEAR_LOCKOUT argument, accepted in SAFE only
// Pintle rail loss (LEAD 2026-10-13: an LTC4365 OV-disconnect trip reaches the ECU and is handled as PINTLE_FAULT -> ABORT). Two
// paths: hardware (LTC4365 /FAULT low gates the MV holding-magnet driver off, independent of this code) and firmware (rail sensed
// on the servo side of the disconnect, ADC2 CH1).
constexpr float kPrailLost_V = 5.5f;               // [DESIGN] servo-side rail below this = lost (HV69 rated 6.0-8.4 V (retailer
                                                   //   copies of MKS data); setpoint 7.49 V, UV of the LTC4365 set at ~5.0 V)
constexpr float kPrailLostTime_s = 0.002f;         // [DESIGN] persistence (2 ADC frames)
constexpr float kPrailSettle_s = 0.060f;           // [DESIGN] ignored this long after the ARM bus comes on: LTC4365 recovery delay
                                                   //   <= 49 ms (DS LTC4365 rev B, 36 ms typ; a start-up delay of the same kind is
                                                   //   ASSUMED) + TPS552882 soft start <= 5 ms (DS)
// Pc-sensor loss in RUN: in flight the burn continues open loop on the map (fault OPEN_LOOP; the landing burn is not thrown away);
// on the test stand (v2.8: stand mode = strap AND finite load cell, latched at ARM) it aborts (PC_SENSOR).
constexpr float kPcSensorLossStand_s = 0.005f;     // [DESIGN] persistence of the stand abort

// ---------------------------------------------------------------- TVC supply fault mode FM-PWR-01 (v2.3, LEAD 2026-10-12)
// Predicted servo plug voltage with both TVC servos at stall (supply.h, calc/tvc_supply_budget_v1.py). ARM rule (LEAD):
// predicted >= V_val (lowest plug voltage GNC validates for n 4.8) AND rest voltage >= kBattArmMin_V. Pad (no start yet):
// ARM refused / ARMED-PREPRESS aborted with Abort::TVC_SUPPLY. In flight: flag only (TLM_GIMBAL b3, log flags b14).
constexpr float kTvcSupplyMin_V = 6.6f;             // [LEAD 2026-10-12, V_val] GNC n 4.8 6-DOF MC: P(landing) 0.982 at a 6.6 V
                                                    //   plug with sag modelled, no loss down to 6.0 V (v2.3 basis was 7.6 V)
constexpr float kTvcSupplyHyst_V = 0.10f;           // [DESIGN] flag clears above min + hysteresis ...
constexpr float kTvcSupplyTime_s = 0.100f;          // [DESIGN] ... set after 100 ms below min
constexpr float kTvcSupplyClearTime_s = 0.500f;     // [DESIGN] ... clear after 500 ms above
constexpr float kTvcServoDesign_A = 9.44f;          // [DERIVED] SB-2292SG stall current at 7.6 V (DATASHEET 7.5 A @ 6.0 V,
                                                    //   9.2 A @ 7.4 V, linear)
constexpr float kAuxDesign_A = 1.0f;                // [ASSUMED] other loads in the landing burn (roll RCS adds up to 2.8 A)
constexpr float kRSrcCal_ohm = 0.015f;              // [ASSUMED, LEAD basis] pack + source path; replace with bench B-PWR-1
constexpr float kRBranchEqCal_ohm = 0.020f;         // [ASSUMED, LEAD basis] per-servo equivalent branch (2 x shared TVC path +
                                                    //   own branch); replace with bench B-PWR-2 (v2.2 drawn ~77, v2.3 ~37 mOhm typ)
constexpr float kRsrcWin_s = 0.50f;                 // [DESIGN] in-situ estimator forgetting time
constexpr float kRsrcMinVar_A2 = 1.0f;              // [DESIGN] excitation: current variance over the window (1 A rms)
constexpr float kRsrcMin_ohm = 0.002f;              // [DESIGN] physical bounds for an accepted estimate
constexpr float kRsrcMax_ohm = 0.200f;
constexpr float kRsrcAvg_s = 1.0f;                  // [DESIGN] averaging of accepted estimates
constexpr float kSupplyVocFc_Hz = 3.0f;             // [DESIGN] load-compensated pack voltage filter
// v2.3: F401 (TVC branch fuse) deleted to cut the shared path; hard shorts are cleared by F101 25 A. Firmware e-fuse before
// the first start: sustained battery current above kEfuse_A drops the TVC power (SAFE) or aborts (ARMED/PREPRESS).
constexpr float kEfuse_A = 22.0f;                   // [DESIGN] > both TVC servos stalled (2 x 9.44 A) + other loads
constexpr float kEfuseTime_s = 1.0f;                // [DESIGN] AWG22 at 20 A heats ~18 K/s adiabatic: 1 s costs < 20 K

// ---------------------------------------------------------------- tank heater permit (v2.3, LEAD 2026-10-12 condition (b))
// GSE heater contactor coil loop returns through the ECU interlock (J616 HTR_ILK). Hardware cut, independent of this code:
// ARM plug present OR ARM bus on OR watchdog not OK -> interlock open. Firmware layer below: permit only in SAFE.
constexpr float kHeaterCutPtank_Pa = 58.0e5f;       // [DESIGN] gauge = 59.0 bar abs = N2O saturation at 27.0 C (CoolProp, as
                                                    //   combustion.json: 56.5 bar a @ 25 C, 63.1 @ 30 C); GSE thermostat is primary
constexpr bool kTankOverPAbortPadOnly = false;      // [LEAD conditional] true once Mechanical confirms a passive tank relief
                                                    //   sized for heater runaway and fire (condition (a)); (b) = this permit
constexpr float kPcSensorMin_V = 0.25f;            // [DESIGN] ratiometric 0.5-4.5 V: outside 0.25..4.75 = fault
constexpr float kPcSensorMax_V = 4.75f;             //          4.75 V = 74.4 bar g with the 0-70 bar g (070BG) transducer
                                                    // v2.6 OI-6: a HIGH over-range during IGNITION aborts as HARD_START (PC_OVERP +
                                                    //   PC_SENSOR bits): the ~0.3 m sense line (zeta < 0.03) rings a fast chamber
                                                    //   rise above the range (SIL: 39 bar in the chamber -> > 73 bar g at the
                                                    //   transducer), so a high reading is treated as real pressure

// ---------------------------------------------------------------- Pc transducer scaling (HAL; v2.6 xdcr:: in sensor_scale.h)
constexpr float kPcXdcrFs_Pa = 70.0e5f;             // [DS TE M3200 08/2018 range code 070B + G] M3234-000005-070BG, 0-70 bar g.
                                                    //  v2.6 OI-6 closure: REQUIREMENTS rev 2 ENG-09 "chamber Pc transducer range
                                                    //  >= 70 bar" -> 070BG baseline (v2.2-v2.5: 01KPG 0-1000 psig = 68.95 bar g,
                                                    //  1.5 % short of the literal requirement). 01KPG stays the alternate via
                                                    //  xdcr::XdcrCal::fs_Pa = 68.9476e5 (same chain; calc/pc_transducer_v2.py).
                                                    //  Reads MEOP 45 bar, the 67.5 bar proof and the 63.1 bar blocked-nozzle bound
constexpr float kPcXdcrZeroFrac = 0.10f;            // [DS] output = Vexc x (0.10 + 0.80 p/FS), ratiometric to +5V_SNS
constexpr float kPcXdcrSpanFrac = 0.80f;
// v2.6 OI-6: ADC chain constants for xdcr:: (sensor_scale.h). The HAL averages 4 ADS131M04 frames (4 kSPS) per 1 ms tick.
constexpr float kAdcVref_V = 1.2f;                  // [DS TI SBAS890D] ADS131M04 internal reference; gain 1 -> FS +/-1.2 V
constexpr float kAdcCodeFs = 8388608.0f;            // [DS] 24-bit two's complement: +FS = 2^23 counts
constexpr float kXdcrDivRtop_ohm = 12.7e3f;         // [DESIGN] R610/R620/R630 0.1 % (hardware/kicad_gen/ecu_design.py)
constexpr float kXdcrDivRbot_ohm = 4.02e3f;         // [DESIGN] R611/R621/R631 0.1 %
constexpr float kAdcZin_ohm = 330.0e3f;             // [DS SBAS890D 8.3.3 and Features: 330 kOhm at gain 1 (fMOD 4.096 MHz); the
                                                    //  Electrical Characteristics table says 300 kOhm - CONFLICT kept: divider
                                                    //  error -0.92 % vs -1.01 %; the B-PC-1 end-to-end calibration absorbs it]
constexpr float kXdcrExcNom_V = 5.0f;               // [DS LT1761-5 nominal] +5V_SNS excitation
constexpr float kXdcrExcMin_V = 4.75f;              // [DS M3200] supply 5 +/- 0.25 V; outside -> sensor not trusted (HAL reads
constexpr float kXdcrExcMax_V = 5.25f;              //   V5SNS_SENSE, Teensy A5, /2)

}  // namespace cfg
}  // namespace ecu
