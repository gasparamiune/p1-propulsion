// REV-ELEC-5 reviewer probe (2026-10-21) on the v2.13 core: logic rig (probe B rig of REV-ELEC-4), TEST VALUES, not measurements or plant
// results. Every number it prints is CALC on the firmware logic.
// H   HOLD STRUCTURE (E4-01 / Q2 (1)): seat_comp_ is bit-constant from the tick after IGNITION entry to E2 + 0.45 s (lit) or to the
//     IGNITION exit (unlit) under TC4 waveforms that pass the step check (fast ramps <= 1.4 K per tick, slow ramps 4.9 K/s, +/-1.4 K
//     alternation) as well as steps; P0 and the E2 tick equal the no-error control bit for bit; unlit (0.42 bar cold flow): 0 E2, 0 b7.
//     Pad and stand FIRST starts and flight / stand RELIGHTS, k 1 / 3, coefficient sign +/-, error start E1 - 80 / - 25 / - 10 / + 5 / + 100
//     / + 300 ms. The same cases are run on a HOLD-DISABLED copy of the core (-DREV5_NO_HOLD, scripts/make_nohold.py) to show the probe
//     discriminates: there only the step / rate checks act.
// A   A5 (ii): A1 flight relight with SEAT_STEP latched in the coast and a stale Pc offset e (TEST VALUE, both signs) present from the coast
//     start: re-zero accept / reject, NOT_VENTED flag, torch gate (TORCH_FAULT at 0.16 s, no lift), BASE_HIGH / BASE_AMB, A7 hold low edge
//     (PC_SENSOR), E2, RUN. Sweeps across the +1.0 bar torch-gate and the -0.76 / -0.46 bar BASE bounds.
// Q1  E4-03 / UT-4: the 8 REV-ELEC-4 probe B re-ARM cases against a fresh ECU (expected 0 differ).
// S   split step (HAL zero-order hold, one conversion every 100 ms, a step split over two conversions as an integrating ADC / AVGSEL 2 can
//     present it): 2.9 K as 1.45 + 1.45 K, 3.2 K as 1.6 + 1.6 K, in COAST (outside the hold).
// Build: g++ -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -I$FW/src/core -I$FW/sil -DECU_SIL_TEST_HOOKS probe_v213.cpp $CORE
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
  std::fflush(stdout);
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
  float p_true_g = 0.0f, T_seat = 293.15f, coef_true = 0.0f, T_cal = 293.15f, pc_offset = 0.0f, tc_err = 0.0f;
  bool tc_override = false; float tc_value = 293.15f;
  float pintle_max = 0.0f; bool track_pintle = false;
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
    in.tc_bore_K = tc_override ? tc_value : T_seat + tc_err;
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
    in.ptorch_valid = true; in.ptorch_Pa = torch_flame ? 2.0e5f : std::fmax(0.0f, p_true_g);
    in.photo_valid = true; in.photo_V = (torch_flame || (o.state == State::RUN && plant_lit)) ? 1.0f : 0.10f;
    in.pmid_valid = true; in.pmid_hi = false;
    in.mv_ladder_ratio = ladder::nominalRatio(in.mv_open_sw, in.mv_closed_sw, in.pmid_hi);
    e.step(in, c, o); e.fillLog(in, o, lr);
    if (track_pintle) pintle_max = std::fmax(pintle_max, o.pintle_cmd_m);
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

// ---------------------------------------------------------------------------------------------------- H: hold structure
struct Wave { std::string name; int kind; float mag; double t0; };   // kind 0 step, 1 fast ramp 1.4 K/tick, 2 slow ramp 4.9 K/s, 3 alternation
static float waveErr(const Wave& w, double te) {   // te = time from E1 [s]
  if (te < w.t0) return 0.0f;
  const double dt = te - w.t0;
  switch (w.kind) {
    case 0: return w.mag;
    case 1: { const float r = 1.4f * static_cast<float>(std::floor(dt * 1000.0 + 1e-6) + 1.0); return w.mag < 0 ? std::fmax(w.mag, -r) : std::fmin(w.mag, r); }
    case 2: return static_cast<float>((w.mag < 0 ? -4.9 : 4.9) * dt);
    default: return (static_cast<long>(std::floor(dt * 1000.0 + 1e-6)) % 2 == 0) ? -1.4f : 0.0f;
  }
}
struct HRes { bool reached_ign = false, e2 = false, b7 = false, comp_const = true, step = false, hold_seen = false; double t_e1 = -1, t_e2 = -1, p0 = NAN;
              float comp0 = 0, comp_dev = 0; int abort = 0; double t_hold_end = -1, t_entry = -1; };
// one start from scratch (deterministic rig): type 0 pad first, 1 stand first, 2 flight relight, 3 stand relight; the TC4 error waveform is
// keyed to the predicted absolute E1 time (from the no-error control); the plant (light or cold flow) is keyed to the actual E1
static HRes runCase(int type, float coef, bool lit, const Wave* w, double tE1_pred, int horizon_ms) {
  const bool stand = type == 1 || type == 3, relight = type >= 2;
  RigS r(stand); r.e.setPcSeatCoef(coef); r.coef_true = coef; r.T_seat = 293.15f; r.torch_delay = 45;
  auto err = [&](double tnext) { return (w && tE1_pred > 0) ? waveErr(*w, tnext - tE1_pred) : 0.0f; };
  HRes h;
  auto stepTick = [&](Cmd cm) { r.tc_err = err(r.t + 1e-3); r.tick(cm); };
  if (!relight) {
    stepTick(Cmd::ARM); for (int i = 0; i < 600; ++i) stepTick(Cmd::NOP); stepTick(Cmd::IGNITE);
  } else {
    stepTick(Cmd::ARM); for (int i = 0; i < 600; ++i) stepTick(Cmd::NOP); stepTick(Cmd::IGNITE);
    for (int i = 0; i < 4000 && r.e.state() != State::IGNITION; ++i) stepTick(Cmd::NOP);
    for (int i = 0; i < 400 && r.e.liftCommandTime() < 0.0 && r.e.state() == State::IGNITION; ++i) stepTick(Cmd::NOP);
    for (int i = 0; i < 30; ++i) stepTick(Cmd::NOP);
    r.p_true_g = 3.0e5f - 101325.f;
    for (int i = 0; i < 60 && r.e.state() != State::RUN; ++i) stepTick(Cmd::NOP);
    r.follow = true; for (int i = 0; i < 800; ++i) stepTick(Cmd::NOP); r.follow = false; stepTick(Cmd::SHUTDOWN); r.p_true_g = 0.0f;
    for (int i = 0; i < 3000 && r.e.state() != State::COAST; ++i) stepTick(Cmd::NOP);
    // seat rise in the coast at a physical rate (A1 14 K at 2.0 K/s, stand 54 K at 2.4 K/s; max 2.42 K/s), then 0.70 / 1.40 K/s through
    // the relight (the Mechanical relight-E1 diaphragm rates, REV-ELEC-4 Q2) so that the hold is tested against a MOVING seat
    const float dT = stand ? 54.0f : 14.0f, rate = stand ? 2.4f : 2.0f, rate2 = stand ? 1.40f : 0.70f;
    while (r.T_seat < 293.15f + dT) { r.T_seat += rate * 1e-3f; stepTick(Cmd::NOP); }
    for (int i = 0; i < 200; ++i) { r.T_seat += rate2 * 1e-3f; stepTick(Cmd::NOP); }
    r.T_seat += rate2 * 1e-3f; stepTick(Cmd::RELIGHT);
  }
  const double t_cmd = r.t;
  bool comp_set = false, was_hold = false;
  double tE1 = -1;
  for (int n = 0; n < horizon_ms + 600; ++n) {
    const double tnext = r.t + 1e-3;
    if (tE1 < 0 && r.e.liftCommandTime() >= 0.0 && r.e.liftCommandTime() > t_cmd - 1e-9) tE1 = r.e.liftCommandTime();
    const double te = tE1 >= 0 ? tnext - tE1 : -1.0;
    if (tE1 >= 0 && !(lit && h.e2)) {
      if (lit) r.p_true_g = te < 0.030 ? 0.0f : 3.0e5f - 101325.f;
      else r.p_true_g = te < 0.030 ? 0.0f : (te < 0.070 ? 0.42e5f * (float)((te - 0.030) / 0.040) : 0.42e5f);
    }
    if (relight) r.T_seat += (stand ? 1.40f : 0.70f) * 1e-3f;
    if (lit && h.e2) r.follow = true;
    stepTick(Cmd::NOP);
    if (r.e.state() == State::IGNITION && !h.reached_ign) { h.reached_ign = true; h.t_entry = r.t; }
    const bool hold = r.e.pcSeatHold();
    if (hold) {
      h.hold_seen = true;
      if (!comp_set) { h.comp0 = r.o.pc_seat_comp_Pa; comp_set = true; }
      else if (r.o.pc_seat_comp_Pa != h.comp0) { h.comp_const = false; h.comp_dev = std::fmax(h.comp_dev, std::fabs(r.o.pc_seat_comp_Pa - h.comp0)); }
      was_hold = true;
    } else if (was_hold && h.t_hold_end < 0 && tE1 >= 0) h.t_hold_end = r.t - tE1;
    if (!h.e2 && r.e.state() == State::RUN) { h.e2 = true; h.t_e2 = tE1 >= 0 ? r.t - tE1 : -1; }
    if (h.reached_ign && (r.o.tlm_flags & tlmf::RISE_HELD_T)) h.b7 = true;
    if (std::isnan(h.p0) && std::isfinite(r.o.ign_ref_Pa) && h.reached_ign) h.p0 = r.o.ign_ref_Pa;
    if (!h.abort && h.reached_ign && r.e.abortCause() != Abort::NONE) h.abort = static_cast<int>(r.e.abortCause());
    if (tE1 >= 0 && r.t - tE1 > horizon_ms * 1e-3) break;
  }
  h.t_e1 = tE1; h.step = r.e.pcSeatStep();
  return h;
}

int main() {
  const float c1 = 0.0248e5f;   // Pa/K, the C1 typical
#ifdef REV5_NO_HOLD
  std::printf("CORE VARIANT: HOLD DISABLED (reviewer copy, -DREV5_NO_HOLD): only the step / rate checks act in the light window\n");
#else
  std::printf("CORE: v2.13 as staged\n");
#endif
#ifdef ECU_BPC1_SHOWN_VARIANT
  std::printf("BUILD: B-PC-1-shown (kIgnBaseCheck %.2f bar)\n", cfg::kIgnBaseCheck_Pa / 1e5);
#else
  std::printf("BUILD: default (kIgnBaseCheck %.2f bar)\n", cfg::kIgnBaseCheck_Pa / 1e5);
#endif
  // ===================================================================== H
  {
    std::vector<Wave> waves;
    const double t0s[] = {-0.080, -0.025, -0.010, 0.005, 0.100, 0.300};
    for (double t0 : t0s)
      for (float m : {-5.0f, -8.0f, -20.0f, -55.0f, 90.0f, 140.0f}) {
        char a[64];
        std::snprintf(a, sizeof a, "step%+.0fK@E1%+.0fms", m, t0 * 1e3); waves.push_back({a, 0, m, t0});
        std::snprintf(a, sizeof a, "ramp1.4Kpt%+.0fK@E1%+.0fms", m, t0 * 1e3); waves.push_back({a, 1, m, t0});
      }
    for (double t0 : {-1.0, -0.025}) for (float m : {-1.0f, 1.0f}) { char a[64]; std::snprintf(a, sizeof a, "slow%+.1fKps@E1%+.0fms", m * 4.9, t0 * 1e3); waves.push_back({a, 2, m, t0}); }
    waves.push_back({"alt1.4K@E1-25ms", 3, 0.0f, -0.025});
    int n_runs = 0, n_e2_unlit = 0, n_b7_unlit = 0, n_comp_moved = 0, n_p0_diff = 0, n_e2_tick_diff = 0, n_lit_not_run = 0, n_ctrl_bad = 0;
    int n_step = 0, n_noign = 0, n_no_ign_state = 0, n_inside = 0, n_before_p0 = 0, n_before_e2moved = 0, n_before_refused = 0; float dp0_before = 0.0f;
    std::string ex, ctrl_d;
    for (int type = 0; type < 4; ++type)
      for (float k : {1.0f, 3.0f})
        for (float sg : {1.0f, -1.0f})
          for (int lit = 1; lit >= 0; --lit) {
            const float coef = sg * k * c1;
            const HRes ctl = runCase(type, coef, lit == 1, nullptr, -1.0, 1500);
            const bool ctl_ok = ctl.reached_ign && ctl.t_e1 > 0 && (lit ? ctl.e2 : !ctl.e2) && ctl.comp_const && ctl.hold_seen;
            if (!ctl_ok) { ++n_ctrl_bad; ctrl_d += sf("CONTROL BAD type %.0f k %.0f s %+.0f lit %.0f (e2 %.0f comp_const %.0f, ", type, k, sg, lit, ctl.e2, ctl.comp_const) +
                                                   sf("ign %.0f e1 %.3f hold_seen %.0f); ", ctl.reached_ign, ctl.t_e1, ctl.hold_seen); continue; }   // r2b: 6-argument sf (was 7 specifiers)
            if (k == 3.0f && sg > 0 && lit)
              ctrl_d += sf("type %.0f k3 s+ lit control: E1 at %.3f s, E2 at E1 + %.0f ms, hold end at E1 + %.0f ms (E2 + %.0f ms); ", type, ctl.t_e1, ctl.t_e2 * 1e3,
                           ctl.t_hold_end * 1e3, (ctl.t_hold_end - ctl.t_e2) * 1e3);
            for (const Wave& w : waves) {
              const HRes h = runCase(type, coef, lit == 1, &w, ctl.t_e1, 1500);
              ++n_runs; if (h.step) ++n_step;
              bool bad = false;
              const bool inside = ctl.t_entry > 0 && ctl.t_e1 + w.t0 > ctl.t_entry + 0.5e-3;   // error starts after the IGNITION entry tick
              if (!h.reached_ign) { ++n_no_ign_state; if (!inside) ++n_before_refused; }
              if (!h.comp_const) { ++n_comp_moved; bad = true; }
              const bool p0d = h.reached_ign && !(h.p0 == ctl.p0) && !(std::isnan(h.p0) && std::isnan(ctl.p0));
              if (inside) { ++n_inside; if (p0d) { ++n_p0_diff; bad = true; } }
              else if (p0d) { ++n_before_p0; dp0_before = std::fmax(dp0_before, std::fabs(h.p0 - ctl.p0)); }
              if (lit) {
                if (!h.e2) { if (inside || h.reached_ign) { ++n_lit_not_run; bad = true; } }
                else if (std::fabs(h.t_e2 - ctl.t_e2) > 1e-9) { if (inside) { ++n_e2_tick_diff; bad = true; } else ++n_before_e2moved; }
              } else {
                if (h.e2) { ++n_e2_unlit; bad = true; }
                if (h.b7) { ++n_b7_unlit; bad = true; }
                if (h.abort == static_cast<int>(Abort::NO_IGNITION)) ++n_noign;
              }
              if (bad && ex.size() < 4000)
                ex += sf("type %.0f k %.0f s %+.0f lit %.0f ", type, k, sg, lit) + w.name +
                      sf(": comp_const %.0f (dev %.0f Pa) P0 %.1f vs %.1f Pa, E2 %.0f at %.1f ms", h.comp_const, h.comp_dev, h.p0, ctl.p0, h.e2, h.t_e2 * 1e3) +
                      sf(" vs %.1f, abort %.0f, ign %.0f; ", ctl.t_e2 * 1e3, h.abort, h.reached_ign);
            }
          }
    const bool ok = n_comp_moved == 0 && n_p0_diff == 0 && n_e2_tick_diff == 0 && n_lit_not_run == 0 && n_e2_unlit == 0 && n_b7_unlit == 0 && n_ctrl_bad == 0;
    check(ok, "H hold: comp bit-constant in the hold, P0 and the E2 tick equal the control, unlit 0 E2 / 0 b7, lit E2 (TC4 steps, sub-threshold ramps, slow ramps, alternation)",
          sf("%.0f runs (%.0f latched SEAT_STEP, %.0f never reached IGNITION); comp moved in the hold %.0f; P0 differs %.0f; lit E2 tick differs %.0f; ",
             n_runs, n_step, n_no_ign_state, n_comp_moved, n_p0_diff, n_e2_tick_diff) + sf("lit without E2 %.0f; unlit E2 %.0f; unlit b7 %.0f; unlit NO_IGNITION %.0f; bad controls %.0f; ", n_lit_not_run, n_e2_unlit, n_b7_unlit, n_noign, n_ctrl_bad) +
          sf("errors starting inside the hold: %.0f runs; errors starting before the IGNITION entry: P0 moved in %.0f (max %.1f Pa), lit E2 tick moved in %.0f, start refused before IGNITION %.0f; ",
             n_inside, n_before_p0, dp0_before, n_before_e2moved, n_before_refused) +
          ctrl_d + (ex.empty() ? std::string("no failing case") : std::string("first failing cases: ") + ex));
  }
  // ===================================================================== A: stale offset at the A1 relight
  {
    std::string d; int n = 0;
    struct AC { float e; int light_ms; };
    std::vector<AC> acs;
    for (float e_bar : {0.25f, 0.35f, 0.70f, 0.76f, 0.80f, 0.95f, 0.99f, 1.01f, 1.05f, 1.20f, -0.25f, -0.35f, -0.44f, -0.48f, -0.70f, -0.75f, -0.77f, -0.80f, -1.00f})
      acs.push_back({e_bar, 128});
    for (float e_bar : {-0.48f, -0.77f, -1.00f, -2.00f, -3.80f}) for (int lm : {30, 50, 60, 80}) acs.push_back({e_bar, lm});
    for (const AC& ac : acs) {
      const float e_bar = ac.e;
      const float coef = 3.0f * c1;
      RigS r(false); r.e.setPcSeatCoef(coef); r.coef_true = coef; r.T_seat = 293.15f; r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast();
      r.tc_err = 5.0f; r.run(5); r.tc_err = 0.0f;   // TC4 +5 K step in COAST -> SEAT_STEP (T_c frozen to the next ARM); the reading returns
      const bool step = r.e.pcSeatStep();
      r.pc_offset = e_bar * 1e5f;                   // the stale offset (TEST VALUE) from the coast start, seen by both coast re-zeros
      r.run(4000);
      const bool rz_rej = r.o.fault2 & f2::REZERO2_REJ;
      r.track_pintle = true; r.pintle_max = 0.0f;
      r.tick(Cmd::RELIGHT);
      const bool nv = r.o.fault2 & f2::NOT_VENTED;
      const bool rz2_rej_cmd = r.o.fault2 & f2::REZERO2_REJ;
      r.until(State::IGNITION, 4000);
      const bool ign = r.e.state() == State::IGNITION;
      // lit relight: chamber light 30 ms after E1 (3 bar abs)
      double t_e1 = -1, t_e2 = -1, t_ab = -1; std::string ab = "NONE"; float p0 = NAN; uint8_t det_f = 0, f2f = 0; float pint_at_abort = -1;
      for (int i = 0; i < 1500; ++i) {
        if (t_e1 < 0 && r.e.liftCommandTime() >= 0.0) t_e1 = r.t;
        if (t_e1 >= 0 && r.t - t_e1 >= ac.light_ms * 1e-3 && r.e.state() != State::ABORT && t_e2 < 0) r.p_true_g = 3.0e5f - 101325.f;
        if (t_e2 >= 0) r.follow = true;
        r.tick();
        if (std::isnan(p0) && std::isfinite(r.o.ign_ref_Pa)) p0 = r.o.ign_ref_Pa;
        det_f |= r.o.ign_det; f2f |= r.o.fault2;
        if (t_e2 < 0 && r.e.state() == State::RUN) t_e2 = r.t;
        if (t_ab < 0 && r.e.abortCause() != Abort::NONE) { t_ab = r.t; ab = abortName(r.e.abortCause()); pint_at_abort = r.pintle_max; }
      }
      ++n;
      (void)rz_rej;
      d += sf("e %+.2f bar light E1+%.0f ms: step %.0f, rz2_rej %.0f, NOT_VENTED %.0f, IGN %.0f, ", e_bar, ac.light_ms, step, rz2_rej_cmd, nv, ign) +
           (t_e1 >= 0 ? std::string("E1 yes") : std::string("no E1")) + sf(", P0 %+.3f bar, BASE_AMB %.0f, BASE_HIGH %.0f, ", std::isnan(p0) ? NAN : p0 / 1e5,
              (det_f & det::BASE_AMB) ? 1 : 0, (f2f & f2::BASE_HIGH) ? 1 : 0) +
           (t_e2 >= 0 ? sf("E2 at E1+%.0f ms", (t_e2 - t_e1) * 1e3) : std::string("no E2")) +
           (t_ab >= 0 ? std::string(", abort ") + ab + sf(" (pintle max before %.3f mm)", pint_at_abort * 1e3) : std::string(", no abort")) +
           std::string(", end state ") + stateName(r.e.state()) + "; ";
    }
    check(true, "A A5 (ii): A1 flight relight, k 3, SEAT_STEP latched in the coast, stale offset e present from the coast start (outcome table, TEST VALUES)", d);
  }
  // ===================================================================== Q1 re-ARM (E4-03 / UT-4)
  {
    std::string d; int n_diff = 0, n = 0;
    struct Q { float k, dT, pex; };
    const Q qs[] = {{1, 5, 0}, {1, 25, 0}, {3, 10, 0}, {3, 10, 0.6e5f}, {3, 20, 0}, {3, 20, 1.3e5f}, {3, 20, -1.3e5f}, {1, 25, 0.9e5f}};
    for (const Q& q : qs) {
      const float coef = q.k * c1;
      RigS f; f.e.setPcSeatCoef(coef); f.coef_true = coef; f.T_seat = 293.15f + q.dT; f.pc_offset = q.pex; f.run(300);
      f.tick(Cmd::ARM); f.run(5);
      const bool fresh_armed = f.e.state() == State::ARMED;
      RigS r; r.e.setPcSeatCoef(coef); r.coef_true = coef; r.T_seat = 293.15f; r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast();
      r.run(200); r.tick(Cmd::SAFE); r.run(5); r.tick(Cmd::DISARM); r.run(5);
      r.T_seat = 293.15f + q.dT; r.pc_offset = q.pex; r.run(300);
      const float comp_safe = r.o.pc_seat_comp_Pa;
      r.tick(Cmd::ARM); r.run(5);
      const bool re_armed = r.e.state() == State::ARMED;
      ++n; if (fresh_armed != re_armed) ++n_diff;
      d += sf("k %.0f dT %.0f K offset %+.1f bar: fresh ", q.k, q.dT, q.pex / 1e5) + (fresh_armed ? "ARMED" : "refused");
      d += std::string(", re-ARM ") + (re_armed ? "ARMED" : "refused") + sf(" (comp in SAFE %.3f bar); ", comp_safe / 1e5);
    }
    check(n_diff == 0, "Q1 re-ARM in the same power cycle decides as a fresh ECU (E4-03 / UT-4)", sf("%.0f of %.0f differ; ", n_diff, n) + d);
  }
  // ===================================================================== S: split step under the HAL zero-order hold (COAST)
  {
    std::string d;
    for (float S : {2.9f, 3.2f, 1.4f}) {
      const float coef = 3.0f * c1;
      RigS r(false); r.e.setPcSeatCoef(coef); r.coef_true = coef; r.T_seat = 293.15f; r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast();
      r.run(500);
      r.tc_override = true; r.tc_value = 293.15f; r.run(100);
      r.tc_value = 293.15f + S / 2.0f; r.run(100);     // conversion n: half the step (integrating ADC / AVGSEL 2)
      r.tc_value = 293.15f + S; r.run(2000);           // conversion n+1: the full step, held
      const float err_Pa = r.o.pc_seat_comp_Pa - coef * 0.0f;   // true seat unchanged: the whole compensation is error
      d += sf("step %.2f K as two conversions of %.2f K: SEAT_STEP %.0f, compensation error after 2 s %.3f bar (T_c - T_true %.2f K); ", S, S / 2.0f,
              r.e.pcSeatStep() ? 1 : 0, err_Pa / 1e5, r.e.pcSeatTcompK() - 293.15f);
    }
    check(true, "S split step (HAL ZOH 100 ms; step split over two conversions), COAST, k 3 (outcome table)", d);
  }
  // ===================================================================== D: slow drift fault outside the hold (FMEA residual check)
  {
    std::string d;
    for (float rate : {2.0f, 4.9f, 5.5f, 7.0f, 14.0f}) {
      const float coef = 3.0f * c1;
      RigS r(false); r.e.setPcSeatCoef(coef); r.coef_true = coef; r.T_seat = 293.15f; r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast();
      r.run(200);
      double t_trip = -1; const double t0 = r.t; float err_at_trip = 0.0f;
      for (int i = 0; i < 20000; ++i) {
        r.tc_err = rate * (float)(r.t + 1e-3 - t0); r.tick();
        if (t_trip < 0 && r.e.pcSeatStep()) { t_trip = r.t - t0; err_at_trip = r.e.pcSeatTcompK() - 293.15f; }
      }
      const float err_end = r.e.pcSeatTcompK() - 293.15f;
      d += sf("TC4 error ramp %.1f K/s for 20 s (COAST, k 3, true seat static): ", rate) +
           (t_trip >= 0 ? sf("SEAT_STEP at %.3f s with T_c moved %.2f K (%.3f bar); ", t_trip, err_at_trip, err_at_trip * coef / 1e5)
                        : sf("no SEAT_STEP; T_c - T_true after 20 s %.1f K = %.2f bar compensation error; frozen flag %.0f; ", err_end, err_end * coef / 1e5,
                             (r.o.f3_flags & f3::SEAT_FROZEN) ? 1 : 0));
    }
    check(true, "D slow TC4 drift fault outside the hold (rate check bound; FMEA residual)", d);
  }
  std::printf("\n%d passed, %d failed (a FAIL is a finding candidate, not a test of the author's suite)\n", n_pass, n_fail);
  return 0;
}
