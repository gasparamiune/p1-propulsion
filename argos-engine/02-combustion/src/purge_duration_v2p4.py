"""Purge duration the hose sweep actually needs, on a 0.1 s grid, and the N2O it vents (Combustion v2.4; coordinator
2026-10-13, relaying Electronics S13: "each pre-scheduled purge uses about 76 g of N2O at 1.0 mm").

Runs retained_vapour_v341_v2p4.main unchanged, on the same inputs (hashes asserted against the trade run
retained_vapour_v341_v2p4.json), with:
  Tp 0.5-2.5 s in 0.1 s steps (the trade used 1.0-4.0 s in 0.5 s steps);
  orifices 0.707 mm (both taps sharing the area of one 1.0 mm restriction equally), 0.8 mm and 1.0 mm per tap;
  tilts 0 and 2 deg (the decision cases; LEAD design attitude theta <= 2 deg), all eight azimuths at 2 deg.
Then, per orifice, tap set and slip bracket: the robust purge time on the fine grid (the smallest Tp from which every longer grid
Tp gives P_abort <= 1e-3 over every heat case, reading, element model and azimuth at 0 and 2 deg), the N2O vented at that time,
and the latest cap clearing time.
Electronics' implementation (electronics.json v2 head_end_bleed_provision): both taps joined at an engine-side tee, one -2 line,
V1 + V2, one restriction downstream of V2, t_purge 2.5 s. Its total flow is that of one 1.0 mm orifice; the split between the
taps is not modelled here. It is bracketed by FD-01 alone at 1.0 mm (all the flow through FD-01) and both taps at 0.707 mm
(equal split); a split that starves FD-01 is outside both brackets.
usage: python -I purge_duration_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import gzip, hashlib, json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import retained_vapour_v341_v2p4 as RV

LIM = 1e-3
CASES = ['isothermal|LO', 'hw+5K|LO', 'ARM_bay45C_liq24C|LO', 'isothermal|HI', 'hw+5K|HI', 'ARM_bay45C_liq24C|HI']


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main(d, out_f):
    base = json.load(open(os.path.join(d, 'retained_vapour_v341_v2p4.json')))
    bi = base['inputs']
    for k in ('segment_heat_v341_v2p4.json', 'relight_vapour_order_v2p4.json', 'coast_migration_v2p4.json', 'start_latency_v2p4.json',
              'post_abort_pocket_v2p4.json'):
        assert sha16(os.path.join(d, k)) == bi[k], k
    files = [bi['mech_budget'], bi['mech_traps_v341'], bi['mech_drain_pose_v341 (workdir)'], bi['mech_bleed_taps_v341 (workdir)'],
             bi['gnc_series'], bi['gnc_relight_attitude_v1']]
    for f in files:
        assert sha16(f['file']) == f['sha256_16'], f['file']
    RV.TP = tuple(round(0.5 + 0.1 * i, 1) for i in range(21))
    RV.ORIF = (0.707, 0.8, 1.0)
    RV.TILTS = (0.0, 2.0)
    raw_f = out_f.replace('.json', '_trade.json')
    RV.main(d, *[f['file'] for f in files], raw_f)
    R = json.load(open(raw_f))
    sf = raw_f.replace('.json', '_summary.json.gz')
    with gzip.open(sf, 'rt') as fh:
        S = json.load(fh)['summary']
    P = lambda k: max(S[k]['P_paused'], S[k]['P_restart'])
    TP = list(RV.TP)
    out = {}
    for o in RV.ORIF:
        for taps in RV.TAPS:
            fk = f'{o}|{taps}'
            sp = R['s_phys'][fk]
            for lin in ('0.0', '1.0'):
                for s_lab in ('scons', 'swall', 's1.0', 's0.5'):
                    worst = {}; n2 = {}; tco = 0.0
                    for Tp in TP:
                        w = 0.0; lo, hi = 1e9, 0.0
                        for m in ('barrier', 'open'):
                            for c in CASES:
                                for tag in ('wet', 'dry'):
                                    for th, azs in ((0.0, (0.0,)), (2.0, RV.AZS)):
                                        for az in azs:
                                            k = f'purge{o}|{taps}|{s_lab}|Tp{Tp}|lin{lin}|{m}|{c}|{tag}|{th}|{az}'
                                            w = max(w, P(k)); lo = min(lo, S[k]['N2O_g'][0]); hi = max(hi, S[k]['N2O_g'][1])
                                            tco = max(tco, S[k]['t_cap_out'][1])
                        worst[f'{Tp}'] = w; n2[f'{Tp}'] = [lo, hi]
                    Tp_r = None
                    for i, Tp in enumerate(TP):
                        if all(worst[f'{x}'] <= LIM for x in TP[i:]):
                            Tp_r = Tp; break
                    out[f'{fk}|lin{lin}|{s_lab}'] = dict(s=(sp['scons'] if s_lab == 'scons' else sp['swall'] if s_lab == 'swall' else float(s_lab[1:])),
                                                        Tp_robust_s=Tp_r, N2O_g_at_Tp_robust=n2[f'{Tp_r}'] if Tp_r else None,
                                                        N2O_g_at_Tp_robust_plus_0p5=n2.get(f'{round(Tp_r + 0.5, 1)}') if Tp_r else None,
                                                        N2O_g_at_2p5s=n2['2.5'], worst_P_by_Tp=worst, N2O_g_by_Tp=n2, t_cap_out_max_s_over_grid=tco)
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/purge_duration_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='coordinator 2026-10-13 (Electronics S13 76 g at 1.0 mm): purge mass at 0.8 vs 1.0 mm for the duration the sweep needs',
               inputs={'retained_vapour_v341_v2p4.json (base trade; input hashes asserted equal)': sha16(os.path.join(d, 'retained_vapour_v341_v2p4.json')),
                       os.path.basename(raw_f): sha16(raw_f), os.path.basename(sf): sha16(sf)},
               grid=dict(Tp_s=TP, orifices_mm=list(RV.ORIF), tilts_deg=list(RV.TILTS), azimuths_deg=list(RV.AZS)),
               flows={k: v for k, v in R['flows'].items()}, s_phys=R['s_phys'], limit=LIM, robust=out,
               electronics_architecture='one 1.0 mm restriction shared by both taps (tee upstream of V1), t_purge 2.5 s: bracketed by 1.0|FD01 and 0.707|2tap',
               tags='DERIVED from the SIM/DERIVED trade model (retained_vapour_v341_v2p4), decision tilts only; worst over the five GNC coast series')
    json.dump(res, open(out_f, 'w'), indent=1, default=float)
    for k, v in out.items():
        if '|lin0.0|' in k:
            n = v['N2O_g_at_Tp_robust']
            print(k, 's', v['s'], 'Tp_r', v['Tp_robust_s'], 'N2O', [round(x, 1) for x in n] if n else None,
                  '+0.5 s', [round(x, 1) for x in v['N2O_g_at_Tp_robust_plus_0p5']] if v['N2O_g_at_Tp_robust_plus_0p5'] else None,
                  '2.5 s', [round(x, 1) for x in v['N2O_g_at_2p5s']], 'tcap %.2f' % v['t_cap_out_max_s_over_grid'])
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])
