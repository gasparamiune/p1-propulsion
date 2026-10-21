// [v2.13 2026-10-21] ARGOS engine SIL - v2.13 scenarios (included after sc_v212.inc; helpers of sil_main.cpp and v212:: in scope).
// S13F (brief A7, REV-ELEC-4 Q2 / section 3): the S13T missions with a TC4 (C1 seat TC) reading FAULT added after the sensor lag
// (SimConfig::seat_tc_fault_*), relight and first starts, lit and unlit, forked from the no-fault control at the IGNITION entry of the start
// (Sim is copyable; the fault starts after the fork). A5 (brief): a TC4 fault in the first burn or the coast, then the relight, with the
// SEAT_STEP relight option off (proceed on the held compensation) and on (refused SEAT_STEP). All runs use the SIL-only seat time-axis
// variant (SimConfig::seat_ts_hook, ECU_SIL_TEST_HOOKS: the TC4 slew and the post-E2 hold on the Mechanical time axis while the S13T seat
// map is compressed; 1 outside the compressed burn) - disclosed. SIL plant on ASSUMED / Combustion bands: firmware-sequencing evidence,
// not hardware. Every number below is SIM.
#include <map>
namespace v213 {
using v211::jb;
using v212::loadSeatHist;

struct Loc { const char* name; bool stand; const std::vector<std::array<double, 3>>* h; double mech_sd, coast; };

static SimConfig baseCfg(const Loc& L, double T0C, double sg, double k) {
  SimConfig c = nominal(97);
  c.eng.hb_fitted = true; c.test_stand = L.stand;
  c.seat_drift = true; c.seat_s = sg; c.seat_k = k; c.seat_T0_K = 273.15 + T0C; c.seat_hist = *L.h; c.seat_mech_sd_s = L.mech_sd;
  c.seat_tc = true; c.seat_tc_err_K = 0.0;
  c.seat_coef_cal = sg * k * c.seat_c_PaK;   // exact coefficient (v212 S13T "comp")
  c.seat_ts_hook = true;
  return c;
}
// the S13T mission of v212::driftRun without its reference-capturing record hooks (forkable): ARM 0.05, PREPRESS 0.80, IGNITE 1.40,
// SHUTDOWN 3.40, tank jump (flight) at 3.70, PURGE at t_rl - kPurgeRelight_s, RELIGHT at t_rl = 3.40 + coast
static Sim mission(SimConfig c, bool lit_relight, bool lit_first, double coast_s) {
  const double t_sd = 3.40, t_rl = t_sd + coast_s;
  c.seat_t_sd = t_sd;
  Sim s(c);
  s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {t_sd, Cmd::SHUTDOWN, 0},
                {t_rl - ecu::cfg::kPurgeRelight_s, Cmd::PURGE, 0}, {t_rl, Cmd::RELIGHT, 0}};
  s.thrust_cmd = [t_sd](double t) { return t < t_sd ? 300.0 : 200.0; };
  if (!lit_first) s.eng.P.ign_delay = 99.0;
  const A1State a; const bool stand = c.test_stand;
  s.hooks.push_back({t_sd + 0.30, [a, lit_relight, stand](Sim& q) {
    if (!stand) { q.eng.setTankState(a.T, a.m); q.eng.Dport = a.D; }
    if (!lit_relight) q.eng.P.ign_delay = 99.0; }});
  return s;
}
struct SOut { std::string outcome; bool armed = false, ran = false, e2_before_light = false, step = false; int abort = 0, refuse = 0;
              double e2_minus_light_ms = NAN, t_e1 = NAN, t_ign = NAN, gap_K = NAN; };
// classify start k (0 first, 1 relight) as v212::driftRun does (lit: RUN / REFUSED / RUN_then_X / X; unlit: FALSE_E2 / REFUSED / unlit_X)
static SOut classify(const Sim& s, size_t k, bool lit, double t_from, double t_to, double t_cmd = -1.0) {
  SOut o; const auto& r = s.rec(); const StartM sm = startM(s, r, k);
  for (const Rec& x : r) {
    if (x.state == (int)State::ARMED) o.armed = true;
    if (x.t >= t_from && x.t < t_to && x.state == (int)State::RUN) o.ran = true;
    if (!o.abort && x.abort) o.abort = x.abort;
    if (!o.refuse && t_cmd > 0.0 && x.t >= t_cmd - 0.001 && x.t < t_cmd + 0.003 && x.relight_block) o.refuse = x.relight_block;
  }
  const bool started = std::isfinite(sm.te);
  if (started) { o.t_ign = sm.te; if (std::isfinite(sm.e1)) o.t_e1 = sm.te + sm.e1; }
  if (std::isfinite(sm.lit) && std::isfinite(sm.e2)) { o.e2_minus_light_ms = (sm.e2 - sm.lit) * 1e3; o.e2_before_light = sm.e2 < sm.lit; }
  if (lit && std::isfinite(sm.e2) && !std::isfinite(sm.lit)) o.e2_before_light = true;   // E2 with no plant light at all
  o.step = s.ecu.pcSeatStep(); o.gap_K = s.ecu.pcSeatHoldGapMaxK();
  const char* an = ecu::abortName(static_cast<ecu::Abort>(o.abort));
  if (!o.armed) o.outcome = "ARM_REFUSED";
  else if (!started) o.outcome = "REFUSED";
  else if (lit) o.outcome = (o.ran && o.abort == 0) ? "RUN" : (std::string(o.ran ? "RUN_then_" : "") + an);
  else o.outcome = o.ran ? "FALSE_E2" : (o.abort ? std::string("unlit_") + an : "unlit_NONE");
  return o;
}
static bool stopAtEntry(const Sim& q, size_t n) { return q.ign_entry_t.size() >= n; }

struct Fault { std::string name; double dK, off_s, dur_s; bool abs_time; };   // off_s from E1 of the start (or absolute time)
static std::vector<Fault> faultSet(bool relight) {
  std::vector<Fault> f;
  for (double d : {-3.0, -5.0, -6.0, -8.0, -10.0, -15.0, -20.0, -30.0, -55.0}) {
    char a[64], b[64];
    std::snprintf(a, sizeof a, "%+.0fK_E1+4ms", d); std::snprintf(b, sizeof b, "%+.0fK_E1-10ms", d);
    f.push_back({a, d, 0.004, 0.0, false}); f.push_back({b, d, -0.010, 0.0, false});
  }
  if (relight) f.push_back({"+90K_from_22.30s", 90.0, 22.30, 0.0, true});
  else f.push_back({"+90K_E1+300ms", 90.0, 0.300, 0.0, false});
  for (double d : {2.0, -2.0}) {   // single-conversion steps (one MAX31856 conversion, 100 ms)
    char a[64], b[64];
    std::snprintf(a, sizeof a, "%+.0fK_1conv_E1+4ms", d); std::snprintf(b, sizeof b, "%+.0fK_1conv_E1-10ms", d);
    f.push_back({a, d, 0.004, 0.100, false}); f.push_back({b, d, -0.010, 0.100, false});
  }
  return f;
}
static std::string sanit(std::string s) {
  for (auto p = s.find("-nan"); p != std::string::npos; p = s.find("-nan")) s.replace(p, 4, "null");
  for (auto p = s.find("nan"); p != std::string::npos; p = s.find("nan")) s.replace(p, 3, "null");
  return s;
}

static void scS13F() {
  const std::string H = "/home/claude/work/electronics/results/v2p12/seat_hist/";
  const auto hA1 = loadSeatHist(H + "seat_hist_A1_NF2b.csv");
  const auto hHI = loadSeatHist(H + "seat_hist_B1_R4_GVHI.csv");
  const auto hLO = loadSeatHist(H + "seat_hist_B1_R4_GVLO.csv");
  const Loc lA1{"A1_flight", false, &hA1, 3.541, 22.211 - 3.541}, lHI{"stand_after_B1_GVHI", true, &hHI, 21.651, 18.67},
            lLO{"stand_after_B1_GVLO", true, &hLO, 21.651, 18.67};
  struct LT { const Loc* L; double T0; };
  const std::vector<LT> lts = {{&lA1, 20.0}, {&lA1, 0.0}, {&lA1, 40.0}, {&lHI, 24.0}, {&lHI, 0.0}, {&lLO, 24.0}, {&lLO, 0.0}};
  int n = 0, n_false_e2 = 0, n_e2_before = 0, n_lit_fail = 0, n_unlit_fail = 0, n_other_diff = 0, n_ctl = 0, n_skipped = 0;
  std::string arr = "[", fails = "[";
  for (int relight = 1; relight >= 0; --relight)
    for (const LT& lt : lts)
      for (double k : {1.0, 3.0})
        for (double sg : {1.0, -1.0})
          for (int lit = 1; lit >= 0; --lit) {
            const Loc& L = *lt.L;
            const SimConfig c = baseCfg(L, lt.T0, sg, k);
            const double t_rl = 3.40 + L.coast, t_end_rl = t_rl + 1.30;
            char cn[200];
            std::snprintf(cn, sizeof cn, "%s_%s_T0_%02.0fC_s%+.0f_k%.0f_%s", relight ? "relight" : "first", L.name, lt.T0, sg, k, lit ? "lit" : "unlit");
            // control (no fault): first start lit unless the unlit FIRST-start set
            const bool lit_first = relight ? true : (lit == 1);
            Sim ctl = mission(c, lit == 1, lit_first, L.coast);
            ctl.runUntil(relight ? t_end_rl : 6.0, [relight](const Sim& q) { return stopAtEntry(q, relight ? 2 : 1); });
            const bool have_entry = ctl.ign_entry_t.size() >= (size_t)(relight ? 2 : 1);
            Sim pre = ctl;   // fork point: the tick of the IGNITION entry of the start (before every fault start)
            double t_to = relight ? t_end_rl : 1e9;
            if (have_entry && !relight) t_to = ctl.ign_entry_t[0] + 0.045 + 1.00;   // first start: E1 (entry + 45 ms) + 1.0 s
            ctl.run(t_to);
            const SOut co = classify(ctl, relight ? 1 : 0, lit == 1, relight ? 3.90 : 0.0, relight ? 1e9 : t_to + 1e-9);
            ++n_ctl;
            char b[900];
            std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"fault\": \"none\", \"outcome\": \"%s\", \"E2_minus_light_ms\": %.1f, \"SEAT_STEP\": %s, \"t_E1\": %.4f}",
                          arr.size() > 1 ? ", " : "", cn, co.outcome.c_str(), co.e2_minus_light_ms, jb(co.step).c_str(), co.t_e1);
            arr += sanit(b);
            std::printf("S13F %-62s %-26s control %-22s E2-light %6.1f step %d\n", cn, "none", co.outcome.c_str(), co.e2_minus_light_ms, (int)co.step);
            if (!have_entry || !std::isfinite(co.t_e1) || co.outcome == "ARM_REFUSED" || co.outcome == "REFUSED") { ++n_skipped; continue; }
            for (const Fault& f : faultSet(relight == 1)) {
              Sim q = pre;
              q.C.seat_tc_fault_K = f.dK; q.C.seat_tc_fault_from = f.abs_time ? f.off_s : co.t_e1 + f.off_s; q.C.seat_tc_fault_dur = f.dur_s;
              q.run(t_to);
              const SOut o = classify(q, relight ? 1 : 0, lit == 1, relight ? 3.90 : 0.0, relight ? 1e9 : t_to + 1e-9);
              ++n;
              bool pass = true; std::string why;
              if (o.outcome == "FALSE_E2") { ++n_false_e2; pass = false; why = "FALSE_E2"; }
              if (lit && o.e2_before_light) { ++n_e2_before; pass = false; why += " E2_before_light"; }
              if (co.outcome == "RUN" && o.outcome != "RUN") { ++n_lit_fail; pass = false; why += " lit_not_RUN"; }
              if (co.outcome == "unlit_NO_IGNITION" && o.outcome != "unlit_NO_IGNITION") { ++n_unlit_fail; pass = false; why += " unlit_not_NO_IGNITION"; }
              if (co.outcome != "RUN" && co.outcome != "unlit_NO_IGNITION" && o.outcome != co.outcome) { ++n_other_diff; pass = false; why += " differs_from_control"; }
              std::snprintf(b, sizeof b, ", {\"case\": \"%s\", \"fault\": \"%s\", \"outcome\": \"%s\", \"control\": \"%s\", \"E2_minus_light_ms\": %.1f, "
                            "\"SEAT_STEP\": %s, \"hold_gap_max_K\": %.3f, \"pass\": %s}",
                            cn, f.name.c_str(), o.outcome.c_str(), co.outcome.c_str(), o.e2_minus_light_ms, jb(o.step).c_str(), o.gap_K, jb(pass).c_str());
              arr += sanit(b);
              if (!pass) { fails += sanit(std::string(fails.size() > 1 ? ", " : "") + "\"" + cn + " " + f.name + ": " + o.outcome + " (" + why + ")\""); }
              std::printf("S13F %-62s %-26s %-24s E2-light %6.1f step %d %s\n", cn, f.name.c_str(), o.outcome.c_str(), o.e2_minus_light_ms, (int)o.step,
                          pass ? "" : ("FAIL" + why).c_str());
              std::fflush(stdout);
            }
          }
  arr += "]"; fails += "]";
  J j; j.k("id").v(std::string("S13F_tc4_fault")); j.k("version").v(std::string("v2.13")); j.k("build_kBpc1Shown").v(ecu::cfg::kBpc1Shown);
  j.k("seat_ts_hook").v(true);
  j.k("tag").v(std::string("SIM (SIL plant, ASSUMED / Combustion bands) x Mechanical SIM seat history; TC4 faults are TEST VALUES (brief A7 / REV-ELEC-4)"));
  j.k("pass_rule").v(std::string("0 FALSE_E2; 0 E2 before the plant light; control RUN -> fault RUN with no abort; control unlit_NO_IGNITION -> "
                                 "fault unlit_NO_IGNITION; any other control outcome -> the same outcome"));
  j.k("n_controls").v(n_ctl); j.k("n_controls_without_start").v(n_skipped); j.k("n_fault_runs").v(n); j.k("n_FALSE_E2").v(n_false_e2);
  j.k("n_E2_before_light").v(n_e2_before); j.k("n_lit_not_RUN").v(n_lit_fail); j.k("n_unlit_not_NO_IGNITION").v(n_unlit_fail);
  j.k("n_other_differs").v(n_other_diff); j.k("failures").raw(fails); j.k("runs").raw(arr);
  writeFile(OUT + (ecu::cfg::kBpc1Shown ? "/S13F_tc4_fault_bpc1_true.json" : "/S13F_tc4_fault_bpc1_false.json"), j.str());
  std::printf("S13F: %d controls (%d without the start), %d fault runs: FALSE_E2 %d, E2 before light %d, lit not RUN %d, unlit not NO_IGNITION %d, "
              "other differs %d\n", n_ctl, n_skipped, n, n_false_e2, n_e2_before, n_lit_fail, n_unlit_fail, n_other_diff);
}

// A5: a TC4 fault (+/- 5 K persistent step: SEAT_STEP latches, the compensation is held) in the first burn (t 2.90 s, RUN) or the coast
// (t 10.0 s), then the relight; seat_step_relight_inhibit off (proceed held) and on (refused SEAT_STEP). Control = the same run, no fault.
static void scA5() {
  const std::string H = "/home/claude/work/electronics/results/v2p12/seat_hist/";
  const auto hA1 = loadSeatHist(H + "seat_hist_A1_NF2b.csv");
  const auto hHI = loadSeatHist(H + "seat_hist_B1_R4_GVHI.csv");
  const auto hLO = loadSeatHist(H + "seat_hist_B1_R4_GVLO.csv");
  const Loc lA1{"A1_flight", false, &hA1, 3.541, 22.211 - 3.541}, lHI{"stand_after_B1_GVHI", true, &hHI, 21.651, 18.67},
            lLO{"stand_after_B1_GVLO", true, &hLO, 21.651, 18.67};
  struct LT { const Loc* L; double T0; };
  const std::vector<LT> lts = {{&lA1, 20.0}, {&lHI, 24.0}, {&lLO, 24.0}};
  std::string arr = "[";
  int n = 0, n_false_e2 = 0, n_e2_before = 0, n_abort_lit = 0, n_lost = 0, n_ctl_run = 0, n_run = 0;
  std::map<std::string, int> tally;
  for (const LT& lt : lts)
    for (double k : {1.0, 3.0})
      for (double sg : {1.0, -1.0})
        for (int lit = 1; lit >= 0; --lit) {
          const Loc& L = *lt.L; const double t_end = 3.40 + L.coast + 1.30;
          SimConfig c = baseCfg(L, lt.T0, sg, k);
          char cn[200];
          std::snprintf(cn, sizeof cn, "%s_T0_%02.0fC_s%+.0f_k%.0f_%s", L.name, lt.T0, sg, k, lit ? "lit" : "unlit");
          Sim ctl = mission(c, lit == 1, true, L.coast);
          ctl.run(2.85); Sim pre_burn = ctl; ctl.run(9.95); Sim pre_coast = ctl; ctl.run(t_end);
          const SOut co = classify(ctl, 1, lit == 1, 3.90, 1e9, 3.40 + L.coast);
          if (lit && co.outcome == "RUN") ++n_ctl_run;
          char b[900];
          std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"fault\": \"none\", \"option\": \"-\", \"outcome\": \"%s\", \"SEAT_STEP\": %s}", arr.size() > 1 ? ", " : "",
                        cn, co.outcome.c_str(), jb(co.step).c_str());
          arr += sanit(b);
          std::printf("A5 %-48s %-14s %-8s control %-22s step %d\n", cn, "none", "-", co.outcome.c_str(), (int)co.step);
          for (int at = 0; at < 2; ++at)
            for (double d : {5.0, -5.0})
              for (int inh = 0; inh < 2; ++inh) {
                if (inh && !(k == 3.0 && sg > 0.0 && lit)) continue;   // the inhibit option on a subset (its refusal is deterministic)
                Sim q = at == 0 ? pre_burn : pre_coast;
                q.C.seat_tc_fault_K = d; q.C.seat_tc_fault_from = at == 0 ? 2.90 : 10.0; q.C.seat_tc_fault_dur = 0.0;
                q.ecu.seat_step_relight_inhibit = inh == 1; q.C.seat_step_inhibit_fw = inh;
                q.run(t_end);
                const SOut o = classify(q, 1, lit == 1, 3.90, 1e9, 3.40 + L.coast);
                ++n;
                if (o.outcome == "FALSE_E2") ++n_false_e2;
                if (lit && o.e2_before_light) ++n_e2_before;
                if (lit && o.outcome != "RUN" && o.outcome != "REFUSED") ++n_abort_lit;
                if (lit && o.outcome == "REFUSED") ++n_lost;
                if (lit && o.outcome == "RUN") ++n_run;
                char fn[64]; std::snprintf(fn, sizeof fn, "%+.0fK_%s", d, at == 0 ? "burn1_2.90s" : "coast_10.0s");
                ++tally[std::string(inh ? "inhibit " : "proceed ") + (lit ? "lit " : "unlit ") + o.outcome];
                std::snprintf(b, sizeof b, ", {\"case\": \"%s\", \"fault\": \"%s\", \"option\": \"%s\", \"outcome\": \"%s\", \"control\": \"%s\", "
                              "\"refuse_code\": %d, \"E2_minus_light_ms\": %.1f, \"SEAT_STEP\": %s, \"first_abort\": \"%s\"}",
                              cn, fn, inh ? "inhibit" : "proceed", o.outcome.c_str(), co.outcome.c_str(), o.refuse, o.e2_minus_light_ms, jb(o.step).c_str(),
                              ecu::abortName(static_cast<ecu::Abort>(o.abort)));
                arr += sanit(b);
                std::printf("A5 %-48s %-14s %-8s %-24s control %-22s refuse %2d step %d\n", cn, fn, inh ? "inhibit" : "proceed", o.outcome.c_str(),
                            co.outcome.c_str(), o.refuse, (int)o.step);
                std::fflush(stdout);
              }
        }
  arr += "]";
  std::string ts = "{";
  for (const auto& kv : tally) ts += std::string(ts.size() > 1 ? ", " : "") + "\"" + kv.first + "\": " + std::to_string(kv.second);
  ts += "}";
  J j; j.k("id").v(std::string("A5_seat_step_relight")); j.k("version").v(std::string("v2.13")); j.k("build_kBpc1Shown").v(ecu::cfg::kBpc1Shown);
  j.k("seat_ts_hook").v(true);
  j.k("tag").v(std::string("SIM (SIL plant, ASSUMED / Combustion bands) x Mechanical SIM seat history; the TC4 faults are TEST VALUES"));
  j.k("n_runs").v(n); j.k("n_FALSE_E2").v(n_false_e2); j.k("n_E2_before_light").v(n_e2_before); j.k("n_lit_abort_or_other").v(n_abort_lit);
  j.k("n_lit_refused").v(n_lost); j.k("n_lit_RUN").v(n_run); j.k("n_lit_controls_RUN").v(n_ctl_run); j.k("tally").raw(ts); j.k("runs").raw(arr);
  writeFile(OUT + (ecu::cfg::kBpc1Shown ? "/A5_seat_step_relight_bpc1_true.json" : "/A5_seat_step_relight_bpc1_false.json"), j.str());
  std::printf("A5: %d runs, FALSE_E2 %d, E2 before light %d, lit RUN %d, lit refused %d, lit abort/other %d; tally %s\n", n, n_false_e2, n_e2_before, n_run,
              n_lost, n_abort_lit, ts.c_str());
}
}  // namespace v213
