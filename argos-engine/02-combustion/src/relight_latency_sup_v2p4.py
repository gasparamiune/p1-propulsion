"""Relight latency, supplementary cases (Combustion v2.4, RC-03; 2026-10-13).

Re-uses the Part 1 grain_q1d start runs stored in start_latency_v2p4.json (no new engine runs) and the same ASSUMED
sequence distributions as start_latency_v2p4.part2, and adds the cases needed for the lead's relight decision:
  * valve PRE-OPENED by flight software before the RELIGHT command (pintle seated): no valve flow-onset delay; the hot
    manifold vapour remains (purge U(0,1) x 0.31 s, or the full 0.31 s);
  * the Pc loop (K 15, as start_latency_v2p4) on every relight case;
  * 'valve command to Pc confirmation' = E1 -> E2 when the valve is commanded at torch confirmation (v2.4 sequence),
    E0 -> E2 + T_pre when it is pre-opened (reported as E1 -> E2 with the pre-open lead time stated separately);
  * p99.9 and the maximum of the 200 000 samples for the lead's planning value (0.6 s + worst case).
Distributions are ASSUMED (no ignition data); IGN-1/T1/T4 replace them.
usage: python -I relight_latency_sup_v2p4.py DATA_V2P4_DIR
"""
from __future__ import annotations
import json, os, sys
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import start_latency_v2p4 as SL

T_PURGE = 0.31          # s, full-vapour segment purge through the 12.5 % lift, valve at the coil end (low_inlet_check_v2p3 C7)
T_PURGE_MANIFOLD = T_PURGE * 4.51 / 21.42   # s, manifold-only vapour (4.51 of 21.42 cm3, safing_relief_v2p4 trapped volumes), purge ~ volume
W_ADOPTED = {'liquid': 0.40, 'vapour': 0.65}   # s from the ignition-lift command (LEAD 2026-10-13, first decision: base 0.40 s + extension
                                               # 0.25 s when vapour is indicated). Final LEAD rules (2026-10-13): stand R1 0.40 s first start,
                                               # R2 0.50 s every relight, R3 0.65 s whole-line vapour proven by two-end superheat; flight
                                               # 0.65 s every relight. Statistics for each W are in by_deadline_from_lift_command.


def quant(x):
    x = np.asarray(x); x = x[np.isfinite(x)]
    return [round(float(np.percentile(x, q)), 4) for q in range(0, 101, 5)] if x.size else []


def stats(x):
    x = np.asarray(x); x = x[np.isfinite(x)]
    if x.size == 0:
        return dict(median=None, p95=None, p99=None, p999=None, max=None, n=0)
    return dict(median=float(np.percentile(x, 50)), p95=float(np.percentile(x, 95)), p99=float(np.percentile(x, 99)),
                p999=float(np.percentile(x, 99.9)), max=float(x.max()))


def main(d, seg_cm3=None):
    """seg_cm3 None: the published run (21.42 cm3 segment, 0.31 s purge). seg_cm3 given (e.g. 32.6, Mechanical CHANGELOG 2026-10-13):
    whole-segment purge scaled with volume (0.31 s x V / 21.42 cm3, DERIVED), manifold purge unchanged (4.51 cm3), plus a hot-end
    vapour pocket of 8 cm3 (purge 0.116 s) and the output goes to relight_latency_sup_seg<V>_v2p4.json."""
    global T_PURGE
    T_PURGE = 0.31 if seg_cm3 is None else 0.31 * seg_cm3 / 21.42
    T_PURGE_HOT = 0.31 * 8.0 / 21.42
    src = os.path.join(d, 'start_latency_v2p4.json')
    J = json.load(open(src))
    rows = J['part1_runs']['v']; lifts = J['ignition_lifts']
    by = {}
    for r in rows:
        if r['ramp'] == 2500.0 and r['F_cmd'] in (200.0, 500.0):
            by.setdefault((r['state'], r['frac'], r.get('loop_K', 0.0)), []).append(r)
    # mode: (valve commanded at E1?, vapour law)
    cases = {
        'relight_valve_open_coast': (False, 'none'), 'relight_valve_closed_liquid_segment': (True, 'none'),
        'relight_valve_closed_vapour_U01': (True, 'U01'), 'relight_valve_closed_full_vapour': (True, 'full'),
        'relight_valve_preopened_liquid': (False, 'none'), 'relight_valve_preopened_vapour_U01': (False, 'U01'),
        'relight_valve_preopened_full_vapour': (False, 'full'),
        'relight_manifold_vapour_unseen_U01': (True, 'manifold'), 'relight_manifold_vapour_unseen_full': (True, 'manifold_full'),
        'pad_start_primed': (False, 'none')}
    if seg_cm3 is not None:
        cases.update({'relight_hot_end_vapour_8cm3_U01': (True, 'hot'), 'relight_hot_end_vapour_8cm3_full': (True, 'hot_full')})
    out = {}; N = 200000
    for loopK in (0.0, 15.0):
        for cname, (vstep, vap) in cases.items():
            st = 'pad_20C' if cname.startswith('pad') else 'A1_relight'
            pool = by.get((st, 0.125, loopK), [])
            if not pool:
                continue
            rng = np.random.default_rng(2024)
            h = lifts[f'{st}|0.125']['lift_m']
            t_lift = SL.T_CMD + h / SL.V_PINTLE + 0.010
            idx = rng.integers(0, len(pool), N)
            tc = np.array([np.nan if p['t_conf_s'] is None else p['t_conf_s'] for p in pool])[idx]
            t9 = np.array([np.nan if p['t90_s'] is None else p['t90_s'] for p in pool])[idx]
            e1 = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)
            arr = np.zeros(N)
            if vstep:
                arr += rng.uniform(0.05, 0.15, N) if vap in ('U01', 'full') else 0.0   # (hot-end pocket: liquid upstream, no valve onset)   # liquid upstream of the manifold: no valve onset
            if vap == 'U01':
                arr += rng.uniform(0.0, 1.0, N) * T_PURGE
            elif vap == 'full':
                arr += T_PURGE
            elif vap == 'manifold':
                arr += rng.uniform(0.0, 1.0, N) * T_PURGE_MANIFOLD
            elif vap == 'manifold_full':
                arr += T_PURGE_MANIFOLD
            elif vap == 'hot':
                arr += rng.uniform(0.0, 1.0, N) * T_PURGE_HOT
            elif vap == 'hot_full':
                arr += T_PURGE_HOT
            ig = rng.uniform(0.05, 0.30, N)
            e12 = t_lift + arr + ig + tc
            E2 = e1 + e12; E3 = e1 + t_lift + arr + ig + t9
            fa = {f'{W:.2f}': float(np.mean(e12[np.isfinite(e12)] > W)) for W in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.10)}
            key = f'{cname}|0.125|loopK{loopK:g}'
            E13 = E3 - e1       # valve command (E1, v2.4 sequence) to 90 % thrust
            out[key] = dict(state=st, valve_commanded_at_E1=vstep, vapour=vap, Pc_loop_K=loopK,
                            E0_E1_s=stats(e1), E1_E2_s=stats(e12), E0_E2_s=stats(E2), E0_E3_s=stats(E3), E1_E3_s=stats(E13),
                            P_E1E3_le_0p5s=float(np.mean(E13[np.isfinite(E13)] <= 0.5)),
                            E1_E3_quantiles_5pct_s=[round(float(np.percentile(E13[np.isfinite(E13)], q)), 4) for q in range(0, 101, 5)],
                            P_E0E3_le_0p5s=float(np.mean(E3[np.isfinite(E3)] <= 0.5)), P_E0E3_le_0p6s=float(np.mean(E3[np.isfinite(E3)] <= 0.6)),
                            false_abort_vs_W_from_E1=fa, E0_E3_quantiles_5pct_s=[round(float(np.percentile(E3[np.isfinite(E3)], q)), 4) for q in range(0, 101, 5)])
            # adopted timing (v2.4, LEAD 2026-10-13): deadline from the ignition-lift command; the extension applies when the sensor
            # indicates vapour (U01 / full vapour cases); manifold-only vapour is the case the inlet-block sensor may not see
            Wa = W_ADOPTED['vapour'] if vap in ('U01', 'full', 'hot', 'hot_full') else W_ADOPTED['liquid']
            fin = np.isfinite(e12) & np.isfinite(E13) & np.isfinite(E3)
            byW = {}
            for Wx in (0.40, 0.45, 0.50, 0.65, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.10):
                okx = fin & (e12 <= Wx)
                byW[f'{Wx:.2f}'] = dict(P_abort_of_a_relight_that_would_light=float(1.0 - np.mean(okx[fin])),
                                        E1_E3_given_success_s=stats(E13[okx]), E0_E3_given_success_s=stats(E3[okx]),
                                        P_E1E3_le_0p5s_given_success=float(np.mean(E13[okx] <= 0.5)) if okx.any() else None)
            out[key]['by_deadline_from_lift_command'] = byW
            ok = fin & (e12 <= Wa)
            out[key]['adopted_timing'] = dict(
                W_from_lift_command_s=Wa, P_abort_of_a_relight_that_would_light=float(1.0 - np.mean(ok[fin])),
                E1_E3_given_success_s=stats(E13[ok]), E0_E3_given_success_s=stats(E3[ok]),
                P_E1E3_le_0p5s_given_success=float(np.mean(E13[ok] <= 0.5)) if ok.any() else None, P_lit_and_E1E3_le_0p5s=float(np.mean(ok[fin] & (E13[fin] <= 0.5))),
                E1_E3_given_success_quantiles_5pct_s=quant(E13[ok]))
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/relight_latency_sup_v2p4.py', source=os.path.basename(src),
               note='12.5 % ignition lift; 200 000 samples, seed 2024; distributions as start_latency_v2p4 (ASSUMED); pre-opened = flight '
                    'software opens the NC valve with the pintle seated at least 0.3 s before RELIGHT (no valve onset in the relight path); '
                    'vapour U01 = segment vapour fraction U(0,1) x 0.31 s purge; full = 0.31 s; E1_E3 = valve command at torch confirmation (E1) '
                    'to 90 % thrust (pre-opened cases: the valve command precedes E0 by >= 0.3 s, so E1_E3 there is torch confirmation to '
                    '90 % and the time from the valve command is E0_E3 + the pre-open lead); adopted_timing = v2.4 deadline from the '
                    'ignition-lift command, 0.40 s, or 0.65 s when vapour is indicated (LEAD 2026-10-13); manifold_vapour_unseen = vapour '
                    'only in the 4.51 cm3 injector manifold (purge 0.065 s) that a sensor in the inlet block may not indicate', cases=out)
    if seg_cm3 is not None:
        res['segment_cm3'] = seg_cm3; res['t_purge_segment_s'] = T_PURGE; res['t_purge_hot_end_8cm3_s'] = T_PURGE_HOT
        res['note'] += f'; SEGMENT {seg_cm3} cm3: whole-segment purge {T_PURGE:.3f} s (scaled with volume, DERIVED), hot-end pocket 8 cm3 {T_PURGE_HOT:.3f} s'
    fn = os.path.join(d, 'relight_latency_sup_v2p4.json' if seg_cm3 is None else f'relight_latency_sup_seg{seg_cm3:g}_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1)
    for k, v in out.items():
        print(f"{k:58s} E1E2 med {v['E1_E2_s']['median']:.3f} p99 {v['E1_E2_s']['p99']:.3f} p999 {v['E1_E2_s']['p999']:.3f} max {v['E1_E2_s']['max']:.3f} | "
              f"E0E3 med {v['E0_E3_s']['median']:.3f} p95 {v['E0_E3_s']['p95']:.3f} p99 {v['E0_E3_s']['p99']:.3f} | P<=0.5 {v['P_E0E3_le_0p5s']:.3f} | "
              f"E1E3 med {v['E1_E3_s']['median']:.3f} p95 {v['E1_E3_s']['p95']:.3f} p99 {v['E1_E3_s']['p99']:.3f} P<=0.5 {v['P_E1E3_le_0p5s']:.3f} | FA@0.40 {v['false_abort_vs_W_from_E1']['0.40']:.4f} FA@0.80 {v['false_abort_vs_W_from_E1']['0.80']:.5f}")
    fm = lambda x, n=3: 'n/a' if x is None else f'{x:.{n}f}'
    for k, v in out.items():
        a = v['adopted_timing']; g = a['E1_E3_given_success_s']; g0 = a['E0_E3_given_success_s']
        print(f"ADOPTED {k:58s} W {a['W_from_lift_command_s']:.2f} P_abort {a['P_abort_of_a_relight_that_would_light']:.4f} | E1E3|ok med "
              f"{fm(g['median'])} p95 {fm(g['p95'])} p99 {fm(g['p99'])} max {fm(g['max'])} P<=0.5|ok {fm(a['P_E1E3_le_0p5s_given_success'])} | "
              f"E0E3|ok p99 {fm(g0['p99'])} max {fm(g0['max'])}")
        print('   P_abort by W', {W: round(b['P_abort_of_a_relight_that_would_light'], 4) for W, b in v['by_deadline_from_lift_command'].items()})
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else None)
