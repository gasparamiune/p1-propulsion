"""Forced-purge sizing table for the A1 relight provision (Combustion v2.4, 2026-10-13; coordinator ask (a)).

Reads purge_sizing_v2p4.json (plug flow) and purge_slip_v2p4.json (cap transport ratio s = 1, 0.5, 0.25, 0) and tabulates,
per orifice (0.6, 0.8 mm), heat case (isothermal, hot wall +5 K, ARM 45 C bay / 24 C liquid; LO and HI) and reading (wet, dry):
  - Tp_robust: the smallest grid purge time from which every longer grid time gives P_abort 0 at W 0.65 s
    (both slug conventions, all five GNC coast series), config A (re-routed trap 13.53 cm3 + 1.08 cm3 dead ends);
  - N2O used (vented overboard) at that time and at 2.0 / 3.0 s, min-max over the series.
The purge ends at E0 ('E0' end) unless stated: the lead requires the bleed confirmed closed before the lift.
usage: python -I purge_table_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import hashlib, json, os, sys
sys.dont_write_bytecode = True

CASES = [('isothermal|LO', 'iso LO'), ('isothermal|HI', 'iso HI'), ('hw+5K|LO', 'hw LO'), ('hw+5K|HI', 'hw HI'),
         ('ARM_bay45C_liq24C|LO', 'ARM LO'), ('ARM_bay45C_liq24C|HI', 'ARM HI')]
TP = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def robust(ok):
    for i, Tp in enumerate(TP):
        if all(ok[i:]):
            return Tp
    return None


def main(d, out_f):
    fs = os.path.join(d, 'purge_sizing_v2p4.json'); fl = os.path.join(d, 'purge_slip_v2p4.json')
    PSZ = json.load(open(fs))['summary']
    SLP = json.load(open(fl))
    SS = SLP['summary']; slips = [float(x) for x in SLP['slips']]
    rows = {}
    for orif in ('0.6', '0.8'):
        for case, lab in CASES:
            for end in ('E0', 'lift'):
                r = {}
                for tag in ('wet', 'dry'):
                    zero = lambda Tp, s: (SS[f'{orif}|{case}|A|{tag}|Tp{Tp}|{end}|s{s}']['P_restart'][1] == 0.0 and
                                          SS[f'{orif}|{case}|A|{tag}|Tp{Tp}|{end}|s{s}']['P_paused'][1] == 0.0)
                    plug_ok = [PSZ[f'{orif}|{case}|A|{tag}|Tp{Tp}|{end}']['P_restart'][1] == 0.0 and
                               PSZ[f'{orif}|{case}|A|{tag}|Tp{Tp}|{end}']['P_paused'][1] == 0.0 for Tp in TP]
                    tpr = robust(plug_ok)
                    n2o = lambda Tp: PSZ[f'{orif}|{case}|A|{tag}|Tp{Tp}|{end}']['N2O_g']
                    r[tag] = dict(Tp_robust_plug=tpr, N2O_g_at_Tp_robust=n2o(tpr) if tpr else None, N2O_g_Tp2=n2o(2.0), N2O_g_Tp3=n2o(3.0),
                                  pocket_cm3_at_Tp_robust=PSZ[f'{orif}|{case}|A|{tag}|Tp{tpr}|{end}']['pocket'] if tpr else None,
                                  P_restart_max_by_Tp_plug={f'{Tp}': PSZ[f'{orif}|{case}|A|{tag}|Tp{Tp}|{end}']['P_restart'][1] for Tp in TP},
                                  slip={})
                    for s in slips:
                        ok = [zero(Tp, s) for Tp in TP]
                        tps = robust(ok)
                        r[tag]['slip'][f's{s}'] = dict(Tp_robust=tps,
                                                      P_restart_max_by_Tp={f'{Tp}': SS[f'{orif}|{case}|A|{tag}|Tp{Tp}|{end}|s{s}']['P_restart'][1] for Tp in TP},
                                                      N2O_g_at_Tp_robust=SS[f'{orif}|{case}|A|{tag}|Tp{tps}|{end}|s{s}']['N2O_g'] if tps else None,
                                                      cap_left_cm3_Tp3=SS[f'{orif}|{case}|A|{tag}|Tp3.0|{end}|s{s}']['cap'],
                                                      slug_cm3_Tp3=SS[f'{orif}|{case}|A|{tag}|Tp3.0|{end}|s{s}']['slug'])
                rows[f'{orif}|{lab}|{end}'] = r
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/purge_table_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={'purge_sizing_v2p4.json': sha16(fs), 'purge_slip_v2p4.json': sha16(fl)}, Tp_grid=TP, slips=slips, rows=rows,
               tags='DERIVED from SIM/DERIVED inputs (see the two input files); Tp grid resolution 0.5 s up to 3.0 s, then 4.0 s')
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    f = lambda a: '-' if a is None else ('%.1f' % a[0] if abs(a[1] - a[0]) < 0.05 else '%.1f-%.1f' % (a[0], a[1]))
    t = lambda x: '>4' if x is None else '%.1f' % x
    for end in ('E0', 'lift'):
        print(f'== end {end}: orif | case | wet: Tp_plug N2O@Tp | dry: Tp_plug N2O@Tp | N2O@2.0 wet/dry | N2O@3.0 wet/dry | slip Tp s0.5/s0.25/s0 wet ; dry')
        for orif in ('0.6', '0.8'):
            for _, lab in CASES:
                r = rows[f'{orif}|{lab}|{end}']; w, dr = r['wet'], r['dry']
                sl = lambda x: '/'.join(t(x['slip'][f's{s}']['Tp_robust']) for s in slips if s < 1.0)
                print(f"{orif} | {lab:7s} | {t(w['Tp_robust_plug'])} {f(w['N2O_g_at_Tp_robust'])} | {t(dr['Tp_robust_plug'])} {f(dr['N2O_g_at_Tp_robust'])} | "
                      f"{f(w['N2O_g_Tp2'])} / {f(dr['N2O_g_Tp2'])} | {f(w['N2O_g_Tp3'])} / {f(dr['N2O_g_Tp3'])} | {sl(w)} ; {sl(dr)}")
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])
