"""Run the quasi-1D engine model over every gnc.json v1 duty cycle + max-thrust cases (Combustion v2).
usage: python run_dc.py OUTDIR [case ...]     cases: dc, maxthrust, map, band, plant (default all)
Outputs (OUTDIR = data/v2/dc): per-run CSV (10 ms), summary_v2.json, figures in figs/v2/dc/.
"""
from __future__ import annotations
import json, math, os, sys, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
from tank import EquilibriumTank
from tank_nheq import NonEqTank
import CoolProp.CoolProp as CP

INP = os.path.join(HERE, '..', 'inputs', 'snap_20261012')
G0 = 9.80665
FLIGHT = {'DC-A1': 'DC-A1_full_flight_drogue_300m_v1', 'DC-A2': 'DC-A2_full_flight_freefall_300m_v1',
          'DC-B1': 'DC-B1_hop_100m_floor20_v1', 'DC-B2': 'DC-B2_hop_50m_floor20_v1'}
GROUND = {'DC-C': 'DC-C_tethered_hover_v1', 'DC-D': 'DC-D_static_fire_qualification_v1'}
GROUND_TANK = dict(V=15e-3, m=10.0, T0=293.15, tag='ASSUMED ground run tank 15 L / 10 kg N2O / 20 C, equilibrium (gnc.json: ground-fed)')


def load_dc(name, inp=None):
    inp = inp or INP
    idxf = sorted(f for f in os.listdir(inp) if f.startswith('duty_cycles_index_'))[-1]
    idx = json.load(open(os.path.join(inp, idxf)))
    meta = [c for c in idx['cycles'] if c['name'] == name][0]
    d = pd.read_csv(os.path.join(inp, name + '.csv'), comment='#')
    dc = dict(t=d.t_s.values, F_cmd=d.F_cmd_N.values, a_axial=d.a_axial_specific_mps2.values)
    return dc, meta, d


def make_tank(kind, V, m, T0, E=1e3, D=0.1016 - 2 * 0.003175):
    if kind == 'eq':
        return EquilibriumTank(V, m, T0)
    return NonEqTank(V, m, T0, D=D, E=E, m_wall=0.9 + 0.35 * V / 2.059e-3)


def summarize(rec, e, name, extra=None):
    r = pd.DataFrame(rec)
    on = r[r.state.isin(['start', 'run'])]
    burn = (r.F > 1.0).sum() * 0.01
    track = on[(on.F_cmd > 0) & (on.state == 'run')]
    err = (track.F - track.F_cmd)
    sat = track[np.isfinite(track.F_ceiling) & (track.F_cmd > track.F_ceiling + 0.5)]
    out = dict(case=name, burn_s=round(burn, 3), impulse_Ns=round(e.impulse, 1), ox_used_kg=round(e.ox_used, 4),
               fuel_used_kg=round(e.fuel_burnt, 4), OF_mean=round(e.ox_used / max(e.fuel_burnt, 1e-9), 3),
               Isp_mean_s=round(e.impulse / ((e.ox_used + e.fuel_burnt) * G0), 1),
               OF_range=[round(float(np.nanmin(on.OF)), 2), round(float(np.nanmax(on.OF)), 2)] if len(on) else None,
               Pc_max_Pa=round(float(r.Pc.max()), 0), w_min_end_mm=round(float(r.w_min.iloc[-1]) * 1e3, 2),
               D_port_end_mm=[round(float(r.D_min.iloc[-1]) * 1e3, 2), round(float(r.D_max.iloc[-1]) * 1e3, 2)],
               burnthrough_s=e.burnthrough, P_tank_end_Pa=round(float(r.P_tank.iloc[-1]), 0),
               m_liq_end_kg=round(float(r.m_liq.iloc[-1]), 4),
               tracking_rms_N=round(float(np.sqrt(np.mean(err ** 2))), 2) if len(track) else None,
               ceiling_limited_s=round(len(sat) * 0.01, 2),
               dpc_min=round(float(np.nanmin(on.dpc)), 3) if len(on) else None,
               min_F_ceiling_N=round(float(np.nanmin(on.F_ceiling)), 1) if on.F_ceiling.notna().any() else None,
               sep_time_s=round(float(on.sep_eps.notna().sum() * 0.01), 2))
    if extra:
        out.update(extra)
    return out


def run_case(name, file, tank_kind='neq', E=1e3, band=1.0, T0=None, outdir=None, cfg=None, ground=False, inp=None):
    dc, meta, d = load_dc(file, inp)
    if ground:
        tk = make_tank('eq', GROUND_TANK['V'], GROUND_TANK['m'], GROUND_TANK['T0'])
        init_run = False
    else:
        T0 = T0 or float(d.T_tank_K.iloc[0]) if 'T_tank_K' in d and np.isfinite(d.T_tank_K.iloc[0]) else 293.15
        tk = make_tank(tank_kind, meta['tank_V_m3'], meta['m_n2o_kg'], T0, E)
        init_run = d.F_cmd_N.iloc[0] > 0
    c = dict(cfg or {}); c['a'] = Q.V['a'] * band
    t0 = time.time()
    rec, e = Q.simulate(dc, tk, cfg=c, init_running=init_run)
    tag = f"{name}_{'ground' if ground else tank_kind + ('' if tank_kind == 'eq' else f'E{E:.0e}')}_reg{band:g}"
    s = summarize(rec, e, tag, dict(tank=('ground ' + GROUND_TANK['tag']) if ground else f"{tank_kind} E={E:g} V={meta['tank_V_m3']*1e3:.3f} L m={meta['m_n2o_kg']} kg",
                                      regression_scale=band, wall_s=round(time.time() - t0, 1), gnc_burn_s=meta.get('burn_time_s'),
                                      gnc_impulse_Ns=meta.get('total_impulse_Ns')))
    if outdir:
        pd.DataFrame(rec).to_csv(os.path.join(outdir, tag + '.csv'), index=False, float_format='%.6g')
    print(json.dumps(s), flush=True)
    return s, rec, e


def run_maxthrust(T0, tank_kind, E, V, m, outdir, label, t_end=30.0, cfg=None):
    dc = dict(t=np.array([0.0, t_end]), F_cmd=np.array([500.0, 500.0]), a_axial=np.array([30.0, 30.0]))
    tk = make_tank(tank_kind, V, m, T0, E)
    rec, e = Q.simulate(dc, tk, cfg=cfg, init_running=True, t_extra=0.0)
    r = pd.DataFrame(rec)
    # stop records at liquid depletion
    r = r[r.m_liq > 0.0]
    tag = f"maxthrust_{label}_{tank_kind}{'' if tank_kind == 'eq' else f'E{E:.0e}'}_T{T0-273.15:.0f}C"
    r.to_csv(os.path.join(outdir, tag + '.csv'), index=False, float_format='%.6g')
    full = r[r.F >= 499.0]
    s = dict(case=tag, T0_C=T0 - 273.15, tank=f'{tank_kind} E={E:g} V={V*1e3:.3f} L m={m} kg',
             t_500N_s=round(float(full.t.max()) if len(full) else 0.0, 2), t_liquid_s=round(float(r.t.max()), 2),
             impulse_to_liquid_Ns=round(float(r.F.sum() * 0.01), 0), fuel_kg=round(e.fuel_burnt, 3),
             P_tank_end=round(float(r.P_tank.iloc[-1]), 0), w_min_end_mm=round(float(r.w_min.iloc[-1]) * 1e3, 2),
             burnthrough_s=e.burnthrough)
    print(json.dumps(s), flush=True)
    return s


class _FixedTank:
    def __init__(self, P, T):
        self.P = P; self.T = T; self.T_L = T; self.liquid = True; self.m_l = 1.0
    def step(self, *a, **k):
        pass


def throttle_map(outdir, cfg=None):
    rows = []
    for Pt in (35e5, 40e5, 45e5, 50e5, 55e5):
        T = CP.PropsSI('T', 'P', Pt, 'Q', 0, 'NitrousOxide')
        for Dp in (0.025, 0.030, 0.035, 0.040, 0.045):
            e = Q.Engine(_FixedTank(Pt, T), cfg=cfg); e.D[:] = Dp
            cei = e.ceiling()
            for fr in (1.0, 0.75, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.125):
                F = 500 * fr
                if cei is None or F > cei['F'] + 0.1:
                    rows.append(dict(P_tank_Pa=Pt, T_tank_K=round(T, 2), D_port_m=Dp, frac=fr, F_N=float('nan'),
                                     F_ceiling_N=cei['F'] if cei else float('nan'), note='above ceiling'))
                    continue
                h, _ = e.lift_for_thrust(F, cei=cei); s = e.steady(h)
                rows.append(dict(P_tank_Pa=Pt, T_tank_K=round(T, 2), D_port_m=Dp, frac=fr, F_N=s['F'], Pc_Pa=s['Pc'],
                                 mdot_ox=s['mox'], mdot_f=s['mf'], OF=s['OF'], Isp_SL_s=s['Isp'], lift_m=s['h'],
                                 dP_over_Pc=s['dpc'], sep_eps=s['es'] or '', F_ceiling_N=cei['F'], ceiling_limit=cei['limit']))
            print(f'map Pt={Pt/1e5:.0f} D={Dp*1e3:.0f} ceiling {cei["F"] if cei else None}', flush=True)
    fn = os.path.join(outdir, 'throttle_map_v2.csv')
    with open(fn, 'w') as f:
        f.write('# Throttle map v2 (quasi-steady, quasi-1D port, uniform port diameter D_port; saturated tank at P_tank; '
                'line loss ~mdot^2; Dyer pintle Cd 0.70; eta_c* 0.92; eta_cf 0.975; ceiling = min(stroke, dP/Pc >= 0.25)). '
                'SIM grain_q1d.py v2 nominal regression law (ASSUMED). SI.\n')
        pd.DataFrame(rows).to_csv(f, index=False, float_format='%.6g')
    return fn


def plant(outdir, cfg=None):
    """Valve-lift -> Pc small-signal step responses at several operating points (tank frozen)."""
    out = []
    for fr in (1.0, 0.5, 0.25, 0.125):
        e = Q.Engine(_FixedTank(50.5e5, 293.15), cfg=cfg)
        s0 = e.init_steady(500 * fr)
        h0 = e.h; dh = 0.03 * h0
        # settle 0.3 s at h0 (thermal lag consistent), then step +3 % lift
        e.t = 0.0
        for _ in range(300):
            e.h_target = h0; e.step(1e-3)
        Pc0 = e.Pc; F0 = e.F
        tr = []
        e.h = e.h_cmd = h0 + dh; e.h_target = h0 + dh
        for k in range(4000):
            e.h_target = h0 + dh; e.h_cmd = h0 + dh
            e.step(1e-3); tr.append((k * 1e-3 + 1e-3, e.Pc, e.F, e.mf, e.mox))
        tr = np.array(tr)
        dP = tr[:, 1] - Pc0; dPinf = dP[-1]
        # fit: dP(t) = K dh [ (1-phi)(1-exp(-t/tc)) + phi (1 - exp(-t/tf)) ] (tc << tf)
        K = dPinf / dh
        fast = dP[int(0.03 / 1e-3)] / dPinf     # value after 30 ms ~ chamber fill complete
        phi = 1 - fast
        # chamber time constant: 63 % of the fast part
        target = 0.632 * fast * dPinf
        i63 = int(np.argmax(dP >= target)); tc = tr[i63, 0]
        rest = (dP - fast * dPinf) / max(phi * dPinf, 1e-9)
        j = int(np.argmax(rest >= 0.632)) if phi > 0.01 else 0; tf = tr[j, 0] if phi > 0.01 else float('nan')
        out.append(dict(frac=fr, h0_m=h0, Pc0_Pa=Pc0, F0_N=F0, K_h_Pa_per_m=K, phi=phi, tau_c_s=tc, tau_f_s=tf,
                        dF_dh_N_per_m=(tr[-1, 2] - F0) / dh))
        print(json.dumps(out[-1]), flush=True)
    json.dump(out, open(os.path.join(outdir, 'plant_valve_to_pc_v2.json'), 'w'), indent=1)
    return out


if __name__ == '__main__':
    outdir = sys.argv[1]; os.makedirs(outdir, exist_ok=True)
    what = sys.argv[2:] or ['dc', 'maxthrust', 'map', 'plant', 'band']
    summ_fn = os.path.join(outdir, 'summary_v2.json')
    S = json.load(open(summ_fn)) if os.path.exists(summ_fn) else {}
    if 'dc' in what:
        for k, f in FLIGHT.items():
            for tk, E in (('neq', 1e3), ('eq', 0), ('neq', 1e2)):
                s, _, _ = run_case(k, f, tk, E, outdir=outdir, cfg=Q.VARIANTS['v1_helix_L200']); S[s['case']] = s
        for k, f in GROUND.items():
            s, _, _ = run_case(k, f, ground=True, outdir=outdir, cfg=Q.VARIANTS['v1_helix_L200']); S[s['case']] = s
        json.dump(S, open(summ_fn, 'w'), indent=1, default=float)
    if 'g2' in what:
        G2 = dict(r_helix=0.0, F_helix=1.0, L_grain=0.200)
        for k, f in list(FLIGHT.items()) + list(GROUND.items()):
            for b in (1.0, 1.5, 0.6):
                s, _, _ = run_case(k + '-G2', f, 'neq', 1e3, band=b, outdir=outdir, ground=k in GROUND, cfg=G2)
                S[s['case']] = s
                json.dump(S, open(summ_fn, 'w'), indent=1, default=float)
    if 'g3' in what:
        # straight centred port, longer grains (v2 grain trade): flight duty cycles only
        for L, tag in ((0.26, 'S260'), (0.23, 'S230')):
            G3 = dict(r_helix=0.0, F_helix=1.0, L_grain=L)
            for k, bands in (('DC-A1', (1.0, 1.5, 0.6)), ('DC-B1', (1.0, 1.5)), ('DC-A2', (1.0,)), ('DC-B2', (1.0,))):
                for b in bands:
                    s, _, _ = run_case(k + '-' + tag, FLIGHT[k], 'neq', 1e3, band=b, outdir=outdir, cfg=G3)
                    S[s['case']] = s
                    json.dump(S, open(summ_fn, 'w'), indent=1, default=float)
    if 'band' in what:
        for k, f in list(FLIGHT.items()) + list(GROUND.items()):
            for b in (0.6, 1.5):
                s, _, _ = run_case(k, f, 'neq', 1e3, band=b, outdir=outdir, ground=k in GROUND,
                                   cfg=Q.VARIANTS['v1_helix_L200']); S[s['case']] = s
        json.dump(S, open(summ_fn, 'w'), indent=1, default=float)
    if 'maxthrust' in what:
        for T0 in (288.15, 293.15, 298.15):
            for tk, E in (('eq', 0), ('neq', 1e3), ('neq', 1e2)):
                s = run_maxthrust(T0, tk, E, 2.059e-3, 1.3, outdir, 'A1tank'); S[s['case']] = s
        json.dump(S, open(summ_fn, 'w'), indent=1, default=float)
    if 'map' in what:
        S['throttle_map_csv'] = throttle_map(outdir)
        json.dump(S, open(summ_fn, 'w'), indent=1, default=float)
    if 'plant' in what:
        S['plant'] = plant(outdir)
        json.dump(S, open(summ_fn, 'w'), indent=1, default=float)
