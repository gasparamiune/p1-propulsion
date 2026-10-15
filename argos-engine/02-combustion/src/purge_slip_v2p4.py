"""Forced purge with bubble slip: the S1 cap is carried down the route more slowly than the liquid (Combustion v2.4,
2026-10-13; check of purge_sizing_v2p4, which moves every item in plug flow).

Why: in the descent the cap sits at S1 (top of the segment) and the purge carries it DOWN the wall line and the coil to the
TEE before the riser takes it up to the crest bleed. A bubble in a downward or near-horizontal run moves at about
C0 u - u_d, with u_d = Fr_d sqrt(g' D) (Fr_d 0.35 vertical, up to ~0.55-0.63 in near-horizontal or shallow downward runs,
LITERATURE as recalled, TO-VERIFY; g' = g (rho_l - rho_v)/rho_l). Liquid velocity in the re-routed hose (ID 10.5-11 mm):
0.6 mm orifice 0.146-0.160 m/s, Fr' 0.49-0.55; 0.8 mm orifice 0.259-0.284 m/s, Fr' 0.87-0.97 (DERIVED below).
Model: purge_sizing_v2p4 with the cap transport ratio s = (cap speed)/(plug speed) in {1, 0.5, 0.25, 0}:
  front vapour removed at Q_v -> the slug ahead of the cap GROWS by (1 - s) Q_v dt (liquid overtakes the cap);
  liquid at the front -> the slug shrinks by s (1 - f) Q_l dt; the cap is removed at Q_v once the slug ahead is gone.
  s = 1 reproduces purge_sizing_v2p4; s = 0 is a stalled cap (it stays at S1 and enters the injector only after the lift).
Same states (reroute_vapour_v2p4.simulate), heat, series, ignition distribution and conventions as purge_sizing_v2p4.
usage: python -I purge_slip_v2p4.py DATA_V2P4_DIR BUDGET_JSON TRAPS_JSON SERIES_CSV OUT_JSON
"""
from __future__ import annotations
import hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import reroute_vapour_v2p4 as RR
import start_latency_v2p4 as SL
import purge_sizing_v2p4 as PS

SLIPS = (1.0, 0.5, 0.25, 0.0)
TP = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def purge_slip(state, Tp, Qv, Ql, Gpath, qR, t0, p, wet, s):
    vpj = p['vap_cm3_per_J']
    Vf = max(state['V_trap_cm3'] - PS.V_ANN, 0.0); Ls = state['slug_cm3']; Vc = state['V_cap_cm3']
    cap_exists = Vc > 1e-12
    if not cap_exists:
        Ls = 1e9
    rem_v = rem_l = 0.0
    n = int(round(Tp / PS.DTP)); dt = PS.DTP
    for k in range(n):
        t = t0 + (k + 0.5) * dt
        if cap_exists:
            Vc += vpj * qR(t) * dt
        G = Gpath(t) * vpj if (wet or Vf <= 1e-12) else 0.0
        budget = dt
        while budget > 1e-12:
            if Vf > 1e-12:
                dtn = Vf / Qv
                use = min(dtn, budget)
                Vf -= Qv * use; rem_v += Qv * use
                if cap_exists:
                    Ls += (1.0 - s) * Qv * use
                budget -= use
                if Vf <= 1e-12:
                    Vf = 0.0
                continue
            if cap_exists and Ls <= 1e-12:
                # cap at the head: remove it as vapour
                Vf = Vc; Vc = 0.0; cap_exists = False; Ls = 1e9
                continue
            f = min(G / Qv, 1.0)
            if f >= 1.0:
                rem_v += Qv * budget; Vf += (G - Qv) * budget; budget = 0.0
                break
            ql = (1.0 - f) * Ql
            if cap_exists and s > 0.0:
                dtn = Ls / (s * ql)
                use = min(dtn, budget)
            else:
                use = budget
            rem_l += ql * use; rem_v += G * use
            if cap_exists:
                Ls -= s * ql * use
                if Ls <= 1e-9:
                    Ls = 0.0
            budget -= use
    return dict(Vf=Vf, slug=Ls if cap_exists else 1e3, cap=Vc if cap_exists else 0.0, rem_v=rem_v, rem_l=rem_l)


def task(args):
    (case, cfg, d, budget_f, traps_f, series_f) = args
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    MG = json.load(open(os.path.join(d, 'coast_migration_v2p4.json')))
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    B = json.load(open(budget_f)); TR = json.load(open(traps_f))
    p = VO['properties']; rho_l, rho_v = p['rho_l'], p['rho_v']
    PURGE = VO['purge_s_per_cm3']; DEAD = VO['liquid_plug_dead_time_s_per_cm3']
    vz = {r['z_mm']: r for r in TR['V_of_z_open_element_retained']}
    V_dead = round(vz[75.0]['V_above_cm3'] - vz[75.0]['V_above_flow_path_cm3'], 3)
    TRAPS = {'A': vz[75.0]['V_above_flow_path_cm3'], 'B': 19.0}
    t_meco = float(B['t_meco_s']); T_m = float(B['coast_s'])
    el = {e['name']: e for e in B['elements']}
    HE = B['head_end_W_vs_t']['v'][case]
    fam = case.split('|')[1]
    th = np.array(HE['t_s']) - t_meco
    f_head = RR.series_fn(th, HE['Q_head_end_W'])
    split = HE['split_W']
    f_path_head = RR.series_fn(th, np.array(split['FD-01']) + np.array(split['TC-02']) + np.array(split['TC-04']))
    E_n = B['needle']['E_J'][0 if fam == 'LO' else 1]
    a_n = E_n / (RR.TAU_NEEDLE * (1 - math.exp(-T_m / RR.TAU_NEEDLE)))
    f_el = {nm: RR.series_fn(np.array(el[nm]['Q_coast_t_s']) - t_meco, el[nm]['Q_coast_W'][case])
            for nm in (RR.N_MOD, RR.N_WALL, RR.N_UNION, RR.N_ENDS, RR.N_HOSE, RR.N_TEE, RR.N_RISER)}
    needle = lambda t: a_n * math.exp(-t / RR.TAU_NEEDLE)
    sp = RR.SPLIT[cfg]
    qT = lambda t: f_head(t) + needle(t) + sum(w * f_el[nm](t) for nm, w in sp['trap'].items())
    qR = lambda t: sum(w * f_el[nm](t) for nm, w in sp['route'].items())
    Gp = lambda t: f_path_head(t) + f_el[RR.N_RISER](t) + 0.5 * f_el[RR.N_TEE](t)
    # ignition distribution (as purge_sizing_v2p4)
    PA_ = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
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
    assert abs(float(base.max()) - PA_['E1_E2_liquid_s']['max']) < 1e-9
    need = base - t_lift

    def ignite(pocket, cap, slug):
        o = {}
        t_s = slug * DEAD; short = need > t_s
        for conv in ('paused', 'restart'):
            if slug <= 1e-9:
                e12 = base + PURGE * (pocket + cap)
            elif conv == 'paused':
                e12 = base + PURGE * pocket + np.where(short, PURGE * cap, 0.0)
            else:
                e12 = base + PURGE * pocket + np.where(short, t_s + PURGE * cap, 0.0)
            o[conv] = float(np.mean(e12 > 0.65))
        return o

    QQ = {}
    for orif in PS.ORIF_MM:
        A = math.pi / 4 * (orif * 1e-3) ** 2
        QQ[orif] = (PS.CD * A * PS.G_V / rho_v * 1e6, PS.CD * A * PS.G_L / rho_l * 1e6)
    capT = TRAPS[cfg] + V_dead
    res = {}
    for sname, sv in MG['series'].items():
        Tw = sv['window_s']; t_dl = Tw - sv['t_from_drogue_load_s']
        for wet in (True, False):
            tag = 'wet' if wet else 'dry'
            for Tp in TP:
                for end in ('lift', 'E0'):
                    t_end = Tw + PS.GATE if end == 'lift' else Tw
                    t0 = t_end - Tp
                    st = RR.simulate(qT, qR, t0, t_dl, p, capT, wet)
                    for orif in PS.ORIF_MM:
                        Qv, Ql = QQ[orif]
                        for s in SLIPS:
                            r = purge_slip(st, Tp, Qv, Ql, Gp, qR, t0, p, wet, s)
                            pocket = PS.V_ANN + r['Vf']
                            if end == 'E0':
                                pocket += Gp(Tw + 0.5 * PS.GATE) * p['vap_cm3_per_J'] * PS.GATE
                            ig_ = ignite(pocket, r['cap'], r['slug'])
                            res[f'{orif}|{case}|{cfg}|{sname}|{tag}|Tp{Tp}|{end}|s{s}'] = dict(
                                pocket_cm3=pocket, slug_cm3=min(r['slug'], 999.0), cap_cm3=r['cap'], N2O_g=r['rem_v'] * rho_v * 1e-3 + r['rem_l'] * rho_l * 1e-3,
                                P_paused=ig_['paused'], P_restart=ig_['restart'],
                                state_at_start=dict(V_trap=st['V_trap_cm3'], V_cap=st['V_cap_cm3'], slug=st['slug_cm3']))
    return res


def main(d, budget_f, traps_f, series_f, out_f):
    B = json.load(open(budget_f))
    cases = list(B['head_end_W_vs_t']['v'].keys())
    jobs = [(c, cfg, d, budget_f, traps_f, series_f) for c in cases for cfg in ('A', 'B')]
    from multiprocessing import Pool
    with Pool(2) as pool:
        parts = pool.map(task, jobs)
    res = {}
    for prt in parts:
        res.update(prt)
    json.dump(res, open(out_f + '.raw.json', 'w'), default=float)   # raw cases first, so a summary error loses nothing
    # summary over series per orif|case|cfg|wet|Tp|end|s
    summ = {}
    for k, r in res.items():
        orif, rest = k.split('|', 1)
        case, cfg, sname, tag, tp, end, s = rest.rsplit('|', 6)   # case is 'name|LO/HI'
        key = '|'.join((orif, case, cfg, tag, tp, end, s))
        sm = summ.setdefault(key, dict(P_paused=[1, 0], P_restart=[1, 0], N2O_g=[1e9, 0], pocket=[1e9, 0], slug=[1e9, 0], cap=[1e9, 0]))
        for kk, val in (('P_paused', r['P_paused']), ('P_restart', r['P_restart']), ('N2O_g', r['N2O_g']), ('pocket', r['pocket_cm3']),
                        ('slug', r['slug_cm3']), ('cap', r['cap_cm3'])):
            sm[kk] = [min(sm[kk][0], val), max(sm[kk][1], val)]
    # robust Tp_min: smallest grid Tp from which every larger grid Tp gives P_abort 0 (both conventions, wet and dry, every series)
    tp_min = {}
    for orif in PS.ORIF_MM:
        for case in cases:
            for cfg in ('A', 'B'):
                for end in ('lift', 'E0'):
                    for s in SLIPS:
                        ok_list = []
                        for Tp in TP:
                            ok = all(summ[f'{orif}|{case}|{cfg}|{tag}|Tp{Tp}|{end}|s{s}']['P_restart'][1] == 0.0 and
                                     summ[f'{orif}|{case}|{cfg}|{tag}|Tp{Tp}|{end}|s{s}']['P_paused'][1] == 0.0 for tag in ('wet', 'dry'))
                            ok_list.append(ok)
                        robust = None
                        for i, Tp in enumerate(TP):
                            if all(ok_list[i:]):
                                robust = Tp; break
                        first = next((Tp for Tp, ok in zip(TP, ok_list) if ok), None)
                        Pmax = {f'Tp{Tp}': max(summ[f'{orif}|{case}|{cfg}|{tag}|Tp{Tp}|{end}|s{s}']['P_restart'][1] for tag in ('wet', 'dry')) for Tp in TP}
                        tp_min[f'{orif}|{case}|{cfg}|{end}|s{s}'] = dict(first_zero=first, robust_zero=robust, P_restart_max_by_Tp=Pmax)
    # hose velocities and Froude numbers for the two orifices
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json'))); p = VO['properties']
    gp = 9.80665 * (p['rho_l'] - p['rho_v']) / p['rho_l']
    vel = {}
    for orif in PS.ORIF_MM:
        A = math.pi / 4 * (orif * 1e-3) ** 2
        Ql = PS.CD * A * PS.G_L / p['rho_l']
        for lab, D in (('hose_ID10.5', 10.5e-3), ('hose_ID11', 11.0e-3), ('wall_line_7.747', 7.747e-3)):
            u = Ql / (math.pi / 4 * D ** 2)
            vel[f'{orif}mm|{lab}'] = dict(u_m_s=u, Fr_prime=u / math.sqrt(gp * D), u_d_vertical_m_s=0.35 * math.sqrt(gp * D),
                                           u_d_shallow_m_s=[0.55 * math.sqrt(gp * D), 0.63 * math.sqrt(gp * D)],
                                           Q_needed_shallow_cm3_s=[1e6 * 0.55 * math.sqrt(gp * D) * math.pi / 4 * D ** 2, 1e6 * 0.63 * math.sqrt(gp * D) * math.pi / 4 * D ** 2])
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/purge_slip_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs=dict(purge_sizing=sha16(os.path.join(d, 'purge_sizing_v2p4.json')), reroute_vapour=sha16(os.path.join(d, 'reroute_vapour_v2p4.json')),
                           mech_budget=sha16(budget_f), mech_traps=sha16(traps_f), gnc_series=sha16(series_f)),
               slips=SLIPS, Tp_grid=TP, velocities=vel, tp_min=tp_min, summary=summ, cases=res,
               tags=dict(model='DERIVED plug flow with a cap transport ratio s (bracket, not a two-phase solution); drift Froude numbers LITERATURE as recalled, TO-VERIFY at CF-4',
                         ignition='SIM on ASSUMED delays'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    for k, v in vel.items():
        print('vel', k, json.dumps(v, default=float))
    for k, v in tp_min.items():
        print('Tp_min', k, v['first_zero'], v['robust_zero'], ' '.join('%s:%.3f' % (a, b) for a, b in v['P_restart_max_by_Tp'].items()))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:6])
