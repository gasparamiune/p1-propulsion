#!/usr/bin/env python3
"""REV-ELEC-4 E4-02: k-dependent coefficient tolerance for the stand relight after a B1-length burn (and the A1 relight), from the
reviewer drift re-derivation data/r4_01_c1_drift_v2.json (same worst-case linear model as scripts/r4_01_c1_drift_v2.py: residual =
eps k c rise F + k c (|grad| + tau |rate| + TC err), c 0.0248 bar/K [DATASHEET typical], F 1.0166 (T0 0 C) [DERIVED, T_aw ASSUMED],
tau 0.25 s and TC err 0.30 K ASSUMED, adders 0.1012 bar = the author's zero drift 0.05 ASSUMED + outgassing 0.05 DESIGN + noise 0.0012
DERIVED) plus the reviewer SIL F3 points (run/rv/f3/S13T_seat_drift_bpc1_false.json). eps = relative coefficient error (fit or
loaded value vs the true slope). Gates: re-zero2 / re-zero1 accepted when the shift <= 0.30 bar (kPcRezeroMax); the relight
NOT_VENTED check <= 0.10 bar against the latest accepted zero (no adders: the TC error is common to the zero and the check).
usage: python3 -I e4_02_eps_table.py <r4_01_json> <f3_json> <out.json>"""
import hashlib, json, sys
src, f3p, outp = sys.argv[1:4]
d = json.load(open(src)); f3 = json.load(open(f3p))
h16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
C, F, TAU, TCE, LIM, ADD, NV = 0.0248, 1.0166, 0.25, 0.30, 0.30, 0.1012, 0.10
rise, grad, rate = d['rise_K_diaphragm'], d['gradient_K_sensor_minus_diaphragm'], d['diaphragm_rate_K_per_s']
ST = ('B1_R4_GVHI', 'B1_R4_GVLO')
def eps_gate(rn, ev, k, add):
    a = k * C; cst = a * (abs(grad[rn][ev]) + TAU * abs(rate[rn][ev]) + TCE)
    return (LIM - add - cst) / (a * rise[rn][ev] * F)
def eps_nv(rn, z, k):
    a = k * C; dr = rise[rn]['E1'] - rise[rn][z]
    cst = a * (abs(grad[rn]['E1'] - grad[rn][z]) + TAU * abs(rate[rn]['E1'] - rate[rn][z]))
    return (NV - cst) / (a * F * dr)
out = {'script': 'e4_02_eps_table.py (REV-ELEC-4)', 'inputs': {'r4_01_c1_drift_v2.json': h16(src), 'S13T_rv_f3.json': h16(f3p)},
       'tag': 'DERIVED (worst-case linear sum) on SIM seat histories x DATASHEET typical coefficient; tau, TC err, adders ASSUMED/DESIGN; a negative value = gate not closable at that k even with an exact coefficient',
       'rows': []}
for k in (1.0, 1.25, 1.5, 2.0, 2.5, 3.0):
    r = {'k': k}
    r['stand_rz2_eps_max_with_adders_pct'] = round(100 * min(eps_gate(s, 'rz2', k, ADD) for s in ST), 2)
    r['stand_rz2_eps_max_without_adders_pct'] = round(100 * min(eps_gate(s, 'rz2', k, 0.0) for s in ST), 2)
    r['stand_rz1_eps_max_with_adders_pct'] = round(100 * min(eps_gate(s, 'rz1', k, ADD) for s in ST), 2)
    r['stand_rz1_eps_max_without_adders_pct'] = round(100 * min(eps_gate(s, 'rz1', k, 0.0) for s in ST), 2)
    r['stand_NV_vs_rz2_eps_max_pct'] = round(100 * min(eps_nv(s, 'rz2', k) for s in ST), 2)
    r['stand_NV_vs_rz1_eps_max_pct'] = round(100 * min(eps_nv(s, 'rz1', k) for s in ST), 2)
    r['A1_rz2_eps_max_with_adders_pct'] = round(100 * eps_gate('A1_NF2b', 'rz2', k, ADD), 2)
    r['A1_rz2_eps_max_without_adders_pct'] = round(100 * eps_gate('A1_NF2b', 'rz2', k, 0.0), 2)
    out['rows'].append(r)
sil = {}
for c in f3['cases']:
    key = '%s_k%.1f' % (c['comp'], c['k'])
    sil.setdefault(key, []).append('%s s%+d rz1 %d rz2 %d %s' % (c['location'].replace('stand_after_B1_', ''), c['sign'], c['rezero1'], c['rezero2'], c['outcome']))
out['SIL_F3_points'] = {'tag': 'SIM (reviewer SIL variant fw_rv, author v2.12 code; no adders; stand after B1, T0 24 C)',
                        'comp_names': 'rv_m5_tcm eps -5 % TC -0.3 K; rv_m5_tc0 -5 % 0 K; rv_m4_tcm -4 % -0.3 K; rv_m3_tcm -3 % -0.3 K; rv_p5_tcp +5 % +0.3 K', 'by_comp_k': sil}
json.dump(out, open(outp, 'w'), indent=1)
for r in out['rows']: print(r)
