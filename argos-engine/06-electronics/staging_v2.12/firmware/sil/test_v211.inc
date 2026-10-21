// v2.11 unit tests (2026-10-13; LEAD CHANGELOG 203 (1)(a) ADOPTED non-sticky over-range + above-FS flag, 203 (1)(b) CANDIDATE FA-1
// ride-through (2026-10-20: LEAD 216 (3) fixed comparator RC, over-range N >= 2), 203 (3) both-open cap 2.55 s, 205 C1 absolute transducer scaling). Included at the end of the test_v29.inc block after
// test_v210.inc (Rig9, toCoast, check, fmt, fmtv in scope). Rig9 is a LOGIC rig: the Pc histories below are TEST VALUES shaped like the
// FA-1 episodes (Combustion SIM construct, ASSUMED), not measurements; the physical consequences (peak Pc, time above 45 bar) come from
// the SIL plant cases S6R/S9R in sil_main, not from these tests.
{
  // Pc history relative to the ignition-lift tick of the start under test (k = 0 is the first tick after toE1 returns)
  struct RideObs {
    int abort_k = -1, e2_k = -1, win_n = 0, win_last = -1, tol_n = 0, bit4_n = 0, t45_n = 0, build_n = 0, ticks = 0;
    Abort cause = Abort::NONE; bool t45_at_abort = false;
  };
  auto play = [](Rig9& r, int nmax, const std::function<float(int, int)>& pc_abs_of_k) {   // (k, e2_k) -> Pa abs; < 0 = follow
    RideObs ob;
    for (int k = 0; k < nmax; ++k) {
      const float p = pc_abs_of_k(k, ob.e2_k);
      if (p >= 0.0f) { r.follow = false; r.setPcAbs(p); } else r.follow = true;
      r.tick(); ++ob.ticks;
      if (ob.e2_k < 0 && r.e.state() == State::RUN) ob.e2_k = k;
      const uint8_t f = r.o.ovr_flags;
      if (f & ovr::RIDE_WIN) { ++ob.win_n; ob.win_last = k; }
      if (f & ovr::RIDE_TOL) ++ob.tol_n;
      if (f & ovr::LONG_RC_RETIRED) ++ob.bit4_n;   // retired 2026-10-20 (LEAD 216 (3)): must stay 0
      if (f & ovr::T45) ++ob.t45_n;
      if (f & ovr::RIDE_BUILD) ++ob.build_n;
      if (r.e.abortCause() != Abort::NONE) { ob.abort_k = k; ob.cause = r.e.abortCause(); ob.t45_at_abort = (f & ovr::T45) != 0; break; }
    }
    r.follow = false;
    return ob;
  };
  // flight relight on a rig WITHOUT the bleed fitted (v2.10 direct path, rule FLIGHT_RELIGHT); stand variant on request
  auto relightToE1 = [&](Rig9& r) {
    if (!toCoast(r)) return false;
    r.run(600); r.tick(Cmd::RELIGHT);
    if (r.e.state() != State::IGNITION) return false;
    r.toE1(); return r.e.state() == State::IGNITION && r.e.liftCommandTime() >= 0.0;
  };
  const float kAmb = 101325.f;
  auto fa1Like = [kAmb](int k, int) { return k < 30 ? kAmb : (k < 44 ? 35.0e5f : -1.0f); };          // 35 bar abs for 14 ms, then healthy
  auto t45Like = [kAmb](int k, int) { return k < 30 ? kAmb : (k < 40 ? 50.0e5f : -1.0f); };          // 50 bar abs for 10 ms (> MEOP)
  auto sustained = [kAmb](int k, int) { return k < 30 ? kAmb : 35.0e5f; };                           // genuine over-pressure, no end
  auto lateEp = [kAmb](int k, int e2) { return k < 30 ? kAmb : ((e2 < 0 || k < e2 + 1) ? 3.0e5f : 40.0e5f); };   // 40 bar abs from E2 + 1 ms

  {   // (v211-1) LEAD 203 (1)(a): above-full-scale flag. One 1 kHz sample at 4.60 V (>= 4.56 V = 139.96 bar abs on C1, < 4.75 V) after E1
      //          of a flight pad start: ovr ABOVE_FS on that tick only (not OVERRANGE, PC_VALID stays 1), LIGHT_SPIKE abovefs, log v12 ls_flags
      //          b7 and ovr_flags; no action (light at 3 bar -> RUN). Control start without the sample: flag and b7 clear
    Rig9 r; r.toIgnition(); r.toE1(); r.run(20);
    r.in.pc_raw_V = 4.60f; r.in.pc_Pa = (4.60f - 0.5f) / 4.0f * cfg::kPcXdcrFs_Pa; r.tick();
    const bool tick_ok = (r.o.ovr_flags & ovr::ABOVE_FS) && !(r.o.ovr_flags & ovr::OVERRANGE) && r.o.pc_above_fs && !r.o.pc_overrange &&
                         r.o.pc_valid && (r.lr.ovr_flags & ovr::ABOVE_FS) && r.e.abortCause() == Abort::NONE;
    r.setPcAbs(kAmb); r.tick();
    const bool next_clear = !(r.o.ovr_flags & (ovr::ABOVE_FS | ovr::OVERRANGE)) && r.o.pc_valid;
    r.run(10); r.setPcAbs(3.0e5f); r.until(State::RUN, 60);
    const bool run = r.e.state() == State::RUN;
    r.follow = true; r.run(500); r.follow = false;
    const LightSpikeRec& L = r.o.light_spike;
    const bool rec_ok = L.done && L.abovefs && !L.overrange && (r.lr.ls_flags & 128u) && r.e.abortCause() == Abort::NONE;
    Rig9 q; q.toIgnition(); q.lightRun(3.0e5f); q.follow = true; q.run(500); q.follow = false;
    const bool ctrl_ok = q.o.light_spike.done && !q.o.light_spike.abovefs && !(q.lr.ls_flags & 128u) && q.lr.version == kLogVersion;
    check(tick_ok && next_clear && run && rec_ok && ctrl_ok && kLogVersion == 13 && sizeof(LogRecord) == 185,
          "v2.11 LEAD 203 (1)(a) above-FS flag: one sample >= 4.56 V after E1 -> ovr ABOVE_FS on that tick only (PC_VALID 1, not OVERRANGE), "
          "LIGHT_SPIKE abovefs + log v12 ls_flags b7 + ovr_flags; no action (RUN); control start: flag and b7 clear",
          fmtv("tick %d next %d run %d record %d control %d (ls_flags 0x%02X / 0x%02X)", (int)tick_ok, (int)next_clear, (int)run, (int)rec_ok,
               (int)ctrl_ok, (unsigned)r.lr.ls_flags, (unsigned)q.lr.ls_flags));
  }
  {   // (v211-2) LEAD 203 (1)(a): non-sticky HIGH over-range in FLIGHT RUN (after the settle): PC_VALID 0 only on the over-range tick
      //          (OPEN_LOOP that tick), no PC_SENSOR latch, pc_commit_valid back on the next tick, RUN kept. Stand as built: PC_SENSOR latched,
      //          pc_commit_valid stays 0. Flight LOW (0.05 V) still latches PC_SENSOR (a sensor fault, not pressure)
    auto hi = [](Rig9& r) { r.in.pc_raw_V = 4.90f; r.in.pc_Pa = 76.0e5f; };
    Rig9 r; r.toIgnition(); r.lightRun(3.0e5f); r.follow = true; r.run(400); r.follow = false;
    const float pc_run = r.in.pc_Pa;
    hi(r); r.tick();
    const bool f_on = !r.o.pc_valid && r.o.pc_overrange && (r.o.ovr_flags & ovr::OVERRANGE) && (r.o.fault_bits & fault::OPEN_LOOP) &&
                      !(r.o.fault_bits & fault::PC_SENSOR) && !r.o.pc_commit_valid;
    r.in.pc_Pa = pc_run; r.in.pc_raw_V = 0.5f + 4.f * pc_run / cfg::kPcXdcrFs_Pa; r.tick();
    const bool f_off = r.o.pc_valid && !r.o.pc_overrange && !(r.o.fault_bits & (fault::OPEN_LOOP | fault::PC_SENSOR)) && r.o.pc_commit_valid;
    r.follow = true; r.run(100); r.follow = false;
    const bool f_run = r.e.state() == State::RUN && r.e.abortCause() == Abort::NONE && !(r.o.fault_bits & fault::PC_SENSOR);
    Rig9 s(false, true); s.toIgnition(); s.lightRun(3.0e5f); s.follow = true; s.run(400); s.follow = false;
    const float pc_s = s.in.pc_Pa;
    hi(s); s.tick(); s.in.pc_Pa = pc_s; s.in.pc_raw_V = 0.5f + 4.f * pc_s / cfg::kPcXdcrFs_Pa; s.tick();
    const bool s_ok = (s.o.fault_bits & fault::PC_SENSOR) && !s.o.pc_commit_valid && s.o.pc_valid;
    Rig9 l; l.toIgnition(); l.lightRun(3.0e5f); l.follow = true; l.run(400); l.follow = false;
    const float pc_l = l.in.pc_Pa;
    l.in.pc_raw_V = 0.05f; l.in.pc_Pa = -5.0e5f; l.tick(); l.in.pc_Pa = pc_l; l.in.pc_raw_V = 0.5f + 4.f * pc_l / cfg::kPcXdcrFs_Pa; l.tick();
    const bool l_ok = (l.o.fault_bits & fault::PC_SENSOR) && !l.o.pc_commit_valid;
    check(f_on && f_off && f_run && s_ok && l_ok,
          "v2.11 LEAD 203 (1)(a) non-sticky over-range: flight RUN 4.90 V for one sample -> PC_VALID 0 / OPEN_LOOP / over-range bit on that "
          "tick only, no PC_SENSOR latch, commit bit back, RUN kept; stand as built (PC_SENSOR latched); flight LOW still latches",
          fmtv("flight on %d off %d run %d; stand %d; low %d", (int)f_on, (int)f_off, (int)f_run, (int)s_ok, (int)l_ok));
  }
  {   // (v211-3) LEAD 203 (1)(b) CANDIDATE ride-through, flight relight (no bleed fitted: v2.10 direct path, rule FLIGHT_RELIGHT), same
      //          Pc histories with ride_through off (as built) and on. FA-1-like 35 bar abs for 14 ms: as built HARD_START, ride tolerated
      //          (RIDE_TOL seen, window closes at E2 + 15 ms, RUN; the retired long-RC bit never set). 50 bar abs for 10 ms: ride HARD_START by
      //          the T45 guard (7 ms). Sustained 35 bar: both abort HARD_START, ride 10 ms later (15 ms vs 5 ms persistence). 40 bar abs from
      //          E2 + 1 ms: ride trips on the first tick outside the window (E2 + 15 ms, persistence already >= 5 ms)
    struct Pair { RideObs asb, ride; bool ok_a = false, ok_r = false; };
    auto both = [&](const std::function<float(int, int)>& prof, int nmax) {
      Pair p;
      Rig9 a; p.ok_a = relightToE1(a) && a.o.relight_ext; p.asb = play(a, nmax, prof);
      Rig9 b; b.e.ride_through = true; p.ok_r = relightToE1(b) && b.o.relight_ext; p.ride = play(b, nmax, prof);
      return p;
    };
    const Pair A = both(fa1Like, 120), B = both(t45Like, 120), C = both(sustained, 120), D = both(lateEp, 120);
    const int win_end_A = A.ride.e2_k + 14;   // last window tick: t - t_lit < 15 ms
    const bool a_ok = A.ok_a && A.ok_r && A.asb.cause == Abort::HARD_START && A.ride.abort_k < 0 && A.ride.e2_k > 0 && A.ride.tol_n > 0 &&
                      A.ride.win_last == win_end_A && A.ride.bit4_n == 0 && A.ride.t45_n == 0 &&
                      A.ride.build_n == A.ride.ticks && A.asb.build_n == 0 && A.asb.win_n == 0 && A.asb.bit4_n == 0;
    const bool b_ok = B.ok_r && B.ride.cause == Abort::HARD_START && B.ride.t45_at_abort && B.ride.t45_n >= 7 && B.ride.abort_k - 30 <= 7 &&
                      B.asb.cause == Abort::HARD_START;
    const bool c_ok = C.asb.cause == Abort::HARD_START && C.ride.cause == Abort::HARD_START && C.ride.abort_k - C.asb.abort_k == 10;
    const bool d_ok = D.asb.cause == Abort::HARD_START && D.ride.cause == Abort::HARD_START && D.ride.e2_k > 0 &&
                      D.ride.abort_k == D.ride.e2_k + 15 && D.asb.abort_k < D.ride.abort_k;
    check(a_ok && b_ok && c_ok && d_ok,
          "v2.11 LEAD 203 (1)(b) ride-through (flight relight): FA-1-like 35 bar x 14 ms tolerated (as built HARD_START), window E1..E2+15 ms "
          "(fixed RC: no long-RC request); 50 bar x 10 ms -> T45 HARD_START <= 7 ms; sustained 35 bar -> HARD_START 10 ms later than as built; late "
          "episode trips at the window end (E2 + 15 ms)",
          fmtv("A asb k%d ride none(tol %d, E2 k%d, win last k%d); B ride k%d T45 %d asb k%d; C asb k%d ride k%d; D asb k%d ride k%d (E2 k%d)",
               A.asb.abort_k, A.ride.tol_n, A.ride.e2_k, A.ride.win_last, B.ride.abort_k, (int)B.ride.t45_at_abort, B.asb.abort_k,
               C.asb.abort_k, C.ride.abort_k, D.asb.abort_k, D.ride.abort_k, D.ride.e2_k));
    // stand relight and the flight pad first start are never in the window
    Rig9 s(false, true); s.e.ride_through = true; const bool s_ign = relightToE1(s) && !s.o.relight_ext; const RideObs so = play(s, 120, fa1Like);
    Rig9 p; p.e.ride_through = true; p.toIgnition(); p.toE1(); const RideObs po = play(p, 120, fa1Like);
    check(s_ign && so.cause == Abort::HARD_START && so.win_n == 0 && so.bit4_n == 0 && so.abort_k == A.asb.abort_k &&
              po.cause == Abort::HARD_START && po.win_n == 0 && po.bit4_n == 0 && po.build_n == po.ticks,
          "v2.11 ride-through never applies to the stand relight nor the flight pad first start (as-built 5 ms trip, no window)",
          fmtv("stand abort k%d (flight as built k%d), pad abort k%d", so.abort_k, A.asb.abort_k, po.abort_k));
    check(!cfg::kRideThroughBuild && !EngineEcu().ride_through && kRideCmpTauMin_s >= 0.010f && kRideCmpTauNom_s > kRideCmpTauMin_s &&
              kRideOverrangeN >= 2 && kRideOvpTime_s >= 0.015f - 1e-6f && kRideWinPostE2_s >= 0.013f,
          "v2.11 ride-through is a build option, default OFF (ECU_RIDE_THROUGH=0); LEAD 216 (3): comparator RC FIXED in the BOM variant "
          "(12.83 ms nominal, >= 10 ms minimum), persistence >= 13 ms + margin, window >= E2 + 8 ms + margin, over-range N >= 2",
          fmtv("tau %.2f / %.2f ms, persistence %.0f ms, window E2 + %.0f ms, N %d", 1e3 * kRideCmpTauNom_s, 1e3 * kRideCmpTauMin_s,
               1e3 * kRideOvpTime_s, 1e3 * kRideWinPostE2_s, kRideOverrangeN));
    // (v211-3b) LEAD 216 (3) over-range N >= 2: IGNITION HIGH over-range (4.90 V) after E1 of a flight relight. Ride on: one tick tolerated
    //           (RIDE_TOL, no light decision that tick, light counter held, the start lights at 3 bar -> RUN); two consecutive ticks ->
    //           HARD_START on the second. As built (ride off): HARD_START on the first tick. Stand relight and pad first start with the ride
    //           build: HARD_START on the first tick (never in the window)
    auto ovrRun = [&](Rig9& r, int n_ovr, bool* tol_seen, int* tol_ticks) {   // returns the tick index of the abort (-1 none) after E1
      r.run(20);
      int ab = -1;
      for (int k = 0; k < n_ovr; ++k) {
        r.in.pc_raw_V = 4.90f; r.in.pc_Pa = 76.0e5f; r.tick();
        if (r.o.ovr_flags & ovr::RIDE_TOL) *tol_seen = true;
        if (r.e.abortCause() != Abort::NONE) { ab = k; break; }
      }
      if (ab < 0) {
        r.setPcAbs(kAmb); r.run(5); r.setPcAbs(3.0e5f); r.until(State::RUN, 60);
        if (r.e.abortCause() != Abort::NONE) ab = 999;
      }
      *tol_ticks = r.e.rideOvrTolTicks();
      return ab;
    };
    bool t1 = false, t2 = false, t3 = false, t4 = false, t5 = false; int n1 = 0, n2 = 0, n3 = 0, n4 = 0, n5 = 0;
    Rig9 g1; g1.e.ride_through = true; const bool e1a = relightToE1(g1); const int k1 = ovrRun(g1, 1, &t1, &n1);
    const bool run1 = g1.e.state() == State::RUN && g1.e.abortCause() == Abort::NONE;
    Rig9 g2; g2.e.ride_through = true; const bool e1b = relightToE1(g2); const int k2 = ovrRun(g2, 3, &t2, &n2);
    Rig9 g3; const bool e1c = relightToE1(g3); const int k3 = ovrRun(g3, 1, &t3, &n3);
    Rig9 g4(false, true); g4.e.ride_through = true; const bool e1d = relightToE1(g4); const int k4 = ovrRun(g4, 1, &t4, &n4);
    Rig9 g5; g5.e.ride_through = true; g5.toIgnition(); g5.toE1(); const int k5 = ovrRun(g5, 1, &t5, &n5);
    check(e1a && e1b && e1c && e1d && k1 < 0 && t1 && n1 == 1 && run1 && k2 == 1 && g2.e.abortCause() == Abort::HARD_START && n2 == 1 &&
              k3 == 0 && g3.e.abortCause() == Abort::HARD_START && !t3 && k4 == 0 && g4.e.abortCause() == Abort::HARD_START && !t4 &&
              k5 == 0 && g5.e.abortCause() == Abort::HARD_START && !t5,
          "v2.11 LEAD 216 (3) over-range N = 2 in the ride window (flight relight, after E1): one HIGH over-range tick tolerated (RIDE_TOL, "
          "no light decision that tick) and the start lights (RUN); two consecutive -> HARD_START on the second; as built, stand relight "
          "and pad first start: HARD_START on the first",
          fmtv("ride 1 tick: abort k%d tol %d (%d) RUN %d; ride 3 ticks: abort k%d (%s); as built k%d; stand k%d; pad k%d", k1, (int)t1, n1,
               (int)run1, k2, abortName(g2.e.abortCause()), k3, k4, k5));
  }
  {   // (v211-4) v2.12 (LEAD 256 (2), 257 (2), 258 (2)): flow 2.43 s, both-open cap 2.39 s. The scheduled purge commands both valves open
      //          for F + t_o - t_c = 2.38 s (+1 tick) on COMMAND time, inside the cap by >= 2 ticks: EV_CAP never fires (v2.11: 2.50 / 2.55 s)
    Rig9 r(true); toCoast(r); r.run(500); r.tick(Cmd::PURGE); const double t0 = r.t;
    int both = 0;
    while (r.t - t0 < kPurgeRelight_s - 0.0005) { r.tick(); if (r.o.hbleed[0] && r.o.hbleed[1]) ++both; }
    const int exp_ms = static_cast<int>(std::lround(1000.0f * (kPurgeFlow_s + kHbleedOpenTime_s - kHbleedCloseTime_s)));
    check(std::abs(both - exp_ms) <= 1 && r.n_ev[hb::EV_CAP] == 0 && std::fabs(kHbleedCap_s - 2.39f) < 1e-6f && 1000 * kHbleedCap_s - both >= 8 &&
              std::fabs(kPurgeFlow_s - 2.43f) < 1e-6f && r.e.purgeFlow_s() == kPurgeFlow_s && r.e.hbleedCap_s() == kHbleedCap_s,
          "v2.12 LEAD 256 (2) / 257 (2) purge FINAL: flow 2.43 s, cap 2.39 s; scheduled both-open command span 2.38 s, never capped "
          "(EV_CAP 0), >= 8 ms command margin (2 ticks + rounding)",
          fmt("both open %.0f ms (expected %.0f), cap %.0f ms", both, exp_ms, 1000 * kHbleedCap_s));
  }
  {   // (v211-5) LEAD 205: C1 Kulite XTL-190SM-2000A absolute scaling through XdcrCal::abs_ref_Pa (gauge-equivalent vs the core ambient)
    using namespace xdcr;
    const float pamb = 101325.f, vexc = cfg::kXdcrExcNom_V;
    const XdcrCal c = calXtl190(pamb), f = pcFlightCal(pamb), g = cal070BG();
    double worst = 0;
    for (float pa : {0.2e5f, 1.01325e5f, 3.0e5f, 25.0e5f, 30.0e5f, 45.0e5f, 70.0e5f, 102.0e5f, 137.0e5f}) {
      const int32_t code = codeForGaugePa(pa - pamb, vexc, c);
      worst = std::fmax(worst, std::fabs(gaugePa(sigVolts(adcVolts(code), c), vexc, c) - (pa - pamb)));
    }
    const float ppc = paPerCount(vexc, c);
    const float p475 = gaugePa(cfg::kPcSensorMax_V, vexc, c) + pamb, p456 = gaugePa(cfg::kPcAboveFs_V, vexc, c) + pamb;
    const float v70 = vexc * (c.zero_frac + c.span_frac * 70.0e5f / c.fs_Pa);
    XdcrCal bad = c; bad.abs_ref_Pa = 1.3e5f;
    check(c.valid() && f.fs_Pa == c.fs_Pa && f.abs_ref_Pa == pamb && g.abs_ref_Pa == 0.0f && worst < 1.5 * ppc && ppc > 1.8f && ppc < 2.4f &&
              std::fabs(p475 - 146.51e5f) < 0.05e5f && std::fabs(p456 - 139.96e5f) < 0.05e5f && v70 > 2.5f && v70 < 2.56f &&
              4.95f * c.k_div < cfg::kAdcVref_V && !bad.valid(),
          "v2.11 LEAD 205 C1 scaling: gauge-equivalent round trip 0.2-137 bar abs within 1.5 LSB (~2.1 Pa/count); 4.75 V = 146.5 bar abs, "
          "4.56 V = 139.96 bar abs, LC-TB70 70 bar abs = 2.53 V; INA rail 4.95 V inside the ADC range; abs_ref bound 0-1.2 bar",
          fmtv("worst %.2f Pa, %.3f Pa/count, 4.75 V = %.2f bar abs, 4.56 V = %.2f bar abs, 70 bar = %.3f V, rail %.4f V at the ADC", worst, ppc,
               p475 / 1e5, p456 / 1e5, v70, 4.95f * c.k_div));
  }
}
