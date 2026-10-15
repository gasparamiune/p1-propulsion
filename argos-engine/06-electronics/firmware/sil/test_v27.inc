// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175: expectations updated; full list in 06-electronics/REPORT-v2.10-HANDBACK.md] ------------------------------------------------------------- v2.7 Combustion review fold-in (LEAD 2026-10-13): unit tests.
// v2.8 edits (LEAD 2026-10-13 decisions): torch gate 0.16 s (cfg::kTorchGate_s), windows from the lift command (R1 0.40 s, flight relight
// 0.65 s), stand rigs carry the coded mode strap (STAND) with the load cell, (4) C7 gate-TC extension retired -> flight relight window,
// (9) direct relight needs a primed segment AND a confirmed-closed valve, (10) log v7. The v2.7 results stay in results/sil_v2p7.
// Included inside the v2.5 Rig5 block of test_core.cpp (Rig5, check, fmt, hex in scope). Rigs are ideal (instant pintle follower,
// ideal torch unless torch_dead / ptorch_bad); the SIL (sil_main.cpp S6/S10) runs the same logic against the plant models.
{   // (1) RC-01 torch-flame gate: no flame -> TORCH_FAULT at cfg::kTorchGate_s (v2.8 0.16 s; v2.7 0.100 s), BEFORE the lift (no N2O through the
    //     pintle); NC valve and torch valves dropped on the abort tick; an invalid P_torch reading is treated as no flame
  for (int variant = 0; variant < 2; ++variant) {
    Rig5 r; if (variant == 0) r.torch_dead = true; else r.ptorch_bad_from_ignite = true;   // (ARM refuses an invalid P_torch: group 12)
    r.toIgnition();
    int n = 0, n2o_alone = 0; float xmax = 0;
    while (r.e.state() == State::IGNITION && n < 1000) { r.tick(); ++n; xmax = std::fmax(xmax, r.o.pintle_cmd_m); n2o_alone += r.o.sol[0] && !r.o.sol[1]; }
    const bool drop = !r.o.mv_latch && !r.o.sol[0] && !r.o.sol[1] && !r.o.igniter_enable && !r.o.spark_gate;
    check(r.e.abortCause() == Abort::TORCH_FAULT && n == static_cast<int>(1000 * cfg::kTorchGate_s + 0.5f) + 1 && xmax == 0.0f && drop &&
              n2o_alone == 0 && (r.o.fault_bits & fault::NO_IGNITION),
          variant == 0 ? "v2.8 RC-01 gate: no torch flame -> TORCH_FAULT at 0.161 s (gate 0.16 s), pintle never lifted (the lift waits for E1); MV, torch and spark off on the abort tick"
                       : "v2.8 RC-01 gate: P_torch reading invalid -> treated as no flame (TORCH_FAULT at 0.161 s, fail-safe)",
          fmt("abort after %.0f ms, pintle command max %.3f mm", n, xmax * 1e3));
  }
}
{   // (2) RC-01 ground timing-only start: SET_TORCH_GATE key in SAFE on a test stand (v2.8: STAND strap AND finite load cell), first
    //     start only, the smallest table lift (<= 12.5 %) at the COMB 0.12 s slot; W from that lift = stand R1 (v2.8.1: 0.35 s)
  Rig5 r; r.torch_dead = true; r.in.load_cell_N = 0.0f; r.in.mode_strap = strap::STAND;
  r.tick(Cmd::SET_TORCH_GATE, cfg::kTorchTimingOnlyKey);
  const bool armed = r.o.torch_gate_bypass;
  r.toIgnition();
  float xmax = 0; int n = 0;
  while (r.e.state() == State::IGNITION && n < 1000) { r.tick(); ++n; xmax = std::fmax(xmax, r.o.pintle_cmd_m); }
  const int n2 = static_cast<int>(std::lround(1000.0 * (cfg::kTimingOnlyLiftAt_s + cfg::kIgnWindowFirstStand_s))) + 1;
  check(armed && r.e.timingOnlyThisStart() && r.e.abortCause() == Abort::NO_IGNITION && std::abs(n - n2) <= 2 &&
            std::fabs(xmax - cfg::kTimingOnlyLift_m) < 1e-7f,
        "v2.8.1 ground timing-only start (stand strap + key, first start): gate bypassed, pintle to the table minimum at 0.12 s, NO_IGNITION at 0.12 + 0.35 s (stand R1)",
        fmt("lift %.4f mm (table max %.4f mm), abort after %.0f ms", xmax * 1e3, cfg::kPintleUnlitLiftMax_m * 1e3, n));
  Rig5 f; f.torch_dead = true;   // flight: FLIGHT strap and NaN load cell -> the key is refused
  f.tick(Cmd::SET_TORCH_GATE, cfg::kTorchTimingOnlyKey); const bool f_armed = f.o.torch_gate_bypass;
  f.toIgnition(); f.until(State::ABORT, 1000);
  Rig5 w; w.in.load_cell_N = 0.0f; w.in.mode_strap = strap::STAND; w.tick(Cmd::SET_TORCH_GATE, 0x1234); const bool w_armed = w.o.torch_gate_bypass;
  Rig5 d; d.in.load_cell_N = 0.0f; d.in.mode_strap = strap::STAND; d.tick(Cmd::SET_TORCH_GATE, cfg::kTorchTimingOnlyKey); d.tick(Cmd::DISARM); const bool d_armed = d.o.torch_gate_bypass;
  check(!f_armed && f.e.abortCause() == Abort::TORCH_FAULT && !w_armed && !d_armed,
        "v2.7 timing-only key refused in flight (NaN load cell -> TORCH_FAULT), wrong key ignored, DISARM in SAFE clears it");
  // relight in the same arming session is always gated: stand + key, first start lit (torch works), relight with a dead torch
  Rig5 g; g.in.load_cell_N = 0.0f; g.in.mode_strap = strap::STAND; g.tick(Cmd::SET_TORCH_GATE, cfg::kTorchTimingOnlyKey);
  g.toIgnition(); const bool lit1 = g.lightRun(); const bool coast = g.burnToCoast();
  g.torch_dead = true; g.toRelight(); g.until(State::ABORT, 1000);
  check(lit1 && coast && g.e.abortCause() == Abort::TORCH_FAULT && !g.e.timingOnlyThisStart(),
        "v2.7 timing-only applies to the first start of the arming session only: a relight with no torch flame -> TORCH_FAULT");
}
{   // (3) LEAD 2026-10-13: NO automatic in-flight relight retry. Relight no-light after a lit burn -> NO_IGNITION, lockout set
  Rig5 r; r.toIgnition(); const bool run1 = r.lightRun(); const bool coast = r.burnToCoast();
  r.toRelight(); r.run(125); r.setPc(kUnlitAbs);   // relight: cold flow only
  int n = 125; bool ev = false; int n_ev = 0;
  while (r.e.state() == State::IGNITION && n < 1500) { r.tick(); ++n; ev |= r.o.relight_lockout_event; n_ev += r.o.relight_lockout_event; }
  const bool at_abort = !r.o.mv_latch && r.o.relight_lockout;
  r.tick(); n_ev += r.o.relight_lockout_event;
  check(run1 && coast && r.e.abortCause() == Abort::NO_IGNITION && ev && n_ev == 1 && at_abort,
        "v2.7 relight no-light after a lit burn: NO_IGNITION, MV dropped on the abort tick, relight lockout set (one-tick event for the NV copy)",
        fmt("abort at %.0f ms after IGNITION entry", n));
  r.setPc(101325.f); r.until(State::SAFE, 2000);
  r.in.mv_open_sw = false; r.in.mv_closed_sw = true;
  r.tick(Cmd::DISARM); r.run(6000); r.tick(Cmd::ARM);
  const bool refused = r.e.state() == State::SAFE && r.e.abortCause() == Abort::RELIGHT_LOCKOUT;
  r.tick(Cmd::DISARM); r.tick(Cmd::CLEAR_LOCKOUT, 0x1111); r.tick(Cmd::ARM);
  const bool bad_key = r.e.state() == State::SAFE && r.e.clearLockoutRefused() == 1 && r.e.abortCause() == Abort::RELIGHT_LOCKOUT;
  r.tick(Cmd::DISARM); r.tick(Cmd::CLEAR_LOCKOUT, cfg::kClearLockoutKey);
  const bool pulse = r.o.relight_lockout_clear && !r.o.relight_lockout;
  r.tick(); const bool one = !r.o.relight_lockout_clear;
  r.tick(Cmd::ARM);
  check(refused && bad_key && pulse && one && r.e.state() == State::ARMED,
        "v2.7 lockout: ARM refused (RELIGHT_LOCKOUT) after DISARM + 6 s (no retry); wrong key refused; keyed CLEAR_LOCKOUT in SAFE clears (one-tick pulse)");
  Rig5 b; b.in.nv_relight_lockout = true; b.tick(Cmd::ARM);
  const bool nv_ref = b.e.state() == State::SAFE && b.e.abortCause() == Abort::RELIGHT_LOCKOUT && b.o.relight_lockout;
  b.tick(Cmd::DISARM); b.tick(Cmd::CLEAR_LOCKOUT, cfg::kClearLockoutKey); const bool nv_pulse = b.o.relight_lockout_clear;
  b.in.nv_relight_lockout = false; b.tick(); b.tick(Cmd::ARM);
  check(nv_ref && nv_pulse && b.e.state() == State::ARMED,
        "v2.7 non-volatile lockout at boot (an ECU reset in flight cannot clear it): ARM refused until CLEAR_LOCKOUT and the HAL clears the flag");
  // a flameout in the first (lit) burn also locks out further starts
  Rig5 q; q.follow = true; q.toIgnition(); const bool run2 = q.lightRun(); q.run(400);
  q.follow = false; q.setPc(101325.f); q.until(State::ABORT, 200);
  check(run2 && q.e.abortCause() == Abort::FLAMEOUT && q.o.relight_lockout, "v2.7 flameout in a lit burn -> FLAMEOUT abort and relight lockout");
  // IGNITE in COAST is refused while the lockout is pending (NV flag)
  Rig5 c; c.toIgnition(); c.lightRun(); c.burnToCoast(); c.in.nv_relight_lockout = true;
  const uint16_t ref0 = c.e.ignitionRefused(); c.tick(Cmd::RELIGHT); c.run(2);
  check(c.e.state() == State::COAST && c.e.ignitionRefused() == ref0 + 1, "v2.7 RELIGHT refused in COAST while a lockout is pending");
}
{   // (4) v2.8 (LEAD 2026-10-13; the v2.7 C7 gate-TC extension is retired): a FLIGHT relight gets W 0.65 s from the lift command on every
    //     relight, whatever the state TCs read (telemetry only in flight); torch open until the abort; spark train capped
  auto relight = [](float tc_K, bool tc_valid, Rig5& r) {
    r.toIgnition(); r.lightRun(); r.burnToCoast();
    r.in.tc_mss1_K = r.in.tc_mss2_K = tc_K; r.in.tc_mss1_valid = r.in.tc_mss2_valid = tc_valid;
    r.toRelight();
  };
  {
    Rig5 r; relight(293.15f, true, r); const double t0 = r.t;
    const bool ext = r.o.relight_ext && std::fabs(r.o.ign_check_s - cfg::kIgnWindowRelightLong_s) < 1e-6f && r.e.ignRule() == rule::FLIGHT_RELIGHT;
    int n = 0, sparks = 0, n_torch = 0; bool prev = false;
    while (r.e.state() == State::IGNITION && n < 1500) {
      if (n == 125) r.setPc(kUnlitAbs);
      r.tick(); ++n;
      if (r.o.spark_gate && !prev) ++sparks;
      prev = r.o.spark_gate; n_torch += r.o.sol[0] && r.o.sol[1];
    }
    const int n_exp = static_cast<int>(std::lround(1000.0 * (r.e.liftCommandTime() - t0 + cfg::kIgnWindowRelightLong_s))) + 1;
    check(ext && r.e.abortCause() == Abort::NO_IGNITION && std::abs(n - n_exp) <= 1 &&
              sparks == static_cast<int>(eng::kSparkTrain_s * eng::kSparkRate_Hz + 0.5f) && n_torch >= n - 2,
          "v2.8 flight relight, no light: NO_IGNITION at the lift + 0.65 s, torch open until the abort, spark train capped at 25 sparks",
          fmt("abort after %.0f ms (expected %.0f), sparks %.0f", n, n_exp, sparks) + fmt(", torch-open ticks %.0f", n_torch));
  }
  {
    Rig5 r; relight(293.15f, true, r);
    r.run(600); r.setPc(6.0e5f); r.until(State::RUN, 60);
    Rig5 v; relight(380.0f, false, v);
    const bool inval = v.o.relight_ext && v.e.ignRule() == rule::FLIGHT_RELIGHT && !v.e.superheatProven();
    check(r.e.state() == State::RUN && inval,
          "v2.8 flight relight: a vapour-delayed light 0.60 s after E0 -> RUN inside the 0.65 s window; state TCs invalid -> still 0.65 s (telemetry only, no R4 in flight)");
  }
}
{   // (5) RC-01 normal shutdown: pintle first, NC valve unlatched on the confirmed seat (5 ticks at <= 0.05 mm), then COAST
  Rig5 r; r.thrust = 300.f; r.follow = true; r.toIgnition(); const bool run1 = r.lightRun(); r.run(500);
  const float x0 = r.o.pintle_cmd_m;
  r.tick(Cmd::SHUTDOWN); r.setPc(101325.f);
  const bool held = r.o.mv_latch && r.o.mv_seat_wait;
  int n = 0, n_seat = -1, n_unl = -1, n_exit = -1;
  while (n < 600 && n_exit < 0) {
    r.tick(); ++n;
    if (n_seat < 0 && r.in.pintle_meas_m <= cfg::kPintleSeatConfirm_m) n_seat = n;
    if (n_unl < 0 && !r.o.mv_latch) n_unl = n;
    if (n_exit < 0 && r.e.state() != State::SHUTDOWN) n_exit = n;
  }
  check(run1 && held && n_seat > 0 && n_unl - n_seat == cfg::kSeatConfirmN - 1 && n_exit >= n_unl && !r.o.mv_seat_timeout &&
            !(r.o.fault_bits & fault::PINTLE),
        "v2.7 RC-01 normal shutdown: NC valve held at SHUTDOWN, unlatched kSeatConfirmN ticks after the encoder reads seated, state exits after",
        fmt("from %.2f mm: seated (encoder) +%.0f ms, valve unlatched +%.0f ms", x0 * 1e3, n_seat, n_unl) + fmt(", COAST +%.0f ms", n_exit));
  // creeping needle (3 mm/s from 1.2 mm: progress marks every 7 ms, no stall trip): valve unlatched on the 0.25 s timeout, flagged
  Rig5 q; q.thrust = 300.f; q.follow = true; q.toIgnition(); q.lightRun(); q.run(500);
  q.pfollow = false; q.in.pintle_meas_m = 1.2e-3f;
  q.tick(Cmd::SHUTDOWN); q.setPc(101325.f);
  int m = 0, m_unl = -1;
  while (m < 600 && m_unl < 0) { q.in.pintle_meas_m = std::fmax(0.0f, q.in.pintle_meas_m - 3.0e-6f); q.tick(); ++m; if (!q.o.mv_latch) m_unl = m; }
  check(m_unl == static_cast<int>(1000 * cfg::kMvSeatTimeout_s + 0.5f) && q.o.mv_seat_timeout && (q.o.fault_bits & fault::PINTLE) &&
            q.e.abortCause() == Abort::NONE && q.e.jamCount() == 0,
        "v2.7 seat not confirmed (needle creeping, monitor not tripped): NC valve unlatched on the 0.25 s timeout regardless, flagged (fault PINTLE), no abort",
        fmt("unlatched %.0f ms after SHUTDOWN, encoder %.3f mm", m_unl, q.in.pintle_meas_m * 1e3));
}
{   // (6) LEAD 2026-10-13: LTC4365 OV-disconnect trip / rail loss -> PINTLE_FAULT -> ABORT, NC valve de-energised at once
  Rig5 r; r.toIgnition(); const bool run1 = r.lightRun(); r.run(200);
  r.in.prail_V = 0.4f;
  int n = 0; while (r.e.state() == State::RUN && n < 50) { r.tick(); ++n; }
  check(run1 && r.e.abortCause() == Abort::PINTLE_FAULT && n == static_cast<int>(1000 * cfg::kPrailLostTime_s + 0.5f) && !r.o.mv_latch &&
            r.o.prail_lost && r.e.jamCount() == 0 && (r.o.fault_bits & fault::PINTLE),
        "v2.7 pintle rail lost in RUN (OV disconnect): PINTLE_FAULT after 2 ms, MV de-energised on the abort tick, prail_lost latched, not a jam",
        fmt("abort %.0f ms after the drop", n));
  Rig5 q; q.in.arm_bus_on = false; q.tick(Cmd::ARM); q.in.arm_bus_on = true; q.in.prail_V = 0.0f;
  q.run(static_cast<int>(1000 * cfg::kPrailSettle_s) - 3);
  const bool settle_ok = q.e.state() == State::ARMED;
  q.in.prail_V = 7.49f; q.run(100);
  q.in.prail_valid = false; q.in.prail_V = 0.0f; q.run(100);
  const bool inval_ok = q.e.state() == State::ARMED;
  q.in.prail_valid = true; q.run(5);
  check(settle_ok && inval_ok && q.e.abortCause() == Abort::PINTLE_FAULT,
        "v2.7 rail check ignored for 60 ms after the ARM bus comes on (soft start / LTC4365 delay) and while ADC2 is invalid; a dead rail on the pad aborts");
  q.until(State::SAFE, 1000); q.tick(Cmd::DISARM);
  check(!q.o.prail_lost, "v2.7 prail_lost cleared by DISARM in SAFE");
}
{   // (7) Pc-sensor loss in RUN: test stand aborts (PC_SENSOR, 5 ms); flight continues open loop
  Rig5 s; s.in.load_cell_N = 0.0f; s.in.mode_strap = strap::STAND; s.toIgnition(); const bool run1 = s.lightRun(); s.run(100);
  s.in.pc_raw_V = 0.02f;
  int n = 0; while (s.e.state() == State::RUN && n < 50) { s.tick(); ++n; }
  Rig5 f; f.toIgnition(); const bool run2 = f.lightRun(); f.run(100);
  f.in.pc_raw_V = 0.02f; f.run(300);
  check(run1 && s.e.abortCause() == Abort::PC_SENSOR && n >= 5 && n <= 6 && run2 && f.e.state() == State::RUN && (f.o.fault_bits & fault::OPEN_LOOP),
        "v2.7 Pc signal lost in RUN: test stand -> PC_SENSOR abort after 5 ms; flight -> burn continues open loop (fault OPEN_LOOP)",
        fmt("stand abort after %.0f ms", n));
}
{   // (8) abort matrix: every abort de-energises the NC valve ON THE ABORT TICK and commands the pintle closed in parallel
  struct Inj { const char* name; Abort expect; int kind; };
  const Inj inj[] = {{"FC ABORT frame", Abort::CMD, 0}, {"rail loss", Abort::PINTLE_FAULT, 1}, {"Pc 31 bar", Abort::PC_OVERPRESSURE, 2},
                     {"flameout", Abort::FLAMEOUT, 3}, {"link loss", Abort::LINK_LOST, 4}};
  bool all = true; std::string det;
  for (const Inj& k : inj) {
    Rig5 r; r.thrust = 400.f; r.follow = true; r.toIgnition(); r.lightRun(); r.run(800);
    r.follow = false;
    bool link = true;
    if (k.kind == 1) r.in.prail_V = 0.3f;
    if (k.kind == 2) r.setPc(31.0e5f);
    if (k.kind == 3) r.setPc(101325.f);
    if (k.kind == 4) link = false;
    float x_before = r.o.pintle_cmd_m;
    int n = 0; bool latched_before_abort = true;
    while (r.e.state() == State::RUN && n < 400) {
      x_before = r.o.pintle_cmd_m;   // command of the previous tick (the Pc loop may open the pintle before a flameout trips)
      if (link) r.tick(k.kind == 0 && n == 0 ? Cmd::ABORT : Cmd::NOP);
      else { r.t += 1e-3; r.in.t_s = r.t; r.c = Commands(); idealTorch(r.in, r.o); r.in.pintle_meas_m = r.o.pintle_cmd_m; r.e.step(r.in, r.c, r.o); }
      ++n;
      if (r.e.state() == State::RUN) latched_before_abort = latched_before_abort && r.o.mv_latch;
    }
    const bool same_tick = r.e.state() == State::ABORT && !r.o.mv_latch && r.o.pintle_cmd_m < x_before;
    const float x1 = r.o.pintle_cmd_m; r.tick(); const bool closing = r.o.pintle_cmd_m < x1 || r.o.pintle_cmd_m == 0.0f;
    const bool ok = r.e.abortCause() == k.expect && same_tick && closing && latched_before_abort;
    all = all && ok;
    det += std::string(k.name) + (ok ? " ok" : " FAIL") + fmt(" (%.0f ms); ", n);
  }
  check(all, "v2.7 abort matrix: CMD, rail loss, over-pressure, flameout, link loss -> NC valve unlatched on the abort tick, pintle command closing in parallel", det);
}
{   // (9) LEAD rule (b) kept, v2.8 Finding A: the direct COAST -> IGNITION path needs a primed segment AND the valve shown closed by both
    //     switches at E0; an MV switch reading open in the coast (switch fault / valve not closed) falls back to PREPRESS
  Rig5 r; r.toIgnition(); r.lightRun(); r.burnToCoast();
  r.in.mv_open_sw = true; r.in.mv_closed_sw = false; r.in.pfeed_Pa = 48e5f;   // switch fault / trapped primed line
  r.tick(Cmd::RELIGHT);
  Rig5 q; q.toIgnition(); q.lightRun(); q.burnToCoast(); q.in.pfeed_Pa = 48e5f;
  q.tick(Cmd::RELIGHT);
  check(r.e.state() == State::PREPRESS && q.e.state() == State::IGNITION && q.e.relightDirect(),
        "v2.8 RELIGHT from COAST: OPEN switch made / CLOSED not made -> PREPRESS; primed segment with the valve shown closed -> direct IGNITION");
}
{   // (10) log v7 (v6 fields unchanged) and the non-volatile lockout bit
  Rig5 r; r.in.load_cell_N = 0.0f; r.in.mode_strap = strap::STAND; r.in.pintle_i_valid = true; r.in.pintle_i_A = 1.234f; r.in.prail_V = 7.512f;
  r.in.tc_bore_valid = true; r.in.tc_bore_K = 300.15f;
  r.tick(Cmd::SET_TORCH_GATE, cfg::kTorchTimingOnlyKey);
  r.toIgnition(); r.run(30);
  LogRecord lg; r.e.fillLog(r.in, r.o, lg);
  const bool f6 = lg.version == 11 && std::fabs(lg.ptorch_Pa - 2.0e5f) < 1.0f && lg.prail_mV == 7512 && lg.pintle_i_mA == 1234 && lg.tcb_dK == 270 &&
                  (lg.seq_flags & 0x01u) && (lg.seq_flags & 0x02u) && lg.ign_check_cs == 35 &&
                  crc16_ccitt(reinterpret_cast<const uint8_t*>(&lg), sizeof(LogRecord) - 2) == lg.crc16;
  r.in.prail_valid = false; r.in.pintle_i_valid = false; r.in.tc_bore_valid = false; r.in.ptorch_valid = false;
  LogRecord l2; r.e.fillLog(r.in, r.o, l2);
  const bool inval = l2.prail_mV == 0xFFFFu && l2.pintle_i_mA == INT16_MIN && l2.tcb_dK == INT16_MIN && std::isnan(l2.ptorch_Pa);
  check(f6 && inval, "v2.7 log fields (log v8): P_torch, rail mV, pintle mA, bore TC, seq_flags b0 torch ok / b1 bypass, window W 0.35 s (stand R1, v2.8.1); invalid markers",
        hex(lg.seq_flags, 2));
  PintleJamEvent ev; ev.kind = jam::STALL_TIME; ev.count = 1;
  const NvJamRecord j1 = nvJamRecordEvent(nvJamBlank(), ev, 1000u);
  const NvJamRecord l1 = nvLockoutSet(j1, 2000u);
  NvJamRecord d; const NvJamStatus s1 = nvJamDecode(reinterpret_cast<const uint8_t*>(&l1), &d);
  const NvJamRecord c1 = nvJamClear(l1); NvJamRecord d2; const NvJamStatus s2 = nvJamDecode(reinterpret_cast<const uint8_t*>(&c1), &d2);
  const NvJamRecord c2 = nvLockoutClear(c1); NvJamRecord d3; const NvJamStatus s3 = nvJamDecode(reinterpret_cast<const uint8_t*>(&c2), &d3);
  NvJamRecord bad = l1; reinterpret_cast<uint8_t*>(&bad)[12] ^= 0x04; NvJamRecord d4; const NvJamStatus s4 = nvJamDecode(reinterpret_cast<const uint8_t*>(&bad), &d4);
  check(s1 == NvJamStatus::VALID && nvLockoutPending(s1, d) && nvJamPending(s1, d) && d.kind == jam::STALL_TIME &&
            s2 == NvJamStatus::VALID && nvLockoutPending(s2, d2) && !nvJamPending(s2, d2) &&
            s3 == NvJamStatus::VALID && !nvLockoutPending(s3, d3) && s4 == NvJamStatus::CORRUPT && nvLockoutPending(s4, d4),
        "v2.7 NvJamRecord flags b1 relight lockout: set/clear independent of the jam flag; CORRUPT = lockout pending (fail-safe)");
}
{   // (11) lockout scope widened to any state after a lit burn; non-volatile lit-session marker (NvJamRecord b2): an ECU reset during
    //      or after a lit burn, before the normal DISARM in SAFE, boots with the lockout pending (the HAL reports b1 OR b2)
  Rig5 r; r.toIgnition(); const bool run1 = r.lightRun(); const bool coast = r.burnToCoast();
  r.in.prail_V = 0.3f; r.until(State::ABORT, 50);
  const bool coast_lock = r.e.abortCause() == Abort::PINTLE_FAULT && r.o.relight_lockout;
  Rig5 p; p.tick(Cmd::ARM); p.run(100); p.in.prail_V = 0.3f; p.until(State::ABORT, 50);
  const bool pad_free = p.e.abortCause() == Abort::PINTLE_FAULT && !p.o.relight_lockout;
  check(run1 && coast && coast_lock && pad_free,
        "v2.7 lockout scope: any abort after a lit burn locks out (here rail loss in COAST; the v2.7 draft covered IGNITION/RUN/SHUTDOWN only); a pad abort before any light does not");
  Rig5 m; m.toIgnition(); m.run(150); m.setPc(6.0e5f);
  int ev1 = 0, n = 0; while (m.e.state() != State::RUN && n < 100) { m.tick(); ++n; ev1 += m.o.lit_session_event; }
  const bool open1 = m.e.litSession();
  m.burnToCoast(); m.toRelight(); m.run(150); m.setPc(6.0e5f);
  int ev2 = 0; n = 0; while (m.e.state() != State::RUN && n < 100) { m.tick(); ++n; ev2 += m.o.lit_session_event; }
  const bool relit = m.e.state() == State::RUN;
  m.burnToCoast(); const bool open2 = m.e.litSession();
  m.tick(Cmd::DISARM); const bool close1 = m.e.state() == State::SAFE && m.o.lit_session_close && !m.e.litSession();
  m.tick(); const bool close_once = !m.o.lit_session_close;
  Rig5 a; a.toIgnition(); a.lightRun(); a.run(100); a.tick(Cmd::ABORT); a.until(State::SAFE, 3000);
  const bool kept = a.e.state() == State::SAFE && a.e.litSession() && a.o.relight_lockout;   // abort path: b2 kept (and b1 set)
  check(ev1 == 1 && open1 && relit && ev2 == 0 && open2 && close1 && close_once && kept,
        "v2.7 lit-session marker: one event at the first light (none at the relight); a commanded DISARM from COAST closes it (one-tick pulse for the NV write); an abort keeps it (lockout set)",
        fmt("events first start %.0f, relight %.0f", ev1, ev2));
  const NvJamRecord s1 = nvLitSessionSet(nvJamBlank());
  NvJamRecord d1; const NvJamStatus st1 = nvJamDecode(reinterpret_cast<const uint8_t*>(&s1), &d1);
  const NvJamRecord s2 = nvLitSessionClear(s1);
  NvJamRecord d2; const NvJamStatus st2 = nvJamDecode(reinterpret_cast<const uint8_t*>(&s2), &d2);
  const NvJamRecord s3 = nvLockoutClear(nvLockoutSet(s1, 5u));
  NvJamRecord d3; const NvJamStatus st3 = nvJamDecode(reinterpret_cast<const uint8_t*>(&s3), &d3);
  check(st1 == NvJamStatus::VALID && nvLockoutPending(st1, d1) && !nvJamPending(st1, d1) && st2 == NvJamStatus::VALID && !nvLockoutPending(st2, d2) &&
            st3 == NvJamStatus::VALID && !nvLockoutPending(st3, d3) && (d3.flags & 6u) == 0,
        "v2.7 NvJamRecord b2 lit-session marker: a boot with b2 set = lockout pending; the session close clears b2; keyed CLEAR_LOCKOUT clears b1 and b2");
}
{   // (12) P_torch robustness (calc/pc_transducer_v2.py: the 2.0 bar abs gate is 0.94 x the 070BG TEB above ambient): ARMED auto-zero,
    //      a reading must be seen below the threshold before it can confirm (stuck-high transducer), ARM sanity on the vented torch
  Rig5 s; s.ptorch_stuck_from_ignite = true; s.ptorch_stuck_Pa = 2.0e5f;   // stuck at the lit level from IGNITION entry; torch works
  s.toIgnition(); s.until(State::ABORT, 1000);
  const bool stuck = s.e.abortCause() == Abort::TORCH_FAULT;
  Rig5 o; o.torch_dead = true; o.ptorch_offset = 1.0e5f;            // +1.0 bar g zero offset (inside the TEB): 2.01 bar abs unzeroed
  o.toIgnition(); o.until(State::ABORT, 1000);
  const bool off_dead = o.e.abortCause() == Abort::TORCH_FAULT && std::fabs(o.e.ptorchZero() - 1.0e5f) < 1.0f;
  Rig5 g; g.ptorch_offset = 1.0e5f; g.toIgnition(); const bool off_lit = g.lightRun();
  check(stuck && off_dead && off_lit,
        "v2.7 P_torch: stuck at the lit level from IGNITION entry -> TORCH_FAULT (no below-threshold reading first); a +1.0 bar g offset is "
        "auto-zeroed in ARMED (dead torch -> TORCH_FAULT, working torch -> RUN)", fmt("zero %.0f Pa", o.e.ptorchZero()));
  Rig5 v; v.ptorch_bad = true; v.tick(Cmd::ARM); const bool inv_ref = v.e.state() == State::SAFE && v.e.abortCause() == Abort::TORCH_FAULT;
  Rig5 h; h.ptorch_offset = 1.2e5f; h.tick(Cmd::ARM); const bool off_ref = h.e.state() == State::SAFE && h.e.abortCause() == Abort::TORCH_FAULT;
  Rig5 k; k.ptorch_bad = true; k.in.load_cell_N = 0.0f; k.in.mode_strap = strap::STAND; k.tick(Cmd::SET_TORCH_GATE, cfg::kTorchTimingOnlyKey); k.tick(Cmd::ARM);
  const bool stand_ok = k.e.state() == State::ARMED;
  check(inv_ref && off_ref && stand_ok,
        "v2.7 ARM refused (TORCH_FAULT) with an invalid P_torch or a vented reading beyond the 1.05 bar TEB band; accepted on the stand with the timing-only key");
}
