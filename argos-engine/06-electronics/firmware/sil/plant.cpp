// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175: photodiode head, bleed valve times, pool source; full list in 06-electronics/REPORT-v2.10-HANDBACK.md] ARGOS engine SIL - plant models (v2.5, 2026-10-12). NOT flight code. See plant.h for scope and tags.
#include "plant.h"
#include <complex>
#include <algorithm>
#include "plant_tables.h"

namespace sil {

static constexpr double kPa = 101325.0;
static inline double clampd(double x, double lo, double hi) { return x < lo ? lo : (x > hi ? hi : x); }

// ------------------------------------------------------------------------------------- tables
static void satRow(double T, double out[7]) {
  const double f = clampd((T - tab::kSatT0) / tab::kSatDT, 0.0, tab::kNsat - 1.000001);
  const int i = static_cast<int>(f);
  const double w = f - i;
  for (int k = 0; k < 7; ++k) out[k] = tab::kSat[i][k] + w * (tab::kSat[i + 1][k] - tab::kSat[i][k]);
}
double satP(double T) { double r[7]; satRow(T, r); return r[0]; }

double ghemSat(double T, double P2) {
  if (P2 >= satP(T)) return 0.0;
  const double fi = clampd((T - tab::kGT0) / tab::kGDT, 0.0, tab::kNGT - 1.000001);
  const double fj = clampd((P2 - tab::kGP0) / tab::kGDP, 0.0, tab::kNGP - 1.000001);
  const int i = static_cast<int>(fi), j = static_cast<int>(fj);
  const double a = fi - i, b = fj - j;
  const double g = (1 - a) * ((1 - b) * tab::kGhem[i][j] + b * tab::kGhem[i][j + 1]) +
                   a * ((1 - b) * tab::kGhem[i + 1][j] + b * tab::kGhem[i + 1][j + 1]);
  return std::max(0.0, g);
}
// v2.5 Combustion v2 convention (gen_tables.py g_dyer_v2, cross-checked against throttle_map_v2.csv within 0.45 %):
// G = k/(1+k) sqrt(2 rho_l (P1-P2)) + 1/(1+k) G_HEM(T1, P2), k = sqrt((P1-P2)/(Pv(T1)-P2)), liquid properties at T1
double dyerG2(double T1, double P1, double P2) {
  if (P1 <= P2) return 0.0;
  double r[7]; satRow(T1, r);
  const double pv = r[0], rl = r[1];
  const double spi = std::sqrt(2.0 * rl * (P1 - P2));
  if (P2 >= pv) return spi;
  const double k = std::sqrt((P1 - P2) / (pv - P2));
  return k / (1.0 + k) * spi + 1.0 / (1.0 + k) * ghemSat(T1, P2);
}
double dyerG(double T, double Pc) { return dyerG2(T, satP(T), Pc); }

static double ceaInterp(const double (*t)[tab::kNOF], double Pc, double of) {
  const double lp = std::log(clampd(Pc, tab::kCeaPc[0], tab::kCeaPc[tab::kNCP - 1]));
  int i = 0;
  while (i < tab::kNCP - 2 && lp > std::log(tab::kCeaPc[i + 1])) ++i;
  const double a = clampd((lp - std::log(tab::kCeaPc[i])) / (std::log(tab::kCeaPc[i + 1]) - std::log(tab::kCeaPc[i])), 0.0, 1.0);
  const double o = clampd(of, tab::kCeaOF[0], tab::kCeaOF[tab::kNOF - 1]);
  int j = 0;
  while (j < tab::kNOF - 2 && o > tab::kCeaOF[j + 1]) ++j;
  const double b = clampd((o - tab::kCeaOF[j]) / (tab::kCeaOF[j + 1] - tab::kCeaOF[j]), 0.0, 1.0);
  return (1 - a) * ((1 - b) * t[i][j] + b * t[i][j + 1]) + a * ((1 - b) * t[i + 1][j] + b * t[i + 1][j + 1]);
}
double ceaCstar(double Pc, double of) { return ceaInterp(tab::kCstar, Pc, of); }
double ceaGamma(double Pc, double of) { return ceaInterp(tab::kGamma, Pc, of); }
double ceaCfVac(double Pc, double of) { return ceaInterp(tab::kCfVac, Pc, of); }
double GammaFn(double g) { return std::sqrt(g) * std::pow(2.0 / (g + 1.0), (g + 1.0) / (2.0 * (g - 1.0))); }

double ballValveArea(double u) {
  // [ASSUMED] full-port ball valve: open area = overlap of the bore and the port circles, centre offset (1 - u) bores
  u = std::min(1.0, std::max(0.0, u));
  const double s = 1.0 - u, r = 0.5;
  if (s >= 1.0) return 0.0;
  const double A = 2.0 * r * r * std::acos(s / (2.0 * r)) - 0.5 * s * std::sqrt(4.0 * r * r - s * s);
  return A / (M_PI * r * r);
}

double gasOrifice(double A, double p1, double T1, double p2, double g, double R) {
  if (p1 <= p2 || A <= 0) return 0.0;
  const double pr = p2 / p1, pcrit = std::pow(2.0 / (g + 1.0), g / (g - 1.0));
  if (pr <= pcrit) return A * p1 * std::sqrt(g / (R * T1)) * std::pow(2.0 / (g + 1.0), (g + 1.0) / (2.0 * (g - 1.0)));
  return A * p1 * std::sqrt(2.0 * g / ((g - 1.0) * R * T1) * (std::pow(pr, 2.0 / g) - std::pow(pr, (g + 1.0) / g)));
}

double pintleArea(double x) {
  // combustion.json v1 / m1_design.py: frustum between sharp seat (Ds) and cone (half-angle a), capped by seat area
  const double Ds = tab::k_Ds_seat, a = tab::k_cone_half;
  const double A_seat = M_PI * Ds * Ds / 4.0;
  const double s = std::max(0.0, x) * std::sin(a);
  const double disc = Ds * Ds - 4.0 * std::cos(a) * A_seat / M_PI;
  const double s_star = (Ds - std::sqrt(std::max(disc, 0.0))) / (2.0 * std::cos(a));
  return s < s_star ? M_PI * s * (Ds - s * std::cos(a)) : A_seat;
}

// ------------------------------------------------------------------------------------- engine
EnginePlant::EnginePlant(const EngineParams& p) : P(p) {
  T_tank = P.T_tank0;
  double r[7]; satRow(T_tank, r);
  m_tank = tab::k_tank_m;
  const double v = tab::k_tank_V / m_tank, vl = 1.0 / r[1], vv = 1.0 / r[2];
  const double xq = (v - vl) / (vv - vl);
  U_tank = m_tank * (r[3] + xq * (r[4] - r[3]));
  P_tank = r[0];
  Dport = tab::k_D_port0;
  Vc = tab::k_V_free0;
  delay_buf_.assign(1, 0.0);
}

void EnginePlant::setTankState(double T, double m) {
  double r[7]; satRow(T, r);
  m_tank = m;
  const double v = tab::k_tank_V / m_tank, vl = 1.0 / r[1], vv = 1.0 / r[2];
  const double xq = (v - vl) / (vv - vl);
  U_tank = m_tank * (r[3] + xq * (r[4] - r[3]));
  tankUpdate(0.0);
}

void EnginePlant::tankUpdate(double dt) {
  (void)dt;
  const double v = tab::k_tank_V / m_tank, u = U_tank / m_tank;
  double lo = 240.0, hi = 307.5;
  for (int it = 0; it < 40; ++it) {
    const double T = 0.5 * (lo + hi);
    double r[7]; satRow(T, r);
    const double xq = (v - 1.0 / r[1]) / (1.0 / r[2] - 1.0 / r[1]);
    const double um = r[3] + xq * (r[4] - r[3]);
    if (um > u) hi = T; else lo = T;
  }
  T_tank = 0.5 * (lo + hi);
  double r[7]; satRow(T_tank, r);
  P_tank = r[0];
  const double xq = (v - 1.0 / r[1]) / (1.0 / r[2] - 1.0 / r[1]);
  liquid_depleted = xq >= 1.0;
}

double EnginePlant::thrustOf(double Pc_abs, double of_) const {
  return std::max(0.0, (tab::k_eta_cfv * ceaCfVac(Pc_abs, of_) * Pc_abs - tab::k_eps * kPa) * tab::k_At);
}

void EnginePlant::steadyState(double T, double x, double* Pc_o, double* mox_o, double* mf_o, double* F_o) const {
  // f(Pc) = (mox(Pc) + mf(Pc)) c*(Pc, O/F) / At - Pc is monotonically decreasing (flux falls as Pc rises): bisection.
  // v2.5: injector inlet P1 = P_tank - dp_line(mdot) (equilibrium tank, P_tank = Pv(T)), fixed point on mdot
  const double Ap = M_PI * Dport * Dport / 4.0;
  const double Ptk = satP(T), CdA = tab::k_Cd * P.Cd_scale * pintleArea(x);
  auto eval = [&](double pc, double* mo, double* mfu, double* o) {
    double m = CdA * dyerG2(T, Ptk, pc);
    for (int it = 0; it < 30; ++it) {
      const double P1 = Ptk - P.dp_line_ref * (m / P.mdot_ref) * (m / P.mdot_ref);
      const double mn = CdA * dyerG2(T, P1, pc);
      if (std::fabs(mn - m) < 1e-9) { m = mn; break; }
      m = 0.5 * (m + mn);
    }
    *mo = m;
    const double G = *mo / Ap;
    *mfu = tab::k_rho_f * M_PI * Dport * tab::k_L_grain * tab::k_helix * tab::k_a_reg * P.reg_scale * std::pow(std::max(G, 0.0), tab::k_n_reg);
    *o = clampd(*mo / std::max(*mfu, 1e-9), 1.0, 14.0);
    const double cs = tab::k_eta_cstar * P.eta_scale * ceaCstar(pc, *o);
    return (*mo + *mfu) * cs / tab::k_At - pc;
  };
  double lo = kPa, hi = satP(T), mo = 0, mfu = 0, o = 6;
  if (eval(lo, &mo, &mfu, &o) <= 0) { hi = lo; }
  for (int it = 0; it < 60 && hi - lo > 0.5; ++it) {
    const double m = 0.5 * (lo + hi);
    if (eval(m, &mo, &mfu, &o) > 0) lo = m; else hi = m;
  }
  const double pc = 0.5 * (lo + hi);
  eval(pc, &mo, &mfu, &o);
  if (Pc_o) *Pc_o = pc;
  if (mox_o) *mox_o = mo;
  if (mf_o) *mf_o = mfu;
  if (F_o) *F_o = thrustOf(pc, o);
}

void EnginePlant::step(double dt, double x, bool mv_latch, double opener_theta, bool sol_n2o, bool sol_prop, bool spark) {
  // ---- scenario: line vented to ambient (drained; the next PREPRESS starts from an unprimed line)
  if (P.line_vent_at >= 0 && !vent_done_ && t >= P.line_vent_at - 1e-9) { vent_done_ = true; fill = 0.0; p_feed = kPa; gas_active = false; }
  // ---- v2.7 C7 scenario: the valve-to-seat volume fills with vapour (hot coast)
  if (P.vapour_fill_at >= 0 && !vap_done_ && t >= P.vapour_fill_at - 1e-9) { vap_done_ = true; vap_left = P.V_vap > 0.0 ? P.V_vap : tab::k_V_valve_to_seat; }
  // ---- main valve (v2.2): the opener's one-way dog pushes it open in proportion to the opener angle; the holding
  //      magnet keeps it open once fully open; the torsion spring closes it otherwise.
  //      v2.8 MV-P poppet (mv_type 1): the cam lifts the poppet in proportion to the opener angle; the magnet holds the over-centre
  //      latch until t_latch_release after its drive goes off (flux decay); the spring + pressure bias close it at the dashpot rate
  const bool poppet = P.mv_type == 1;
  if (mv_latch) latch_off_t_ = 0.0; else latch_off_t_ += dt;
  const bool holding = mv_latch || (poppet && latch_off_t_ < P.t_latch_release);
  const double t_close = poppet ? P.t_mv_close_poppet : P.t_mv_close;
  const double u_push = clampd(opener_theta / P.theta_full_open, 0.0, 1.0);
  if (u_push > mv_frac) mv_frac = std::min(u_push, mv_frac + dt / P.t_mv_open);
  else if (!(holding && mv_frac > 0.98)) mv_frac = std::max(u_push, mv_frac - dt / t_close);
  const double mv_area = poppet ? mv_frac : ballValveArea(mv_frac);     // v2.8: poppet curtain area ~ lift (constant-rise cam)
  const double CdA_mv = poppet ? P.Cv_poppet * 1.699e-5 : P.CdA_mv;     // [DERIVED] Cd*A = Cv x 1.699e-5 m2
  mv_open_sw = mv_frac > 0.97;
  mv_closed_sw = mv_frac < 0.03;

  // ---- liquid density at tank state
  double r[7]; satRow(T_tank, r);
  const double rho_l = r[1];

  // ---- feed line priming (v2.2): liquid enters through the opening MV (Cd*A from Cv, ball-valve area law) and
  //      compresses the gas pocket at the dead end (pintle); gas leaves through the pintle lift into the chamber.
  //      Adiabatic ideal gas, no wall heat transfer, no liquid inertia or flashing: an indicative check of the
  //      COMB v2 priming rule (Combustion owns the hazard analysis).
  const double A = pintleArea(x);
  double prime_out = 0.0;   // liquid volume flow into the line [m3/s] (also leaves the tank)
  if (mv_frac > 0.0 && fill < 1.0) {
    const double cv = P.R_gas / (P.gamma_gas - 1.0), cp = cv + P.R_gas;
    if (!gas_active) {
      gas_active = true; gas_T = P.T_gas0; gas_p = std::max(p_feed, kPa);
      gas_m = gas_p * P.V_line * (1.0 - fill) / (P.R_gas * gas_T);
    }
    const double Vg = P.V_line * (1.0 - fill);
    const double Q = CdA_mv * mv_area * std::sqrt(2.0 * std::max(0.0, P_tank - gas_p) / rho_l);
    const double dV = std::min(Q * dt, 0.01 * Vg);   // <= 1 % of the pocket per sub-step (explicit energy update)
    const double mo = std::min(0.5 * gas_m, gasOrifice(tab::k_Cd * P.Cd_scale * A, gas_p, gas_T, Pc, P.gamma_gas, P.R_gas) * dt);
    const double U = gas_m * cv * gas_T + gas_p * dV - mo * cp * gas_T;
    gas_m -= mo;
    fill += dV / P.V_line;
    prime_out = dV / dt; prime_Q = prime_out;
    if (gas_m <= 1e-12 || fill >= 0.9995) { fill = 1.0; gas_active = false; }
    else {
      gas_T = U / (gas_m * cv);
      gas_p = gas_m * P.R_gas * gas_T / (P.V_line * (1.0 - fill));
      gas_T_max = std::max(gas_T_max, gas_T); gas_p_max = std::max(gas_p_max, gas_p);
    }
  } else prime_Q = 0.0;
  // ---- v2.9 head-end bleed (see EngineParams): valve positions, flow from the segment (vapour first, reachable part), P_mid
  mdot_hb = 0.0; mvap_hb = 0.0;
  if (P.hb_fitted) {
    for (int k = 0; k < 2; ++k) {
      const bool tgt_open = hb_stuck[k] || (hb_cmd[k] && !hb_failc[k]);
      hb_pos[k] = tgt_open ? std::min(1.0, hb_pos[k] + dt / P.hb_t_open) : std::max(0.0, hb_pos[k] - dt / P.hb_t_close);
    }
    const double A_hb = P.hb_Cd * M_PI / 4.0 * P.hb_d * P.hb_d * std::min(hb_pos[0], hb_pos[1]);   // series pair: the less open one limits
    if (A_hb > 0.0 && !gas_active) {
      const double reach = vap_left - P.hb_unreached;
      if (reach > 0.0) {
        mvap_hb = A_hb * tab::k_vap_G;
        vap_left = std::max(P.hb_unreached, vap_left - mvap_hb / tab::k_vap_rho * dt);
        if (vap_left <= 1e-12) vap_left = 0.0;
      } else {
        const double ff = fill > 0.05 ? 1.0 : fill / 0.05;
        mdot_hb = A_hb * dyerG2(T_tank, p_feed, kPa) * ff;
        // MV shut: the trapped saturated liquid flashes to refill what the bleed draws, so the drawn volume becomes vapour at the crown
        // (where the taps are: the next sub-step vents it at the vapour flux). Crude flashing estimate; no air pocket is created.
        if (mv_frac <= 0.02) {
          double rr[7]; satRow(T_tank, rr);
          vap_left = std::min(P.V_line, vap_left + mdot_hb / rr[1] * dt);
        }
      }
    }
    const bool v1 = hb_pos[0] > 0.5, v2 = hb_pos[1] > 0.5;
    double tgt = P_mid, tau = P.hb_tau_fill;
    if (v1) tgt = v2 ? kPa + P.hb_mid_frac * (p_feed - kPa) : p_feed;
    else if (v2) { tgt = kPa; tau = P.hb_tau_vent; }
    P_mid += (tgt - P_mid) * std::min(1.0, dt / tau);
    m_hb_liq += mdot_hb * dt; m_hb_vap += mvap_hb * dt;
  }
  // ---- pintle flow (liquid only once the gas pocket is gone). v2.5: Dyer flux from the injector-inlet (feed) pressure
  //      P1 with liquid properties at the tank temperature (Combustion v2 convention); P1 follows P_tank - dp_line(mox)
  //      through the feed-pressure lag below (tau_feed), so the line loss now reduces the flow (v2.4: saturated inlet)
  const double G = dyerG2(T_tank, p_feed, Pc);
  double flow_factor;
  if (gas_active) flow_factor = 0.0;
  else if (mv_frac > 0.5) flow_factor = fill;
  else flow_factor = fill > 0.05 ? 1.0 : fill / 0.05;
  mox = tab::k_Cd * P.Cd_scale * A * G * flow_factor;
  // v2.7 C7: vapour first (choked vapour flux through the pintle lift, valve open behind it); liquid only once it is gone
  mvap = 0.0;
  if (vap_left > 0.0) {
    if (mv_frac > 0.5 && A > 0.0) {
      mvap = tab::k_Cd * P.Cd_scale * A * tab::k_vap_G;
      vap_left = std::max(0.0, vap_left - mvap / tab::k_vap_rho * dt);
    }
    mox = 0.0;
  }
  // v2.2: the line drains only once the valve is (almost) shut; a part-open ball valve still feeds it (v2.1: below 50 %)
  if (mv_frac <= 0.02 && mox > 0) fill = std::max(0.0, fill - mox * dt / (rho_l * P.V_line));   // (the bleed draw flashes instead, above)
  // v2.9: the line carries the injector AND the bleed flow (parallel draw from the tank; the bleed adds line loss only)
  const double m_line = mox + mdot_hb;
  const double dp_line = P.dp_line_ref * (m_line / P.mdot_ref) * (m_line / P.mdot_ref);
  double p_target;
  if (mv_frac > 0.5) p_target = Pc + fill * fill * (P_tank - dp_line - Pc);
  else p_target = fill > 0.05 ? std::max(Pc, satP(T_tank) - dp_line) : Pc + (fill / 0.05) * (satP(T_tank) - Pc);
  if (mv_frac <= 0.02 && x <= 0.0 && mdot_hb <= 0.0 && mvap_hb <= 0.0) p_target = p_feed;   // trapped liquid, valve, pintle and bleed shut: hold
  const double p_feed_old = p_feed;
  if (gas_active) p_feed = gas_p;                     // v2.2: the feed transducer (injector inlet) sees the gas pocket
  else p_feed += (p_target - p_feed) * std::min(1.0, dt / P.tau_feed);
  p_feed = std::max(p_feed, kPa);
  dpfeed_dt_max = std::max(dpfeed_dt_max, (p_feed - p_feed_old) / dt);

  // ---- tank (equilibrium blowdown); priming flow also leaves the tank
  if ((mv_frac > 0.02 || prime_out > 0.0) && !liquid_depleted) {
    // v2.7 C7: the liquid that pushes the vapour plug out of the valve-to-seat volume also leaves the tank
    const double out = (mv_frac > 0.02 ? mox + mdot_hb : 0.0) + rho_l * prime_out + (mvap > 0.0 ? rho_l * mvap / tab::k_vap_rho : 0.0) +
                       (mv_frac > 0.02 && mvap_hb > 0.0 ? rho_l * mvap_hb / tab::k_vap_rho : 0.0);   // v2.9 bleed (liquid; liquid replacing vented vapour)
    m_tank -= out * dt;
    U_tank -= out * r[5] * dt;
    ox_used += out * dt;
    tankUpdate(dt);
  }

  // ---- combustion delay (ox injected -> ox burning)
  const size_t n = std::max<size_t>(1, static_cast<size_t>(std::lround(P.comb_delay / dt)));
  if (delay_buf_.size() != n) { delay_buf_.assign(n, mox); delay_idx_ = 0; }
  mox_burn = delay_buf_[delay_idx_];
  delay_buf_[delay_idx_] = mox;
  delay_idx_ = (delay_idx_ + 1) % n;

  // ---- torch igniter
  if (sol_n2o && sol_prop) sol_timer_ += dt; else sol_timer_ = 0;
  if (!torch_lit && !P.torch_fail && sol_timer_ > P.torch_delay && spark && p_feed > Pc + 3.0e5) torch_lit = true;
  if (!(sol_n2o && sol_prop)) torch_lit = false;
  {   // v2.7 torch chamber pressure (ESTIMATE model, see EngineParams)
    const double tgt = torch_lit ? std::max(P.torch_p_lit, Pc + 0.1e5) : ((sol_n2o && sol_prop) ? Pc + P.torch_dp_cold : Pc);
    P_torch += (tgt - P_torch) * std::min(1.0, dt / P.torch_tau);
  }

  // ---- main ignition / extinction
  const bool forced_out = P.flameout_at >= 0 && t >= P.flameout_at;
  if (!ignited) {
    unburnt += (mox_burn - unburnt / 0.10) * dt;   // ASSUMED 0.1 s clearing of pooled unburnt N2O
    inflow_unlit += mox_burn * dt;                 // v2.10 RE-11 (pool_fret source)
    if (torch_lit && mox_burn > 1e-3 && !forced_out) ign_timer_ += dt; else ign_timer_ = 0;
    if (ign_timer_ >= P.ign_delay) {
      ignited = true; low_flow_timer_ = 0;
      burst_left = P.hard_start_gain * unburnt;
      pool_left = P.pool_fret >= 0.0 ? std::min(P.pool_cap_kg, P.pool_fret * std::max(0.0, inflow_unlit - burst_left))
                                      : P.pool_kg;   // v2.10 pool-burn source (scenario; 0 = none; RE-11 dispersed via pool_fret)
      t_lit_plant = t;         // v2.10 starve scenario reference
    }
  } else {
    if (mox_burn + mpool < P.mdot_extinguish) low_flow_timer_ += dt; else low_flow_timer_ = 0;   // v2.10: a burning pool sustains the flame
    if (low_flow_timer_ > 0.05 || (forced_out && !torch_lit)) { ignited = false; ign_timer_ = 0; unburnt = 0; pool_left = 0.0; inflow_unlit = 0.0; }
  }
  // v2.10 pool-burn source: evaporation at q x A_wet / h_vap while lit and the pool lasts
  mpool = 0.0;
  if (ignited && pool_left > 0.0) {
    mpool = std::min(pool_left / dt, P.pool_q_Wm2 * P.pool_Awet_m2 / P.pool_hvap_Jkg);
    pool_left -= mpool * dt; pool_burnt += mpool * dt;
  }

  // ---- fuel
  const double Ap = M_PI * Dport * Dport / 4.0;
  if (ignited) {
    const double Gox = (mox_burn + mpool) / Ap;   // v2.10: + pool evaporation
    const double rq = tab::k_helix * tab::k_a_reg * P.reg_scale * std::pow(std::max(Gox, 0.0), tab::k_n_reg);
    const double mfq = tab::k_rho_f * M_PI * Dport * tab::k_L_grain * rq;
    double tau = P.tau_f_fixed > 0 ? P.tau_f_fixed : (rq > 1e-6 ? P.tl_scale * P.alpha_fuel / (rq * rq) : 1.0);
    tau = clampd(tau, 0.01, 1.0);
    mf += (mfq - mf) * std::min(1.0, dt / tau);
  } else {
    mf -= mf * std::min(1.0, dt / 0.005);
  }
  const double rdot = mf / (tab::k_rho_f * M_PI * Dport * tab::k_L_grain);
  Dport += 2.0 * rdot * dt;
  fuel_used += mf * dt;
  Vc = tab::k_V_free0 + tab::k_L_grain * M_PI / 4.0 * (Dport * Dport - tab::k_D_port0 * tab::k_D_port0);

  // ---- chamber
  double gam;
  if (ignited) {
    of = clampd((mox_burn + mpool) / std::max(mf, 1e-6), 1.0, 14.0);   // v2.10: + pool
    cstar = tab::k_eta_cstar * P.eta_scale * ceaCstar(Pc, of);
    if (P.starve_s > 0.0 && t_lit_plant >= 0.0 && t - t_lit_plant < P.starve_s) {   // v2.10 scenario: plateau cap (steady Pc <= cap)
      const double At_e = tab::k_At * ((P.At_block_at >= 0 && t >= P.At_block_at) ? (1.0 - P.At_block_frac) : 1.0);
      cstar = std::min(cstar, P.starve_pc_cap_Pa * At_e / std::max(mox_burn + mpool + mf, 1e-6));
    }
    gam = ceaGamma(Pc, of);
  } else {
    of = 0; cstar = P.cstar_cold; gam = P.gamma_cold;
  }
  double burst_rate = 0;
  if (burst_left > 0) { burst_rate = std::min(burst_left / dt, P.hard_start_gain > 0 ? burst_left / 0.005 + 1e-9 : 0.0); burst_left -= burst_rate * dt; }
  const double mgen = mox_burn + mpool + mf + burst_rate + mvap;   // v2.7: vapour purge enters as cold gas; v2.10: + pool
  const double choke = std::min(1.0, std::sqrt(std::max(0.0, (Pc - kPa) / (0.9 * kPa))));
  const double At_eff = tab::k_At * ((P.At_block_at >= 0 && t >= P.At_block_at) ? (1.0 - P.At_block_frac) : 1.0);
  const double mout = Pc * At_eff / cstar * choke;
  const double RT = std::pow(GammaFn(gam) * cstar, 2);
  Pc += RT / Vc * (mgen - mout) * dt;
  Pc = std::max(Pc, kPa);
  thrust = (ignited ? thrustOf(Pc, of) : std::max(0.0, 1.2 * (Pc - kPa) * tab::k_At)) * (At_eff / tab::k_At);   // blockage: approximate
  t += dt;
}

// ------------------------------------------------------------------------------------- servo
// piecewise-linear in supply voltage, linear extrapolation beyond the end points
static double interpN(double V, const double* v, const double* y, int n) {
  int i = 0;
  while (i < n - 2 && V > v[i + 1]) ++i;
  return y[i] + (V - v[i]) * (y[i + 1] - y[i]) / (v[i + 1] - v[i]);
}
struct ServoCurve { int n; double V[4], T[4], s60[4], Ist[4]; };
static constexpr double KGCM = 0.0980665;
static const ServoCurve kSB2292 = {3, {6.0, 7.4, 8.4, 0}, {22.0 * KGCM, 31.0 * KGCM, 45.0 * KGCM, 0},   // DATASHEET (lower set)
                                   {0.085, 0.07, 0.055, 0}, {7.5, 9.2, 10.4, 0}};                       // s/60deg; A (8.4 V ASSUMED)
static const ServoCurve kHV69 = {4, {4.8, 6.0, 7.4, 8.2}, {6.0 * KGCM, 7.5 * KGCM, 9.2 * KGCM, 10.2 * KGCM},   // MKS (retailers)
                                 {0.17, 0.13, 0.11, 0.10},
                                 {1.5 * 4.8 / 7.4, 1.5 * 6.0 / 7.4, 1.5, 1.5 * 8.2 / 7.4}};   // ASSUMED 1.5 A at 7.4 V, ~V
static const ServoCurve& curveOf(int model) { return model == 1 ? kHV69 : kSB2292; }

double ServoParams::tstall() const { const ServoCurve& c = curveOf(model); return torque_scale * std::max(0.05, interpN(V, c.V, c.T, c.n)); }
double ServoParams::wnl() const { const ServoCurve& c = curveOf(model); return speed_scale * (M_PI / 3.0) / std::max(0.03, interpN(V, c.V, c.s60, c.n)); }
double ServoParams::istall() const { const ServoCurve& c = curveOf(model); return std::max(0.05, interpN(V, c.V, c.Ist, c.n)); }

HobbyServo::HobbyServo(const ServoParams& p, uint32_t seed) : P(p), rng_(seed) {
  const double wn = std::sqrt(P.tstall() / P.pb_rad / P.J_int);
  kd_ = std::max(0.0, 2.0 * P.zeta * wn * P.J_int / P.tstall() - 1.0 / P.wnl());
  std::uniform_real_distribution<double> u(0.0, P.frame);
  next_frame_ = u(rng_);
}

void HobbyServo::step(double dt, double t, double T_load, double J_load) {
  // frame latch: pulse starts at next_frame_, width read at its falling edge, applied after latency
  if (t >= next_frame_) {
    std::uniform_real_distribution<double> jit(-0.25, 0.25);   // ASSUMED input-capture jitter [us]
    double us = us_in_ + jit(rng_);
    us = std::round((us - 800.0) / P.quant_us) * P.quant_us + 800.0;
    if (q_n_ == kQ) { q_head_ = (q_head_ + 1) % kQ; --q_n_; }   // cannot happen at 333 Hz; drop the oldest
    const int tail = (q_head_ + q_n_) % kQ;
    q_val_[tail] = us; q_at_[tail] = next_frame_ + us * 1e-6 + P.latency; ++q_n_;
    next_frame_ += P.frame;
  }
  while (q_n_ > 0 && t >= q_at_[q_head_]) { target = (q_val_[q_head_] - P.center_us) / P.us_per_rad; q_head_ = (q_head_ + 1) % kQ; --q_n_; }
  const double Ts = P.tstall(), wnl = P.wnl();
  if (powered) {
    const double e = target - theta;
    const double hb = 0.5 * P.deadband_us / P.us_per_rad;
    const double edb = std::fabs(e) <= hb ? 0.0 : e - std::copysign(hb, e);
    const double u = clampd(edb / P.pb_rad - kd_ * omega, -1.0, 1.0);
    T_motor = Ts * (u - omega / wnl);
    // the drive cannot exceed the torque-speed line in either quadrant
    T_motor = clampd(T_motor, -Ts * (1.0 + std::fabs(omega) / wnl), Ts * (1.0 + std::fabs(omega) / wnl));
  } else {
    T_motor = 0;
  }
  current = 0.005 + P.istall() * std::fabs(T_motor) / Ts;
  const double J = P.J_int + J_load;
  const double Tnet = T_motor - T_load;
  if (std::fabs(omega) < 1e-4 && std::fabs(Tnet) <= P.fric) { omega = 0; return; }
  const double a = (Tnet - std::copysign(P.fric, std::fabs(omega) > 1e-4 ? omega : Tnet)) / J;
  omega += a * dt;
  theta += omega * dt;
}

// ------------------------------------------------------------------------------------- gimbal
GimbalAxis::GimbalAxis(const GimbalParams& g, const ServoParams& s, uint32_t seed) : servo(s, seed), G(g) {}

void GimbalAxis::step(double dt, double t, double us_cmd) {
  servo.setPulse(us_cmd);
  const double ths = servo.theta;
  const double d = G.r_h * std::sin(ths) - G.R_e * std::sin(theta_e);
  const double dd = G.r_h * std::cos(ths) * servo.omega - G.R_e * std::cos(theta_e) * omega_e;
  const double hb = 0.5 * (G.play_m + servo.P.backlash_rad * G.r_h);
  double F = 0;
  if (d > hb) F = G.k_link * (d - hb) + G.c_link * dd;
  else if (d < -hb) F = G.k_link * (d + hb) + G.c_link * dd;
  F_rod = F;
  const double T_servo = F * G.r_h * std::cos(ths);
  const double M_act = F * G.R_e * std::cos(theta_e);
  double M = M_act - (G.k_hose + G.M_acc_per_rad) * theta_e - G.M_mis * G.thrust_frac - G.M_side - G.c_damp * omega_e;
  if (std::fabs(omega_e) > 1e-5) M -= std::copysign(G.M_fric, omega_e);
  else if (std::fabs(M) <= G.M_fric) M = 0;
  else M -= std::copysign(G.M_fric, M);
  omega_e += M / G.I * dt;
  theta_e += omega_e * dt;
  if (theta_e > G.stop_rad) { theta_e = G.stop_rad; omega_e = std::min(0.0, omega_e); }
  if (theta_e < -G.stop_rad) { theta_e = -G.stop_rad; omega_e = std::max(0.0, omega_e); }
  servo.step(dt, t, T_servo, 0.0);
}

// ------------------------------------------------------------------------------------- pintle drive
PintleDrive::PintleDrive(const PintleMechParams& m, const ServoParams& s, uint32_t seed) : servo(s, seed), M(m) {
  servo.theta = (M.phi_c - 5.0 * M_PI / 180) - M.phi_n;   // start seated at the closed command
  servo.target = servo.theta;
  flank_ = -0.5 * servo.P.backlash_rad;
  // crank angle at the lift stop (bisection on the monotonic crank-slider lift between contact and bottom dead centre)
  double lo = M.phi_c, hi = M_PI;
  for (int i = 0; i < 60; ++i) { const double mid = 0.5 * (lo + hi); if (M.lift(mid) < M.stroke_max) lo = mid; else hi = mid; }
  phi_stop = 0.5 * (lo + hi);
}

void PintleDrive::step(double dt, double t, double us_cmd, double p_feed, double Pc) {
  servo.setPulse(us_cmd);
  // v2.5 lift stop: the crank cannot pass the 4.2 mm stop (runaway / over-travel); the servo stalls against it
  at_stop = crank() >= phi_stop;
  if (at_stop) { servo.theta = phi_stop - M.phi_n - flank_; servo.omega = std::min(0.0, servo.omega); }
  const double phi = crank();
  const bool contact = phi > M.phi_c;
  x = contact ? std::min(M.stroke_max, M.lift(phi)) : 0.0;
  const double dxdphi = M.dxdphi(phi);
  xdot = dxdphi * servo.omega;
  const double w = std::min(1.0, x / 1.0e-4);
  const double f_seat = (p_feed - Pc) * M.A_seat - (p_feed - kPa) * M.A_stem;
  const double f_open = -(p_feed - kPa) * M.A_stem;
  const double Fp = (1 - w) * f_seat + w * f_open;
  const double Fs = M.F0 + M.k_spring * x;
  const double Ff = M.F_seal * std::tanh(xdot / M.v_eps);
  F_net = contact ? Fp + Fs + Ff : 0.0;
  contact_lost = contact && (Fp + Fs - M.F_seal < 0.0);
  // gear flank: preload keeps the train on the opening flank while the net load resists opening
  const double hb = 0.5 * servo.P.backlash_rad;
  if (contact && F_net > 1.0) flank_ = -hb;
  else if (contact && F_net < -1.0) flank_ = +hb;
  double T_load = 0.0;
  if (contact) T_load = F_net * dxdphi * (servo.omega >= 0 ? 1.0 / M.eta : M.eta);
  if (at_stop) T_load = std::max(T_load, servo.T_motor);   // the stop reacts whatever drives the crank into it
  servo.step(dt, t, T_load, 0.02 * dxdphi * dxdphi);
}

// ------------------------------------------------------------------------------------- 2-axis gimbal (v2.6)
GimbalPlant2::GimbalPlant2(const Gimbal2Params& g, const ServoParams& sa, const ServoParams& sb, uint32_t seed)
    : servo{HobbyServo(sa, seed), HobbyServo(sb, seed + 101)}, G(g) {}

void GimbalPlant2::leverEye(int i, double al_, double be, double P[3], double dPa[3], double dPb[3]) const {
  // R = Rx(al) Ry(be): Ry P0 = (x1, y0, z1); P = (x1, y0 ca - z1 sa, y0 sa + z1 ca)
  const double x0 = G.P0[i][0], y0 = G.P0[i][1], z0 = G.P0[i][2];
  const double ca = std::cos(al_), sa = std::sin(al_), cb = std::cos(be), sb = std::sin(be);
  const double x1 = x0 * cb + z0 * sb, z1 = -x0 * sb + z0 * cb;
  P[0] = x1; P[1] = y0 * ca - z1 * sa; P[2] = y0 * sa + z1 * ca;
  if (dPa) { dPa[0] = 0.0; dPa[1] = -y0 * sa - z1 * ca; dPa[2] = y0 * ca - z1 * sa; }
  if (dPb) { dPb[0] = z1; dPb[1] = x1 * sa; dPb[2] = -x1 * ca; }   // d(x1)/db = z1, d(z1)/db = -x1
}

double GimbalPlant2::dz(int i, double al_, double be, double* dda, double* ddb) const {
  double P[3], Pa[3], Pb[3];
  leverEye(i, al_, be, P, Pa, Pb);
  if (dda) *dda = Pa[2];
  if (ddb) *ddb = Pb[2];
  return P[2] - G.P0[i][2];
}

double GimbalPlant2::rodLength(int i) const {
  double P[3];
  leverEye(i, G.flex ? al : a, G.flex ? bl : b, P, nullptr, nullptr);
  const double th = servo[i].theta, c = std::cos(th), s = std::sin(th);
  const double H[3] = {G.C[i][0] - G.r_h * c * G.u[i][0], G.C[i][1] - G.r_h * c * G.u[i][1], G.C[i][2] + G.r_h * s};
  return std::sqrt((P[0] - H[0]) * (P[0] - H[0]) + (P[1] - H[1]) * (P[1] - H[1]) + (P[2] - H[2]) * (P[2] - H[2]));
}

void GimbalPlant2::step(double dt, double t, const double us_cmd[2]) {
  // rods act on the lever frame (flex) or directly on the engine (rigid structure)
  const double qa = G.flex ? al : a, qb = G.flex ? bl : b, qwa = G.flex ? wal : wa, qwb = G.flex ? wbl : wb;
  double Ma = 0, Mb = 0;
  for (int i = 0; i < 2; ++i) {
    servo[i].setPulse(us_cmd[i]);
    double P[3], Pa[3], Pb[3];
    leverEye(i, qa, qb, P, Pa, Pb);
    const double th = servo[i].theta, c = std::cos(th), s = std::sin(th);
    const double H[3] = {G.C[i][0] - G.r_h * c * G.u[i][0], G.C[i][1] - G.r_h * c * G.u[i][1], G.C[i][2] + G.r_h * s};
    const double Hth[3] = {G.r_h * s * G.u[i][0], G.r_h * s * G.u[i][1], G.r_h * c};   // dH/dtheta
    const double r[3] = {P[0] - H[0], P[1] - H[1], P[2] - H[2]};
    const double len = std::sqrt(r[0] * r[0] + r[1] * r[1] + r[2] * r[2]);
    const double e[3] = {r[0] / len, r[1] / len, r[2] / len};                          // unit vector horn eye -> lever eye
    const double eA = e[0] * Pa[0] + e[1] * Pa[1] + e[2] * Pa[2], eB = e[0] * Pb[0] + e[1] * Pb[1] + e[2] * Pb[2];
    const double eH = e[0] * Hth[0] + e[1] * Hth[1] + e[2] * Hth[2];
    const double ldot = eA * qwa + eB * qwb - eH * servo[i].omega;                     // rod length rate
    const double x = G.L_rod - len;                                                    // shortening (compression > 0)
    const double hb = 0.5 * (G.play_m + servo[i].P.backlash_rad * G.r_h);
    double F = 0;
    if (x > hb) F = G.k_link * (x - hb) - G.c_link * ldot;
    else if (x < -hb) F = G.k_link * (x + hb) - G.c_link * ldot;
    F_rod[i] = F;
    Ma += F * eA; Mb += F * eB;                      // compression pushes the lever eye away from the horn eye
    servo[i].step(dt, t, F * eH, 0.0);               // ... and resists the horn eye moving toward the lever eye
  }
  const double Md = G.M_mis * G.thrust_frac + G.M_side;
  const double Mdist[2] = {Md * std::cos(G.dist_dir_rad), Md * std::sin(G.dist_dir_rad)};
  double* w[2] = {&wa, &wb};
  double* th[2] = {&a, &b};
  double* wl[2] = {&wal, &wbl};
  double* thl[2] = {&al, &bl};
  const double Mr[2] = {Ma, Mb};
  for (int k = 0; k < 2; ++k) {
    double Me;                                       // moment reaching the engine through the structure
    if (G.flex) {
      const double cs = 2.0 * G.zeta_struct * std::sqrt(G.K_struct[k] * G.I[k]);
      Me = G.K_struct[k] * (*thl[k] - *th[k]) + cs * (*wl[k] - *w[k]);
      *wl[k] += (Mr[k] - Me) / G.I_lev * dt;
      *thl[k] += *wl[k] * dt;
    } else {
      Me = Mr[k];
    }
    double M = Me - (G.k_hose - G.K_axacc) * *th[k] - Mdist[k] - G.c_damp * *w[k] + M_ext[k];
    if (std::fabs(*w[k]) > 1e-5) M -= std::copysign(G.M_fric, *w[k]);
    else if (std::fabs(M) <= G.M_fric) M = 0;
    else M -= std::copysign(G.M_fric, M);
    const double Ie = G.flex ? G.I[k] - G.I_lev : G.I[k];
    *w[k] += M / Ie * dt;
    *th[k] += *w[k] * dt;
  }
  const double r = std::sqrt(a * a + b * b);
  at_stop = r > G.stop_rad;
  if (at_stop) {   // conical stop: back onto the cone, remove the outward radial velocity
    const double ua = a / r, ub = b / r;
    a = ua * G.stop_rad; b = ub * G.stop_rad;
    const double vr = wa * ua + wb * ub;
    if (vr > 0) { wa -= vr * ua; wb -= vr * ub; }
  }
  if (!G.flex) { al = a; bl = b; wal = wa; wbl = wb; }
}

// lowest eigenvalue of K x = w^2 M x (3 DOF, M diagonal, K symmetric positive definite) by inverse iteration
static double lowestOmega2(const double K[3][3], const double Md[3]) {
  double x[3] = {1.0, 1.0, 1.0}, lam = 0.0;
  for (int it = 0; it < 200; ++it) {
    double rhs[3] = {Md[0] * x[0], Md[1] * x[1], Md[2] * x[2]};
    double A[3][4];
    for (int r = 0; r < 3; ++r) { for (int c = 0; c < 3; ++c) A[r][c] = K[r][c]; A[r][3] = rhs[r]; }
    for (int p = 0; p < 3; ++p)
      for (int r = p + 1; r < 3; ++r) { const double f = A[r][p] / A[p][p]; for (int c = p; c < 4; ++c) A[r][c] -= f * A[p][c]; }
    double y[3];
    for (int r = 2; r >= 0; --r) { double v = A[r][3]; for (int c = r + 1; c < 3; ++c) v -= A[r][c] * y[c]; y[r] = v / A[r][r]; }
    const double n = std::sqrt(y[0] * y[0] + y[1] * y[1] + y[2] * y[2]);
    for (int k = 0; k < 3; ++k) x[k] = y[k] / n;
    double xKx = 0, xMx = 0;
    for (int r = 0; r < 3; ++r) { xMx += Md[r] * x[r] * x[r]; for (int c = 0; c < 3; ++c) xKx += x[r] * K[r][c] * x[c]; }
    const double l2 = xKx / xMx;
    if (it > 5 && std::fabs(l2 - lam) < 1e-12 * l2) { lam = l2; break; }
    lam = l2;
  }
  return lam;
}

// linear chain matrices for one axis at neutral (shared by the undamped mode and the damped response)
struct Chain3 { double K[3][3], C[3][3], M[3], Kse; };
static Chain3 chain3(const Gimbal2Params& g, const ServoParams& s, int axis) {
  GimbalPlant2 p(g, s, s, 1);
  double m2 = 0, j2 = 0;
  for (int i = 0; i < 2; ++i) {
    double Pa[3], Pb[3], P[3];
    p.leverEye(i, 0.0, 0.0, P, Pa, Pb);
    const double j = axis == 0 ? Pa[2] : Pb[2];
    j2 += j * j; m2 += (j / g.r_h) * (j / g.r_h);
  }
  const double Ts = s.tstall(), wnl = s.wnl(), Ks = Ts / s.pb_rad;
  const double wn = std::sqrt(Ks / s.J_int), kd = std::max(0.0, 2.0 * s.zeta * wn * s.J_int / Ts - 1.0 / wnl);   // as HobbyServo
  Chain3 c{};
  c.Kse = Ks * m2;
  const double Kch = g.k_link * j2, Kst = g.flex ? g.K_struct[axis] : 1e12, Kh = g.k_hose - g.K_axacc;
  const double Cr = Ts * (kd + 1.0 / wnl) * m2, Cch = g.c_link * j2;
  const double Cst = g.flex ? 2.0 * g.zeta_struct * std::sqrt(g.K_struct[axis] * g.I[axis]) : 0.0;
  const double Kr[3][3] = {{c.Kse + Kch, -Kch, 0.0}, {-Kch, Kch + Kst, -Kst}, {0.0, -Kst, Kst + Kh}};
  const double Cm[3][3] = {{Cr + Cch, -Cch, 0.0}, {-Cch, Cch + Cst, -Cst}, {0.0, -Cst, Cst + g.c_damp}};
  for (int r = 0; r < 3; ++r) for (int k = 0; k < 3; ++k) { c.K[r][k] = Kr[r][k]; c.C[r][k] = Cm[r][k]; }
  c.M[0] = s.J_int * m2; c.M[1] = g.flex ? g.I_lev : 1e-9; c.M[2] = g.flex ? g.I[axis] - g.I_lev : g.I[axis];
  return c;
}

double rockingGain(const Gimbal2Params& g, const ServoParams& s, int axis, double f_Hz) {
  const Chain3 c = chain3(g, s, axis);
  const double w = 2.0 * M_PI * f_Hz;
  std::complex<double> A[3][4];
  for (int r = 0; r < 3; ++r) {
    for (int k = 0; k < 3; ++k) A[r][k] = std::complex<double>(c.K[r][k] - (r == k ? w * w * c.M[r] : 0.0), w * c.C[r][k]);
    A[r][3] = r == 0 ? std::complex<double>(c.Kse, 0.0) : 0.0;   // unit commanded angle through the servo loop stiffness
  }
  for (int p = 0; p < 3; ++p)
    for (int r = p + 1; r < 3; ++r) { const std::complex<double> f = A[r][p] / A[p][p]; for (int k = p; k < 4; ++k) A[r][k] -= f * A[p][k]; }
  std::complex<double> x[3];
  for (int r = 2; r >= 0; --r) { std::complex<double> v = A[r][3]; for (int k = r + 1; k < 3; ++k) v -= A[r][k] * x[k]; x[r] = v / A[r][r]; }
  return std::abs(x[2]);
}

double rockingPeakHz(const Gimbal2Params& g, const ServoParams& s, int axis, double* gain_peak, double fmin, double fmax) {
  double fb = fmin, gb = 0;
  for (double f = fmin; f <= fmax; f *= 1.01) { const double v = rockingGain(g, s, axis, f); if (v > gb) { gb = v; fb = f; } }
  if (gain_peak) *gain_peak = gb;
  return fb;
}

double rockingModeHz(const Gimbal2Params& g, const ServoParams& s, int axis) {
  // generalized coordinates: q0 = servo angles in the axis pattern (psi_i = m_i q0, m_i = d psi_i / d theta_axis at neutral),
  // q1 = lever frame, q2 = engine (both about the axis); undamped
  const Chain3 c = chain3(g, s, axis);
  return std::sqrt(lowestOmega2(c.K, c.M)) / (2.0 * M_PI);
}

// ------------------------------------------------------------------------------------- Pc sense line (v2.1)
SenseLine::SenseLine(const SenseLineParams& p) : P(p) {}
double SenseLine::c() const { return std::sqrt(P.n_poly * 8.314462618 * P.T / P.M); }
void SenseLine::init(double p0) { p_.assign(P.N, p0); q_.assign(P.N, 0.0); }

double SenseLine::step(double dt, double p_in) {
  if (!P.enabled) return p_in;
  if (p_.empty()) init(p_in);
  const double A = M_PI / 4 * P.ID * P.ID, r = 0.5 * P.ID, dx = P.L / P.N;
  const double Rs = 8.314462618 / P.M;
  const double R = 8.0 * P.mu * dx / (M_PI * r * r * r * r);           // Poiseuille resistance per section (volumetric)
  const int m = std::max(1, static_cast<int>(std::ceil(dt * c() / (0.5 * dx))));
  const double h = dt / m;
  if (P.legacy_v21) {   // v2.1-v2.5 (kept for comparison): q_ = volumetric flow, inertance at the branch-mean density
    for (int s = 0; s < m; ++s) {
      for (int k = 0; k < P.N; ++k) {
        const double pu = k == 0 ? p_in : p_[k - 1];
        const double rho = std::max(0.5 * (pu + p_[k]), 1.0e3) / (Rs * P.T);
        const double Lk = rho * dx / A;
        q_[k] = (q_[k] + h / Lk * (pu - p_[k])) / (1.0 + h * R / Lk);
      }
      for (int k = 0; k < P.N; ++k) {
        const double V = A * dx + (k == P.N - 1 ? P.V_end : 0.0);
        const double C = V / (P.n_poly * std::max(p_[k], 1.0e3));
        const double qout = k == P.N - 1 ? 0.0 : q_[k + 1];
        p_[k] += h * (q_[k] - qout) / C;
      }
    }
    return p_[P.N - 1];
  }
  // v2.6: q_ = MASS flow [kg/s]; node storage dp/dt = c^2 (mdot_in - mdot_out) / V with c^2 = n Rs T (linear acoustics about the
  // line gas state, mass-conservative); branch momentum dmdot/dt = (A/dx)(p_up - p) - (A/dx)(R/rho) mdot (laminar friction at the
  // local density, semi-implicit). Same small-signal response as v2.1 at any mean pressure; a step now overshoots <= 2x (lossless
  // bound) instead of growing. Strong-shock reflection (pressure ratio >> 2) is outside this lumped model.
  const double c2 = P.n_poly * Rs * P.T;
  for (int s = 0; s < m; ++s) {
    for (int k = 0; k < P.N; ++k) {                                       // branch k: node k-1 (or inlet) -> node k
      const double pu = k == 0 ? p_in : p_[k - 1];
      const double rho = std::max(0.5 * (pu + p_[k]), 1.0e3) / (Rs * P.T);
      q_[k] = (q_[k] + h * A / dx * (pu - p_[k])) / (1.0 + h * A / dx * R / rho);
    }
    for (int k = 0; k < P.N; ++k) {                                       // node k: storage (+ end volume)
      const double V = A * dx + (k == P.N - 1 ? P.V_end : 0.0);
      const double qout = k == P.N - 1 ? 0.0 : q_[k + 1];
      p_[k] = std::max(p_[k] + h * c2 * (q_[k] - qout) / V, 1.0e3);    // no pressure below 0.01 bar abs (vacuum limit)
    }
  }
  return p_[P.N - 1];
}

}  // namespace sil
