#!/usr/bin/env python3
# REV-ELEC-4: independent inside_v2 call (Mechanical's classifier, hub 04-fea/v352/lc_tb70_envelope.py, imported by path) on the
# reviewer's re-run 25 us head traces (S6R max-face, trace0). Run: python3 -I r4_02_check.py <out.json>
import csv, hashlib, importlib.util, json, sys
H = '/home/claude/work/shared-fallback/engine'
P = H + '/04-fea/v352/lc_tb70_envelope.py'
assert hashlib.sha256(open(P, 'rb').read()).hexdigest()[:16] == 'd14489808338006b'
spec = importlib.util.spec_from_file_location('lc_env', P); env = importlib.util.module_from_spec(spec); spec.loader.exec_module(env)
A = '/dev/shm/rev_elec4/run/a'
runs = ['s6r_traces/S6R_fa1rep_max_face_alone_control__as_built_head25us.csv', 's6r_traces/S6R_fa1rep_max_face_alone_control__ride_head25us.csv',
        's6r_traces/S6R_fa1rep_max_face_then_plateau_50bar__as_built_head25us.csv', 's6r_traces/S6R_fa1rep_max_face_then_plateau_50bar__ride_tauMax_bandHigh_head25us.csv',
        'trace0/trace0_A1_relight_ride_head25us.csv']
out = {'classifier': 'lc_tb70_envelope.py d14489808338006b', 'tag': 'DERIVED on SIM (reviewer re-run traces)', 'runs': []}
for r in runs:
    p = A + '/' + r
    t, pr = [], []
    for row in csv.DictReader(open(p)):
        t.append(float(row['t_s'])); pr.append(float(row['p_bar_abs']))
    res = env.inside_v2(t, pr)
    keep = {k: res.get(k) for k in ('inside', 'zone_max', 'peak_bar_abs', 'Q_JFWD_bar_abs', 'jfwd_rule_triggered', 'S_max_0p02_50ms_bar_abs')}
    keep['trace'] = r; keep['sha16'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
    out['runs'].append(keep); print(keep)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
