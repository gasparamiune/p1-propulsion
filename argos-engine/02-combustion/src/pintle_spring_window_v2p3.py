"""Spring feasibility window for the 3 mm-stem pintle with the needle-force laws of needle_force_v2p3.py (Combustion, 2026-10-12).

Mechanical's criteria (pintle_inline_v34.py v2.1), with the force law each criterion needs:
  C1 spring close (-10 % spring, full stroke, tank 3.5 / 5.5 / 7.0 MPa): law L0 (opening bound after 0.1 mm) - the conservative closing case.
  C2 servo opening (+10 % spring) <= HV69 stall 0.90 N m (7.4 V) / 1.5 = 0.60 N m over the FLIGHT cases, with L1 (central) or L2 (upper):
     bench full stroke (no pressure), start to the ignition lift (<= 0.3 mm, P1 = tank 5.05 or 7.0 MPa, chamber 1.5 bar torch),
     hot-fire line (throttle_map_v2 states, P_down = Pc, D_port 25 mm).  Unlit full stroke at tank pressure is a ground-test case (procedure).
Configurations: Mechanical's S3 (3 mm stem, seal 18.75 N ASSUMED) with the PTFE 15 mm guide at mu 0.10 and 0.20, plus two hypothetical
rolling-guide variants (rolling_18mm, plain or ball link pins) to bracket the lead's 'rolling guide, lower preload' fallback.
Spring T = T0 + k (phi - 15 deg); seat load = T0 / (dx/dphi at closed).  Everything inherits Mechanical's ASSUMED frictions.
Output: data/v2/pintle_spring_window_v2p3.json.  DERIVED, not a test result.
"""
from __future__ import annotations
import sys, json, math, hashlib, importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import needle_force_v2p3 as NF                                # F_bounds, PA, P_TORCH, load_mech

OUT = ROOT / 'data/v2/pintle_spring_window_v2p3.json'
T_ALLOW = 0.90 / 1.5


def main():
    m = NF.load_mech()
    df = pd.read_csv(NF.OUT_CSV, comment='#')
    hot = df[df.D_port_m == 0.025]
    configs = {
        'S3_PTFE15mu20 (lead baseline friction)': dict(m.CONFIGS['S3_PTFE15mu20_plainpins']),
        'S3_PTFE15 (mu 0.10)': dict(m.CONFIGS['S3_PTFE15_plainpins']),
        'S3_rolling_plainpins (hypothetical)': {'stem_d': 3.0, 'f_seal': 18.75, 'guide': 'rolling_18mm', 'pin_mu': 0.15},
        'S3_rolling_ballpins (hypothetical)': {'stem_d': 3.0, 'f_seal': 18.75, 'guide': 'rolling_18mm', 'pin_mu': 0.005},
    }
    y_use = 11
    phi_c = m.CRANK['phi_closed']
    phis_full = list(np.linspace(phi_c, m.phi_at_lift(m.CRANK['x_stop']), 40))
    phis_start = list(np.linspace(phi_c, m.phi_at_lift(0.3), 12))
    dx0 = m.dxdphi(phi_c) * 1e-3
    T0s = np.round(np.arange(0.10, 0.451, 0.01), 3)
    ks = np.round(np.arange(0.0, 0.301, 0.01), 3)
    out = {'version': 'v2.3', 'date': '2026-10-12', 'script': '02-combustion/src/pintle_spring_window_v2p3.py',
           'mechanical_script_sha256_16': hashlib.sha256(NF.MECH.read_bytes()).hexdigest()[:16],
           'criteria': {'C1': 'L0, -10 % spring, min closing assist over the stroke at 3.5/5.5/7.0 MPa >= 0 (targets 0.05 at MEOP, 0.08 at 5.5 MPa)',
                        'C2': f'L1 or L2, +10 % spring, max opening torque over bench + start (<= 0.3 mm, 5.05/7.0 MPa, torch) + hot-fire line <= {T_ALLOW:.2f} N m'},
           'grid': {'T0_Nm': [float(T0s[0]), float(T0s[-1]), 0.01], 'k_Nm_per_rad': [float(ks[0]), float(ks[-1]), 0.01]}, 'results': {}}
    orig = m.F_po
    for cname, c in configs.items():
        m.set_config(c)
        g = m.GUIDE_OPTIONS[c['guide']]
        d = c['stem_d'] * 1e-3
        # pre-compute pressure forces (Mechanical sign + opening) per case
        cases_c1 = {P: (lambda P: (lambda x_mm, PP: orig(x_mm, P)))(P) for P in (3.5e6, 5.5e6, 7.0e6)}
        res_c = {}
        for law in ('L1', 'L2'):
            idx = 1 if law == 'L1' else 2

            def f_start(P1):
                return lambda x_mm, PP: -NF.F_bounds(P1, NF.P_TORCH, max(0.0, x_mm) * 1e-3, d)[idx]
            hot_rows = [(m.phi_at_lift(x.lift_mm), -NF.F_bounds(x.P1_Pa, x.Pc_Pa, x.lift_mm * 1e-3, d)[idx], x.P1_Pa) for x in hot.itertuples()]
            feas = []
            grid = {}
            for T0 in T0s:
                for k in ks:
                    Tn = lambda p: T0 + k * math.radians(p - phi_c)
                    # C1 (L0)
                    m.F_po = orig
                    a = {P: min(m.servo_torque(p, 0.9 * Tn(p), P, False, g, y_use, c['f_seal'])[0] for p in phis_full) for P in (3.5e6, 5.5e6, 7.0e6)}
                    if a[7.0e6] < 0 or a[5.5e6] < 0 or a[3.5e6] < 0:
                        continue
                    # C2 bench (no pressure)
                    m.F_po = lambda x_mm, PP: 0.0
                    t_b = max(m.servo_torque(p, 1.1 * Tn(p), NF.PA, True, g, y_use, c['f_seal'])[0] for p in phis_full)
                    if t_b > T_ALLOW:
                        continue
                    t_s = 0.0
                    for P1 in (5.05e6, 7.0e6):
                        m.F_po = f_start(P1)
                        t_s = max(t_s, max(m.servo_torque(p, 1.1 * Tn(p), P1, True, g, y_use, c['f_seal'])[0] for p in phis_start))
                    t_h = 0.0
                    for phi, fpo, P1 in hot_rows:
                        m.F_po = (lambda v: (lambda x_mm, PP: v))(fpo)
                        t_h = max(t_h, m.servo_torque(phi, 1.1 * Tn(phi), P1, True, g, y_use, c['f_seal'])[0])
                    t2 = max(t_b, t_s, t_h)
                    if t2 <= T_ALLOW:
                        feas.append({'T0_Nm': float(T0), 'k_Nm_per_rad': float(k), 'C2_max_Nm': round(t2, 3), 'C2_bench_start_hot': [round(t_b, 3), round(t_s, 3), round(t_h, 3)],
                                     'margin_7V4': round(0.90 / t2, 2), 'assist_MEOP': round(a[7.0e6], 3), 'assist_5p5': round(a[5.5e6], 3),
                                     'assist_3p5': round(a[3.5e6], 3), 'seat_load_nom_N': round(T0 / dx0, 1),
                                     'targets_met': bool(a[7.0e6] >= 0.05 and a[5.5e6] >= 0.08)})
            m.F_po = orig
            best = max(feas, key=lambda r: (r['targets_met'], r['assist_MEOP'], r['margin_7V4'])) if feas else None
            res_c[law] = {'n_feasible': len(feas), 'n_targets_met': sum(r['targets_met'] for r in feas),
                          'T0_range_Nm': [min(r['T0_Nm'] for r in feas), max(r['T0_Nm'] for r in feas)] if feas else None,
                          'seat_load_nom_range_N': [min(r['seat_load_nom_N'] for r in feas), max(r['seat_load_nom_N'] for r in feas)] if feas else None,
                          'best_by_MEOP_assist': best,
                          'lead_baseline_T0.30_k0.10_inside': any(abs(r['T0_Nm'] - 0.30) < 1e-9 and abs(r['k_Nm_per_rad'] - 0.10) < 1e-9 for r in feas),
                          'v2p1_T0.19_k0.17_inside': any(abs(r['T0_Nm'] - 0.19) < 1e-9 and abs(r['k_Nm_per_rad'] - 0.17) < 1e-9 for r in feas),
                          'feasible': feas}
            print(cname, law, json.dumps({k_: v_ for k_, v_ in res_c[law].items() if k_ != 'feasible'}))
        res_c['config'] = c
        out['results'][cname] = res_c
    m.F_po = orig
    OUT.write_text(json.dumps(out, indent=1, default=float))


if __name__ == '__main__':
    main()
