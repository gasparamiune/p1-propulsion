"""Decided bleed path and RG-01 line states for GNC's re-fly (Combustion v2.4, 2026-10-13).

Lead decisions (interfaces/CHANGELOG.md 2026-10-13, lines 160-161): the bleed path is set by its TOTAL flow, ~31 g/s
(1.0 mm-equivalent); a restrictor at each tap, areas summing to the 1.0 mm equivalent (F3); each valve >= 4x the restriction's
capacity, so the valves do not control (F1); scheduled purge 2.5 s; purge mass planned <= 76 g; design attitude theta <= 2 deg with a
balanced or axial vent; RG-01 stays BLOCKING until GNC re-flies on Combustion's re-routed-coil tables and CF-4.
Coordinator (2026-10-13): until Mechanical gives the tap restrictor areas, use two equal restrictors (0.707 mm each).

This script does NOT re-run the purge model.  purge_duration_v2p4 already ran exactly that path ('0.707|2tap': both taps,
0.707 mm each, Cd 0.70, valves not modelled = non-controlling) on the fine Tp grid (0.5-2.5 s, 0.1 s steps) at 0 and 2 deg, all
eight azimuths at 2 deg, with the inputs whose hashes it asserts; the model is deterministic.  A re-run would reproduce the same
numbers.  This script reduces the per-series results (raw file, streamed) into:
  Part 1  per tilt (0 and 2 deg separately) and lining (unlined, 1 mm PTFE): robust Tp, N2O vented, cap clearing, residual pocket
          at the lift and the governing case; the stuck-open flow of the path.
  Part 2  line states for GNC's re-fly, in the format of post_abort_pocket_v2p4 'line_states_for_gnc_44cm3': P_abort at W 0.65 s,
          E0 -> E2 median / p99 / max over all samples, 5 % quantiles of E0 -> E2 given a light.  Same 200 000-sample ignition
          set (seed 2024) and the same E0 -> E1 torch-gate sample as post_abort_pocket_v2p4 (reproduced and asserted).
  Part 3  the minimal case set for P_abort <= 1e-3 (with retained_table_v341_v2p4 for the no-purge combinations).
usage: python -I rg01_line_states_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import gzip, hashlib, json, math, os, re, sys
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import start_latency_v2p4 as SL

W = 0.65
LIM = 1e-3
PATH = '0.707|2tap'
TP_SCHED = 2.5
SLIPS = ('scons', 'swall', 's1.0', 's0.5')
CASES = ('isothermal|LO', 'hw+5K|LO', 'ARM_bay45C_liq24C|LO', 'isothermal|HI', 'hw+5K|HI', 'ARM_bay45C_liq24C|HI')
EXPECT = {'purge_duration_v2p4.json': '1ff6bfcd7d2f454c', 'purge_duration_v2p4_trade.json': '69e7192f63b5d8b8',
          'purge_duration_v2p4_trade_summary.json.gz': '5971815ccd035b29', 'purge_duration_v2p4_trade.json.raw.json.gz': '02c30eb2e6569e8d',
          'start_latency_v2p4.json': '809491fd86b91439', 'post_abort_pocket_v2p4.json': 'a786b42bb499d68a',
          'relight_vapour_order_v2p4.json': '78120ff97c0ac8dc', 'retained_table_v341_v2p4.json': '812cacc5b318e351'}
# open-loop subtractive estimate (stuck-open bleed during the burn)
LINE_LOSS_REF = (2.5e5, 0.25)        # Pa at kg/s, ~ mdot^2 (ASSUMED, grain_q1d; as ignition_detect_v2p4 part E)
MDOT_100 = 0.26408                   # kg/s oxidiser at 100 % (DERIVED, v2.3)
DP_INJ_OVER_PC_100, PC_100 = 0.907, 25.0e5   # combustion.json v2.3 operating_points.max_thrust (SIM)


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def stream_records(fn, prefixes):
    """Stream the raw per-series file; return {key: dict} for keys starting with one of prefixes (records hold no nested dicts)."""
    pat = re.compile(r'"((?:' + '|'.join(re.escape(p) for p in prefixes) + r')[^"]*)":\{([^{}]*)\}')
    out = {}; buf = ''
    with gzip.open(fn, 'rt') as fh:
        while True:
            chunk = fh.read(1 << 25)
            if not chunk:
                break
            buf += chunk
            end = 0
            for mm in pat.finditer(buf):
                out[mm.group(1)] = json.loads('{' + mm.group(2) + '}')
                end = mm.end()
            buf = buf[max(end, len(buf) - 20000):]
    for mm in pat.finditer(buf):
        out[mm.group(1)] = json.loads('{' + mm.group(2) + '}')
    return out


def main(d, out_f):
    for k, h in EXPECT.items():
        assert sha16(os.path.join(d, k)) == h, (k, sha16(os.path.join(d, k)))
    PD = json.load(open(os.path.join(d, 'purge_duration_v2p4.json')))
    assert PD['inputs']['purge_duration_v2p4_trade.json'] == EXPECT['purge_duration_v2p4_trade.json']
    assert PD['inputs']['purge_duration_v2p4_trade_summary.json.gz'] == EXPECT['purge_duration_v2p4_trade_summary.json.gz']
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    PURGE = VO['purge_s_per_cm3']; DEAD = VO['liquid_plug_dead_time_s_per_cm3']
    PA = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
    RT = json.load(open(os.path.join(d, 'retained_table_v341_v2p4.json')))
    # ------------------------------------------------------------------ ignition-delay set, as post_abort_pocket_v2p4 (same stream)
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    rows = J['part1_runs']['v']; lifts = J['ignition_lifts']
    pool = [r for r in rows if r['ramp'] == 2500.0 and r['F_cmd'] in (200.0, 500.0) and r['state'] == 'A1_relight'
            and r['frac'] == 0.125 and r.get('loop_K', 0.0) == 15.0]
    N = 200000; rng = np.random.default_rng(2024)
    h = lifts['A1_relight|0.125']['lift_m']; t_lift = SL.T_CMD + h / SL.V_PINTLE + 0.010
    idx = rng.integers(0, len(pool), N)
    tc = np.array([np.nan if q['t_conf_s'] is None else q['t_conf_s'] for q in pool])[idx]
    e1_all = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)
    ig = rng.uniform(0.05, 0.30, N)
    base_all = t_lift + ig + tc
    fin = np.isfinite(base_all)
    base = base_all[fin]; e1 = e1_all[fin]
    assert abs(float(base.max()) - PA['E1_E2_liquid_s']['max']) < 1e-12
    assert abs(float(np.median(base)) - PA['E1_E2_liquid_s']['median']) < 1e-12
    n_run = base - t_lift

    def e12(seq, conv):
        P1, S1, C1, S2, C2 = seq
        if C1 <= 0.0 and C2 <= 0.0:
            # a single pocket followed by liquid: no gap, so neither convention adds anything (the trade's 'restart' adds the
            # dead time of the 1 cm3 tank-liquid placeholder, +0.023 s, conservative; corrected here)
            return base + PURGE * P1
        t1, t2 = S1 * DEAD, S2 * DEAD
        if conv == 'paused':
            return base + PURGE * P1 + np.where(n_run > t1, PURGE * C1, 0.0) + np.where(n_run > t1 + t2, PURGE * C2, 0.0)
        return base + PURGE * P1 + np.where(n_run > t1, t1 + PURGE * C1 + np.where(n_run > t2, t2 + PURGE * C2, 0.0), 0.0)

    def table(e):
        ok = e <= W
        E02 = e1 + e
        return dict(P_abort_W0p65=float(1.0 - ok.mean()),
                    E0_E2_all_s=dict(median=float(np.median(E02)), p99=float(np.percentile(E02, 99)), max=float(E02.max())),
                    E0_E2_given_light_quantiles_5pct_s=[round(float(np.percentile(E02[ok], q)), 4) for q in range(0, 101, 5)] if ok.any() else [],
                    E1_E2_max_s=float(e.max()))

    # reproduce the published 19 cm3 state (checks the E0 -> E1 sample and the format)
    ref = PA['line_states_for_gnc_44cm3']['v']['pocket_19cm3']
    chk = table(base + PA['by_lift']['lift_0.2039mm_v2p8']['purge_s_per_cm3'] * 19.0)
    assert abs(chk['P_abort_W0p65'] - ref['P_abort_W0p65']) < 1e-12 and abs(chk['E0_E2_all_s']['median'] - ref['E0_E2_all_s']['median']) < 1e-12
    assert abs(PA['by_lift']['lift_0.2039mm_v2p8']['purge_s_per_cm3'] - PURGE) < 1e-9

    # ------------------------------------------------------------------ stream the per-series records
    raw = stream_records(os.path.join(d, 'purge_duration_v2p4_trade.json.raw.json.gz'), ('purge' + PATH + '|', 'nopurge|'))
    P = {}; NP = {}
    for k, r in raw.items():
        p = k.split('|')
        if k.startswith('purge'):
            # purge0.707|2tap|slab|TpX|linY|m|case_a|case_b|tag|th|az|series
            slab, Tp, lin, m, case, tag, th, az, ser = p[2], float(p[3][2:]), p[4][3:], p[5], p[6] + '|' + p[7], p[8], float(p[9]), float(p[10]), p[11]
            P[(slab, Tp, lin, m, case, tag, th, az, ser)] = r
        else:
            lin, m, case, tag, th, az, ser = p[1][3:], p[2], p[3] + '|' + p[4], p[5], float(p[6]), float(p[7]), p[8]
            NP[(lin, m, case, tag, th, az, ser)] = r
    TPS = sorted({k[1] for k in P})
    n_expect = len(TPS) * 4 * 2 * 2 * 6 * 2 * 9 * 5
    assert len(P) == n_expect, (len(P), n_expect)
    assert len(NP) == 2 * 2 * 6 * 2 * 9 * 5, len(NP)
    Pt = lambda r: max(r['P_paused'], r['P_restart'])          # as the trade (restart adds the placeholder dead time to single pockets)
    def single(r):
        sq = r['seq'] if 'seq' in r else [r['P1'], r['S1'], r['C1'], r['S2'], r['C2']]
        return sq[2] <= 0.0 and sq[4] <= 0.0
    Pm = lambda r: r['P_paused'] if single(r) else max(r['P_paused'], r['P_restart'])   # corrected: single pockets have no restart
    Pp = lambda r: r['P_paused']

    # ------------------------------------------------------------------ Part 1
    def sel(slabs, lin, ths):
        return [(k, r) for k, r in P.items() if k[0] in slabs and k[2] == lin and k[6] in ths]

    part1 = {}
    for lin in ('0.0', '1.0'):
        for th_lab, ths in (('0deg', (0.0,)), ('2deg', (2.0,)), ('0-2deg', (0.0, 2.0))):
            for s_lab, slabs in [(s, (s,)) for s in SLIPS] + [('all_slips', SLIPS)]:
                rs = sel(slabs, lin, ths)
                worst = {}; argw = {}; n2 = {}; tco = {}; p1 = {}; ncap = {}
                for k, r in rs:
                    Tp = k[1]; v = Pm(r)
                    if v > worst.get(Tp, -1.0):
                        worst[Tp] = v; argw[Tp] = k
                    lo, hi = n2.get(Tp, (1e9, -1e9)); n2[Tp] = (min(lo, r['N2O_g']), max(hi, r['N2O_g']))
                    if r['t_cap_out'] >= 0:
                        tco[Tp] = max(tco.get(Tp, -1.0), r['t_cap_out'])
                    else:
                        ncap[Tp] = ncap.get(Tp, 0) + 1
                    lo, hi = p1.get(Tp, (1e9, -1e9)); p1[Tp] = (min(lo, r['P1']), max(hi, r['P1']))
                Tp_r = None
                for i, Tp in enumerate(TPS):
                    if all(worst[x] <= LIM for x in TPS[i:]):
                        Tp_r = Tp; break
                conv_r = {}
                for lab_c, fP in (('trade_max_of_conventions', Pt), ('paused_only', Pp), ('corrected', Pm)):
                    wc = {}
                    for k, r in rs:
                        wc[k[1]] = max(wc.get(k[1], 0.0), fP(r))
                    conv_r[lab_c] = next((Tp for i, Tp in enumerate(TPS) if all(wc[x] <= LIM for x in TPS[i:])), None)
                gov = None
                if Tp_r is not None and TPS.index(Tp_r) > 0:
                    Tm = TPS[TPS.index(Tp_r) - 1]; kk = argw[Tm]
                    gov = dict(Tp_s=Tm, P_abort=worst[Tm], slip=kk[0], element=kk[3], heat_case=kk[4], reading=kk[5], tilt_deg=kk[6], az_deg=kk[7], series=kk[8],
                               seq_P1_S1_C1_S2_C2_cm3=P[kk]['seq'], cap_left_cm3=P[kk]['cap_left'], VH_left_cm3=P[kk]['VH_left'])
                part1[f'lin{lin}|{th_lab}|{s_lab}'] = dict(
                    Tp_robust_s=Tp_r, Tp_robust_s_by_convention=conv_r, margin_at_scheduled_2p5_s=(round(TP_SCHED - Tp_r, 2) if Tp_r is not None else None),
                    worst_P_by_Tp={f'{t:.1f}': worst[t] for t in TPS},
                    N2O_g_at_Tp_robust=list(n2[Tp_r]) if Tp_r is not None else None, N2O_g_at_2p5s=list(n2[TP_SCHED]),
                    t_cap_out_max_s_at_2p5s=tco.get(TP_SCHED), n_records_cap_not_cleared_at_2p5s=ncap.get(TP_SCHED, 0), n_records=len(rs) // len(TPS),
                    residual_P1_cm3_at_2p5s=list(p1[TP_SCHED]),
                    governing_just_below_Tp_robust=gov)
    # cross-check against purge_duration_v2p4 (tilts combined)
    for lin in ('0.0', '1.0'):
        for s in SLIPS:
            a = PD['robust'][f'{PATH}|lin{lin}|{s}']; b = part1[f'lin{lin}|0-2deg|{s}']
            assert a['Tp_robust_s'] == b['Tp_robust_s_by_convention']['trade_max_of_conventions'], (lin, s, a['Tp_robust_s'], b)
            for x, y in zip(a['N2O_g_at_2p5s'], b['N2O_g_at_2p5s']):
                assert abs(x - y) <= 1e-3 * max(abs(x), 1.0), (lin, s, x, y)
    # stuck-open flow
    fl = PD['flows'][PATH]
    m_bleed = fl['liquid_g_s_all_taps'] * 1e-3
    a_, m_ref = LINE_LOSS_REF
    dp_extra = a_ * ((MDOT_100 + m_bleed) ** 2 - MDOT_100 ** 2) / m_ref ** 2
    dp_inj = DP_INJ_OVER_PC_100 * PC_100
    stuck = dict(path='two equal restrictors 0.707 mm (Cd 0.70 ASSUMED), valves non-controlling (F1), both taps liquid',
                 coast_state='46.45 bar, 289.5 K (Dyer 56 843 kg/m2s liquid, HEM 15 450 kg/m2s vapour)',
                 liquid_g_s_total=fl['liquid_g_s_all_taps'], liquid_g_s_per_tap=fl['mdot_liquid_g_s_per_tap'], vapour_g_s_per_tap=fl['mdot_vapour_g_s_per_tap'],
                 fraction_of_100pct_flow=fl['fraction_of_100pct_flow'],
                 gnc_S313_bleed_g_s=31.3, gnc_S313_covers=bool(31.3 >= fl['liquid_g_s_all_taps']),
                 additive_reasoning=('The taps sit on the feed upstream of the pintle and draw from the tank in parallel with the injector. While the Pc loop is '
                                     'closed it restores the injector flow, so the bleed is ADDITIVE tank outflow. Open loop (or at the pintle travel limit) the '
                                     'extra line loss subtracts a little from the injector: see open_loop_estimate. At the ignition lift the injector loses '
                                     '<= 0.09 % (ignition_detect_v2p4 part E, 19-20 g/s).'),
                 open_loop_estimate=dict(extra_line_loss_bar=dp_extra / 1e5, dP_inj_100pct_bar=dp_inj / 1e5,
                                         injector_flow_change_pct=-50.0 * dp_extra / dp_inj,
                                         tag='DERIVED: line loss ASSUMED 2.5 bar at 0.25 kg/s ~ mdot^2; dP_inj/Pc 0.907 at 100 % (SIM, combustion.json v2.3); square-root law'),
                 bound_note='Upper bound: the flux is the saturated-liquid Dyer flux at the coast tank state; it falls with tank pressure in blowdown and with the line loss upstream of the taps during the burn.',
                 tag='DERIVED (Dyer/HEM, Cd 0.70 ASSUMED)')

    # ------------------------------------------------------------------ Part 2: line states
    def worst_state(recs, seq_of, p_of, top=40):
        """Pick the worst sequence: highest P_abort (record value), then the largest bound on the added delay; verify the top few in full."""
        cand = {}
        for k, r in recs:
            sq = tuple(round(float(x), 4) for x in seq_of(r))
            bound = PURGE * (sq[0] + sq[2] + sq[4]) + DEAD * (sq[1] + sq[3])
            key = sq
            if key not in cand or p_of(r) > cand[key][0]:
                cand[key] = (p_of(r), bound, k)
        ranked = sorted(cand.items(), key=lambda kv: (kv[1][0], PURGE * (kv[0][0]) + (PURGE * kv[0][2] if kv[0][1] * DEAD < n_run.max() else 0.0)), reverse=True)[:top]
        best = None
        for sq, (pv, bound, k) in ranked:
            for conv in ('paused', 'restart'):
                e = e12(sq, conv)
                tb = table(e)
                score = (tb['P_abort_W0p65'], tb['E0_E2_all_s']['p99'], tb['E0_E2_all_s']['max'])
                if best is None or score > best[0]:
                    best = (score, sq, conv, k, tb, pv)
        score, sq, conv, k, tb, pv = best
        assert tb['P_abort_W0p65'] >= pv - 1e-4, (tb['P_abort_W0p65'], pv, k)
        return dict(tb, sequence_P1_S1_C1_S2_C2_cm3=list(sq), convention=conv, case=list(k))

    def best_state(recs, seq_of):
        sq = min((tuple(round(float(x), 4) for x in seq_of(r)) for k, r in recs), key=lambda s: (s[0] + s[2] + s[4], s[0]))
        e = e12(sq, 'paused')
        return dict(table(e), sequence_P1_S1_C1_S2_C2_cm3=list(sq), convention='paused (identical: no slug gaps)' if sq[2] == 0 and sq[4] == 0 else 'paused')

    states = {}
    states['liquid_line'] = dict(table(base), sequence_P1_S1_C1_S2_C2_cm3=[0, 0, 0, 0, 0], note='reference: primed, liquid to the seat (v2.8 start)')
    for lin in ('0.0', '1.0'):
        ll = 'unlined' if lin == '0.0' else 'lined'
        for th_lab, ths in (('0-2deg', (0.0, 2.0)), ('0deg', (0.0,)), ('2deg', (2.0,))):
            for Tp in (TP_SCHED,):
                recs = [(k, r) for k, r in P.items() if k[1] == Tp and k[2] == lin and k[6] in ths]
                states[f'purged_{ll}_Tp{Tp:g}_{th_lab}_worst'] = worst_state(recs, lambda r: r['seq'], Pm)
                if th_lab == '0-2deg':
                    states[f'purged_{ll}_Tp{Tp:g}_{th_lab}_least'] = best_state(recs, lambda r: r['seq'])
    # truncated purge (unlined and lined): worst state by Tp, 0-2 deg
    trunc = {}
    for lin in ('0.0', '1.0'):
        for Tp in TPS:
            if Tp < 1.0 - 1e-9:
                continue
            recs = [(k, r) for k, r in P.items() if k[1] == Tp and k[2] == lin]
            ws = worst_state(recs, lambda r: r['seq'], Pm)
            trunc[f'lin{lin}|Tp{Tp:.1f}'] = dict(P_abort_W0p65=ws['P_abort_W0p65'], E0_E2_all_s=ws['E0_E2_all_s'], E1_E2_max_s=ws['E1_E2_max_s'],
                                                 sequence_P1_S1_C1_S2_C2_cm3=ws['sequence_P1_S1_C1_S2_C2_cm3'], convention=ws['convention'])
    for lin in ('0.0', '1.0'):
        ll = 'unlined' if lin == '0.0' else 'lined'
        Tr = part1[f'lin{lin}|0-2deg|all_slips']['Tp_robust_s']
        recs = [(k, r) for k, r in P.items() if abs(k[1] - Tr) < 1e-9 and k[2] == lin]
        states[f'purged_{ll}_Tp{Tr:g}_robust_edge_0-2deg_worst'] = worst_state(recs, lambda r: r['seq'], Pm)
    # purge not run (valve fails closed, trigger gate never released): re-routed coil alone, 0-2 deg
    npseq = lambda r: [r['P1'], r['S1'], r['C1'], r['S2'], r['C2']]
    for lin in ('0.0', '1.0'):
        ll = 'unlined' if lin == '0.0' else 'lined'
        for fam in ('LO', 'HI'):
            recs = [(k, r) for k, r in NP.items() if k[0] == lin and k[2].endswith(fam) and k[4] in (0.0, 2.0)]
            states[f'purge_not_run_{ll}_{fam}_0-2deg_worst'] = worst_state(recs, npseq, Pm)
        recs = [(k, r) for k, r in NP.items() if k[0] == lin and k[4] in (0.0, 2.0)]
        states[f'purge_not_run_{ll}_0-2deg_least'] = best_state(recs, npseq)
    states['bleed_fault_closure_unconfirmed'] = dict(
        same_as='purged_unlined_Tp2.5_0-2deg_worst',
        note=('LEAD (CHANGELOG line 160): if closure is not confirmed before E1 the relight proceeds and BLEED_FAULT goes to the FC. The line state '
              'at the lift is the purged state; the open bleed draws from the tank in parallel (injector -0.09 % at the lift), so E0 -> E2 is that of '
              'the purged state. Mass: up to 31.2 g/s additive from E0 until the end of the flight (stuck_open), GNC S313 arm.'))
    # ------------------------------------------------------------------ Part 3: minimal set
    A = RT['A_no_purge']
    def worst_np(lin):
        return max(v['P_abort'] for kk, v in A.items() if kk.startswith(f'lin{lin}|') and kk.split('|')[1] in ('0.0', '2.0'))
    def worst_pg(lin, Tp):
        return max(Pm(r) for k, r in P.items() if k[1] == Tp and k[2] == lin)
    minimal = dict(
        combinations_0_2deg_worst_P_abort={
            '(1) re-route alone': worst_np('0.0'),
            '(2) re-route + 1 mm PTFE lining': worst_np('1.0'),
            '(3) re-route + purge, decided path, Tp 2.5 s, unlined': worst_pg('0.0', TP_SCHED),
            '(4) re-route + lining + purge, decided path, Tp 2.5 s': worst_pg('1.0', TP_SCHED)},
        minimal_set=('(3): re-routed coil (CAD v3.4.1 traps) + pre-scheduled 2-tap purge on the decided path (a restrictor per tap, equal 0.707 mm, '
                     'valves non-controlling) for 2.5 s, ending 0.05 s before E0 + design attitude theta <= 2 deg held by a balanced or axial vent. '
                     'No lining. Needed Tp: unlined %.1f s, lined %.1f s (the lining lengthens it in the s 0.5 bracket).'
                     % (part1['lin0.0|0-2deg|all_slips']['Tp_robust_s'], part1['lin1.0|0-2deg|all_slips']['Tp_robust_s'])),
        what_each_element_removes=dict(
            reroute='the 44 cm3 inverted U of CAD v3.4 (superseded); leaves traps of 12.0-13.8 cm3 at 0 deg plus humps of up to 3.84 cm3 at 2 deg',
            purge='the HI head-trap overflow (whole segment vapour, P = 1) and the S1-side cap (ARM LO wet 0.24, hot-wall HI dry 0.65)',
            attitude='keeps the hose humps <= 3.84 cm3 (9.27 at 4 deg, 16.9 at 10 deg)',
            balanced_vent='keeps the purge jet from tilting the vehicle (single lateral 2.1 N jet: 1.18-1.85 deg, GNC relight_attitude_v1)'),
        conditions=['CF-4 confirms the purge model (tap flows, cap slip, hump sweep) and the zero-abort pocket (V_zero 18.86 cm3)',
                    'IGN-1/T1 ignition-delay p99.9 <= 0.30 s (moves V_zero)', 'Mechanical restrictor areas within the split sensitivity (re-run when given)',
                    'GNC re-fly: A1 reserve at 76 g per purge and the PURGE commitment at E0 - 2.90 s'])
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/rg01_line_states_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='coordinator 2026-10-13 after CHANGELOG 160-161: (1) purge on the decided path, Tp and N2O at 0 and 2 deg, lined and unlined, stuck-open flow; (2) RG-01 line-state tables for the GNC re-fly and the minimal case set',
               inputs={k: v for k, v in EXPECT.items()}, path=PATH, W_s=W, limit=LIM, PURGE_s_per_cm3=PURGE, DEAD_s_per_cm3=DEAD, t_lift_s=t_lift,
               timing=dict(scheduled_Tp_s=TP_SCHED, MV_open_ramp_s=0.35, flow_stopped_before_E0_s=0.05,
                           PURGE_command_before_E0_s=0.35 + TP_SCHED + 0.05,
                           note='Tp is the time both taps flow (measured from valve open to valve closed), not the command interval; the close command leads by the measured closing time (S12: 77 ms)'),
               part1_decided_path=part1, stuck_open=stuck, part2_line_states_for_gnc=dict(v=states, truncated_purge_worst_by_Tp=trunc,
                    tag='SIM on ASSUMED delays (start_latency_v2p4 pool, 200 000 samples, seed 2024) + DERIVED line states (retained_vapour_v341_v2p4 model, purge_duration_v2p4 grid); a light requires E1 -> E2 <= W 0.65 s; E0 -> E1 = U(5,20) + U(20,100) + U(5,30) ms ASSUMED (as post_abort_pocket_v2p4)'),
               part3_minimal_set=minimal,
               tags='DERIVED reduction of SIM/DERIVED results; no new physics; worst over the five GNC coast series, both element models, all slip brackets unless stated')
    json.dump(res, open(out_f, 'w'), indent=1, default=float)
    # ------------------------------------------------------------------ print
    print('stuck-open %.2f g/s (per tap liquid %.2f, vapour %.2f), %.1f %% of 100 %%; open-loop extra loss %.2f bar, injector %.2f %%' % (
        fl['liquid_g_s_all_taps'], fl['mdot_liquid_g_s_per_tap'], fl['mdot_vapour_g_s_per_tap'], 100 * fl['fraction_of_100pct_flow'], dp_extra / 1e5, -50.0 * dp_extra / dp_inj))
    for k, v in part1.items():
        if k.endswith('all_slips') or '0-2deg' not in k:
            g = v['governing_just_below_Tp_robust']
            print(k, 'Tp_r', v['Tp_robust_s'], 'N2O@Tpr', [round(x, 1) for x in v['N2O_g_at_Tp_robust']] if v['N2O_g_at_Tp_robust'] else None,
                  'N2O@2.5', [round(x, 1) for x in v['N2O_g_at_2p5s']], 'tcap@2.5', v['t_cap_out_max_s_at_2p5s'], 'notclr', v['n_records_cap_not_cleared_at_2p5s'],
                  'P1@2.5', [round(x, 2) for x in v['residual_P1_cm3_at_2p5s']],
                  'gov', (g['slip'], g['element'], g['heat_case'], g['reading'], g['tilt_deg'], g['az_deg'], g['P_abort']) if g else None,
                  'by conv', v['Tp_robust_s_by_convention'])
    for k, v in states.items():
        if 'P_abort_W0p65' in v:
            print(f"{k:48s} P {v['P_abort_W0p65']:.6f} E0E2 med {v['E0_E2_all_s']['median']:.3f} p99 {v['E0_E2_all_s']['p99']:.3f} max {v['E0_E2_all_s']['max']:.3f} seq {[round(x, 2) for x in v['sequence_P1_S1_C1_S2_C2_cm3']]}")
    for k, v in trunc.items():
        print(k, 'P %.5f' % v['P_abort_W0p65'], 'E0E2 p99 %.3f max %.3f' % (v['E0_E2_all_s']['p99'], v['E0_E2_all_s']['max']))
    print(json.dumps(minimal['combinations_0_2deg_worst_P_abort']))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])
