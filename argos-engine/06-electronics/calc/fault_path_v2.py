#!/usr/bin/env python3
"""Relight fault path on the retained-vapour targets of the coil re-route (Electronics, 2026-10-13, v2) - driver of SIL scenario S11.

LEAD 2026-10-13 (CHANGELOG, RETAINED-VAPOUR FIX = COIL RE-ROUTE, option (e)): flow-path retained vapour <= 13.5 cm3 nominal and <= 19 cm3
at a 10 deg swing, MV closed through the coast; one condition is "Electronics re-runs the fault path on the new segment". Coordinator
relay: a drained segment plus retained-vapour slugs of 13.5 and 19 cm3 at W 0.65 s cover it.

Volumes are read, not typed:
  * slug volumes        the lead's decision line in interfaces/CHANGELOG.md (regex on "<= X cm3 nominal, <= Y cm3 at 10 deg swing")
  * segment volume      a Mechanical trap-analysis JSON (--segment-json, key path --segment-keys). Default: the CAD v3.4 analysis
                        segment_traps_v34_v1p1.json (43.444 cm3 barrier model / 45.254 cm3 element open), i.e. the segment BEFORE the
                        re-route -> the drained case is PROVISIONAL until Mechanical publishes the re-routed segment (re-run with
                        --segment-json <published file>).
SIL S11 (firmware/sil/sil_main.cpp scFaultPath) runs every case kind on every volume; this script reports the physical ones:
  slug volumes    -> vapour_direct (segment reads PRIMED, direct path, W 0.65 s from the lift) and vapour_unknown_prep (P_feed invalid)
  segment volume  -> drained_prep (UNPRIMED, prep path)
The SIL output goes to its own folder (results/sil_v2p8_3_s11_v2), not into the manifest-covered results/sil_v2p8_3.
What it is: firmware-sequencing characterisation on ASSUMED plant models (vapour purged first through the ignition lift, no light on
vapour; drained line = adiabatic air pocket). Not Combustion's two-phase analysis; not hardware validation (CF-3, IGN-1, T4).
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
STATE = {0: 'NONE', 1: 'PRIMED (direct path)', 2: 'UNPRIMED', 3: 'UNKNOWN'}


def sha16(p: str) -> str:
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def fw_version() -> str:
    first = open(os.path.join(ROOT, 'firmware', 'src', 'core', 'config.h'), encoding='utf-8').readline()
    m = re.search(r'\((v[0-9][0-9.]*)', first)
    return m.group(1) if m else 'unknown'


def cfg_float(name: str) -> float:
    """literal value of a config.h constant (the numeric definition; the SIL what-if branch defines it from a macro)"""
    txt = open(os.path.join(ROOT, 'firmware', 'src', 'core', 'config.h'), encoding='utf-8').read()
    m = re.findall(r'constexpr float %s = ([0-9.eE+-]+)f;' % name, txt)
    if len(m) != 1:
        raise SystemExit('%s: %d literal definitions in config.h' % (name, len(m)))
    return float(m[0])


def lead_targets(changelog: str):
    pat = re.compile(r'retained vapour <= ([0-9.]+) cm3 nominal, <= ([0-9.]+) cm3 at 10 deg swing')
    for n, line in enumerate(open(changelog, encoding='utf-8'), 1):
        if 'RETAINED-VAPOUR FIX = COIL RE-ROUTE' in line:
            m = pat.search(line)
            if not m:
                raise SystemExit('lead line %d found but the target pattern did not match' % n)
            return n, float(m.group(1)), float(m.group(2)), line.strip()[:400]
    raise SystemExit('lead decision "RETAINED-VAPOUR FIX = COIL RE-ROUTE" not found in ' + changelog)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default='/home/claude/work/shared-fallback/engine')
    ap.add_argument('--segment-json', default='/home/claude/work/mechanical/engine/03-cad/src/calcs/segment_traps_v34_v1p1.json')
    ap.add_argument('--segment-keys', default='segment_volume_cm3.MV_closed_barrier_model,segment_volume_cm3.MV_closed_element_pores_open')
    ap.add_argument('--segment-status', default='PROVISIONAL: CAD v3.4 segment before the coil re-route')
    ap.add_argument('--sil', default=os.path.join(ROOT, 'firmware', 'build', 'sil'))
    ap.add_argument('--out', default=os.path.join(RES, 'sil_v2p8_3_s11_v2'))
    a = ap.parse_args()

    f_cl = os.path.join(a.engine_root, 'interfaces', 'CHANGELOG.md')
    f_plant = os.path.join(ROOT, 'firmware', 'sil', 'plant.h')
    n_line, v_nom, v_swing, line_txt = lead_targets(f_cl)
    seg = json.load(open(a.segment_json, encoding='utf-8'))
    seg_vols = []
    for kp in a.segment_keys.split(','):
        o = seg
        for k in kp.split('.'):
            o = o[k]
        seg_vols.append((kp.split('.')[-1], float(o)))
    slugs = [('lead_nominal', v_nom), ('lead_10deg_swing', v_swing)]
    spec = ','.join('%s=%.3f' % (lab, v) for lab, v in slugs + [('segment_' + lab, v) for lab, v in seg_vols])
    os.makedirs(a.out, exist_ok=True)
    log = os.path.join(a.out, 'S11_run_log.txt')
    with open(log, 'w', encoding='utf-8') as f:
        r = subprocess.run(['nice', '-n', '10', a.sil, 'fault', a.out, spec], stdout=f, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise SystemExit('sil fault failed, see ' + log)
    s11 = json.load(open(os.path.join(a.out, 'S11_fault_path.json'), encoding='utf-8'))
    b = s11['bounds_s']
    by = {c['case']: c for c in s11['cases']}
    W, gate = cfg_float('kIgnWindowRelightLong_s'), cfg_float('kTorchGate_s')   # build constants (config.h literal definitions)
    if abs(gate + W - b['direct_planning']) > 1e-6:
        raise SystemExit('S11 direct bound %.4f s != config.h gate %.3f + W %.3f' % (b['direct_planning'], gate, W))

    def pick(prefix: str, v: float):
        return by.get('%s_%.2fcm3' % (prefix, v))

    slug_rows = []
    for lab, v in slugs:
        vd, vu = pick('vapour_direct', v), pick('vapour_unknown_prep', v)
        row = {'label': lab, 'V_vapour_cm3': v, 'vapour_direct': vd, 'vapour_unknown_prep': vu}
        if vd and vd['first_abort'] == 'NONE' and W is not None:
            row['vapour_direct_margin_to_W_s'] = round(W - vd['E1_to_E2_s'], 4)
        if vu and vu['first_abort'] == 'NONE' and W is not None:
            row['vapour_unknown_prep_margin_to_W_s'] = round(W - vu['E1_to_E2_s'], 4)
        slug_rows.append(row)
    seg_rows = [{'label': lab, 'V_segment_cm3': v, 'drained_prep': pick('drained_prep', v)} for lab, v in seg_vols]

    findings = []
    for row in slug_rows:
        vd, vu = row['vapour_direct'], row['vapour_unknown_prep']
        for nm, c, mk in (('direct (reads PRIMED)', vd, 'vapour_direct_margin_to_W_s'), ('prep (P_feed invalid, UNKNOWN)', vu, 'vapour_unknown_prep_margin_to_W_s')):
            if not c:
                continue
            if c['first_abort'] == 'NONE':
                findings.append('%.1f cm3 retained-vapour slug, %s: lit, command -> E2 %.3f s, E1 -> E2 %.3f s vs W %.2f s (margin %.3f s); unignited N2O %.2f g'
                                % (row['V_vapour_cm3'], nm, c['cmd_to_E2_s'], c['E1_to_E2_s'], W, row[mk], c['ox_unlit_relight_kg'] * 1e3))
            else:
                findings.append('%.1f cm3 retained-vapour slug, %s: %s %.3f s after the command (no light)'
                                % (row['V_vapour_cm3'], nm, c['first_abort'], c['cmd_to_abort_s']))
    for row in seg_rows:
        c = row['drained_prep']
        if c:
            findings.append('drained %.3f cm3 segment (%s), prep path: %s' % (
                row['V_segment_cm3'], a.segment_status,
                ('command -> E2 %.3f s (E0 %.3f s) vs the 1.37 s bound and the 1.41 s plan' % (c['cmd_to_E2_s'], c['cmd_to_E0_s']))
                if c['first_abort'] == 'NONE' else '%s %.3f s after the command' % (c['first_abort'], c['cmd_to_abort_s'])))

    out = {
        'id': 'fault_path', 'version': 'v2', 'date': '2026-10-13', 'script': 'calc/fault_path_v2.py',
        'supersedes': 'fault_path_v1.json (kept): v1 ran fw v2.8.2 on the old 19/21.4/32.6/44 cm3 volumes as whole-segment vapour',
        'sil_scenario': 'firmware/sil/sil_main.cpp scFaultPath (S11), firmware ' + fw_version(),
        'request': 'LEAD CHANGELOG line %d condition "Electronics re-runs the fault path on the new segment"; coordinator relay: drained '
                   'segment + retained-vapour slugs of the two targets at W 0.65 s' % n_line,
        'inputs': {'CHANGELOG.md': {'path': f_cl, 'line': n_line, 'text': line_txt},
                   'segment': {'path': a.segment_json, 'sha256_16': sha16(a.segment_json), 'keys': a.segment_keys,
                               'status': a.segment_status},
                   'plant_h': [os.path.relpath(f_plant, ROOT), sha16(f_plant)],
                   'sil_binary': [os.path.relpath(a.sil, ROOT), sha16(a.sil)]},
        'bounds_s': b,
        'W_relight_flight_s': W,
        'references': {'liquid_direct': by.get('liquid_direct'), 'liquid_unknown_prep': by.get('liquid_unknown_prep')},
        'retained_vapour_slugs': slug_rows,
        'drained_segment': seg_rows,
        'pending': 'drained case on the RE-ROUTED segment: re-run with --segment-json <Mechanical re-route trap file> --segment-status '
                   '"re-routed (v3.4.1)" once Mechanical publishes it; the slug cases do not depend on the total segment volume in this plant',
        'findings': findings,
        'limitations': [
            'slug cases: the vapour volume is purged first as choked saturated vapour through the ignition lift (plant v2.7 C7 model, '
            'vapour state from Combustion low_inlet_check_v2p3), then liquid; no light on vapour; no buoyant migration modelled '
            '(Combustion owns the migration analysis)',
            'drained case: adiabatic AIR pocket at 1 bar in the whole segment (indicative); a real unprimed segment holds N2O at a '
            'higher pressure, so the pocket to compress is smaller',
            'one seed per case; ASSUMED valve opening, opener ramp and line-loss models; SIL is not hardware validation (CF-3, IGN-1, T4)'],
    }
    with open(os.path.join(RES, 'fault_path_v2.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    lines = ['fault_path_v2 (2026-10-13): SIL S11 on firmware %s; targets from CHANGELOG line %d (%.1f / %.1f cm3); segment %s'
             % (fw_version(), n_line, v_nom, v_swing, a.segment_status),
             '  bounds: direct %.2f s (torch gate %.2f + W %.2f, build constants), prep %.2f s, GNC plan %.2f s, PREPRESS_FAIL %.2f s'
             % (b['direct_planning'], gate, W, b['prep_path'], b['gnc_option_c_plan'], b['prepress_fail'])]
    for nm in ('liquid_direct', 'liquid_unknown_prep'):
        c = by.get(nm)
        if c:
            lines.append('  reference %-20s %s: command -> E0 %.3f s, E1 -> E2 %.3f s, command -> E2 %.3f s, abort %s'
                         % (nm, STATE.get(c['tlm_state_at_cmd'], '?'), c['cmd_to_E0_s'], c['E1_to_E2_s'], c['cmd_to_E2_s'], c['first_abort']))
    lines += ['  ' + f for f in findings]
    txt = '\n'.join(lines)
    with open(os.path.join(RES, 'fault_path_v2.txt'), 'w', encoding='utf-8') as f:
        f.write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
