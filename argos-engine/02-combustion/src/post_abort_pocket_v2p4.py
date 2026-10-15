"""Relight abort probability against a retained vapour pocket (Combustion v2.4, 2026-10-13).

Two questions from the v2.4 close-out:
  (1) the flight requirement "retained vapour <= 19 cm3 at RELIGHT" (LEAD 2026-10-13): show the probability that a relight that
      would light is aborted by W = 0.65 s (from the ignition-lift command) against the pocket volume, and the largest pocket
      with no abort in the 200 000 samples;
  (2) the state after an abort of a burn (MV-P closes first in 30 ms; segment_drain_v2p4): the pocket left in the 44 cm3
      segment, with and without compression to tank pressure before the lift (MV open at E0, or the unprimed-path prepress).

Model: identical to relight_latency_sup_v2p4 (same Part 1 grain_q1d pool A1_relight, 12.5 % flow, Pc loop K 15; same ASSUMED
delay distributions, seed 2024, 200 000 samples). The valve is open before the lift (v2.8: MV at E0), so no valve-onset term.
The pocket purge time is 0.31 s per 21.42 cm3 at the 12.5 % lift of the A1 state (0.2192 mm; SIM C7, scaled with volume,
DERIVED) and x 0.2192/0.2039 at the v2.8 default lift 0.2039 mm (DERIVED, purge ~ 1/flow area).
Compression: isothermal ideal-gas ratio P_seg/P_tank (ASSUMED: no condensation credit, no evaporation), P_tank = Psat(T_tank).
usage: python -I post_abort_pocket_v2p4.py DATA_V2P4_DIR
"""
from __future__ import annotations
import json, os, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import start_latency_v2p4 as SL

PURGE_PER_CM3 = {'lift_0.2192mm_12.5pct': 0.31 / 21.42, 'lift_0.2039mm_v2p8': 0.31 / 21.42 * 0.2191572 / 0.2039}
POCKETS = (0.0, 4.0, 8.0, 12.0, 16.0, 18.0, 19.0, 20.0, 22.0, 24.0, 30.0, 44.0)
WS = (0.50, 0.65, 0.85, 1.00)


def main(d):
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    rows = J['part1_runs']['v']; lifts = J['ignition_lifts']
    pool = [r for r in rows if r['ramp'] == 2500.0 and r['F_cmd'] in (200.0, 500.0) and r['state'] == 'A1_relight'
            and r['frac'] == 0.125 and r.get('loop_K', 0.0) == 15.0]
    assert pool, 'no A1_relight K15 pool'
    N = 200000
    rng = np.random.default_rng(2024)
    h = lifts['A1_relight|0.125']['lift_m']
    t_lift = SL.T_CMD + h / SL.V_PINTLE + 0.010
    idx = rng.integers(0, len(pool), N)
    tc = np.array([np.nan if p['t_conf_s'] is None else p['t_conf_s'] for p in pool])[idx]
    _e1 = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)  # kept for stream parity
    ig = rng.uniform(0.05, 0.30, N)
    base = t_lift + ig + tc                       # E1 -> E2 with a liquid line (no pocket)
    fin = np.isfinite(base)
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/post_abort_pocket_v2p4.py',
               basis='relight_latency_sup_v2p4 pool A1_relight 12.5 % K15; ASSUMED delays; 200 000 samples seed 2024; MV open before the lift',
               E1_E2_liquid_s=dict(median=float(np.median(base[fin])), p99=float(np.percentile(base[fin], 99)), max=float(base[fin].max())),
               by_lift={})
    for lab, ppc in PURGE_PER_CM3.items():
        tab = {}
        for V in POCKETS:
            e12 = base[fin] + ppc * V
            tab[f'{V:g}cm3'] = {f'W{W:.2f}': float(np.mean(e12 > W)) for W in WS}
            tab[f'{V:g}cm3']['E1_E2_max_s'] = float(e12.max())
        v_allow = (0.65 - float(base[fin].max())) / ppc
        out['by_lift'][lab] = dict(purge_s_per_cm3=ppc, P_abort_vs_pocket=tab, pocket_with_no_abort_at_W0p65_cm3=v_allow)
        print(lab, 'pocket with no abort at W 0.65 s: %.1f cm3' % v_allow)
        for V in POCKETS:
            r = tab[f'{V:g}cm3']
            print(f'   {V:5.1f} cm3: P_abort W0.50 {r["W0.50"]:.4f} W0.65 {r["W0.65"]:.4f} W0.85 {r["W0.85"]:.4f}  E1E2max {r["E1_E2_max_s"]:.3f} s')
    # post-abort pockets from segment_drain_v2p4 (44 cm3 and 32.6 cm3), with and without compression to P_tank
    sd = json.load(open(os.path.join(d, 'segment_drain_v2p4.json')))
    ppc = PURGE_PER_CM3['lift_0.2039mm_v2p8']
    pa = {}
    for key, c in sd['cases'].items():
        if not key.split('|')[-1].startswith('MV_first'):
            continue
        T = c['T_tank_C'] + 273.15
        Pt = CP.PropsSI('P', 'T', T, 'Q', 0, 'NitrousOxide')
        V = c['segment_end']['vapour_volume_cm3']; Ps = c['segment_end']['P_bar'] * 1e5
        Vc = V * min(Ps / Pt, 1.0)
        row = dict(T_tank_C=c['T_tank_C'], P_tank_bar=Pt / 1e5, P_seg_bar=Ps / 1e5, pocket_cm3=V, pocket_compressed_cm3=Vc)
        for lab2, VV in (('uncompressed', V), ('compressed', Vc)):
            e12 = base[fin] + ppc * VV
            row[f'P_abort_W0.65_{lab2}'] = float(np.mean(e12 > 0.65))
        pa[key] = row
        print(f'{key:42s} P_seg {Ps/1e5:5.1f} / P_tank {Pt/1e5:5.1f} bar: pocket {V:5.1f} -> {Vc:5.1f} cm3; P_abort(W 0.65) '
              f'{row["P_abort_W0.65_uncompressed"]:.3f} / {row["P_abort_W0.65_compressed"]:.3f}')
    out['post_abort_pockets'] = dict(v=pa, tag='segment_drain_v2p4 (SIM, Cd 0.70 ASSUMED) + isothermal compression (ASSUMED, no condensation credit); lift 0.2039 mm')
    # line states for GNC's Monte Carlo at the 44 cm3 segment under the 19 cm3 requirement (start delay E0 -> E2; lights only if
    # E1 -> E2 <= W 0.65 s, otherwise an abort, which in flight is a loss): pocket U(0, 19) cm3, 19 cm3, and the post-abort pockets
    e1 = _e1[fin]
    states = {'pocket_U0_19cm3': rng.uniform(0.0, 19.0, int(fin.sum())), 'pocket_19cm3': np.full(int(fin.sum()), 19.0),
              'post_abort_compressed_20.1cm3': np.full(int(fin.sum()), 20.1), 'post_abort_uncompressed_24.3cm3': np.full(int(fin.sum()), 24.3)}
    ls = {}
    for lab, V in states.items():
        e12 = base[fin] + ppc * V
        ok = e12 <= 0.65
        E02 = e1 + e12
        ls[lab] = dict(P_abort_W0p65=float(1.0 - ok.mean()),
                       E0_E2_all_s=dict(median=float(np.median(E02)), p99=float(np.percentile(E02, 99)), max=float(E02.max())),
                       E0_E2_given_light_quantiles_5pct_s=[round(float(np.percentile(E02[ok], q)), 4) for q in range(0, 101, 5)] if ok.any() else [])
        print(f'{lab:34s} P_abort {ls[lab]["P_abort_W0p65"]:.4f}; E0->E2 median {np.median(E02):.3f} max {E02.max():.3f} s')
    out['line_states_for_gnc_44cm3'] = dict(v=ls, tag='SIM on ASSUMED delays; lift 0.2039 mm; MV open before the lift (v2.8); a light requires E1->E2 <= 0.65 s')
    fn = os.path.join(d, 'post_abort_pocket_v2p4.json')
    json.dump(out, open(fn, 'w'), indent=1)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
