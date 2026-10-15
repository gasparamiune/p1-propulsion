// LEAD CHANGELOG 194 (7) evidence (Electronics, 2026-10-13, firmware v2.10): Combustion's FA-1 relight pressure histories (fa1_envelope_v2p4a,
// 896 cases, exported by calc/v2p10/fa1_overrange.py extract) played through the SIL Pc measurement chain with the 070BG output limited at a
// swept saturation level v_sat (the transducer output above full scale is NOT stated in the TE M3200 datasheet: MISSING).
// Adapted from calc/v2p10/spike_chain.cpp (that file is left as published). Differences: the transducer output is limited per instant
// (before the ADC; sim.cpp limits the 1 kHz average at 4.95 V, which over-reads above full scale), the ADC range is 4.99 V at PC_SIG
// (DERIVED: 1.2 V FS / 0.2404 divider), the E2 relative light rule is emulated so each over-range reading is placed before or after E2,
// and the persistence is cfg::kPcOverPressureTime_s (5 ms, LEAD RE-20; spike_chain's JSON text "3 ms" dates from before RE-20).
//   head (or aft) P -> SenseLine (sil/plant.cpp defaults, ASSUMED; or off) -> port pressure (proof check) -> 0.9 ms lag -> v = 0.5 + 4 p_g/FS,
//   limited at v_sat -> (a) comparator RC 5.283 ms, trip 2.298 / 2.208 V; (b) ADC 4 kSPS, 4.99 V, 4:1 average -> 1 kHz reading ->
//   4.75 V over-range check, LowPass2 50 Hz -> 30 bar abs, Persist 5 ms; E2 = 10 ticks of filtered AND raw rise >= 0.8 bar over the
//   pre-light reference with both >= 1.8 bar abs.
// Transducer lag tau_x: 0.9 ms (SIL; 10-90 % rise 2.0 ms = the DATASHEET bound '< 2 ms', so the slowest response the datasheet
// allows) and 0.1 ms (a faster unit; the datasheet gives only the bound).
// Sensitivity columns (not proposals): comparator RC 10 / 20 ms at the low band edge; filtered persistence 10 / 15 ms.
// Env FA1_TRACE=<case>,<head|aft>,<on|off>,<vsat|none>,<tau_x ms>,<file>: also writes the 0.1 ms trace of that case (ADC phase 0).
// The histories are open loop: a trip does not change them; every check is reported as if the others had not acted.
// Usage: fa1_overrange_chain <hist_head.txt> <hist_aft.txt> <out_csv>. SIM on COMB SIM inputs; not hardware validation.
#include <cmath>
#include <cstdio>
#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>
#include "config.h"
#include "filters.h"
#include "plant.h"
#include "ovp_hw_params.h"

namespace {
constexpr double kPamb = 101325.0, kAdcMax_V = 4.99, kNone = std::numeric_limits<double>::infinity();

struct Res {
  double port_pk = 0, port_min = 1e30, vmax = 0, raw_pk = 0, filt_pk = 0, t30f = 0, cmp_v = 0;
  double t475 = -1, tE2 = -1, tfw = -1, tcmp = -1;
  int n475 = 0, n475_ign = 0;
  bool fw30 = false, cmp_nom = false, cmp_lo = false;
  bool cmp_lo_t10 = false, cmp_lo_t20 = false, fw30_p10 = false, fw30_p15 = false;   // sensitivities
};

Res run(const std::vector<double>& p, double phase_s, bool line_on, double vsat, double tau_x, std::FILE* tr = nullptr) {
  using namespace ecu;
  const double dtp = 25e-6, fs = sil::ovp::kPcFs_Pa, tau_rc = sil::ovp::kTau_s, dgrid = 1e-4;
  const double v_nom = 0.5 + 4.0 * sil::ovp::kTripPa_g / fs, v_lo = 0.5 + 4.0 * (sil::ovp::kTripPa_g - sil::ovp::kBandPa) / fs;
  sil::SenseLineParams sp; sp.enabled = line_on;
  sil::SenseLine line(sp); line.init(p[0] * 1e5);
  LowPass2 lpf; lpf.setup(cfg::kPcFilterFc_Hz, cfg::kDt_s);
  for (int k = 0; k < 400; ++k) lpf.step(static_cast<float>(p[0] * 1e5 - kPamb));   // settled on the pre-light level
  Persist pers, pers10, pers15; Res r;
  auto volt = [&](double pa) { return std::fmax(0.0, std::fmin(vsat, 0.5 + 4.0 * (pa - kPamb) / fs)); };
  double x2 = p[0] * 1e5, vc = volt(x2), vc10 = vc, vc20 = vc, acc = 0, ref_f = 0, ref_r = 0; int nacc = 0, nref = 0, ign_n = 0;
  double last_v = 0, last_filt = 0; double next_tr = 0.0;
  const double pre = 0.05, t_hist = dgrid * (p.size() - 1), t_end = 0.100;
  double next_adc = -pre + phase_s, next_ms = -pre + phase_s + 1e-3;
  bool lit = false;
  for (double ts = -pre; ts <= t_end; ts += dtp) {
    double ph = p[0];
    if (ts >= t_hist) ph = p.back();
    else if (ts >= 0.0) { const size_t j = std::min(p.size() - 2, static_cast<size_t>(ts / dgrid)); const double f = std::fmin(1.0, ts / dgrid - j); ph = p[j] + (p[j + 1] - p[j]) * f; }
    const double s1 = line.step(dtp, ph * 1e5);
    if (ts >= 0.0) { r.port_pk = std::fmax(r.port_pk, s1); r.port_min = std::fmin(r.port_min, s1); }
    x2 += (s1 - x2) * std::fmin(1.0, dtp / tau_x);
    const double v_sig = volt(x2);                                        // transducer output (limited at v_sat)
    vc += (v_sig - vc) * dtp / tau_rc;
    vc10 += (v_sig - vc10) * dtp / 0.010; vc20 += (v_sig - vc20) * dtp / 0.020;
    if (ts >= 0.0) {
      r.cmp_v = std::fmax(r.cmp_v, vc);
      if (vc > v_lo) { r.cmp_lo = true; }
      if (vc > v_nom && !r.cmp_nom) { r.cmp_nom = true; r.tcmp = ts; }
      if (vc10 > v_lo) r.cmp_lo_t10 = true;
      if (vc20 > v_lo) r.cmp_lo_t20 = true;
    }
    if (tr && ts >= next_tr - 1e-9 && ts <= 0.030) {
      next_tr += 1e-4;
      std::fprintf(tr, "%.4f,%.3f,%.3f,%.3f,%.4f,%.4f,%.4f,%.3f\n", ts * 1e3, ph, s1 / 1e5, x2 / 1e5, v_sig, vc, last_v, last_filt);
    }
    if (ts >= next_adc) { acc += std::isinf(vsat) ? v_sig : std::fmin(kAdcMax_V, v_sig); ++nacc; next_adc += 0.00025; }
    if (ts >= next_ms) {
      next_ms += 1e-3;
      const double v = nacc ? acc / nacc : v_sig; acc = 0; nacc = 0;            // 1 kHz reading (pc_raw_V)
      const double raw_g = (v - 0.5) / 4.0 * fs, raw_abs = raw_g + kPamb;
      const float filt_g = lpf.step(static_cast<float>(raw_g));
      const double filt_abs = static_cast<double>(filt_g) + kPamb;
      if (ts < 0.0) {                                                         // reference: the last 20 ticks before the light
        if (ts >= -0.0205) { ref_f += filt_g; ref_r += raw_g; ++nref; }
        continue;
      }
      const double rf = nref ? ref_f / nref : 0.0, rr = nref ? ref_r / nref : 0.0;
      if (!lit) {
        const bool ok = (filt_g - rf) >= cfg::kIgnRise_Pa && (raw_g - rr) >= cfg::kIgnRise_Pa && filt_abs >= cfg::kIgnFloorAbs_Pa &&
                        raw_abs >= cfg::kIgnFloorAbs_Pa;
        ign_n = ok ? ign_n + 1 : 0;
      }
      const bool hi = v >= cfg::kPcSensorMax_V;
      if (hi) { ++r.n475; if (!lit) ++r.n475_ign; if (r.t475 < 0) r.t475 = ts; }   // a reading on the E2 tick is still in IGNITION
      if (!lit && ign_n >= cfg::kIgnConfirmRelN) { lit = true; r.tE2 = ts; }
      r.vmax = std::fmax(r.vmax, v);
      r.raw_pk = std::fmax(r.raw_pk, raw_abs); r.filt_pk = std::fmax(r.filt_pk, filt_abs);
      if (filt_abs > cfg::kPcOverPressureAbs_Pa) r.t30f += 1e-3;
      if (pers.step(filt_abs > cfg::kPcOverPressureAbs_Pa, cfg::kPcOverPressureTime_s, cfg::kDt_s) && !r.fw30) { r.fw30 = true; r.tfw = ts; }
      if (pers10.step(filt_abs > cfg::kPcOverPressureAbs_Pa, 0.010f, cfg::kDt_s)) r.fw30_p10 = true;
      if (pers15.step(filt_abs > cfg::kPcOverPressureAbs_Pa, 0.015f, cfg::kDt_s)) r.fw30_p15 = true;
      last_v = v; last_filt = filt_abs / 1e5;
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
}  // namespace

int main(int argc, char** argv) {
  if (argc < 4) { std::fprintf(stderr, "usage: fa1_overrange_chain <hist_head.txt> <hist_aft.txt> <out_csv>\n"); return 1; }
  const auto head = load(argv[1]), aft = load(argv[2]);
  if (const char* e = std::getenv("FA1_TRACE")) {                      // one trace, then exit
    char nd[8] = {0}, ln[8] = {0}, vs[16] = {0}, fn[512] = {0}; int c = -1; double tx = 0.9;
    if (std::sscanf(e, "%d,%7[^,],%7[^,],%15[^,],%lf,%511s", &c, nd, ln, vs, &tx, fn) != 6 || c < 0 || c >= static_cast<int>(head.size())) {
      std::fprintf(stderr, "bad FA1_TRACE\n"); return 1;
    }
    std::FILE* tr = std::fopen(fn, "w");
    std::fprintf(tr, "t_ms,P_node_bar,P_port_bar,P_xdcr_bar,v_sig_V,cmp_rc_V,reading_V_last,filt_bar_last\n");
    const Res r = run(std::string(nd) == "aft" ? aft[c] : head[c], 0.0, std::string(ln) == "on",
                      std::string(vs) == "none" ? kNone : std::atof(vs), tx * 1e-3, tr);
    std::fclose(tr);
    std::printf("trace case %d %s line %s vsat %s: port pk %.2f bar, vmax %.3f V, t475 %.1f ms, tE2 %.1f ms, filt pk %.2f, fw30 %d (%.1f ms), "
                "cmp %.3f V nom %d (%.2f ms) low %d\n", c, nd, ln, vs, r.port_pk / 1e5, r.vmax, r.t475 * 1e3, r.tE2 * 1e3, r.filt_pk / 1e5,
                r.fw30, r.tfw * 1e3, r.cmp_v, r.cmp_nom, r.tcmp * 1e3, r.cmp_lo);
    return 0;
  }
  std::FILE* fo = std::fopen(argv[3], "w");
  std::fprintf(fo, "case,node,line,tau_x_ms,vsat,port_pk_bar,vmax_V,hi475,t475_ms,n475,n475_ign,tE2_ms,raw_pk_bar,filt_pk_bar,t30f_ms,fw30,t_fw30_ms,"
                   "cmp_vmax,cmp_nom,cmp_lo,t_cmp_ms,cmp_lo_t10,cmp_lo_t20,fw30_p10,fw30_p15,port_min_bar\n");
  const double vsats[4] = {4.95, 4.74, 4.50, kNone};
  const char* vname[4] = {"4.95", "4.74", "4.50", "none"};
  long nrun = 0;
  struct Cfg { int node, ln; double tau; const char* tname; };
  const Cfg cfgs[4] = {{0, 0, 0.0009, "0.9"}, {0, 1, 0.0009, "0.9"}, {0, 1, 0.0001, "0.1"}, {1, 0, 0.0009, "0.9"}};   // aft: tap sensitivity
  for (const Cfg& g : cfgs) {
    const int node = g.node, ln = g.ln;
    const auto& H = node == 0 ? head : aft;
    {
      for (int q = 0; q < 4; ++q) {
        for (size_t c = 0; c < H.size(); ++c) {
          Res w; bool first = true;
          for (int ph = 0; ph < 4; ++ph) {
            const Res r = run(H[c], ph * 0.00025, ln == 0, vsats[q], g.tau); ++nrun;
            if (first) { w = r; first = false; continue; }
            w.port_pk = std::fmax(w.port_pk, r.port_pk); w.port_min = std::fmin(w.port_min, r.port_min); w.vmax = std::fmax(w.vmax, r.vmax); w.raw_pk = std::fmax(w.raw_pk, r.raw_pk);
            w.filt_pk = std::fmax(w.filt_pk, r.filt_pk); w.t30f = std::fmax(w.t30f, r.t30f); w.cmp_v = std::fmax(w.cmp_v, r.cmp_v);
            w.t475 = tmin(w.t475, r.t475); w.tE2 = tmin(w.tE2, r.tE2); w.tfw = tmin(w.tfw, r.tfw); w.tcmp = tmin(w.tcmp, r.tcmp);
            w.n475 = std::max(w.n475, r.n475); w.n475_ign = std::max(w.n475_ign, r.n475_ign);
            w.fw30 |= r.fw30; w.cmp_nom |= r.cmp_nom; w.cmp_lo |= r.cmp_lo;
            w.cmp_lo_t10 |= r.cmp_lo_t10; w.cmp_lo_t20 |= r.cmp_lo_t20; w.fw30_p10 |= r.fw30_p10; w.fw30_p15 |= r.fw30_p15;
          }
          std::fprintf(fo, "%zu,%s,%s,%s,%s,%.4f,%.4f,%d,%.2f,%d,%d,%.2f,%.4f,%.4f,%.1f,%d,%.2f,%.4f,%d,%d,%.3f,%d,%d,%d,%d,%.4f\n", c, node ? "aft" : "head",
                       ln ? "off" : "on", g.tname, vname[q], w.port_pk / 1e5, w.vmax, w.n475 > 0, w.t475 * 1e3, w.n475, w.n475_ign, w.tE2 * 1e3,
                       w.raw_pk / 1e5, w.filt_pk / 1e5, w.t30f * 1e3, w.fw30 ? 1 : 0, w.tfw * 1e3, w.cmp_v, w.cmp_nom ? 1 : 0,
                       w.cmp_lo ? 1 : 0, w.tcmp * 1e3, w.cmp_lo_t10, w.cmp_lo_t20, w.fw30_p10, w.fw30_p15, w.port_min / 1e5);
        }
      }
    }
  }
  std::fclose(fo);
  std::printf("runs %ld (cases x configurations x 4 ADC phases) -> %s\n", nrun, argv[3]);
  return 0;
}
