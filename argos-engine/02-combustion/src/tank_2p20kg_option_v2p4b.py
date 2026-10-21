"""2.20 kg N2O tank option: first-order A1 erosion / residual-web / thermal impact (Combustion v2.4b, 2026-10-19; LEAD
CHANGELOG 219 (founder: tank stays 2.00 kg; 2.20 kg is a characterized OPTION, no re-run requested) and 227 (9) (its A1 burn p99
8.92 / 8.71 s, max 9.24 s, exceeds the 8.258 s sizing counter: B1 / thermal / erosion check TO-VERIFY); lead request 2026-10-19
item 4: estimate if cheap, else an open item with an owner).

Method (DERIVED scaling, no new flight or grain run): the A1 rows of the published v2.4a tables (REPORT 062e307a8d25e1ec, Tables
4.5 / 4.6 / 5.3, record DC-A1 dispersed p99, engine-on 8.258 s counter, 8.24 s erosion burn) are scaled to the 2.20 kg burn times
(time ratio t / 8.258 s) and, as the upper end, by the thrust factor (m_2.20 / m_2.00)^0.8 on the whole burn (the GNC rev4 item
[15] T/W ratios give the mass ratio: liftoff 2.92 / 2.72, touchdown 3.16 / 2.95; Bartz-type h ~ Pc^0.8).  Residual web: the extra
burn time at the largest regression rate of the A1 grain run (a x1.0, n 0.5, read from the record CSV), and x the band ratio of the
web consumed (Table 4.6: a x1.5 n 0.35 against a x1.0 n 0.5).  Thermal: the A1 burn stays below B1's (21.8-23.6 s), which governs.
usage: python -I tank_2p20kg_option_v2p4b.py HUB_REPORT_V2P4A CHANGELOG GNC_V32_PROPOSALS_REV4 A1_RECORD_CSV OUT_JSON
"""
from __future__ import annotations
import csv, hashlib, json, os, re, sys

EXPECT = {'report': '062e307a8d25e1ec', 'gnc': '6fd6d66e08aef5d8', 'a1_csv': 'a9567e1f6df0c6c9'}
EXPECT_LINE = {219: None, 227: None}
T_COUNTER = 8.258


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def row(report, prefix):
    hits = [ln for ln in report.splitlines() if ln.startswith(prefix)]
    assert len(hits) == 1, (prefix, len(hits))
    return [c.strip() for c in hits[0].strip().strip('|').split('|')]


def main(report_f, chlog_f, gnc_f, a1_csv, out_f):
    for k, f in (('report', report_f), ('gnc', gnc_f), ('a1_csv', a1_csv)):
        assert sha16(f) == EXPECT[k], (k, sha16(f))
    L = open(chlog_f).read().splitlines()
    l227, l219 = L[226], L[218]
    m = re.search(r"A1 burn p99 ([0-9.]+) / ([0-9.]+) s \(max ([0-9.]+) s\) exceeds the ([0-9.]+) s sizing counter", l227)
    assert m and '2.20 kg' in l227 and '2.20 kg' in l219, 'CHANGELOG 219 / 227 text'
    t99a, t99b, tmax, tc = (float(x) for x in m.groups())
    assert tc == T_COUNTER
    m2 = re.search(r"burn p99 ([0-9.]+) / ([0-9.]+) s at 210 m against ([0-9.]+) / ([0-9.]+) s at 285 m", l227)
    assert m2 and 'RV6-05' in l227, 'CHANGELOG 227 (9) RV6-05 text'
    b210a, b210b, b285a, b285b = (float(x) for x in m2.groups())
    G = json.load(open(gnc_f))
    it = G['items'][15]['proposal_rev4']
    tw = re.search(r"0 kg ([0-9.]+) / ([0-9.]+) / ([0-9.]+);.*?sized loads \+1 kg at 2\.20 kg ([0-9.]+) / ([0-9.]+) / ([0-9.]+)", it)
    assert tw, 'GNC item 15 T/W'
    tw0_lo, tw0_td, _, tw2_lo, tw2_td, _ = (float(x) for x in tw.groups())
    mass_ratio = dict(liftoff=tw0_lo / tw2_lo, touchdown=tw0_td / tw2_td)
    k_thrust = max(mass_ratio.values()) ** 0.8
    R = open(report_f).read()
    r45 = row(R, '| A1 dispersed p99 | 8.26 |')
    r46 = row(R, '| A1 dispersed p99 (8.26 s) |')
    r53 = row(R, '| A1 dispersed p99, a x1.0 n 0.5 | 8.24 |')
    r53n = row(R, '| A1 p99, a x1.0 n 0.68 | 8.24 |')
    web_end_10_05 = float(r45[5])
    w46 = {('x0.6', 'x1.0', 'x1.5')[i]: [float(x) for x in r46[1 + i].split('/')] for i in range(3)}
    nom_pct, cons_pct = float(r53[3]), float(r53[6])
    lit_pct = [float(x) for x in r53[9].split('-')]
    nom_pct_n068 = float(r53n[3])
    # A1 grain run: web and regression rate on the run rows
    rows = [r for r in csv.DictReader(open(a1_csv)) if r['state'] == 'run']
    t = [float(r['t']) for r in rows]; w = [float(r['w_min']) * 1e3 for r in rows]
    rates = [(w[i] - w[i + 1]) / (t[i + 1] - t[i]) for i in range(len(t) - 1) if 0 < t[i + 1] - t[i] < 0.02]
    r_max = max(rates); r_mean = (w[0] - w[-1]) / sum(t[i + 1] - t[i] for i in range(len(t) - 1) if 0 < t[i + 1] - t[i] < 0.02)
    w0 = w[0]
    band_ratio = (w0 - w46['x1.5'][0]) / (w0 - w46['x1.0'][1])                     # a x1.5 n 0.35 against a x1.0 n 0.5
    cases = {}
    for lab, tb in (('p99_8.71s', t99b), ('p99_8.92s', t99a), ('max_9.24s', tmax)):
        kt = tb / T_COUNTER; dt = tb - T_COUNTER
        lo, hi = kt, kt * k_thrust
        cases[lab] = dict(
            burn_s=tb, time_ratio=round(kt, 4), extra_burn_s=round(dt, 3),
            erosion_nominal_dAt_pct=[round(nom_pct * lo, 2), round(nom_pct * hi, 2)],
            erosion_nominal_n068_dAt_pct=[round(nom_pct_n068 * lo, 2), round(nom_pct_n068 * hi, 2)],
            erosion_conservative_dAt_pct=[round(cons_pct * lo, 2), round(cons_pct * hi, 2)],
            erosion_literature_dAt_pct=[round(lit_pct[0] * lo, 1), round(lit_pct[1] * hi, 1)],
            web_end_a1p0_n0p5_mm=[round(web_end_10_05 - dt * r_max, 2), round(web_end_10_05 - dt * r_mean, 2)],
            web_end_min_band_a1p5_n0p35_mm=round(w46['x1.5'][0] - dt * r_max * band_ratio, 2))
    # 2.00 kg tank at the decided 210 m target (RV6-05, line 227 (9)): same vehicle and tank, so thrust factor 1; time ratio only
    cases_210 = {}
    for lab, tb in (('210m_p99_%.3fs' % b210a, b210a), ('210m_p99_%.3fs' % b210b, b210b)):
        kt = tb / T_COUNTER; dt = tb - T_COUNTER
        cases_210[lab] = dict(
            burn_s=tb, time_ratio=round(kt, 4), extra_burn_s=round(dt, 3),
            erosion_nominal_dAt_pct=round(nom_pct * max(kt, 1.0), 2), erosion_nominal_n068_dAt_pct=round(nom_pct_n068 * max(kt, 1.0), 2),
            erosion_conservative_dAt_pct=round(cons_pct * max(kt, 1.0), 2),
            erosion_literature_dAt_pct=[round(lit_pct[0] * max(kt, 1.0), 1), round(lit_pct[1] * max(kt, 1.0), 1)],
            web_end_a1p0_n0p5_mm=round(web_end_10_05 - max(dt, 0.0) * r_max, 2),
            web_end_min_band_a1p5_n0p35_mm=round(w46['x1.5'][0] - max(dt, 0.0) * r_max * band_ratio, 2))
    out = dict(
        version='v2.4b', date='2026-10-19', script='02-combustion/src/tank_2p20kg_option_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
        request='LEAD 2026-10-19 item 4; CHANGELOG 219, 227 (9)',
        inputs=dict(report_v2p4a='02-combustion/REPORT.md (v2.4a) %s' % sha16(report_f),
                    changelog_lines={'219': hashlib.sha256(l219.encode()).hexdigest()[:16], '227': hashlib.sha256(l227.encode()).hexdigest()[:16]},
                    gnc_v32_proposals_rev4='01-systems-gnc/staging_v3.1/rev4/out_rev4/v32/v32_proposals_rev4.json %s (item [15])' % sha16(gnc_f),
                    a1_record_csv='data/v2/dc_gncv3/DC-A1dispp99-S230_neqE1e+03_reg1.csv %s' % sha16(a1_csv)),
        basis=dict(sizing_counter_s=T_COUNTER, burn_p99_s=[t99a, t99b], burn_max_s=tmax, mass_ratio=mass_ratio,
                   thrust_factor_upper=round(k_thrust, 4),
                   a1_record=dict(erosion_nominal_pct=nom_pct, erosion_nominal_n068_pct=nom_pct_n068, erosion_conservative_pct=cons_pct,
                                  erosion_literature_pct=lit_pct, web_end_mm_a1p0_n0p5=web_end_10_05, web_table46=w46,
                                  web_initial_mm=round(w0, 3), regression_mm_s=dict(max=round(r_max, 3), mean=round(r_mean, 3)),
                                  band_ratio_web_consumed=round(band_ratio, 3)),
                   criteria=dict(NZ01_dAt_pct=2.0, ENG06_dAt_pct=5.0, ENG06_web_mm=1.0)),
        cases=cases,
        cases_2p00kg_210m=dict(
            source='LEAD CHANGELOG 227 (9) (RV6-05): GNC rev4 burn p99 %.3f / %.3f s at 210 m against %.3f / %.3f s at 285 m (SIM, staged; '
                   'two main bases)' % (b210a, b210b, b285a, b285b),
            note='time ratio against the 8.258 s A1 sizing counter, floored at 1 (a shorter burn keeps the 8.258 s tables); same tank and '
                 'vehicle, so no thrust factor', cases=cases_210),
        findings=[
            '2.00 kg at the decided 210 m target (RV6-05): the A1 burn p99 %.3f s is %+.3f s (%+.1f %%) over the 8.258 s sizing counter; '
            'first order, nominal A1 throat-area growth %.2f %% per flight at n 0.5 (below the NZ-01 2 %% criterion) and %.2f %% at n 0.68 '
            '(above it, as at 8.258 s: OI-40), residual web >= %.2f mm '
            '(a x1.0 n 0.5) and >= %.2f mm (band corner); the A1 tables on 8.258 s understate the A1 time by up to %.1f %%; B1 governs.' % (
                b210a, b210a - T_COUNTER, (b210a / T_COUNTER - 1) * 100, cases_210['210m_p99_%.3fs' % b210a]['erosion_nominal_dAt_pct'],
                cases_210['210m_p99_%.3fs' % b210a]['erosion_nominal_n068_dAt_pct'],
                cases_210['210m_p99_%.3fs' % b210a]['web_end_a1p0_n0p5_mm'], cases_210['210m_p99_%.3fs' % b210a]['web_end_min_band_a1p5_n0p35_mm'],
                (b210a / T_COUNTER - 1) * 100),
            'Nominal-model A1 throat-area growth goes from 1.86 %% (8.24 s record) to %.2f-%.2f %% per flight (time ratio, x thrust factor): '
            'the 8.92 s p99 and 9.24 s max cross the NZ-01 2 %% criterion (OI-40) even on the nominal model; the conservative (%.1f-%.1f %%) '
            'and literature (%.1f-%.1f %%) models were already above ENG-06 5 %% at 2.00 kg.' % (
                cases['p99_8.71s']['erosion_nominal_dAt_pct'][0], cases['max_9.24s']['erosion_nominal_dAt_pct'][1],
                cases['p99_8.71s']['erosion_conservative_dAt_pct'][0], cases['max_9.24s']['erosion_conservative_dAt_pct'][1],
                cases['p99_8.71s']['erosion_literature_dAt_pct'][0], cases['max_9.24s']['erosion_literature_dAt_pct'][1]),
            'Residual web: >= %.2f mm at a x1.0 n 0.5 and >= %.2f mm at the band corner a x1.5 n 0.35 (9.24 s, largest A1 regression rate): '
            'ENG-06 >= 1 mm holds.' % (cases['max_9.24s']['web_end_a1p0_n0p5_mm'][0], cases['max_9.24s']['web_end_min_band_a1p5_n0p35_mm']),
            'Thermal: the A1 burn (<= 9.24 s) stays well below B1 (21.8-23.6 s), which governs soak and insert life; A1 heat input rises '
            '<= %.0f %% (time x thrust factor).' % ((cases['max_9.24s']['time_ratio'] * k_thrust - 1) * 100),
            'Not covered (OPEN): B1 with the 2.20 kg tank (no GNC record: a heavier vehicle and +0.2 kg N2O change the B1 duty cycle that '
            'governs sizing), the A1 relight state at 210 m with 2.20 kg (OI-49), the wall-temperature rise of a longer burn (erosion rate '
            'grows with Tw, so linear scaling can understate), the longer tank structure.'],
        open_item=dict(id='OI-50', text='2.20 kg tank option: B1 and A1 records with the 2.20 kg tank (GNC), then S230 grain / erosion / thermal '
                       're-run (Combustion Tables 4.5, 4.6, 5.3, 6.x), tank and structure (Mechanical); until then the datasheet quotes the '
                       '2.20 kg option with "B1 / thermal / erosion TO-VERIFY" and this first-order A1 estimate.',
                       owners=['GNC (records)', 'Combustion (re-run)', 'Mechanical (tank / structure, NZ-01 criterion OI-40)']),
        tags=dict(scaling='DERIVED (first-order; no run)', records='SIM (gnc.json v3.1 A1 record; GNC rev4 item [15] SIM / DERIVED)',
                  criteria='REQ / LEAD', status='not physical evidence'))
    json.dump(out, open(out_f, 'w'), indent=1)
    print('wrote', out_f, sha16(out_f))
    for k, v in cases.items():
        print(k, v)
    print('k_thrust', round(k_thrust, 4), 'r_max', round(r_max, 3), 'r_mean', round(r_mean, 3), 'w0', round(w0, 3), 'band', round(band_ratio, 3))


if __name__ == '__main__':
    main(*sys.argv[1:6])
