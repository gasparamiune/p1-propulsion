#!/usr/bin/env python3
"""REV-ELEC-2: per-case comparison of the reviewer chain (rev_fa1_cases.csv) with the author's harness CSV (fa1_overrange_v2p10_cases.csv)
for the no-line head configurations. Usage: python -I compare_author.py <author_csv> <reviewer_csv>"""
import csv, sys, collections
A = list(csv.DictReader(open(sys.argv[1])))
R = list(csv.DictReader(open(sys.argv[2])))
print('author rows', len(A), 'reviewer rows', len(R))
cfgs = collections.Counter((r['node'], r['line'], r['tau_x_ms'], r['vsat']) for r in A)
print('author configurations:', sorted(cfgs.items()))
for tau in ('0.9', '0.1'):
    for vs in ('4.95', '4.74', '4.50', 'none'):
        a = {int(r['case']): r for r in A if r['node'] == 'head' and r['line'] == 'off' and r['tau_x_ms'] == tau and r['vsat'] == vs}
        for adc in ('inst', 'sinc3') + (('inst_noclip_none',) if vs == 'none' else ()):
            rv = {int(r['i']): r for r in R if r['tau_x_ms'] == tau and r['vsat'] == vs and r['adc'] == adc}
            if not a or not rv:
                continue
            dis = collections.Counter(); dmax = collections.defaultdict(float); ex = collections.defaultdict(list)
            for i in a:
                x, y = a[i], rv[i]
                for ka, kr in (('fw30', 'fw30_5'), ('cmp_nom', 'cmp_nom'), ('cmp_lo', 'cmp_lo'), ('fw30_p10', 'fw30_10'), ('fw30_p15', 'fw30_15'),
                               ('cmp_lo_t10', 'cmp_lo_rc10'), ('cmp_lo_t20', 'cmp_lo_rc20')):
                    if int(x[ka]) != int(y[kr]):
                        dis[ka] += 1; ex[ka].append(i)
                if (int(x['n475_ign']) > 0) != (int(y['n475_ign']) > 0):
                    dis['n475_ign'] += 1; ex['n475_ign'].append(i)
                for ka, kr in (('vmax_V', 'vmax_V'), ('raw_pk_bar', 'raw_pk_bar'), ('filt_pk_bar', 'filt_pk_bar'), ('cmp_vmax', 'cmp_vmax'),
                               ('t30f_ms', 't30f_ms'), ('tE2_ms', 'tE2_ms'), ('port_pk_bar', 'head_pk_bar')):
                    dmax[ka] = max(dmax[ka], abs(float(x[ka]) - float(y[kr])))
            print('tau %s vsat %-4s adc %-16s n %d | flag disagreements %s | max |diff| %s | examples %s' % (
                tau, vs, adc, len(a), dict(dis), {k: round(v, 3) for k, v in dmax.items()}, {k: v[:6] for k, v in ex.items()}))
