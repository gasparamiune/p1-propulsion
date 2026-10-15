// ARGOS engine SIL - ignition-lift derivation in the SIL plant cold-flow model (v1, 2026-10-13; from scratch/flow_recon).
// LEAD 2026-10-13 (CHANGELOG): the ignition lift is defined by cold flow, <= 37.4 g/s at the A1 relight state and <= 37.1 g/s at 20 C,
// calibrated at CF-3 as a lift-vs-T_tank table. Until CF-3, the firmware default (config.h kIgnLiftTab_m, flat 0.2039 mm) comes from this
// program: the lift that gives 37.1 g/s at 20 C, Pc 1.0 bar abs (chamber vented at the lift; the 1.66 bar row shows the sensitivity).
// Model (plant.h, same as Combustion's cold-flow basis): Dyer k-blend mass flux dyerG2 at a SATURATED inlet with no line loss (upper bound
// of the flow), discharge coefficient tab::k_Cd (Cd 0.70 ASSUMED, Combustion), frustum curtain area pintleArea(x). ESTIMATE: not a
// measurement; the real table comes from CF-3 (bench plan), with the N2O temperature recorded at every point.
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
static double tsatFromP(double p) { double lo = 250, hi = 309; for (int i = 0; i < 80; ++i) { const double m = 0.5 * (lo + hi); (satP(m) < p ? lo : hi) = m; } return 0.5 * (lo + hi); }

int main(int argc, char** argv) {
  const std::string out = argc > 1 ? argv[1] : "../results/ignition_lift_v1.json";
  // inputs (tags in the JSON)
  const double m20 = 37.1e-3, mA1 = 37.4e-3;      // [LEAD 2026-10-13] cold-flow limits at 20 C and at the A1 relight state
  const double T20 = 293.15, TA1 = 286.7;          // [DESIGN 20 C] / [COMB A1_relight state, relight_window_rule_v2p4 / start_latency_v2p4]
  const double x_cmb_A1 = 0.2191572e-3, x_cmb_20 = 0.20589804e-3;   // [COMB] Combustion's 12.5 % lifts at those states (flow reconciliation)
  const double x_v27 = 0.301e-3;                   // [COMB v2.1] 20 % ignition lift used by firmware v2.5-v2.7
  FILE* f = std::fopen(out.c_str(), "w");
  if (!f) { std::perror("open"); return 1; }
  std::fprintf(f, "{\n \"id\": \"ignition_lift\", \"version\": \"v1\", \"date\": \"2026-10-13\", \"script\": \"firmware/sil/ign_lift_cal.cpp\",\n");
  std::fprintf(f, " \"model\": \"SIL plant cold flow: k_Cd x pintleArea(x) x dyerG2(T, Psat(T), Pc); saturated inlet, no line loss (upper bound); ESTIMATE\",\n");
  std::fprintf(f, " \"k_Cd\": %.4f,\n", tab::k_Cd);
  std::fprintf(f, " \"inputs\": {\"m_20C_max_kg_s\": [%.4f, \"LEAD 2026-10-13 CHANGELOG\"], \"m_A1_max_kg_s\": [%.4f, \"LEAD 2026-10-13 CHANGELOG\"], "
                  "\"T_20C_K\": [%.2f, \"DESIGN\"], \"T_A1_K\": [%.2f, \"COMB A1 relight state\"]},\n", m20, mA1, T20, TA1);
  std::fprintf(f, " \"lift_for_limit_m\": [\n");
  bool first = true;
  for (double pc : {1.0e5, 1.66e5}) {
    const double x20 = liftFor(T20, m20, pc), xa1 = liftFor(TA1, mA1, pc);
    std::fprintf(f, "%s  {\"Pc_abs_Pa\": %.0f, \"lift_37p1_at_20C_m\": %.4e, \"flow_A1_at_it_kg_s\": %.5f, \"lift_37p4_at_A1_m\": %.4e, \"flow_20C_at_it_kg_s\": %.5f}",
                 first ? "" : ",\n", pc, x20, flow(TA1, x20, pc), xa1, flow(T20, xa1, pc));
    first = false;
  }
  std::fprintf(f, "\n ],\n");
  const double x_def = ecu::cfg::kIgnLiftTab_m[0];
  std::fprintf(f, " \"firmware_default_m\": [%.4e, \"config.h kIgnLiftTab_m (both rows), from lift_37p1_at_20C at Pc 1.0 bar\"],\n", x_def);
  std::fprintf(f, " \"default_flow\": {\"at_20C_Pc1_kg_s\": %.5f, \"at_A1_Pc1_kg_s\": %.5f, \"at_20C_Pc1p66_kg_s\": %.5f},\n",
               flow(T20, x_def, 1.0e5), flow(TA1, x_def, 1.0e5), flow(T20, x_def, 1.66e5));
  std::fprintf(f, " \"flow_vs_T_at_default_lift\": [");
  first = true;
  for (double T : {273.15, 283.15, 288.15, 293.15, 298.15, 303.15, 308.15}) {
    std::fprintf(f, "%s{\"T_K\": %.2f, \"Psat_Pa\": %.0f, \"flow_kg_s\": %.5f}", first ? "" : ", ", T, satP(T), flow(T, x_def, 1.0e5));
    first = false;
  }
  std::fprintf(f, "],\n");
  // what a temperature-dependent table holding 37.1 g/s at every T_tank would contain (the LEAD default is flat; CF-3 decides)
  std::fprintf(f, " \"lift_for_37p1_vs_T_m\": [");
  first = true;
  for (double T : {273.15, 283.15, 293.15, 303.15, 308.15}) {   // below the N2O critical point (309.5 K)
    std::fprintf(f, "%s{\"T_K\": %.2f, \"lift_m\": %.4e}", first ? "" : ", ", T, liftFor(T, m20, 1.0e5));
    first = false;
  }
  std::fprintf(f, "],\n");
  std::fprintf(f, " \"reconciliation\": {\"comb_12p5pct_A1_lift_m\": %.4e, \"flow_at_it_A1_kg_s\": %.5f, \"comb_12p5pct_20C_lift_m\": %.4e, \"flow_at_it_20C_kg_s\": %.5f, "
                  "\"v2p7_lift_m\": %.4e, \"flow_at_v2p7_lift_20C_Pc1p66_kg_s\": %.5f, \"T_tank_at_48p32bar_K\": %.2f, "
                  "\"note\": \"the 51.6 g/s that Combustion read from the SIL came from the 0.301 mm (20 %%) lift of firmware v2.5-v2.7, not from a different flow model\"},\n",
               x_cmb_A1, flow(TA1, x_cmb_A1, 1.0e5), x_cmb_20, flow(T20, x_cmb_20, 1.0e5), x_v27, flow(T20, x_v27, 1.66e5), tsatFromP(48.32e5));
  std::fprintf(f, " \"limitations\": \"saturated inlet with no line loss (real flow lower); Cd 0.70 ASSUMED; area law and Dyer blend are models; the flow rises with T_tank at a fixed lift, so CF-3 measures a lift-vs-T_tank table\"\n}\n");
  std::fclose(f);
  std::printf("ignition lift v1: default %.4f mm -> %.2f g/s at 20 C, %.2f g/s at A1 (Pc 1 bar); written %s\n", x_def * 1e3, flow(T20, x_def, 1e5) * 1e3,
              flow(TA1, x_def, 1e5) * 1e3, out.c_str());
  return 0;
}
