// ------------------------------------------------------------- v2.8 lead decisions 2026-10-13 (relight path, windows R1-R4, S1, over-thrust,
// mode strap, case/bay temperature, TLM_RELIGHT): unit tests. Included inside the v2.5 Rig5 block of test_core.cpp (Rig5, check, fmt, hex in
// scope) after test_v27.inc. Rigs are ideal (instant pintle follower, ideal torch: P_torch reads 2.0 bar g one tick after both torch valves
// open). Rig times: E0 = IGNITION entry tick, E1 = ignition-lift command (torch confirmation), W counted from E1. The SIL (sil_main.cpp) runs
// the same logic against the plant models. TEST VALUES are not measurements.
{   // (1) LEAD 2026-10-13: the ignition-lift command is issued AT the torch confirmation (E1); the pintle stays seated before it; the lift
    //     is the lift-vs-T_tank table value (default 0.2039 mm both rows)
  Rig5 r; r.toIgnition(); const double t0 = r.t;
  int n = 0, n_ok = -1, n_lift = -1; bool seated_before = true;
  while (n < 100 && r.e.state() == State::IGNITION) {
    r.tick(); ++n;
    if (n_ok < 0 && r.o.torch_ok) n_ok = n;
    if (n_lift < 0 && r.o.pintle_cmd_m > 0.0f) n_lift = n;
    if (n_ok < 0) seated_before = seated_before && r.o.pintle_cmd_m == 0.0f;
  }
  const double e1 = r.e.liftCommandTime() - t0;
  check(n_ok > 0 && n_lift == n_ok && seated_before && std::fabs(e1 - 1e-3 * n_ok) < 1e-6 && std::fabs(r.o.ign_lift_t_s - e1) < 1e-6 &&
            std::fabs(r.e.ignLift() - cfg::kIgnLiftTab_m[0]) < 1e-10f && r.e.ignRule() == rule::FIRST,
        "v2.8 lift at E1: pintle seated until the torch confirmation, lift commanded on the confirmation tick (table 0.2039 mm), rule R1",
        fmt("torch confirmed %.0f ms after E0, pintle moving at %.0f ms, lift %.4f mm", n_ok, n_lift, r.e.ignLift() * 1e3));
  // flight relight with P_tank invalid: no segment proof -> PREPRESS (slow priming) -> IGNITION on the OPEN switch and the cock time (flight
  // rule), T_tank unknown -> the smallest table lift. Pad start with P_tank invalid: no priming proof -> PREPRESS_FAIL
  Rig5 v; v.toIgnition(); v.lightRun(); v.burnToCoast(); v.in.ptank_valid = false; v.run(2);
  v.tick(Cmd::RELIGHT); const bool vpre = v.e.state() == State::PREPRESS;
  v.in.mv_open_sw = true; v.in.mv_closed_sw = false; const int nv = v.until(State::IGNITION, 2000);
  const bool vign = v.e.state() == State::IGNITION && std::fabs(v.e.ignLift() - cfg::ignLiftTabMin()) < 1e-10f && !v.e.relightDirect();
  Rig5 p; p.tick(Cmd::ARM); p.run(600); p.in.ptank_valid = false; p.tick(Cmd::IGNITE);
  p.in.mv_open_sw = true; p.in.mv_closed_sw = false; p.in.pfeed_Pa = 48e5f;
  p.until(State::ABORT, 3000);
  check(vpre && vign && cfg::ignLiftTabAscending() && cfg::ignLiftTabMax() <= cfg::kPintleUnlitLiftMax_m && p.e.abortCause() == Abort::PREPRESS_FAIL,
        "v2.8 P_tank invalid: flight relight -> PREPRESS slow priming -> IGNITION with the smallest table lift; pad start -> PREPRESS_FAIL; "
        "table rows ascending and <= the unlit-lift limit",
        fmt("relight E0 %.0f ms after RELIGHT; table max %.4f mm, unlit limit %.4f mm", nv + 1, cfg::ignLiftTabMax() * 1e3, cfg::kPintleUnlitLiftMax_m * 1e3));
}
{   // (2) torch gate 0.16 s (LEAD provisional): a flame confirmed at ~0.149 s (after the 0.100 s interface value, inside the gate) proceeds;
    //     W counts from that late E1
  Rig5 r; r.torch_dead = true; r.toIgnition(); const double t0 = r.t;
  r.run(145); r.torch_dead = false;
  int n = 145; while (r.e.liftCommandTime() < 0.0 && r.e.state() == State::IGNITION && n < 400) { r.tick(); ++n; }
  const double e1 = r.e.liftCommandTime() - t0;
  r.run(300); r.setPc(6.0e5f); r.until(State::RUN, 60);
  check(r.e.state() == State::RUN && e1 > eng::kTorchConfirmBy_s && e1 <= cfg::kTorchGate_s,
        "v2.8 gate 0.16 s: torch confirmed at about 0.15 s (the v2.7 0.100 s gate would have aborted) -> lift at E1, light 0.30 s later -> RUN",
        fmt("E1 %.3f s after E0", e1));
}
{   // (3) stand windows. v2.8.1 (LEAD 2026-10-13 stand relief fallback (b)): R1 first start 0.35 s; R2 every stand relight 0.35 s; R3
    //     DELETED (superheat proven at both state TCs no longer extends the window; the flag is telemetry only); R4 any of MSS-1, MSS-2,
    //     P_feed invalid -> RELIGHT refused (unchanged). (v2.8 final: R1 0.40 / R2 0.50 / R3 0.65 s.)
  auto standCoast = [](Rig5& r) { r.in.load_cell_N = 0.0f; r.in.mode_strap = strap::STAND; r.toIgnition(); const bool a = r.lightRun(); return a && r.burnToCoast(); };
  auto noLight = [](Rig5& r, double t0, float W, int* n_out) {   // runs to the abort; returns |n - expected| <= 1
    int n = 0; while (r.e.state() == State::IGNITION && n < 2000) { r.tick(); ++n; }
    *n_out = n;
    const int n_exp = static_cast<int>(std::lround(1000.0 * (r.e.liftCommandTime() - t0 + W))) + 1;
    return r.e.abortCause() == Abort::NO_IGNITION && std::abs(n - n_exp) <= 1;
  };
  float tsat = 0.0f; const bool ts_ok = n2o::tsatK(48e5f + 101325.f, &tsat);   // rig P_feed 48 bar g
  {
    Rig5 r; r.in.load_cell_N = 0.0f; r.in.mode_strap = strap::STAND; r.toIgnition(); const double t0 = r.t; int n = 0;
    const bool w_ok = std::fabs(r.e.ignitionWindow() - cfg::kIgnWindowFirstStand_s) < 1e-6f;
    const bool ok = noLight(r, t0, cfg::kIgnWindowFirstStand_s, &n);
    check(w_ok && ok && r.e.ignRule() == rule::FIRST && r.e.modeStand(), "v2.8.1 stand R1: first start, no light -> NO_IGNITION at the lift + 0.35 s",
          fmt("abort %.0f ms after E0 (lift at %.0f ms)", n, 1e3 * (r.e.liftCommandTime() - t0)));
  }
  {
    Rig5 r; const bool c = standCoast(r); r.toRelight(); const double t0 = r.t; int n = 0;
    const bool rule2 = r.e.ignRule() == rule::STAND_DEFAULT && std::fabs(r.e.ignitionWindow() - cfg::kIgnWindowRelightStand_s) < 1e-6f && !r.e.superheatProven();
    const bool ok = noLight(r, t0, cfg::kIgnWindowRelightStand_s, &n);
    check(c && rule2 && ok && r.e.relightDirect(), "v2.8.1 stand R2: relight with the state TCs at ambient -> W 0.35 s, NO_IGNITION at the lift + 0.35 s",
          fmt("abort %.0f ms after E0 (Tsat(P_feed) %.2f K, TCs 293.15 K)", n, tsat));
  }
  {
    Rig5 r; const bool c = standCoast(r);
    r.in.tc_mss1_K = tsat + 6.0f; r.in.tc_mss2_K = tsat + 6.0f; r.run(5);
    r.toRelight(); const double t0 = r.t; int n = 0;
    const bool no_r3 = r.e.ignRule() == rule::STAND_DEFAULT && r.e.superheatProven() && !r.o.relight_ext &&
                       std::fabs(r.e.ignitionWindow() - cfg::kIgnWindowRelightStand_s) < 1e-6f;
    const bool ok = noLight(r, t0, cfg::kIgnWindowRelightStand_s, &n);
    check(ts_ok && c && no_r3 && ok,
          "v2.8.1 stand R3 deleted: MSS-1 AND MSS-2 >= Tsat(P_feed) + 5 K at E0 -> still R2 W 0.35 s (superheat flag logged only)",
          fmt("abort %.0f ms after E0 (Tsat %.2f K)", n, tsat));
  }
  {
    Rig5 r; const bool c = standCoast(r); r.in.tc_mss2_valid = false; r.run(2);
    const uint8_t blk = r.o.relight_block;
    r.tick(Cmd::RELIGHT); const bool ev = r.o.cmd_refused_event; r.run(2);
    const bool ref1 = r.e.state() == State::COAST && r.e.ignRefusedR4() == 1 && r.o.cmd_refused == refuse::R4_SENSOR && blk == refuse::R4_SENSOR && ev;
    r.in.tc_mss2_valid = true; r.in.pfeed_valid = false; r.run(2);
    r.tick(Cmd::RELIGHT); r.run(2);
    const bool ref2 = r.e.state() == State::COAST && r.e.ignRefusedR4() == 2;
    r.in.pfeed_valid = true; r.run(2); r.tick(Cmd::RELIGHT);
    check(c && ref1 && ref2 && r.e.state() == State::IGNITION,
          "v2.8 stand R4: MSS-2 invalid or P_feed invalid -> RELIGHT refused (R4_SENSOR, one event, TLM block); all valid -> accepted");
  }
}
{   // (4) direct relight: opener ramp 0.35 s + hold 0.15 s from E0 with the latch; OPEN switch supervision (kMvOpenBy_s 0.95 s):
    //     no OPEN switch on a lit relight -> stand MV_FAULT abort, flight flag only (v2.8 draft aborted in flight: retired)
  Rig5 r; r.toIgnition(); r.lightRun(); r.burnToCoast(); r.toRelight();
  const bool latch0 = r.o.mv_latch && r.e.relightDirect();
  float us175 = 0, us400 = 0, us499 = 0, us501 = 0; bool latched = true;
  for (int k = 1; k <= 520 && r.e.state() == State::IGNITION; ++k) {
    r.tick(); latched = latched && r.o.mv_latch;
    if (k == 175) us175 = r.o.servo_us[3];
    if (k == 400) us400 = r.o.servo_us[3];
    if (k == 499) us499 = r.o.servo_us[3];
    if (k == 501) us501 = r.o.servo_us[3];
  }
  const float mid = cfg::kMvOpenerRest_us + 0.5f * (cfg::kMvOpenerCock_us - cfg::kMvOpenerRest_us);
  check(latch0 && latched && std::fabs(us175 - mid) < 2.0f && us400 == cfg::kMvOpenerCock_us && us499 == cfg::kMvOpenerCock_us &&
            us501 == cfg::kMvOpenerRest_us,
        "v2.8 direct relight: latch on at E0, opener ramp rest->cock over 0.35 s, hold to 0.50 s, then rest (the latch holds)",
        fmt("servo3 %.1f us at 175 ms, %.1f at 400 ms, %.1f at 501 ms", us175, us400, us501));
  for (int stand = 0; stand < 2; ++stand) {
    Rig5 m; m.follow = true;
    if (stand) { m.in.load_cell_N = 0.0f; m.in.mode_strap = strap::STAND; }
    m.toIgnition(); m.lightRun(); m.burnToCoast();
    m.tick(Cmd::RELIGHT); const double t0 = m.t; m.in.mv_closed_sw = false;   // valve leaves CLOSED; the OPEN switch never makes (failed)
    const bool direct = m.e.relightDirect();
    m.run(300); m.setPc(6.0e5f); m.until(State::RUN, 60);
    const bool run = m.e.state() == State::RUN;
    int n = 0; while (n < 1200 && (m.e.state() == State::RUN)) { m.tick(); ++n; if (m.t - t0 > 1.2) break; }
    const double t_end = m.t - t0;
    if (stand) {
      check(direct && run && m.e.abortCause() == Abort::MV_FAULT && std::fabs(t_end - (cfg::kMvOpenBy_s + 1e-3)) < 1.5e-3,
            "v2.8 stand: lit direct relight with no OPEN switch -> MV_FAULT abort at E0 + 0.95 s (switch/latch to be inspected)",
            fmt("abort %.3f s after E0", t_end));
    } else {
      check(direct && run && m.e.state() == State::RUN && (m.o.fault_bits & fault::MV) && m.e.abortCause() == Abort::NONE,
            "v2.8 flight: lit direct relight with no OPEN switch -> fault MV flag only, burn continues (draft aborted MV_FAULT: retired)",
            fmt("still RUN %.3f s after E0, faults ", t_end) + hex(m.o.fault_bits, 4));
    }
  }
}
{   // (5) S1 relief monitor (LEAD 2026-10-13): in-situ zero (PREPRESS with the OPEN switch, COAST 0.2-0.4 s), P_feed - P_tank - zero > 2.0 bar
    //     for 1 s with the MV closed -> S1 fault; stand -> relight lockout; flight -> flag only, relight proceeds; +1.5 bar -> nothing
  auto s1run = [](Rig5& r, bool stand, float over_Pa, int ms, int* n_fault, int* n_ev) {
    if (stand) { r.in.load_cell_N = 0.0f; r.in.mode_strap = strap::STAND; }
    r.toIgnition(); r.lightRun(); r.burnToCoast(); r.run(500);   // past this coast's zero window
    const float z = r.e.s1Zero(); const bool zok = r.e.s1ZeroOk();
    r.in.pfeed_Pa = r.in.ptank_Pa + z + over_Pa;
    *n_fault = -1; *n_ev = 0;
    for (int k = 1; k <= ms; ++k) { r.tick(); *n_ev += r.o.s1_event; if (*n_fault < 0 && r.o.s1_fault) *n_fault = k; }
    return zok && std::fabs(z + 2.0e5f) < 0.05e5f;   // rig: P_feed 48 bar g, P_tank 50 bar g -> zero -2 bar
  };
  Rig5 s; int ns = 0, es = 0; const bool zs = s1run(s, true, 2.5e5f, 1300, &ns, &es);
  const uint16_t refs = s.e.ignitionRefused(); s.tick(Cmd::RELIGHT); s.run(2);
  check(zs && ns >= 1000 && ns <= 1010 && es == 1 && s.o.relight_lockout && s.e.state() == State::COAST && s.e.ignitionRefused() == refs + 1 &&
            s.o.cmd_refused == refuse::LOCKOUT,
        "v2.8 S1 stand: +2.5 bar over the in-situ zero for 1 s -> S1 fault (one event) and relight lockout; RELIGHT refused (LOCKOUT)",
        fmt("fault %.0f ms after the step, zero %.2f bar", ns, s.e.s1Zero() / 1e5));
  Rig5 f; int nf = 0, ef = 0; const bool zf = s1run(f, false, 2.5e5f, 1300, &nf, &ef);
  const bool flag = f.o.s1_fault && !f.o.relight_lockout && (f.o.fault_bits & fault::MV);
  can::TlmRelight tm; const bool dec = can::decodeTlmRelight(can::encodeTlmRelight(3, f.o), &tm);
  f.tick(Cmd::RELIGHT);
  check(zf && nf >= 1000 && nf <= 1010 && ef == 1 && flag && dec && (tm.flags & tlmr::S1_FAULT) && f.e.state() == State::IGNITION && f.e.relightDirect(),
        "v2.8 S1 flight: same -> S1 fault flag (fault MV, TLM_RELIGHT S1_FAULT), no lockout; RELIGHT proceeds (direct, opens the MV at E0)",
        fmt("fault %.0f ms after the step", nf));
  Rig5 g; int ng = 0, eg = 0; const bool zg = s1run(g, true, 1.5e5f, 3000, &ng, &eg);
  check(zg && ng < 0 && eg == 0 && !g.o.s1_fault && std::fabs(g.o.s1_dp_Pa - 1.5e5f) < 0.05e5f,
        "v2.8 S1: +1.5 bar over the zero for 3 s -> no fault (threshold 2.0 bar)", fmt("s1_dp %.2f bar", g.o.s1_dp_Pa / 1e5));
  // a coast zero beyond 2 x TEB (5.1 bar: transducer fault) is not accepted: the PREPRESS zero is kept
  Rig5 z; z.toIgnition(); z.lightRun(); const float z_pre = z.e.s1Zero(); z.in.pfeed_Pa = 40e5f;   // -10 bar in the coast window
  z.burnToCoast(); z.run(500);
  check(std::fabs(z.e.s1Zero() - z_pre) < 1.0f && z.e.s1ZeroOk() && std::fabs(z_pre + 2.0e5f) < 0.05e5f,
        "v2.8 S1: a coast zero of -10 bar (beyond 5.1 bar) rejected, PREPRESS zero kept", fmt("zero %.2f bar", z.e.s1Zero() / 1e5));
}
{   // (6) over-thrust. v2.8.1 (LEAD 2026-10-13 ADOPTED, GNC m2_fc_thrust v1.1): flight, RUN, 3 CONSECUTIVE fresh FC_THRUST frames with the
    //     valid flag above 650 N -> OVER_THRUST on the tick of the third frame (20 ms span at 100 Hz); runs with the Pc channel valid or
    //     not; a frame at or below 650 N, an invalid frame, a gap above 50 ms or leaving RUN restarts the count; never on the stand.
    //     (v2.8: 20 ms persistence on the held value, Pc lost only.)
  auto burn = [](Rig5& r, bool stand) {
    r.thrust = 400.f; r.follow = true;
    if (stand) { r.in.load_cell_N = 0.0f; r.in.mode_strap = strap::STAND; }
    r.toIgnition(); const bool ok = r.lightRun(); r.run(400); r.follow = false;   // chamber held at the last Pc (a sensor fault then sticks)
    return ok;
  };
  // one FC_THRUST frame on the next tick, then (gap_ms - 1) ticks without a frame
  auto frame = [](Rig5& r, float F, bool valid, int gap_ms = 10) {
    r.fc_period_ms = 1; r.fc_F = F; r.fc_ok = valid; r.fc_send = true; r.tick(); r.fc_send = false;
    const bool ab = r.e.state() == State::ABORT;
    if (!ab) r.run(gap_ms - 1);
    return ab;
  };
  // (a) Pc VALID, closed loop: frames 1 and 2 above -> still RUN; frame 3 -> OVER_THRUST on its own tick, MV latch dropped on that tick
  Rig5 a; const bool la = burn(a, false);
  const bool a1 = frame(a, 700.f, true), a2 = frame(a, 700.f, true);
  const bool run2 = a.e.state() == State::RUN;
  const bool a3 = frame(a, 700.f, true, 1);
  check(la && !a1 && !a2 && run2 && a3 && a.e.abortCause() == Abort::OVER_THRUST && !a.o.mv_latch && (a.o.fault_bits & fault::PC_OVERP) &&
            a.e.pcSensorOk(),
        "v2.8.1 over-thrust, Pc VALID (in-range wrong Pc coverage): 2 frames at 700 N -> RUN; 3rd frame (20 ms after the 1st) -> OVER_THRUST on "
        "that tick, MV latch dropped on the abort tick");
  // (b) Pc LOST (open loop): same rule
  Rig5 b; const bool lb = burn(b, false); b.in.pc_raw_V = 0.02f; b.run(20);
  const bool b_ol = b.e.state() == State::RUN && (b.o.fault_bits & fault::OPEN_LOOP);
  frame(b, 700.f, true); frame(b, 700.f, true); const bool b3 = frame(b, 700.f, true, 1);
  check(lb && b_ol && b3 && b.e.abortCause() == Abort::OVER_THRUST, "v2.8.1 over-thrust, Pc LOST (open loop): 3 consecutive frames at 700 N -> OVER_THRUST",
        "lit " + std::to_string(lb) + " open-loop " + std::to_string(b_ol) + " abort-on-3rd " + std::to_string(b3) + " cause " +
            std::to_string(static_cast<int>(b.e.abortCause())) + " state " + std::to_string(static_cast<int>(b.e.state())));
  // (c) no trip: 700, 700, 600 repeated for 300 ms; 650.0 N exactly (not above); 700 N with the valid flag clear; two frames, a 60 ms gap
  //     (stale), two frames
  Rig5 c; const bool lc = burn(c, false); bool c_ab = false;
  for (int k = 0; k < 10 && !c_ab; ++k) { c_ab = frame(c, 700.f, true) || frame(c, 700.f, true) || frame(c, 600.f, true); }
  Rig5 d; const bool ld = burn(d, false); bool d_ab = false;
  for (int k = 0; k < 30 && !d_ab; ++k) d_ab = frame(d, cfg::kOverThrust_N, true);
  Rig5 v; const bool lv = burn(v, false); bool v_ab = false;
  for (int k = 0; k < 30 && !v_ab; ++k) v_ab = frame(v, 700.f, false);
  Rig5 g; const bool lg = burn(g, false);
  bool g_ab = frame(g, 700.f, true) || frame(g, 700.f, true, 61) || frame(g, 700.f, true) || frame(g, 700.f, true, 61);
  const bool g_run = g.e.state() == State::RUN;
  const bool g_3 = frame(g, 700.f, true) || frame(g, 700.f, true) || frame(g, 700.f, true, 1);   // a fresh run of three trips
  check(lc && ld && lv && lg && !c_ab && !d_ab && !v_ab && !g_ab && g_run && g_3 && c.e.state() == State::RUN && d.e.state() == State::RUN &&
            v.e.state() == State::RUN && g.e.abortCause() == Abort::OVER_THRUST,
        "v2.8.1 over-thrust not tripped: 700/700/600 N pattern; 650.0 N (not above); 700 N with the FC valid flag clear; 2 frames + 61 ms gap "
        "(stale, count restarts) + 2 frames; then a fresh run of 3 frames trips");
  // (d) frames above the threshold before RUN do not count (IGNITION), and the stand never runs the check (Pc valid: burn continues; Pc
  //     lost: PC_SENSOR after 5 ms, as v2.7)
  Rig5 i; i.thrust = 400.f; i.follow = true; i.toIgnition(); frame(i, 700.f, true); frame(i, 700.f, true); i.run(100);
  const bool i_lit = i.lightRun(6.0e5f, 1);
  const bool i_ab = frame(i, 700.f, true);
  Rig5 st; const bool ls = burn(st, true); bool st_ab = false;
  for (int k = 0; k < 30 && !st_ab; ++k) st_ab = frame(st, 700.f, true);
  Rig5 sp; const bool lsp = burn(sp, true); sp.fc_send = true; sp.fc_period_ms = 10; sp.fc_F = 700.f; sp.in.pc_raw_V = 0.02f; sp.run(50);
  check(i_lit && !i_ab && i.e.state() == State::RUN && ls && !st_ab && st.e.state() == State::RUN && lsp && sp.e.abortCause() == Abort::PC_SENSOR,
        "v2.8.1 over-thrust: 2 frames at 700 N in IGNITION + 1 in RUN -> no trip (count restarts at RUN); stand: 30 frames at 700 N with Pc valid "
        "-> RUN, Pc lost -> PC_SENSOR (5 ms) first",
        "i_lit " + std::to_string(i_lit) + " i_ab " + std::to_string(i_ab) + " i_state " + std::to_string(static_cast<int>(i.e.state())) +
            " | stand lit " + std::to_string(ls) + " ab " + std::to_string(st_ab) + " state " + std::to_string(static_cast<int>(st.e.state())) +
            " | sp lit " + std::to_string(lsp) + " cause " + std::to_string(static_cast<int>(sp.e.abortCause())));
}
{   // (7) FC_THRUST (0x024) decoder: round trip 0.1 N, length, CRC, undefined flag bits, repeated sequence
  can::Decoder dec; Commands c;
  const bool ok = dec.accept(can::encodeFcThrust(1, 652.3f, true), c) && c.fc_thrust_valid && std::fabs(c.fc_thrust_N - 652.3f) < 0.051f && c.fc_thrust_ok;
  Commands c2; const bool rep = !dec.accept(can::encodeFcThrust(1, 652.3f, true), c2) && dec.rejected_seq == 1;
  can::Frame l = can::encodeFcThrust(2, 100.f, true); l.len = 4; Commands c3; const bool len = !dec.accept(l, c3) && dec.rejected_len == 1;
  can::Frame x = can::encodeFcThrust(3, 100.f, true); x.d[1] ^= 0x01; Commands c4; const bool crc = !dec.accept(x, c4) && dec.rejected_crc == 1;
  can::Frame y = can::encodeFcThrust(4, 100.f, true); y.d[3] |= 0x02; y.d[4] = can::crc8(y.d, 4); Commands c5;
  const bool flg = !dec.accept(y, c5) && dec.rejected_key == 1;
  Commands c6; const bool inv = dec.accept(can::encodeFcThrust(5, 700.f, false), c6) && c6.fc_thrust_valid && !c6.fc_thrust_ok;
  Commands c7; const bool neg = dec.accept(can::encodeFcThrust(6, -5.f, true), c7) && c7.fc_thrust_N == 0.0f;
  check(ok && rep && len && crc && flg && inv && neg, "v2.8 FC_THRUST decoder: 0.1 N round trip; repeat, length, CRC, undefined flag bit rejected; valid flag carried; negative clamped to 0",
        fmt("decoded %.2f N", c.fc_thrust_N));
}
{   // (8) mode strap (LEAD 2026-10-13): ARM needs a valid strap agreeing with the load-cell check; mismatch after ARM = flag only
  struct M { uint8_t s; bool lc; bool arm; bool stand; };
  const M m[] = {{strap::FLIGHT, false, true, false}, {strap::STAND, true, true, true}, {strap::STAND, false, false, false},
                 {strap::FLIGHT, true, false, false}, {strap::INVALID, false, false, false}, {strap::INVALID, true, false, false},
                 {3, false, false, false}};
  bool all = true; std::string det;
  for (const M& k : m) {
    Rig5 r; r.in.mode_strap = k.s; r.in.load_cell_N = k.lc ? 0.0f : std::numeric_limits<float>::quiet_NaN();
    r.tick(Cmd::ARM);
    const bool armed = r.e.state() == State::ARMED;
    const bool ok = k.arm ? (armed && r.e.modeStand() == k.stand) : (!armed && r.e.abortCause() == Abort::MODE_MISMATCH);
    all = all && ok; det += fmt("%.0f/%.0f:", k.s, k.lc) + (ok ? "ok " : "FAIL ");
  }
  check(all, "v2.8 mode strap: FLIGHT+NaN and STAND+finite load cell arm; any disagreement or an invalid code -> ARM refused (MODE_MISMATCH)", det);
  Rig5 r; r.in.load_cell_N = 0.0f; r.in.mode_strap = strap::STAND; r.toIgnition(); r.lightRun();
  r.in.mode_strap = strap::FLIGHT; r.in.load_cell_N = std::numeric_limits<float>::quiet_NaN(); r.run(50);
  const bool still = r.e.state() == State::RUN && r.e.modeMismatch() && r.e.modeStand() && r.o.mode_stand;
  LogRecord lg; r.e.fillLog(r.in, r.o, lg);
  check(still && (lg.seq2_flags & 0x40u) && (lg.seq2_flags & 0x20u),
        "v2.8 mode strap: a change after ARM is a flag only (no abort; the session mode stays latched); logged seq2 b5 stand, b6 mismatch", hex(lg.seq2_flags, 2));
}
{   // (9) case temperature (LEAD 2026-10-13 correction): abort 448.15 K / 0.2 s while the MV is latched or OPEN; start refusal 433.15 K
  Rig5 r; r.follow = true; r.thrust = 300.f; r.toIgnition(); r.lightRun(); r.run(200);
  r.in.tc_K[0] = 440.0f; r.run(400);
  const bool no_abort = r.e.state() == State::RUN;
  r.in.tc_K[0] = 450.0f;
  int n = 0; while (r.e.state() == State::RUN && n < 400) { r.tick(); ++n; }
  check(no_abort && r.e.abortCause() == Abort::OVER_TEMP && n >= 200 && n <= 201 && !r.o.mv_latch,
        "v2.8 case 440 K in RUN: no abort (v2.8 draft 433.15 K would have); 450 K -> OVER_TEMP after 0.2 s, MV dropped",
        fmt("abort %.0f ms after the step", n));
  Rig5 c; c.toIgnition(); c.lightRun(); c.burnToCoast();
  c.in.tc_K[1] = 450.0f; c.run(500);
  const bool soak = c.e.state() == State::COAST && !(c.o.fault_bits & fault::OVER_TEMP);
  const uint16_t h0 = c.e.ignRefusedHot();
  c.tick(Cmd::RELIGHT); c.run(2); const bool r1 = c.e.state() == State::COAST && c.o.cmd_refused == refuse::CASE_HOT;
  c.in.tc_K[1] = 435.0f; c.run(2); c.tick(Cmd::RELIGHT); c.run(2); const bool r2 = c.e.state() == State::COAST && c.e.ignRefusedHot() == h0 + 2;
  c.in.tc_K[1] = 430.0f; c.run(2); c.tick(Cmd::RELIGHT);
  check(soak && r1 && r2 && c.e.state() == State::IGNITION,
        "v2.8 case in COAST (MV closed): 450 K soak -> no abort, no flag; RELIGHT refused (CASE_HOT) at 450 K and 435 K, accepted at 430 K");
}
{   // (10) bay temperature (LEAD 2026-10-13 launch constraint, limit TO-DEFINE ~45 C): ARM inhibit and pad first-start refusal; relights never
  Rig5 a; a.in.bay_K = 320.0f; a.tick(Cmd::ARM); const bool hot = a.e.state() == State::SAFE && a.e.abortCause() == Abort::BAY_HOT;
  Rig5 b; b.in.bay_valid = false; b.tick(Cmd::ARM); const bool inv = b.e.state() == State::SAFE && b.e.abortCause() == Abort::BAY_HOT;
  Rig5 c; c.in.bay_K = 318.0f; c.tick(Cmd::ARM); const bool ok = c.e.state() == State::ARMED;
  c.run(600); c.in.bay_K = 320.0f; c.tick(Cmd::IGNITE); c.run(2);
  const bool pad = c.e.state() == State::ARMED && c.e.ignRefusedBay() == 1 && c.o.cmd_refused == refuse::BAY_HOT;
  check(hot && inv && ok && pad, "v2.8 bay: ARM refused (BAY_HOT) at 320 K or with no valid reading, accepted at 318 K; pad IGNITE refused when the bay heats after ARM");
  Rig5 r; r.toIgnition(); r.lightRun(); r.burnToCoast(); r.in.bay_K = 330.0f; r.in.bay_valid = false; r.run(2);
  const uint8_t blk = r.o.relight_block; r.tick(Cmd::RELIGHT);
  check(blk == refuse::NONE && r.e.state() == State::IGNITION, "v2.8 bay: a relight in COAST is never refused on the bay temperature (330 K, invalid)");
}
{   // (11) PREPRESS refused in COAST (LEAD 2026-10-13); accepted in ARMED
  Rig5 r; r.toIgnition(); r.lightRun(); r.burnToCoast();
  r.tick(Cmd::PREPRESS); const bool ev = r.o.cmd_refused_event; r.tick(); const bool once = !r.o.cmd_refused_event;
  check(r.e.state() == State::COAST && r.e.prepressRefused() == 1 && r.o.cmd_refused == refuse::PREPRESS_IN_COAST && ev && once && !r.o.mv_latch,
        "v2.8 PREPRESS in COAST refused (PREPRESS_IN_COAST, one-tick event), valve stays closed");
  Rig5 a; a.tick(Cmd::ARM); a.run(600); a.tick(Cmd::PREPRESS);
  check(a.e.state() == State::PREPRESS, "v2.8 PREPRESS in ARMED accepted (pad)");
}
{   // (12) Tsat(P) table (calc/manifold_state_v1.py) spot check against CoolProp 8.0.0 HEOS at off-grid pressures (values computed
    //      2026-10-13 with PropsSI('T','P',p,'Q',0,'NitrousOxide')); out-of-range and NaN rejected
  struct S { float p; double T; };
  const S s[] = {{12.34e5f, 241.15244}, {31.3e5f, 273.24880}, {49.01325e5f, 291.81579}, {51.01325e5f, 293.57421}, {63.7e5f, 303.60266}};
  double worst = 0; bool all = true;
  for (const S& k : s) { float T = 0; all = all && n2o::tsatK(k.p, &T); worst = std::fmax(worst, std::fabs(T - k.T)); }
  float d = 0; const bool rej = !n2o::tsatK(4.9e5f, &d) && !n2o::tsatK(72.5e5f, &d) && !n2o::tsatK(std::numeric_limits<float>::quiet_NaN(), &d);
  check(all && worst < 0.02 && rej, "v2.8 N2O Tsat table vs CoolProp at 5 off-grid points (12-64 bar abs); out of range / NaN rejected",
        fmt("worst %.4f K", worst));
}
{   // (13) TLM_RELIGHT (0x102; LEAD 2026-10-13 PRIMED/UNPRIMED status; v2.8 final GNC v3 option (c) states): fields, worst-case planning
    //      value, round trip, invariants. VALID only in COAST after the MECO valve closure; UNKNOWN = VALID with P_feed or P_tank invalid
  Rig5 r; r.toIgnition(); r.lightRun(); r.burnToCoast(); r.run(50);
  can::TlmRelight p; const bool d1 = can::decodeTlmRelight(can::encodeTlmRelight(10, r.o), &p);
  const bool primed = d1 && p.seq == 10 && p.state == static_cast<uint8_t>(State::COAST) && (p.flags & tlmr::PRIMED) && (p.flags & tlmr::VALID) &&
                      (p.flags & tlmr::READY) && !(p.flags & (tlmr::UNKNOWN | tlmr::POST_ABORT | tlmr::STAND)) && p.block == refuse::NONE &&
                      p.worst_ms == 810 && p.ratio_pct == 96 && tlmr::stateOf(p.flags) == segstate::PRIMED && r.o.relight_state == segstate::PRIMED;
  r.in.pfeed_Pa = 10e5f; r.run(50);   // segment below half the tank pressure (gas pocket possible)
  can::TlmRelight u; const bool d2 = can::decodeTlmRelight(can::encodeTlmRelight(11, r.o), &u);
  const bool unprimed = d2 && !(u.flags & tlmr::PRIMED) && (u.flags & tlmr::VALID) && (u.flags & tlmr::READY) && !(u.flags & tlmr::UNKNOWN) &&
                        u.worst_ms == 1370 && u.ratio_pct == 22 && tlmr::stateOf(u.flags) == segstate::UNPRIMED;
  r.in.pfeed_valid = false; r.run(2);
  can::TlmRelight v; const bool d3 = can::decodeTlmRelight(can::encodeTlmRelight(12, r.o), &v);
  const bool unknown = d3 && !(v.flags & tlmr::PRIMED) && (v.flags & tlmr::VALID) && (v.flags & tlmr::UNKNOWN) && v.ratio_pct == 0xFF &&
                       v.worst_ms == 1370 && tlmr::stateOf(v.flags) == segstate::UNKNOWN;
  r.in.pfeed_valid = true; r.in.pfeed_Pa = 48e5f; r.in.ptank_valid = false; r.run(50);   // P_tank invalid alone
  can::TlmRelight k; const bool d4 = can::decodeTlmRelight(can::encodeTlmRelight(13, r.o), &k);
  const bool unknown_t = d4 && (k.flags & tlmr::VALID) && (k.flags & tlmr::UNKNOWN) && !(k.flags & tlmr::PRIMED) && k.worst_ms == 1370;
  r.in.ptank_valid = true; r.in.pfeed_Pa = 10e5f; r.run(50); r.tick(Cmd::RELIGHT);
  const bool path = r.e.state() == State::PREPRESS;   // the status matched the path the ECU then takes
  check(primed && unprimed && unknown && unknown_t && path,
        "v2.8 final TLM_RELIGHT flight COAST: primed -> PRIMED|VALID|READY, worst 810 ms, ratio 96 %; P_feed 10 bar g -> UNPRIMED, 1370 ms "
        "(RELIGHT then takes PREPRESS); P_feed invalid -> VALID|UNKNOWN, ratio 0xFF, 1370 ms; P_tank invalid -> VALID|UNKNOWN, 1370 ms",
        fmt("worst %.0f / %.0f / %.0f ms", p.worst_ms, u.worst_ms, v.worst_ms));
  Rig5 s; s.in.load_cell_N = 0.0f; s.in.mode_strap = strap::STAND; s.toIgnition(); s.lightRun(); s.burnToCoast(); s.run(50);
  can::TlmRelight st; can::decodeTlmRelight(can::encodeTlmRelight(1, s.o), &st);
  can::TlmRelight run; Rig5 q; q.toIgnition(); q.lightRun(); can::decodeTlmRelight(can::encodeTlmRelight(2, q.o), &run);
  check((st.flags & tlmr::STAND) && st.worst_ms == 510 && !(run.flags & tlmr::READY) && !(run.flags & tlmr::VALID) && run.block == refuse::NOT_COAST &&
            tlmr::stateOf(run.flags) == segstate::NONE,
        "v2.8.1 TLM_RELIGHT: stand relight -> worst 0.16 + 0.35 = 510 ms (R2, R3 deleted); in RUN -> VALID 0 (state NONE), READY 0, block NOT_COAST",
        fmt("stand %.0f ms", st.worst_ms));
  can::Frame f = can::encodeTlmRelight(7, r.o);
  auto withFlags = [&f](uint8_t fl) { can::Frame g = f; g.d[2] = fl; g.d[7] = can::crc8(g.d, 7); return g; };
  can::TlmRelight w;
  const bool inv = !can::decodeTlmRelight(withFlags(tlmr::PRIMED), &w) && !can::decodeTlmRelight(withFlags(tlmr::UNKNOWN), &w) &&
                   !can::decodeTlmRelight(withFlags(tlmr::VALID | tlmr::PRIMED | tlmr::UNKNOWN), &w) &&
                   !can::decodeTlmRelight(withFlags(tlmr::VALID | tlmr::PRIMED | tlmr::POST_ABORT), &w) &&
                   can::decodeTlmRelight(withFlags(tlmr::VALID | tlmr::UNKNOWN | tlmr::POST_ABORT), &w) &&
                   can::decodeTlmRelight(withFlags(tlmr::VALID | tlmr::POST_ABORT), &w) && tlmr::stateOf(w.flags) == segstate::UNPRIMED &&
                   can::decodeTlmRelight(withFlags(tlmr::VALID | tlmr::PRIMED | tlmr::READY | tlmr::STAND | tlmr::S1_FAULT | tlmr::LOCKOUT), &w);
  can::Frame bc = f; bc.d[3] ^= 0x01u;
  can::Frame bl = f; bl.len = 7;
  can::Frame bi = f; bi.id = can::ID_TLM_FAST;
  check(inv && !can::decodeTlmRelight(bc, &w) && !can::decodeTlmRelight(bl, &w) && !can::decodeTlmRelight(bi, &w) && f.id == 0x102 && f.len == 8,
        "v2.8 final TLM_RELIGHT decoder: rejects PRIMED or UNKNOWN without VALID, PRIMED with UNKNOWN or POST_ABORT, a CRC error, a wrong length "
        "and a wrong id; accepts VALID|UNKNOWN|POST_ABORT and VALID|POST_ABORT (UNPRIMED)");
}
{   // (14) v2.8 refusal reasons reported for the v2.7 rules (same counters): NOT_VENTED, VENT_WAIT, LOCKOUT, MAX_STARTS
  Rig5 a; a.tick(Cmd::ARM); a.run(600); a.setPc(101325.f + 0.15e5f); a.run(100); a.tick(Cmd::IGNITE);
  const bool nv = a.o.cmd_refused == refuse::NOT_VENTED && a.o.cmd_refused_event && a.e.ignitionRefused() == 1;
  Rig5 b; b.toIgnition(); b.run(125); b.setPc(2.9e5f); b.until(State::ABORT, 1000); b.setPc(101325.f); b.until(State::SAFE, 1000);
  b.in.mv_open_sw = false; b.in.mv_closed_sw = true; b.in.pfeed_Pa = 0; b.tick(Cmd::DISARM); b.tick(Cmd::ARM); b.run(600); b.tick(Cmd::IGNITE);
  const bool vw = b.o.cmd_refused == refuse::VENT_WAIT;
  Rig5 c; c.toIgnition(); c.lightRun(); c.burnToCoast(); c.in.nv_relight_lockout = true; c.tick(Cmd::RELIGHT);
  const bool lk = c.o.cmd_refused == refuse::LOCKOUT;
  // start limit: after kMaxStarts lit starts SHUTDOWN ends in SAFE, not COAST, so a further RELIGHT is ignored (refuse::MAX_STARTS is a
  // defensive code: COAST, where TLM_RELIGHT evaluates it, is never entered with the starts used up)
  Rig5 m; m.toIgnition(); m.lightRun(); m.burnToCoast();
  int burns = 1; bool last_safe = false;
  for (int k = 0; k < cfg::kMaxStarts - 1; ++k) {
    m.toRelight(); const bool lit = m.lightRun(); const bool coast = m.burnToCoast();
    if (lit) ++burns;
    if (k == cfg::kMaxStarts - 2) last_safe = !coast && m.e.state() == State::SAFE && m.e.abortCause() == Abort::NONE;
  }
  m.tick(Cmd::RELIGHT); m.run(2);
  const bool ms = burns == cfg::kMaxStarts && last_safe && m.e.state() == State::SAFE;
  check(nv && vw && lk && ms, "v2.8 refusal codes: NOT_VENTED, VENT_WAIT, LOCKOUT; after 4 lit starts SHUTDOWN ends in SAFE (no COAST) and a RELIGHT is ignored",
        fmt("burns %.0f", burns));
}
{   // (15) log v7 fields (v2.8 draft) and v8 fields (v2.8 final: interlock tank temperature, seq3_flags)
  Rig5 r; r.in.tc_mss1_K = 300.15f; r.in.tc_mss2_K = 301.15f; r.in.bay_K = 305.65f;
  r.toIgnition(); r.lightRun(); r.burnToCoast(); r.toRelight(); r.run(20);
  r.fc_send = true; r.fc_F = 123.4f; r.run(10);
  LogRecord lg; r.e.fillLog(r.in, r.o, lg);
  const bool f7 = lg.version == 9 && lg.tcm1_dK == 270 && lg.tcm2_dK == 280 && lg.bay_dK == 325 && lg.fc_thr_dN == 1234 &&
                  lg.ign_rule == rule::FLIGHT_RELIGHT && lg.ign_lift_ms != 0xFFu && (lg.seq2_flags & 0x01u) && !(lg.seq2_flags & 0x20u) &&
                  lg.s1_dp_hPa == INT16_MIN && lg.cmd_refused == refuse::NONE && lg.seq3_flags == 0 &&
                  crc16_ccitt(reinterpret_cast<const uint8_t*>(&lg), sizeof(LogRecord) - 2) == lg.crc16;
  r.in.tc_mss1_valid = false; r.in.bay_valid = false; r.fc_send = false; r.run(60);
  LogRecord l2; r.e.fillLog(r.in, r.o, l2);
  check(f7 && l2.tcm1_dK == INT16_MIN && l2.bay_dK == INT16_MIN && l2.fc_thr_dN == 0xFFFFu,
        "v2.8 log v8 (v7 fields): MSS-1/2, bay (dK), FC thrust (dN), rule, lift time, seq2 b0 direct, S1 dp NaN marker with the MV open, refusal; "
        "seq3 0 in IGNITION; invalid markers", fmt("lift at %.0f ms, rule %.0f", lg.ign_lift_ms, lg.ign_rule));
  Rig5 k; k.toIgnition(); k.lightRun(); k.burnToCoast(); k.run(50);
  LogRecord l3; k.e.fillLog(k.in, k.o, l3);
  const long t_exp = std::lround((k.o.tank_T_K - 273.15f) * 10.0f);
  const bool c3 = l3.ttank_dK == t_exp && t_exp == 204 && l3.seq3_flags == (segstate::PRIMED | 0x40u);
  k.in.ttank_wall_valid[0] = k.in.ttank_wall_valid[1] = false; k.in.ptank_valid = false; k.run(2);
  LogRecord l4; k.e.fillLog(k.in, k.o, l4);
  const bool c4 = l4.ttank_dK == INT16_MIN && (l4.seq3_flags & 0x03u) == segstate::UNKNOWN && (l4.seq3_flags & 0x08u) && (l4.seq3_flags & 0x40u);
  check(c3 && c4, "v2.8 final log v8: tank T 0.1 K (Tsat(51.0 bar abs) 293.57 K -> 204), seq3 = PRIMED | b6 MECO closed in COAST; no tank reading "
        "-> INT16_MIN, seq3 UNKNOWN | b3 tank hot | b6", hex(l3.seq3_flags, 2) + " / " + hex(l4.seq3_flags, 2));
}
{   // (16) planned cut-off (COMB v2.4 item 1, LEAD 2026-10-13): pintle first; the NC valve is unlatched on the seat confirmation or at
    //      kMvSeatTimeout_s 0.30 s regardless (v2.7-v2.8 draft 0.25 s); the timeout flags only. A SHUTDOWN never takes the abort path by
    //      itself: the abort calls live in SHUTDOWN are fault monitors (firmware/hardware over-pressure, pintle stall/runaway with a valid
    //      encoder, pintle rail lost, ARM lost) and the FC ABORT/DISARM commands (code review in the REPORT)
  // mode 0: healthy (ideal follower); 1: encoder invalid from the SHUTDOWN tick; 2: needle hangs at 0.10 mm (inside the 0.15 mm stall band,
  // above the 0.05 mm seat band: the stall monitor stays quiet, the seat is never confirmed)
  auto cut = [](Rig5& r, int mode, int* n_unl, int* n_coast) {
    r.toIgnition(); r.lightRun(); r.run(300);
    r.tick(Cmd::SHUTDOWN); r.setPc(101325.f);
    if (mode == 1) r.in.pintle_meas_valid = false;
    if (mode == 2) r.pfollow = false;
    *n_unl = -1; *n_coast = -1;
    for (int k = 1; k <= 1000 && r.e.state() == State::SHUTDOWN; ++k) {
      if (mode == 2) r.in.pintle_meas_m = std::fmax(0.10e-3f, r.o.pintle_cmd_m);
      r.tick();
      if (*n_unl < 0 && !r.o.mv_latch) *n_unl = k;
      if (!r.o.mv_latch) { r.in.mv_open_sw = false; r.in.mv_closed_sw = true; }
      if (r.e.state() == State::COAST) *n_coast = k;
    }
    return r.e.state() == State::COAST && r.e.abortCause() == Abort::NONE && !r.o.seg_vapour;
  };
  Rig5 a; int ua = 0, ca = 0; const bool okA = cut(a, 0, &ua, &ca);
  const bool healthy = okA && ua > 0 && ua < 100 && !a.o.mv_seat_timeout && !(a.o.fault_bits & fault::PINTLE) && ca >= ua;
  a.run(50); const bool primed = a.o.relight_state == segstate::PRIMED;
  a.tick(Cmd::RELIGHT); const bool direct = a.e.state() == State::IGNITION && a.e.relightDirect();
  check(healthy && primed && direct && std::fabs(cfg::kMvSeatTimeout_s - 0.30f) < 1e-6f,
        "v2.8 final planned cut-off, healthy: MV unlatched on the seat confirmation, COAST, no abort, no vapour flag -> TLM PRIMED, RELIGHT direct",
        fmt("MV unlatched %.0f ms after SHUTDOWN, COAST at %.0f ms", ua, ca));
  Rig5 b; int ub = 0, cb = 0; const bool okB = cut(b, 1, &ub, &cb);
  check(okB && ub >= 300 && ub <= 301 && b.o.mv_seat_timeout && (b.o.fault_bits & fault::ENCODER) && !(b.o.fault_bits & fault::PINTLE) && cb >= ub,
        "v2.8 final planned cut-off, encoder lost at SHUTDOWN: MV unlatched at the 0.30 s timeout (flag), COAST, no abort, fault ENCODER only",
        fmt("MV unlatched %.0f ms after SHUTDOWN, COAST at %.0f ms", ub, cb));
  Rig5 c; int uc = 0, cc = 0; const bool okC = cut(c, 2, &uc, &cc);
  check(okC && uc >= 300 && uc <= 301 && c.o.mv_seat_timeout && (c.o.fault_bits & fault::PINTLE) && cc >= uc,
        "v2.8 final planned cut-off, needle hangs at 0.10 mm: MV unlatched at the 0.30 s timeout, fault PINTLE flag, COAST, no abort",
        fmt("MV unlatched %.0f ms after SHUTDOWN", uc));
}
{   // (17) post-abort vapour segment (COMB v2.4 item 2, LEAD 2026-10-13): any abort from a powered state sets the flag (RAM + one-tick NV b3
    //      event); TLM POST_ABORT and never PRIMED; stand: the next start uses the R2/R3 logic with the R4 sensor check; flight pad retry keeps
    //      R1 (PREPRESS primes the line); a confirmed light (RUN entry) clears it (one-tick NV clear event)
  auto noLightAbort = [](Rig5& r, int* n_ev) {   // first start, cold-flow-like 2.9 bar abs after the lift: NO_IGNITION
    r.toIgnition(); r.run(125); r.setPc(2.9e5f);
    *n_ev = 0; for (int k = 0; k < 1000 && r.e.state() != State::ABORT; ++k) { r.tick(); *n_ev += r.o.seg_vapour_event; }
    r.setPc(101325.f); for (int k = 0; k < 1000 && r.e.state() != State::SAFE; ++k) { r.tick(); *n_ev += r.o.seg_vapour_event; }
    r.run(5); return r.e.abortCause() == Abort::NO_IGNITION && r.e.state() == State::SAFE;
  };
  auto rearm = [](Rig5& r) {   // safing as test (14): valve closed, line vented, DISARM, ARM, past the 5 s vent wait
    r.in.mv_open_sw = false; r.in.mv_closed_sw = true; r.in.pfeed_Pa = 0; r.tick(Cmd::DISARM); r.tick(Cmd::ARM); r.run(5100);
    return r.e.state() == State::ARMED;
  };
  auto startTo = [](Rig5& r) {   // IGNITE -> PREPRESS -> IGNITION (rig valve switches and feed)
    r.tick(Cmd::IGNITE); r.in.mv_open_sw = true; r.in.mv_closed_sw = false; r.in.pfeed_Pa = 48e5f; r.until(State::IGNITION, 2000);
    return r.e.state() == State::IGNITION;
  };
  Rig5 a; int ev = 0; const bool ab = noLightAbort(a, &ev);
  can::TlmRelight t1; const bool d1 = can::decodeTlmRelight(can::encodeTlmRelight(1, a.o), &t1);
  const bool flagged = ab && ev == 1 && a.o.seg_vapour && a.e.segVapour() && d1 && (t1.flags & tlmr::POST_ABORT) && !(t1.flags & (tlmr::VALID | tlmr::PRIMED));
  const bool ra = rearm(a); const bool st = startTo(a);
  const bool r1 = st && a.e.ignRule() == rule::FIRST && a.o.seg_vapour;
  a.run(150); a.setPc(6.0e5f); int clr = 0;
  for (int k = 0; k < 100 && a.e.state() != State::RUN; ++k) { a.tick(); clr += a.o.seg_vapour_clear; }
  a.run(5); clr += 0;
  const bool cleared = a.e.state() == State::RUN && clr == 1 && !a.o.seg_vapour && !a.e.segVapour();
  check(flagged && ra && r1 && cleared,
        "v2.8 final post-abort flag, flight pad: NO_IGNITION abort -> vapour flag (one NV set event), TLM POST_ABORT with VALID 0; retry after "
        "the vent wait keeps R1 (flight); the light clears it (one NV clear event)", fmt("set events %.0f, clear events %.0f", ev, clr));
  Rig5 s; s.in.load_cell_N = 0.0f; s.in.mode_strap = strap::STAND; int evs = 0; const bool abs_ = noLightAbort(s, &evs);
  const bool rs = rearm(s);
  s.in.tc_mss2_valid = false; s.run(2); s.tick(Cmd::IGNITE); s.run(2);
  const bool r4 = s.e.state() == State::ARMED && s.o.cmd_refused == refuse::R4_SENSOR && s.e.ignRefusedR4() == 1;
  s.in.tc_mss2_valid = true; s.run(2);
  const bool ss = startTo(s); const double t0 = s.t;
  const bool r2 = ss && s.e.ignRule() == rule::STAND_DEFAULT && std::fabs(s.e.ignitionWindow() - cfg::kIgnWindowRelightStand_s) < 1e-6f;
  int n = 0; while (s.e.state() == State::IGNITION && n < 2000) { s.tick(); ++n; }
  const int n_exp = static_cast<int>(std::lround(1000.0 * (s.e.liftCommandTime() - t0 + cfg::kIgnWindowRelightStand_s))) + 1;
  check(abs_ && evs == 1 && rs && r4 && r2 && s.e.abortCause() == Abort::NO_IGNITION && std::abs(n - n_exp) <= 1,
        "v2.8 final post-abort flag, stand: the next start after safing is a vapour-segment start - IGNITE refused with MSS-2 invalid (R4); "
        "accepted -> R2 (W 0.50 s, no superheat proof), NO_IGNITION at the lift + 0.50 s", fmt("abort %.0f ms after E0 (expected %.0f)", n, n_exp));
  // NV b3 (CORRUPT = pending) and the defensive invariant: a pending flag in COAST (NV read) -> TLM UNPRIMED + POST_ABORT, RELIGHT -> PREPRESS
  const NvJamRecord j1 = nvSegVapourSet(nvJamBlank());
  NvJamRecord d; const NvJamStatus s1 = nvJamDecode(reinterpret_cast<const uint8_t*>(&j1), &d);
  const NvJamRecord j2 = nvSegVapourClear(nvLockoutSet(j1, 5u)); NvJamRecord d2; const NvJamStatus s2 = nvJamDecode(reinterpret_cast<const uint8_t*>(&j2), &d2);
  NvJamRecord bad = j1; reinterpret_cast<uint8_t*>(&bad)[3] ^= 0x01; NvJamRecord d3; const NvJamStatus s3 = nvJamDecode(reinterpret_cast<const uint8_t*>(&bad), &d3);
  const NvJamRecord j5 = nvLitSessionSet(nvJamBlank()); NvJamRecord d5; const NvJamStatus s5 = nvJamDecode(reinterpret_cast<const uint8_t*>(&j5), &d5);
  const bool nv = s1 == NvJamStatus::VALID && nvSegVapourPending(s1, d) && !nvLockoutPending(s1, d) && !nvJamPending(s1, d) &&
                  s2 == NvJamStatus::VALID && !nvSegVapourPending(s2, d2) && nvLockoutPending(s2, d2) && s3 == NvJamStatus::CORRUPT && nvSegVapourPending(s3, d3) &&
                  s5 == NvJamStatus::VALID && !nvSegVapourPending(s5, d5) && nvSegVapourAtBoot(s5, d5) && !nvSegVapourAtBoot(s2, d2) && nvSegVapourAtBoot(s1, d);
  Rig5 c; c.toIgnition(); c.lightRun(); c.burnToCoast(); c.in.nv_seg_vapour = true; c.run(50);
  can::TlmRelight t2; can::decodeTlmRelight(can::encodeTlmRelight(2, c.o), &t2);
  const bool inv = (t2.flags & tlmr::VALID) && (t2.flags & tlmr::POST_ABORT) && !(t2.flags & tlmr::PRIMED) && c.o.relight_state == segstate::UNPRIMED && t2.worst_ms == 1370;
  c.tick(Cmd::RELIGHT); const bool prep = c.e.state() == State::PREPRESS;
  check(nv && inv && prep, "v2.8 final NvJamRecord b3: set/clear independent of b1, CORRUPT = pending, boot input also set by b2 (reset during a lit "
        "burn); a pending flag in COAST -> TLM VALID|POST_ABORT, UNPRIMED (never PRIMED), 1370 ms; RELIGHT takes PREPRESS");
}
{   // (18) tank interlock (LEAD 2026-10-13, COMB v2.4 item 3; ENG-12 15-24 C): T_tank = max(valid wall DS18B20 #1/#2, Tsat(P_tank)) <= 297.15 K
    //      at ARM and at a pad first start or any stand start; a flight relight is flagged only; |wall mean - Tsat| > 3 K = cross-check flag
  float ts50 = 0.0f; const bool ts_ok = n2o::tsatK(50e5f + 101325.f, &ts50);   // rig P_tank 50 bar g
  Rig5 a; a.in.ttank_wall_K[0] = 297.5f; a.tick(Cmd::ARM);
  const bool wall = a.e.state() == State::SAFE && a.e.abortCause() == Abort::TANK_HOT && a.o.tank_hot;
  Rig5 b; b.in.ptank_Pa = 56e5f; b.tick(Cmd::ARM);
  const bool sat = b.e.state() == State::SAFE && b.e.abortCause() == Abort::TANK_HOT && b.o.tank_T_K > cfg::kTankIgnMax_K;
  Rig5 c; c.in.ttank_wall_valid[0] = c.in.ttank_wall_valid[1] = false; c.in.ptank_valid = false; c.tick(Cmd::ARM);
  const bool none = c.e.state() == State::SAFE && c.e.abortCause() == Abort::TANK_HOT && std::isnan(c.o.tank_T_K) && c.o.tank_hot;
  Rig5 d; d.in.ttank_wall_valid[0] = d.in.ttank_wall_valid[1] = false; d.tick(Cmd::ARM);
  Rig5 e; e.in.ptank_valid = false; e.in.ttank_wall_K[0] = 296.0f; e.tick(Cmd::ARM);
  const bool one = d.e.state() == State::ARMED && std::fabs(d.o.tank_T_K - ts50) < 1e-3f && e.e.state() == State::ARMED && std::fabs(e.o.tank_T_K - 296.0f) < 1e-3f;
  check(ts_ok && wall && sat && none && one,
        "v2.8 final tank interlock at ARM: refused (TANK_HOT) with a wall at 297.5 K, with P_tank 56 bar g (Tsat above 297.15 K) and with no valid "
        "reading; accepted on Tsat(P_tank) alone (walls invalid) or on the walls alone (P_tank invalid, 296 K)",
        fmt("Tsat(56 bar g) %.2f K, Tsat(50 bar g) %.2f K", b.o.tank_T_K, ts50));
  Rig5 f; f.tick(Cmd::ARM); f.run(600); f.in.ttank_wall_K[1] = 298.0f; f.run(2); f.tick(Cmd::IGNITE); f.run(2);
  const bool pad = f.e.state() == State::ARMED && f.o.cmd_refused == refuse::TANK_HOT && f.e.ignRefusedTank() == 1;
  Rig5 s; s.in.load_cell_N = 0.0f; s.in.mode_strap = strap::STAND; s.toIgnition(); s.lightRun(); s.burnToCoast();
  s.in.ttank_wall_K[0] = 298.0f; s.run(2); const uint8_t blk = s.o.relight_block; s.tick(Cmd::RELIGHT); s.run(2);
  const bool stand = s.e.state() == State::COAST && s.o.cmd_refused == refuse::TANK_HOT && blk == refuse::TANK_HOT && s.e.ignRefusedTank() == 1;
  Rig5 g; g.toIgnition(); g.lightRun(); g.burnToCoast(); g.in.ttank_wall_K[0] = 298.0f; g.run(2);
  const bool g_blk = g.o.relight_block == refuse::NONE && g.o.tank_hot && !g.o.tank_hot_relight;
  g.tick(Cmd::RELIGHT); const bool flight = g.e.state() == State::IGNITION && g.o.tank_hot_relight;
  check(pad && stand && g_blk && flight,
        "v2.8 final tank interlock at the start: pad IGNITE refused (TANK_HOT) when a wall reads 298 K after ARM; stand RELIGHT refused (TLM block "
        "TANK_HOT); flight RELIGHT accepted with the tank_hot_relight flag (flag only)");
  Rig5 x; x.in.ttank_wall_K[0] = x.in.ttank_wall_K[1] = 289.0f; x.run(2);
  const bool xc = x.o.tank_xcheck && !x.o.tank_hot;
  x.in.ttank_wall_K[0] = x.in.ttank_wall_K[1] = 293.0f; x.run(2); const bool latched = x.o.tank_xcheck;
  x.tick(Cmd::DISARM); const bool cleared = !x.o.tank_xcheck;
  x.tick(Cmd::ARM); const bool armx = x.e.state() == State::ARMED;
  Rig5 h; h.in.ptank_Pa = 71.5e5f; h.run(5);   // 72.5 bar abs, beyond the table (critical 72.45 bar abs)
  const bool beyond = h.o.tank_hot && std::fabs(h.o.tank_T_K - n2o::kTsat_K[n2o::kSatN - 1]) < 1e-3f;
  check(xc && latched && cleared && armx && beyond,
        "v2.8 final tank cross-check: wall mean 289 K vs Tsat 293.6 K -> flag (latched, cleared by DISARM in SAFE, ARM allowed); P_tank beyond "
        "72.0 bar abs counts as the table's last temperature (hot)", fmt("table last %.2f K", n2o::kTsat_K[n2o::kSatN - 1]));
}
{   // (19) RUN-entry Pc reference (SIL v2.8 S6 hard_start finding, kept in results/sil_v2p8_draft/sil_run_log.txt): a late light confirmed
    //      during its pressure spike no longer sets the flameout/band reference at the spike; reference = min(measured, map Pc of the lift)
  Rig5 r; r.toIgnition(); r.run(260);   // late light, inside W (E1 ~2 ms + 0.40 s)
  r.setPc(20.0e5f);                      // spike below the 30 bar abort
  r.until(State::RUN, 20); r.tick(); const float ref0 = r.e.pcRef();
  r.setPc(3.5e5f); r.run(200);           // lit at the ignition lift after the spike (below the map value, as the SIL plant)
  const bool lit = r.e.state() == State::RUN && r.e.abortCause() == Abort::NONE;
  r.follow = true; r.run(400);
  check(ref0 < 5.0e5f && lit && r.e.state() == State::RUN && r.e.abortCause() == Abort::NONE,
        "v2.8 final RUN entry at a 20 bar spike: reference starts at the map Pc of the ignition lift (not the spike); the chamber at 3.5 bar abs "
        "after the spike is not a FLAMEOUT; the burn continues (pre-fix: reference at the spike, false FLAMEOUT in the SIL)",
        fmt("reference %.2f bar abs one tick after RUN entry", ref0 / 1e5));
}
{   // (20) TLM_RELIGHT VALID timing (v2.8 final): VALID only in COAST after the MECO valve closure (CLOSED switch with OPEN clear, latch off),
    //      or once the closure is overdue (kMvCloseConfirm_s after the unlatch; no closed-valve proof -> UNPRIMED, fault MV)
  Rig5 r; r.toIgnition(); r.lightRun(); r.run(300); r.tick(Cmd::SHUTDOWN); r.setPc(101325.f);
  bool valid_early = false, none_shut = true; int n_unl = -1, n_coast = -1, n_valid = -1;
  for (int n = 1; n <= 1500; ++n) {
    r.tick();
    if (!r.o.mv_latch) { r.in.mv_open_sw = false; r.in.mv_closed_sw = false; if (n_unl < 0) n_unl = n; }   // CLOSED switch never makes
    if (n_coast < 0 && r.e.state() == State::COAST) n_coast = n;
    if (n_valid < 0 && r.o.meco_closed) n_valid = n;
    if (r.e.state() == State::SHUTDOWN) none_shut = none_shut && r.o.relight_state == segstate::NONE;
    if (r.e.state() != State::COAST && r.o.meco_closed) valid_early = true;
  }
  const int dv = n_valid - n_unl;
  check(none_shut && !valid_early && n_coast > 0 && dv >= 500 && dv <= 502 && r.o.relight_state == segstate::UNPRIMED && (r.o.fault_bits & fault::MV),
        "v2.8 final TLM VALID with the CLOSED switch failed: NONE through SHUTDOWN; VALID only once the closure is overdue (0.5 s after the "
        "unlatch) and then UNPRIMED (no closed-valve proof), fault MV", fmt("VALID %.0f ms after the unlatch", dv));
  Rig5 q; q.toIgnition(); q.lightRun(); q.run(300); q.tick(Cmd::SHUTDOWN); q.setPc(101325.f);
  int m_coast = -1, m_valid = -1;
  for (int n = 1; n <= 800; ++n) {
    q.tick(); if (!q.o.mv_latch) { q.in.mv_open_sw = false; q.in.mv_closed_sw = true; }
    if (m_coast < 0 && q.e.state() == State::COAST) m_coast = n;
    if (m_valid < 0 && q.o.meco_closed) m_valid = n;
  }
  const bool prim = q.o.relight_state == segstate::PRIMED;
  q.tick(Cmd::RELIGHT); const bool gone = q.o.relight_state == segstate::NONE && !q.o.meco_closed;
  check(m_coast > 0 && m_valid == m_coast + 1 && prim && gone,
        "v2.8 final TLM VALID with healthy switches: one tick after the COAST entry (CLOSED seen in this coast) -> PRIMED; NONE again once the "
        "RELIGHT leaves COAST", fmt("COAST at %.0f ms, VALID at %.0f ms after SHUTDOWN", m_coast, m_valid));
}
{   // (21) v2.8.1 (LEAD 2026-10-13 stand fallback (b)): a stand start that does not confirm Pc within W = 0.35 s from the lift command ends
    //      in NO_IGNITION at E1 + 0.351 s; on that tick the NC valve latch is dropped (enter(ABORT)) and the pintle command closes from the
    //      ignition lift at the close rate; the torch valves are shut. First start (PREPRESS path) and relight (direct path, latch at E0)
  struct Res { bool ok = false; double w_ms = 0; int n_close = -1; bool latch_before = false, same_tick = false, torch_shut = false; };
  auto standNoLight = [](Rig5& r, bool relight) {
    Res q;
    r.in.load_cell_N = 0.0f; r.in.mode_strap = strap::STAND;
    if (relight) { r.toIgnition(); r.lightRun(); r.burnToCoast(); r.toRelight(); } else r.toIgnition();
    const double t0 = r.t;
    while (r.e.state() == State::IGNITION && r.t - t0 < 2.0) {
      q.latch_before = r.o.mv_latch;
      r.tick();
    }
    q.w_ms = 1e3 * (r.t - r.e.liftCommandTime());
    q.same_tick = r.e.state() == State::ABORT && !r.o.mv_latch && r.o.pintle_cmd_m < r.e.ignLift();
    q.torch_shut = !r.o.sol[0] && !r.o.sol[1] && !r.o.spark_gate;
    for (int n = 0; n < 50 && q.n_close < 0; ++n) { if (r.o.pintle_cmd_m <= 0.0f) q.n_close = n; else r.tick(); }
    q.ok = r.e.abortCause() == Abort::NO_IGNITION && std::fabs(r.e.ignitionWindow() - 0.35f) < 1e-6f && r.e.modeStand();
    return q;
  };
  Rig5 a; const Res fa = standNoLight(a, false);
  Rig5 b; const Res fb = standNoLight(b, true);
  check(fa.ok && fb.ok && fa.latch_before && fb.latch_before && fa.same_tick && fb.same_tick && fa.torch_shut && fb.torch_shut &&
            fa.n_close >= 0 && fa.n_close <= 5 && fb.n_close >= 0 && fb.n_close <= 5 && std::fabs(fa.w_ms - 351.0) <= 1.0 && std::fabs(fb.w_ms - 351.0) <= 1.0 &&
            b.e.ignRule() == rule::STAND_DEFAULT && a.e.ignRule() == rule::FIRST,
        "v2.8.1 stand no-light (LEAD request): first start (R1) and relight (R2) not confirmed within 0.35 s -> NO_IGNITION at E1 + 351 ms; MV latch "
        "dropped on the abort tick (latched before), pintle command closing on that tick and at 0 within 5 ms, torch valves and spark off",
        fmt("abort at E1 + %.0f / %.0f ms; pintle command 0 after %.0f ms (first start)", fa.w_ms, fb.w_ms, fa.n_close));
}
{   // (22) v2.8.1 the stand windows are keyed off the mode strap latched at ARM: a FLIGHT strap (no load cell) never loads them (first start
    //      0.40 s, relight 0.65 s); a STAND strap with a load cell gets 0.35 / 0.35 s; a strap that changes after ARM does not change the
    //      window (mode latched, MODE_MISMATCH flag); a strap / load-cell disagreement refuses ARM
  Rig5 f; f.toIgnition(); const float wf1 = f.e.ignitionWindow(); f.lightRun(); f.burnToCoast(); f.toRelight(); const float wf2 = f.e.ignitionWindow();
  Rig5 s; s.in.load_cell_N = 0.0f; s.in.mode_strap = strap::STAND; s.toIgnition(); const float ws1 = s.e.ignitionWindow();
  s.lightRun(); s.burnToCoast(); s.toRelight(); const float ws2 = s.e.ignitionWindow();
  Rig5 m; m.toIgnition(); m.lightRun(); m.burnToCoast();
  m.in.mode_strap = strap::STAND; m.in.load_cell_N = 0.0f; m.run(5); m.toRelight();   // strap moved to STAND in flight: latched FLIGHT stays
  const float wm = m.e.ignitionWindow(); const bool mm = m.e.modeMismatch() && !m.e.modeStand();
  Rig5 x; x.in.mode_strap = strap::STAND; x.tick(Cmd::ARM); x.run(5);           // STAND strap without a load cell -> ARM refused
  Rig5 y; y.in.load_cell_N = 0.0f; y.tick(Cmd::ARM); y.run(5);                  // FLIGHT strap with a load cell -> ARM refused
  check(std::fabs(wf1 - 0.40f) < 1e-6f && std::fabs(wf2 - 0.65f) < 1e-6f && std::fabs(ws1 - 0.35f) < 1e-6f && std::fabs(ws2 - 0.35f) < 1e-6f &&
            std::fabs(wm - 0.65f) < 1e-6f && mm && x.e.state() == State::SAFE && x.e.abortCause() == Abort::MODE_MISMATCH &&
            y.e.state() == State::SAFE && y.e.abortCause() == Abort::MODE_MISMATCH,
        "v2.8.1 windows keyed off the strap: FLIGHT 0.40 / 0.65 s; STAND 0.35 / 0.35 s; strap changed after ARM -> window unchanged (0.65 s), "
        "MODE_MISMATCH flag; STAND strap without load cell or FLIGHT strap with load cell -> ARM refused (MODE_MISMATCH)",
        fmt("flight %.2f / %.2f s, stand %.2f s", wf1, wf2, ws1));
}
{   // (23) v2.8.1 ABORT / SHUTDOWN exit: an invalid Pc reading cannot declare the chamber vented. Pc channel failed low in RUN (flight, open
    //      loop), then ABORT: the ARM bus stays requested (pintle powered, driven closed) until kShutdownTimeout_s 0.5 s, then SAFE. Same abort
    //      with a VALID Pc reading 1 bar abs: SAFE after the 50 ms minimum (v2.8 behaviour, unchanged)
  Rig5 a; a.thrust = 400.f; a.follow = true; a.toIgnition(); a.lightRun(); a.run(300); a.follow = false;
  a.in.pc_raw_V = 0.02f; a.in.pc_Pa = (0.02f - 0.5f) / 4.0f * cfg::kPcXdcrFs_Pa;   // failed LOW: the HAL reading follows the voltage (-8.4 bar g)
  a.run(20); const bool ol = a.e.state() == State::RUN && !a.e.pcSensorOk();
  a.tick(Cmd::ABORT); int na = 0; bool req = true;
  while (a.e.state() == State::ABORT && na < 1000) { a.tick(); ++na; if (a.e.state() == State::ABORT) req = req && a.o.arm_bus_request; }
  Rig5 b; b.thrust = 400.f; b.follow = true; b.toIgnition(); b.lightRun(); b.run(300); b.follow = false;
  b.tick(Cmd::ABORT); b.setPc(101325.f); int nb = 0;
  while (b.e.state() == State::ABORT && nb < 1000) { b.tick(); ++nb; }
  check(ol && req && a.e.state() == State::SAFE && na >= 500 && na <= 502 && b.e.state() == State::SAFE && nb >= 50 && nb <= 60,
        "v2.8.1 ABORT exit: Pc channel invalid -> ABORT held with the ARM bus requested until 0.5 s (pintle driven closed under power), then SAFE; "
        "Pc valid at 1 bar abs -> SAFE after ~50 ms (unchanged)",
        fmt("invalid Pc: SAFE after %.0f ms; valid Pc: SAFE after %.0f ms", na, nb));
}
{   // (24) v2.8.2 GNC review REV-GNC-1 RG-08: a pintle-position anomaly in the coast latches the relight state and forces the prep path.
    //      (a) encoder invalid for ONE coast tick -> UNKNOWN on that tick and after the encoder returns (latched), worst 1370 ms; RELIGHT ->
    //      PREPRESS; the relight lights -> RUN entry clears the latch -> the next coast is PRIMED again. (b) encoder lift 0.12 mm (below the
    //      0.15 mm stall error): PRIMED for 19 ticks, UNPRIMED from the 20th and after the needle reads seated again; RELIGHT -> PREPRESS.
    //      (c) a 15 ms excursion to 0.30 mm (shock bounce) -> no latch, direct relight. (d) 0.20 mm (above the stall error): UNPRIMED at
    //      20 ms, stall monitor PINTLE_FAULT at ~0.10 s. (e) one-tick event, log v9 seq3 b7, event argument, DISARM in SAFE clears.
  can::TlmRelight fa, fb;
  Rig5 a; a.toIgnition(); a.lightRun(); a.burnToCoast(); a.run(50);
  const bool a0 = a.o.relight_state == segstate::PRIMED && a.o.coast_pintle == 0u;
  a.pfollow = false; a.in.pintle_meas_valid = false; a.tick();
  const bool a1 = a.o.relight_state == segstate::UNKNOWN && a.o.coast_pintle == 1u && a.o.coast_pintle_event == 1u && a.o.relight_worst_ms == 1370;
  a.in.pintle_meas_valid = true; a.in.pintle_meas_m = 0.0f; a.tick();
  const bool a2 = a.o.relight_state == segstate::UNKNOWN && a.o.coast_pintle_event == 0u && a.e.coastEncLost();
  a.run(100);
  const bool a3 = can::decodeTlmRelight(can::encodeTlmRelight(3, a.o), &fa) && tlmr::stateOf(fa.flags) == segstate::UNKNOWN && fa.ratio_pct == 96 &&
                  fa.worst_ms == 1370 && (fa.flags & tlmr::READY);
  a.pfollow = true; const int na = a.toRelight();
  const bool a4 = na > 400 && na < 700 && !a.e.relightDirect();
  const bool lit = a.lightRun(); const bool cleared = !a.e.coastPintleAnomaly(); a.burnToCoast(); a.run(50);
  const bool a5 = lit && cleared && a.o.relight_state == segstate::PRIMED && a.o.coast_pintle == 0u;
  check(a0 && a1 && a2 && a3 && a4 && a5,
        "v2.8.2 RG-08 (a): pintle encoder invalid for one COAST tick -> TLM UNKNOWN on that tick and latched after the encoder returns (ratio 96 %, "
        "worst 1370 ms, READY); RELIGHT -> prep path; the light (RUN entry) clears the latch; next coast PRIMED",
        fmt("RELIGHT -> IGNITION %.0f ms (prep path)", na));
  Rig5 b; b.toIgnition(); b.lightRun(); b.burnToCoast(); b.run(50);
  b.pfollow = false; b.in.pintle_meas_m = 0.12e-3f;
  int n_unp = -1; bool primed_before = true;
  for (int n = 1; n <= 40; ++n) {
    b.tick();
    if (n_unp < 0 && b.o.relight_state == segstate::UNPRIMED) n_unp = n;
    if (n_unp < 0) primed_before = primed_before && b.o.relight_state == segstate::PRIMED;
  }
  b.in.pintle_meas_m = 0.0f; b.run(50);
  const bool b1 = can::decodeTlmRelight(can::encodeTlmRelight(4, b.o), &fb) && tlmr::stateOf(fb.flags) == segstate::UNPRIMED && fb.ratio_pct == 96 &&
                  fb.worst_ms == 1370 && b.o.coast_pintle == 2u && b.e.state() == State::COAST && b.e.abortCause() == Abort::NONE;
  LogRecord lb; b.e.fillLog(b.in, b.o, lb);
  const bool b2 = lb.version == 9 && (lb.seq3_flags & 0x80u) && (lb.seq3_flags & 0x03u) == segstate::UNPRIMED;
  b.pfollow = true; const int nb = b.toRelight();
  check(n_unp == cfg::kCoastPintleOpenN && primed_before && b1 && b2 && nb > 400 && !b.e.relightDirect(),
        "v2.8.2 RG-08 (b): encoder lift 0.12 mm in COAST (stall monitor quiet below 0.15 mm) -> PRIMED for 19 ticks, UNPRIMED from the 20th, "
        "latched after the needle reads seated (P_feed ratio still 96 %); log v9 seq3 b7; RELIGHT -> prep path",
        fmt("UNPRIMED after %.0f ticks; RELIGHT -> IGNITION %.0f ms", n_unp, nb));
  Rig5 c; c.toIgnition(); c.lightRun(); c.burnToCoast(); c.run(50);
  c.pfollow = false; c.in.pintle_meas_m = 0.30e-3f; c.run(15); c.in.pintle_meas_m = 0.0f; c.run(30);
  const bool c1 = c.o.relight_state == segstate::PRIMED && c.o.coast_pintle == 0u && c.e.abortCause() == Abort::NONE && c.e.state() == State::COAST;
  c.pfollow = true; const int nc = c.toRelight();
  Rig5 d; d.toIgnition(); d.lightRun(); d.burnToCoast(); d.run(50);
  d.pfollow = false; d.in.pintle_meas_m = 0.20e-3f;
  int n_u = -1, n_ab = -1;
  for (int n = 1; n <= 200 && n_ab < 0; ++n) {
    d.tick();
    if (n_u < 0 && d.o.relight_state == segstate::UNPRIMED) n_u = n;
    if (d.e.state() == State::ABORT) n_ab = n;
  }
  check(c1 && nc == 0 && c.e.relightDirect() && n_u == cfg::kCoastPintleOpenN && n_ab >= 99 && n_ab <= 102 && d.e.abortCause() == Abort::PINTLE_FAULT,
        "v2.8.2 RG-08 (c, d): a 15 ms excursion to 0.30 mm (shock bounce) does not latch (direct relight); 0.20 mm (above the 0.15 mm stall "
        "error) -> UNPRIMED at 20 ms, then the stall monitor aborts PINTLE_FAULT at ~0.10 s",
        fmt("0.20 mm: UNPRIMED at %.0f ms, abort at %.0f ms", n_u, n_ab));
  Rig5 e; e.toIgnition(); e.lightRun(); e.burnToCoast(); e.run(50);
  e.pfollow = false; e.in.pintle_meas_m = 0.12e-3f; int ev = 0;
  for (int n = 0; n < 60; ++n) { e.tick(); if (e.o.coast_pintle_event) ++ev; }
  e.in.pintle_meas_m = 0.0f; e.pfollow = true;
  e.tick(Cmd::DISARM); const bool still = e.e.state() == State::SAFE && e.e.coastPintleAnomaly();   // COAST -> SAFE: latch kept
  e.tick(Cmd::DISARM); const bool gone = !e.e.coastPintleAnomaly() && e.o.coast_pintle == 0u;      // DISARM in SAFE (ack): cleared
  const bool arg = evt::coastPintleArg(2, true, 0.12e-3f) == static_cast<uint16_t>(2u | (12u << 8)) &&
                   evt::coastPintleArg(1, false, 0.0f) == static_cast<uint16_t>(1u | 0xFF00u) &&
                   evt::coastPintleArg(2, true, 3.0e-3f) == static_cast<uint16_t>(2u | (254u << 8)) && evt::COAST_PINTLE == 0x1C;
  check(ev == 1 && still && gone && arg,
        "v2.8.2 RG-08 (e): EVENT COAST_PINTLE one tick per latch; DISARM from COAST keeps the latch, DISARM in SAFE clears it; event argument "
        "kind | lift [10 um] << 8 (0xFF invalid, 254 cap)", fmt("events %.0f", ev));
}
{   // (25) v2.8.2 GNC RG-15 (LEAD 2026-10-13: FC_THRUST does NOT freeze on a Pc loss; k_est_asc and the B apex predictor DO): Pc-derived
    //      telemetry carries an invalid marker. Pc channel failed low in RUN -> Outputs::pc_valid false, TLM_FAST d2-d3 = 0xFFFF (fault bit
    //      PC_SENSOR latched in d6-d7), TLM_GIMBAL thrust d6-d7 = 0xFFFF via tlmThrust(); valid channel -> kPa and 0.1 N values
  Rig5 a; a.thrust = 400.f; a.follow = true; a.toIgnition(); a.lightRun(); a.run(300);
  const can::Frame f1 = can::encodeTlmFast(1, a.o, a.e.pcAbsFiltered(), a.o.pintle_cmd_m);
  const float m0[2] = {0.0f, 0.0f};
  const can::Frame g1 = can::encodeTlmGimbal(1, a.o.gimbal_flags, m0, can::tlmThrust(a.o));
  const unsigned pc1 = f1.d[2] | (f1.d[3] << 8), th1 = g1.d[6] | (g1.d[7] << 8);
  const bool ok1 = a.o.pc_valid && pc1 != 0xFFFFu && std::abs(static_cast<int>(pc1) - static_cast<int>(std::lround(a.e.pcAbsFiltered() / 1000.f))) <= 1 &&
                   th1 != 0xFFFFu && std::abs(static_cast<int>(th1) - static_cast<int>(std::lround(a.o.thrust_est_N * 10.f))) <= 1;
  a.follow = false; a.in.pc_raw_V = 0.02f; a.in.pc_Pa = (0.02f - 0.5f) / 4.0f * cfg::kPcXdcrFs_Pa; a.run(5);
  const can::Frame f2 = can::encodeTlmFast(2, a.o, a.e.pcAbsFiltered(), a.o.pintle_cmd_m);
  const can::Frame g2 = can::encodeTlmGimbal(2, a.o.gimbal_flags, m0, can::tlmThrust(a.o));
  const unsigned pc2 = f2.d[2] | (f2.d[3] << 8), th2 = g2.d[6] | (g2.d[7] << 8), fb2 = f2.d[6] | (f2.d[7] << 8);
  const bool ok2 = !a.o.pc_valid && pc2 == 0xFFFFu && th2 == 0xFFFFu && (fb2 & fault::PC_SENSOR) && a.e.state() == State::RUN;
  check(ok1 && ok2,
        "v2.8.2 RG-15: Pc channel valid -> TLM_FAST Pc kPa and TLM_GIMBAL thrust 0.1 N carry values; channel failed low in RUN (flight, open loop) "
        "-> pc_valid false, both fields 0xFFFF (invalid marker for the FC freeze), PC_SENSOR fault bit set, burn continues",
        fmt("valid: %.0f kPa, %.1f N", pc1, th1 * 0.1));
}
