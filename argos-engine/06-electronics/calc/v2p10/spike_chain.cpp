// v2.10 item 1/2 evidence (Electronics, 2026-10-13): Combustion's late-light head-pressure traces (late_light_spike_v2p4.json 'traces',
// exported by extract_spike_traces.py) played through the SIL Pc measurement chain and the ECU's own filter:
//   head Pc -> SenseLine (sil/plant.cpp, SenseLineParams defaults, ASSUMED) -> transducer lag 0.9 ms (sim.h pc_tau) -> 4 kSPS ADC, 4:1
//   average, 0..4.95 V clamp (sim.cpp) -> 1 kHz raw reading -> ECU LowPass2 50 Hz (filters.h, cfg::kPcFilterFc_Hz) -> 30 bar abort
//   persistence (cfg::kPcOverPressureTime_s, Persist) ; comparator: transducer voltage -> RC 5.283 ms -> trip 0.5 + 4 x 31.47 bar g / FS
//   (nominal and low band edge, ovp_hw_params.h).
// Reports per trace (worst over 4 ADC phases): raw / filtered peak, time above 8 / 30 bar abs, max transducer voltage (4.75 V = the
// IGNITION HIGH over-range HARD_START, engine_ecu.cpp step()), 30 bar abort trip, comparator trip. SIM on ASSUMED inputs; not hardware.
// Usage: spike_chain <trace_dir> <n_traces> <out_json> [scale_trace_index scale_peak_bar]; env SPIKE_NO_LINE=1: no sense line
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include "config.h"
#include "filters.h"
#include "plant.h"
#include "ovp_hw_params.h"

struct Res { double raw_pk = 0, filt_pk = 0, xdcr_pk = 0, vmax = 0, t8r = 0, t8f = 0, t30r = 0, t30f = 0, cmp_v = 0; bool fw30 = false, cmp_nom = false, cmp_lo = false, hard475 = false; };

static Res run(const std::vector<double>& t, const std::vector<double>& p, double phase_s) {
  using namespace ecu;
  const double dtp = 25e-6, fs = sil::ovp::kPcFs_Pa, tau_x = 0.0009, tau_rc = sil::ovp::kTau_s;
  const double v_nom = 0.5 + 4.0 * sil::ovp::kTripPa_g / fs, v_lo = 0.5 + 4.0 * (sil::ovp::kTripPa_g - sil::ovp::kBandPa) / fs;
  sil::SenseLineParams sp; if (std::getenv("SPIKE_NO_LINE")) sp.enabled = false;   // sensitivity: head pressure at the transducer
  sil::SenseLine line(sp); line.init(p[0] * 1e5);
  LowPass2 lpf; lpf.setup(cfg::kPcFilterFc_Hz, cfg::kDt_s);
  Persist pers; Res r;
  double x2 = p[0] * 1e5, vf = 0.5 + 4.0 * (x2 - 101325.0) / fs, acc = 0; int nacc = 0;
  for (int k = 0; k < 400; ++k) lpf.step(static_cast<float>(p[0] * 1e5 - 101325.0));   // settle on the pre-light level
  const double pre = 0.05, t_end = t.back();
  double next_adc = -pre + phase_s, next_ms = -pre + phase_s + 1e-3;
  size_t j = 0;
  for (double ts = -pre; ts <= t_end; ts += dtp) {
    while (j + 1 < t.size() && t[j + 1] <= ts) ++j;
    double ph = p[0];
    if (ts >= t[0]) ph = (j + 1 < t.size()) ? p[j] + (p[j + 1] - p[j]) * (ts - t[j]) / (t[j + 1] - t[j]) : p.back();
    const double s1 = line.step(dtp, ph * 1e5);
    x2 += (s1 - x2) * dtp / tau_x;
    r.xdcr_pk = std::fmax(r.xdcr_pk, x2);
    const double v_sig = std::fmin(4.95, 0.5 + 4.0 * (x2 - 101325.0) / fs);
    vf += (v_sig - vf) * dtp / tau_rc; r.cmp_v = std::fmax(r.cmp_v, vf);
    if (vf > v_nom) r.cmp_nom = true;
    if (vf > v_lo) r.cmp_lo = true;
    if (ts >= next_adc) { acc += x2; ++nacc; next_adc += 0.00025; }
    if (ts >= next_ms) {
      next_ms += 1e-3;
      const double avg = nacc ? acc / nacc : x2; acc = 0; nacc = 0;
      const double v = std::fmin(4.95, std::fmax(0.0, 0.5 + 4.0 * (avg - 101325.0) / fs));
      const double raw_abs = (v - 0.5) / 4.0 * fs + 101325.0;
      const float filt_abs = lpf.step(static_cast<float>(raw_abs - 101325.0)) + 101325.0f;
      if (ts < 0.0) continue;
      r.vmax = std::fmax(r.vmax, v); if (v >= cfg::kPcSensorMax_V) r.hard475 = true;
      r.raw_pk = std::fmax(r.raw_pk, raw_abs); r.filt_pk = std::fmax(r.filt_pk, static_cast<double>(filt_abs));
      if (raw_abs > 8.0e5) r.t8r += 1e-3;
      if (filt_abs > 8.0e5f) r.t8f += 1e-3;
      if (raw_abs > cfg::kPcOverPressureAbs_Pa) r.t30r += 1e-3;
      if (filt_abs > cfg::kPcOverPressureAbs_Pa) r.t30f += 1e-3;
      if (pers.step(filt_abs > cfg::kPcOverPressureAbs_Pa, cfg::kPcOverPressureTime_s, cfg::kDt_s)) r.fw30 = true;
    }
  }
  return r;
}

int main(int argc, char** argv) {
  if (argc < 4) { std::fprintf(stderr, "usage: spike_chain <trace_dir> <n> <out_json> [scale_idx scale_peak_bar]\n"); return 1; }
  const std::string dir = argv[1]; const int n = std::atoi(argv[2]);
  const int sidx = argc > 5 ? std::atoi(argv[4]) : -1; const double speak = argc > 5 ? std::atof(argv[5]) : 0.0;
  std::ostringstream js; js << "{\"id\": \"spike_chain_v2p10\", \"cases\": [\n";
  int ncase = 0;
  for (int i = 0; i < n + (sidx >= 0 ? 1 : 0); ++i) {
    const int ti = i < n ? i : sidx;
    std::ifstream f(dir + "/trace" + std::to_string(ti) + ".csv"); std::string line; std::getline(f, line);
    std::vector<double> t, p; double a, b; char c;
    while (f >> a >> c >> b) { t.push_back(a); p.push_back(b); }
    if (i >= n) {   // scaled copy: excess above the first sample scaled so the head peak = speak (bounding the 43.7 bar pad case)
      double pm = 0; for (double v : p) pm = std::fmax(pm, v);
      const double k = (speak - p[0]) / (pm - p[0]); for (double& v : p) v = p[0] + (v - p[0]) * k;
    }
    Res w; bool first = true;
    for (int q = 0; q < 4; ++q) {
      const Res r = run(t, p, q * 0.00025);
      if (first) { w = r; first = false; continue; }
      w.raw_pk = std::fmax(w.raw_pk, r.raw_pk); w.filt_pk = std::fmax(w.filt_pk, r.filt_pk); w.xdcr_pk = std::fmax(w.xdcr_pk, r.xdcr_pk);
      w.vmax = std::fmax(w.vmax, r.vmax); w.t8r = std::fmax(w.t8r, r.t8r); w.t8f = std::fmax(w.t8f, r.t8f); w.t30r = std::fmax(w.t30r, r.t30r);
      w.t30f = std::fmax(w.t30f, r.t30f); w.cmp_v = std::fmax(w.cmp_v, r.cmp_v); w.fw30 |= r.fw30; w.cmp_nom |= r.cmp_nom; w.cmp_lo |= r.cmp_lo;
      w.hard475 |= r.hard475;
    }
    double ph = 0; for (double v : p) ph = std::fmax(ph, v);
    std::printf("case %d (trace%d%s): head %.2f | xdcr %.2f | raw %.2f | filt %.2f bar abs | t8 raw %.0f filt %.0f ms | t30 raw %.0f filt %.0f ms | "
                "Vmax %.3f V (4.75 V HARD_START %s) | fw 30 bar abort %s | comparator V %.3f (trip nom %s, low band %s)\n",
                ncase, ti, i >= n ? " scaled" : "", ph, w.xdcr_pk / 1e5, w.raw_pk / 1e5, w.filt_pk / 1e5, w.t8r * 1e3, w.t8f * 1e3, w.t30r * 1e3,
                w.t30f * 1e3, w.vmax, w.hard475 ? "YES" : "no", w.fw30 ? "TRIPS" : "no", w.cmp_v, w.cmp_nom ? "YES" : "no", w.cmp_lo ? "YES" : "no");
    char b2[900];
    std::snprintf(b2, sizeof b2, "%s{\"case\": %d, \"trace\": %d, \"scaled_to_bar\": %s, \"head_peak_bar\": %.3f, \"xdcr_peak_bar\": %.3f, \"raw_peak_bar\": %.3f, "
                  "\"filt_peak_bar\": %.3f, \"t8_raw_ms\": %.0f, \"t8_filt_ms\": %.0f, \"t30_raw_ms\": %.0f, \"t30_filt_ms\": %.0f, \"vmax_V\": %.4f, "
                  "\"hard_start_4p75V\": %s, \"fw_30bar_abort\": %s, \"comparator_rc_V_max\": %.4f, \"comparator_trip_nominal\": %s, \"comparator_trip_low_band\": %s}",
                  ncase ? ",\n" : "", ncase, ti, i >= n ? std::to_string(speak).c_str() : "null", ph, w.xdcr_pk / 1e5, w.raw_pk / 1e5, w.filt_pk / 1e5,
                  w.t8r * 1e3, w.t8f * 1e3, w.t30r * 1e3, w.t30f * 1e3, w.vmax, w.hard475 ? "true" : "false", w.fw30 ? "true" : "false", w.cmp_v,
                  w.cmp_nom ? "true" : "false", w.cmp_lo ? "true" : "false");
    js << b2; ++ncase;
  }
  js << "\n], \"chain\": \"SenseLine defaults (L 0.30 m, ID 1.59 mm, ASSUMED) + 0.9 ms transducer + 4:1 avg + LowPass2 50 Hz + Persist 3 ms; comparator RC 5.283 ms\", "
        "\"phases\": \"worst of 4 ADC phases (0, 0.25, 0.5, 0.75 ms)\", \"tags\": \"SIM on COMB SIM traces (ASSUMED inputs); not hardware validation\"}\n";
  std::ofstream(argv[3]) << js.str();
  return 0;
}
