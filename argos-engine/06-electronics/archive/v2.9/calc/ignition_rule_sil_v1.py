#!/usr/bin/env python3
"""v2.9 light rule at the A1 relight state (Electronics, 2026-10-13, v1) - driver of SIL scenario S13 (firmware/sil/sil_main.cpp scIgnRule).

LEAD 2026-10-13 fixed light rule: P0 = mean over [E1 - 20 ms, E1] checked against the auto-zero ambient within residual + 0.1 bar (else
ambient); light = rise >= 0.8 bar filtered AND raw for 10 ms; floor 1.8 bar abs (2.0 bar once B-PC-1 <= 0.3 bar); kIgnitionPcAbs 3.0 bar
withdrawn. Targets (coordinator): 0/300 lit aborts, 0 unlit false lights, E2 within ~15 ms of light. Drogue release rule (lead, FC side):
E2 AND [Pc >= 3.0 bar abs OR rise held to E2 + 0.10 s] - scored here from the ECU telemetry bits (tlmf::) recorded by the SIL.

The A1 relight state (tank T, mass, port diameter) is READ from Combustion's start_latency_v2p4.json states.A1_relight; nothing is typed.
What it is: firmware logic on ASSUMED/SIM plant models (sil plant, Combustion bands via mcConfigs); not hardware validation (IGN-1, B-PC-1).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
SRC = '/home/claude/work/combustion/data/v2/v2p4/start_latency_v2p4.json'


def sha16(p: str) -> str:
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'results', 'sil_v2p9', 'S13'))
    ap.add_argument('--sil', default=os.path.join(ROOT, 'firmware', 'build', 'sil'))
    ap.add_argument('--n', type=int, default=300)
    ap.add_argument('--post-only', action='store_true', help='re-read an existing SIL output (no SIL run)')
    a = ap.parse_args()
    st = json.load(open(SRC))['states']['A1_relight']
    T, m, D = float(st['T']), float(st['m']), float(st['D'])
    os.makedirs(a.out, exist_ok=True)
    spec = '%.3f,%.4f,%.6f' % (T, m, D)
    if not a.post_only:
        log = subprocess.run(['nice', '-n', '10', a.sil, 'ignrule', a.out, spec, str(a.n)], capture_output=True, text=True, check=True).stdout
        open(os.path.join(a.out, 'S13_run_log.txt'), 'w').write(log)
    res = json.load(open(os.path.join(a.out, 'S13_ignition_rule.json')))
    rel = [r for r in res['A_mc'] if r['rule'].startswith('relative')][0]
    # runs that reached the relight (a pad-start abort - e.g. the pre-existing TVC_SUPPLY pad refusals at the battery-R corners - never
    # exercises the light rule): statistics over the lit relative-rule rows that entered RUN without abort
    rows = [x for x in csv.DictReader(open(os.path.join(a.out, 'S13_a1_mc.csv'))) if x['rule'] == 'relative']
    lit = [x for x in rows if x['plant_lit'] == '1']
    pad_ab = [x for x in lit if x['abort'] != '0' and x['E1_s'] == 'nan']
    reach = [x for x in lit if x not in pad_ab]
    ran = [x for x in reach if x['entered_RUN'] == '1' and x['abort'] == '0']

    def st(k):
        v = sorted(float(x[k]) for x in ran if x[k] != 'nan')
        return {'n': len(v), 'min': v[0], 'p50': v[len(v) // 2], 'p95': v[int(0.95 * (len(v) - 1))], 'max': v[-1]} if v else None
    post = {'lit_runs_pad_abort_before_relight': len(pad_ab), 'pad_abort_codes': sorted({x['abort'] for x in pad_ab}),
            'lit_runs_reaching_relight': len(reach), 'lit_light_rule_aborts': len(reach) - len(ran),
            'E2_minus_light_ms': st('E2_minus_light_ms'), 'A3_ratio_min': st('A3_ratio_min'), 'Pc_light30_abs_Pa': st('Pc_light30_Pa'),
            'drogue_rise_held_to_E2_0p10': sum(x['rise_held_to_E2_0p10'] == '1' for x in ran),
            'drogue_E2_to_Pc3bar_ms': st('E2_to_Pc3bar_ms'), 'drogue_E2_to_release_ms': st('E2_to_drogue_rule_ms')}
    targets = {
        'lit_aborts_0': post['lit_light_rule_aborts'] == 0,
        'unlit_false_lights_0': rel['unlit_false_lights'] == 0,
        'E2_minus_light_max_le_15ms': post['E2_minus_light_ms'] is not None and post['E2_minus_light_ms']['max'] <= 15.0,
        'B_corners_all_pass': res['B_fail'] == 0,
    }
    out = {'id': 'ignition_rule_sil_v1', 'version': 'v1', 'date': '2026-10-13', 'owner': 'electronics', 'script': 'calc/ignition_rule_sil_v1.py',
           'tag': 'SIL (firmware logic on ASSUMED/SIM plant bands); not IGN-1 / B-PC-1 evidence',
           'a1_state': {'T_K': T, 'm_kg': m, 'D_port_m': D, 'source': SRC, 'sha256_16': sha16(SRC), 'tag': 'COMB (SIM)'},
           'runs_per_cell': a.n, 'targets': targets, 'post': post, 'A_relative': rel,
           'A_legacy': [r for r in res['A_mc'] if not r['rule'].startswith('relative')][0],
           'B_cases': res['B_cases'], 'B_fail': res['B_fail'], 'sil_json': os.path.join(a.out, 'S13_ignition_rule.json')}
    json.dump(out, open(os.path.join(ROOT, 'results', 'ignition_rule_sil_v1.json'), 'w'), indent=1)
    print(json.dumps({'targets': targets, 'post': post}, indent=1))


if __name__ == '__main__':
    main()
