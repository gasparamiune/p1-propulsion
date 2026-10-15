"""combustion.json v2.4 from the published v2.3 by keyed edits (Combustion v2.4, 2026-10-13).
Every v2.3 key is kept (values updated where v2.4 changes them); v2.4 content is added under new keys. Numbers are read from the
v2.4 data files, whose hashes are asserted. usage: python -I write_interface_v2p4.py V23_JSON DATA_V2P4_DIR OUT_JSON
"""
import copy, hashlib, json, os, sys
V23 = 'd9ec54fbf450e243'
EXP = {'rg01_line_states_v2p4.json': '2939549811d4c381', 'fd01_element_deficit_v2p4.json': '035189ab53929eb2',
       'cf4_void_budget_v2p4.json': '6c294cf2dec7af5d', 'purge_hazard_v2p4.json': 'ba24882f3ca956ba',
       'safing_relief_v2p4.json': '33a95a70e8008e2e', 'stored_energy_sup_v2p4.json': '1b846c99f3145985',
       'nozzle_joint_v2p4.json': 'b5f396c7155c06c4', 'nozzle_lip_melt_v2p4.json': '118b7901855d74a4',
       'drogue_hold_check_v2p4.json': '70820e0038be39a7', 'late_light_tables_v2p4.json': '7baa4f6fa76bfdd3',
       'late_light_spike_v2p4.json': '57fce738164fd571', 'safing_vent_v2p4.json': 'ccc94365e1c8e737',
       'purge_vented_mass_v2p4.json': '0038561f71a51502'}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
src, dd, out = sys.argv[1:4]
assert sha(src) == V23, 'combustion.json is not v2.3'
for f, h in EXP.items():
    assert sha(os.path.join(dd, f)) == h, f
J = lambda f: json.load(open(os.path.join(dd, f)))
d = json.load(open(src)); d0 = copy.deepcopy(d)
fd = J('fd01_element_deficit_v2p4.json')['readings']['Mechanical_CdA_1.57mm2']
se, sr = J('stored_energy_sup_v2p4.json')['rows'], J('safing_relief_v2p4.json')['D_stored_energy']['v']
ph = J('purge_hazard_v2p4.json')['leak']
dh = J('drogue_hold_check_v2p4.json')
T = lambda v, tag, **k: dict(v=v, tag=tag, **k)
R = 'REPORT v2.4'

# ---- header (keys kept) ----
d['revision_history'] = list(d['revision_history']) + [d['revision_note']]
d.update(version='v2.4', date='2026-10-13',
         revision_note=('v2.4 (2026-10-13): answer to REVIEW-COMBUSTION (RC-01..RC-20), REV-GNC-1 and the Electronics SIL items, with the lead decisions to '
                        'CHANGELOG line 164 and Mechanical line 162. igniter.sequence rewritten for firmware v2.8 (A5 deleted, PURGE at E0 - 2.90 s, FA-1 '
                        '(a)/(b)); new keys relight_purge, light_windows, abort_matrix_v2p4, late_light_and_meop, meop_basis_v2p4, fmea_input, cf4_gate, '
                        'stored_energy, nozzle_joint, drogue_release_hold, superseded_v2p4. All v2.3 keys kept.'),
         status=('v2.4 REVISION (digital only, Por revisar). Design point unchanged. No number is MEASURED. The relight claim is gated by CF-4; '
                 'FA-1 is accepted for design continuation only.'),
         supersedes='combustion.json v2.3 (d9ec54fbf450e243), kept as 02-combustion/data/v2/combustion_interface_v2p3_as_published.json')

# ---- igniter.sequence (keys kept, values updated) ----
s = d['igniter']['sequence']
s['tag'] = 'LEAD (CHANGELOG 153-164) + DERIVED (REPORT v2.4 §7.3-7.7, §2.8); firmware v2.8 (Electronics). Verify at IGN-1, CF-4, T1-T4'
v = s['v']
v['arm_preconditions'] = [
    'tank 15-25 C (ENG-12); T_tank <= 24 C at ARM and at ignition (liquid-line interlock, §2.8); tank heater hard-disabled at ARM',
    'pintle seated, encoder healthy; MV-P closed; bleed valves V1 and V2 closed, drivers inhibited',
    'P_torch auto-zero; ARM refused if P_torch > 1.05 bar abs',
    'Pc and P_torch transducers 0-70 bar class (ENG-09 >= 70 bar); P_feed, P_tank healthy; Pc reads ambient',
    'igniter continuity (spark coil, SOL1, SOL2); photodiode healthy (needed for the 2oo2 E1)',
    'relight only: chamber vented; RELIGHT refused if a case thermocouple reads > 433.15 K']
v['start'] = [
    {'epoch': 'PURGE (A1 relight only)', 't_s': -2.90, 't_rel_E0_s': -2.90, 'action': 'MV latch and opener ramp (0.35 s) with the pintle seated; V1 and V2 open; both taps flow 2.5 s; close command leads by the measured valve closing time so the flow stops by E0 - 0.05 s; closure confirmed before E1 or BLEED_FAULT to the FC (relight proceeds). ECU cap = 2.5 s of flow + measured valve times. The relight is never committed before a complete purge: if T_fire would cut the flow below 1.9 s, the FC delays T_fire'},
    {'epoch': 'E0', 't_s': 0.0, 't_rel_E0_s': 0.0, 'action': 'START or RELIGHT at T_fire: MV opens with the pintle seated (already open after PURGE); SOL1 (N2O) and SOL2 (propane) open; spark 50 Hz, 50 mJ from E0 + 0.02 s'},
    {'epoch': 'torch gate', 't_s': 0.16, 't_rel_E0_s': 0.16, 't_s_meaning': 'latest E1', 'action': 'no E1 by E0 + 0.16 s -> TORCH_FAULT (A1); no main N2O admitted'},
    {'epoch': 'E1', 't_s': 0.09, 't_s_meaning': 'median E0 -> E1 (torch_gate_v2p4)', 'action': 'torch flame confirmed on P_torch AND photodiode (2oo2, FA-1 (a)), 10 ms persistence; pintle commanded to the ignition lift 0.2039 mm (t_lift 29.6 ms; CF-3 lift table keeps <= 37.1 g/s at 20 C, <= 37.4 g/s at the A1 state). From E1 to E2 the torch is supervised on both sensors: loss on BOTH for >= 5 ms closes the pintle and the MV (FA-1 (b), A16)'},
    {'epoch': 'W', 't_s': 0.81, 't_s_meaning': 'relight plan limit for E2: torch gate 0.16 s + W 0.65 s', 'action': 'abort deadline W from the lift command: 0.40 s flight first start, 0.65 s flight relight, 0.35 s stand (A2)'},
    {'epoch': 'E2', 't_s': 0.442, 't_s_meaning': 'median E0 -> E2 on the worst purged relight state (p99 0.589, max 0.626)', 'action': 'light: Pc >= 0.8 bar above the pre-lift baseline on filtered AND raw Pc for 10 ms, above 1.8 bar abs; SOL1 off first, SOL2 within 20 ms (torch ends propane-only), spark off, ramp released. LIGHT_SPIKE event logged (replaces A5)'},
    {'epoch': 'E3', 't_s': None, 't_s_meaning': 'set by the ramp; ENG-04 latency in REPORT v2.4 §7.7', 'action': 'thrust >= 90 % of the command (ENG-04 latency, §7.7)'}]
v['abort_if_no_ignition'] = [
    'pintle closed; torch solenoids closed (SOL1 not after SOL2); MV closed (abort is MV-first)',
    'no retry into a pooled chamber; ground: wait >= 5 s, N2 purge, safing (§10.2)',
    'flight: no retry; vehicle-level response per GNC',
    'A5 (Pc > 8 bar for 5 ms) is DELETED (LEAD line 160): it tripped on 98 % of the late-light grid; LIGHT_SPIKE records the event instead']
v['shutdown'] = ['pre-MECO throttle-down to <= 75 % (ENG-05)', 'pintle closes at full drive speed',
                 'MV de-energised on seat confirmation (encoder at seat and Pc < 2 bar abs) or 0.30 s after the command',
                 'trapped liquid relieves to the tank through S1 (§2.7); ground: 30 s hold then safing']
v['relight'] = ['MV closed during coasts (LEAD); the v2.3 text "the isolation valve may stay open between burns" is withdrawn',
                'A1 relight: PURGE at E0 - 2.90 s (2.5 s of flow, theta <= 2 deg, balanced or axial vent), then the start sequence from E0',
                'settling: liquid at the tank outlet from E0 - 2.90 s - t_settle (§2.4 note); RELIGHT refused if a case thermocouple > 433.15 K',
                'light window W 0.65 s; E0 -> E2 max 0.626 s on the worst purged line state (rg01_line_states_v2p4); 0.81 s plan holds']
v['flashback_and_backflow'] = list(v['flashback_and_backflow']) + ['v2.4: R-T1 no N2O-only flow through a hot torch; R-T2 dead-ended N2O <= 0.05 cm3, SOL1 on a thermal stand-off (§7.5); A8 torch-line over-temperature']
v['purge'] = ['ground tests: N2 purge of the chamber after shutdown and before a re-start attempt (unchanged)',
              'flight A1 relight: forced bleed purge of the valve-to-seat segment (PURGE, see start[0] and relight_purge); no purge gas carried']
v['fa1_supervision'] = T({'a_E1_2oo2': 'E1 only on P_torch AND photodiode', 'b_E1_to_E2': 'loss on BOTH sensors for >= 5 ms closes pintle and MV (A16); unlit N2O bounded to 0.9-4.0 g',
                          'status': 'REQUIRED of Electronics; FA-1 accepted for design continuation only; flight acceptance needs IGN-1 (>= 30 lights incl. photodiode false-positive tests) and the Mechanical 75.5 bar <= 3 ms pulse check'},
                         'LEAD line 164')
v['light_windows_W_s'] = T({'flight_first_start': 0.40, 'flight_relight': 0.65, 'stand': 0.35, 'measured_from': 'lift command'}, 'LEAD; REPORT v2.4 §7.3')

# ---- RC-20: tags on the untagged nested objects (keys added, none renamed) ----
n2o = d['thermal_and_loads']['head_end_bc']['v']['n2o_side']['v']
for k in ('props_100pct', 'props_12p5pct'):
    n2o[k]['tag'] = 'DERIVED (rho, cp CoolProp HEOS liquid N2O; mu, k ASSUMED: CoolProp 8 has no N2O transport model)'

# ---- new v2.4 keys ----
d['light_windows'] = v['light_windows_W_s']
d['relight_purge'] = T({
    'design_basis': 'minimal set (3): coil re-route + pre-scheduled 2-tap purge on the decided path, theta <= 2 deg, balanced or axial vent, no lining (LEAD line 164)',
    'restrictors': {'n': 2, 'd_mm': 0.707, 'drill_mm': 0.71, 'Cd': 0.70, 'Cd_tag': 'ASSUMED (CF-4 measures; each restrictor flow-tested)'},
    'valves': '2 NC in series, each >= 4x the restrictor capacity; drivers hardware-inhibited outside the purge window; mass 2 x 0.30 kg is a MASS RISK (target <= 0.15 kg each)',
    'filter_F2': {'element': 'inline <= 15 um on the FD-01 leg, tap to tee', 'CdA_min_mm2': 1.57, 'FD01_leg_deficit_max': round(1 - fd['worst_ratio'], 4),
                  'needed_flow_time_bound_s': round(fd['needed_Tp_bound_s'], 3), 'margin_at_2p5_s': round(fd['margin_at_2p5_bound_s'], 3),
                  'CdA_for_0p3s_margin_mm2': 0.63, 'two_flow_grid': 'not run (margin >= 0.3 s); run if measured Cd.A < 0.63 mm2', 'tag': 'DERIVED fd01_element_deficit_v2p4.json'},
    'timing_s': {'PURGE_command_rel_E0': -2.90, 'MV_ramp': 0.35, 'flow': 2.5, 'flow_end_rel_E0': -0.05, 'needed_flow_unlined': 1.9, 'min_flow_before_T_fire_delay': 1.9},
    'flows_g_s': {'liquid_per_tap': 15.62, 'vapour_per_tap': 4.25, 'total_liquid': 31.24, 'fraction_of_100pct': 0.118},
    'N2O_vented_g': {'at_2p5s': [34.3, 72.9], 'at_needed_time': [19.5, 54.7], 'plan_max': 76},
    'pocket_at_lift_cm3_at_2p5s': [4.77, 8.15], 'P_abort_W0p65': 0.0, 'samples': 200000,
    'E0_to_E2_s_worst_purged': {'median': 0.442, 'p99': 0.589, 'max': 0.626},
    'truncated_purge_P_abort_unlined': {'1.0': 1.0, '1.5': 0.52, '1.6': 0.37, '1.7': 0.24, '1.8': 0.098, '1.9': 0.0},
    'stuck_open': {'g_s': 31.24, 'governing': 'additive tank outflow (GNC S313)', 'open_loop_injector_loss_100pct': 0.0154, 'at_ignition_lift_max': 0.0009},
    'exposure_MV_open_pintle_seated_s': [2.99, 3.06], 'seat_leak_added_mg': {'acceptance': [2.9, 4.2], 'fault': [40.4, 250.9]},
    'jets_N': {'per_tap': [1.6, 2.5], 'both_one_way': [3.3, 5.0]}, 'closure_surge_bar': 2.9,
    'vented_mass_vs_flow_time_g': {'t_flow_s__min_p50_p99_max': [[r['t_flow_s'], r['min_g'], r['p50_g'], r['p99_g'], r['max_g']] for r in J('purge_vented_mass_v2p4.json')['rows']],
                                   'flow_start_rel_E0_s': -2.55, 'closure_add_max_g_per_s_of_t_close': 31.24, 'file': 'purge_vented_mass_v2p4.json'},
    'line_states_file': 'rg01_line_states_v2p4.json (2939549811d4c381)', 'gate': 'CF-4 (02-combustion/CF-4-SPEC.md)'},
    'SIM/DERIVED on ASSUMED Cd and slip brackets; LEAD lines 160, 161, 164; Mechanical line 162')
d['abort_matrix_v2p4'] = T({'A2': 'no E2 within W of the lift command (0.40 / 0.65 / 0.35 s)', 'A4': 'Pc > 30 bar raw for 5 ms', 'A5': 'DELETED -> LIGHT_SPIKE log',
                            'A7': 'Pc loss or implausibility, bands and the flight START high-side rule (Electronics sets values)',
                            'A14': 'bleed valve fault or closure not confirmed by E0 - 0.05 s -> BLEED_FAULT to the FC (FC action LOG-ONLY, line 168); fail-closed -> no purge -> no relight on that pass; closure from P_mid is a pad go/no-go (line 168)',
                            'A15': 'pintle or chamber anomaly during PURGE: inhibit torch, close MV', 'A16': 'torch loss on BOTH sensors >= 5 ms between E1 and E2: close pintle and MV'},
                           'LEAD lines 160, 164; REPORT v2.4 §7.4')
d['late_light_and_meop'] = T({
    'decomposition_peak_bar': {'pad_15C': {'sharp': 43.7, 'rounded': 40.6}, 'pad_20C': {'sharp': 43.1, 'rounded': 40.1}, 'pad_25C': {'sharp': 42.0, 'rounded': 39.3},
                               'A1_relight': {'sharp': 37.8, 'rounded': 36.7}},
    'MEOP_45bar': 'holds for decomposition-only late light; rounded entrance REQUIRED',
    'fuel_assisted_relight_bar': {'burn_1ms': [48.9, 75.5], 'burn_5ms_max': 55.5, 'burn_10ms_max': 41.4},
    'fuel_assisted_status': 'MEOP NOT shown -> FMEA FA-1 (single-control hazard)', 'superseded': '44.9 bar (v2.4 draft); 72.8 / 62.9 bar (run 1)'},
    'SIM late_light_tables_v2p4.json, late_light_spike_v2p4.json on ASSUMED burn time and fuel fraction')
d['meop_basis_v2p4'] = T({'basis_bar': 44.33, 'margin_to_MEOP_bar': 0.67, 'proof_margin_min_bar': 21.9, 'supersedes': 'v2.3 basis 42.85 bar (RC-08)'}, 'SIM meop_basis_v2p4.json')
d['fmea_input'] = T({
    'FA-1': {'hazard': 'fuel-assisted fast part at an A1 relight, 48.9-75.5 bar at 1 ms', 'single_control': 'torch-first gate',
             'failure_modes': ['FM1 false torch confirmation', 'FM2 lift before E1', 'FM3 torch blow-out between E1 and E2', 'FM4 torch does not ignite the main flow'],
             'required': ['(a) 2oo2 E1', '(b) supervision, loss on both sensors >= 5 ms closes pintle and MV'], 'residual': '(b) bounds unlit N2O to 0.9-4.0 g; the pulse itself cannot be stopped',
             'severity': 'catastrophic if case or closures fail; critical otherwise', 'occurrence': 'unknown',
             'owners': {'Electronics': '(a), (b), sequence checks', 'Combustion': 'bound refinement with IGN-1/T4', 'Mechanical': '75.5 bar <= 3 ms pulse check', 'lead': 'acceptance'}},
    'bleed': ['B-1 one valve stuck open', 'B-2 both stuck open or common cause (31.24 g/s)', 'B-3 one valve fails closed (series pair doubles it): no purge, no relight on that pass',
              'B-4 restrictor or FD-01 element partly blocked (no flight detection)', 'B-5 purge truncated by T_fire (FC delays T_fire below 1.9 s)']},
    'DERIVED; LEAD lines 160, 164; REPORT v2.4 §9.1')
d['cf4_gate'] = T({'document': '02-combustion/CF-4-SPEC.md', 'claim': 'A1 relight lights within W 0.65 s with P_abort <= 1e-3, venting <= 76 g, theta <= 2 deg',
                   'pass_criteria': ['P1 liquid at the pintle inlet <= 0.293 s after reaching the lift', 'P2 >= 0.35 s continuous liquid or inside the void budget',
                                     'P3 cap clears FD-01 crown <= 2.3 s after flow start', 'P4 each tap >= 80 % of model flow', 'P5 <= 76 g vented (IS-1, IS-2)',
                                     'P6 closure by E0 - 0.05 s and BLEED_FAULT on a held-open valve', 'P7 no unfiltered path to the seat'],
                   'void_budget_file': 'cf4_void_budget_v2p4.json (6c294cf2dec7af5d)'}, 'LEAD line 164 (accepted as the gate); physical execution by the founders')
d['stored_energy'] = T({k: {'decomposition_TNT_kg': round(r['decomposition_TNT_kg'], 4), 'R_6p9kPa_m': round(r['R_6p9kPa_m_decomposition'], 1)}
                        for k, r in list(sr.items()) + [(k2, se[k2]) for k2 in ('stand_allowable_13p84g', 'flight_inventory_accepted_26p6g')] if 'decomposition_TNT_kg' in r},
                       'DERIVED safing_relief_v2p4.json, stored_energy_sup_v2p4.json; scaled distance 17.9 m/kg^(1/3) LITERATURE as recalled, TO-VERIFY')
d['nozzle_joint'] = T({'NZ03_gasket': 'mica/vermiculite 900 C rating vs 1595 C FE: fails by 695 K', 'proposal_J1': '2.0 mm carbon-phenolic flange + 0.5 mm flexible-graphite seal at the lip face',
                       'unsealed_leak_fraction': [0.0083, 0.0110], 'lip_melt_s': {'J1_lumped_1mm': [1.07, 5.70], 'J1_FD_1mm': [6.63, 40.26], 'J1b_lumped_1mm': [1.19, 6.34], 'J1b_FD_1mm': [7.39, 44.33]},
                       'H19_control': 'N2 pressure-decay leak check at 67.5 bar before and after every firing (criterion TO-DEFINE)'},
                      'DERIVED nozzle_joint_v2p4.json, nozzle_lip_melt_v2p4.json; FEA Mechanical; materials as recalled TO-VERIFY')
d['drogue_release_hold'] = T({'lead_predicate_line168': 'RELEASE iff RUN AND b4 AND [(Pc valid AND >= 300 kPa abs) OR b7 OR (d2-d3 = 0xFFFF AND t >= t_E2 + 0.10 s)], latched; t_E2 from EVENT 0x120; b7 only on a valid filtered channel', 'check_rule': dh['rule'], 'corners': 288, 'hold_ok': 288, 'min_margins_bar': [0.74, 0.48], 'unlit_rise_max_bar': round(dh['unlit_rise_max_bar'], 3)},
                             'SIM/DERIVED drogue_hold_check_v2p4.json')
d['superseded_v2p4'] = T({'44.9 bar late light': 'Tables 7.4/7.5', 'about 50 g per purge': '34.3-72.9 g at 2.5 s', '0.8 mm per tap': '2 x 0.707 mm',
                          'PURGE at E0 - 2.40 s': 'E0 - 2.90 s', 'A5': 'LIGHT_SPIKE', 'ECU cap 2.5 + 0.3 s': '2.5 s + measured valve times', 'PTFE lining': 'dropped',
                          'coast leak ceiling 0.039 g/s': '0.0055 g/s', 'MEOP basis 42.85 bar': '44.33 bar', 'throat life 1.0-4.3 A1 flights': 'one insert per flight',
                          '15.91 cm3 (Mechanical)': '10 deg robustness row; 4.84 cm3 at theta <= 2 deg'}, 'REPORT v2.4 §13')
d['unknowns_and_open_items'] = list(d['unknowns_and_open_items']) + [
    'v2.4: CF-4 (slip, restrictor Cd, element dP-flow), IGN-1 (torch reliability, photodiode false positives, FA-1), seat face <= 800 K MECO->E1 (Mechanical), nozzle joint FE re-run, GNC RG-01 re-fly incl. the T_fire delay height cost (REPORT v2.4 §11-12)']
d['files'] = dict(d['files']); d['files']['v2p4'] = T({'report': '02-combustion/REPORT v2.4 (draft REPORT_v2p4.txt)', 'cf4': '02-combustion/CF-4-SPEC.md',
                                                        'data_index': '02-combustion/data/v2/v2p4/FILE-INDEX.txt', 'writer': '02-combustion/src/write_interface_v2p4.py'}, 'index')

def keys(o, p=''):
    r = set()
    if isinstance(o, dict):
        for k, x in o.items():
            r.add(p + '/' + k); r |= keys(x, p + '/' + k)
    return r
lost = keys(d0) - keys(d)
assert not lost, sorted(lost)[:10]
json.dump(d, open(out, 'w'), indent=1, ensure_ascii=False)
print('ok', out, sha(out), 'v2.3 keys kept:', len(keys(d0)), 'v2.4 keys:', len(keys(d)))
