"""Electronics v2.11 (2026-10-21), LEAD CHANGELOG 203 (7) 'gen_tables is re-run on v2.4b': leaf diff of every combustion.json subtree
firmware/tools/gen_tables.py v3.3 reads, v2.3 (d9ec54fbf450e243, the source of the generated headers) against v2.4b (interfaces/combustion.json),
plus the v3.3 start-sequence step parse (find_step regexes) on both. Output: results/gen_tables_v2p4b_leafdiff_v1.json. DERIVED (file
comparison); no header is regenerated here."""
import json, sys, hashlib, os
ER = '/home/claude/work/shared-fallback/engine'
A = json.load(open(ER + '/02-combustion/data/v2/combustion_interface_v2p3_as_published.json'))
B = json.load(open(ER + '/interfaces/combustion.json'))
PATHS = ['gas_path.nozzle.throat_area_m2', 'gas_path.nozzle.expansion_ratio', 'gas_path.grain.port.initial_diameter_m',
         'gas_path.grain.regression_law', 'gas_path.grain.density_kg_m3', 'gas_path.grain.length_m',
         'gas_path.injector.seat_diameter_m', 'gas_path.injector.Cd', 'gas_path.overall.free_chamber_volume_initial_m3',
         'operating_points.throttle_points_20C_initial_port', 'operating_points.max_thrust', 'operating_points.pressure_limits',
         'operating_points.tank_MEOP_Pa', 'operating_points.floor_stretch_12p5pct', 'operating_points.thrust_ceiling_rule',
         'operating_points.throttle_map_csv', 'valves_and_actuators.pintle_actuator.stroke_m',
         'valves_and_actuators.isolation_valve.close_time_max_s', 'valves_and_actuators.plant_model_valve_to_Pc',
         'igniter.sequence', 'igniter.electrical', 'igniter.spark', 'decisions.N2O_load_and_tank']
def get(d, p):
    for k in p.split('.'):
        if not isinstance(d, dict) or k not in d: return '<absent>'
        d = d[k]
    return d
def leaves(x, pre=''):
    if isinstance(x, dict):
        for k, v in x.items(): yield from leaves(v, pre + '.' + k if pre else k)
    elif isinstance(x, list):
        for i, v in enumerate(x): yield from leaves(v, '%s[%d]' % (pre, i))
    else: yield pre, x
out = {'a': ['v2.3', A.get('version'), 'd9ec54fbf450e243'], 'b': [B.get('version'), hashlib.sha256(open(ER + '/interfaces/combustion.json','rb').read()).hexdigest()[:16]], 'paths': {}}
for p in PATHS:
    a, b = get(A, p), get(B, p)
    la, lb = dict(leaves(a)), dict(leaves(b))
    num, txt, tag = [], [], []
    for k in sorted(set(la) | set(lb)):
        va, vb = la.get(k, '<absent>'), lb.get(k, '<absent>')
        if va == vb: continue
        rec = [k, va, vb]
        if k.endswith('tag') or '.tag' in k or k.endswith('note') or k.endswith('source'): tag.append(rec)
        elif isinstance(va, (int, float)) and isinstance(vb, (int, float)): num.append(rec)
        else: txt.append(rec)
    out['paths'][p] = {'numeric_changes': num, 'text_changes': txt, 'tag_changes': len(tag), 'n_leaves_a': len(la), 'n_leaves_b': len(lb)}
# throttle map file
def mapf(C):
    m = get(C, 'operating_points.throttle_map_csv'); m = m['v'] if isinstance(m, dict) and 'v' in m else m
    fn = m if os.path.exists(m) else os.path.join(ER, m.split('/engine/', 1)[1]) if '/engine/' in m else m
    return fn, (hashlib.sha256(open(fn,'rb').read()).hexdigest()[:16] if os.path.exists(fn) else 'MISSING')
out['throttle_map'] = {'v2.3': mapf(A), 'v2.4b': mapf(B)}
import re
STEPS = ['pintle to the ignition lift', 'open torch solenoids', 'spark train', 'torch-flame confirmation', 'ignition check',
         'ramp to the commanded thrust', 'propane solenoid closed', 'N2O torch solenoid closed', 'bleed lift']
def parse(C):
    s = get(C, 'igniter.sequence'); s = s['v'] if isinstance(s, dict) and 'v' in s else s
    return {p: any(re.search(p, st['action'], re.I) for st in s['start']) for p in STEPS}
out['v3p3_step_parse_found'] = {'v2.3': parse(A), 'v2.4b': parse(B)}
nn = sum(len(r['numeric_changes']) for k, r in out['paths'].items() if k != 'igniter.sequence')
out['summary'] = {'numeric_changes_outside_igniter_sequence': nn,
                  'igniter_sequence_numeric_changes': len(out['paths']['igniter.sequence']['numeric_changes']),
                  'v3p3_parse_fails_on_v2p4b': not all(out['v3p3_step_parse_found']['v2.4b'].values()),
                  'throttle_map_same_file': out['throttle_map']['v2.3'][1] == out['throttle_map']['v2.4b'][1]}
json.dump(out, open('/home/claude/work/electronics/results/gen_tables_v2p4b_leafdiff_v1.json', 'w'), indent=1, default=str)
print(json.dumps(out['summary']), json.dumps(out['v3p3_step_parse_found']['v2.4b']))
