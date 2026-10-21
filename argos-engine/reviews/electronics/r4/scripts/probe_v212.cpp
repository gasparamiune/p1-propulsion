// REV-ELEC-4 reviewer probe (2026-10-21) on the v2.12 core: logic rig, TEST VALUES, not measurements or plant results.
// Q1  re-ARM in the same power cycle after a hot session: the ARM sanity check with the seat compensation still active from the
//     previous arming (seat_ref_ok_ is reset only on entering ARMED) against a fresh ECU with the same inputs.
// Q2  seat-TC reading step (a TC wire short at a cold point) in the light window after E1, chamber unlit and vented: false E2?
// Q3  threshold discrimination the author's tests cannot show: PC_SENSOR HIGH TB-state at 4.75 V, J-FWD indication at 47.5 bar abs,
//     torch re-zero limit 0.60 bar, BASE check 0.76 bar (default build).
// Build (absolute paths): g++ -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -I$FW/src/core -I$FW/sil -DECU_SIL_TEST_HOOKS
//   probe_v212.cpp $FW/src/core/control.cpp $FW/src/core/engine_ecu.cpp $FW/src/core/protocol.cpp $FW/src/core/sensor_scale.cpp
// Rig: a copy of test_v29.inc Rig9 (ideal follower plant) reduced to what these checks need, plus the seat TC input.
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
  std::printf("%s %s\n     [%s]\n", ok ? "PASS" : "FAIL", name.c_str(), detail.c_str());
}
static std::string sf(const char* f, double a, double b = 0, double c = 0, double d = 0, double e = 0, double g = 0) {
  char buf[512]; std::snprintf(buf, sizeof buf, f, a, b, c, d, e, g); return buf;
}
static GimbalNotchCal testNotchCal() {
  GimbalNotchCal c;
  c.ax[0].enabled = true; c.ax[0].f0_Hz = 22.0f; c.ax[0].q = 1.0f; c.ax[0].depth_dB = -12.0f;
  c.ax[1].enabled = true; c.ax[1].f0_Hz = 25.3f; c.ax[1].q = 1.4f; c.ax[1].depth_dB = -15.0f;
  return c;
}
struct Rig {
  EngineEcu e; Inputs in; Commands c; Outputs o; LogRecord lr; double t = 0; float thrust = 300.f;
  bool follow = false; bool plant_lit = true;   // plant_lit false: the torch fires but the main chamber never lights
  int torch_delay = 0, torch_n = 0;
  explicit Rig(bool stand = false) {
    e.init(0.0); e.ptank_cal_ok = true; e.setGimbalNotchCal(testNotchCal()); e.hbleed_fitted = false;
    in.arm_plug_present = true; in.arm_bus_on = true; in.vbat_V = 8.2f; in.mv_closed_sw = true; in.ptank_Pa = 50e5f; in.pfeed_Pa = 48e5f;
    in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f; setPcG(0.0f);
    in.tc_bore_valid = true; in.tc_bore_K = 293.15f;
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
    torch_n = both ? torch_n + 1 : 0;
    const bool torch_flame = both && torch_n > torch_delay;
    in.ptorch_valid = true; in.ptorch_Pa = torch_flame ? 2.0e5f : std::fmax(0.0f, in.pc_Pa);
    in.photo_valid = true; in.photo_V = (torch_flame || (o.state == State::RUN && plant_lit)) ? 1.0f : 0.10f;
    in.pmid_valid = true; in.pmid_hi = false;
    in.mv_ladder_ratio = ladder::nominalRatio(in.mv_open_sw, in.mv_closed_sw, in.pmid_hi);
    e.step(in, c, o); e.fillLog(in, o, lr);
  }
  void run(int n) { for (int i = 0; i < n; ++i) tick(); }
  int until(State s, int nmax) { int n = 0; while (e.state() != s && n < nmax) { tick(); ++n; } return n; }
  int toIgnition() { tick(Cmd::ARM); run(600); tick(Cmd::IGNITE); return until(State::IGNITION, 4000); }
  int toE1(int nmax = 400) { int n = 0; while (e.liftCommandTime() < 0.0 && e.state() == State::IGNITION && n < nmax) { tick(); ++n; } return n; }
  bool lightRun(float pc_abs = 3.0e5f) { toE1(); run(30); setPcAbs(pc_abs); until(State::RUN, 60); return e.state() == State::RUN; }
  bool burnToCoast(int run_ms = 800) {
    follow = true; run(run_ms); follow = false; tick(Cmd::SHUTDOWN); setPcG(0.0f);
    until(State::COAST, 3000); return e.state() == State::COAST;
  }
  // vented chamber, pure thermal zero shift of the TRUE coefficient: raw = coef_true x (T_seat - T_cal); TC reads T_seat
  void seat(float coef_true, float T_seat, float T_cal = 293.15f, float p_extra_g = 0.0f) {
    in.tc_bore_K = T_seat; setPcG(coef_true * (T_seat - T_cal) + p_extra_g);
  }
};

int main() {
  const float c1 = 0.0248e5f;   // Pa/K, the C1 typical
  // ===================================================================== Q1 re-ARM after a hot session (same power cycle)
  {
    std::string d;
    bool all = true;
    for (float k : {1.0f, 3.0f})
      for (float dT : {5.0f, 20.0f})
        for (float pex : {0.0f, 1.3e5f}) {
          const float coef = k * c1;
          // fresh ECU, seat at T_cal + dT, TC valid, coefficient loaded
          Rig f; f.e.setPcSeatCoef(coef); f.seat(coef, 293.15f + dT, 293.15f, pex); f.run(300); f.tick(Cmd::ARM); f.run(5);
          const bool fresh_armed = f.e.state() == State::ARMED;
          // same ECU after a session: ARM at T_cal, burn, coast, SAFE; the seat is then at T_cal + dT; ARM again
          Rig r; r.e.setPcSeatCoef(coef); r.seat(coef, 293.15f); r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast();
          r.seat(coef, 293.15f); r.run(200); r.tick(Cmd::SAFE); r.run(5); r.tick(Cmd::DISARM); r.run(5);
          const bool in_safe = r.e.state() == State::SAFE;
          r.seat(coef, 293.15f + dT, 293.15f, pex); r.run(300);
          const float comp_safe = r.o.pc_seat_comp_Pa;
          r.tick(Cmd::ARM); r.run(5);
          const bool re_armed = r.e.state() == State::ARMED;
          d += sf("k %.0f dT %.0f K non-vented %.1f bar: fresh ARMED %.0f, re-ARM ARMED %.0f (comp in SAFE %.3f bar); ", k, dT, pex / 1e5,
                  fresh_armed ? 1.0 : 0.0, re_armed ? 1.0 : 0.0, comp_safe / 1e5);
          if (!in_safe || fresh_armed != re_armed) all = false;   // the re-ARM decision must equal the fresh one
        }
    check(all, "Q1 re-ARM in the same power cycle decides as a fresh ECU (expected: equal decisions)", d);
  }
  // ===================================================================== Q2 seat-TC step in the light window (unlit, vented)
  {
    std::string d; int n_false = 0, n_case = 0, n_ctrl_lit = 0;
    for (bool stand : {false, true})
      for (float k : {1.0f, 3.0f})
        for (float dT : {15.0f, 55.0f})
          for (bool step : {false, true}) {
            const float coef = k * c1;
            Rig r(stand); r.e.setPcSeatCoef(coef); r.seat(coef, 293.15f); r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast();
            // coast: the seat warms to T_cal + dT (TC and raw drift together, vented chamber); re-zero blocks see ~0 compensated
            for (int i = 0; i < 4000; ++i) { r.seat(coef, 293.15f + dT * std::fmin(1.0f, i / 3000.0f)); r.tick(); }
            r.plant_lit = false;
            r.tick(Cmd::RELIGHT); r.until(State::IGNITION, 4000);
            const bool ign = r.e.state() == State::IGNITION;
            r.toE1(); r.run(5);
            if (step) r.in.tc_bore_K = 293.15f;   // TC wire short at a cold point: reads ~T0; raw unchanged (unlit, vented)
            int n = 0; bool lit = false;
            while (n < 600 && (r.e.state() == State::IGNITION)) { r.tick(); ++n; }
            lit = r.e.state() == State::RUN;
            const int n_e2 = n;
            std::string after;
            if (lit) { r.run(500); after = std::string(", +500 ms ") + stateName(r.e.state()) + " / " + abortName(r.e.abortCause()); }
            ++n_case;
            if (step && lit) ++n_false;
            if (!step && lit) ++n_ctrl_lit;
            d += std::string(stand ? "stand" : "flight") + sf(" k %.0f dT %.0f K step %.0f: IGN %.0f -> ", k, dT, step ? 1 : 0, ign ? 1 : 0) +
                 (lit ? sf("RUN (E2 %.0f ms after the step)", n_e2) : std::string(stateName(r.e.state())) + " / " + abortName(r.e.abortCause())) +
                 after + sf(" (refuse %.0f); ", (double)r.o.cmd_refused);
          }
    check(n_false == 0 && n_ctrl_lit == 0, "Q2 a seat-TC step to T0 after E1 (unlit, vented chamber) never gives E2 (false light)",
          sf("false E2 %.0f of %.0f stepped cases; controls lit %.0f; ", n_false, n_case / 2, n_ctrl_lit) + d);
  }
  // ===================================================================== Q3 thresholds
  {   // PC_SENSOR HIGH TB-state at 4.75 V (flight RUN, one tick): 4.7495 V no TB, 4.7505 V TB
    auto tb = [](float v) { Rig f; f.toIgnition(); f.lightRun(3.0e5f); f.follow = true; f.run(300); f.follow = false;
                            f.in.pc_raw_V = v; f.tick(); f.follow = true; f.run(5); return (f.o.f3_flags & f3::TB_STATE) != 0; };
    const bool lo = tb(4.7495f), hi = tb(4.7505f);
    check(!lo && hi, "Q3a TB_STATE PC_SENSOR HIGH discriminates 4.7495 / 4.7505 V (flight RUN, one tick)", sf("4.7495 V TB %.0f, 4.7505 V TB %.0f", lo, hi));
  }
  {   // J-FWD indication 47.5 bar abs (one raw sample after E1)
    auto jf = [](float pa) { Rig j; j.toIgnition(); j.toE1(); j.run(5); j.setPcAbs(pa); j.tick(); j.setPcAbs(1.5e5f); j.run(3);
                             return (j.o.f3_flags & f3::JFWD_LS) != 0; };
    const bool lo = jf(47.49e5f), hi = jf(47.51e5f);
    check(!lo && hi, "Q3b JFWD_LS discriminates 47.49 / 47.51 bar abs (one raw sample in the window)", sf("47.49 -> %.0f, 47.51 -> %.0f", lo, hi));
  }
  {   // torch re-zero limit 0.60 bar: +0.595 accepted, +0.605 rejected (torch block; the Pc block is rejected at both)
    auto tz = [](float g) { Rig a; a.toIgnition(); a.lightRun(3.0e5f); a.burnToCoast(); a.setPcG(g); a.run(1400);
                            return std::make_pair(std::fabs(a.e.ptorchZero() - g) < 0.002e5f, (a.o.f3_flags & f3::PT_RZ_REJ) != 0); };
    const auto lo = tz(0.595e5f), hi = tz(0.605e5f);
    check(lo.first && !lo.second && !hi.first && hi.second, "Q3c torch re-zero limit discriminates 0.595 / 0.605 bar",
          sf("0.595: accepted %.0f rej %.0f; 0.605: accepted %.0f rej %.0f", lo.first, lo.second, hi.first, hi.second));
  }
  {   // BASE check (pad first start): P0 +0.75 kept / +0.77 BASE_HIGH refused; -0.75 kept / -0.77 BASE_AMB refused
    auto base = [](float g) { Rig r; r.torch_delay = 40; r.toIgnition(); r.setPcG(g); int n = 0;
                              while (r.e.state() == State::IGNITION && n < 400) { r.tick(); ++n; }
                              const bool refused = r.e.liftCommandTime() < 0.0 && r.e.abortCause() == Abort::PC_SENSOR;
                              return std::make_pair(refused, (int)((r.o.fault2 & f2::BASE_HIGH) ? 1 : ((r.o.ign_det & det::BASE_AMB) ? 2 : 0))); };
    const float b = cfg::kIgnBaseCheck_Pa;
    const auto p1 = base(b - 0.01e5f), p2 = base(b + 0.01e5f), m1 = base(-b + 0.01e5f), m2 = base(-b - 0.01e5f);
    check(!p1.first && p2.first && p2.second == 1 && !m1.first && m2.first && m2.second == 2,
          sf("Q3d BASE check %.2f bar discriminates +/-0.01 bar on both sides (pad: lift refused PC_SENSOR outside)", b / 1e5),
          sf("+%.2f refused %.0f, +%.2f refused %.0f (BASE_HIGH), ", (b - 0.01e5f) / 1e5, p1.first, (b + 0.01e5f) / 1e5, p2.first) +
              sf("-%.2f refused %.0f, -%.2f refused %.0f (BASE_AMB)", (b - 0.01e5f) / 1e5, m1.first, (b + 0.01e5f) / 1e5, m2.first));
  }
  std::printf("\n%d passed, %d failed (a FAIL is a finding candidate, not a test of the author's suite)\n", n_pass, n_fail);
  return 0;
}
