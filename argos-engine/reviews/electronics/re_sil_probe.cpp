// REV-ELEC-1 reviewer probe (independent of the author's scenario code; links the UNCHANGED v2.9 ECU core and SIL plant from a
// reviewer COPY of 06-electronics/firmware). Build: see re_build_probe.sh. Evidence class of every output: SIM (plant parameters are the
// author's ASSUMED/ESTIMATE values; hard_start_gain is a scenario parameter, not a physical datum). Nothing here is hardware evidence.
//
// Probe A  OI-A5-LATE boundary: pad first start (flight, W 0.40 s), torch-to-main delay swept, accumulation release fraction swept.
//          Records the abort cause, plant/filtered/transducer peaks, time the FILTERED Pc spends above 8.0 bar abs (A5) and above
//          30 bar abs (firmware OVP), and the unignited N2O per start.
// Probe B  BASE_AMB high-side fallback: constant offset that appears at the first IGNITION entry (after the OI-12 vented check; a
//          stand-in for a torch contribution to the pre-lift chamber pressure or a post-check shift), lit and unlit (main never lights).
// Probe C  A1 relight (direct path, flight W 0.65 s) with the same offset at the relight IGNITION entry, lit and unlit.
// Usage: re_sil_probe <A|B|C> <out.json>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include "sim.h"

using namespace sil;
using ecu::Cmd;
using ecu::State;

struct Res {
  int abort = 0; bool ran = false; double t_abort = NAN, e0 = NAN, e1 = NAN, lit = NAN, e2 = NAN;
  double pc_plant_max = 0, pc_filt_max = 0, pc_xdcr_max = 0, t_f_above8 = 0, t_f_above30 = 0, ox_unlit = NAN, p0 = NAN;
  int base_amb = 0, det = 0;
};

static Res scan(const Sim& s, size_t k_start) {
  Res m;
  if (k_start < s.ign_entry_t.size()) m.e0 = s.ign_entry_t[k_start];
  const double tn = k_start + 1 < s.ign_entry_t.size() ? s.ign_entry_t[k_start + 1] : 1e9;
  for (const auto& x : s.rec()) {
    if (x.abort && !m.abort) { m.abort = x.abort; m.t_abort = x.t; }
    if (std::isnan(m.e0) || x.t < m.e0 || x.t >= tn) continue;
    if (x.state == (int)State::RUN) { m.ran = true; if (std::isnan(m.e2)) m.e2 = x.t - m.e0; }
    if (std::isnan(m.e1) && x.ign_lift_t >= 0.0) m.e1 = x.ign_lift_t;
    if (std::isnan(m.lit) && x.ignited) m.lit = x.t - m.e0;
    if (x.state == (int)State::IGNITION || x.state == (int)State::RUN) {
      m.pc_plant_max = std::max(m.pc_plant_max, x.Pc);
      m.pc_filt_max = std::max(m.pc_filt_max, x.Pc_meas);
      m.pc_xdcr_max = std::max(m.pc_xdcr_max, x.Pc_xdcr);
      if (x.Pc_meas > 8.0e5) m.t_f_above8 += 1e-3;
      if (x.Pc_meas > 30.0e5) m.t_f_above30 += 1e-3;
      m.det |= x.ign_det;
      if (std::isnan(m.p0) && std::isfinite(x.ign_ref)) m.p0 = x.ign_ref;
    }
  }
  m.base_amb = (m.det & ecu::det::BASE_AMB) ? 1 : 0;
  m.ox_unlit = k_start < s.ox_unlit_starts.size() ? s.ox_unlit_starts[k_start] : NAN;
  if (std::isfinite(m.t_abort) && std::isfinite(m.e0)) m.t_abort -= m.e0;
  return m;
}

static std::string js(const char* name, double a, double b, const Res& m) {
  char buf[1400];
  std::snprintf(buf, sizeof buf,
                "{\"case\": \"%s\", \"p1\": %.4f, \"p2\": %.4f, \"abort\": \"%s\", \"entered_RUN\": %s, \"t_abort_from_E0_s\": %.4f, "
                "\"E1_s\": %.4f, \"plant_light_from_E0_s\": %.4f, \"E2_from_E0_s\": %.4f, \"plant_Pc_max_abs_bar\": %.3f, "
                "\"filtered_Pc_max_abs_bar\": %.3f, \"xdcr_Pc_max_abs_bar\": %.3f, \"filtered_above_8bar_ms\": %.0f, \"filtered_above_30bar_ms\": %.0f, "
                "\"ox_unignited_this_start_g\": %.2f, \"P0_gauge_bar\": %.3f, \"base_ambient\": %d}",
                name, a, b, ecu::abortName(static_cast<ecu::Abort>(m.abort)), m.ran ? "true" : "false", m.t_abort, m.e1, m.lit, m.e2,
                m.pc_plant_max / 1e5, m.pc_filt_max / 1e5, m.pc_xdcr_max / 1e5, m.t_f_above8 * 1e3, m.t_f_above30 * 1e3, m.ox_unlit * 1e3,
                m.p0 / 1e5, m.base_amb);
  std::string s(buf);
  for (const char* tok : {"-nan", "nan"}) for (size_t p = s.find(tok); p != std::string::npos; p = s.find(tok)) s.replace(p, std::strlen(tok), "null");
  return s;
}

int main(int argc, char** argv) {
  if (argc < 3) { std::printf("usage: re_sil_probe <A|B|C> <out.json>\n"); return 2; }
  const std::string which = argv[1];
  std::string arr = "[";
  int n = 0;
  auto add = [&](const std::string& j) { arr += (n++ ? ",\n " : "\n ") + j; };
  char nm[160];
  if (which == "A") {
    const double gains[4] = {0.0, 0.25, 0.5, 1.0};
    const double delays[15] = {0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.22, 0.25, 0.28, 0.30, 0.33, 0.36};
    for (double g : gains) for (double d : delays) {
      SimConfig c; c.seed = 7;
      Sim s(c);
      s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}};
      s.thrust_cmd = [](double) { return 300.0; };
      s.eng.P.ign_delay = d; s.eng.P.hard_start_gain = g;
      s.run(2.4);
      const Res m = scan(s, 0);
      std::snprintf(nm, sizeof nm, "pad_late_light_delay_%.2fs_gain_%.2f", d, g);
      add(js(nm, d, g, m));
      std::printf("A delay %.2f gain %.2f -> %-14s RUN %d plant max %6.2f filt max %6.2f xdcr %6.2f >8bar %3.0f ms >30bar %2.0f ms ox %.2f g light %.3f E2 %.3f\n",
                  d, g, ecu::abortName(static_cast<ecu::Abort>(m.abort)), m.ran, m.pc_plant_max / 1e5, m.pc_filt_max / 1e5, m.pc_xdcr_max / 1e5,
                  m.t_f_above8 * 1e3, m.t_f_above30 * 1e3, m.ox_unlit * 1e3, m.lit, m.e2);
    }
  } else if (which == "B") {
    const double offs[11] = {0.30e5, 0.39e5, 0.41e5, 0.45e5, 0.60e5, 0.69e5, 0.71e5, 0.75e5, 0.90e5, -0.45e5, -0.75e5};
    for (double r : offs) for (int u = 0; u < 2; ++u) {
      SimConfig c; c.seed = 97; c.pc_off = r; c.pc_off_on_ign = true;
      Sim s(c);
      s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}};
      s.thrust_cmd = [](double) { return 300.0; };
      if (u) s.eng.P.ign_delay = 99.0;
      s.run(2.6);
      const Res m = scan(s, 0);
      std::snprintf(nm, sizeof nm, "pad_offset_at_E0_%+.2fbar_%s", r / 1e5, u ? "unlit" : "lit");
      add(js(nm, r / 1e5, u, m));
      std::printf("B %-36s -> %-12s RUN %d P0 %+.3f bar%s filt max %.2f bar abs\n", nm, ecu::abortName(static_cast<ecu::Abort>(m.abort)), m.ran,
                  m.p0 / 1e5, m.base_amb ? " (BASE_AMB)" : "", m.pc_filt_max / 1e5);
    }
  } else if (which == "C") {
    const double offs[6] = {0.41e5, 0.60e5, 0.71e5, 0.75e5, 0.90e5, -0.75e5};
    for (double r : offs) for (int u = 0; u < 2; ++u) {
      SimConfig c; c.seed = 97;
      Sim s(c);
      const double t_meco = 2.40, t_rl = 5.00;
      s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {t_meco, Cmd::SHUTDOWN, 0}, {t_rl, Cmd::RELIGHT, 0}};
      s.thrust_cmd = [t_meco](double t) { return t < t_meco ? 300.0 : 200.0; };
      const bool lit = u == 0;
      s.hooks.push_back({t_meco + 0.30, [lit](Sim& q) { q.eng.setTankState(286.70, 1.16); q.eng.Dport = 0.032213; if (!lit) q.eng.P.ign_delay = 99.0; }});
      s.C.pc_off = r; s.C.pc_off_from = t_rl + 0.001;   // after the RELIGHT vented check, at the relight E0
      s.run(t_rl + 1.30);
      const Res m = scan(s, 1);
      std::snprintf(nm, sizeof nm, "a1_relight_offset_at_E0_%+.2fbar_%s", r / 1e5, u ? "unlit" : "lit");
      add(js(nm, r / 1e5, u, m));
      std::printf("C %-40s -> %-12s RUN %d P0 %+.3f bar%s filt max %.2f bar abs\n", nm, ecu::abortName(static_cast<ecu::Abort>(m.abort)), m.ran,
                  m.p0 / 1e5, m.base_amb ? " (BASE_AMB)" : "", m.pc_filt_max / 1e5);
    }
  } else if (which == "D") {
    // Probe D  FC drogue predicate after a false E2 (A1 relight, offset at the relight E0, lit / unlit). GNC rev1 predicate (CHANGELOG
    //          l.157): RELEASE iff b4 AND [(Pc valid AND >= 300 kPa abs) OR b7]; b4/b7 read from the SIL record (Rec::a7 b4-b7 = tlm_flags),
    //          Pc = filtered abs (Rec::Pc_meas, the value the SIL scores; the HAL that fills TLM_FAST d2-d3 is not written). Pc validity is
    //          taken from the PC_SENSOR fault bit. Records whether the predicate becomes true, when, and in which ECU state.
    const double offs[5] = {1.00e5, 1.50e5, 1.80e5, 2.00e5, 2.50e5};
    for (double r : offs) for (int u = 0; u < 2; ++u) {
      SimConfig c; c.seed = 97;
      Sim s(c);
      const double t_meco = 2.40, t_rl = 5.00;
      s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {t_meco, Cmd::SHUTDOWN, 0}, {t_rl, Cmd::RELIGHT, 0}};
      s.thrust_cmd = [t_meco](double t) { return t < t_meco ? 300.0 : 200.0; };
      const bool lit = u == 0;
      s.hooks.push_back({t_meco + 0.30, [lit](Sim& q) { q.eng.setTankState(286.70, 1.16); q.eng.Dport = 0.032213; if (!lit) q.eng.P.ign_delay = 99.0; }});
      s.C.pc_off = r; s.C.pc_off_from = t_rl + 0.001;
      s.run(t_rl + 1.30);
      const Res m = scan(s, 1);
      double t_rel = NAN; int st_rel = -1; bool b7 = false;
      for (const auto& x : s.rec()) {
        if (std::isnan(m.e0) || x.t < m.e0) continue;
        const bool b4 = (x.a7 & 0x10) != 0; b7 = b7 || (x.a7 & 0x80) != 0;
        const bool pc_ok = (x.faults & ecu::fault::PC_SENSOR) == 0;
        if (std::isnan(t_rel) && b4 && ((pc_ok && x.Pc_meas >= 3.0e5) || (x.a7 & 0x80))) { t_rel = x.t - m.e0; st_rel = x.state; }
      }
      std::snprintf(nm, sizeof nm, "a1_relight_offset_at_E0_%+.2fbar_%s", r / 1e5, u ? "unlit" : "lit");
      std::string j = js(nm, r / 1e5, u, m);
      char extra[200];
      std::snprintf(extra, sizeof extra, ", \"fc_release_predicate_true_from_E0_s\": %.4f, \"ecu_state_at_release\": %d, \"b7_seen\": %s}", t_rel, st_rel, b7 ? "true" : "false");
      j.pop_back(); j += extra;
      for (const char* tok : {"-nan", "nan"}) for (size_t p = j.find(tok); p != std::string::npos; p = j.find(tok)) j.replace(p, std::strlen(tok), "null");
      add(j);
      std::printf("D %-40s -> %-12s RUN %d P0 %+.3f bar%s E2 %.3f plant light %.3f filt max %.2f bar abs | FC release %s at %.3f s (state %d) b7 %d\n",
                  nm, ecu::abortName(static_cast<ecu::Abort>(m.abort)), m.ran, m.p0 / 1e5, m.base_amb ? " (BASE_AMB)" : "", m.e2, m.lit, m.pc_filt_max / 1e5,
                  std::isnan(t_rel) ? "NO " : "YES", t_rel, st_rel, b7 ? 1 : 0);
    }
  } else if (which == "E") {
    // Probe E  zero shift that appears AFTER the coast re-zero (A1 coast lengthened to the GNC DC-A1 nominal 20.6 s; shift switched on at
    //          COAST + 2.0 s, i.e. after the re-zero block at COAST + 1.0-1.2 s): does the OI-12 vented check refuse the RELIGHT?
    const double offs[5] = {0.05e5, 0.09e5, 0.11e5, 0.15e5, -0.11e5};
    for (double r : offs) {
      SimConfig c; c.seed = 97;
      Sim s(c);
      const double t_meco = 2.40, t_rl = t_meco + 20.6;
      s.schedule = {{0.05, Cmd::ARM, 0}, {0.80, Cmd::PREPRESS, 0}, {1.40, Cmd::IGNITE, 0}, {t_meco, Cmd::SHUTDOWN, 0}, {t_rl, Cmd::RELIGHT, 0}};
      s.thrust_cmd = [t_meco](double t) { return t < t_meco ? 300.0 : 200.0; };
      s.hooks.push_back({t_meco + 0.30, [](Sim& q) { q.eng.setTankState(286.70, 1.16); q.eng.Dport = 0.032213; }});
      s.C.pc_off = r; s.C.pc_off_from = t_meco + 2.0;
      s.run(t_rl + 1.30);
      const bool started = s.ign_entry_t.size() >= 2;
      const Res m = scan(s, 1);
      int refused = 0;
      for (const auto& x : s.rec()) if (x.t >= t_rl && x.t < t_rl + 0.05 && x.relight_block) { refused = x.relight_block; break; }
      std::snprintf(nm, sizeof nm, "a1_coast20p6s_shift_after_rezero_%+.2fbar", r / 1e5);
      std::string j = js(nm, r / 1e5, 0, m);
      char extra[160];
      std::snprintf(extra, sizeof extra, ", \"relight_started\": %s, \"refuse_code_at_T_fire\": %d}", started ? "true" : "false", refused);
      j.pop_back(); j += extra;
      for (const char* tok : {"-nan", "nan"}) for (size_t p = j.find(tok); p != std::string::npos; p = j.find(tok)) j.replace(p, std::strlen(tok), "null");
      add(j);
      std::printf("E %-44s -> relight started %d refuse code %d abort %s RUN %d\n", nm, started ? 1 : 0, refused,
                  ecu::abortName(static_cast<ecu::Abort>(m.abort)), m.ran);
    }
  } else { std::printf("unknown probe\n"); return 2; }
  arr += "\n]";
  FILE* f = std::fopen(argv[2], "w");
  if (!f) return 1;
  std::fprintf(f, "{\"review\": \"REV-ELEC-1\", \"probe\": \"%s\", \"evidence\": \"SIM (v2.9 core + SIL plant, reviewer copy; plant parameters ASSUMED/ESTIMATE as published; not hardware evidence)\", "
                  "\"kIgnBaseCheck_Pa\": %.0f, \"kIgnFloorAbs_Pa\": %.0f, \"kBpc1Shown\": %s,\n\"cases\": %s}\n",
               which.c_str(), (double)ecu::cfg::kIgnBaseCheck_Pa, (double)ecu::cfg::kIgnFloorAbs_Pa, ecu::cfg::kBpc1Shown ? "true" : "false", arr.c_str());
  std::fclose(f);
  return 0;
}
