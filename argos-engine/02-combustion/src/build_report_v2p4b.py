"""REPORT.md v2.4b from the published v2.4a by asserted edits (Combustion v2.4b, 2026-10-13).

Answers REV-COMB-3 (a786101f28d45d6f) R3-01..R3-17, folds LEAD lines 186 and 194 and the coordinator relays of lines 203-205.  Every
edit replaces or inserts at an anchor that must occur exactly once.  Numbers come from the hash-asserted v2.4b data files, the
staged combustion.json v2.4b and the specifications; each data file's producing script is checked against the file in src/.
usage: python -I build_report_v2p4b.py REPORT_V24A DATA_V2P4B_DIR COMBUSTION_JSON_V24B SPEC_T1T4 SPEC_CF4 SRC_DIR OUT_MD
"""
import hashlib, json, os, sys
sys.dont_write_bytecode = True
import numpy as np
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
rep_f, dd, cj_f, spec_t, spec_c, src_dir, out = sys.argv[1:8]
assert sha(rep_f) == '062e307a8d25e1ec', 'REPORT is not v2.4a'
EXP = {'release_hold_v2p4b.json': 'a926426da0e6e436', 'release_hold_records_v2p4b.csv': '59e7f44e44fbfeef',
       'population_statements_v2p4b.json': 'bffabc97aee6a5cb', 'fa1_spectra_v2p4b.json': '372b8078d7a90e75',
       'fa1_spectra_dense_v2p4b.json': '7468996959538d0f', 'fa1_histories_solver_v2p4b.npz': '399bf43d1c09de24',
       'fa1_pressure_spectra_v2p4b.csv': '55df65344f35759b', 'fa1_thrust_spectra_v2p4b.csv': '288a2294151e3760',
       'fa1_pressure_spectra_dense_v2p4b.csv': '4a4ebb65b38a9a03', 'fa1_thrust_spectra_dense_v2p4b.csv': '072f2e0f2987fda5',
       'cold_flow_start_lift_v2p4b.json': '28ce48092f33da1b', 'start_level_lit_thrust_v2p4b.json': 'ae2038c5141b7f73',
       'start_level_lit_thrust_v2p4b.csv': 'f6ac2a4da04f8d45', 'start_level_lit_thrust_0p21776mm_v2p4b.json': '10cdc03154b95216',
       'start_level_lit_thrust_0p21776mm_v2p4b.csv': 'c073d4f993f8c412', 'tank_outlet_dip_v2p4b.json': '6c11d3c19afe983c',
       'nozzle_lip_melt_in718_v2p4b.json': '23b85b7febb90c60', 'test_budgets_v2p4b.json': 'c0e4ce35659f21fa',
       'lead_items_203_205_v2p4b.json': 'e20a8b8c33af9162', 'a1_profile_line213_v2p4b.json': '46b6a1c6efec0351'}
for f, h in EXP.items():
    assert sha(os.path.join(dd, f)) == h, (f, sha(os.path.join(dd, f)))
J = lambda f: json.load(open(os.path.join(dd, f)))
CJ = json.load(open(cj_f)); assert CJ['version'] == 'v2.4b'
H_CJ, H_T, H_C = sha(cj_f), sha(spec_t), sha(spec_c)
assert (H_T, H_C) == ('b0c42b09ba47cb9c', '86cd01e34c28aa82')
# producing scripts: the file in src/ must be the one that wrote each data file
SCR = {}
for f in ('release_hold_v2p4b.json', 'population_statements_v2p4b.json', 'fa1_spectra_v2p4b.json', 'fa1_spectra_dense_v2p4b.json',
          'cold_flow_start_lift_v2p4b.json', 'start_level_lit_thrust_v2p4b.json', 'start_level_lit_thrust_0p21776mm_v2p4b.json',
          'tank_outlet_dip_v2p4b.json', 'nozzle_lip_melt_in718_v2p4b.json', 'test_budgets_v2p4b.json', 'lead_items_203_205_v2p4b.json',
          'a1_profile_line213_v2p4b.json'):
    x = J(f); s = os.path.basename(x['script'])
    assert sha(os.path.join(src_dir, s)) == x['script_sha256_16'], (f, s)
    SCR[f] = (s, x['script_sha256_16'])
for s in ('build_specs_v2p4b.py', 'write_interface_v2p4b.py', 'build_report_v2p4b.py'):
    SCR[s] = (s, sha(os.path.join(src_dir, s)))

RH = J('release_hold_v2p4b.json'); G = RH['groups']
PS = J('population_statements_v2p4b.json')['counts']
DN = J('fa1_spectra_dense_v2p4b.json'); PD = DN['period_domain']
CF = J('cold_flow_start_lift_v2p4b.json'); CS = CF['summary']
L1 = J('start_level_lit_thrust_v2p4b.json'); L2 = J('start_level_lit_thrust_0p21776mm_v2p4b.json')
DIP = J('tank_outlet_dip_v2p4b.json')['summary']
NZ = J('nozzle_lip_melt_in718_v2p4b.json')['summary']
TB = J('test_budgets_v2p4b.json')
LI = J('lead_items_203_205_v2p4b.json')
A1 = J('a1_profile_line213_v2p4b.json')
A1S, A1P, A1R, A1T = A1['comparators_300m_summary'], A1['purge_scaling'], A1['comparators_300m_records'], A1['states']
assert A1P['M_2p5s_slope_g_per_K'] == 0.66 and A1P['T_at_76g_2p5s_K'] == 294.21 and A1S['ascent_cooling_K'] == [5.81, 7.49]
assert round(A1T['297.15K']['F_bound_map_lift_N'], 2) == 14.93 and A1S['T_relight_K'] == [282.97, 290.07]
I1, I2, I3, I4, I5, I6, I7, I8 = (LI[k] for k in ('item1_purge_basis', 'item2_start_level_lift', 'item3_E2_rule', 'item4_firmware_sources',
                                                 'item5_fa1', 'item6_classes_500N', 'item7_A1_duration', 'item8_pc_port_gas'))
f1 = lambda x: f'{x:.1f}'
f2 = lambda x: f'{x:.2f}'
pdv = lambda b, k: PD[b][k]['value_bar']
# numbers asserted against the prose below
assert (round(pdv('T_le_0p1ms', 'head|all'), 1), round(pdv('T_le_0p1ms', 'head|baseline'), 1)) == (93.6, 88.6)
assert (round(pdv('T_0p1_to_1ms', 'head|all'), 1), round(pdv('T_0p1_to_1ms', 'head|baseline'), 1)) == (120.3, 102.5)
assert (round(pdv('T_1_to_20ms', 'head|all'), 1), round(pdv('T_1_to_20ms', 'head|baseline'), 1)) == (146.9, 138.9)
tc02 = [b for b in DN['mechanical_modal_bands'] if b['dominant_part'] == 'ENG-TC-02'][0]
assert (round(tc02['max_in_band_baseline']['value_bar'], 1), round(tc02['max_in_band_all']['value_bar'], 1)) == (99.5, 111.7)
Tt = np.array(DN['periods_ms']['thrust'])
def thr(grp, k, t):
    x = DN['envelopes'][grp][k]
    return float(np.interp(t, Tt, np.array(x['value'] if isinstance(x, dict) else x)))
GB, GA = 'vapour_once|rounded_Cd1.0|grid_OF4-12|all', 'all|all|incl_OF3-3.5|all'
assert round(thr(GA, 'F_whole_Cf1.35_N', 25.0)) == 1743 and round(thr(GA, 'F_whole_Cf1.35_N', 40.0)) == 1452
s1, s2 = L1['summary'], L2['summary']
assert s2['n_corners_never_ge_37p16N_in_window'] == 3 and s1['n_corners_never_ge_37p16N_in_window'] == 8
assert abs(s2['latest_first_t_ge_37p16N_after_E2_s'] - 0.205) < 1e-9
m = {k: v for k, v in I1['vented_mass_g'].items()}
k260 = [k for k in m if k.startswith('2.60 s')][0]
assert abs(m[k260]['combustion_bound_open_g'] - 76.05) < 1e-6 and abs(I1['cap_for_76g']['both_open_s_with_0p05_offset'] - 2.5483) < 1e-6
assert I8['c_design_min_m_s'] == 181.0 and I8['c_isentropic_N2O_min_m_s'] == 202.0 and I8['c_products_frozen_range_m_s'] == [1049.0, 1136.0]
assert abs(I3['shift_bound_s'] - 0.0147) < 1e-9
ns = NZ['solidus|T0_342C']; ns655 = NZ['solidus|T0_655C']; ns295 = NZ['solidus|T0_295C']
assert [round(x, 2) for x in ns['L1_lumped_1mm_s']] == [1.10, 5.88] and [round(x, 2) for x in ns655['L1_lumped_1mm_s']] == [0.77, 4.08]
C4 = TB['CF4']; assert (C4['runs_lower'], C4['runs_upper_with_4deg_repeats']) == (59, 105)
assert [round(C4['N2O_kg'][k], 1) for k in ('lower', 'upper')] == [10.0, 17.8]
pp = C4['P1_lift_basis']; assert round(pp['0.21776mm']['P1_after_lift_s'], 3) == 0.275 and round(pp['0.21776mm']['t_lift_s'] * 1e3, 1) == 29.5

text = open(rep_f, encoding='utf-8').read()
N = [0]


def R(old, new):
    global text
    c = text.count(old)
    assert c == 1, ('anchor count', c, old[:120])
    text = text.replace(old, new); N[0] += 1


def AFTER(anchor, block):
    R(anchor, anchor + block)


# ================================================================== header and §0
R(text.split('\n')[2], (
    'Version 2.4b, 2026-10-13. Owner: Combustion and Propulsion. Interface: `interfaces/combustion.json` v2.4b (sha256/16 `%s`); v2.4a '
    '(`5237d4584bad38c4`) is kept as `data/v2/combustion_interface_v2p4a_as_published.json` and `superseded/v2p4a/combustion.json`, v2.4 '
    '(`469727032124329f`) and v2.3 (`d9ec54fbf450e243`) as before. Status: targeted revision v2.4b in answer to the independent re-review '
    '`reviews/REVIEW-COMBUSTION-R3.md` (REV-COMB-3, REVISE (targeted)), the lead decisions of CHANGELOG lines 186 and 194 and the '
    'coordinator relays of lines 203-205, and the founder decision of line 213 (A1 apogee target about 210 m). v2.4a of this report (`062e307a8d25e1ec`) is archived as `02-combustion/superseded/v2p4a/REPORT.md`. '
    'Digital only, *Por revisar*: the v2.4b changes await re-review (line 194 (10): a delta check of the R3-01 and R3-02 numbers, the rest by '
    'document diff). Companion files: `02-combustion/CF-4-SPEC.md` v2.1 (`%s`), `02-combustion/T1-T4-REGRESSION-SPEC.md` v3 (`%s`) and the '
    'item-by-item answer `02-combustion/REVISION-RESPONSE-R3.md`. Nothing in this report is physical approval.') % (H_CJ, H_C, H_T))
R('The structural load is 90 bar abs quasi-static at head and aft for every part, 92 / 102 bar abs for parts with periods of 0.25-1 ms, and a '
  '1.8 kN x 4 ms thrust spike (LEAD line 173).',
  'The structural load (LEAD line 194 (1)-(2), which restates line 173 with a period domain) is 90 bar abs quasi-static at head and aft for '
  'load paths with a natural period T <= 0.1 ms; for 0.1 < T <= 1 ms yield at 93 bar abs and ultimate at 102 bar abs; for T > 1 ms the '
  'all-case spectrum value at the part\'s period, or Mechanical\'s FA1S step case (about 151 bar abs); the 1.8 kN x 4 ms thrust rectangle for '
  'T <= 20 ms and the FA-1 long-period thrust spectrum above 20 ms. v2.4b publishes the spectra (§7.6): the all-case head value exceeds the '
  'domain values below 1 ms (%s bar abs at T <= 0.1 ms; %s bar abs at 0.1-1 ms, baseline %s), a contradiction kept for the lead (OI-41).'
  % (f1(pdv('T_le_0p1ms', 'head|all')), f1(pdv('T_0p1_to_1ms', 'head|all')), f1(pdv('T_0p1_to_1ms', 'head|baseline'))))
R('so the 0.81 s plan holds (SIM, `rg01_line_states_v2p4.json`)',
  'so the 0.81 s plan holds on the predictor path, with PURGE committed (scope of LEAD line 181 (2)) (SIM, `rg01_line_states_v2p4.json`)')
R('v2.4a: the PURGE commit rule of LEAD line 175 (3) and Combustion\'s check of an unpurged start are in item 12 and §2.8.',
  'v2.4b: the commit rule is decided: PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s; below it there is no purge '
  'and no unpurged relight on that pass (LEAD line 186 (1); item 13, §2.8, §15.2).')
R('could melt the 316L lip in 1.07-5.70 s (lumped bound); hence hazard H19',
  'could melt the lip, which is Inconel 718 since TC-09 changed material (LEAD lines 177 (1)/178), in %s-%s s (lumped bound from 342 C; '
  '%s-%s s from 655 C; v2.4b, §6.5); hence hazard H19' % (f2(ns['L1_lumped_1mm_s'][0]), f2(ns['L1_lumped_1mm_s'][1]),
                                                        f2(ns655['L1_lumped_1mm_s'][0]), f2(ns655['L1_lumped_1mm_s'][1])))
R('**PURGE commit rule (LEAD line 175 (3), PROVISIONAL): PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge.** '
  'Line 164\'s "the FC delays T_fire" is withdrawn.',
  '**PURGE commit rule.** v2.4a carried the PROVISIONAL rule of LEAD line 175 (3) (commit no later than the plain relight trigger - 1.7 s); '
  'line 186 (1) superseded it (L* = 1.3 s; item 13). Line 164\'s "the FC delays T_fire" is withdrawn.')
R('Proposal: no commit by the deadline -> no relight on that pass. The lead decides (OI-31).',
  'Combustion proposed no relight on that pass after a missed commit; the lead adopted it (line 186 (1); OI-31 closed).')
R('under HI (no light). Combustion recommends L* = 1.3 s (§2.8, Table 2.17).',
  'under HI (no light). Combustion recommended L* = 1.3 s (§2.8, Table 2.17), which line 186 (1) adopted.')
R('Quasi-static coverage needs 13.6 mm of liquid, 78.6-82.5 g: about 9x below the minimum (§2.4).',
  'Quasi-static coverage needs 13.6 mm of liquid (78.6-82.5 g); 766 g remains at the end of the purge flow, 9.3-9.7x (LEAD line 194 (5) '
  'wording; §2.4).')
R('and heat pick-up from the hot chamber is excluded. PROPOSAL: hold the open-loop command at the start level while the drogue is attached '
  'with Pc invalid (OI-38).',
  'and heat pick-up is excluded (line 194 (4) places the TO-VERIFY on the injector-body and feed soak-back temperature at the relight). '
  'The command hold at the start level while the drogue is attached with Pc invalid, proposed here, was adopted by LEAD line 186 (2); its '
  'margin is CONDITIONAL on Cd x A x G at the start lift (line 194 (4); item 13).')
hold = {g: {p: G[g][p]['hold_needed_s'] for p in ('ramp_to_200N', 'ramp_to_500N', 'lift_flow_held')} for g in G}
AFTER('    - GNC rev2 gives a specific-force angle of up to 2.71 deg during the purge flow, above the 2 deg purge basis: OPEN (OI-35; §2.8).\n',
      '13. **v2.4b patch (REV-COMB-3; LEAD lines 186, 194 and 203-205).**\n'
      '    - **Release hold (R3-01; LEAD line 194 (3); §2.8, Table 2.18).** The "E2 + 0.22 s" hold of line 186 (1) came from one state and is '
      'withdrawn by the lead. Over all 2160 PURGE NOT RUN records the hold that leaves no released-then-A3 start is 0.30 s with the 2500 N/s '
      'ramp to 200 N (%.2f s with the 10 ms frame margin), %.2f s with the ramp to 500 N, and none inside W with the flow held at the start '
      'lift (%.2f s). The unpurged alternative is NOT ADOPTED (line 204 (2)); the per-record classes of all three profiles are published for '
      'GNC. With the ECU\'s relative E2 rule the holds move by at most +%.1f ms (§15.5).\n'
      '    - **FA-1 spectra (R3-02, R3-03, R3-04; LEAD line 194 (1)-(2); §7.6, Tables 7.6c and 7.6d).** Head and aft equivalent-pressure spectra '
      'to 50 ms on the 896 cases, dense below 1 ms. Maximum head values, all cases / baseline: %s / %s bar abs at T <= 0.1 ms, %s / %s at '
      '0.1-1 ms, %s / %s at 1-20 ms. The all-case values exceed the line-194 (1) numbers below 1 ms (OI-41, for the lead); FA1S (about 151 '
      'bar abs) bounds every period. Long-period thrust: %.2f kN at 25 ms, %.2f kN at 40 ms, %.2f kN at 100 ms (all cases); the 1.8 kN x 4 ms '
      'rectangle bounds FA-1 to 20 ms.\n'
      '    - **Start-level cold flow and lit thrust (R3-05, R3-14; LEAD line 194 (4); §7.3, Table 7.3b).** The 16.31 N margin of the command '
      'hold is CONDITIONAL on Cd x A x G at the start lift; CF-3 accepts it (F <= 16.31 N minus the heat allowance, or mdot <= %.1f-%.1f g/s). '
      'The heat that matters is added at tank pressure: injector-body and feed soak-back temperature at the relight. The grain_q1d lit '
      'history at THE start-level lift (0.21776 mm, A1 state): %.1f-%.1f N between E2 and E2 + 0.5 s, %d of 72 corners below 37.16 N '
      'throughout that window (at 0.2039 mm: %.1f-%.1f N, %d of 72).\n'
      '    - **THE start-level lift (line 203 (7); §15.3).** h_s(T) is the row of the ignition-lift table at the E0 tank temperature: 0.2039 mm '
      'at 20 C (37.1 g/s), 0.21776 mm at the A1 relight state (37.4 g/s). The ECU hold lift 0.2154 mm (an open-loop-map value) is retired; '
      'CF-3 measures at the commanded lift with the encoder recorded.\n'
      '    - **H19 for Inconel 718 (R3-09; LEAD line 194 (9); §6.5).** Solidus 1260 C (DATASHEET, Special Metals SMC-045; PDF not archived, '
      'TO-ARCHIVE): lumped 1 mm %s-%s s from 342 C and %s-%s s from 655 C; 1 mm depth (FD) %s-%s s from 342 C. Sealing stays the control.\n'
      '    - **Stand dynamic Pc channel (R3-10; LEAD line 194 (7); §10).** Range >= 100 bar abs; proof >= 1.1 x the all-case spectrum at the '
      'transducer path period: >= 112 bar abs flush-mounted (103 needed), >= 132 bar abs for a 0.1-1 ms path; a path period above 1 ms is not '
      'acceptable.\n'
      '    - **Specifications (R3-06, R3-07, R3-08; LEAD line 194 (8); §10.3-10.4).** T1-T4 v3: two-sided flux test, red lines and abort '
      'criteria, validity rules, char removal, counts and N2O (T1 at 2t = 8 s uses %.3f kg, %.0f %% of a 2.0 kg flight load; 2t <= %.1f s on a '
      'flight-size tank; stand tank MISSING). CF-4 v2.1: re-baselined on the v3.5.1 bleed path, red lines, IS-1/IS-2 preparation, the probe '
      'threshold, P1 in volume form, %d-%d runs and %.1f-%.1f kg of N2O (TO-QUOTE, Sønderborg DK-6400).\n'
      '    - **NZ-01, outlet coverage and outlet dip (R3-15, R3-16, R3-17; LEAD line 194 (5)-(6)).** The frozen-prediction procedure (§15.12); '
      'the line-186 (5) wording (§2.4); dip onset %.1f-%.1f g at 125 N, %.1f-%.1f g at 250 N and %.1f-%.1f g at 500 N (283-289.5 K) for '
      'GNC\'s landing reserve (§2.4, §15.11).\n'
      '    - **Population statements (R3-13).** Counted per command profile (§2.8, `population_statements_v2p4b.json`).\n'
      '    - **Lines 203-205 (§15).** Purge flow basis: neither 29.8 nor 32.0 g/s x t; the record basis gives <= %.2f g at 2.5 s and %.2f g at '
      '2.60 s of flow (the 2.55 s both-open cap), at the 76 g limit (OI-42). The firmware constants 2500 N/s, 0.5 s, 5 bar abs and 0.12 s '
      'have source text (§15.10). A1_none p99 8.375 s changes no A1 statement (§15.13). Pc port passage (line 205): c >= %.0f m/s if the '
      'passage holds no liquid N2O (near-critical N2O; %.0f m/s for N2O compressed from saturation; burned products %.0f-%.0f m/s). Combustion '
      'cannot bound c better than 222-400 m/s in the direction that matters, and the gas-filled lower end is below 222 m/s (OI-45; §15.8).\n'
      '    - **Stale text** of the v2.4a fold and of line 186 replaced (R3-09, R3-11); the old values are in §13 and under `*_superseded` keys '
      'in the interface.\n' % (
          hold['linboth|LO']['ramp_to_200N'], hold['linboth|LO']['ramp_to_500N'], hold['linboth|LO']['lift_flow_held'], 1e3 * I3['shift_bound_s'],
          f1(pdv('T_le_0p1ms', 'head|all')), f1(pdv('T_le_0p1ms', 'head|baseline')), f1(pdv('T_0p1_to_1ms', 'head|all')),
          f1(pdv('T_0p1_to_1ms', 'head|baseline')), f1(pdv('T_1_to_20ms', 'head|all')), f1(pdv('T_1_to_20ms', 'head|baseline')),
          thr(GA, 'F_whole_Cf1.35_N', 25.0) / 1e3, thr(GA, 'F_whole_Cf1.35_N', 40.0) / 1e3, thr(GA, 'F_whole_Cf1.35_N', 100.0) / 1e3,
          CS['mdot_limit_no_heat_g_s'][0], CS['mdot_limit_no_heat_g_s'][1],
          s2['F_min_over_corners_in_E2_to_E2p0p5_N'], s2['F_max_over_corners_in_E2_to_E2p0p5_N'], s2['n_corners_never_ge_37p16N_in_window'],
          s1['F_min_over_corners_in_E2_to_E2p0p5_N'], s1['F_max_over_corners_in_E2_to_E2p0p5_N'], s1['n_corners_never_ge_37p16N_in_window'],
          f2(ns['L1_lumped_1mm_s'][0]), f2(ns['L1_lumped_1mm_s'][1]), f2(ns655['L1_lumped_1mm_s'][0]), f2(ns655['L1_lumped_1mm_s'][1]),
          f2(ns['FD_1mm_depth_s'][0]), f2(ns['FD_1mm_depth_s'][1]),
          TB['T1_100pct_2t_8s_kg']['4.5MPa'], 100 * TB['T1_2t_share_of_flight_load'], TB['T1_100pct_max_2t_s_on_flight_tank'],
          C4['runs_lower'], C4['runs_upper_with_4deg_repeats'], C4['N2O_kg']['lower'], C4['N2O_kg']['upper'],
          DIP['125N']['liquid_at_onset_g_283_to_289p5K'][0], DIP['125N']['liquid_at_onset_g_283_to_289p5K'][1],
          DIP['250N']['liquid_at_onset_g_283_to_289p5K'][0], DIP['250N']['liquid_at_onset_g_283_to_289p5K'][1],
          DIP['500N']['liquid_at_onset_g_283_to_289p5K'][0], DIP['500N']['liquid_at_onset_g_283_to_289p5K'][1],
          m['2.50 s flow (nominal schedule)']['combustion_bound_open_g'], m[k260]['combustion_bound_open_g'],
          I8['c_design_min_m_s'], I8['c_isentropic_N2O_min_m_s'], I8['c_products_frozen_range_m_s'][0], I8['c_products_frozen_range_m_s'][1]))

# ------------------------------------------------------------------ checkpoint paragraphs
lines = text.split('\n')
cfg_old = [l for l in lines if l.startswith('**Configuration.** CAD v3.4.1 (Mechanical: coil re-route')][0]
cut = cfg_old.index('The throttle floor requirement is ENG-02')
R(cfg_old, (
    '**Configuration.** v2.4b: lead decisions to CHANGELOG line 213 (lines 186, 194, 203, 204, 205 and 213 folded; line 206 read for status: '
    'CAD v3.5.1 FROZEN as built, v3.5.2 levers with conditions; lines 207-212 read for status, 208 (1) and (3) cross-referenced in §15.15). '
    'A1 apogee target: about 210 m (line 213, founder decision; GNC sets the exact band in gnc.json v3.2). The A1 values in this report are on '
    'the 300 m records of gnc.json v3.1 and the 285 m GNC rev3 records and stay as comparators (§15.15); B1 still governs thermal and erosion '
    'sizing. Interfaces read: combustion.json v2.4a (`5237d4584bad38c4`); mechanical.json '
    'v2.1 (`e4d3e7c9df529171`; the v2.2 of line 186 (4) is not yet in the hub); gnc.json v3.1 (`4f3209323b0e0ed4`); electronics.json v3 '
    '(`38bf149f368c1d4c`, author-published, unreviewed until REV-ELEC-2) with the firmware `config.h` (`0880af5a27880a5b`), `engine_params.h` '
    '(`6b73317fcd7d07ac`) and `results/bleed_driver_v1.json` (`298b405b0621acd5`), read only; Mechanical\'s interim Pc-port files '
    '(`v351/pc/pc_line_period_v1.json` `7f5d8950516d98f2`, `pc_transducer_temperature_v1.json` `774519536f26c762`; Mechanical workdir, read '
    'only) and materials v1.4 (`18aa13a888b1e6f3`). The v2.4b analyses stay on CAD v3.4.1 and the v2.4a construct; CF-4 v2.1 is '
    're-baselined on the frozen v3.5.1 bleed path (part list MISSING in the interface). v2.4a configuration, kept: CAD v3.4.1 (Mechanical: '
    'coil re-route, FS-01 module with MV-P, bleed taps T4 and FD-01); ENGINE-BASELINE v0; REQUIREMENTS rev 2. ' + cfg_old[cut:]))
src_old = [l for l in lines if l.startswith('**Sources.** NASA CEA (RocketCEA)')][0]
R(src_old, src_old + ' v2.4b adds: Special Metals Corporation, INCONEL alloy 718, publication SMC-045 (2007), Table 2 (melting range '
               '1260-1336 C; DATASHEET, read through the web-fetch reader because the proxy refused the PDF download; the PDF is TO-ARCHIVE); '
               'Mechanical\'s materials v1.4 (IN718 properties, LITERATURE-approx); Cantera gri30 for the frozen products in the Pc port; '
               'CoolProp for propane saturation; the review REV-COMB-3 (comparator only; no reviewer code is used).')
fil_old = [l for l in lines if l.startswith('**Files.** Hub `02-combustion/`')][0]
R(fil_old, fil_old.replace('the CF-4 specification `CF-4-SPEC.md` (v2.0), the T1-T4 specification `T1-T4-REGRESSION-SPEC.md` (v2)',
                           'the CF-4 specification `CF-4-SPEC.md` (v2.1), the T1-T4 specification `T1-T4-REGRESSION-SPEC.md` (v3)')
           + ' v2.4b: data in `data/v2p4b/` (`HASHES.txt`, `sha256sum -c` format); the item answer `REVISION-RESPONSE-R3.md`; v2.4a archived in '
             '`superseded/v2p4a/`.')
tst_old = [l for l in lines if l.startswith('**Tests (digital).** Every v2.4 script asserts its input hashes.')][0]
R(tst_old, tst_old + (
    ' v2.4b: every script asserts its input hashes and the report builder checks that each data file was written by the script now in '
    '`src/`. The spectra script reproduces all 896 v2.4a cases (peaks, impulse, thrust and DLF lists to 1e-9 relative) before it extends them; '
    'the dense spectra agree with the per-case values to 4e-5 bar; an ODE cross-check (solve_ivp) agrees to 4e-4 bar. The release-hold script '
    'reproduces the rg01 set; the population counts reproduce its group means to < 6e-5. The lit-history variant at 0.21776 mm records its '
    'parent script\'s hash; the 0.2039 mm run reproduces the A1 rows of `drogue_hold_check_v2p4.json`. The interface writer keeps every v2.4a '
    'key (3227 of 3227). The A1-profile script (line 213) reproduces the three stored tank states of `cold_flow_start_lift_v2p4b.json` to '
    '1e-9 and the stored purge rates to 0.006 g/s, and checks the 300 m record hashes against the gnc.json v3.1 index. Failures kept (§13): the first runs of the lead-items script (a format error, then no N2O conductivity model in '
    'CoolProp, then a passage minimum taken at two pressures only: 201 m/s replaced by 181 m/s before use).'))
unk_old = [l for l in lines if l.startswith('**Unknowns** (§11).')][0]
R(unk_old, unk_old + (
    ' v2.4b: Cd x A x G at the start lift (CF-3) and the injector-body temperature at the relight; the gas in the Pc port passage at the FA-1 '
    'instant (composition MISSING; liquid N2O in the passage not bounded); the bleed Cd behind the 76 g cap (+-0.7 g per 1 %); which FA-1 case '
    'group governs each period domain (OI-41); the founders\' stand tank capacity (T1 at 2t = 8 s); the tank outlet geometry (OI-32); the 210 m A1 record (OI-49).'))
nxt_old = [l for l in lines if l.startswith('**Next closure** (§12).')][0]
R(nxt_old, (
    '**Next closure** (§12). Lead: OI-41 (which FA-1 case group governs each period domain; the flight Pc proof follows), OI-42 (accept 76.05 g '
    'at the 2.55 s cap or set 2.54 s). Electronics v2.11: THE start-level lift as the hold lift (OI-43), the unpurged RELIGHT guard, the '
    'over-range flag, the seat-mounted Pc unit with c_min = 181 m/s in the passage (OI-45), the firmware constant mapping (OI-46). Mechanical: '
    'the CC-2 head detail at c_min, the modal closure with periods per load path (194 (1)), TC-02 against the dense spectrum, the outlet '
    'geometry (OI-32), the IN718 datasheet archive (OI-47). GNC: R2 v2 and P4c with F_cold and the lit history at 0.21776 mm; the landing '
    'reserve against the dip onset; P2 on the v3.5.1 ledger; the 210 m A1 record (gnc.json v3.2; OI-49), after which Combustion re-runs its '
    'A1 items (§15.15). Founders: CF-3 (start-lift point with the encoder and a load cell), CF-4 v2.1, '
    'IGN-1 on the >= 100 bar abs stand channel, B-PC-1, B-PNT-1, then T1-T4 per specification v3 with a stated stand tank. Combustion: the '
    'NZ-01 prediction file before each T-series firing (OI-48), the purge at 2.7 deg (OI-35), the 1-D FA-1 run (OI-36).'))
R('- §15', '- §15') if '- §15' in text else None
R('- §11 Unknowns; §12 Open items with owners; §13 Failures and superseded evidence; §14 File index and reproduction\n',
  '- §11 Unknowns; §12 Open items with owners; §13 Failures and superseded evidence; §14 File index and reproduction\n'
  '- §15 v2.4b: lead lines 186, 194, 203-205 and 213 (decisions folded, PURGE and L*, THE start-level lift, E2 rules, classes, FA-1 items, '
  'Pc port gas, purge basis, firmware constants, outlet dip, NZ-01, A1 duration, configuration, A1 apogee target about 210 m)\n')
R('- v2.4a changes are marked "v2.4a" in place:',
  '- v2.4b changes are marked "v2.4b" in place: §0 item 13; §2.4 the dip onset and the 186 (5) wording; §2.8 the decided commit rule, the '
  'population statements and Table 2.18; §6.5 IN718; §7.3 the start-lift cold flow, CF-3 and the lit history (Table 7.3b); §7.6 the FA-1 '
  'spectra (Tables 7.6c and 7.6d); §9 the FMEA rows; §10 the test plan; §11-§15.\n- v2.4a changes are marked "v2.4a" in place:')

# ================================================================== §2.4
R(': about 9x below the 766 g minimum (DERIVED; `tank_outlet_coverage_v2p4a` in the interface).',
  '; 766 g remains at the end of the purge flow, 9.3-9.7x the 78.6-82.5 g (LEAD line 194 (5) wording; DERIVED; `tank_outlet_coverage_v2p4a` '
  'in the interface).')
dip_rows = '\n'.join('| %s | %.1f-%.1f | %.1f-%.1f | %.1f-%.1f | %.4f |' % (
    k, DIP[k]['liquid_at_onset_g'][0], DIP[k]['liquid_at_onset_g'][1], DIP[k]['liquid_at_onset_g_283_to_289p5K'][0],
    DIP[k]['liquid_at_onset_g_283_to_289p5K'][1], DIP[k]['h_c_mm'][0], DIP[k]['h_c_mm'][1], DIP[k]['mdot_ox_kg_s'])
    for k in ('62.5N', '125N', '250N', '375N', '500N'))
AFTER('Owners: Mechanical (CAD), GNC (OI-32).\n', (
    '- **v2.4b: landing-burn outlet dip onset (REV-COMB-3 R3-17; LEAD line 194 (6)).** `src/%s` (`%s`), `data/v2p4b/tank_outlet_dip_v2p4b.json` '
    '(`6c11d3c19afe983c`). Same correlation and tank geometry as above (Lubin and Springer 1967, non-swirling drain from a flat bottom, '
    'LITERATURE as recalled, N2O applicability TO-VERIFY; centre outlet, no tilt), with the oxidiser flow from the S230 map (largest over port '
    'and tank pressure) and g\' = F / m for m from GNC\'s ledger v3d dry mass 13.6706 kg to +0.6 kg (ASSUMED residuals).\n\n'
    'Table 2.4b. Liquid left in the tank when gas is first pulled into the outlet (DERIVED; no swirl, slosh, sump or baffle).\n\n'
    '| Thrust | Liquid at onset, 270-289.5 K [g] | Liquid at onset, 283-289.5 K [g] | Dip height h_c [mm] | mdot_ox [kg/s] |\n'
    '|---|---|---|---|---|\n%s\n\n'
    'GNC checks the landing usable reserve against these values instead of the ASSUMED 3 %% (60 g) residual (line 194 (6)); the outlet '
    'geometry (OI-32, Mechanical) closes it. A vortex, slosh or a tilted outlet raise the onset; a sump or an anti-vortex baffle lower it.\n'
) % (SCR['tank_outlet_dip_v2p4b.json'][0], SCR['tank_outlet_dip_v2p4b.json'][1], dip_rows))

# ================================================================== §2.8
R('11. Line 164: the minimal set (3) is the RG-01 design basis and the PTFE lining is dropped. PURGE is commanded at E0 - 2.90 s. The ECU cap '
  'is 2.5 s of flow plus the measured valve opening and closing times. The relight is never committed before a complete purge: if T_fire '
  'would cut the flow below 1.9 s, the FC delays T_fire [SUPERSEDED: withdrawn by LEAD line 175 (3); item 18]. The 0.81 s plan holds.',
  '11. Line 164: the minimal set (3) is the RG-01 design basis and the PTFE lining is dropped. PURGE is commanded at E0 - 2.90 s. The ECU cap '
  'is 2.5 s of flow plus the measured valve opening and closing times [v2.4b: both-open cap <= 2.55 s, line 203 (3); item 22]. The relight '
  'is never committed before a complete purge: if T_fire would cut the flow below 1.9 s, the FC delays T_fire [SUPERSEDED: withdrawn by LEAD '
  'line 175 (3); item 18]. The 0.81 s plan holds on the predictor path (line 181 (2)).')
R('7. PURGE is pre-scheduled: it ends before T_fire, so the 0.81 s plan holds; the integrated form is the fallback (line 153).',
  '7. PURGE is pre-scheduled: it ends before T_fire, so the 0.81 s plan holds on the predictor path (PURGE committed; line 181 (2)); the '
  'integrated form is the fallback (line 153).')
R('16. Lines 172 and 173 (v2.4a): one stand safing rule (172 (1)); the FA-1 load restated as an envelope, then fixed at 90 bar abs '
  'quasi-static at head and aft for every part, 92 / 102 bar abs for parts with periods of 0.25-1 ms, and a 1.8 kN x 4 ms thrust spike '
  '(172 (2), 173);',
  '16. Lines 172 and 173 (v2.4a): one stand safing rule (172 (1)); the FA-1 load restated as an envelope, then fixed at 90 bar abs '
  'quasi-static at head and aft for every part, 92 / 102 bar abs for parts with periods of 0.25-1 ms, and a 1.8 kN x 4 ms thrust spike '
  '(172 (2), 173) [v2.4b: restated by line 194 (1)-(2) with a period domain; item 20];')
R('18. Line 175 (3) (v2.4a), PROVISIONAL: **PURGE commits no later than the plain relight trigger - 1.7 s (T_fire delay <= 0.6 s); otherwise '
  'no purge.** Line 164\'s "the FC delays T_fire" is withdrawn. The rule\'s second branch, "the relight proceeds unpurged", is refuted by '
  'Combustion\'s check (v2.4a subsection after Table 2.15); the lead decides between no relight on that pass and a ride-through mode (OI-31).',
  '18. Line 175 (3) (v2.4a), PROVISIONAL [SUPERSEDED by line 186 (1), item 19]: PURGE commits no later than the plain relight trigger - '
  '1.7 s, otherwise no purge. Line 164\'s "the FC delays T_fire" is withdrawn. The rule\'s second branch, "the relight proceeds unpurged", '
  'was refuted by Combustion\'s check (v2.4a subsection after Table 2.15).\n'
  '19. Line 186 (1) (v2.4b): **L* = 1.3 s ADOPTED for both brackets: PURGE commits iff the lead to the plain relight trigger is >= 1.3 s; '
  'below it there is no purge and no unpurged relight on that pass** (drogue descent; vehicle loss in the FMEA). Line 203 (7) adds the ECU '
  'unpurged RELIGHT guard (v2.11). Line 204 (1): L* stays, but a commit lead below about 2.1 s is not counted as a landing (GNC rev3; '
  'nominal leads >= 2.65 s).\n'
  '20. Line 194 (1)-(2) (v2.4b): FA-1 load by period domain (90 bar abs for T <= 0.1 ms; 93 / 102 bar abs for 0.1-1 ms; the all-case '
  'spectrum or FA1S above 1 ms; the 1.8 kN x 4 ms rectangle for T <= 20 ms, the long-period thrust spectrum above). §7.6, Tables 7.6c and '
  '7.6d; OI-41.\n'
  '21. Line 194 (3) and 204 (2) (v2.4b): the "E2 + 0.22 s" hold is withdrawn; the unpurged alternative is flown by GNC only as a comparator '
  'and is NOT ADOPTED. Table 2.18 below.\n'
  '22. Line 203 (3) (v2.4b): the ECU both-open cap is <= 2.55 s; the vented-mass basis is in §15.9 (76.05 g on the bound at 2.60 s of flow; '
  'OI-42).')
R('| Sequence | PURGE command at E0 - (0.35 + 2.5 + 0.05) = E0 - 2.90 s.',
  '| Sequence | PURGE command at E0 - (0.35 + 2.5 + 0.05) = E0 - 2.90 s.')
R('Commit rule (LEAD line 175 (3), PROVISIONAL): PURGE commits no later than the plain relight trigger - 1.7 s, so that >= 1.9 s of flow fits '
  'with T_fire delayed by <= 0.6 s; otherwise no purge. The v2.4 rule "the FC delays T_fire" (line 164) is withdrawn. What follows a missed '
  'commit is open: Combustion\'s check refutes "the relight proceeds unpurged" (v2.4a subsection below) | LEAD lines 153, 160, 161, 164, 175 |',
  'Commit rule (LEAD line 186 (1), ADOPTED): PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s; below it there is no '
  'purge and no unpurged relight on that pass (ECU guard, line 203 (7)). The PROVISIONAL rule of line 175 (3) (1.7 s) and the v2.4 rule '
  '"the FC delays T_fire" (line 164) are superseded (§13). ECU both-open cap <= 2.55 s (line 203 (3); §15.9) | LEAD lines 153, 160, 161, '
  '164, 175, 186, 203 |')
R('- **Release.** E2 in the latency model is Pc > 3 bar abs held 10 ms, so the drogue-release term (Pc valid AND >= 300 kPa abs, LEAD line '
  '168 (1)) is already true at E2; the release follows within one 10 ms telemetry frame.',
  '- **Release.** E2 in the latency model is Pc > 3 bar abs held 10 ms, so the drogue-release term (Pc valid AND >= 300 kPa abs, LEAD line '
  '168 (1)) is already true at E2; the release follows within one 10 ms telemetry frame. [v2.4b, R3-12: the firmware E2 is the relative '
  'rule (§15.5). With the flow held at the start lift the lit plateau is 2.66-3.11 bar abs at 0.2039 mm, so the >= 3.0 bar term can be '
  'false and the release then waits for b7 (E2 + 0.10 s): probability moves from released-then-A3 to A3-before-release; P(success) is '
  'unchanged.]')
R('- **Verdict (SIM/DERIVED, not physical).** The provisional rule is refuted as written: an unpurged start at the late-commit point carries '
  'a hazard outside its abort model (H20).',
  '- **Verdict (SIM/DERIVED, not physical).** The provisional rule is refuted as written: an unpurged start at the late-commit point carries '
  'a hazard outside its abort model (H20). [v2.4b: line 186 (1) then adopted L* = 1.3 s with no unpurged relight below it.]')
R('- **Proposal for the lead.** No commit by the plain trigger - 1.7 s -> no relight on that pass, as A14 does for a fail-closed bleed. A '
  'ride-through mode (drogue release held on unpurged starts; torch kept on and A3 adapted through the gap) is a research option only.',
  '- **Decided (LEAD line 186 (1); v2.4b).** No commit by the plain trigger - L* (1.3 s) -> no relight on that pass, as A14 does for a '
  'fail-closed bleed. A ride-through mode (drogue release held on unpurged starts; torch kept on and A3 adapted through the gap) stays a '
  'research option only, NOT ADOPTED (line 204 (2)).')
R('and asks which applies.', 'and asks which applies. [v2.4b: line 186 (1) adopted L* = 1.3 s for both.]')
R('In the population, P(success) per record is bimodal (0 or 1): 0 in 82 % of the unlined and 77 % of the lined LO records, and in every HI '
  'record. The released-then-A3 hazard is present under both ends (population means 0.52-0.80 LO, 0.22-0.48 HI).',
  'In the population, P(success) per record is mostly 0 or 1 [v2.4b, R3-13: counted per command profile, `population_statements_v2p4b.json`]. '
  'With the flow held at the lift it is 0 in %.0f %% of the unlined and %.0f %% of the lined LO records and in every HI record; on the 2500 N/s '
  'ramp to 200 N it is 0 in %.0f %% / %.0f %% of the LO records, in every unlined HI record and in %d of 540 lined HI records (%d succeed); on '
  'the ramp to 500 N in %.0f %% / %.0f %% of the LO records and %.0f %% / %.0f %% of the HI records. The released-then-A3 hazard is present '
  'under both ends (population means at E2: 0.52-0.80 LO, 0.22-0.48 HI over the 200 N ramp and the held flow).' % (
      100 * PS['lin0.0|LO|lift_flow_held']['frac_P_success_zero'], 100 * PS['lin1.0|LO|lift_flow_held']['frac_P_success_zero'],
      100 * PS['lin0.0|LO|ramp_to_200N']['frac_P_success_zero'], 100 * PS['lin1.0|LO|ramp_to_200N']['frac_P_success_zero'],
      PS['lin1.0|HI|ramp_to_200N']['n_P_success_zero'], PS['lin1.0|HI|ramp_to_200N']['n_P_success_one'],
      100 * PS['lin0.0|LO|ramp_to_500N']['frac_P_success_zero'], 100 * PS['lin1.0|LO|ramp_to_500N']['frac_P_success_zero'],
      100 * PS['lin0.0|HI|ramp_to_500N']['frac_P_success_zero'], 100 * PS['lin1.0|HI|ramp_to_500N']['frac_P_success_zero']))
R('- **Recommendation (SIM/DERIVED; the lead decides, OI-31).** FSW L* = 1.3 s (the HI value): PURGE commits whenever the lead to the plain '
  'trigger is >= 1.3 s. Below 1.3 s, no unpurged relight on that pass (no purge -> no relight, as A14), unless GNC shows that holding the '
  'drogue release on unpurged starts to >= E2 + 0.22 s (gap arrival <= 0.193 s with the flow held at the lift, plus 0.022 s A3 detection) '
  'gains P. With that hold the light-gap-A3 sequence aborts with the drogue attached.',
  '- **Recommendation (v2.4a), now decided.** FSW L* = 1.3 s: ADOPTED by line 186 (1). Below 1.3 s, no unpurged relight on that pass (no '
  'purge -> no relight, as A14). The v2.4a hold "E2 + 0.22 s" was derived from the LO worst state only and is WITHDRAWN (line 194 (3)); the '
  'population table by command profile is Table 2.18. The unpurged alternative is NOT ADOPTED (line 204 (2)).')
G_ = ('lin0.0|LO', 'lin1.0|LO', 'lin0.0|HI', 'lin1.0|HI', 'linboth|LO', 'linboth|HI')
lab = {'lin0.0|LO': 'LO, unlined (540)', 'lin1.0|LO': 'LO, lined (540)', 'lin0.0|HI': 'HI, unlined (540)', 'lin1.0|HI': 'HI, lined (540)',
       'linboth|LO': 'LO, both (1080)', 'linboth|HI': 'HI, both (1080)'}
cell = lambda g, p: ('%.2f' % G[g][p]['hold_needed_s']) + ('' if G[g][p]['hold_within_W'] else ' (outside W)')
t218 = '\n'.join('| %s | %s | %s | %s | %.2f / %.2f / %.2f |' % (
    lab[g], cell(g, 'ramp_to_200N'), cell(g, 'ramp_to_500N'), cell(g, 'lift_flow_held'),
    G[g]['ramp_to_200N']['mean_P_success_worst_convention'], G[g]['ramp_to_500N']['mean_P_success_worst_convention'],
    G[g]['lift_flow_held']['mean_P_success_worst_convention']) for g in G_)
for g in ('lin0.0|LO', 'lin1.0|LO', 'linboth|LO', 'linboth|HI'):
    b = G[g]['ramp_to_200N']['by_hold']['0.30']; assert b['optimistic']['max'] == 0.0 and b['conservative']['max'] == 0.0
eh = I3['holds']
t218e = '\n'.join('| %s | %.2f / %.2f / %.2f |' % (lab[g], eh[g]['ramp_to_200N']['hold_from_ECU_E2_bound_s'], eh[g]['ramp_to_500N']['hold_from_ECU_E2_bound_s'],
                                                   eh[g]['lift_flow_held']['hold_from_ECU_E2_bound_s']) for g in G_)
AFTER('Per start: 0.712 (unlined) and 0.819 (lined) at the LO worst states.\n', (
    '\n**v2.4b: release hold over the record population (REV-COMB-3 R3-01; LEAD line 194 (3))** (`src/%s` `%s`; `data/v2p4b/release_hold_v2p4b.json` '
    '`a926426da0e6e436`; per-record classes `release_hold_records_v2p4b.csv` `59e7f44e44fbfeef`, 2160 records x 3 profiles; SIM on ASSUMED '
    'delays + DERIVED line states, records not re-run; bracket records, NOT probability-weighted). The v2.4a "E2 + 0.22 s" was derived from '
    'the LO worst state with the flow held; line 194 (3) withdrew it.\n\n'
    'Table 2.18. Drogue-release hold H after E2 that leaves no released-then-A3 start, by post-E2 command profile [s] (latest A3 trip over '
    'the records plus one 10 ms frame, rounded up to 10 ms; 0 and 2 deg; open and barrier element), and mean P(success) per profile (worst '
    'of the two timing conventions; independent of H).\n\n'
    '| Records | Ramp to 200 N (2500 N/s) | Ramp to 500 N | Flow held at the start lift | Mean P(success): 200 N / 500 N / held |\n'
    '|---|---|---|---|---|\n%s\n\n'
    '- At H = 0.30 s on the 200 N ramp the released-then-A3 residual is 0 in every group under both conventions; the 0.31 s values add the '
    'frame margin. W is 0.65 s, so no hold is admissible with the flow held in the LO groups.\n'
    '- The hold adds no success: it moves released-then-A3 to A3-before-release (abort with the drogue attached). Any P gain comes only from '
    'records that light without a gap trip; the P cost of the longer hold is GNC\'s.\n'
    '- With Pc invalid the command is held at the start level while the drogue is attached (line 186 (2)), so the alternative is not '
    'admissible there (line 194 (3)).\n'
    '- ECU E2 (relative rule) against the model E2 (Pc > 3 bar abs for 10 ms): the ECU E2 comes at most %.1f ms earlier (§15.5). Holds counted '
    'from the ECU E2 (bound, rounded up to 10 ms; 200 N / 500 N / held):\n\n'
    '| Records | Hold from the ECU E2 [s] |\n|---|---|\n%s\n\n'
    '- Status: the unpurged alternative is NOT ADOPTED (line 204 (2)); these are comparator data for GNC P4c, with the per-record classes for '
    'all three profiles (§15.6).\n') % (SCR['release_hold_v2p4b.json'][0], SCR['release_hold_v2p4b.json'][1], t218, 1e3 * I3['shift_bound_s'], t218e))

# ================================================================== §6.5 lip melt (IN718)
R('**Lip melt if the leak impinges** (DERIVED; 316L melting at 1400 C; deposition 5-20 % ASSUMED; adiabatic outer face and no latent heat, '
  'so the times are short and conservative):',
  '**Lip melt if the leak impinges** (v2.4b: TC-09, which carries the J1 lip, is Inconel 718 since LEAD lines 177 (1)/178; DERIVED; melt '
  'onset at the IN718 solidus 1260 C, liquidus 1336 C, DATASHEET Special Metals SMC-045 Table 2, read through the web-fetch reader, PDF '
  'TO-ARCHIVE; properties from Mechanical\'s materials v1.4, LITERATURE-approx, extrapolated above 700 C ASSUMED; deposition 5-20 %% ASSUMED; '
  'adiabatic outer face and no latent heat, so the times are short and conservative; `src/%s` `%s`, `data/v2p4b/nozzle_lip_melt_in718_v2p4b.json` '
  '`23b85b7febb90c60`):' % SCR['nozzle_lip_melt_in718_v2p4b.json'])
R('| Joint and start temperature | Lumped, 1 mm of lip [s] | Finite difference, 1 mm depth [s] |\n|---|---|---|\n'
  '| J1, start 342 C (B1 p99, the worst start) | 1.07-5.70 | 6.63-40.26 |\n'
  '| J1b (0.5 mm graphite), B1 start 223 C | 1.19-6.34 | 7.39-44.33 |\n',
  '| Joint, material and start temperature | Lumped, 1 mm of lip [s] | Finite difference, 1 mm depth [s] | Finite difference, surface [s] |\n'
  '|---|---|---|---|\n'
  '| J1, IN718, start 342 C (B1 p99, the v2.4 worst start) | %s-%s | %s-%s | %s-%s |\n'
  '| J1, IN718, start 295 C (Mechanical: J1 lip in flight) | %s-%s | %s-%s | %s-%s |\n'
  '| J1, IN718, start 655 C (TC-09 part maximum, RM1-06; upper start) | %s-%s | %s-%s | %s-%s |\n'
  '| Superseded (v2.4): J1, 316L at 1400 C, start 342 C | 1.07-5.70 | 6.63-40.26 | - |\n'
  '| Superseded (v2.4): J1b (0.5 mm graphite), 316L, B1 start 223 C | 1.19-6.34 | 7.39-44.33 | - |\n\n'
  'With Mechanical\'s v1.4 property tables the IN718 lumped bound is about 3 %% longer than the 316L one and the 1 mm FD times 16-21 %% '
  'shorter. J1b is not recomputed. The 1.8 mm TC-09 barrel wall of the v3.5.2 lever (line 206 (2)(a)) does not change the lumped reading; '
  'the FD readings use a 6 mm slab and shorten if the lip section thins (re-run on the v3.5.2 geometry).\n' % tuple(
      f2(x) for row in (ns, ns295, ns655) for k in ('L1_lumped_1mm_s', 'FD_1mm_depth_s', 'FD_surface_s') for x in row[k]))

# ================================================================== §7.3 R2 and cold flow
R('otherwise hold the drogue and command ABORT at t_E2 + 0.8 s; a PROPOSAL to be flown)',
  'otherwise hold the drogue and command ABORT at t_E2 + 0.5 s (pcf_tmax 0.5 s, line 181 (4); the 0.8 s of the v2.4a text is superseded); '
  'with the command held at the start level while the drogue is attached, line 186 (2))')
R('unless the heat pick-up exceeds about 2.8 kW.',
  'unless the heat pick-up exceeds about 2.8 kW [v2.4b, line 194 (4): heat added at tank pressure, i.e. the injector-body and feed soak-back '
  'temperature at the relight].')
R('- **PROPOSAL (for GNC R2 v2 and the lead; OI-38).** While the drogue is attached and Pc is invalid, hold the open-loop command at the '
  'start level, or cap the lift at the start-level lift, until R2 confirms;',
  '- **ADOPTED in design (LEAD line 186 (2); OI-38; v2.4b).** While the drogue is attached and Pc is invalid, the ECU holds the open-loop '
  'command at the start level (THE start-level lift, §15.3) until release;')
R('Hypothesis: the hold keeps the dead-engine apparent thrust within the margin while a lit engine still releases (62.5 N x pcf_k 0.875 = '
  '54.7 N; GNC\'s release estimate >= 48.4 N).',
  'Hypothesis: the hold keeps the dead-engine apparent thrust within the margin while a lit engine still releases (lit side: the grain_q1d '
  'start-level history, Table 7.3b; the v2.4a figure 62.5 N x pcf_k 0.875 = 54.7 N is superseded, lines 194 (4) and 204 (4)).')
lit_row = lambda s, e: '| %s | %.1f-%.1f ms | %.1f-%.1f N | %d of 72 | %.3f s | %.1f-%.1f N | %.1f / %.1f / %.1f N |' % (
    s, 1e3 * e['summary']['E2_s_range'][0], 1e3 * e['summary']['E2_s_range'][1], e['summary']['F_min_over_corners_in_E2_to_E2p0p5_N'],
    e['summary']['F_max_over_corners_in_E2_to_E2p0p5_N'], e['summary']['n_corners_never_ge_37p16N_in_window'],
    e['summary']['latest_first_t_ge_37p16N_after_E2_s'], e['summary']['F_at_1s_range_N'][0], e['summary']['F_at_1s_range_N'][1],
    e['envelope']['F_median_N'][0], e['envelope']['F_median_N'][3], e['envelope']['F_median_N'][-1])
assert L2['envelope']['t_s'][0] == 0.03 and L2['envelope']['t_s'][3] == 0.2 and L2['envelope']['t_s'][-1] == 1.0
lsc = SCR['start_level_lit_thrust_0p21776mm_v2p4b.json']
blk73 = (
    '\n**v2.4b: start-lift cold flow, the CF-3 acceptance and the start-level lit history (REV-COMB-3 R3-05, R3-14; LEAD lines 194 (4) and '
    '203 (7))** (`src/%s` `%s`, `data/v2p4b/cold_flow_start_lift_v2p4b.json` `28ce48092f33da1b`; `src/%s` `%s` and `src/%s` `%s`, '
    '`data/v2p4b/start_level_lit_thrust_v2p4b.json`/`.csv` and `start_level_lit_thrust_0p21776mm_v2p4b.json`/`.csv`).\n\n'
    '- **CONDITIONAL margin.** The start-level bound (%.1f-%.1f N over 283.15-289.5 K; %.2f N at THE start-level lift 0.21776 mm, A1 state) '
    'rests on Cd x A x G at the start lift: the 16.31 N margin is %.2f-%.2f x the bound. A spray-type (SPI) flux at the same lift gives '
    '%.1f-%.1f N, above the margin. The margin is CONDITIONAL until CF-3 measures it.\n'
    '- **CF-3 start-lift point (acceptance, line 194 (4)).** At the commanded start-level lift with the encoder lift recorded: mdot and the '
    'load-cell thrust (cold chamber). Accept if F <= 16.31 N minus the heat allowance, or mdot <= %.1f-%.1f g/s (the flow that reaches '
    '16.31 N with no heat). A failure returns the hold level and the W10 rule to the lead.\n'
    '- **Heat location (R3-14).** The %.1f-%.1f kW (%.0f-%.0f kJ/kg) threshold applies to heat added at tank pressure, before the throttling: '
    'the TO-VERIFY is the injector-body and feed soak-back temperature at the relight (a thermocouple on the injector body in the T series; '
    'Mechanical\'s soak-back model). Heat added in the chamber at 1.03-1.3 bar converts poorly to thrust.\n'
    '- **FLAMEOUT_OPT (Electronics v2.10).** %s\n\n'
    'Table 7.3b. Start-level lit thrust (grain_q1d v2, A1 relight state 286.7 K, 1.16 kg, port 32.2 mm; lift held from the light; 72 corners '
    'of Cd, a, n, r_i and eta; SIM on ASSUMED laws and bands, quasi-steady, roughness not modelled). Time from the light; 37.16 N is the R2 '
    'threshold.\n\n'
    '| Lift | E2 after the light | F, E2 to E2 + 0.5 s | Corners below 37.16 N throughout | Latest first F >= 37.16 N after E2 | F at 1 s | '
    'Median F at 0.03 / 0.2 / 1.0 s |\n|---|---|---|---|---|---|---|\n%s\n%s\n\n'
    'GNC\'s R2 v2 and P4c use F_cold (`cold_flow_thrust_v2p4a.csv`) plus this history at 0.21776 mm, not 62.5 N x pcf_k (line 194 (4); '
    'SUPERSEDED in line 204 (4)). The 0.2039 mm row is the 20 C row and a low-lift sensitivity. IGN-1 and the T series with a load cell '
    'measure it.\n') % (
    SCR['cold_flow_start_lift_v2p4b.json'][0], SCR['cold_flow_start_lift_v2p4b.json'][1], SCR['start_level_lit_thrust_v2p4b.json'][0],
    SCR['start_level_lit_thrust_v2p4b.json'][1], lsc[0], lsc[1], CS['F_bound_N'][0], CS['F_bound_N'][1], I2['cold_flow_bound_at_hs']['A1_relight_N'],
    CS['factor_on_CdAG'][0], CS['factor_on_CdAG'][1], CS['F_bound_SPI_N'][0], CS['F_bound_SPI_N'][1],
    CS['mdot_limit_no_heat_g_s'][0], CS['mdot_limit_no_heat_g_s'][1], CS['heat_to_16p31N_kW'][0], CS['heat_to_16p31N_kW'][1],
    CS['heat_to_16p31N_kJ_kg'][0], CS['heat_to_16p31N_kJ_kg'][1], I4['FLAMEOUT_OPT_cold_flow_text'],
    lit_row('0.21776 mm (THE start-level lift, A1 state)', L2), lit_row('0.2039 mm (20 C row; sensitivity)', L1))
anchor73 = [l for l in text.split('\n') if l.startswith('- **ADOPTED in design (LEAD line 186 (2); OI-38; v2.4b).**')][0] + '\n'
AFTER(anchor73, blk73)

# ================================================================== §7.4 sequence and transducers
R('  - Pc and P_torch 070BG (ENG-09 >= 70 bar; RC-13 d); P_feed and P_tank 170BG;',
  '  - Pc: flight unit RESELECTED by Electronics (LEAD line 205): seat-mounted miniature, body within 12 mm x 30 mm, front dead volume '
  '<= 20 mm3, proof >= 112 bar abs (lead basis 1.1 x 102; 132 bar abs on Combustion\'s all-case 0.1-1 ms value, OI-41), range covering '
  'the 45 bar MEOP with the 30 bar abort resolvable, >= 120 C; passage gas c >= 181 m/s if free of liquid N2O (§15.8). P_torch 070BG '
  '(ENG-09 >= 70 bar; RC-13 d); P_feed and P_tank 170BG;')
R('**PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge** (LEAD line 175 (3), PROVISIONAL; T_fire delay '
  '<= 0.6 s; line 164\'s "the FC delays T_fire" is withdrawn). What follows a missed commit is for the lead: line 175 (3) says the relight '
  'proceeds unpurged; Combustion\'s check refutes that branch and proposes no relight on that pass (§2.8, v2.4a; H20).',
  '**PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s; otherwise no purge and no unpurged relight on that pass** '
  '(LEAD line 186 (1); ECU unpurged RELIGHT guard, line 203 (7); a commit lead below about 2.1 s is not counted as a landing, line 204 (1)). '
  'ECU both-open cap <= 2.55 s (line 203 (3); §15.9). The PROVISIONAL 1.7 s rule of line 175 (3) is superseded (§13).')
R('4. **E1:** the pintle is commanded to the ignition lift: 0.2039 mm, the v2.8 default (37.1 g/s cold flow at 20 C, 35.0 g/s at the A1 '
  'relight state). CF-3 calibrates a lift-against-T_tank table that keeps the flow <= 37.1 g/s at 20 C and <= 37.4 g/s at the A1 state '
  '(LEAD). The lift is held until E2 (ENG-04 ignition-lift hold).',
  '4. **E1:** the pintle is commanded to THE start-level lift h_s(T_tank at E0) (v2.4b definition, §15.3; LEAD line 203 (7)): the row of '
  'the ignition-lift table, 0.2039 mm at 20 C (37.1 g/s cold flow) and 0.21776 mm at the A1 relight state (37.4 g/s; 0.2039 mm gives '
  '35.0 g/s there). CF-3 calibrates the table (<= 37.1 g/s at 20 C, <= 37.4 g/s at the A1 state; LEAD) and measures at the commanded lift '
  'with the encoder recorded. The lift is held until E2 (ENG-04 ignition-lift hold) and, with Pc invalid and the drogue attached, until '
  'release (line 186 (2)).')
R('No commit or no flow means no purge (LEAD line 175 (3), PROVISIONAL). Combustion proposes no relight on that pass (H20; OI-31); the lead '
  'decides. If the relight proceeds unpurged, the line state is "PURGE NOT RUN"',
  'No commit or no flow means no purge and no relight on that pass (LEAD line 186 (1); ECU guard, line 203 (7)). For the record (H20): an '
  'unpurged start would see the line state "PURGE NOT RUN"')
R('- Unchanged: software Pc cap 25 bar; ECU over-pressure abort at 31.47 bar g (OVP comparator, A4 in §7.4); Pc transducer range >= 70 bar.',
  '- Unchanged: software Pc cap 25 bar; ECU over-pressure abort at 31.47 bar g (OVP comparator, A4 in §7.4). Changed (v2.4b): the flight Pc '
  'transducer is reselected (LEAD line 205): proof >= 112 bar abs, range covering the 45 bar MEOP with the 30 bar abort resolvable, '
  'over-range bit and above-full-scale flag (line 203 (1)(a)); the 0-70 bar class stays for P_torch.')

# ================================================================== §7.6 FA-1 load and spectra
R('- **Load (LEAD line 173).** FA-1 structural load: 90 bar abs quasi-static at head and aft for every part; parts with natural periods of '
  '0.25-1 ms also at 92 bar abs (design: baseline rounded with DLF and the +3 % fuel basis) and 102 bar abs (sensitivity: upper bracket, '
  'sharp, DLF); thrust spike 1.8 kN x 4 ms, confirmed bounding.',
  '- **Load (LEAD line 173, restated by line 194 (1)-(2); v2.4b).** FA-1 equivalent static pressure at head and aft: 90 bar abs quasi-static '
  'for load paths with T <= 0.1 ms; for 0.1 < T <= 1 ms yield at 93 bar abs (design; replaces the 92 bar of line 173, R3-04) and ultimate '
  'at 102 bar abs (sensitivity); for T > 1 ms the all-case spectrum value at the part\'s period, or Mechanical\'s FA1S step case (DLF 2.0, '
  'about 151 bar abs), the design case for every pressure-loaded path until Mechanical\'s modal closure lists each with its period. Thrust: '
  'the 1.8 kN x 4 ms rectangle for T <= 20 ms; above 20 ms the FA-1 long-period thrust spectrum (Table 7.6d). The v2.4a text of this item '
  'follows for the record: 90 bar abs for every part; 0.25-1 ms parts also at 92 bar abs (baseline rounded with DLF and the +3 % fuel basis) '
  'and 102 bar abs; thrust spike 1.8 kN x 4 ms.')
R('The 92 bar design value (89.0 x 1.03) becomes about 92.2 bar with the 4 % form (92.9 bar at 8 %); the 102 bar sensitivity covers it.',
  'The 92 bar design value (89.0 x 1.03) becomes about 92.2 bar with the 4 % form (92.9 bar at 8 %); the 102 bar sensitivity covers it. '
  '[v2.4b: line 194 (1) replaced 92 by 93 bar abs (R3-04).]')
pd_row = lambda lab_, b, rule: '| %s | %s | %s (%s ms) | %s | %s |' % (
    lab_, f1(pdv(b, 'head|baseline')), f1(pdv(b, 'head|all')), PD[b]['head|all']['period_ms'], f1(pdv(b, 'aft|baseline')), f1(pdv(b, 'aft|all')))
t76c = '\n'.join([pd_row('T <= 0.1 ms (90 quasi-static)', 'T_le_0p1ms', ''), pd_row('0.1 < T <= 1 ms (93 yield / 102 ultimate)', 'T_0p1_to_1ms', ''),
                  pd_row('1 < T <= 20 ms (spectrum, or FA1S about 151)', 'T_1_to_20ms', ''), pd_row('20 < T <= 50 ms', 'T_20_to_50ms', '')])
t76d_rows = []
for lab_, grp, k in (('All cases, whole history, Cf 1.35', GA, 'F_whole_Cf1.35_N'), ('Baseline, whole history, Cf 1.35', GB, 'F_whole_Cf1.35_N'),
                     ('All cases, whole history, QS x 0.975', GA, 'F_whole_QSx0.975_N'), ('All cases, above steady, Cf 1.35', GA, 'F_above_Cf1.35_N')):
    t76d_rows.append('| %s | %s |' % (lab_, ' | '.join('%.0f' % thr(grp, k, t) for t in (4.0, 20.0, 25.0, 40.0, 100.0, 200.0))))
TH = DN['thrust']; dec = DN['decomposition_90p7_vs_89p0']
fsp, fsd = SCR['fa1_spectra_v2p4b.json'], SCR['fa1_spectra_dense_v2p4b.json']
blk76 = (
    '\n**v2.4b: FA-1 equivalent-pressure and thrust spectra (REV-COMB-3 R3-02, R3-03, R3-04; LEAD line 194 (1)-(2))** (`src/%s` `%s`, '
    '`src/%s` `%s`; `data/v2p4b/fa1_spectra_v2p4b.json` `372b8078d7a90e75` per case, `fa1_spectra_dense_v2p4b.json` `7468996959538d0f`, the '
    'CSV tables `fa1_pressure_spectra*_v2p4b.csv` and `fa1_thrust_spectra*_v2p4b.csv`, and the solver histories '
    '`fa1_histories_solver_v2p4b.npz` `399bf43d1c09de24`). The script first reproduces all 896 v2.4a cases (peaks, 25 ms impulse, thrust '
    'peaks, the v2.4a DLF lists) to 1e-9 relative. Each case\'s head and aft histories at the solver step (0.05 ms), from the light to '
    'max(t_f, tau_pool) + 60 ms (61-129 ms), drive an undamped SDOF from rest; P_eq(T) = p_amb + max k x for the gauge history; the published '
    'value is the larger of the conventions (b) max(P - p_amb, 0) and (c) P - p_amb (they differ only in the vapour-once cases); 2 %% and '
    '5 %% damping are in the JSON. Periods 0.02-50 ms (0.005 ms steps below 1 ms); thrust 0.5-200 ms.\n\n'
    'Table 7.6c. Maximum equivalent static pressure by period domain [bar abs] (SIM construct + DERIVED SDOF; undamped). Baseline: vapour '
    'once, rounded entrance (Cd 1.0), O/F 4-12 (168 cases); all cases: 896 (as-written start, sharp entrance and O/F 3-3.5 included).\n\n'
    '| Domain (LEAD 194 (1) value) | Head, baseline | Head, all cases (period) | Aft, baseline | Aft, all cases |\n|---|---|---|---|---|\n%s\n\n'
    '- **Contradiction for the lead (OI-41).** For T <= 0.1 ms the all-case head value (%s bar abs) exceeds the 90 bar abs quasi-static value; '
    'the baseline (%s) does not. For 0.1-1 ms the baseline (%s) is at the 102 bar abs ultimate and the all-case value (%s) exceeds yield 93 '
    'and ultimate 102. In the ENG-TC-02 band (0.272-0.385 ms, Mechanical\'s modal value) the head value is %s bar abs baseline and %s all '
    'cases undamped (%s at 2 %%, %s at 5 %% damping). FA1S (about 151 bar abs) bounds every period (largest %s bar abs at %s ms). The '
    'line-194 (1) values came from the coarse v2.4a grid; which case group governs each domain is the lead\'s decision, and the flight Pc proof '
    '(1.1 x 102 = 112 bar abs, line 205) follows from it.\n'
    '- **R3-04 (90.7 against 89.0 bar).** Baseline case, 0.25 ms: %.2f bar (v2.4a, sampled at 0.05 ms in a 30 ms window, convention b), '
    '%.2f (continuous solver history, b), %.2f (c), %.2f at a 0.0125 ms solver step; the reviewer\'s %.2f is reproduced to 0.15 bar. The '
    'difference is sampling and convention, not physics.\n'
    '- **Histories (relay of line 203, item 5).** Published at the solver step to %s-%s ms per case; after 25 ms the head stays at %s-%s bar abs '
    '(pool plateau ASSUMED). Use the construct to about the end of its pool term; beyond it the start-level lit history applies (Table 7.3b). '
    'Near 6 ms (the 0.30 m sense-line period, deleted by line 205) the head value is %s bar abs baseline and %s all cases.\n'
    '- **Limits.** Lumped three-node construct on ASSUMED inputs (fuel inventory, O/F, burn time, pool plateau); no structure model; no 1-D '
    'waves (OI-36). Not physical evidence: IGN-1 on the stand dynamic channel measures FA-1.\n\n'
    'Table 7.6d. FA-1 thrust equivalent force [N] by SDOF period (DERIVED; Cf 1.35 ASSUMED band, or quasi-steady x 0.975).\n\n'
    '| Reading | 4 ms | 20 ms | 25 ms | 40 ms | 100 ms | 200 ms |\n|---|---|---|---|---|---|---|\n%s\n\n'
    'The rectangle 1.8 kN x 4 ms (SDOF maximum 3.6 kN at short periods) bounds FA-1 for T <= 20 ms in all four readings (smallest ratio %.2f); '
    'FA-1 exceeds it from %s-%s ms. Line 194 (2) makes the long-period spectrum the load for T > 20 ms (vehicle modes, equipment on '
    'isolators, tank mounts); the lead carries it into ICD-AIRFRAME v2.1. The reviewer\'s values (1.76 kN at 25 ms, 1.45 kN at 40 ms, '
    '1.04 kN at 100 ms) are within 3 %%.\n') % (
    fsp[0], fsp[1], fsd[0], fsd[1], t76c,
    f1(pdv('T_le_0p1ms', 'head|all')), f1(pdv('T_le_0p1ms', 'head|baseline')), f1(pdv('T_0p1_to_1ms', 'head|baseline')),
    f1(pdv('T_0p1_to_1ms', 'head|all')), f1(tc02['max_in_band_baseline']['value_bar']), f1(tc02['max_in_band_all']['value_bar']),
    f1(tc02['max_in_band_governing_cases_zeta0.02_bar']), f1(tc02['max_in_band_governing_cases_zeta0.05_bar']),
    f1(pdv('T_1_to_20ms', 'head|all')), PD['T_1_to_20ms']['head|all']['period_ms'],
    dec['v2p4a_published_sampled_0p05ms_30ms_window_b'], dec['continuous_0p05ms_solver_b'], dec['continuous_0p05ms_solver_c'],
    dec['continuous_0p0125ms_solver_b'], dec['reviewer_r3_fa1_check'],
    I5['histories']['t_end_ms'][0], I5['histories']['t_end_ms'][1], I5['histories']['max_head_after_25ms_bar'][0],
    I5['histories']['max_head_after_25ms_bar'][1], f1(I5['head_spectrum_near_6ms']['values']['baseline']['at_6p0ms_bar']),
    f1(I5['head_spectrum_near_6ms']['values']['all_cases']['at_6p0ms_bar']), '\n'.join(t76d_rows),
    min(TH['min_rectangle_over_FA1_T_le_20ms'].values()), min(TH['first_period_ms_FA1_exceeds_rectangle'].values()),
    max(TH['first_period_ms_FA1_exceeds_rectangle'].values()))
anchor76 = [l for l in text.split('\n') if l.startswith('- **Load (LEAD line 173, restated by line 194 (1)-(2); v2.4b).**')][0] + '\n'
AFTER(anchor76, blk76)

# ================================================================== relight timing (§7.7) and §9
R('- Flight planning value **0.81 s** = torch gate 0.16 + W 0.65. It is the latest Pc confirmation of any light, by construction.',
  '- Flight planning value **0.81 s** = torch gate 0.16 + W 0.65. It is the latest Pc confirmation of any light, by construction (on the '
  'predictor path; line 181 (2)).')
R('the 0.81 s plan from T_fire and W 0.65 s stay (E0 -> E2 max 0.626 s on the worst purged state).',
  'the 0.81 s plan from T_fire and W 0.65 s stay on the predictor path (line 181 (2)) (E0 -> E2 max 0.626 s on the worst purged state).')
R('PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge (LEAD line 175 (3), PROVISIONAL; it withdraws line '
  '164\'s "the FC delays T_fire"). In GNC rev2 the T_fire delay is <= 0.6 s and costs no measurable P; the decided-path height cost is '
  '<= 3.04 m (line 174, SIM). After a missed commit see H20 (§2.8, v2.4a).',
  'PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s (LEAD line 186 (1)); otherwise no purge and no relight on that '
  'pass. The v2.4a statement that the T_fire delay is <= 0.6 s and costs no measurable P is withdrawn (line 181 (2)); GNC rev3: a commit '
  'lead below about 2.1 s is not counted as a landing (line 204 (1)). The decided-path height cost is <= 3.04 m (line 174, SIM).')
R('No commit by the plain trigger - 1.7 s -> no purge (LEAD line 175 (3), PROVISIONAL; the T_fire delay of line 164 is withdrawn). '
  'Proposal: no relight on that pass (H20) |',
  'No commit by the plain trigger - L* (1.3 s) -> no purge and no relight on that pass (LEAD line 186 (1); ECU guard, line 203 (7)) |')
R('An unsealed joint leaks 0.83-1.10 % of the engine flow; the 316L lip could melt in 1.07-5.70 s (lumped bound) (§6.5)',
  'An unsealed joint leaks 0.83-1.10 %% of the engine flow; the Inconel 718 lip (TC-09) could melt in %s-%s s (lumped bound from 342 C; '
  '%s-%s s from 655 C) (§6.5)' % (f2(ns['L1_lumped_1mm_s'][0]), f2(ns['L1_lumped_1mm_s'][1]), f2(ns655['L1_lumped_1mm_s'][0]),
                                 f2(ns655['L1_lumped_1mm_s'][1])))
R('released, then A3, in 0.712 of starts (lined 0.819; population means 0.22-0.58)',
  'released, then A3, in 0.712 of starts (lined 0.819; population means 0.22-0.58 on the 200 N ramp, up to 0.80 with the flow held; '
  'Table 2.17)')
R('| Proposal: no relight on that pass (as A14). Research option: ride-through (release held on unpurged starts; torch kept on; A3 '
  'adapted) on CF-4 O-3 and IGN-1 evidence. The lead decides (OI-31). Line 181 (2): worst-state P(success) 0 under LO and under HI; '
  'Combustion recommends L* = 1.3 s (Table 2.17) |',
  '| Decided: no relight on that pass below L* = 1.3 s (LEAD line 186 (1); ECU guard, line 203 (7)). The ride-through and the unpurged '
  'alternative are NOT ADOPTED (line 204 (2)); the classes stay as data (Table 2.18). Worst-state P(success) 0 under LO and under HI '
  '(Table 2.17) |')
R('| FC timing | PURGE commits no later than the plain trigger - 1.7 s, so >= 1.9 s of flow fits with T_fire delayed by <= 0.6 s; otherwise '
  'no purge (LEAD line 175 (3), PROVISIONAL; the T_fire delay of line 164 is withdrawn) |',
  '| FC timing | PURGE commits iff the lead to the plain trigger is >= L* = 1.3 s; otherwise no purge and no relight on that pass (LEAD line '
  '186 (1)); a commit lead below about 2.1 s is not counted as a landing (line 204 (1)) |')
R('| B-6 (v2.4a) | Unpurged relight (no commit by the plain trigger - 1.7 s, or no flow) |',
  '| B-6 (v2.4a) | Unpurged relight (no commit by the plain trigger - L*, or no flow) |')
R('| Proposal: no relight on that pass (OI-31); the lead decides. L* = 1.3 s recommended (line 181 (2), Table 2.17) |',
  '| Excluded by design: no relight on that pass (LEAD line 186 (1)); ECU unpurged RELIGHT guard (line 203 (7)); the unpurged alternative '
  'NOT ADOPTED (line 204 (2)) |')
R('| PROPOSAL: command hold at the start level while the drogue is attached; GNC re-flies R2 with the cold-flow term (OI-38) |',
  '| ADOPTED: command hold at the start level while the drogue is attached (LEAD line 186 (2)); margin CONDITIONAL on Cd x A x G at the '
  'start lift (line 194 (4)); CF-3 start-lift point; FLAMEOUT_OPT (Electronics v2.10); GNC re-flies R2 v2 with F_cold and the lit history '
  '(OI-38) |')
R('J-FWD A4-80 (yield MS +0.29 at 92 bar, ultimate +0.61 at 102 bar)',
  'J-FWD A4-80 (yield MS +0.29 at 92 bar, about +0.28 at 93 bar per line 194 (1), ultimate +0.61 at 102 bar)')

# ================================================================== §10
R('### 10.3 CF-4 summary (full text in `CF-4-SPEC.md` v2.0)', '### 10.3 CF-4 summary (full text in `CF-4-SPEC.md` v2.1, v2.4b)')
R('### 10.4 Regression-rate measurement at T1-T4 and the law form (RG-03; specification v2)',
  '### 10.4 Regression-rate measurement at T1-T4 and the law form (RG-03; specification v3, v2.4b)')
R('- **T1:** LIGHT_SPIKE logging at every start; the nozzle-joint N2 leak check at 67.5 bar before and after (H19); lip thermocouples (§6.5); '
  'Pc transducer >= 70 bar.',
  '- **T1:** LIGHT_SPIKE logging at every start; the nozzle-joint N2 leak check at 67.5 bar before and after (H19); lip thermocouples (§6.5); '
  'the stand dynamic Pc channel >= 100 bar abs with proof >= 112 bar abs flush-mounted (>= 132 bar abs for a 0.1-1 ms path; > 1 ms not '
  'acceptable) (LEAD line 194 (7); T1-T4 v3).')
R('CF-3 adds a thrust load cell and logs the cold-flow thrust at the start-level (about 0.22 mm), 200 N and 500 N lifts (cold chamber).',
  'CF-3 adds a thrust load cell and logs the cold-flow thrust at THE start-level lift (h_s, 0.21776 mm at the A1 state; encoder lift '
  'recorded), 200 N and 500 N lifts (cold chamber); acceptance at the start lift: F <= 16.31 N minus the heat allowance, or mdot <= '
  '52.6-56.3 g/s (LEAD line 194 (4)).')
AFTER('### 10.1 Cleaning, drying and catch volumes (RC-14)', '')
R('\n### 10.1 Cleaning, drying and catch volumes (RC-14)', (
    '\n**v2.4b amendments to the test plan** (REV-COMB-3 R3-06, R3-07, R3-08, R3-10; LEAD line 194 (4), (7), (8)).\n'
    '- **Stand dynamic Pc channel (R3-10):** range >= 100 bar abs (FA-1 construct head peak up to 88.0 bar abs); proof >= 1.1 x the all-case '
    'FA-1 spectrum at the transducer path period: flush mount >= 103 bar abs, carried as the 112 bar abs class of the line-205 flight unit; a '
    '0.1-1 ms path >= 132 bar abs; a path period > 1 ms is not acceptable; the passage free of liquid N2O (§15.8). Founder instrumentation '
    'item, TO-QUOTE delivered to Sønderborg DK-6400.\n'
    '- **CF-3 start-lift point (R3-05):** at THE start-level lift with the encoder lift recorded, mdot and load-cell thrust; acceptance as in '
    '§7.3 (v2.4b).\n'
    '- **T1-T4 v3 (`%s`):** the oxidiser-flux law is shown only if |S - S_ox| <= 1.645 sigma (two-sided); S below that is "neither shown": '
    'the default gate stays and Combustion re-evaluates the burn limit on the measured axial profile. Red lines and abort criteria; validity '
    'rules for short firings; the char-removal procedure; counts and N2O: T1 at 2t = 8 s uses %.3f kg (%.0f %% of a 2.0 kg flight load); with a '
    'flight-size tank 2t <= %.1f s; the stand tank is MISSING (founders state it or shorten t); series N1 / N2 / N4 / N8: %.1f / %.1f / %.1f / '
    '%.1f kg of N2O with a 10 %% allowance (DERIVED; TO-QUOTE, Sønderborg DK-6400; no price is assumed).\n'
    '- **CF-4 v2.1 (`%s`):** re-baselined on the frozen v3.5.1 bleed path (part list MISSING in mechanical.json v2.1); run red lines and abort '
    'criteria; the IS-1/IS-2 preparation; the continuous-liquid probe threshold (one probe response at the start-level lift flow passes '
    '%.3f cm3 of void); P1 in volume form (18.86 cm3 of lift flow: %.3f s at 0.21776 mm, %.3f s at 0.2039 mm); %d / %d / %d runs, %.0f g of '
    'N2O per run, %.1f / %.1f / %.1f kg (%.1f / %.1f / %.1f kg with the allowance; optional runs and the tank heel excluded).\n') % (
    H_T, TB['T1_100pct_2t_8s_kg']['4.5MPa'], 100 * TB['T1_2t_share_of_flight_load'], TB['T1_100pct_max_2t_s_on_flight_tank'],
    TB['series']['N1']['N2O_kg']['4.5MPa'], TB['series']['N2']['N2O_kg']['4.5MPa'], TB['series']['N4']['N2O_kg']['4.5MPa'],
    TB['series']['N8']['N2O_kg']['4.5MPa'], H_C, C4['probe_dropout']['dropout_volume_cm3_per_response'],
    pp['0.21776mm']['P1_after_lift_s'], pp['0.20390mm']['P1_after_lift_s'], C4['runs_lower'], C4['runs_base_5_per_state_and_attitude'],
    C4['runs_upper_with_4deg_repeats'], C4['N2O_per_run_g'], C4['N2O_kg']['lower'], C4['N2O_kg']['base'], C4['N2O_kg']['upper'],
    C4['N2O_kg_with_allowance']['lower'], C4['N2O_kg_with_allowance']['base'], C4['N2O_kg_with_allowance']['upper'])
    + '\n### 10.1 Cleaning, drying and catch volumes (RC-14)')

# ================================================================== §11 unknowns
R('31. The cold-flow thrust after a flame-out, cold and with a hot chamber, grain and nozzle (heat pick-up MISSING): CF-3 with a load cell; '
  'a post-burn N2O pulse in the T series (§10, v2.4a).',
  '31. The cold-flow thrust after a flame-out, cold and with a hot chamber, grain and nozzle (the injector-body and feed soak-back '
  'temperature at the relight MISSING, line 194 (4)): CF-3 with a load cell at the start lift; a post-burn N2O pulse in the T series (§10).')
AFTER('32. Which end of the wall heat-transfer bracket (LO or HI) governs the coast flashing in the segment: CF-4 optional generation runs, T4.\n',
      '33. v2.4b: Cd x A x G at THE start-level lift (CF-3 start-lift point).\n'
      '34. v2.4b: the gas in the Pc port passage at the FA-1 instant (composition MISSING; whether liquid N2O can reach the passage): IGN-1 and '
      'B-PC-1 with the port ring-down recorded (§15.8).\n'
      '35. v2.4b: the bleed restrictor Cd behind the 76 g cap (+-0.7 g per 1 %): CF-4 / B-BLEED-1 (§15.9).\n'
      '36. v2.4b: which FA-1 case group governs each period domain (OI-41): lead; IGN-1 measures the real peaks.\n'
      '37. v2.4b: the founders\' stand tank capacity and heel (T1 at 2t = 8 s; CF-4 budget).\n'
      '38. v2.4b: the minimum propane supply temperature implied by the 5 bar abs propane cut-off (about 2 C; §15.10).\n'
      '39. v2.4b (line 213): the 210 m A1 record: engine-on time, T_tank at MECO and relight, coast duration and the ARM-hot case (gnc.json '
      'v3.2); Mechanical\'s relight wall temperatures on it (OI-49; §15.15).\n')

# ================================================================== §12 open items
def row_rep(prefix, new):
    l = [x for x in text.split('\n') if x.startswith(prefix)]
    assert len(l) == 1, prefix
    R(l[0], new)
row_rep('| OI-6 | Pc transducer |', '| OI-6 | Pc transducer | v2.4b: RE-OPENED by line 205: the flight unit is reselected (seat-mounted, proof >= 112 bar abs per the lead; '
        'Combustion\'s all-case 0.1-1 ms value gives 132 bar abs, OI-41); was "range >= 70 bar per ENG-09" | Electronics; Mechanical (CC-2 head) |')
row_rep('| OI-17 | FA-1 load |', '| OI-17 | FA-1 load | v2.4b: load per line 194 (1)-(2) (period domain; thrust rectangle to 20 ms, long-period spectrum above); '
        'spectra in §7.6 (Tables 7.6c, 7.6d); contradiction OI-41. Line-177 actions: TC-09 Inconel 718 in CAD v3.5 and J-FWD A4-80 done on paper; '
        'open: the gimbal bearing selection (C0 >= 1.80 kN per bearing from a maker datasheet) and Mechanical\'s modal closure | Mechanical, lead |')
row_rep('| OI-22 | Nozzle joint |', '| OI-22 | Nozzle joint | J1 CONFIRMED (line 146); FE re-run with the two-layer stack; the lip is Inconel 718 (TC-09): H19 '
        'recomputed (lumped %s-%s s from 342 C; §6.5); the 10.6 MPa bearing; leak criterion | Mechanical, Combustion |' % (
            f2(ns['L1_lumped_1mm_s'][0]), f2(ns['L1_lumped_1mm_s'][1])))
row_rep('| OI-31 | PURGE commit rule (H20) |', '| OI-31 | PURGE commit rule (H20) | CLOSED by line 186 (1): L* = 1.3 s, no unpurged relight below it; line '
        '204 (1)-(2): L* stays, the unpurged alternative NOT ADOPTED; ECU guard in v2.11 (line 203 (7)). "E2 + 0.22 s" withdrawn (194 (3)); Table '
        '2.18 | Lead (decided); Electronics (guard) |')
row_rep('| OI-32 | Tank outlet |', '| OI-32 | Tank outlet | Outlet position and diameter, dip tube or sump, anti-vortex device, orientation and bulkhead face '
        'in CAD; a slosh bound; the 500-run specific-force angle during PURGE. v2.4b: dip onset for the landing reserve (Table 2.4b; line 194 (6)) '
        '| Mechanical, GNC |')
row_rep('| OI-34 | Stand dynamic Pc channel |', '| OI-34 | Stand dynamic Pc channel | >= 10-20 kHz, anti-alias filter, flush mount or a characterised '
        'short sense line, range >= 100 bar abs, proof >= 112 bar abs flush (>= 132 bar abs for a 0.1-1 ms path; > 1 ms not acceptable; line '
        '194 (7)), for IGN-1 and T1-T3; price TO-QUOTE (Sønderborg DK-6400) | Electronics, founders |')
row_rep('| OI-37 | Interface configuration (R2-13) |', '| OI-37 | Interface configuration (R2-13) | Decided by line 186 (4): mechanical.json v2.2 carries '
        'MEOP 45 bar, proof 67.5 bar, FA-1 per line 194 (1) and the rounded entrance, and cites the tank relief setpoint; v2.2 is not yet in '
        'the hub (v2.1 read). electronics.json v3 (v2.10) read; A5 and the Burkert 6027 HP to be removed per 186 (4) | Lead, Mechanical, Electronics |')
row_rep('| OI-38 | Cold-flow thrust and R2 (line 181 (4)) |', '| OI-38 | Cold-flow thrust and R2 (line 181 (4)) | ADOPTED in design (line 186 (2)); '
        'margin CONDITIONAL on Cd x A x G at the start lift (194 (4)): CF-3 start-lift point (encoder, load cell); GNC R2 v2 with F_cold and the '
        'start-level lit history at 0.21776 mm (Table 7.3b); injector-body temperature at the relight | GNC; founders (CF-3); Combustion (model) |')
row_rep('| OI-40 | NZ-01 acceptance criterion (line 183 (2)) |', '| OI-40 | NZ-01 acceptance criterion (line 183 (2)) | DECIDED (line 186 (3) with the '
        '194 (5) wording): more than 2 % beyond the erosion predicted for that firing, the prediction frozen before the firing and updated only '
        'with earlier firings; a non-axisymmetric step; a missing fragment. Procedure §15.12 (OI-48) | Lead (decided); founders (inspection) |')
new_oi = [
    '| OI-41 | FA-1 period-domain values (v2.4b) | Dense all-case spectrum above the line-194 (1) values: %s > 90 bar abs (T <= 0.1 ms); 0.1-1 ms '
    'baseline %s, all cases %s against 93 / 102; ENG-TC-02 band %s / %s. Decide which case group governs each domain; the flight Pc proof '
    'follows | Lead; Mechanical |' % (f1(pdv('T_le_0p1ms', 'head|all')), f1(pdv('T_0p1_to_1ms', 'head|baseline')), f1(pdv('T_0p1_to_1ms', 'head|all')),
                                      f1(tc02['max_in_band_baseline']['value_bar']), f1(tc02['max_in_band_all']['value_bar'])),
    '| OI-42 | Purge cap and the 76 g allowance (v2.4b) | The 2.55 s both-open cap gives %.2f g on the record bound (75.99 g on the record '
    'slope); strict 76 g needs <= %.3f s; Cd ASSUMED (+-0.7 g per 1 %%). Accept 76.05 g as 76 g, or set 2.54 s; CF-4 / B-BLEED-1 measure the '
    'flow (§15.9). Line 213: a warmer 210 m relight state adds about %.2f g per K above 289.5 K (OI-49) | Lead; Electronics; founders |'
    % (m[k260]['combustion_bound_open_g'], I1['cap_for_76g']['both_open_s_with_0p05_offset'], A1P['M_2p5s_slope_g_per_K']),
    '| OI-43 | THE start-level lift in the ECU (v2.4b) | Hold lift = h_s(T_tank at E0), the ignition-lift row (0.21776 mm at the A1 state), '
    'replacing 0.2154 mm; gen_tables re-run on v2.4b; CF-3 at the commanded lift with the encoder (§15.3) | Electronics; founders |',
    '| OI-44 | E2 rule difference (v2.4b) | ECU relative-rule E2 up to %.1f ms earlier than the model E2; bound holds from the ECU E2 (§15.5) for '
    'GNC P4c if the comparator is flown | GNC; Electronics |' % (1e3 * I3['shift_bound_s']),
    '| OI-45 | Pc port passage gas (line 205; v2.4b) | c >= %.0f m/s if free of liquid N2O (near-critical N2O); composition MISSING; liquid N2O '
    'in the passage not bounded; CC-1 needs c >= 220.2 m/s for 1 ms. Mechanical sizes CC-2 at c_min; B-PC-1 / IGN-1 record the ring-down '
    '(§15.8) | Mechanical; Electronics; founders |' % I8['c_design_min_m_s'],
    '| OI-46 | Firmware constant sources (v2.4b) | Source text for 2500 N/s, 0.5 s, 5 bar abs and 0.12 s (§15.10); the propane cut-off implies '
    'a supply >= about 2 C. Electronics confirms the mapping; founders state the propane conditioning | Electronics; founders |',
    '| OI-47 | IN718 datasheet archive (v2.4b) | SMC-045 read through the web-fetch reader; the proxy refused the PDF download. Archive the PDF '
    'with its hash | Mechanical; founders |',
    '| OI-48 | NZ-01 frozen prediction (v2.4b) | Combustion issues the prediction file before each T-series firing; founders measure the bore '
    '(§15.12) | Combustion; founders |',
    '| OI-49 | A1 apogee target about 210 m (line 213; v2.4b) | No 210 m A1 record yet; the A1 values are 300 m / 285 m comparators. The '
    'warm-end relight state rises: purge +%.2f g per K above 289.5 K (76 g on the 2.5 s schedule up to %.2f K), cold-flow bound +0.13 N '
    'per K. GNC publishes the 210 m record; Combustion re-runs the A1 grain run, Table 7.3b, the purge records at the warm-end state and '
    'FA-1 at the relight state; Mechanical the relight wall temperatures; no new sizing case (LEAD) (§15.15) | GNC; Combustion; Mechanical |'
    % (A1P['M_2p5s_slope_g_per_K'], A1P['T_at_76g_2p5s_K'])]
row40 = [x for x in text.split('\n') if x.startswith('| OI-40 | NZ-01 acceptance criterion (line 183 (2)) |')][0]
AFTER(row40 + '\n', '\n'.join(new_oi) + '\n')
R('## 12. Open items with owners (v2.4, updated in v2.4a)', '## 12. Open items with owners (v2.4, updated in v2.4a and v2.4b)')

# ================================================================== §13
R('| Refuted as written (SIM/DERIVED); OI-31 for the lead |', '| Refuted as written (SIM/DERIVED); OI-31 closed by line 186 (1) |')
last13 = [x for x in text.split('\n') if x.startswith('| Line 183 (2) refutation "throat-area change > 2 %" |')][0]
rows13 = [
    '| Line 175 (3) PROVISIONAL commit rule (1.7 s) and the 1.7 s interim of line 181 (2) | Superseded by line 186 (1) | L* = 1.3 s; no unpurged '
    'relight below it (v2.4b) |',
    '| "E2 + 0.22 s" release hold (line 186 (1)) | Derived from one state (R3-01) | Withdrawn (line 194 (3)); Table 2.18 |',
    '| Line 173 "90 bar for every part" and the 92 bar design value | The load rule had no period domain; the DLF stopped at 1 ms (R3-02, R3-04) | '
    'Period domain (line 194 (1)); spectra §7.6 |',
    '| Line-194 (1) values below 1 ms | The dense all-case spectrum gives %s bar abs (T <= 0.1 ms) and %s bar abs (0.1-1 ms) | Contradiction kept '
    '(OI-41) |' % (f1(pdv('T_le_0p1ms', 'head|all')), f1(pdv('T_0p1_to_1ms', 'head|all'))),
    '| 316L lip melt 1.07-5.70 s (H19) | TC-09 is Inconel 718 (lines 177 (1)/178) | IN718 %s-%s s (§6.5) |' % (f2(ns['L1_lumped_1mm_s'][0]),
                                                                                                         f2(ns['L1_lumped_1mm_s'][1])),
    '| ABORT at t_E2 + 0.8 s (v2.4a §7.3) | Line 181 (4) set pcf_tmax 0.5 s | Corrected (R3-09) |',
    '| "The 0.81 s plan holds" without scope | Line 181 (2) scoped it to the predictor path | Scoped (R3-09) |',
    '| "The T_fire delay is <= 0.6 s and costs no measurable P" | Withdrawn by line 181 (2) | Removed (R3-09) |',
    '| "0 in 82 % / 77 %", "every HI record", the H20 population means | True for one command profile only (R3-13) | Stated per profile (§2.8) |',
    '| Command hold "PROPOSAL" (OI-38), NZ-01 "proposal" (OI-40) | Decided by lines 186 (2) and 186 (3) | Text updated; 194 (4)-(5) |',
    '| "Chamber heat pick-up" TO-VERIFY | The threshold is for heat at tank pressure (R3-14) | Injector-body and feed soak-back temperature |',
    '| "About x9 margin" (line 186 (5)) | The 81.6 g depletion is inside the 766 g basis (R3-16) | 766 g is 9.3-9.7x the 78.6-82.5 g |',
    '| 62.5 N x pcf_k as the lit thrust in R2 | Fuel-starved start (R3-14) | grain_q1d start-level history (Table 7.3b) |',
    '| ECU hold lift 0.2154 mm; "ignition lift 0.2039 mm" as a single value | An open-loop-map lift, not a definition; the lift depends on T_tank | '
    'THE start-level lift h_s(T) (§15.3) |',
    '| Purge vented mass as 29.8 or 32.0 g/s x t | A rate times time; the line starts with vapour | Record basis (§15.9) |',
    '| Pc port gas bracket 222-400 m/s (Mechanical interim) | Gas-filled minimum 181 m/s; products up to 1136 m/s | §15.8; OI-45 |',
    '| Lead-items script, first runs | A format-string error, then no CoolProp N2O conductivity model (no output); then the passage minimum taken '
    'at the median and maximum peaks only (201 m/s) | Fixed: ASSUMED 0.10 W/m K upper-bound conductivity for the penetration estimate; dense '
    'minimum over the 22-88 bar peak range (181 m/s) before any value was used |',
    '| A1 apogee target 285 m (trim) / 300 m (lead default) as the A1 basis | LEAD line 213 (founder): about 210 m | 300 m and 285 m values '
    'kept as comparators; directions in §15.15 |']
AFTER(last13 + '\n', '\n'.join(rows13) + '\n')

# ================================================================== §14
scr_rows = [
    ('release_hold_v2p4b.json', 'release_hold_v2p4b.json (`a926426da0e6e436`), release_hold_records_v2p4b.csv (`59e7f44e44fbfeef`)', 'Table 2.18, R3-01'),
    ('population_statements_v2p4b.json', 'population_statements_v2p4b.json (`bffabc97aee6a5cb`)', '§2.8, R3-13'),
    ('fa1_spectra_v2p4b.json', 'fa1_spectra_v2p4b.json (`372b8078d7a90e75`), fa1_pressure_spectra_v2p4b.csv (`55df65344f35759b`), '
                               'fa1_thrust_spectra_v2p4b.csv (`288a2294151e3760`), fa1_histories_solver_v2p4b.npz (`399bf43d1c09de24`)', '§7.6, R3-02/03'),
    ('fa1_spectra_dense_v2p4b.json', 'fa1_spectra_dense_v2p4b.json (`7468996959538d0f`), fa1_pressure_spectra_dense_v2p4b.csv (`4a4ebb65b38a9a03`), '
                                     'fa1_thrust_spectra_dense_v2p4b.csv (`072f2e0f2987fda5`)', 'Tables 7.6c, 7.6d'),
    ('cold_flow_start_lift_v2p4b.json', 'cold_flow_start_lift_v2p4b.json (`28ce48092f33da1b`)', '§7.3, R3-05'),
    ('start_level_lit_thrust_v2p4b.json', 'start_level_lit_thrust_v2p4b.json (`ae2038c5141b7f73`), .csv (`f6ac2a4da04f8d45`)', 'Table 7.3b, 0.2039 mm'),
    ('start_level_lit_thrust_0p21776mm_v2p4b.json', 'start_level_lit_thrust_0p21776mm_v2p4b.json (`10cdc03154b95216`), .csv (`c073d4f993f8c412`)',
     'Table 7.3b, 0.21776 mm'),
    ('tank_outlet_dip_v2p4b.json', 'tank_outlet_dip_v2p4b.json (`6c11d3c19afe983c`)', 'Table 2.4b, R3-17'),
    ('nozzle_lip_melt_in718_v2p4b.json', 'nozzle_lip_melt_in718_v2p4b.json (`23b85b7febb90c60`)', '§6.5, H19'),
    ('test_budgets_v2p4b.json', 'test_budgets_v2p4b.json (`c0e4ce35659f21fa`)', '§10, specifications'),
    ('lead_items_203_205_v2p4b.json', 'lead_items_203_205_v2p4b.json (`e20a8b8c33af9162`)', '§15'),
    ('a1_profile_line213_v2p4b.json', 'a1_profile_line213_v2p4b.json (`46b6a1c6efec0351`)', '§15.15, line 213')]
t14 = '\n'.join('| `%s` (`%s`) | %s | %s |' % (SCR[k][0], SCR[k][1], d, u) for k, d, u in scr_rows)
t14 += '\n| `build_specs_v2p4b.py` (`%s`) | `T1-T4-REGRESSION-SPEC.md` v3 (`%s`), `CF-4-SPEC.md` v2.1 (`%s`) | §10 |' % (SCR['build_specs_v2p4b.py'][1], H_T, H_C)
t14 += ('\n| `write_interface_v2p4b.py` (`%s`) | `interfaces/combustion.json` v2.4b (`%s`) | every v2.4a key kept; replaced values under '
        '`*_superseded` |' % (SCR['write_interface_v2p4b.py'][1], H_CJ))
t14 += '\n| `build_report_v2p4b.py` (`%s`), `build_response_r3_v2p4b.py` | this report and `REVISION-RESPONSE-R3.md` | - |' % SCR['build_report_v2p4b.py'][1]
AFTER('Reproduction (v2.4a): each script asserts its input hashes; run with `/opt/engine-venv/bin/python -I`.', (
    '\n\nv2.4b additions (scripts in `02-combustion/src/`; data in `02-combustion/data/v2p4b/` with `HASHES.txt` in `sha256sum -c` format; '
    'sha256/16; each data file records its producing script\'s hash, checked by the report builder):\n\n'
    '| Script | Data | Use |\n|---|---|---|\n%s\n\n'
    'Reproduction (v2.4b): run each script with `/opt/engine-venv/bin/python -I` from `src/`; usage is in each docstring; the input hashes are '
    'asserted. The two lit-history runs take about 28-32 min each on the shared CPU; the rest take seconds to minutes.') % t14)

# ================================================================== §15 (new)
fw = I4['constants']
fw_rows = '\n'.join('- **%s** (`engine_params.h`: `%s`; %s). %s' % (k, v['firmware'][0], v['tag'], v['source_text']) for k, v in fw.items())
pg = I8
hist = '\n'.join('%d. %s' % (i + 1, h) for i, h in enumerate(pg['history']))
rl = pg['relight_instant_c_m_s']
air_rng = (min(v['air_m_s'] for v in rl.values()), max(v['air_m_s'] for v in rl.values()))
prod_rng = (min(v[k] for v in rl.values() for k in v if k.endswith('water_saturated_m_s')), max(v[k] for v in rl.values() for k in v if k.endswith('water_saturated_m_s')))
n2o_rng = (min(v['N2O_vapour_m_s'] for v in rl.values()), max(v['N2O_vapour_m_s'] for v in rl.values()))
hot = pg['hot_products_frozen']
dmin = pg['N2O_single_phase_minimum_dense']
isd = pg['N2O_isentropic_from_saturation_minimum']
wall = pg['N2O_wall_cooled_at_peak']
pb_rows = '\n'.join('| %s | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f |' % (
    k, v['combustion_bound_open_g'], v['combustion_record_slope_g'], v['combustion_barrier_g'], v['electronics_comb_basis_g'],
    v['electronics_sil_basis_g'], v['all_liquid_line_from_t0_g']) for k, v in m.items())
cl = I6['groups']
cl_rows = '\n'.join('| %s | %.2f / %.2f | %.4f / %.4f | %.4f / %.4f |' % (
    lab[g], cl[g]['ramp_to_200N']['hold_needed_s'], cl[g]['ramp_to_500N']['hold_needed_s'], cl[g]['ramp_to_200N']['mean_P_success_worst_convention'],
    cl[g]['ramp_to_500N']['mean_P_success_worst_convention'], cl[g]['ramp_to_200N']['mean_P_trip'], cl[g]['ramp_to_500N']['mean_P_trip']) for g in G_)
sec15 = '''

## 15. v2.4b: lead lines 186, 194, 203-205 and 213

Sources: `src/%s` (`%s`) and its output `data/v2p4b/lead_items_203_205_v2p4b.json` (`e20a8b8c33af9162`), with the data files named in each
subsection. Tags are given per value. Nothing here is physical evidence or approval.

### 15.1 Decisions folded

| Line | Decision | Where |
|---|---|---|
| 186 (1) | L* = 1.3 s ADOPTED; no purge and no unpurged relight below it | §0 item 13, §2.8 items 19-22, §7.4, §9 (H17, H20, B-5, B-6); JSON `purge_commit_rule_v2p4b` |
| 186 (2) | R2 command hold at the start level ADOPTED | §7.3, B-7; JSON `cold_flow_thrust_v2p4a.proposal`, `fmea_input` |
| 186 (3), 194 (5) | NZ-01 criterion with the frozen prediction | §5.4 note, §15.12; JSON `nz01_criterion_v2p4b` |
| 186 (4) | Interface configuration | OI-37 |
| 186 (5), 194 (5) | Outlet coverage wording | §0 item 12, §2.4 |
| 194 (1)-(2) | FA-1 period domain and thrust domain | §0 item 2, §7.6 (Tables 7.6c, 7.6d); OI-41 |
| 194 (3), 204 (2) | "E2 + 0.22 s" withdrawn; alternative NOT ADOPTED; classes published | §2.8 Table 2.18, §15.6 |
| 194 (4) | Margin CONDITIONAL; CF-3 start-lift point; heat location; lit history | §7.3 (Table 7.3b), §10 |
| 194 (6) | Outlet dip for GNC | §2.4 Table 2.4b, §15.11 |
| 194 (7) | Stand dynamic channel >= 100 bar abs with proof rating | §10, OI-34 |
| 194 (8) | T1-T4 v3, CF-4 v2.1, budgets | §10 |
| 194 (9) | Stale text; H19 for IN718 | §6.5, §13 |
| 203 (3) | ECU cap <= 2.55 s; flow basis | §15.9, OI-42 |
| 203 (7) | THE start-level lift | §15.3, OI-43 |
| 204 (1) | L* stays; commit lead < about 2.1 s not a landing | §2.8 item 19, §7.4 |
| 204 (4) F11 | A1_none p99 8.375 s | §15.13 |
| 205 | Pc port passage gas sound speed; flight Pc reselected | §15.8, §7.4; OI-6, OI-45 |

### 15.2 PURGE commit and L* (lines 186 (1), 194 (3), 203 (7), 204 (1)-(2))

PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s, for both wall heat-transfer brackets. Below L* there is no purge
and no unpurged relight on that pass (drogue descent; vehicle loss in the FMEA); the ECU enforces it with the unpurged RELIGHT guard (v2.11).
GNC rev3: purging after L* is never worse than no relight, but a commit lead below about 2.1 s is not counted as a landing (P about 0 at
1.31 s, 0.76-0.78 at about 1.7 s, 0.99 at about 2.1 s with the nominal start); nominal leads are >= 2.65 s. The unpurged alternative is NOT
ADOPTED; it would be revisited only if the gate-failure probability is shown >= 1 %% per flight, or if CF-4/T4 settle the unpurged start as
LO and the per-record classes confirm the 0 residual (Table 2.18 shows 0 at H = 0.30 s on the 200 N ramp, with Pc valid). LO/HI stays open:
CF-4 generation runs and T4 measure it.

### 15.3 THE start-level lift (line 203 (7); relay item 2)

%s

- Values before CF-3 (DERIVED; flow linear in lift between 0.2039 and 0.218 mm; Cd 0.70 ASSUMED): A1 relight state 286.70 K: **%.5f mm**
  (the ECU table row; Combustion's own model gives %.5f mm, %.3f %%); 20 C: **%.4f mm** (the 293.15 K ECU row %.5f mm scaled to the 37.1 g/s
  cap is %.5f mm).
- Retired: the ECU hold lift 0.2154 mm (the open-loop-map lift for 62.5 N at the SIL S17 state). The S230 map's 62.5 N lift (%.4f-%.4f mm
  over 289.5-283.15 K) is the nominal lit level of the map, not a lift definition.
- Cold-flow bound at h_s (A1 state): %.2f N (DERIVED; CONDITIONAL on Cd x A x G; margin 16.31 N).
- Consequences: %s

### 15.4 Start-level lit thrust (line 194 (4))

Table 7.3b (§7.3). At THE start-level lift (0.21776 mm, A1 state) the lit thrust between E2 and E2 + 0.5 s is %.1f-%.1f N and %d of 72
corners stay below 37.16 N throughout; at 0.2039 mm, %.1f-%.1f N and %d of 72. GNC uses the 0.21776 mm history.

### 15.5 E2: latency model against the ECU relative rule (relay item 3)

- Model E2 (start_latency_v2p4, used by rg01 and the release-hold tables): measured Pc > 3.0 bar abs held 10 ms, latency 2.3 ms; light to E2
  %.1f-%.1f ms (median %.1f ms) at the %.4f mm lift (%d A1 runs; SIM).
- ECU E2: rise >= 0.8 bar over the pre-lift baseline on filtered AND raw Pc for 10 ms, above 1.8 bar abs (§7.3); >= 12.3 ms after the light
  by construction; %.1f-%.1f ms in the grain_q1d runs at 0.21776 mm (%.1f-%.1f ms at 0.2039 mm).
- %s
- Bound holds from the ECU E2: §2.8 (v2.4b table after Table 2.18). The per-record CSV stays on the model E2. (DERIVED from stored SIM; no
  re-run.)

### 15.6 Per-record classes for the 500 N ramp (relay item 6)

`release_hold_records_v2p4b.csv` (6480 rows = 2160 records x 3 profiles; the column `profile` is `ramp_to_200N`, `ramp_to_500N` or
`lift_flow_held`) carries every per-record class column for each profile. Group summary (hold needed [s], 200 N / 500 N; mean P(success),
worst convention; mean P(A3 trip)):

| Records | Hold needed | Mean P(success) | Mean P(A3 trip) |
|---|---|---|---|
%s

Status: %s. Tag: %s.

### 15.7 FA-1 items (relay item 5)

- Head spectrum near 6 ms (the 0.30 m sense line, 5.7-8.7 ms per Mechanical; deleted by line 205): %.2f bar abs baseline, %.2f all cases at
  6.0 ms; maxima over 5.7-8.7 ms %.2f / %.2f; over 2.5-4.9 ms %.2f / %.2f (DERIVED; undamped).
- Histories: %s

### 15.8 Gas in the Pc port passage at the FA-1 instant (line 205)

Mechanical's interim (`v351/pc/pc_line_period_v1.json` `7f5d8950516d98f2`; read only) needs the gas sound speed c in the Pc port passage
(Ø2.0 x 54.17 mm drilled from the seat to the head metal face, then Ø3.0 x 2.0 mm through the TC-10 disc, 184.3 mm3) at the FA-1 instant;
it brackets c at 222-400 m/s. Wall temperature at RELIGHT: %.1f-%.1f K (Mechanical, A1 p99 case, SIM with a 20 C start ASSUMED; %.1f K with
an ASSUMED +20 K hot-day shift).

**What fills the passage** (DERIVED reasoning; composition MISSING because the construct does not model the port mouth):

%s

Table 15.8. Sound speed of the candidate gases [m/s] (CoolProp HEOS for N2O, air and water; Cantera gri30 frozen equilibrium products at the
case O/F, as the v2.4a construct; DERIVED).

| Gas | State | c [m/s] |
|---|---|---|
| Relight-instant air | 1 atm, wall temperature | %.0f-%.0f |
| Cooled first-burn products (O/F 3-8, water saturated) | 1 atm, wall temperature | %.0f-%.0f |
| N2O vapour | 1 atm, wall temperature | %.0f-%.0f |
| Burned products entering during the rise | frozen, T_HP %.0f-%.0f K, O/F 3-8 | %.0f-%.0f |
| N2O vapour from saturation (<= %.1f bar, the flash limit), compressed isentropically | peaks %.1f-%.1f bar abs | >= %.0f (entry %.1f bar, peak %.1f bar) |
| N2O at the wall temperature | median and maximum peaks (48.2 / 88 bar) | %.0f-%.0f |
| N2O single-phase minimum over the peak range | %s, %.1f K (%s) | %.0f (%.0f below 70 bar) |
| Compressed relight-instant air at the closed end | isothermal / isentropic | 350-%.0f |
| Two-phase N2O (droplets, condensate) | below 72.45 bar | not bounded (MISSING) |

**Answer.** %s

**Period.** %s

**Tags and limits.** Wall temperatures SIM (Mechanical interim; 20 C start ASSUMED; the hot-day shift ASSUMED here); the thermal-penetration
estimate uses an ASSUMED upper-bound N2O conductivity of 0.10 W/m K (CoolProp has no N2O conductivity model; a larger value only deepens the
layer); construct peaks SIM on ASSUMED inputs; the gas composition is MISSING. TO-VERIFY: IGN-1 and B-PC-1 with the port ring-down recorded.

### 15.9 Purge flow basis and the ECU cap (line 203 (3); relay item 1)

%s

Table 15.9. Vented mass by flow time [g] (Combustion: records, SIM on ASSUMED Cd 0.70 and slip brackets, extended at the all-liquid rate:
DERIVED upper bound; Electronics: as published in `bleed_driver_v1.json`).

| Flow time | Combustion bound (open) | Record slope | Barrier | Electronics, 29.2 g/s basis | Electronics, SIL basis | All-liquid line from t = 0 |
|---|---|---|---|---|---|---|
%s

- **Cap.** %s
- GNC's 80 g sensitivity is reached at %.3f s of flow on the bound. Until CF-4 / B-BLEED-1 measure the flow, GNC carries the higher basis as a
  sensitivity (line 203 (3)).
- All-liquid two-tap rate by tank state (Dyer, Cd 0.70 ASSUMED): %s.

### 15.10 Firmware constant sources (relay item 4)

Matched by value and the [COMB] tag in `06-electronics/firmware/src/core/engine_params.h` (`6b73317fcd7d07ac`, read only); Electronics
confirms the mapping (OI-46).

%s

- **FLAMEOUT_OPT (cold_flow text).** %s

### 15.11 Tank outlet dip onset (line 194 (6); R3-17)

Table 2.4b (§2.4). GNC checks the landing usable reserve against the dip onset (%.1f-%.1f g at 125 N, %.1f-%.1f g at 250 N, %.1f-%.1f g at
500 N; 283-289.5 K) instead of the ASSUMED 3 %% (60 g) residual; the reviewer's comparator (60-62 / 68-69 / 78-80 g) agrees. Line 186 (5)
wording: quasi-static coverage needs 13.6 mm of liquid (78.6-82.5 g); 766 g remains at the end of the purge flow, 9.3-9.7x.

### 15.12 NZ-01 frozen prediction (lines 186 (3), 194 (5); R3-15)

Criterion (lead): refutation is any of: a throat-area change more than 2 %% beyond the erosion predicted for that firing, the prediction frozen
before the firing and updated only with earlier firings; a non-axisymmetric step; a missing fragment. Procedure (Combustion, DESIGN):

%s

Consequence (DERIVED): %s

### 15.13 A1 duration (line 204 (4) F11; relay item 7)

%s

### 15.14 Configuration notes

- Line 186 (4): mechanical.json v2.2 is not yet in the hub (v2.1 read); electronics.json v3 is read for status (OI-37).
- Line 206 (read for status): v3.5.1 FROZEN as built; of the v3.5.2 levers, (a) the TC-09 1.8 mm barrel wall is noted against H19 (§6.5)
  and (c) keeps every MV-to-seat part stainless, as the lead stated; no Combustion analysis changes.
- Lines 194 (10) and 186 (6): the re-review of v2.4b is a delta check of the R3-01 and R3-02 numbers, the rest by document diff.
''' % (SCR['lead_items_203_205_v2p4b.json'][0], SCR['lead_items_203_205_v2p4b.json'][1],
       I2['definition'], I2['values_before_CF3']['A1_relight_286p70K_mm'], I2['values_before_CF3']['A1_relight_combustion_model_mm'],
       I2['values_before_CF3']['A1_relight_agreement_pct'], I2['values_before_CF3']['pad_20C_mm'], I2['values_before_CF3']['pad_20C_ECU_row_mm'],
       I2['values_before_CF3']['pad_20C_ECU_row_scaled_to_37p1_mm'], I2['retired']['map_62p5N_lift_mm'][0], I2['retired']['map_62p5N_lift_mm'][1],
       I2['cold_flow_bound_at_hs']['A1_relight_N'], '; '.join(I2['consequences']),
       s2['F_min_over_corners_in_E2_to_E2p0p5_N'], s2['F_max_over_corners_in_E2_to_E2p0p5_N'], s2['n_corners_never_ge_37p16N_in_window'],
       s1['F_min_over_corners_in_E2_to_E2p0p5_N'], s1['F_max_over_corners_in_E2_to_E2p0p5_N'], s1['n_corners_never_ge_37p16N_in_window'],
       1e3 * I3['light_to_E2_model_s']['min'], 1e3 * I3['light_to_E2_model_s']['max'], 1e3 * I3['light_to_E2_model_s']['median'],
       I3['light_to_E2_model_s']['lift_mm'], I3['light_to_E2_model_s']['n'],
       1e3 * I3['light_to_E2_relative_s']['0.21776mm']['E2_torch0_s'][0], 1e3 * I3['light_to_E2_relative_s']['0.21776mm']['E2_torch0_s'][1],
       1e3 * I3['light_to_E2_relative_s']['0.2039mm']['E2_torch0_s'][0], 1e3 * I3['light_to_E2_relative_s']['0.2039mm']['E2_torch0_s'][1],
       I3['statement'], cl_rows, I6['status'], I6['tag'],
       I5['head_spectrum_near_6ms']['values']['baseline']['at_6p0ms_bar'], I5['head_spectrum_near_6ms']['values']['all_cases']['at_6p0ms_bar'],
       I5['head_spectrum_near_6ms']['values']['baseline']['max_5p7_to_8p7ms_bar'], I5['head_spectrum_near_6ms']['values']['all_cases']['max_5p7_to_8p7ms_bar'],
       I5['head_spectrum_near_6ms']['values']['baseline']['max_2p5_to_4p9ms_bar'], I5['head_spectrum_near_6ms']['values']['all_cases']['max_2p5_to_4p9ms_bar'],
       I5['histories']['limit'],
       pg['wall_temperature_at_relight_K']['A1_SIM'][0], pg['wall_temperature_at_relight_K']['A1_SIM'][1],
       pg['wall_temperature_at_relight_K']['hot_day_ASSUMED_plus20K'][1], hist,
       air_rng[0], air_rng[1], prod_rng[0], prod_rng[1], n2o_rng[0], n2o_rng[1],
       min(v['T_HP_K'] for v in hot.values()), max(v['T_HP_K'] for v in hot.values()), min(v['c_frozen_m_s'] for v in hot.values()),
       max(v['c_frozen_m_s'] for v in hot.values()), max(pg['N2O_flash_limit_bar'].values()), pg['construct_head_peak_bar']['min'],
       pg['construct_head_peak_bar']['max'], isd['c_m_s'], isd['entry_bar'], isd['peak_bar'],
       min(wall[k]['c_range_m_s'][0] for k in ('48.2bar', '88bar')), max(wall[k]['c_range_m_s'][1] for k in ('48.2bar', '88bar')),
       dmin['minimum']['at'], dmin['minimum']['T_K'], dmin['minimum']['phase'], dmin['minimum']['c_m_s'], dmin['minimum_below_70bar']['c_m_s'],
       max(v['isentropic_c_m_s'] for d in pg['air_compressed_to_peak'].values() for v in d.values()),
       pg['answer']['bound'], pg['answer']['period_scaling'],
       I1['answer'], pb_rows, I1['cap_for_76g']['note'], I1['gnc_80g_sensitivity']['t_flow_s'],
       '; '.join('%.2f g/s at %.2f K (%.2f bar)' % (v['all_liquid_two_taps_g_s'], v['T_K'], v['P_tank_bar']) for v in I1['liquid_rate_by_state_two_taps'].values()),
       fw_rows, I4['FLAMEOUT_OPT_cold_flow_text'],
       DIP['125N']['liquid_at_onset_g_283_to_289p5K'][0], DIP['125N']['liquid_at_onset_g_283_to_289p5K'][1],
       DIP['250N']['liquid_at_onset_g_283_to_289p5K'][0], DIP['250N']['liquid_at_onset_g_283_to_289p5K'][1],
       DIP['500N']['liquid_at_onset_g_283_to_289p5K'][0], DIP['500N']['liquid_at_onset_g_283_to_289p5K'][1],
       '\n'.join('%d. %s' % (i + 1, x) for i, x in enumerate(CJ['nz01_criterion_v2p4b']['v']['frozen_prediction'])),
       CJ['nz01_criterion_v2p4b']['v']['consequence'], I7['statement'])
text = text.rstrip('\n') + sec15
R('Combustion proposes that the post-firing inspection compare the measured bore with the erosion expected for the firing (pre/post bore, '
  'duty cycle), and count as refutation any area change > 2 % beyond that expectation, any non-axisymmetric step or any missing fragment '
  '(contradiction kept for the lead, OI-40).',
  'Combustion proposed that the post-firing inspection compare the measured bore with the erosion expected for the firing; the lead decided '
  'it (line 186 (3)) with the wording of line 194 (5): more than 2 % beyond the erosion predicted for that firing, the prediction frozen '
  'before the firing and updated only with earlier firings; a non-axisymmetric step; a missing fragment. Procedure: §15.12.')
# ================================================================== LEAD line 213: A1 apogee target about 210 m (v2.4b)
AFTER('    - **Stale text** of the v2.4a fold and of line 186 replaced (R3-09, R3-11); the old values are in §13 and under `*_superseded` keys '
      'in the interface.\n',
      '14. **A1 apogee target about 210 m (LEAD line 213, founder decision; §15.15).** GNC sets the exact band (gnc.json v3.2). The A1 values '
      'in this report come from the 300 m records of gnc.json v3.1 (A1 sizing cycle 8.258 s, apex 302.4 m) and the 285 m GNC rev3 records '
      '(A1_none p99 8.375 s); they stay as comparators. B1 still governs thermal and erosion sizing (LEAD); no new sizing case. What moves '
      'with a lower apogee (DERIVED directions; no 210 m record yet): the A1 duty cycle is shorter; at the same launch temperature the relight '
      'tank state is warmer, because the modelled tank keeps its MECO temperature over the coast and the 300 m ascent cools it by %.2f-%.2f K. '
      'The purge vented mass then rises by about %.2f g per K above the 289.5 K basis (76 g on the 2.5 s schedule up to %.2f K; the 2.55 s cap '
      'is already at 76 g, OI-42), and the start-level cold-flow bound rises (%.2f N at the 297.15 K ARM limit, below 16.31 N). Open item '
      'OI-49.\n' % (A1S['ascent_cooling_K'][0], A1S['ascent_cooling_K'][1], A1P['M_2p5s_slope_g_per_K'], A1P['T_at_76g_2p5s_K'],
                    A1T['297.15K']['F_bound_map_lift_N']))
_cap = {'Table 2.3. ': ' [LEAD line 213: DC-A1 v1 is a 300 m profile; a comparator for the about-210 m A1 target (§15.15).]',
        'Table 2.4b. ': ' [LEAD line 213: the tank states are those of the 300 m era; line 208 (1) fixes GNC\'s onset at 80 g (§15.15).]',
        'Table 4.4. ': ' [LEAD line 213: the A1 rows are 300 m cycles; comparators for the about-210 m A1 target (§15.15).]',
        'Table 4.6. ': ' [LEAD line 213: the A1 rows are on the 300 m gnc.json v3 cycles; comparators for the about-210 m A1 target (§15.15).]',
        'Table 5.3. ': ' [LEAD line 213: the A1 rows are on the 300 m gnc.json v3 records; comparators; the about-210 m A1 duty cycle is shorter '
                       '(LEAD) and its values are MISSING (§15.15).]',
        'Table 7.3a. ': ' [LEAD line 213: the tank states are those of the 300 m era; a warmer 210 m relight state raises the bound by about '
                        '0.13 N per K (§15.15).]',
        'Table 7.3b. ': ' [LEAD line 213: the A1 relight state of the 300 m era; a comparator; Table 7.3b at the 210 m relight state is MISSING '
                        '(§15.15).]'}
for _pre, _add in _cap.items():
    _l = [x for x in text.split('\n') if x.startswith(_pre)]
    assert len(_l) == 1, _pre
    R(_l[0], _l[0] + _add)
R('**Life statement (replaces "1.0-4.3 A1 flights", v2.3).**',
  '**Life statement (replaces "1.0-4.3 A1 flights", v2.3).** [v2.4b, LEAD line 213: the A1 counts below are on the 300 m gnc.json v3 A1 p99 '
  'cycle and stay as comparators; the about-210 m A1 duty cycle is shorter (LEAD) and its values are MISSING until the 210 m record; one '
  'insert per flight stays (§15.15).]')
_l17 = [x for x in text.split('\n') if x.startswith('17. Line 175 (1)-(2) (v2.4a): A1 apogee target 285 m;')]
assert len(_l17) == 1
R(_l17[0], _l17[0] + ' [v2.4b: LEAD line 213 lowered the A1 target to about 210 m; the 285 m and 300 m values stay as comparators (§15.15).]')
R('(§7.4; LEAD line 166 (4)); Pc transducer range >= 70 bar (ENG-09) |',
  '(§7.4; LEAD line 166 (4)); Pc transducer: flight unit reselected (LEAD line 205; proof >= 112 bar abs, range covering the 45 bar MEOP; '
  '§7.4) [v2.4a: range >= 70 bar (ENG-09)] |')
R('6. **The 0.81 s plan holds.** The purge flow stops 0.05 s before E0',
  '6. **The 0.81 s plan holds on the predictor path, with PURGE committed (scope of LEAD line 181 (2); v2.4b, R3-09).** The purge flow '
  'stops 0.05 s before E0')
AFTER('| 204 (4) F11 | A1_none p99 8.375 s | §15.13 |\n',
      '| 208 (1), (3) (read; cross-reference) | GNC dip onset fixed at 80 g; the ~80 g purge sensitivity arm; NOT ADOPTED strengthened | §15.15 |\n'
      '| 213 (founder) | A1 apogee target about 210 m; the 300 m and 285 m values kept as comparators | §0 item 14, table captions, §15.15; '
      'JSON `a1_apogee_target_v2p4b`; CF-4 v2.1 §4 |\n')
AFTER(I7['statement'] + '\n',
      '\nLEAD line 213 (v2.4b): the A1 target is about 210 m. 8.258 s (the 300 m A1 sizing record, apex 302.4 m) and 8.375 s (the 285 m F11 '
      'record) are comparators. The 210 m duty cycle is shorter (LEAD), so (a) and (c) hold on it; (b), the relight state, moves: a warmer '
      'tank and a smaller port after a shorter ascent (§15.15).\n')
_r15a = '\n'.join('| `%s` | %.2f | %.2f | %.2f-%.2f | %.2f | %.2f | %s | %s |' % (
    k.replace('.csv', ''), v['T0_K'], v['T_relight_K'], v['ascent_burn_s'][0], v['ascent_burn_s'][1], v['ascent_cooling_K'], v['coast_s'],
    ('%.1f' % v['apex_m']) if v.get('apex_m') else 'not indexed (h max %.1f)' % v['max_h_m_csv'],
    ('%.3f' % v['engine_on_counter_s']) if v.get('engine_on_counter_s') else '-') for k, v in A1R.items())
_pr = A1P['rows']
_r15b = '\n'.join('| %.2f | %.2f | %.2f | %s | %s | %.2f | %.2f | %.5f |' % (
    v['T_K'], v['P_sat_bar'], v['purge_all_liquid_two_taps_g_s'],
    ('%.2f' % _pr[k]['M_2p5s_g']) if k in _pr else '-', ('%.2f' % _pr[k]['M_2p60s_g']) if k in _pr else '-',
    v['F_bound_map_lift_N'], v['F_bound_h_s_N'], v['h_s_ECU_mm']) for k, v in A1T.items())
_r15c = '\n'.join('| %s | %s | %s | %s | %s |' % (x['id'], x['topic'], x['basis'], x['direction_at_210m'], x['status']) for x in A1['statements'])
_x208 = A1['line208_cross_references']
sec1515 = ('\n\n### 15.15 A1 apogee target about 210 m (line 213)\n\n'
           'LEAD line 213 (founder decision, 2026-10-13): the A1 apogee target is lowered from the 300 m lead default (285 m trim since line 175) '
           'to about 210 m. The exact target is the line-208 band of the GNC rev4 N = 1000 re-fly on massprops v3.5.1, expected within about 5 m '
           'of 210 m; a band outside 200-220 m returns to the founder. gnc.json v3.2 will carry it. The lead states that the A1 duty cycle '
           'shortens, that B1 still governs thermal and erosion sizing, and that no new sizing case is needed. No 210 m A1 record exists yet, '
           'so this section computes no 210 m value. It states the basis of each A1-profile statement of v2.4b, the direction at 210 m and '
           'the status. Source: `src/%s` (`%s`), `data/v2p4b/a1_profile_line213_v2p4b.json` (`46b6a1c6efec0351`). The tank-state functions are '
           'the v2.4a/v2.4b ones unchanged, and the stored states are reproduced first (§0 Tests).\n\n'
           'Table 15.15a. The 300 m A1 records of gnc.json v3.1 (SIM, GNC; read only). The modelled tank keeps its MECO temperature over the '
           'coast (largest change %.4f K), so the relight state is the launch temperature minus the ascent cooling.\n\n'
           '| Record | T0 [K] | T at MECO = relight [K] | Ascent burn [s] | Ascent cooling [K] | Coast [s] | Apex [m] (index) | Engine-on [s] |\n'
           '|---|---|---|---|---|---|---|---|\n%s\n\n'
           'gnc.json v3.1 lists `DC-A1_full_flight_disp_p99_kest2_tg711_v3` as a run above 24 C (its T0 is above the ARM limit). The 285 m '
           'comparator is GNC rev3 F11 (A1_none p99 engine-on 8.375 s; records, not sizing).\n\n'
           'Table 15.15b. Saturated tank states at relight (DERIVED; CoolProp HEOS; taps Cd 0.70 and bound Cd 0.80 ASSUMED). The purge masses '
           'are scaled from the 289.5 K basis (%s); the purge records are not re-run. The cold-flow bound uses the open-loop map lift (clamped at '
           'the map\'s 5.0 MPa row above 50 bar) and THE start-level lift h_s(T) of the ECU table.\n\n'
           '| T [K] | P_sat [bar] | Purge, all liquid, two taps [g/s] | M at 2.5 s of flow [g] | M at 2.60 s of flow [g] | Cold-flow bound, map lift [N] | Cold-flow bound at h_s [N] | h_s(T) [mm] |\n'
           '|---|---|---|---|---|---|---|---|\n%s\n\n'
           'Reading: the 2.5 s schedule stays <= 76 g up to %.2f K; the 2.55 s cap (2.60 s of flow) is at 76 g at 289.5 K and above it at any '
           'warmer state, reaching 80 g at %s; the cold-flow bound stays below the 16.31 N margin up to 298.15 K. The 297.15 K row is the 24 C '
           'ARM limit, the upper bound of the relight state while the modelled tank does not warm over the coast.\n\n'
           'Table 15.15c. A1-profile statements of v2.4b.\n\n'
           '| ID | Topic | Basis (300 m / 285 m) | Direction at about 210 m | Status |\n|---|---|---|---|---|\n%s\n\n'
           'Line 208 (read; cross-references, no Combustion change):\n- %s\n- %s\n- %s\n\n'
           'Missing: %s.\n') % (SCR['a1_profile_line213_v2p4b.json'][0], SCR['a1_profile_line213_v2p4b.json'][1],
                                A1S['coast_T_change_max_K'], _r15a, A1P['method'], _r15b, A1P['T_at_76g_2p5s_K'],
                                ('%.2f K' % A1P['T_at_80g_2p60s_K']) if not isinstance(A1P['T_at_80g_2p60s_K'], str) else A1P['T_at_80g_2p60s_K'],
                                _r15c, _x208['dip_onset'], _x208['purge_80g'], _x208['not_adopted'], '; '.join(A1['missing']))
text = text.rstrip('\n') + sec1515
open(out, 'w', encoding='utf-8').write(text if text.endswith('\n') else text + '\n')
print('edits', N[0], 'lines', text.count('\n') + 1)
print('wrote', out, sha(out))
