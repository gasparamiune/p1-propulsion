// v2.10 unit tests (2026-10-13; LEAD CHANGELOG 156/160/161; (v210-16) LEAD CHANGELOG 181 (4); (v210-17) LEAD CHANGELOG 186 (2)). Included at the end of the test_v29.inc block (Rig9 in scope).
  {   // (v210-1) LIGHT_SPIKE record on an unlit start (NO_IGNITION at W): opens at E1, closes at the exit (closed_by_exit, not lit) with one
      //          event; EVENT arg encoding (0.5 bar / 2 ms units, saturation) and the log v11 fields
    Rig9 r; r.toIgnition(); r.toE1();
    r.setPcAbs(1.5e5f);                                       // 1.5 bar abs: rise 0.49 bar over P0 < 0.8 bar -> never lit
    int nev = 0; for (int k = 0; k < 900 && r.e.state() == State::IGNITION; ++k) { r.tick(); if (r.o.light_spike_event) ++nev; }
    r.tick(); if (r.o.light_spike_event) ++nev;
    const LightSpikeRec& L = r.o.light_spike;
    const uint16_t a1 = evt::lightSpikeArg(20.0e5f, 0.030f), a2 = evt::lightSpikeArg(200.0e5f, 2.0f), a3 = evt::lightSpikeArg(std::nanf(""), 0.0f);
    const bool log_ok = r.lr.version == 11 && r.lr.ls_raw_hPa == static_cast<uint16_t>(std::lround(L.peak_raw_Pa * 0.01f)) && r.lr.ls_tlight_ms == 0xFFFFu &&
                        (r.lr.ls_flags & 0x16u) == 0x12u;   // done + closed by exit, not lit
    check(r.e.abortCause() == Abort::NO_IGNITION && L.done && !L.lit && L.closed_by_exit && nev == 1 && std::fabs(L.peak_raw_Pa - 1.5e5f) < 600.0f &&
              L.t8_raw_s == 0.0f && !std::isfinite(L.t_light_s) && a1 == (40u | (15u << 8)) && a2 == (254u | (255u << 8)) && a3 == 0x00FFu && log_ok,
          "v2.10 LIGHT_SPIKE: unlit start closes the record at the NO_IGNITION exit (not lit, one event); EVENT 0x20 arg = raw peak [0.5 bar] | "
          "t8 [2 ms] << 8 with saturation; log v11 ls_* fields",
          fmtv("raw peak %.3f bar abs, events %.0f, arg(20 bar, 30 ms) %.0f (= 40 | 15 << 8), log ls_flags %.0f (= done + exit 18)", L.peak_raw_Pa / 1e5, (double)nev, (double)a1, (double)r.lr.ls_flags));
  }
  {   // (v210-2) item 3 (LEAD CHANGELOG 160 (3)): an A7 START high-side excursion in FLIGHT (7.6 bar abs at the ignition lift, 62.5 N: the
      //          late-light pool-burn shape) flags A7 but neither switches the Pc loop to open loop (fault OPEN_LOOP never set) nor invalidates
      //          the telemetered Pc (pc_valid, TLM_FAST d2-d3 != 0xFFFF on every tick); state RUN and b4 stay; the latched PC_SENSOR bit is the
      //          only trace in the fault word. pc_sensor_ok_ has ONE assignment (the voltage window, engine_ecu.cpp step()).
    Rig9 r; r.thrust = 62.5f; r.toIgnition(); r.lightRun(3.0e5f); r.setPcAbs(7.6e5f);
    int n = 0, ol = 0, inval = 0, tlm_bad = 0; bool flag = false; int n_flag = -1;
    auto obs = [&]() {
      if (r.o.fault_bits & fault::OPEN_LOOP) ++ol;
      if (!r.o.pc_valid) ++inval;
      const can::Frame f = can::encodeTlmFast(1, r.o, r.e.pcAbsFiltered(), r.o.pintle_cmd_m);
      if ((f.d[2] | (f.d[3] << 8)) == 0xFFFF || (f.d[1] & 0x0F) != static_cast<uint8_t>(State::RUN) || !(f.d[1] & tlmf::E2)) ++tlm_bad;
      if (r.o.a7_flag && n_flag < 0) n_flag = n;
      flag |= r.o.a7_flag;
    };
    for (int k = 0; k < 400 && r.e.state() == State::RUN; ++k) { r.tick(); ++n; obs(); }   // pool-like excursion inside the blank
    const bool quiet = !flag;
    r.follow = true; for (int k = 0; k < 60; ++k) { r.tick(); ++n; obs(); } r.follow = false;
    const int n_x = n;
    for (int k = 0; k < 100 && r.e.state() == State::RUN; ++k) { r.setPcAbs(1.5f * r.o.pc_sp_active_Pa); r.tick(); ++n; obs(); }   // < PC_BAND 150 ms
    check(quiet && flag && n_flag - n_x >= 50 && n_flag - n_x <= 60 && r.e.state() == State::RUN && r.e.abortCause() == Abort::NONE &&
              ol == 0 && inval == 0 && tlm_bad == 0 && (r.o.fault_bits & fault::PC_SENSOR),
          "v2.10 item 3 + RE-12: flight A7 high side quiet for a 7.6 bar excursion inside E2..E2 + 0.45 s; after the blank 1.5 x setpoint flags "
          "(fault bit PC_SENSOR, EVENT PC_IMPLAUS) with the Pc loop closed (no OPEN_LOOP) and the telemetered Pc valid (no 0xFFFF; RUN + b4 kept)",
          fmtv("A7 flag %.0f ms after the excursion, OPEN_LOOP ticks %.0f, Pc-invalid ticks %.0f, bad TLM frames %.0f", (double)(n_flag - n_x), (double)ol,
               (double)inval, (double)tlm_bad));
  }
  {   // (v210-3) item 5 (LEAD CHANGELOG 161 (2) interim FC rule): Pc channel invalid (open input, 0.02 V, reading -8.8 bar) at E2 + 20 ms in
      //          FLIGHT: the ECU stays in RUN (no abort for 300 ms), open loop (OPEN_LOOP), A3 and A7 suspended (no FLAMEOUT / PC_SENSOR abort on
      //          the garbage reading, a7 phase OFF), TLM_FAST d1 state RUN + b4 valid while d2-d3 = 0xFFFF; b5-b7 clear (b7 never set).
      //          Stand: PC_SENSOR abort after 5 ms.
    auto lose = [](Rig9& r) { r.in.pc_raw_V = 0.02f; r.in.pc_Pa = (0.02f - 0.5f) / 4.0f * cfg::kPcXdcrFs_Pa; };
    Rig9 r; r.toIgnition(); r.toE1(); r.run(30); r.setPcAbs(3.0e5f); r.until(State::RUN, 60);
    r.follow = true; r.run(20); r.follow = false; lose(r);
    int n = 0, ol = 0, ok_frames = 0, b567 = 0, ph = 0;
    for (; n < 300 && r.e.state() == State::RUN; ++n) {
      r.tick(); lose(r);
      if (r.o.fault_bits & fault::OPEN_LOOP) ++ol;
      if (r.o.a7_phase != a7::OFF) ++ph;
      const can::Frame f = can::encodeTlmFast(1, r.o, r.e.pcAbsFiltered(), r.o.pintle_cmd_m);
      if ((f.d[2] | (f.d[3] << 8)) == 0xFFFF && (f.d[1] & 0x0F) == static_cast<uint8_t>(State::RUN) && (f.d[1] & tlmf::E2)) ++ok_frames;
      if (f.d[1] & (tlmf::RISE_NOW | tlmf::RISE_HELD | tlmf::RISE_HELD_T)) ++b567;
    }
    Rig9 s(false, true); s.toIgnition(); s.toE1(); s.run(30); s.setPcAbs(3.0e5f); s.until(State::RUN, 60);
    s.follow = true; s.run(20); s.follow = false; lose(s); int m = 0; while (m < 50 && s.e.state() == State::RUN) { s.tick(); lose(s); ++m; }
    check(n == 300 && r.e.state() == State::RUN && r.e.abortCause() == Abort::NONE && ol == 300 && ph == 0 && ok_frames == 300 && b567 == 0 &&
              s.e.abortCause() == Abort::PC_SENSOR && m >= 5 && m <= 7,
          "v2.10 item 5: Pc invalid at E2 + 20 ms in flight -> RUN open loop for 300 ms, A3/A7 suspended, every TLM_FAST frame state RUN + b4 with "
          "d2-d3 = 0xFFFF and b5-b7 clear (FC interim rule: release at E2 + 0.10 s); stand -> PC_SENSOR abort in 5 ms",
          fmtv("flight: %.0f ms RUN, OPEN_LOOP %.0f, A7 phase on %.0f, frames OK %.0f, b5-b7 %.0f; stand abort after %.0f ms", (double)n, (double)ol,
               (double)ph, (double)ok_frames, (double)b567, (double)m));
  }
  {   // (v210-4) FMEA FA-1 (a) (LEAD CHANGELOG 164 (8)): E1 = P_torch AND photodiode lit on the same 3 consecutive ticks. Photodiode invalid
      //          -> no E1 -> TORCH_FAULT at the torch gate (pintle never lifted); photodiode 20 ms later than P_torch -> E1 at the photodiode;
      //          photodiode stuck lit from E0 (never seen dark) -> TORCH_FAULT; P_torch alone never lifts
    Rig9 a; a.photo_bad = true; a.toIgnition(); const double e0a = a.t; a.until(State::ABORT, 400);
    const bool fa = a.e.abortCause() == Abort::TORCH_FAULT && a.e.liftCommandTime() < 0.0 && std::fabs(a.t - e0a - kTorchGate_s) < 0.003;
    Rig9 b; b.photo_delay = 20; b.toIgnition(); const double e0b = b.t; b.toE1(); const double lb = b.e.liftCommandTime() - e0b;
    Rig9 c; c.toIgnition(); const double e0c = c.t; c.toE1(); const double lc = c.e.liftCommandTime() - e0c;
    Rig9 d; d.photo_stuck_V = 1.0f; d.run(200); d.toIgnition(); d.until(State::ABORT, 400);
    const bool fd = d.e.abortCause() == Abort::TORCH_FAULT && d.e.liftCommandTime() < 0.0;
    check(fa && fd && lb >= lc + 0.019 && lb <= lc + 0.022 && (b.o.fa1 & fa1::E1_2OO2),
          "v2.10 FA-1 (a): E1 only on P_torch AND photodiode (2oo2, same 3 ticks): photodiode invalid -> TORCH_FAULT at the gate, no lift; "
          "photodiode 20 ms late -> E1 20 ms later; photodiode stuck lit (never seen dark) -> TORCH_FAULT",
          fmt("lift nominal E0+%.0f ms, photodiode +20 ms -> E0+%.0f ms", lc * 1e3, lb * 1e3));
  }
  {   // (v210-5) FMEA FA-1 (b): torch supervision from E1 to E2. Both sensors dark for 5 ms -> TORCH_LOST: NC valve unlatched, pintle
      //          commanded closed (flight; accepted mission loss); 4 ms of both dark -> continues; only one sensor dark -> continues
    Rig9 a; a.toIgnition(); a.toE1(); a.run(10); a.torch_out = true; int na = 0;
    while (a.e.state() == State::IGNITION && na < 50) { a.tick(); ++na; }
    const bool fa = a.e.abortCause() == Abort::TORCH_LOST && !a.o.mv_latch && (a.o.fault_bits & fault::NO_IGNITION);
    Rig9 b; b.toIgnition(); b.toE1(); b.run(10); b.torch_out = true; b.run(4); b.torch_out = false; b.run(30);
    Rig9 c; c.toIgnition(); c.toE1(); c.run(10); c.photo_stuck_V = 0.10f; c.run(40);   // photodiode dark, P_torch lit
    Rig9 d; d.toIgnition(); d.toE1(); d.run(10); d.photo_stuck_V = 1.0f; d.torch_out = true; d.run(40);   // P_torch dark, photodiode lit
    check(fa && na >= 5 && na <= 7 && b.e.state() == State::IGNITION && c.e.state() == State::IGNITION && d.e.state() == State::IGNITION,
          "v2.10 FA-1 (b): both flame sensors dark >= 5 ms between E1 and E2 -> TORCH_LOST (NC valve unlatched, fault NO_IGNITION); 4 ms "
          "-> continues; one sensor dark -> continues",
          fmt("TORCH_LOST %.0f ms after the torch went out", na));
  }
  {   // (v210-6) REV-GNC-2 (2) FLAMEOUT_OPT: flight RUN, main-chamber view proven (lit 20 ms after the torch closed), Pc channel invalid ->
      //          open loop; photodiode dark 20 ms -> FLAMEOUT; photodiode lit -> RUN continues; torch-only view (dark once the torch closes)
      //          never arms -> no optical check (FMEA case)
    auto runPcLost = [&](Rig9& r) { r.toIgnition(); r.lightRun(3.0e5f); r.follow = true; r.run(300); r.follow = false;
                                    r.in.pc_raw_V = 0.02f; r.in.pc_Pa = -8.8e5f; r.run(50); };
    Rig9 a; runPcLost(a); const bool armed = (a.o.fa1 & fa1::FLAMEOUT_OPT) != 0; a.main_out = true; int na = 0;
    while (a.e.state() == State::RUN && na < 100) { a.tick(); ++na; }
    Rig9 b; runPcLost(b); b.run(300);
    Rig9 c; c.photo_torch_only = true; runPcLost(c); const bool c_armed = (c.o.fa1 & fa1::FLAMEOUT_OPT) != 0; c.run(300);
    check(armed && a.e.abortCause() == Abort::FLAMEOUT && na >= 20 && na <= 22 && b.e.state() == State::RUN && (b.o.fault_bits & fault::OPEN_LOOP) &&
              !c_armed && c.e.state() == State::RUN,
          "v2.10 REV-GNC-2 (2) FLAMEOUT_OPT: RUN with Pc invalid, view proven -> photodiode dark 20 ms -> FLAMEOUT; lit -> burn continues open "
          "loop; torch-only view never arms (no optical check, FMEA)",
          fmt("FLAMEOUT %.0f ms after the main flame went dark", na));
  }
  {   // (v210-7) REV-GNC-2 (1), LEAD CHANGELOG 168 drogue predicate RELEASE iff RUN AND b4 AND [(Pc valid AND >= 300 kPa) OR b7 OR (0xFFFF AND
      //          t >= t_E2 + 0.10 s)], latched; t_E2 from EVENT STATE (RUN). Chamber 2.6 bar abs (below 300 kPa: branch 1 never). Pc invalid
      //          (a) before E2 -> PC_SENSOR abort in IGNITION, never RUN, never released; (b) at E2 + 50 ms -> RUN open loop, b7 never set,
      //          release at E2 + 0.10 s (branch 3); (c) at E2 + 150 ms -> b7 latched at E2 + 0.10 s stays set, release at E2 + 0.10 s (b7).
      //          EVENT STATE at E2: t_ms = E2 tick, copy index in arg bits 13-15
    struct Res { bool run = false, rel = false, b7_inv = false; double t_rel = -1, t_e2 = -1, t_end = -1; int branch = 0, cause = 0; uint32_t ev_ms = 0; uint16_t ev_arg = 0; };
    auto drive = [&](int t_inv_ms, bool follow) {   // t_inv_ms: Pc invalid from E2 + t_inv_ms (negative: before E2, in IGNITION)
      Rig9 r; Res q; r.toIgnition(); r.toE1(); r.run(30); r.setPcAbs(2.6e5f); bool b7_after = false;
      bool latched = false; double t_e2 = -1;
      for (int k = 0; k < 600; ++k) {
        if (t_inv_ms < 0 && k == 3) { r.in.pc_raw_V = 0.02f; r.in.pc_Pa = -8.8e5f; }
        if (t_e2 >= 0 && t_inv_ms >= 0 && r.t - t_e2 >= t_inv_ms * 1e-3 - 1e-9) { r.in.pc_raw_V = 0.02f; r.in.pc_Pa = -8.8e5f; }
        r.tick();
        if (follow && t_e2 >= 0 && r.o.pc_valid) r.follow = true;
        if (r.in.pc_raw_V < 0.1f) r.follow = false;
        if (t_e2 >= 0 && r.t - t_e2 > 0.30) { b7_after = (r.o.tlm_flags & tlmf::RISE_HELD_T) != 0 && r.e.state() == State::RUN; break; }
        if (r.o.state_event && r.o.state == State::RUN) {
          t_e2 = r.t; q.t_e2 = r.t; q.ev_ms = r.o.state_t_ms;
          const can::Frame f = can::encodeStateEvent(r.o.state, r.o.abort_cause, r.o.state_t_ms, 1);
          q.ev_arg = static_cast<uint16_t>(f.d[6] | (f.d[7] << 8));
        }
        const bool run = r.o.state == State::RUN, b4 = (r.o.tlm_flags & tlmf::E2) != 0, b7 = (r.o.tlm_flags & tlmf::RISE_HELD_T) != 0;
        const float pc_kpa = r.o.pc_valid ? 0.001f * r.e.pcAbsFiltered() : -1.0f;
        int br = 0;
        if (run && b4) { if (r.o.pc_valid && pc_kpa >= 300.0f) br = 1; else if (b7) br = 2; else if (!r.o.pc_valid && t_e2 >= 0 && r.t + 1e-9 >= t_e2 + 0.10) br = 3; }
        if (!follow && !r.o.pc_valid && b7 && t_e2 >= 0) q.b7_inv = true;   // (b): b7 must never set once Pc is invalid
        if (!latched && br) { latched = true; q.rel = true; q.t_rel = r.t - t_e2; q.branch = br; }
        q.run = q.run || run;
        if (r.e.state() == State::ABORT) { q.cause = static_cast<int>(r.e.abortCause()); q.t_end = r.t - t_e2; break; }
      }
      if (follow) q.b7_inv = !b7_after;   // (c): b7 stays latched and RUN continues after the loss
      return q;
    };
    const Res a = drive(-1, false), b = drive(20, false), c = drive(150, true);
    const bool ev = b.ev_ms == static_cast<uint32_t>(std::llround(b.t_e2 * 1000.0)) && (b.ev_arg & 0xFFu) == static_cast<uint8_t>(State::RUN) &&
                    ((b.ev_arg >> 13) & 7u) == 1u && ((b.ev_arg >> 8) & 0x1Fu) == 0u;
    check(!a.run && !a.rel && b.run && b.rel && b.branch == 3 && std::fabs(b.t_rel - 0.10) < 0.0015 && !b.b7_inv &&
              c.rel && c.t_rel <= 0.10 + 0.0015 && !c.b7_inv && c.cause == 0 && ev,
          "v2.10 drogue predicate (CHANGELOG 168): Pc invalid before E2 -> no RUN, no release; at E2 + 20 ms (inside [E2, E2+0.10]) -> "
          "RUN open loop, b7 never set, release at E2 + 0.10 s (0xFFFF branch); at E2 + 150 ms (normal burn) -> released before by Pc or b7, "
          "b7 stays latched, RUN continues; EVENT STATE(RUN) t_ms = E2, copy index in arg b13-15",
          fmt("(b) release E2+%.0f ms branch %.0f", b.t_rel * 1e3, b.branch) + fmt(", (c) E2+%.0f ms branch %.0f", c.t_rel * 1e3, c.branch) +
              fmt("; EVENT t_ms %.0f arg %.0f (decimal)", (double)b.ev_ms, (double)b.ev_arg));
  }
  {   // (v210-8) both-valves-open cap (LEAD CHANGELOG 164 (2)): a schedule that never closes V1 (test hook) -> both close at once at
      //          kHbleedCap_s after V2 opened (EV_CAP, closure NOT CONFIRMED, BLEED_FAULT flag); flow reported = cap - open time + close time
    Rig9 r(true); toCoast(r); r.run(600); r.e.test_inhibit_purge_close = true; r.tick(Cmd::PURGE);
    int both = 0, ncap = 0; for (int k = 0; k < 4000 && r.e.state() == State::PURGE; ++k) {
      r.tick(); if (r.o.hbleed[0] && r.o.hbleed[1]) ++both; if (r.o.hbleed_event == hb::EV_CAP) ++ncap; if (r.o.hbleed2 & hb2::NOT_CONFIRMED) break; }
    check(ncap == 1 && !r.o.hbleed[0] && !r.o.hbleed[1] && std::abs(both - static_cast<int>(std::lround(1000 * kHbleedCap_s)) - 1) <= 2 &&
              (r.o.hbleed2 & hb2::NOT_CONFIRMED) && r.o.bleed_fault,
          "v2.10 hard cap: both bleed valves commanded open longer than 2.5 s + open + close time -> both close at once (EV_CAP), NOT CONFIRMED",
          fmt("both open %.0f ms (cap %.0f ms)", both, 1000 * kHbleedCap_s));
  }
  {   // (v210-9) LEAD RE-07 second re-zero, 20.6 s coast (REV-ELEC-1 RE-07/RE-11): drift steps after the first re-zero. +0.25 bar at coast
      //          + 5 s: the block before the RELIGHT re-zeroes (REZERO2, shift 0.25 bar), the chamber reads vented, no NOT_VENTED flag. +0.35 bar
      //          (> 0.30 bar from the pad zero): REZERO2_REJ; flight RELIGHT proceeds with NOT_VENTED, stand refused NOT_VENTED. Bleed fitted:
      //          the second re-zero ends before the PURGE command at coast + 17.7 s (E0 - 2.90 s) and the purge relight carries no flag
    auto drift = [](Rig9& r, float d, int coast_ms) { r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast(); r.run(5000); r.setPcG(d); r.run(coast_ms - 5000); };
    Rig9 a; drift(a, 0.25e5f, 20600);
    const bool first0 = a.n_rz_ev == 1 && std::fabs(a.o.rezero_shift_Pa) < 0.005e5f;
    a.tick(Cmd::RELIGHT); a.tick();
    const bool ok_a = first0 && a.e.state() != State::COAST && (a.o.fault2 & f2::REZERO2) && !(a.o.fault2 & f2::NOT_VENTED) &&
                      std::fabs(a.o.rezero_shift_Pa - 0.25e5f) < 0.005e5f && a.n_rz_ev == 2;
    Rig9 b; drift(b, 0.35e5f, 20600);
    b.tick(Cmd::RELIGHT); b.tick();
    const bool ok_b = b.e.state() != State::COAST && (b.o.fault2 & f2::REZERO2_REJ) && (b.o.fault2 & f2::NOT_VENTED) && !(b.o.fault2 & f2::REZERO2);
    Rig9 c(false, true); drift(c, 0.35e5f, 20600);
    c.tick(Cmd::RELIGHT); c.tick();
    const bool ok_c = c.e.state() == State::COAST && c.o.cmd_refused == refuse::NOT_VENTED;
    Rig9 p(true); drift(p, 0.25e5f, 17700);
    p.tick(Cmd::PURGE);
    const bool pz = p.e.state() == State::PURGE && (p.o.fault2 & f2::REZERO2) && !(p.o.fault2 & f2::NOT_VENTED);
    p.run(1000); p.tick(Cmd::RELIGHT); p.until(State::IGNITION, 3000);
    const bool ok_p = pz && p.e.state() == State::IGNITION && !(p.o.fault2 & f2::NOT_VENTED);
    check(ok_a && ok_b && ok_c && ok_p,
          "v2.10 second re-zero (LEAD RE-07), 20.6 s coast: +0.25 bar drift after the first re-zero -> REZERO2 at the RELIGHT, no NOT_VENTED; "
          "+0.35 bar -> REZERO2_REJ, flight NOT_VENTED flag + relight, stand refused; purge path re-zeroes at the PURGE command (E0 - 2.90 s)",
          fmt("A: shift %.3f bar; B flags 0x%02.0f", a.o.rezero_shift_Pa / 1e5, b.o.fault2));
  }
  {   // (v210-10) LEAD RE-08 case TCs: both valid at ARM (one invalid -> ARM refused OVER_TEMP); one lost in RUN -> the other carries the
      //           monitor (CASE_TC_DEGRADED, burn continues; a hot valid TC still aborts); both lost: stand -> OVER_TEMP abort, flight -> burn
      //           continues, relight refused CASE_HOT
    Rig9 a; a.in.tc_valid[1] = false; a.tick(Cmd::ARM); a.run(5);
    const bool arm_ref = a.e.state() != State::ARMED && a.e.abortCause() == Abort::OVER_TEMP;
    Rig9 b; b.toIgnition(); b.toE1(); b.run(30); b.setPcAbs(3.0e5f); b.until(State::RUN, 60); b.follow = true; b.run(200);
    b.in.tc_valid[0] = false; b.run(200);
    const bool one = b.e.state() == State::RUN && (b.o.fault2 & f2::CASE_TC_DEGRADED);
    b.in.tc_K[1] = 600.0f; b.run(260);   // kOverTempTime_s 0.2 s persistence
    const bool hot1 = b.e.abortCause() == Abort::OVER_TEMP;
    Rig9 f; f.toIgnition(); f.toE1(); f.run(30); f.setPcAbs(3.0e5f); f.until(State::RUN, 60); f.follow = true; f.run(200);
    f.in.tc_valid[0] = f.in.tc_valid[1] = false; f.run(300);
    const bool fl_cont = f.e.state() == State::RUN;
    f.burnToCoast(); f.run(1400); f.tick(Cmd::RELIGHT); f.tick();
    const bool fl_ref = f.e.state() == State::COAST && f.o.cmd_refused == refuse::CASE_HOT;
    Rig9 s(false, true); s.toIgnition(); s.toE1(); s.run(30); s.setPcAbs(3.0e5f); s.until(State::RUN, 60); s.follow = true; s.run(200);
    s.in.tc_valid[0] = s.in.tc_valid[1] = false; s.run(300);
    const bool st_ab = s.e.abortCause() == Abort::OVER_TEMP;
    check(arm_ref && one && hot1 && fl_cont && fl_ref && st_ab,
          "v2.10 case TCs (LEAD RE-08): ARM needs both valid; one lost -> CASE_TC_DEGRADED, the other still aborts when hot; both lost -> "
          "flight burn continues and the relight is refused CASE_HOT, stand OVER_TEMP abort",
          fmt("arm %.0f one %.0f hot %.0f", arm_ref, one, hot1) + fmt(" cont %.0f ref %.0f st %.0f", fl_cont, fl_ref, st_ab) +
          fmt(" (flight refusal code %.0f, stand state %.0f)", f.o.cmd_refused, static_cast<int>(s.e.state())));
  }
  {   // (v210-11) RE-17 tank lower bound 15 C, same validity logic as the 24 C top: 14 C at ARM -> TANK_COLD; no valid reading -> refused
      //           (TANK_HOT first, as v2.8); 16 C arms
    auto armAt = [](float tK, bool valid) {
      Rig9 r; r.in.ttank_wall_valid[0] = r.in.ttank_wall_valid[1] = valid; r.in.ttank_wall_K[0] = r.in.ttank_wall_K[1] = tK;
      r.in.ptank_valid = false; r.tick(Cmd::ARM); r.run(5); return std::make_pair(r.e.state(), r.e.abortCause()); };
    const auto c14 = armAt(287.15f, true), c16 = armAt(289.15f, true), cinv = armAt(290.0f, false);
    check(c14.second == Abort::TANK_COLD && c16.first == State::ARMED && cinv.first != State::ARMED,
          "v2.10 tank lower bound (RE-17): 14 C refused at ARM (TANK_COLD), 16 C arms, no valid tank temperature refused", "");
  }
  {   // (v210-13) LEAD CHANGELOG 172 (4) interlock guard band: wall and P_tank each against 24 C / Psat(24 C) minus the channel uncertainty.
      //           Uncalibrated P_tank (boot default): 51.01 bar abs refused at ARM (TANK_HOT), 50.01 arms; calibrated (B-PT-1 record):
      //           51.01 arms, 54.51 refused; wall 23.50 C refused, 23.40 C arms
    auto armAt = [](bool cal, float pg, float wK) {
      Rig9 r; r.e.ptank_cal_ok = cal; r.in.ptank_valid = true; r.in.ptank_Pa = pg;
      r.in.ttank_wall_valid[0] = r.in.ttank_wall_valid[1] = true; r.in.ttank_wall_K[0] = r.in.ttank_wall_K[1] = wK;
      r.tick(Cmd::ARM); r.run(5); return std::make_pair(r.e.state(), r.e.abortCause()); };
    const auto u51 = armAt(false, 49.9e5f, 290.0f), u50 = armAt(false, 48.9e5f, 290.0f);
    const auto c51 = armAt(true, 49.9e5f, 290.0f), c545 = armAt(true, 53.4e5f, 290.0f);
    const auto w235 = armAt(true, 45.0e5f, 296.65f), w234 = armAt(true, 45.0e5f, 296.55f);
    const bool ok = u51.second == Abort::TANK_HOT && u50.first == State::ARMED && c51.first == State::ARMED && c545.second == Abort::TANK_HOT &&
                    w235.second == Abort::TANK_HOT && w234.first == State::ARMED;
    check(ok, "v2.10 interlock guard band (LEAD 172 (4)): uncalibrated P_tank threshold 50.34 bar abs (51.01 refused, 50.01 arms); after "
              "B-PT-1 54.30 bar abs (51.01 arms, 54.51 refused); wall threshold 23.44 C (23.50 refused, 23.40 arms)",
          fmt("u51 %.0f u50 %.0f c51 %.0f", static_cast<int>(u51.first), static_cast<int>(u50.first), static_cast<int>(c51.first)) +
          fmt(" c545 %.0f w235 %.0f w234 %.0f", static_cast<int>(c545.first), static_cast<int>(w235.first), static_cast<int>(w234.first)));
  }
  {   // (v210-14) LEAD 172 (1) safing hold scope and NV: a stand NO_IGNITION and a stand abort in IGNITION with another cause open the
      //           hold; a boot with NV b4 restarts it (CLEAR_LOCKOUT refused until 960 s after the boot); NvJamRecord b4 set / clear.
      //           (The flight relight no-light: lockout without a hold, CLEAR accepted at once - test_v27 (3).)
    Rig9 s(false, true); s.toIgnition(); s.until(State::ABORT, 3000);
    const bool st_hold = s.e.abortCause() == Abort::NO_IGNITION && s.o.safing_hold && s.o.relight_lockout;
    Rig9 h(false, true); h.toIgnition(); h.toE1(); h.run(20);
    const State before = h.e.state(); h.tick(Cmd::ABORT); h.run(2);   // operator abort in IGNITION (Abort::CMD)
    const bool other = before == State::IGNITION && h.e.state() == State::ABORT && h.e.abortCause() != Abort::NO_IGNITION && h.o.safing_hold;
    Rig9 b; b.in.nv_safing_hold = true; b.in.nv_relight_lockout = true; b.tick();
    const bool boot_ev = b.o.safing_hold_event && b.o.safing_hold && b.o.safing_hold_left_s > 959.0f;
    b.tick(Cmd::CLEAR_LOCKOUT, cfg::kClearLockoutKey);
    const bool boot_ref = b.o.cmd_refused == refuse::SAFING_HOLD && !b.o.relight_lockout_clear;
    const double tb = b.t; while (b.t - tb < cfg::kNoLightSafingMin_s) b.tick();
    b.tick(Cmd::CLEAR_LOCKOUT, cfg::kClearLockoutKey);
    const bool boot_clr = b.o.relight_lockout_clear && !b.o.safing_hold;
    const NvJamRecord n1 = nvSafingHoldSet(nvJamBlank()); NvJamRecord d1; const NvJamStatus s1 = nvJamDecode(reinterpret_cast<const uint8_t*>(&n1), &d1);
    const NvJamRecord n2 = nvLockoutClear(n1); NvJamRecord d2; const NvJamStatus s2 = nvJamDecode(reinterpret_cast<const uint8_t*>(&n2), &d2);
    const bool nv = s1 == NvJamStatus::VALID && nvSafingHoldPending(s1, d1) && nvLockoutPending(s1, d1) && (d1.flags & 0x12u) == 0x12u &&
                    s2 == NvJamStatus::VALID && !nvSafingHoldPending(s2, d2) && !nvLockoutPending(s2, d2);
    check(st_hold && other && boot_ev && boot_ref && boot_clr && nv,
          "v2.10 safing hold scope (LEAD 172 (1)): stand NO_IGNITION and a stand abort in IGNITION (other cause) open the hold; a boot with NV "
          "b4 restarts it (CLEAR_LOCKOUT refused, accepted 960 s after the boot); NvJamRecord b4 set with b1, cleared by nvLockoutClear",
          fmt("stand %.0f other %.0f (cause %.0f)", st_hold, other, static_cast<int>(h.e.abortCause())) +
          fmt(" boot %.0f/%.0f/%.0f", boot_ev, boot_ref, boot_clr) + fmt(" nv %.0f", nv));
  }
  {   // (v210-15) LEAD CHANGELOG 175 (GNC rev2 decisions touching the ECU):
      //   (1) FC -> ECU ABORT path with Pc invalid in flight RUN: the 0x010 ABORT frame decodes (no sequence check) and acts on the NEXT
      //       1 kHz tick: state ABORT, cause CMD, MV holding magnet released on that tick, pintle commanded to 0 (rate-limited) and driven
      //       shut, EVENT STATE (ABORT | CMD << 8), log abort_cause. While Pc is invalid before the abort, TLM_FAST keeps state RUN and
      //       b4 (E2) with d2-d3 = 0xFFFF, and the E2 time stays the RUN-entry state event time (b7 is valid-channel only, unchanged).
      //   (4) ONE pad launch-commit bit: TLM_RELIGHT d6 b7 = Outputs::pc_commit_valid (valid this tick AND no latched PC_SENSOR); a single
      //       invalid tick clears it until DISARM/SAFE in SAFE; the decoder masks the refuse:: reason (d6 & 0x3F from LEAD 186 (2)).
      //   (3) TLM_FAST d4-d5 = crank-encoder lift [um] via can::tlmPintle, 0xFFFF with the encoder invalid.
    Rig9 r; r.toIgnition(); r.lightRun(3.0e5f); r.follow = true; r.run(20);   // Pc lost at E2 + ~20 ms (S14B shape): b7 can never latch
    const uint32_t t_e2 = r.o.state_t_ms;   // last state change = RUN entry (E2)
    r.follow = false; r.in.pc_raw_V = 0.10f; int bad = 0;
    for (int k = 0; k < 150; ++k) {
      r.tick();
      const can::Frame f = can::encodeTlmFast(1, r.o, r.e.pcAbsFiltered(), can::tlmPintle(r.o));
      if (!((f.d[2] | (f.d[3] << 8)) == 0xFFFF && (f.d[1] & 0x0F) == static_cast<uint8_t>(State::RUN) && (f.d[1] & tlmf::E2) &&
            !(f.d[1] & tlmf::RISE_HELD_T))) ++bad;
    }
    can::Decoder dec; Commands cc; const bool acc = dec.accept(can::encodeAbort(7, 0), cc) && cc.abort_frame;
    r.t += 1e-3; r.in.t_s = r.t; cc.fast_valid = true; cc.thrust_sp_N = r.thrust; r.e.step(r.in, cc, r.o); r.e.fillLog(r.in, r.o, r.lr);
    const bool same_tick = r.e.state() == State::ABORT && r.e.abortCause() == Abort::CMD && !r.o.mv_latch && r.o.state_event &&
                           r.lr.abort_cause == static_cast<uint8_t>(Abort::CMD);
    int n0 = -1; for (int k = 0; k < 30 && n0 < 0; ++k) { r.tick(); if (r.o.pintle_cmd_m <= 0.0f) n0 = k + 1; }
    check(acc && bad == 0 && same_tick && n0 > 0 && n0 <= 10 && t_e2 > 0,
          "v2.10 LEAD 175 (1): Pc invalid in flight RUN -> TLM_FAST state RUN + E2 kept with d2-d3 0xFFFF (b7 clear); FC ABORT frame acts "
          "on the next tick: ABORT/CMD, MV magnet released that tick, EVENT STATE, logged; pintle command 0 within 10 ms",
          fmt("bad TLM ticks %.0f, pintle command at 0 after %.0f ms", bad, n0) + fmt(", t_E2 %.0f ms", (double)t_e2));
    Rig9 a; a.run(100);
    auto bit = [&](const Rig9& q, bool* blk_ok) {
      const can::Frame f = can::encodeTlmRelight(3, q.o); can::TlmRelight d; const bool okd = can::decodeTlmRelight(f, &d);
      *blk_ok = okd && d.block == (q.o.relight_block & tlmr6::BLOCK_MASK) && d.pc_valid == q.o.pc_commit_valid;
      return okd && d.pc_valid;
    };
    bool k0 = false, k1 = false, k2 = false, k3 = false;
    const bool b0 = bit(a, &k0);
    a.in.pc_raw_V = 0.10f; a.tick(); const bool b1 = bit(a, &k1);
    a.setPcG(0.0f); a.run(20); const bool b2 = bit(a, &k2);
    a.tick(Cmd::SAFE); a.run(5); const bool b3 = bit(a, &k3);
    Rig9 p; p.run(10); p.pfollow = false; p.in.pintle_meas_m = 0.4321e-3f; p.tick();
    const can::Frame g1 = can::encodeTlmFast(1, p.o, p.e.pcAbsFiltered(), can::tlmPintle(p.o));
    p.in.pintle_meas_valid = false; p.tick();
    const can::Frame g2 = can::encodeTlmFast(2, p.o, p.e.pcAbsFiltered(), can::tlmPintle(p.o));
    const int um1 = g1.d[4] | (g1.d[5] << 8), um2 = g2.d[4] | (g2.d[5] << 8);
    check(b0 && !b1 && !b2 && b3 && k0 && k1 && k2 && k3 && um1 == 432 && um2 == 0xFFFF,
          "v2.10 LEAD 175 (4)/(3): pad launch-commit bit TLM_RELIGHT d6 b7 (valid; one invalid tick clears it until SAFE; decoder masks the "
          "reason) and TLM_FAST d4-d5 = encoder lift [um], 0xFFFF with the encoder invalid",
          fmt("bits %.0f%.0f", b0, b1) + fmt("%.0f%.0f", b2, b3) + fmt("; lift %.0f um, invalid %.0f", um1, um2));
  }
  {   // (v210-12) LEAD RE-04 lift clamp: map plant (Pc = map Pc of the ENCODER lift), pintle moving at 20 mm/s toward the command, 100 -> 500 N
      //           step. While the reference or the pintle travels the command never exceeds the trimmed map lift at (active setpoint +
      //           margin), LIFT_CLAMP is flagged, the trim does not move, and the plant Pc stays <= 28 bar abs
    Rig9 r; r.toIgnition(); r.lightRun(3.0e5f); r.follow = true; r.thrust = 100.f; r.run(1500); r.follow = false; r.pfollow = false;
    const float pt = r.in.ptank_Pa + 101325.f;
    float x = r.o.pintle_cmd_m, pcmax = 0.0f, viol = 0.0f; int ncl = 0; bool trim_fixed = true;
    float pc = ValveMap::pcForLift(x, pt), dbg = -1.0f, dbgx = 0.0f;
    r.thrust = 500.f;
    for (int k = 0; k < 600; ++k) {
      const float tr0 = r.e.pcc().trim();
      x += std::fmax(-0.8e-5f, std::fmin(0.8e-5f, r.o.pintle_cmd_m - x));   // 8 mm/s servo (a slow servo makes the clamp bind)
      r.in.pintle_meas_m = x;
      pc += (ValveMap::pcForLift(x, pt) - pc) * (1e-3f / 0.020f);            // 20 ms chamber + combustion lag (ASSUMED test plant)
      r.setPcAbs(pc); pcmax = std::fmax(pcmax, pc);
      r.tick();
      dbg = std::fmax(dbg, r.o.pintle_cmd_m - (1.0f + r.e.pcc().trim()) * ValveMap::lift(r.e.pcc().setpointActive() + kLiftClampMarginPc_Pa, pt, nullptr));
      dbgx = std::fmax(dbgx, std::fabs(r.o.pintle_cmd_m - x));
      if (r.o.fault2 & f2::LIFT_CLAMP) {
        ++ncl;
        const float lim = (1.0f + r.e.pcc().trim()) * ValveMap::lift(r.e.pcc().setpointActive() + kLiftClampMarginPc_Pa, pt, nullptr);
        viol = std::fmax(viol, r.o.pintle_cmd_m - lim);
        trim_fixed = trim_fixed && r.e.pcc().trim() == tr0;
      }
    }
    check(ncl > 20 && viol <= 1e-7f && trim_fixed && pcmax <= 28.0e5f && std::fabs(r.in.pc_Pa + 101325.f - r.e.pcc().setpointActive()) < 0.5e5f,
          "v2.10 lift clamp (LEAD RE-04): pintle lagging the command at 8 mm/s on a lagged map plant -> command <= trimmed map lift at (setpoint + "
          "margin) while travelling, LIFT_CLAMP flagged, trim held, plant Pc <= 28 bar abs, settles on the setpoint",
          fmt("clamp %.0f ms, plant max %.2f bar abs, final %.2f bar abs", ncl, pcmax / 1e5, (r.in.pc_Pa + 101325.f) / 1e5) +
          fmt("; command - limit max %.4f mm, pintle lag max %.3f mm", dbg * 1e3, dbgx * 1e3));
  }
  {   // (v210-16) LEAD CHANGELOG 181 (4): R2 ADOPTED in design; pcf_tmax 0.5 s (0.8 s NOT adopted); pcf_tmax, the 37.16 N threshold and the
      //           baseline reference are FC parameters. With Pc lost in flight RUN and R2 not met, the FC holds the drogue and commands ECU
      //           ABORT at t_E2 + pcf_tmax. ECU side, for loss onsets E2 + 5 / 10 ms (GNC R2 v2 onsets) and pcf_tmax 0.5 / 0.8 s (the ECU path
      //           does not depend on the FC value): t_E2 = EVENT STATE time of the RUN entry (o.state_t_ms); from the loss to the ABORT frame
      //           the ECU stays in RUN with no ECU-initiated transition (flight: Pc loss flagged, not aborted; photodiode lit), TLM_FAST keeps
      //           RUN + b4 with d2-d3 0xFFFF, PC_VALID clear; the ABORT frame at t_E2 + pcf_tmax acts on that tick (ABORT/CMD, MV magnet
      //           released, EVENT STATE, logged), pintle command 0 within 10 ms. Ideal lit plant (Rig9), no FC_THRUST frames.
    int bad = 0, nrun_bad = 0, worst_n0 = 0, ncase = 0, nok = 0; double dt_err_ms = 0.0;
    for (int onset_ms : {5, 10}) for (int tmax_ms : {500, 800}) {
      ++ncase;
      Rig9 r; r.toIgnition(); const bool lit = r.lightRun(3.0e5f); r.follow = true;
      const uint32_t t_e2 = r.o.state_t_ms;                   // RUN-entry tick = E2 (EVENT STATE t_ms on the FC clock)
      r.run(onset_ms - 1);
      r.follow = false; r.in.pc_raw_V = 0.10f;                // first invalid sample at E2 + onset_ms
      while (std::llround(r.t * 1000.0) + 1 < static_cast<long long>(t_e2) + tmax_ms) {
        r.tick();
        const can::Frame f = can::encodeTlmFast(1, r.o, r.e.pcAbsFiltered(), can::tlmPintle(r.o));
        if (r.e.state() != State::RUN) ++nrun_bad;
        if (!((f.d[2] | (f.d[3] << 8)) == 0xFFFF && (f.d[1] & 0x0F) == static_cast<uint8_t>(State::RUN) && (f.d[1] & tlmf::E2))) ++bad;
      }
      const bool pcv_clear = !r.o.pc_commit_valid;
      can::Decoder dec; Commands cc; const bool acc = dec.accept(can::encodeAbort(9, 0), cc) && cc.abort_frame;
      r.t += 1e-3; r.in.t_s = r.t; cc.fast_valid = true; cc.thrust_sp_N = r.thrust; r.e.step(r.in, cc, r.o); r.e.fillLog(r.in, r.o, r.lr);
      dt_err_ms = std::fmax(dt_err_ms, std::fabs(r.t * 1000.0 - (static_cast<double>(t_e2) + tmax_ms)));
      const bool same_tick = r.e.state() == State::ABORT && r.e.abortCause() == Abort::CMD && !r.o.mv_latch && r.o.state_event &&
                             r.lr.abort_cause == static_cast<uint8_t>(Abort::CMD);
      int n0 = -1; for (int k = 0; k < 30 && n0 < 0; ++k) { r.tick(); if (r.o.pintle_cmd_m <= 0.0f) n0 = k + 1; }
      worst_n0 = std::max(worst_n0, n0 < 0 ? 999 : n0);
      if (lit && t_e2 > 0 && pcv_clear && acc && same_tick && n0 > 0 && n0 <= 10) ++nok;
    }
    check(nok == ncase && bad == 0 && nrun_bad == 0 && dt_err_ms < 0.5,
          "v2.10 LEAD 181 (4): Pc lost at E2 + 5/10 ms in flight RUN, R2 not met -> FC ABORT at t_E2 + pcf_tmax (0.5 s adopted, 0.8 s "
          "checked): ECU stays RUN with E2 published and Pc 0xFFFF until the frame, PC_VALID clear; ABORT/CMD on that tick, MV magnet "
          "released, pintle command 0 within 10 ms",
          fmt("%.0f of %.0f cases; non-RUN ticks %.0f", nok, ncase, nrun_bad) + fmt(", bad TLM ticks %.0f, worst pintle-0 %.0f ms", bad, worst_n0) +
          fmt(", abort time error %.2f ms", dt_err_ms));
  }
  {   // (v210-17) LEAD CHANGELOG 186 (2) R2 command hold. While the FC reports the drogue attached (Cmd::DROGUE 1) and the Pc channel is
      //           invalid in flight RUN, the open-loop thrust command is held at kR2HoldThrust_N (62.5 N, the start level; never above the FC
      //           command) at once, until the FC reports the release (Cmd::DROGUE 0) or Pc is valid again; the command then returns at
      //           <= kStartRamp_Nps (the Pc setpoint slew kPcSpRateLimit_Paps applies throughout). Echo TLM_RELIGHT d6 b6; log tlm_flags
      //           b0 R2_HOLD / b1 DROGUE (TLM_FAST d1 carries b4-b7 only). Controls: no drogue report, stand, Pc valid -> no hold. Command
      //           handling: args other than 0/1 ignored, ARM resets to 'not attached', CAN round trip. Ideal lit plant (Rig9), FC thrust
      //           200 N; the FC side (deployment report, R2 test on F_meas, release) is SIL S17. Thrust read back from the active setpoint.
    auto toRun = [](Rig9& r, bool attach) {   // toIgnition() with the FC drogue report one tick after ARM (same tick count), 150 ms lit
      r.tick(Cmd::ARM); if (attach) r.tick(Cmd::DROGUE, 1); else r.tick();
      r.run(599); r.tick(Cmd::IGNITE); r.until(State::IGNITION, 4000);
      const bool lit = r.lightRun(3.0e5f); r.follow = true; r.run(150); return lit && r.e.state() == State::RUN;
    };
    auto F = [](const Rig9& r) { return thrust::thrustFromPcAbs(r.o.pc_sp_active_Pa, r.e.pamb_Pa); };
    auto spHold = [](const Rig9& r) { return std::fmax(kPcSpMinAbs_Pa, std::fmin(kPcSpMaxAbs_Pa, thrust::pcAbsFromThrust(kR2HoldThrust_N, r.e.pamb_Pa))); };
    // A: hold, then the FC release with Pc still invalid
    Rig9 r; r.thrust = 200.f; const bool runA = toRun(r, true);
    const float sp200 = r.o.pc_sp_active_Pa, f200 = F(r); const bool pre_ok = !r.o.r2_hold && r.o.drogue_attached && std::fabs(f200 - 200.f) < 0.5f;
    r.follow = false; r.in.pc_raw_V = 0.10f;                   // Pc channel failed low (flight: flagged, burn continues open loop)
    int nh = 0, nup = 0, n_reach = -1, nfast_bad = 0, nrl_bad = 0, nlog_bad = 0; float sp_prev = sp200;
    for (int k = 0; k < 300; ++k) {
      r.tick();
      if (r.o.r2_hold) ++nh;
      if (r.o.pc_sp_active_Pa > sp_prev + 1.0f) ++nup;
      sp_prev = r.o.pc_sp_active_Pa;
      if (n_reach < 0 && std::fabs(r.o.pc_sp_active_Pa - spHold(r)) < 100.0f) n_reach = k + 1;
      const can::Frame ff = can::encodeTlmFast(1, r.o, r.e.pcAbsFiltered(), can::tlmPintle(r.o));
      if ((ff.d[1] & 0x0F) != static_cast<uint8_t>(State::RUN)) ++nfast_bad;
      can::TlmRelight d;
      if (!(can::decodeTlmRelight(can::encodeTlmRelight(2, r.o), &d) && d.drogue && !d.pc_valid && d.block == (r.o.relight_block & tlmr6::BLOCK_MASK))) ++nrl_bad;
      if ((r.lr.tlm_flags & (tlmf::R2_HOLD | tlmf::DROGUE)) != (tlmf::R2_HOLD | tlmf::DROGUE)) ++nlog_bad;
    }
    const int n_slew = static_cast<int>(std::ceil((sp200 - spHold(r)) / (kPcSpRateLimit_Paps * 1e-3f))) + 2;
    const int n_ramp = static_cast<int>(std::floor((200.f - kR2HoldThrust_N) / (kStartRamp_Nps * 1e-3f)));
    const float f_held = F(r); const bool held = std::fabs(r.o.pc_sp_active_Pa - spHold(r)) < 1.0f && std::fabs(f_held - kR2HoldThrust_N) < 0.5f;
    float fprev = f_held, dmax = 0.0f; int n200 = -1, nh_after = 0;
    r.tick(Cmd::DROGUE, 0);                                   // FC: R2 met on F_meas -> release, then reports it
    const bool off0 = !r.o.r2_hold && !r.o.drogue_attached && !(r.lr.tlm_flags & (tlmf::R2_HOLD | tlmf::DROGUE));
    can::TlmRelight d1; const bool rel_echo = can::decodeTlmRelight(can::encodeTlmRelight(3, r.o), &d1) && !d1.drogue;
    for (int k = 0; k < 250; ++k) {
      if (k > 0) r.tick();
      const float f = F(r); dmax = std::fmax(dmax, f - fprev); fprev = f;
      if (n200 < 0 && std::fabs(f - 200.f) < 0.5f) n200 = k + 1;
      if (r.o.r2_hold) ++nh_after;
    }
    check(runA && pre_ok && nh == 300 && nup == 0 && n_reach > 0 && n_reach <= n_slew && n_reach < n_ramp && held && nfast_bad == 0 && nrl_bad == 0 &&
          nlog_bad == 0 && off0 && rel_echo && dmax <= 2.55f && n200 >= n_ramp && n200 <= n_ramp + 5 && nh_after == 0 && r.e.state() == State::RUN,
          "v2.10 LEAD 186 (2) R2 command hold: flight RUN at 200 N, drogue attached, Pc invalid -> command held at 62.5 N at once (setpoint "
          "slew only, faster than the start ramp) on every tick, RUN kept, TLM_RELIGHT d6 b6 and log b0/b1 set, TLM_FAST state nibble "
          "clean; DROGUE 0 -> hold off on that tick, command back to 200 N at <= 2.5 N/ms",
          fmt("hold level reached after %.0f ms (slew bound %.0f, ramp %.0f ms)", n_reach, n_slew, n_ramp) +
          fmt(", held %.2f N; release max step %.3f N/ms, 200 N after %.0f ms", f_held, dmax, n200));
    // B: the hold also ends when Pc is valid again (drogue still attached); C: no drogue report; S: stand; D: Pc valid; E: commands
    Rig9 v; v.thrust = 200.f; const bool runB = toRun(v, true);
    v.follow = false; v.in.pc_raw_V = 0.10f; v.run(60); const bool hB = v.o.r2_hold;
    float fpB = F(v), dB = 0.0f; int nhB = 0, n200B = -1; v.follow = true;
    for (int k = 0; k < 250; ++k) {
      v.tick(); if (v.o.r2_hold) ++nhB;
      const float f = F(v); dB = std::fmax(dB, f - fpB); fpB = f;
      if (n200B < 0 && std::fabs(f - 200.f) < 0.5f) n200B = k + 1;
    }
    const bool caseB = runB && hB && nhB == 0 && v.o.drogue_attached && dB <= 2.55f && n200B > 0 && v.e.state() == State::RUN;
    Rig9 n; n.thrust = 200.f; const bool runC = toRun(n, false); const float spC = n.o.pc_sp_active_Pa;
    n.follow = false; n.in.pc_raw_V = 0.10f; int nhC = 0;
    for (int k = 0; k < 200; ++k) { n.tick(); if (n.o.r2_hold || (n.lr.tlm_flags & (tlmf::R2_HOLD | tlmf::DROGUE))) ++nhC; }
    const bool caseC = runC && nhC == 0 && std::fabs(n.o.pc_sp_active_Pa - spC) < 100.0f && n.e.state() == State::RUN;
    Rig9 s(false, true); s.thrust = 200.f; const bool runS = toRun(s, true);
    s.follow = false; s.in.pc_raw_V = 0.10f; int nhS = 0;
    for (int k = 0; k < 400 && s.e.state() == State::RUN; ++k) { s.tick(); if (s.o.r2_hold) ++nhS; }
    const bool caseS = runS && nhS == 0 && s.e.abortCause() == Abort::PC_SENSOR && s.o.drogue_attached;
    Rig9 p; p.thrust = 200.f; const bool runD = toRun(p, true); int nhD = 0;
    for (int k = 0; k < 200; ++k) { p.tick(); if (p.o.r2_hold) ++nhD; }
    const bool caseD = runD && nhD == 0 && p.o.drogue_attached && std::fabs(F(p) - 200.f) < 0.5f;
    Rig9 q; q.tick(Cmd::DROGUE, 1); const bool e1 = q.o.drogue_attached;        // SAFE: accepted in any state
    q.tick(Cmd::DROGUE, 2); const bool e2 = q.o.drogue_attached;                 // other values ignored
    q.tick(Cmd::ARM); const bool e3 = q.e.state() == State::ARMED && !q.o.drogue_attached;   // an accepted ARM resets it
    q.tick(Cmd::DROGUE, 1); q.tick(Cmd::DROGUE, 0); q.tick(Cmd::DROGUE, 0xFFFF); const bool e4 = !q.o.drogue_attached;
    can::Decoder dec; Commands cc;
    const bool e5 = dec.accept(can::encodeCmdState(4, Cmd::DROGUE, 1), cc) && cc.state_valid && cc.cmd == Cmd::DROGUE && cc.arg == 1;
    check(caseB && caseC && caseS && caseD && e1 && e2 && e3 && e4 && e5,
          "v2.10 LEAD 186 (2) R2 hold boundaries: Pc valid again -> hold off on that tick, ramp <= 2.5 N/ms; no drogue report -> no hold "
          "(open loop at 200 N); stand -> no hold, PC_SENSOR abort; Pc valid -> no hold; DROGUE accepted in SAFE, args other than 0/1 "
          "ignored, ARM resets, CMD_STATE round trip",
          fmt("B %.0f (ramp max %.3f N/ms, 200 N after %.0f ms)", caseB, dB, n200B) + fmt("; C %.0f S %.0f D %.0f", caseC, caseS, caseD) +
          fmt("; E %.0f%.0f%.0f", e1, e2, e3) + fmt("%.0f%.0f", e4, e5));
  }
