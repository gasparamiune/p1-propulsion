#!/usr/bin/env python3
# Electronics v2.12 (2026-10-21), REV-ELEC-3 R3-02 / LEAD 258 (3)-(4): flight J-FWD indication level on the C1 LIGHT_SPIKE raw peak.
# DERIVED on SIM: the C1 chain model (results/fa1_chain_v2p11_cases.csv, build/fa1_chain_v2p11, four C1 chain variants) on the 896-case
# Combustion v2.4b FA-1 grid, against Mechanical's per-case Q_JFWD (04-fea/v352/lc_tb70_envelope_v2.json grid_per_case, inside_v2 on the
# solver histories). Case order: the npz order in both files (checked here: head peak identical for all 896 cases).
# Run: python3 -I jfwd_ls_threshold_v2p12.py <out.json>
import csv, hashlib, json, sys
E = '/home/claude/work/electronics'
H = '/home/claude/work/shared-fallback/engine'
CSV = E + '/results/fa1_chain_v2p11_cases.csv'
ENV = H + '/04-fea/v352/lc_tb70_envelope_v2.json'
LEVEL = 47.5            # bar abs, chosen: 0.25 bar below the lowest C1 raw peak of any Q_JFWD > 60 case over the four C1 chains
Q_RULE = 60.0           # bar abs, jfwd_replace_rule_v2
def h16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
g = json.load(open(ENV))['grid_per_case']
hd = g['header']; rows = g['rows']
iq, ip, ii = hd.index('Q_JFWD'), hd.index('peak'), hd.index('ideal_1kHz_worst')
by = {}
for x in csv.DictReader(open(CSV)): by.setdefault(x['chain'], {})[int(x['case'])] = x
n = len(rows)
assert n == 896 and all(len(v) == n for v in by.values())
Q = [r[iq] for r in rows]
chk = max(abs(float(by[c][i]['head_pk_bar']) - rows[i][ip]) for c in by for i in range(n))
assert chk < 1e-3, chk
out = {'script': 'calc/v2p12/jfwd_ls_threshold_v2p12.py', 'date': '2026-10-21',
       'tag': 'DERIVED on SIM (C1 chain model x FA-1 grid x Mechanical Q_JFWD); grid counts on an ASSUMED construct, not rates; TO-VERIFY (B-PC-1 chain, CF-3 / T1 records)',
       'inputs': {'fa1_chain_v2p11_cases.csv': h16(CSV), 'lc_tb70_envelope_v2.json': h16(ENV)},
       'case_order_check_max_abs_head_peak_diff_bar': chk,
       'n_cases': n, 'n_Q_JFWD_above_60': sum(q > Q_RULE for q in Q), 'n_peak_above_60': sum(r[ip] > Q_RULE for r in rows),
       'level_bar_abs': LEVEL, 'chains': {}}
for c in sorted(by):
    if not c.startswith('c1'): continue
    raw = [float(by[c][i]['raw_pk_bar']) for i in range(n)]
    hi = [raw[i] for i in range(n) if Q[i] > Q_RULE]
    lo = [raw[i] for i in range(n) if Q[i] <= Q_RULE]
    out['chains'][c] = {
        'min_raw_over_Q_above_60_bar_abs': round(min(hi), 3), 'max_raw_over_Q_le_60_bar_abs': round(max(lo), 3),
        'misses_Q_above_60_raw_below_level': sum(1 for v in hi if v < LEVEL),
        'flags_Q_le_60_raw_at_or_above_level': sum(1 for v in lo if v >= LEVEL), 'n_Q_le_60': len(lo),
        'min_raw_all_bar_abs': round(min(raw), 3), 'n_overrange_475': sum(int(by[c][i]['n475']) > 0 for i in range(n))}
ideal = [r[ii] for r in rows]
out['ideal_1kHz_sampler_worst_min_over_Q_above_60_bar_abs'] = round(min(ideal[i] for i in range(n) if Q[i] > Q_RULE), 3)
out['reading'] = ('LEVEL flags every grid case with Q_JFWD > 60 bar abs on all four C1 chain variants (0 misses) and also flags the stated '
                  'number of Q <= 60 cases (conservative: a false flag costs an inspection). It is a LIGHT-WINDOW level only (the LIGHT_SPIKE '
                  'record runs from E1 to E2 + 0.45 s) and sits above MEOP 45 bar abs, so a normal light (Z0, head <= 45 bar abs) does not '
                  'reach it on the chain model. Without the chain (ideal 1 kHz sampler) the lowest Q > 60 case reads the value above: the '
                  'level depends on the C1 chain (seat passage ringing, INA333 / AAF, 4:1 average) and is TO-VERIFY with the B-PC-1 chain.')
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(json.dumps(out, indent=1))
