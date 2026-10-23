// [v2.13 2026-10-21] Unit tests of the v2.13 core changes: REV-ELEC-4 E4-01 (MAJOR) light-window hold and TC4 step / rate checks (Q2 UT-1
// to UT-4 as specified, plus UT-5 bumpless resume), E4-03 (ARM check after an earlier ARM), E4-N01 (kPcSeatArmDevMax_K 40 K), E4-N02 (LEAD
// 264 (2) A1 pad rule, LEAD 264 (7) JFWD_LS relight inhibit) and the A5 SEAT_STEP relight option. Included from test_v29.inc after
// test_v212.inc (check, fmtv, loadNotch in scope). RigT follows the REV-ELEC-4 probe B rig (reviews/electronics/r4/scripts/probe_v212b.cpp
// 30df3496d533455e): the C1 thermal zero shift coef_true x (T_seat - T_cal) and any Pc sensor offset act on the Pc channel only; P_torch reads
// the TRUE chamber pressure. Additions: TC4 sample-and-hold every conv_ms (0 = a new reading every 1 ms tick, the SIL basis), a TC4 error
// schedule, the seat temperature as a function of time. LOGIC rig: TEST VALUES, not measurements or plant results.
  struct RigT {
    EngineEcu e; Inputs in; Commands c; Outputs o; LogRecord lr; double t = 0; float thrust = 300.f;
    bool follow = false, plant_lit = true; int torch_delay = 0, torch_n = 0;
    float p_true_g = 0.0f, T_seat = 293.15f, coef_true = 0.0f, T_cal = 293.15f, pc_offset = 0.0f, tc_err = 0.0f;
    float seat_rate = 0.0f;              // K/s: T_seat advances by seat_rate every tick (0 = static)
    int conv_ms = 0; double t_conv = -1.0; float tc_held = 293.15f;
    bool tc_ok = true;
    explicit RigT(bool stand = false) {
      e.init(0.0); e.ptank_cal_ok = true; loadNotch(e); e.hbleed_fitted = false;
      in.arm_plug_present = true; in.arm_bus_on = true; in.vbat_V = 8.2f; in.mv_closed_sw = true; in.ptank_Pa = 50e5f; in.pfeed_Pa = 48e5f;
      in.pintle_meas_valid = true; in.pintle_meas_m = 0.0f; in.tc_bore_valid = true;
      if (stand) { in.load_cell_N = 0.0f; in.mode_strap = strap::STAND; }
      apply();
    }
    void apply() {
      in.pc_Pa = p_true_g + coef_true * (T_seat - T_cal) + pc_offset;
      in.pc_raw_V = 0.5f + 4.f * in.pc_Pa / cfg::kPcXdcrFs_Pa;
      const float rd = T_seat + tc_err;
      if (conv_ms <= 0) in.tc_bore_K = rd;
      else if (t_conv < 0.0 || t - t_conv >= conv_ms * 1e-3 - 1e-9) { tc_held = rd; t_conv = t; in.tc_bore_K = rd; }
      else in.tc_bore_K = tc_held;
      in.tc_bore_valid = tc_ok;
    }
    void tick(Cmd cm = Cmd::NOP, uint16_t arg = 0) {
      t += 1e-3; in.t_s = t; c = Commands(); c.fast_valid = true; c.thrust_sp_N = thrust;
      if (cm != Cmd::NOP) { c.state_valid = true; c.cmd = cm; c.arg = arg; }
      if (follow && o.state == State::RUN && o.pc_sp_active_Pa > 0) p_true_g = o.pc_sp_active_Pa - 101325.f;
      T_seat += seat_rate * 1e-3f;
      apply();
      in.pintle_meas_m = o.pintle_cmd_m;
      if (o.servo_us[3] > 1800.f) { in.mv_open_sw = true; in.mv_closed_sw = false; }
      if (!o.mv_latch && o.servo_us[3] < 1600.f) { in.mv_open_sw = false; in.mv_closed_sw = true; }
      const bool both = o.sol[0] && o.sol[1];
      torch_n = both ? torch_n + 1 : 0;
      const bool torch_flame = both && torch_n > torch_delay;
      in.ptorch_valid = true; in.ptorch_Pa = torch_flame ? 2.0e5f : std::fmax(0.0f, p_true_g);
      in.photo_valid = true; in.photo_V = (torch_flame || (o.state == State::RUN && plant_lit)) ? 1.0f : 0.10f;
      in.pmid_valid = true; in.pmid_hi = false;
      in.mv_ladder_ratio = ladder::nominalRatio(in.mv_open_sw, in.mv_closed_sw, in.pmid_hi);
      e.step(in, c, o); e.fillLog(in, o, lr);
    }
    void run(int n) { for (int i = 0; i < n; ++i) tick(); }
    int until(State s, int nmax) { int n = 0; while (e.state() != s && n < nmax) { tick(); ++n; } return n; }
    int toIgnition() { tick(Cmd::ARM); run(600); tick(Cmd::IGNITE); return until(State::IGNITION, 4000); }
    int toE1(int nmax = 400) { int n = 0; while (e.liftCommandTime() < 0.0 && e.state() == State::IGNITION && n < nmax) { tick(); ++n; } return n; }
    bool lightRun(float pc_abs = 3.0e5f) { toE1(); run(30); p_true_g = pc_abs - 101325.f; until(State::RUN, 60); return e.state() == State::RUN; }
    bool burnToCoast(int run_ms = 800) {
      follow = true; run(run_ms); follow = false; tick(Cmd::SHUTDOWN); p_true_g = 0.0f;
      until(State::COAST, 3000); return e.state() == State::COAST;
    }
  };
  const float c1 = 0.0248e5f;   // Pa/K, C1 typical (k = 1)
  // Relight base (probe B Q2 set-up, made physical): ARM, lit first start, 0.8 s burn, coast with the seat rising at 2.0 K/s (A1, 14 K) or
  // 2.4 K/s (stand after B1, 54 K; physical maximum 2.42 K/s), then at the Mechanical relight-E1 diaphragm rate (A1 0.70, stand 1.40 K/s
  // [SIM, REV-ELEC-4 Q2]) through the relight. Returned in COAST just before the RELIGHT command.
  auto relightBase = [&](bool stand, float coef) {
    RigT r(stand); r.e.setPcSeatCoef(coef); r.coef_true = coef; r.T_seat = 293.15f;
    r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast();
    const float dT = stand ? 54.0f : 14.0f, rate = stand ? 2.4f : 2.0f;
    r.seat_rate = rate; while (r.T_seat < 293.15f + dT) r.tick();
    r.seat_rate = stand ? 1.40f : 0.70f; r.run(200);
    return r;
  };
  // First-start base: ARMED with the latch done (pad / stand first start, seat at T0), just before IGNITE
  auto firstBase = [&](bool stand, float coef) {
    RigT r(stand); r.e.setPcSeatCoef(coef); r.coef_true = coef; r.T_seat = 293.15f; r.tick(Cmd::ARM); r.run(600); return r;
  };
  struct StartRes { bool e2 = false; double t_e2 = -1, t_e1 = -1, t_ign = -1; std::string ab = "NONE"; bool run_end = false; bool step = false;
                    double comp_dev_max = 0.0; };
  // One start from a base: relight (RELIGHT in COAST) or first start (IGNITE in ARMED). Unlit: cold-flow ramp 0 until E1 + 30 ms, 0.42 bar
  // by E1 + 70 ms (SIL S13T unlit runs, reviewer data/e1_timing_unlit.json). Lit: the plant lights at E1 + 30 ms (3.0 bar abs) and follows
  // the setpoint from E2. TC4 error err_K from E1 + start_ms for dur_ms (< 0 = persistent), the E1 tick taken from the control run (e1_off).
  auto runStart = [&](const RigT& base, bool relight, bool lit, int e1_off, float err_K, int start_ms, int dur_ms, int n_after = 700) {
    RigT r = base; StartRes s; r.plant_lit = lit;
    r.tick(relight ? Cmd::RELIGHT : Cmd::IGNITE); r.until(State::IGNITION, 4000);
    s.t_ign = r.t; const float comp0 = r.o.pc_seat_comp_Pa;
    const double t_err0 = s.t_ign + e1_off * 1e-3 + start_ms * 1e-3, t_err1 = dur_ms < 0 ? 1e9 : t_err0 + dur_ms * 1e-3;
    int n = 0; double tE1 = -1;
    while (n < 3000) {
      const double te = tE1 >= 0 ? r.t + 1e-3 - tE1 : -1.0;
      if (tE1 >= 0 && !(lit && s.e2)) {
        if (lit) r.p_true_g = te < 0.030 ? 0.0f : 3.0e5f - 101325.f;
        else r.p_true_g = te < 0.030 ? 0.0f : (te < 0.070 ? 0.42e5f * (float)((te - 0.030) / 0.040) : 0.42e5f);
      }
      if (lit && s.e2) r.follow = true;
      const double tn = r.t + 1e-3;
      r.tc_err = (err_K != 0.0f && tn >= t_err0 - 1e-9 && tn < t_err1 - 1e-9) ? err_K : 0.0f;
      r.tick(); ++n;
      if (tE1 < 0 && r.e.liftCommandTime() >= 0.0) { tE1 = r.e.liftCommandTime(); s.t_e1 = tE1; }
      if (!s.e2 && r.e.state() == State::RUN) { s.e2 = true; s.t_e2 = r.t; }
      if (s.ab == "NONE" && r.e.abortCause() != Abort::NONE) s.ab = abortName(r.e.abortCause());
      const bool held_window = r.e.state() == State::IGNITION || (s.e2 && r.t < s.t_e2 + kPcSeatHoldPostE2_s - 1e-6);
      if (held_window) s.comp_dev_max = std::fmax(s.comp_dev_max, std::fabs(r.o.pc_seat_comp_Pa - comp0));
      if (tE1 >= 0 && r.t - tE1 >= n_after * 1e-3) break;
    }
    s.run_end = r.e.state() == State::RUN; s.step = r.e.pcSeatStep();
    return s;
  };
  // ===================================================================== UT-1 hold (Q2): unlit starts with the 0.42 bar cold-flow rise
  {
    const float mags[] = {-3, -5, -8, -15, -20, -55, 90, 140};
    const int starts[] = {-25, -10, 5, 100, 300, 600};
    const int durs[] = {100, 250, -1};
    int n_unlit = 0, n_false = 0, n_unlit_noig = 0, n_lit = 0, n_lit_same = 0, n_lit_run = 0; double dev_max = 0.0;
    std::string d, e1s;
    // torch delay 0: E1 = IGNITION entry + 3-4 ms in the rig, so the E1 - 25 / - 10 ms errors start BEFORE the entry (step check outside the
    // hold); 45 ms: E1 = entry + 48-49 ms as in the SIL (entry -> E1 45 / 51 ms [SIM]), so they start inside the hold before the P0 window
    for (int tdel : {0, 45})
    for (bool relight : {true, false})
      for (bool stand : {false, true})
        for (float k : {1.0f, 3.0f})
          for (float sg : {1.0f, -1.0f}) {
            const float coef = sg * k * c1;
            RigT base = relight ? relightBase(stand, coef) : firstBase(stand, coef); base.torch_delay = tdel;
            // controls: E1 offset from the IGNITION entry, the lit E2 tick, the unlit outcome (no error)
            const StartRes cu = runStart(base, relight, false, 0, 0.0f, 0, 0), cl = runStart(base, relight, true, 0, 0.0f, 0, 0);
            const int e1_off = (int)std::lround((cu.t_e1 - cu.t_ign) * 1e3);
            if (sg > 0 && k == 1.0f) e1s += fmtv("torch delay %d %s %s: E1 = entry + %d ms, lit E2 = E1 + %.0f ms; ", tdel, relight ? "relight" : "first",
                                                 stand ? "stand" : "flight", e1_off, (cl.t_e2 - cl.t_e1) * 1e3);
            if (cu.e2) { ++n_false; d += fmtv("CONTROL unlit E2 (%s %s k %.0f s %+.0f); ", relight ? "rl" : "fs", stand ? "st" : "fl", k, sg); }
            for (float X : mags)
              for (int st : starts)
                for (int du : durs) {
                  const StartRes u = runStart(base, relight, false, e1_off, X, st, du);
                  ++n_unlit; if (u.e2) { ++n_false; if (n_false < 12) d += fmtv("FALSE E2 %s %s k %.0f s %+.0f X %+.0f st %d du %d; ", relight ? "rl" : "fs",
                                                                                 stand ? "st" : "fl", k, sg, X, st, du); }
                  if (!u.e2 && u.ab == "NO_IGNITION") ++n_unlit_noig;
                  else if (!u.e2 && n_unlit - n_unlit_noig < 6) d += fmtv("unlit end %s (%s %s k %.0f X %+.0f st %d du %d); ", u.ab.c_str(), relight ? "rl" : "fs",
                                                                          stand ? "st" : "fl", k, X, st, du);
                  const StartRes l = runStart(base, relight, true, e1_off, X, st, du);
                  ++n_lit; if (l.e2 && std::fabs(l.t_e2 - cl.t_e2) < 1e-6) ++n_lit_same;
                  else if (n_lit - n_lit_same < 6) d += fmtv("lit E2 moved (%s %s k %.0f X %+.0f st %d du %d: %.4f vs %.4f); ", relight ? "rl" : "fs",
                                                             stand ? "st" : "fl", k, X, st, du, l.t_e2, cl.t_e2);
                  if (l.run_end && l.ab == "NONE") ++n_lit_run;
                  dev_max = std::fmax(dev_max, std::fmax(u.comp_dev_max, l.comp_dev_max));
                }
          }
    check(n_false == 0 && n_unlit_noig == n_unlit && n_lit_same == n_lit && n_lit_run == n_lit && dev_max <= 1.0,
          "v2.13 UT-1 (REV-ELEC-4 Q2) light-window hold: TC4 errors -3/-5/-8/-15/-20/-55/+90/+140 K from E1-25/-10/+5/+100/+300/+600 ms for "
          "100 ms / 250 ms / persistent, coef 0.0248e5 and 0.0744e5 Pa/K both signs, relight (probe B rig) and pad / stand first start, torch "
          "delay 0 and 45 ms: 0 E2 unlit (all NO_IGNITION); every lit control E2 at the same tick and RUN with no abort 0.7 s after E1; "
          "compensation constant in the hold",
          fmtv("unlit %d: false E2 %d, NO_IGNITION %d; lit %d: same E2 tick %d, RUN no abort %d; max comp change in the hold %.3f Pa; ",
               n_unlit, n_false, n_unlit_noig, n_lit, n_lit_same, n_lit_run, dev_max) + e1s + d);
  }
  // ===================================================================== UT-2 step and rate checks (Q2)
  {
    // (a) a 2 K one-conversion step inside the window (relight, A1 k 3, 100 ms = one conversion from E1 + 20 ms) and outside it (COAST), both
    //     signs, 1 kHz and 10 Hz conversions: the compensation holds (+/- 1 Pa) and SEAT_STEP latches
    int na = 0, na_ok = 0; std::string da;
    for (int conv : {0, 100})
      for (float X : {2.0f, -2.0f}) {
        // inside: relight base, the step from E1 + 20 ms
        RigT b = relightBase(false, 3.0f * c1); b.conv_ms = conv;
        const StartRes cu = runStart(b, true, false, 0, 0.0f, 0, 0); const int e1_off = (int)std::lround((cu.t_e1 - cu.t_ign) * 1e3);
        for (bool lit : {false, true}) {
          RigT r = b; r.plant_lit = lit; r.tick(Cmd::RELIGHT); r.until(State::IGNITION, 4000);
          const double t_ign = r.t; const float comp0 = r.o.pc_seat_comp_Pa; float dev = 0.0f; bool e2 = false; double tE1 = -1;
          for (int i = 0; i < 1500; ++i) {
            const double tn = r.t + 1e-3, te = tE1 >= 0 ? tn - tE1 : -1.0;
            if (tE1 >= 0 && !e2) r.p_true_g = lit ? (te < 0.030 ? 0.0f : 3.0e5f - 101325.f) : (te < 0.030 ? 0.0f : 0.42e5f * (float)std::fmin(1.0, (te - 0.030) / 0.040));
            if (e2) r.follow = true;
            r.tc_err = (tn >= t_ign + (e1_off + 20) * 1e-3 && tn < t_ign + (e1_off + 120) * 1e-3) ? X : 0.0f;
            r.tick();
            if (tE1 < 0 && r.e.liftCommandTime() >= 0.0) tE1 = r.e.liftCommandTime();
            if (r.e.state() == State::RUN) e2 = true;
            if (r.e.state() == State::SAFE || r.e.state() == State::ABORT) break;   // SAFE clears the compensation (E4-03)
            dev = std::fmax(dev, std::fabs(r.o.pc_seat_comp_Pa - comp0));
          }
          ++na; const bool ok = dev <= 1.0f && r.e.pcSeatStep() && (r.o.f3_flags & f3::SEAT_STEP) && (r.lr.f3_flags & f3::SEAT_STEP) && (lit == e2);
          if (ok) ++na_ok; else da += fmtv("inside conv %d X %+.0f lit %d: dev %.2f Pa step %d E2 %d; ", conv, X, (int)lit, dev, (int)r.e.pcSeatStep(), (int)e2);
        }
        // outside: COAST, seat ramping at 0.70 K/s, the step for one conversion
        RigT q = b; float comp0 = 0.0f, dev = 0.0f;
        for (int i = 0; i < 3000; ++i) {
          q.tc_err = (i >= 500 && i < 600) ? X : 0.0f;
          q.tick(); if (i == 499) comp0 = q.o.pc_seat_comp_Pa;
          if (i >= 499) dev = std::fmax(dev, std::fabs(q.o.pc_seat_comp_Pa - comp0));
        }
        ++na; const bool ok = dev <= 1.0f && q.e.pcSeatStep() && q.e.state() == State::COAST;
        if (ok) ++na_ok; else da += fmtv("outside conv %d X %+.0f: dev %.2f Pa step %d; ", conv, X, dev, (int)q.e.pcSeatStep());
      }
    // (b) a 14 K/s ramp error outside the hold (ARMED after the latch, seat static; and COAST with the seat at 0.70 K/s): SEAT_STEP within
    //     0.5 s, compensation moved <= 2 K x coef before the trip; 1 kHz and 10 Hz conversions
    int nb = 0, nb_ok = 0; std::string db;
    for (int conv : {0, 100})
      for (int where : {0, 1}) {
        RigT r = where == 0 ? firstBase(false, 3.0f * c1) : relightBase(false, 3.0f * c1); r.conv_ms = conv;
        r.run(150); const float comp0 = r.o.pc_seat_comp_Pa; double t_trip = -1; float dmove = 0.0f; const double t0 = r.t;
        for (int i = 0; i < 1000 && t_trip < 0; ++i) {
          r.tc_err = 14.0f * (float)(r.t + 1e-3 - t0); r.tick();
          if (r.e.pcSeatStep()) t_trip = r.t - t0; else dmove = std::fmax(dmove, std::fabs(r.o.pc_seat_comp_Pa - comp0));
        }
        float dhold = 0.0f; const float compt = r.o.pc_seat_comp_Pa;
        for (int i = 0; i < 500; ++i) { r.tc_err = 14.0f * (float)(r.t + 1e-3 - t0); r.tick(); dhold = std::fmax(dhold, std::fabs(r.o.pc_seat_comp_Pa - compt)); }
        // the true seat move over the same time (COAST 0.70 K/s) is allowed for in the bound: <= (2 K + rate x t_trip) x coef
        const float allow = (2.0f + (where == 1 ? 0.70f : 0.0f) * (float)std::fmax(0.0, t_trip)) * 3.0f * c1;
        ++nb; const bool ok = t_trip > 0 && t_trip <= 0.5 && dmove <= allow && dhold <= 1.0f;
        if (ok) ++nb_ok;
        db += fmtv("%s conv %d: trip %.3f s, comp moved %.4f bar (%.2f K), held after %.1f Pa; ", where == 0 ? "ARMED" : "COAST", conv, t_trip, dmove / 1e5,
                   dmove / (3.0f * c1), dhold);
      }
    // (c) a 2.42 K/s TRUE ramp for 60 s (ARMED after the latch, k 3): neither SEAT_STEP nor SEAT_FROZEN, compensation within 0.1 K of the
    //     reading (1 kHz, the SIL basis); 10 Hz conversions: settled within 0.1 K 50 ms after each conversion, peak lag reported
    int nc = 0, nc_ok = 0; std::string dc;
    for (int conv : {0, 100}) {
      RigT r = firstBase(false, 3.0f * c1); r.conv_ms = conv; r.seat_rate = 2.42f;
      float lag_max = 0.0f, lag_settled = 0.0f, err_true = 0.0f; bool any_step = false, any_frozen = false;
      for (int i = 0; i < 60000; ++i) {
        r.tick();
        const float lag = std::fabs(r.in.tc_bore_K - r.e.pcSeatTcompK());
        lag_max = std::fmax(lag_max, lag);
        if (conv > 0 && r.t - r.t_conv >= 0.050 - 1e-9) lag_settled = std::fmax(lag_settled, lag);
        err_true = std::fmax(err_true, std::fabs(r.T_seat - r.e.pcSeatTcompK()));
        any_step = any_step || r.e.pcSeatStep(); any_frozen = any_frozen || (r.o.f3_flags & f3::SEAT_FROZEN);
      }
      ++nc; const bool ok = !any_step && !any_frozen && (conv == 0 ? lag_max <= 0.1f : lag_settled <= 0.1f) && r.e.state() == State::ARMED;
      if (ok) ++nc_ok;
      dc += fmtv("conv %d ms: step %d frozen %d, |reading - T_c| max %.4f K (settled %.4f K), |true - T_c| max %.4f K, seat +%.1f K; ", conv, (int)any_step,
                 (int)any_frozen, lag_max, lag_settled, err_true, r.T_seat - 293.15f);
    }
    check(na_ok == na && nb_ok == nb && nc_ok == nc,
          "v2.13 UT-2 (REV-ELEC-4 Q2) TC4 step / rate checks: a 2 K one-conversion step inside or outside the light window holds the "
          "compensation (+/- 1 Pa) and sets SEAT_STEP (f3 b7, log v13); a 14 K/s ramp error sets SEAT_STEP within 0.5 s after moving the "
          "compensation <= 2 K x coef; a 2.42 K/s true ramp for 60 s sets neither and the compensation follows within 0.1 K",
          fmtv("(a) %d/%d ", na_ok, na) + da + fmtv("(b) %d/%d ", nb_ok, nb) + db + fmtv("(c) %d/%d ", nc_ok, nc) + dc);
  }
  // ===================================================================== UT-3 RUN (Q2): +90 K TC4 step in RUN at k = 3
  // pc_f_ against the no-error run over the 100 ms after the step (>= 5 time constants of the 50 Hz filter): the step itself must move it by
  // <= 0.02 bar. Over the following 0.6 s the held compensation (SEAT_STEP: held until the next ARM) no longer follows the TRUE seat drift
  // that the no-error run keeps compensating (relight base: 0.70 K/s) - that difference is the documented residual after a hold (coef x
  // rate x time since the freeze), reported and bounded, not a step effect
  {
    int n = 0, n_ok = 0; std::string d;
    for (bool relight : {false, true})
      for (float sg : {1.0f, -1.0f})
        for (int at_ms : {40, 200, 600}) {   // after E2: inside the hold (40, 200 ms; S13T +90 K at 22.30 s = E2 + 36 ms) and after it (600 ms)
          const float coef = sg * 3.0f * c1;
          const RigT base = relight ? relightBase(false, coef) : firstBase(false, coef);
          auto go = [&](bool err, double* t_e2_out, double* t_ign_out, std::vector<float>* pf, bool* ab, bool* stp) {
            RigT r = base; r.plant_lit = true; r.tick(relight ? Cmd::RELIGHT : Cmd::IGNITE); r.until(State::IGNITION, 4000);
            *t_ign_out = r.t; double tE1 = -1, tE2 = -1;
            for (int i = 0; i < 3000; ++i) {
              const double tn = r.t + 1e-3;
              if (tE1 >= 0 && tE2 < 0) r.p_true_g = (tn - tE1) < 0.030 ? 0.0f : 3.0e5f - 101325.f;
              if (tE2 >= 0) r.follow = true;
              r.tc_err = (err && tE2 >= 0 && tn >= tE2 + at_ms * 1e-3 - 1e-9) ? 90.0f : 0.0f;
              r.tick();
              if (tE1 < 0 && r.e.liftCommandTime() >= 0.0) tE1 = r.e.liftCommandTime();
              if (tE2 < 0 && r.e.state() == State::RUN) tE2 = r.t;
              if (tE2 >= 0 && r.t >= tE2 + at_ms * 1e-3 - 1e-9) pf->push_back(r.e.pcAbsFiltered());
              if (tE2 >= 0 && r.t > tE2 + at_ms * 1e-3 + 0.6) break;
            }
            *t_e2_out = tE2; *ab = r.e.abortCause() != Abort::NONE; *stp = r.e.pcSeatStep();
          };
          double te_c = 0, te_e = 0, ti_c = 0, ti_e = 0; std::vector<float> pc_c, pc_e; bool ab_c = false, ab_e = false, st_c = false, st_e = false;
          go(false, &te_c, &ti_c, &pc_c, &ab_c, &st_c); go(true, &te_e, &ti_e, &pc_e, &ab_e, &st_e);
          float d100 = 0.0f, d600 = 0.0f; const size_t m = std::min(pc_c.size(), pc_e.size());
          for (size_t i = 0; i < m; ++i) { const float x = std::fabs(pc_e[i] - pc_c[i]); d600 = std::fmax(d600, x); if (i <= 100) d100 = std::fmax(d100, x); }
          // residual bound: the seat drift the held compensation misses, from the freeze (IGNITION entry inside the hold, the step after it)
          const double t_freeze = at_ms * 1e-3 < kPcSeatHoldPostE2_s ? ti_e : te_e + at_ms * 1e-3;
          const double t_end = te_e + at_ms * 1e-3 + 0.6, rate = relight ? 0.70 : 0.0;
          const float resid = (float)(std::fabs(coef) * rate * (t_end - t_freeze)) + 0.002e5f;
          ++n; const bool ok = std::fabs(te_c - te_e) < 1e-6 && m > 500 && d100 <= 0.02e5f && d600 <= resid && !ab_e && !ab_c && st_e && !st_c;
          if (ok) ++n_ok;
          d += fmtv("%s s %+.0f at E2+%d ms: pc_f change %.5f bar in 0.1 s, %.4f bar in 0.6 s (residual bound %.4f), abort %d, SEAT_STEP %d; ",
                    relight ? "relight" : "first", sg, at_ms, d100 / 1e5, d600 / 1e5, resid / 1e5, (int)ab_e, (int)st_e);
        }
    check(n_ok == n, "v2.13 UT-3 (REV-ELEC-4 Q2): a +90 K TC4 step in RUN at k = 3 (inside the hold E2 + 40 / 200 ms and after it E2 + 600 ms, "
                     "first start and relight, both signs) moves pc_f_ by <= 0.02 bar against the no-error run (100 ms after the step), no abort, "
                     "SEAT_STEP set; the later difference is the held-compensation residual (coef x seat rate x time since the freeze)",
          fmtv("%d/%d; ", n_ok, n) + d);
  }
  // ===================================================================== UT-4 re-ARM (Q2; probe B Q1 cases on v2.13)
  {
    std::string d; int n_diff = 0, n = 0; float comp_safe_max = 0.0f;
    struct Q { float k, dT, pex; };
    const Q qs[] = {{1, 5, 0}, {1, 25, 0}, {3, 10, 0}, {3, 10, 0.6e5f}, {3, 20, 0}, {3, 20, 1.3e5f}, {3, 20, -1.3e5f}, {1, 25, 0.9e5f}};
    for (const Q& q : qs) {
      const float coef = q.k * c1;
      RigT f; f.e.setPcSeatCoef(coef); f.coef_true = coef; f.T_seat = 293.15f + q.dT; f.pc_offset = q.pex; f.run(300);
      f.tick(Cmd::ARM); f.run(5);
      const bool fresh_armed = f.e.state() == State::ARMED;
      RigT r; r.e.setPcSeatCoef(coef); r.coef_true = coef; r.T_seat = 293.15f; r.toIgnition(); r.lightRun(3.0e5f); r.burnToCoast();
      r.run(200); r.tick(Cmd::SAFE); r.run(5); r.tick(Cmd::DISARM); r.run(5);
      r.T_seat = 293.15f + q.dT; r.pc_offset = q.pex; r.run(300);
      const float comp_safe = r.o.pc_seat_comp_Pa; comp_safe_max = std::fmax(comp_safe_max, std::fabs(comp_safe));
      r.tick(Cmd::ARM); r.run(5);
      const bool re_armed = r.e.state() == State::ARMED;
      ++n; if (fresh_armed != re_armed) ++n_diff;
      d += fmtv("k %.0f dT %.0f off %+.1f: fresh %s re-ARM %s (comp in SAFE %.3f bar); ", q.k, q.dT, q.pex / 1e5, fresh_armed ? "ARMED" : abortName(f.e.abortCause()),
                re_armed ? "ARMED" : abortName(r.e.abortCause()), comp_safe / 1e5);
    }
    check(n_diff == 0 && comp_safe_max == 0.0f, "v2.13 UT-4 (REV-ELEC-4 Q2, E4-03): the 8 probe B Q1 re-ARM cases decide as a fresh ECU "
                                                "(SAFE clears the seat reference and compensation; the ARM check adds the applied compensation back)",
          fmtv("%d of %d differ; ", n_diff, n) + d);
  }
  // ===================================================================== UT-5 bumpless resume after the hold (lit relight, stand, k 3)
  {
    int n = 0, n_ok = 0; std::string d;
    for (bool stand : {false, true})
      for (float sg : {1.0f, -1.0f}) {
        const float coef = sg * 3.0f * c1;
        RigT r = relightBase(stand, coef); r.tick(Cmd::RELIGHT); r.until(State::IGNITION, 4000);
        double tE1 = -1, tE2 = -1; float dstep = 0.0f, prev = r.o.pc_seat_comp_Pa, gap_end = -1.0f; bool hold_prev = true;
        for (int i = 0; i < 2500; ++i) {
          const double tn = r.t + 1e-3;
          if (tE1 >= 0 && tE2 < 0) r.p_true_g = (tn - tE1) < 0.030 ? 0.0f : 3.0e5f - 101325.f;
          if (tE2 >= 0) r.follow = true;
          r.tick();
          if (tE1 < 0 && r.e.liftCommandTime() >= 0.0) tE1 = r.e.liftCommandTime();
          if (tE2 < 0 && r.e.state() == State::RUN) tE2 = r.t;
          if (hold_prev && !r.e.pcSeatHold() && tE2 >= 0) gap_end = std::fabs(r.in.tc_bore_K - r.e.pcSeatTcompK());
          hold_prev = r.e.pcSeatHold();
          dstep = std::fmax(dstep, std::fabs(r.o.pc_seat_comp_Pa - prev)); prev = r.o.pc_seat_comp_Pa;
        }
        const float lim = kPcSeatSlew_Kps * 1e-3f * std::fabs(coef) * 1.001f + 0.5f;   // + float rounding of T_c (ulp 3e-5 K at 300-350 K)
        ++n; const bool ok = tE2 > 0 && gap_end >= 0.0f && gap_end < kPcSeatRateTrip_K && !r.e.pcSeatStep() && dstep <= lim && r.e.state() == State::RUN &&
                             std::fabs(r.in.tc_bore_K - r.e.pcSeatTcompK()) < 0.01f;
        if (ok) ++n_ok;
        d += fmtv("%s s %+.0f: hold-end gap %.3f K (record %.3f K), max comp step %.2f Pa/tick (limit %.2f), caught up %d; ", stand ? "stand" : "A1", sg, gap_end,
                  r.e.pcSeatHoldGapMaxK(), dstep, lim, (int)(std::fabs(r.in.tc_bore_K - r.e.pcSeatTcompK()) < 0.01f));
      }
    check(n_ok == n, "v2.13 UT-5 bumpless resume: after E2 + 0.45 s the compensation temperature slews to the reading at <= 5 K/s "
                     "(comp step <= 5 K/s x coef per tick), the hold-end gap stays below the 3 K rate trip, no SEAT_STEP, RUN continues",
          fmtv("%d/%d; ", n_ok, n) + d);
  }
  // ===================================================================== E4-N01: kPcSeatArmDevMax_K 40 K
  {
    auto armAt = [&](float T0, float tcal, float off) {
      RigT r; r.e.setPcSeatCoef(3.0f * c1); r.e.setPcSeatTcal(tcal); r.coef_true = 3.0f * c1; r.T_cal = tcal; r.T_seat = T0; r.pc_offset = off;
      r.run(300); r.tick(Cmd::ARM); r.run(5);
      return r.e.state() == State::ARMED ? 1 : (r.e.abortCause() == Abort::PC_SENSOR ? 0 : -1);
    };
    const int a35 = armAt(273.15f, 308.15f, 0.0f), a35o = armAt(273.15f, 308.15f, 0.6e5f), a405 = armAt(267.65f, 308.15f, 0.0f);
    const int a40hot = armAt(313.15f, 283.15f, 0.0f);   // T0 40 C, T_cal 10 C: 30 K
    check(a35 == 1 && a35o == 0 && a405 == 0 && a40hot == 1 && kPcSeatArmDevMax_K == 40.0f,
          "v2.13 E4-N01: kPcSeatArmDevMax_K 40 K - T0 0 C with T_cal 35 C (35 K, k = 3, -2.60 bar thermal zero) ARMS (v2.12 30 K refused it: "
          "cold-day NO-GO); a +0.6 bar sensor offset there is still refused; 40.5 K drops the static term (refused, fail-safe); T0 40 C / T_cal 10 C arms",
          fmtv("35 K %d, 35 K + 0.6 bar %d, 40.5 K %d, 30 K hot %d (1 ARMED, 0 PC_SENSOR)", a35, a35o, a405, a40hot));
  }
  // ===================================================================== E4-N02 / LEAD 264 (2): A1 pad rule (seat_arm_rule)
  {
    auto armRule = [&](bool rule, bool stand, float coef, bool tc_ok, float T) {
      RigT r(stand); r.e.seat_arm_rule = rule; if (coef != 0.0f) r.e.setPcSeatCoef(coef); r.coef_true = coef; r.tc_ok = tc_ok; r.T_seat = T;
      r.run(300); r.tick(Cmd::ARM); r.run(5);
      return r.e.state() == State::ARMED ? std::string("ARMED") : std::string(abortName(r.e.abortCause()));
    };
    const std::string p0 = armRule(true, false, 0.0f, true, 293.15f), p1 = armRule(true, false, c1, false, 293.15f),
                      p2 = armRule(true, false, c1, true, 480.0f), p3 = armRule(true, false, c1, true, 293.15f),
                      p4 = armRule(true, true, 0.0f, true, 293.15f), p5 = armRule(false, false, 0.0f, true, 293.15f);
    // pad start: TC4 valid at the ARM command but invalid over the ARM window (no reference: SEAT_NOREF) -> IGNITE refused SEAT_TC;
    // a 2 K step after the latch (SEAT_STEP) -> refused SEAT_TC; normal -> accepted
    auto padStart = [&](int mode) {
      RigT r; r.e.seat_arm_rule = true; r.e.setPcSeatCoef(c1); r.coef_true = c1; r.run(300); r.tick(Cmd::ARM);
      if (mode == 1) r.tc_ok = false;
      r.run(600); r.tc_ok = true;
      if (mode == 2) { r.tc_err = 2.0f; r.run(100); r.tc_err = 0.0f; }
      r.run(20); r.tick(Cmd::IGNITE); const int refused = r.o.cmd_refused; r.run(5);
      return std::make_pair(refused, r.e.state());
    };
    const auto s0 = padStart(0), s1 = padStart(1), s2 = padStart(2);
    const bool ok = p0 == "SEAT_TC" && p1 == "SEAT_TC" && p2 == "SEAT_TC" && p3 == "ARMED" && p4 == "ARMED" && p5 == "ARMED" &&
                    s0.first == refuse::NONE && s0.second != State::ARMED && s1.first == refuse::SEAT_TC && s1.second == State::ARMED &&
                    s2.first == refuse::SEAT_TC && s2.second == State::ARMED && std::string(abortName(Abort::SEAT_TC)) == "SEAT_TC" && !kSeatArmRuleBuild;
    check(ok, "v2.13 LEAD 264 (2) A1 pad rule (EngineEcu::seat_arm_rule, A1 build value true): flight ARM refused SEAT_TC with coefficient 0, "
              "TC4 invalid or out of range; accepted with both; stand and rule-off builds unchanged; pad IGNITE refused SEAT_TC with no seat "
              "reference (SEAT_NOREF) or SEAT_STEP set",
          fmtv("ARM: coef 0 %s, TC invalid %s, 480 K %s, ok %s, stand %s, rule off %s; IGNITE: normal %d/%s, NOREF %d/%s, SEAT_STEP %d/%s", p0.c_str(),
               p1.c_str(), p2.c_str(), p3.c_str(), p4.c_str(), p5.c_str(), s0.first, stateName(s0.second), s1.first, stateName(s1.second), s2.first,
               stateName(s2.second)));
  }
  // ===================================================================== E4-N02 / LEAD 264 (7): JFWD_LS relight inhibit; A5 SEAT_STEP option
  {
    auto relightAfter = [&](bool stand, bool spike, bool inhibit_member, bool seat_step, bool step_inhibit) {
      RigT r(stand); r.e.jfwd_relight_inhibit = inhibit_member; r.e.seat_step_relight_inhibit = step_inhibit;
      if (seat_step) { r.e.setPcSeatCoef(c1); r.coef_true = c1; }
      r.toIgnition(); r.toE1(); r.run(5);
      if (spike) { r.p_true_g = 48.0e5f - 101325.f; r.tick(); r.p_true_g = 0.4e5f; r.run(3); }
      r.run(22); r.p_true_g = 3.0e5f - 101325.f; r.until(State::RUN, 60); r.burnToCoast();
      if (seat_step) { r.tc_err = 2.0f; r.run(100); r.tc_err = 0.0f; }
      r.run(1500);
      const int blk = r.o.relight_block; const bool jf = (r.o.f3_flags & f3::JFWD_LS) != 0;
      r.tick(Cmd::RELIGHT); const int refused = r.o.cmd_refused; r.run(3);
      return fmtv("%d/%d/%s/%d", refused, blk, stateName(r.e.state()), (int)jf);
    };
    const std::string j1 = relightAfter(false, true, true, false, false), j0 = relightAfter(false, false, true, false, false),
                      js = relightAfter(true, true, true, false, false), jo = relightAfter(false, true, false, false, false),
                      ss = relightAfter(false, false, true, true, true), sd = relightAfter(false, false, true, true, false);
    const std::string exp_j1 = fmtv("%d/%d/COAST/1", (int)refuse::JFWD_USED, (int)refuse::JFWD_USED), exp_ss = fmtv("%d/%d/COAST/0", (int)refuse::SEAT_STEP, (int)refuse::SEAT_STEP);
    const bool acc_j0 = j0.rfind("0/0/", 0) == 0 && j0.find("COAST") == std::string::npos, acc_js = js.rfind("0/0/", 0) == 0 && js.find("COAST") == std::string::npos;
    const bool acc_jo = jo.rfind("0/0/", 0) == 0 && jo.find("COAST") == std::string::npos, acc_sd = sd.rfind("0/0/", 0) == 0 && sd.find("COAST") == std::string::npos;
    check(j1 == exp_j1 && acc_j0 && acc_js && acc_jo && ss == exp_ss && acc_sd && kJfwdLsRelightInhibit && !kSeatStepRelightInhibit,
          "v2.13 LEAD 264 (7) PROVISIONAL: flight relight after a flagged first light (f3 JFWD_LS, LIGHT_SPIKE raw 48 bar abs) refused JFWD_USED "
          "(TLM relight_block too); no flag, stand, or the inhibit off -> accepted; A5 option: SEAT_STEP latched -> refused SEAT_STEP only with "
          "seat_step_relight_inhibit (build value false: the relight proceeds on the held compensation)",
          fmtv("refused/block/state/JFWD: spike %s, none %s, stand %s, inhibit off %s; SEAT_STEP inhibit %s, default %s", j1.c_str(), j0.c_str(),
               js.c_str(), jo.c_str(), ss.c_str(), sd.c_str()));
  }
  // ===================================================================== UT-6 catch-up after the hold (LEAD 16:11Z ITEM 2, accepted 16:27Z)
  // Pad first start, k = 1, torch delay 45 ms (E1 = entry + 48 ms), plant light at E1 + 0.30 s (hold about 0.81 s, so 5 K/s x hold > 3 K).
  // The TC4 READING ramps at r_hold K/s over the hold (seat static: a reading error; increments on the ticks after a hold tick, so g0 =
  // r_hold x the hold duration D measured by the ECU), then r_after K/s. mode 1: a 2 K one-conversion step 0.10 s after the hold end;
  // mode 2 (resume): a 14 K/s ramp from 0.80 s after the catch-up ended (gap closed): the NORMAL rate check must trip at 3 K (a catch-up
  // still active would trip at its growth limit, about 1.5 K).
  {
    struct CatchRes { double D = -1, t_end = -1, t_trip = -1, t_catch_end = -1; float g0 = -1, gap_trip = -1, gap_final = -1;
                      bool catch_seen = false, step = false, catch_at_end = false, step_at_end = false; };
    auto catchRun = [&](float r_hold, float r_after, int mode, int n_after_ms) {
      RigT r; r.e.setPcSeatCoef(c1); r.coef_true = c1; r.torch_delay = 45;
      r.tick(Cmd::ARM); r.run(600); r.tick(Cmd::IGNITE); r.until(State::IGNITION, 4000);
      CatchRes s; double tE1 = -1, tE2 = -1, t_h0 = -1, t_ramp2 = -1; bool hold_prev = false, ended = false;
      for (int i = 0; i < 8000; ++i) {
        const double tn = r.t + 1e-3;
        if (tE1 >= 0 && tE2 < 0) r.p_true_g = (tn - tE1) < 0.300 ? 0.0f : 3.0e5f - 101325.f;
        if (tE2 >= 0) r.follow = true;
        if (hold_prev) r.tc_err += r_hold * 1e-3f;
        else if (s.t_end >= 0) {
          r.tc_err += r_after * 1e-3f;
          if (mode == 1 && std::fabs(tn - (s.t_end + 0.100)) < 0.5e-3) r.tc_err += 2.0f;
          if (mode == 2 && t_ramp2 >= 0 && tn >= t_ramp2 - 1e-9) r.tc_err += 14.0f * 1e-3f;
        }
        r.tick();
        if (tE1 < 0 && r.e.liftCommandTime() >= 0.0) tE1 = r.e.liftCommandTime();
        if (tE2 < 0 && r.e.state() == State::RUN) tE2 = r.t;
        const bool h = r.e.pcSeatHold();
        if (h && !hold_prev && t_h0 < 0) t_h0 = r.t;
        if (!h && hold_prev && s.t_end < 0) {
          s.t_end = r.t; s.D = r.t - t_h0; s.g0 = r.e.pcSeatHoldGapMaxK(); s.catch_at_end = r.e.pcSeatCatch(); s.step_at_end = r.e.pcSeatStep();
        }
        hold_prev = h;
        if (r.e.pcSeatCatch()) s.catch_seen = true;
        if (s.catch_seen && !r.e.pcSeatCatch() && !ended && !r.e.pcSeatStep()) { ended = true; s.t_catch_end = r.t; if (mode == 2) t_ramp2 = r.t + 0.800; }
        if (r.e.pcSeatStep() && s.t_trip < 0) { s.t_trip = r.t; s.gap_trip = std::fabs(r.in.tc_bore_K - r.e.pcSeatTcompK()); }
        if (s.t_end >= 0 && r.t - s.t_end >= n_after_ms * 1e-3) break;
      }
      s.step = r.e.pcSeatStep(); s.gap_final = std::fabs(r.in.tc_bore_K - r.e.pcSeatTcompK());
      return s;
    };
    const float ru = 0.98f * kPcSeatSlew_Kps, ro = 1.02f * kPcSeatSlew_Kps;
    const CatchRes a = catchRun(ru, 0.0f, 0, 2000), b = catchRun(ro, 0.0f, 0, 100), c = catchRun(ru, 7.0f, 0, 1500),
                   dd = catchRun(ru, 5.05f, 0, 2600), e = catchRun(ru, 0.0f, 1, 400), f = catchRun(ru, 0.0f, 2, 3000);
    const bool ok_a = a.D > 0.61 && a.g0 > kPcSeatRateTrip_K && a.g0 <= kPcSeatSlew_Kps * (float)a.D && a.catch_at_end && !a.step && a.t_catch_end > 0 &&
                      a.gap_final < 0.01f;
    const bool ok_b = b.g0 > kPcSeatSlew_Kps * (float)b.D && b.step_at_end && std::fabs(b.t_trip - b.t_end) < 0.5e-3 && !b.catch_seen;
    const bool ok_c = c.catch_at_end && c.step && c.gap_trip > c.g0 + kPcSeatStepMax_K && c.gap_trip < c.g0 + kPcSeatStepMax_K + 0.01f &&
                      std::fabs((c.t_trip - c.t_end) - kPcSeatStepMax_K / 2.0f) < 0.01;
    const bool ok_d = dd.catch_at_end && dd.step && std::fabs(dd.t_trip - (dd.t_end + kPcSeatCatchCapX * dd.D)) <= 2.0e-3 &&
                      dd.gap_trip < dd.g0 + kPcSeatStepMax_K;
    const bool ok_e = e.catch_at_end && e.step && std::fabs(e.t_trip - (e.t_end + 0.100)) < 1.5e-3;
    const bool ok_f = f.catch_seen && f.t_catch_end > 0 && f.step && f.gap_trip > kPcSeatRateTrip_K && f.gap_trip < kPcSeatRateTrip_K + 0.02f &&
                      f.t_trip > f.t_catch_end + 0.8;
    check(ok_a && ok_b && ok_c && ok_d && ok_e && ok_f && kPcSeatCatchCapX == 2.0f,
          "v2.13 UT-6 (LEAD ITEM 2) catch-up after the hold: g0 just under 5 K/s x hold -> catch-up, no trip, resume, converged; just over -> "
          "SEAT_STEP at the hold-end tick; gap growth 1.5 K above the lowest gap -> trip; gap still above 3 K at 2 x hold after the hold end -> "
          "trip; the step check stays on in the catch-up; after the resume the NORMAL rate check trips at 3 K",
          fmtv("under: D %.3f s g0 %.3f K (bound %.3f) catch %d step %d caught up %.3f s after the end, final gap %.4f K; ", a.D, a.g0,
               kPcSeatSlew_Kps * a.D, (int)a.catch_at_end, (int)a.step, a.t_catch_end - a.t_end, a.gap_final) +
          fmtv("over: g0 %.3f K (bound %.3f) trip at the end %d (dt %.4f s) catch seen %d; ", b.g0, kPcSeatSlew_Kps * b.D, (int)b.step_at_end,
               b.t_trip - b.t_end, (int)b.catch_seen) +
          fmtv("growth 7 K/s: trip %.3f s after the end, gap %.3f K (limit g0 + 1.5 = %.3f); ", c.t_trip - c.t_end, c.gap_trip, c.g0 + kPcSeatStepMax_K) +
          fmtv("cap 5.05 K/s: trip %.4f s after the end (2 x D = %.4f), gap %.3f K; ", dd.t_trip - dd.t_end, kPcSeatCatchCapX * dd.D, dd.gap_trip) +
          fmtv("2 K step in the catch-up: trip %.4f s after the end; ", e.t_trip - e.t_end) +
          fmtv("resume: catch-up ended %.3f s after the end, 14 K/s ramp trip at gap %.3f K, %.3f s after the catch-up end", f.t_catch_end - f.t_end,
               f.gap_trip, f.t_trip - f.t_catch_end));
  }
  // ===================================================================== LEAD 16:11Z RULING 1 (b), 16:27Z option (2): EVENT BUILD 0x25 + log b7
  {
    int n = 0, n_ok = 0; std::string d;
    for (bool rule : {false, true})
      for (bool hb : {false, true}) {
        RigT r; r.e.seat_arm_rule = rule; r.e.hbleed_fitted = hb;
        r.tick();   // the first step = boot
        const uint8_t exp = static_cast<uint8_t>((rule ? evt::BUILD_SEAT_RULE : 0u) | (hb ? evt::BUILD_HBLEED : 0u));
        const bool boot_ev = r.o.build_event && r.o.build_bits == exp;
        const can::Frame fr = can::encodeEvent(evt::BUILD, r.o.state, 0u, r.o.build_bits);
        const bool frame_ok = fr.id == can::ID_EVENT && fr.len == 8 && fr.d[0] == 0x25 && fr.d[6] == exp && fr.d[7] == 0;
        const bool log_ok = ((r.o.ovr_flags & ovr::SEAT_RULE_BUILD) != 0) == rule && ((r.lr.ovr_flags & 0x80u) != 0) == rule &&
                            r.lr.version == 13 && sizeof(LogRecord) == 185;
        int quiet = 0; for (int i = 0; i < 50; ++i) { r.tick(); if (r.o.build_event) ++quiet; }
        r.tick(Cmd::ARM); const bool arm_ev = r.o.build_event && r.o.build_bits == exp;
        r.tick(); const bool after = !r.o.build_event;
        r.run(5); r.tick(Cmd::ARM); const bool arm2_ev = r.o.build_event;   // a second ARM command (state ARMED, or SAFE after a refusal)
        bool log_b7_all = true; for (int i = 0; i < 20; ++i) { r.tick(); log_b7_all &= ((r.lr.ovr_flags & 0x80u) != 0) == rule; }
        ++n; const bool ok = boot_ev && frame_ok && log_ok && quiet == 0 && arm_ev && after && arm2_ev && log_b7_all;
        if (ok) ++n_ok;
        d += fmtv("rule %d hbleed %d: boot %d bits 0x%02X frame %02X..%02X%02X log b7 %d quiet %d ARM %d next %d ARM2 %d (%s); ", (int)rule, (int)hb,
                  (int)boot_ev, exp, fr.d[0], fr.d[7], fr.d[6], (int)(log_ok && log_b7_all), quiet, (int)arm_ev, (int)after, (int)arm2_ev,
                  stateName(r.e.state()));
      }
    check(n_ok == n && evt::BUILD == 0x25 && evt::IGN_WINDOW == 0x15,
          "v2.13 LEAD RULING 1 (b) option (2): EVENT BUILD 0x25 (arg b0 seat_arm_rule, b1 hbleed_fitted) at boot and at every ARM command, "
          "for both values of each; log v13 ovr_flags b7 = seat_arm_rule (185 B unchanged)", fmtv("%d/%d; ", n_ok, n) + d);
  }
  // ===================================================================== SEAT_TC: ARM refusal emits no STATE event; STATE encoder guard
  {
    RigT r; r.e.seat_arm_rule = true; r.run(300);
    int ev = 0; r.tick(Cmd::ARM); if (r.o.state_event) ++ev;
    const bool refused = r.e.abortCause() == Abort::SEAT_TC && r.e.state() == State::SAFE; const int log_cause = r.lr.abort_cause;
    for (int i = 0; i < 20; ++i) { r.tick(); if (r.o.state_event) ++ev; }
    const uint32_t ov0 = can::g_state_cause_overflow;
    const can::Frame f1 = can::encodeStateEvent(State::SAFE, Abort::SEAT_TC, 1000u, 0);
    const uint32_t ov1 = can::g_state_cause_overflow;
    const can::Frame f2 = can::encodeStateEvent(State::SAFE, Abort::CASE_WARM_STAND, 1000u, 2);
    const uint32_t ov2 = can::g_state_cause_overflow;
    const int cf1 = f1.d[7] & 0x1F, cf2 = f2.d[7] & 0x1F, cp2 = f2.d[7] >> 5;
    check(refused && ev == 0 && log_cause == 32 && ov1 == ov0 + 1 && ov2 == ov1 && cf1 == 31 && cf2 == 31 && cp2 == 2,
          "v2.13 (LEAD 16:27Z) Abort::SEAT_TC (32) is ARM-refusal only: no STATE event on the refusal (state stays SAFE), log abort_cause 32; "
          "the STATE encoder never masks a cause above 31 into the 5-bit field (32 would read NONE): saturated to 31 and counted",
          fmtv("refused %d, STATE events %d, log cause %d, overflow +%u / +%u, cause field %d / %d, copy %d", (int)refused, ev, log_cause,
               ov1 - ov0, ov2 - ov1, cf1, cf2, cp2));
  }
