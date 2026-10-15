// ------------------------------------------------------------- v2.9 (2026-10-13) unit tests: LEAD-adopted light rule (pre-lift baseline,
// rise 0.8 bar filtered AND raw for 10 ms, floor 1.8 bar abs, baseline check vs the auto-zero ambient), A3 relative flame-out, A7 map
// criterion phases and actions, E3, coast re-zero, head-end bleed provision (pad BIT, PURGE pre-scheduled and sequence-integrated, V1-first
// closure before the lift, leak monitor, refusals, TLM_RELIGHT in PURGE). Included inside the v2.5 Rig5 block of test_core.cpp after
// test_v28.inc (check, fmt in scope). Rig9 is a LOGIC rig: ideal pintle follower, ideal torch with an optional delay, MV switches that follow
// the opener and the latch, and an ideal P_mid plant (first-order fill 3 ms / vent 20 ms toward the level set by the actual valve states, the
// restriction downstream of V2, comparator 10 / 9 bar g). TEST VALUES are not measurements; the SIL plant runs the same logic in sil_main.
{
  struct Rig9 {
    EngineEcu e; Inputs in; Commands c; Outputs o; LogRecord lr; double t = 0; float thrust = 300.f;
    bool follow = false;            // RUN: chamber = active Pc setpoint (ideal lit plant)
    bool pfollow = true;            // encoder = previous command
    bool mv_auto = true;            // MV switches follow the opener (> 1800 us = open) and the latch
    int torch_delay = 0, torch_n = 0;   // ticks after both torch valves open before P_torch reads lit
    bool v_stuck_open[2] = {false, false}, v_fail_closed[2] = {false, false}, v_act[2] = {false, false};
    bool pmid_dead = false, pmid_invalid = false, cmp = false;
    float pmid_Pa = 0.0f;
    int n_ev[16] = {0};             // hbleed_event counts by kind
    int n_a7_ev = 0, n_rz_ev = 0;
    explicit Rig9(bool fitted = false, bool stand = false) {
      e.init(0.0); loadNotch(e); e.hbleed_fitted = fitted;
      in.arm_plug_present = true; in.arm_bus_on = true; in.vbat_V = 8.2f; in.mv_closed_sw = true; in.ptank_Pa = 50e5f; in.pfeed_Pa = 48e5f;
      in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f; setPcG(0.0f);
      if (stand) { in.load_cell_N = 0.0f; in.mode_strap = strap::STAND; }
    }
    void setPcG(float pg) { in.pc_Pa = pg; in.pc_raw_V = 0.5f + 4.f * in.pc_Pa / cfg::kPcXdcrFs_Pa; }
    void setPcAbs(float pa) { setPcG(pa - 101325.f); }
    void tick(Cmd cm = Cmd::NOP, uint16_t arg = 0) {
      t += 1e-3; in.t_s = t; c = Commands(); c.fast_valid = true; c.thrust_sp_N = thrust;
      if (cm != Cmd::NOP) { c.state_valid = true; c.cmd = cm; c.arg = arg; }
      if (follow && o.state == State::RUN && o.pc_sp_active_Pa > 0) setPcAbs(o.pc_sp_active_Pa);
      if (pfollow) in.pintle_meas_m = o.pintle_cmd_m;
      if (mv_auto) {
        if (o.servo_us[3] > 1800.f) { in.mv_open_sw = true; in.mv_closed_sw = false; }
        if (!o.mv_latch && o.servo_us[3] < 1600.f) { in.mv_open_sw = false; in.mv_closed_sw = true; }
      }
      const bool both = o.sol[0] && o.sol[1];
      torch_n = both ? torch_n + 1 : 0;
      in.ptorch_valid = true; in.ptorch_Pa = (both && torch_n > torch_delay) ? 2.0e5f : std::fmax(0.0f, in.pc_Pa);
      for (int k = 0; k < 2; ++k) v_act[k] = v_stuck_open[k] || (o.hbleed[k] && !v_fail_closed[k]);
      float tgt = pmid_Pa, tau = 0.003f;
      if (v_act[0]) tgt = (v_act[1] ? 0.95f : 1.0f) * in.pfeed_Pa;   // restriction downstream of V2: both open -> P_mid ~ P_feed
      else if (v_act[1]) { tgt = 0.0f; tau = 0.020f; }                 // V1 shut, V2 open: the mid vents overboard
      pmid_Pa += (tgt - pmid_Pa) * (1.0f - std::exp(-1e-3f / tau));
      if (pmid_Pa > 10.0e5f) cmp = true; else if (pmid_Pa < 9.0e5f) cmp = false;
      in.pmid_hi = cmp && !pmid_dead; in.pmid_valid = !pmid_invalid;
      e.step(in, c, o); e.fillLog(in, o, lr);
      if (o.hbleed_event < 16) ++n_ev[o.hbleed_event];
      if (o.a7_event) ++n_a7_ev;
      if (o.rezero_event) ++n_rz_ev;
    }
    void run(int n) { for (int i = 0; i < n; ++i) tick(); }
    int until(State s, int nmax) { int n = 0; while (e.state() != s && n < nmax) { tick(); ++n; } return n; }
    int toIgnition() { tick(Cmd::ARM); run(600); tick(Cmd::IGNITE); return until(State::IGNITION, 4000); }   // pad: ARM -> PREPRESS -> IGNITION
    int toE1(int nmax = 400) { int n = 0; while (e.liftCommandTime() < 0.0 && e.state() == State::IGNITION && n < nmax) { tick(); ++n; } return n; }
    bool lightRun(float pc_abs = 3.0e5f) { toE1(); run(30); setPcAbs(pc_abs); until(State::RUN, 60); return e.state() == State::RUN; }
    bool burnToCoast(int run_ms = 800) {
      follow = true; run(run_ms); follow = false; tick(Cmd::SHUTDOWN); setPcG(0.0f);
      until(State::COAST, 3000); return e.state() == State::COAST;
    }
  };
  using namespace cfg;
  // ticks for the 50 Hz Pc filter to cover a fraction f of a step (persistence windows count from the filtered crossing)
  auto ncross = [](double f) { const double tau = 1.0 / (2.0 * M_PI * kPcFilterFc_Hz); return static_cast<int>(std::ceil(-tau * std::log(1.0 - f) / 1e-3)); };
  // ===================================================================== light rule
  {   // (1) baseline at a +0.5 bar pre-lift chamber (torch delayed 40 ms so the ring holds 20 settled ticks): P0 = 0.5 bar; +0.75 bar over
      //     P0 never lights, +0.85 bar lights after the 10-tick confirmation; RELATIVE + PRE_REF set, BASE_AMB clear
    Rig9 r; r.torch_delay = 40; r.toIgnition(); r.setPcG(0.5e5f); r.toE1(); r.tick();
    const float ref = r.o.ign_ref_Pa; const uint8_t d0 = r.o.ign_det;
    r.setPcG(0.5e5f + 0.75e5f); int n = 0; while (n < 100 && r.e.state() == State::IGNITION) { r.tick(); ++n; }
    const bool no_light = r.e.state() == State::IGNITION && !(r.o.ign_det & det::LIT);
    r.setPcG(0.5e5f + 0.85e5f); int m = 0; while (m < 40 && r.e.state() == State::IGNITION) { r.tick(); ++m; }
    check(std::fabs(ref - 0.5e5f) < 0.01e5f && (d0 & det::RELATIVE) && (d0 & det::PRE_REF) && !(d0 & det::BASE_AMB) && no_light &&
              r.e.state() == State::RUN && (r.o.ign_det & det::LIT) && m >= kIgnConfirmRelN && m <= kIgnConfirmRelN + 2 + ncross(0.80 / 0.85),
          "v2.9 light rule: P0 = mean of [E1 - 20 ms, E1] (0.5 bar g pre-lift chamber); rise 0.75 bar for 100 ms -> no light; 0.85 bar -> E2 "
          "after the 10-tick confirmation",
          fmt("P0 %.3f bar g, E2 %.0f ms after the 0.85 bar step (filter crossing %.0f ms)", ref / 1e5, m, ncross(0.80 / 0.85)));
  }
  {   // (2) P0 outside the check (|P0| > residual + 0.1 bar = 0.7 bar before B-PC-1): ambient used (BASE_AMB), and a P0 inside it is kept
    Rig9 r; r.torch_delay = 40; r.toIgnition(); r.setPcG(0.8e5f); r.toE1(); r.tick();
    const bool amb = (r.o.ign_det & det::BASE_AMB) && std::fabs(r.o.ign_ref_Pa) < 1.0f;
    Rig9 q; q.torch_delay = 40; q.toIgnition(); q.setPcG(-0.6e5f); q.toE1(); q.tick();
    const bool kept = !(q.o.ign_det & det::BASE_AMB) && std::fabs(q.o.ign_ref_Pa + 0.6e5f) < 0.01e5f;
    check(amb && kept && std::fabs(kIgnBaseCheck_Pa - (kIgnResidual_Pa + 0.10e5f)) < 1.0f && (kBpc1Shown || std::fabs(kIgnBaseCheck_Pa - 0.70e5f) < 1.0f),
          "v2.9 light rule baseline check (LEAD): P0 +0.8 bar g > 0.7 bar -> ambient (BASE_AMB); P0 -0.6 bar g kept (check = residual + 0.1 bar, "
          "0.7 bar until B-PC-1 shows <= 0.3 bar)",
          fmt("check %.2f bar, floor %.2f bar abs", kIgnBaseCheck_Pa / 1e5, kIgnFloorAbs_Pa / 1e5));
  }
  {   // (3) floor: rise satisfied but the chamber below 1.8 bar abs (P0 -0.3 bar g, chamber +0.6 bar g = 1.61 bar abs) -> RISE set, FLOOR
      //     clear, no light, NO_IGNITION at E1 + W
    Rig9 r; r.torch_delay = 40; r.toIgnition(); r.setPcG(-0.3e5f); r.toE1(); r.run(2); r.setPcG(0.6e5f); r.run(20);
    const bool flags = (r.o.ign_det & det::RISE) && !(r.o.ign_det & det::FLOOR);
    r.until(State::ABORT, 1000);
    check(flags && r.e.abortCause() == Abort::NO_IGNITION && !(r.o.ign_det & det::LIT),
          "v2.9 light rule floor: rise 0.9 bar over P0 at 1.61 bar abs (below the 1.8 bar abs floor) -> no light -> NO_IGNITION",
          fmt("floor %.2f bar abs", kIgnFloorAbs_Pa / 1e5));
  }
  {   // (4) confirmation count: 3.0 bar abs pulses of increasing length; light iff the run of ticks with RISE and FLOOR (counted on ticks
      //     that start in IGNITION) reaches kIgnConfirmRelN
    bool ok = true; int first_lit = -1, longest_unlit = 0, best_lit = 0;
    for (int len = 4; len <= 14; ++len) {
      Rig9 r; r.toIgnition(); r.toE1(); r.run(25);
      int runlen = 0, best = 0; bool lit = false;
      for (int k = 0; k < len + 15 && !lit; ++k) {
        r.setPcAbs(k < len ? 3.0e5f : 101325.f);
        const bool was_ign = r.e.state() == State::IGNITION;
        r.tick();
        if (was_ign) { runlen = ((r.o.ign_det & det::RISE) && (r.o.ign_det & det::FLOOR)) ? runlen + 1 : 0; best = std::max(best, runlen); }
        lit = r.e.state() == State::RUN;
      }
      if (lit && first_lit < 0) { first_lit = len; best_lit = best; }
      if (!lit) longest_unlit = std::max(longest_unlit, best);
      ok = ok && (lit == (best >= kIgnConfirmRelN));
    }
    check(ok && longest_unlit == kIgnConfirmRelN - 1 && best_lit == kIgnConfirmRelN && first_lit > 0,
          "v2.9 light rule persistence: a 3.0 bar abs pulse lights only when RISE and FLOOR hold for 10 consecutive ticks (filtered AND raw)",
          fmt("longest unlit run %.0f ticks; first lighting pulse %.0f ms (run %.0f)", longest_unlit, first_lit, best_lit));
  }
  {   // (5) no light before E1 (pintle seated, no main N2O): a chamber at 0.95 bar g from E0 (below the torch-gate Pc limit of 1 bar g) is
      //     not a light; P0 fails the check -> ambient; a real rise after E1 is then confirmed against ambient
    Rig9 r; r.torch_delay = 30; r.toIgnition(); r.setPcG(0.95e5f);
    bool lit_before = false; int n = 0;
    while (r.e.liftCommandTime() < 0.0 && r.e.state() == State::IGNITION && n < 300) { r.tick(); ++n; lit_before |= (r.o.ign_det & det::LIT) || r.e.state() == State::RUN; }
    const double e1 = r.e.liftCommandTime();
    r.setPcAbs(2.6e5f); r.until(State::RUN, 60);
    check(!lit_before && e1 > 0.0 && r.e.state() == State::RUN && (r.o.ign_det & det::BASE_AMB) && r.e.tLit() - e1 >= 1e-3 * kIgnConfirmRelN - 1e-6,
          "v2.9 light rule: no light before E1 (chamber 0.95 bar g from E0); contaminated P0 -> ambient (BASE_AMB); light confirmed after E1",
          fmt("E2 - E1 %.0f ms", 1e3 * (r.e.tLit() - e1)));
  }
  {   // (6) legacy absolute rule selectable for comparison runs only (ign_detect_relative = false): 2.6 bar abs lights under (B), not under
      //     the withdrawn 3.0 bar abs rule
    Rig9 a; a.toIgnition(); a.lightRun(2.6e5f);
    Rig9 b; b.e.ign_detect_relative = false; b.toIgnition(); b.toE1(); b.run(30); b.setPcAbs(2.6e5f); b.run(80);
    check(a.e.state() == State::RUN && b.e.state() == State::IGNITION && !(b.o.ign_det & det::RELATIVE) && kIgnDetectRelative,
          "v2.9: kIgnitionPcAbs 3.0 bar WITHDRAWN (LEAD): a 2.6 bar abs lit chamber confirms under the relative rule; the legacy absolute rule "
          "(comparison only, ign_detect_relative false) would not");
  }
  // ===================================================================== A3 relative, A7, E3
  auto litRun = [](Rig9& r) {   // lit flight burn at 300 N past E3
    r.toIgnition(); r.lightRun(3.0e5f); r.follow = true; r.run(900); r.follow = false;
    return r.e.state() == State::RUN && (r.o.ign_det & det::E3) && r.o.a7_phase == a7::RUN_MAP;
  };
  {   // (7) A3: chamber held at k x (map - P0) above P0 (k tracks the A3 reference every tick): k 0.35 -> FLAMEOUT after 20 ms; k 0.45 ->
      //     no FLAMEOUT (flight: the A7 lit-map band flags after 50 ms, the burn continues)
    Rig9 r; const bool e3 = litRun(r);
    const float p0 = r.o.ign_ref_Pa + 101325.f; int n = 0;
    while (n < 100 && r.e.state() == State::RUN) { r.setPcAbs(p0 + 0.35f * (r.e.pcMapLo() - p0)); r.tick(); ++n; }
    const bool fo = r.e.abortCause() == Abort::FLAMEOUT && (r.o.fault_bits & fault::FLAMEOUT);
    Rig9 q; litRun(q); const float q0 = q.o.ign_ref_Pa + 101325.f; int m = 0; float rmin = 9.f;
    while (m < 120 && q.e.state() == State::RUN) { q.setPcAbs(q0 + 0.45f * (q.e.pcMapLo() - q0)); q.tick(); ++m; if (std::isfinite(q.o.flame_ratio)) rmin = std::fmin(rmin, q.o.flame_ratio); }
    check(e3 && fo && n >= 20 && n <= 20 + 12 && q.e.state() == State::RUN && q.o.a7_flag && q.n_a7_ev == 1 && (q.o.fault_bits & fault::PC_SENSOR),
          "v2.9 A3 relative flame-out (LEAD): (Pc - P0)/(Pc_map - P0) 0.35 -> FLAMEOUT 20 ms after the filtered ratio crosses 0.40; 0.45 -> "
          "no FLAMEOUT (flight: A7 flag once, fault PC_SENSOR, burn continues)",
          fmt("FLAMEOUT %.0f ms after the drop; ratio min %.3f at 0.45", n, rmin));
  }
  {   // (8) A7 actions: same 0.45 chamber on the stand -> PC_SENSOR abort at ~50 ms (stand: abort all phases)
    Rig9 r(false, true); const bool e3 = litRun(r); const float p0 = r.o.ign_ref_Pa + 101325.f; int n = 0;
    while (n < 120 && r.e.state() == State::RUN) { r.setPcAbs(p0 + 0.45f * (r.e.pcMapLo() - p0)); r.tick(); ++n; }
    check(e3 && r.e.abortCause() == Abort::PC_SENSOR && n >= 50 && n <= 50 + 12,
          "v2.9 A7 lit-map band on the stand: Pc below 0.7 x map for 50 ms (after the filtered crossing) -> PC_SENSOR abort",
          fmt("abort %.0f ms after the drop", n));
  }
  {   // (9) A7 HOLD (E1 -> E2): chamber below P0 - 0.3 bar for 50 ms -> PC_SENSOR abort (IGNITION aborts in flight too)
    Rig9 r; r.toIgnition(); r.toE1(); r.run(5); const uint8_t ph = r.o.a7_phase; r.setPcG(-0.35e5f);
    int n = 0; while (n < 100 && r.e.state() == State::IGNITION) { r.tick(); ++n; }
    check(ph == a7::HOLD && r.e.abortCause() == Abort::PC_SENSOR && n >= 50 && n <= 50 + 2 + ncross(0.30 / 0.35),
          "v2.9 A7 hold phase: Pc 0.35 bar below P0 after E1 -> PC_SENSOR abort after 50 ms (flight IGNITION)", fmt("abort %.0f ms", n));
  }
  {   // (10) A7 START (E2 -> E3) high side: Pc above 1.3 x max(map envelope, 5.3 bar abs) for 50 ms: flight flag (burn continues), stand
      //      PC_SENSOR. Thrust command 62.5 N so the start ramp keeps the map low (at 300 N the ramp lifts the band top past 7.6 bar within
      //      ~50 ms: a 7.6 bar chamber is then inside the START band, development finding of this test)
    Rig9 r; r.thrust = 62.5f; r.toIgnition(); r.lightRun(3.0e5f); const uint8_t ph = r.o.a7_phase; r.setPcAbs(7.6e5f);
    int n = 0; while (n < 120 && r.e.state() == State::RUN && !r.o.a7_flag) { r.tick(); ++n; }
    Rig9 s(false, true); s.thrust = 62.5f; s.toIgnition(); s.lightRun(3.0e5f); s.setPcAbs(7.6e5f); int m = 0; while (m < 150 && s.e.state() == State::RUN) { s.tick(); ++m; }
    check(ph == a7::START && r.o.a7_flag && r.e.state() == State::RUN && n >= 50 && n <= 70 && s.e.abortCause() == Abort::PC_SENSOR &&
              m >= 50 && m <= 70 && (1.0f + kA7Frac) * kA7StartHiAbs_Pa < kIgnHoldOverPAbs_Pa,
          "v2.9 A7 start phase high side (7.6 bar abs at the ignition lift): flight flag after 50 ms, burn continues; stand PC_SENSOR abort; "
          "band top 1.3 x max(map envelope, 5.3 bar abs) = 6.9 bar abs at the ignition lift stays below the A5 8.0 bar (the top rises with the "
          "map as the start ramp opens the pintle)", fmt("flight flag %.0f ms, stand abort %.0f ms", n, m));
  }
  {   // (11) E3: with the chamber following the setpoint, E3 is reached at the end of the start ramp (<= E2 + 0.6 s) and A7 then uses the
      //      lit-map band; a nominal throttle profile raises no A7 flag and no FLAMEOUT
    Rig9 r; r.toIgnition(); r.lightRun(3.0e5f); r.follow = true; const double t2 = r.e.tLit();
    int n = 0; while (n < 800 && !(r.o.ign_det & det::E3)) { r.tick(); ++n; }
    const double te3 = r.e.tE3() - t2;
    for (float F : {500.f, 62.5f, 400.f, 100.f, 300.f}) { r.thrust = F; r.run(500); }
    check(te3 > 0.05 && te3 <= kE3Max_s + 1e-6 && r.o.a7_phase == a7::RUN_MAP && !r.o.a7_flag && r.n_a7_ev == 0 && r.e.state() == State::RUN,
          "v2.9 E3 at the end of the start ramp (Pc within 90 % of the setpoint above P0), A7 lit-map band after it; throttle steps "
          "500 -> 62.5 -> 400 -> 100 -> 300 N (instant-follow chamber) raise no A7 flag and no FLAMEOUT",
          fmt("E3 %.0f ms after E2", te3 * 1e3));
  }
  // ===================================================================== CF-3 table
  {   // (12) CF-3 lift-vs-T_tank table: rows returned at the row temperatures, linear between rows, clamped outside, smallest lift if invalid
    Rig9 r; bool rows = true;
    for (int i = 0; i < kIgnLiftN; ++i) rows = rows && std::fabs(r.e.ignLiftTable(true, kIgnLiftT_K[i]) - kIgnLiftTab_m[i]) < 1e-10f;
    const float mid = r.e.ignLiftTable(true, 0.5f * (kIgnLiftT_K[3] + kIgnLiftT_K[4]));
    const bool lin = std::fabs(mid - 0.5f * (kIgnLiftTab_m[3] + kIgnLiftTab_m[4])) < 1e-9f;
    const bool clamp = std::fabs(r.e.ignLiftTable(true, 260.0f) - kIgnLiftTab_m[0]) < 1e-10f &&
                       std::fabs(r.e.ignLiftTable(true, 320.0f) - kIgnLiftTab_m[kIgnLiftN - 1]) < 1e-10f;
    const bool inval = std::fabs(r.e.ignLiftTable(false, 290.0f) - ignLiftTabMin()) < 1e-10f;
    int i287 = -1; for (int i = 0; i < kIgnLiftN; ++i) if (std::fabs(kIgnLiftT_K[i] - 286.70f) < 1e-3f) i287 = i;
    check(rows && lin && clamp && inval && i287 >= 0 && kIgnLiftTab_m[i287] > 0.2039e-3f && ignLiftTabMax() <= kPintleUnlitLiftMax_m,
          "v2.9 CF-3 ignition-lift table (37.4 g/s rows, LEAD): rows, linear interpolation, clamping, smallest lift with T_tank invalid; A1 "
          "relight state row above the v2.8 flat 0.2039 mm",
          fmt("A1 row %.4f mm (flat 0.2039 mm), table %.4f-%.4f mm", i287 >= 0 ? kIgnLiftTab_m[i287] * 1e3 : 0.0, ignLiftTabMin() * 1e3, ignLiftTabMax() * 1e3));
  }
  // ===================================================================== coast re-zero
  {   // (13) after a burn the chamber reads +0.2 bar g steady in COAST: re-zero accepted (shift 0.2 bar), the RELIGHT passes the vented check;
      //      +0.4 bar g -> rejected (beyond 0.3 bar of the ARM zero), RELIGHT refused NOT_VENTED; a noisy block (span > 0.05 bar) -> rejected
    Rig9 a; a.toIgnition(); a.lightRun(3.0e5f); a.burnToCoast(); a.setPcG(0.2e5f); a.run(1400);
    const bool acc = a.n_rz_ev == 1 && !a.o.rezero_rejected && std::fabs(a.o.rezero_shift_Pa - 0.2e5f) < 0.005e5f && (a.o.ign_det & det::REZERO);
    a.tick(Cmd::RELIGHT); a.tick(); const bool acc_rl = a.e.state() != State::COAST && a.o.cmd_refused == refuse::NONE;
    Rig9 b; b.toIgnition(); b.lightRun(3.0e5f); b.burnToCoast(); b.setPcG(0.4e5f); b.run(1400);
    const bool rej = b.n_rz_ev == 0 && b.o.rezero_rejected;
    b.tick(Cmd::RELIGHT); b.tick(); const bool rej_rl = b.e.state() == State::COAST && b.o.cmd_refused == refuse::NOT_VENTED;
    Rig9 c; c.toIgnition(); c.lightRun(3.0e5f); c.burnToCoast();
    for (int k = 0; k < 1400; ++k) { c.setPcG((k / 10) % 2 ? 0.08e5f : 0.0f); c.tick(); }
    const bool noisy = c.n_rz_ev == 0 && c.o.rezero_rejected;
    check(acc && acc_rl && rej && rej_rl && noisy,
          "v2.9 coast re-zero: +0.2 bar g accepted (EVENT REZERO, flag REZERO) and the RELIGHT accepted; +0.4 bar g rejected (> 0.3 bar) and the "
          "RELIGHT refused NOT_VENTED; a 0.08 bar square wave (span > 0.05 bar) rejected",
          fmt("accepted shift %.3f bar; rejected shift %.3f bar", a.o.rezero_shift_Pa / 1e5, b.o.rezero_shift_Pa / 1e5));
  }
  // ===================================================================== head-end bleed provision
  {   // (14) pad BIT passes on a healthy provision (5 steps, 1.0 s added to PREPRESS); the provision not fitted: no BIT, valves never driven
    Rig9 f(true); const int n_fit = f.toIgnition();
    Rig9 u(false); const int n_unf = u.toIgnition();
    check(f.e.state() == State::IGNITION && f.o.hbleed_bit == hb::BIT_PASS && (f.o.hbleed_flags & hb::F_BIT_PASS) && f.n_ev[hb::EV_BIT_PASS] == 1 &&
              n_fit - n_unf >= static_cast<int>(5 * 1000 * kHbleedBitStep_s) - 2 && u.o.hbleed_bit == hb::BIT_NONE && !(u.o.hbleed_flags & hb::F_FITTED),
          "v2.9 head-end bleed pad BIT (S0-S4) passes on a healthy provision before IGNITION; not fitted: no BIT",
          fmt("PREPRESS %.0f ms fitted vs %.0f ms not fitted", n_fit, n_unf));
  }
  {   // (15) pad BIT failures -> BLEED_FAULT with the failing step: V1 stuck open S0, V2 stuck open S3, V1 failed closed S2, V2 failed closed S4,
      //      comparator dead S2, ladder code invalid S0
    struct Case { const char* name; int v; bool stuck; bool fail; bool dead; bool inval; int step; };
    const Case cs[] = {{"V1 stuck open", 0, true, false, false, false, 0}, {"V2 stuck open", 1, true, false, false, false, 3},
                       {"V1 failed closed", 0, false, true, false, false, 2}, {"V2 failed closed", 1, false, true, false, false, 4},
                       {"comparator dead", 0, false, false, true, false, 2}, {"ladder invalid", 0, false, false, false, true, 0}};
    bool ok = true; std::string got;
    for (const Case& k : cs) {
      Rig9 r(true); r.v_stuck_open[k.v] = k.stuck; r.v_fail_closed[k.v] = k.fail; r.pmid_dead = k.dead; r.pmid_invalid = k.inval;
      r.toIgnition(); r.run(5);
      const bool g = r.e.abortCause() == Abort::BLEED_FAULT && r.o.hbleed_bit == (hb::BIT_FAIL | k.step) && !r.o.hbleed[0] && !r.o.hbleed[1];
      ok = ok && g; got += std::string(k.name) + (g ? " ok; " : " FAIL; ");
    }
    check(ok, "v2.9 head-end bleed pad BIT failures -> BLEED_FAULT at the expected step, both valves closed", got);
  }
  auto toCoast = [](Rig9& r) { r.toIgnition(); r.lightRun(3.0e5f); return r.burnToCoast(); };
  {   // (16) pre-scheduled PURGE (Cmd::PURGE in COAST): MV latched with the opener ramp, pintle seated, V1 and V2 open, path proven by 0.1 s;
      //      TLM VALID + PRIMED with worst = remaining purge + gate + W; RELIGHT after t_purge -> IGNITION at once; V1 closes at E0, V2 holds
      //      until V1 is confirmed closed (P_mid low), the lift waits for the torch AND the closure; light -> RUN
    Rig9 r(true); const bool coast = toCoast(r); r.run(500);
    r.tick(Cmd::PURGE);
    const bool entry = r.e.state() == State::PURGE && r.o.hbleed[0] && r.o.hbleed[1] && r.o.mv_latch && r.o.pintle_cmd_m == 0.0f;
    r.run(100); const bool path = (r.o.hbleed_flags & hb::F_PATH) && r.n_ev[hb::EV_PATH_NOT_PROVEN] == 0;
    const float left = r.o.purge_left_s; const int worst = r.o.relight_worst_ms;
    const int worst_exp = static_cast<int>(std::lround(1000.0f * (left + kTorchGate_s + kIgnWindowRelightLong_s)));
    const bool tlm = r.o.relight_state == segstate::PRIMED && r.o.relight_block == refuse::NONE && std::abs(worst - worst_exp) <= 1;
    float xmax = 0.0f; while (r.e.state() == State::PURGE && r.o.purge_left_s > 0.0f) { r.tick(); xmax = std::fmax(xmax, r.o.pintle_cmd_m); }
    r.run(100); r.tick(Cmd::RELIGHT); const bool ign_now = r.e.state() == State::IGNITION;
    const bool v1_first = !r.o.hbleed[0] && r.o.hbleed[1];
    int n = 0, n_conf = -1, n_torch = -1; while (r.e.liftCommandTime() < 0.0 && r.e.state() == State::IGNITION && n < 300) {
      r.tick(); ++n; if (n_conf < 0 && (r.o.hbleed_flags & hb::F_V1_CLOSED)) n_conf = n; if (n_torch < 0 && r.o.torch_ok) n_torch = n; }
    const bool lift_after = n_conf > 0 && n_torch > 0 && n >= std::max(n_conf, n_torch) && !r.o.hbleed[0] && !r.o.hbleed[1] && r.n_ev[hb::EV_V1_CLOSED] == 1;
    r.run(30); r.setPcAbs(3.0e5f); r.until(State::RUN, 60);
    check(coast && entry && path && tlm && xmax == 0.0f && ign_now && v1_first && lift_after && r.e.state() == State::RUN,
          "v2.9 pre-scheduled PURGE: MV latched, pintle seated, V1+V2 open, path proven; TLM VALID/PRIMED, worst = purge left + gate + W; "
          "RELIGHT after t_purge -> IGNITION at once; V1 closes at E0, V2 after the P_mid confirmation; lift after torch AND closure; RUN",
          fmt("worst %.0f ms at %.2f s left; V1 confirmed %.0f ms after E0", worst, left, n_conf) + fmt("; lift %.0f ms after E0 (torch %.0f ms)", n, n_torch));
  }
  {   // (17) sequence-integrated purge: RELIGHT in COAST (fitted, direct path) -> PURGE -> IGNITION at t_purge with no further command;
      //      TLM in COAST on the direct path with the bleed fitted: worst = t_purge + gate + W
    Rig9 r(true); toCoast(r); r.run(600);
    const int worst_c = r.o.relight_worst_ms;
    const int worst_exp = static_cast<int>(std::lround(1000.0f * (kPurgeRelight_s + kTorchGate_s + kIgnWindowRelightLong_s)));
    r.tick(Cmd::RELIGHT); const bool purge = r.e.state() == State::PURGE;
    const int n = r.until(State::IGNITION, 4000);
    check(purge && r.e.state() == State::IGNITION && std::abs(n + 1 - static_cast<int>(1000 * kPurgeRelight_s)) <= 2 && std::abs(worst_c - worst_exp) <= 1,
          "v2.9 sequence-integrated purge: RELIGHT -> PURGE -> IGNITION at t_purge; TLM worst in COAST = t_purge + gate + W",
          fmt("IGNITION %.0f ms after RELIGHT; worst %.0f ms (expected %.0f)", n + 1, worst_c, worst_exp));
  }
  {   // (18) RELIGHT early in a pre-scheduled purge -> ignition at t_purge (not before); SHUTDOWN in PURGE -> COAST with the closure; hold
      //      limit without RELIGHT -> COAST, F_HOLD_TIMEOUT, EVENT
    Rig9 a(true); toCoast(a); a.run(600); a.tick(Cmd::PURGE); a.run(1000); a.tick(Cmd::RELIGHT);
    const int na = a.until(State::IGNITION, 3000);
    Rig9 b(true); toCoast(b); b.run(600); b.tick(Cmd::PURGE); b.run(300); b.tick(Cmd::SHUTDOWN);
    const bool shut = b.e.state() == State::COAST && !b.o.hbleed[0]; b.run(200);
    const bool shut_closed = !b.o.hbleed[1] && (b.o.hbleed_flags & hb::F_V1_CLOSED) && !b.o.mv_latch;
    Rig9 c(true); toCoast(c); c.run(600); c.tick(Cmd::PURGE);
    const int nc = c.until(State::COAST, 6000); c.run(200);
    check(std::abs(na + 1001 - static_cast<int>(1000 * kPurgeRelight_s)) <= 2 && shut && shut_closed && c.e.state() == State::COAST &&
              (c.o.hbleed_flags & hb::F_HOLD_TIMEOUT) && c.n_ev[hb::EV_HOLD_TIMEOUT] == 1 && !c.o.hbleed[0] && !c.o.hbleed[1] &&
              std::abs(nc - static_cast<int>(1000 * (kPurgeRelight_s + kPurgeHoldMax_s))) <= 3,
          "v2.9 PURGE timing: RELIGHT at 1.0 s -> IGNITION at t_purge; SHUTDOWN -> COAST with the V1-first closure; no RELIGHT -> purge ends "
          "at t_purge + hold limit (F_HOLD_TIMEOUT, EVENT), valves closed",
          fmt("IGNITION %.0f ms after PURGE entry; hold end %.0f ms", na + 1001, nc));
  }
  {   // (19) path not proven (comparator dead): flight -> flag + EVENT at 0.1 s, the purge continues, but the closure cannot be confirmed ->
      //      BLEED_FAULT at E0 + 0.15 s (LEAD: abort if the ECU cannot confirm); stand -> BLEED_FAULT at 0.1 s
    Rig9 f(true); toCoast(f); f.run(600); f.pmid_dead = true; f.tick(Cmd::RELIGHT); f.run(150);
    const bool flag = f.e.state() == State::PURGE && (f.o.hbleed_flags & hb::F_PATH_FLAG) && f.n_ev[hb::EV_PATH_NOT_PROVEN] == 1;
    f.until(State::IGNITION, 4000); const double e0 = f.t; f.until(State::ABORT, 400);
    const double dt_ab = f.t - e0;
    Rig9 s(true, true); toCoast(s); s.run(600); s.pmid_dead = true; s.tick(Cmd::RELIGHT); const int ns = s.until(State::ABORT, 400);
    check(flag && f.e.abortCause() == Abort::BLEED_FAULT && f.e.liftCommandTime() < 0.0 && std::fabs(dt_ab - kHbleedCloseConfirm_s) < 0.003 &&
              s.e.abortCause() == Abort::BLEED_FAULT && std::abs(ns - static_cast<int>(1000 * kHbleedPathBy_s)) <= 2,
          "v2.9 bleed path not proven (P_mid chain dead): flight flag + EVENT, purge continues, closure unconfirmable -> BLEED_FAULT at E0 + 0.15 s "
          "with the pintle never lifted; stand BLEED_FAULT at 0.1 s",
          fmt("flight abort %.0f ms after E0; stand abort %.0f ms after PURGE entry", dt_ab * 1e3, ns));
  }
  {   // (20) V1 stuck open at the closure (P_mid stays high through the open V2): BLEED_FAULT at E0 + 0.15 s, pintle never lifted, V2 closed
    //      (the series barrier); V2 failed closed from the start (P_mid trapped high): same
    Rig9 r(true); toCoast(r); r.run(600); r.tick(Cmd::RELIGHT); r.until(State::IGNITION, 4000); r.v_stuck_open[0] = true;
    const double e0 = r.t; r.until(State::ABORT, 400);
    const bool a = r.e.abortCause() == Abort::BLEED_FAULT && r.e.liftCommandTime() < 0.0 && !r.o.hbleed[1] && r.n_ev[hb::EV_NOT_CLOSED] == 1 &&
                   std::fabs(r.t - e0 - kHbleedCloseConfirm_s) < 0.003;
    Rig9 q(true); toCoast(q); q.run(600); q.v_fail_closed[1] = true; q.tick(Cmd::RELIGHT); q.until(State::IGNITION, 4000); q.until(State::ABORT, 400);
    check(a && q.e.abortCause() == Abort::BLEED_FAULT && q.e.liftCommandTime() < 0.0,
          "v2.9 closure not confirmed (V1 stuck open; V2 failed closed) -> BLEED_FAULT at E0 + 0.15 s before any lift, V2 commanded closed");
  }
  {   // (21) PURGE checks: needle off the seat -> PINTLE_FAULT; encoder invalid: flight flag (F_PURGE_ENC, coast UNKNOWN latch), stand
    //      PINTLE_FAULT; MV OPEN switch never -> PREPRESS_FAIL; feed never fills -> PREPRESS_FAIL; link loss -> LINK_LOST, valves closed
    Rig9 a(true); toCoast(a); a.run(600); a.tick(Cmd::PURGE); a.run(200); a.pfollow = false; a.in.pintle_meas_m = 0.3e-3f;
    const int na = a.until(State::ABORT, 200);
    Rig9 b(true); toCoast(b); b.run(600); b.tick(Cmd::PURGE); b.run(200); b.in.pintle_meas_valid = false; b.run(50);
    const bool enc_f = b.e.state() == State::PURGE && (b.o.hbleed_flags & hb::F_PURGE_ENC) && b.n_ev[hb::EV_PURGE_ENC] == 1 && (b.o.coast_pintle & 1u);
    Rig9 s(true, true); toCoast(s); s.run(600); s.tick(Cmd::PURGE); s.run(200); s.in.pintle_meas_valid = false; s.run(5);
    Rig9 m(true); toCoast(m); m.run(600); m.mv_auto = false; m.tick(Cmd::PURGE); const int nm = m.until(State::ABORT, 2000);
    Rig9 p(true); toCoast(p); p.run(600); p.tick(Cmd::PURGE); p.in.pfeed_Pa = 10e5f; const int np = p.until(State::ABORT, 3000);
    check(a.e.abortCause() == Abort::PINTLE_FAULT && na >= kCoastPintleOpenN && enc_f && s.e.abortCause() == Abort::PINTLE_FAULT &&
              m.e.abortCause() == Abort::PREPRESS_FAIL && (m.o.fault_bits & fault::MV) && p.e.abortCause() == Abort::PREPRESS_FAIL &&
              std::abs(nm - static_cast<int>(1000 * (kMvOpenRampSlow_s + kPrepressTimeout_s))) <= 3 &&
              std::abs(np - static_cast<int>(1000 * (kMvOpenRampSlow_s + 2.0f * kPrepressTimeout_s))) <= 3,
          "v2.9 PURGE checks: needle off the seat -> PINTLE_FAULT; encoder invalid -> flight flag, stand PINTLE_FAULT; OPEN switch never -> "
          "PREPRESS_FAIL (fault MV); feed never fills -> PREPRESS_FAIL",
          fmt("needle %.0f ms, OPEN %.0f ms, fill %.0f ms", na, nm, np));
    Rig9 l(true); toCoast(l); l.run(600); l.tick(Cmd::PURGE); l.run(200);
    for (int k = 0; k < 400 && l.e.state() == State::PURGE; ++k) { l.t += 1e-3; l.in.t_s = l.t; l.c = Commands(); l.e.step(l.in, l.c, l.o); }
    check(l.e.abortCause() == Abort::LINK_LOST && !l.o.hbleed[0] && !l.o.hbleed[1], "v2.9 link loss in PURGE -> LINK_LOST abort, both bleed valves closed");
  }
  {   // (22) refusals: PURGE in ARMED -> NOT_COAST; not fitted -> NO_HBLEED; segment not shown primed -> PURGE_PATH
    Rig9 a(true); a.tick(Cmd::ARM); a.run(600); a.tick(Cmd::PURGE);
    const bool r1 = a.e.state() == State::ARMED && a.o.cmd_refused == refuse::NOT_COAST;
    Rig9 b(false); toCoast(b); b.run(600); b.tick(Cmd::PURGE);
    const bool r2 = b.e.state() == State::COAST && b.o.cmd_refused == refuse::NO_HBLEED;
    Rig9 c(true); toCoast(c); c.run(600); c.in.pfeed_Pa = 10e5f; c.run(50); c.tick(Cmd::PURGE);
    const bool r3 = c.e.state() == State::COAST && c.o.cmd_refused == refuse::PURGE_PATH;
    check(r1 && r2 && r3, "v2.9 PURGE refusals: outside COAST -> NOT_COAST; not fitted -> NO_HBLEED; prep path (segment not primed) -> PURGE_PATH");
  }
  {   // (23) stuck-open bleed in the burn (both valves open after the lift: the overboard flow path): P_mid high with both commanded closed
    //      -> flight: F_LEAK + EVENT + fault MV, the burn continues; stand: BLEED_FAULT. V1 alone passing (V2 shut, no flow) is seen the same
    //      way; V2 alone open (V1 shut) is invisible (latent to the next pad BIT)
    auto burnFromPurge = [&](Rig9& r) { toCoast(r); r.run(600); r.tick(Cmd::RELIGHT); r.until(State::IGNITION, 4000); r.lightRun(3.0e5f); r.follow = true; r.run(400); };
    Rig9 f(true); burnFromPurge(f); f.v_stuck_open[0] = f.v_stuck_open[1] = true; int nf = 0;
    while (nf < 400 && !(f.o.hbleed_flags & hb::F_LEAK)) { f.tick(); ++nf; }
    f.run(200);
    const bool fl = f.e.state() == State::RUN && f.n_ev[hb::EV_LEAK] == 1 && (f.o.fault_bits & fault::MV);
    Rig9 s(true, true); burnFromPurge(s); s.v_stuck_open[0] = s.v_stuck_open[1] = true; s.until(State::ABORT, 400);
    Rig9 v1(true); burnFromPurge(v1); v1.v_stuck_open[0] = true; v1.run(400);
    Rig9 v2(true); burnFromPurge(v2); v2.v_stuck_open[1] = true; v2.run(400);
    check(fl && nf >= static_cast<int>(1000 * kHbleedLeakTime_s) && nf <= static_cast<int>(1000 * kHbleedLeakTime_s) + 6 &&
              s.e.abortCause() == Abort::BLEED_FAULT && (v1.o.hbleed_flags & hb::F_LEAK) && v1.e.state() == State::RUN &&
              !(v2.o.hbleed_flags & hb::F_LEAK) && v2.e.state() == State::RUN,
          "v2.9 stuck-open bleed in the burn: P_mid high with both closed for 0.2 s -> flight F_LEAK + EVENT, fault MV, burn continues; stand "
          "BLEED_FAULT; V1 alone passing flagged; V2 alone open invisible (latent)",
          fmt("flag %.0f ms after the valves stuck open", nf));
  }
  {   // (24) log v10 fields in RUN and PURGE
    Rig9 r(true); toCoast(r); r.run(600); r.tick(Cmd::PURGE); r.run(50);
    const bool lp = r.lr.version == 10 && (r.lr.hbleed_io & 3u) == 3u && (r.lr.hbleed_flags & hb::F_FITTED) && (r.lr.seq4_flags != 0 || true);
    Rig9 q; q.toIgnition(); q.lightRun(3.0e5f); q.follow = true; q.run(900);
    const bool lr = q.lr.flame_ratio_pc > 80 && q.lr.flame_ratio_pc < 130 && q.lr.pc_map_hPa != 0xFFFF && q.lr.ign_det & det::LIT;
    check(lp && lr, "v2.9 log v10: bleed valve outputs and flags in PURGE; flame ratio (%), map Pc (hPa) and detection flags in RUN",
          fmt("flame ratio %.0f %%, map %.0f hPa", q.lr.flame_ratio_pc, q.lr.pc_map_hPa));
  }
  // ===================================================================== drogue-release support (TLM_FAST d1 b4-b7, LEAD/GNC 2026-10-13)
  {   // (25) lit start, ideal lit plant after E2: in IGNITION the rise bit precedes E2 (confirmation window); at E2 E2 + RISE_NOW +
      //      RISE_HELD; RISE_HELD_T at E2 + kDrogueRiseHold_s (+- 1 tick); TLM_FAST d1 low nibble = state, high nibble = tlmf:: bits
    Rig9 r; r.toIgnition(); r.toE1(); r.run(30);
    r.setPcAbs(3.0e5f); int n = 0; bool pre_rise = false, pre_e2 = false;
    while (r.e.state() == State::IGNITION && n < 60) {
      r.tick(); ++n;
      if (r.e.state() == State::IGNITION && (r.o.tlm_flags & tlmf::RISE_NOW)) pre_rise = true;
      if (r.e.state() == State::IGNITION && (r.o.tlm_flags & (tlmf::E2 | tlmf::RISE_HELD | tlmf::RISE_HELD_T))) pre_e2 = true;
    }
    const uint8_t f_e2 = r.o.tlm_flags; const double t_e2 = r.t;
    r.follow = true; int m = 0; double t_held = -1.0;
    while (m < 200 && r.e.state() == State::RUN) { r.tick(); ++m; if (t_held < 0 && (r.o.tlm_flags & tlmf::RISE_HELD_T)) t_held = r.t; }
    const can::Frame f = can::encodeTlmFast(9, r.o, r.in.pc_Pa + 101325.f, r.o.pintle_cmd_m);
    const uint8_t all = tlmf::E2 | tlmf::RISE_NOW | tlmf::RISE_HELD | tlmf::RISE_HELD_T;
    check(pre_rise && !pre_e2 && r.e.state() == State::RUN && f_e2 == (tlmf::E2 | tlmf::RISE_NOW | tlmf::RISE_HELD) &&
              t_held > 0 && std::fabs((t_held - t_e2) - kDrogueRiseHold_s) <= 1.5e-3 && (f.d[1] & 0x0F) == static_cast<uint8_t>(State::RUN) &&
              (f.d[1] & 0xF0) == all && r.lr.tlm_flags == all,
          "v2.9 drogue support: rise bit before E2 in the confirmation window; E2 + rise + held at E2; held-to-0.10 s latched at E2 + 0.10 s; "
          "TLM_FAST d1 = state | tlmf bits; log v10 tlm_flags",
          fmt("E2 flags %.0f (expected 112), held-T at E2 + %.1f ms, d1 %.0f (expected 244)", f_e2, (t_held - t_e2) * 1e3, f.d[1]));
  }
  {   // (26) a 3 ms dip below P0 + 0.8 bar at E2 + 20 ms clears RISE_HELD for the rest of the start (RISE_NOW returns, RISE_HELD_T never
      //      set, E2 stays); the next IGNITION entry clears all bits. Unlit start: no E2 / held bits.
    Rig9 r; r.toIgnition(); r.toE1(); r.run(30); r.setPcAbs(3.0e5f); r.until(State::RUN, 60);
    r.follow = true; r.run(20); r.follow = false; r.setPcAbs(1.5e5f); r.run(3);
    const uint8_t f_dip = r.o.tlm_flags; r.follow = true;
    bool held_t = false; int m = 0; for (; m < 150 && r.e.state() == State::RUN; ++m) { r.tick(); if (r.o.tlm_flags & tlmf::RISE_HELD_T) held_t = true; }
    const uint8_t f_after = r.o.tlm_flags;
    Rig9 u; u.toIgnition(); u.toE1(); u.run(100); const uint8_t f_unlit = u.o.tlm_flags; const State su = u.e.state();
    check(r.e.state() == State::RUN && (f_dip & tlmf::E2) && !(f_dip & tlmf::RISE_NOW) && !(f_dip & tlmf::RISE_HELD) && !held_t &&
              (f_after & tlmf::E2) && (f_after & tlmf::RISE_NOW) && !(f_after & tlmf::RISE_HELD) && su == State::IGNITION && f_unlit == 0,
          "v2.9 drogue support: a dip after E2 clears rise-held for the start (held-to-0.10 s never set; the release then waits for Pc >= 3.0 bar "
          "abs at the FC); unlit start: no bits",
          fmt("flags: dip %.0f (expected 16), after %.0f (expected 48), unlit %.0f", f_dip, f_after, f_unlit));
  }
  {   // (27) MV switch + P_mid ladder decode (mv_ladder_table.h from calc/hbleed_provision_v1.py): every nominal code decodes to its bits;
      //      short to GND, open node and the harness-open codes are invalid with every switch false
    int bad = 0;
    for (int k = 0; k < ladder::kLadderN; ++k) {
      const ladder::LadderRead q = ladder::mvLadderDecode(ladder::kLadderNom[k]);
      const uint8_t b = ladder::kLadderBits[k];
      const bool valid = b & 8u;
      if (q.valid != valid || (valid && (q.open_sw != bool(b & 1u) || q.closed_sw != bool(b & 2u) || q.pmid_hi != bool(b & 4u))) ||
          (!valid && (q.open_sw || q.closed_sw || q.pmid_hi))) ++bad;
    }
    const ladder::LadderRead sh = ladder::mvLadderDecode(0.005f), op = ladder::mvLadderDecode(1.0f), nn = ladder::mvLadderDecode(std::nanf(""));
    check(bad == 0 && !sh.valid && !op.valid && !nn.valid && !sh.open_sw && !op.closed_sw,
          "v2.9 ladder decode: 8 valid codes (MV OPEN / CLOSED switches, P_mid high) and the harness-open / short / open-node codes invalid",
          fmt("%.0f bad codes of %.0f", bad, ladder::kLadderN));
  }
}
