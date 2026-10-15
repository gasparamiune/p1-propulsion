#!/usr/bin/env python3
"""REV-ELEC-2: transducer-lag sensitivity of the reviewer FA-1 chain. The M3200 datasheet rise-time row reads '< 2 ms (mV output);
< 3 ms (mA output)' with no row for the 0.5-4.5 V output (TO-VERIFY with TE); tau 1.36 ms gives a 3 ms 10-90 % rise.
Usage: python -I rev_fa1_tau_sens.py <rev_fa1_chain.py> <fa1_envelope_v2p4a.json>"""
import importlib.util, json, sys
import numpy as np
spec = importlib.util.spec_from_file_location('rc', sys.argv[1]); rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
d = json.load(open(sys.argv[2]))
p0 = d['state']['P0_cold_flow_Pa']; grid = np.array(d['history_grid_ms']) * 1e-3; keys = list(d['cases'].keys())
H = np.maximum(np.array([d['cases'][k]['P_head_hist_bar'] for k in keys]) * 1e5, p0)
tpos = np.clip(rc.T, 0.0, grid[-1]); P = np.empty((len(keys), len(rc.T)))
for i in range(len(keys)):
    P[i] = np.interp(tpos, grid, H[i])
P[:, :rc.I0] = H[:, :1]
for tau in (0.00136, 0.0009):
    parts = [rc.run_chunk(P[c:c + 112], tau, 4.95, 'inst') for c in range(0, len(keys), 112)]
    w = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    fw5 = ~np.isnan(w['tfw5']); ign = w['n475_ign'] > 0
    print('tau %.2f ms vsat 4.95 inst: any abort %d | fw30 5 ms %d, 10 ms %d, 15 ms %d | cmp nom %d low %d | >=4.75 V %d | raw pk max %.2f bar | filt pk max %.2f | '
          'longest filtered run above 30 bar %d ms' % (tau * 1e3, int((ign | fw5 | w['cmp_nom']).sum()), int(fw5.sum()), int((~np.isnan(w['tfw10'])).sum()),
          int((~np.isnan(w['tfw15'])).sum()), int(w['cmp_nom'].sum()), int(w['cmp_lo'].sum()), int((w['n475'] > 0).sum()), w['raw_pk'].max() / 1e5,
          w['filt_pk'].max() / 1e5, int(w['maxrun30'].max())))
