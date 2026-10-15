# REV-COMB-3: independent re-review of Combustion v2.4a

2026-10-13. Reviewer seat REV-COMB-3 (independent of the author; the same seat as REV-COMB-2).

**Scope.**
- 02-combustion v2.4a as answered to REV-COMB-2 (R2-01 to R2-13).
- Lead decisions up to CHANGELOG line 186. Lines 187-190 were read for context only.

**Writes.** Only hub reviews/combustion/r3/ and my scratch area. No report, interface, CHANGELOG, REQUIREMENTS or SUPERVISION file was touched.

**Evidence status.** Evidence tags are as in the REPORT. When two computations agree, that shows only that the computation repeats. It is not physical evidence.

## 0. Verdict

**02-combustion v2.4a: REVISE (targeted).**

**Finding count:** 0 BLOCKING, 2 MAJOR (R3-01, R3-02), 8 MINOR (R3-03 to R3-10), 7 NOTE (R3-11 to R3-17).

**What the fixes need:**
- R3-01: a hold table over the existing PURGE NOT RUN record population.
- R3-02: the existing 896 FA-1 histories reduced to a longer-period spectrum, plus a period domain for line 173 from the lead.
- Everything else: text, interface and specification edits.

**Re-review:** a delta check of the new numbers for R3-01 and R3-02. The other items can be checked as a document diff.

## 1. Findings

| ID | Severity | Gates | Finding |
|---|---|---|---|
| R3-01 | MAJOR | GNC alternative of line 186 (1); SIL/HIL freeze (FSW hold value); A1 | The E2 + 0.22 s release hold is derived from one state. The population needs >= 0.30 s on the 200 N ramp, and no hold within W covers lift-flow operation. |
| R3-02 | MAJOR | FA-1 structural acceptance (REV-MECH-2, CAD v3.5.1 freeze); A1 | FA-1 pressure DLF spectrum is truncated at 1 ms (112-146 bar abs at 1.5-10 ms); the line 173 rule has no period domain. |
| R3-03 | MINOR | Airframe/ICD loads; A1 | The 1.8 kN x 4 ms rectangle bounds only to about 20 ms. FA-1 exceeds it at >= 25 ms (whole history) and >= 40 ms (above steady); impulse 28.4 against 7.2 N s. |
| R3-04 | MINOR | FA-1 yield acceptance at 92 bar | The 92 bar design value is below the author's own model-form estimate (92.2-92.9). The published 0.1 ms histories give 90.7 bar, not 89.0, at 0.25 ms. |
| R3-05 | MINOR | OI-38 / GNC R2 v2; CF-3; A1 | The start-level cold-flow margin (1.22-1.30x) rests on Cd x A x G at the start lift, which no test accepts. |
| R3-06 | MINOR | B1 grain gate; T1-T4 | The T1-T4 v2 "oxidiser-flux shown" test is one-sided. |
| R3-07 | MINOR | T1-T4; first static fire | T1-T4 v2 lacks abort criteria, firing-validity rules, the char-removal procedure and counts/N2O (2t = 8 s at 100 % uses 1.93 kg). |
| R3-08 | MINOR | CF-4 | CF-4 v2.0 lacks run red lines, IS-1/IS-2 preparation, the "continuous liquid" probe threshold and a run/N2O budget; §1 is stale; the hardware baseline is pre-RM1-01. |
| R3-09 | MINOR | Next fold; H19 FMEA | Stale text inside the v2.4a fold: 181 (2), 181 (4), and the 316L lip against 177 (1)/178. |
| R3-10 | MINOR | IGN-1; T-series | No stated range for the stand dynamic Pc channel; the >= 70 bar channel clips the 83-88 bar FA-1 peaks. |
| R3-11 | NOTE | Next fold | Items made stale by line 186 after publication (list in §7). |
| R3-12 | NOTE | — | Release basis and mixed ignition-lift basis of the unpurged-start model. |
| R3-13 | NOTE | — | Population statements ("0 in 82 %", "every HI record", the H20 row). |
| R3-14 | NOTE | OI-38 | Line 186 (2) "chamber heat pick-up" points at the wrong location; start-level lit thrust history. |
| R3-15 | NOTE | NZ-01 / T-series | Line 186 (3) "prediction updated by measurement" is circular unless the prediction is frozen before each firing. |
| R3-16 | NOTE | OI-32 | Line 186 (5) wording on the "x9 margin". |
| R3-17 | NOTE | OI-32; GNC reserve | Landing-burn outlet dip (60-80 g) against GNC's ASSUMED 3 % (60 g) unusable residual. |

### R3-01 (MAJOR): the E2 + 0.22 s release hold does not cover the record population

**Where:**
- REPORT l.776 (Recommendation) and l.2419 (OI-31).
- JSON `purge_commit_rule_v2p4a.v.line181_2_answer.below_L_star`.
- Lead line 186 (1): "GNC flies the alternative: unpurged relight with drogue release held to >= E2 + 0.22 s".

**Evidence.** SIM/DERIVED on the author's stated model, using my own quadrature (`r3_unpurged_classes.json` c162cde0363c4917).
- The 0.22 s is the LO-worst unlined gap arrival under the lift-flow bracket (0.193 s) plus the 22 ms A3 detection.
- Table 2.16's own lined LO-worst row already arrives up to 0.220 s, which means a trip at 0.242 s.

Latest A3 trip after E2 over the PURGE NOT RUN records (0 and 2 deg, 540 per group), in seconds:

| Group | 2500 N/s ramp to 200 N | ramp to 500 N | flow held at the lift |
|---|---|---|---|
| LO unlined | 0.282 | 0.177 | 0.727 |
| HI unlined | 0.153 | 0.134 | 0.322 |
| LO lined (reference) | 0.290 | 0.173 | 0.731 |
| HI lined (reference) | 0.269 | 0.177 | 0.627 |

P(released, then A3) per record for a hold H, unlined, shown as mean / max / number of records above 1e-3. Release happens at E2 + H if A3 has not yet tripped.
- Optimistic criterion: the hazard counts only if the gap arrives at or after H.
- Conservative criterion ("cons."): it counts if the trip comes after H.

| H | LO, 200 N ramp | LO, lift flow | HI, 200 N ramp | HI, lift flow |
|---|---|---|---|---|
| 0.01 s (as now) | 0.584 / 1.0 / 324 | 0.803 / 1.0 / 442 | 0.221 / 1.0 / 180 | 0.222 / 1.0 / 180 |
| 0.22 s | 0.054 / 0.41 / 126 (cons. 0.113 / 0.64) | 0.657 / 1.0 / 424 | 0 | 0.039 / 0.30 / 90 |
| 0.25 s | 0.005 / 0.09 / 43 (cons. 0.036 / 0.32) | 0.626 / 1.0 / 388 | 0 | 0.019 / 0.18 / 90 |
| 0.30 s | 0 (cons. 0) | 0.578 / 1.0 / 361 | 0 | 0 (cons. 0.002 / 0.07) |
| 0.65 s | 0 | 0.011 / 0.20 / 62 | 0 | 0 |

**Why it matters:**
- The sentence "With that hold the light-gap-A3 sequence aborts with the drogue attached" (REPORT l.776 and the JSON) is true only at the LO-worst state.
- GNC's sim does not model the post-light vapour gap. GNC therefore cannot see the residual "dead vehicle released" class (about -32 m/s at touchdown) that remains at 0.22 s.
- The hold adds no success. It only turns released-then-A3 into A3-before-release. Any P gain must come from the population states that light without a gap trip (LO unlined mean 0.18 with lift flow, 0.40 on the ramp). The cost of a longer hold must be weighed: REPORT l.1727 records that GNC found a 0.4 s hold costs P.

**Fix (Combustion, no grid re-run):**
- Publish the hold as a function of the post-E2 command profile flown during the hold. Each value is the latest trip over all PURGE NOT RUN records plus one 10 ms frame:
  - about 0.30 s on the 2500 N/s ramp to 200 N;
  - about 0.19 s on the ramp to 500 N;
  - no value within W with the flow held at the lift.
- State which profile the FSW flies while the drogue is held. The line 186 (2) start-level hold applies with Pc invalid, and that case is lift flow.
- Correct l.776, l.2419 and the JSON.
- Give GNC the per-record classes so it can weight them.

### R3-02 (MAJOR): FA-1 pressure DLF stops at 1 ms; the load rule has no period domain

**Where:**
- REPORT §7.6 l.1998: "1.05-1.20 for periods of 0.25-1 ms".
- REPORT l.2002.
- The `fa1_envelope_v2p4a.py` pressure SDOF periods (T_SDOF_P), 0.04-1 ms.
- Line 173: 90 bar abs quasi-static "for all parts"; 92 and 102 bar abs only for parts with periods of 0.25-1 ms.

**Evidence.** DERIVED from the 896 stored head and aft histories.
- Own undamped SDOF with first-order-hold discretisation. Self-test against the analytic rectangle and step: error < 0.1 % (`r3_fa1_check.json` 20f60dbdd6443c4a).

Equivalent static pressure (bar abs):

| Period [ms] | 0.25 | 0.5 | 1 | 1.5 | 2 | 3 | 5 | 10 | 20 |
|---|---|---|---|---|---|---|---|---|---|
| Baseline (vapour once, rounded), head | 90.7 | 86.4 | 79.4 | 111.9 | 129.0 | 138.8 | 134.2 | 112.8 | 89.0 |
| All 896 cases, head | 96.6 | 102.0 | 93.1 | 115.2 | 134.1 | 146.3 | 143.2 | 121.8 | 95.4 |
| All 896 cases, aft | 85.9 | 88.0 | 90.6 | 122.3 | 137.8 | 146.4 | 141.4 | 119.8 | 94.7 |

- The governing case is "as written", O/F 4, tf 1 ms, t_res 0.06, pool q2.
- For periods above 1 ms the 1 ms rise acts as a step: up to 1.66x the 88.0 bar abs head peak (1.67x the baseline 83.0).
- For T >= 1.5 ms these values do not depend on how the history is extended beyond the stored 25 ms. They are identical with the plateau ended at tau_pool and with it held to t_end.

**Why it matters:**
- 90/92/102 bar bound only parts whose governing mode is at or below 1 ms, and nothing shows that every pressure-loaded load path is that stiff:
  - REV-MECH-1 RM1-09 records the modal DLF as OPEN, and lead line 188 (8) asks for its closure.
  - The modal model is axisymmetric n = 0 without internals. Its frequencies are upper bounds, so its periods are lower bounds.
- Candidates with longer periods:
  - the pintle and its servo linkage (Pc acts on the pintle; line 172 itself places the linkage at 1-5 ms);
  - equipment carried by the forward closure (FS-01/MV-P, bleed valves);
  - the nozzle on the J1 lip;
  - the Pc port and its sense line.
- REV-COMB-2 classed closures, bolts and the J1 lip as quasi-static on the shell breathing mode alone. This re-derivation corrects that.
- Mechanical's FA1S step case (DLF 2.0, about 151 bar) bounds every value above. However, it is carried as a sensitivity (REV-MECH-1 C1: J-FWD with A4-70 gives MS_u -0.047), and line 188 (9) keeps FA-1 acceptance at 92/102 bar.

**Fix:**
- Combustion publishes head and aft spectra to >= 20 ms in §7.6, combustion.json and a CSV, and states the period domain of each DLF statement.
- The lead restates line 173 with periods:
  - 90 bar quasi-static is valid only for T <= 0.1 ms;
  - 92/102 bar for T of 0.25-1 ms;
  - for T > 1 ms, the spectrum, or FA1S as the design case until Mechanical's modal closure lists every pressure-loaded load path with its period.

### R3-03 (MINOR): the thrust rectangle is bounding only to about 20 ms

**Where:**
- REPORT l.1997: SDOF "<= 3.05 kN at periods of 0.5-5 ms ... which therefore bounds".
- Line 173: "confirmed bounding".
- REQUIREMENTS l.118: "1.8 kN for 4 ms thrust spike for low-frequency parts".

**Evidence.** Cf 1.35, aft node. The pool plateau ends at tau_pool (64-69 ms, the author's `run()`) and then decays with the fitted 4.1 ms post-spike constant.

| Period [ms] | 5 | 10 | 20 | 25 | 30 | 40 | 50 | 70 | 100 |
|---|---|---|---|---|---|---|---|---|---|
| Rectangle 1.8 kN x 4 ms [N] | 3600 | 3424 | 2116 | 1734 | 1464 | 1112 | 895 | 643 | 451 |
| FA-1 whole history [N] | 2843 | 2413 | 1912 | 1764 | 1640 | 1452 | 1321 | 1160 | 1040 |
| FA-1 above the 87.6 N steady [N] | 2670 | 2236 | 1735 | 1586 | 1464 | 1280 | 1152 | 993 | 872 |

- Impulse above steady: 28.4 N s, against 7.2 N s for the rectangle.
- My first-pass extension (25 ms value held to t_end) gave 48.0 N s and identical SDOF values.
- The author's SDOF (0.5-5 ms, 30 ms window) is reproduced within 1.56 %.
- The excess comes from the ASSUMED pool plateau (about 22 bar).

**Why it matters.** The rectangle covers the 1-5 ms parts it was chosen for. REQUIREMENTS l.118, however, assigns it to "low-frequency parts". Below about 25-40 Hz (vehicle-level modes, equipment on isolators, tank mounts) it is not bounding: it is low by 2.3x at 10 Hz.

**Fix:** state the domain (T <= 20 ms) in §7.6, the JSON and the requirement, and publish the long-period spectrum for the airframe ICD.

### R3-04 (MINOR): the 92 bar design value

- The author's own outflow-form sensitivity puts the design value at about 92.2 bar (4 % form) and 92.9 bar (8 %) (l.2000).
- "The 102 bar sensitivity covers it" is true only for the ultimate case. Yield acceptance is at 92 bar (lines 177 (2), 188 (9)).
- On the published 0.1 ms histories the baseline rounded case gives 90.7 bar abs at 0.25 ms (and 84.8 at 0.04 ms). The author's 89.0 was computed on the 0.05 ms solver output. A user of the published file cannot reproduce 89.0.
- No design change follows: J-FWD A4-80 has yield MS +0.29 at 92 bar.

**Fix:** state 93 bar abs as the design value, or record the excess explicitly; publish the histories at solver resolution, or state the resolution effect. R2-11 stays PARTLY (OI-36).

### R3-05 (MINOR): the cold-flow bound at the start level is conditional

**Where:** REPORT l.1736-1758 (Table 7.3a), JSON `cold_flow_thrust_v2p4a`, line 186 (2).

The arithmetic is reproduced (§3.2). The conditions are not covered:
- At the start level the margin, 13.3 N against 16.31 N, is a factor of 1.22-1.30 on Cd x A x G. Either of these uses it up:
  - a lift offset of 0.048-0.071 mm at the 0.21-0.23 mm start lift;
  - a flux nearer single-phase incompressible (SPI) flow: G_SPI = 1.51-1.52 x G_Dyer at kappa = 1.
- Cd <= 0.80 is accepted only at full stroke (CF-1/CF-3, line 172 (4)). Cd, A(h) and the zero offset at the start lift are not accepted by any test.

**Fix:**
- CF-3 measures mdot, and with the load cell F, at the start-level lift, recording the encoder lift.
- Acceptance: F <= 16.31 N minus a heat allowance, or mdot <= 52.6-56.3 g/s (16.31 N / v_iso).
- The REPORT states the bound as conditional on that measurement.

### R3-06 (MINOR): the T1-T4 v2 oxidiser-flux acceptance is one-sided

**Where:** T1-T4 spec §2 point 2 (l.32-33) and §10 (l.205).

**The defect:**
- "Shown" needs both S + 1.645 sigma < S_total and S - 1.645 sigma <= S_ox. The second condition passes any S below S_ox.
- A law with S < 1 would therefore be classed "oxidiser-flux shown". Two examples:
  - a Marxman form G^0.8 x^-0.2, with S of about 0.73 at T3 (O/F 4.85; DERIVED);
  - a head-end spray effect.
- That would relax the 1.25 gate and drop the rho correction, although the axial profile matches neither modelled law. Regression would peak at the head, and a_meas at x/L 0.97 does not see the head.

**Fix:**
- Make the test two-sided: shown only if |S - S_ox| <= 1.645 sigma.
- If S < S_ox - 1.645 sigma, treat it as "neither shown": the default gate stays, and Combustion re-evaluates the burn limit on the measured axial profile.
- Add the same branch to §10.

### R3-07 (MINOR): T1-T4 v2 is not executable as written

**Present:** instruments and resolutions (§4), the decision and refutation rules, and the data return.

**Missing:**
- **Abort criteria and red lines.** There is no reference to the §7.4 stand matrix or the §10.2 stand rules.
- **A validity rule for aborted or short firings** in the two-duration differential.
- **The char-removal procedure.** It is required ("defined") but not given.
- **The count.** Kinds x 2 durations x N repeats (N from 1 to 32; N <= 8 practical), the grains (plus one witness grain per kind), and the N2O. Using the S230 map, oxidiser only:
  - the five law firing kinds at t and 2t use 7.92 kg of N2O per repeat set, so 16-63 kg for N = 2-8;
  - T1 at 100 % for 2t = 8 s alone uses 1.93 kg, 96 % of the 2.0 kg flight load, so the stand tank capacity or t must be stated.
- **A quote line.** None is given (CF-4 has "TO-QUOTE, Sønderborg DK-6400").

### R3-08 (MINOR): CF-4 v2.0 gaps

**Present:** hardware, instruments with response times, P1-P7 with Table 1, refutation, general safety, data return and a quote line.

**Missing or stale:**
- **Run red lines and abort criteria** for heated holds and flowing runs: wall temperature, catch-volume pressure, relief lift, leak, and a valve stuck open beyond P6(c).
- **IS-1/IS-2 preparation and verification** (how "traps full, short slug, cap at S1" is created and confirmed, with tolerances).
- **The probe threshold that defines "continuous liquid"** (signal level, allowed dropout). P1 and P2 depend on it.
- **A run and N2O budget.** At least 5 runs per state and attitude gives about 75-105 runs before optional runs, depending on whether IS-3 and the 4 deg runs are repeated per azimuth. Each run vents up to 76 g, plus the lift flow and conditioning.
- **§1 l.20-21 is stale.** It still states the PROVISIONAL -1.7 s rule and "proceeds unpurged", against line 186 (1).
- **The C-RL baseline is CAD v3.4.1.** The bleed adapter and lines change under RM1-01 (lead line 188 (1)), so CF-4 must be re-baselined to the frozen v3.5.1 bleed path.
- **P1 mixes lift bases.** Its t_lift of 29.6 ms is the 0.2192 mm value; at 0.2039 mm it is 28.7 ms. The "0.32 s" rounding is unaffected.

### R3-09 (MINOR): stale text inside the v2.4a fold

The v2.4a fold covers lines up to 177 and line 181 (2), (4) and (10).

| Stale text | Where | Against |
|---|---|---|
| "the T_fire delay is <= 0.6 s and costs no measurable P" | l.2073 | Withdrawn by 181 (2) |
| "the 0.81 s plan holds", without the predictor-path scope | l.24, l.415, l.488; JSON `igniter.sequence.v.relight[3]` | 181 (2) |
| "command ABORT at t_E2 + 0.8 s" | l.1732 | 181 (4): pcf_tmax 0.5 s, 0.8 s not adopted |
| "316L lip" | l.32; l.1630 (melt bound on 316L at 1400 C); l.2169 (H19); l.2410 (OI-22) | TC-09 aft section, which carries the J1 lip, is Inconel 718 since 177 (1)/178 |

- The H19 melt-time bound (1.07-5.70 s) must be recomputed for IN718. Its melting range is lower (about 1260-1336 C, AS RECALLED, TO-VERIFY from a datasheet), so the bound shortens.
- R2-09 is downgraded to PARTLY.

### R3-10 (MINOR): range of the Pc evidence channel

- Line 173 names "IGN-1 with the dynamic Pc channel" as the physical FA-1 evidence.
- The stand dynamic channel has a stated bandwidth (>= 10-20 kHz) but no stated range.
- The flight/control transducer is the 070BG (ENG-09, >= 70 bar; l.1775). FA-1 peaks are 83-88 bar abs.

**Fix:** state the dynamic channel range (>= 100 bar abs, with its proof rating) and the flight transducer's behaviour when over-ranged. R2-10 is otherwise confirmed.

### Notes

**R3-11.** Items made stale by line 186 after publication; the next fold must carry them (list in §7).

**R3-12. Basis of the release and the ignition lift.**
- Class split: "release at E2" uses the latency model's E2 (Pc > 3 bar abs held 10 ms). The firmware E2 is the relative rule. At 0.2039 mm the lit plateau is 2.66-3.11 bar abs (l.1720), so in some corners release waits for the b7 term (E2 + 0.10 s). That moves probability from released-then-A3 to A3-before-release; P(success) = 0 is unchanged.
- Lift basis: PURGE s/cm3 is the 0.2039 mm value, while t_lift (29.6 ms) and the confirmation-time pool come from the 0.2192 mm runs.

**R3-13. Population statements.**
- "0 in 82 % / 77 %" (l.775) holds for lift flow only. On the ramp it is 60 % / 53 %.
- "In every HI record" fails for HI lined on the ramp: 20 of 540 records succeed.
- The H20 row (l.2170) quotes population means of 0.22-0.58 (ramp only); Table 2.17 has up to 0.80.
- Line 186 (1)'s parenthetical describes the LO mechanism. The HI worst state never lights (A2 under the drogue).

**R3-14. Line 186 (2), heat location and lit thrust.**
- The 2.8-3.7 kW threshold is for heat added at tank pressure, before the throttling (injector or feed soak-back).
- Chamber heat at 1.03-1.3 bar converts only 0.15-4 % per joule. At 1.3 bar the margin is approached only near 600 kJ/kg.
- The TO-VERIFY should therefore name injector-body temperature at the relight.
- GNC's R2 v2 should use the grain_q1d start-level lit history, which is fuel-starved for 0.1-0.4 s at 0.2039 mm (l.1720), not 62.5 N x pcf_k.

**R3-15. Line 186 (3).** "Prediction updated by measurement" refutes nothing if the update uses the same firing. Freeze the prediction before each firing, updating it only with earlier firings.

**R3-16. Line 186 (5).** The margin is 766 g of liquid left at the end of the purge flow, which is 9.3-9.7x the 78.6-82.5 g that 13.6 mm holds. The 81.6 g depletion is already inside the 766 g basis; it is not the reference of the "x9".

**R3-17. Landing-burn outlet dip (extension, DERIVED).**
- Same correlation as the author, centre outlet, flat bulkhead, no tilt, g' bounded below by F / 13.6706 kg.
- Dip onset comes at 60-62 g of liquid (125 N), 68-69 g (250 N) and 78-80 g (500 N).
- GNC rev1's ASSUMED unusable residual is 3 % = 60 g (REPORT-GNC-rev1 l.161 and l.296), so the usable reserve (55-65 g) could be up to about 20 g lower.
- Route this to OI-32 and GNC. The outlet geometry is MISSING.

## 2. (a) Status of the R2 items

| Item | Author | R3 | Basis |
|---|---|---|---|
| R2-01 | Closed in text | CONFIRMED | A4 filtered; E1 closure-or-deadline; A14 in §7.3/7.4 and the JSON. The remaining "30 bar raw" hits are data (raw time above 30 bar <= 1.9 ms). |
| R2-02 | Closed in text | CONFIRMED | One safing rule. "wait >= 5 s" appears only in superseded text, §13, or "supersedes" notes. |
| R2-03 | Closed on paper | PARTLY | Envelope delivered and reproduced exactly. REV-COMB-2 item 2 asked for a 1-5 ms DLF; for pressure it was not delivered, and the thrust domain is not stated (R3-02, R3-03). |
| R2-04 | Closed in the specification | CLOSED | Burden reversed, T3 carries the decision, sigma and repeats, errs-safe rho. New defects R3-06 and R3-07. |
| R2-05 | Closed in the interface | CONFIRMED | Key-level SUPERSEDED tags (e.g. the 42.85 entries), `relief_v2p4a`, `superseded_v2p4a`. The remaining 7.5 MPa hits are a seat-load row or describe mechanical.json. |
| R2-06 | Closed in text | CONFIRMED | §9.1; CF-4 P4 per tap and phase; P5 brackets. |
| R2-07 | Closed in text | CONFIRMED | OI-33 stays open. |
| R2-08 | Closed in text | CONFIRMED | — |
| R2-09 | Closed in text | PARTLY | 316L lip text (R3-09). |
| R2-10 | Closed in text | CONFIRMED | Channel range (R3-10). |
| R2-11 | Partly | PARTLY | R3-04; OI-36. |
| R2-12 | Done by lead | CONFIRMED | — |
| R2-13 | Recorded | CONFIRMED | Acted on by line 186 (4); the REPORT notes are now stale (R3-11). |

## 3. (b) Re-derivations with own code

### 3.1 Unpurged-start classes (`r3_unpurged_classes.py` 0ad0b7caaec98845; json c162cde0363c4917)

**Model:** the author's, as stated in §2.8. The code is not a copy of the author's.

**Numerics:**
- Asserted input hashes.
- Deterministic quadrature over the exact n_run CDF: 40 000 cells, n_run = U(0.05, 0.30) + one of the 54 confirmation times.
- My own parse of the 2160 PURGE NOT RUN records.
- My own flow integral from the S230 map (spread of mdot_ox across P_tank recorded).
- Every later void is followed. Modes: lift flow, ramp to 200 N, ramp to 500 N; both conventions.

**Results against Table 2.17** (worst over conventions; ramp / lift):

| State | No light | A3 before release | Released, then A3 | Success |
|---|---|---|---|---|
| LO worst unlined, author | 0.242 | 0.046 / 0.040 | 0.712 / 0.717 | 0 |
| LO worst unlined, R3 | 0.2425 | 0.0457 / 0.0400 | 0.7117 / 0.7175 | 0 in every mode (also 500 N) and convention |
| LO worst lined, author / R3 | 0.135 / 0.1360 | 0.046 / 0.040 both | 0.819 / 0.825 vs 0.8183 / 0.8240 | 0 / 0 |
| HI worst, both | 1.0 | 0 | 0 | 0 |
| Population LO unlined, author / R3 | 0.012 / 0.0118 | 0.005 / 0.0040 | 0.58 / 0.80 vs 0.584 / 0.803 | 0.40 / 0.18 vs 0.400 / 0.181 |
| Population LO lined, author / R3 | 0.003 / 0.0035 | 0.003 / 0.0025 | 0.52 / 0.77 vs 0.523 / 0.768 | 0.47 / 0.23 vs 0.470 / 0.226 |
| Population HI unlined, author / R3 | 0.771 / 0.7711 | 0.008 / 0.0067 | 0.22 / 0.22 vs 0.221 / 0.222 | 0 / 0 |
| Population HI lined, author / R3 | 0.516 / 0.5165 | 0.006 / 0.0053 | 0.44 / 0.48 vs 0.440 / 0.478 | 0.04 / 0 vs 0.037 / 0 |

**Agreement checks:**
- The share of LO records with P(success) < 0.05 is 0.8185 unlined and 0.7741 lined, identical to the author.
- P(no light) agrees with the records within 0.0011. The first-void-only classes agree with the author within 0.0009.
- No record has C2 > 0, and no record trips on a second void.

**"P 0 at the worst states under LO and HI": CONFIRMED within the model.** At HI worst there is no light. At LO worst:
- The first slug lasts t1 = 0.260 s at lift flow.
- A light after the 23.4 cm3 void would need W >= 0.849 s, so every light falls in the first slug and the void follows.
- At a constant 500 N the void still lasts 0.055 s, longer than the 22 ms A3 detection.
- Making it shorter than 22 ms needs phi > 16.6. The 4.0 mm stroke reaches only about 14.5-15.5 (area ratio to the start lift).
- So no reachable flow avoids A3: GNC's P_total ~0.75 is refuted within the slug model.

**Physical status:** the slug idealisation, vapour-flow scaling and flame survival are ASSUMED. CF-4 O-3 and IGN-1 are the evidence.

### 3.2 Cold-flow bound (`r3_cold_flow_bound.py` 2ab9ca8ed50f28c5; json 69e164645dd8a296)

**Method:** my own CoolProp-based Dyer and HEM fluxes and isentropic equilibrium expansion. All 54 CSV rows are reproduced to 9.4e-6.

| Command | Lift [mm] at 283.15 / 286.7 / 289.5 K | Bound [N] | Table 7.3a |
|---|---|---|---|
| 62.5 N | 0.228 / 0.219 / 0.213 | 12.50 / 12.96 / 13.33 | 12.5-13.3 |
| 200 N | 0.662 / 0.633 / 0.611 | 35.62 / 36.67 / 37.48 | 35.6-37.5 |
| 500 N | 2.431 / 2.211 / 2.059 | 119.90 / 118.65 / 117.77 | 117.7-119.9 |
| 4.0 mm stroke | 4.0 | 181.46 / 195.26 / 206.49 | 181.5-206.5 |

**Further reproduced values:**
- v_iso: 289.65 / 300.99 / 310.19 m/s. G_Dyer: 53 506 / 55 405 / 56 854 kg/m2s.
- Command at which each threshold is reached:
  - 4.16 N: already at the start level;
  - 16.31 N: 87.75 / 84.0 / 81.25 N;
  - 37.16 N: 207.5 / 202.5 / 198.5 N.
- Heat at tank pressure needed to reach 16.31 N: 84.8 / 74.2 / 66.1 kJ/kg, that is 3.66 / 3.20 / 2.84 kW.
- Heat added after the throttling, extra work per joule: 0.0015-0.0027 at 1.03 bar, 0.023-0.041 at 1.3 bar, 0.062-0.107 at 2 bar, 0.127-0.203 at 4 bar.

**Conclusion:** the arithmetic is CONFIRMED. The physical conditions are in R3-05 and R3-14.

### 3.3 Tank-outlet arithmetic (`r3_tank_outlet.py` b740009e266da7da; json 1a15375ee2057478)

All values are reproduced:
- Depth at the 766 g end-of-purge minimum: 126.2-132.5 mm (192.8-202.4 mm at 1170 g).
- Wall drop: 2.26 mm at 2.71 deg and 5.73 mm at 6.86 deg. The wall uncovers at 69.3 deg.
- h_c: 7.74-7.97 mm, using the author's Lubin-Springer form; author 7.86 mm.
- 13.59 mm of depth holds 78.6-82.5 g, which is 9.3-9.75x below 766 g.
- Ekman spin-up 359 s; first slosh mode 2.923 Hz.

**Not verified:** the correlation's coefficient and form against the paper, and its applicability to near-saturated N2O. The outlet geometry is MISSING (OI-32).

## 4. (c) FA-1 tables against the line 173 rule

`r3_fa1_check.py` (e655fa5c924c4922) reproduces Table 7.6a exactly and all 56 x 2 cells of Table 7.6b.

| Line 173 statement | Re-derived | Status |
|---|---|---|
| Head peak 83.0 / 84.8 / 88.0 bar abs; aft 0.95-1.00 of head | 83.0 / 84.8 / 86.4 / 88.0; aft 0.951-0.999 | Reproduced |
| Above 45 bar <= 3.65 ms (4.45); above 67.5 bar <= 1.0 ms (1.3); never above 90 bar | 3.60 / 3.65 / 4.45; 0.95 / 1.00 / 1.30; 0 ms | Reproduced |
| Impulse <= 726 bar ms (757) | 721 / 726 / 752 / 757 | Reproduced |
| Thrust spike <= 1.77 kN; SDOF <= 3.05 kN | 1.70 kN (Cf 1.35), 1.77 kN (quasi-steady x 0.975); SDOF max 2.94 kN; author's SDOF within 1.56 % | Reproduced; domain R3-03 |
| DLF <= 1.007 at <= 0.1 ms; 0.25-1 ms gives <= 89.0 / 102.0 bar | 102.0 reproduced; 90.7 at 0.25 ms on the published grid | R3-04 |
| 90 bar quasi-static "for all parts" | Valid at T <= 0.1 ms only; 112-146 bar at 1.5-10 ms | R3-02 |
| Rectangle "confirmed bounding" | True at T <= 20 ms; not at >= 25-40 ms | R3-03 |

## 5. (d) Can the founders execute the specifications?

| Element | CF-4 v2.0 | T1-T4 v2 |
|---|---|---|
| Instruments and resolution | Yes (§3) | Yes (§4); Pc dynamic range missing (R3-10) |
| Acceptance | P1-P7, Table 1 | §2 decision rule (one-sided, R3-06) |
| Refutation | §7 | §10 |
| Abort criteria / red lines | Only general safety (§9) | None |
| Initial-state preparation | IS-1/IS-2 named, no procedure | Grain/ambient recorded; conditioning not given |
| Aborted-run validity | No | No |
| Counts and consumables | No (about 75-105 runs) | No (7.92 kg N2O per repeat set) |
| Quote line | Yes | No |

**Verdict:** both specifications are executable in principle with the stated instruments and acceptance criteria. Neither can be run safely as written without the run rules in R3-07 and R3-08.

## 6. (e) Line 186 decisions

**(1) L* = 1.3 s for both brackets, and no unpurged relight below it: FOLLOWS.**
- The worst-state P(success) is 0 under both brackets (reproduced), and an unpurged attempt carries the released-dead-vehicle class (0.71 at LO worst).
- The refutation of 0.75 holds within the model.
- The parenthetical describes LO only (R3-13).
- The GNC alternative at ">= E2 + 0.22 s" does NOT follow from the evidence (R3-01).
- "LO/HI stays open" is appropriate.

**(2) Command hold: FOLLOWS as a design mitigation.** The bound rises with lift, so the start level gives the lowest apparent thrust after a flame-out. However:
- the 16.31 N margin is conditional on Cd x A x G at the start lift (R3-05);
- "chamber heat pick-up" is the wrong location (R3-14).

**(3) NZ-01 criterion:** usable, but only if the prediction is frozen before each firing (R3-15).

**(4) Configuration: FOLLOWS.** The mechanical.json v2.2 "FA-1 90 bar" entry should carry the period domain once R3-02 is settled.

**(5) Outlet routed to Mechanical: FOLLOWS.** The wording needs correcting (R3-16).

**(6) Launch of REV-COMB-3:** not assessed (no evidence to weigh).

## 7. (f) Stale values

**(i) Inside the fold (author misses):** R3-09.

**(ii) Stale against line 186, which was decided after v2.4a was published (next fold):**

| Stale item | REPORT lines | JSON / CF-4 |
|---|---|---|
| PROVISIONAL "-1.7 s" commit rule and "proceeds unpurged" | 39, 433, 698, 755, 758, 1794, 1870, 1877, 2073, 2208-2209, 2419 | JSON `purge_commit_rule_v2p4a` (rule and proposal), `fmea_input.v.bleed[4]/[5]`, `igniter.sequence.v.start[0]`; CF-4 l.20-21 |
| OI-31 shown open | 39, 55, 776, 1877, 2170, 2209, 2419 | — |
| OI-38 shown as a PROPOSAL | 42, 55, 1758, 2210, 2287, 2426 | `fmea_input.v.flameout_pc_invalid_v2p4a`, `cold_flow_thrust_v2p4a.v.proposal` |
| OI-40 shown as a proposal | 1480, 2428 | `throat_insert_line183_note_v2p4a` |
| Configuration notes (mechanical.json v2.1, electronics.json v2) | 45, 2425 | — |

**No stale hits** for RG-16 "per-flight", "300 m" or the GNC 0.30 kg trigger. The "0.30 kg" hits refer to bleed-valve masses.

## 8. Checkpoint

**Claim.**
- The author's v2.4a numbers are reproduced by independent code: the unpurged classes, the cold-flow bound, the tank arithmetic and the FA-1 tables.
- Two scope gaps carry MAJOR findings: the population release hold (R3-01) and the FA-1 period domain (R3-02).
- Everything is SIM/DERIVED. None of it is physical approval.

**Configuration.**
- 22 inputs, listed in `r3_inputs.sha256` (530994e4ce39ee1e). All verified OK.
  - REPORT 062e307a8d25e1ec.
  - REVISION-RESPONSE-R2 e99595103ee17214.
  - CF-4 a94211a295fe0224; T1-T4 bbf0ea642453dc7a.
  - combustion.json 5237d4584bad38c4.
  - CHANGELOG cfbc03ad2893e94d (190 lines; decisions assessed to line 186).
  - REQUIREMENTS ef308e24783cba0e.
  - data/v2p4a HASHES.txt b5e951a4864badd1: 16 of 16 re-verified.
  - GNC purge_outlet_inputs 47b4deb96ea22043.
- Environment: Python 3.13.16, numpy 2.5.4, scipy 1.18.1, CoolProp 8.0.0; run with nice 10, single thread, `-I`. None of my processes are left running.

**Sources.** REPORT §2.4, §2.8, §7.3, §7.6, §9-§14; REVISION-RESPONSE-R2; the CF-4 and T1-T4 specifications; combustion.json; the v2p4/v2p4a data; REV-COMB-2; REV-MECH-1 (RM1-09, FA1S); GNC rev1/rev2 inputs. The author's scripts were read only for model definitions.

**Files (hub reviews/combustion/r3/, sha256/16).**

| File | Script | JSON | Log |
|---|---|---|---|
| r3_unpurged_classes | 0ad0b7caaec98845 | c162cde0363c4917 | ed5e69a4c894c7bd |
| r3_cold_flow_bound | 2ab9ca8ed50f28c5 | 69e164645dd8a296 | 9853e386d1951fd2 |
| r3_fa1_check | e655fa5c924c4922 | 20f60dbdd6443c4a | 9a9ca9ba4439b456 |
| r3_tank_outlet | b740009e266da7da | 1a15375ee2057478 | 4084a5ebfed3e3c5 |
| r3_stale_scan | 28a7ad6248979b47 | 4feeda91e26366e0 | c3dfe05aa0a66aab |

- `MANIFEST_REV-COMB-3.sha256`: a8ddc0f9854683d4. Running `sha256sum -c` in that directory gives 16 of 16 OK.

**Tests.**
- Reproduction tolerances: Table 2.17 within 0.0012; 54 cold-flow rows within 9.4e-6; Tables 7.6a/b exact; author SDOF within 1.56 %; author part D values exact.
- SDOF self-test against the analytic rectangle and step: < 0.1 %.
- The stale scan re-run gives a byte-identical JSON. Every scan hit was read by hand.
- Not run: grid re-runs, the author's code, and npm test/build (no app change).

**Unknowns.**
- The slug-flow line states, vapour-flow scaling and flame survival in the gap (ASSUMED).
- The post-E2 command profile flown during a hold.
- The records are bracket cases, not probability-weighted.
- The FA-1 construct: fuel inventory MISSING, pool ASSUMED. The extension beyond 25 ms is the reviewer's.
- The natural periods of pressure-loaded load paths.
- Cd, A and the zero offset at the start lift; the injector and chamber thermal state at the relight.
- The Lubin-Springer form and its applicability to N2O; the outlet geometry.
- The IN718 melting range (AS RECALLED).

**Next closure.**
- **Combustion v2.4b:**
  - R3-01 hold table, with l.776, l.2419 and the JSON corrected;
  - R3-02 spectra to 20 ms, with the R3-03 and R3-04 statements;
  - R3-05 conditional bound and CF-3 acceptance;
  - R3-06, R3-07 and R3-08 specification edits;
  - R3-09 text and the IN718 lip-melt recompute;
  - R3-10 channel range;
  - fold line 186 (R3-11).
- **Lead:**
  - restate line 173 with a period domain;
  - fix the REQUIREMENTS l.118 wording;
  - give GNC the population hold table, not 0.22 s;
  - word 186 (3) as "prediction frozen before each firing".
- **Mechanical:** the modal closure (188 (8)) lists every pressure-loaded load path with its period; until then, FA1S is the design case for parts with T > 1 ms.
- **GNC:**
  - fly the unpurged alternative only with the hold table and the actual post-E2 command profile;
  - fly R2 v2 with F_cold and the start-level lit history;
  - check the landing residual under OI-32.
- **Founders:**
  - CF-3 measurement at the start lift;
  - a stand dynamic Pc channel of >= 100 bar abs for IGN-1;
  - CF-4 O-3.
- **Re-review:** a delta check of the R3-01 and R3-02 numbers. The rest by document diff.
