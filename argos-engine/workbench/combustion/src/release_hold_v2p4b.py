"""Drogue-release hold table for an unpurged relight start (Combustion v2.4b, 2026-10-13).

REV-COMB-3 R3-01 (MAJOR) and LEAD CHANGELOG line 194 (3): the 'E2 + 0.22 s' release hold of line 186 (1) came from one state (the
LO-worst unlined gap arrival 0.193 s with the flow held at the lift, plus the 22 ms A3 detection) and is WITHDRAWN.  This script gives
the hold as a function of the post-E2 command profile flown while the drogue is held, over ALL 2160 PURGE NOT RUN records (2 linings x
barrier/open x 3 thermal cases x LO/HI x wet/dry x 0/2 deg x azimuths x series; every record is at 0 or 2 deg), and the per-record
outcome classes for a hold H, for GNC to weight.
The module header and the main() code up to post_light() are copied VERBATIM from unpurged_start_check_v2p4a.py (41fad4500f472bd4) by
gen_release_hold_v2p4b.py (only the GNC-input assert is replaced by the parent asserts); the rg01 ignition-delay set (200 000 samples,
seed 2024) is re-asserted against the published P_abort as in the parent.  The v2.4a classes (unpurged_outcomes_v2p4a.json) are
reproduced first (named states on the full set, population on the parent's 20 000-sample subset) to 1e-12.
Profiles flown during the hold (the start ramp is ASSUMED to begin at E2, as in the parent):
  ramp_to_200N    2500 N/s from the 62.5 N start level to 200 N, volumetric flow ~ mdot_ox(F) of the S230 map
  ramp_to_500N    2500 N/s to 500 N
  lift_flow_held  the command held at the start level (the LEAD line 186 (2) hold with Pc invalid is this case)
A3 trips 22 ms after the gap reaches the pintle (gap lasting >= 22 ms).  With a hold H the first release opportunity is E2 + max(H,
10 ms) (one TLM_FAST frame).  Two release criteria bracket the Pc >= 3.0 bar abs release term during a gap:
  optimistic    released then A3 iff the gap arrives at or after the release (Pc already low at the release frame -> no release)
  conservative  released then A3 iff the A3 trip comes after the release (Pc read >= 3 bar until the trip)
Latest A3 trip: the maximum over the 200 000-sample set (MC) and a deterministic supremum over the support of n_run (slug-1 lights on
a 20 001-point grid; every record has C2 = 0, asserted, so no light is followed by a second void).  Hold value per profile = latest
trip over all records + one 10 ms frame, rounded up to 10 ms.
Lights during vapour are not modelled; flame survival in the gap, the slug idealisation and vapour-flow scaling are ASSUMED (parent).
Tags: SIM on ASSUMED delays + DERIVED line states (records not re-run); NOT probability-weighted; not physical evidence.
usage: python -I release_hold_v2p4b.py DATA_V2P4_DIR THROTTLE_MAP_S230 OUTCOMES_V2P4A_JSON OUT_JSON OUT_CSV
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
import time
PARENT_PY = 'unpurged_start_check_v2p4a.py'
EXPECT_PARENT_PY = '41fad4500f472bd4'
OUTCOMES_PY = 'unpurged_outcomes_v2p4a.py'
EXPECT_OUTCOMES_PY = '8256face5bcf7b27'
EXPECT_OUTCOMES_JSON = '18a639d61b58ce8a'


def main(d, map_fn, outcomes_json, out_f, out_csv):
    for k, hsh in {**RG.EXPECT, **EXPECT_EXTRA}.items():
        assert sha16(os.path.join(d, k)) == hsh, (k, sha16(os.path.join(d, k)))
    for k, hsh in EXPECT_SRC.items():
        assert sha16(os.path.join(HERE, k)) == hsh, (k, sha16(os.path.join(HERE, k)))
    assert sha16(os.path.join(HERE, PARENT_PY)) == EXPECT_PARENT_PY, sha16(os.path.join(HERE, PARENT_PY))
    assert sha16(os.path.join(HERE, OUTCOMES_PY)) == EXPECT_OUTCOMES_PY, sha16(os.path.join(HERE, OUTCOMES_PY))
    assert sha16(outcomes_json) == EXPECT_OUTCOMES_JSON, sha16(outcomes_json)
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

    # ================================================================== NEW in release_hold_v2p4b: release-hold table (R3-01)
    PJ = json.load(open(outcomes_json))
    HOLDS = (0.01, 0.05, 0.10, 0.15, 0.19, 0.20, 0.22, 0.25, 0.28, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80)
    MODES = ('ramp_to_200N', 'ramp_to_500N', 'lift_flow_held')
    FC = {'ramp_to_200N': 200.0, 'ramp_to_500N': 500.0, 'lift_flow_held': None}
    tc_fin = np.array([q['t_conf_s'] for q in pool if q['t_conf_s'] is not None])
    nr_min = 0.05 + float(tc_fin.min())                 # support of n_run = U(0.05, 0.30) + t_conf (finite)
    assert float(n_run.min()) >= nr_min - 1e-12 and float(n_run.min()) - nr_min < 1e-3
    N_S = float(len(base))
    SUB = slice(0, 20000)                               # the parent's population subset (cross-check only)

    def hold_classes(seq, conv, mode, sub=None):
        e, lit, has, gapV, out = post_light(seq, conv, sub=sub, modes=(mode,))
        ta, dg, Fg = out[mode]
        trip = has & (dg >= A3_DETECT_S)
        n = float(len(lit))
        r = dict(P_no_light=float((~lit).mean()), P_success=float((lit & ~trip).mean()), P_light=float(lit.mean()),
                 P_trip=float(trip.mean()), latest_trip_mc_s=(float((ta[trip] + A3_DETECT_S).max()) if trip.any() else None),
                 earliest_trip_mc_s=(float((ta[trip] + A3_DETECT_S).min()) if trip.any() else None))
        tt = ta[trip]
        for H in HOLDS:
            He = max(H, FRAME_S)
            r[f'opt|{H:.2f}'] = float((tt >= He).sum() / n)
            r[f'cons|{H:.2f}'] = float((tt + A3_DETECT_S > He).sum() / n)
        return r

    def trip_sup(seq, mode):
        """Deterministic latest A3 trip after E2 over the support of n_run (slug-1 lights within W)."""
        P1, S1, C1, S2, C2 = seq
        if C1 <= 0.0:
            return None
        t1 = S1 * DEAD
        nr_hi = min(t1, W - t_lift - PURGE * P1)
        if nr_hi < nr_min:
            return None
        rem = np.linspace(t1 - nr_hi, t1 - nr_min, 20001)
        ta = Finv(FC[mode], rem); te = Finv(FC[mode], rem + PURGE * C1)
        ok = (te - ta) >= A3_DETECT_S
        return float((ta[ok] + A3_DETECT_S).max()) if ok.any() else None

    # ---- (1) v2.4a named states reproduced on the full set (H = 10 ms optimistic = the v2.4a class)
    named = {}
    for key, v in PJ['named_states'].items():
        seq = tuple(v['sequence_P1_S1_C1_S2_C2_cm3'])
        named[key] = dict(sequence_P1_S1_C1_S2_C2_cm3=list(seq))
        for conv in ('paused', 'restart'):
            named[key][conv] = {}
            for mo in MODES:
                hc = hold_classes(seq, conv, mo)
                ref = v[conv][mo]
                assert abs(hc['opt|0.01'] - ref['P_released_then_A3']) < 1e-12, (key, conv, mo, hc['opt|0.01'], ref['P_released_then_A3'])
                assert abs(hc['P_success'] - ref['P_success']) < 1e-12 and abs(hc['P_no_light'] - ref['P_no_light']) < 1e-12
                hc['latest_trip_sup_s'] = trip_sup(seq, mo)
                named[key][conv][mo] = hc
    print('named states reproduced', flush=True)

    # ---- (2) all PURGE NOT RUN records
    raw = RG.stream_records(os.path.join(d, 'purge_duration_v2p4_trade.json.raw.json.gz'), ('nopurge|',))
    recs = []
    for k, r in raw.items():
        p = k.split('|')
        assert len(p) == 9 and p[0] == 'nopurge'
        sq = tuple(round(float(r[x]), 4) for x in ('P1', 'S1', 'C1', 'S2', 'C2'))
        assert sq[4] == 0.0, (k, sq)                  # no second void in any record
        recs.append(dict(key=k, lining=p[1][3:], m=p[2], thermal_case=p[3], bracket=p[4], tag=p[5], theta_deg=float(p[6]),
                         az_deg=float(p[7]), series=p[8], seq=sq))
    assert len(recs) == 2160 and {r['theta_deg'] for r in recs} == {0.0, 2.0}
    seqs = sorted({r['seq'] for r in recs})
    print('records', len(recs), 'unique sequences', len(seqs), flush=True)
    # cross-check: v2.4a population (parent subset, pool ramp) per convention
    for lin in ('0.0', '1.0'):
        for fam in ('LO', 'HI'):
            sel = [r for r in recs if r['lining'] == lin and r['bracket'] == fam]
            ref = PJ['population_0_2deg'][f'lin{lin}|{fam}']['mean_over_records_pool_ramp_by_convention']
            cache = {}
            for conv in ('paused', 'restart'):
                acc = 0.0
                for r in sel:
                    ck = (r['seq'], conv)
                    if ck not in cache:
                        e, lit, has, gapV, out = post_light(r['seq'], conv, sub=SUB, modes=('ramp_pool_Fcmd',))
                        ta, dg, Fg = out['ramp_pool_Fcmd']
                        cache[ck] = float(((ta >= FRAME_S) & (dg >= A3_DETECT_S) & has).mean())
                    acc += cache[ck]
                assert abs(acc / len(sel) - ref[conv]['P_released_then_A3']) < 1e-12, (lin, fam, conv, acc / len(sel), ref[conv])
    print('v2.4a population reproduced', flush=True)

    T0 = time.time()
    SC = {}
    for i, sq in enumerate(seqs):
        for mo in MODES:
            a = hold_classes(sq, 'paused', mo); b = hold_classes(sq, 'restart', mo)
            for H in HOLDS:                                # the trip classes do not depend on the convention (slug-1 voids only)
                assert a[f'opt|{H:.2f}'] == b[f'opt|{H:.2f}'] and a[f'cons|{H:.2f}'] == b[f'cons|{H:.2f}']
            assert a['P_trip'] == b['P_trip']
            SC[(sq, mo)] = dict(paused=a, restart=b, sup=trip_sup(sq, mo))
        if i % 200 == 0:
            print('seq', i, round(time.time() - T0, 1), 's', flush=True)

    def rec_row(r, mo):
        c = SC[(r['seq'], mo)]; a, b = c['paused'], c['restart']
        w = a if a['P_success'] <= b['P_success'] else b            # worst convention (lower P_success)
        return a, b, w, c['sup'], r

    def lt_of(x):
        v = [y for y in (x[2]['latest_trip_mc_s'], x[3]) if y is not None]
        return max(v) if v else -1.0

    groups = {}
    for lin in ('0.0', '1.0', 'both'):
        for fam in ('LO', 'HI'):
            sel = [r for r in recs if (lin == 'both' or r['lining'] == lin) and r['bracket'] == fam]
            g = dict(n_records=len(sel))
            for mo in MODES:
                rows = [rec_row(r, mo) for r in sel]
                lt_mc = [x[2]['latest_trip_mc_s'] for x in rows if x[2]['latest_trip_mc_s'] is not None]
                lt_sup = [x[3] for x in rows if x[3] is not None]
                latest = max(lt_mc + lt_sup) if (lt_mc or lt_sup) else None
                gm = dict(latest_trip_mc_s=max(lt_mc) if lt_mc else None, latest_trip_sup_s=max(lt_sup) if lt_sup else None,
                          hold_needed_s=(math.ceil(round((latest + FRAME_S) * 100.0, 9)) / 100.0) if latest is not None else None,
                          hold_within_W=(latest is not None and latest + FRAME_S <= W),
                          n_records_with_trip=sum(1 for x in rows if x[2]['P_trip'] > 0.0),
                          mean_P_success_worst_convention=float(np.mean([x[2]['P_success'] for x in rows])),
                          mean_P_no_light_worst_convention=float(np.mean([x[2]['P_no_light'] for x in rows])),
                          mean_P_trip=float(np.mean([x[2]['P_trip'] for x in rows])), by_hold={})
                if latest is not None:
                    arg = max(rows, key=lt_of)
                    gm['latest_trip_record'] = dict(key=arg[4]['key'], sequence_P1_S1_C1_S2_C2_cm3=list(arg[4]['seq']), latest_trip_s=lt_of(arg),
                                                    P_light=arg[2]['P_light'], P_trip=arg[2]['P_trip'])
                for H in HOLDS:
                    o = np.array([x[2][f'opt|{H:.2f}'] for x in rows]); cns = np.array([x[2][f'cons|{H:.2f}'] for x in rows])
                    gm['by_hold'][f'{H:.2f}'] = dict(
                        optimistic=dict(mean=float(o.mean()), max=float(o.max()), n_records_gt_1e3=int((o > 1e-3).sum())),
                        conservative=dict(mean=float(cns.mean()), max=float(cns.max()), n_records_gt_1e3=int((cns > 1e-3).sum())))
                g[mo] = gm
            groups[f'lin{lin}|{fam}'] = g

    # per-record CSV (one row per record and profile)
    hdr = (['record_key', 'lining', 'barrier_or_open', 'thermal_case', 'bracket', 'tag', 'theta_deg', 'az_deg', 'series',
            'P1_cm3', 'S1_cm3', 'C1_cm3', 'S2_cm3', 'C2_cm3', 'profile', 'P_no_light_paused', 'P_no_light_restart', 'P_success_paused',
            'P_success_restart', 'P_A3_trip', 'latest_trip_mc_s', 'latest_trip_sup_s']
           + [f'P_released_then_A3_opt_H{H:.2f}' for H in HOLDS] + [f'P_released_then_A3_cons_H{H:.2f}' for H in HOLDS])
    with open(out_csv, 'w', newline='') as fh:
        wr = csv.writer(fh); wr.writerow(hdr)
        for r in recs:
            for mo in MODES:
                a, b, w, sup, _ = rec_row(r, mo)
                fmt = lambda x: '' if x is None else f'{x:.6f}'
                wr.writerow([r['key'], r['lining'], r['m'], r['thermal_case'], r['bracket'], r['tag'], r['theta_deg'], r['az_deg'], r['series']]
                            + [f'{x:.4f}' for x in r['seq']] + [mo, fmt(a['P_no_light']), fmt(b['P_no_light']), fmt(a['P_success']),
                                                                 fmt(b['P_success']), fmt(a['P_trip']), fmt(a['latest_trip_mc_s']), fmt(sup)]
                            + [fmt(a[f'opt|{H:.2f}']) for H in HOLDS] + [fmt(a[f'cons|{H:.2f}']) for H in HOLDS])

    res = dict(version='v2.4b', date='2026-10-13', script=os.path.basename(__file__), script_sha256_16=sha16(os.path.abspath(__file__)),
               request='REV-COMB-3 R3-01; LEAD CHANGELOG line 194 (3): release hold as a function of the post-E2 command profile over all '
                       'PURGE NOT RUN records + one 10 ms frame; per-record classes for GNC',
               inputs={**{k: v for k, v in RG.EXPECT.items()}, **EXPECT_EXTRA, **EXPECT_SRC, PARENT_PY: EXPECT_PARENT_PY,
                       OUTCOMES_PY: EXPECT_OUTCOMES_PY, os.path.basename(outcomes_json): EXPECT_OUTCOMES_JSON,
                       os.path.basename(map_fn): sha16(map_fn)},
               constants=dict(W_s=W, PURGE_s_per_cm3=PURGE, DEAD_s_per_cm3=DEAD, t_lift_s=t_lift, A3_detect_s=A3_DETECT_S, frame_s=FRAME_S,
                              ramp_N_s=RAMP_N_S, F_lift_N=F_LIFT, n_samples=int(len(base)), n_run_min_support_s=nr_min,
                              holds_s=list(HOLDS), profiles=list(MODES)),
               definitions=dict(
                   release='first release opportunity E2 + max(H, 10 ms); release term Pc >= 3.0 bar abs (E2 in the latency model is Pc > 3 bar '
                           'abs held 10 ms, so the term is true at E2 until a gap arrives)',
                   optimistic='released then A3 iff the gap arrives at or after the release',
                   conservative='released then A3 iff the A3 trip (gap arrival + 22 ms) comes after the release',
                   A3_before_release='P_A3_trip - P_released_then_A3 (abort with the drogue attached)',
                   success='light and no gap lasting >= 22 ms; independent of H',
                   hold_needed='latest A3 trip over the records of the group (max of MC and deterministic supremum) + 10 ms, rounded up to 10 ms',
                   worst_convention='per record the paused/restart convention with the lower P_success (the trip classes are identical in both)'),
               named_states=named, groups=groups, n_records=len(recs), n_unique_sequences=len(seqs),
               csv=dict(file=os.path.basename(out_csv), rows=len(recs) * len(MODES), columns=hdr),
               notes=['R3-12: in the latency model E2 is Pc > 3 bar abs held 10 ms; the firmware E2 is the relative rule. At the 0.2039 mm start '
                      'lift the lit plateau is 2.66-3.11 bar abs, so with the command held at the start level the Pc >= 3.0 bar term can be false '
                      'and the release waits for the b7 term (E2 + 0.10 s): read the H = 0.10 s row for those corners. This moves probability '
                      'from released-then-A3 to A3-before-release; P(success) is unchanged.',
                      'R3-12: lift basis: PURGE s/cm3 is the 0.2039 mm value; t_lift (29.6 ms) and the confirmation-time pool come from the '
                      '0.2192 mm runs (t_lift at 0.2039 mm is 28.7 ms). Not re-run; the hold values move by < 1 ms of t_lift.',
                      'The hold adds no success: it moves released-then-A3 to A3-before-release. Any P gain must come from records that '
                      'light without a gap trip; the cost of the longer hold is GNC\'s (REPORT §7.3: GNC found a 0.4 s hold costs P).'],
               tags=dict(classes='SIM on ASSUMED delays (rg01 set reproduced) + DERIVED line states (records not re-run); post-light timing DERIVED '
                                 'approximation (parent); A3 rule per REPORT v2.4 7.4; lights during vapour not modelled',
                         population='bracket records, NOT probability-weighted; means are unweighted over records'))
    json.dump(res, open(out_f, 'w'), indent=1, default=float)
    for gk, g in groups.items():
        for mo in MODES:
            gm = g[mo]
            print(f"{gk:12s} {mo:15s} latest trip mc {gm['latest_trip_mc_s']} sup {gm['latest_trip_sup_s']} -> hold {gm['hold_needed_s']} "
                  f"(within W {gm['hold_within_W']}); P_succ {gm['mean_P_success_worst_convention']:.3f} P_trip {gm['mean_P_trip']:.3f}")
            print('   ', ' '.join(f"H{H:.2f}:{gm['by_hold'][f'{H:.2f}']['optimistic']['mean']:.3f}/{gm['by_hold'][f'{H:.2f}']['optimistic']['max']:.2f}/"
                                  f"{gm['by_hold'][f'{H:.2f}']['optimistic']['n_records_gt_1e3']}"
                                  f"(c{gm['by_hold'][f'{H:.2f}']['conservative']['mean']:.3f}/{gm['by_hold'][f'{H:.2f}']['conservative']['max']:.2f})"
                                  for H in HOLDS))
    print('wrote', out_f, sha16(out_f), out_csv, sha16(out_csv), round(time.time() - T0, 1), 's')


if __name__ == '__main__':
    main(*sys.argv[1:6])
