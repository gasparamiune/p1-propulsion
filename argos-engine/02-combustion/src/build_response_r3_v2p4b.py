"""REVISION-RESPONSE-R3.md: Combustion's item-by-item answer to REV-COMB-3 (Combustion v2.4b, 2026-10-13; final fold 2026-10-19, §9).

Every reference is resolved at build time to a 1-based line of the published file: an anchor string that must occur the stated number
of times in REPORT.md / the specifications, or a key path in combustion.json (as written, indent 1).  Hashes of the reviewed and the
answering files are asserted or recorded.  The author's statement only; the verdict belongs to a different reviewer.
usage: python -I build_response_r3_v2p4b.py REVIEW_R3 REPORT_V24B COMBUSTION_JSON_V24B SPEC_T1T4 SPEC_CF4 DATA_V2P4B_DIR OUT_MD DATASHEET_MD
"""
import hashlib, json, os, sys
sys.dont_write_bytecode = True
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
rev_f, rep_f, cj_f, spec_t, spec_c, dd, out, ds_f = sys.argv[1:9]
assert sha(rev_f) == 'a786101f28d45d6f', 'not REV-COMB-3'
CJ = json.load(open(cj_f)); assert CJ['version'] == 'v2.4b'
assert CJ['specs_v2p4b']['v']['02-combustion/CF-4-SPEC.md']['sha256_16'] == sha(spec_c)
assert CJ['specs_v2p4b']['v']['02-combustion/T1-T4-REGRESSION-SPEC.md']['sha256_16'] == sha(spec_t)
TXT = {'REPORT.md': open(rep_f, encoding='utf-8').read().split('\n'),
       'T1-T4-REGRESSION-SPEC.md': open(spec_t, encoding='utf-8').read().split('\n'),
       'CF-4-SPEC.md': open(spec_c, encoding='utf-8').read().split('\n')}
assert 'Version 2.4b, 2026-10-19' in TXT['REPORT.md'][2], 'REPORT is not the v2.4b final fold'
assert CJ['datasheet_inputs_v2p4b']['v']['sha256_16'] == sha(ds_f)
JL = open(cj_f, encoding='utf-8').read().split('\n')
A1 = json.load(open(os.path.join(dd, 'a1_profile_line213_v2p4b.json')))
LI = json.load(open(os.path.join(dd, 'lead_items_203_205_v2p4b.json')))


def L(fname, anchor, nth=1, count=1):
    hits = [i + 1 for i, x in enumerate(TXT[fname]) if anchor in x]
    assert len(hits) == count, (fname, anchor, hits)
    return '`%s:%d`' % (fname, hits[nth - 1])


def JK(path):
    """Line of a key path (dot-separated dict keys) in combustion.json as written with indent=1."""
    o = CJ
    for k in path.split('.'):
        assert isinstance(o, dict) and k in o, (path, k)
        o = o[k]
    pos = 0
    for depth, k in enumerate(path.split('.'), start=1):
        pat = ' ' * depth + json.dumps(k) + ':'
        for i in range(pos, len(JL)):
            if JL[i].startswith(pat):
                pos = i
                break
        else:
            raise KeyError(path)
    return '`combustion.json:%d` (`%s`)' % (pos + 1, path)


R_ = lambda a, **k: L('REPORT.md', a, **k)
T_ = lambda a, **k: L('T1-T4-REGRESSION-SPEC.md', a, **k)
C_ = lambda a, **k: L('CF-4-SPEC.md', a, **k)
DATA = lambda f: '`data/v2p4b/%s` (`%s`)' % (f, sha(os.path.join(dd, f)))
pb = LI['item1_purge_basis']['vented_mass_g']
k260 = [k for k in pb if k.startswith('2.60 s')][0]

items = [
    ('R3-01', 'MAJOR', 'ADDRESSED',
     'The "E2 + 0.22 s" hold came from one state; the lead withdrew it (194 (3)). Table 2.18 now gives the hold over all 2160 PURGE NOT RUN '
     'records by command profile: 0.30 s at zero residual on the 2500 N/s ramp to 200 N (0.31 s with the 10 ms frame margin), 0.19 s on the '
     'ramp to 500 N, and none inside W with the flow held (0.75 s). Counted from the ECU E2 the holds move by at most +14.7 ms. The '
     'per-record classes of all three profiles are published as data; the unpurged alternative is NOT ADOPTED (204 (2)).',
     [R_('**Release hold (R3-01;'), R_('Table 2.18.', nth=1, count=2), R_('### 15.5 '), R_('### 15.6 '), R_('| "E2 + 0.22 s" release hold'),
      JK('release_hold_v2p4b'), JK('drogue_release_hold.v.line175_5_note_v2p4a_superseded'), DATA('release_hold_v2p4b.json'),
      DATA('release_hold_records_v2p4b.csv')]),
    ('R3-02', 'MAJOR', 'ADDRESSED; CONTRADICTION KEPT (OI-41)',
     'Head and aft equivalent-pressure spectra to 50 ms on the 896 FA-1 cases, dense below 1 ms; the load rule carries the period domain of '
     'LEAD 194 (1). The dense all-case values exceed the 194 (1) numbers below 1 ms (93.6 bar abs at T <= 0.1 ms against 90; 120.3 bar abs '
     'at 0.1-1 ms against 93 / 102; baseline 88.6 and 102.5). Kept for the lead (OI-41).',
     [R_('**FA-1 spectra (R3-02'), R_('Table 7.6c.'), R_('| OI-41 |'), R_('| Line 173 "90 bar for every part"'), JK('fa1_spectra_v2p4b'),
      JK('fa1_envelope_v2p4a.v.structural_load_LEAD_173_superseded'), DATA('fa1_spectra_dense_v2p4b.json')]),
    ('R3-03', 'MINOR', 'ADDRESSED',
     'Long-period thrust spectrum published (all cases, Cf 1.35: 1743 N at 25 ms, 1452 N at 40 ms, 1032 N at 100 ms). The 1.8 kN x 4 ms '
     'rectangle bounds T <= 20 ms (minimum ratio 1.077); the spectrum governs above it (LEAD 194 (2)).',
     [R_('Table 7.6d.'), JK('fa1_spectra_v2p4b'), DATA('fa1_thrust_spectra_dense_v2p4b.csv')]),
    ('R3-04', 'MINOR', 'ADDRESSED by LEAD 194 (1); see OI-41',
     'Line 194 (1) replaced 92 by 93 bar abs (yield) with 102 bar abs (ultimate) for 0.1-1 ms paths. The dense 0.1-1 ms values '
     '(baseline 102.5, all cases 120.3 bar abs) lie above 93; recorded in OI-41.',
     [R_('replaced 92 by 93 bar abs (R3-04)'), R_('| OI-41 |')]),
    ('R3-05', 'MINOR', 'ADDRESSED (closure is physical: CF-3)',
     'The 16.31 N margin is stated CONDITIONAL on Cd x A x G at the start lift (factor 1.22-1.31). CF-3 start-lift acceptance: F <= 16.31 N '
     'minus the heat allowance, or mdot <= 52.6-56.3 g/s with no heat allowance.',
     [R_('**CONDITIONAL margin.**'), R_('| OI-38 |'), JK('cold_flow_start_lift_v2p4b'), DATA('cold_flow_start_lift_v2p4b.json')]),
    ('R3-06', 'MINOR', 'ADDRESSED',
     'T1-T4 v3: the flux test is two-sided; a signature below the oxidiser-flux band reads "neither shown" (LEAD 194 (8)).',
     [T_('**Signature below the oxidiser-flux band** (S_meas < S_ox - 1.645 σ(S) on a T3 hold)'), T_('## 2. Decision rule'),
      JK('t1t4_law_v2.v.spec_superseded'), JK('specs_v2p4b')]),
    ('R3-07', 'MINOR', 'ADDRESSED; stand tank MISSING',
     'T1-T4 v3 adds red lines and aborts, validity of short or aborted firings, the char and melt-layer procedure, and counts and N2O '
     '(T1 at 2t = 8 s uses 1.928 kg, 96.4 % of a 2.0 kg flight load; 2t <= 6.04 s on a flight-size tank). The founders\' stand tank is MISSING.',
     [T_('## 11. Run rules'), T_('## 12. Validity'), T_('## 13. Char'), T_('## 14. Counts and N2O budget'), DATA('test_budgets_v2p4b.json')]),
    ('R3-08', 'MINOR', 'ADDRESSED; model numbers on CAD v3.4.1 until the v3.5.1 purge re-run',
     'CF-4 v2.1: §1 states the decided commit rule; the hardware baseline is the frozen v3.5.1 bleed path; §4.1 IS-1 to IS-3 preparation and '
     'verification; §5.1 the continuous-liquid probe threshold; §9.1 red lines; §12 runs and N2O (59 / 75 / 105 runs, 10.0 / 12.7 / 17.8 kg).',
     [C_('Changes in v2.1'), C_('### 4.1 Preparation'), C_('### 5.1 What "continuous liquid" means'), C_('### 9.1 Red lines'),
      C_('## 12. Run and N2O budget'), JK('cf4_gate.spec_version_superseded')]),
    ('R3-09', 'MINOR', 'ADDRESSED',
     'Line 181 (2): "the 0.81 s plan holds" is scoped to the predictor path with PURGE committed. Line 181 (4): ABORT at t_E2 + 0.5 s. '
     'Line 177 (1)/178: H19 is recomputed for the Inconel 718 lip (lumped 1.10-5.88 s from 342 C; 1 mm depth 5.21-33.92 s).',
     [R_('6. **The 0.81 s plan holds on the predictor path'), R_('t_E2 + 0.5 s'), R_('**Lip melt if the leak impinges**'), R_('| H19 |'),
      JK('nozzle_lip_melt_in718_v2p4b'), JK('nozzle_joint.v.lip_melt_s_superseded'), DATA('nozzle_lip_melt_in718_v2p4b.json')]),
    ('R3-10', 'MINOR', 'ADDRESSED',
     'Stand dynamic Pc channel: range >= 100 bar abs; proof >= 112 bar abs flush-mounted (103 needed), >= 132 bar abs for a 0.1-1 ms path; a '
     'path period above 1 ms is not acceptable (LEAD 194 (7)).',
     [R_('**Stand dynamic Pc channel (R3-10', nth=1, count=2), R_('| OI-34 |'), JK('pc_dynamic_channel.v.stand_proof_rating_v2p4b')]),
    ('R3-11', 'NOTE', 'ADDRESSED',
     'Every item of review §7 (ii) is replaced: the PROVISIONAL rule by L* = 1.3 s; OI-31 closed; OI-38 adopted with the margin CONDITIONAL; '
     'OI-40 decided; the configuration notes updated. Old values are kept under `*_superseded` keys and in REPORT §13.',
     [R_('**PURGE commit rule.** v2.4a carried'), R_('| OI-31 |'), R_('| OI-38 |'), R_('| OI-40 |'), R_('**Configuration.** v2.4b'),
      JK('purge_commit_rule_v2p4a.v.rule_LEAD_175_3_superseded'), JK('fmea_input.v.bleed_superseded'),
      JK('fmea_input.v.flameout_pc_invalid_v2p4a_superseded'), JK('cold_flow_thrust_v2p4a.v.proposal_superseded'),
      JK('throat_insert_line183_note_v2p4a.v_superseded'), C_('Changes in v2.1')]),
    ('R3-12', 'NOTE', 'ADDRESSED',
     'The release is read on the firmware release term (Pc valid and >= 3.0 bar abs) with the ECU\'s relative E2 rule (§15.5); the lift basis '
     'is one definition, THE start-level lift h_s(T) (§15.3).',
     [R_('[v2.4b, R3-12:'), R_('### 15.3 '), R_('### 15.5 '), JK('E2_rule_v2p4b'), JK('start_level_lift_v2p4b')]),
    ('R3-13', 'NOTE', 'ADDRESSED',
     'The population statements are counted per command profile.',
     [R_('**Population statements (R3-13).**'), R_('[v2.4b, R3-13:'), DATA('population_statements_v2p4b.json')]),
    ('R3-14', 'NOTE', 'ADDRESSED; injector-body temperature TO-VERIFY',
     'The heat that matters is added at tank pressure (injector-body and feed soak-back at the relight). The R2 lit thrust is the grain_q1d '
     'start-level history (Table 7.3b: 33.1-71.0 N between E2 and E2 + 0.5 s at 0.21776 mm, 3 of 72 corners below 37.16 N), not 62.5 N x pcf_k.',
     [R_('- **Heat location (R3-14).**'), R_('Table 7.3b.'), JK('cold_flow_thrust_v2p4a.v.line194_4_heat_location_v2p4b'),
      JK('start_level_lit_thrust_v2p4b'), JK('drogue_release_hold.v.line194_4_lit_history_v2p4b')]),
    ('R3-15', 'NOTE', 'ADDRESSED; consequence recorded for the lead',
     'The prediction is a script and parameters hashed before the firing; only the logged inputs come from the firing. Consequence: at the '
     'literature erosion rate, firing 1 would count as a refutation (8.4-13.6 % against 1.9 % predicted).',
     [R_('### 15.12 '), R_('| OI-48 |'), T_('## 15. Throat check'), JK('nz01_criterion_v2p4b')]),
    ('R3-16', 'NOTE', 'ADDRESSED',
     'Wording per LEAD 194 (5): 766 g remains at the end of the purge flow, 9.3-9.7x the 78.6-82.5 g that 13.6 mm holds.',
     [R_('766 g remains at the end of the purge flow', nth=2, count=3), R_('| "About x9 margin"'),
      JK('tank_outlet_coverage_v2p4a.v.min_liquid_for_quasistatic_coverage_g.margin_superseded')]),
    ('R3-17', 'NOTE', 'ADDRESSED; outlet geometry MISSING (OI-32)',
     'Dip onset by thrust level (Lubin-Springer, LITERATURE; N2O applicability TO-VERIFY): 60.3-62.0 g at 125 N, 67.9-69.9 g at 250 N, '
     '78.3-80.6 g at 500 N (283-289.5 K). GNC fixed its onset at 80 g (LEAD 208 (1)).',
     [R_('Table 2.4b.'), R_('### 15.11 '), JK('tank_outlet_dip_v2p4b'), DATA('tank_outlet_dip_v2p4b.json')]),
]
r2 = [
    ('R2-03', 'PARTLY', 'ADDRESSED through R3-02 and R3-03', 'Pressure spectrum to 50 ms; thrust domain stated (LEAD 194 (2)).', [R_('Table 7.6c.'), R_('Table 7.6d.')]),
    ('R2-09', 'PARTLY', 'ADDRESSED through R3-09', 'The 316L lip text is replaced by the IN718 values.', [R_('**Lip melt if the leak impinges**')]),
    ('R2-11', 'PARTLY', 'PARTLY', 'The design value follows LEAD 194 (1) (R3-04); the 1-D FA-1 run stays OPEN (OI-36).', [R_('| OI-36 |')]),
    ('R2-13', 'CONFIRMED (notes stale)', 'ADDRESSED through R3-11', 'Configuration paragraph rebuilt.', [R_('**Configuration.** v2.4b')]),
    ('R2-01, R2-02, R2-04 to R2-08, R2-10, R2-12', 'CONFIRMED or CLOSED', 'No change', 'R2-04\'s new defects are R3-06 and R3-07; R2-10\'s channel '
     'range is R3-10; OI-33 stays open (R2-07).', [R_('| OI-34 |')]),
]
LD = CJ['lead_decisions_folded_v2p4b']['v']
relay = [
    ('203-204 item 1', 'Purge flow basis (SIL 32.0 vs 29.8 g/s); vented mass at 2.5 s and at the 2.55 s cap',
     'Neither constant rate: record basis M(2.5 s) <= %.2f g; %.2f g at 2.60 s of flow (the 2.55 s both-open cap with the 0.05 s offset), at '
     'the 76 g limit (OI-42). Line 216 (5) then asked for ONE basis: 29.25 g/s (§9).' % (pb['2.50 s flow (nominal schedule)']['combustion_bound_open_g'], pb[k260]['combustion_bound_open_g']),
     [R_('### 15.9 '), R_('| OI-42 |'), JK('purge_basis_v2p4b')]),
    ('203-204 item 2', 'THE start-level lift', 'h_s(T) = the ignition-lift row at the E0 tank temperature: 0.2039 mm at 20 C, 0.21776 mm at the '
     'A1 relight state; the ECU hold lift 0.2154 mm is retired (OI-43).', [R_('### 15.3 '), R_('| OI-43 |'), JK('start_level_lift_v2p4b')]),
    ('203-204 item 3', 'E2 model against the ECU relative rule', 'The ECU E2 is earlier than the model E2 by at most 14.7 ms; holds from the '
     'ECU E2 are given (OI-44).', [R_('### 15.5 '), R_('| OI-44 |'), JK('E2_rule_v2p4b')]),
    ('203-204 item 4', 'Source text for 2500 N/s, 0.5 s, 5 bar abs and 0.12 s; FLAMEOUT_OPT in the cold_flow text', 'Written (OI-46).',
     [R_('### 15.10 '), R_('| OI-46 |'), JK('firmware_constant_sources_v2p4b')]),
    ('203-204 item 5', 'FA-1 head spectrum near 6 ms; histories beyond 25 ms', 'Values near 6 ms and the history limits are given; the head '
     'stays at 3.78-22.13 bar after 25 ms.', [R_('### 15.7 '), JK('fa1_spectra_v2p4b')]),
    ('203-204 item 6', 'Per-record classes for the 500 N ramp', 'Published as data for all three profiles (the alternative is NOT ADOPTED).',
     [R_('### 15.6 '), JK('release_hold_v2p4b')]),
    ('203-204 item 7', 'A1_none p99 8.375 s against the 8.258 s cycle', 'No A1 statement changes (web >= 4.24 mm; B1 governs).',
     [R_('### 15.13 '), JK('a1_duration_note_v2p4b')]),
    ('205', 'Gas sound speed in the Pc port passage at the FA-1 instant', 'c >= 181 m/s if the passage holds no liquid N2O (near-critical '
     'N2O); 202 m/s for N2O compressed from saturation; products 1049-1136 m/s. Combustion cannot bound c better than 222-400 m/s in the '
     'direction that matters; the gas-filled lower end is below 222 m/s and two-phase N2O is unbounded (OI-45).',
     [R_('### 15.8 '), R_('| OI-45 |'), JK('pc_port_gas_v2p4b')]),
    ('213', 'A1 apogee target about 210 m (founder decision; DECIDED by 214, 227 (1))', 'The 300 m and 285 m A1 values are kept as comparators; no 210 m record yet. '
     'Directions: the A1 duty cycle does not shorten (line 227 (9), RV6-05, corrects 213); warmer relight state at the same launch temperature, so the purge mass rises by about %.2f g per K '
     'above 289.5 K (76 g on the 2.5 s schedule up to %.2f K) and the start-level cold-flow bound rises (below 16.31 N to 298.15 K) (OI-49).'
     % (A1['purge_scaling']['M_2p5s_slope_g_per_K'], A1['purge_scaling']['T_at_76g_2p5s_K']),
     [R_('14. **A1 apogee target'), R_('### 15.15 '), R_('| OI-49 |'), C_('A1 profile (LEAD lines 213'), JK('a1_apogee_target_v2p4b'),
      DATA('a1_profile_line213_v2p4b.json')]),
]


FD = CJ['fa1_spectra_damped_v2p4b']['v']; PBN = CJ['purge_basis_line216_v2p4b']['v']; PMV = dict(CJ['fa1_per_mode_peq_v2p4b']['v'])
P4V = CJ['p4c_lit_side_v2p4b']['v']; TKC = CJ['tank_2p20kg_option_v2p4b']['v']
_tdb = PMV['time_domain_bound_all_case']['TC01_JFWD']
PMV['jfwd_tdb0'] = max(_tdb['zeta0|s%.2f' % s]['TH_upper_bar_abs'] for s in (1.0, 0.9, 0.85))
PMV['jfwd_tdb2'] = max(_tdb['zeta0.02|s%.2f' % s]['TH_upper_bar_abs'] for s in (1.0, 0.9, 0.85))
PMV['jfwd_er0'] = max(_tdb['zeta0|s%.2f' % s]['E_rule_upper_bar_abs'] for s in (1.0, 0.9, 0.85))
_sg = PMV['jfwd_spectral_sums_bar_abs']['zeta0']
PMV['sg0'] = '%.1f-%.1f' % tuple(_sg['signed']); PMV['ab0'] = '%.1f-%.1f' % tuple(_sg['ABS']); PMV['sr0'] = '%.1f-%.1f' % tuple(_sg['SRSS'])
CQJ = FD['proposal']['consequence_TC01_JFWD']
assert _sg['ABS'][0] > PMV['jfwd_breakeven_bar_abs']['yield_'] and CQJ['rule_b_E_rule']['P_bar_abs'] > PMV['jfwd_breakeven_bar_abs']['yield_']
_c210 = TKC['cases_2p00kg_210m']['cases']
TKV = dict(a1_210=max(c['erosion_nominal_dAt_pct'] for c in _c210.values()),
           max_220=max(c['erosion_nominal_dAt_pct'][1] for c in TKC['cases'].values()))
_hb = FD['head_all_band_maxima_bar_abs']
fold = [
    ('2026-10-19 item 1', 'FA-1 spectra as data (head / aft, T 0.02-50 ms, zeta 0 / 0.02 / 0.05, baseline and all cases; thrust >= 200 ms); state the '
     'contradiction with 194 (1); restated band values or a per-mode rule',
     'Published as CSV and JSON. Head, all cases, zeta 0: %.1f bar abs at T <= 0.1 ms (194 (1): 90) and %.1f at 0.1-1 ms (%.1f at zeta 0.02; 194 (1): 93 / '
     '102): the band values are below the all-case spectrum. Proposed: %d / %d / %d / %d bar abs, or the per-mode rule (time-domain modal bound; E rule until '
     'the share vector).' % (_hb['T_le_0p1ms']['zeta0'], _hb['T_0p1_to_1ms']['zeta0'], _hb['T_0p1_to_1ms']['zeta0.02'],
                             FD['proposal']['band_values_bar_abs']['T_le_0p1ms'], FD['proposal']['band_values_bar_abs']['T_0p1_to_1ms'],
                             FD['proposal']['band_values_bar_abs']['T_1_to_20ms'], FD['proposal']['band_values_bar_abs']['T_20_to_50ms']),
     [R_('### 16.2 '), R_('### 16.3 '), R_('| OI-41 |'), JK('fa1_spectra_damped_v2p4b'), DATA('fa1_pressure_spectra_published_v2p4b.csv'),
      DATA('fa1_pressure_spectra_modal_periods_v2p4b.csv'), DATA('fa1_spectra_damped_v2p4b.json'), DATA('fa1_thrust_spectra_dense_v2p4b.csv')]),
    ('2026-10-19 item 2; line 228 (c)', 'TC-01 per-mode Peq = sum share_i x S(T_i) at J-FWD and LC1; zeta 0 and a justified damping; absolute sum and SRSS; '
     'x0.85 / 0.90 / 1.00; residual at the maximum below 0.195 ms; TC-02 / TC-09 / NZ-01 if cheap; say what is missing',
     'J-FWD, zeta 0, worst factor: signed %s, absolute %s, SRSS %s bar abs (intervals: %d of 60 shares published); time-domain modal bound %.1f (%.1f at zeta '
     '0.02, ASSUMED), E rule %.1f; break-even %.1f / %.1f. Missing: the FEA3D 60-mode share vector per node (OI-51). TC-02, TC-09, NZ-01: spectral sums '
     'given.' % (PMV['sg0'], PMV['ab0'], PMV['sr0'], PMV['shares_published_jfwd']['n_known'], PMV['jfwd_tdb0'], PMV['jfwd_tdb2'], PMV['jfwd_er0'],
                 PMV['jfwd_breakeven_bar_abs']['yield_'], PMV['jfwd_breakeven_bar_abs']['ult']),
     [R_('### 16.4 '), R_('| OI-51 |'), R_('| OI-52 |'), JK('fa1_per_mode_peq_v2p4b'), DATA('fa1_per_mode_peq_v2p4b.json'), DATA('fa1_modal_th_bound_v2p4b.json'),
      DATA('fa1_relative_spectrum_E_v2p4b.csv')]),
    ('2026-10-19 item 3', 'GNC P4c lit side and the pcf_tmax proposal, as data with tags',
     'At %.5f mm: F min %.2f N in the 0.5 and 0.8 s windows; %d of 72 corners never reach 37.16 N, the others by E2 + %.3f s (+3 frames %.3f s); '
     'pcf_tmax 0.8 s is not limited by the lit side.' % (P4V['lift_mm'], P4V['F_min_N']['lift_0p21776mm'], P4V['corners_never_37p16N_0p8s']['lift_0p21776mm'],
                                                         P4V['latest_crossing_37p16N_s']['lift_0p21776mm'][0], P4V['latest_crossing_37p16N_s']['lift_0p21776mm'][1]),
     [R_('### 16.7 '), JK('p4c_lit_side_v2p4b'), DATA('p4c_lit_side_v2p4b.json')]),
    ('2026-10-19 item 4; 219, 227 (9)', '2.20 kg tank: B1 / thermal / erosion impact if cheap, else an open item with an owner',
     'First-order A1 estimate (no run): nominal throat-area growth up to %.2f %% per flight; B1 with 2.20 kg not covered: OI-50 (GNC records; Combustion '
     're-run; Mechanical tank / structure).' % TKV['max_220'],
     [R_('### 16.8 '), R_('| OI-50 |'), JK('tank_2p20kg_option_v2p4b'), DATA('tank_2p20kg_option_v2p4b.json')]),
    ('2026-10-19 item 5', 'out_v2p4b/DATASHEET-INPUTS-COMBUSTION.md: one table of the headline engine numbers with tags',
     'Published (`02-combustion/DATASHEET-INPUTS-COMBUSTION.md`).', [R_('### 16.9 '), JK('datasheet_inputs_v2p4b')]),
    ('216 (5)', 'ONE purge flow basis (g/s) with derivation and uncertainty',
     '%.2f g/s = 76 g / %.4f s of flow at 289.5 K; %.2f-%.2f g/s over the relight states; measured-time cap after CF-4.' % (
         PBN['mdot_g_s'], PBN['t76_flow_s'], PBN['uncertainty_g_s']['tank_state_283p15_to_297p15K'][0], PBN['uncertainty_g_s']['tank_state_283p15_to_297p15K'][1]),
     [R_('### 16.5 '), R_('| OI-42 |'), JK('purge_basis_line216_v2p4b'), JK('purge_basis_v2p4b.v.answer_superseded'), C_('Flow basis (LEAD 216 (5))'),
      DATA('purge_basis_line216_v2p4b.json')]),
    ('216 (9)', 'the start-level lift as a LIFT value at the A1 relight state', '%.5f mm (ECU table row, DESIGN; model -0.056 %%); TO-VERIFY at CF-3.' % P4V['lift_mm'],
     [R_('### 16.6 '), R_('- LEAD line 216 (9) (final fold)'), JK('start_level_lift_v2p4b.v.line216_9')]),
    ('214, 227 (1), 227 (9)', 'A1 = 210 m decided; "A1 duty cycle shortens" corrected (RV6-05)', 'A1 values stay comparators; corrected in place; first-order values.',
     [R_('### 16.8 '), R_('| OI-49 |'), JK('a1_apogee_target_v2p4b.v.target.lead_consequences_superseded'), JK('a1_duration_note_v2p4b.line213_note_superseded')]),
    ('215-228 (other)', 'read for status', 'Folded or read as listed.', [R_('### 16.1 '), JK('final_fold_v2p4b')]),
]


def table(rows, head):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    for r in rows:
        out.append('| ' + ' | '.join(list(r[:-1]) + ['; '.join(r[-1])]) + ' |')
    return '\n'.join(out)


ld_rows = '\n'.join('| %s | %s |' % (k, v) for k, v in LD.items())
x208 = A1['line208_cross_references']
doc = f'''# REVISION-RESPONSE-R3: Combustion v2.4b answer to REV-COMB-3

Version v2.4b, 2026-10-19 (staged 2026-10-13; final fold of LEAD lines 214-228 and the lead requests of 2026-10-19 in §9). Author: Combustion and Propulsion. Answers `reviews/REVIEW-COMBUSTION-R3.md` (REV-COMB-3, REVISE (targeted),
`{sha(rev_f)}`) on REPORT v2.4a (`062e307a8d25e1ec`). Answering files (sha256/16): `02-combustion/REPORT.md` v2.4b (`{sha(rep_f)}`),
`interfaces/combustion.json` v2.4b (`{sha(cj_f)}`), `02-combustion/CF-4-SPEC.md` v2.1 (`{sha(spec_c)}`),
`02-combustion/T1-T4-REGRESSION-SPEC.md` v3 (`{sha(spec_t)}`), `02-combustion/DATASHEET-INPUTS-COMBUSTION.md` (`{sha(ds_f)}`), data in `02-combustion/data/v2p4b/` (`HASHES.txt`). References are
1-based lines of those files, resolved by `src/build_response_r3_v2p4b.py` at build time (combustion.json as written, indent 1).

This is the author's statement. A reviewer other than the author records criteria and verdict. Status words: ADDRESSED (changed as asked
or as the lead decided); CONTRADICTION KEPT (a remaining disagreement recorded for the lead); PARTLY / OPEN (data or a decision outside
Combustion is needed). No test, hash match or rendered table here is physical approval.

## 1. Findings R3-01 to R3-17

{table(items, ['Item', 'Severity', 'Status', 'Change', 'Where'])}

## 2. R2 items (review §2)

{table(r2, ['Item', 'R3 status', 'v2.4b status', 'Change', 'Where'])}

## 3. Review §6 and §7

- §6 (1)-(5): the line-186 decisions are folded as decided; the GNC alternative hold is withdrawn (194 (3)); the parenthetical that described
  LO only is restated per profile (R3-13); the heat location is corrected (R3-14); the NZ-01 prediction is frozen (R3-15); the outlet
  wording follows 194 (5) (R3-16). §6 (4): mechanical.json v2.2 is not yet in the hub (v2.1 read; OI-37).
- §7 (i): R3-09. §7 (ii): R3-11. The review found no stale "300 m" hit in v2.4a; after LEAD line 213 the A1 values are labelled as
  300 m / 285 m comparators ({R_('### 15.15 ')}).

## 4. Lead lines folded ({JK('lead_decisions_folded_v2p4b')}; REPORT {R_('### 15.1 ')})

| Line | Fold |
|---|---|
{ld_rows}

## 5. Coordinator relays: lines 203-204 (items 1-7), 205 and 213

{table(relay, ['Relay', 'Question', 'Answer', 'Where'])}

Line 208 (read; cross-references, no Combustion change): {x208['dip_onset']}. {x208['purge_80g']}. {x208['not_adopted']}.

## 6. Points for the lead

1. OI-41: the published all-case FA-1 spectrum exceeds the 194 (1) values below 1 ms ({R_('### 16.2 ')}); the lead's flight Pc proof of 112 bar abs
   (1.1 x 102) becomes 132 bar abs on the all-case 0.1-1 ms value. Proposed ({R_('### 16.3 ')}): restated band values {FD['proposal']['band_values_bar_abs']['T_le_0p1ms']} / {FD['proposal']['band_values_bar_abs']['T_0p1_to_1ms']} / {FD['proposal']['band_values_bar_abs']['T_1_to_20ms']} / {FD['proposal']['band_values_bar_abs']['T_20_to_50ms']} bar abs, or the
   per-mode rule (E rule until FEA3D's share vector, OI-51). Which applies is the lead's call.
2. OI-42: ONE flow basis {PBN['mdot_g_s']:.2f} g/s (line 216 (5)); the 2.55 s both-open cap gives 76.05 g on the Combustion bound; a strict 76 g needs
   both-open <= {PBN['cap_overlap_s']:.3f} s until CF-4 / B-BLEED-1 measure the flow (then overlap <= 76 g / mdot_measured - (t_close - t_open)). The bleed
   Cd is ASSUMED (+-0.7 g per 1 %).
3. Release hold for GNC P6c: 0.30 s is the zero-residual value on the ramp to 200 N; Table 2.18 lists 0.31 s with the 10 ms frame margin.
   The alternative is NOT ADOPTED, so this matters only if GNC flies the comparator.
4. NZ-01 (R3-15): under the decided rule, an erosion at the literature rate on firing 1 counts as a refutation (a conservative false
   refutation), recorded, not changed.
5. Lines 213 / 214: at the same launch temperature a 210 m relight state is warmer than the 289.5 K basis; the purge mass then rises by about
   {A1['purge_scaling']['M_2p5s_slope_g_per_K']:.2f} g per K and the 2.55 s cap, already at 76 g, exceeds it. GNC's 210 m record settles the
   magnitude (OI-49).
6. Line 208 (1): GNC's fixed onset of 80 g is inside the 500 N bracket at 283-289.5 K (78.3-80.6 g) and below the 270 K row (82.9-83.6 g);
   the 300 m records end the landing burn at {A1['comparators_300m_summary']['T_end_landing_K'][0]:.2f}-{A1['comparators_300m_summary']['T_end_landing_K'][1]:.2f} K. Whether 80 g bounds the onset depends on the
   thrust when the liquid runs low (GNC).
7. The IN718 datasheet PDF could not be archived: the proxy refused the download from www.specialmetals.com; the values were read through
   the web-fetch reader (OI-47).
8. Line 228 (c): at TC-01 J-FWD the time-domain modal bound is {PMV['jfwd_tdb0']:.1f} bar abs undamped against the {PMV['jfwd_breakeven_bar_abs']['yield_']:.1f} / {PMV['jfwd_breakeven_bar_abs']['ult']:.1f} bar abs
   break-even (MS {CQJ['rule_b_time_domain_bound']['MS_yield']:+.3f} / {CQJ['rule_b_time_domain_bound']['MS_ult']:+.3f}; it holds the yield margin while the residual's absolute share is <= {PMV['jfwd_bound_residual_caveat']['residual_abs_share_limit_for_yield']:.3f}
   against its published signed {PMV['jfwd_bound_residual_caveat']['residual_signed_share']:.3f}); its E-rule form {CQJ['rule_b_E_rule']['P_bar_abs']:.1f} and the absolute spectral sum ({PMV['ab0']}) exceed the yield break-even. With the restated
   band value {CQJ['band_a']['P_bar_abs']} bar abs J-FWD reads MS {CQJ['band_a']['MS_yield']:+.3f} / {CQJ['band_a']['MS_ult']:+.3f} (line 228 lists +0.25 / +0.23 on 93 / 102). The signed spectral sum is an
   interval ({PMV['sg0']}) because FEA3D publishes {PMV['shares_published_jfwd']['n_known']} of 60 shares (OI-51); damping is ASSUMED (OI-52).
9. Line 227 (9): the A1 duty cycle does not shorten; first order the nominal A1 throat-area growth is {TKV['a1_210']:.2f} % per flight at 210 m
   (2.00 kg) and up to {TKV['max_220']:.2f} % with the 2.20 kg option, above the NZ-01 2 % criterion (OI-40, OI-50).

## 7. Failures kept as evidence

- Lead-items script, first runs: a format-string error; then no N2O thermal-conductivity model in CoolProp (fixed with an ASSUMED 0.10 W/m K
  upper bound, recorded); then a Pc-passage minimum taken at two pressures only (201 m/s), replaced by the dense minimum (181 m/s) before
  any value was used.
- Population-statement script: a lining-label mismatch (division by zero); fixed by matching the CSV label.
- Interface writer: a first build dropped sub-keys of replaced dicts; fixed so every v2.4a key is kept (3227 of 3227).
- Report builder: a literal percent sign in a formatted string; fixed before output.
- Line-213 patch: a first patch of the interface writer named a line that was not duplicated; no output was written; re-applied.

## 8. Checkpoint

The full checkpoint (claim, configuration, sources, files, tests, unknowns, next closure) is in REPORT §0 ({R_('**Configuration.** v2.4b')}
and the paragraphs around it). Nothing here is physical approval.

## 9. Final fold (2026-10-19): lead lines 214-228 and the lead requests of 2026-10-19

{table(fold, ['Item', 'Request', 'Answer', 'Where'])}
'''
open(out, 'w', encoding='utf-8').write(doc)
print('wrote', out, sha(out), 'lines', doc.count('\n') + 1)
