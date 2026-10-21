// REV-ELEC-4 reviewer probe B (2026-10-21) on the v2.12 core: logic rig, TEST VALUES, not measurements or plant results.
// Fixes the probe A rig artefact: the C1 thermal drift and any Pc sensor offset now act on the Pc channel only; P_torch reads the TRUE
// chamber pressure (probe A fed the drifted Pc into P_torch and got TORCH_FAULT at ARM / relight above ~1.05 bar of drift).
// Q1  re-ARM in the same power cycle after a session (seat compensation still active in SAFE on the previous ARM reference; ARM check
//     subtracts the static term coef x (T - T_cal) again) against a fresh ECU with the same inputs; 'pex' is a Pc SENSOR OFFSET (the
//     fault the 0.5 bar ARM sanity check exists for), not chamber pressure.
// Q2  seat-TC reading error after E1 in an UNLIT start (cold-flow rise 0.42 bar from E1 + 30 ms, as the SIL S13T unlit runs show): spike
//     of 100 ms (one bad MAX31856 conversion), 250 ms, or persistent; reports E2 (false light), RISE_HELD_T (b7, the FC drogue-release
//     term), the state / abort 600 ms after the error starts.
// Build (absolute paths): g++ -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -I$FW/src/core -I$FW/sil -DECU_SIL_TEST_HOOKS
//   probe_v212b.cpp $FW/src/core/control.cpp $FW/src/core/engine_ecu.cpp $FW/src/core/protocol.cpp $FW/src/core/sensor_scale.cpp
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
struct RigS {
  EngineEcu e; Inputs in; Commands c; Outputs o; LogRecord lr; double t = 0; float thrust = 300.f;
  bool follow = false, plant_lit = true; int torch_delay = 0, torch_n = 0;
  // plant / sensor state: true chamber gauge pressure, seat temperature, true coefficient, Pc sensor offset, TC reading error
  float p_true_g = 0.0f, T_seat = 293.15f, coef_true = 0.0f, T_cal = 293.15f, pc_offset = 0.0f, tc_err = 0.0f;
  explicit RigS(bool stand = false) {
    e.init(0.0); e.ptank_cal_ok = true; e.setGimbalNotchCal(testNotchCal()); e.hbleed_fitted = false;
    in.arm_plug_present = true; in.arm_bus_on = true; in.vbat_V = 8.2f; in.mv_closed_sw = true; in.ptank_Pa = 50e5f; in.pfeed_Pa = 48e5f;
    in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f; in.tc_bore_valid = true;
    if (stand) { in.load_cell_N = 0.0f; in.mode_strap = strap::STAND; }
    apply();
  }
  void apply() {
    in.pc_Pa = p_true_g + coef_true * (T_seat - T_cal) + pc_offset;
    in.pc_raw_V = 0.5f + 4.f * in.pc_Pa / cfg::kPcXdcrFs_Pa;
    in.tc_bore_K = T_seat + tc_err;
  }
  void tick(Cmd cm = Cmd::NOP, uint16_t arg = 0) {
    t += 1e-3; in.t_s = t; c = Commands(); c.fast_valid = true; c.thrust_sp_N = thrust;
    if (cm != Cmd::NOP) { c.state_valid = true; c.cmd = cm; c.arg = arg; }
    if (follow && o.state == State::RUN && o.pc_sp_active_Pa > 0) p_true_g = o.pc_sp_active_Pa - 101325.f;
    apply();
    in.pintle_meas_m = o.pintle_cmd_m;
    if (o.servo_us[3] > 1800.f) { in.mv_open_sw = true; in.mv_closed_sw = false; }
    if (!o.mv_latch && o.servo_us[3] < 1600.f) { in.mv_open_sw = false; in.mv_closed_sw = true; }
    const bool both = o.sol[0] && o.sol[1];
    torch_n = both ? torch_n + 1 : 0;
    const bool torch_flame = both && torch_n > torch_delay;
    in.ptorch_valid = true; in.ptorch_Pa = torch_flame ? 2.0e5f : std::fmax(0.0f, p_true_g);   // TRUE pressure only (probe A artefact fixed)
    in.photo_valid = true; in.photo_V = (torch_flame || (o.state == State::RUN && plant_lit)) ? 1.0f : 0.10f;
    in.pmid_valid = true; in.pmid_hi = false;
    in.mv_ladder_ratio = ladder::nominalRatio(in.mv_open_sw, in.mv_closed_sw, in.pmid_hi);
    e.step(in, c, o); e.fillLog(in, o, lr);
  }
  void run(int n) { for (int i = 0; i < n; ++i) tick(); }
  int until(State s, int nmax) { int n = 0; while (e.state() != s && n < nmax) { tick(); ++n; } return n; }
  int toIgnition() { tick(Cmd::ARM); run(600); tick(Cmd::IGNITE); return until(State::IGNITION, 4000); }
  int toE1(int nmax = 400) { int n = 0; while (e.liftCommandTime() < 0.0 && e.state() == State::IGNITION && n < nmax) { tick(); ++n; } return n; }
  bool lightRun(float pc_abs = 3.0e5f) { toE1(); run(30); p_true_g = pc_abs - 101325.f; until(State::RUN, 60); return e.state() == State::RUN; }
  bool burnToCoast(int run_ms = 800) {
    follow = true; run(run_ms); follow = false; tick(Cmd::SHUTDOWN); p_true_g = 0.0f;
    until(State::COAST, 3000); return e.state() == State::COAST;
  }
};

int main() {
  const float c1 = 0.0248e5f;   // Pa/K, the C1 typical
  // ===================================================================== Q1 re-ARM after a session (same power cycle)
  {
    std::string d; int n_diff = 0, n_false_accept = 0, n = 0;
    struct Q { float k, dT, pex; };
    const Q qs[] = {{1, 5, 0}, {1, 25, 0}, {3, 10, 0}, {3, 10, 0.6e5f}, {3, 20, 0}, {3, 20, 1.3e5f}, {3, 20, -1.3e5f}, {1, 25, 0.9e5f}};
    for (const Q& q : qs) {
      const float coef = q.k * c1;
      RigS f; f.e.setPcSeatCoef(coef); f.coef_true = coef; f.T_seat = 293.15f + q.dT; f.pc_offset = q.pex; f.run(300);
      f.tick(Cmd::ARM); f.run(5);
      const bool fresh_armed = f.e.state() == State::ARMED;
      const std::string fresh_why = fresh_armed ? "ARMED" : std::string(stateName(f.e.state())) + "/" + abortName(f.e.abortCause());
      RigS r; r.e.setPcSeatCoef(coef); r.coef_true = coef; r.T_seat = 293.15f; r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast();
      r.run(200); r.tick(Cmd::SAFE); r.run(5); r.tick(Cmd::DISARM); r.run(5);
      const bool in_safe = r.e.state() == State::SAFE;
      r.T_seat = 293.15f + q.dT; r.pc_offset = q.pex; r.run(300);
      const float comp_safe = r.o.pc_seat_comp_Pa;
      r.tick(Cmd::ARM); r.run(5);
      const bool re_armed = r.e.state() == State::ARMED;
      const std::string re_why = re_armed ? "ARMED" : std::string(stateName(r.e.state())) + "/" + abortName(r.e.abortCause());
      ++n; if (fresh_armed != re_armed) ++n_diff; if (re_armed && !fresh_armed) ++n_false_accept;
      d += sf("k %.0f dT %.0f K offset %+.1f bar: fresh ", q.k, q.dT, q.pex / 1e5) + fresh_why;
      d += std::string(", re-ARM ") + re_why + sf(" (in SAFE %.0f, comp in SAFE %.3f bar, expected re-ARM residual %.3f bar); ", in_safe ? 1 : 0, comp_safe / 1e5,
                                                 (q.pex - coef * q.dT) / 1e5);
    }
    check(n_diff == 0, "Q1 re-ARM in the same power cycle decides as a fresh ECU (expected: equal decisions)",
          sf("%.0f of %.0f differ, %.0f re-ARM accepts a Pc offset the fresh ECU refuses; ", n_diff, n, n_false_accept) + d);
  }
  // ===================================================================== Q2 seat-TC error after E1, unlit start with cold flow
  {
    std::string d; int n_false = 0, n_b7 = 0, n_case = 0, n_ctrl = 0;
    for (bool stand : {false, true})
      for (float k : {1.0f, 3.0f})
        for (float X : {5.0f, 8.0f, 15.0f, 20.0f, 55.0f})
          for (int dur : {0, 100, 250, 100000}) {   // 0 = control (no error)
            if (dur == 0 && X != 5.0f) continue;
            const float coef = k * c1;
            const float dT = stand ? 54.0f : 14.0f;   // seat rise at the relight (Mechanical SIM, A1 / stand after B1)
            RigS r(stand); r.e.setPcSeatCoef(coef); r.coef_true = coef; r.T_seat = 293.15f; r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast();
            for (int i = 0; i < 4000; ++i) { r.T_seat = 293.15f + dT * std::fmin(1.0f, i / 3000.0f); r.tick(); }
            r.plant_lit = false;
            r.tick(Cmd::RELIGHT); r.until(State::IGNITION, 4000);
            const bool ign = r.e.state() == State::IGNITION;
            r.toE1(); const double tE1 = r.t;
            int n = 0; double t_e2 = -1, t_b7 = -1, t_ab = -1; std::string ab = "NONE";
            while (n < 700) {
              const double te = r.t - tE1;
              r.p_true_g = te < 0.030 ? 0.0f : (te < 0.070 ? 0.42e5f * (float)((te - 0.030) / 0.040) : 0.42e5f);   // unlit cold flow
              r.tc_err = (dur > 0 && te >= 0.005 && te < 0.005 + dur * 1e-3) ? -X : 0.0f;
              r.tick(); ++n;
              if (t_e2 < 0 && r.e.state() == State::RUN) t_e2 = r.t - tE1;
              if (t_b7 < 0 && (r.o.tlm_flags & tlmf::RISE_HELD_T)) t_b7 = r.t - tE1;
              if (t_ab < 0 && r.e.abortCause() != Abort::NONE) { t_ab = r.t - tE1; ab = abortName(r.e.abortCause()); }
            }
            ++n_case;
            if (dur > 0 && t_e2 >= 0) ++n_false;
            if (dur > 0 && t_b7 >= 0) ++n_b7;
            if (dur == 0 && t_e2 >= 0) ++n_ctrl;
            if (dur == 0) { d += std::string(stand ? "stand" : "flight") + sf(" k %.0f control: E2 %.0f; ", k, t_e2 >= 0 ? 1 : 0); continue; }
            d += std::string(stand ? "stand" : "flight") + sf(" k %.0f TC -%.0f K for %.0f ms (+%.3f bar): IGN %.0f, ", k, X, dur > 10000 ? -1.0 : (double)dur,
                                                             coef * X / 1e5, ign ? 1 : 0) +
                 (t_e2 >= 0 ? sf("FALSE E2 at E1+%.0f ms", t_e2 * 1e3) : std::string("no E2")) +
                 (t_b7 >= 0 ? sf(", b7 at E1+%.0f ms", t_b7 * 1e3) : std::string(", b7 0")) +
                 (t_ab >= 0 ? sf(", abort at E1+%.0f ms ", t_ab * 1e3) + ab : std::string(", no abort in 0.7 s")) + "; ";
          }
    check(n_false == 0 && n_ctrl == 0, "Q2 a seat-TC reading error after E1 in an unlit start never gives E2 (false light)",
          sf("false E2 %.0f, b7 latched %.0f of %.0f error cases; controls with E2 %.0f; ", n_false, n_b7, n_case - 4, n_ctrl) + d);
  }
  std::printf("\n%d passed, %d failed (a FAIL is a finding candidate, not a test of the author's suite)\n", n_pass, n_fail);
  return 0;
}
