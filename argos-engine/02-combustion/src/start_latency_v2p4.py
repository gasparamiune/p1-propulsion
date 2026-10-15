"""Start / relight latency of the v2.4 sequence and the abort-deadline trade (Combustion v2.4; closes review RC-03, feeds
RC-01 and RC-02).

Sequence modelled (v2.4, igniter.sequence_v2p4 in combustion.json):
  E0  ECU receives START/RELIGHT: torch SOL1 (N2O) + SOL2 (propane) open, spark train.
  E1  torch flame confirmed (hard gate): NC valve command (if closed) AND pintle to the ignition lift (never further).
      N2O reaches the chamber: at once for a primed liquid-full line (pad start, valve-open coast, or a liquid-full trapped
      segment); after the valve flow onset plus the vapour purge for a segment holding vapour (C7).
  ign main ignition after an ignition delay (unknown; ASSUMED band).
  E2  Pc confirmation: measured Pc (2.3 ms latency) > 3.0 bar abs for 10 ms. SOL1 closed first, SOL2 with it;
      the thrust ramp starts 20 ms later (SOL1 closing time, ASSUMED).
  E3  thrust >= 90 % of the relight command (ramp <= 2500 N/s cap; 1000 N/s slow case).
Part 1: grain_q1d v2 start transients from main ignition at the ignition lift (port, tank, regression law (a, n)
        re-anchored at r(300 kg/m2s) = 1 mm/s, preheat fraction, eta_c*), giving ignition->E2 and E2->E3.
Part 2: Monte Carlo of E0->E2 / E0->E3 per line-state case with the ASSUMED input distributions below; percentiles
        for GNC; false-abort probability against the abort deadline (counted from the ignition-lift command).
Every distribution here is ASSUMED (no ignition data exist); IGN-1, T1 and T4 replace them.
usage: python -I start_latency_v2p4.py OUTDIR [--quick]
"""
from __future__ import annotations
import json, math, os, sys, time, itertools
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
from tank import EquilibriumTank

PAMB = 101325.0
V_PINTLE = 0.004 / 0.24          # HV69 at MEOP (DERIVED)
T_CMD = 0.0065                   # electronics.json v1: ECU -> servo PWM 5 ms + servo internal 1.5 ms
PC_LAT = 0.0023                  # electronics.json v1 pc_sensor_to_controller
P_CONF = 3.0e5                   # ENG-04 / igniter.sequence: Pc > 3 bar abs
T_PERSIST = 0.010                # ASSUMED confirmation persistence
T_SOL1 = 0.020                   # ASSUMED SOL1 closing time before the ramp may start
STATES = {
    'A1_relight': dict(T=286.70, m=1.16, D=0.032213, tag='Combustion A1 v2 run at the relight command (t 24.08 s): P_tank 4.35 MPa, '
                       'T 286.7 K, port 32.2 mm'),
    'pad_20C': dict(T=293.15, m=2.0, D=0.025, tag='pad start, tank 20 C, initial port'),
    'pad_15C': dict(T=288.15, m=2.0, D=0.025, tag='pad start, tank 15 C (cold corner of ENG-12), initial port'),
}


def law(n, a_fac):
    return dict(a=1.0e-3 / 300.0 ** n * a_fac, n=n)


def ign_lift(state, frac):
    s = STATES[state]
    e = Q.Engine(EquilibriumTank(3.17e-3, s['m'], s['T']))      # ECU map = nominal law (a x1.0, n 0.5, eta_c* 0.92)
    e.D[:] = s['D']
    h, _ = e.lift_for_thrust(frac * 500.0)
    return h, e.steady(h)


def start_sim(state, frac, a_fac, n, r_ign, eta, ramp, F_cmd, h_ign, dt=5e-4, t_max=1.6, loop_K=0.0):
    """Main ignition at t = 0 with the pintle at h_ign and the chamber at the cold-flow pressure (1.1 bar).
    After confirmation the thrust command ramps at `ramp` to F_cmd; the lift is the feed-forward map lift (quasi-steady
    regression) times (1 + c), with dc/dt = loop_K (F_cmd_eff - F)/F_cmd (an integral thrust/Pc loop, ASSUMED gain;
    loop_K = 0 is feed-forward only), c in [-0.3, 0.6], lift capped by the stiffness ceiling."""
    s = STATES[state]
    cfg = dict(law(n, a_fac)); cfg.update(r_ign_frac=r_ign, eta_cstar=eta, t_open_delay=0.0, h_rate=V_PINTLE)
    e = Q.Engine(EquilibriumTank(3.17e-3, s['m'], s['T']), cfg)
    e.D[:] = s['D']
    e.h = e.h_cmd = e.h_target = h_ign; e.state = 'start'; e.t_on = 0.0; e.Pc = 1.1e5; e.F = 0.0
    k_lat = int(round(PC_LAT / dt))
    hist_P = []; t = 0.0; t_conf = None; t_rs = None; t90 = None; F_at_rs = None; above = None
    t_true3 = None; next_ctrl = 0.0; cei = None; c_int = 0.0; Fc = 0.0; i = 0
    while t < t_max:
        e.t = t
        if t_conf is None:
            Pm = hist_P[-1 - k_lat] if len(hist_P) > k_lat else 1.1e5
            if Pm >= P_CONF:
                above = t if above is None else above
                if t - above >= T_PERSIST:
                    t_conf = t; t_rs = t + T_SOL1
            else:
                above = None
        if t_rs is not None and t >= t_rs and t >= next_ctrl - 1e-12:
            if F_at_rs is None:
                F_at_rs = e.F
            Fc = min(F_cmd, F_at_rs + ramp * (t - t_rs))
            if cei is None or (t - t_rs) % 0.1 < 0.010:
                cei = e.ceiling()
            hff, cei = e.lift_for_thrust(Fc, h_guess=e.h_target if e.h_target > 0 else None, cei=cei)
            if loop_K > 0:
                c_int = min(max(c_int + loop_K * (Fc - e.F) / F_cmd * 0.010, -0.3), 0.6)
            e.h_target = min(hff * (1.0 + c_int), cei['h'] if cei else hff)
            next_ctrl = t + 0.010
        e.step(dt)
        hist_P.append(e.Pc)
        if t_true3 is None and e.Pc >= P_CONF:
            t_true3 = t
        if t_conf is not None and t90 is None and e.F >= 0.9 * F_cmd:
            t90 = t
            break
        t += dt; i += 1
    return dict(t_true_3bar_s=t_true3, t_conf_s=t_conf, t_ramp_start_s=t_rs, t90_s=t90,
                F_at_ramp_start_N=F_at_rs, Pc_end_Pa=e.Pc, loop_K=loop_K)


def part1(quick=False):
    fracs = (0.125, 0.15, 0.20)
    a_facs = (0.6, 1.0, 1.5)
    ns = (0.35, 0.5, 0.68)
    r_igns = (0.15, 0.3, 0.6)
    etas = (0.85, 0.92)
    states = ('A1_relight', 'pad_20C')
    if quick:
        a_facs = (1.0,); ns = (0.5,); r_igns = (0.3,); etas = (0.92,); states = ('A1_relight',)
    lifts = {}
    for st in states:
        for fr in fracs:
            h, s = ign_lift(st, fr)
            lifts[f'{st}|{fr:.3f}'] = dict(lift_m=h, Pc_settled_nominal_Pa=s['Pc'], F_settled_nominal_N=s['F'], mox_kg_s=s['mox'])
    rows = []
    for st, fr, af, n, ri, et in itertools.product(states, fracs, a_facs, ns, r_igns, etas):
        h = lifts[f'{st}|{fr:.3f}']['lift_m']
        Fcmd = 200.0 if st == 'A1_relight' else 500.0
        r = start_sim(st, fr, af, n, ri, et, 2500.0, Fcmd, h)
        r.update(state=st, frac=fr, a_fac=af, n=n, r_ign=ri, eta=et, ramp=2500.0, F_cmd=Fcmd)
        rows.append(r)
    # integral-loop variant (ASSUMED K 15 1/s) at the A1 relight over the same grid
    for fr, af, n, ri, et in itertools.product(fracs, a_facs, ns, r_igns, etas):
        h = lifts[f'A1_relight|{fr:.3f}']['lift_m']
        r = start_sim('A1_relight', fr, af, n, ri, et, 2500.0, 200.0, h, loop_K=15.0)
        r.update(state='A1_relight', frac=fr, a_fac=af, n=n, r_ign=ri, eta=et, ramp=2500.0, F_cmd=200.0)
        rows.append(r)
    # pad 15 C at the nominal law only
    for fr, ri in itertools.product(fracs, r_igns):
        st = 'pad_15C'
        h, sx = ign_lift(st, fr)
        lifts[f'{st}|{fr:.3f}'] = dict(lift_m=h, Pc_settled_nominal_Pa=sx['Pc'], F_settled_nominal_N=sx['F'], mox_kg_s=sx['mox'])
        r = start_sim(st, fr, 1.0, 0.5, ri, 0.92, 2500.0, 500.0, h)
        r.update(state=st, frac=fr, a_fac=1.0, n=0.5, r_ign=ri, eta=0.92, ramp=2500.0, F_cmd=500.0)
        rows.append(r)
    # slow-ramp and 300 N subsets at the nominal law
    for st, fr in itertools.product(('A1_relight',), fracs):
        h = lifts[f'{st}|{fr:.3f}']['lift_m']
        for ramp, Fcmd in ((1000.0, 200.0), (2500.0, 300.0), (1000.0, 300.0)):
            for ri in r_igns:
                r = start_sim(st, fr, 1.0, 0.5, ri, 0.92, ramp, Fcmd, h)
                r.update(state=st, frac=fr, a_fac=1.0, n=0.5, r_ign=ri, eta=0.92, ramp=ramp, F_cmd=Fcmd)
                rows.append(r)
    return lifts, rows


def pct(x, q):
    x = np.asarray([v for v in x if v is not None and np.isfinite(v)])
    return float(np.percentile(x, q)) if len(x) else float('nan')


def part2(lifts, rows, N=200000, seed=2024):
    """Monte Carlo of the sequence; distributions ASSUMED (tags in the output)."""
    rng = np.random.default_rng(seed)
    out = {}; dl = {}
    dist = dict(t_sol_open_s='U(0.005, 0.020) ASSUMED small NC solenoid', t_torch_light_s='U(0.02, 0.10) ASSUMED spark-to-flame',
                t_torch_detect_s='U(0.005, 0.030) ASSUMED flame sensor (photodiode / torch-cavity pressure)',
                t_pintle_to_lift_s=f'{T_CMD*1e3:.1f} ms command + lag/travel at {V_PINTLE*1e3:.1f} mm/s (DERIVED)',
                t_valve_flow_onset_s='U(0.05, 0.15) ASSUMED (servo-cocked ball valve, ~0.3 s full opening, electronics.json v1)',
                vapour_fraction_of_segment='U(0, 1) ASSUMED (no coast thermal model of the segment yet)',
                t_purge_full_vapour_s='0.31 s, NC valve at the coil end (low_inlet_check_v2p3, C7)',
                main_ignition_delay_s='U(0.05, 0.30) ASSUMED (review RC-03 band)',
                ignition_to_confirmation_and_ramp='resampled from the Part 1 grain_q1d runs at the case state and lift '
                                                  '(a x0.6-1.5, n 0.35-0.68, preheat 0.15-0.6, eta_c* 0.85/0.92; ramp 2500 N/s)')
    by = {}
    for r in rows:
        if r['ramp'] == 2500.0 and r['F_cmd'] in (200.0, 500.0):
            by.setdefault((r['state'], r['frac'], r.get('loop_K', 0.0)), []).append(r)
    cases = {'pad_start_primed': ('pad_20C', 0), 'pad_start_primed_15C': ('pad_15C', 0),
             'relight_valve_open_coast': ('A1_relight', 0), 'relight_valve_closed_liquid_segment': ('A1_relight', 1),
             'relight_valve_closed_vapour_segment_U01': ('A1_relight', 2), 'relight_valve_closed_full_vapour': ('A1_relight', 3)}
    cases.update({'relight_valve_open_coast_PcLoop': ('A1_relight', 0, 15.0),
                  'relight_valve_closed_vapour_segment_U01_PcLoop': ('A1_relight', 2, 15.0)})
    for cname, spec in cases.items():
        st, mode = spec[0], spec[1]; lk = spec[2] if len(spec) > 2 else 0.0
        for fr in (0.125, 0.15, 0.20):
            pool = by.get((st, fr, lk), [])
            if not pool:
                continue
            h = lifts[f'{st}|{fr:.3f}']['lift_m']
            t_lift = T_CMD + h / V_PINTLE + 0.010            # command + travel + ~1 lag constant (DERIVED)
            idx = rng.integers(0, len(pool), N)
            tc = np.array([np.nan if p['t_conf_s'] is None else p['t_conf_s'] for p in pool])[idx]
            t9 = np.array([np.nan if p['t90_s'] is None else p['t90_s'] for p in pool])[idx]
            e1 = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)
            if mode == 0:
                arr = np.zeros(N); valve = np.zeros(N)
            elif mode == 1:
                arr = np.zeros(N); valve = np.ones(N)
            elif mode == 2:
                arr = rng.uniform(0.05, 0.15, N) + rng.uniform(0.0, 1.0, N) * 0.31; valve = np.ones(N)
            else:
                arr = rng.uniform(0.05, 0.15, N) + 0.31; valve = np.ones(N)
            ig = rng.uniform(0.05, 0.30, N)
            from_lift_cmd_to_conf = t_lift + arr + ig + tc        # abort deadline is counted from the lift command (= E1)
            E2 = e1 + from_lift_cmd_to_conf
            E3 = e1 + t_lift + arr + ig + t9
            fail = ~np.isfinite(tc)
            key = f'{cname}|{fr:.3f}'
            out[key] = dict(
                state=st, ignition_lift_m=h, valve_step=bool(valve[0]), no_confirmation_fraction=float(fail.mean()),
                E0_to_E1_torch_s=dict(median=pct(e1, 50), p95=pct(e1, 95), p99=pct(e1, 99)),
                E1_to_E2_s=dict(median=pct(from_lift_cmd_to_conf, 50), p95=pct(from_lift_cmd_to_conf, 95), p99=pct(from_lift_cmd_to_conf, 99),
                                p999=pct(from_lift_cmd_to_conf, 99.9)),
                E0_to_E2_s=dict(median=pct(E2, 50), p95=pct(E2, 95), p99=pct(E2, 99)),
                E0_to_E3_s=dict(median=pct(E3, 50), p95=pct(E3, 95), p99=pct(E3, 99), p999=pct(E3, 99.9),
                                P_le_0p5s=float(np.mean(E3[np.isfinite(E3)] <= 0.5)), P_le_0p6s=float(np.mean(E3[np.isfinite(E3)] <= 0.6))),
                E2_to_E3_s=dict(median=pct(t9 - tc, 50), p95=pct(t9 - tc, 95), p99=pct(t9 - tc, 99)))
            # false-abort probability against the abort deadline (from the lift command), excluding no-confirmation runs
            dd = {}
            for W in (0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70, 0.80, 1.00):
                ok = np.isfinite(from_lift_cmd_to_conf)
                dd[f'{W:.2f}'] = float(np.mean(from_lift_cmd_to_conf[ok] > W)) if ok.any() else float('nan')
            dl[key] = dd
            # GNC sampling table: quantiles of E0->E3 (1 % steps) for the case
            out[key]['E0_to_E3_quantiles_s'] = [round(pct(E3, q), 4) for q in range(0, 101, 5)]
    return dist, out, dl


def main(outdir, quick=False):
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    lifts, rows = part1(quick)
    t1 = time.time()
    dist, mc, dl = part2(lifts, rows)
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/start_latency_v2p4.py',
               closes='REVIEW-COMBUSTION RC-03 (latency of the adopted sequence); inputs to RC-01/RC-02 (abort deadline)',
               epochs=dict(E0='ECU receives START/RELIGHT (torch valves open, spark)', E1='torch flame confirmed: valve command '
                           '(if closed) and pintle command to the ignition lift', E2='Pc confirmation (measured Pc > 3.0 bar abs for '
                           '10 ms, 2.3 ms sensor latency)', E3='thrust >= 90 % of the start/relight command'),
               constants=dict(V_pintle_m_s=V_PINTLE, T_cmd_s=T_CMD, Pc_latency_s=PC_LAT, P_conf_Pa=P_CONF, T_persist_s=T_PERSIST,
                              T_SOL1_s=T_SOL1, tags=dict(V_pintle='DERIVED HV69 0.24 s full stroke at MEOP', T_cmd='DERIVED electronics.json v1',
                                                         Pc_latency='DERIVED electronics.json v1', P_conf='LEAD ENG-04 / v2.3 sequence',
                                                         T_persist='ASSUMED', T_SOL1='ASSUMED')),
               states=STATES, ignition_lifts=lifts,
               part1_runs=dict(v=rows, tag='SIM grain_q1d v2 start from main ignition at the ignition lift (chamber 1.1 bar), '
                               'confirmation logic and ramp as in the docstring; t from main ignition', runtime_s=round(t1 - t0, 1)),
               mc_input_distributions=dict(v=dist, tag='ASSUMED (no ignition data); IGN-1/T1/T4 replace them'),
               latency_mc=dict(v=mc, tag='SIM Monte Carlo 200 000 samples per case (seed 2024) over the ASSUMED distributions'),
               false_abort_vs_deadline=dict(v=dl, tag='SIM: probability that Pc confirmation comes later than the abort deadline W '
                                            '(W counted from the ignition-lift command)'))
    fn = os.path.join(outdir, 'start_latency_v2p4.json' if not quick else 'start_latency_v2p4_quick.json')
    with open(fn, 'w') as f:
        json.dump(res, f, indent=1, default=float)
    print('wrote', fn, f'{time.time()-t0:.1f}s')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else os.path.join(HERE, '..', 'data', 'v2', 'v2p4'),
         quick='--quick' in sys.argv)
