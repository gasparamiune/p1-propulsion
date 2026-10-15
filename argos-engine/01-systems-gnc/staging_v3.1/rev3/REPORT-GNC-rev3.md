1. CLAIM (checkpoint per SUPERVISION-WORKFLOW)
- These are SIM / DERIVED results for lead line 181 items P2-P6 and P8-P9. They ran on the rev3 code (sim6/run6 v2.9-dev to v2.12-dev, all bit-checked) and include the folds from lines 182, 186, 188 and 194. P1 (rev2.1 / rev2.2) was already done. P7 was not run.
- Nothing here is gnc.json, a physical approval or hardware evidence. Matching hashes and passing checks do not change that.
- I did not write public/engineering/supervision.json, REQUIREMENTS, reviews/, gnc.json, rev1/rev2/rev2p1/rev2p2 or the published duty_cycles index. The independent reviewer must be someone other than GNC.

2. FILES (hub root /home/claude/work/shared-fallback/engine; sha256/16)
Staging folder: 01-systems-gnc/staging_v3.1/rev3/ (486 files plus the MANIFEST, 160.6 MB). It contains results/, tables/ (fly and p5 tables, gzip -n), duty_cycles/, streams/ (npz files), scripts/, sim/gncsim_v2.12-dev, sim/iface_v35a, pins/ and logs/.

Index files:
- MANIFEST_rev3.sha256: 79c2c8cd5d10e3c4
- NOT_STAGED_rev3.txt: c4de8309bd95bb23 (lists only the temporary scratch of the v2.9 suite)

Results:

| File | sha256/16 |
|---|---|
| results/rev3_results.json (checkpoint inside; 11 v3.2 proposals, none applied) | e0f6e7611fe523b5 |
| results/eval/rev3_fly.json | e07783c149007c0e |
| results/eval/p6_late_commit_v1p1.json | 1cda7af00f531ef4 |
| results/eval/p6_late_commit.json (v1.0, kept) | afd7b24ff0e254ef |
| results/eval/reserve_dip.json (v1.1) | 806f589f7ae272b4 |
| results/eval/r2v2_eval.json | 4d5ddc5da93a16df |
| results/eval/hold_trace.json | 6aa0cb6acec996da |
| results/eval/p5_latency.json | c3ada252722a7a9d |
| results/eval/rg16w.json | f8d296ecca36f542 |
| results/eval/mass_v35_vs_v3d.json | ee89a8c0dff34d89 |

Bit-checks:

| Check | Off-parts | Functional |
|---|---|---|
| v2.10 | a8556319da77316c | f599391dac4703a8 |
| v2.11 | f542bb399b3e7e4f | 57c1d9a3f38c7b49 |
| v2.12 | 00c15ef32e04ca02 | v1.0 FAIL kept d1165a5ebed4fd0f; v1.1 29cdaad8abdf5649 |
| v2.9 full suite on rev3 code | — | 5c03053a5ad87605 |

Duty cycles:
- dc_record_285m.json: 27932a7e9d59b5a7
- DC-A1_full_flight_285m_disp_p99_kest2_liqG73_A1none_rev3.csv: b1064b3c879ccda3
- DC-A1_full_flight_285m_disp_p99_kest2_liqG73_A1Jpc_rev3.csv: 370d4cde38f26f31

Pins:
- pins_rev3: 23f3b29b29b3f476
- pins_rev3_v35a: c77a56322ece7124
- pins_rev3_v35a_cold: 0964e35a53bb1978

Simulator (sim6 / run6):

| Tree | Version | sim6 | run6 |
|---|---|---|---|
| gnc_dev3 | v2.9-dev | f90e0ba8e993ad60 | b054a222eff38b6e |
| gnc_dev4 | v2.10-dev, V2 | 1f92061d41db894a | 8719591fd6f8cafb |
| gnc_dev5 | v2.11-dev, L | 8ae4ecdc5ac910dc | d6b91f1649048254 |
| gnc_dev6 | v2.12-dev, V3 | b0d9d8a0ded64e28 | a1df28f35a2576f1 |

The v2.10 and v2.11 trees can be rebuilt from the staged patch scripts. The v2.9-dev code is in staging rev2.

Scripts:

| Script | sha256/16 |
|---|---|
| m2_rev3_results v1.0 | 62a706e465292652 |
| m2_rev3_stage v1.2 | 881dee094f3dd820 |
| m2_rev3_dc_record v1.0 (gnc_dev3) | 95714e685fba4d59 |
| m2_rev3_reserve_dip v1.1 | 1637162f04be1bd2 |
| m2_rev3_fly v1.1 (gnc_dev3) | a14abdef9fdcfb17 |
| m2_rev3_fly v2.1 (gnc_dev4) | 3ed1248b8bcfa49f |
| m2_rev3_fly v2.2 (gnc_dev6) | f477103ab2abe71d |
| m2_rev3_p6 v1.1 | 61ce9e2bc4ae8121 |
| m2_rev3_hold_trace | 52212d775267cc55 |
| m2_rev3_r2v2_eval | c317e4d9b21414d1 |
| m2_rev3_p5 | 37da7abc476e6363 |
| m2_rev3_rg16w | 84df5367bb8d2f3c |
| m2_bitcheck_v212 v1.1 | 6c24a695159f6ba1 |
| m2_bitcheck_v29 v1.2 | a18c353d695df53d |
| patch_sim6_v212 | 2e38c044e9c6a158 |
| patch_run6_v212 | 6809841346b56f48 |

Snapshots of the superseded script versions are in scripts/notes/.

Work area: /home/claude/work/space/out/rev3/. Notes are in /home/claude/work/space/rev3_notes/PROGRESS.md (731c19f9b03f111a).

3. CONFIGURATION
- Environment: gnc_dev3/scripts/m2r3_env.sh with GNC_IFACE=iface_v3d (the v3.5 arms use iface_v35a) and GNC_IFACE_PIN=pins_rev3 (the v3.5 arms use pins_rev3_v35a). GNC_STRICT=1, seed 101, 500 paired runs per arm.
- P5 / RG-16 used 200 runs; the traces and functional checks used 4-12 runs.
- Which tree each group was flown on:
  - gnc_dev3: repro, P2, P2v35, P2opt, P3, duty-cycle record.
  - gnc_dev4: P4s, P6, P8, P6b.
  - gnc_dev5: P5.
  - gnc_dev6: P6c, hold trace, final evaluation, v2.9 suite.
  - Each amendment is off by default and bit-identical when off, so the decided-path arms stay on their earlier tree.
- Apogee target: 285 m for P2, P3, P4, P6 and P8. P5 and RG-16 stay on the rev2 300 m comparator configuration, which is where the reviewer's 2.973 % / 4.015 % were computed.
- The 32 new tables were compressed with gzip -n. The P6, reserve-dip and fly evaluations were then re-run on the .gz files. Only the table references changed (64 / 16 / 64 path and hash entries); no value changed, compared field by field.

4. RESULTS BY ITEM
Labels: SIM = flown in the 6-DOF Monte Carlo; DERIVED = computed from SIM tables or interface data. Pairs of P values are A1_none / A1J_pc.

P6 late commit (SIM), coordinator watch item CONFIRMED:

| Commit lead | Nominal start | L400 start |
|---|---|---|
| ant13 (p50 1.31 s) | 0.000 / 0.012 | 0.000 / 0.000 |
| ant17 | 0.758 / 0.780 | 0.000 / 0.000 |
| ant21 | 0.990 / 0.990 | 0.640 / 0.720 |
| ant25 | 0.996 / 0.990 | 0.786 / 0.854 |
| Decided 2.90 s | 0.992 / 0.990 | 0.940 / 0.952 |

- Mechanism: the FSW holds T_fire until 1.9 s of flow (amendment G pgg_Tmin). Ignition therefore comes 0.99 s (p50) after the plain trigger, with E0 at 22.3 m (p50).
- Failure modes: tipover and no-touchdown with the nominal start (td_vz p50 about -12 m/s); tipover with L400 (td_vz p50 about -23.7 m/s).
- Consequence: purging at 1.3 s or later is never worse than the no-relight baseline, but the 1.3-1.7 s band must not be counted as a landing.
- Gate-delay tolerance (DERIVED): the commit comes at least 2.965 s after the gate opens. A commit lead below 2.4 s needs a gate delay of at least 3.465 s; below 1.3 s, at least 4.565 s.
- The smallest nominal commit lead in these tables is 2.65 s; the reviewer reports at least 2.66 s in 2000/2000 runs (REVIEW-GNC-R2 l.202).

Line-194 release-hold comparator, P6c (SIM x DERIVED). Reference: release at E2, 0.994 / 0.990.

| Arm | P | Paired result |
|---|---|---|
| rh300c200 | 0.986 / 0.980 | -4/+0, p 0.125; -7/+2, p 0.18 (not significant) |
| rh400c200 | 0.986 / 0.972 | A1J_pc -9/+0, p 0.004, LOSES |
| rh190c500 | 0.984 / 0.970 | A1J_pc -10/+0, p 0.002, LOSES |
| rh300 natural (about 100 N) | 0.994 / 0.990 | -1/+1 |

- P_total for the 200 N arms (DERIVED, minimum over bases): LO 0.39-0.46, HI 0-0.036, worst states 0.
- Residual released-then-A3: 0 for holds of 0.30 s or more at 200 N, and covered at 0.19 s at 500 N.
- Not admissible with Pc invalid.

P2 mass at 285 m (SIM, 60 g residual):
- The v3.5 ledger loses by exhaustion:
  - v35a: liq 0.940 / 0.942, pw 0.950 / 0.954 (-56/+9, p 2e-9).
  - v35t: liq 0.970 / 0.966, pw 0.976 / 0.970 (-30/+10, p 0.002).
- Options with no significant pooled loss against the v3d mass (not a proof of equivalence):
  - v35a: liq 245 m; pw 255 m and 245 m.
  - v35t: liq 275, 255 and 245 m and kd 0.7; pw 265 m or lower and kd 0.7.
  - liq v35t is not monotone (h265 loses at p 0.03), so treat these trims as bands, not thresholds.
- kd 0.7 against the same v35a bracket gains (+19/-6, p 0.015). The 5 m terminal gate loses heavily.
- New in v1.1 (DERIVED): I re-tested the options with the reviewer's tank-dip onset (R3-17, 69-80 g) applied to both arms. The 60 g column reproduces the evaluation exactly. With the dip onset:
  - liq v35t h275 and kd 0.7 become significant losses, and pw v35a h255 becomes one at 80 g.
  - What remains is v35a at 245 m (both states), and v35t at 255 m or lower (liq) / 265 m or lower (pw).
- NOT FLOWN: the v3.5.1 ledger and a separate 0.20 kg allowance arm (massprops v3.5.1 is not in the hub). The DERIVED bracket is v35t + 0.20 kg = +1.068 kg, between the flown v35t and v35a.

P3 285 m coverage (SIM):
- Decided G73 arms on the four bases:

| Arm | A1_none | A1J_pc | A1_pc | A1J_none |
|---|---|---|---|---|
| liq|G73 | 0.990 | 0.986 | 0.990 | 0.990 |
| pw|G73 | 0.990 | 0.988 | 0.986 | 0.990 |
| pl|G73 | 0.990 | 0.986 | 0.986 | 0.992 |
| e19|G73 | 0.992 | 0.990 | 0.990 | 0.994 |

- 285 m is better than 300 m: liq|G73 over all four bases -12/+29, p 0.012. Exhaustions fall from 8 to 0.
- e19|G73|L400 gives 0.940 / 0.952 and LOSES (-43/+3); the failures are mostly no-touchdown and lateral speed.
- The repro against the staged rev2 tables is identical.
- Duty-cycle record (one Monte Carlo run each, re-flown with the recorder; each reproduces its table row field by field):
  - A1_none run 380: engine-on counter 8.375 s, which is above the published A1 sizing cycle (8.258 s). Thrust-on 8.52 s, impulse 2911 N s, apex 288.2 m.
  - A1J_pc run 472: counter 8.189 s, inside the sizing cycle.
  - The 300 m v2.8 record is longer (8.528 s, 3020 N s).
  - These are records, not sizing cases; B1 governs thermal and erosion sizing.
  - Staged in rev3/duty_cycles/. The published index is unchanged; adding them is proposed for v3.2.

P4 R2 v2 (SIM statistics on DERIVED cold-flow bounds):
- Lit side PENDING: the lit model was withdrawn by line 194 (2), so P4c (20 arms x 2 bases) was not flown.
- Flame-out side, mode 3, 0.8 s window:
  - Inside W10 < 6 m/s: maximum 31.86 N, margin +5.30 N at 37.159 N. With x 1.3 heat pick-up: 35.3 N.
  - All winds: 39.45 N, margin -2.29 N; 4 of 2072 runs are above the threshold.
- Hold trace: with the hold the command stays at 62.5 N for 0.8 s and F_cold is 12.5-12.9 N. Without the hold, F_cold is 71.5-75.2 N and R2 is 50-63 N. The hold is load-bearing.

P5 RG-16 at the 0.5 s allowance (SIM on ASSUMED fault shape and vibration; flown at the 300 m comparator target):
- 0.5 s at 670 N adds 16.3-18.7 m/s (p50).
- A1 ascent apex p99 is 358 m (V) / 436 m (Lhi), maximum 463 m.
- B1 floor: highest height after onset p99 118 m, against a nominal apex of 62.9 m.
- The FC_THRUST in-loop statistic would trip in every dla05 run.
- Windowed budget:
  - A1 comp 2.973 % PASS by 0.012 pp; A1 non-comp 4.015 % FAIL. Both reproduce the reviewer.
  - B1 comp 2.083 % and non-comp 2.385 % PASS on white noise.
  - AR(1) vibration at the same RMS fails everywhere. The margin is not robust.

P7: NOT RUN. It needs a new sim amendment with its own bit-check, a dropout length (TO-DEFINE) and a throttle-map error band. The lead gates it at SIL/HIL.

P8 RG-08 late flip (SIM):
- liqF 0.972 / 0.978: -17/+4, p 0.007, LOSES.
- pwF 0.924 / 0.932: -64/+3, LOSES.
- liqP / pwP (UNKNOWN treated as UNPRIMED from the start) cost nothing measurable.
- A T_fire re-plan is listed as a research proposal with hypothesis, comparator and refutation. It was not flown.

P9 configuration:
- All three pin lists resolve and match.
- Code hashes are in every bit-check.
- G6 with P30_reproduced passes (rev2.1 recheck).
- The full m2_bitcheck_v29 v1.2 suite on gnc_dev6 is ALL PASS: A0, A1, G, K, V, N and RF; code unchanged during the run; 88 inputs hashed. It runs with the rev3 amendments off, so it does not test V2, L or V3 themselves; the v2.10 / v2.11 / v2.12 bit-checks do that.

5. LINE 194 FOLDS AND OLD VALUES
- (1) The E2 + 0.22 s hold is withdrawn. The comparator was re-flown as P6c using the reviewer's per-H table (r3_unpurged_classes.json c162cde0363c4917).
  - OLD VALUES: nrLO|none|rh220|h285 and rh250 (both bases) flew 0.22 / 0.25 s on the ~100 N guidance profile (m2_rev3_fly v2.0, sim6 v2.10-dev).
  - The P6 v1.0 P_total was computed from them. Both are kept as SUPERSEDED evidence.
- (2) The lit model 62.5 N x pcf_k is withdrawn.
  - OLD VALUES: the P4s lit arms (lit_k100, k875, k875_L400, k875_dt05, k875_dt10) and the r2v2 lit columns, marked WITHDRAWN_MODEL.
  - The 16.31 N margin is CONDITIONAL on CF-3.
- (6) R3-17 dip onset: applied as a DERIVED effect afterwards, not flown.
  - OLD VALUES: every flown A1 table (repro, P2, P2v35, P2opt, P3, P4s, P6, P6b, P6c, P8) and the duty-cycle record used the 60 g ASSUMED residual.

6. TESTS
- Bit-checks v2.10 / v2.11 / v2.12 (options off): ALL IDENTICAL.
- v2.12 functional:
  - v1.1 PASS.
  - v1.0 FAIL kept: the criterion was wrong because the guidance legitimately commands exactly 500 N on ascent and quantised 200 N records on landing. Part A was not re-flown.
- Full v2.9 suite on the rev3 code: ALL PASS.
- Repro against staged rev2: identical.
- RG-16 reproduction of the stored comparators: identical.
- Pins: all match.
- Duty-cycle re-flights reproduce their rows.
- The gzip re-evaluation changed references only.
- Staged MANIFEST: sha256sum -c OK.
- Not tested: hardware (none exists), SIL/HIL, canopy, measured vibration, the lit start history.

7. NOT RUN
- P7.
- P4c and the lit side.
- P2 at the v3.5.1 ledger and the 0.20 kg arm.
- P5 / RG-16 at 285 m.
- A gate-failure probability for P6 (canopy not modelled) and the Tp < 1.9 s class.
- The P8 re-plan.
- sigma_u(3 m) as a flight variable.
- 188 (7): TVC robustness and the bay-wall / stop item.
- G76 / PS10 / firmware-cap purge masses at 285 m.
- Electronics line 198 (6), the R2 counting start after a Pc loss: carried into P4c and the FSW record.

8. UNKNOWNS / TO-VERIFY (owner)
- Bleed valve pair mass, 2 x 0.30 kg ASSUMED (Mechanical / procurement datasheet).
- massprops v3.5.1 (Mechanical).
- Tank outlet geometry, OI-32 (Mechanical).
- v2.4b start-level lit history CSV and per-record classes incl. the 500 N profile (Combustion).
- CF-3 start lift (founders / Combustion).
- Injector body and feed soak-back heat (Combustion).
- IMU vibration spectrum (Electronics / Mechanical).
- Canopy dynamics and gate dispersion (GNC with Mechanical).
- Purge class for flows of 1.9-2.2 s and below 1.9 s (Combustion).
- K dropout length and throttle-map error band (GNC / Electronics; Combustion).
- sigma_u(3 m) pad procedure (founders).

9. NEXT CLOSURE
- Independent check of staging rev3, then the lead decides on the 11 proposals.
- Combustion v2.4b leads to the P4 lit side and the joint P4c confirmation; after that the lead sets pcf_tmax.
- massprops v3.5.1 and the valve datasheet lead to the P2 re-fly.
- The lead decides the trim for the v3.5-class mass.
- P7 before the SIL/HIL freeze.

10. PROCESS NOTES
- Disk: free space fell to about 518 MB while Mechanical's FEA runs grew. I warned main. After your cleanup, staging v1.2 includes the npz streams and refuses to copy if less than 200 MB would remain; about 9.25 GB was free afterwards.
- Nothing was installed. All processes were nice'd, one heavy process at a time, and stopped by PID only. No rev3 process is running and the monitors are stopped.
- Observation kept: the run6 strict-mode error texts still begin "run6 v2.9-dev:" (gnc_dev6/gncsim/run6.py lines 87, 107, 129). This is text only and was not changed, because the code is bit-checked as it stands.
- Incoming CHANGELOG line 198 (Electronics):
  - (1) The purge_bound wording in gnc.json v3.1 calls 2.5 s the ECU cap, but it is the scheduled flow; the firmware cap is 2.61 s, at which 77.7-83.6 g would be vented, above the 76 g allowance. This is listed as a v3.2 proposal.
  - (6) The R2 counting start after a Pc loss is noted in P4.
- One earlier thread reply was posted via hearthbot; nothing since.
