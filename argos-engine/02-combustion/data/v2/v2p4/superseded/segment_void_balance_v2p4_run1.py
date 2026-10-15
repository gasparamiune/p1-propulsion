"""Volume balance of the MV-to-seat segment over the A1 coast, with S1 venting, option (d) and a no-U re-route
(Combustion v2.4; coordinator relays of Electronics SIL S11 and the GNC drogue window, 2026-10-13).

Why: relight_vapour_order_v2p4 treats the route (module + wall line, 16.13 cm3) as vented by S1 and adds only a
quasi-steady bubble void. A relief valve vents the volume EXPANSION, not the void: whenever vapour sits at the S1 port,
S1 vents vapour and the segment's void grows by the evaporated liquid volume, v_l/h_fg = 0.0067 cm3/J (the vented vapour
carries away only (v_g - v_l)/h_fg per joule). Once the U is full, every joule that still evaporates liquid adds 0.0067 cm3
of vapour cap under S1, at the top of the route (the end of the segment farthest from the pintle in flow order).
Option (d) adds a second exit: with the MV open the top of the route can exchange vapour for tank liquid through the MV
path, limited by counter-current flooding. The U cannot use it (its crest is 159.6 mm above the U-bottom).

Model (per heat case x GNC coast series; dt 10 ms; MECO to the relight command):
  heat q(t): Mechanical FE bore shape of the case family (same extrapolation as relight_vapour_order_v2p4), split U / route
    by the case totals (vapour_options_v2p4 six cases).
  coast-up (before the drogue load, f_z <= 0.5 g): bubbles stay where they form (no drift in the small passages); S1 sees
    liquid and vents liquid. U vapour fills the U (excess pushed into the route as bubbles); route vapour stays as bubbles.
  drogue load: route bubbles rise to the top of the route (cap). From then on:
    arrivals at the top  A = v_g/h_fg q_R + overflow of a full U;
    expansion            e = (v_g - v_l)/h_fg q_evap (q_evap = heat that still evaporates liquid);
    vapour leaving the top X = min(A + cap/dt, X_max); dcap = (A - X) dt; cap + U <= 44 cm3.
    S1 only: X_max = e. MV open (d): X_max = the largest X with X <= e (co-current, no limit) or the Wallis counter-current
    limit sqrt(X) rho_v^.25 + sqrt(X - e) rho_l^.25 <= C (g D drho)^.25 sqrt(A_p) (liquid in = X - e), at the series' f_z
    (0 when f_z <= 0), D = 8 mm module drilling (ASSUMED, as vapour_options_v2p4), C 0.725 and 1.0.
  post-fill heat of a full U: 'wet' = it keeps evaporating liquid at the U-bottom front at the FE rate (as relight_vapour_order;
    heat conducted to the liquid); 'dry' = it stops (dry walls; lower bound).
  no-U re-route (research case): the only trap is the 4.51 cm3 bore-leg annulus; every other vapour reaches the top of a
    monotonic line; exchange through a line / MV path of D = 8-16 mm.
Ignition (same 200 000-sample E1 -> E2 distribution, seed 2024): flow order [U vapour][liquid slug L][cap][tank liquid].
  'paused' convention: the ignition clock runs only on liquid: E2 = base + purge (U + cap if the slug is too short);
  'restart' convention: a slug shorter than ignition delay + confirmation is dead time and the clock restarts on tank liquid:
    E2 = base + purge U + (slug time + purge cap if too short). The truth is between them (ignition data: IGN-1, CF-4).
usage: python -I segment_void_balance_v2p4.py DATA_V2P4_DIR SERIES_CSV DROGUE_ENVELOPE_CSV OUT_JSON
"""
from __future__ import annotations
import json, math, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import start_latency_v2p4 as SL

V_SEG = 44.0
WS = (0.65, 0.76, 0.85, 0.88, 0.93, 1.05)
DT = 0.01
FAM_LAB = {'LO': 'DC-A1dispp99_tg711_hi_SS316L_L2.5_v11pre36IN', 'HI': 'DC-A1dispp99_tg711_hi_SS316L_L2.5_v11pre36ING10'}


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def wallis_xmax(e, fz, D, p, C):
    """Largest vapour outflow X [cm3/s] through a tube of diameter D [m] when the liquid inflow is X - e (X > e is
    counter-current); X <= e is always possible (co-current outflow)."""
    if fz <= 0 or C <= 0:
        return e
    A = math.pi / 4 * D * D
    K = C * (fz * D * (p['rho_l'] - p['rho_v'])) ** 0.25 * math.sqrt(A)        # sqrt(m3/s) units
    f = lambda X: math.sqrt(X * 1e-6) * p['rho_v'] ** 0.25 + math.sqrt(max(X - e, 0.0) * 1e-6) * p['rho_l'] ** 0.25 - K
    if f(e) >= 0:
        return e
    lo, hi = e, e + 1.0
    while f(hi) < 0:
        hi *= 2.0
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if f(m) < 0:
            lo = m
        else:
            hi = m
    return lo


def simulate(qf, Q_U, Q_R, Tw, t_dl, p, V_Umax, wet, t_mv=None, D_mv=8e-3, C=0.0, fz_of_t=None):
    """Returns V_U, V_cap at Tw (cm3), the U fill time and the cap history summary."""
    vpj, lpj = p['vap_cm3_per_J'], p['liq_cm3_per_J']
    VU = 0.0; Rb = 0.0; cap = 0.0; t_full = None; cap_max = 0.0; t_cap_zero_after_mv = None
    n = int(round(Tw / DT))
    for k in range(n):
        t = (k + 0.5) * DT
        q = qf(t); qU = q * Q_U; qR = q * Q_R
        if t < t_dl:                                           # coast-up: frozen bubbles, S1 vents liquid
            dV = vpj * qU * DT
            room = V_Umax - VU
            if dV <= room:
                VU += dV
            else:
                VU = V_Umax; Rb += dV - room
                t_full = t_full if t_full is not None else t
            Rb += vpj * qR * DT
            if VU + Rb >= V_SEG:
                Rb = V_SEG - VU
            continue
        if Rb > 0:                                             # drogue load: route bubbles reach the top
            cap += Rb; Rb = 0.0
        if VU < V_Umax:
            dV = vpj * qU * DT; room = V_Umax - VU
            if dV <= room:
                VU += dV; over = 0.0; q_ev = qU + qR
            else:
                VU = V_Umax; frac = room / dV; over = (dV - room) if wet else 0.0
                q_ev = qR + qU * (1.0 if wet else frac)
                t_full = t_full if t_full is not None else t
        else:
            over = vpj * qU * DT if wet else 0.0
            q_ev = qR + (qU if wet else 0.0)
        A = vpj * qR * DT + over
        e = (vpj - lpj) * q_ev                                 # cm3/s
        mv_open = t_mv is not None and t >= t_mv
        fz = fz_of_t(t) if (mv_open and fz_of_t is not None) else 0.0
        if (not mv_open) or (A + cap <= e * DT):
            Xmax = e                                           # S1 only, or nothing beyond the expansion to remove
        else:
            Xmax = wallis_xmax(e, fz, D_mv, p, C)
        X = min(A + cap, Xmax * DT)
        cap = cap + A - X
        if VU + cap > V_SEG:
            cap = V_SEG - VU
        cap_max = max(cap_max, cap)
        if mv_open and cap <= 1e-9 and t_cap_zero_after_mv is None:
            t_cap_zero_after_mv = t - t_mv
    return dict(V_U_cm3=VU, V_cap_cm3=max(cap, 0.0), slug_cm3=max(V_SEG - VU - cap, 0.0), t_U_full_s=t_full, cap_max_cm3=cap_max,
                t_cap_cleared_after_MV_open_s=t_cap_zero_after_mv)


def main(d, series_f, env_f, out_f):
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    OP = json.load(open(os.path.join(d, 'vapour_options_v2p4.json')))
    MG = json.load(open(os.path.join(d, 'coast_migration_v2p4.json')))
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    PA = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
    p = VO['properties']; geo = VO['geometry']; V_U = geo['U_volume_cm3']; V_bore = geo['bore_leg_cm3']
    mc_f = VO['inputs']['mech_coast']['file']
    # Mechanical's coast file may have gained runs since relight_vapour_order_v2p4 read it (05:36 adds DC-A1v28liq); the two
    # series used here must reproduce VO's window scales exactly (checked below), whatever the file hash
    MC = json.load(open(mc_f)); T_m = VO['window_s']['mech']
    trap = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')
    shapes = {}
    for fam, lab in FAM_LAB.items():
        s = MC['runs'][lab]['series']; tt0 = np.array(s['t_s']) - s['t_s'][0]; q = np.array(s['Q_W']); kf = np.polyfit(tt0[-5:], q[-5:], 1)
        def qf(t, tt0=tt0, q=q, kf=kf):
            return float(np.interp(t, tt0, q)) if t <= tt0[-1] else float(np.polyval(kf, t))
        x = np.linspace(0, tt0[-1], 2000); E = trap(np.interp(x, tt0, q), x)
        if T_m > tt0[-1]:
            xx = np.linspace(tt0[-1], T_m, 200); E += trap(np.polyval(kf, xx), xx)
        else:
            x = np.linspace(0, T_m, 2000); E = trap(np.interp(x, tt0, q), x)
        shapes[fam] = (qf, E)
        def E_to(T, tt0=tt0, q=q, kf=kf):
            if T <= tt0[-1]:
                x = np.linspace(0, T, 400); return float(trap(np.interp(x, tt0, q), x))
            x = np.linspace(tt0[-1], T, 200); return float(trap(q, tt0) + trap(np.polyval(kf, x), x))
        for w, T in VO['window_s'].items():
            assert abs(E_to(T) / E_to(T_m) - VO['window_scale'][fam][w]) < 1e-9, f'coast series {lab} differs from the VO input'
    S = pd.read_csv(series_f)
    fz_series = {}
    for name, g in S.groupby('series'):
        g = g[g.t_minus_relight_cmd_s <= 1e-9].sort_values('t_s')
        tt = g.t_s.values - g.t_s.values[0]; fz = g.fz_mv_mps2.values
        fz_series[name] = (lambda t, tt=tt, fz=fz: float(np.interp(t, tt, fz)))
    # distribution
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
    assert abs(float(base.max()) - PA['E1_E2_liquid_s']['max']) < 1e-9, 'distribution not reproduced'
    need = base - t_lift                                       # liquid time needed for E2 (ignition delay + confirmation)
    PURGE = VO['purge_s_per_cm3']; DEAD = VO['liquid_plug_dead_time_s_per_cm3']

    def ignite(VUv, cap, slug):
        o = {}
        t_s = slug * DEAD
        short = need > t_s
        for conv in ('paused', 'restart'):
            if slug <= 1e-9:
                e12 = base + PURGE * (VUv + cap)
            elif conv == 'paused':
                e12 = base + PURGE * VUv + np.where(short, PURGE * cap, 0.0)
            else:
                e12 = base + PURGE * VUv + np.where(short, t_s + PURGE * cap, 0.0)
            o[conv] = {f'W{W:.2f}': float(np.mean(e12 > W)) for W in WS}
            o[conv]['E1_E2_max_s'] = float(e12.max())
        o['P_slug_too_short'] = float(np.mean(short)) if slug > 1e-9 else 1.0
        return o

    res = {}
    for case, hc in OP['heat_cases'].items():
        fam = hc['heat']['family']; qf, E = shapes[fam]
        Q_U, Q_R = hc['heat']['Q_U_J'] / E, hc['heat']['Q_route_J'] / E      # multipliers of the shape
        for sname, sv in MG['series'].items():
            Tw = sv['window_s']; t_dl = Tw - sv['t_from_drogue_load_s']
            runs = {}
            for wet in (True, False):
                tag = 'wet' if wet else 'dry'
                r = simulate(qf, Q_U, Q_R, Tw, t_dl, p, V_U, wet)
                r['ignition'] = ignite(r['V_U_cm3'], r['V_cap_cm3'], r['slug_cm3']); runs[f'S1_only|{tag}'] = r
                for t_open, lab in ((t_dl - 2.0, 'MV_at_deployment'), (t_dl, 'MV_at_drogue_load')):
                    for C in (0.725, 1.0):
                        r = simulate(qf, Q_U, Q_R, Tw, t_dl, p, V_U, wet, t_mv=t_open, D_mv=8e-3, C=C, fz_of_t=fz_series[sname])
                        r['MV_open_s'] = Tw - t_open
                        r['ignition'] = ignite(r['V_U_cm3'], r['V_cap_cm3'], r['slug_cm3']); runs[f'd_{lab}|C{C}|{tag}'] = r
                # no-U re-route research case (bore-leg trap only), S1 only and (d) at the drogue load
                r = simulate(qf, Q_U, Q_R, Tw, t_dl, p, V_bore, wet)
                r['ignition'] = ignite(r['V_U_cm3'], r['V_cap_cm3'], r['slug_cm3']); runs[f'noU_S1_only|{tag}'] = r
                for D in (8e-3, 10e-3, 12e-3, 16e-3):
                    r = simulate(qf, Q_U, Q_R, Tw, t_dl, p, V_bore, wet, t_mv=t_dl, D_mv=D, C=0.725, fz_of_t=fz_series[sname])
                    r['ignition'] = ignite(r['V_U_cm3'], r['V_cap_cm3'], r['slug_cm3']); runs[f'noU_d_D{D*1e3:.0f}mm|C0.725|{tag}'] = r
            res[f'{case}|{sname}'] = dict(window_s=Tw, t_drogue_load_s=t_dl, runs=runs)
        print(case, 'done', flush=True)
    # summary over series per case / option
    summ = {}
    for k, v in res.items():
        case = k.rsplit('|', 1)[0]
        for opt, r in v['runs'].items():
            s = summ.setdefault(f'{case}|{opt}', dict(V_U_cm3=[1e9, 0], V_cap_cm3=[1e9, 0], slug_cm3=[1e9, 0],
                                                       P_abort_W0p65_paused=[1, 0], P_abort_W0p65_restart=[1, 0],
                                                       P_abort_W1p05_paused=[1, 0], P_abort_W1p05_restart=[1, 0],
                                                       P_abort_W0p88_restart=[1, 0], E1_E2_max_restart_s=[9, 0]))
            for key, val in (('V_U_cm3', r['V_U_cm3']), ('V_cap_cm3', r['V_cap_cm3']), ('slug_cm3', r['slug_cm3']),
                             ('P_abort_W0p65_paused', r['ignition']['paused']['W0.65']), ('P_abort_W0p65_restart', r['ignition']['restart']['W0.65']),
                             ('P_abort_W1p05_paused', r['ignition']['paused']['W1.05']), ('P_abort_W1p05_restart', r['ignition']['restart']['W1.05']),
                             ('P_abort_W0p88_restart', r['ignition']['restart']['W0.88']), ('E1_E2_max_restart_s', r['ignition']['restart']['E1_E2_max_s'])):
                s[key] = [min(s[key][0], val), max(s[key][1], val)]
    E = pd.read_csv(env_f)
    env = dict(t_s=E.t_since_drogue_deploy_s.values.tolist()[::50], fz_seat_p01=E.fz_seat_p01_mps2.values.tolist()[::50])
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/segment_void_balance_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs=dict(vapour_order=sha16(os.path.join(d, 'relight_vapour_order_v2p4.json')), vapour_options=sha16(os.path.join(d, 'vapour_options_v2p4.json')),
                           coast_migration=sha16(os.path.join(d, 'coast_migration_v2p4.json')), mech_coast=dict(file=mc_f, sha256_16=sha16(mc_f)),
                           gnc_series=dict(file=series_f, sha256_16=sha16(series_f)), gnc_drogue_envelope=dict(file=env_f, sha256_16=sha16(env_f))),
               constants=dict(V_seg_cm3=V_SEG, V_U_cm3=V_U, V_bore_leg_cm3=V_bore, vap_cm3_per_J=p['vap_cm3_per_J'], liq_cm3_per_J=p['liq_cm3_per_J'],
                              purge_s_per_cm3=PURGE, liquid_dead_time_s_per_cm3=DEAD, dt_s=DT, D_MV_path_m=8e-3),
               cases=res, summary=summ, drogue_envelope_p01_decimated=env,
               tags=dict(model='DERIVED volume balance (Mechanical ESTIMATE heat, GNC SIM f_z, LITERATURE Wallis flooding as recalled, TO-VERIFY)',
                         ignition='SIM on ASSUMED delays; two conventions bracket the unknown ignition behaviour on a short liquid slug'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    for k, s in summ.items():
        print('%-58s VU %5.2f-%5.2f cap %5.2f-%5.2f slug %5.2f-%5.2f | P65 p %.3f-%.3f r %.3f-%.3f | P105 p %.4f-%.4f r %.4f-%.4f | P88r %.3f-%.3f | E12max r %.3f' % (
            k, *s['V_U_cm3'], *s['V_cap_cm3'], *s['slug_cm3'], *s['P_abort_W0p65_paused'], *s['P_abort_W0p65_restart'],
            *s['P_abort_W1p05_paused'], *s['P_abort_W1p05_restart'], *s['P_abort_W0p88_restart'], s['E1_E2_max_restart_s'][1]))
    print('wrote', out_f)


if __name__ == '__main__':
    main(*sys.argv[1:5])
