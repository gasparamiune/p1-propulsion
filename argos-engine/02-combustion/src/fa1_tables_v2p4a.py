"""Combustion v2.4a: compact FA-1 envelope tables for REPORT v2.4a (§7.6, §9.1) and combustion.json v2.4a.
Reads fa1_envelope_v2p4a.json (hash-asserted) and writes fa1_tables_v2p4a.json plus a markdown snippet file.
No computation beyond max/min/selection over the published cases (DERIVED from SIM).
usage: python -I fa1_tables_v2p4a.py FA1_JSON OUT_JSON OUT_MD
"""
import hashlib, json, sys
src, out_j, out_md = sys.argv[1:4]
h16 = hashlib.sha256(open(src, 'rb').read()).hexdigest()[:16]
assert h16 == '64b328150025fa1e', h16
d = json.load(open(src))
C = d['cases']; E = d['envelope']
GRID = (4.0, 5.0, 6.0, 8.0, 10.0, 12.0)
def sel(**kw):
    out = []
    for k, c in C.items():
        if all((c[a] in b) if isinstance(b, (tuple, list, set)) else c[a] == b for a, b in kw.items()):
            out.append((k, c))
    return out
def mx(rows, f):
    k, c = max(rows, key=lambda x: x[1][f]); return c[f], k
r1 = lambda x: round(x, 1); r2 = lambda x: round(x, 2); r3 = lambda x: round(x, 3)
T = {}
# T1: per reading x entrance, grid O/F 4-12
t1 = []
for init in ('vapour_once', 'as_written'):
    for ent in ('rounded_Cd1.0', 'sharp_Cd0.65'):
        rows = sel(init=init, entrance=ent, OF=GRID)
        ph, kph = mx(rows, 'peak_head_bar'); pa, _ = mx(rows, 'peak_aft_bar')
        a45, _ = mx(rows, 'above45_head_total_ms'); c45, _ = mx(rows, 'above45_head_cont_ms')
        a675, _ = mx(rows, 'above67p5_head_total_ms'); a90, _ = mx(rows, 'above90_head_total_ms')
        imp, _ = mx(rows, 'impulse_above_P0_25ms_head_bar_ms')
        a45a, _ = mx(rows, 'above45_aft_total_ms'); a675a, _ = mx(rows, 'above67p5_aft_total_ms')
        ratio = [min(c['aft_over_head_peak'] for _, c in rows), max(c['aft_over_head_peak'] for _, c in rows)]
        cm = C[kph]
        t1.append(dict(reading=init, entrance=ent, n=len(rows), head_peak_bar=r1(ph), aft_peak_bar=r1(pa),
                       above45_head_ms=r2(a45), above45_head_cont_ms=r2(c45), above67p5_head_ms=r2(a675),
                       above90_head_ms=r2(a90), above45_aft_ms=r2(a45a), above67p5_aft_ms=r2(a675a),
                       impulse_head_bar_ms=round(imp), aft_over_head=[r3(ratio[0]), r3(ratio[1])],
                       governing_case=kph, rise_10_90_ms_at_peak=r2(cm['rise_10_90_head_ms']),
                       t_peak_ms_at_peak=r2(cm['t_peak_head_ms'])))
T['by_reading_entrance_OF4_12'] = t1
# T2: head peak by O/F x tf, baseline (vapour once, rounded) and upper bracket (as written, sharp), max over t_res and pool
t2 = []
for OF in (3.0, 3.5) + GRID:
    row = dict(OF=OF)
    for lab, init, ent in (('baseline', 'vapour_once', 'rounded_Cd1.0'), ('bracket', 'as_written', 'sharp_Cd0.65')):
        row[lab] = [r1(mx(sel(init=init, entrance=ent, OF=OF, tf_ms=float(tf)), 'peak_head_bar')[0]) for tf in range(1, 8)]
    t2.append(row)
T['head_peak_by_OF_tf'] = dict(tf_ms=list(range(1, 8)), rows=t2,
                               note='max over t_res 0.02/0.06 s and pool none/q 2 MW/m2; baseline = vapour once, rounded entrance; bracket = as written, sharp entrance')
# T3: O/F 4 baseline by tf (max over t_res, pool): peak, >45, >67.5, impulse
t3 = []
for tf in range(1, 8):
    rows = sel(init='vapour_once', entrance='rounded_Cd1.0', OF=4.0, tf_ms=float(tf))
    t3.append(dict(tf_ms=tf, head_peak_bar=r1(mx(rows, 'peak_head_bar')[0]), above45_ms=r2(mx(rows, 'above45_head_total_ms')[0]),
                   above67p5_ms=r2(mx(rows, 'above67p5_head_total_ms')[0]), impulse_bar_ms=round(mx(rows, 'impulse_above_P0_25ms_head_bar_ms')[0]),
                   aft_peak_bar=r1(mx(rows, 'peak_aft_bar')[0])))
T['OF4_baseline_by_tf'] = t3
# T4: thrust and SDOF, interim comparison
il = d['interim_load_comparison']
tb = {}
for lab, key in (('baseline_rounded', 'vapour_once|grid_OF4-12|rounded_Cd1.0'), ('vapour_once_all', 'vapour_once|grid_OF4-12|all'),
                 ('both_readings_all', 'both|grid_OF4-12|all')):
    e = E[key]
    tb[lab] = dict(F_peak_Cf1p35_N=round(e['F_peak_Cf1.35_N']['max']), F_peak_QS0p975_N=round(e['F_peak_QSx0.975_N']['max']),
                   F_impulse_25ms_Ns=r1(max(e['F_impulse_25ms_QSx0.975_Ns']['max'], e['F_impulse_25ms_Cf1.35_Ns']['max'])),
                   F_sdof_QS0p975_N_by_period=[round(x) for x in e['F_sdof_QSx0.975_N_max_by_period']],
                   F_sdof_Cf1p35_N_by_period=[round(x) for x in e['F_sdof_Cf1.35_N_max_by_period']],
                   P_head_DLF_by_period=[r3(x) for x in e['P_head_DLF_max_by_period']],
                   P_head_equiv_static_bar_by_period=[r1(x['P_equiv_static_abs_bar']) for x in e['P_head_equiv_static_by_period']],
                   P_aft_equiv_static_bar_by_period=[r1(x['P_equiv_static_abs_bar']) for x in e['P_aft_equiv_static_by_period']])
T['thrust_and_dynamic'] = dict(sdof_periods_thrust_ms=il['sdof_periods_ms'], dlf_periods_pressure_ms=[0.04, 0.1, 0.25, 0.5, 1.0],
                               interim_rect_1p8kN_4ms_sdof_N=[round(x) for x in il['thrust_rect_sdof_N']], readings=tb,
                               head_peak_over_90bar=r3(il['both|grid_OF4-12|all|head_peak_vs_90bar']),
                               aft_peak_over_90bar=r3(il['both|grid_OF4-12|all|aft_peak_vs_90bar']),
                               sdof_QS_over_rect=[r3(x) for x in il['both|grid_OF4-12|all|sdof_QS0.975_over_rect']],
                               F_peak_QS_over_1p8kN=r3(il['both|grid_OF4-12|all|F_peak_QS0.975_vs_1.8kN']))
# check the DLF periods used in the source
md = d['metric_definitions']
T['metric_definitions'] = md
# T5: fuel-basis sensitivity (styrene gas)
fs = d['fuel_basis_sensitivity_styrene_gas']
ratios = [v['ratio'] for v in fs.values() if isinstance(v, dict) and 'ratio' in v]
pk = max((v['peak_head_bar'], k) for k, v in fs.items() if isinstance(v, dict) and 'peak_head_bar' in v)
base_rounded = max((v['peak_head_bar'], k) for k, v in fs.items() if isinstance(v, dict) and 'peak_head_bar' in v and k.startswith('vapour_once|rounded') and ('OF3' not in k.split('|')[2] or k.split('|')[2] in ('OF4',)))
T['fuel_basis_styrene_gas'] = dict(n=len(ratios), ratio_range=[r3(min(ratios)), r3(max(ratios))], max_peak_bar=r2(pk[0]), max_case=pk[1],
                                   baseline_rounded_max_bar=r2(base_rounded[0]), baseline_rounded_case=base_rounded[1])
T['inventory_checks_note'] = 'ig 0.30 s basis; flight_latest light identical peak and impulse; ig 0.05 s about 3.2 bar lower, about half the impulse (inventory_checks in the source)'
T['reviewer_comparison'] = d['reviewer_comparison']
fv = d['fuel_vapour_inventory']
T['fuel_vapour_inventory'] = dict(status=fv['status'], keys=list(fv.keys()))
T['not_modelled'] = d['not_modelled']
res = dict(version='v2.4a', date='2026-10-13', script='02-combustion/src/fa1_tables_v2p4a.py', inputs={'fa1_envelope_v2p4a.json': h16},
           tags='DERIVED selections (max/min) over the SIM cases of fa1_envelope_v2p4a.json (ASSUMED construct)', tables=T)
json.dump(res, open(out_j, 'w'), indent=1)
# markdown snippets
L = []
L.append('T1')
L.append('| Reading | Entrance | Head peak [bar abs] | Aft peak [bar abs] | Above 45 bar, head [ms] (longest continuous) | Above 67.5 bar, head [ms] | Above 90 bar [ms] | Impulse above P0, head, 25 ms [bar ms] | Aft / head peak |')
L.append('|---|---|---|---|---|---|---|---|---|')
for r in t1:
    L.append(f"| {r['reading'].replace('_', ' ')} | {r['entrance'].split('_')[0]} | {r['head_peak_bar']} | {r['aft_peak_bar']} | {r['above45_head_ms']} ({r['above45_head_cont_ms']}) | {r['above67p5_head_ms']} | {r['above90_head_ms']} | {r['impulse_head_bar_ms']} | {r['aft_over_head'][0]}-{r['aft_over_head'][1]} |")
L.append('T2')
L.append('| O/F | ' + ' | '.join(f'tf {tf} ms' for tf in range(1, 8)) + ' |')
L.append('|---|' + '---|' * 7)
for r in t2:
    L.append(f"| {r['OF']:g} | " + ' | '.join(f"{a} / {b}" for a, b in zip(r['baseline'], r['bracket'])) + ' |')
L.append('T3')
for r in t3: L.append(json.dumps(r))
L.append('T4'); L.append(json.dumps(T['thrust_and_dynamic']))
L.append('T5'); L.append(json.dumps(T['fuel_basis_styrene_gas']))
open(out_md, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
