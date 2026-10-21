// [v2.11 2026-10-13, LEAD CHANGELOG 205: absolute-transducer scaling, C1 / 070BG calibration defaults]
// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175: RE-19 ladder decode (short_gnd, OPEN+CLOSED invalid); full list in 06-electronics/REPORT-v2.10-HANDBACK.md] ARGOS engine ECU - pressure transducer scaling (v2.6, OI-6). See sensor_scale.h.
#include "sensor_scale.h"
#include "mv_ladder_table.h"

#include <cmath>

namespace ecu {
namespace xdcr {

float dividerGain(float r_top_ohm, float r_bot_ohm, float zin_ohm) {
  const float rb = zin_ohm > 0.0f ? r_bot_ohm * zin_ohm / (r_bot_ohm + zin_ohm) : r_bot_ohm;
  return rb / (r_top_ohm + rb);
}

float adcVolts(int32_t code) { return static_cast<float>(code) * (cfg::kAdcVref_V / cfg::kAdcCodeFs); }

float sigVolts(float v_ain, const XdcrCal& c) { return v_ain / c.k_div; }

float gaugePa(float v_sig, float v_exc, const XdcrCal& c) {
  const float p_nom = (v_sig / v_exc - c.zero_frac) / c.span_frac * c.fs_Pa;
  return c.gain_corr * p_nom + c.offset_Pa - c.abs_ref_Pa;   // v2.11: abs_ref_Pa = 0 for a gauge transducer
}

int32_t codeForGaugePa(float p_Pa, float v_exc, const XdcrCal& c) {
  const float p_nom = (p_Pa + c.abs_ref_Pa - c.offset_Pa) / c.gain_corr;
  const float v_sig = v_exc * (c.zero_frac + c.span_frac * p_nom / c.fs_Pa);
  const double fs = static_cast<double>(cfg::kAdcCodeFs);
  const double code = std::round(static_cast<double>(v_sig) * static_cast<double>(c.k_div) / static_cast<double>(cfg::kAdcVref_V) * fs);
  const double hi = fs - 1.0, lo = -fs;
  return static_cast<int32_t>(code > hi ? hi : (code < lo ? lo : code));
}

float paPerCount(float v_exc, const XdcrCal& c) {
  return c.gain_corr * (cfg::kAdcVref_V / cfg::kAdcCodeFs) / c.k_div / v_exc / c.span_frac * c.fs_Pa;
}

XdcrCal cal070BG() { return XdcrCal(); }

XdcrCal calXtl190(float pamb_Pa) {
  XdcrCal c;
  c.fs_Pa = cfg::kPcXdcrC1Fs_Pa; c.zero_frac = cfg::kPcXdcrC1ZeroFrac; c.span_frac = cfg::kPcXdcrC1SpanFrac;
  c.abs_ref_Pa = pamb_Pa;
  return c;
}

XdcrCal pcFlightCal(float pamb_Pa) { return cfg::kPcXdcrSel == 1 ? calXtl190(pamb_Pa) : cal070BG(); }

}  // namespace xdcr
namespace ladder {
LadderRead mvLadderDecode(float ratio) {
  LadderRead r;
  if (!(ratio >= kLadderShortRatio) || ratio > 1.05f) { r.short_gnd = ratio < kLadderShortRatio; return r; }   // short / NaN / range
  // v2.10 RE-19: the lowest window ends at its nominal minus its upper half-width (v2.9 ran it down to kLadderShortRatio)
  if (ratio < kLadderNom[0] - (kLadderThr[0] - kLadderNom[0])) { r.short_gnd = true; return r; }
  int k = 0;
  while (k < kLadderN - 1 && ratio > kLadderThr[k]) ++k;
  const uint8_t b = kLadderBits[k];
  if (!(b & 8u)) return r;
  if ((b & 3u) == 3u) { r.both_sw = true; return r; }   // v2.10 RE-19: OPEN + CLOSED is not a valid state
  r.valid = true; r.open_sw = b & 1u; r.closed_sw = b & 2u; r.pmid_hi = b & 4u;
  return r;
}
float nominalRatio(bool open_sw, bool closed_sw, bool pmid_hi) {
  const uint8_t want = static_cast<uint8_t>(8u | (open_sw ? 1u : 0u) | (closed_sw ? 2u : 0u) | (pmid_hi ? 4u : 0u));
  for (int k = 0; k < kLadderN; ++k) if (kLadderBits[k] == want) return kLadderNom[k];
  return __builtin_nanf("");
}
}  // namespace ladder
}  // namespace ecu
