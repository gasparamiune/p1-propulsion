# T1-T4 regression-rate measurement and law form (RG-03), v2

Combustion v2.4a, 2026-10-13. Replaces v2.4 of this file, which is archived as `02-combustion/superseded/v2p4/T1-T4-REGRESSION-SPEC.md`. Responds to REV-COMB-2 R2-04 and to LEAD CHANGELOG line 172 (3). REPORT v2.4a §10.4 summarises this text.

The founders carry out the firings; Combustion reduces the data. This file is a digital specification. It contains no physical result and approves nothing.

Evidence tags: SIM, DERIVED, ASSUMED, DATASHEET, TO-VERIFY, LITERATURE, DESIGN, LEAD, MISSING.

Computation: `02-combustion/src/t1t4_law_resolution_v2p4a.py` (3701b74681de700b) writes `02-combustion/data/v2p4a/t1t4_law_resolution_v2p4a.json` (05b5ae5c20e04bd8). It reduces published SIM histories and re-runs no grain grid.

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
2. **The oxidiser-flux law counts as shown only when all of these hold:**
   - The law signature S = r(x_law)/r(x_ref) is measured at the law stations x/L 0.80, 0.85 and 0.90. The head reference is x/L 0.10, or x/L 0.30 if the spray check in §4 fails.
   - σ(S) <= 1.5 % (LEAD line 172 (3)), on the firings in §3.
   - On the deep-throttle holds T3, and on at least one T1 or T2 firing, S_meas + 1.645 σ(S) < S_total. S_total is the total-flux prediction at the (a, n) fitted to the same firings, computed by Combustion on the as-fired oxidiser history.
   - On the same firings, S_meas - 1.645 σ(S) <= S_ox. S_ox is the oxidiser-flux prediction on the same history, which is about 1.00.
3. **Total-flux shown, or neither law shown:** the default stays.
   - When the total-flux law is shown, Combustion recomputes the burn limit for GNC with 1.1 a_meas and the total-flux form (REPORT §4.6).
4. **Errs-safe correction (DERIVED; proposal for the lead to decide).** This applies whenever the oxidiser-flux law is not shown.
   - The gate uses a_meas,gate = max(1, ρ_max) x a_meas.
   - ρ_max = max over the B1 records of E_B1/E_cal for the calibration set actually fired (§7).
   - With a T3 hold in the calibration set, ρ_max <= 1.004, so the correction is negligible. With T1 at 100 % alone, ρ_max = 1.068.
5. **Law stations.** The stations are x/L 0.80-0.90, outside the aft-end region. a_meas stays at x/L 0.97 for the gate (REQUIREMENTS line 117).

## 3. Firings and what each contributes

T1-T4 are as defined in REPORT §10. The durations below are those of the computation (ASSUMED). The founders' as-fired histories replace them.

| Firing | Role in the law test | S = r(0.85)/r(0.10) over the band a 0.6-1.5, n 0.35-0.68 (DERIVED) | P(show the oxidiser-flux law \| it is true) at σ(S) 1.5 % |
|---|---|---|---|
| T1, 100 % for 4 s | a anchor at high flux; weak law signal | 1.014-1.072 | 0.24-1.00 |
| T1, 50 % for 4 s | second flux | 1.022-1.091 | 0.43-1.00 |
| T2, 100/50/25 % for 2 s each | n fit | 1.022-1.082 | 0.42-1.00 |
| T3, 20 % for 4 s | **law firing** | 1.037-1.120 | 0.79-1.00 |
| T3, 12.5 % for 4 s | **law firing** | 1.046-1.135 | 0.92-1.00 |
| T4, DC-D duty cycle (S230 grain, 3 starts) | life and relight data; law check only | 1.023-1.077 | 0.46-1.00 |

At a x1.0 (Table A1 in §6), T1 at 100 % gives S = 1.024 / 1.035 / 1.049 for n = 0.35 / 0.5 / 0.68. The probability of showing the oxidiser-flux law is then 0.47 / 0.76 / 0.95.

The deep-throttle holds roughly double the signature: S = 1.060-1.092. They therefore carry the law decision.

Regression depth: the law stations need a diameter change of at least 3 mm (ASSUMED), so that a 0.02 mm bore-gauge resolution contributes no more than about 0.5 % to σ(S).
- At 12.5 % (G_ox about 74 kg/m2 s at D 25 mm, a x1.0, n 0.5), r is about 0.5 mm/s (DERIVED). A 4 s hold then gives ΔD of about 4 mm.
- Combustion recomputes the required hold durations from the founders' T1 data before T3 is fired.

## 4. Measurements

Changes from v2.4: stations x/L 0.80 and 0.85 are added, there are four diameters per station, and the witness and quench items are new.

- **Grain mass** before and after each firing. Balance resolution <= 0.1 g. Dry to constant mass.
- **Bore stations.** Measure at x/L 0.10, 0.30, 0.50, 0.70, 0.80, 0.85, 0.90 and 0.97 from the head end.
  - Use at least four diameters at 45° spacing (bore gauge, resolution <= 0.02 mm), or a 3-D scan of the bore with the same stations extracted.
  - Report ovality per station.
  - Locate the stations with a fixture. Position error <= 0.5 mm (ASSUMED).
- **Head-end spray check.** Compare r(0.10) with r(0.30). If they differ by more than the uncertainty, use x/L 0.30 as the head reference.
- **Time histories.**
  - Pc on the control channel at 1 kHz, and on the stand dynamic channel at >= 10-20 kHz with anti-alias filtering (R2-10; REPORT §10).
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

Combustion returns, as SIM/DERIVED:
- S_meas with σ(S);
- the fitted (a, n) for both laws;
- S_ox and S_total on the as-fired history;
- the law decision under §2;
- a_meas at x/L 0.97;
- ρ_max for the fired set;
- the recomputed burn limit.

## 10. Refutation

- **The oxidiser-flux law is refuted** if S_meas exceeds S_ox by more than 1.645 σ(S) on the T3 holds.
- **The total-flux law is refuted** if S_meas + 1.645 σ(S) < S_total(a_fit, n_fit) on T3 and on a T1 or T2 firing.
- **Neither refuted:** the LEAD default gate applies.

Any outcome is test evidence. None of it is flight approval.
