// ARGOS engine ECU - pressure transducer scaling (v2.6, 2026-10-12, OI-6). Platform independent: the Teensy HAL calls these
// with the ADS131M04 codes (4:1 averaged to 1 kHz) and fills Inputs::pc_Pa / pc_raw_V; the unit tests pin the numbers and
// calc/pc_transducer_v2.py reproduces them. Chain (hardware/kicad_gen/ecu_design.py):
//   TE M3234-000005-070BG (0-70 bar g; 0.5-4.5 V ratiometric on +5V_SNS) -> divider 12.7k/4.02k 0.1 % loaded by the ADC input impedance
//   -> 22 nF anti-alias -> ADS131M04 gain 1 (+/-1.2 V internal reference, 24 bit, OSR 1024 = 4 kSPS) -> HAL 4:1 boxcar.
// Calibration: the B-PC-1 bench run (flight ECU, flight +5V_SNS, reference gauge, N2 0-70 bar g) fits gain_corr/offset_Pa
// end to end; the ARMED auto-zero (engine_ecu.cpp) then removes the zero drift at the pad temperature before every start.
#pragma once
#include <cstdint>
#include "config.h"

namespace ecu {
namespace xdcr {

// V_ain / V_sig: r_bot in parallel with the ADC input impedance zin (zin <= 0: unloaded)
float dividerGain(float r_top_ohm, float r_bot_ohm, float zin_ohm);

struct XdcrCal {
  float fs_Pa = cfg::kPcXdcrFs_Pa;            // range-code full scale, gauge (baseline 070BG 70e5; alternate 01KPG 68.9476e5)
  float zero_frac = cfg::kPcXdcrZeroFrac;     // [DS] output at 0 = 10 % of the excitation
  float span_frac = cfg::kPcXdcrSpanFrac;     // [DS] 0 -> FS spans 80 % of the excitation
  float k_div = dividerGain(cfg::kXdcrDivRtop_ohm, cfg::kXdcrDivRbot_ohm, cfg::kAdcZin_ohm);   // [DERIVED] 0.23822
  float gain_corr = 1.0f;                     // B-PC-1: p = gain_corr * p_nominal + offset_Pa
  float offset_Pa = 0.0f;
  // bounds: a record outside them is refused (the HAL keeps the defaults and flags the calibration)
  bool valid() const {
    return fs_Pa >= 1.0e5f && fs_Pa <= 2.0e7f && zero_frac > 0.05f && zero_frac < 0.15f && span_frac > 0.7f &&
           span_frac < 0.9f && k_div > 0.20f && k_div < 0.30f && gain_corr > 0.95f && gain_corr < 1.05f &&
           offset_Pa > -0.02f * fs_Pa && offset_Pa < 0.02f * fs_Pa;
  }
};

float adcVolts(int32_t code);                                   // ADS131M04 code -> differential input voltage [V]
float sigVolts(float v_ain, const XdcrCal& c);                  // transducer output voltage [V] (fault window, OVP)
float gaugePa(float v_sig, float v_exc, const XdcrCal& c);      // gauge pressure [Pa]; v_exc = +5V_SNS (nominal 5.0 V unless
                                                                //   the A5 relative correction is enabled)
int32_t codeForGaugePa(float p_Pa, float v_exc, const XdcrCal& c);   // inverse (tests, bench tables); saturates at +/-FS
inline bool excitationOk(float v_exc) { return v_exc >= cfg::kXdcrExcMin_V && v_exc <= cfg::kXdcrExcMax_V; }
// one ADC LSB expressed in pressure at the given excitation [Pa/count]
float paPerCount(float v_exc, const XdcrCal& c);

}  // namespace xdcr

// v2.9 MV switch + head-end bleed P_mid resistor ladder on Teensy pin 23 (A9), values and windows from calc/hbleed_provision_v1.py
// (mv_ladder_table.h, generated). ratio = V_pin / V_ref (pull-up on the ADC reference). An invalid code (short to GND, harness open, the
// node above the last window) returns valid = false with every switch false (the HAL then sets pmid_valid = false and both MV switches
// false; the existing MV-switch fault paths apply).
namespace ladder {
struct LadderRead { bool open_sw = false, closed_sw = false, pmid_hi = false, valid = false; };
LadderRead mvLadderDecode(float ratio);
}  // namespace ladder
}  // namespace ecu
