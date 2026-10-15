"""Generates src/unpurged_outcomes_v2p4a.py from the parent check (verbatim copy of the setup, e12s and post_light code).
usage: python -I gen_unpurged_outcomes_v2p4a.py   (Combustion v2.4a, 2026-10-13)
"""
import hashlib, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'unpurged_start_check_v2p4a.py')      # parent check (asserted 41fad4500f472bd4)
OUT = os.path.join(HERE, 'unpurged_outcomes_v2p4a.py')         # written next to it (expected 8256face5bcf7b27)
assert hashlib.sha256(open(SRC, 'rb').read()).hexdigest()[:16] == '41fad4500f472bd4'
L = open(SRC).read().split('\n')
i_fut = L.index('from __future__ import annotations')
i_main = L.index('def main(d, map_fn, gnc_fn, out_f):')
i_summ = L.index('    def summarise(seq, conv):')
header = L[i_fut:i_main]                      # imports, constants, sha16, load_map
body = L[i_main + 1:i_summ]                   # main body up to (excluding) summarise
gl = '    assert sha16(gnc_fn) == EXPECT_GNC, sha16(gnc_fn)'
assert body.count(gl) == 1
body[body.index(gl)] = ('    assert sha16(os.path.join(HERE, PARENT_PY)) == EXPECT_PARENT_PY, sha16(os.path.join(HERE, PARENT_PY))\n'
                        '    assert sha16(parent_json) == EXPECT_PARENT_JSON, sha16(parent_json)')
DOC = '''"""Unpurged relight start: outcome classes and success probability by LO/HI family (Combustion v2.4a, 2026-10-13).

Asked by the coordinator after REV-GNC-3 / LEAD CHANGELOG line 181 (2): the PURGE deadline is the P_total-maximising rule, L* = 1.7 s
if an unpurged start is LO (GNC used P_abort 0.242, P_total ~0.75) and 1.3 s if HI (P_abort 1.0); "state clearly: LO or HI, with
evidence class, and the hazard".  This script extends unpurged_start_check_v2p4a.py (41fad4500f472bd4): the module header and the
main() code up to post_light() are copied VERBATIM from it by gen_outcomes.py (only the GNC-input assert is replaced by the parent
asserts), and the rg01 ignition-delay set is re-asserted against the published P_abort as in the parent.  New: every start is put in
exactly one class
  NO_LIGHT            no light by W (the abort model's P_abort; drogue held, A2)
  A3_BEFORE_RELEASE   light, then a post-light vapour gap lasting >= the A3 detection that reaches the pintle before the first release
                      frame after E2 (abort with the drogue attached)
  RELEASED_THEN_A3    light, release at E2 (Pc >= 3 bar abs; E2 is Pc > 3 bar held 10 ms in the latency model), then the gap trips A3
                      after the release: the engine is shut down after the drogue has been released (dead vehicle released)
  SUCCESS             light and no post-light gap, or a gap shorter than the A3 detection (a Pc dip only)
for the named PURGE NOT RUN / purged states and for every PURGE NOT RUN record at 0 and 2 deg (the parent's population scan), with the
pool start ramp (2500 N/s from 62.5 N to F_cmd 200/500 N) and with the flow held at the lift (bracket).  Lights during vapour are not
modelled (as in the parent); A3 is the v2.4 rule (Pc < 0.40 x map for 20 ms, detection ~22 ms) with Pc VALID.
usage: python -I unpurged_outcomes_v2p4a.py DATA_V2P4_DIR THROTTLE_MAP_S230 PARENT_JSON OUT_JSON
"""'''
NEW = r'''
    # ================================================================== NEW in unpurged_outcomes_v2p4a: outcome classes
    PJ = json.load(open(parent_json))

    def classes(seq, conv, sub=None, mode='ramp_pool_Fcmd'):
        e, lit, has, gapV, out = post_light(seq, conv, sub=sub, modes=(mode,))
        ta, dg, Fg = out[mode]
        trip = has & (dg >= A3_DETECT_S)
        rel = trip & (ta >= FRAME_S)
        pre = trip & (ta < FRAME_S)
        r = dict(P_no_light=float((~lit).mean()), P_A3_before_release=float(pre.mean()), P_released_then_A3=float(rel.mean()),
                 P_success=float((lit & ~trip).mean()), P_light=float(lit.mean()), P_light_then_gap=float(has.mean()),
                 P_gap_shorter_than_A3=float((has & ~trip).mean()))
        tot = r['P_no_light'] + r['P_A3_before_release'] + r['P_released_then_A3'] + r['P_success']
        assert abs(tot - 1.0) < 1e-12, tot
        return r

    named = {}
    for key, pv in PJ['partA_post_light_gap']['states'].items():
        s = states[key]; seq = tuple(s['sequence_P1_S1_C1_S2_C2_cm3'])
        named[key] = dict(sequence_P1_S1_C1_S2_C2_cm3=list(seq), published_P_abort=s['P_abort_W0p65'])
        for conv in ('paused', 'restart'):
            named[key][conv] = {m: classes(seq, conv, mode=m) for m in ('ramp_pool_Fcmd', 'lift_flow_held', 'ramp_to_200N', 'ramp_to_500N')}
            # cross-check against the parent JSON (same code, same samples)
            p = pv[conv]
            assert abs(named[key][conv]['ramp_pool_Fcmd']['P_light'] - p['P_light_within_W']) < 1e-12
            assert abs(named[key][conv]['ramp_pool_Fcmd']['P_light_then_gap'] - p['P_light_then_vapour_gap']) < 1e-12
            if 'ramp_pool_Fcmd' in p:
                assert abs(named[key][conv]['ramp_pool_Fcmd']['P_released_then_A3'] - p['ramp_pool_Fcmd']['P_released_then_A3']) < 1e-12
                assert abs(named[key][conv]['lift_flow_held']['P_released_then_A3'] - p['lift_flow_held']['P_released_then_A3']) < 1e-12
        named[key]['P_success_min_over_conventions_and_modes'] = min(
            named[key][c][m]['P_success'] for c in ('paused', 'restart') for m in ('ramp_pool_Fcmd', 'lift_flow_held', 'ramp_to_200N', 'ramp_to_500N'))
        named[key]['P_success_max_over_conventions_and_modes'] = max(
            named[key][c][m]['P_success'] for c in ('paused', 'restart') for m in ('ramp_pool_Fcmd', 'lift_flow_held', 'ramp_to_200N', 'ramp_to_500N'))

    # population: all PURGE NOT RUN records at 0 and 2 deg (as the parent), per unique rounded sequence
    raw = RG.stream_records(os.path.join(d, 'purge_duration_v2p4_trade.json.raw.json.gz'), ('nopurge|',))
    NP = {}
    for k, r in raw.items():
        p = k.split('|')
        lin, m, case, tag, th, az, ser = p[1][3:], p[2], p[3] + '|' + p[4], p[5], float(p[6]), float(p[7]), p[8]
        NP[(lin, m, case, tag, th, az, ser)] = r
    assert len(NP) == 2 * 2 * 6 * 2 * 9 * 5, len(NP)
    SUB = slice(0, 20000)
    pop = {}
    for (lin, m, case, tag, th, az, ser), r in NP.items():
        if th not in (0.0, 2.0):
            continue
        sq = tuple(round(float(r[x]), 4) for x in ('P1', 'S1', 'C1', 'S2', 'C2'))
        fam = 'LO' if case.endswith('LO') else 'HI'
        pop.setdefault((lin, fam), {}).setdefault(sq, 0)
        pop[(lin, fam)][sq] += 1
    popsum = {}
    for (lin, fam), seqs in sorted(pop.items()):
        n_rec = sum(seqs.values())
        acc = {}
        rows_ = []
        for sq, cnt in seqs.items():
            cl = {(c, mo): classes(sq, c, sub=SUB, mode=mo) for c in ('paused', 'restart') for mo in ('ramp_pool_Fcmd', 'lift_flow_held')}
            # parent's choice: convention with the larger P(released then A3) under the pool ramp (cross-check of the parent's mean)
            par_c = max(('paused', 'restart'), key=lambda c: cl[(c, 'ramp_pool_Fcmd')]['P_released_then_A3'])
            worst = min(cl.values(), key=lambda v: v['P_success'])
            best = max(cl.values(), key=lambda v: v['P_success'])
            rows_.append((sq, cnt, cl, par_c, worst, best))
        def mean_(f):
            return float(sum(c * f(x) for x in rows_ for c in [x[1]]) / n_rec)
        parent_mean = mean_(lambda x: x[2][(x[3], 'ramp_pool_Fcmd')]['P_released_then_A3'])
        pv = PJ['partA_post_light_gap']['population_0_2deg'][f'lin{lin}|{fam}']
        assert abs(parent_mean - pv['mean_over_records_P_released_then_A3_pool_ramp']) < 1e-12, (parent_mean, pv)
        ps_w = np.repeat([x[4]['P_success'] for x in rows_], [x[1] for x in rows_])
        popsum[f'lin{lin}|{fam}'] = dict(
            n_records=n_rec, n_unique_sequences=len(seqs),
            mean_over_records_worst_case=dict(
                P_success=mean_(lambda x: x[4]['P_success']), P_no_light=mean_(lambda x: x[4]['P_no_light']),
                P_A3_before_release=mean_(lambda x: x[4]['P_A3_before_release']),
                P_released_then_A3=mean_(lambda x: x[4]['P_released_then_A3']), P_light=mean_(lambda x: x[4]['P_light'])),
            mean_over_records_best_case=dict(
                P_success=mean_(lambda x: x[5]['P_success']), P_released_then_A3=mean_(lambda x: x[5]['P_released_then_A3']),
                P_light=mean_(lambda x: x[5]['P_light'])),
            mean_over_records_pool_ramp_by_convention={c: dict(P_success=mean_(lambda x, c=c: x[2][(c, 'ramp_pool_Fcmd')]['P_success']),
                                                               P_released_then_A3=mean_(lambda x, c=c: x[2][(c, 'ramp_pool_Fcmd')]['P_released_then_A3']),
                                                               P_light=mean_(lambda x, c=c: x[2][(c, 'ramp_pool_Fcmd')]['P_light']))
                                                       for c in ('paused', 'restart')},
            P_success_worst_case_over_records=dict(min=float(ps_w.min()), p10=float(np.percentile(ps_w, 10)), median=float(np.median(ps_w)),
                                                   p90=float(np.percentile(ps_w, 90)), max=float(ps_w.max())),
            share_of_records_P_success_below_0p05=float((ps_w < 0.05).mean()),
            share_of_records_P_success_above_0p70=float((ps_w > 0.70).mean()),
            parent_mean_P_released_then_A3_pool_ramp_reproduced=parent_mean)
    for fam in ('LO', 'HI'):
        a = [popsum[f'lin{l}|{fam}'] for l in ('0.0', '1.0')]
        popsum[f'both_linings|{fam}'] = dict(
            n_records=sum(x['n_records'] for x in a),
            mean_P_success_worst_case=float(sum(x['n_records'] * x['mean_over_records_worst_case']['P_success'] for x in a) / sum(x['n_records'] for x in a)),
            mean_P_success_best_case=float(sum(x['n_records'] * x['mean_over_records_best_case']['P_success'] for x in a) / sum(x['n_records'] for x in a)),
            mean_P_released_then_A3_worst_case=float(sum(x['n_records'] * x['mean_over_records_worst_case']['P_released_then_A3'] for x in a)
                                                     / sum(x['n_records'] for x in a)))

    res = dict(version='v2.4a', date='2026-10-13', script=os.path.basename(__file__), script_sha256_16=sha16(os.path.abspath(__file__)),
               request='coordinator after REV-GNC-3 / LEAD CHANGELOG line 181 (2): unpurged start at the late-commit point, LO or HI, evidence class, hazard',
               inputs={**{k: v for k, v in RG.EXPECT.items()}, **EXPECT_EXTRA, **EXPECT_SRC, PARENT_PY: EXPECT_PARENT_PY,
                       os.path.basename(parent_json): EXPECT_PARENT_JSON, os.path.basename(map_fn): sha16(map_fn)},
               constants=dict(W_s=W, PURGE_s_per_cm3=PURGE, DEAD_s_per_cm3=DEAD, t_lift_s=t_lift, A3_detect_s=A3_DETECT_S, frame_s=FRAME_S,
                              ramp_N_s=RAMP_N_S, F_lift_N=F_LIFT, n_samples=int(len(base)), population_subset='first 20 000 samples'),
               named_states=named, population_0_2deg=popsum,
               lo_hi_meaning=('LO/HI are the two ends of Mechanical\'s wall heat-transfer coefficient bracket (segment heat cases isothermal, hw+5K, '
                              'ARM_bay45C_liq24C, each at h LO and h HI; segment_heat_v341_v2p4.json) that set how much liquid in the line flashes '
                              'during the coast: ASSUMED bounds, not a measurement. Neither end is supported or excluded by evidence; CF-4 (optional '
                              'generation runs) and T4 measure it.'),
               tags=dict(classes='SIM on ASSUMED delays (rg01 set reproduced) + DERIVED line states (records not re-run); post-light timing DERIVED '
                                 'approximation (parent); A3 rule per REPORT v2.4 7.4; release at E2 with Pc valid; lights during vapour not modelled',
                         population='bracket records, NOT probability-weighted; means are unweighted over records'))
    json.dump(res, open(out_f, 'w'), indent=1, default=float)
    for key, v in named.items():
        for conv in ('paused', 'restart'):
            for mo in ('ramp_pool_Fcmd', 'lift_flow_held'):
                x = v[conv][mo]
                print(f"{key:46s} {conv:7s} {mo:15s} noL {x['P_no_light']:.4f} A3pre {x['P_A3_before_release']:.4f} "
                      f"relA3 {x['P_released_then_A3']:.4f} succ {x['P_success']:.4f} (dip-only {x['P_gap_shorter_than_A3']:.4f})")
    for k, v in popsum.items():
        print(k, json.dumps(v))
    print('wrote', out_f, sha16(out_f))
'''
TAIL = '''

if __name__ == '__main__':
    main(*sys.argv[1:5])
'''
consts = ("PARENT_PY = 'unpurged_start_check_v2p4a.py'\n"
          "EXPECT_PARENT_PY = '41fad4500f472bd4'\n"
          "EXPECT_PARENT_JSON = '4c745dcfbf09aef7'\n")
txt = (DOC + '\n' + '\n'.join(header).rstrip('\n') + '\n' + consts + '\n\n'
       + 'def main(d, map_fn, parent_json, out_f):\n' + '\n'.join(body).rstrip() + '\n' + NEW + TAIL)
open(OUT, 'w').write(txt)
print('wrote', OUT, hashlib.sha256(txt.encode()).hexdigest()[:16], len(txt.split('\n')), 'lines')
