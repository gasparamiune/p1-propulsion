"""combustion.json v2.4a from the published v2.4 by keyed edits (Combustion v2.4a, 2026-10-13).

Answers REV-COMB-2 (reviews/REVIEW-COMBUSTION-R2.md e6bf189fb271e652) R2-01, 02, 04-10 with the lead decisions to CHANGELOG line 177,
and the coordinator's two checks after GNC rev2 (line 175 (3)), and the line-181 requests (2), (4), (10) (REV-GNC-3 decisions).  Every v2.4 key is kept: stale values are replaced in place with a
SUPERSEDED note, or tagged SUPERSEDED with their replacement; v2.4a content is added under new keys.  Numbers are read from the v2.4a
data files, whose hashes are asserted.
usage: python -I write_interface_v2p4a.py V24_JSON DATA_V2P4A_DIR OUT_JSON
"""
import copy, hashlib, json, os, sys
V24 = '469727032124329f'
EXP = {'fa1_envelope_v2p4a.json': '64b328150025fa1e', 'fa1_tables_v2p4a.json': '677fd9ccd297fdf4',
       'fa1_outflow_sens_v2p4a.json': '540a78f8b9634f76', 'vented_mass_brackets_v2p4a.json': '8e8ca9329c74a01f',
       't1t4_law_resolution_v2p4a.json': '05b5ae5c20e04bd8', 'unpurged_start_check_v2p4a.json': '4c745dcfbf09aef7',
       'unpurged_outcomes_v2p4a.json': '18a639d61b58ce8a', 'cold_flow_thrust_v2p4a.json': 'a226dfacf494cb2c',
       'cold_flow_thrust_v2p4a.csv': 'e094c4be80d12f66'}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
src, dd, out = sys.argv[1:4]
assert sha(src) == V24, 'combustion.json is not v2.4'
for f, h in EXP.items():
    assert sha(os.path.join(dd, f)) == h, f
J = lambda f: json.load(open(os.path.join(dd, f)))
d = json.load(open(src)); d0 = copy.deepcopy(d)
T = lambda v, tag, **k: dict(v=v, tag=tag, **k)
R = 'REPORT v2.4a'
SUP = lambda why: 'SUPERSEDED (v2.4a): ' + why

# ------------------------------------------------------------------ numbers from the data files (asserted against the text)
tb = J('fa1_tables_v2p4a.json')['tables']
t1 = tb['by_reading_entrance_OF4_12']
UP = J('unpurged_start_check_v2p4a.json')
pa = UP['partA_post_light_gap']; lo = pa['states']['purge_not_run_unlined_LO_0-2deg_worst']['restart']
assert abs(lo['P_light_within_W'] - 0.75757) < 1e-4 and lo['gap_volume_cm3'] == [23.4431]
lor = lo['ramp_to_200N']; lol = lo['lift_flow_held']
assert abs(lor['P_released_then_A3'] - 0.7116) < 1e-3
lin = pa['states']['purge_not_run_lined_LO_0-2deg_worst']['restart']
pop = pa['population_0_2deg']
pb = UP['partB_A3_ratio_in_gap']; assert pb['A3_ratio_max'] < 0.24
pc = UP['partC_liquid_readmission']; pd = UP['partD_tank_outlet']
TT = J('t1t4_law_resolution_v2p4a.json'); S = TT['partB_summary']['all']
assert abs(S['T1_100']['rho_max'] - 1.0677) < 1e-4 and abs(S['T3_20']['rho_max'] - 1.004) < 1e-4
VB = J('vented_mass_brackets_v2p4a.json')

# ------------------------------------------------------------------ header (keys kept)
d['revision_history'] = list(d['revision_history']) + [d['revision_note']]
d.update(version='v2.4a', date='2026-10-13',
         revision_note=('v2.4a (2026-10-13): targeted patch for REV-COMB-2 (e6bf189fb271e652) R2-01..R2-10 with the lead decisions to CHANGELOG '
                        'line 177. A4 on the filtered channel (166 (4)); E1 closure term (166 (3)); one stand safing rule (172 (1)); stale values '
                        'superseded in place; relief_v2p4a; FA-1 envelope and the line-173 load; guard band; stand dynamic Pc channel; T1-T4 v2 '
                        '(reversed burden); PURGE commit rule of line 175 (3) with Combustion\'s unpurged-start finding; tank-outlet coverage '
                        'screening; answers to LEAD line 181 (2) (unpurged start: LO or HI, outcome classes, L*), (4) (cold-flow apparent thrust under the '
                        'drogue after a flame-out) and (10) (coverage on liquid depletion). All v2.4 keys kept.'),
         status=('v2.4a REVISION (digital only, Por revisar). Design point unchanged. No number is MEASURED. The relight claim is gated by CF-4; '
                 'FA-1 is accepted for design continuation only; the line-175 (3) provisional PURGE commit rule is refuted by Combustion\'s '
                 'unpurged-start check (SIM/DERIVED) and awaits the lead. Line 181 (2): Combustion recommends L* = 1.3 s (worst-state P(success) 0 under '
                 'LO and HI). Line 181 (4): the cold-flow thrust can satisfy the R2 threshold by itself once the open-loop command exceeds '
                 'about 200 N (bound) / 310-350 N (nominal) (cold_flow_thrust_v2p4a).'),
         supersedes='combustion.json v2.4 (469727032124329f), kept as 02-combustion/data/v2/combustion_interface_v2p4_as_published.json')

# ------------------------------------------------------------------ R2-05: stale values, replaced or tagged SUPERSEDED (keys kept)
d['decisions']['tank_pressurisation']['v'] = ('Self-pressurised N2O conditioned 15-24 C at ARM (ENG-12 as amended; was 15-25 C) with the heater '
                                              'hard-disabled at ARM and the T_tank <= 24 C interlock at ARM and ignition (guard band: '
                                              'interlock_guard_band); heater blanket removed at liftoff; N2 supercharge NOT baselined')
d['decisions']['tank_pressurisation']['tag'] += '; ENG-12 amended (REQUIREMENTS amendments, ENG-09/ENG-12 lines)'
pl = d['operating_points']['pressure_limits']
pl['full_stroke_failure_S230_max_bar']['tag'] = SUP('v2.3 SIM full-stroke maximum (30 C, Cd 0.8) is no longer the MEOP basis; '
                                                     'replacement 44.33 bar at the 24 C interlock (meop_basis_v2p4, REPORT §3.6); value kept for compatibility')
row = pl['full_stroke_failure_S230']['v'][11]
assert row['Pc_bar'] == 42.85 and row['T_tank_C'] == 30.0
row['status'] = SUP('30 C is not a credible ignition state (24 C interlock); basis 44.33 bar (meop_basis_v2p4)')
op = d['operating_points']
op['max_thrust_hold_baseline_tank']['t_500N_held_s']['tag'] = ('SIM 15-25 C computed range (ENG-12 as amended: 15-24 C at ARM, so the 25 C end is a '
                                                                'bound), eq/neq E 100/1000 tank (min, max)')
op['tank_pressure_range_Pa']['tag'] = ('CoolProp Psat 15-25 C computed range (ENG-12 as amended: 15-24 C at ARM; the 25 C end is a bound) '
                                       '(n2o_validation_v2.json: CoolProp vs ESDU <= 0.98 % to 300 K)')
va = d['valves_and_actuators']
va['isolation_valve']['trapped_liquid_relief'] = T(
    SUP('v1 "required (<= 7.5 MPa) between the isolation valve and the pintle" is replaced by the back-relief check MV segment -> tank '
        '(Cv >= 0.1) and the secondary rupture disc 9.5 MPa +/- 5 % on FS-01 (LEAD line 172 (6)); see relief_v2p4a'),
    'LEAD line 172 (6); REQUIREMENTS amendments (ENG-09 trapped-liquid relief text superseded)')
va['hose']['v'] = va['hose']['v'].replace('(15-25 C)', '(15-25 C computed; ENG-12 as amended allows 15-24 C at ARM, so 25 C is a bound)')
pr = va['priming_rule']['v']
assert 'valve left open' in pr[1] and '7.5 MPa' in pr[2]
pr[1] = ('relights with the line primed (P_feed >= 0.5 P_tank, trapped liquid; the MV is closed in coasts, igniter.sequence): normal sequence, '
         'with PURGE on A1 relights. ' + SUP('"or valve left open" withdrawn (MV closed in coasts)'))
pr[2] = SUP('trapped-liquid relief <= 7.5 MPa (mechanical.json v1) replaced by the back-relief check to the tank (Cv >= 0.1) and the 9.5 MPa '
            '+/- 5 % disc (LEAD line 172 (6), relief_v2p4a)')
bs = va['pintle_actuator']['seat_and_seal_review_v2p3']['v']['b_seat']
assert '0.039 g/s' in bs['leak_tightness'] and 'relief 7.5 MPa' in bs['load_sources']
bs['leak_tightness'] = bs['leak_tightness'].replace(
    'Combustion ceiling for a coast: 10 % of the 8.74 g hard-start inventory over 22.2 s = 0.039 g/s; until measured close the NC valve during coasts (trapped-liquid relief stays)',
    'Combustion coast leak ceiling 0.0055 g/s (REPORT v2.4 §3.5; ' + SUP('the v2.3 ceiling 0.039 g/s from 8.74 g was understated, RC-02') +
    '); the MV is closed in coasts; relief per relief_v2p4a')
assert '0.0055 g/s' in bs['leak_tightness']
bs['load_sources'] += ('. ' + SUP('the 7.5 MPa relief load row (plus10_relief_7p5MPa_N) is kept as a bound only: the trapped-liquid relief is '
                                   'replaced by the back-relief check to the tank (segment <= tank pressure + the check crack, Cv >= 0.1) and the '
                                   '9.5 MPa +/- 5 % disc (relief_v2p4a); the disc case sits above the 7.5 MPa row and below the 10.5 MPa proof row'))
d['igniter']['model_transients']['tag'] = SUP('v2.3 figures (0.28-0.29 s to 90 %) assumed a 0.10 s torch-to-main delay and a direct step; the adopted '
                                               'sequence is in REPORT v2.4 §7.7 and light_windows / igniter.sequence (E0 -> E2 median 0.442 s, '
                                               'p99 0.589 s, max 0.626 s on the worst purged relight state)')
fpi = d['thermal_and_loads']['flights_per_insert_A1']
fpi['tag'] = SUP('"1.0-4.3 A1 flights" is not supported on the v2 cycles (RC-06); replacement: one insert per flight (REPORT v2.4 §5.4)')
oi = d['open_interface_issues'][5]
assert oi['id'] == 'OI-6' and '0-69 bar' in oi['action']
oi['action'] = SUP('"0-69 bar" option: ENG-09 requires a Pc range >= 70 bar and igniter.sequence uses the 0-70 bar class; the stand also '
                   'carries the dynamic channel pc_dynamic_channel')
oi['status'] = 'CLOSED by ENG-09 (range >= 70 bar)'
d['stability']['hybrid_LF_note'] = d['stability']['hybrid_LF_note'].replace(
    'static fire T2/T3 with 1 kHz Pc logging',
    'static fire T2/T3 with the 1 kHz control channel for the 0.3-2 Hz band and the stand dynamic channel (>= 10-20 kHz, pc_dynamic_channel) '
    'for the 1L / Helmholtz modes at 1.1-1.8 kHz, which 1 kHz logging aliases')

# ------------------------------------------------------------------ igniter.sequence (keys kept; values updated)
s = d['igniter']['sequence']
s['tag'] = ('LEAD (CHANGELOG 153-177) + DERIVED (REPORT v2.4a §7.3-7.7, §2.8); firmware v2.8 (Electronics). Verify at IGN-1, CF-4, T1-T4')
v = s['v']
assert v['arm_preconditions'][0].startswith('tank 15-25 C')
v['arm_preconditions'][0] = ('tank 15-24 C at ARM (ENG-12 as amended); T_tank <= 24 C at ARM and at ignition (liquid-line interlock, §2.8) with '
                             'the thresholds lowered by the channel uncertainty (interlock_guard_band); tank heater hard-disabled at ARM')
st0 = v['start'][0]; assert st0['epoch'].startswith('PURGE')
st0['action'] = ('PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge (LEAD line 175 (3), PROVISIONAL; T_fire delay '
                 '<= 0.6 s; SUPERSEDED: line 164 "the FC delays T_fire", withdrawn). Combustion\'s unpurged-start check refutes the "relight proceeds unpurged" '
                 'branch (purge_commit_rule_v2p4a). When committed: MV latch and opener ramp (0.35 s) with the pintle seated; V1 and V2 open; both '
                 'taps flow 2.5 s; the close command leads by the measured valve closing time so the flow stops by E0 - 0.05 s (scheduled flow '
                 'end, LEAD line 164). Closure (V1 first, on P_mid) is confirmed by the closure deadline <= the torch gate (Electronics: E0 + 0.15 s), '
                 'otherwise BLEED_FAULT (see E1). ECU cap = 2.5 s of flow + measured valve times')
st3 = v['start'][3]; assert st3['epoch'] == 'E1'
st3['action'] = ('E1 = torch flame confirmed on P_torch AND photodiode (2oo2, FA-1 (a)), 10 ms persistence, AND, on an A1 relight with the bleed '
                 'fitted, [bleed closure confirmed OR the closure deadline reached] (deadline <= torch gate E0 + 0.16 s; LEAD line 166 (3)). At the '
                 'deadline without confirmation: flight - BLEED_FAULT to the FC (log-only, line 168), V2 commanded closed, the lift proceeds; stand - '
                 'abort. Then the pintle is commanded to the ignition lift 0.2039 mm (t_lift 29.6 ms; CF-3 lift table keeps <= 37.1 g/s at 20 C, '
                 '<= 37.4 g/s at the A1 state). From E1 to E2 the torch is supervised on both sensors: loss on BOTH for >= 5 ms closes the pintle and '
                 'the MV (FA-1 (b), A16)')
assert 'wait >= 5 s' in v['abort_if_no_ignition'][1]
v['abort_if_no_ignition'][1] = ('no retry into a pooled chamber; stand: N2 purge >= 60 s at >= 10 g/s, then a hold of >= 15 min before approach '
                                'with Pc at ambient and the head thermocouples falling, then safing (LEAD line 172 (1); stand_safing_v2p4a). '
                                + SUP('"wait >= 5 s" withdrawn'))
fs = v['fa1_supervision']
fs['v']['status'] = ('REQUIRED of Electronics; FA-1 accepted for design continuation only; flight acceptance needs IGN-1 (>= 30 lights incl. '
                     'photodiode false-positive tests) with the stand dynamic Pc channel, and the structural load of LEAD lines 172 (2) / 173 '
                     '(90 bar abs QS head and aft; 92 / 102 bar for 0.25-1 ms parts; 1.8 kN x 4 ms), closed by Mechanical in S-AX (line 176) '
                     'with the lead\'s actions of line 177. ' + SUP('"Mechanical 75.5 bar <= 3 ms pulse check" replaced by the line-173 load'))
fs['tag'] = 'LEAD lines 164, 172 (2), 173, 177'

# ------------------------------------------------------------------ abort matrix, FMEA, CF-4 gate
am = d['abort_matrix_v2p4']['v']
am['A4'] = ('Pc > 30 bar abs on the FILTERED channel for 5 ms (LEAD line 166 (4); amends line 160 "raw"); the hardware OVP comparator '
            '(31.47 bar g) stays the fast path for a blocked throat. Decomposition spike filtered peak <= 21.4 bar: no trip')
am['A14'] = ('bleed valve fault, or closure not confirmed by the closure deadline (<= torch gate E0 + 0.16 s; Electronics E0 + 0.15 s) -> '
             'BLEED_FAULT to the FC (FC action LOG-ONLY, line 168); flight: V2 commanded closed and the lift proceeds (E1 term, line 166 (3)); '
             'stand: abort; fail-closed -> no purge -> no relight on that pass; closure from P_mid is a pad go/no-go (line 168). '
             + SUP('"closure not confirmed by E0 - 0.05 s" (E0 - 0.05 s stays the scheduled flow end only)'))
am['A3_unpurged_note_v2p4a'] = ('A3 trips on the post-light vapour gap of an unpurged start (ratio <= %.2f against 0.40 for >= 22 ms), after the '
                                 'drogue-release term is already true: see purge_commit_rule_v2p4a' % pb['A3_ratio_max'])
d['abort_matrix_v2p4']['tag'] = 'LEAD lines 160, 164, 166, 168, 175; REPORT v2.4a §7.4'
fm = d['fmea_input']['v']
fa = fm['FA-1']
fa['hazard'] = ('fuel-assisted fast part at an A1 relight: envelope head %.1f-%.1f bar abs, aft %.1f-%.1f bar abs at tf 1 ms over O/F 4-12 and '
                'both readings (fa1_envelope_v2p4a); never above 90 bar; above 45 bar <= 4.45 ms. ' % (
                    min(r['head_peak_bar'] for r in t1), max(r['head_peak_bar'] for r in t1),
                    min(r['aft_peak_bar'] for r in t1), max(r['aft_peak_bar'] for r in t1))
                + SUP('"48.9-75.5 bar at 1 ms" (v2.4 single reading)'))
fa['residual'] = ('(b) bounds unlit N2O to 0.9-4.0 g; the pulse itself cannot be stopped; fuel inventory at the light TO-VERIFY (IGN-1 / T4 '
                  'with the stand dynamic Pc channel)')
fa['owners']['Mechanical'] = ('structural load per LEAD lines 172 (2) / 173: 90 bar abs QS head and aft every part; 92 / 102 bar for parts with '
                              'periods 0.25-1 ms; 1.8 kN x 4 ms; closed in S-AX/joints (line 176) with the actions of line 177 (TC-09 Inconel 718, '
                              'J-FWD, gimbal bearings). ' + SUP('"75.5 bar <= 3 ms pulse check"'))
assert 'FM2 lift before E1' in fa['failure_modes'][1]
bl = fm['bleed']; assert bl[4].startswith('B-5')
bl[4] = ('B-5 purge truncated or not run at a late commit: ' + SUP('"FC delays T_fire below 1.9 s" (line 164, withdrawn by line 175 (3))')
         + '; PROVISIONAL rule commit <= plain trigger - 1.7 s else no purge; the unpurged branch carries the post-light-gap hazard (B-6)')
fm['bleed'] = list(bl) + ['B-6 unpurged relight (no commit by plain trigger - 1.7 s): every light of the LO worst state is followed by a 23.4 cm3 '
                          'vapour gap after the drogue release -> A3 abort, dead vehicle released (purge_commit_rule_v2p4a)']
cg = d['cf4_gate']['v']['pass_criteria']
assert cg[3].startswith('P4') and cg[5].startswith('P6')
cg[3] = ('P4 per tap and per phase: vapour >= 3.4 g/s per tap (80 % of HEM 4.25), liquid >= 12.5 g/s per tap (80 % of Dyer 15.62), Cd_eff >= 0.56, '
         'dP V1+V2 <= 11 %; judged against the open-element reading; the barrier-element T4 stall is a model construct (bubble point ~0.7 kPa '
         'vs 45.5 bar) and a measured stall is a finding')
cg[5] = ('P6 flow stopped by E0 - 0.05 s (scheduled); closure confirmed (V1 first, P_mid) by the deadline <= torch gate (Electronics E0 + 0.15 s); '
         'one valve held open -> BLEED_FAULT at the deadline; flight build: V2 commanded closed and the lift proceeds; stand build: abort')
d['cf4_gate']['tag'] = 'LEAD line 164 (accepted as the gate), 166 (3); CF-4-SPEC v2.0; physical execution by the founders'
d['cf4_gate']['spec_version'] = 'CF-4-SPEC v2.0 (v2.4a)'
d['relight_purge']['v']['design_basis'] += ('. v2.4a: GNC rev2 records give a specific-force angle to the body axis of up to 2.71 deg raw (2.65 deg '
                                            '0.1 s mean) during the flow (purge_outlet_inputs.json 47b4deb96ea22043): above the 2 deg basis; the '
                                            'model is not computed at 2.7 deg (OPEN); CF-4 v2 adds 3 deg runs')

# ------------------------------------------------------------------ nozzle joint (R2-09)
nj = d['nozzle_joint']['v']
nj['J1_status'] = ('CONFIRMED by the lead (CHANGELOG line 146; J1b dropped unless S-AX fails the lip). The lip 250 C was a goal (line 145); '
                   'J1\'s lip runs at about 342 C (REV-COMB-2 R2-09); Mechanical reports the NZ-04 history to RELIGHT (line 146)')
d['unknowns_and_open_items'][12] = d['unknowns_and_open_items'][12].replace(
    'GNC RG-01 re-fly incl. the T_fire delay height cost',
    'GNC RG-01 re-fly (' + SUP('T_fire delay height cost: the delay rule is withdrawn, line 175 (3)') + ')')

d['drogue_release_hold']['v']['line175_5_note_v2p4a'] = (
    'LEAD line 175 (5): the time-only 0xFFFF term is REPLACED in design by R2 (Pc invalid: release iff ECU RUN AND accelerometer thrust '
    '>= 37.16 N for 3 frames at 100 Hz, otherwise hold the drogue and ECU ABORT at t_E2 + 0.8 s; PROPOSAL to be flown). The Pc-valid terms '
    'are unchanged. On an unpurged start the Pc-valid term releases before the post-light vapour gap (purge_commit_rule_v2p4a)')
d['drogue_release_hold']['tag'] += '; LEAD line 175 (5)'

# ------------------------------------------------------------------ new blocks
d['relief_v2p4a'] = T(dict(
    tank_relief_set_MPa=6.9, tank_relief_basis='below the 7.0 MPa tank MEOP (ENG-09); fire case relieving at 8.35 MPa',
    fire_relieving_MPa=8.35, MAWP_MPa_min=8.42, proof_MPa_min=10.5,
    back_relief_check='MV segment -> tank, Cv >= 0.1', secondary_disc='9.5 MPa +/- 5 % on FS-01, discharge overboard',
    supersedes='trapped-liquid relief <= 7.5 MPa (v1; ENG-09 text superseded by LEAD line 172 (6))',
    naming_note='LEAD line 172 (6) calls this block "relief_v2p4"; the brief names it relief_v2p4a; same content'),
    'LEAD line 172 (6); REPORT v2.4 §2.7 (DERIVED sizing); REQUIREMENTS amendments. Verification CF-3 / proof test (founders)')
d['stand_safing_v2p4a'] = T(['no retry into a pooled chamber',
                             'N2 purge of the chamber >= 60 s at >= 10 g/s',
                             'hold >= 15 min before approach, with Pc at ambient and the head thermocouples falling',
                             'then the safing procedure (REPORT §10.2)'],
                            'LEAD line 172 (1); supersedes "wait >= 5 s" everywhere (H9, §10.2, igniter.sequence.abort_if_no_ignition)')
fe = J('fa1_envelope_v2p4a.json')
d['fa1_envelope_v2p4a'] = T(dict(
    file='02-combustion/data/v2p4a/fa1_envelope_v2p4a.json (64b328150025fa1e); tables fa1_tables_v2p4a.json (677fd9ccd297fdf4)',
    by_reading_entrance_tf1ms_OF4_12=[{k: r[k] for k in ('reading', 'entrance', 'head_peak_bar', 'aft_peak_bar', 'above45_head_ms',
                                                        'above67p5_head_ms', 'above90_head_ms', 'impulse_head_bar_ms', 'aft_over_head',
                                                        'governing_case')} for r in t1],
    head_peak_by_OF_tf_baseline_over_bracket_bar=tb['head_peak_by_OF_tf'],
    thrust_and_dynamic=tb['thrust_and_dynamic'],
    outflow_frozen_vs_equilibrium='throat outflow at 0.963 / 0.92 of the area: peaks +0.42-0.61 % / +0.9-1.3 % at tf 1 ms, +1.40-1.60 % / '
                                  '+3.0-3.5 % at tf 3 ms (fa1_outflow_sens_v2p4a 540a78f8b9634f76); the 92 bar design value becomes about '
                                  '92.2 bar (92.9 at 8 %); the 102 bar bracket covers both',
    fuel_basis_styrene='peaks x1.018-1.028; maximum 90.08 bar (as written, sharp, O/F 4, tf 1 ms); baseline rounded 85.0 bar',
    fuel_inventory_at_light='TO-VERIFY (O/F below 4 not excluded; the closed-volume pressure peaks at O/F 3.5-4)',
    structural_load_LEAD_173='90 bar abs quasi-static at head and aft for every part; parts with periods 0.25-1 ms also 92 bar design '
                             '(baseline rounded 89.0 x 1.03 fuel basis) and 102 bar sensitivity; 1.8 kN for 4 ms confirmed bounding',
    not_modelled='1-D gas dynamics across the 230 mm port (acoustic transit 0.3-1 ms; REV-COMB-2 R2-11); real burn time and fuel '
                 'fraction (IGN-1 / T4 with the dynamic Pc channel)'),
    'SIM (constant-cv network, reviewer readings) on ASSUMED burn time and fuel inventory; LEAD lines 172 (2), 173')
d['pc_dynamic_channel'] = T(dict(
    stand='>= 10-20 kHz sampling with an anti-alias filter; flush-mounted transducer or a characterised short sense line (resonance '
          'measured); ranges covering the FA-1 envelope (>= 100 bar abs)',
    flight='control channel 1 kHz; LIGHT_SPIKE values logged at 1 kHz are LOWER BOUNDS of a 1-3 ms spike',
    why='modelled spikes last 1-3 ms (raw above 30 bar <= 1.9 ms); 1L and Helmholtz modes at 1.1-1.8 kHz alias at 1 kHz'),
    'LEAD line 172 (5); REV-COMB-2 R2-10; owners Electronics (channel) and founders (stand)')
d['interlock_guard_band'] = T(dict(
    thresholds='T_tank <= 24 C and P_tank <= 55.28 bar abs, each lowered by the total channel uncertainty (Electronics states it)',
    margin_to_cover='MEOP margin 0.67 bar on Pc ~ 0.92 K ~ 1.14 bar of P_tank (Table 3.8: +0.73 bar Pc and +1.24 bar P_sat per K, DERIVED)',
    CF1_CF3_acceptance='full-stroke Cd <= 0.80 and line loss >= the modelled value at the failure flow (~0.38 kg/s; ~2.5-2.7 bar by mdot^2 '
                       'scaling, DERIVED); otherwise MEOP is restated'),
    'LEAD line 172 (4); REV-COMB-2 R2-07; values MISSING until Electronics states the channel uncertainty')
d['t1t4_law_v2'] = T(dict(
    spec='02-combustion/T1-T4-REGRESSION-SPEC.md v2',
    rule=('default gate "current rule OR a_meas >= 1.25 -> change grain" unless the oxidiser-flux law is positively shown at sigma(S) <= 1.5 % '
          'on the T3 holds and a T1/T2 firing (LEAD line 172 (3))'),
    law_stations_x_over_L=[0.80, 0.85, 0.90], ref_stations=[0.10, 0.30], a_meas_station=0.97,
    errs_safe_rho_max={k: S[k]['rho_max'] for k in S}, errs_safe_allowance_left={k: S[k]['allowance_left_min'] for k in S},
    errs_safe_rule='a_meas,gate = max(1, rho_max) x a_meas for the fired calibration set unless the oxidiser-flux law is shown (proposal)',
    file='t1t4_law_resolution_v2p4a.json (05b5ae5c20e04bd8)'),
    'DERIVED from SIM grain_q1d histories (78 B1 records on gnc.json v3 and v3.1 cycles; O/F is not a gnc.json quantity); ASSUMED durations, s1, ss')
d['purge_commit_rule_v2p4a'] = T(dict(
    rule_LEAD_175_3=('PROVISIONAL: PURGE commits no later than the plain relight trigger - 1.7 s (T_fire delay <= 0.6 s); with no commit the '
                     'purge is NOT run and the relight proceeds unpurged; refuted if Combustion shows an unpurged start carries a hazard outside '
                     'its abort model'),
    finding=('REFUTED as written (SIM/DERIVED). The abort model counts a light inside a liquid slug as a success and does not model the '
             'voids behind it. PURGE NOT RUN LO worst (unlined [12.49, 11.21, 23.44, 0, 0] cm3): every light within W (P %.3f of starts) is '
             'inside the first slug and is followed by the 23.4 cm3 vapour gap %.3f-%.3f s after E2 on the 200 N start ramp (lift flow: median '
             '%.3f, max %.3f s); gap %.3f-%.3f s (lift flow %.3f s). E2 in the latency model is Pc > 3 bar abs, so the drogue-release term is '
             'already true; A3 ratio in the gap <= %.2f (< 0.40) -> A3 abort after the release in %.3f of starts (dead vehicle released, GNC '
             'R1 class) instead of the modelled abort under the drogue. Same model: no successful light in that state (P_total ~ 0, not ~0.75)'
             % (lo['P_light_within_W'], lor['arrival_after_E2_s']['min'], lor['arrival_after_E2_s']['max'], lol['arrival_after_E2_s']['median'],
                lol['arrival_after_E2_s']['max'], lor['gap_duration_s']['min'], lor['gap_duration_s']['max'], lol['gap_duration_s']['max'],
                pb['A3_ratio_max'], lor['P_released_then_A3'])),
    lined_LO_worst_P_released_then_A3=lin['ramp_to_200N']['P_released_then_A3'],
    population_0_2deg={k: dict(n_records=v['n_records'], n_light_then_gap=v['n_records_light_then_gap'],
                               mean_P_released_then_A3=round(v['mean_over_records_P_released_then_A3_pool_ramp'], 3)) for k, v in pop.items()},
    purged_states='no post-light gap (P 0)',
    HI_worst='P_abort 1.0: no light, no release; no new hazard',
    least_state='0.74 cm3 gap, 4-11 ms: below the A3 detection (dip only)',
    FA1_interaction=('200 N relight ramp: the pintle seats before the liquid returns (no re-admission); 500 N ramp bound <= %.1f g upper / '
                     '%.2f g linear closing vs the 2.141 g FA-1 fast part (only if flamed out in the gap)'
                     % (pc['ramp_to_500N']['liquid_g_upper']['max'], pc['ramp_to_500N']['liquid_g_linear_closing']['max'])),
    proposal=('no commit by the plain trigger - 1.7 s -> no relight on that pass (as A14 for a fail-closed bleed), unless GNC and Combustion '
              'close a ride-through mode (drogue release held on unpurged starts; torch kept on and A3 adapted through the gap) on evidence '
              '(CF-4 O-3, IGN-1). Lead decides'),
    file='unpurged_start_check_v2p4a.json (4c745dcfbf09aef7)'),
    'SIM on ASSUMED delays (rg01 set reproduced) + DERIVED line states; ramp and flow ~ mdot_ox(F) DERIVED; A3 ratio DERIVED (CEA); not physical')
d['tank_outlet_coverage_v2p4a'] = T(dict(
    inputs='GNC purge_outlet_inputs.json 47b4deb96ea22043 (six re-flown records; 500-run tilt distributions)',
    geometry_used='tube 101.6 x 3.175 mm (ID 95.25 mm), internal length 0.4449 m, flat bolted bulkheads (mechanical.json v1 concept, not in CAD)',
    liquid_depth_m={'766 g': [round(min(x['depth_m'] for x in pd['liquid_depth'] if x['m_liq_g'] < 900), 4),
                              round(max(x['depth_m'] for x in pd['liquid_depth'] if x['m_liq_g'] < 900), 4)],
                    '1170 g': [round(min(x['depth_m'] for x in pd['liquid_depth'] if x['m_liq_g'] > 900), 4),
                               round(max(x['depth_m'] for x in pd['liquid_depth'] if x['m_liq_g'] > 900), 4)]},
    surface_drop_at_wall_m={k: round(v['surface_drop_at_wall_m'], 4) for k, v in pd['surface_tilt_at_wall'].items()},
    wall_uncovering_angle_deg=round(pd['wall_uncovering_angle_deg'], 1),
    dip_pull_through_h_c_m=round(pd['dip_pull_through_LubinSpringer_h_c_m'], 4),
    roll_spin_up_s_min=round(pd['roll_spin_up_Ekman_s_min'], 0), slosh_first_mode_Hz=round(pd['slosh_first_mode_Hz'], 2),
    verdict=('COVERED quasi-statically with large margin IF the outlet is on the aft bulkhead of an axial tank (>= 120 mm of liquid over any point '
             'of the aft bulkhead at 766 g and the largest angle); not a final verdict'),
    missing=pd['missing']),
    'DERIVED (geometry, CoolProp); GNC SIM inputs; LITERATURE screening (Lubin & Springer 1967); not a physical approval')
d['vented_mass_brackets_v2p4a'] = T(dict(
    file='vented_mass_brackets_v2p4a.json (8e8ca9329c74a01f)', rows=VB['rows'], rate_lines_g_s=VB['rate_lines_g_s'],
    note=('open-element minimum = the all-vapour line until 1.0 s; the barrier-element minimum is a construct (T4 stall; bubble point ~0.7 kPa vs '
          '45.5 bar) below it until 1.6 s; the maximum never reaches the all-liquid line (every record starts with vapour)')),
    'SIM reduction of purge_duration_v2p4 records (not re-run); REV-COMB-2 R2-06')
d['superseded_v2p4a'] = T({
    'A4 30 bar raw 5 ms': '30 bar filtered 5 ms (line 166 (4))',
    'closure confirmed before E1 / by E0 - 0.05 s': 'E1 closure term, deadline <= torch gate (line 166 (3)); E0 - 0.05 s = scheduled flow end',
    'FC delays T_fire (line 164)': 'commit <= plain trigger - 1.7 s, else no purge (line 175 (3), provisional; unpurged branch refuted)',
    'wait >= 5 s after a no-light': 'stand_safing_v2p4a (line 172 (1))',
    'trapped-liquid relief <= 7.5 MPa': 'relief_v2p4a (line 172 (6))',
    'FA-1 48.9-75.5 bar; Mechanical 75.5 bar <= 3 ms pulse check': 'fa1_envelope_v2p4a; load per line 173',
    '15-25 C conditioning': '15-24 C at ARM (ENG-12 as amended)',
    'T1-T4 law decision on the total-flux form': 't1t4_law_v2 (reversed burden, line 172 (3))',
    'J1 pending agreement; lip <= 250 C requirement': 'J1 CONFIRMED (line 146); 250 C a goal, J1 lip ~342 C'}, R + ' §13')

# ------------------------------------------------------------------ LEAD line 181 (2), (4), (10): coordinator request after REV-GNC-3
UO = J('unpurged_outcomes_v2p4a.json'); nm = UO['named_states']; pp = UO['population_0_2deg']
w_ = nm['purge_not_run_unlined_LO_0-2deg_worst']; wl_ = nm['purge_not_run_lined_LO_0-2deg_worst']; wh_ = nm['purge_not_run_unlined_HI_0-2deg_worst']
assert w_['paused']['ramp_pool_Fcmd']['P_success'] == 0.0 and abs(w_['paused']['ramp_pool_Fcmd']['P_released_then_A3'] - 0.7116) < 1e-3
assert wh_['paused']['ramp_pool_Fcmd']['P_no_light'] == 1.0 and wl_['paused']['ramp_pool_Fcmd']['P_success'] == 0.0
cls = lambda x: {k: round(x[k], 4) for k in ('P_no_light', 'P_A3_before_release', 'P_released_then_A3', 'P_success')}
popc = {}
for k in ('lin0.0|LO', 'lin1.0|LO', 'lin0.0|HI', 'lin1.0|HI'):
    v = pp[k]
    popc[k.replace('lin0.0', 'unlined').replace('lin1.0', 'lined')] = dict(
        n_records=v['n_records'],
        mean_P_success_pool_ramp=round(v['mean_over_records_best_case']['P_success'], 3),
        mean_P_success_lift_flow=round(v['mean_over_records_worst_case']['P_success'], 3),
        mean_P_released_then_A3_pool_ramp=round(v['mean_over_records_best_case']['P_released_then_A3'], 3),
        mean_P_released_then_A3_lift_flow=round(v['mean_over_records_worst_case']['P_released_then_A3'], 3),
        mean_P_no_light=round(v['mean_over_records_worst_case']['P_no_light'], 3),
        share_records_P_success_below_0p05=round(v['share_of_records_P_success_below_0p05'], 3))
d['purge_commit_rule_v2p4a']['v']['line181_2_answer'] = dict(
    LO_or_HI=('NOT SETTLED by analysis. LO and HI are the two ends of Mechanical\'s wall heat-transfer bracket (segment heat cases isothermal, '
              'hw+5K, ARM_bay45C_liq24C at h LO / h HI); both ends are ASSUMED and no evidence selects one. CF-4 optional generation runs and '
              'T4 measure it'),
    decision_independent=('The L* choice does not need LO/HI: at the worst PURGE NOT RUN states an unpurged start succeeds with P = 0 under '
                          'both (HI: no light, P_abort 1.0; LO: every light is followed by the vapour gap and an A3 abort). GNC\'s LO premise '
                          '(P_total ~0.75 = 1 - P_abort) counted every light as a success, which the abort model never checked'),
    L_star_recommendation=dict(v=1.3, unit='s', note='use the HI value: purge whenever the lead to the plain trigger is >= 1.3 s'),
    below_L_star=('no unpurged relight on that pass (no purge -> no relight, as A14), unless GNC shows that holding the drogue release on '
                  'unpurged starts to >= E2 + 0.22 s (gap arrival <= 0.193 s with the flow held at the lift + 0.022 s A3 detection) gains P; '
                  'then the light-gap-A3 sequence aborts with the drogue attached'),
    hazard=('RELEASED_THEN_A3 (outside the abort model): light -> drogue release at E2 (Pc >= 3 bar abs) -> post-light vapour gap -> A3 abort '
            '-> dead vehicle released (GNC touchdown class about -32 m/s against about -22 m/s on the drogue)'),
    outcome_classes_worst_states={
        'LO_worst_unlined_[12.49,11.21,23.44]': dict(pool_ramp=cls(w_['paused']['ramp_pool_Fcmd']), lift_flow=cls(w_['paused']['lift_flow_held'])),
        'LO_worst_lined_[15.6,12.4,19.2]': dict(pool_ramp=cls(wl_['paused']['ramp_pool_Fcmd']), lift_flow=cls(wl_['paused']['lift_flow_held'])),
        'HI_worst_[51.8]': dict(pool_ramp=cls(wh_['paused']['ramp_pool_Fcmd']))},
    population_0_2deg=popc,
    population_note=('all PURGE NOT RUN records at 0 and 2 deg; bracket records, NOT probability-weighted; P(success) per record is bimodal '
                     '(0 or 1); pool ramp = 2500 N/s start ramp to F_cmd 200/500 N, lift flow = flow held at the lift (upper bound on times)'),
    file='unpurged_outcomes_v2p4a.json (18a639d61b58ce8a); script unpurged_outcomes_v2p4a.py (copies the parent code verbatim)',
    tag='SIM on ASSUMED delays (rg01 set reproduced) + DERIVED line states; LO/HI ASSUMED bracket ends; not physical')
CF = J('cold_flow_thrust_v2p4a.json'); cs = CF['states']
rng2 = lambda vals, nd=1: [round(min(vals), nd), round(max(vals), nd)]
perF = {}
for i, r0 in enumerate(cs['A1_relight_286.7K']['per_F_cmd']):
    rows = [cs[k]['per_F_cmd'][i] for k in cs]
    key = ('%g N' % r0['F_cmd_N']) if not isinstance(r0['F_cmd_N'], str) else r0['F_cmd_N']
    perF[key] = dict(lift_mm=rng2([r['lift_mm'] for r in rows], 3), F_bound_N=rng2([r['F_bound_N'] for r in rows]),
                     F_nominal_Cd070_N=rng2([r['F_nom_N'] for r in rows]), F_nominal_Cd080_N=rng2([r['F_nom_Cd080_N'] for r in rows]))
assert abs(perF['62.5 N']['F_bound_N'][1] - 13.3) < 0.05 and abs(perF['500 N']['F_bound_N'][1] - 119.9) < 0.05
prof = {}
for p in ('hold_start_level_62p5N', 'ramp_to_200N', 'ramp_to_500N', 'envelope_any_command'):
    prof[p] = dict(F_bound_max_0_0p8s_N=rng2([cs[k]['profiles'][p]['F_bound_N']['max_0_0p8s'] for k in cs]),
                   F_nominal_max_0_0p8s_N=rng2([cs[k]['profiles'][p]['F_nom_N']['max_0_0p8s'] for k in cs]),
                   t_bound_reaches_37p16N_s=[cs[k]['profiles'][p]['t_first_s']['37.16N_threshold_alone']['bound'] for k in cs],
                   t_nominal_reaches_37p16N_s=[cs[k]['profiles'][p]['t_first_s']['37.16N_threshold_alone']['nominal'] for k in cs])
reach = {lv: {m: rng2([cs[k]['F_cmd_at_which_cold_flow_reaches'][lv][m] for k in cs], 0) for m in ('bound', 'nominal', 'nominal_Cd080')}
         for lv in ('4.16N_margin_all_winds', '16.31N_margin_W_lt6', '37.16N_threshold_alone')}
d['cold_flow_thrust_v2p4a'] = T(dict(
    question='LEAD line 181 (4): cold-flow apparent thrust under the drogue after an undetected flame-out at E2, 0-0.8 s after E2, relight tank states',
    setting=('Pc invalid in flight -> ECU open loop on the P_feed feed-forward map (A7; electronics.json "Pc sensor fault"); A3 is blind, so nothing '
             'closes the pintle on a flame-out: the lift follows the thrust command (drive 16.7 mm/s, 10 ms lag; stroke 4.0 mm)'),
    tank_states={k: dict(T_K=round(v['T_tank_K'], 2), P_bar=round(v['P_tank_bar'], 2), v_iso_eq_m_s=round(v['v_iso_eq_m_s'], 1)) for k, v in cs.items()},
    bound_definition=('F <= mdot_max x v_iso,eq: mdot_max = Cd 0.80 (CF acceptance limit, line 172 (4)) x pintle area x Dyer flux at P1 = P_tank '
                      '(no line loss), saturated liquid, downstream at 1 atm; v_iso,eq = isentropic equilibrium expansion of the tank liquid to '
                      '1 atm. Holds for any steady adiabatic flow (dF = (P_e - P_a) dA_e; irreversibility only lowers it)'),
    nominal_definition=('quasi-steady HEM: Dyer injector (Cd 0.70; 0.80 variant), line loss 2.5 bar at 0.25 kg/s ~ mdot^2, adiabatic chamber at '
                        'the tank-liquid enthalpy, HEM nozzle (A_t 147.9 mm2 x 0.98, eps 2.0) choked or venturi, optimum-expansion thrust'),
    per_F_cmd=perF, profiles_0_0p8s=prof, F_cmd_at_which_cold_flow_reaches=reach,
    R2_numbers=CF['R2_numbers'],
    heat_pickup=dict(v_iso_eq_A1_m_s_by_added_heat={k: round(v['v_bound'], 1) for k, v in cs['A1_relight_286.7K']['heat_pickup_sensitivity'].items()},
                     start_level_bound_N_by_added_heat={k: round(v['F_bound_N'], 2) for k, v in cs['A1_relight_286.7K']['heat_pickup_nominal_sensitivity']['F_cmd_62.5N'].items()},
                     added_heat_for_start_level_bound_to_reach_16p31N_kJ_kg=rng2([cs[k]['dh_for_start_level_bound_to_reach_W_lt6_margin_J_kg'] / 1e3 for k in cs]),
                     same_as_heat_rate_kW=rng2([cs[k]['heat_rate_for_that_W'] / 1e3 for k in cs], 2),
                     note='EXCLUDED from the bound; thermal state of the chamber, grain and nozzle at the relight MISSING; hot-gas energy in the chamber at the flame-out about 0.55-0.80 kJ'),
    finding=('With the open-loop command held at the 62.5 N start level the cold-flow thrust is <= 12.5-13.3 N (bound; nominal HEM about 1 N) over '
             '0-0.8 s: it consumes the 4.16 N all-winds margin (33.0 vs 37.16 N) but not the 16.31 N margin inside W10 < 6 m/s, unless heat '
             'pick-up exceeds about 66-85 kJ/kg (2.8-3.7 kW). Any command above about 200 N (bound) or 310-350 N (nominal) makes the cold flow '
             'ALONE exceed 37.16 N, within 0.035-0.07 s (bound) or 0.07-0.125 s (nominal) of E2 on a 500 N ramp or a full-rate pintle: R2 would '
             'then release a dead vehicle. sim6 V (no cold-flow term) does not support the "holds the drogue in 1000/1000" result for such commands'),
    proposal=dict(text=('PROPOSAL for GNC R2 v2 and the lead: while the drogue is attached and Pc is invalid, hold the open-loop command at the '
                        'start level (or cap the lift at the start-level lift) until R2 confirms; GNC adds F_cold(lift, P_tank) from the CSV to '
                        'the sim6 V truth thrust (bound and nominal) and re-flies; alternatively a ratio test (accelerometer thrust against the '
                        'open-loop expected thrust)'),
                  hypothesis='the command hold keeps the dead-engine apparent thrust within the R2 margin while a lit engine still releases',
                  comparator='R2 as flown (no cold-flow term, unconstrained command)',
                  evidence_needed='CF-3 with a thrust load cell at the start-level, 200 N and 500 N lifts (cold chamber); a post-burn N2O pulse at the start-level lift in the T series (hot chamber; also measures re-ignition)',
                  refutation='a measured cold-flow thrust above 16.3 N at the start-level lift, or a GNC re-fly in which the hold loses P'),
    gnc_table='cold_flow_thrust_v2p4a.csv (e094c4be80d12f66): lift -> mdot and F (bound, nominal) per tank state',
    excluded=CF['excluded'],
    file='cold_flow_thrust_v2p4a.json (a226dfacf494cb2c); script cold_flow_thrust_v2p4a.py'),
    'DERIVED thermodynamic bound (CoolProp HEOS, Dyer flux) on ASSUMED Cd <= 0.80 and adiabatic flow; DERIVED HEM nominal on ASSUMED Cd 0.70 '
    'and line loss; ASSUMED command profiles; GNC numbers SIM; no measurement exists')
d['drogue_release_hold']['v']['line181_4_cold_flow_note_v2p4a'] = (
    'Under Pc invalid the dead engine still produces cold-flow thrust that follows the open-loop lift: <= 13.3 N at the start level, '
    '<= 37.5 N at 200 N, <= 120 N at 500 N, <= 207 N at the stroke (bound, 283.15-289.5 K): see cold_flow_thrust_v2p4a')
fm['flameout_pc_invalid_v2p4a'] = ('B-7 undetected flame-out with Pc invalid (R2 branch): the open-loop lift keeps N2O flowing; cold-flow thrust '
                                   '<= 13.3 N at the start level, alone > 37.16 N above about 200 N command (bound) -> R2 may release a dead '
                                   'vehicle; mitigation PROPOSAL: command hold at the start level while the drogue is attached (cold_flow_thrust_v2p4a)')
to = d['tank_outlet_coverage_v2p4a']['v']
A_tank = 3.141592653589793 * (0.09525 / 2) ** 2
h_req = pd['dip_pull_through_LubinSpringer_h_c_m'] + pd['surface_tilt_at_wall']['tilt_max']['surface_drop_at_wall_m']
rhos = sorted({x['rho_l'] for x in pd['liquid_depth']})
to['liquid_basis_line181_10'] = ('LEAD line 181 (10): the check already uses the liquid in the tank at the END of the PURGE flow (GNC m_liq pairs '
                                 '[start, end]; minimum end 766.4 g; depletion in the flow window 79.8-81.8 g, consistent with the 81.6 g liquid '
                                 'depletion of which 8.6 g boils into the ullage), not the 73.0 g vented mass')
to['min_liquid_for_quasistatic_coverage_g'] = dict(
    v=[round(rhos[0] * A_tank * h_req * 1e3, 1), round(rhos[-1] * A_tank * h_req * 1e3, 1)],
    basis='depth >= dip height h_c %.1f mm + wall drop %.1f mm at the 6.86 deg tilt = %.1f mm, outlet anywhere on the aft bulkhead; '
          'rho_l %.1f-%.1f kg/m3 (283.15-289.5 K)' % (pd['dip_pull_through_LubinSpringer_h_c_m'] * 1e3,
                                                     pd['surface_tilt_at_wall']['tilt_max']['surface_drop_at_wall_m'] * 1e3, h_req * 1e3, rhos[0], rhos[-1]),
    margin='766 g at the end of the flow is about 9x the requirement; outlet geometry still MISSING (OI-32)')

d['throat_insert_line183_note_v2p4a'] = T(
    ('LEAD line 183 (2): NZ-01 graphite throat insert MS -0.44 (thermal) accepted TEST-BASED if mechanically captured, refuted by fragment loss '
     'or a throat-area change > 2 %. Combustion: erosion alone changes the throat area by 1.9 % (nominal), 8.0-8.5 % (conservative) or 8.4-13.6 % '
     '(literature) in one A1 flight (REPORT 5.4), so the 2 % criterion cannot separate a crack from erosion. PROPOSAL: refutation = area change '
     '> 2 % beyond the erosion expected for the firing (pre/post bore, duty cycle), a non-axisymmetric step or a missing fragment (OI-40, lead)'),
    'SIM erosion (REPORT v2.4 5.4; LITERATURE kinetics as used in v2) against a LEAD criterion; contradiction kept for the lead')
# ------------------------------------------------------------------ checks: every v2.4 key kept
def keys(o, p=''):
    if isinstance(o, dict):
        for k, v in o.items():
            yield p + '/' + k
            yield from keys(v, p + '/' + k)
k0 = set(keys(d0)); k1 = set(keys(d))
assert k0 <= k1, sorted(k0 - k1)[:10]
json.dump(d, open(out, 'w'), indent=1, ensure_ascii=False)
print('v2.4 keys', len(k0), 'v2.4a keys', len(k1), 'added', len(k1 - k0))
print('wrote', out, sha(out))
