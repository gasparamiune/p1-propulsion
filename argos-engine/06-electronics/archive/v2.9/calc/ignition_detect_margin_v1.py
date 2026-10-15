"""Light-detection margin at the v2.8 ignition lift (Electronics, 2026-10-13, v1).

Finding that triggered it: the SIL S5 dispersed pad-start Monte Carlo (300 runs) shows 31 NO_IGNITION aborts from firmware v2.8.1 on
(v2.7: 0), all on a LIT plant. This script replays every S5 run of the v2.8.3 record (`sil mcone`, same seeds as results/sil_v2p8_3/S5_mc.csv)
and extracts the plant chamber pressure 30 ms after the plant light, i.e. the lit plateau at the ignition lift, against the light-detection
threshold kIgnitionDetectAbs_Pa (engine_params.h, from combustion.json). SIL plant on ASSUMED/COMB bands: a margin indication, not
hardware evidence (IGN-1, T1 measure the real lit Pc at the ignition lift).
Writes results/ignition_detect_margin_v1.json; replay CSVs go to a scratch folder and are deleted after reading.
"""
import csv, json, os, re, subprocess, sys, hashlib, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
SIL = os.path.join(ROOT, 'firmware', 'build', 'sil')
OUT = tempfile.mkdtemp(prefix='ign_margin_')
S5 = os.path.join(ROOT, 'results', 'sil_v2p8_3', 'S5_mc.csv')
rows = list(csv.DictReader(open(S5)))
def sha16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
ep = open(os.path.join(ROOT, 'firmware', 'src', 'core', 'engine_params.h')).read()
m = re.search(r'kIgnitionPcAbs_Pa\s*=\s*([0-9.eE+-]+)f?;', ep)
THR = float(m.group(1)) / 1e5 if m else None
cfgh = open(os.path.join(ROOT, 'firmware', 'src', 'core', 'config.h')).read()
m2 = re.search(r'kIgnLiftTab_m\[kIgnLiftN\] = \{([^}]*)\}', cfgh)
LIFT = m2.group(1).strip() if m2 else None
idx = [int(r['run']) for r in rows]          # all runs
res = []
for k in idx:
    f = os.path.join(OUT, 'S5_mc_run%d.csv' % k)
    if not os.path.exists(f):
        subprocess.run(['nice', '-n', '10', SIL, 'mcone', OUT, str(k)], stdout=subprocess.DEVNULL, check=True)
    t_light = None; t_lift = None; plateau = []; t_end = None; ab = 0
    for r in csv.DictReader(open(f)):
        t = float(r['t'])
        if t < 1.40: continue
        if t_lift is None and float(r['ign_lift_t']) >= 0: t_lift = 1.40 + float(r['ign_lift_t'])
        if t_light is None and r['ignited'] == '1': t_light = t
        st = int(r['state'])
        if st != 3 and t_end is None and t > 1.41:
            t_end = t; ab = int(r['abort'])
        if t_light is not None and t_end is None and t >= t_light + 0.030:
            plateau.append(float(r['Pc']))
    rec = {'run': k, 'abort': int(rows[k]['abort']), 'Cd_scale': float(rows[k]['Cd_scale']), 'reg_scale': float(rows[k]['reg_scale']),
           'eta_scale': float(rows[k]['eta_scale']), 'T_tank0': float(rows[k]['T_tank0']),
           'lit_pc_first_bar_abs': plateau[0] / 1e5 if plateau else None, 'lit_pc_max_in_ignition_bar_abs': max(plateau) / 1e5 if plateau else None,
           'light_after_lift_s': (t_light - t_lift) if (t_light and t_lift) else None, 'ignition_end_s': t_end}
    res.append(rec)
    os.remove(f)
first = [r['lit_pc_first_bar_abs'] for r in res if r['lit_pc_first_bar_abs'] is not None]
first.sort()
q = lambda p: first[min(len(first) - 1, int(p * (len(first) - 1) + 0.5))]
summ = {'n': len(res), 'n_no_ignition': sum(r['abort'] == 3 for r in res),
        'lit_pc_30ms_after_light_bar_abs': {'min': first[0], 'p05': q(0.05), 'p50': q(0.5), 'p95': q(0.95), 'max': first[-1]},
        'frac_below_threshold': sum(1 for x in first if x < THR) / len(first), 'runs': res}
summ = {'id': 'ignition_detect_margin', 'version': 'v1', 'date': '2026-10-13', 'script': 'calc/ignition_detect_margin_v1.py',
        'inputs': {'S5_mc.csv': [os.path.relpath(S5, ROOT), sha16(S5)], 'sil_binary': [os.path.relpath(SIL, ROOT), sha16(SIL)],
                   'engine_params.h': sha16(os.path.join(ROOT, 'firmware', 'src', 'core', 'engine_params.h'))},
        'light_threshold_bar_abs': {'v': THR, 'tag': 'COMB v2.1 via engine_params.h kIgnitionPcAbs_Pa'},
        'ignition_lift_table_m': {'v': LIFT, 'tag': 'LEAD 2026-10-13 v2.8 default (config.h kIgnLiftTab_m)'},
        **summ,
        'limitations': ['SIL plant (ASSUMED c*, regression, Cd, combustion-delay bands), one seed per run, no sensor bias (S9 covers bias)',
                        'lit plateau = plant Pc 30 ms after the plant light, inside the IGNITION state; hardware evidence: IGN-1 / T1']}
json.dump(summ, open(os.path.join(ROOT, 'results', 'ignition_detect_margin_v1.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in summ.items() if k != 'runs'}, indent=1))
