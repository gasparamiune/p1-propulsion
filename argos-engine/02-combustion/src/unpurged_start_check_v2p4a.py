"""Unpurged relight start and tank-outlet coverage during PURGE (Combustion v2.4a, 2026-10-13).

Asked by the coordinator after GNC rev2 (LEAD CHANGELOG line 175 (3)): the FC no longer delays T_fire for the purge; if PURGE has
not committed by the plain relight trigger minus 1.7 s, the relight proceeds UNPURGED (PURGE NOT RUN LO / HI states).  Two checks:
  (1) does an unpurged start carry a hazard outside Combustion's abort model (P_abort 0.242 LO, 1.0 HI)?
  (2) tank-outlet coverage during the PURGE flow, from GNC's inputs (purge_outlet_inputs.json 47b4deb96ea22043).

Nothing here re-runs the purge model or the line-state model.  Part A reproduces the rg01_line_states_v2p4 ignition-delay set
(200 000 samples, seed 2024; asserted against the published P_abort of the PURGE NOT RUN LO worst state) and asks what the abort model
does not: when a light happens inside a liquid slug, which vapour gap follows it, when does it reach the pintle after E2 and how long
does it last.  The abort model counts such a light as a success ("post-light voids are not modelled").
Part B estimates the A3 ratio during a post-light vapour gap (CEA c*, flux ratio from the model's PURGE/DEAD constants).
Part C bounds liquid re-admission after an A3 trip (pintle closing at the servo speed of start_latency_v2p4).
Part D screens tank-outlet coverage with the geometry that exists (mechanical.json tank tube, internal length) and lists what is missing.

usage: python -I unpurged_start_check_v2p4a.py DATA_V2P4_DIR THROTTLE_MAP_S230 GNC_PURGE_OUTLET_INPUTS OUT_JSON
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


def main(d, map_fn, gnc_fn, out_f):
    for k, hsh in {**RG.EXPECT, **EXPECT_EXTRA}.items():
        assert sha16(os.path.join(d, k)) == hsh, (k, sha16(os.path.join(d, k)))
    for k, hsh in EXPECT_SRC.items():
        assert sha16(os.path.join(HERE, k)) == hsh, (k, sha16(os.path.join(HERE, k)))
    assert sha16(gnc_fn) == EXPECT_GNC, sha16(gnc_fn)
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

    def summarise(seq, conv):
        e, lit, has, gapV, out = post_light(seq, conv)
        r = dict(sequence_P1_S1_C1_S2_C2_cm3=list(seq), convention=conv, P_light_within_W=float(lit.mean()),
                 P_light_then_vapour_gap=float(has.mean()),
                 share_of_lights_followed_by_gap=float(has.sum() / max(lit.sum(), 1)))
        if has.any():
            r['gap_volume_cm3'] = sorted({round(float(x), 4) for x in gapV[has]})
            for lab, (ta, dg, Fg) in out.items():
                a, g_, f_ = ta[has], dg[has], Fg[has]
                r[lab] = dict(arrival_after_E2_s=dict(min=float(a.min()), median=float(np.median(a)), max=float(a.max())),
                              gap_duration_s=dict(min=float(g_.min()), median=float(np.median(g_)), max=float(g_.max())),
                              F_at_gap_N=dict(min=float(f_.min()), max=float(f_.max())),
                              P_gap_ge_A3_detect=float(((dg >= A3_DETECT_S) & has).mean()),
                              P_gap_after_release_frame=float(((ta >= FRAME_S) & has).mean()),
                              P_gap_after_b7_hold=float(((ta >= B7_HOLD_S) & has).mean()),
                              P_released_then_A3=float(((ta >= FRAME_S) & (dg >= A3_DETECT_S) & has).mean()))
        return r

    partA = dict(states={})
    for key in ('purge_not_run_unlined_LO_0-2deg_worst', 'purge_not_run_lined_LO_0-2deg_worst', 'purge_not_run_unlined_0-2deg_least',
                'purge_not_run_lined_0-2deg_least', 'purge_not_run_unlined_HI_0-2deg_worst', 'purged_unlined_Tp2.5_0-2deg_worst',
                'purged_lined_Tp2.5_0-2deg_worst', 'purged_lined_Tp2.2_robust_edge_0-2deg_worst'):
        s = states[key]; seq = tuple(s['sequence_P1_S1_C1_S2_C2_cm3'])
        partA['states'][key] = {c: summarise(seq, c) for c in ('paused', 'restart')}
        partA['states'][key]['published'] = dict(P_abort_W0p65=s['P_abort_W0p65'], convention=s['convention'])

    # all PURGE NOT RUN records at 0 and 2 deg (as rg01 Part 2), per unique sequence
    raw = RG.stream_records(os.path.join(d, 'purge_duration_v2p4_trade.json.raw.json.gz'), ('nopurge|',))
    NP = {}
    for k, r in raw.items():
        p = k.split('|')
        lin, m, case, tag, th, az, ser = p[1][3:], p[2], p[3] + '|' + p[4], p[5], float(p[6]), float(p[7]), p[8]
        NP[(lin, m, case, tag, th, az, ser)] = r
    assert len(NP) == 2 * 2 * 6 * 2 * 9 * 5, len(NP)
    SUB = slice(0, 20000)            # population scan on the first 20 000 samples of the set (resolution 5e-5)
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
        n_rec = sum(seqs.values()); rows_ = []
        for sq, cnt in seqs.items():
            worst = None
            for conv in ('paused', 'restart'):
                e, lit, has, gapV, out = post_light(sq, conv, sub=SUB, modes=('lift_flow_held', 'ramp_pool_Fcmd'))
                ta, dg, Fg = out['ramp_pool_Fcmd']; ta0, dg0, _ = out['lift_flow_held']
                v = dict(P_light=float(lit.mean()), P_light_gap=float(has.mean()),
                         P_released_then_A3_pool_ramp=float(((ta >= FRAME_S) & (dg >= A3_DETECT_S) & has).mean()),
                         P_released_then_A3_lift_flow=float(((ta0 >= FRAME_S) & (dg0 >= A3_DETECT_S) & has).mean()))
                if worst is None or v['P_released_then_A3_pool_ramp'] > worst[1]['P_released_then_A3_pool_ramp']:
                    worst = (conv, v)
            rows_.append((sq, cnt, worst))
        hz = [x for x in rows_ if x[2][1]['P_light_gap'] > 0.0]
        a3 = [x for x in rows_ if x[2][1]['P_released_then_A3_pool_ramp'] > 1e-3]
        top = max(rows_, key=lambda x: x[2][1]['P_released_then_A3_pool_ramp'])
        popsum[f'lin{lin}|{fam}'] = dict(
            n_records=n_rec, n_unique_sequences=len(seqs),
            n_records_light_then_gap=sum(c for _, c, _ in hz),
            n_records_released_then_A3_gt_1em3=sum(c for _, c, _ in a3),
            mean_over_records_P_released_then_A3_pool_ramp=float(sum(c * w[1]['P_released_then_A3_pool_ramp'] for _, c, w in rows_) / n_rec),
            max_P_released_then_A3_pool_ramp=dict(value=top[2][1]['P_released_then_A3_pool_ramp'], sequence=list(top[0]), convention=top[2][0],
                                                  P_light=top[2][1]['P_light'], P_light_gap=top[2][1]['P_light_gap']),
            max_P_light_gap=max(x[2][1]['P_light_gap'] for x in rows_))
    partA['population_0_2deg'] = popsum
    partA['population_note'] = ('all PURGE NOT RUN records at 0 and 2 deg (2 linings x LO/HI), per unique rounded sequence; the convention with the '
                                'larger P(released then A3) is kept; first 20 000 samples of the 200 000-sample set (resolution 5e-5); records '
                                'are bracket cases, not probability-weighted')
    partA['tags'] = ('SIM on ASSUMED delays (rg01 ignition-delay set reproduced, seed 2024, 200 000 samples) + DERIVED line states '
                     '(retained_vapour_v341_v2p4 / purge_duration_v2p4 records, not re-run). Post-light timing: flow held at the lift '
                     '(upper bound on times) or the start ramp 2500 N/s from 62.5 N to F_cmd with volumetric flow ~ mdot_ox(F) of the S230 map '
                     '(DERIVED approximation, ramp ASSUMED to start at E2). A3 trip when the gap lasts >= 22 ms (REPORT §7.4). Release: E2 in '
                     'the latency model is Pc > 3 bar abs held 10 ms, so the Pc >= 300 kPa release term is already true at E2; one TLM_FAST '
                     'frame <= 10 ms ASSUMED. Lights during vapour (pocket or gap) are not modelled.')

    # ------------------------------------------------------------------ Part B: A3 ratio during a post-light vapour gap
    import CoolProp.CoolProp as CP
    import cea_cards as CC
    import thermo_tables as TT
    from rocketcea.cea_obj import add_new_oxidizer
    CC.register_all()
    T = 286.7; Mw = 44.0128e-3
    h_ig = CP.PropsSI('H', 'T', 298.15, 'P', 10.0, 'NitrousOxide')
    h_l = CP.PropsSI('H', 'T', T, 'Q', 0, 'NitrousOxide'); h_v = CP.PropsSI('H', 'T', T, 'Q', 1, 'NitrousOxide')
    rho_l = CP.PropsSI('D', 'T', T, 'Q', 0, 'NitrousOxide'); rho_v = CP.PropsSI('D', 'T', T, 'Q', 1, 'NitrousOxide')
    hf_l = 82.05 + (h_l - h_ig) * Mw / 1000.0; hf_v = 82.05 + (h_v - h_ig) * Mw / 1000.0
    add_new_oxidizer('N2O_L287', f'oxid N2O_L287  N 2 O 1  wt%=100.\nh,kj/mol={hf_l:.3f}  t(k)={T:.2f}  rho={rho_l/1000:.3f}\n')
    add_new_oxidizer('N2O_V287', f'oxid N2O_V287  N 2 O 1  wt%=100.\nh,kj/mol={hf_v:.3f}  t(k)={T:.2f}\n')
    cl = TT.cea_obj('ABS_TYP_v1', 'N2O_L287'); cv = TT.cea_obj('ABS_TYP_v1', 'N2O_V287')
    r_ox = (rho_v * DEAD) / (rho_l * PURGE)            # vapour / liquid oxidiser mass flow through the same opening (model constants)
    Pb = SL.PAMB
    pts = []
    for F in (62.5, 100.0, 200.0, 500.0):
        Pc_l = float(np.interp(F, M['F'], M['Pc'])); OF_l = float(np.interp(F, M['F'], M['OF']))
        for n in (0.35, 0.5, 0.68):
            r_f = r_ox ** n; OF_v = OF_l * r_ox / r_f
            cs_l = cl.get_Cstar(Pc=Pc_l / 1e5, MR=OF_l)
            Pc_v = Pc_l * (r_ox * OF_l + r_f) / (OF_l + 1.0)
            for _ in range(3):
                Pc_v = Pc_l * (r_ox * OF_l + r_f) / (OF_l + 1.0) * cv.get_Cstar(Pc=max(Pc_v, 1.05e5) / 1e5, MR=OF_v) / cs_l
            pts.append(dict(F_N=F, Pc_lit_bar=Pc_l / 1e5, OF_lit=OF_l, n=n, OF_vapour=OF_v, Pc_vapour_bar_abs_choked=Pc_v / 1e5,
                            cstar_ratio=cv.get_Cstar(Pc=max(Pc_v, 1.05e5) / 1e5, MR=OF_v) / cs_l,
                            A3_ratio=(Pc_v - Pb) / (Pc_l - Pb)))
    partB = dict(rho_l_kg_m3=rho_l, rho_v_kg_m3=rho_v, vapour_to_liquid_oxidiser_flow=r_ox, baseline_Pa=Pb, points=pts,
                 A3_ratio_max=max(p['A3_ratio'] for p in pts), A3_threshold=0.40,
                 tag=('DERIVED: oxidiser flow ratio from the model constants (PURGE, DEAD) and CoolProp saturated densities at 286.7 K; fuel '
                      'flow ~ G_ox^n (n 0.35-0.68 bracket, ASSUMED); c* from CEA (RocketCEA, ABS_TYP_v1 card, vapour and liquid N2O cards '
                      'at 286.7 K), efficiency cancels; nozzle assumed choked; baseline = ambient; lit point from the S230 throttle map at 4.5 MPa. '
                      'Flame assumed to survive the gap (if it does not, the ratio is lower).'))

    # ------------------------------------------------------------------ Part C: liquid re-admission after an A3 trip (LO worst state)
    s = states['purge_not_run_unlined_LO_0-2deg_worst']; seq = tuple(s['sequence_P1_S1_C1_S2_C2_cm3'])
    e, lit, has, gapV, out = post_light(seq, 'restart')
    partC = {}
    lift_at = lambda F: np.interp(F, M['F'], M['lift'])
    mox_at = lambda F: np.interp(F, M['F'], M['mox'])
    for lab in ('lift_flow_held', 'ramp_to_200N', 'ramp_to_500N', 'ramp_pool_Fcmd'):
        ta, dg, Fg = out[lab]
        trip = has & (dg >= A3_DETECT_S)
        if lab == 'lift_flow_held':
            Fcmd_t = np.full_like(ta, F_LIFT)
        elif lab == 'ramp_to_200N':
            Fcmd_t = np.minimum(F_LIFT + RAMP_N_S * (ta + A3_DETECT_S), 200.0)
        elif lab == 'ramp_to_500N':
            Fcmd_t = np.minimum(F_LIFT + RAMP_N_S * (ta + A3_DETECT_S), 500.0)
        else:
            Fcmd_t = np.minimum(F_LIFT + RAMP_N_S * (ta + A3_DETECT_S), fcmd)
        t_close = SL.T_CMD + lift_at(Fcmd_t) / SL.V_PINTLE           # from the A3 command to the seat
        overlap = np.clip(A3_DETECT_S + t_close - dg, 0.0, None)      # liquid back at the seat before it closes
        # liquid admitted: flow falls ~linearly with the lift while closing; upper bound = full flow at the command point
        m_up = mox_at(Fcmd_t) * overlap * 1e3
        frac_left = np.clip(overlap / np.maximum(t_close, 1e-9), 0.0, 1.0)
        m_lin = mox_at(Fcmd_t) * overlap * 0.5 * frac_left * 1e3
        sel = trip & (overlap > 0.0)
        partC[lab] = dict(P_trip=float(trip.mean()), P_liquid_back_before_seat=float(sel.mean()),
                          liquid_g_upper=dict(median=float(np.median(m_up[sel])) if sel.any() else 0.0, max=float(m_up[sel].max()) if sel.any() else 0.0),
                          liquid_g_linear_closing=dict(median=float(np.median(m_lin[sel])) if sel.any() else 0.0, max=float(m_lin[sel].max()) if sel.any() else 0.0),
                          P_liquid_gt_FA1_fast_part=float((trip & (m_lin > FA1_FAST_PART_G)).mean()))
    partC['tag'] = ('DERIVED bound: A3 command 22 ms into the gap; ECU-to-servo 6.5 ms and servo speed 4 mm / 0.24 s (start_latency_v2p4 T_CMD, '
                    'V_PINTLE); lift at the commanded thrust from the S230 map; liquid back at the seat when the gap ends before the seat; mass '
                    'with the flow at the command point (upper) or falling linearly with the lift (linear). Only a hazard if the flame went out in '
                    'the gap (not modelled; IGN-1/stand evidence) and the chamber re-lights the admitted liquid late (FA-1 class, no torch: SOL1/'
                    'SOL2 off at E2).')

    # ------------------------------------------------------------------ Part D: tank-outlet coverage screening
    GN = json.load(open(gnc_fn))
    recs = GN['records']
    sf_raw = max(r['sf_axis_angle_deg_raw']['max'] for r in recs.values())
    sf_01 = max(r['sf_axis_angle_deg_0p1s']['max'] for r in recs.values())
    fax_min = min(r['fax_g']['min'] for r in recs.values()); fax_max = max(r['fax_g']['max'] for r in recs.values())
    m_liq = [min(min(r['m_liq_g']) for r in recs.values()), max(max(r['m_liq_g']) for r in recs.values())]
    tilt_max = max(v['tilt_max_in_flow_deg']['max'] for v in GN['distributions'].values())
    tilt_p99 = max(v['tilt_max_in_flow_deg']['p99'] for v in GN['distributions'].values())
    ID = 0.1016 - 2 * 0.003175; R = ID / 2; A = math.pi * R * R; L_int = 0.4449
    Q_m = 0.031241633637819454          # kg/s two-tap liquid purge (rg01 stuck_open, upper; GNC G73 29.2 g/s)
    Tlist = (283.15, 286.7, 289.5)
    dep = []
    for Tk in Tlist:
        rl = CP.PropsSI('D', 'T', Tk, 'Q', 0, 'NitrousOxide'); rv = CP.PropsSI('D', 'T', Tk, 'Q', 1, 'NitrousOxide')
        for mg in m_liq:
            h_ = mg / 1000.0 / rl / A
            dep.append(dict(T_K=Tk, rho_l=rl, m_liq_g=mg, depth_m=h_, ullage_length_m=L_int - h_))
    hmin = min(x['depth_m'] for x in dep)
    angles = dict(sf_raw_max=sf_raw, sf_0p1s_max=sf_01, tilt_p99=tilt_p99, tilt_max=tilt_max, illustrative_45=45.0)
    tiltcov = {k: dict(surface_drop_at_wall_m=R * math.tan(math.radians(a)), min_height_at_wall_m=hmin - R * math.tan(math.radians(a)))
               for k, a in angles.items()}
    theta_uncover_wall = math.degrees(math.atan(hmin / R))
    # Lubin & Springer (1967) dip (no-swirl) critical height for gas pull-through in a draining tank: h_c = 0.69 d (Fr' rho1/(rho1-rho2))^0.2,
    # Fr' = Q^2 / (g d^5): h_c is then independent of d.
    rl = CP.PropsSI('D', 'T', 286.7, 'Q', 0, 'NitrousOxide'); rv = CP.PropsSI('D', 'T', 286.7, 'Q', 1, 'NitrousOxide')
    Qv = Q_m / rl
    hc = 0.69 * (Qv ** 2 / (fax_min * 9.80665) * rl / (rl - rv)) ** 0.2
    # liquid spin-up by roll (Ekman time h / sqrt(nu * Omega)), nu of liquid N2O
    # CoolProp 8.0 has no N2O viscosity model: kinematic viscosity bracket 0.5e-7 to 2e-7 m2/s (ASSUMED; liquid N2O ~ 1e-7)
    nu_lo, nu_hi = 0.5e-7, 2.0e-7; nu = [nu_lo, nu_hi]
    roll_max = max(r['roll_rate_deg_s']['max'] for r in recs.values()); Om = math.radians(roll_max)
    t_ek = hmin / math.sqrt(nu_hi * Om)            # shortest spin-up time of the bracket
    # first lateral slosh mode of a flat-bottom cylinder
    w_sl = math.sqrt(1.8412 * fax_min * 9.80665 / R * math.tanh(1.8412 * hmin / R))
    partD = dict(
        gnc_inputs=dict(file=os.path.basename(gnc_fn), sha256_16=EXPECT_GNC, sf_axis_angle_deg_raw_max=sf_raw, sf_axis_angle_deg_0p1s_max=sf_01,
                        sf_angle_source='6 re-flown records only (run 0, largest-tilt, largest-rate per base); no 500-run distribution',
                        tilt_deg_p99=tilt_p99, tilt_deg_max=tilt_max, axial_g=[fax_min, fax_max], m_liq_g=m_liq, roll_deg_s_max=roll_max),
        tank_geometry_used=dict(ID_m=ID, internal_cyl_length_m=L_int, bulkheads='flat (14.0 mm plate, bolted, O-ring)',
                                source='interfaces/mechanical.json fixed_module.tank (v1 concept, not yet in CAD); 03-cad/calcs/HAND-CALCS.md',
                                tag='DATASHEET tube size / DESIGN concept'),
        liquid_depth=dep, min_depth_m=hmin,
        surface_tilt_at_wall=tiltcov,
        centre_outlet_note=('a planar surface tilted about the tank axis keeps the height above a bottom-centre outlet equal to the mean depth '
                            'until it meets the bottom; that needs tan(theta) > h/R'),
        wall_uncovering_angle_deg=theta_uncover_wall,
        dip_pull_through_LubinSpringer_h_c_m=hc,
        dip_pull_through_note='LITERATURE correlation (Lubin & Springer 1967, non-swirling drain, water/fuel-like liquids); h_c independent of the '
                              'outlet diameter in this form; applicability to near-saturated N2O TO-VERIFY',
        roll_spin_up_Ekman_s_min=t_ek, nu_liquid_m2_s_bracket_ASSUMED=nu, roll_rate_used_deg_s=roll_max,
        slosh_first_mode_Hz=w_sl / (2 * math.pi),
        missing=['outlet position on the aft bulkhead (centre or radius r_o) and diameter (MISSING: tank not in CAD)',
                 'any dip tube, sump, anti-vortex plate or screen (MISSING)',
                 'tank axis orientation in the vehicle and which bulkhead is aft (DESIGN intent: axial, outlet aft; not in CAD)',
                 'internal bulkhead face geometry (protrusions, port bosses) that changes the depth near the outlet (MISSING)',
                 'slosh amplitude under the transverse rates (sim6 liquid is a lumped mass; no slosh model)',
                 'specific-force angle distribution over the 500 runs (only 6 records given)'],
        tag=('DERIVED (geometry and CoolProp densities); GNC SIM inputs; LITERATURE screening correlations. Quasi-static only; not a physical '
             'approval.'))

    res = dict(version='v2.4a', date='2026-10-13', script=os.path.basename(__file__), script_sha256_16=sha16(os.path.abspath(__file__)),
               request='coordinator after GNC rev2 / LEAD CHANGELOG line 175 (3): unpurged start at the late-commit point; tank outlet coverage during PURGE',
               inputs={**{k: v for k, v in RG.EXPECT.items()}, **EXPECT_EXTRA, **EXPECT_SRC,
                       os.path.basename(map_fn): sha16(map_fn), os.path.basename(gnc_fn): EXPECT_GNC},
               constants=dict(W_s=W, PURGE_s_per_cm3=PURGE, DEAD_s_per_cm3=DEAD, t_lift_s=t_lift, A3_detect_s=A3_DETECT_S, b7_hold_s=B7_HOLD_S,
                              frame_s=FRAME_S, ramp_N_s=RAMP_N_S, F_lift_N=F_LIFT, FA1_fast_part_g=FA1_FAST_PART_G),
               partA_post_light_gap=partA, partB_A3_ratio_in_gap=partB, partC_liquid_readmission=partC, partD_tank_outlet=partD)
    json.dump(res, open(out_f, 'w'), indent=1, default=float)
    # ------------------------------------------------------------------ print a summary
    for key, v in partA['states'].items():
        for c in ('paused', 'restart'):
            x = v[c]
            line = f"{key:46s} {c:7s} Plit {x['P_light_within_W']:.4f} Plit+gap {x['P_light_then_vapour_gap']:.4f}"
            if 'ramp_pool_Fcmd' in x:
                y = x['ramp_pool_Fcmd']; z = x['lift_flow_held']
                line += (f" gapV {x['gap_volume_cm3']} | lift: arr {z['arrival_after_E2_s']['median']:.3f}/{z['arrival_after_E2_s']['max']:.3f} "
                         f"dur {z['gap_duration_s']['min']:.3f}-{z['gap_duration_s']['max']:.3f} | pool ramp: arr {y['arrival_after_E2_s']['min']:.3f}/"
                         f"{y['arrival_after_E2_s']['median']:.3f}/{y['arrival_after_E2_s']['max']:.3f} dur {y['gap_duration_s']['min']:.3f}-"
                         f"{y['gap_duration_s']['max']:.3f} F {y['F_at_gap_N']['min']:.0f}-{y['F_at_gap_N']['max']:.0f} P_rel+A3 {y['P_released_then_A3']:.4f} "
                         f"P_b7first {y['P_gap_after_b7_hold']:.4f}")
            print(line)
    for k, v in popsum.items():
        print(k, json.dumps(v))
    print('A3 ratio in gap: max %.3f; r_ox %.4f; rho_l %.1f rho_v %.1f' % (partB['A3_ratio_max'], r_ox, rho_l, rho_v))
    for p in pts:
        print('  F %5.1f n %.2f Pc_lit %.2f OF %.2f -> OF_v %.2f Pc_v %.2f c*r %.3f A3 %.3f' % (p['F_N'], p['n'], p['Pc_lit_bar'], p['OF_lit'], p['OF_vapour'], p['Pc_vapour_bar_abs_choked'], p['cstar_ratio'], p['A3_ratio']))
    for k, v in partC.items():
        print('C', k, json.dumps(v)[:400])
    print('D depth min %.4f m; h_c %.4f m; Ekman %.0f s; slosh %.2f Hz; wall-uncover %.1f deg; sf %.2f/%.2f deg; tilt p99 %.2f max %.2f'
          % (hmin, hc, t_ek, w_sl / (2 * math.pi), theta_uncover_wall, sf_raw, sf_01, tilt_p99, tilt_max))
    for k, v in tiltcov.items():
        print('   ', k, '%.4f %.4f' % (v['surface_drop_at_wall_m'], v['min_height_at_wall_m']))
    for x in dep:
        print('   ', x)
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:5])
