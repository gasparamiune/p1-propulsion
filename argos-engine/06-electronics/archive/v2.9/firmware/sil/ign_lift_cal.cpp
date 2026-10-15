// ARGOS engine SIL - ignition-lift table in the SIL plant cold-flow model (v2, 2026-10-13; v1 archived in tools/archive/ign_lift_cal_v1.cpp,
// its output results/ignition_lift_v1.json kept as evidence of the flat 0.2039 mm default).
// LEAD 2026-10-13 (CHANGELOG line 134, adopting Combustion ignition_detect_v2p4.json a34b05c90499badb part H): "CF-3 temperature-dependent
// ignition-lift table (to 37.4 g/s, within the 26.6 g / 13.84 g inventory caps) to be implemented in firmware", replacing the flat
// 0.2039 mm (37.1 g/s at 20 C but only 35.0 g/s at the A1 relight state, 38.2 g/s at 24 C). Electronics reading of "to 37.4 g/s": the
// table holds the cold flow at 37.4 g/s at every tank temperature (the lift falls as T_tank rises), so no row exceeds 37.4 g/s; at 20 C
// this is +0.8 % over the earlier 37.1 g/s figure (Combustion's inventory check covers it; the lead may cap the warm rows at 37.1 g/s
// by editing them). The table rows below go into config.h kIgnLiftTab_m; this program recomputes them and checks the configured table.
// Model (plant.h, same basis as Combustion's cold flow): Dyer k-blend mass flux dyerG2 at a SATURATED inlet with no line loss (upper
// bound of the flow), discharge coefficient tab::k_Cd (Cd 0.70 ASSUMED, Combustion), frustum curtain area pintleArea(x). ESTIMATE, not a
// measurement: CF-3 (bench plan) measures the real lift-vs-T_tank table, with the N2O temperature recorded at every point.
// Usage: ign_lift_cal <out.json>
#include <cmath>
#include <cstdio>
#include <string>
#include "plant.h"
#include "plant_tables.h"
#include "config.h"
using namespace sil;

static double flow(double T, double x, double Pc) { return tab::k_Cd * pintleArea(x) * dyerG2(T, satP(T), Pc); }
static double liftFor(double T, double m, double Pc) {   // bisection on the monotonic lift -> flow law
  double lo = 0.0, hi = 0.6e-3;
  for (int i = 0; i < 80; ++i) { const double x = 0.5 * (lo + hi); (flow(T, x, Pc) < m ? lo : hi) = x; }
  return 0.5 * (lo + hi);
}

int main(int argc, char** argv) {
  const std::string out = argc > 1 ? argv[1] : "../results/ignition_lift_v2.json";
  const double m_tgt = 37.4e-3;        // [LEAD 2026-10-13 CHANGELOG line 134] cold-flow target of every row
  const double x_flat = 0.2039e-3;     // v2.8-v2.8.3 flat default (ignition_lift_v1.json), for comparison
  const double W_stand = ecu::cfg::kIgnWindowRelightStand_s, W_flight = ecu::cfg::kIgnWindowRelightLong_s;
  FILE* f = std::fopen(out.c_str(), "w");
  if (!f) { std::perror("open"); return 1; }
  std::fprintf(f, "{\n \"id\": \"ignition_lift\", \"version\": \"v2\", \"date\": \"2026-10-13\", \"script\": \"firmware/sil/ign_lift_cal.cpp\",\n");
  std::fprintf(f, " \"model\": \"SIL plant cold flow: k_Cd x pintleArea(x) x dyerG2(T, Psat(T), Pc); saturated inlet, no line loss (upper bound); ESTIMATE\",\n");
  std::fprintf(f, " \"k_Cd\": [%.4f, \"ASSUMED (Combustion Cd 0.70)\"],\n", tab::k_Cd);
  std::fprintf(f, " \"target_flow_kg_s\": [%.4f, \"LEAD 2026-10-13 CHANGELOG line 134 (CF-3 table to 37.4 g/s); Electronics reading: every row at 37.4 g/s\"],\n", m_tgt);
  // 1. the derived table (Pc 1.0 bar abs: chamber vented at the lift; 1.66 bar shows the back-pressure sensitivity)
  std::fprintf(f, " \"derived_rows\": [");
  bool first = true;
  for (double T : {273.15, 275.65, 278.15, 280.65, 283.15, 285.65, 286.7, 288.15, 290.65, 293.15, 295.65, 297.15, 298.15, 300.65, 303.15, 305.65, 308.15}) {
    std::fprintf(f, "%s\n  {\"T_K\": %.2f, \"Psat_Pa\": %.0f, \"lift_Pc1_m\": %.4e, \"lift_Pc1p66_m\": %.4e, \"flow_at_flat_0p2039mm_kg_s\": %.5f}",
                 first ? "" : ",", T, satP(T), liftFor(T, m_tgt, 1.0e5), liftFor(T, m_tgt, 1.66e5), flow(T, x_flat, 1.0e5));
    first = false;
  }
  std::fprintf(f, "\n ],\n");
  // 2. check of the table configured in config.h (rows, flow at each row, inventory over the windows at constant flow)
  std::fprintf(f, " \"configured_table\": {\"source\": \"config.h kIgnLiftT_K / kIgnLiftTab_m\", \"rows\": [");
  double fmax = 0.0, fmin = 1.0;
  for (int i = 0; i < ecu::cfg::kIgnLiftN; ++i) {
    const double T = ecu::cfg::kIgnLiftT_K[i], x = ecu::cfg::kIgnLiftTab_m[i], m = flow(T, x, 1.0e5);
    fmax = std::fmax(fmax, m); fmin = std::fmin(fmin, m);
    std::fprintf(f, "%s\n  {\"T_K\": %.2f, \"lift_m\": %.4e, \"flow_Pc1_kg_s\": %.5f, \"flow_Pc1p66_kg_s\": %.5f, \"inv_W%.2f_g\": %.2f, \"inv_W%.2f_g\": %.2f}",
                 i ? "," : "", T, x, m, flow(T, x, 1.66e5), W_stand, 1e3 * m * W_stand, W_flight, 1e3 * m * W_flight);
  }
  // between rows the firmware interpolates the lift linearly: worst flow between rows (fine T scan)
  double scan_max = 0.0, scan_T = 0.0;
  for (double T = ecu::cfg::kIgnLiftT_K[0]; T <= ecu::cfg::kIgnLiftT_K[ecu::cfg::kIgnLiftN - 1] + 1e-9; T += 0.05) {
    double x = ecu::cfg::kIgnLiftTab_m[ecu::cfg::kIgnLiftN - 1];
    for (int i = 1; i < ecu::cfg::kIgnLiftN; ++i)
      if (T <= ecu::cfg::kIgnLiftT_K[i]) {
        const double fr = (T - ecu::cfg::kIgnLiftT_K[i - 1]) / (ecu::cfg::kIgnLiftT_K[i] - ecu::cfg::kIgnLiftT_K[i - 1]);
        x = ecu::cfg::kIgnLiftTab_m[i - 1] + fr * (ecu::cfg::kIgnLiftTab_m[i] - ecu::cfg::kIgnLiftTab_m[i - 1]);
        break;
      }
    const double m = flow(T, x, 1.0e5);
    if (m > scan_max) { scan_max = m; scan_T = T; }
  }
  std::fprintf(f, "\n ], \"flow_min_kg_s\": %.5f, \"flow_max_kg_s\": %.5f, \"interpolated_flow_max_kg_s\": %.5f, \"interpolated_flow_max_at_T_K\": %.2f,\n"
                  "  \"inventory_tag\": \"constant-flow estimate (flow x W, no opening transient, no line loss); Combustion's inventory check (ignition_detect_v2p4 H, LEAD line 134) is the authority: 24.8 g at W 0.65 s, 13.45 g at 0.35 s against the 26.6 g flight / 13.84 g stand caps\"},\n",
               fmin, fmax, scan_max, scan_T);
  std::fprintf(f, " \"table_extent\": {\"below_first_row\": \"clamped to the first row\", \"above_last_row\": \"clamped to the last row\", \"T_tank_invalid\": \"smallest lift of the table (ignLiftTabMin)\"},\n");
  std::fprintf(f, " \"limitations\": \"saturated inlet with no line loss (real flow lower); Cd 0.70 ASSUMED; area law and Dyer blend are models; T_tank = Tsat(P_tank) at E0; CF-3 measures the real lift-vs-T_tank table\"\n}\n");
  std::fclose(f);
  std::printf("ignition lift v2: configured table flow %.2f-%.2f g/s at the rows, interpolated max %.2f g/s at %.2f K; written %s\n",
              fmin * 1e3, fmax * 1e3, scan_max * 1e3, scan_T, out.c_str());
  std::printf("  rows (config.h form):\n  T_K  {");
  for (double T : {273.15, 275.65, 278.15, 280.65, 283.15, 285.65, 286.7, 288.15, 290.65, 293.15, 295.65, 297.15, 298.15, 300.65, 303.15, 305.65, 308.15}) std::printf("%.2ff, ", T);
  std::printf("}\n  lift {");
  for (double T : {273.15, 275.65, 278.15, 280.65, 283.15, 285.65, 286.7, 288.15, 290.65, 293.15, 295.65, 297.15, 298.15, 300.65, 303.15, 305.65, 308.15}) std::printf("%.5fe-3f, ", liftFor(T, m_tgt, 1.0e5) * 1e3);
  std::printf("}\n");
  return 0;
}
