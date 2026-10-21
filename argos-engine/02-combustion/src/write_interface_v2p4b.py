"""combustion.json v2.4b from the published v2.4a by keyed edits (Combustion v2.4b, 2026-10-13).

Answers REV-COMB-3 (reviews/REVIEW-COMBUSTION-R3.md a786101f28d45d6f, REVISE (targeted)) R3-01..R3-17, folds the lead decisions of
CHANGELOG lines 186 and 194, and the coordinator relays of lines 203-205.  Every v2.4a key is kept.  A value replaced in v2.4b moves
to a sibling key '<key>_superseded' (the v2.4a value, the replacing version and the reason); a replaced list item moves to
'<list key>_superseded' under its index.  v2.4b content is added under new keys.  Numbers are read from the v2.4b data files and
the specifications, whose hashes are asserted.
usage: python -I write_interface_v2p4b.py V24A_JSON DATA_V2P4B_DIR SPEC_T1T4 SPEC_CF4 OUT_JSON
"""
import copy, hashlib, json, os, sys
sys.dont_write_bytecode = True
V24A = '5237d4584bad38c4'
EXP = {'release_hold_v2p4b.json': 'a926426da0e6e436', 'release_hold_records_v2p4b.csv': '59e7f44e44fbfeef',
       'population_statements_v2p4b.json': 'bffabc97aee6a5cb',
       'fa1_spectra_v2p4b.json': '372b8078d7a90e75', 'fa1_spectra_dense_v2p4b.json': '7468996959538d0f',
       'fa1_pressure_spectra_v2p4b.csv': '55df65344f35759b', 'fa1_thrust_spectra_v2p4b.csv': '288a2294151e3760',
       'fa1_pressure_spectra_dense_v2p4b.csv': '4a4ebb65b38a9a03', 'fa1_thrust_spectra_dense_v2p4b.csv': '072f2e0f2987fda5',
       'fa1_histories_solver_v2p4b.npz': '399bf43d1c09de24', 'cold_flow_start_lift_v2p4b.json': '28ce48092f33da1b',
       'start_level_lit_thrust_v2p4b.json': 'ae2038c5141b7f73', 'start_level_lit_thrust_v2p4b.csv': 'f6ac2a4da04f8d45',
       'start_level_lit_thrust_0p21776mm_v2p4b.json': '10cdc03154b95216', 'start_level_lit_thrust_0p21776mm_v2p4b.csv': 'c073d4f993f8c412',
       'tank_outlet_dip_v2p4b.json': '6c11d3c19afe983c', 'nozzle_lip_melt_in718_v2p4b.json': '23b85b7febb90c60',
       'test_budgets_v2p4b.json': 'c0e4ce35659f21fa', 'lead_items_203_205_v2p4b.json': 'e20a8b8c33af9162',
       'a1_profile_line213_v2p4b.json': '46b6a1c6efec0351'}
EXP_SPEC = {'T1-T4': 'b0c42b09ba47cb9c', 'CF-4': '86cd01e34c28aa82'}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
src, dd, spec_t, spec_c, out = sys.argv[1:6]
assert sha(src) == V24A, 'combustion.json is not v2.4a'
for f, h in EXP.items():
    assert sha(os.path.join(dd, f)) == h, (f, sha(os.path.join(dd, f)))
assert sha(spec_t) == EXP_SPEC['T1-T4'], sha(spec_t)
assert sha(spec_c) == EXP_SPEC['CF-4'], sha(spec_c)
J = lambda f: json.load(open(os.path.join(dd, f)))
d = json.load(open(src)); d0 = copy.deepcopy(d)
T = lambda v, tag, **k: dict(v=v, tag=tag, **k)
VER = 'v2.4b (2026-10-13)'
R = 'REPORT v2.4b'
N_SUP = []


def supersede(container, key, new, why):
    sk = key + '_superseded'
    assert sk not in container, sk
    container[sk] = dict(v=container[key], version='v2.4a', superseded_by=VER, why=why)
    container[key] = new
    N_SUP.append(key)


def supersede_item(container, listkey, idx, new, why):
    sk = listkey + '_superseded'
    ent = container.setdefault(sk, dict(items={}, version='v2.4a', superseded_by=VER))
    assert str(idx) not in ent['items']
    ent['items'][str(idx)] = dict(v=container[listkey][idx], why=why)
    container[listkey][idx] = new
    N_SUP.append(f'{listkey}[{idx}]')


# ------------------------------------------------------------------ data (asserted against the text below)
RH = J('release_hold_v2p4b.json'); G = RH['groups']; PROF = ('ramp_to_200N', 'ramp_to_500N', 'lift_flow_held')
assert (G['linboth|LO']['ramp_to_200N']['hold_needed_s'], G['linboth|LO']['ramp_to_500N']['hold_needed_s']) == (0.31, 0.19)
assert G['linboth|LO']['lift_flow_held']['hold_within_W'] is False and G['lin0.0|LO']['ramp_to_200N']['hold_needed_s'] == 0.30
for g in ('lin0.0|LO', 'lin1.0|LO', 'linboth|LO', 'linboth|HI'):
    b = G[g]['ramp_to_200N']['by_hold']['0.30']
    assert b['optimistic']['max'] == 0.0 and b['conservative']['max'] == 0.0, g
PS = J('population_statements_v2p4b.json')['counts']
assert PS['lin0.0|LO|lift_flow_held']['frac_P_success_zero'] == 0.8185 and PS['lin1.0|LO|lift_flow_held']['frac_P_success_zero'] == 0.7741
assert PS['lin0.0|LO|ramp_to_200N']['frac_P_success_zero'] == 0.6 and PS['lin1.0|LO|ramp_to_200N']['frac_P_success_zero'] == 0.5296
assert PS['lin1.0|HI|ramp_to_200N']['n_P_success_one'] == 20
DN = J('fa1_spectra_dense_v2p4b.json'); PD = DN['period_domain']
v = lambda b, k: round(PD[b][k]['value_bar'], 1)
assert (v('T_le_0p1ms', 'head|all'), v('T_0p1_to_1ms', 'head|baseline'), v('T_0p1_to_1ms', 'head|all'), v('T_1_to_20ms', 'head|all')) == \
       (93.6, 102.5, 120.3, 146.9)
tc02 = [b for b in DN['mechanical_modal_bands'] if b['dominant_part'] == 'ENG-TC-02'][0]
assert round(tc02['max_in_band_baseline']['value_bar'], 1) == 99.5 and round(tc02['max_in_band_all']['value_bar'], 1) == 111.7
TH = DN['thrust']
import numpy as np
Tt = np.array(DN['periods_ms']['thrust'])
def thr(grp, k, t):
    x = DN['envelopes'][grp][k]
    return round(float(np.interp(t, Tt, np.array(x['value'] if isinstance(x, dict) else x))), 0)
GB, GA = 'vapour_once|rounded_Cd1.0|grid_OF4-12|all', 'all|all|incl_OF3-3.5|all'
thr_tab = {f'{t:g}ms': dict(baseline_whole_Cf1p35_N=thr(GB, 'F_whole_Cf1.35_N', t), all_case_whole_Cf1p35_N=thr(GA, 'F_whole_Cf1.35_N', t),
                           all_case_whole_QSx0p975_N=thr(GA, 'F_whole_QSx0.975_N', t), all_case_above_Cf1p35_N=thr(GA, 'F_above_Cf1.35_N', t))
           for t in (20.0, 25.0, 40.0, 100.0, 200.0)}
assert thr_tab['25ms']['all_case_whole_Cf1p35_N'] == 1743.0 and thr_tab['100ms']['all_case_whole_Cf1p35_N'] == 1032.0
CF = J('cold_flow_start_lift_v2p4b.json'); CS = CF['summary']
assert [round(x, 2) for x in CS['F_bound_N']] == [12.5, 13.33] and [round(x, 1) for x in CS['mdot_limit_no_heat_g_s']] == [52.6, 56.3]
LIT = J('start_level_lit_thrust_v2p4b.json')['summary']; LIT2 = J('start_level_lit_thrust_0p21776mm_v2p4b.json')['summary']
assert round(LIT['F_min_over_corners_in_E2_to_E2p0p5_N'], 2) == 30.38 and LIT['n_corners_never_ge_37p16N_in_window'] == 8
DIP = J('tank_outlet_dip_v2p4b.json')['summary']
NZ = J('nozzle_lip_melt_in718_v2p4b.json'); NS = NZ['summary']
assert [round(x, 2) for x in NS['solidus|T0_342C']['L1_lumped_1mm_s']] == [1.10, 5.88]
TB = J('test_budgets_v2p4b.json')
assert round(TB['T1_100pct_2t_8s_kg']['4.5MPa'], 3) == 1.928 and round(TB['T1_100pct_max_2t_s_on_flight_tank'], 2) == 6.04
LI = J('lead_items_203_205_v2p4b.json')
I1, I2, I3, I4, I5, I6, I7, I8 = (LI[k] for k in ('item1_purge_basis', 'item2_start_level_lift', 'item3_E2_rule', 'item4_firmware_sources',
                                                 'item5_fa1', 'item6_classes_500N', 'item7_A1_duration', 'item8_pc_port_gas'))
HS_A1 = I2['values_before_CF3']['A1_relight_286p70K_mm']; assert HS_A1 == 0.21776
PB = I1['vented_mass_g']
m255 = PB['2.60 s flow (2.55 s both-open cap + 0.05 s valve-time offset, Electronics ASSUMED 30/80 ms)']
assert abs(m255['combustion_bound_open_g'] - 76.05) < 0.02
c_min = I8['c_design_min_m_s']; c_iso = I8['c_isentropic_N2O_min_m_s']; c_hot = I8['c_products_frozen_range_m_s']
spec_files = {'02-combustion/T1-T4-REGRESSION-SPEC.md': dict(version='v3 (v2.4b)', sha256_16=sha(spec_t)),
              '02-combustion/CF-4-SPEC.md': dict(version='v2.1 (v2.4b)', sha256_16=sha(spec_c))}

# ------------------------------------------------------------------ header (keys kept)
d['revision_history'] = list(d['revision_history']) + [d['revision_note']]
d.update(version='v2.4b', date='2026-10-13',
         revision_note=('v2.4b (2026-10-13): targeted patch for REV-COMB-3 (a786101f28d45d6f, REVISE targeted) R3-01..R3-17 with the lead '
                        'decisions of CHANGELOG lines 186 and 194 and the coordinator relays of lines 203-205: release-hold population table by '
                        'command profile and per-record classes (release_hold_v2p4b); FA-1 head and aft pressure spectra to 50 ms with the '
                        'LEAD 194 (1) period domain and the long-period thrust spectrum (fa1_spectra_v2p4b); cold-flow start-lift bound '
                        'CONDITIONAL with the CF-3 start-lift acceptance (cold_flow_start_lift_v2p4b); THE start-level lift (start_level_lift_v2p4b) '
                        'and its lit thrust history (start_level_lit_thrust_v2p4b); H19 for the IN718 lip; stand dynamic Pc channel proof rating; '
                        'NZ-01 frozen prediction; tank-outlet dip onset; purge flow basis and the 2.55 s cap; E2 rule; firmware constant sources; '
                        'Pc port passage gas sound speed (line 205); T1-T4 v3 and CF-4 v2.1; stale text replaced (values kept under '
                        '*_superseded keys); LEAD line 213: A1 apogee target about 210 m, the 300 m and 285 m A1 values kept as comparators '
                        '(a1_apogee_target_v2p4b). All v2.4a keys kept.'),
         status=('v2.4b REVISION (digital only, Por revisar). Design point unchanged. No number is MEASURED. The relight claim is gated by CF-4; '
                 'FA-1 is accepted for design continuation only. Decided by the lead and folded here: L* = 1.3 s with no unpurged relight '
                 'below it (186 (1)); the R2 command hold at the start level (186 (2), margin CONDITIONAL 194 (4)); the FA-1 period domain '
                 '(194 (1)), which Combustion\'s dense spectrum exceeds in two domains (OI-41, for the lead); the unpurged alternative NOT '
                 'ADOPTED (204 (2)). A1 apogee target about 210 m (213, founder): the A1 values here are 300 m / 285 m comparators until '
                 'the 210 m record; B1 still governs sizing. Nothing here is physical approval.'),
         supersedes='combustion.json v2.4a (5237d4584bad38c4), kept as 02-combustion/data/v2/combustion_interface_v2p4a_as_published.json '
                    'and 02-combustion/superseded/v2p4a/combustion.json')
d['inputs_read']['REVIEW-COMBUSTION-R3.md'] = 'reviews/REVIEW-COMBUSTION-R3.md a786101f28d45d6f (REV-COMB-3, REVISE targeted)'
d['inputs_read']['CHANGELOG lines 186-206'] = 'interfaces/CHANGELOG.md lead decisions 186, 194, 203, 204, 205 (and 206 read for status)'
d['inputs_read']['electronics_v2p10'] = ('electronics.json v3 38bf149f368c1d4c; 06-electronics/results/bleed_driver_v1.json 298b405b0621acd5; '
                                         'firmware config.h 0880af5a27880a5b and engine_params.h 6b73317fcd7d07ac (read only)')
d['inputs_read']['mechanical_pc_interim'] = ('mechanical v351/pc/pc_line_period_v1.json 7f5d8950516d98f2, pc_transducer_temperature_v1.json '
                                             '774519536f26c762 (interim, Mechanical workdir; read only); materials_v1p4.json 18aa13a888b1e6f3')
d['inputs_read']['gnc_v3p1'] = 'gnc.json v3.1 4f3209323b0e0ed4 (ledger v3d dry mass 13.6706 kg)'
d['inputs_read']['IN718_datasheet'] = ('Special Metals SMC-045 (2007) Table 2, melting range 1260-1336 C, read through the web-fetch reader '
                                       '(PDF download refused by the proxy; TO-ARCHIVE)')
d['files']['v2p4b'] = T(dict(report='02-combustion/REPORT.md v2.4b', response='02-combustion/REVISION-RESPONSE-R3.md',
                             data='02-combustion/data/v2p4b/ (HASHES.txt, sha256sum -c format)', specs=spec_files,
                             writer='02-combustion/src/write_interface_v2p4b.py',
                             archive_v2p4a='02-combustion/superseded/v2p4a/ (REPORT, REVISION-RESPONSE-R2, combustion.json, CF-4, T1-T4)'), 'index')

# ------------------------------------------------------------------ stale values replaced (R3-09, R3-11); old values under *_superseded
ig = d['igniter']['sequence']['v']
s0 = ig['start'][0]
supersede(s0, 'action', (
    'PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s (LEAD 186 (1), ADOPTED for both wall heat-transfer brackets; '
    'replaces the 1.7 s interim of 181 (2) and the PROVISIONAL rule of 175 (3)); below L* no purge and no unpurged relight on that pass '
    '(drogue descent; vehicle loss in the FMEA); the ECU unpurged RELIGHT guard enforces it (LEAD 203 (7), v2.11). A commit lead below '
    'about 2.1 s is not counted as a landing (LEAD 204 (1), GNC). When committed: MV latch and opener ramp (0.35 s) with the pintle seated; '
    'V1 and V2 open; both taps flow 2.5 s; the close command leads by the measured valve closing time so the flow stops by E0 - 0.05 s '
    '(scheduled flow end, LEAD line 164). Closure (V1 first, on P_mid) is confirmed by the closure deadline <= the torch gate (Electronics: '
    'E0 + 0.15 s), otherwise BLEED_FAULT (see E1). ECU both-open cap <= 2.55 s (LEAD 203 (3)); vented mass on the Combustion record basis '
    '<= %.2f g at 2.50 s and <= %.2f g at 2.60 s of flow (purge_basis_v2p4b)') % (PB['2.50 s flow (nominal schedule)']['combustion_bound_open_g'],
                                                                                   m255['combustion_bound_open_g']),
    'LEAD 186 (1) adopted L* = 1.3 s; 194 (3) and 204 (2) settle the unpurged alternative (NOT ADOPTED); 203 (3) sets the cap')
s3 = ig['start'][3]
supersede(s3, 'action', s3['action'].replace(
    'Then the pintle is commanded to the ignition lift 0.2039 mm (t_lift 29.6 ms; CF-3 lift table keeps <= 37.1 g/s at 20 C, <= 37.4 g/s at '
    'the A1 state).',
    'Then the pintle is commanded to THE start-level lift h_s(T_tank at E0), the row of the ignition-lift table: 0.2039 mm at 20 C, '
    '0.21776 mm at the A1 relight state 286.70 K (t_lift 28.7-29.5 ms); CF-3 calibrates the table to <= 37.1 g/s at 20 C and <= 37.4 g/s at '
    'the A1 state and measures at the commanded lift with the encoder recorded (start_level_lift_v2p4b; LEAD 203 (7)).'),
    'LEAD 203 (7): Combustion defines THE start-level lift; the ECU hold lift equals it')
assert 'THE start-level lift' in s3['action']
supersede_item(ig, 'relight', 3, ('light window W 0.65 s; E0 -> E2 max 0.626 s on the worst purged line state (rg01_line_states_v2p4); the 0.81 s '
                                  'plan holds on the predictor path (PURGE committed with lead >= L* = 1.3 s; LEAD 181 (2) scope); after a '
                                  'commit lead below L* there is no relight on that pass'),
               'LEAD 181 (2): "the 0.81 s plan holds" is scoped to the predictor path (R3-09)')
supersede_item(ig, 'arm_preconditions', 3, (
    'Pc transducer: flight unit RESELECTED by Electronics (LEAD 205): miniature seat-mounted, body within 12 mm x 30 mm, front dead volume '
    '<= 20 mm3, proof >= 1.1 x 102 = 112 bar abs (lead basis; Combustion\'s all-case 0.1-1 ms spectrum gives 1.1 x 120.3 = 132 bar abs, OI-41), '
    'range covering the 45 bar MEOP with the 30 bar abort resolvable, >= 120 C; over-range bit and above-full-scale flag (LEAD 203 (1)(a)); '
    'P_torch 0-70 bar class (ENG-09); P_feed, P_tank healthy; Pc reads ambient'),
    'LEAD 205 reselects the flight Pc transducer; the 0-70 bar class stays for P_torch only')
fm = d['fmea_input']['v']
supersede_item(fm, 'bleed', 4, (
    'B-5 purge truncated or not committed: PURGE commits iff the lead to the plain trigger is >= L* = 1.3 s (LEAD 186 (1)); below L* no purge '
    'and no unpurged relight on that pass (ECU guard, LEAD 203 (7)): drogue descent, vehicle loss in the FMEA; a commit lead below about '
    '2.1 s is not counted as a landing (LEAD 204 (1)); truncated-purge P_abort up to 0.098 at 1.8 s of flow, 1.0 at 1.0 s'),
    'LEAD 186 (1) replaces the PROVISIONAL 1.7 s rule')
supersede_item(fm, 'bleed', 5, (
    'B-6 unpurged relight: EXCLUDED by design (LEAD 186 (1); ECU unpurged RELIGHT guard, 203 (7)). The unpurged alternative (GNC comparator '
    'P6c: hold >= 0.30 s on the 200 N ramp, >= 0.19 s on the 500 N ramp, none admissible with the flow held at the start lift; '
    'release_hold_v2p4b) is NOT ADOPTED (LEAD 204 (2)) and not admissible with Pc invalid (194 (3)). If the guard failed: every light of the '
    'LO worst state is followed by a 23.4 cm3 vapour gap after the drogue release -> A3 abort, dead vehicle released (H20)'),
    'LEAD 186 (1), 194 (3), 203 (7), 204 (2)')
supersede(fm, 'flameout_pc_invalid_v2p4a', (
    'B-7 undetected flame-out with Pc invalid (R2 branch): the open-loop lift keeps N2O flowing; cold-flow thrust <= %.1f-%.1f N at the '
    'start level (bound; %.1f N at h_s = 0.21776 mm, A1 state), alone > 37.16 N above about 200 N command (bound). Mitigation ADOPTED in '
    'design (LEAD 186 (2)): open-loop command held at the start level (THE start-level lift) while the drogue is attached with Pc invalid; '
    'its 16.31 N W10 margin is CONDITIONAL on Cd x A x G at the start lift (194 (4); CF-3 start-lift point: F <= 16.31 N minus the heat '
    'allowance, or mdot <= 52.6-56.3 g/s); heat TO-VERIFY is the injector-body and feed soak-back temperature at the relight (2.8-3.7 kW '
    'at tank pressure). FLAMEOUT_OPT (Electronics v2.10) aborts on the photodiode in RUN with Pc invalid (cold_flow_start_lift_v2p4b)')
    % (CS['F_bound_N'][0], CS['F_bound_N'][1], I2['cold_flow_bound_at_hs']['A1_relight_N']),
    'LEAD 186 (2) adopted the command hold; 194 (4) states the margin CONDITIONAL')
dr = d['drogue_release_hold']['v']
supersede(dr, 'line175_5_note_v2p4a', (
    'LEAD line 175 (5): the time-only 0xFFFF term is REPLACED in design by R2 (Pc invalid: release iff ECU RUN AND accelerometer thrust '
    '>= 37.16 N for 3 frames at 100 Hz, otherwise hold the drogue and ECU ABORT at t_E2 + 0.5 s: pcf_tmax 0.5 s, LEAD 181 (4); 0.8 s not '
    'adopted). While the drogue is attached with Pc invalid the open-loop command is held at the start level (LEAD 186 (2)); GNC R2 v2 '
    'uses F_cold plus the grain_q1d start-level lit history (start_level_lit_thrust_v2p4b), not 62.5 N x pcf_k (194 (4); SUPERSEDED 204 (4)). '
    'The Pc-valid terms are unchanged. Unpurged starts are excluded by design (186 (1)); on such a start the Pc-valid term would release '
    'before the post-light vapour gap (H20)'),
    'LEAD 181 (4) (t_E2 + 0.5 s), 186 (2), 194 (4) (R3-09)')
dr['line194_4_lit_history_v2p4b'] = T(dict(
    at_0p21776mm_A1=dict(E2_s=LIT2['E2_s_range'], F_min_max_E2_to_E2p0p5_N=[round(LIT2['F_min_over_corners_in_E2_to_E2p0p5_N'], 2),
                                                                             round(LIT2['F_max_over_corners_in_E2_to_E2p0p5_N'], 2)],
                         corners_never_ge_37p16N=LIT2['n_corners_never_ge_37p16N_in_window'],
                         latest_first_ge_37p16N_after_E2_s=LIT2['latest_first_t_ge_37p16N_after_E2_s']),
    at_0p2039mm=dict(E2_s=LIT['E2_s_range'], F_min_max_E2_to_E2p0p5_N=[round(LIT['F_min_over_corners_in_E2_to_E2p0p5_N'], 2),
                                                                      round(LIT['F_max_over_corners_in_E2_to_E2p0p5_N'], 2)],
                     corners_never_ge_37p16N=LIT['n_corners_never_ge_37p16N_in_window'],
                     latest_first_ge_37p16N_after_E2_s=LIT['latest_first_t_ge_37p16N_after_E2_s']),
    file='start_level_lit_thrust_v2p4b'), 'SIM grain_q1d v2 (quasi-steady, ASSUMED laws/bands; 72 corners); not physical evidence')
supersede(d['throat_insert_line183_note_v2p4a'], 'v', (
    'LEAD 186 (3) as worded by 194 (5): NZ-01 graphite throat insert accepted TEST-BASED if mechanically captured; refutation is any of: a '
    'throat-area change more than 2 % beyond the erosion predicted for that firing, the prediction frozen before the firing and updated only '
    'with earlier firings; a non-axisymmetric step; a missing fragment. Combustion\'s frozen-prediction procedure: nz01_criterion_v2p4b'),
    'LEAD 186 (3) decided the criterion; 194 (5) fixes its wording (R3-15)')
fa = d['fa1_envelope_v2p4a']['v']
supersede(fa, 'structural_load_LEAD_173', (
    'LEAD 194 (1) (replaces 173\'s "for every part" and the 92 bar value): FA-1 equivalent static pressure at head and aft: T <= 0.1 ms: '
    '90 bar abs quasi-static; 0.1 < T <= 1 ms: yield 93 bar abs (design), ultimate 102 bar abs (sensitivity); T > 1 ms: all-case spectrum '
    'value at the part period, or FA1S (DLF 2.0, about 151 bar abs) until Mechanical\'s modal closure. Thrust: 1.8 kN x 4 ms only for '
    'T <= 20 ms; T > 20 ms: the FA-1 long-period thrust spectrum (194 (2)). Combustion\'s dense spectrum exceeds the 194 (1) values in '
    'two domains (OI-41): fa1_spectra_v2p4b'),
    'LEAD 194 (1)-(2) (R3-02, R3-03, R3-04)')
supersede(fa, 'outflow_frozen_vs_equilibrium', fa['outflow_frozen_vs_equilibrium'].replace(
    'the 92 bar design value becomes about 92.2 bar (92.9 at 8 %); the 102 bar bracket covers both',
    'the v2.4a 92 bar design value would become about 92.2 bar (92.9 at 8 %); LEAD 194 (1) replaced it by 93 bar abs (R3-04); the 102 bar '
    'ultimate covers both'), 'LEAD 194 (1): 93 bar replaces 92 bar')
assert '93 bar abs (R3-04)' in fa['outflow_frozen_vs_equilibrium']
pr = d['purge_commit_rule_v2p4a']['v']
supersede(pr, 'rule_LEAD_175_3', ('DECIDED (LEAD 186 (1)): PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s; below it no '
                                  'purge and no unpurged relight on that pass. The PROVISIONAL 175 (3) rule (1.7 s, relight proceeds '
                                  'unpurged) is superseded; see purge_commit_rule_v2p4b'), 'LEAD 186 (1)')
supersede(pr, 'proposal', ('DECIDED: no commit by the plain trigger - L* -> no relight on that pass (LEAD 186 (1)); the ride-through and '
                           'unpurged-alternative options are NOT ADOPTED (LEAD 204 (2)); revisit only if the gate-failure probability is shown '
                           '>= 1 % per flight, or CF-4/T4 settle the unpurged start as LO and the per-record classes confirm the 0 residual'),
          'LEAD 186 (1), 204 (2)')
la = pr['line181_2_answer']
supersede(la, 'below_L_star', ('LEAD 194 (3): the "E2 + 0.22 s" hold of 186 (1) is WITHDRAWN (derived from one state). Population hold table '
                               '(release_hold_v2p4b): H >= 0.30 s on the 2500 N/s ramp to 200 N (0.31 s with the 10 ms frame margin), '
                               '>= 0.19 s on the ramp to 500 N, no admissible hold with the flow held at the start lift (0.75 s > W). '
                               'The alternative is NOT ADOPTED (LEAD 204 (2)); the classes are comparator data for GNC P4c'),
          'LEAD 194 (3) (R3-01)')
cf = d['cold_flow_thrust_v2p4a']['v']
cfp = cf['proposal']
supersede(cf, 'proposal', dict(text=('ADOPTED in design (LEAD 186 (2)): while the drogue is attached with Pc invalid the ECU open-loop command is '
                                     'held at the start level (THE start-level lift, start_level_lift_v2p4b) until release. Its 16.31 N margin '
                                     'is CONDITIONAL on Cd x A x G at the start lift (194 (4)); CF-3 start-lift point accepts it; a failure '
                                     'returns the hold level and the W10 rule to the lead'),
                               hypothesis=cfp['hypothesis'] + ' (the lit side: grain_q1d start-level lit history, start_level_lit_thrust_v2p4b)',
                               comparator=cfp['comparator'],
                               evidence_needed=('CF-3 start-lift point: mdot and load-cell F at the commanded start-level lift with the encoder '
                                                'lift recorded (cold chamber), plus the 200 N and 500 N lifts; injector-body and feed soak-back '
                                                'temperature at the relight; a post-burn N2O pulse at the start-level lift in the T series'),
                               refutation=('CF-3 at the start lift: F > 16.31 N minus the heat allowance with mdot > 52.6-56.3 g/s (LEAD 194 (4)), '
                                           'or a GNC re-fly in which the hold loses P'),
                               file='cold_flow_start_lift_v2p4b'), 'LEAD 186 (2), 194 (4) (R3-05, R3-14)')
cf['line194_4_heat_location_v2p4b'] = T(('The heat TO-VERIFY is the injector-body and feed soak-back temperature at the relight: the 2.8-3.7 kW '
                                         '(66-85 kJ/kg) threshold applies to heat added at tank pressure, before the throttling; heat added in '
                                         'the chamber at 1.03-1.3 bar converts poorly to thrust (R3-14). The finding text above keeps the '
                                         'v2.4a wording as evidence'), 'LEAD 194 (4); DERIVED')
nj = d['nozzle_joint']['v']
s342, s295, s655 = NS['solidus|T0_342C'], NS['solidus|T0_295C'], NS['solidus|T0_655C']
rr = lambda x: [round(x[0], 2), round(x[1], 2)]
supersede(nj, 'lip_melt_s', dict(
    J1_lumped_1mm=rr(s342['L1_lumped_1mm_s']), J1_FD_1mm=rr(s342['FD_1mm_depth_s']),
    J1b_lumped_1mm='not recomputed for IN718 (the 316L value is under lip_melt_s_superseded)',
    J1b_FD_1mm='not recomputed for IN718 (the 316L value is under lip_melt_s_superseded)',
    J1_IN718_T0_342C=dict(lumped_1mm=rr(s342['L1_lumped_1mm_s']), FD_1mm=rr(s342['FD_1mm_depth_s']), FD_surface=rr(s342['FD_surface_s'])),
    J1_IN718_T0_295C=dict(lumped_1mm=rr(s295['L1_lumped_1mm_s']), FD_1mm=rr(s295['FD_1mm_depth_s'])),
    J1_IN718_T0_655C=dict(lumped_1mm=rr(s655['L1_lumped_1mm_s']), FD_1mm=rr(s655['FD_1mm_depth_s'])),
    melt_C='IN718 solidus 1260 C (DATASHEET SMC-045; liquidus 1336 C)', J1b='not recomputed (316L values superseded; J1 is CONFIRMED)',
    file='nozzle_lip_melt_in718_v2p4b'), 'TC-09, which carries the J1 lip, is Inconel 718 (LEAD 177 (1)/178); R3-09, 194 (9)')
pc = d['pc_dynamic_channel']['v']
supersede(pc, 'stand', (
    '>= 10-20 kHz sampling with an anti-alias filter; flush-mounted transducer or a characterised short sense line (resonance measured); '
    'range >= 100 bar abs (FA-1 construct head peak up to 88.0 bar abs; LEAD 194 (7)); proof rating >= 1.1 x the all-case FA-1 spectrum at '
    'the transducer path period: flush mount (T <= 0.1 ms) >= 103 bar abs (1.1 x 93.6), carried as the 112 bar abs class of the flight '
    'unit (LEAD 205); path period 0.1-1 ms >= 132 bar abs (1.1 x 120.3); path period > 1 ms not acceptable for the dynamic channel; '
    'passage free of liquid N2O (pc_port_gas_v2p4b); founder instrumentation item, TO-QUOTE delivered to Sonderborg DK-6400'),
    'LEAD 194 (7) (R3-10): range >= 100 bar abs with a stated proof rating')
supersede(pc, 'flight', ('flight Pc transducer RESELECTED (LEAD 205): seat-mounted miniature unit, proof >= 112 bar abs (lead), range covering '
                         '45 bar MEOP with the 30 bar abort resolvable; control channel 1 kHz; LIGHT_SPIKE values logged at 1 kHz are LOWER '
                         'BOUNDS of a 1-3 ms spike; non-sticky over-range bit and above-full-scale flag (LEAD 203 (1)(a)); the 070BG '
                         'over-range behaviour is MISSING (B-PC-1 row, TE inquiry)'), 'LEAD 203 (1)-(2), 205')
pc['stand_proof_rating_v2p4b'] = T(dict(
    rule='proof >= 1.1 x P_eq(all cases) at the transducer path period (LEAD 205 uses 1.1 x 102 = 112 bar abs for the flight unit)',
    flush_T_le_0p1ms_bar_abs=dict(spectrum=v('T_le_0p1ms', 'head|all'), x1p1=round(1.1 * PD['T_le_0p1ms']['head|all']['value_bar'], 1),
                                  adopted=112.0),
    path_0p1_to_1ms_bar_abs=dict(spectrum=v('T_0p1_to_1ms', 'head|all'), x1p1=round(1.1 * PD['T_0p1_to_1ms']['head|all']['value_bar'], 1),
                                 adopted=132.0, baseline_spectrum=v('T_0p1_to_1ms', 'head|baseline')),
    path_gt_1ms='not acceptable (head all-case up to %.1f bar abs at 1-20 ms; the channel would not resolve the 1-3 ms spike)'
                % PD['T_1_to_20ms']['head|all']['value_bar'],
    contradiction='the lead\'s 112 bar abs uses 102 bar (the 194 (1) 0.1-1 ms ultimate); the dense all-case value is 120.3 bar abs (OI-41)'),
    'DERIVED (SDOF on SIM construct histories); proof rule DESIGN; physical rating DATASHEET of the selected unit (MISSING)')
supersede(d['t1t4_law_v2']['v'], 'spec', '02-combustion/T1-T4-REGRESSION-SPEC.md v3 (v2.4b, %s)' % sha(spec_t), 'T1-T4 v3 (LEAD 194 (8))')
cg = d['cf4_gate']
supersede(cg, 'spec_version', 'CF-4-SPEC v2.1 (v2.4b, %s)' % sha(spec_c), 'CF-4 v2.1 (LEAD 194 (8))')
pp = TB['CF4']['P1_lift_basis']
k_hs = [k for k in pp if k.startswith('0.21776')][0]; k_28 = [k for k in pp if k.startswith('0.2039')][0]
supersede_item(cg['v'], 'pass_criteria', 0, (
    'P1 liquid at the pintle inlet within 18.86 cm3 of lift-flow volume after reaching the start-level lift: %.3f s at %s (A1 state), %.3f s '
    'at %s (v2.8 basis) (CF-4 v2.1; volume form)') % (pp[k_hs]['P1_after_lift_s'], k_hs, pp[k_28]['P1_after_lift_s'], k_28),
    'CF-4 v2.1: P1 in volume form at THE start-level lift (LEAD 203 (7))')
cg['v']['baseline_v2p4b'] = ('re-baselined on the frozen v3.5.1 bleed path (LEAD 194 (8)); bleed-path part numbers and lengths are taken from '
                             'Mechanical\'s v3.5.1 freeze (mechanical.json v2.2 not yet published: MISSING in the hub)')
cg['tag'] = cg['tag'] + '; CF-4-SPEC v2.1 (v2.4b): red lines, abort criteria, IS-1/IS-2 preparation, probe threshold, budget (194 (8))'
am = d['abort_matrix_v2p4']['v']
supersede(am, 'A3_unpurged_note_v2p4a', am['A3_unpurged_note_v2p4a'] + '; unpurged relight excluded by design (LEAD 186 (1); ECU guard 203 (7))',
          'LEAD 186 (1), 203 (7)')
oi6 = d['open_interface_issues'][5]; assert oi6['id'] == 'OI-6'
supersede(oi6, 'status', 'RE-OPENED by LEAD 205: the flight Pc transducer is reselected (seat-mounted, proof >= 112 bar abs per the lead; '
                         'Combustion\'s all-case 0.1-1 ms value gives 132 bar abs: OI-41); Electronics selects, Mechanical makes the CC-2 head',
          'LEAD 203 (2), 205')
to = d['tank_outlet_coverage_v2p4a']['v']['min_liquid_for_quasistatic_coverage_g']
supersede(to, 'margin', 'quasi-static coverage needs 13.6 mm of liquid (78.6-82.5 g); 766 g remains at the end of the purge flow, 9.3-9.7x '
                        '(LEAD 194 (5) wording; outlet geometry still MISSING, OI-32)', 'LEAD 194 (5) (R3-16)')

# ------------------------------------------------------------------ new v2.4b blocks
d['purge_commit_rule_v2p4b'] = T(dict(
    rule='PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s; below L* no purge and no unpurged relight on that pass',
    basis='LEAD 186 (1) (adopted for both LO and HI); 194 (3) (baseline unchanged); 204 (1) (L* stays; a commit lead below about 2.1 s is not '
          'counted as a landing; nominal leads >= 2.65 s); 203 (7) (ECU unpurged RELIGHT guard, v2.11)',
    unpurged_alternative='NOT ADOPTED (LEAD 204 (2)); comparator data: release_hold_v2p4b',
    ecu_cap='both-open cap <= 2.55 s (LEAD 203 (3)); Combustion basis in purge_basis_v2p4b: %.2f g on the bound at 2.60 s of flow, at the 76 g '
            'limit within %.2f g; strict <= 76 g needs both-open <= %.3f s (OI-42)' % (m255['combustion_bound_open_g'],
                                                                                      m255['combustion_bound_open_g'] - 76.0,
                                                                                      I1['cap_for_76g']['both_open_s_with_0p05_offset']),
    LO_HI='open: CF-4 generation runs and T4 measure it (LEAD 186 (1))'), 'LEAD decisions; Combustion SIM/DERIVED basis')
d['purge_basis_v2p4b'] = T(I1, 'DERIVED from SIM purge records (ASSUMED Cd 0.70, slip brackets); lead_items_203_205_v2p4b item 1')
d['release_hold_v2p4b'] = T(dict(
    question='R3-01; LEAD 194 (3): drogue-release hold over the PURGE NOT RUN record population by post-E2 command profile',
    table={g: {p: dict(hold_needed_s=G[g][p]['hold_needed_s'], within_W=G[g][p]['hold_within_W'],
                       latest_trip_s=round(G[g][p]['latest_trip_sup_s'], 4),
                       mean_P_success_worst=round(G[g][p]['mean_P_success_worst_convention'], 4)) for p in PROF} for g in G},
    residual_at_0p30s_ramp_200N='0 released-then-A3 in every group, both conventions; the table value 0.31 s adds the 10 ms frame margin',
    definitions=RH['definitions'], notes=RH['notes'],
    per_record_classes=I6, population_statements=dict(file='population_statements_v2p4b.json', counts=PS),
    E2_rule=dict(statement=I3['statement'], shift_bound_s=I3['shift_bound_s'], holds_from_ECU_E2_bound=I3['holds']),
    withdrawn='E2 + 0.22 s of LEAD 186 (1): WITHDRAWN (194 (3))',
    status='the unpurged alternative is NOT ADOPTED (LEAD 204 (2)) and not admissible with Pc invalid (194 (3)); comparator data for GNC P4c',
    files=dict(json='release_hold_v2p4b.json a926426da0e6e436', csv='release_hold_records_v2p4b.csv 59e7f44e44fbfeef')),
    'SIM on ASSUMED delays + DERIVED line states; bracket records, NOT probability-weighted')
d['E2_rule_v2p4b'] = T(I3, 'DERIVED bound from stored SIM (no re-run)')
d['fa1_spectra_v2p4b'] = T(dict(
    question='R3-02/R3-03/R3-04; LEAD 194 (1)-(2): head and aft pressure spectra to >= 20 ms and the long-period thrust spectrum',
    convention='equivalent static pressure P_eq(T) = p_amb + max k x for the gauge history from rest at the light; envelope of conventions '
               '(b) max(P - p_amb, 0) and (c) P - p_amb; undamped unless stated (2 % and 5 % in the JSON)',
    period_domain_bar_abs={b: {k: dict(value=round(x['value_bar'], 2), period_ms=x.get('period_ms'))
                               for k, x in PD[b].items() if isinstance(x, dict) and 'value_bar' in x} for b in PD},
    LEAD_194_1_values=dict(T_le_0p1ms=90.0, T_0p1_to_1ms_yield=93.0, T_0p1_to_1ms_ultimate=102.0, T_gt_1ms='all-case spectrum or FA1S about 151'),
    contradiction=('OI-41 (for the lead): the all-case head value exceeds 90 bar abs for T <= 0.1 ms (%.1f; baseline %.1f); for 0.1-1 ms the '
                   'baseline is %.1f and the all-case %.1f bar abs against yield 93 / ultimate 102; in the ENG-TC-02 band (0.272-0.385 ms) '
                   'baseline %.1f, all-case %.1f bar abs (undamped). FA1S (about 151 bar abs) bounds every period (max %.1f). Which group '
                   'governs each domain is the lead\'s decision; the flight Pc proof (1.1 x 102 = 112) follows from it')
                  % (v('T_le_0p1ms', 'head|all'), v('T_le_0p1ms', 'head|baseline'), v('T_0p1_to_1ms', 'head|baseline'),
                     v('T_0p1_to_1ms', 'head|all'), tc02['max_in_band_baseline']['value_bar'], tc02['max_in_band_all']['value_bar'],
                     PD['T_1_to_20ms']['head|all']['value_bar']),
    tc02_band=tc02, decomposition_90p7_vs_89p0=DN['decomposition_90p7_vs_89p0'],
    thrust=dict(long_period_equivalent_force=thr_tab, rectangle='1.8 kN x 4 ms (SDOF maximum 3.6 kN at short periods)',
                rectangle_bounds_FA1_for_T_le_20ms=TH['rectangle_bounds_FA1_for_T_le_20ms'],
                min_rectangle_over_FA1_T_le_20ms=TH['min_rectangle_over_FA1_T_le_20ms'],
                first_period_ms_FA1_exceeds_rectangle=TH['first_period_ms_FA1_exceeds_rectangle'],
                rule='LEAD 194 (2): rectangle only for T <= 20 ms; for T > 20 ms the FA-1 long-period thrust spectrum (ICD-AIRFRAME v2.1, lead)'),
    histories=I5['histories'], head_spectrum_near_6ms=I5['head_spectrum_near_6ms'],
    files=dict(json='fa1_spectra_v2p4b.json 372b8078d7a90e75 (coarse, per case)', dense='fa1_spectra_dense_v2p4b.json 7468996959538d0f',
               csv='fa1_pressure_spectra_v2p4b.csv, fa1_thrust_spectra_v2p4b.csv, *_dense_v2p4b.csv', npz='fa1_histories_solver_v2p4b.npz 399bf43d1c09de24')),
    'SIM v2.4a construct histories (ASSUMED inputs; pool plateau ASSUMED) + DERIVED SDOF; not physical evidence')
d['cold_flow_start_lift_v2p4b'] = T(dict(
    status='CONDITIONAL (LEAD 194 (4)): the 16.31 N W10 margin of the 186 (2) command hold rests on Cd x A x G at the start lift, which no test '
           'has accepted', summary=CS, acceptance_rule=CF['acceptance_rule'],
    at_THE_start_level_lift=I2['cold_flow_bound_at_hs'], heat_location=d['cold_flow_thrust_v2p4a']['v']['line194_4_heat_location_v2p4b']['v'],
    FLAMEOUT_OPT=I4['FLAMEOUT_OPT_cold_flow_text'], file='cold_flow_start_lift_v2p4b.json 28ce48092f33da1b'),
    'DERIVED (adiabatic isentropic-equilibrium bound; Cd 0.80 ASSUMED limit); not physical evidence')
d['start_level_lift_v2p4b'] = T(I2, 'DEFINITION (DESIGN) with DERIVED values; CF-3 replaces every row')
d['start_level_lit_thrust_v2p4b'] = T(dict(
    for_GNC='R2 v2 and P4c: F_cold (cold_flow_thrust_v2p4a.csv) plus this lit history, not 62.5 N x pcf_k (LEAD 194 (4); SUPERSEDED 204 (4))',
    lift_0p21776mm_A1=dict(file='start_level_lit_thrust_0p21776mm_v2p4b.json/.csv', summary=LIT2),
    lift_0p2039mm=dict(file='start_level_lit_thrust_v2p4b.json/.csv', summary=LIT, role='20 C row / low-lift sensitivity'),
    time_origin='light at t = 0; E2 per corner'), 'SIM grain_q1d v2 (ASSUMED laws/bands; quasi-steady); IGN-1 and the T series measure it')
d['nozzle_lip_melt_in718_v2p4b'] = T(dict(summary=NS, melting_range_C=NZ['melting_range_C'], starting_temperatures_C=NZ['starting_temperatures_C'],
                                          published_316L_v2p4=NZ['published_316L_v2p4'], file='nozzle_lip_melt_in718_v2p4b.json 23b85b7febb90c60',
                                          note='TC-09 barrel wall 1.8 mm (LEAD 206 (2)(a) lever) does not change the lumped 1 mm reading; the '
                                               'FD readings use a 6 mm slab and shorten if the lip section thins: re-run on the v3.5.2 geometry'),
                                     'DERIVED on ASSUMED deposition, DATASHEET melting range (PDF TO-ARCHIVE) and LITERATURE-approx properties')
d['tank_outlet_dip_v2p4b'] = T(dict(summary=DIP, wording_186_5='quasi-static coverage needs 13.6 mm of liquid (78.6-82.5 g); 766 g remains at the end '
                                                          'of the purge flow, 9.3-9.7x (LEAD 194 (5))',
                                    for_GNC='LEAD 194 (6): GNC checks the landing usable reserve against the dip onset instead of the ASSUMED 3 % '
                                            '(60 g) residual; Mechanical\'s OI-32 outlet geometry closes it',
                                    file='tank_outlet_dip_v2p4b.json 6c11d3c19afe983c'),
                               'DERIVED on LITERATURE correlation (Lubin & Springer 1967, N2O applicability TO-VERIFY), SIM map flows, DESIGN geometry')
d['test_budgets_v2p4b'] = T(dict(
    T1_100pct_2t_8s_kg=round(TB['T1_100pct_2t_8s_kg']['4.5MPa'], 3), share_of_flight_load=round(TB['T1_2t_share_of_flight_load'], 3),
    T1_max_2t_s_on_flight_tank=round(TB['T1_100pct_max_2t_s_on_flight_tank'], 2), stand_tank='MISSING (founders): the T1 2t = 8 s firing uses '
    '96 % of a 2.0 kg flight load; with a flight-size tank 2t <= 6.0 s (T1-T4 v3 states both)', CF4=TB['CF4'], series=TB['series'],
    quote='TO-QUOTE: N2O, N2 and grains delivered to Sonderborg DK-6400 (no price is assumed)', file='test_budgets_v2p4b.json'),
    'DERIVED (SIM map flows, ASSUMED durations/repeats, DESIGN loads); stand tank MISSING')
d['specs_v2p4b'] = T(spec_files, 'DESIGN test specifications; physical execution by the founders; nothing here is physical approval')
d['nz01_criterion_v2p4b'] = T(dict(
    criterion='LEAD 186 (3) as worded by 194 (5): refutation is any of: a throat-area change more than 2 % beyond the erosion predicted for '
              'that firing, the prediction frozen before the firing and updated only with earlier firings; a non-axisymmetric step; a missing '
              'fragment',
    frozen_prediction=['before firing k Combustion issues the prediction as a script + parameter file (REPORT §5.4 erosion model; kinetics '
                       'calibrated on firings 1..k-1 only; for k = 1 the v2.4 nominal kinetics), records its sha256 in the test log, and does '
                       'not change it after the firing',
                       'the prediction is evaluated on firing k\'s logged history (Pc, burn time, command trace): the function is frozen, only '
                       'its inputs come from the firing; a duty-cycle-only form is used if the log is incomplete',
                       'after firing k: measured area change (pre/post bore, founders) minus the frozen prediction; > 2 % of the throat area '
                       '= refutation; firing k then enters the calibration for k + 1'],
    consequence=('DERIVED: on firing 1 the nominal kinetics predict 1.9 % per A1-equivalent; an erosion at the literature rate (8.4-13.6 %) '
                 'would exceed it by more than 2 % and count as a refutation under the lead\'s rule (a conservative false-refutation risk), '
                 'recorded for the lead, not a rule change'),
    owners='Combustion (prediction file), founders (bore measurement)'), 'LEAD criterion; DESIGN procedure; SIM erosion model')
d['firmware_constant_sources_v2p4b'] = T(I4, 'DESIGN/DERIVED source text; Electronics confirms the mapping (read-only firmware)')
d['a1_duration_note_v2p4b'] = T(I7, 'DERIVED (linear scaling of REPORT Table 4.6 SIM values); GNC F11 as relayed (LEAD 204 (4))')
d['pc_port_gas_v2p4b'] = T(I8, 'DERIVED properties on MISSING composition; SIM wall temperatures (Mechanical interim); not physical evidence')
A1J = J('a1_profile_line213_v2p4b.json')
assert A1J['version'] == 'v2.4b'
d['a1_apogee_target_v2p4b'] = T(dict(
    target=A1J['target'],
    comparators=dict(records_300m_summary=A1J['comparators_300m_summary'],
                     records_300m={k: dict(T0_K=x['T0_K'], T_MECO_K=x['T_MECO_K'], T_relight_K=x['T_relight_K'], P_relight_bar=x['P_relight_bar'],
                                           ascent_burn_s=x['ascent_burn_s'], coast_s=x['coast_s'], ascent_cooling_K=x['ascent_cooling_K'],
                                           apex_m=x.get('apex_m'), engine_on_counter_s=x.get('engine_on_counter_s'), sha256_16=x['sha256_16'])
                                   for k, x in A1J['comparators_300m_records'].items()},
                     comparator_285m=A1J['comparator_285m']),
    statements=A1J['statements'],
    purge_scaling={k: A1J['purge_scaling'][k] for k in ('basis_T_K', 'liquid_rate_slope_g_s_per_K', 'M_2p5s_slope_g_per_K', 'T_at_76g_2p5s_K',
                                                         'T_at_76g_2p60s_K', 'T_at_80g_2p5s_K', 'T_at_80g_2p60s_K', 'rows', 'method')},
    states={k: {kk: x[kk] for kk in ('T_K', 'P_sat_bar', 'purge_all_liquid_two_taps_g_s', 'F_bound_map_lift_N', 'F_bound_h_s_N', 'h_s_ECU_mm',
                                      'map_lift_clamped')} for k, x in A1J['states'].items()},
    line208_cross_references=A1J['line208_cross_references'], missing=A1J['missing'],
    data='02-combustion/data/v2p4b/a1_profile_line213_v2p4b.json %s' % sha(os.path.join(dd, 'a1_profile_line213_v2p4b.json')),
    script='02-combustion/src/a1_profile_line213_v2p4b.py %s' % A1J['script_sha256_16']),
    'LEAD target (CHANGELOG line 213, founder decision); SIM comparators (GNC 300 m records, read only); DERIVED directions and '
    'sensitivities (records not re-run); nothing here is physical approval', src=R + ' §15.15')
_l213 = {'a1_duration_note_v2p4b': 'A1-1', 'purge_basis_v2p4b': 'A1-3', 'cold_flow_start_lift_v2p4b': 'A1-4', 'start_level_lift_v2p4b': 'A1-5',
         'start_level_lit_thrust_v2p4b': 'A1-5', 'pc_port_gas_v2p4b': 'A1-7', 'tank_outlet_dip_v2p4b': 'A1-8', 'release_hold_v2p4b': 'A1-9',
         'fa1_spectra_v2p4b': 'A1-10'}
for _k, _sid in _l213.items():
    assert _k in d and isinstance(d[_k], dict) and 'v' in d[_k], _k
    _st = [x for x in A1J['statements'] if x['id'] == _sid][0]
    d[_k]['line213_note'] = ('LEAD line 213: A1 apogee target about 210 m. The A1-profile values here are from the 300 m / 285 m records and stay as '
                             'comparators. %s: %s. Status: %s (a1_apogee_target_v2p4b)' % (_sid, _st['direction_at_210m'], _st['status']))
d['inputs_read']['CHANGELOG line 213'] = ('interfaces/CHANGELOG.md line 213 (founder decision, A1 apogee about 210 m), relayed by the coordinator; '
                                          'line text %s; lines 207-212 read for status (208 (1), (3) cross-referenced)'
                                          % A1J['inputs']['CHANGELOG line 213 text'])
d['inputs_read']['gnc_A1_records_300m'] = '01-systems-gnc/duty_cycles/DC-A1_*.csv (6 records; hashes in a1_apogee_target_v2p4b)'
d['lead_decisions_folded_v2p4b'] = T({
    '186 (1)': 'L* = 1.3 s ADOPTED: purge_commit_rule_v2p4b; igniter start[0]; fmea B-5/B-6',
    '186 (2)': 'R2 command hold ADOPTED: cold_flow_thrust_v2p4a.proposal; fmea B-7; drogue_release_hold',
    '186 (3)': 'NZ-01 criterion: throat_insert_line183_note_v2p4a; nz01_criterion_v2p4b (wording of 194 (5))',
    '186 (4)': 'interface configuration: open_items_v2p4b OI-37 (mechanical.json v2.2 not yet in the hub)',
    '186 (5)': 'tank outlet wording (194 (5)): tank_outlet_coverage_v2p4a margin; tank_outlet_dip_v2p4b',
    '194 (1)-(2)': 'FA-1 period domain and thrust domain: fa1_envelope_v2p4a.structural_load_LEAD_173; fa1_spectra_v2p4b (OI-41)',
    '194 (3)': 'E2 + 0.22 s withdrawn; population hold table: release_hold_v2p4b; per-record classes',
    '194 (4)': 'margin CONDITIONAL; CF-3 start-lift point; heat location; lit history: cold_flow_start_lift_v2p4b, start_level_lit_thrust_v2p4b',
    '194 (5)': 'wording of 186 (3) and 186 (5)',
    '194 (6)': 'outlet dip for GNC: tank_outlet_dip_v2p4b',
    '194 (7)': 'stand dynamic channel >= 100 bar abs with proof rating: pc_dynamic_channel.stand_proof_rating_v2p4b',
    '194 (8)': 'T1-T4 v3, CF-4 v2.1, budgets: specs_v2p4b, test_budgets_v2p4b',
    '194 (9)': 'stale text replaced (*_superseded keys); H19 for IN718: nozzle_lip_melt_in718_v2p4b',
    '203 (3)': 'purge flow basis and the 2.55 s cap: purge_basis_v2p4b (OI-42)',
    '203 (7)': 'THE start-level lift: start_level_lift_v2p4b (OI-43)',
    '204 (2)': 'unpurged alternative NOT ADOPTED; classes published as data (release_hold_v2p4b)',
    '204 (4) F11': 'A1 duration: a1_duration_note_v2p4b',
    '205': 'Pc port passage gas sound speed: pc_port_gas_v2p4b (OI-45); flight Pc reselection in igniter arm_preconditions and pc_dynamic_channel',
    '213 (founder)': 'A1 apogee target about 210 m: a1_apogee_target_v2p4b; line213_note in the A1-profile blocks; CF-4 v2.1 §4 note',
    '208 (1), (3) (cross-reference)': 'dip onset fixed at 80 g and the ~80 g purge arm: a1_apogee_target_v2p4b.line208_cross_references; '
                                      'NOT ADOPTED strengthened: no change',
    'relay items 1-7 of 203-204': 'purge_basis_v2p4b, start_level_lift_v2p4b, E2_rule_v2p4b, firmware_constant_sources_v2p4b, fa1_spectra_v2p4b, '
                                  'release_hold_v2p4b.per_record_classes, a1_duration_note_v2p4b'}, 'index; nothing here is physical approval')
d['open_items_v2p4b'] = T([
    dict(id='OI-41', item='FA-1 dense spectrum vs the LEAD 194 (1) values (all-case %.1f > 90 bar abs at T <= 0.1 ms; 0.1-1 ms baseline %.1f, '
                          'all-case %.1f vs 93/102; TC-02 band %.1f/%.1f)' % (v('T_le_0p1ms', 'head|all'), v('T_0p1_to_1ms', 'head|baseline'),
                                                                          v('T_0p1_to_1ms', 'head|all'), tc02['max_in_band_baseline']['value_bar'],
                                                                          tc02['max_in_band_all']['value_bar']),
         action='lead: state which case group governs each domain; Mechanical re-checks TC-02 and the flight Pc proof follows', owner='Lead, Mechanical'),
    dict(id='OI-42', item='2.55 s both-open cap gives %.2f g on the Combustion bound (76 g limit); strict cap %.3f s; Cd ASSUMED (+-0.7 g per 1 %%)'
                          % (m255['combustion_bound_open_g'], I1['cap_for_76g']['both_open_s_with_0p05_offset']),
         action='lead: accept 76.05 g as 76 g or set the cap to 2.54 s; CF-4/B-BLEED-1 measure the flow', owner='Lead, Electronics, founders'),
    dict(id='OI-43', item='THE start-level lift h_s replaces the ECU hold lift 0.2154 mm (0.21776 mm at the A1 state)',
         action='Electronics v2.11 implements; CF-3 measures at the commanded lift with the encoder recorded; gen_tables re-run on v2.4b',
         owner='Electronics, founders'),
    dict(id='OI-44', item='ECU E2 (relative rule) earlier than the model E2 by <= %.1f ms' % (1e3 * I3['shift_bound_s']),
         action='GNC P4c uses the bound holds if it flies the comparator; Electronics confirms the latency', owner='GNC, Electronics'),
    dict(id='OI-45', item='Pc port passage gas: c >= %.0f m/s if free of liquid N2O (pseudo-critical N2O at the peak); composition MISSING; '
                          'two-phase N2O unbounded' % c_min,
         action='Mechanical sizes the CC-2 passage at c_min; B-PC-1/IGN-1 record the port ring-down', owner='Mechanical, Electronics, founders'),
    dict(id='OI-46', item='firmware constant source texts (2500 N/s, 0.5 s, 5 bar abs, 0.12 s); propane minimum temperature about 2 C implied',
         action='Electronics confirms the mapping; founders state the propane conditioning', owner='Electronics, founders'),
    dict(id='OI-47', item='IN718 datasheet (SMC-045) read through the web-fetch reader; PDF not archived (proxy refused the download)',
         action='archive the datasheet PDF with its hash', owner='Mechanical, founders'),
    dict(id='OI-48', item='NZ-01 frozen prediction per firing (nz01_criterion_v2p4b)', action='Combustion issues the prediction file before each '
         'T-series firing; founders measure the bore', owner='Combustion, founders'),
    dict(id='OI-49', item='A1 apogee target about 210 m (213): no 210 m A1 record yet; the A1 values are 300 m / 285 m comparators; the '
                          'warm-end relight state rises (purge +%.2f g per K above 289.5 K; 76 g on the 2.5 s schedule up to %s K)'
                          % (A1J['purge_scaling']['M_2p5s_slope_g_per_K'], A1J['purge_scaling']['T_at_76g_2p5s_K']),
         action='GNC publishes the 210 m record (gnc.json v3.2); Combustion re-runs the A1 grain run, Table 7.3b, the purge records at '
                'the warm-end state and FA-1 at the relight state; Mechanical the relight wall temperatures; no new sizing case (LEAD)',
         owner='GNC, Combustion, Mechanical'),
    dict(id='updates', items={'OI-6': 'RE-OPENED by LEAD 205 (flight Pc reselected)', 'OI-17': 'load per LEAD 194 (1)-(2); OI-41',
                              'OI-42 (213)': 'warmer 210 m relight states raise the purge mass (+0.66 g per K above 289.5 K; OI-49)', 'OI-22': 'lip is IN718; H19 recomputed', 'OI-31': 'CLOSED by LEAD 186 (1)/204 (1)-(2); ECU guard in v2.11',
                              'OI-32': 'dip onset values for GNC (194 (6)); geometry MISSING', 'OI-34': 'proof rating stated (194 (7))',
                              'OI-37': 'decided by 186 (4); mechanical.json v2.2 not yet in the hub', 'OI-38': 'ADOPTED, margin CONDITIONAL; CF-3',
                              'OI-40': 'DECIDED (186 (3), 194 (5)); procedure nz01_criterion_v2p4b'})],
    'open items (REPORT v2.4b §12)')
d['unknowns_and_open_items'] = list(d['unknowns_and_open_items']) + [
    'v2.4b: gas composition in the Pc port passage at the FA-1 instant (MISSING; c bracket %.0f-%.0f m/s if free of liquid); Cd x A x G at the '
    'start lift (CF-3); injector-body soak-back temperature at the relight; bleed Cd (purge mass +-0.7 g per 1 %%); which FA-1 case group '
    'governs (OI-41); the stand tank capacity (T1 at 2t = 8 s); outlet geometry (OI-32)' % (c_min, c_hot[1])]
d['unknowns_and_open_items'].append('v2.4b (line 213): the 210 m A1 record (engine-on time, T_tank at MECO and relight, coast '
                                    'duration, ARM-hot case) is MISSING; the A1 values are 300 m / 285 m comparators (OI-49)')
d['superseded_v2p4b'] = T({
    'PURGE commit <= plain trigger - 1.7 s, PROVISIONAL (175 (3), 181 (2))': 'L* = 1.3 s, no unpurged relight below it (186 (1))',
    'E2 + 0.22 s release hold (186 (1))': 'WITHDRAWN (194 (3)); population table release_hold_v2p4b',
    'R2 command hold PROPOSAL (OI-38)': 'ADOPTED (186 (2)); margin CONDITIONAL (194 (4))',
    'NZ-01 criterion PROPOSAL (OI-40)': 'decided (186 (3)) with the 194 (5) wording; nz01_criterion_v2p4b',
    'FA-1 load 90 bar for every part, 92 bar design (173)': 'period domain 90 / 93-102 / spectrum or FA1S (194 (1))',
    'ABORT at t_E2 + 0.8 s': 't_E2 + 0.5 s (181 (4))',
    'the 0.81 s plan holds (unscoped)': 'on the predictor path (181 (2))',
    '316L lip melt 1.07-5.70 s (lumped)': 'IN718 1.10-5.88 s (lumped, 342 C start)',
    'Pc transducer 0-70 bar class (070BG)': 'flight unit reselected (205); stand channel >= 100 bar abs with proof rating',
    'ignition lift 0.2039 mm (single value); ECU hold lift 0.2154 mm': 'THE start-level lift h_s(T): 0.2039 mm at 20 C, 0.21776 mm at A1',
    'CF-4 P1 0.293 s': 'P1 in volume form (18.86 cm3 of lift flow)',
    'T1-T4 v2, CF-4 v2.0': 'T1-T4 v3, CF-4 v2.1',
    '"about x9 margin" (186 (5))': '766 g is 9.3-9.7x the 78.6-82.5 g (194 (5))',
    'chamber heat pick-up TO-VERIFY': 'injector-body and feed soak-back temperature at the relight (194 (4))',
    '62.5 N x pcf_k lit model for R2': 'grain_q1d start-level lit history (194 (4), 204 (4))',
    'A1 apogee target 285 m trim / 300 m lead default as the A1 basis': 'about 210 m (213, founder); 300 m and 285 m values kept as '
                                                                         'comparators (a1_apogee_target_v2p4b)'}, 'REPORT v2.4b §13')

# ------------------------------------------------------------------ checks: every v2.4a key kept
def keys(o, p=''):
    if isinstance(o, dict):
        for k, x in o.items():
            yield p + '/' + k
            yield from keys(x, p + '/' + k)
k0 = set(keys(d0)); k1 = set(keys(d))
assert k0 <= k1, sorted(k0 - k1)[:10]
json.dump(d, open(out, 'w'), indent=1, ensure_ascii=False, default=float)
print('v2.4a keys', len(k0), 'v2.4b keys', len(k1), 'added', len(k1 - k0), 'superseded entries', len(N_SUP))
print('wrote', out, sha(out))
