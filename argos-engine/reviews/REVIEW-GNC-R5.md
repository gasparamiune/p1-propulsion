# REVIEW-GNC-R5 (REV-GNC-7)

Independent delta re-check of GNC rev4b, the gnc.json v3.2 candidate, the ENG-11 FE-plant re-run and the CAD v3.5.2 R3 stiffness band, returned by the reviewer 2026-10-21T10:30:29Z (date -u); its interims went to the lead at 09:09:20Z and 09:25:51Z. Saved here by the lead on 2026-10-21T10:39:38Z (date -u), verbatim from the reviewer's final message: the harness does not let a subagent write a report file, so the handback text is the review. Reviewer artefacts: `reviews/gnc/rev4b/` (`MANIFEST_REV-GNC-7.sha256` e04257acba555551, 94 entries, verified by the lead 94/94 OK at 10:38:50Z). Reviewed set: the candidate `01-systems-gnc/staging_v3.1/rev4b/v32/gnc_v3.2_rev4b.json` (43d58c4aff164b86) against `interfaces/gnc.json` v3.1 (4f3209323b0e0ed4), with `01-systems-gnc/staging_v3.1/rev4b/DATASHEET-INPUTS-GNC.md` (9aacdefaaa0df250). Authoritative corrections: `reviews/gnc/rev4b/data/b/rv7_v32_corrections.json` (f7c0c6051efd5a08); reviewer trial `data/b/gnc_v3.2_rv7_trial.json` (fea33eacdd8a7d56). Lead disposition: CHANGELOG line 258. A verdict is not physical approval: no hardware exists.

```text
BEGIN REVIEW-GNC-R5

REVIEW-GNC-R5: REV-GNC-7, an independent delta re-check of GNC rev4b, the gnc.json v3.2 candidate, the ENG-11 FE-plant re-run and the v3.5.2 R3 stiffness band
- Reviewer: REV-GNC-7.
- Brief received 2026-10-21T08:41:22Z. Returned 2026-10-21T10:30:29Z (date -u, run just before this handback).
- Nothing in this review is physical approval. Each number carries its evidence tag.

Inputs read (sha256/16; H = /home/claude/work/shared-fallback/engine)

| Input | sha256/16 | Note |
|---|---|---|
| candidate 01-systems-gnc/staging_v3.1/rev4b/v32/gnc_v3.2_rev4b.json | 43d58c4aff164b86 | |
| baseline interfaces/gnc.json v3.1 | 4f3209323b0e0ed4 | |
| 01-systems-gnc/staging_v3.1/rev4b/DATASHEET-INPUTS-GNC.md | 9aacdefaaa0df250 | |
| eng11fe_summary.json (rev4b/eng11_fe/) | 4d0f340d965ee5cc | |
| m2_eng11_fe.py v1.0 | fab0f05eb87d8e61 | unchanged |
| m2_eng11.py v1.1 | aaad9a07a0551b9b | my copy c5fdd60625343431 redirects only SP and MECH_HUB to a read-only snapshot (scripts/m2_eng11_redirect.diff) |
| 04-fea/assembly3d_v352/results/v352/k_table_r3_v352.json | f3c7cfbcfb98bcd7 | |
| combustion.json v2.4c | 661db0a593462382 | |
| interfaces/electronics.json v4 | 11f7896ad0d0613b | |
| S17v2_r2v2_sweep.json | 404a19d7064b336f | |
| DC-D v2 CSV | 9c5d7cf391d8297b | |
| p2_rev4.json | 68cf1f643effd5b9 | |
| V5c gimbal_k_summary | 82a737caa138259a | |
| k_cone_c71 | bfb9b56ed85b6a2f | |
| k_stop_c71 | fd9ca16b0b3d2304 | |
| t10_postcheck v2 | d51d079d81d64766 | |
| mechanical.json snapshot | e4d3e7c9df529171 | v2.1; the hub now holds v2.3 55397a9b8ddb59be; gear_ratio_n is 4.8 in both, and it is the only value the loop reads |

=====================================================================
1. VERDICT: PUBLISHABLE WITH CORRECTIONS
=====================================================================
- Findings: 0 BLOCKING, 4 MAJOR (RV7-01 to RV7-04), 5 MINOR (RV7-05 to RV7-09), 3 NOTE (RV7-10 to RV7-12).
- The corrections are 34 gnc.json operations and 7 DATASHEET-INPUTS-GNC.md operations.
  - The machine-readable copy is the authoritative one: reviews/gnc/rev4b/data/b/rv7_v32_corrections.json (f7c0c6051efd5a08). For each op it gives op, path, old and new.
  - Appendices A and B reproduce the same texts.
- Applying all 34 ops to the candidate gives my trial, data/b/gnc_v3.2_rv7_trial.json (fea33eacdd8a7d56).
  - The trial passes t10_postcheck v3 --publication --rv7: exit 0, 0 critical unmarked, 0 required failed.
  - The candidate as staged gives exit 1.
- The trial only shows that the corrections are complete and consistent. The lead publishes v3.2 and sets its version, status and supersedes fields.
- Publish only with RV7-01 to RV7-04 applied.
- The ENG-11 datasheet sentence becomes design-to 100-110 N m/rad, not 100-120. Only 100 N m/rad passes at both ends of the R3 band.

=====================================================================
2. FINDINGS
=====================================================================
**RV7-01 MAJOR ((d), (e)). The ENG-11 window is refuted on CAD v3.5.2.**
- Two texts do not hold on the CAD v3.5.2 R3 plant:
  - datasheet row 8, "Design-to 100-120 N m/rad (V5c ∩ CAD v3.5.1 FE)";
  - the candidate's ENG-11 text, "100-130 on V5c, FE re-run not folded".
- What the R3 plant gives at J 1.6e-3 (both axes):
  - pose-wise: <= 90-110;
  - band maximum: <= 90-100;
  - band minimum: <= 90-115 and 150->= 160.
- Inside 100-120, 115 and 120 fail pose-wise on beta, and 105-120 fail at the band maximum on alpha.
- Corrections: ops [0]-[3] and [5]; DS row 8 (Appendix B).
- Interim sent 09:09:20Z.

**RV7-02 MAJOR ((h)(i), (h)(vi), S17 v2.11, noise budget, OI-FC-PC-BRANCH). The S17 v2.11 result is not folded.**
- The candidate still says "Electronics v2.11 ... confirms it or returns it".
- It carries none of the conditions under which S17 v2.11 confirmed pcf_tmax 0.8 s:
  - hold;
  - flush;
  - photodiode view or re-taken reference;
  - FC Pc branch;
  - noise budget;
  - cold flow × 1.3;
  - W10 < 6 only.
- Corrections: ops [6]-[8], [10]-[15], [17]-[21], [25], [27]; DS row 11f and the carried pcf_tmax line.
- Interim sent 09:25:51Z.

**RV7-03 MAJOR ((d)). The K band is missing.**
- The candidate does not carry the R3 K band = range_over_posted_R3_poses (lead 250 (6)). t10 R10 reports NO.
- Correction: op [4] (the band text, section 3).

**RV7-04 MAJOR ((h)(ii)). The final purge is not folded, and the warm end at Cd 0.80 fails line 208.**
- The candidate carries the superseded 2.55 s both-open cap (v32_items_rev4b[9], purge_bound.note_rev4b and reference line 203 (3)).
- The final purge of 256 (2) / 257 (2) is not folded.
- At 297.15 K and Cd 0.80 [ESTIMATE], the fixed 2.43 s schedule vents 85.5 g (85.8 g at the cap). The line-208 test fails there: UB95 1.206 pp on liquid.
- I checked the lead's remedy, 257 (2) condition (d), in section 5 (ii). It holds, with two additions.
- Corrections: ops [24] and [28]-[31].
- Interim sent 09:25:51Z.

**RV7-05 MINOR ((h)(iii)). The lost-relight mission outcome (253 (7)(iv)) is not stated.** Corrections: ops [9] and [26].

**RV7-06 MINOR ((h)(iv)). The R3-01 open item is missing** (REV-ELEC-3 MAJOR; 253 (7)(iii) HELD). Correction: op [23].

**RV7-07 MINOR ((h)(v), line 230 (5)). The R4-03 lit corners at W 0.8 s and OI-FMIN-LIT are missing.** Corrections: op [22], plus the lit-side text in op [8].

**RV7-08 MINOR ((b)). One C06a hit, and the status does not record the fold.**
- C06a hits once, at checkpoint_rev4b/unknowns/4.
- The status carries no record of the REV-GNC-7 fold.
- Corrections: ops [16] and [33].

**RV7-09 MINOR ((f), (e)). Datasheet rows need correcting:**
- row 5 (basis paragraph);
- row 8: sentence, evidence, and the source attribution, which belongs to A10 and not A03;
- row 11b;
- row 11f;
- the carried-unchanged pcf_tmax line.
- Correction: DS ops 1-7.

**RV7-10 NOTE ((c)). n48 judgement.** See section 4.

**RV7-11 NOTE ((g)).**
- The post_k servo factor (RM2-05) is consistent with the series model and with 234 (5) / (6).
- The ca2c fold does not touch the loop inputs.
- No ops.

**RV7-12 NOTE (T4 / N-07). No GNC objective needs the DC-D v2 duty as one firing in Combustion's T4.** Correction: op [32].

=====================================================================
3. (d) THE R3 K BAND AND THE ENG-07d LOOP CHECK
=====================================================================
**Method [DERIVED, linear; K_s, J, bending and damping ASSUMED]**
- Tooling: the author's, unchanged. m2_eng11_fe v1.0 runs on m2_eng11 v1.1; my driver is scripts/rv7_eng11_r3.py v1.0 (0ab8c677bcfdf7a4).
- Loop model: f = sqrt(K_tot / (I_piv + J g)) / 2π, with K_tot = 1 / (1/S + 1/(K_s g)).
- ENG-07d criterion: stable, upper GM >= 6 dB at every floor20 corner, continuous cone + stop envelope.
- One fixed ECU notch: Q 1 / -12 dB at e 0.95 / 1 / 1.05 × the R3 centre landing mode.
- Damping and bending: zeta 0.02 / 0.05 / 0.10; first bending 24.3 Hz full / 25.64 Hz landing (ASSUMED).
- K_s grid: 90-160 step 5, so window edges are ±5 N m/rad.
- J: 0.76e-3, 1.6e-3 and 2.7e-3 kg m², the values ENG-11 uses, with cons kinematics.

**Plants**
- "Pose-wise": S = FE_coupled R3 at each of the 17 poses; g = V5c on the 9 cone poses and CAD kinematics at the 8 stops (the author's choice).
- "Band max / min":
  - S is set to the band value at every pose; g stays per pose; the notch stays on the R3 centre pose.
  - Band values used: alpha 7293.95 / 9337.32 and beta 3971.84 / 7172.21 N m/rad. These are the outer envelope of the FE_coupled and FE_diagonal ranges, which differ by at most 0.24 N m/rad (0.003 %), so one run covers both quantities.

**K quantities the loop uses**
- S (FE coupled), at both band ends.
- The k_s58 / k_s174 columns are not loop inputs (the loop forms the servo in series itself). I checked the loop at K_s 58 and 174.
- g: I also ran R3G_JC, with g = the R3-implied servo factor. It gives the same windows as V5c/kinematics g.
- Envelope: I also ran R3C_JC, on the cone poses only.

**Windows (K_s in N m/rad passing ENG-07d; "both" = both axes)**

| J (kg m²) | Plant | Both | Alpha | Beta |
|---|---|---|---|---|
| 1.6e-3 | pose-wise | <= 90-110 | <= 90-115, 140->= 160 | <= 90-110 |
| 1.6e-3 | band max | <= 90-100 | <= 90-100, 135->= 160 | <= 90-110 |
| 1.6e-3 | band min | <= 90-115, 150->= 160 | <= 90-115, 150->= 160 | <= 90->= 160 |
| 1.6e-3 | R3G (R3-implied g) | <= 90-110 | <= 90-115, 140->= 160 | <= 90-110 |
| 1.6e-3 | R3C (cone only) | <= 90-115 | <= 90-120, 140->= 160 | <= 90-115 |
| 0.76e-3 | pose-wise | 130->= 160 | 105->= 160 | 130->= 160 |
| 0.76e-3 | band max | 130->= 160 | 105->= 160 | 130->= 160 |
| 0.76e-3 | band min | 130->= 160 | 110->= 160 | <= 90-105, 130->= 160 |
| 2.7e-3 | pose-wise | 120->= 160 | 100->= 160 | 120->= 160 |
| 2.7e-3 | band max | 110->= 160 | 100->= 160 | 110->= 160 |
| 2.7e-3 | band min | 120->= 160 | 100->= 160 | 120->= 160 |

- All three J together: pose-wise none; band maximum none; band minimum 150->= 160.
- R3C (cone only): the stops cost 5 N m/rad at J 1.6e-3.

**Margins: worst upper GM over all floor20 corners at J 1.6e-3 (dB), alpha / beta**

| Plant | K_s 100 | K_s 105 | K_s 110 |
|---|---|---|---|
| pose-wise | 6.223 / 6.098 | 6.252 / 6.130 | 6.280 / 6.155 |
| band max | 6.229 / 6.134 | alpha FAIL 5.884 (23.941 Hz) / 6.166 | alpha FAIL 5.911 (23.981 Hz) / 6.191 |
| band min | 6.219 / 6.098 | 6.248 / 6.130 | 6.276 / 6.155 |

- Pose-wise, the worst GM inside 100-110 is 6.098-6.155 dB (beta).
- Upper edge at J 1.6e-3, pose-wise:
  - alpha 120 fails at 5.861 dB (24.077 Hz);
  - beta 115 fails at 5.941 dB (23.901 Hz).
- Every J 1.6e-3 failing corner, pose-wise and at both band ends, is the same condition:
  - full tank, 500 N, fast actuator, no aero;
  - zeta 0.02, notch e 0.95;
  - frequencies 23.900-24.550 Hz.
  This is the full-tank rocking mode coinciding with the first bending.
- J 0.76e-3, pose-wise:
  - alpha fails 90-100: 5.910 / 5.920 / 5.502 dB at 24.074 / 24.142 / 24.367 Hz.
  - beta fails 90-125. At 125 the displayed GM is 6.000, but it is below 6 dB (24.461 Hz, max-q finless corner). The first pass is 130, at 6.205.
  - At the band maximum, alpha 100 fails at 24.684 Hz.
- J 2.7e-3, pose-wise:
  - alpha fails 90-95: 5.956 / 5.994 dB at 18.575 / 18.978 Hz.
  - beta fails 90-115: 5.826-5.988 dB at 16.301-17.752 Hz. The first pass is 120, at 6.013.
  - All of these are the max-q corner: full tank, 500 N, worst actuator, fins, zeta 0.10.
  - Over all J 2.7e-3 plants the failures span 16.30-19.22 Hz.
  - At the band maximum, beta 110 passes at 6.005.
- At K_s 58 / 174 (pose-wise, J 1.6e-3):
  - K_s 58: alpha fails at 5.840 dB (17.492 Hz, max-q with fins); beta fails at 5.935 dB (15.202 Hz, no aero). Both are worst-actuator corners at zeta 0.10.
  - K_s 174: alpha passes at 6.519; beta fails at 5.964 dB (24.341 Hz, bending coincidence).
- Why R3 moves the window:
  - The R3 plant is stiffer than the RM2-05-corrected v3.5.1 plant: S_R3 / S_v351 is 1.089-1.150 (alpha) and 1.022-1.098 (beta) across the poses [DERIVED].
  - This puts the rocking mode into the full-tank bending band about 5-10 N m/rad lower in K_s.

**The band text** is op [4], the new key requirements.gimbal.tvc_actuator.ENG-11_servo_output_stiffness.k_band_r3_v352, given verbatim in Appendix A.
- Values in N m/rad, with min and max poses:

  | Quantity | Alpha | Beta |
  |---|---|---|
  | FE_coupled | 7293.95 (stop000) – 9337.08 (stop180) | 3971.84 (stop180) – 7172.12 (stop000) |
  | FE_diagonal | 7294.05 – 9337.32 | 3971.94 – 7172.21 |
  | k_s58 coupled | 1149.93 (neutral) – 1426.19 (stop000) | 790.77 (stop180) – 1799.09 (stop000) |
  | k_s58 diagonal | 1149.93 – 1520.79 (stop315) | 790.77 – 1799.09 |
  | k_s174 coupled | 2697.48 – 3075.77 | 1696.7 – 3594.13 |
  | k_s174 diagonal | 2697.48 – 3165.81 | 1696.7 – 3594.14 |

- Tags:
  - SIM: FE unit steps on the v3.5.2 R3 pose runs, FEA3D.
  - DERIVED: servo in series; K_s 58 / 174 ASSUMED, TO-VERIFY at B-TVC-1.
  - Loop check: DERIVED (linear).
  - Not physical approval.
- Beta sign trend (information): the fraction of the stop045 delta per pose is
  - 0.8799-1.2085 for beta > 0;
  - 0.5159-0.9896 for beta = 0;
  - 0.1716-0.8207 for beta < 0.

  It follows the sign of beta, and the RM2-05 band built from the stop045 delta does not bound every pose.

=====================================================================
4. (c) REPRODUCTION, "NO K_s FOR ALL THREE J", AND n48
=====================================================================
**Reproduction (re-run with the author's tooling, compared row by row)**
- Check run: identical in every block (c1_fe_table, c2_kinematics, c3_reproduce_rev_gnc6_v05B, c4_two_mass_limits, c5_centre_full_Hz, passed). Only t_s differs in c3. Input shas are the same, apart from the m2_eng11 redirect.
- Full rows: A01, A03, A08, B01 and C01 match 30 of 30 rows each.
- Edge rows only (time box):
  - A02: 8 of 8 rows identical (K_s 105, 110, 125, 130, both axes).
  - B07: 12 of 12 rows identical (K_s 90, 95, 115, 120, 145, 150).
- Windows reproduced:
  - A01: <= 90-120.
  - A03: 120->= 160.
  - A08: <= 90-120.
  - B01: none (alpha <= 90-110, 150->= 160; beta none).
  - C01: none (alpha 135->= 160; beta none).
  - A02 edges: among the K_s tested, only 130 passes, consistent with the author's 130->= 160.
  - B07 edges: among the K_s tested, only 150 passes, consistent with the author's 150->= 160.

**"No K_s for all three J": CONFIRMED, and the cause is confirmed**
- Where it holds: pose-wise on R3, at the R3 band maximum, and on CAD v3.5.1 rigid T_REF (A01 <= 90-120 against A02 130->= 160).
- It depends on the plant. At the R3 band minimum, 150->= 160 passes all three J. The author's compliant + hot group (A07 / A09 / A10) passes 130-140 and 160.
- Cause: the full-tank rocking mode crosses the ~24.3 Hz first bending between J 0.76e-3 and J 1.6e-3.
  - At J 1.6e-3 the window lies below the coincidence, which sets its upper edge.
  - At J 0.76e-3 the window lies above it, which sets its lower edge.
  - The J 2.7e-3 lower edge has a different cause: the max-q corner.
- The new ENG-11 text states all of this.

**RV7-10, n48 (B01-B03)**
- B01 reproduces exactly (none at J 1.6e-3).
- n48 reflects J by n² = 23.04 at every pose. It is a bounding sensitivity, not the verified convention: 227 (2) VERIFIED cons.
- The datasheet's wording is adequate: "the inertia convention (n48 at J 1.6e-3, CAD v3.5.1: none)", kept as a non-robustness statement.
- No GNC work is needed before B-TVC-1, which measures the reflected-inertia convention (open_items[46]).
- B02 / B03 are NOT RUN (time box). I judged them from B01 and the author's summary.

=====================================================================
5. (h) R2 v2 INPUTS SINCE REV4B
=====================================================================
**(i) R3-04's conditions.**
- The text is op [8] (relight_conditions.s17_v2p11_conditions), with conditions (a)-(g).
- Every number in it I confirmed in S17v2_r2v2_sweep.json (404a19d7064b336f) and in electronics.json v4 drogue_release_support.r2v2_sweep.verdict_227_5 [SIM, Electronics; GNC R2 v2 evaluated offline].
- With hold + flush:
  - 0 of 2000 dead evaluations are released at either window;
  - minimum margin +5.789 N at 0.5 s and +4.954 N at 0.8 s;
  - 1360 runs leave RUN before any R2 decision, and 640 are decided by R2.
- Without the hold: 320 of 1000 normal dead runs are released.
- Without the flush: 264 / 326 (normal) and 160 / 172 (starved040) of 1000 dead runs are released at 0.5 / 0.8 s.
- Photodiode-blind families: 20 / 42 (normal_noopt) and 42 / 98 (starved040_noopt) of 1000 dead runs are released at 0.5 / 0.8 s. The noise-free margin is -1.788 / -2.136 N at 0.8 s.
- FC frame-noise budget for P(dead release) <= 1e-3:
  - 2.51 N rms iid (1.65 N AR(1), rho 0.61) at 0.8 s;
  - 3.06 N rms iid (2.00 N AR(1)) at 0.5 s;
  - 5 N rms gives P 6.9 % / 22.9 %.
- At cold flow × 1.3: margins +2.077 / +1.242 N, budgets 1.10 / 0.63 N rms.
- All winds: 320 of 1000 normal dead runs are released at 0.8 s.
- OI-FC-PC-BRANCH: Pc_f at E2 is 3.04 bar abs, against the 3.0 threshold. The branch releases every normal-family run at the E2 frame, outside R2 (op [20]).

**(ii) Purge.**

Reserve judgement at 76 / 80.5 g [DERIVED from SIM; above 80 g, ESTIMATE (linear per-run shift)]:
- Test setup: line 208 against the v3d reference st|G73|h285, A1 210 m, v351, the first 500 runs of each of the 2 bases (n = 1000), dip onset 80 g, paired by run index, one-sided 95 % upper bound.
- My method reproduces p2_rev4 G80_vs_v3d_ref exactly: lost 12, gained 10, UB95 0.972 pp.

| Vented mass | UB95 liquid (pp) | UB95 powered (pp) | Result |
|---|---|---|---|
| 76 g | 0.854 | 0.617 | PASS |
| 80.5 g | 0.972 | 0.617 | PASS (margin 0.028 pp) |
| 82.1 g | 1.089 | — | first liquid fail (0.1 g steps) |
| 85.5-85.8 g | 1.206 | 0.736 | FAIL on liquid |

- relight_ok is 1.000 in every flown base (G73 / G80).
- The 76 g basis stays: G73 is decided and G80 is the sensitivity.
- The 80.5 g of 256 (2) is the 289.5 K figure. The binding warm end is 297.15 K, which is RV7-04.

The remedy, 257 (2) condition (d): my plain answer is that **it does not fail on the vent or on the sign of the margin anywhere**.
- Model (h7):
  - cap = floor((76/(31.06 r) - 0.05)/0.01) × 0.01 s, never above 2.39 s;
  - scheduled flow = cap - 0.01 + 0.05 s, never above 2.43 s;
  - need at 283.15 K = 2.2/r (2.25/r and 2.30/r with the FD-01 element bounds);
  - the 1/(Cd × A) need scaling is ASSUMED.
- Vent at the cap: at most 75.99 g for r 1.0-2.0.
- 283.15 K margins:
  - 0.23 / 0.213 / 0.208 / 0.187 / 0.178 s at r 1.00 / 1.08 / 1.13 / 1.20 / 1.30;
  - 0.10-0.18 s with FD-01 over 1.0-1.3;
  - positive up to r 2.0 (0.11 s; 0.085 / 0.06 s with FD-01).
- It needs two additions, both in op [29] and op [24]:
  - (1) The re-set must take the upper 95 % bound of the measured Cd × A.
    - At r = 1.1326, a ratio measured 3 / 5 / 7.9 / 10 % low gives a true vent of 78.27 / 79.78 / 81.99 / 83.58 g.
    - At 7.9 % low it is just under the 82.1 g first fail.
  - (2) CF-4 must show the 283.15 K need at the re-set flow.
    - At r 1.13 the flow is 2.15 s, against 2.2 s if the need does not scale.
- Fallback without the re-set: measured Cd × A <= 1.08 × the Cd 0.70 value (vent <= 82 g at the cap). Otherwise GNC re-runs the A1 reserve test at the measured vent.
- Below r 1, condition (b) governs:
  - r 0.95: margin 0.114 s (0.062 / 0.009 s with FD-01);
  - r 0.91: 0.012 s, and negative with FD-01.

**(iii) Lost-relight mission outcome.**
- Op [9] (relight_conditions.unprimed_or_unknown_line) and op [26] (FMEA).
- No RUN, so no drogue release and no released dead vehicle.
- The vehicle descends on the drogue, touching down at p50 -21.8 / p01 -24.3 m/s, about 0.46 × the energy of a released dead vehicle (SIM, rev2 amendment V).
- The flight is a vehicle loss (P 0). The probability is not quantified.
- OI-UNPURGED-RELIGHT stays open (253 (7)(iv)).

**(iv) R3-01.** Op [23].

**(v) R4-03 lit corners at W 0.8 s.**
- In op [8] (lit side) and op [22] (OI-FMIN-LIT).
- At the 0.21776 mm start-level lift (TO-VERIFY at CF-3, 230 (4)), 3 of 72 P4c corners never reach 37.16 N within 0.8 s.
  - F_min is 33.14 N with torch 0.
  - Cd0.65|a0.6|n0.68|ri0.3|eta0.85 crosses at E2 + 0.857 s.
- With the flush, no lit run is released. The drogue is held and the relight is aborted at t_E2 + 0.8 s (ECU backstop E2 + 0.85 s), which is a lost relight in the Pc-invalid branch.
- Both 37.16 N and 0.8 s are kept:
  - a 0.887 s window rescues only one corner;
  - a 33.14 N threshold would sit below the 35.92 N dead-side maximum at cold flow × 1.3.

**(vi) OI-PHOTODIODE-VIEW.** Op [21] (HIGH).

**Also checked:**
- line 230 (5): ops [8] and [22];
- S17 v2.11: ops [6]-[8] and [10]-[15];
- noise budget: ops [15], [25] and [27];
- OI-FMIN-LIT: op [22];
- OI-FC-PC-BRANCH: op [20];
- purge_bound wording: ops [28]-[31]. The 2.55 s note is renamed to note_rev4b_superseded_256_2, not deleted.

=====================================================================
6. (e) GNC'S DATASHEET SENTENCE FOR ENG-11
=====================================================================
- **REFUTED as written.** "Design-to 100-120 N m/rad ... V5c (100-130) ∩ CAD v3.5.1 FE (<= 90-120)" does not hold on CAD v3.5.2.
- The exact replacement text is DS row 8 in Appendix B: design-to 100-110 N m/rad; only 100 N m/rad also passes at both band ends; no K_s passes at all three J.
- Row 8's source line also needs a fix:
  - the row's "J 2.7e-3 120->= 160" is the rigid T_REF variant A03;
  - the summary group J_2.7_cons_FE says 125->= 160, which is set by A10 (compliant + hot E -10 %).

=====================================================================
7. (b) t10_postcheck v3 AND THE UPDATED C06 RULE
=====================================================================
**The updated C06 rule** (scripts/t10_postcheck_v3.py, db3139a6db3758f8):
- C06a "pcf_tmax 0.8 s without its W10 < 6 / 227 (5) scope":
  - regex `(?i)pcf_tmax[^.;]{0,30}0\.8`;
  - a hit counts unless `W10 ?(<|&lt;) ?6|227 \(5\)` occurs within 200 characters.
- C06b "pcf_tmax 0.5 s presented as current":
  - regex `(?i)pcf_tmax[^.;]{0,30}0\.5 ?s`;
  - a hit counts unless there is a marker word within 120 characters (the v2 MARK rule, superseded / history / verbatim paths), or `v3\.1|[Rr]eplac` within 120 characters.
- Exempt: reviewer_probes, rev4b_document_self_check and rev2p2_document_self_check.
- The `--rv7` flag adds four required checks:
  - R08: relight_conditions carries photodiode, Pc branch, cold flow 1.3 and 2.51 N;
  - R09: purge_bound carries 2.43 s, 2.39 s and 80.5 g;
  - R10: f3c7cfbcfb98bcd7 present;
  - R11: unprimed / UNKNOWN ... refused.

**Exit codes and remaining hits**
- Candidate, --publication: exit 1. One C06a hit, at checkpoint_rev4b/unknowns/4: 'S17 confirmation of pcf_tmax 0.8 s, the mode-3 flush, the FC frame-noise budget'.
- Candidate, --publication --rv7: exit 1. The same hit, and R08-R11 all NO.
- Trial: exit 0, 0 hits. C01-C19 and N01 are unmarked 0; R01-R11 and U01-U04 are yes.
- Remaining hits after the corrections: none.

=====================================================================
8. (a) DOCUMENT DIFF (v3.1 → candidate)
=====================================================================
- Leaves: 41 changed, 779 added, 41 removed.
  - 38 of the removed leaves are the checkpoint_rev2p2 block.
  - The other 3 are the B-TVC-1 gate_outcomes (2) and measure[5].
- The author's keydiff (9c15a392574cd511) gives 41 / 76 / 4. That count is by key, and it is consistent with the leaf count. The checkpoint_rev2p2 removal is declared there, and v3.1 keeps it on record.
- The verbatim lead lines 204, 208, 213, 214, 219, 222 and 227 are EXACT.
- Open items:
  - they go from 42 to 53; new items 42-52 each have an owner;
  - changed old items: 31, 35, 36, 37, 39, 40, 41;
  - with ops [20]-[24] they become 58 (indices 53-57).
- RV6 texts: 20 of 22 new texts are present. Two fragments are missing:
  - RV6-01 " admits failing stiffnesses..." (superseded by RV7-01);
  - RV6-09 "+2 kg 2.55 kg..." (superseded by 256 (2), RV7-04).

  One RV6-01 "old" text that shows as present is a false positive: it is a prefix of its new text.

=====================================================================
9. (f) DATASHEET-INPUTS-GNC.md, ROW BY ROW
=====================================================================
- Rows 1-7, 9 and 10 are verified.
  - Row 2: 62 m, P 0.996 [0.986, 0.999], cap 62.9248 m.
  - Row 10: the paired line-208 comparison of the +1 kg / 2.20 kg arm against the 0 kg vehicle (pl0, tank at 0.58 m, h210) gives lost 8, gained 8 of 1000, UB95 0.658 pp: PASS [DERIVED from SIM].
- The open-item references in rows 11a-11l match the candidate's indices.
- Corrections needed: row 5 (basis), row 8 (sentence, evidence, source), rows 11b and 11f, and the carried pcf_tmax line (Appendix B).
- Row 8 against the summary proposal: the row matches the eng11fe_summary proposal on CAD v3.5.1, except the J 2.7e-3 attribution (A03 against A10). On CAD v3.5.2 it is superseded (RV7-01).
- I recommend adding one-line datasheet entries for the new open items 53-57: OI-FC-PC-BRANCH, OI-PHOTODIODE-VIEW (HIGH), OI-FMIN-LIT, R3-01, and PURGE condition (d).

=====================================================================
10. (g) POST_K SERVO FACTOR (RM2-05), 234 (5) / (6), AND THE ca2c FOLD (RV7-11)
=====================================================================
- The implied servo factor 1/(K_s (1/k_s − 1/S)) from k_s58 and from k_s174 agrees to 4 decimals at every pose and axis. The table's with-servo columns are therefore the series model, with the per-pose, per-servo effective horn radius of 234 (5) (7.88-11.14 mm) [DERIVED].
- How that factor compares with the loop's g:
  - within 0.05 % at neutral (23.04 = n²), at the beta stops, and at the 7-degree beta poses;
  - 0.996 at stop135 / 225;
  - at cone 135 / 225: 0.997 (alpha) and 0.989-0.990 (beta);
  - at the 7-degree alpha poses: 0.966 (alpha) and 0.948-0.949 (beta);
  - 0.935 at stop090 / 270;
  - 0.936 / 0.923 at cone 045 / 315;
  - 0.840 at stop045 / 315.
- Effect on ENG-11: none. R3G_JC, with this factor, gives exactly the R3P_JC windows.
- The R3 with-servo K is 0.5-4.6 % above the 234 (5) v3.5.1 values (787-1759 at K_s 58 and 1681-3436 at K_s 174).
- 234 (5) "FE not preferred over V5c until the beta cause is found" is kept in the new text: the design-to is the window that passes on both plants.
- 234 (6): the candidate's only mention of the 21-33 Hz pair is v32_items_rev4b/items/12 (0.786 × the FE 21-33 Hz). It complies: not loop-relevant.
- ca2c (243 (8), the RM2-06 modal fold, modes below 3.9 kHz change by at most 0.102 %):
  - it does not touch the loop inputs (static S per pose, g, J, the ASSUMED bending);
  - a 0.1 % change is far below the 5 N m/rad (about 4.5 %) grid step;
  - a deeper check is NOT RUN.

=====================================================================
11. T4 / N-07 (RV7-12)
=====================================================================
**No GNC objective needs the DC-D v2 duty as one firing in Combustion's T4.**

The DC-D v2 duty [DERIVED from the DC-D v2 file 9c5d7cf391d8297b]:
- 49.27 s thrust-on, in burns of 31.76 / 7.75 / 9.76 s;
- 6.31 kg of N2O on the v2 map, 7.02 kg on the S230 map.

GNC's static-fire objectives need DC-D segments, not the full duty:
- throttle map and Pc loop:
  - staircase 500 → 62.5 N (1.47 kg);
  - steps 100 ↔ 500 N (0.59 kg);
  - sweep 175-399 N (1.16 kg);
  - burn 2 triangle up to 428 N (0.94 kg);
  - burn 3 hold at 130 N (0.60 kg);
- F_acc against the load cell at >= 450 N: 10.13 s in DC-D v2, of which 5.9 s is the 500 N hold (1.44 kg);
- IMU vibration at F_max;
- gimbal sweeps, thrust-vector alignment, roll torque, and the rocking mode under thrust;
- >= 30 starts for the ignition-latency distribution.

Each can be flown inside the A = 150 C limit. The DC-D first burn would cross that limit at about 23.5 s (N-07).

The DC-D relights do not represent A1:
- DC-D: coasts of 10.25 / 8.25 s after a 31.76 s burn.
- A1 p99 record: 3.78 s at 0.88, coast to 22.79 s, then 4.59 s at 0.47.
- The A1-like relight objective sits with REV-COMB-4's shortest T4 firing: B1 p99 21.76 s, a coast of about 19 s, then one relight of about 4.6 s at about 0.47, about 2.0 kg in all.

Naming collision: GNC's test_campaign T4 is the drogue drop test; Combustion's T4 is the DC-D firing.

=====================================================================
12. NOT RUN
=====================================================================
- B02 / B03 (n48 at the other J): judged from B01 and the author's summary (time box).
- A02 / B07: re-run on edge rows only (8 / 12 rows), not on all 30.
- ca2c: no deeper check beyond the inputs argument.
- GNC's own R2 v2 re-run with the flush: an open item for GNC (open_items[47]), not part of this review.

All runs were linear and DERIVED. At most 2 sim processes ran at nice 10. All my processes have ended, and I touched no other agent's files or processes.

=====================================================================
13. FILES: reviews/gnc/rev4b/MANIFEST_REV-GNC-7.sha256
=====================================================================
- Manifest: 94 files, all hashes re-verified (0 mismatches). The manifest's own sha256/16 is e04257acba555551.
- Hub use: 2.27 MB.
- Scratch /dev/shm/rev_gnc7 has been removed.
- Disk free at the end: 2.2675 GB (2.112 GiB).
- Two stage scripts still point at the scratch paths, so they record what ran but will not re-run as they are:
  - stage_hub.sh and finalize.sh;
  - master_q.sh and the slot scripts.
- The corrections and t10 outputs were produced last from the hub copies. data/b/rv7_v32_corrections.json's run_dir = reviews/gnc/rev4b/data/out/d_r3.

Files (sha256/16, path relative to reviews/gnc/rev4b/):

**data/a**
- d4c2fe715a26acf5 data/a/a1_docdiff.json
- 406d2fb3e8e5a8d9 data/a/a2_rv6_texts.json

**data/b**
- fea33eacdd8a7d56 data/b/gnc_v3.2_rv7_trial.json
- f7c0c6051efd5a08 data/b/rv7_v32_corrections.json
- d52bdf289fb61a4c data/b/t10v3_candidate_pub.json
- e297bc19c8ebd9a9 data/b/t10v3_candidate_pub.log
- b7700ce41b8e3410 data/b/t10v3_candidate_pub_rv7.json
- 33caa63c27c3850f data/b/t10v3_candidate_pub_rv7.log
- dbfe3907b22b9d6c data/b/t10v3_trial_pub_rv7.json
- 71ce6403609dcae1 data/b/t10v3_trial_pub_rv7.log

**data/chk**
- 48207388a0ed9784 data/chk/fea3d_manifest_abs.sha256

**data/h**
- 4f613171e014f9fa data/h/c_compare2.json
- 0e93d58d059859cd data/h/d_summary.json
- 254ccd4556ad2e28 data/h/d_table.json
- 75f072dea897e416 data/h/f1_payload_pair.json
- 6970e0d5d94d7e6f data/h/h1_reserve.json
- a009c67a857cc9bf data/h/h2_reserve_dip.json
- f8f40cdb5d048bf8 data/h/h3_reserve_warm.json
- d668b150a697635d data/h/h4_l208_ub95.json
- 2a71a245e31184e8 data/h/h5_l208_edge.json
- 9c89d4d939c7bb70 data/h/h6_purge_remedy.json (superseded by h7)
- b671617ce06ec922 data/h/h7_purge_remedy_v2.json

**data/out**
- 3f8dad4161ba689c data/out/c_repro/eng11fe_A01.json
- c6dcef156b572b8e data/out/c_repro/eng11fe_A03.json
- 113f564e9cc9731e data/out/c_repro/eng11fe_A08.json
- 011f791021604fb3 data/out/c_repro/eng11fe_B01.json
- 433630ef115a2604 data/out/c_repro/eng11fe_C01.json
- 43b19e96828dc9d0 data/out/c_repro/eng11fe_check.json
- d93e55bdc889b123 data/out/c_repro_A02e/eng11fe_A02.json
- 0c0201cc0daf6360 data/out/c_repro_B07e/eng11fe_B07.json
- e00732b63dfb9ef5 data/out/d_r3/eng11fe_R3C_JC.json
- 003041e63e90c121 data/out/d_r3/eng11fe_R3G_JC.json
- 76ace0181a6ed349 data/out/d_r3/eng11fe_R3Hi_JC.json
- 09b5c7e4559f7630 data/out/d_r3/eng11fe_R3Hi_JHI.json
- 2f33d3ea00abb673 data/out/d_r3/eng11fe_R3Hi_JLO.json
- 943920165ce87eec data/out/d_r3/eng11fe_R3Lo_JC.json
- 43f8c9a85f7bcbdc data/out/d_r3/eng11fe_R3Lo_JHI.json
- 4fc6e41296433225 data/out/d_r3/eng11fe_R3Lo_JLO.json
- a174c0d31a2a052b data/out/d_r3/eng11fe_R3P_JC.json
- 628ba81e3e014b61 data/out/d_r3/eng11fe_R3P_JHI.json
- cea75471ba618878 data/out/d_r3/eng11fe_R3P_JLO.json
- 62470111242b4a0e data/out/d_r3/rv7_r3_inputs.json
- 21e1e96005d17d9e data/out/d_r3_ks58_174/eng11fe_R3P_JC.json
- 62470111242b4a0e data/out/d_r3_ks58_174/rv7_r3_inputs.json

**logs**
- 364e1583b3968974 logs/c_check.log
- 001bc4f1912734c3 logs/c_compare2.log
- b30e2a30ba0bc8cc logs/c_edgeA02.log
- ffb8ba3763b7f9ba logs/c_edgeB07.log
- a5bcb225a8819f7b logs/c_full.log
- 11e29b9a87bfd6a5 logs/c_full_r.log
- 56b2e70154b1a5b5 logs/d_r3_b2.log
- ad4135e0797a99f7 logs/d_r3_b2r.log
- b0115983fabd9d6f logs/d_r3_b3.log
- 330b4601e247c806 logs/d_r3_b3b.log
- e1b672902e4c68eb logs/d_r3_b3r.log
- d80d9dbdbf23697b logs/d_r3_b4.log
- 75ba7c7daae3b36c logs/d_r3_b4g.log
- 50c75833365414c9 logs/d_r3_s2.log
- 214138d0dfc4d946 logs/d_summary.log
- b6a8267a0d9edb2b logs/d_table.log
- 7ea2acf8263e1a78 logs/master.log
- da8e93053b4ff4eb logs/pin_abs.sha256
- 781c9f08eb16499d logs/rv7_v32_corrections.log

**scripts**
- 1b4aa309baf1792c scripts/a1_docdiff.py
- a6a503cbfae77866 scripts/a2_rv6_texts.py
- 276233a096da9019 scripts/c_compare.py
- 4d5d6a66d5c920a4 scripts/c_compare2.py
- a9315b196cf40394 scripts/d_summary.py
- 40ab41702812fe24 scripts/d_table.py
- d7c1e0162c81829e scripts/env7.sh
- fd190903e453c56f scripts/f1_payload_pair.py
- 404756331deb3913 scripts/finalize.sh
- 3c4ec98375787fcd scripts/guard_run.py
- 3a1638983dc027d3 scripts/h1_reserve.py
- 59f4940b1a976fe9 scripts/h2_reserve_dip.py
- 771512a2865ea958 scripts/h3_reserve_warm.py
- 6d3509f8779b6b2e scripts/h4_l208_ub95.py
- edbe1ba42bfda2e7 scripts/h5_l208_edge.py
- 6dd2958d791955bc scripts/h6_purge_remedy.py
- b6057177a82464c6 scripts/h7_purge_remedy_v2.py
- 6049f270f2fe9eae scripts/m2_eng11_redirect.diff
- 62501c5c36e3f1b0 scripts/master_q.sh
- ddcb0e5a866f56ca scripts/print_ops.py
- d89bf98f8056d876 scripts/run_fe.sh
- 310890b172ab8af5 scripts/run_r3.sh
- a82477ffac770b42 scripts/run_repro.sh
- 0ab8c677bcfdf7a4 scripts/rv7_eng11_r3.py
- 25b3abedf37f146d scripts/rv7_repro.py
- 4fb2cc81e1eb7eca scripts/rv7_v32_corrections.py
- fae9e03d9ea24f66 scripts/slot1_c.sh
- 7e25124548d15627 scripts/slot1_next.sh
- 0b14bb3ca9ec9bc0 scripts/slot2_next.sh
- 6513ef9b1fb14426 scripts/stage_hub.sh
- db3139a6db3758f8 scripts/t10_postcheck_v3.py

=====================================================================
APPENDIX A: gnc.json v3.2 OPERATIONS (exact; the authoritative copy is data/b/rv7_v32_corrections.json f7c0c6051efd5a08)
=====================================================================
**[0]-[2] replace (RV7-01).** The same OLD segment is replaced by the same NEW text in three fields:
- requirements/gimbal/tvc_actuator/ENG-11_servo_output_stiffness/v
- requirements/gimbal/tvc_actuator/B-TVC-1/v/acceptance
- status

OLD: design-to window 100 <= K_s <= 130 N m/rad (two-sided) for the servo output stiffness on the V5c plant (CAD v3.3) at the ASSUMED J 1.6e-3 kg m2 (servo output shaft, added to I_piv), cons kinematics and the ASSUMED first bending 24.3 Hz full / 25.64 Hz landing; acceptance: ENG-07d (stable, upper GM >= 6 dB at every floor20 corner, continuous pose envelope, notch as flown) re-run on the B-TVC-1 measured K_s (with its uncertainty), J, reflected-inertia convention and rocking modes at the poses and on the measured or airframe-FE first bending mode (full and landing); K_s is frozen only on a PASS; on a FAIL the notch set (second notch on the measured bending mode) is changed and the margins re-run before any K_s change. Plant basis: on the 3D FE structure of CAD v3.5.1 the top of the window falls to about 126 (alpha) / 129 (beta) N m/rad (DERIVED frequency map, uniform pose scaling ASSUMED); GNC re-verifies the window on the FE plant before it is quoted as design-to (RV6-14 re-run, staged apart in 01-systems-gnc/staging_v3.1/rev4b/eng11_fe/, not folded here)

NEW: design-to window 100 <= K_s <= 110 N m/rad (two-sided) for the servo output stiffness at the ASSUMED J 1.6e-3 kg m2 (servo output shaft, added to I_piv), cons kinematics and the ASSUMED first bending 24.3 Hz full / 25.64 Hz landing: the 227 (3) window (100-130, V5c plant, CAD v3.3) re-verified on the FE plant (227 (3), RV6-14), i.e. the part of it that passes on both plants (234 (5): the FE plant is not preferred over V5c until the beta cause is found). FE plant CAD v3.5.2: the R3 pose table (04-fea/assembly3d_v352/results/v352/k_table_r3_v352.json (f3c7cfbcfb98bcd7); S = FE coupled R3 per pose, g = V5c on the 9 cone poses / CAD kinematics at the 8 stops, cone + stop envelope) passes <= 90-110 N m/rad on both axes (alpha <= 90-115, 140->= 160, beta <= 90-110; worst upper GM 6.098-6.155 dB inside 100-110); at the ends of the R3 K band (k_band_r3_v352: S at the band value at every pose, one fixed ECU notch referenced on the R3 centre pose) it passes <= 90-100 at the band maximum and <= 90-115, 150->= 160 at the band minimum, so 100 N m/rad is the only grid value of the design-to window that passes at both band ends [DERIVED, linear ENG-07d with m2_eng11_fe v1.0 / m2_eng11 v1.1 unchanged, REV-GNC-7 (reviews/REVIEW-GNC-R5.md; reviews/gnc/rev4b/, MANIFEST_REV-GNC-7.sha256); K_s grid 90-160 step 5, edges +-5 N m/rad]; the upper edge is the coincidence of the full-tank rocking mode with the first bending (failing corners at 23.90-24.55 Hz pose-wise and at both band ends, zeta 0.02, notch e 0.95). Not robust: on the R3 plant J 2.7e-3 gives 120->= 160 (band maximum 110->= 160, band minimum 120->= 160) and J 0.76e-3 gives 130->= 160 (band maximum 130->= 160, band minimum 130->= 160); all three J together: pose-wise none, band maximum none, band minimum 150->= 160; the J 2.7e-3 lower edge is the max-q corner (full tank, 500 N, worst actuator, fins, zeta 0.10, 16.3-19.2 Hz), the J 0.76e-3 lower edge the bending coincidence (as on the CAD v3.5.1 FE plant, rigid airframe, T_REF: 130->= 160 / <= 90-120 / 120->= 160, and 125->= 160 at J 2.7e-3 with the compliant airframe + hot E -10 % (A10); on that compliant + hot set all three J pass 130-140, 160); with the first bending at 0.9 x the window is empty (CAD v3.5.1 FE plant, eng11_fe C01). Superseded plant bases (records): V5c 100-130 (CAD v3.3); CAD v3.5.1 FE <= 90-120 (eng11_fe, 24 variants), whose 'design-to 100-120' does not hold on CAD v3.5.2 (115 and 120 fail pose-wise on beta, 105-120 at the band maximum on alpha). acceptance: ENG-07d (stable, upper GM >= 6 dB at every floor20 corner, continuous pose envelope, notch as flown) re-run on the B-TVC-1 measured K_s (with its uncertainty), J, reflected-inertia convention and rocking modes at the poses and on the measured or airframe-FE first bending mode (full and landing); K_s is frozen only on a PASS; on a FAIL the notch set (second notch on the measured bending mode) is changed and the margins re-run before any K_s change

**[3] replace (RV7-01).** Path: requirements/gimbal/tvc_actuator/ENG-11_servo_output_stiffness/tag

OLD: J convention VERIFIED (227 (2))

NEW: J convention VERIFIED (227 (2)); plant basis CAD v3.5.2 R3 pose table checked by REV-GNC-7 (DERIVED, rv7_eng11_r3 v1.0 on m2_eng11_fe v1.0 / m2_eng11 v1.1, unchanged)

**[4] set (RV7-03).** Path: requirements/gimbal/tvc_actuator/ENG-11_servo_output_stiffness/k_band_r3_v352

NEW (JSON object):
{"v": {"FE_coupled_N_m_per_rad": {"alpha": {"min": 7293.95, "min_pose": "stop000", "max": 9337.08, "max_pose": "stop180"}, "beta": {"min": 3971.84, "min_pose": "stop180", "max": 7172.12, "max_pose": "stop000"}}, "FE_diagonal_N_m_per_rad": {"alpha": {"min": 7294.05, "min_pose": "stop000", "max": 9337.32, "max_pose": "stop180"}, "beta": {"min": 3971.94, "min_pose": "stop180", "max": 7172.21, "max_pose": "stop000"}}, "k_s58_coupled_N_m_per_rad": {"alpha": {"min": 1149.93, "min_pose": "neutral", "max": 1426.19, "max_pose": "stop000"}, "beta": {"min": 790.77, "min_pose": "stop180", "max": 1799.09, "max_pose": "stop000"}}, "k_s58_diagonal_N_m_per_rad": {"alpha": {"min": 1149.93, "min_pose": "neutral", "max": 1520.79, "max_pose": "stop315"}, "beta": {"min": 790.77, "min_pose": "stop180", "max": 1799.09, "max_pose": "stop000"}}, "k_s174_coupled_N_m_per_rad": {"alpha": {"min": 2697.48, "min_pose": "neutral", "max": 3075.77, "max_pose": "stop000"}, "beta": {"min": 1696.7, "min_pose": "stop180", "max": 3594.13, "max_pose": "stop000"}}, "k_s174_diagonal_N_m_per_rad": {"alpha": {"min": 2697.48, "min_pose": "neutral", "max": 3165.81, "max_pose": "stop315"}, "beta": {"min": 1696.7, "min_pose": "stop180", "max": 3594.14, "max_pose": "stop000"}}}, "units": "N m/rad", "definition": "K band = range_over_posted_R3_poses (lead 250 (6)): min and max over the 17 posted v3.5.2 R3 poses (8 stops at 8 deg, neutral, 8 range-cone poses at 7 deg; 17 of 17 posted, all ACCEPTED, lead 18:40:44Z) per quantity, with the pose; FE = structure + rod chain with the servo rigid (coupled = other axis moment-free, the S of the ENG-07d loop; diagonal = other axis held); k_s58 / k_s174 = with the servo output compliance in series at K_s 58 / 174 N m/rad (FEA3D post_k with the RM2-05 effective horn radius per servo and pose, 234 (5)); alpha = outer axis X, beta = inner ring axis Y", "loop_check": "ENG-07d (stable, upper GM >= 6 dB at every floor20 corner, cone + stop envelope) with one fixed ECU notch (Q 1 / -12 dB at e 0.95 / 1 / 1.05 x the R3 centre landing mode), K_s 90-160 step 5, both axes: J 1.6e-3 pose-wise <= 90-110, band maximum <= 90-100, band minimum <= 90-115, 150->= 160; J 0.76e-3 pose-wise 130->= 160, band maximum 130->= 160, band minimum 130->= 160; J 2.7e-3 pose-wise 120->= 160, band maximum 110->= 160, band minimum 120->= 160; all three J together: pose-wise none, band maximum none, band minimum 150->= 160; at K_s 58 / 174 N m/rad (the with-servo K quantities of the table) the pose-wise loop gives: K_s 58 alpha fail, beta fail (worst-actuator corners at zeta 0.10: alpha max-q with fins, 17.492 Hz, GM 5.840 dB; beta no-aero, 15.202 Hz, GM 5.935 dB); K_s 174 alpha PASS, beta fail (bending coincidence, 24.341 Hz, GM 5.964 dB) [DERIVED, linear, REV-GNC-7 (reviews/REVIEW-GNC-R5.md; reviews/gnc/rev4b/, MANIFEST_REV-GNC-7.sha256)]", "information": "beta sign trend (the table's beta_sign_trend, fraction of the stop045 delta per pose): beta > 0 0.8799-1.2085, beta = 0 0.5159-0.9896, beta < 0 0.1716-0.8207: the fraction follows the sign of beta, and the RM2-05 band built from the stop045 delta does not bound every pose (the table's statement; stop000, beta+, combined045 and combined315 ACCEPTED above the original band, lead 18:40:44Z). R3 is stiffer than the RM2-05 corrected v3.5.1 values: S_R3 / S_v351 = 1.089-1.150 (alpha), 1.022-1.098 (beta) over the 17 poses. The R3-implied servo factor 1 / (58 (1 / k_s58 - 1 / S)) equals the loop's g within 0.05 % at neutral (23.04 = n^2), at the beta stops stop000 / stop180 and at the 7 deg beta poses; it is 0.996 of it at stop135 / 225 (cone 135 / 225: 0.997 alpha, 0.989-0.990 beta), 0.966 / 0.948-0.949 (alpha / beta) at the 7 deg alpha poses, 0.935 at the alpha stops stop090 / 270, 0.936 / 0.923 at cone 045 / 315 and 0.840 at stop045 / 315 (the loop takes V5c g on the cone and CAD kinematics at the stops) [DERIVED]", "tag": "SIM (FE unit steps on the v3.5.2 R3 pose runs, FEA3D) + DERIVED (servo in series; K_s 58 / 174 ASSUMED, TO-VERIFY B-TVC-1); loop check DERIVED (linear); not physical approval", "src": "04-fea/assembly3d_v352/results/v352/k_table_r3_v352.json (f3c7cfbcfb98bcd7)"}

**[5] set (RV7-01).** Path: open_items/43

NEW: rev4b (227 (3); RV6-14): ENG-11 window on the 3D FE plant: CAD v3.5.1 re-run by GNC (eng11_fe, 24 variants: J 1.6e-3 <= 90-120) and CAD v3.5.2 checked by REV-GNC-7 on the R3 pose table (J 1.6e-3 <= 90-110; band ends <= 90-100 / <= 90-115, 150->= 160; J 2.7e-3 120->= 160; J 0.76e-3 130->= 160) [DERIVED]: CLOSED for the datasheet sentence (requirements.gimbal.tvc_actuator.ENG-11_servo_output_stiffness, design-to 100-110 N m/rad); remaining: B-TVC-1 (open_items[46]) and the bending mode (open_items[44]). Owner: lead (datasheet sentence)

**[6] replace (RV7-02).** Path: requirements/ignition/relight_conditions/v

OLD: Electronics v2.11 carries 0.8 s into its S17 sweep and confirms it or returns it to the lead.

NEW: Electronics v2.11 S17 CONFIRMED 0.8 s for the W10 < 6 m/s envelope (227 (5)) with conditions (relight_conditions.s17_v2p11_conditions).

**[7] replace (RV7-02).** Path: requirements/ignition/relight_conditions/v

OLD: Electronics implements it in v2.11 and runs S17 (onsets 1-50 ms x frame phases x noise); GNC re-runs the R2 v2 statistics with the flush afterwards; Electronics states the FC frame-noise budget against the +5.3 to +6.0 N mode-3 margin (227 (6)).

NEW: implemented in the v2.11 S17 evaluator (the ECU has no mode-3 filter: the flight implementation is the FC owner's); FC frame-noise budget <= 2.51 N rms iid at 0.8 s (s17_v2p11_conditions (e)); GNC re-runs the R2 v2 statistics with the flush (open_items[47]).

**[8] set (RV7-02).** Path: requirements/ignition/relight_conditions/s17_v2p11_conditions

NEW: Electronics v2.11 S17 CONFIRMED pcf_tmax 0.8 s for the W10 < 6 m/s envelope, not returned (227 (5); interfaces/electronics.json v4 11f7896ad0d0613b drogue_release_support.r2v2_sweep.verdict_227_5; SIM S17v2_r2v2_sweep.json 404a19d7064b336f, GNC R2 v2 evaluated offline): with the ECU R2 hold and the mode-3 flush, 0 of 2000 dead evaluations are released at either window, minimum margin +5.789 N at 0.5 s and +4.954 N at 0.8 s (normal and starved040 families, photodiode main-chamber view, reference none); of the 2000 dead evaluations per window 1360 leave RUN (ECU FLAMEOUT) before any R2 decision and 640 are decided by R2. 0.8 s holds only with ALL of: (a) the ECU R2 hold with the FC DROGUE report (without it 320 of 1000 normal dead runs are released); (b) the mode-3 flush at the Pc-invalid onset (without it 264 / 326 normal and 160 / 172 starved040 of 1000 dead runs are released at 0.5 / 0.8 s); (c) the photodiode main-chamber view proven (FLAMEOUT_OPT armed) or the R2 reference re-taken at the ECU E2 or at the light: photodiode-blind families release 20 / 42 (normal_noopt) and 42 / 98 (starved040_noopt) of 1000 dead runs at 0.5 / 0.8 s, noise-free margin -1.788 / -2.136 N at 0.8 s (OI-PHOTODIODE-VIEW); (d) the FC Pc branch (release on a frame with Pc valid and filtered Pc >= 3.0 bar abs) off until the flame-out window has passed, or its threshold moved with a stated margin: Pc_f at E2 is 3.04 bar abs, so the branch releases every normal-family run at the E2 frame, lit or about to flame out 1-50 ms later, outside R2 (OI-FC-PC-BRANCH); (e) FC frame noise inside the budget for P(dead release) <= 1e-3: <= 2.51 N rms iid (1.65 N AR(1), rho 0.61) at 0.8 s, <= 3.06 N rms iid (2.00 N AR(1)) at 0.5 s; 5 N rms is not admissible (P 6.9 % / 22.9 %); (f) the cold-flow bound: at cold-flow apparent thrust x 1.3 (basis: the Combustion v2.4a adiabatic bound) the hold + flush margins fall to +2.077 / +1.242 N and the iid budget to 1.10 / 0.63 N rms at 0.5 / 0.8 s (REV-ELEC-3 R3-04); (g) inside W10 < 6 m/s only (all winds: 320 of 1000 normal dead runs released at 0.8 s). Lit side: a starved plateau is released at all 10 frame phases up to 0.75 s at the 0.8 s window (0.45 s at 0.5 s), 0.35 s over GNC's 0.4 s starve top. Low lit corners (230 (5), OI-FMIN-LIT; REV-COMB-4 R4-03): at the 0.21776 mm start-level lift 3 of 72 Combustion P4c corners never reach 37.16 N within 0.8 s (F_min 33.14 N with torch 0; Cd0.65|a0.6|n0.68|ri0.3|eta0.85 crosses at E2 + 0.857 s, the other two stay below 37.16 N to the end of the 1.0 s record); with the flush such a lit run is not released (lit thrust capped at 33.14 N: no lit run released; without the flush 274 of 1000 are), the drogue is held and the relight is aborted at t_E2 + 0.8 s (drogue_release_hold; ECU R2 backstop E2 + 0.85 s); 37.16 N and 0.8 s are kept: a 0.887 s window rescues one of the three corners and costs dead-side margin, and a 33.14 N threshold sits below the dead-side maximum at cold flow x 1.3 (35.92 N at 0.8 s) [SIM S17 / DERIVED]; the outcome is a lost relight (the outcome class of relight_conditions.unprimed_or_unknown_line) in the Pc-invalid branch only; the start-level lift is TO-VERIFY at CF-3 (230 (4)). GNC has not re-flown the R2 v2 statistics with the flush on the v2.11 implementation (open_items[47])

**[9] set (RV7-05).** Path: requirements/ignition/relight_conditions/unprimed_or_unknown_line

NEW: An unprimed or UNKNOWN-line relight with the bleed fitted is REFUSED for A1 (fail-safe; lead 253 (7)(iv)); OI-UNPURGED-RELIGHT stays open (253 (7)(iv)) until Combustion has a model of that case. Mission outcome (GNC): no relight on that pass; the ECU never enters RUN, so the drogue is never released (RELEASE iff RUN AND b4 AND [...]) and no dead vehicle is released; the vehicle descends on the drogue to touchdown at about -22 m/s (rev2 amendment V, SIM: drogue descent of a vehicle whose engine is out, touchdown p50 -21.8 m/s, p01 -24.3 m/s, about 0.46 x the impact energy of a released dead vehicle; rev2 runs, transfer to 210 m / v3.5.1 ASSUMED); a vehicle loss (P 0 for that flight), the outcome class of a pass below L* (lead 186 (1)), of a lit run held by R2 below 37.16 N (OI-FMIN-LIT) and of a C1-drift relight abort (R3-01). Its probability is P(unprimed or UNKNOWN line at the relight), not quantified by GNC (owner Combustion / Electronics: PRIMED flag)

**[10] set (RV7-02).** Path: requirements/ignition/relight_conditions/tag

NEW: DESIGN (LEAD CHANGELOG lines 168 (1), 181 (4), 186 (1)-(2), 227 (5)-(6), 253 (7)(iv)); S17 v2.11 CONFIRMED with conditions (SIM, Electronics v2.11; REV-ELEC-3 R3-04; REV-COMB-4 R4-03 / OI-PHOTODIODE-VIEW)

**[11] replace (RV7-02).** Path: flight_software/rev2p1_entries/drogue_release_pc_invalid/v

**[12] replace (RV7-02).** Path: rev2/amendment_V_pc_invalid/status_rev4b

Ops [11] and [12] use the same OLD and NEW:

OLD: Electronics v2.11 carries 0.8 s into its S17 sweep and confirms it or returns it to the lead;

NEW: Electronics v2.11 S17 CONFIRMED 0.8 s for W10 < 6 m/s with conditions (relight_conditions.s17_v2p11_conditions: hold, flush, photodiode view or re-taken reference, FC Pc branch off or moved with margin, FC noise <= 2.51 N rms iid, cold flow x 1.3 margin +1.242 N, W10 < 6 only);

**[13] replace (RV7-02).** Path: flight_software/rev2p1_entries/drogue_release_pc_invalid/v

OLD: Electronics implements it in v2.11 and runs S17 (onsets 1-50 ms x frame phases x noise); GNC re-runs the R2 v2 statistics with the flush afterwards

NEW: implemented in the v2.11 S17 evaluator (flight implementation: FC owner); GNC re-runs the R2 v2 statistics with the flush (open_items[47])

**[14] replace (RV7-02).** Path: rev2/amendment_V_pc_invalid/status_rev4b

OLD: Electronics implements it in v2.11 and runs S17 (onsets 1-50 ms x frame phases x noise); GNC re-runs the R2 v2 statistics with the flush afterwards; frame-noise budget by Electronics (227 (6));

NEW: implemented in the v2.11 S17 evaluator (flight implementation: FC owner); GNC re-runs the R2 v2 statistics with the flush (open_items[47]); FC frame-noise budget <= 2.51 N rms iid at 0.8 s (S17 v2.11);

**[15] replace (RV7-02).** Path: flight_software/rev4b_entries/r2_frame_noise_budget/v

OLD: against the v3.1 R2 margin (16.31 N = 37.16 - 20.85 N) the probability is about 0.

NEW: against the v3.1 R2 margin (16.31 N = 37.16 - 20.85 N) the probability is about 0. Electronics v2.11 S17 [SIM + DERIVED, iid ASSUMED]: on the plant's dead-side maxima (margins +5.789 / +4.954 N) the budget for P(dead release) <= 1e-3 is 3.06 / 2.51 N rms iid (2.00 / 1.65 N AR(1), rho 0.61) at 0.5 / 0.8 s; 5 N rms gives P 6.9 % / 22.9 % (GNC's design maxima reproduce the 6.5 / 18.4 % above); at cold flow x 1.3 the budget is 1.10 / 0.63 N rms; the photodiode-blind families have no budget without a re-taken reference (4.28 N rms iid at 0.8 s with the reference at the light).

**[16] set (RV7-08).** Path: checkpoint_rev4b/unknowns/4

NEW: S17 v2.11 folded: pcf_tmax 0.8 s for W10 < 6 m/s CONFIRMED with conditions (227 (5); relight_conditions.s17_v2p11_conditions); open: OI-FC-PC-BRANCH, OI-PHOTODIODE-VIEW, OI-FMIN-LIT, the measured FC frame noise and GNC's R2 v2 re-run with the flush

**[17] set (RV7-02).** Path: checkpoint_rev4b/next_closure/1

NEW: GNC: 210 m gate-delay arm before flight acceptance (227 (8)); R2 v2 re-run with the flush on the v2.11 implementation (open_items[47])

**[18] set (RV7-02).** Path: open_items/47

NEW: rev4b (227 (6)): mode-3 flush implemented in the Electronics v2.11 S17 evaluator and S17 run (onsets 1-50 ms x 10 frame phases x noise; 0 of 2000 dead evaluations released with hold + flush; FC frame-noise budget <= 2.51 / 3.06 N rms iid at 0.8 / 0.5 s, 0.63 / 1.10 N rms at cold flow x 1.3) [SIM]; open: the flight implementation (FC owner) and GNC's re-run of the R2 v2 statistics with the flush. Owner: FC owner, then GNC

**[19] set (RV7-02).** Path: open_items/48

NEW: rev4b (227 (5)): pcf_tmax 0.8 s CONFIRMED by Electronics v2.11 S17 for W10 < 6 m/s with conditions (relight_conditions.s17_v2p11_conditions); the lit side on Combustion v2.4b / v2.4c: 3 of 72 P4c corners below 37.16 N in the window (OI-FMIN-LIT). CLOSED as a GNC input; the conditions are open items. Owner: lead (record)

**[20] append to open_items (becomes index 53).**

NEW: OI-FC-PC-BRANCH (Electronics v2.11, REV-ELEC-3 R3-04): the FC Pc branch of the release predicate ((Pc valid AND Pc >= 300 kPa abs)) releases every normal-family run at the E2 frame in S17 (Pc_f at E2 3.04 bar abs, 0.04 bar above the threshold), including runs that flame out 1-50 ms later, outside R2 (no drogue held): a released-dead-vehicle path with Pc valid. GNC / FC owner states the branch margin or moves it (branch off until the flame-out window has passed, or a threshold with margin over the E2 value), then GNC re-flies the release statistics. Owner: GNC / FC owner

**[21] append to open_items (index 54).**

NEW: OI-PHOTODIODE-VIEW (HIGH; REV-COMB-4, Electronics v2.11): pcf_tmax 0.8 s (W10 < 6 m/s, 227 (5)) holds on the dead side only with the photodiode main-chamber view (FLAMEOUT_OPT armed) or the GNC reference re-taken at the ECU E2 / light; photodiode-blind families release 42 / 98 of 1000 dead runs at 0.8 s (normal_noopt / starved040_noopt, flush on, reference none) [SIM S17]. Closes at IGN-1. Owner: Combustion / Mechanical (view), GNC (reference option)

**[22] append to open_items (index 55; RV7-07).**

NEW: OI-FMIN-LIT (230 (5); Electronics v2.11; REV-COMB-4 R4-03): at the 0.21776 mm start-level lift 3 of 72 P4c corners never reach 37.16 N within the 0.8 s window (F_min 33.14 N torch 0; one crosses at E2 + 0.857 s); with the flush such a lit run is not released, the drogue is held and the relight is aborted at t_E2 + 0.8 s: a lost relight in the Pc-invalid branch; 37.16 N and 0.8 s are kept (a 33.14 N threshold is below the 35.92 N dead-side maximum at cold flow x 1.3). The start-level lift is TO-VERIFY at CF-3 (230 (4)). Owner: GNC / lead, Combustion (CF-3)

**[23] append to open_items (index 56; RV7-06).**

NEW: R3-01 (REV-ELEC-3 MAJOR; lead 253 (7)(iii) HELD): the C1 transducer thermal zero is not in the re-zero / BASE limits; a negative drift loses the A1 relight (PC_SENSOR) at k = maximum / typical coefficient >= 1.46 (node T1_head_top_bracket_foot) / 1.02 (head_bore_N2O) in the kBpc1Shown build and >= 2.18 / 1.53 in the default build; a positive drift of 1.05 bar or more gives TORCH_FAULT at k >= about 3.1 / 2.15; re-zero2 is rejected at k >= 1.024 / 0.648 (REVIEWER DERIVED on Mechanical's A1 seat history, typical 0.0248 bar/K; the maximum coefficient is MISSING, F-10). Outcome when it trips: lost relight, drogue descent, vehicle loss. GNC's A1 P does not include it (the SIL has no thermal drift; S13 A 0 / 500 BASE_AMB is structural). Owner: Electronics v2.12 (R3-01 items 1-8), Mechanical (seat node), founders (F-10); GNC re-flies the relight outcome on the S13 A re-run with the drift model

**[24] append to open_items (index 57; RV7-04).**

NEW: PURGE condition (d) (257 (2)): kPurgeFlow_s and the both-open cap re-set from the CF-4 / B-BLEED-1 measured N2O Cd x A (upper 95 % bound) with the mass flow at 297.15 K, never above 2.43 / 2.39 s, and CF-4 shows the 283.15 K need at the re-set flow; without the re-set, measured Cd x A <= 1.08 x the Cd 0.70 value or GNC re-runs the A1 reserve test at the measured vent (purge_bound.note_256_2). Owner: Combustion / Electronics (CF-4, constants), GNC (reserve test if needed)

**[25] replace (RV7-02).** Path: fmea_inputs_rev2p1/status_rev4b

OLD: frame-noise budget pending (227 (6))

NEW: FC frame-noise budget <= 2.51 N rms iid at 0.8 s (Electronics v2.11 S17, 0 of 2000 dead evaluations released with hold + flush, margin +4.954 N; +1.242 N at cold flow x 1.3); with the FC Pc branch on, a run that flames out 1-50 ms after E2 is released at the E2 frame (OI-FC-PC-BRANCH)

**[26] append to fmea_inputs_rev2p1/v (RV7-05).**

NEW: unprimed or UNKNOWN line at the A1 relight with the bleed fitted: relight refused (253 (7)(iv)); no RUN, no drogue release, drogue descent to touchdown at about -22 m/s (rev2 amendment V), vehicle loss; probability not quantified (PRIMED flag owner)

**[27] replace (RV7-02).** Path: requirements/launch_commit_rev2p1/v/1/why_rev4b

OLD: the frame-noise budget is pending (227 (6); at 5 N rms iid ASSUMED the bounding run releases with probability 18.4 % at 0.8 s, RV6-07 DERIVED)

NEW: the FC frame-noise budget is <= 2.51 N rms iid at 0.8 s (Electronics v2.11 S17; at 5 N rms iid ASSUMED the bounding run releases with probability 18.4 % on GNC's design maxima, 22.9 % on the S17 plant)

**[28] rename (RV7-04).**
- Key: flight_software/relight_sequence_placeholder/v/purge_bound/note_rev4b
- New key: note_rev4b_superseded_256_2
- The content is unchanged.

**[29] set (RV7-04).** Path: flight_software/relight_sequence_placeholder/v/purge_bound/note_256_2

NEW: PURGE FINAL (lead 256 (2) and 257 (2); combustion.json v2.4c purge_decision_v2p4c): scheduled flow 2.43 s (both-open overlap 2.38 s + 0.05 s) with the 2.39 s both-open cap (2.44 s of flow at the cap); needed flow 2.2 / 1.9 / 1.8 s at 283.15 / 289.5 / 297.15 K unlined (lined, 283.15 K needs 2.5 s); margins at 2.43 s 0.23 / 0.53 / 0.63 s (0.18 / 0.13 s at 283.15 K with the FD-01 element bounds); vented N2O at the ASSUMED Cd 0.70 66.7 / 70.8 / 75.1 g at 2.43 s (bound law 66.4 / 70.7 / 75.4 g, 75.75 g at the cap) [DERIVED by REV-COMB-4 on Combustion's SIM model]. At Cd 0.80 the fixed schedule vents about 80.5 g at 289.5 K and 85.5 g (85.8 g at the cap) at 297.15 K [ESTIMATE]. A1 reserve (line-208 test against the v3d reference, A1 210 m, v351, N = 500 per base, dip onset 80 g; vented mass above the flown G73 / G80 as a per-run liquid shift, ESTIMATE above 80 g; REV-GNC-7): 76 g UB95 0.854 pp liquid / 0.617 pp powered, PASS; 80.5 g 0.972 / 0.617 pp, PASS (margin 0.028 pp); the liquid test first fails at 82.1 g (1.089 pp); 85.5-85.8 g 1.206 pp liquid, FAIL (powered 0.736 pp passes) [DERIVED from SIM]; relight_ok 1.000 in every flown base (G73 / G80). The 76 g basis stays (G73 decided, G80 sensitivity). Condition (d) (257 (2)): after CF-4 / B-BLEED-1, kPurgeFlow_s and the cap are re-set from the measured Cd x A by the measured-time form with the mass flow at 297.15 K, never above 2.43 / 2.39 s, so the 297.15 K vent stays <= 76 g at any measured Cd x A (REV-GNC-7 check, scheduled overlap 10 ms under the cap: vent at the cap <= 75.99 g for Cd x A ratios 1.0-2.0; 283.15 K margin 0.23 / 0.21 / 0.21 / 0.19 / 0.18 s at ratios 1.00 / 1.08 / 1.13 / 1.20 / 1.30, 0.10-0.18 s with the FD-01 element bounds over 1.0-1.3, positive to ratio 2.0; need scaling 1 / (Cd x A) ASSUMED); the re-set takes the upper 95 % bound of the measured N2O Cd x A (a cap set from a ratio measured 7.9 % low vents 82.0 g at 297.15 K, just under the 82.1 g where the line-208 test first fails), and CF-4 shows the 283.15 K need at the re-set flow (else the cold corner stays model-only and the 1 / (Cd x A) need scaling ASSUMED); without the re-set: measured Cd x A <= 1.08 x the Cd 0.70 value (vent <= 82 g at the cap), else GNC re-runs the A1 reserve test at the measured vent. Below a ratio of 1 condition (b) of 256 (2) governs (>= 0.91, >= 0.95 with the FD-01 bound). The 14.5 g value and the reserve_frac_minus_purge_bound entries are superseded evidence (note_rev2)

**[30] set (RV7-04).** Path: v32_items_rev4b/items/9/status_after_rev_gnc_7

NEW: text superseded by 256 (2) / 257 (2) (2.43 s flow, 2.39 s cap, condition (d)): purge_bound.note_256_2

**[31] replace (RV7-04).** Path: lead_decisions_2026-10-19/rev4b_lines_204_227/reference_lines/203 (3)

OLD: purge: ECU both-open cap <= 2.55 s (v32_items_rev4b [9])

NEW: purge: ECU both-open cap <= 2.55 s (v32_items_rev4b [9]; superseded by 256 (2): 2.43 s flow, 2.39 s cap, purge_bound.note_256_2)

**[32] set (RV7-12).** Path: duty_cycles/note_n07_rev_gnc_7

NEW: N-07 (REV-ELEC-3, routed to REV-GNC-7 by 256 (5)): no GNC objective needs the DC-D v2 duty (49.27 s thrust-on in burns of 31.76 / 7.75 / 9.76 s; 6.31 kg N2O on the v2 map, 7.02 kg on the S230 map) as one firing in Combustion's T4. GNC's static-fire objectives (flight_profile.test_campaign[1] 'T1 static fires (DC-D)', requests[15], over_thrust_fc_thrust.v.refutation[0] and .v.unknowns[1]) need DC-D segments, not its length: throttle map and Pc loop (staircase 500 -> 62.5 N, throttle 1.0 -> 0.125, 0.90-12.50 s, 1.47 kg N2O; steps 100 <-> 500 N, 12.50-16.52 s, 0.59 kg; sweep 175-399 N, 16.52-24.51 s, 1.16 kg; burn 2 triangle up to 428 N, 0.94 kg; burn 3 hold at 130 N, throttle 0.26, 0.60 kg), F_acc against the load cell at >= 450 N and the IMU vibration at F_max (10.13 s at >= 450 N in DC-D v2, 5.9 s of it in the 500 N hold of 24.51-30.52 s, 1.44 kg), gimbal sweeps, thrust-vector alignment, roll torque and rocking mode under thrust, and >= 30 starts for the ignition-latency distribution (a count; 3 per DC-D run) [DERIVED from the DC-D v2 file 9c5d7cf391d8297b, v2 basis]. Each can be flown as its own segment or firing inside the A = 150 C limit (N-07: the DC-D first burn would cross at about 23.5 s, merged bound); the DC-D v2 relights (coasts 10.25 / 8.25 s after a 31.76 s burn) do not represent the A1 relight (A1 p99 record: 3.78 s at 0.88, coast to 22.79 s, 4.59 s at 0.47), so the A1-like relight objective sits with REV-COMB-4's shortest T4 firing (B1 p99 burn 21.76 s, coast about 19 s, one relight of about 4.6 s at about 0.47; about 2.0 kg). qualification_check (DC-D 2.089 x the dispersed longest burn) is a record of the v2 sequence, not a GNC requirement. Naming: GNC's test_campaign T4 is the drogue drop test; Combustion's T4 is the DC-D firing of the T1-T4 regression series

**[33] replace (RV7-08).** Path: status

OLD: (9) Carried from v3.1 unchanged:

NEW: (9a) REV-GNC-7 folds (lead 250 (6), 253 (7), 256 (2), 257 (2)): the R3 K band and the ENG-11 check on CAD v3.5.2 (requirements.gimbal.tvc_actuator.ENG-11_servo_output_stiffness.k_band_r3_v352); the S17 v2.11 conditions of pcf_tmax 0.8 s for W10 < 6 m/s (227 (5); requirements.ignition.relight_conditions.s17_v2p11_conditions); the lost-relight outcome (relight_conditions.unprimed_or_unknown_line); the final purge with condition (d) (purge_bound.note_256_2); open items OI-FC-PC-BRANCH, OI-PHOTODIODE-VIEW, OI-FMIN-LIT, R3-01 and purge condition (d). (9) Carried from v3.1 unchanged:

=====================================================================
APPENDIX B: DATASHEET-INPUTS-GNC.md OPERATIONS (exact; each OLD occurs exactly once in 9aacdefaaa0df250)
=====================================================================
**[DS 1] row 5, basis paragraph (RV7-09)**

OLD: The ENG-11 FE-plant re-run is staged separately in `rev4b/eng11_fe/` and is not folded into the v3.2 text.

NEW: The ENG-11 FE-plant re-run (CAD v3.5.1, `rev4b/eng11_fe/`) and REV-GNC-7's check on the CAD v3.5.2 R3 pose table and K band are folded into the v3.2 text (ENG-11_servo_output_stiffness, k_band_r3_v352).

**[DS 2] row 8, sentence (RV7-01, RV7-09, (e))**

OLD: **Design-to 100-120 N m/rad at the nominal servo J 1.6e-3 kg m2 (cons): the V5c window (100-130) intersected with the CAD v3.5.1 FE window (<= 90-120).** It is **not robust**: it moves with J (FE, cons: 0.76e-3 130->= 160; 2.7e-3 120->= 160), the inertia convention (n48 at J 1.6e-3: none) and the rotor model (two-mass: 150->= 160), and it is empty at 0.9 x first bending.

NEW: **Design-to 100-110 N m/rad at the nominal servo J 1.6e-3 kg m2 (cons): the V5c window (100-130, CAD v3.3) intersected with the CAD v3.5.2 FE window (R3 pose table: <= 90-110).** Only 100 N m/rad also passes at both ends of the R3 K band (band maximum <= 90-100, band minimum <= 90-115, 150->= 160). It is **not robust**: it moves with J (R3 pose table, cons: 0.76e-3 130->= 160; 2.7e-3 120->= 160; no K_s passes at all three J), the inertia convention (n48 at J 1.6e-3, CAD v3.5.1: none) and the rotor model (two-mass, CAD v3.5.1: 150->= 160), and it is empty at 0.9 x first bending (CAD v3.5.1).

**[DS 3] row 8, evidence (RV7-09)**

OLD: DERIVED (linear ENG-07d, one fixed ECU notch, K_s grid 90-160 step 5, edges +-5 N m/rad); PROPOSAL for the lead (227 (3) keeps the decision); REV-GNC-7 check pending

NEW: DERIVED (linear ENG-07d, one fixed ECU notch, K_s grid 90-160 step 5, edges +-5 N m/rad); CAD v3.5.2 R3 plant and band ends checked by REV-GNC-7 (the 100-120 of CAD v3.5.1 does not hold on CAD v3.5.2); PROPOSAL for the lead (227 (3) keeps the decision)

**[DS 4] row 8, source (RV7-09)**

OLD: J_2.7_cons_FE 125->= 160;

NEW: J_2.7_cons_FE 125->= 160 (set by A10, compliant + hot E -10 %; the row's 120->= 160 is the rigid T_REF variant A03);

**[DS 5] row 11b (RV7-09)**

OLD: The re-run is delivered as DERIVED in `rev4b/eng11_fe/` (row 8). It needs the REV-GNC delta check before the datasheet quotes a window.

NEW: The CAD v3.5.1 re-run (`rev4b/eng11_fe/`) and REV-GNC-7's CAD v3.5.2 check are done (row 8; design-to 100-110 N m/rad on CAD v3.5.2). Remaining: B-TVC-1 and the bending mode.

**[DS 6] row 11f (RV7-02, RV7-09)**

OLD: Electronics v2.11 implements the mode-3 filter re-initialisation at the Pc-invalid onset and runs S17. Electronics states the FC frame-noise budget against the +5.3 to +6.0 N mode-3 margin. pcf_tmax 0.8 s is confirmed or returned to the lead. Combustion v2.4b supplies the lit side.

NEW: Electronics v2.11 S17 CONFIRMED pcf_tmax 0.8 s for W10 < 6 m/s with conditions: the ECU R2 hold, the mode-3 flush, the photodiode main-chamber view (or the reference re-taken), the FC Pc branch off or moved with margin (OI-FC-PC-BRANCH), FC frame noise <= 2.51 N rms iid at 0.8 s, cold flow x 1.3 margin +1.242 N. Lit side: 3 of 72 P4c corners stay below 37.16 N (OI-FMIN-LIT). GNC re-runs R2 v2 with the flush.

**[DS 7] carried-unchanged list (RV7-09)**

OLD: - pcf_tmax is 0.8 s for the W10 < 6 m/s envelope (227 (5)).

NEW: - (changed in v3.2, not carried: v3.1 had 0.5 s, line 181 (4)) pcf_tmax is 0.8 s for the W10 < 6 m/s envelope (227 (5)), CONFIRMED by Electronics v2.11 S17 with conditions (row 11f).

END REVIEW-GNC-R5
```
