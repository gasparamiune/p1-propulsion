"""R2 hold lift and the lit side for GNC P4c and the pcf_tmax proposal (Combustion v2.4b final, 2026-10-19; LEAD CHANGELOG lines
194 (4), 203 (7), 216 (9), 227 (5)-(6); lead request 2026-10-19 item 3).

Line 216 (9): the ECU R2 hold becomes a lift-commanded hold at Combustion v2.4b's start-level lift, and CF-3 measures at that lift
with the encoder recorded.  Line 227 (5): the R2 window is 0.8 s for the W10 < 6 m/s envelope.  GNC rev3/rev4: P4c (the lit side)
waits for the v2.4b lit history.  This script publishes, from the stored grain_q1d runs (no re-run):
  (1) THE start-level lift at the A1 relight state as a lift value, with the rule and the ECU table rows around it;
  (2) the lit thrust at that lift from E2 (per corner, torch 0 and 0.3 s) in the 0.5 s and 0.8 s windows: minima, the corners that
      never reach a threshold, the latest first crossing, for thresholds 25 / 30 / 33 / 35 / 37.16 N, and the same at 0.2039 mm
      (the 20 C row, low-lift sensitivity);
  (3) the flame-out side at the lift: the DERIVED adiabatic cold-flow bound by tank state (CONDITIONAL on Cd x A x G, CF-3);
  (4) what the lit side implies for pcf_tmax and for the threshold (data for GNC and the lead; no value is set here);
  (5) pointers (file, sha16) to the per-corner histories and to the per-record release-hold classes (incl. the 500 N profile).
Tags: lit histories SIM (grain_q1d v2 on ASSUMED laws and bands; quasi-steady; eta_cf 0.975 and Schmucker separation ASSUMED; zero
thrust below 1.3 atm chamber pressure); ECU table DESIGN (Electronics config.h, read only); cold-flow bound DERIVED; nothing measured.
usage: python -I p4c_lit_side_v2p4b.py DATA_V2P4B_DIR OUT_JSON
"""
from __future__ import annotations
import csv, hashlib, json, os, sys
import numpy as np

EXPECT = {'start_level_lit_thrust_v2p4b.json': 'ae2038c5141b7f73', 'start_level_lit_thrust_v2p4b.csv': 'f6ac2a4da04f8d45',
          'start_level_lit_thrust_0p21776mm_v2p4b.json': '10cdc03154b95216', 'start_level_lit_thrust_0p21776mm_v2p4b.csv': 'c073d4f993f8c412',
          'a1_profile_line213_v2p4b.json': '46b6a1c6efec0351', 'cold_flow_start_lift_v2p4b.json': '28ce48092f33da1b',
          'lead_items_203_205_v2p4b.json': 'e20a8b8c33af9162', 'release_hold_v2p4b.json': 'a926426da0e6e436',
          'release_hold_records_v2p4b.csv': '59e7f44e44fbfeef'}
THRESHOLDS = (25.0, 30.0, 33.0, 35.0, 37.16)
WINDOWS = (0.5, 0.8)
FRAMES_3_S = 0.03            # 3 consecutive 100 Hz frames (R2 confirmation; gnc.json v3.1)


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def r(x, n=3):
    return None if x is None else round(float(x), n)


def lit_stats(J, csv_f):
    rows = list(csv.reader(open(csv_f)))
    hdr = rows[0]; data = np.array([[float(x) if x not in ('', 'nan') else np.nan for x in row[:4] + row[5:]] for row in rows[1:]])
    t = data[:, 0]; cols = [h for h in hdr[5:]]; F = data[:, 4:]
    assert len(cols) == 72 and F.shape[1] == 72
    out = {}
    for torch in ('torch0.0', 'torch0.3'):
        per = []
        for jc, c in enumerate(J['corners']):
            assert cols[jc] == 'F_N|' + c['corner'], (cols[jc], c['corner'])
            e2 = c[torch]['E2_s']
            per.append((c['corner'], e2, F[:, jc]))
        res = {}
        for w in WINDOWS:
            mins, maxs, means = [], [], []
            first = {thr: [] for thr in THRESHOLDS}
            for name, e2, f in per:
                m = (t >= e2 - 1e-12) & (t <= e2 + w + 1e-12)
                assert t[m][-1] >= e2 + w - 1e-9, ('window beyond the stored history', name, w)
                fw = f[m]; tw = t[m] - e2
                mins.append(fw.min()); maxs.append(fw.max()); means.append(fw.mean())
                for thr in THRESHOLDS:
                    k = np.nonzero(fw >= thr)[0]
                    first[thr].append(max(0.0, float(tw[k[0]])) if k.size else None)
            thr_tab = {}
            for thr in THRESHOLDS:
                fc = [x for x in first[thr] if x is not None]
                thr_tab['%.2f N' % thr] = dict(n_corners_never=int(sum(1 for x in first[thr] if x is None)), n_corners=72,
                                               latest_first_crossing_after_E2_s=r(max(fc), 4) if fc else None,
                                               latest_plus_3_frames_s=r(max(fc) + FRAMES_3_S, 4) if fc else None)
            worst = int(np.argmin(mins))
            res['window_%.1fs' % w] = dict(F_min_over_corners_N=r(min(mins), 2), F_window_max_of_worst_corner_N=r(maxs[worst], 2),
                                           worst_corner=per[worst][0], F_mean_min_p05_p50_N=[r(np.min(means), 2), r(np.percentile(means, 5), 2),
                                                                                            r(np.median(means), 2)],
                                           thresholds=thr_tab)
        res['E2_s_range'] = [r(min(p[1] for p in per), 4), r(max(p[1] for p in per), 4)]
        out[torch] = res
    never = [c['corner'] for c in J['corners'] if all(x < 37.16 for x in c['F_N'].values())]
    out['corners_below_37p16N_at_every_stored_time_to_1s'] = never
    out['F_at_1s_range_N'] = [r(x, 2) for x in J['summary']['F_at_1s_range_N']]
    return out


def main(d, out_f):
    for f, h in EXPECT.items():
        assert sha16(os.path.join(d, f)) == h, (f, sha16(os.path.join(d, f)))
    A1 = json.load(open(os.path.join(d, 'a1_profile_line213_v2p4b.json')))
    CF = json.load(open(os.path.join(d, 'cold_flow_start_lift_v2p4b.json')))
    LI = json.load(open(os.path.join(d, 'lead_items_203_205_v2p4b.json')))['item2_start_level_lift']
    RH = json.load(open(os.path.join(d, 'release_hold_v2p4b.json')))
    J1 = json.load(open(os.path.join(d, 'start_level_lit_thrust_0p21776mm_v2p4b.json')))
    J0 = json.load(open(os.path.join(d, 'start_level_lit_thrust_v2p4b.json')))
    tab = LI['ecu_table']
    T_A1 = 286.70
    h_A1 = tab['lift_mm'][tab['T_K'].index(T_A1)]
    assert abs(h_A1 - 0.21776) < 1e-9 and abs(J1['lift_mm'] - h_A1) < 1e-9
    lit1 = lit_stats(J1, os.path.join(d, 'start_level_lit_thrust_0p21776mm_v2p4b.csv'))
    lit0 = lit_stats(J0, os.path.join(d, 'start_level_lit_thrust_v2p4b.csv'))
    fo = {k: dict(T_K=v['T_K'], P_sat_bar=r(v['P_sat_bar'], 2), h_s_ECU_mm=v['h_s_ECU_mm'], F_cold_bound_at_h_s_N=r(v['F_bound_h_s_N'], 2),
                  F_cold_bound_with_SPI_flux_N=None)
          for k, v in A1['states'].items()}
    for k, v in CF['states'].items():
        kk = '%.2fK' % v['T_K']
        if kk in fo:
            fo[kk]['F_cold_bound_with_SPI_flux_N'] = r(v['F_bound_with_SPI_flux_N'] * fo[kk]['F_cold_bound_at_h_s_N'] / v['F_bound_N'], 2)
    w8 = lit1['torch0.0']['window_0.8s']; w5 = lit1['torch0.0']['window_0.5s']
    thr = w8['thresholds']['37.16 N']
    out = dict(
        version='v2.4b', date='2026-10-19', script='02-combustion/src/p4c_lit_side_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
        request=('LEAD CHANGELOG 216 (9): THE start-level lift as a LIFT value at the A1 relight state (ECU R2 lift-commanded hold; CF-3); '
                 'lead request 2026-10-19 item 3: what GNC needs for P4c and the pcf_tmax proposal, as data with tags'),
        inputs={f: sha16(os.path.join(d, f)) for f in EXPECT},
        start_level_lift=dict(
            value_mm=h_A1, state='A1 relight state of record: 286.70 K, P_sat 43.53 bar, port 32.2 mm, 1.16 kg (start_latency_v2p4 STATES)',
            tag='DESIGN (ECU table row, Electronics config.h kIgnLiftTab_m, read only); DERIVED cross-check: Combustion injector model 0.21788 mm '
                '(-0.056 %); TO-VERIFY at CF-3 (encoder lift, mdot, load cell)',
            rule='the R2 hold commands h_s(T_tank at E0), the same ECU ignition-lift row the ECU commands at E1 and holds to E2; no thrust-map '
                 'lookup in the hold (Pc invalid); at the A1 relight state of record h_s = %.5f mm' % h_A1,
            ecu_rows_near=[dict(T_K=T, lift_mm=h) for T, h in zip(tab['T_K'], tab['lift_mm']) if 280.0 <= T <= 298.2],
            pad_20C=dict(ecu_row_293p15K_mm=tab['lift_mm'][tab['T_K'].index(293.15)], at_37p1_g_s_cap_mm=0.2039,
                         note='the ECU rows hold 37.4 g/s at every temperature; at 20 C the 37.1 g/s cap gives 0.2039 mm (Electronics cuts the '
                              'warm rows to the cap; CF-3 confirms)'),
            at_210m='the 210 m relight state is MISSING (GNC 210 m duty-cycle record not flown; OI-49); a warmer state reads a lower row '
                    '(0.2148 mm at 288.15 K, 0.2100 mm at 290.65 K); the rule, not the number, is what the ECU implements',
            cf3_points=['%.5f mm (A1 relight row), encoder recorded, at the test tank state with P_tank and T_tank logged' % h_A1,
                        'h_s at the CF-3 tank temperature (the row the ECU would command on that day)', '0.2039 mm (20 C cap value)',
                        'acceptance per cold_flow_start_lift_v2p4b (F <= 16.31 N - heat allowance, or mdot <= 16.31 N / v)']),
        lit_side=dict(
            lift_0p21776mm=lit1, lift_0p2039mm_sensitivity=lit0,
            time_origin='E2 per corner (the corner E2 of start_level_lit_thrust_*; torch 0 and 0.3 s cases); GNC aligns its E2 with it',
            statistic='raw engine thrust F(t) from grain_q1d (not the accelerometer estimate); GNC applies its R2 estimator, filter, frame '
                      'noise and drogue terms',
            files=dict(lift_0p21776mm=dict(csv='start_level_lit_thrust_0p21776mm_v2p4b.csv', sha256_16=EXPECT['start_level_lit_thrust_0p21776mm_v2p4b.csv'],
                                           json='start_level_lit_thrust_0p21776mm_v2p4b.json', sha256_16_json=EXPECT['start_level_lit_thrust_0p21776mm_v2p4b.json'],
                                           columns='t from the light (0-1.0 s, 0.5 ms); min / median / max over 72 corners; one column per corner (N)'),
                       lift_0p2039mm=dict(csv='start_level_lit_thrust_v2p4b.csv', sha256_16=EXPECT['start_level_lit_thrust_v2p4b.csv'])),
            gnc_model_withdrawn='62.5 N x pcf_k 0.875 = 54.7 N (withdrawn by line 194 (2)); the published median is 45-55 N and the minimum 33-36 N'),
        flame_out_side=dict(
            by_state=fo, tag='DERIVED adiabatic isentropic-equilibrium bound, Cd 0.80 limit ASSUMED; CONDITIONAL on Cd x A x G at the start lift '
                             '(CF-3); SPI-flux column = the non-equilibrium sensitivity',
            note='raw engine force of a dead engine at the hold lift; GNC adds drogue drag, baseline and estimator terms (its fo_cb arms)'),
        implications=dict(
            pcf_tmax=('lit side at 0.21776 mm, torch 0: every corner that reaches 37.16 N does so by E2 + %.3f s (+ 3 frames: %.3f s), inside both '
                      'windows; %d of 72 corners never reach 37.16 N in the 0.8 s window (%d in 0.5 s): a longer window does not rescue them '
                      '(F at 1 s >= %.2f N), so pcf_tmax 0.8 s (line 227 (5)) is not limited by the lit side'
                      % (thr['latest_first_crossing_after_E2_s'], thr['latest_plus_3_frames_s'], thr['n_corners_never'],
                         w5['thresholds']['37.16 N']['n_corners_never'], lit1['F_at_1s_range_N'][0])),
            threshold=('the lit minimum in the 0.8 s window is %.2f N at 0.21776 mm (worst corner %s) against the 37.16 N threshold; the '
                       'raw dead-engine bound is <= %.2f N at the A1 state and %.2f N at the 297.15 K ARM limit; GNC states its fo / lit statistics '
                       'on the R2 estimate; raising the lift to lift the low corners conflicts with the 37.1 / 37.4 g/s start-flow caps (hard start, '
                       'line 194); threshold and window are GNC / lead decisions'
                       % (w8['F_min_over_corners_N'], w8['worst_corner'], fo['286.70K']['F_cold_bound_at_h_s_N'], fo['297.15K']['F_cold_bound_at_h_s_N'])),
            what_gnc_needs=['the per-corner lit histories at 0.21776 mm (A1 state) and 0.2039 mm', 'E2 per corner', 'the cold-flow bound at the '
                            'hold lift by tank state', 'the per-record release-hold classes incl. the 500 N profile (release_hold_records_v2p4b.csv)',
                            'the start-level lift rule h_s(T_tank at E0)']),
        release_hold_classes=dict(file='release_hold_records_v2p4b.csv', sha256_16=EXPECT['release_hold_records_v2p4b.csv'],
                                  summary_json='release_hold_v2p4b.json', sha256_16_json=EXPECT['release_hold_v2p4b.json'],
                                  status='unpurged-start alternative NOT ADOPTED (lines 204 (2), 208 (3)); data kept for GNC',
                                  profiles=RH['constants']['profiles']),
        missing=['the lit history at the 210 m relight state (state MISSING, OI-49)', 'measured start-level thrust (IGN-1, T series with load cell)',
                 'Cd x A x G at the start lift (CF-3)', 'the R2 estimator noise and drogue terms (GNC / Electronics)'],
        tags=dict(lit='SIM grain_q1d v2 on ASSUMED laws and bands', lift='DESIGN (ECU table) / DERIVED cross-check', flame_out='DERIVED bound, CONDITIONAL',
                  status='not physical evidence; nothing here is physical approval'))
    json.dump(out, open(out_f, 'w'), indent=1)
    for lab, L in (('0.21776', lit1), ('0.2039', lit0)):
        for torch in ('torch0.0', 'torch0.3'):
            for w in ('window_0.5s', 'window_0.8s'):
                x = L[torch][w]
                print(lab, torch, w, 'Fmin', x['F_min_over_corners_N'], 'worst', x['worst_corner'],
                      {k: (v['n_corners_never'], v['latest_first_crossing_after_E2_s']) for k, v in x['thresholds'].items()})
    print('implications', out['implications']['pcf_tmax'])
    print(out['implications']['threshold'])
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])
