// REV-ELEC-3 reviewer probe (2026-10-21): threshold discrimination on the v2.11 core (logic rig, TEST VALUES, not measurements).
// The author's test_core v211b-1 uses +/-0.5 K (stand T0) and +1.0 K (start limit) offsets and the v210-10 case-TC test uses 600 K:
// none of them can tell a 0.1 K threshold error, a >= / > slip or a persistence off by a few ticks. This probe steps each limit by
// +/-0.05 K and the case-TC persistence by +/-10 ms around 0.200 s.
// Build (from the firmware root, like test_core): g++ -std=c++17 -O2 -Isrc/core -Isil -DECU_SIL_TEST_HOOKS <this file> src/core/control.cpp
//   src/core/engine_ecu.cpp src/core/protocol.cpp src/core/sensor_scale.cpp -o probe_thresholds
// Rig: a copy of test_v29.inc Rig9 (ideal follower plant), reduced to what these checks need.
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>
#include "control.h"
#include "engine_ecu.h"
#include "protocol.h"
#include "sensor_scale.h"
#include "mv_ladder_table.h"

using namespace ecu;
static int n_pass = 0, n_fail = 0;
static void check(bool ok, const std::string& name, const std::string& detail) {
  (ok ? n_pass : n_fail)++;
  std::printf("%s %s  [%s]\n", ok ? "PASS" : "FAIL", name.c_str(), detail.c_str());
}
static GimbalNotchCal testNotchCal() {   // as test_core.cpp (TEST VALUES)
  GimbalNotchCal c;
  c.ax[0].enabled = true; c.ax[0].f0_Hz = 22.0f; c.ax[0].q = 1.0f; c.ax[0].depth_dB = -12.0f;
  c.ax[1].enabled = true; c.ax[1].f0_Hz = 25.3f; c.ax[1].q = 1.4f; c.ax[1].depth_dB = -15.0f;
  return c;
}
struct Rig {
  EngineEcu e; Inputs in; Commands c; Outputs o; LogRecord lr; double t = 0; float thrust = 300.f;
  bool follow = false;
  explicit Rig(bool stand = false) {
    e.init(0.0); e.ptank_cal_ok = true; e.setGimbalNotchCal(testNotchCal()); e.hbleed_fitted = false;
    in.arm_plug_present = true; in.arm_bus_on = true; in.vbat_V = 8.2f; in.mv_closed_sw = true; in.ptank_Pa = 50e5f; in.pfeed_Pa = 48e5f;
    in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f; setPcG(0.0f);
    if (stand) { in.load_cell_N = 0.0f; in.mode_strap = strap::STAND; }
  }
  void setPcG(float pg) { in.pc_Pa = pg; in.pc_raw_V = 0.5f + 4.f * in.pc_Pa / cfg::kPcXdcrFs_Pa; }
  void setPcAbs(float pa) { setPcG(pa - 101325.f); }
  void tick(Cmd cm = Cmd::NOP, uint16_t arg = 0) {
    t += 1e-3; in.t_s = t; c = Commands(); c.fast_valid = true; c.thrust_sp_N = thrust;
    if (cm != Cmd::NOP) { c.state_valid = true; c.cmd = cm; c.arg = arg; }
    if (follow && o.state == State::RUN && o.pc_sp_active_Pa > 0) setPcAbs(o.pc_sp_active_Pa);
    in.pintle_meas_m = o.pintle_cmd_m;
    if (o.servo_us[3] > 1800.f) { in.mv_open_sw = true; in.mv_closed_sw = false; }
    if (!o.mv_latch && o.servo_us[3] < 1600.f) { in.mv_open_sw = false; in.mv_closed_sw = true; }
    const bool both = o.sol[0] && o.sol[1];
    in.ptorch_valid = true; in.ptorch_Pa = both ? 2.0e5f : std::fmax(0.0f, in.pc_Pa);
    in.photo_valid = true; in.photo_V = (both || o.state == State::RUN) ? 1.0f : 0.10f;
    in.pmid_valid = true; in.pmid_hi = false;
    in.mv_ladder_ratio = ladder::nominalRatio(in.mv_open_sw, in.mv_closed_sw, in.pmid_hi);
    e.step(in, c, o); e.fillLog(in, o, lr);
  }
  void run(int n) { for (int i = 0; i < n; ++i) tick(); }
  int until(State s, int nmax) { int n = 0; while (e.state() != s && n < nmax) { tick(); ++n; } return n; }
  int toIgnition() { tick(Cmd::ARM); run(600); tick(Cmd::IGNITE); return until(State::IGNITION, 4000); }
  int toE1(int nmax = 400) { int n = 0; while (e.liftCommandTime() < 0.0 && e.state() == State::IGNITION && n < nmax) { tick(); ++n; } return n; }
  bool lightRun(float pc_abs = 3.0e5f) { toE1(); run(30); setPcAbs(pc_abs); until(State::RUN, 60); return e.state() == State::RUN; }
};
static std::string sf(const char* f, double a, double b = 0, double c = 0, double d = 0) {
  char s[300]; std::snprintf(s, sizeof s, f, a, b, c, d); return s;
}

int main() {
  using namespace cfg;
  std::printf("REV-ELEC-3 probe_thresholds: kCaseStandArmMax_K %.2f, kCaseRelightMax_K %.2f, kCaseOverTemp_K %.2f, kOverTempTime_s %.3f\n",
              kCaseStandArmMax_K, kCaseRelightMax_K, kCaseOverTemp_K, kOverTempTime_s);
  // P1 stand T0 ARM rule, both TCs, +/-0.05 K and exactly at the limit (rule: refuse when the reading is ABOVE 297.15 K)
  {
    auto arm = [](bool stand, int idx, float T) { Rig r(stand); r.in.tc_K[idx] = T; r.tick(Cmd::ARM); return std::make_pair(r.e.state(), r.e.abortCause()); };
    bool ok = true; std::string d;
    for (int idx = 0; idx < 2; ++idx) {
      const auto lo = arm(true, idx, kCaseStandArmMax_K - 0.05f), at = arm(true, idx, kCaseStandArmMax_K), hi = arm(true, idx, kCaseStandArmMax_K + 0.05f);
      const auto fl = arm(false, idx, kCaseStandArmMax_K + 0.05f);
      ok = ok && lo.first == State::ARMED && at.first == State::ARMED && hi.first == State::SAFE && hi.second == Abort::CASE_WARM_STAND &&
           fl.first == State::ARMED;
      d += std::string("TC") + std::to_string(idx + 1) + " -0.05 " + stateName(lo.first) + " / at " + stateName(at.first) + " / +0.05 " +
           abortName(hi.second) + " / flight +0.05 " + stateName(fl.first) + "; ";
    }
    check(ok, "P1 stand T0 ARM rule discriminates +/-0.05 K at 297.15 K on TC1 and TC2 (strict >), flight not affected", d);
  }
  // P2 start / ARM limit 403.15 K (both modes), +/-0.05 K
  {
    auto arm = [](bool stand, int idx, float T) { Rig r(stand); r.in.tc_K[idx] = T; r.tick(Cmd::ARM); return std::make_pair(r.e.state(), r.e.abortCause()); };
    bool ok = true; std::string d;
    for (int idx = 0; idx < 2; ++idx) {
      const auto lo = arm(false, idx, kCaseRelightMax_K - 0.05f), hi = arm(false, idx, kCaseRelightMax_K + 0.05f);
      const auto sh = arm(true, idx, kCaseRelightMax_K + 0.05f);
      ok = ok && lo.first == State::ARMED && hi.first == State::SAFE && hi.second == Abort::OVER_TEMP && sh.second == Abort::OVER_TEMP;
      d += std::string("TC") + std::to_string(idx + 1) + " flight -0.05 " + stateName(lo.first) + " / +0.05 " + abortName(hi.second) +
           " / stand +0.05 " + abortName(sh.second) + "; ";
    }
    check(ok, "P2 ARM start limit discriminates +/-0.05 K at 403.15 K (TC1, TC2; stand gets OVER_TEMP before CASE_WARM_STAND)", d);
  }
  // P3 COAST RELIGHT refusal CASE_HOT at 403.15 K +/-0.05 K (flight, bleed not fitted)
  {
    auto relight = [](float T, int idx) {
      Rig r; r.toIgnition(); r.lightRun(3.0e5f); r.follow = true; r.run(800); r.follow = false; r.tick(Cmd::SHUTDOWN); r.setPcG(0.0f);
      r.until(State::COAST, 3000); r.run(1400);
      r.in.tc_K[idx] = T; r.tick(Cmd::RELIGHT); r.tick();
      return std::make_pair(r.e.state(), static_cast<int>(r.o.cmd_refused));
    };
    const auto lo = relight(kCaseRelightMax_K - 0.05f, 0), hi = relight(kCaseRelightMax_K + 0.05f, 0), hi2 = relight(kCaseRelightMax_K + 0.05f, 1);
    const bool ok = lo.second != refuse::CASE_HOT && lo.first != State::COAST && hi.first == State::COAST && hi.second == refuse::CASE_HOT &&
                    hi2.second == refuse::CASE_HOT;
    check(ok, "P3 COAST RELIGHT refused CASE_HOT at 403.15 K + 0.05 K (TC1 and TC2), accepted at - 0.05 K",
          std::string("-0.05 K: state ") + stateName(lo.first) + sf(", refuse %.0f; +0.05 K: state ", lo.second) + stateName(hi.first) +
              sf(", refuse %.0f (TC2 %.0f)", hi.second, hi2.second));
  }
  // P4 in-burn case-TC abort 423.15 K, 0.200 s persistence: level +/-0.05 K, duration 190 / 210 ms, time to abort, flight and stand
  {
    auto burn = [](bool stand, int idx, float T, int ms_hot, int& ab_ms) {
      Rig r(stand); r.toIgnition(); r.lightRun(3.0e5f); r.follow = true; r.run(300);
      const bool run_ok = r.e.state() == State::RUN;
      r.in.tc_K[idx] = T; ab_ms = -1;
      for (int k = 0; k < 1500 && r.e.state() == State::RUN; ++k) {
        if (k == ms_hot) r.in.tc_K[idx] = 400.0f;
        r.tick();
        if (r.e.state() != State::RUN && ab_ms < 0) ab_ms = k + 1;
      }
      return std::make_pair(run_ok, r.e.abortCause());
    };
    int a1, a2, a3, a4, a5, a6;
    const auto lvl_lo = burn(false, 0, kCaseOverTemp_K - 0.05f, 100000, a1);
    const auto lvl_hi = burn(false, 0, kCaseOverTemp_K + 0.05f, 100000, a2);
    const auto d190 = burn(false, 0, kCaseOverTemp_K + 0.05f, 190, a3);
    const auto d210 = burn(false, 1, kCaseOverTemp_K + 0.05f, 210, a4);
    const auto st_hi = burn(true, 1, kCaseOverTemp_K + 0.05f, 100000, a5);
    const auto st_lo = burn(true, 1, kCaseOverTemp_K - 0.05f, 100000, a6);
    const bool ok = lvl_lo.first && lvl_lo.second == Abort::NONE && a1 < 0 && lvl_hi.second == Abort::OVER_TEMP && a2 >= 199 && a2 <= 202 &&
                    d190.second == Abort::NONE && a3 < 0 && d210.second == Abort::OVER_TEMP && a4 >= 199 && a4 <= 202 &&
                    st_hi.second == Abort::OVER_TEMP && a5 >= 199 && a5 <= 202 && st_lo.second == Abort::NONE;
    check(ok, "P4 in-burn case-TC abort: 423.15 K - 0.05 K never aborts (1.5 s), + 0.05 K aborts OVER_TEMP after 0.200 s; 190 ms hot -> no "
              "abort, 210 ms hot -> abort; stand the same",
          std::string("-0.05 K ") + abortName(lvl_lo.second) + sf(" (%.0f ms); +0.05 K ", a1) + abortName(lvl_hi.second) + sf(" at %.0f ms; 190 ms ", a2) +
              abortName(d190.second) + sf(" (%.0f); 210 ms TC2 ", a3) + abortName(d210.second) + sf(" at %.0f ms; stand +0.05 ", a4) +
              abortName(st_hi.second) + sf(" at %.0f ms, stand -0.05 ", a5) + abortName(st_lo.second));
  }
  // P5 armed window: after the SHUTDOWN command the case-TC monitor cannot abort (MV closed); a 430 K reading in COAST for 1 s
  {
    Rig r; r.toIgnition(); r.lightRun(3.0e5f); r.follow = true; r.run(500); r.follow = false; r.tick(Cmd::SHUTDOWN); r.setPcG(0.0f);
    r.until(State::COAST, 3000);
    const bool coast = r.e.state() == State::COAST;
    r.in.tc_K[0] = 430.0f; r.run(1000);
    check(coast && r.e.state() == State::COAST && r.e.abortCause() == Abort::NONE,
          "P5 post-burn soak: 430 K on TC1 for 1 s in COAST does not abort (MV closed: case monitor not armed)",
          std::string("state ") + stateName(r.e.state()) + ", abort " + abortName(r.e.abortCause()));
  }
  std::printf("SUMMARY probe_thresholds: %d passed, %d failed\n", n_pass, n_fail);
  return n_fail == 0 ? 0 : 1;
}
