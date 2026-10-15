#!/usr/bin/env python3
"""Provisional over-thrust abort: basis, coverage and timing (Electronics, 2026-10-13, v1).

LEAD 2026-10-13 (gnc.json v3 lead_decisions_2026-10-13.over_thrust_abort): firmware v2.7+ flies open loop on a Pc-sensor loss; with the
Pc channel failed the firmware over-pressure check and the hardware comparator (same PC_SIG wire) are blind, so an accelerometer
over-thrust abort is added on the CAN frame FC_THRUST (0x024, >= 100 Hz): provisional 650 N held 20 ms = 500 N x 1.143 (Cd band) x
1.10 (estimate error, ASSUMED); stale (> 50 ms) or invalid -> flag only. GNC is to publish the estimate's 3-sigma error and latency,
the false-abort rate and the stuck-pintle detection time.

This script makes the basis traceable and shows what the provisional numbers do and do not cover:
  (1) false-trip margin: largest nominal delivered thrust (FC command 500 N x the Cd band) x (1 + estimate error) vs the threshold;
  (2) coverage of the runaway (pintle full-stroke failure) cases published by Combustion (combustion.json
      pressure_limits.full_stroke_failure_S230, SIM steady, initial port): detected only if F x (1 - estimate error) > threshold;
  (3) the chamber-pressure equivalent of the threshold (least-squares F = a Pc + b over the same table) vs the ECU abort and MEOP;
  (4) the reaction-time budget from the threshold crossing to the NC valve closed (estimate latency, frame period, persistence,
      MV-P latch release and closing; Mechanical mv_actuator_v1 and calc/mv_latch_magnet_v1 results).
Inputs: interfaces/combustion.json, interfaces/gnc.json (decision record, read for traceability), firmware/src/core/config.h (threshold,
persistence, staleness; parsed), results/mv_latch_magnet_v1.json, Mechanical mv_actuator_v1.json (closing time). Nothing about other
teams' numbers is typed in here. Outputs: ../results/over_thrust_v1.json / .txt. An analysis on SIM inputs, not a validation.
"""
from __future__ import annotations

import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'results')
CFG_H = os.path.join(HERE, '..', 'firmware', 'src', 'core', 'config.h')

F_CMD_MAX_N = 500.0          # [REQ] engine nominal maximum thrust (sea level), the largest FC thrust command
EST_ERR = (0.0, 0.05, 0.10, 0.15)   # [ASSUMED sweep] FC estimate error fraction (GNC to publish the 3-sigma value; LEAD basis 0.10)
FC_PERIOD_S = 0.010          # [ASSUMED >= 100 Hz] FC_THRUST period (GNC: >= 100 Hz)
FC_LAT_S = 0.020             # [GNC decision text: raw or lightly filtered, tau <= 20 ms] estimate latency bound used here


def cfg_value(name: str) -> float:
    txt = open(CFG_H, encoding='utf-8').read()
    m = re.search(r'constexpr\s+float\s+' + re.escape(name) + r'\s*=\s*([0-9.eE+-]+)f?\s*;', txt)
    if not m:
        raise SystemExit(f'{name} not found in config.h')
    return float(m.group(1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default='/mnt/project-files/engine')
    ap.add_argument('--mech-root', default=None, help='Mechanical workdir engine root (mv_actuator_v1.json), default = engine root')
    a = ap.parse_args()
    comb = json.load(open(os.path.join(a.engine_root, 'interfaces', 'combustion.json'), encoding='utf-8'))
    gnc = json.load(open(os.path.join(a.engine_root, 'interfaces', 'gnc.json'), encoding='utf-8'))
    pl = comb['gas_path']['pressure_limits'] if 'pressure_limits' in comb.get('gas_path', {}) else None
    if pl is None:   # locate the block wherever it sits
        def find(d):
            if isinstance(d, dict):
                if 'full_stroke_failure_S230' in d:
                    return d
                for v in d.values():
                    r = find(v)
                    if r is not None:
                        return r
            return None
        pl = find(comb)
    rows = pl['full_stroke_failure_S230']['v']
    meop = pl['chamber_MEOP_Pa']['v']
    abort_pa = pl['abort_Pa']['v']
    cd_rows = sorted({r['Cd'] for r in rows})
    cd_nom = 0.7 if 0.7 in cd_rows else cd_rows[len(cd_rows) // 2]   # Combustion nominal Cd (map basis)
    cd_band = max(cd_rows) / cd_nom
    thr = cfg_value('kOverThrust_N'); t_hold = cfg_value('kOverThrustTime_s'); t_stale = cfg_value('kFcThrustStale_s')
    gnc_rec = gnc.get('lead_decisions_2026-10-13', {}).get('v', {}).get('over_thrust_abort', 'not found')

    # (1) false-trip margin
    F_nom_max = F_CMD_MAX_N * cd_band
    false_trip = [{'est_err': e, 'F_est_N': F_nom_max * (1 + e), 'margin_N': thr - F_nom_max * (1 + e)} for e in EST_ERR]
    # (2) runaway coverage
    cov = []
    for e in EST_ERR:
        det = [r for r in rows if r['F_N'] * (1 - e) > thr]
        cov.append({'est_err': e, 'detected': len(det), 'of': len(rows),
                    'missed': [f"{r['T_tank_C']:.0f} C Cd {r['Cd']}: {r['F_N']:.1f} N, {r['Pc_bar']:.2f} bar" for r in rows if r['F_N'] * (1 - e) <= thr]})
    # (3) Pc equivalent (least squares F = a Pc + b, Pc in Pa abs as published in bar)
    n = len(rows); sx = sum(r['Pc_bar'] for r in rows); sy = sum(r['F_N'] for r in rows)
    sxx = sum(r['Pc_bar'] ** 2 for r in rows); sxy = sum(r['Pc_bar'] * r['F_N'] for r in rows)
    a_ = (n * sxy - sx * sy) / (n * sxx - sx * sx); b_ = (sy - a_ * sx) / n
    pc_thr_bar = (thr - b_) / a_
    resid = max(abs(r['F_N'] - (a_ * r['Pc_bar'] + b_)) for r in rows)
    # (4) timing budget from the true thrust crossing the threshold to the NC valve closed
    mech_root = a.mech_root or a.engine_root
    mv = None
    for rel in ('03-cad/calcs/mv_actuator_v1.json', '03-cad/src/calcs/mv_actuator_v1.json'):
        p = os.path.join(mech_root, rel)
        if os.path.exists(p):
            mv = json.load(open(p, encoding='utf-8')); break
    t_close = mv['B_balanced_poppet_MVP']['closing_with_dashpot_s'] if mv else float('nan')
    mag = json.load(open(os.path.join(RES, 'mv_latch_magnet_v1.json'), encoding='utf-8'))
    t_rel = mag['selected']['release']['cold_8V4']['t_release_s']   # worst (8.4 V, -10 C) release estimate
    budget = {'fc_latency_s': FC_LAT_S, 'fc_frame_period_s': FC_PERIOD_S, 'ecu_persistence_s': t_hold, 'ecu_tick_s': 0.001,
              'mv_latch_release_s': t_rel, 'mv_close_s': t_close}
    tot = sum(v for v in budget.values() if isinstance(v, (int, float)) and v == v)
    out = {
        'id': 'over_thrust', 'version': 'v1', 'date': '2026-10-13', 'script': 'calc/over_thrust_v1.py',
        'inputs': {
            'threshold_N': [thr, 'config.h kOverThrust_N (LEAD PROVISIONAL)'], 'hold_s': [t_hold, 'config.h kOverThrustTime_s (LEAD PROVISIONAL)'],
            'stale_s': [t_stale, 'config.h kFcThrustStale_s (GNC decision: stale > 50 ms -> flag only)'],
            'F_cmd_max_N': [F_CMD_MAX_N, 'REQ'], 'Cd_rows': [cd_rows, 'combustion.json full_stroke_failure_S230'],
            'Cd_band': [cd_band, 'DERIVED max Cd / nominal 0.7 (combustion.json rows)'],
            'MEOP_Pa': [meop, 'combustion.json pressure_limits (LEAD)'], 'abort_Pa': [abort_pa, 'combustion.json pressure_limits (LEAD)'],
            'gnc_decision': gnc_rec,
        },
        'false_trip': {'F_nominal_max_N': F_nom_max, 'cases': false_trip,
                       'note': 'LEAD basis 500 x 1.143 x 1.10 = 628 N < 650 N; a 3-sigma estimate error above ~13.7 % removes the margin'},
        'runaway_coverage': cov,
        'pc_equivalent': {'fit_F_N_per_bar': a_, 'fit_offset_N': b_, 'fit_resid_max_N': resid, 'threshold_Pc_bar_abs': pc_thr_bar,
                          'abort_bar_abs': abort_pa / 1e5, 'MEOP_bar_abs': meop / 1e5},
        'timing_budget_s': budget, 'timing_total_s': tot,
        'limitations': ['SIM steady runaway table (initial port); transients and the estimate dynamics are not modelled here (SIL S6 runs them with ASSUMED '
                        'latency 20 ms and 5 N rms noise)',
                        'blind to throat blockage (thrust falls while Pc rises) and to over-pressure without over-thrust',
                        'estimate error and latency ASSUMED until GNC publishes them'],
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, 'over_thrust_v1.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    lines = [f'over_thrust_v1 (2026-10-13): threshold {thr:.0f} N held {t_hold * 1e3:.0f} ms (LEAD PROVISIONAL)',
             f'  nominal max delivered thrust {F_nom_max:.1f} N (500 N x Cd band {cd_band:.3f})']
    for c in false_trip:
        lines.append(f"  false trip: estimate error {c['est_err'] * 100:4.0f} % -> {c['F_est_N']:.1f} N, margin {c['margin_N']:+.1f} N")
    for c in cov:
        lines.append(f"  runaway coverage at estimate error -{c['est_err'] * 100:.0f} %: {c['detected']}/{c['of']} detected; missed: {'; '.join(c['missed']) or 'none'}")
    lines.append(f'  Pc equivalent of {thr:.0f} N: {pc_thr_bar:.2f} bar abs (fit {a_:.2f} N/bar {b_:+.1f} N, residual <= {resid:.1f} N); ECU abort '
                 f'{abort_pa / 1e5:.1f} bar, MEOP {meop / 1e5:.1f} bar')
    lines.append(f'  crossing -> NC valve closed budget {tot * 1e3:.1f} ms: ' + ', '.join(f'{k} {v * 1e3:.1f} ms' for k, v in budget.items() if isinstance(v, (int, float))))
    txt = '\n'.join(lines)
    with open(os.path.join(RES, 'over_thrust_v1.txt'), 'w', encoding='utf-8') as f:
        f.write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
