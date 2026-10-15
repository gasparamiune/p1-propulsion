"""Population statements of the unpurged-start records (Combustion v2.4b, 2026-10-13; REV-COMB-3 R3-13).

R3-13 found three population statements of REPORT v2.4a (l.775 "0 in 82 % / 77 %", "in every HI record"; the H20 row means) true for
one profile only.  This script counts them per command profile from the v2.4b per-record CSV (release_hold_records_v2p4b.csv,
59e7f44e44fbfeef; 2160 PURGE NOT RUN records x 3 profiles), so the REPORT text states each count with its profile.
P_success per record is the worst of the paused/restart conventions (as release_hold_v2p4b); a record counts as 'zero' if
P_success < 1e-9 and as 'one' if P_success > 1 - 1e-9.  Bracket records, NOT probability-weighted.
Tags: SIM on ASSUMED delays + DERIVED line states (counting only; no new physics).
usage: python -I population_statements_v2p4b.py RECORDS_CSV RELEASE_HOLD_JSON OUT_JSON
"""
from __future__ import annotations
import csv, hashlib, json, os, sys
sys.dont_write_bytecode = True

EXPECT = {'csv': '59e7f44e44fbfeef', 'json': 'a926426da0e6e436'}


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main(csv_f, rh_f, out_f):
    assert sha16(csv_f) == EXPECT['csv'], sha16(csv_f)
    assert sha16(rh_f) == EXPECT['json'], sha16(rh_f)
    RH = json.load(open(rh_f))
    rows = list(csv.DictReader(open(csv_f)))
    assert len(rows) == 6480, len(rows)
    out = {}
    for lin in ('lin0.0', 'lin1.0'):
        for br in ('LO', 'HI'):
            for prof in ('ramp_to_200N', 'ramp_to_500N', 'lift_flow_held'):
                sel = [r for r in rows if 'lin' + r['lining'] == lin and r['bracket'] == br and r['profile'] == prof]
                ps = [min(float(r['P_success_paused']), float(r['P_success_restart'])) for r in sel]
                pnl = [max(float(r['P_no_light_paused']), float(r['P_no_light_restart'])) for r in sel]
                trip = [float(r['P_A3_trip']) for r in sel]
                rel = [float(r['P_released_then_A3_opt_H0.01']) for r in sel]
                n = len(sel)
                out[f'{lin}|{br}|{prof}'] = dict(
                    n_records=n, n_P_success_zero=sum(p < 1e-9 for p in ps), n_P_success_one=sum(p > 1 - 1e-9 for p in ps),
                    n_P_success_between=sum(1e-9 <= p <= 1 - 1e-9 for p in ps), frac_P_success_zero=round(sum(p < 1e-9 for p in ps) / n, 4),
                    mean_P_success=round(sum(ps) / n, 4), mean_P_no_light=round(sum(pnl) / n, 4), mean_P_A3_trip=round(sum(trip) / n, 4),
                    mean_P_released_then_A3_at_E2_opt=round(sum(rel) / n, 4))
    # cross-check against the group means of release_hold_v2p4b (same records, same convention)
    for lin, g in (('lin0.0', 'lin0.0'), ('lin1.0', 'lin1.0')):
        for br in ('LO', 'HI'):
            for prof in ('ramp_to_200N', 'ramp_to_500N', 'lift_flow_held'):
                a = out[f'{lin}|{br}|{prof}']['mean_P_success']; b = RH['groups'][f'{g}|{br}'][prof]['mean_P_success_worst_convention']
                assert abs(a - b) < 6e-5, (lin, br, prof, a, b)
    res = dict(version='v2.4b', date='2026-10-13', script='02-combustion/src/population_statements_v2p4b.py',
               script_sha256_16=sha16(os.path.abspath(__file__)),
               request='REV-COMB-3 R3-13: population statements per command profile',
               inputs={'release_hold_records_v2p4b.csv': sha16(csv_f), 'release_hold_v2p4b.json': sha16(rh_f)},
               check='group means of P_success reproduce release_hold_v2p4b to < 6e-5',
               counts=out,
               tags=dict(records='SIM on ASSUMED delays + DERIVED line states', population='bracket records, NOT probability-weighted',
                         status='counting only; not physical evidence'))
    json.dump(res, open(out_f, 'w'), indent=1)
    for k, v in out.items():
        print(k, v['n_records'], 'zero', v['n_P_success_zero'], v['frac_P_success_zero'], 'one', v['n_P_success_one'], 'mean', v['mean_P_success'],
              'nolight', v['mean_P_no_light'], 'rel@E2', v['mean_P_released_then_A3_at_E2_opt'])
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:4])
