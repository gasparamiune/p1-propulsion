"""Hard-start consequence of a wider relight abort window (Combustion v2.4; coordinator relay of Electronics SIL S11, 2026-10-13).

Question: for a vapour-full 44 cm3 segment lit at W 0.76 s (SIL prep path) or 0.93 s (SIL direct path), and at the
proposed W 1.05 s, what unignited N2O is in the chamber at light, and what is the hard-start peak against MEOP 45 bar, given
that the first part of the admitted N2O is vapour?
Method:
  1. Inventories admitted from the ignition-lift command to the light at W, interpolated from relight_window_rule_seg44_v2p4.json
     (hard_start_v2p4.inventory: Dyer cold flow, Cd 0.70 ASSUMED, Electronics v2.8 lift 0.2039 mm; vapour-first rows: the 44 cm3
     of saturated vapour passes first over 0.637 s, then liquid). The ECU applies the same W to a primed segment, so the
     liquid-line row at the same W is the bounding inventory of the rule.
  2. Vapour resident in the chamber during the purge: the pocket vapour throttled isenthalpically from the line state to the
     cold-flow chamber pressure (CoolProp), in the 300.9 cm3 gas path, against the flashed vapour of a liquid start
     (cold_flow_at_ignition_lift).
  3. Credible case (two-component, three-node network of hard_start_multivolume_v2p4, flight = no disc, unchanged inputs):
     fast part = chamber vapour + spray in transit 0.06 s at the head, reacting top-hat over tf; slow pool = the rest of the
     inventory, evaporation-limited at q over the wetted area; peaks at every inventory of step 1 up to 40.3 g.
usage: python -I hard_start_wide_window_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import json, math, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hard_start_v2p4 as HS
import hard_start_multivolume_v2p4 as MVN

FL = 'NitrousOxide'
WS = (0.65, 0.76, 0.93, 1.05)


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def interp_row(rows, W, key):
    Wk = sorted(float(k) for k in rows)
    x = np.array(Wk); y = np.array([rows[f'{w:.2f}'][key] for w in Wk])
    return float(np.interp(W, x, y))


def main(d, out_f):
    RW = json.load(open(os.path.join(d, 'relight_window_rule_seg44_v2p4.json')))
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    inv = {}
    for st, rows in RW['inventory_vs_W']['v'].items():
        inv[st] = {f'W{W:.2f}': dict(primed_liquid_line_g=interp_row(rows, W, 'liquid_line_g'),
                                     vapour_full_44_total_g=interp_row(rows, W, 'whole_segment_vapour_g'),
                                     vapour_full_44_vapour_part_g=interp_row(rows, W, 'whole_segment_vapour_vapour_part_g'))
                   for W in WS}
        for W in WS:
            r = inv[st][f'W{W:.2f}']; r['vapour_full_44_liquid_part_g'] = r['vapour_full_44_total_g'] - r['vapour_full_44_vapour_part_g']
    # 2. chamber-resident vapour during the purge
    cold = J['cold_flow_at_ignition_lift']['v']
    lifts = J['ignition_lifts']['v']
    resid = {}
    for st in ('A1_relight', '20C', '25C'):
        L = lifts[f'{st}|0.125']; c = cold[f'{st}|0.125']
        P1 = CP.PropsSI('P', 'T', L['T_tank_K'], 'Q', 1, FL); hv = CP.PropsSI('H', 'T', L['T_tank_K'], 'Q', 1, FL)
        P2 = c['P2_Pa']
        T2 = CP.PropsSI('T', 'P', P2, 'H', hv, FL); r2 = CP.PropsSI('D', 'P', P2, 'H', hv, FL)
        resid[st] = dict(line_P_bar=P1 / 1e5, chamber_P_bar=P2 / 1e5, T_after_throttle_K=T2, rho_kg_m3=r2,
                         purge_vapour_in_chamber_g=r2 * 300.9e-6 * 1e3,
                         liquid_start_vapour_in_chamber_g=c['vapour_in_chamber_g']['reviewer_300.9cm3'],
                         purge_vapour_flow_g_s=44.0 * CP.PropsSI('D', 'T', L['T_tank_K'], 'Q', 1, FL) / 1e3 / RW['inputs']['t_purge_segment_s'])
    # 3. credible case at the inventories of step 1 (flight: no disc)
    prods = {'20C': HS.products('dec', 293.15), 'A1_relight': HS.products('dec', 286.70), '25C': HS.products('dec', 298.15)}
    A_wet = math.pi * 0.025 * 0.230 + math.pi / 4 * 0.054 ** 2
    cred = {}
    for st in ('A1_relight', '20C', '25C'):
        c = cold[f'{st}|0.125']; prod_s = prods[st]
        V3 = MVN.volumes(0.0499, 0.025); Vs = sum(V3)
        m_vap = c['vapour_in_chamber_g']['reviewer_300.9cm3'] * 1e-3 * Vs / 300.9e-6
        m_s = c['liquid_flow_kg_s'] * 0.06; m_f = m_vap + m_s
        split_f = [(m_vap * V3[0] / Vs + m_s) / m_f, m_vap * V3[1] / Vs / m_f, m_vap * V3[2] / Vs / m_f]
        masses = sorted({round(v, 1) for W in WS for k, v in inv[st][f'W{W:.2f}'].items() if k in ('primed_liquid_line_g', 'vapour_full_44_total_g')} | {26.6})
        for restr in ('entrance', 'exit'):
            for cd in (1.0, 0.65):
                net = MVN.make_net(prod_s, V3, 0.025, cd, restr, 'none')
                for mg in masses:
                    m_pool = max(mg * 1e-3 - m_f, 0.0)
                    for q in (0.5e6, 2.0e6):
                        tau_pool = max(m_pool * 375e3 / (q * A_wet), 1e-3)
                        for tf in (1e-3, 5e-3):
                            pk = net.peak(m_pool, tau_pool, [v / Vs for v in V3], m_fast=m_f, tau_fast=tf, split_fast=split_f)
                            cred[f'{st}|{restr}|Cd{cd}|{mg}g|q{q/1e6:.1f}|tf{tf*1e3:.0f}ms'] = dict(m_fast_g=m_f * 1e3, m_pool_g=m_pool * 1e3,
                                                                                                    tau_pool_s=tau_pool, peak_bar=[x / 1e5 for x in pk])
        print('credible', st, 'done', flush=True)
    # summary: max head-node peak per state / entrance, over inventories, by tf
    summ = {}
    for k, v in cred.items():
        st, restr, cd, mg, q, tf = k.split('|')
        key = f'{st}|{restr}|{cd}|{tf}'
        s = summ.setdefault(key, dict(min_bar=1e9, max_bar=0.0, inventories_g=[]))
        s['min_bar'] = min(s['min_bar'], v['peak_bar'][0]); s['max_bar'] = max(s['max_bar'], v['peak_bar'][0]); s['inventories_g'].append(float(mg[:-1]))
    for s in summ.values():
        s['inventories_g'] = sorted(set(s['inventories_g']))
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/hard_start_wide_window_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={k: sha16(os.path.join(d, k)) for k in ('relight_window_rule_seg44_v2p4.json', 'hard_start_v2p4.json', 'relight_vapour_order_v2p4.json')},
               inventory_at_W=inv, purge_vapour_resident=resid, credible_case=cred, credible_summary_head_node=summ,
               MEOP_bar=45.0, proof_bar=67.5,
               tags=dict(inventory='DERIVED (hard_start_v2p4.inventory, ASSUMED Cd)', resident='DERIVED (CoolProp throttling)',
                         credible='ESTIMATE: ASSUMED inputs as hard_start_multivolume_v2p4 section 3 (flight, no disc)'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    for st, r in inv.items():
        print(st, {W: {k: round(v, 2) for k, v in x.items()} for W, x in r.items()})
    print('resident', json.dumps({k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in resid.items()}))
    for k, s in sorted(summ.items()):
        print(k, round(s['min_bar'], 2), round(s['max_bar'], 2), s['inventories_g'])
    print('wrote', out_f)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
