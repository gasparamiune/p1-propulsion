"""Retained vapour after the adopted coil re-route (option e): trap fill, route cap at S1, migration and the W 0.65 s light
(Combustion v2.4; coordinator relay 2026-10-13 "the retained-vapour decision changes your task", items 1-2).

Lead decision (CHANGELOG 2026-10-13): hose fixed end at the wall-line start, bore-crown low point >= 75 mm, flow-path
retained vapour <= 13.5 cm3 nominal / <= 19 cm3 at a 10 deg swing, MV closed through the coast, (d) dropped, (a) fallback.
Mechanical (segment_traps_v34 v1.1): V_above_flow_path(75 mm) = 13.533 cm3 (open filter element), dead ends above 75 mm
1.081 cm3 (V_above 14.614). These are v3.4 volumes above 75 mm; the re-routed CAD is not yet analysed (Mechanical re-run).

Configurations (trap = flow-path vapour that cannot reach S1 without going down):
  A  trap 13.533 cm3: the low point is the riser bottom / TEE; hose and both hose ends drain to the route side (this is what
     the 13.5 figure implies: the v3.4 volume above 75 mm holds the head, block and riser, not the hose).
  B  trap 19.0 cm3: the lead's 10 deg swing figure, same heat split as A.
  C  trap 22.0 cm3: sensitivity if the re-routed low point is the hose fixed end and the hose (9.2 cm3) rises to the TEE, i.e.
     the hose joins the trap (v3.4 flow path above the old saddle 22.01 cm3); heat split as the v3.4 U (vapour_options).
Heat (Mechanical segment_heat_budget_v1, per case, MECO -> RELIGHT, W(t) histories, not uniform):
  head end = Q_head_end_W(t) (FE manifold bore + FD-01 + TC-02 + TC-04) -> trap;
  needle 50 / 150 J (ESTIMATE, no history) -> trap, exp(-t/2 s) (ASSUMED);
  riser FD-03 -> trap; TEE FD-05 0.5 / 0.5 (A, B) or trap (C); hose and hose ends -> route (A, B) or trap / 0.5 (C);
  module, wall line, union -> route.  Histories beyond 18.5 s: linear extrapolation of the last 5 points, clipped >= 0.
Volume balance (same as segment_void_balance_v2p4.simulate, dt 10 ms, the five GNC coast series):
  coast-up (to the drogue load, f_z <= 0.5 g): bubbles stay where they form; S1 vents liquid (void grows 0.0388 cm3/J).
  trap fills first (dead ends first, they are at the top); a full trap overflows past the saddle ('wet') or stops boiling
  ('dry': the hot head walls are above the liquid front);
  after the drogue load route bubbles reach the top: S1 vents only the expansion e = (v_g - v_l)/h_fg q_evap; the cap at the
  module top grows by v_l/h_fg = 0.0067 cm3/J.  MV-early variants (evidence only; (d) is dropped): Wallis counter-current
  exchange through an 8 mm MV path at C 0.725 from Tw - 1 s, Tw - 3 s and the drogue load.
Ignition (same 200 000-sample E1 -> E2 distribution, seed 2024; 'paused' and 'restart' conventions) with flow order
[trap vapour (flow-path part)][liquid slug][cap][tank liquid].
Migration: Taylor-bubble drift (relight_vapour_order_v2p4.drift) along the wall line (0.296 m, 7.75 mm, ASSUMED axial) on each
GNC f_z series: arrival time at S1 and the in-transit volume at the relight command.
usage: python -I reroute_vapour_v2p4.py DATA_V2P4_DIR BUDGET_JSON TRAPS_JSON SERIES_CSV OUT_JSON
"""
from __future__ import annotations
import json, math, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import start_latency_v2p4 as SL
import relight_vapour_order_v2p4 as RV
import segment_void_balance_v2p4 as SV

V_SEG = 44.0
WS = (0.65, 0.76, 0.85, 0.88, 0.93, 1.05)
DT = 0.01
TAU_NEEDLE = 2.0
L_WALL = 0.29644
D_WALL = 7.747e-3
N_MOD = 'MV/FS-01 module, outlet side (316L body)'
N_WALL = 'fixed wall line 3/8 x 0.035 316L, module -> coil (~250 mm)'
N_UNION = 'line-coil union / 90 deg elbow (316)'
N_ENDS = 'coil hose ends 2x -6 JIC swivel + nipple (316)'
N_HOSE = 'coil hose O3b 0.252 m, PTFE liner 1.0 + SS braid 0.5 (equivalent)'
N_TEE = 'FD-05 TEE + MSS-1 port (316L)'
N_RISER = 'FD-03 riser 3/8 x 0.035 316L (~130 mm)'
SPLIT = {'A': dict(trap={N_RISER: 1.0, N_TEE: 0.5}, route={N_MOD: 1.0, N_WALL: 1.0, N_UNION: 1.0, N_ENDS: 1.0, N_HOSE: 1.0, N_TEE: 0.5}),
         'C': dict(trap={N_RISER: 1.0, N_TEE: 1.0, N_HOSE: 1.0, N_ENDS: 0.5}, route={N_MOD: 1.0, N_WALL: 1.0, N_UNION: 1.0, N_ENDS: 0.5})}
SPLIT['B'] = SPLIT['A']


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def series_fn(t_rel, q):
    t_rel = np.asarray(t_rel, float); q = np.clip(np.asarray(q, float), 0.0, None); kf = np.polyfit(t_rel[-5:], q[-5:], 1)
    def f(t):
        return float(np.interp(t, t_rel, q)) if t <= t_rel[-1] else max(float(np.polyval(kf, t)), 0.0)
    return f


def simulate(qT, qR, Tw, t_dl, p, cap_T, wet, t_mv=None, D_mv=8e-3, C=0.725, fz_of_t=None, rec=False):
    """Trap volume VU (fill capacity cap_T incl. dead ends), route cap at S1, slug; same logic as SV.simulate with separate
    trap / route heat histories."""
    vpj, lpj = p['vap_cm3_per_J'], p['liq_cm3_per_J']
    VU = 0.0; Rb = 0.0; cap = 0.0; t_full = None; cap_max = 0.0; over_tot = 0.0; vent_liq = 0.0
    hist = []
    n = int(round(Tw / DT))
    for k in range(n):
        t = (k + 0.5) * DT
        qU = qT(t); qr = qR(t)
        if t < t_dl:
            dV = vpj * qU * DT; room = cap_T - VU
            if dV <= room:
                VU += dV
            else:
                VU = cap_T; Rb += (dV - room) if wet else 0.0; over_tot += (dV - room) if wet else 0.0
                t_full = t_full if t_full is not None else t
            Rb += vpj * qr * DT
            if VU + Rb >= V_SEG:
                Rb = V_SEG - VU
            if rec and k % 50 == 0:
                hist.append((round(t, 2), round(VU, 3), round(Rb, 3)))
            continue
        if Rb > 0:
            cap += Rb; Rb = 0.0
        if VU < cap_T:
            dV = vpj * qU * DT; room = cap_T - VU
            if dV <= room:
                VU += dV; over = 0.0; q_ev = qU + qr
            else:
                VU = cap_T; frac = room / dV; over = (dV - room) if wet else 0.0
                q_ev = qr + qU * (1.0 if wet else frac)
                t_full = t_full if t_full is not None else t
        else:
            over = vpj * qU * DT if wet else 0.0
            q_ev = qr + (qU if wet else 0.0)
        over_tot += over
        A = vpj * qr * DT + over
        e = (vpj - lpj) * q_ev
        mv_open = t_mv is not None and t >= t_mv
        fz = fz_of_t(t) if (mv_open and fz_of_t is not None) else 0.0
        if (not mv_open) or (A + cap <= e * DT):
            Xmax = e
        else:
            Xmax = SV.wallis_xmax(e, fz, D_mv, p, C)
        X = min(A + cap, Xmax * DT)
        if A + cap < e * DT:
            vent_liq += e * DT - (A + cap)
        cap = cap + A - X
        if VU + cap > V_SEG:
            cap = V_SEG - VU
        cap_max = max(cap_max, cap)
        if rec and k % 50 == 0:
            hist.append((round(t, 2), round(VU, 3), round(cap, 3)))
    gen_T_end = vpj * qT(Tw)
    out = dict(V_trap_cm3=VU, V_cap_cm3=max(cap, 0.0), slug_cm3=max(V_SEG - VU - cap, 0.0), t_trap_full_s=t_full, cap_max_cm3=cap_max,
               overflow_past_saddle_cm3=over_tot, trap_generation_at_relight_cm3_s=gen_T_end,
               q_trap_at_relight_W=qT(Tw), q_route_at_relight_W=qR(Tw))
    if rec:
        out['history_t_trap_capOrBubbles'] = hist
    return out


def main(d, budget_f, traps_f, series_f, out_f):
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    MG = json.load(open(os.path.join(d, 'coast_migration_v2p4.json')))
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    PA = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
    B = json.load(open(budget_f)); TR = json.load(open(traps_f))
    p = VO['properties']; vpj, lpj = p['vap_cm3_per_J'], p['liq_cm3_per_J']
    PURGE = VO['purge_s_per_cm3']; DEAD = VO['liquid_plug_dead_time_s_per_cm3']
    vz = {r['z_mm']: r for r in TR['V_of_z_open_element_retained']}
    V75, V75p = vz[75.0]['V_above_cm3'], vz[75.0]['V_above_flow_path_cm3']
    V_dead = round(V75 - V75p, 3)
    assert abs(V75p - 13.533) < 1e-9 and abs(V_dead - 1.081) < 1e-9, 'trap file differs from the lead basis'
    TRAPS = {'A': V75p, 'B': 19.0, 'C': 22.0}
    t_meco = float(B['t_meco_s']); T_m = float(B['coast_s'])
    el = {e['name']: e for e in B['elements']}
    HE = B['head_end_W_vs_t']['v']
    trap_int = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')
    heat = {}
    checks = {}
    for case in HE:
        fam = case.split('|')[1]
        th = np.array(HE[case]['t_s']) - t_meco
        f_head = series_fn(th, HE[case]['Q_head_end_W'])
        E_head = float(trap_int(np.clip(HE[case]['Q_head_end_W'], 0, None), th))
        E_head_budget = B['totals'][case]['head_end_J'] - B['totals'][case]['head_end_split_J']['needle (ESTIMATE)']
        checks[case] = dict(E_head_series_J=E_head, E_head_budget_less_needle_J=E_head_budget)
        assert abs(E_head / E_head_budget - 1) < 0.05, (case, E_head, E_head_budget)
        E_n = B['needle']['E_J'][0 if fam == 'LO' else 1]
        a_n = E_n / (TAU_NEEDLE * (1 - math.exp(-T_m / TAU_NEEDLE)))
        f_needle = (lambda t, a=a_n: a * math.exp(-t / TAU_NEEDLE))
        f_el = {}
        for nm in (N_MOD, N_WALL, N_UNION, N_ENDS, N_HOSE, N_TEE, N_RISER):
            e = el[nm]; te = np.array(e['Q_coast_t_s']) - t_meco
            f_el[nm] = series_fn(te, e['Q_coast_W'][case])
            Ei = float(trap_int(np.clip(e['Q_coast_W'][case], 0, None), te))
            assert abs(Ei - e['E_coast_J'][case]) < 0.03 * e['E_coast_J'][case] + 1.0, (nm, case, Ei, e['E_coast_J'][case])
        heat[case] = dict(fam=fam, head=f_head, needle=f_needle, el=f_el, E_needle=E_n)

    def q_funcs(case, cfg):
        h = heat[case]; sp = SPLIT[cfg]
        def qT(t):
            return h['head'](t) + h['needle'](t) + sum(w * h['el'][n](t) for n, w in sp['trap'].items())
        def qR(t):
            return sum(w * h['el'][n](t) for n, w in sp['route'].items())
        return qT, qR

    S = pd.read_csv(series_f)
    fz_series, migr = {}, {}
    for name, g in S.groupby('series'):
        g = g[g.t_minus_relight_cmd_s <= 1e-9].sort_values('t_s')
        tt = g.t_s.values - g.t_s.values[0]; fz = g.fz_mv_mps2.values
        fz_series[name] = (lambda t, tt=tt, fz=fz: float(np.interp(t, tt, fz)))
        sv = MG['series'][name]; Tw = sv['window_s']; t_dl = Tw - sv['t_from_drogue_load_s']
        assert abs(tt[-1] - Tw) < 0.02, (name, tt[-1], Tw)
        # wall-line transit: bubble released at the low point at time t0 (>= drogue load), arrival at S1
        u = np.array([math.copysign(RV.drift(D_WALL, abs(f), p)[0], f) if f != 0 else 0.0 for f in fz])
        dtt = np.diff(tt, prepend=tt[0]); x = np.cumsum(u * dtt)
        def arrive(t0):
            i0 = int(np.searchsorted(tt, t0)); target = x[i0] + L_WALL
            j = np.where(x[i0:] >= target)[0]
            return float(tt[i0 + j[0]] - t0) if len(j) else None
        tr_dl = arrive(t_dl)
        # latest release time that still reaches S1 by the relight command
        lo_, hi_ = t_dl, Tw
        for _ in range(40):
            m = 0.5 * (lo_ + hi_)
            a = arrive(m)
            if a is not None and m + a <= Tw:
                lo_ = m
            else:
                hi_ = m
        migr[name] = dict(window_s=Tw, t_drogue_load_s=t_dl, transit_from_drogue_load_s=tr_dl, latest_release_reaching_S1_s=lo_,
                          last_interval_in_transit_s=Tw - lo_, u_drift_last_1s_mean_mps=float(np.mean(u[tt > Tw - 1.0])))
    # ---------------------------------------------------------------- ignition distribution (as SV / post_abort_pocket)
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
    need = base - t_lift

    def single(V):
        e12 = base + PURGE * V
        return {**{f'W{W:.2f}': float(np.mean(e12 > W)) for W in WS}, 'E1_E2_max_s': float(e12.max()), 'E1_E2_p99_s': float(np.quantile(e12, 0.99))}

    def ignite(VUv, cap, slug):
        Vp = max(VUv - V_dead, 0.0)
        o = {}
        t_s = slug * DEAD
        short = need > t_s
        for conv in ('paused', 'restart'):
            if slug <= 1e-9:
                e12 = base + PURGE * (Vp + cap)
            elif conv == 'paused':
                e12 = base + PURGE * Vp + np.where(short, PURGE * cap, 0.0)
            else:
                e12 = base + PURGE * Vp + np.where(short, t_s + PURGE * cap, 0.0)
            o[conv] = {f'W{W:.2f}': float(np.mean(e12 > W)) for W in WS}
            o[conv]['E1_E2_max_s'] = float(e12.max())
        o['P_slug_too_short'] = float(np.mean(short)) if slug > 1e-9 else 1.0
        o['purge_volume_cm3'] = Vp
        return o

    single_tab = {f'{V:.3f}': single(V) for V in sorted(set([10.0, 12.0, 13.533, 14.0, 16.0, 18.0, 18.5, 18.86, 19.0, 19.5, 20.0, 22.0, 24.0, 26.0, 30.0]))}
    Vzero = (0.65 - float(base.max())) / PURGE
    need_q = {f'q{q}': float(np.quantile(need, q)) for q in (0.5, 0.99, 0.999, 1.0)}
    slug_for_q = {k: v / DEAD for k, v in need_q.items()}
    res = {}
    for case in HE:
        for cfg in ('A', 'B', 'C'):
            qT, qR = q_funcs(case, cfg)
            capT = TRAPS[cfg] + V_dead
            for sname, sv in MG['series'].items():
                Tw = sv['window_s']; t_dl = Tw - sv['t_from_drogue_load_s']
                runs = {}
                for wet in (True, False):
                    tag = 'wet' if wet else 'dry'
                    r = simulate(qT, qR, Tw, t_dl, p, capT, wet, rec=(sname == 'nominal'))
                    r['ignition'] = ignite(r['V_trap_cm3'], r['V_cap_cm3'], r['slug_cm3']); runs[f'S1_only|{tag}'] = r
                    for lab, t_open in (('MV_open_Tw-1s', Tw - 1.0), ('MV_open_Tw-3s', Tw - 3.0), ('MV_open_drogue_load', t_dl)):
                        r = simulate(qT, qR, Tw, t_dl, p, capT, wet, t_mv=t_open, fz_of_t=fz_series[sname])
                        r['ignition'] = ignite(r['V_trap_cm3'], r['V_cap_cm3'], r['slug_cm3']); runs[f'evidence_{lab}|{tag}'] = r
                res[f'{case}|{cfg}|{sname}'] = dict(window_s=Tw, t_drogue_load_s=t_dl, runs=runs)
            print(case, cfg, 'done', flush=True)
    summ = {}
    for k, v in res.items():
        key0 = k.rsplit('|', 1)[0]
        for opt, r in v['runs'].items():
            s = summ.setdefault(f'{key0}|{opt}', {})
            vals = dict(V_trap_cm3=r['V_trap_cm3'], V_cap_cm3=r['V_cap_cm3'], slug_cm3=r['slug_cm3'],
                        t_trap_full_s=(r['t_trap_full_s'] if r['t_trap_full_s'] is not None else float('nan')),
                        trap_gen_at_relight_cm3_s=r['trap_generation_at_relight_cm3_s'], overflow_cm3=r['overflow_past_saddle_cm3'],
                        P_short=r['ignition']['P_slug_too_short'],
                        P65_paused=r['ignition']['paused']['W0.65'], P65_restart=r['ignition']['restart']['W0.65'],
                        P88_restart=r['ignition']['restart']['W0.88'], P105_restart=r['ignition']['restart']['W1.05'],
                        E12max_restart=r['ignition']['restart']['E1_E2_max_s'])
            for kk, val in vals.items():
                if kk not in s:
                    s[kk] = [val, val]
                else:
                    s[kk] = [min(s[kk][0], val), max(s[kk][1], val)]
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/reroute_vapour_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs=dict(vapour_order=sha16(os.path.join(d, 'relight_vapour_order_v2p4.json')), coast_migration=sha16(os.path.join(d, 'coast_migration_v2p4.json')),
                           start_latency=sha16(os.path.join(d, 'start_latency_v2p4.json')), post_abort_pocket=sha16(os.path.join(d, 'post_abort_pocket_v2p4.json')),
                           mech_budget=dict(file=budget_f, sha256_16=sha16(budget_f)), mech_traps=dict(file=traps_f, sha256_16=sha16(traps_f)),
                           gnc_series=dict(file=series_f, sha256_16=sha16(series_f))),
               constants=dict(V_seg_cm3=V_SEG, traps_flow_path_cm3=TRAPS, V_dead_end_above_75mm_cm3=V_dead, vap_cm3_per_J=vpj, liq_cm3_per_J=lpj,
                              purge_s_per_cm3=PURGE, liquid_dead_time_s_per_cm3=DEAD, dt_s=DT, tau_needle_s=TAU_NEEDLE, L_wall_m=L_WALL, D_wall_m=D_WALL,
                              heat_split=SPLIT),
               heat_checks=checks,
               single_pocket=dict(table=single_tab, V_max_zero_abort_W0p65_cm3=Vzero, E1_E2_liquid_max_s=float(base.max()),
                                  liquid_need_s=need_q, slug_needed_cm3=slug_for_q),
               migration=migr, cases=res, summary=summ,
               tags=dict(model='DERIVED volume balance (Mechanical ESTIMATE heat histories, Mechanical DERIVED trap volumes on CAD v3.4, GNC SIM f_z, '
                               'LITERATURE drift / Wallis forms as recalled, TO-VERIFY)',
                         ignition='SIM on ASSUMED delays; two conventions bracket the unknown behaviour of a short liquid slug',
                         status='trap volumes are v3.4 volumes above 75 mm, not the re-routed CAD (Mechanical re-run pending)'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print('single pocket:', {k: (round(v['W0.65'], 5), round(v['E1_E2_max_s'], 3)) for k, v in single_tab.items()})
    print('V zero-abort at W0.65: %.2f cm3; need quantiles' % Vzero, need_q, 'slug needed', slug_for_q)
    for k, v in migr.items():
        print('migration', k, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()})
    for k, s in summ.items():
        if 'evidence' in k and 'drogue' not in k and 'Tw-3s' not in k:
            continue
        print('%-52s trap %5.2f-%5.2f full %5.2f-%5.2f gen %5.2f-%5.2f cap %5.2f-%5.2f slug %5.2f-%5.2f | Pshort %.3f-%.3f | P65 p %.4f-%.4f r %.4f-%.4f | P88r %.4f-%.4f | P105r %.4f-%.4f | E12max %.3f' % (
            k, *s['V_trap_cm3'], *s['t_trap_full_s'], *s['trap_gen_at_relight_cm3_s'], *s['V_cap_cm3'], *s['slug_cm3'], *s['P_short'],
            *s['P65_paused'], *s['P65_restart'], *s['P88_restart'], *s['P105_restart'], s['E12max_restart'][1]))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:6])
