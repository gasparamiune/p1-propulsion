**REVIEW-GNC-R1.** Independent re-review of the GNC rev1 response to REV-GNC-1 (hub 01-systems-gnc/staging_v3.1/rev1).

**Reviewer:** the independent GNC reviewer. This reviewer wrote REV-GNC-1 and did not write rev1.

**Date:** 2026-10-13.

Everything here is simulation, analysis, code reading or arithmetic. A re-run that reproduces a number shows that the computation repeats. It does not show that the physics is right. Nothing here is physical acceptance or product acceptance.

### 0. CHECKPOINT (docs/SUPERVISION-WORKFLOW.md)

**Entregado por / revisado por / fecha:**
- Delivered by GNC (01-systems-gnc); rev1 staged 2026-10-13T10:07:29Z.
- Reviewed by the independent GNC reviewer.
- 2026-10-13.

**Área y configuración:**
- **Area:** Space Systems / GNC.
- **Simulator:** sim6 v2.8-dev with amendments M, W, F, P, R and S (sim6.py f9094b63e64f2324, run6.py 35b5c808487b9339).
- **Interface pin:** /home/claude/work/space/iface_v3c:
  - combustion v2.3, d9ec54fbf450e243;
  - electronics v1, 42fe12e15baa6e3e;
  - mechanical v2, 4f024ed4ccb4618c;
  - ENGINE-BASELINE, 508faa652ccbd539;
  - throttle_map_v2.csv, 4f2e6d846f7253da;
  - actuator_rate_check_v2.json, 2e1341e06b9e3968.
- **FSW record:** v1.4, 08c85849a5da950d.
- **Monte Carlo:** seed 101, 500 runs per base.
- **Re-runs:** /opt/engine-venv, NUMBA_NUM_THREADS=1, one process at a time, nice 10.

**Cambio y afirmación a comprobar:**
- **The response:** rev1 answers RG-01 to RG-20 (REPORT §3).
- **New work:**
  - the decided release rule implemented as amendments R and S, flown with the start plateau and mapped onto TLM_FAST;
  - the pre-scheduled purge mass flown in the A1 reserve;
  - θ at RELIGHT;
  - a stuck-open bleed bracket at 1.0 mm;
  - the ENG-07 EI bracket on the re-routed coil;
  - the RG-16 terms;
  - the FSW record v1.4;
  - the claim "bit-check v1.5 ALL PASSED".
- **Disputes and reports:**
  - GNC disputes the reviewer's RG-16 window hypothesis.
  - GNC reports that the live hub combustion.json lacks igniter.sequence.
- **Lead decisions:** CHANGELOG lines 160–161 adopt or override parts of rev1.

**Fuentes y archivos exactos:** §1.

**Criterios, método y resultados:** §2 (criteria C1–C8), with details in §3 to §6.

**Dictamen y uso permitido:** CONDICIONADO overall. RG-01 stays OPEN and BLOCKING. By item: 7 CLOSED, 11 PARTLY CLOSED with named gates, 2 OPEN (§3).
- **Allowed use:** as the GNC simulation basis for the lead decisions that §5.4 lists as supported.
- **Not allowed:**
  - relight closure;
  - freezing 0.81 s or 1.41 s;
  - arming FC_THRUST on A1 at the decided bleed path;
  - using the interim Pc-invalid rule as a final rule;
  - accepting the stuck-open bleed risk without an FMEA probability;
  - any physical claim.

**Qué sigue sin demostrarse:** §8.

**Próximo cierre:** §9.

### 1. SOURCES AND FILES (sha256/16)

**Reviewed, read only** (paths under hub /home/claude/work/shared-fallback/engine/):

| File | sha256/16 |
|---|---|
| 01-systems-gnc/staging_v3.1/rev1/REPORT-GNC-rev1.md | 2b96c0ec92263d0c |
| MANIFEST_rev1.sha256 (387 entries; header "m2_stage_hub_rev1 v1.4 2026-10-13T10:07:29Z") | 2dbe49919289f0ac |
| results/rev1_items/rev1_items.json | 799258458f0142a5 |
| results/fsw_record/fsw_config_record_v1.json (v1.4) | 08c85849a5da950d |
| sim/gncsim_v2.8-dev_MWFPRS/sim6.py | f9094b63e64f2324 |
| sim/gncsim_v2.8-dev_MWFPRS/run6.py | 35b5c808487b9339 |
| results/v28_checks_v15/bitcheck_v28.json (v1.5) | e1c6d9b6b5292718 |
| results/v28_checks_v13/bitcheck_v28.json (v1.3) | 1c4024b30617d10e |
| results/start_transient/start_transient.json | d2a2ef14b5565d41 |
| results/eng07_6v6/eng07_6v6.json | 162650b8752f9ca7 |
| results/rg16_terms/rg16_fct_terms.json | 3e6d85f0400f70d3 |
| results/khat_offset/khat_offset.json | e34bf4ea9e0104f4 |
| results/purge_cost/purge_cost.json | c591330634246228 |
| results/purge_bleed_1mm/purge_bleed.json | 872a021fc9be0b93 |
| results/web_limit/web_limit.json | 1eb37418cb1762a6 |
| results/mass_est_v2/mest_budget_v1.json | 05a2fb5728e73be7 |
| results/fault_f/fault_f.json | 6e393efb6254ad74 |
| results/gust_criterion/gust_criterion.json | e1e70d26b9c3a5a7 |
| results/rg02/rg02_accounting_v1.json | f6d7cfd257f70b9c |
| results/gnc_json_rebuild_v3_check/rebuild_check_v1.json | b5a7a6e4018bb485 |
| results/relight_attitude_ps10/relight_attitude_v1.json | 06296daef74e8d95 |
| scripts/m2_start_transient.py | 13a80609db37ec98 |
| scripts/m2_web_limit.py | 9caf9e461d3bfff0 |
| scripts/m2_khat_offset.py | 9c3d0c4a15394367 |
| interfaces/CHANGELOG.md (164 lines when read; request scope lines 157–161) | 72853147f71cb860 |
| interfaces/combustion.json (v2.3) | d9ec54fbf450e243 |
| interfaces/electronics.json (v2) | da067408c1594814 |
| reviews/REVIEW-GNC.md (REV-GNC-1) | 33d44f5022ebf5c4 |

**Context, read only:**
- the GNC work area /home/claude/work/space (iface_v3c, out/, the dev tree);
- CHANGELOG lines 162–164, which post-date the request. Their effect is noted in §5.

**Reviewer files** (reviews/gnc/rev1/, sha256/16):
- **rv00_runner.py** 19b38f630ebeb6f0. Runs a scratch-copy GNC script under python -I and refuses any path in the GNC staging or work area.
- **rv01_rerun.sh** 95dc9191d43f72db. Sequential re-runs with every GNC output redirected.
  - Logs: logs/rv01_chain.log 5ae1269749d79f21; rv01_st.log c4b0e48ff8ef2486; rv01_e7.log 6b12854203677488; rv01_bitcheck.log 825aad296e50c2bd.
  - Output: rv01_bitcheck/bitcheck_v28.json 1f51b1ab504d7b01.
- **rv02_compare.py** e4e520b0b791b870 / .json 2d9ae8d230d534b9. Re-flown arms against the published ones, with the reviewer's own exact McNemar.
- **rv03_bitcheck_compare.py** b471fdd8f2f79b4d / .json 0b05470205ef34db.
- **rv04_manifest_claims.py** bb77d4852819a1c5 / .json 0d451b7f7eb2655a. Full manifest re-hash, reference tables, igniter probes and the RG-04 code check.
- **rv05_rg16_window.py** v1.0.1, 9b9581d70264f710 / .json 359d3f61397bc782.
- **rv06_purge_reserve.py** 36fd4f0aada004f5 / .json 3868ac5973ee2f87.
- **rv07_rg16_1mm.py** d6171546a36129be / .json 4d1e7c90e3b6a779.
- **rv08_iface_probe.py** 9f51922ff33e06e3 / .json 19ebb128a77d2ec5.
- **rv09_stats_recompute.py** 363edbec4fa4e75d / .json 0762ca2e9753e3cc.

**Write discipline:**
- Nothing was written outside reviews/gnc/rev1 and the reviewer's scratch area.
- mtime/size snapshots of the GNC work area and the staging, taken before and after the re-runs and the probe, differ by 0 lines.

### 2. CRITERIA, METHOD AND RESULTS

**C1. The staged bytes are the manifest's bytes.**
- **Method:** sha256 of all 387 entries (rv04, part M).
- **Result:**
  - 387/387 equal.
  - Only MANIFEST and REPORT lie outside the manifest, as expected.
  - The manifest does not pin the inputs needed to re-run (N4).
- **State:** Comprobado en su alcance.

**C2. Amendments switched off are bit-identical, and the bit-check passes on the final code.**
- **Method:** m2_bitcheck_v28 v1.5 re-run with all 13 parts (A–H, W, X, P, R, S) on a verified scratch copy (rv01, rv03).
- **Result:**
  - ALL PASSED: 49 "passed" flags, 0 false.
  - Every value equals GNC's v1.5 values (parts A, C–F, P, R, S) and v1.3 values (B, G, H, W, X).
  - GNC's own v1.5 run left part B empty and did not run G, H, W or X on the final code (N3). This re-run closes that gap.
- **State:** Comprobado en su alcance.

**C3. Published P and lost/gained values reproduce.**
- **Method:**
  - Re-flew L400_te on A1_none and A1J_pc, and RR66_EI05 on A1_none and rbl_B1_lead62_pc_k2, 500 runs each, between 10:32:48Z and 10:37:56Z.
  - Compared field by field (rv02).
- **L400_te:**
  - The CSVs are byte-identical (decompressed sha16 93932f3b0a0f1548 and 692f0e5d783cbb80).
  - Against the decided rule:
    - A1_none: 0.972, −11/+2, p 0.0225;
    - A1J_pc: 0.968, −12/+4, p 0.0768;
    - pooled: −23/+6, p 0.0023157, the published value.
  - Against L400 (reviewer comparison): pooled −19/+7, p 0.029.
- **RR66_EI05:**
  - 95 000 values per base are identical. The files differ only by the 4 amendment-S columns (rel_br, rel_vz, st_vz_end, st_h_end).
  - A1: 0.738, −128/+1, p 3.8e-37.
  - B1: 0.982, −7/+0, p 0.0156.
  - Pooled: −135/+1, p 3.1e-39, the published value.
- **State:** Comprobado en su alcance.

**C4. Paired statistics of the purge and stuck-bleed arms.**
- **Method:** reviewer's exact McNemar on the published run tables (rv09). These arms were not re-flown.
- **Result:** every published value reproduces:
  - PS10: −7/+4, p 0.549, with 2 + 2 exhausted runs;
  - PS08: −4/+2, p 0.688;
  - PS10_L400: −11/+3, p 0.057;
  - A1 S313_0: −49/+2, p 1.2e-12, 48 exhausted;
  - A1 S313_1: −10/+2, p 0.039;
  - B1 B313_0: −312/+2, 315 exhausted;
  - B1 B313_1: −3/+4.
- **State:** Comprobado en su alcance.

**C5. The RG-04 ×0.90 clarification.**
- **Method:** the reviewer's rg05 code and GNC's conditional tables.
- **Result:** CONFIRMED (§4.2).
- **State:** Comprobado.

**C6. "The live hub combustion.json lacks igniter.sequence".**
- **Method:** key probes of every copy run6 can read, and a build probe of the live hub set against the pin (rv04 part I, rv08).
- **Result:** REFUTED (§4.3).
- **State:** Rechazado.

**C7. The RG-16 window dispute.**
- **Method:** GNC's per-run diagnostic, plus reviewer arithmetic (rv05).
- **Result:** GNC's dispute UPHELD (§4.1).
- **State:** Comprobado en su alcance.

**C8. Lead decisions in lines 160–161 are consistent with the GNC evidence.**
- **Method:** the decisions read against GNC's tables, plus reviewer first-order checks (rv06, rv07).
- **Result:** supported in part; 3 MAJOR findings and several NOTEs (§5).
- **State:** Condicionado.

### 3. VERDICT PER RG ITEM

| RG | REV-GNC-1 severity | GNC rev1 claim | Verdict |
|---|---|---|---|
| RG-01 | BLOCKING | OPEN, partly fixed | OPEN, BLOCKING (partial work in §3.1) |
| RG-02 | MAJOR | FIXED | PARTLY CLOSED |
| RG-03 | MAJOR | FIXED | PARTLY CLOSED |
| RG-04 | MAJOR | FIXED as a rule | PARTLY CLOSED |
| RG-05 | MAJOR | FIXED by the lead | CLOSED |
| RG-06 | MAJOR | PROPOSAL | PARTLY CLOSED |
| RG-07 | MINOR | FIXED | CLOSED |
| RG-08 | MINOR | PARTLY FIXED | PARTLY CLOSED |
| RG-09 | MINOR | FIXED by the lead | CLOSED |
| RG-10 | MINOR | FIXED | CLOSED |
| RG-11 | MINOR | FIXED | CLOSED |
| RG-12 | MINOR | PARTLY FIXED | PARTLY CLOSED |
| RG-13 | MINOR | FIXED on the GNC side | PARTLY CLOSED |
| RG-14 | NOTE | DEFERRED | OPEN (assigned) |
| RG-15 | NOTE | rule FIXED, simulator deferred | PARTLY CLOSED |
| RG-16 | MAJOR | FIXED, with a dispute | PARTLY CLOSED |
| RG-17 | MINOR | FIXED | CLOSED |
| RG-18 | MINOR | FIXED | PARTLY CLOSED |
| RG-19 | MINOR | PARTLY FIXED | PARTLY CLOSED |
| RG-20 | NOTE | FIXED | CLOSED |

**Reasons and gates:**

**RG-02.**
- **Done:**
  - the accounting is per line state, with no weighted mean;
  - p_nl appears only as a sensitivity (0 / 0.005 / 0.02 / 0.05), labelled "no source";
  - the demonstration rule is stated.
- **Not yet usable:** the rows are the 44 cm³ rows, which the coil re-route supersedes.
- **Gate (REV-GNC-1 A1 criterion):** a sourced p_nl,ign (torch qualification / IGN-1) and π_s (Mechanical), applied to the RG-01 re-fly rows before A1.

**RG-03.**
- **Done:**
  - "covers" withdrawn (lead);
  - band records published;
  - burn limit in sim6 and in the FSW model, with a defined action;
  - W1p 0.994 (−2/+1);
  - 0/500 runs below 1 mm of web under the quasi-steady law.
- **Not shown:** under Combustion's total-flux law (truth k = 1.149 a, i.e. a_meas not taken at the station of largest local regression), the defined action still leaves runs below 1 mm of web near touchdown (W1p_tot):
  - 19/500 runs, or 11/483 after the lead's current pre-flight gate;
  - minimum web 0.26 mm;
  - no burn-through; P unchanged.
  - Raising the FSW factor to 1.25 a_meas (W1p_tot_k125) does not change these counts.
- **Report error:** REPORT §2.8 calls these 19 runs "without the limit action". The result file flies them with the action on (web_act 1).
- **Gate:**
  - Combustion fixes the basis on which a is measured at T1–T4.
  - If the total-flux law applies, the lead extends the pre-flight grain-change gate before B1. GNC's scan: "lead rule OR a_meas ≥ 1.25" leaves 0/364 runs below 1 mm and keeps 72.8 % of engines.
  - GNC corrects the §2.8 sentence.

**RG-04.**
- **Done:**
  - the cap rule is written in measured quantities;
  - the corner k_c = k − 2u_k is held fixed in a conditional MC that requires P ≥ 0.99 and no exhausted run;
  - the lead adopted the rule (line 161 (7)).
- **Gate:**
  - T1–T4 values: k, u_k, the 2σ region of (a, n), g and u_g;
  - the rule applied per engine;
  - A1 reserve and P reported at the corner.
- The ×0.90 clarification is confirmed (§4.2).

**RG-05.**
- ENG-03 now requires ≥ 5 F_max/s (2500 N/s) under load, which is the flown value (line 111 (1)).
- Measurement under load stays with B-PNT-1.

**RG-06.**
- **Done:**
  - the criterion is W10 < 6 m/s AND σu(3 m) ≤ 1.0 m/s, as 10-minute statistics before ARM, with an anemometer at 3 m;
  - it was flown at the limit: 500/500 on both profiles;
  - the model-form assumption is labelled (σu imposed as the Dryden intensity).
- **Gate (REV-GNC-1 B1 criterion):** ACEMA site statistics before B1. The lead adopted the rule as PROVISIONAL with site data TO-DEFINE.

**RG-07.**
- B1 62 m on the ENG-07d basis: 0.992 (−3/+1, p 0.625). This equals the reviewer's rg05 value.
- At 7.4 V: 0.992. With the burn limit: 0.998.

**RG-08.**
- **Done:**
  - the rationale is restated (19.8 s against 6.1–7.4 min);
  - the Electronics flag is recorded: UNKNOWN on an encoder fault or P_feed invalid; UNPRIMED when the lift exceeds 0.10 mm for 20 ms;
  - the lead set UNKNOWN = UNPRIMED.
- **Gate:** simulate the flag in the loop, including a late flip (sim6 amendment or SIL), before the SIL/HIL freeze of the relight logic.

**RG-09.** Governance per quantity (line 111 (3)).

**RG-10.**
- The Pc-based B predictor is flown: apex p99 68.99 m, maximum 69.96 m. These equal the reviewer's rg13 values.
- The safety area is sized on the apex.
- The FC software port must carry the same predictor; this is checked at SIL.

**RG-11.**
- (a) Doubling J_ref and g emulates a J-proportional growth law exactly for J ≤ 2 J_ref; the maximum J/J_ref is 1.192. P 0.994 → 0.994; maximum growth 10.97 → 12.15 %.
- (b) The cap search uses the 0.25 m grid.
- (c) Handled under RG-16.
- (d) and (e) are recorded.

**RG-12.**
- **Done:**
  - the lead aligned the REQUIREMENTS;
  - the ENG-07 limit is bracketed in (0.25, 0.5] N·m².
- **Refuted:** GNC's note that the live combustion.json has drifted (§4.3, N5).
- **Gate:**
  - the v3.1 build lists in inputs_read the exact bytes the runs read, including electronics v1 42fe12e15baa6e3e;
  - a current owner source for the TVC loop parameters;
  - RC-03 and RC-07 brought into the hub (Combustion).

**RG-13.**
- **Done:**
  - FSW record v1.4 with an as-flown table and check();
  - the ratchet is recorded explicitly;
  - the v1.3 error is corrected.
- **Gate:**
  - HIL-TR-1;
  - one declared flight-FSW configuration for the RG-01 re-fly (N1);
  - the label defect in start_transient.json fixed (N2).

**RG-14.** Pad-slope specification in ICD-AIRFRAME before the B1 and A1 landing areas are fixed.

**RG-15.**
- **Done:**
  - the rule is decided (line 113 (2));
  - Electronics v2 publishes the 0xFFFF markers (can_interface rg15_pc_invalid).
- **Gate, before the SIL/HIL freeze:**
  - sim6 amendment (b), the freeze of k_est_asc and the apex predictor, with its own API, hypotheses, tests and review;
  - a re-fly of the Pc-lost arms;
  - amendment (c), Pc invalid inside [E2, release] (§5.1).

**RG-16.**
- **Done** (all four actions, at the 0.8 mm path):
  - **Budget line:** 3σ of the random terms (RSS) plus the sum of the bias bounds.
    - A1: 1.408 % at end of burn, 1.344 % in the FC window.
    - B1: 1.88 % and 2.21 %.
  - **Estimator:** flown with the errors in the flow.
  - **A1 offset:** explained (the dispute is upheld, §4.1).
  - **650 N threshold:** re-checked on both sides. The held maximum is ≤ 593.9 N, and misses occur only in non-adopted variants (1/1000 each).
- **Gate:**
  - (i) Re-run the terms at the decided ~31 g/s path, using Combustion's vented-mass table for the final path, on both sides.
    - The miss side (booking residual about 45 g, GNC DERIVED) is unflown.
    - On the false-alarm side, the reviewer's DERIVED estimate is ≤ 595.4 N, a margin of at least 54.6 N (rv07).
  - (ii) The lead adopts the budget form in place of "≤ 1 % (1σ)", together with its two requirement candidates:
    - weighing at ARM, 20 g at 1σ (scale TO-DEFINE);
    - a static-fire flow-calibration residual of 1.5 %.
  - (iii) The FSW and SIL implement the compensation with a CG model (the sim uses the true CG), and HIL verifies it.

**RG-17.**
- The bounds are corrected (0/500 → 0.60 %, 0/200 → 1.49 %), results are given per profile, and the tail criterion is replaced.
- The same pooled-bound wording reappears in §2.10 (see RG-18).

**RG-18.**
- **Done:** fault flights at 670 and 876 N, from ascent and landing, with Pc valid and lost, all detectors active, and the consequence of a miss. The valid window is "no drogue load", with a tether rule for flight C.
- **Gate:**
  - Re-fly the Pc-lost arms after amendment (b): sim6 still updates k_est from F/tsc without checking Pc validity.
  - Correct the §2.10 bounds.
    - 0/800 (0.48 %) and 0/1192 (0.32 %) pool arms that share draws; fault_f.json itself says the pooled bound is "not tighter than the per-arm bound in effect".
    - Per arm, 0/200 gives 1.49 % (exact, one-sided) or 1.9 % (Wilson).
- The arms were flown on the pre-R simulator (b4fe41a2); they carry over through the off-identity confirmed in C2.

**RG-19.**
- **Known terms:** 78.6 ms mean and 84.1 ms maximum (Electronics); GNC decision time p99 45–301 ms.
- **Gate:**
  - an end-to-end HIL budget with each term sourced: IMU group delay, FC and ECU scheduling, CAN, axial modes;
  - T1–T4 logs of F_acc against the load cell, including low-frequency content.

**RG-20.** The builder is fixed. The v3 rebuild shows 7 differences, none numeric, each classified.

#### 3.1 RG-01: partial work only (BLOCKING stays)

- **Release rule and plateau:** reproduced (C3). This supports not adding the plateau to the relight plan.
- **θ at RELIGHT** (not re-flown by the reviewer):
  - maximum 0.76° with a balanced 1.0 mm purge; 0 of 500 runs above 1°;
  - the governing limit is the quasi-steady, massless drogue model;
  - canopy pendulum motion is unmodelled and adds directly to θ.
- **Purge in the A1 reserve:** see §5.2.
- **Stuck-open bracket:** see §5.3. Combustion now says the additive case is the physical one (line 163), so A1 0.896 and B1 0.368 are the governing consequences.
- **FSW configuration:** mixed (N1).
- **Per-state accounting:** on superseded rows (RG-02).
- **Still missing:**
  - hub copies of Combustion's re-routed-coil tables (line 163 cites workdir files);
  - CF-4 (the spec is accepted, line 164 (5); the founders run it);
  - canopy data;
  - B-FD-1;
  - the re-fly itself (started, line 164 (9)).

### 4. RULINGS ON THE DISPUTED AND QUESTIONED CLAIMS

#### 4.1 RG-16 comparison-window hypothesis: GNC's dispute is UPHELD; the reviewer's hypothesis is withdrawn

Evidence (rv05, on GNC's per-run diagnostic m2_khat_offset v1.1, 200 runs per profile):
- **The "halves" are not equal halves.** The code splits the window at t0 + 0.5 s: the first 0.5 s against the rest. The A1 window is 1.32–1.98 s (p01–p99), median 1.63 s. This does not change the ruling.
- **The offset is present within a single window:**
  - first part, median −1.67 %;
  - second part, median −1.27 %;
  - negative in 198/200 runs (first part) and 200/200 runs (second part).

  A difference between two comparison windows cannot produce an offset inside one window.
- **The decomposition closes on every run:** |total − (lever + direction + aero + bias)| ≤ 2.2e-16.
- **Order of magnitude (reviewer arithmetic):** (ω_x² + ω_y²) · r_z · m/F, using the published medians (34.1 °/s, r_z 0.4996 m), gives −0.83 %. The published median lever term is −0.85 %.
- **B1 contrast:** median transverse body rate 3.4 °/s and total offset −0.04 %. This is consistent with a term that scales with the rate squared.

Carried to the RG-16 gate (not established by this ruling):
- **The lever term scales with ω².** The A1 body rates come from the sim's attitude activity under a quasi-steady massless drogue and through the release transient. Canopy dynamics are unmodelled.
- **The compensation uses the true CG.** sim6 l.2421 and l.2552 compute (z_imu − zcg), with zcg taken from the true mass properties, although the comment says "CG model". Reviewer arithmetic: a 5 cm CG-model error changes the lever term by about 0.05/0.50 × 0.85 % ≈ 0.09 %.
- **A residual remains.** After lever and direction compensation, −0.18 % (the aero term) remains in A1.
- **This is a model-internal diagnostic.** The physical check is F_acc against the load cell at T1–T4.

#### 4.2 RG-04 ×0.90 clarification: CONFIRMED

- **The reviewer's case.** rg05 l.94 sets `d["thrust_scale"] = dr["thrust_scale"] * mod["thrust"]`. This applies ×0.90 on top of the per-run N(1, 0.05) draw, so k ≈ N(0.90, 0.045).
- **GNC's case.** GNC's conditional tables hold thrust_scale fixed: each cond_A1_k* table has a single value.
- **Both numbers stand, for different cases:**
  - 0.950: k with mean 0.90 and a 4.5 % spread;
  - 0.980 with 5 exhausted runs: k known to be 0.90.
- **Which case applies.** Under the adopted cap rule, which fixes the corner k_c = k − 2u_k, the fixed-k case is the relevant analogue. Drawing k again around the corner would count u_k twice.
- **Note on resolution.** At 500 runs, A1 P is not monotone in k: 0.986 / 0.988 / 0.996 / 0.980 at k = 1.00 / 0.97 / 0.95 / 0.90. Differences of this size are within the resolution. The informative signal is the exhausted count: 0 / 0 / 0 / 5.

#### 4.3 "The live hub combustion.json lacks igniter.sequence": REFUTED

- **The files are identical and carry the key.** The live hub interfaces/combustion.json and the pin iface_v3c/combustion.json are byte-identical (d9ec54fbf450e243, v2.3).
  - Both carry igniter.sequence with 7 keys: abort_if_no_ignition, arm_preconditions, flashback_and_backflow, purge, relight, shutdown, start.
  - The hub file's mtime is 2026-10-12T22:19:20Z, before the rev1 work.
  - GNC's own v3 rebuild reads two igniter.sequence entries (interface_contradictions_kept).
- **Where the key is missing.** Only in the simulator's local fallback snapshots, which hold combustion v1 (598365dac1bfa0c1):
  - gnc_dev28/data/iface_snapshot;
  - hub 01-systems-gnc/sim/data/iface_snapshot.
- **Possible origin (HYPOTHESIS; GNC's log would settle it).** run6._json silently falls back to that snapshot when the GNC_IFACE file cannot be read, with no version check and no warning. The default GNC_IFACE, /mnt/project-files/engine/interfaces, returns an I/O error in this container.
- **What actually differs between the live hub and the pin is electronics.json:**
  - hub v2, da067408c1594814, written 2026-10-13T09:35:16Z;
  - pin v1, 42fe12e15baa6e3e;
  - mechanical and ENGINE-BASELINE are identical.
- **Executed probe (rv08):**
  - with the live hub set, run6.build fails with KeyError 'dynamics_for_GNC' at run6.py l.368;
  - with the pin, it builds (777 parameters).

  The pin is therefore necessary, but for a different reason from the one stated (N5).
- **The coordinator's non-reproduction is confirmed.** GNC should withdraw the Unknowns row and the RG-12 note, and state the electronics dependency instead.

### 5. LEAD DECISIONS (CHANGELOG lines 160–161) AGAINST THE GNC EVIDENCE

#### 5.1 Interim Pc-invalid rule, line 161 (2): MAJOR, before the SIL/HIL freeze and A1

**Timing is consistent with GNC's evidence.** Releasing 0.10 s after a confirmed light lies inside the band that does not change P (a 100 ms hold gives −4/+4). The firmware declares E2 16–18 ms after the light.

**The defects are in the rule's scope and in the evidence it relies on:**

- **(a) The general sentence contradicts the adopted predicate.** The decision says "The FC never holds the drogue with the engine in RUN beyond E2 + 0.10 s". Under the adopted predicate (line 161 (1)), a valid Pc below 3.0 bar with b7 clear holds the drogue until the Pc branch fires:
  - L400_nto releases at 404–405 ms;
  - bit-check S4 (2.0 bar plateau, with E2 placed at the light as the sim does) releases at 0.407 s in the reviewer's re-run.

  The sentence should be limited to the invalid case. If a general timeout is intended, that is an unflown change to the decided rule (line 142), and it removes the positive evidence of combustion at release.
- **(b) The rule is not written as a predicate term.** The adopted predicate has no branch for the invalid marker. With d2-d3 = 0xFFFF the Pc branch is false, and b7 cannot latch if the invalidity starts before E2 + 0.10 s.
  - Suggested form, for the lead to decide: RELEASE iff RUN AND b4 AND [(Pc valid AND ≥ 300 kPa abs) OR b7 OR (d2-d3 = 0xFFFF AND t ≥ t_E2 + 0.10 s)], with t_E2 taken from EVENT 0x120.
  - This form also defines the late case (Pc goes invalid after E2 + 0.10 s while the FC waits for 3.0 bar): release on the first invalid frame.
  - How b7 behaves on an invalid channel is not specified in the Electronics material I read.
- **(c) RUN is no evidence of combustion in this case.**
  - electronics.json v2 fail_safe_states: "Pc sensor fault = RUN: open-loop feed-forward map on P_feed + fault flag".
  - The FLAMEOUT cause in the abort matrix is defined on Pc: kFlameoutPc_Pa 150 kPa, kFlameoutFrac 0.35, 20 ms.
  - I found no flame-out detection that does not use Pc (MISSING DATA if one exists).
  - So with an invalid Pc channel, the ECU stays in RUN by design and cannot see a flame-out. The interim rule rests on the light at E2 alone.
  - A single sensor fault on a lit engine releases correctly. A sensor fault plus a flame-out inside [E2, E2 + 0.10 s] releases on a dead engine; this is a double fault, or a common-cause fault.
  - The rule is acceptable as INTERIM only if this case is recorded in the FMEA. Amendment (c) should fly exactly this case against the accelerometer-gated comparator.
- **(d) No simulation evidence.** sim6 has no Pc-invalid model in the release logic (rev1_items open item). The rule is an unflown interim design.

#### 5.2 Purge mass in the A1 reserve, line 160 (5): MAJOR, before the re-fly result is used

**Reviewer first-order estimate (rv06).** DERIVED from GNC's paired tables:
- the reserve falls by α × the purged mass, with α 1.011–1.013;
- the unusable residual is about 59.4–59.5 g, read from the exhausted runs.

**Lowest usable reserve under the decided rule:**

| Base | Run | Usable reserve |
|---|---|---|
| A1_none | 14 | 54.7 g |
| A1_none | 108 | 67.5 g |
| A1J_pc | 108 | 64.1 g |
| A1J_pc | 14 | 65.8 g |

- In both bases the next-lowest reserve is at least 103.9 g, so the issue is two tail draws per base.
- In all four cases above, exhaustion is a loss (ok 0).
- **First-order limit for no new exhaustion:** 54.1 g (A1_none) and 63.4 g (A1J_pc).

**Predicted new exhaustions per base (A1_none / A1J_pc):**

| Purge mass | A1_none | A1J_pc |
|---|---|---|
| 50 g | 0 | 0 |
| 60.5 g | 1 | 0 |
| 68.8 g | 2 | 2 |
| 73.0 g | 2 | 2 |
| 76 g | 2 | 2 |
| 78.1 g | 2 | 2 |
| 94.5 g | 2 | 2 |

PS08 (1/0) and PS10 (2/2) agree with this estimate.

**Consequences for the decision:**
- "Line the segment (saves ~0.3 s)" does not remove the exhaustion: 68.8 g still exhausts both draws in both bases.
- The needed flow time alone (1.8–1.9 s) sits at the A1_none limit: 56–59 g if the flow is all liquid, against 54.1 g.
- Only two options close it:
  - trim the A1 apogee to gain about 22 g of reserve on the lowest draw (for 76 g);
  - or explicitly accept 2/500 per base.
- The re-fly decides. This estimate is not a re-fly.
- GNC's statement "a 50 g purge leaves at least 5 g" comes to about 4.2 g with α 1.011 (immaterial).

**Later lines 163–164 change part of this:**
- the lining is dropped, because it costs time (2.2 s lined against 1.9 s unlined);
- the ECU cap is set at 2.5 s of flow plus the measured valve opening and closing times;
- Combustion bounds the N2O at ≤ 73.0 g for 2.5 s of flow.

At 73.0 g the first-order estimate still predicts 2 exhausted draws per base. The +0.60 kg valve-mass sensitivity (line 164 (7)) and any T_fire delay (line 164 (2)) can only lower the reserve; this is a direction, not a computed value.

#### 5.3 Stuck-open bleed handled as a risk at about 31 g/s, line 160 (5): MAJOR for the risk acceptance

- **(a) A1: the inhibit does not cover the residual case.**
  - The hardware inhibit covers the ascent only.
  - The residual A1 case is a failure to close at the lift after the scheduled purge. This is exactly GNC's S313 arms (blf_ph 4: "the relight lift, the bleed fails to close", sim6 l.176).
  - The inhibit cannot prevent it: the drivers are enabled in that window, and a mechanical double-stuck valve does not respond to an inhibit.
  - **Consequence with no FSW response:** 0.896 additive (48 exhausted, 7 crashes) or 0.974 subtractive. Combustion has since stated that the additive case is the physical one (line 163).
  - **The probability is missing** (FMEA).
  - **"BLEED_FAULT goes to the FC" has no flown FC action**, because the leak response is research only. The decision should say that the FC action is log-only until a response is flown and reviewed.
- **(b) B1 and the A1 pad start: make bleed closure a pad go/no-go.**
  - If CF-4 shows that the pad start needs a purge, the whole-flight inhibit no longer holds.
  - B313_0 (stuck from ignition, additive) gives 0.368, with 315 exhausted runs and 114 crashes.
  - On the pad, closure can be confirmed before ignition from P_mid, so it should be a launch-commit go/no-go item.
  - The argument "a leaking relight beats no relight" does not apply on the pad.
- **(c) NOTE: the evidence for rejecting GNC's ≤ 0.8 mm (about 20 g/s) is indirect.**
  - The rejection rests on two results: a single-tap 15.6 g/s path (FD-01 alone) failing the sweep, and F1 at ≤ 18 g/s sitting near the 14.1 g/s floor.
  - Combustion's grid has total flows of 31.25, 40 and 62.5 g/s. A total of about 20 g/s split over both taps is not in it.
  - The decision may be right, but the cited evidence does not test that point. That point is the comparator if the FMEA cannot bound the probability of the additive consequence.
- **(d) Vent geometry.**
  - The 31.3 g/s evidence is for a balanced vent.
  - The lateral-vent case (2.1 N, ASSUMED) was flown only at 20.0 g/s, and left 0.15° of margin to θ ≤ 2°.
  - Reviewer first-order estimate (HYPOTHESIS: jet reaction proportional to flow at a similar exit velocity, about 3.3 N): θ maximum about 2.5°, p50 about 1.8°.
  - Since addressed: line 164 (1) puts "balanced or axial vent" in the design basis.
- **(e) FC_THRUST at 31 g/s.**
  - RG-16 was flown at 0.8 mm.
  - False-alarm side (reviewer DERIVED scaling, rv07): held maximum ≤ 595.4 N, a margin of at least 54.6 N to 650 N.
  - Miss side: the booking residual of about 45 g is unflown, and the non-adopted Llo_cmd variant already misses 1/1000 at 29.1 g.
  - Re-fly before FC_THRUST is armed on A1.

#### 5.4 Supported decisions (NOTE)

- **Line 161 (1), predicate adopted and plateau NOT added to the plan.** Supported by the reviewer's re-flight (C3). The planner change also loses against the same plateau with the planner unchanged: −19/+7, p 0.029.
- **Consistent with the evidence:**
  - line 161 (3), UNKNOWN = UNPRIMED;
  - line 161 (6), launch commit, provisional;
  - line 161 (8), geofence as a backstop;
  - line 161 (9), OI-GNC-V3 is a lookup fix;
  - line 161 (10), igniter claim not reproduced (agrees with §4.3).
- **Line 161 (7), cap rule.**
  - Because the corner is k_c = k − 2u_k, the B1 cap reaches 62 m only if k − 2u_k ≥ about 0.994. This is reviewer arithmetic, interpolating linearly between GNC's 62.5 m at 1.00 and 60.0 m at 0.97.
  - T1–T4 must therefore measure k ≥ about 1.014 (if u_k = 1 %) or 1.034 (if u_k = 2 %) for 62 m to hold. Otherwise the cap falls below 62 m, as the decision anticipates.
- **Line 161 (4), purge gate and ECU cap.** Unflown (amendment a). The cap value was set later (line 164 (2)).
- **Line 161 (5), "PS10 bounds the purge cost".** Valid while the ECU cap stays below the longest modelled purge (3.43 s).

### 6. NEW FINDINGS ON THE REV1 SET

**N1 (MAJOR; gate: RG-01 re-fly). One relight claim rests on several FSW configurations.**
- The release-rule, start-transient and purge-cost arms fly the stored v2.8 FSW (mest_mode 0, kest_comp 0, fct_comp 0).
- m2_purge_bleed flies the flown-estimator FSW without fct_comp.
- Bases with the flown estimator exist only for A1_none (decided base f26b2baad2fa83ce) and B1 (B1_62m_W1p c33bc6248e2c80ec). A1J_pc has only the stored base.
- Pairing inside each study is valid. Combining the studies into one relight statement is not shown.
- **Required:** one declared flight FSW for every base and arm of the RG-01 re-fly, or paired evidence that the differences are immaterial.

**N2 (MINOR). Wrong t_ign_est label in start_transient.json.**
- The file reports t_ign_est_s 0.81 for L400_te, but that arm flew 1.11 s (FSW record as-flown table).
- Cause: m2_start_transient l.83 builds the arm with _te, while the evaluation at l.165 does not.
- The P values are unaffected.

**N3 (MINOR). Incomplete bit-check claim.**
- "Bit-check v1.5 ALL PASSED" covers parts A, C–F, P, R and S. Part B is empty. Parts G, H, W and X were last run at v1.3, on the pre-R code.
- The claim should state which parts were run. The reviewer's re-run (C2) closes the gap for this code.

**N4 (MINOR, reproducibility). The rev1 set cannot be re-run from the hub alone.**
- The manifest pins the simulator code but not its inputs: the interface pin, actuator_rate_check_v2.json and sim data/ (6 tables, equal today to hub 01-systems-gnc/sim/data).
- Some inputs are read from other specialists' work areas:
  - Combustion purge_table_v2p4, 79880ab51139ff99;
  - Combustion burn_limit_proxy_v2p4, bc95a09b083e45ae;
  - Mechanical coil_o3b_v34_v1, 1c45d4ed2485d25e.
- run6 falls back silently to the v1 snapshot when GNC_IFACE cannot be read.
- **Required:**
  - fail on fallback, or assert the source label and version;
  - pin these inputs, or hub copies of them, in the v3.1 manifest.

**N5 (MINOR, part of RG-12). The TVC loop parameters have no current source.**
- run6.build reads the electronics.json fields actuators.tvc_A.dynamics_for_GNC, engine_side_at_n7_7V4 and hinge_moment_assumed_Nm (run6 l.367–369, l.545–550, l.633–637).
- electronics v2 removed these fields as "superseded by mechanical.json v2, gnc.json v3 and the TVC calcs".
- The actuator small-signal parameters therefore have no current owner value. In every rev1 MC they are ω_n 94.2 rad/s (ASSUMED, with its MC range), ζ 0.7 and a transport delay of 4.5 ms. For RV-1c, deadband and backlash come from mechanical.json.
- **Required:** Electronics or B-TVC-1 supplies the parameters or confirms the v1 values.

**N6 (NOTE). ENG-07 coil coupling is not modelled.**
- The coupled coil stiffness is flown as a per-axis spring at the largest eigenvalue (sim6 l.1988, l.2144–2146). The off-diagonal term, 32.728 × EI, is not modelled.
- Reviewer arithmetic: at an equal-sign diagonal deflection, the per-actuator torque is (64.459 + 32.728)/93.476 = 1.040 times the flown value. EI 0.25 then acts like about 0.26 on one axis.
- This does not move the (0.25, 0.5] bracket at its resolution, and it supports the lead's preference for K_max ≤ 17.2 N·m/rad.

**N7 (NOTE). PS10_L400 is within 1 % only when pooled.**
- Pooled: 0.979 against 0.987, within 1 %.
- A1J_pc alone: 0.970 against 0.984 (−9/+2, p 0.065), not within 1 %.

### 7. MODEL AND EVIDENCE LIMITS

- **Quasi-steady massless drogue.** Canopy motion is unmodelled; this governs θ and the A1 body rates (RG-16 lever term).
- **Stuck-open bleed physics.** The FSW does not model the leak.
- **Regression law.** The truth law is a DERIVED proxy, ASSUMED until T1–T4.
- **k and u_k.** Unknown until T1–T4.
- **TVC dynamics source.** None current (N5).
- **Pc-invalid behaviour in the release logic.** Not modelled.
- **Resolution.** At 500 runs, differences of 1–2 % in P are near the resolution limit. "Not significant" means not resolved, not "no effect".

### 8. QUÉ SIGUE SIN DEMOSTRARSE (what remains undemonstrated)

- **All physical behaviour:**
  - relight on the re-routed coil;
  - the purge sweep and CF-4;
  - light, spike and roughness;
  - canopy motion;
  - stuck-open bleed physics;
  - the web law;
  - k and u_k;
  - latencies;
  - TVC dynamics.
- **Relight P on the current design basis.** The RG-01 re-fly has not been done.
- **ECU behaviour with Pc invalid inside [E2, release],** and b7 on an invalid channel.
- **The probability of a stuck-open double or common-cause fault.**
- **The FC_THRUST miss side** at the decided purge flow.
- **Reproducibility of the rev1 set from the hub alone** (N4).
- **The interim Pc-invalid rule and the purge gate** (both unflown).

### 9. PRÓXIMO CIERRE (next closure, in order)

1. **GNC, text and records (small):**
   - withdraw the igniter Unknowns row and the RG-12 drift note, and state the electronics dependency instead (N5);
   - correct §2.8 (W1p_tot);
   - correct the §2.10 bounds;
   - list the parts run in the bit-check claim;
   - fix the start_transient label.
2. **GNC, in the RG-01 re-fly now under way:**
   - one declared flight FSW (N1);
   - pin the inputs and fail on fallback (N4);
   - fly the purge at the ECU cap (2.5 s of flow plus valve times; ≤ 73.0 g per Combustion) and report the A1 reserve tail explicitly;
   - RG-16 terms at the decided path, on both sides;
   - the +0.60 kg valve-mass sensitivity.
3. **GNC amendments**, each with its own API, hypotheses, tests and independent review:
   - (a) the purge gate and cap;
   - (b) the freeze on Pc invalid, then a re-fly of the Pc-lost arms (RG-15, RG-18);
   - (c) Pc invalid inside [E2, release], including a flame-out with an invalid channel, against hold-and-abort and the accelerometer-gated comparator;
   - the flag in the loop with a late flip (RG-08).
4. **Lead:**
   - restate the interim rule as a predicate term limited to the invalid case (§5.1);
   - FMEA entries for release on a dead engine under Pc invalid, and for the stuck-open bleed;
   - define the FC action on BLEED_FAULT;
   - a pad go/no-go on bleed closure if CF-4 requires a pad purge;
   - decide on the two A1 tail draws (apogee trim or acceptance);
   - adopt the RG-16 budget form;
   - extend the pre-flight grain gate if the total-flux law applies (RG-03).
5. **Electronics:**
   - RUN-exit and b7 behaviour with Pc invalid;
   - a source for the TVC loop parameters;
   - the OI-GNC-V3 lookup fix;
   - the filtered-only hold.
6. **Combustion:**
   - hub copies of the line 163 tables;
   - the basis for measuring a at T1–T4;
   - the vented-mass table on the final path, for the RG-16 booking residual;
   - optionally, the two-tap ~20 g/s point as the comparator for §5.3 (c).
7. **SIL/HIL and tests:**
   - HIL-TR-1;
   - the RG-19 latency budget;
   - T1–T4: k, u_k, (a, n), g, and F_acc against the load cell;
   - B-FD-1;
   - B-PNT-1;
   - CF-4 (run by the founders).
8. **Supervision:** registering this verdict in supervision.json is outside the reviewer's write scope and is left to the lead.
