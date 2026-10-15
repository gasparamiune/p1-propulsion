"""Tables and supplementary runs for OI-A5-LATE (Combustion v2.4, 2026-10-13): late light inside W, A5 and the start monitors.

Reads late_light_spike_v2p4.json (the 5 400-row case grid) and adds four supplementary sets with the same model
(late_light_spike_v2p4.Light, admitted, metrics; nothing in the model is changed):
  S1  flight FIRST START window (kIgnWindowFirst_s 0.40 s, electronics.json firmware.W_build_constant): latest light whose E2 still
      falls inside W, t_L = 0.40 - 0.018 s, pad states 15 / 20 / 25 C (fresh 25 mm port), the full tf / t_res / pool grid;
  S2  pool-burn duration above 6.9 bar abs (A7 START-band high limit 1.3 x 5.3 bar while the map is below 5.3 bar) and above 8 bar,
      against a fine sweep of the evaporation flux q (0.80-2.00 MW/m2, 0.05 steps), retained pool (f_ret 1), tf 5 ms, t_res 60 ms,
      rounded entrance, at the latest light of each window and at the lead's accepted 26.6 g (SIL-flow basis, CHANGELOG line 82-83);
  S3  firmware-filter reading of the decomposition spike: the measured channel (2.3 ms latency) through a first-order 50 Hz filter
      (tau 3.18 ms; ASSUMED stand-in for the firmware filter) and through the comparator RC (tau 5.28 ms): peak and continuous time
      above 30 bar abs, for every tf 1 and 2 ms row at the latest lights;
  S4  the pool evaporation rate and pool lifetime per state and q (DERIVED: q A_wet / h_fg).
usage: python -I late_light_tables_v2p4.py DATA_V2P4_DIR SPIKE_JSON OUT_JSON
"""
from __future__ import annotations
import hashlib, itertools, json, math, os, sys, time
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import late_light_spike_v2p4 as LL
import hard_start_v2p4 as HS
import hard_start_multivolume_v2p4 as MV

A7_HI = 1.3 * 5.3e5          # Pa abs: START-band high limit while the map is below 5.3 bar (electronics.json start_monitors_v2p9.A7)
TAU50 = 1.0 / (2.0 * math.pi * 50.0)
INV_LEAD = 26.6e-3           # kg: flight relight inventory accepted by the lead (CHANGELOG line 82-83, SIL flow at W 0.65 s)
Q_SWEEP = tuple(round(0.80 + 0.05 * i, 2) for i in range(25))


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def pct(v):
    v = np.asarray(v, float)
    return dict(min=float(v.min()), p50=float(np.percentile(v, 50)), p99=float(np.percentile(v, 99)), max=float(v.max()), n=int(v.size))


def above(t, x, thr):
    m_ = x > thr
    if not m_.any():
        return 0.0
    i0 = int(np.argmax(m_)); j = i0
    while j < len(m_) and m_[j]:
        j += 1
    return float(t[min(j, len(t) - 1)] - t[i0])


def lowpass(t, x, tau, x0):
    y = np.empty_like(x); acc = x0
    for i in range(len(x)):
        dt = (t[i] - t[i - 1]) if i else 0.0
        a = dt / (tau + dt) if dt > 0 else 0.0
        acc += a * (x[i] - acc); y[i] = acc
    return y


def setup(J, M, st):
    lifts = J['ignition_lifts']['v']; cold = J['cold_flow_at_ignition_lift']['v']
    L = lifts[f'{st}|0.125']; c = cold[f'{st}|0.125']
    P1, T1, P2 = L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa']
    if st in ('20C', 'A1_relight'):
        prod = M['products']['dec_20C' if st == '20C' else 'dec_A1']
    else:
        prod = HS.products('dec', 288.15 if st == '15C' else 298.15)
    r_inj = HS.mdot_cold(LL.H_IGN, P1, T1, P2)
    x_liq = c['liquid_flow_kg_s'] / c['mdot_cold_kg_s']
    D = 0.032213 if st == 'A1_relight' else 0.025
    return dict(P1=P1, T1=T1, P2=P2, prod=prod, r_inj=r_inj, x_liq=x_liq, D=D, vap_g=c['vapour_in_chamber_g']['reviewer_300.9cm3'])


def fast(sd, lt, tres, m_inv):
    m_vap = sd['vap_g'] * 1e-3 * lt.Vs / 300.9e-6
    m_s = sd['r_inj'] * sd['x_liq'] * tres
    m_f = min(m_vap + m_s, m_inv)
    sp = [(m_vap * lt.V3[0] / lt.Vs + m_s) / (m_vap + m_s), m_vap * lt.V3[1] / lt.Vs / (m_vap + m_s), m_vap * lt.V3[2] / lt.Vs / (m_vap + m_s)]
    return m_f, sp


def main(d, spike_f, out_f):
    t0 = time.time()
    SP = json.load(open(spike_f)); R = SP['rows']
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    M = json.load(open(os.path.join(d, 'hard_start_multivolume_v2p4.json')))
    assert sha16(os.path.join(d, 'hard_start_v2p4.json')) == SP['inputs']['hard_start_v2p4.json']
    assert sha16(os.path.join(d, 'hard_start_multivolume_v2p4.json')) == SP['inputs']['hard_start_multivolume_v2p4.json']
    band = {f'{x:.3f}' for x in SP['constants']['ig_band_s']}
    STATES = ('15C', '20C', '25C', 'A1_relight')

    def sel(st=None, ent=None, labs=None, tf=None, pool=None, tres=None):
        out = []
        for k, r in R.items():
            s, e, lab, tfk, trk, pk = k.split('|')
            if (st and s != st) or (ent and not e.startswith(ent)) or (labs and lab not in labs) or (tf and tfk != tf) \
               or (pool and pk != pool) or (tres and trk != tres):
                continue
            out.append(r)
        return out

    # ---- T1: per state and window, over the case grid (equal weights: a grid percentile, not a probability)
    T1 = {}
    for st in STATES:
        for scope, labs in (('flight_W0.65', band | {'flight_latest'}), ('stand_W0.35', band | {'stand_latest'}),
                            ('band_only', band), ('flight_latest_only', {'flight_latest'}), ('stand_latest_only', {'stand_latest'})):
            for ent in (None, 'rounded', 'sharp'):
                S = sel(st, ent, labs)
                T1[f'{scope}|{st}|{ent or "both"}'] = dict(
                    peak_head_bar=pct([r['peak_head_bar'] for r in S]), above8_cont_s=pct([r['above8_cont_s'] for r in S]),
                    above8_measured_cont_s=pct([r['above8_meas_cont_s'] for r in S]), above30_cont_s_max=max(r['above30_cont_s'] for r in S),
                    above45_cont_s_max=max(r['above45_cont_s'] for r in S), comparator_RC_peak_abs_bar_max=max(r['comparator_filtered_peak_abs_bar'] for r in S),
                    comparator_trips=int(sum(r['comparator_trip_low_band'] for r in S)), A5_trip_fraction=float(np.mean([r['t_A5_s'] is not None for r in S])),
                    A5_before_E2_fraction=float(np.mean([r['A5_before_E2'] for r in S])),
                    t_A5_after_light_s=[min(r['t_A5_s'] for r in S if r['t_A5_s'] is not None), max(r['t_A5_s'] for r in S if r['t_A5_s'] is not None)],
                    t_E2_after_light_raw_s=[min(r['t_E2_s'] for r in S if r['t_E2_s'] is not None), max(r['t_E2_s'] for r in S if r['t_E2_s'] is not None)],
                    inventory_g=[min(r['inventory_g'] for r in S), max(r['inventory_g'] for r in S)])
    # ---- T2: peak by tf (max over light time, t_res, pool), per state and entrance; A5 fraction by tf
    T2 = {}
    for st in STATES:
        for ent in ('rounded', 'sharp'):
            for tf in SP['constants']['tf_s']:
                S = sel(st, ent, band | {'flight_latest', 'stand_latest'}, tf=f'tf{tf*1e3:.0f}ms')
                T2[f'{st}|{ent}|tf{tf*1e3:.0f}ms'] = dict(peak_max_bar=max(r['peak_head_bar'] for r in S), peak_min_bar=min(r['peak_head_bar'] for r in S),
                                                         above30_max_s=max(r['above30_cont_s'] for r in S),
                                                         A5_trip_fraction=float(np.mean([r['t_A5_s'] is not None for r in S])),
                                                         above8_no_pool_max_s=max(r['above8_cont_s'] for r in S if r['m_pool_g'] == 0.0))
    # ---- T3: time above 8 bar by pool model, latest lights (max over state-specific rows)
    T3 = {}
    for st in STATES:
        for lab in ('flight_latest', 'stand_latest'):
            for pool in [p for p in SP['constants']['pools']]:
                S = sel(st, None, {lab}, pool=pool)
                T3[f'{lab}|{st}|{pool}'] = dict(above8_max_s=max(r['above8_cont_s'] for r in S), m_pool_g=max(r['m_pool_g'] for r in S),
                                                tau_pool_s=max(r['tau_pool_s'] for r in S), peak_max_bar=max(r['peak_head_bar'] for r in S))
    # ---- T4: SIL light times (20 C, rounded): the SIL plant gave 26.9 / 28.6 bar abs at t_L 0.20 / 0.25 s
    sil = SP['sil_comparison_20C_rounded']
    T4 = {}
    for tl in ('0.200', '0.250'):
        rows = {k: v for k, v in sil.items() if f'SIL_tL{tl}' in k}
        T4[tl] = dict(peak_bar=[min(v['peak_head_bar'] for v in rows.values()), max(v['peak_head_bar'] for v in rows.values())],
                      peak_tf1_tres0p02_bar=[min(v['peak_head_bar'] for k, v in rows.items() if 'tf1ms|tres0.02' in k), max(v['peak_head_bar'] for k, v in rows.items() if 'tf1ms|tres0.02' in k)],
                      t_A5_s=[min(v['t_A5_s'] for v in rows.values() if v['t_A5_s']), max(v['t_A5_s'] for v in rows.values() if v['t_A5_s'])],
                      t_E2_raw_s=[min(v['t_E2_s'] for v in rows.values()), max(v['t_E2_s'] for v in rows.values())],
                      above8_s=[min(v['above8_cont_s'] for v in rows.values()), max(v['above8_cont_s'] for v in rows.values())])
    print('aggregation done', round(time.time() - t0, 1), 's', flush=True)
    # ---- supplementary runs
    S1 = {}; S2 = {}; S3 = {}; S4 = {}
    tl_lift = LL.t_lift()
    for st in STATES:
        sd = setup(J, M, st)
        for lab_e, cd in LL.ENTR:
            lt = LL.Light(sd['prod'], sd['D'], cd, sd['P2'])
            # S1: flight first start, pad states only
            if st != 'A1_relight':
                t_L = 0.40 - LL.SIL_E2_MAX
                m_inv, _ = LL.admitted(sd['P1'], sd['T1'], sd['P2'], t_L)
                for tf, tres in itertools.product(LL.TFS, LL.TRES):
                    m_f, sp = fast(sd, lt, tres, m_inv)
                    for lab_p, fr, q in LL.POOLS:
                        m_pool = max(m_inv - m_f, 0.0) * fr
                        t, P, tau_p = lt.run(sd['r_inj'], m_f, sp, tf, m_pool, q)
                        mt = LL.metrics(t, P, sd['P2'])
                        S1[f'{st}|{lab_e}|first_latest|tf{tf*1e3:.0f}ms|tres{tres}|{lab_p}'] = dict(t_L_s=t_L, inventory_g=1e3 * m_inv, m_pool_g=1e3 * m_pool, tau_pool_s=tau_p, **mt)
            # S3: filtered readings of the spike, tf 1 and 2 ms, latest lights
            for lab_t, t_L in (('flight_latest', 0.65 - LL.SIL_E2_MAX), ('stand_latest', 0.35 - LL.SIL_E2_MAX)):
                m_inv, _ = LL.admitted(sd['P1'], sd['T1'], sd['P2'], t_L)
                for tf, tres in itertools.product((1e-3, 2e-3), LL.TRES):
                    m_f, sp = fast(sd, lt, tres, m_inv)
                    for lab_p, fr, q in LL.POOLS:
                        m_pool = max(m_inv - m_f, 0.0) * fr
                        t, P, tau_p = lt.run(sd['r_inj'], m_f, sp, tf, m_pool, q)
                        ph = P[0]; k = int(round(LL.SL.PC_LAT / LL.DT_OUT))
                        pm = np.concatenate([np.full(k, sd['P2']), ph[:-k]])
                        f50 = lowpass(t, pm, TAU50, sd['P2']); frc = lowpass(t, pm, LL.RC_TAU, sd['P2'])
                        S3[f'{st}|{lab_e}|{lab_t}|tf{tf*1e3:.0f}ms|tres{tres}|{lab_p}'] = dict(
                            raw_peak_bar=float(ph.max()) / 1e5, raw_above30_s=above(t, pm, LL.FW_ABS),
                            f50_peak_bar=float(f50.max()) / 1e5, f50_above30_s=above(t, f50, LL.FW_ABS),
                            rc_peak_bar=float(frc.max()) / 1e5)
        # S2: pool duration against q (rounded entrance), latest lights and the lead's 26.6 g
        lt = LL.Light(sd['prod'], sd['D'], 1.0, sd['P2'])
        cases = [('flight_relight_latest', 0.65 - LL.SIL_E2_MAX, None), ('stand_latest', 0.35 - LL.SIL_E2_MAX, None)]
        if st == 'A1_relight':
            cases.append(('lead_26.6g', 0.65 - LL.SIL_E2_MAX, INV_LEAD))
        else:
            cases += [('flight_first_latest', 0.40 - LL.SIL_E2_MAX, None), ('lead_26.6g', 0.65 - LL.SIL_E2_MAX, INV_LEAD)]
        for lab_c, t_L, inv_override in cases:
            m_inv = inv_override if inv_override else LL.admitted(sd['P1'], sd['T1'], sd['P2'], t_L)[0]
            m_f, sp = fast(sd, lt, 0.06, m_inv)
            for qq in Q_SWEEP:
                q = qq * 1e6
                m_pool = max(m_inv - m_f, 0.0)
                t, P, tau_p = lt.run(sd['r_inj'], m_f, sp, 5e-3, m_pool, q, t_cap=1.6)
                ph = P[0]
                mid = (t > 0.02) & (t < max(0.03, 0.8 * tau_p))
                S2[f'{st}|{lab_c}|q{qq:.2f}'] = dict(inventory_g=1e3 * m_inv, m_pool_g=1e3 * m_pool, tau_pool_s=tau_p,
                                                     plateau_bar=float(np.median(ph[mid])) / 1e5 if mid.any() else None,
                                                     above6p9_s=above(t, ph, A7_HI), above8_s=above(t, ph, LL.A5_P))
        for qq in (0.5, 1.0, 1.5, 2.0):
            S4[f'{st}|q{qq}'] = dict(A_wet_m2=lt.A_wet, evap_g_s=1e3 * qq * 1e6 * lt.A_wet / LL.H_EV, injector_g_s=1e3 * sd['r_inj'])
        print(st, 'supplementary done', round(time.time() - t0, 1), 's', flush=True)
    # ---- summaries of the supplementary sets
    S1s = {}
    for st in ('15C', '20C', '25C'):
        rows = [v for k, v in S1.items() if k.startswith(st + '|')]
        S1s[st] = dict(peak_head_bar=pct([r['peak_head_bar'] for r in rows]), above8_cont_s=pct([r['above8_cont_s'] for r in rows]),
                       inventory_g=rows[0]['inventory_g'], A5_trip_fraction=float(np.mean([r['t_A5_s'] is not None for r in rows])))
    S2s = {}
    for k, v in S2.items():
        st, lab, _ = k.split('|')
        key = f'{st}|{lab}'
        cur = S2s.setdefault(key, dict(above6p9_max_s=0.0, q_at_max_6p9=None, above8_max_s=0.0, q_at_max_8=None, inventory_g=v['inventory_g']))
        if v['above6p9_s'] > cur['above6p9_max_s']:
            cur['above6p9_max_s'] = v['above6p9_s']; cur['q_at_max_6p9'] = float(k.split('|q')[1])
        if v['above8_s'] > cur['above8_max_s']:
            cur['above8_max_s'] = v['above8_s']; cur['q_at_max_8'] = float(k.split('|q')[1])
    S3s = dict(raw_above30_max_s=max(v['raw_above30_s'] for v in S3.values()), f50_peak_max_bar=max(v['f50_peak_bar'] for v in S3.values()),
               f50_above30_max_s=max(v['f50_above30_s'] for v in S3.values()), rc_peak_max_bar=max(v['rc_peak_bar'] for v in S3.values()),
               raw_peak_max_bar=max(v['raw_peak_bar'] for v in S3.values()))
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/late_light_tables_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='coordinator OI-A5-LATE: late-light spike at flight W 0.65 s and stand W 0.35 s (max, p99), A5 purpose and re-specification, MEOP margin',
               inputs={'late_light_spike_v2p4.json': sha16(spike_f), 'late_light_spike_v2p4.py (model imported unchanged)': sha16(os.path.join(HERE, 'late_light_spike_v2p4.py')),
                       'hard_start_v2p4.json': sha16(os.path.join(d, 'hard_start_v2p4.json')), 'hard_start_multivolume_v2p4.json': sha16(os.path.join(d, 'hard_start_multivolume_v2p4.json'))},
               windows=dict(flight_first_start_W_s=0.40, flight_relight_W_s=0.65, stand_R1_R2_W_s=0.35, latest_light_rule='t_L = W - 0.018 s (SIL light-to-E2 max)',
                            src='electronics.json firmware.W_build_constant (LEAD 2026-10-13)'),
               thresholds=dict(A5_Pa_abs=LL.A5_P, A7_START_hi_floor_Pa_abs=A7_HI, firmware_30bar_Pa_abs=LL.FW_ABS, filter_50Hz_tau_s=TAU50, comparator_RC_tau_s=LL.RC_TAU),
               note_percentiles='p50/p99 are taken over the equal-weight case grid of ASSUMED inputs (light time, tf, t_res, pool, entrance); they are not probabilities',
               T1_by_state_and_window=T1, T2_by_tf=T2, T3_latest_by_pool=T3, T4_SIL_light_times_20C_rounded=T4,
               S1_flight_first_start_W0p40_summary=S1s, S1_rows=S1, S2_pool_duration_vs_q_summary=S2s, S2_rows=S2, S3_filtered_spike_summary=S3s, S3_rows=S3,
               S4_pool_rates=S4,
               tags=dict(model='SIM (late_light_spike_v2p4 network) on ASSUMED inputs: an ESTIMATE, not acceptance evidence',
                         filter='first-order 50 Hz ASSUMED stand-in for the firmware filter; comparator RC 5.28 ms per Electronics v2.8/v2.9'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    # ---- print the tables used in the report and the message
    print('\nT1 flight W0.65 / stand W0.35 (both entrances)')
    for st in STATES:
        for sc in ('flight_W0.65', 'stand_W0.35'):
            v = T1[f'{sc}|{st}|both']
            print(sc, st, 'peak p50/p99/max %.1f/%.1f/%.1f' % (v['peak_head_bar']['p50'], v['peak_head_bar']['p99'], v['peak_head_bar']['max']),
                  '| >8 p50/p99/max %.3f/%.3f/%.3f' % (v['above8_cont_s']['p50'], v['above8_cont_s']['p99'], v['above8_cont_s']['max']),
                  '| >30 max %.4f' % v['above30_cont_s_max'], '| RC pk %.1f' % v['comparator_RC_peak_abs_bar_max'], '| A5 %.3f A5<E2 %.3f' % (v['A5_trip_fraction'], v['A5_before_E2_fraction']),
                  '| tA5', [round(x * 1e3, 1) for x in v['t_A5_after_light_s']], 'tE2', [round(x * 1e3, 1) for x in v['t_E2_after_light_raw_s']], '| inv', [round(x, 1) for x in v['inventory_g']])
        for ent in ('rounded', 'sharp'):
            v = T1[f'flight_W0.65|{st}|{ent}']
            print('   ', ent, 'peak p99/max %.1f/%.1f' % (v['peak_head_bar']['p99'], v['peak_head_bar']['max']))
    print('\nT2 peak by tf (max over the rest)')
    for k, v in T2.items():
        print(k, 'peak %.1f-%.1f' % (v['peak_min_bar'], v['peak_max_bar']), '>30 %.4f' % v['above30_max_s'], 'A5 %.3f' % v['A5_trip_fraction'], '>8 no-pool max %.4f' % v['above8_no_pool_max_s'])
    print('\nT3 latest lights by pool')
    for k, v in T3.items():
        print(k, '>8 %.3f' % v['above8_max_s'], 'pool %.1f g' % v['m_pool_g'], 'tau %.3f' % v['tau_pool_s'], 'peak %.1f' % v['peak_max_bar'])
    print('\nT4 SIL light times', json.dumps(T4))
    print('\nS1 flight first start W 0.40', json.dumps({k: dict(peak_max=v['peak_head_bar']['max'], peak_p99=v['peak_head_bar']['p99'], a8_max=v['above8_cont_s']['max'], a8_p99=v['above8_cont_s']['p99'], inv=v['inventory_g'], A5=v['A5_trip_fraction']) for k, v in S1s.items()}))
    print('\nS2 pool duration vs q'); [print(k, json.dumps(v)) for k, v in S2s.items()]
    print('\nS3 filtered spike', json.dumps(S3s))
    print('\nS4 rates', json.dumps(S4))
    print('wrote', out_f, sha16(out_f), round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main(*sys.argv[1:4])
