"""Relight vapour options against the lead's question of 2026-10-13 (Combustion v2.4; Electronics SIL S11 relayed by the
coordinator: the ECU cannot detect saturated vapour; at W 0.65 s a vapour-full 44 cm3 segment does not light; the minimum W
that lights it is 0.76 s on the prep path and 0.93 s on the direct path; at 32.6 cm3 the direct path still fails).

Questions and what this script computes:
 (d) MV opened early under the drogue, pintle held seated:
     - the U (U-bottom z 45 -> crest z 204.6 -> seat, 27.87 cm3): buoyant exchange path to the MV, with f_z after the drogue
       load from coast_migration_v2p4 (GNC staging v3.1 histories);
     - the route (module + wall line, 16.1 cm3): Taylor-bubble drift time up the 195 mm wall line, and the counter-current
       (flooding) capacity of the wall line and of the module drilling (Wallis form, C 0.725-1.0, m 1; LITERATURE form as
       recalled, TO-VERIFY) against the vapour generation of each Mechanical heat case at the end of the coast;
     - the line bore that a self-venting re-route (no crest) would need to vent the U-side generation by counter-current flow;
     - exposure: time with the MV open on a seated pintle (drogue load -> relight command per GNC series) and the inventory
       behind the seat (segment vs tank).
 (a) Crest prime bleed (MV open, pintle seated, NC bleed valve to ambient, timed because no sensor sees vapour):
     - real-fluid choked vapour flux and Dyer (k = 1, saturated liquid) liquid flux from CoolProp at the relight tank state of
       the A1 sizing history; orifice diameter to clear 27.87 / 34.0 / 38.7 / 44.0 cm3 in 0.30 and 0.50 s;
     - N2O lost per relight: vapour-full and primed (a timed bleed dumps liquid for its whole open time when the line is
       primed); 25 % timing margin on the open time (ASSUMED);
     - residual pocket at the lift: bore-leg term + U boiling x (gap + E0->E1) for every heat case; P_abort at W 0.65 / 0.85 / 1.05;
     - fail-open flow during the landing burn and at the ignition lift.
 (b) Wider W: the W that lights each heat case with P_abort = 0 in the post_abort_pocket model (base max + purge x V_eff).
 Heat cases: the six totals of Mechanical's segment_heat_budget_v1 (isothermal, hw+5K, ARM_bay45C_liq24C; LO / HI), mapped to
 the flow-order elements exactly as relight_vapour_order_v2p4 maps the isothermal pair, time-scaled with the LO / HI FE
 series shape (ASSUMED for the new cases).
usage: python -I vapour_options_v2p4.py DATA_V2P4_DIR MECH_BUDGET A1_HISTORY_CSV OUT_JSON
"""
from __future__ import annotations
import json, math, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import relight_vapour_order_v2p4 as RV
import start_latency_v2p4 as SL

FL = 'NitrousOxide'
PAMB = 101325.0
CD = 0.70                      # ASSUMED sharp-edged orifice, band 0.6-0.8
MARGIN = 1.25                  # ASSUMED timing margin on a timed bleed
CASES = ('isothermal|LO', 'isothermal|HI', 'hw+5K|LO', 'hw+5K|HI', 'ARM_bay45C_liq24C|LO', 'ARM_bay45C_liq24C|HI')


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def g_hem(P1, s1, h1, P2):
    """Homogeneous-equilibrium isentropic mass flux [kg/m2s] from (P1, s1, h1) to the best throat pressure >= P2."""
    best = (0.0, P2)
    for Pt in np.linspace(P2, 0.995 * P1, 240):
        try:
            ht = CP.PropsSI('H', 'P', Pt, 'S', s1, FL); rt = CP.PropsSI('D', 'P', Pt, 'S', s1, FL)
        except ValueError:
            continue
        if h1 > ht:
            G = rt * math.sqrt(2.0 * (h1 - ht))
            if G > best[0]:
                best = (G, Pt)
    return best


def flood_Q(D, g, rl, rv, C):
    """Wallis counter-current flooding with equal volume fluxes up (vapour) and down (liquid): sqrt(j)(rv^.25 + rl^.25) =
    C (g D (rl - rv))^.25; returns the volumetric exchange capacity [m3/s] of a tube of diameter D."""
    sj = C * (g * D * (rl - rv)) ** 0.25 / (rv ** 0.25 + rl ** 0.25)
    return sj * sj * math.pi / 4 * D * D


def D_for_flood(Q, g, rl, rv, C):
    lo, hi = 1e-3, 0.1
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if flood_Q(m, g, rl, rv, C) < Q:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def main(d, budget_f, a1_f, out_f):
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    MG = json.load(open(os.path.join(d, 'coast_migration_v2p4.json')))
    ST = json.load(open(os.path.join(d, 'relight_vapour_states_v2p4.json')))
    B = json.load(open(budget_f))
    assert sha16(budget_f) == VO['inputs']['mech_budget']['sha256_16'], 'budget differs from relight_vapour_order input'
    p = VO['properties']; geo = VO['geometry']
    V_U = geo['U_volume_cm3']; V_bore = geo['bore_leg_cm3']; V_mod = geo['module_cm3']; V_wall = geo['wall_line_cm3']
    vpj = p['vap_cm3_per_J']; PURGE = VO['purge_s_per_cm3']; DEAD = VO['liquid_plug_dead_time_s_per_cm3']
    T_m = VO['window_s']['mech']
    ID_wall = (9.525 - 2 * 0.889) * 1e-3; A_wall = math.pi / 4 * ID_wall ** 2

    # ------------------------------------------------------------------ heat cases mapped to the U / route sides (as RV)
    el = {e['name']: e for e in B['elements']}
    E = lambda name, case: float(el[name]['E_coast_J'][case])
    fe = B['fe_head_bore']; nd = B['needle']['E_J']
    route_names = ('MV/FS-01 module, outlet side (316L body)', 'fixed wall line 3/8 x 0.035 316L, module -> coil (~250 mm)',
                   'line-coil union / 90 deg elbow (316)')
    U_names = ('coil hose O3b 0.252 m, PTFE liner 1.0 + SS braid 0.5 (equivalent)', 'FD-05 TEE + MSS-1 port (316L)',
               'FD-03 riser 3/8 x 0.035 316L (~130 mm)', 'FD-01 inlet block (316L, ~52 g)',
               'TC-02 head cap: filter bore 14 x 21 + axial 8 x 7 (6061)', 'TC-04 bonnet: axial 8 x 26 + cross 8 x 14 + T4 port (6061)')
    hose_ends = 'coil hose ends 2x -6 JIC swivel + nipple (316)'
    heat = {}
    for case in CASES:
        fam = case.split('|')[1]
        QU = sum(E(n, case) for n in U_names) + 0.5 * E(hose_ends, case) + fe[fam]['E_coast_J'] + nd[0 if fam == 'LO' else 1]
        QR = sum(E(n, case) for n in route_names) + 0.5 * E(hose_ends, case)
        heat[case] = dict(Q_U_J=QU, Q_route_J=QR, Q_total_J=QU + QR, mechanical_total_J=B['totals'][case]['E_total_J'],
                          family=fam)
    chk = dict(isothermal_LO_U=heat['isothermal|LO']['Q_U_J'], VO_LO_U=VO['heat_J']['LO']['U'],
               isothermal_HI_U=heat['isothermal|HI']['Q_U_J'], VO_HI_U=VO['heat_J']['HI']['U'])
    chk['reproduces_VO'] = bool(abs(chk['isothermal_LO_U'] - chk['VO_LO_U']) < 0.2 and abs(chk['isothermal_HI_U'] - chk['VO_HI_U']) < 0.2)

    # ------------------------------------------------------------------ base latency distribution (post_abort_pocket model)
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
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
    bmax = float(base.max())
    dist_chk = dict(base_max_s=bmax, states_base_max_s=ST['distribution_check']['base_max_s'],
                    reproduces=bool(abs(bmax - ST['distribution_check']['base_max_s']) < 1e-12))

    def pab(V, W):
        return float(np.mean(base + PURGE * np.broadcast_to(np.asarray(V, dtype=float), base.shape) > W))

    def W_req(V):
        return bmax + PURGE * float(np.max(V))

    # ------------------------------------------------------------------ pockets of every heat case at RELIGHT (relight_vapour_order_v2p4 logic)
    g_p01 = 7.74
    Ud_wall = RV.drift(ID_wall, g_p01, p)[0]
    lpj = p['liq_cm3_per_J']
    pockets = {}
    for case, hc in heat.items():
        fam = hc['family']; sc = VO['window_scale'][fam]
        rate_U = hc['Q_U_J'] / T_m * sc['q_end_over_mean'] * vpj          # cm3/s at the end of the coast (U side)
        rate_R = hc['Q_route_J'] / T_m * sc['q_end_over_mean'] * vpj       # cm3/s (route side)
        rows = {}
        for w in ('min', 'mech', 'p50', 'max'):
            Vg = hc['Q_U_J'] * sc[w] * vpj
            Q_L1 = (fe[fam]['E_coast_J'] + nd[0 if fam == 'LO' else 1]) * sc[w]
            share_desc = 1.0 - sc['coast_up_share'] / sc[w]
            plug_refill = max(0.0, V_bore - Q_L1 * share_desc * lpj)
            o = {}
            for lab, plug in (('bore_leg_refilled', plug_refill), ('bore_leg_dry', 0.0)):
                V_vap_U = min(Vg, V_U - plug)
                over = max(0.0, Vg - (V_U - plug))
                void = 0.0
                if over > 0:
                    jv = (rate_U + rate_R) * 1e-6 / A_wall
                    void = jv / (1.2 * jv + Ud_wall)
                Veff = V_vap_U + (plug * DEAD / PURGE if plug > 0 else 0.0) + void * (V_wall + V_mod)
                o[lab] = dict(plug_cm3=plug, overflow_cm3=over, wall_void=void, V_eff_cm3=Veff,
                              P_abort={f'W{W:.2f}': pab(Veff, W) for W in (0.65, 0.85, 1.05)}, W_for_P_abort_0_s=W_req(Veff))
            rows[w] = dict(window_s=VO['window_s'][w], V_generated_U_cm3=Vg, U_full=bool(Vg >= V_U), **o)
        pockets[case] = dict(heat=hc, U_boil_rate_end_cm3_s=rate_U, route_boil_rate_end_cm3_s=rate_R, windows=rows)
    # the isothermal pair must reproduce relight_vapour_order_v2p4 (corrected run)
    rep = []
    for fam in ('LO', 'HI'):
        for w in ('min', 'mech', 'p50', 'max'):
            for lab in ('bore_leg_refilled', 'bore_leg_dry'):
                rep.append(abs(pockets[f'isothermal|{fam}']['windows'][w][lab]['V_eff_cm3'] - VO['results'][f'{fam}|{w}'][lab]['V_eff_cm3']))
    chk['pocket_max_abs_diff_vs_VO_cm3'] = float(max(rep))
    assert chk['pocket_max_abs_diff_vs_VO_cm3'] < 1e-6, chk

    # ------------------------------------------------------------------ (d) early MV opening, pintle seated
    rl, rv = p['rho_l'], p['rho_v']
    fz_after = {k: v['fz_min_after_drogue_load_mps2'] for k, v in MG['series'].items()}
    t_drogue = {k: v['t_from_drogue_load_s'] for k, v in MG['series'].items()}
    env_td = {q: MG['envelope_aligned_at_relight_cmd'][q]['t_from_drogue_load_s'] for q in ('p01', 'p50', 'p99')}
    g_set = dict(min_after_drogue=min(fz_after.values()), descent_mean_p01=7.74, descent_mean_p50=8.18)
    drift_t = {k: 0.195 / RV.drift(ID_wall, g, p)[0] for k, g in g_set.items()}
    flood = {}
    for lab, D in (('wall line 7.75 mm', ID_wall), ('module drilling 8 mm (MV path, ASSUMED = D_h of the module)', 8.0e-3)):
        flood[lab] = {f'{k}|C{C}': 1e6 * flood_Q(D, g, rl, rv, C) for k, g in g_set.items() for C in (0.725, 1.0)}
    need = {}
    for case, pk in pockets.items():
        q_all = (pk['U_boil_rate_end_cm3_s'] + pk['route_boil_rate_end_cm3_s']) * 1e-6
        need[case] = {f'D_mm_C{C}_g{gl}': 1e3 * D_for_flood(q_all, g_set[gl], rl, rv, C)
                      for C in (0.725, 1.0) for gl in ('min_after_drogue', 'descent_mean_p01')}
    opt_d = dict(
        U_exchange=dict(path='none: the crest (z 204.6) is 159.6 mm above the U-bottom (z 45); every buoyant path from the crest to '
                        'the MV first descends to the U-bottom', fz_min_after_drogue_load_mps2=fz_after,
                        exchange_time_s='infinite (no reversal of f_z after the drogue load in any GNC series)'),
        route=dict(volume_cm3=V_mod + V_wall, wall_line_traverse_s=drift_t,
                   note='already vents through S1 to the tank with the MV closed (relight_vapour_order_v2p4); opening the MV only adds a second path'),
        flooding_capacity_cm3_s=flood,
        generation_at_relight_cm3_s={c: dict(U=pk['U_boil_rate_end_cm3_s'], route=pk['route_boil_rate_end_cm3_s']) for c, pk in pockets.items()},
        self_venting_reroute_line_D_needed_mm=need,
        bore_leg_note='the 2 mm annular bore leg (4.51 cm3) keeps a vapour fill whenever its generation exceeds its own counter-current capacity '
                      '(flood capacity of a 2 mm gap ~1e-2 cm3/s at 8 m/s2 order); it is the residual of any self-venting layout',
        exposure=dict(MV_open_on_seated_pintle_s=t_drogue, envelope_s=env_td, v2p8_E0_ramp_s=0.35,
                      inventory_behind_seat_MV_closed_g=44.0 * rl / 1e3, inventory_behind_seat_MV_open='tank liquid (see a1_tank_at_relight)'),
        tag='DERIVED (GNC SIM f_z, LITERATURE forms as recalled, TO-VERIFY; Mechanical ESTIMATE heat)')

    # ------------------------------------------------------------------ tank state at the relight (A1 sizing history)
    H = pd.read_csv(a1_f)
    off = (H.F_cmd.values <= 0.0)
    on_edges = np.where(off[:-1] & ~off[1:])[0]                   # off -> on transitions: the relight is the first one
    i_rel = int(on_edges[0]) + 1 if len(on_edges) else 0
    tank = dict(history=os.path.basename(a1_f), history_sha256_16=sha16(a1_f), t_relight_s=float(H.t.values[i_rel]),
                P_tank_bar=float(H.P_tank.values[i_rel]) / 1e5, T_tank_K=float(H.T_tank.values[i_rel]), m_liq_kg=float(H.m_liq.values[i_rel]),
                m_liq_end_kg=float(H.m_liq.values[-1]), mox_full_thrust_kg_s=float(H.mox.max()))

    # ------------------------------------------------------------------ (a) crest bleed
    P1 = CP.PropsSI('P', 'T', tank['T_tank_K'], 'Q', 0, FL)
    rlt = CP.PropsSI('D', 'P', P1, 'Q', 0, FL); rvt = CP.PropsSI('D', 'P', P1, 'Q', 1, FL)
    sl, hl = CP.PropsSI('S', 'P', P1, 'Q', 0, FL), CP.PropsSI('H', 'P', P1, 'Q', 0, FL)
    sv, hv = CP.PropsSI('S', 'P', P1, 'Q', 1, FL), CP.PropsSI('H', 'P', P1, 'Q', 1, FL)
    Gv, Ptv = g_hem(P1, sv, hv, PAMB)
    Gl_hem, Ptl = g_hem(P1, sl, hl, PAMB)
    Gl_spi = math.sqrt(2 * rlt * (P1 - PAMB))
    Gl = 0.5 * (Gl_spi + Gl_hem)                                  # Dyer, k = 1 (saturated liquid)
    qv_per_A = CD * Gv / rvt                                      # m3/s of line vapour per m2 of orifice
    bleed = {}
    for Vc in (27.87, 34.0, 38.66, 44.0):
        for T in (0.30, 0.50):
            A = Vc * 1e-6 / (T * qv_per_A)
            mdot_l = CD * Gl * A
            bleed[f'{Vc:g}cm3|{T:.2f}s'] = dict(orifice_d_mm=1e3 * math.sqrt(4 * A / math.pi), A_mm2=A * 1e6, open_time_cmd_s=MARGIN * T,
                                               vapour_g=Vc * rvt / 1e3, liquid_g_s=1e3 * mdot_l,
                                               lost_g_vapour_full=Vc * rvt / 1e3 + 1e3 * mdot_l * (MARGIN - 1) * T,
                                               lost_g_primed=1e3 * mdot_l * MARGIN * T,
                                               fail_open_fraction_of_full_flow=mdot_l / tank['mox_full_thrust_kg_s'],
                                               fail_open_vs_ignition_flow_35g_s=1e3 * mdot_l / 35.0)
    # residual at the lift for each heat case: bore-leg term + U boiling x (gap + E0->E1)
    bore_term = max(V_bore, V_bore * DEAD / PURGE)
    resid = {}
    for case, pk in pockets.items():
        r = pk['U_boil_rate_end_cm3_s']
        for gap in (0.0, 0.5, 1.0):
            V = bore_term + r * (gap + e1)
            resid[f'{case}|gap{gap:.1f}s'] = dict(U_boil_rate_cm3_s=r, residual_cm3=dict(median=float(np.median(V)), max=float(V.max())),
                                                  P_abort={f'W{W:.2f}': pab(V, W) for W in (0.65, 0.85, 1.05)})
    opt_a = dict(line_state=dict(P1_bar=P1 / 1e5, T_K=tank['T_tank_K'], rho_l=rlt, rho_v=rvt), Cd=CD, timing_margin=MARGIN,
                 G_vapour_choked_kg_m2s=Gv, Pt_vapour_bar=Ptv / 1e5, G_liquid_dyer_kg_m2s=Gl, G_liquid_hem=Gl_hem, G_liquid_spi=Gl_spi,
                 lost_primed_over_V_kg_m3=MARGIN * Gl / Gv * rvt, sizing=bleed, residual_at_lift=resid,
                 tag='DERIVED: CoolProp HEM / Dyer (k = 1) fluxes, Cd 0.70 and 25 % timing margin ASSUMED; residual model as relight_vapour_states_v2p4')

    # ------------------------------------------------------------------ (b) wider W
    opt_b = {case: dict(W_for_P_abort_0_s={w: max(pk['windows'][w][l]['W_for_P_abort_0_s'] for l in ('bore_leg_refilled', 'bore_leg_dry'))
                                           for w in pk['windows']},
                        P_abort_W1p05={w: max(pk['windows'][w][l]['P_abort']['W1.05'] for l in ('bore_leg_refilled', 'bore_leg_dry'))
                                       for w in pk['windows']}) for case, pk in pockets.items()}
    opt_b['vapour_full_44cm3'] = dict(W_for_P_abort_0_s=W_req(44.0), P_abort={f'W{W:.2f}': pab(44.0, W) for W in (0.65, 0.76, 0.85, 0.93, 1.05)})
    opt_b['vapour_full_32.6cm3'] = dict(W_for_P_abort_0_s=W_req(32.6), P_abort={f'W{W:.2f}': pab(32.6, W) for W in (0.65, 0.76, 0.85, 0.93, 1.05)})
    opt_b['SIL_S11_minimum_W_44cm3_s'] = dict(prep=0.76, direct=0.93, tag='SIM Electronics SIL S11 (coordinator relay 2026-10-13)')

    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/vapour_options_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs=dict(relight_vapour_order=sha16(os.path.join(d, 'relight_vapour_order_v2p4.json')),
                           coast_migration=sha16(os.path.join(d, 'coast_migration_v2p4.json')),
                           relight_vapour_states=sha16(os.path.join(d, 'relight_vapour_states_v2p4.json')),
                           mech_budget=dict(file=budget_f, sha256_16=sha16(budget_f))),
               checks=dict(heat_mapping=chk, distribution=dist_chk), heat_cases=pockets, option_d=opt_d, a1_tank_at_relight=tank,
               option_a=opt_a, option_b=opt_b,
               tags=dict(heat='Mechanical ESTIMATE (segment_heat_budget_v1, six cases)', pockets='DERIVED (flow-order model)',
                         latency='SIM on ASSUMED delays (post_abort_pocket model)'))
    json.dump(out, open(out_f, 'w'), indent=1)
    print('checks', json.dumps(out['checks']))
    for case, pk in pockets.items():
        w = pk['windows']
        print(f'{case:24s} Q_U {pk["heat"]["Q_U_J"]:7.1f} J  Q_R {pk["heat"]["Q_route_J"]:6.1f} J  U rate {pk["U_boil_rate_end_cm3_s"]:6.2f} route {pk["route_boil_rate_end_cm3_s"]:5.2f} cm3/s | '
              + ' '.join(f'{k}: Vg {v["V_generated_U_cm3"]:.1f} Veff {v["bore_leg_dry"]["V_eff_cm3"]:.1f}/{v["bore_leg_refilled"]["V_eff_cm3"]:.1f} '
                         f'Pab65 {v["bore_leg_dry"]["P_abort"]["W0.65"]:.2f}/{v["bore_leg_refilled"]["P_abort"]["W0.65"]:.2f} '
                         f'Pab85 {v["bore_leg_dry"]["P_abort"]["W0.85"]:.2f}/{v["bore_leg_refilled"]["P_abort"]["W0.85"]:.2f} '
                         f'Wreq {max(v["bore_leg_dry"]["W_for_P_abort_0_s"], v["bore_leg_refilled"]["W_for_P_abort_0_s"]):.3f}'
                         for k, v in w.items() if k in ('min', 'mech', 'max')))
    print('d: drift times', {k: round(v, 2) for k, v in drift_t.items()})
    print('d: flood', {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in flood.items()})
    print('d: D needed', {k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in need.items()})
    print('d: exposure', {k: round(v, 2) for k, v in t_drogue.items()}, env_td)
    print('tank', tank)
    print('a: G', round(Gv), round(Gl), round(Gl_hem), round(Gl_spi), 'P1', round(P1 / 1e5, 2), 'lost/V', round(opt_a['lost_primed_over_V_kg_m3'], 1))
    for k, v in bleed.items():
        print('a:', k, {kk: round(vv, 3) for kk, vv in v.items()})
    for k, v in resid.items():
        print('a resid:', k, round(v['residual_cm3']['max'], 2), v['P_abort'])
    print('b:', json.dumps({k: v for k, v in opt_b.items() if 'vapour_full' in k}))
    print('wrote', out_f)


if __name__ == '__main__':
    main(*sys.argv[1:5])
