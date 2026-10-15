#!/usr/bin/env python3
"""Relight fault path on the CAD v3.4.1 segment with the v2.9 light rule and the head-end bleed (Electronics, 2026-10-13, v3) - driver
of SIL scenario S11v29 (firmware/sil/sil_main.cpp scFaultPath29).

Coordinator relay 2026-10-13: re-run S11 on the 48.23 cm3 segment with retained-vapour slugs of 12 / 19 / 29 cm3 using the new (relative)
light rule; the bleed (2 taps T4 crown + FD-01 radial, 2 NC valves in series, orifice >= 0.8-1.0 mm) purges the vapour before the lift.
Lead 2026-10-13 (CHANGELOG): retained-vapour design attitude at RELIGHT theta <= 2 deg (provisional); 10 deg cases = robustness only.

Volumes are read, not typed:
  * segment volume   hub 03-cad/calcs/segment_traps_v341_v1.json  segment_volume_cm3.MV_closed_barrier_model           (published)
  * slug 0 deg       same file, retained_split_nominal['MV_closed|barrier|+Z'].retained_flow_path_cm3                      (published)
  * slug lead limit  lead decision line 'RETAINED-VAPOUR FIX = COIL RE-ROUTE' in interfaces/CHANGELOG.md ('<= Y cm3 at 10 deg swing')
  * slug 10 deg max  same hub file, max tilt_sensitivity[].split.retained_flow_path_cm3 over the barrier model at 10 deg      (published)
  * unreached vapour (bleed fitted, taps T4 + FD-01): Mechanical WORKDIR bleed_taps_v341 (UNPUBLISHED, labelled as such):
        v1.1 summary['barrier|S1+T4+FD01']['2'].flow_path_max_cm3   -> design attitude 2 deg
        v1   summary['barrier|S1+T4+FD01']['10'].flow_path_max_cm3  -> 10 deg robustness
    The SIL runs one 'unreached' value per invocation, so the script runs S11v29 twice (two output folders).
What it is: firmware-sequencing characterisation on ASSUMED plant models (vapour first through the ignition lift or the bleed, no light on
vapour, flashing draw through the bleed with the MV shut). Not Combustion's two-phase analysis; not hardware validation (CF-3/CF-4, IGN-1,
T4, B-BLEED-1).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
HUB = '/home/claude/work/shared-fallback/engine'
MECH = '/home/claude/work/mechanical/engine/03-cad/src/calcs'


def sha16(p: str) -> str:
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def lead_limit(changelog: str):
    pat = re.compile(r'<= ([0-9.]+) cm3 at 10 deg swing')
    for n, line in enumerate(open(changelog, encoding='utf-8'), 1):
        if 'RETAINED-VAPOUR FIX = COIL RE-ROUTE' in line:
            m = pat.search(line)
            if m:
                return float(m.group(1)), n
    raise SystemExit('lead retained-vapour limit line not found in %s' % changelog)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'results', 'sil_v2p9'))
    ap.add_argument('--sil', default=os.path.join(ROOT, 'firmware', 'build', 'sil'))
    a = ap.parse_args()
    seg_p = os.path.join(HUB, '03-cad', 'calcs', 'segment_traps_v341_v1.json')
    chg = os.path.join(HUB, 'interfaces', 'CHANGELOG.md')
    t1_p = os.path.join(MECH, 'bleed_taps_v341_v1.json')
    t11_p = os.path.join(MECH, 'bleed_taps_v341_v1p1.json')
    st = json.load(open(seg_p))
    seg = float(st['segment_volume_cm3']['MV_closed_barrier_model'])
    s0 = float(st['retained_split_nominal']['MV_closed|barrier|+Z']['retained_flow_path_cm3'])
    s10 = max(float(r['split']['retained_flow_path_cm3']) for r in st['tilt_sensitivity']
              if r.get('model') == 'barrier' and abs(float(r.get('tilt_deg', 0)) - 10.0) < 1e-6)
    lim, lim_line = lead_limit(chg)
    u2 = float(json.load(open(t11_p))['summary']['barrier|S1+T4+FD01']['2']['flow_path_max_cm3'])
    u10 = float(json.load(open(t1_p))['summary']['barrier|S1+T4+FD01']['10']['flow_path_max_cm3'])
    runs = []
    for tag, un, src in (('attitude_2deg', u2, t11_p), ('robustness_10deg', u10, t1_p)):
        od = os.path.join(a.out, 'S11v29_%s' % tag)
        os.makedirs(od, exist_ok=True)
        spec = 'seg=%.2f,unreached=%.2f,s0deg=%.2f,leadlimit=%.2f,s10degmax=%.2f' % (seg, un, s0, lim, s10)
        log = subprocess.run(['nice', '-n', '10', a.sil, 'fault29', od, spec], capture_output=True, text=True, check=True).stdout
        open(os.path.join(od, 'S11v29_run_log.txt'), 'w').write(log)
        res = json.load(open(os.path.join(od, 'S11v29_fault_path.json')))
        runs.append({'tag': tag, 'unreached_cm3': un, 'unreached_source': {'file': src, 'sha256_16': sha16(src), 'status': 'Mechanical workdir, UNPUBLISHED'},
                     'spec': spec, 'out_dir': od, 'cases': res['cases']})
    out = {
        'id': 'fault_path_v3', 'version': 'v3', 'date': '2026-10-13', 'owner': 'electronics', 'script': 'calc/fault_path_v3.py',
        'tag': 'SIL (firmware sequencing on ASSUMED plant models); volumes MECH/LEAD as cited',
        'inputs': {
            'segment_cm3': {'value': seg, 'source': seg_p, 'sha256_16': sha16(seg_p), 'tag': 'MECH (published)'},
            'slug_0deg_cm3': {'value': s0, 'source': seg_p, 'tag': 'MECH (published)'},
            'slug_lead_limit_cm3': {'value': lim, 'source': '%s line %d' % (chg, lim_line), 'tag': 'LEAD'},
            'slug_10deg_max_cm3': {'value': s10, 'source': seg_p, 'tag': 'MECH (published), 10 deg = robustness only (lead 2026-10-13)'},
        },
        'runs': runs,
        'limits': ['SIL logic + ASSUMED two-phase plant; Combustion owns the vapour physics (reroute_vapour on v3.4.1)',
                   'unreached volumes are from an UNPUBLISHED Mechanical workdir file and may change',
                   'side jet of the bleed not modelled; lead 2026-10-13: purge vent balanced or axial'],
    }
    p = os.path.join(ROOT, 'results', 'fault_path_v3.json')
    json.dump(out, open(p, 'w'), indent=1)
    lines = ['fault_path_v3 (S11v29): segment %.2f cm3, slugs %.2f / %.2f / %.2f cm3; unreached 2 deg %.2f / 10 deg %.2f cm3 (unpublished)' % (seg, s0, lim, s10, u2, u10)]
    for r in runs:
        for c in r['cases']:
            f = lambda x, n=2: 'nan' if x is None else ('%.*f' % (n, x))
            lines.append('%-17s %-48s V %6.2f bleed %d direct %d cmd->E2 %s s E2-light %s ms abort %-14s unlit %s g vap-pintle %s g bleed-liq %s g' % (
                r['tag'], c['case'], c['V_cm3'], c['bleed'], c['direct'], f(c['cmd_to_E2_s'], 3), f(c['E2_minus_light_ms'], 1), c['first_abort'],
                f(c['ox_unlit_relight_g']), f(c['vapour_through_pintle_g'], 3), f(c['liquid_through_bleed_g'])))
    open(os.path.join(ROOT, 'results', 'fault_path_v3.txt'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
