// ARGOS engine ECU - FC<->ECU CAN protocol, binary log format and non-volatile jam / gimbal-notch records (v2.9: log v10 (+12 bytes: head-end
// bleed, light-rule baseline/rise, A3 ratio, lagged map Pc, A7 / E3 / re-zero flags), events 0x1D HBLEED, 0x1E REZERO, 0x1F PC_IMPLAUS,
// TLM_RELIGHT VALID/PRIMED through a PURGE, FC_THRUST valid-flag wording 'no drogue load'; v2.8.3: sat_flags b1 = tracker shaping, no layout change; v2.8.2: event 0x1C
// COAST_PINTLE, log v9 (seq3_flags b7, layout unchanged), TLM_RELIGHT frame unchanged with UNKNOWN / UNPRIMED also set by a coast pintle
// anomaly (GNC REV-GNC-1 RG-08); v2.8.1: FC_THRUST rule
// adopted, frame unchanged; v2.8: FC_THRUST frame 0x024, log v7, events 0x19-0x1B and 0x15 redefined; v2.7: log v6, events 0x15-0x18,
// relight lockout in NvJamRecord flags b1, lit-session marker b2)
// CAN 2.0B 1 Mbit/s, 11-bit IDs, little-endian payloads. Safety frames carry an 8-bit rolling
// sequence and a CRC-8 (SAE J1850 polynomial 0x1D, init 0xFF, final XOR 0xFF) over the preceding
// payload bytes, on top of the CAN controller's own CRC-15.
#pragma once
#include <cstdint>
#include <cstring>
#include <limits>
#include "types.h"
#include "control.h"   // v2.6: GimbalNotchCal (NvGimbalCal record)

namespace ecu {
namespace can {

constexpr uint16_t ID_ABORT = 0x010, ID_CMD_FAST = 0x020, ID_FC_THRUST = 0x024, ID_CMD_AUX = 0x028, ID_CMD_STATE = 0x030;
constexpr uint16_t ID_TLM_FAST = 0x100, ID_TLM_GIMBAL = 0x101, ID_TLM_RELIGHT = 0x102, ID_TLM_SLOW = 0x110, ID_EVENT = 0x120;

struct Frame {
  uint16_t id = 0;
  uint8_t len = 0;
  uint8_t d[8] = {0};
};

uint8_t crc8(const uint8_t* p, int n);
inline uint16_t keyFor(Cmd c) { return static_cast<uint16_t>(0xA500u | (static_cast<uint8_t>(c) ^ 0x5Au)); }

// --- FC side encoders (used by the FC firmware, the test-stand box and the SIL)
Frame encodeCmdFast(uint8_t seq, float thrust_sp_N, float ga_rad, float gb_rad);   // thrust in 0.1 N steps
Frame encodeCmdState(uint8_t seq, Cmd c, uint16_t arg);
Frame encodeAbort(uint8_t seq, uint8_t code);
Frame encodeCmdAux(uint8_t seq, uint8_t roll_bits);   // >= 50 Hz while a roll pulse is wanted (dead-man 50 ms)
// v2.8 FC_THRUST (0x024, len 5): d0 seq, d1-d2 u16 thrust estimate [0.1 N], d3 flags (b0 estimate valid), d4 CRC-8. FC accelerometer
// thrust estimate, first-order tau 20 ms (GNC m2_fc_thrust v1.1); 100 Hz = interface requirement. b0 set by the FC only while airborne,
// engine lit (ECU RUN) and with NO DROGUE LOAD (LEAD 2026-10-13 CHANGELOG line 111 (6); v2.8-v2.8.3 wording "drogue released"). v2.8.1: used by the ADOPTED OVER_THRUST abort (> 650 N on 3 consecutive
// fresh valid frames, flight RUN, with or without a valid Pc; never on the stand); stale (> 50 ms) or b0 = 0 -> flag only.
Frame encodeFcThrust(uint8_t seq, float thrust_N, bool valid);

// --- ECU side decoder with per-ID sequence supervision. Returns true if the frame was accepted.
class Decoder {
 public:
  bool accept(const Frame& f, Commands& out);
  uint32_t rejected_crc = 0, rejected_seq = 0, rejected_key = 0, rejected_len = 0;
 private:
  bool have_seq_[4] = {false, false, false, false};   // [0] CMD_FAST [1] CMD_STATE [2] FC_THRUST (v2.8) [3] CMD_AUX
  uint8_t last_seq_[4] = {0, 0, 0, 0};
  bool seqOk(int idx, uint8_t seq);
};

// --- ECU telemetry encoders
Frame encodeTlmFast(uint8_t seq, const Outputs& o, float pc_abs_Pa, float pintle_m);
Frame encodeTlmGimbal(uint8_t seq, uint8_t flags, const float meas_rad[2], float thrust_N);
// TLM_FAST (0x100, 500 Hz, len 8): d0 seq, d1 b0-b3 state (State 0..8; read as d1 & 0x0F) b4-b7 tlmf:: drogue-release support bits
// (v2.9, LEAD/GNC 2026-10-13: E2 of this start, rise now, rise held since E2, rise held to E2 + kDrogueRiseHold_s), d2-d3 Pc [kPa abs],
// d4-d5 pintle lift [um], d6-d7 fault bits (fault::PC_SENSOR included). The E2 timestamp is EVENT STATE (RUN entry) t_ms.
// v2.8.2 (GNC RG-15, LEAD 2026-10-13): Pc-derived telemetry carries an invalid marker. TLM_FAST d2-d3 Pc [kPa abs] = 0xFFFF while the Pc
// channel is invalid this tick (Outputs::pc_valid; the latched fault::PC_SENSOR stays in d6-d7); TLM_GIMBAL d6-d7 thrust [0.1 N] = 0xFFFF
// for a NaN argument - the HAL passes tlmThrust(o). The FC freezes k_est_asc and the B apex predictor on the marker; FC_THRUST (the
// accelerometer over-thrust estimate) keeps running.
inline float tlmThrust(const Outputs& o) { return o.pc_valid ? o.thrust_est_N : std::numeric_limits<float>::quiet_NaN(); }
Frame encodeEvent(uint8_t code, State s, uint32_t t_ms, uint16_t arg);
// v2.8 TLM_RELIGHT (0x102, len 8; LEAD 2026-10-13: the FC must know before T_fire whether the MV segment is primed; v2.8 final: GNC v3
// option (c) states and stale-flag rule, LEAD-accepted). The HAL sends it every 20 ms (50 Hz) in every state (requirement: >= 10 Hz in
// COAST). d0 seq (rolling, +1 per frame), d1 state, d2 flags (tlmr::), d3-d4 u16 relight_worst_ms (RELIGHT command -> Pc-confirm
// deadline of a RELIGHT sent now: 810 flight direct, 1370 flight prep path), d5 P_feed/P_tank absolute [%] (0xFF = not valid; 0-254),
// d6 refuse:: reason a RELIGHT sent now would get (0 = accepted), d7 CRC-8 over d0-d6.
// Relight state (segstate::) = VALID b1, PRIMED b0, UNKNOWN b7: VALID 0 -> NONE (before the MECO valve closure / not in COAST);
// VALID 1: UNKNOWN 1 -> UNKNOWN (P_feed or P_tank invalid, or v2.8.2 the pintle encoder was invalid on a COAST tick since the last light),
// else PRIMED 1 -> PRIMED, else UNPRIMED (v2.8.2 includes the coast pintle-open latch: encoder lift > 0.10 mm for 20 ms). PRIMED = a RELIGHT now takes the
// direct path; UNPRIMED/UNKNOWN = it runs the prep path. Invariants (decoder rejects otherwise): PRIMED or UNKNOWN only with VALID;
// never PRIMED and UNKNOWN together.
// v2.9 head-end bleed (A1 build, EngineEcu::hbleed_fitted): in PURGE the frame shows VALID 1 + PRIMED (the purge runs on the direct path
// only), READY when a RELIGHT would be accepted, and worst_ms = remaining purge + torch gate + W; in COAST on the direct path with the
// bleed fitted, worst_ms = t_purge + gate + W (a RELIGHT runs the sequence-integrated purge: 2.5 + 0.16 + 0.65 s = 3310 ms flight). A
// RELIGHT sent at or after the end of a pre-scheduled PURGE (FC: PURGE at T_fire - t_purge) keeps the 0.81 s plan. GNC owns the FC use.
// FC rule (GNC v3, LEAD 2026-10-13): fresh = CRC good, sequence advancing, age <= 0.3 s (GNC ASSUMED; Electronics confirms: 15 frame
// periods; the fastest seat-leak unpriming is >= 6.1 min, MECH seat_leak_drain_v1). PRIMED -> plan 0.81 s; UNPRIMED or UNKNOWN -> plan
// 1.41 s; VALID 0 or stale -> hold the last valid state since the MECO valve closure, none -> 0.81 s. READY 0 -> a RELIGHT would be
// refused (d6). POST_ABORT (b6): an abort since the last light, PRIMED is never shown (COMB v2.4 vapour segment).
Frame encodeTlmRelight(uint8_t seq, const Outputs& o);
struct TlmRelight { uint8_t seq = 0, state = 0, flags = 0, ratio_pct = 0xFF, block = 0; uint16_t worst_ms = 0; };
bool decodeTlmRelight(const Frame& f, TlmRelight* r);   // FC / test stand / SIL side: length + CRC check (sequence: caller)

}  // namespace can
namespace tlmr {   // TLM_RELIGHT d2 flag bits (v2.8 final)
constexpr uint8_t PRIMED = 1u << 0;     // a RELIGHT now takes the direct path (segstate::PRIMED); only with VALID, never with UNKNOWN
constexpr uint8_t DIRECT_PATH = PRIMED; // v2.8.2 alias (LEAD 2026-10-13): the bit means DIRECT PATH, not "liquid in the segment"
constexpr uint8_t VALID = 1u << 1;      // relight state valid: COAST after the MECO valve closure, or PURGE (v2.9) (v2.8 draft: pressures valid)
constexpr uint8_t READY = 1u << 2;      // in COAST or PURGE (v2.9) and a RELIGHT now would be accepted (d6 = 0)
constexpr uint8_t LOCKOUT = 1u << 3;    // relight lockout pending
constexpr uint8_t S1_FAULT = 1u << 4;   // S1 relief suspected failed (flight: flag only)
constexpr uint8_t STAND = 1u << 5;      // stand mode (strap)
constexpr uint8_t POST_ABORT = 1u << 6; // v2.8 final: an abort since the last light (vapour-segment start; v2.8 draft b6 = DIRECT build flag)
constexpr uint8_t UNKNOWN = 1u << 7;    // v2.8 final: VALID and P_feed or P_tank invalid (segstate::UNKNOWN; the FC treats it as UNPRIMED)
inline uint8_t stateOf(uint8_t flags) {   // segstate:: from the flags of a decoded frame
  if (!(flags & VALID)) return segstate::NONE;
  if (flags & UNKNOWN) return segstate::UNKNOWN;
  return (flags & PRIMED) ? segstate::PRIMED : segstate::UNPRIMED;
}
}  // namespace tlmr

// EVENT (0x120) codes (v2.6: first enumeration; the HAL emits one frame per event, three times 10 ms apart)
namespace evt {
constexpr uint8_t STATE = 0x01;        // arg = new state | (abort cause << 8)
constexpr uint8_t PINTLE_JAM = 0x10;   // arg = jam kind | (jam count this power cycle << 8); details: log + NvJamRecord
constexpr uint8_t JAM_CLEARED = 0x11;  // CLEAR_JAM accepted ("bearing A replaced"); arg = clear count after the update
constexpr uint8_t JAM_RECORD_BAD = 0x12;   // NvJamRecord unreadable at boot (CRC/magic): treated as pending (fail-safe)
constexpr uint8_t GIMBAL_CAL_BAD = 0x13;   // v2.6: NvGimbalCal unreadable or out of range at boot: no notch -> IGNITE/RELIGHT refused
constexpr uint8_t GIMBAL_CAL_STORED = 0x14;   // v2.6: notch calibration changed in SAFE and stored; arg = axes enabled (b0 alpha, b1 beta) | seq << 8
constexpr uint8_t IGN_WINDOW = 0x15;          // v2.8 (v2.7 RELIGHT_CHECK_EXT retired): at each IGNITION entry; arg = rule:: (low byte) |
                                              //   W [10 ms] (high byte); the HAL adds the lift time (E0->E1) to the log only
constexpr uint8_t RELIGHT_CHECK_EXT = IGN_WINDOW;   // v2.7 name kept for decoders
constexpr uint8_t RELIGHT_LOCKOUT = 0x16;     // v2.7: arg 1 = lockout set (no further ignition), 0 = cleared by CLEAR_LOCKOUT
constexpr uint8_t TORCH_GATE_BYPASS = 0x17;   // v2.7: arg 1 = ground timing-only start armed, 2 = used by this start, 0 = cleared
constexpr uint8_t PRAIL_LOST = 0x18;          // v2.7: pintle rail lost (OV disconnect or regulator failure); arg = rail [mV] at detection
constexpr uint8_t S1_FAULT = 0x19;            // v2.8: S1 relief suspected failed; arg = P_feed - P_tank - zero [hPa] at detection
                                              //   (stand: the relight lockout follows with 0x16; flight: flag only)
constexpr uint8_t CMD_REFUSED = 0x1A;         // v2.8: IGNITE/RELIGHT/PREPRESS refused for a v2.8 reason; arg = refuse:: | (state << 8)
constexpr uint8_t MODE_MISMATCH = 0x1B;       // v2.8: strap / load cell disagree after ARM (flag); arg = strap | (load cell finite << 8)
constexpr uint8_t COAST_PINTLE = 0x1C;        // v2.8.2 (GNC RG-08): coast pintle anomaly latched; arg = 1 encoder invalid (TLM UNKNOWN) or
                                              //   2 lift > 0.10 mm for 20 ms (TLM UNPRIMED) | (encoder lift [10 um], 0xFF = invalid) << 8
constexpr uint8_t HBLEED = 0x1D;              // v2.9 head-end bleed (LEAD A1 provision): arg = hb::EV_* (low byte) | Outputs::hbleed_bit << 8
                                              //   (BIT pass/fail with the failed step, path not proven, V1 confirmed closed, V1 NOT confirmed
                                              //   closed -> BLEED_FAULT, leak with both closed, purge hold timeout, encoder invalid in PURGE)
constexpr uint8_t REZERO = 0x1E;              // v2.9 coast re-zero of Pc ACCEPTED; arg = int16 shift from the zero in use before [hPa]
constexpr uint8_t PC_IMPLAUS = 0x1F;          // v2.9 A7 map criterion tripped; arg = a7:: phase (low byte) | Pc abs [0.1 bar, 0..254] << 8
                                              //   (IGNITION or stand: PC_SENSOR abort follows; flight RUN: flag only, burn continues)
inline uint16_t pcImplausArg(uint8_t phase, float pc_abs_Pa) {
  const float u = pc_abs_Pa * 1.0e-4f;
  const unsigned hi = !(u == u) ? 0xFFu : (u <= 0.0f ? 0u : (u >= 254.0f ? 254u : static_cast<unsigned>(u + 0.5f)));
  return static_cast<uint16_t>((phase & 0xFFu) | (hi << 8));
}
inline uint16_t rezeroArg(float shift_Pa) {
  const float h = shift_Pa * 0.01f;
  const int v = !(h == h) ? 0 : (h > 32767.0f ? 32767 : (h < -32767.0f ? -32767 : static_cast<int>(h < 0 ? h - 0.5f : h + 0.5f)));
  return static_cast<uint16_t>(static_cast<int16_t>(v));
}
inline uint16_t jamArg(const PintleJamEvent& e) { return static_cast<uint16_t>(e.kind | ((e.count > 255 ? 255 : e.count) << 8)); }
// v2.8.2 COAST_PINTLE argument (HAL): kind 1/2 in the low byte, encoder lift in 10 um steps in the high byte (0xFF invalid; 0..2.54 mm)
inline uint16_t coastPintleArg(uint8_t kind, bool enc_valid, float lift_m) {
  const float u = lift_m * 1.0e5f;
  const unsigned hi = !enc_valid || !(u == u) ? 0xFFu : (u <= 0.0f ? 0u : (u >= 254.0f ? 254u : static_cast<unsigned>(u + 0.5f)));
  return static_cast<uint16_t>(kind | (hi << 8));
}
}  // namespace evt

// TLM_GIMBAL (0x101) d[1] flag bits (v2.3; Outputs::gimbal_flags)
namespace tlmg {
constexpr uint8_t TVC_PWR = 1u << 0;          // TVC servo power switch commanded on
constexpr uint8_t ENC_A_OK = 1u << 1, ENC_B_OK = 1u << 2;   // gimbal encoder readings valid
constexpr uint8_t SUPPLY_DEGRADED = 1u << 3;  // FM-PWR-01: predicted both-stall plug voltage below kTvcSupplyMin_V
constexpr uint8_t GIMBAL_FAULT = 1u << 4;     // fault::GIMBAL set (command-model vs encoder mismatch)
constexpr uint8_t RSRC_MEASURED = 1u << 5;    // in-situ source-resistance estimate available
constexpr uint8_t HEATER_PERMIT = 1u << 6;    // firmware tank-heater permit (hardware interlock also required)
constexpr uint8_t SAT_LONG = 1u << 7;         // v2.4 ENG-07b: a gimbal saturation episode > 0.1 s since the last IGNITION
}  // namespace tlmg

// ----------------------------------------------------------------------------------- log record
// One record per 1 ms tick; identical on the flight ECU and on the static-fire stand.
#pragma pack(push, 1)
struct LogRecord {
  uint16_t magic;        // 0xA7E5
  uint8_t version;       // 10 (v2.9: + hbleed_flags .. seq4_flags, tlm_flags; 150 bytes); 9 (v2.8.2: seq3_flags b7 = coast pintle anomaly, layout unchanged); 8 (v2.8 final: + tank T, seq3_flags); 7 (v2.8 draft: + MSS-1/MSS-2 TCs, FC thrust estimate, S1 dp, seq2_flags, ign_rule, lift time, refusal, bay T; v6 (v2.7):
                         //   + ptorch, prail, pintle current, bore TC, seq_flags, ign_check_cs; v5 (v2.6): sat_flags b5-b7
                         //   pintle; v4: + sat_ms, sat_flags, sat_long; v3: + ibat_cA, vplug_pred_mV, flags b14/b15)
  uint8_t state;
  uint32_t t_us;
  uint16_t rec_seq;      // rolls over; gaps reveal dropped records
  uint16_t fault_bits;
  uint8_t abort_cause;
  uint8_t starts_used;
  float pc_Pa, pc_sp_Pa, pfeed_Pa, ptank_Pa;   // Pc and setpoint ABSOLUTE (filtered); feed/tank GAUGE
  float pintle_cmd_m, pintle_meas_m;
  float ga_cmd_rad, gb_cmd_rad, ga_meas_rad, gb_meas_rad;
  float thrust_est_N, load_cell_N;     // load cell = NaN in flight
  int32_t pc_raw4[4];                  // 4 kHz raw ADC codes of the Pc channel within this ms
  uint16_t servo_us[4];
  int16_t tc_dK[4];                    // 0.1 K, offset from 273.15 K (range -3276..+3276 K)
  uint16_t vbat_mV;
  int16_t ibat_cA;                     // v3: battery current, 0.01 A (positive = discharge)
  uint16_t vplug_pred_mV;              // v3: FM-PWR-01 predicted TVC servo plug voltage, both servos at stall
  uint16_t flags;                      // b0 latch b1 ign_en b2 spark b3 arm_req b4 arm_bus b5 link_ok b6 sol1 b7 sol2 b8 sol3 b9 mv_open b10 mv_closed
                                       // b11 dP/Pc ceiling b12 sol4 b13 sol5 b14 TVC supply degraded (v3) b15 heater permit (v3)
  uint16_t sat_ms;                     // v4 ENG-07b: duration of the actuator-saturation episode in progress [ms] (0 = none)
  uint8_t sat_flags;                   // v4: b0 7 deg limit b1 rate/accel shaping (context; v2.8.3 tracker) b2/b3 actuator A/B proxy b4 notch on
                                       // v5: b5 pintle back-off b6 pintle no progress >= 20 ms b7 pintle jam record pending
  uint8_t sat_long;                    // v4: episodes > 0.1 s since the last IGNITION entry (saturating at 255)
  float ptorch_Pa;                     // v6: torch chamber pressure, GAUGE [Pa] (NaN = invalid)
  uint16_t prail_mV;                   // v6: pintle rail, servo side of the LTC4365 [mV] (0xFFFF = invalid)
  int16_t pintle_i_mA;                 // v6: pintle rail current [mA] (INT16_MIN = no current sense)
  int16_t tcb_dK;                      // v6: bore-top / manifold TC, 0.1 K offset 273.15 K (INT16_MIN = not fitted/invalid)
  uint8_t seq_flags;                   // v6: b0 torch flame confirmed b1 timing-only bypass (armed or in use) b2 ignition window 0.65 s
                                       //     (v7: stand R3 or flight relight; v6: C7 extended) b3 relight lockout b4 MV seat wait b5 pintle
                                       //     rail lost b6 torch valves closed by event b7 last normal shutdown released the MV on the timeout
  uint8_t ign_check_cs;                // v7: ignition window W of the current start [10 ms FROM THE LIFT COMMAND] (0 = none);
                                       //   v6: deadline from IGNITION entry
  int16_t tcm1_dK;                     // v7: MSS-1 inlet-block state TC, 0.1 K offset 273.15 K (INT16_MIN = invalid / not fitted)
  int16_t tcm2_dK;                     // v7: MSS-2 NC-valve-outlet state TC (same coding)
  uint16_t fc_thr_dN;                  // v7: FC thrust estimate [0.1 N] when fresh and valid (0xFFFF = none)
  int16_t s1_dp_hPa;                   // v7: P_feed - P_tank - zero with the MV closed [hPa] (INT16_MIN = not evaluated)
  uint8_t seq2_flags;                  // v7: b0 direct relight (valve at E0) b1 superheat proven (R3) b2 S1 zero captured b3 S1 fault
                                       //     b4 FC thrust fresh b5 stand mode b6 mode mismatch after ARM b7 mode strap invalid
  uint8_t ign_rule;                    // v7: rule:: of the current/last start (1 R1, 2 R2, 3 R3, 5 flight relight)
  uint8_t ign_lift_ms;                 // v7: E0 -> ignition-lift command [ms] (0xFF = no lift yet in this start)
  uint8_t cmd_refused;                 // v7: refuse:: reason of the last refused start command (sticky until an accepted one)
  int16_t bay_dK;                      // v7: bay temperature at the TVC servo bracket (DS18B20 #3), 0.1 K offset 273.15 K (INT16_MIN = invalid)
  int16_t ttank_dK;                    // v8: interlock tank temperature max(wall DS18B20, Tsat(P_tank)), 0.1 K offset 273.15 K (INT16_MIN = none)
  uint8_t seq3_flags;                  // v8: b0-b1 relight state segstate:: (0 none 1 primed 2 unprimed 3 unknown) b2 vapour segment after an
                                       //     abort (NV b3) b3 tank interlock condition b4 tank cross-check flag b5 tank flag on a flight
                                       //     relight b6 MECO valve closure seen (TLM VALID basis) b7 (v9) coast pintle anomaly latched
                                       //     (encoder invalid or lift > 0.10 mm for 20 ms in COAST since the last light; RG-08)
  uint8_t hbleed_flags;                // v10: hb::F_* (fitted, path, V1 closed, leak, BIT pass, path flag, hold timeout, purge encoder)
  uint8_t hbleed_io;                   // v10: b0 V1 commanded open b1 V2 commanded open b2 P_mid high (comparator) b3 P_mid valid (ladder)
                                       //      b4-b7 hb::EV_* event of this tick (0 = none)
  uint8_t hbleed_bit;                  // v10: hb::BIT_* pad BIT state / result
  int16_t ign_ref_hPa;                 // v10: light-rule baseline P0, filtered gauge [hPa] (INT16_MIN = not captured in this start)
  int16_t ign_rise_hPa;                // v10: filtered rise over P0 in IGNITION [hPa] (INT16_MIN = outside / before E1)
  uint8_t ign_det;                     // v10: det:: flags (relative rule, P0 captured, ambient fallback, rise, floor, lit, E3, re-zero)
  uint8_t flame_ratio_pc;              // v10: A3 ratio (Pc - P0)/(Pc_map - P0) x 100 in RUN, clamped 0..254 (0xFF = outside RUN)
  uint16_t pc_map_hPa;                 // v10: A3 reference map min(40 ms lagged, instantaneous) lit-map Pc at the lift, absolute [hPa] (0xFFFF = outside IGNITION/RUN)
  uint8_t seq4_flags;                  // v10: b0-b1 a7:: phase b2 A7 flag (flight RUN) b3 A7 event this tick b4 E3 reached b5 re-zero accepted
                                       //      this tick b6 last re-zero rejected b7 this start came from PURGE
  uint8_t tlm_flags;                   // v10: tlmf:: drogue-release support bits (= TLM_FAST d1 b4-b7; b0-b3 zero)
  uint16_t crc16;                      // CRC-16/CCITT-FALSE over all previous bytes
};
#pragma pack(pop)
static_assert(sizeof(LogRecord) == 150, "log record size changed: bump version and decoder (v10 = 150; v8/v9 = 137 bytes; v7 = 134; v6 = 120; v4/v5 = 108)");
uint16_t crc16_ccitt(const uint8_t* p, int n);

// ----------------------------------------------------------------------------------- non-volatile pintle-jam record (v2.6)
// MECH/LEAD rule: any recorded pintle jam -> bearing A replaced before the next flight. The core produces the event
// (Outputs::pintle_jam_event, one tick) and the clear request (Outputs::maint_clear_jam); the HAL stores this record (Teensy
// 4.1 EEPROM emulation, two copies A/B, newest valid wins) and reports pending at boot in Inputs::maint_pintle_jam.
// Blank (all 0xFF, new board) = not pending; unreadable (magic/version/CRC) = PENDING (fail-safe) + evt::JAM_RECORD_BAD.
#pragma pack(push, 1)
struct NvJamRecord {
  uint16_t magic;        // 0x4A4D
  uint8_t version;       // 1
  uint8_t flags;         // b0 pending (ARM refused until CLEAR_JAM); b1 (v2.7) relight lockout pending (ARM refused until
                         //   CLEAR_LOCKOUT); b2 (v2.7) lit session open (set at the first light, cleared when a commanded
                         //   DISARM/SAFE safes the ECU; set at boot = the ECU was reset during or after a lit burn -> treated
                         //   as a lockout); b3 (v2.8 final) vapour segment after an abort (cleared at the next confirmed light);
                         //   other bits 0. A v2.6 decoder ignores b1-b3 (no lockout in v2.6)
  uint16_t count;        // jam events since the last CLEAR_JAM (saturating)
  uint16_t total;        // jam events ever recorded (saturating)
  uint32_t t_ms;         // ECU time of the last event [ms since boot]
  uint8_t state, kind;   // state at detection, jam:: kind
  int16_t cmd_um, meas_um;   // lift command / encoder lift at detection [um]
  int16_t i_mA;          // pintle rail current at detection [mA] (-1 = no current sense)
  uint16_t noprog_ms;    // time without progress at detection [ms]
  uint16_t clears;       // CLEAR_JAM count (bearing A replacements)
  uint8_t reserved[6];
  uint16_t crc16;        // CRC-16/CCITT-FALSE over the previous 30 bytes
};
#pragma pack(pop)
static_assert(sizeof(NvJamRecord) == 32, "NvJamRecord is 32 bytes");
enum class NvJamStatus : uint8_t { VALID = 0, BLANK = 1, CORRUPT = 2 };
NvJamRecord nvJamBlank();                                              // a valid, not-pending record (count 0)
NvJamRecord nvJamRecordEvent(const NvJamRecord& prev, const PintleJamEvent& e, uint32_t t_ms);   // pending, counts++
NvJamRecord nvJamClear(const NvJamRecord& prev);                       // not pending, count 0, clears++
NvJamStatus nvJamDecode(const uint8_t* p, NvJamRecord* out);           // 32 bytes as stored
inline bool nvJamPending(NvJamStatus st, const NvJamRecord& r) { return st == NvJamStatus::CORRUPT || (st == NvJamStatus::VALID && (r.flags & 1u)); }
// v2.7 relight lockout in the same record (b1): set / cleared without touching the jam fields; CORRUPT = pending (fail-safe).
// b2 lit-session marker: nvLitSessionSet / nvLitSessionClear (Outputs::lit_session_event / lit_session_close); a boot with b2 set
// is a pending lockout. nvLockoutClear (keyed CLEAR_LOCKOUT) clears b1 and b2.
NvJamRecord nvLockoutSet(const NvJamRecord& prev, uint32_t t_ms);
NvJamRecord nvLockoutClear(const NvJamRecord& prev);
NvJamRecord nvLitSessionSet(const NvJamRecord& prev);
NvJamRecord nvLitSessionClear(const NvJamRecord& prev);
inline bool nvLockoutPending(NvJamStatus st, const NvJamRecord& r) { return st == NvJamStatus::CORRUPT || (st == NvJamStatus::VALID && (r.flags & 6u)); }
// v2.8 final b3 vapour segment after an abort (COMB v2.4, LEAD 2026-10-13): set on Outputs::seg_vapour_event, cleared on
// Outputs::seg_vapour_clear (light confirmed); CORRUPT = pending (fail-safe: the next start is treated as a vapour-segment start)
NvJamRecord nvSegVapourSet(const NvJamRecord& prev);
NvJamRecord nvSegVapourClear(const NvJamRecord& prev);
inline bool nvSegVapourPending(NvJamStatus st, const NvJamRecord& r) { return st == NvJamStatus::CORRUPT || (st == NvJamStatus::VALID && (r.flags & 8u)); }
// HAL boot value of Inputs::nv_seg_vapour: b3, or b2 set at boot (an ECU reset during or after a lit burn: the NC valve and the pintle
// dropped as in an abort, so the segment is treated the same way), or CORRUPT
inline bool nvSegVapourAtBoot(NvJamStatus st, const NvJamRecord& r) { return nvSegVapourPending(st, r) || (st == NvJamStatus::VALID && (r.flags & 4u)); }

// ----------------------------------------------------------------------------------- non-volatile gimbal notch record (v2.6)
// LEAD 2026-10-12 (GNC csi_v3): the ENG-07d notch is REQUIRED, PER AXIS, set from the B-TVC-1 measurement in SAFE
// (Cmd::SET_GIMBAL_NOTCH / SET_GIMBAL_NOTCH_QD or EngineEcu::setGimbalNotchCal) and kept across power cycles. The core reports a
// change for one tick (Outputs::gimbal_cal_changed); the HAL then stores this record (Teensy 4.1 EEPROM emulation, two copies
// A/B, the valid copy with the higher seq wins) and applies it at boot with EngineEcu::setGimbalNotchCal (state SAFE).
// Blank (new board) = no notch; unreadable or out of range = no notch + evt::GIMBAL_CAL_BAD. Both leave IGNITE/RELIGHT refused
// (cfg::kIgnitionRequiresGimbalNotch) until the axes are set again - the fail-safe direction for a missing calibration.
#pragma pack(push, 1)
struct NvGimbalCal {
  uint16_t magic;          // 0x4743
  uint8_t version;         // 1
  uint8_t flags;           // b0 alpha notch enabled, b1 beta notch enabled
  uint16_t f0_cHz[2];      // centre frequency [0.01 Hz], [0] alpha (outer axis), [1] beta (inner axis)
  uint16_t q_milli[2];     // quality factor [0.001]
  int16_t depth_cdB[2];    // gain at f0 [0.01 dB] (negative)
  uint16_t seq;            // store counter (A/B selection), saturating
  uint32_t t_ms;           // ECU time of the store [ms since boot] (provenance only)
  uint8_t reserved[8];
  uint16_t crc16;          // CRC-16/CCITT-FALSE over the previous 30 bytes
};
#pragma pack(pop)
static_assert(sizeof(NvGimbalCal) == 32, "NvGimbalCal is 32 bytes");
enum class NvGimbalStatus : uint8_t { VALID = 0, BLANK = 1, CORRUPT = 2, OUT_OF_RANGE = 3 };
NvGimbalCal nvGimbalEncode(const GimbalNotchCal& c, uint16_t seq, uint32_t t_ms);   // values rounded to the record resolution
// 32 bytes as stored -> calibration (VALID only; otherwise *out = both axes disabled, the defaults)
NvGimbalStatus nvGimbalDecode(const uint8_t* p, GimbalNotchCal* out, NvGimbalCal* raw = nullptr);
inline bool nvGimbalBad(NvGimbalStatus st) { return st == NvGimbalStatus::CORRUPT || st == NvGimbalStatus::OUT_OF_RANGE; }

}  // namespace ecu
