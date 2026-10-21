// v2.11 S17 sweep against GNC's R2 v2 (LEAD CHANGELOG 216 (1), 227 (5) / (6), 230 (5); REV-ELEC-2 R2-01, R2-16, R2-23). Included by sil_main.cpp
// after sc_v211.inc.   sil r2v2 <out>      (SIL_R2V2_QUICK=1: smoke test, 4 onsets; SIL_R2V2_DBG=pl,F,dead,onset_ms,report: one trace)
// METHOD. One closed-loop SIL run (ECU firmware + plant, flight A1 relight: pad start 1.40 s 300 N, MECO 2.40 s, A1 state at MECO + 0.3 s,
// RELIGHT 5.00 s at 200 / 500 N) per (family, command, drogue report, lit / dead, Pc-loss onset). The FC stand-in only sends DROGUE 1 at 2.90 s
// (with the report; without it the ECU never holds) and takes no decision in the loop: every FC decision happens at or after the Pc-invalid
// counting start and the ECU's behaviour before a decision does not depend on it (causal), so the R2 v2 rule is evaluated OFFLINE on the
// recorded 1 ms history for every frame phase, window, flush option, reference option and noise level. After a decision the run is not
// used. GNC R2 v2 (staging_v3.1/rev4 REPORT-GNC-rev4-HANDBACK.md section 6; rev3 results/eval/r2v2_eval.json 4d5ddc5da93a16df, flame-out
// side NOT withdrawn, lit side WITHDRAWN W2 by rev4 withdrawn_markers): mode-3 thrust estimate = first-order low-pass (tau 20 ms) of the
// accelerometer thrust minus the reference sampled at E2 (drag-compensated); counting starts at the first step with E2 and Pc invalid;
// frames every 10 ms from that step (phase TO-VERIFY: all 10 phases run); release on 3 consecutive frames >= 37.159 N inside E2 + W
// (W 0.5 / 0.8 s), else ABORT at E2 + W. FC side before the counting start (as the v2.10 stand-in): release on a TLM_FAST frame (even ms)
// with Pc valid and filtered Pc >= 3.0 bar abs (branch 1) or RISE_HELD_T (branch 2).
// STATISTIC on the SIL history: s_k = LP20(F_true)(t_k) - ref + d + noise_k. F_true = plant thrust while lit, Combustion v2.4a cold-flow
// thrust (bound, x cold_scale) at the plant lift while unlit with N2O flowing. d = GNC's dynamics-only statistic bound (fo_none max of the
// 3-frame minimum, mode 3): W10 < 6 m/s 18.996 / 19.831 N, all winds 22.333 / 29.158 N (0.5 / 0.8 s), applied to every frame (superposition
// of maxima: conservative against GNC's fo_cb design max 31.183 / 31.861 N). Lit side d = 0 (sensitivity -12 N: GNC lit_k100 minima 50.38 /
// 53.80 against 62.5 N, a WITHDRAWN arm, used only as a sensitivity). Options: flush = the mode-3 filter re-initialised at the counting
// start (state := reference: estimate 0, LEAD 227 (6)). Reference thrust content: ref 0 = none (GNC sim6 assumption), ref 1 = the
// unflushed LP at the ECU-reported E2 (a flight FC sampling at the E2 report), ref 2 = the LP at the plant light (GNC's timing with the SIL
// thrust content: N2O cold flow from the ignition lift is already acting). ref 0 is the bound for the dead side, ref 1 / 2 for the lit side.
// Noise: iid N(0, sigma^2) per frame [ASSUMED iid, as RV6-07]: release probability by an exact forward recursion over the frames (run-length
// states 0 / 1 / 2), cross-checked by seeded Monte Carlo; sensitivity AR(1) rho = exp(-10 ms / 20 ms) (white noise through the 20 ms filter,
// seeded MC). SIL plant on ASSUMED / COMB SIM inputs; not physical approval.
// v2.11 second pass (same scenario): (a) fc_pc_branch false = the FC Pc branch (Pc_f >= 3.0 bar abs on a frame before the Pc loss) is not
// available, so mode 3 decides a NORMAL start too (normal family: Pc_f at E2 = 3.04 bar abs, 0.04 bar above the branch threshold; with the
// branch every normal run is released at the E2 frame); (b) families *_noopt: dead runs with the photodiode NOT viewing the main chamber
// (SimConfig photo_sees_main false, FMEA case: FLAMEOUT_OPT never arms), so R2 alone decides the dead side for every onset 1-50 ms (with the
// view proven the optical flame-out aborts onsets >= 17 ms before the FC decides). The noise budget is taken over every dead evaluation of
// every family with the hold (bounding run named). Third pass (2026-10-21): per-family iid sigma(1e-2), P(5 N), bounding run and AR(1)
// sensitivity in the noise budget (the second pass gave the AR(1) figures on the overall bounding run only, a *_noopt run).
#include <chrono>
namespace v211 {

constexpr double kR2T_N = 37.159, kR2Tau = 0.020;                                     // [GNC rev2 T 37.159 N; mode-3 tau 20 ms]
constexpr double kDW6[2] = {18.996, 19.831}, kDAll[2] = {22.333, 29.158};             // [GNC r2v2_eval fo_none mode 3, max over bases]
constexpr double kFoCbW6[2] = {31.183, 31.861};                                       // [GNC r2v2_eval mode3 W10_lt6 flameout_design_max]
constexpr double kWin[2] = {0.5, 0.8};
constexpr double kFminLit_N = 33.14;                                                  // [LEAD 230 (5), Combustion v2.4b P4c F_min at 0.21776 mm]
constexpr double kColdScaleHi = 1.30;                                                 // [GNC r2v2_eval fo_cb130 sensitivity: cold flow x 1.3]
static const char* kRefName[3] = {"none_GNC_sim6", "LP_at_ECU_E2", "LP_at_plant_light"};

static FILE* g_r2dbg = nullptr;   // debug trace (SIL_R2V2_DBG, see scR2v2): one line per ms from the reference E2 - 20 ms
struct R2Tr {
  std::string fam; double F_rl = 0, plateau = 0; bool report = false, dead = false; double onset = NAN;
  double t0 = 0, e2 = NAN, t_light = NAN, t_leave = NAN; int ecu_abort = 0;
  std::vector<float> F; std::vector<uint8_t> b;   // b: 1 lit, 2 pc_valid, 4 Pc_f >= 3 bar valid, 8 RISE_HELD_T, 16 r2_hold, 32 ECU RUN, 64 cold flow
  int hold_ticks = 0; double t_hold0 = NAN, t_backstop = NAN, lift_hold = NAN, F_hold_lit = NAN, F_hold_dead = NAN;
  double t_cmp = NAN, pc_pre_bar = NAN, pcf_max_bar = NAN; int glitch_hold_ticks = 0;   // R2-23 glitch runs
};
static R2Tr r2Plant(const std::string& fam, double F_rl, double plateau, bool report, bool dead, double onset, double e2_ref, uint32_t seed,
                    double glitch_at = -1.0, int ride = -1, bool photo_main = true) {
  SimConfig c = nominal(seed);
  c.photo_sees_main = photo_main;   // false: FLAMEOUT_OPT never arms (FMEA case)
  if (ride >= 0) { c.ride_fw = ride; c.ovp3_tau = ride ? ecu::cfg::kRideCmpTauNom_s : ovp3::kTau_s; }
  Sim s(c);
  const double t_meco = 2.40, t_rl = 5.00, t_end = t_rl + 1.25;
  s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {t_meco, Cmd::SHUTDOWN, 0}, {t_rl, Cmd::RELIGHT, 0}};
  s.thrust_cmd = [t_meco, F_rl](double t) { return t < t_meco ? 300.0 : F_rl; };
  const A1State a;
  s.hooks.push_back({t_meco + 0.30, [a](Sim& q) { q.eng.setTankState(a.T, a.m); q.eng.Dport = a.D; }});
  if (plateau > 0.0) s.hooks.push_back({t_rl - 0.01, [plateau](Sim& z) { z.eng.P.starve_s = plateau; z.eng.P.starve_pc_cap_Pa = 2.6e5; }});
  if (std::isfinite(e2_ref) && std::isfinite(onset)) {
    s.pc_sensor_fail_at = e2_ref + onset;
    if (dead) { const double tf = e2_ref + onset + 0.001; s.hooks.push_back({tf - 1e-4, [tf](Sim& z) { z.eng.P.flameout_at = tf; }}); }
  }
  // R2-23 glitch: the C1 conditioner output at its rail for 1.0 ms ending 0.2 ms before the HAL read at glitch_at, so that exactly the 4 ADC
  // samples averaged into that read are at the rail (AAF tau 67 us settled): ONE HIGH over-range tick at glitch_at; the comparator tap sees 1.0 ms
  if (glitch_at > 0.0) { s.pc_stuck_high_at = glitch_at - 1.2e-3; s.pc_stuck_high_to = glitch_at - 0.2e-3; }
  R2Tr R; R.fam = fam; R.F_rl = F_rl; R.plateau = plateau; R.report = report; R.dead = dead; R.onset = onset; R.t0 = t_rl - 0.05;
  bool deployed = false; double sx = 0, sfl = 0, sfd = 0; int nx = 0, nfl = 0, nfd = 0;
  while (s.t < t_end - 1e-9) {
    if (report && !deployed && s.t + 1e-9 >= 2.90) { deployed = true; schedInsert(s, s.t, Cmd::DROGUE, 1); }
    if (glitch_at > 0.0 && std::fabs(s.t - (glitch_at - 2e-3)) < 1e-7) R.pc_pre_bar = s.eng.Pc / 1e5;
    s.run(s.t + 1e-3);
    const double tk = s.t - 1e-3;
    if (tk < R.t0 - 1e-9) continue;
    const bool lit = s.eng.ignited, cold = !lit && s.eng.mox > 1e-3;
    R.F.push_back(static_cast<float>(lit ? s.eng.thrust : (cold ? coldFlowN(s.pintle.x * 1e3, false) : 0.0)));
    const bool run = s.out.state == State::RUN;
    R.b.push_back(static_cast<uint8_t>((lit ? 1 : 0) | (s.out.pc_valid ? 2 : 0) | ((s.out.pc_valid && s.ecu.pcAbsFiltered() >= kDroguePcAbs_Pa) ? 4 : 0) |
                                       ((s.out.tlm_flags & ecu::tlmf::RISE_HELD_T) ? 8 : 0) | (s.out.r2_hold ? 16 : 0) | (run ? 32 : 0) | (cold ? 64 : 0)));
    if (std::isnan(R.t_light) && lit) R.t_light = tk;
    if (std::isnan(R.e2) && run && (s.out.tlm_flags & ecu::tlmf::E2)) R.e2 = s.out.state_t_ms * 1e-3;
    if (std::isfinite(R.e2) && std::isnan(R.t_leave) && !run && tk > R.e2) { R.t_leave = tk; R.ecu_abort = static_cast<int>(s.out.abort_cause); }
    if (s.out.r2_hold) {
      ++R.hold_ticks;
      if (std::isnan(R.t_hold0)) R.t_hold0 = tk;
      if (tk > R.t_hold0 + 0.05 - 1e-9) {   // steady hold (the first 50 ms are the servo slew from the closed-loop lift)
        sx += s.pintle.x * 1e3; ++nx;
        if (lit) { sfl += s.eng.thrust; ++nfl; } else if (cold) { sfd += R.F.back(); ++nfd; }
      }
    }
    if (glitch_at > 0.0 && tk >= glitch_at - 2e-3 - 1e-9 && tk < glitch_at + 0.030) {
      if (s.out.r2_hold) ++R.glitch_hold_ticks;
      const double pf = s.ecu.pcAbsFiltered() / 1e5;
      R.pcf_max_bar = std::isnan(R.pcf_max_bar) ? pf : std::max(R.pcf_max_bar, pf);
    }
    if (std::isnan(R.t_backstop) && s.out.r2_backstop_event) R.t_backstop = tk;
    if (g_r2dbg && std::isfinite(e2_ref) && tk >= e2_ref - 0.020)
      std::fprintf(g_r2dbg, "%.0f,%d,%d,%d,%d,%.5f,%.5f,%.3f,%.4f,%.4f,%d\n", (tk - e2_ref) * 1e3, static_cast<int>(s.out.state), s.out.pc_valid ? 1 : 0,
                   s.out.r2_hold ? 1 : 0, lit ? 1 : 0, s.pintle.x * 1e3, s.out.pintle_cmd_m * 1e3, R.F.back(), s.eng.Pc / 1e5, s.ecu.pcAbsFiltered() / 1e5,
                   static_cast<int>(s.out.abort_cause));
  }
  if (s.ovp_trip_t >= 0.0) R.t_cmp = s.ovp_trip_t;
  if (nx) R.lift_hold = sx / nx;
  if (nfl) R.F_hold_lit = sfl / nfl;
  if (nfd) R.F_hold_dead = sfd / nfd;
  return R;
}

struct R2Cfg { int w = 1; int phase = 0; bool flush = true; int ref = 0; double d = 0.0; double lit_cap = 1e9; double cold_scale = 1.0; bool pcb = true; };
// outcome codes
enum R2O { O_NONE = 0, O_LIT_REL = 1, O_DEAD_REL = 2, O_LIT_AB = 3, O_DEAD_AB = 4, O_ECU_LEFT = 5, O_NO_R2 = 6 };
static const char* r2oName(int o) {
  static const char* n[] = {"NONE", "LIT_RELEASED", "DEAD_RELEASED", "LIT_ABORT", "DEAD_ABORT", "ECU_LEFT_RUN", "NO_R2_WINDOW"};
  return n[o];
}
struct R2Det {
  int out = O_NONE, branch = 0; double t_dec = NAN, t_c = NAN, stat = -1e9; int k_stat = -1;
  std::vector<double> mu; std::vector<uint8_t> dead;   // frames inside the window (for the noise recursion)
  double est_c = NAN, ref_N = NAN;
};
static inline double r2F(const R2Tr& tr, int i, const R2Cfg& c) {
  double f = tr.F[i];
  if ((tr.b[i] & 1) && (tr.b[i] & 16)) f = std::min(f, c.lit_cap);   // F_min sensitivity: lit thrust during the hold capped
  if (!(tr.b[i] & 1) && (tr.b[i] & 64)) f *= c.cold_scale;          // cold-flow sensitivity (GNC fo_cb130)
  return f;
}
// reference values of a run (LP20 of F at the plant light and at the ECU E2)
static void r2Refs(const R2Tr& tr, double* at_light, double* at_e2) {
  const double a = 1.0 - std::exp(-1e-3 / kR2Tau);
  const int il = std::isfinite(tr.t_light) ? static_cast<int>(std::lround((tr.t_light - tr.t0) * 1000.0)) : -1;
  const int ie = std::isfinite(tr.e2) ? static_cast<int>(std::lround((tr.e2 - tr.t0) * 1000.0)) : -1;
  double y = 0.0; *at_light = NAN; *at_e2 = NAN;
  for (int i = 0; i < static_cast<int>(tr.F.size()); ++i) { y += (tr.F[i] - y) * a; if (i == il) *at_light = y; if (i == ie) *at_e2 = y; }
}
static R2Det r2Eval(const R2Tr& tr, const R2Cfg& c) {
  R2Det d;
  const int n = static_cast<int>(tr.F.size());
  auto idx = [&](double t) { return static_cast<int>(std::lround((t - tr.t0) * 1000.0)); };
  if (!std::isfinite(tr.e2)) { d.out = O_NONE; return d; }
  const int ie2 = idx(tr.e2), iend = std::min(n - 1, idx(tr.e2 + kWin[c.w]));
  const int il = std::isfinite(tr.t_light) ? idx(tr.t_light) : ie2;
  const double a = 1.0 - std::exp(-1e-3 / kR2Tau);
  std::vector<double> lp(n);
  double y = 0.0;
  for (int i = 0; i < n; ++i) { y += (r2F(tr, i, c) - y) * a; lp[i] = y; }
  // FC side before the counting start: TLM_FAST frames (even ms), Pc branch / b7, then the first frame with Pc invalid
  int ic = -1;
  for (int i = ie2; i <= iend; ++i) {
    if (!(tr.b[i] & 32)) { d.out = O_ECU_LEFT; d.t_dec = (i - ie2) * 1e-3; return d; }
    const long ms = std::lround((tr.t0 + i * 1e-3) * 1000.0);
    if (ms % 2 != 0) continue;
    if (c.pcb && (tr.b[i] & 4)) { d.out = (tr.b[i] & 1) ? O_LIT_REL : O_DEAD_REL; d.branch = 1; d.t_dec = (i - ie2) * 1e-3; return d; }
    if (tr.b[i] & 8) { d.out = (tr.b[i] & 1) ? O_LIT_REL : O_DEAD_REL; d.branch = 2; d.t_dec = (i - ie2) * 1e-3; return d; }
    if (!(tr.b[i] & 2)) { ic = i; break; }
  }
  if (ic < 0) { d.out = O_NO_R2; return d; }
  d.t_c = (ic - ie2) * 1e-3;
  const double ref = c.ref == 1 ? lp[ie2] : (c.ref == 2 ? lp[il] : 0.0);
  d.ref_N = ref;
  // estimate: with the flush the filter restarts at ic from the reference state (estimate 0)
  std::vector<double> est(n, 0.0);
  double yf = ref;
  for (int i = ic; i < n; ++i) {
    if (c.flush) { yf += (r2F(tr, i, c) - yf) * a; est[i] = yf - ref; } else est[i] = lp[i] - ref;
  }
  d.est_c = est[ic];
  int run = 0;
  for (int i = ic + c.phase; i <= iend; i += 10) {
    bool left = false;   // the ECU left RUN before this frame: no FC decision any more
    for (int q = std::max(ic, i - 10 + 1); q <= i; ++q) if (!(tr.b[q] & 32)) left = true;
    if (left) { if (d.out == O_NONE) { d.out = O_ECU_LEFT; d.t_dec = (i - ie2) * 1e-3; } break; }
    const double mu = est[i] + c.d;
    d.mu.push_back(mu); d.dead.push_back((tr.b[i] & 1) ? 0 : 1);
    const int m = static_cast<int>(d.mu.size());
    if (m >= 3) {
      const double s3 = std::min(d.mu[m - 1], std::min(d.mu[m - 2], d.mu[m - 3]));
      if (s3 > d.stat) { d.stat = s3; d.k_stat = m - 1; }
    }
    if (d.out == O_NONE) {
      run = mu >= kR2T_N ? run + 1 : 0;
      if (run >= 3) { d.out = (tr.b[i] & 1) ? O_LIT_REL : O_DEAD_REL; d.branch = 4; d.t_dec = (i - ie2) * 1e-3; }
    }
  }
  if (d.out == O_NONE) { d.out = (tr.b[iend] & 1) ? O_LIT_AB : O_DEAD_AB; d.t_dec = kWin[c.w]; }
  return d;
}
// exact release probabilities with iid N(0, sigma^2) frame noise: forward recursion over the run length of consecutive exceedances
struct R2P { double p_dead = 0.0, p_lit = 0.0; };
static R2P r2Prob(const R2Det& d, double sigma) {
  R2P o;
  double P0 = 1.0, P1 = 0.0, P2 = 0.0;
  for (size_t k = 0; k < d.mu.size(); ++k) {
    const double p = sigma > 0.0 ? 0.5 * std::erfc((kR2T_N - d.mu[k]) / (sigma * M_SQRT2)) : (d.mu[k] >= kR2T_N ? 1.0 : 0.0);
    const double rel = P2 * p;
    if (d.dead[k]) o.p_dead += rel; else o.p_lit += rel;
    const double q = 1.0 - p;
    const double n0 = (P0 + P1 + P2) * q, n1 = P0 * p, n2 = P1 * p;
    P0 = n0; P1 = n1; P2 = n2;
  }
  return o;
}
// seeded Monte Carlo: iid (rho 0) or stationary AR(1) frame noise; common random numbers for a given seed (monotone in sigma)
static double r2Mc(const R2Det& d, double sigma, double rho, int N, uint32_t seed) {
  std::mt19937 g(seed); std::normal_distribution<double> nd(0.0, 1.0);
  const double sq = std::sqrt(std::max(0.0, 1.0 - rho * rho));
  int nrel = 0;
  for (int r = 0; r < N; ++r) {
    int run = 0; double e = nd(g);
    for (size_t k = 0; k < d.mu.size(); ++k) {
      if (k) e = rho * e + sq * nd(g);
      run = (d.mu[k] + sigma * e >= kR2T_N) ? run + 1 : 0;
      if (run >= 3) { if (d.dead[k]) ++nrel; break; }
    }
  }
  return static_cast<double>(nrel) / N;
}
static double r2SigmaFor(const std::function<double(double)>& P, double target) {   // largest sigma with P(sigma) <= target (P monotone)
  double lo = 0.01, hi = 20.0;
  if (P(lo) > target) return 0.0;
  if (P(hi) <= target) return hi;
  for (int it = 0; it < 40; ++it) { const double mid = 0.5 * (lo + hi); if (P(mid) <= target) lo = mid; else hi = mid; }
  return lo;
}
static std::string r2Num(double x, const char* fmt = "%.3f") { if (!std::isfinite(x)) return "null"; char b[48]; std::snprintf(b, sizeof b, fmt, x); return b; }

static void scR2v2() {
  if (const char* e = std::getenv("SIL_R2V2_DBG")) {   // debug: "plateau_s,F,dead,onset_ms,report[,glitch_ms,ride]" -> trace on stdout, no results
    double pl = 0, F = 200, on = 5, gl = -1; int dd = 1, rp = 1, rd = -1;   // onset_ms < 0: no Pc loss; glitch_ms from E2 (< 0: none)
    if (std::sscanf(e, "%lf,%lf,%d,%lf,%d,%lf,%d", &pl, &F, &dd, &on, &rp, &gl, &rd) >= 5) {
      const R2Tr ref = r2Plant("dbg_ref", F, pl, rp != 0, false, NAN, NAN, 171, -1.0, rd);
      std::printf("dbg reference: light %.4f E2 %.4f\nt_from_E2_ms,state,pc_valid,r2_hold,lit,x_mm,x_cmd_mm,F_N,Pc_bar,Pcf_bar,abort\n", ref.t_light, ref.e2);
      g_r2dbg = stdout;
      r2Plant("dbg", F, pl, rp != 0, dd != 0, on >= 0 ? on * 1e-3 : NAN, ref.e2, 171, gl >= 0 ? ref.e2 + gl * 1e-3 : -1.0, rd);
      g_r2dbg = nullptr;
    }
    return;
  }
  J j;
  j.k("id").v("sil_S17_r2v2_v2p11"); j.k("version").v("v2.11"); j.k("date").v("2026-10-20");
  j.k("method").v("see the header of firmware/sil/sc_v211_r2.inc (one closed-loop run per case, GNC R2 v2 evaluated offline on the recorded 1 ms "
                  "history: causal, decisions only at or after the counting start). SIM on ASSUMED / COMB SIM inputs; not physical approval");
  j.k("gnc_inputs").v("rev3 results/eval/r2v2_eval.json 4d5ddc5da93a16df (flame-out side; lit side WITHDRAWN W2); rev4 REPORT-GNC-rev4-HANDBACK.md "
                      "section 6 (counting start, no flush in sim6, reference at the light, 20.85 N contains ~0.06 N rms modelled IMU noise only)");
  j.k("threshold_N").v(kR2T_N); j.k("tau_s").v(kR2Tau);
  j.k("d_dead_W10lt6_N").raw("[18.996, 19.831]"); j.k("d_dead_allwinds_N").raw("[22.333, 29.158]"); j.k("gnc_fo_cb_design_max_W10lt6_N").raw("[31.183, 31.861]");
  j.k("ref_options").raw("[\"none_GNC_sim6\", \"LP_at_ECU_E2\", \"LP_at_plant_light\"]");
  const auto clk0 = std::chrono::steady_clock::now();
  const bool quick = std::getenv("SIL_R2V2_QUICK") != nullptr;   // smoke test: onsets 1 / 5 / 25 / 50 ms, plateaus 0.10 / 0.40 / 0.70 s (not for results)
  std::vector<int> onsets; for (int on = 1; on <= 50; ++on) if (!quick || on == 1 || on == 5 || on == 25 || on == 50) onsets.push_back(on);
  j.k("quick_smoke_test").raw(quick ? "true" : "false");
  // ---------------------------------------------------------------- plant runs
  std::vector<R2Tr> T;
  std::map<std::string, double> e2ref;
  struct Fam { std::string name; double plateau; bool opt; };   // opt false: photodiode without the main-chamber view (dead runs, hold only)
  const std::vector<Fam> fams = {{"normal", 0.0, true}, {"starved040", 0.40, true}, {"normal_noopt", 0.0, false}, {"starved040_noopt", 0.40, false}};
  int nrun = 0;
  std::string refs = "[";
  for (const Fam& fm : fams)
    for (double F : {200.0, 500.0}) {
      const R2Tr ref = r2Plant(fm.name, F, fm.plateau, true, false, NAN, NAN, 171, -1.0, -1, fm.opt);
      char key[64]; std::snprintf(key, sizeof key, "%s_%.0f", fm.name.c_str(), F); e2ref[key] = ref.e2;
      double rl = NAN, re = NAN; r2Refs(ref, &rl, &re);
      std::printf("S17v2 reference %-10s %.0f N: light %.4f s, E2 %.4f s (E2 - light %.1f ms), LP20 thrust at the light %.2f N, at E2 %.2f N\n", fm.name.c_str(),
                  F, ref.t_light, ref.e2, (ref.e2 - ref.t_light) * 1e3, rl, re);
      char q[300]; std::snprintf(q, sizeof q, "%s{\"family\": \"%s\", \"F_rl_N\": %.0f, \"t_light_s\": %.4f, \"t_E2_s\": %.4f, \"LP20_at_light_N\": %.3f, \"LP20_at_E2_N\": %.3f}",
                                 refs.size() > 1 ? ", " : "", fm.name.c_str(), F, ref.t_light, ref.e2, rl, re);
      refs += q;
      for (bool rep : {true, false})
        for (bool dead : {false, true})
          for (int on : onsets) {
            if (!fm.opt && (!rep || !dead)) continue;   // *_noopt: dead runs with the hold only (the view changes nothing on a lit run)
            T.push_back(r2Plant(fm.name, F, fm.plateau, rep, dead, on * 1e-3, ref.e2, 171, -1.0, -1, fm.opt));
            ++nrun;
          }
      std::fflush(stdout);
    }
  j.k("references").raw(refs + "]");
  // starve-threshold family (lit, hold, Pc lost at E2 + 5 ms), plateau 0.10-0.80 s
  std::vector<R2Tr> TS;
  for (double F : {200.0, 500.0})
    for (int ip = 0; ip <= 14; ++ip) {
      if (quick && ip % 6 != 0) continue;
      const double pl = 0.10 + 0.05 * ip;
      const R2Tr ref = r2Plant("starve_thr", F, pl, true, false, NAN, NAN, 171);
      TS.push_back(r2Plant("starve_thr", F, pl, true, false, 0.005, ref.e2, 171));
      ++nrun;
    }
  std::printf("S17v2 plant runs: %d (+ references), %.1f s wall\n", nrun, std::chrono::duration<double>(std::chrono::steady_clock::now() - clk0).count());
  std::fflush(stdout);
  // ---------------------------------------------------------------- per-run plant facts (E2 identity)
  int e2_mismatch = 0;
  for (const R2Tr& t : T) {
    char key[64]; std::snprintf(key, sizeof key, "%s_%.0f", t.fam.c_str(), t.F_rl);
    if (std::fabs(t.e2 - e2ref[key]) > 1e-9) ++e2_mismatch;
  }
  j.k("e2_differs_from_reference_runs").v(e2_mismatch);
  // ---------------------------------------------------------------- deterministic sweep (+ sigma 5 N iid probability for the dead side)
  // groups: family x F x report x lit/dead; configs: window x flush x ref (3) x d (dead: W6 design / all winds; lit: 0 / -12) x extra
  // (lit: no cap / F_min cap 33.14 N in the hold; dead: cold flow x 1.0 / x 1.3)
  std::string groups = "[";
  int ng = 0;
  // CSV (gzip) of every deterministic evaluation that reaches mode 3 (starved families; normal families with the FC Pc branch off), design d,
  // no extra
  std::string cmd = "gzip -9 > '" + OUT + "/S17v2_r2v2_evals_mode3.csv.gz'";
  FILE* csv = quick ? nullptr : popen(cmd.c_str(), "w");
  if (csv) std::fprintf(csv, "family,F_rl,report,kind,fc_pc_branch,onset_ms,window_s,flush,ref,d_N,phase,outcome,branch,t_decision_ms,t_count_start_ms,ref_N,stat_N,margin_N\n");
  struct Agg {
    int n = 0, cnt[7] = {0, 0, 0, 0, 0, 0, 0}; double stat_max = -1e9, t_rel_min = 1e9, t_rel_max = -1e9, p5_max = 0.0, p5_sum = 0.0;
    std::string worst; std::vector<double> t_rel;
  };
  for (const Fam& fm : fams)
    for (double F : {200.0, 500.0})
      for (bool rep : {true, false})
        for (bool dead : {false, true}) {
          std::vector<const R2Tr*> sel;
          for (const R2Tr& t : T) if (t.fam == fm.name && t.F_rl == F && t.report == rep && t.dead == dead) sel.push_back(&t);
          if (sel.empty()) continue;
          const bool normal_fam = fm.plateau <= 0.0;
          std::vector<int> pbs; if (normal_fam && fm.opt) pbs = {1, 0}; else if (normal_fam) pbs = {0}; else pbs = {1};
          for (int pb : pbs)
          for (int w = 0; w < 2; ++w)
            for (bool fl : {false, true})
              for (int rf : {0, 1, 2})
                for (int dv = 0; dv < 2; ++dv)
                  for (int ex = 0; ex < 2; ++ex) {
                    const double dd = dead ? (dv == 0 ? kDW6[w] : kDAll[w]) : (dv == 0 ? 0.0 : -12.0);
                    Agg A;
                    for (const R2Tr* tp : sel)
                      for (int ph = 0; ph < 10; ++ph) {
                        R2Cfg c; c.w = w; c.phase = ph; c.flush = fl; c.ref = rf; c.d = dd; c.pcb = pb != 0;
                        if (ex && !dead) c.lit_cap = kFminLit_N;
                        if (ex && dead) c.cold_scale = kColdScaleHi;
                        const R2Det d = r2Eval(*tp, c);
                        ++A.n; ++A.cnt[d.out];
                        if (d.out == O_LIT_REL || d.out == O_DEAD_REL) { A.t_rel.push_back(d.t_dec); A.t_rel_min = std::min(A.t_rel_min, d.t_dec); A.t_rel_max = std::max(A.t_rel_max, d.t_dec); }
                        if (d.stat > A.stat_max) {
                          A.stat_max = d.stat;
                          char wb[160]; std::snprintf(wb, sizeof wb, "onset %.0f ms phase %d (frame %d, t_c %.0f ms)", tp->onset * 1e3, ph, d.k_stat, d.t_c * 1e3); A.worst = wb;
                        }
                        if (dead) { const R2P p = r2Prob(d, 5.0); A.p5_max = std::max(A.p5_max, p.p_dead); A.p5_sum += p.p_dead; }
                        if (csv && (!normal_fam || pb == 0) && dv == 0 && ex == 0)
                          std::fprintf(csv, "%s,%.0f,%d,%s,%d,%.0f,%.1f,%d,%d,%.3f,%d,%s,%d,%.1f,%.1f,%.3f,%.3f,%.3f\n", fm.name.c_str(), F, rep ? 1 : 0,
                                       dead ? "dead" : "lit", pb, tp->onset * 1e3, kWin[w], fl ? 1 : 0, rf, dd, ph, r2oName(d.out), d.branch,
                                       d.t_dec * 1e3, d.t_c * 1e3, d.ref_N, d.stat > -1e8 ? d.stat : NAN, d.stat > -1e8 ? kR2T_N - d.stat : NAN);
                      }
                    std::sort(A.t_rel.begin(), A.t_rel.end());
                    const bool anyrel = !A.t_rel.empty();
                    const double med = anyrel ? A.t_rel[A.t_rel.size() / 2] : NAN;
                    const std::string p5m = dead ? r2Num(A.p5_max, "%.4e") : "null", p5a = (dead && A.n) ? r2Num(A.p5_sum / A.n, "%.4e") : "null";
                    const std::string smax = A.stat_max > -1e8 ? r2Num(A.stat_max) : "null", smar = A.stat_max > -1e8 ? r2Num(kR2T_N - A.stat_max) : "null";
                    const char* exn = ex ? (dead ? "cold_flow_x1.3" : "lit_cap_33.14N") : "none";
                    char b[1400];
                    std::snprintf(b, sizeof b, "%s{\"family\": \"%s\", \"photo_main_view\": %s, \"fc_pc_branch\": %s, \"F_rl_N\": %.0f, \"drogue_report_hold\": %s, \"kind\": \"%s\", \"window_s\": %.1f, \"flush\": %s, "
                                  "\"ref\": \"%s\", \"d_N\": %.3f, \"d_basis\": \"%s\", \"sensitivity\": \"%s\", \"evaluations\": %d, \"LIT_RELEASED\": %d, \"DEAD_RELEASED\": %d, "
                                  "\"LIT_ABORT\": %d, \"DEAD_ABORT\": %d, \"ECU_LEFT_RUN\": %d, \"NO_R2_WINDOW\": %d, \"stat_max_N\": %s, \"margin_min_N\": %s, "
                                  "\"worst\": \"%s\", \"release_from_E2_ms_min_med_max\": [%s, %s, %s], \"p_dead_release_sigma5_max\": %s, \"p_dead_release_sigma5_mean\": %s}",
                                  ng++ ? ",\n" : "", fm.name.c_str(), jb(fm.opt).c_str(), jb(pb != 0).c_str(), F, jb(rep).c_str(), dead ? "dead" : "lit", kWin[w], jb(fl).c_str(), kRefName[rf], dd,
                                  dead ? (dv == 0 ? "W10<6 fo_none" : "all-winds fo_none") : (dv == 0 ? "lit 0" : "lit -12 (W2 withdrawn arm, sensitivity)"),
                                  exn, A.n, A.cnt[1], A.cnt[2], A.cnt[3], A.cnt[4], A.cnt[5], A.cnt[6], smax.c_str(), smar.c_str(), A.worst.c_str(),
                                  r2Num(anyrel ? A.t_rel_min * 1e3 : NAN, "%.1f").c_str(), r2Num(med * 1e3, "%.1f").c_str(), r2Num(anyrel ? A.t_rel_max * 1e3 : NAN, "%.1f").c_str(),
                                  p5m.c_str(), p5a.c_str());
                    groups += b;
                    if (dv == 0 && ex == 0)
                      std::printf("S17v2 %-16s pcb %d %3.0f N hold %d %-4s W %.1f flush %d ref %d: LIT_REL %4d DEAD_REL %4d LIT_AB %4d DEAD_AB %4d ECU_LEFT %4d NO_R2 %4d stat max %s (margin %s) %s rel %s..%s ms p5max %s\n",
                                  fm.name.c_str(), pb, F, rep ? 1 : 0, dead ? "dead" : "lit", kWin[w], fl ? 1 : 0, rf, A.cnt[1], A.cnt[2], A.cnt[3], A.cnt[4], A.cnt[5], A.cnt[6],
                                  smax.c_str(), smar.c_str(), A.worst.c_str(), r2Num(anyrel ? A.t_rel_min * 1e3 : NAN, "%.0f").c_str(),
                                  r2Num(anyrel ? A.t_rel_max * 1e3 : NAN, "%.0f").c_str(), p5m.c_str());
                  }
        }
  if (csv) pclose(csv);
  j.k("groups").raw(groups + "\n]");
  std::fflush(stdout);
  // ---------------------------------------------------------------- noise budget (dead side)
  struct NbCase { int w; bool fl, rep; int rf; double cs; const char* tag; };
  std::vector<NbCase> nbc;
  for (int w = 0; w < 2; ++w) {
    nbc.push_back({w, false, true, 0, 1.0, "design_noflush"}); nbc.push_back({w, true, true, 0, 1.0, "design_flush"});
    nbc.push_back({w, false, false, 0, 1.0, "nohold_noflush"}); nbc.push_back({w, true, false, 0, 1.0, "nohold_flush"});
    nbc.push_back({w, true, true, 2, 1.0, "flush_ref_at_light"}); nbc.push_back({w, true, true, 0, kColdScaleHi, "flush_cold_x1.3"});
  }
  const double rho = std::exp(-0.010 / kR2Tau);
  std::string nb = "[";
  int nn = 0;
  for (const NbCase& k : nbc) {
    std::vector<R2Det> D; std::vector<std::string> Dn, Df;
    for (const R2Tr& t : T) {
      if (!t.dead || t.report != k.rep) continue;
      for (int ph = 0; ph < 10; ++ph) {
        // mode 3 on every family: the FC Pc branch off (it never fires on the starved families; on the normal families it is the
        // fc_pc_branch false variant, the only way a normal start reaches mode 3)
        R2Cfg c; c.w = k.w; c.phase = ph; c.flush = k.fl; c.ref = k.rf; c.d = kDW6[k.w]; c.cold_scale = k.cs; c.pcb = false;
        const R2Det d = r2Eval(t, c);
        if (!d.mu.empty()) {
          D.push_back(d); Df.push_back(t.fam);
          char q[120]; std::snprintf(q, sizeof q, "%s %.0f N onset %.0f ms phase %d", t.fam.c_str(), t.F_rl, t.onset * 1e3, ph); Dn.push_back(q);
        }
      }
    }
    auto pmaxOf = [&](double sg, const std::string& fam) {
      double m = 0; for (size_t i = 0; i < D.size(); ++i) if (fam.empty() || Df[i] == fam) m = std::max(m, r2Prob(D[i], sg).p_dead); return m; };
    auto pmax = [&](double sg) { return pmaxOf(sg, ""); };
    double stat = -1e9; size_t ib = 0; double pb = -1;
    for (size_t i = 0; i < D.size(); ++i) { stat = std::max(stat, D[i].stat); const double p = r2Prob(D[i], 5.0).p_dead; if (p > pb) { pb = p; ib = i; } }
    const double s3 = D.empty() ? NAN : r2SigmaFor(pmax, 1e-3), s2 = D.empty() ? NAN : r2SigmaFor(pmax, 1e-2), p5 = D.empty() ? NAN : pb;
    std::string perfam = "{";
    for (const Fam& fm : fams) {
      bool any = false; for (const std::string& f : Df) if (f == fm.name) { any = true; break; }
      if (!any) continue;
      const double sf = r2SigmaFor([&](double sg) { return pmaxOf(sg, fm.name); }, 1e-3);
      const double sf2 = r2SigmaFor([&](double sg) { return pmaxOf(sg, fm.name); }, 1e-2);
      double st = -1e9, pbf = -1.0; size_t ibf = 0;
      for (size_t i = 0; i < D.size(); ++i) if (Df[i] == fm.name) {
        st = std::max(st, D[i].stat); const double p = r2Prob(D[i], 5.0).p_dead; if (p > pbf) { pbf = p; ibf = i; } }
      // v2.11 third pass: per-family bounding run with the AR(1) sensitivity (the families with the optical flame-out armed are the
      // design case; the *_noopt families are the FMEA case), so the frame-noise budget of LEAD 227 (6) is stated per family
      double far5 = NAN, far_s3 = NAN;
      if (k.rep && k.fl) {
        far5 = r2Mc(D[ibf], 5.0, rho, 200000, 4245);
        far_s3 = r2SigmaFor([&](double sg) { return r2Mc(D[ibf], sg, rho, 100000, 4246); }, 1e-3);
      }
      char q[700]; std::snprintf(q, sizeof q, "%s\"%s\": {\"stat_max_N\": %.3f, \"margin_min_N\": %.3f, \"iid_sigma_for_Pmax_1e-3_N\": %.3f, "
                                 "\"iid_sigma_for_Pmax_1e-2_N\": %.3f, \"iid_Pmax_at_5N_rms\": %.5f, \"bounding_run_at_5N\": \"%s\", "
                                 "\"mc_ar1_P_at_5N_bounding_run\": %s, \"mc_ar1_sigma_for_P_1e-3_bounding_run_N\": %s}", perfam.size() > 1 ? ", " : "",
                                 fm.name.c_str(), st, kR2T_N - st, sf, sf2, pbf, Dn[ibf].c_str(), r2Num(far5, "%.5f").c_str(), r2Num(far_s3).c_str());
      perfam += q;
    }
    perfam += "}";
    double mc5 = NAN, ar5 = NAN, ar_s3 = NAN;
    if (!D.empty() && k.rep && k.fl) {   // MC cross-check (iid) and the AR(1) sensitivity on the bounding run
      mc5 = r2Mc(D[ib], 5.0, 0.0, 200000, 4242);
      ar5 = r2Mc(D[ib], 5.0, rho, 200000, 4243);
      ar_s3 = r2SigmaFor([&](double sg) { return r2Mc(D[ib], sg, rho, 100000, 4244); }, 1e-3);
    }
    const double m = kR2T_N - stat;
    char b[4096];
    std::snprintf(b, sizeof b, "%s{\"case\": \"%s\", \"window_s\": %.1f, \"flush\": %s, \"drogue_report_hold\": %s, \"ref\": \"%s\", \"cold_scale\": %.2f, "
                  "\"bounding_run_at_5N\": \"%s\", \"per_family\": %s, "
                  "\"dead_evaluations_with_R2_frames\": %zu, \"stat_max_N\": %s, \"margin_min_N\": %s, \"iid_sigma_for_Pmax_1e-3_N\": %s, "
                  "\"iid_sigma_for_Pmax_1e-2_N\": %s, \"iid_Pmax_at_5N_rms\": %s, \"mc_iid_P_at_5N_bounding_run\": %s, "
                  "\"ar1_rho\": %.4f, \"mc_ar1_P_at_5N_bounding_run\": %s, \"mc_ar1_sigma_for_P_1e-3_bounding_run_N\": %s}",
                  nn++ ? ",\n" : "", k.tag, kWin[k.w], jb(k.fl).c_str(), jb(k.rep).c_str(), kRefName[k.rf], k.cs, D.empty() ? "" : Dn[ib].c_str(), perfam.c_str(),
                  D.size(), r2Num(D.empty() ? NAN : stat).c_str(),
                  r2Num(D.empty() ? NAN : m).c_str(), r2Num(s3).c_str(), r2Num(s2).c_str(), r2Num(p5, "%.5f").c_str(), r2Num(mc5, "%.5f").c_str(), rho,
                  r2Num(ar5, "%.5f").c_str(), r2Num(ar_s3).c_str());
    nb += b;
    std::printf("S17v2 noise %-18s W %.1f: stat max %.2f N (margin %.2f), iid sigma(P<=1e-3) %.2f N, sigma(P<=1e-2) %.2f N, P(5 N) %.4f (MC %.4f), AR1 P(5 N) %.4f, AR1 sigma(1e-3) %.2f N; bounding %s\n",
                k.tag, kWin[k.w], stat, m, s3, s2, p5, mc5, ar5, ar_s3, D.empty() ? "-" : Dn[ib].c_str());
    std::printf("S17v2 noise %-18s W %.1f per family: %s\n", k.tag, kWin[k.w], perfam.c_str());
    std::fflush(stdout);
  }
  j.k("noise_budget_dead_W10lt6").raw(nb + "\n]");
  // GNC-margin cross-check (RV6-07 basis): constant margin 5.977 / 5.298 N over the window frames (50 / 80), exact recursion and AR(1) MC
  {
    std::string g = "[";
    for (int w = 0; w < 2; ++w) {
      R2Det d; const double m = kR2T_N - kFoCbW6[w]; const int N = static_cast<int>(std::lround(kWin[w] * 100.0));
      for (int k = 0; k < N; ++k) { d.mu.push_back(kFoCbW6[w]); d.dead.push_back(1); }
      const double p5 = r2Prob(d, 5.0).p_dead;
      const double s3 = r2SigmaFor([&](double sg) { return r2Prob(d, sg).p_dead; }, 1e-3), s2 = r2SigmaFor([&](double sg) { return r2Prob(d, sg).p_dead; }, 1e-2);
      const double a5 = r2Mc(d, 5.0, rho, 200000, 4245);
      const double as3 = r2SigmaFor([&](double sg) { return r2Mc(d, sg, rho, 100000, 4246); }, 1e-3);
      char b[500];
      std::snprintf(b, sizeof b, "%s{\"window_s\": %.1f, \"gnc_fo_cb_design_max_N\": %.3f, \"margin_N\": %.3f, \"frames\": %d, \"iid_P_at_5N\": %.5f, "
                    "\"iid_sigma_for_P_1e-3_N\": %.3f, \"iid_sigma_for_P_1e-2_N\": %.3f, \"ar1_P_at_5N\": %.5f, \"ar1_sigma_for_P_1e-3_N\": %.3f}",
                    w ? ", " : "", kWin[w], kFoCbW6[w], m, N, p5, s3, s2, a5, as3);
      g += b;
      std::printf("S17v2 GNC margin %.3f N W %.1f (%d frames): iid P(5 N) %.4f, sigma(1e-3) %.2f N, sigma(1e-2) %.2f N; AR1 P(5 N) %.4f, sigma(1e-3) %.2f N\n",
                  m, kWin[w], N, p5, s3, s2, a5, as3);
    }
    j.k("gnc_margin_constant_check").raw(g + "]");
  }
  // ---------------------------------------------------------------- starve threshold (lit, hold, Pc lost at E2 + 5 ms)
  {
    std::string st = "[";
    int ns = 0;
    for (double F : {200.0, 500.0})
      for (int w = 0; w < 2; ++w)
        for (bool fl : {false, true})
          for (int rf : {0, 1, 2}) {
            double thr_all = -1.0, thr_any = -1.0;   // longest plateau released at every phase / at some phase
            std::string rows;
            for (const R2Tr& t : TS) {
              if (t.F_rl != F) continue;
              int nrel = 0; double tmax = -1;
              for (int ph = 0; ph < 10; ++ph) {
                R2Cfg c; c.w = w; c.phase = ph; c.flush = fl; c.ref = rf; c.d = 0.0;
                const R2Det d = r2Eval(t, c);
                if (d.out == O_LIT_REL) { ++nrel; tmax = std::max(tmax, d.t_dec); }
              }
              if (nrel == 10 && t.plateau > thr_all) thr_all = t.plateau;
              if (nrel > 0 && t.plateau > thr_any) thr_any = t.plateau;
              char q[120]; std::snprintf(q, sizeof q, "%s[%.2f, %d, %s]", rows.empty() ? "" : ", ", t.plateau, nrel, r2Num(nrel ? tmax * 1e3 : NAN, "%.1f").c_str()); rows += q;
            }
            char b[1600];
            std::snprintf(b, sizeof b, "%s{\"F_rl_N\": %.0f, \"window_s\": %.1f, \"flush\": %s, \"ref\": \"%s\", \"plateau_released_at_all_10_phases_max_s\": %s, "
                          "\"plateau_released_at_some_phase_max_s\": %s, \"rows_plateau_s_released_phases_latest_release_ms\": [%s]}",
                          ns++ ? ",\n" : "", F, kWin[w], jb(fl).c_str(), kRefName[rf], r2Num(thr_all > 0 ? thr_all : NAN, "%.2f").c_str(),
                          r2Num(thr_any > 0 ? thr_any : NAN, "%.2f").c_str(), rows.c_str());
            st += b;
            std::printf("S17v2 starve threshold %.0f N W %.1f flush %d ref %d: all phases released up to %.2f s, some phase up to %.2f s\n", F, kWin[w], fl ? 1 : 0, rf,
                        thr_all, thr_any);
          }
    j.k("starve_threshold").raw(st + "\n]");
    std::string sp = "[";
    for (size_t i = 0; i < TS.size(); ++i) {
      double rl = NAN, re = NAN; r2Refs(TS[i], &rl, &re);
      char q[400]; std::snprintf(q, sizeof q, "%s{\"F_rl_N\": %.0f, \"plateau_s\": %.2f, \"E2_from_light_ms\": %.1f, \"LP20_at_light_N\": %.3f, \"LP20_at_E2_N\": %.3f, "
                                 "\"hold_lift_steady_mm\": %.5f, \"F_lit_in_hold_steady_mean_N\": %.2f, \"ecu_left_RUN_from_E2_ms\": %.1f, \"ecu_abort\": \"%s\"}",
                                 i ? ", " : "", TS[i].F_rl, TS[i].plateau, (TS[i].e2 - TS[i].t_light) * 1e3, rl, re, TS[i].lift_hold, TS[i].F_hold_lit,
                                 (TS[i].t_leave - TS[i].e2) * 1e3, ecu::abortName(static_cast<ecu::Abort>(TS[i].ecu_abort)));
      sp += q;
    }
    j.k("starve_runs").raw(sp + "]");
  }
  // ---------------------------------------------------------------- plant facts per family (steady hold lift, lit / dead thrust in the hold, backstop)
  {
    std::string pf = "[";
    int np = 0;
    for (const Fam& fm : fams)
      for (double F : {200.0, 500.0})
        for (bool rep : {true, false})
          for (bool dead : {false, true}) {
            double lift = 0, fl = 0, fd = 0; int nl = 0, nfl = 0, nfd = 0, nbs = 0, nleave = 0; double bsmin = 1e9, bsmax = -1e9;
            std::map<int, int> ab;
            int nsel = 0;
            for (const R2Tr& t : T) {
              if (t.fam != fm.name || t.F_rl != F || t.report != rep || t.dead != dead) continue;
              ++nsel;
              if (std::isfinite(t.lift_hold)) { lift += t.lift_hold; ++nl; }
              if (std::isfinite(t.F_hold_lit)) { fl += t.F_hold_lit; ++nfl; }
              if (std::isfinite(t.F_hold_dead)) { fd += t.F_hold_dead; ++nfd; }
              if (std::isfinite(t.t_backstop)) { ++nbs; bsmin = std::min(bsmin, t.t_backstop - t.e2); bsmax = std::max(bsmax, t.t_backstop - t.e2); }
              if (std::isfinite(t.t_leave) && t.t_leave - t.e2 < kWin[1]) { ++nleave; ++ab[t.ecu_abort]; }
            }
            if (!nsel) continue;
            std::string abs;
            for (auto& kv : ab) { char q[80]; std::snprintf(q, sizeof q, "%s%s: %d", abs.empty() ? "" : ", ", ecu::abortName(static_cast<ecu::Abort>(kv.first)), kv.second); abs += q; }
            char b[800];
            std::snprintf(b, sizeof b, "%s{\"family\": \"%s\", \"F_rl_N\": %.0f, \"drogue_report_hold\": %s, \"kind\": \"%s\", \"hold_lift_steady_mean_mm\": %.5f, "
                          "\"F_lit_in_hold_steady_mean_N\": %.2f, \"F_cold_in_hold_steady_mean_N\": %.2f, \"backstop_runs\": %d, \"backstop_from_E2_ms\": [%.1f, %.1f], "
                          "\"ecu_left_RUN_before_E2_plus_0p8_runs\": %d, \"ecu_aborts\": \"%s\"}",
                          np++ ? ",\n" : "", fm.name.c_str(), F, jb(rep).c_str(), dead ? "dead" : "lit", nl ? lift / nl : NAN, nfl ? fl / nfl : NAN, nfd ? fd / nfd : NAN,
                          nbs, nbs ? bsmin * 1e3 : NAN, nbs ? bsmax * 1e3 : NAN, nleave, abs.c_str());
            pf += b;
          }
    j.k("plant_facts").raw(pf + "\n]");
  }
  // ---------------------------------------------------------------- R2-23: one HIGH over-range tick (C1 at its rail for 1 ms) with the drogue attached
  {
    std::string g = "[";
    int ngl = 0;
    for (const Fam& fm : fams)
      if (fm.opt)
      for (int ride : {0, 1})
        for (double F : {200.0, 300.0, 400.0, 500.0})
          for (double tg : {0.020, fm.plateau > 0.0 ? 0.040 : 0.350}) {   // starved family: before its A3 abort at E2 + 53 ms (Pc valid, SIL stand-in)
            if (fm.plateau > 0.0 && (F == 300.0 || F == 400.0)) continue;   // intermediate levels (comparator trip bracket): normal family only
            const R2Tr ref = r2Plant("glitch_ref", F, fm.plateau, true, false, NAN, NAN, 171, -1.0, ride);
            const R2Tr t = r2Plant("glitch", F, fm.plateau, true, false, NAN, NAN, 171, ref.e2 + tg, ride);
            double def = 0, dmax = 0; const int i0 = static_cast<int>(std::lround((ref.e2 + tg - t.t0) * 1000.0));
            for (int i = i0; i < std::min<int>(i0 + 280, static_cast<int>(std::min(t.F.size(), ref.F.size()))); ++i) { const double dd = ref.F[i] - t.F[i]; def += dd * 1e-3; dmax = std::max(dmax, dd); }
            const bool left = std::isfinite(t.t_leave);
            char b[800];
            std::snprintf(b, sizeof b, "%s{\"family\": \"%s\", \"ride_through\": %d, \"comparator_tau_ms\": %.3f, \"F_rl_N\": %.0f, \"glitch_from_E2_ms\": %.1f, \"glitch_len_ms\": 1.0, "
                          "\"Pc_before_bar_abs\": %.3f, \"Pc_filtered_max_30ms_bar_abs\": %.3f, \"r2_hold_ticks_in_30ms\": %d, \"comparator_trip_from_glitch_ms\": %s, "
                          "\"ecu_left_RUN_from_glitch_ms\": %s, \"ecu_abort\": \"%s\", \"thrust_deficit_Ns_over_280ms\": %.3f, \"thrust_deficit_max_N\": %.2f}",
                          ngl++ ? ",\n" : "", fm.name.c_str(), ride, (ride ? ecu::cfg::kRideCmpTauNom_s : ovp3::kTau_s) * 1e3, F, tg * 1e3, t.pc_pre_bar, t.pcf_max_bar,
                          t.glitch_hold_ticks, r2Num(std::isfinite(t.t_cmp) ? (t.t_cmp - ref.e2 - tg) * 1e3 : NAN, "%.2f").c_str(),
                          r2Num(left ? (t.t_leave - ref.e2 - tg) * 1e3 : NAN, "%.1f").c_str(), left ? ecu::abortName(static_cast<ecu::Abort>(t.ecu_abort)) : "NONE",
                          def, dmax);
            g += b;
            std::printf("S17v2 R2-23 glitch %-10s ride %d %.0f N at E2+%.0f ms: Pc %.2f bar, Pcf max %.2f bar, hold ticks %d, comparator %s, ECU %s at +%.1f ms, deficit %.3f N s\n",
                        fm.name.c_str(), ride, F, tg * 1e3, t.pc_pre_bar, t.pcf_max_bar, t.glitch_hold_ticks, std::isfinite(t.t_cmp) ? "TRIP" : "no trip",
                        left ? ecu::abortName(static_cast<ecu::Abort>(t.ecu_abort)) : "stays in RUN", left ? (t.t_leave - ref.e2 - tg) * 1e3 : NAN, def);
          }
    j.k("r2_23_overrange_glitch").raw(g + "\n]");
  }
  j.k("wall_s").v(std::chrono::duration<double>(std::chrono::steady_clock::now() - clk0).count());
  writeFile(OUT + (quick ? "/S17v2_r2v2_sweep_QUICK.json" : "/S17v2_r2v2_sweep.json"), j.str());
}

}  // namespace v211
