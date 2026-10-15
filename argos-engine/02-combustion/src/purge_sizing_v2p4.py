"""Forced purge of the valve-to-seat segment before an A1 relight: time, N2O used and the light at W 0.65 s
(Combustion v2.4; lead decision 2026-10-13 "A1 RELIGHT CONFIGURATION" item 2 and coordinator ask (a)).

Purge (LEAD): MV open with the pintle seated, head-end bleed at the T4 port (bonnet cross-drilling, the crest), 0.6 or 0.8 mm
orifice behind two NC valves in series, open for T_p ending at the lift (or at E0 = the relight command, 0.16 s before the lift).
The segment state at the purge start comes from reroute_vapour_v2p4.simulate (config A, the adopted re-route; config B, the
19 cm3 swing trap), same heat histories, GNC series and readings.
Purge model (DERIVED, plug-flow in flow order, dt 1 ms):
  queue from the bleed: [trap vapour less the needle annulus][liquid slug][S1 cap][tank liquid]; the bleed removes the front
  item at Q_v (vapour) or Q_l (liquid): choked HEM vapour 15 450 kg/m2s and saturated liquid (Dyer, k = 1) 56 843 kg/m2s at
  the coast state, Cd 0.70 ASSUMED (vapour_options_v2p4 fluxes).
  The 4.42 cm3 manifold annulus around the needle (Mechanical segment_traps v1.1) is a dead-end leg off the bleed path with the
  pintle seated: it is taken as vapour at the lift (upper bound; its drift to the crest in a 2 mm gap, 0.016-0.093 m/s, is not credited).
  Boiling on the bleed path during the purge (FD-01, TC-02, TC-04 from Mechanical's head-end split, riser, half the TEE) adds
  vapour that the bleed must pass first: with liquid at the front, a time share G/Q_v passes vapour and (1 - G/Q_v) Q_l passes
  liquid. 'wet': from the purge start; 'dry': once liquid reaches the head. FE manifold-bore and needle heat stay in the annulus.
  S1-side boiling during the purge adds to the cap item.
  End at the lift: the pocket ahead of the first liquid is the annulus + any front vapour. End at E0: the path boiling over the
  0.16 s gate adds to the pocket.
Ignition: the same 200 000-sample E1 -> E2 distribution and the 'paused' / 'restart' conventions (reroute_vapour_v2p4).
usage: python -I purge_sizing_v2p4.py DATA_V2P4_DIR BUDGET_JSON TRAPS_JSON SERIES_CSV OUT_JSON
"""
from __future__ import annotations
import hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import reroute_vapour_v2p4 as RR
import start_latency_v2p4 as SL

G_V, G_L, CD = 15450.0, 56843.0, 0.70
ORIF_MM = (0.6, 0.8)
TP = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)
V_ANN = 4.4225
GATE = 0.16
DTP = 0.001


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def purge(state, Tp, Qv, Ql, Gpath, qR, t0, p, wet):
    """state: dict(V_trap, V_cap, slug). Returns the queue left, vapour and liquid removed [cm3], times."""
    vpj = p['vap_cm3_per_J']
    q = [['V', max(state['V_trap_cm3'] - V_ANN, 0.0)], ['L', state['slug_cm3']], ['V', state['V_cap_cm3']], ['L', 1e9]]
    q = [it for it in q if it[1] > 1e-12]
    rem_v = rem_l = 0.0; t_trap_out = None; t_cap_out = None; liquid_at_head = q[0][0] == 'L'
    n = int(round(Tp / DTP))
    cap_present = state['V_cap_cm3'] > 1e-9
    for k in range(n):
        t = t0 + (k + 0.5) * DTP
        G = Gpath(t) * vpj if (wet or liquid_at_head) else 0.0          # cm3/s of vapour made on the bleed path
        # S1-side boiling feeds the cap item while it exists
        for it in q:
            if it[0] == 'V' and it is not q[0]:
                it[1] += vpj * qR(t) * DTP
                break
        budget = DTP
        while budget > 1e-12 and q:
            kind, vol = q[0]
            if kind == 'V':
                dt_need = vol / Qv
                if dt_need <= budget:
                    rem_v += vol; budget -= dt_need; q.pop(0)
                    if t_trap_out is None:
                        t_trap_out = t - t0
                    if not q or q[0][0] == 'L':
                        liquid_at_head = True
                    continue
                q[0][1] -= Qv * budget; rem_v += Qv * budget; budget = 0.0
            else:
                f = min(G / Qv, 1.0)
                if f >= 1.0:                                              # boiling exceeds the bleed: vapour builds at the front
                    rem_v += Qv * budget
                    q.insert(0, ['V', (G - Qv) * budget]); budget = 0.0; break
                dt_need = vol / ((1.0 - f) * Ql)
                if dt_need <= budget:
                    rem_l += vol; rem_v += G * dt_need; budget -= dt_need; q.pop(0)
                    continue
                rem_l += (1.0 - f) * Ql * budget; rem_v += G * budget; q[0][1] -= (1.0 - f) * Ql * budget; budget = 0.0
        if cap_present and t_cap_out is None and not any(it[0] == 'V' for it in q):
            t_cap_out = t - t0
    return q, rem_v, rem_l, t_trap_out, t_cap_out


def main(d, budget_f, traps_f, series_f, out_f):
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    MG = json.load(open(os.path.join(d, 'coast_migration_v2p4.json')))
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    PA = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
    RRJ = json.load(open(os.path.join(d, 'reroute_vapour_v2p4.json')))
    B = json.load(open(budget_f)); TR = json.load(open(traps_f))
    p = VO['properties']; rho_l, rho_v = p['rho_l'], p['rho_v']
    PURGE = VO['purge_s_per_cm3']; DEAD = VO['liquid_plug_dead_time_s_per_cm3']
    prim = TR['segment_volume_by_primitive_cm3']
    assert abs(prim['TC-03/TC-02/TC-04 manifold bore (annulus around the needle)'] - V_ANN) < 1e-9
    vz = {r['z_mm']: r for r in TR['V_of_z_open_element_retained']}
    V_dead = round(vz[75.0]['V_above_cm3'] - vz[75.0]['V_above_flow_path_cm3'], 3)
    TRAPS = {'A': vz[75.0]['V_above_flow_path_cm3'], 'B': 19.0}
    t_meco = float(B['t_meco_s']); T_m = float(B['coast_s'])
    el = {e['name']: e for e in B['elements']}
    HE = B['head_end_W_vs_t']['v']
    heat = {}
    for case in HE:
        fam = case.split('|')[1]
        th = np.array(HE[case]['t_s']) - t_meco
        f_head = RR.series_fn(th, HE[case]['Q_head_end_W'])
        split = HE[case]['split_W']
        fe_key = [k for k in split if k.startswith('FE manifold bore')][0]
        f_path_head = RR.series_fn(th, np.array(split['FD-01']) + np.array(split['TC-02']) + np.array(split['TC-04']))
        assert abs(np.array(split['FD-01']) + np.array(split['TC-02']) + np.array(split['TC-04']) + np.array(split[fe_key])
                   - np.array(HE[case]['Q_head_end_W'])).max() < 0.05
        E_n = B['needle']['E_J'][0 if fam == 'LO' else 1]
        a_n = E_n / (RR.TAU_NEEDLE * (1 - math.exp(-T_m / RR.TAU_NEEDLE)))
        f_el = {nm: RR.series_fn(np.array(el[nm]['Q_coast_t_s']) - t_meco, el[nm]['Q_coast_W'][case])
                for nm in (RR.N_MOD, RR.N_WALL, RR.N_UNION, RR.N_ENDS, RR.N_HOSE, RR.N_TEE, RR.N_RISER)}
        heat[case] = dict(head=f_head, path_head=f_path_head, needle=(lambda t, a=a_n: a * math.exp(-t / RR.TAU_NEEDLE)), el=f_el)

    def funcs(case, cfg):
        h = heat[case]; sp = RR.SPLIT[cfg]
        qT = lambda t: h['head'](t) + h['needle'](t) + sum(w * h['el'][n](t) for n, w in sp['trap'].items())
        qR = lambda t: sum(w * h['el'][n](t) for n, w in sp['route'].items())
        Gp = lambda t: h['path_head'](t) + h['el'][RR.N_RISER](t) + 0.5 * h['el'][RR.N_TEE](t)
        return qT, qR, Gp

    # ignition distribution (as RR)
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
    assert abs(float(base.max()) - PA['E1_E2_liquid_s']['max']) < 1e-9
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
        o['E1_E2_max_s'] = float((base + PURGE * pocket).max())
        return o

    res, summ = {}, {}
    QQ = {}
    for orif in ORIF_MM:
        A = math.pi / 4 * (orif * 1e-3) ** 2
        QQ[orif] = (CD * A * G_V / rho_v * 1e6, CD * A * G_L / rho_l * 1e6)
    for case in HE:
        for cfg in ('A', 'B'):
            qT, qR, Gp = funcs(case, cfg)
            capT = TRAPS[cfg] + V_dead
            for sname, sv in MG['series'].items():
                Tw = sv['window_s']; t_dl = Tw - sv['t_from_drogue_load_s']
                for wet in (True, False):
                    tag = 'wet' if wet else 'dry'
                    for Tp in TP:
                        for end in ('lift', 'E0'):
                            t_end = Tw + GATE if end == 'lift' else Tw
                            t0 = t_end - Tp
                            st = RR.simulate(qT, qR, t0, t_dl, p, capT, wet)
                            for orif in ORIF_MM:
                                Qv, Ql = QQ[orif]
                                qq, rv, rl, t_tr, t_cap = purge(st, Tp, Qv, Ql, Gp, qR, t0, p, wet)
                                pocket = V_ANN
                                if qq and qq[0][0] == 'V':
                                    pocket += qq[0][1]; qq = qq[1:]
                                if end == 'E0':
                                    pocket += Gp(Tw + 0.5 * GATE) * p['vap_cm3_per_J'] * GATE
                                slug = qq[0][1] if qq and qq[0][0] == 'L' else 0.0
                                cap = qq[1][1] if len(qq) > 1 and qq[1][0] == 'V' else 0.0
                                if slug > 1e8:
                                    slug, cap = 1e3, 0.0
                                ig_ = ignite(pocket, cap, slug)
                                r = dict(state_at_start=dict(V_trap=st['V_trap_cm3'], V_cap=st['V_cap_cm3'], slug=st['slug_cm3']),
                                         vapour_removed_cm3=rv, liquid_removed_cm3=rl, N2O_g=rv * rho_v * 1e-3 + rl * rho_l * 1e-3,
                                         t_trap_vapour_out_s=t_tr, t_last_vapour_out_s=t_cap, pocket_cm3=pocket, slug_cm3=slug, cap_cm3=cap,
                                         G_path_at_end_cm3_s=Gp(t_end) * p['vap_cm3_per_J'], P_abort_W0p65=ig_)
                                res[f'{orif}|{case}|{cfg}|{sname}|{tag}|Tp{Tp}|{end}'] = r
                                key = f'{orif}|{case}|{cfg}|{tag}|Tp{Tp}|{end}'
                                s_ = summ.setdefault(key, dict(P_paused=[1, 0], P_restart=[1, 0], N2O_g=[1e9, 0], pocket=[1e9, 0], cap=[1e9, 0], slug=[1e9, 0]))
                                for kk, val in (('P_paused', ig_['paused']), ('P_restart', ig_['restart']), ('N2O_g', r['N2O_g']),
                                                ('pocket', pocket), ('cap', cap), ('slug', min(slug, 999.0))):
                                    s_[kk] = [min(s_[kk][0], val), max(s_[kk][1], val)]
            print(case, cfg, 'done', flush=True)
    # minimum Tp with P_abort 0 (both conventions) for every series and reading, per orifice / case / cfg / end
    tp_min = {}
    for orif in ORIF_MM:
        for case in HE:
            for cfg in ('A', 'B'):
                for end in ('lift', 'E0'):
                    ok = None
                    for Tp in TP:
                        if all(summ[f'{orif}|{case}|{cfg}|{tag}|Tp{Tp}|{end}']['P_restart'][1] == 0.0 and
                               summ[f'{orif}|{case}|{cfg}|{tag}|Tp{Tp}|{end}']['P_paused'][1] == 0.0 for tag in ('wet', 'dry')):
                            ok = Tp; break
                    tp_min[f'{orif}|{case}|{cfg}|{end}'] = ok
    flows = {}
    for orif in ORIF_MM:
        A = math.pi / 4 * (orif * 1e-3) ** 2
        flows[f'{orif}mm'] = dict(Q_vapour_cm3_s=CD * A * G_V / rho_v * 1e6, Q_liquid_cm3_s=CD * A * G_L / rho_l * 1e6,
                                  mdot_vapour_g_s=CD * A * G_V * 1e3, mdot_liquid_g_s=CD * A * G_L * 1e3,
                                  N2O_liquid_full_g={f'Tp{Tp}': CD * A * G_L * 1e3 * Tp for Tp in TP},
                                  jet_thrust_liquid_N=CD * A * G_L * math.sqrt(2 * (p['P_Pa'] - 101325.0) / rho_l))
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/purge_sizing_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs=dict(reroute_vapour=sha16(os.path.join(d, 'reroute_vapour_v2p4.json')), vapour_order=sha16(os.path.join(d, 'relight_vapour_order_v2p4.json')),
                           mech_budget=dict(file=budget_f, sha256_16=sha16(budget_f)), mech_traps=dict(file=traps_f, sha256_16=sha16(traps_f)),
                           gnc_series=dict(file=series_f, sha256_16=sha16(series_f))),
               constants=dict(G_vapour_kg_m2s=G_V, G_liquid_kg_m2s=G_L, Cd=CD, V_annulus_cm3=V_ANN, gate_s=GATE, dt_s=DTP, traps=TRAPS, V_dead=V_dead),
               flows=flows, tp_min_for_P_abort_0=tp_min, summary=summ, cases=res,
               tags=dict(model='DERIVED plug-flow purge on the reroute_vapour_v2p4 state (Mechanical ESTIMATE heat, DERIVED trap volumes, GNC SIM windows); '
                               'fluxes HEM / Dyer at the coast state; Cd ASSUMED', ignition='SIM on ASSUMED delays'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print(json.dumps(flows, indent=0))
    for k, v in tp_min.items():
        print('Tp_min', k, v)
    for k, s in summ.items():
        if '|A|' in k and ('Tp2.0' in k or 'Tp3.0' in k or 'Tp1.0' in k):
            print('%-48s P65 p %.4f-%.4f r %.4f-%.4f  N2O %.1f-%.1f g  pocket %.2f-%.2f  slug %.1f-%.1f cap %.2f-%.2f' % (
                k, *s['P_paused'], *s['P_restart'], *s['N2O_g'], *s['pocket'], *s['slug'], *s['cap']))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:6])
