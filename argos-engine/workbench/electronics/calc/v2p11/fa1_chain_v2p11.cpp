// Electronics v2.11 (2026-10-13) FA-1 Pc-chain harness: LEAD CHANGELOG 203 (1)(b) ride-through sizing and LEAD 205 transducer
// reselection. Combustion's FA-1 relight pressure histories (02-combustion/data/v2p4a/fa1_envelope_v2p4a.json, 896 cases, exported
// by calc/v2p10/fa1_overrange.py extract; SIM on an ASSUMED construct) are played open loop through each Pc measurement chain and
// the firmware rules of the light window are evaluated on the 1 kHz reading (firmware constants from config.h).
// Chains (all SIM; tags per element):
//   v210_line   : v2.10 SIL chain, TE 070BG 0-70 bar g on the 0.30 m sense line (plant.h SenseLineParams defaults, ASSUMED),
//                 0.9 ms lag, output limited at 4.95 V, U330 tap 0.2401 / RC 5.283 ms (calc/pc_transducer_v2.py). Comparator only.
//   v210_noline : the same transducer without the line (the v2.10 sizing basis after LEAD 203 (2)).
//   c1_*        : v2.11 proposal C1 Kulite XTL-190SM-2000A (137.9 bar abs) on the seat passage of the v3.5.1 head (sil::SenseLine
//                 lumped model: CC-1 = dia 2.044 mm equivalent x 56.17 mm (passage 54.17 + disc 2.0, volume 184.3 mm3 as Mechanical),
//                 CC-2 = 32 mm; front dead volume 6 mm3 ASSUMED (20 mm3 bound); passage gas sound speed MISSING -> bracket 222 m/s
//                 (N2O vapour 200 K) and 400 m/s (products 400 K) as Mechanical pc_line_period_v1), transducer f_n ~ 1 MHz (no lag),
//                 INA333 pole 4.39 kHz and rail limit 4.95 V (DATASHEET-derived), ADC path anti-alias 2.37 kHz (DESIGN), U330 tap
//                 1/2, RC 5.225 ms, trip 32.59 bar abs +/- 1.51 bar (calc/v2p11/pc_transducer_v3.py, generated ovp_hw_params.h ovp3).
// Per case (worst over 4 ADC phases): face peak, 1 kHz reading peak, over-range (>= 4.75 V) and above-FS (>= 4.56 V) ticks before
// E2, E2 time (relative light rule), filtered (50 Hz) peak, cumulative and longest continuous filtered > 30 bar abs, end of the
// last filtered > 30 episode relative to E2, firmware 30 bar persistence trips for 5 (as built) / 10 / 15 / 20 / 25 ms, comparator
// RC maxima and trips (nominal / low band edge) for tau = as built / 10 / 15 / 20 / 30 ms held over the whole history (the
// ride-through switched capacitor is engaged before the light and the node is pre-charged: no charge-sharing step, DESIGN), the
// longest continuous and total raw reading > 45 bar abs, and the head-history time above 45 bar (0.1 ms grid).
// Open loop: a trip does not change the history. Usage: fa1_chain_v2p11 <hist_head.txt> <out_csv> [chain,...]
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>
#include "config.h"
#include "filters.h"
#include "ovp_hw_params.h"
#include "plant.h"

namespace {
constexpr double kPamb = 101325.0;
constexpr int kNP = 5, kNT = 5;
const double kPers[kNP] = {0.005, 0.010, 0.015, 0.020, 0.025};
const double kTauW[kNT] = {-1.0, 0.010, 0.015, 0.020, 0.030};   // -1 = as built

struct Chain {
  const char* name;
  bool abs_xdcr;            // false: 070BG gauge (v = 0.5 + 4 (p - pamb)/FS); true: absolute (v = 0.5 + 4 p/FS)
  double fs, tau_x, vsat, adc_max_V, ina_fc, aaf_fc, tau_rc, v_nom, v_lo;
  bool line;                // passage / line model on
  sil::SenseLineParams sp;
};

struct Res {
  double face_pk = 0, vmax = 0, raw_pk = 0, filt_pk = 0, t30f = 0, c30f = 0, c30_end = -1, tE2 = -1, t45c = 0, t45t = 0;
  int n475_ign = 0, n456_ign = 0, n475 = 0;
  bool fw[kNP] = {false, false, false, false, false};
  double tfw0 = -1;
  double cmpv[kNT] = {0, 0, 0, 0, 0};
  bool cnom[kNT] = {false, false, false, false, false}, clo[kNT] = {false, false, false, false, false};
  double tcmp0 = -1;
};

Res run(const std::vector<double>& p, double phase_s, const Chain& ch) {
  using namespace ecu;
  const double dtp = 25e-6, dgrid = 1e-4;
  sil::SenseLine line(ch.sp); line.init(p[0] * 1e5);
  LowPass2 lpf; lpf.setup(cfg::kPcFilterFc_Hz, cfg::kDt_s);
  const double p0g = p[0] * 1e5 - kPamb;
  for (int k = 0; k < 400; ++k) lpf.step(static_cast<float>(p0g));
  Persist pers[kNP]; Res r;
  auto vlin = [&](double pa) { return 0.5 + 4.0 * (ch.abs_xdcr ? pa : pa - kPamb) / ch.fs; };
  const double v0 = vlin(p[0] * 1e5);
  double x2 = p[0] * 1e5, vina = v0, vaaf = v0, vc[kNT];
  for (int k = 0; k < kNT; ++k) vc[k] = v0;
  double acc = 0, ref_f = 0, ref_r = 0; int nacc = 0, nref = 0, ign_n = 0;
  const double pre = 0.05, t_hist = dgrid * (p.size() - 1), t_end = 0.100;
  double next_adc = -pre + phase_s, next_ms = -pre + phase_s + 1e-3;
  bool lit = false, in45 = false, in30 = false; double run45 = 0, run30 = 0;
  for (double ts = -pre; ts <= t_end; ts += dtp) {
    double ph = p[0];
    if (ts >= t_hist) ph = p.back();
    else if (ts >= 0.0) { const size_t j = std::min(p.size() - 2, static_cast<size_t>(ts / dgrid)); const double f = std::fmin(1.0, ts / dgrid - j); ph = p[j] + (p[j + 1] - p[j]) * f; }
    const double s1 = ch.line ? line.step(dtp, ph * 1e5) : ph * 1e5;               // pressure at the diaphragm
    if (ts >= 0.0) r.face_pk = std::fmax(r.face_pk, s1);
    if (ch.tau_x > 0.0) x2 += (s1 - x2) * std::fmin(1.0, dtp / ch.tau_x); else x2 = s1;
    double v_sig;
    if (ch.ina_fc > 0.0) {                                                         // v2.11: INA333 pole, then its rail limit
      vina += (vlin(x2) - vina) * (1.0 - std::exp(-2.0 * M_PI * ch.ina_fc * dtp));
      v_sig = std::fmax(0.05, std::fmin(ch.vsat, vina));
    } else {
      v_sig = std::fmax(0.0, std::fmin(ch.vsat, vlin(x2)));                         // v2.10: transducer output limited at v_sat
    }
    for (int k = 0; k < kNT; ++k) {
      const double tau = kTauW[k] < 0 ? ch.tau_rc : kTauW[k];
      vc[k] += (v_sig - vc[k]) * dtp / tau;
      if (ts >= 0.0) {
        r.cmpv[k] = std::fmax(r.cmpv[k], vc[k]);
        if (vc[k] > ch.v_lo) r.clo[k] = true;
        if (vc[k] > ch.v_nom) { if (!r.cnom[k] && k == 0) r.tcmp0 = ts; r.cnom[k] = true; }
      }
    }
    double v_adc = v_sig;
    if (ch.aaf_fc > 0.0) { vaaf += (v_sig - vaaf) * (1.0 - std::exp(-2.0 * M_PI * ch.aaf_fc * dtp)); v_adc = vaaf; }
    if (ts >= next_adc) { acc += std::fmin(ch.adc_max_V, v_adc); ++nacc; next_adc += 0.00025; }   // per-sample ADC limit
    if (ts >= next_ms) {
      next_ms += 1e-3;
      const double v = nacc ? acc / nacc : v_adc; acc = 0; nacc = 0;            // 1 kHz reading (pc_raw_V)
      const double raw_g = (v - 0.5) / 4.0 * ch.fs - (ch.abs_xdcr ? kPamb : 0.0), raw_abs = raw_g + kPamb;
      const float filt_g = lpf.step(static_cast<float>(raw_g));
      const double filt_abs = static_cast<double>(filt_g) + kPamb;
      if (ts < 0.0) { if (ts >= -0.0205) { ref_f += filt_g; ref_r += raw_g; ++nref; } continue; }
      const double rf = nref ? ref_f / nref : 0.0, rr = nref ? ref_r / nref : 0.0;
      if (!lit) {
        const bool ok = (filt_g - rf) >= cfg::kIgnRise_Pa && (raw_g - rr) >= cfg::kIgnRise_Pa && filt_abs >= cfg::kIgnFloorAbs_Pa &&
                        raw_abs >= cfg::kIgnFloorAbs_Pa;
        ign_n = ok ? ign_n + 1 : 0;
      }
      if (v >= cfg::kPcSensorMax_V) { ++r.n475; if (!lit) ++r.n475_ign; }
      if (v >= 4.56 && !lit) ++r.n456_ign;                                         // above full scale (FS 4.5 V + 0.06 V)
      if (!lit && ign_n >= cfg::kIgnConfirmRelN) { lit = true; r.tE2 = ts; }
      r.vmax = std::fmax(r.vmax, v);
      r.raw_pk = std::fmax(r.raw_pk, raw_abs); r.filt_pk = std::fmax(r.filt_pk, filt_abs);
      const bool f30 = filt_abs > cfg::kPcOverPressureAbs_Pa;
      if (f30) { r.t30f += 1e-3; run30 += 1e-3; r.c30f = std::fmax(r.c30f, run30); r.c30_end = ts; in30 = true; } else { run30 = 0; in30 = false; }
      for (int k = 0; k < kNP; ++k)
        if (pers[k].step(f30, static_cast<float>(kPers[k]), cfg::kDt_s) && !r.fw[k]) { r.fw[k] = true; if (k == 0) r.tfw0 = ts; }
      const bool a45 = raw_abs > cfg::kPcMeopLeadAbs_Pa;
      if (a45) { r.t45t += 1e-3; run45 += 1e-3; r.t45c = std::fmax(r.t45c, run45); } else run45 = 0;
      (void)in45; (void)in30;
    }
  }
  return r;
}

std::vector<std::vector<double>> load(const std::string& fn) {
  std::vector<std::vector<double>> out; std::ifstream f(fn); std::string line;
  while (std::getline(f, line)) {
    std::istringstream is(line); int i; is >> i; std::vector<double> v; double x;
    while (is >> x) v.push_back(x);
    if (static_cast<int>(out.size()) != i || v.size() != 251) { std::fprintf(stderr, "bad line %d in %s\n", i, fn.c_str()); std::exit(2); }
    out.push_back(v);
  }
  return out;
}
double tmin(double a, double b) { return a < 0 ? b : (b < 0 ? a : std::fmin(a, b)); }

sil::SenseLineParams passage(double L, double c, double V_end_mm3) {
  sil::SenseLineParams sp;
  sp.L = L; sp.ID = 2.044e-3; sp.V_end = V_end_mm3 * 1e-9; sp.N = 24; sp.n_poly = 1.15;   // N 24: ladder cutoff >= 30 kHz
  sp.M = c < 300 ? 0.044 : 0.0235;                     // N2O vapour / products molar mass [ASSUMED]
  sp.T = c * c * sp.M / (sp.n_poly * 8.314462618);     // gas temperature that gives the bracket sound speed c (Mechanical table)
  sp.mu = 1.5e-5;                                      // [ASSUMED] gas viscosity (laminar friction only: low damping, conservative)
  sp.enabled = true;
  return sp;
}

double headAbove(const std::vector<double>& p, double lvl_bar, bool cont) {
  double best = 0, run = 0, tot = 0;
  for (size_t i = 0; i + 1 < p.size(); ++i) {
    const bool a = p[i] > lvl_bar;
    if (a) { run += 1e-4; tot += 1e-4; best = std::fmax(best, run); } else run = 0;
  }
  return cont ? best : tot;
}
}  // namespace

int main(int argc, char** argv) {
  if (argc < 3) { std::fprintf(stderr, "usage: fa1_chain_v2p11 <hist_head.txt> <out_csv> [chain,...]\n"); return 1; }
  const auto head = load(argv[1]);
  std::vector<Chain> chains;
  {
    Chain a{}; a.name = "v210_line"; a.abs_xdcr = false; a.fs = sil::ovp::kPcFs_Pa; a.tau_x = 0.0009; a.vsat = 4.95; a.adc_max_V = 4.99;
    a.ina_fc = 0; a.aaf_fc = 0; a.tau_rc = sil::ovp::kTau_s; a.v_nom = 0.5 + 4.0 * sil::ovp::kTripPa_g / a.fs;
    a.v_lo = 0.5 + 4.0 * (sil::ovp::kTripPa_g - sil::ovp::kBandPa) / a.fs; a.line = true; a.sp = sil::SenseLineParams();
    chains.push_back(a);
    Chain b = a; b.name = "v210_noline"; b.line = false; b.sp.enabled = false; chains.push_back(b);
    Chain c{}; c.abs_xdcr = true; c.fs = sil::ovp3::kPcFsAbs_Pa; c.tau_x = 0; c.vsat = sil::ovp3::kVsat_V;
    c.adc_max_V = 1.2 / 0.23822; c.ina_fc = sil::ovp3::kInaFc_Hz; c.aaf_fc = sil::ovp3::kAafFc_Hz; c.tau_rc = sil::ovp3::kTau_s;
    c.v_nom = 0.5 + 4.0 * sil::ovp3::kTripPaAbs / c.fs; c.v_lo = 0.5 + 4.0 * (sil::ovp3::kTripPaAbs - sil::ovp3::kBandPa) / c.fs;
    c.line = true;
    Chain c1 = c; c1.name = "c1_cc1_c222_v6"; c1.sp = passage(0.05617, 222.0, 6.0); chains.push_back(c1);
    Chain c2 = c; c2.name = "c1_cc1_c400_v6"; c2.sp = passage(0.05617, 400.0, 6.0); chains.push_back(c2);
    Chain c3 = c; c3.name = "c1_cc1_c222_v20"; c3.sp = passage(0.05617, 222.0, 20.0); chains.push_back(c3);
    Chain c4 = c; c4.name = "c1_cc2_c222_v6"; c4.sp = passage(0.032, 222.0, 6.0); chains.push_back(c4);
  }
  std::vector<std::string> want;
  if (argc > 3) { std::stringstream ss(argv[3]); std::string t; while (std::getline(ss, t, ',')) want.push_back(t); }
  // passage self-check (linear small step 30 -> 31 bar abs with a 0.05 ms ramp): dominant frequency by a DFT scan 0.3-5 kHz over
  // 8 ms (-> period, to compare with Mechanical pc_line_period_v1), and the face peak for a 1 -> 40 bar abs step with a 0.5 ms ramp
  for (const Chain& ch : chains) {
    if (!ch.line || !ch.sp.enabled || std::strncmp(ch.name, "c1", 2)) continue;
    sil::SenseLine ln(ch.sp); ln.init(30e5);
    std::vector<double> y;
    for (int k = 0; k < 8000; ++k) { const double t = k * 1e-6; y.push_back(ln.step(1e-6, 30e5 + 1e5 * std::fmin(1.0, t / 5e-5)) - 31e5); }
    double fbest = 0, abest = 0;
    for (double f = 300; f <= 5000; f += 5) {
      double re = 0, im = 0;
      for (size_t k = 0; k < y.size(); ++k) { re += y[k] * std::cos(2 * M_PI * f * k * 1e-6); im += y[k] * std::sin(2 * M_PI * f * k * 1e-6); }
      const double amp = std::hypot(re, im);
      if (amp > abest) { abest = amp; fbest = f; }
    }
    sil::SenseLine l2(ch.sp); l2.init(1e5); double pk = 0;
    for (int k = 0; k < 8000; ++k) { const double t = k * 1e-6; pk = std::fmax(pk, l2.step(1e-6, 1e5 + 39e5 * std::fmin(1.0, t / 5e-4))); }
    std::printf("passage %s: c %.0f m/s, dominant %.0f Hz -> period %.3f ms; 1->40 bar (0.5 ms ramp) face peak %.2f bar abs (x%.3f of the step)\n",
                ch.name, ln.c(), fbest, 1e3 / fbest, pk / 1e5, (pk - 1e5) / 39e5);
  }
  std::FILE* fo = std::fopen(argv[2], "w");
  std::fprintf(fo, "case,chain,face_pk_bar,vmax_V,n475_ign,n456_ign,n475,tE2_ms,raw_pk_bar,filt_pk_bar,t30f_ms,c30f_ms,c30_end_rel_E2_ms,"
                   "fw5,fw10,fw15,fw20,fw25,t_fw5_ms,cmp_v_asb,cmp_v_10,cmp_v_15,cmp_v_20,cmp_v_30,cnom_asb,clo_asb,clo_10,clo_15,clo_20,"
                   "clo_30,t_cmp_ms,t45c_ms,t45t_ms,head_above45_cont_ms,head_above45_tot_ms,head_pk_bar\n");
  long nrun = 0;
  for (const Chain& ch : chains) {
    if (!want.empty() && std::find(want.begin(), want.end(), ch.name) == want.end()) continue;
    for (size_t c = 0; c < head.size(); ++c) {
      Res w; bool first = true;
      for (int ph = 0; ph < 4; ++ph) {
        const Res r = run(head[c], ph * 0.00025, ch); ++nrun;
        if (first) { w = r; first = false; continue; }
        w.face_pk = std::fmax(w.face_pk, r.face_pk); w.vmax = std::fmax(w.vmax, r.vmax); w.raw_pk = std::fmax(w.raw_pk, r.raw_pk);
        w.filt_pk = std::fmax(w.filt_pk, r.filt_pk); w.t30f = std::fmax(w.t30f, r.t30f); w.c30f = std::fmax(w.c30f, r.c30f);
        const double e_w = w.c30_end >= 0 && w.tE2 >= 0 ? w.c30_end - w.tE2 : -1e9, e_r = r.c30_end >= 0 && r.tE2 >= 0 ? r.c30_end - r.tE2 : -1e9;
        if (e_r > e_w) { w.c30_end = r.c30_end; }
        w.tE2 = tmin(w.tE2, r.tE2); w.tfw0 = tmin(w.tfw0, r.tfw0); w.tcmp0 = tmin(w.tcmp0, r.tcmp0);
        w.t45c = std::fmax(w.t45c, r.t45c); w.t45t = std::fmax(w.t45t, r.t45t);
        w.n475_ign = std::max(w.n475_ign, r.n475_ign); w.n456_ign = std::max(w.n456_ign, r.n456_ign); w.n475 = std::max(w.n475, r.n475);
        for (int k = 0; k < kNP; ++k) w.fw[k] |= r.fw[k];
        for (int k = 0; k < kNT; ++k) { w.cmpv[k] = std::fmax(w.cmpv[k], r.cmpv[k]); w.cnom[k] |= r.cnom[k]; w.clo[k] |= r.clo[k]; }
      }
      const double end_rel = (w.c30_end >= 0 && w.tE2 >= 0) ? (w.c30_end - w.tE2) * 1e3 : -999.0;
      std::fprintf(fo, "%zu,%s,%.3f,%.4f,%d,%d,%d,%.1f,%.3f,%.3f,%.1f,%.1f,%.1f,%d,%d,%d,%d,%d,%.1f,%.4f,%.4f,%.4f,%.4f,%.4f,%d,%d,%d,%d,%d,%d,%.2f,%.1f,%.1f,%.2f,%.2f,%.3f\n",
                   c, ch.name, w.face_pk / 1e5, w.vmax, w.n475_ign, w.n456_ign, w.n475, w.tE2 * 1e3, w.raw_pk / 1e5, w.filt_pk / 1e5, w.t30f * 1e3,
                   w.c30f * 1e3, end_rel, w.fw[0], w.fw[1], w.fw[2], w.fw[3], w.fw[4], w.tfw0 * 1e3, w.cmpv[0], w.cmpv[1], w.cmpv[2], w.cmpv[3],
                   w.cmpv[4], w.cnom[0], w.clo[0], w.clo[1], w.clo[2], w.clo[3], w.clo[4], w.tcmp0 * 1e3, w.t45c * 1e3, w.t45t * 1e3,
                   headAbove(head[c], 45.0, true) * 1e3, headAbove(head[c], 45.0, false) * 1e3, *std::max_element(head[c].begin(), head[c].end()));
    }
    std::fflush(fo);
    std::printf("chain %s done (%ld runs so far)\n", ch.name, nrun);
  }
  std::fclose(fo);
  std::printf("runs %ld -> %s\n", nrun, argv[2]);
  return 0;
}
