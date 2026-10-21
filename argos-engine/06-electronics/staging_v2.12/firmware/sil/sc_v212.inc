// [v2.12 2026-10-21] ARGOS engine SIL - v2.12 scenarios (included at the end of sil_main.cpp; helpers of sil_main.cpp in scope).
// S13T (REV-ELEC-3 R3-01 A6): the S13 A relight re-run with the C1 seat thermal zero drift (sim.h seat_*) on the Mechanical seat histories
// (Electronics results/v2p12/seat_hist/*.csv from hub 04-fea/v352/c1seat c1_seat_v352_v1.json + the v352 hist npz; calc/v2p12/c1_drift_v2p12.py),
// with and without the seat compensation (option (b), the seat TC on Inputs::tc_bore_K). SIL plant on ASSUMED / Combustion bands: firmware-
// sequencing evidence, not hardware. Every number below is SIM.
namespace v212 {
using v211::jb;

static std::vector<std::array<double, 3>> loadSeatHist(const std::string& path) {
  std::vector<std::array<double, 3>> h;
  FILE* f = std::fopen(path.c_str(), "r");
  if (!f) { std::fprintf(stderr, "S13T: cannot read %s\n", path.c_str()); std::exit(2); }
  char line[512]; bool first = true;
  while (std::fgets(line, sizeof line, f)) {
    if (first) { first = false; continue; }   // header t_s,dT_seat_K,dT_sensor_K,dT_station_K
    double a, b, c, d;
    if (std::sscanf(line, "%lf,%lf,%lf,%lf", &a, &b, &c, &d) == 4) h.push_back({a, b, c});
  }
  std::fclose(f);
  return h;
}

struct DriftOut {
  int rz1 = -1, rz2 = -1;              // -1 not attempted / not evaluated, 0 rejected, 1 accepted
  double rz1_shift = NAN, rz2_shift = NAN, comp_e1 = NAN, drift_e1 = NAN, drift_rz2 = NAN, drift_rz1 = NAN;
  bool not_vented = false, base_high = false, base_amb = false, ran = false, refused = false, ovp_trip = false, tb = false, jfwd = false;
  bool armed = false;                  // ARMED reached (false = ARM refused, e.g. PC_SENSOR on the static thermal zero term)
  int abort = 0, refuse_code = 0; double e2_minus_light_ms = NAN, ovp_vf_max_bar = NAN, ls_raw_bar = NAN, ovp_vf_max_burn1_bar = NAN;
  std::string outcome;
};

// mission: ARM 0.05, PREPRESS 0.80, IGNITE 1.40 (bleed fitted: the pad BIT adds 1.0 s, light ~2.5 s), SHUTDOWN t_sd 3.40 (the SIL burn,
// compressed onto the Mechanical burn by seatMechT), tank jump to the A1 relight state at t_sd + 0.30, PURGE pre-scheduled at
// E0 - kPurgeRelight_s, RELIGHT at E0 = t_sd + (E0_mech - MECO_mech) so the coast is REAL time (A1: 22.211 - 3.541 = 18.670 s; stand
// after B1: S + 18.67 s, Mechanical's stand events)
static DriftOut driftRun(SimConfig c, bool lit, double coast_s, std::string* csv_path = nullptr) {
  const double t_sd = 3.40, t_rl = t_sd + coast_s;
  c.seat_t_sd = t_sd;
  Sim s(c);
  s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {t_sd, Cmd::SHUTDOWN, 0},
                {t_rl - ecu::cfg::kPurgeRelight_s, Cmd::PURGE, 0}, {t_rl, Cmd::RELIGHT, 0}};
  s.thrust_cmd = [t_sd](double t) { return t < t_sd ? 300.0 : 200.0; };
  const A1State a;
  // flight: the A1 relight tank state; stand: the SIL tank after its own burn (no jump: the A1 state is a flight state - the v2.12 pre-run
  // with the jump tripped the S1 MV-seat monitor on the P_tank step and locked the stand out, refuse 6; the stand tank after B1 is TO-VERIFY)
  const bool stand = c.test_stand;
  s.hooks.push_back({t_sd + 0.30, [a, lit, stand](Sim& q) {
    if (!stand) { q.eng.setTankState(a.T, a.m); q.eng.Dport = a.D; }
    if (!lit) q.eng.P.ign_delay = 99.0; }});
  DriftOut o;
  // re-zero1: block from COAST + 1.0 s (200 ticks) -> evaluated at COAST + 1.5 s; re-zero2 at the PURGE command -> evaluated 2 ms after it
  s.hooks.push_back({t_sd + 1.60, [&o](Sim& q) {
    o.rz1 = q.ecu.rezeroApplied() ? 1 : (q.ecu.rezeroRejected() ? 0 : -1); o.rz1_shift = q.ecu.rezeroShift(); o.drift_rz1 = q.seatDriftPa(q.t); }});
  s.hooks.push_back({t_rl - ecu::cfg::kPurgeRelight_s - 0.010, [&o](Sim& q) { o.drift_rz2 = q.seatDriftPa(q.t); }});
  s.hooks.push_back({t_rl - ecu::cfg::kPurgeRelight_s + 0.003, [&o](Sim& q) { o.rz2_shift = q.ecu.rezeroShift(); }});
  double t_e1 = -1.0;
  s.run(t_rl + 1.30);
  const auto& r = s.rec();
  const StartM sm = startM(s, r, 1);
  double ta; o.abort = firstAbortCause(r, &ta);
  if (std::isfinite(sm.te) && std::isfinite(sm.e1)) t_e1 = sm.te + sm.e1;
  double vmax = -1.0, vmax1 = -1.0;
  for (const Rec& x : r) {
    if (x.t < t_sd) vmax1 = std::max(vmax1, x.ovp_vf);
    if (x.t >= t_rl - ecu::cfg::kPurgeRelight_s - 0.001 && x.t < t_rl - ecu::cfg::kPurgeRelight_s + 0.010 && o.rz2 < 0) {
      if (x.fault2 & ecu::f2::REZERO2) o.rz2 = 1; else if (x.fault2 & ecu::f2::REZERO2_REJ) o.rz2 = 0;
    }
    if (x.state == (int)State::ARMED) o.armed = true;
    if (x.t >= t_sd + 0.5) {
      o.not_vented |= (x.fault2 & ecu::f2::NOT_VENTED) != 0;
      o.base_high |= (x.fault2 & ecu::f2::BASE_HIGH) != 0;
      o.base_amb |= (x.ign_det & ecu::det::BASE_AMB) != 0;
      if (x.state == (int)State::RUN) o.ran = true;
    }
    if (x.t >= t_rl - 0.001) vmax = std::max(vmax, x.ovp_vf);
    if (x.relight_block && x.t >= t_rl - 0.001 && x.t < t_rl + 0.003 && !o.refuse_code) o.refuse_code = x.relight_block;
  }
  o.refused = !std::isfinite(sm.te);
  o.ovp_trip = s.ovp_trip_t >= 0.0;
  o.ovp_vf_max_bar = vmax > 0 ? ((vmax - 0.5) / 4.0 * c.pc_fs_abs) / 1e5 : NAN;
  o.ovp_vf_max_burn1_bar = vmax1 > 0 ? ((vmax1 - 0.5) / 4.0 * c.pc_fs_abs) / 1e5 : NAN;
  if (t_e1 > 0) { o.drift_e1 = s.seatDriftPa(t_e1); }
  o.comp_e1 = s.ecu.pcSeatComp();
  o.tb = s.ecu.tbState(); o.jfwd = (s.ecu.f3Flags() & ecu::f3::JFWD_LS) != 0;
  o.ls_raw_bar = std::isfinite(s.ecu.lightSpike().peak_raw_Pa) ? s.ecu.lightSpike().peak_raw_Pa / 1e5 : NAN;
  if (std::isfinite(sm.lit) && std::isfinite(sm.e2)) o.e2_minus_light_ms = (sm.e2 - sm.lit) * 1e3;
  const char* an = ecu::abortName(static_cast<ecu::Abort>(o.abort));
  if (!o.armed) o.outcome = "ARM_REFUSED";
  else if (lit) o.outcome = (o.ran && o.abort == 0) ? "RUN" : o.refused ? "REFUSED" : (std::string(o.ran ? "RUN_then_" : "") + an);
  else o.outcome = o.ran ? "FALSE_E2" : o.refused ? "REFUSED" : (o.abort ? std::string("unlit_") + an : "unlit_NONE");
  if (csv_path && !csv_path->empty()) s.writeCsv(*csv_path);
  return o;
}

static void scS13T() {
  const std::string H = "/home/claude/work/electronics/results/v2p12/seat_hist/";
  const auto hA1 = loadSeatHist(H + "seat_hist_A1_NF2b.csv");
  const auto hHI = loadSeatHist(H + "seat_hist_B1_R4_GVHI.csv");
  const auto hLO = loadSeatHist(H + "seat_hist_B1_R4_GVLO.csv");
  const char* only = std::getenv("S13T_ONLY");   // optional: one case name (timing / debug)
  struct Comp { const char* name; bool tc; double eps, err_K; };
  const Comp comps[] = {{"off", false, 0.0, 0.0}, {"comp", true, 0.0, 0.0}, {"comp_under", true, -0.10, -0.30}, {"comp_over", true, 0.10, 0.30}};
  struct Loc { const char* name; bool stand; const std::vector<std::array<double, 3>>* h; double mech_sd, coast; std::vector<double> T0C; bool unlit; };
  const std::vector<Loc> locs = {
      {"A1_flight", false, &hA1, 3.541, 22.211 - 3.541, {0.0, 20.0, 40.0}, true},
      {"stand_after_B1_GVHI", true, &hHI, 21.651, 18.67, {0.0, 24.0}, true},
      {"stand_after_B1_GVLO", true, &hLO, 21.651, 18.67, {0.0, 24.0}, false}};
  const double ks[] = {1.0, 1.5, 2.0, 3.0};
  J j; j.k("id").v(std::string("S13T_seat_drift")); j.k("version").v(std::string("v2.12")); j.k("build_kBpc1Shown").v(ecu::cfg::kBpc1Shown);
  j.k("kIgnBaseCheck_Pa").v(ecu::cfg::kIgnBaseCheck_Pa); j.k("kPcRezeroMax_Pa").v(ecu::cfg::kPcRezeroMax_Pa);
  j.k("tag").v(std::string("SIM (SIL plant, ASSUMED / Combustion bands) x Mechanical SIM seat history x DATASHEET typical coefficient; k ASSUMED (F-10 MISSING)"));
  std::string arr = "[";
  int n = 0, n_false_e2 = 0, n_lit_not_run = 0, n_arm_refused = 0;
  for (const Loc& L : locs)
    for (double T0 : L.T0C)
      for (const Comp& cp : comps) {
        if (cp.eps != 0.0 && T0 != (L.stand ? 24.0 : 20.0)) continue;   // the coefficient-error variants at the reference T0 only
        for (double sg : {1.0, -1.0})
          for (double k : ks)
            for (int lit = 1; lit >= 0; --lit) {
              if (!lit && (!L.unlit || cp.eps != 0.0)) continue;
              char nm[200];
              std::snprintf(nm, sizeof nm, "%s_T0_%02.0fC_%s_s%+.0f_k%.1f_%s", L.name, T0, cp.name, sg, k, lit ? "lit" : "unlit");
              if (only && std::string(only) != nm) continue;
              SimConfig c = nominal(97);
              c.eng.hb_fitted = true; c.test_stand = L.stand;
              c.seat_drift = true; c.seat_s = sg; c.seat_k = k; c.seat_T0_K = 273.15 + T0; c.seat_hist = *L.h; c.seat_mech_sd_s = L.mech_sd;
              c.seat_tc = cp.tc; c.seat_tc_err_K = cp.err_K;
              c.seat_coef_cal = cp.tc ? sg * k * c.seat_c_PaK * (1.0 + cp.eps) : 0.0;
              std::string csvp = (only ? OUT + "/S13T_" + std::string(nm) + ".csv" : "");
              const DriftOut o = driftRun(c, lit == 1, L.coast, &csvp);
              ++n; if (o.outcome == "FALSE_E2") ++n_false_e2; if (lit && o.outcome != "RUN") ++n_lit_not_run; if (!o.armed) ++n_arm_refused;
              char b[1600];
              std::snprintf(b, sizeof b,
                            "%s{\"case\": \"%s\", \"location\": \"%s\", \"T0_C\": %.0f, \"comp\": \"%s\", \"sign\": %.0f, \"k\": %.1f, \"plant_lit\": %s, \"armed\": %s, "
                            "\"rezero1\": %d, \"rezero1_shift_bar\": %.4f, \"drift_rz1_bar\": %.4f, \"rezero2\": %d, \"rezero2_shift_bar\": %.4f, \"drift_rz2_bar\": %.4f, "
                            "\"drift_E1_bar\": %.4f, \"comp_end_bar\": %.4f, \"NOT_VENTED\": %s, \"BASE_HIGH\": %s, \"BASE_AMB\": %s, \"refused\": %s, \"refuse_code\": %d, "
                            "\"first_abort\": \"%s\", \"outcome\": \"%s\", \"E2_minus_light_ms\": %.1f, \"U330_trip\": %s, \"U330_node_max_relight_bar_abs_equiv\": %.3f, "
                            "\"U330_node_max_burn1_bar_abs_equiv\": %.3f, \"TB_STATE\": %s, \"JFWD_LS\": %s, \"LIGHT_SPIKE_raw_peak_bar_abs\": %.3f}",
                            n > 1 ? ", " : "", nm, L.name, T0, cp.name, sg, k, lit ? "true" : "false", jb(o.armed).c_str(), o.rz1, o.rz1_shift / 1e5, o.drift_rz1 / 1e5, o.rz2,
                            o.rz2_shift / 1e5, o.drift_rz2 / 1e5, o.drift_e1 / 1e5, o.comp_e1 / 1e5, jb(o.not_vented).c_str(), jb(o.base_high).c_str(),
                            jb(o.base_amb).c_str(), jb(o.refused).c_str(), o.refuse_code, ecu::abortName(static_cast<ecu::Abort>(o.abort)), o.outcome.c_str(),
                            o.e2_minus_light_ms, jb(o.ovp_trip).c_str(), o.ovp_vf_max_bar, o.ovp_vf_max_burn1_bar, jb(o.tb).c_str(), jb(o.jfwd).c_str(), o.ls_raw_bar);
              std::string sb(b);
              for (auto p2 = sb.find("-nan"); p2 != std::string::npos; p2 = sb.find("-nan")) sb.replace(p2, 4, "null");
              for (auto p2 = sb.find("nan"); p2 != std::string::npos; p2 = sb.find("nan")) sb.replace(p2, 3, "null");
              arr += sb;
              std::printf("S13T %-58s rz1 %2d rz2 %2d NV %d BH %d BA %d | %-22s E2-light %6.1f ms | U330 %d node %.2f | comp %.3f drift_E1 %.3f\n", nm, o.rz1, o.rz2,
                          (int)o.not_vented, (int)o.base_high, (int)o.base_amb, o.outcome.c_str(), o.e2_minus_light_ms, (int)o.ovp_trip, o.ovp_vf_max_bar,
                          o.comp_e1 / 1e5, o.drift_e1 / 1e5);
              std::fflush(stdout);
            }
      }
  arr += "]";
  j.k("n_runs").v(n); j.k("n_false_E2").v(n_false_e2); j.k("n_lit_not_RUN").v(n_lit_not_run); j.k("n_ARM_refused").v(n_arm_refused);
  j.k("cases").raw(arr);
  if (!only) writeFile(OUT + (ecu::cfg::kBpc1Shown ? "/S13T_seat_drift_bpc1_true.json" : "/S13T_seat_drift_bpc1_false.json"), j.str());
}

// v2.12 (REV-COMB-4 R4-02; N-04 burn-on cases): the S6R setup with NO over-pressure profile (pad start 1.40 s 300 N, MECO 2.40 s, A1 state at
// MECO + 0.3 s, RELIGHT 5.00 s at 200 N; flight, ride-through build) with the 25 us head trace from the RELIGHT command to t_rl + 1.30 s and
// the plant light time. calc/v2p12/r4_02_reclass_v2p12.py composes max(this plant trace, grid history from the plant light) for each burn-on
// grid case (the ride-through build does not abort them: N-04), the S6R replay convention (sim.h gop: the chain sees max(plant, profile)).
static void scTrace0() {
  SimConfig c = nominal(7001);
  c.ride_fw = 1; c.ovp3_tau = ecu::cfg::kRideCmpTauNom_s; c.trace25 = true; c.trace25_from = 5.00;
  Sim s(c);
  const double t_meco = 2.40, t_rl = 5.00;
  s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {t_meco, Cmd::SHUTDOWN, 0}, {t_rl, Cmd::RELIGHT, 0}};
  s.thrust_cmd = [t_meco](double t) { return t < t_meco ? 300.0 : 200.0; };
  const A1State a;
  s.hooks.push_back({t_meco + 0.30, [a](Sim& qq) { qq.eng.setTankState(a.T, a.m); qq.eng.Dport = a.D; }});
  s.run(t_rl + 1.30);
  const auto& r = s.rec();
  double t_light = NAN; for (const Rec& x : r) if (x.t >= t_rl && x.ignited) { t_light = x.t; break; }
  double ta; const int ab = firstAbortCause(r, &ta);
  FILE* tf = std::fopen((OUT + "/trace0_A1_relight_ride_head25us.csv").c_str(), "w");
  if (tf) { std::fprintf(tf, "t_s,p_bar_abs\n"); for (size_t q = 0; q < s.tr25_t.size(); ++q) std::fprintf(tf, "%.6f,%.5f\n", s.tr25_t[q], s.tr25_p[q] / 1e5); std::fclose(tf); }
  char b[400];
  std::snprintf(b, sizeof b, "{\"id\": \"trace0_A1_relight_ride\", \"version\": \"v2.12\", \"t_relight_cmd_s\": %.4f, \"t_plant_light_s\": %.6f, "
                "\"plant_t_lit_s\": %.6f, \"first_abort\": \"%s\", \"n_samples\": %zu, \"tag\": \"SIM (SIL plant, ASSUMED / COMB bands)\"}",
                t_rl, t_light, s.eng.t_lit_plant, ecu::abortName(static_cast<ecu::Abort>(ab)), s.tr25_t.size());
  writeFile(OUT + "/trace0_A1_relight_ride.json", b);
  std::printf("trace0: light %.4f s, abort %s, %zu samples\n", t_light, ecu::abortName(static_cast<ecu::Abort>(ab)), s.tr25_t.size());
}

}  // namespace v212
