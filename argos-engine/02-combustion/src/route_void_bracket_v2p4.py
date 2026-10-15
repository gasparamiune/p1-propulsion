"""Route-void bracket for the RELIGHT pocket (Combustion v2.4 check of relight_vapour_order_v2p4, 2026-10-13).

Why: relight_vapour_order_v2p4 (and vapour_options_v2p4, which reproduces it) add the quasi-steady drift-flux void of the
overflow, alpha_ss x (wall line + module, 16.13 cm3), to the pocket of every case whose U overflows, and nothing when the U
does not overflow. Two inconsistencies follow:
  1. the void cannot hold more vapour than has entered the route within one bubble residence time. With a small overflow
     (U just full), alpha_ss x 16.13 cm3 (5.8 cm3 in LO) exceeds the overflow itself (0.34 cm3 in LO at 18.67 s);
  2. without overflow the route's own boiling (module, wall line, U-bottom fittings) still leaves a bubbly void, which is
     omitted.
Transit-consistent value (Little's law per source, same drift-flux closure and the same end-of-window rates):
  no overflow:  V_rv = alpha(r_R) x V_route
  overflow:     t_res = alpha(r_U + r_R) x V_route / (r_U + r_R);  V_rv = r_R t_res + min(overflow, r_U t_res)
  alpha(r) = j/(1.2 j + U_d), j = r / A_wall, U_d = Taylor drift in the 7.75 mm wall line at the p01 descent force (as VO).
  V_eff = U vapour + bore-leg plug as dead time (unchanged) + V_rv.
The quasi-steady value of VO stays the upper bound; this is the best estimate. Liquid left in a partly filled U (LO 17.77 s,
<= 1.4 cm3 at the U-bottom) is neither counted as vapour nor as dead time (as in VO).
P_abort: the same 200 000-sample E1 -> E2 distribution (seed 2024), reproduced and asserted.
usage: python -I route_void_bracket_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import json, math, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import start_latency_v2p4 as SL
import relight_vapour_order_v2p4 as RV

WS = (0.65, 0.76, 0.85, 0.93, 1.05)


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def st(x):
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return None
    return dict(median=float(np.median(x)), p95=float(np.percentile(x, 95)), p99=float(np.percentile(x, 99)), max=float(x.max()))


def main(d, out_f):
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    OP = json.load(open(os.path.join(d, 'vapour_options_v2p4.json')))
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    PA = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
    p = VO['properties']; geo = VO['geometry']
    V_route = geo['wall_line_cm3'] + geo['module_cm3']
    ID_wall = 9.525 - 2 * 0.889; A_wall = math.pi / 4 * ID_wall ** 2 * 1e-6
    gd = VO['mobility']['g_desc_m_s2']['p01']
    Ud = RV.drift(ID_wall / 1e3, gd, p)[0]
    alpha = lambda r_cm3_s: (lambda j: j / (1.2 * j + Ud) if j > 0 else 0.0)(r_cm3_s * 1e-6 / A_wall)
    # distribution (as relight_vapour_states_v2p4)
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
    fin = np.isfinite(base) & np.isfinite(b3); base, b3, e1 = base[fin], b3[fin], e1[fin]
    assert abs(float(base.max()) - PA['E1_E2_liquid_s']['max']) < 1e-9, 'distribution not reproduced'
    PURGE = VO['purge_s_per_cm3']
    # check: the VO quasi-steady void is reproduced from the end rates of vapour_options
    chk = []
    res = {}
    for case, hc in OP['heat_cases'].items():
        rU, rR = hc['U_boil_rate_end_cm3_s'], hc['route_boil_rate_end_cm3_s']
        a_ss, a_R = alpha(rU + rR), alpha(rR)
        t_res = a_ss * V_route / (rU + rR)
        for w, x in hc['windows'].items():
            for lab in ('bore_leg_refilled', 'bore_leg_dry'):
                y = x[lab]
                if y['overflow_cm3'] > 0:
                    chk.append(abs(y['wall_void'] - a_ss))
                V_base = y['V_eff_cm3'] - y['wall_void'] * V_route
                if y['overflow_cm3'] > 0:
                    V_rv = rR * t_res + min(y['overflow_cm3'], rU * t_res)
                else:
                    V_rv = a_R * V_route
                V_c = V_base + V_rv
                e12 = base + PURGE * V_c
                r = dict(window_s=x['window_s'], plug_cm3=y['plug_cm3'], overflow_cm3=y['overflow_cm3'],
                         V_eff_quasi_steady_cm3=y['V_eff_cm3'], route_void_quasi_steady_cm3=y['wall_void'] * V_route,
                         route_void_transit_cm3=V_rv, V_eff_transit_cm3=V_c, t_res_s=t_res, alpha_ss=a_ss, alpha_route_only=a_R,
                         W_for_P_abort_0_s=float(base.max() + PURGE * V_c),
                         P_abort={f'W{W:.2f}': float(np.mean(e12 > W)) for W in WS},
                         P_abort_quasi_steady={f'W{W:.2f}': float(np.mean(base + PURGE * y['V_eff_cm3'] > W)) for W in WS})
                ok = e12 <= 1.05
                r['W1.05_E0_E2_given_light_s'] = st((e1 + e12)[ok]); r['W1.05_E0_E3_given_light_s'] = st((e1 + b3 + PURGE * V_c)[ok])
                res[f'{case}|{w}|{lab}'] = r
    assert max(chk) < 1e-9, 'VO quasi-steady void not reproduced'
    # fixed line states for the report's latency table (same distribution; W from the lift command)
    fixed = {}
    for V in (0.0, 4.51, 6.9, 9.6, 19.0, 27.87, 35.09, 44.0):   # 4.51 bore leg; 6.9-9.6 option (a) residual at the lift (vapour_options_v2p4)
        e12 = base + PURGE * V; ok = e12 <= 1.05
        fixed[f'{V:g}'] = dict(V_cm3=V, P_abort={f'W{W:.2f}': float(np.mean(e12 > W)) for W in WS}, W_for_P_abort_0_s=float(base.max() + PURGE * V),
                               W1p05_E0_E2_given_light_s=st((e1 + e12)[ok]), W1p05_E0_E3_given_light_s=st((e1 + b3 + PURGE * V)[ok]))
    summ = {}
    for k, r in res.items():
        case = '|'.join(k.split('|')[:2])
        s = summ.setdefault(case, dict(V_eff_transit_cm3=[1e9, 0], V_eff_quasi_steady_cm3=[1e9, 0], P_abort_W0p65_transit=[1, 0],
                                       P_abort_W0p85_transit=[1, 0], W_for_P_abort_0_transit_s=[9, 0]))
        for key, v in (('V_eff_transit_cm3', r['V_eff_transit_cm3']), ('V_eff_quasi_steady_cm3', r['V_eff_quasi_steady_cm3']),
                       ('P_abort_W0p65_transit', r['P_abort']['W0.65']), ('P_abort_W0p85_transit', r['P_abort']['W0.85']),
                       ('W_for_P_abort_0_transit_s', r['W_for_P_abort_0_s'])):
            s[key] = [min(s[key][0], v), max(s[key][1], v)]
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/route_void_bracket_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={k: dict(file=f'v2p4/{k}', sha256_16=sha16(os.path.join(d, k))) for k in
                       ('relight_vapour_order_v2p4.json', 'vapour_options_v2p4.json', 'start_latency_v2p4.json', 'post_abort_pocket_v2p4.json')},
               constants=dict(V_route_cm3=V_route, A_wall_m2=A_wall, U_drift_wall_m_s=Ud, g_desc_p01_m_s2=gd, purge_s_per_cm3=PURGE,
                              E1_E2_liquid_max_s=float(base.max())),
               cases=res, summary=summ, fixed_states=fixed,
               tag='DERIVED (drift-flux transit estimate; Mechanical ESTIMATE heat; SIM on ASSUMED delays)')
    json.dump(out, open(out_f, 'w'), indent=1)
    print('U_d %.4f m/s, V_route %.2f cm3' % (Ud, V_route))
    for k, s in summ.items():
        print('%-28s V_eff transit %.2f-%.2f | quasi-steady %.2f-%.2f | P_abort W0.65 %.3f-%.3f W0.85 %.3f-%.3f | W_req %.3f-%.3f' % (
            k, *s['V_eff_transit_cm3'], *s['V_eff_quasi_steady_cm3'], *s['P_abort_W0p65_transit'], *s['P_abort_W0p85_transit'], *s['W_for_P_abort_0_transit_s']))
    for k, r in res.items():
        if k.startswith('isothermal'):
            print('  %-44s ovf %6.2f  rv qs %.2f tr %.2f  V_eff qs %.2f tr %.2f  P65 %.3f P85 %.3f  E0E3 max %.3f' % (
                k, r['overflow_cm3'], r['route_void_quasi_steady_cm3'], r['route_void_transit_cm3'], r['V_eff_quasi_steady_cm3'],
                r['V_eff_transit_cm3'], r['P_abort']['W0.65'], r['P_abort']['W0.85'], r['W1.05_E0_E3_given_light_s']['max']))
    for k, r in fixed.items():
        print('fixed %6s cm3 P_abort %s W_req %.3f E0E2 %s E0E3 %s' % (k, {w: round(p, 4) for w, p in r['P_abort'].items()}, r['W_for_P_abort_0_s'],
              {q: round(v, 3) for q, v in r['W1p05_E0_E2_given_light_s'].items()}, {q: round(v, 3) for q, v in r['W1p05_E0_E3_given_light_s'].items()}))
    print('wrote', out_f)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
