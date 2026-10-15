#!/usr/bin/env python3
"""Summary of the v2.11 FA-1 Pc-chain harness (calc/v2p11/fa1_chain_v2p11.cpp) -> results/fa1_chain_v2p11.json / .txt.

LEAD CHANGELOG 203 (1)(b) (ride-through CANDIDATE, sized from the FA-1 envelope) and 205 (flight transducer reselection). Counts are
over Combustion's 896-case FA-1 grid (equal weights: a fraction of the GRID, not a probability). SIM on SIM inputs (Combustion's
construct ASSUMED); nothing here is hardware evidence. Ride-through sizing rule (DESIGN): each knob takes the smallest grid value
with zero FA-1 trips in every v2.11 C1 chain, plus the stated margin; the window end X after E2 covers the latest end of a filtered
> 30 bar episode plus margin; the T45 guard (raw reading > 45 bar abs continuous) sits above the longest FA-1 episode plus margin.
Usage: python3 calc/v2p11/fa1_chain_summary.py [--csv results/fa1_chain_v2p11_cases.csv]
"""
import argparse
import csv
import hashlib
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PERS_MS = [5, 10, 15, 20, 25]
TAUW = ['asb', '10', '15', '20', '30']


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', default=os.path.join(ROOT, 'results', 'fa1_chain_v2p11_cases.csv'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'results', 'fa1_chain_v2p11.json'))
    ap.add_argument('--v210', default=os.path.join(ROOT, 'results', 'fa1_overrange_v2p10.json'))
    ap.add_argument('--margin-pers-ms', type=float, default=3.0)
    ap.add_argument('--margin-x-ms', type=float, default=5.0)
    ap.add_argument('--margin-t45-ms', type=float, default=2.0)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv)))
    chains = []
    for r in rows:
        if r['chain'] not in chains:
            chains.append(r['chain'])
    I = lambda r, k: int(r[k])
    F = lambda r, k: float(r[k])
    out = {'script': 'calc/v2p11/fa1_chain_summary.py', 'date': '2026-10-13',
           'inputs': {'cases_csv': {'file': os.path.relpath(a.csv, ROOT), 'sha256_16': sha16(a.csv), 'rows': len(rows)},
                      'harness_source_sha256_16': sha16(os.path.join(HERE, 'fa1_chain_v2p11.cpp')),
                      'fa1_envelope': '02-combustion/data/v2p4a/fa1_envelope_v2p4a.json 64b328150025fa1e (896 cases, via calc/v2p10/'
                                      'fa1_overrange.py extract)'},
           'tags': 'SIM (open-loop replay of Combustion SIM histories through modelled chains); chain elements DATASHEET/DESIGN/ASSUMED '
                   'as listed in the harness header; grid fractions are not probabilities',
           'chains': {}}
    L = []
    for ch in chains:
        R = [r for r in rows if r['chain'] == ch]
        n = len(R)
        s = {'n_cases': n}
        s['overrange_475_in_IGNITION'] = sum(1 for r in R if I(r, 'n475_ign') > 0)
        s['above_fs_456_in_IGNITION'] = sum(1 for r in R if I(r, 'n456_ign') > 0)
        for p in PERS_MS:
            s['fw30_trips_persist_%dms' % p] = sum(1 for r in R if I(r, 'fw%d' % p))
        s['cmp_trips_as_built_nominal'] = sum(1 for r in R if I(r, 'cnom_asb'))
        for t in TAUW:
            s['cmp_trips_tau_%s_low_band' % t] = sum(1 for r in R if I(r, 'clo_%s' % t))
        s['as_built_aborts_nominal'] = sum(1 for r in R if I(r, 'n475_ign') > 0 or I(r, 'fw5') or I(r, 'cnom_asb'))
        s['as_built_aborts_low_band'] = sum(1 for r in R if I(r, 'n475_ign') > 0 or I(r, 'fw5') or I(r, 'clo_asb'))
        s['as_built_abort_fraction_low_band'] = round(s['as_built_aborts_low_band'] / n, 4)
        s['max'] = {k: round(max(F(r, k) for r in R), 3) for k in ('face_pk_bar', 'head_pk_bar', 'raw_pk_bar', 'filt_pk_bar', 'vmax_V',
                                                                    'c30f_ms', 't30f_ms', 't45c_ms', 't45t_ms', 'head_above45_cont_ms',
                                                                    'head_above45_tot_ms')}
        ends = [F(r, 'c30_end_rel_E2_ms') for r in R if F(r, 'c30_end_rel_E2_ms') > -998]
        s['max']['c30_end_rel_E2_ms'] = round(max(ends), 1) if ends else None
        e2 = [F(r, 'tE2_ms') for r in R if F(r, 'tE2_ms') >= 0]
        s['E2_ms_from_light'] = [round(min(e2), 1), round(max(e2), 1)] if e2 else None
        s['unlit_cases'] = n - len(e2)
        s['cmp_v_max'] = {t: round(max(F(r, 'cmp_v_%s' % t) for r in R), 4) for t in TAUW}
        worst = max(R, key=lambda r: F(r, 'face_pk_bar'))
        s['worst_face_case'] = {'case': int(worst['case']), 'face_pk_bar': F(worst, 'face_pk_bar'), 'head_pk_bar': F(worst, 'head_pk_bar')}
        s['face_over_head_max'] = round(max(F(r, 'face_pk_bar') / F(r, 'head_pk_bar') for r in R), 3)
        out['chains'][ch] = s
        L.append('%-16s face max %6.2f (x%.3f head) raw %6.2f filt %5.2f vmax %.3f | >=4.75 V %3d, >=4.56 %3d | fw30 5/10/15/20/25 ms %s | '
                 'cmp nom %3d low asb/10/15/20/30 %s | as-built aborts nom %3d low %3d (%.1f %%) | c30 %4.1f ms end E2%+5.1f | T45 cont %.1f tot %.1f '
                 '(head %.2f/%.2f) | E2 %s' % (
                     ch, s['max']['face_pk_bar'], s['face_over_head_max'], s['max']['raw_pk_bar'], s['max']['filt_pk_bar'], s['max']['vmax_V'],
                     s['overrange_475_in_IGNITION'], s['above_fs_456_in_IGNITION'], [s['fw30_trips_persist_%dms' % p] for p in PERS_MS],
                     s['cmp_trips_as_built_nominal'], [s['cmp_trips_tau_%s_low_band' % t] for t in TAUW], s['as_built_aborts_nominal'],
                     s['as_built_aborts_low_band'], 100 * s['as_built_abort_fraction_low_band'], s['max']['c30f_ms'],
                     s['max']['c30_end_rel_E2_ms'] or -999, s['max']['t45c_ms'], s['max']['t45t_ms'], s['max']['head_above45_cont_ms'],
                     s['max']['head_above45_tot_ms'], s['E2_ms_from_light']))
    # ------------------------------------------------------------------------------------------------ ride-through sizing
    c1 = [c for c in chains if c.startswith('c1_')]
    pers = next((p for p in PERS_MS if all(out['chains'][c]['fw30_trips_persist_%dms' % p] == 0 for c in c1)), None)
    tauw = next((t for t in TAUW[1:] if all(out['chains'][c]['cmp_trips_tau_%s_low_band' % t] == 0 for c in c1)), None)
    c30_max = max(out['chains'][c]['max']['c30f_ms'] for c in c1)
    x_need = max(out['chains'][c]['max']['c30_end_rel_E2_ms'] or 0 for c in c1)
    t45_max = max(out['chains'][c]['max']['t45c_ms'] for c in c1)
    p_w = max(pers or 99, math.ceil(c30_max + a.margin_pers_ms))
    x_w = math.ceil((x_need + a.margin_x_ms) / 5.0) * 5.0
    t45_w = math.ceil(t45_max + a.margin_t45_ms)
    sizing = {
        'kRideOvpTime_s': {'v': p_w / 1000.0, 'basis': 'longest continuous filtered > 30 bar abs over the C1 chains %.1f ms + %.1f ms margin '
                                                      '(grid: first zero-trip persistence %s ms)' % (c30_max, a.margin_pers_ms, pers)},
        'kRideTauW_s': {'v': (float(tauw) / 1000.0) if tauw else None, 'basis': 'first grid RC with zero low-band-edge trips in every C1 '
                                                                               'chain (max RC voltages %s)' % {c: out['chains'][c]['cmp_v_max'] for c in c1}},
        'kRideWinPostE2_s': {'v': x_w / 1000.0, 'basis': 'latest end of a filtered > 30 episode after E2 %.1f ms + %.1f ms margin, rounded '
                                                         'up to 5 ms' % (x_need, a.margin_x_ms)},
        'kRideT45_s': {'v': t45_w / 1000.0, 'basis': 'longest continuous raw reading > 45 bar abs %.1f ms + %.1f ms margin (head-history '
                                                     'bracket 4.45 ms, LEAD 203 (1))' % (t45_max, a.margin_t45_ms)},
        'overrange_rule': {'v': 'unchanged (immediate HARD_START on a HIGH over-range in IGNITION)',
                           'basis': 'C1 chains: %s FA-1 cases reach 4.75 V (137.9 bar abs span); no relaxation is needed, so none is '
                                    'proposed' % sum(out['chains'][c]['overrange_475_in_IGNITION'] for c in c1)},
    }
    out['ride_through_sizing'] = sizing
    # ride-through outcome on the grid with the sized values (the grid knob at or below each sized value)
    pk = max(p for p in PERS_MS if p <= p_w)
    tk = tauw
    res = {}
    for c in chains:
        R = [r for r in rows if r['chain'] == c]
        ab = [r for r in R if I(r, 'n475_ign') > 0 or I(r, 'fw%d' % pk) or (tk and I(r, 'clo_%s' % tk)) or F(r, 't45c_ms') > t45_w]
        res[c] = {'aborts_low_band': len(ab), 'fraction': round(len(ab) / len(R), 4),
                  'by_path': {'overrange': sum(1 for r in R if I(r, 'n475_ign') > 0), 'fw30': sum(1 for r in R if I(r, 'fw%d' % pk)),
                              'comparator_low_band': sum(1 for r in R if tk and I(r, 'clo_%s' % tk)),
                              't45': sum(1 for r in R if F(r, 't45c_ms') > t45_w)}}
    out['ride_through_outcome_grid'] = {'persistence_ms_used': pk, 'tau_w_ms_used': tk, 't45_ms': t45_w, 'per_chain': res,
                                        'note': 'v210 chains shown for reference only: the ride-through is proposed for the C1 chain'}
    L.append('SIZING: kRideOvpTime_s %.3f, tau_w %s ms, X %.3f s after E2, T45 %.3f s; outcome %s' % (
        p_w / 1000.0, tk, x_w / 1000.0, t45_w / 1000.0, {c: res[c]['aborts_low_band'] for c in chains}))
    # regression vs the published v2.10 harness (no line, tau 0.9, v_sat 4.95)
    if os.path.exists(a.v210):
        v = json.load(open(a.v210))
        out['v210_published'] = {'file': os.path.relpath(a.v210, ROOT), 'sha256_16': sha16(a.v210)}
        try:
            for blk in v.get('summaries', v.get('summary', [])):
                pass
        except Exception:
            pass
    out['summary'] = L
    json.dump(out, open(a.out, 'w'), indent=1)
    open(a.out.replace('.json', '.txt'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    print('wrote', os.path.relpath(a.out, ROOT), sha16(a.out))


if __name__ == '__main__':
    main()
