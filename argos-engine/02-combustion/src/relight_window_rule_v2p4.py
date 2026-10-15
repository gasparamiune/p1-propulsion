"""Graded relight abort window against the 20 g stand cap (Combustion v2.4, RC-02 / RC-03; lead request 2026-10-13).

Question (lead): with the NC valve opened at E0 (pintle seated) and the lift at E1, a hot relight on the stand whose
manifold alone boils is mostly a liquid-line case; at the 0.65 s deadline it admits about 25 g, above the 20 g
stand-protection cap. Propose a graded rule (whole-line vapour: full 0.25 s extension; manifold-only vapour: an
extension sized to the 0.065 s purge plus margin) that keeps every stand case at or below 20 g, with inventories at
the author's cold flow and at the SIL flow.
Inputs:
  * author inventory model hard_start_v2p4.inventory (Dyer cold flow, Cd 0.70 ASSUMED, servo history, abort at W after
    the lift command, close command 6.5 ms later), A1 relight state and 20 C, 12.5 % lift (hard_start_v2p4.json);
  * SIL inventories (SIM, Electronics firmware v2.7, CHANGELOG 2026-10-13) scaled linearly in W with the SIL-implied hold
    flow 51.6 g/s (DERIVED in sil_inventory_bound_v2p4): cold relight 11.11 g at 0.35 s;
  * vapour-line cases: the vapour in the segment purges first (full segment 21.42 cm3, 0.31 s; manifold 4.51 cm3, 0.065 s,
    low_inlet_check_v2p3 C7 scaled by volume), then liquid; vapour mass = volume x saturated-vapour density at the tank
    state (CoolProp, DERIVED);
  * false-abort rates from relight_latency_sup_v2p4.json (valve open at E0: the 'preopened' and 'manifold' cases).
usage: python -I relight_window_rule_v2p4.py DATA_V2P4_DIR [v2p8 [SEG_CM3]]   (v2p8: 0.2039 mm lift, segment 32.6 cm3 or SEG_CM3, hot-end pocket)
"""
from __future__ import annotations
import json, os, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hard_start_v2p4 as HS

V_SEG, V_MAN = 21.42e-6, 4.51e-6
T_PURGE_SEG = 0.31
T_PURGE_MAN = T_PURGE_SEG * V_MAN / V_SEG
SIL_FLOW = (26.59 - 11.11) * 1e-3 / 0.30
WS = (0.40, 0.45, 0.50, 0.52, 0.55, 0.60, 0.65)


def inv_liquid(L, c, W):
    return HS.inventory(L['lift_m'], L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], W)[0]


def inv_vapour_first(L, c, W, V_vap, t_purge):
    """Vapour of the given volume purges first over t_purge (vapour mass at saturation, tank temperature), then liquid
    flows until the pintle seats: liquid = full-liquid inventory minus the liquid that would have flowed before t_purge."""
    rho_v = CP.PropsSI('D', 'T', L['T_tank_K'], 'Q', 1, 'NitrousOxide')
    m_v = V_vap * rho_v
    t, H = HS.servo_history(L['lift_m'], W)
    m = np.array([HS.mdot_cold(hh, L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa']) if hh > 1e-8 else 0.0 for hh in H])
    keep = t >= t_purge
    tr = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz
    m_l = float(tr(m * keep, t))
    return m_v + m_l, m_v, m_l


def main_v2p8(d, seg_cm3=32.6, lift_m=0.2039e-3):
    """v2.4b (lead relays 2026-10-13): Electronics v2.8 default ignition lift 0.2039 mm, Mechanical segment 32.6 cm3. Whole-segment
    vapour purge scales with volume (0.31 s x V/21.42, DERIVED); manifold 4.51 cm3 (0.065 s); hot-end pocket 8 cm3 (0.116 s).
    The SIL-scaled columns of the first run are withdrawn (the 51.6 g/s came from a 0.301 mm lift; Electronics v2.8 now gives
    37.1 g/s at 20 C at 0.2039 mm, which this model reproduces within 1 %)."""
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    cold = J['cold_flow_at_ignition_lift']['v']; lifts = J['ignition_lifts']['v']
    V_seg = seg_cm3 * 1e-6; t_seg = T_PURGE_SEG * seg_cm3 / 21.42; t_hot = T_PURGE_SEG * 8.0 / 21.42
    inv = {}
    for st in ('15C', '20C', '25C', 'A1_relight'):
        L = dict(lifts[f'{st}|0.125']); L['lift_m'] = lift_m; c = cold[f'{st}|0.125']
        rows = {}
        for W in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10):
            liq = inv_liquid(L, c, W)
            vs = inv_vapour_first(L, c, W, V_seg, t_seg)
            vm = inv_vapour_first(L, c, W, V_MAN, T_PURGE_MAN)
            vh = inv_vapour_first(L, c, W, 8.0e-6, t_hot)
            rows[f'{W:.2f}'] = dict(liquid_line_g=1e3 * liq, whole_segment_vapour_g=1e3 * vs[0], whole_segment_vapour_vapour_part_g=1e3 * vs[1],
                                    manifold_vapour_g=1e3 * vm[0], hot_end_8cm3_vapour_g=1e3 * vh[0])
        inv[st] = rows
        print(st, {W: {k: round(v, 1) for k, v in r.items()} for W, r in rows.items() if W in ('0.35', '0.40', '0.50', '0.65', '0.85')}, flush=True)
    out = dict(version='v2.4b', date='2026-10-13', script='02-combustion/src/relight_window_rule_v2p4.py (main_v2p8)',
               inputs=dict(lift_m=lift_m, V_segment_m3=V_seg, t_purge_segment_s=t_seg, V_manifold_m3=V_MAN, t_purge_manifold_s=T_PURGE_MAN,
                           V_hot_end_m3=8.0e-6, t_purge_hot_end_s=t_hot,
                           tags=dict(lift='Electronics v2.8 default (LEAD accepted 2026-10-13)', segment='Mechanical CHANGELOG 2026-10-13 (32.6 cm3)',
                                     purge='SIM C7 0.31 s for 21.42 cm3, scaled with volume (DERIVED)', hot_end='ASSUMED pocket bound from 18-58 W manifold heating (Mechanical)')),
               inventory_vs_W=dict(v=inv, tag='DERIVED hard_start_v2p4 inventory (Dyer, Cd 0.70 ASSUMED, servo history, W from the lift command, close command 6.5 ms later)'),
               superseded='relight_window_rule_v2p4.json (21.42 cm3, author lift, SIL-scaled columns)')
    fn = os.path.join(d, f'relight_window_rule_seg{seg_cm3:g}_v2p4.json')
    json.dump(out, open(fn, 'w'), indent=1, default=float)
    print('wrote', fn)


def main(d):
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    lifts = J['ignition_lifts']['v']; cold = J['cold_flow_at_ignition_lift']['v']
    R = json.load(open(os.path.join(d, 'relight_latency_sup_v2p4.json')))['cases']
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/relight_window_rule_v2p4.py',
               inputs=dict(V_segment_m3=V_SEG, V_manifold_m3=V_MAN, t_purge_segment_s=T_PURGE_SEG, t_purge_manifold_s=T_PURGE_MAN,
                           SIL_hold_flow_kg_s=SIL_FLOW, cap_g=20.0,
                           tags=dict(volumes='SIM low_inlet_check_v2p3 / safing_relief_v2p4 (CAD v3.3 stations)',
                                     purge='SIM C7 0.31 s, manifold scaled by volume (DERIVED)', SIL='SIM Electronics v2.7, scaled (DERIVED)',
                                     cap='LEAD 2026-10-13 (stand-protection criterion)')))
    inv = {}
    for st in ('A1_relight', '20C'):
        L = lifts[f'{st}|0.125']; c = cold[f'{st}|0.125']
        rows = {}
        for W in WS:
            liq = inv_liquid(L, c, W)
            vs = inv_vapour_first(L, c, W, V_SEG, T_PURGE_SEG)
            vm = inv_vapour_first(L, c, W, V_MAN, T_PURGE_MAN)
            rows[f'{W:.2f}'] = dict(author_liquid_line_g=1e3 * liq, author_whole_line_vapour_g=1e3 * vs[0], author_whole_line_vapour_vapour_g=1e3 * vs[1],
                                    author_manifold_vapour_g=1e3 * vm[0],
                                    SIL_liquid_line_g=11.11 + 1e3 * SIL_FLOW * (W - 0.35),
                                    SIL_whole_line_vapour_g=3.38 + 15.0 * max(W - 0.35, 0.0) / 0.30)
        inv[st] = rows
        for W, r in rows.items():
            print(st, W, {k: round(v, 2) for k, v in r.items()}, flush=True)
    out['inventory_vs_W'] = dict(v=inv, tag='DERIVED; W from the ignition-lift command; SIL whole-line vapour scaled from 18.38 g at 0.65 s '
                                 '(3.38 g vapour) assuming the liquid arrives at about 0.35 s as in the SIL')
    fa = {}
    for k in ('relight_valve_preopened_liquid', 'relight_manifold_vapour_unseen_U01', 'relight_manifold_vapour_unseen_full',
              'relight_valve_preopened_vapour_U01', 'relight_valve_preopened_full_vapour'):
        v = R[f'{k}|0.125|loopK15']
        fa[k] = dict(false_abort_vs_W=v['false_abort_vs_W_from_E1'], E1_E2_max_s=v['E1_E2_s']['max'], E1_E2_p999_s=v['E1_E2_s']['p999'])
    out['false_abort'] = dict(v=fa, tag='SIM relight_latency_sup_v2p4 (ASSUMED distributions, 200k samples, loop K15); valve open at E0')
    fn = os.path.join(d, 'relight_window_rule_v2p4.json')
    json.dump(out, open(fn, 'w'), indent=1, default=float)
    print('wrote', fn)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2] == 'v2p8':
        main_v2p8(sys.argv[1], seg_cm3=float(sys.argv[3]) if len(sys.argv) > 3 else 32.6)
    else:
        main(sys.argv[1])
