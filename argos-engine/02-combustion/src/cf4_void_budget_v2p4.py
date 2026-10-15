"""CF-4 pass/fail budget: how much vapour may sit behind the first liquid at the lift (Combustion v2.4, 2026-10-13).

The relight model (v2.4 200 000-sample E1 -> E2 distribution, seed 2024; pocket purge 0.015555 s/cm3, liquid dead time
0.023192 s/cm3; conventions 'paused' and 'restart') gives P(E1 -> E2 > W 0.65 s) for a vapour/liquid sequence at the seat.
CF-4 measures that sequence at the lift.  This script tabulates:
  - V_zero: the largest single pocket with P = 0 (18.86 cm3) and the pocket for P = 1e-3;
  - the largest second void C1 behind a first liquid slug S1, for a first pocket P1, with P_abort <= 1e-3 (worst convention);
  - the time-domain equivalents (what the CF-4 phase probe at the injector reads).
usage: python -I cf4_void_budget_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import hashlib, json, os, sys
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import start_latency_v2p4 as SL
import retained_vapour_v341_v2p4 as RV

LIM = 1e-3


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def main(d, out_f):
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    PA = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
    PURGE = VO['purge_s_per_cm3']; DEAD = VO['liquid_plug_dead_time_s_per_cm3']
    rws = J['part1_runs']['v']; lifts = J['ignition_lifts']
    pool = [r for r in rws if r['ramp'] == 2500.0 and r['F_cmd'] in (200.0, 500.0) and r['state'] == 'A1_relight'
            and r['frac'] == 0.125 and r.get('loop_K', 0.0) == 15.0]
    N = 200000; rng = np.random.default_rng(2024)
    h = lifts['A1_relight|0.125']['lift_m']; t_lift = SL.T_CMD + h / SL.V_PINTLE + 0.010
    idx = rng.integers(0, len(pool), N)
    tc = np.array([np.nan if q['t_conf_s'] is None else q['t_conf_s'] for q in pool])[idx]
    _ = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)
    ig = rng.uniform(0.05, 0.30, N)
    base = t_lift + ig + tc; base = base[np.isfinite(base)]
    assert abs(float(base.max()) - PA['E1_E2_liquid_s']['max']) < 1e-9
    bs = np.sort(base)
    Pab = lambda P1, S1, C1: max(RV.sorted_eval(bs, t_lift, PURGE, DEAD, P1, S1, C1, 0.0, 0.0, c) for c in ('paused', 'restart'))
    Vzero = (RV.W - float(base.max())) / PURGE
    # single pocket at P = 1e-3
    lo, hi = Vzero, 60.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if Pab(mid, 0.0, 0.0) <= LIM else (lo, mid)
    V1e3 = lo
    budget = {}
    for P1 in (0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5):
        for S1 in (2.5, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0):
            if Pab(P1, S1, 0.0) > LIM:
                budget[f'P1_{P1}|S1_{S1}'] = 0.0; continue
            lo, hi = 0.0, 80.0
            if Pab(P1, S1, hi) <= LIM:
                budget[f'P1_{P1}|S1_{S1}'] = None; continue          # no limit in range
            for _ in range(50):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if Pab(P1, S1, mid) <= LIM else (lo, mid)
            budget[f'P1_{P1}|S1_{S1}'] = lo
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/cf4_void_budget_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={n: sha16(os.path.join(d, n)) for n in ('relight_vapour_order_v2p4.json', 'start_latency_v2p4.json', 'post_abort_pocket_v2p4.json')},
               limit=LIM, W_s=RV.W, PURGE_s_per_cm3=PURGE, DEAD_s_per_cm3=DEAD, t_lift_s=t_lift, E1_E2_liquid_max_s=float(base.max()),
               V_zero_cm3=Vzero, V_single_P1e3_cm3=V1e3,
               time_equivalents_s=dict(first_liquid_after_lift_for_V_zero=Vzero * PURGE, first_liquid_after_lift_for_V_1e3=V1e3 * PURGE),
               C1_max_cm3_by_P1_S1=budget,
               note='C1 = the second void (after the first liquid slug S1), followed by continuous liquid; 0.0 = the first pocket alone already '
                    'exceeds the limit; None = no limit below 80 cm3. Worst of the paused and restart conventions.',
               tags='SIM (ignition delays ASSUMED as in v2.4) / DERIVED')
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print('V_zero %.3f cm3 (%.4f s), V(P=1e-3) %.3f cm3 (%.4f s)' % (Vzero, Vzero * PURGE, V1e3, V1e3 * PURGE))
    S1s = (2.5, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0)
    print('C1 max (cm3) rows P1, columns S1', S1s)
    for P1 in (0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5):
        print('P1 %5.1f |' % P1, ' '.join(('  none' if budget[f'P1_{P1}|S1_{S1}'] is None else '%6.2f' % budget[f'P1_{P1}|S1_{S1}']) for S1 in S1s))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])
