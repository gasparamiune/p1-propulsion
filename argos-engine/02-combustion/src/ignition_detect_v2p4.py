"""Light detection at the v2.8 ignition lift: earliest light after the lift, lit and unlit chamber pressure, the rise
between them, and the other Pc thresholds Combustion set when the ignition flow was about 52 g/s
(Combustion v2.4, 2026-10-13; coordinator priority item after Electronics' ignition_detect_margin_v1, lead decision
"relative light detection").

Parts (all SIM or DERIVED on ASSUMED inputs unless stated):
  A  earliest light after E1 (pintle command to the ignition lift) for a liquid start, a vapour-slug start and a
     post-purge start, from the start_latency_v2p4 constants and the purge_sizing_v2p4 pockets.
  B  lit Pc while the pintle holds the v2.8 ignition lift (0.2039 mm), grain_q1d v2 (same plant as start_latency_v2p4):
     regression law a x0.6-1.5, n 0.35-0.68, eta_c* 0.85/0.92, preheated fraction at main ignition 0 (fuel from zero,
     as Electronics' SIL plant), 0.15, 0.3, 0.6; states A1 relight (286.7 K, port 32.2 mm), pad 15/20/24 C; flow per
     the plant at Cd 0.70 and +/-7 % (Cd 0.65/0.75). Pc sampled from main ignition.
  C  fuel-free lit bound: mox x eta_c* x c*(Pc, O/F 14)/A_t (the O/F clamp of both plants; CEA table).
  D  unlit (cold-flow) Pc: all N2O evaporated to gas at 190-600 K leaving through the throat (Cd 0.98, subsonic or
     choked, no diffuser recovery: an upper bound); Electronics' SIL cold model (c* 400 m/s with its choke factor)
     reproduced for comparison.
  E  stuck-open head-end bleed during the light: the bleed sits upstream of the seat, in parallel with the pintle;
     with the MV open the bleed flow comes from the tank and only adds feed-line loss (dp_line 2.5 bar at 0.25 kg/s,
     ASSUMED, grain_q1d).
  F  A3 flame-out (Pc < 0.5 x Pc_map(lift) for 20 ms after E2) and A5 (Pc > 8.0 bar abs for 5 ms at the ignition lift):
     hold at the lift, E2 by the old absolute rule or by a relative rule, then the 2500 N/s ramp to 100 or 200 N; the
     ECU map is the nominal law (a x1.0, n 0.5, eta 0.92), the plant is dispersed.
  G  drogue release on Pc >= 50 % of the floor Pc (gnc.json), at the 20 % baseline floor and the 12.5 % stretch floor.
  H  hard-start inventory margin for a higher ignition lift (option C), from relight_window_rule_seg44_v2p4.json.
usage: python -I ignition_detect_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import hashlib, itertools, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
from tank import EquilibriumTank
import start_latency_v2p4 as SL

H_V28 = 0.2039e-3
PA = 101325.0
STATES = dict(SL.STATES)
STATES['pad_24C'] = dict(T=297.15, m=2.0, D=0.025, tag='pad start, tank 24 C (ARM/START interlock)')
RESIDUAL = (0.0, 0.3e5, 0.6e5)       # post-zero residual of the Pc channel: 0, B-PC-1 target, Electronics' present band


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def engine(state, cfg=None):
    s = STATES[state]
    e = Q.Engine(EquilibriumTank(3.17e-3, s['m'], s['T']), cfg)
    e.D[:] = s['D']
    return e


def hold_run(state, Cd, af, n, ri, eta, t_end=0.40, dt=5e-4):
    cfg = dict(SL.law(n, af)); cfg.update(r_ign_frac=ri, eta_cstar=eta, Cd=Cd, t_open_delay=0.0, h_rate=SL.V_PINTLE)
    e = engine(state, cfg)
    e.h = e.h_cmd = e.h_target = H_V28; e.state = 'start'; e.t_on = 0.0; e.Pc = 1.1e5; e.F = 0.0
    if ri <= 0.0:
        e.r_eff[:] = 1e-12               # fuel from zero (SIL convention); grain_q1d otherwise seeds r_ign x r_qs
    ts, Ps, OFs, mo = [], [], [], []
    t = 0.0
    while t < t_end - 1e-12:
        e.t = t; e.step(dt); t += dt
        ts.append(t); Ps.append(e.Pc); OFs.append(e.OF); mo.append(e.mox)
    ts = np.array(ts); Ps = np.array(Ps)
    at = lambda tt: float(np.interp(tt, ts, Ps))
    w = (ts >= 0.030)
    return dict(state=state, Cd=Cd, a_fac=af, n=n, r_ign=ri, eta=eta, mox_g_s=1e3 * float(np.mean(mo[-20:])),
                Pc_bar={f'+{int(round(1e3 * tt))}ms': at(tt) / 1e5 for tt in (0.010, 0.020, 0.030, 0.050, 0.100, 0.200, 0.300, 0.400)},
                Pc_min_30_400ms_bar=float(Ps[w].min()) / 1e5, Pc_max_0_400ms_bar=float(Ps.max()) / 1e5,
                OF_at_30ms=float(np.interp(0.030, ts, OFs)), OF_at_400ms=float(OFs[-1]))


def ramp_run(state, af, n, ri, eta, F_cmd, rule, thr, dt=5e-4, t_max=1.2):
    """Light at t = 0 at the ignition lift; E2 by rule ('abs': measured Pc >= thr; 'rel': measured Pc >= PA + thr) for
    10 ms with 2.3 ms latency; ramp released 20 ms later at 2500 N/s to F_cmd on the nominal-law map lift (feed-forward,
    as start_latency_v2p4 with loop_K 0). Returns the minimum Pc/Pc_map(h) from E2 to E2 + 0.6 s and the max Pc in the hold."""
    cfg = dict(SL.law(n, af)); cfg.update(r_ign_frac=ri, eta_cstar=eta, t_open_delay=0.0, h_rate=SL.V_PINTLE)
    e = engine(state, cfg)
    m = engine(state)                                  # ECU map: nominal law, eta 0.92
    e.h = e.h_cmd = e.h_target = H_V28; e.state = 'start'; e.t_on = 0.0; e.Pc = 1.1e5; e.F = 0.0
    if ri <= 0.0:
        e.r_eff[:] = 1e-12
    k_lat = int(round(SL.PC_LAT / dt)); hist = []
    t = 0.0; above = None; t_conf = None; t_rs = None; F_rs = None; next_ctrl = 0.0; cei = None
    ratio_min = {r: 9.9 for r in RESIDUAL}; Pc_hold_max = 0.0; map_cache = (None, None)
    unlit_ratio_max = dict(gas600K=0.0, SIL=0.0); rel_min = 9.9; rel_unlit_max = dict(gas600K=0.0, SIL=0.0)
    while t < t_max:
        if t_conf is None and t > 0.65:
            break
        e.t = t
        Pm = hist[-1 - k_lat] if len(hist) > k_lat else 1.1e5
        if t_conf is None:
            ok = (Pm >= thr) if rule == 'abs' else (Pm >= PA + thr)
            if ok:
                above = t if above is None else above
                if t - above >= SL.T_PERSIST:
                    t_conf = t; t_rs = t + SL.T_SOL1
            else:
                above = None
            Pc_hold_max = max(Pc_hold_max, e.Pc)
        if t_rs is not None and t >= t_rs and t >= next_ctrl - 1e-12:
            if F_rs is None:
                F_rs = e.F
            Fc = min(F_cmd, F_rs + 2500.0 * (t - t_rs))
            if cei is None:
                cei = m.ceiling()
            hff, _ = m.lift_for_thrust(Fc, h_guess=e.h_target if e.h_target > 0 else None, cei=cei)
            e.h_target = min(hff, cei['h'])
            next_ctrl = t + 0.010
        if t_conf is not None and t <= t_conf + 0.6 and (len(hist) % 20 == 0):
            hk = round(e.h, 7)
            if map_cache[0] != hk:
                s = m.steady(max(e.h, 1e-6)); map_cache = (hk, s['Pc'] if s else None)
            if map_cache[1]:
                for r in RESIDUAL:
                    ratio_min[r] = min(ratio_min[r], (e.Pc - r) / map_cache[1])
                rel_min = min(rel_min, (e.Pc - PA) / (map_cache[1] - PA))
                if e.mox > 1e-4:
                    ug, us = unlit_gas(e.mox, 600.0)[0], unlit_sil(e.mox)
                    unlit_ratio_max['gas600K'] = max(unlit_ratio_max['gas600K'], ug / map_cache[1])
                    unlit_ratio_max['SIL'] = max(unlit_ratio_max['SIL'], us / map_cache[1])
                    rel_unlit_max['gas600K'] = max(rel_unlit_max['gas600K'], (ug - PA) / (map_cache[1] - PA))
                    rel_unlit_max['SIL'] = max(rel_unlit_max['SIL'], (us - PA) / (map_cache[1] - PA))
        e.step(dt); hist.append(e.Pc); t += dt
        if t_conf is not None and t > t_conf + 0.6:
            break
    return dict(state=state, a_fac=af, n=n, r_ign=ri, eta=eta, F_cmd=F_cmd, rule=rule, thr=thr, t_conf_s=t_conf,
                Pc_hold_max_bar=Pc_hold_max / 1e5, ratio_min={f'residual_{r/1e5:.1f}bar': v for r, v in ratio_min.items()},
                unlit_ratio_max=unlit_ratio_max, relative_ratio_min=rel_min, relative_unlit_ratio_max=rel_unlit_max)


def fuel_free(e, mox, eta):
    Pc = 3e5
    for _ in range(50):
        Pn = mox * eta * Q.perf().cstar(Pc, 14.0) / e.At
        if abs(Pn - Pc) < 1.0:
            break
        Pc = Pn
    return Pc


def unlit_gas(mdot, T, Pa=PA, Cd_t=0.98, At=None):
    R = 8.314462 / 0.0440128
    At = At or math.pi / 4 * 0.013724 ** 2
    g = 1.27
    Gam = Q.Gamma(g)
    Pc_ch = mdot * math.sqrt(R * T) / (Gam * Cd_t * At)
    crit = ((g + 1) / 2) ** (g / (g - 1))
    if Pc_ch / Pa >= crit:
        return Pc_ch, 'choked'
    Pc = Pa + 1e4
    for _ in range(100):
        rho = Pc / (R * T)
        Pn = Pa + mdot ** 2 / (2 * rho * (Cd_t * At) ** 2)
        if abs(Pn - Pc) < 0.1:
            break
        Pc = 0.5 * (Pc + Pn)
    return Pc, 'subsonic'


def unlit_sil(mdot, cs=400.0, At=None):
    At = At or math.pi / 4 * 0.013724 ** 2
    lo, hi = PA, 20e5
    for _ in range(80):
        x = 0.5 * (lo + hi)
        mout = x * At / cs * min(1.0, math.sqrt(max(0.0, (x - PA) / (0.9 * PA))))
        if mout > mdot:
            hi = x
        else:
            lo = x
    return 0.5 * (lo + hi)


def main(d, out_f):
    SLJ = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    PS = json.load(open(os.path.join(d, 'purge_sizing_v2p4.json')))
    RW = json.load(open(os.path.join(d, 'relight_window_rule_seg44_v2p4.json')))
    PURGE = VO['purge_s_per_cm3']
    # ---------------- A: earliest light after E1 ----------------
    t_crack = SL.T_CMD + 0.010 * 0.0
    t_lift = SL.T_CMD + H_V28 / SL.V_PINTLE + 0.010
    ig_min = 0.05
    # post-purge pocket at the lift for purges that give P_abort 0 at every longer grid time (0.8 mm >= 1.5 s, 0.6 mm >= 2.5 s; config A)
    def pk(end):
        v = 0.0
        for k, s_ in PS['summary'].items():
            orif, case, cfg, tag, tp, e_ = k.split('|')[0], '|'.join(k.split('|')[1:3]), k.split('|')[3], k.split('|')[4], float(k.split('|')[5][2:]), k.split('|')[6]
            if cfg == 'A' and e_ == end and ((orif == '0.8' and tp >= 1.5) or (orif == '0.6' and tp >= 2.5)):
                v = max(v, s_['pocket'][1])
        return v
    pockets = dict(post_purge_end_at_lift=float(pk('lift')), post_purge_end_at_E0=float(pk('E0')),
                   annulus=PS['constants']['V_annulus_cm3'], zero_abort_limit=18.859)
    A = dict(t_command_to_motion_s=SL.T_CMD, t_lift_reached_s=t_lift, ignition_delay_min_s=ig_min,
             liquid_start=dict(earliest_light_s=t_lift + ig_min,
                               note='N2O enters the chamber as the pintle cracks (seat at the injector exit); light >= lift reached + 0.05 s (lower end of the ASSUMED U(0.05, 0.30) s band)'),
             vapour_slug_start={f'{k}_{v:.2f}cm3': dict(liquid_at_chamber_s=t_lift + PURGE * v, earliest_liquid_light_s=t_lift + PURGE * v + ig_min,
                                                          earliest_light_if_vapour_lights_s=t_lift + ig_min)
                                for k, v in (('annulus', pockets['annulus']), ('post_purge_end_at_lift', pockets['post_purge_end_at_lift']),
                                             ('post_purge_end_at_E0', pockets['post_purge_end_at_E0']), ('zero_abort_limit', pockets['zero_abort_limit']))},
             purge_s_per_cm3=PURGE,
             bound_for_all_starts_s=t_lift + ig_min,
             SIL_S5_light_after_lift_s=[0.126, 0.152],
             tag='DERIVED on ASSUMED delays (start_latency_v2p4 constants; ignition delay U(0.05, 0.30) s ASSUMED, review band)')
    # ---------------- B: lit band at the v2.8 lift ----------------
    grid = []
    for st in STATES:
        grid += [(st, 0.65, 0.6, 0.68, 0.0, 0.85),            # low corner: low flow, slow law, fuel from zero, low eta
                 (st, 0.70, 1.0, 0.5, 0.3, 0.92),             # nominal
                 (st, 0.75, 1.5, 0.35, 0.6, 0.92)]            # high corner (A5)
    grid += [('A1_relight', 0.70, 1.0, 0.5, ri, 0.92) for ri in (0.0, 0.15, 0.6)]
    grid += [('A1_relight', 0.70, 0.6, 0.68, ri, 0.85) for ri in (0.15, 0.3)]
    fgrid = [(st, af, n, ri, eta, Fc, rule, thr) for (st, af, n, ri, eta) in (('A1_relight', 0.6, 0.68, 0.0, 0.85), ('A1_relight', 1.0, 0.5, 0.3, 0.92),
                                                                               ('A1_relight', 0.6, 0.68, 0.3, 0.85), ('pad_20C', 0.6, 0.68, 0.0, 0.85),
                                                                               ('pad_20C', 1.0, 0.5, 0.3, 0.92))
             for Fc in (100.0, 200.0) for rule, thr in (('abs', 3.0e5), ('rel', 0.8e5))]
    from multiprocessing import Pool
    with Pool(2) as pool:
        ra = pool.starmap_async(hold_run, grid)
        rb = pool.starmap_async(ramp_run, fgrid)
        runs = ra.get(); Fr = rb.get()
    B = {}
    for st in STATES:
        for ri in (0.0, 0.15, 0.3, 0.6):
            rs = [r for r in runs if r['state'] == st and r['r_ign'] == ri]
            if not rs:
                continue
            B[f'{st}|r_ign{ri}|n{len(rs)}'] = dict(mox_g_s=[min(r['mox_g_s'] for r in rs), max(r['mox_g_s'] for r in rs)],
                                         Pc30_bar=[min(r['Pc_bar']['+30ms'] for r in rs), max(r['Pc_bar']['+30ms'] for r in rs)],
                                         Pc_min_30_400_bar=[min(r['Pc_min_30_400ms_bar'] for r in rs), max(r['Pc_min_30_400ms_bar'] for r in rs)],
                                         Pc400_bar=[min(r['Pc_bar']['+400ms'] for r in rs), max(r['Pc_bar']['+400ms'] for r in rs)],
                                         Pc_max_bar=max(r['Pc_max_0_400ms_bar'] for r in rs),
                                         Pc_per_mox_30ms_bar_per_g_s=min(r['Pc_bar']['+30ms'] / r['mox_g_s'] for r in rs))
    # ---------------- C: fuel-free bound ----------------
    C = {}
    for st in STATES:
        e = engine(st)
        for Cd in (0.65, 0.70, 0.75):
            e2 = engine(st, dict(Cd=Cd)); mox, _ = e2.mox_inj(H_V28, 2.6e5)
            for eta in (0.85, 0.92):
                C[f'{st}|Cd{Cd}|eta{eta}'] = dict(mox_g_s=1e3 * mox, Pc_bar=fuel_free(e2, mox, eta) / 1e5)
    for lab, mox in (('SIL_A1_35.0', 0.0350), ('SIL_pad_37.1', 0.0371), ('cap_A1_37.4', 0.0374)):
        e = engine('A1_relight')
        for eta in (0.85, 0.92):
            C[f'{lab}|eta{eta}'] = dict(mox_g_s=1e3 * mox, Pc_bar=fuel_free(e, mox, eta) / 1e5)
    # ---------------- D: unlit ----------------
    D = {}
    for lab, mox in (('29.0', 0.029), ('35.0', 0.035), ('37.1', 0.0371), ('37.4', 0.0374), ('42.0', 0.042)):
        row = {}
        for T in (190.0, 290.0, 450.0, 600.0):
            p, reg = unlit_gas(mox, T)
            row[f'gas_{int(T)}K'] = dict(Pc_bar=p / 1e5, rise_bar=(p - PA) / 1e5, regime=reg)
        p = unlit_sil(mox); row['SIL_cold_cstar400'] = dict(Pc_bar=p / 1e5, rise_bar=(p - PA) / 1e5)
        D[f'mox_{lab}_g_s'] = row
    vap_frac = 15450.0 / 56843.0
    D['vapour_slug_flow'] = dict(mass_flow_ratio_vapour_to_liquid=vap_frac,
                                 Pc_bar_at_37p1_liquid_equivalent=unlit_gas(0.0371 * vap_frac, 290.0)[0] / 1e5,
                                 note='HEM vapour 15 450 vs Dyer liquid 56 843 kg/m2s through the same lift (vapour_options_v2p4)')
    # ---------------- E: stuck-open bleed ----------------
    E = {}
    for st in ('A1_relight', 'pad_20C'):
        e = engine(st)
        m0, P10 = e.mox_inj(H_V28, 2.6e5)
        for lab, mb in (('0.6mm_vapour', 3.058e-3), ('0.8mm_vapour', 5.436e-3), ('0.6mm_liquid', 11.25e-3), ('0.8mm_liquid', 20.0e-3), ('coordinator_19g_s', 19.0e-3)):
            m = m0
            for _ in range(20):
                P1 = e.tank.P - e.dp_line(m + mb)
                m = e.c['Cd'] * Q.INJ.pintle_area(H_V28) * e.GT.G(P1, e.tank.T, 2.6e5)
            E[f'{st}|{lab}'] = dict(bleed_g_s=1e3 * mb, mox_no_bleed_g_s=1e3 * m0, mox_with_bleed_g_s=1e3 * m, change_pct=100 * (m / m0 - 1),
                                    P1_drop_bar=(P10 - P1) / 1e5)
    E['tag'] = ('DERIVED: bleed in parallel with the pintle, both fed from the segment, MV fully open (it has been open for the purge); '
                'line loss ASSUMED 2.5 bar at 0.25 kg/s ~ mdot^2 (grain_q1d). The bleed flow is drawn from the tank, not from the injector flow')
    # ---------------- F: A3 / A5 ----------------
    F = dict(runs=Fr)
    for rule in ('abs', 'rel'):
        rs = [r for r in Fr if r['rule'] == rule and r['t_conf_s'] is not None]
        F[f'summary_{rule}'] = dict(n=len([r for r in Fr if r['rule'] == rule]), n_confirmed=len(rs),
                                    t_conf_s=[min(r['t_conf_s'] for r in rs), max(r['t_conf_s'] for r in rs)] if rs else None,
                                    ratio_min={k: min(r['ratio_min'][k] for r in rs) for k in rs[0]['ratio_min']} if rs else None,
                                    Pc_hold_max_bar=max(r['Pc_hold_max_bar'] for r in Fr if r['rule'] == rule),
                                    unlit_ratio_max={k: max(r['unlit_ratio_max'][k] for r in rs) for k in ('gas600K', 'SIL')} if rs else None,
                                    relative_ratio_min=min(r['relative_ratio_min'] for r in rs) if rs else None,
                                    relative_unlit_ratio_max={k: max(r['relative_unlit_ratio_max'][k] for r in rs) for k in ('gas600K', 'SIL')} if rs else None)
    # ---------------- G: drogue release ----------------
    G = {}
    for st in ('A1_relight',):
        e = engine(st)
        for frac in (0.125, 0.20):
            h, s = e.lift_for_thrust(frac * 500.0)
            sx = e.steady(h)
            G[f'{st}|floor{frac}'] = dict(lift_mm=1e3 * h, floor_Pc_bar=sx['Pc'] / 1e5, release_threshold_bar=0.5 * sx['Pc'] / 1e5)
    # ---------------- H: option (C) inventory margin ----------------
    inv = RW['inventory_vs_W']['v']
    H = dict(source='relight_window_rule_seg44_v2p4.json (0.2039 mm, Dyer, Cd 0.70 ASSUMED)', liquid_line_g={})
    for st in inv:
        H['liquid_line_g'][st] = {W: inv[st][W]['liquid_line_g'] for W in ('0.35', '0.65') if W in inv[st]}
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/ignition_detect_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={os.path.basename(f): sha16(os.path.join(d, f)) for f in ('start_latency_v2p4.json', 'relight_vapour_order_v2p4.json',
                                                                                 'purge_sizing_v2p4.json', 'relight_window_rule_seg44_v2p4.json')},
               A_earliest_light=A, B_lit_hold=B, B_runs=runs, C_fuel_free=C, D_unlit=D, E_stuck_open_bleed=E, F_A3_A5=F,
               G_drogue_release=G, H_optionC_inventory=H,
               tags=dict(plant='SIM grain_q1d v2 on ASSUMED laws/bands; no ignition data exist (IGN-1, T1 measure lit and unlit Pc at the ignition lift)',
                         unlit='DERIVED gas-phase bound; the SIL cold model is Electronics ASSUMED'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print(json.dumps(A, indent=1, default=float))
    for k, v in B.items():
        print('B', k, json.dumps(v, default=float))
    for k, v in C.items():
        print('C', k, '%.2f g/s -> %.3f bar' % (v['mox_g_s'], v['Pc_bar']))
    for k, v in D.items():
        print('D', k, json.dumps(v, default=float))
    for k, v in E.items():
        print('E', k, v)
    for k in ('summary_abs', 'summary_rel'):
        print('F', k, json.dumps(F[k], default=float))
    print('G', json.dumps(G, default=float))
    print('H', json.dumps(H, default=float))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])
