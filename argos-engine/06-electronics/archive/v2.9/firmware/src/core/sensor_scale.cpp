// ARGOS engine ECU - pressure transducer scaling (v2.6, OI-6). See sensor_scale.h.
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
  return c.gain_corr * p_nom + c.offset_Pa;
}

int32_t codeForGaugePa(float p_Pa, float v_exc, const XdcrCal& c) {
  const float p_nom = (p_Pa - c.offset_Pa) / c.gain_corr;
  const float v_sig = v_exc * (c.zero_frac + c.span_frac * p_nom / c.fs_Pa);
  const double fs = static_cast<double>(cfg::kAdcCodeFs);
  const double code = std::round(static_cast<double>(v_sig) * static_cast<double>(c.k_div) / static_cast<double>(cfg::kAdcVref_V) * fs);
  const double hi = fs - 1.0, lo = -fs;
  return static_cast<int32_t>(code > hi ? hi : (code < lo ? lo : code));
}

float paPerCount(float v_exc, const XdcrCal& c) {
  return c.gain_corr * (cfg::kAdcVref_V / cfg::kAdcCodeFs) / c.k_div / v_exc / c.span_frac * c.fs_Pa;
}

}  // namespace xdcr
namespace ladder {
LadderRead mvLadderDecode(float ratio) {
  LadderRead r;
  if (!(ratio >= kLadderShortRatio) || ratio > 1.05f) return r;   // short to GND / NaN / out of range
  int k = 0;
  while (k < kLadderN - 1 && ratio > kLadderThr[k]) ++k;
  const uint8_t b = kLadderBits[k];
  if (!(b & 8u)) return r;
  r.valid = true; r.open_sw = b & 1u; r.closed_sw = b & 2u; r.pmid_hi = b & 4u;
  return r;
}
}  // namespace ladder
}  // namespace ecu
