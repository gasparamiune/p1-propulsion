#!/usr/bin/env python3
"""build_specs_v2p4b.py - T1-T4-REGRESSION-SPEC v3 and CF-4-SPEC v2.1 (Combustion v2.4b) from the published v2 / v2.0 by asserted edits.

REV-COMB-3 R3-06, R3-07, R3-08, R3-10, R3-15; LEAD CHANGELOG lines 186 (1), 194 (3), (5), (7), (8).
Numbers come from the hash-asserted data files: test_budgets_v2p4b.json (counts, N2O, probe dropout, P1 lift basis) and
release_hold_v2p4b.json (hold table).  Every literal edit must match exactly once.
usage: python -I build_specs_v2p4b.py T1T4_V2_MD CF4_V2_MD TEST_BUDGETS_JSON RELEASE_HOLD_JSON OUT_T1T4 OUT_CF4 LEAD_ITEMS_JSON FA1_DENSE_JSON A1_PROFILE_JSON
(LEAD_ITEMS_JSON = lead_items_203_205_v2p4b.json: THE start-level lift and the Pc-port sound speed; FA1_DENSE_JSON = fa1_spectra_dense_v2p4b.json)
"""
import hashlib, json, os, sys
sys.dont_write_bytecode = True

EXPECT = {'t1t4': 'bbf0ea642453dc7a', 'cf4': 'a94211a295fe0224', 'budgets': None, 'hold': 'a926426da0e6e436'}


def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


class Doc:
    def __init__(self, text):
        self.T = text; self.n = 0

    def rep(self, old, new, n=1):
        c = self.T.count(old)
        assert c == n, ('rep count', c, old[:100])
        self.T = self.T.replace(old, new); self.n += 1


def f1(x):
    return f'{x:.1f}'


def main(t1t4_f, cf4_f, bud_f, hold_f, out_t, out_c, items_f, dense_f, a1_f):
    assert h16(t1t4_f) == EXPECT['t1t4'], h16(t1t4_f)
    assert h16(cf4_f) == EXPECT['cf4'], h16(cf4_f)
    assert h16(hold_f) == EXPECT['hold'], h16(hold_f)
    B = json.load(open(bud_f)); HB = h16(bud_f)
    assert B['version'] == 'v2.4b'
    here = os.path.dirname(os.path.abspath(__file__))
    S_BUD = h16(os.path.join(here, 'test_budgets_v2p4b.py'))
    assert B['script_sha256_16'] == S_BUD, 'test_budgets_v2p4b.json was not written by the current script'
    HJ = json.load(open(hold_f))
    IT = json.load(open(items_f)); DN = json.load(open(dense_f)); HI_ = h16(items_f); HD_ = h16(dense_f)
    A1 = json.load(open(a1_f)); HA1 = h16(a1_f)
    assert A1['version'] == 'v2.4b' and A1['script_sha256_16'] == h16(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a1_profile_line213_v2p4b.py')), 'a1_profile_line213_v2p4b.json was not written by the current script'
    A1S = A1['comparators_300m_summary']; A1P = A1['purge_scaling']
    assert IT['version'] == 'v2.4b' and DN['version'] == 'v2.4b' and DN['smoke_test_subset'] == 0
    SLL = IT['item2_start_level_lift']['values_before_CF3']
    assert abs(SLL['A1_relight_286p70K_mm'] - 0.21776) < 1e-9 and abs(SLL['pad_20C_mm'] - 0.2039) < 1e-9
    PG = IT['item8_pc_port_gas']; c_min = PG['c_design_min_m_s']; pk_med = PG['construct_head_peak_bar']['median']; pk_max = PG['construct_head_peak_bar']['max']
    PDm = DN['period_domain']; q01 = PDm['T_le_0p1ms']['head|all']['value_bar']; q1 = PDm['T_0p1_to_1ms']['head|all']['value_bar']
    q20 = PDm['T_1_to_20ms']['head|all']['value_bar']

    # ------------------------------------------------------------------ numbers
    P = ('4.0MPa', '4.5MPa', '5.0MPa')
    K = B['kinds']
    rng = lambda key, sub: (min(K[key][p][sub] for p in P), max(K[key][p][sub] for p in P))
    per_set = [B['N2O_per_repeat_set_kg'][p] for p in P]; per_set_a = [B['N2O_per_repeat_set_with_allowance_kg'][p] for p in P]
    t1_2t = [B['T1_100pct_2t_8s_kg'][p] for p in P]
    t_max_flight = B['T1_100pct_max_2t_s_on_flight_tank']
    share = B['T1_2t_share_of_flight_load']
    dcd = B['T4_DCD']
    ser = B['series']
    cf4 = B['CF4']; pr = cf4['probe_dropout']; p1 = cf4['P1_lift_basis']
    t_lift = p1['0.20390mm']['t_lift_s']; t_lift_old = p1['0.21920mm']['t_lift_s']; p1_cmd = p1['0.20390mm']['P1_after_command_s']
    t_lift_s = p1['0.21776mm']['t_lift_s']; P1_s = p1['0.21776mm']['P1_after_lift_s']; P1_v28 = p1['0.20390mm']['P1_after_lift_s']
    assert abs(t_lift - 0.0287) < 5e-5 and abs(t_lift_old - 0.0296) < 5e-5 and p1_cmd <= 0.3225
    assert abs(P1_v28 - 0.2934) < 5e-4 and 0.27 < P1_s < 0.28 and abs(pr['lift_mm'] - 0.21776) < 1e-9

    # ================================================================== T1-T4 v3
    D = Doc(open(t1t4_f, encoding='utf-8').read())
    D.rep('# T1-T4 regression-rate measurement and law form (RG-03), v2\n',
          '# T1-T4 regression-rate measurement and law form (RG-03), v3\n')
    D.rep('Combustion v2.4a, 2026-10-13. Replaces v2.4 of this file, which is archived as `02-combustion/superseded/v2p4/T1-T4-REGRESSION-SPEC.md`. '
          'Responds to REV-COMB-2 R2-04 and to LEAD CHANGELOG line 172 (3). REPORT v2.4a §10.4 summarises this text.',
          'Combustion v2.4b, 2026-10-13. Replaces v2 (Combustion v2.4a), which is archived as `02-combustion/superseded/v2p4a/T1-T4-REGRESSION-SPEC.md`; '
          'v2 replaced v2.4 (`superseded/v2p4/`). v2 responded to REV-COMB-2 R2-04 and LEAD CHANGELOG line 172 (3); v3 responds to REV-COMB-3 R3-06, '
          'R3-07, R3-10 and R3-15 and to LEAD CHANGELOG line 194 (5), (7) and (8). REPORT v2.4b §10.4 summarises this text.')
    D.rep('Computation: `02-combustion/src/t1t4_law_resolution_v2p4a.py` (3701b74681de700b) writes `02-combustion/data/v2p4a/t1t4_law_resolution_v2p4a.json` '
          '(05b5ae5c20e04bd8). It reduces published SIM histories and re-runs no grain grid.',
          'Computation:\n'
          '- `02-combustion/src/t1t4_law_resolution_v2p4a.py` (3701b74681de700b) writes `02-combustion/data/v2p4a/t1t4_law_resolution_v2p4a.json` '
          '(05b5ae5c20e04bd8). It reduces published SIM histories and re-runs no grain grid.\n'
          f'- `02-combustion/src/test_budgets_v2p4b.py` ({S_BUD}) writes `02-combustion/data/v2p4b/test_budgets_v2p4b.json` ({HB}): the counts and '
          'N2O of §14, from the S230 throttle map (SIM) and the DC-D ground record.\n\n'
          'Changes in v3:\n'
          '- §2 and §10: the oxidiser-flux test is two-sided, and a signature below the oxidiser-flux band is "neither shown" (R3-06; LEAD line 194 (8)).\n'
          '- §4: the stand dynamic Pc channel has a range of at least 100 bar abs and a stated proof rating (R3-10; LEAD line 194 (7)); grain '
          'conditioning is stated.\n'
          '- New sections: §11 run rules (red lines, aborts, series stop), §12 validity of short or aborted firings, §13 char and melt-layer '
          'procedure, §14 counts and N2O budget, §15 throat check against the frozen prediction (NZ-01; LEAD line 194 (5)), §16 cost '
          '(R3-07; LEAD line 194 (8)).')
    D.rep('2. **The oxidiser-flux law counts as shown only when all of these hold:**',
          '2. **The oxidiser-flux law counts as shown only when all of these hold (two-sided test; REV-COMB-3 R3-06, LEAD line 194 (8)):**')
    D.rep('   - On the deep-throttle holds T3, and on at least one T1 or T2 firing, S_meas + 1.645 σ(S) < S_total. S_total is the total-flux prediction at '
          'the (a, n) fitted to the same firings, computed by Combustion on the as-fired oxidiser history.\n'
          '   - On the same firings, S_meas - 1.645 σ(S) <= S_ox. S_ox is the oxidiser-flux prediction on the same history, which is about 1.00.\n',
          '   - On the deep-throttle holds T3, and on at least one T1 or T2 firing, |S_meas - S_ox| <= 1.645 σ(S). S_ox is the oxidiser-flux '
          'prediction on the as-fired oxidiser history, about 1.00. (v2 required only S_meas - 1.645 σ(S) <= S_ox, which any S below S_ox passed.)\n'
          '   - On the same firings, S_meas + 1.645 σ(S) < S_total. S_total is the total-flux prediction at the (a, n) fitted to the same firings, '
          'computed by Combustion on the as-fired oxidiser history.\n')
    D.rep('3. **Total-flux shown, or neither law shown:** the default stays.\n'
          '   - When the total-flux law is shown, Combustion recomputes the burn limit for GNC with 1.1 a_meas and the total-flux form (REPORT §4.6).\n',
          '3. **Total-flux shown, or neither law shown:** the default stays.\n'
          '   - When the total-flux law is shown, Combustion recomputes the burn limit for GNC with 1.1 a_meas and the total-flux form (REPORT §4.6).\n'
          '   - **Signature below the oxidiser-flux band** (S_meas < S_ox - 1.645 σ(S) on a T3 hold): "neither shown" (LEAD line 194 (8)). Regression '
          'is then highest toward the head, where a_meas at x/L 0.97 does not look. Examples are a Marxman-type G^0.8 x^-0.2 law (S about 0.73 at '
          'T3, O/F 4.85; DERIVED in REV-COMB-3) or a head-end spray effect. The default gate stays, and Combustion re-evaluates the burn limit on '
          'the measured axial profile: the r(x) of the eight stations (§4), fitted per firing and scaled to the B1 duty cycle, gives the web '
          'left at the most-regressed station, which replaces the x/L 0.97 web in the B1 gate.\n')
    D.rep('| T1, 100 % for 4 s | a anchor at high flux; weak law signal | 1.014-1.072 | 0.24-1.00 |',
          f'| T1, 100 % for 4 s (N2O: §14; 2t = 8 s needs about {max(t1_2t):.2f} kg) | a anchor at high flux; weak law signal | 1.014-1.072 | 0.24-1.00 |')
    D.rep('- **Grain mass** before and after each firing. Balance resolution <= 0.1 g. Dry to constant mass.\n',
          '- **Grain mass** before and after each firing. Balance resolution <= 0.1 g. Dry to constant mass.\n'
          '- **Grain conditioning (new in v3).** Both grains of a pair from one print job with the same settings; bagged with desiccant after '
          'drying; held at the stand ambient for >= 24 h before the firing (ASSUMED); grain and ambient temperatures recorded at ignition.\n')
    D.rep('  - Pc on the control channel at 1 kHz, and on the stand dynamic channel at >= 10-20 kHz with anti-alias filtering (R2-10; REPORT §10).\n',
          '  - Pc on the control channel at 1 kHz, and on the stand dynamic channel at >= 10-20 kHz with anti-alias filtering (R2-10; REPORT §10). '
          '**Range >= 100 bar abs, with the transducer\'s proof rating stated in the firing record** (R3-10; LEAD line 194 (7)). The FA-1 construct '
          f'head peak is {pk_med:.0f} bar abs (median) to {pk_max:.1f} bar abs (maximum) over its 896 cases (REPORT §7.6, SIM), which a 70 bar '
          'channel clips. **Proof rating** (DERIVED from the FA-1 spectra, REPORT §7.6 v2.4b; same rule as the LEAD line 205 flight unit, 1.1 x '
          'the governing equivalent pressure): at least 1.1 x the all-case spectrum value at the period of the transducer path. Flush mount '
          f'(path period <= 0.1 ms): >= {1.1 * q01:.0f} bar abs, use >= 112 bar abs (1.1 x 102, the line-205 value). Short sense line with a path '
          f'period of 0.1-1 ms: >= {1.1 * q1:.0f} bar abs. A path period above 1 ms is not acceptable (the spectrum reaches {q20:.1f} bar abs '
          f'between 1 and 20 ms). The path period depends on the gas in the passage: use c >= {c_min:.0f} m/s and no liquid N2O in the passage '
          '(REPORT §15.8; LEAD line 205), and measure the path ringing in the first firing. The founders state the rating from the maker\'s '
          'datasheet (TO-VERIFY). The flight Pc transducer is reselected by LEAD line 205 (seat-mounted miniature unit, proof >= 112 bar abs); '
          'its over-range behaviour and the effect on the 30 bar abort, the Pc-valid flag and the logged peak are Electronics\' items (LEAD line '
          '194 (7)).\n')
    D.rep('Combustion returns, as SIM/DERIVED:\n',
          'Also return (new in v3): the validity checklist of §12 for every firing; the red-line channel records of §11; the frozen throat '
          'prediction (file and hash) and the throat measurements of §15; the photographs and weights of §13.\n\n'
          'Combustion returns, as SIM/DERIVED:\n')
    D.rep('## 10. Refutation\n\n'
          '- **The oxidiser-flux law is refuted** if S_meas exceeds S_ox by more than 1.645 σ(S) on the T3 holds.\n'
          '- **The total-flux law is refuted** if S_meas + 1.645 σ(S) < S_total(a_fit, n_fit) on T3 and on a T1 or T2 firing.\n'
          '- **Neither refuted:** the LEAD default gate applies.\n',
          '## 10. Refutation\n\n'
          '- **The oxidiser-flux law is refuted** if |S_meas - S_ox| > 1.645 σ(S) on the T3 holds, in either direction (v3; v2 tested only '
          'S_meas above S_ox).\n'
          '- **The total-flux law is refuted** if S_meas + 1.645 σ(S) < S_total(a_fit, n_fit) on T3 and on a T1 or T2 firing.\n'
          '- **Signature below the oxidiser-flux band** (S_meas < S_ox - 1.645 σ(S) on T3): both modelled axial forms are refuted. The default '
          'gate applies and the burn limit is re-evaluated on the measured axial profile (§2 point 3).\n'
          '- **Neither refuted:** the LEAD default gate applies.\n')

    # new sections 11-16
    kinds_rows = []
    lab = {'T1_100pct': 'T1, 100 %', 'T1_50pct': 'T1, 50 %', 'T2_100_50_25pct': 'T2, 100/50/25 %', 'T3_20pct': 'T3, 20 %', 'T3_12p5pct': 'T3, 12.5 %'}
    for k, nm in lab.items():
        a = rng(k, 'N2O_t_kg'); b = rng(k, 'N2O_2t_kg'); c = rng(k, 'N2O_pair_with_allowance_kg')
        kinds_rows.append(f'| {nm} | {K[k]["t_s"]:g} s / {2 * K[k]["t_s"]:g} s | {a[0]:.2f}-{a[1]:.2f} | {b[0]:.2f}-{b[1]:.2f} | {c[0]:.2f}-{c[1]:.2f} |')
    ser_rows = []
    for N in ('N1', 'N2', 'N4', 'N8'):
        s = ser[N]; n2o = [s['N2O_kg'][p] for p in P]
        ser_rows.append(f'| {N[1:]} | {s["firings"]} | {s["grains"]} | {min(n2o):.1f}-{max(n2o):.1f} | {s["N2_quench_kg"]:.1f} | '
                        f'{s["ground_tank_fills_at_4p5MPa"]:.1f} |')
    NEW = f'''
## 11. Run rules: red lines, aborts and series stop (new in v3; R3-07, LEAD line 194 (8))

The stand runs the abort matrix of REPORT §7.4 in its stand build (rows A1-A16 with their stand actions) and the safing rules of REPORT §10.2. Every abort below is the abort of REPORT §7.3 (MV de-energised at once, pintle commanded closed, torch valves de-energised), followed by the N2 quench (§4) and the §10.2 safing; there is no retry into a pooled chamber (LEAD line 172 (1)). The founders may tighten a limit; relaxing one needs the lead.

Table 11.1. Red lines of the T series (values ASSUMED unless tagged).

| # | Red line | Channel | Limit and persistence | Action |
|---|---|---|---|---|
| T-R1 | Over-pressure | Pc, filtered control channel; hardware comparator | > 30 bar abs for 5 ms; comparator at 31.47 bar g (A4; LEAD line 166 (4)) | Abort |
| T-R2 | Pressure above MEOP | Pc, stand dynamic channel | any sample > 45 bar abs (MEOP 4.5 MPa) | Abort if running; series stop |
| T-R3 | No light | E2 (relative rule) | not reached by the lift command + 0.35 s (stand R1 = R2; A2) | Abort; the one no-light rule of REPORT §10.2 |
| T-R4 | Flame-out | A3 relative rule | as REPORT §7.4 | Abort |
| T-R5 | Case over-temperature | either case thermocouple | > 448.15 K for 0.2 s (A12, LEAD) | Abort |
| T-R6 | Aft closure and J1 lip | TC-09 and lip thermocouples (REPORT §6.5) | Mechanical's Inconel 718 time-at-temperature limit (LEAD line 188 (5)); until it is published, 600 C (ASSUMED: 50 K below the 650 C limit cited in REV-MECH-1 RM1-06) | Abort |
| T-R7 | Over-thrust | thrust load cell | > 650 N for 20 ms (the flight FC_THRUST value, PROVISIONAL LEAD, applied on the stand) | Abort |
| T-R8 | Combustion roughness | Pc, stand dynamic channel | peak-to-peak > 10 % of the mean Pc for > 50 ms after E3 (ASSUMED; REPORT §8) | Abort |
| T-R9 | Torch and bleed valves | A8, A9, A14, A16 | as REPORT §7.4 | As REPORT §7.4, stand build |
| T-R10 | Pintle | A6, A15 | as REPORT §7.4 | Abort |
| T-R11 | Tank | P_tank | above the stand tank's relief set minus 5 % (stand value MISSING) | Abort; remote vent |
| T-R12 | N2O leak | gas detector; closed-segment pressure | any alarm; a decay > 0.5 bar/min with the MV closed at steady temperature | Abort; remote vent; N2 purge |
| T-R13 | Red-line channel lost | Pc (either channel), case and TC-09 thermocouples, load cell | loss or out of range for 50 ms | Abort; no firing starts without its red-line channels |
| T-R14 | Visual | video of the case, the joints and the feed | flame or smoke from the case, a joint or the feed | Abort (operator) |

**Series stop.** The series halts, and Combustion and Mechanical review the data before the next firing, after any of:
- an abort whose cause is not identified;
- T-R2 (a Pc sample above 45 bar abs) or an A4 trip;
- a failed nozzle-joint N2 leak check at 67.5 bar, run before and after each firing (H19; REPORT §10);
- a throat result outside the NZ-01 criterion (§15);
- a cracked, debonded or slumped grain, or a mark on the liner or case at inspection;
- a TC-09 or lip temperature above Mechanical's limit, or distortion of the J1 lip or a closure at inspection.

## 12. Validity of short or aborted firings (new in v3; R3-07)

A firing counts in the law test (§2) and in the two-duration differential only if all of these hold (tolerances ASSUMED):
1. It reached E2 and ran to the planned shutdown command without an abort.
2. Its burn time (E2 to the tail-off at 10 % of the run Pc) is within ±5 % of the planned t or 2t, and the 2t firing of a pair lasts 2.00 ± 0.10 times its t firing.
3. Its steady-phase mean oxidiser flow is within ±5 % of plan, and the two firings of a pair agree within ±3 %. For T2 and T3 each throttle level is held within ±3 % over at least 90 % of the level.
4. The N2 quench started within 0.5 s of the shutdown command.
5. Both grains of the pair come from one print job with the same settings (§4), and their temperatures at ignition agree within 3 K.
6. The procedure of §13 was applied without deviation, and every channel of §4 recorded.

An aborted or short firing is not used in a differential pair. Its pair is re-fired with fresh grains; its data are still returned and reduced as a single firing (flagged; end effects not removed) for the anomaly record. After a no-light (A2) before E2 the grain stays usable only if its mass change is <= 0.1 g and its bore is unchanged at every station within the gauge resolution; otherwise it is replaced. A firing that loses any channel used by §2 is invalid for the law test.

## 13. Char and melt-layer procedure (new in v3; R3-07)

The same procedure is used for every firing, because the two-duration differential removes only a layer that is the same at t and 2t:
1. After the N2 quench and the §10.2 hold, cool the grain in its case under dry N2 to <= 40 C (ASSUMED). No water, no solvent.
2. Remove the grain and photograph each station with a scale bar before any other handling.
3. Remove loose deposits only: dry N2 blow-off at <= 2 bar gauge and a soft nylon brush, two axial passes per station (ASSUMED). Weigh the grain before and after this step (<= 0.1 g).
4. Do not machine, scrape or abrade the bore. The resolidified ABS melt and char layer is measured, not removed: a removal tool adds its own depth, which differs from firing to firing.
5. Measure the bore at the stations of §4 on this surface.
6. Correct each station for the layer: d_solid = d_measured + 2δ, with δ the layer depth at that station from the witness section of the same firing kind (§4). δ and its scatter enter s_s (§5). In the differential an equal layer at t and 2t cancels; the witness sections at t and 2t show whether it does.
7. Record the tools, passes, pressure and operator in the firing record. A deviation makes the firing invalid for the law test (§12).

The founders may propose a removal method in place of step 4 if a witness grain shows its removal depth per station; the lead decides.

## 14. Counts and N2O budget (new in v3; R3-07, LEAD line 194 (8))

From `test_budgets_v2p4b.json` ({HB}; DERIVED). Oxidiser flow from the S230 throttle map (SIM, grain_q1d v2 nominal law, Cd 0.70, eta_c* 0.92) at a tank pressure of 4.0-5.0 MPa, the largest value over the map's port diameters. Durations and repeats are those of §3 and §6 (ASSUMED). The allowance of 10 % (ASSUMED) covers starts, tail-offs and chill-down.

Table 14.1. N2O per firing kind [kg].

| Kind | t / 2t | at t | at 2t | pair (t + 2t) with the allowance |
|---|---|---|---|---|
''' + '\n'.join(kinds_rows) + f'''

- **Per repeat set** (the five kinds at t and 2t): {min(per_set):.2f}-{max(per_set):.2f} kg, or {min(per_set_a):.2f}-{max(per_set_a):.2f} kg with the allowance (REV-COMB-3 R3-07: 7.92 kg).
- **T4** (DC-D duty cycle, S230 grain, 3 starts) uses {dcd['N2O_kg']:.2f} kg (integrated from the S230 ground record, SIM).
- **N2** for the quench: {B['N2_quench_per_firing_kg']:.1f} kg per firing (60 s at 10 g/s, REPORT §10.2), plus the purges after any abort.

Table 14.2. Series size for N repeats (§6; N <= 8 practical). Grains: 10N firings plus one witness grain per firing kind (5).

| N | Firings | Grains | N2O [kg] (with allowance) | N2 quench [kg] | Fills of a 15 L ground tank (10.4 kg, ASSUMED) at 4.5 MPa |
|---|---|---|---|---|---|
''' + '\n'.join(ser_rows) + f'''

**Stand tank and T1 at 2t (R3-07; LEAD line 194 (8)).** T1 at 100 % for 2t = 8 s uses {min(t1_2t):.2f}-{max(t1_2t):.2f} kg, {100 * share:.0f} % of the 2.0 kg flight load. The founders' stand tank is MISSING from every Combustion document. Two ways to run T1:
- a ground tank that holds at least one T1 pair with its heel, for example the 15 L / 10.4 kg tank used as the REPORT's sizing example (§2.7, ASSUMED); or
- the flight tank, with T1 at 100 % shortened so that 2t stays within 80 % of the flight load (ASSUMED usable share): 2t <= {t_max_flight:.1f} s, for example t = 3 s and 2t = 6 s. The law decision rests on the T3 holds (§2), so a shorter T1 costs only resolution of the a anchor; Combustion recomputes the T1 signature for the as-fired durations.
The founders state the stand tank capacity in the firing plan.

## 15. Throat check against the frozen prediction (NZ-01; LEAD lines 183 (2), 186 (3) and 194 (5); R3-15)

- Before each firing Combustion issues the predicted throat-area change for that firing, from the erosion model updated only with the measurements of earlier firings, and freezes it: the prediction file and its hash go into the firing record before the firing.
- After the firing the founders measure the throat bore (at least four diameters at 45° spacing, resolution <= 0.01 mm, ASSUMED), photograph the insert, and check it for steps and missing fragments.
- **Refutation (any one):** a throat-area change more than 2 % beyond the erosion predicted for that firing, with the prediction frozen before the firing; a non-axisymmetric step; a missing fragment. 2 % of the area is about 1 % of the 13.7 mm throat diameter (0.14 mm; DERIVED from A_t = 1.479e-4 m2 in the S230 record), well above the gauge resolution.
- A refutation stops the series (§11) and returns the insert to Mechanical and the erosion model to Combustion.

## 16. Cost

Grains (§14), N2O (§14), N2 for the quench and purges, the stand dynamic Pc transducer (>= 100 bar abs) and its conditioning, the bore gauge or 3-D scanner, the sectioning or CT service and the load cells: TO-QUOTE, delivered to Sønderborg, DK-6400. No price is assumed.
'''
    D.rep('Any outcome is test evidence. None of it is flight approval.', 'Any outcome is test evidence. None of it is flight approval.\n' + NEW.rstrip('\n'))
    open(out_t, 'w', encoding='utf-8').write(D.T if D.T.endswith('\n') else D.T + '\n')

    # ================================================================== CF-4 v2.1
    C = Doc(open(cf4_f, encoding='utf-8').read())
    C.rep('Version 2.0 (Combustion v2.4a), 2026-10-13. It replaces v1.0, which is archived as `02-combustion/superseded/v2p4/CF-4-SPEC.md`.',
          'Version 2.1 (Combustion v2.4b), 2026-10-13. It replaces v2.0 (Combustion v2.4a), which is archived as '
          '`02-combustion/superseded/v2p4a/CF-4-SPEC.md`; v1.0 is in `superseded/v2p4/`.')
    C.rep('Changes in v2.0:\n',
          'Changes in v2.1 (REV-COMB-3 R3-08; LEAD CHANGELOG lines 186 (1) and 194 (3) and (8)):\n'
          '- §1 states the decided PURGE commit rule (L* = 1.3 s; below it no purge and no unpurged relight) and removes the "proceeds unpurged" '
          'text and the 0.22 s hold, which line 194 (3) withdrew.\n'
          '- §2: the hardware baseline is the frozen CAD v3.5.1 bleed path (REV-MECH-1 RM1-01, LEAD line 188 (1)); the model numbers of §5 are on '
          'CAD v3.4.1 until the purge grid is re-run on v3.5.1.\n'
          '- The lift is THE start-level lift (LEAD line 203 (7)): the ignition-lift table row at the test tank temperature (0.21776 mm at '
          '286.7 K before CF-3; 0.2039 mm at 20 C). P1 is stated in volume, 18.86 cm3 of lift flow after the pintle reaches the lift: '
          f'{P1_s:.3f} s at 0.21776 mm, {P1_v28:.3f} s at 0.2039 mm; t_lift {1e3 * t_lift_s:.1f} ms at 0.21776 mm ({1e3 * t_lift:.1f} ms at 0.2039 mm).\n'
          '- New: §4.1 preparation and verification of IS-1 to IS-3, §5.1 the continuous-liquid probe threshold, §9.1 red lines and abort '
          'criteria, §12 run and N2O budget.\n'
          '- LEAD line 213 (founder decision): the A1 apogee target is about 210 m (it was the 300 m lead default and the 285 m trim). The A1 '
          'relight tank state of §4 and the IS-2 coast duration come from the 300 m records and stay as comparators; the 210 m warm-end relight '
          'state becomes a tank-state point when GNC publishes the 210 m record (§4; REPORT §15.15).\n\n'
          'Changes in v2.0:\n')
    C.rep('- `02-combustion/REPORT` v2.4a: §2.8 (the purge and the integrated trade), §7.3 (sequence), §9.1 (hazards and FMEA input) and §10 (test plan);\n'
          '- `interfaces/combustion.json` v2.4a: `purge`, `cf4_gate`, `igniter.sequence` and `purge_commit_rule_v2p4a`.',
          '- `02-combustion/REPORT` v2.4b: §2.8 (the purge and the integrated trade), §7.3 (sequence), §9.1 (hazards and FMEA input) and §10 (test plan);\n'
          '- `interfaces/combustion.json` v2.4b: `purge`, `cf4_gate`, `igniter.sequence`, `purge_commit_rule_v2p4b` and `release_hold_v2p4b`.')
    G_ = HJ['groups']
    hold = {g: {pr: G_[g][pr]['hold_needed_s'] for pr in ('ramp_to_200N', 'ramp_to_500N', 'lift_flow_held')} for g in G_}
    assert hold['lin0.0|LO'] == {'ramp_to_200N': 0.3, 'ramp_to_500N': 0.19, 'lift_flow_held': 0.74}, hold['lin0.0|LO']
    assert max(hold[g]['ramp_to_200N'] for g in G_) == 0.31 and max(hold[g]['lift_flow_held'] for g in G_) == 0.75
    assert HJ['n_records'] == 2160
    C.rep('**PURGE commit (LEAD line 175 (3), PROVISIONAL).** PURGE commits no later than the plain relight trigger minus 1.7 s; otherwise no purge is run. '
          'The withdrawn rule of line 164 had the FC delay T_fire instead.\n'
          '- Under the provisional rule, a relight without a commit proceeds unpurged.\n'
          '- Combustion finds that an unpurged start carries a hazard outside its abort model (`unpurged_start_check_v2p4a.json`, SIM/DERIVED):\n'
          '  - In the PURGE NOT RUN LO worst state, every light (P 0.758) happens inside the first liquid slug.\n'
          '  - A 23.4 cm3 vapour gap follows that light 0-0.19 s after E2. That is after the drogue-release term (Pc >= 3 bar abs) is already true.\n'
          '  - The gap drives A3. The ratio during the gap is at most 0.24, against the 0.40 threshold.\n'
          '- REPORT v2.4a §2.8 has the analysis, and the lead decides the rule. CF-4 tests the purge, not the commit rule. Optional run O-3 (§8) '
          'measures the unpurged sequence.\n',
          '**PURGE commit (LEAD line 186 (1); it replaces the PROVISIONAL rule of line 175 (3) and the 1.7 s interim of line 181 (2)).** PURGE commits '
          'iff the lead to the plain relight trigger is >= L* = 1.3 s, for both heat brackets. Below L* there is no purge and no unpurged relight on '
          'that pass (drogue descent; vehicle loss in the FMEA).\n'
          '- Basis (SIM/DERIVED: `unpurged_start_check_v2p4a.json`, `unpurged_outcomes_v2p4a.json`, `release_hold_v2p4b.json`): at the worst PURGE NOT '
          'RUN states an unpurged start succeeds with P 0 under both brackets. In the LO worst state every light (P 0.758) happens inside the first '
          'liquid slug, and a 23.4 cm3 vapour gap follows 0-0.19 s after E2 (flow held at the lift), when the drogue-release term is already true; '
          'the gap drives A3 (ratio <= 0.24 against 0.40).\n'
          '- The "E2 + 0.22 s" release hold of line 186 (1) is WITHDRAWN (LEAD line 194 (3)). Over all 2160 PURGE NOT RUN records (0 and 2 deg), '
          'the latest A3 trip after E2 plus one 10 ms frame is 0.30 s with the 2500 N/s ramp to 200 N flown during the hold, 0.19 s with the ramp to '
          '500 N, and 0.74 s with the flow held at the lift, which is outside W 0.65 s (unlined records; 0.31 / 0.19 / 0.75 s with the lined '
          'records). With Pc invalid the command is held at the start level (line 186 (2)), which is the lift-flow case, so the unpurged '
          'alternative is not admissible then; GNC flies it only as a comparator.\n'
          '- CF-4 tests the purge, not the commit rule. Optional run O-3 (§8) measures the unpurged sequence; the generation runs (§8) measure the '
          'LO/HI bracket, which stays open (line 186 (1)).\n')
    C.rep('In each run the ECU executes PURGE and then the lift to 0.2039 mm.',
          'In each run the ECU executes PURGE and then the lift to THE start-level lift: the ignition-lift table row at the test tank temperature '
          '(LEAD line 203 (7); 0.21776 mm at 286.7 K and 0.2039 mm at 20 C before CF-3), with the encoder lift recorded.')
    C.rep('**Claim C-RL.** On CAD v3.4.1 with the decided purge path and 2.5 s of flow ending 0.05 s before E0,',
          '**Claim C-RL.** With the decided purge path as frozen in CAD v3.5.1 (§2) and 2.5 s of flow ending 0.05 s before E0,')
    C.rep('The model behind the claim (SIM, `data/v2/v2p4/rg01_line_states_v2p4.json`, `2939549811d4c381`) needs',
          'The model behind the claim (SIM on CAD v3.4.1, `data/v2/v2p4/rg01_line_states_v2p4.json`, `2939549811d4c381`; re-run on v3.5.1 before '
          'the test, §2) needs')
    C.rep('## 2. Hardware\n\n',
          '## 2. Hardware\n\n'
          '**Baseline (v2.1; R3-08, LEAD line 194 (8)).** The test hardware is the frozen CAD v3.5.1 bleed path. REV-MECH-1 RM1-01 (LEAD line 188 (1)) '
          'relocates BL-02 and re-routes BL-03 and BL-04, so the v3.4.1 segment, restrictor positions and line lengths used by the model change. '
          'The v3.5.1 paths are MISSING from this specification: Mechanical is freezing them, and the lead forwards them. Before CF-4 is run, '
          'Combustion re-runs the two-flow purge grid on the v3.5.1 geometry (about 20 min) and re-issues P1, P3, P4, P5, Table 1 and the '
          'segment inventory. Until then the numbers in this specification are the v3.4.1 values.\n\n')
    C.rep('| IS-3 | Liquid-primed segment | Calibration reference, not a flight state |\n',
          '| IS-3 | Liquid-primed segment | Calibration reference, not a flight state |\n\n'
          '### 4.1 Preparation and verification of the initial states (new in v2.1; R3-08)\n\n'
          'A run starts only when its state is verified as below; a run whose state is not verified does not count. Tolerances are ASSUMED; the '
          'founders may tighten them.\n\n'
          '| State | Preparation | Verification before the PURGE command |\n'
          '|---|---|---|\n'
          '| IS-3 liquid-primed | MV open with the pintle seated and both bleed valves open until every segment probe reads liquid for >= 2 s; then '
          'bleeds and MV closed | Every segment probe liquid for >= 2 s; P_feed within 0.5 bar of P_tank; the probe liquid levels recorded for §5.1 |\n'
          '| IS-1 vapour-full (HI bound) | From IS-3: MV closed; drain the segment through the bleed path into the vent catch volume with the walls '
          'held at T_sat(P_tank) + 2-5 K by the segment heaters until every probe reads vapour; bleeds closed | Every segment probe vapour for >= 10 s; '
          'drained mass on the vent load cell >= 90 % of the segment liquid inventory (37.8 g at 20 C on v3.4.1; re-issued for v3.5.1); every wall '
          'thermocouple >= T_sat(P_tank); the probe vapour levels recorded for §5.1 |\n'
          '| IS-2 ARM-LO-like (traps full, short slug, cap at S1) | From IS-3: MV closed; heated hold at Mechanical\'s LO coast heat budget for the A1 '
          'coast duration (the generation-run condition, §8), so that the cap grows at S1 while the traps stay full. A drained measured mass from IS-3 '
          'may replace the hold if the probe pattern below is met | S1-cap probe vapour; trap probes (hump crowns at 2 deg, FD-01 crown, T4 crown, '
          'riser top) liquid; heat input logged; cap volume estimated from the heat input (0.0067 cm3/J with vapour at the S1 port, 0.0388 cm3/J '
          'with liquid; REPORT §2.7) within ±30 % of the model\'s IS-2 cap (rg01 ARM-LO state, re-issued with the v3.5.1 re-run) |\n')
    C.rep('| P1 | First continuous liquid at the pintle inlet <= 0.293 s after the pintle reaches the 0.2039 mm lift (encoder), i.e. <= 0.32 s after the '
          'lift command (t_lift 29.6 ms) |',
          '| P1 | First continuous liquid (§5.1) at the pintle inlet after at most 18.86 cm3 of lift flow from the moment the pintle reaches the '
          'commanded start-level lift (encoder): time limit = 18.86 cm3 / the measured liquid volume flow at the lift. '
          f'{P1_s:.3f} s at the A1-state lift 0.21776 mm (37.4 g/s), {P1_v28:.3f} s at 0.2039 mm (35.0 g/s); after the lift command add t_lift '
          f'({1e3 * t_lift_s:.1f} ms at 0.21776 mm, {1e3 * t_lift:.1f} ms at 0.2039 mm: 6.5 ms command, 10 ms lag, lift at 16.7 mm/s). v2.0 quoted '
          f'0.293 s after the 0.2039 mm lift with t_lift {1e3 * t_lift_old:.1f} ms, the 0.2192 mm value |')
    C.rep('## 6. Model checks (not gating)\n',
          f'''### 5.1 What "continuous liquid" means (new in v2.1; R3-08)

- Each void probe is calibrated in every series on IS-1 (vapour level V_v) and IS-3 (liquid level V_l), at the test pressure and temperature.
- A sample reads liquid above V_v + 0.6 (V_l - V_v) and vapour below V_v + 0.4 (V_l - V_v); between the two the previous reading holds (hysteresis, ASSUMED).
- Continuous liquid is a liquid reading interrupted by no vapour reading longer than the probe response (5 ms). Each shorter vapour reading counts as a void of one probe response at the lift flow, {pr['dropout_volume_cm3_per_response']:.2f} cm3 ({pr['lift_flow_g_s']:.2f} g/s at the A1-state start-level lift {pr['lift_mm']:.5f} mm, liquid {pr['rho_liquid_kg_m3']:.0f} kg/m3; DERIVED, CoolProp). These voids are added up and judged against Table 1 as a second void.
- P1 is the time of the first sample of the continuous-liquid interval that meets P2.
- A probe that fails its calibration (contrast V_l - V_v below the maker's minimum, TO-VERIFY) invalidates the run.

## 6. Model checks (not gating)
''')
    C.rep('- O-3, unpurged start (new). From IS-2 with PURGE not run, lift directly to 0.2039 mm. Record the phase sequence at the pintle inlet for 1.5 s, '
          'then compare it with the PURGE NOT RUN LO state: pocket 12.5 cm3, slug 11.2 cm3, gap 23.4 cm3 (`rg01_line_states_v2p4.json`). A sequence '
          'with no gap after the first slug refutes Combustion\'s unpurged-start finding for that state. A gap confirms it.',
          '- O-3, unpurged start. From IS-2 with PURGE not run, lift directly to the start-level lift (table row at the test tank temperature). '
          'Record the phase sequence at the pintle inlet for 1.5 s, '
          'then compare it with the PURGE NOT RUN LO state: pocket 12.5 cm3, slug 11.2 cm3, gap 23.4 cm3 (`rg01_line_states_v2p4.json`). A sequence '
          'with no gap after the first slug refutes Combustion\'s unpurged-start finding for that state. A gap confirms it, and its arrival time '
          'after the first liquid is the input of the hold table (`release_hold_v2p4b.json`).')
    C.rep('- After the series: the tank is vented remotely and still holds cold liquid until its mass shows otherwise (REPORT §10.2).\n',
          '- After the series: the tank is vented remotely and still holds cold liquid until its mass shows otherwise (REPORT §10.2).\n\n'
          '### 9.1 Red lines and abort criteria (new in v2.1; R3-08)\n\n'
          'Heated holds and flowing runs stop as below. "Abort" means: MV de-energised; bleed valves V1 and V2 commanded closed (stand build; a valve '
          'that does not close leaves the segment venting into the vent catch volume, which is sized for it); pintle commanded closed; heaters off; '
          'then the REPORT §10.2 safing (remote vent, N2 purge, hold before approach). Values are ASSUMED unless tagged; the founders may tighten '
          'them; relaxing one needs the lead.\n\n'
          '| # | Red line | Limit | Action |\n'
          '|---|---|---|---|\n'
          '| C-R1 | Segment over-pressure with the MV closed (S1 flag) | P_feed - P_tank > 2 bar for 1 s (A13, LEAD) | Heaters off; lock out (stand A13); '
          'vent through the bleed path |\n'
          '| C-R2 | Segment wall temperature in a heated hold | above the coast-budget maximum + 5 K, or segment liquid more than 3 K above the tank '
          'temperature (a liquid-full segment with S1 stuck reaches MAWP after 7.3 K of warming; REPORT §2.7, DERIVED) | Heaters off; vent through '
          'the bleed path |\n'
          '| C-R3 | Tank state | T_tank > 24 C or P_tank > 5.53 MPa (the ARM interlock; the A1 state is 43.5-46.5 bar, 286.7-289.5 K) | Abort; '
          'remote vent |\n'
          '| C-R4 | Catch-volume pressure | > 80 % of its relief set | Abort; remote vent |\n'
          '| C-R5 | Any relief or disc lift (stand, segment or catch volume) | any | Abort; the run is invalid; inspect |\n'
          '| C-R6 | Leak | gas-detector alarm, or a closed-segment pressure decay > 0.5 bar/min at steady temperature | Abort; remote vent; N2 purge |\n'
          '| C-R7 | Bleed valve stuck open beyond P6 (c) | after BLEED_FAULT at the closure deadline, V2 not closed within 0.10 s of its command, or the '
          'pressure downstream of V2 not at the vent back-pressure within 0.5 s | Abort (stand build); recorded as a P6 failure |\n'
          '| C-R8 | Pintle | A6 or A15 (REPORT §7.4): encoder invalid, jam, or drift > 0.05 mm for 10 ms while commanded seated during PURGE | Abort |\n'
          '| C-R9 | Channel loss | any red-line channel (P_tank, P_feed, catch-volume pressure, wall thermocouples, pintle encoder) lost for 50 ms | Abort |\n')
    cf = cf4
    C.rep('## 11. Cost\n\n'
          'Valves, restrictors, the FD-01 element, probes, fixtures and catch volumes: TO-QUOTE, delivered to Sønderborg, DK-6400. No price is assumed.',
          f'''## 11. Cost

Valves, restrictors, the FD-01 element, probes, fixtures and catch volumes, and the N2O of §12: TO-QUOTE, delivered to Sønderborg, DK-6400. No price is assumed.

## 12. Run and N2O budget (new in v2.1; R3-08)

From `test_budgets_v2p4b.json` ({HB}; DERIVED on ASSUMED repeats):
- **Runs.** 3 states x 5 attitude settings (0 deg; 2 and 3 deg toward azimuth 45 and 180 deg) x 5 repeats = {cf['runs_base_5_per_state_and_attitude']} (base). With the 4 deg settings also repeated 5 times per state: {cf['runs_upper_with_4deg_repeats']}. With IS-3 once per attitude and each 4 deg setting once per state: {cf['runs_lower']}.
- **N2O per run:** <= {cf['N2O_per_run_terms_g']['vent_max']:.0f} g vented (P5 limit) + {cf['N2O_per_run_terms_g']['lift_flow']:.1f} g of lift flow over the 1.5 s record ({pr['lift_flow_g_s']:.2f} g/s at the A1-state start-level lift; {cf['N2O_per_run_g_at_0p2039mm']:.1f} g per run at 0.2039 mm) + {cf['N2O_per_run_terms_g']['segment_state']:.1f} g of segment inventory to set the state (v3.4.1, 20 C) = {cf['N2O_per_run_g']:.0f} g.
- **Total N2O:** {cf['N2O_kg']['lower']:.1f} / {cf['N2O_kg']['base']:.1f} / {cf['N2O_kg']['upper']:.1f} kg for {cf['runs_lower']} / {cf['runs_base_5_per_state_and_attitude']} / {cf['runs_upper_with_4deg_repeats']} runs, or {cf['N2O_kg_with_allowance']['lower']:.1f} / {cf['N2O_kg_with_allowance']['base']:.1f} / {cf['N2O_kg_with_allowance']['upper']:.1f} kg with a 10 % allowance (ASSUMED) for fills, chill-down and aborted runs.
- That is {cf['N2O_kg_with_allowance']['lower'] / 2.0:.0f}-{cf['N2O_kg_with_allowance']['upper'] / 2.0:.0f} fills of the 2.0 kg flight load, or {cf['N2O_kg_with_allowance']['lower'] / 10.4:.1f}-{cf['ground_tank_fills_upper']:.1f} fills of a 15 L ground tank (10.4 kg, ASSUMED). The founders' stand tank is MISSING. Optional runs (generation runs, the prep-path credit, O-3) and the tank heel are not included.''')
    C.rep("Tank at the A1 relight state: 43.5-46.5 bar, 286.7-289.5 K. Segment heaters set to Mechanical's segment heat budget.",
          "Tank at the A1 relight state: 43.5-46.5 bar, 286.7-289.5 K. Segment heaters set to Mechanical's segment heat budget.\n\n"
          "A1 profile (LEAD line 213; new in v2.1). The A1 apogee target is about 210 m; GNC sets the exact band (gnc.json v3.2). The bracket "
          "above comes from the 300 m records and stays as a comparator (300 m records, SIM: relight %.2f-%.2f K, coast %.2f-%.2f s). At the same "
          "launch temperature the 210 m relight state is warmer: the modelled tank keeps its MECO temperature over the coast, and a shorter "
          "ascent cools it less (DERIVED direction; magnitude MISSING). When GNC publishes the 210 m record, its warm-end relight state is added "
          "as a tank-state point and P5 is read there. The purge vented mass rises by about %.2f g per K above %.1f K (DERIVED scaling of the "
          "records, not re-run); the 2.5 s schedule stays <= 76 g up to %s, and the 2.55 s cap is already at the 76 g limit at %.1f K (OI-42) "
          "(`a1_profile_line213_v2p4b.json` `%s`). The IS-2 heated hold keeps the 300 m coast duration: the longer coast puts more heat into "
          "the segment, which is the conservative side for the vapour cap (DERIVED direction)."
          % (A1S['T_relight_K'][0], A1S['T_relight_K'][1], A1S['coast_s'][0], A1S['coast_s'][1], A1P['M_2p5s_slope_g_per_K'],
             A1P['basis_T_K'], ('%.2f K' % A1P['T_at_76g_2p5s_K']) if not isinstance(A1P['T_at_76g_2p5s_K'], str) else A1P['T_at_76g_2p5s_K'],
             A1P['basis_T_K'], HA1))
    open(out_c, 'w', encoding='utf-8').write(C.T if C.T.endswith('\n') else C.T + '\n')
    print('T1-T4 v3 edits', D.n, 'CF-4 v2.1 edits', C.n)
    print('wrote', out_t, h16(out_t), out_c, h16(out_c))


if __name__ == '__main__':
    main(*sys.argv[1:10])
