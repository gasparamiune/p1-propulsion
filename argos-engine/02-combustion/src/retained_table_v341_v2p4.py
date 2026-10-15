"""Tables for the v3.4.1 retained-vapour trade (Combustion v2.4, 2026-10-13).

Reads retained_vapour_v341_v2p4.json (summary: max over the five GNC coast series) and writes:
  A. combinations (1) re-route only and (2) + PTFE lining, no purge: P_abort at W 0.65 s per heat case, reading (wet / dry)
     and relight tilt (worst azimuth), worst of the two element models and of the two slug conventions, with the failure mode
     (void at the seat beyond the zero-abort slug, or a vapour gap behind a short slug);
  B. combinations (3) + purge and (4) + lining + purge, per orifice (0.8, 1.0 mm), tap set (both taps; FD-01 alone) and cap
     slip s: the robust purge time Tp_r (smallest grid time from which every longer grid time gives P_abort <= 1e-3 in every
     heat case, reading, element model and azimuth at that tilt), the cap clearing time and the N2O vented;
  D. the decision view (LEAD 2026-10-13: design attitude theta <= 2 deg, vent balanced or axial): worst over 0 and 2 deg;
  C. hump-sweep check (minimum column flow while hump vapour remained) and the annulus-venting sensitivity.
P_abort = max(P_paused, P_restart).  Slip labels (see the trade file): scons (hose downslope or wall line, conservative), swall
(wall line only: design-attitude estimate), s1.0 and s0.5 brackets; at 0 and 2 deg every label at every azimuth, at 4, 10 and
20 deg scons at every azimuth and the other labels at az 45 (worst hump direction).
usage: python -I retained_table_v341_v2p4.py RETAINED_JSON OUT_JSON
"""
from __future__ import annotations
import gzip, hashlib, json, os, sys
sys.dont_write_bytecode = True

CASES = [('isothermal|LO', 'iso LO'), ('hw+5K|LO', 'hw LO'), ('ARM_bay45C_liq24C|LO', 'ARM LO'),
         ('isothermal|HI', 'iso HI'), ('hw+5K|HI', 'hw HI'), ('ARM_bay45C_liq24C|HI', 'ARM HI')]
AZ = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)
TILTS = (0.0, 2.0, 4.0, 10.0, 20.0)
DECISION = (0.0, 2.0)
MODELS = ('barrier', 'open')
ORIF = ('0.8', '1.0')
TAPS = ('2tap', 'FD01')
LIM = 1e-3


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def main(rf, out_f):
    R = json.load(open(rf)); sp = R['s_phys']; TP = [float(x) for x in R['constants']['TP']]
    sf = os.path.join(os.path.dirname(rf), os.path.basename(rf).replace('.json', '_summary.json.gz'))
    with gzip.open(sf, 'rt') as fh:
        S = json.load(fh)['summary']
    assert sha16(sf) == R['summary_file_sha256_16']
    Vz = R['constants']['V_zero_abort_cm3']
    P = lambda k: max(S[k]['P_paused'], S[k]['P_restart'])
    azs = lambda th: (0.0,) if th == 0.0 else AZ
    # ---------------------------------------------------------------- A: no purge
    A = {}
    for lin in ('0.0', '1.0'):
        for th in TILTS:
            for c, lab in CASES:
                for tag in ('wet', 'dry'):
                    keys = [f'nopurge|lin{lin}|{m}|{c}|{tag}|{th}|{az}' for m in MODELS for az in azs(th)]
                    v = max(P(k) for k in keys)
                    kw = max(keys, key=P)
                    s_ = S[kw]
                    mode = 'pass' if v <= LIM else ('void at the seat > zero-abort slug' if s_['P1'][1] > Vz else 'vapour gap behind a short slug')
                    A[f'lin{lin}|{th}|{lab}|{tag}'] = dict(P_abort=v, mode=mode, worst_key=kw, P1_cm3=s_['P1'], cap_cm3=s_['cap'], C1_cm3=s_['C1'])
    # ---------------------------------------------------------------- B: purge
    B = {}
    for o in ORIF:
        for taps in TAPS:
            fk = f'{o}|{taps}'
            for lin in ('0.0', '1.0'):
                for s_lab, s in (('scons', sp[fk]['scons']), ('swall', sp[fk]['swall']), ('s1.0', 1.0), ('s0.5', 0.5)):
                    for th in TILTS:
                        az_set = azs(th) if (s_lab == 'scons' or th in DECISION) else (45.0,)
                        ok, worst_by_Tp, tco, n2 = [], {}, [1e9, -1e9], {}
                        for Tp in TP:
                            worst = 0.0
                            for m in MODELS:
                                for c, lab in CASES:
                                    for tag in ('wet', 'dry'):
                                        for az in az_set:
                                            k = f'purge{o}|{taps}|{s_lab}|Tp{Tp}|lin{lin}|{m}|{c}|{tag}|{th}|{az}'
                                            worst = max(worst, P(k))
                                            if Tp == TP[-1]:
                                                tco = [min(tco[0], S[k]['t_cap_out'][0]), max(tco[1], S[k]['t_cap_out'][1])]
                                            nn = S[k]['N2O_g']; cur = n2.get(f'{Tp}', [1e9, 0.0])
                                            n2[f'{Tp}'] = [min(cur[0], nn[0]), max(cur[1], nn[1])]
                            ok.append(worst <= LIM); worst_by_Tp[f'{Tp}'] = worst
                        Tp_r = None
                        for i, Tp in enumerate(TP):
                            if all(ok[i:]):
                                Tp_r = Tp; break
                        B[f'{fk}|lin{lin}|{s_lab}|{th}'] = dict(s=s, Tp_robust_s=Tp_r, worst_P_by_Tp=worst_by_Tp, t_cap_out_s_at_Tp_max=tco,
                                                               N2O_g_by_Tp=n2, N2O_g_at_Tp_robust=n2[f'{Tp_r}'] if Tp_r else None, azimuths=list(az_set))
    # ---------------------------------------------------------------- D: decision view (worst over 0 and 2 deg)
    D = {}
    for o in ORIF:
        for taps in TAPS:
            for lin in ('0.0', '1.0'):
                for s_lab in ('scons', 'swall', 's1.0', 's0.5'):
                    rows = [B[f'{o}|{taps}|lin{lin}|{s_lab}|{th}'] for th in DECISION]
                    tps = [r['Tp_robust_s'] for r in rows]
                    Tp_r = None if any(t is None for t in tps) else max(tps)
                    n = None
                    if Tp_r is not None:
                        n = [min(r['N2O_g_by_Tp'][f'{Tp_r}'][0] for r in rows), max(r['N2O_g_by_Tp'][f'{Tp_r}'][1] for r in rows)]
                    D[f'{o}|{taps}|lin{lin}|{s_lab}'] = dict(Tp_robust_s=Tp_r, N2O_g_at_Tp_robust=n,
                                                             t_cap_out_max_s=max(r['t_cap_out_s_at_Tp_max'][1] for r in rows))
    # ---------------------------------------------------------------- C: hump sweep and annulus sensitivity
    C = {}
    for o in ORIF:
        for taps in TAPS:
            pre = f'purge{o}|{taps}|'
            qm = min(v.get('Qcol_min_while_humps_cm3_s', 1e9) for k, v in S.items() if k.startswith(pre))
            ann = max(max(v['P_paused_annvent'], v['P_restart_annvent']) - max(v['P_paused'], v['P_restart'])
                      for k, v in S.items() if k.startswith(pre))
            C[f'{o}|{taps}'] = dict(Qcol_min_while_hump_vapour_present_cm3_s=qm, max_P_change_if_annulus_vents=ann)
    C['hump_sweep_min_column_flow_cm3_s'] = R['constants']['hump_sweep_min_column_flow_cm3_s']
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/retained_table_v341_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={'retained_vapour_v341_v2p4.json': sha16(rf), 'retained_vapour_v341_v2p4_summary.json.gz': sha16(sf)}, limit=LIM, V_zero_abort_cm3=Vz, s_phys=sp, Tp_grid_s=TP, flows=R['flows'],
               design_attitude=R.get('design_attitude'), decision_tilts_deg=DECISION, humps_cm3=R['humps_cm3'],
               A_no_purge=A, B_purge=B, D_decision=D, C_checks=C,
               tags='DERIVED from the SIM/DERIVED trade file; worst over the five GNC coast series, both element models, both slug conventions')
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    # ---------------------------------------------------------------- print
    f = lambda x: '0' if x == 0 else ('%.0e' % x if x < 0.01 else '%.2f' % x)
    print('A. no purge: P_abort (worst model, az, convention); columns', ' '.join(f'{lab}:w/d' for _, lab in CASES))
    for lin in ('0.0', '1.0'):
        for th in TILTS:
            print(f"({'2' if lin == '1.0' else '1'}) tilt {th:4.0f} | " + ' | '.join(f"{f(A[f'lin{lin}|{th}|{lab}|wet']['P_abort'])}/{f(A[f'lin{lin}|{th}|{lab}|dry']['P_abort'])}" for _, lab in CASES))
    print('A modes at 2 deg:', {k: v['mode'] for k, v in A.items() if '|2.0|' in k and v['mode'] != 'pass'})
    print('B. purge: Tp_robust (s) by tilt', TILTS, '[N2O g at Tp_r] tc = max cap clearing time')
    for o in ORIF:
        for taps in TAPS:
            for lin in ('0.0', '1.0'):
                for s_lab in ('scons', 'swall', 's1.0', 's0.5'):
                    row = []
                    for th in TILTS:
                        b = B[f'{o}|{taps}|lin{lin}|{s_lab}|{th}']
                        n = b['N2O_g_at_Tp_robust']
                        row.append(f"{b['Tp_robust_s']} [{n[0]:.0f}-{n[1]:.0f}] tc{b['t_cap_out_s_at_Tp_max'][1]:.2f}" if n else 'None')
                    print(f"({'4' if lin == '1.0' else '3'}) {o} {taps:4s} {s_lab:6s} | " + ' | '.join(row))
    print('D. decision (0 and 2 deg):')
    for k, v in D.items():
        print('  ', k, v)
    print('C.', json.dumps(C, default=float))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])
