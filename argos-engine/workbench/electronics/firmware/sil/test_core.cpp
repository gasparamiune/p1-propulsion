// [v2.11 2026-10-13, LEAD CHANGELOG 203/205: test_v211.inc (above-FS, non-sticky over-range, ride-through CANDIDATE, cap 2.55 s, C1 scaling); test (17) unpurged guard; log v12; JSON version label v2.11 (was the stale v2.8.3)]
// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175/181/186: test_v210.inc (v210-16 181 (4), v210-17 186 (2) R2 command hold); full list in 06-electronics/REPORT-v2.10-HANDBACK.md] ARGOS engine ECU - unit tests of the platform-independent core (v2.8.3, 2026-10-13: gnc.json v3 TVC tracker - group (26) of
// sil/test_v28.inc, flight-chain ramp lag, the linear chain-gain checks run with the tracker off; v2.8.1/v2.8.2 groups (21)-(25);
// the JSON "version" field said "v2.8 final" through v2.8.2 - corrected here; v2.8 final, 2026-10-13: COMB v2.4 / GNC v3 / MECH fold-in - seat
// timeout 0.30 s and planned cut-off, post-abort vapour segment, tank interlock, RUN-entry reference, TLM_RELIGHT VALID/UNKNOWN/POST_ABORT,
// groups (13) and (15)-(20) of sil/test_v28.inc; v2.8, 2026-10-13: lead decisions on the relight path, ignition windows R1-R4, S1,
// over-thrust, mode strap, case/bay temperature, TLM_RELIGHT, sil/test_v28.inc; v2.7, 2026-10-13: Combustion review fold-in,
// sil/test_v27.inc; v2.6, 2026-10-12).
// v2.6: the test rigs read the pintle encoder (ARM requires it, LEAD stall monitor): an ideal follower (lift = previous tick's
// command) unless a test injects a stuck/runaway needle (follow = false).
// Build/run: make test   (or g++ -std=c++17 -Isrc/core -Isil sil/test_core.cpp src/core/*.cpp -o build/test_core)
// Exit code 0 = all checks passed. Output: one line per check + summary; ../results/sil/test_core.json.
#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <functional>
#include <limits>
#include <string>
#include <vector>
#include <cstdarg>
#include "control.h"
#include "engine_ecu.h"
#include "n2o_sat_table.h"
#include "protocol.h"
#include "sensor_scale.h"
#include "mv_ladder_table.h"
#include "valve_map_table.h"

using namespace ecu;
static int n_pass = 0, n_fail = 0;
static std::vector<std::string> lines;
static void check(bool ok, const std::string& name, const std::string& detail = "") {
  (ok ? n_pass : n_fail)++;
  const std::string l = std::string(ok ? "PASS " : "FAIL ") + name + (detail.empty() ? "" : "  [" + detail + "]");
  std::printf("%s\n", l.c_str());
  lines.push_back(l);
}
static std::string fmt(const char* f, double a, double b = 0, double c = 0) { char s[200]; std::snprintf(s, sizeof s, f, a, b, c); return s; }
// v2.10: variadic detail formatter (more than three values; doubles only, as fmt)
static std::string fmtv(const char* f, ...) { char s[480]; va_list ap; va_start(ap, f); std::vsnprintf(s, sizeof s, f, ap); va_end(ap); return s; }
static std::string hex(unsigned v, int w) { char s[32]; std::snprintf(s, sizeof s, "got 0x%0*X", w, v); return s; }

// v2.6 LEAD (GNC csi_v3): the ENG-07d notch is REQUIRED per axis before IGNITE/RELIGHT. Rigs that ignite load a B-TVC-1-like
// calibration first. TEST VALUES, not measurements: alpha 22.0 Hz Q 1.0 -12 dB, beta 25.3 Hz (+15 %) Q 1.4 -15 dB.
static GimbalNotchCal testNotchCal() {
  GimbalNotchCal c;
  c.ax[0].enabled = true; c.ax[0].f0_Hz = 22.0f; c.ax[0].q = 1.0f; c.ax[0].depth_dB = -12.0f;
  c.ax[1].enabled = true; c.ax[1].f0_Hz = 25.3f; c.ax[1].q = 1.4f; c.ax[1].depth_dB = -15.0f;
  return c;
}
// v2.9: unlit (cold-flow) plateau used by the no-light tests: P0 + 0.70 bar (1.71 bar abs), below the LEAD-adopted 0.8 bar rise and the
// 1.8 bar abs floor (COMB unlit bound 1.42-1.45 bar abs). v2.6-v2.8.3 tests used 2.9 bar abs (below the withdrawn 3.0 bar abs rule).
static constexpr float kUnlitAbs = 101325.f + 0.70e5f;
// v2.9: lit-start plateau used to bring the rigs to RUN before setting their RUN pressure (A5 aborts above 8 bar abs in the hold)
static constexpr float kLitStartAbs = 2.6e5f;
static bool loadNotch(EngineEcu& e) { return e.setGimbalNotchCal(testNotchCal()); }
// v2.7 ideal torch for the rigs (RC-01 gate): the torch chamber reads 2.0 bar g (lit) one tick after BOTH torch valves are
// commanded open; otherwise it follows the chamber (the torch exhausts into it)
// v2.10 FA-1: the rigs' photodiode reads lit (1.0 V) while the torch burns (both torch valves open) or the engine runs, else dark (0.10 V)
static constexpr float kPhotoDarkRig_V = 0.10f, kPhotoLitRig_V = 1.0f;
static void idealTorch(Inputs& in, const Outputs& o) {
  in.ptorch_valid = true; in.ptorch_Pa = (o.sol[0] && o.sol[1]) ? 2.0e5f : std::fmax(0.0f, in.pc_Pa);
  in.photo_valid = true; in.photo_V = ((o.sol[0] && o.sol[1]) || o.state == State::RUN) ? kPhotoLitRig_V : kPhotoDarkRig_V;
}
// digital response of one Notch2 section at f [Hz] (independent expected value for the per-axis checks)
static double notchMagDb(float f0, float q, float depth_dB, double f, double dt = 1e-3) {
  Notch2 n; n.setup(f0, q, depth_dB, static_cast<float>(dt));
  const std::complex<double> zi = std::exp(std::complex<double>(0.0, -2.0 * M_PI * f * dt));
  const std::complex<double> H = (static_cast<double>(n.b0) + static_cast<double>(n.b1) * zi + static_cast<double>(n.b2) * zi * zi) /
                                 (1.0 + static_cast<double>(n.a1) * zi + static_cast<double>(n.a2) * zi * zi);
  return 20.0 * std::log10(std::abs(H));
}

int main(int argc, char** argv) {
  const std::string out = argc > 1 ? argv[1] : "../results/sil";
  // ------------------------------------------------------------- checksums (catalogue check values)
  const uint8_t msg[9] = {'1', '2', '3', '4', '5', '6', '7', '8', '9'};
  check(can::crc8(msg, 9) == 0x4B, "CRC-8/SAE-J1850 check value 0x4B", hex(can::crc8(msg, 9), 2));
  check(crc16_ccitt(msg, 9) == 0x29B1, "CRC-16/CCITT-FALSE check value 0x29B1", hex(crc16_ccitt(msg, 9), 4));
  check(sizeof(LogRecord) == 180 && kLogVersion == 12, "LogRecord v12 is 180 bytes (v2.11: + ovr_flags; 1 kHz x 180 B = 180 kB/s to SD; v11 179 B, v10 150 B, v8/v9 137 B, v7 134 B, v6 120 B)");
  check(can::keyFor(Cmd::ARM) == 0xA55B && can::keyFor(Cmd::IGNITE) == 0xA55E, "2-key state command keys");

  // ------------------------------------------------------------- frame codec and supervision
  {
    can::Decoder dec; Commands c;
    can::Frame f = can::encodeCmdFast(1, 123.4f, 0.05f, -0.02f);
    const bool ok1 = dec.accept(f, c);
    check(ok1 && std::fabs(c.thrust_sp_N - 123.4f) < 0.051f && std::fabs(c.gimbal_cmd_rad[0] - 0.05f) < 2e-5f && std::fabs(c.gimbal_cmd_rad[1] + 0.02f) < 2e-5f,
          "CMD_FAST round trip (0.1 N, 1 mdeg quantisation)", fmt("F %.2f N", c.thrust_sp_N));
    check(!dec.accept(f, c) && dec.rejected_seq == 1, "CMD_FAST repeated sequence rejected (stale buffer)");
    can::Frame g = can::encodeCmdFast(2, 200.f, 0, 0); g.d[3] ^= 0x10;
    check(!dec.accept(g, c) && dec.rejected_crc == 1, "CMD_FAST corrupted payload rejected by CRC-8");
    can::Frame h = can::encodeCmdFast(3, 200.f, 0, 0); h.len = 7;
    check(!dec.accept(h, c) && dec.rejected_len == 1, "CMD_FAST wrong length rejected");
    can::Frame s = can::encodeCmdState(5, Cmd::IGNITE, 0); s.d[4] ^= 0x01; s.d[6] = can::crc8(s.d, 6);
    check(!dec.accept(s, c) && dec.rejected_key == 1, "CMD_STATE with wrong key rejected (valid CRC)");
    can::Frame a = can::encodeAbort(9, 1);
    Commands c2; const bool a1 = dec.accept(a, c2); Commands c3; const bool a2 = dec.accept(a, c3);
    check(a1 && a2 && c2.abort_frame && c3.abort_frame, "ABORT frame accepted on repeat (no sequence check)");
    can::Frame r1 = can::encodeCmdAux(4, 0x01); Commands c4;
    check(dec.accept(r1, c4) && c4.aux_valid && c4.roll_bits == 1, "CMD_AUX roll frame accepted");
    can::Frame r2 = can::encodeCmdAux(5, 0x02); r2.d[2] ^= 0x04; r2.d[3] = can::crc8(r2.d, 3); Commands c5;
    check(!dec.accept(r2, c5), "CMD_AUX with broken complement copy rejected (valid CRC)");
    // exhaustive single- and double-bit corruption of one CMD_FAST frame (64 data bits incl. CRC byte)
    can::Frame base = can::encodeCmdFast(77, 321.0f, 0.1f, -0.1f);
    int und1 = 0, und2 = 0, n2 = 0, und3 = 0, n3 = 0;
    for (int i = 0; i < 64; ++i) {
      can::Frame x = base; x.d[i / 8] ^= (1u << (i % 8));
      if (can::crc8(x.d, 7) == x.d[7]) ++und1;
      for (int j = i + 1; j < 64; ++j) {
        can::Frame y = x; y.d[j / 8] ^= (1u << (j % 8)); ++n2;
        if (can::crc8(y.d, 7) == y.d[7]) ++und2;
        for (int k = j + 1; k < 64; ++k) {
          can::Frame z = y; z.d[k / 8] ^= (1u << (k % 8)); ++n3;
          if (can::crc8(z.d, 7) == z.d[7]) ++und3;
        }
      }
    }
    check(und1 == 0, "all 64 single-bit errors detected by CRC-8 (on top of CAN CRC-15)");
    check(und2 == 0, "all 2016 double-bit errors detected by CRC-8", fmt("undetected %.0f of %.0f", und2, n2));
    check(true, "triple-bit errors: informational", fmt("undetected %.0f of %.0f (%.4f %%)", und3, n3, 100.0 * und3 / n3));
  }

  // ------------------------------------------------------------- pintle linkage
  {
    double worst = 0; bool mono = true; float prev_us = -1;
    for (int i = 0; i <= 400; ++i) {
      const float x = 4.0e-3f * i / 400.0f;
      const float phi = linkage::liftToCrank(x);
      const float x2 = linkage::crankToLift(phi);
      if (i > 0) worst = std::fmax(worst, std::fabs(x2 - x));
      const float us = linkage::liftToUs(x, 0.0f, 1.0f);
      if (i > 0 && us <= prev_us) mono = false;
      prev_us = us;
    }
    check(worst < 2e-7, "linkage lift->crank->lift inverse (0-4 mm)", fmt("worst %.2e m", worst));
    check(mono, "pintle pulse width strictly increasing with lift");
    const float us_closed = linkage::liftToUs(0.0f, 0.0f, 1.0f), us_full = linkage::liftToUs(eng::kPintleStroke_m, 0.0f, 1.0f);
    check(us_closed > cfg::kServoMin_us && us_full < cfg::kServoMax_us, "pintle pulse range inside servo travel", fmt("%.1f .. %.1f us", us_closed, us_full));
    check(linkage::crankToLift(eng::kCrankPhiContact_rad - eng::kCrankLostMotion_rad) == 0.0f, "closed command lies inside the lost-motion zone (needle seated by spring)");
    const double dx_floor = linkage::dLiftDCrank(2.0e-4f) * (1.0 * M_PI / 180.0) / cfg::kPintleUsPerDeg;
    check(dx_floor < 5e-6, "lift per 1 us at the 12.5 % floor < 5 um", fmt("%.2f um/us", dx_floor * 1e6));
    // v2.5 crank-slider (HV69): firmware closed form vs the generator's Python implementation (independent code)
    double dphi = 0, dlift = 0;
    for (int i = 0; i < eng::kNCrankChk; ++i) {
      if (eng::kCrankChkLift_m[i] <= 0) continue;   // lift 0 is the seat: the command goes 5 deg further (lost motion), below
      dphi = std::fmax(dphi, std::fabs(linkage::liftToCrank(eng::kCrankChkLift_m[i]) - eng::kCrankChkPhi_rad[i]));
      dlift = std::fmax(dlift, std::fabs(linkage::crankToLift(eng::kCrankChkPhi_rad[i]) - eng::kCrankChkLift_m[i]));
    }
    check(dphi < 2e-5 && dlift < 2e-8, "crank-slider law matches the generator (0.1-4.2 mm)", fmt("dphi %.2e rad, dlift %.2e m", dphi, dlift));
    check(std::fabs(linkage::liftToCrank(0.0f) - (eng::kCrankChkPhi_rad[0] - eng::kCrankLostMotion_rad)) < 2e-5,
          "closed command = generator contact angle - 5 deg lost motion", fmt("%.3f deg", linkage::liftToCrank(0.0f) * 57.29578f));
    const double h = 1e-4, x0 = 2.0e-3;
    const double num = (linkage::crankToLift(linkage::liftToCrank(x0) + h) - linkage::crankToLift(linkage::liftToCrank(x0) - h)) / (2 * h);
    check(std::fabs(linkage::dLiftDCrank(x0) / num - 1.0) < 1e-3, "dLift/dCrank analytic = numeric at 2 mm", fmt("%.5f vs %.5f mm/rad", linkage::dLiftDCrank(x0) * 1e3, num * 1e3));
    const float travel = (eng::kCrankPhiMax_rad - (eng::kCrankPhiContact_rad - eng::kCrankLostMotion_rad)) * 57.29578f;
    check(travel < 99.0f, "pintle command travel (closed .. 4 mm) inside the 99 deg MKS confirmation item", fmt("%.2f deg", travel));
  }

  // ------------------------------------------------------------- v2.6 OI-6 pressure transducer scaling (sensor_scale.h)
  {
    using namespace xdcr;
    const XdcrCal c;   // defaults: 070BG 0-70 bar g (v2.6 OI-6 baseline), divider loaded by the ADC input impedance (330 kOhm)
    const float k0 = dividerGain(cfg::kXdcrDivRtop_ohm, cfg::kXdcrDivRbot_ohm, 0.0f);
    const float k300 = dividerGain(cfg::kXdcrDivRtop_ohm, cfg::kXdcrDivRbot_ohm, 300.0e3f);
    check(std::fabs(k0 - 0.240431f) < 2e-6f && std::fabs(c.k_div - 0.238215f) < 2e-5f && c.valid(),
          "divider 12.7k/4.02k: 0.24043 unloaded, 0.23822 with the ADS131M04 330 kOhm input (-0.92 %; 300 kOhm: -1.01 %)",
          fmt("k0 %.6f k330 %.6f k300 %.6f", k0, c.k_div, k300));
    const float vexc = cfg::kXdcrExcNom_V;
    const float pts[7] = {0.0f, 3.0e5f - 101325.f, 436985.f - 101325.f, 25.0e5f - 101325.f, 30.0e5f - 101325.f, 45.0e5f - 101325.f, 66.5e5f};
    double worst = 0;
    for (float p : pts) {
      const int32_t code = codeForGaugePa(p, vexc, c);
      const float back = gaugePa(sigVolts(adcVolts(code), c), vexc, c);
      worst = std::fmax(worst, std::fabs(back - p));
    }
    const float ppc = paPerCount(vexc, c);
    check(worst < 1.5 * ppc && ppc > 0.9f && ppc < 1.2f, "ADC code <-> gauge Pa round trip 0-66.5 bar g within 1.5 LSB; 1 LSB ~ 1 Pa",
          fmt("worst %.2f Pa, %.3f Pa/count", worst, ppc));
    const int32_t c3 = codeForGaugePa(3.0e5f - 101325.f, vexc, c), c31 = codeForGaugePa(3.1e5f - 101325.f, vexc, c);
    check(c31 - c3 > 9000, "0.1 bar at the 3.0 bar abs ignition threshold = > 9000 ADC counts (resolution is not the limit)",
          fmt("%.0f counts per 0.1 bar (code at 3 bar abs %.0f)", c31 - c3, c3));
    const float v_hi = cfg::kPcSensorMax_V * c.k_div, v_rail = 5.0f * c.k_div;
    check(v_hi < cfg::kAdcVref_V && v_rail < cfg::kAdcVref_V, "ADC not saturated inside the fault window (4.75 V) nor at a 5.0 V output",
          fmt("%.4f V and %.4f V at the ADC vs 1.2 V FS", v_hi, v_rail));
    check(std::fabs(c.fs_Pa - 70.0e5f) < 1.0f && c.fs_Pa >= 70.0e5f - 1.0f,
          "baseline Pc transducer range 070BG = 0-70 bar g (ENG-09 rev 2: range >= 70 bar)", fmt("%.4f bar g", c.fs_Pa / 1e5));
    XdcrCal c1k = c; c1k.fs_Pa = 68.9476e5f;
    const int32_t code45 = codeForGaugePa(44.0e5f, vexc, c);
    const float p1k = gaugePa(sigVolts(adcVolts(code45), c1k), vexc, c1k);
    check(c1k.valid() && std::fabs(p1k / 44.0e5f - 68.9476f / 70.0f) < 1e-4f,
          "alternate range 01KPG is a calibration value (fs_Pa 68.9476e5): same code reads x 68.95/70", fmt("%.4f bar g", p1k / 1e5));
    XdcrCal bad = c; bad.gain_corr = 1.2f;
    check(!bad.valid() && excitationOk(5.0f) && !excitationOk(4.70f) && !excitationOk(5.30f),
          "calibration bounds (gain_corr 0.95-1.05) and excitation window 4.75-5.25 V (M3200 supply)");
  }

  // ------------------------------------------------------------- thrust model and valve map
  {
    double worst = 0; bool mono = true; float prev = -1;
    for (float F = 40.0f; F <= 520.0f; F += 0.5f) {
      const float pc = thrust::pcAbsFromThrust(F, eng::kPamb_Pa);
      worst = std::fmax(worst, std::fabs(thrust::thrustFromPcAbs(pc, eng::kPamb_Pa) - F));
      if (pc <= prev) mono = false;
      prev = pc;
    }
    check(worst < 2e-3 && mono, "thrust<->Pc table inverse and monotonic (40-520 N)", fmt("worst %.2e N", worst));
    for (int i = 0; i < eng::kNThr; ++i) {
      const float F = eng::kThrFvac_N[i] - eng::kPamb_Pa * eng::kAe_m2;
      if (std::fabs(thrust::pcAbsFromThrust(F, eng::kPamb_Pa) - eng::kThrPcAbs_Pa[i]) > 5.0f) mono = false;
    }
    check(mono, "thrust table reproduces Combustion's points (Pc within 5 Pa)");
    bool vm = true; double inv = 0;
    for (int j = 0; j < vmap::kNPt; ++j) {
      const float pt = vmap::kPtGrid_Pa[j];
      float last = -1;
      for (float pc = 4.0e5f; pc < 26.0e5f; pc += 0.25e5f) {
        float g; const float x = ValveMap::lift(pc, pt, &g);
        if (x < last - 1e-9f) vm = false;
        last = x;
        if (x < eng::kPintleStroke_m * 0.98f && pc < pt / 1.3f) inv = std::fmax(inv, std::fabs(ValveMap::pcForLift(x, pt) - pc) / pc);
      }
    }
    check(vm, "valve map lift non-decreasing in Pc on every tank-pressure row");
    check(inv < 0.01, "valve map inverse within 1 % below the dP/Pc ceiling", fmt("worst %.3f %%", 100 * inv));
  }

  // ------------------------------------------------------------- controller sanity (no plant)
  {
    // v2.5: started at the map lift of the setpoint (bumpless equilibrium); v2.4 started at 0.3 mm, which with the
    // Combustion v2 map lies 0.05 bar below 6 bar, so the reference-model transient itself was integrated (test premise)
    PcController p; p.reset(ValveMap::lift(6.0e5f, 46e5f, nullptr), 46e5f);
    float x = 0;
    for (int i = 0; i < 200; ++i) x = p.step(6.0e5f, 6.0e5f, 46e5f, 1e-3f, true, true);
    check(std::fabs(p.trim()) < 1e-6f, "no trim drift when measured Pc equals the setpoint", fmt("trim %.2e", p.trim()));
    PcController q; q.reset(3.0e-4f, 46e5f);
    for (int i = 0; i < 3000; ++i) x = q.step(6.0e5f, 5.0e5f, 46e5f, 1e-3f, true, true);
    check(q.trim() > 0 && q.trim() <= cfg::kTrimLimit + 1e-6f, "trim rises on persistent low Pc and stays inside its limit", fmt("trim %.3f", q.trim()));
    PcController r; r.reset(3.0e-4f, 46e5f);
    for (int i = 0; i < 3000; ++i) x = r.step(2.0e5f, 10.0e5f, 46e5f, 1e-3f, true, true);   // setpoint below floor, Pc reads high
    const float xmin = (1.0f + r.trim()) * ValveMap::lift(cfg::kLiftMinRunFrac * cfg::kPcSpMinAbs_Pa, 46e5f, nullptr);
    check(r.setpointActive() >= cfg::kPcSpMinAbs_Pa - 1.0f, "setpoint below the floor is raised to the minimum Pc setpoint");
    check(x >= xmin - 1e-7f && r.trim() >= -cfg::kTrimLimit - 1e-6f, "lift never below the trimmed anti-flameout floor", fmt("x %.1f um, floor %.1f um, trim %.3f", x * 1e6, xmin * 1e6, r.trim()));
  }

  // ------------------------------------------------------------- state machine guards (no plant)
  {
    EngineEcu e; e.init(0.0); e.ptank_cal_ok = true; loadNotch(e);
    Inputs in; Commands c; Outputs o;
    in.arm_plug_present = false; in.vbat_V = 8.2f; in.mv_closed_sw = true; in.ptank_Pa = 50e5f;
    bool heartbeat = false;
    auto tick = [&](double t, Cmd cmd = Cmd::NOP) {
      in.t_s = t; c = Commands();
      if (heartbeat) { c.fast_valid = true; c.thrust_sp_N = 0; }
      if (cmd != Cmd::NOP) { c.state_valid = true; c.cmd = cmd; }
      e.step(in, c, o);
    };
    in.arm_plug_present = true; in.arm_bus_on = true;
    tick(0.0005, Cmd::ARM);
    check(e.state() == State::SAFE && e.abortCause() == Abort::LINK_LOST, "ARM refused without FC heartbeat (CMD_FAST)");
    tick(0.0007, Cmd::DISARM);
    heartbeat = true; in.arm_plug_present = false; in.arm_bus_on = false;
    tick(0.001, Cmd::ARM);
    check(e.state() == State::SAFE && e.abortCause() == Abort::ARM_LOST, "ARM refused without arming plug (inhibit latched)");
    tick(0.002, Cmd::DISARM);
    in.arm_plug_present = true; in.arm_bus_on = true; in.vbat_V = 7.6f;
    tick(0.003, Cmd::ARM);
    check(e.state() == State::SAFE && e.abortCause() == Abort::BATT_LOW, "ARM refused below the 8.1 V rest permit");
    tick(0.004, Cmd::DISARM);
    in.vbat_V = 8.2f;
    tick(0.005, Cmd::IGNITE);
    check(e.state() == State::SAFE && !o.igniter_enable && !o.mv_latch, "IGNITE ignored in SAFE (nothing energised)");
    tick(0.006, Cmd::ARM);
    check(e.state() == State::ARMED, "ARM accepted with plug, battery, closed MV, zero Pc", fmt("state %.0f cause %.0f", (double)e.state(), (double)e.abortCause()));
    check(!o.igniter_enable && !o.spark_gate && !o.sol[0] && !o.sol[1], "ARMED: igniter, spark and torch valves off");
    tick(0.007, Cmd::ABORT);
    check(e.state() == State::ABORT || e.state() == State::SAFE, "ABORT command from ARMED goes to ABORT/SAFE");
    for (int i = 0; i < 2000; ++i) tick(0.008 + i * 1e-3);
    check(e.state() == State::SAFE && !o.mv_latch && !o.arm_bus_request, "after ABORT the ECU settles in SAFE with MV latch and ARM request off");
    tick(2.0085, Cmd::ARM);
    check(e.state() == State::SAFE, "ARM refused while the abort cause is latched (DISARM acknowledges)");
    tick(2.009, Cmd::DISARM); tick(2.0095, Cmd::ARM);
    check(e.state() == State::ARMED, "ARM accepted after DISARM acknowledged the abort");
    heartbeat = false;
    for (int i = 0; i < 150; ++i) tick(2.010 + i * 1e-3);
    check(e.state() == State::SAFE || e.state() == State::ABORT, "ARMED + FC heartbeat lost > 100 ms -> abort to SAFE", fmt("state %.0f cause %.0f", (double)e.state(), (double)e.abortCause()));
    heartbeat = true;
    tick(2.2, Cmd::DISARM);
    c = Commands(); c.fast_valid = true; c.state_valid = true; c.cmd = Cmd::VENT; c.arg = 1; in.t_s = 2.201; e.step(in, c, o);
    check(o.sol[2], "VENT works in SAFE (vent valve is not ARM-gated)");
  }

  // ------------------------------------------------------------- TVC mixing (v2.6: as-built linkage, mechanical.json v2, exact pushrod solve)
  {
    const float d = 0.1f * 0.0174533f;
    double lin_err = 0;
    for (int i = 0; i < 2; ++i) {
      const float s = std::sin(mech::kLeverAz_rad[i]), c = std::cos(mech::kLeverAz_rad[i]);
      for (int k = 0; k < 8; ++k) {
        const float a = d * std::cos(k * 0.785398f), b = d * std::sin(k * 0.785398f);
        const float lin = mech::kLeverR_m * (s * a - c * b);
        lin_err = std::fmax(lin_err, std::fabs(TvcShaper::leverDz(a, b, i) - lin) / (mech::kLeverR_m * d));
      }
    }
    check(lin_err < 0.01, "TVC lever-eye displacement matches the linear map at 0.1 deg (< 1 % of r_e*angle)", fmt("worst %.4f", lin_err));
    // exact solve, checked independently in double: the pushrod keeps its length at every pose up to the 8 deg stop cone
    double len_err = 0, pmin = 1e9, pmax = -1e9, v1_err = 0;
    for (int k = 0; k < 360; ++k) for (int r = 1; r <= 8; ++r) {
      const double amp = r * static_cast<double>(mech::kStopCone_rad) / 8.0, a = amp * std::cos(k * M_PI / 180), b = amp * std::sin(k * M_PI / 180);
      for (int i = 0; i < 2; ++i) {
        const double psi = TvcShaper::servoAngle(static_cast<float>(a), static_cast<float>(b), i);
        const double x0 = mech::kLeverEye0_m[i][0], y0 = mech::kLeverEye0_m[i][1], z0 = mech::kLeverEye0_m[i][2];
        const double x1 = x0 * std::cos(b) + z0 * std::sin(b), z1 = -x0 * std::sin(b) + z0 * std::cos(b);
        const double P[3] = {x1, y0 * std::cos(a) - z1 * std::sin(a), y0 * std::sin(a) + z1 * std::cos(a)};
        const double rh = mech::kHornR_m, cp = std::cos(psi), sp = std::sin(psi);
        const double H[3] = {mech::kShaftC_m[i][0] - rh * cp * mech::kHornU[i][0], mech::kShaftC_m[i][1] - rh * cp * mech::kHornU[i][1],
                             mech::kShaftC_m[i][2] + rh * sp};
        const double len = std::sqrt((P[0] - H[0]) * (P[0] - H[0]) + (P[1] - H[1]) * (P[1] - H[1]) + (P[2] - H[2]) * (P[2] - H[2]));
        len_err = std::max(len_err, std::fabs(len - mech::kPushrod_m));
        if (r == 7) {
          pmin = std::min(pmin, psi * 180 / M_PI); pmax = std::max(pmax, psi * 180 / M_PI);
          v1_err = std::max(v1_err, std::fabs(psi - std::asin(TvcShaper::leverDz(static_cast<float>(a), static_cast<float>(b), i) / mech::kHornR_m)) * 180 / M_PI);
        }
      }
    }
    check(len_err < 1e-6, "exact TVC solve: pushrod length kept to < 1 um at all poses up to the 8 deg stop (independent double check)",
          fmt("max error %.3g m", len_err));
    check(std::fabs(pmin - mech::kPsiRange_deg[0]) < 0.02 && std::fabs(pmax - mech::kPsiRange_deg[1]) < 0.02,
          "servo-angle extremes on the 7 deg cone equal the generated values (mechanical.json v2: -32.37 / +37.39 deg)",
          fmt("%.3f / %.3f deg", pmin, pmax));
    check(v1_err > 1.5, "evidence: the v2.1-v2.5 vertical-rod map would be off by > 1.5 deg of servo angle on this linkage",
          fmt("%.2f deg", v1_err));
    const float hm = 0.25f * 0.0174533f;
    double mix_err = 0;
    for (int i = 0; i < 2; ++i) {
      const double da = (TvcShaper::servoAngle(hm, 0, i) - TvcShaper::servoAngle(-hm, 0, i)) / (2 * hm);
      const double db = (TvcShaper::servoAngle(0, hm, i) - TvcShaper::servoAngle(0, -hm, i)) / (2 * hm);
      mix_err = std::max({mix_err, std::fabs(da - mech::kMixNeutral[i][0]), std::fabs(db - mech::kMixNeutral[i][1])});
    }
    check(mix_err < 0.01, "neutral mixing d psi / d(alpha, beta) equals mechanical.json (3.394 deg/deg)", fmt("max diff %.4f", mix_err));
    const double clo = cfg::kTvcPsiMin_rad * 57.29578, chi = cfg::kTvcPsiMax_rad * 57.29578;
    check(mech::kPsiStop_deg[0] < clo && clo < mech::kPsiRange_deg[0] && mech::kPsiRange_deg[1] < chi && chi < mech::kPsiStop_deg[1],
          "horn clamp per sense lies between the 7 deg need and the 8 deg stop", fmt("clamp %.2f / %.2f deg", clo, chi) +
          fmt(" (need %.2f / %.2f,", mech::kPsiRange_deg[0], mech::kPsiRange_deg[1]) + fmt(" stop %.2f / %.2f)", mech::kPsiStop_deg[0], mech::kPsiStop_deg[1]));
    TvcShaper sh; const float z[2] = {0, 0}; sh.reset(z);
    float oe[2] = {0, 0}, ou[2] = {0, 0}, us_min = 1e9f, us_max = -1e9f;
    const float big[2] = {0.2f, 0.2f};
    for (int k = 0; k < 400; ++k) sh.step(big, 1e-3f, oe, ou);
    const float nrm = std::sqrt(oe[0] * oe[0] + oe[1] * oe[1]);
    check(std::fabs(nrm - mech::kRangeVec_rad) < 1e-4f, "command (11.5, 11.5) deg is clamped to the 7 deg vector norm", fmt("norm %.4f deg", nrm * 57.29578));
    TvcShaper sh2; sh2.reset(z);
    for (int k = 0; k < 3000; ++k) {
      const float th = k * 0.00628f, c2[2] = {0.2f * std::cos(th), 0.2f * std::sin(th)};
      sh2.step(c2, 1e-3f, oe, ou);
      if (k > 200) for (int i = 0; i < 2; ++i) { us_min = std::fmin(us_min, ou[i]); us_max = std::fmax(us_max, ou[i]); }
    }
    check(us_min > 1500 - 500 && us_max < 1500 + 500, "TVC pulses stay inside 1000-2000 us for any over-range command",
          fmt("%.1f .. %.1f us", us_min, us_max));
    const float pa[2] = {0.05f, 0.0f}, pb[2] = {0.0f, 0.05f};
    TvcShaper sh3; sh3.reset(z);
    for (int k = 0; k < 200; ++k) sh3.step(pa, 1e-3f, oe, ou);
    const float ua0 = ou[0], ua1 = ou[1];
    TvcShaper sh4; sh4.reset(z);
    for (int k = 0; k < 200; ++k) sh4.step(pb, 1e-3f, oe, ou);
    check(ua0 > 1500 && ua1 < 1500 && ou[0] > 1500 && ou[1] > 1500,
          "levers at 135/225 deg: +alpha lifts horn A and lowers horn B, +beta lifts both", fmt("alpha: A %.1f B %.1f us", ua0, ua1) + fmt(", beta: A %.1f B %.1f us", ou[0], ou[1]));
  }

  // ------------------------------------------------------------- chamber over-pressure (v2.2, lead decision 2026-10-12)
  {
    check(cfg::kPcSpMaxAbs_Pa <= 25.0e5f + 1.0f, "Pc setpoint ceiling within the lead cap of 25 bar", fmt("%.3f bar abs", cfg::kPcSpMaxAbs_Pa / 1e5));
    check(cfg::kPcXdcrFs_Pa > 63.0e5f && 0.5f + 4.0f * (63.0e5f - 101325.f) / cfg::kPcXdcrFs_Pa < 4.5f,
          "Pc transducer in range at the 63 bar blocked-nozzle bound", fmt("%.3f V", 0.5 + 4.0 * (63.0e5 - 101325.) / cfg::kPcXdcrFs_Pa));
    struct Rig {
      EngineEcu e; Inputs in; Commands c; Outputs o; double t = 0; float thrust = 500.f; bool follow = true;
      Rig() {
        e.init(0.0); e.ptank_cal_ok = true; loadNotch(e);
        in.arm_plug_present = true; in.arm_bus_on = true; in.vbat_V = 8.2f; in.mv_closed_sw = true; in.ptank_Pa = 50e5f;
        in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f; setPc(101325.f);
      }
      void setPc(float pabs) { in.pc_Pa = pabs - 101325.f; in.pc_raw_V = 0.5f + 4.f * in.pc_Pa / cfg::kPcXdcrFs_Pa; }
      void tick(Cmd cmd = Cmd::NOP) {
        t += 1e-3; in.t_s = t; c = Commands(); c.fast_valid = true; c.thrust_sp_N = thrust;
        if (cmd != Cmd::NOP) { c.state_valid = true; c.cmd = cmd; }
        if (follow) in.pintle_meas_m = o.pintle_cmd_m;   // ideal follower, one tick late
        idealTorch(in, o);   // v2.7
        e.step(in, c, o);
      }
      void run(int n) { for (int i = 0; i < n; ++i) tick(); }
      bool toRun(float pc_abs) {   // ARM -> IGNITE (PREPRESS: MV open, feed primed) -> IGNITION -> Pc up -> RUN
        tick(Cmd::ARM); run(600);
        tick(Cmd::IGNITE);
        in.mv_open_sw = true; in.mv_closed_sw = false; in.pfeed_Pa = 48e5f;
        for (int i = 0; i < 1000 && e.state() != State::IGNITION; ++i) tick();
        run(130); setPc(kLitStartAbs);   // v2.9: light at a lit-start plateau (A5 aborts above 8 bar abs in the hold), then the RUN pressure
        for (int i = 0; i < 100 && e.state() != State::RUN; ++i) tick();
        setPc(pc_abs);
        return e.state() == State::RUN;
      }
    };
    {
      Rig r;
      const bool in_run = r.toRun(25.0e5f);
      r.run(500);
      check(in_run && r.e.state() == State::RUN, "test rig reaches RUN at Pc 25 bar (500 N)");
      r.setPc(29.0e5f); r.run(200);
      check(r.e.state() == State::RUN, "Pc 29 bar abs for 200 ms: no abort (below the 30 bar limit)");
      r.setPc(31.0e5f);
      int n = 0; while (r.e.state() == State::RUN && n < 50) { r.tick(); ++n; }
      check(r.e.abortCause() == Abort::PC_OVERPRESSURE && n <= 11, "Pc 31 bar abs in RUN -> PC_OVERPRESSURE abort (v2.10 RE-20: filtered, 5 ms)",
            fmt("cause %.0f after %.0f ms", (double)r.e.abortCause(), n));
      check(!r.o.mv_latch && r.o.arm_bus_request, "PC_OVERPRESSURE: MV latch released, ARM bus kept to drive the pintle shut");
      r.run(15);
      check(r.o.pintle_cmd_m < 1e-6f, "PC_OVERPRESSURE: pintle commanded fully closed at the close rate", fmt("cmd %.3f mm", r.o.pintle_cmd_m * 1e3));
      r.follow = false; r.in.pintle_meas_valid = true; r.in.pintle_meas_m = 0.0f; r.run(30);
      check(r.o.arm_bus_request, "ABORT with the pintle reading closed at 45 ms: ARM bus still requested");
    }
    {
      Rig r; r.toRun(25.0e5f); r.run(500);
      const float x_run = r.o.pintle_cmd_m;
      r.follow = false; r.in.pintle_meas_m = 2.0e-3f;   // needle stays at 2 mm (jam) from the abort on
      r.tick(Cmd::ABORT);
      int n = 0, n_ep = -1; while (r.o.arm_bus_request && n < 300) { r.tick(); ++n; if (n_ep < 0 && r.o.pintle_noprog_s > 0) n_ep = n; }
      // v2.6: the 40 ms 'still open' check is retired (HV69 closes 4 mm in 0.13-0.17 s); the progress monitor releases the bus
      // 0.1 s after the closing command passes 0.15 mm below the stuck needle; the jam is recorded once (abort cause stays CMD)
      check(!r.o.arm_bus_request && n_ep > 0 && n - n_ep >= 99 && n - n_ep <= 101 && r.e.abortCause() == Abort::CMD &&
            r.o.pintle_fault_kind == jam::STALL_TIME && r.e.jamCount() == 1 && r.o.maint_jam_pending,
            "v2.6 ABORT, needle stuck at 2 mm: no closing progress for 0.1 s -> ARM bus released, one jam event (STALL_TIME), MAINT pending",
            fmt("cmd at abort %.2f mm, episode from %.0f ms, released after %.0f ms", x_run * 1e3, n_ep, n));
    }
    {
      Rig r; r.toRun(25.0e5f); r.run(100);
      r.tick(Cmd::ABORT); r.setPc(33.0e5f);
      int n = 0; while (r.o.arm_bus_request && n < 100) { r.tick(); ++n; }
      check(!r.o.arm_bus_request && n >= 58 && n <= 63, "ABORT with Pc still above 30 bar at 60 ms: ARM bus released", fmt("released after %.0f ms", n));
    }
    {
      Rig r; r.toRun(25.0e5f); r.run(500);
      r.in.pc_raw_V = 4.9f; r.in.pc_Pa = 75.0e5f;   // reading saturated high (also a sensor fault)
      r.run(10);
      check(r.e.abortCause() == Abort::PC_OVERPRESSURE, "Pc reading saturated high (4.9 V) aborts: OVP not gated by sensor validity",
            fmt("cause %.0f", (double)r.e.abortCause()));
    }
    {
      Rig r;
      r.tick(Cmd::ARM); r.run(600);
      r.tick(Cmd::IGNITE); r.in.mv_open_sw = true; r.in.mv_closed_sw = false; r.in.pfeed_Pa = 48e5f;
      for (int i = 0; i < 1000 && r.e.state() != State::IGNITION; ++i) r.tick();
      r.run(130); r.setPc(40.0e5f); int nh = 0; while (r.e.state() == State::IGNITION && nh < 30) { r.tick(); ++nh; }
      while (r.e.state() == State::RUN && nh < 30) { r.tick(); ++nh; }
      // v2.10 RE-20: with 5 ms on the filtered channel a 40 bar step in IGNITION confirms light (E2 at 10 ticks) one tick before the
      // persistence completes (filter crossing ~6 ms + 5 ms), so the abort is PC_OVERPRESSURE from RUN; v2.9 (3 ms) gave HARD_START
      check((r.e.abortCause() == Abort::HARD_START || r.e.abortCause() == Abort::PC_OVERPRESSURE) && nh <= 12,
            "Pc 40 bar during ignition -> over-pressure abort within 12 ms (v2.10 RE-20 filtered 5 ms; the persistence now runs on across E2: cause HARD_START in the start phase)",
            fmt("cause %.0f after %.0f ms", (double)r.e.abortCause(), nh));
    }
    {
      Rig r;
      r.in.ovp_ok = false; r.run(20);
      check(r.e.state() == State::SAFE && r.e.abortCause() == Abort::NONE, "OVP_OK low in SAFE is ignored (latch state undefined before ARM)");
      r.in.ovp_ok = true; r.tick(Cmd::ARM); r.run(10);
      check(r.e.state() == State::ARMED && r.o.arm_bus_request, "ARMED with OVP_OK high (latch set by the ARM_REQ edge)");
      r.in.ovp_ok = false;
      int n = 0; while (r.e.state() == State::ARMED && n < 20) { r.tick(); ++n; }
      check(r.e.abortCause() == Abort::HW_OVERPRESSURE && n <= 3 && !r.o.arm_bus_request, "OVP_OK low in ARMED -> HW_OVERPRESSURE abort, ARM request dropped",
            fmt("cause %.0f after %.0f ms", (double)r.e.abortCause(), n));
    }
  }

  // ------------------------------------------------------------- line priming rule (v2.2, COMB v2 via lead 2026-10-12)
  {
    bool follow = true;
    auto mk = [&follow](EngineEcu& e, Inputs& in) {
      e.init(0.0); e.ptank_cal_ok = true; loadNotch(e); follow = true;
      in.arm_plug_present = true; in.arm_bus_on = true; in.vbat_V = 8.2f; in.mv_closed_sw = true; in.ptank_Pa = 50e5f;
      in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f; in.pc_Pa = 0; in.pc_raw_V = 0.5f;
    };
    auto tick = [&follow](EngineEcu& e, Inputs& in, Outputs& o, double& t, Cmd cmd = Cmd::NOP) {
      t += 1e-3; in.t_s = t; Commands c; c.fast_valid = true; c.thrust_sp_N = 100.f;
      if (cmd != Cmd::NOP) { c.state_valid = true; c.cmd = cmd; }
      if (follow) in.pintle_meas_m = o.pintle_cmd_m;
      idealTorch(in, o);   // v2.7
      e.step(in, c, o);
    };
    {   // empty line (P_feed ~ 0 bar g): bleed first, then a slow opener ramp
      EngineEcu e; Inputs in; Outputs o; double t = 0; mk(e, in);
      tick(e, in, o, t, Cmd::ARM); for (int i = 0; i < 600; ++i) tick(e, in, o, t);
      tick(e, in, o, t, Cmd::IGNITE);
      double t_bleed = -1, t_open_start = -1, t_cock = -1; const double t0 = t;
      for (int i = 0; i < 700 && e.state() == State::PREPRESS; ++i) {
        tick(e, in, o, t);
        if (t_bleed < 0 && o.pintle_cmd_m >= 0.99f * cfg::kBleedLift_m) t_bleed = t - t0;
        if (t_open_start < 0 && o.servo_us[3] > cfg::kMvOpenerRest_us + 4.5f) t_open_start = t - t0;
        if (t_cock < 0 && o.servo_us[3] >= cfg::kMvOpenerCock_us - 0.5f) t_cock = t - t0;
      }
      check(e.state() == State::PREPRESS || e.state() == State::ARMED || e.state() == State::ABORT, "priming test rig stays out of IGNITION without a primed feed");
      check(t_bleed >= 0 && t_open_start > t_bleed + 0.04, "empty line: pintle at the 0.10 mm bleed lift before the main valve starts to open",
            fmt("bleed %.0f ms, opener moves %.0f ms", t_bleed * 1e3, t_open_start * 1e3));
      check(t_cock - t_open_start >= 0.30, "empty line: main-valve opener ramp lasts >= 0.3 s (COMB v2)", fmt("%.0f ms", (t_cock - t_open_start) * 1e3));
    }
    {   // empty line but the encoder shows the pintle still seated at the bleed check: never open into a dead end
      EngineEcu e; Inputs in; Outputs o; double t = 0; mk(e, in);
      tick(e, in, o, t, Cmd::ARM); for (int i = 0; i < 600; ++i) tick(e, in, o, t);
      follow = false; in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f;
      tick(e, in, o, t, Cmd::IGNITE);
      float us_max = 0; int n = 0;
      while (e.state() == State::PREPRESS && n < 200) { tick(e, in, o, t); us_max = std::max(us_max, o.servo_us[3]); ++n; }
      check(e.abortCause() == Abort::PREPRESS_FAIL && us_max <= cfg::kMvOpenerRest_us + 0.5f,
            "bleed lift not confirmed by the encoder -> PREPRESS_FAIL before the valve moves", fmt("abort after %.0f ms, opener max %.0f us", n, us_max));
      check(o.pintle_fault_kind == jam::BLEED_NOT_CONFIRMED && e.jamCount() == 1 && o.maint_jam_pending,
            "v2.6: unconfirmed bleed lift recorded as a suspected jam (kind 4), MAINT pending", fmt("kind %.0f", o.pintle_fault_kind));
    }
    {   // primed line (relight, P_feed ~ P_tank): no bleed; v2.6 LEAD rule (b): the opener still ramps >= 0.3 s (every opening)
      EngineEcu e; Inputs in; Outputs o; double t = 0; mk(e, in);
      in.pfeed_Pa = 49e5f;
      tick(e, in, o, t, Cmd::ARM); for (int i = 0; i < 600; ++i) tick(e, in, o, t);
      tick(e, in, o, t, Cmd::IGNITE);
      float pint_max = 0; double t_cock = -1, t_open_start = -1; const double t0 = t;
      for (int i = 0; i < 700 && e.state() == State::PREPRESS; ++i) {
        tick(e, in, o, t); pint_max = std::max(pint_max, o.pintle_cmd_m);
        if (t_open_start < 0 && o.servo_us[3] > cfg::kMvOpenerRest_us + 4.5f) t_open_start = t - t0;
        if (t_cock < 0 && o.servo_us[3] >= cfg::kMvOpenerCock_us - 0.5f) t_cock = t - t0;
      }
      check(pint_max == 0.0f && t_open_start >= 0 && t_open_start <= 0.005 && t_cock - t_open_start >= 0.30,
            "v2.6 primed line: no bleed lift, opener ramp >= 0.3 s on this opening too (LEAD rule b)",
            fmt("pintle max %.3f mm, opener moves %.1f ms, cock at %.0f ms", pint_max * 1e3, t_open_start * 1e3, t_cock * 1e3));
    }
  }

  // ------------------------------------------------------------- v2.5 Combustion v2.1 start sequence (M2 re-read)
  {
    struct Rig5 {
      EngineEcu e; Inputs in; Commands c; Outputs o; double t = 0; float thrust = 100.f;
      bool follow = false;   // ideal plant: in RUN the chamber follows the last active Pc setpoint (no FLAMEOUT/PC_BAND trips)
      bool pfollow = true;   // v2.6: ideal pintle follower (encoder = previous command)
      bool torch_dead = false;   // v2.7: the torch never lights (P_torch follows the chamber)
      bool ptorch_bad = false;   // v2.7: P_torch reading invalid (ADC2 fault / open transducer)
      bool ptorch_bad_from_ignite = false, ptorch_stuck_from_ignite = false, stuck_on = false;   // v2.7: failures after ARM
      float ptorch_offset = 0.0f, ptorch_stuck_Pa = 0.0f;   // v2.7: transducer zero offset (gauge) / stuck reading
      bool fc_send = false; float fc_F = 0.0f; bool fc_ok = true; int fc_period_ms = 10;   // v2.8: FC_THRUST estimate (100 Hz)
      long n_tick = 0;
      Rig5() {
        e.init(0.0); e.ptank_cal_ok = true; loadNotch(e);
        in.arm_plug_present = true; in.arm_bus_on = true; in.vbat_V = 8.2f; in.mv_closed_sw = true; in.ptank_Pa = 50e5f;
        in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f; setPc(101325.f);
      }
      void setPc(float pabs) { in.pc_Pa = pabs - 101325.f; in.pc_raw_V = 0.5f + 4.f * in.pc_Pa / cfg::kPcXdcrFs_Pa; }
      void tick(Cmd cmd = Cmd::NOP, uint16_t arg = 0) {
        t += 1e-3; in.t_s = t; c = Commands(); c.fast_valid = true; c.thrust_sp_N = thrust;
        if (cmd != Cmd::NOP) { c.state_valid = true; c.cmd = cmd; c.arg = arg; }
        if (fc_send && (n_tick % fc_period_ms) == 0) { c.fc_thrust_valid = true; c.fc_thrust_N = fc_F; c.fc_thrust_ok = fc_ok; }
        ++n_tick;
        if (follow && o.state == State::RUN && o.pc_sp_active_Pa > 0) setPc(o.pc_sp_active_Pa);
        if (pfollow) in.pintle_meas_m = o.pintle_cmd_m;
        idealTorch(in, o);   // v2.7
        if (torch_dead) { in.ptorch_Pa = std::fmax(0.0f, in.pc_Pa); if (o.state != State::RUN) in.photo_V = kPhotoDarkRig_V; }
        in.ptorch_Pa += ptorch_offset;
        if (stuck_on) in.ptorch_Pa = ptorch_stuck_Pa;
        if (ptorch_bad) in.ptorch_valid = false;
        e.step(in, c, o);
      }
      bool lightRun(float pc_abs = 6.0e5f, int wait = 150) { run(wait); setPc(pc_abs); until(State::RUN, 100); return e.state() == State::RUN; }
      bool burnToCoast(int run_ms = 300) {   // RUN -> SHUTDOWN (pintle then valve) -> COAST, MV switch follows the latch
        run(run_ms); tick(Cmd::SHUTDOWN); setPc(101325.f);
        for (int i = 0; i < 2000 && e.state() != State::COAST; ++i) { tick(); if (!o.mv_latch) { in.mv_open_sw = false; in.mv_closed_sw = true; } }
        return e.state() == State::COAST;
      }
      int toRelight() {    // COAST -> RELIGHT -> PREPRESS (opener ramp) -> IGNITION; returns ms
        tick(Cmd::RELIGHT);
        in.mv_open_sw = true; in.mv_closed_sw = false; in.pfeed_Pa = 48e5f;
        int n = 0; for (; n < 2000 && e.state() != State::IGNITION; ++n) tick();
        return n;
      }
      void run(int n) { for (int i = 0; i < n; ++i) tick(); }
      int until(State s, int nmax) { int n = 0; while (e.state() != s && n < nmax) { tick(); ++n; } return n; }
      int toIgnition() {   // returns ms spent in PREPRESS
        tick(Cmd::ARM); run(600);
        if (ptorch_bad_from_ignite) ptorch_bad = true;
        if (ptorch_stuck_from_ignite) stuck_on = true;
        tick(Cmd::IGNITE);
        in.mv_open_sw = true; in.mv_closed_sw = false; in.pfeed_Pa = 48e5f;
        int n = 0; for (; n < 1000 && e.state() != State::IGNITION; ++n) tick();
        return n;
      }
    };
    {   // v2.7 RC-01: both torch valves open at IGNITION entry and close TOGETHER on the light-confirmation event (not 0.40/0.60 s)
      Rig5 r; r.toIgnition();
      const bool closed_at_entry = !r.o.sol[0] && !r.o.sol[1];   // entry tick ran the PREPRESS branch
      r.tick();
      check(r.e.state() == State::IGNITION && r.o.sol[0] && r.o.sol[1] && closed_at_entry,
            "both torch solenoids open on the first IGNITION tick (COMB t 0, 1 ms tick)");
      int t_prop = -1, t_n2o = -1, t_run = -1, t_ok = -1, sparks = r.o.spark_gate ? 1 : 0, n2o_alone = 0; bool prev = r.o.spark_gate;
      bool closed_flag_at_run = false;
      for (int k = 2; k <= 700; ++k) {
        if (k == 200) r.setPc(eng::kIgnitionPcAbs_Pa + 0.2e5f);   // lit at 3.2 bar abs (below the propane backstop)
        r.tick();
        if (t_ok < 0 && r.o.torch_ok) t_ok = k;
        if (t_prop < 0 && !r.o.sol[1]) t_prop = k;
        if (t_n2o < 0 && !r.o.sol[0]) t_n2o = k;
        if (t_run < 0 && r.e.state() == State::RUN) { t_run = k; closed_flag_at_run = r.o.torch_closed; }
        n2o_alone += r.o.sol[0] && !r.o.sol[1];
        if (r.o.spark_gate && !prev) ++sparks;
        prev = r.o.spark_gate;
      }
      check(t_prop == t_n2o && t_n2o == t_run && t_run > 200 && n2o_alone == 0 && closed_flag_at_run,
            "v2.7 RC-01: both torch valves close on the light-confirmation tick (RUN entry), never N2O-only (COMB v2.3 0.40/0.60 s retired)",
            fmt("light step 200 ms, RUN %.0f ms, propane %.0f ms, N2O %.0f ms", t_run, t_prop, t_n2o) + fmt(", torch confirmed at %.0f ms, N2O-alone ticks %.0f", t_ok, n2o_alone));
      const int sp_expect = static_cast<int>(std::ceil((t_n2o - 1000 * eng::kSparkStart_s) / (1000.0 / eng::kSparkRate_Hz)));
      check(sparks == sp_expect, "v2.7 spark train 50 Hz from 0.02 s, stopped with the torch valves", fmt("%.0f sparks (expected %.0f)", sparks, sp_expect));
      check(t_ok >= 2 && t_ok <= 2 + cfg::kTorchConfirmN, "v2.7 torch flame confirmed kTorchConfirmN ticks after the torch chamber reads lit (ideal rig torch)",
            fmt("confirmed at %.0f ms", t_ok));
    }
    {   // v2.7 RC-01 propane backstop: raw Pc at (5.0 - 1.0) bar abs before the confirmation closes BOTH torch valves
      Rig5 r; r.follow = true; r.toIgnition(); r.run(150); r.setPc(4.2e5f);
      bool open_before = true;   // v2.10 RE-18: the backstop needs kPropaneBackstopN consecutive raw samples (v2.9: the first one)
      for (int k = 0; k < cfg::kPropaneBackstopN - 1; ++k) { r.tick(); open_before = open_before && r.o.sol[0] && r.o.sol[1]; }
      r.tick();
      const bool both_closed_1 = !r.o.sol[1] && !r.o.sol[0] && r.e.state() == State::IGNITION;
      const int n = r.until(State::RUN, 50);                    // lit detection on the 50 Hz filtered Pc
      check(r.e.state() == State::RUN && open_before && both_closed_1 && !r.o.sol[1] && !r.o.sol[0],
            "v2.7 propane backstop at Pc 4.2 bar abs (before 5 bar): BOTH torch valves closed (v2.6 left the N2O torch valve open); v2.10 "
            "RE-18: on the kPropaneBackstopN-th consecutive raw sample, open before",
            fmt("RUN %.0f ms after the step", n + cfg::kPropaneBackstopN));
    }
    {   // ignition check 3.0 bar ABSOLUTE; v2.8: window W (R1, first start: 0.40 s) counted from the ignition-lift command (E1)
      Rig5 r; r.toIgnition(); const double t_e0 = r.t; r.run(125); r.setPc(kUnlitAbs);   // v2.9: cold-flow plateau P0 + 0.70 bar: not lit
      int n = 125; while (r.e.state() == State::IGNITION && n < 1000) { r.tick(); ++n; }
      const int n_exp = static_cast<int>(std::lround(1000.0 * (r.e.liftCommandTime() - t_e0 + cfg::kIgnWindowFirst_s))) + 1;
      check(r.e.abortCause() == Abort::NO_IGNITION && std::abs(n - n_exp) <= 1 && r.e.ignRule() == rule::FIRST,
            "v2.9 unlit plateau P0 + 0.70 bar (1.71 bar abs): NO_IGNITION abort at the lift command + W (R1 0.40 s) (v2.8.3: 2.9 bar abs vs the 3.0 bar rule)",
            fmt("cause %.0f after %.0f ms, lift at %.0f ms", (double)r.e.abortCause(), n, 1e3 * (r.e.liftCommandTime() - t_e0)));
      Rig5 q; q.toIgnition(); const double q0 = q.t; q.run(250); q.setPc(3.1e5f);
      const int m = q.until(State::RUN, 60);
      check(q.e.state() == State::RUN && 250 + m < 1000 * (q.e.liftCommandTime() - q0 + cfg::kIgnWindowFirst_s),
            "Pc 3.1 bar abs at 0.25 s: lit -> RUN (v2.9 relative rule: rise >= 0.8 bar, 10 ms)", fmt("RUN %.0f ms after the step (filter)", m));
    }
    {   // v2.6 OI-6 (v2.9 values): light confirmation = filtered AND raw rise >= 0.8 bar over P0 and >= 1.8 bar abs for 10 consecutive ticks
      Rig5 r; r.toIgnition(); r.run(150);
      float pf_max = 0.0f;
      r.setPc(101325.f + 20.0e5f); r.tick();                  // one 1 ms frame at 20 bar g (spark EMI / bad ADC frame)
      r.setPc(101325.f);
      for (int k = 0; k < 60; ++k) { r.tick(); pf_max = std::fmax(pf_max, r.e.pcAbsFiltered()); }
      check(r.e.state() == State::IGNITION && pf_max > eng::kIgnitionPcAbs_Pa,
            "v2.6 OI-6: a single 20 bar spike does not confirm light (the filtered Pc alone would have: v2.5 rule)",
            fmt("filtered peak %.2f bar abs, state %.0f", pf_max / 1e5, (double)r.e.state()));
      int n_run = 0;
      for (int k = 0; k < 400 && r.e.state() == State::IGNITION; ++k) {   // 50 Hz train of 2 ms spikes (spark-synchronous)
        r.setPc(101325.f + ((k % 20) < 2 ? 20.0e5f : 0.0f)); r.tick();
        if (r.e.state() == State::RUN) ++n_run;
      }
      check(n_run == 0 && r.e.abortCause() == Abort::NO_IGNITION,
            "v2.6 OI-6: 50 Hz train of 2 ms, 20 bar spikes on an unlit chamber -> no light, NO_IGNITION (v2.8: lift + 0.40 s)",
            fmt("cause %.0f", (double)r.e.abortCause()));
      Rig5 q; q.toIgnition(); q.run(250); q.setPc(3.1e5f);
      int m = 0; while (q.e.state() == State::IGNITION && m < 60) { q.tick(); ++m; }
      Rig5 w; w.toIgnition(); w.run(250); w.setPc(3.1e5f);
      int first_above = -1, k2 = 0;
      for (; k2 < 60 && w.e.state() == State::IGNITION; ++k2) {
        w.tick();
        if (first_above < 0 && (w.o.ign_det & det::RISE) && (w.o.ign_det & det::FLOOR)) first_above = k2 + 1;
      }
      check(q.e.state() == State::RUN && first_above > 0 && m - first_above == cfg::kIgnConfirmRelN - 1,
            "v2.9 light confirmed kIgnConfirmRelN-1 ticks after filtered AND raw first show the 0.8 bar rise over P0 and the 1.8 bar abs floor (v2.6 OI-6 rule, LEAD-adopted values)",
            fmt("rise+floor first at %.0f ms, RUN at %.0f ms", first_above, m));
    }
    {   // v2.6 OI-6: ARM zero sanity on the filtered gauge Pc (a single raw spike at the ARM tick no longer refuses ARM)
      Rig5 r; r.run(100);
      r.setPc(101325.f + 1.0e5f); r.tick(Cmd::ARM); r.setPc(101325.f); r.run(10);
      const bool armed = r.e.state() == State::ARMED;
      Rig5 q; q.setPc(101325.f + 0.6e5f); q.run(200); q.tick(Cmd::ARM); q.run(5);
      check(armed && q.e.state() == State::SAFE && q.e.abortCause() == Abort::PC_SENSOR,
            "v2.6 OI-6: ARM accepted with a 1 bar single-frame spike; refused (PC_SENSOR) with a steady 0.6 bar reading",
            fmt("spike case state %.0f, steady case cause %.0f", (double)r.e.state(), (double)q.e.abortCause()));
    }
    {   // v2.6 OI-6: sensor over-range during IGNITION: HIGH = over-pressure (HARD_START), LOW = sensor fault
      // v2.11 (LEAD 203 (1)(a)): in FLIGHT the HIGH over-range no longer latches PC_SENSOR (non-sticky over-range bit); the stand as built
      Rig5 r; r.toIgnition(); r.run(150);
      r.in.pc_raw_V = 4.9f; r.in.pc_Pa = 76.0e5f; r.tick();
      Rig5 rs; rs.in.load_cell_N = 0.0f; rs.in.mode_strap = strap::STAND; rs.toIgnition(); rs.run(150);
      rs.in.pc_raw_V = 4.9f; rs.in.pc_Pa = 76.0e5f; rs.tick();
      check(r.e.abortCause() == Abort::HARD_START && !(r.o.fault_bits & fault::PC_SENSOR) && (r.o.fault_bits & fault::PC_OVERP) &&
            r.o.pc_overrange && (r.o.ovr_flags & ovr::OVERRANGE) && !r.o.pc_valid &&
            rs.e.abortCause() == Abort::HARD_START && (rs.o.fault_bits & fault::PC_SENSOR) && (rs.o.fault_bits & fault::PC_OVERP),
            "v2.6 OI-6 / v2.11 203 (1)(a): over-range HIGH (4.9 V) in IGNITION -> HARD_START on the same tick; flight PC_OVERP + over-range bit "
            "(no PC_SENSOR latch), stand PC_SENSOR + PC_OVERP (as built)",
            fmt("flight cause %.0f faults ", (double)r.e.abortCause()) + hex(r.o.fault_bits, 4) + fmt(", stand cause %.0f faults ", (double)rs.e.abortCause()) +
            hex(rs.o.fault_bits, 4));
      Rig5 q; q.toIgnition(); q.run(150);
      q.in.pc_raw_V = 0.05f; q.in.pc_Pa = -5.0e5f; q.tick();
      check(q.e.abortCause() == Abort::PC_SENSOR && !(q.o.fault_bits & fault::PC_OVERP),
            "v2.6 OI-6: over-range LOW (0.05 V, open/short) in IGNITION -> PC_SENSOR", fmt("cause %.0f", (double)q.e.abortCause()));
    }
    {   // start ramp <= 2500 N/s from the ignition thrust, then the ordinary setpoint slew; pre-MECO throttle-down + SHUTDOWN
      Rig5 r; r.thrust = 500.f; r.follow = true; r.toIgnition(); r.run(150); r.setPc(6.2e5f); r.until(State::RUN, 50);
      const bool run = r.e.state() == State::RUN;
      const float F0 = thrust::thrustFromPcAbs(r.o.pc_sp_active_Pa, r.e.pamb_Pa);
      r.run(100);
      const float F1 = thrust::thrustFromPcAbs(r.o.pc_sp_active_Pa, r.e.pamb_Pa);
      const float rate = (F1 - F0) / 0.100f;
      check(run && rate > 0.95f * eng::kStartRamp_Nps && rate < 1.01f * eng::kStartRamp_Nps && r.e.startRampActive(),
            "start ramp follows <= 2500 N/s after ignition (COMB v2.1)", fmt("%.0f N/s from %.0f N", rate, F0));
      r.run(200);
      check(!r.e.startRampActive() && std::fabs(thrust::thrustFromPcAbs(r.o.pc_sp_active_Pa, r.e.pamb_Pa) - 500.f) < 2.f, "start ramp ends at the command (500 N)");
      r.thrust = 375.f; r.run(60);   // GNC pre-MECO throttle-down (<= 75 %) is an ordinary FC thrust command
      const float Fd = thrust::thrustFromPcAbs(r.o.pc_sp_active_Pa, r.e.pamb_Pa);
      check(std::fabs(Fd - 375.f) < 2.f, "pre-MECO throttle-down to 75 % followed at the RUN setpoint slew", fmt("%.1f N after 60 ms", Fd));
      const float x75 = r.o.pintle_cmd_m;
      r.tick(Cmd::SHUTDOWN);
      int n = 0; while (r.o.pintle_cmd_m > 1e-6f && n < 100) { r.tick(); ++n; }
      check(r.e.state() == State::SHUTDOWN && n <= static_cast<int>(1000 * x75 / cfg::kPintleCloseRate_mps) + 2,
            "SHUTDOWN (MECO): pintle command closed at the full close rate (servo-limited)", fmt("from %.2f mm in %.0f ms", x75 * 1e3, n));
    }
    {   // OI-12 vented chamber: IGNITE/RELIGHT ignored while |Pc gauge| >= 0.1 bar
      Rig5 r; r.tick(Cmd::ARM); r.run(600);
      r.setPc(101325.f + 0.15e5f); r.run(100);
      r.tick(Cmd::IGNITE); r.run(5);
      check(r.e.state() == State::ARMED && r.e.ignitionRefused() == 1, "IGNITE ignored with Pc 0.15 bar g (chamber not vented, OI-12)",
            fmt("state %.0f refused %.0f", (double)r.e.state(), r.e.ignitionRefused()));
      r.setPc(101325.f + 0.05e5f); r.run(100);
      r.tick(Cmd::IGNITE); r.run(2);
      check(r.e.state() == State::PREPRESS, "IGNITE accepted with Pc 0.05 bar g", fmt("state %.0f", (double)r.e.state()));
    }
    {   // v2.10 (LEAD CHANGELOG 172 (1)) ground no-light safing rule, pad first start (replaces the COMB v2.2 5 s retry wait): NO_IGNITION
        // sets the lockout and opens the safing hold; ARM refused (RELIGHT_LOCKOUT) at +6 s; a keyed CLEAR_LOCKOUT in SAFE is refused
        // (SAFING_HOLD) at +959.9 s and accepted at +960.0 s; then ARM and IGNITE are accepted (full 960 s run at 1 kHz)
      Rig5 r; r.toIgnition(); r.run(125); r.setPc(kUnlitAbs);
      r.until(State::ABORT, 1000);
      const double t_ab = r.t; const bool cause = r.e.abortCause() == Abort::NO_IGNITION;
      const bool hold_ev = r.o.safing_hold_event && r.o.relight_lockout && r.o.safing_hold;
      r.setPc(101325.f); r.until(State::SAFE, 1000);
      r.in.mv_open_sw = false; r.in.mv_closed_sw = true; r.in.pfeed_Pa = 0;
      while (r.t - t_ab < 6.0) r.tick();
      r.tick(Cmd::DISARM); r.tick(Cmd::ARM); r.run(5);
      const bool arm_ref = r.e.state() == State::SAFE && r.e.abortCause() == Abort::RELIGHT_LOCKOUT;
      while (r.t - t_ab < cfg::kNoLightSafingMin_s - 0.1) r.tick();
      const uint16_t cr0 = r.e.clearLockoutRefused();
      r.tick(Cmd::DISARM); r.tick(Cmd::CLEAR_LOCKOUT, cfg::kClearLockoutKey);
      const bool early_ref = r.e.clearLockoutRefused() == cr0 + 1 && r.o.cmd_refused == refuse::SAFING_HOLD && r.o.cmd_refused_event &&
                             r.o.relight_lockout && r.o.safing_hold_left_s > 0.0f && r.o.safing_hold_left_s < 0.2f;
      const double t_early = r.t - t_ab;
      while (r.t - t_ab < cfg::kNoLightSafingMin_s + 0.001) r.tick();
      r.tick(Cmd::CLEAR_LOCKOUT, cfg::kClearLockoutKey);
      const bool cleared = r.o.relight_lockout_clear && !r.o.safing_hold;
      const double t_clr = r.t - t_ab;
      r.tick(Cmd::DISARM); r.tick(Cmd::ARM); r.run(600); r.tick(Cmd::IGNITE); r.run(2);
      check(cause && hold_ev && arm_ref && early_ref && cleared && r.e.state() == State::PREPRESS,
            "v2.10 ground no-light safing rule (LEAD 172 (1), 5 s retry withdrawn): NO_IGNITION on the pad first start -> lockout + safing "
            "hold; ARM refused at +6 s; keyed CLEAR_LOCKOUT refused (SAFING_HOLD) before 960 s, accepted after; then ARM + IGNITE accepted",
            fmt("CLEAR refused at %.1f s, accepted at %.3f s", t_early, t_clr) + fmt(" (hold %.0f s)", cfg::kNoLightSafingMin_s));
    }
#include "test_v27.inc"
#include "test_v28.inc"
#include "test_v29.inc"
  }

  // ------------------------------------------------------------- v2.3 FM-PWR-01 TVC supply, e-fuse, pad-only aborts, heater permit
  {
    // (1) in-situ source-resistance estimator on a synthetic 25 mOhm source with servo-like current pulses and ADC noise
    {
      SupplyMonitor m; uint32_t sd = 12345u;
      auto rnd = [&]() { sd = sd * 1664525u + 1013904223u; return (sd >> 8) * (1.0f / 16777216.0f); };
      const float R = 0.025f, voc = 8.30f;
      for (int k = 0; k < 4000; ++k) {
        const float i = 0.5f + ((k / 40) % 4 == 0 ? 9.0f * rnd() : 0.3f * rnd());
        const float v = voc - R * i + 0.006f * (rnd() - 0.5f) * 3.46f;
        m.step(v, i + 0.03f * (rnd() - 0.5f) * 3.46f, 1e-3f);
      }
      check(m.measured() && std::fabs(m.rsrcEstimate() - R) < 1.5e-3f, "supply: in-situ source resistance recovered (25 mOhm, 6 mV / 30 mA noise)",
            fmt("estimate %.2f mOhm, accepted %.0f", m.rsrcEstimate() * 1e3, (double)m.accepted()));
      const float vp = m.vplugPred(), expect = voc - (2 * cfg::kTvcServoDesign_A + cfg::kAuxDesign_A) * R - cfg::kTvcServoDesign_A * cfg::kRBranchEqCal_ohm;
      check(std::fabs(vp - expect) < 0.02f, "supply: predicted both-stall plug voltage uses the measured resistance", fmt("%.3f V vs %.3f V", vp, expect));
      SupplyMonitor q;
      for (int k = 0; k < 3000; ++k) q.step(8.10f - 0.015f * 0.4f, 0.4f, 1e-3f);
      check(!q.measured() && std::fabs(q.rsrcUsed() - cfg::kRSrcCal_ohm) < 1e-6f, "supply: no excitation -> no estimate, bench calibration used");
      check(std::fabs(q.vplugPred() - 7.612f) < 0.01f, "supply: 8.1 V rest with the LEAD basis (15/20 mOhm) predicts 7.61 V (calc/tvc_supply_budget_v1)",
            fmt("%.3f V", q.vplugPred()));
      SupplyMonitor w;   // a lower in-situ value never replaces the bench calibration
      for (int k = 0; k < 4000; ++k) { const float i = (k / 50) % 2 ? 8.0f : 0.5f; w.step(8.3f - 0.008f * i, i, 1e-3f); }
      check(w.measured() && std::fabs(w.rsrcUsed() - cfg::kRSrcCal_ohm) < 1e-6f, "supply: 8 mOhm measured < 15 mOhm calibration -> calibration kept (conservative)",
            fmt("estimate %.2f mOhm", w.rsrcEstimate() * 1e3));
    }
    struct Rig3 {
      EngineEcu e; Inputs in; Commands c; Outputs o; LogRecord r; double t = 0; float voc = 8.30f, rsrc = 0.015f, iload = 0.4f;
      Rig3() {
        e.init(0.0); e.ptank_cal_ok = true; loadNotch(e);
        in.arm_plug_present = true; in.arm_bus_on = true; in.mv_closed_sw = true; in.ptank_Pa = 50e5f;
        in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f;
        setPc(101325.f); setI(0.4f);
      }
      void setPc(float pabs) { in.pc_Pa = pabs - 101325.f; in.pc_raw_V = 0.5f + 4.f * in.pc_Pa / cfg::kPcXdcrFs_Pa; }
      void setI(float i) { iload = i; in.ibat_A = i; in.vbat_V = voc - rsrc * i; }
      void tick(Cmd cmd = Cmd::NOP, uint16_t arg = 0) {
        t += 1e-3; in.t_s = t; c = Commands(); c.fast_valid = true; c.thrust_sp_N = 300.f;
        if (cmd != Cmd::NOP) { c.state_valid = true; c.cmd = cmd; c.arg = arg; }
        setI(iload);
        in.pintle_meas_m = o.pintle_cmd_m;   // v2.6 ideal pintle follower
        idealTorch(in, o);   // v2.7
        e.step(in, c, o); e.fillLog(in, o, r);
      }
      void run(int n) { for (int i = 0; i < n; ++i) tick(); }
      void sweep(int n) { for (int i = 0; i < n; ++i) { setI(((i / 60) % 3 == 0) ? 9.5f : 0.6f); tick(); } setI(0.4f); }   // servo-like pulses
      bool toRun() {
        tick(Cmd::ARM); run(600); tick(Cmd::IGNITE);
        in.mv_open_sw = true; in.mv_closed_sw = false; in.pfeed_Pa = 48e5f;
        for (int i = 0; i < 1000 && e.state() != State::IGNITION; ++i) tick();
        run(130); setPc(kLitStartAbs);   // v2.9: light at a lit-start plateau (A5 8 bar abs in the hold), then 15 bar
        for (int i = 0; i < 100 && e.state() != State::RUN; ++i) tick();
        setPc(15e5f);
        return e.state() == State::RUN;
      }
    };
    // (2) ARM rule (v2.4, LEAD: V_val 6.6 V): rest 8.26 V passes the 8.1 V permit, but a 100 mOhm (aged or cold) source seen
    //     in the pre-flight TVC sweep predicts 6.1 V at the plug -> ARM refused with TVC_SUPPLY (19). A 45 mOhm source
    //     (7.2 V predicted; refused under the v2.3 7.6 V basis) is now accepted.
    {
      Rig3 g; g.rsrc = 0.100f;
      g.tick(Cmd::TVC_TEST_ENABLE, 1); g.sweep(2000); g.tick(Cmd::TVC_TEST_ENABLE, 0); g.run(400);
      g.tick(Cmd::ARM);
      check(g.e.state() == State::SAFE && g.e.abortCause() == Abort::TVC_SUPPLY,
            "FM-PWR-01: 100 mOhm source found in the TVC sweep -> predicted < 6.6 V (V_val) -> ARM refused, cause 19 TVC_SUPPLY",
            fmt("rest %.2f V, R used %.1f mOhm, predicted %.2f V", g.in.vbat_V, g.o.rsrc_ohm * 1e3, g.o.vplug_pred_V));
      check((g.o.gimbal_flags & tlmg::RSRC_MEASURED) && (g.o.gimbal_flags & tlmg::SUPPLY_DEGRADED), "FM-PWR-01: TLM_GIMBAL flags show the estimate and the degraded supply");
      Rig3 c; c.rsrc = 0.045f;
      c.tick(Cmd::TVC_TEST_ENABLE, 1); c.sweep(2000); c.tick(Cmd::TVC_TEST_ENABLE, 0); c.run(400); c.tick(Cmd::ARM);
      check(c.e.state() == State::ARMED, "FM-PWR-01: cold 45 mOhm source predicts 7.2 V >= 6.6 V -> ARM accepted (v2.3 7.6 V basis refused it)",
            fmt("R used %.1f mOhm, predicted %.2f V", c.o.rsrc_ohm * 1e3, c.o.vplug_pred_V));
      Rig3 h; h.tick(Cmd::TVC_TEST_ENABLE, 1); h.sweep(2000); h.tick(Cmd::TVC_TEST_ENABLE, 0); h.run(400); h.tick(Cmd::ARM);
      check(h.e.state() == State::ARMED, "FM-PWR-01: 15 mOhm source at 8.3 V -> ARM accepted", fmt("predicted %.2f V", h.o.vplug_pred_V));
    }
    // (3) in flight: supply sags (pack 6.9 V, 15 mOhm) -> predicted 6.4 V < 6.6 V -> flag 100 ms after the 3 Hz-filtered
    //     prediction crosses 6.6 V (~0.2 s), no abort;
    //     log flags b14, vplug_pred_mV, ibat_cA
    {
      Rig3 g; const bool run_ok = g.toRun();
      g.voc = 6.90f; g.setI(3.0f); g.run(300);
      check(run_ok && g.e.state() == State::RUN && g.o.tvc_supply_degraded && (g.r.flags & 0x4000) && g.e.abortCause() == Abort::NONE,
            "FM-PWR-01 in flight: degraded flag set, burn continues (no abort)",
            fmt("state %.0f, predicted %.2f V, log vplug %.0f mV", (double)g.e.state(), g.o.vplug_pred_V, (double)g.r.vplug_pred_mV));
      check(g.r.version == kLogVersion && g.r.ibat_cA == 300, "log v12 (v10 fields unchanged) carries the battery current (0.01 A)", fmt("ibat_cA %.0f", (double)g.r.ibat_cA));
      g.voc = 8.30f; g.setI(1.0f); g.run(450); const bool still = g.o.tvc_supply_degraded; g.run(550);
      check(still && !g.o.tvc_supply_degraded, "FM-PWR-01: flag holds 0.5 s after recovery, then clears (min + 0.1 V hysteresis)",
            fmt("predicted %.2f V", g.o.vplug_pred_V));
    }
    // (4) BATT_LOW and tank over-pressure: abort only before the first start
    {
      Rig3 p; p.tick(Cmd::ARM); p.run(10); p.voc = 6.40f; p.run(300);
      check(p.e.abortCause() == Abort::TVC_SUPPLY && (p.o.fault_bits & fault::BATT_LOW),
            "pad (ARMED, no start): pack collapse to 6.4 V aborts (TVC_SUPPLY trips at 100 ms, before BATT_LOW at 200 ms; both recorded)",
            fmt("cause %.0f", (double)p.e.abortCause()));
      auto toCoastPrepress = [](Rig3& g) {
        if (!g.toRun()) return false;
        g.run(300); g.tick(Cmd::SHUTDOWN); g.setPc(101325.f);
        for (int i = 0; i < 3000 && g.e.state() != State::COAST; ++i) g.tick();
        g.in.mv_open_sw = false; g.in.pfeed_Pa = 0.0f;      // line not primed -> relight goes through PREPRESS
        g.tick(Cmd::RELIGHT);
        return g.e.state() == State::PREPRESS;
      };
      Rig3 q; const bool pre = toCoastPrepress(q);
      q.voc = 6.40f; q.run(300);
      check(pre && q.e.abortCause() == Abort::NONE && (q.o.fault_bits & fault::BATT_LOW), "relight PREPRESS in flight: BATT_LOW flags, no abort",
            fmt("prepress %.0f, state %.0f", pre, (double)q.e.state()));
      Rig3 u; const bool pre2 = toCoastPrepress(u);
      u.in.ptank_Pa = 66e5f; u.run(300);
      check(pre2 && u.e.abortCause() == Abort::TANK_OVERPRESSURE, "relight PREPRESS, tank > 65 bar: still aborts while the relief device is unconfirmed (LEAD condition a)");
      Rig3 x; x.e.tank_overp_pad_only = true; const bool pre3 = toCoastPrepress(x);
      x.in.ptank_Pa = 66e5f; x.run(300);
      check(pre3 && x.e.abortCause() == Abort::NONE && (x.o.fault_bits & fault::TANK_OVERP), "same with tank_overp_pad_only (after condition a): flag only");
    }
    // (5) e-fuse (F401 deleted): pad only
    {
      Rig3 g; g.tick(Cmd::ARM); g.run(10); g.setI(25.0f); g.run(1100);
      check(g.e.abortCause() == Abort::OVERCURRENT, "e-fuse: 25 A for 1.1 s in ARMED aborts (cause 20 OVERCURRENT)");
      Rig3 s; s.tick(Cmd::TVC_TEST_ENABLE, 1); s.setI(25.0f); s.run(1100);
      check(!s.o.servo_enable_tvc && s.e.abortCause() == Abort::OVERCURRENT, "e-fuse: in SAFE the TVC test power is dropped and an inhibit recorded");
      Rig3 f; const bool run_ok = f.toRun(); f.setI(25.0f); f.run(1100);
      check(run_ok && f.e.state() == State::RUN, "e-fuse: no action in flight (TVC power is kept)");
    }
    // (6) tank heater permit (firmware layer)
    {
      Rig3 g; g.in.arm_plug_present = false; g.in.arm_bus_on = false; g.run(5);
      const bool p0 = g.o.heater_permit && (g.o.gimbal_flags & tlmg::HEATER_PERMIT);
      g.in.ptank_Pa = 59e5f; g.run(5); const bool p_hot = g.o.heater_permit;
      g.in.ptank_Pa = 50e5f; g.in.arm_plug_present = true; g.run(5); const bool p_plug = g.o.heater_permit;
      g.in.arm_bus_on = true; g.tick(Cmd::ARM); g.run(5); const bool p_arm = g.o.heater_permit;
      check(p0 && !p_hot && !p_plug && !p_arm && g.e.state() == State::ARMED, "heater permit: SAFE only, cut above 58 bar g, with the ARM plug, and when ARMED",
            fmt("%.0f %.0f %.0f", p0, p_hot, p_plug));
    }
  }
  // ------------------------------------------------------------- v2.4 GNC command shaping, ENG-07d notch, ENG-07b saturation episodes
  {
    // (1) structural low-pass, GNC sim6 equations: continuous 2nd order 50 rad/s zeta 0.5 overshoots 16.3 % at 72.6 ms
    {
      Lpf2Cmd f; f.reset(0.0f); double pk = 0, tpk = 0; float y = 0;
      for (int k = 1; k <= 1000; ++k) { y = f.step(1.0f, cfg::kGimbalCmdLpfW_radps, cfg::kGimbalCmdLpfZeta, 1e-3f); if (y > pk) { pk = y; tpk = k * 1e-3; } }
      check(std::fabs(pk - 1.163) < 0.01 && std::fabs(tpk - 0.0726) < 0.003 && std::fabs(y - 1.0f) < 1e-3f,
            "GNC command low-pass (50 rad/s, zeta 0.5, sim6 difference equations): overshoot 16.3 %, peak 72.6 ms, unity DC",
            fmt("peak %.4f at %.1f ms, final %.5f", pk, tpk * 1e3, y));
    }
    // gain/phase of the shaped engine command (alpha) for a small sine (rate limit inactive), notch off/on.
    // v2.8.3: these checks are about the LINEAR part of the chain (low-pass + notch), so the shapers below run with the
    // gnc.json v3 tracker's acceleration limit set to 0 (plain 100 deg/s limiter, inactive at 0.05 deg). The tracker is amplitude
    // dependent (0.05 deg at 35 Hz needs 2418 deg/s2 > 2000) and is tested on its own in sil/test_v28.inc group (26).
    auto chainGain = [](TvcShaper& sh, double fhz, double amp_rad, double* ph) {
      const float z[2] = {0, 0}; sh.reset(z);
      double sc = 0, ss = 0; int n = 0; const int N0 = 3000, N = 3000 + static_cast<int>(std::ceil(20.0 / fhz * 1000.0));
      for (int k = 0; k < N; ++k) {
        const double tt = k * 1e-3; const float c[2] = {static_cast<float>(amp_rad * std::sin(2 * M_PI * fhz * tt)), 0.0f};
        float oe[2], ou[2]; sh.step(c, 1e-3f, oe, ou);
        if (k >= N0) { sc += oe[0] * std::cos(2 * M_PI * fhz * tt); ss += oe[0] * std::sin(2 * M_PI * fhz * tt); ++n; }
      }
      *ph = std::atan2(sc, ss) * 180 / M_PI; return 2 * std::sqrt(sc * sc + ss * ss) / n / amp_rad;
    };
    {
      TvcShaper a; a.accel_limit_radps2 = 0.0f; double p8, p35, p2;
      const double g8 = chainGain(a, 8.0, 0.05 * M_PI / 180, &p8), g35 = chainGain(a, 35.0, 0.05 * M_PI / 180, &p35), g2 = chainGain(a, 2.0, 0.05 * M_PI / 180, &p2);
      const double w = 2 * M_PI * 35.0 / cfg::kGimbalCmdLpfW_radps, g35c = 1.0 / std::sqrt((1 - w * w) * (1 - w * w) + (2 * cfg::kGimbalCmdLpfZeta * w) * (2 * cfg::kGimbalCmdLpfZeta * w));
      check(std::fabs(g35 - g35c) < 0.1 * g35c, "shaping chain small-signal gain at 35 Hz (rocking band) matches the continuous low-pass",
            fmt("%.4f (%.1f dB) vs %.4f", g35, 20 * std::log10(g35), g35c));
      check(true, "shaping chain small-signal response (informational, notch off): gain / phase", fmt("2 Hz %.3f / %.1f deg", g2, p2) + fmt(", 8 Hz %.3f / %.1f deg", g8, p8));
      TvcShaper b; b.accel_limit_radps2 = 0.0f; b.setNotch(true, cfg::kGimbalNotchHz, cfg::kGimbalNotchQ, cfg::kGimbalNotchDepth_dB, 1e-3f);
      double q2, q8, q35, q26, q46, p26, p46;
      TvcShaper a2; a2.accel_limit_radps2 = 0.0f;
      const double h2 = chainGain(b, 2.0, 0.05 * M_PI / 180, &q2), h8 = chainGain(b, 8.0, 0.05 * M_PI / 180, &q8), h35 = chainGain(b, 35.0, 0.05 * M_PI / 180, &q35);
      const double h26 = chainGain(b, 26.4, 0.05 * M_PI / 180, &q26), h46 = chainGain(b, 45.7, 0.05 * M_PI / 180, &q46);
      const double g26 = chainGain(a2, 26.4, 0.05 * M_PI / 180, &p26), g46 = chainGain(a2, 45.7, 0.05 * M_PI / 180, &p46);
      check(std::fabs(20 * std::log10(h35 / g35) - cfg::kGimbalNotchDepth_dB) < 0.5, "ENG-07d notch (35 Hz, Q 1, -12 dB) adds its depth at f0 in the shaping chain",
            fmt("%.2f dB", 20 * std::log10(h35 / g35)));
      check(true, "ENG-07d notch cost/benefit (informational): extra attenuation at the GNC band edges and phase lag at 2/8 Hz",
            fmt("26.4 Hz %.1f dB, 45.7 Hz %.1f dB", 20 * std::log10(h26 / g26), 20 * std::log10(h46 / g46)) +
            fmt(", phase change 2 Hz %.1f deg, 8 Hz %.1f deg", q2 - p2, q8 - p8) + fmt(", gain 2 Hz %.3f, 8 Hz %.3f", h2 / g2, h8 / g8));
      // setter semantics: an out-of-range enable request is ignored, disabling always works
      const bool r_bad = b.setNotch(true, 300.0f, 1.0f, -12.0f, 1e-3f);
      const bool still = b.notchEnabled() && std::fabs(b.notchHz() - cfg::kGimbalNotchHz) < 1e-4f;
      b.setNotch(false, 0, 0, 0, 1e-3f);
      check(!r_bad && still && !b.notchEnabled() && !cfg::kGimbalNotchEnabled,
            "notch setter: 300 Hz request ignored (35 Hz kept), disable works, default build constant is OFF");
    }
    // (2) large and fast commands: hard 7 deg vector limit after the low-pass, 100 deg/s shaping, ramp lag of the chain
    {
      TvcShaper sh; const float z[2] = {0, 0}; sh.reset(z);
      double nmax = 0, rmax = 0; bool b1 = false; float prev = 0, oe[2], ou[2];
      for (int k = 0; k < 600; ++k) {
        const float c[2] = {static_cast<float>(10 * M_PI / 180), static_cast<float>(10 * M_PI / 180)};
        sh.step(c, 1e-3f, oe, ou);
        nmax = std::max(nmax, static_cast<double>(std::hypot(oe[0], oe[1])));
        if (k > 0) rmax = std::max(rmax, std::fabs(oe[0] - prev) / 1e-3);
        prev = oe[0]; b1 |= (sh.limitFlags() & 2u) != 0;
      }
      check(nmax <= cfg::kGimbalRadialLimit_rad + 1e-6 && (sh.limitFlags() & 1u) && b1,
            "10/10 deg command: shaped vector norm never exceeds 7 deg (limit after the low-pass), b0/b1 flagged",
            fmt("max norm %.4f deg, max rate %.1f deg/s", nmax * 180 / M_PI, rmax * 180 / M_PI));
      // 100 deg/s ramp -6 -> +6 deg, lag at 100 ms. (a) v2.8.2 chain (plain limiter = acceleration limit 0): low-pass lag
      // 2 zeta / w x rate = 2.0 deg. (b) v2.8.3 flight chain (gnc.json v3 tracker): the tracker reaches 100 deg/s after v / a = 50 ms
      // and then lags v^2 / 2a = 2.5 deg, plus the low-pass 2.0 deg and its decaying transient (analytic about +0.3 deg at 100 ms for
      // zeta 0.5) = about 4.8 deg. Expected value: independent double-precision transcription of the sim6 equations (tracker, then the
      // semi-implicit low-pass), tolerance 0.02 deg.
      auto rampLag = [&](float acc) {
        TvcShaper r; r.accel_limit_radps2 = acc; r.reset(z); double lag = 0;
        for (int k = 0; k <= 160; ++k) {
          const double tt = k * 1e-3, cd = -6.0 + std::min(12.0, 100.0 * tt);
          const float c[2] = {static_cast<float>(cd * M_PI / 180), 0.0f};
          if (k == 0) { const float s0[2] = {c[0], 0.0f}; r.reset(s0); }
          r.step(c, 1e-3f, oe, ou);
          if (k == 100) lag = cd - oe[0] * 180 / M_PI;
        }
        return lag;
      };
      const double lag0 = rampLag(0.0f), lag1 = rampLag(cfg::kGimbalAccelLimit_radps2);
      double lagr = 0;
      {
        const double Ar = cfg::kGimbalAccelLimit_radps2, Vr = cfg::kGimbalRateLimit_radps, Wr = cfg::kGimbalCmdLpfW_radps, Zr = cfg::kGimbalCmdLpfZeta;
        const double dtr = 1e-3;
        double yr = -6.0 * M_PI / 180, vr = 0, ly = yr, lyd = 0;
        for (int k = 1; k <= 100; ++k) {
          const double x = (-6.0 + std::min(12.0, 100.0 * k * dtr)) * M_PI / 180, e = x - yr;
          double vd = std::min({std::sqrt(2 * Ar * std::fabs(e)), std::fabs(e) / dtr, Vr});
          if (e < 0) vd = -vd;
          vr += std::max(-Ar * dtr, std::min(Ar * dtr, vd - vr)); yr += vr * dtr;
          lyd += (Wr * Wr * (yr - ly) - 2 * Zr * Wr * lyd) * dtr; ly += lyd * dtr;
          if (k == 100) lagr = (x - ly) * 180 / M_PI;
        }
      }
      check(lag0 > 1.6 && lag0 < 2.1, "100 deg/s command ramp, acceleration limit 0 (v2.8.2 plain limiter): chain lag about 2 zeta / w x rate = 2.0 deg",
            fmt("lag %.2f deg at 100 ms", lag0));
      check(std::fabs(lag1 - lagr) < 0.02 && lagr > 4.3 && lagr < 5.1,
            "v2.8.3 100 deg/s command ramp through the flight chain (gnc.json v3 tracker 2000 deg/s2 + low-pass): lag = tracker v^2/2a 2.5 deg "
            "+ low-pass 2.0 deg + transient, matches the double-precision sim6 transcription (informational for GNC/B-TVC-1)",
            fmt("lag %.3f deg at 100 ms, reference %.3f deg", lag1, lagr));
    }
    // (3) ENG-07b actuator-saturation episodes and the SET_GIMBAL_NOTCH command, on the full ECU
    struct RigS {
      EngineEcu e; Inputs in; Commands c; Outputs o; LogRecord r; double t = 0;
      float cmd[2] = {0, 0}, meas[2] = {0, 0}, tau_a = 0.015f, rate_a = 1e9f, offset = 0;
      bool jam = false;
      explicit RigS(bool notch = true) {
        e.init(0.0); e.ptank_cal_ok = true; if (notch) loadNotch(e);
        in.arm_plug_present = true; in.arm_bus_on = true; in.mv_closed_sw = true; in.ptank_Pa = 50e5f;
        in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f;
        in.vbat_V = 8.294f; in.ibat_A = 0.4f; setPc(101325.f);
      }
      void setPc(float pabs) { in.pc_Pa = pabs - 101325.f; in.pc_raw_V = 0.5f + 4.f * in.pc_Pa / cfg::kPcXdcrFs_Pa; }
      void tick(Cmd cm = Cmd::NOP, uint16_t arg = 0) {
        t += 1e-3; in.t_s = t; c = Commands(); c.fast_valid = true; c.thrust_sp_N = 300.f;
        c.gimbal_cmd_rad[0] = cmd[0]; c.gimbal_cmd_rad[1] = cmd[1];
        if (cm != Cmd::NOP) { c.state_valid = true; c.cmd = cm; c.arg = arg; }
        for (int k = 0; k < 2; ++k) {   // actuator: first-order lag tau_a, rate limit rate_a (engine side), or jammed
          if (!jam) meas[k] += clampf((o.gimbal_cmd_shaped_rad[k] - meas[k]) * (1e-3f / tau_a), -rate_a * 1e-3f, rate_a * 1e-3f);
          in.gimbal_meas_rad[k] = meas[k] + (k == 0 ? offset : 0.0f);
        }
        in.pintle_meas_m = o.pintle_cmd_m;   // v2.6 ideal pintle follower
        idealTorch(in, o);   // v2.7
        e.step(in, c, o); e.fillLog(in, o, r);
      }
      void run(int n) { for (int i = 0; i < n; ++i) tick(); }
      void steps(int n_cycles, float amp_deg) {   // +/- amp on alpha every 0.3 s
        for (int i = 0; i < n_cycles; ++i) { cmd[0] = static_cast<float>((i % 2 ? -1 : 1) * amp_deg * M_PI / 180); run(300); }
        cmd[0] = 0; run(300);
      }
    };
    {
      RigS h; h.tick(Cmd::TVC_TEST_ENABLE, 1); h.steps(6, 5.0f);
      check(h.o.gimbal_sat_long == 0 && !(h.o.gimbal_flags & tlmg::SAT_LONG), "healthy actuator (15 ms lag) on +/-5 deg steps through the shaping: no episode > 0.1 s",
            fmt("longest %.0f ms, episodes %.0f", h.o.gimbal_sat_max_s * 1e3, (double)h.o.gimbal_sat_count));
      RigS f; f.tau_a = 0.009f; f.tick(Cmd::TVC_TEST_ENABLE, 1); f.steps(6, 5.0f);
      RigS sl; sl.tau_a = 0.022f; sl.tick(Cmd::TVC_TEST_ENABLE, 1); sl.steps(6, 5.0f);
      check(f.o.gimbal_sat_long == 0 && sl.o.gimbal_sat_long == 0, "actuator lag 9 and 22 ms (10-25 Hz class): no false episode > 0.1 s",
            fmt("longest %.0f / %.0f ms", f.o.gimbal_sat_max_s * 1e3, sl.o.gimbal_sat_max_s * 1e3));
      RigS v; v.rate_a = static_cast<float>(40 * M_PI / 180); v.tick(Cmd::TVC_TEST_ENABLE, 1); v.steps(6, 5.0f);
      check(v.o.gimbal_sat_long > 0 && (v.o.gimbal_flags & tlmg::SAT_LONG), "speed-limited actuator (40 deg/s < 100 deg/s shaping): episodes > 0.1 s counted, SAT_LONG set",
            fmt("longest %.0f ms, long %.0f, episodes %.0f", v.o.gimbal_sat_max_s * 1e3, (double)v.o.gimbal_sat_long, (double)v.o.gimbal_sat_count));
      // v2.6: with the required notch in the shaping chain the episode starts ~6 ms later than in v2.4 (56 ms after the jam)
      // v2.8.3: the gnc.json v3 tracker moves the shaped 3 deg command over ~80 ms instead of 30 ms, so the episode starts later.
      // v2.8.3 runs 1-2 kept the fixed 170 ms window and FAILED (sat_ms 94 at 170 ms; results/sil_v2p8_3/test_core_v2p8_3_run1/2.txt);
      // the check now runs until SAT_LONG (<= 0.30 s after the jam) and reports the jam-to-SAT_LONG time.
      RigS j; j.tick(Cmd::TVC_TEST_ENABLE, 1); j.run(100); j.jam = true; j.cmd[0] = static_cast<float>(3 * M_PI / 180);
      int n_long = -1;
      for (int n = 1; n <= 300 && n_long < 0; ++n) { j.tick(); if (j.o.gimbal_sat_long == 1) n_long = n; }
      j.run(10);
      const bool long1 = n_long > 0 && j.o.gimbal_sat_long == 1 && (j.o.gimbal_flags & tlmg::SAT_LONG) && j.r.sat_ms > 100 && (j.r.sat_flags & 0x04u) && j.r.version == kLogVersion;
      check(long1, "jammed actuator (torque saturation proxy): episode passes 0.1 s, SAT_LONG, log v5 sat_ms/sat_flags b2 (v2.8.3: within 0.30 s of the jam)",
            fmt("SAT_LONG %.0f ms after the jam, sat_ms %.0f, flags %.0f", n_long, (double)j.r.sat_ms, (double)j.r.sat_flags));
      RigS s2; s2.tick(Cmd::TVC_TEST_ENABLE, 1); s2.run(100);
      s2.offset = static_cast<float>(1.0 * M_PI / 180); s2.run(60); s2.offset = 0; s2.run(50);
      check(s2.o.gimbal_sat_long == 0 && s2.o.gimbal_sat_count == 1 && std::fabs(s2.o.gimbal_sat_max_s - 0.060f) < 0.0025f,
            "60 ms encoder excursion of 1 deg: one short episode (60 ms), not long", fmt("max %.1f ms, count %.0f", s2.o.gimbal_sat_max_s * 1e3, (double)s2.o.gimbal_sat_count));
      // per-burn statistics: the bench run's long episode is cleared at IGNITION entry
      j.jam = false; j.cmd[0] = 0; j.run(400); j.tick(Cmd::TVC_TEST_ENABLE, 0); j.run(50);
      const bool before = j.o.gimbal_sat_long == 1;
      j.tick(Cmd::ARM); j.run(600); j.tick(Cmd::IGNITE);
      j.in.mv_open_sw = true; j.in.mv_closed_sw = false; j.in.pfeed_Pa = 48e5f;
      for (int i = 0; i < 1000 && j.e.state() != State::IGNITION; ++i) j.tick();
      j.run(5);
      check(before && j.e.state() == State::IGNITION && j.o.gimbal_sat_long == 0 && !(j.o.gimbal_flags & tlmg::SAT_LONG),
            "ENG-07b statistics are per burn: the bench episode is cleared at IGNITION entry", fmt("state %.0f", (double)j.e.state()));
    }
    {
      RigS n; n.tick(Cmd::SET_GIMBAL_NOTCH, 352);
      const bool on_safe = n.o.gimbal_notch_on && std::fabs(n.e.tvc().notchHz() - 35.2f) < 1e-3f && (n.r.sat_flags & 0x10u);
      n.tick(Cmd::ARM); n.run(5); n.tick(Cmd::SET_GIMBAL_NOTCH, 0); n.run(2);
      const bool kept_armed = n.e.state() == State::ARMED && n.o.gimbal_notch_on;
      n.tick(Cmd::DISARM); n.run(2); n.tick(Cmd::SET_GIMBAL_NOTCH, 2500); n.run(2);
      const bool bad_ignored = n.o.gimbal_notch_on && std::fabs(n.e.tvc().notchHz() - 35.2f) < 1e-3f;
      n.tick(Cmd::SET_GIMBAL_NOTCH, 0); n.run(2);
      check(on_safe && kept_armed && bad_ignored && !n.o.gimbal_notch_on && !(n.r.sat_flags & 0x10u),
            "SET_GIMBAL_NOTCH: 35.2 Hz set in SAFE (log b4), ignored when ARMED, 250 Hz rejected, arg 0 disables",
            fmt("%.0f %.0f %.0f", on_safe, kept_armed, bad_ignored));
    }
    // (4) v2.6 per-axis notch (LEAD 2026-10-12, GNC csi_v3: alpha and beta modes differ 8-15 %): own f0, Q and depth per axis,
    //     settable in SAFE only, stored as NvGimbalCal, REQUIRED on both axes before IGNITE/RELIGHT
    {
      auto chainGainAx = [](TvcShaper& sh, int ax, double fhz, double amp_rad) {
        const float z[2] = {0, 0}; sh.reset(z);
        double sc = 0, ss = 0; int n = 0; const int N0 = 3000, N = 3000 + static_cast<int>(std::ceil(20.0 / fhz * 1000.0));
        for (int k = 0; k < N; ++k) {
          const double tt = k * 1e-3; float c[2] = {0.0f, 0.0f}; c[ax] = static_cast<float>(amp_rad * std::sin(2 * M_PI * fhz * tt));
          float oe[2], ou[2]; sh.step(c, 1e-3f, oe, ou);
          if (k >= N0) { sc += oe[ax] * std::cos(2 * M_PI * fhz * tt); ss += oe[ax] * std::sin(2 * M_PI * fhz * tt); ++n; }
        }
        return 2 * std::sqrt(sc * sc + ss * ss) / n / amp_rad;
      };
      const GimbalNotchCal cal = testNotchCal();
      TvcShaper off, on;
      const bool set0 = on.setNotchAxis(0, cal.ax[0], 1e-3f), set1 = on.setNotchAxis(1, cal.ax[1], 1e-3f);
      const double A = 0.05 * M_PI / 180;
      double worst = 0, il[2][2];
      for (int ax = 0; ax < 2; ++ax) for (int j = 0; j < 2; ++j) {   // axis ax driven at the centre frequency of axis j
        const double f = cal.ax[j].f0_Hz;
        il[ax][j] = 20 * std::log10(chainGainAx(on, ax, f, A) / chainGainAx(off, ax, f, A));
        worst = std::max(worst, std::fabs(il[ax][j] - notchMagDb(cal.ax[ax].f0_Hz, cal.ax[ax].q, cal.ax[ax].depth_dB, f)));
      }
      char det[200];
      std::snprintf(det, sizeof det, "alpha: %.2f dB at 22.0 / %.2f dB at 25.3 Hz; beta: %.2f dB at 22.0 / %.2f dB at 25.3 Hz; worst vs section response %.3f dB",
                    il[0][0], il[0][1], il[1][0], il[1][1], worst);
      check(set0 && set1 && worst < 0.3 && std::fabs(il[0][0] + 12.0) < 0.3 && std::fabs(il[1][1] + 15.0) < 0.3,
            "per-axis notch: alpha (22.0 Hz, Q 1.0, -12 dB) and beta (25.3 Hz, Q 1.4, -15 dB) each act with their own section", det);
      TvcShaper sx; sx.setNotchAxis(0, cal.ax[0], 1e-3f); sx.setNotchAxis(1, cal.ax[1], 1e-3f);
      NotchAxis badq = cal.ax[1]; badq.q = 20.0f;
      const bool rb = sx.setNotchAxis(1, badq, 1e-3f);
      NotchAxis aoff = sx.notchAxis(0); aoff.enabled = false;
      sx.setNotchAxis(0, aoff, 1e-3f);
      check(!rb && sx.notchAxis(1).q == cal.ax[1].q && sx.notchEnabled(1) && !sx.notchEnabled(0) && sx.notchAxis(0).f0_Hz == cal.ax[0].f0_Hz,
            "per-axis setter: Q 20 on beta refused (beta kept), alpha disabled alone (beta stays on, alpha values kept)");
      // ECU calibration record: SAFE only, all-or-nothing
      RigS g;
      GimbalNotchCal c2 = cal; c2.ax[0].f0_Hz = 19.0f; c2.ax[1].f0_Hz = 400.0f;
      const bool r1 = g.e.setGimbalNotchCal(c2);
      const float k1 = g.e.gimbalNotchCal().ax[0].f0_Hz;
      GimbalNotchCal c3 = cal; c3.ax[0].f0_Hz = 19.0f;
      g.tick(Cmd::ARM); g.run(10);
      const bool armed = g.e.state() == State::ARMED;
      const bool r2 = g.e.setGimbalNotchCal(c3);
      g.tick(Cmd::DISARM); g.run(2);
      const bool r3 = g.e.setGimbalNotchCal(c3);
      const GimbalNotchCal k3 = g.e.gimbalNotchCal();
      check(!r1 && k1 == 22.0f && armed && !r2 && r3 && k3.ax[0].f0_Hz == 19.0f && k3.ax[1].f0_Hz == 25.3f && k3.complete(),
            "setGimbalNotchCal: one axis out of range refuses both, refused when ARMED, accepted in SAFE");
      // CAN commands per axis (SAFE): SET_GIMBAL_NOTCH b15 = 1, b14 axis, b0-13 f0 [0.1 Hz]; SET_GIMBAL_NOTCH_QD b15 axis, b8-14 dB, b0-7 Q x 20
      RigS h;
      h.tick(Cmd::SET_GIMBAL_NOTCH, static_cast<uint16_t>(0x8000u | (1u << 14) | 268u));      // beta 26.8 Hz
      const bool ch1 = h.o.gimbal_cal_changed; h.tick(); const bool ch1b = h.o.gimbal_cal_changed;
      const NotchAxis a1 = h.e.tvc().notchAxis(0), b1 = h.e.tvc().notchAxis(1);
      h.tick(Cmd::SET_GIMBAL_NOTCH_QD, static_cast<uint16_t>((18u << 8) | 30u));             // alpha: -18 dB, Q 1.5
      const NotchAxis a2 = h.e.tvc().notchAxis(0), b2 = h.e.tvc().notchAxis(1);
      h.tick(Cmd::SET_GIMBAL_NOTCH_QD, static_cast<uint16_t>((1u << 15) | (12u << 8) | 2u));  // beta Q 0.1: out of range
      const bool rej = !h.o.gimbal_cal_changed && h.e.tvc().notchAxis(1).q == b2.q;
      h.tick(Cmd::SET_GIMBAL_NOTCH, 300u);                                                  // v2.4 form: both axes 30.0 Hz
      const NotchAxis a3 = h.e.tvc().notchAxis(0), b3 = h.e.tvc().notchAxis(1);
      const bool per_ok = ch1 && !ch1b && a1.f0_Hz == 22.0f && std::fabs(b1.f0_Hz - 26.8f) < 1e-4f && b1.q == 1.4f;
      const bool qd_ok = a2.q == 1.5f && a2.depth_dB == -18.0f && a2.f0_Hz == 22.0f && b2.q == 1.4f && b2.depth_dB == -15.0f && rej;
      const bool legacy_ok = std::fabs(a3.f0_Hz - 30.0f) < 1e-4f && std::fabs(b3.f0_Hz - 30.0f) < 1e-4f && a3.q == 1.5f && b3.q == 1.4f &&
                             a3.depth_dB == -18.0f && b3.depth_dB == -15.0f && a3.enabled && b3.enabled;
      check(per_ok && qd_ok && legacy_ok, "SAFE commands per axis: beta f0 only, alpha Q/depth only, bad Q refused, v2.4 both-axis form keeps per-axis Q/depth, change flagged one tick",
            fmt("%.0f %.0f %.0f", per_ok, qd_ok, legacy_ok));
      h.tick(Cmd::ARM); h.run(10);
      h.tick(Cmd::SET_GIMBAL_NOTCH, static_cast<uint16_t>(0x8000u));                        // alpha off: ignored when ARMED
      h.tick(Cmd::SET_GIMBAL_NOTCH_QD, static_cast<uint16_t>((1u << 15) | (6u << 8) | 40u)); // beta Q 2, -6 dB: ignored
      check(h.e.state() == State::ARMED && h.e.tvc().notchEnabled(0) && h.e.tvc().notchAxis(1).q == 1.4f && h.o.gimbal_notch_axes == 3u,
            "per-axis notch commands ignored when ARMED");
      // IGNITE/RELIGHT interlock: a fresh ECU (blank record) arms (B-PNT-1 needs ARM) but refuses ignition until both axes are set
      RigS u(false);
      u.tick(Cmd::ARM); u.run(600); u.tick(Cmd::IGNITE); u.run(5);
      const bool ref0 = u.e.state() == State::ARMED && u.e.ignitionRefusedNotch() == 1 && u.o.gimbal_notch_axes == 0u;
      u.tick(Cmd::DISARM); u.run(2); u.tick(Cmd::SET_GIMBAL_NOTCH, static_cast<uint16_t>(0x8000u | 220u));   // alpha only
      u.tick(Cmd::ARM); u.run(600); u.tick(Cmd::IGNITE); u.run(5);
      const bool ref1 = u.e.state() == State::ARMED && u.e.ignitionRefusedNotch() == 2 && u.o.gimbal_notch_axes == 1u;
      u.tick(Cmd::DISARM); u.run(2); u.tick(Cmd::SET_GIMBAL_NOTCH, static_cast<uint16_t>(0x8000u | (1u << 14) | 253u));
      u.tick(Cmd::ARM); u.run(600); u.tick(Cmd::IGNITE); u.run(5);
      const bool acc = (u.e.state() == State::PREPRESS || u.e.state() == State::IGNITION) && u.e.ignitionRefusedNotch() == 2;
      check(ref0 && ref1 && acc, "IGNITE refused without a notch on both axes (blank, alpha only), accepted once beta is set",
            fmt("%.0f %.0f %.0f", ref0, ref1, acc));
      // non-volatile record
      NvGimbalCal rec = nvGimbalEncode(cal, 7, 123456u);
      uint8_t b[32]; std::memcpy(b, &rec, 32);
      GimbalNotchCal dcal; NvGimbalCal raw;
      const NvGimbalStatus st = nvGimbalDecode(b, &dcal, &raw);
      bool same = st == NvGimbalStatus::VALID && raw.seq == 7 && raw.t_ms == 123456u;
      for (int k = 0; k < 2; ++k)
        same = same && dcal.ax[k].enabled == cal.ax[k].enabled && std::fabs(dcal.ax[k].f0_Hz - cal.ax[k].f0_Hz) <= 0.005f &&
               std::fabs(dcal.ax[k].q - cal.ax[k].q) <= 0.0005f && std::fabs(dcal.ax[k].depth_dB - cal.ax[k].depth_dB) <= 0.005f;
      uint8_t blank[32]; std::memset(blank, 0xFF, 32);
      GimbalNotchCal db; const NvGimbalStatus sb = nvGimbalDecode(blank, &db);
      uint8_t bad[32]; std::memcpy(bad, b, 32); bad[5] ^= 0x01;
      GimbalNotchCal dc; const NvGimbalStatus sc = nvGimbalDecode(bad, &dc);
      GimbalNotchCal hi = cal; hi.ax[1].f0_Hz = 300.0f;
      NvGimbalCal rh = nvGimbalEncode(hi, 8, 0); uint8_t bh[32]; std::memcpy(bh, &rh, 32);
      GimbalNotchCal dh; const NvGimbalStatus sh = nvGimbalDecode(bh, &dh);
      check(sizeof(NvGimbalCal) == 32 && same && sb == NvGimbalStatus::BLANK && !db.ax[0].enabled && !db.ax[1].enabled &&
            sc == NvGimbalStatus::CORRUPT && !dc.complete() && sh == NvGimbalStatus::OUT_OF_RANGE && !dh.complete() &&
            nvGimbalBad(sc) && nvGimbalBad(sh) && !nvGimbalBad(sb),
            "NvGimbalCal 32 B: round trip within 0.01 Hz / 0.001 / 0.01 dB; blank = no notch; corrupt or out of range = no notch + GIMBAL_CAL_BAD");
      RigS w(false); const bool ok_boot = w.e.setGimbalNotchCal(dcal);
      check(ok_boot && w.e.gimbalNotchCal().complete() && std::fabs(w.e.gimbalNotchCal().ax[1].f0_Hz - 25.3f) < 0.006f,
            "boot path: the decoded record is applied in SAFE (both axes, beta 25.3 Hz)");
      // B-TVC-1 frequency-response mode: TVC_TEST_ENABLE 2 bypasses the shaping low-pass and the notch, in SAFE only
      RigS q; q.tick(Cmd::TVC_TEST_ENABLE, 2); q.cmd[0] = static_cast<float>(1.0 * M_PI / 180); q.run(20);
      const float raw20 = q.o.gimbal_cmd_shaped_rad[0];
      const bool byp_safe = q.e.tvc().bypass_filters;
      RigS q1; q1.tick(Cmd::TVC_TEST_ENABLE, 1); q1.cmd[0] = static_cast<float>(1.0 * M_PI / 180); q1.run(20);
      const float flt20 = q1.o.gimbal_cmd_shaped_rad[0];
      q.cmd[0] = 0; q.run(100); q.tick(Cmd::ARM); q.run(10);
      check(std::fabs(raw20 - static_cast<float>(M_PI / 180)) < 1e-6f && byp_safe && flt20 < 0.6f * static_cast<float>(M_PI / 180) &&
            q.e.state() == State::ARMED && !q.e.tvc().bypass_filters,
            "TVC_TEST_ENABLE 2 (B-TVC-1 FRF): filters bypassed in SAFE (1 deg reached in 20 ms, slew-limited only), restored when ARMED",
            fmt("raw %.3f deg, flight shaping %.3f deg at 20 ms", raw20 * 57.29578, flt20 * 57.29578));
    }
  }
  // ------------------------------------------------------------- v2.6 pintle stall/tracking monitor, jam record, LEAD rules (a)/(b)
  {
    // Logic rig: the needle follows the command after a latency (3 ms frame + 4 ms internal) at a limited speed (HV69 mid-stroke
    // ~20-28 mm/s), or sticks, or runs away. Rail current: idle / moving / stalled. NOT the dynamics model (calc/pintle_dynamics_v2.py
    // derives the thresholds); this checks the firmware logic only.
    struct RigP {
      EngineEcu e; Inputs in; Commands c; Outputs o; LogRecord r; double t = 0; float thrust = 300.f;
      enum Mode { FOLLOW, STUCK, RUNAWAY } mode = FOLLOW;
      float v_mps = 0.025f, v_run_mps = 0.020f, x = 0.0f;
      float i_idle = 0.3f, i_move = 0.8f, i_stall = 1.5f;
      bool isense = false, follow_pc = true, mv_auto = true;
      float pc_frac = 1.0f;
      const int kLat = 7;
      float hist[16] = {0}; int hi = 0;
      int n_events = 0, n_clear = 0; uint8_t sat_or = 0; float noprog_max = 0;
      RigP() {
        e.init(0.0); e.ptank_cal_ok = true; loadNotch(e);
        in.arm_plug_present = true; in.arm_bus_on = true; in.vbat_V = 8.2f; in.ibat_A = 0.4f; in.mv_closed_sw = true; in.ptank_Pa = 50e5f;
        in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f; setPc(101325.f);
      }
      void setPc(float pabs) { in.pc_Pa = pabs - 101325.f; in.pc_raw_V = 0.5f + 4.f * in.pc_Pa / cfg::kPcXdcrFs_Pa; }
      void tick(Cmd cm = Cmd::NOP, uint16_t arg = 0) {
        t += 1e-3; in.t_s = t; c = Commands(); c.fast_valid = true; c.thrust_sp_N = thrust;
        if (cm != Cmd::NOP) { c.state_valid = true; c.cmd = cm; c.arg = arg; }
        hist[hi] = o.pintle_cmd_m; const float tgt = hist[(hi + 16 - kLat) % 16]; hi = (hi + 1) % 16;
        const float x0 = x;
        if (mode == FOLLOW) x += clampf(tgt - x, -v_mps * 1e-3f, v_mps * 1e-3f);
        else if (mode == RUNAWAY) x = std::fmin(4.2e-3f, x + v_run_mps * 1e-3f);
        in.pintle_meas_m = x;
        const bool moving = std::fabs(x - x0) > 1e-9f, wants = std::fabs(tgt - x) > 0.02e-3f;
        in.pintle_i_valid = isense; in.pintle_i_A = moving ? i_move : (wants ? i_stall : i_idle);
        if (mv_auto) {   // main valve follows its opener (open beyond 2/3 of the travel) and the latch; line primed when open
          if (o.servo_us[3] > 1800.f) { in.mv_open_sw = true; in.mv_closed_sw = false; in.pfeed_Pa = 48e5f; }
          if (!o.mv_latch && o.servo_us[3] < 1600.f) { in.mv_open_sw = false; in.mv_closed_sw = true; }
        }
        if (follow_pc && o.state == State::RUN && o.pc_sp_active_Pa > 0) setPc(pc_frac * o.pc_sp_active_Pa);
        idealTorch(in, o);   // v2.7
        e.step(in, c, o); e.fillLog(in, o, r);
        if (o.pintle_jam_event) ++n_events;
        if (o.maint_clear_jam) ++n_clear;
        sat_or |= r.sat_flags; noprog_max = std::fmax(noprog_max, o.pintle_noprog_s);
      }
      void run(int n) { for (int i = 0; i < n; ++i) tick(); }
      int until(State s, int nmax) { int n = 0; while (e.state() != s && n < nmax) { tick(); ++n; } return n; }
      bool toRun(float pc_lit = 6.0e5f) {   // ARM -> IGNITE -> PREPRESS (MV ramps open) -> IGNITION -> lit at 0.15 s -> RUN
        tick(Cmd::ARM); run(600); tick(Cmd::IGNITE);
        until(State::IGNITION, 2000); run(150); setPc(pc_lit);
        until(State::RUN, 100);
        return e.state() == State::RUN;
      }
    };
    // (1) normal operation with a 25 mm/s follower and current sense: ignition, throttle steps 62.5-500 N, MECO, coast, relight
    {
      RigP g; g.isense = true;
      const bool run1 = g.toRun();
      const float prof[] = {500.f, 100.f, 450.f, 62.5f, 375.f, 150.f};
      for (float F : prof) { g.thrust = F; g.run(600); }
      g.tick(Cmd::SHUTDOWN); g.setPc(101325.f); g.until(State::COAST, 1000); g.run(500);
      g.tick(Cmd::RELIGHT); g.until(State::IGNITION, 2000); g.run(150); g.setPc(6.0e5f); g.until(State::RUN, 100);
      g.thrust = 250.f; g.run(800); g.tick(Cmd::SHUTDOWN); g.setPc(101325.f); g.until(State::COAST, 1000); g.run(1200);
      check(run1 && g.e.state() == State::COAST && g.n_events == 0 && !(g.o.fault_bits & fault::PINTLE) && g.e.abortCause() == Abort::NONE &&
            g.o.starts_used == 2,
            "v2.6 monitor: 25 mm/s follower through ignition, steps 62.5-500 N, MECO, coast and a relight: no jam event, no PINTLE fault",
            fmt("longest no-progress interval %.0f ms (time path 100 ms, current path needs 20 + 50 ms)", g.noprog_max * 1e3));
    }
    // (2) needle jammed closed (seat break-out), primed line: IGNITION opens toward the ignition lift -> time path 0.10 s
    {
      RigP g; g.mode = RigP::STUCK; g.in.pfeed_Pa = 49e5f;   // primed line: no bleed, so the jam meets the ignition lift
      g.tick(Cmd::ARM); g.run(600); g.tick(Cmd::IGNITE); g.until(State::IGNITION, 2000);
      int n_ep = -1, n = 0, ev_tick = -1, mv_at_trip = -1;
      while (g.e.state() == State::IGNITION && n < 600) {
        g.tick(); ++n;
        if (n_ep < 0 && g.o.pintle_noprog_s > 0) n_ep = n;
        if (g.o.pintle_jam_event) { ev_tick = n; mv_at_trip = g.o.mv_latch; }
      }
      const int ev_after = n_ep > 0 && ev_tick > 0 ? ev_tick - n_ep : -1;
      g.run(2);
      check(g.e.abortCause() == Abort::PINTLE_FAULT && g.o.pintle_fault_kind == jam::STALL_TIME && ev_after >= 99 && ev_after <= 101 &&
            1e-3 * ev_tick < cfg::kIgnWindowFirst_s && mv_at_trip == 0 && g.o.pintle_backoff && g.o.pintle_cmd_m < 1e-6f && g.n_events == 1 &&
            (g.o.fault_bits & fault::PINTLE),
            "v2.6 jam closed in IGNITION: no progress for 0.10 s -> PINTLE_FAULT abort (MV unlatched), back-off, one jam event, before the ignition window ends (v2.8: lift + 0.40 s)",
            fmt("episode at %.0f ms after IGNITION entry, event %.0f ms later", n_ep, ev_after) + fmt(", recorded cmd %.3f mm, lift %.3f mm", g.e.lastJam().cmd_m * 1e3, g.e.lastJam().meas_m * 1e3));
      check(g.e.lastJam().state == static_cast<uint8_t>(State::IGNITION) && std::fabs(g.e.lastJam().noprog_s - 0.100f) < 0.0015f && g.e.lastJam().i_A < 0.0f,
            "v2.6 jam event record: state IGNITION, 0.10 s without progress, no current sense (-1)", fmt("noprog %.4f s", g.e.lastJam().noprog_s));
    }
    // (3) same jam with the optional rail current sense: current path (> 1.0 A, no progress >= 20 ms, held 50 ms)
    {
      RigP g; g.mode = RigP::STUCK; g.isense = true; g.in.pfeed_Pa = 49e5f;
      g.tick(Cmd::ARM); g.run(600); g.tick(Cmd::IGNITE); g.until(State::IGNITION, 2000);
      int n_ep = -1, n = 0, ev_tick = -1;
      while (g.e.state() == State::IGNITION && n < 600) {
        g.tick(); ++n;
        if (n_ep < 0 && g.o.pintle_noprog_s > 0) n_ep = n;
        if (g.o.pintle_jam_event) ev_tick = n;
      }
      const int ev_after = n_ep > 0 && ev_tick > 0 ? ev_tick - n_ep : -1;
      check(g.e.abortCause() == Abort::PINTLE_FAULT && g.o.pintle_fault_kind == jam::STALL_CURRENT && ev_after >= 69 && ev_after <= 71 &&
            std::fabs(g.e.lastJam().i_A - 1.5f) < 1e-6f,
            "v2.6 jam closed with current sense: STALL_CURRENT 70 ms after the episode starts (20 ms no progress + 50 ms > 1.0 A)",
            fmt("event %.0f ms after the episode start, I %.2f A", ev_after, g.e.lastJam().i_A));
    }
    // (4) slow but moving (8 mm/s, a third of the HV69 speed): no trip; creeping (2.5 mm/s): tracking timeout 0.6 s
    {
      RigP g; g.v_mps = 0.008f; g.thrust = 100.f;
      const bool run1 = g.toRun(); g.run(800); g.thrust = 500.f; g.run(1000);
      check(run1 && g.e.state() == State::RUN && g.n_events == 0, "v2.6 slow needle (8 mm/s) on a 100 -> 500 N step: progress marks every 2.5 ms, no trip",
            fmt("longest no-progress %.0f ms", g.noprog_max * 1e3));
      RigP h; h.v_mps = 0.0015f; h.thrust = 100.f;
      const bool run2 = h.toRun(); h.run(800); h.thrust = 500.f;
      int n = 0; while (h.e.state() == State::RUN && n < 2000) { h.tick(); ++n; }
      check(run2 && h.e.abortCause() == Abort::PINTLE_FAULT && h.o.pintle_fault_kind == jam::TRACK_TIMEOUT && n > 600 && n < 700,
            "v2.6 creeping needle (1.5 mm/s, a mark every 13 ms): TRACK_TIMEOUT after 0.6 s of tracking error -> PINTLE_FAULT",
            fmt("abort %.0f ms after the step, longest no-progress %.0f ms", n, h.noprog_max * 1e3));
    }
    // (5) needle jammed open at MECO: SHUTDOWN -> no closing progress 0.10 s -> PINTLE_FAULT; in ABORT the bus is released at
    //     once (the episode is not restarted); one event only; log v5 flags b5/b6/b7
    RigP j5;
    {
      RigP& g = j5; g.thrust = 400.f;
      const bool run1 = g.toRun(); g.run(800);
      const float x_meco = g.x;
      g.mode = RigP::STUCK; g.tick(Cmd::SHUTDOWN);
      int n = 0, n_abort = -1, n_drop = -1;
      while (n < 400) {
        g.tick(); ++n;
        if (n_abort < 0 && g.e.state() == State::ABORT) n_abort = n;
        if (n_abort >= 0 && n_drop < 0 && !g.o.arm_bus_request) n_drop = n;
        if (n_drop >= 0) break;
      }
      check(run1 && g.e.abortCause() == Abort::PINTLE_FAULT && g.o.pintle_fault_kind == jam::STALL_TIME && n_abort >= 100 && n_abort < 115 &&
            n_drop - n_abort <= 1 && g.n_events == 1 && !g.o.mv_latch,
            "v2.6 jam open at MECO: SHUTDOWN, no closing progress 0.10 s -> PINTLE_FAULT, ARM bus released on the next tick, one event",
            fmt("needle %.2f mm, abort %.0f ms after SHUTDOWN, bus released %.0f ms later", x_meco * 1e3, n_abort, n_drop - n_abort));
      check((g.sat_or & 0x40u) && (g.r.sat_flags & 0x20u) && (g.r.sat_flags & 0x80u) && g.r.version == kLogVersion,
            "v2.6 log v5/v6: sat_flags b6 no progress >= 20 ms (before the trip), b5 back-off, b7 jam record pending", hex(g.r.sat_flags, 2));
    }
    // (6) MAINT_JAM: ARM refused until CLEAR_JAM (keyed, SAFE only); NV flag from the HAL at boot
    {
      RigP& g = j5;
      g.in.arm_bus_on = false; g.setPc(101325.f); g.until(State::SAFE, 2000); g.run(10);
      g.tick(Cmd::DISARM); g.tick(Cmd::ARM);
      const bool refused = g.e.state() == State::SAFE && g.e.abortCause() == Abort::MAINT_JAM && g.o.maint_jam_pending;
      g.tick(Cmd::DISARM); g.tick(Cmd::CLEAR_JAM, 0x1234); g.tick(Cmd::ARM);
      const bool bad_key = g.e.state() == State::SAFE && g.e.abortCause() == Abort::MAINT_JAM && g.e.clearJamRefused() == 1 && g.n_clear == 0;
      g.tick(Cmd::DISARM); g.tick(Cmd::CLEAR_JAM, cfg::kClearJamKey);
      const bool pulse = g.o.maint_clear_jam && !g.o.maint_jam_pending; g.tick();
      const bool one_tick = !g.o.maint_clear_jam && g.n_clear == 1;
      // v2.7: the jam aborted SHUTDOWN after a lit burn, so the relight lockout is also set: ARM still refused until CLEAR_LOCKOUT
      g.x = 0.0f; g.mode = RigP::FOLLOW; g.in.arm_bus_on = true; g.tick(Cmd::ARM);
      const bool lock = g.e.state() == State::SAFE && g.e.abortCause() == Abort::RELIGHT_LOCKOUT;
      g.tick(Cmd::DISARM); g.tick(Cmd::CLEAR_LOCKOUT, cfg::kClearLockoutKey); g.tick(Cmd::ARM);
      check(refused && bad_key && pulse && one_tick && lock && g.e.state() == State::ARMED,
            "v2.6 MAINT_JAM: ARM refused (cause 21) after a jam; CLEAR_JAM with a wrong key refused; keyed CLEAR_JAM in SAFE -> one-tick clear pulse; "
            "v2.7: the MECO abort also set the relight lockout (cause 23) -> CLEAR_LOCKOUT, ARM accepted",
            fmt("%.0f %.0f %.0f", refused, bad_key, pulse) + fmt(" %.0f", lock));
      g.tick(Cmd::CLEAR_JAM, cfg::kClearJamKey);
      check(g.e.state() == State::ARMED && g.e.clearJamRefused() == 2 && g.n_clear == 1, "v2.6 CLEAR_JAM outside SAFE is ignored (counted)");
      RigP b; b.in.maint_pintle_jam = true; b.tick(Cmd::ARM);
      const bool nv_ref = b.e.state() == State::SAFE && b.e.abortCause() == Abort::MAINT_JAM;
      b.tick(Cmd::DISARM); b.tick(Cmd::CLEAR_JAM, cfg::kClearJamKey); const bool nv_pulse = b.o.maint_clear_jam;
      b.in.maint_pintle_jam = false; b.tick(); b.tick(Cmd::ARM);   // the HAL cleared the record
      check(nv_ref && nv_pulse && b.e.state() == State::ARMED, "v2.6 non-volatile jam flag at boot: ARM refused (MAINT_JAM) until CLEAR_JAM and the HAL clears the record");
    }
    // (7) runaway in COAST (servo drives open with the command closed): RUNAWAY kind, abort, bus released
    {
      RigP g; g.thrust = 300.f;
      const bool run1 = g.toRun(); g.run(500); g.tick(Cmd::SHUTDOWN); g.setPc(101325.f); g.until(State::COAST, 1000); g.run(300);
      const bool coast = g.e.state() == State::COAST;
      g.mode = RigP::RUNAWAY;
      int n = 0; while (g.e.state() == State::COAST && n < 500) { g.tick(); ++n; }
      g.tick();
      check(run1 && coast && g.e.abortCause() == Abort::PINTLE_FAULT && g.o.pintle_fault_kind == jam::RUNAWAY && !g.o.arm_bus_request && g.n_events == 1,
            "v2.6 runaway in COAST (needle driven open at 20 mm/s): kind RUNAWAY, PINTLE_FAULT, ARM bus released",
            fmt("abort %.0f ms after the runaway start, lift %.2f mm", n, g.x * 1e3));
    }
    // (8) abort that ends before the monitor trips (Pc vented in 50 ms) with the needle stuck at 0.8 mm: the unpowered-closing check
    //     in SAFE records NOT_CLOSED 1 s after power removal
    {
      RigP g; g.thrust = 150.f;
      const bool run1 = g.toRun(); g.run(600);
      g.mode = RigP::STUCK; g.x = std::fmax(g.x, 0.8e-3f);
      g.tick(Cmd::ABORT); g.setPc(101325.f);
      const int n_safe = g.until(State::SAFE, 600);
      const bool none_yet = g.n_events == 0;
      g.in.arm_bus_on = false; g.run(990); const bool before = g.n_events == 0; g.run(20);
      check(run1 && none_yet && before && g.n_events == 1 && g.o.pintle_fault_kind == jam::NOT_CLOSED && g.o.maint_jam_pending,
            "v2.6 abort over before the 0.1 s trip, needle stuck at 0.8 mm: SAFE check records NOT_CLOSED 1.0 s after power removal",
            fmt("SAFE %.0f ms after the abort", n_safe));
    }
    // (9) LEAD rule (a): a positive learned trim never takes the unlit pintle past the ignition lift (v2.5 scaled it up)
    {
      RigP g; g.thrust = 300.f; g.pc_frac = 0.85f;   // chamber 15 % below the map: the trim winds up
      const bool run1 = g.toRun(); g.run(1500);
      const float trim = g.e.pcc().trim();
      g.tick(Cmd::SHUTDOWN); g.setPc(101325.f); g.until(State::COAST, 1000); g.run(300);
      g.tick(Cmd::RELIGHT); g.until(State::IGNITION, 2000);
      float xmax = 0; int n = 0; while (g.e.state() == State::IGNITION && n < 330) { g.tick(); xmax = std::fmax(xmax, g.o.pintle_cmd_m); ++n; }
      check(run1 && trim > 0.1f && xmax <= cfg::kPintleUnlitLiftMax_m + 1e-9f && xmax > 0.99f * g.e.ignLift(),
            "v2.6 rule (a): learned trim +" + fmt("%.2f", trim) + " -> relight IGNITION lift capped at the ignition lift (v2.8: table, " +
                fmt("%.4f mm", cfg::kPintleUnlitLiftMax_m * 1e3) + "; v2.5 would command (1+trim) x)",
            fmt("max %.4f mm vs v2.5 %.4f mm", xmax * 1e3, (1.0f + trim) * g.e.ignLift() * 1e3));
      g.until(State::ABORT, 1000); g.run(5);
      check(g.e.abortCause() == Abort::NO_IGNITION && g.o.pintle_cmd_m < 1e-6f && g.e.ignRule() == rule::FLIGHT_RELIGHT,
            "v2.6 rule (a): no light (Pc stays at ambient) -> NO_IGNITION abort (v2.8 flight relight: lift + 0.65 s) and the pintle closes",
            fmt("cmd %.3f mm", g.o.pintle_cmd_m * 1e3));
    }
    // (10) LEAD rule (b): MV unlatched at MECO and closed through the coast; every opening ramps >= 0.3 s. v2.8 (LEAD Finding A):
    //      a primed segment relights DIRECTLY (NC valve latch + opener ramp at E0 with the torch, lift at E1); a segment holding gas
    //      (P_feed < 0.5 P_tank) still runs PREPRESS (bleed lift, ramp, hold) first
    {
      RigP g; g.thrust = 300.f;
      const bool run1 = g.toRun(); g.run(800);
      g.tick(Cmd::SHUTDOWN); const bool held_at_shut = g.o.mv_latch && g.o.mv_seat_wait;   // v2.7: pintle first, valve on the seat
      g.setPc(101325.f);
      bool unl_shut = false; for (int i = 0; i < 1000 && g.e.state() == State::SHUTDOWN; ++i) { g.tick(); unl_shut |= !g.o.mv_latch && g.e.state() == State::SHUTDOWN; }
      g.until(State::COAST, 1000);
      bool latch_coast = false; for (int i = 0; i < 2000; ++i) { g.tick(); latch_coast |= g.o.mv_latch; }
      g.in.pfeed_Pa = 47e5f;   // trapped segment still primed (seat tight)
      g.tick(Cmd::RELIGHT);
      const bool direct = g.e.state() == State::IGNITION && g.o.relight_direct && g.o.mv_latch;
      double t_open = -1, t_cock = -1, t_sw = -1, t_lift = -1; const double t0 = g.t; int n = 0;
      // the opener keeps ramping after a fast light (RUN from ~0.16 s): observe IGNITION and RUN for 0.70 s from E0
      while ((g.e.state() == State::IGNITION || g.e.state() == State::RUN) && n < 700) {
        g.tick(); ++n;
        if (t_open < 0 && g.o.servo_us[3] > cfg::kMvOpenerRest_us + 4.5f) t_open = g.t - t0;
        if (t_cock < 0 && g.o.servo_us[3] >= cfg::kMvOpenerCock_us - 0.5f) t_cock = g.t - t0;
        if (t_sw < 0 && g.in.mv_open_sw) t_sw = g.t - t0;
        if (t_lift < 0 && g.o.pintle_cmd_m > 0.0f) t_lift = g.t - t0;
        if (n == 150) g.setPc(6.0e5f);
      }
      check(run1 && held_at_shut && unl_shut && !latch_coast && direct && t_cock - t_open >= 0.30 && t_sw > 0 && t_sw < cfg::kMvOpenBy_s &&
                t_lift > 0 && t_lift < 0.02 && g.e.state() == State::RUN && g.e.abortCause() == Abort::NONE,
            "v2.6 rule (b) / v2.8 Finding A: MV unlatched in SHUTDOWN once seated, closed through a 2 s coast; primed RELIGHT -> IGNITION at E0 "
            "with the opener ramp >= 0.3 s running, OPEN switch before kMvOpenBy_s, lift at the torch confirmation, RUN",
            fmt("ramp %.0f ms, OPEN switch %.0f ms, lift %.0f ms after E0", (t_cock - t_open) * 1e3, t_sw * 1e3, t_lift * 1e3));
      // gas in the segment: PREPRESS (bleed + ramp + hold) before IGNITION
      RigP h; h.thrust = 300.f; h.toRun(); h.run(500); h.tick(Cmd::SHUTDOWN); h.setPc(101325.f); h.until(State::COAST, 2000); h.run(600);
      h.in.pfeed_Pa = 10e5f;   // segment vented / gas pocket (< 0.5 P_tank absolute)
      h.run(30);               // the ECU judges the filtered P_feed (50 Hz): one sample of 10 bar is not yet 'unprimed'
      h.tick(Cmd::RELIGHT);
      const bool prep = h.e.state() == State::PREPRESS;
      double ho = -1, hc = -1; const double h0 = h.t; int k = 0;
      while (h.e.state() == State::PREPRESS && k < 3000) {
        h.tick(); ++k;
        if (ho < 0 && h.o.servo_us[3] > cfg::kMvOpenerRest_us + 4.5f) ho = h.t - h0;
        if (hc < 0 && h.o.servo_us[3] >= cfg::kMvOpenerCock_us - 0.5f) hc = h.t - h0;
      }
      const double t_ign = h.t - h0;
      check(prep && hc - ho >= 0.30 && ho >= cfg::kBleedSettle_s - 0.002 && h.e.state() == State::IGNITION && !h.o.relight_direct &&
                std::fabs(t_ign - (cfg::kBleedSettle_s + cfg::kMvOpenRampSlow_s + cfg::kMvCockHold_s)) < 0.004,
            "v2.8 RELIGHT with gas in the segment (P_feed 10 bar g < 0.5 P_tank): PREPRESS bleed 60 ms, opener ramp >= 0.3 s, hold, then IGNITION",
            fmt("ramp %.0f ms from %.0f ms, IGNITION at %.0f ms", (hc - ho) * 1e3, ho * 1e3, t_ign * 1e3));
    }
    // (11) pintle encoder at ARM; encoder loss in RUN = flag only
    {
      RigP g; g.in.pintle_meas_valid = false; g.tick(Cmd::ARM);
      const bool r1 = g.e.state() == State::SAFE && g.e.abortCause() == Abort::PINTLE_FAULT;
      g.in.pintle_meas_valid = true; g.x = 0.3e-3f; g.mode = RigP::STUCK; g.tick(Cmd::DISARM); g.tick(Cmd::ARM);
      const bool r2 = g.e.state() == State::SAFE && g.e.abortCause() == Abort::PINTLE_FAULT;
      check(r1 && r2, "v2.6 ARM refused (PINTLE_FAULT) without a valid pintle encoder, and with the needle not seated (0.3 mm)");
      RigP h; const bool run1 = h.toRun(); h.run(300); h.in.pintle_meas_valid = false;
      for (int i = 0; i < 500; ++i) { h.tick(); h.in.pintle_meas_valid = false; }
      check(run1 && h.e.state() == State::RUN && (h.o.fault_bits & fault::ENCODER) && h.n_events == 0,
            "v2.6 pintle encoder lost in RUN: fault ENCODER flagged, burn continues (monitor blind; Pc loop and PC_BAND still active)");
    }
    // (12) non-volatile jam record (HAL storage format)
    {
      uint8_t ff[32]; std::memset(ff, 0xFF, sizeof ff);
      NvJamRecord b; const NvJamStatus sb = nvJamDecode(ff, &b);
      PintleJamEvent ev; ev.kind = jam::STALL_CURRENT; ev.state = static_cast<uint8_t>(State::RUN); ev.cmd_m = 2.345e-3f; ev.meas_m = 1.234e-3f;
      ev.i_A = 1.52f; ev.noprog_s = 0.0703f; ev.count = 1;
      const NvJamRecord r1 = nvJamRecordEvent(nvJamBlank(), ev, 123456u);
      NvJamRecord d; const NvJamStatus s1 = nvJamDecode(reinterpret_cast<const uint8_t*>(&r1), &d);
      const bool fields = d.kind == jam::STALL_CURRENT && d.cmd_um == 2345 && d.meas_um == 1234 && d.i_mA == 1520 && d.noprog_ms == 70 &&
                          d.count == 1 && d.total == 1 && d.t_ms == 123456u && (d.flags & 1u);
      NvJamRecord bad = r1; reinterpret_cast<uint8_t*>(&bad)[9] ^= 0x01;
      NvJamRecord d2; const NvJamStatus s2 = nvJamDecode(reinterpret_cast<const uint8_t*>(&bad), &d2);
      const NvJamRecord c1 = nvJamClear(r1); NvJamRecord d3; const NvJamStatus s3 = nvJamDecode(reinterpret_cast<const uint8_t*>(&c1), &d3);
      check(sb == NvJamStatus::BLANK && !nvJamPending(sb, b) && s1 == NvJamStatus::VALID && nvJamPending(s1, d) && fields &&
            s2 == NvJamStatus::CORRUPT && nvJamPending(s2, d2) && s3 == NvJamStatus::VALID && !nvJamPending(s3, d3) && d3.clears == 1 && d3.total == 1,
            "v2.6 NvJamRecord (32 B, CRC-16): blank = not pending, event round trip, one flipped bit = CORRUPT = pending (fail-safe), clear keeps the total",
            "EVENT arg " + hex(evt::jamArg(ev), 4));
    }
    // (13) HV69 pulse calibration as a run-time parameter (B-PNT-1 sweep)
    {
      RigP g; g.tick();
      const float us_closed0 = g.o.servo_us[2];
      linkage::PintleCal c; c.center_us = 1500.0f;
      const bool ok = g.e.setPintleCal(c); g.tick();
      const float us_closed1 = g.o.servo_us[2];
      linkage::PintleCal bad1; bad1.us_per_deg = 30.0f;
      linkage::PintleCal bad2; bad2.max_us = 1900.0f;   // would cut the stroke (4 mm needs ~2014 us)
      const bool r1 = !g.e.setPintleCal(bad1), r2 = !g.e.setPintleCal(bad2);
      g.tick(Cmd::ARM); g.run(2);
      linkage::PintleCal c2; const bool r3 = !g.e.setPintleCal(c2);
      check(ok && std::fabs(us_closed1 - us_closed0 + 20.0f) < 0.01f && r1 && r2 && r3 && std::fabs(g.e.pintleCal().center_us - 1500.0f) < 1e-6f,
            "v2.6 PintleCal: accepted in SAFE (centre 1520 -> 1500 us shifts the closed pulse by -20 us); bad scale, stroke-cutting clamp and non-SAFE refused",
            fmt("closed %.1f -> %.1f us", us_closed0, us_closed1) + fmt(", 4 mm at the default %.1f us", linkage::liftToUs(eng::kPintleStroke_m, linkage::PintleCal())));
    }
    check(true, "v2.6 stall thresholds vs calc/pintle_dynamics_v2.py (informational)",
          fmt("time path %.0f ms = %.1f x the 24 ms normal maximum; tracking %.2f s", cfg::kPintleStallTime_s * 1e3, cfg::kPintleStallTime_s / cfg::kPintleNoProgNormal_s, cfg::kPintleTrackTime_s) +
          fmt(" = %.2f x the slowest full stroke", cfg::kPintleTrackTime_s / cfg::kPintleFullStrokeSlow_s));
  }

  {   // Pc filter (v2.2): 2nd-order Butterworth 50 Hz at 1 kHz
    LowPass2 f; f.setup(cfg::kPcFilterFc_Hz, cfg::kDt_s);
    auto gain = [&](double fhz, double* ph) {
      LowPass2 g = f; g.reset(0.0f); double sc = 0, ss = 0; int n = 0;
      for (int k = 0; k < 20000; ++k) {
        const double tt = k * 1e-3; const float y = g.step(static_cast<float>(std::sin(2 * M_PI * fhz * tt)));
        if (k >= 10000) { sc += y * std::cos(2 * M_PI * fhz * tt); ss += y * std::sin(2 * M_PI * fhz * tt); ++n; }
      }
      *ph = std::atan2(sc, ss) * 180 / M_PI; return 2 * std::sqrt(sc * sc + ss * ss) / n;
    };
    double p20, p50, p144, p188, p6;
    const double g20 = gain(20, &p20), g50 = gain(50, &p50), g144 = gain(144, &p144), g188 = gain(188, &p188);
    gain(6, &p6);
    check(std::fabs(g50 - 0.7071) < 0.01 && g144 < 0.13 && g188 < 0.08, "Pc low-pass: -3 dB at 50 Hz, <= 0.13 at the 144-188 Hz sense-line band",
          fmt("g50 %.3f, g144 %.3f, g188 %.3f", g50, g144, g188));
    check(true, "Pc low-pass phase (informational: COMB asked < 1 deg at 20 Hz, not achievable with a 50 Hz low-pass)",
          fmt("phase 6 Hz %.1f deg, 20 Hz %.1f deg, gain 20 Hz %.3f", p6, p20, g20));
  }

  std::printf("\n%d passed, %d failed\n", n_pass, n_fail);
  std::ofstream f(out + "/test_core.json");
  f << "{\n \"id\": \"test_core\", \"version\": \"v2.11\", \"passed\": " << n_pass << ", \"failed\": " << n_fail << ",\n \"lines\": [\n";
  for (size_t i = 0; i < lines.size(); ++i) {
    std::string l = lines[i]; for (auto& ch : l) if (ch == '"') ch = '\'';
    f << "  \"" << l << "\"" << (i + 1 < lines.size() ? "," : "") << "\n";
  }
  f << " ]\n}\n";
  return n_fail ? 1 : 0;
}
