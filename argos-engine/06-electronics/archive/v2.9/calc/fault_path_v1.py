#!/usr/bin/env python3
"""Relight fault path vs MV-to-seat segment volume (Electronics, 2026-10-13, v1) - driver of SIL scenario S11.

LEAD 2026-10-13 (relay of GNC v3 option (c)): the FC plans 1.41 s on UNPRIMED against the ECU's 1.37 s prep-path bound (margin 0.04 s);
Electronics re-states the fault-path time (prep + ignition) for the ~44 cm3 MV-to-seat segment of Mechanical option A.

This script takes the segment volumes from the files that own them (nothing about other teams' numbers is typed in here):
  * plant V_line           firmware/sil/plant.h EngineParams::V_line (Electronics ASSUMED gas-pocket volume of the SIL plant)
  * COMB v2.3              hub 02-combustion/data/v2/low_inlet_check_v2p3.json 3_volumes.valve_to_seat_cm3.valve_at_coil_fixed_end
  * COMB v2.4 recheck      Combustion workdir data/v2/v2p4/segment_recheck_v2p4.json A_masses_purge (volumes in the block keys, e.g.
                           "Mechanical_32.6cm3", "zone_top_44cm3"; also Combustion's scaled full-vapour purge times, for comparison)
  * MECH option A          Mechanical workdir 03-cad/src/calcs/seat_leak_drain_v1.json inputs.V_segment_cm3
runs `sil fault <out> label=cm3,...` (firmware/sil/sil_main.cpp scFaultPath) and writes ../results/fault_path_v1.json / .txt.

What S11 shows and does not show: the SIL plant (indicative adiabatic air pocket for a drained line; choked saturated-vapour purge through
the ignition lift for a vapour segment) runs the unchanged ECU core. It is a firmware-sequencing characterisation on ASSUMED plant models,
not Combustion's two-phase analysis and not hardware validation (CF-3 / IGN-1 measure the real times).
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
RES = os.path.join(ROOT, 'results')


def sha16(p: str) -> str:
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def plant_v_line_cm3(plant_h: str) -> float:
    m = re.search(r'double\s+V_line\s*=\s*([0-9.eE+-]+)\s*;', open(plant_h, encoding='utf-8').read())
    if not m:
        raise SystemExit('V_line not found in plant.h')
    return float(m.group(1)) * 1e6


def fw_version() -> str:
    """firmware version from the first line of firmware/src/core/config.h ('tunable configuration (vX.Y.Z, ...')"""
    import re as _re
    first = open(os.path.join(ROOT, 'firmware', 'src', 'core', 'config.h'), encoding='utf-8').readline()
    m = _re.search(r'\((v[0-9][0-9.]*)', first)
    return m.group(1) if m else 'unknown'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default='/home/claude/work/shared-fallback/engine')
    ap.add_argument('--comb-data', default='/home/claude/work/combustion/data/v2/v2p4', help='Combustion workdir v2.4 data (read only)')
    ap.add_argument('--mech-calcs', default='/home/claude/work/mechanical/engine/03-cad/src/calcs', help='Mechanical workdir calcs (read only)')
    ap.add_argument('--sil', default=os.path.join(ROOT, 'firmware', 'build', 'sil'))
    ap.add_argument('--out', default=os.path.join(RES, 'sil_v2p8_final'))
    a = ap.parse_args()

    f_plant = os.path.join(ROOT, 'firmware', 'sil', 'plant.h')
    f_li = os.path.join(a.engine_root, '02-combustion', 'data', 'v2', 'low_inlet_check_v2p3.json')
    f_rc = os.path.join(a.comb_data, 'segment_recheck_v2p4.json')
    f_sl = os.path.join(a.mech_calcs, 'seat_leak_drain_v1.json')
    src = []   # (label, cm3, source text)
    src.append(('plant_V_line_ASSUMED', plant_v_line_cm3(f_plant), 'firmware/sil/plant.h EngineParams::V_line (Electronics ASSUMED)'))
    li = json.load(open(f_li, encoding='utf-8'))
    src.append(('COMB_v2p3_valve_at_coil', float(li['3_volumes']['valve_to_seat_cm3']['valve_at_coil_fixed_end']),
                'hub low_inlet_check_v2p3.json 3_volumes.valve_to_seat_cm3.valve_at_coil_fixed_end'))
    rc = json.load(open(f_rc, encoding='utf-8'))
    comb_purge = {}
    for k, blk in rc['A_masses_purge'].items():
        m = re.search(r'([0-9.]+)cm3', k)
        if not m:
            continue
        v = float(m.group(1))
        comb_purge[v] = {'key': k, 'purge_full_vapour_s': blk.get('purge_full_vapour_s'),
                         'vapour_if_full_g': {s: blk[s]['vapour_if_full_g'] for s in blk if isinstance(blk[s], dict) and 'vapour_if_full_g' in blk[s]}}
        src.append(('COMB_v2p4_' + k.split('_')[0], v, 'Combustion workdir segment_recheck_v2p4.json A_masses_purge key "%s"' % k))
    sl = json.load(open(f_sl, encoding='utf-8'))
    src.append(('MECH_optionA', float(sl['inputs']['V_segment_cm3']), 'Mechanical workdir seat_leak_drain_v1.json inputs.V_segment_cm3'))
    # one SIL run per distinct volume (labels merged)
    vols = {}
    for lab, v, s in src:
        key = round(v, 2)
        vols.setdefault(key, {'labels': [], 'sources': []})
        vols[key]['labels'].append(lab)
        vols[key]['sources'].append(s)
    spec = ','.join('%s=%.2f' % ('+'.join(d['labels']), v) for v, d in sorted(vols.items()))
    os.makedirs(a.out, exist_ok=True)
    log = os.path.join(a.out, 'S11_run_log.txt')
    with open(log, 'w', encoding='utf-8') as f:
        r = subprocess.run(['nice', '-n', '10', a.sil, 'fault', a.out, spec], stdout=f, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise SystemExit('sil fault failed, see ' + log)
    s11 = json.load(open(os.path.join(a.out, 'S11_fault_path.json'), encoding='utf-8'))
    b = s11['bounds_s']
    rows = s11['cases']
    by = {c['case']: c for c in rows}

    def pick(prefix: str, v: float):
        return by.get('%s_%.2fcm3' % (prefix, v))

    table = []
    for v, d in sorted(vols.items()):
        dr, vd, vu = pick('drained_prep', v), pick('vapour_direct', v), pick('vapour_unknown_prep', v)
        cp = comb_purge.get(v) or comb_purge.get(round(v, 1))
        table.append({'V_cm3': v, 'labels': d['labels'], 'sources': d['sources'],
                      'drained_prep': dr, 'vapour_direct': vd, 'vapour_unknown_prep': vu,
                      'comb_v2p4_purge_full_vapour_s': cp['purge_full_vapour_s'] if cp else None})
    v44 = max(vols)
    t44 = [t for t in table if t['V_cm3'] == v44][0]

    def cmd_e2(c):
        return c['cmd_to_E2_s'] if c and c['first_abort'] == 'NONE' else None

    findings = []
    dr44 = t44['drained_prep']
    if dr44:
        if dr44['first_abort'] == 'NONE':
            findings.append('drained %.2f cm3 segment (prep path): command -> E2 %.3f s (E0 at %.3f s) vs the 1.37 s bound and the GNC 1.41 s plan'
                            % (v44, dr44['cmd_to_E2_s'], dr44['cmd_to_E0_s']))
        else:
            findings.append('drained %.2f cm3 segment (prep path): %s %.3f s after the command (no light; bound 2.42 s)'
                            % (v44, dr44['first_abort'], dr44['cmd_to_abort_s']))
    vd44 = t44['vapour_direct']
    if vd44:
        findings.append('vapour-full %.2f cm3 segment read PRIMED (direct): %s' % (
            v44, ('lit, command -> E2 %.3f s (E1 -> E2 %.3f s vs W 0.65 s)' % (vd44['cmd_to_E2_s'], vd44['E1_to_E2_s']))
            if vd44['first_abort'] == 'NONE' else ('%s %.3f s after the command; unignited N2O %.2f g, vapour purged %.2f g'
                                                   % (vd44['first_abort'], vd44['cmd_to_abort_s'], vd44['ox_unlit_relight_kg'] * 1e3,
                                                      vd44['vapour_purged_kg'] * 1e3))))
    out = {
        'id': 'fault_path', 'version': 'v1', 'date': '2026-10-13', 'script': 'calc/fault_path_v1.py',
        'sil_scenario': 'firmware/sil/sil_main.cpp scFaultPath (S11), firmware ' + fw_version(),
        'inputs': {'plant_h': [os.path.relpath(f_plant, ROOT), sha16(f_plant)], 'low_inlet_check_v2p3': [f_li, sha16(f_li)],
                   'segment_recheck_v2p4': [f_rc, sha16(f_rc)], 'seat_leak_drain_v1': [f_sl, sha16(f_sl)]},
        'bounds_s': b,
        'references': {'liquid_direct': by.get('liquid_direct'), 'liquid_unknown_prep': by.get('liquid_unknown_prep')},
        'by_volume': table,
        'findings': findings,
        'limitations': [
            'drained case: adiabatic AIR pocket at 1 bar in the whole segment (plant v2.2 indicative model, no wall heat transfer, no '
            'flashing); a real unprimed segment holds N2O vapour/liquid at a higher pressure, so the pocket to compress is smaller',
            'vapour case: choked saturated-vapour purge through the ignition lift (plant v2.7 C7 model, 20 C vapour state from '
            'Combustion low_inlet_check_v2p3) and no light on vapour (conservative for the window)',
            'one seed per case; ASSUMED valve opening, opener ramp and line-loss models; SIL is not hardware validation (CF-3, IGN-1)'],
    }
    with open(os.path.join(RES, 'fault_path_v1.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    lines = ['fault_path_v1 (2026-10-13): relight from the RELIGHT command, SIL S11 on firmware ' + fw_version() + ' (bounds: direct %.2f s, prep %.2f s, '
             'GNC plan %.2f s, PREPRESS_FAIL %.2f s)' % (b['direct_planning'], b['prep_path'], b['gnc_option_c_plan'], b['prepress_fail'])]
    for nm in ('liquid_direct', 'liquid_unknown_prep'):
        c = by.get(nm)
        if c:
            lines.append('  reference %-20s TLM state %d worst %d ms: command -> E0 %.3f s, -> E2 %.3f s, abort %s'
                         % (nm, c['tlm_state_at_cmd'], c['tlm_worst_ms'], c['cmd_to_E0_s'], c['cmd_to_E2_s'], c['first_abort']))
    for t in table:
        lines.append('  V %.2f cm3 (%s)' % (t['V_cm3'], ', '.join(t['labels'])))
        for nm in ('drained_prep', 'vapour_direct', 'vapour_unknown_prep'):
            c = t[nm]
            if not c:
                continue
            res = ('command -> E0 %.3f s, E1 -> E2 %.3f s, command -> E2 %.3f s' % (c['cmd_to_E0_s'], c['E1_to_E2_s'], c['cmd_to_E2_s'])
                   if c['first_abort'] == 'NONE' else '%s at %.3f s after the command' % (c['first_abort'], c['cmd_to_abort_s']))
            lines.append('    %-20s TLM state %d (%s), worst %d ms: %s; unignited N2O %.2f g, vapour purged %.2f g'
                         % (nm, c['tlm_state_at_cmd'], {0: 'NONE', 1: 'PRIMED', 2: 'UNPRIMED', 3: 'UNKNOWN'}.get(c['tlm_state_at_cmd'], '?'),
                            c['tlm_worst_ms'], res, c['ox_unlit_relight_kg'] * 1e3, c['vapour_purged_kg'] * 1e3))
        if t['comb_v2p4_purge_full_vapour_s'] is not None:
            lines.append('    Combustion v2.4 full-vapour purge estimate (scaled SIM C7): %.3f s' % t['comb_v2p4_purge_full_vapour_s'])
    lines += ['  finding: ' + f for f in findings]
    txt = '\n'.join(lines)
    with open(os.path.join(RES, 'fault_path_v1.txt'), 'w', encoding='utf-8') as f:
        f.write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
