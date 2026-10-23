// [v2.13 2026-10-21: Abort::SEAT_TC (32), refuse JFWD_USED (17) / SEAT_TC (18) / SEAT_STEP (19), f3::SEAT_STEP (b7); Inputs::tc_bore_K = the C1 seat TC (TC4)]
// [v2.12 2026-10-21: f3:: flags (TB-state, C1 seat compensation, flight J-FWD flag, torch re-zero rejected), Outputs f3_flags / pc_seat_comp_Pa;
//  Inputs::tc_bore_K re-assigned to the C1 seat TC (REV-ELEC-3 R3-01 option (b), LEAD 2026-10-21T11:25Z working basis)]
// [v2.11 2026-10-13, LEAD CHANGELOG 203: refuse UNPURGED (16), ovr:: flags, LightSpikeRec.abovefs, Outputs pc_overrange / pc_above_fs / ovr_flags (ovp_long_rc removed 2026-10-20, LEAD 216 (3))]
// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175/181/186: Abort TORCH_LOST / TANK_COLD, refuse SAFING_HOLD / TANK_COLD, f2 flags, Outputs pc_commit_valid / pintle_meas; Cmd::DROGUE + R2 hold outputs (186 (2)); full list in 06-electronics/REPORT-v2.10-HANDBACK.md] ARGOS engine ECU - shared types (v2.9, 2026-10-13: Abort::BLEED_FAULT, refuse::NO_HBLEED / PURGE_PATH, Inputs pmid_hi / pmid_valid
// (head-end bleed P_mid comparator via the MV switch ladder), Outputs hbleed[2] / hbleed_flags / hbleed_bit / hbleed_event (hb::), light-
// detection diagnostics ign_det / ign_ref_Pa / ign_rise_Pa (det::, LEAD-adopted relative rule), A3 relative flame-out ratio and A7 map
// criterion (flame_ratio, pc_map_Pa, a7_phase / a7_flag / a7_event, a7::), coast re-zero flags. v2.8.2: Outputs coast_pintle / coast_pintle_event
// (GNC RG-08). v2.8: relight with the NC valve opened at E0 and the lift at E1 (LEAD Finding A),
// ignition window W from the lift command with the stand rules R1-R4 / flight 0.65 s (two state TCs MSS-1/MSS-2), S1 relief monitor,
// provisional over-thrust abort from the FC thrust estimate (FC_THRUST frame), explicit stand/flight mode strap, case over-temperature
// armed with the MV open; v2.7: torch-flame gate (P_torch), relight lockout, pintle-rail sense (LTC4365 OV disconnect), seat-confirmed
// shutdown; v2.6: pintle stall/tracking monitor, jam events, MAINT_JAM inhibit). Platform independent: no Arduino headers here.
#pragma once
#include <cstdint>
#include <limits>

namespace ecu {

enum class State : uint8_t {
  SAFE = 0, ARMED = 1, PREPRESS = 2, IGNITION = 3, RUN = 4, SHUTDOWN = 5, PURGE = 6, COAST = 7, ABORT = 8
};
const char* stateName(State s);

// Commands carried by CAN frame 0x030 CMD_STATE (and 0x010 ABORT)
enum class Cmd : uint8_t {
  NOP = 0, ARM = 1, DISARM = 2, PREPRESS = 3, IGNITE = 4, SHUTDOWN = 5, PURGE = 6, SAFE = 7, RELIGHT = 8,
  SET_LINK_POLICY = 9,
  TVC_TEST_ENABLE = 10,    // SAFE only: arg 0 off, 1 bench TVC through the flight shaping, 2 (v2.6) shaping low-pass and notch
                           //   bypassed for the B-TVC-1 frequency response (slew and angle limits stay)
  VENT = 11,
  SET_GIMBAL_NOTCH = 12,   // v2.4 ENG-07d: SAFE only; arg b15 = 0: centre for BOTH axes in 0.1 Hz (0 = disable both; each axis
                           //   keeps its own Q/depth); v2.6 arg b15 = 1: per axis, b14 axis (0 alpha, 1 beta), b0-b13 centre in
                           //   0.1 Hz (0 = disable that axis)
  CLEAR_JAM = 13,          // v2.6: SAFE only; arg must equal cfg::kClearJamKey ("bearing A replaced"); the HAL then clears the
                           //   non-volatile pintle-jam record (MECH/LEAD rule: any recorded jam -> bearing A replaced before flight)
  SET_GIMBAL_NOTCH_QD = 14,  // v2.6 per-axis notch Q and depth, SAFE only: arg b15 axis (0 alpha, 1 beta), b8-b14 attenuation at f0
                             //   in dB (depth = -value), b0-b7 Q x 20; invalid values ignored (ranges in config.h)
  CLEAR_LOCKOUT = 15,      // v2.7 (LEAD 2026-10-13, no in-flight retry): SAFE only, arg must equal cfg::kClearLockoutKey;
                           //   clears the relight lockout set by an in-flight no-light / hard start / flameout (ground action)
  SET_TORCH_GATE = 16,     // v2.7 (RC-01): SAFE only. arg == cfg::kTorchTimingOnlyKey and a test stand detected (finite load-cell
                           //   reading): GROUND timing-only start allowed (torch-flame gate bypassed on the first start of the
                           //   arming session only, reduced ignition lift cfg::kTimingOnlyLift_m);
                           //   any other arg: gate enforced (default). Cleared by DISARM in SAFE and at power-up
  DROGUE = 17,             // v2.10 (LEAD CHANGELOG 186 (2), R2 command hold): the FC's drogue state, any state: arg 1 = attached (sent at
                           //   the deployment), 0 = released (sent at the R2 release); other values ignored. Reset to 'not attached' at
                           //   power-up and at an accepted ARM. Echo: TLM_RELIGHT d6 b6 (tlmr6::DROGUE). Effect: flight RUN only (config.h
                           //   'R2 command hold')
  ABORT = 0xAB
};

// Abort / inhibit causes (first cause latched; all causes OR-ed in fault bits)
enum class Abort : uint8_t {
  NONE = 0, CMD = 1, HARD_START = 2, NO_IGNITION = 3, FLAMEOUT = 4, PC_BAND = 5, OVER_TEMP = 6,
  TANK_OVERPRESSURE = 7, GIMBAL_FAULT = 8, PINTLE_FAULT = 9, LINK_LOST = 10, PREPRESS_FAIL = 11,
  PC_SENSOR = 12, BATT_LOW = 13, MV_FAULT = 14, ARM_LOST = 15, WATCHDOG = 16,
  PC_OVERPRESSURE = 17,   // v2.2: firmware Pc > kPcOverPressureAbs_Pa outside the ignition phase
  HW_OVERPRESSURE = 18,   // v2.2: hardware comparator/latch (OVP_OK low): ARM bus already off in hardware
  TVC_SUPPLY = 19,        // v2.3 FM-PWR-01: predicted both-stall servo plug voltage below kTvcSupplyMin_V (pad only)
  OVERCURRENT = 20,       // v2.3: firmware e-fuse (battery current > kEfuse_A for kEfuseTime_s) before the first start
  MAINT_JAM = 21,         // v2.6: ARM refused - a pintle jam is recorded (non-volatile) and not yet cleared by CLEAR_JAM
  TORCH_FAULT = 22,       // v2.7 (RC-01): no torch flame (P_torch) by kTorchConfirmBy_s: abort BEFORE the pintle step (fault
                          //   bit NO_IGNITION: the 16-bit fault word has no spare bit)
  RELIGHT_LOCKOUT = 23,   // v2.7 (LEAD 2026-10-13): ARM / IGNITE / RELIGHT refused after an abort from IGNITION/RUN/SHUTDOWN
                          //   following a lit burn this power cycle or on a relight, until CLEAR_LOCKOUT (ground; non-volatile)
  OVER_THRUST = 24,       // v2.8 (LEAD 2026-10-13, PROVISIONAL 650 N / 20 ms): flight, RUN, Pc sensor lost: the FC accelerometer
                          //   thrust estimate (FC_THRUST frame) fresh, valid and above cfg::kOverThrust_N (fault bit PC_OVERP)
  MODE_MISMATCH = 25,     // v2.8 (LEAD 2026-10-13): ARM refused - mode strap invalid, or strap and load-cell reading disagree
  BAY_HOT = 26,           // v2.8 (LEAD 2026-10-13 launch constraint): ARM refused - bay temperature above cfg::kBayArmMax_K or no
                          //   valid reading (SB-2292SG rating in flight)
  TANK_HOT = 27,          // v2.8 final (LEAD 2026-10-13, ENG-12 15-24 C; COMB v2.4 MEOP 45 bar kept, worst band corner 44.33 bar at
                          //   24 C): ARM refused - tank temperature (max of the valid tank-wall DS18B20 and Tsat(P_tank)) above
                          //   cfg::kTankIgnMax_K, or no valid tank temperature at all
  BLEED_FAULT = 28,       // v2.9 (LEAD 2026-10-13 head-end bleed provision): pad BIT failed; STAND: closure not confirmed, purge path
                          //   not proven, leak with both valves commanded closed (fault bit MV: no spare bit). v2.10 (LEAD RE-05): in
                          //   FLIGHT an unconfirmed closure is a FLAG to the FC (Outputs::bleed_fault), the relight proceeds
  TORCH_LOST = 29,         // v2.10 FMEA FA-1 (b) (LEAD CHANGELOG 164 (8)): torch confirmed (E1 2oo2) but BOTH flame sensors (P_torch,
                          //   photodiode) read no flame for cfg::kTorchLossTime_s before E2: pintle and NC valve close (fault NO_IGNITION)
  TANK_COLD = 30,         // v2.10 RE-17: tank below cfg::kTankIgnMin_K (15 C) or no valid tank temperature at ARM (pad first start,
                          //   stand starts; a flight relight is flagged only, the tank cools in every burn)
  CASE_WARM_STAND = 31,   // v2.11 (LEAD 2026-10-20 stand T0 rule, ADOPTED): ARM refused in stand mode with TC1 or TC2 above
                          //   cfg::kCaseStandArmMax_K (24 C) - a backstop; the founder pre-fire checklist (stand ambient <= 24 C) is the control
  SEAT_TC = 32            // v2.13 (LEAD 264 (2) A1 pad rule, REV-ELEC-4 E4-N02; LEAD 16:27Z: ARM-REFUSAL ONLY - the state stays SAFE, so
                          //   it never rides an EVENT STATE (5-bit cause field 0-31, guarded in can::encodeStateEvent); carried in the
                          //   uint8 log abort_cause like every ARM-refusal cause. A STATE-event cause of 31 means CASE_WARM_STAND only
                          //   while can::g_state_cause_overflow is 0; the log byte abort_cause (uint8) is the authority): FLIGHT mode
                          //   with EngineEcu::seat_arm_rule (A1 build value
                          //   true): ARM refused unless the C1 seat coefficient is loaded (setPcSeatCoef != 0) AND the C1 seat TC (TC4) is
                          //   valid and in range at ARM (stand mode: no rule)
};
const char* abortName(Abort a);

namespace fault {  // bit positions in the 16-bit fault word
constexpr uint16_t HARD_START = 1u << 0, NO_IGNITION = 1u << 1, FLAMEOUT = 1u << 2, PC_BAND = 1u << 3,
                   OVER_TEMP = 1u << 4, TANK_OVERP = 1u << 5, GIMBAL = 1u << 6, PINTLE = 1u << 7,
                   LINK_DEGRADED = 1u << 8, LINK_LOST = 1u << 9, PC_SENSOR = 1u << 10, BATT_LOW = 1u << 11,
                   MV = 1u << 12, ARM_PLUG = 1u << 13, OPEN_LOOP = 1u << 14, ENCODER = 1u << 15;
constexpr uint16_t PC_OVERP = HARD_START;   // v2.2: bit 0 = any chamber over-pressure (hard start, firmware or hardware trip)
}

enum class LinkPolicy : uint8_t { SHUTDOWN = 0, HOLD_THEN_SHUTDOWN = 1 };

// v2.6 pintle jam kinds (LEAD 2026-10-12: stall detection = position error plus current or time; every jam is logged because a
// jam means bearing A must be replaced before the next flight)
namespace jam {
constexpr uint8_t NONE = 0,
                  STALL_TIME = 1,           // |cmd - lift| > kPintleStallErr_m with no 20 um progress mark for kPintleStallTime_s
                  STALL_CURRENT = 2,        // same, rail current > kPintleStallI_A for kPintleStallTimeI_s (current sense fitted)
                  TRACK_TIMEOUT = 3,        // error above kPintleStallErr_m for kPintleTrackTime_s while creeping
                  BLEED_NOT_CONFIRMED = 4,  // PREPRESS: encoder below kBleedConfirm_m at the bleed check (needle did not lift)
                  NOT_CLOSED = 5,           // SAFE: lift above kPintleStallErr_m kPintleUnpoweredClose_s after power removal
                                            //   (the spring did not close the needle by back-driving the unpowered servo)
                  RUNAWAY = 6;              // lift moved >= kPintleProgMin_m AWAY from the command in the no-progress interval
                                            //   (servo runaway / wrong direction); recorded like a jam (inspection)
// kinds 4-6 are suspected jams: recorded and inhibiting ARM like 1-3 (conservative); whether they invoke the bearing-A
// replacement rule is Mechanical's maintenance call (TO-AGREE)
}
struct PintleJamEvent {           // last jam event of this power cycle (the HAL persists it: protocol.h nvJamEncode)
  double t_s = 0;
  uint8_t state = 0, kind = jam::NONE;
  float cmd_m = 0, meas_m = 0;    // lift command and encoder lift at detection
  float i_A = -1.0f;              // rail current at detection (-1 = no current sense)
  float noprog_s = 0;             // time without a progress mark at detection
  uint16_t count = 0;             // jam events this power cycle
};

// Everything the ECU reads each 1 ms tick (already scaled to SI by the HAL)
struct Inputs {
  double t_s = 0;                 // monotonic time
  float pc_Pa = 0;                // chamber pressure, GAUGE, 1 kHz decimated (auto-zero applied by core)
  float pc_raw_V = 2.5f;          // transducer output voltage (fault detection)
  float pfeed_Pa = 0;             // feed GAUGE pressure (v2.8: J602 170BG at the FS-01 MV-outlet block, next to MSS-2, MECH 2026-10-13)
  bool pfeed_valid = true;        // v2.8: HAL range/excitation check (invalid -> stand relight refused (R4), S1 not evaluated)
  float ptank_Pa = 0;             // tank GAUGE pressure
  bool ptank_valid = true;        // v2.8: HAL range/excitation check (invalid -> S1 not evaluated, ignition-lift table at its minimum)
  float tc_K[4] = {293.15f, 293.15f, 293.15f, 293.15f};  // v2.8 (MECH 2026-10-13): [0] case az 90, [1] case az 270 (both bonded on
                                  //   the case OD 12.6-17.6 mm below the injector face), [2] nozzle holder, [3] pintle-servo bracket
  bool tc_valid[4] = {true, true, true, true};
  float gimbal_meas_rad[2] = {0, 0};  // encoder (engine angle)
  bool gimbal_meas_valid[2] = {true, true};
  float pintle_meas_m = 0;        // lift from crank encoder via linkage::crankToLift (0 when below contact)
  bool pintle_meas_valid = true;
  bool mv_open_sw = false, mv_closed_sw = true;
  float vbat_V = 8.2f;
  float ibat_A = 0.4f;            // v2.3: battery current (A2, INA181A1 x20 on 2 mOhm), positive = discharge
  bool arm_plug_present = false;  // sensed upstream of the ARM high-side switch
  bool arm_bus_on = false;        // sensed downstream (proves the switch closed)
  bool ovp_ok = true;             // v2.2: hardware over-pressure latch U331 Q on pin 29 (true = not tripped)
  float pintle_i_A = 0.0f;        // v2.6: pintle rail current [A] (INA181 on the TPS552882 sense resistor, ADC2 CH2; HAL averages
  bool pintle_i_valid = false;    //   over one 3 ms servo frame); false = no current sense -> the stall monitor uses the time path
  // v2.7 (2026-10-13 review fold-in): second ADS131M04 (ADC2) channels
  float ptorch_Pa = 0.0f;         // torch chamber GAUGE pressure (M3200 070BG on a standoff, ADC2 CH0): torch-flame confirmation
  bool ptorch_valid = true;       //   (RC-01 hard gate for the pintle step); invalid = not confirmed (fail-safe: TORCH_FAULT)
  float prail_V = 7.49f;          // pintle servo rail at the servo side of the LTC4365 OV disconnect (ADC2 CH1, /10.1): a drop
  bool prail_valid = true;        //   while the servo should be powered = OV trip or regulator failure -> PINTLE_FAULT abort;
                                  //   invalid (ADC2 fault) = not evaluated (the LTC4365 /FAULT -> MV-latch hardware gate remains)
  float preg_V = 7.49f;           // TPS552882 output before the disconnect (ADC2 CH3): diagnostic only (fail-high vs false trip)
  float tc_bore_K = 293.15f;      // v2.12: C1 SEAT thermocouple (MAX31856 #4, re-assigned from the v2.7 bore-top / manifold TC; REV-ELEC-3
                                  //   R3-01 option (b)): head-top surface at the C1 boss (Mechanical c1_seat_v352 sensor node r 25.875 mm,
                                  //   z = zt); input of the Pc seat compensation (EngineEcu::setPcSeatCoef). CF-3/T1 C7 bore-top -> stand DAQ
  bool tc_bore_valid = false;     //   not fitted / open / fault = invalid (compensation OFF at ARM, or held after ARM; f3:: flags)
                                  //   v2.13 HAL contract: tc_bore_K HOLDS the last MAX31856 conversion between conversions (a change of the
                                  //   value = a new conversion for the TC4 step check); valid false only on a fault. MAX31856 #4 (U904)
                                  //   set to the 50 Hz notch (CR0 bit 0 = 1; DK and AR mains 50 Hz), auto-conversion (CMODE = 1), AVGSEL
                                  //   <= cfg::kPcSeatAvgselMax (2) samples: period <= cfg::kPcSeatConvMax_s 0.130 s [DATASHEET 19-7534 Rev 0
                                  //   tCONV 50 Hz 98 / 110 ms + 20 ms per extra sample; TO-VERIFY on the PDF]. A longer period needs
                                  //   cfg::kPcSeatStepMax_K re-derived (config.h). The bench measures the period (bench plan B-TC-1)
  // v2.8 state thermocouples of the valve-to-seat segment (LEAD 2026-10-13, stand rules R3/R4; flight: telemetry only). Type T,
  // MI 1/16 in, SS-100-1-2BT into 1/8 NPT. The HAL reports not fitted / open / fault as invalid.
  float tc_mss1_K = 293.15f;      // MSS-1: inlet-block TC (MAX31856 #5), tip up the riser (sheath >= 200 mm, MECH)
  bool tc_mss1_valid = true;
  float tc_mss2_K = 293.15f;      // MSS-2: NC-valve-outlet TC (MAX31856 #6) on the FS-01 MV-outlet block
  bool tc_mss2_valid = true;
  float bay_K = 293.15f;          // v2.8 (LEAD 2026-10-13): bay temperature at the TVC servo bracket (DS18B20 #3 on the existing 1-Wire
  bool bay_valid = true;          //   bus, 12-bit, 1 Hz). HAL: not found / CRC error / older than 2 s = invalid. ARM inhibit + pad first start
  uint8_t mode_strap = 1;         // v2.8 (LEAD 2026-10-13): 2-pin coded harness strap decoded by the HAL: 1 = FLIGHT (MODE_A high,
                                  //   MODE_B low), 2 = STAND (A low, B high), 0 = invalid (both high = open harness, both low = short)
  bool maint_pintle_jam = false;  // v2.6: non-volatile pintle-jam record pending (HAL reads it at boot; ARM refused, MAINT_JAM)
  bool nv_relight_lockout = false;  // v2.7: non-volatile relight lockout pending (HAL: NvJamRecord flags b1 OR b2 at boot, or
                                    //   CORRUPT; cleared by the HAL on Outputs::relight_lockout_clear)
  bool nv_safing_hold = false;    // v2.10 (LEAD 172 (1)): NvJamRecord b4 at boot (or CORRUPT) - a ground no-light safing hold was open;
                                  //   the hold restarts at boot (elapsed time unknown). The HAL clears it on Outputs::relight_lockout_clear
  bool nv_seg_vapour = false;     // v2.8 final (COMB v2.4 / LEAD 2026-10-13): NvJamRecord b3 at boot (or CORRUPT) - an abort left vapour in
                                  //   the valve-to-seat segment; the next start is a vapour-segment start (HAL clears it on seg_vapour_clear)
  float ttank_wall_K[2] = {293.15f, 293.15f};   // v2.8 final (LEAD 2026-10-13 tank interlock): tank-wall DS18B20 #1/#2 on J608 (1-Wire bus
  bool ttank_wall_valid[2] = {true, true};      //   shared with the bay sensor, 12-bit, 1 Hz). HAL: not found / CRC error / older than 2 s = invalid
  float load_cell_N = std::numeric_limits<float>::quiet_NaN();   // test stand only: NaN in flight. v2.7: a FINITE reading identifies
                                  //   the test stand; v2.8: the mode is the strap AND this check (mismatch -> ARM refused)
  // v2.9 head-end bleed P_mid (pressure between V1 and V2): LMV331 comparator (cfg::kHbleedPmidHi_Pa, ~1 bar hysteresis) on one branch
  // of the MV switch resistor ladder (Teensy pin 23 / A9, sensor_scale.h mvLadderDecode). An invalid ladder code (open / short harness)
  // gives pmid_valid = false AND mv_open_sw = mv_closed_sw = false (the existing MV-switch fault paths then apply)
  bool pmid_hi = false;           // P_mid above the comparator threshold
  bool pmid_valid = true;         // ladder code valid (false: P_mid unknown -> path not proven, closure not confirmable)
  // v2.10 RE-19: ladder decoded OPEN+CLOSED (impossible; HAL also reports the code invalid: switches false, pmid_valid false) and the
  // raw ladder ratio V_pin / V_ref (NaN = not reported) for the pad-BIT harness-resistance step
  bool mv_sw_conflict = false;
  float mv_ladder_ratio = std::numeric_limits<float>::quiet_NaN();
  // v2.10 FA-1 flame-light head (photodiode + log transimpedance amplifier, ADC2 CH3 through the divider; CH3 was preg_V, retired):
  // head output [V] referred to the head (HAL scales the divider); photo_valid = ADC status good (the range check is in the core)
  float photo_V = 0.0f;
  bool photo_valid = false;
};
namespace strap { constexpr uint8_t INVALID = 0, FLIGHT = 1, STAND = 2; }

// v2.8 ignition-window rule of a start (Outputs::ign_rule, log v7 ign_rule, EVENT IGN_WINDOW)
namespace rule {
constexpr uint8_t NONE = 0,
                  FIRST = 1,            // R1: first start of the arming session, W 0.40 s flight (pad) / 0.35 s stand (v2.8.1 LEAD fallback (b))
                  STAND_DEFAULT = 2,    // R2: stand relight, W 0.35 s (v2.8.1; v2.8 final 0.50 s)
                  STAND_SUPERHEAT = 3,  // R3: RETIRED in v2.8.1 (LEAD 2026-10-13: no extended stand window); code kept for log decoding
                  FLIGHT_RELIGHT = 5;   // flight relight, W 0.65 s on every relight (state TCs telemetry only)
}
// v2.8 refusal reasons of IGNITE / RELIGHT / PREPRESS reported once per command (Outputs::cmd_refused_event, EVENT CMD_REFUSED)
namespace refuse {
constexpr uint8_t NONE = 0, R4_SENSOR = 1, CASE_HOT = 2, PREPRESS_IN_COAST = 3,
                  BAY_HOT = 4,      // pad first start with the bay above cfg::kBayArmMax_K or no valid bay reading
                  // v2.8: the v2.7 refusals now report too (EVENT CMD_REFUSED, TLM_RELIGHT d6), same rules and counters as v2.7
                  MAX_STARTS = 5,   // starts used up (cfg::kMaxStarts)
                  LOCKOUT = 6,      // relight lockout pending (no automatic in-flight retry; CLEAR_LOCKOUT on the ground)
                  NOTCH = 7,        // ENG-07d notch not enabled on both axes
                  NOT_VENTED = 8,   // |Pc gauge| >= 0.1 bar (COMB OI-12)
                  VENT_WAIT = 9,    // RETIRED v2.10 (LEAD 172 (1): the 5 s retry wait is withdrawn); code reserved, never sent
                  NOT_COAST = 10,   // TLM_RELIGHT: a RELIGHT now would be ignored (not in COAST/PURGE); v2.9: PURGE outside COAST
                  TANK_HOT = 11,    // v2.8 final: tank above cfg::kTankIgnMax_K or no valid tank temperature (pad first start, stand starts)
                  NO_HBLEED = 12,   // v2.9: Cmd::PURGE with the head-end bleed not fitted (EngineEcu::hbleed_fitted)
                  PURGE_PATH = 13,  // v2.9: Cmd::PURGE while a RELIGHT would take the prep path (segment not shown primed, post-abort
                                    //   vapour, coast pintle anomaly): the purge is defined on the direct path only
                  TANK_COLD = 14,   // v2.10 RE-17: tank below cfg::kTankIgnMin_K or no valid tank temperature (pad first start, stand starts)
                  SAFING_HOLD = 15, // v2.10 LEAD 172 (1): CLEAR_LOCKOUT inside the ground no-light safing hold (cfg::kNoLightSafingMin_s)
                  UNPURGED = 16,    // v2.11 LEAD 203 (7): flight, bleed fitted - RELIGHT/IGNITE in COAST with no purge running (the only accepted
                                    //   flight relight is a RELIGHT during PURGE; cfg::kUnpurgedRelightGuard). TLM_RELIGHT d6: relight_block =
                                    //   UNPURGED in COAST when no startBlock() reason applies (READY 0, read as 'PURGE first'; Cmd::PURGE is
                                    //   accepted) and relight_worst_ms includes the PURGE lead (kPurgeRelight_s + gate + W)
                  JFWD_USED = 17,   // v2.13 (LEAD 264 (7) PROVISIONAL, cfg::kJfwdLsRelightInhibit): flight relight (PURGE / RELIGHT / IGNITE,
                                    //   starts >= 1) refused after a flagged light in this arming (f3::JFWD_LS latched): lost-relight outcome
                  SEAT_TC = 18,     // v2.13 (LEAD 264 (2), EngineEcu::seat_arm_rule): flight PAD first start refused - the C1 seat compensation
                                    //   is not active (no seat reference at the ARM latch, f3::SEAT_NOREF) or is held after a TC4 trip (f3::SEAT_STEP)
                  SEAT_STEP = 19;   // v2.13 (REV-ELEC-4 Q2 item 4, lead decision; cfg::kSeatStepRelightInhibit, default false = NOT used):
                                    //   flight relight refused while f3::SEAT_STEP is latched (the alternative to a relight on the held compensation)
}
// v2.11 (LEAD CHANGELOG 203 (1)) Pc over-range / ride-through flags: Outputs::ovr_flags, log v12 ovr_flags
namespace ovr {
constexpr uint8_t OVERRANGE = 1u << 0,     // reading >= cfg::kPcSensorMax_V this tick (non-sticky; PC_VALID 0 while set)
                  ABOVE_FS = 1u << 1,      // reading >= cfg::kPcAboveFs_V this tick (above the transducer full scale; flag only)
                  RIDE_WIN = 1u << 2,      // ride-through window open (CANDIDATE build option, flight relight, lift -> E2 + X)
                  RIDE_TOL = 1u << 3,      // tolerated by the window: filtered Pc above 30 bar past the as-built persistence, or (2026-10-20) an IGNITION HIGH over-range tick below N
                  LONG_RC_RETIRED = 1u << 4,   // v2.11 draft long-RC request: RETIRED 2026-10-20 (LEAD 216 (3) fixed RC); always 0
                  T45 = 1u << 5,           // ride window: raw reading above the 45 bar MEOP this tick (T45 guard counting)
                  RIDE_BUILD = 1u << 6,    // ride-through enabled in this build / configuration (EngineEcu::ride_through)
                  SEAT_RULE_BUILD = 1u << 7;   // v2.13 (LEAD 16:11Z RULING 1 (b)): EngineEcu::seat_arm_rule (A1 flight build 1); also EVENT BUILD b0
}
// v2.12 (REV-ELEC-3 R3-01 / R3-02; LC-TB70 v2 F4 abort set, mechanical.json v2.4 lc_tb70_envelope_v352): Outputs::f3_flags, log v13 f3_flags
namespace f3 {
constexpr uint8_t TB_STATE = 1u << 0,      // latched until the next ARM: a TB-state abort or event in this arming - HW_OVERPRESSURE,
                                           //   PC_OVERPRESSURE, HARD_START, the case / nozzle-holder OVER_TEMP abort (p_otemp_), or a Pc HIGH
                                           //   over-range reading (>= cfg::kPcSensorMax_V = 146.5 bar abs on C1) in a powered state (on the
                                           //   stand it aborts PC_SENSOR / HARD_START). Bench plan v5 F-14: the J-FWD joint counts as used
                  TB_PCS_HIGH = 1u << 1,   // latched: the TB-state includes a Pc HIGH over-range (PC_SENSOR HIGH side; LOW side not in the set)
                  SEAT_COMP = 1u << 2,     // this tick: C1 seat compensation active (coefficient loaded AND seat reference latched at ARM)
                  SEAT_FROZEN = 1u << 3,   // this tick: compensation held at its last value (seat TC invalid / implausible after ARM)
                  SEAT_NOREF = 1u << 4,    // latched until the next ARM: coefficient loaded but no valid seat TC over the ARM window ->
                                           //   compensation OFF for this arming (the v2.11 behaviour, flagged)
                  JFWD_LS = 1u << 5,       // latched until the next ARM: LIGHT_SPIKE raw peak >= cfg::kJfwdLsRawAbs_Pa (1 kHz lower bound of
                                           //   the head event; information, LEAD 258 (3)-(4): the flight J-FWD indication; no action)
                  PT_RZ_REJ = 1u << 6,     // the last torch re-zero (coast block or second re-zero) was rejected (> cfg::kPtorchRezeroMax_Pa)
                  SEAT_STEP = 1u << 7;     // v2.13 (REV-ELEC-4 E4-01 / Q2): latched until the next ARM: a TC4 (C1 seat TC) conversion failed
                                           //   the step check (|T_n - T_n-1| > cfg::kPcSeatStepMax_K) or the rate check (reading more than
                                           //   cfg::kPcSeatRateTrip_K from the slewed compensation temperature, outside the light-window
                                           //   hold) -> the compensation is held at its last good value until the next ARM
}
// v2.9 head-end bleed (LEAD 2026-10-13 A1 provision): Outputs::hbleed_flags bits, hbleed_bit codes, hbleed_event kinds (EVENT HBLEED)
namespace hb {
constexpr uint8_t F_FITTED = 1u << 0,       // provision fitted (EngineEcu::hbleed_fitted)
                  F_PATH = 1u << 1,         // this purge: P_mid has read high with V1 open (path open, P_mid chain alive)
                  F_V1_CLOSED = 1u << 2,    // this start: V1 confirmed closed before the lift
                  F_LEAK = 1u << 3,         // P_mid high with both valves commanded closed (latched until DISARM in SAFE)
                  F_BIT_PASS = 1u << 4,     // pad BIT passed in this arming session
                  F_PATH_FLAG = 1u << 5,    // a purge did not prove the path by cfg::kHbleedPathBy_s (latched until DISARM in SAFE)
                  F_HOLD_TIMEOUT = 1u << 6, // a purge ended without RELIGHT (hold limit; latched until DISARM in SAFE)
                  F_PURGE_ENC = 1u << 7;    // pintle encoder invalid during a purge (flight flag; latched until DISARM in SAFE)
constexpr uint8_t BIT_NONE = 0,             // hbleed_bit: not run; 1..5 = step S0..S4 in progress; BIT_PASS; BIT_FAIL | step (S0..S4)
                  BIT_PASS = 0x0F, BIT_FAIL = 0x10;
constexpr uint8_t EV_NONE = 0, EV_BIT_PASS = 1, EV_BIT_FAIL = 2, EV_PATH_NOT_PROVEN = 3, EV_V1_CLOSED = 4, EV_NOT_CLOSED = 5,
                  EV_LEAK = 6, EV_HOLD_TIMEOUT = 7, EV_PURGE_ENC = 8,
                  EV_FLOW_START = 9,   // v2.10: V2 opened (flow start = command + cfg::kHbleedOpenTime_s)
                  EV_CAP = 10;         // v2.10: both valves commanded open longer than cfg::kHbleedCap_s -> both closed at once
}
// v2.10 purge / closure detail (Outputs::hbleed2, log v11 hb2_flags): per purge, cleared at PURGE entry
namespace hb2 {
constexpr uint8_t FILL = 1u << 0,           // fill step running / done (V1 open, V2 closed)
                  FLOW = 1u << 1,           // flow started (V2 commanded open)
                  FLOW_DONE = 1u << 2,      // V1 close command issued (flow end = command + cfg::kHbleedCloseTime_s)
                  CONFIRMED = 1u << 3,      // closure confirmed (chain proven AND vent AND hold test)
                  NOT_CONFIRMED = 1u << 4,  // closure not confirmed (BLEED_FAULT to the FC; stand abort)
                  R_CHAIN = 1u << 5,        // reason: P_mid chain not proven in the fill step
                  R_VENT = 1u << 6,         // reason: the mid did not vent (P_mid not low) before V2 had to close
                  R_HOLD = 1u << 7;         // reason: P_mid high / invalid in the hold test (V1 not shut) or closure forced (cap/deadline)
}
// v2.10 flags to the FC without a fault-word bit (Outputs::fault2, log v11 fault2, EVENT FLAGS2 0x22 on every change)
namespace f2 {
constexpr uint8_t BLEED_FAULT = 1u << 0,    // closure not confirmed (LEAD RE-05; flight flag, the relight proceeds)
                  BASE_HIGH = 1u << 1,      // light-rule baseline P0 above +check: measured P0 kept (LEAD RE-02)
                  NOT_VENTED = 1u << 2,     // flight RELIGHT with the chamber not shown vented (LEAD RE-07; stand: refusal)
                  CASE_TC_DEGRADED = 1u << 3,   // one case TC invalid, the other in use (LEAD RE-08)
                  LIFT_CLAMP = 1u << 4,     // RE-04 lift clamp active this tick
                  REZERO2 = 1u << 5,        // RE-07 second (pre-PURGE / pre-RELIGHT) coast re-zero applied
                  REZERO2_REJ = 1u << 6,    // RE-07 second re-zero block rejected (span or > 0.30 bar from the pad zero): zero kept
                  TANK_COLD_RELIGHT = 1u << 7;   // RE-17 flight relight accepted with the tank below 15 C or no valid tank temperature
}
// v2.10 FA-1 flame sensing (Outputs::fa1, log v11 fa1_flags)
namespace fa1 {
constexpr uint8_t PHOTO_VALID = 1u << 0, PHOTO_LIT = 1u << 1, PT_LIT = 1u << 2, E1_2OO2 = 1u << 3, SUPERVISING = 1u << 4,
                  BOTH_DARK = 1u << 5,      // both sensors no flame this tick (E1 -> E2 supervision)
                  PHOTO_DARK_SEEN = 1u << 6,
                  FLAMEOUT_OPT = 1u << 7;   // RUN with Pc invalid: optical flame-out check armed (REV-GNC-2 (2))
}
// v2.9 light-detection and start-phase diagnostics (Outputs::ign_det, log v10)
namespace det {
constexpr uint8_t RELATIVE = 1u << 0,   // relative rule in force (else the legacy absolute rule, comparison runs only)
                  PRE_REF = 1u << 1,    // pre-lift baseline P0 captured (at E1)
                  BASE_AMB = 1u << 2,   // P0 failed the check against the auto-zero ambient -> ambient used (LEAD)
                  RISE = 1u << 3,       // filtered AND raw rise over P0 >= cfg::kIgnRise_Pa this tick
                  FLOOR = 1u << 4,      // filtered AND raw Pc >= cfg::kIgnFloorAbs_Pa this tick
                  LIT = 1u << 5,        // E2: light confirmed by the relative rule in this start
                  E3 = 1u << 6,         // E3 reached (start complete: A7 uses the lit map band from here)
                  REZERO = 1u << 7;     // v2.9 coast re-zero applied in this arming session (Pc)
}
// v2.9 TLM_FAST d1 high nibble (drogue-release support, LEAD/GNC 2026-10-13; Outputs::tlm_flags, log v10 tlm_flags). d1 low nibble =
// State (0..8): decoders read the state as d1 & 0x0F. The FC applies the release rule; these bits only report the ECU's light-rule terms.
namespace tlmf {
constexpr uint8_t E2 = 1u << 4,          // light confirmed (E2, det::LIT) in the current/last start (cleared at the next IGNITION entry)
                  RISE_NOW = 1u << 5,    // filtered AND raw Pc >= P0 + kIgnRise_Pa this tick (IGNITION after E1, RUN; 0 elsewhere / Pc invalid)
                  RISE_HELD = 1u << 6,   // v2.10 (LEAD 156 / RE-03): the FILTERED-ONLY rise (filtered Pc >= P0 + kIgnRise_Pa) on every tick
                                         //   since E2 of this start (cleared at the first tick without it or with Pc invalid; not re-set)
                  RISE_HELD_T = 1u << 7; // v2.10: the filtered-only rise held on every tick from E2 to E2 + kDrogueRiseHold_s (latched for the
                                         //   start; never set on an invalid channel, LEAD 168 (1))
// v2.10 (LEAD CHANGELOG 186 (2)) LOG-ONLY bits b0-b1 of Outputs::tlm_flags / LogRecord::tlm_flags (TLM_FAST d1 carries b4-b7 only)
constexpr uint8_t R2_HOLD = 1u << 0,     // R2 command hold active this tick (flight RUN, drogue attached, Pc invalid)
                  DROGUE = 1u << 1,      // drogue attached as last reported by the FC (Cmd::DROGUE)
                  R2_BACKSTOP = 1u << 2; // v2.11 (LEAD 216 (2)(b)): the hold was ended by the E2 + kR2HoldBackstop_s backstop (latched per start)
}
// v2.10 LIGHT_SPIKE record (LEAD 2026-10-13 CHANGELOG 160 (1): A5 deleted as an abort, flight and stand; this record and the EVENT
// LIGHT_SPIKE let IGN-1/T1 measure whether real lights spike). One per start, reset at the IGNITION entry. Window: E1 (lift command) to
// E2 + cfg::kLightSpikeWin_s, or to the exit from IGNITION/RUN (abort, shutdown, no light). Absolute pressures; raw = the 1 kHz decimated
// reading, filt = the 50 Hz 2nd-order channel; a LOW invalid reading (< 0.25 V) is skipped, a HIGH over-range counts (v2.6 OI-6).
// Light estimate = first tick of the run of ticks that confirmed E2 (E2 - (kIgnConfirmRelN - 1) ms). Peak times are from the light
// estimate (from E1 when the start did not light). t8_*: time above cfg::kLightSpikeLoAbs_Pa while the lit-map Pc at the measured lift is
// below it (after E2 the start ramp raises the expected Pc); t30_*: time above cfg::kLightSpikeHiAbs_Pa. RECORD ONLY: no action attached.
// v2.10 (LEAD CHANGELOG 172 (5), REV-COMB-2 R2-10): every value is a LOWER BOUND of the chamber event (peaks low, durations short or
// missed): modelled light spikes last 1-3 ms and the 1L/Helmholtz modes sit at 1.1-1.8 kHz, while this channel is the 1/8 in sense line
// (144-188 Hz resonance, COMB) -> RC 2.4 kHz -> ADS131M04 sinc3 at 4 kSPS -> 4:1 average -> 1 kHz (config.h kLightSpikeLoAbs_Pa block; v2.10 chain, v2.11 flight: C1 at the seat).
// The spike itself is measured on the stand dynamic Pc channel (bench plan v3 B-DPC-1: >= 20 kHz, anti-alias, flush mount), not here.
struct LightSpikeRec {
  bool open = false;              // window open
  bool done = false;              // record of this start complete (closed)
  bool lit = false;               // E2 reached inside the window
  bool closed_by_exit = false;    // closed by leaving IGNITION/RUN before E2 + window (abort, shutdown, no light)
  bool masked = false;            // a tick with Pc above 8 bar abs was not counted (lit map >= 8 bar abs)
  bool overrange = false;         // a sample at or above the transducer HIGH limit (4.75 V) was counted
  bool abovefs = false;           // v2.11 (LEAD 203 (1)(a)): a sample at or above cfg::kPcAboveFs_V (above the transducer full scale) was counted
  float peak_raw_Pa = std::numeric_limits<float>::quiet_NaN();
  float peak_filt_Pa = std::numeric_limits<float>::quiet_NaN();
  float t_peak_raw_s = std::numeric_limits<float>::quiet_NaN();    // from the light estimate (from E1 when unlit); set at the close
  float t_peak_filt_s = std::numeric_limits<float>::quiet_NaN();
  float t_light_s = std::numeric_limits<float>::quiet_NaN();       // light estimate from E1 (NaN = not lit)
  float t8_raw_s = 0.0f, t8_filt_s = 0.0f, t30_raw_s = 0.0f, t30_filt_s = 0.0f;
};

// v2.9 A7 map-criterion phase (Outputs::a7_phase, EVENT PC_IMPLAUS arg)
namespace a7 {
constexpr uint8_t OFF = 0, HOLD = 1, START = 2, RUN_MAP = 3;   // E1->E2 / E2->E3 / after E3
}
// v2.8 final relight-planning state published in TLM_RELIGHT (GNC v3 option (c), LEAD 2026-10-13). NONE until the NC valve has closed
// after MECO (VALID = 0); then PRIMED (a RELIGHT now takes the direct path, 0.81 s flight), UNPRIMED (a RELIGHT now runs the prep path,
// 1.37 s flight) or UNKNOWN (P_feed or P_tank invalid: the ECU runs the prep path; the FC treats UNKNOWN as UNPRIMED)
namespace segstate {
constexpr uint8_t NONE = 0, PRIMED = 1, UNPRIMED = 2, UNKNOWN = 3;
// v2.8.2 (LEAD 2026-10-13 on GNC RG-01): PRIMED means "a RELIGHT now takes the DIRECT path" (pressure rule, both MV switches, no abort and
// no coast pintle anomaly since the last light). It is NOT a liquid indication: saturated vapour in the segment reads PRIMED (the ECU
// cannot see it). Decoders should use the alias names below; the numeric values are unchanged.
constexpr uint8_t DIRECT_PATH = PRIMED, PREP_PATH = UNPRIMED, PREP_PATH_UNKNOWN = UNKNOWN;
}

// Decoded commands (CAN parser fills this; core consumes)
struct Commands {
  bool fast_valid = false;        // a new valid CMD_FAST frame arrived since last tick
  float thrust_sp_N = 0;          // sea-level-equivalent thrust setpoint [N] (ECU converts to Pc)
  float gimbal_cmd_rad[2] = {0, 0};
  bool state_valid = false;       // a new valid CMD_STATE frame (key checked)
  Cmd cmd = Cmd::NOP;
  uint16_t arg = 0;
  bool abort_frame = false;       // valid ABORT frame
  bool aux_valid = false;         // a new valid CMD_AUX frame (roll thrusters, GNC v1 proposal)
  uint8_t roll_bits = 0;          // b0 = roll couple CW, b1 = roll couple CCW (both set = invalid -> both off)
  bool fc_thrust_valid = false;   // v2.8: a new valid FC_THRUST frame (0x024) arrived since last tick
  float fc_thrust_N = 0;          //   FC accelerometer-derived thrust estimate [N] (GNC; error and latency TO-PUBLISH)
  bool fc_thrust_ok = false;      //   frame flag b0: the FC marks its estimate valid
};

// Everything the ECU drives each tick
struct Outputs {
  float servo_us[4] = {1500, 1500, 1500, 1500};  // TVC servo A, TVC servo B (mixed, see TvcShaper), PINTLE, MV_OPENER
  bool servo_enable_tvc = false;  // ACT_PWR switch (TVC servos)
  bool arm_bus_request = false;   // request ARM high-side switch (also needs watchdog + plug)
  bool mv_latch = false;          // main valve holding magnet (dynamic gate driven by HAL while true)
  bool igniter_enable = false;    // 12 V IGN boost enable (spark coil + torch solenoids live)
  bool spark_gate = false;        // coil IGBT gate (dwell pulses; HAL ANDs with the charge-pump enable)
  bool sol[5] = {false, false, false, false, false};  // SOL1 torch N2O, SOL2 torch propane, SOL3 tank vent (not ARM-gated),
                                                     // SOL4 roll couple CW, SOL5 roll couple CCW (GNC v1 roll provision, ARM-gated)
  // telemetry
  State state = State::SAFE;
  Abort abort_cause = Abort::NONE;
  uint16_t fault_bits = 0;
  float pc_sp_active_Pa = 0;      // rate-limited ABSOLUTE Pc setpoint actually tracked
  float pintle_cmd_m = 0;
  float gimbal_cmd_shaped_rad[2] = {0, 0};
  float thrust_est_N = 0;
  bool pc_valid = true;           // v2.8.2 (GNC RG-15, LEAD 2026-10-13): Pc channel valid THIS tick (raw voltage inside the valid window);
                                  //   fault::PC_SENSOR is the latched record. Invalid -> TLM_FAST Pc and TLM_GIMBAL thrust = 0xFFFF (the FC
                                  //   freezes its Pc-based estimators k_est_asc and the B apex predictor; FC_THRUST does NOT freeze)
                                  //   v2.10 (LEAD CHANGELOG 175 (4)): the k_hat freeze is withdrawn FC-side; the markers are unchanged
  bool drogue_attached = false;   // v2.10 (LEAD CHANGELOG 186 (2)): FC drogue state held by the ECU (Cmd::DROGUE); TLM_RELIGHT d6 b6 echo
  bool r2_hold = false;           // v2.10 (LEAD CHANGELOG 186 (2)): R2 command hold active this tick (v2.11: lift-commanded kR2HoldLift_m)
  bool r2_backstop = false;       // v2.11 (LEAD 216 (2)(b)): backstop fired in this start (hold ended at E2 + kR2HoldBackstop_s)
  bool r2_backstop_event = false; // v2.11: ONE tick when the backstop fires (EVENT R2_BACKSTOP 0x24, arg = hold ticks this start)
  int r2_hold_ticks = 0;          // v2.11: R2 hold ticks in this start
  bool pc_commit_valid = true;    // v2.10 (LEAD CHANGELOG 175 (4), Pc VALID = launch-commit condition): ONE pad bit = pc_valid this tick
                                  //   AND fault::PC_SENSOR not latched AND no latched PC_SENSOR abort / ARM refusal. TLM_RELIGHT d6 b7
                                  //   (tlmr6::PC_VALID, 50 Hz, every state). Latched terms clear only with DISARM/SAFE in SAFE [DESIGN]
  float pintle_meas_m = 0;        // v2.10 (LEAD 175 (3)): crank-encoder lift this tick (copied from Inputs) for TLM_FAST d4-d5
  bool pintle_meas_valid = true;  //   encoder reading valid this tick (false -> TLM_FAST d4-d5 = 0xFFFF; can::tlmPintle)
  uint8_t starts_used = 0;
  // v2.3 FM-PWR-01 TVC supply monitor and tank heater permit
  bool tvc_supply_degraded = false; // predicted both-stall plug voltage below kTvcSupplyMin_V (persistent, hysteresis)
  float vplug_pred_V = 0;         // predicted TVC servo plug voltage, both servos at stall
  float rsrc_ohm = 0;             // source resistance used (max of bench calibration and in-situ estimate)
  bool rsrc_measured = false;     // in-situ estimate available (excitation seen)
  bool heater_permit = false;     // firmware layer of the GSE tank-heater interlock (hardware also cuts at ARM)
  uint8_t gimbal_flags = 0;       // TLM_GIMBAL d[1] (protocol.h tlmg::)
  // v2.4 ENG-07b gimbal saturation episodes (per burn: reset at each IGNITION entry) and ENG-07d notch state
  uint8_t gimbal_sat_flags = 0;   // b0 7 deg axis/vector limit, b1 rate/accel shaping (context; v2.8.3 tracker 100 deg/s, 2000 deg/s2), b2 actuator A, b3 actuator B
                                  //   saturation proxy (episodes run on b2|b3 only), this tick
  float gimbal_sat_episode_s = 0; // duration of the actuator-saturation episode in progress (0 when none)
  float gimbal_sat_max_s = 0;     // longest episode since the last IGNITION entry
  uint8_t gimbal_sat_long = 0;    // episodes longer than cfg::kSatEpisodeMax_s since the last IGNITION entry (saturating)
  uint16_t gimbal_sat_count = 0;  // completed episodes since the last IGNITION entry (saturating)
  bool gimbal_notch_on = false;   // any axis notched
  uint8_t gimbal_notch_axes = 0;  // v2.6: b0 alpha notched, b1 beta notched (3 = complete, required for IGNITE/RELIGHT)
  bool gimbal_cal_changed = false; // v2.6: ONE tick when the notch calibration changed in SAFE: the HAL stores NvGimbalCal
  // v2.6 pintle tracking / stall monitor and jam record
  uint8_t pintle_fault_kind = 0;  // jam:: kind of the first jam since the last DISARM in SAFE
  bool pintle_backoff = false;    // pintle command forced closed after a jam (latched until DISARM in SAFE)
  bool pintle_jam_event = false;  // ONE tick when a new jam is detected: the HAL writes the non-volatile record, an EVENT frame
  PintleJamEvent pintle_jam;      //   (protocol.h evt::PINTLE_JAM) and the log; details here
  bool maint_jam_pending = false; // a jam is recorded and not cleared (this power cycle or the non-volatile flag): ARM refused
  bool maint_clear_jam = false;   // ONE tick when CLEAR_JAM is accepted: the HAL clears the non-volatile record
  float pintle_noprog_s = 0;      // time since the last progress mark in the current tracking episode (0 = no episode)
  // v2.7 (2026-10-13 review fold-in): sequence flags (log v6 seq_flags)
  bool torch_ok = false;          // torch flame confirmed (P_torch) in this start
  bool torch_gate_bypass = false; // GROUND timing-only start armed (SET_TORCH_GATE key) or in use in this start
  bool torch_closed = false;      // torch valves closed by the light-confirmation event or the propane backstop (this start)
  bool relight_ext = false;       // v2.8: this start's ignition window is 0.65 s (flight relight; v2.8.1: stand R3 retired); v2.7: C7 extension
  bool relight_lockout = false;   // no further ignition until CLEAR_LOCKOUT (ground); RAM flag OR the non-volatile input
  bool relight_lockout_event = false;   // ONE tick when the lockout is set: the HAL writes the non-volatile flag + EVENT 0x16
  bool relight_lockout_clear = false;   // ONE tick when CLEAR_LOCKOUT is accepted: the HAL clears the non-volatile flags b1, b2 and b4
  bool safing_hold = false;             // v2.10 (LEAD 172 (1)): ground no-light safing hold open (CLEAR_LOCKOUT refused while time is left)
  float safing_hold_left_s = 0.0f;      // v2.10: time left before CLEAR_LOCKOUT can be accepted [s] (0 = none or elapsed)
  bool safing_hold_event = false;       // v2.10: ONE tick when the hold opens: the HAL sets NvJamRecord b4 + EVENT SAFING_HOLD
  bool lit_session_event = false; // ONE tick at the first confirmed light since the last commanded DISARM/SAFE: the HAL sets
                                  //   NvJamRecord b2 ("lit session open"). A boot with b2 set (ECU reset during or after a lit burn,
                                  //   before the normal DISARM) reports Inputs::nv_relight_lockout = true -> no start until CLEAR_LOCKOUT
  bool lit_session_close = false; // ONE tick when a commanded DISARM/SAFE safes the ECU after a lit session (normal end; not an
                                  //   abort): the HAL clears b2
  bool mv_seat_wait = false;      // SHUTDOWN: NC valve held until the pintle is seated or kMvSeatTimeout_s (pintle then valve)
  bool mv_seat_timeout = false;   // the last normal shutdown released the valve on the timeout, not on a confirmed seat
  bool prail_lost = false;        // pintle rail lost while the servo should be powered (latched until DISARM in SAFE)
  float ign_check_s = 0.0f;       // v2.8: ignition window W of the current start [s from the ignition-lift command] (v2.7: deadline
                                  //   from IGNITION entry); 0 outside IGNITION
  // v2.8 (LEAD 2026-10-13)
  uint8_t ign_rule = 0;           // rule:: of the current/last start
  float ign_lift_t_s = -1.0f;     // E0 -> ignition-lift command of the current start [s] (-1 before the lift)
  float ign_lift_m = 0.0f;        // ignition lift of the current start (lift-vs-T_tank table, before the map trim)
  bool superheat_proven = false;  // stand R3 condition at E0 of the current start (both state TCs >= Tsat(P_feed) + 5 K)
  bool relight_direct = false;    // this start opened the NC valve at E0 (Finding A; no PREPRESS)
  bool s1_zero_ok = false;        // in-situ P_feed - P_tank zero captured (MV open, pintle seated, no flow)
  bool s1_fault = false;          // S1 relief suspected failed (latched until DISARM in SAFE): stand -> relight lockout; flight flag
  bool s1_event = false;          // ONE tick when s1_fault is set (EVENT S1_FAULT)
  float s1_dp_Pa = 0.0f;          // P_feed - P_tank - zero with the MV closed (NaN when not evaluated)
  bool mode_stand = false;        // mode of this arming session (strap, latched at ARM; live strap AND load cell in SAFE)
  bool mode_mismatch = false;     // strap / load-cell disagreement after ARM (flag only, latched until DISARM in SAFE)
  bool fc_thrust_fresh = false;   // FC thrust estimate valid and younger than cfg::kFcThrustStale_s
  uint8_t cmd_refused = 0;        // refuse:: reason of the last refused IGNITE/RELIGHT/PREPRESS (sticky until the next accepted one)
  bool cmd_refused_event = false; // ONE tick per refused command with a v2.8 reason (EVENT CMD_REFUSED)
  // v2.8 final (LEAD 2026-10-13: COMB v2.4 abort -> vapour segment, GNC v3 primed flag, tank interlock)
  bool seg_vapour = false;        // an abort since the last confirmed light: the segment is treated as holding vapour (NV b3); a RELIGHT
                                  //   takes the prep path, TLM UNPRIMED/UNKNOWN; stand: the next start uses the R2/R3 logic (R4 refusal)
  bool seg_vapour_event = false;  // ONE tick: the HAL sets NvJamRecord b3
  bool seg_vapour_clear = false;  // ONE tick: the HAL clears b3 (light confirmed, RUN entry)
  uint8_t relight_state = 0;      // segstate:: published in TLM_RELIGHT (NONE until the MECO valve closure in COAST)
  bool meco_closed = false;       // COAST: the NC valve has shown CLOSED with OPEN clear since this coast began (or the closure is overdue)
  float tank_T_K = 0.0f;          // tank temperature used by the interlock: max(valid wall DS18B20, Tsat(P_tank)) [K]; NaN = no valid reading
  bool tank_hot = false;          // interlock condition this tick (above cfg::kTankIgnMax_K, or no valid reading)
  bool tank_xcheck = false;       // wall mean and Tsat(P_tank) differ by more than cfg::kTankXcheckMax_K (flag; latched until DISARM in SAFE)
  bool tank_hot_relight = false;  // a flight relight was accepted with the interlock condition set (flag only; latched until DISARM in SAFE)
  bool tank_cold = false;         // v2.10 RE-17: below cfg::kTankIgnMin_K or no valid reading this tick (ARM / pad / stand refusal)
  // v2.8 (LEAD 2026-10-13, GNC: the FC must know before T_fire whether the segment is primed) relight-planning status, sent by the HAL
  // in TLM_RELIGHT (0x102) at 50 Hz in every state (>= 10 Hz required in COAST): same criterion as the ECU's relight path selection
  bool seg_valid = false;         // P_feed and P_tank readings both valid (PRIMED is meaningful only with this set)
  bool seg_primed = false;        // valve-to-seat segment primed: P_tank > 5 bar g and P_feed >= kPrimeSlowFrac P_tank (absolute)
  float seg_ratio = 0.0f;         // P_feed / P_tank (absolute, filtered); NaN when not valid
  uint8_t relight_block = 0;      // refuse:: reason a RELIGHT sent now would get (0 = would be accepted; NOT_COAST outside COAST)
  uint16_t relight_worst_ms = 0;  // E0 -> Pc-confirm deadline of a RELIGHT sent now [ms]: direct path gate + W (flight 810), segment not
                                  //   primed: + bleed settle + opener ramp + hold (flight 1370), assuming the feed primes by the end of
                                  //   the hold (PREPRESS bound 2420 ms, then PREPRESS_FAIL); v2.11 flight, bleed fitted, in COAST: kPurgeRelight_s + gate + W (3710)
  // v2.8.2 (GNC REV-GNC-1 RG-08): coast pintle-position anomaly (latched until a confirmed light or DISARM in SAFE)
  uint8_t coast_pintle = 0;       // b0 encoder invalid on a COAST tick (TLM UNKNOWN), b1 lift above cfg::kCoastPintleOpen_m for
                                  //   cfg::kCoastPintleOpenN COAST ticks (TLM UNPRIMED); either forces the prep path
  uint8_t coast_pintle_event = 0; // ONE tick: 1 encoder-lost latch set, 2 pintle-open latch set (EVENT COAST_PINTLE)
  // v2.9 head-end bleed provision (LEAD 2026-10-13; cfg 'head-end bleed' block). Drives: V1 on Teensy pin 15 (shared with the heater
  // permit: heater only in SAFE with the ARM plug out, bleed only with the ARM bus on - the HAL ORs both, the core never sets both),
  // V2 on pin 24 (freed by the MV switch ladder); both through AHCT buffers (/OE = watchdog) and FETs on +12V_ARM
  bool hbleed[2] = {false, false};  // [0] V1 (upstream, T4 port), [1] V2 (downstream); true = energise (NC valve open)
  uint8_t hbleed_flags = 0;       // hb::F_* (path, closure, leak, BIT, latched flags)
  uint8_t hbleed_bit = 0;         // hb::BIT_* pad BIT state / result
  uint8_t hbleed_event = 0;       // ONE tick: hb::EV_* (EVENT HBLEED 0x1D)
  float purge_left_s = 0.0f;      // PURGE: time to the planned IGNITION (t_purge - elapsed, >= 0; 0 outside PURGE)
  // v2.9 light detection (B): references of the current/last start (gauge, auto-zeroed, filtered) and flags (det::)
  uint8_t ign_det = 0;
  float ign_ref_Pa = std::numeric_limits<float>::quiet_NaN();    // P0 pre-lift baseline, gauge (NaN before E1)
  float ign_rise_Pa = std::numeric_limits<float>::quiet_NaN();   // filtered rise over P0 this tick (NaN before E1)
  // v2.9 A3 relative flame-out and A7 map criterion (config.h)
  float flame_ratio = std::numeric_limits<float>::quiet_NaN();   // (Pc - P0) / (Pc_map - P0) in RUN (NaN outside)
  float pc_map_Pa = std::numeric_limits<float>::quiet_NaN();     // A3 reference map: min(40 ms lagged, instantaneous) lit-map Pc at the
                                                                  //   (encoder) lift, absolute (NaN outside IGNITION/RUN)
  uint8_t a7_phase = 0;           // a7:: phase of the map criterion this tick
  bool a7_flag = false;           // A7 map criterion tripped in flight RUN (latched for this burn; fault PC_SENSOR)
  bool a7_event = false;          // ONE tick: A7 map criterion tripped (EVENT PC_IMPLAUS)
  // v2.9 coast re-zero
  bool rezero_event = false;      // ONE tick: the Pc zero was re-taken in COAST (EVENT REZERO, log)
  float rezero_shift_Pa = 0.0f;   // last Pc re-zero shift from the zero in use before it [Pa] (accepted or rejected)
  bool rezero_rejected = false;   // the last COAST re-zero attempt was rejected (shift above cfg::kPcRezeroMax_Pa or not steady)
  // v2.9 drogue-release support: tlmf:: bits (TLM_FAST d1 b4-b7); E2 time = EVENT STATE (RUN) t_ms
  uint8_t tlm_flags = 0;
  // v2.10 LIGHT_SPIKE record of the current/last start (A5 deleted, LEAD CHANGELOG 160) and its one-tick closing pulse
  LightSpikeRec light_spike;
  bool light_spike_event = false;   // ONE tick: the record closed (EVENT LIGHT_SPIKE 0x20, log v11 ls_flags b3)
  // v2.10 purge on flow time (LEAD CHANGELOG 164) and closure detail
  bool state_event = false;          // ONE tick: the state changed on this tick (EVENT STATE, can::encodeStateEvent; E2 = change to RUN)
  uint32_t state_t_ms = 0;           // ECU time of the last state change [ms] (= t_E2 for the change to RUN)
  uint8_t hbleed2 = 0;               // hb2:: flags of the current / last purge
  uint16_t purge_flow_ms = 0xFFFF;   // achieved FLOW time of the last purge [ms] (DERIVED: command times + valve times); 0xFFFF none
  bool purge_flow_event = false;     // ONE tick: V1 close command issued (EVENT PURGE_FLOW 0x21, arg = purge_flow_ms)
  bool bleed_fault = false;          // closure not confirmed in this arming session (flight FLAG to the FC; latched until DISARM)
  uint8_t fault2 = 0;                // f2:: flags (latched ones until DISARM in SAFE; LIFT_CLAMP per tick)
  bool fault2_event = false;         // ONE tick: a latched f2:: flag was set (EVENT FLAGS2 0x22, arg = fault2 | new bits << 8)
  uint8_t fault2_new = 0;
  // v2.10 FA-1 flame sensing
  uint8_t fa1 = 0;                   // fa1:: flags
  float photo_V = 0.0f;              // photodiode head reading this tick [V]
  float photo_dark_V = 0.0f;         // dark level frozen at E0 (tracked before) [V]
  // v2.11 (LEAD CHANGELOG 203 (1)): Pc over-range / above-full-scale (non-sticky, this tick) and the FA-1 ride-through CANDIDATE
  bool pc_overrange = false;         // reading >= cfg::kPcSensorMax_V this tick (PC_VALID 0 only while it lasts; flight: no PC_SENSOR latch)
  bool pc_above_fs = false;          // reading >= cfg::kPcAboveFs_V this tick (flag only)
  uint8_t ovr_flags = 0;             // ovr:: bits (log v12)
  bool build_event = false;          // v2.13 ONE tick: at boot (first step) and on every ARM command received (EVENT BUILD 0x25)
  uint8_t build_bits = 0;            // v2.13 EVENT BUILD arg: evt::BUILD_SEAT_RULE (seat_arm_rule) | evt::BUILD_HBLEED (hbleed_fitted)
  // v2.12: TB-state, seat compensation, J-FWD indication (f3::, log v13)
  uint8_t f3_flags = 0;              // f3:: bits
  float pc_seat_comp_Pa = 0.0f;      // seat compensation subtracted from the Pc reading this tick [Pa] (0 when off)
};

}  // namespace ecu
