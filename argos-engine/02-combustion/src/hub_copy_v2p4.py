"""Copy the Combustion v2.4 workdir results to the hub (02-combustion), file superseded runs apart, and write a file index.
(Combustion v2.4 handback, 2026-10-13; coordinator item 4: every v2p4 file cited in CHANGELOG lines 155 and 159, plus
reroute_vapour, nozzle_joint, ignition_detect, drogue_hold_check and nozzle_lip_melt, and the superseded runs marked as such.)

Rules: copy a file only if it is missing in the hub or differs; never delete; verify every copy by hash; superseded runs go to
data/v2/v2p4/superseded/ with SUPERSEDED.txt; CAD v3.4-basis results stay in data/v2/v2p4/ (cited evidence) and are flagged in
FILE-INDEX.txt.
usage: python -I hub_copy_v2p4.py WORKDIR HUB_02_COMBUSTION SCRATCHPAD
"""
from __future__ import annotations
import hashlib, json, os, shutil, sys, time
sys.dont_write_bytecode = True

SUPERSEDED_DATA = {   # workdir data/v2/v2p4 -> superseded/
    'segment_void_balance_v2p4.json': ('retained_vapour_v341_v2p4.json + purge_duration_v2p4.json + rg01_line_states_v2p4.json',
                                       'segment void balance on the CAD v3.4 44 cm3 inverted U (hardware no longer exists)'),
    'segment_void_balance_v2p4_run1_coastup_wet.json': ('segment_void_balance_v2p4.json (itself superseded)', 'run 1: coast-up wet reading only'),
    'relight_vapour_order_v2p4_pre_void_fix.json': ('relight_vapour_order_v2p4.json', 'before the route-void fix (route_void_bracket_v2p4)'),
    'relight_vapour_states_v2p4_pre_void_fix.json': ('relight_vapour_states_v2p4.json', 'before the route-void fix'),
    'prep_path_inventory_v2p4_run1_bleed0p06.json': ('prep_path_inventory_v2p4.json', 'run 1 read the PREPRESS as a 0.06 s bleed; the firmware holds it longer'),
}
SUPERSEDED_SCRATCH = {
    'late_light_spike_v2p4_run1_20C_A1.json': ('late_light_spike_v2p4.json', 'run 1: 20 C pad and A1 relight only; run 2 adds 15 and 25 C and the full grid'),
    'purge_hazard_v2p4_prelabelfix.json': ('purge_hazard_v2p4.json', 'label fix only (numbers unchanged)'),
    'purge_hazard_v2p4_prelabelfix.py': ('src/purge_hazard_v2p4.py', 'label fix only'),
    'ignition_detect_v2p4_run1.json': ('ignition_detect_v2p4.json', 'run 1 before the part E / G corrections'),
    'segment_void_balance_v2p4_run1.py': ('src/segment_void_balance_v2p4.py (itself superseded)', 'run 1 script'),
    'prep_path_inventory_v2p4_run1.py': ('src/prep_path_inventory_v2p4.py', 'run 1 script'),
}
V34_BASIS = ('reroute_vapour_v2p4.json', 'reroute_vapour_vseg50p6_v2p4.json', 'purge_slip_v2p4.json', 'purge_slip_v2p4.json.raw.json',
             'purge_table_v2p4.json', 'route_void_bracket_v2p4.json', 'vapour_options_v2p4.json', 'segment_recheck_v2p4.json',
             'throat_block_seg44_v2p4.json', 'relight_window_rule_seg44_v2p4.json', 'relight_window_rule_seg32.6_v2p4.json',
             'relight_latency_sup_seg44_v2p4.json', 'relight_latency_sup_seg32.6_v2p4.json', 'retained_vapour_check_v2p4.json',
             'segment_drain_v2p4.json')
NOTES = {
    'purge_sizing_v2p4.json': 'CAD v3.4 crest-bleed sizing; its tap fluxes (HEM 15 450, Dyer 56 843 kg/m2s, Cd 0.70) are still used; Tp and N2O superseded by purge_duration_v2p4 / rg01_line_states_v2p4',
    'rg01_line_states_v2p4.json': 'decided bleed path (2 x 0.707 mm), GNC line states, minimal set (coordinator items 1-2, after CHANGELOG 160-161)',
    'purge_duration_v2p4.json': 'purge time on the fine grid (CHANGELOG 159)',
    'late_light_spike_v2p4.json': 'late-light spike (CHANGELOG 159)', 'late_light_tables_v2p4.json': 'late-light tables (CHANGELOG 159)',
    'drogue_hold_check_v2p4.json': 'drogue-release hold check (CHANGELOG 155)',
    'retained_vapour_v341_v2p4.json': 'integrated trade on CAD v3.4.1 (summary in _summary.json.gz, per-series raw in .raw.json.gz)',
    'segment_drain_v2p4.json': 'computed on 44 cm3; carried for the shutdown order (scales with the segment)',
    'purge_vented_mass_v2p4.json': 'vented mass against time on the decided path (REV-GNC-2 RG-16)',
    'fd01_element_deficit_v2p4.json': 'FD-01 inline element deficit on the decided path (CHANGELOG 164 check)',
    'cf4_void_budget_v2p4.json': 'CF-4 Table 10.4 void budget (CF-4-SPEC.md Table 1)',
}


def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()[:16]


def copy(src, dst, log):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and sha16(dst) == sha16(src):
        log.append(('same', dst)); return
    act = 'replace' if os.path.exists(dst) else 'new'
    shutil.copy2(src, dst)
    assert sha16(dst) == sha16(src), dst
    log.append((act, dst))


def main(wd, hub, scratch):
    log = []
    dsrc = os.path.join(wd, 'data', 'v2'); ddst = os.path.join(hub, 'data', 'v2')
    sup_dir = os.path.join(ddst, 'v2p4', 'superseded')
    for root, _, files in os.walk(dsrc):
        for fn in files:
            s = os.path.join(root, fn); rel = os.path.relpath(s, dsrc)
            if rel.startswith('v2p4' + os.sep) and fn in SUPERSEDED_DATA and os.path.dirname(rel) == 'v2p4':
                copy(s, os.path.join(sup_dir, fn), log)
            else:
                copy(s, os.path.join(ddst, rel), log)
    for fn in SUPERSEDED_SCRATCH:
        copy(os.path.join(scratch, fn), os.path.join(sup_dir, fn), log)
    copy(os.path.join(wd, 'deliver', 'v2p4', 'superseded_s2_8_v34_inverted_U.txt'), os.path.join(hub, 'superseded', 's2_8_v34_inverted_U.txt'), log)
    for fn in sorted(os.listdir(os.path.join(wd, 'src'))):
        if fn.endswith('.py'):
            copy(os.path.join(wd, 'src', fn), os.path.join(hub, 'src', fn), log)
    t0 = time.mktime(time.strptime('2026-10-13 00:00', '%Y-%m-%d %H:%M'))
    for fn in sorted(os.listdir(os.path.join(wd, 'logs'))):
        p = os.path.join(wd, 'logs', fn)
        if os.path.isfile(p) and os.path.getmtime(p) >= t0:
            copy(p, os.path.join(ddst, 'v2p4', 'logs', fn), log)
    # SUPERSEDED.txt
    lines = ['Superseded Combustion v2.4 runs (kept as evidence; do not cite as current). sha256/16, superseded by, reason.', '']
    for fn, (by, why) in list(SUPERSEDED_DATA.items()) + list(SUPERSEDED_SCRATCH.items()):
        lines.append(f'{fn} | {sha16(os.path.join(sup_dir, fn))} | superseded by {by} | {why}')
    lines += ['', 'Report text: ../../../../superseded/s2_8_v34_inverted_U.txt (v2.4-draft section 2.8 on the CAD v3.4 inverted U; replaced by REPORT v2.4 section 2.8).']
    open(os.path.join(sup_dir, 'SUPERSEDED.txt'), 'w').write('\n'.join(lines) + '\n')
    # FILE-INDEX.txt for data/v2/v2p4 (top level)
    vd = os.path.join(ddst, 'v2p4')
    idx = ['Combustion v2.4 data index (data/v2/v2p4). Columns: file | sha256/16 | bytes | producing script | status.',
           'Status: current; CAD v3.4 basis (44 cm3 inverted U or 32.6/44 cm3 segment: cited evidence, superseded for decisions by the v3.4.1 trade); see superseded/ for replaced runs.', '']
    for fn in sorted(os.listdir(vd)):
        p = os.path.join(vd, fn)
        if not os.path.isfile(p):
            continue
        scr = ''
        if fn.endswith('.json') and os.path.getsize(p) < 40e6:
            try:
                scr = json.load(open(p)).get('script', '') or ''
            except Exception:
                scr = ''
        st = 'CAD v3.4 basis' if fn in V34_BASIS else 'current'
        note = NOTES.get(fn, '')
        idx.append(f'{fn} | {sha16(p)} | {os.path.getsize(p)} | {scr} | {st}' + (f' | {note}' if note else ''))
    for sub in ('erosion', 'logs', 'superseded'):
        if os.path.isdir(os.path.join(vd, sub)):
            idx.append(f'{sub}/ | directory | {len(os.listdir(os.path.join(vd, sub)))} files')
    open(os.path.join(vd, 'FILE-INDEX.txt'), 'w').write('\n'.join(idx) + '\n')
    n = {}
    for a, _ in log:
        n[a] = n.get(a, 0) + 1
    print('copy actions', n)
    for a, p in log:
        if a == 'replace':
            print('replaced', p)
    print('SUPERSEDED.txt', sha16(os.path.join(sup_dir, 'SUPERSEDED.txt')), 'FILE-INDEX.txt', sha16(os.path.join(vd, 'FILE-INDEX.txt')))


if __name__ == '__main__':
    main(*sys.argv[1:4])
