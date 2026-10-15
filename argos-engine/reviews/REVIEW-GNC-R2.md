# REV-GNC-3: independent review of GNC rev2 (staging_v3.1/rev2) and the sim6 v2.9-dev amendments G, K and V

## 0. Checkpoint (docs/SUPERVISION-WORKFLOW.md)

- **Delivered by:** Space/GNC, author of GNC rev2 (CHANGELOG line 174).
- **Reviewed by:** independent Space/GNC reviewer, REV-GNC-3. I authored no rev2 file, script or result.
- **Date:** 2026-10-13.
- **Nature of evidence:** simulation and analysis only (sim6/run6 v2.9-dev Monte Carlo, seed 101, paired draws).
  - No bench, static-fire or flight data exist for any item.
  - Identical numbers show that a computation repeats. They are not physical approval.
- **Files I wrote:**
  - only my scratch area and hub `reviews/gnc/rev2/`;
  - no report, interface, CHANGELOG, REQUIREMENTS or SUPERVISION file was edited.

## 1. Claim (afirmación)

**(a) The rev2 simulation evidence is reproducible and correctly tabulated.**
- This covers RG-01, the decided G path, K, V, the RG-16 budget arithmetic, the +0.60 kg runs on A1 and B1, and the B1 grain gate.
- Exceptions are listed in §4.

**(b) Four interpretations that the lead's provisional decisions rest on are not supported as stated:**
- the late-commit basis, for line 175 (3);
- the "per-flight provisional support" for the RG-16 definition, for line 175 (6);
- pcf_tmax 0.8 s treated as a free widening, for line 175 (5);
- the 0.30 kg trigger, for line 175 (2).

**(c) The staging JSON is not publishable as gnc.json v3.1.**

## 2. Scope and configuration

### 2.1 Files read (sha256/16)

**Hub `01-systems-gnc/staging_v3.1/rev2/`**
- REPORT-GNC-rev2.md 2edf0360cbc975e5.
- MANIFEST_rev2.sha256 cb5d2c48e8d8fa27 (280 entries).
- results/gnc_json/gnc_v3.1_staging_rev2.json a5564b45ed7fb463.
- results/rg01_refly/rg01_refly.json 8a3b34a08289d5b1, plus the rf_*.csv.gz tables (all manifest-verified).
- results/bitcheck_v29:
  - bitcheck_v29.json e945cc883b459701;
  - bitcheck_v29_run1_FAIL.json 187d4d6ac8d5848d;
  - bitcheck_v29_run1_FAIL.log d3670e606aa69c34.
- results/kfz_pcl/kfz_pcl.json 5f9193f628950610.
- results/kfz_fault_f/kfz_fault_f.json 1d50206be7a19cdb.
- results/rg16_v2:
  - rg16_fct_terms_v2.json 2ae2a6eedd90249a;
  - fct2_A1_H_cal_comp_path d39e319dad954da7;
  - fct2_A1_H_cal_path 703a3640af7ee781;
  - fct2_A1_H_cal_comp_pbk 9f255c7f008e137c;
  - the other 13 fct2 files: structure only, hashes in the manifest.
- results/b1_m60:
  - b1_m60.json f9de38ee5e376774;
  - b1_ref.csv.gz 89ad1277a701fcfb;
  - b1_m60.csv.gz 0f20ffb045b955c6;
  - b1_blf31.csv.gz 40e66e5a294da765.
- Pin lists:
  - sim/pins/pins_rev2.sha256 4c97768d53b57eef;
  - pins_rev2_pre_comb24.sha256 576725b1c6b5e061.
- sim/iface_v3d: MANIFEST ee682a07eb209c83, README 3ea8cf8a42614f1f. The 16 pinned files:
  - ENGINE-BASELINE 508faa652ccbd539;
  - combustion 469727032124329f;
  - electronics v1 42fe12e15baa6e3e;
  - mechanical 4f024ed4ccb4618c;
  - throttle_map_v2 4f2e6d846f7253da;
  - actuator_rate_check_v2 2e1341e06b9e3968;
  - tvc_supply_budget_v1 3ee9d60ad039ed45;
  - rg01_line_states 2939549811d4c381;
  - purge_duration 1ff6bfcd7d2f454c;
  - purge_table 79880ab51139ff99;
  - purge_vented_mass 0038561f71a51502;
  - late_light_spike 57fce738164fd571;
  - late_light_tables 7baa4f6fa76bfdd3;
  - burn_limit_proxy bc95a09b083e45ae;
  - drogue_hold_check 70820e0038be39a7;
  - coil_o3b 1c45d4ed2485d25e.
- sim/gncsim_v2.9-dev_MWFPRSGKV:
  - sim6 f90e0ba8e993ad60, run6 b054a222eff38b6e, engine_v2 f8f6a70289cbf180;
  - tailoff 7ac146f91b11bc5e, aero 6bd19061f857e757, mc1d 5c403c0a6ad6a305;
  - params 67ed7ff7cabb7618, propulsion aceb7be6a727b121, regband 6410f7dadeb20106;
  - run1d c6f357119665b5f9, sim1d 5a83ef71124543a6, sizing 608d522aa1c4ab73;
  - tables e37545f98c7cc366, tvc_analytic 55d9e47f4c97f24d, vehicle f22ba08947596613.
- scripts:
  - m2_rg01_refly 73004f1fd6ffbf21, m2_bitcheck_v29 ef1c8bd71339687a, m2_bit29_runner 4c24129aba762f1e;
  - m2_kfz_pcl 71aa66d8a36de7cc, m2_kfz_fault_f 6f19529337d716b5, m2_mass_est_v2 5720b196a3464ce6;
  - m2_rg16_fct_terms_v2 9e46f9e79b98c5d4, m2_fc_thrust d6364936bf727494, m2_b1_m60 8e2276483da45bc9;
  - m2_web_limit 9caf9e461d3bfff0, m2_mc6 f0252806feda9116, m2_eng03_rate 37b25a4594edc2e3;
  - m2_prop_closure 3f5f613f8bb5f641, m2_relight_v28 8dd91cc2b5427499, m2_gnc_json_v31_rev2 faff9f0c14fcc296;
  - m2r2_env.sh 86b4d8b92dade4b7.

**Other hub files**
- interfaces/CHANGELOG.md:
  - lines 155–175 read at 5d4d377621f1dcbb;
  - the file is now 528f0e26b63f0aa3. Lines 176–177 (Mechanical FA-1 and the lead's decision on it) were added during the review. I read them: they hold no GNC decision, but line 177 (1) and (4) change engine-module mass (see RV3-05).
- 00-requirements/REQUIREMENTS.md fbb9e1205707082f (amendments, lines 101–119).
- reviews/REVIEW-GNC-R1.md a5c6b147c830b67e (REV-GNC-2).
- reviews/REVIEW-GNC.md 33d44f5022ebf5c4 (REV-GNC-1; hash only).
- 02-combustion/data/v2p4:
  - HASHES.txt d5e46452e871a09f;
  - rg01_line_states_v2p4.json 2939549811d4c381;
  - purge_vented_mass_v2p4.json 0038561f71a51502.
- 06-electronics/results/tvc_supply_budget_v1.json 3ee9d60ad039ed45.
- staging_v3.1/rev1/results/start_transient/start_transient.json d2a2ef14b5565d41.

**GNC work area** (read only; outside every manifest)
- out/throat_growth/throat_growth.json ca2e1f62891d5ef9.
- out/mass_est_v2/mest_budget_v1.json 05a2fb5728e73be7 (hash only; its terms are not re-derived here).
- mest2 K-off references, for example A1_none pcllo_re_comp 8f4e258409fbfac9.
- release_rule tables: rel_A1_none_rel1 ae0ce8dd505eb563, rel_A1J_pc_rel1 aa231b129c7de817.

**Not reviewed:** purge_outlet_inputs (Combustion's request; rev2 gives no verdict), b1_of phases, REV-ELEC-1 items, duty cycles.

### 2.2 Environment

- **Run copy:** a verified scratch copy of the staged simulator and scripts.
  - Every script is hash-identical to its staged copy.
  - Simulator data come from the hub `01-systems-gnc/sim/data`.
- **Runtime:** `/opt/engine-venv/bin/python -I`, nice 10, NUMBA_NUM_THREADS=1, one process at a time.
- **Strict inputs:** GNC_STRICT=1, GNC_IFACE_PIN = pins_rev2.sha256, GNC_IFACE = staged iface_v3d.
- **Write protection:** a Python audit-hook write guard refused every write outside my scratch area. Outputs were then copied to `reviews/gnc/rev2/`.

## 3. Criteria and method

- **Reproduction standard:** byte identity of CSV tables, or exact equality of every JSON leaf and per-run statistic.
- **Statistics:** recomputed with my own code (`rvlib.py`, no author code imported).
  - Wilson 95 % intervals.
  - Exact two-sided McNemar test (binomial on the discordant pairs).
  - "Loses" means P is below the comparator with p < 0.05 (the author's adopted rule).
- **Re-flights** used the author's fly functions on the final code, in the scratch copy:
  - bit-check v29, all parts;
  - RG-01 A1_none liq|G73 and pw|G73, 500 runs each;
  - K-off and K-on, A1_none pcllo re_comp, 500 runs each;
  - RG-16 A1 H_cal_comp_path and H_cal_path, 200 runs each, re-evaluated with detector-output statistics added;
  - four amendment-V probes on A1_none, 500 runs each.
- **Derivations:** where a claim needs a quantity the author did not compute, I derived it and labelled it DERIVED (reviewer).
- **RG-16 budget form:** the one adopted at line 168 (5), with the author's conventions.
  - σ = (p50 − p1)/2.326.
  - total = 3·RSS(random) + Σ bias.
  - Allowed total 1 − 650/670 = 2.985 %.

## 4. Results per item

### 4.1 Integrity (item 1)

**Manifest:** 280/280 entries verified. There are 282 files on disk: the 280 entries plus the MANIFEST and the REPORT.

**Pins and strict mode**
- The iface_v3d set matches the 16-entry pin list.
- Strict mode refuses:
  - an unreadable iface (N1);
  - a pin mismatch (N2);
  - a version mismatch (N3);
  - electronics v2 (N4).
- N5 confirms 692 values identical between combustion v2.3 and v2.4.
- All of this reproduced.
- Limits (RV3-07):
  - `engine_v2.pin_check` matches by basename, and does nothing when GNC_IFACE_PIN is unset.
  - The simulator's own data tables are not pinned: tables.py CEA/N2O npz, the regband model, relay and tailoff data.
  - Several script inputs in the work area are not pinned either: throat_growth.json, the v2.8 base-case JSONs, the release_rule tables, the mass_est_v2 references, mest_budget_v1, fct_mest_v2 and fault_f.
  - REV-GNC-2 N4 is therefore only partly closed.

**Bit-check v29, full re-run on the final code**
- Leaves per part: A0 13, A1 78, K 19, V 46, RF 16, G 84, N 24.
- 0 differences against the author's run 1 (A0, A1, K, V, RF) and run 2 (G, N).
- The code hashes run 2 records (sim6, run6, the tool) equal the staged files and my copy.

**Claim "run 1 failed and run 2 corrected the tests without changing the simulator": SUPPORTED.**
- Run 1 (12:15:20) failed two subtests:
  - G1 compared the purge mass with the record liquid drop (81.6 g vs 73.0 g);
  - N4 expected a different KeyError.
- The sim6 and run6 modification times (11:44:03) are before run 1.
- Run 2's code hashes equal the staged files.
- I reproduce the run-1 leaves on the final code.
- Caveats (RV3-08):
  - Run 1 records no code hashes, so its code identity rests on the file times plus my reproduction.
  - G6 was also redesigned between runs:
    - in run 1 it passed with no positive control (no comparison arm showed a start above 200 m);
    - run 2 adds the exact rev1 P30 arm, which shows 6 starts above 200 m;
    - the change is declared in the script docstring but not in REPORT §7.
  - P30_reproduced is reported but is not part of G6's pass criterion.

### 4.2 RG-01 (item 2)

**Reproduced exactly**
- P|lit per state and base, Wilson intervals and exhausted counts (§6).
- P_abort is 0 for liq, pw, pl and e19, and 0.242 / 1.0 for PURGE NOT RUN LO / HI, as in rg01_line_states_v2p4.
- Pairings against liq|none:
  - liq|G73: main2 −9/+4 p .27; four-base pool −21/+7 p .0125, LOSES;
  - pw −7/+4 p .55; pl −3/+1 p .63; e19 −5/+5 p 1.0;
  - prep path: liqP −12/+4 p .077 (A1_none −6/+0 p .031, LOSES); pwP −11/+4 p .12;
  - bf|G73: P .924 / .920 with 32/32 exhausted.

**Re-flights on the final code**
- A1_none liq|G73 and pw|G73 (500 runs each) are byte-identical to the staged tables: 0afa9509026325ac and a038901c424fe2e5 uncompressed.
- So the main tables, flown before the 11:44 code freeze, are what the final code produces.

**0.81 s plan**
- Largest E0→E2 given light reproduced:
  - 0.499 s (liq), 0.626 s (pw), 0.573 s (pl), 0.730 s (e19), 0.628 s (nrLO);
  - margins 0.311, 0.184, 0.237, 0.080 and 0.182 s.
- e19|G73|L400 loses heavily:
  - −39/+3 against liq|none|L400;
  - −43/+2 against e19|G73.
- The report excludes it because the decided path always flows ≥ 2.387 s. That exclusion is valid on the decided predictor path: the predictor commits in 2000/2000 runs, flow ≥ 2.387 s, lead ≥ 2.66 s.
- It is not valid under the provisional late-commit rule (line 175 (3)). That rule allows flows from 1.9 s (lead 1.7–2.3 s), which is exactly the e19 state.
- "The plan holds" must be scoped to the predictor path (RV3-02).

**Plateau with a P0 offset (L400o)**
- The report gives −17/+9, p .17, against liq|G73|L400o.
- Against the nominal pw|G73 it is −17/+5, p .017: LOSES.
- Against pw|G73|L400 it is −11/+6, p .33, so the two causes are not separated.
- The report names only the first comparator (RV3-09).

**285 m trim: reproduced**
- 0 exhausted in liq|G73|h285 and pw|G73|h285 on A1_none and A1J_pc.
- Reserve minima: 4.8 / 9.6 g (liquid) and 15.0 / 19.3 g (pw).
- Against the untrimmed arms: −8/+13 p .38 (liq), −7/+11 p .48 (pw).
- Against liq|none at 300 m: −9/+9 and −8/+9, p 1.
- Scope limits (RV3-06):
  - Flown only on the two main bases and on the liquid and purged-worst tables.
  - The four-base liquid loss at 300 m (−21/+7) is not re-tested at 285 m.
  - pl, e19, the prep path, the plateau and the failure states are not flown at 285 m.
- The trim changes the failure mode:
  - exhaustions disappear;
  - new landing failures appear: touchdown horizontal speed 1.0–1.8 m/s (criterion 0.5 m/s), flagged crash;
  - all of them are at winds of 6.96–7.84 m/s, above the provisional launch commit W10 < 6 m/s;
  - for W < 6 m/s, P is 364/364 (363/364 for A1J_pc liquid).

### 4.3 Amendment G (item 3)

**Decided path reproduced** (e19|G73, four bases, 2000 runs)
- The predictor commits in 2000/2000 runs, at 88.8–129.6 m.
- The gate opens at 219.5–255.3 m. Gate to commit ≥ 3.68 s (p01 4.07 s).
- |a_z,f| after the gate opens: p99 1.22 m/s², max 1.33 m/s².
- 0 spurious starts.
- E0 height: p50 44.7 m, min 34.7 m.
- Flow ≥ 2.387 s; purge mass 69.7–73.0 g.
- In all 649 runs where the plain trigger fired, the commit came ≥ 2.66 s before it.

**Hypotheses**
- **H-G1** (no commit during the drogue transient): tested as stated. Both refutation criteria were evaluated (commit before the gate opens; |a_z,f| > 1.5 m/s²). Not refuted, but only inside the quasi-steady, massless drogue model.
- **H-G2** (the 1.9 s floor costs no P): not refuted, but the floor never binds (lead ≥ 2.66 s). This shows the floor is inactive; it does not measure the floor's cost.
- **H-G3** ("delay T_fire instead" is safe): refuted. A commit at the plain trigger gives P 0.000 / 0.000. Reproduced.
- **P30 fix:** supported.
  - The rev1 P30 arm gives 6 starts above 200 m.
  - The gate-off, constant-acceleration variant gives 6 flagged spurious.
  - The decided sequence gives 0 starts above 160 m and 0 spurious.

**Late-commit table: reproduced**
- Forced commit at 100 / 90 / 80 / 70 m gives P .992/.986, .946/.932, .446/.458 and .018/.022.
- Pooled against the decided commit: −3/+4 at 100 m; −51/+2 at 90 m (LOSES).

**Claim "a T_fire delay up to ~0.6 s costs no measurable P": NOT SUPPORTED.**
- The 100 m arm hides the effect: only 3 of its 1000 runs exceed a 0.5 s delay.
- I paired every forced-commit run with its decided-commit twin, keeping the runs that succeed with the decided commit. Share lost, by actual delay:

| T_fire delay | Share lost |
|---|---|
| ≤ 0.2 s | 0.2 % |
| 0.2–0.3 s | 1.4 % |
| 0.3–0.4 s | 0.9 % |
| 0.40–0.45 s | 4.1 % |
| 0.45–0.50 s | 6.2 % |
| 0.50–0.55 s | 7.4 % |
| 0.55–0.60 s | 22.4 % [15.8, 30.8] |
| 0.60–0.65 s | 26.5 % |
| 0.65–0.70 s | 46 % |

- Unpaired P by lead (commit to plain trigger):

| Lead | P |
|---|---|
| 1.30–1.40 s | 0.040 |
| 1.65–1.70 s | 0.691 |
| 1.70–1.75 s | 0.789 |
| 1.75–1.80 s | 0.883 |
| 1.80–1.90 s | 0.936 |
| 1.90–2.00 s | 0.986 |

**The −1.7 s rule**
- At a lead of about 1.68–1.70 s, the delayed-relight P (about 0.69–0.79) crosses the PURGE NOT RUN LO P_total.
  - That P_total is 0.743–0.754: nrLO|none .986/.980 and nrLO|G73z .994/.986, each × (1 − 0.242).
- So −1.7 s is a break-even rule under LO, not a no-cost point.
- P_total ≈ 0.75 is the right comparator only if LO applies.
  - Under HI, P_total is 0, so any commit with a lead of about 1.3 s or more (P 0.04–0.79) beats skipping the purge.
  - "P about 0 for the delay rule" holds only for leads below about 1.3 s.
- The contingency is never reached on the decided path in the Monte Carlo. How likely it is depends on the gate failing to open, for example under canopy oscillation, which is not modelled. Not quantified.

### 4.4 Amendment K (item 4)

**Pairing is valid.** I re-flew A1_none pcllo re_comp with kfz_on 0 and 1 on the final code:
- K-off is byte-identical to the stored rev1 K-off table;
- K-on is identical to the rev2 table (.996 → .860, −68/+0);
- the same FSW sits on both sides of the pair, so there is no N1-type mixing.

**The FSW of the K evidence is not FSW-R2.**
- The K arms use the mass-estimator Pc-lost configuration: Pc lost from the pad, comb prior, no decided release predicate, no fct_comp.
- FSW-R2 has no Pc-lost arm.
- The refutation does not depend on that, because the mechanism (a frozen k_hat cannot learn) is configuration-independent. The replacement must still be flown on FSW-R2.

**Mechanism confirmed**
- With the freeze, k_hat stays at 1.000. Without it, k_hat learns the open-loop factor (about 0.85–0.875).
- K-on failures are touchdown tilt above 5° and tip-over.
- The K-off learning reference F/tsc carries no throttle-map error (not modelled). The replacement's refutation clause covers this.

### 4.5 Amendment V (item 5)

**R0–R3 reproduced on both bases**
- Engine lit:
  - R1: .990 / .986, release at 100 ms;
  - R2: .990 / .984, release 40–70 ms, estimate at release ≥ 48.4 N;
  - R2 at pcf_k 0.875: .990 / .988, release 40–80 ms;
  - R2 with the L400 plateau: .986 / .976, release 440–470 ms, 0 aborts;
  - R3: 0/1000; R0: .392 / .396.
- Undetected flame-out:
  - R1 releases a dead vehicle in 1000/1000 runs (touchdown p50 −32.3 m/s);
  - R2 and R3 hold the drogue in 1000/1000 (touchdown p50 −21.8 m/s);
  - largest R2 estimate: 29.92 N (A1_none, wind 7.30 m/s) and 32.98 N (A1J_pc, wind 7.52 m/s), both below 37.16 N;
  - for W < 6 m/s the largest estimate is 18.75 / 20.85 N.

**Flame-out model**
- The flame-out is at E2 (pcf_dt 0) and undetected: the ECU stays in RUN.
- No cold-flow thrust is modelled after the flame-out.
- Only pcf_dt 0 was flown. The valid-Pc branch releases 5–12 ms after light, which bounds the onset window to about 0–12 ms.

**Reviewer probe: pcf_tmax 0.8 s with flame-out** (A1_none, pw|G73, R2, 500 runs)
- Maximum estimate 35.20 N: margin 1.96 N (5.3 %) to 37.16 N.
- p99 27.14 N, against 20.68 N at 0.5 s.
- In 44 of 500 runs the estimate keeps growing after 0.5 s, by up to +21.0 N.
  - Worst run 218: 14.2 → 35.2 N, wind 7.30 m/s, gust scale 1.39.
  - The runs that grow have mean wind 6.1 m/s, against 3.9 m/s for the others.
- For W < 6 m/s the maximum is 18.75 N at 0.5 s and 20.06 N at 0.8 s.
- Interpretation: gust-driven drag changes on the drogue show up as "thrust" against the baseline frozen at E0, and a longer window collects more of them.

**Reviewer probe: L400 × pcf_k 0.875** (the author did not fly this combination)
- Releases at 440–470 ms, 0 aborts, P .988 (−1/+2 against L400 alone).
- The tables at pcf_tmax 0.5 s and 0.8 s are byte-identical, because every release happens before 0.5 s.
- The deadline margin is 30 ms at 0.5 s and 330 ms at 0.8 s.

**Soundness of pcf_tmax 0.8 s**
- It widens the plateau margin.
- But the plateau and flame-out margins are coupled through the window length: 0.8 s alone cuts the flame-out margin from about 7 N to 2 N on A1_none, in winds above the launch-commit limit.
- No flown run released later than 470 ms, so releases between 0.5 and 0.8 s and the landings after them are unflown.

**R2 margin adequacy: not demonstrated.** Each of the following acts on the same 33.0-to-37.16 N gap and is unmodelled:
- canopy breathing, pendulum motion and riser elasticity (the drogue is massless and quasi-steady; the snatch itself happens at deployment, long before E0, but its after-oscillation is not modelled);
- accelerometer bias drift and the vibration spectrum at the IMU (the vibration term is ASSUMED at 2.0 m/s² × F/Fmax and is zero with the engine dead);
- cold-flow apparent thrust after the flame-out.

### 4.6 RG-16 (item 6)

**Budget arithmetic reproduced**
- H_cal_comp_path, single-frame form: 4.453 %, FAIL.
  - Frame σ 1.047 %, mass σ 0.143 %.
  - Bias 1.281 % = mass bias 0.915 + purge term 0.350 + |b_sys median| 0.016.
- H_cal_path, single-frame form: 5.268 %, FAIL.
- Form B (per-flight): 2.486 % PASS (comp), 3.707 % FAIL (H_cal).
- The over-read side passes in every form.
- Realised Monte Carlo: 0/1000 misses at 670 N.

**Barrier-element statement**
- The arithmetic is correct: 4.453 − 0.350 = 4.103 %.
- It also holds for the instantaneous detector-output form: 3.85 % without the purge term, still a FAIL.
- It does not hold for windowed forms between 0.2 and 0.5 s, where the purge term decides pass or fail: at 200 ms, strict form, 3.225 % fails and 2.875 % without the purge term passes.

**Can the lead's definition be computed from the rev2 data?**
- Not from the stored files. They hold:
  - pooled single-frame quantiles;
  - per-run eps p1 / min / median;
  - b_sys at the onsets;
  - the over-read held maximum.
- The miss-side error distribution after the 3-frame hold is not stored.
- It can be computed by re-evaluation. I re-ran A1 H_cal_comp_path and H_cal_path (200 runs each) on the final code.
  - Every stored per-run statistic reproduced: held max, frame count, eps min / p1 / median, with 0 mismatches.
  - The pooled quantiles are identical.
  - I then recorded the frame streams the detector sees.

**Results for H_cal_comp_path** (the flown FSW-R2 configuration; allowed total 2.985 %)
- **Frame noise:** sd 0.986 %; lag-1 / lag-2 correlation 0.616 / 0.378. White noise through the 20 ms filter would give e^−0.5 = 0.607 and e^−1 = 0.368. Systematic part σ 0.347 %.
- **D1, instantaneous detector output** (minimum of 3 consecutive filtered frames of fa/ft):
  - σ 0.961 %, total 4.197 %: FAIL;
  - the hold also lowers the median by 0.563 pp, giving 4.760 %: FAIL;
  - in the detector's own form, min(fa)/ft[k]: 4.488 % / 5.107 %, both FAIL.
- **D2, sustained fault detected within window W** (maximum of the held output over W):

| W | 50 ms | 100 ms | 200 ms | 300 ms | 500 ms | 1000 ms |
|---|---|---|---|---|---|---|
| Strict | 3.876 % | 3.497 % | 3.225 % | 3.086 % | 2.973 % | 2.780 % |
| Window gain credited | 3.835 % | 3.098 % | 2.477 % | 2.145 % | 1.804 % | 1.342 % |

  D2 passes strictly from W ≈ 0.5 s, and from W ≈ 0.2 s with the window gain credited.
- **Per-flight at the detector output** (spread of the per-run median of the held output): 2.319 %. The Form B equivalent is 2.486 %.
- **Empirical cross-check** with the full unflown bias stack subtracted:
  - 11.5 % of instants fall below the allowance (D1);
  - 3 × 10⁻⁵ of 200 ms windows;
  - 0 of 61,318 windows of 300 ms or longer.

**Results for H_cal_path**
- D1: 5.069 % (5.616 % with the hold shift).
- D2: 4.86 to 3.51 % strict; 4.79 to 1.84 % credited, passing credited only from W ≈ 0.5 s.

**Reading**
- After the filter and the hold, the random term barely shrinks (0.961 % against 1.047 %), and the hold lowers the output.
- The single-decision form fails. The per-flight form is the long-window limit of the sustained-fault decision.
- The lead's definition can be computed only once a detection window is stated: a latency allowance from the 670 N plateau. No requirement gives one.
- Its consequence is unassessed. Reviewer arithmetic: 670 N instead of about 500 N for 0.2–0.5 s is about 2–6 m/s of extra Δv.
- The B1 miss-side budget under this definition is not computed in rev2.
- The noise comes from the ASSUMED white vibration model. A real spectrum (combustion or structural lines, aliasing at 100 Hz) would change both D1 and D2.

### 4.7 +0.60 kg (item 7)

**A1 reproduced**
- liq|none|m60: .992 / .980, with 2/2 exhausted.
- liq|G73|m60: .980 / .980 (6/7 exhausted).
- pw|G73|m60: .984 / .978 (6/7).
- The report pairs these against liq|none|m60, which measures the purge effect at +0.60 kg:
  - A1_none −6/+0, p .031, LOSES;
  - pooled −11/+5, p .21 (liq) and −11/+6, p .33 (pw);
  - reproduced, but the comparator is not named in the report.
- The mass effect itself (same arm, with and without the mass) is not significant:
  - liq|G73 −15/+12, p .70; pw|G73 −17/+13, p .59 (pooled);
  - exhaustions go from 2 to 6 and from 2 to 7.
- Exhausted per base at 300 / 290 / 280 / 275 m:
  - liq: 6/7, 5/5, 3/4, 3/3;
  - pw: 6/7, 5/4, 3/3, 3/3.
- Runs 14, 108 and 490 end at the residual even at 275 m. Reproduced.

**B1 reproduced** (FSW-R2, W1p, 500 engines)
- P .988 → .990 (−2/+3), Wilson [.977, .996], 0 exhausted.
- Reserve shift p50 −10.66 g, min −39.18 g.
- Apex p50 62.78 → 62.72 m.
- Default grain gate (re-executed with the author's measurement draws):
  - 364/500 engines kept;
  - P .989 [.972, .996], −2/+2, 0 exhausted;
  - fuel web at end ≥ 2.618 mm;
  - burn limit acted in 1/364 runs (34/500 ungated);
  - 0/364 below 1 mm.

**0.30 kg trigger** (DERIVED by me; no 0.30 kg arm was flown)
- At 280 m, +0.60 kg shifts the tail runs by at least:
  - 10.3 g (run 14) and 26–28 g (runs 108 and 490) on A1_none;
  - 18–44 g on A1J_pc.
- These are lower bounds, because exhaustion floors the recorded value.
- B1 gives −10.7 g (p50) to −39.2 g (min) per 0.60 kg.
- Run 14 has 4.8 g of reserve at 285 m (A1_none liquid; 9.6 g on A1J_pc).
- Linear scaling puts the first re-exhaustion at about 0.07–0.28 kg, below the 0.30 kg trigger.

### 4.8 Staging JSON (item 8)

**Consistent**
- relight_conditions holds the restated predicate (line 168 (1)); the old text is kept.
- purge_bound is superseded by ≤ 76 g / 73.0 g; the old value is kept.
- flight_profile h_target_A1_m_rev2 is 285.0.
- rev2.fsw_declared says "FC_THRUST not armed on A1"; rev2.rg16_v2.status says "NOT armed".
- The K finding says "REFUTED … do not fly the freeze".
- text_fixes_rev1 has 7 entries, matching the report's 6 items. Checked:
  - the 0/200 bound: 1.487 % exact, 1.885 % Wilson;
  - W1p_tot was flown with web_act 1;
  - L400_te flew t_ign_est 1.11 s.

**Stale or inconsistent** (all would be published as they stand)
- (a) Top-level status still says "FC_THRUST (650 N / 20 ms confirmed …)", "A1 300 m baseline" and "FC_THRUST error budget: OPEN (script staged, not run)".
- (b) over_thrust_fc_thrust.proposal still has the threshold "CONFIRMED" and mass_estimate_requirement "≤ 1 % (1 sigma)".
  - Both are replaced by line 168 (5) and by the not-armed decision.
  - The same text appears in open_items[22], open_items[29] and answers_to_requests.lead_fc_thrust_closure_item_1.
  - None carries a supersession marker, and none is listed in changes_rev2.
- (c) amendment_G_late_commit.finding keeps "DERIVED: a T_fire delay up to ~0.6 s costs no measurable P", which §4.3 contradicts.
- (d) relight_conditions keeps the time-only 0xFFFF term without the line 175 (5) status: "replaced in design by R2, proposal to be flown".
- (e) There is no Pc-VALID launch-commit entry (line 175 (4)), and the K replacement is absent from flight_software.
- (f) Lead decisions are folded only to line 172. Line 175 is absent, and the late-commit PROPOSAL is not marked as the lead's provisional rule.

## 5. Findings

### RV3-01: BLOCKING, for the gnc.json v3.1 publication gate only

- **Finding:** the staging JSON contradicts adopted decisions and is internally stale (§4.8 (a)–(f)).
- **Fix:** rebuild as rev2.1. Mark superseded fields, fold in line 175 and this review's outcome, and correct the G rationale. This is text and JSON work only; no new flights.
- **Gates:** gnc.json v3.1 publication. No flight gate.

### RV3-02: MAJOR, late-commit rule (line 175 (3))

- **Finding:**
  - The stated basis is contradicted: paired loss 7.4 % at 0.50–0.55 s and 22.4 % at 0.55–0.60 s of delay.
  - −1.7 s is the break-even only against PURGE NOT RUN LO; under HI the rule throws away P 0.04–0.79 for leads of 1.3–1.75 s.
  - A deadline with no measurable loss would be about plain trigger − 1.9 s.
  - The contingency re-admits flows of 1.9–2.4 s, which voids the e19 × L400 exclusion of the 0.81 s plan check (e19|L400 −39/+3).
  - The contingency's probability is unquantified.
- **Gates:**
  - SIL/HIL freeze (the FSW rule);
  - A1 (Combustion settles LO/HI and the hazard);
  - publication (text).

### RV3-03: MAJOR, RG-16 definition (line 175 (6))

- **Finding:**
  - At the instantaneous detector output the budget fails: 4.20 % (4.76 % with the hold shift) against 2.99 %.
  - The per-flight 2.49 % equals only the sustained-fault decision over W of 0.5 s or more (0.2 s with the window gain).
  - No latency requirement exists.
  - The noise model is ASSUMED.
  - The B1 miss side under this definition is not computed.
- **Gates:**
  - FC_THRUST arming on A1, and on B1 under the new definition;
  - publication (text);
  - A1 FMEA.

### RV3-04: MAJOR, R2 deadline and margin coupling (line 175 (5))

- **Finding:**
  - pcf_tmax 0.8 s lowers the flame-out margin to 1.96 N (35.20 N against 37.16 N on A1_none), through gusts acting on the E0-frozen baseline.
  - Canopy dynamics, cold flow, IMU drift and spectrum, onsets of 0–12 ms, and landing after a 0.5–0.8 s release are all unflown.
- **Gates:**
  - A1 (adopting R2);
  - SIL/HIL freeze (R2 threshold, baseline handling and tmax).

### RV3-05: MAJOR, mass trigger (line 175 (2))

- **Finding:**
  - The 0.30 kg trigger sits above the DERIVED first re-exhaustion at 285 m (about 0.07–0.28 kg).
  - Engine-module mass growth from line 177 (1) (Inconel 718 TC-09) and (4) (bearings) adds to the same budget.
- **Gates:**
  - A1 (mass change control);
  - SIL/HIL freeze (A1 targets).

### RV3-06: MINOR, 285 m trim coverage

- **Finding:**
  - Two bases and two states only; the four-base liquid loss is not re-tested.
  - The trim trades exhaustion for wind-driven landing failures at W10 of 6.96–7.84 m/s, so the launch-commit wind limit becomes binding.
- **Gates:**
  - SIL/HIL freeze (coverage);
  - A1 (W10 < 6 m/s as a hard rule).

### RV3-07: MINOR, pin coverage (remainder of REV-GNC-2 N4)

- **Finding:** the simulator's data tables and the work-area inputs are not pinned or manifested.
- **Gates:** SIL/HIL freeze (configuration control).

### RV3-08: MINOR, bit-check record

- **Finding:**
  - The G6 redesign between runs 1 and 2 is not declared in the report.
  - P30_reproduced is not part of G6's pass criterion: a G6 that cannot reproduce P30 passes, as it did in run 1.
  - Run 1 records no code hashes.
- **Gates:** publication (text).

### RV3-09: MINOR, unnamed comparators

- **Finding:**
  - The m60 pairs measure the purge effect at +0.60 kg, not the mass effect (the mass effect is −15/+12, p .70).
  - L400o loses against the nominal pw|G73 (−17/+5, p .017); the report gives only the line-state comparator.
- **Gates:**
  - publication (text);
  - FMEA.

### RV3-10: NOTE, K evidence configuration

- **Finding:**
  - The K evidence was flown on the mass-estimator Pc-lost configuration, not FSW-R2.
  - The refutation stands; the replacement is unflown.
- **Gates:** SIL/HIL freeze (fly the replacement on FSW-R2 with a map-error band).

### RV3-11: NOTE, B1 default grain gate

- **Finding:**
  - "Lead rule OR a_meas ≥ 1.25" reduces logically to a_meas ≥ 1.25.
  - That means a grain change for 136/500 draws (27.2 %), against 17/500 under the lead rule alone.
- **Gates:** B1 (programme cost).

### RV3-12: NOTE, FMEA and interface

- **Finding:**
  - With FC_THRUST not armed and the K freeze withdrawn, an in-flight Pc loss on A1 has no over-thrust detector. The launch-commit Pc-VALID rule covers only the pad.
  - On the nominal flight, the purge lowers the tank liquid by 81.6 g while venting 73.0 g: 8.6 g boils into the ullage in the tank model.
    - The "≤ 73.0 g" interface figure is vented, vehicle-level mass.
    - Liquid depletion is larger.
    - The reserve results already include this.
- **Gates:**
  - A1 FMEA;
  - Combustion/Mechanical interface note.

## 6. Recomputation table (author vs reviewer)

| Quantity | Author (rev2) | Reviewer | Status |
|---|---|---|---|
| Manifest | 280/280 | 280/280 | identical |
| Bit-check v29 (A0, A1, K, V, RF run 1; G, N run 2) | PASS | full re-run, 280 leaves, 0 differ | identical |
| RG-01 A1_none liq\|G73, 500 runs | stored table | byte-identical 0afa9509026325ac | identical |
| RG-01 A1_none pw\|G73, 500 runs | stored table | byte-identical a038901c424fe2e5 | identical |
| P\|lit, 10 states × bases, Wilson, exhausted | report §1 | same | identical |
| liq\|G73 vs liq\|none | −9/+4 p .27; four-base −21/+7 p .0125 LOSES | same | identical |
| pw / pl / e19 vs liq\|none | −7/+4 .55; −3/+1 .63; −5/+5 1.0 | same | identical |
| Prep path liqP / pwP | −12/+4 .077 (A1_none −6/+0 .031) / −11/+4 .12 | same | identical |
| 0.81 s plan, largest E0→E2 | .499/.626/.573/.730/.628 s | same | identical; scope note (RV3-02) |
| e19\|G73\|L400 | −39/+3 LOSES | −39/+3, p 5.6e-9 | identical |
| L400o | −17/+9 p .17 (vs liq\|G73\|L400o) | same; vs pw\|G73 −17/+5 p .017 LOSES | comparator added |
| 285 m trim | 0 exhausted; −8/+13 .38; −7/+11 .48; reserve 4.8/9.6, 15.0/19.3 g | same | identical; scope note |
| G decided path, 2000 runs | commit 88.8–129.6 m; gate 219.5–255.3 m; ≥ 3.68 s; aq p99 1.21, max 1.33; 0 spurious; E0 44.7/34.7 m; flow ≥ 2.387 s; 69.7–73.0 g | same (aq p99 1.22) | identical |
| Forced commit 100/90/80/70 m, plain trigger | .992/.986, .946/.932, .446/.458, .018/.022, 0/0 | same | identical |
| "Delay ≤ 0.6 s costs no measurable P" | DERIVED claim | paired loss 7.4 % (0.50–0.55 s), 22.4 % (0.55–0.60 s) | NOT reproduced |
| PURGE NOT RUN LO P_total | 0.742–0.753 | 0.743–0.754 | identical |
| K, A1_none pcllo re_comp | .996 → .860, −68/+0 | both sides re-flown, byte-identical | identical |
| V R0–R3, lit / k875 / L400 / flame-out | report table | same | identical |
| V flame-out max, tmax 0.5 s | 33.0 N | 29.92 / 32.98 N | identical |
| V flame-out max, tmax 0.8 s | not flown | 35.20 N (A1_none) | new |
| V L400 × k875 | not flown | 440–470 ms, 0 aborts, P .988 | new |
| RG-16 single-frame (comp / H_cal) | 4.45 / 5.27 % | 4.453 / 5.268 % | identical |
| RG-16 Form B (comp / H_cal) | 2.49 / 3.71 % | 2.486 / 3.707 % | identical |
| Barrier statement | 4.10 % without purge term | 4.103 % | identical |
| RG-16 stored per-run statistics | stored | 0 mismatches (200 runs × 2 cases) | identical |
| RG-16 at detector output | not computed | D1 4.197 % (4.760 %); D2 3.88 → 2.78 % | new: instantaneous FAIL |
| A1 m60 pairs | A1_none −6/+0 .031; pooled −11/+5 .21; pw −11/+6 .33 | same (vs liq\|none\|m60) | identical; comparator named |
| m60 exhausted by base and target | 6/7, 5/5, 3/4, 3/3; 6/7, 5/4, 3/3, 3/3 | same | identical |
| B1 m60 | .988 → .990 −2/+3; −10.7 / −39.2 g; apex 62.78 → 62.72 m | −10.66 / −39.18 g; rest same | identical |
| B1 default gate | 364; .989 [.972, .996]; −2/+2; web ≥ 2.62 mm; 1/364; 0/364 | same (2.618 mm) | identical |
| bf\|G73 | .924/.920, 32/32 exhausted | same | identical |
| 0/200 bound (text fix) | 1.49 % / 1.9 % | 1.487 % / 1.885 % | identical |

## 7. Verdicts on the lead's provisional decisions (CHANGELOG line 175)

### (1) A1 apogee target 285 m: SUPPORTED WITH CONDITIONS

- The evidence reproduces exactly on its flown scope.
- Conditions:
  - Fly 285 m on all four bases, and on pl, e19, the prep path, L400 and PURGE NOT RUN, before SIL/HIL freeze.
  - Enforce W10 < 6 m/s as a hard launch-commit rule.
  - The 4.8 g reserve tail leaves no room for mass growth (RV3-05).

### (2) +0.60 kg: SUPPORTED WITH CONDITIONS

- "No trim below 275 m now" is supported: the mass is not real yet, and at +0.60 kg even 275 m leaves 3/3 exhausted, so a trim alone would not fix it.
- The 0.30 kg trigger is not supported.
- Recommended: re-fly at the actual ledger for any confirmed growth in landing mass of about 0.1 kg or more over ledger v3d, counted across all engine-module changes, including line 177 (1) and (4).

### (3) Withdrawal of "the FC delays T_fire": SUPPORTED. Provisional −1.7 s rule: SUPPORTED WITH CONDITIONS

- The rule is acceptable as a break-even rule under LO only. Its stated basis is wrong.
- Conditions:
  - Restate the basis.
  - Combustion settles LO or HI, and the hazard, for an unpurged start at that point (the refutation clause).
  - Scope "the 0.81 s plan holds" to the predictor path.
  - Quantify how likely the contingency is.
  - If the aim is no measurable loss, use plain trigger − 1.9 s.

### (4) Amendment b refuted, freeze withdrawn, Pc VALID as a launch-commit condition: SUPPORTED

- The replacement must still be flown on FSW-R2 with a map-error band before SIL/HIL freeze.

### (5) R2 replaces the time-only term in design: SUPPORTED WITH CONDITIONS

- R2 over R1 is strongly supported:
  - flame-out: 1000/1000 dead vehicles released by R1, against 1000/1000 held by R2;
  - no loss on lit flights.
- pcf_tmax 0.8 s is not supported as proposed: it lowers the flame-out margin to 1.96 N (RV3-04).
- Before adoption:
  - re-reference or compensate the drogue baseline;
  - re-derive the threshold for the window length;
  - fly both bases at 0.5 s and 0.8 s with the wind distribution, adding onsets of 0.005 and 0.010 s and the late-release landings;
  - get a cold-flow bound from Combustion;
  - get canopy-dynamics data or a model.

### (6) RG-16 random term at the detector output: SUPPORTED WITH CONDITIONS

- "FC_THRUST stays NOT armed on A1" is supported.
- "The per-flight form (2.49 %) is provisional support" is NOT supported:
  - at the instantaneous detector output, after the filter and the 3-frame hold, the total is 4.20 % (4.76 % with the hold shift), against 2.99 %.
- Conditions:
  - The lead states a detection-latency allowance from the 670 N plateau, with its trajectory consequence.
  - GNC then budgets the windowed detector output for A1 and B1.
  - The A1 FMEA records that A1 has no over-thrust detector after an in-flight Pc loss.

### (7) FMEA inputs: SUPPORTED, as simulation inputs

- BLEED_FAULT reproduced: P .924 / .920 with 32/32 exhausted.
- PURGE NOT RUN HI P_total 0 follows by construction (P_abort 1.0).
- About 22 m/s at drogue touchdown matches the drogue-only runs of the V arms (p50 −21.8 m/s). This is an inference: the "both TCs lost / ECU reset" path was not flown separately.

## 8. What remains undemonstrated (desconocidos)

- **Physical evidence:** none of this has been checked on hardware.
- **Drogue canopy dynamics** (breathing, pendulum, riser elasticity): the drogue is massless and quasi-steady. This affects:
  - whether the G gate opens, and the commit;
  - the R2 margins;
  - the RG-16 lever term.
- **After a flame-out:** cold flow; onsets 0–12 ms after E2.
- **IMU:** noise density, bias drift and the vibration spectrum at the mount. The vibration term is ASSUMED white at 2.0 m/s² × F/Fmax.
- **PURGE NOT RUN:** LO or HI, and the hazard of an unpurged late start (Combustion). The probability of reaching the late-commit contingency.
- **RG-16:**
  - the latency requirement and its trajectory consequence;
  - the B1 miss-side budget under the line 175 (6) definition;
  - F_acc against the load cell (T1–T4);
  - mest_budget_v1 terms (bias 0.915 %, random 0.143 %), not re-derived here.
- **K:** the replacement, with a map-error band, on FSW-R2.
- **285 m:** on the other two bases and the other states; mass sensitivity at +0.1, +0.2 and +0.3 kg.
- **R2:** landings after releases between 0.5 and 0.8 s.
- **Configuration:** the unpinned simulator data tables and work-area inputs.
- **Other inputs:**
  - the no-light probability p_nl (P_total is quoted only at 0 % and 5 %);
  - tank-outlet coverage during the purge (Combustion / Mechanical; rev2 gives no verdict).

## 9. Next closure (siguiente cierre)

1. **GNC, for publication:**
   - build a rev2.1 staging JSON: superseded markers, line 175 and this review's dispositions, named comparators, a corrected G basis, the RG-16 detector-output results, and the V probes and their trade-off;
   - a reviewer checks the document;
   - then publish v3.1.
2. **Lead, with GNC:**
   - set the RG-16 latency allowance; GNC supplies its trajectory consequence;
   - GNC then computes the windowed detector-output budget for A1 and B1;
   - decide FC_THRUST arming;
   - add the FMEA entry for an in-flight Pc loss on A1.
3. **Combustion:**
   - LO or HI, and the hazard, for an unpurged start at the −1.7 s point;
   - the cold-flow apparent thrust under the drogue after a flame-out.
4. **GNC, R2 v2:**
   - set the baseline at E2, or compensate it for drag;
   - re-derive the threshold for the window length;
   - fly both bases at tmax 0.5 s and 0.8 s with L400, k875, flame-out and onsets of 0.005 and 0.010 s;
   - fly the late-release landings.
5. **GNC, 285 m and mass:**
   - fly 285 m on the four bases and on pl, e19, the prep path, L400 and nr;
   - fly +0.1, +0.2 and +0.3 kg at 285 m;
   - the lead then resets the trigger.
6. **GNC, K replacement:** fly it on FSW-R2 with a throttle-map error band.
7. **GNC, configuration and records:**
   - pin the simulator data tables and the work-area inputs;
   - record code hashes in every bit-check run;
   - make P30_reproduced part of G6's pass criterion.
8. **Founders, physical, when hardware exists:**
   - a drogue hang or drop test with the flight IMU (axial specific-force drift, canopy oscillation);
   - F_acc against the load cell in T1–T4;
   - the IMU vibration spectrum on the engine mount.

## 10. Overall verdict

**rev2: CONDICIONADO.**
- The simulation evidence reproduces exactly wherever I re-ran it.
- The conditions are RV3-02 to RV3-06, as SIL/HIL freeze and A1 gates.

**gnc.json v3.1 may NOT be published from this staging (a5564b45ed7fb463)** (RV3-01).
- A rev2.1 rebuild with the text and JSON corrections can be published after a document check, with no new flights.
- The technical conditions stay open as flight gates.
- Nothing in this review is physical acceptance.

## 11. Reviewer artefacts

**Location:** `/home/claude/work/shared-fallback/engine/reviews/gnc/rev2/`, with MANIFEST_REV-GNC-3.sha256 d3bca19f1fdb1ca2 (61 files).

- **scripts/**
  - rvlib.py 74bf681a3d696135;
  - guard_run.py 3c4ec98375787fcd;
  - rv_rg16_held.py 74dcf793481eeec0;
  - rv_rg16_budget.py b3af9334f1d7a581;
  - rv_vprobe.py b87b597940fbb68c;
  - s01–s16, rv_kfz*.py and env.sh.
- **logs/:** every analysis output.
- **results/**
  - bit29/bitcheck_v29_reviewer.json 2e464672256d2d29;
  - rg01/ — the two re-flights, gz;
  - kfz/ — K off and K on, gz;
  - rg16held/ — rg16held_*.json, plus rv_rg16_budget.json 65939777a57180ec;
  - vprobe/ — 4 probe tables. Uncompressed hashes:
    - rvR2fo_t08 050332a405a1d822;
    - rvR2L400_t08 8ee6edfbef0888f7;
    - rvR2L400k_t05 and rvR2L400k_t08 68a603c7cf0a4dc1.
- **Not copied:** the two 10 MB npz frame files of the RG-16 re-evaluation. rv_rg16_held.py regenerates them in about 25 s per case.
