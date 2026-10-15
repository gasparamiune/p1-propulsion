"""Unignited N2O on a LIQUID (primed) line on the prep path (Combustion v2.4; lead request 2026-10-13: "the unignited
inventory on a LIQUID line on the prep path at W 0.88 s").

Prep (unprimed / UNKNOWN) path, fw v2.8.x as modelled in REPORT v2.4 section 7: PREPRESS before E0 = a 0.10 mm bleed lift
held for 0.06 s while the MV opens, then the pintle reseats (prepress 0.50-0.56 s in all); E0 torch, E1 ignition lift
0.2039 mm after the 0.16 s gate; abort deadline W from the ignition-lift command.
Inventory = prepress admission (0.10 mm lift, close command 0.06 s after the lift command, servo history and Dyer flow of
hard_start_v2p4, Cd 0.70 ASSUMED) + ignition-lift admission up to W (relight_window_rule_v2p4 liquid-line method).
Bounding convention of hard_start_v2p4: everything admitted is retained (no throat outflow before ignition), full tank
pressure at the pintle during the prepress (a primed segment is at tank pressure). The prepress row uses the cold-flow
chamber pressure of the ignition lift (P2) and, as a bound, ambient pressure.
usage: python -I prep_path_inventory_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import json, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hard_start_v2p4 as HS

LIFT_IGN = 0.2039e-3
LIFT_PRE, T_PRE = 0.10e-3, 0.06
WS = (0.65, 0.76, 0.88, 0.93, 1.05)


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def main(d, out_f):
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    RW = json.load(open(os.path.join(d, 'relight_window_rule_seg44_v2p4.json')))
    lifts = J['ignition_lifts']['v']; cold = J['cold_flow_at_ignition_lift']['v']
    res = {}
    for st in ('A1_relight', '15C', '20C', '25C'):
        L = lifts[f'{st}|0.125']; c = cold[f'{st}|0.125']
        pre_P2 = HS.inventory(LIFT_PRE, L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], T_PRE)[0]
        pre_amb = HS.inventory(LIFT_PRE, L['P_tank_Pa'], L['T_tank_K'], HS.PAMB, T_PRE)[0]
        rows = {}
        for W in WS:
            ign = HS.inventory(LIFT_IGN, L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], W)[0]
            rows[f'W{W:.2f}'] = dict(ignition_lift_g=1e3 * ign, prepress_g=1e3 * pre_P2, prepress_ambient_bound_g=1e3 * pre_amb,
                                     total_g=1e3 * (ign + pre_P2), total_bound_g=1e3 * (ign + pre_amb))
        # cross-check of the ignition-lift rows against relight_window_rule_seg44_v2p4 (same method)
        chk = {f'{W:.2f}': RW['inventory_vs_W']['v'][st][f'{W:.2f}']['liquid_line_g'] for W in (0.65, 1.05)}
        res[st] = dict(rows=rows, check_vs_window_rule_g=chk,
                       check_ok=bool(all(abs(rows[f'W{float(w):.2f}']['ignition_lift_g'] - v) < 0.05 for w, v in chk.items())))
    # 24 C interlock by linear interpolation 20 -> 25 C
    i24 = {}
    for W in WS:
        k = f'W{W:.2f}'
        i24[k] = {q: res['20C']['rows'][k][q] + 0.8 * (res['25C']['rows'][k][q] - res['20C']['rows'][k][q]) for q in res['20C']['rows'][k]}
    res['24C_interp'] = dict(rows=i24)
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/prep_path_inventory_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={k: sha16(os.path.join(d, k)) for k in ('hard_start_v2p4.json', 'relight_window_rule_seg44_v2p4.json')},
               prep_path=dict(prepress_lift_m=LIFT_PRE, prepress_close_cmd_after_s=T_PRE, ignition_lift_m=LIFT_IGN, W_from_ignition_lift_cmd=True),
               states=res, accepted_flight_inventory_g=26.6,
               tag='DERIVED (hard_start_v2p4 inventory: Dyer cold flow, Cd 0.70 ASSUMED, servo history; everything admitted retained)')
    json.dump(out, open(out_f, 'w'), indent=1)
    for st, r in res.items():
        print(st, {W: {k: round(v, 2) for k, v in x.items()} for W, x in r['rows'].items()}, r.get('check_ok'))
    print('wrote', out_f)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
