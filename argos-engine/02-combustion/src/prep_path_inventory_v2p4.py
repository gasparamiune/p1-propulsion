"""Prep-path relight: unignited N2O on a LIQUID (primed) line and the vapour purge of the PREPRESS bleed (Combustion v2.4;
lead request 2026-10-13: "the unignited inventory on a LIQUID line on the prep path at W 0.88 s ... I need it to know whether a
prep-path fallback exists at all").

Run 2 (2026-10-13). Run 1 read the PREPRESS as a 0.10 mm bleed lift held 0.06 s; the firmware holds it longer and only when the
segment reads below half the tank pressure or a pressure is invalid. Run 1 is kept: prep_path_inventory_v2p4_run1_bleed0p06.json.

Prep path as coded in Electronics fw v2.8.2 (hub 06-electronics/firmware/src/core/engine_ecu.cpp, PREPRESS state, and config.h;
read as data, hashes below):
  * slow priming (prime_slow) is chosen at PREPRESS entry when P_feed < 0.5 P_tank (absolute) or P_feed / P_tank is invalid;
  * with slow priming the pintle goes to the 0.10 mm bleed lift; the MV opener ramp starts after kBleedSettle 0.06 s and runs
    kMvOpenRampSlow 0.35 s, then holds kMvCockHold 0.15 s; the bleed stays while ts < 0.56 s and the feed does not read primed;
    in flight with an invalid pressure, "primed" = MV OPEN switch made, so the bleed ends at the OPEN switch (<= 0.41 s; bound);
  * without slow priming (valid pressures, segment at P_tank: a primed line, or a vapour-full one) the pintle stays seated
    through the PREPRESS (MV ramp 0.35 s + hold 0.15 s); W counts from the ignition-lift command as on the direct path.
Inventory (liquid line) = bleed admission (0.10 mm, close command at the bleed end) + ignition-lift admission (0.2039 mm) up to W;
hard_start_v2p4.inventory (Dyer cold flow, Cd 0.70 ASSUMED, servo history; everything admitted retained, no throat outflow).
Vapour purged by the bleed from a vapour-full segment: the purge flow scales with the pintle area (lift); at the 0.2039 mm lift
the 44 cm3 segment purges in 0.685 s (0.015555 s/cm3, relight_vapour_order_v2p4), so V = integral(h dt) / (0.2039 mm x 0.015555 s/cm3).
P(abort of a would-be light) for the residual pocket: the same 200 000-sample E1 -> E2 distribution as every v2.4 table (seed 2024).
MV gate check (why the SIL's prep path lights 44 cm3 0.17 s earlier than its direct path): the SIL plant purges vapour only with the
MV more than 50 % open (06-electronics/firmware/sil/plant.cpp). Physically the pocket leaves through the pintle at P_tank and the MV
only has to pass the replacing liquid; pressure drop across the MV-P (Mechanical mv_actuator_v1 Cv 3.64, ESTIMATE; curtain area
proportional to lift) at the purge's liquid-replacement flow, by opening fraction.
usage: python -I prep_path_inventory_v2p4.py DATA_V2P4_DIR MV_ACTUATOR_JSON FW_ENGINE_ECU_CPP FW_CONFIG_H SIL_PLANT_CPP OUT_JSON
"""
from __future__ import annotations
import json, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hard_start_v2p4 as HS
import start_latency_v2p4 as SL

LIFT_IGN = 0.2039e-3
LIFT_BLEED = 0.10e-3
BLEEDS = {'run1_reading_0.06s': 0.06, 'invalid_pressure_to_OPEN_switch_0.41s': 0.41, 'firmware_bound_t_cock_end_0.56s': 0.56}
WS = (0.65, 0.76, 0.88, 0.93, 1.05)
V_SEG = 44.0


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def bleed_lift_integral(t_b):
    """integral of the lift [m s] for a 0.10 mm bleed whose close command comes t_b after the lift command (servo history of HS)."""
    t, H = HS.servo_history(LIFT_BLEED, t_b)
    return float(np.trapezoid(H, t) if hasattr(np, 'trapezoid') else np.trapz(H, t))


def main(d, mv_f, fw_ecu, fw_cfg, sil_plant, out_f):
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    RW = json.load(open(os.path.join(d, 'relight_window_rule_seg44_v2p4.json')))
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    SLJ = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    PA = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
    MV = json.load(open(mv_f))
    # firmware constants this script relies on (fail if the firmware changed them)
    cfg = open(fw_cfg).read(); ecu = open(fw_ecu).read(); plant = open(sil_plant).read()
    for s in ('kBleedSettle_s = 0.060f', 'kMvOpenRampSlow_s = 0.35f', 'kMvCockHold_s = 0.15f', 'kPrimeSlowFrac'):
        assert s in cfg, f'firmware config changed: {s}'
    for s in ('bleed_active_ = prime_slow_ && ts < t_cock_end && !feedPrimed(in);', 'if (!pfeed_ok_ || !ptank_ok_) prime_slow_ = true;',
              'if (!in.pfeed_valid || !in.ptank_valid) return starts_ >= 1 && !stand_;'):
        assert s in ecu, f'firmware PREPRESS logic changed: {s}'
    assert 'if (mv_frac > 0.5 && A > 0.0) {' in plant, 'SIL plant vapour gate changed'
    PURGE = VO['purge_s_per_cm3']
    lifts = J['ignition_lifts']['v']; cold = J['cold_flow_at_ignition_lift']['v']
    # ---- inventories (liquid line)
    res = {}
    for st in ('A1_relight', '15C', '20C', '25C'):
        L = lifts[f'{st}|0.125']; c = cold[f'{st}|0.125']
        bl = {k: 1e3 * HS.inventory(LIFT_BLEED, L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], tb)[0] for k, tb in BLEEDS.items()}
        rows = {}
        for W in WS:
            ign = 1e3 * HS.inventory(LIFT_IGN, L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], W)[0]
            rows[f'W{W:.2f}'] = dict(ignition_lift_g=ign,
                                     prep_valid_pressures_no_bleed_g=ign,
                                     prep_invalid_pressure_bleed_to_OPEN_switch_g=ign + bl['invalid_pressure_to_OPEN_switch_0.41s'],
                                     prep_bleed_to_t_cock_end_bound_g=ign + bl['firmware_bound_t_cock_end_0.56s'],
                                     run1_reading_bleed_0p06s_g=ign + bl['run1_reading_0.06s'])
        chk = {f'{W:.2f}': RW['inventory_vs_W']['v'][st][f'{W:.2f}']['liquid_line_g'] for W in (0.65, 1.05)}
        res[st] = dict(bleed_g=bl, rows=rows, check_vs_window_rule_g=chk,
                       check_ok=bool(all(abs(rows[f'W{float(w):.2f}']['ignition_lift_g'] - v) < 0.05 for w, v in chk.items())))
        assert res[st]['check_ok'], 'ignition-lift inventory does not reproduce relight_window_rule_seg44_v2p4'
    i24 = {}
    for W in WS:
        k = f'W{W:.2f}'
        i24[k] = {q: res['20C']['rows'][k][q] + 0.8 * (res['25C']['rows'][k][q] - res['20C']['rows'][k][q]) for q in res['20C']['rows'][k]}
    res['24C_interp'] = dict(rows=i24, bleed_g={q: res['20C']['bleed_g'][q] + 0.8 * (res['25C']['bleed_g'][q] - res['20C']['bleed_g'][q])
                                               for q in res['20C']['bleed_g']})
    # ---- E1 -> E2 distribution (as route_void_bracket_v2p4 / segment_void_balance_v2p4)
    rws = SLJ['part1_runs']['v']; lf = SLJ['ignition_lifts']
    pool = [r for r in rws if r['ramp'] == 2500.0 and r['F_cmd'] in (200.0, 500.0) and r['state'] == 'A1_relight'
            and r['frac'] == 0.125 and r.get('loop_K', 0.0) == 15.0]
    N = 200000; rng = np.random.default_rng(2024)
    h = lf['A1_relight|0.125']['lift_m']; t_lift = SL.T_CMD + h / SL.V_PINTLE + 0.010
    idx = rng.integers(0, len(pool), N)
    tc = np.array([np.nan if q['t_conf_s'] is None else q['t_conf_s'] for q in pool])[idx]
    _ = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)
    ig = rng.uniform(0.05, 0.30, N)
    base = t_lift + ig + tc; base = base[np.isfinite(base)]
    assert abs(float(base.max()) - PA['E1_E2_liquid_s']['max']) < 1e-9, 'distribution not reproduced'
    # ---- vapour purged by the bleed and the abort probability of a vapour-full 44 cm3 segment on the prep path
    vap = {}
    for k, tb in dict(no_bleed_valid_pressures=0.0, **BLEEDS).items():
        V_p = 0.0 if tb == 0.0 else min(V_SEG, bleed_lift_integral(tb) / (LIFT_IGN * PURGE))
        pocket = V_SEG - V_p
        vap[k] = dict(bleed_close_cmd_s=tb, vapour_purged_cm3=V_p, pocket_at_lift_cm3=pocket,
                      W_for_P_abort_0_s=float(base.max() + PURGE * pocket),
                      P_abort={f'W{W:.2f}': float(np.mean(base + PURGE * pocket > W)) for W in WS})
    # ---- MV gate check
    Cv = MV['B_balanced_poppet_MVP']['Cv']; CdA_full = Cv * 1.699e-5
    rho_l = VO['properties']['rho_l']
    Q_purge = 1e-6 / PURGE                                   # m3/s of vapour leaving at the ignition lift = liquid replacing it
    mgate = {f'{f:.2f}': dict(dP_bar=(rho_l * Q_purge / (CdA_full * f)) ** 2 / (2 * rho_l) / 1e5) for f in (0.05, 0.10, 0.25, 0.45, 1.0)}
    out = dict(version='v2.4', run=2, date='2026-10-13', script='02-combustion/src/prep_path_inventory_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs=dict(**{k: sha16(os.path.join(d, k)) for k in ('hard_start_v2p4.json', 'relight_window_rule_seg44_v2p4.json',
                                                                    'relight_vapour_order_v2p4.json', 'start_latency_v2p4.json', 'post_abort_pocket_v2p4.json')},
                           mv_actuator=dict(file=mv_f, sha256_16=sha16(mv_f), Cv=Cv, tag='Mechanical ESTIMATE'),
                           firmware_engine_ecu_cpp=dict(file=fw_ecu, sha256_16=sha16(fw_ecu)), firmware_config_h=dict(file=fw_cfg, sha256_16=sha16(fw_cfg)),
                           sil_plant_cpp=dict(file=sil_plant, sha256_16=sha16(sil_plant))),
               prep_path=dict(bleed_lift_m=LIFT_BLEED, ignition_lift_m=LIFT_IGN, W_from_ignition_lift_cmd=True, bleed_cases_s=BLEEDS,
                              rule='bleed only with P_feed < 0.5 P_tank or an invalid pressure (fw v2.8.2); a liquid line with valid pressures has no bleed'),
               states=res, vapour_full_prep_path=vap, mv_gate_check=dict(Q_replacement_m3_s=Q_purge, CdA_full_m2=CdA_full, by_opening_fraction=mgate),
               accepted_flight_inventory_g=26.6,
               tag='DERIVED (hard_start_v2p4 inventory: Dyer cold flow, Cd 0.70 ASSUMED, servo history; everything admitted retained; '
                   'purge scaled with lift; SIM on ASSUMED delays for P_abort)')
    json.dump(out, open(out_f, 'w'), indent=1)
    for st, r in res.items():
        print(st, 'bleed g', {k: round(v, 2) for k, v in r['bleed_g'].items()})
        for W, x in r['rows'].items():
            print('   ', W, {k: round(v, 2) for k, v in x.items()})
    for k, v in vap.items():
        print('vapour-full prep', k, 'purged %.2f cm3 pocket %.2f W_req %.3f' % (v['vapour_purged_cm3'], v['pocket_at_lift_cm3'], v['W_for_P_abort_0_s']),
              {w: round(p, 4) for w, p in v['P_abort'].items()})
    print('MV gate dP [bar] by opening fraction', {f: round(x['dP_bar'], 4) for f, x in mgate.items()})
    print('wrote', out_f)


if __name__ == '__main__':
    main(*sys.argv[1:7])
