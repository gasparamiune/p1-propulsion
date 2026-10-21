// [v2.13 2026-10-21: v212-1 (a) / (c) seat rises as 4 K/s ramps instead of one-tick steps (the v2.13 TC4 step check); assertions unchanged]
// [v2.12 2026-10-21] Unit tests of the v2.12 core changes (REV-ELEC-3 R3-01 option (b) seat compensation, LEAD 2026-10-21T11:25Z working
// basis; the TB-state of the LC-TB70 v2 F4 abort set with the PC_SENSOR HIGH addition; purge FINAL 2.43 / 2.39 s as calibration constants,
// LEAD 256 (2) / 257 (2); the torch re-zero limit; the flight J-FWD indication; log v13). Included from test_v29.inc (Rig9, toCoast, check,
// fmt, fmtv in scope). Rig9 is a LOGIC rig: the pressures and temperatures below are TEST VALUES, not plant results.
  {   // (v212-1) seat compensation: coefficient 0.0248 bar/K (the C1 typical), seat TC 20 C at ARM; in COAST the seat reads +12.5 K and the
      //          raw Pc +0.31 bar in a vented chamber (pure thermal zero shift): compensated -> re-zero accepted with ~0 shift; coefficient 0
      //          (v2.11 fallback) -> the same block is rejected (> 0.30 bar); TC lost after ARM -> held; no TC at ARM -> OFF, flagged
    Rig9 a; const bool set_ok = a.e.setPcSeatCoef(0.0248e5f); a.in.tc_bore_valid = true; a.in.tc_bore_K = 293.15f;
    a.toIgnition();
    const bool comp_on = (a.o.f3_flags & f3::SEAT_COMP) && std::fabs(a.e.pcSeatRefK() - 293.15f) < 0.01f;
    a.lightRun(3.0e5f); a.burnToCoast();
    // v2.13: the 12.5 K seat rise is a 4 K/s ramp (3.125 s) with the thermal shift following it (v2.12: one-tick step, which v2.13 treats as a
    // TC4 fault by design - UT-2 in test_v213.inc); assertions unchanged
    for (int i = 1; i <= 3125; ++i) { const float T = 293.15f + 12.5f * (float)i / 3125.0f; a.in.tc_bore_K = T; a.setPcG(0.0248e5f * (T - 293.15f)); a.tick(); }
    a.in.tc_bore_K = 305.65f; a.setPcG(0.31e5f); a.run(1400);
    const bool a_acc = a.n_rz_ev == 1 && !a.o.rezero_rejected && std::fabs(a.o.rezero_shift_Pa) < 0.005e5f &&
                       std::fabs(a.o.pc_seat_comp_Pa - 0.31e5f) < 0.001e5f;
    const bool a_log = a.lr.seat_comp_hPa == 310 && a.lr.seat_ref_dK == 200 && (a.lr.f3_flags & f3::SEAT_COMP) && a.lr.version == 13 &&
                       crc16_ccitt(reinterpret_cast<const uint8_t*>(&a.lr), sizeof(LogRecord) - 2) == a.lr.crc16;
    const bool not_safe = !a.e.setPcSeatCoef(0.01e5f) && a.e.pcSeatCoef() == 0.0248e5f;
    a.tick(Cmd::RELIGHT); a.tick();
    const bool a_rl = a.e.state() != State::COAST && a.o.cmd_refused == refuse::NONE && !(a.o.fault2 & f2::NOT_VENTED);
    Rig9 b; b.in.tc_bore_valid = true; b.in.tc_bore_K = 293.15f; b.toIgnition(); b.lightRun(3.0e5f); b.burnToCoast();
    b.in.tc_bore_K = 305.65f; b.setPcG(0.31e5f); b.run(1400);
    const bool b_rej = b.n_rz_ev == 0 && b.o.rezero_rejected && !(b.o.f3_flags & f3::SEAT_COMP) && b.lr.seat_comp_hPa == INT16_MIN &&
                       !(b.o.f3_flags & f3::SEAT_NOREF);
    Rig9 c; c.e.setPcSeatCoef(0.0248e5f); c.in.tc_bore_valid = true; c.in.tc_bore_K = 293.15f; c.toIgnition(); c.lightRun(3.0e5f);
    c.burnToCoast();
    for (int i = 1; i <= 2500; ++i) { c.in.tc_bore_K = 293.15f + 10.0f * (float)i / 2500.0f; c.tick(); }   // v2.13: 4 K/s ramp (v2.12: one-tick step)
    c.in.tc_bore_K = 303.15f; c.run(5); c.in.tc_bore_valid = false; c.in.tc_bore_K = 400.0f; c.run(5);
    const bool c_hold = (c.o.f3_flags & f3::SEAT_FROZEN) && (c.o.f3_flags & f3::SEAT_COMP) && std::fabs(c.o.pc_seat_comp_Pa - 0.248e5f) < 0.001e5f;
    c.in.tc_bore_valid = true; c.in.tc_bore_K = 293.15f + 160.0f; c.run(2);   // implausible rise (> kPcSeatDevMax_K) -> held as well
    const bool c_imp = (c.o.f3_flags & f3::SEAT_FROZEN) && std::fabs(c.o.pc_seat_comp_Pa - 0.248e5f) < 0.001e5f;
    Rig9 d; d.e.setPcSeatCoef(0.0248e5f); d.in.tc_bore_valid = false; d.toIgnition(); d.in.tc_bore_valid = true; d.in.tc_bore_K = 310.0f; d.run(5);
    const bool d_off = (d.o.f3_flags & f3::SEAT_NOREF) && !(d.o.f3_flags & f3::SEAT_COMP) && d.o.pc_seat_comp_Pa == 0.0f;
    EngineEcu x; x.init(0.0);
    const bool cal = !x.setPcSeatCoef(1.1e4f) && !x.setPcSeatCoef(std::numeric_limits<float>::quiet_NaN()) && x.setPcSeatCoef(-0.05e5f) &&
                     x.pcSeatCoef() == -0.05e5f && x.setPcSeatCoef(0.0f);
    check(set_ok && comp_on && a_acc && a_log && not_safe && a_rl && b_rej && c_hold && c_imp && d_off && cal,
          "v2.12 R3-01 option (b): seat compensation 0.0248 bar/K x 12.5 K removes a 0.31 bar thermal shift (re-zero accepted, ~0 shift, vented); "
          "coefficient 0 = v2.11 fallback (rejected, flag clear); TC lost or implausible after ARM -> held (SEAT_FROZEN); no TC at ARM -> OFF "
          "(SEAT_NOREF); coefficient SAFE-only and bounded; log v13 seat_comp_hPa / seat_ref_dK / f3_flags",
          fmtv("comp %.3f bar, re-zero shift %.4f bar (comp) / rejected %d (no comp), held %.3f bar, log comp %d hPa ref %d dK",
               a.o.pc_seat_comp_Pa / 1e5, a.o.rezero_shift_Pa / 1e5, (int)b.o.rezero_rejected, c.o.pc_seat_comp_Pa / 1e5,
               (int)a.lr.seat_comp_hPa, (int)a.lr.seat_ref_dK));
  }
  {   // (v212-2) TB-state (LC-TB70 v2 F4 set, Mechanical: + PC_SENSOR HIGH): stand RUN, a HIGH over-range (>= 4.75 V) for the 5 ms
      //          persistence -> PC_SENSOR abort with TB_STATE and TB_PCS_HIGH; the LOW side (open wire) -> PC_SENSOR abort, NOT a TB-state;
      //          flight RUN: one HIGH tick -> TB_STATE latched (information, no abort); a case OVER_TEMP abort -> TB_STATE
    Rig9 s(false, true); s.toIgnition(); s.lightRun(3.0e5f); s.follow = true; s.run(300); s.follow = false;
    int ns = 0; while (s.e.state() == State::RUN && ns < 50) { s.in.pc_raw_V = 4.80f; s.tick(); ++ns; }
    const bool s_hi = s.e.abortCause() == Abort::PC_SENSOR && (s.o.f3_flags & f3::TB_STATE) && (s.o.f3_flags & f3::TB_PCS_HIGH) &&
                      (s.lr.f3_flags & f3::TB_STATE) && s.e.tbState();
    Rig9 l(false, true); l.toIgnition(); l.lightRun(3.0e5f); l.follow = true; l.run(300); l.follow = false;
    int nl = 0; while (l.e.state() == State::RUN && nl < 50) { l.in.pc_raw_V = 0.10f; l.tick(); ++nl; }
    const bool l_lo = l.e.abortCause() == Abort::PC_SENSOR && !(l.o.f3_flags & f3::TB_STATE);
    Rig9 f; f.toIgnition(); f.lightRun(3.0e5f); f.follow = true; f.run(300); f.follow = false;
    const bool f_pre = !(f.o.f3_flags & f3::TB_STATE);
    f.in.pc_raw_V = 4.80f; f.tick(); f.follow = true; f.run(50);
    const bool f_hi = f.e.state() == State::RUN && (f.o.f3_flags & f3::TB_STATE) && (f.o.f3_flags & f3::TB_PCS_HIGH);
    Rig9 o(false, true); o.toIgnition(); o.lightRun(3.0e5f); o.follow = true; o.in.tc_valid[0] = true; o.in.tc_K[0] = 430.0f;
    int no = 0; while (o.e.state() == State::RUN && no < 600) { o.tick(); ++no; }
    const bool o_ot = o.e.abortCause() == Abort::OVER_TEMP && (o.o.f3_flags & f3::TB_STATE) && !(o.o.f3_flags & f3::TB_PCS_HIGH);
    check(s_hi && l_lo && f_pre && f_hi && o_ot,
          "v2.12 TB-state: stand HIGH over-range -> PC_SENSOR abort + TB_STATE + TB_PCS_HIGH (log v13 f3 b0/b1); LOW side -> PC_SENSOR abort "
          "without TB_STATE; flight HIGH tick -> TB_STATE latched, burn continues; case OVER_TEMP abort -> TB_STATE",
          fmtv("stand HIGH abort after %d ms, LOW abort after %d ms, OVER_TEMP abort after %d ms", ns, nl, no));
  }
  {   // (v212-3) purge FINAL as calibration constants (LEAD 256 (2), 257 (2), 258 (2)): defaults 2.43 / 2.39 s, flow start 0.42 s after
      //          PURGE; a rule-(d) re-set is accepted in SAFE within the bounds only; a 2.0 / 2.0 s re-set flows 2.0 s, ends E0 - 0.05 s
    EngineEcu x; x.init(0.0);
    const bool d0 = x.purgeFlow_s() == kPurgeFlow_s && x.hbleedCap_s() == kHbleedCap_s && std::fabs(x.purgeFlowStart_s() - 0.42f) < 1e-5f &&
                    std::fabs(kPurgeFlowStart_s - 0.42f) < 1e-5f;
    const bool rj = !x.setPurgeCal(2.44f, 2.39f) && !x.setPurgeCal(2.43f, 2.40f) && !x.setPurgeCal(2.38f, 2.33f) &&
                    !x.setPurgeCal(0.9f, 2.0f) && !x.setPurgeCal(std::numeric_limits<float>::quiet_NaN(), 2.0f) && x.purgeFlow_s() == kPurgeFlow_s;
    const bool ok = x.setPurgeCal(2.0f, 2.0f) && x.purgeFlow_s() == 2.0f && x.hbleedCap_s() == 2.0f;
    Rig9 r(true); const bool rs = r.e.setPurgeCal(2.0f, 2.0f); toCoast(r); r.run(500);
    const bool coast_rej = !r.e.setPurgeCal(2.43f, 2.39f);
    r.tick(Cmd::PURGE); const double t0 = r.t;
    int both = 0; double t_v2 = -1.0;
    while (r.t - t0 < kPurgeRelight_s - 0.0005) {
      r.tick();
      if (r.o.hbleed[1] && t_v2 < 0.0) t_v2 = r.t - t0;
      if (r.o.hbleed[0] && r.o.hbleed[1]) ++both;
    }
    const bool flow = rs && coast_rej && r.o.purge_flow_ms == 2000 && std::abs(both - 1950) <= 1 && r.n_ev[hb::EV_CAP] == 0 &&
                      std::fabs(t_v2 - (kPurgeRelight_s - kPurgeFlowEndLead_s - 2.0 - kHbleedOpenTime_s)) < 0.0025;
    check(d0 && rj && ok && flow,
          "v2.12 purge FINAL: defaults 2.43 s flow / 2.39 s cap (flow start PURGE + 0.42 s); re-set accepted in SAFE only, never above "
          "2.43 / 2.39 s, span + 2 ticks inside the cap; a 2.0 / 2.0 s re-set flows 2.0 s (V2 at PURGE + 0.82 s), EV_CAP 0",
          fmtv("re-set flow %u ms, both-open %d ms, V2 open at PURGE + %.3f s", (unsigned)r.o.purge_flow_ms, both, t_v2));
  }
  {   // (v212-4) torch re-zero on its own 070BG limit (0.60 bar, R3-01 item 7): +0.45 bar on both channels in COAST -> the Pc block is
      //          rejected (> 0.30 bar) and the torch block accepted; +0.65 bar -> the torch block rejected (PT_RZ_REJ), the torch ARM zero kept
    Rig9 a; a.toIgnition(); a.lightRun(3.0e5f); a.burnToCoast(); const float tz0 = a.e.ptorchZero(); a.setPcG(0.45e5f); a.run(1400);
    const bool a_ok = a.o.rezero_rejected && std::fabs(a.e.ptorchZero() - 0.45e5f) < 0.005e5f && !(a.o.f3_flags & f3::PT_RZ_REJ);
    Rig9 b; b.toIgnition(); b.lightRun(3.0e5f); b.burnToCoast(); const float tz1 = b.e.ptorchZero(); b.setPcG(0.65e5f); b.run(1400);
    const bool b_rej = b.o.rezero_rejected && std::fabs(b.e.ptorchZero() - tz1) < 1.0f && (b.o.f3_flags & f3::PT_RZ_REJ);
    check(a_ok && b_rej && std::fabs(kPtorchRezeroMax_Pa - 0.60e5f) < 1.0f,
          "v2.12 torch re-zero limit 0.60 bar (070BG basis): 0.45 bar accepted on the torch while the Pc block (0.30 bar limit) is rejected; "
          "0.65 bar rejected (f3 PT_RZ_REJ)",
          fmtv("torch zero %.3f -> %.3f bar (accepted); %.3f bar kept (rejected)", tz0 / 1e5, a.e.ptorchZero() / 1e5, b.e.ptorchZero() / 1e5));
  }
  {   // (v212-6) ARM sanity static term (R3-01, SIL S13T pre-fix finding): soak 0 C (20 K below T_cal 20 C), coefficient 3 x 0.0248 bar/K,
      //          the uncompensated vented reading -1.488 bar (pure thermal zero shift): option (b) -> ARM accepted (gauge - coef x (T - T_cal)
      //          = 0); coefficient 0 -> refused PC_SENSOR (v2.11 check); TC invalid -> no static term -> refused; T_cal SAFE-only and bounded
    auto armAt = [](float coef, bool tc_ok, float tcal) {
      Rig9 r; if (coef != 0.0f) r.e.setPcSeatCoef(coef); if (tcal > 0.0f) r.e.setPcSeatTcal(tcal);
      r.in.tc_bore_valid = tc_ok; r.in.tc_bore_K = 273.15f; r.setPcG(-1.488e5f); r.run(200); r.tick(Cmd::ARM); r.run(5);
      return r.e.state() == State::ARMED ? 1 : (r.e.abortCause() == Abort::PC_SENSOR || r.o.cmd_refused != 0 ? 0 : -1);
    };
    const int a_on = armAt(3.0f * 0.0248e5f, true, 0.0f), a_off = armAt(0.0f, true, 0.0f), a_notc = armAt(3.0f * 0.0248e5f, false, 0.0f);
    const int a_tcal = armAt(3.0f * 0.0248e5f, true, 303.15f);   // T_cal 30 C: 30 K -> -2.23 bar static term, 0.74 bar residual -> refused
    EngineEcu x; x.init(0.0);
    const bool tc = !x.setPcSeatTcal(280.0f) && !x.setPcSeatTcal(310.0f) && !x.setPcSeatTcal(std::numeric_limits<float>::quiet_NaN()) &&
                    x.setPcSeatTcal(296.15f) && x.pcSeatTcal() == 296.15f && kPcSeatTcalDefault_K == 293.15f;
    check(a_on == 1 && a_off == 0 && a_notc == 0 && a_tcal == 0 && tc,
          "v2.12 ARM sanity static term: 0 C soak, 3 x 0.0248 bar/K, -1.488 bar uncompensated zero -> ARM accepted with option (b) "
          "(gauge - coef x (T_seat - T_cal)); coefficient 0 or TC invalid -> refused (v2.11 check); wrong T_cal -> refused; T_cal SAFE-only, 10-35 C",
          fmtv("ARM on %d / off %d / no TC %d / T_cal 30 C %d (1 = ARMED, 0 = refused)", a_on, a_off, a_notc, a_tcal));
  }
  {   // (v212-5) flight J-FWD indication: in the LIGHT_SPIKE window one raw sample at 48.0 bar abs sets f3::JFWD_LS; 47.0 bar abs does not
    Rig9 j; j.toIgnition(); j.toE1(); j.run(5); j.setPcAbs(48.0e5f); j.tick(); j.setPcAbs(1.5e5f); j.run(3);
    Rig9 k; k.toIgnition(); k.toE1(); k.run(5); k.setPcAbs(47.0e5f); k.tick(); k.setPcAbs(1.5e5f); k.run(3);
    check((j.o.f3_flags & f3::JFWD_LS) && !(k.o.f3_flags & f3::JFWD_LS) && (j.lr.f3_flags & f3::JFWD_LS) &&
              std::fabs(kJfwdLsRawAbs_Pa - 47.5e5f) < 1.0f,
          "v2.12 J-FWD indication: LIGHT_SPIKE raw >= 47.5 bar abs (C1 chain on the FA-1 grid, 0 / 298 misses) sets f3 JFWD_LS; 47.0 does not",
          fmtv("48.0 -> 0x%02x, 47.0 -> 0x%02x", (unsigned)j.o.f3_flags, (unsigned)k.o.f3_flags));
  }
