// ARGOS engine ECU - protocol implementation (v2.8.2: frames unchanged, log v9 written by engine_ecu.cpp; v2.8 final: TLM_RELIGHT states PRIMED/UNPRIMED/UNKNOWN + POST_ABORT, NV b3, log v8; v2.8: FC_THRUST frame; v2.7: relight lockout and lit-session marker in the NV record;
// v2.6: non-volatile pintle-jam and gimbal-notch records)
#include "protocol.h"
#include <cmath>

namespace ecu {
namespace can {

uint8_t crc8(const uint8_t* p, int n) {
  uint8_t c = 0xFF;
  for (int i = 0; i < n; ++i) {
    c ^= p[i];
    for (int b = 0; b < 8; ++b) c = (c & 0x80) ? static_cast<uint8_t>((c << 1) ^ 0x1D) : static_cast<uint8_t>(c << 1);
  }
  return static_cast<uint8_t>(c ^ 0xFF);
}

static void put16(uint8_t* d, uint16_t v) { d[0] = v & 0xFF; d[1] = v >> 8; }
static void puts16(uint8_t* d, int16_t v) { put16(d, static_cast<uint16_t>(v)); }
static uint16_t get16(const uint8_t* d) { return static_cast<uint16_t>(d[0] | (d[1] << 8)); }
static int16_t gets16(const uint8_t* d) { return static_cast<int16_t>(get16(d)); }
static int16_t radToMdeg(float r) {
  float v = r * 57295.78f;
  if (v > 32767.f) v = 32767.f;
  if (v < -32768.f) v = -32768.f;
  return static_cast<int16_t>(std::lround(v));
}

Frame encodeCmdFast(uint8_t seq, float thrust_N, float ga, float gb) {
  Frame f; f.id = ID_CMD_FAST; f.len = 8;
  float dn = thrust_N * 10.f; if (dn < 0) dn = 0; if (dn > 65535.f) dn = 65535.f;
  f.d[0] = seq; put16(&f.d[1], static_cast<uint16_t>(std::lround(dn)));
  puts16(&f.d[3], radToMdeg(ga)); puts16(&f.d[5], radToMdeg(gb));
  f.d[7] = crc8(f.d, 7);
  return f;
}
Frame encodeCmdState(uint8_t seq, Cmd c, uint16_t arg) {
  Frame f; f.id = ID_CMD_STATE; f.len = 7;
  f.d[0] = seq; f.d[1] = static_cast<uint8_t>(c); put16(&f.d[2], arg); put16(&f.d[4], keyFor(c));
  f.d[6] = crc8(f.d, 6);
  return f;
}
Frame encodeAbort(uint8_t seq, uint8_t code) {
  Frame f; f.id = ID_ABORT; f.len = 5;
  f.d[0] = 0xA5; f.d[1] = 0x5A; f.d[2] = code; f.d[3] = seq; f.d[4] = crc8(f.d, 4);
  return f;
}

Frame encodeFcThrust(uint8_t seq, float thrust_N, bool valid) {   // v2.8
  Frame f; f.id = ID_FC_THRUST; f.len = 5;
  float dn = thrust_N * 10.f; if (dn < 0) dn = 0; if (dn > 65535.f) dn = 65535.f;
  f.d[0] = seq; put16(&f.d[1], static_cast<uint16_t>(std::lround(dn))); f.d[3] = valid ? 1u : 0u;
  f.d[4] = crc8(f.d, 4);
  return f;
}

Frame encodeCmdAux(uint8_t seq, uint8_t roll_bits) {
  Frame f; f.id = ID_CMD_AUX; f.len = 4;
  f.d[0] = seq; f.d[1] = roll_bits; f.d[2] = static_cast<uint8_t>(~roll_bits); f.d[3] = crc8(f.d, 3);
  return f;
}

bool Decoder::seqOk(int idx, uint8_t seq) {
  // accept any first frame; afterwards reject exact repeats (stale/replayed buffer)
  if (have_seq_[idx] && seq == last_seq_[idx]) return false;
  have_seq_[idx] = true; last_seq_[idx] = seq;
  return true;
}

bool Decoder::accept(const Frame& f, Commands& out) {
  switch (f.id) {
    case ID_CMD_FAST: {
      if (f.len != 8) { ++rejected_len; return false; }
      if (crc8(f.d, 7) != f.d[7]) { ++rejected_crc; return false; }
      if (!seqOk(0, f.d[0])) { ++rejected_seq; return false; }
      out.fast_valid = true;
      out.thrust_sp_N = get16(&f.d[1]) * 0.1f;
      out.gimbal_cmd_rad[0] = gets16(&f.d[3]) / 57295.78f;
      out.gimbal_cmd_rad[1] = gets16(&f.d[5]) / 57295.78f;
      return true;
    }
    case ID_CMD_STATE: {
      if (f.len != 7) { ++rejected_len; return false; }
      if (crc8(f.d, 6) != f.d[6]) { ++rejected_crc; return false; }
      const Cmd c = static_cast<Cmd>(f.d[1]);
      if (get16(&f.d[4]) != keyFor(c)) { ++rejected_key; return false; }
      if (!seqOk(1, f.d[0])) { ++rejected_seq; return false; }
      out.state_valid = true; out.cmd = c; out.arg = get16(&f.d[2]);
      return true;
    }
    case ID_CMD_AUX: {
      if (f.len != 4) { ++rejected_len; return false; }
      if (crc8(f.d, 3) != f.d[3]) { ++rejected_crc; return false; }
      if (static_cast<uint8_t>(~f.d[1]) != f.d[2]) { ++rejected_key; return false; }   // complement copy
      if (!seqOk(3, f.d[0])) { ++rejected_seq; return false; }
      out.aux_valid = true; out.roll_bits = f.d[1] & 0x03;
      return true;
    }
    case ID_FC_THRUST: {   // v2.8
      if (f.len != 5) { ++rejected_len; return false; }
      if (crc8(f.d, 4) != f.d[4]) { ++rejected_crc; return false; }
      if ((f.d[3] & ~1u) != 0) { ++rejected_key; return false; }   // undefined flag bits set
      if (!seqOk(2, f.d[0])) { ++rejected_seq; return false; }
      out.fc_thrust_valid = true; out.fc_thrust_N = get16(&f.d[1]) * 0.1f; out.fc_thrust_ok = (f.d[3] & 1u) != 0;
      return true;
    }
    case ID_ABORT: {
      if (f.len != 5 || f.d[0] != 0xA5 || f.d[1] != 0x5A) { ++rejected_len; return false; }
      if (crc8(f.d, 4) != f.d[4]) { ++rejected_crc; return false; }
      out.abort_frame = true;   // no sequence check: repeats of an abort are welcome
      return true;
    }
    default: return false;
  }
}

Frame encodeTlmFast(uint8_t seq, const Outputs& o, float pc, float pintle) {
  Frame f; f.id = ID_TLM_FAST; f.len = 8;
  f.d[0] = seq; f.d[1] = static_cast<uint8_t>(o.state);
  // v2.8.2 (GNC RG-15): 0xFFFF = Pc channel invalid this tick (o.pc_valid false); valid readings clamp to 0..65534 kPa
  float kpa = pc / 1000.f; if (!(kpa > 0)) kpa = 0; if (kpa > 65534.f) kpa = 65534.f;
  put16(&f.d[2], o.pc_valid ? static_cast<uint16_t>(std::lround(kpa)) : static_cast<uint16_t>(0xFFFFu));
  float um = pintle * 1e6f; if (um < 0) um = 0;
  put16(&f.d[4], static_cast<uint16_t>(std::lround(um)));
  put16(&f.d[6], o.fault_bits);
  return f;
}
Frame encodeTlmGimbal(uint8_t seq, uint8_t flags, const float m[2], float thrust) {
  Frame f; f.id = ID_TLM_GIMBAL; f.len = 8;
  f.d[0] = seq; f.d[1] = flags; puts16(&f.d[2], radToMdeg(m[0])); puts16(&f.d[4], radToMdeg(m[1]));
  // v2.8.2 (GNC RG-15): NaN (HAL passes can::tlmThrust(o): NaN while the Pc channel is invalid) -> 0xFFFF; else 0..65534 (0.1 N)
  float d = thrust * 10.f; if (d < 0) d = 0; if (d > 65534.f) d = 65534.f;
  put16(&f.d[6], std::isnan(thrust) ? static_cast<uint16_t>(0xFFFFu) : static_cast<uint16_t>(std::lround(d)));
  return f;
}
Frame encodeEvent(uint8_t code, State s, uint32_t t_ms, uint16_t arg) {
  Frame f; f.id = ID_EVENT; f.len = 8;
  f.d[0] = code; f.d[1] = static_cast<uint8_t>(s);
  f.d[2] = t_ms & 0xFF; f.d[3] = (t_ms >> 8) & 0xFF; f.d[4] = (t_ms >> 16) & 0xFF; f.d[5] = (t_ms >> 24) & 0xFF;
  put16(&f.d[6], arg);
  return f;
}

// v2.8 TLM_RELIGHT
Frame encodeTlmRelight(uint8_t seq, const Outputs& o) {
  Frame f; f.id = ID_TLM_RELIGHT; f.len = 8;
  f.d[0] = seq; f.d[1] = static_cast<uint8_t>(o.state);
  const uint8_t rs = o.relight_state;   // v2.8 final: segstate:: (NONE / PRIMED / UNPRIMED / UNKNOWN)
  f.d[2] = static_cast<uint8_t>((rs == segstate::PRIMED ? tlmr::PRIMED : 0u) | (rs != segstate::NONE ? tlmr::VALID : 0u) |
                                ((o.state == State::COAST && o.relight_block == refuse::NONE) ? tlmr::READY : 0u) |
                                (o.relight_lockout ? tlmr::LOCKOUT : 0u) | (o.s1_fault ? tlmr::S1_FAULT : 0u) |
                                (o.mode_stand ? tlmr::STAND : 0u) | (o.seg_vapour ? tlmr::POST_ABORT : 0u) |
                                (rs == segstate::UNKNOWN ? tlmr::UNKNOWN : 0u));
  put16(&f.d[3], o.relight_worst_ms);
  const float pct = o.seg_ratio * 100.0f;
  f.d[5] = (o.seg_valid && std::isfinite(pct)) ? static_cast<uint8_t>(std::lround(pct < 0.0f ? 0.0f : (pct > 254.0f ? 254.0f : pct))) : 0xFFu;
  f.d[6] = o.relight_block;
  f.d[7] = crc8(f.d, 7);
  return f;
}
bool decodeTlmRelight(const Frame& f, TlmRelight* r) {
  if (f.id != ID_TLM_RELIGHT || f.len != 8 || crc8(f.d, 7) != f.d[7]) return false;
  // v2.8 final invariants: PRIMED or UNKNOWN only with VALID; never PRIMED with UNKNOWN; never PRIMED after an abort (POST_ABORT)
  const uint8_t fl = f.d[2];
  if (((fl & (tlmr::PRIMED | tlmr::UNKNOWN)) && !(fl & tlmr::VALID)) || ((fl & tlmr::PRIMED) && (fl & (tlmr::UNKNOWN | tlmr::POST_ABORT)))) return false;
  r->seq = f.d[0]; r->state = f.d[1]; r->flags = f.d[2];
  r->worst_ms = static_cast<uint16_t>(f.d[3] | (f.d[4] << 8)); r->ratio_pct = f.d[5]; r->block = f.d[6];
  return true;
}

}  // namespace can

uint16_t crc16_ccitt(const uint8_t* p, int n) {
  uint16_t c = 0xFFFF;
  for (int i = 0; i < n; ++i) {
    c ^= static_cast<uint16_t>(p[i]) << 8;
    for (int b = 0; b < 8; ++b) c = (c & 0x8000) ? static_cast<uint16_t>((c << 1) ^ 0x1021) : static_cast<uint16_t>(c << 1);
  }
  return c;
}

// ------------------------------------------------------------------------------------ non-volatile jam record (v2.6)
static void nvSeal(NvJamRecord& r) { r.crc16 = crc16_ccitt(reinterpret_cast<const uint8_t*>(&r), sizeof(NvJamRecord) - 2); }
static int16_t sat16(float v) { return static_cast<int16_t>(std::lround(v > 32767.f ? 32767.f : (v < -32768.f ? -32768.f : v))); }

NvJamRecord nvJamBlank() {
  NvJamRecord r;
  std::memset(&r, 0, sizeof r);
  r.magic = 0x4A4D; r.version = 1; r.i_mA = -1;
  nvSeal(r);
  return r;
}
NvJamRecord nvJamRecordEvent(const NvJamRecord& prev, const PintleJamEvent& e, uint32_t t_ms) {
  NvJamRecord r = prev;
  r.magic = 0x4A4D; r.version = 1;
  r.flags |= 1u;
  if (r.count < 0xFFFFu) ++r.count;
  if (r.total < 0xFFFFu) ++r.total;
  r.t_ms = t_ms; r.state = e.state; r.kind = e.kind;
  r.cmd_um = sat16(e.cmd_m * 1e6f); r.meas_um = sat16(e.meas_m * 1e6f);
  r.i_mA = e.i_A < 0.0f ? static_cast<int16_t>(-1) : sat16(e.i_A * 1e3f);
  const float np = e.noprog_s * 1e3f;
  r.noprog_ms = static_cast<uint16_t>(np < 0.f ? 0.f : (np > 65535.f ? 65535.f : np));
  nvSeal(r);
  return r;
}
NvJamRecord nvJamClear(const NvJamRecord& prev) {
  NvJamRecord r = prev;
  r.magic = 0x4A4D; r.version = 1;
  r.flags &= static_cast<uint8_t>(~1u); r.count = 0;
  if (r.clears < 0xFFFFu) ++r.clears;
  nvSeal(r);
  return r;
}
// v2.7 relight lockout (flags b1); the jam fields and counters are kept
NvJamRecord nvLockoutSet(const NvJamRecord& prev, uint32_t t_ms) {
  NvJamRecord r = prev;
  r.magic = 0x4A4D; r.version = 1;
  r.flags |= 2u;
  (void)t_ms;   // the jam event time stays in t_ms; the lockout time is in the log and the EVENT frame
  nvSeal(r);
  return r;
}
NvJamRecord nvLockoutClear(const NvJamRecord& prev) {
  NvJamRecord r = prev;
  r.magic = 0x4A4D; r.version = 1;
  r.flags &= static_cast<uint8_t>(~6u);   // b1 lockout and b2 lit-session marker
  nvSeal(r);
  return r;
}
NvJamRecord nvLitSessionSet(const NvJamRecord& prev) {
  NvJamRecord r = prev;
  r.magic = 0x4A4D; r.version = 1;
  r.flags |= 4u;
  nvSeal(r);
  return r;
}
NvJamRecord nvLitSessionClear(const NvJamRecord& prev) {
  NvJamRecord r = prev;
  r.magic = 0x4A4D; r.version = 1;
  r.flags &= static_cast<uint8_t>(~4u);
  nvSeal(r);
  return r;
}
// v2.8 final b3: vapour segment after an abort (COMB v2.4 / LEAD 2026-10-13)
NvJamRecord nvSegVapourSet(const NvJamRecord& prev) {
  NvJamRecord r = prev;
  r.magic = 0x4A4D; r.version = 1;
  r.flags |= 8u;
  nvSeal(r);
  return r;
}
NvJamRecord nvSegVapourClear(const NvJamRecord& prev) {
  NvJamRecord r = prev;
  r.magic = 0x4A4D; r.version = 1;
  r.flags &= static_cast<uint8_t>(~8u);
  nvSeal(r);
  return r;
}
NvJamStatus nvJamDecode(const uint8_t* p, NvJamRecord* out) {
  bool blank = true;
  for (size_t i = 0; i < sizeof(NvJamRecord); ++i) blank = blank && p[i] == 0xFF;
  if (blank) { *out = nvJamBlank(); return NvJamStatus::BLANK; }
  std::memcpy(out, p, sizeof(NvJamRecord));
  if (out->magic != 0x4A4D || out->version != 1 || crc16_ccitt(p, sizeof(NvJamRecord) - 2) != out->crc16) return NvJamStatus::CORRUPT;
  return NvJamStatus::VALID;
}

// ------------------------------------------------------------------------------- non-volatile gimbal notch record (v2.6)
static uint16_t satU16(float v) { return static_cast<uint16_t>(std::lround(v < 0.f ? 0.f : (v > 65535.f ? 65535.f : v))); }

NvGimbalCal nvGimbalEncode(const GimbalNotchCal& c, uint16_t seq, uint32_t t_ms) {
  NvGimbalCal r;
  std::memset(&r, 0, sizeof r);
  r.magic = 0x4743; r.version = 1;
  r.flags = static_cast<uint8_t>((c.ax[0].enabled ? 1u : 0u) | (c.ax[1].enabled ? 2u : 0u));
  for (int k = 0; k < 2; ++k) {
    r.f0_cHz[k] = satU16(c.ax[k].f0_Hz * 100.0f);
    r.q_milli[k] = satU16(c.ax[k].q * 1000.0f);
    r.depth_cdB[k] = sat16(c.ax[k].depth_dB * 100.0f);
  }
  r.seq = seq; r.t_ms = t_ms;
  r.crc16 = crc16_ccitt(reinterpret_cast<const uint8_t*>(&r), sizeof(NvGimbalCal) - 2);
  return r;
}

NvGimbalStatus nvGimbalDecode(const uint8_t* p, GimbalNotchCal* out, NvGimbalCal* raw) {
  *out = GimbalNotchCal();
  bool blank = true;
  for (size_t i = 0; i < sizeof(NvGimbalCal); ++i) blank = blank && p[i] == 0xFF;
  if (blank) return NvGimbalStatus::BLANK;
  NvGimbalCal r;
  std::memcpy(&r, p, sizeof r);
  if (raw) *raw = r;
  if (r.magic != 0x4743 || r.version != 1 || crc16_ccitt(p, sizeof(NvGimbalCal) - 2) != r.crc16 || (r.flags & ~3u) != 0)
    return NvGimbalStatus::CORRUPT;
  GimbalNotchCal c;
  for (int k = 0; k < 2; ++k) {
    c.ax[k].enabled = (r.flags >> k) & 1u;
    c.ax[k].f0_Hz = 0.01f * static_cast<float>(r.f0_cHz[k]);
    c.ax[k].q = 0.001f * static_cast<float>(r.q_milli[k]);
    c.ax[k].depth_dB = 0.01f * static_cast<float>(r.depth_cdB[k]);
    NotchAxis chk = c.ax[k]; chk.enabled = true;   // a stored disabled axis must still carry valid values
    if (!chk.valid(cfg::kDt_s)) return NvGimbalStatus::OUT_OF_RANGE;
  }
  *out = c;
  return NvGimbalStatus::VALID;
}

}  // namespace ecu
