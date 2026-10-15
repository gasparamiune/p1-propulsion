// Line-priming gas-pocket sweep (v1 2026-10-12): peak gas temperature in the SIL plant's adiabatic priming model versus
// pintle bleed lift and main-valve opening ramp. Indicative only (no wall heat transfer, no liquid inertia or flashing):
// it shows how much gas the bleed can vent before the liquid compresses it, not the real line temperature.
// Build: g++ -std=c++17 -O2 -Isrc/core -Isil sil/prime_sweep.cpp sil/plant.cpp -o build/prime_sweep
// Usage: prime_sweep [T_tank_C] -> JSON on stdout
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include "plant.h"
int main(int argc, char** argv) {
  const double Tc = argc > 1 ? std::atof(argv[1]) : 20.0;
  const double lifts_mm[] = {0.0, 0.05, 0.10, 0.20, 0.50, 1.00};
  const double ramps_s[] = {0.05, 0.35, 1.0, 3.0};
  std::printf("{\"tool\": \"sil/prime_sweep.cpp v1\", \"T_tank_C\": %.1f, \"model\": \"adiabatic gas pocket, Cv 3 ball valve (circle-overlap area law), "
              "V_line 19 cm3, air at 1 bar 293 K, opener ramp to full open (40 deg of a linear 45 deg ramp)\", \"rows\": [", Tc);
  bool first = true;
  for (double lm : lifts_mm) for (double rs : ramps_s) {
    sil::EngineParams p; p.T_tank0 = 273.15 + Tc;
    sil::EnginePlant e(p);
    const double dt = 25e-6, th_full = 45.0 * M_PI / 180;
    double t = 0, t_fill = NAN;
    while (t < rs + 1.0) {
      const double th = th_full * std::min(1.0, t / rs);
      e.step(dt, lm * 1e-3, true, th, false, false, false);
      if (std::isnan(t_fill) && !e.gas_active && e.fill >= 1.0) t_fill = t;
      t += dt;
      if (!std::isnan(t_fill) && t > t_fill + 0.01) break;
    }
    if (std::isnan(t_fill)) t_fill = -1.0;   // -1 = gas never expelled (dead end)
    std::printf("%s{\"bleed_lift_mm\": %.2f, \"bleed_area_mm2\": %.3f, \"ramp_s\": %.2f, \"gas_T_max_K\": %.0f, \"gas_p_max_bar\": %.2f, \"t_gas_gone_s\": %.4f, "
                "\"fill_end\": %.4f, \"dpfeed_dt_max_bar_per_s\": %.0f}",
                first ? "" : ", ", lm, sil::pintleArea(lm * 1e-3) * 1e6, rs, e.gas_T_max, e.gas_p_max / 1e5, t_fill, e.fill, e.dpfeed_dt_max / 1e5);
    first = false;
  }
  std::printf("]}\n");
  return 0;
}
