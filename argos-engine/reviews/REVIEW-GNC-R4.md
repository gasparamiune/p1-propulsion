REV-GNC-6: independent delta re-check of GNC rev4 (staging_v3.1/rev4), for gnc.json v3.2
I am the independent reviewer, not the author (I also did REV-GNC-3, -4 and -5). I checked only the staged rev4 copy (MANIFEST_rev4 083675a6abddaabe), my REV-GNC-5 (REVIEW-GNC-R3.md f2aafa51c7117ba8), CHANGELOG lines 203-223 (file e40141003255e78f, 223 lines) and gnc.json v3.1 (4f3209323b0e0ed4). For [12] I also used, as the lead asked, the 3D FE modal (REPORT-FEA3D.md a9f7f30055063c8e sections 9 / 9A, results/modal_summary_v351.json 561195eb1aa49aae), Electronics servo_jint_estimate_v1.json (8ef633c09a6d84f6) and mechanical.json (e4d3e7c9df529171). Everything below is SIM (flown tables), DERIVED (my own statistics or linear margins on them) or ASSUMED where stated. Matching numbers show that a computation repeats; nothing here is physical approval.

VERDICT: PUBLISHABLE WITH CORRECTIONS
- No BLOCKING finding. Every rev4 number I re-computed or re-flew reproduces, most exactly.
- A1 = 210 m is ACCEPTED: my own exact McNemar / UB95 statistics on the staged per-run tables give the same band, and a full re-fly of the six decision tables (6000 flights) is identical to the staged rows on every column.
- Four MAJOR findings need exact text changes before v3.2 is written:
  - the ENG-11 requirement wording (RV6-01);
  - the ENG-11 window's dependence on the plant, from the 3D FE check (RV6-14);
  - the landing-mass window (RV6-02);
  - the 210 m gate-delay premise (RV6-03).
- None of them needs a new flight or a re-run before publication. RV6-03 makes the 210 m relight P conditional on an arm that must be flown before that P is used for flight acceptance. RV6-14 asks GNC for an ENG-11 re-run before the K_s window is quoted as design-to.
- The lead's FE question on [12] (answered in [12], FE plant check):
  - rev4's J is servo-side, as the lead read it;
  - ENG-11's engine inertia matches the FE modal inertia within 1.6 %;
  - the "37 % below" compares the servo-rotor term with the engine term, which add;
  - the FE's stiffer structure puts the top of the 100-130 window at risk (DERIVED; GNC re-run recommended).
- The two contradictions the lead asked about: D_crit at 210 m is a MAJOR condition, not a blocker; line 213's duty-cycle sentence is a MINOR record correction, not a blocker.

== (a) What I ran (all in my scratch; staged code, pins and tables only) ==

| Check | Script | Size | Result |
|---|---|---|---|
| Line-208 band, own statistics | v01_p2_band | 38 tables, N=1000 main bases | 210 m; identical to the author at every band |
| Decision-table re-fly, subset | v03_refly4 | 11 arms, 438 flights (all 80 g discordant runs + 16 concordant per arm) | identical on every column |
| Decision-table re-fly, full | v03_refly4 (RV6_FULL) | 6 tables x 1000 flights: case liq h210 / h215 both main bases, reference liq h285 both main bases | identical on every column, 6000/6000 rows |
| D_crit and duty cycle at 210 m | v02_dcrit_duty | all v351 h200-h235 tables, 4 bases | reproduces R4-F5 / R4-F6 |
| Items [11] [13] [14b] [15], RV5-06 | v04_items, v07_extra | staged tables / JSON | see items |
| ENG-11, author's linear model imported unchanged | v05_eng11_env | 9 grid rows, 20 continuous-pose rows, 72 bending-sweep rows | see [12] |
| R2 starve re-fly | m2_r2_starve v1.0 unchanged, reviewer tree7 | 24 cases x 60 = 1440 flights | 0 of all values differ |
| ENG-11 6-DOF claim | v08_eng11_fly | 20 staged e11 tables, N=500 per base | reproduces; author counts equal |
| ENG-11 plant vs 3D FE | v09_fe_plant | frequency arithmetic only, no margins | see [12] FE plant check |

- Trees: tree3 = staged gnc_dev3 (sim6 v2.9-dev) and tree7 = staged gnc_dev7 (sim6 v2.13-dev), with the work-area paths redirected by sed to scratch copies of staged files (diffs in logs/*_tree_path_diff.out). Pins: iface_v351 against pins_rev4_v351 and iface_v3d against pins_rev3 (both sha256sum -c OK).
- The re-fly audit hook recorded no file opened outside the hub, my scratch and the Python install. A write guard refused any write outside my scratch.
- The draw-prefix claim holds: runs 0-499 of the 1000-run draw equal the 500-run draw on every drawn value (checked in every re-fly job).
- Processes: at most two of my own at a time, nice 10, NUMBA_NUM_THREADS=1. I touched no other process and nothing under /home/claude/work/fea3d.

== (b) A1 = 210 m under the line-208 rule (my statistics) ==

Rule as applied: highest 5 m band h with h and every lower flown band showing no significant pooled loss (A1_none + A1J_pc, exact two-sided McNemar on discordant pairs, p < 0.05 and lower) against st|G73|h285 (v3d), success = ok AND 1000 liq_left >= 80 g, and UB95 = d + 1.645 se <= 1.0 pp with d = (lost - gained)/n and se = sqrt(lost + gained - (lost - gained)^2/n)/n. Decision = lower of liq and pw. Newcombe method-10 bound reported beside it (my own implementation).

liq|G73, N=1000 per main base (pooled n 2000):

| Band | lost / gained | p | UB95 (pp) | Newcombe (pp) | Rule |
|---|---|---|---|---|---|
| 200 m | 15 / 23 | 0.256 | 0.107 | 0.120 | PASS |
| 205 m | 16 / 20 | 0.618 | 0.293 | 0.312 | PASS |
| 210 m | 25 / 20 | 0.5515 | 0.802 | 0.827 | PASS |
| 215 m | 29 / 20 | 0.2529 | 1.026 | 1.053 | bound fails |
| 220 m | 39 / 22 | 0.0396 | 1.492 | 1.521 | loses |
| 225 m | 37 / 20 | 0.0331 | 1.470 | 1.501 | loses |

- pw|G73: band 220 m (225 m UB95 1.169 pp). Decision value = 210 m, under either reading of "every lower band". All figures equal the author's p2_rev4.json (68cf1f643effd5b9).
- Reference tables equal the cited hashes (rev3 h285 + rev4 refext x500). N = 1000 on the main bases, 500 on A1_pc / A1J_none.
- Sensitivity arms reproduce: G80 at 210 m liq UB95 0.972 / pw 0.617 pp (vs G73 at 210 m: liq -1/+0, pw 0/0); v351t liq 210 PASS / 215 UB95 1.206 pp, pw 210 and 215 PASS; v352 210 and 215 PASS on both states.
- Four-base pooled (informational): at the author's mixed N, liq 210 m -33/+28 UB95 0.595 pp, 215 m -47/+29 UB95 1.078 pp; at equal N = 500 on all four bases, 210 m -19/+18 UB95 0.55 pp PASS and 215 m -35/+19 p 0.040 LOSES.
- Stability (NOTE RV6-11): runs 0-499 alone give 210 m, runs 500-999 alone 205 m; a paired bootstrap (B = 2000, runs resampled jointly over states and bases) gives the decision band 205 / 210 / 215 m in 28.3 / 29.4 / 32.3 % of resamples (200-220 m in 96.6 %). Onset sensitivity (liq): 90 g or 100 g gives 205 m. 210 m is the rule's value at N = 1000; it is a statistical decision with about +/- 5 m sampling width, and 215 m fails by 0.026 pp.
- 204 (1) counting rule applied to every nominal run (a fired commit lead below 2.1 s counted as not landed): liq 210 m -26/+20, UB95 0.858 pp PASS; 215 m 1.081 pp. Band unchanged (NOTE RV6-13).

== (c) The two contradictions ==

D_crit at 210 m (R4-F5): reproduces exactly, and it is a MAJOR condition (RV6-03), not a blocker.

| A1 trim, liq|G73, N | A1_none | A1J_pc |
|---|---|---|
| Runs fired / zero-slack commits | 785 / 16 of 1000 | 765 / 16 of 1000 |
| Nominal commit lead min / p01 | 2.264 / 2.586 s | 1.946 (run 191) / 2.630 s |
| D_crit(2.4 s) min | -0.136 s | -0.454 s |
| D_crit(2.1 s) min / p01 | 0.164 / 0.576 s | -0.154 / 0.674 s |
| D_crit(1.9 s) / D_crit(1.3 s) min | 0.364 / 0.964 s | 0.046 / 0.646 s |
| 285 m comparator D_crit(2.1 s) min, N=1000 | 3.765 s | 3.633 s |

- Line 204 (1) rests on "Nominal leads are >= 2.65 s in every table, so the band arises only after a gate fault (gate delay >= 3.465 s)" and 208 (4) on D_crit 3.765 s. Both hold at 285 m only. At 210 m one nominal A1J_pc run (and the same run on A1_pc) is already in the uncounted band with no gate fault.
- The drogue model is quasi-steady and the deploy-to-inflation delay is not modelled (gnc.json v3.1 open item). Any such delay acts as a gate delay on every flight, not as a rare fault.
- Reviewer estimate (ASSUMED: the REV-GNC-5 285 m P-by-realised-lead curve transferred to 210 m; a uniform gate delay D first uses each run's slack, then cuts its lead): expected P loss at 210 m 0.003-0.04 pp at D 0.25 s, 0.06-0.12 pp at 0.5 s, 0.21-0.28 pp at 0.75 s, 0.74-1.15 pp at 1.0 s, about 7.2-7.4 pp at 1.5 s. The 210 m PASS has 0.198 pp of headroom to the 1.0 pp bound, so by this estimate it holds to an effective gate delay of about 0.5 s and is consumed near 0.75 s. At 285 m the same transfer gives about 0 up to ~3.5 s. This is my estimate, not a flown result.

Line 213 "the A1 duty cycle shortens" (R4-F6): not supported; MINOR (RV6-05), not a blocker (B1 governs sizing). Like for like at N = 1000 the A1 engine-on p99 is unchanged:

| burn_time p99, N=1000 | 210 m (v3.5.1) | 285 m (v3d) |
|---|---|---|
| A1_none liq | 8.443 s (max 8.727) | 8.446 s (max 8.796) |
| A1_none pw | 8.339 s | 8.337 s |
| A1J_pc liq | 8.270 s | 8.227 s |
| A1J_pc pw | 8.165 s | 8.111 s |

- All A1_none values exceed the 8.258 s A1 sizing counter, as at 285 m. The author's [5] compares the 210 m halves (8.374 / 8.510 s) with the 285 m runs 0-499 only (8.371 s); its conclusion is right, its figures mix N.

== (d) Items [0]-[15] ==

| Item | Subject | REV-GNC-5 correction | Status | Findings |
|---|---|---|---|---|
| [0] | /rev3_rev4 block | RV5-03, 05, 06, 09, 10 | CLOSED (RV5-06 with a residual) | RV6-10 |
| [1] | late commit / gate delay | RV5-04 | CLOSED; new 210 m reading reproduces | RV6-03 (MAJOR), RV6-04 |
| [2] | unpurged alternative (P6c) | RV5-03, RV5-08 | CLOSED | - |
| [3] | A1 band, propellant closure | RV5-01, RV5-06, RV5-02 | CLOSED; A1 = 210 m ACCEPTED | RV6-11, RV6-13 (NOTE) |
| [4] | launch-commit wind evidence | RV5-05 | CLOSED | - |
| [5] | duty-cycle records | condition stated | CLOSED; figures corrected | RV6-05 |
| [6] | R2 v2 statistics | RV5-06, RV5-09 | CLOSED; lit bracket reproduces (re-flown) | RV6-08 |
| [7] | FC_THRUST latency | RV5-10 note | CLOSED | - |
| [8] | RG-08 re-plan proposal | as written | CLOSED | - |
| [9] | purge bound text | RV5-07 | CLOSED | - |
| [10] | 100 N vs 62.5 N start level | as written | CLOSED | - |
| [11] | landing-mass window | NEW | coverage of 16.15 kg nominal ACCEPTED; widening REJECTED | RV6-02 (MAJOR) |
| [12] | ENG-11 K_s requirement | NEW | grid, continuous envelope and 6-DOF reproduce; J convention VERIFIED against the FE; requirement wording REJECTED; window conditional on the plant | RV6-01, RV6-14 (MAJOR) |
| [13] | RE-24 gimbal-fault monitor | NEW | reproduces; undetected-jam claim needs its scope | RV6-06, RV6-12 |
| [14] | R2 v2 answers (a)-(c) | NEW | (a) and (c) reproduce; (b) needs precision | RV6-07, RV6-08 |
| [15] | payload record | NEW | 31/31 arms reproduce; description corrections | RV6-09 |

Items [0]-[10], per REV-GNC-5 correction:
- RV5-01 (rule restated, sweep to 200 m, four bases at 210/215 m): applied as specified; my numbers equal the author's. CLOSED.
- RV5-02 (250 m planning value): WITHDRAWN in [3]. CLOSED.
- RV5-03 (pooled ECU-hold losses): rh300c200 -11/+2 p 0.0225, rh400c200 -13/+0 p 2.4e-4, rh190c500 -15/+0 p 6.1e-5 equal my REV-GNC-5 values. CLOSED.
- RV5-04 (per-threshold D_crit, L400 bins, "below about 2.1 s" band): present and correct at 285 m. CLOSED. The 210 m reading is new; see RV6-03 and RV6-04.
- RV5-05 (W10 split of the e19|G73|L400 loss): -40/+3 at W10 >= 6, -3/+0 inside W10 < 6 (n 728). CLOSED.
- RV5-06 (withdrawn-value markers): 20 sidecars; every target sha256 equals the staged rev3 file and every one of the 14 table hashes equals the staged table. An independent JSON walk finds every W1 (rh220/rh250) leaf and every W2 leaf (lit_k*, gap_N, T_mid_N) covered in five of six JSON targets (the r2v2_eval sidecar marks 64 derived leaves beyond the name match, which is conservative). The rev3_results.json sidecar misses the lit-model hold trace: RV6-10. The rev4 v3.2 texts cite rh220/rh250, gap_N/T_mid_N and 60 g only as withdrawn or superseded. CLOSED with a MINOR residual.
- RV5-07 (cap <= 2.55 s; ~80 g flown at 210 m): present; G80 at 210 m reproduces. CLOSED.
- RV5-08 (hold timing margins; revisit rule per 208 (3)): present. CLOSED.
- RV5-09 (both R2 windows): present in [0] and [6]. CLOSED.
- RV5-10 (AR(1) wording): present in [0] and [7]. CLOSED.

[11] Landing mass (DERIVED from the P2 h210 tables, N=1000 per main base)
- The touchdown-mass figures reproduce: 14.18-18.13 kg, p01 14.50, p50 16.03, p99 17.47 kg; 42-43 % at >= 16.15 kg.
- The dispersion is the vehicle's: m_land correlates 0.987 with dry_scale and -0.46 with liq_left. The heavy runs are heavier vehicles that land with less liquid (bin medians 532 g below 15 kg, 311 g at >= 17 kg).
- P(80 g) falls with touchdown mass in all four strata. Fisher exact (two-sided), >= 16.15 kg vs below: A1_none liq 0.9742 vs 0.9913, p 0.041; A1J_pc liq p 0.46; both pw strata p 0.55-0.57; pooled liq (both bases) 0.9764 vs 0.9887, p 0.049; pooled pw p 0.31. The author's "unpaired, not a test" understates this.
- At >= 17 kg there are only 62-64 runs per stratum (P 0.968-0.984); the 18.13 kg maximum is a single run. The dispersed tail is not a demonstration of landing capability at 18.13 kg.
- Paired evidence exists in the rev4 payload tables (same seed and run index, liq, N=500 per base, pooled main bases), against the 0 kg vehicle with the same tank layout (pl0 h210, nominal touchdown 16.07 kg):

| Arm | Nominal touchdown (p50) | vs pl0 h210 | Line-208 |
|---|---|---|---|
| +0.5 kg, 210 m | 16.52 kg | -22/+6, p 0.0037, UB95 2.47 pp | loses (less liquid) |
| +0.5 kg, 190 m | 16.56 kg | -5/+8, UB95 0.29 pp | PASS |
| +1 kg, 2.20 kg N2O, 210 m | 17.25 kg | -8/+8, p 1.0, UB95 0.66 pp | PASS |
| +2 kg, 2.45 kg N2O, 210 m | 18.49 kg | -23/+10, p 0.035, UB95 2.24 pp | loses |
| +2 kg, 2.55 kg N2O, 210 m | 18.64 kg | -36/+12, p 7.2e-4, UB95 3.53 pp | loses |

- So, paired: a 17.25 kg nominal touchdown lands as well as 16.07 kg when the propellant margin is restored, and 18.49-18.64 kg loses even with surplus liquid (failures at touchdown angular rate, see [15]). These arms also move the CG (+27 to +65 mm) and are liq only.
- Is the 16.15 kg coverage claim sound? Yes, as a nominal claim: the 210 m decision was made on an MC centred there (nominal deterministic touchdown 16.11 kg). Can the window be widened on the unpaired evidence? No: see RV6-02.

[12] ENG-11 (DERIVED, linear; the author's m2_eng11 v1.1 imported unchanged; V5c structure, J 1.6e-3 kg m2, cons kinematics, fixed ECU notch Q 1 / -12 dB at e x the landing centre-pose mode, e 0.95 / 1 / 1.05, zeta 0.02 / 0.05 / 0.10, floor20 corners; ENG-07d = stable and upper GM >= 6 dB)
- Reproduction (9 grid rows): alpha 100 PASS 6.18 dB, 130 PASS 6.18, 140 fail 5.30 (9/1458 corners), 160 PASS 6.42; beta 100 PASS 6.03, 150 PASS 6.24, 160 fail 4.47 (12/1458), 190 PASS 6.33, 220 PASS 6.39. All equal the author's grid.
- Continuous pose envelope. The loop depends only on (f, zeta), and the rocking frequency moves continuously with the gimbal angle between the 9 FE poses (continuity ASSUMED). I re-evaluated every corner on a dense frequency grid over each condition's [f_min, f_max] (0.1 Hz, 0.02 Hz within 1 Hz of bending):

| K_s (N m/rad) | alpha, 9 poses / continuous | beta, 9 poses / continuous |
|---|---|---|
| 100 | PASS 6.18 / PASS 6.178 | PASS 6.03 / PASS 6.029 |
| 110 | PASS / PASS 6.235 | PASS / PASS 6.083 |
| 120 | PASS / PASS 6.283 | PASS / PASS 6.129 |
| 130 | PASS / PASS 6.184 (f 24.02 Hz) | PASS / PASS 6.171 |
| 140 / 150 | fail 5.30 / 5.45 (not re-run) | PASS / PASS 6.204, 6.236 |
| 160 | PASS / PASS 6.424 | fail 4.47 (not re-run) |
| 190 | PASS / PASS 6.496 | PASS 6.33 / FAIL 5.09 (120 corners, f 24.44 Hz) |
| 220 | PASS / PASS 6.552 | PASS 6.39 / FAIL 5.74 (65 corners, f 24.46 Hz) |
| 230 | (PASS) / not run | PASS 6.40 / FAIL 5.91 (39 corners) |
| 250 | PASS / PASS 6.598 | PASS 6.43 / PASS 6.204 |
| 270 | PASS / PASS 6.622 | PASS 6.45 / PASS 6.440 |

- So the beta passes at 190 and 220-230 N m/rad are pose-sampling artifacts: no FE pose lands in the failing band, but poses between them do. The failing corners are all full tank, act_fast, z 0.02 (with and without max-q aero), with the rocking mode at 24.14-24.66 Hz against the 24.30 Hz bending mode, and the notch (e 0.95 x the centre landing mode) below about 24.3 Hz. This explains the author's "no simple separation rule". The failures come from the full-tank rocking range coinciding with the bending mode, and they also depend on where the fixed notch sits relative to the bending mode: beta passes at 250-270 on the continuous envelope although its pose range spans 24.3 Hz, with the notch's e 0.95 corner at 24.3-24.7 Hz. It supports the bending-coincidence explanation. Every failing corner recorded at the nominal bending lies at a full-tank rocking frequency of 24.14-24.71 Hz: 45 corners, from the author's grid and sens rows and my continuous envelope (v09).
- Bending sweep (part C; full-tank bending scaled, landing scaled with it, K_s 100 / 110 / 120 / 130, both axes, 9 poses and continuous; upper GM in dB):

| Full-tank first bending | alpha, K_s 100-130 | beta, K_s 100-130 |
|---|---|---|
| 10 Hz (gnc.json v3.1 minimum) | fail 2.68-2.88 | fail 1.70-2.03 |
| 12 Hz | fail 5.20-5.44 | fail 3.43-4.03 |
| 15 Hz (v3.1 goal) | PASS 6.03-6.17 | fail 1.89-4.43 |
| 18 Hz | 100 fail 5.16 (continuous 5.54); 110-130 PASS 6.16-6.25 | fail 0.05-1.98 (continuous unstable) |
| 20 Hz | 100 fail 0.14 (continuous unstable); 110 fail 2.12; 120 fail 5.60; 130 PASS 6.28 | fail 0.02-0.87 (continuous unstable) |
| 22 Hz | fail 0.79-3.42 | fail 0.60-3.61 (continuous unstable to 4.19) |
| 24.3 Hz (ASSUMED nominal) | PASS 6.17-6.28 (continuous 6.18-6.32) | PASS 6.03-6.17 |
| 27 Hz | PASS 6.19-6.34 | PASS 6.05-6.19 |
| 30 Hz | PASS 6.21-6.36 | PASS 6.06-6.20 |

- The 9-pose and continuous results agree on pass / fail in all 72 rows.
- The lowest tested bending at which the whole window passes on both axes is the nominal 24.3 Hz. At 22 Hz every row fails, so the threshold lies between 22 and 24.3 Hz (not resolved).
- Failure mechanism at 10-15 Hz: the bending mode erodes the margin by itself. The worst corners are landing floor100N, with the rocking mode at 18-23 Hz, far from the bending mode.
- Failure mechanism at 18-22 Hz: rocking-bending coincidence. The worst corners have the rocking mode within about 0.6 Hz of the bending mode, at z 0.02 and act_fast, and several are unstable.
- So gnc.json v3.1 /requirements/structure/airframe_first_bending_min_Hz = 10 Hz (goal 15 Hz, "DERIVED >= 5 x attitude crossover") is not consistent with ENG-07d at K_s 100-130 with the single fixed ECU notch: both axes fail at 10 Hz and beta fails at 15 Hz (DERIVED).
- This extends the author's 0.9 x shift (21.9 Hz full: K_s 116 fails on both axes) to the whole range the requirement allows, and supports the author's RESEARCH PROPOSAL of a second notch on the measured bending mode.
- 6-DOF claim (v08; my exact McNemar on the staged e11 tables against the P2 h210 table, N=500 per base, success = ok and ok AND 80 g): 20 arms (2 bases x 10 K_s / rocking-range arms, K_s 58 included), lost 0-2, gained 0-2, every p >= 0.5, UB95 <= 0.77 pp. "No arm loses a landing" reproduces, and the counts equal the author's. As the author says, the 6-DOF does not carry the linear flex corner set (no bending-mode coincidence), so it cannot support the window.
- The v1.1 bisection (alpha 157.0, beta 95.4) is correctly SUPERSEDED: pass/fail is not monotone in K_s, on the 9 poses or on the continuous envelope.
- "K_s >= 100 N m/rad measured at B-TVC-1, plus a measured bending mode before freeze" is not self-consistent: as a one-sided bound it admits values the author's own grid fails (140-180 and 200-210) and values that pass only by pose sampling (190, 220-230); clause (2) gives no acceptance criterion and no consequence of a failed re-run. Correct wording: RV6-01.

[12] FE plant check (lead request, CHANGELOG 221 and 223 (5))
Inputs: REPORT-FEA3D 9 / 9A (a9f7f30055063c8e), results/modal_summary_v351.json (561195eb1aa49aae), Electronics servo_jint_estimate_v1.json (8ef633c09a6d84f6) and mechanical.json (e4d3e7c9df529171). Method: my v09, frequency arithmetic with m2_eng11's own V5c table, g and I_piv imported unchanged. No margin was evaluated; a margin re-run is GNC's job (RV6-14).

(1) J convention rev4 used: J is servo-side, as the lead read it. The convention is VERIFIED (CODE / DERIVED); the value of J stays ASSUMED, TO-VERIFY at B-TVC-1.
- J (1.6e-3 kg m2, range 0.76-2.7e-3) is the servo's internal rotor + gear-train inertia at the servo OUTPUT shaft, the shaft where K_s is defined.
- Source: Electronics SB-2292SG at 7.4 V, J_int 1.597e-3 (range 0.762-2.71e-3), DERIVED from datasheet torque and speed with an ASSUMED tau_m of 3-8 ms and gear efficiency 0.7. Electronics' own engine-side value is 0.0368 kg m2.
- m2_eng11 reflects J with the V5c kinematic factor g: 23.04 = n^2 at the centre pose; over the 9 poses 23.0-28.7 (alpha) and 17.7-36.7 (beta).
- It then ADDS J g to the engine's own inertia about the pivot, I_piv = 0.05944 kg m2 full / 0.05882 landing (m2_csi_v3.build_conditions on the v3.5.1 mass properties). The loop sees I_piv + J g = 0.0957-0.0963 kg m2 at the centre pose.
- mechanical.json rocking_mode_Hz states the same split: "EXCLUDES the reflected servo rotor inertia J_int n^2 ... GNC CSI carries both".

(2) Is the ENG-11 plant consistent with the FE? DERIVED, from SIM V5c against SIM 3D FE:
- Engine inertia: consistent. The FE modal inertia (0.0585 kg m2 beta, engine; 0.0590 alpha, engine + ring) is the quantity ENG-11 calls I_piv, and I_piv equals it within -0.3 % to +1.6 %.
- J against the FE: the lead's "37 % below the FE value" compares two different terms. The FE leaves the servo rotor out by construction, so J g (0.0369 kg m2) adds to the 0.0585 kg m2 rather than estimating it. ENG-11's total rocking inertia is 1.62-1.64 x the FE's.
- The 2.5e-3 kg m2 (0.0585 / 23.04) is the ENGINE's inertia seen at the servo shaft, not a J estimate. ENG-11's servo-side total is 4.15e-3 kg m2.
- Nothing in the FE moves the nominal J toward the 2.7e-3 corner. That corner (beta 5.91 dB at K_s 116, rev4 sens) is the upper end of the J_int range and stays the J risk, as rev4 states. The FE cannot test J.
- Kinematics: consistent. The FE's servo-in-series stiffnesses imply g = 23.039 on both axes and at both k_s, equal to ENG-11's centre g (23.038 / 23.040).
- Structural K: the FE is stiffer. The FE neutral production-pose stiffness (rigid servo) is K_alpha 7284 / K_beta 5370 N m/rad, against V5c centre mech_T 6539 / 4325: +11.4 % / +24.2 %. V5c's chain-high centre values (7527 / 4736) bracket alpha but not beta.
- The FE 8 deg stop range is 6400-8577 / 3888-6570 N m/rad, against V5c 5808-7406 / 3239-5167 on its 9 poses at 7 deg. These come from different CAD (v3.3 with a rigid engine, v3.5.1 with a flexible engine) and different pose sets.
- Rocking frequency: consistent once J is accounted for. Like for like (centre pose, J = 0, as in the FE):

| alpha / beta, Hz | ENG-11 plant (landing) | FE (production K) |
|---|---|---|
| servo rigid | 53.07 / 43.16 | 55.51 / 47.82 |
| k_s 58 in series | 21.86 / 20.97 | 21.86 / 21.35 |
| k_s 174 in series | 32.71 / 29.93 | 33.07 / 31.27 |

- With the servo in series, ENG-11 reproduces the FE within 0 to -4.3 %; the remainder is the structure.
- With the nominal J, the loop's rocking frequency is sqrt(I_piv / (I_piv + J g)) = 0.786 of these: about 16.4-25.6 Hz at the centre pose for k_s 58-174.
- So the FE's "21-33 Hz with the servo in series" is not the loop's rocking frequency, because it omits J. Both bands overlap the ASSUMED bending mode (24.3 / 25.6 Hz).

(3) What this does to the 100-130 N m/rad window. Frequency map (DERIVED; uniform scaling of the V5c poses by the FE / V5c neutral ratio is ASSUMED until the F2 cone poses post). The coincidence band is the 24.14-24.71 Hz above, at the nominal bending:

| Full-tank 9-pose rocking range, Hz | V5c (ENG-11 as run) | FE structure |
|---|---|---|
| alpha, K_s 130, J 1.6e-3 | 23.25-24.02 | 23.63-24.41 (in band) |
| beta, K_s 130, J 1.6e-3 | 19.71-23.06 | 20.56-24.22 (in band) |
| K_s at which the pose maximum reaches the band, J 1.6e-3 (alpha / beta) | 131.9 / 156.3 | 126.1 / 128.5 |
| the same, FE with hot E (S -10 %) | - | 131.7 / 139.9 |
| the same, J 0.76e-3 | 94.8 / 89.5 | 90.9 / 79.7 |
| J 2.7e-3, K_s 100-130 (alpha / beta range) | 18.8-21.2 / 16.4-19.9 (below the band) | 19.1-21.6 / 17.0-20.9 (below the band) |

- At nominal J on the FE structure, the top of the window (K_s about 126-130) enters the coincidence band.
- At J 0.76e-3 the whole window is exposed on either structure: beta's pose range straddles the band at every K_s from 100 to 130. Rev4's 9-pose PASS at J 0.76e-3 / K_s 116 is therefore not evidence for the continuous envelope.
- The n48 convention gives the same exposure. Its V5c beta range straddles the band at K_s 110-130; rev4 sens n48 beta K_s 116 already FAILS at 2.83 dB with f 24.20 Hz.
- Hot E moves the edge back to about 132 / 140 N m/rad. The full-tank corners occur early in the flight, when the gimbal is coldest, so the T_REF structure applies to them (ASSUMED).
- The compliant-airframe variant (k_af ASSUMED, stop045 only) lowers the rigid-servo K by 13-14 %. Applied at neutral (ASSUMED), it would take back all of the alpha difference and about two thirds of beta's, so the airframe stiffness belongs in the re-run.
- Consequence: 100-130 N m/rad is a window of the V5c plant at nominal J. On the FE plant its top is not established, and it is not robust over the J range.
- The requirement wording therefore has to state the plant it was computed on, and its acceptance clause (re-run on the measured K_s, J and rocking / bending modes) carries the weight. Wording and re-run: RV6-14.

[13] RE-24 (SIM, sim6 v2.13-dev amendment J; my statistics on the staged tables)
- rec0 equals the P2 h210 table on every run and all 217 / 219 common columns. mon2: 0 aborts and 0 monitor trips in 1000 nominal flights (one-sided 95 % UB 0.30 %); largest no-jam metric 0.179 deg (x50) / 0.191 deg (s50, lit) against 1.5 deg. The model includes the flexible engine mount (rock_K drawn over the iface_v351 axis-stiffness range) and the AS5048A quantisation; encoder noise and vibration are not modelled (NOTE RV6-12).
- Detected landing-burn jams reproduce: continue / abort per arm 42/13, 39/14 (A1_none servo A / B), 44/11, 44/14 (A1J_pc) of 469. Pooled P with the jam: 0.136-0.150 flown on, 0.084-0.088 with the abort (the v32 text says 0.144-0.150 and 0.086-0.088, omitting servo B and A1J_pc lbA2). The time-to-go bins (59/84, 12/210, about 0) reproduce from lbA1.
- Undetected jams: 31 per arm reproduce, 0 lost and 0 gained against the no-jam twin in every arm. But the undetected population is exclusively late jams: onset at u >= 0.742 of the landing burn, 0.252-1.192 s before the twin's touchdown (p50 0.34-0.39 s). Every earlier jam was detected (detected time-to-go p50 2.64-2.66 s). Excursions are not small (jam_dmax up to 4.97 deg); the monitor metric reached 1.35-1.49 deg. The four arms hold 60 distinct runs (pairwise overlap 16-21 of 31). 0 of 31 lost gives a one-sided 95 % UB of 9.2 % per arm.
- "undetected_identical_to_record_twin" compares lbA2 with lbA1 when the monitor did not act; it is a code identity, not evidence.

[14] R2 v2 answers
- (a) Code reading confirmed in the staged gnc_dev7 sim6: mode-3 axial filter runs from phase >= 3 and is never reset; reference and descent rate sampled at E2 with (vz/vz(E2))^2; frames every 10 ms from the first step with E2 and Pc invalid; 3-frame running minimum; release also needs engine-lit truth. ACCEPTED.
- (b) Frame-noise estimate, my Monte Carlo under the author's assumptions (iid N(0, 5 N) per frame, flat signal, increase of the window maximum of the 3-frame running minimum): 50 frames p50 +3.1 N, p99 +7.8 N; 80 frames p50 +3.8 N, p99 +8.2 N. The author's "+4 N (median) to +8 N (p99) over 50 frames" overstates the 50-frame median. The "+5.3 to +6.0 N" margin is R2 v2 mode 3 (31.86 / 31.18 N at W10 < 6 against 37.16 N), not the 20.85 N (R2 v1, margin 16.31 N) bound named in the same paragraph. At the bounding run the exceedance probability is 6.5 % (0.5 s window, margin 5.98 N) and 18.4 % (0.8 s, 5.30 N); at the v3.1 margin of 16.31 N it is 0. RV6-07.
- (c) Starve threshold: I re-flew m2_r2_starve v1.0 unchanged (gnc_dev7, iface_v3d + pins_rev3, N=60, 24 cases): every released / aborted / landed count and release time equals the staged r2_starve.json. Thresholds 0.30 s (0.5 s window) and 0.60 s (0.8 s; W10 < 6 0.65 s) ACCEPTED. Corrections in RV6-08.

[15] Payload (record; founder line 219 keeps 2.00 kg and no payload)
- All 31 arm-level line-208 statistics (N500 and N250 sets, vs the v3d reference) equal the author's JSON. pl0 h210 and pl1 h210 m2.20 both read -9/+11 against the reference by coincidence: they are distinct tables (464f1d52a7621d2c vs 6668166b8383282d; touchdown p50 16.07 vs 17.25 kg; 7 and 9 discordant runs between them per base).
- Bands: with the author's 180 m floor, 0 kg 210 m and +0.5 kg 190 m reproduce. Under the literal line-208 rule ("every lower flown band") 0 kg and +0.5 kg have no band, because the flown 170 m (and 155 m) screens fail (0 kg 170 m UB95 2.48 pp; +0.5 kg 170 m UB95 4.42 pp). The floor is defensible (a separate relight-timeline mechanism) but must be stated as part of the rule.
- Failure modes at +2 kg: the author's fail_modes omit the touchdown-rate criterion. At 2.55 kg every failure has touchdown rate > 10 deg/s (18/18 A1_none, 19/19 A1J_pc), and 12 of them have no other listed mode; at 2.45 kg rate > 10 deg/s is 10/11 and 14/15. "Touchdown tilt / lateral speed" should read "touchdown angular rate > 10 deg/s (with tilt or lateral speed in a minority)". Zero exhaustion confirmed.
- Engine-on time of the 2.20 kg option: burn_time p99 8.92 s (A1_none) / 8.71 s (A1J_pc), max 9.24 s, against 8.37 / 8.20 s at 2.00 kg and the 8.258 s A1 sizing counter; 2.45-2.55 kg 9.27-9.58 s. [15] does not state it.
- DERIVED against MC. The equal-margin apogees (DERIVED, deterministic, payload_rev4.json) are 181.1 / 155.3 / 117.0 / 91.4 m for +0.5 / +1 / +2 / +3 kg (liq). They are propellant-margin equivalences, not bands; the MC gives a band only at +0.5 kg (190 m).
- Below about 180 m the relight timeline governs: at 155 m, P(80 g) is 0.55-0.57 with +1 kg (N=500 per base) and 0.71-0.77 even with 0 kg (N=250 per base); at 115 m (+2 kg) and 90 m (+3 kg) it is 0.
- The "115 / 90 m" in [15] are the flown points next to the DERIVED 117.0 / 91.4 m, and CHANGELOG 218 (4) quotes 117 / 91 m. The two are consistent, but the text should name both.

== (e) Findings ==

RV6-01 MAJOR - [12] ENG-11 requirement wording.
Problem: "K_s >= 100 N m/rad" admits failing stiffnesses (140-180, 200-210 on the author's grid; 190 and 220-230 fail on the continuous pose envelope), and clause (2) has no acceptance criterion. The listed pass set "100-130, 190, 220-270" is partly a 9-pose sampling artifact.
Exact correction (replaces the FINAL REQUIREMENT PROPOSED sentence):
"FINAL REQUIREMENT PROPOSED (DERIVED, linear, on the V5c structure (CAD v3.3), at the ASSUMED J 1.6e-3 kg m2 (servo output shaft, reflected by g = n^2 at the centre and added to the engine inertia), cons kinematics and first bending 24.3 Hz full / 25.64 Hz landing): (1) design-to window for the servo output stiffness 100 <= K_s <= 130 N m/rad (two-sided; the only contiguous window that passes ENG-07d on every floor20 corner on the continuous pose envelope between the 9 V5c poses; margins 0.03-0.28 dB above 6 dB; conditional on the plant, see the RV6-14 sentence); (2) acceptance: ENG-07d (stable, upper GM >= 6 dB at every floor20 corner, continuous pose envelope, notch as flown) re-run on the B-TVC-1 measured K_s (with its measurement uncertainty), J and reflected-inertia convention and rocking modes at the poses, and on the measured or airframe-FE first bending mode (full and landing); K_s is frozen only on a PASS; on a FAIL the notch set (second notch on the measured bending mode) is changed and the margins re-run before any K_s change. The 9-pose passes at 190 and 220-230 N m/rad are WITHDRAWN (pose sampling); 250-270 N m/rad pass on both axes but are not a design-to value."
Also:
(i) Replace "No K_s in 58-174 N m/rad is robust to a -10 % bending error with one fixed notch" with: "No K_s in 58-174 N m/rad is robust to a -10 % bending error with one fixed notch; with that notch the 100-130 window passes only for a full-tank first bending >= 24.3 Hz among the values tested (10, 12, 15, 18, 20 and 22 Hz each fail on at least one axis; 24.3, 27 and 30 Hz pass; REV-GNC-6 v05 part C, DERIVED)".
(ii) Replace "The grid gives no simple separation rule (beta passes at 220-270 with its pose range spanning the bending frequency)" with: "The grid gives no simple separation rule: on the continuous pose envelope beta fails at 190 and 220-230 and passes at 250-270 with its pose range spanning the bending frequency; every failing corner at the nominal bending has its full-tank rocking frequency at 24.14-24.71 Hz".
(iii) Record against gnc.json /requirements/structure/airframe_first_bending_min_Hz (10 Hz, goal 15 Hz): "NOT CONSISTENT with ENG-07d at K_s 100-130 with the single fixed ECU notch (DERIVED, REV-GNC-6 v05 part C). Set the airframe minimum from the measured bending mode and the ENG-07d re-run, or adopt the second notch." Per line 222 this is an open item kept for the airframe work, not a new v3.2 number.

RV6-02 MAJOR - [11] landing-mass window.
Problem: the proposal widens /icd_inputs_for_airframe/landing_mass_window_kg to the dispersed touchdown set 14.18-18.13 kg on unpaired evidence that falls with mass (pooled liq Fisher p 0.049) and has no demonstration near 18 kg; paired arms bracket the nominal capability between 17.25 kg (PASS) and 18.49 kg (loses).
Exact correction (replaces the [11] proposal):
"landing_mass_window_kg: lower bounds unchanged (DERIVED hover rule: floor 12.5 % 7.08, 20 % 11.33, 25 % 14.16 kg). Upper bound: REQ reference for the lead to restate; GNC evidence: nominal touchdown 16.11 kg (DERIVED, A1_none liq, tank at 0.58 m, 210 m) / 16.15 kg (lead's v3.5.1 estimate) is covered by the line-208 210 m decision MC (SIM, N=1000 per main base). Record, kept as engine data / open item for the airframe work (CHANGELOG 222: ICD-AIRFRAME v2.1 is out of the finish scope; SIM, not a controller-qualified window): dispersed touchdown mass in that MC 14.18-18.13 kg (p01 14.50, p50 16.03, p99 17.47 kg); P(80 g) falls with touchdown mass inside it (pooled liq 0.976 at >= 16.15 kg vs 0.989 below, Fisher p 0.049). Paired record (SIM, liq, N=500/base, payload arms): nominal 17.25 kg with the propellant restored PASSES against the 0 kg vehicle (-8/+8, UB95 0.66 pp); 18.49 / 18.64 kg LOSE (p 0.035 / 7.2e-4). A planning touchdown mass above 16.15 kg needs its own paired arm."

RV6-03 MAJOR - [1] / lines 204 (1) and 208 (4) at the 210 m trim (D_crit).
Problem: the 285 m gate-delay tolerance does not carry to 210 m (table in (c)); 204 (1)'s "nominal leads >= 2.65 s" and "only after a gate fault" are false at 210 m, and the unmodelled drogue inflation delay acts as a gate delay on every flight.
Exact correction (append to [1] and to the A1 entry of [3]): "At the A1 trim 210 m the line 204 (1) / 208 (4) premises hold only at 285 m: nominal commit leads go down to 2.264 s (A1_none) and 1.946 s (A1J_pc, A1_pc), 16 of 1000 runs per main base commit with zero slack, D_crit(2.1 s) is 0.164 / -0.154 s (p01 0.576 / 0.674 s). The A1 = 210 m P (line-208 PASS, UB95 0.802 pp) holds for zero effective gate delay; by a reviewer estimate (ASSUMED transfer of the 285 m P-by-lead curve) it holds to about 0.5 s and is consumed near 0.75 s. CONDITION: a gate-delay injection arm at 210 m (D = 0.25 / 0.5 / 0.75 / 1.0 s, both states, N=1000 per main base, line-208 statistics) is flown, and the drogue deploy-to-inflation delay is bounded (TO-VERIFY, canopy data), before the 210 m relight P is used for flight acceptance." Not blocking for v3.2.

RV6-04 MINOR - [1] comparator and counting.
Exact correction: replace "the 285 m tolerance (3.765 s for 2.1 s; +0.156 s on pc bases)" with "the 285 m tolerance at N=1000 (3.765 s A1_none / 3.633 s A1J_pc for 2.1 s; 3.921 s on A1_pc, N=500)". Add: "the A1J_pc run 191 (nominal lead 1.946 s) is not a landing under 204 (1); with that rule on every nominal run the band is unchanged (liq 210 m -26/+20, UB95 0.858 pp)".

RV6-05 MINOR - [5] duty cycle figures.
Exact correction: replace the 210 m / 285 m p99 comparison with "liq|G73 burn_time p99 at N=1000: A1_none 8.443 s at 210 m vs 8.446 s at 285 m; A1J_pc 8.270 vs 8.227 s (pw 8.339 / 8.337 and 8.165 / 8.111 s). Line 213's 'the A1 duty cycle shortens' is not supported: equal within 0.003 s on A1_none, +0.043 s on A1J_pc." Keep "B1 governs; record only".

RV6-06 MINOR - [13] undetected-jam claim scope and P ranges.
Exact correction: replace "an UNDETECTED gimbal jam at the bound does not lose a landing" with "a landing-burn jam that the monitor does not trip on before touchdown lost no landing in this set: 31 runs per base and servo, all jams in the last 0.25-1.19 s before the twin's touchdown (onset u >= 0.742 of the landing burn; every earlier jam was detected), 0 lost / 0 gained against the no-jam twin (one-sided 95 % UB 9.2 % per arm; 60 distinct runs over the four arms)". Replace "0.144-0.150" with "0.136-0.150" and "0.086-0.088" with "0.084-0.088". Drop "identical to record twin" as evidence.

RV6-07 MINOR - [14] (b) noise wording.
Exact correction: "5 N rms frame noise (iid ASSUMED) raises the window maximum of the 3-frame minimum by +3.1 N median / +7.8 N p99 over 50 frames (0.5 s) and +3.8 / +8.2 N over 80 frames (0.8 s). Against the R2 v2 mode-3 margins at W10 < 6 (+5.98 N at 0.5 s, +5.30 N at 0.8 s) the bounding run would be released with probability 6.5 % / 18.4 %; against the v3.1 R2 margin (16.31 N = 37.16 - 20.85 N) the probability is about 0."

RV6-08 MINOR - [6] / [14] (c) starve scope.
Exact correction: add "(SIM, N=60, A1_none pw, 285 m v3d trim; transfer to 210 m / v3.5.1 ASSUMED; 0/60 aborts gives a one-sided 95 % UB of 4.9 %). With the 0.8 s window every lit run is released up to 0.60 s, but landings fall with the plateau (all winds 58/60 at 0.40 s, 55 at 0.45-0.50 s, 50/60 at 0.60 s; W10 < 6 44/44 to 0.55 s, 43/44 at 0.60 s); with 0.5 s at 0.40 s 53 of 55 released land. The window choice decides release; the starve itself costs landings." Accept the thresholds.

RV6-09 MINOR - [15] payload record.
Exact corrections: (i) "+2 kg 2.55 kg ... the residual losses are touchdown angular rate > 10 deg/s (18/18, 19/19 failures; tilt > 5 deg 4/4, lateral > 0.5 m/s 4/6), no exhaustion"; (ii) state the band rule as "line-208 rule with the sweep floor at 180 m (below it the relight timeline governs; the 0 kg and +0.5 kg 170 m screens fail, so the rule without a floor gives no band)"; (iii) add to the 2.20 kg option "A1 engine-on p99 8.92 s (A1_none) / 8.71 s (A1J_pc), max 9.24 s, vs 8.37 / 8.20 s at 2.00 kg and the 8.258 s A1 sizing counter: B1/thermal and erosion check TO-VERIFY before the option is quoted on the datasheet"; (iv) add the paired line "2.20 kg +1 kg vs the 0 kg vehicle (pl0 h210): -8/+8, UB95 0.66 pp"; (v) replace "P 0 at their equal-margin apogees 115 / 90 m" with "P 0 when flown at 115 / 90 m, next to their DERIVED equal-margin apogees 117.0 / 91.4 m; the equal-margin apogee is not a band below the ~180 m relight-timeline floor (at 155 m P(80 g) is 0.55-0.57 with +1 kg (N=500 per base) and 0.71-0.77 with 0 kg (N=250 per base))".

RV6-10 MINOR - RV5-06 residual (sidecars).
Exact correction: add to results/rev3_results.json.WITHDRAWN.json set W2 the paths /P4_R2v2/command_hold_trace/lit_k100_hold/* (9 leaf patterns: n_runs, hold_s[], hold_records_at_62p5N[], ECU_command_values_N[], F_cold_max_N[], valve_lift_max_mm[], R2_estimate_max_N[] 52.39-60.30 N, F_truth_max_N[] 59.5-65.3 N) and /bitchecks/v2.10_vs_v2.9/functional/checks/hold_trace_lit_k875, or state why these lit-model values are not withdrawn.

RV6-11 NOTE - A1 band width. State in [3]: "runs 0-499 alone give 210 m and runs 500-999 205 m; paired bootstrap 205 / 210 / 215 m in 28 / 29 / 32 % of resamples; 215 m fails the bound by 0.026 pp". The rule's value stands.

RV6-12 NOTE - [13] false-abort basis. "0/1000 (UB95 0.30 %); nominal metric max 0.18-0.19 deg vs 1.5 deg with the flexible mount and encoder quantisation modelled; encoder noise, vibration and supply sag not modelled."

RV6-13 NOTE - 204 (1) counting rule at 210 m: band unchanged (see (b)).

RV6-14 MAJOR - [12] ENG-11 plant against the 3D FE (CHANGELOG 221, 223 (5)).
Problem: the FE evidence settles the lead's J question:
- the convention is VERIFIED (J servo-side, added to the engine inertia);
- the engine inertia and the kinematic factor agree with the FE;
- the "37 % below" compares the rotor term with the engine term.
But the FE structure is 11 % (alpha) / 24 % (beta) stiffer than the V5c structure ENG-11 used. On the frequency map, that moves the rocking-bending coincidence into the top of the 100-130 window at nominal J (K_s about 126 / 129 N m/rad); at J 0.76e-3 the whole window is exposed. Rev4's window is a V5c-plant result, not yet one that holds for the FE plant.
Exact correction: append to [12] after "At the ASSUMED bending mode, K_s 100-130 N m/rad is the window to design to":
"The window is computed on the V5c structure (CAD v3.3). The 3D FE of CAD v3.5.1 (CHANGELOG 221; SIM, coarsened-model modes, production-model K) agrees with the ENG-11 plant on the engine inertia (0.0585 / 0.0590 vs I_piv 0.0588-0.0594 kg m2) and on the kinematic factor (23.04). It leaves the servo rotor out: J 1.6e-3 kg m2 is servo-side, 0.0369 kg m2 at the pivot, added to the engine inertia, so the loop's rocking frequency is 0.786 x the FE's 21-33 Hz. The FE structure is stiffer: neutral K 7284 / 5370 against V5c centre 6539 / 4325 N m/rad. On that structure, at nominal J, the full-tank rocking range reaches the coincidence band (24.1-24.7 Hz at the nominal bending) at K_s about 126 (alpha) / 129 (beta) N m/rad (DERIVED frequency map; uniform pose scaling ASSUMED). At J 0.76e-3 the whole window is exposed. GNC re-verifies the window before it is quoted as design-to."
Re-run recommended to GNC (not done by the reviewer): m2_eng11 on the continuous pose envelope, with:
(a) the FE structure: neutral and 8 stop poses now, the F2 cone poses when posted, rigid and compliant airframe, T_REF and hot E (-5 / -10 %);
(b) I_piv as now (consistent with the FE);
(c) J 0.76 / 1.6 / 2.7e-3 kg m2 with both the cons and the n48 convention, and optionally the rotor on the servo side of K_s (a two-mass chain, now that the FE gives the engine-side inertia) instead of lumped on the engine;
(d) the bending at nominal and at 0.9 / 1.1 x, or the airframe value when measured;
(e) K_s 90-160 N m/rad in 5 N m/rad steps.
Output: the window per J and structure, with the corners that set it. Not blocking for v3.2: the requirement already makes the freeze conditional on a re-run.

== (f) v3.2 values ==

ACCEPTED (with the tags given):
- A1 apogee target 210 m: liq|G73 band 210 m (-25/+20, p 0.5515, UB95 0.802 pp, Newcombe 0.827 pp), 215 m fails (1.026 pp), pw|G73 band 220 m; decision 210 m. SIM / DERIVED. With the RV6-03 condition.
- Four-base 210 m liq UB95 0.595 pp / pw 0.277 pp (informational); G80 at 210 m liq 0.97 / pw 0.62 pp; v351t liq 210 m, pw >= 215 m; v352 >= 215 m both states (upper-censored).
- 210 m gate figures: D_crit(2.4 / 2.1 / 1.9 / 1.3 s) min -0.136 / 0.164 / 0.364 / 0.964 s (A1_none) and -0.454 / -0.154 / 0.046 / 0.646 s (A1J_pc); p01(2.1 s) 0.576 / 0.674 s; 16/1000 zero-slack commits. DERIVED.
- Line 213 duty-cycle consequence: not supported (RV6-05 figures). DERIVED.
- ENG-11: K_s 58 FAILS (3.09 / 0.34 dB); design-to window 100-130 N m/rad (GM >= 6.18 / 6.03 dB, min |PM| 23.8 / 23.3 deg, modulus margin >= 0.354) at the ASSUMED inputs on the V5c structure, conditional on the plant (RV6-14) and with the RV6-01 wording; ksmin/mink bisection SUPERSEDED; 6-DOF "no arm loses" (lost 0-2 / gained 0-2, p >= 0.5). DERIVED / SIM.
- ENG-11 J convention: J servo-side (output shaft), reflected by g (n^2 = 23.04 at the centre), added to I_piv; I_piv 0.0594 / 0.0588 kg m2 consistent with the FE modal inertia 0.0585 / 0.0590 (within 1.6 %). CODE / DERIVED; J value ASSUMED, TO-VERIFY B-TVC-1.
- Landing mass: nominal 16.11 kg / 16.15 kg covered by the 210 m decision MC; dispersed 14.18-18.13 kg (p01 14.50, p99 17.47) as a loads record. SIM / DERIVED.
- RE-24: 0 false aborts in 1000; detected-jam P 0.136-0.150 (continue) / 0.084-0.088 (abort); coast and ascent jams P 0.000-0.002; undetected-jam result with the RV6-06 scope. SIM / ASSUMED (SIL bound).
- R2 v2: (a) code facts; starve thresholds 0.30 s (0.5 s window) / 0.60 s (0.8 s; W10 < 6 0.65 s), N=60, 285 m. SIM.
- Payload record: all arm statistics as staged; 2.20 kg +1 kg PASS at 210 m (-9/+11 vs reference, UB95 0.54 pp); +2 kg not met at 2.45 / 2.55 kg; iso-margin apogees 181.1 / 155.3 / 117.0 / 91.4 m and T/W as DERIVED (read from payload_rev4.json, not re-computed by me; not bands below ~180 m, RV6-09 (v)). Record only (line 219).

REJECTED (replace with the RV6 text):
- "K_s >= 100 N m/rad" as the requirement, and the pass set "190-190, 220-270" as stated (RV6-01); 100-130 N m/rad as a window without its plant basis (RV6-14).
- For the record (not rev4 text): the reading "J 1.6e-3 is 37 % below the FE inertia / the FE value is near the 2.7e-3 corner" (CHANGELOG 223 (5)). The two terms add; the FE does not inform J ([12] FE plant check).
- landing_mass_window_kg widened to 14.18-18.13 kg (RV6-02).
- "an UNDETECTED gimbal jam at the bound does not lose a landing" without its scope; "0.144-0.150" / "0.086-0.088" (RV6-06).
- "the 285 m tolerance ... +0.156 s on pc bases" (RV6-04); the [5] p99 figure pairs (RV6-05); "+4 N (median)" and the margin attribution in [14] (b) (RV6-07); "touchdown tilt / lateral speed" at 2.55 kg (RV6-09).

== (g) Files (hub reviews/gnc/rev4/; sha256 first 16; MANIFEST_REV-GNC-6.sha256 is sha256sum -c OK) ==
- Manifest: reviews/gnc/rev4/MANIFEST_REV-GNC-6.sha256 0102191ef982cb8b (48 files, 7.5 MB; sha256sum -c OK when run in reviews/gnc/rev4/). This review file is outside the manifest.
- Scripts (scripts/): rv6lib.py a120cdb2bd19c7f5, guard_run.py 3c4ec98375787fcd, env6.sh 56dcf1d9a5f29817, env7.sh c38f2cd23e11c78a, v01_p2_band.py aa519d6ca81ccc45, v02_dcrit_duty.py aea7bde9fd6494d7, v03_refly4.py a4086c7fda39ec3d, v03_run.sh 4e3f05fa7189325c, v03_full.sh 108b512503630cfa, v04_items.py 03c2e242887b7e0c, v05_eng11_env.py 7d11c314227c0d69, v07_extra.py 52a4491576cdca2d, v08_eng11_fly.py 20e12d7823a3d6c9, v09_fe_plant.py 48eba75f1804063e, stage_rv6.sh 6a29b30219218c82.
- Results (results/): v01_p2_band.json 9a25f38c8b2d5ed3, v02_dcrit_duty.json 0de7dcb9c2ecc03f, v04_items.json daa13dcfd36bd5d9, v05_eng11_env.json f0432df3c70dad6e, v07_extra.json 58ff60a78416f8fd, v08_eng11_fly.json 85ffca95264d63c0, v09_fe_plant.json a513b164c16d37d1, r2_starve_refly_tree7.json 2ef5a75bcabd1489.
- Re-fly comparison records: results/refly/ v03r4_case_1792437849.json 120c399dd96f4fa4, v03r4_case_1792437926.json c52feae699b826dc, v03r4_ref_1792437914.json 9ee7cc12893e115f; results/refly_full/ v03r4_case_1792438345.json 09fcaece33152115, v03r4_ref_1792438206.json 3d9c80197df07466.
- Re-flown decision tables (tables/, N=1000 each, identical to the staged rows): rf_A1_none_liq_G73_v351_h210 235eab877b94e5d4, rf_A1J_pc_liq_G73_v351_h210 bbcdb4a56eb7ba46, rf_A1_none_liq_G73_v351_h215 e55597fbd5da2786, rf_A1J_pc_liq_G73_v351_h215 205d6bd109ea1316, rf_A1_none_liq_G73_h285 129950826009d67d, rf_A1J_pc_liq_G73_h285 e932395a6a727ab2 (each .csv_rv6_n1000.csv.gz).
- Logs (logs/): v01.log 500f77ce6c50daba, v02.log 295580695e77eb17, v03_case.log 605ae23e3b0b3d86, v03_ref.log bb9c329ab8aba877, v03_full_case.log 5606f761e0eecc72, v03_full_ref.log 4217806e87fb2a17, v03_tree_path_diff.out fefe576f49581c3d, v04.log 37a9cc1db89a8267, v05.log a1e75ffb3dbad8c4, v06_r2s.log 6a6bc9e576873610, v06_tree7_path_diff.out 50d7a6908419a57f, v07.log f8fac8ddf2dbe274, v08.log 72420013cdfc132b, v09.log 3e4634aacb286286.
