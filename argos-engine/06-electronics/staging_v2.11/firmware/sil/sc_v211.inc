// v2.11 SIL scenarios (2026-10-20, lead brief Electronics v2.11, LEAD CHANGELOG 216 / 227 / 230). Included by sil_main.cpp before main().
//   S6R  sil s6r <out>     LEAD 216 (3): in-window genuine over-pressure (50 bar steps, ramps to 60 bar, FA-1 followed by 35-50 bar plateaus)
//                          on the A1 flight relight, as built and ride-through builds, each checked against Mechanical's LC-TB70 envelope
//                          (04-fea/v352/lc_tb70_envelope_v1.json 6f710726e4787134, lc_tb70_envelope.py inside() 855ebe04dfe5dbd0)
//   S6C  sil rccost <out>  LEAD 216 (3): the fixed comparator RC costed over the whole burn (S6 hardware-path cases at tau 5.225 / 12.825 /
//                          13.552 ms)
// SIL plant on ASSUMED / COMB SIM inputs: interface and sequencing evidence, not physical approval.
#include "fa1_replay_cases.h"

namespace v211 {

constexpr double kMEOP = 45.0e5, kTB70 = 58.1e5, kTBS = 63.1e5, kFA1 = 75.519e5, kJFWD = 60.0e5;   // [MECH lc_tb70_envelope_v1] Pa abs
constexpr double kTEvent = 0.300, kTFa1 = 0.0030, kTrFa1 = 0.0008;                                  // [MECH] s

// event profiles: tau [s] from the trigger, p0 = head pressure at the trigger [Pa abs] -> Pa abs
using Prof = std::function<double(double, double)>;
// Mechanical's FA-1 pulse (lc_tb70_envelope.py fa1_pulse): 1.01325 -> 75.519 bar abs linear over tr = 0.8 ms / 0.8 (10-90 % 0.8 ms), then
// exponential decay with tau_d such that the time above 45 bar abs is 3.0 ms (Combustion v2.4 worst row, sax.py FA1)
static double fa1Env(double tau) {
  const double p0 = 1.01325, P = 75.519, q = (45.0 - p0) / (P - p0), tr = kTrFa1 / 0.8;
  const double td = (kTFa1 - tr * (1.0 - q)) / (-std::log(q));
  if (tau < 0.0) return p0 * 1e5;
  const double x = tau <= tr ? tau / tr : std::exp(-(tau - tr) / td);
  return (p0 + (P - p0) * x) * 1e5;
}
constexpr double kFa1EnvTpk = kTrFa1 / 0.8;
// Combustion v2.4a FA-1 replay history k (fa1_replay_cases.h, bar abs, 0.1 ms grid, 25 ms); after 25 ms the replay contributes nothing
static double fa1Rep(int k, double tau) {
  const auto& c = fa1rep::kCases[k];
  if (tau < 0.0 || tau >= 0.025) return 101325.0;
  const int j = std::min(249, static_cast<int>(tau / 1e-4));
  const double f = std::min(1.0, tau / 1e-4 - j);
  return (c.h[j] + (c.h[j + 1] - c.h[j]) * f) * 1e5;
}
static double fa1RepTpk(int k) {
  const auto& c = fa1rep::kCases[k]; int jm = 0;
  for (int j = 1; j < 251; ++j) if (c.h[j] > c.h[jm]) jm = j;
  return jm * 1e-4;
}

struct GopCase { std::string name, family; int trig; double dt; Prof prof; std::string note; };
struct GopBuild { std::string name; int ride; double tau; double band; bool fw_off; };

struct Env { bool inside = true; int zone = 0; bool jfwd = false; double rise = NAN; std::string why; };
// Mechanical's inside() on the plant-step metrics (sim.h env_*); the 10-90 % rise of a Z3 pulse is a property of the INPUT history (the ECU
// cannot change it): it is taken from the profile (rise_in, NaN = no Z3 pulse in the input)
static Env envCheck(const Sim& s, double rise_in) {
  Env e;
  const double pk = s.env_pk;
  e.zone = pk > kTBS ? 3 : pk > kTB70 ? 2 : pk > kMEOP ? 1 : 0;
  e.jfwd = pk > kJFWD;
  e.rise = rise_in;
  char b[200];
  if (pk > kFA1 + 1.0) { std::snprintf(b, sizeof b, "P %.3f > 75.519 bar abs; ", pk / 1e5); e.why += b; }   // 1 Pa: rounding
  if (s.env_t45a >= 0.0 && s.env_t45b - s.env_t45a > kTEvent) {
    std::snprintf(b, sizeof b, "P > MEOP at tau %.1f ms > 300 ms; ", (s.env_t45b - s.env_t45a) * 1e3); e.why += b;
  }
  if (s.env_t63a >= 0.0 && s.env_t63b - s.env_t63a > kTFa1) {
    std::snprintf(b, sizeof b, "P > 63.1 bar abs for %.2f ms > 3.0 ms; ", (s.env_t63b - s.env_t63a) * 1e3); e.why += b;
  }
  if (e.zone == 3 && std::isfinite(rise_in) && rise_in < kTrFa1 - 2e-6) {   // 2 us = the profile sampling
    std::snprintf(b, sizeof b, "Z3 pulse rise %.3f ms < 0.8 ms (input); ", rise_in * 1e3); e.why += b;
  }
  e.inside = e.why.empty();
  return e;
}
// input history: peak over 0-30 ms and the 10-90 % rise of its first pulse (base = profile at tau 0), 1 us resolution (rise NaN when the
// peak is <= 63.1 bar abs: no Z3 pulse)
struct ProfInfo { double pk = 0.0, rise = NAN, span63 = 0.0; std::string why; };   // why: the INPUT alone leaves the envelope (Z3 rules)
static ProfInfo profInfo(const Prof& f) {
  ProfInfo o; double t_pk = 0.0, t63a = -1.0, t63b = -1.0;
  for (int i = 0; i <= 30000; ++i) {
    const double v = f(i * 1e-6, 101325.0);
    if (v > o.pk) { o.pk = v; t_pk = i * 1e-6; }
    if (v > kTBS) { if (t63a < 0.0) t63a = i * 1e-6; t63b = i * 1e-6; }
  }
  if (t63a >= 0.0) o.span63 = t63b - t63a;
  char b[160];
  if (o.pk > kFA1 + 1.0) { std::snprintf(b, sizeof b, "input peak %.3f > 75.519 bar abs; ", o.pk / 1e5); o.why += b; }   // 1 Pa: rounding
  if (o.span63 > kTFa1) { std::snprintf(b, sizeof b, "input above 63.1 bar abs for %.2f ms > 3.0 ms; ", o.span63 * 1e3); o.why += b; }
  if (o.pk <= kTBS) return o;
  const double p0 = f(0.0, 101325.0), lo = p0 + 0.1 * (o.pk - p0), hi = p0 + 0.9 * (o.pk - p0);
  double t10 = NAN, t90 = NAN;
  for (int i = 0; i <= static_cast<int>(t_pk / 1e-6) + 1; ++i) {
    const double v = f(i * 1e-6, 101325.0);
    if (std::isnan(t10) && v >= lo) t10 = i * 1e-6;
    if (std::isnan(t90) && v >= hi) { t90 = i * 1e-6; break; }
  }
  o.rise = t90 - t10;
  if (o.rise < kTrFa1 - 2e-6) { std::snprintf(b, sizeof b, "input Z3 rise %.3f ms < 0.8 ms; ", o.rise * 1e3); o.why += b; }
  return o;
}
static void writeTraceGz(const Sim& s, const std::string& fn) {   // bounding / failing cases only (lead disk rule): gzip CSV, tau [ms], p [bar abs]
  if (const char* e = std::getenv("SIL_NO_TRACE")) if (e[0] == '1') return;
  std::string cmd = "gzip -9 > '" + fn + "'";
  FILE* p = popen(cmd.c_str(), "w");
  if (!p) return;
  std::fprintf(p, "tau_ms,p_head_bar_abs\n");
  for (size_t i = 0; i < s.gtr_t.size(); ++i) if (i % 4 == 0 || s.gtr_t[i] > 0.05f) std::fprintf(p, "%.3f,%.3f\n", s.gtr_t[i] * 1e3, s.gtr_p[i] / 1e5);
  pclose(p);
}
static std::string jb(bool b) { return b ? "true" : "false"; }

// ---------------------------------------------------------------------------------------------------------------- S6R
static void scS6R() {
  using ecu::Abort;
  std::vector<GopCase> cases;
  // steps rise linearly over 1.0 ms from the head pressure at the trigger (10-90 % 0.8 ms, Mechanical's FA-1 pulse convention; a head
  // pressure cannot step faster than the chamber filling allows); step0 = ideal step (one plant step) as a sensitivity
  auto step = [](double P) { return Prof([P](double tau, double p0) { return p0 + (P - p0) * std::min(1.0, tau / 1.0e-3); }); };
  auto step0 = [](double P) { return Prof([P](double, double) { return P; }); };
  auto ramp = [](double P, double Tr) { return Prof([P, Tr](double tau, double p0) { return p0 + (P - p0) * std::min(1.0, tau / Tr); }); };
  auto envPl = [](double P) { return Prof([P](double tau, double) { const double x = fa1Env(tau); return tau <= kFa1EnvTpk ? x : std::max(x, P); }); };
  auto repPl = [](int k, double P) {
    const double tpk = fa1RepTpk(k);
    return Prof([k, P, tpk](double tau, double) { const double x = fa1Rep(k, tau); return (tau <= tpk || P <= 0.0) ? x : std::max(x, P); });
  };
  cases.push_back({"step50_at_plant_light", "step50", 1, 0.0, step(50e5), "50 bar abs from the first plant-light tick (window open: IGNITION)"});
  cases.push_back({"step50_at_E2_plus_5ms", "step50", 2, 0.005, step(50e5), "inside the post-E2 part of the window (E2 + 15 ms)"});
  cases.push_back({"step50_at_E2_plus_12ms", "step50", 2, 0.012, step(50e5), "T45 (7 ms) runs past the window end: as-built timing from E2 + 15 ms"});
  cases.push_back({"step50_at_E2_plus_30ms_post_window", "step50", 2, 0.030, step(50e5), "contrast: after the window (as-built rules in both builds)"});
  cases.push_back({"step50_ideal_at_plant_light", "step50_ideal", 1, 0.0, step0(50e5), "sensitivity: ideal 25 us step (rings the seat passage)"});
  cases.push_back({"step50_ideal_at_E2_plus_5ms", "step50_ideal", 2, 0.005, step0(50e5), "sensitivity: ideal 25 us step"});
  cases.push_back({"step50_ideal_at_E2_plus_12ms", "step50_ideal", 2, 0.012, step0(50e5), "sensitivity: ideal 25 us step"});
  for (double Tr : {0.020, 0.050, 0.100}) {
    char n[80]; std::snprintf(n, sizeof n, "ramp60_%.0fms_at_plant_light", Tr * 1e3);
    cases.push_back({n, "ramp60", 1, 0.0, ramp(60e5, Tr), "linear from the head pressure at the trigger to 60 bar abs, then held"});
  }
  cases.push_back({"ramp60_20ms_at_E2_plus_5ms", "ramp60", 2, 0.005, ramp(60e5, 0.020), "linear to 60 bar abs from E2 + 5 ms, then held"});
  cases.push_back({"fa1env_alone_control", "fa1env", 1, 0.0, Prof([](double tau, double) { return fa1Env(tau); }),
                   "Mechanical's FA-1 pulse alone (75.519 bar abs, 3.0 ms above 45): ride-through target, no plateau"});
  for (double P : {35.0, 40.0, 45.0, 47.0, 50.0}) {
    char n[80]; std::snprintf(n, sizeof n, "fa1env_then_plateau_%.0fbar", P);
    cases.push_back({n, "fa1env_plateau", 1, 0.0, envPl(P * 1e5), "FA-1 pulse, then the head stays at the plateau (max of the decaying pulse and P)"});
  }
  const int kT45 = 3, kFace = 0;   // fa1rep::kCases: [3] max_t45 (62.958 bar face peak), [0] max_face (125.139 bar)
  cases.push_back({"fa1rep_max_t45_alone_control", "fa1rep", 1, 0.0, repPl(kT45, 0.0), "Combustion v2.4a replay max_t45 alone"});
  for (double P : {35.0, 40.0, 45.0, 47.0, 50.0}) {
    char n[80]; std::snprintf(n, sizeof n, "fa1rep_max_t45_then_plateau_%.0fbar", P);
    cases.push_back({n, "fa1rep_plateau", 1, 0.0, repPl(kT45, P * 1e5), "replay max_t45, then the plateau"});
  }
  cases.push_back({"fa1rep_max_face_alone_control", "fa1rep", 1, 0.0, repPl(kFace, 0.0),
                   "replay max_face (125.139 bar abs at the face: above the 75.519 bar Z3 limit BY THE INPUT)"});
  cases.push_back({"fa1rep_max_face_then_plateau_50bar", "fa1rep_plateau", 1, 0.0, repPl(kFace, 50e5), "replay max_face, then 50 bar abs"});
  const std::vector<GopBuild> builds = {
      {"as_built", 0, ovp3::kTau_s, 0.0, false},
      {"ride", 1, ecu::cfg::kRideCmpTauNom_s, 0.0, false},
      {"ride_tauMax_bandHigh", 1, ecu::cfg::kRideCmpTauMax_s, 1.0, false},
      {"ride_hwOnly_tauMax_bandHigh", 1, ecu::cfg::kRideCmpTauMax_s, 1.0, true},
      {"as_built_hwOnly_bandHigh", 0, ovp3::kTau_s, 1.0, true},
  };
  J j;
  j.k("id").v("sil_S6R_v2p11"); j.k("version").v("v2.11"); j.k("date").v("2026-10-20");
  j.k("scenario").v("S6R LEAD 216 (3): in-window genuine over-pressure on the A1 flight relight (pad start 1.40 s 300 N, MECO 2.40 s, A1 state at MECO + 0.3 s, "
                    "RELIGHT 5.00 s at 200 N; flight mode, rule FLIGHT_RELIGHT). From the trigger the head pressure seen by the Pc chain is max(plant, profile x "
                    "decay): the profile holds until the first ECU ABORT / SAFE or ARM-bus loss, then decays with the plant injector-flow ratio (ASSUMED; "
                    "sim.h gop). Each case checked against Mechanical's LC-TB70 envelope (lc_tb70_envelope_v1 6f710726e4787134, inside() of "
                    "lc_tb70_envelope.py 855ebe04dfe5dbd0) on the plant-step (25 us) head pressure: Z0 <= 45, Z1 <= 58.1, Z2 <= 63.1, Z3 <= 75.519 bar abs "
                    "(tau <= 3 ms, span above 63.1 <= 3.0 ms, 10-90 % rise >= 0.8 ms: input property), nothing above 45 bar later than 300 ms after the "
                    "first crossing; J-FWD rule = any excursion above 60 bar abs. Pass = aborted and inside (controls: no plateau, informational). "
                    "SIM on ASSUMED / COMB SIM inputs, not physical approval.");
  j.k("envelope").v("Z1 label 'case at the 448.15 K abort' (Mechanical's TB thermal field); the v2.11 case-TC abort in force is A = 423.15 K "
                    "(lead ruling 2026-10-20T21:46:49Z): the analysed thermal state is hotter than any the abort now admits");
  std::string bl = "[";
  for (size_t b = 0; b < builds.size(); ++b) {
    char q[300]; std::snprintf(q, sizeof q, "%s{\"build\": \"%s\", \"ride_through\": %d, \"comparator_tau_ms\": %.3f, \"trip_shift_band\": %.0f, \"fw_ovp_off\": %s}",
                               b ? ", " : "", builds[b].name.c_str(), builds[b].ride, builds[b].tau * 1e3, builds[b].band, jb(builds[b].fw_off).c_str());
    bl += q;
  }
  j.k("builds").raw(bl + "]");
  std::string arr = "[";
  int n = 0, n_pass = 0, n_req = 0, n_out = 0, n_inout = 0;
  for (size_t ci = 0; ci < cases.size(); ++ci) {
    const GopCase& G = cases[ci];
    const ProfInfo pi = profInfo(G.prof);
    const double rise_in = pi.rise;
    const bool control = G.family == "fa1env" || G.family == "fa1rep";
    for (size_t bi = 0; bi < builds.size(); ++bi) {
      const GopBuild& B = builds[bi];
      SimConfig c = nominal(7001 + static_cast<uint32_t>(ci));
      c.ride_fw = B.ride; c.ovp3_tau = B.tau; c.ovp3_trip_Pa_abs += B.band * ovp3::kBandPa;
      Sim s(c);
      const double t_meco = 2.40, t_rl = 5.00;
      s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {t_meco, Cmd::SHUTDOWN, 0}, {t_rl, Cmd::RELIGHT, 0}};
      s.thrust_cmd = [t_meco](double t) { return t < t_meco ? 300.0 : 200.0; };
      const A1State a;
      s.hooks.push_back({t_meco + 0.30, [a](Sim& qq) { qq.eng.setTankState(a.T, a.m); qq.eng.Dport = a.D; }});
      if (B.fw_off) { s.fw_ovp_disabled = true; }
      s.gop = G.prof; s.gop_trig = G.trig; s.gop_after = t_rl; s.gop_dt = G.dt;
      s.run(t_rl + 1.30);
      if (const char* dbg = std::getenv("S6R_CSV"))   // debugging aid: S6R_CSV=<case>__<build>[=<path>] writes that run's window CSV
        if ((G.name + "__" + B.name) == std::string(dbg).substr(0, std::string(dbg).find('='))) {
          const std::string d(dbg); const size_t e = d.find('=');
          s.writeCsv(e == std::string::npos ? OUT + "/S6R_debug.csv" : d.substr(e + 1), s.gop_t0 - 0.03, s.gop_t0 + 0.12);
        }
      const auto& r = s.rec();
      double t_light = NAN; for (const Rec& x : r) if (x.t >= t_rl && x.ignited) { t_light = x.t; break; }
      const double e2 = s.run_entry_t.size() >= 2 ? s.run_entry_t[1] : NAN;   // [0] = the pad start
      int cause = 0; double t_ab = NAN;
      for (const Rec& x : r) if (x.t >= t_rl && x.abort && std::isnan(t_ab)) { cause = x.abort; t_ab = x.t; }
      double pcf_ab = NAN; int ovr_ab = 0; bool win_ab = false;
      for (const Rec& x : r) if (std::isfinite(t_ab) && x.t >= t_ab - 1e-9) { pcf_ab = x.Pc_meas; ovr_ab = x.ovr_flags; break; }
      for (const Rec& x : r) if (std::isfinite(t_ab) && x.t >= t_ab - 1.5e-3 && x.t <= t_ab + 1e-9) win_ab = win_ab || (x.ovr_flags & ecu::ovr::RIDE_WIN);
      const double t0 = s.gop_t0;
      const double t_mvc = firstTime(r, std::isfinite(t0) && t0 > 0 ? t0 : t_rl, [](const Rec& x) { return x.mv < 0.03; });
      const double t_armoff = firstTime(r, t_rl, [](const Rec& x) { return !x.arm_bus; });
      const Env e = envCheck(s, rise_in);
      const bool aborted = cause != 0;
      const bool in_out = !pi.why.empty();   // the input history alone already leaves the envelope (not an ECU result)
      const bool ok = control ? e.inside : (aborted && e.inside);
      const std::string cls = in_out ? "INPUT_outside_envelope" : control ? (e.inside ? "CONTROL_inside" : "CONTROL_outside")
                                     : !aborted ? "FAIL_no_abort" : e.inside ? "PASS_aborted_inside" : "FAIL_aborted_outside";
      if (!control && !in_out) { ++n_req; n_pass += ok; }
      n_out += !e.inside && !in_out; n_inout += in_out; ++n;
      const bool bounding = (!e.inside && !in_out) || (!control && !aborted && !in_out) || (in_out && B.name == "ride") ||
                            ((G.name == "step50_at_E2_plus_12ms" || G.name == "step50_ideal_at_E2_plus_5ms" || G.name == "fa1env_then_plateau_50bar" ||
                              G.name == "ramp60_20ms_at_plant_light") &&
                             (B.name == "ride" || B.name == "ride_hwOnly_tauMax_bandHigh"));
      std::string trace;
      if (bounding) { trace = "S6R_" + G.name + "__" + B.name + ".csv.gz"; writeTraceGz(s, OUT + "/" + trace); }
      char bb[2600];
      std::snprintf(bb, sizeof bb,
                    "%s{\"case\": \"%s\", \"family\": \"%s\", \"build\": \"%s\", \"note\": \"%s\", \"trigger\": \"%s\", \"trigger_from_light_ms\": %.1f, "
                    "\"trigger_from_E2_ms\": %.1f, \"E2_from_light_ms\": %.1f, \"aborted\": %s, \"cause\": \"%s\", \"trigger_to_abort_ms\": %.1f, "
                    "\"abort_in_ride_window\": %s, \"head_at_abort_bar_abs\": %.2f, \"filtered_Pc_at_abort_bar_abs\": %.2f, \"ovr_flags_at_abort\": %d, "
                    "\"trigger_to_hw_comparator_trip_ms\": %.1f, \"trigger_to_ARM_bus_off_ms\": %.1f, \"trigger_to_MV_closed_ms\": %.1f, "
                    "\"ride_tolerated_ticks\": %d, \"peak_head_bar_abs\": %.2f, \"first_above_45_from_trigger_ms\": %.2f, \"span_above_45_ms\": %.2f, "
                    "\"time_above_45_ms\": %.2f, \"time_above_58p1_ms\": %.2f, \"time_above_60_ms\": %.2f, \"time_above_63p1_ms\": %.2f, \"span_above_63p1_ms\": %.2f, "
                    "\"input_peak_bar_abs\": %.2f, \"input_rise_10_90_ms\": %.3f, \"zone_max\": %d, \"inside_LC_TB70\": %s, \"reasons\": \"%s\", \"jfwd_rule_triggered\": %s, "
                    "\"input_outside_reasons\": \"%s\", \"control_case\": %s, \"class\": \"%s\", \"pass\": %s, \"trace\": \"%s\"}",
                    n > 1 ? ", " : "", G.name.c_str(), G.family.c_str(), B.name.c_str(), G.note.c_str(), G.trig == 1 ? "plant_light" : "E2",
                    (t0 - t_light) * 1e3, (t0 - e2) * 1e3, (e2 - t_light) * 1e3, jb(aborted).c_str(), ecu::abortName(static_cast<Abort>(cause)),
                    (t_ab - t0) * 1e3, jb(win_ab).c_str(), s.gop_p_ab / 1e5, pcf_ab / 1e5, ovr_ab, s.ovp_trip_t >= 0 ? (s.ovp_trip_t - t0) * 1e3 : NAN,
                    (t_armoff - t0) * 1e3, (t_mvc - t0) * 1e3, s.ecu.rideTolTicks(), s.env_pk / 1e5,
                    s.env_t45a >= 0 ? (s.env_t45a - t0) * 1e3 : NAN, s.env_t45a >= 0 ? (s.env_t45b - s.env_t45a) * 1e3 : 0.0, s.env_t45 * 1e3,
                    s.env_t581 * 1e3, s.env_t60 * 1e3, s.env_t631 * 1e3, s.env_t63a >= 0 ? (s.env_t63b - s.env_t63a) * 1e3 : 0.0, pi.pk / 1e5, e.rise * 1e3, e.zone,
                    jb(e.inside).c_str(), e.why.c_str(), jb(e.jfwd).c_str(), pi.why.c_str(), jb(control).c_str(), cls.c_str(),
                    in_out ? "null" : jb(ok).c_str(), trace.c_str());
      arr += bb;
      std::printf("S6R %-38s %-28s %-15s +%6.1f ms win %d head@ab %5.1f pk %6.2f t45 %6.1f ms span45 %6.1f z%d %s jfwd %d %s\n", G.name.c_str(),
                  B.name.c_str(), ecu::abortName(static_cast<Abort>(cause)), (t_ab - t0) * 1e3, win_ab ? 1 : 0, s.gop_p_ab / 1e5, s.env_pk / 1e5,
                  s.env_t45 * 1e3, s.env_t45a >= 0 ? (s.env_t45b - s.env_t45a) * 1e3 : 0.0, e.zone, e.inside ? "IN " : "OUT", e.jfwd ? 1 : 0,
                  cls.c_str());
      std::fflush(stdout);
    }
  }
  j.k("cases").raw(arr + "]");
  j.k("required_cases").v(n_req); j.k("required_passed").v(n_pass); j.k("runs").v(n); j.k("runs_outside_envelope_ecu").v(n_out);
  j.k("runs_input_outside_envelope").v(n_inout);
  writeFile(OUT + "/S6R_in_window_overpressure.json", j.str());
}

// ---------------------------------------------------------------------------------------------------------------- S6C
// The ride-through BOM variant fixes the comparator RC for the WHOLE burn (LEAD 216 (3)). Cost: the S6 cases where the hardware comparator
// acts (firmware over-pressure check off, or racing it), pad first start at 300 / 500 N, at tau = as built 5.225 ms, ride nominal 12.825 ms and
// the ride tolerance maximum 13.552 ms. Envelope metrics on the plant-step head pressure from the injection.
static void scRcCost() {
  using ecu::Abort;
  struct C6 { std::string name; std::function<void(Sim&)> inj; std::function<void(SimConfig&)> cfg; double F; };
  auto bandHi = [](SimConfig& c) { c.ovp3_trip_Pa_abs += ovp3::kBandPa; c.ovp_trip_Pa_g += ovp::kBandPa; };
  const std::vector<C6> cases = {
      {"pintle_runaway_fw_ovp_off_hw_trip", [](Sim& s) { s.pintle_runaway_at = 3.0; s.fw_ovp_disabled = true; s.pintle_mon_disabled = true; }, nullptr, 300.0},
      {"pintle_runaway_fw_ovp_off_hw_trip_24C_Cd0p8_band_high", [](Sim& s) { s.pintle_runaway_at = 3.0; s.fw_ovp_disabled = true; s.pintle_mon_disabled = true; },
       [bandHi](SimConfig& c) { hot24Cd08(c); bandHi(c); }, 300.0},
      {"pintle_runaway_500N_fw_ovp_off_hw_trip_24C_Cd0p8_band_high", [](Sim& s) { s.pintle_runaway_at = 3.0; s.fw_ovp_disabled = true; s.pintle_mon_disabled = true; },
       [bandHi](SimConfig& c) { hot24Cd08(c); bandHi(c); }, 500.0},
      {"throat_blocked_70pct_fw_ovp_off_hw_trip", [](Sim& s) { s.eng.P.At_block_at = 3.0; s.eng.P.At_block_frac = 0.7; s.fw_ovp_disabled = true; }, nullptr, 300.0},
      {"throat_blocked_70pct_500N_fw_ovp_off_hw_trip_24C_Cd0p8_band_high", [](Sim& s) { s.eng.P.At_block_at = 3.0; s.eng.P.At_block_frac = 0.7; s.fw_ovp_disabled = true; },
       [bandHi](SimConfig& c) { hot24Cd08(c); bandHi(c); }, 500.0},
      {"throat_blocked_70pct_500N_24C_Cd0p8_fw_on", [](Sim& s) { s.eng.P.At_block_at = 3.0; s.eng.P.At_block_frac = 0.7; }, hot24Cd08, 500.0},
      {"pintle_runaway_500N_24C_Cd0p8_fw_on", [](Sim& s) { s.pintle_runaway_at = 3.0; }, hot24Cd08, 500.0},
  };
  const double taus[3] = {ovp3::kTau_s, ecu::cfg::kRideCmpTauNom_s, ecu::cfg::kRideCmpTauMax_s};
  const char* tn[3] = {"as_built_5p225ms", "ride_nom_12p825ms", "ride_max_13p552ms"};
  J j;
  j.k("id").v("sil_S6C_rc_cost_v2p11"); j.k("version").v("v2.11"); j.k("date").v("2026-10-20");
  j.k("scenario").v("S6C LEAD 216 (3): whole-burn cost of the FIXED comparator RC of the ride-through BOM variant. S6 pad first start (300 / 500 N, fault "
                    "at 3.0 s), hardware path alone (firmware over-pressure check off; runaway also with the stall monitor off) or racing the firmware, "
                    "at the as-built 5.225 ms, the ride nominal 12.825 ms and the ride tolerance maximum 13.552 ms. Plant-produced over-pressure (physical "
                    "decay through the MV-P poppet); LC-TB70 envelope on the plant-step head pressure from the injection. SIM, not physical approval.");
  std::string arr = "[";
  int n = 0;
  for (const C6& cc : cases) {
    for (int k = 0; k < 3; ++k) {
      SimConfig c = nominal(8101 + n);
      if (cc.cfg) cc.cfg(c);
      c.ovp3_tau = taus[k];
      Sim s(c);
      s.schedule = padSequence(1.40);
      const double F = cc.F;
      s.thrust_cmd = [F](double) { return F; };
      cc.inj(s);
      std::sort(s.schedule.begin(), s.schedule.end(), [](const StateCmd& a, const StateCmd& b) { return a.t < b.t; });
      s.schedule.push_back({4.5, Cmd::SHUTDOWN, 0});
      s.ch_from = 3.0;
      s.run(5.0);
      const auto& r = s.rec();
      int cause = 0; double t_ab = NAN;
      for (const Rec& x : r) if (x.abort && std::isnan(t_ab)) { cause = x.abort; t_ab = x.t; }
      const double t_armoff = firstTime(r, 3.0, [](const Rec& x) { return !x.arm_bus; });
      const double t_mvc = firstTime(r, 3.0, [](const Rec& x) { return x.mv < 0.03; });
      const Env e = envCheck(s, NAN);
      const bool bounding = k == 2 && (cc.name.find("500N") != std::string::npos);
      std::string trace;
      if (bounding || !e.inside) { trace = "S6C_" + cc.name + "__" + tn[k] + ".csv.gz"; writeTraceGz(s, OUT + "/" + trace); }
      char bb[1800];
      std::snprintf(bb, sizeof bb,
                    "%s{\"case\": \"%s\", \"tau\": \"%s\", \"comparator_tau_ms\": %.3f, \"cause\": \"%s\", \"inj_to_abort_ms\": %.1f, "
                    "\"inj_to_hw_comparator_trip_ms\": %.1f, \"inj_to_ARM_bus_off_ms\": %.1f, \"inj_to_MV_closed_ms\": %.1f, \"peak_head_bar_abs\": %.2f, "
                    "\"time_above_30_ms\": %.2f, \"time_above_45_ms\": %.2f, \"span_above_45_ms\": %.2f, \"time_above_58p1_ms\": %.2f, \"time_above_60_ms\": %.2f, "
                    "\"zone_max\": %d, \"inside_LC_TB70\": %s, \"reasons\": \"%s\", \"jfwd_rule_triggered\": %s, \"trace\": \"%s\"}",
                    n ? ", " : "", cc.name.c_str(), tn[k], taus[k] * 1e3, ecu::abortName(static_cast<Abort>(cause)), (t_ab - 3.0) * 1e3,
                    s.ovp_trip_t >= 0 ? (s.ovp_trip_t - 3.0) * 1e3 : NAN, (t_armoff - 3.0) * 1e3, (t_mvc - 3.0) * 1e3, s.env_pk / 1e5, s.ch_t30 * 1e3,
                    s.env_t45 * 1e3, s.env_t45a >= 0 ? (s.env_t45b - s.env_t45a) * 1e3 : 0.0, s.env_t581 * 1e3, s.env_t60 * 1e3, e.zone,
                    jb(e.inside).c_str(), e.why.c_str(), jb(e.jfwd).c_str(), trace.c_str());
      arr += bb;
      std::printf("S6C %-64s %-18s %-16s ab +%5.1f hw +%5.1f ms pk %6.2f t45 %5.1f ms z%d %s jfwd %d\n", cc.name.c_str(), tn[k],
                  ecu::abortName(static_cast<Abort>(cause)), (t_ab - 3.0) * 1e3, s.ovp_trip_t >= 0 ? (s.ovp_trip_t - 3.0) * 1e3 : NAN, s.env_pk / 1e5,
                  s.env_t45 * 1e3, e.zone, e.inside ? "IN" : "OUT", e.jfwd ? 1 : 0);
      std::fflush(stdout);
      ++n;
    }
  }
  j.k("cases").raw(arr + "]");
  writeFile(OUT + "/S6C_rc_cost.json", j.str());
}

// ------------------------------------------------------------------------------------------ v2.11 S10v211 cold rule (LEAD 216 (7))
// Pad first start (ARM 0.05, PREPRESS 0.80, IGNITE 1.40 s, 300 N) with the tank conditioned just above the 15 C bound: the coldest valid
// tank estimate (min of the wall DS18B20 readings and Tsat(P_tank), engine_ecu.cpp tankUpdate) is sampled every ms; DROP = its value at
// the ARM check minus its minimum over PREPRESS (the line fill draws tank mass: Tsat falls). Margin rule (config.h kTankColdArmMargin_K):
// ARM needs tmin >= 288.15 K + kTankColdArmMargin_K (0.42 K). Cases: T0 = 288.15 + m (m 0.20 ... 2.00 K) at the nominal fill and at 60 % fill; plus the SAFE EXIT
// case: the wall readings fall 0.6 K at 1.00 s (tank cooling in the ARM dwell, outside the margin by design) -> IGNITE refused TANK_COLD
// in PREPRESS -> back to ARMED on that tick, MV unlatched, valve closed, pintle seated. SIL plant (saturated tank, wall = bulk + bias):
// the wall-vs-bulk lag is NOT modelled (TO-VERIFY at the tank conditioning tests). Not physical approval.
static void scColdRule() {
  using namespace ecu::cfg;
  J j; j.k("id").v("sil_S10v211_cold_rule"); j.k("version").v("v2.11"); j.k("date").v("2026-10-21");
  j.k("scenario").v("pad first start ARM 0.05 / PREPRESS 0.80 / IGNITE 1.40 s, tank T0 = 288.15 K + m; tmin = min(wall DS18B20, Tsat(P_tank)) every ms; "
                    "drop = tmin at the ARM tick - min over PREPRESS; plus the safe-exit case (walls -0.6 K at 1.00 s)");
  j.k("arm_margin_K").v(kTankColdArmMargin_K); j.k("prepress_drop_K_config").v(kTankColdPrepressDrop_K); j.k("repeat_K_config").v(kTankColdRepeat_K);
  struct CC { std::string name; double m; double fill; bool cool; };
  std::vector<CC> cs;
  for (double fill : {1.0, 0.6})
    for (double m : {0.20, 0.30, 0.41, 0.42, 0.43, 0.60, 1.00, 2.00}) {   // v2.11 margin 0.42 K (pre-record grid 0.31 K +/- 0.01)
      char nm[80]; std::snprintf(nm, sizeof nm, "T0_15C_plus_%.2fK_fill%.0fpct", m, fill * 100.0); cs.push_back({nm, m, fill, false});
    }
  cs.push_back({"safe_exit_walls_minus0p6K_at_1p00s_T0_15C_plus_0.50K", 0.50, 1.0, true});
  std::string arr = "[";
  double drop_max = 0.0, est_lo = 1e9, est_hi = -1e9; int nfail = 0;
  for (size_t i = 0; i < cs.size(); ++i) {
    const CC& k = cs[i];
    SimConfig c = nominal(2201 + i); c.eng.T_tank0 = 288.15 + k.m;
    Sim s(c);
    if (k.fill < 1.0) { const double T0 = c.eng.T_tank0, mf = tab::k_tank_m * k.fill; s.hooks.push_back({0.0, [T0, mf](Sim& q) { q.eng.setTankState(T0, mf); }}); }
    if (k.cool) s.hooks.push_back({1.00, [](Sim& q) { q.ttank_wall_bias_K[0] = q.ttank_wall_bias_K[1] = -0.6; }});
    s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}};
    s.thrust_cmd = [](double) { return 300.0; };
    double t_arm_ok = NAN, tmin_arm = NAN, tmin_pp = 1e9, tmin_ign = NAN, t_pp = NAN, t_exit = NAN, t_unl = NAN, t_ign = NAN, ptank_arm = NAN, ptank_pp_min = 1e12;
    double tmin_cmd = NAN, tplant_cmd = NAN;   // v2.11 record fix: the ECU estimate the ARM check used (tankUpdate runs before the command) and the plant T
    int refused = 0, st_after = -1;
    bool in_pp = false;
    while (s.t < 1.80 - 1e-9) {
      s.run(s.t + 1e-3);
      const double tk = s.t - 1e-3;
      const State st = s.out.state;
      if (std::isnan(tmin_cmd) && tk >= 0.05 - 1e-9) { tmin_cmd = s.ecu.tankTminK(); tplant_cmd = s.eng.T_tank; }
      if (std::isnan(t_arm_ok) && st == State::ARMED) { t_arm_ok = tk; tmin_arm = s.ecu.tankTminK(); ptank_arm = s.eng.P_tank; }
      if (st == State::PREPRESS) {
        if (std::isnan(t_pp)) t_pp = tk;
        in_pp = true; tmin_pp = std::min(tmin_pp, static_cast<double>(s.ecu.tankTminK())); ptank_pp_min = std::min(ptank_pp_min, s.eng.P_tank);
      } else if (in_pp && std::isnan(t_exit) && st == State::ARMED) { t_exit = tk; st_after = static_cast<int>(st); }
      if (std::isnan(tmin_ign) && tk >= 1.40 - 1e-9) tmin_ign = s.ecu.tankTminK();
      if (std::isnan(t_ign) && st == State::IGNITION) t_ign = tk;
      if (std::isfinite(t_exit) && std::isnan(t_unl) && !s.out.mv_latch) t_unl = tk;
      if (s.out.cmd_refused == ecu::refuse::TANK_COLD) refused = 1;
    }
    const auto& r = s.rec();
    double ta; const int ab = firstAbortCause(r, &ta);
    const double drop = (std::isfinite(tmin_arm) && tmin_pp < 1e8) ? tmin_arm - tmin_pp : NAN;
    if (!k.cool && std::isfinite(drop)) drop_max = std::max(drop_max, drop);
    // expectations: m below the margin -> ARM refused TANK_COLD; at or above it -> IGNITION entered, no refusal; safe exit -> refused, ARMED,
    // MV unlatched on the exit tick (the plant valve closes on its spring), no abort.
    // v2.11 record fix (2026-10-21): grid points within kBand of the margin are INDETERMINATE - the ECU decides on its own estimate
    // min(wall, Tsat(5 Hz-filtered P_tank)), which differs from the plant temperature by the estimate error (first record: the 0.43 K /
    // 100 % point was refused); there the outcome is checked against the ECU's own estimate on the ARM tick instead
    const double kBand = 0.02;
    const bool indet = !k.cool && std::fabs(k.m - kTankColdArmMargin_K) < kBand - 1e-9;
    const bool arm_should = k.m + 1e-6 >= kTankColdArmMargin_K;
    const bool arm_by_est = std::isfinite(tmin_cmd) && tmin_cmd >= kTankIgnMin_K + kTankColdArmMargin_K;
    bool pass;
    if (k.cool) pass = refused && std::isfinite(t_exit) && std::isnan(t_ign) && ab == 0 && std::isfinite(t_unl) && t_unl - t_exit <= 0.0011 && s.ecu.prepressExits() == 1;
    else if (indet) pass = arm_by_est ? (ab == 0 && !refused && std::isfinite(t_ign)) : (ab == (int)ecu::Abort::TANK_COLD && std::isnan(t_ign));
    else if (!arm_should) pass = ab == (int)ecu::Abort::TANK_COLD && std::isnan(t_ign);
    else pass = ab == 0 && !refused && std::isfinite(t_ign);
    if (!k.cool && std::isfinite(tmin_cmd)) { est_lo = std::min(est_lo, tmin_cmd - tplant_cmd); est_hi = std::max(est_hi, tmin_cmd - tplant_cmd); }
    nfail += !pass;
    const Rec* xe = std::isfinite(t_exit) ? recAt(r, t_exit + 0.20) : nullptr;
    char b[1800];
    std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"T0_K\": %.3f, \"fill_frac\": %.2f, \"first_abort\": \"%s\", \"t_abort_s\": %.4f, \"armed_s\": %.4f, "
                  "\"tmin_at_arm_K\": %.4f, \"tmin_min_prepress_K\": %.4f, \"tmin_at_ignite_cmd_K\": %.4f, \"prepress_drop_K\": %.4f, \"P_tank_at_arm_bar\": %.4f, "
                  "\"P_tank_min_prepress_bar\": %.4f, \"ignite_refused_TANK_COLD\": %d, \"ignition_entry_s\": %.4f, \"prepress_exit_s\": %.4f, \"mv_unlatched_s\": %.4f, "
                  "\"prepress_exits\": %d, \"mv_pos_exit_plus_0p2s\": %.3f, \"pintle_mm_exit_plus_0p2s\": %.4f, \"final_state\": \"%s\", \"expect_arm\": %s, "
                  "\"tmin_ecu_at_arm_cmd_K\": %.4f, \"T_tank_plant_at_arm_cmd_K\": %.4f, \"estimate_minus_plant_K\": %.4f, \"pass\": %s}",
                  i ? ",\n" : "", k.name.c_str(), c.eng.T_tank0, k.fill, ecu::abortName(static_cast<ecu::Abort>(ab)), ta, t_arm_ok, tmin_arm, tmin_pp < 1e8 ? tmin_pp : NAN,
                  tmin_ign, drop, ptank_arm / 1e5, ptank_pp_min < 1e11 ? ptank_pp_min / 1e5 : NAN, refused, t_ign, t_exit, t_unl, s.ecu.prepressExits(),
                  xe ? xe->mv : NAN, xe ? xe->x * 1e3 : NAN, ecu::stateName(s.ecu.state()), indet ? "\"either (inside the estimate band)\"" : jb(arm_should).c_str(),
                  tmin_cmd, tplant_cmd, tmin_cmd - tplant_cmd, jb(pass).c_str());
    arr += b;
    std::printf("S10v211 cold %-52s %s%s abort %-10s armed %.3f tmin ARM %.4f PP min %.4f drop %.4f K refused %d ign %.3f exit %.3f unl %.3f est-plant %+.4f K\n",
                k.name.c_str(), pass ? "PASS" : "FAIL", indet ? " (band)" : "", ecu::abortName(static_cast<ecu::Abort>(ab)), t_arm_ok, tmin_arm,
                tmin_pp < 1e8 ? tmin_pp : NAN, drop, refused, t_ign, t_exit, t_unl, tmin_cmd - tplant_cmd);
    (void)st_after;
  }
  j.k("cases").raw(arr + "\n]");
  j.k("prepress_drop_max_K").v(drop_max);
  j.k("margin_check").v(std::string("1.5 x drop_max + repeat = ") + std::to_string(1.5 * drop_max + kTankColdRepeat_K) + " K vs kTankColdArmMargin_K " +
                        std::to_string(kTankColdArmMargin_K) + " K: " + ((1.5 * drop_max + kTankColdRepeat_K <= kTankColdArmMargin_K + 1e-6) ? "covered" : "NOT covered"));
  j.k("indeterminate_band_K").v(0.02);
  j.k("estimate_minus_plant_K_range").raw("[" + std::to_string(est_lo) + ", " + std::to_string(est_hi) + "]");
  j.k("fail").v(nfail);
  writeFile(OUT + "/S10v211_cold_rule.json", j.str());
  std::printf("S10v211 cold rule: drop max %.4f K, 1.5 x drop + repeat %.4f K vs margin %.2f K, ECU estimate - plant at the ARM tick %.4f .. %.4f K, "
              "%d not as expected\n", drop_max, 1.5 * drop_max + kTankColdRepeat_K, kTankColdArmMargin_K, est_lo, est_hi, nfail);
}

}  // namespace v211
