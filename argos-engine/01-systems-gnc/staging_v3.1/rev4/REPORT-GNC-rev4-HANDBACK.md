BEGIN GNC-REV4-HANDBACK

GNC rev4 is finished, staged in the hub and logged in the CHANGELOG. gnc.json is not written: v3.2 waits for REV-GNC-5's delta re-check. Every figure is SIM, DERIVED, ASSUMED or TO-VERIFY. There is no hardware data, and none of this is physical approval.

== CLAIM ==

**1. A1 apogee band = 210 m** on massprops v3.5.1 (488b47f9d55ff91b), line-208 rule, N=1000 per main base (SIM).
- liq|G73:
  - 210 m: P 0.9835 vs 0.986, -25/+20, p 0.55, UB95 0.80 pp → PASS.
  - 215 m: UB95 1.03 pp, fails the 1.0 pp bound by 0.03 pp. This is a statistical boundary, not a physical margin.
- pw|G73: band 220 m. The lower state sets the decision, so the band is 210 m.
- Remaining arms at 210/215 m (N=500 per base):
  - Four-base pooled (informational), 210 m: PASS on both states (liq UB95 0.595 pp, pw 0.277 pp).
  - G80 at 210 m: PASS (liq UB95 0.97 pp, pw 0.62 pp).
  - v351t (valve target): liq 210 m, pw ≥ 215 m.
  - v352: ≥ 215 m on both states. v351t and v352 were flown only at 210 and 215 m, so a 215 m reading is a lower limit (the true band may be higher).

**2. Landing mass: COVERED** (DERIVED from the P2 h210 tables). The rev4 210 m landing set covers the 16.15 kg v3.5.1 landing estimate.
- Dispersed touchdown mass 14.18–18.13 kg (p01 14.50, p50 16.03, p99 17.47 kg).
- 42–43 % of runs land at ≥ 16.15 kg, with P(80 g) 0.974–0.986 there, against 0.986–0.991 below. This comparison is unpaired, not a test.
- 52–53 % of runs exceed the 16.0 kg upper bound of landing_mass_window_kg in gnc.json v3.1. Proposal [11] widens the window.

**3. ENG-11 final requirement** (DERIVED, linear CSI; V5c structure; nominal J 1.6e-3 kg m²; fixed ECU notch Q1/-12 dB on the centre-pose mode ±5 %; ENG-07d GM ≥ 6 dB at every floor20 corner).
- K_s 58 N m/rad FAILS: GM 3.09 dB (alpha) / 0.34 dB (beta).
- On a 10 N m/rad grid from 70 to 270:
  - both axes pass at 100–130, at 190 and at 220–270 N m/rad;
  - they fail at 140–180 and 200–210.
- Margins inside 100–130 N m/rad:
  - upper GM ≥ 6.18 dB (alpha) / 6.03 dB (beta);
  - smallest |PM| over all gain crossings 23.8° / 23.3°;
  - modulus margin ≥ 0.354;
  - rigid-loop |PM| with the lowest notch ≥ 23.5°.
- Why the passing set is not a single interval:
  - The failures above 130 come from the full-tank engine rocking mode meeting the ASSUMED first bending mode (24.3 Hz full / 25.6 Hz landing, PETG tube).
  - Shifting the bending frequency by 0.9× / 1.1× flips 6 of 16 tested corners. At 0.9× bending, beta fails at K_s 116 / 145 / 174 (0.28 / 1.70 / 1.29 dB). This supports the bending hypothesis (its refutation criterion was not met).
  - No K_s in 58–174 N m/rad is robust to a −10 % bending error with one notch.
  - The window also fails at J 2.7e-3 (beta 5.9 dB at K_s 116) and with the n48 kinematics convention (2.8 dB).
- Proposed requirement:
  1. K_s ≥ 100 N m/rad, measured at B-TVC-1 together with J and the reflected-inertia convention. This replaces the interim "K_s ≥ 116".
  2. The vehicle first bending mode is MEASURED, or computed from the airframe FE, and the margins are re-run on it before K_s is frozen. At the ASSUMED bending mode, design to 100–130 N m/rad.
- The v1.1 ksmin/mink bisection values (alpha 157.0, beta 95.4) are SUPERSEDED: they assume pass/fail is monotone in K_s, which the grid refutes.
- 6-DOF (SIM, N=500 per base): no arm loses a landing, K_s 58 included. That model does not carry the linear flex corner set, so the requirement rests on the linear margins.
- Research proposal (not flown): a second notch on the measured bending mode.
  - Hypothesis: it removes the coincidence failures.
  - Comparator: the single notch.
  - Refutation: any corner below 6 dB for K_s 100–270 at 0.9–1.1× bending.

**4. RE-24** (SIM; sim6 v2.13-dev amendment J; N=500 per base; jam bound ASSUMED from the Electronics SIL).
- An UNDETECTED jam at the bound loses no landing: in each base and servo arm, 31 of 31 undetected runs land exactly as their no-jam twins (p = 1).
- 0 false GIMBAL_FAULT aborts in 1000 nominal flights. The largest no-jam monitor excursion is 0.18° against the 1.5° threshold.
- Detected landing-burn jams land 0.136–0.150 if flown on, and 0.084–0.088 with the abort (A1_none servo A: continue 42/469, abort 13/469).
- Coast and ascent jams are lost either way (P 0.000–0.002).
- Whether to inhibit the abort near touchdown is a safety decision for the lead; it is not proposed here.

**5. Payload** (separate table, v32 item [15]; SIM flights, DERIVED iso-margin and T/W, ASSUMED point payload at the A05 station z 1.15 m; tank moved to 0.58–1.08 m per the integration note, liftoff CG +7.5 mm).
- Monte Carlo N: 250 per base screen; 500 per base on the decision arms (same seed); liq state only.
- (a) Apogee loss per kg:

  | Payload | Equal-margin apogee (DERIVED) | Liftoff CG shift | MC band (line-208 rule, floor 180 m) |
  |---|---|---|---|
  | +0.5 kg | 181 m (58 m/kg) | +14.1 mm | 190 m (20 m, 40 m/kg) |
  | +1 kg | 155 m (55 m/kg) | +27.4 mm | none |
  | +2 kg | 117 m (47 m/kg) | +52 mm | none |
  | +3 kg | 91 m (40 m/kg) | +74 mm | none |

  - A relight-timeline floor near 180 m appears that the margin calculation does not see: the payload-0 vehicle itself fails the bound at 170 m and loses at 155 m.
  - +0.5 kg: 200 m fails the bound and 210 m loses (p 0.024).
  - +1 kg: 180 m fails the bound (UB95 1.64 pp) and 190–210 m lose.
  - +2 / +3 kg: P 0 at their equal-margin apogees.
- (b) Load to carry the payload to 210 m:
  - +1 kg: 2.20 kg N2O (3.48 L at 85 % fill, inner span 0.58–1.069 m, tube 0.509 m) → PASS: −9/+11, UB95 0.54 pp, N=500 per base.
  - +2 kg: NOT met.
    - 2.45 kg (3.88 L, inner 0.58–1.124 m, clashes with A05 at 1.15 m): UB95 2.10 pp.
    - 2.55 kg: loses (p 0.003) with zero exhaustion; the failures are touchdown tilt and lateral speed. More N2O does not fix +2 kg; it needs a landing-control and structure study.
- (c) Liftoff T/W / touchdown T/W / landing floor ratio:
  - 0 kg: 2.92 / 3.16 / 0.633;
  - +0.5 kg: 2.84 / 3.08 / 0.616;
  - +1 kg: 2.76 / 3.00 / 0.600;
  - +2 kg: 2.62 / 2.85 / 0.570;
  - +3 kg: 2.49 / 2.72 / 0.543;
  - +1 kg at 2.20 kg N2O: 2.72 / 2.95 / 0.590;
  - +2 kg at 2.45 kg N2O: 2.53 / 2.75 / 0.550.

**6. R2 v2 answers** (lead ~19:05Z 10-13; v32 items [6] and [14]).
- (a) Counting start and estimator flush, as implemented in sim6:
  - Counting starts on the first 1 ms step with E2 (the 6-DOF light, rel_dt 0) and Pc invalid (pcf_dt 0) both true. Frames are then taken every 10 ms from that step. The frame phase is tied to the counting start, which is TO-VERIFY against the flight FC.
  - The mode-3 filter (τ 20 ms) runs continuously and is NOT flushed. The reference is sampled at E2, with (vz/vz(E2))² drag compensation. Lit thrust therefore carries about 60 ms into a later flame-out.
  - GNC's flame-out set (never-lit cold flow, onsets 0/5/10 ms) does not contain a 10–20 ms flame-out after a light.
  - The sim gates release on engine-lit truth, so the released-dead-vehicle counts are counterfactual window statistics, not flown releases.
  - Proposal: re-initialise the filter at Pc-invalid onset, or count from onset + 3τ, then re-run after Electronics' S17 sweep.
- (b) The 20.85 N bound contains the modelled ADIS16470 noise: ~0.06 N rms after the filter (DERIVED, 100 µg/√Hz ASSUMED), plus the bias, scale and mass dispersions.
  - It does NOT contain a 5 N rms frame noise (~90× the modelled level), canopy breathing, FC jitter, or vibration of an unlit vehicle.
  - Estimate (DERIVED, independent frames ASSUMED): 5 N rms raises the window maximum of the 3-frame minimum by +4 N (median) to +8 N (p99). That is the whole +5.3 to +6.0 N margin at W10 < 6.
- (c) Starve threshold (SIM, gnc_dev7, A1_none pw, N=60):
  - 0.5 s window: all lit runs released up to 0.30 s; 5/60 aborted at 0.40 s, 56/60 at 0.45 s.
  - 0.8 s window: all released up to 0.60 s (W10 < 6: 0.65 s); 1/60 aborted at 0.65 s.
  - Release comes 0.08–0.12 s after the plateau ends. So the 0.5 s window has about 0 to −0.1 s margin over the 0.4 s top of the starve range; Electronics' 0.46–0.48 s is not reproduced. The 0.8 s window has ≥ 0.20 s margin.
  - The latest release at 0.8 s is E2 + 0.80 s, which precedes the ECU backstop at E2 + 0.8 s + margin.
  - Trade for the lead: 0.8 s releases 4/2072 dead vehicles at all winds but 0/1502 at W10 < 6.

**7. Contradictions recorded as evidence.**
- Gate-delay tolerance (R4-F5, DERIVED): the 285 m value does not carry to 210 m.
  - D_crit(2.1 s) min is 0.164 s on A1_none and −0.154 s on the pc bases (p01 0.58–0.67 s), against 3.765 s at 285 m.
  - 16/1000 runs commit with zero slack.
  - The P cost of a gate delay at 210 m is not flown.
- Line 213's "A1 duty cycle shortens" is NOT supported on v3.5.1 (R4-F6, DERIVED): the A1_none p99 engine-on time is 8.37–8.51 s, against 8.37 s at 285 m and the 8.258 s sizing counter. B1 governs sizing, so this is a record only.

**8. v3.2 proposals corrected per REV-GNC-5** (out_rev4/v32/v32_proposals_rev4.json).
- [0]–[4], [6] and [9] are corrected with RV5-01 to RV5-10.
- A1 = 210 m, with the 285 m figures as comparators.
- [5]: its condition (adoption of the 285 m trim) is not met, so the 285 m records are not added; the 210 m reading is added.
- [7], [8] and [10] are as written ([7] with the RV5-10 note).
- NEW items [11]–[15], not yet reviewed: landing-mass window, ENG-11, RE-24, R2 answers, payload.
- Withdrawn-value sidecars (rev3 unchanged, 487/487 OK at 19:00Z):
  - W1: the rh220/rh250 arms at E2 + 0.22 s;
  - W2: the lit model 62.5 N × pcf_k, including the 32 P4 gap_N/T_mid_N entries;
  - W3: the 60 g bands.

== CONFIGURATION ==

**Sim trees**
- Production: gnc_dev3, sim6 v2.9-dev (sim6 f90e0ba8e993ad60).
- gnc_dev7: sim6 v2.13-dev amendment J (sim6 f6a74a495474beab, run6 20eb901a3ec7e5d0).
- Bit-check v2.13 v1.1: off-parts ALL IDENTICAL, functional ALL PASS. The v1.0 FAILs (B2/B5) were wrong test expectations; their output is kept.

**Interfaces and pins**
- iface_v351 + pins_rev4_v351 (P2, ENG-11, payload, RE-24), plus the cfg ballast 0.99744 kg at 0.4426 m.
- iface_v3d + pins_rev3 (R2 starve, rev3 recompute).

**Statistics**
- Seed 101.
- Main bases A1_none + A1J_pc, paired exact McNemar.
- Dip onset 80 g; UB95 = d + 1.645·se with the Newcombe bound beside it.

**N used**

| Run | N |
|---|---|
| P2 band | 1000 per base |
| Other A1 arms | 500 per base |
| ENG-11 6-DOF | 500 per base |
| RE-24 | 500 per base |
| Payload | 250 per base screen, 500 per base decision arms |
| R2 starve | 60 (enough: 5/60 aborts at 0.40 s decides the 0.5 s window) |

== SOURCES ==
- CHANGELOG lines 203–217 (as read; 217 before my append).
- REVIEW-GNC-R3.md (RV5-01 to 13 and the verdict table).
- rev3_results.json e0f6e7611fe523b5.
- V5c gimbal_k_summary 82a737caa138259a.
- electronics.json v3 38bf149f368c1d4c.
- mechanical.json in iface_v351.

== FILES (hub staging_v3.1/rev4/; sha256 first 16) ==

| File | sha256/16 |
|---|---|
| MANIFEST_rev4.sha256 (1173 files, sha256sum -c OK, 138 MB; rev4_notes/PROGRESS.txt outside the manifest by design) | 083675a6abddaabe |
| out_rev4/rev4_results.json | 31eb2290c2e8c74b |
| out_rev4/v32/v32_proposals_rev4.json | 6fd6d66e08aef5d8 |
| out_rev4/v32/v32_new_items_rev4.json | 76b1944af3bc9a95 |
| out_rev4/p2/p2_rev4.json | 68cf1f643effd5b9 |
| out_rev4/p2/landing_mass_coverage_h210.json | d40472c8d92eaac9 |
| out_rev4/eng11/lin_v351/eng11_final.json | 47190558a3ae45e3 |
| out_rev4/eng11/lin_v351/eng11_grid.json | 540a11f66863dbda |
| out_rev4/eng11/fly_v351_h210/eng11_fly.json | 600a9708c35586b8 |
| out_rev4/re24/v351_h210/re24.json | b2e784adbfe205be |
| out_rev4/bitcheck_v213/bitcheck_v213_func.json | 1f4b6d7aa78de31d |
| out_rev4/bitcheck_v213/bitcheck_v213_offparts.json | 4f4449fde2c8bd3b |
| out_rev4/payload/payload_rev4.json (N250) | 0b8f9a48792aad1e |
| out_rev4/payload_n500/payload_rev4.json | 6d62104dac3f4fcd |
| out_rev4/r2_starve/r2_starve.json | d743193bd5bdf88b |
| out_rev4/v32/v32_recompute.json | 0eea0a1754212961 |
| out_rev4/v32/dcrit_210.json | 51f430824a5ad09c |
| withdrawn_markers/WITHDRAWN_INDEX.json | 9a652a75813fada2 |

Also staged:
- sim/: the gnc_dev3 v2.9-dev, gnc_dev4 v2.10, gnc_dev5 v2.11 and gnc_dev7 v2.13-dev trees (gncsim + scripts, no caches), their shared data/, iface_v3c, iface_v351, iface_v352, and iface_v352L (marked WITHDRAWN).
- pins/pins_rev4/.
- NOT_STAGED_rev4.txt: the 415 cache files.

Scripts (sha256/16):

| Script | sha256/16 |
|---|---|
| m2_rev4_p2 | a0688a06a7adcc3e |
| m2_eng11 v1.1 | aaad9a07a0551b9b |
| m2_eng11_grid v1.0 | 0067f643262fc379 |
| m2_eng11_fly | b8bd069aef7e92ea |
| m2_rev4_payload v1.1 | 4cb365cf62edb408 |
| m2_rev4_v32fix | db4ed415e8ee41fb |
| m2_rev4_wmark | 9d2343c104694954 |
| m2_rev4_report | f4ab037c2c98debc |
| m2_rev4_v32new | f3ed7deffef5ab90 |
| m2_rev4_v32prop | 89fbe1537648bf8f |
| stage_rev4.sh | 106dee9b4ec0d2ad |
| m2_re24 v1.1 | 973fac958a25bcb0 |
| m2_bitcheck_v213 v1.1 | e7b525d1ff2f597f |
| m2_r2_starve v1.0 | a016079e1a77f24c |

- CHANGELOG: line 218 appended, dated 2026-10-19. The line count was asserted at 217 first and read back after 10 s: 218 lines, file 32501d42f3ea31b9, line dffff032c1b7b75d.
- PROGRESS note: rev4_notes/PROGRESS.txt, updated.

== TESTS ==
- P2 references verified against MANIFEST_rev3.
- Payload repro: 0 mismatches on both bases; +1 kg moment check and tank-move check OK.
- RE-24 rec0 equals the P2 table on every run.
- ENG-11 self-check passed.
- Bit-check v2.13 v1.1 ALL PASS.
- MANIFEST_rev4 sha256sum -c OK.
- rev3 MANIFEST 487/487 OK.

== UNKNOWNS / TO-VERIFY (owner) ==
- First bending mode, full and landing (airframe owner / Mechanical).
- K_s, J and the reflected-inertia convention at B-TVC-1 (founders / Electronics).
- S17 sweep against GNC's R2 v2, then the mode-3 filter flush (Electronics, then GNC).
- Combustion v2.4b lit side (Combustion).
- FC frame phase and noise budget (Electronics).
- Payload inertia, station and longer-tank layout (payload owner / Mechanical).
- Bleed valve mass, 2 × 0.30 kg ASSUMED (Mechanical / supplier datasheet).

== NOT RUN / NEXT CLOSURE (GNC) ==
- 210 m coverage set (e19, L400, wind sweep).
- Gate-delay injection at 210 m.
- 210 m duty-cycle record re-flown with the recorder.
- ENG-11 second-notch study.
- v351t/v352 bands above 215 m, if the lead wants them.
- +2 kg landing-control study.

== STATEMENTS ==
- Nothing new installed.
- ENG-11 v1.0 'ends' run SUPERSEDED: its outputs were moved to out_rev4/eng11/superseded_v1.0/ with a note, replaced by v1.1 on v3.5.1 and the K_s grid.
- v352L arm WITHDRAWN by line 209 (realised −91.6 g); not flown.
- Other superseded scripts (archived in superseded_rev4/): m2_bitcheck_v213 v1.0 criteria, m2_re24 v1.0 (now gated), m2_rev4_payload v1.0.
- Process kills were refused by the auto-mode classifier earlier and were not retried. A run gate stopped the queued RE-24 duplicates instead, and a skip/lock check made the duplicate R2-starve job exit without flying.
- No other agents' processes were touched.
- Not written: gnc.json, REQUIREMENTS, SUPERVISION.json, reviews/, other subsystems' folders, rev1–rev3, /mnt/project-files.

END GNC-REV4-HANDBACK