"""Coast heat into the MV-to-seat segment on CAD v3.4.1 hardware, with and without a 1 mm PTFE lining
(Combustion v2.4, 2026-10-13; coordinator relay "retained vapour is now an integrated trade": re-run on v3.4.1, FS-01A 6061
52.1 g, FD-05 316L 42.1 g, FD-08F 13.5 g, hose 180.25 mm; PTFE lining >= 1 mm as a research option).

Method: Mechanical's own 1-D slab model, imported read-only from 04-fea/thermal/segment_heat_budget.py (v1.1: implicit FD slab
from ignition to RELIGHT, burn = Dittus-Boelter flow h to the liquid temperature of the head-end BC CSV, coast LO h 376 W/m2K or
HI Cooper nucleate boiling capped 20 kW/m2K, cases isothermal / hw+5K / ARM bay 45 C liquid 24 C).  Only the ROUTE elements are
re-defined for v3.4.1; the head end (FE manifold bore, FD-01, TC-02, TC-04, needle) is unchanged hardware and is taken from
segment_heat_budget_v1.json as published.  Validation: the v3.4 route elements re-run with this driver reproduce the published
E_coast values (assert).

v3.4.1 route elements (DERIVED from Mechanical's v3.4.1 BOM and wetted areas, ptfe_lining_estimate_v1 and segment_traps_v341_v1):
  FS-01A module outlet side, 6061, 52.1 g on 2070 mm2 (depth 9.32 mm; Mechanical lumps the whole FS-01A mass on the outlet side);
  FD-08F wall-line flange, 316L, 13.5 g, wetted 300 mm2 ESTIMATE (bore 7.75 mm x ~12 mm; also inside Mechanical's 2070 mm2:
    counted twice, conservative);
  FD-08 wall line 3/8 x 0.035 316L, 278.75 mm, bay air 5 W/m2K (as v3.4);
  FD-07A/B hose-end sleeves, 316L, 2 x 25 g ESTIMATE on 1010 mm2 (replace the -6 JIC ends and the union);
  FD-07 hose 180.25 mm, bore 10.59 mm (15.88 cm3), PTFE liner 1.0 + braid 0.5 equivalent (as v3.4, TO-CONFIRM with the maker);
  FD-05 TEE, 316L, 42.1 g on 496 mm2 (depth 10.61 mm);
  FD-03 riser 3/8 x 0.035 316L, 67.0 mm (bore 3.159 cm3), bay air 5 W/m2K.
Lining option: 1.0 mm PTFE on the wetted face of FS-01A, FD-08F, FD-05 and the sleeves (Mechanical's lined set).
usage: python -I segment_heat_v341_v2p4.py BUDGET_JSON HEADEND_CSV TRAPS_V341_JSON PTFE_JSON OUT_JSON
"""
from __future__ import annotations
import copy, hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
FEA = '/home/claude/work/shared-fallback/engine/04-fea'
sys.path.insert(0, os.path.join(FEA, 'src')); sys.path.insert(0, os.path.join(FEA, 'thermal'))
import segment_heat_budget as SHB   # read-only import (no bytecode written)

LINING_MM = 1.0


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def elements_v341(TR, PT):
    prim = TR['segment_volume_by_primitive_cm3']
    hose_V = prim['FD-07 hose bore']; hose_L = TR['cad']['feed']['hose_len_mm']
    hose_D = 2 * math.sqrt(hose_V * 1e3 / (math.pi * hose_L))
    riser_V = prim['FD-03 riser bore']; riser_L = riser_V * 1e3 / (math.pi / 4 * 7.747 ** 2)
    wall_L = TR['cad']['feed']['wall_len_mm']
    A = PT['area_m2']
    A_mod = A['module outlet side (FS-01A chamber, ports, line passage)'] * 1e6
    A_tee = A['TEE FD-05 bores'] * 1e6
    A_slv = A['hose-end sleeves FD-07A/B'] * 1e6
    d_mod = 52.1 / 2.70 * 1e3 / A_mod          # mm
    d_tee = 42.1 / 8.00 * 1e3 / A_tee
    d_slv = 50.0 / 8.00 * 1e3 / A_slv
    A_08f = 300.0; d_08f = 13.5 / 8.00 * 1e3 / A_08f
    E = [
        dict(key='module', name='FS-01A module outlet side (6061, 52.1 g)', A_mm2=A_mod, layers=[('AL6061-T6', d_mod)], D_mm=10.0, back='adiabatic',
             lined=True, group='upper', tag='DERIVED from Mechanical v3.4.1 BOM / wetted area (ptfe_lining_estimate_v1)'),
        dict(key='fd08f', name='FD-08F wall-line flange (316L, 13.5 g)', A_mm2=A_08f, layers=[('SS316L', d_08f)], D_mm=7.75, back='adiabatic',
             lined=True, group='upper', tag='ESTIMATE wetted area 300 mm2 (also inside the 2070 mm2 module area: counted twice, conservative)'),
        dict(key='wall', name=f'FD-08 wall line 3/8 x 0.035 316L ({wall_L:.2f} mm)', A_mm2=math.pi * 7.747 * wall_L, layers=[('SS316L', 0.889)],
             D_mm=7.75, back=('air', 5.0), lined=False, group='upper', tag='DESIGN length (segment_traps_v341_v1 cad.feed); bay air 5 W/m2K ASSUMED as v3.4'),
        dict(key='sleeves', name='FD-07A/B hose-end sleeves (316L, 2 x 25 g ESTIMATE)', A_mm2=A_slv, layers=[('SS316L', d_slv)], D_mm=10.5,
             back='adiabatic', lined=True, group='hose', tag='Mechanical ESTIMATE mass; wetted area per ptfe_lining_estimate_v1'),
        dict(key='hose', name=f'FD-07 hose {hose_L:.2f} mm, bore {hose_D:.2f} mm, PTFE liner 1.0 + braid 0.5', A_mm2=math.pi * hose_D * hose_L,
             layers=[('PTFE', 1.0), ('SS316L', 0.5)], D_mm=hose_D, back='adiabatic', lined=False, group='hose',
             tag='bore from the 15.88 cm3 voxel volume; liner as v3.4 (TO-CONFIRM with the hose maker)'),
        dict(key='tee', name='FD-05 TEE (316L, 42.1 g)', A_mm2=A_tee, layers=[('SS316L', d_tee)], D_mm=7.75, back='adiabatic', lined=True,
             group='tee', tag='DERIVED from Mechanical v3.4.1 BOM / wetted area'),
        dict(key='riser', name=f'FD-03 riser 3/8 x 0.035 316L ({riser_L:.1f} mm)', A_mm2=math.pi * 7.747 * riser_L, layers=[('SS316L', 0.889)],
             D_mm=7.75, back=('air', 5.0), lined=False, group='trap', tag='length from the 3.159 cm3 voxel bore volume'),
    ]
    return E, dict(hose_D_mm=hose_D, riser_L_mm=riser_L, wall_L_mm=wall_L, depth_mm=dict(module=d_mod, tee=d_tee, sleeves=d_slv, fd08f=d_08f))


def run_el(el, grid, cases, C):
    t_grid, T_liq, mdot, burning, t_meco, t_rel = grid
    out = {'E_coast_J': {}, 'Q_coast_W': {}}
    ts_ = np.arange(t_meco, t_rel + 1e-9, 0.25)
    for cn, T0 in cases.items():
        for mode in ('LO', 'HI'):
            E, qh = SHB.slab(el, t_grid, T_liq, mdot, burning, T0, mode, C)
            qa = np.array(qh)
            out['E_coast_J'][f'{cn}|{mode}'] = round(float(E), 2)
            out['Q_coast_W'][f'{cn}|{mode}'] = [round(float(v), 3) for v in np.interp(ts_, qa[:, 0], qa[:, 1])]
    out['Q_coast_t_s'] = [round(float(v), 2) for v in ts_]
    return out


def main(budget_f, csv_f, traps_f, ptfe_f, out_f):
    import CoolProp.CoolProp as CP
    B = json.load(open(budget_f)); TR = json.load(open(traps_f)); PT = json.load(open(ptfe_f))
    d = np.genfromtxt(csv_f, delimiter=',', names=True, skip_header=1)
    t, b, TL, md = d['t_s'], d['burning'] > 0.5, d['T_N2O_liquid_K'], d['mdot_ox_kg_s']
    on = np.nonzero(b)[0]
    k_meco = on[np.nonzero(np.diff(on) > 1)[0][0]]
    t_meco, t_rel = float(t[k_meco]), float(t[on[np.nonzero(np.diff(on) > 1)[0][0] + 1]])
    assert abs(t_meco - B['t_meco_s']) < 1e-6 and abs(t_rel - B['t_relight_s']) < 1e-6
    sel = t <= t_rel + 1e-9
    t_grid = np.unique(np.concatenate([np.arange(0.0, t_meco, 0.02), np.arange(t_meco, t_rel + 1e-9, 0.05), [t_meco, t_rel]]))
    T_liq = np.interp(t_grid, t[sel], TL[sel]); mdot = np.interp(t_grid, t[sel], md[sel])
    burning = t_grid <= t_meco + 1e-9
    T_sat = float(T_liq[-1]); C, pr = SHB.cooper_C(T_sat)
    T_liq0 = float(T_liq[0])
    cases = {'isothermal': T_liq0, 'hw+5K': T_liq0 + 5.0, 'ARM_bay45C_liq24C': T_liq0 + 21.0}
    grid = (t_grid, T_liq, mdot, burning, t_meco, t_rel)
    # validation: the v3.4 module and TEE elements of the published budget, re-run with this driver
    val = {}
    for el in SHB.ELEMENTS:
        if el['name'] in ('MV/FS-01 module, outlet side (316L body)', 'FD-05 TEE + MSS-1 port (316L)', 'coil hose O3b 0.252 m, PTFE liner 1.0 + SS braid 0.5 (equivalent)'):
            r = run_el(el, grid, cases, C)
            pub = [e for e in B['elements'] if e['name'] == el['name']][0]['E_coast_J']
            val[el['name']] = {k: (r['E_coast_J'][k], pub[k]) for k in pub}
            for k in pub:
                assert abs(r['E_coast_J'][k] - pub[k]) <= 0.002 * abs(pub[k]) + 0.2, (el['name'], k, r['E_coast_J'][k], pub[k])
    E341, geo = elements_v341(TR, PT)
    rows = []
    for el in E341:
        for lin in ((0.0, 1.0) if el['lined'] else (0.0,)):
            e2 = copy.deepcopy(el)
            if lin > 0:
                e2['layers'] = [('PTFE', lin)] + e2['layers']
            r = run_el(e2, grid, cases, C)
            rows.append(dict(key=el['key'], name=el['name'], group=el['group'], lining_mm=lin, A_mm2=round(el['A_mm2'], 1),
                             layers=[(m, round(t_, 3)) for m, t_ in e2['layers']], back=str(el['back']), tag=el['tag'], **r))
            print(f"{el['key']:8s} lin {lin:.1f}", {k: round(v, 1) for k, v in r['E_coast_J'].items()}, flush=True)
    # totals per group and lining
    tot = {}
    for cn in cases:
        for mode in ('LO', 'HI'):
            k = f'{cn}|{mode}'
            for lin in (0.0, 1.0):
                s = {}
                for el in E341:
                    rr = [r for r in rows if r['key'] == el['key'] and (r['lining_mm'] == lin if el['lined'] else True)][0]
                    s[el['key']] = rr['E_coast_J'][k]
                tot[f'{k}|lining{lin:.1f}'] = dict(by_element_J=s, route_total_J=sum(s.values()))
    v34_route = {k: sum(e['E_coast_J'][k] for e in B['elements'] if e['group'] == 'route') for k in B['elements'][0]['E_coast_J']}
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/segment_heat_v341_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={os.path.basename(budget_f): sha16(budget_f), os.path.basename(csv_f): sha16(csv_f), os.path.basename(traps_f): sha16(traps_f),
                       os.path.basename(ptfe_f): sha16(ptfe_f),
                       'segment_heat_budget.py (imported, Mechanical)': sha16(os.path.join(FEA, 'thermal', 'segment_heat_budget.py')),
                       'engmat.py (imported, Mechanical)': sha16(os.path.join(FEA, 'src', 'engmat.py'))},
               t_meco_s=t_meco, t_relight_s=t_rel, coast_s=t_rel - t_meco, T_sat_K=T_sat, cooper_C=C, cases_T0_K=cases, geometry=geo,
               validation_v34_elements=val, elements=rows, totals=tot, v34_route_total_J=v34_route,
               head_end='unchanged hardware: use segment_heat_budget_v1.json head_end_W_vs_t and needle as published',
               tags=dict(model="Mechanical's slab model (imported, unchanged); v3.4.1 element inputs DERIVED/ESTIMATE as listed; h LO/HI bounds as Mechanical",
                         lining='research option: 1.0 mm PTFE, k 0.25 W/mK (LITERATURE-approx, Mechanical POLY table)'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    for k, v in tot.items():
        print(k, 'route %.1f J' % v['route_total_J'], {kk: round(vv, 1) for kk, vv in v['by_element_J'].items()})
    print('v3.4 route totals', {k: round(v, 1) for k, v in v34_route.items()})
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:6])
