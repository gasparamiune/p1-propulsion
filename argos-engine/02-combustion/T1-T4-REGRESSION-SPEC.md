# T1-T4 regression-rate measurement and law form (RG-03), v3.2

v3.2 (Combustion v2.4d), 2026-10-21: the T4 note on line 294 updated by the lead for GNC's N-07 answer in `interfaces/gnc.json` v3.2 (`bde317782574cbd9`), with T4 re-sized to the shortest firing (LEAD 261), and a pointer on line 61; the edits are in place, so the line numbers are kept; v3.1 (`b00b2d852ed3475c`) is archived as `02-combustion/superseded/v2p4c/T1-T4-REGRESSION-SPEC.md`. The v3.1 header follows unchanged. v3.1 (Combustion v2.4c), 2026-10-21: text corrections from REV-COMB-4 (`reviews/REVIEW-COMBUSTION-R4.md`, `2908321d7f75d439`) applied by the lead: the proof values of line 83 (R4-05; LEAD 230 (2), 249 (4)) and the T4 N2O note on line 294 (N-07); the edits are in place, so the line numbers are kept; v3 (`b0c42b09ba47cb9c`) is archived as `02-combustion/superseded/v2p4b/T1-T4-REGRESSION-SPEC.md`. The v3 header follows unchanged. Combustion v2.4b, 2026-10-13. Replaces v2 (Combustion v2.4a), which is archived as `02-combustion/superseded/v2p4a/T1-T4-REGRESSION-SPEC.md`; v2 replaced v2.4 (`superseded/v2p4/`). v2 responded to REV-COMB-2 R2-04 and LEAD CHANGELOG line 172 (3); v3 responds to REV-COMB-3 R3-06, R3-07, R3-10 and R3-15 and to LEAD CHANGELOG line 194 (5), (7) and (8). REPORT v2.4b §10.4 summarises this text.

The founders carry out the firings; Combustion reduces the data. This file is a digital specification. It contains no physical result and approves nothing.

Evidence tags: SIM, DERIVED, ASSUMED, DATASHEET, TO-VERIFY, LITERATURE, DESIGN, LEAD, MISSING.

Computation:
- `02-combustion/src/t1t4_law_resolution_v2p4a.py` (3701b74681de700b) writes `02-combustion/data/v2p4a/t1t4_law_resolution_v2p4a.json` (05b5ae5c20e04bd8). It reduces published SIM histories and re-runs no grain grid.
- `02-combustion/src/test_budgets_v2p4b.py` (d8a7a83f4a992e31) writes `02-combustion/data/v2p4b/test_budgets_v2p4b.json` (c0e4ce35659f21fa): the counts and N2O of §14, from the S230 throttle map (SIM) and the DC-D ground record.

Changes in v3:
- §2 and §10: the oxidiser-flux test is two-sided, and a signature below the oxidiser-flux band is "neither shown" (R3-06; LEAD line 194 (8)).
- §4: the stand dynamic Pc channel has a range of at least 100 bar abs and a stated proof rating (R3-10; LEAD line 194 (7)); grain conditioning is stated.
- New sections: §11 run rules (red lines, aborts, series stop), §12 validity of short or aborted firings, §13 char and melt-layer procedure, §14 counts and N2O budget, §15 throat check against the frozen prediction (NZ-01; LEAD line 194 (5)), §16 cost (R3-07; LEAD line 194 (8)).

## 1. Why it matters

The B1 gate uses a measured regression multiplier a_meas. Suppose the true law is the total-flux form and the test does not detect it. REV-GNC-2 then leaves 11 of 483 runs below 1 mm of web (REV-COMB-2 R2-04).

LEAD line 168 (6) sets a stricter gate for that case: "current rule OR a_meas >= 1.25 -> change grain".

v2.4 of this file applied the stricter gate only when the test showed the total-flux law. The reviewer showed two problems:
- the test cannot resolve the signature at T1;
- when the test detects nothing, v2.4 defaults to the less safe gate.

v2 reverses the burden of proof (LEAD line 172 (3)).

## 2. Decision rule (reversed burden)

1. **Default (LEAD).**
   - The B1 gate applies "current rule OR a_meas >= 1.25 -> change grain".
   - a_meas is evaluated at x/L 0.97 (REQUIREMENTS line 117).
   - The default holds unless the oxidiser-flux law is positively shown under point 2.
2. **The oxidiser-flux law counts as shown only when all of these hold (two-sided test; REV-COMB-3 R3-06, LEAD line 194 (8)):**
   - The law signature S = r(x_law)/r(x_ref) is measured at the law stations x/L 0.80, 0.85 and 0.90. The head reference is x/L 0.10, or x/L 0.30 if the spray check in §4 fails.
   - σ(S) <= 1.5 % (LEAD line 172 (3)), on the firings in §3.
   - On the deep-throttle holds T3, and on at least one T1 or T2 firing, |S_meas - S_ox| <= 1.645 σ(S). S_ox is the oxidiser-flux prediction on the as-fired oxidiser history, about 1.00. (v2 required only S_meas - 1.645 σ(S) <= S_ox, which any S below S_ox passed.)
   - On the same firings, S_meas + 1.645 σ(S) < S_total. S_total is the total-flux prediction at the (a, n) fitted to the same firings, computed by Combustion on the as-fired oxidiser history.
3. **Total-flux shown, or neither law shown:** the default stays.
   - When the total-flux law is shown, Combustion recomputes the burn limit for GNC with 1.1 a_meas and the total-flux form (REPORT §4.6).
   - **Signature below the oxidiser-flux band** (S_meas < S_ox - 1.645 σ(S) on a T3 hold): "neither shown" (LEAD line 194 (8)). Regression is then highest toward the head, where a_meas at x/L 0.97 does not look. Examples are a Marxman-type G^0.8 x^-0.2 law (S about 0.73 at T3, O/F 4.85; DERIVED in REV-COMB-3) or a head-end spray effect. The default gate stays, and Combustion re-evaluates the burn limit on the measured axial profile: the r(x) of the eight stations (§4), fitted per firing and scaled to the B1 duty cycle, gives the web left at the most-regressed station, which replaces the x/L 0.97 web in the B1 gate.
4. **Errs-safe correction (DERIVED; proposal for the lead to decide).** This applies whenever the oxidiser-flux law is not shown.
   - The gate uses a_meas,gate = max(1, ρ_max) x a_meas.
   - ρ_max = max over the B1 records of E_B1/E_cal for the calibration set actually fired (§7).
   - With a T3 hold in the calibration set, ρ_max <= 1.004, so the correction is negligible. With T1 at 100 % alone, ρ_max = 1.068.
5. **Law stations.** The stations are x/L 0.80-0.90, outside the aft-end region. a_meas stays at x/L 0.97 for the gate (REQUIREMENTS line 117).

## 3. Firings and what each contributes

T1-T4 are as defined in REPORT §10. The durations below are those of the computation (ASSUMED). The founders' as-fired histories replace them.

| Firing | Role in the law test | S = r(0.85)/r(0.10) over the band a 0.6-1.5, n 0.35-0.68 (DERIVED) | P(show the oxidiser-flux law \| it is true) at σ(S) 1.5 % |
|---|---|---|---|
| T1, 100 % for 4 s (N2O: §14; 2t = 8 s needs about 1.93 kg) | a anchor at high flux; weak law signal | 1.014-1.072 | 0.24-1.00 |
| T1, 50 % for 4 s | second flux | 1.022-1.091 | 0.43-1.00 |
| T2, 100/50/25 % for 2 s each | n fit | 1.022-1.082 | 0.42-1.00 |
| T3, 20 % for 4 s | **law firing** | 1.037-1.120 | 0.79-1.00 |
| T3, 12.5 % for 4 s | **law firing** | 1.046-1.135 | 0.92-1.00 |
| T4, DC-D duty cycle (S230 grain, 3 starts; v3.2: re-sized, line 294) | life and relight data; law check only | 1.023-1.077 | 0.46-1.00 |

At a x1.0 (Table A1 in §6), T1 at 100 % gives S = 1.024 / 1.035 / 1.049 for n = 0.35 / 0.5 / 0.68. The probability of showing the oxidiser-flux law is then 0.47 / 0.76 / 0.95.

The deep-throttle holds roughly double the signature: S = 1.060-1.092. They therefore carry the law decision.

Regression depth: the law stations need a diameter change of at least 3 mm (ASSUMED), so that a 0.02 mm bore-gauge resolution contributes no more than about 0.5 % to σ(S).
- At 12.5 % (G_ox about 74 kg/m2 s at D 25 mm, a x1.0, n 0.5), r is about 0.5 mm/s (DERIVED). A 4 s hold then gives ΔD of about 4 mm.
- Combustion recomputes the required hold durations from the founders' T1 data before T3 is fired.

## 4. Measurements

Changes from v2.4: stations x/L 0.80 and 0.85 are added, there are four diameters per station, and the witness and quench items are new.

- **Grain mass** before and after each firing. Balance resolution <= 0.1 g. Dry to constant mass.
- **Grain conditioning (new in v3).** Both grains of a pair from one print job with the same settings; bagged with desiccant after drying; held at the stand ambient for >= 24 h before the firing (ASSUMED); grain and ambient temperatures recorded at ignition.
- **Bore stations.** Measure at x/L 0.10, 0.30, 0.50, 0.70, 0.80, 0.85, 0.90 and 0.97 from the head end.
  - Use at least four diameters at 45° spacing (bore gauge, resolution <= 0.02 mm), or a 3-D scan of the bore with the same stations extracted.
  - Report ovality per station.
  - Locate the stations with a fixture. Position error <= 0.5 mm (ASSUMED).
- **Head-end spray check.** Compare r(0.10) with r(0.30). If they differ by more than the uncertainty, use x/L 0.30 as the head reference.
- **Time histories.**
  - Pc on the control channel at 1 kHz, and on the stand dynamic channel at >= 10-20 kHz with anti-alias filtering (R2-10; REPORT §10). **Range >= 100 bar abs, with the transducer's proof rating stated in the firing record** (R3-10; LEAD line 194 (7)). The FA-1 construct head peak is 48 bar abs (median) to 88.0 bar abs (maximum) over its 896 cases (REPORT §7.6, SIM), which a 70 bar channel clips. **Proof rating** (DERIVED from the FA-1 spectra, REPORT §7.6 v2.4b; same rule as the LEAD line 205 flight unit, 1.1 x the governing equivalent pressure): at least 1.1 x the all-case spectrum value at the period of the transducer path. Flush mount (path period <= 0.1 ms): >= 103.4 bar abs (1.1 x 94, the LEAD 230 (2) band value). Short sense line with a path period of 0.1-1 ms: >= 133.1 bar abs (1.1 x 121), with a range >= 132 bar abs (REV-COMB-4 R4-09). The flight unit's proof >= 166.14 bar abs (1.1 x FA1S 151.04; LEAD 249 (4)) covers every path period. A path period above 1 ms is not acceptable (the spectrum reaches 146.9 bar abs between 1 and 20 ms). The path period depends on the gas in the passage: use c >= 181 m/s and no liquid N2O in the passage (REPORT §15.8; LEAD line 205), and measure the path ringing in the first firing. The founders state the rating from the maker's datasheet (TO-VERIFY). The flight Pc transducer is reselected by LEAD line 205 (seat-mounted miniature unit, proof >= 166.14 bar abs = 1.1 x FA1S 151.04, LEAD 249 (4); the C1 Kulite XTL-190SM-2000A pick, 206.8 bar abs, meets it); its over-range behaviour and the effect on the 30 bar abort, the Pc-valid flag and the logged peak are Electronics' items (LEAD line 194 (7)).
  - Oxidiser mass flow from the tank load cell and P_feed.
  - Thrust.
  - Burn time from E2 to the tail-off at 10 % of the run Pc.
  - The time of the shutdown command and of the N2 quench.
- **N2 quench at shutdown.** Use the stand purge (REPORT §10.2: >= 60 s at >= 10 g/s), started at the shutdown command. It limits post-shutdown melt and soak-back regression.
- **Witness sectioning.** After the last firing of each kind, section one grain at the law stations, or use CT, to measure the melt and char layer depth. This is destructive: one grain per firing kind (ASSUMED).
- **Print density map.** Measure the density along x on a witness grain printed in the same job with the same settings, by slicing and weighing or by CT.

## 5. Systematic terms

None of these terms was in v2.4. The residual targets are ASSUMED. The founders bound each term from their data; Combustion combines them into s_s, the residual systematic standard deviation of S.

| Term | Effect | Mitigation | Residual target on S (ASSUMED) |
|---|---|---|---|
| Post-shutdown melt and soak-back regression | Adds depth after the burn. The added depth is not proportional to the burn, so short firings are biased. | N2 quench at the shutdown command. **Two-duration differential:** fire the same condition for t and 2t; r = (ΔD_2t - ΔD_t)/(2t) removes end effects common to both firings. | <= 0.5 % |
| Melt and char layer at the measured surface | The gauge reads the char or melt surface, not the regressed solid | A defined char-removal procedure before measurement. Witness sectioning gives the layer depth per station. | <= 0.5 % |
| Ovality and non-axisymmetric regression | Two diameters miss it | >= 4 diameters or a scan. Use the diameter of the area-equivalent circle. | <= 0.3 % |
| Print density along x | Equal mass loss gives unequal ΔD | Density map from a witness print. r is taken from the bore (geometric); mass closure is checked per segment. | report |
| Start and tail-off transients | Flux and O/F differ from the steady phase | Two-duration differential. Combustion computes S_ox and S_total on the as-fired mox(t), start and tail-off included. | <= 0.3 % |
| Head-end spray | Biases the reference r(0.10) | x/L 0.30 as the reference when the spray check fails | – |
| Aft-end flow (x/L > 0.9) | Contaminates the law stations | Law stations at 0.80-0.90; x/L 0.97 is used only for a_meas | – |
| Station position | Axial gradient times the x error | Fixture | <= 0.1 % |

If s_s >= 1.5 %, the law cannot be shown and the default gate stays.

## 6. σ target and repeats

- **Target:** σ(S) <= 1.5 % (LEAD line 172 (3)). For a 95 % chance of showing the oxidiser-flux law when it holds, the signature must be δ >= 3.29 σ.
  - T3 meets this with σ 1.5 % over the whole band at 12.5 % (P >= 0.92). At 20 % P >= 0.79 over the band and 0.99 at a x1.0.
  - T1 at 100 % needs σ <= 0.72-1.06 % for n 0.35-0.5 at a x1.0.
- **Repeats:** N = ceil(s1^2/(σ_t^2 - s_s^2)).
  - s1 is the single-firing random scatter of S. It is measured from the repeats themselves: the first two repeats give an estimate, then N is recomputed.
  - s_s is the residual systematic term from §5.
  - s1 and s_s below are ASSUMED bands.

| s1 \ s_s | 0.5 % | 1.0 % | 1.4 % |
|---|---|---|---|
| 1 % | 1 | 1 | 4 |
| 2 % | 2 | 4 | 14 |
| 3 % | 5 | 8 | 32 |

A practical count (N <= 8) needs s_s <= 1.0 %.

Table A1 (a x1.0, DERIVED). x_law = 0.85 and x_ref = 0.10. E is the regression-weighted total-flux enhancement at x/L 0.97.

| Firing | n | O/F, regression-weighted (min-max) | S | P(show) at σ 1.5 % | σ for 95 % power | E(0.97) |
|---|---|---|---|---|---|---|
| T1, 100 % for 4 s | 0.35 | 10.73 (10.28-11.23) | 1.024 | 0.47 | 0.72 % | 1.031 |
| T1, 100 % for 4 s | 0.5 | 10.43 | 1.035 | 0.76 | 1.06 % | 1.046 |
| T1, 100 % for 4 s | 0.68 | 10.12 (9.54-10.65) | 1.049 | 0.95 | 1.50 % | 1.064 |
| T2, 100/50/25 % for 2 s each | 0.35 | 8.00 (4.22-11.23) | 1.036 | 0.77 | 1.09 % | 1.047 |
| T2, 100/50/25 % for 2 s each | 0.5 | 8.44 (5.32-10.43) | 1.046 | 0.92 | 1.39 % | 1.060 |
| T2, 100/50/25 % for 2 s each | 0.68 | 8.90 (6.81-10.18) | 1.057 | 0.98 | 1.73 % | 1.074 |
| T3, 20 % for 4 s | 0.35 | 4.03 (3.92-4.14) | 1.060 | 0.99 | 1.83 % | 1.079 |
| T3, 20 % for 4 s | 0.5 | 4.85 | 1.073 | 1.00 | 2.22 % | 1.095 |
| T3, 20 % for 4 s | 0.68 | 5.99 (5.84-6.13) | 1.082 | 1.00 | 2.50 % | 1.107 |
| T3, 12.5 % for 4 s | 0.35 | 3.21 (3.13-3.29) | 1.074 | 1.00 | 2.26 % | 1.097 |
| T3, 12.5 % for 4 s | 0.5 | 4.06 | 1.087 | 1.00 | 2.63 % | 1.113 |
| T3, 12.5 % for 4 s | 0.68 | 5.32 (5.21-5.42) | 1.092 | 1.00 | 2.80 % | 1.121 |
| T4, DC-D (S230) | 0.35 | 7.35 (2.83-11.35) | 1.040 | 0.85 | 1.22 % | 1.052 |
| T4, DC-D (S230) | 0.5 | 8.37 (4.06-11.13) | 1.047 | 0.93 | 1.42 % | 1.061 |
| T4, DC-D (S230) | 0.68 | 10.00 (6.08-13.08) | 1.051 | 0.96 | 1.56 % | 1.067 |

Over the band, the station choice matters little. At T3 12.5 %, the minimum S is 1.043 for 0.80/0.10, 1.046 for 0.85/0.10 and 1.036 for 0.90/0.30.

## 7. Errs-safe check against the B1 O/F history

- **Claim checked.** v2.4 said that a total-flux truth shows up as a larger a_meas at x/L 0.97, so the gate "errs on the safe side whichever law holds".
- **What is needed.** If the truth is total-flux:
  - a_meas = E_cal x a_true;
  - the B1 aft regression is E_B1 x the oxidiser-flux prediction.
  - The gate with 1.1 a_meas therefore keeps the full 1.1 for measurement error only if ρ = E_B1/E_cal <= 1. The allowance left is 1.1/ρ - 1.
- **B1 histories.**
  - The B1 O/F histories are 78 Combustion grain_q1d records (SIM):
    - 30 on the gnc.json v3 85 m duty-cycle band;
    - 48 on the v3.1 62 m records, including the _lawtotal runs.
  - They cover a 0.6-1.65 and n 0.35-0.68, with start transients included.
  - **O/F is not a gnc.json quantity.** gnc.json v3 gives the duty cycles (throttle and thrust schedules); the O/F comes from Combustion's grain model run on those cycles.
  - B1 O/F reaches 1.78 at its minimum. The lowest 5 % of the web burns below O/F 2.24 (lowest record). The regression-weighted O/F is 2.84-11.93.

| Calibration set | ρ_max | Allowance left (1.1/ρ - 1) | ρ_min | B1 web below the calibration's minimum O/F (max share) |
|---|---|---|---|---|
| T1, 100 % for 4 s | 1.068 | +3.0 % | 1.018 | 99 % |
| T1, 50 % for 4 s | 1.043 | +5.4 % | 1.008 | 92 % |
| T2, 100/50/25 % | 1.045 | +5.3 % | 1.012 | 92 % |
| T3, 20 % for 4 s | 1.004 | +9.6 % | 0.977 | 81 % |
| T3, 12.5 % for 4 s | 0.990 | +11.2 % | 0.960 | 14 % |
| T4, DC-D (S230) | 1.042 | +5.6 % | 1.013 | 20 % |

**Verdict (DERIVED).**
- With a T1-only calibration, the gate does not err safe with the full margin. Under a total-flux truth, the B1 aft regression exceeds the calibration-based prediction by up to 6.8 %, which leaves 3.0 % of the 10 % allowance.
- With a T3 hold in the calibration set, the gate errs safe:
  - ρ <= 1.004 at 20 %, with 9.6 % left;
  - ρ <= 0.990 at 12.5 %, with 11.2 % left.
- The low-O/F phases are included in E_B1 through the records. B1 still burns up to 14 % of its web below the 12.5 % hold's minimum O/F. That share enters through e = (1 + x/OF)^n and is covered by ρ <= 0.990.
- Rule (§2 point 4): use a_meas from a calibration set that includes T3, or apply ρ_max. Combustion recomputes ρ_max on the as-fired histories.

## 8. Model and limits

- **Total-flux factor.** e(x) = (1 + x/OF)^n at the local station, first order, with fuel added uniformly along the port (DERIVED).
- **Calibration histories.** These are quasi-steady and analytic: r = a x 1 mm/s x (G_ox/300)^n.
  - ρ_f is 1000 kg/m3, ASSUMED (grain_q1d).
  - L is 0.230 m and D runs from 25 mm to the S230 burn-through at 53.5 mm.
  - mox per step comes from `engine_S230/throttle_map_v2.csv` at 4.5 MPa.
- **Model check** against the grain_q1d DC-D record (S230, a x1.0, n 0.5): E(0.97) is 1.0607 against 1.0664, web 14.25 mm against 14.24 mm, and regression-weighted O/F 8.37 against 8.17.
  - The v2.4a first pass read the pre-S230 DC-D file and the start rows, and gave a nonsense check. That pass was corrected before publication, and it is recorded here.
- **What the test does not do.** It does not test the axial model of grain_q1d. It decides the law form and measures a, n and a_meas.
- **ASSUMED values:** s1, s_s, the durations and the station position error.

## 9. Data to return to Combustion

For each firing return:
- the as-fired mox(t), Pc(t) on both channels, F(t), and the shutdown and quench times;
- the bore per station and diameter, before and after;
- the grain masses;
- the sectioning or CT results;
- the density map;
- the grain and ambient temperatures.

Also return (new in v3): the validity checklist of §12 for every firing; the red-line channel records of §11; the frozen throat prediction (file and hash) and the throat measurements of §15; the photographs and weights of §13.

Combustion returns, as SIM/DERIVED:
- S_meas with σ(S);
- the fitted (a, n) for both laws;
- S_ox and S_total on the as-fired history;
- the law decision under §2;
- a_meas at x/L 0.97;
- ρ_max for the fired set;
- the recomputed burn limit.

## 10. Refutation

- **The oxidiser-flux law is refuted** if |S_meas - S_ox| > 1.645 σ(S) on the T3 holds, in either direction (v3; v2 tested only S_meas above S_ox).
- **The total-flux law is refuted** if S_meas + 1.645 σ(S) < S_total(a_fit, n_fit) on T3 and on a T1 or T2 firing.
- **Signature below the oxidiser-flux band** (S_meas < S_ox - 1.645 σ(S) on T3): both modelled axial forms are refuted. The default gate applies and the burn limit is re-evaluated on the measured axial profile (§2 point 3).
- **Neither refuted:** the LEAD default gate applies.

Any outcome is test evidence. None of it is flight approval.

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

From `test_budgets_v2p4b.json` (c0e4ce35659f21fa; DERIVED). Oxidiser flow from the S230 throttle map (SIM, grain_q1d v2 nominal law, Cd 0.70, eta_c* 0.92) at a tank pressure of 4.0-5.0 MPa, the largest value over the map's port diameters. Durations and repeats are those of §3 and §6 (ASSUMED). The allowance of 10 % (ASSUMED) covers starts, tail-offs and chill-down.

Table 14.1. N2O per firing kind [kg].

| Kind | t / 2t | at t | at 2t | pair (t + 2t) with the allowance |
|---|---|---|---|---|
| T1, 100 % | 4 s / 8 s | 0.96-0.96 | 1.93-1.93 | 3.18-3.18 |
| T1, 50 % | 4 s / 8 s | 0.48-0.48 | 0.95-0.95 | 1.57-1.57 |
| T2, 100/50/25 % | 6 s / 12 s | 0.85-0.85 | 1.69-1.69 | 2.79-2.79 |
| T3, 20 % | 4 s / 8 s | 0.21-0.21 | 0.42-0.42 | 0.69-0.69 |
| T3, 12.5 % | 4 s / 8 s | 0.15-0.15 | 0.29-0.29 | 0.48-0.48 |

- **Per repeat set** (the five kinds at t and 2t): 7.92-7.92 kg, or 8.71-8.71 kg with the allowance (REV-COMB-3 R3-07: 7.92 kg).
- **T4** (DC-D duty cycle, S230 grain, 3 starts) uses 7.02 kg (integrated from the S230 ground record, SIM). v3.1 note (REV-COMB-4 N-07, ESTIMATE from the GNC records): the Combustion T4 objectives (erosion per cycle and soak temperatures at the B1 sizing duty; relight latency from a soaked state) need about 2.0 kg of N2O: burn 1 on the B1 p99 profile (21.76 s; 23.58 s if the life rule is sized on max), a coast of about 19 s, then one relight of about 4.6 s at about 0.47 throttle; a third start is a repeat only, and DC-C carries no Combustion T4 objective. v3.2 note (lead, Combustion v2.4d): GNC confirms it (`interfaces/gnc.json` v3.2 `bde317782574cbd9`, duty_cycles.note_n07_rev_gnc_7): no GNC objective needs the DC-D duty as one firing; GNC's static-fire objectives need DC-D segments, each flown as its own segment or firing inside the A = 150 C case limit (REV-ELEC-3 N-07: the DC-D first burn would cross that limit at about 23.5 s, merged bound [DERIVED]); the A1-like relight objective sits with the shortest firing above. T4 is therefore re-sized to that firing (LEAD 261): planning value about 2.0 kg of N2O [ESTIMATE]; 7.02 kg is the record of the DC-D sequence. The T4 rows of lines 61, 143-145 and 171 stay the DC-D computation [SIM] until Combustion re-runs them on the re-sized profile (OPEN).
- **N2** for the quench: 0.6 kg per firing (60 s at 10 g/s, REPORT §10.2), plus the purges after any abort.

Table 14.2. Series size for N repeats (§6; N <= 8 practical). Grains: 10N firings plus one witness grain per firing kind (5).

| N | Firings | Grains | N2O [kg] (with allowance) | N2 quench [kg] | Fills of a 15 L ground tank (10.4 kg, ASSUMED) at 4.5 MPa |
|---|---|---|---|---|---|
| 1 | 10 | 15 | 8.7-8.7 | 6.0 | 0.8 |
| 2 | 20 | 25 | 17.4-17.4 | 12.0 | 1.7 |
| 4 | 40 | 45 | 34.8-34.8 | 24.0 | 3.4 |
| 8 | 80 | 85 | 69.7-69.7 | 48.0 | 6.7 |

**Stand tank and T1 at 2t (R3-07; LEAD line 194 (8)).** T1 at 100 % for 2t = 8 s uses 1.93-1.93 kg, 96 % of the 2.0 kg flight load. The founders' stand tank is MISSING from every Combustion document. Two ways to run T1:
- a ground tank that holds at least one T1 pair with its heel, for example the 15 L / 10.4 kg tank used as the REPORT's sizing example (§2.7, ASSUMED); or
- the flight tank, with T1 at 100 % shortened so that 2t stays within 80 % of the flight load (ASSUMED usable share): 2t <= 6.0 s, for example t = 3 s and 2t = 6 s. The law decision rests on the T3 holds (§2), so a shorter T1 costs only resolution of the a anchor; Combustion recomputes the T1 signature for the as-fired durations.
The founders state the stand tank capacity in the firing plan.

## 15. Throat check against the frozen prediction (NZ-01; LEAD lines 183 (2), 186 (3) and 194 (5); R3-15)

- Before each firing Combustion issues the predicted throat-area change for that firing, from the erosion model updated only with the measurements of earlier firings, and freezes it: the prediction file and its hash go into the firing record before the firing.
- After the firing the founders measure the throat bore (at least four diameters at 45° spacing, resolution <= 0.01 mm, ASSUMED), photograph the insert, and check it for steps and missing fragments.
- **Refutation (any one):** a throat-area change more than 2 % beyond the erosion predicted for that firing, with the prediction frozen before the firing; a non-axisymmetric step; a missing fragment. 2 % of the area is about 1 % of the 13.7 mm throat diameter (0.14 mm; DERIVED from A_t = 1.479e-4 m2 in the S230 record), well above the gauge resolution.
- A refutation stops the series (§11) and returns the insert to Mechanical and the erosion model to Combustion.

## 16. Cost

Grains (§14), N2O (§14), N2 for the quench and purges, the stand dynamic Pc transducer (>= 100 bar abs) and its conditioning, the bore gauge or 3-D scanner, the sectioning or CT service and the load cells: TO-QUOTE, delivered to Sønderborg, DK-6400. No price is assumed.
