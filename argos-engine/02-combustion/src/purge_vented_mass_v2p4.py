"""Vented N2O mass against time over the purge and through the closure, decided path (2 x 0.707 mm, Cd 0.70 ASSUMED), unlined,
theta 0 and 2 deg (Combustion v2.4, 2026-10-13; coordinator after REV-GNC-2 RG-16, CHANGELOG 168).
The mass vented by time t into the flow equals the total of a purge truncated at t (the flow history up to t does not depend on when
the purge ends), so the envelope over every record at Tp = t is the vented-mass envelope at time t. Closure: after the close command the
flow decays over the valve closing time t_c (measured; ASSUMED 0.02-0.05 s here), bounded by the flow at the close command.
usage: python -I purge_vented_mass_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
import hashlib, json, os, sys
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from rg01_line_states_v2p4 import stream_records, sha16
RAW, RAW_SHA = 'purge_duration_v2p4_trade.json.raw.json.gz', '02c30eb2e6569e8d'
d, out = sys.argv[1:3]
assert sha16(os.path.join(d, RAW)) == RAW_SHA
raw = stream_records(os.path.join(d, RAW), ('purge0.707|2tap|',))
G = {}
for k, r in raw.items():
    p = k.split('|')
    Tp, lin, th = float(p[3][2:]), p[4][3:], float(p[9])
    if lin == '0.0' and th in (0.0, 2.0):
        G.setdefault(Tp, []).append(r['N2O_g'])
rows = []
for Tp in sorted(G):
    a = np.array(G[Tp])
    rows.append(dict(t_flow_s=Tp, n=int(a.size), min_g=round(float(a.min()), 2), p50_g=round(float(np.median(a)), 2), p99_g=round(float(np.percentile(a, 99)), 2), max_g=round(float(a.max()), 2)))
for i in range(1, len(rows)):
    dt = rows[i]['t_flow_s'] - rows[i - 1]['t_flow_s']
    rows[i]['max_rate_bound_g_s'] = round(min(31.2416, max(rows[i]['max_g'] - rows[i - 1]['min_g'], 0) / dt), 2)
LIQ, VAP = 31.2416, 2 * 4.2458
res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/purge_vented_mass_v2p4.py',
           script_sha256_16=hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()[:16], inputs={RAW: RAW_SHA},
           path='2 x 0.707 mm restrictors, Cd 0.70 ASSUMED, valves non-controlling; unlined; theta 0 and 2 deg; all slip brackets, heat cases, readings, element models, azimuths and coast series',
           flows_g_s=dict(all_liquid=LIQ, all_vapour=VAP), rows=rows,
           before_first_grid_point='m(t) between 8.49 t (both taps vapour) and 31.24 t (both liquid), g with t in s',
           timeline_rel_E0_s=dict(PURGE_command=-2.90, flow_start=-2.55, flow_end=-0.05, note='MV ramp 0.35 s with the bleeds closed to flow; t_flow = t - (E0 - 2.55)'),
           closure=dict(t_close_s_ASSUMED=[0.02, 0.05], added_g_max=[round(LIQ * 0.02, 2), round(LIQ * 0.05, 2)],
                        note='the close command leads the flow end by the measured closing time, so the scheduled 2.5 s already contains the closing transient; '
                             'if the closing time is not subtracted, add at most 31.24 g/s x t_close'),
           stuck_open='after a failed closure the flow continues at <= 31.24 g/s (both taps liquid) until landing or MV closure',
           tags='SIM (purge_duration_v2p4 trade records) on ASSUMED Cd and slip brackets; closure DERIVED')
json.dump(res, open(out, 'w'), indent=1)
for r in rows:
    print(r)
print(sha16(out))
