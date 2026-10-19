"""LEAD CHANGELOG lines 203-205 items for Combustion v2.4b (2026-10-13; coordinator relays of lines 203-204 and 205).

Answers, from stored data (no grid re-run except the start-level lit history at the defined lift, run separately):
  (1) purge flow basis (Electronics SIL 32.0 g/s against the Combustion 29.8 g/s) and the vented mass for the 2.5 s schedule and the
      2.55 s ECU cap (line 203 (3));
  (2) THE start-level lift and its basis (line 203 (7));
  (3) the latency-model E2 (Pc > 3 bar abs, withdrawn) against the ECU relative rule: effect on the R3-01 hold table;
  (4) source text for the firmware constants 2500 N/s, 0.5 s, 5 bar abs and 0.12 s, and FLAMEOUT_OPT;
  (5) FA-1: head spectrum near 6 ms; history length and model limit;
  (6) per-record classes for the 500 N ramp profile;
  (7) A1_none p99 engine-on time 8.375 s against the 8.258 s A1 sizing cycle;
  (8) line 205: gas in the Pc port passage at the relight and during the FA-1 rise, and its sound speed.
Tags are given per value in the output.  Nothing here is physical evidence.
usage: python -I lead_items_203_205_v2p4b.py DATA_V2_DIR HUB_DIR MECH_PC_DIR OUT_JSON
"""
from __future__ import annotations
import csv, hashlib, json, math, os, re, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

EXPECT = {
    'v2p4a/vented_mass_brackets_v2p4a.json': '8e8ca9329c74a01f',
    'v2p4/start_latency_v2p4.json': '809491fd86b91439',
    'v2p4/drogue_hold_check_v2p4.json': '70820e0038be39a7',
    'v2p4a/fa1_envelope_v2p4a.json': '64b328150025fa1e',
    'v2p4b/release_hold_v2p4b.json': 'a926426da0e6e436',
    'v2p4b/cold_flow_start_lift_v2p4b.json': '28ce48092f33da1b',
    'v2p4b/fa1_spectra_dense_v2p4b.json': '7468996959538d0f',
    'v2p4b/fa1_histories_solver_v2p4b.npz': '399bf43d1c09de24',
    'v2p4b/start_level_lit_thrust_v2p4b.json': 'ae2038c5141b7f73',
}
EXPECT_HUB = {
    '06-electronics/results/bleed_driver_v1.json': '298b405b0621acd5',
    '06-electronics/firmware/src/core/config.h': '0880af5a27880a5b',
    '06-electronics/firmware/src/core/engine_params.h': '6b73317fcd7d07ac',
}
EXPECT_MECH = {'pc_line_period_v1.json': '7f5d8950516d98f2', 'pc_transducer_temperature_v1.json': '774519536f26c762'}
N2O = 'NitrousOxide'
P_ATM = 101325.0


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def r(x, n=3):
    return None if x is None else round(float(x), n)


def ceil10ms(x):
    return math.ceil(round(x / 0.010, 6)) * 0.010


# ----------------------------------------------------------------------------------------------------------------- (1)
def purge_basis(D, H):
    VM = json.load(open(os.path.join(D, 'v2p4a/vented_mass_brackets_v2p4a.json')))
    BD = json.load(open(os.path.join(H, '06-electronics/results/bleed_driver_v1.json')))
    CF = json.load(open(os.path.join(D, 'v2p4b/cold_flow_start_lift_v2p4b.json')))
    LIQ, VAP = VM['rate_lines_g_s']['all_liquid'], VM['rate_lines_g_s']['all_vapour']
    rows = {round(x['t_flow_s'], 2): x for x in VM['rows']}
    m25o, m25b = rows[2.5]['open']['max_g'], rows[2.5]['barrier']['max_g']
    m24o = rows[2.4]['open']['max_g']
    slope_end = (m25o - m24o) / 0.1
    A2 = 2 * math.pi / 4 * (0.707e-3) ** 2; A1mm = math.pi / 4 * (1.0e-3) ** 2
    G_coast = LIQ * 1e-3 / (0.70 * A2)
    sil = BD['inputs']['mdot_sil_g_s']; comb = BD['inputs']['mdot_comb_g_s']
    by_state = {k: dict(T_K=v['T_K'], P_tank_bar=r(v['P_tank_bar'], 2), G_dyer_kg_m2s=r(v['G_dyer_kg_m2s'], 0),
                        all_liquid_two_taps_g_s=r(0.70 * A2 * v['G_dyer_kg_m2s'] * 1e3, 2)) for k, v in CF['states'].items()}

    def M(t, slope=LIQ):
        return m25o + slope * (t - 2.5) if t >= 2.5 else None
    times = {'2.50 s flow (nominal schedule)': 2.50, '2.55 s flow (cap read as flow time)': 2.55,
             '2.60 s flow (2.55 s both-open cap + 0.05 s valve-time offset, Electronics ASSUMED 30/80 ms)': 2.60,
             '2.66 s flow (Electronics firmware-cap row, both open 2.61 s)': 2.66, '3.293 s flow (Electronics hardware window bound)': 3.293}
    tab = {}
    for lab, t in times.items():
        tab[lab] = dict(t_flow_s=t, combustion_bound_open_g=r(M(t), 2), combustion_record_slope_g=r(M(t, slope_end), 2),
                        combustion_barrier_g=r(m25b + LIQ * (t - 2.5), 2), electronics_comb_basis_g=r(comb * t, 2),
                        electronics_sil_basis_g=r(sil * t, 2), all_liquid_line_from_t0_g=r(LIQ * t, 2))
    t76 = 2.5 + (76.0 - m25o) / LIQ
    t80 = 2.5 + (80.0 - m25o) / LIQ
    return dict(
        question='LEAD 203 (3) relay: Electronics SIL 32.0 g/s against Combustion 29.8 g/s (+7 %); which is right; vented mass at the 2.5 s '
                 'schedule and the 2.55 s ECU cap',
        what_the_two_numbers_are=dict(
            electronics_32p0='83.6 g / 2.61 s: SIL S12 nominal 31.44 g/s (78.6 g / 2.5 s) x 2.66 s of flow, divided by the 2.61 s both-open time',
            electronics_29p8='77.7 g / 2.61 s: 29.2 g/s (= 73.0 g / 2.5 s, the Combustion record maximum averaged over 2.5 s) x 2.66 s, '
                             'divided by 2.61 s',
            tag='DERIVED from 06-electronics/results/bleed_driver_v1.json (298b405b0621acd5)'),
        answer=('Neither constant rate is right. The vented mass is the purge-record mass M(t), not a rate times t. The records '
                '(vented_mass_brackets_v2p4a, SIM on ASSUMED Cd 0.70 and slip brackets) start with vapour at the taps (8.49 g/s line) and '
                'turn to liquid (31.24 g/s line); M(2.5 s) <= %.2f g (open element; barrier %.2f g). After 2.5 s the marginal rate is at '
                'most the all-liquid rate %.2f g/s (two taps at 0.707 mm, Cd 0.70 ASSUMED, Dyer %.0f kg/m2s at the coast state 46.45 bar, '
                '289.5 K: an upper-bound flux); the maximum record itself ends at %.1f g/s (2.4-2.5 s). 29.2 g/s x t is right only at '
                't = 2.5 s and understates the slope after it by <= %.1f g/s; 31.44-32.0 g/s x t applies the all-liquid rate from t = 0, '
                'i.e. assumes the line holds no vapour when the purge starts, which is the condition the purge exists to remove: it '
                'overstates M(2.5 s) by %.1f g (+%.1f %%). The SIL liquid rate (31.44 g/s nominal, 31.86 g/s maximum in S12 v2.9) is '
                '%.1f-%.1f %% above the Combustion all-liquid rate: a plant-state/flux-model difference (SIL flux %.0f kg/m2s at Cd 0.70 '
                'on the 1.0 mm area), not a basis disagreement.') % (
                    m25o, m25b, LIQ, G_coast, slope_end, LIQ - comb, sil * 2.5 - m25o, 100 * (sil * 2.5 / m25o - 1),
                    100 * (sil / LIQ - 1), 100 * (31.86 / LIQ - 1), sil * 1e-3 / (0.70 * A1mm)),
        rule='M(t) <= M_rec(2.5 s) + 31.24 g/s x (t - 2.5 s) for t >= 2.5 s (DERIVED upper bound); M_rec(2.5 s) = %.2f g open / %.2f g barrier'
             % (m25o, m25b),
        vented_mass_g=tab,
        cap_for_76g=dict(t_flow_s=r(t76, 4), both_open_s_with_0p05_offset=r(t76 - 0.05, 4),
                         note='the 2.55 s both-open cap (2.60 s of flow) gives <= %.2f g on the bound (%.2f g on the record slope): at the 76 g '
                              'limit within %.2f g; a strict <= 76 g on the bound needs both-open <= %.3f s. Cd 0.70 is ASSUMED: +-1 %% on Cd '
                              'moves M(2.5 s) by about +-0.7 g, more than the cap difference; the bleed Cd is TO-VERIFY (CF-4 / LEAK-1)'
                              % (M(2.60), M(2.60, slope_end), M(2.60) - 76.0, t76 - 0.05)),
        gnc_80g_sensitivity=dict(t_flow_s=r(t80, 3), note='80 g (GNC sensitivity) is reached at %.3f s of flow on the bound' % t80),
        liquid_rate_by_state_two_taps=by_state,
        rate_lines_g_s=dict(all_vapour=VAP, all_liquid=LIQ),
        tags=dict(records='SIM (purge_duration_v2p4 trade records; ASSUMED Cd 0.70, slip brackets)', extension='DERIVED upper bound',
                  flux='DERIVED (Dyer, CoolProp HEOS) at the coast state; upper bound', electronics='as published by Electronics'))


# ----------------------------------------------------------------------------------------------------------------- (2)
def start_level_lift(D, H, lit_lift_f):
    cfg = open(os.path.join(H, '06-electronics/firmware/src/core/config.h')).read()
    T_tab = [float(x) for x in re.findall(r'([0-9.]+)f', re.search(r'kIgnLiftT_K\[kIgnLiftN\] = \{([^}]*)\}', cfg).group(1))]
    h_tab = [float(x) * 1e3 for x in re.findall(r'([0-9.e-]+)f', re.search(r'kIgnLiftTab_m\[kIgnLiftN\] = \{([^}]*)\}', cfg).group(1))]
    assert len(T_tab) == len(h_tab) == 17, (len(T_tab), len(h_tab))
    row = dict(zip(T_tab, h_tab))
    CF = json.load(open(os.path.join(D, 'v2p4b/cold_flow_start_lift_v2p4b.json')))
    a1 = CF['states']['A1_relight_286.7K']
    h_v28, mdot_a1_v28, mdot_20C_v28 = 0.2039, 35.0, 37.1           # REPORT v2.4a §7.4 step 4 (v2.8 default)
    h_a1_comb = h_v28 * 37.4 / mdot_a1_v28                           # linear in lift (DERIVED)
    h_20_ecu_at_cap = row[293.15] * 37.1 / 37.4
    Fb_hs = a1['F_bound_N'] * row[286.70] / a1['start_lift_mm']
    lit = {}
    for lab, f in (('0.2039mm', os.path.join(D, 'v2p4b/start_level_lit_thrust_v2p4b.json')), ('0.21776mm', lit_lift_f)):
        if f and os.path.exists(f):
            J = json.load(open(f)); s = J['summary']
            lit[lab] = dict(file=os.path.basename(f), sha256_16=sha16(f), E2_s_range=[r(x, 4) for x in s['E2_s_range']],
                            F_min_max_E2_to_E2p0p5_N=[r(s['F_min_over_corners_in_E2_to_E2p0p5_N'], 2), r(s['F_max_over_corners_in_E2_to_E2p0p5_N'], 2)],
                            n_corners_never_ge_37p16N_in_window=s['n_corners_never_ge_37p16N_in_window'],
                            latest_first_t_ge_37p16N_after_E2_s=r(s['latest_first_t_ge_37p16N_after_E2_s'], 4),
                            F_at_1s_range_N=[r(x, 2) for x in s['F_at_1s_range_N']],
                            envelope_median_N={str(t): r(v, 2) for t, v in zip(J['envelope']['t_s'], J['envelope']['F_median_N'])})
    return dict(
        definition=('THE start-level lift h_s(T) is the ignition lift: the lift of the lift-vs-T_tank table at the E0 tank temperature, '
                    'defined by cold flow (LEAD caps: <= 37.1 g/s at 20 C, <= 37.4 g/s at the A1 relight state; REPORT §7.4 step 4) and '
                    'calibrated by CF-3. The ECU commands it at E1, holds it to E2 and, in the LEAD 186 (2) command hold with Pc invalid, '
                    'keeps it (no open-loop map lookup in the hold). CF-3 measures mdot and the load-cell F at the commanded lift with '
                    'the encoder lift recorded (start-lift acceptance, cold_flow_start_lift_v2p4b).'),
        values_before_CF3=dict(
            A1_relight_286p70K_mm=r(row[286.70], 5), A1_relight_source='ECU row 0.21776 mm (Electronics SIL flow model at 37.4 g/s; '
                                                                     'Dyer k-blend, Cd 0.70 ASSUMED, no line loss: an upper-bound flow model)',
            A1_relight_combustion_model_mm=r(h_a1_comb, 5),
            A1_relight_agreement_pct=r(100 * (row[286.70] / h_a1_comb - 1), 3),
            pad_20C_mm=r(h_v28, 4), pad_20C_source='0.2039 mm gives 37.1 g/s at 20 C (v2.8 default, Combustion injector model)',
            pad_20C_ECU_row_mm=r(row[293.15], 5),
            pad_20C_ECU_row_scaled_to_37p1_mm=r(h_20_ecu_at_cap, 5),
            note=('the ECU rows hold 37.4 g/s at every temperature; at 20 C that is 0.8 %% above the 37.1 g/s cap (Electronics\' own note): '
                  'the 293.15 K row scaled to 37.1 g/s is %.4f mm, which is the 0.2039 mm v2.8 default. So 0.2039 mm is the start-level '
                  'lift at 20 C and 0.21776 mm the start-level lift at the A1 relight state; they are one definition at two states.')
                 % h_20_ecu_at_cap,
            tags='DERIVED (flow linear in lift between 0.2039 and 0.218 mm; Cd 0.70 ASSUMED); CF-3 replaces every row'),
        retired=dict(ECU_hold_0p2154mm='open-loop-map lift for 62.5 N at the SIL S17 state: not the start-level lift; the hold lift becomes h_s',
                     map_62p5N_lift_mm=[r(CF['summary']['start_lift_mm'][0], 4), r(CF['summary']['start_lift_mm'][1], 4)],
                     map_62p5N_lift_note='the 62.5 N S230 map lift (0.2133-0.2278 mm over 289.5-283.15 K; 0.2195 mm at 286.7 K) is the '
                                         'nominal lit level of the map, not a lift definition; at the A1 state it is 0.8 % above h_s'),
        cold_flow_bound_at_hs=dict(A1_relight_N=r(Fb_hs, 2), map_lift_value_N=r(a1['F_bound_N'], 2), margin_N=16.31,
                                   tag='DERIVED: the v2.4b start-lift bound scaled with the lift (mdot linear in lift); CONDITIONAL on Cd x A x G '
                                       'at the start lift (CF-3 start-lift point)'),
        lit_history=lit,
        consequences=['ECU: hold lift = h_s(T_tank at E0) (the ignition-lift row), replacing the S17 open-loop map value 0.2154 mm',
                      'CF-3: start-lift point at the commanded table lift, encoder lift recorded (LEAD 194 (4) acceptance unchanged)',
                      'GNC R2 v2 / P4c: lit history at 0.21776 mm (A1 state) published; the 0.2039 mm history is the 20 C-row / low-lift '
                      'sensitivity',
                      'the warm table rows (>= 293.15 K) are cut to the 37.1 g/s cap (Electronics; CF-3 confirms)'],
        ecu_table=dict(T_K=T_tab, lift_mm=[r(x, 5) for x in h_tab], source='06-electronics/firmware/src/core/config.h kIgnLiftTab_m (read only)'))


# ----------------------------------------------------------------------------------------------------------------- (3)
def e2_rule(D, lit_lift_f):
    SLJ = json.load(open(os.path.join(D, 'v2p4/start_latency_v2p4.json')))
    rows = [x for x in SLJ['part1_runs']['v'] if x['state'] == 'A1_relight' and abs(x['frac'] - 0.125) < 1e-9]
    tc = np.array([x['t_conf_s'] for x in rows if x['t_conf_s'] is not None])
    lift = SLJ['ignition_lifts']['A1_relight|0.125']['lift_m'] * 1e3
    rel = {}
    for lab, f in (('0.2039mm', os.path.join(D, 'v2p4b/start_level_lit_thrust_v2p4b.json')), ('0.21776mm', lit_lift_f)):
        if f and os.path.exists(f):
            J = json.load(open(f))
            e2 = [c['torch0.0']['E2_s'] for c in J['corners'] if c['torch0.0'].get('E2_s') is not None]
            e3 = [c['torch0.3']['E2_s'] for c in J['corners'] if c.get('torch0.3', {}).get('E2_s') is not None]
            rel[lab] = dict(E2_torch0_s=[r(min(e2), 4), r(max(e2), 4)], E2_torch0p3_s=[r(min(e3), 4), r(max(e3), 4)] if e3 else None,
                            n_no_E2_torch0=len(J['corners']) - len(e2))
    e2_rel_floor = 0.010 + 0.0023                       # 10 ms persistence + 2.3 ms latency (construction bound)
    d_max = float(tc.max()) - e2_rel_floor
    RH = json.load(open(os.path.join(D, 'v2p4b/release_hold_v2p4b.json')))
    holds = {}
    for g, v in RH['groups'].items():
        holds[g] = {}
        for p in ('ramp_to_200N', 'ramp_to_500N', 'lift_flow_held'):
            ts = v[p]['latest_trip_sup_s']
            holds[g][p] = dict(table_hold_s=v[p]['hold_needed_s'], latest_trip_from_model_E2_s=r(ts, 4),
                               hold_from_ECU_E2_bound_s=r(ceil10ms(ts + d_max + 0.010), 2))
    return dict(
        model_E2='latency model (start_latency_v2p4; used by rg01 and release_hold_v2p4b): measured Pc > 3.0 bar abs for 10 ms, 2.3 ms '
                 'latency (LEAD 134 rule, withdrawn)',
        ECU_E2='relative rule: rise >= 0.8 bar over the pre-lift baseline on filtered AND raw Pc for 10 ms, above 1.8 bar abs (REPORT §7.3); '
               'latency 2.3 ms',
        light_to_E2_model_s=dict(lift_mm=r(lift, 4), n=int(len(tc)), min=r(tc.min(), 4), median=r(np.median(tc), 4), max=r(tc.max(), 4),
                                 tag='SIM (start_latency_v2p4 part 1, A1 relight, 12.5 % lift)'),
        light_to_E2_relative_s=rel, relative_rule_floor_s=e2_rel_floor,
        shift_bound_s=r(d_max, 4),
        statement=('The ECU E2 comes earlier than the model E2 by at most %.1f ms (model 16.5-27.0 ms after the light at %.4f mm; relative rule '
                   '>= 12.3 ms by construction, 14-16 ms in the grain_q1d runs). The gap arrival after the light does not depend on the E2 '
                   'rule for the held profile and moves earlier by at most the same shift for the ramp profiles (the ramp starts at E2). '
                   'So the hold counted from the ECU E2 is at most the table hold plus the shift: bound values below (rounded up to 10 ms). '
                   'P(success) and the trip class of each record do not change; for a given H the split between released-then-A3 and '
                   'A3-before-release moves by <= the shift. The release-term reading of the table (Pc >= 3.0 bar abs, R3-12 note) is '
                   'unchanged.') % (1e3 * d_max, lift),
        holds=holds,
        tags='DERIVED bound from stored SIM (no re-run); the per-record CSV is on the model E2')


# ----------------------------------------------------------------------------------------------------------------- (4)
def firmware_sources(H):
    ep = open(os.path.join(H, '06-electronics/firmware/src/core/engine_params.h')).read()
    def line(name):
        m = re.search(r'constexpr float ' + name + r' = ([^;]+);\s*//(.*)', ep)
        return (m.group(1).strip(), m.group(2).strip()) if m else (None, None)
    rho = {T: CP.PropsSI('P', 'T', T + 273.15, 'Q', 0, 'Propane') / 1e5 for T in (0.0, 10.0, 20.0)}
    T5 = CP.PropsSI('T', 'P', 5e5, 'Q', 0, 'Propane') - 273.15
    t1090 = 0.8 * (500.0 - 62.5) / 2500.0
    out = {
        'kStartRamp_Nps = 2500 N/s': dict(firmware=line('kStartRamp_Nps'), source_text=(
            'Start ramp: after E2, and after the release of the LEAD 186 (2) command hold, the thrust command rises at <= 2500 N/s '
            '(5 F_max per second) from the thrust at the start lift (REPORT v2.4a §7.4 step 6; Combustion v2.1 start sequence). Basis: '
            '(a) it equals the actuator rate under load required of ENG-03 (>= 5 F_max/s = 2500 N/s, LEAD 2026-10-13, bench plan v2), so '
            'the command never outruns the actuator during the start; (b) a full 62.5 -> 500 N ramp at 2500 N/s has t10-90 = %.3f s, '
            'inside the ENG-03 t10-90 <= 0.15 s (gnc.json v2), the slowest ramp meeting it being %.0f N/s; (c) every start-timing result '
            'uses it (start_latency_v2p4 with a 1000 N/s slow case, REPORT Tables 2.16-2.17, release_hold_v2p4b ramp profiles).') % (
                t1090, 0.8 * 437.5 / 0.15), tag='DESIGN (Combustion v2.1 choice) with DERIVED consistency checks; not a physical limit'),
        'kSparkTrain_s = 0.5 s': dict(firmware=line('kSparkTrain_s'), source_text=(
            'Spark train: 50 Hz, 50 mJ, from E0 + 0.02 s for at most 0.5 s (to E0 + 0.52 s), stopped earlier at E2 (REPORT §7.4 steps 2 and 6; '
            'igniter sequence v2.2). Basis: it covers the torch-light window with margin (torch gate E1 by E0 + 0.16 s; E0 -> E1 median '
            '0.09 s) and re-sparks a torch that blows out before the main light while the torch runs (SOL1 off at E2, torch off by '
            'E0 + 0.6 s). The latest E2 (0.626 s from E0 on the purged relight) can fall after the train: the torch then runs without spark '
            'until E2 or 0.6 s; torch stability under the main flow is an IGN-1 item (FA-1 FM3).'),
            tag='DESIGN; window values DERIVED (start_latency_v2p4, torch_gate_v2p4)'),
        'kPropaneOffPcAbs_Pa = 5 bar abs': dict(firmware=line('kPropaneOffPcAbs_Pa'), source_text=(
            'Propane solenoid (SOL2) closed at E0 + 0.40 s or before the chamber pressure exceeds 5 bar abs, whichever first; in the v2.4 '
            'sequence SOL2 closes within 20 ms of SOL1 at E2 (Pc about 3 bar) and this is the backstop. Basis: the propane supply is '
            'self-pressurised at its vapour pressure (%.2f bar abs at 0 C, %.2f at 10 C, %.2f at 20 C, CoolProp); with Pc above the supply '
            'pressure, chamber gas can flow back into the propane line. 5 bar abs is the propane vapour pressure at %.1f C, so the rule '
            'protects a supply at or above about 2 C (REPORT §7.2: torch Pc 3 bar stays below the propane vapour pressure down to about 0 C).')
            % (rho[0.0], rho[10.0], rho[20.0], T5),
            tag='DERIVED (CoolProp propane saturation) on the DESIGN torch; the minimum propane temperature (about 2 C) is an implied '
                'operating limit, TO-VERIFY against the founders\' propane conditioning'),
        'kPintleToIgnitionLift_s = 0.12 s': dict(firmware=line('kPintleToIgnitionLift_s'), source_text=(
            'Ignition-lift slot of a timing-only (ground) start: the pintle is commanded to the ignition lift at E0 + 0.12 s when no E1 '
            'sensor result is used. It is the v2.2 sequence value: torch confirmed by E0 + 0.10 s plus 20 ms. In flight (v2.8 on) the '
            'lift command is issued at E1 (torch confirmed on P_torch AND photodiode), not at 0.12 s. The unlit-inventory figures are '
            'counted from the lift command (REPORT §2.8, W from the lift command) and do not depend on the slot.'),
            tag='DESIGN (legacy v2.2 slot, ground timing-only starts)'),
    }
    flame = ('FLAMEOUT_OPT (Electronics v2.10, REV-GNC-2 (2)): in RUN with the Pc channel invalid the photodiode is the only flame '
             'indication; it is armed only after the main-chamber view is proven (lit 20 ms in RUN with the torch closed) and aborts '
             '(FLAMEOUT) after 20 ms dark. Cold-flow relation: the dead-engine apparent thrust bound (12.5-13.3 N at the start lift, '
             'CONDITIONAL on Cd x A x G) is the thrust GNC sees until FLAMEOUT_OPT or R2 acts; Combustion has no data on the photodiode '
             'levels or the main-chamber line of sight (photodiode levels ASSUMED by Electronics; view MISSING until IGN-1).')
    return dict(note='matched by value and [COMB] tag in 06-electronics/firmware/src/core/engine_params.h; Electronics confirms the mapping',
                constants=out, FLAMEOUT_OPT_cold_flow_text=flame)


# ----------------------------------------------------------------------------------------------------------------- (5)
def fa1_items(D):
    J = json.load(open(os.path.join(D, 'v2p4b/fa1_spectra_dense_v2p4b.json')))
    Tp = np.array(J['periods_ms']['pressure'])
    base = J['envelopes']['vapour_once|rounded_Cd1.0|grid_OF4-12|all']; allc = J['envelopes']['all|all|incl_OF3-3.5|all']
    out = {}
    for lab, g in (('baseline', base), ('all_cases', allc)):
        hv = np.array(g['P_head_eq_bar|env']['value'])
        out[lab] = dict(at_6p0ms_bar=r(np.interp(6.0, Tp, hv), 2),
                        max_5p7_to_8p7ms_bar=r(hv[(Tp >= 5.7 - 1e-9) & (Tp <= 8.7 + 1e-9)].max(), 2),
                        max_2p5_to_4p9ms_bar=r(hv[(Tp >= 2.5 - 1e-9) & (Tp <= 4.9 + 1e-9)].max(), 2),
                        max_0p02_to_1ms_bar=r(hv[Tp <= 1.0 + 1e-9].max(), 2),
                        grid_points_5p7_to_8p7=int(((Tp >= 5.7 - 1e-9) & (Tp <= 8.7 + 1e-9)).sum()))
    Z = np.load(os.path.join(D, 'v2p4b/fa1_histories_solver_v2p4b.npz'), allow_pickle=False)
    off = Z['offsets']; t = Z['t_s']; ph = Z['P_head_bar']; keys = Z['case_keys']
    tend = np.array([float(t[off[i + 1] - 1]) for i in range(len(keys))])
    peak = np.array([float(ph[off[i]:off[i + 1]].max()) for i in range(len(keys))])
    late = []
    for i in range(len(keys)):
        tt = t[off[i]:off[i + 1]]; pp = ph[off[i]:off[i + 1]]
        late.append(float(pp[tt >= 0.025].max()) if (tt >= 0.025).any() else float('nan'))
    late = np.array(late)
    return dict(head_spectrum_near_6ms=dict(values=out, convention='envelope max(b, c), undamped SDOF, head node (bar abs)',
                                            note='070BG sense line (0.30 m ASSUMED) period 5.7-8.7 ms per Mechanical; the sense line is '
                                                 'deleted by LEAD line 205 (seat-mounted unit); values kept for the record',
                                            tag='DERIVED (SDOF on SIM construct histories)'),
                histories=dict(file='fa1_histories_solver_v2p4b.npz', step_ms=0.05,
                               t_end_ms=[r(1e3 * tend.min(), 1), r(1e3 * tend.max(), 1)],
                               t_end_rule='each case runs from the light to max(t_f, tau_pool) + 60 ms',
                               max_head_after_25ms_bar=[r(np.nanmin(late), 2), r(np.nanmax(late), 2)],
                               construct_head_peak_bar=[r(peak.min(), 2), r(float(np.median(peak)), 2), r(peak.max(), 2)],
                               limit=('the construct supports histories beyond 25 ms (published to %.0f-%.0f ms at solver resolution), but past '
                                      'the pool term its pressure is set by the ASSUMED pool plateau and the lumped vented network; it does not '
                                      'model the transition to the lit start level (grain_q1d start-level history, 0-1 s) or roughness. Use '
                                      'it to about the end of the pool term; beyond, use the start-level history.') % (1e3 * tend.min(), 1e3 * tend.max()),
                               tag='SIM construct (ASSUMED inputs; pool plateau ASSUMED)'))


# ----------------------------------------------------------------------------------------------------------------- (6)
def classes_500N(D):
    RH = json.load(open(os.path.join(D, 'v2p4b/release_hold_v2p4b.json')))
    out = {}
    for g, v in RH['groups'].items():
        out[g] = {p: dict(hold_needed_s=v[p]['hold_needed_s'], hold_within_W=v[p].get('hold_within_W'),
                          mean_P_success_worst_convention=r(v[p]['mean_P_success_worst_convention'], 4),
                          mean_P_trip=r(v[p].get('mean_P_trip'), 4)) for p in ('ramp_to_200N', 'ramp_to_500N')}
    return dict(csv='release_hold_records_v2p4b.csv (59e7f44e44fbfeef): 6480 rows = 2160 records x 3 profiles; column profile = '
                    'ramp_to_200N / ramp_to_500N / lift_flow_held; every per-record class column exists for each profile',
                groups=out, status='the unpurged alternative is NOT ADOPTED (LEAD 204 (2)); the classes are data for GNC P4c',
                tag='SIM on ASSUMED delays + DERIVED line states (not probability-weighted)')


# ----------------------------------------------------------------------------------------------------------------- (7)
def a1_note():
    web_p99 = dict(a06=(9.64, 9.66, 9.67), a10=(7.12, 7.39, 7.62), a15=(4.35, 5.02, 5.61))       # REPORT Table 4.6, A1 p99 8.26 s
    web_g = dict(a06=(9.71, 9.73, 9.73), a10=(7.20, 7.46, 7.69), a15=(4.46, 5.10, 5.68))         # A1 p99 growth 8.14 s
    dw = max(web_g[k][i] - web_p99[k][i] for k in web_p99 for i in range(3))
    dt_ref = 8.26 - 8.14; dt_new = 8.375 - 8.258
    loss = dw * dt_new / dt_ref
    return dict(statement=('GNC F11: A1_none p99 engine-on 8.375 s against the 8.258 s A1 sizing cycle (+%.3f s, +%.1f %%). B1 still governs '
                           'thermal and erosion sizing. Combustion\'s A1 statements: (a) Table 4.6 A1 residual web (8.26 s): on the REPORT '
                           'pair p99 8.26 s / growth 8.14 s the web changes by <= %.2f mm per 0.12 s, so +0.117 s takes <= %.2f mm: minimum '
                           'A1 web >= %.2f mm, ENG-06 (>= 1 mm) still holds everywhere on A1; (b) the A1 relight state (286.7 K, 43.5 bar, '
                           'port 32.2 mm, from the A1 v2 run at the relight command) is not a duration-sized statement; (c) no A1 thermal '
                           'limit is stated by Combustion: liner, insert and closure sizing use B1. No A1 conclusion changes.')
                          % (dt_new, 100 * dt_new / 8.258, dw, loss, 4.35 - loss),
                tags='DERIVED (linear duration scaling on REPORT Table 4.6 SIM values); GNC F11 value as relayed (LEAD 204 (4))')


# ----------------------------------------------------------------------------------------------------------------- (8)
def pc_port_gas(D, MP):
    PL = json.load(open(os.path.join(MP, 'pc_line_period_v1.json')))
    PT = json.load(open(os.path.join(MP, 'pc_transducer_temperature_v1.json')))
    a1 = [v for k, v in PT.items() if k.startswith('DC-A1')][0]['series']
    Tw_C = [s['at_RELIGHT_C'] for s in a1.values() if s.get('at_RELIGHT_C') is not None]
    Tw = (min(Tw_C) + 273.15, max(Tw_C) + 273.15)
    Tw_hot = (Tw[0] + 20.0, Tw[1] + 20.0)                         # hot-day start 40 C instead of 20 C: +20 K (ASSUMED shift)
    FE = json.load(open(os.path.join(D, 'v2p4a/fa1_envelope_v2p4a.json')))
    prods = FE['products']
    Z = np.load(os.path.join(D, 'v2p4b/fa1_histories_solver_v2p4b.npz'), allow_pickle=False)
    off = Z['offsets']; ph = Z['P_head_bar']
    peaks = np.array([float(ph[off[i]:off[i + 1]].max()) for i in range(len(off) - 1)])
    P_pk = (float(np.percentile(peaks, 50)), float(peaks.max()))
    P_list = sorted(set([round(P_pk[0], 1), round(P_pk[1], 1), 72.45, 102.0]))
    P_rng = (float(peaks.min()), float(peaks.max()))
    P_dense = sorted(set([float(x) for x in np.arange(math.floor(P_rng[0]), math.ceil(P_rng[1]) + 0.5, 2.0)] + [72.0, 72.2, 72.45, 72.7, 73.0]))
    # ---- relight-instant gas, 1 atm, wall temperature
    import cantera as ct
    import hard_start_v2p4 as HS
    def frozen_products(OF):
        X, h, _ = HS._reactants('comb', 286.7, OF)
        g = HS._eq(X, h, P=45e5)
        return g.mole_fraction_dict(), g.T, math.sqrt(g.cp_mass / g.cv_mass * ct.gas_constant / g.mean_molecular_weight * g.T)
    gas = ct.Solution('gri30.yaml')
    def c_ideal(X, T, P=P_ATM):
        gas.TPX = T, P, X
        return math.sqrt(gas.cp_mass / gas.cv_mass * ct.gas_constant / gas.mean_molecular_weight * T), gas.mean_molecular_weight
    relight = {}
    for T in (Tw[0], Tw[1], Tw_hot[1]):
        row = dict(T_K=r(T, 1), air_m_s=r(CP.PropsSI('A', 'T', T, 'P', P_ATM, 'Air'), 1),
                   N2O_vapour_m_s=r(CP.PropsSI('A', 'T', T, 'P', P_ATM, N2O), 1))
        psat_w = CP.PropsSI('P', 'T', T, 'Q', 0, 'Water')
        for OF in (3.0, 4.0, 6.0, 8.0):
            X, T_hp, c_hot = frozen_products(OF)
            Xd = {k: v for k, v in X.items() if v > 1e-6}
            c_wet, M_wet = c_ideal(Xd, T)
            xw = Xd.get('H2O', 0.0); xmax = psat_w / P_ATM
            if xw > xmax:                                            # condense the excess water (saturated gas phase)
                n_other = 1.0 - xw; n_w = xmax * n_other / (1.0 - xmax)
                Xs = {k: (v if k != 'H2O' else n_w) for k, v in Xd.items()}
                s_ = sum(Xs.values()); Xs = {k: v / s_ for k, v in Xs.items()}
            else:
                Xs = Xd
            c_sat, M_sat = c_ideal(Xs, T)
            row[f'products_OF{OF:g}_water_saturated_m_s'] = r(c_sat, 1)
            row[f'products_OF{OF:g}_all_water_vapour_m_s'] = r(c_wet, 1)
        relight[f'{T:.1f}K'] = row
    hot = {}
    for OF in (3.0, 4.0, 6.0, 8.0):
        X, T_hp, c_hot = frozen_products(OF)
        hot[f'OF{OF:g}'] = dict(T_HP_K=r(T_hp, 0), c_frozen_m_s=r(c_hot, 0))
    # ---- N2O: saturated vapour (cold-flow phase and flash states); isentropic compression to the peak; wall-cooled states
    sat = {}
    for p in (1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0, 40.0):
        sat[f'{p:g}bar'] = dict(T_sat_K=r(CP.PropsSI('T', 'P', p * 1e5, 'Q', 1, N2O), 1), c_m_s=r(CP.PropsSI('A', 'P', p * 1e5, 'Q', 1, N2O), 1))
    p_flash = {'A1_286p7K': CP.PropsSI('P', 'T', 286.7, 'Q', 0, N2O) / 1e5, 'coast_289p5K': CP.PropsSI('P', 'T', 289.5, 'Q', 0, N2O) / 1e5}
    entries = [1.0, 1.5, 3.0, 10.0, 20.0, 30.0, 40.0] + [round(v, 2) for v in p_flash.values()]
    isen = {}
    for pe in entries:
        s = CP.PropsSI('S', 'P', pe * 1e5, 'Q', 1, N2O)
        isen[f'from_sat_vapour_{pe:g}bar'] = {f'{pf:g}bar': dict(T_K=r(CP.PropsSI('T', 'P', pf * 1e5, 'S', s, N2O), 1),
                                                                 c_m_s=r(CP.PropsSI('A', 'P', pf * 1e5, 'S', s, N2O), 1))
                                              for pf in P_list if pf > pe}
    c_isen_min = min(v['c_m_s'] for d in isen.values() for k, v in d.items() if float(k[:-3]) >= P_pk[0] - 0.05)
    wall = {}
    for pf in P_list:
        vals = {}
        for T in np.arange(Tw[0], Tw_hot[1] + 0.01, 1.0):
            try:
                vals[r(T, 1)] = (CP.PropsSI('A', 'T', float(T), 'P', pf * 1e5, N2O), CP.PhaseSI('T', float(T), 'P', pf * 1e5, N2O))
            except Exception:
                pass
        cm = min(vals.items(), key=lambda kv: kv[1][0])
        wall[f'{pf:g}bar'] = dict(c_range_m_s=[r(min(v[0] for v in vals.values()), 1), r(max(v[0] for v in vals.values()), 1)],
                                  c_min_at_T_K=cm[0], c_min_phase=cm[1][1], T_range_K=[r(Tw[0], 1), r(Tw_hot[1], 1)])
    scan = {}
    for pf in P_list:
        Ts = np.arange(250.0, 600.0, 0.5); cs = []
        for T in Ts:
            try:
                cs.append(CP.PropsSI('A', 'T', float(T), 'P', pf * 1e5, N2O))
            except Exception:
                cs.append(np.nan)
        cs = np.array(cs); i = int(np.nanargmin(cs))
        scan[f'{pf:g}bar'] = dict(c_min_single_phase_m_s=r(cs[i], 1), at_T_K=r(Ts[i], 1))
    # ---- air of the relight-instant gas compressed to the peak
    air = {}
    for T in (Tw[0], Tw[1]):
        s = CP.PropsSI('S', 'T', T, 'P', P_ATM, 'Air')
        air[f'from_{T:.1f}K'] = {f'{pf:g}bar': dict(isentropic_T_K=r(CP.PropsSI('T', 'P', pf * 1e5, 'S', s, 'Air'), 0),
                                                    isentropic_c_m_s=r(CP.PropsSI('A', 'P', pf * 1e5, 'S', s, 'Air'), 0),
                                                    isothermal_c_m_s=r(CP.PropsSI('A', 'T', T, 'P', pf * 1e5, 'Air'), 1)) for pf in P_list}
    # ---- thermal penetration during the rise
    pen = {}
    for lab, (T, P, fl) in {'N2O_330K_85bar': (330.0, 85e5, N2O), 'N2O_450K_85bar': (450.0, 85e5, N2O), 'N2O_250K_10bar': (250.0, 10e5, N2O),
                            'air_1000K_85bar': (1000.0, 85e5, 'Air')}.items():
        try:
            k = CP.PropsSI('L', 'T', T, 'P', P, fl); k_src = 'CoolProp'
        except ValueError:                                           # CoolProp has no thermal-conductivity model for N2O
            k = 0.10; k_src = ('ASSUMED upper bound 0.10 W/m K (no CoolProp N2O conductivity model; gas-phase N2O is about 0.017 W/m K '
                               'at 300 K and 1 bar, LITERATURE as recalled, TO-VERIFY); a larger k only deepens the layer')
        rho = CP.PropsSI('D', 'T', T, 'P', P, fl); cp = CP.PropsSI('C', 'T', T, 'P', P, fl)
        a = k / (rho * cp)
        pen[lab] = dict(k_W_mK=k, k_source=k_src, alpha_m2_s=float(a), depth_mm_1ms=r(1e3 * math.sqrt(a * 1e-3), 4),
                        depth_mm_4ms=r(1e3 * math.sqrt(a * 4e-3), 4))
    frac = {f'{pf:g}bar': dict(relight_gas_isothermal_pct=r(100 * (P_ATM / 1e5 / pf), 2),
                               relight_gas_adiabatic_air_pct=r(100 * (P_ATM / 1e5 / pf) ** (1 / 1.4), 2),
                               cold_flow_inflow_to_1p5bar_pct=[r(100 * ((1.5 / pf) - (P_ATM / 1e5 / pf)), 2),
                                                                r(100 * ((1.5 / pf) ** (1 / 1.3) - (P_ATM / 1e5 / pf) ** (1 / 1.3)), 2)])
            for pf in P_list}
    T_c222 = PL['rows'][0]['T_ms_N2O_vap_200K']; c_ref = PL['c_m_s']['N2O_vap_200K']
    def T_cc1(c):
        return T_c222 * c_ref / c
    # ---- dense minima over the whole construct peak range (every case peak lies in P_rng)
    def cmin_single(pf):
        best = (np.inf, None)
        for T in np.arange(250.0, 600.0, 0.5):
            try:
                c = CP.PropsSI('A', 'T', float(T), 'P', pf * 1e5, N2O)
            except Exception:
                continue
            if c < best[0]:
                best = (c, float(T))
        for T in np.arange(best[1] - 1.0, best[1] + 1.0, 0.02):
            try:
                c = CP.PropsSI('A', 'T', float(T), 'P', pf * 1e5, N2O)
            except Exception:
                continue
            if c < best[0]:
                best = (c, float(T))
        return best[0], best[1], CP.PhaseSI('T', best[1], 'P', pf * 1e5, N2O)
    dense = {}
    for pf in P_dense:
        c, Tm, phs = cmin_single(pf)
        dense[f'{pf:g}bar'] = dict(c_min_m_s=r(c, 1), at_T_K=r(Tm, 2), phase=phs)
    kmin = min(dense, key=lambda k: dense[k]['c_min_m_s'])
    c_lo_gas = dense[kmin]['c_min_m_s']
    sub = {k: v for k, v in dense.items() if float(k[:-3]) < 70.0}
    c_sub_min = min(v['c_min_m_s'] for v in sub.values()); k_sub = min(sub, key=lambda k: sub[k]['c_min_m_s'])
    isd = (np.inf, None, None)
    for pe in [1.0, 1.5, 3.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0] + list(p_flash.values()):
        se = CP.PropsSI('S', 'P', pe * 1e5, 'Q', 1, N2O)
        for pf in P_dense:
            if pf <= pe:
                continue
            try:
                c = CP.PropsSI('A', 'P', pf * 1e5, 'S', se, N2O)
            except Exception:
                continue
            if c < isd[0]:
                isd = (c, pe, pf)
    c_isen_min = isd[0]
    fr_med, fr_max = frac[f'{round(P_pk[0], 1):g}bar'], frac[f'{round(P_pk[1], 1):g}bar']
    relg = [fr_max['relight_gas_isothermal_pct'], fr_med['relight_gas_adiabatic_air_pct']]
    cfg = [fr_max['cold_flow_inflow_to_1p5bar_pct'][0], fr_med['cold_flow_inflow_to_1p5bar_pct'][1]]
    head_share = [100.0 - relg[1] - cfg[1], 100.0 - fr_max['relight_gas_isothermal_pct'] - fr_max['cold_flow_inflow_to_1p5bar_pct'][0]]
    pen_max = max(v['depth_mm_4ms'] for v in pen.values()); pen_peak = max(v['depth_mm_4ms'] for k, v in pen.items() if '85bar' in k)
    out = dict(
        passage=dict(geometry=PL['geometry_cad_v3.5.1'], source='Mechanical v351/pc/pc_line_period_v1.json (interim, read only)'),
        wall_temperature_at_relight_K=dict(A1_SIM=[r(Tw[0], 1), r(Tw[1], 1)], hot_day_ASSUMED_plus20K=[r(Tw_hot[0], 1), r(Tw_hot[1], 1)],
                                          source='Mechanical pc_transducer_temperature_v1.json, A1 p99 case, monitors at RELIGHT (20 C start '
                                                 'ASSUMED; the hot-day re-run at T0 = 40 C is Mechanical\'s closure, +20 K ASSUMED here)'),
        history=[
            'Before the first start the passage holds pad air at ambient pressure (DESIGN: the port is open to the chamber).',
            'First burn (A1 0-3.5 s): chamber pressure compresses the passage contents toward the transducer and head-face gas enters; '
            'at 25 bar abs the pad air keeps 4-10 % of the volume (isothermal-adiabatic). The passage walls stay at 20-22 C through MECO '
            '(A1 SIM monitors); the radial thermal time of the 1 mm-radius passage at 25 bar is about 0.2 s, so the gas sits at the wall '
            'temperature. Diffusion over the burn (about 1.5 mm at 25 bar) and pressure pumping mix the pad-air slug with head-face gas.',
            'MECO: the chamber vents to ambient; the passage gas re-expands and leaves mouth-first. With plug flow the pad air would refill '
            'the passage; with the mixing above the passage holds pad air mixed with first-burn head-face gas (N2, CO2, CO, H2, O2, water to '
            'saturation, N2O). The proportions are MISSING (not modelled).',
            'Coast (MECO to RELIGHT 18.7 s, A1): the walls warm to 32.2-51.9 C (A1 SIM; +4-11 % gas expansion, outflow); the descent from '
            'apogee raises ambient pressure by about 3 % (inflow of about 3 % of the volume: chamber gas = air drawn through the nozzle, '
            'post-shutdown N2O from the seat annulus, grain pyrolysis gas); diffusion at 1 bar homogenises over about 17 mm of the 56 mm.',
            'PURGE (E0 - 2.9 s to E0 - 0.05 s): the bleed taps vent the feed upstream of the seated pintle overboard (REPORT §2.7, H15); no '
            'flow passes the chamber, so the passage is unchanged.',
            'Relight before the light: cold N2O (vapour first on an unpurged line) enters the chamber; the cold-flow chamber pressure '
            '(about 1.5 bar abs) pushes head-face gas (flashed N2O vapour at T_sat 191 K, torch products) into about 25-33 % of the volume.',
            ('FA-1 rise (light to peak, construct t_f 1-4 ms): at the median (%.1f bar abs) and maximum (%.1f bar abs) construct peaks the '
             'relight-instant gas is compressed into the closed-end %.1f-%.1f %% of the passage (isothermal-adiabatic) and the cold-flow gas '
             'into the next %.1f-%.1f %%; %.0f-%.0f %% of the passage at the peak is head-face gas that entered during the rise (lower peaks '
             'leave a larger closed-end share). The core is compressed adiabatically: thermal penetration in 4 ms is <= %.2f mm at the peak '
             'pressure and <= %.2f mm early in the rise, against the 1.0 mm radius. What enters during the rise is the gas at the port mouth '
             '(r 20.5 mm on the head face): the lumped construct does not predict it (its head node burns every source at the case O/F by '
             'convention): MISSING.') % (P_pk[0], P_pk[1], relg[0], relg[1], cfg[0], cfg[1], head_share[0], head_share[1], pen_peak, pen_max)],
        relight_instant_c_m_s=relight,
        hot_products_frozen=hot,
        N2O_saturated_vapour=sat, N2O_flash_limit_bar={k: r(v, 2) for k, v in p_flash.items()},
        N2O_isentropic_to_peak=isen, N2O_wall_cooled_at_peak=wall, N2O_single_phase_minimum=scan,
        N2O_single_phase_minimum_dense=dict(pressures_bar=[P_dense[0], P_dense[-1]], step='2 bar plus 72.0-73.0 bar; T 250-600 K at 0.5 K, '
                                                                                     'refined to 0.02 K', values=dense,
                                            minimum=dict(c_m_s=c_lo_gas, at=kmin, T_K=dense[kmin]['at_T_K'], phase=dense[kmin]['phase']),
                                            minimum_below_70bar=dict(c_m_s=c_sub_min, at=k_sub, T_K=sub[k_sub]['at_T_K'])),
        N2O_isentropic_from_saturation_minimum=dict(c_m_s=r(isd[0], 1), entry_bar=r(isd[1], 2), peak_bar=r(isd[2], 2),
                                                    rule='saturated vapour at an entry pressure <= the flash limit, compressed isentropically to '
                                                         'a peak in the construct range'),
        air_compressed_to_peak=air, thermal_penetration=pen, volume_fractions_at_peak=frac,
        construct_head_peak_bar=dict(min=r(P_rng[0], 2), median=r(P_pk[0], 2), max=r(P_pk[1], 2), source='fa1_histories_solver_v2p4b.npz (896 cases)'),
        c_design_min_m_s=r(c_lo_gas, 1), c_isentropic_N2O_min_m_s=r(c_isen_min, 1),
        c_products_frozen_range_m_s=[r(min(v['c_frozen_m_s'] for v in hot.values()), 0), r(max(v['c_frozen_m_s'] for v in hot.values()), 0)],
        c_needed_T_le_1ms_Vend0_m_s=r(T_c222 * c_ref, 1),
        answer=dict(
            at_relight=('c of the relight-instant gas at 1 atm and the A1 wall temperature: air %.0f-%.0f m/s, cooled first-burn products '
                        '(O/F 3-8, water saturated) %.0f-%.0f m/s, N2O vapour %.0f-%.0f m/s (DERIVED, CoolProp / Cantera frozen '
                        'composition); composition MISSING') % (
                min(v['air_m_s'] for v in relight.values()), max(v['air_m_s'] for v in relight.values()),
                min(v[k] for v in relight.values() for k in v if k.endswith('water_saturated_m_s')),
                max(v[k] for v in relight.values() for k in v if k.endswith('water_saturated_m_s')),
                min(v['N2O_vapour_m_s'] for v in relight.values()), max(v['N2O_vapour_m_s'] for v in relight.values())),
            at_FA1_instant=('c in the passage core at the FA-1 peak (construct head peaks %.1f-%.1f bar abs, median %.1f) depends on what '
                            'enters during the rise (MISSING): burned products %.0f-%.0f m/s (frozen, T_HP, O/F 3-8; higher after '
                            'compression); unburned N2O that flashed at <= %.1f bar and was compressed isentropically >= %.0f m/s (entry '
                            '%.1f bar, peak %.1f bar); N2O at the wall temperature (wall layer, or a slow rise) %.0f-%.0f m/s at the median and '
                            'maximum peaks; the single-phase N2O minimum anywhere in the peak range is %.0f m/s (%s, %.1f K, %s), %.0f m/s '
                            'below 70 bar; the compressed relight-instant air at the closed end 350-%.0f m/s (isothermal-isentropic).') % (
                P_rng[0], P_rng[1], P_pk[0], min(v['c_frozen_m_s'] for v in hot.values()), max(v['c_frozen_m_s'] for v in hot.values()),
                max(p_flash.values()), c_isen_min, isd[1], isd[2],
                min(w['c_range_m_s'][0] for k, w in wall.items() if abs(float(k[:-3]) - round(P_pk[0], 1)) < 0.05 or abs(float(k[:-3]) - round(P_pk[1], 1)) < 0.05),
                max(w['c_range_m_s'][1] for k, w in wall.items() if abs(float(k[:-3]) - round(P_pk[0], 1)) < 0.05 or abs(float(k[:-3]) - round(P_pk[1], 1)) < 0.05),
                c_lo_gas, kmin, dense[kmin]['at_T_K'], dense[kmin]['phase'], c_sub_min,
                max(v['isentropic_c_m_s'] for d in air.values() for k, v in d.items() if float(k[:-3]) >= P_pk[0] - 0.05)),
            bound=('Combustion cannot bound c better than 222-400 m/s in the direction that matters. For a gas-filled passage the lower end '
                   'is about %.0f m/s (N2O near its critical point, a peak near 72.5 bar with the gas near 310 K) and about %.0f m/s for N2O '
                   'vapour compressed from saturation (the core of a 1-4 ms rise), not 222 m/s; if liquid N2O reaches the passage (spray or '
                   'condensate below the critical pressure) the two-phase sound speed is far lower and is not bounded here. The upper end is '
                   'about %.0f m/s (burned products), not 400 m/s; a higher c only shortens the period. Design value for a <= 1 ms check: '
                   'c_min = %.0f m/s with the passage kept free of liquid N2O (CONDITIONAL; TO-VERIFY at IGN-1 / B-PC-1 with the port '
                   'ringing recorded).') % (c_lo_gas, c_isen_min, max(v['c_frozen_m_s'] for v in hot.values()), c_lo_gas),
            period_scaling=('on Mechanical\'s CC-1 V_end = 0 row (lossless 1-D, uniform gas: T = %.3f ms at %.0f m/s, T proportional to 1/c): '
                            'T = %.3f ms at %.0f m/s (c_min), %.3f ms at %.0f m/s (isentropic N2O), %.3f ms at %.0f m/s (products). '
                            'c >= %.1f m/s is needed for T <= 1 ms on CC-1 at V_end = 0, so CC-1 does not meet 1 ms at c_min; Mechanical '
                            'recomputes the CC-2 passage (<= 30 mm) at c_min.') % (
                T_c222, c_ref, T_cc1(c_lo_gas), c_lo_gas, T_cc1(c_isen_min), c_isen_min,
                T_cc1(min(v['c_frozen_m_s'] for v in hot.values())), min(v['c_frozen_m_s'] for v in hot.values()), T_c222 * c_ref)),
        tags=dict(properties='DERIVED (CoolProp HEOS N2O/air/water; Cantera gri30 frozen equilibrium products, as the v2.4a construct)',
                  wall_temperatures='SIM (Mechanical, interim, 20 C start ASSUMED)', composition='MISSING (not modelled)',
                  peaks='SIM construct', status='not physical evidence'))
    return out


def main(D, H, MP, out_f):
    for f, h in EXPECT.items():
        assert sha16(os.path.join(D, f)) == h, (f, sha16(os.path.join(D, f)))
    for f, h in EXPECT_HUB.items():
        assert sha16(os.path.join(H, f)) == h, (f, sha16(os.path.join(H, f)))
    for f, h in EXPECT_MECH.items():
        assert sha16(os.path.join(MP, f)) == h, (f, sha16(os.path.join(MP, f)))
    lit_lift_f = os.path.join(D, 'v2p4b/start_level_lit_thrust_0p21776mm_v2p4b.json')
    out = dict(version='v2.4b', date='2026-10-13', script='02-combustion/src/lead_items_203_205_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='coordinator relays of LEAD CHANGELOG lines 203-204 (items 1-7) and 205 (Pc port gas sound speed)',
               inputs=dict(data={f: h for f, h in EXPECT.items()}, hub=EXPECT_HUB, mechanical_workdir=EXPECT_MECH,
                           lit_history_0p21776mm=(sha16(lit_lift_f) if os.path.exists(lit_lift_f) else 'MISSING')),
               item1_purge_basis=purge_basis(D, H), item2_start_level_lift=start_level_lift(D, H, lit_lift_f),
               item3_E2_rule=e2_rule(D, lit_lift_f), item4_firmware_sources=firmware_sources(H), item5_fa1=fa1_items(D),
               item6_classes_500N=classes_500N(D), item7_A1_duration=a1_note(), item8_pc_port_gas=pc_port_gas(D, MP))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    for k in ('item1_purge_basis', 'item2_start_level_lift', 'item3_E2_rule', 'item5_fa1', 'item7_A1_duration', 'item8_pc_port_gas'):
        print('==', k, json.dumps(out[k], default=float)[:2500])
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:5])
