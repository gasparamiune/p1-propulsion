// Frequency response of the SIL Pc sense-line model (plant.cpp SenseLine). v1 2026-10-12. Intended for comparison with an analytic
// Bergh-Tijdeman solution; that comparison script (planned as calc/pc_sense_line_v1.py) is NOT written (open item, 2026-10-13 note).
// Build: g++ -std=c++17 -O2 -Isrc/core -Isil sil/senseline_fr.cpp sil/plant.cpp -o build/senseline_fr
// Usage: senseline_fr L ID V_end_cm3 T Pc_bar  -> JSON lines {f, gain, phase_deg}
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include "plant.h"

int main(int argc, char** argv) {
  sil::SenseLineParams p;
  if (argc > 5) { p.L = std::atof(argv[1]); p.ID = std::atof(argv[2]); p.V_end = std::atof(argv[3]) * 1e-6; p.T = std::atof(argv[4]); }
  const double Pc = (argc > 5 ? std::atof(argv[5]) : 25.0) * 1e5;
  const double A = 0.01 * Pc;                                  // 1 % ripple: linear regime
  const double dt = 25e-6;                                     // SIL plant step
  std::printf("{\"L\": %g, \"ID\": %g, \"V_end_cm3\": %g, \"T\": %g, \"Pc_bar\": %g, \"c\": %.1f, \"points\": [", p.L, p.ID, p.V_end * 1e6, p.T, Pc / 1e5,
              sil::SenseLine(p).c());
  const double fs[] = {5, 10, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 230, 260, 300, 350, 400, 500, 600, 800, 1000};
  bool first = true;
  for (double f : fs) {
    sil::SenseLine s(p);
    s.init(Pc);
    const double T_settle = std::max(0.3, 40.0 / f), T_meas = std::max(0.2, 20.0 / f);
    double t = 0, sc = 0, ss = 0; int n = 0;
    while (t < T_settle + T_meas) {
      const double pin = Pc + A * std::sin(2 * M_PI * f * t);
      const double pout = s.step(dt, pin);
      if (t >= T_settle) { sc += (pout - Pc) * std::cos(2 * M_PI * f * t); ss += (pout - Pc) * std::sin(2 * M_PI * f * t); ++n; }
      t += dt;
    }
    const double amp = 2 * std::sqrt(sc * sc + ss * ss) / n, ph = std::atan2(sc, ss) * 180 / M_PI;
    std::printf("%s{\"f\": %g, \"gain\": %.4f, \"phase_deg\": %.2f}", first ? "" : ", ", f, amp / A, ph);
    first = false;
  }
  std::printf("]}\n");
  return 0;
}
