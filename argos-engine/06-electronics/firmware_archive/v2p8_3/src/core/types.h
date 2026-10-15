// ARGOS engine ECU - shared types (v2.8.2, 2026-10-13: Outputs coast_pintle / coast_pintle_event (GNC RG-08). v2.8: relight with the NC valve opened at E0 and the lift at E1 (LEAD Finding A),
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
  TANK_HOT = 27           // v2.8 final (LEAD 2026-10-13, ENG-12 15-24 C; COMB v2.4 MEOP 45 bar kept, worst band corner 44.33 bar at
                          //   24 C): ARM refused - tank temperature (max of the valid tank-wall DS18B20 and Tsat(P_tank)) above
                          //   cfg::kTankIgnMax_K, or no valid tank temperature at all
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
  float tc_bore_K = 293.15f;      // v2.7: bore-top / manifold thermocouple (MAX31856 #4; CF-3/T1 C7 evidence, flight TO-DEFINE)
  bool tc_bore_valid = false;     //   not fitted = invalid (logged only)
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
  bool nv_seg_vapour = false;     // v2.8 final (COMB v2.4 / LEAD 2026-10-13): NvJamRecord b3 at boot (or CORRUPT) - an abort left vapour in
                                  //   the valve-to-seat segment; the next start is a vapour-segment start (HAL clears it on seg_vapour_clear)
  float ttank_wall_K[2] = {293.15f, 293.15f};   // v2.8 final (LEAD 2026-10-13 tank interlock): tank-wall DS18B20 #1/#2 on J608 (1-Wire bus
  bool ttank_wall_valid[2] = {true, true};      //   shared with the bay sensor, 12-bit, 1 Hz). HAL: not found / CRC error / older than 2 s = invalid
  float load_cell_N = std::numeric_limits<float>::quiet_NaN();   // test stand only: NaN in flight. v2.7: a FINITE reading identifies
                                  //   the test stand; v2.8: the mode is the strap AND this check (mismatch -> ARM refused)
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
                  VENT_WAIT = 9,    // < 5 s since a no-light / flameout (COMB v2.2)
                  NOT_COAST = 10,   // TLM_RELIGHT only: a RELIGHT now would be ignored (not in COAST)
                  TANK_HOT = 11;    // v2.8 final: tank above cfg::kTankIgnMax_K or no valid tank temperature (pad first start, stand starts)
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
  bool relight_lockout_clear = false;   // ONE tick when CLEAR_LOCKOUT is accepted: the HAL clears the non-volatile flags b1 and b2
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
  // v2.8 (LEAD 2026-10-13, GNC: the FC must know before T_fire whether the segment is primed) relight-planning status, sent by the HAL
  // in TLM_RELIGHT (0x102) at 50 Hz in every state (>= 10 Hz required in COAST): same criterion as the ECU's relight path selection
  bool seg_valid = false;         // P_feed and P_tank readings both valid (PRIMED is meaningful only with this set)
  bool seg_primed = false;        // valve-to-seat segment primed: P_tank > 5 bar g and P_feed >= kPrimeSlowFrac P_tank (absolute)
  float seg_ratio = 0.0f;         // P_feed / P_tank (absolute, filtered); NaN when not valid
  uint8_t relight_block = 0;      // refuse:: reason a RELIGHT sent now would get (0 = would be accepted; NOT_COAST outside COAST)
  uint16_t relight_worst_ms = 0;  // E0 -> Pc-confirm deadline of a RELIGHT sent now [ms]: direct path gate + W (flight 810), segment not
                                  //   primed: + bleed settle + opener ramp + hold (flight 1370), assuming the feed primes by the end of
                                  //   the hold (PREPRESS bound 2420 ms, then PREPRESS_FAIL)
  // v2.8.2 (GNC REV-GNC-1 RG-08): coast pintle-position anomaly (latched until a confirmed light or DISARM in SAFE)
  uint8_t coast_pintle = 0;       // b0 encoder invalid on a COAST tick (TLM UNKNOWN), b1 lift above cfg::kCoastPintleOpen_m for
                                  //   cfg::kCoastPintleOpenN COAST ticks (TLM UNPRIMED); either forces the prep path
  uint8_t coast_pintle_event = 0; // ONE tick: 1 encoder-lost latch set, 2 pintle-open latch set (EVENT COAST_PINTLE)
};

}  // namespace ecu
