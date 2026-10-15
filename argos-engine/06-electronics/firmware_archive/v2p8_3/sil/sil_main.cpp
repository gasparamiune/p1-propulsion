// ARGOS engine SIL - scenarios (v2.8, 2026-10-13: LEAD decisions - direct relight on a primed segment, windows from the lift (flight
// 0.65 s, stand R1-R4), torch gate 0.16 s, MV-P poppet plant (S6 throat-block comparison with the v2.7 ball valve), over-thrust, mode
// strap, case 448.15 / 433.15 K, bay inhibit, TLM_RELIGHT; S10 rewritten (results/sil_v2p8_draft); v2.7, 2026-10-13: Combustion review fold-in - torch-flame gate, C7 relight check, relight lockout,
// seat-confirmed shutdown, LTC4365 rail disconnect, stand-only rules, S10 set, unignited-N2O inventory per start, torch N2O-alone
// check; v2.6, 2026-10-12: stall-monitor clearance, jam events, relight timing with the MV closed in the coast; v2, 2026-10-11).
// v2.8 final (2026-10-13, COMB v2.4 / GNC v3 option (c) / MECH option A and seat-leak drain): S6 hard-start cases are late lights inside W
// (no abort after the RUN-entry reference fix; the v2.8 draft false FLAMEOUT stays in results/sil_v2p8_draft), hot corner 24 C (tank
// interlock), TANK_HOT ARM cases; S10 TLM VALID/UNKNOWN semantics, seat-timeout cut-off, CLOSED-switch failure, post-abort stand start,
// tank interlock; new S11 fault path vs segment volume (sil fault). Results: results/sil_v2p8_final.
// v2.8.1 (2026-10-13, LEAD stand fallback (b), over-thrust adopted): stand no-light closure cases, over-thrust frame-rule cases, FC
// estimate tau 20 ms. Results: results/sil_v2p8_1. v2.8.2 (2026-10-13, GNC review REV-GNC-1 RG-08): S10 coast pintle-anomaly cases
// (encoder dropout -> UNKNOWN, needle read 0.12 mm off the seat -> UNPRIMED, late flip after the last frame EVIDENCE) and the MECO
// encoder-loss case re-expected (prep path). Results: results/sil_v2p8_2.
// v2.8.3 (2026-10-13, gnc.json v3 conformance, REV-GNC-1 RG-13): TvcShaper runs the gnc.json v3 rate- and acceleration-limited
// tracker (100 deg/s, 2000 deg/s2) ahead of the low-pass; the S7 per-axis cases, vector checks and time history fly it, the S7
// actuator-capability runs keep the actuator-only setting (no ECU rate limit, tracker off). Results: results/sil_v2p8_3.
// Runs the unchanged ECU core (src/core) against the plant models.
// LIMITATION (v2.6, unchanged in v2.7): the PintleDrive plant is still the v2.5 mechanism (compression spring on the needle, rigid
// servo-crank coupling, free back-drive of the unpowered HV69); the in-line dog + spiral spring + guide friction physics is in
// calc/pintle_dynamics_v2.py / _v3.py (which derive the monitor thresholds). v2.7 torch pressure and C7 vapour models are ESTIMATES
// (plant.h). The SIL is a firmware/sequencing check, not the pintle dynamics or ignition reference.
// Usage: sil <scenario|all> <out_dir> [mc_runs]
//   scenarios: mission steps deep hover aborts tvc priming pcx fold mc | mcone (sil mcone <out_dir> <run index>: replay one MC case)
//   | fault (v2.8 final S11: sil fault <out_dir> label=cm3,label=cm3,...; run by calc/fault_path_v1.py, not part of 'all')
// Output: CSV time histories + summary JSON per scenario in out_dir. A SIL pass is NOT hardware validation.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>
#include "sim.h"

using namespace sil;
using ecu::Cmd;
using ecu::State;

static std::string OUT = "../results/sil";
// v2.6 stall-monitor clearance across the no-fault scenarios (S1-S5): longest no-progress interval and jam events seen
static double G_NOPROG = 0; static int G_JAM_NOFAULT = 0, G_RUNS = 0;
static void noteMon(const sil::Sim& s) { G_NOPROG = std::max(G_NOPROG, s.noprog_max); G_JAM_NOFAULT += s.jam_events; ++G_RUNS; }
static constexpr double D2R = M_PI / 180.0, R2D = 180.0 / M_PI;

// ------------------------------------------------------------------------------------------ JSON helper
struct J {
  std::ostringstream s; bool first = true;
  J() { s << "{"; }
  J& k(const std::string& key) { s << (first ? "" : ",") << "\n \"" << key << "\": "; first = false; return *this; }
  J& v(double x) { if (std::isfinite(x)) s << x; else s << "null"; return *this; }
  J& v(const std::string& x) { s << "\"" << x << "\""; return *this; }
  J& raw(const std::string& x) { s << x; return *this; }
  std::string str() { return s.str() + "\n}"; }
};
// JSON has no NaN/Inf: replace bare nan/-nan/inf tokens (printf output of undefined metrics) by null
static std::string jsonSanitize(std::string s) {
  auto isid = [](char c) { return std::isalnum(static_cast<unsigned char>(c)) || c == '_' || c == '"' || c == '.'; };
  for (const char* tok : {"-nan", "nan", "-inf", "inf"}) {
    const std::string t(tok);
    for (size_t p = s.find(t); p != std::string::npos; p = s.find(t, p + 1)) {
      const bool l = p == 0 || !isid(s[p - 1]) || (t[0] != '-' && s[p - 1] == '-');
      const bool r = p + t.size() >= s.size() || !isid(s[p + t.size()]);
      if (l && r) { s.replace(p, t.size(), "null"); }
    }
  }
  return s;
}
static void writeFile(const std::string& fn, const std::string& txt) { std::ofstream f(fn); f << jsonSanitize(txt) << "\n"; }

// ------------------------------------------------------------------------------------------ config
static SimConfig nominal(uint32_t seed = 1) {
  SimConfig c;
  c.seed = seed;
  return c;
}
static std::vector<StateCmd> padSequence(double t_ign) {
  return {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {t_ign, Cmd::IGNITE, 0}};
}

// ------------------------------------------------------------------------------------------ metrics
struct StepM { double t10 = NAN, t90 = NAN, rise = NAN, cmd90 = NAN, overshoot = NAN, settle = NAN, ss_err = NAN, pp = NAN, mean = NAN; };
static StepM stepMetrics(const std::vector<Rec>& r, double t0, double F0, double F1, double t_end, double win = 0.4) {
  StepM m;
  const double dF = F1 - F0, sgn = dF > 0 ? 1 : -1;
  double peak = -1e9;
  double last_out = t0;
  const double band = std::max(2.5, 0.05 * std::fabs(dF));
  for (const Rec& x : r) {
    if (x.t < t0 || x.t > t_end) continue;
    const double p = (x.F - F0) / dF;
    if (std::isnan(m.t10) && p >= 0.1) m.t10 = x.t;
    if (std::isnan(m.t90) && p >= 0.9) m.t90 = x.t;
    peak = std::max(peak, sgn * (x.F - F1));
    if (std::fabs(x.F - F1) > band) last_out = x.t;
  }
  m.rise = m.t90 - m.t10; m.cmd90 = m.t90 - t0;
  m.overshoot = 100.0 * std::max(0.0, peak) / std::fabs(dF);
  m.settle = last_out - t0;
  double s = 0, mn = 1e9, mx = -1e9; int n = 0;
  for (const Rec& x : r) if (x.t >= t_end - win && x.t <= t_end) { s += x.F; mn = std::min(mn, x.F); mx = std::max(mx, x.F); ++n; }
  m.mean = n ? s / n : NAN; m.ss_err = m.mean - F1; m.pp = mx - mn;
  return m;
}
static std::string stepJson(const StepM& m) {
  char b[400];
  std::snprintf(b, sizeof b, "{\"t10_s\": %.4f, \"t90_s\": %.4f, \"rise_10_90_s\": %.4f, \"cmd_to_90_s\": %.4f, \"overshoot_pct\": %.2f, "
                "\"settle_s\": %.3f, \"ss_err_N\": %.3f, \"pp_N\": %.3f, \"mean_N\": %.3f}",
                m.t10, m.t90, m.rise, m.cmd90, m.overshoot, m.settle, m.ss_err, m.pp, m.mean);
  std::string s(b);
  for (auto p = s.find("nan"); p != std::string::npos; p = s.find("nan")) s.replace(p, 3, "null");
  return s;
}
static double firstTime(const std::vector<Rec>& r, double t0, const std::function<bool(const Rec&)>& c) {
  for (const Rec& x : r) if (x.t >= t0 && c(x)) return x.t;
  return NAN;
}

// ------------------------------------------------------------------------------------------ S1 mission
static void scMission() {
  Sim s(nominal(11));
  s.schedule = padSequence(1.40);
  s.schedule.push_back({4.00, Cmd::SHUTDOWN, 0});
  s.schedule.push_back({10.00, Cmd::RELIGHT, 0});
  s.schedule.push_back({16.00, Cmd::SHUTDOWN, 0});
  s.schedule.push_back({18.00, Cmd::RELIGHT, 0});
  s.schedule.push_back({19.50, Cmd::SHUTDOWN, 0});
  s.schedule.push_back({20.50, Cmd::DISARM, 0});
  s.thrust_cmd = [](double t) {
    if (t < 3.0) return 450.0;
    if (t < 3.7) return 500.0;
    if (t < 10.0) return 375.0;   // v2.6: pre-MECO throttle-down to 75 % (LEAD: required, GNC owns the timing; ENG-05 from 100 % fails)
    if (t < 11.5) return 150.0;
    if (t < 12.5) return 150.0 - 70.0 * (t - 11.5);
    if (t < 13.0) return 80.0;
    if (t < 14.0) return 62.5;
    if (t < 15.0) return 100.0;
    if (t < 18.0) return 120.0;
    return 250.0;
  };
  s.gimbal_cmd = [](double t, float* g) {
    g[0] = g[1] = 0;
    if (t > 2.0 && t < 2.5) g[0] = 3 * D2R;
    if (t > 2.5 && t < 3.0) g[0] = -3 * D2R;
    if (t > 3.0 && t < 3.5) g[1] = 5 * D2R;
    if (t > 11.0 && t < 15.5) g[0] = static_cast<float>(0.5 * D2R * std::sin(2 * M_PI * 2.0 * (t - 11.0)));
  };
  // roll couples (GNC v1 provision): CW pulse in coast 6.00-6.30 s, CCW pulse in the landing burn 12.00-12.20 s
  s.roll_cmd = [](double t) { return static_cast<uint8_t>((t >= 6.0 && t < 6.3) ? 1 : (t >= 12.0 && t < 12.2) ? 2 : 0); };
  s.run(21.5);
  s.writeCsv(OUT + "/S1_mission.csv");
  const auto& r = s.rec();
  J j;
  j.k("scenario").v("S1 mission: pad start (ARM, PREPRESS, IGNITE), ascent 450-500 N, pre-MECO throttle-down to 375 N at 3.7 s, MECO 4.0 s, "
                     "coast with the MV CLOSED (v2.6 LEAD rule b), relights at T_fire (v2.8: primed segment -> NC valve + torch at E0, "
                     "opener ramp >= 0.3 s, lift at E1) to the landing profile incl. 62.5 N, third start");
  noteMon(s);
  {
    char b[200]; std::snprintf(b, sizeof b, "{\"jam_events\": %d, \"noprog_max_s\": %.4f, \"time_path_s\": %.3f}", s.jam_events, s.noprog_max, ecu::cfg::kPintleStallTime_s);
    j.k("pintle_monitor").raw(b);
  }
  {   // v2.8 relight timing for GNC (LEAD 2026-10-13: RELIGHT at T_fire; primed segment -> IGNITION at once = E0 with the NC valve
      // and the torch; lift at E1 = torch confirmation; E2 = Pc confirmation). TLM_RELIGHT as decoded by the FC just before the command.
    std::string rl = "[";
    const double rcmd[2] = {10.00, 18.00};
    for (int k = 0; k < 2; ++k) {
      const double tc = rcmd[k];
      const double t_pre = firstTime(r, tc, [](const Rec& x) { return x.state == (int)State::PREPRESS; });
      const double t_ign = firstTime(r, tc, [](const Rec& x) { return x.state == (int)State::IGNITION; });
      const double t_e1r = firstTime(r, t_ign, [](const Rec& x) { return x.state == (int)State::IGNITION && x.ign_lift_t >= 0.0; });
      const Rec* xe1 = std::isfinite(t_e1r) ? &*std::find_if(r.begin(), r.end(), [&](const Rec& x) { return x.t >= t_e1r; }) : nullptr;
      const double t_e1 = xe1 ? t_ign + xe1->ign_lift_t : NAN;
      const double t_run = firstTime(r, tc, [](const Rec& x) { return x.state == (int)State::RUN; });
      const double t_crack = firstTime(r, tc, [](const Rec& x) { return x.mv >= 0.02; });
      const double t_full = firstTime(r, tc, [](const Rec& x) { return x.mv >= 0.98; });
      const ecu::can::TlmRelight* tm = nullptr;
      for (const auto& f : s.tlmr) if (f.t < tc - 1e-9) tm = &f.m;
      const double worst = tm ? 1e-3 * tm->worst_ms : NAN;
      char b[900];
      std::snprintf(b, sizeof b, "%s{\"relight_cmd_t\": %.2f, \"tlm_primed\": %d, \"tlm_valid\": %d, \"tlm_ready\": %d, \"tlm_worst_s\": %.3f, "
                    "\"direct\": %s, \"to_PREPRESS_s\": %.4f, \"to_E0_IGNITION_s\": %.4f, \"E0_to_E1_lift_s\": %.4f, \"to_MV_crack_s\": %.4f, "
                    "\"to_MV_full_s\": %.4f, \"to_E2_RUN_s\": %.4f, \"within_published_worst\": %s}",
                    k ? ", " : "", tc, tm ? (tm->flags & ecu::tlmr::PRIMED ? 1 : 0) : -1, tm ? (tm->flags & ecu::tlmr::VALID ? 1 : 0) : -1,
                    tm ? (tm->flags & ecu::tlmr::READY ? 1 : 0) : -1, worst, std::isfinite(t_pre) && t_pre < t_ign ? "false" : "true",
                    t_pre < t_ign ? t_pre - tc : NAN, t_ign - tc, t_e1 - t_ign, t_crack - tc, t_full - tc, t_run - tc,
                    (std::isfinite(t_run) && t_run - tc <= worst + 1e-9) ? "true" : "false");
      rl += b;
    }
    rl += "]";
    j.k("relight_timing").raw(rl);
    // v2.8 worst-case relight sequence from the firmware constants (DERIVED from config.h): valve command -> Pc-confirm deadline.
    // Primed segment (direct): torch gate + W; gas in the segment: + bleed settle + opener ramp + hold, assuming the feed shows primed
    // by the end of the hold; the PREPRESS bound (feed primed only at the second timeout) is reported too. Flight planning value =
    // the primed value (LEAD 2026-10-13; the v2.7 '0.6 s + sequence' rule is withdrawn); the FC reads TLM_RELIGHT for the path.
    using namespace ecu::cfg;
    const double prep = kBleedSettle_s + kMvOpenRampSlow_s + kMvCockHold_s;
    const double fl_p = kTorchGate_s + kIgnWindowRelightLong_s, fl_u = prep + fl_p;
    const double bound = kBleedSettle_s + kMvOpenRampSlow_s + 2.0 * kPrepressTimeout_s + fl_p;
    char b[900];
    std::snprintf(b, sizeof b, "{\"torch_gate_s\": %.3f, \"W_flight_relight_s\": %.3f, \"W_stand_R2_s\": %.3f, \"W_stand_R1_s\": %.3f, "
                  "\"bleed_settle_s\": %.3f, \"mv_ramp_s\": %.3f, \"cock_hold_s\": %.3f, \"flight_primed_s\": %.3f, \"flight_unprimed_s\": %.3f, "
                  "\"flight_prepress_fail_bound_s\": %.3f, \"stand_R2_primed_s\": %.3f, \"stand_R2_unprimed_s\": %.3f, \"gnc_planning_value_s\": %.3f, "
                  "\"basis\": \"DERIVED from config.h (v2.8.1); planning value = primed flight value (LEAD 2026-10-13); unprimed bound assumes the feed "
                  "primes by the end of the hold, else up to the PREPRESS bound then PREPRESS_FAIL\"}",
                  kTorchGate_s, kIgnWindowRelightLong_s, kIgnWindowRelightStand_s, kIgnWindowFirstStand_s, kBleedSettle_s, kMvOpenRampSlow_s,
                  kMvCockHold_s, fl_p, fl_u, bound, kTorchGate_s + kIgnWindowRelightStand_s, prep + kTorchGate_s + kIgnWindowRelightStand_s, fl_p);
    j.k("relight_sequence_bound").raw(b);
  }
  const double ign[3] = {1.40, 10.00, 18.00}, thr[3] = {450.0, 150.0, 250.0};
  std::string starts = "[";
  for (int k = 0; k < 3; ++k) {
    const double t90 = firstTime(r, ign[k], [&](const Rec& x) { return x.F >= 0.9 * thr[k]; });
    const double tlit = firstTime(r, ign[k], [](const Rec& x) { return x.ignited != 0; });
    char b[200]; std::snprintf(b, sizeof b, "%s{\"cmd_t\": %.3f, \"cmd_to_lit_s\": %.4f, \"cmd_to_90pct_thrust_s\": %.4f}", k ? ", " : "", ign[k], tlit - ign[k], t90 - ign[k]);
    starts += b;
  }
  starts += "]";
  j.k("starts").raw(starts);
  const double sd[3] = {4.0, 16.0, 19.5};
  std::string sds = "[";
  for (int k = 0; k < 3; ++k) {
    double F0 = 0; for (const Rec& x : r) if (x.t < sd[k]) F0 = x.F;
    const double t10 = firstTime(r, sd[k], [&](const Rec& x) { return x.F < 0.1 * F0; });
    const double t10max = firstTime(r, sd[k], [&](const Rec& x) { return x.F < 50.0; });
    char b[200]; std::snprintf(b, sizeof b, "%s{\"cmd_t\": %.2f, \"F_before_N\": %.1f, \"to_10pct_of_F_s\": %.4f, \"to_below_50N_s\": %.4f}", k ? ", " : "", sd[k], F0, t10 - sd[k], t10max - sd[k]);
    sds += b;
  }
  sds += "]";
  j.k("shutdowns").raw(sds);
  int aborts = 0; for (const Rec& x : r) if (x.abort) { aborts = x.abort; break; }
  j.k("abort_cause_seen").v(aborts);
  {   // v2.7: unignited N2O admitted through the pintle per start (IGNITION entry -> main light), torch N2O-alone time
    std::string ox = "[";
    for (size_t k = 0; k < s.ox_unlit_starts.size(); ++k) { char q[40]; std::snprintf(q, sizeof q, "%s%.5f", k ? ", " : "", s.ox_unlit_starts[k]); ox += q; }
    ox += "]";
    j.k("ox_unlit_per_start_kg").raw(ox);
    j.k("ox_unlit_total_kg").v(s.ox_unlit_total);
    j.k("n2o_alone_ms").v(static_cast<double>(s.n2o_alone_ms));
  }
  j.k("final_state").v(r.back().state);
  j.k("ox_used_kg").v(s.eng.ox_used); j.k("fuel_used_kg").v(s.eng.fuel_used); j.k("port_D_end_m").v(s.eng.Dport);
  j.k("vbat_min_V").v(std::min_element(r.begin(), r.end(), [](const Rec& a, const Rec& b) { return a.vbat < b.vbat; })->vbat);
  j.k("i_peak_A").v(std::max_element(r.begin(), r.end(), [](const Rec& a, const Rec& b) { return a.i_tot < b.i_tot; })->i_tot);
  double pcmax = 0; for (const Rec& x : r) pcmax = std::max(pcmax, x.Pc);
  j.k("Pc_max_abs_Pa").v(pcmax);
  {  // roll valve timing: on-time per pulse and turn-off delay after the last CMD_AUX frame (dead-man)
    double on4 = 0, on5 = 0, off4 = NAN, off5 = NAN;
    for (const Rec& x : r) { on4 += x.sol4 * 1e-3; on5 += x.sol5 * 1e-3; }
    for (size_t i = 1; i < r.size(); ++i) {
      if (r[i - 1].sol4 && !r[i].sol4 && std::isnan(off4)) off4 = r[i].t;
      if (r[i - 1].sol5 && !r[i].sol5 && std::isnan(off5)) off5 = r[i].t;
    }
    char b[300]; std::snprintf(b, sizeof b, "{\"cw_on_s\": %.3f, \"cw_off_at_s\": %.3f, \"ccw_on_s\": %.3f, \"ccw_off_at_s\": %.3f, \"note\": \"commands end at 6.30/12.20 s; FC sends CMD_AUX at 100 Hz incl. zeros; dead-man 50 ms if frames stop\"}", on4, off4, on5, off5);
    j.k("roll_valves").raw(b);
  }
  writeFile(OUT + "/S1_mission.json", j.str());
  std::printf("S1 mission done: %s\n", j.str().c_str());
}

// ------------------------------------------------------------------------------------------ S2 throttle steps
static StepM runStep(double F0, double F1, const SimConfig& c, const std::string& csv, double t_step = 3.4, double hold = 1.6) {
  Sim s(c);
  s.schedule = padSequence(1.40);
  s.schedule.push_back({t_step + hold, Cmd::SHUTDOWN, 0});
  s.thrust_cmd = [=](double t) { return t < t_step ? F0 : F1; };
  s.run(t_step + hold + 0.3);
  noteMon(s);
  if (!csv.empty()) s.writeCsv(csv);
  return stepMetrics(s.rec(), t_step, F0, F1, t_step + hold - 0.05);
}
static void scSteps() {
  const std::vector<std::pair<double, double>> steps = {{100, 500}, {500, 100}, {62.5, 500}, {500, 62.5}, {250, 375}, {375, 250}, {100, 150}, {62.5, 100}, {100, 62.5}};
  J j;
  j.k("scenario").v("S2 throttle steps (ENG-03: 10-90 % <= 150 ms, target 100 ms); thrust = plant (true) thrust");
  std::string arr = "[";
  for (size_t i = 0; i < steps.size(); ++i) {
    char fn[128]; std::snprintf(fn, sizeof fn, "%s/S2_step_%g_to_%g.csv", OUT.c_str(), steps[i].first, steps[i].second);
    const StepM m = runStep(steps[i].first, steps[i].second, nominal(21 + i), fn);
    char b[64]; std::snprintf(b, sizeof b, "%s{\"from_N\": %g, \"to_N\": %g, \"m\": ", i ? ", " : "", steps[i].first, steps[i].second);
    arr += b + stepJson(m) + "}";
    std::printf("S2 %6.1f -> %6.1f N: rise %.1f ms, cmd->90 %.1f ms, overshoot %.1f %%, settle %.0f ms, ss err %.2f N, pp %.2f N\n",
                steps[i].first, steps[i].second, m.rise * 1e3, m.cmd90 * 1e3, m.overshoot, m.settle * 1e3, m.ss_err, m.pp);
  }
  arr += "]";
  j.k("steps").raw(arr);
  // sensitivity: weak battery, slow fuel lag 0.5 s, long combustion delay 10 ms, worse servo deadband/backlash
  std::string sens = "[";
  struct V { const char* name; std::function<void(SimConfig&)> f; };
  // weak battery: rests at 8.15 V (just above the v2.2 8.1 V ARM permit) with an aged-pack 0.08 ohm source resistance,
  // so the servo bus sags to ~7.2-7.5 V under actuator load (the 7.4 V TVC margin point of first_pass_v1)
  std::vector<V> vs = {{"weak battery 8.15 V, 0.08 ohm", [](SimConfig& c) { c.vbat0 = 8.15; c.R_batt = 0.08; }},
                       {"tau_f fixed 0.5 s", [](SimConfig& c) { c.eng.tau_f_fixed = 0.5; }},
                       {"comb delay 10 ms", [](SimConfig& c) { c.eng.comb_delay = 0.010; }},
                       {"deadband 3 us, backlash 0.5 deg", [](SimConfig& c) { c.sv_pintle.deadband_us = 3.0; c.sv_pintle.backlash_rad = 0.5 * D2R; }}};
  for (size_t i = 0; i < vs.size(); ++i) {
    SimConfig c = nominal(31 + i); vs[i].f(c);
    const StepM up = runStep(100, 500, c, "");
    const StepM dn = runStep(500, 100, c, "");
    sens += std::string(i ? ", " : "") + "{\"case\": \"" + vs[i].name + "\", \"up_100_500\": " + stepJson(up) + ", \"down_500_100\": " + stepJson(dn) + "}";
    std::printf("S2 sens %-32s up rise %.1f ms ovs %.1f %% | down rise %.1f ms ovs %.1f %%\n", vs[i].name, up.rise * 1e3, up.overshoot, dn.rise * 1e3, dn.overshoot);
  }
  sens += "]";
  j.k("sensitivity").raw(sens);
  writeFile(OUT + "/S2_steps.json", j.str());
}

// ------------------------------------------------------------------------------------------ S3 deep-end resolution
struct DeepWorst { double err = NAN, pp = NAN, step = NAN, us_pp = NAN; int refused = 0; };
static std::string deepRun(const SimConfig& c, const std::string& tag, const std::string& prefix = "S3_deep_",
                           DeepWorst* w = nullptr, const std::function<void(Sim&)>& inject = nullptr) {
  Sim s(c);
  s.schedule = padSequence(1.40);
  std::vector<std::pair<double, double>> prof;   // (t_start, F)
  double t = 3.2, F = 62.5;
  prof.push_back({0.0, F});
  const double dwell = 0.8;
  auto add = [&](double dF, int n) { for (int i = 0; i < n; ++i) { F += dF; prof.push_back({t, F}); t += dwell; } };
  t += dwell;   // settle at 62.5
  add(+2.5, 4); add(+5.0, 4); add(+10.0, 2); add(-10.0, 2); add(-5.0, 4); add(-2.5, 4);
  const double t_end = t;
  s.schedule.push_back({t_end, Cmd::SHUTDOWN, 0});
  s.thrust_cmd = [prof](double tt) { double f = prof[0].second; for (auto& p : prof) if (tt >= p.first) f = p.second; return f; };
  if (inject) {
    inject(s);
    std::stable_sort(s.schedule.begin(), s.schedule.end(), [](const StateCmd& a, const StateCmd& b) { return a.t < b.t; });
  }
  s.run(t_end + 0.3);
  noteMon(s);
  s.writeCsv(OUT + "/" + prefix + tag + ".csv");
  const auto& r = s.rec();
  std::string arr = "[";
  double worst_err = 0, worst_pp = 0, worst_step_err = 0, worst_us_pp = 0;
  double prev_mean = NAN;
  for (size_t i = 1; i < prof.size(); ++i) {
    const double t0 = prof[i].first, t1 = (i + 1 < prof.size()) ? prof[i + 1].first : t_end;
    double sm = 0, mn = 1e9, mx = -1e9, se = 0; int n = 0;
    double us_mn = 1e9, us_mx = -1e9;
    for (const Rec& x : r) if (x.t >= t1 - 0.4 && x.t < t1) { sm += x.F; se += x.F_est; mn = std::min(mn, x.F); mx = std::max(mx, x.F); us_mn = std::min(us_mn, x.us_pintle); us_mx = std::max(us_mx, x.us_pintle); ++n; }
    const double mean = sm / n;
    double prev = NAN;
    if (i == 1) { double s2 = 0; int n2 = 0; for (const Rec& x : r) if (x.t >= t0 - 0.4 && x.t < t0) { s2 += x.F; ++n2; } prev = s2 / n2; prev_mean = prev; }
    else prev = prev_mean;
    const double dcmd = prof[i].second - prof[i - 1].second, dach = mean - prev;
    worst_err = std::max(worst_err, std::fabs(mean - prof[i].second));
    worst_pp = std::max(worst_pp, mx - mn);
    worst_step_err = std::max(worst_step_err, std::fabs(dach - dcmd));
    worst_us_pp = std::max(worst_us_pp, us_mx - us_mn);
    char b[300];
    std::snprintf(b, sizeof b, "%s{\"t\": %.2f, \"F_cmd\": %.2f, \"dF_cmd\": %.2f, \"F_mean\": %.3f, \"dF_achieved\": %.3f, \"err_N\": %.3f, \"pp_N\": %.3f, \"us_pp\": %.3f}",
                  i > 1 ? ", " : "", t0, prof[i].second, dcmd, mean, dach, mean - prof[i].second, mx - mn, us_mx - us_mn);
    arr += b;
    prev_mean = mean;
  }
  arr += "]";
  char b[300];   // header only: the step array can be longer than any fixed buffer
  std::snprintf(b, sizeof b, "{\"case\": \"%s\", \"worst_abs_err_N\": %.3f, \"worst_pp_N\": %.3f, \"worst_step_error_N\": %.3f, \"steps\": ",
                tag.c_str(), worst_err, worst_pp, worst_step_err);
  std::printf("%s%-10s worst |err| %.2f N, worst p-p %.2f N, worst step error %.2f N, worst pintle p-p %.2f us\n", prefix.c_str(),
              tag.c_str(), worst_err, worst_pp, worst_step_err, worst_us_pp);
  if (w) { w->err = worst_err; w->pp = worst_pp; w->step = worst_step_err; w->us_pp = worst_us_pp; w->refused = s.ecu.ignitionRefused(); }
  return std::string(b) + arr + "}";
}
static void scDeep() {
  J j;
  j.k("scenario").v("S3 deep-end resolution 62.5-112.5 N: staircase of 2.5/5/10 N steps (0.5/1/2 % of Fmax), 0.8 s dwell; stats over last 0.4 s of each step");
  // analytic actuator resolution at the deep end (linkage x map gain)
  std::string an = "[";
  sil::EngineParams ep; sil::EnginePlant e(ep);
  const double Fpts[3] = {62.5, 75.0, 100.0};
  for (int i = 0; i < 3; ++i) {
    const double pc = ecu::thrust::pcAbsFromThrust(static_cast<float>(Fpts[i]), 101325.0f);
    float g; const float x = ecu::ValveMap::lift(static_cast<float>(pc), 5.0525e6f, &g);
    const double dxdus = ecu::linkage::dLiftDCrank(x) * (D2R / 10.0);   // 10 us/deg
    const double dFdPc = ecu::eng::kCfVacEff * ecu::eng::kAt_m2;
    char b[400];
    std::snprintf(b, sizeof b, "%s{\"F_N\": %.1f, \"Pc_abs_Pa\": %.0f, \"lift_m\": %.4e, \"gain_Pa_per_m\": %.4e, \"lift_per_us_m\": %.4e, "
                  "\"N_per_us\": %.3f, \"N_per_12bit_lsb\": %.3f, \"N_per_deadband_1us\": %.3f, \"N_per_deadband_3us\": %.3f}",
                  i ? ", " : "", Fpts[i], pc, x, g, dxdus, dxdus * g * dFdPc, dxdus * g * dFdPc * (1400.0 / 4096.0), dxdus * g * dFdPc, 3 * dxdus * g * dFdPc);
    an += b;
  }
  an += "]";
  j.k("analytic_resolution").raw(an);
  j.k("command_quantisation").raw("{\"can_thrust_N\": 0.1, \"servo_12bit_us\": 0.3418, \"teensy_pwm_us\": 0.0533, \"note\": \"FlexPWM 150 MHz / 8 at 333 Hz (DERIVED); servo resolution DATASHEET 12-bit over 800-2200 us\"}");
  std::string runs = "[" + deepRun(nominal(41), "nominal");
  SimConfig c = nominal(42); c.sv_pintle.deadband_us = 3.0; c.sv_pintle.backlash_rad = 0.5 * D2R;
  runs += ", " + deepRun(c, "db3us_bl0p5");
  SimConfig c2 = nominal(43); c2.vbat0 = 8.15; c2.R_batt = 0.08; c2.eng.tau_f_fixed = 0.5; c2.eng.comb_delay = 0.01;
  runs += ", " + deepRun(c2, "slowplant");
  runs += "]";
  j.k("runs").raw(runs);
  writeFile(OUT + "/S3_deep.json", j.str());
}

// ------------------------------------------------------------------------------------------ S4 hover tracking
static void scHover() {
  Sim s(nominal(51));
  s.schedule = padSequence(1.40);
  s.schedule.push_back({9.0, Cmd::SHUTDOWN, 0});
  s.thrust_cmd = [](double t) {
    if (t < 3.0) return 150.0;
    if (t < 6.0) return 150.0 + 25.0 * std::sin(2 * M_PI * 1.0 * (t - 3.0));
    if (t < 7.0) return 150.0 + 250.0 * (t - 6.0);
    if (t < 8.0) return 400.0 - 250.0 * (t - 7.0);
    return 150.0;
  };
  s.run(9.3);
  noteMon(s);
  s.writeCsv(OUT + "/S4_hover.csv");
  const auto& r = s.rec();
  double se = 0, sc = 0, ss = 0; int n = 0;
  for (const Rec& x : r) if (x.t >= 4.0 && x.t < 6.0) {
    const double ph = 2 * M_PI * (x.t - 3.0);
    se += std::pow(x.F - x.thr_cmd, 2); sc += (x.F - 150.0) * std::cos(ph); ss += (x.F - 150.0) * std::sin(ph); ++n;
  }
  const double amp = 2.0 * std::sqrt(sc * sc + ss * ss) / n, phase = std::atan2(sc, ss) * R2D;
  double se2 = 0; int n2 = 0; for (const Rec& x : r) if (x.t >= 6.1 && x.t < 7.9) { se2 += std::pow(x.F - x.thr_cmd, 2); ++n2; }
  J j;
  j.k("scenario").v("S4 hover-type tracking: 150 N +/- 25 N sine at 1 Hz, then 250 N/s ramps 150-400-150 N");
  j.k("sine_rms_err_N").v(std::sqrt(se / n)); j.k("sine_gain").v(amp / 25.0); j.k("sine_phase_deg").v(phase);
  j.k("ramp_rms_err_N").v(std::sqrt(se2 / n2));
  writeFile(OUT + "/S4_hover.json", j.str());
  std::printf("S4 hover: sine rms err %.2f N gain %.3f phase %.1f deg; ramp rms err %.2f N\n", std::sqrt(se / n), amp / 25.0, phase, std::sqrt(se2 / n2));
}

// ------------------------------------------------------------------------------------------ S5 Monte Carlo
// dispersed configurations (deterministic sequence: run i always gets the same parameters)
static std::vector<SimConfig> mcConfigs(int N) {
  std::mt19937 rng(20261011);
  auto U = [&](double a, double b) { return std::uniform_real_distribution<double>(a, b)(rng); };
  std::vector<SimConfig> v;
  for (int i = 0; i < N; ++i) {
    SimConfig c = nominal(1000 + i);
    c.eng.Cd_scale = U(0.6 / 0.7, 0.8 / 0.7);
    c.eng.reg_scale = U(0.6, 1.5);
    c.eng.tl_scale = U(0.5, 3.0);
    c.eng.comb_delay = U(0.003, 0.010);
    c.eng.eta_scale = U(0.85 / 0.92, 0.96 / 0.92);
    c.eng.T_tank0 = 273.15 + U(17.0, 23.0);
    for (ServoParams* sp : {&c.sv_pintle, &c.sv_tvc[0], &c.sv_tvc[1]}) {
      sp->deadband_us = U(0.5, 3.0); sp->backlash_rad = U(0.05, 0.5) * D2R; sp->pb_rad = U(1.0, 3.0) * D2R;
      sp->J_int = U(1.0e-3, 5.0e-3); sp->latency = U(0.0005, 0.002); sp->torque_scale = U(0.85, 1.0); sp->speed_scale = U(0.85, 1.0);
    }
    c.pc_span_err = U(-0.005, 0.005);
    c.vbat0 = U(8.15, 8.40);   // v2.2 ARM permit requires >= 8.1 V (batteries below it never reach RUN, see S6 battery_low_ARMED)
    c.R_batt = U(0.010, 0.080); // fresh to aged 2S pack incl. connector [ASSUMED]
    c.record_every_ms = 1;
    v.push_back(c);
  }
  return v;
}
static void mcProfile(Sim& s) {
  s.schedule = padSequence(1.40);
  s.schedule.push_back({7.6, Cmd::SHUTDOWN, 0});
  s.thrust_cmd = [](double t) { if (t < 3.0) return 100.0; if (t < 4.2) return 500.0; if (t < 5.4) return 100.0; if (t < 6.6) return 62.5; return 72.5; };
  s.gimbal_cmd = [](double t, float* g) { g[0] = static_cast<float>(t > 2.0 && t < 7.0 ? 2.0 * D2R * std::sin(2 * M_PI * 1.5 * t) : 0.0); g[1] = 0; };
}
static void scMCone(int k) {   // re-run one dispersed case with its full time history
  const std::vector<SimConfig> cs = mcConfigs(k + 1);
  Sim s(cs[k]);
  mcProfile(s);
  s.run(8.0);
  s.writeCsv(OUT + "/S5_mc_run" + std::to_string(k) + ".csv");
  int ab = 0; double t_ab = NAN; for (const Rec& x : s.rec()) if (x.abort && !ab) { ab = x.abort; t_ab = x.t; }
  std::printf("S5 run %d: abort %d (%s) at %.3f s, final %s\n", k, ab, ecu::abortName(static_cast<ecu::Abort>(ab)), t_ab, ecu::stateName(s.ecu.state()));
}
static void scMC(int N) {
  const std::vector<SimConfig> cs = mcConfigs(N);
  std::ofstream f(OUT + "/S5_mc.csv");
  f << "run,Cd_scale,reg_scale,tl_scale,comb_delay,eta_scale,T_tank0,db_us,backlash_deg,pb_deg,J_int,latency,torque_scale,speed_scale,span_err,vbat0,R_batt,"
       "ign_cmd90,up_rise,up_cmd90,up_ovs,up_settle,dn_rise,dn_cmd90,dn_ovs,deep_err,deep_pp,step10_err,pc_max,abort,final_state,contact_lost,"
       "noprog_max_s,jam_events\n";
  int aborts = 0, n_ok_req = 0, n_ok_tgt = 0, n_ok_res = 0;
  std::vector<double> ups, dns, ovs, deep_pp, pcmaxs;
  int hw_trips = 0, ovp_aborts = 0, mc_jams = 0;
  std::vector<double> mc_noprog;
  for (int i = 0; i < N; ++i) {
    const SimConfig& c = cs[i];
    Sim s(c);
    mcProfile(s);
    bool contact_lost = false;
    s.runUntil(8.0, [&](const Sim& sm) { contact_lost |= sm.pintle.contact_lost; return false; });
    noteMon(s); mc_noprog.push_back(s.noprog_max); mc_jams += s.jam_events;
    const auto& r = s.rec();
    const double ig90 = firstTime(r, 1.40, [](const Rec& x) { return x.F >= 90.0; }) - 1.40;
    const StepM up = stepMetrics(r, 3.0, 100, 500, 4.15);
    const StepM dn = stepMetrics(r, 4.2, 500, 100, 5.35);
    const StepM dp = stepMetrics(r, 5.4, 100, 62.5, 6.55);
    const StepM s10 = stepMetrics(r, 6.6, 62.5, 72.5, 7.55);
    double pcmax = 0; int ab = 0;
    for (const Rec& x : r) { pcmax = std::max(pcmax, x.Pc); if (!ab && x.abort) ab = x.abort; }
    if (ab) ++aborts;
    pcmaxs.push_back(pcmax); hw_trips += s.ovp_trip_t >= 0; ovp_aborts += (ab == (int)ecu::Abort::PC_OVERPRESSURE || ab == (int)ecu::Abort::HW_OVERPRESSURE);
    const bool req = up.rise <= 0.150 && dn.rise <= 0.150, tgt = up.rise <= 0.100 && dn.rise <= 0.100;
    const bool res = std::fabs(dp.ss_err) <= 5.0 && dp.pp <= 10.0 && std::fabs(s10.ss_err) <= 5.0 && s10.pp <= 10.0;
    n_ok_req += req; n_ok_tgt += tgt; n_ok_res += res;
    ups.push_back(up.rise); dns.push_back(dn.rise); ovs.push_back(std::max(up.overshoot, dn.overshoot)); deep_pp.push_back(dp.pp);
    char b[800];
    std::snprintf(b, sizeof b, "%d,%.4f,%.4f,%.4f,%.5f,%.4f,%.2f,%.3f,%.3f,%.3f,%.5f,%.5f,%.3f,%.3f,%.5f,%.3f,%.4f,%.4f,%.4f,%.4f,%.2f,%.3f,%.4f,%.4f,%.2f,%.3f,%.3f,%.3f,%.0f,%d,%d,%d,%.4f,%d\n",
                  i, c.eng.Cd_scale, c.eng.reg_scale, c.eng.tl_scale, c.eng.comb_delay, c.eng.eta_scale, c.eng.T_tank0, c.sv_pintle.deadband_us,
                  c.sv_pintle.backlash_rad * R2D, c.sv_pintle.pb_rad * R2D, c.sv_pintle.J_int, c.sv_pintle.latency, c.sv_pintle.torque_scale,
                  c.sv_pintle.speed_scale, c.pc_span_err, c.vbat0, c.R_batt, ig90, up.rise, up.cmd90, up.overshoot, up.settle, dn.rise, dn.cmd90, dn.overshoot,
                  dp.ss_err, dp.pp, s10.ss_err, pcmax, ab, r.back().state, contact_lost ? 1 : 0, s.noprog_max, s.jam_events);
    f << b;
    if ((i + 1) % 25 == 0) std::printf("S5 MC %d/%d\n", i + 1, N);
  }
  auto pct = [](std::vector<double> v, double p) { std::sort(v.begin(), v.end()); return v[std::min(v.size() - 1, static_cast<size_t>(p * (v.size() - 1) + 0.5))]; };
  J j;
  j.k("scenario").v("S5 Monte Carlo: 100 N ignite -> 500 N -> 100 N -> 62.5 N -> 72.5 N; plant, servo, sensor and battery parameters uniform over their ASSUMED/combustion bands");
  j.k("runs").v(N); j.k("aborts").v(aborts);
  j.k("pass_eng03_req_150ms_frac").v(double(n_ok_req) / N); j.k("pass_eng03_target_100ms_frac").v(double(n_ok_tgt) / N);
  j.k("pass_deep_resolution_frac").v(double(n_ok_res) / N);
  j.k("up_rise_p50_s").v(pct(ups, 0.5)); j.k("up_rise_p95_s").v(pct(ups, 0.95)); j.k("up_rise_max_s").v(pct(ups, 1.0));
  j.k("dn_rise_p50_s").v(pct(dns, 0.5)); j.k("dn_rise_p95_s").v(pct(dns, 0.95)); j.k("dn_rise_max_s").v(pct(dns, 1.0));
  j.k("overshoot_p50_pct").v(pct(ovs, 0.5)); j.k("overshoot_p95_pct").v(pct(ovs, 0.95)); j.k("overshoot_max_pct").v(pct(ovs, 1.0));
  j.k("deep_pp_p50_N").v(pct(deep_pp, 0.5)); j.k("deep_pp_p95_N").v(pct(deep_pp, 0.95)); j.k("deep_pp_max_N").v(pct(deep_pp, 1.0));
  j.k("pc_max_abs_p50_Pa").v(pct(pcmaxs, 0.5)); j.k("pc_max_abs_p95_Pa").v(pct(pcmaxs, 0.95)); j.k("pc_max_abs_max_Pa").v(pct(pcmaxs, 1.0));
  j.k("ovp_fw_threshold_abs_Pa").v(ecu::cfg::kPcOverPressureAbs_Pa); j.k("ovp_aborts").v(ovp_aborts); j.k("hw_comparator_trips").v(hw_trips);
  j.k("pintle_noprog_p50_s").v(pct(mc_noprog, 0.5)); j.k("pintle_noprog_max_s").v(pct(mc_noprog, 1.0)); j.k("pintle_jam_events").v(mc_jams);
  writeFile(OUT + "/S5_mc.json", j.str());
  std::printf("S5 MC: %s\n", j.str().c_str());
}

// ------------------------------------------------------------------------------------------ S6 abort paths
struct AbortCase {
  std::string name; int expect; std::function<void(Sim&)> inject; double t_inj; bool burning;
  std::function<void(SimConfig&)> cfg = nullptr;   // v2.2: configuration applied before the Sim is built (tank temperature ...)
  int expect_alt = -99;                            // v2.6: a second acceptable first cause (two detectors race; both abort)
  double ox_unlit_max_kg = -1.0;                   // v2.8 final: > 0 -> pass also needs the first start's unignited N2O <= this
};
// v2.2: +/-7 deg steps on alpha (3.0-3.6 s), beta (3.6-4.0 s) and along the 65 deg worst servo direction (4.0-4.4 s)
static void fullSlews(double t, float* g) {
  g[0] = g[1] = 0;
  const double D2Rl = M_PI / 180.0;
  if (t >= 3.0 && t < 3.6) g[0] = static_cast<float>((std::fmod(t - 3.0, 0.3) < 0.15 ? 7.0 : -7.0) * D2Rl);
  else if (t >= 3.6 && t < 4.0) g[1] = static_cast<float>((std::fmod(t - 3.6, 0.2) < 0.1 ? 7.0 : -7.0) * D2Rl);
  else if (t >= 4.0 && t < 4.4) {
    const double d = (std::fmod(t - 4.0, 0.2) < 0.1 ? 7.0 : -7.0) * D2Rl;
    g[0] = static_cast<float>(d * std::cos(65 * D2Rl)); g[1] = static_cast<float>(d * std::sin(65 * D2Rl));
  }
}
// v2.8 final (LEAD 2026-10-13 tank interlock T_tank <= 24 C at ARM and at ignition; ENG-12 15-24 C): the hot corner moves from 30 C (no longer
// a credible ignition state; the 30 C runs stay in results/sil_v2p8_draft and earlier) to 24 C - 0.05 K (297.10 K, below the 297.15 K
// interlock with the P_tank noise), Cd 0.8. Combustion v2.4: MEOP 45.06 bar at 25 C, 44.33 bar at 24 C
static void hot24Cd08(SimConfig& c) { c.eng.T_tank0 = 297.10; c.eng.Cd_scale = 0.8 / 0.7; }   // lead/Combustion worst corner: 24 C, Cd 0.8
static void scAborts() {
  const int OVP = (int)ecu::Abort::PC_OVERPRESSURE, HWOVP = (int)ecu::Abort::HW_OVERPRESSURE, PFAULT = (int)ecu::Abort::PINTLE_FAULT;
  std::vector<AbortCase> cases = {
      // v2.7 RC-01 torch-flame gate: the torch never lights -> TORCH_FAULT at 0.101 s, before the 0.12 s pintle step (v2.6 expected
      // NO_IGNITION at 0.35 s with the pintle at the ignition lift: N2O admitted with no ignition source - the RC-01 finding)
      {"torch_fails_TORCH_FAULT_before_pintle_step", (int)ecu::Abort::TORCH_FAULT, [](Sim& s) { s.eng.P.torch_fail = true; }, 1.40, false},
      {"torch_transducer_invalid_IGNITION", (int)ecu::Abort::TORCH_FAULT, [](Sim& s) { s.ptorch_fail_at = 1.40; }, 1.40, false},
      // v2.5-v2.7 (window from E0): a 0.25 s torch-to-main delay ignited after the 0.35 s check (NO_IGNITION); a 0.20 s delay raced the
      // check (HARD_START / NO_IGNITION, plant 39.1 bar). v2.8 (LEAD 2026-10-13, W 0.40 s counted from the lift at the torch confirmation
      // E1 ~0.045 s): both ignite INSIDE W (0.27 / 0.32 s after E0) as late lights with an accumulation spike (plant 26.7 / 28.3 bar abs,
      // below the 30 bar abort and MEOP). v2.8 draft EVIDENCE (results/sil_v2p8_draft): RUN was entered during the spike, the
      // flameout/band reference was reset to the measured ~20 bar and a false FLAMEOUT followed 47 ms later with the chamber lit.
      // v2.8 final: reference = min(measured, map Pc of the ignition lift) -> expected: no abort, unignited N2O <= 20 g (LEAD stand cap)
      {"hard_start_0p25s_delay_late_light_inside_W", 0, [](Sim& s) { s.eng.P.ign_delay = 0.25; s.eng.P.hard_start_gain = 1.0; }, 1.40, false,
       nullptr, -99, 0.020},
      {"hard_start_0p20s_delay_late_light_inside_W", 0, [](Sim& s) { s.eng.P.ign_delay = 0.20; s.eng.P.hard_start_gain = 1.0; }, 1.40, false,
       nullptr, -99, 0.020},
      {"flameout", (int)ecu::Abort::FLAMEOUT, [](Sim& s) { s.eng.P.flameout_at = 3.0; }, 3.0, true},
      // a jam is only observable when the command moves: hold 300 N, jam at 3.0 s, FC then commands 150 N at 3.05 s
      {"pintle_jam_then_throttle_down", (int)ecu::Abort::PINTLE_FAULT, [](Sim& s) { s.pintle_jam_at = 3.0; s.thrust_cmd = [](double t) { return t < 3.05 ? 300.0 : 150.0; }; }, 3.0, true},
      {"pintle_jam_steady_cmd_detect_late", (int)ecu::Abort::PINTLE_FAULT, [](Sim& s) { s.pintle_jam_at = 3.0; }, 3.0, true},
      // v2.6: the spring closes the unpowered needle away from the command -> stall monitor (kind DIVERGING) or flameout, whichever first
      {"pintle_servo_unpowered", (int)ecu::Abort::PINTLE_FAULT, [](Sim& s) { s.pintle_unpower_at = 3.0; }, 3.0, true, nullptr, (int)ecu::Abort::FLAMEOUT},
      // v2.8 (LEAD 2026-10-13 correction, MECH pre36): case abort 448.15 K / 0.2 s while the MV is latched or OPEN; 445 K (above the
      // 433.15 K start refusal, below the abort) must not abort a burn
      {"case_over_temp_455K", (int)ecu::Abort::OVER_TEMP, [](Sim& s) { s.tc_hot_at = 3.0; s.tc_hot_idx = 0; s.tc_hot_K = 455.0; }, 3.0, true},
      {"case_445K_in_RUN_no_abort", 0, [](Sim& s) { s.tc_hot_at = 3.0; s.tc_hot_idx = 1; s.tc_hot_K = 445.0; }, 3.0, true},
      {"tank_overpressure_in_ARMED", (int)ecu::Abort::TANK_OVERPRESSURE, [](Sim& s) { s.ptank_bias_at = 0.4; s.ptank_bias = 20e5; }, 0.4, false},
      {"tank_overpressure_in_RUN_flag_only", 0, [](Sim& s) { s.ptank_bias_at = 3.0; s.ptank_bias = 20e5; }, 3.0, true},
      // FC gimbal command 2 deg sine at 1 Hz from 2.0 s; actuator A output locks at 3.0 s.
      // v2.6 EVIDENCE (FAILS since the as-built linkage, mechanical.json v2): servos act along the 135/225 deg diagonals, so with A
      // locked an alpha command is followed half by B: engine (a, -a)/2 for a command a, i.e. 1.0 deg per-axis mismatch (1.41 deg
      // along servo A's line) at a = 2 deg, below the 1.5 deg monitor threshold. v2.1-v2.5 (v1 linkage, levers 64.5/154.5 deg)
      // detected it in 184-249 ms. Detection bound now: >= 3 deg along an axis / >= 2.12 deg along a servo line (+ lag allowance).
      // Threshold or metric change (servo-frame error, x1.41 sensitivity) is a GNC false-abort trade -> open interface issue.
      {"gimbal_jam_moving_cmd", (int)ecu::Abort::GIMBAL_FAULT, [](Sim& s) { s.tvc_jam_at = 3.0;
         s.gimbal_cmd = [](double t, float* g) { g[0] = static_cast<float>(t > 2.0 ? 2.0 * D2R * std::sin(2 * M_PI * (t - 2.0)) : 0.0); g[1] = 0; }; }, 3.0, true},
      // v2.6: the same jam under a 4 deg alpha sine (above the bound): must be detected
      {"gimbal_jam_moving_cmd_4deg", (int)ecu::Abort::GIMBAL_FAULT, [](Sim& s) { s.tvc_jam_at = 3.0;
         s.gimbal_cmd = [](double t, float* g) { g[0] = static_cast<float>(t > 2.0 ? 4.0 * D2R * std::sin(2 * M_PI * (t - 2.0)) : 0.0); g[1] = 0; }; }, 3.0, true},
      {"gimbal_jam_at_commanded_angle_undetectable", 0, [](Sim& s) { s.tvc_jam_at = 3.0; }, 3.0, true},
      // v2.2 full-range steps at the 150 deg/s ECU limit (no FC shaping): the widened mismatch window must not trip
      {"gimbal_full_slews_no_false_fault", 0, [](Sim& s) { s.gimbal_cmd = fullSlews; }, 3.0, true},
      // v2.3/v2.4 FM-PWR-01 ARM rule: an 80 mOhm pack at 8.15 V predicts < 6.6 V at the servo plug -> ARM refused (TVC_SUPPLY);
      // the no-false-fault check at a sagging supply uses a 45 mOhm pack (7.1 V predicted, accepted)
      {"gimbal_full_slews_weak_batt_0p08ohm_ARM_refused", (int)ecu::Abort::TVC_SUPPLY, [](Sim& s) { s.gimbal_cmd = fullSlews; }, 3.0, true, [](SimConfig& c) { c.vbat0 = 8.15; c.R_batt = 0.08; }},
      {"gimbal_full_slews_no_false_fault_batt_0p045ohm", 0, [](Sim& s) { s.gimbal_cmd = fullSlews; }, 3.0, true, [](SimConfig& c) { c.vbat0 = 8.15; c.R_batt = 0.045; }},
      {"gimbal_jam_during_full_slews", (int)ecu::Abort::GIMBAL_FAULT, [](Sim& s) { s.gimbal_cmd = fullSlews; s.tvc_jam_at = 3.3; }, 3.3, true},
      {"link_loss_RUN", (int)ecu::Abort::LINK_LOST, [](Sim& s) { s.link_down_from = 3.0; }, 3.0, true},
      // GNC v1 landing-burn policy: HOLD last setpoint and gimbal 0.3 s, then SHUTDOWN (arg = (hold in 0.1 s) << 8 | HOLD_THEN_SHUTDOWN)
      {"link_loss_RUN_landing_hold_0p3s", (int)ecu::Abort::LINK_LOST, [](Sim& s) { s.link_down_from = 3.0; s.schedule.insert(s.schedule.begin(), {0.02, Cmd::SET_LINK_POLICY, (3 << 8) | 1}); }, 3.0, true},
      {"mcu_hang_watchdog", -1, [](Sim& s) { s.hang_at = 3.0; }, 3.0, true},
      // roll valve held on by the FC when the link drops: dead-man must close it within 50 ms (+ LINK_LOST abort after 100 ms)
      {"roll_valve_on_at_link_loss", (int)ecu::Abort::LINK_LOST, [](Sim& s) { s.roll_cmd = [](double t) { return static_cast<uint8_t>(t >= 2.8 ? 1 : 0); }; s.link_down_from = 3.0; }, 3.0, true},
      {"arm_plug_pulled_RUN", (int)ecu::Abort::ARM_LOST, [](Sim& s) { s.arm_plug_pull_at = 3.0; }, 3.0, true},
      // v2.3: the TVC supply prediction (100 ms) trips before BATT_LOW (200 ms); both are recorded
      {"battery_low_ARMED", (int)ecu::Abort::TVC_SUPPLY, [](Sim& s) { s.vbat_drop_at = 0.4; s.vbat_drop = 1.8; }, 0.4, false, nullptr, (int)ecu::Abort::BATT_LOW},
      {"pc_sensor_fail_RUN_openloop", 0, [](Sim& s) { s.pc_sensor_fail_at = 3.0; }, 3.0, true},
      // v2.7: on the test stand (finite load cell) a Pc-signal loss in RUN aborts after 5 ms (flight keeps the open-loop rule above)
      {"pc_sensor_fail_RUN_test_stand", (int)ecu::Abort::PC_SENSOR, [](Sim& s) { s.pc_sensor_fail_at = 3.0; }, 3.0, true,
       [](SimConfig& c) { c.test_stand = true; }},
      // v2.7 LEAD 2026-10-13: LTC4365 OV disconnect -> /FAULT drops the MV holding magnet in hardware, the servo-side rail collapses
      // (10 uF / 1 kOhm bleed, idle servo = slowest), firmware PINTLE_FAULT 2 ms below 5.5 V; the unpowered needle is closed by the
      // spring back-driving the HV69 (plant: free back-drive; B-PNT-1 measures the real back-drive torque)
      {"pintle_rail_ov_trip_transient_RUN", PFAULT, [](Sim& s) { s.prail_ov_at = 3.0; }, 3.0, true},
      {"pintle_regulator_fail_high_RUN", PFAULT, [](Sim& s) { s.preg_fail_at = 3.0; }, 3.0, true},
      {"pintle_rail_ov_trip_ARMED", PFAULT, [](Sim& s) { s.prail_ov_at = 0.4; }, 0.4, false},
      // LTC4365 restart delay at its 49 ms maximum: the servo-side rail comes up 53 ms after the ARM bus, inside the 60 ms settle
      {"ltc4365_restart_49ms_no_false_trip", 0, [](Sim& s) {}, 3.0, true, [](SimConfig& c) { c.ltc_restart_s = 0.049; }},
      {"pc_sensor_fail_IGNITION", (int)ecu::Abort::PC_SENSOR, [](Sim& s) { s.pc_sensor_fail_at = 1.45; }, 1.45, false},
      {"fc_abort_command", (int)ecu::Abort::CMD, [](Sim& s) { s.schedule.push_back({3.0, Cmd::ABORT, 0}); }, 3.0, true},
      // v2.2 chamber over-pressure (lead 2026-10-12: MEOP 45 bar, ECU abort ~30 bar, pintle full-stroke failure 32-44 bar).
      // Runaway = pintle servo drives to full travel (2100 us) whatever the command, while it has power.
      // v2.6: the stall monitor (needle moving away from the command, kind DIVERGING) races the over-pressure check; either aborts
      {"pintle_runaway_RUN", OVP, [](Sim& s) { s.pintle_runaway_at = 3.0; }, 3.0, true, nullptr, PFAULT},
      {"pintle_runaway_RUN_24C_Cd0p8", OVP, [](Sim& s) { s.pintle_runaway_at = 3.0; }, 3.0, true, hot24Cd08, PFAULT},
      {"pintle_runaway_500N_24C_Cd0p8", OVP, [](Sim& s) { s.pintle_runaway_at = 3.0; s.thrust_cmd = [](double) { return 500.0; }; }, 3.0, true, hot24Cd08, PFAULT},
      // firmware check disabled (SIL hook): the comparator/latch must trip on its own and drop the ARM bus
      // hardware path alone: firmware over-pressure check AND (v2.6) the pintle stall monitor disabled by SIL hooks
      {"pintle_runaway_fw_ovp_off_hw_trip", HWOVP, [](Sim& s) { s.pintle_runaway_at = 3.0; s.fw_ovp_disabled = true; s.pintle_mon_disabled = true; }, 3.0, true},
      {"pintle_runaway_fw_ovp_off_hw_trip_24C_Cd0p8_band_high", HWOVP, [](Sim& s) { s.pintle_runaway_at = 3.0; s.fw_ovp_disabled = true; s.pintle_mon_disabled = true; }, 3.0, true,
       [](SimConfig& c) { hot24Cd08(c); c.ovp_trip_Pa_g += ovp::kBandPa; }},
      {"pintle_runaway_500N_fw_ovp_off_hw_trip_24C_Cd0p8_band_high", HWOVP, [](Sim& s) { s.pintle_runaway_at = 3.0; s.fw_ovp_disabled = true; s.pintle_mon_disabled = true;
         s.thrust_cmd = [](double) { return 500.0; }; }, 3.0, true, [](SimConfig& c) { hot24Cd08(c); c.ovp_trip_Pa_g += ovp::kBandPa; }},
      // v2.6 stall monitor alone (firmware over-pressure check off): runaway at 300 N caught by the monitor
      {"pintle_runaway_fw_ovp_off_monitor_catches", PFAULT, [](Sim& s) { s.pintle_runaway_at = 3.0; s.fw_ovp_disabled = true; }, 3.0, true, nullptr, HWOVP},
      // sudden partial throat blockage (debris): Pc jumps faster than the Pc loop can throttle down
      {"throat_blocked_70pct_RUN", OVP, [](Sim& s) { s.eng.P.At_block_at = 3.0; s.eng.P.At_block_frac = 0.7; }, 3.0, true},
      // v2.6: the hardware comparator (unfiltered tap) trips 8 ms after the blockage, before the firmware's filtered 3 ms check:
      // either cause is correct; the case still FAILS the MEOP criterion (v2.7/v2.8 draft at 30 C: plant Pc 55.7 bar > 45 bar; a sudden
      // 70 % blockage at 500 N / Cd 0.8 outruns any shutdown; below the 67.5 bar proof) - evidence for Combustion/Mechanical (COMB v2.4:
      // acceptable as a FAULT load case, LC-TB70; the MV closing time changes the time above MEOP by <= 2 ms). v2.8 final: 24 C corner
      {"throat_blocked_70pct_500N_24C_Cd0p8", OVP, [](Sim& s) { s.eng.P.At_block_at = 3.0; s.eng.P.At_block_frac = 0.7;
         s.thrust_cmd = [](double) { return 500.0; }; }, 3.0, true, hot24Cd08, HWOVP},
      // v2.8 LEAD 2026-10-13 MV concept change: the same case with the v2.2-v2.7 spring-return ball valve (closing 0.10 s, ball overlap
      // area law) for comparison with the MV-P poppet baseline (dashpot closing ~30 ms after a 9.4 ms latch release) above
      {"throat_blocked_70pct_500N_24C_Cd0p8_ballvalve_v2p7_compare", OVP, [](Sim& s) { s.eng.P.At_block_at = 3.0; s.eng.P.At_block_frac = 0.7;
         s.thrust_cmd = [](double) { return 500.0; }; }, 3.0, true, [](SimConfig& c) { hot24Cd08(c); c.eng.mv_type = 0; }, HWOVP},
      // v2.8 over-thrust (v2.8.1 LEAD ADOPTED: 650 N on 3 consecutive fresh FC_THRUST frames, flight RUN, with or without a valid Pc): the
      // Pc channel fails at 3.0 s (the hardware comparator on the same PC_SIG is blind too), the pintle runs away at 3.1 s; FC estimate
      // v2.8.1 = adopted first-order tau 20 ms (v2.8: pure 20 ms delay), 5 N rms noise [ASSUMED]. The stall monitor (DIVERGING) races the
      // over-thrust abort; either is accepted
      {"pc_lost_then_runaway_500N_24C_Cd0p8_over_thrust", (int)ecu::Abort::OVER_THRUST, [](Sim& s) { s.pc_sensor_fail_at = 3.0; s.pintle_runaway_at = 3.1;
         s.thrust_cmd = [](double) { return 500.0; }; }, 3.1, true, hot24Cd08, PFAULT},
      {"pc_lost_then_runaway_300N_over_thrust_monitor_off", (int)ecu::Abort::OVER_THRUST, [](Sim& s) { s.pc_sensor_fail_at = 3.0; s.pintle_runaway_at = 3.1;
         s.pintle_mon_disabled = true; }, 3.1, true},
      // v2.8.1 sensitivity: the IMU internal filter / sample delay and the FC scheduling are UNKNOWN (datasheet not read): an extra 10 ms
      // [ASSUMED] pure delay on top of the tau 20 ms estimate
      {"pc_lost_then_runaway_500N_24C_Cd0p8_over_thrust_extra_delay_10ms", (int)ecu::Abort::OVER_THRUST, [](Sim& s) { s.pc_sensor_fail_at = 3.0;
         s.pintle_runaway_at = 3.1; s.fc_thr_lat = 0.010; s.thrust_cmd = [](double) { return 500.0; }; }, 3.1, true, hot24Cd08, PFAULT},
      // v2.8.1 in-range wrong Pc (why the check also runs with a valid Pc): PC_SIG reads 0.70 x the true gauge pressure from 3.0 s (one
      // transducer: firmware sample and hardware comparator both see the low value); the Pc loop drives the true Pc up to hold the set point
      {"pc_reads_low_x0p70_500N_24C_Cd0p8_over_thrust_pc_valid", (int)ecu::Abort::OVER_THRUST, [](Sim& s) { s.pc_gain_at = 3.0; s.pc_gain = 0.70;
         s.thrust_cmd = [](double) { return 500.0; }; }, 3.0, true, hot24Cd08},
      // coverage EVIDENCE: a 0.85 x reading error keeps the true thrust below 650 N: no detector trips (Pc loop error stays in range)
      {"pc_reads_low_x0p85_500N_24C_Cd0p8_below_threshold_EVIDENCE", 0, [](Sim& s) { s.pc_gain_at = 3.0; s.pc_gain = 0.85;
         s.thrust_cmd = [](double) { return 500.0; }; }, 3.0, true, hot24Cd08},
      // false-abort check at the design basis: 500 N at the hot corner (v2.8 final 24 C) / Cd 0.8 with the FC estimate biased +10 % (< 650 N)
      {"pc_lost_500N_24C_Cd0p8_fc_bias_plus10pct_no_false_trip", 0, [](Sim& s) { s.pc_sensor_fail_at = 3.0; s.fc_thr_bias = 0.10;
         s.thrust_cmd = [](double) { return 500.0; }; }, 3.0, true, hot24Cd08},
      // v2.8.1: the same with a valid Pc (the check now also runs with a valid Pc)
      {"pc_valid_500N_24C_Cd0p8_fc_bias_plus10pct_no_false_trip", 0, [](Sim& s) { s.fc_thr_bias = 0.10;
         s.thrust_cmd = [](double) { return 500.0; }; }, 3.0, true, hot24Cd08},
      // dependency EVIDENCE: FC estimate stale (frames stop at 3.05 s): over-thrust blind; only the stall monitor remains
      {"pc_lost_runaway_fc_estimate_stale_monitor_only", PFAULT, [](Sim& s) { s.pc_sensor_fail_at = 3.0; s.pintle_runaway_at = 3.1; s.fc_thr_stale_from = 3.05;
         s.thrust_cmd = [](double) { return 500.0; }; }, 3.1, true, hot24Cd08},
      // v2.8 mode strap (LEAD 2026-10-13): STAND strap in a flight harness (no load cell) -> ARM refused; bay inhibit ~45 C (TO-DEFINE)
      {"mode_strap_stand_without_load_cell_ARM_refused", (int)ecu::Abort::MODE_MISMATCH, [](Sim& s) { s.strap_override = 2; }, 0.05, false},
      {"mode_strap_invalid_open_harness_ARM_refused", (int)ecu::Abort::MODE_MISMATCH, [](Sim& s) { s.strap_override = 0; }, 0.05, false},
      {"bay_hot_320K_ARM_refused", (int)ecu::Abort::BAY_HOT, [](Sim& s) { s.bay_K = 320.0; }, 0.05, false},
      // v2.8 final tank interlock (LEAD 2026-10-13): a 30 C tank (wall DS18B20 = plant tank temperature, Tsat(P_tank) 303.15 K) -> ARM refused
      {"tank_30C_ARM_refused", (int)ecu::Abort::TANK_HOT, [](Sim& s) {}, 0.05, false, [](SimConfig& c) { c.eng.T_tank0 = 303.15; }},
      // P_tank invalid and both wall sensors invalid (no valid tank reading) -> ARM refused; one wall valid at 20 C -> no abort, burns
      {"tank_no_valid_reading_ARM_refused", (int)ecu::Abort::TANK_HOT, [](Sim& s) { s.ptank_valid = false; s.ttank_wall_valid[0] = s.ttank_wall_valid[1] = false; }, 0.05, false},
      {"throat_blocked_70pct_fw_ovp_off_hw_trip", HWOVP, [](Sim& s) { s.eng.P.At_block_at = 3.0; s.eng.P.At_block_frac = 0.7; s.fw_ovp_disabled = true; }, 3.0, true},
      // small blockage: the Pc loop holds Pc (no abort) but thrust falls ~30 % while the Pc-based thrust estimate does not
      {"throat_blocked_30pct_RUN_loop_holds_Pc", 0, [](Sim& s) { s.eng.P.At_block_at = 3.0; s.eng.P.At_block_frac = 0.3; }, 3.0, true},
  };
  J j;
  j.k("scenario").v("S6 abort paths: 300 N burn (or pad state), fault injected at t_inj; expect = Abort enum (0 = no abort expected, -1 = watchdog reset, ECU reboots in SAFE); "
                     "v2.2: pass also requires plant Pc <= lead MEOP 45 bar abs. v2.8: MV-P poppet plant (mv_type 1) unless a case says ballvalve");
  j.k("mv_plant").raw(std::string("{\"mv_type_default\": ") + std::to_string(EngineParams().mv_type) + ", \"t_close_poppet_s\": " +
                      std::to_string(EngineParams().t_mv_close_poppet) + ", \"t_latch_release_s\": " + std::to_string(EngineParams().t_latch_release) +
                      ", \"t_close_ball_s\": " + std::to_string(EngineParams().t_mv_close) + "}");
  std::string arr = "[";
  int pass = 0;
  for (size_t i = 0; i < cases.size(); ++i) {
    const AbortCase& ac = cases[i];
    SimConfig cfg0 = nominal(61 + i);
    if (ac.cfg) ac.cfg(cfg0);
    Sim s(cfg0);
    s.schedule = padSequence(1.40);
    s.thrust_cmd = [](double) { return 300.0; };
    ac.inject(s);
    std::sort(s.schedule.begin(), s.schedule.end(), [](const StateCmd& a, const StateCmd& b) { return a.t < b.t; });
    s.schedule.push_back({4.5, Cmd::SHUTDOWN, 0});
    s.run(5.0);
    const auto& r = s.rec();
    s.writeCsv(OUT + "/S6_" + ac.name + ".csv");
    int cause = 0; double t_ab = NAN;
    for (const Rec& x : r) if (x.abort && std::isnan(t_ab)) { cause = x.abort; t_ab = x.t; }
    double F_inj = 0; for (const Rec& x : r) if (x.t < ac.t_inj) F_inj = x.F;
    const double t_low = ac.burning ? firstTime(r, ac.t_inj, [&](const Rec& x) { return x.F < 0.1 * std::max(F_inj, 1.0); }) : NAN;
    const double t_mvc = firstTime(r, ac.t_inj, [](const Rec& x) { return x.mv < 0.03; });
    double roll_off = NAN; bool roll_on_at_inj = false;
    for (const Rec& x : r) if (x.t <= ac.t_inj && x.t > ac.t_inj - 0.002) roll_on_at_inj = roll_on_at_inj || x.sol4 || x.sol5;
    if (roll_on_at_inj) roll_off = firstTime(r, ac.t_inj, [](const Rec& x) { return !x.sol4 && !x.sol5; }) - ac.t_inj;
    double pcmax = 0; for (const Rec& x : r) if (x.t >= ac.t_inj - 0.5) pcmax = std::max(pcmax, x.Pc);
    double Fmax_inj = 0; for (const Rec& x : r) if (x.t >= ac.t_inj) Fmax_inj = std::max(Fmax_inj, x.F);   // v2.8.1
    // v2.2 over-pressure metrics (plant Pc, absolute)
    const double meop = ecu::cfg::kPcMeopLeadAbs_Pa, lim = ecu::cfg::kPcOverPressureAbs_Pa;
    double t_over = 0, t_over_meop = 0; for (const Rec& x : r) if (x.t >= ac.t_inj) { t_over += (x.Pc > lim) * 1e-3; t_over_meop += (x.Pc > meop) * 1e-3; }
    const double t_arm_off = firstTime(r, ac.t_inj, [](const Rec& x) { return !x.arm_bus; }) - ac.t_inj;
    const double t_hw = s.ovp_trip_t >= 0 ? s.ovp_trip_t - ac.t_inj : NAN;
    const double t_pclosed = ac.burning ? firstTime(r, ac.t_inj + 0.002, [](const Rec& x) { return x.x < 0.05e-3; }) - ac.t_inj : NAN;
    double F_true_end = NAN, F_est_end = NAN; for (const Rec& x : r) if (x.t <= 4.4) { F_true_end = x.F; F_est_end = x.F_est; }
    const bool meop_ok = pcmax <= meop;
    const int jam_kind = s.out.pintle_fault_kind;
    // v2.7: hardware MV-latch drive off (after the /FAULT gate), torch N2O-alone, unignited N2O per start, lockout at the end
    const double t_latch_hw = firstTime(r, ac.t_inj, [](const Rec& x) { return !x.mv_latch_hw; }) - ac.t_inj;
    std::string oxs = "[";
    for (size_t k = 0; k < s.ox_unlit_starts.size(); ++k) { char q[40]; std::snprintf(q, sizeof q, "%s%.5f", k ? ", " : "", s.ox_unlit_starts[k]); oxs += q; }
    oxs += "]";
    bool ok;
    if (ac.expect == -1) ok = s.ecu.state() == State::SAFE && std::isfinite(t_low);
    else ok = cause == ac.expect || cause == ac.expect_alt;
    ok = ok && meop_ok;   // v2.2: every case must also keep the plant Pc at or below the lead MEOP (45 bar)
    ok = ok && s.n2o_alone_ms == 0;   // v2.7 RC-01: torch N2O never flows without propane
    if (roll_on_at_inj) ok = ok && roll_off <= ecu::cfg::kRollDeadman_s + 0.0015;
    if (ac.ox_unlit_max_kg > 0) ok = ok && !s.ox_unlit_starts.empty() && s.ox_unlit_starts[0] <= ac.ox_unlit_max_kg;   // v2.8 final
    pass += ok;
    char b[2000];
    std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"expect\": %d, \"cause\": %d, \"cause_name\": \"%s\", \"t_inj\": %.3f, \"inj_to_abort_s\": %.4f, "
                  "\"inj_to_F_below_10pct_s\": %.4f, \"inj_to_MV_closed_s\": %.4f, \"inj_to_roll_valve_off_s\": %.4f, \"F_at_inj_N\": %.1f, \"Pc_max_abs_Pa\": %.0f, "
                  "\"t_Pc_above_30bar_s\": %.4f, \"t_Pc_above_MEOP_s\": %.4f, \"inj_to_hw_comparator_trip_s\": %.4f, \"inj_to_ARM_bus_off_s\": %.4f, "
                  "\"inj_to_pintle_closed_s\": %.4f, \"F_true_at_4p4s_N\": %.1f, \"F_est_at_4p4s_N\": %.1f, \"final_state\": \"%s\", \"meop_ok\": %s, "
                  "\"jam_events\": %d, \"jam_kind\": %d, \"noprog_max_s\": %.4f, \"Pc_xdcr_max_abs_Pa\": %.0f, \"fault_bits\": %u, "
                  "\"inj_to_MV_latch_hw_off_s\": %.4f, \"ltc4365_trips\": %d, \"n2o_alone_ms\": %ld, \"ox_unlit_per_start_kg\": %s, "
                  "\"relight_lockout_end\": %s, \"F_max_after_inj_N\": %.1f, \"pass\": %s}",
                  i ? ", " : "", ac.name.c_str(), ac.expect, cause, ecu::abortName(static_cast<ecu::Abort>(cause)), ac.t_inj, t_ab - ac.t_inj,
                  t_low - ac.t_inj, t_mvc - ac.t_inj, roll_off, F_inj, pcmax, t_over, t_over_meop, t_hw, t_arm_off, t_pclosed, F_true_end, F_est_end,
                  ecu::stateName(s.ecu.state()), meop_ok ? "true" : "false", s.jam_events, jam_kind, s.noprog_max, s.pc_xdcr_max, (unsigned)s.out.fault_bits,
                  t_latch_hw, s.ltc_trips, s.n2o_alone_ms, oxs.c_str(), s.out.relight_lockout ? "true" : "false", Fmax_inj, ok ? "true" : "false");
    std::string sb(b);
    for (auto p = sb.find("nan"); p != std::string::npos; p = sb.find("nan")) sb.replace(p, 3, "null");
    arr += sb;
    std::printf("S6 jam events %d kind %d, Pc at transducer max %.1f bar, faults 0x%04X | ", s.jam_events, jam_kind, s.pc_xdcr_max / 1e5, (unsigned)s.out.fault_bits);
    std::printf("S6 %-52s expect %3d got %3d (%s) abort+%.0f ms, F<10%% +%.0f ms, MV closed +%.0f ms, ARM off +%.0f ms, Pc max %.1f bar%s, final %s %s\n",
                ac.name.c_str(), ac.expect, cause, ecu::abortName(static_cast<ecu::Abort>(cause)), (t_ab - ac.t_inj) * 1e3, (t_low - ac.t_inj) * 1e3,
                (t_mvc - ac.t_inj) * 1e3, t_arm_off * 1e3, pcmax / 1e5, meop_ok ? "" : " > MEOP", ecu::stateName(s.ecu.state()), ok ? "PASS" : "FAIL");
  }
  arr += "]";
  j.k("cases").raw(arr);
  j.k("passed").v(pass); j.k("total").v(static_cast<double>(cases.size()));
  writeFile(OUT + "/S6_aborts.json", j.str());
}

// ------------------------------------------------------------------------------------------ S7 TVC (2-axis Cardan gimbal, v2.6)
// Firmware TvcShaper (v2.6 exact pushrod solve on the as-built linkage, per-axis ENG-07d notch) driving GimbalPlant2 (v2.6: 3-D
// pushrods, FEA structure compliance per axis, mechanical.json v2); misalignment + floor side load applied together along servo
// A's direction (conservative). v2.1-v2.5 used the mechanical.json v1 linkage (n 6, levers 64.5/154.5 deg) - superseded.
struct TvcRun { std::vector<double> t, ca, cb, a, b, usa, usb, Fa, Fb; int stop_ms = 0; double len_err_max = 0; };
static TvcRun tvcSim(const ServoParams& sp, const Gimbal2Params& gp, const std::function<void(double, float*)>& cmd, double T,
                     uint32_t seed, double rate_limit = ecu::cfg::kGimbalRateLimit_radps, const ecu::GimbalNotchCal* nc = nullptr,
                     bool bypass = false, double accel_limit = ecu::cfg::kGimbalAccelLimit_radps2) {
  GimbalPlant2 g(gp, sp, sp, seed);
  ecu::TvcShaper sh;
  sh.horn_r_m = static_cast<float>(gp.r_h);
  sh.rate_limit_radps = static_cast<float>(rate_limit);
  sh.accel_limit_radps2 = static_cast<float>(accel_limit);   // v2.8.3: gnc.json v3 tracker (flight default); 0 = plain slew limiter
  sh.bypass_filters = bypass;                         // v2.6 B-TVC-1 FRF mode (TVC_TEST_ENABLE 2)
  if (nc) { sh.setNotchAxis(0, nc->ax[0], 1e-3f); sh.setNotchAxis(1, nc->ax[1], 1e-3f); }
  const float z[2] = {0, 0}; sh.reset(z);
  TvcRun r;
  const int n = 40;
  for (int ms = 0; ms < static_cast<int>(T * 1000); ++ms) {
    const double t = ms * 1e-3;
    float c[2]; cmd(t, c);
    float oe[2], ou[2];
    sh.step(c, 1e-3f, oe, ou);
    const double us[2] = {ou[0], ou[1]};
    for (int k = 0; k < n; ++k) g.step(1e-3 / n, t + k * 1e-3 / n, us);
    if (g.at_stop) ++r.stop_ms;
    r.len_err_max = std::max({r.len_err_max, std::fabs(g.rodLength(0) - gp.L_rod), std::fabs(g.rodLength(1) - gp.L_rod)});
    r.t.push_back(t); r.ca.push_back(oe[0]); r.cb.push_back(oe[1]); r.a.push_back(g.a); r.b.push_back(g.b);
    r.usa.push_back(ou[0]); r.usb.push_back(ou[1]); r.Fa.push_back(g.F_rod[0]); r.Fb.push_back(g.F_rod[1]);
  }
  return r;
}
// ENG-07 (LEAD 2026-10-12): worst-direction slew at 7 deg >= 100 deg/s at the 7.4 V nominal plug; 6.6 V degraded accepted on the
// GNC MC. Ramp commands along direction dir in the (alpha, beta) plane (both servos coordinated, straight engine path):
// v2.8.3: these are ACTUATOR capability runs: the ECU slew limit is 1000 rad/s (not deg/s as the v2.2-v2.8.2 comment said; in effect
// no limit) and the gnc.json v3 tracker is OFF (acceleration limit 0), so both rows keep their v2.8.2 meaning; flight shaping is in
// the per-axis cases below and in test_core group (26).
//  * capability: no ECU rate limit (1000 rad/s), 150 deg/s ramp -7 -> +7 deg; the actuator saturates where it cannot follow, so the mean
//    rate while the engine moves from 4 to 6 deg (and -1 to +1 deg) is its loaded capability there;
//  * tracking: 100 deg/s ramp; lag at mid-travel and at the end of the ramp; mean rate of the engine AND of the shaped command
//    over -1..+1 deg (steady ramp) and 4..6 deg (the raw ramp ends at 7 deg, so the shaped command already decelerates there).
// Both slew senses are run (the constant disturbance moments aid one sense and oppose the other); the worst is kept.
// v2.6 criterion review (evidence kept): v2.5 flagged meets_100 = cap46 >= 100 && engine 4-6 deg ramp rate >= 97. That second
// term failed in every row (92.8-96.4 deg/s), including 8.4 V and directions with >= 150 deg/s capability, because the 4-6 deg
// window contains the end-of-ramp deceleration of the low-pass-shaped command; it measured the shaping, not the actuator.
// v2.6: meets_100 = capability at 6.25-6.75 deg >= 100 deg/s (ENG-07 near 7 deg) && engine mid-travel ramp rate >= 97 deg/s.
// The v2.5 term is still computed and reported as v25_ramp_term_pass.
static std::string tvcCapability(const std::string& tag, const ServoParams& sp, const Gimbal2Params& gp, double dir_deg, bool* pass,
                                 double* cap_out = nullptr, double* cap7_out = nullptr) {
  const double c = std::cos(dir_deg * D2R), sn = std::sin(dir_deg * D2R);
  double cap_c = 1e9, cap46 = 1e9, cap67 = 1e9, r100_46 = 1e9, lag_mid = 0, lag_end = 0;
  double r100_mid = 1e9, c100_mid = 1e9, c100_46 = 1e9;
  for (int sgn : {+1, -1}) {
    for (double R : {150.0, 100.0}) {
      TvcRun q = tvcSim(sp, gp, [=](double t, float* cm) {
          const double d0 = -sgn * 7 * D2R, d1 = sgn * 7 * D2R, Rr = R * D2R;
          const double d = t < 0.4 ? d0 : (sgn > 0 ? std::min(d1, d0 + Rr * (t - 0.4)) : std::max(d1, d0 - Rr * (t - 0.4)));
          cm[0] = static_cast<float>(d * c); cm[1] = static_cast<float>(d * sn); }, 0.8, 29, 1000.0, nullptr, false, 0.0);
      auto prog = [&](size_t i) { return sgn * (q.a[i] * c + q.b[i] * sn) * R2D; };
      auto progc = [&](size_t i) { return sgn * (q.ca[i] * c + q.cb[i] * sn) * R2D; };
      auto crossf = [&](const std::function<double(size_t)>& f, double v) -> double {
        for (size_t i = 1; i < q.t.size(); ++i) {
          if (q.t[i] > 0.4 && f(i - 1) < v && f(i) >= v) return q.t[i - 1] + (v - f(i - 1)) / (f(i) - f(i - 1)) * 1e-3;
        }
        return NAN;
      };
      auto cross = [&](double v) { return crossf(prog, v); };
      auto crossc = [&](double v) { return crossf(progc, v); };
      const double t4 = cross(4.0), t6 = cross(6.0), tm1 = cross(-1.0), tp1 = cross(1.0), t625 = cross(6.25), t675 = cross(6.75);
      if (R == 150.0) { cap46 = std::min(cap46, 2.0 / (t6 - t4)); cap_c = std::min(cap_c, 2.0 / (tp1 - tm1)); cap67 = std::min(cap67, 0.5 / (t675 - t625)); }
      else {
        r100_46 = std::min(r100_46, 2.0 / (t6 - t4));
        r100_mid = std::min(r100_mid, 2.0 / (tp1 - tm1));
        c100_mid = std::min(c100_mid, 2.0 / (crossc(1.0) - crossc(-1.0)));
        c100_46 = std::min(c100_46, 2.0 / (crossc(6.0) - crossc(4.0)));
        for (size_t i = 1; i < q.t.size(); ++i) {
          if (q.t[i] <= 0.4) continue;
          if (progc(i - 1) < 0.0 && progc(i) >= 0.0) lag_mid = std::max(lag_mid, progc(i) - prog(i));
          if (progc(i - 1) < 6.999 && progc(i) >= 6.999) lag_end = std::max(lag_end, progc(i) - prog(i));
        }
      }
    }
  }
  const bool v25 = cap46 >= 100.0 && r100_46 >= 97.0;
  const bool ok = cap67 >= 100.0 && r100_mid >= 97.0;
  if (pass) *pass = ok;
  if (cap_out) *cap_out = cap46;
  if (cap7_out) *cap7_out = cap67;
  char b[1000];
  std::snprintf(b, sizeof b, "{\"case\": \"%s\", \"dir_deg\": %.0f, \"V\": %.1f, \"cap_rate_centre_dps\": %.1f, \"cap_rate_4_to_6deg_dps\": %.1f, "
                "\"cap_rate_6p25_to_6p75deg_dps\": %.1f, \"ramp100_rate_mid_dps\": %.1f, \"ramp100_cmd_rate_mid_dps\": %.1f, "
                "\"ramp100_rate_4_to_6deg_dps\": %.1f, \"ramp100_cmd_rate_4_to_6deg_dps\": %.1f, \"ramp100_lag_mid_deg\": %.2f, \"ramp100_lag_end_deg\": %.2f, "
                "\"v25_ramp_term_pass\": %s, \"meets_100\": %s}",
                tag.c_str(), dir_deg, sp.V, cap_c, cap46, cap67, r100_mid, c100_mid, r100_46, c100_46, lag_mid, lag_end, v25 ? "true" : "false", ok ? "true" : "false");
  return b;
}

static std::string tvcAxisCase(const std::string& tag, const ServoParams& sp, const Gimbal2Params& gp, int ax, const ecu::GimbalNotchCal* nc) {
  std::string o = "{\"case\": \"" + tag + "\", \"axis\": \"" + std::string(ax == 0 ? "alpha" : "beta") + "\", \"notch\": " + (nc ? "true" : "false");
  auto sel = [ax](const TvcRun& r, size_t i) { return ax == 0 ? r.a[i] : r.b[i]; };
  const double rl = ecu::cfg::kGimbalRateLimit_radps;
  for (double A : {0.1, 0.5, 1.0, 7.0}) {
    TvcRun r = tvcSim(sp, gp, [ax, A](double t, float* c) { c[0] = c[1] = 0; c[ax] = t > 0.2 ? static_cast<float>(A * D2R) : 0.0f; }, 0.8, 7, rl, nc);
    double th0 = 0; int n0 = 0; for (size_t i = 0; i < r.t.size(); ++i) if (r.t[i] > 0.1 && r.t[i] <= 0.2) { th0 += sel(r, i); ++n0; }
    th0 /= std::max(n0, 1);
    double t10 = NAN, t90 = NAN, pk = -1e9, ring = 0;
    for (size_t i = 0; i < r.t.size(); ++i) if (r.t[i] > 0.2) {
      const double p = (sel(r, i) - th0) / (A * D2R);
      if (std::isnan(t10) && p >= 0.1) t10 = r.t[i];
      if (std::isnan(t90) && p >= 0.9) t90 = r.t[i];
      pk = std::max(pk, p);
    }
    // residual oscillation after the command has settled (> 0.35 s): peak-to-peak of the engine minus the shaped command
    double lo = 1e9, hi = -1e9;
    for (size_t i = 0; i < r.t.size(); ++i) if (r.t[i] > 0.55) { const double e = sel(r, i) - (ax == 0 ? r.ca[i] : r.cb[i]); lo = std::min(lo, e); hi = std::max(hi, e); }
    ring = (hi - lo) * R2D;
    double fin = 0; int nf = 0; for (size_t i = 0; i < r.t.size(); ++i) if (r.t[i] > 0.6) { fin += sel(r, i); ++nf; }
    char b[460]; std::snprintf(b, sizeof b, ", \"step_%gdeg\": {\"rise_s\": %.4f, \"t90_s\": %.4f, \"overshoot_pct\": %.1f, \"increment_err_deg\": %.4f, "
                              "\"static_offset_before_deg\": %.4f, \"final_abs_err_deg\": %.4f, \"residual_pp_after_0p35s_deg\": %.4f}",
                              A, t90 - t10, t90 - 0.2, 100 * std::max(0.0, pk - 1), (fin / nf - th0) * R2D - A, th0 * R2D, fin / nf * R2D - A, ring);
    o += b;
  }
  {  // slew -7 -> +7 deg (rate limit as flown: 100 deg/s shaping)
    TvcRun r = tvcSim(sp, gp, [ax](double t, float* c) { c[0] = c[1] = 0; c[ax] = static_cast<float>((t < 0.4 ? -7 : 7) * D2R); }, 1.2, 9, rl, nc);
    double vmax = 0; for (size_t i = 1; i < r.t.size(); ++i) vmax = std::max(vmax, (sel(r, i) - sel(r, i - 1)) / 1e-3);
    double t_end = NAN; for (size_t i = 0; i < r.t.size(); ++i) if (r.t[i] > 0.4 && std::isnan(t_end) && sel(r, i) > 6.9 * D2R) t_end = r.t[i];
    double Fmax = 0; for (size_t i = 0; i < r.t.size(); ++i) Fmax = std::max(Fmax, std::max(std::fabs(r.Fa[i]), std::fabs(r.Fb[i])));
    char b[260]; std::snprintf(b, sizeof b, ", \"slew\": {\"max_rate_dps\": %.1f, \"t_14deg_s\": %.3f, \"rod_force_max_N\": %.1f, \"rod_length_err_max_um\": %.2f}",
                              vmax * R2D, t_end - 0.4, Fmax, r.len_err_max * 1e6);
    o += b;
  }
  std::string sw = ", \"sweep\": [";
  double bw = NAN, ph8 = NAN, g8 = NAN, gmax = 0, fmax = 0;
  bool first = true;
  for (double fz : {0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0, 22.0, 25.0, 30.0}) {
    const double A = 0.5 * D2R, T0 = 0.5, cyc = std::max(4.0, fz * 1.0);
    const double T = T0 + cyc / fz;
    TvcRun r = tvcSim(sp, gp, [=](double t, float* c) { c[0] = c[1] = 0; c[ax] = t > 0.1 ? static_cast<float>(A * std::sin(2 * M_PI * fz * (t - 0.1))) : 0.0f; }, T, 11, rl, nc);
    double sc = 0, ss = 0; int n = 0;
    for (size_t i = 0; i < r.t.size(); ++i) if (r.t[i] >= T0 && r.t[i] < T - 1e-9) {
      const double ph = 2 * M_PI * fz * (r.t[i] - 0.1);
      sc += sel(r, i) * std::cos(ph); ss += sel(r, i) * std::sin(ph); ++n;
    }
    const double amp = 2 * std::sqrt(sc * sc + ss * ss) / n, gain = amp / A, phase = std::atan2(sc, ss) * R2D;
    if (std::isnan(bw) && gain < 0.7071) bw = fz;
    if (fz == 8.0) { ph8 = phase; g8 = gain; }
    if (fz >= 10.0 && gain > gmax) { gmax = gain; fmax = fz; }
    char b[120]; std::snprintf(b, sizeof b, "%s{\"f_Hz\": %g, \"gain\": %.4f, \"phase_deg\": %.1f}", first ? "" : ", ", fz, gain, phase);
    sw += b; first = false;
  }
  sw += "]";
  char b[260]; std::snprintf(b, sizeof b, ", \"bw_first_f_below_-3dB_Hz\": %s, \"gain_8Hz\": %.3f, \"phase_8Hz_deg\": %.1f, \"gain_max_10_30Hz\": %.4f, \"f_gain_max_Hz\": %.0f",
                              std::isnan(bw) ? "\">30\"" : std::to_string(bw).c_str(), g8, ph8, gmax, fmax);
  o += sw + b;
  {  // resolution: 0.05 deg staircase
    TvcRun r = tvcSim(sp, gp, [ax](double t, float* c) { c[0] = c[1] = 0; c[ax] = static_cast<float>(std::floor(t / 0.3) * 0.05 * D2R); }, 3.0, 13, rl, nc);
    std::string rs = ", \"staircase_0p05deg\": [";
    for (int k = 1; k < 10; ++k) {
      double m = 0; int n = 0;
      for (size_t i = 0; i < r.t.size(); ++i) if (r.t[i] >= k * 0.3 + 0.2 && r.t[i] < (k + 1) * 0.3) { m += sel(r, i); ++n; }
      char c2[60]; std::snprintf(c2, sizeof c2, "%s%.4f", k > 1 ? ", " : "", m / n * R2D);
      rs += c2;
    }
    o += rs + "]";
  }
  return o + "}";
}
// v2.6 rocking-mode identification as B-TVC-1 does it: ECU TVC-test mode 2 (shaping filters bypassed), 0.3 deg sine on one axis,
// gain = engine encoder / shaped command (lock-in over whole cycles); the peak gives the mode the notch is tuned to.
struct ModeId { double f_peak = NAN, g_peak = NAN, g8 = NAN; std::string rows; };
static ModeId frfId(const ServoParams& sp, const Gimbal2Params& gp, int ax, double amp_deg = 0.3) {
  ModeId m; double best = 0; bool first = true;
  m.rows = "[";
  for (double f = 6.0; f <= 50.0 + 1e-9; f += (f < 14.0 ? 2.0 : 1.0)) {
    const double A = amp_deg * D2R, T0 = 0.4, cyc = std::max(6.0, f * 0.4), T = T0 + cyc / f;
    TvcRun r = tvcSim(sp, gp, [=](double t, float* c) { c[0] = c[1] = 0; c[ax] = t > 0.1 ? static_cast<float>(A * std::sin(2 * M_PI * f * (t - 0.1))) : 0.0f; },
                      T + 0.1, 23, ecu::cfg::kGimbalRateLimit_radps, nullptr, true);
    double sc = 0, ss = 0, cc = 0, cs = 0; int n = 0;
    for (size_t i = 0; i < r.t.size(); ++i) if (r.t[i] >= T0 && r.t[i] < T0 + cyc / f - 1e-9) {
      const double ph = 2 * M_PI * f * (r.t[i] - 0.1), y = ax == 0 ? r.a[i] : r.b[i], u = ax == 0 ? r.ca[i] : r.cb[i];
      sc += y * std::cos(ph); ss += y * std::sin(ph); cc += u * std::cos(ph); cs += u * std::sin(ph); ++n;
    }
    const double g = std::sqrt(sc * sc + ss * ss) / std::sqrt(cc * cc + cs * cs);
    const double ph = (std::atan2(sc, ss) - std::atan2(cc, cs)) * R2D;
    if (g > best) { best = g; m.f_peak = f; }
    if (std::fabs(f - 8.0) < 1e-9) m.g8 = g;
    char b[100]; std::snprintf(b, sizeof b, "%s{\"f_Hz\": %g, \"gain\": %.3f, \"phase_deg\": %.1f}", first ? "" : ", ", f, g, std::remainder(ph, 360.0));
    m.rows += b; first = false;
  }
  m.g_peak = best; m.rows += "]";
  return m;
}
static void scTvc() {
  J j;
  j.k("scenario").v("S7 TVC v2.6 (ENG-07: worst-direction slew at 7 deg >= 100 deg/s at the 7.4 V nominal plug, 6.6 V degraded accepted on the GNC MC; ENG-07d per-axis notch REQUIRED, LEAD 2026-10-12): as-built linkage mechanical.json v2 (levers 135/225 deg, r_e 53.47 mm, eye z -28 mm, horn 11.139 mm, rod 42.3 mm, n 4.8), firmware exact pushrod solve, 3-D pushrods in the plant, FEA structure per axis, servo rotor J_int 1.6e-3 kg m2 (estimate) and position-loop stiffness T_stall / PB (PB ASSUMED 2 deg nominal). v2.8.3: flight shaping = gnc.json v3 tracker 100 deg/s, 2000 deg/s2 + 50 rad/s low-pass (per-axis cases, vector, time history); capability rows: tracker off, no ECU rate limit");
  ServoParams sp; Gimbal2Params gp;
  ecu::GimbalNotchCal nc;
  {  // analytic + mode identification
    GimbalPlant2 g0(gp, sp, sp, 1);
    ServoParams s66 = sp; s66.V = 6.6;
    double m[2]; { double P[3], Pa[3], Pb[3]; g0.leverEye(0, 0, 0, P, Pa, Pb); m[0] = Pa[2] / gp.r_h; m[1] = Pb[2] / gp.r_h; }
    const double cap_axis_74 = 2 * sp.tstall() * std::fabs(m[0]), cap_axis_66 = 2 * s66.tstall() * std::fabs(m[0]);
    std::string ks = "[";
    bool first = true;
    for (double V : {6.6, 7.4}) for (double pb : {1.0, 2.0, 3.0}) {
      ServoParams s = sp; s.V = V; s.pb_rad = pb * D2R;
      char b[200]; std::snprintf(b, sizeof b, "%s{\"V\": %.1f, \"PB_deg\": %.0f, \"K_s_Nm_per_rad\": %.0f, \"f_alpha_Hz\": %.1f, \"f_beta_Hz\": %.1f}",
                                first ? "" : ", ", V, pb, s.tstall() / s.pb_rad, rockingModeHz(gp, s, 0), rockingModeHz(gp, s, 1));
      ks += b; first = false;
    }
    ks += "]";
    // modes vs servo stiffness K_s (output), J_int and structure: the B-TVC-1 gate is K_s >= ~100 N m/rad (LEAD)
    std::string tab = "[";
    first = true;
    for (double Ks : {58.0, 87.0, 100.0, 120.0, 174.0, 250.0}) for (double J : {0.76e-3, 1.6e-3, 2.7e-3}) for (int st = 0; st < 3; ++st) {
      ServoParams s = sp; s.J_int = J; s.pb_rad = s.tstall() / Ks;
      Gimbal2Params q = gp;
      const char* stn = st == 0 ? "centre" : (st == 1 ? "lowest_pose" : "structure_x2");
      if (st == 1) { q.K_struct[0] = mech::k_K_struct_min_Nm_per_rad[0]; q.K_struct[1] = mech::k_K_struct_min_Nm_per_rad[1]; }
      if (st == 2) { q.K_struct[0] *= 2; q.K_struct[1] *= 2; }
      char b[200]; std::snprintf(b, sizeof b, "%s{\"K_s\": %.0f, \"J_int\": %.2e, \"structure\": \"%s\", \"f_alpha_Hz\": %.1f, \"f_beta_Hz\": %.1f}",
                                first ? "" : ", ", Ks, J, stn, rockingModeHz(q, s, 0), rockingModeHz(q, s, 1));
      tab += b; first = false;
    }
    tab += "]";
    Gimbal2Params rigid = gp; rigid.flex = false;
    const ModeId ia = frfId(sp, gp, 0), ib = frfId(sp, gp, 1), ra = frfId(sp, rigid, 0);
    double gpa = 0, gpb = 0, gpr = 0;
    const double fpa = rockingPeakHz(gp, sp, 0, &gpa), fpb = rockingPeakHz(gp, sp, 1, &gpb), fpr = rockingPeakHz(rigid, sp, 0, &gpr);
    nc = autoNotchCal(SimConfig());
    char b[3200];
    std::snprintf(b, sizeof b, "{\"mixing_servo_per_engine_neutral\": %.4f, \"servo_angle_range_7deg\": [%.2f, %.2f], \"servo_stall_torque_7V4_Nm\": %.3f, \"servo_stall_torque_6V6_Nm\": %.3f, "
                  "\"axis_moment_capacity_neutral_7V4_Nm\": %.2f, \"axis_moment_capacity_neutral_6V6_Nm\": %.2f, \"hinge_linear_sum_MECH_Nm\": %.2f, "
                  "\"K_s_gate_100_PB_deg_7V4\": %.2f, \"K_s_gate_100_PB_deg_6V6\": %.2f, \"K_struct_centre\": [%.0f, %.0f], \"K_struct_lowest_pose\": [%.0f, %.0f], "
                  "\"k_chain_rod_N_per_m\": %.3e, \"I_kgm2\": [%.5f, %.5f], \"J_int_kgm2\": %.2e, \"modes_vs_PB_and_V\": %s, "
                  "\"mode_id_btvc1_sweep_nominal\": {\"alpha\": {\"sil_peak_Hz\": %.1f, \"sil_peak_gain\": %.2f, \"sil_gain_8Hz\": %.3f, \"linear_damped_peak_Hz\": %.1f, \"linear_damped_peak_gain\": %.2f, \"undamped_Hz\": %.2f}, "
                  "\"beta\": {\"sil_peak_Hz\": %.1f, \"sil_peak_gain\": %.2f, \"sil_gain_8Hz\": %.3f, \"linear_damped_peak_Hz\": %.1f, \"linear_damped_peak_gain\": %.2f, \"undamped_Hz\": %.2f}, "
                  "\"alpha_rigid_structure\": {\"sil_peak_Hz\": %.1f, \"sil_peak_gain\": %.2f, \"linear_damped_peak_Hz\": %.1f, \"undamped_Hz\": %.2f}}, "
                  "\"notch_cal_sil\": {\"alpha\": {\"f0_Hz\": %.2f, \"q\": %.2f, \"depth_dB\": %.1f}, \"beta\": {\"f0_Hz\": %.2f, \"q\": %.2f, \"depth_dB\": %.1f}}, "
                  "\"MECH_f_rock_servo_rigid_centre_Hz\": [%.1f, %.1f]}",
                  m[0], static_cast<double>(ecu::mech::kPsiRange_deg[0]), static_cast<double>(ecu::mech::kPsiRange_deg[1]), sp.tstall(), s66.tstall(), cap_axis_74, cap_axis_66, mech::k_hinge_linear_sum_Nm,
                  sp.tstall() / 100.0 * R2D, s66.tstall() / 100.0 * R2D, gp.K_struct[0], gp.K_struct[1], mech::k_K_struct_min_Nm_per_rad[0], mech::k_K_struct_min_Nm_per_rad[1],
                  gp.k_link, gp.I[0], gp.I[1], sp.J_int, ks.c_str(),
                  ia.f_peak, ia.g_peak, ia.g8, fpa, gpa, rockingModeHz(gp, sp, 0), ib.f_peak, ib.g_peak, ib.g8, fpb, gpb, rockingModeHz(gp, sp, 1),
                  ra.f_peak, ra.g_peak, fpr, rockingModeHz(rigid, sp, 0),
                  nc.ax[0].f0_Hz, nc.ax[0].q, nc.ax[0].depth_dB, nc.ax[1].f0_Hz, nc.ax[1].q, nc.ax[1].depth_dB,
                  mech::k_f_rock_mech_centre_Hz[0], mech::k_f_rock_mech_centre_Hz[1]);
    j.k("analytic").raw(b);
    j.k("modes_vs_Ks_Jint_structure").raw(tab);
    j.k("btvc1_sweep_alpha").raw(ia.rows); j.k("btvc1_sweep_beta").raw(ib.rows); j.k("btvc1_sweep_alpha_rigid_structure").raw(ra.rows);
    {  // amplitude dependence of the identified peak (servo loop nonlinearity: deadband, quantisation, drive saturation)
      std::string am = "[";
      bool f1 = true;
      for (double A : {0.05, 0.1, 0.2, 0.3, 0.6}) for (int ax = 0; ax < 2; ++ax) {
        const ModeId q = frfId(sp, gp, ax, A);
        char bb[160]; std::snprintf(bb, sizeof bb, "%s{\"amp_deg\": %.2f, \"axis\": \"%s\", \"peak_Hz\": %.0f, \"peak_gain\": %.2f, \"gain_8Hz\": %.3f}",
                                    f1 ? "" : ", ", A, ax ? "beta" : "alpha", q.f_peak, q.g_peak, q.g8);
        am += bb; f1 = false;
      }
      j.k("btvc1_sweep_amplitude_dependence").raw(am + "]");
      std::printf("S7 sweep amplitude dependence: %s]\n", am.c_str());
    }
    std::printf("S7 analytic: %s\n", b);
  }
  {  // ENG-07 slew capability on the as-built linkage, compared with Mechanical's table
    std::string cap = "[";
    bool first = true;
    double worst74 = 1e9, worst66 = 1e9; double wdir74 = 0, wdir66 = 0, w7_74 = 1e9, w7_66 = 1e9;
    for (double V : {6.6, 7.4, 7.6, 7.8, 8.4}) {
      std::vector<double> dirs = (V == 6.6 || V == 7.4) ? std::vector<double>{0, 45, 90, 135, 180, 225, 270, 315}
                                                        : std::vector<double>{mech::k_slew_worst_dir_deg};
      for (double dir : dirs) {
        ServoParams sv = sp; sv.V = V;
        char tg[80]; std::snprintf(tg, sizeof tg, "as built %.1f V dir %.0f", V, dir);
        bool ok = false; double c46 = 0, c67 = 0;
        const std::string row = tvcCapability(tg, sv, gp, dir, &ok, &c46, &c67);
        if (V == 7.4 && c46 < worst74) { worst74 = c46; wdir74 = dir; }
        if (V == 6.6 && c46 < worst66) { worst66 = c46; wdir66 = dir; }
        if (V == 7.4) w7_74 = std::min(w7_74, c67);
        if (V == 6.6) w7_66 = std::min(w7_66, c67);
        cap += (first ? "" : ", ") + row; first = false;
        std::printf("S7 capability: %s\n", row.c_str());
      }
    }
    j.k("slew_capability").raw(cap + "]");
    char b[1400];
    std::snprintf(b, sizeof b, "{\"sil_worst_4to6deg_7V4_dps\": %.1f, \"sil_worst_dir_7V4_deg\": %.0f, \"sil_worst_4to6deg_6V6_dps\": %.1f, \"sil_worst_dir_6V6_deg\": %.0f, "
                  "\"sil_worst_6p25to6p75deg_7V4_dps\": %.1f, \"sil_worst_6p25to6p75deg_6V6_dps\": %.1f, "
                  "\"MECH_worst_at_7deg_7V4_dps\": %.1f, \"MECH_worst_at_7deg_6V6_dps\": %.1f, \"MECH_worst_dir_deg\": %.0f, \"ENG07_7V4_pass_near_7deg\": %s, "
                  "\"note\": \"SIL load = MECH misalignment + floor side load along servo A (constant), servo torque-speed line, rotor J_int; MECH = 3.19 N m opposing at exactly 7 deg; both senses run (dir 45 = dir 225 reversed); SIL dir is the (alpha, beta) command direction, MECH dir its own convention; meets_100 (v2.6) = capability 6.25-6.75 deg >= 100 and mid-travel 100 deg/s ramp tracked >= 97 (v2.5 4-6 deg ramp term kept as v25_ramp_term_pass)\"}",
                  worst74, wdir74, worst66, wdir66, w7_74, w7_66, mech::k_slew_worst_dps[1], mech::k_slew_worst_dps[0], mech::k_slew_worst_dir_deg, w7_74 >= 100.0 ? "true" : "false");
    j.k("eng07").raw(b);
    std::printf("S7 ENG-07: %s\n", b);
  }
  std::string arr = "[" + tvcAxisCase("nominal 7.4 V, per-axis notch", sp, gp, 0, &nc) + ", " + tvcAxisCase("nominal 7.4 V, per-axis notch", sp, gp, 1, &nc);
  arr += ", " + tvcAxisCase("nominal 7.4 V, notch OFF (v2.5 behaviour)", sp, gp, 0, nullptr) + ", " + tvcAxisCase("nominal 7.4 V, notch OFF (v2.5 behaviour)", sp, gp, 1, nullptr);
  ServoParams s2 = sp; s2.V = 6.6; arr += ", " + tvcAxisCase("6.6 V degraded (notch tuned at 7.4 V)", s2, gp, 0, &nc);
  ServoParams s3 = sp; s3.deadband_us = 3.0; s3.backlash_rad = 0.5 * D2R; arr += ", " + tvcAxisCase("deadband 3 us, backlash 0.5 deg", s3, gp, 0, &nc);
  Gimbal2Params g4 = gp; g4.K_struct[1] = mech::k_K_struct_min_Nm_per_rad[1]; arr += ", " + tvcAxisCase("structure at the lowest FEA pose (beta -7 deg)", sp, g4, 1, &nc);
  Gimbal2Params g5 = gp; g5.k_hose = mech::k_K_hose_Nm_per_rad[0]; g5.M_fric = 0.5; arr += ", " + tvcAxisCase("soft hose, pivot friction 0.5 N m", sp, g5, 1, &nc);
  Gimbal2Params g6 = gp; g6.I[0] = mech::k_I_dry_kgm2[0] + mech::k_I_ring_alpha_kgm2; g6.I[1] = mech::k_I_dry_kgm2[1]; arr += ", " + tvcAxisCase("dry inertia", sp, g6, 0, &nc);
  ServoParams s7 = sp; s7.J_int = 2.7e-3; arr += ", " + tvcAxisCase("J_int 2.7e-3 (estimate upper end)", s7, gp, 0, &nc);
  ServoParams s8 = sp; s8.pb_rad = 3.0 * D2R; arr += ", " + tvcAxisCase("PB 3 deg (K_s 58 N m/rad, below the 100 gate)", s8, gp, 1, &nc);
  arr += "]";
  j.k("cases").raw(arr);
  {  // vector checks: 7 deg circle (servo pulses, stop contact, rod length) and a 10/10 deg command (norm clamp)
    TvcRun r = tvcSim(sp, gp, [](double t, float* c) { const double th = 2 * M_PI * 0.5 * t; c[0] = static_cast<float>(7 * D2R * std::cos(th)); c[1] = static_cast<float>(7 * D2R * std::sin(th)); }, 2.5, 19, ecu::cfg::kGimbalRateLimit_radps, &nc);
    double usmin = 1e9, usmax = -1e9, rmax = 0;
    for (size_t i = 500; i < r.t.size(); ++i) { usmin = std::min({usmin, r.usa[i], r.usb[i]}); usmax = std::max({usmax, r.usa[i], r.usb[i]});
      rmax = std::max(rmax, std::hypot(r.a[i], r.b[i])); }
    TvcRun q = tvcSim(sp, gp, [](double t, float* c) { c[0] = c[1] = t > 0.1 ? static_cast<float>(10 * D2R) : 0.0f; }, 0.8, 21, ecu::cfg::kGimbalRateLimit_radps, &nc);
    double qn = 0; for (size_t i = 600; i < q.t.size(); ++i) qn = std::max(qn, std::hypot(q.a[i], q.b[i]));
    char b[500]; std::snprintf(b, sizeof b, "{\"circle_7deg_0p5Hz\": {\"pulse_min_us\": %.1f, \"pulse_max_us\": %.1f, \"max_vector_deg\": %.3f, \"stop_contact_ms\": %d, \"rod_length_err_max_um\": %.2f}, "
                  "\"cmd_10_10deg\": {\"settled_vector_norm_deg\": %.3f, \"stop_contact_ms\": %d}}", usmin, usmax, rmax * R2D, r.stop_ms, r.len_err_max * 1e6, qn * R2D, q.stop_ms);
    j.k("vector").raw(b);
    std::printf("S7 vector: %s\n", b);
  }
  writeFile(OUT + "/S7_tvc.json", j.str());
  TvcRun r = tvcSim(sp, gp, [](double t, float* c) {
    c[1] = 0;
    c[0] = static_cast<float>(t < 0.4 ? 0.0 : (t < 1.2 ? 1.0 * D2R : (t < 2.0 ? -7 * D2R : (t < 2.8 ? 7 * D2R : 0.5 * D2R * std::sin(2 * M_PI * 8.0 * (t - 2.8))))));
    if (t >= 3.6) { const double th = 2 * M_PI * 0.5 * (t - 3.6); c[0] = static_cast<float>(7 * D2R * std::cos(th)); c[1] = static_cast<float>(7 * D2R * std::sin(th)); }
  }, 5.6, 17, ecu::cfg::kGimbalRateLimit_radps, &nc);
  std::ofstream f(OUT + "/S7_tvc.csv");
  f << "t,cmd_alpha_deg,alpha_deg,cmd_beta_deg,beta_deg,us_A,us_B,F_rod_A,F_rod_B\n";
  for (size_t i = 0; i < r.t.size(); ++i)
    f << r.t[i] << "," << r.ca[i] * R2D << "," << r.a[i] * R2D << "," << r.cb[i] * R2D << "," << r.b[i] * R2D << "," << r.usa[i] << "," << r.usb[i] << "," << r.Fa[i] << "," << r.Fb[i] << "\n";
  std::printf("S7 TVC: %s\n", arr.substr(0, 1500).c_str());
}

// ------------------------------------------------------------------------------------------ S8 line priming (v2.2)
// COMB v2 rule (lead relay 2026-10-12): opening the MV into a dead-ended, gas-filled line compresses the gas to 600-900 K.
// If P_feed < 0.5 P_tank: pintle to a 0.10 mm bleed lift, then open the MV over >= 0.3 s; a primed line keeps the normal
// sequence. The plant's gas pocket is adiabatic (no wall heat transfer, no liquid inertia): T_gas is an indicator only.
struct PrimeCase { std::string name; std::function<void(Sim&)> setup; double t_prep; double t_end; int expect; };
static void scPriming() {
  auto relight = [](Sim& s) {   // burn 1.4-3.0 s, coast (MV held, closes at +30 s), relight at 34 s, shut down at 36 s
    s.schedule.push_back({3.0, Cmd::SHUTDOWN, 0}); s.schedule.push_back({34.0, Cmd::RELIGHT, 0}); s.schedule.push_back({36.0, Cmd::SHUTDOWN, 0});
  };
  std::vector<PrimeCase> cases = {
      {"first_start_empty_line_v22_rule", [](Sim& s) { s.schedule.push_back({3.0, Cmd::SHUTDOWN, 0}); }, 0.80, 3.5, 0},
      {"first_start_empty_line_v21_sequence_for_comparison", [](Sim& s) { s.force_fast_prime = true; s.schedule.push_back({3.0, Cmd::SHUTDOWN, 0}); }, 0.80, 3.5, 0},
      {"first_start_pintle_stuck_on_seat", [](Sim& s) { s.pintle_jam_at = 0.0; }, 0.80, 2.0, (int)ecu::Abort::PREPRESS_FAIL},
      {"relight_mv_closed_line_still_primed", relight, 34.0, 36.5, 0},
      {"relight_line_vented_before_relight", [&](Sim& s) { relight(s); s.eng.P.line_vent_at = 33.5; }, 34.0, 36.5, 0},
  };
  J j;
  j.k("scenario").v("S8 line priming (COMB v2 rule via lead 2026-10-12): pad sequence ARM 0.05 s, PREPRESS 0.80 s, IGNITE 1.40 s, 300 N; "
                    "relight cases: SHUTDOWN 3.0 s (MV closed in the coast, v2.6 rule b), RELIGHT 34 s: v2.8 primed segment -> direct relight "
                    "(no bleed), vented segment -> PREPRESS bleed + ramp. Gas pocket adiabatic (indicator only)");
  std::string arr = "[";
  int pass = 0;
  for (size_t i = 0; i < cases.size(); ++i) {
    const PrimeCase& pc = cases[i];
    Sim s(nominal(81 + i));
    s.schedule = padSequence(1.40);
    s.thrust_cmd = [](double) { return 300.0; };
    pc.setup(s);
    std::sort(s.schedule.begin(), s.schedule.end(), [](const StateCmd& a, const StateCmd& b) { return a.t < b.t; });
    s.runUntil(pc.t_prep - 0.0005, [](const Sim&) { return false; });
    s.eng.gas_T_max = 0; s.eng.gas_p_max = 0; s.eng.dpfeed_dt_max = 0;     // maxima of this priming only
    const double pf0 = s.eng.p_feed, pt0 = s.eng.P_tank;
    s.run(pc.t_end);
    const auto& r = s.rec();
    s.writeCsv(OUT + "/S8_" + pc.name + ".csv");
    const double t0 = pc.t_prep;
    const double t_bleed = firstTime(r, t0, [](const Rec& x) { return x.x >= 0.05e-3; }) - t0;
    const double t_crack = firstTime(r, t0, [](const Rec& x) { return x.mv >= 0.02; }) - t0;
    const double t_full = firstTime(r, t0, [](const Rec& x) { return x.mv >= 0.98; }) - t0;
    const double t_primed = firstTime(r, t0, [](const Rec& x) { return x.pfeed > 0.8 * x.ptank; }) - t0;
    const double t_ign = firstTime(r, t0, [](const Rec& x) { return x.state == (int)State::IGNITION; }) - t0;
    const double t_f90 = firstTime(r, t0, [](const Rec& x) { return x.F >= 0.9 * 300.0; }) - t0;
    double mv_max = 0; for (const Rec& x : r) if (x.t >= t0) mv_max = std::max(mv_max, x.mv);
    int cause = 0; for (const Rec& x : r) if (x.t >= t0 - 0.5 && x.abort && !cause) cause = x.abort;
    std::printf("S8 jam events %d kind %d noprog max %.0f ms | ", s.jam_events, (int)s.out.pintle_fault_kind, s.noprog_max * 1e3);
    const bool slow = std::isfinite(t_bleed) && std::isfinite(t_crack) && t_bleed < t_crack;
    bool ok = cause == pc.expect;
    if (pc.name.find("v22_rule") != std::string::npos || pc.name.find("vented") != std::string::npos)
      ok = ok && slow && (t_full - t_crack) >= 0.30 * (40.0 / 45.0) - 0.005;   // valve full at 40 of the 45 deg ramp
    if (pc.name.find("still_primed") != std::string::npos) ok = ok && !(std::isfinite(t_bleed) && t_bleed < t_crack);
    if (pc.name.find("stuck") != std::string::npos) ok = ok && mv_max < 0.02;
    pass += ok;
    char b[1200];
    std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"p_feed_over_p_tank_at_prepress\": %.3f, \"slow_sequence\": %s, \"t_bleed_s\": %.4f, \"t_mv_crack_s\": %.4f, "
                  "\"t_mv_full_s\": %.4f, \"mv_crack_to_full_s\": %.4f, \"t_feed_primed_s\": %.4f, \"t_ignition_state_s\": %.4f, \"t_F90pct_300N_s\": %.4f, "
                  "\"gas_T_max_K\": %.0f, \"gas_p_max_Pa\": %.0f, \"dpfeed_dt_max_Pa_per_s\": %.3e, \"mv_max\": %.3f, \"abort\": %d, \"abort_name\": \"%s\", \"expect\": %d, \"pass\": %s}",
                  i ? ", " : "", pc.name.c_str(), pf0 / pt0, slow ? "true" : "false", t_bleed, t_crack, t_full, t_full - t_crack, t_primed, t_ign, t_f90,
                  s.eng.gas_T_max, s.eng.gas_p_max, s.eng.dpfeed_dt_max, mv_max, cause, ecu::abortName(static_cast<ecu::Abort>(cause)), pc.expect, ok ? "true" : "false");
    std::string sb(b);
    for (auto p = sb.find("nan"); p != std::string::npos; p = sb.find("nan")) sb.replace(p, 3, "null");
    arr += sb;
    std::printf("S8 %-50s pf/pt %.2f slow %d bleed %.0f ms crack %.0f full %.0f ms primed %.0f ms IGN %.0f ms F90 %.0f ms gasTmax %.0f K pmax %.1f bar abort %d %s\n",
                pc.name.c_str(), pf0 / pt0, slow, t_bleed * 1e3, t_crack * 1e3, t_full * 1e3, t_primed * 1e3, t_ign * 1e3, t_f90 * 1e3, s.eng.gas_T_max,
                s.eng.gas_p_max / 1e5, cause, ok ? "PASS" : "FAIL");
  }
  arr += "]";
  j.k("cases").raw(arr);
  j.k("passed").v(pass); j.k("total").v(static_cast<double>(cases.size()));
  writeFile(OUT + "/S8_priming.json", j.str());
}

// per-start epochs from IGNITION entry te (E0): rule, W, direct path, E1 (lift command), torch confirmed / valves closed, plant light,
// E2 (RUN = Pc confirmed), sparks, pintle lift max while unlit, unignited N2O of the start
struct StartM { double te = NAN, w = NAN, e1 = NAN, ok = NAN, tc = NAN, lit = NAN, e2 = NAN, xmax = 0, ox = NAN; int rule = 0, direct = 0, sparks = 0; };
static StartM startM(const Sim& s, const std::vector<Rec>& r, size_t k) {
  StartM m;
  if (k >= s.ign_entry_t.size()) return m;
  m.te = s.ign_entry_t[k];
  const double tn = k + 1 < s.ign_entry_t.size() ? s.ign_entry_t[k + 1] : 1e9;
  bool prev = false, rule_set = false;
  for (const Rec& x : r) {
    if (x.t < m.te || x.t >= tn) continue;
    if (!rule_set && x.t >= m.te + 0.0015 && x.state == (int)State::IGNITION) { m.w = x.ign_check; m.rule = x.ign_rule; m.direct = x.relight_direct; rule_set = true; }
    if (std::isnan(m.e1) && x.ign_lift_t >= 0.0) m.e1 = x.ign_lift_t;
    if (std::isnan(m.ok) && x.torch_ok) m.ok = x.t - m.te;
    if (std::isnan(m.tc) && x.torch_closed) m.tc = x.t - m.te;
    if (std::isnan(m.lit) && x.ignited) m.lit = x.t - m.te;
    if (std::isnan(m.e2) && x.state == (int)State::RUN) m.e2 = x.t - m.te;
    if (x.state == (int)State::IGNITION) { if (x.spark && !prev) ++m.sparks; prev = x.spark; if (!x.ignited) m.xmax = std::max(m.xmax, x.x); }
  }
  m.ox = k < s.ox_unlit_starts.size() ? s.ox_unlit_starts[k] : NAN;
  return m;
}
// ------------------------------------------------------------------------------------------ S9 Pc transducer (v2.6, OI-6)
// Lead OI-6 (2026-10-12): >= 70 bar class transducer (v2.6 baseline 070BG 0-70 bar g); resolution at the 12.5 % floor for the Pc loop; Pc resolved cleanly at the
// 3 bar ignition rule. The ASSUMED transducer noise (0.05 % FS per 4 kSPS frame) is swept; B-PC-1 measures the real value.
static void scPcXdcr() {
  J j;
  j.k("scenario").v("S9 Pc transducer TE M3234-000005-070BG (0-70 bar g; v2.6 OI-6 baseline, 01KPG alternate) on the ADS131M04 chain (OI-6): (A) Pc-loop noise sensitivity on the "
                    "S3 deep-end staircase 62.5-112.5 N; (B) unlit cold flow (v2.7: torch lit and confirmed, main never lights): false-light margin under noise, a 50 Hz "
                    "spike train and a +1.03 bar post-zero bias; (C) light-detection latency after the plant ignites; (D) post-zero "
                    "bias on the floor staircase; (E) sense-line step amplification at the transducer");
  j.k("noise_model").v("Gaussian, sigma at the 1 kHz decimated sample = 0.5 x pc_noise (4:1 average of 4 kSPS frames); nominal "
                       "pc_noise 3450 Pa = 0.05 % FS ASSUMED (M3200 datasheet gives no noise figure)");
  // (A) noise sweep, same seed (plant and servo draws identical; only the Pc noise amplitude differs)
  const double mult[6] = {0, 1, 2, 4, 8, 16};
  std::string arrA = "[";
  for (int i = 0; i < 6; ++i) {
    SimConfig c = nominal(41); c.pc_noise = 3450.0 * mult[i];
    DeepWorst w; char tag[32]; std::snprintf(tag, sizeof tag, "noise_x%.0f", mult[i]);
    // the FC repeats an IGNITE the ECU refused (OI-12 vented check on the filtered Pc): every 50 ms up to 1 s
    deepRun(c, tag, "S9_deep_", &w, [](Sim& s) { for (int k = 1; k <= 20; ++k) s.schedule.push_back({1.40 + 0.05 * k, Cmd::IGNITE, 0}); });
    char b[400];
    std::snprintf(b, sizeof b, "%s{\"noise_mult\": %.0f, \"sigma_1kHz_Pa\": %.0f, \"worst_abs_err_N\": %.3f, \"worst_pp_N\": %.3f, "
                  "\"worst_step_error_N\": %.3f, \"worst_pintle_us_pp\": %.2f, \"ignite_refused\": %d}", i ? ", " : "", mult[i], 0.5 * c.pc_noise,
                  w.err, w.pp, w.step, w.us_pp, w.refused);
    arrA += b;
  }
  arrA += "]";
  j.k("A_noise_sweep_deep_staircase").raw(arrA);
  // (B) unlit cold flow at the ignition lift: must end in NO_IGNITION, never RUN. v2.7: the torch lights and is confirmed, the MAIN
  // never lights (ign_delay 99 s). v2.6 used a torch that never lights; since the v2.7 flame gate that case aborts TORCH_FAULT at
  // 0.101 s before any pintle opening, so it no longer exercises the cold-flow false-light margin (the first v2.7 run showed it: 5 FAIL)
  struct UCase { const char* name; double mult, spike_Pa, period, len, bias_Pa; };
  const UCase uc[5] = {{"unlit_noise_x1", 1, 0, 0, 0, 0}, {"unlit_noise_x8", 8, 0, 0, 0, 0}, {"unlit_noise_x16", 16, 0, 0, 0, 0},
                       {"unlit_spike_train_20bar_2ms_50Hz", 1, 20.0e5, 0.020, 0.002, 0},
                       {"unlit_bias_plus_1p034bar_TEB", 1, 0, 0, 0, 1.034e5}};
  std::string arrB = "[";
  for (int i = 0; i < 5; ++i) {
    SimConfig c = nominal(71); c.pc_noise = 3450.0 * uc[i].mult; c.pc_nl_bias = uc[i].bias_Pa;
    Sim s(c);
    s.schedule = padSequence(1.40);
    s.thrust_cmd = [](double) { return 300.0; };
    s.eng.P.ign_delay = 99.0;
    if (uc[i].spike_Pa != 0) { s.pc_spike_at = 1.40; s.pc_spike_end = 2.40; s.pc_spike_period = uc[i].period; s.pc_spike_len = uc[i].len; s.pc_spike_Pa = uc[i].spike_Pa; }
    s.run(3.0);
    s.writeCsv(OUT + "/S9_" + uc[i].name + ".csv");
    int cause = 0; bool ran = false; double t_ign = NAN, t_ab = NAN, pf_max = 0, pc_max = 0;
    for (const Rec& x : s.rec()) {
      if (x.state == (int)State::RUN) ran = true;
      if (x.state == (int)State::IGNITION) { if (std::isnan(t_ign)) t_ign = x.t; pf_max = std::max(pf_max, x.Pc_meas); pc_max = std::max(pc_max, x.Pc); }
      if (x.abort && std::isnan(t_ab)) { cause = x.abort; t_ab = x.t; }
    }
    // v2.7: the safety property is "never RUN on an unlit chamber". Under the 20 bar spike train the torch gate's Pc interlock
    // (filtered Pc < 1 bar g while confirming) blocks the flame confirmation -> TORCH_FAULT before the pintle step: fail-safe, an
    // availability cost only if spark EMI of that size were real (B-IGN measures the Pc channel during the spark train)
    const bool ok = !ran && (cause == (int)ecu::Abort::NO_IGNITION || cause == (int)ecu::Abort::TORCH_FAULT);
    char b[500];
    std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"sigma_1kHz_Pa\": %.0f, \"cause\": \"%s\", \"entered_RUN\": %s, \"ign_to_abort_s\": %.4f, "
                  "\"plant_Pc_max_unlit_abs_Pa\": %.0f, \"filtered_Pc_max_abs_Pa\": %.0f, \"margin_to_3bar_Pa\": %.0f, \"pass\": %s}",
                  i ? ", " : "", uc[i].name, 0.5 * c.pc_noise, ecu::abortName(static_cast<ecu::Abort>(cause)), ran ? "true" : "false",
                  t_ab - t_ign, pc_max, pf_max, ecu::cfg::kIgnitionDetectAbs_Pa - pf_max, ok ? "true" : "false");
    std::printf("S9 %-36s cause %s, RUN %s, plant Pc max %.2f bar, filtered max %.2f bar abs %s\n", uc[i].name,
                ecu::abortName(static_cast<ecu::Abort>(cause)), ran ? "yes" : "no", pc_max / 1e5, pf_max / 1e5, ok ? "PASS" : "FAIL");
    arrB += b;
  }
  arrB += "]";
  j.k("B_unlit_cold_flow").raw(arrB);
  // (C) light detection after the plant ignites (pad start, 300 N)
  struct LCase { const char* name; double mult, bias_Pa; };
  const LCase lc[4] = {{"lit_noise_x1", 1, 0}, {"lit_noise_x8", 8, 0}, {"lit_bias_minus_1p034bar_TEB", 1, -1.034e5}, {"lit_bias_plus_1p034bar_TEB", 1, 1.034e5}};
  std::string arrC = "[";
  for (int i = 0; i < 4; ++i) {
    SimConfig c = nominal(81); c.pc_noise = 3450.0 * lc[i].mult; c.pc_nl_bias = lc[i].bias_Pa;
    Sim s(c);
    s.schedule = padSequence(1.40);
    s.thrust_cmd = [](double) { return 300.0; };
    s.run(2.6);
    double t_run = NAN, t_ign = NAN, pc_at_run = NAN; int cause = 0;
    for (const Rec& x : s.rec()) {
      if (x.state == (int)State::IGNITION && std::isnan(t_ign)) t_ign = x.t;
      if (x.state == (int)State::RUN && std::isnan(t_run)) { t_run = x.t; pc_at_run = x.Pc; }
      if (x.abort && !cause) cause = x.abort;
    }
    const bool ok = std::isfinite(t_run) && cause == 0;
    char b[500];
    std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"sigma_1kHz_Pa\": %.0f, \"bias_Pa\": %.0f, \"ign_to_plant_lit_s\": %.4f, \"plant_lit_to_RUN_s\": %.4f, "
                  "\"plant_Pc_at_RUN_abs_Pa\": %.0f, \"abort\": \"%s\", \"pass\": %s}", i ? ", " : "", lc[i].name, 0.5 * c.pc_noise, lc[i].bias_Pa,
                  s.first_lit_t - t_ign, t_run - s.first_lit_t, pc_at_run, ecu::abortName(static_cast<ecu::Abort>(cause)), ok ? "true" : "false");
    std::printf("S9 %-36s plant lit +%.0f ms after IGNITION, RUN +%.1f ms after plant light (Pc %.2f bar abs) %s\n", lc[i].name,
                (s.first_lit_t - t_ign) * 1e3, (t_run - s.first_lit_t) * 1e3, pc_at_run / 1e5, ok ? "PASS" : "FAIL");
    arrC += b;
  }
  arrC += "]";
  j.k("C_light_detection").raw(arrC);
  // (F) v2.8 final: light-detection margin at the v2.8 ignition lift (0.2039 mm, cold-flow defined; v2.5-v2.7 0.301 mm). The v2.8 draft run
  // lost the lit_bias_minus_1p034bar_TEB case (NO_IGNITION: the chamber lit at the lift sits near the 3.0 bar abs rule). Sweep of the
  // post-zero negative bias (same error shape as (D)) to find where detection is lost; plant lit steady Pc at the lift for reference.
  {
    double pc_ss = NAN, mo_ss = NAN, mf_ss = NAN, F_ss = NAN;
    { SimConfig c = nominal(81); Sim s(c); s.eng.steadyState(c.eng.T_tank0, ecu::cfg::kIgnLiftTab_m[0], &pc_ss, &mo_ss, &mf_ss, &F_ss); }
    const double bsw[8] = {-0.10e5, -0.20e5, -0.30e5, -0.40e5, -0.50e5, -0.60e5, -0.80e5, -1.034e5};
    std::string arrF = "[";
    double last_ok = 0.0, first_fail = NAN;
    for (int i = 0; i < 8; ++i) {
      SimConfig c = nominal(81); c.pc_nl_bias = bsw[i];
      Sim s(c);
      s.schedule = padSequence(1.40);
      s.thrust_cmd = [](double) { return 300.0; };
      s.run(2.6);
      double t_run = NAN, pmax_meas = 0; int cause = 0;
      for (const Rec& x : s.rec()) {
        if (x.state == (int)State::RUN && std::isnan(t_run)) t_run = x.t;
        if (x.state == (int)State::IGNITION) pmax_meas = std::max(pmax_meas, x.Pc_meas);
        if (x.abort && !cause) cause = x.abort;
      }
      const bool ok = std::isfinite(t_run) && cause == 0;
      if (ok && std::isnan(first_fail)) last_ok = bsw[i];
      if (!ok && std::isnan(first_fail)) first_fail = bsw[i];
      const StartM m = startM(s, s.rec(), 0);
      const double lit_e1 = s.first_lit_t - (m.te + m.e1);   // plant light after the lift command
      char b[400];
      std::snprintf(b, sizeof b, "%s{\"bias_Pa\": %.0f, \"detected\": %s, \"abort\": \"%s\", \"Pc_meas_max_in_IGNITION_abs_Pa\": %.0f, \"E1_to_plant_light_s\": %.4f, "
                    "\"E1_to_E2_s\": %.4f, \"W_s\": %.3f}", i ? ", " : "", bsw[i], ok ? "true" : "false", ecu::abortName(static_cast<ecu::Abort>(cause)), pmax_meas,
                    lit_e1, m.e2 - m.e1, m.w);
      arrF += b;
      std::printf("S9 F light detection with post-zero bias %+.2f bar: %s (abort %s), measured Pc max in IGNITION %.2f bar abs, plant light E1+%.3f s, E2 E1+%.3f s (W %.2f s)\n",
                  bsw[i] / 1e5, ok ? "detected" : "NOT detected", ecu::abortName(static_cast<ecu::Abort>(cause)), pmax_meas / 1e5, lit_e1, m.e2 - m.e1, m.w);
    }
    arrF += "]";
    char h[400];
    std::snprintf(h, sizeof h, "{\"ign_lift_m\": %.4e, \"plant_lit_steady_Pc_at_lift_abs_Pa\": %.0f, \"plant_lit_steady_F_at_lift_N\": %.1f, \"detect_threshold_abs_Pa\": %.0f, "
                  "\"largest_negative_bias_detected_Pa\": %.0f, \"first_negative_bias_lost_Pa\": %.0f, \"cases\": ", ecu::cfg::kIgnLiftTab_m[0], pc_ss, F_ss,
                  ecu::cfg::kIgnitionDetectAbs_Pa, last_ok, first_fail);
    j.k("F_light_detection_bias_sweep").raw(std::string(h) + arrF + "}");
    std::printf("S9 F lit steady Pc at the %.4f mm lift %.2f bar abs (F %.0f N), rule %.2f bar abs: detection kept down to %+.2f bar, lost at %+.2f bar\n",
                ecu::cfg::kIgnLiftTab_m[0] * 1e3, pc_ss / 1e5, F_ss, ecu::cfg::kIgnitionDetectAbs_Pa / 1e5, last_ok / 1e5, first_fail / 1e5);
  }
  // (D) post-zero bias (zero drift after the ARMED auto-zero, or BFSL/TEB terms) on the deep staircase
  // error shape pc_nl_bias * min(1, p_g / 1 bar): zero at 0 bar g (the ARMED auto-zero and the OI-12 vented check are unaffected)
  const double bias[4] = {0.345e5, -0.345e5, 1.034e5, -1.034e5};
  const char* btag[4] = {"bias_plus_0p345bar_2xBFSL", "bias_minus_0p345bar_2xBFSL", "bias_plus_1p034bar_TEB", "bias_minus_1p034bar_TEB"};
  std::string arrD = "[";
  for (int i = 0; i < 4; ++i) {
    SimConfig c = nominal(41); c.pc_nl_bias = bias[i];
    DeepWorst w;
    const double bb = bias[i];
    deepRun(c, btag[i], "S9_deep_", &w);
    char b[400];
    std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"bias_Pa\": %.0f, \"worst_abs_err_N\": %.3f, \"worst_pp_N\": %.3f, \"worst_step_error_N\": %.3f}",
                  i ? ", " : "", btag[i], bb, w.err, w.pp, w.step);
    arrD += b;
  }
  arrD += "]";
  j.k("D_bias_deep_staircase").raw(arrD);
  // (E) sense line + transducer lag: chamber step 1 -> 40 bar abs with a linear rise over tr; peak at the diaphragm / final
  std::string arrE = "[";
  const double trs[7] = {0.0, 0.5e-3, 1.0e-3, 2.0e-3, 3.0e-3, 5.0e-3, 10.0e-3};
  auto stepPeak = [](bool legacy, double tr, double p1) {
    SimConfig c = nominal(1); c.sense.legacy_v21 = legacy;
    SenseLine L(c.sense); L.init(101325.0);
    double x = 101325.0, pk = 0; const double dt = 25e-6;
    for (double t = 0; t < 0.08; t += dt) {
      const double pin = tr > 0 ? 101325.0 + (p1 - 101325.0) * std::min(1.0, t / tr) : p1;
      x += (L.step(dt, pin) - x) * dt / c.pc_tau;
      pk = std::max(pk, x);
    }
    return pk;
  };
  for (int i = 0; i < 7; ++i) {
    const double p1 = 40.0e5, pk = stepPeak(false, trs[i], p1), pl = stepPeak(true, trs[i], p1);
    const double p63 = 63.08e5, pk63 = stepPeak(false, trs[i], p63);
    char b[400];
    std::snprintf(b, sizeof b, "%s{\"rise_s\": %.4f, \"v26_peak_40bar_abs_Pa\": %.0f, \"v26_gain_gauge\": %.3f, \"v26_peak_63bar_abs_Pa\": %.0f, "
                  "\"legacy_v21_peak_40bar_abs_Pa\": %.0f, \"legacy_v21_gain_gauge\": %.3f}", i ? ", " : "", trs[i], pk, (pk - 101325.0) / (p1 - 101325.0),
                  pk63, pl, (pl - 101325.0) / (p1 - 101325.0));
    arrE += b;
    std::printf("S9 sense line step 1->40 bar, rise %4.1f ms: transducer peak v2.6 %6.1f bar abs (x%.2f of the gauge step; 63 bar step -> %.1f), "
                "legacy v2.1 %7.1f bar (x%.2f)\n", trs[i] * 1e3, pk / 1e5, (pk - 101325.0) / (p1 - 101325.0), pk63 / 1e5, pl / 1e5,
                (pl - 101325.0) / (p1 - 101325.0));
  }
  arrE += "]";
  // small-signal frequency response at 25 bar mean, 1 % ripple: resonance of both formulations (must agree)
  std::string arrF = "[";
  for (int lg = 0; lg < 2; ++lg) {
    double fbest = 0, gbest = 0;
    for (double f = 60; f <= 400; f += 2) {
      SimConfig c = nominal(1); c.sense.legacy_v21 = lg == 1;
      SenseLine L(c.sense); const double Pm = 25.0e5, A = 0.01 * Pm, dt = 25e-6; L.init(Pm);
      const double Ts = std::max(0.15, 30.0 / f), Tm = std::max(0.1, 15.0 / f);
      double sc = 0, ss = 0; int n = 0;
      for (double t = 0; t < Ts + Tm; t += dt) {
        const double po = L.step(dt, Pm + A * std::sin(2 * M_PI * f * t));
        if (t >= Ts) { sc += (po - Pm) * std::cos(2 * M_PI * f * t); ss += (po - Pm) * std::sin(2 * M_PI * f * t); ++n; }
      }
      const double g = 2 * std::sqrt(sc * sc + ss * ss) / n / A;
      if (g > gbest) { gbest = g; fbest = f; }
    }
    char b[200];
    std::snprintf(b, sizeof b, "%s{\"model\": \"%s\", \"f_peak_Hz\": %.0f, \"gain_peak\": %.2f}", lg ? ", " : "", lg ? "legacy_v21" : "v2.6", fbest, gbest);
    arrF += b;
    std::printf("S9 sense line small-signal resonance (25 bar, 1 %% ripple) %s: %.0f Hz, gain %.2f\n", lg ? "legacy v2.1" : "v2.6", fbest, gbest);
  }
  arrF += "]";
  j.k("E_sense_line_small_signal").raw(arrF);
  {
    SimConfig c = nominal(1); SenseLine L(c.sense);
    char b[300];
    std::snprintf(b, sizeof b, "{\"L_m\": %.3f, \"ID_m\": %.5f, \"V_end_m3\": %.2e, \"T_K\": %.0f, \"sound_speed_mps\": %.1f, \"tau_xdcr_s\": %.4f}",
                  c.sense.L, c.sense.ID, c.sense.V_end, c.sense.T, L.c(), c.pc_tau);
    j.k("E_sense_line_params").raw(b);
  }
  j.k("E_sense_line_step").raw(arrE);
  writeFile(OUT + "/S9_pc_transducer.json", j.str());
}

// ------------------------------------------------------------------------------------------ S10 relight path and windows (v2.8)
// LEAD 2026-10-13 decisions (v2.8): RELIGHT at T_fire; a primed segment relights DIRECTLY (NC valve latch + opener ramp with the torch at
// E0, ignition lift at the torch confirmation E1, light confirmation E2); a segment that may hold gas (P_feed < 0.5 P_tank or a reading
// invalid) runs PREPRESS first. Window W from the lift command: flight 0.65 s on every relight (first start 0.40 s); stand (v2.8.1, LEAD
// fallback (b)) R1 0.35 s first start, R2 0.35 s every other stand start, R3 deleted, R4 no relight with a state sensor invalid. Torch gate
// 0.16 s (Combustion v2.4 confirmed). Case
// abort 448.15 K (MV open) / start refusal 433.15 K. Kept from v2.7: relight lockout (NV, lit-session marker), seat-confirmed shutdown,
// rail loss -> PINTLE_FAULT, stand timing-only start. Flight profile: ARM 0.05, PREPRESS 0.80, IGNITE 1.40 (300 N), MECO SHUTDOWN 3.00
// (MV closed in the coast), RELIGHT 5.00 (150 N), SHUTDOWN 7.00, DISARM 8.00. Vapour: from 4.0 s the valve-to-seat volume holds N2O
// vapour (Combustion low_inlet_check_v2p3 volume and state); the plant does not let vapour light the main (conservative for the window).
// TLM_RELIGHT (0x102) as decoded by the FC is checked in every case (rate in COAST, sequence, status at the RELIGHT command).
// v2.8.2 (GNC RG-08): a pintle-position anomaly in the coast (encoder invalid, or lift > 0.10 mm for 20 ms) latches UNKNOWN / UNPRIMED and
// the prep path until the next light.
// The v2.7 S10 (C7 gate-TC cases) stays in results/sil_v2p7. A SIL pass is NOT hardware validation.
struct FoldCase {
  std::string name, expect;
  std::function<void(SimConfig&)> cfg;
  std::function<void(Sim&)> setup;
  double t_end;
  std::function<bool(const Sim&, const std::vector<Rec>&, std::string*)> pass;   // pass + case-specific detail
};
static std::vector<StateCmd> foldMission() {
  return {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {3.00, Cmd::SHUTDOWN, 0}, {5.00, Cmd::RELIGHT, 0},
          {7.00, Cmd::SHUTDOWN, 0}, {8.00, Cmd::DISARM, 0}};
}
static int firstAbortCause(const std::vector<Rec>& r, double* t_ab) {
  for (const Rec& x : r) if (x.abort) { *t_ab = x.t; return x.abort; }
  *t_ab = NAN; return 0;
}
static const Rec* recAt(const std::vector<Rec>& r, double t) {
  for (const Rec& x : r) if (x.t >= t - 1e-9) return &x;
  return r.empty() ? nullptr : &r.back();
}
static unsigned nvFlags(const Sim& s) { ecu::NvJamRecord jr; (void)ecu::nvJamDecode(s.nv_jam, &jr); return jr.flags; }
static std::string startJson(const Sim& s, const std::vector<Rec>& r, size_t k) {
  const StartM m = startM(s, r, k);
  char b[700];
  std::snprintf(b, sizeof b, "{\"E0_ignition_entry_t\": %.3f, \"rule\": %d, \"W_s\": %.3f, \"direct\": %d, \"E0_to_E1_lift_s\": %.4f, \"to_torch_confirmed_s\": %.4f, "
                "\"to_torch_valves_closed_s\": %.4f, \"to_plant_light_s\": %.4f, \"E0_to_E2_RUN_s\": %.4f, \"E1_to_E2_s\": %.4f, \"sparks\": %d, "
                "\"pintle_lift_max_unlit_mm\": %.4f, \"ox_unlit_kg\": %.5f}",
                m.te, m.rule, m.w, m.direct, m.e1, m.ok, m.tc, m.lit, m.e2, m.e2 - m.e1, m.sparks, m.xmax * 1e3, m.ox);
  return b;
}
// TLM_RELIGHT as received by the FC: frames in COAST (count, longest gap, sequence advancing by 1) and the last frame before t_cmd
struct TlmM { int n_coast = 0; double gap_max = 0; bool seq_ok = true; const ecu::can::TlmRelight* at_cmd = nullptr; };
static TlmM tlmM(const Sim& s, double t_cmd) {
  TlmM m; double t_prev = NAN; int seq_prev = -1;
  for (const auto& f : s.tlmr) {
    if (seq_prev >= 0 && f.m.seq != static_cast<uint8_t>(seq_prev + 1)) m.seq_ok = false;
    seq_prev = f.m.seq;
    if (f.t < t_cmd - 1e-9) m.at_cmd = &f.m;
    if (f.m.state != static_cast<uint8_t>(State::COAST)) { t_prev = NAN; continue; }
    ++m.n_coast;
    if (std::isfinite(t_prev)) m.gap_max = std::max(m.gap_max, f.t - t_prev);
    t_prev = f.t;
  }
  return m;
}
static void scFold() {
  const int NOIGN = (int)ecu::Abort::NO_IGNITION, TORCH = (int)ecu::Abort::TORCH_FAULT, LOCK = (int)ecu::Abort::RELIGHT_LOCKOUT;
  const int PFAULT = (int)ecu::Abort::PINTLE_FAULT, OT = (int)ecu::Abort::OVER_TEMP, MVF = (int)ecu::Abort::MV_FAULT;
  using namespace ecu::cfg;
  const double kGateAb = kTorchGate_s + 0.001;   // abort tick after the gate (strict deadline, 1 ms tick)
  auto vapour = [](SimConfig& c) { c.eng.vapour_fill_at = 4.0; };
  auto stand = [](SimConfig& c) { c.test_stand = true; };
  auto standVapour = [](SimConfig& c) { c.test_stand = true; c.eng.vapour_fill_at = 4.0; };
  auto never = [](Sim& s) { s.hooks.push_back({4.0, [](Sim& q) { q.eng.P.ign_delay = 99.0; }}); };
  // relight lit: no abort, two RUN entries, rule / W / path as expected, RELIGHT command -> E2 within the published worst case
  auto relightLit = [=](const Sim& s, const std::vector<Rec>& r, std::string* d, int rule, double W, int direct, double worst) {
    double ta; const int ab = firstAbortCause(r, &ta);
    const StartM m = startM(s, r, 1);
    const double cmd_e2 = m.te + m.e2 - 5.00;
    char b[300]; std::snprintf(b, sizeof b, "relight rule %d W %.2f s direct %d: E0 %.3f s after the command, E1 +%.3f s, E2 +%.3f s; command -> E2 %.3f s (published %.3f s)",
                               m.rule, m.w, m.direct, m.te - 5.00, m.e1, m.e2, cmd_e2, worst);
    *d = b;
    return ab == 0 && s.run_entry_t.size() == 2 && m.rule == rule && std::fabs(m.w - W) < 1e-4 && m.direct == direct && cmd_e2 <= worst + 1e-9;
  };
  // relight not lit: NO_IGNITION at E1 + W + 1 ms (strict deadline), lockout; unignited N2O of the relight vs the LEAD caps
  auto relightUnlit = [=](const Sim& s, const std::vector<Rec>& r, std::string* d, double W, double cap_g) {
    double ta; const int ab = firstAbortCause(r, &ta);
    const StartM m = startM(s, r, 1);
    const double dt = ta - (m.te + m.e1);
    char b[300]; std::snprintf(b, sizeof b, "NO_IGNITION %.3f s after the lift (W %.2f s), %.3f s after E0; relight unignited N2O %.2f g (LEAD figure %.1f g), vapour %.2f g, lockout %d",
                               dt, m.w, ta - m.te, m.ox * 1e3, cap_g, s.vapour_purged_kg * 1e3, (int)s.out.relight_lockout);
    *d = b;
    return ab == NOIGN && std::fabs(dt - (W + 0.001)) < 0.0015 && s.out.relight_lockout;
  };
  // v2.8.1 stand no-light closure (LEAD request): abort at E1 + W + 1 ms; NC valve unlatched on the abort tick (hardware latch line), MV-P
  // closed (plant opening < 3 %) within 0.10 s of the abort [B-MV-1 close <= 0.10 s, LEAD/COMB v2.4; run 1 used an untraceable 60 ms
  // criterion and failed the relight case at 61 ms: on a direct relight the opener still holds the cam up (ramp 0.35 s + cock hold
  // 0.15 s after E0) when W 0.35 s ends, so the poppet follows the opener back; plant ASSUMES a cam-limited poppet], pintle seated (plant
  // lift <= the seat-confirm lift) within 50 ms [DESIGN], torch valves closed on the abort tick
  auto standNoLightClose = [=](const Sim& s, const std::vector<Rec>& r, std::string* d, size_t k, double W) {
    double ta = NAN; int ab = 0;
    const StartM m = startM(s, r, k);
    for (const Rec& x : r) if (x.t >= m.te && x.abort) { ta = x.t; ab = x.abort; break; }
    const double dt = ta - (m.te + m.e1);
    const double t_unl = firstTime(r, ta - 0.0005, [](const Rec& x) { return !x.mv_latch_hw; });
    const double t_mvc = firstTime(r, ta - 0.0005, [](const Rec& x) { return x.mv < 0.03; });
    const double t_seat = firstTime(r, ta - 0.0005, [](const Rec& x) { return x.x <= ecu::cfg::kPintleSeatConfirm_m; });
    const double t_torch = firstTime(r, ta - 0.0005, [](const Rec& x) { return !x.sol1 && !x.sol2; });
    double us_op = NAN, mv_ab = NAN;
    for (const Rec& x : r) if (x.t >= ta - 0.0015) { us_op = x.us_mvop; mv_ab = x.mv; break; }   // opener command and MV opening at the abort
    char b[520]; std::snprintf(b, sizeof b, "rule %d W %.2f s: NO_IGNITION %.3f s after the lift; at the abort opener cmd %.0f us, MV opening %.2f; from the abort: latch off "
                               "+%.1f ms, MV-P closed +%.1f ms (B-MV-1 <= 100 ms), pintle seated +%.1f ms, torch valves closed +%.1f ms; unignited N2O this start "
                               "%.2f g (aft DN32 disc alone 9.1-14.8 g, COMB v2.4)",
                               m.rule, m.w, dt, us_op, mv_ab, (t_unl - ta) * 1e3, (t_mvc - ta) * 1e3, (t_seat - ta) * 1e3, (t_torch - ta) * 1e3, m.ox * 1e3);
    *d = b;
    return ab == NOIGN && std::fabs(m.w - W) < 1e-4 && std::fabs(dt - (W + 0.001)) < 0.0015 && t_unl - ta < 0.0015 && t_mvc - ta <= 0.100 &&
           t_seat - ta < 0.050 && t_torch - ta < 0.0015;
  };
  const double kWorstP = kTorchGate_s + kIgnWindowRelightLong_s;   // 0.81 s
  const double kPrep = kBleedSettle_s + kMvOpenRampSlow_s + kMvCockHold_s;
  std::vector<FoldCase> cases = {
      {"relight_flight_liquid_direct", "primed segment: direct relight, W 0.65 s, lit; command -> E2 <= 0.81 s", nullptr, [](Sim&) {}, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) { return relightLit(s, r, d, ecu::rule::FLIGHT_RELIGHT, kIgnWindowRelightLong_s, 1, kWorstP); }},
      {"relight_flight_vapour_direct", "vapour in the segment delays the light; W 0.65 s keeps the start", vapour, [](Sim&) {}, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) { return relightLit(s, r, d, ecu::rule::FLIGHT_RELIGHT, kIgnWindowRelightLong_s, 1, kWorstP); }},
      {"relight_flight_liquid_main_never_lights_EVIDENCE", "NO_IGNITION at the lift + 0.65 s; unignited N2O vs the 26.6 g flight figure", nullptr, never, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) { return relightUnlit(s, r, d, kIgnWindowRelightLong_s, 26.6); }},
      {"relight_flight_vapour_main_never_lights_EVIDENCE", "NO_IGNITION at the lift + 0.65 s; vapour then liquid unignited", vapour, never, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) { return relightUnlit(s, r, d, kIgnWindowRelightLong_s, 26.6); }},
      {"relight_torch_fails", "TORCH_FAULT 0.161 s after E0 (gate 0.16 s), no N2O through the pintle, lockout", nullptr,
       [](Sim& s) { s.hooks.push_back({4.0, [](Sim& q) { q.eng.P.torch_fail = true; }}); }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const StartM m = startM(s, r, 1);
         char b[160]; std::snprintf(b, sizeof b, "abort %.3f s after E0, relight unignited N2O %.2f g, lockout %d", ta - m.te, m.ox * 1e3, (int)s.out.relight_lockout); *d = b;
         return ab == TORCH && std::fabs(ta - m.te - kGateAb) < 0.0015 && m.ox < 1e-4 && s.out.relight_lockout; }},
      {"relight_never_lights_lockout_DISARM_ARM_refused", "NO_IGNITION, lockout; DISARM + ARM in flight refused (RELIGHT_LOCKOUT, NV b1)", nullptr,
       [=](Sim& s) { never(s); s.schedule.push_back({7.20, Cmd::DISARM, 0}); s.schedule.push_back({7.30, Cmd::ARM, 0}); }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const Rec* x = recAt(r, 7.32);
         char b[160]; std::snprintf(b, sizeof b, "first abort %s; at 7.32 s state %d cause %d; NV flags 0x%02X", ecu::abortName(static_cast<ecu::Abort>(ab)), x ? x->state : -1, x ? x->abort : -1, nvFlags(s)); *d = b;
         return ab == NOIGN && x && x->state == (int)State::SAFE && x->abort == LOCK && (nvFlags(s) & 2u); }},
      {"lockout_survives_watchdog_reset", "as above, then an MCU hang + watchdog reset: ARM still refused (NV b1)", nullptr,
       [=](Sim& s) { never(s); s.hang_at = 6.5; s.schedule.push_back({7.20, Cmd::DISARM, 0}); s.schedule.push_back({7.30, Cmd::ARM, 0}); }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         const Rec* x = recAt(r, 7.32);
         char b[160]; std::snprintf(b, sizeof b, "boots %d; at 7.32 s state %d cause %d; NV flags 0x%02X", s.boots, x ? x->state : -1, x ? x->abort : -1, nvFlags(s)); *d = b;
         return s.boots == 2 && x && x->state == (int)State::SAFE && x->abort == LOCK; }},
      {"hang_in_RUN_reboot_ARM_refused_then_keyed_clear", "MCU hang in the first burn: after the reset the lit-session marker (NV b2) refuses ARM; ground keyed CLEAR_LOCKOUT then ARM accepted",
       nullptr, [](Sim& s) {
         s.hang_at = 2.5;
         s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {3.20, Cmd::ARM, 0}, {3.30, Cmd::DISARM, 0},
                       {3.40, Cmd::CLEAR_LOCKOUT, ecu::cfg::kClearLockoutKey}, {3.50, Cmd::ARM, 0}, {3.80, Cmd::DISARM, 0}}; }, 4.0,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         const Rec* a = recAt(r, 3.22); const Rec* b2 = recAt(r, 3.60);
         char b[200]; std::snprintf(b, sizeof b, "boots %d; at 3.22 s state %d cause %d; at 3.60 s state %d; NV flags at end 0x%02X", s.boots, a ? a->state : -1, a ? a->abort : -1, b2 ? b2->state : -1, nvFlags(s)); *d = b;
         return s.boots == 2 && a && a->state == (int)State::SAFE && a->abort == LOCK && b2 && b2->state == (int)State::ARMED && (nvFlags(s) & 6u) == 0; }},
      {"relight_pfeed_invalid_prepress_path", "P_feed invalid in the coast: TLM VALID|UNKNOWN (PRIMED 0; v2.8 draft VALID 0), worst 1.37 s; RELIGHT runs PREPRESS (0.56 s) then lights; command -> E2 <= 1.37 s",
       nullptr, [](Sim& s) { s.hooks.push_back({4.0, [](Sim& q) { q.pfeed_valid = false; }}); }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         const TlmM t = tlmM(s, 5.00);
         const bool tl = t.at_cmd && (t.at_cmd->flags & ecu::tlmr::VALID) && (t.at_cmd->flags & ecu::tlmr::UNKNOWN) && !(t.at_cmd->flags & ecu::tlmr::PRIMED) &&
                         t.at_cmd->worst_ms == 1370;
         const bool lit = relightLit(s, r, d, ecu::rule::FLIGHT_RELIGHT, kIgnWindowRelightLong_s, 0, kPrep + kWorstP);
         const StartM m = startM(s, r, 1);
         *d += " | E0 " + std::to_string(m.te - 5.00).substr(0, 5) + " s after the command";
         return tl && lit && std::fabs(m.te - 5.00 - kPrep) < 0.004; }},
      {"relight_direct_open_switch_fails_flight", "MV OPEN switch never makes (valve fine): lit, fault MV flag only, burn continues to SHUTDOWN", nullptr,
       [](Sim& s) { s.mv_open_sw_fail_from = 4.0; }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const Rec* x = recAt(r, 6.5);
         char b[160]; std::snprintf(b, sizeof b, "first abort %s; at 6.5 s state %d faults 0x%04X; RUN entries %zu", ecu::abortName(static_cast<ecu::Abort>(ab)), x ? x->state : -1, x ? x->faults : 0, s.run_entry_t.size()); *d = b;
         return ab == 0 && x && x->state == (int)State::RUN && (x->faults & ecu::fault::MV) && s.run_entry_t.size() == 2; }},
      {"relight_direct_open_switch_fails_stand", "stand: same -> MV_FAULT abort at E0 + 0.951 s", stand,
       [](Sim& s) { s.mv_open_sw_fail_from = 4.0; }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const StartM m = startM(s, r, 1);
         char b[160]; std::snprintf(b, sizeof b, "first abort %s %.3f s after E0", ecu::abortName(static_cast<ecu::Abort>(ab)), ta - m.te); *d = b;
         return ab == MVF && std::fabs(ta - m.te - (kMvOpenBy_s + 0.001)) < 0.0015; }},
      {"stand_relight_R2_liquid", "stand relight, state TCs at ambient: R2 W 0.35 s (v2.8.1), lit", stand, [](Sim&) {}, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) { return relightLit(s, r, d, ecu::rule::STAND_DEFAULT, kIgnWindowRelightStand_s, 1, kTorchGate_s + kIgnWindowRelightStand_s); }},
      {"stand_relight_superheat_R3_deleted_still_R2", "v2.8.1: stand relight, MSS-1 and MSS-2 at 310 K (>= Tsat(P_feed) + 5 K): R3 deleted -> R2 W 0.35 s, lit", stand,
       [](Sim& s) { s.hooks.push_back({4.0, [](Sim& q) { q.tc_mss1_K = 310.0; q.tc_mss2_K = 310.0; }}); }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) { return relightLit(s, r, d, ecu::rule::STAND_DEFAULT, kIgnWindowRelightStand_s, 1, kTorchGate_s + kIgnWindowRelightStand_s); }},
      {"stand_relight_R4_mss2_invalid_refused", "stand, MSS-2 invalid in the coast: RELIGHT refused (R4_SENSOR), no relight, no abort", stand,
       [](Sim& s) { s.hooks.push_back({4.0, [](Sim& q) { q.mss2_valid = false; }}); }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const TlmM t = tlmM(s, 5.00);
         char b[160]; std::snprintf(b, sizeof b, "TLM block at the command %d, IGNITION entries %zu, first abort %s", t.at_cmd ? t.at_cmd->block : -1, s.ign_entry_t.size(),
                                    ecu::abortName(static_cast<ecu::Abort>(ab))); *d = b;
         return ab == 0 && s.ign_entry_t.size() == 1 && t.at_cmd && t.at_cmd->block == ecu::refuse::R4_SENSOR && !(t.at_cmd->flags & ecu::tlmr::READY); }},
      {"stand_relight_vapour_main_never_lights_R2_EVIDENCE", "stand R2: NO_IGNITION at the lift + 0.35 s; unignited N2O vs the aft DN32 disc alone 9.1-14.8 g (COMB v2.4)", standVapour, never, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) { return relightUnlit(s, r, d, kIgnWindowRelightStand_s, 9.1); }},
      // v2.8.1 LEAD request: a stand start that does not confirm within 0.35 s drops the NC valve and closes the pintle (plant times)
      {"stand_first_start_no_light_0p35_MV_and_pintle_close", "v2.8.1 stand R1 never lights: NO_IGNITION at E1 + 0.351 s; NC valve unlatched on the abort tick, "
       "MV-P closed and pintle seated (plant) within 60 / 50 ms; unignited N2O vs the aft DN32 disc alone 9.1-14.8 g", stand,
       [](Sim& s) { s.eng.P.ign_delay = 99.0; s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {3.00, Cmd::DISARM, 0}}; }, 3.0,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) { return standNoLightClose(s, r, d, 0, kIgnWindowFirstStand_s); }},
      {"stand_relight_liquid_no_light_0p35_MV_and_pintle_close", "v2.8.1 stand R2 relight never lights (liquid segment): NO_IGNITION at E1 + 0.351 s; NC valve unlatched "
       "on the abort tick, MV-P closed and pintle seated (plant) within 60 / 50 ms", stand, never, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) { return standNoLightClose(s, r, d, 1, kIgnWindowRelightStand_s); }},
      {"stand_timing_only_dead_torch", "test stand + key: gate bypassed, pintle at the table minimum (0.2039 mm) at 0.12 s, NO_IGNITION at 0.12 + 0.35 s (stand R1, v2.8.1)",
       stand,
       [](Sim& s) { s.eng.P.torch_fail = true; s.schedule = {{0.02, Cmd::SET_TORCH_GATE, ecu::cfg::kTorchTimingOnlyKey}, {0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}}; }, 3.0,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         double xmax = 0; for (const Rec& x : r) if (x.state == (int)State::IGNITION) xmax = std::max(xmax, x.x);
         const StartM m = startM(s, r, 0);
         char b[220]; std::snprintf(b, sizeof b, "abort %.3f s after E0, plant lift max %.4f mm, unignited N2O %.2f g", ta - m.te, xmax * 1e3, m.ox * 1e3); *d = b;
         return ab == NOIGN && std::fabs(ta - m.te - (kTimingOnlyLiftAt_s + kIgnWindowFirstStand_s + 0.001)) < 0.003 && std::fabs(xmax - kTimingOnlyLift_m) < 0.03e-3; }},
      {"stand_dead_torch_no_key", "test stand without the key: TORCH_FAULT at 0.161 s, no N2O through the pintle", stand,
       [](Sim& s) { s.eng.P.torch_fail = true; }, 3.0,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const StartM m = startM(s, r, 0);
         char b[120]; std::snprintf(b, sizeof b, "abort %.3f s after E0, unignited N2O %.2f g", ta - m.te, m.ox * 1e3); *d = b;
         return ab == TORCH && std::fabs(ta - m.te - kGateAb) < 0.0015 && m.ox < 1e-4; }},
      {"rail_ov_trip_in_COAST", "LTC4365 trip in the coast: PINTLE_FAULT, lockout (lit burn), no relight", nullptr, [](Sim& s) { s.prail_ov_at = 4.0; }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const Rec* x = recAt(r, ta - 0.0015);
         char b[160]; std::snprintf(b, sizeof b, "abort %.3f s after the trip in state %d, lockout %d, RUN entries %zu", ta - 4.0, x ? x->state : -1, (int)s.out.relight_lockout, s.run_entry_t.size()); *d = b;
         return ab == PFAULT && ta - 4.0 < 0.010 && x && x->state == (int)State::COAST && s.out.relight_lockout && s.run_entry_t.size() == 1; }},
      {"meco_seat_confirmed_shutdown", "MECO: pintle first, NC valve unlatched after the confirmed seat (< 0.30 s timeout), then COAST; MV-P closes in ~30 ms", nullptr, [](Sim&) {}, 4.0,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         const double t_seat = firstTime(r, 3.0, [](const Rec& x) { return x.x <= ecu::cfg::kPintleSeatConfirm_m; });
         const double t_unl = firstTime(r, 3.0, [](const Rec& x) { return !x.mv_latch_hw; });
         const double t_coast = firstTime(r, 3.0, [](const Rec& x) { return x.state == (int)State::COAST; });
         const double t_mvc = firstTime(r, 3.0, [](const Rec& x) { return x.mv < 0.03; });
         char b[220]; std::snprintf(b, sizeof b, "from SHUTDOWN: seated (plant) +%.0f ms, MV unlatched +%.0f ms, COAST +%.0f ms, MV closed +%.0f ms (unlatch -> closed %.0f ms)",
                                    (t_seat - 3.0) * 1e3, (t_unl - 3.0) * 1e3, (t_coast - 3.0) * 1e3, (t_mvc - 3.0) * 1e3, (t_mvc - t_unl) * 1e3); *d = b;
         return t_unl >= t_seat && t_unl - 3.0 < ecu::cfg::kMvSeatTimeout_s - 1e-3 && t_coast >= t_unl && t_mvc - t_unl < 0.060; }},
      {"case_TC_445K_in_RUN_no_abort_relight_refused", "445 K on a case TC from 2.5 s: no abort in the burn (abort 448.15 K); RELIGHT in the coast refused (CASE_HOT > 433.15 K)",
       nullptr, [](Sim& s) { s.tc_hot_at = 2.5; s.tc_hot_idx = 0; s.tc_hot_K = 445.0; }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const TlmM t = tlmM(s, 5.00);
         char b[160]; std::snprintf(b, sizeof b, "first abort %s; TLM block at the command %d; IGNITION entries %zu", ecu::abortName(static_cast<ecu::Abort>(ab)),
                                    t.at_cmd ? t.at_cmd->block : -1, s.ign_entry_t.size()); *d = b;
         return ab == 0 && s.ign_entry_t.size() == 1 && t.at_cmd && t.at_cmd->block == ecu::refuse::CASE_HOT; }},
      {"case_TC_455K_in_RUN_abort", "455 K on a case TC in the burn: OVER_TEMP 0.2 s after the step", nullptr,
       [](Sim& s) { s.tc_hot_at = 2.5; s.tc_hot_idx = 0; s.tc_hot_K = 455.0; }, 4.0,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         char b[120]; std::snprintf(b, sizeof b, "abort %s %.3f s after the TC step", ecu::abortName(static_cast<ecu::Abort>(ab)), ta - 2.5); *d = b;
         return ab == OT && std::fabs(ta - 2.5 - kOverTempTime_s) < 0.003; }},
      // ---- v2.8 final (COMB v2.4, GNC v3 option (c), LEAD 2026-10-13)
      // planned cut-off with the pintle encoder lost from the SHUTDOWN tick: NC valve unlatched on the 0.30 s seat timeout (flag, fault
      // ENCODER), COAST, no abort. v2.8.2 (GNC RG-08): the encoder was invalid on COAST ticks (3.30-4.00 s), so the relight state is latched
      // UNKNOWN although the encoder is back at 4.0 s; the RELIGHT runs the prep path and lights within 1.37 s (v2.8 final: direct, lit)
      {"meco_encoder_lost_seat_timeout_no_abort_RG08_prep_path", "MECO with the encoder lost: NC valve unlatched at the 0.30 s timeout, COAST, no abort; "
       "v2.8.2 RG-08: TLM UNKNOWN latched (encoder invalid in the coast), relight via the prep path, lit <= 1.37 s",
       nullptr, [](Sim& s) { s.enc_fail_from = 3.0; s.enc_fail_to = 4.0; }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         const double t_unl = firstTime(r, 3.0, [](const Rec& x) { return !x.mv_latch_hw; });
         const double t_coast = firstTime(r, 3.0, [](const Rec& x) { return x.state == (int)State::COAST; });
         const TlmM t = tlmM(s, 5.00);
         const bool tl = t.at_cmd && (t.at_cmd->flags & ecu::tlmr::VALID) && (t.at_cmd->flags & ecu::tlmr::UNKNOWN) && !(t.at_cmd->flags & ecu::tlmr::PRIMED) &&
                         t.at_cmd->worst_ms == 1370;
         std::string d2; const bool lit = relightLit(s, r, &d2, ecu::rule::FLIGHT_RELIGHT, kIgnWindowRelightLong_s, 0, kPrep + kWorstP);
         char b[260]; std::snprintf(b, sizeof b, "MV unlatched +%.1f ms, COAST +%.1f ms after SHUTDOWN; TLM at the command flags 0x%02X worst %d ms | ",
                                    (t_unl - 3.0) * 1e3, (t_coast - 3.0) * 1e3, t.at_cmd ? t.at_cmd->flags : 0, t.at_cmd ? t.at_cmd->worst_ms : -1);
         *d = std::string(b) + d2;
         return tl && lit && std::fabs(t_unl - 3.0 - kMvSeatTimeout_s) < 0.0025 && t_coast >= t_unl; }},
      // ---- v2.8.2 (GNC REV-GNC-1 RG-08): pintle-position anomaly in the coast -> TLM UNKNOWN / UNPRIMED (latched), prep path
      {"coast_encoder_dropout_20ms_RG08_unknown_prep_path", "v2.8.2 RG-08: pintle encoder invalid 4.50-4.52 s in the coast -> TLM VALID|UNKNOWN from the "
       "dropout and still at the command (latched), worst 1370 ms; RELIGHT via the prep path, lit <= 1.37 s",
       nullptr, [](Sim& s) { s.enc_fail_from = 4.50; s.enc_fail_to = 4.52; }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         const TlmM t = tlmM(s, 5.00);
         double t_unk = NAN; bool primed_before = false;
         for (const auto& f : s.tlmr) {
           if (f.t > 4.40 && f.t < 4.50 && ecu::tlmr::stateOf(f.m.flags) == ecu::segstate::PRIMED) primed_before = true;
           if (f.t >= 4.50 && !std::isfinite(t_unk) && ecu::tlmr::stateOf(f.m.flags) == ecu::segstate::UNKNOWN) t_unk = f.t;
         }
         const bool tl = t.at_cmd && ecu::tlmr::stateOf(t.at_cmd->flags) == ecu::segstate::UNKNOWN && t.at_cmd->worst_ms == 1370 && t.at_cmd->ratio_pct >= 50;
         std::string d2; const bool lit = relightLit(s, r, &d2, ecu::rule::FLIGHT_RELIGHT, kIgnWindowRelightLong_s, 0, kPrep + kWorstP);
         char b[220]; std::snprintf(b, sizeof b, "PRIMED before %d; first UNKNOWN frame %.0f ms after the dropout; at the command flags 0x%02X ratio %d %% | ",
                                    (int)primed_before, (t_unk - 4.50) * 1e3, t.at_cmd ? t.at_cmd->flags : 0, t.at_cmd ? t.at_cmd->ratio_pct : -1);
         *d = std::string(b) + d2;
         return primed_before && tl && lit && t_unk - 4.50 <= 0.0205; }},
      {"coast_pintle_reads_0p12mm_RG08_unprimed_prep_path", "v2.8.2 RG-08: encoder reads the needle 0.12 mm off the seat 4.50-4.60 s (stall monitor quiet "
       "below 0.15 mm) -> TLM UNPRIMED 20 ms later, latched at the command with the P_feed ratio >= 50 %; RELIGHT via the prep path, lit <= 1.37 s",
       nullptr, [](Sim& s) { s.enc_bias_from = 4.50; s.enc_bias_to = 4.60; s.enc_bias_m = 0.12e-3; }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const TlmM t = tlmM(s, 5.00);
         double t_unp = NAN;
         for (const auto& f : s.tlmr) if (f.t >= 4.50 && !std::isfinite(t_unp) && ecu::tlmr::stateOf(f.m.flags) == ecu::segstate::UNPRIMED) t_unp = f.t;
         const bool tl = t.at_cmd && ecu::tlmr::stateOf(t.at_cmd->flags) == ecu::segstate::UNPRIMED && t.at_cmd->worst_ms == 1370 && t.at_cmd->ratio_pct >= 50 &&
                         (t.at_cmd->flags & ecu::tlmr::READY);
         std::string d2; const bool lit = relightLit(s, r, &d2, ecu::rule::FLIGHT_RELIGHT, kIgnWindowRelightLong_s, 0, kPrep + kWorstP);
         char b[220]; std::snprintf(b, sizeof b, "first UNPRIMED frame %.0f ms after the offset; at the command flags 0x%02X ratio %d %%; coast abort %s | ",
                                    (t_unp - 4.50) * 1e3, t.at_cmd ? t.at_cmd->flags : 0, t.at_cmd ? t.at_cmd->ratio_pct : -1, ecu::abortName(static_cast<ecu::Abort>(ab)));
         *d = std::string(b) + d2;
         return tl && lit && t_unp - 4.50 >= 0.019 && t_unp - 4.50 <= 0.0405; }},
      // late flip: the anomaly appears after the last TLM_RELIGHT frame the FC sees before T_fire. The FC planned PRIMED (deadline 0.81 s);
      // the ECU takes the prep path (the latch is evaluated on the RELIGHT tick), whose deadline is 1.37 s. EVIDENCE of the residual
      // planning gap (deadline +0.56 s); the first TLM_RELIGHT after the command shows d1 = PREPRESS (prep path) instead of IGNITION
      // (direct), so the FC learns the path within one frame period. Run 1 (results/sil_v2p8_2_run1) also required the light to come
      // after 0.81 s: wrong criterion (0.81 s is a deadline; a liquid segment lights at ~0.69 s on the prep path) -> removed
      {"coast_encoder_loss_after_last_frame_RG08_late_flip_EVIDENCE", "v2.8.2 RG-08 late flip: encoder invalid from 4.995 s (after the last frame before "
       "the 5.00 s command): FC saw PRIMED (deadline 0.81 s), the ECU takes the prep path (deadline 1.37 s); the first frame after the command shows "
       "PREPRESS; lit <= 1.37 s",
       nullptr, [](Sim& s) { s.enc_fail_from = 4.995; s.enc_fail_to = 5.20; }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         const TlmM t = tlmM(s, 5.00);
         double t_after = NAN; int st_after = -1, wst_after = -1;
         for (const auto& f : s.tlmr) if (f.t > 5.00 + 1e-9) { t_after = f.t; st_after = f.m.state; wst_after = f.m.worst_ms; break; }
         const bool fc_primed = t.at_cmd && ecu::tlmr::stateOf(t.at_cmd->flags) == ecu::segstate::PRIMED && t.at_cmd->worst_ms == 810;
         std::string d2; const bool lit = relightLit(s, r, &d2, ecu::rule::FLIGHT_RELIGHT, kIgnWindowRelightLong_s, 0, kPrep + kWorstP);
         const StartM m = startM(s, r, 1);
         const double cmd_e2 = m.te + m.e2 - 5.00;
         char b[300]; std::snprintf(b, sizeof b, "FC frame before the command: state %s worst %d ms; first frame after the command +%.0f ms state %d (PREPRESS %d) "
                                    "worst %d ms; command -> E2 %.3f s (PRIMED deadline 0.810 s, prep deadline 1.370 s) | ", fc_primed ? "PRIMED" : "not PRIMED",
                                    t.at_cmd ? t.at_cmd->worst_ms : -1, (t_after - 5.00) * 1e3, st_after, (int)State::PREPRESS, wst_after, cmd_e2);
         *d = std::string(b) + d2;
         return fc_primed && lit && st_after == (int)State::PREPRESS && t_after - 5.00 <= 0.0205; }},
      // MV CLOSED switch fails just before MECO (valve fine): no closed-valve proof -> TLM VALID 0 until the closure is overdue (0.5 s after
      // the unlatch), then UNPRIMED; the RELIGHT runs the prep path and lights within the 1.37 s fault-path bound
      {"mv_closed_switch_fails_tlm_unprimed_prep_path", "CLOSED switch failed at MECO: TLM VALID only 0.5 s after the unlatch, then UNPRIMED (1.37 s); RELIGHT via PREPRESS, lit <= 1.37 s",
       nullptr, [](Sim& s) { s.mv_closed_sw_fail_from = 2.9; }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         const TlmM t = tlmM(s, 5.00);
         const double t_unl = firstTime(r, 3.0, [](const Rec& x) { return !x.mv_latch_hw; });
         double t_valid = NAN; for (const auto& f : s.tlmr) if (f.t > 3.0 && (f.m.flags & ecu::tlmr::VALID)) { t_valid = f.t; break; }
         const bool tl = t.at_cmd && (t.at_cmd->flags & ecu::tlmr::VALID) && !(t.at_cmd->flags & (ecu::tlmr::PRIMED | ecu::tlmr::UNKNOWN)) && t.at_cmd->worst_ms == 1370;
         std::string d2; const bool lit = relightLit(s, r, &d2, ecu::rule::FLIGHT_RELIGHT, kIgnWindowRelightLong_s, 0, kPrep + kWorstP);
         char b[200]; std::snprintf(b, sizeof b, "first VALID frame %.0f ms after the unlatch, flags at the command 0x%02X | ", (t_valid - t_unl) * 1e3, t.at_cmd ? t.at_cmd->flags : 0);
         *d = std::string(b) + d2;
         return tl && lit && t_valid - t_unl >= kMvCloseConfirm_s && t_valid - t_unl <= kMvCloseConfirm_s + 0.025; }},
      // post-abort vapour segment (COMB v2.4 item 2): stand first start never lights -> NO_IGNITION (R1), NV b3 set; after safing (DISARM, ARM,
      // past the 5 s vent wait) the next IGNITE is a vapour-segment start: R2 (W 0.35 s since v2.8.1) instead of R1; it lights; b3 cleared
      {"stand_start_after_abort_R2_vapour_segment", "stand: no-light abort, then the next start after safing uses R2 (0.35 s), not R1; lit; NV b3 set then cleared",
       stand, [](Sim& s) {
         const double d0 = s.eng.P.ign_delay; s.eng.P.ign_delay = 99.0;
         s.hooks.push_back({6.5, [d0](Sim& q) { q.eng.P.ign_delay = d0; }});
         s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {2.60, Cmd::DISARM, 0}, {2.70, Cmd::ARM, 0},
                       {7.00, Cmd::IGNITE, 0}, {9.00, Cmd::SHUTDOWN, 0}, {10.00, Cmd::DISARM, 0}}; }, 10.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const StartM m0 = startM(s, r, 0), m1 = startM(s, r, 1);
         bool b3_seen = false, later_abort = false;
         for (const Rec& x : r) { b3_seen = b3_seen || x.segvap; if (x.t > 2.65 && x.abort) later_abort = true; }
         char b[300]; std::snprintf(b, sizeof b, "first start rule %d abort %s; second start rule %d W %.2f s, E2 +%.3f s after E0; vapour flag seen %d; NV flags at end 0x%02X",
                                    m0.rule, ecu::abortName(static_cast<ecu::Abort>(ab)), m1.rule, m1.w, m1.e2, (int)b3_seen, nvFlags(s)); *d = b;
         return ab == NOIGN && m0.rule == ecu::rule::FIRST && m1.rule == ecu::rule::STAND_DEFAULT && std::fabs(m1.w - kIgnWindowRelightStand_s) < 1e-4 &&
                s.run_entry_t.size() == 1 && std::isfinite(m1.e2) && b3_seen && !(nvFlags(s) & 8u) && !later_abort; }},
      // tank interlock (LEAD 2026-10-13): a wall DS18B20 reads 298 K in the coast (> 297.15 K): stand -> RELIGHT refused; flight -> flag only
      {"tank_hot_stand_relight_refused", "stand: tank wall 298 K in the coast -> RELIGHT refused (TANK_HOT), no relight, no abort", stand,
       [](Sim& s) { s.hooks.push_back({4.0, [](Sim& q) { q.ttank_wall_override_K = 298.0; }}); }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         double ta; const int ab = firstAbortCause(r, &ta);
         const TlmM t = tlmM(s, 5.00);
         char b[160]; std::snprintf(b, sizeof b, "TLM block at the command %d, IGNITION entries %zu, first abort %s, refusals %u", t.at_cmd ? t.at_cmd->block : -1,
                                    s.ign_entry_t.size(), ecu::abortName(static_cast<ecu::Abort>(ab)), (unsigned)s.ecu.ignRefusedTank()); *d = b;
         return ab == 0 && s.ign_entry_t.size() == 1 && t.at_cmd && t.at_cmd->block == ecu::refuse::TANK_HOT && !(t.at_cmd->flags & ecu::tlmr::READY) &&
                s.ecu.ignRefusedTank() >= 1; }},
      {"tank_hot_flight_relight_flag_only", "flight: tank wall 298 K in the coast -> RELIGHT accepted with the tank_hot_relight flag, direct, lit", nullptr,
       [](Sim& s) { s.hooks.push_back({4.0, [](Sim& q) { q.ttank_wall_override_K = 298.0; }}); }, 8.5,
       [=](const Sim& s, const std::vector<Rec>& r, std::string* d) {
         const bool lit = relightLit(s, r, d, ecu::rule::FLIGHT_RELIGHT, kIgnWindowRelightLong_s, 1, kWorstP);
         *d += s.ecu.tankHotRelight() ? " | tank_hot_relight flag set" : " | tank_hot_relight flag MISSING";
         return lit && s.ecu.tankHotRelight(); }},
  };
  J j;
  j.k("scenario").v("S10 v2.8 relight path and windows (LEAD 2026-10-13): direct relight on a primed segment (NC valve + torch at E0, lift at E1), PREPRESS on a "
                     "segment that may hold gas, W from the lift (flight 0.65 s; stand v2.8.1 R1 0.35 / R2 0.35 s, R3 deleted, R4 refused), torch gate 0.16 s, MV OPEN "
                     "switch supervision, case 448.15 / 433.15 K, relight lockout (NV), seat-confirmed shutdown, rail loss in COAST, stand timing-only start. "
                     "TLM_RELIGHT checked in every case (>= 10 Hz in COAST, sequence, status at the command). Flight: no load cell (NaN), strap FLIGHT");
  std::string arr = "[";
  int pass = 0, tlm_pass = 0;
  for (size_t i = 0; i < cases.size(); ++i) {
    const FoldCase& fc = cases[i];
    SimConfig c0 = nominal(101 + i);
    if (fc.cfg) fc.cfg(c0);
    Sim s(c0);
    s.schedule = foldMission();
    s.thrust_cmd = [](double t) { return t < 4.0 ? 300.0 : 150.0; };
    fc.setup(s);
    std::sort(s.schedule.begin(), s.schedule.end(), [](const StateCmd& a, const StateCmd& b) { return a.t < b.t; });
    s.run(fc.t_end);
    const auto& r = s.rec();
    s.writeCsv(OUT + "/S10_" + fc.name + ".csv");
    std::string det;
    bool ok = fc.pass(s, r, &det);
    ok = ok && s.n2o_alone_ms == 0;
    double pcmax = 0; for (const Rec& x : r) pcmax = std::max(pcmax, x.Pc);
    ok = ok && pcmax <= ecu::cfg::kPcMeopLeadAbs_Pa;
    // TLM_RELIGHT (LEAD: >= 10 Hz during COAST with a valid bit and a sequence counter): every case that reaches COAST
    const TlmM tm = tlmM(s, 5.00);
    const bool tlm_ok = tm.seq_ok && (tm.n_coast == 0 || tm.gap_max <= 0.100 + 1e-9);
    ok = ok && tlm_ok; tlm_pass += tlm_ok;
    pass += ok;
    double ta; const int ab = firstAbortCause(r, &ta);
    std::string st = "[";
    for (size_t k = 0; k < s.ign_entry_t.size(); ++k) st += (k ? ", " : "") + startJson(s, r, k);
    st += "]";
    char tl[400];
    std::snprintf(tl, sizeof tl, "{\"frames_in_COAST\": %d, \"max_gap_COAST_s\": %.3f, \"seq_advancing\": %s, \"at_cmd_flags\": %d, \"at_cmd_worst_ms\": %d, \"at_cmd_block\": %d, \"at_cmd_ratio_pct\": %d}",
                  tm.n_coast, tm.gap_max, tm.seq_ok ? "true" : "false", tm.at_cmd ? tm.at_cmd->flags : -1, tm.at_cmd ? tm.at_cmd->worst_ms : -1,
                  tm.at_cmd ? tm.at_cmd->block : -1, tm.at_cmd ? tm.at_cmd->ratio_pct : -1);
    char b[1200];
    std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"expect\": \"%s\", \"pass\": %s, \"detail\": \"%s\", \"first_abort\": \"%s\", \"first_abort_t\": %.4f, "
                  "\"final_state\": \"%s\", \"boots\": %d, \"nv_flags\": %u, \"relight_lockout_end\": %s, \"n2o_alone_ms\": %ld, \"vapour_purged_kg\": %.5f, "
                  "\"ltc4365_trips\": %d, \"Pc_max_abs_Pa\": %.0f, \"tlm_relight\": %s, \"starts\": ",
                  i ? ", " : "", fc.name.c_str(), fc.expect.c_str(), ok ? "true" : "false", det.c_str(), ecu::abortName(static_cast<ecu::Abort>(ab)), ta,
                  ecu::stateName(s.ecu.state()), s.boots, nvFlags(s), s.out.relight_lockout ? "true" : "false", s.n2o_alone_ms, s.vapour_purged_kg,
                  s.ltc_trips, pcmax, tl);
    arr += std::string(b) + st + "}";
    std::printf("S10 %-52s %s | %s | first abort %s | TLM coast frames %d gap %.0f ms\n", fc.name.c_str(), ok ? "PASS" : "FAIL", det.c_str(),
                ecu::abortName(static_cast<ecu::Abort>(ab)), tm.n_coast, tm.gap_max * 1e3);
  }
  arr += "]";
  j.k("cases").raw(arr);
  j.k("passed").v(pass); j.k("total").v(static_cast<double>(cases.size())); j.k("tlm_relight_checks_passed").v(tlm_pass);
  writeFile(OUT + "/S10_relight_v2p8.json", j.str());
}

// ------------------------------------------------------------------------------------------ S11 fault path vs segment volume (v2.8 final)
// LEAD 2026-10-13 (GNC v3 option (c) margin 1.41 - 1.37 s = 0.04 s): re-state the fault-path time (prep + ignition) for the MV-to-seat segment
// of option A (~44 cm3). Volumes come from the command line (calc/fault_path_v1.py reads them from the interface / team JSON files; nothing
// is typed in here): "label=cm3,label=cm3,...". Flight profile as S10 (MECO 3.0 s, RELIGHT 5.0 s at 150 N). Cases per volume:
//   drained_prep          line vented at 4.5 s (gas pocket at 1 bar in V_line = V; air, adiabatic, indicative): UNPRIMED -> PREPRESS
//                         (bleed + ramp) -> IGNITION once P_feed > 0.8 P_tank with the OPEN switch, else PREPRESS_FAIL (1.61 s bound)
//   vapour_direct         saturated vapour fills V from 4.0 s; P_feed stays at Psat so the segment reads PRIMED (the COMB v2.4 gap): direct
//                         relight, the vapour is purged through the ignition lift before liquid reaches the seat (light later, W 0.65 s)
//   vapour_unknown_prep   the same with P_feed invalid (UNKNOWN): the PREPRESS bleed purges part of the vapour before E0
// References (volume independent in this plant): liquid_direct, liquid_unknown_prep (P_feed invalid). A SIL characterisation on ASSUMED
// plant models (gas pocket, vapour purge flux); not hardware validation and not Combustion's two-phase analysis.
static void scFaultPath(const std::string& spec) {
  using namespace ecu::cfg;
  std::vector<std::pair<std::string, double>> vols;
  {
    size_t a = 0;
    while (a < spec.size()) {
      size_t b = spec.find(',', a); if (b == std::string::npos) b = spec.size();
      const std::string item = spec.substr(a, b - a); const size_t e = item.find('=');
      if (e != std::string::npos) vols.push_back({item.substr(0, e), std::atof(item.c_str() + e + 1)});
      a = b + 1;
    }
  }
  struct FP { std::string name, label; double V_cm3; int kind; };   // kind 0 drained, 1 vapour direct, 2 vapour + P_feed invalid, 3 liquid, 4 liquid + P_feed invalid
  std::vector<FP> cases = {{"liquid_direct", "reference", 0.0, 3}, {"liquid_unknown_prep", "reference", 0.0, 4}};
  for (const auto& v : vols) {
    char nb[64];
    std::snprintf(nb, sizeof nb, "%.2fcm3", v.second);
    cases.push_back({std::string("drained_prep_") + nb, v.first, v.second, 0});
    cases.push_back({std::string("vapour_direct_") + nb, v.first, v.second, 1});
    cases.push_back({std::string("vapour_unknown_prep_") + nb, v.first, v.second, 2});
  }
  const double kPrepB = kBleedSettle_s + kMvOpenRampSlow_s + kMvCockHold_s, kWorst = kTorchGate_s + kIgnWindowRelightLong_s;
  J j;
  j.k("scenario").v("S11 fault path vs MV-to-seat segment volume (LEAD 2026-10-13 option (c) margin): flight, MECO 3.0 s, RELIGHT 5.0 s, 150 N; times from the RELIGHT command");
  j.k("bounds_s").raw(std::string("{\"direct_planning\": ") + std::to_string(kWorst) + ", \"prep_path\": " + std::to_string(kPrepB + kWorst) +
                      ", \"gnc_option_c_plan\": 1.41, \"prepress_fail\": " + std::to_string(kBleedSettle_s + kMvOpenRampSlow_s + 2.0 * kPrepressTimeout_s + kWorst) + "}");
  std::string arr = "[";
  for (size_t i = 0; i < cases.size(); ++i) {
    const FP& fc = cases[i];
    SimConfig c0 = nominal(301 + i);
    const double V = fc.V_cm3 * 1e-6;
    if (fc.kind == 0) { c0.eng.V_line = V; c0.eng.line_vent_at = 4.5; }
    if (fc.kind == 1 || fc.kind == 2) { c0.eng.vapour_fill_at = 4.0; c0.eng.V_vap = V; }
    Sim s(c0);
    s.schedule = foldMission();
    s.thrust_cmd = [](double t) { return t < 4.0 ? 300.0 : 150.0; };
    if (fc.kind == 2 || fc.kind == 4) s.hooks.push_back({4.0, [](Sim& q) { q.pfeed_valid = false; }});
    s.run(8.5);
    const auto& r = s.rec();
    s.writeCsv(OUT + "/S11_" + fc.name + ".csv");
    const TlmM tm = tlmM(s, 5.00);
    const StartM m = startM(s, r, 1);
    double ta; const int ab = firstAbortCause(r, &ta);
    const double t_e0 = m.te - 5.00, t_e2 = m.te + m.e2 - 5.00;
    const uint8_t st = tm.at_cmd ? ecu::tlmr::stateOf(tm.at_cmd->flags) : 0xFF;
    const double t_primed = firstTime(r, 5.0, [](const Rec& x) { return x.pfeed > 0.8 * x.ptank; }) - 5.0;
    char b[1400];
    std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"volume_source\": \"%s\", \"V_cm3\": %.2f, \"tlm_state_at_cmd\": %d, \"tlm_flags_at_cmd\": %d, \"tlm_worst_ms\": %d, "
                  "\"direct\": %d, \"cmd_to_E0_s\": %.4f, \"E0_to_E1_s\": %.4f, \"E1_to_E2_s\": %.4f, \"cmd_to_E2_s\": %.4f, \"cmd_to_feed_primed_s\": %.4f, "
                  "\"first_abort\": \"%s\", \"cmd_to_abort_s\": %.4f, \"ox_unlit_relight_kg\": %.5f, \"vapour_purged_kg\": %.5f, \"gas_p_max_Pa\": %.0f, "
                  "\"within_1p37\": %s, \"within_1p41\": %s}",
                  i ? ", " : "", fc.name.c_str(), fc.label.c_str(), fc.V_cm3, (int)st, tm.at_cmd ? tm.at_cmd->flags : -1, tm.at_cmd ? tm.at_cmd->worst_ms : -1,
                  m.direct, t_e0, m.e1, m.e2 - m.e1, t_e2, t_primed, ecu::abortName(static_cast<ecu::Abort>(ab)), ab ? ta - 5.0 : NAN, m.ox, s.vapour_purged_kg,
                  s.eng.gas_p_max, (ab == 0 && t_e2 <= kPrepB + kWorst + 1e-9) ? "true" : "false", (ab == 0 && t_e2 <= 1.41 + 1e-9) ? "true" : "false");
    std::string sb(b);
    for (auto p2 = sb.find("nan"); p2 != std::string::npos; p2 = sb.find("nan")) sb.replace(p2, 3, "null");
    arr += sb;
    std::printf("S11 %-34s V %6.2f cm3 (%s) TLM state %d worst %d ms direct %d | cmd->E0 %.3f E1 +%.3f E2 +%.3f cmd->E2 %.3f s | abort %s | unlit %.2f g vapour %.2f g\n",
                fc.name.c_str(), fc.V_cm3, fc.label.c_str(), (int)st, tm.at_cmd ? tm.at_cmd->worst_ms : -1, m.direct, t_e0, m.e1, m.e2 - m.e1, t_e2,
                ecu::abortName(static_cast<ecu::Abort>(ab)), m.ox * 1e3, s.vapour_purged_kg * 1e3);
  }
  arr += "]";
  j.k("cases").raw(arr);
  writeFile(OUT + "/S11_fault_path.json", j.str());
}

int main(int argc, char** argv) {
  const std::string which = argc > 1 ? argv[1] : "all";
  if (argc > 2) OUT = argv[2];
  const int mc = argc > 3 ? std::atoi(argv[3]) : 300;
  if (which == "mission" || which == "all") scMission();
  if (which == "steps" || which == "all") scSteps();
  if (which == "deep" || which == "all") scDeep();
  if (which == "hover" || which == "all") scHover();
  if (which == "aborts" || which == "all") scAborts();
  if (which == "tvc" || which == "all") scTvc();
  if (which == "priming" || which == "all") scPriming();
  if (which == "pcx" || which == "all") scPcXdcr();
  if (which == "mc" || which == "all") scMC(mc);
  if (which == "mcone") scMCone(mc);      // sil mcone <out> <run index>
  if (which == "fold" || which == "all") scFold();
  if (which == "fault") scFaultPath(argc > 3 ? argv[3] : "");   // v2.8 final S11 (sil fault <out_dir> label=cm3,...; calc/fault_path_v1.py)
  {   // v2.7 RC-01: the torch N2O solenoid is never energised without the propane solenoid, over every Sim of this invocation
    std::printf("SIL v2.7 torch N2O-without-propane over all runs of '%s': %ld ms (must be 0)\n", which.c_str(), Sim::g_n2o_alone_ms);
    char b[200]; std::snprintf(b, sizeof b, "{\"id\": \"sil_n2o_alone\", \"version\": \"v2.7\", \"scope\": \"%s\", \"n2o_alone_ms\": %ld, \"pass\": %s}\n",
                               which.c_str(), Sim::g_n2o_alone_ms, Sim::g_n2o_alone_ms == 0 ? "true" : "false");
    writeFile(OUT + "/sil_n2o_alone_" + which + ".json", b);
  }
  if (G_RUNS) {
    std::printf("SIL v2.6 stall-monitor clearance over %d no-fault runs (S1-S5): longest no-progress %.1f ms (time path %.0f ms), jam events %d\n",
                G_RUNS, G_NOPROG * 1e3, ecu::cfg::kPintleStallTime_s * 1e3, G_JAM_NOFAULT);
    char b[300]; std::snprintf(b, sizeof b, "{\"id\": \"sil_monitor_clearance\", \"version\": \"v2.6\", \"runs\": %d, \"noprog_max_s\": %.4f, \"jam_events\": %d, \"time_path_s\": %.3f}\n",
                               G_RUNS, G_NOPROG, G_JAM_NOFAULT, ecu::cfg::kPintleStallTime_s);
    writeFile(OUT + "/sil_monitor_clearance_" + which + ".json", b);
  }
  return 0;
}
