#!/usr/bin/env python3
"""REV-ELEC-2: make a reviewer probe copy of sil_main.cpp (S17 R2 hold) with FC frame phases, starve duration, a dropped DROGUE 0
frame and extra sweeps. The firmware core is not modified; only the SIL scenario file copy is patched. Usage: make_probe.py <in> <out>"""
import sys
src = open(sys.argv[1]).read()
def rep(a, b, n=1):
    global src
    c = src.count(a)
    assert c == n, (a, c)
    src = src.replace(a, b)
rep('struct R2Fc {\n', 'static int g_ph100 = 5, g_ph50 = 0; static double g_starve_s = 0.40; static bool g_drop_release = false;   // REV-ELEC-2 probe\nstruct R2Fc {\n')
rep('const bool frame100 = (ms % 10 == 5);', 'const bool frame100 = (ms % 10 == g_ph100);')
rep('if (ms % 2 == 0) {   // TLM_FAST frame', 'if (ms % 2 == g_ph50) {   // TLM_FAST frame')
rep('if (report) schedInsert(s, s.t, Cmd::DROGUE, 0);', 'if (report && !g_drop_release) schedInsert(s, s.t, Cmd::DROGUE, 0);')
rep('if (k.starve) s.hooks.push_back({t_rl - 0.01, [](Sim& z) { z.eng.P.starve_s = 0.40;', 'if (k.starve) s.hooks.push_back({t_rl - 0.01, [](Sim& z) { z.eng.P.starve_s = g_starve_s;')
probe = r'''
  if (std::getenv("R2PROBE")) {   // REV-ELEC-2 reviewer probe (not part of the author's record)
    const double W6p = 37.16 - 16.31;
    auto pr = [&](const char* tag, const S17Case& k, double e2) {
      const S17R R = run(k, e2, nullptr);
      std::printf("PROBE %-14s F %3.0f rep %d onset %5.1f fo %5.1f d_app %5.2f noise %.1f seed %4u ph100 %d ph50 %d starve %.3f drop %d | %-16s | rel %7.1f ms br %d | "
                  "abort_frame %7.1f | ECU %-12s %7.1f | inval %6.1f | Fmax %6.2f nmax %d | hold %4d (%7.1f..%7.1f) sp %.2f | dead lift %.4f Fcold %.2f\n",
                  tag, k.F_rl, k.report ? 1 : 0, k.loss_dt * 1e3, k.fo_dt * 1e3, k.d_app, k.noise, k.seed, g_ph100, g_ph50, g_starve_s,
                  g_drop_release ? 1 : 0, R.outcome.c_str(), R.fc.t_rel * 1e3, R.fc.branch, R.fc.t_abort * 1e3,
                  ecu::abortName(static_cast<ecu::Abort>(R.abort)), (R.t_ab - R.fc.t_e2) * 1e3, R.fc.t_inval * 1e3, R.fc.f_meas_max_r2,
                  R.fc.n_ok_max, R.fc.hold_ticks, (R.fc.hold_first - R.fc.t_e2) * 1e3, (R.fc.hold_last - R.fc.t_e2) * 1e3, R.f_hold_sp,
                  R.lift_dead_mm, R.fcold_dead);
      std::fflush(stdout);
      return R;
    };
    const std::string mode = std::getenv("R2PROBE");
    if (mode == "A" || mode == "all") {   // FC frame phase x onset, dead engine, W6 bound, hold
      for (double on : {0.005, 0.010}) for (int ph = 0; ph < 10; ++ph) for (int p50 = 0; p50 < 2; ++p50) {
        g_ph100 = ph; g_ph50 = p50;
        pr("A_phase_W6", S17Case{"A", 200, true, true, on, on + 0.001, W6p, 0, false, 1, "", ""}, e2ref["200_1"]);
      }
      g_ph100 = 5; g_ph50 = 0;
    }
    if (mode == "B" || mode == "all") {   // onset sweep, all 100 Hz phases, W6, hold
      for (double on : {0.001, 0.002, 0.003, 0.004, 0.006, 0.008, 0.012, 0.015, 0.020, 0.030, 0.050}) for (int ph = 0; ph < 10; ++ph) {
        g_ph100 = ph;
        pr("B_onset_W6", S17Case{"B", 200, true, true, on, on + 0.001, W6p, 0, false, 1, "", ""}, e2ref["200_1"]);
      }
      g_ph100 = 5;
    }
    if (mode == "C" || mode == "all") {   // W6 + 5 N rms noise, hold and no hold, 200 / 500 N, 100 seeds each
      for (double F : {200.0, 500.0}) for (bool rep : {true, false}) for (int i = 0; i < 100; ++i) {
        char key[40]; std::snprintf(key, sizeof key, "%.0f_1", F);
        pr(rep ? "C_W6_noise" : "C_W6_noise_NR", S17Case{"C", F, rep, true, 0.005, 0.006, W6p, 5.0, false, static_cast<uint32_t>(2000 + i), "", ""}, e2ref[key]);
      }
    }
    if (mode == "D" || mode == "all") {   // lit start, starved plateau of varying length, Pc lost at E2 + 5 ms, hold, calm and W6
      for (double st : {0.30, 0.36, 0.40, 0.42, 0.44, 0.46, 0.48, 0.50, 0.52, 0.55, 0.60}) for (double da : {0.0, W6p}) {
        g_starve_s = st;
        const S17R ref = run(S17Case{"ref", 200, true, true, -1.0, -1.0, 0.0, 0.0, false, 1, "", ""}, NAN, nullptr);
        pr(da > 0 ? "D_starve_W6" : "D_starve_calm", S17Case{"D", 200, true, true, 0.005, -1.0, da, 0.0, false, 1, "", ""}, ref.fc.t_e2);
      }
      g_starve_s = 0.40;
    }
    if (mode == "E" || mode == "all") {   // DROGUE 0 frame lost after an R2 release with Pc invalid (lit, starved, hold)
      g_drop_release = true;
      pr("E_drop_rel", S17Case{"E", 200, true, true, 0.005, -1.0, 0.0, 0.0, false, 1, "", ""}, e2ref["200_1"]);
      pr("E_drop_rel500", S17Case{"E", 500, true, true, 0.005, -1.0, 0.0, 0.0, false, 1, "", ""}, e2ref["500_1"]);
      g_drop_release = false;
      pr("E_ctrl", S17Case{"E", 200, true, true, 0.005, -1.0, 0.0, 0.0, false, 1, "", ""}, e2ref["200_1"]);
    }
    return;
  }
'''
rep('  j.k("references").raw(refs + "]");\n', '  j.k("references").raw(refs + "]");\n' + probe)
open(sys.argv[2], 'w').write(src)
print('probe source written')
