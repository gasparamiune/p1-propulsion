"""Relight line states from the flow-order vapour analysis: abort probability, latency given a light, and option (a) with
the E0 -> lift time included (Combustion v2.4 supplement to relight_vapour_order_v2p4; 2026-10-13).

Why: relight_vapour_order_v2p4 gives the pocket ahead of the first sustained liquid at RELIGHT (LO / HI heat, GNC windows).
GNC needs, for the P cost of planning every relight as a vapour start (W 1.05 s), the E0 -> E2 and E0 -> E3 distributions
given a light; the stand rule R2 = 0.35 s needs the abort probability of a primed and of a vapour relight; and the option (a)
residual in relight_vapour_order_v2p4 counted the U boiling only up to E0, not up to the lift at E1.

Model: identical to post_abort_pocket_v2p4 (same Part 1 pool A1_relight 12.5 % K15, seed 2024, 200 000 samples, same random
stream order idx -> E0->E1 -> ignition delay), plus t90 of the same pool rows for E3 (as relight_latency_sup_v2p4).
  E1 -> E2 = t_lift + ignition delay + t_conf + purge x V_eff;  E0 -> E2 = E0 -> E1 + E1 -> E2;  E3 likewise with t90.
  A relight lights only if E1 -> E2 <= W (W counted from the lift command at E1); otherwise it aborts.
Option (a) residual (bleed at the crest with the MV opened early; pintle seated): bore-leg term + U boil rate x (gap + E0->E1),
  bore-leg term = 4.51 cm3 of vapour, or a liquid-full bore leg counted as dead time (4.51 x 0.02319 / 0.01556 = 6.72 cm3
  equivalent; bounding), whichever is larger; gap = time from bleed closure to E0.
Descent-only bound (REV-GNC-1 RG-20 time history, added 2026-10-13): the most favourable reading in which every bubble
  formed before the drogue load leaves the U (it cannot: coast_migration_v2p4 moves it <= 53 mm) keeps only the vapour formed
  in the U between the drogue load and the relight command of each GNC series: V = Q_U x [E(T_w) - E(T_w - t_d)] / E(T_mech)
  x v_fg, E(T) = integral of Mechanical's coast heat series (same extrapolation as relight_vapour_order_v2p4), T_w = the
  series' MECO -> relight window, t_d = drogue load -> relight command (coast_migration_v2p4), capped at the U volume.
usage: python -I relight_vapour_states_v2p4.py DATA_V2P4_DIR OUT_JSON [COAST_MIGRATION_JSON]
"""
from __future__ import annotations
import json, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import start_latency_v2p4 as SL

WS = (0.35, 0.65, 0.85, 1.05)


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def st(x):
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return None
    return dict(median=float(np.median(x)), p95=float(np.percentile(x, 95)), p99=float(np.percentile(x, 99)), max=float(x.max()))


def main(d, out_f, mig_f=None):
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    PA = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    rws = J['part1_runs']['v']; lifts = J['ignition_lifts']
    pool = [r for r in rws if r['ramp'] == 2500.0 and r['F_cmd'] in (200.0, 500.0) and r['state'] == 'A1_relight'
            and r['frac'] == 0.125 and r.get('loop_K', 0.0) == 15.0]
    N = 200000; rng = np.random.default_rng(2024)
    h = lifts['A1_relight|0.125']['lift_m']; t_lift = SL.T_CMD + h / SL.V_PINTLE + 0.010
    idx = rng.integers(0, len(pool), N)
    tc = np.array([np.nan if q['t_conf_s'] is None else q['t_conf_s'] for q in pool])[idx]
    t9 = np.array([np.nan if q['t90_s'] is None else q['t90_s'] for q in pool])[idx]
    e1 = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)
    ig = rng.uniform(0.05, 0.30, N)
    base = t_lift + ig + tc; b3 = t_lift + ig + t9
    fin = np.isfinite(base) & np.isfinite(b3)
    base, b3, e1 = base[fin], b3[fin], e1[fin]
    check = dict(base_max_s=float(base.max()), post_abort_pocket_max_s=PA['E1_E2_liquid_s']['max'],
                 reproduces=bool(abs(float(base.max()) - PA['E1_E2_liquid_s']['max']) < 1e-9))
    PURGE = VO['purge_s_per_cm3']; DEAD = VO['liquid_plug_dead_time_s_per_cm3']
    V_bore = VO['geometry']['bore_leg_cm3']

    def state(Veff):
        Veff = np.broadcast_to(np.asarray(Veff, dtype=float), base.shape)
        e12 = base + PURGE * Veff; E02 = e1 + e12; E03 = e1 + b3 + PURGE * Veff
        o = {}
        for W in WS:
            ok = e12 <= W
            o[f'W{W:.2f}'] = dict(P_abort=float(1.0 - ok.mean()),
                                  E0_E2_given_light_s=st(E02[ok]) if ok.any() else None,
                                  E0_E3_given_light_s=st(E03[ok]) if ok.any() else None,
                                  P_E0E3_le_0p5_given_light=float(np.mean(E03[ok] <= 0.5)) if ok.any() else None)
        okW = e12 <= 1.05
        o['W1.05']['E0_E2_given_light_quantiles_5pct_s'] = [round(float(np.percentile(E02[okW], q)), 4) for q in range(0, 101, 5)] if okW.any() else []
        o['W1.05']['E0_E3_given_light_quantiles_5pct_s'] = [round(float(np.percentile(E03[okW], q)), 4) for q in range(0, 101, 5)] if okW.any() else []
        return o

    states = {'liquid (primed, no pocket)': 0.0, 'requirement 19 cm3': 19.0, 'U full of vapour, bore leg dry (27.87 cm3)': 27.87}
    for k, v in VO['results'].items():
        for lab in ('bore_leg_refilled', 'bore_leg_dry'):
            states[f'{k} {lab} (V_eff {v[lab]["V_eff_cm3"]:.2f} cm3)'] = v[lab]['V_eff_cm3']
    desc = {}
    if mig_f:
        MC = json.load(open(VO['inputs']['mech_coast']['file']))
        assert sha16(VO['inputs']['mech_coast']['file']) == VO['inputs']['mech_coast']['sha256_16'], 'Mechanical coast heat file changed'
        MG = json.load(open(mig_f)); V_U = VO['geometry']['U_volume_cm3']; vpj = VO['properties']['vap_cm3_per_J']
        trap = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')
        T_m = VO['window_s']['mech']
        for c, lab in (('LO', 'DC-A1dispp99_tg711_hi_SS316L_L2.5_v11pre36IN'), ('HI', 'DC-A1dispp99_tg711_hi_SS316L_L2.5_v11pre36ING10')):
            s = MC['runs'][lab]['series']; tt0 = np.array(s['t_s']) - s['t_s'][0]; q = np.array(s['Q_W']); kf = np.polyfit(tt0[-5:], q[-5:], 1)
            def E_to(T, t=tt0, q=q, kf=kf):
                if T <= 0:
                    return 0.0
                if T <= t[-1]:
                    x = np.linspace(0, T, 400); return float(trap(np.interp(x, t, q), x))
                x = np.linspace(t[-1], T, 200)
                return float(trap(q, t) + trap(np.polyval(kf, x), x))
            for sname, sv in list(MG['series'].items()):
                Tw = sv['window_s']; td = sv['t_from_drogue_load_s']
                Vd = VO['heat_J'][c]['U'] * (E_to(Tw) - E_to(Tw - td)) / E_to(T_m) * vpj
                desc[f'{c}|{sname}'] = dict(window_s=Tw, t_drogue_to_relight_s=td, V_descent_only_cm3=Vd, V_eff_cm3=min(Vd, V_U),
                                            U_full=bool(Vd >= V_U))
                states[f'descent-only {c} {sname} (V_eff {min(Vd, V_U):.2f} cm3)'] = min(Vd, V_U)
    S = {k: dict(V_eff_cm3=v, **state(v)) for k, v in states.items()}
    # option (a) with the E0 -> E1 time included
    bore_term = max(V_bore, V_bore * DEAD / PURGE)
    oa = {}
    for c in ('LO', 'HI'):
        rate = VO['option_a'][f'{c}|bleed_end_0.5s_before_E0']['U_boil_rate_cm3_s']
        for gap in (0.0, 0.5, 1.0):
            V = bore_term + rate * (gap + e1)
            r = state(V)
            oa[f'{c}|bleed_closed_{gap:.1f}s_before_E0'] = dict(U_boil_rate_cm3_s=rate, bore_leg_term_cm3=bore_term,
                                                               residual_cm3=dict(median=float(np.median(V)), max=float(V.max())),
                                                               P_abort={w: r[w]['P_abort'] for w in r},
                                                               E0_E2_given_light_W0p65_s=r['W0.65']['E0_E2_given_light_s'])
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/relight_vapour_states_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={k: dict(file=f'v2p4/{k}', sha256_16=sha16(os.path.join(d, k))) for k in
                       ('start_latency_v2p4.json', 'post_abort_pocket_v2p4.json', 'relight_vapour_order_v2p4.json')},
               distribution_check=check, purge_s_per_cm3=PURGE, plug_dead_time_s_per_cm3=DEAD, states=S, option_a_with_E0_E1=oa,
               descent_only_bound=desc,
               tag='SIM on ASSUMED delays (post_abort_pocket_v2p4 model) + DERIVED pockets (relight_vapour_order_v2p4)')
    if mig_f:
        out['inputs']['coast_migration_v2p4.json'] = dict(file='v2p4/coast_migration_v2p4.json', sha256_16=sha16(mig_f))
    json.dump(out, open(out_f, 'w'), indent=1)
    print('check', check)
    for k, v in S.items():
        print(f'{k:62s} ' + ' '.join(f'{w}:{v[w]["P_abort"]:.4f}' for w in ('W0.35', 'W0.65', 'W0.85', 'W1.05'))
              + (' | W1.05 E0E2 med/p99/max ' + '/'.join(f'{v["W1.05"]["E0_E2_given_light_s"][q]:.3f}' for q in ('median', 'p99', 'max'))
                 + ' E0E3 med/p95/p99/max ' + '/'.join(f'{v["W1.05"]["E0_E3_given_light_s"][q]:.3f}' for q in ('median', 'p95', 'p99', 'max'))
                 if v['W1.05']['E0_E2_given_light_s'] else ''))
    for k, v in oa.items():
        print(f'option a {k:34s} residual med {v["residual_cm3"]["median"]:.2f} max {v["residual_cm3"]["max"]:.2f} cm3 P_abort '
              + ' '.join(f'{w}:{p:.4f}' for w, p in v['P_abort'].items()))
    for k, v in desc.items():
        print(f'descent-only {k:12s} window {v["window_s"]:.2f} s, drogue->relight {v["t_drogue_to_relight_s"]:.2f} s, V {v["V_descent_only_cm3"]:.2f} cm3')
    print('wrote', out_f)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
