"""Unpurged relight start: outcome classes and success probability by LO/HI family (Combustion v2.4a, 2026-10-13).

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
"""
from __future__ import annotations
import hashlib, json, math, os, sys, csv
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rg01_line_states_v2p4 as RG
SL = RG.SL

W = RG.W
A3_DETECT_S = 0.022          # REPORT v2.4 §7.4 A3: 20 ms persistence, "detection about 22 ms"
B7_HOLD_S = 0.10             # drogue-release b7: 0.8 bar rise held to E2 + 0.10 s (REPORT §7.3)
FRAME_S = 0.010              # one TLM_FAST frame, ASSUMED <= 10 ms
FA1_FAST_PART_G = 2.141      # FA-1 envelope basis (fa1_envelope_v2p4a, fast part N2O)
RAMP_N_S = 2500.0            # start ramp of the start_latency pool
F_LIFT = 62.5                # N, 12.5 % of 500 N: the pool's lift (frac 0.125)
EXPECT_EXTRA = {'rg01_line_states_v2p4.json': '2939549811d4c381'}
EXPECT_SRC = {'rg01_line_states_v2p4.py': 'a7f68a1a84286f9b', 'start_latency_v2p4.py': '989ccd9a004b2cb9'}
EXPECT_GNC = '47b4deb96ea22043'


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def load_map(fn, p_tank=4.5e6, d_port=0.030):
    rows = [r for r in csv.reader(open(fn)) if r and not r[0].startswith('#')]
    h = rows[0]
    sel = [r for r in rows[1:] if abs(float(r[h.index('P_tank_Pa')]) - p_tank) < 1.0 and abs(float(r[h.index('D_port_m')]) - d_port) < 1e-6]
    sel.sort(key=lambda r: float(r[h.index('F_N')]))
    g = lambda k: np.array([float(r[h.index(k)]) for r in sel])
    return dict(F=g('F_N'), mox=g('mdot_ox'), Pc=g('Pc_Pa'), OF=g('OF'), lift=g('lift_m'))
PARENT_PY = 'unpurged_start_check_v2p4a.py'
EXPECT_PARENT_PY = '41fad4500f472bd4'
EXPECT_PARENT_JSON = '4c745dcfbf09aef7'


def main(d, map_fn, parent_json, out_f):
    for k, hsh in {**RG.EXPECT, **EXPECT_EXTRA}.items():
        assert sha16(os.path.join(d, k)) == hsh, (k, sha16(os.path.join(d, k)))
    for k, hsh in EXPECT_SRC.items():
        assert sha16(os.path.join(HERE, k)) == hsh, (k, sha16(os.path.join(HERE, k)))
    assert sha16(os.path.join(HERE, PARENT_PY)) == EXPECT_PARENT_PY, sha16(os.path.join(HERE, PARENT_PY))
    assert sha16(parent_json) == EXPECT_PARENT_JSON, sha16(parent_json)
    RJ = json.load(open(os.path.join(d, 'rg01_line_states_v2p4.json')))
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    PURGE = VO['purge_s_per_cm3']; DEAD = VO['liquid_plug_dead_time_s_per_cm3']
    PA = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
    # ------------------------------------------------------------------ the rg01 ignition-delay set, reproduced
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    rows = J['part1_runs']['v']; lifts = J['ignition_lifts']
    pool = [r for r in rows if r['ramp'] == 2500.0 and r['F_cmd'] in (200.0, 500.0) and r['state'] == 'A1_relight'
            and r['frac'] == 0.125 and r.get('loop_K', 0.0) == 15.0]
    N = 200000; rng = np.random.default_rng(2024)
    h = lifts['A1_relight|0.125']['lift_m']; t_lift = SL.T_CMD + h / SL.V_PINTLE + 0.010
    idx = rng.integers(0, len(pool), N)
    tc = np.array([np.nan if q['t_conf_s'] is None else q['t_conf_s'] for q in pool])[idx]
    fcmd = np.array([q['F_cmd'] for q in pool])[idx]
    e1_all = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)
    ig = rng.uniform(0.05, 0.30, N)
    base_all = t_lift + ig + tc
    fin = np.isfinite(base_all)
    base = base_all[fin]; fcmd = fcmd[fin]
    assert abs(float(base.max()) - PA['E1_E2_liquid_s']['max']) < 1e-12
    assert abs(float(np.median(base)) - PA['E1_E2_liquid_s']['median']) < 1e-12
    assert abs(t_lift - RJ['t_lift_s']) < 1e-15 and abs(PURGE - RJ['PURGE_s_per_cm3']) < 1e-15 and abs(DEAD - RJ['DEAD_s_per_cm3']) < 1e-15
    n_run = base - t_lift

    def e12(seq, conv):            # verbatim from rg01_line_states_v2p4.main
        P1, S1, C1, S2, C2 = seq
        if C1 <= 0.0 and C2 <= 0.0:
            return base + PURGE * P1
        t1, t2 = S1 * DEAD, S2 * DEAD
        if conv == 'paused':
            return base + PURGE * P1 + np.where(n_run > t1, PURGE * C1, 0.0) + np.where(n_run > t1 + t2, PURGE * C2, 0.0)
        return base + PURGE * P1 + np.where(n_run > t1, t1 + PURGE * C1 + np.where(n_run > t2, t2 + PURGE * C2, 0.0), 0.0)

    states = RJ['part2_line_states_for_gnc']['v']
    for key in ('purge_not_run_unlined_LO_0-2deg_worst', 'purge_not_run_lined_LO_0-2deg_worst', 'purge_not_run_unlined_HI_0-2deg_worst',
                'purge_not_run_unlined_0-2deg_least', 'purged_unlined_Tp2.5_0-2deg_worst', 'purged_lined_Tp2.2_robust_edge_0-2deg_worst'):
        s = states[key]; conv = s['convention'].split(' ')[0]
        p = float(1.0 - (e12(s['sequence_P1_S1_C1_S2_C2_cm3'], conv) <= W).mean())
        assert abs(p - s['P_abort_W0p65']) < 1e-12, (key, p, s['P_abort_W0p65'])

    # ------------------------------------------------------------------ flow growth after E2 (ramp), from the S230 throttle map
    M = load_map(map_fn)
    phi = lambda F: np.interp(F, M['F'], M['mox']) / np.interp(F_LIFT, M['F'], M['mox'])
    tg = np.arange(0.0, 3.0, 5.0e-4)
    G = {}
    for Fc in (None, 200.0, 500.0):          # None: flow held at the lift (no ramp) -> G(t) = t
        if Fc is None:
            G[Fc] = tg.copy()
        else:
            F = np.minimum(F_LIFT + RAMP_N_S * tg, Fc)
            G[Fc] = np.concatenate([[0.0], np.cumsum(0.5 * (phi(F[1:]) + phi(F[:-1])) * np.diff(tg))])
    Finv = lambda Fc, g: np.interp(g, G[Fc], tg)
    F_at = lambda Fc, t: np.full_like(t, F_LIFT) if Fc is None else np.minimum(F_LIFT + RAMP_N_S * t, Fc)

    def e12s(seq, conv, b, nr):     # e12 on a sample subset (same formula)
        P1, S1, C1, S2, C2 = seq
        if C1 <= 0.0 and C2 <= 0.0:
            return b + PURGE * P1
        t1, t2 = S1 * DEAD, S2 * DEAD
        if conv == 'paused':
            return b + PURGE * P1 + np.where(nr > t1, PURGE * C1, 0.0) + np.where(nr > t1 + t2, PURGE * C2, 0.0)
        return b + PURGE * P1 + np.where(nr > t1, t1 + PURGE * C1 + np.where(nr > t2, t2 + PURGE * C2, 0.0), 0.0)

    def post_light(seq, conv, sub=None, modes=('lift_flow_held', 'ramp_to_200N', 'ramp_to_500N', 'ramp_pool_Fcmd')):
        """Lights followed by a vapour gap.  Returns per-sample arrays (gap volume, arrival after E2, duration) for each flow mode.
        sub: optional sample slice (population scan only)."""
        P1, S1, C1, S2, C2 = seq
        bs = base if sub is None else base[sub]; nr = n_run if sub is None else n_run[sub]; fc = fcmd if sub is None else fcmd[sub]
        e = e12s(seq, conv, bs, nr)
        lit = e <= W
        t1, t2 = S1 * DEAD, S2 * DEAD
        gapV = np.zeros_like(bs); rem = np.zeros_like(bs)       # rem: lift-seconds of liquid left in the slug at E2
        if not (C1 <= 0.0 and C2 <= 0.0):
            in1 = nr <= t1
            gapV = np.where(in1, C1, 0.0); rem = np.where(in1, t1 - nr, 0.0)
            if conv == 'paused':
                in2 = (nr > t1) & (nr <= t1 + t2)
                rem = np.where(in2, t1 + t2 - nr, rem); gapV = np.where(in2, C2, gapV)
            else:
                in2 = (nr > t1) & (nr <= t2)
                rem = np.where(in2, t2 - nr, rem); gapV = np.where(in2, C2, gapV)
        has = lit & (gapV > 0.0)
        out = {}
        for lab, Fsel in (('lift_flow_held', None), ('ramp_to_200N', 200.0), ('ramp_to_500N', 500.0), ('ramp_pool_Fcmd', 'pool')):
            if lab not in modes:
                continue
            if Fsel == 'pool':
                ta = np.where(fc == 200.0, Finv(200.0, rem), Finv(500.0, rem))
                te = np.where(fc == 200.0, Finv(200.0, rem + PURGE * gapV), Finv(500.0, rem + PURGE * gapV))
                Fg = np.where(fc == 200.0, F_at(200.0, ta), F_at(500.0, ta))
            else:
                ta = Finv(Fsel, rem)
                te = Finv(Fsel, rem + PURGE * gapV)
                Fg = F_at(Fsel, ta)
            out[lab] = (ta, te - ta, Fg)
        return e, lit, has, gapV, out

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


if __name__ == '__main__':
    main(*sys.argv[1:5])
