// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175: purge tests rewritten (flow-time schedule, unpurged RELIGHT); full list in 06-electronics/REPORT-v2.10-HANDBACK.md] ------------------------------------------------------------- v2.9 (2026-10-13) unit tests: LEAD-adopted light rule (pre-lift baseline,
// rise 0.8 bar filtered AND raw for 10 ms, floor 1.8 bar abs, baseline check vs the auto-zero ambient), A3 relative flame-out, A7 map
// criterion phases and actions, E3, coast re-zero, head-end bleed provision (pad BIT, PURGE pre-scheduled; v2.10: the sequence-integrated mode is deleted, V1-first
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
    // v2.10 FA-1 photodiode controls: extra delay after P_torch, invalid, torch flame out (both sensors), torch-only view (dark once the
    // torch closes), main flame out (photodiode dark in RUN), stuck reading (>= 0)
    int photo_delay = 0; bool photo_bad = false, torch_out = false, photo_torch_only = false, main_out = false; float photo_stuck_V = -1.0f;
    float ladder_dr = 0.0f;         // v2.10 RE-19: ladder ratio error (harness leak / degraded resistor) seen by the pad-BIT harness step
    float mid_frac = 0.95f;         // P_mid / P_feed with both valves open: 0.95 = v2.9 restriction downstream of V2; v2.10 decided path
                                    // (0.707 mm restrictor at each tap, UPSTREAM of V1, valves 4x): 0.06 = liquid incompressible bound
    float pmid_Pa = 0.0f;
    int n_ev[16] = {0};             // hbleed_event counts by kind
    int n_a7_ev = 0, n_rz_ev = 0;
    explicit Rig9(bool fitted = false, bool stand = false) {
      e.init(0.0); e.ptank_cal_ok = true; loadNotch(e); e.hbleed_fitted = fitted;
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
      const bool torch_flame = both && torch_n > torch_delay && !torch_out;
      in.ptorch_valid = true; in.ptorch_Pa = torch_flame ? 2.0e5f : std::fmax(0.0f, in.pc_Pa);
      const bool ph_flame = (torch_flame && torch_n > torch_delay + photo_delay) || (o.state == State::RUN && !photo_torch_only && !main_out);
      in.photo_valid = !photo_bad; in.photo_V = photo_stuck_V >= 0.0f ? photo_stuck_V : (ph_flame ? 1.0f : 0.10f);   // v2.10 FA-1
      for (int k = 0; k < 2; ++k) v_act[k] = v_stuck_open[k] || (o.hbleed[k] && !v_fail_closed[k]);
      float tgt = pmid_Pa, tau = 0.003f;
      if (v_act[0]) tgt = (v_act[1] ? mid_frac : 1.0f) * in.pfeed_Pa;   // both open: mid_frac x P_feed (restriction position)
      else if (v_act[1]) { tgt = 0.0f; tau = 0.020f; }                 // V1 shut, V2 open: the mid vents overboard
      pmid_Pa += (tgt - pmid_Pa) * (1.0f - std::exp(-1e-3f / tau));
      if (pmid_Pa > 10.0e5f) cmp = true; else if (pmid_Pa < 9.0e5f) cmp = false;
      in.pmid_hi = cmp && !pmid_dead; in.pmid_valid = !pmid_invalid;
      // v2.10 RE-19: raw ladder ratio of the reported code (+ ladder_leak offset); invalid code -> open-circuit ratio
      in.mv_ladder_ratio = in.pmid_valid ? ladder::nominalRatio(in.mv_open_sw, in.mv_closed_sw, in.pmid_hi) + ladder_dr : 1.0f;
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
  {   // (2) v2.10 (LEAD REV-ELEC-1 RE-02, CHANGELOG 166) one-sided baseline check (check = residual + 0.1 bar = 0.7 bar before B-PC-1):
      //     pad P0 +0.8 bar g -> the measured P0 is never replaced by ambient: BASE_HIGH, the lift is refused (PC_SENSOR, no pintle command);
      //     v2.11 (LEAD CHANGELOG 216 (4)): pad P0 -0.8 bar g -> BASE_AMB, the lift is refused as well (PC_SENSOR, no pintle command; v2.10:
      //     P0 := 0, lift, then the A7 HOLD low edge gave PC_SENSOR after the lift); P0 -0.6 bar g kept (lift commanded)
    Rig9 r; r.torch_delay = 40; r.toIgnition(); r.setPcG(0.8e5f);
    float pin_max = 0.0f; int n = 0;
    while (r.e.state() == State::IGNITION && n < 400) { r.tick(); ++n; pin_max = std::max(pin_max, r.o.pintle_cmd_m); }
    const bool refused = r.e.liftCommandTime() < 0.0 && r.e.abortCause() == Abort::PC_SENSOR && (r.o.fault2 & f2::BASE_HIGH) &&
                         !(r.o.ign_det & det::BASE_AMB) && pin_max <= 0.0f;
    Rig9 lo; lo.torch_delay = 40; lo.toIgnition(); lo.setPcG(-0.8e5f);
    float lo_pin = 0.0f; int nl = 0;
    while (lo.e.state() == State::IGNITION && nl < 400) { lo.tick(); ++nl; lo_pin = std::max(lo_pin, lo.o.pintle_cmd_m); }
    const bool lo_refused = lo.e.liftCommandTime() < 0.0 && lo.e.abortCause() == Abort::PC_SENSOR && (lo.o.ign_det & det::BASE_AMB) &&
                            !(lo.o.fault2 & f2::BASE_HIGH) && lo_pin <= 0.0f && !(lo.o.ign_det & det::LIT);
    Rig9 q; q.torch_delay = 40; q.toIgnition(); q.setPcG(-0.6e5f); q.toE1(); q.tick();
    const bool kept = !(q.o.ign_det & det::BASE_AMB) && !(q.o.fault2 & f2::BASE_HIGH) && std::fabs(q.o.ign_ref_Pa + 0.6e5f) < 0.01e5f &&
                      q.e.liftCommandTime() > 0.0;
    check(refused && lo_refused && kept && std::fabs(kIgnBaseCheck_Pa - (kIgnResidual_Pa + 0.10e5f)) < 1.0f &&
              (kBpc1Shown || std::fabs(kIgnBaseCheck_Pa - 0.70e5f) < 1.0f),
          "v2.10 light rule baseline (LEAD RE-02) + v2.11 LEAD 216 (4): pad P0 +0.8 bar g -> BASE_HIGH, lift refused PC_SENSOR, no pintle "
          "command; P0 -0.8 bar g -> BASE_AMB, lift refused PC_SENSOR, no pintle command; P0 -0.6 bar g kept, lift commanded",
          fmtv("check %.2f bar, floor %.2f bar abs; pad refusal at E0 + %d ms (high) / E0 + %d ms (low)", kIgnBaseCheck_Pa / 1e5,
               kIgnFloorAbs_Pa / 1e5, n, nl));
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
      //     not a light. v2.10 (LEAD RE-02): on the pad the high P0 refuses the lift (PC_SENSOR, BASE_HIGH); at the A1 relight (flight, a
      //     lit burn since boot) the start proceeds on the MEASURED P0: +0.75 bar over P0 never lights, +1.6 bar over P0 lights after E1
    Rig9 r; r.torch_delay = 30; r.toIgnition(); r.setPcG(0.95e5f);
    bool lit_before = false; int n = 0;
    while (r.e.state() == State::IGNITION && n < 400) { r.tick(); ++n; lit_before |= (r.o.ign_det & det::LIT) || r.e.state() == State::RUN; }
    const bool pad = !lit_before && r.e.liftCommandTime() < 0.0 && r.e.abortCause() == Abort::PC_SENSOR && (r.o.fault2 & f2::BASE_HIGH);
    Rig9 a; a.toIgnition(); a.lightRun(3.0e5f); a.burnToCoast(); a.run(1400);
    a.tick(Cmd::RELIGHT); const bool ign = a.e.state() == State::IGNITION || a.e.state() == State::PREPRESS;
    a.torch_delay = 40; a.until(State::IGNITION, 4000); a.setPcG(0.95e5f);
    bool lit_a = false; int na = 0;
    while (a.e.liftCommandTime() < 0.0 && a.e.state() == State::IGNITION && na < 400) { a.tick(); ++na; lit_a |= (a.o.ign_det & det::LIT); }
    const double e1 = a.e.liftCommandTime();
    a.tick();
    const bool p0 = std::fabs(a.o.ign_ref_Pa - 0.95e5f) < 0.01e5f && (a.o.fault2 & f2::BASE_HIGH) && !(a.o.ign_det & det::BASE_AMB);
    a.setPcG(0.95e5f + 0.75e5f); a.run(60);
    const bool no_false = a.e.state() == State::IGNITION && !(a.o.ign_det & det::LIT);
    a.setPcG(0.95e5f + 1.6e5f); a.until(State::RUN, 60);
    check(pad && ign && !lit_a && e1 > 0.0 && p0 && no_false && a.e.state() == State::RUN && a.e.tLit() - e1 >= 1e-3 * kIgnConfirmRelN - 1e-6,
          "v2.10 light rule (LEAD RE-02): chamber 0.95 bar g from E0 is no light before E1; pad -> lift refused PC_SENSOR (BASE_HIGH); A1 "
          "relight -> lift on the measured P0 (BASE_HIGH flag), +0.75 bar over P0 no light, +1.6 bar over P0 -> RUN",
          fmt("pad refusal at E0 + %.0f ms; A1 P0 %.3f bar g, E2 - E1 %.0f ms", n, a.o.ign_ref_Pa / 1e5, 1e3 * (a.e.tLit() - e1)));
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
  {   // (10) A7 high side. v2.10 (RE-12, LEAD CHANGELOG 166 (7)): blanked from E2 to E2 + 0.45 s (stand and flight): a 7.6 bar abs chamber
      //      for 0.40 s from E2 (v2.9: flight flag / stand abort after 50 ms) gives no A7 event; after the blank a chamber at 1.5 x the
      //      setpoint (above 1.3 x the map) flags after 50 ms in flight (burn continues) and aborts PC_SENSOR on the stand (before PC_BAND)
    auto rig = [](Rig9& q) {
      q.thrust = 62.5f; q.toIgnition(); q.lightRun(3.0e5f); const uint8_t ph = q.o.a7_phase; q.setPcAbs(7.6e5f);
      int ev = 0; for (int k = 0; k < 400; ++k) { q.tick(); ev += q.o.a7_event ? 1 : 0; }
      q.follow = true; q.run(60); q.follow = false;
      int n = -1;
      for (int k = 0; k < 120 && q.e.state() == State::RUN; ++k) {
        q.setPcAbs(1.5f * q.o.pc_sp_active_Pa); q.tick(); ev += q.o.a7_event ? 1 : 0;
        if (n < 0 && (q.o.a7_flag || q.e.state() != State::RUN)) n = k + 1;
      }
      return std::make_tuple(ph, ev, n);
    };
    Rig9 r; const auto fr = rig(r);
    Rig9 s(false, true); const auto sr = rig(s);
    check(std::get<0>(fr) == a7::START && std::get<1>(fr) == 1 && r.o.a7_flag && r.e.state() == State::RUN && std::get<2>(fr) >= 50 &&
              std::get<2>(fr) <= 60 && s.e.abortCause() == Abort::PC_SENSOR && std::get<2>(sr) >= 50 && std::get<2>(sr) <= 60 &&
              (1.0f + kA7Frac) * kA7StartHiAbs_Pa < kLightSpikeLoAbs_Pa,
          "v2.10 A7 high side: 7.6 bar abs for 0.40 s from E2 -> no A7 event (blank E2..E2 + 0.45 s, RE-12); after the blank 1.5 x setpoint "
          "-> flight flag after 50 ms (burn continues), stand PC_SENSOR abort; start-band top 6.9 bar abs < 8.0 bar LIGHT_SPIKE level",
          fmt("A7 events flight %.0f; flag %.0f ms / stand abort %.0f ms after the excursion", std::get<1>(fr), std::get<2>(fr), std::get<2>(sr)));
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
      //      +0.4 bar g -> rejected (beyond 0.3 bar of the ARM zero). v2.10 (LEAD RE-07): flight RELIGHT then proceeds with f2::NOT_VENTED
      //      (second re-zero also rejected, REZERO2_REJ); on the stand it stays refused NOT_VENTED; a noisy block (span > 0.05 bar) rejected
    Rig9 a; a.toIgnition(); a.lightRun(3.0e5f); a.burnToCoast(); a.setPcG(0.2e5f); a.run(1400);
    const bool acc = a.n_rz_ev == 1 && !a.o.rezero_rejected && std::fabs(a.o.rezero_shift_Pa - 0.2e5f) < 0.005e5f && (a.o.ign_det & det::REZERO);
    const float acc_shift = a.o.rezero_shift_Pa;
    a.tick(Cmd::RELIGHT); a.tick();
    const bool acc_rl = a.e.state() != State::COAST && a.o.cmd_refused == refuse::NONE && !(a.o.fault2 & f2::NOT_VENTED);
    Rig9 b; b.toIgnition(); b.lightRun(3.0e5f); b.burnToCoast(); b.setPcG(0.4e5f); b.run(1400);
    const bool rej = b.n_rz_ev == 0 && b.o.rezero_rejected;
    b.tick(Cmd::RELIGHT); b.tick();
    const bool fl_rl = b.e.state() != State::COAST && b.o.cmd_refused == refuse::NONE && (b.o.fault2 & f2::NOT_VENTED) &&
                       (b.o.fault2 & f2::REZERO2_REJ);
    Rig9 sd(false, true); sd.toIgnition(); sd.lightRun(3.0e5f); sd.burnToCoast(); sd.setPcG(0.4e5f); sd.run(1400);
    sd.tick(Cmd::RELIGHT); sd.tick();
    const bool st_rl = sd.e.state() == State::COAST && sd.o.cmd_refused == refuse::NOT_VENTED && !(sd.o.fault2 & f2::NOT_VENTED);
    Rig9 c; c.toIgnition(); c.lightRun(3.0e5f); c.burnToCoast();
    for (int k = 0; k < 1400; ++k) { c.setPcG((k / 10) % 2 ? 0.08e5f : 0.0f); c.tick(); }
    const bool noisy = c.n_rz_ev == 0 && c.o.rezero_rejected;
    check(acc && acc_rl && rej && fl_rl && st_rl && noisy,
          "v2.10 coast re-zero: +0.2 bar g accepted (EVENT REZERO) and the RELIGHT accepted; +0.4 bar g rejected (> 0.3 bar): flight RELIGHT "
          "proceeds with NOT_VENTED + REZERO2_REJ flags (LEAD RE-07), stand RELIGHT refused NOT_VENTED; 0.08 bar square wave rejected",
          fmt("accepted shift %.3f bar; rejected shift %.3f bar", acc_shift / 1e5, b.o.rezero_shift_Pa / 1e5));
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
  {   // (16) v2.10 pre-scheduled PURGE on FLOW time (LEAD CHANGELOG 164): fill step (V1 open, V2 closed) proves the path; V2 opens at
      //      kPurgeFlowStart_s - kHbleedOpenTime_s; V1 close command at flow start + 2.5 s - kHbleedCloseTime_s; PURGE_FLOW event 2500 ms;
      //      RELIGHT at T_fire = PURGE + kPurgeRelight_s -> IGNITION at once; vent + hold test -> CONFIRMED; the lift waits for the end of
      //      the closure step and the 2oo2 torch confirmation; never with a bleed valve open; RUN. Run at both P_mid flowing levels.
    for (int mf = 0; mf < 2; ++mf) {
      Rig9 r(true); r.mid_frac = mf == 0 ? 0.95f : 0.06f; const bool coast = toCoast(r); r.run(500);
      r.tick(Cmd::PURGE); const double t0 = r.t;
      const bool entry = r.e.state() == State::PURGE && r.o.hbleed[0] && !r.o.hbleed[1] && r.o.mv_latch && r.o.pintle_cmd_m == 0.0f &&
                         (r.o.hbleed2 & hb2::FILL);
      double t_v2 = -1, t_v1c = -1; int both_ms = 0, n_flow_ev = 0; uint16_t flow_ms = 0xFFFF; bool path_before_v2 = false; float xmax = 0.0f;
      int worst_err = 0; bool tlm_ok = true;
      while (r.t - t0 < kPurgeRelight_s - 0.0005) {
        r.tick(); xmax = std::fmax(xmax, r.o.pintle_cmd_m);
        if (t_v2 < 0 && r.o.hbleed[1]) { t_v2 = r.t - t0; path_before_v2 = (r.o.hbleed_flags & hb::F_PATH) && r.n_ev[hb::EV_PATH_NOT_PROVEN] == 0; }
        if (t_v1c < 0 && t_v2 > 0 && !r.o.hbleed[0]) t_v1c = r.t - t0;
        if (r.o.hbleed[0] && r.o.hbleed[1]) ++both_ms;
        if (r.o.purge_flow_event) { ++n_flow_ev; flow_ms = r.o.purge_flow_ms; }
        if (r.e.state() == State::PURGE) {
          const int we = static_cast<int>(std::lround(1000.0f * (r.o.purge_left_s + kTorchGate_s + kIgnWindowRelightLong_s)));
          worst_err = std::max(worst_err, std::abs(r.o.relight_worst_ms - we));
          tlm_ok = tlm_ok && r.o.relight_state == segstate::PRIMED;
        }
      }
      r.tick(Cmd::RELIGHT); const bool ign_now = r.e.state() == State::IGNITION; const double e0 = r.t;
      int n = 0; bool open_at_lift = false; double t_done = -1;
      while (r.e.liftCommandTime() < 0.0 && r.e.state() == State::IGNITION && n < 300) {
        r.tick(); ++n; if (t_done < 0 && (r.o.hbleed2 & (hb2::CONFIRMED | hb2::NOT_CONFIRMED))) t_done = r.t - e0; }
      open_at_lift = r.o.hbleed[0] || r.o.hbleed[1];
      const double t_lift = r.e.liftCommandTime() - e0;
      r.run(30); r.setPcAbs(3.0e5f); r.until(State::RUN, 60);
      const double v2_exp = kPurgeFlowStart_s - kHbleedOpenTime_s, v1c_exp = v2_exp + kHbleedOpenTime_s + kPurgeFlow_s - kHbleedCloseTime_s;
      check(coast && entry && path_before_v2 && std::fabs(t_v2 - v2_exp) < 0.0025 && std::fabs(t_v1c - v1c_exp) < 0.0025 &&
                n_flow_ev == 1 && std::abs(static_cast<int>(flow_ms) - static_cast<int>(1000 * kPurgeFlow_s)) <= 1 &&
                both_ms <= static_cast<int>(1000 * kHbleedCap_s) && worst_err <= 1 && tlm_ok && xmax == 0.0f && ign_now &&
                (r.o.hbleed2 & hb2::CONFIRMED) && !(r.o.hbleed2 & hb2::NOT_CONFIRMED) && !r.o.bleed_fault && r.n_ev[hb::EV_V1_CLOSED] == 1 &&
                t_done >= 0 && t_lift + 1e-9 >= t_done && t_lift <= kTorchGate_s + 0.002 && !open_at_lift && r.e.state() == State::RUN,
            std::string("v2.10 pre-scheduled PURGE on flow time, P_mid flowing level ") + (mf == 0 ? "0.95 P_feed (v2.9 basis)" : "0.06 P_feed (decided path, liquid bound)") +
                ": fill step proves the path, V2 at 0.32 s, V1 close at 2.77 s, PURGE_FLOW 2500 ms, both-open <= cap, RELIGHT at T_fire -> IGNITION, "
                "CONFIRMED, lift after the closure step and the 2oo2 torch, no valve open at the lift, RUN",
            fmt("V2 %.0f ms, V1 close %.0f ms, both open %.0f ms", t_v2 * 1e3, t_v1c * 1e3, both_ms) +
                fmt(", flow %.0f ms; closure done E0+%.0f ms, lift E0+%.0f ms", flow_ms, t_done * 1e3, t_lift * 1e3));
    }
  }
  {   // (17) v2.10 (LEAD CHANGELOG 175 (3)-(4)) unpurged RELIGHT, SUPERSEDED in flight by v2.11 (LEAD 203 (7) ADOPTED; 186 (1), 204 (2)):
      //      flight + bleed fitted: a RELIGHT from COAST is REFUSED (refuse::UNPURGED, stays COAST, no valve), TLM block UNPURGED (READY 0),
      //      worst = PURGE lead 2.90 s + gate + W; Cmd::PURGE is accepted. UNKNOWN line (P_feed invalid): RELIGHT refused UNPURGED and
      //      PURGE refused PURGE_PATH (no accepted flight relight: reported consequence). Stand: the unpurged start is kept (CF-4 / T4):
      //      direct path IGNITION on the command tick. Flight without the bleed fitted: v2.10 paths (direct IGNITION)
    Rig9 r(true); toCoast(r); r.run(600);
    const int worst_c = r.o.relight_worst_ms; const uint8_t blk = r.o.relight_block;
    const int worst_exp = static_cast<int>(std::lround(1000.0f * (kPurgeRelight_s + kTorchGate_s + kIgnWindowRelightLong_s)));
    r.tick(Cmd::RELIGHT);
    const bool refused = r.e.state() == State::COAST && r.o.cmd_refused == refuse::UNPURGED && r.o.cmd_refused_event;
    bool valve = false;
    for (int k = 0; k < 300; ++k) { r.tick(); valve = valve || r.o.hbleed[0] || r.o.hbleed[1]; }
    r.tick(Cmd::PURGE); const bool purge_ok = r.e.state() == State::PURGE;
    Rig9 u(true); toCoast(u); u.run(600); u.in.pfeed_valid = false; u.run(50);
    const uint8_t st_u = u.o.relight_state; u.tick(Cmd::RELIGHT);
    const bool u_ref = u.e.state() == State::COAST && u.o.cmd_refused == refuse::UNPURGED;
    u.tick(Cmd::PURGE); const bool u_pp = u.e.state() == State::COAST && u.o.cmd_refused == refuse::PURGE_PATH;
    Rig9 s(true, true); toCoast(s); s.run(600); s.tick(Cmd::RELIGHT);
    const bool stand_ign = s.e.state() == State::IGNITION && s.o.cmd_refused == refuse::NONE;
    Rig9 n(false); toCoast(n); n.run(600); n.tick(Cmd::RELIGHT);
    const bool nofit_ign = n.e.state() == State::IGNITION && n.o.cmd_refused == refuse::NONE;
    check(refused && !valve && blk == refuse::UNPURGED && std::abs(worst_c - worst_exp) <= 1 && purge_ok && st_u == segstate::UNKNOWN && u_ref &&
              u_pp && stand_ign && nofit_ign,
          "v2.11 LEAD 203 (7) unpurged RELIGHT guard: flight + bleed fitted -> RELIGHT from COAST refused UNPURGED (no valve, TLM block "
          "UNPURGED, worst = 2.90 s + gate + W), PURGE accepted; UNKNOWN line -> RELIGHT UNPURGED and PURGE PURGE_PATH (no flight path); "
          "stand unpurged start kept; no bleed fitted -> v2.10 direct relight",
          fmt("block %.0f worst %.0f ms (expected %.0f)", blk, worst_c, worst_exp) + fmt("; unknown-line state %.0f", st_u) +
              (u_pp ? ", PURGE_PATH" : ", not PURGE_PATH") +
              (stand_ign ? ", stand IGNITION" : ", stand NOT IGNITION") + (nofit_ign ? ", unfitted IGNITION" : ", unfitted NOT IGNITION"));
  }
  {   // (18) RELIGHT early (1.0 s) -> IGNITION at 2.90 s, never before (no truncation); SHUTDOWN in the flow (1.0 s) -> COAST with the
      //      closure step (CONFIRMED) and the achieved flow reported; no RELIGHT -> the post-flow hold (bleed CLOSED) expires at the scheduled
      //      E0 + kPurgeHoldMax_s -> COAST, F_HOLD_TIMEOUT, EVENT; the valves are never both open longer than the cap
    Rig9 a(true); toCoast(a); a.run(600); a.tick(Cmd::PURGE); a.run(1000); a.tick(Cmd::RELIGHT);
    const int na = a.until(State::IGNITION, 3000);
    Rig9 b(true); toCoast(b); b.run(600); b.tick(Cmd::PURGE); b.run(1000); b.tick(Cmd::SHUTDOWN);
    const bool shut = b.e.state() == State::COAST && !b.o.hbleed[0]; const uint16_t bflow = b.o.purge_flow_ms; b.run(300);
    const bool shut_closed = !b.o.hbleed[1] && (b.o.hbleed_flags & hb::F_V1_CLOSED) && !b.o.mv_latch;
    const int bflow_exp = static_cast<int>(std::lround(1000.0 * (1.001 + kHbleedCloseTime_s - kPurgeFlowStart_s)));
    Rig9 c(true); toCoast(c); c.run(600); c.tick(Cmd::PURGE);
    int both = 0, nc = 0; bool open_in_hold = false;
    while (c.e.state() != State::COAST && nc < 6000) {
      c.tick(); ++nc; if (c.o.hbleed[0] && c.o.hbleed[1]) ++both;
      if (nc > static_cast<int>(1000 * kPurgeRelight_s) && (c.o.hbleed[0] || c.o.hbleed[1])) open_in_hold = true;
    }
    c.run(200);
    check(std::abs(na + 1001 - static_cast<int>(1000 * kPurgeRelight_s)) <= 2 && shut && shut_closed && std::abs(bflow - bflow_exp) <= 2 &&
              c.e.state() == State::COAST && (c.o.hbleed_flags & hb::F_HOLD_TIMEOUT) && c.n_ev[hb::EV_HOLD_TIMEOUT] == 1 && !c.o.hbleed[0] &&
              !c.o.hbleed[1] && !open_in_hold && both <= static_cast<int>(1000 * kHbleedCap_s) &&
              std::abs(nc - static_cast<int>(1000 * (kPurgeRelight_s + kPurgeHoldMax_s))) <= 3,
          "v2.10 PURGE timing: RELIGHT at 1.0 s -> IGNITION at 2.90 s; SHUTDOWN at 1.0 s -> COAST with the closure (CONFIRMED), achieved flow "
          "reported; no RELIGHT -> hold with the bleed CLOSED ends at the scheduled E0 + hold limit (F_HOLD_TIMEOUT, EVENT); both-open <= cap",
          fmt("IGNITION %.0f ms after PURGE entry; SHUTDOWN flow %.0f ms", na + 1001, bflow) + fmt(" (exp %.0f); hold end %.0f ms", bflow_exp, nc));
  }
  {   // (19) path not proven (comparator dead): flight -> flag + EVENT when V2 opens (path deadline), the purge runs; the closure cannot be
      //      confirmed (R_CHAIN) -> BLEED_FAULT FLAG to the FC, the relight PROCEEDS (LEAD RE-05): lift, RUN; stand -> BLEED_FAULT abort at
      //      the path deadline
    Rig9 f(true); toCoast(f); f.run(600); f.pmid_dead = true; f.tick(Cmd::PURGE); f.tick(Cmd::RELIGHT); f.run(499);   // v2.10 LEAD 175: FC PURGE + RELIGHT
    const bool flag = f.e.state() == State::PURGE && (f.o.hbleed_flags & hb::F_PATH_FLAG) && f.n_ev[hb::EV_PATH_NOT_PROVEN] == 1 && f.o.hbleed[1];
    f.until(State::IGNITION, 4000); const double e0 = f.t; f.toE1(); const double t_lift = f.e.liftCommandTime() - e0;
    f.run(30); f.setPcAbs(3.0e5f); f.until(State::RUN, 60);
    Rig9 s(true, true); toCoast(s); s.run(600); s.pmid_dead = true; s.tick(Cmd::PURGE); const int ns = s.until(State::ABORT, 800);
    const int ns_exp = static_cast<int>(std::lround(1000.0 * (kPurgeFlowStart_s - kHbleedOpenTime_s + kHbleedPathBy_s)));
    check(flag && f.e.state() == State::RUN && (f.o.hbleed2 & hb2::NOT_CONFIRMED) && (f.o.hbleed2 & hb2::R_CHAIN) && f.o.bleed_fault &&
              (f.o.fault2 & f2::BLEED_FAULT) && t_lift >= 0.0 && t_lift <= kTorchGate_s + 0.002 &&
              s.e.abortCause() == Abort::BLEED_FAULT && std::abs(ns - ns_exp) <= 3,
          "v2.10 bleed path not proven (P_mid chain dead): flight flag + EVENT, purge runs, closure NOT CONFIRMED (chain) -> BLEED_FAULT flag, "
          "relight proceeds (lift, RUN); stand BLEED_FAULT abort at the path deadline",
          fmt("flight lift E0+%.0f ms; stand abort %.0f ms after PURGE (exp %.0f)", t_lift * 1e3, ns, ns_exp));
  }
  {   // (20) V1 stuck open at the closure: with P_mid high while flowing (0.95) the mid never vents (R_VENT); with the decided-path level
      //      (0.06) it reads low while flowing but re-pressurises in the hold test after V2 closes (R_HOLD). Flight: NOT CONFIRMED -> BLEED_FAULT
      //      flag, V2 commanded closed, the relight proceeds (lift <= torch gate, RUN). Stand: BLEED_FAULT abort. V2 failed closed from the
      //      start (no flow, P_mid trapped high): R_VENT, same actions.
    bool ok = true; std::string det;
    for (int k = 0; k < 3; ++k) {
      for (int stand = 0; stand < 2; ++stand) {
        Rig9 r(true, stand == 1); r.mid_frac = k == 1 ? 0.06f : 0.95f; toCoast(r); r.run(600);
        if (k == 2) r.v_fail_closed[1] = true;
        r.tick(Cmd::PURGE); r.tick(Cmd::RELIGHT); const double t_rl = r.t;   // v2.10 LEAD 175: FC PURGE, RELIGHT in the purge
        while (r.e.state() == State::PURGE && !(r.o.hbleed2 & hb2::FLOW_DONE)) r.tick();
        if (k < 2) r.v_stuck_open[0] = true;
        if (stand == 0) {
          r.until(State::IGNITION, 1000); const double e0 = r.t; r.toE1(); const double tl = r.e.liftCommandTime() - e0;
          r.run(30); r.setPcAbs(3.0e5f); r.until(State::RUN, 60);
          const uint8_t why = k == 1 ? hb2::R_HOLD : hb2::R_VENT;
          const bool g = r.e.state() == State::RUN && (r.o.hbleed2 & hb2::NOT_CONFIRMED) && (r.o.hbleed2 & why) && r.o.bleed_fault &&
                         !r.o.hbleed[1] && r.n_ev[hb::EV_NOT_CLOSED] == 1 && tl >= 0.0 && tl <= kTorchGate_s + 0.002;
          ok = ok && g; det += fmt("case %.0f flight ", k) + (g ? "ok" : "FAIL") + fmt(" lift E0+%.0f ms; ", tl * 1e3);
        } else {
          r.until(State::ABORT, 1000);
          const bool g = r.e.abortCause() == Abort::BLEED_FAULT && r.e.liftCommandTime() < t_rl;   // no lift of this relight
          ok = ok && g; det += fmt("case %.0f stand ", k) + (g ? "ok; " : "FAIL") + (g ? "" : fmt(" (cause %.0f, state %.0f, lift %.3f); ", (double)r.e.abortCause(), (double)r.e.state(), r.e.liftCommandTime()));
        }
      }
    }
    check(ok, "v2.10 closure not confirmed (V1 stuck open at both P_mid flowing levels; V2 failed closed) -> flight: BLEED_FAULT flag, V2 "
              "closed, relight proceeds to RUN (lift <= torch gate); stand: BLEED_FAULT abort before any lift", det);
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
    auto burnFromPurge = [&](Rig9& r) { toCoast(r); r.run(600); r.tick(Cmd::PURGE); r.tick(Cmd::RELIGHT); r.until(State::IGNITION, 4000); r.lightRun(3.0e5f); r.follow = true; r.run(400); };
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
    const bool lp = r.lr.version == kLogVersion && (r.lr.hbleed_io & 3u) == 1u && (r.lr.hbleed_flags & hb::F_FITTED) && (r.lr.hb2_flags & hb2::FILL) &&
                    r.lr.purge_flow_ms == 0xFFFF && (r.lr.fa1_flags & fa1::PHOTO_VALID);   // v2.10: fill step (V1 only), photodiode logged
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
  {   // (26) v2.10 (LEAD CHANGELOG 156: RISE_HELD / RISE_HELD_T on the FILTERED channel only; v2.9 used filtered AND raw, and the 3 ms dip
      //      below cleared the hold). (a) a 3 ms dip of the reading to 1.5 bar abs at E2 + 20 ms: RISE_NOW (b5, filtered AND raw) drops
      //      during the dip, RISE_HELD stays (the 50 Hz channel does not fall below P0 + 0.8 bar), RISE_HELD_T latches at E2 + 0.10 s.
      //      (b) a 12 ms dip (the filtered channel falls below P0 + 0.8 bar; shorter than the A3 20 ms persistence, which a 30 ms dip trips):
      //      RISE_HELD clears for the rest of the start, RISE_HELD_T never set, E2 stays. Unlit start: no E2 / held bits.
    auto dip = [](Rig9& r, int ms, uint8_t* f_dip, bool* held_t, uint8_t* f_after) {
      r.toIgnition(); r.toE1(); r.run(30); r.setPcAbs(3.0e5f); r.until(State::RUN, 60);
      r.follow = true; r.run(20); r.follow = false; r.setPcAbs(1.5e5f); r.run(ms);
      *f_dip = r.o.tlm_flags; r.follow = true; *held_t = false;
      for (int m = 0; m < 150 && r.e.state() == State::RUN; ++m) { r.tick(); if (r.o.tlm_flags & tlmf::RISE_HELD_T) *held_t = true; }
      *f_after = r.o.tlm_flags;
    };
    Rig9 a; uint8_t fa_dip = 0, fa_after = 0; bool ha = false; dip(a, 3, &fa_dip, &ha, &fa_after);
    Rig9 b; uint8_t fb_dip = 0, fb_after = 0; bool hb_ = false; dip(b, 12, &fb_dip, &hb_, &fb_after);
    Rig9 u; u.toIgnition(); u.toE1(); u.run(100); const uint8_t f_unlit = u.o.tlm_flags; const State su = u.e.state();
    check(a.e.state() == State::RUN && (fa_dip & tlmf::E2) && !(fa_dip & tlmf::RISE_NOW) && (fa_dip & tlmf::RISE_HELD) && ha &&
              (fa_after & tlmf::RISE_HELD_T) && b.e.state() == State::RUN && (fb_dip & tlmf::E2) && !(fb_dip & tlmf::RISE_HELD) && !hb_ &&
              (fb_after & tlmf::E2) && (fb_after & tlmf::RISE_NOW) && !(fb_after & tlmf::RISE_HELD) && su == State::IGNITION && f_unlit == 0,
          "v2.10 drogue support (filtered-only hold): a 3 ms reading dip after E2 drops RISE_NOW but keeps RISE_HELD, RISE_HELD_T latches at "
          "E2 + 0.10 s; a 12 ms dip (filtered below P0 + 0.8 bar, no A3 trip) clears RISE_HELD for the start (held-to-0.10 s never set: the release then "
          "waits for Pc >= 3.0 bar abs at the FC); unlit start: no bits",
          fmtv("3 ms: dip %.0f (expected 80) after %.0f (expected 240); 12 ms: dip %.0f (expected 16) after %.0f (expected 48) state %.0f; unlit %.0f",
              (double)fa_dip, (double)fa_after, (double)fb_dip, (double)fb_after, (double)b.e.state(), (double)f_unlit));
  }
  {   // (27) MV switch + P_mid ladder decode (mv_ladder_table.h from calc/hbleed_provision_v1.py): every nominal code decodes to its bits;
      //      short to GND, open node and the harness-open codes are invalid with every switch false. v2.10 (RE-19): the two OPEN+CLOSED
      //      codes are invalid with both_sw; a soft short of 1.1-4.3 kOhm to GND (v2.9: decoded VALID as the lowest code) is invalid
    int bad = 0, both = 0;
    for (int k = 0; k < ladder::kLadderN; ++k) {
      const ladder::LadderRead q = ladder::mvLadderDecode(ladder::kLadderNom[k]);
      const uint8_t b = ladder::kLadderBits[k];
      const bool conflict = (b & 8u) && (b & 3u) == 3u;
      const bool valid = (b & 8u) && !conflict;
      both += q.both_sw;
      if (q.valid != valid || q.both_sw != conflict || (valid && (q.open_sw != bool(b & 1u) || q.closed_sw != bool(b & 2u) || q.pmid_hi != bool(b & 4u))) ||
          (!valid && (q.open_sw || q.closed_sw || q.pmid_hi))) ++bad;
    }
    const ladder::LadderRead sh = ladder::mvLadderDecode(0.005f), op = ladder::mvLadderDecode(1.0f), nn = ladder::mvLadderDecode(std::nanf(""));
    // soft short R_s to GND across the no-switch ladder (R_top 10k, EOL 82.5k): 1.1-4.3 kOhm in 0.1 kOhm steps
    int soft_valid = 0;
    for (double rs = 1100.0; rs <= 4300.0 + 1e-6; rs += 100.0) {
      const double rp = 1.0 / (1.0 / 82500.0 + 1.0 / rs);
      soft_valid += ladder::mvLadderDecode(static_cast<float>(rp / (10000.0 + rp))).valid;
    }
    check(bad == 0 && both == 2 && soft_valid == 0 && !sh.valid && !op.valid && !nn.valid && !sh.open_sw && !op.closed_sw && sh.short_gnd,
          "v2.10 ladder decode (RE-19): 6 valid codes; OPEN+CLOSED codes invalid (both_sw -> MV_FAULT); soft short 1.1-4.3 kOhm to GND invalid; "
          "harness-open / short / open-node codes invalid",
          fmt("%.0f bad codes of %.0f; soft-short readings decoded valid %.0f", bad, ladder::kLadderN, soft_valid));
  }
  {   // (27b) v2.10 RE-19: pad-BIT harness-resistance step and the OPEN+CLOSED conflict. A ladder ratio 0.017 low (122 kOhm leak across
      //       the OPEN-state ladder, DERIVED) fails the BIT at S0 -> BLEED_FAULT; +0.003 (1 % parts) passes. Conflict at ARM -> MV_FAULT;
      //       in RUN: stand -> MV_FAULT abort after 5 ms, flight -> fault MV flag, burn continues
    Rig9 lk(true); lk.ladder_dr = -0.017f; lk.tick(Cmd::ARM); lk.run(600); lk.tick(Cmd::IGNITE); lk.until(State::ABORT, 4000);
    const bool leak = lk.e.abortCause() == Abort::BLEED_FAULT && (lk.o.hbleed_bit & hb::BIT_FAIL);
    Rig9 ok(true); ok.ladder_dr = 0.003f; ok.tick(Cmd::ARM); ok.run(600); ok.tick(Cmd::IGNITE); ok.until(State::IGNITION, 4000);
    const bool tol = ok.e.state() == State::IGNITION && ok.o.hbleed_bit == hb::BIT_PASS;
    Rig9 ar; ar.in.mv_sw_conflict = true; ar.tick(Cmd::ARM); ar.run(5);
    const bool arm = ar.e.state() != State::ARMED && ar.e.abortCause() == Abort::MV_FAULT;
    Rig9 st(false, true); st.toIgnition(); st.lightRun(3.0e5f); st.follow = true; st.run(100); st.in.mv_sw_conflict = true; st.run(10);
    const bool sab = st.e.abortCause() == Abort::MV_FAULT;
    Rig9 fl; fl.toIgnition(); fl.lightRun(3.0e5f); fl.follow = true; fl.run(100); fl.in.mv_sw_conflict = true; fl.run(50);
    const bool ffl = fl.e.state() == State::RUN && (fl.o.fault_bits & fault::MV);
    check(leak && tol && arm && sab && ffl,
          "v2.10 pad-BIT harness step + ladder conflict (RE-19): ratio -0.017 (122 kOhm leak) -> BIT FAIL / BLEED_FAULT, +0.003 passes; "
          "OPEN+CLOSED at ARM -> MV_FAULT; in RUN stand MV_FAULT abort, flight fault MV flag only",
          fmt("BIT %.0f / %.0f; tolerance %.3f", lk.o.hbleed_bit, ok.o.hbleed_bit, kLadderBitTol));
  }
#include "test_v210.inc"   // v2.10 (Rig9 in scope)
#include "test_v211.inc"   // v2.11 (Rig9, toCoast in scope)
#include "test_v211b.inc"  // v2.11 2026-10-20 (LEAD 216 / 227 / 230 / 21:46:49Z rulings; Rig9, toCoast in scope)
}
