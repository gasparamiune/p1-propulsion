// v2.11 unit tests, part b (2026-10-20): LEAD 216 (2) R2 hold backstop / lost DROGUE 0, 216 (9) lift-commanded R2 hold + R2-23, 216 (4) BASE_AMB per location,
// 216 (7) cold-rule ARM margin + PREPRESS safe exit, LEAD 2026-10-20T21:46:49Z items 3 / 5 (stand T0 ARM rule, case-TC ARM limits),
// 166 (3) / 216 (5) hardware both-open timer constants. Included after test_v211.inc (Rig9, toCoast, check, fmt, fmtv in scope).
// Rig9 is a LOGIC rig (ideal plant, TEST VALUES, not measurements); the plant-level evidence is SIL S6 / S10 / S12 / S17 (sil_main).
{
  {   // (v211b-1) LEAD 21:46:49Z item 3 + 21:51:07Z STAND T0 ARM rule and item 5 case-TC ARM limits. Stand: TC1 or TC2 above kCaseStandArmMax_K
      //           (297.15 K, 24 C) -> ARM refused CASE_WARM_STAND (its own code); 0.5 K below -> ARMED. Flight: no T0 rule (300 K -> ARMED).
      //           Both modes: TC1 / TC2 above the start limit kCaseRelightMax_K (403.15 K) -> OVER_TEMP; TC3 above the nozzle-holder limit
      //           kNozzleHolderOverTemp_K (523.15 K) -> OVER_TEMP; TC3 at 450 K -> ARMED (v2.8-v2.10 compared TC3 with the case abort)
    auto armWith = [](bool stand, int idx, float T) {
      Rig9 r(false, stand); r.in.tc_K[idx] = T; r.tick(Cmd::ARM);
      return std::make_pair(r.e.state(), r.e.abortCause());
    };
    const auto s1 = armWith(true, 0, kCaseStandArmMax_K + 0.5f), s2 = armWith(true, 1, kCaseStandArmMax_K + 0.5f);
    const auto s3 = armWith(true, 0, kCaseStandArmMax_K - 0.5f), f1 = armWith(false, 0, 300.0f);
    const auto f2 = armWith(false, 0, kCaseRelightMax_K + 1.0f), f3 = armWith(false, 1, kCaseRelightMax_K + 1.0f);
    const auto s4 = armWith(true, 1, kCaseRelightMax_K + 1.0f);
    const auto f4 = armWith(false, 2, kNozzleHolderOverTemp_K + 1.0f), f5 = armWith(false, 2, 450.0f);
    const bool stand_ok = s1.first == State::SAFE && s1.second == Abort::CASE_WARM_STAND && s2.first == State::SAFE &&
                          s2.second == Abort::CASE_WARM_STAND && s3.first == State::ARMED;
    const bool flight_ok = f1.first == State::ARMED && f2.first == State::SAFE && f2.second == Abort::OVER_TEMP && f3.second == Abort::OVER_TEMP &&
                           s4.second == Abort::OVER_TEMP && f4.first == State::SAFE && f4.second == Abort::OVER_TEMP && f5.first == State::ARMED;
    check(stand_ok && flight_ok && kCaseStandArmMax_K == 297.15f && kCaseRelightMax_K == 403.15f && kCaseOverTemp_K == 423.15f &&
              std::string(abortName(Abort::CASE_WARM_STAND)) == "CASE_WARM_STAND",
          "v2.11 LEAD 21:46:49Z items 3/5: stand ARM refused CASE_WARM_STAND with TC1 or TC2 > 297.15 K (24 C), accepted 0.5 K below; flight "
          "has no T0 rule (300 K ARMED); TC1/TC2 > start limit 403.15 K -> OVER_TEMP (both modes); TC3 > 523.15 K -> OVER_TEMP, TC3 450 K ARMED",
          fmtv("stand %s/%s/%s, flight 300 K %s, TC1 404 K %s, TC3 524 K %s, TC3 450 K %s", abortName(s1.second), abortName(s2.second),
               stateName(s3.first), stateName(f1.first), abortName(f2.second), abortName(f4.second), stateName(f5.first)));
  }

  // flight pad start with the FC drogue report one tick after ARM (as v210-17), 150 ms lit at the FC command
  auto toRunD = [](Rig9& r, bool attach) {
    r.tick(Cmd::ARM); if (attach) r.tick(Cmd::DROGUE, 1); else r.tick();
    r.run(599); r.tick(Cmd::IGNITE); r.until(State::IGNITION, 4000);
    const bool lit = r.lightRun(3.0e5f); r.follow = true; r.run(150); return lit && r.e.state() == State::RUN;
  };
  auto Fsp = [](const Rig9& r) { return thrust::thrustFromPcAbs(r.o.pc_sp_active_Pa, r.e.pamb_Pa); };

  {   // (v211b-2) LEAD 216 (2)(b)/(c) LOST DROGUE 0: flight RUN at 200 N, drogue attached, Pc lost at E2 + 0.15 s; the FC's DROGUE 0 never
      //           arrives (lost frame). The ECU ends the hold at E2 + kR2HoldBackstop_s (0.85 s = R2 v2 window 0.8 s + 2 FC frames 20 ms +
      //           link latency 10 ms) on its own: one R2_BACKSTOP event (arg = hold ticks), log/TLM tlm_flags b2 R2_BACKSTOP, no hold after
      //           it in this burn (Pc still invalid), the command returns to 200 N at <= the start ramp, RUN kept (open loop). Control: the
      //           FC's DROGUE 0 at E2 + 0.40 s ends the hold then and no backstop event follows. v2.10: the hold stayed for the rest of the burn
    Rig9 r; r.thrust = 200.f; const bool run = toRunD(r, true);
    const double tE2 = r.e.tLit();
    r.follow = false; r.in.pc_raw_V = 0.10f;
    int nh = 0, nev = 0, ev_ticks = -1, nh_after = 0; double t_end = -1.0; bool flag_seen = false; float fprev = Fsp(r), dmax = 0.0f; int n200 = -1;
    for (int k = 0; k < 1500 && r.e.state() == State::RUN; ++k) {
      r.tick();
      if (r.o.r2_hold) { ++nh; if (t_end > 0.0) ++nh_after; }
      else if (nh > 0 && t_end < 0.0) t_end = r.t;
      if (r.o.r2_backstop_event) { ++nev; ev_ticks = r.o.r2_hold_ticks; }
      if (r.lr.tlm_flags & tlmf::R2_BACKSTOP) flag_seen = true;
      if (t_end > 0.0) { const float f = Fsp(r); dmax = std::fmax(dmax, f - fprev); if (n200 < 0 && std::fabs(f - 200.f) < 0.5f) n200 = static_cast<int>(std::lround((r.t - t_end) * 1e3)); }
      fprev = Fsp(r);
    }
    const double t_rel = t_end - tE2;
    const bool a_ok = run && nev == 1 && t_end > 0.0 && std::fabs(t_rel - kR2HoldBackstop_s) <= 1.5e-3 && r.e.r2Backstop() && flag_seen &&
                      nh_after == 0 && ev_ticks == nh && r.e.state() == State::RUN && dmax <= 2.55f && n200 > 0 &&
                      std::fabs(kR2HoldBackstop_s - (kR2WindowMax_s + 2.0f * kFcFramePeriod_s + kFcLinkLatency_s)) < 1e-6f;
    Rig9 c; c.thrust = 200.f; const bool runc = toRunD(c, true);
    const double tE2c = c.e.tLit();
    c.follow = false; c.in.pc_raw_V = 0.10f;
    int nevc = 0; double t_endc = -1.0; bool sent = false;
    for (int k = 0; k < 1500 && c.e.state() == State::RUN; ++k) {
      if (!sent && c.t - tE2c >= 0.40 - 1e-9) { c.tick(Cmd::DROGUE, 0); sent = true; } else c.tick();
      if (!c.o.r2_hold && t_endc < 0.0 && sent) t_endc = c.t;
      if (c.o.r2_backstop_event) ++nevc;
    }
    const bool c_ok = runc && sent && nevc == 0 && t_endc > 0.0 && std::fabs(t_endc - tE2c - 0.40) <= 2.5e-3 && !c.e.r2Backstop();
    check(a_ok && c_ok,
          "v2.11 LEAD 216 (2)(b)/(c) lost DROGUE 0: hold ends at E2 + 0.85 s (0.8 s window + 2 x 20 ms FC frames + 10 ms latency) by the "
          "ECU backstop, one R2_BACKSTOP event (arg = hold ticks), tlm_flags b2, no hold after it, command back to 200 N at <= 2.5 N/ms, "
          "RUN kept; with the FC's DROGUE 0 at E2 + 0.40 s the hold ends then and no backstop fires",
          fmtv("backstop at E2 + %.4f s (bound %.3f), events %d, hold ticks %d / %d, after %d, max step %.3f N/ms, 200 N after %d ms; "
               "control release E2 + %.4f s, events %d", t_rel, kR2HoldBackstop_s, nev, ev_ticks, nh, nh_after, dmax, n200, t_endc - tE2c, nevc));
    // the backstop is per burn: Pc VALID and the FC's DROGUE 0 lost -> it still fires at E2 + 0.85 s (drogue reported attached; no hold
    // was active, the event is the record); the next RUN entry (relight) clears it
    Rig9 g; g.thrust = 200.f; const bool rung = toRunD(g, true);
    int nevg = 0; for (int k = 0; k < 1000; ++k) { g.tick(); if (g.o.r2_backstop_event) ++nevg; }
    const bool bs1 = g.e.r2Backstop() && nevg == 1 && g.o.r2_hold_ticks == 0;
    const bool coast = g.burnToCoast(200);
    g.run(600); g.tick(Cmd::RELIGHT); g.toE1(); g.run(30); g.setPcAbs(3.0e5f); g.until(State::RUN, 60);
    const bool bs2 = g.e.state() == State::RUN && !g.e.r2Backstop() && g.o.r2_hold_ticks == 0;
    check(rung && bs1 && coast && bs2,
          "v2.11 R2 backstop is per burn: with Pc valid and DROGUE 0 lost it still fires at E2 + 0.85 s (one event, no hold ticks); cleared at "
          "the next RUN entry (relight)",
          fmtv("first burn backstop %d (events %d), coast %d, relight RUN with backstop clear %d", (int)bs1, nevg, (int)coast, (int)bs2));
  }

  {   // (v211b-3) LEAD 216 (9) LIFT-COMMANDED HOLD at kR2HoldLift_m (0.21776 mm, Combustion v2.4b start-level lift at the A1 relight state,
      //           OI-43; CF-3 measures it): during the hold the pintle command goes to the hold lift (rate-limited) whatever the map says; the
      //           setpoint is parked (bumpless return). R2-23 statement: ONE HIGH over-range tick (4.90 V) in flight RUN with the drogue
      //           attached is Pc-invalid for the FC too, so it engages the hold for exactly that tick (non-sticky, LEAD 203 (1)(a)); cost = the
      //           return to the FC command at <= the start ramp
    Rig9 r; r.thrust = 200.f; const bool run = toRunD(r, true);
    r.follow = false; r.in.pc_raw_V = 0.10f;
    float x_last = 0.0f; int n_at = -1;
    for (int k = 0; k < 300; ++k) {
      r.tick(); x_last = r.o.pintle_cmd_m;
      if (n_at < 0 && std::fabs(r.o.pintle_cmd_m - kR2HoldLift_m) < 1e-7f) n_at = k + 1;
    }
    const bool lift_ok = run && r.o.r2_hold && std::fabs(x_last - kR2HoldLift_m) < 1e-7f && n_at > 0 && n_at < 200;
    // R2-23: one over-range tick after the settle, drogue attached, Pc otherwise valid
    Rig9 q; q.thrust = 200.f; const bool runq = toRunD(q, true); q.follow = true; q.run(250);
    const float pc_run = q.in.pc_Pa; q.follow = false;
    q.in.pc_raw_V = 4.90f; q.in.pc_Pa = 76.0e5f; q.tick();
    const bool h_on = q.o.r2_hold && !q.o.pc_valid && q.o.pc_overrange && !(q.o.fault_bits & fault::PC_SENSOR);
    q.in.pc_Pa = pc_run; q.in.pc_raw_V = 0.5f + 4.f * pc_run / cfg::kPcXdcrFs_Pa; q.follow = true; q.tick();
    const bool h_off = !q.o.r2_hold && q.o.pc_valid;
    int n_back = -1; for (int k = 0; k < 200; ++k) { q.tick(); if (n_back < 0 && std::fabs(Fsp(q) - 200.f) < 0.5f) n_back = k + 2; }
    const bool r223 = runq && h_on && h_off && n_back > 0 && n_back <= static_cast<int>((200.f - kR2HoldThrust_N) / (kStartRamp_Nps * 1e-3f)) + 6 &&
                      q.e.state() == State::RUN && q.o.r2_hold_ticks == 1;
    check(lift_ok && r223,
          "v2.11 LEAD 216 (9) lift-commanded R2 hold: pintle command = kR2HoldLift_m 0.21776 mm during the hold (rate-limited approach); "
          "R2-23: one HIGH over-range tick after E2 with the drogue attached engages the hold on that tick only (no PC_SENSOR latch), "
          "the FC command returns at the start ramp",
          fmtv("hold lift reached after %d ms (%.5f mm); over-range tick: hold %d -> %d, ticks %d, 200 N again after %d ms", n_at, x_last * 1e3,
               (int)h_on, (int)!h_off, q.o.r2_hold_ticks, n_back));
  }

  // pressure for a given Tsat on the ECU table (bisection, ABSOLUTE)
  auto pForTsat = [](float T) {
    float lo = 30.0e5f, hi = 60.0e5f;
    for (int i = 0; i < 60; ++i) { const float m = 0.5f * (lo + hi); float tt = 0.0f; n2o::tsatK(m, &tt); if (tt < T) lo = m; else hi = m; }
    return 0.5f * (lo + hi);
  };

  {   // (v211b-4) LEAD 216 (7) cold-rule ARM margin: ARM needs the coldest valid tank estimate >= kTankIgnMin_K + kTankColdArmMargin_K.
      //           Walls (DS18B20) at 15 C + 0.20 K, Tsat(P_tank) warm -> ARM refused TANK_COLD; walls at 15 C + margin + 0.05 K -> ARMED;
      //           Tsat(P_tank) at 15 C + 0.20 K with the walls warm -> refused (the coldest estimate decides)
    auto armT = [&](float tw, float tsat) {
      Rig9 r; r.in.ttank_wall_K[0] = r.in.ttank_wall_K[1] = tw; r.in.ptank_Pa = pForTsat(tsat) - 101325.f; r.in.pfeed_Pa = r.in.ptank_Pa - 2.0e5f;
      r.run(300); r.tick(Cmd::ARM);
      return std::make_pair(r.e.state(), r.e.abortCause());
    };
    const auto a = armT(kTankIgnMin_K + 0.20f, 291.15f), b = armT(kTankIgnMin_K + kTankColdArmMargin_K + 0.05f, 291.15f);
    const auto c = armT(291.15f, kTankIgnMin_K + 0.20f), d = armT(291.15f, kTankIgnMin_K + kTankColdArmMargin_K + 0.05f);
    check(a.first == State::SAFE && a.second == Abort::TANK_COLD && b.first == State::ARMED && c.first == State::SAFE &&
              c.second == Abort::TANK_COLD && d.first == State::ARMED && kTankColdArmMargin_K >= 0.30f,
          "v2.11 LEAD 216 (7) cold ARM margin: coldest tank estimate 15 C + 0.20 K -> ARM refused TANK_COLD (wall or Tsat(P_tank)); 15 C + "
          "margin + 0.05 K -> ARMED",
          fmtv("margin %.2f K: wall +0.20 %s, wall +%.2f %s, Tsat +0.20 %s, Tsat +%.2f %s", kTankColdArmMargin_K, abortName(a.second),
               kTankColdArmMargin_K + 0.05f, stateName(b.first), abortName(c.second), kTankColdArmMargin_K + 0.05f, stateName(d.first)));
  }

  {   // (v211b-5) LEAD 216 (7) PREPRESS SAFE EXIT: pad ARM, manual PREPRESS (valve opened, line primed), then the tank estimate falls below
      //           15 C (P_tank lowered, TEST VALUE standing for the PREPRESS Tsat drop) and IGNITE is refused TANK_COLD: the ECU leaves
      //           PREPRESS on the refusal tick (ARMED, MV unlatched, pintle seated) and the CLOSED switch is seen within kMvCloseConfirm_s
      //           (Rig9 switch model; the plant closing time is SIL S10 cold_rule). Same exit on a CASE_HOT refusal (TC1 at the start limit
      //           + 2 K). v2.10 stayed in PREPRESS with the MV open up to kPrepressHoldMax_s (60 s)
    auto exitOn = [&](int kind, int* close_ms, bool* latch_drop, uint8_t* why) {
      Rig9 r; r.in.ttank_wall_K[0] = r.in.ttank_wall_K[1] = 291.15f;
      r.tick(Cmd::ARM); r.run(600); r.tick(Cmd::PREPRESS);
      if (r.e.state() != State::PREPRESS) return false;
      r.run(1500);                                          // primed, cocked, waiting (manual PREPRESS: no auto-ignite)
      if (r.e.state() != State::PREPRESS || !r.o.mv_latch) return false;
      if (kind == 0) { r.in.ttank_wall_K[0] = r.in.ttank_wall_K[1] = kTankIgnMin_K - 0.10f; r.run(5); }
      else { r.in.tc_K[0] = kCaseRelightMax_K + 2.0f; r.run(2); }
      r.tick(Cmd::IGNITE);
      *why = r.o.cmd_refused; *latch_drop = !r.o.mv_latch;
      const bool armed_now = r.e.state() == State::ARMED && r.e.prepressExits() == 1;
      int n = 0; while (!r.in.mv_closed_sw && n < 1000) { r.tick(); ++n; }
      *close_ms = r.in.mv_closed_sw ? n : -1;
      r.run(700);
      return armed_now && r.e.state() == State::ARMED && !(r.o.fault_bits & fault::MV) && r.o.pintle_cmd_m == 0.0f;
    };
    int cm0 = -1, cm1 = -1; bool ld0 = false, ld1 = false; uint8_t w0 = 0, w1 = 0;
    const bool e0 = exitOn(0, &cm0, &ld0, &w0), e1 = exitOn(1, &cm1, &ld1, &w1);
    check(e0 && e1 && ld0 && ld1 && w0 == refuse::TANK_COLD && w1 == refuse::CASE_HOT && cm0 >= 0 && cm0 <= 500 && cm1 >= 0 && cm1 <= 500,
          "v2.11 LEAD 216 (7) PREPRESS safe exit: IGNITE refused in PREPRESS (TANK_COLD; CASE_HOT) -> ARMED on the refusal tick, MV unlatched, "
          "pintle seated, CLOSED switch within kMvCloseConfirm_s 0.5 s, no MV fault (never a wait with the MV open)",
          fmtv("TANK_COLD: refuse %u, latch dropped %d, CLOSED after %d ms; CASE_HOT: refuse %u, latch dropped %d, CLOSED after %d ms", (unsigned)w0,
               (int)ld0, cm0, (unsigned)w1, (int)ld1, cm1));
  }

  {   // (v211b-6) LEAD 166 (3) / 216 (5) hardware both-commanded-open timer (DESIGN constants; behaviour in SIL S12 hw_timer) and the 230 (3)
      //           purge basis: T_hw,min after the firmware cap + 1 tick, the scheduled command span below both; physical flow at the cap and
      //           at T_hw,max on the one 29.25 g/s basis and the 31.06 g/s warm end
    const float thw_min = kHbleedHwBothNom_s * (1.0f - kHbleedHwBothErr), thw_max = kHbleedHwBothNom_s * (1.0f + kHbleedHwBothErr);
    const float span = kPurgeFlow_s + kHbleedOpenTime_s - kHbleedCloseTime_s, dtv = kHbleedCloseTime_s - kHbleedOpenTime_s;
    const float m_cap = kPurgeMdotBasis_kgps * (kHbleedCap_s + dtv), m_cap_w = kPurgeMdotWarm_kgps * (kHbleedCap_s + dtv);
    const float m_hw = kPurgeMdotBasis_kgps * (thw_max + dtv), m_hw_w = kPurgeMdotWarm_kgps * (thw_max + dtv);
    check(thw_min >= kHbleedCap_s + kDt_s && span + kDt_s < kHbleedCap_s && m_cap <= 0.0761f && m_hw < 0.096f && m_hw_w < 0.096f,
          "v2.11 hardware both-open timer (DESIGN): T_hw,min after the firmware cap + 1 tick (the firmware acts first, the 2.45 s scheduled "
          "span is never cut); hardware residual below the PURGE_WIN 96-104 g bound; 230 (3) basis 76.05 g at the cap",
          fmtv("T_hw %.3f s (min %.3f, max %.3f), cap %.3f s, span %.3f s; at the cap %.2f g (basis) / %.2f g (warm); at T_hw,max %.1f g / %.1f g",
               kHbleedHwBothNom_s, thw_min, thw_max, kHbleedCap_s, span, 1e3 * m_cap, 1e3 * m_cap_w, 1e3 * m_hw, 1e3 * m_hw_w));
  }

  {   // (v211b-7) LEAD 216 (4) (R2-04, 203 (5) RESTATED per location), P0 offsets at E0 (check 0.7 bar): pad first start and stand first start
      //           with P0 -0.8 bar g -> BASE_AMB, the lift is REFUSED (PC_SENSOR, no pintle command, MV closed by the abort); stand P0 +0.8
      //           bar g -> BASE_HIGH refusal as on the pad; stand P0 -0.6 bar g -> no flag, lift commanded (control). A1 relight (flight, lit
      //           since boot) P0 -0.8 bar g -> P0 := 0 (ambient), BASE_AMB, the lift IS commanded and the A7 HOLD low edge (P0 - 0.3 bar for
      //           kA7Time_s) aborts PC_SENSOR before any light (v2.10 path kept; the lead set no A1 target, the outcome is stated)
    struct BR { bool lift = true, mv_closed = false; Abort cause = Abort::NONE; unsigned det = 0, f2b = 0; float pin = 0.0f; int n = 0; };
    auto groundStart = [&](bool stand, float pg) {
      BR b; Rig9 r(false, stand); r.torch_delay = 40; r.toIgnition(); r.setPcG(pg);
      while (r.e.state() == State::IGNITION && b.n < 400) { r.tick(); ++b.n; b.pin = std::max(b.pin, r.o.pintle_cmd_m); }
      b.lift = r.e.liftCommandTime() >= 0.0; b.cause = r.e.abortCause(); b.det = r.o.ign_det; b.f2b = r.o.fault2;
      r.run(700); b.mv_closed = r.in.mv_closed_sw && !r.o.mv_latch;
      return b;
    };
    const BR pl = groundStart(false, -0.8e5f), sl = groundStart(true, -0.8e5f), sh = groundStart(true, 0.8e5f), sk = groundStart(true, -0.6e5f);
    auto refusedLow = [](const BR& b) { return !b.lift && b.cause == Abort::PC_SENSOR && (b.det & det::BASE_AMB) && !(b.f2b & f2::BASE_HIGH) && b.pin <= 0.0f && b.mv_closed; };
    const bool g_ok = refusedLow(pl) && refusedLow(sl) && !sh.lift && sh.cause == Abort::PC_SENSOR && (sh.f2b & f2::BASE_HIGH) && sh.pin <= 0.0f &&
                      sh.mv_closed && sk.lift && !(sk.det & det::BASE_AMB) && !(sk.f2b & f2::BASE_HIGH);
    Rig9 a; a.toIgnition(); a.lightRun(3.0e5f); a.burnToCoast(); a.run(1400);
    a.tick(Cmd::RELIGHT); a.torch_delay = 40; a.until(State::IGNITION, 4000); a.setPcG(-0.8e5f);
    int na = 0; while (a.e.liftCommandTime() < 0.0 && a.e.state() == State::IGNITION && na < 400) { a.tick(); ++na; }
    const double e1 = a.e.liftCommandTime();
    a.tick();
    const bool amb = (a.o.ign_det & det::BASE_AMB) && std::fabs(a.o.ign_ref_Pa) < 1.0f && !(a.o.fault2 & f2::BASE_HIGH);
    int nb = 0; while (a.e.state() == State::IGNITION && nb < 400) { a.tick(); ++nb; }
    const double t_ab = a.t - e1;
    a.run(700);
    const bool a_ok = e1 > 0.0 && amb && a.e.abortCause() == Abort::PC_SENSOR && !(a.o.ign_det & det::LIT) && t_ab >= kA7Time_s - 1e-6 &&
                      t_ab <= kA7Time_s + 0.010 && a.in.mv_closed_sw;
    check(g_ok && a_ok,
          "v2.11 LEAD 216 (4) BASE_AMB per location: pad and stand P0 -0.8 bar g -> lift refused PC_SENSOR (BASE_AMB, no pintle command, MV "
          "closed); stand +0.8 bar g -> BASE_HIGH refusal; stand -0.6 bar g -> lift; A1 relight -0.8 bar g -> P0 := 0, lift, A7 HOLD "
          "PC_SENSOR before any light, MV closed",
          fmtv("refusal at E0 + %d ms (pad low) / %d ms (stand low) / %d ms (stand high); A1: lift at E0 + %d ms, PC_SENSOR %.1f ms after the lift",
               pl.n, sl.n, sh.n, na, 1e3 * t_ab));
  }
}
