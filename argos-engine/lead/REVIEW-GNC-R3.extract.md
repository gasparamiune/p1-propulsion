REV-GNC-5: independent check of GNC staging rev3 (staging_v3.1/rev3)
I am not the author; I also did REV-GNC-3 and REV-GNC-4. I checked only the staged rev3 copy. Everything below is SIM (flown tables or streams) or DERIVED (my own statistics on them). Matching numbers show that a computation repeats; none of this is physical approval.

VERDICT: PUBLISHABLE WITH CORRECTIONS
- There is no BLOCKING finding.
- Every number I checked reproduces from the staged code, pins and tables. That covers P6, P6c, P2 (with and without the dip onset), P3, the P5 windowed budget, F7, F9 and F11.
- The bit-check claims hold on the parts I re-ran.
- On line 204:
  - (1), (2) and (4) follow from the evidence, with the precision corrections listed below.
  - (3): the apogee rule needs restating (MAJOR, RV5-01).
- On the 11 proposals: 5 are publishable as written, 6 are publishable with corrections, none is not publishable.

== (a) Reproduction (SIM tables, my own statistics) ==

Re-fly sample
Source: staged v2.12-dev tree (sim6 b0d9d8a0ded64e28, run6 a1df28f35a2576f1), staged pins, hub interfaces.

| Group | Arms | Result |
|---|---|---|
| Monte Carlo arms, 500 runs each | 16 | 3 byte-identical (flown on v2.12): rh300c200 on both bases, rh190c500 A1J_pc. 13 identical on every staged column: 8 flown on v2.10 (ant13 ×2, ant17, ant21, L400 ant21, L400 ant13, liqF, r2s_fo_cb) and 5 flown on v2.9 (e19\|G73\|L400, A1_pc pw\|G73, v35a h245, v35t h255, v35a h285). |
| P5 arms, 200 runs each, flown on v2.11 | 3 (A1asc dla05 V, B1floor dla05 Lhi, A1 nom V) | Byte-identical. |

- P equals the meta value in every arm.
- No file was opened outside the hub or my scratch area. For this I set GNC_FW_CONFIG to the hub config.h; it has the same hash, 0880af5a27880a5b, as the work-area file.

P6 late commit — the full table reproduces.

| Commit lead | Nominal start (A1_none / A1J_pc) | L400 start (A1_none / A1J_pc) |
|---|---|---|
| ant13 | 0.000 / 0.012 | 0 / 0 |
| ant17 | 0.758 / 0.780 | 0 / 0 |
| ant21 | 0.990 / 0.990 | 0.640 / 0.720 |
| ant25 | 0.996 / 0.990 | 0.786 / 0.854 |
| Decided | 0.992 / 0.990 | 0.940 / 0.952 |

- Realised lead p50: 1.31 / 1.71 / 2.11 / 2.52 / 2.87 s.
- E0 height p50: 22.3 / 31.2 / 40.1 / 41.8 / 44.7 m.
- ant13 failures: td_vz p50 −12.1 / −12.6 m/s with the nominal start, −23.7 m/s with L400; mostly tipovers.
- Gate-delay tolerance:
  - Minimum slack: 2.965 s (A1_none, A1J_none) and 3.121 s (A1J_pc, A1_pc).
  - D_crit minimum: 3.465 s (2.4 s), 3.765 s (2.1 s), 3.965 s (1.9 s), 4.565 s (1.3 s).
  - The 2.90 s bound for non-fired runs is valid: E0 − commit = 2.900 exactly in every non-fired run.
  - Minimum fired lead: 2.65 s.

P by realised lead, pooled over the ant arms and both bases (DERIVED):

| Lead (s) | Nominal start | L400 start |
|---|---|---|
| 2.4–2.9 | 0.994 | 0.825 |
| 2.1–2.4 | 0.993 (n 742) | 0.764 |
| 1.9–2.1 | 0.982 (n 280) | 0.454 |
| 1.7–1.9 | 0.835 | 0 |
| 1.5–1.7 | 0.604 | 0 |
| 1.3–1.5 | 0.009 | 0 |
| < 1.3 | 0 | 0 |

P6c comparator
- Per-base P and the paired results against release at E2 reproduce exactly:
  - rh300c200: −4/+0 and −7/+2;
  - rh400c200 (A1J_pc): −9/+0, p 0.0039;
  - rh190c500 (A1J_pc): −10/+0, p 0.00195;
  - rh300: −1/+1.
- Profile times and truth thrust under the profile also reproduce.
- P_total = P_success × P_GNC (minimum over bases):
  - LO: lin0.0 0.392, lin1.0 0.461; HI: 0 and 0.036; worst states 0.
  - With rh400c200: LO 0.389 / 0.457.
- Combustion hold table for the 200 N ramp at H ≥ 0.30 s: residual 0 in all four groups (mean, max and conservative).

P2 mass options — reproduce.
- At 60 g:
  - v35a: liq 0.940 / 0.942, pw 0.950 / 0.954; pooled −56/+9, p 2.05e-9.
  - v35t pooled: −30/+10, p 0.00222.
  - Option sets without a significant loss: as stated by the author. liq v35t h265 loses at p 0.029 (non-monotone).
  - kd70 against v35a h285: +19/−6, p 0.0146. ht5 loses everywhere.
- With the dip onset applied to both arms:
  - At 69 g, liq v35t loses h275 and kd70.
  - At 80 g, pw v35a loses h255.
  - What remains: v35a 245 m; v35t ≤ 255 m (liq) / ≤ 265 m (pw).

P3 coverage at 285 m — reproduces.
- liq|G73 on the four bases: 0.990 / 0.986 / 0.990 / 0.990.
- 285 m against 300 m, liq|G73 on all four bases: −12/+29, p 0.0115. It still gains with the 80 g onset (−10/+26, p 0.011). Exhaustions fall from 8 to 0.
- e19|G73|L400: 0.940 / 0.952, −43/+3, p 4.62e-10.
- Duty-cycle p99 pick (numpy percentile, unrounded): run 380 at 8.375 s (A1_none) and run 472 at 8.189 s (A1J_pc). The record file hashes match.

P5
- My own windowed-budget code on the staged streams reproduces all 44 strict W = 500 ms totals (4 cases × 11 noise variants) exactly, with the same frame counts:

  | Case | Strict total |
  |---|---|
  | A1 comp | 2.9727 % (passes by 0.0124 pp) |
  | A1 non-comp | 4.0147 % (FAIL) |
  | B1 comp | 2.0831 % |
  | B1 non-comp | 2.3853 % |

  The A1 terms come from the staged rev2 rg16_fct_terms_v2.json; the B1 terms from the staged rev1 mest_budget_v1.json.
- Δv p50: 16.34–18.69 m/s.
- A1 apex p99: 358.0 m (V) / 435.6 m (Lhi); maximum 463.2 m.

Also reproduced
- F7 (mode 3, 0.8 s window):
  - inside W10 < 6 m/s: 31.861 N, margin +5.298 N;
  - all winds: 39.452 N, margin −2.292 N, 4/2072 runs above;
  - ×1.3 sensitivity inside W10 < 6: 35.31 N.
- F9:
  - liqF 0.972 / 0.978, −17/+4, p 0.0072;
  - pwF 0.924 / 0.932, −64/+3, p 6.8e-16.

== (b) Bit-checks ==

v2.12 Part A (options off), re-run on the v2.12 side
- My stream is byte-identical to the staged bc_v212.npz (db1c3fc7212209fe), all 26 arrays.
- I compared it with my own code against the staged v2.11 stream (da734c786d7c852c): all 12 of 12 cases are identical on the 200 common results and 76 common record columns. The only additions are the v2.12 results pv3_rhp_s and pv3_Frhp_max.

v2.12 Part B (functional), v1.1
- ALL PASS.
- My output JSON is byte-identical to the staged one (29cdaad8abdf5649).

v2.9 suite v1.2, parts A0, G, K, V and RF re-run on v2.12
- ALL PASS.
- Part results are identical to the staged ones, except for the reference path strings; the reference hashes are identical.
- Not re-run:
  - A1 (it needs the rev1 simulator subprocess);
  - N (it needs iface_v3c, which is not in the hub).

v2.10/v2.11 identical when off
- Not re-flown directly, because those trees are not staged; only their patch scripts are.
- It is supported indirectly by the re-fly sample above: v2.12 reproduces the v2.9-, v2.10- and v2.11-flown tables.

== (c) Old values (line 194) ==

In rev3_results.json:
- The rh220/rh250 arms carry status SUPERSEDED.
- The lit statistics carry WITHDRAWN_MODEL keys.
- The 60 g basis is tagged (residual_basis), and the dip adjustment is given beside it.
- F3 and proposal [2] use none of the withdrawn holds.
- No live proposal relies on an unmarked old value, with the exceptions in RV5-06 (proposal [3] and the P4 gap/T_mid keys).

== (d) Line 204 decisions ==

(1) Follows from the evidence.
- The ~2.1 s threshold separates landings for the nominal start: 0.993 at 2.1–2.4 s, 0.982 at 1.9–2.1 s, 0.835 at 1.7–1.9 s.
- With L400 it does not separate them (0.76–0.83), which the decision states.
- "Never worse than no relight" holds in landing-P terms only; no hazard comparison exists.
- A predictor failure (commit at the plain trigger) is a separate fault class that the gate-delay tolerance does not cover.
- For the D_crit pairing, see RV5-04.

(2) NOT ADOPTED follows from the evidence, and the pooled P cost (RV5-03) strengthens it.
- The expected gain is at most 0.46 pp per flight at a 1 % gate-fault probability, in LO with the best convention; it is at most 0.036 pp in HI. Both are below the Monte Carlo resolution.
- The revisit rule is acceptable once it carries the refinements in RV5-08.

(3) The band statement reproduces for the 69–80 g onset. The rule as worded does not follow (RV5-01).
- 250 m was consistent with the line-204 bracket (v35t + 0.20 kg = +1.068 kg).
- Line 206 changes that (RV5-02). Line 206 was appended after my input set; the first 204 lines are unchanged (hash 60190e33f21480b6).

(4) F6–F11 are recorded correctly as found, with the nuances in RV5-05, RV5-09 and RV5-10. Marking the old values SUPERSEDED is right.

== RANKED FINDINGS ==

RV5-01 — MAJOR
Gates: A1 apogee decision (204 (3)); rev4 P2 re-fly design; v3.2 if the rule text is published.
The apogee rule tests only for a significant loss. It has no non-inferiority margin, no monotonicity condition and no fixed onset.
- Non-monotone case: at the 62 g onset, which is inside the R3-17 bracket, liq v35t shows no significant loss at 275 m (−19/+9, p 0.087) but loses at 265 m (−23/+9, p 0.020). The rule as worded would pick 275 m.
- Undetected deficit: at the bands that pass, the one-sided 95 % upper bound on the pooled P deficit is 0.8–1.9 pp (DERIVED, normal approximation):
  - v35a h245: 1.5–1.9 pp (liq), 1.3–1.7 pp (pw);
  - v35t h255 liq: 0.8–1.0 pp;
  - v35t h265 pw: 1.4–1.7 pp.
- Sweep floor: the flown sweep ends at 245 m, and that is the only band where v35a passes.

Correction:
- Choose the highest band h such that h and every lower flown band show no significant pooled loss at the upper onset of the bracket (80 g), and the one-sided 95 % upper deficit bound is ≤ δ. The lead sets δ.
- Extend the sweep below 245 m.
- Fly the candidate bands on all four bases.

RV5-02 — MINOR
Gates: the planning value given to other teams; the A1 apogee decision.
- Line 206 states the as-built v3.5.1 as about v35a + 0.20 kg, i.e. +1.37 kg. That is outside the flown brackets.
- The nearest flown arm, v35a (0.20 kg lighter), passes only at 245 m, the lowest band flown.
- No flown evidence supports 250 m at that mass.
- Correction: state "≤ 245 m, TO-VERIFY by rev4 P2 on v3.5.1", or flag 250 m as above the flown evidence.

RV5-03 — MINOR
Gate: v3.2 proposal [2].
F3 and proposal [2] give per-base results only. Pooled over the two main bases (the 204 (3) convention), all three ECU-hold arms lose against release at E2:

| Arm | Pooled P vs release at E2 | Discordant pairs | p |
|---|---|---|---|
| rh300c200 | 0.983 vs 0.992 | −11/+2 | 0.0225 (LOSES) |
| rh400c200 | 0.979 vs 0.992 | −13/+0 | 2.4e-4 |
| rh190c500 | 0.977 vs 0.992 | −15/+0 | 6.1e-5 |

rh190c500 also loses against liq|none: −12/+2, p 0.013.

RV5-04 — MINOR
Gate: v3.2 proposal [1].
- Proposal [1] still says the band is 1.3–1.7 s. Line 204 (1) says below about 2.1 s. Proposal [1] must follow the decision.
- 204 (1) and [1] should give D_crit for each threshold:

  | Threshold | D_crit (A1_none, A1J_none) |
  |---|---|
  | 2.4 s | 3.465 s |
  | 2.1 s | 3.765 s |
  | 1.9 s | 3.965 s |
  | 1.3 s | 4.565 s |

  Add 0.156 s for A1J_pc and A1_pc. The 3.465 s quoted in 204 (1) belongs to the 2.4 s threshold; it is conservative for 2.1 s.
- Add the L400 lead bins.

RV5-05 — MINOR
Gate: v3.2 proposal [4] (launch-commit evidence).
The e19|G73|L400 loss is not a trim effect and lies almost entirely outside the hard launch-commit rule.
- 40 of the 43 lost pairs are at W10 ≥ 6 m/s (−40/+3, p 3.0e-9).
- Inside W10 < 6 m/s: −3/+0, p 0.25 (n 728, low power).
- Against the same arm at 300 m: −25/+24, p 1. The loss is already in the rev2 data (line 180).
- The record should say this and give the P with the dip onset applied.

RV5-06 — MINOR
Gate: v3.2 proposals [0], [3] and [6].
The withdrawn-value markers exist only in rev3_results.json.
- The staged evaluation files carry withdrawn values with no marker at all:
  - p6_late_commit.json v1.0 (P_total from rh220/rh250);
  - rev3_fly.json;
  - r2v2_eval.json (lit columns);
  - reserve_dip.json;
  - the table meta files of the rh220/rh250/lit_k* arms.
- In P4_R2v2.thresholds, gap_N and T_mid_N (16 entries) are computed from the WITHDRAWN_MODEL lit minima but are not marked.
- Proposal [3] keeps the 60 g-basis bands without the SUPERSEDED label that 204 (4) gives the 60 g residual.

RV5-07 — MINOR
Gate: v3.2 purge_bound wording.
- Proposal [9] predates line 203 (3). The ECU cap is now ≤ 2.55 s (75.9 g on the Combustion basis), and GNC carries about 80 g as a sensitivity.
- [9] still presents the v2.10 cap of 2.61 s as current.
- The ~80 g case has not been flown at 285 m.

RV5-08 — NOTE
Gate: any revisit of 204 (2).
- At H = 0.30 s on the 200 N ramp, lin1.0|LO is 0.25 ms short of the frame rule: latest trip 0.2902 s + 10 ms > 0.30 s. The per-record classification, however, gives a residual of 0.
- H = 0.19 s at 500 N has a margin of 2.5–2.7 ms.
- The P_success labelled "ramp" is the best case over both conventions and both modes, so it is an upper bound.
- The revisit rule should require an ECU timing margin and state its trigger as an expected gain (q × P_total).

RV5-09 — NOTE
Gates: P4c; the pcf_tmax decision.
- F7 and 204 (4) quote only the 0.8 s window.
- At the current pcf_tmax of 0.5 s (line 181 (4)), mode 3 gives:
  - all winds: 34.88 N, margin +2.28 N, 0/2072 runs above;
  - inside W10 < 6 m/s: 31.18 N, margin +5.98 N.
- Carry both windows.

RV5-10 — NOTE
Gate: FC_THRUST arming.
- "AR(1) fails everywhere" in 204 (4) is true only for the same-RMS variants.
- With the frame-level RMS equal to the white model's (the _fr variants):
  - B1 comp passes at all three correlation times;
  - A1 comp passes at 5 ms by 0.0016 pp.
- F8's own wording is accurate.
- The B1 |b_sys median| comes from fct2_B1_H_cal(_comp).json, which is not in the hub (TO-VERIFY, ≤ 0.044 pp). I took the author's value.

RV5-11 — NOTE (reproducibility closure)
- The v2.10 and v2.11 trees are not staged. The v2.12 tree covers the arms I sampled.
- The default run chain reads a work-area config.h. The hub copy has the same hash.
- iface_v3c, needed by suite part N, is not in the hub.

RV5-12 — NOTE
- The v2.12 functional criterion was relaxed after the v1.0 failure. The v1.0 FAIL is kept (d1165a5ebed4fd0f), and the change is justified with a probe.
- My re-run of v1.1 is identical.

RV5-13 — NOTE
- P5 was flown at the 300 m comparator configuration.
- Its apex figures are therefore conservative for the 285 m and 250 m trims.

== (e) Proposals ==

| # | Verdict | Corrections |
|---|---|---|
| [0] | Publishable with corrections | Fold in RV5-03, 05, 06, 09 and 10 |
| [1] | Publishable with corrections | RV5-04 |
| [2] | Publishable with corrections | RV5-03 and RV5-08; add NOT ADOPTED per 204 (2) |
| [3] | Publishable with corrections | RV5-01 and RV5-06; RV5-02 for context |
| [4] | Publishable with corrections | RV5-05 |
| [5] | Publishable as written | It is a record, and conditional on the 285 m trim |
| [6] | Publishable with corrections | RV5-06 (gap_N, T_mid_N) and RV5-09 |
| [7] | Publishable as written | RV5-10 as a NOTE |
| [8] | Publishable as written | — |
| [9] | Publishable with corrections | RV5-07 |
| [10] | Publishable as written | — |

== CHECKPOINT ==

Claim
- The rev3 numbers reproduce from the staged code, pins, tables and streams, and the bit-checks re-run as stated (SIM/DERIVED).
- Line 204 (1), (2) and (4) are supported. 204 (3) needs restating, and the 250 m value needs revisiting after line 206.
- 6 of the 11 proposals need corrections.
- No physical approval.

Configuration
- MANIFEST_rev3 79c2c8cd5d10e3c4: 487/487 OK, both at the start and at hand-back.
- Staged v2.12-dev tree (scratch copy), with only path redirects (logged).
- Pins: pins_rev3 23f3b29b29b3f476 and pins_rev3_v35a c77a56322ece7124 (52/52 entries resolved to hub copies).
- Interfaces: iface_v3d (rev2 staged) and iface_v35a (rev3 staged).
- Seed 101; N = 500 (200 for P5).
- Run settings: /opt/engine-venv python -I, NUMBA_NUM_THREADS=1, nice 10, at most 2 processes, killed by PID only.

Sources
- rev3_results.json e0f6e7611fe523b5
- REPORT-GNC-rev3.md 4726faa1ce2ab39d
- gnc.json 4f3209323b0e0ed4
- CHANGELOG lines 1–204: 60190e33f21480b6. The file now has 206 lines (37d45a7f44977079); lines 205–206 were read as context.
- REVIEW-COMBUSTION-R3.md a786101f28d45d6f
- r3_unpurged_classes.json c162cde0363c4917
- rg16_fct_terms_v2.json 2ae2a6eedd90249a
- mest_budget_v1.json 05a2fb5728e73be7

Files (hub reviews/gnc/rev3/)
MANIFEST_REV-GNC-5.sha256 ce04a68c0539b7a1: 71 files, 9.7 MB, sha256sum -c 71/71 OK.

| File | sha256/16 |
|---|---|
| results/v05_p6.json | 2ca68e0c258734cc |
| results/v06_p6c.json | a093c3458cc4b6f8 |
| results/v07_p2.json | 7fd1c41a481fa7c1 |
| results/v08_p3.json | 4e2d300caab36447 |
| results/v09_p5.json | e2a0878f54054a02 |
| results/v10_bc_compare.json | 2c3671105512e3b1 |
| results/bitcheck_v212_func_rv.json | 29cdaad8abdf5649 |
| results/bitcheck_v29_parts_A0_G_K_V_RF_rv.json | 3c903e37ede0e687 |
| results/v11_oldvalues.json | 1e358d60c1db6bfb |
| results/v12_f7.json | a3039ff6b722bd62 |
| results/v13_p8.json | 8ac6a1ea3ba53dba |
| results/refly_v03_*.json | 6a5d13a933e6ff1a, b897b98893b189c2, fe1ce5891d67ab28 |
| results/p5refly_v14_*.json | 38c0128af7724d06 |
| scripts/rv5lib.py | c2c1d2178c27faa1 |
| logs/v04_refly_batch.out | cd49d71d01d5aa8e |

The folder also holds the 16 re-flown tables in tables/refly and the 3 P5 tables in tables/p5_refly, all gzipped.

Tests
- Manifest and input hash checks.
- Pin resolution.
- 19 arms re-flown (16 Monte Carlo + 3 P5).
- v2.12 bit-check Part A (v2.12 side) and Part B.
- v2.9 suite parts A0, G, K, V and RF.
- My own statistics for P6, P6c, P2, P3, P5, F7 and P9.
- Scan for withdrawn values.

Unknowns
- Canopy and gate-opening dynamics, and the gate-fault probability.
- A measured IMU spectrum.
- OI-32 outlet geometry and the true dip onset.
- The v3.5.1 ledger and the real valve mass (not flown).
- Per-record P_success at 500 N.
- The LO/HI unpurged start (CF-4/T4).
- The v2.4b lit history.
- ECU timing margins.
- The source file for the B1 b_sys median.
- Suite parts A1 and N (not re-run).
- The F10 probe (not checked numerically).

Next closure
1. The author corrects proposals [0]–[4], [6] and [9], and adds markers to the evaluation files.
2. The lead restates 204 (3) (δ, monotonicity, fixed onset) before rev4 P2 on v3.5.1. That re-fly extends the sweep below 245 m and flies the candidate bands on four bases.
3. The 250 m planning value is reviewed against line 206.
4. A delta re-check of the corrected proposals before v3.2 is published.
5. The lead registers the verdict in supervision.json; I did not edit it.

SIM/DERIVED only; not physical approval.
