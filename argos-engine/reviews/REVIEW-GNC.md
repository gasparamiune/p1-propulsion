
REVIEW-GNC-1. Independent review of Space Systems / GNC: 01-systems-gnc v3 and interfaces/gnc.json v3, with an addendum on the v3.1 staging set (FC_THRUST).
Reviewer: the independent GNC reviewer, who did not author the work. Date: 2026-10-13.

Everything below is simulation, analysis or arithmetic. Nothing here is physical acceptance. A reproduced number shows that the computation can be repeated. It does not show that the physics is right.

## 1. SCOPE AND FILES

Reviewed files (hub /home/claude/work/shared-fallback/engine/, sha256/16):

| File | Version | sha256/16 |
|---|---|---|
| interfaces/gnc.json | v3 | 3e97c378cfebee95 |
| 01-systems-gnc/REPORT-v3.md | v3 checkpoint | 2d79920b8cc1537d |
| 01-systems-gnc/sim/gncsim/sim6.py | v2.7.1-dev | f314dae1a0d6aaa1 |
| 01-systems-gnc/sim/gncsim/run6.py | v2.7.1-dev | 8ba04021394c3d36 |
| results/relight_v28/relight_v28.json | | 01e0ceb15b73797a |
| results/regband/regband_mc.json | | d422c97e0aff3a70 |
| duty_cycles/duty_cycles_index_v3.json | rev d | 4a07d68946bd0dc9 |
| staging_v3.1/gnc_v3.1_staging.json | v3.1-staging | 695a069e8fc8dc53 |
| staging_v3.1/REPORT-v3.1-staging.md | | 2e167607d7fbde5f |
| staging_v3.1/MANIFEST_staging_v3.1.sha256 | | ab2f07016b45cdfa |
| staging_v3.1/results/fc_thrust/fc_thrust.json | | 0726d6197d341cbd |
| staging_v3.1/results/fc_thrust/fc_thrust_mest.json | | 37a82ed93a25ebfa |

**Context, read only:**
- 00-requirements/REQUIREMENTS.md, rev 2 plus amendments. First read at 17228d276eadd5f4; re-read at 89cbf24e346e67a4 after the 04:26Z ENG-05 amendment. Line numbers below refer to the current file.
- TEAM-CHARTER.md 9b5e35a774ac4b3e.
- interfaces/CHANGELOG.md. First read at 8406e37d982140ba (104 lines); re-read at 7cd18c1425efd087 (109 lines).
  - Lines 100–109 post-date the GNC v3 publication. They are used here as new evidence.
  - Findings that rest on them are not author errors, but they change what can be accepted.
- combustion.json v2.3 d9ec54fbf450e243; mechanical.json v2 4f024ed4ccb4618c; electronics.json v1 42fe12e15baa6e3e.
- reviews/REVIEW-COMBUSTION.md 54ceaa46e9e17594 (format model).
- The Combustion RC-03 file relight_latency_sup_v2p4.json f0ea1eb9905919ce. This is the file the author used; it is not in the hub.
- The GNC work area (fc_thrust_runs_{A1,B1}.npy), read only.

**Not reviewed:**
- the firmware (engine_ecu.cpp);
- the Combustion and Mechanical models behind their inputs;
- the CSI/flex analysis;
- the evidence for ENG-07b and ENG-11.

**Reviewer files** (reviews/gnc/, sha256/16 of .py / .json):
- rg01_stats c090fff1237e6174 / b53eb6a27580bc0d: P, Wilson, McNemar and q* from the published tables; RC-03 abort fold-in.
- rg02_mc_repro 3bc4595d9c1befd2 / 11972fe1fce818da: re-fly on a byte-identical copy.
- rg03_vertical 62d4a1fa79e28ff7 (v1.1) / d4a15adff8f52c62 (produced by v1): independent 1-DOF model. v1.1 only adds k_thr and reproduces v1 at k_thr = 1 on three flights (rg08 check_k1).
- rg04_b1_bound 6b6d452ce943e4f2 / 03ced62b0e1dfbff: 62 m band population vs the 85 m sizing populations.
- rg05_sens 5b32dd88d044e3c3 / 3e10e51644563264: paired sensitivity MCs.
- rg06_compare_nominal fe3388f33583d6a2 / c6396b6264a274a5.
- rg07_touchdown 5f93b9e49567808e / 215fd5f6ce472e2b.
- rg08_isp 493b1ee4c452c366 / 97a870d7d186a53a.
- rg09_gust b262542d8eed8019 / 819dedb0c34f6ceb.
- rg10_settling 1f1f4e6d1a67d88a / 50997a744592be82.
- rg11_cap_isp e7a0fbbfec3f3661 / 40f134e54f7c3699.
- rg12_jref 4e9c98a0f38591a6 / 565a33afd01bbf6c.
- rg13_predictor_leak f1d82e88f75bd8c2 / ad4ced5b28a6aebb.
- rg14_corner_mc 4ecd8fd4e8c1bdd2 / 30d3c3e570a0d793.
- rg15_fct_review 7bcaf82016fa35ff / 66b28b9e439fb389.
- rg16_mest_stuck 7f560ef56cc7002c (v1.1) / 932f9feff6ba9379.

## 2. METHOD

**Reproduction (rg02).**
- The sim and scripts (86 files) were copied to the scratchpad and checked for byte identity; the interface set was checked identical to the hub.
- Re-flew the first 100 / 60 / 100 runs of v28_liq_p0.81_A1_none_k2, v28_fault_p1.41_A1_none_k2 and rbl_B1_lead62_pc_k2. All 134 fields of all 260 rows are bit-identical.
- rg05, rg13 and rg14 re-flew complete 500-run base cases (500/500 'ok' identical) before applying their single change.

**Statistics (rg01).** Recomputed from the published run tables with own code: exact integer McNemar, Wilson z = 1.96, and a bootstrap with both the author's seed and an independent one.

**Independent model (rg03).**
- A 1-DOF vertical model written by the reviewer from the interface files, using the author's +25 % rule: usable = liquid − 0.03 × 2.00 kg; reserve = usable / N2O burned.
- It is a consistency check only. It is not claimed to be more accurate, and more degrees of freedom are not taken as proof of accuracy.

**Sensitivities (rg05, rg09, rg11, rg13, rg14).**
- The author's code is unchanged except for the one named change. Same draws (seed 101), paired with exact McNemar against the published table.
- At 500 runs, differences of 1–2 % in P are near the resolution limit. "Not significant" means not resolved; it does not mean "no effect".

**v3.1 addendum (rg15, rg16).** A re-implementation of the v1.1 synthetic stuck-ramp loop: same generator 20261020, same loop order. It reproduces every published count exactly (R16) before the reviewer questions are asked of it.

**Constraints.** CPU ≤ 2 processes. Nothing outside reviews/gnc/ was written.

**Severity scale:**
- BLOCKING: a published value that a gate depends on is invalid or unsupported on current evidence.
- MAJOR: a claim is overstated or a material dependency is missing; it must close before the named gate.
- MINOR: a text, traceability or method correction with limited effect on gate decisions.
- NOTE: an observation or confirmation.

## 3. RECOMPUTATION TABLE (reviewer vs author)

| # | Quantity | Author | Reviewer | Result |
|---|---|---|---|---|
| R1 | C1 P by line state (12 cells), Wilson | REPORT l.9–14 | rg01 from run tables | identical |
| R2 | C2 option (c) paired | l.20–27: 0/361, 0/316, 0/360, 0/319; p ≤ 1.9e-95 | rg01 | identical |
| R3 | C2 fault spread | l.30–33 | rg01 | identical |
| R4 | C3 q* | l.45: 0.022–0.111; CI 0.003–0.146 | rg01: 0.0217–0.1114; CI 0.0029–0.1456; independent seed (n 4000) within 0.003 | identical. On the fault-SPREAD basis q* = 0.055–0.85 (reviewer addition) |
| R5 | MC rows | run tables | rg02: 260 rows × 134 fields | bit-identical |
| R6 | Start-delay tables | l.86 | rg01: liq max 0.499 (p95 0.437); vapU 0.801 (0.666); vapF 0.809 (0.747) | identical |
| R7 | vapF P | l.11–14: 0.990–0.994 | rg01, with the RC-03 abort at W 0.65 s folded in (no retry): vapF 0.949–0.953; vapU −0.001; liq 0 | DIFFERS: published P is conditional on light |
| R8 | A1 nominal | 6-DOF: N2O 1.1869 kg, reserve 38.5 %, MECO 3.159 s / 99.6 m / 64.0 m/s | rg03/rg06: 1.1897 kg, 38.1 %, 3.095 s / 94.4 m / 62.3 m/s, apex 300.1 m | agree; N2O per impulse within 0.3 % |
| R9 | B1 62 m nominal | 44.4 %, apex 63.57 m | 45.5 %, apex 60.6 m | agree |
| R10 | B1 85 m nominal reserve | 26.34 % | 24.73 %; post-MECO impulse 2614 vs 2578 N s (+1.4 %) | DIFFERS on the rule outcome (< 25 % in the reviewer model) |
| R11 | Corner cap | l.62: 62.9 m, 25.8 % at 62 m | rg11 at thrust_scale 1.00: 62.92 m, 25.8 % | identical |
| R12 | B1 62 m MC | l.63–65: P 0.996 [0.986, 0.999]; 0 exhausted; usable p01 0.188 kg; counter 15.81 / 18.25 / 20.16 s | rg05, rg04 | identical |
| R13 | "85 m cycles cover 62 m" | l.65 | rg04: holds for engine-on time, N2O burned (1 run above the 85 m p99) and J. Fails for fuel burned (max 0.344 vs 0.298 / 0.306 kg) and mean O/F (max 11.63 vs 6.56 / 6.42) | DIFFERS |
| R14 | Coast and drogue axial acceleration | staging l.136–142. Author nominal: hold MECO→RELIGHT 19.80 s; f_z mean MECO→apogee −0.36 m/s²; apogee→command 13.36 s at 8.19 m/s² | rg10: 19.66 s; −0.35; 13.15 s at 8.18; f_z ≥ 4.9 m/s² continuously 11.6 s before light (author record 11.8 s) | agree |
| R15 | FC_THRUST Pc lost | staging l.57: 0/1000, upper 95 % 0.30 % | rg15: held max 634.5 / 635.6 N; A1–B1 correlation 0.980; n_eff ≈ 505; bound 0.59 % | DIFFERS on the bound |
| R16 | Stuck 670 N misses at 650 N | l.74 and l.100: 252/4000 at 3 %, 0 at 1 %, 43 at 2 % | rg15/rg16: 252, 0 and 43 reproduced; lowest post-onset held maximum 627.5 / 660.1 / 643.8 N reproduced. Misses come from 40 (3 %) and 7 (2 %) distinct error sets out of 500 | counts identical; DIFFERS on the effective sample (l.77) |
| R17 | F_acc_c correction | l.95 | algebra and code reading | exact (RG-20) |

## 4. FINDINGS

| ID | Severity | Title | Gates |
|---|---|---|---|
| RG-01 | BLOCKING | Relight evidence rests on the superseded 21.4 cm³ segment; the current flight state has no evaluated case | SIL/HIL freeze of relight logic; A1 |
| RG-02 | MAJOR | No-light accounting is stale and omits a quantified no-light source | A1 |
| RG-03 | MAJOR | "85 m covers 62 m" fails for fuel, web and O/F; the burn limit is not implemented | B1; grain and insert sizing |
| RG-04 | MAJOR | Cap and A1 margin depend on engine properties that are fixed per engine but drawn per run | T1–T4 review → B1, A1 |
| RG-05 | MAJOR | ENG-03 ramp ≥ 2 F_max/s is not supported by the 6-DOF (MC flies 5) | B-PNT-1 acceptance; SIL; B1 |
| RG-06 | MAJOR | Launch commit lacks a turbulence criterion | B1, A1 |
| RG-07 | MINOR | B1 62 m evaluated only on the reference actuator basis | B1 (after B-TVC-1) |
| RG-08 | MINOR | Stale-flag rule stands, but its rationale uses the wrong window and the flag is blind to vapour | SIL/HIL; A1 |
| RG-09 | MINOR | "B1 governs thermal and erosion" is not true per quantity | thermal sizing before T1 |
| RG-10 | MINOR | B apex predictor uses the true thrust; the cap is a target, not an apex bound | SIL port; B1 safety area |
| RG-11 | MINOR | Model-form biases: growth cap, MECO quantisation, mass-error form | post-T1–T4 cap re-derivation |
| RG-12 | MINOR | Traceability and compliance records stale or inconsistent | interface freeze for SIL/HIL |
| RG-13 | MINOR | FSW exists only in the sim; ratchet switched by an environment default | SIL/HIL |
| RG-14 | NOTE | Touchdown tip-over margin depends on pad slope | B1, A1 landing area |
| RG-15 | NOTE | Confirmations (k_est_asc 2, reproduction, consistency) | — |
| RG-16 | MAJOR | ≤ 1 % mass-estimate requirement derived without systematic terms (v3.1) | SIL/HIL; first flight with FC_THRUST armed |
| RG-17 | MINOR | v3.1 confidence bounds overstated about ×2; normal tails restate the assumption | v3.1 publication |
| RG-18 | MINOR | Synthetic stuck ramps test the measurement chain, not the system; valid window undefined | HIL; safety case |
| RG-19 | MINOR | Unmodelled latencies and exposure after detection | HIL |
| RG-20 | NOTE | v3.1 confirmations; builder reproducibility defect | v3.1 publication |

### RG-01 (BLOCKING). Relight evidence rests on the superseded segment.

**Gates:** SIL/HIL freeze of the relight logic; A1. Not B1, B2, C or D: none of them has an in-flight relight.

**Evidence.**
- **The basis is the old segment.** C1–C3, option (c) and the fault spread were flown with the RC-03 E0→E2 tables and a fixed 1.37 s fault point, both derived on the 21.4 cm³ segment (REPORT l.85–88, l.97; gnc.json l.36). The author flagged this dependency (REPORT l.145–148; CHANGELOG l.98).
- **The segment is now ~44 cm³** (CHANGELOG l.95; REQUIREMENTS l.109). Combustion v2.4 (CHANGELOG l.101 (5)) reports:
  - purge time 0.64–0.69 s;
  - a fully vapour-filled segment aborts at W 0.65 s; lighting it would need W 1.05 s, which Combustion does not recommend;
  - flight W 0.65 s holds only if retained vapour is ≤ ~19 cm³;
  - a vapour-full segment at saturation reads PRIMED, so option (c) does not cover it;
  - after any abort, the next attempt is a vapour start.
- **The flag cannot see vapour.** The Electronics PRIMED test is P_feed ≥ 0.5 P_tank (CHANGELOG l.84 (2)), a pressure test that cannot separate saturated vapour from liquid.
- **Retained vapour is not met** (Mechanical RELAY-2, CHANGELOG l.106 (5)):
  - A1 coast 18.67 s against a budget of 19 cm³ = 489 J;
  - lower bound 875 J = 34 cm³ (the head end alone is 22.8 cm³); upper bound 5.0 kJ, at which the whole segment vaporises;
  - the cause is stored-heat soak-back, so insulation does not fix it.
- **The lead's response** (CHANGELOG l.107): Combustion assesses buoyant migration; GNC computes the P of planning every relight as a vapour start (0.16 + 1.05 s); candidate fixes (a) and (d) are held.
- **The fault path no longer fits 1.41 s.** Reviewer arithmetic, on the HYPOTHESIS that the unprimed prep must cover the purge: 0.81 + 0.64–0.69 = 1.45–1.50 s, which exceeds the 1.41 s plan.
  - The 0.56 s prep is 1.37 − 0.81 on the old segment (REPORT l.88); Electronics' PREPRESS of 0.50–0.56 s (l.84) was sized for that segment.
  - The 0.04 s margin (REPORT l.148) disappears.
- **Option (c) does not cover the expected state.** The gain 0.270 → 0.992 (C2) applies only when the line is known to be UNPRIMED. If the line holds vapour while reading PRIMED, the plan is 0.81 s and the start aborts at W 0.65 s. With no retry (gnc.json l.34) that is a mission loss.
- **The plan has no margin for a late light.** Reviewer 1-DOF (rg03): a 1.37 s light with the 0.81 s plan touches down at 1.60 m/s nominally, against the 2 m/s criterion. This is consistent with the 6-DOF P of 0.270 under dispersion.

**Required action:**
1. Publish the 44 cm³ fault-path time and re-fly C2 and C3 on it.
2. Compute the P of option (b), as the lead requested, paired against the liquid plan. Include the early-light cost when the line is in fact liquid; the 1.41 s rule on a primed line already costs 0.056–0.080 (REPORT l.39).
3. Fly a partially vapour-filled case at Combustion's governing vapour volume, with the abort-at-W probability folded in.
4. Electronics: either a PRIMED test that detects vapour at saturation, or a statement that it cannot. The known candidates are the withdrawn Tsat − 5 K criterion (gnc.json l.26) and the research level element (CHANGELOG l.82–83). If it cannot, the flag must not be used for planning.
5. Do not freeze 0.81 s or 1.41 s as flight values in SIL/HIL until items 1–4 close.

### RG-02 (MAJOR). No-light accounting is stale.

**Gate:** A1.

**Evidence.**
- **The table is on the wrong rows.** gnc.json l.19000 builds the no_light_accounting table on rl181 rows (the v2.7, 1.81 s plan; P_6DOF 0.982–0.990), not on the adopted v2.8 rows.
- **p_nl has no source.** The values 0.005–0.05 are placeholders (gnc.json l.38, l.5446).
- **RC-03 already gives a no-light probability at W 0.65 s:** vapF 4.12 %, vapU 0.07 %, liquid 0 (rg01; E1→E2 max 0.667 s).
  - The published vapF P of 0.990–0.994 is conditional on light. Folded in without retry, it is 0.949–0.953 (R7).
  - The product form P_6DOF (1 − p_nl) assumes p_nl does not depend on line state, which RC-03 contradicts.

**Required action:**
- Rebuild the accounting per line state on the v2.8 rows, and later on the 44 cm³ rows: P_total = Σ π_s · P_6DOF|s,lit · (1 − p_abort,s) · (1 − p_nl,ign).
- Count the attempts toward the 3/N rule only if they represent the flight segment state (gnc.json l.19000 demonstration_rule already says so).

### RG-03 (MAJOR). "85 m covers 62 m" fails for fuel-side quantities, and the burn limit is not implemented.

**Gates:** B1 first free flight; Combustion and Mechanical grain and insert sizing.

**Evidence.**
- **The claim and the check.** REPORT l.65, gnc.json l.31 and REQUIREMENTS l.102 keep the 85 m cycles as the conservative sizing cases on the basis of engine-on time. rg04 compares the 62 m band population (rbl_B1_lead62_pc_k2) with the two 85 m sizing populations:
  - **Fuel burned:** p99 / max 0.343 / 0.344 kg against 0.272 / 0.298 and 0.278 / 0.306 kg. 82 / 72 runs exceed the 85 m p99 and 43 / 37 exceed its max.
  - **Mean O/F:** max 11.63 against 6.56 / 6.42. 188 / 198 runs exceed the 85 m p99 and 171 / 179 its max.
  - Engine-on time, N2O burned and J are covered.
- **Web.** Reviewer arithmetic, assuming uniform regression of a straight 25 mm port in a 53.5 mm OD × 230 mm grain of 0.404 kg:
  - 0.344 kg burned leaves a mean web of 1.6 mm; the 85 m maximum (0.306 kg) leaves 2.7 mm.
  - ENG-06 (REQUIREMENTS l.54) requires a web of at least 1 mm over the whole band.
  - Combustion v2.4 (CHANGELOG l.101 (10)) finds that the a ×1.5 / n 0.35 corner burns through locally at 17.0–17.8 s even at 62 m. In the 62 m MC, the a 1.2–1.5 runs burn for p99 / max 17.81 / 18.01 s (rg04).
- **The burn limit has no counterpart in GNC.** The lead's rule (burn limit at t(web = 1 mm) using 1.1 × measured a; CHANGELOG l.102) is in neither gnc.json v3 nor sim6.
  - sim6 has no web state: reg_X is cumulative oxidiser mass (l.1446–1448).
  - The FSW action at the limit is undefined, and in a continuous-burn hop the limit can arrive during the landing burn.
  - P 0.996 therefore counts runs whose web state is unknown.
- **O/F.** O/F of 8–11.6 in the a 0.6–0.9 tercile (p50 8.0) is oxidiser-rich operation not represented in the 85 m cycles. HYPOTHESIS for Combustion: oxidising attack on the throat and walls. The J metric (sim6 l.688) does not depend on O/F.
- **The staged 62 m records cannot test the band corners.** They come from the growth-only populations tgl_B1_lead62_{none,pc}_k2, without the regression band, and are selected by engine-on counter (staging l.145–155; records file sources).

**Required action:**
1. Withdraw "covers" for fuel, web and O/F; keep it for time, N2O and J.
2. Publish band records selected by fuel burned and by O/F, plus the high-a runs with the longest burns.
3. Implement the burn limit in the FSW and in sim6, define the action at the limit, and fly the 62 m band with it.
4. Re-derive the cap after T1–T4 (RG-04).

### RG-04 (MAJOR). The cap and the A1 margin depend on engine properties that are fixed per engine but drawn per run.

**Gates:** T1–T4 data review, then B1 and A1.

**Evidence.**
- **What the MC averages over.** Delivered thrust per propellant flow (run6 thrust_scale, which scales thrust at the same flow, sim6 l.1385 and l.1443–1444) and the regression law are fixed properties of a built engine. The MC draws them per run (N(1, 0.05); (a, n) uniform), so P 0.996 is an average over engines. The cap itself was set on the nominal flight at thrust_scale 1.0 (REPORT l.62).
- **Cap sensitivity (rg11, author's code and cap search).**
  - At thrust_scale 1.00 / 0.97 / 0.95 / 0.90 the corner cap is 62.92 / 59.65 / 56.43 / 50.79 m.
  - The reserve at 62 m is 25.8 / 22.9 / 20.6 / 14.4 %.
  - A 3 % shortfall, 0.6σ of the MC's own dispersion, moves the cap below 62 m.
- **Corner-conditional MC (rg14, same draws).**
  - Corner (a 0.6, n 0.68, growth 0.11): P 0.990 [0.977, 0.996], 3 runs exhausted, usable p01 0.078 kg.
  - Corner plus ×0.97: P 0.988, 5 exhausted, usable p01 0.027 kg.
  - The band average has 0 exhausted and usable p01 0.188 kg. Only 17 of the 500 published runs have a < 0.8 and n > 0.6.
- **A1 sensitivity.**
  - Thrust ×0.90 on every run: A1 0.950 (−24/+3, p 4.9e-5) and A1J 0.946, each with 21 exhausted (rg05).
  - Reviewer 1-DOF (rg08): A1 meets the +25 % rule down to k_thr 0.922 and B1 62 m down to 0.859. B1 85 m is already at 24.73 % at 1.00.
- **B1 62 m at ×0.90:** P 0.986 (p 0.125), 2 exhausted, usable p01 0.031 kg.

**Required action:**
1. T1–T4 report delivered thrust per flow (with uncertainty) and the regression law.
2. Recompute the cap on the measured engine, with a conditional MC as in rg14; carry the residual uncertainty as a bounded epistemic range, not as a per-run draw.
3. Report A1's reserve and P at the measured efficiency.
4. Write the cap rule in terms of measured quantities so that it can be re-applied per engine.

### RG-05 (MAJOR). ENG-03's ramp minimum is not supported by the 6-DOF.

**Gates:** B-PNT-1 acceptance value; SIL; B1.

**Evidence.**
- **Where the requirement comes from.** ENG-03 (REQUIREMENTS l.51) sets ramp ≥ 2 F_max/s, taken from a 1-DOF sweep. gnc.json l.1419–1423 records "SIM mc1d v1p2 slew sweep (6-DOF runs at 5 F_max/s)", note "target 5 F_max/s".
- **What the 6-DOF flies.** Every 6-DOF result flies 5 F_max/s (run6 l.220; sim6 l.1389).
- **What happens at 2 F_max/s** (rg05):
  - A1: 0.992 → 0.978 (−8/+1, p 0.039).
  - A1J: 0.988 → 0.966 (−13/+2, p 0.0074).
  - B1 62 m: 0.996 → 0.982 (p 0.065).
  - B1 on the ENG-07d basis: 0.976 (−11/+1 against the published table, p 0.0063).

**Required action:**
- Either raise ENG-03 to the value flown (5 F_max/s = 2500 N/s), or publish the 6-DOF P at 2 F_max/s and have the lead accept that loss explicitly.
- B-PNT-1 must measure the slew under load.

### RG-06 (MAJOR). Launch commit has no turbulence criterion.

**Gates:** B1, A1.

**Evidence.**
- **How the model links turbulence to wind.** run6 ties the Dryden intensity to the mean wind: σ_w = 0.1 W20 × U(0.5, 1.5) (l.602, l.846), with wind U(0, 8) m/s.
- **Gust ×2** (rg09):
  - B1: < 6 m/s 1.000 → 1.000 (364 runs); ≥ 6 m/s 0.985 → 0.860 (136 runs, −18/+1, p 7.6e-5).
  - A1: < 6 m/s 0.997 → 0.992; ≥ 6 m/s 0.978 → 0.846 (p 7.6e-6).
- **Intensity factor at the top of its range (1.5):** B1 ≥ 6 m/s 0.934 (p 0.039); A1 0.949 (p 0.22).
- **What this means for the proposal.** The GNC proposal of ≤ 6 m/s mean wind (gnc.json l.5091, l.19845) is supported in this model. But a mean-wind limit bounds turbulence only because the model makes intensity proportional to the mean wind; on a real site, gustiness is not.

**Required action:**
- Add a gust or σ_w criterion to the launch-commit rule, with the sensor and averaging defined.
- Obtain ACEMA site data, or state the assumption used.
- Run a 6-DOF check at the proposed limit.

### RG-07 (MINOR). B1 62 m is evaluated only on the reference actuator basis.

**Gate:** B1, after B-TVC-1.

**Evidence.**
- A1 is published on both actuator bases (REPORT l.13–14); B1 62 m only on the reference basis.
- Reviewer, on the ENG-07d basis (rg05 mc2): 0.992 (−3/+1, p 0.625).
  - Plus slew 2 F_max/s: 0.976 (p 0.0063).
  - Plus gust ×2: 0.964 (p 1.4e-4).

**Required action:** publish B1 62 m on the ENG-07d basis.

### RG-08 (MINOR). Stale-flag rule: acceptable, but the stated rationale compares the wrong window.

**Gates:** SIL/HIL; A1.

**Evidence.**
- **The rule is supported.** On the fault-spread basis, q* is 0.055–0.85 (rg01), above the fixed-point 0.022–0.111. Maximin pays only if the probability of an unreported emptying is large. This supports the rule (REPORT l.47–59; gnc.json l.1485–1488).
- **The rationale uses the wrong window.**
  - The lead's reason is "drain ≥ 6 min >> 0.3 s staleness" (CHANGELOG l.104).
  - Under the rule, a flag can be held from MECO to T_fire: 19.80 s (author) or 19.66 s (rg10).
  - The right comparison is 6.1–7.4 min (l.103) against 19.8 s, a factor ≥ 18, so the conclusion stands.
- **Cases the flag does not cover.**
  - A stuck-open pintle (≥ 1 g/s) drains the 30–34 g in ≤ ~34 s, comparable to the hold.
  - Soak-back vapour reads PRIMED (RG-01).
- **What is not specified or simulated.**
  - The flag specification is not in electronics.json (REPORT l.144; gnc.json l.5110).
  - The latch and "fire at once" behaviour (REPORT l.50) is not simulated (l.76, l.151).

**Required action:**
- Restate the rationale against the hold window.
- The ECU publishes UNPRIMED or UNKNOWN on any pintle-position anomaly during the coast (EL-05 encoder) and when P_feed is invalid.
- Electronics publishes the flag specification.
- Simulate the flag in the loop, including a late flip to UNPRIMED.

### RG-09 (MINOR). "B1 governs thermal and erosion" does not hold for every quantity.

**Gate:** thermal sizing before T1.

**Evidence.**
- The claim appears in gnc.json l.23 and REPORT l.72.
- **A1 governs the TC-03 exit-lip peak:** 819.5 °C for A1 against 710.7 °C for B1 (CHANGELOG l.106 (3)).
- The A1 early-light records exceed the A1 sizing counter: 8.53 and 8.35 s against 8.26 s (REPORT l.69–72).
- B1 does govern the integrated loads; the seal sees 224.7 °C, with 2.65 s above 200 °C.

**Required action:** state governance per quantity, and use the A1 p99 early-light cycles for peak-temperature checks.

### RG-10 (MINOR). The B apex predictor uses the true delivered thrust.

**Gates:** SIL firmware port; B1 safety area.

**Evidence.**
- **The two predictors differ.** sim6 l.885–889 uses the true F in the ramp-down term. The A-profile predictor uses the Pc-based F/tsc (l.856, l.871), which is what the flight computer can know.
- **B1 cuts off before the estimator runs.** B1's 62 m cut-off comes at 0.88–0.90 s (rg05 scan), before the estimator gate t > 1 s (l.1882–1884). So the simulated predictor knows something the real FSW cannot.
- **Effect** (rg13: the three lines changed to F/tsc in a scratch copy):
  - P 0.996 → 0.994 (−2/+1, p 1).
  - Apex p99 66.10 → 68.99 m; max 67.48 → 69.96 m.
  - Per-run shift: mean +0.44 m, sd 1.29 m, range −2.31 to +6.85 m.

**Required action:**
- Correct the sim, or document the idealisation and re-run.
- Have the firmware predictor use the Pc-based thrust.
- Size the B1 safety area and any geofence on the apex distribution (about 70 m), not on the 62 m target.

### RG-11 (MINOR). Model-form items with an optimistic or unquantified bias.

**Gate:** post-T1–T4 cap re-derivation.

**Evidence.**
- **(a) Throat growth is frozen above J_ref.** Growth is held once J > J_ref (sim6 l.688). 27 % of the 62 m runs and 38 % of the 85 m runs exceed J_ref (J/J_ref max 1.19 / 1.23). A J-proportional law would give 12.1–12.4 % growth (rg12), and these are the long burns closest to exhaustion.
- **(b) The cap search assumes monotonic reserve.** MECO is quantised at 10 ms, so reserve(h) is a step function: 25.8 % over 61.5–62.75 m, 24.4 % from 63.0 m (rg05 scan). Bisection can then go non-monotonic: the no-band cap is 76.84 m at ×0.97 but 78.45 m at ×0.95 (rg11).
- **(c) The mass-knowledge error is a constant proportional N(0, 3 %)** (run6 l.634, l.831). B1 is sensitive to it: m_est ×2 gives 0.982 (p 0.039) and a maximum burn of 23.24 s (rg05).
- **(d) CA_nf and CA_legs are not dispersed.** ±30 % has no significant effect (p ≥ 0.45).
- **(e) Rigid airframe and quasi-steady drogue** (staging l.141).

**Required action:**
- (a) State the growth law beyond J_ref, or extend it.
- (b) Search on a grid that resolves the reserve steps, or interpolate MECO.
- (c) See RG-16.

### RG-12 (MINOR). Traceability and compliance records are stale or inconsistent.

**Gate:** interface freeze for SIL/HIL.

**Evidence.**
- **inputs_read is out of date.** gnc.json l.166–190 lists combustion v1, mechanical v1 and REQUIREMENTS rev 1. The runs used combustion v2.3, mechanical v2 and electronics v1 (REPORT l.83).
- **The REQUIREMENTS body disagrees with its amendments:**
  - B1 85 m (l.26) vs 62 m (l.102);
  - ENG-04 "plans relight on 0.6 s" (l.52) vs 0.81 s (l.103);
  - ENG-06 envelope "DC-B1 v2 (100 m, 19 s)" (l.54) vs the dispersed cycles up to 24.09 s (gnc.json l.40).
- **ENG-04 non-compliance is not recorded as a deviation.** ENG-04 (l.52) asks for ≤ 0.5 s and ±50 ms. The vapour-state relight delays reach 0.809 s (REPORT l.86); the liquid state alone spreads 0.37 s; gnc.json l.1469 itself notes "t90 1.04–1.43 s".
- **ENG-07 slew is below 100°/s at the v2 load.** The requirement text says 111.2°/s "as built" (l.55), but that figure is for the v1 load. gnc.json l.1884 gives 99.847°/s at the v2 load and 97.766°/s with the hose at its limit; Mechanical's exact kinematics are still owed.
- **B-TVC-1 still names reduced bandwidth as a fallback** (l.89), against the lead decision recorded at gnc.json l.33, l.1916 and l.5061 (degraded mode: P 0.676 / 0.968, p 0.00098).
- **Sources and interface gaps.** RC-03 and RC-07 sit outside the hub (REPORT l.97, l.129). electronics.json v1 lacks the tracker, notch interface, abort law, k_est_asc 2, v2.8 sequence, flag and FC_THRUST (gnc.json l.5110).

**Required action:**
- Update inputs_read.
- Lead: align the REQUIREMENTS body with the amendments.
- Record ENG-04 compliance per line state, or record a deviation.
- Close ENG-07 at the v2 load.
- Correct the B-TVC-1 text.
- Bring RC-03 and RC-07 into the hub.

### RG-13 (MINOR). The FSW exists only in the simulator, and the ratchet is switched by an environment default.

**Gate:** SIL/HIL.

**Evidence.**
- **The firmware does not have the FSW yet.** gnc.json l.302: the tracker and the governor are not in the firmware. k_est_asc 2 and the v2.8 plan logic are also sim-only.
- **The ratchet is switched by the environment.**
  - It is enabled by `os.environ.setdefault("GNC_PC_RATCHET", "1")` in 13 scripts (e.g. m2_relight_v28 l.43, m2_regband_mc l.32, m2_throat_mc l.38).
  - m2_prop_closure l.47 maps it to att_ref_mode 1; the run6 default is att_ref_mode=0 (l.215).
  - An external GNC_PC_RATCHET=0 would silently change the FSW under test.
- **Not independently tested.** The reviewer did not re-test the ratchet's benefit.

**Required action:**
- Keep the FSW configuration in a versioned record that is hashed with each result.
- SIL/HIL acceptance: firmware traces match sim6 traces for the same inputs, within stated tolerances.

### RG-14 (NOTE). Touchdown margin depends on pad slope.

rg07 is a rigid-body energy check, using the ASSUMED legs from gnc.json (4 legs, foot radius 0.40 m, 14.77 kg, z_cg 0.654 m).
- At the criteria corner (0.5 m/s, 10°/s, 5° tilt, toward a pivot between two feet), the margin is ×1.94. A 3.4° downhill slope consumes it (5.1° with the stroke-lowered CG).
- With horizontal speed alone, the margin is ×4.92 and the limiting slope 9.3°.

**Action:** a pad slope specification (TO-DEFINE with the leg design).

### RG-15 (NOTE). Confirmations.

- **Reproducibility and statistics** are exact (R1–R6, R11–R12).
- **The 1-DOF cross-check** agrees on propellant and impulse within 0.3 %, and on the coast acceleration.
- **k_est_asc 2:**
  - its benefit is confirmed: k_est_asc 0 gives P 0.968 (−15/+1, p 5.2e-4) with 11 exhausted and a maximum burn of 32.57 s;
  - it is insensitive to CA ±30 % and to accelerometer bias up to 10 mg (p ≥ 0.375);
  - it is sensitive to the mass error in B1 (RG-11 c).
  - Its behaviour with Pc invalid is unspecified: k_raw divides by F_mod (sim6 l.1890), which the flight computer derives from Pc. The estimator must freeze when Pc is invalid.
- **Other items consistent:** ×0.75 as a degraded mode, the ARM rule (gnc.json l.1877–1879; ENG-13 l.64) and n 4.8.
- **The cap closes the +25 % rule** at the corner under the author's assumptions.
- **MEOP holds with the 24 °C interlock.** 45 bar holds (44.33 bar, CHANGELOG l.101 (9); REQUIREMENTS l.105–106). The MC's U(15, 25) °C draw is immaterial (staging §3).

### ADDENDUM: v3.1 STAGING (FC_THRUST). The lead adopted 650 N held for 3 frames on the τ 20 ms estimate, and a provisional mass-estimate requirement of ≤ 1 % (1σ) (CHANGELOG l.108).

### RG-16 (MAJOR). The ≤ 1 % requirement is derived without systematic terms.

**Gates:** SIL/HIL; first flight with FC_THRUST armed (C or B1).

**Evidence.**
- **How the requirement was derived.** e is treated as a zero-mean per-flight error (staging l.94–100).
  - Reproduced (rg16): at 1 %, the lowest post-onset held maximum is 660.1 N, a margin of 10.1 N over 650 N.
  - At 1.5 % it is 651.9 N, a margin of 1.9 N.
- **Reviewer question (rg16 part 2): add a common under-read b to the 1 % random error.**

  | b | Misses of 670 N (of 4000) | Lowest held maximum |
  |---|---|---|
  | −0.5 % | 0 | 656.7 N |
  | −1 % | 0 | 653.3 N |
  | −1.5 % | 1 | 649.9 N |
  | −2 % | 19 (7 error sets) | 646.6 N |

  A 1 % (1σ) figure does not bound a scale or map bias, which adds linearly.
- **Flow-integration bias when Pc is lost (HYPOTHESIS).** The estimator form is "integrated flow from the ECU map" (gnc.json l.5086). If the 1.143 band top is a flow excess, the mass over-reads by (m0 − b)/(m0 − 1.143 b) − 1 (rg15):
  - A1: +0.69 % at the end of full thrust (+4.0 N at 571.5 N), +1.29 % at end of burn;
  - B1 85 m: +0.22 % and +1.58 %.
  - This acts on the false-abort side, where the Pc-lost held maximum is 635.6 N at 3 %. Throat growth and c* errors enter the same integral; they are not computed here.
  - sim6's Pc-lost branch scales thrust, not flow (l.1443–1444), so the term is absent from the flights.
- **An unexplained A1 offset** of 1.4 % between k_hat and F_acc (median 0.986; B1 0.999; staging l.167) is of the order of the requirement. HYPOTHESIS: the comparison windows differ, because the A1 estimator runs only in the landing burn (sim6 l.1882–1884).
- **The mass estimate also drives guidance:** B1 guidance uses the same m_est (RG-11 c).

**Required action:**
1. State the requirement as a total budget over the burn: weighing at ARM (scale TO-DEFINE), integration (map, c*, growth) and Pc-lost behaviour, with bias and random parts separated.
2. GNC specifies the estimator and flies it in sim6 with the errors in the flow, not only in the thrust.
3. Explain the A1 offset.
4. Re-check 650 N against the budget's systematic terms on both sides.

### RG-17 (MINOR). Confidence bounds are overstated about ×2.

**Evidence.**
- **The two profiles share their draws.** A1 run i and B1 run i share the seed-101 bias draws (rg15).
  - The Pc-lost held maxima correlate at 0.980, and depend on the bias factor with R² 0.98.
  - The pooled 1000 flights carry n_eff ≈ 505, so 0/1000 bounds the false-abort rate at 0.59 % (0.60 % per profile), not 0.30 % (l.57).
- **The stuck cases rest on 500 error sets.** The 4000 cases use 500 distinct error sets: "about 1000" (l.77) should read 500, with a bound of 0.60 %. At 3 %, the 252 misses come from 75 rows and 40 sets.
- **The normal tails restate the assumption.** The normal-fit tails (l.58, l.100) and the criterion "tails ≤ 1e-4" (l.117) are tails of the assumed N(0, s), not evidence. The v1.1 per-frame normal model (1.9 % at 1 %) is superseded.

**Required action:**
- Correct the bounds.
- Use independent draws, or report per profile.
- Replace the tail criterion with a margin on the budgeted error.

### RG-18 (MINOR). The synthetic ramps test the measurement chain, not the system.

**Evidence.**
- **What the ramps omit** (staging l.64–77):
  - the drag terms: D_true − D_model and the error acting on D, of order ±4 N at 60 m/s (reviewer estimate);
  - the thrust shape and tank decay;
  - the vehicle response;
  - the Pc-valid detectors (the 30 bar abort, ENG-09 l.60; PINTLE_FAULT, ENG-13 l.64).
- **What the miss rate therefore covers.** It is the rate of the FC_THRUST channel alone. The case it protects is a lost Pc plus a stuck pintle, or a linkage failure the encoder does not see.
- **Consequences are not evaluated** (l.230). Reviewer inference, not computed: a miss at 670 N means a powered climb at thrust-to-weight 4.3–4.6 until exhaustion, which is a range-safety case.
- **The valid window is ambiguous.**
  - "Drogue released" (l.113; CHANGELOG l.108) must mean "no drogue load". Otherwise the A1 ascent cases from 500 N fall outside the window.
  - Flight C needs a rule for tether load (reviewer addition).

**Required action:**
- 6-DOF fault flights: stuck at 670 and 876 N, from ascent and from landing, with Pc valid and with Pc lost, using all detectors, including the consequence of a miss.
- Define the valid window explicitly.

### RG-19 (MINOR). Unmodelled latencies and exposure after detection.

**Evidence.**
- **What the published latency covers.** The flight-computer side is a 20 ms ramp lag and 38.5 / 43 ms to the decision (l.47).
- **What it excludes:** IMU group delay, flight-computer and ECU scheduling, CAN, axial modes, and decimation aliasing (l.50, l.226).
- **After the decision:** MV close ≤ 0.10 s and a tail-off of 37.5–38.2 N s (CHANGELOG l.101 (2), (5)).
- **Exposure (reviewer arithmetic).** From the onset, the p99 detection of the 876 N cases is 0.126 s (from 500 N) or 0.265 s (from 150 N). Adding the MV close and the tail-off gives 0.28–0.47 s at up to 876 N, before the unbudgeted terms.
- **Low-frequency combustion oscillation** is outside the vibration model and erodes the margin between 571.5 N and 650 N.

**Required action:**
- An end-to-end budget with each term sourced, verified in HIL.
- T1–T4 log F_acc against the load cell, including the low-frequency content (l.236).

### RG-20 (NOTE). v3.1 confirmations and a reproducibility defect.

- **The F_acc_c correction is exact.** F_acc − D_model = m(1 + e) f_meas. The correction is applied per sample, before the linear filter and before the 0.1 N rounding. D_model (m2_fc_thrust_mest l.48–54) equals the term used in reconstruct.
- **Flights not re-flown.** They were not re-flown with c·e; this is immaterial for the monitor. The same m_est drives k_est_asc 2 (sim6 l.1899), but its effect on guidance is not evaluated.
- **Counts reproduce** (R15, R16).
- **Coast acceleration reproduces** (R14). The lead's wording "≥ 11.4 s of +8 m/s²" (CHANGELOG l.107) merges two numbers: the minimum duration of positive f_z (11.4 s, l.142) and the mean (8.18 m/s², l.140). Combustion should use the time history, including the −1.90 m/s² turnover dip (l.141).
- **The T_tank note is accepted.**
- **Builder defect.** m2_gnc_json_v3 v5 fails with a NameError when fc_thrust.json exists (l.168), so v3 cannot be rebuilt from the current tree. Fix this before v3.1 is published.

## 5. MODEL ADEQUACY

**Fit for:**
- paired comparisons of FSW options;
- propellant and reserve trends;
- duty-cycle shapes;
- the measurement-chain statistics of FC_THRUST.

The 1-DOF cross-check matches N2O per impulse within 0.3 %. The B1 85 m rule outcome is model-dependent: 26.34 % in the 6-DOF against 24.73 % in the 1-DOF.

**Not yet fit for:**
- **Absolute P claims.** Delivered thrust per flow and the regression law are epistemic but drawn per run (RG-04).
- **Relight claims on the current hardware.** The start-delay tables are SIM on ASSUMED data from the old segment, P is conditional on light, and the flag is not simulated (RG-01, RG-02).
- **Grain web and O/F effects.** sim6 has no web state, and the J metric ignores O/F (RG-03).
- **Gust robustness.** Turbulence is tied to mean wind (RG-06).
- **FC_THRUST system miss rates.** These need synthetic ramps replaced by flights, a rigid airframe replaced by axial modes, and real latencies (RG-18, RG-19).

**Other model features:**
- the growth cap at J_ref and the 10 ms MECO quantisation bias the critical tail (RG-11);
- the B predictor's truth leak shifts the apex tail by about 3 m (RG-10).

**Statistical resolution.** At 500 runs and P = 0.99, the Wilson half-width is about 0.8–1 %, so effects below about 2 % are not resolved.

## 6. EVIDENCE RIGOUR

**Strong:**
- paired common random numbers with exact McNemar;
- bit-identical reproducibility;
- explicit SIM / ASSUMED / DERIVED tags;
- failures kept as evidence (REPORT l.133–140);
- open items declared, including the 44 cm³ dependency;
- "no significant difference" correctly not read as "no degradation" (gnc.json l.39).

**Weak:**
- P conditional on light, presented without the abort probability (RG-02);
- epistemic quantities averaged as aleatory (RG-04);
- "covers" asserted from one metric (RG-03);
- q* depends on the fixed 1.37 s fault point; on the spread basis it is 0.055–0.85;
- pooled bounds over correlated draws, and normal tails used as acceptance (RG-17);
- configuration by environment variable (RG-13);
- sources outside the hub (RG-12);
- a builder that cannot rebuild the published file (RG-20).

## 7. CONSISTENCY TABLE

| Item | Statement A | Statement B | Status |
|---|---|---|---|
| Segment volume | gnc.json l.36: 21.4 cm³ | CHANGELOG l.86: 32.6 cm³; l.95 and REQ l.109: ~44 cm³ | superseded |
| Fault path | REPORT l.87: fixed 1.37 s (prep 0.56 s) | CHANGELOG l.101: purge 0.64–0.69 s | open (RG-01) |
| PRIMED meaning | l.84: P_feed ≥ 0.5 P_tank | l.101: vapour-full reads PRIMED | contradiction (RG-01) |
| B1 cap | REQ l.26: 85 m | REQ l.102 and gnc.json l.31: 62 m | body stale |
| Relight plan | REQ l.52: 0.6 s | REQ l.103 and gnc.json l.1471: 0.81 s | body stale |
| ENG-04 latency | REQ l.52: ≤ 0.5 s, ±50 ms | gnc.json l.1469: 1.04–1.43 s; REPORT l.86: to 0.809 s | non-compliance unrecorded |
| ENG-07 slew | REQ l.55: 111.2°/s as built | gnc.json l.1884: 99.847 / 97.766°/s | open |
| Reduced bandwidth | REQ l.89: B-TVC-1 fallback | gnc.json l.33, l.1916, l.5061: degraded mode only | REQ text wrong |
| Thermal governance | gnc.json l.23, REPORT l.72: B1 governs | CHANGELOG l.106: A1 lip 819.5 vs B1 710.7 °C | per quantity (RG-09) |
| 62 m sizing | REPORT l.65, REQ l.102: covered by 85 m | rg04; CHANGELOG l.101 (10) | fails for fuel and O/F (RG-03) |
| Inputs | gnc.json l.166–190: v1 / v1 / rev 1 | REPORT l.83: v2.3 / v2 / v1 | stale |
| ENG-06 envelope | REQ l.54: DC-B1 v2 (100 m, 19 s) | gnc.json l.40: dispersed cycles | stale |
| Effective sample | staging l.77: ~1000 | rg15: 500 error sets | correct to 500 |
| Stale-flag rationale | CHANGELOG l.104: drain vs 0.3 s | hold window 19.7–19.8 s | rationale wrong, rule stands |
| Drogue acceleration | CHANGELOG l.107: ≥ 11.4 s at +8 m/s² | staging l.140–142; rg10 | wording |
| FC_THRUST window | CHANGELOG l.108: drogue released | A1 ascent cases from 500 N | define "no drogue load" |
| T_tank | MC U(15, 25) °C | ENG-12 15–24 °C (REQ l.106) | immaterial, noted |

## 8. REQUIREMENTS TRACEABILITY

| Requirement | GNC evidence | Reviewer status |
|---|---|---|
| A1 mission (REQ l.15–23) | C1–C3 on the old segment | OPEN (RG-01, RG-02) |
| B1 (REQ l.26 / l.102) | C5 | PARTIAL: cap provisional; burn limit not implemented (RG-03, RG-04) |
| ENG-03 (l.51) | MC at 5 F_max/s | NOT SUPPORTED at 2 F_max/s (RG-05) |
| ENG-04 (l.52 / l.103) | delay tables; t90 note | NON-COMPLIANT for vapour relights, unrecorded (RG-12) |
| ENG-05 (l.53 / l.104, l.107) | abort law; tail-off bracket on 21.4 cm³ | bracket stale (RG-01) |
| ENG-06 (l.54) | duty cycles; growth MC | web not shown at 62 m (RG-03); growth capped (RG-11) |
| ENG-07 (l.55) | gnc.json l.1884 | marginal at the v2 load; B-TVC-1 (RG-12) |
| ENG-07c/d (l.57–58) | A1J basis | B1 62 m not on this basis (RG-07) |
| ENG-09 / ENG-12 (l.60, l.63; l.105–106) | T_tank note | consistent |
| ENG-13 (l.64) | arm_rule l.1877 | consistent |
| Over-thrust abort (gnc.json l.24; CHANGELOG l.108) | staging v3.1 | threshold provisional; mass requirement REVISE (RG-16 to RG-19) |
| Retained vapour ≤ 19 cm³ (REQ l.109) | Mechanical: NOT MET | OPEN, drives RG-01 |
| B-PNT-1 / B-TVC-1 (l.88–89) | — | slew value (RG-05); text (RG-12) |

## 9. VERDICTS AND ACCEPTANCE CRITERIA

**Overall: REVISE.**

| Deliverable | Verdict | Conditions |
|---|---|---|
| interfaces/gnc.json v3 | REVISE | RG-01 to RG-06, RG-12 |
| REPORT-v3 checkpoint | REVISE | C2/C3 superseded; C5 "cover" |
| FSW v2.7 k_est_asc 2 + ratchet (provisional SIL/HIL baseline) | ACCEPT WITH COMMENTS | RG-11 c, RG-13, RG-15 (freeze on Pc invalid), RG-16 |
| v2.8 planning rule (plan = Pc-confirm deadline) | ACCEPT WITH COMMENTS | the value 0.81 s holds only for a liquid or ≤ 19 cm³ segment (RG-01) |
| Option (c) 1.41 s | REVISE | RG-01 |
| Stale-flag rule | ACCEPT WITH COMMENTS | RG-08 |
| B1 62 m cap as a provisional planning value | ACCEPT WITH COMMENTS | not a flight value until RG-03 and RG-04 close |
| "85 m cycles cover 62 m" | REVISE | RG-03 |
| Duty cycles rev d records | ACCEPT WITH COMMENTS | RG-09 |
| No-light accounting | REVISE | RG-02 |
| Throat growth 7–11 % | ACCEPT WITH COMMENTS | RG-11 a |
| ×0.75 degraded mode | ACCEPT | REQ text (RG-12) |
| n 4.8, ARM rule, slew ≥ 100°/s | ACCEPT WITH COMMENTS | ENG-07 at the v2 load |
| ENG-03 minimum 2 F_max/s | REVISE | RG-05 |
| Launch commit ≤ 6 m/s | ACCEPT WITH COMMENTS | gust criterion (RG-06) |
| v3.1 FC_THRUST 650 N / 3 frames / τ 20 ms | ACCEPT WITH COMMENTS (provisional) | RG-17 to RG-19 |
| v3.1 mass requirement ≤ 1 % (1σ) | REVISE | RG-16 |
| v3.1 coast acceleration; T_tank note | ACCEPT | — |
| v3.1 B1 62 m records | REVISE | band records (RG-03) |

**Acceptance criteria by gate.**

**SIL/HIL firmware freeze:**
- Firmware implements the tracker, governor/ratchet, k_est_asc 2 with a freeze when Pc is invalid, and a Pc-based B predictor.
- Traces match sim6 within stated tolerances.
- The FSW configuration is hashed with the results.
- Relight values are not frozen until RG-01 closes.
- The flag, including stale and late-flip cases, is simulated in the loop.
- The FC_THRUST end-to-end latency is measured and the valid window defined.
- electronics.json carries the flag, FC_THRUST and k_est interfaces.

**B-PNT-1:** the ENG-03 value is resolved and measured under load.

**B-TVC-1:** ENG-07 is measured at the v2 load at 6.6 and 7.4 V; B1 62 m is re-flown on the resulting basis; the REQUIREMENTS text is corrected.

**T1–T4:**
- delivered thrust per flow and the regression law, each with uncertainty;
- throat growth per flight;
- low-frequency thrust content;
- F_acc against the load cell;
- relight attempts in the flight segment state, counted toward p_nl.

**B1 first free flight:**
- cap re-derived on the measured engine with a conditional MC;
- burn limit implemented, simulated, with its action defined;
- Combustion has reviewed the band records;
- launch commit includes a gust criterion and site data;
- safety area sized on the apex distribution;
- pad slope specified;
- mass-estimate budget closed;
- ENG-03 resolved.

**A1:** all of the B1 criteria that apply, plus:
- RG-01 closed: 44 cm³ fault path, retained vapour resolved, a flag that can see vapour or planning without it, relight P re-flown;
- RG-02: accounting rebuilt with a sourced p_nl;
- RG-09: thermal governance per quantity.

**Supervision.** Registration of this verdict in supervision.json is outside the reviewer's write scope and is left to the lead.

