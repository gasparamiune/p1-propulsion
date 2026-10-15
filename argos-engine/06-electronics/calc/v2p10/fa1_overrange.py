#!/usr/bin/env python3
"""LEAD CHANGELOG 194 (7) / coordinator relay: 070BG over-range at the FA-1 relight peaks (Electronics, 2026-10-13, firmware v2.10).

Two steps around the C++ harness calc/v2p10/fa1_overrange_chain.cpp:
  extract   : read Combustion's FA-1 envelope (02-combustion/data/v2p4a/fa1_envelope_v2p4a.json, read-only), write the 896 head and aft
              pressure histories (bar abs, 0.1 ms grid, 0-25 ms from the light) as one line per case for the harness. Each value is
              clipped below at P0 = state.P0_cold_flow_Pa (the vapour_once first sample 0.054 bar is the construct's initial gas x 0.05,
              not a chamber pressure). The tail after 25 ms is P_at_25ms held (ASSUMED; higher than the solver's P_end 3.7-4.5 bar, so
              it can only raise the over-pressure checks; P_at_25ms <= 22.1 bar < 30 bar, so the hold alone trips nothing).
  summarize : join the harness CSV with the case keys and metrics, write results/fa1_overrange_v2p10.json.
Tags: the histories are COMB SIM (lumped three-node construct, inputs ASSUMED); the chain is the SIL chain (sense line, transducer lag,
ADC averaging, ECU filter and persistence, comparator RC, all as in firmware/sil); the transducer output above full scale is MISSING
from the datasheet, so the saturation level is a swept parameter. SIM; not hardware; not a physical validation.
"""
import argparse, collections, csv, datetime, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RES = os.path.join(ROOT, 'results')
ENGINE = '/home/claude/work/shared-fallback/engine'
FA1 = os.path.join(ENGINE, '02-combustion', 'data', 'v2p4a', 'fa1_envelope_v2p4a.json')
FS_BAR_G, PAMB_BAR = 70.0, 1.01325          # [DATASHEET] 070BG 0-70 bar g; [ASSUMED] sea-level ambient (the transducer is gauge)
V_HI = 4.75                                  # [DESIGN] cfg::kPcSensorMax_V


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def v_of_bar_abs(p):
    return 0.5 + 4.0 * (p - PAMB_BAR) / FS_BAR_G


def extract(a):
    d = json.load(open(a.fa1))
    p0 = d['state']['P0_cold_flow_Pa'] / 1e5
    grid = d['history_grid_ms']
    assert len(grid) == 251 and abs(grid[1] - 0.1) < 1e-9 and abs(grid[-1] - 25.0) < 1e-9, 'history grid changed'
    os.makedirs(a.out, exist_ok=True)
    idx, n_clip = [], 0
    with open(os.path.join(a.out, 'hist_head.txt'), 'w') as fh, open(os.path.join(a.out, 'hist_aft.txt'), 'w') as fa:
        for i, (k, c) in enumerate(d['cases'].items()):
            for f, key in ((fh, 'P_head_hist_bar'), (fa, 'P_aft_hist_bar')):
                h = c[key]
                n_clip += sum(1 for v in h if v < p0)
                f.write('%d %s\n' % (i, ' '.join('%.5f' % max(v, p0) for v in h)))
            idx.append({'i': i, 'key': k, 'family': k.split('|')[0], 'peak_head_bar': c['peak_head_bar'], 'peak_aft_bar': c['peak_aft_bar'],
                        't_peak_head_ms': c['t_peak_head_ms'], 'above67p5_head_total_ms': c['above67p5_head_total_ms'],
                        'above67p5_aft_total_ms': c['above67p5_aft_total_ms'], 'P_at_25ms_head_bar': c['P_at_25ms_head_bar'],
                        'P_at_25ms_aft_bar': c['P_at_25ms_aft_bar'], 'P_end_bar': c['P_end_bar'], 't_end_ms': c['t_end_ms']})
    meta = {'source': os.path.relpath(a.fa1, ENGINE), 'source_sha256_16': sha16(a.fa1), 'source_version': d.get('version'),
            'P0_cold_flow_bar_abs': p0, 'n_cases': len(idx), 'samples_clipped_to_P0': n_clip, 'cases': idx}
    json.dump(meta, open(os.path.join(a.out, 'index.json'), 'w'), indent=0)
    print('cases', len(idx), 'P0 %.4f bar abs' % p0, 'samples clipped to P0', n_clip, 'source', meta['source_sha256_16'])


def summarize(a):
    meta = json.load(open(os.path.join(a.work, 'index.json')))
    cases = {c['i']: c for c in meta['cases']}
    rows = list(csv.DictReader(open(a.csv)))
    num = lambda r, k: float(r[k])
    by_cfg = collections.OrderedDict()
    for r in rows:
        by_cfg.setdefault((r['node'], r['line'], r['tau_x_ms'], r['vsat']), []).append(r)
    out = collections.OrderedDict()
    out['id'] = 'fa1_overrange_v2p10'
    out['version'] = 'v1'
    out['date'] = datetime.date.today().isoformat()
    out['owner'] = 'electronics'
    out['firmware'] = 'v2.10'
    out['request'] = ('LEAD CHANGELOG 194 (7) and the coordinator relay of line 194: 070BG over-range behaviour at the FA-1 relight '
                      'peaks and its effect on the 30 bar abort, the comparator, the Pc-valid flag and the logged FA-1 peak')
    out['tags'] = ('SIM (SIL chain on COMB SIM histories; inputs ASSUMED where marked). The transducer output above full scale is '
                   'MISSING from the datasheet: v_sat is swept, not known. Not hardware, not a physical validation.')
    out['inputs'] = {'fa1_envelope': {'file': meta['source'], 'sha256_16': meta['source_sha256_16'], 'version': meta['source_version'],
                                      'tag': 'COMB SIM'},
                     'P0_cold_flow_bar_abs': meta['P0_cold_flow_bar_abs'], 'samples_clipped_to_P0': meta['samples_clipped_to_P0'],
                     'harness_csv': {'file': os.path.relpath(a.csv, ROOT), 'sha256_16': sha16(a.csv), 'rows': len(rows)}}
    out['chain'] = collections.OrderedDict([
        ('pressure_node', 'head (the Pc tap is at the head top, SenseLineParams comment; aft run as a sensitivity)'),
        ('pre_light', '50 ms at P0 (cold flow at the start lift), filter settled on P0'),
        ('tail', 'P_at_25ms held to 100 ms after the light [ASSUMED; conservative for over-pressure]'),
        ('sense_line', 'sil::SenseLine defaults: L 0.30 m, ID 1.59 mm PTFE, V_end 0.5 cm3, T 350 K, n 1.15, N 16 [ASSUMED]; "off" = head '
                       'pressure at the transducer'),
        ('transducer', 'first-order lag tau_x 0.9 ms (SIL pc_tau: 10-90 % rise 2.0 ms = the DATASHEET bound < 2 ms, i.e. the slowest '
                       'response the datasheet allows) or 0.1 ms (faster unit; sensitivity); output 0.5 + 4 p_g/70 bar g, limited at v_sat'),
        ('v_sat_V', {'4.95': 'SIL value [ASSUMED]', '4.74': 'just below the 4.75 V over-range check: silent clip at 74.2 bar g',
                     '4.50': 'clip at full scale (70 bar g): silent', 'none': 'reference only, not physical for a 5 V ratiometric '
                     'transducer: the true pressure through the same chain with no transducer or ADC limit'}),
        ('adc', 'ADS131M04 4 kSPS samples (instantaneous; the sinc3 response is not modelled), PC_SIG range to 4.99 V [DERIVED: 1.2 V FS / '
                '0.2404 divider 12.7k/4.02k; 5.04 V with the 330 kOhm input], 4:1 average to the 1 kHz reading, worst of 4 phases. The limit '
                'is applied to each sample (transducer output, then ADC); sil/sim.cpp limits the 1 kHz average at 4.95 V instead, which '
                'over-reads above full scale (no effect below it)'),
        ('firmware', 'cfg::kPcSensorMax_V 4.75 V (IGNITION: HARD_START on that tick; any state: fault::PC_SENSOR, sticky until '
                     'DISARM in SAFE; PC_VALID = 0); LowPass2 50 Hz + Persist cfg::kPcOverPressureTime_s 5 ms on the FILTERED channel '
                     'at 30 bar abs; E2 by the relative rule (rise >= 0.8 bar filtered AND raw, floor 1.8 bar abs, 10 ticks)'),
        ('comparator', 'PC_SIG -> RC 5.283 ms -> trip 2.298 V (31.47 bar g, nominal) / 2.208 V (low band edge); U331 latch forces the '
                       'ARM bus off'),
        ('configurations', 'head with the sense line (tau_x 0.9 ms); head without the line (tau_x 0.9 and 0.1 ms); aft with the line '
                           '(tap-location sensitivity); each with v_sat 4.95 / 4.74 / 4.50 / none'),
        ('sensitivities_not_proposals', 'comparator RC 10 and 20 ms at the low band edge; filtered persistence 10 and 15 ms'),
        ('counts', 'counts are over Combustion\'s parametric grid (O/F, fuel time, residence, pool, entrance, initial gas); they are '
                   'not probabilities'),
    ])
    summ = []
    for (node, line, taux, vsat), rr in by_cfg.items():
        for fam in ('vapour_once', 'as_written', 'all'):
            sel = [r for r in rr if fam == 'all' or cases[int(r['case'])]['family'] == fam]
            if not sel:
                continue
            n = len(sel)
            cnt = lambda k: sum(1 for r in sel if r[k] == '1')
            worst = lambda k: max(sel, key=lambda r: num(r, k))
            w_x, w_raw, w_f, w_c = worst('port_pk_bar'), worst('raw_pk_bar'), worst('filt_pk_bar'), worst('cmp_vmax')
            ign = [r for r in sel if r['n475_ign'] != '0']
            def first_src(r):
                ts = [(num(r, 't475_ms'), 'over-range 4.75 V (IGNITION HARD_START)') if r['n475_ign'] != '0' else None,
                      (num(r, 't_cmp_ms'), 'hardware comparator (nominal; ARM bus off)') if r['cmp_nom'] == '1' else None,
                      (num(r, 't_fw30_ms'), 'firmware filtered 30 bar / 5 ms (HARD_START)') if r['fw30'] == '1' else None]
                ts = [x for x in ts if x]
                return min(ts)[1] if ts else 'none'
            fs_cnt = collections.Counter(first_src(r) for r in sel)
            e2 = [num(r, 'tE2_ms') for r in sel if num(r, 'tE2_ms') >= 0]
            summ.append(collections.OrderedDict([
                ('node', node), ('sense_line', line), ('tau_x_ms', taux), ('v_sat_V', vsat), ('family', fam), ('n_cases', n),
                ('cases_any_abort_path_nominal', sum(1 for r in sel if r['n475_ign'] != '0' or r['fw30'] == '1' or r['cmp_nom'] == '1')),
                ('cases_any_abort_path_low_band', sum(1 for r in sel if r['n475_ign'] != '0' or r['fw30'] == '1' or r['cmp_lo'] == '1')),
                ('first_abort_path_counts', dict(fs_cnt)),
                ('E2_ms_from_light_range', [min(e2), max(e2)] if e2 else None),
                ('port_peak_bar_abs_max', round(num(w_x, 'port_pk_bar'), 2), ), ('port_peak_case', cases[int(w_x['case'])]['key']),
                ('cases_port_at_line_model_floor', sum(1 for r in sel if num(r, 'port_min_bar') < 0.05)),
                ('port_peak_vs_proof', 'proof 140 bar g = %.1f bar abs [DATASHEET 2x rated]; max at the transducer port %.1f bar abs' % (2 * FS_BAR_G + PAMB_BAR, num(w_x, 'port_pk_bar'))),
                ('cases_reading_ge_4p75V', cnt('hi475')),
                ('cases_reading_ge_4p75V_before_E2', len(ign)),
                ('first_reading_ge_4p75V_ms_from_light_min', round(min(num(r, 't475_ms') for r in ign), 2) if ign else None),
                ('cases_E2_before_first_overrange', sum(1 for r in sel if r['hi475'] == '1' and r['n475_ign'] == '0')),
                ('logged_raw_peak_bar_abs_max', round(num(w_raw, 'raw_pk_bar'), 2)),
                ('logged_raw_peak_case_true_head_peak_bar', round(cases[int(w_raw['case'])]['peak_head_bar'], 2)),
                ('cases_logged_without_overrange_flag_above_67p5', sum(1 for r in sel if r['hi475'] == '0' and num(r, 'raw_pk_bar') > 67.5)),
                ('cases_logged_at_or_above_full_scale_without_flag', sum(1 for r in sel if r['hi475'] == '0' and num(r, 'raw_pk_bar') >= FS_BAR_G + PAMB_BAR - 0.01)),
                ('filt_peak_bar_abs_max', round(num(w_f, 'filt_pk_bar'), 2)),
                ('filt_t_above_30_ms_max', max(num(r, 't30f_ms') for r in sel)),
                ('cases_fw_30bar_5ms_trip', cnt('fw30')),
                ('comparator_rc_V_max', round(num(w_c, 'cmp_vmax'), 3)),
                ('cases_comparator_trip_nominal', cnt('cmp_nom')),
                ('cases_comparator_trip_low_band', cnt('cmp_lo')),
                ('cases_no_E2', sum(1 for r in sel if num(r, 'tE2_ms') < 0)),
                ('sens_comparator_trip_low_band_rc10ms', cnt('cmp_lo_t10')), ('sens_comparator_trip_low_band_rc20ms', cnt('cmp_lo_t20')),
                ('sens_fw_30bar_trip_persist10ms', cnt('fw30_p10')), ('sens_fw_30bar_trip_persist15ms', cnt('fw30_p15')),
            ]))
    out['summary'] = summ
    # per-case table for the baseline chain (head, line on, v_sat 4.95) for the cases that matter (head peak > 45 bar)
    base = [r for r in rows if r['node'] == 'head' and r['line'] == 'off' and r['tau_x_ms'] == '0.9' and r['vsat'] == '4.95']
    keep = sorted((r for r in base if cases[int(r['case'])]['peak_head_bar'] > 67.5), key=lambda r: -cases[int(r['case'])]['peak_head_bar'])
    out['table_note'] = ('cases with a head peak above 67.5 bar abs; chain: head, NO sense line, tau_x 0.9 ms, v_sat 4.95 V (the line-on '
                         'results are a sensitivity: the linear line model swings to its 1 kPa floor on these inputs)')
    out['cases_head_peak_above_67p5_no_line'] = [collections.OrderedDict([
        ('key', cases[int(r['case'])]['key']), ('head_peak_bar', round(cases[int(r['case'])]['peak_head_bar'], 2)),
        ('above67p5_head_ms', cases[int(r['case'])]['above67p5_head_total_ms']), ('port_peak_bar', round(num(r, 'port_pk_bar'), 2)),
        ('vmax_V', round(num(r, 'vmax_V'), 3)), ('reading_ge_4p75V', r['hi475'] == '1'), ('t_first_ge_4p75V_ms', round(num(r, 't475_ms'), 2)),
        ('tE2_ms', round(num(r, 'tE2_ms'), 1)), ('logged_raw_peak_bar', round(num(r, 'raw_pk_bar'), 2)), ('filt_peak_bar', round(num(r, 'filt_pk_bar'), 2)),
        ('fw_30bar_trip', r['fw30'] == '1'), ('comparator_V_max', round(num(r, 'cmp_vmax'), 3)), ('comparator_trip_nominal', r['cmp_nom'] == '1'),
        ('comparator_trip_low_band', r['cmp_lo'] == '1')]) for r in keep]
    json.dump(out, open(a.json_out, 'w'), indent=1)
    for s in summ:
        if s['family'] != 'all':
            continue
        print('%-4s line %-3s tau %s vsat %-4s | any %3d/%3d | port max %6.2f | >=4.75V %3d (before E2 %3d, first %s ms) | logged max %6.2f | no-flag >67.5: %3d | '
              'filt max %6.2f t30 %4.1f ms | fw30 %3d | cmp Vmax %.3f nom %3d low %3d | noE2 %d' % (
                  s['node'], s['sense_line'], s['tau_x_ms'], s['v_sat_V'], s['cases_any_abort_path_nominal'], s['cases_any_abort_path_low_band'],
                  s['port_peak_bar_abs_max'], s['cases_reading_ge_4p75V'],
                  s['cases_reading_ge_4p75V_before_E2'], s['first_reading_ge_4p75V_ms_from_light_min'], s['logged_raw_peak_bar_abs_max'],
                  s['cases_logged_without_overrange_flag_above_67p5'], s['filt_peak_bar_abs_max'], s['filt_t_above_30_ms_max'],
                  s['cases_fw_30bar_5ms_trip'], s['comparator_rc_V_max'], s['cases_comparator_trip_nominal'], s['cases_comparator_trip_low_band'],
                  s['cases_no_E2']))
        print('      floor hits', s['cases_port_at_line_model_floor'], '| first path', s['first_abort_path_counts'], '| E2', s['E2_ms_from_light_range'], '| sens cmp-lo RC10/20 %d/%d, fw p10/p15 %d/%d' % (
            s['sens_comparator_trip_low_band_rc10ms'], s['sens_comparator_trip_low_band_rc20ms'], s['sens_fw_30bar_trip_persist10ms'],
            s['sens_fw_30bar_trip_persist15ms']))
    print('->', a.json_out, sha16(a.json_out))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    e = sp.add_parser('extract'); e.add_argument('--fa1', default=FA1); e.add_argument('--out', required=True)
    s = sp.add_parser('summarize'); s.add_argument('--work', required=True); s.add_argument('--csv', required=True)
    s.add_argument('--json-out', default=os.path.join(RES, 'fa1_overrange_v2p10.json'))
    a = ap.parse_args()
    extract(a) if a.cmd == 'extract' else summarize(a)


if __name__ == '__main__':
    main()
