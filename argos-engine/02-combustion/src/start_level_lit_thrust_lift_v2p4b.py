"""Lit thrust at the start level, pintle held at THE start-level lift (Combustion v2.4b, 2026-10-13; LEAD CHANGELOG line 203 (7)).

Variant of start_level_lit_thrust_v2p4b.py (identical plant, corners, step and outputs) with the held lift as an argument.
v2.4b defines THE start-level lift as the ignition lift of the lift-vs-T_tank table at E0 (cold-flow capped: <= 37.1 g/s at 20 C and
<= 37.4 g/s at the A1 state, LEAD; CF-3 calibrates it); pre-CF-3 A1 value 0.21776 mm (ECU row at 286.70 K).  The 0.2039 mm run of
the parent script reproduces drogue_hold_check_v2p4 exactly; at another lift that check does not apply and is not asserted.
Parent description follows.

Lit thrust at the start level, pintle held at the 0.2039 mm ignition lift (Combustion v2.4b, 2026-10-13).

REV-COMB-3 R3-14 and LEAD CHANGELOG line 194 (4): GNC's R2 v2 uses F_cold plus the grain_q1d start-level lit history (fuel-starved for
0.1-0.4 s at 0.2039 mm), not 62.5 N x pcf_k.  This script publishes that history.  The plant is the one of drogue_hold_check_v2p4.trace
and ignition_detect_v2p4 part B (grain_q1d v2; pintle held at the v2.8 ignition lift 0.2039 mm from the light; no throttle ramp; the
command held at the start level, which is the LEAD line 186 (2) case with Pc invalid), run to 1.0 s at the solver step (0.5 ms) for the
A1 relight state over Cd 0.65 / 0.70 / 0.75, regression law (a x0.6 n 0.68; a x1.0 n 0.50; a x1.5 n 0.35), preheated fraction at main
ignition 0 / 0.15 / 0.3 / 0.6 and eta_c* 0.85 / 0.92 (72 corners).  E2 per corner by the adopted relative rule (drogue_hold_check_v2p4.
check: rise >= 0.8 bar over the pre-lift baseline for 10 ms on the measured channel, latency 2.3 ms; torch term 0 and 0.3 bar).
Thrust: grain_q1d.thrust (CEA Cf with Schmucker separation, eta_cf 0.975 ASSUMED; zero below 1.3 atm chamber pressure).
Reproduction: the A1 rows of drogue_hold_check_v2p4.json (E2, minimum Pc and rise in the 0.10 s hold) are reproduced exactly (asserted).
Tags: SIM grain_q1d v2 on ASSUMED laws/bands (quasi-steady; combustion roughness not modelled); not physical evidence.
usage: python -I start_level_lit_thrust_lift_v2p4b.py DATA_V2P4_DIR OUT_JSON OUT_CSV LIFT_MM
"""
from __future__ import annotations
import csv, hashlib, itertools, json, os, sys, time
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ignition_detect_v2p4 as ID
import drogue_hold_check_v2p4 as DH
import start_latency_v2p4 as SL

EXPECT_SRC = {'ignition_detect_v2p4.py': 'f21876e9ec9e3cc0', 'drogue_hold_check_v2p4.py': 'b26fb2a78fa483c6',
              'grain_q1d.py': 'e00f692489ec5234', 'start_latency_v2p4.py': '989ccd9a004b2cb9'}
EXPECT_DATA = {'drogue_hold_check_v2p4.json': '70820e0038be39a7'}
T_END, DT = 1.0, 5e-4
R2_N = 37.16                      # GNC R2 accelerometer threshold
PCF_TMAX = 0.5                    # LEAD line 181 (4)
F_START, PCF_K = 62.5, 0.875      # GNC's present start-level model (62.5 N x pcf_k)


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


LIFT_M = None


def run(Cd, af, n, ri, eta):
    cfg = dict(SL.law(n, af)); cfg.update(r_ign_frac=ri, eta_cstar=eta, Cd=Cd, t_open_delay=0.0, h_rate=SL.V_PINTLE)
    e = ID.engine('A1_relight', cfg)
    e.h = e.h_cmd = e.h_target = LIFT_M; e.state = 'start'; e.t_on = 0.0; e.Pc = 1.1e5; e.F = 0.0
    if ri <= 0.0:
        e.r_eff[:] = 1e-12
    ts, Ps, Fs, OF, mo = [], [], [], [], []
    t = 0.0
    while t < T_END - 1e-12:
        e.t = t; e.step(DT); t += DT
        ts.append(t); Ps.append(e.Pc); Fs.append(e.F); OF.append(e.OF); mo.append(e.mox)
    return np.array(ts), np.array(Ps), np.array(Fs), np.array(OF), np.array(mo)


def main(d, out_f, out_csv, lift_mm):
    global LIFT_M
    LIFT_M = float(lift_mm) * 1e-3
    t0 = time.time()
    for f, h in EXPECT_SRC.items():
        assert sha16(os.path.join(HERE, f)) == h, (f, sha16(os.path.join(HERE, f)))
    for f, h in EXPECT_DATA.items():
        assert sha16(os.path.join(d, f)) == h, (f, sha16(os.path.join(d, f)))
    DJ = json.load(open(os.path.join(d, 'drogue_hold_check_v2p4.json')))
    ref = {(r['Cd'], r['a_fac'], r['n'], r['r_ign'], r['eta']): r for r in DJ['rows'] if r['state'] == 'A1_relight'}
    laws = ((0.6, 0.68), (1.0, 0.5), (1.5, 0.35))
    corners = []; cols = {}
    for Cd, (af, n), ri, eta in itertools.product((0.65, 0.70, 0.75), laws, (0.0, 0.15, 0.3, 0.6), (0.85, 0.92)):
        ts, Ps, Fs, OF, mo = run(Cd, af, n, ri, eta)
        k400 = ts <= 0.40 + 1e-12
        chk = DH.check(ts[k400], Ps[k400])
        r0 = ref[(Cd, af, n, ri, eta)]
        for tk in ('torch0.0', 'torch0.3'):
            a, b = chk[tk], r0[tk]
            if abs(LIFT_M - ID.H_V28) < 1e-12:
                assert (a.get('E2_s') is None) == (b.get('E2_s') is None), (Cd, af, n, ri, eta, tk)
                if a.get('E2_s') is not None:
                    for m_ in ('E2_s', 'rise_min_true_bar', 'Pc_min_abs_bar'):
                        assert abs(a[m_] - b[m_]) < 1e-12, (Cd, af, n, ri, eta, tk, m_, a[m_], b[m_])
        lab = f'Cd{Cd:.2f}|a{af:g}|n{n:g}|ri{ri:g}|eta{eta:.2f}'
        cols[lab] = Fs
        row = dict(corner=lab, Cd=Cd, a_fac=af, n=n, r_ign=ri, eta=eta, mox_g_s_at_1s=1e3 * float(mo[-1]),
                   F_N={f'+{int(round(1e3 * tt))}ms': float(np.interp(tt, ts, Fs)) for tt in (0.03, 0.05, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0)},
                   Pc_bar={f'+{int(round(1e3 * tt))}ms': float(np.interp(tt, ts, Ps)) / 1e5 for tt in (0.03, 0.1, 0.2, 0.4, 1.0)},
                   OF={f'+{int(round(1e3 * tt))}ms': float(np.interp(tt, ts, OF)) for tt in (0.03, 0.1, 0.2, 0.4, 1.0)})
        for tk in ('torch0.0', 'torch0.3'):
            e2 = chk[tk].get('E2_s')
            if e2 is None:
                row[tk] = dict(E2_s=None); continue
            w = (ts >= e2) & (ts <= e2 + PCF_TMAX + 1e-12)
            above = ts[w & (Fs >= R2_N)]
            row[tk] = dict(E2_s=e2, F_at_E2_N=float(np.interp(e2, ts, Fs)), F_min_E2_to_E2p0p5_N=float(Fs[w].min()),
                           F_max_E2_to_E2p0p5_N=float(Fs[w].max()), F_mean_E2_to_E2p0p5_N=float(Fs[w].mean()),
                           first_t_after_E2_F_ge_37p16N_s=(float(above[0] - e2) if len(above) else None),
                           share_of_window_F_ge_37p16N=float((Fs[w] >= R2_N).mean()))
        corners.append(row)
    Fm = np.vstack([cols[k] for k in cols])
    env = dict(t_s=[0.03, 0.05, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0])
    for lab_, fn in (('min', np.min), ('median', np.median), ('max', np.max)):
        env[f'F_{lab_}_N'] = [float(np.interp(tt, ts, fn(Fm, axis=0))) for tt in env['t_s']]
    e2s = [c['torch0.0']['E2_s'] for c in corners if c['torch0.0'].get('E2_s') is not None]
    summ = dict(n_corners=len(corners), n_E2_torch0=len(e2s), E2_s_range=[min(e2s), max(e2s)],
                F_min_over_corners_in_E2_to_E2p0p5_N=min(c['torch0.0']['F_min_E2_to_E2p0p5_N'] for c in corners if c['torch0.0'].get('E2_s')),
                F_max_over_corners_in_E2_to_E2p0p5_N=max(c['torch0.0']['F_max_E2_to_E2p0p5_N'] for c in corners if c['torch0.0'].get('E2_s')),
                n_corners_never_ge_37p16N_in_window=sum(1 for c in corners if c['torch0.0'].get('E2_s') and c['torch0.0']['first_t_after_E2_F_ge_37p16N_s'] is None),
                latest_first_t_ge_37p16N_after_E2_s=max((c['torch0.0']['first_t_after_E2_F_ge_37p16N_s'] for c in corners
                                                         if c['torch0.0'].get('E2_s') and c['torch0.0']['first_t_after_E2_F_ge_37p16N_s'] is not None), default=None),
                gnc_present_model_N=F_START * PCF_K,
                F_at_1s_range_N=[float(Fm[:, -1].min()), float(Fm[:, -1].max())])
    with open(out_csv, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['t_from_light_s', 'F_min_N', 'F_median_N', 'F_max_N', 'Pc_note'] + [f'F_N|{k}' for k in cols])
        Fmin, Fmed, Fmax = Fm.min(axis=0), np.median(Fm, axis=0), Fm.max(axis=0)
        for i, tt in enumerate(ts):
            w.writerow([f'{tt:.4f}', f'{Fmin[i]:.3f}', f'{Fmed[i]:.3f}', f'{Fmax[i]:.3f}', ''] + [f'{cols[k][i]:.3f}' for k in cols])
    out = dict(version='v2.4b', date='2026-10-13', script='02-combustion/src/start_level_lit_thrust_lift_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='LEAD CHANGELOG line 203 (7) and 194 (4): grain_q1d lit thrust history at THE start-level lift (A1 table row) for GNC R2 v2 and P4c', lift_mm=float(lift_mm), parent_script=dict(file='start_level_lit_thrust_v2p4b.py', sha256_16=sha16(os.path.join(HERE, 'start_level_lit_thrust_v2p4b.py'))),
               inputs=dict(code=EXPECT_SRC, data=EXPECT_DATA), reproduction=('A1 rows of drogue_hold_check_v2p4.json identical (asserted)' if abs(LIFT_M - ID.H_V28) < 1e-12 else 'not applicable at this lift (the parent 0.2039 mm run reproduces drogue_hold_check_v2p4 exactly)'),
               state=f'A1_relight (start_latency_v2p4 STATES: T 286.70 K, m 1.16 kg, port 32.2 mm); lift {float(lift_mm):.5f} mm held from the light; no ramp',
               time_origin='light (main ignition) at t = 0; E2 per corner below; GNC aligns its E2 with the corner E2',
               R2=dict(threshold_N=R2_N, window_s=PCF_TMAX, gnc_present_model='62.5 N x pcf_k 0.875 = 54.7 N'),
               summary=summ, envelope=env, corners=corners,
               csv=dict(file=os.path.basename(out_csv), step_s=DT, columns='t from the light; min/median/max over the 72 corners; one column per corner (N)'),
               tags=dict(model='SIM grain_q1d v2 on ASSUMED laws/bands (quasi-steady; roughness not modelled); thrust grain_q1d.thrust with '
                               'Schmucker separation and eta_cf 0.975 ASSUMED; zero below 1.3 atm chamber pressure',
                         status='not physical evidence; IGN-1 and the T series with a load cell measure it'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print(json.dumps(summ, indent=1))
    print('envelope', json.dumps(env))
    for c in corners[:6]:
        print(c['corner'], c['torch0.0'], c['F_N'])
    print('wrote', out_f, sha16(out_f), out_csv, sha16(out_csv), round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main(*sys.argv[1:5])
