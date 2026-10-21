#!/usr/bin/env python3
# Electronics v2.12 (2026-10-21): REV-COMB-4 R4-02 / LEAD 258 (3)-(4) / mechanical.json v2.4 requests_v352[4] and how_to_use.
# Re-classification against LC-TB70 v2 (Z3 v2 + Q_JFWD) with Mechanical's inside_v2(t, p) (hub 04-fea/v352/lc_tb70_envelope.py, imported;
# its main() does not run on import) of
#   (a) the 10 S6R runs (fa1rep max_face alone / then 50 bar abs, five builds each): the SIL plant head pressure the Pc chain sees (p_ch,
#       25 us plant step) from the RELIGHT command (vented chamber) to the end of the run (sil s6r with S6R_ONLY=fa1rep_max_face and
#       S6R_TRACE_DIR), and
#   (b) the N-04 burn-on grid cases (grid head peak above the v1 Z3 limit 75.519 bar abs: 46 cases, of which 29-33 abort as built on the
#       four C1 chains and 0 with the ride-through, REV-ELEC-3 N-04): the SIL nominal A1 relight with the ride-through build (sil trace0,
#       25 us, no abort) composed with the Combustion v2.4b grid history from the plant light, p = max(plant, grid) - the S6R replay
#       convention (the chain sees max(plant, profile)); the ride-through build does not abort these cases, so the plant burns on.
# SIM on ASSUMED constructs (Combustion grid, SIL plant); not physical approval. Z3 v2 is NOT EVALUATED in flight (1 kHz record).
# Run: python3 -B -I r4_02_reclass_v2p12.py <s6r_trace_dir> <trace0_dir> <out.json>
import csv, glob, hashlib, importlib.util, json, os, sys
import numpy as np
H = '/home/claude/work/shared-fallback/engine'
E = '/home/claude/work/electronics'
ENV_PY = H + '/04-fea/v352/lc_tb70_envelope.py'
NPZ = H + '/02-combustion/data/v2p4b/fa1_histories_solver_v2p4b.npz'
CSV = E + '/results/fa1_chain_v2p11_cases.csv'
def h16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert h16(ENV_PY) == 'd14489808338006b', h16(ENV_PY)
assert h16(NPZ) == '399bf43d1c09de24', h16(NPZ)
spec = importlib.util.spec_from_file_location('lc_tb70_envelope', ENV_PY)
env = importlib.util.module_from_spec(spec); spec.loader.exec_module(env)

def readTrace(p):
    a = np.loadtxt(p, delimiter=',', skiprows=1)
    return a[:, 0], a[:, 1]

def nat(v):   # numpy scalars / arrays -> Python natives (np.bool_ is not 'is True' and not JSON-serialisable)
    if isinstance(v, np.generic): return v.item()
    if isinstance(v, np.ndarray): return [nat(a) for a in v.tolist()]
    if isinstance(v, (list, tuple)): return [nat(a) for a in v]
    if isinstance(v, dict): return {k: nat(a) for k, a in v.items()}
    return v

def keep(r):
    r = nat(r)
    k = {x: r.get(x) for x in ('inside', 'zone_max', 'peak_bar_abs', 'S_max_0p02_50ms_bar_abs', 'S_max_at_T_ms', 'Q_JFWD_bar_abs',
                               'Q_JFWD_lower_bound_bar_abs', 'jfwd_rule_triggered', 'reasons', 'record_starts_before_light',
                               'light_window_evaluable', 'window_above_63p1_ms', 'rise_10_90_ms')}
    k['excursion_windows'] = len(r.get('excursion_windows', []))
    return k

s6r_dir, t0_dir, out_p = sys.argv[1], sys.argv[2], sys.argv[3]
out = {'script': 'calc/v2p12/r4_02_reclass_v2p12.py', 'date': '2026-10-21',
       'tag': 'DERIVED on SIM (SIL plant / replay traces x Combustion v2.4b grid; Mechanical inside_v2); grid counts on an ASSUMED construct',
       'inputs': {'lc_tb70_envelope.py': 'd14489808338006b', 'fa1_histories_solver_v2p4b.npz': '399bf43d1c09de24', 'fa1_chain_v2p11_cases.csv': h16(CSV)},
       'flight': 'Z3 v2 and Q_JFWD NOT EVALUATED in flight (1 kHz record; the LIGHT_SPIKE raw peak is a lower bound: f3 JFWD_LS indication at 47.5 bar abs)'}
# (a) S6R
rows = []
for p in sorted(glob.glob(os.path.join(s6r_dir, 'S6R_fa1rep_max_face*_head25us.csv'))):
    t, pr = readTrace(p)
    r = env.inside_v2(t, pr)
    dt = float(np.max(np.diff(t)))
    rows.append({'run': os.path.basename(p).replace('_head25us.csv', ''), 'trace_sha16': h16(p), 'n': int(len(t)), 'max_step_ms': round(dt * 1e3, 4),
                 'first_sample_bar_abs': round(float(pr[0]), 4), **keep(r)})
out['S6R'] = rows
out['S6R_summary'] = {'n': len(rows), 'inside': sum(1 for x in rows if x['inside'] is True), 'outside': sum(1 for x in rows if x['inside'] is False),
                      'not_evaluable': sum(1 for x in rows if x['inside'] is None), 'jfwd_rule_triggered': sum(1 for x in rows if x['jfwd_rule_triggered'])}
# (b) N-04 burn-on composition
tj = json.load(open(os.path.join(t0_dir, 'trace0_A1_relight_ride.json')))
tp, pp = readTrace(os.path.join(t0_dir, 'trace0_A1_relight_ride_head25us.csv'))
t_light = float(tj['t_plant_light_s'])
z = np.load(NPZ, allow_pickle=False)
keys, off, ts, ph = z['case_keys'], z['offsets'], z['t_s'], z['P_head_bar']
by = {}
for x in csv.DictReader(open(CSV)): by.setdefault(x['chain'], {})[int(x['case'])] = x
c1 = sorted(c for c in by if c.startswith('c1'))
sel = [i for i in range(len(keys)) if float(ph[off[i]:off[i + 1]].max()) > 75.519]
base = env.inside_v2(tp, pp)
out['trace0'] = {'json': tj, 'plant_trace_sha16': h16(os.path.join(t0_dir, 'trace0_A1_relight_ride_head25us.csv')), 'plant_alone': keep(base)}
nrows = []
for i in sel:
    gt = ts[off[i]:off[i + 1]].astype(float); gp = ph[off[i]:off[i + 1]].astype(float)
    gt = gt - gt[0]
    tg = t_light + gt
    tu = np.union1d(tp, tg[(tg >= tp[0]) & (tg <= tp[-1])])
    pu = np.interp(tu, tp, pp)
    m = (tu >= tg[0]) & (tu <= tg[-1])
    pu[m] = np.maximum(pu[m], np.interp(tu[m], tg, gp))
    r = env.inside_v2(tu, pu)
    asb = {c: int(by[c][i]['fw5']) for c in c1}
    nrows.append({'grid_case': int(i), 'key': str(keys[i]), 'grid_peak_bar_abs': round(float(gp.max()), 3), 'as_built_fw5_abort_by_chain': asb,
                  'ride_fw15_abort_by_chain': {c: int(by[c][i]['fw15']) for c in c1}, **keep(r)})
out['N04_burn_on'] = nrows
out['N04_summary'] = {'n_cases_peak_above_75p519': len(sel),
                      'as_built_abort_counts_by_chain_fw5': {c: sum(r['as_built_fw5_abort_by_chain'][c] for r in nrows) for c in c1},
                      'ride_abort_counts_by_chain_fw15': {c: sum(r['ride_fw15_abort_by_chain'][c] for r in nrows) for c in c1},
                      'inside_v2': sum(1 for r in nrows if r['inside'] is True), 'outside_v2': sum(1 for r in nrows if r['inside'] is False),
                      'not_evaluable': sum(1 for r in nrows if r['inside'] is None),
                      'jfwd_rule_triggered': sum(1 for r in nrows if r['jfwd_rule_triggered']),
                      'Q_JFWD_range_bar_abs': [min(r['Q_JFWD_bar_abs'] for r in nrows if r['Q_JFWD_bar_abs'] is not None),
                                               max(r['Q_JFWD_bar_abs'] for r in nrows if r['Q_JFWD_bar_abs'] is not None)] if nrows else None,
                      'ESP_max_bar_abs': max((r['S_max_0p02_50ms_bar_abs'] or 0) for r in nrows) if nrows else None}
json.dump(nat(out), open(out_p, 'w'), indent=1)
print(json.dumps({k: out[k] for k in ('S6R_summary', 'N04_summary')}, indent=1))
for x in rows: print(x['run'], x['inside'], x['zone_max'], x['S_max_0p02_50ms_bar_abs'], x['S_max_at_T_ms'], x['Q_JFWD_bar_abs'], x['jfwd_rule_triggered'], x['reasons'])
