"""Run counts and N2O budgets for the T1-T4 regression series and for CF-4 (Combustion v2.4b, 2026-10-13).

REV-COMB-3 R3-07/R3-08 and LEAD CHANGELOG line 194 (8): counts and N2O budgets, and the stand tank against T1 at 2t = 8 s.
  T1-T4: oxidiser per firing = sum over the planned throttle levels of mdot_ox(F) x duration, mdot_ox from the S230 throttle map (SIM
  grain_q1d v2 nominal law; Cd 0.70, eta_c* 0.92) at P_tank 4.0 / 4.5 / 5.0 MPa, taking the largest value over the map's port diameters
  25-45 mm (conservative for budgeting); every law firing kind at t and at 2t (two-duration differential); plus the DC-D duty cycle
  (T4) integrated from the S230 ground record.  Starts, tail-offs and chill-down are covered by a 10 % allowance (ASSUMED).
  CF-4: runs = states x attitude settings x repeats (>= 5, CF-4 §4); N2O per run = purge vent (<= 76 g, P5 limit) + the lift flow at
  THE start-level lift (0.21776 mm at the A1 state, LEAD 203 (7); 0.2039 mm kept as a sensitivity) over the recorded window + the
  segment inventory used to set the initial state (37.8 g at 20 C on CAD v3.4.1, REPORT §7.4 A6;
  re-baselined on v3.5.1).
Tank capacities: flight tank 2.0 kg N2O load (combustion.json); ground tank 15 L, 10.4 kg (ASSUMED in REPORT §2.7 and Table 4.4; the
founders' stand tank is MISSING).
Tags: DERIVED on SIM map flows and ASSUMED durations, repeats and allowances; for planning only.
usage: python -I test_budgets_v2p4b.py THROTTLE_MAP_S230 DC_D_S230_CSV OUT_JSON
"""
from __future__ import annotations
import csv, hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP

EXPECT_MAP = '4f2e6d846f7253da'
F_FULL = 500.0
KINDS = {                                              # (label, [(fraction of 500 N, seconds at t)])
    'T1_100pct': [(1.0, 4.0)],
    'T1_50pct': [(0.5, 4.0)],
    'T2_100_50_25pct': [(1.0, 2.0), (0.5, 2.0), (0.25, 2.0)],
    'T3_20pct': [(0.2, 4.0)],
    'T3_12p5pct': [(0.125, 4.0)],
}
ALLOW = 0.10                                           # starts, tail-offs, chill-down (ASSUMED)
N_REPEATS = (1, 2, 4, 8)
FLIGHT_LOAD_KG = 2.0
GROUND_TANK_KG = 10.4
N2_QUENCH_KG = 60.0 * 0.010                            # REPORT §10.2: >= 60 s at >= 10 g/s per firing
# CF-4
CF4_STATES = ('IS-1', 'IS-2', 'IS-3')
CF4_ATT = (('0deg', 1), ('2deg_az45', 1), ('2deg_az180', 1), ('3deg_az45', 1), ('3deg_az180', 1))
CF4_ATT4 = (('4deg_az45', 1), ('4deg_az180', 1))
CF4_REPEATS = 5
VENT_MAX_G = 76.0
LIFT_FLOW_G_S = 34.81                                  # 0.2039 mm at the A1 state (fa1_envelope_v2p4a state r_inj 0.03481 kg/s)
H_V28_MM, H_START_A1_MM = 0.2039, 0.21776             # v2.8 default (20 C row) and THE start-level lift at the A1 state (LEAD 203 (7); ECU row)
LIFT_FLOW_START_G_S = LIFT_FLOW_G_S * H_START_A1_MM / H_V28_MM   # flow linear in lift between the two (DERIVED)
LIFT_WINDOW_S = 1.5                                    # record window after the lift (O-3 records 1.5 s; P1 + P2 need <= 0.67 s)
SEGMENT_G = 37.8                                       # REPORT §7.4 A6 (CAD v3.4.1, 20 C)
T_A1 = 286.7                                           # K, A1 relight tank state (REPORT §2.8)
PROBE_RESPONSE_S = 5e-3                                # CF-4 §3 void-probe response
LAT_CMD_S, LAG_S, V_PINTLE_MM_S = 6.5e-3, 10e-3, 16.7     # REPORT §7.4 latencies: command to servo, servo lag, pintle speed (DERIVED)
V_ZERO_CM3, S_PER_CM3 = 18.86, 0.015555                   # CF-4 P1 basis (zero-abort volume, s/cm3 at 0.2039 mm)


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main(map_fn, dcd_fn, out_f):
    assert sha16(map_fn) == EXPECT_MAP, sha16(map_fn)
    rows = [r for r in csv.reader(open(map_fn)) if r and not r[0].startswith('#')]
    h = rows[0]; rows = rows[1:]
    col = lambda r, k: float(r[h.index(k)])
    mox = {}
    for P in (4.0e6, 4.5e6, 5.0e6):
        best = {}
        for D in sorted({col(r, 'D_port_m') for r in rows}):
            sel = sorted([r for r in rows if abs(col(r, 'P_tank_Pa') - P) < 1 and abs(col(r, 'D_port_m') - D) < 1e-9], key=lambda r: col(r, 'F_N'))
            Fs = np.array([col(r, 'F_N') for r in sel]); ms = np.array([col(r, 'mdot_ox') for r in sel])
            for frac in (1.0, 0.5, 0.25, 0.2, 0.125):
                F = frac * F_FULL
                if F < Fs.min() - 1e-9 or F > Fs.max() + 1e-9:
                    continue
                v = float(np.interp(F, Fs, ms))
                if frac not in best or v > best[frac][0]:
                    best[frac] = (v, D)
        mox[P] = best
    kinds = {}
    for k, levels in KINDS.items():
        o = {}
        for P in mox:
            m_t = sum(mox[P][fr][0] * s for fr, s in levels)
            o[f'{P/1e6:.1f}MPa'] = dict(N2O_t_kg=m_t, N2O_2t_kg=2.0 * m_t, N2O_pair_kg=3.0 * m_t,
                                        N2O_pair_with_allowance_kg=3.0 * m_t * (1.0 + ALLOW))
        o['t_s'] = sum(s for _, s in levels)
        kinds[k] = o
    per_set = {f'{P/1e6:.1f}MPa': sum(kinds[k][f'{P/1e6:.1f}MPa']['N2O_pair_kg'] for k in KINDS) for P in mox}
    per_set_allow = {kk: v * (1.0 + ALLOW) for kk, v in per_set.items()}
    t1_2t = {f'{P/1e6:.1f}MPa': kinds['T1_100pct'][f'{P/1e6:.1f}MPa']['N2O_2t_kg'] for P in mox}
    m100_max = max(mox[P][1.0][0] for P in mox)
    t_max_flight = 0.8 * FLIGHT_LOAD_KG / m100_max / (1.0 + ALLOW)       # 2t at 100 % within 80 % of the flight load (ASSUMED usable share)
    # DC-D (T4) oxidiser from the S230 ground record
    dr = [r for r in csv.reader(open(dcd_fn)) if r and not r[0].startswith('#')]
    hd = dr[0]; dr = dr[1:]
    t = np.array([float(r[hd.index('t')]) for r in dr]); mo = np.array([float(r[hd.index('mox')] or 0.0) for r in dr])
    trap = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')
    m_dcd = float(trap(mo, t)); m_liq0 = float(dr[0][hd.index('m_liq')]); m_liq1 = float(dr[-1][hd.index('m_liq')])
    series = {}
    for N in N_REPEATS:
        series[f'N{N}'] = dict(grains=10 * N + 5, firings=10 * N,
                               N2O_kg={kk: v * N for kk, v in per_set_allow.items()},
                               N2_quench_kg=10 * N * N2_QUENCH_KG,
                               ground_tank_fills_at_4p5MPa=per_set_allow['4.5MPa'] * N / GROUND_TANK_KG)
    # CF-4
    n_base = len(CF4_STATES) * len(CF4_ATT) * CF4_REPEATS
    n_min = 2 * len(CF4_ATT) * CF4_REPEATS + CF4_REPEATS * 1 + 2 * len(CF4_ATT4) * 1   # IS-3 once per attitude set, 4 deg single runs
    n_max = n_base + len(CF4_STATES) * len(CF4_ATT4) * CF4_REPEATS
    per_run = VENT_MAX_G + LIFT_FLOW_START_G_S * LIFT_WINDOW_S + SEGMENT_G
    per_run_v28 = VENT_MAX_G + LIFT_FLOW_G_S * LIFT_WINDOW_S + SEGMENT_G
    rho_l = CP.PropsSI('D', 'T', T_A1, 'Q', 0, 'NitrousOxide')
    q_lift = LIFT_FLOW_START_G_S * 1e-3 / rho_l
    probe = dict(T_K=T_A1, rho_liquid_kg_m3=rho_l, lift_volume_flow_cm3_s=q_lift * 1e6, dropout_volume_cm3_per_response=q_lift * PROBE_RESPONSE_S * 1e6,
                 probe_response_s=PROBE_RESPONSE_S, lift_mm=H_START_A1_MM, lift_flow_g_s=LIFT_FLOW_START_G_S,
                 note='a vapour reading of one probe response at the start-level lift flow (A1 state) passes this void volume (DERIVED; CoolProp)')
    cf4 = dict(runs_lower=n_min, runs_base_5_per_state_and_attitude=n_base, runs_upper_with_4deg_repeats=n_max,
               N2O_per_run_g=per_run, N2O_per_run_terms_g=dict(vent_max=VENT_MAX_G, lift_flow=LIFT_FLOW_START_G_S * LIFT_WINDOW_S, segment_state=SEGMENT_G),
               N2O_per_run_g_at_0p2039mm=per_run_v28, lift_basis='THE start-level lift at the A1 state, 0.21776 mm (LEAD 203 (7)); 0.2039 mm value kept',
               N2O_kg=dict(lower=n_min * per_run / 1e3, base=n_base * per_run / 1e3, upper=n_max * per_run / 1e3),
               N2O_kg_with_allowance=dict(lower=n_min * per_run * (1 + ALLOW) / 1e3, base=n_base * per_run * (1 + ALLOW) / 1e3,
                                          upper=n_max * per_run * (1 + ALLOW) / 1e3),
               ground_tank_fills_upper=n_max * per_run * (1 + ALLOW) / 1e3 / GROUND_TANK_KG,
               note='optional runs (generation runs, prep-path credit, O-3) not included; tank heel not included (stand tank MISSING)',
               probe_dropout=probe,
               P1_lift_basis={f'{hh:.5f}mm': dict(t_lift_s=LAT_CMD_S + LAG_S + hh / V_PINTLE_MM_S,
                                                   s_per_cm3=S_PER_CM3 * H_V28_MM / hh,
                                                   P1_after_lift_s=V_ZERO_CM3 * S_PER_CM3 * H_V28_MM / hh,
                                                   P1_after_command_s=LAT_CMD_S + LAG_S + hh / V_PINTLE_MM_S + V_ZERO_CM3 * S_PER_CM3 * H_V28_MM / hh)
                             for hh in (H_V28_MM, H_START_A1_MM, 0.2192)},
               P1_note='P1 = 18.86 cm3 (zero-abort void) x s/cm3 at the commanded lift; s/cm3 scales as 1/flow, flow linear in lift (DERIVED); '
                       'the volume form (18.86 cm3 / measured liquid volume flow at the lift) is the test criterion')
    out = dict(version='v2.4b', date='2026-10-13', script='02-combustion/src/test_budgets_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='REV-COMB-3 R3-07/R3-08; LEAD CHANGELOG line 194 (8): counts and N2O budgets; T1 at 2t = 8 s against the stand tank',
               inputs={os.path.basename(map_fn): sha16(map_fn), os.path.basename(dcd_fn): sha16(dcd_fn)},
               mdot_ox_kg_s={f'{P/1e6:.1f}MPa': {f'{fr:g}': dict(value=v, D_port_m=D) for fr, (v, D) in mox[P].items()} for P in mox},
               kinds=kinds, N2O_per_repeat_set_kg=per_set, N2O_per_repeat_set_with_allowance_kg=per_set_allow,
               T1_100pct_2t_8s_kg=t1_2t, T1_2t_share_of_flight_load=max(t1_2t.values()) / FLIGHT_LOAD_KG,
               T1_100pct_max_2t_s_on_flight_tank=2.0 * (t_max_flight / 2.0), flight_load_kg=FLIGHT_LOAD_KG, ground_tank_kg=GROUND_TANK_KG,
               T4_DCD=dict(N2O_kg=m_dcd, m_liq_start_kg=m_liq0, m_liq_end_kg=m_liq1),
               series=series, N2_quench_per_firing_kg=N2_QUENCH_KG, allowance=ALLOW, CF4=cf4,
               tags=dict(flows='SIM S230 map (grain_q1d v2 nominal law)', durations='ASSUMED (T1-T4 spec §3)', repeats='ASSUMED (spec §6, N <= 8 practical)',
                         tanks='flight load DESIGN; ground tank 15 L / 10.4 kg ASSUMED; the founders\' stand tank is MISSING'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ('mdot_ox_kg_s', 'N2O_per_repeat_set_kg', 'N2O_per_repeat_set_with_allowance_kg', 'T1_100pct_2t_8s_kg',
                                          'T1_2t_share_of_flight_load', 'T1_100pct_max_2t_s_on_flight_tank', 'T4_DCD', 'series', 'CF4')}, indent=1, default=float))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:4])
