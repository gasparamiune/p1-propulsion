#!/usr/bin/env python3
"""v2.10 item 2 helper: export Combustion's six late-light head-pressure traces (late_light_spike_v2p4.json 'traces', read-only,
sha256/16 57fce738164fd571) to one CSV per trace for spike_chain.cpp. Prints a one-line summary per trace."""
import hashlib, json, os, sys
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
h = hashlib.sha256(open(src, 'rb').read()).hexdigest()[:16]
d = json.load(open(src))
idx = []
for i, (k, v) in enumerate(d['traces'].items()):
    fn = os.path.join(out, f'trace{i}.csv')
    with open(fn, 'w') as f:
        f.write('t_from_light_s,P_head_abs_bar\n')
        for t, p in zip(v['t_from_light_s'], v['P_head_abs_bar']):
            f.write(f'{t:.7f},{p:.5f}\n')
    t, p = v['t_from_light_s'], v['P_head_abs_bar']
    idx.append({'i': i, 'key': k, 'n': len(t), 't0': t[0], 't1': t[-1], 'p_max_bar': max(p)})
    print(f"trace{i} n={len(t)} t {t[0]:+.4f}..{t[-1]:+.4f} s, dt_min {min(b - a for a, b in zip(t, t[1:])):.2e} s, Pmax {max(p):.2f} bar abs | {k}")
json.dump({'source': src, 'source_sha256_16': h, 'traces': idx}, open(os.path.join(out, 'index.json'), 'w'), indent=1)
print('source sha256/16', h)
