# REVIEW-COMBUSTION-R4 (REV-COMB-4)

Independent delta re-review of Combustion v2.4b, stamped by the reviewer 2026-10-21T08:32:27Z (date -u); its interim went to the lead at 07:52:49Z. Saved here by the lead on 2026-10-21T08:38:49Z (date -u), verbatim from the reviewer's final message: the harness does not let a subagent write a report file, so the handback text is the review. Reviewer artefacts: `reviews/combustion/r4/` (`MANIFEST_REV-COMB-4.sha256` 996475830cae731f, 23 entries, verified by the lead 23/23 OK at 08:37:28Z). Reviewed set: `02-combustion/` v2.4b (REPORT.md d8b795478d4013ee) and `interfaces/combustion.json` v2.4b (fd3a7da6d27c7c66); inputs with full sha256 in `reviews/combustion/r4/r4_inputs.sha256` (802b57945d3d69d6). Lead disposition: CHANGELOG line 256. A verdict is not physical approval: no hardware exists.

```text
BEGIN REVIEW-COMBUSTION-R4

REV-COMB-4: independent delta re-review of Combustion v2.4b. Author: Combustion and Propulsion. Reviewer: REV-COMB-4. Stamp 2026-10-21T08:32:27Z (from date -u). Interim sent 2026-10-21T07:52:49Z. Anything new or changed since then is marked [DELTA].

What I read:
- REPORT.md v2.4b d8b795478d4013ee
- interfaces/combustion.json v2.4b fd3a7da6d27c7c66
- REVISION-RESPONSE-R3 21791d15dc88eaeb
- DATASHEET-INPUTS-COMBUSTION 46a8222018666b1d
- HANDBACK-SUMMARY d12c8862bf5524a4
- CF-4-SPEC v2.1 60bbc51f6f487682
- T1-T4 v3 b0c42b09ba47cb9c
- CHANGELOG 427d7944be3f1733 (255 lines)
- mechanical.json v2.2, read at 03-cad/v3.5.2/history/mechanical.json.f790d31b5ca7d954. I did not read the current mechanical.json 55397a9b8ddb59be.
- Every input, with its full sha256, is listed in reviews/combustion/r4/r4_inputs.sha256.

A reproduced number shows that a computation repeats, not that the physics is right. Nothing here is physical approval.

## 0. Verdict

**ACCEPT WITH CORRECTIONS.**
- Combustion needs no re-run. Every correction it owns is text for v2.4c (findings R4-03 to R4-08 and the notes).
- Two MAJOR items are owned outside Combustion's documents, both by Mechanical:
  - R4-01 (P_torch): answered, and closes when Mechanical publishes the tap-wall v2 row.
  - R4-02 (Z3 restatement): open.
- Line 230:
  - (1) to (4): CONFIRMED.
  - (5): CONFIRMED as a decision. Its supporting sentence is REFUTED for 1 of the 3 corners (R4-03).
- R3: all 17 items are closed. 10 CLOSED, 7 CLOSED WITH RESIDUAL, 0 OPEN.
- Count: 0 BLOCKING, 2 MAJOR, 11 MINOR, 5 NOTE.

## 1. Findings

### R4-01 MAJOR (Mechanical; Combustion text). P_torch during FA-1. ANSWERED, closes on publication.

**What I found.** 102 bar abs does not cover the torch passage during FA-1.
- Model: my linear lossless two-segment waveguide, ASSUMED (r4_torch_passage).
- Tap station peak: 129.85 bar abs at c 150 m/s, 121.96 at c 181, 116.61 at c 202, 108.00 at c 222.
- Cases above 102 bar abs at the tap: 48 / 42 / 36 / 12 at those four sound speeds, and 22 at c 400-450.
- Closed seat: up to 148.72 bar abs.
- No case exceeds 151.04 bar abs at any c from 150 to 1200 m/s [DERIVED].

**Mechanical's re-check** (the lead's 08:16Z notice). I read the work-tree file jfwd_tapwall_v352_v2.json (9f8849412d4419d7) at FA1S 151.04 bar abs, uniform over the passage:
- σ 136.9 MPa.
- MS_y +0.670 and MS_u +0.785 at the thread temperature (SOAK52).
- MS_y +0.294 at the screw temperature (SOAK52). The screw-temperature sensitivity governs at SOAK70: +0.275.
- Lamé factor 2.2094 [CALC on SIM].
- My linear-term estimate gave +0.671 / +0.787 / +0.295 / +0.275, which agrees to within 0.002.

**DLF 1.0: no separate finding.** Mechanical applies the 151.04 bar abs load with a dynamic load factor (DLF) of 1.0. That is acceptable for two reasons:
- 151.04 exceeds my linear tap peak by at least 16 % (129.85 at c 150; 24 % at c ≥ 181). So a local ligament DLF up to 1.16 is already covered.
- The tap-ligament local mode should sit far above the passage periods (0.29-2.02 ms).

Mechanical should state the ligament's lowest local natural frequency in the published row, expected well above 10 kHz.

**Residual, not modelled:** wave steepening and shock reflection, losses, torch-chamber compliance, N2O decomposition, and a blocked-outlet deflagration.

**Correction (combustion.json FA-1 block and Mechanical row):** "P_torch during FA-1: design case FA1S 151.04 bar abs uniform over the passage (REV-COMB-4 R4-01); linear lossless passage peaks <= 129.9 bar abs at the J-FWD tap and <= 148.7 at the torch seat for c 150-1200 m/s; the band values 94 / 121 / 147 / 94 do not bound gas-filled passages."

### R4-02 MAJOR (Mechanical owns LC-TB70; Electronics S6R). Z3 must be restated. OPEN.

**The peaks are real SIM bracket cases, not an artefact.** v2.4b histories equal v2.4a to 1e-9. Counts over the 896 cases:

| Grid | Cases | Peak above 75.519 / 63.1 / 60 bar abs |
|---|---|---|
| All | 896 | 46 / 141 / 185 |
| Baseline | 168 | 5 / 19 / 26 |
| as_written | 448 | 28 above 75.519 (max 88.02) |

- By O/F: OF4 has 11 cases above Z3 (max 88.02); OF8 has 1 (75.85); OF10 and OF12 have none.
- All 46 are outside Z3 by peak only:
  - time above 63.1 bar abs is at most 1.669 ms (limit 3.0 ms);
  - the 10-90 % rise is at least 0.842 ms (limit 0.8 ms);
  - time above 75.519 is at most 0.699 ms.

**Raising only the ceiling does not work.** If the ceiling were raised to 88.1 bar abs with the same shape limits, admissible trapezoids reach an equivalent static pressure (ESP) of 171.45 / 165.03 / 152.60 bar abs at 3.0 / 1.7 / 1.0 ms above 63.1. All exceed FA1S. Z3 as written reaches 147.29 [DERIVED, r4_z3_pulse_check].

**Correction for lc_tb70 (proposed Z3'):** "Z3': head peak <= 88.1 bar abs AND undamped SDOF ESP of the head history <= 151.04 bar abs at every period 0.02-50 ms (every FA-1 grid case meets it: max 146.88 at 3.5 ms)". Alternatives are tighter shape limits that imply this, or a higher FA1S.

**Who acts:**
- Electronics re-classifies the 10 S6R runs and the 29-33 N-04 burn-on cases against Z3'.
- Combustion adds the grid statistics above to combustion.json. No re-run.

### R4-03 MINOR (Combustion). P4c supporting sentence is false for one corner [DELTA].

The sentence "a longer window does not rescue them (F at 1 s >= 36.33 N)" is false for corner Cd0.65|a0.6|n0.68|ri0.3|eta0.85:
- It crosses 37.16 N at 0.872 s after the light, which is E2 + 0.857 s with torch 0 and E2 + 0.855 s with torch 0.3.
- F at 1 s is 37.28 N.
- The other two corners stay below 37.16 N to the end of the 1.0 s record (36.33 / 36.80 N, still rising).

**Correction for p4c_lit_side_v2p4b.v.implications.pcf_tmax, REPORT §16.7 (REPORT.md:3109) and RESPONSE §9 item 3:** "lit side at 0.21776 mm, torch 0: every corner that reaches 37.16 N within E2 + 0.857 s does so by E2 + 0.205 s (+3 frames: 0.235 s); 3 of 72 corners never reach 37.16 N in the 0.5 or 0.8 s window: one (Cd0.65|a0.6|n0.68|ri0.3|eta0.85) crosses at E2 + 0.857 s (a window >= 0.887 s with 3 frames would rescue it), the other two stay below 37.16 N to the end of the 1.0 s record (36.33 / 36.80 N, still rising); the count is the same for every window from 0.235 to 0.857 s, so pcf_tmax 0.8 s (227 (5)) is not limited by the lit side; the low corners are a threshold matter (GNC / lead)."

### R4-04 MINOR (Combustion). pcf_tmax 0.5 s texts are stale after LEAD 227 (5) [DELTA].

227 (5) adopted 0.8 s, and line 232 confirms the reversal.

| Location | Current text | Replace with |
|---|---|---|
| combustion.json drogue_release_hold.v.line175_5_note_v2p4a | "otherwise hold the drogue and ECU ABORT at t_E2 + 0.5 s: pcf_tmax 0.5 s, LEAD 181 (4); 0.8 s not adopted)" | "otherwise hold the drogue and ECU ABORT at t_E2 + 0.8 s: pcf_tmax 0.8 s, ADOPTED by LEAD 227 (5) for the W10 < 6 m/s launch-commit envelope (reverses 181 (4); Electronics v2.11 S17 confirms or returns it))" |
| combustion.json superseded_v2p4b.v["ABORT at t_E2 + 0.8 s"] | "t_E2 + 0.5 s (181 (4))" | delete the entry, or "t_E2 + 0.5 s (181 (4)); reversed by LEAD 227 (5): t_E2 + 0.8 s is current" |
| REPORT 1807 | "ABORT at t_E2 + 0.5 s (pcf_tmax 0.5 s, line 181 (4); the 0.8 s of the v2.4a text is superseded)" | "ABORT at t_E2 + 0.8 s (pcf_tmax 0.8 s, ADOPTED by line 227 (5); the 0.5 s of line 181 (4) is superseded)" |
| REPORT 2639, column 2 | "Line 181 (4) set pcf_tmax 0.5 s" | "181 (4) set 0.5 s; 227 (5) re-adopted 0.8 s" |
| REPORT 2639, column 3 | (as is) | "Current: t_E2 + 0.8 s" |

The history leaf line175_5_note_v2p4a_superseded.why is left as it is.

### R4-05 MINOR (Combustion). "112 bar abs" proof texts are stale after 249 (4).

249 (4) sets the proof at ≥ 166 bar abs (1.1 x FA1S). The handback says 4 places; I found 7 leaves (r4_stale_scan). Write 166.14, because 166 and 166.1 understate 1.1 x 151.04 = 166.144. The C1 pick (206.8 bar abs) meets either.

combustion.json:
- (1) igniter.sequence.v.arm_preconditions[3] and (2) open_interface_issues[5].status: replace the 112 clause with "proof >= 166.14 bar abs (1.1 x FA1S 151.04; LEAD 249 (4)); C1 Kulite XTL-190SM-2000A 206.8 bar abs (DATASHEET 1.5x rule) meets it; OI-41 DECIDED by LEAD 230 (2)".
- (3) pc_dynamic_channel.v.stand: "flush mount (path period <= 0.1 ms) >= 103.4 bar abs (1.1 x 94); 0.1-1 ms path >= 133.1 bar abs (1.1 x 121); the flight unit's >= 166.14 bar abs (LEAD 249 (4)) covers every path period; range >= 100 bar abs flush, >= 132 bar abs with a sense line (REV-COMB-4 R4-09)".
- (4) pc_dynamic_channel.v.flight: "proof >= 166.14 bar abs (1.1 x FA1S; LEAD 249 (4))".
- (5) pc_dynamic_channel.v.stand_proof_rating_v2p4b.v.rule: "(flight unit: 1.1 x FA1S = 166.14 bar abs, LEAD 249 (4))".
- (6) pc_dynamic_channel.v.stand_proof_rating_v2p4b.v.contradiction and (7) fa1_spectra_v2p4b.v.contradiction: "RESOLVED by LEAD 230 (2) (band values 94 / 121 / 147 / 94 bar abs; FA1S bounds every period) and 249 (4) (flight Pc proof >= 166.14 bar abs)".

Apply the same substitutions to:
- REPORT lines 50, 1175, 1866, 2106, 2279, 2396, 2408, 2520, 2553;
- T1-T4 line 83.

### R4-06 MINOR (Combustion). "E0 + 0.15 s" texts are stale.

Electronics v4 sets the closure deadline at 160 ms = E0 + 0.16 s = kTorchGate_s. The handback says 3 places; I found 4 leaves.

| Location | Replace with |
|---|---|
| igniter.sequence.v.start[0].action, "(Electronics: E0 + 0.15 s)" | "(Electronics v4: E0 + 0.16 s = the torch gate, 160 ms, kTorchGate_s)" |
| abort_matrix_v2p4.v.A14 | "(closure deadline = torch gate, E0 + 0.16 s; Electronics v4)" |
| cf4_gate.v.pass_criteria[5] | "(Electronics v4: E0 + 0.16 s)" |
| start[0].action_superseded.v | keep as history; append "superseded: Electronics v4 E0 + 0.16 s" |
| REPORT 461, 740, 1788, 1888, 1968, 2433; CF-4 lines 15 and 103 | same substitution |

### R4-07 MINOR (Combustion; CF-4). Purge cold corner and conditions.

**What I found** (DERIVED sensitivity on the author's model; 289.5 K reproduced exactly):
- Decided unlined path: the needed flow is 2.2 s at 283.15 K, 1.9 s at 289.5 K and 1.8 s at 297.15 K.
- So 2.43 s holds, with margins of 0.23 / 0.53 / 0.63 s. At the cold corner the margin falls to 0.18 / 0.13 s with the FD-01 element bounds (interim).
- [DELTA] With a lining, 283.15 K needs 2.5 s: P_abort is 0.061 at 2.43 s. So 2.43 s also requires that the line stays unlined, as decided.
- CF-4 tests only 286.7-289.5 K (line 64).

**Texts:**
- REPORT 24: "Needed flow time 1.9 s at the 289.5 K basis (<= 1.94 s with the FD-01 element) and 2.2 s at the 283.15 K relight corner (REV-COMB-4); the decided 2.43 s flow (LEAD 253 (7)(ii)) covers 283.15-297.15 K unlined".
- REPORT 519: append "(283.15 K: 2.2 s unlined, 2.5 s lined; REV-COMB-4)".
- CF-4 35: "needs 1.9 s of flow at 289.5 K (<= 1.94 s with the FD-01 element) and 2.2 s at 283.15 K (REV-COMB-4)".
- CF-4 §4 / C-R3: add a run at or below 283.15 K, or state that the cold corner is model-only.
- CF-4 P5: add "measured Cd x A of the two-tap path >= 0.91 x the Cd 0.70 value (>= 0.95 x with the 4x FD-01 element bound), else re-size the flow".

**Vented N2O at 2.43 s, unlined, Cd 0.70:** at most 66.7 / 70.8 / 75.1 g at 283.15 / 289.5 / 297.15 K. On the bound law: 66.4 / 70.7 / 75.4 g; at the 2.44 s cap, 75.75 g.
- [DELTA] At Cd 0.80 the vented mass is about 80.5 g (2.43 x 33.13, average-rate estimate). This is above the 76 g basis and is for GNC (REV-GNC-7).

### R4-08 MINOR (Combustion). Open-item statuses and datasheet rows are stale after 230, 249 and 253.

**OI-41** (REPORT 2560; open_items_v2p4b.v[0]): "DECIDED by LEAD 230 (2) (final on REV-COMB-4): band values 94 / 121 / 147 / 94 bar abs for structural SDOF paths; FA1S 151.04 bar abs bounds every period and case (max 146.88, margin 4.16 bar) and is the design case for pressure-filled passages; per-mode values are an analysis path only; flight Pc proof >= 166.14 bar abs (249 (4))".

**OI-42** (REPORT 2561; v[1]): "2.43 s scheduled flow with the 2.39 s cap ADOPTED (253 (7)(ii); final on REV-COMB-4): needed 2.2 / 1.9 / 1.8 s at 283.15 / 289.5 / 297.15 K unlined; vented <= 66.7 / 70.8 / 75.1 g at Cd 0.70; conditions (a) cold-corner 2.2 s stated, (b) measured Cd x A >= 0.91 x the Cd 0.70 value, (c) unlined; mass above 76 g at Cd 0.80 judged by GNC (REV-GNC-7)".

**Datasheet rows:**
- "Relight purge flow basis": "flow 2.43 s scheduled (both-open overlap 2.38 s + 0.05 s), cap 2.39 s (LEAD 253 (7)(ii)); basis 29.25 g/s = 76 g / 2.5982 s at 289.5 K (27.58-31.06 g/s over 283.15-297.15 K); vented at 2.43 s <= 75.1 g (Cd 0.70)". Tag LEAD (flow); DERIVED.
- "FA-1 structural load": replace "LEAD to decide" and the OI-41 proposal with "band values 94 / 121 / 147 / 94 bar abs DECIDED (LEAD 230 (2)); FA1S 151.04 bar abs bounds every period and case and is the design case for pressure-filled passages".
- "FA-1 at TC-01 J-FWD (per-mode)": add "analysis path only (230 (2)); TC-01 J-FWD not met conservatively, design change sized to FA1S (230 (1)); shares FEA3D ca2b (ca2c moves the bin bounds by -0.6 to +0.2 bar)". Alternatively, drop the row.
- "Start level": add "one of the 3 corners crosses at E2 + 0.857 s" (R4-03) and "with the SPI flux the cold-flow bound is 19.5 N at 286.70 K, above 16.31 N" (R4-17).

### R4-09 MINOR (Electronics). Pc-port face-peak sound-speed bracket [DELTA].

**Reproduction.** My lossless duct (r4_pc_port_face) reproduces Electronics' laminar-ladder face peaks within +0.9 to +3.2 bar:

| Chain | Electronics (bar abs) | Lossless duct (bar abs) |
|---|---|---|
| CC-1, 6 mm3, c 222 | 104.49 | 106.43 |
| CC-1, 6 mm3, c 400 | 121.59 | 122.47 |
| CC-1, 20 mm3, c 222 | 108.87 | 112.11 |
| CC-2, 6 mm3, c 222 | 125.14 | 126.01 |

**What the two-point bracket misses.** Electronics evaluates only c 222 and 400 m/s. That misses the range c 181-222 m/s and the interior maximum:
- CC-1 6 mm3: 130.16 bar abs at c 320;
- CC-1 20 mm3: 131.31 at c 181;
- CC-2: 130.46 at c 202.

All of these are below the C1 span (137.9), FA1S and the 166.14 proof, so no conclusion changes. But the over-range margin at c ≥ 181 m/s is 6.6 bar, not about 16 bar.

**Other observations:**
- Below the gas bound, at c 150, CC-1 reaches 144.04 bar abs (7 cases above 137.9) and 152.32 bar abs with 20 mm3 (2 cases above FA1S).
- The face reaches 1.01-1.24 x the SDOF spectrum, so the band values do not bound a gas column; FA1S does.

**Correction (electronics.json, fa1_chain):** "lossless bound over c 181-1200 m/s: 130.2 / 131.3 / 130.5 bar abs (CC-1 6 mm3 / CC-1 20 mm3 / CC-2; REV-COMB-4); C1 over-range margin >= 6.6 bar at c >= 181 m/s". Either sweep c densely from 181 to 1136 m/s, or quote this bound.

### R4-10 MINOR (lead wording). Line 253 (8).

Replace "would mark the joint used after about a fifth of normal lights" with "would mark the joint used in 185 of the 896 FA-1 hard-start bracket cases (a SIM grid count on an ASSUMED construct, not a rate of normal lights)".

### R4-11 MINOR (lead wording; already being corrected). Line 253 (7)(ii).

"Inside GNC's 0.10 kg re-fly trigger" is a category error. That trigger covers dry landing-mass growth over ledger v3d. Vented N2O is judged against the 76 g basis (G73 decided, G80 sensitivity) and the A1 reserve (REV-GNC-7).

### R4-12 MINOR (Electronics; routed to v2.12). P_torch transducer proof rating.

Electronics must state the proof rating of the TE M3234-000005-070BG against the passage pressure during FA-1:
- design case FA1S 151.04 bar abs; linear peak at most 148.7 bar abs at the seat;
- required proof ≥ 166.14 bar abs, or isolate the transducer;
- the 74.4 bar g full scale over-ranges during FA-1, so state the saturation and recovery behaviour.

### R4-13 MINOR (Electronics; routed). config.h:831 cites a superseded source.

config.h:831 cites "1.0-2.0 s" from purge_sizing_v2p4.json (00955c206987e5e8, which used 0.6 / 0.8 mm orifices and is superseded). Cite instead purge_duration_v2p4.json (1ff6bfcd7d2f454c): 1.9 s at 289.5 K on 2 x 0.707 mm, and 2.2 s at 283.15 K (REV-COMB-4).

### Notes

- **R4-14 NOTE. Release-hold wording.** REPORT 45, combustion.json purge_commit_rule_v2p4a.v.line181_2_answer.below_L_star and RESPONSE §6 point 3 say "0.30 s (0.31 s with the 10 ms frame margin)". Every Table 2.18 value already includes the frame. Text: "H >= 0.30 s unlined / 0.31 s lined on the 2500 N/s ramp to 200 N (latest A3 trip 0.282 / 0.290 s + one 10 ms frame, rounded up to 10 ms)".
- **R4-15 NOTE. A1 throat-growth time basis.** 1.90 / 2.10 % = 1.86 / 2.05 x 8.443 / 8.258, giving 1.902 / 2.096 [DERIVED]. If the 1.86 % belongs to the 8.24 s record, as REPORT 3136 says, the values are 1.906 / 2.100, which round to 1.91 / 2.10. State the basis; the NZ-01 conclusions do not change.
- **R4-16 NOTE. Table 2.13.** Table 2.13 lists s 1.0 unlined 1.1 s and lined swall 1.2 s. purge_duration_v2p4.json, which I reproduced exactly, gives 1.2 and 1.3 s. The governing 1.9 / 2.2 s do not change.
- **R4-17 NOTE. Two datasheet rows.**
  - The full-stroke "876 N, 42.85 bar abs at the 30 C bound" is SUPERSEDED in combustion.json (30 C is not credible; the interlock is at 24 C). Label it so in the datasheet.
  - The start-level row should carry the SPI-flux cold-flow sensitivity, 19.0-20.1 N over 283.15-289.5 K, which is above the 16.31 N margin. The CF-3 condition is not a formality.
- **R4-18 NOTE. Item (d), ca2b to ca2c.** See §7. Add to fa1_per_mode_peq_v2p4b: "shares FEA3D modal_v351ca2b_c71 (9af80c657eed11ac); ca2c (619272cd3b66072b) changes the bin-level bounds by -0.6 to +0.2 bar (REV-COMB-4); analysis path only (230 (2))". In the OI-51 action, name modal_v351ca2c_c71.

## 2. R3 closure table

| Item | Status | Basis |
|---|---|---|
| R3-01 | CLOSED (re-computation) | Table 2.18 and release_hold_v2p4b (a926426da0e6e436) match my independent R3 quadrature (c162cde0363c4917). Latest A3 trips for the 200 N ramp / 500 N ramp / held lift, in s: LO unlined 0.2822 / 0.1775 / 0.7267; HI unlined 0.1532 / 0.1336 / 0.3216; LO lined 0.2902 / 0.1725 / 0.7309; HI lined 0.2693 / 0.1773 / 0.6271. P at H 0.22 / 0.25 / 0.30 / 0.65 is identical. Holds: 0.30 (unlined) / 0.31 (lined) s, 0.19 s, none within W. Texts corrected (REPORT 45 and 817; combustion.json below_L_star); alternative NOT ADOPTED. Wording: R4-14. |
| R3-02 | CLOSED (re-computation) | Spectra published to 50 ms. My exact run (896 cases, 790 periods to 2000 ms) reproduces the published ζ 0 columns to at most 0.0005 bar, and the ζ 0.02 / 0.05 0.1-1 ms band to +0.009 / +0.007 bar. Period domain set by 230 (2). |
| R3-03 | CLOSED | Published thrust spectrum: 1742.6 / 1451.8 / 1032.3 N at 25 / 40 / 100 ms. Rectangle minimum ratio over T ≤ 20 ms is 1.0767, evaluated by me. |
| R3-04 | CLOSED (superseded) | 92 became 93 (194 (1)), then 94 / 121 (230 (2)). |
| R3-05 | CLOSED WITH RESIDUAL | Stated CONDITIONAL, with CF-3 acceptance (16.31 N or 52.6-56.3 g/s). Residual: physical closure at CF-3, and the SPI sensitivity (R4-17). |
| R3-06 | CLOSED | T1-T4 v3 §2 item 3 is two-sided. |
| R3-07 | CLOSED WITH RESIDUAL | §11-14 added. Residual: stand tank MISSING; line 83 (R4-05). |
| R3-08 | CLOSED WITH RESIDUAL | CF-4 §1, §4.1, §5.1, §9.1, §12 added. Residual: lines 15 / 103 / 35 / 64 (R4-06, R4-07). |
| R3-09 | CLOSED WITH RESIDUAL | IN718 lip values match 23b85b7febb90c60 (lumped 1.10-5.88 s; 1 mm 5.21-33.92 s). Residual: the "t_E2 + 0.5 s" correction is itself stale after 227 (5) (R4-04). |
| R3-10 | CLOSED WITH RESIDUAL | Range ≥ 100 bar abs is stated. Residual: proof texts (R4-05); a sense-line mount needs ≥ 132 bar abs range (R4-09). |
| R3-11 | CLOSED | Stale items replaced; old values kept under *_superseded keys. |
| R3-12 | CLOSED | Firmware release term; E2_rule_v2p4b (at most 14.7 ms); one lift definition. |
| R3-13 | CLOSED | Statements counted per command profile (population_statements_v2p4b). |
| R3-14 | CLOSED WITH RESIDUAL | Heat location corrected; lit history published (33.14 N and 3 of 72 reproduced). Residual: injector-body temperature TO-VERIFY. |
| R3-15 | CLOSED | Frozen prediction (§15.12, T1-T4 §15). |
| R3-16 | CLOSED | Wording per 194 (5) (REPORT 267). |
| R3-17 | CLOSED WITH RESIDUAL | Dip onset by thrust level (LITERATURE; N2O TO-VERIFY). Residual: outlet geometry MISSING (OI-32). |

## 3. Line 230 (1)-(5)

**(1) CONFIRMED.** FA1S bounds every period and every case.
- Coverage: 896 cases x 790 periods, from below 0.02 ms to 2000 ms, head and aft, clipped and unclipped.
- Head maximum 146.881 bar abs (3.5 ms); aft 146.601. Margin 4.159 bar (ratio 0.9725); 0 points above FA1S.
- Gas columns: the torch passage stays at or below 148.72 for c ≥ 150 m/s, and the Pc port at or below 131.3 for c ≥ 181 m/s. The only exceedance is the Pc port with 20 mm3 dead volume at c 150, below the gas bound.
- MS arithmetic confirmed: −0.0385 / +0.0396 at 121; −0.0839 / −0.0095 at 127.0; +0.0152 / +0.0976 at 114.6.
- J-FWD at FA1S: −0.221 / −0.160. So "not met conservatively" holds, and Mechanical's design change is sized correctly to FA1S.

**(2) CONFIRMED.** Band values 93.641 → 94, 120.302 → 121, 146.881 → 147, 93.641 → 94 (at 21.08 ms).
- 50-2000 ms: 63.37. T < 0.02 ms: 88.89.
- FA1S is the bound for every period. The per-mode method is an analysis path only.
- Scope note: the band values bound SDOF structural paths, not gas-filled passages (R4-01, R4-09).

**(3) CONFIRMED** (arithmetic).
- 29.25 g/s = 76 / 2.598 s, where t76 = 0.2274 + (76 − 1.931) / 31.2416.
- Over 283.15-297.15 K: 27.58-31.05 g/s.
- Strict cap 2.548 s; 2.60 s of flow gives 76.05 g; warm-end overlap cap 76 / 31.06 − 0.05 = 2.397 s.
- [DELTA] An independent CoolProp Dyer calculation gives G_L 56854 against the author's 56843 kg/m2s (+0.019 %). Tank-state ratios agree within 0.014 %.

**(4) CONFIRMED.** 0.21776 mm is the ECU kIgnLiftTab_m row at 286.70 K [DESIGN, read]. The author's injector model gives 0.21788 mm (−0.056 %); I did not re-run it. TO-VERIFY at CF-3.

**(5) CONFIRMED as a decision.**
- F_min is 33.141 N with torch 0 and 33.497 N with torch 0.3.
- 3 of 72 corners never reach 37.16 N in either window.
- Every corner that crosses within 0.857 s does so by E2 + 0.205 s.
- The supporting sentence is REFUTED for one corner (R4-03). The window is not limited by the lit side; the threshold is.

## 4. (e) P_torch

- **MEOP 45 bar row:** the passage is dead-ended at a uniform Pc of at most 45 bar abs (quasi-static); about 3 bar abs during the torch run. Covered by 102.
- **75.5 bar FA-1 pulse row:** superseded. The head peak is 88.02 bar abs, and the passage amplifies it.
- **Line-176 rows (90 / 102):** 102 does NOT cover the passage (R4-01 numbers).
- **Value to re-check at:** FA1S 151.04 bar abs, uniform over the passage. Mechanical has done this; all margins are positive (R4-01).
- **Status:** answered, closes on publication of jfwd_tapwall_v352_v2.

## 5. (f)(i) face peaks and (f)(ii) S6R

**(f)(i).** 104.5 / 121.6 / 125.1 are consistent with my lossless bound and below FA1S and 166.14. They exceed my SDOF spectrum at the quarter-wave period by 1.05-1.22 x, so the spectrum is not a bound for a gas column. The bracket gap is R4-09.

**(f)(ii).** The S6R peaks are real SIM bracket cases, not an artefact (R4-02).
- 253 (7)(i) need not be re-opened, provided two things are in: Z3' is adopted, and Mechanical's FA1S design change (230 (1)). The 46 peaks have ESP ≤ 146.88, which is below FA1S.
- 253 (8): R4-10. Mechanical states whether the 60 bar replace-all rule is meant for normal-light transients; Electronics states the logged quantity and threshold that detect it.

## 6. (f)(iii) Electronics items and (f)(iv) N-07

### Purge

- **Adequacy:** 2.43 s is adequate (unlined) at all three corners (R4-07). The vented mass at 2.43 s is inside 76 g at Cd 0.70.
- **Source of "1.0-2.0 s":** purge_sizing_v2p4 (superseded).
- **What the 76 g basis protects:** GNC's A1 N2O reserve (G73 decided, G80 sensitivity).
- **80.76 / 86.14 g:** not admissible on the basis. Both exceed G80; on the bound law, 81.08 g at 297.15 K with the 2.55 s cap. They are moot, because 2.43 s is confirmed. GNC judges any mass above 76 g at Cd 0.80.

### Open items: what to do before the datasheet

| Item | Disposition |
|---|---|
| OI-E2-LATENCY (LOW) | Leave open; IGN-1. |
| OI-STAND-LATE-LIGHT (LOW) | Leave open; IGN-1. |
| OI-UNPURGED-RELIGHT (MEDIUM) | Change combustion.json before the datasheet. (a) Add the 253 (7)(iv) refusal: "an unprimed or UNKNOWN-line relight with the bleed fitted stays refused for A1 (fail-safe)". (c) In the latency and hold blocks, cite E2_rule_v2p4b: the ECU relative E2 comes at most 14.7 ms before the model E2. (b) The torch-kept ride-through stays a research option. The OI stays open until Combustion models an unpurged relight (253 (7)(iv)). |
| OI-PHOTODIODE-VIEW (HIGH) | Leave open for IGN-1. combustion.json and the datasheet must carry this condition: "pcf_tmax 0.8 s holds on the dead side only with the photodiode main-chamber view (FLAMEOUT_OPT armed) or the GNC reference re-taken at the ECU E2 / light; photodiode-blind families release 42 / 98 of 1000 dead runs at 0.8 s". |
| OI-SEAT-RINGING (MEDIUM) | Leave open; B-DPC-1 / HIL-TR-1. The grid's minimum 10-90 % rise is 0.842 ms, against the ideal 25 µs steps. |
| OI-GEN-TABLES (MEDIUM) | Change combustion.json in v2.4c: add a machine-readable igniter-sequence block (requests[7]). |
| OI-38-R2-COMMAND-HOLD (HIGH) | Leave open; GNC R2 v2 / B-FC-1 / CF-3. |

### N-07

T1-T4 v3's own objectives fix no DC-D or DC-C duration. Its T4 row reads "DC-D ... law check only", with 7.02 kg. The durations are taken from GNC's DC-D v2 (32.0 + 8.0 + 10.0 s; 6.31 kg ox) [ASSUMED].

The objectives that do set durations are in REPORT §10's T4 row:
- **Erosion per cycle and soak temperatures:** these need the B1 sizing duty. B1 p99 is 21.76 s at mean throttle 0.257 (1.54 kg); B1 max is 23.58 s (1.63 kg).
- **Relight latency:** this needs an A1-like relight from a soaked state. The A1 p99 record has 3.78 s at 0.88, a coast to 22.79 s, then 4.59 s at 0.47.

Shortest firing that meets them [ESTIMATE from the GNC records]:
- burn 1 = the B1 p99 profile (21.76 s; use 23.58 s if the life rule is sized on max);
- then a coast of about 19 s;
- then one relight of about 4.6 s at about 0.47 throttle.

That is about 2.0 kg of N2O, against 7.02 kg. A third start serves only as a repeat. DC-C (27.0 + 9.5 s, 2.39 kg) carries no Combustion T4 objective; it adds soak data above the sizing duty.

## 7. (d) ca2c

**Share changes at TC-01 node 2785:**
- residual 0.38197 → 0.38228;
- 1-20 ms bin: signed 0.01781 → 0.01367, absolute 0.0956 → 0.0803;
- 0.1-1 ms bin: signed 0.6002 → 0.6041, absolute 0.8678 → 0.8823;
- T_min 0.19491 → 0.19351 ms;
- modal-period spectrum values change by at most about 0.1 bar.

**Effect.**
- The author's intervals lie inside my bin-only bounds at s 1.00 / 0.90 / 0.85:

| s | Signed bound (bar abs) | Absolute upper bound (bar abs) |
|---|---|---|
| 1.00 | 88.1-118.8 | 155.9 |
| 0.90 | 86.6-119.7 | 156.5 |
| 0.85 | 86.8-119.9 | 156.7 |

- ca2c moves those bounds by −0.56 to +0.19 bar [DERIVED].
- The band values do not depend on FE shares, so they are unchanged.
- OI-51 stays OPEN: ca2c publishes only the top 5 modes plus bins.

**Restatement:** a note in combustion.json only (R4-18). No datasheet restatement beyond R4-08.

## 8. (g) Datasheet and open-item statuses

**Values.** I checked 12 of 13 rows against their sources by value; all match:
- rated point (500 N, 25.01 bar, O/F 10.435, 241.0 + 23.1 g/s);
- limits (LEAD);
- full-stroke 619.3-822.0 N and 30.66-40.29 bar;
- ceiling;
- throttle;
- 500 N hold (4.06-7.01 s; 3387-3616 N s);
- mission burns (summary_v2p4 7f4f181b80d55331);
- 2.20 kg option (1.96-2.20 %, web 2.54 mm);
- start level;
- purge;
- the two FA-1 rows.

The nozzle/grain row was read for its tag only.

**Tags and owners:** consistent. The stale items are R4-08 and R4-17.

**Open-item statuses:**
- OI-41 and OI-42: stale (R4-08).
- OI-49: true. gnc.json is still v3.1 (4f3209323b0e0ed4), with no 210 m record.
- OI-50: true. There is no 2.20 kg B1 record.
- OI-51: true, but its action should name ca2c.
- OI-52: true.

## 9. Confirmed numbers

| Quantity | Value | Tag |
|---|---|---|
| FA-1 head band maxima, all cases, ζ 0 | 93.641 / 120.302 / 146.881 / 93.641 bar abs | DERIVED on SIM |
| FA-1 aft band maxima | 86.942 / 102.503 / 146.601 / 93.108 | DERIVED |
| FA-1 head baseline | 88.635 / 102.491 / 138.852 / 87.593 | DERIVED |
| FA-1 head peak | 88.019 | SIM |
| 0.1-1 ms band, ζ 0.02 / 0.05 | 115.431 / 109.585 (published 115.422 / 109.578) | DERIVED |
| Purge basis and caps | 29.25 g/s; 2.548 s; 76.05 g; 2.397 s; 27.58-31.05 g/s | DERIVED |
| Lift | 0.21776 mm | DESIGN, read |
| P4c | 33.14 N; 3 of 72; latest crossing E2 + 0.205 s | DERIVED on SIM |
| A1 throat-area growth | 1.902 / 2.096 % | DERIVED, first order |
| R3-01 trips | as in §2 | SIM / DERIVED |
| TC-01 MS arithmetic | as in §3 | DERIVED |
| Release-hold and thrust-spectrum values | as in §2 | read |

Each value is shown for repetition only; none is physical evidence.

## 10. NOT RUN

| Check | Reason |
|---|---|
| TC-01 per-mode exact intervals (signed 101.5-109.4, absolute 137.3-147.9, SRSS 55.7-58.1), time-domain bound 114.6, E rule 127.0 | The author's chain needs LP intervals over unpublished shares, plus the modal time-history chain; the scripts assert ca2b hashes. Did not fit the time box. Done instead: the containment check and the ca2c bin delta (§7). |
| ca2c re-run of the per-mode chain | Same reason. |
| Injector-model lift 0.21788 mm | Not re-run; the 0.21776 mm ECU row was read. |
| Thrust spectra | Values read from the author's CSV, not recomputed. |
| 2.20 kg option | Read only. |

## 11. Delta since the interim (07:52:49Z)

- R4-03: the third P4c corner crosses at E2 + 0.857 s.
- R4-04: pcf_tmax 0.5 s texts.
- R4-05 and R4-06: added REPORT 2433, 2520, 2553 and T1-T4 83 to the stale-text list.
- R4-07: the lined variant needs 2.5 s at 283.15 K; Cd 0.80 gives about 80.5 g; the independent Dyer check.
- R4-09: Pc-port face bracket.
- ζ 0.02 / 0.05 band values reproduced.
- The R3 closure table (§2).
- (d) quantified on the bin bounds.
- (e) Mechanical's v2 row read and agrees; the DLF note.
- Notes R4-14 to R4-17.

## 12. Disclosures

- In the earlier session, two commands used cd, against the rule. No input or output was affected.
- The first r4_damped_check run had an inverted sufficiency label. I corrected it and re-ran; the values were identical.
- Mechanical's v2 file sits in its work tree and was read only.
- No CalculiX. At most one heavy process at a time, at nice 15; peak RSS about 0.33 GB. No processes of mine are left running.
- Scratch /dev/shm/rev_comb4 (38.8 MB) was removed at 08:27Z.
- Net new hub disk: 335,869 B. Free space at 08:31:11Z: 2,298,454,016 B (2.14 GiB).

## 13. Files

Folder: /home/claude/work/shared-fallback/engine/reviews/combustion/r4/. MANIFEST_REV-COMB-4.sha256 has sha16 996475830cae731f and verifies.

| Script (sha16) | Output (sha16) |
|---|---|
| r4_fa1_spectrum.py c78f6193d09a529e | json 403efc7d3788a903 |
| r4_damped_check.py ccbe8aa6e482bf1a | json 439b787d09fb9e06 |
| r4_fa1_envelope_stats.py d3cff38b3bc80d84 | json 9a4f010f2fd37049 |
| r4_torch_passage.py 2b09667dc16b7095 | json 8cb4b0c80173b88d |
| r4_pc_port_face.py 3fd1210877851445 | json 94f5a39166a8f778 |
| r4_purge_corners.py 8d4278fbfe47a961 | json 9249ed093c21a3a3 |
| r4_dyer_check.py 87f1aac1c3d989b5 | json 5907c02bdbf10a3d |
| r4_p4c_check.py 56424fd598102984 | json 0b10c8878a5b49f3 |
| r4_per_mode_crude.py f0eb2f37f75f6900 | json 5d018889a4569fd6 |
| r4_z3_pulse_check.py 16a43986290f8c56 | json 8807b744c7e3b74b |
| r4_stale_scan.py f94dd23f9980039c | json af52af04f9933e67 |

Inputs list: r4_inputs.sha256 802b57945d3d69d6.

To reproduce:
- r4_fa1_spectrum.py regenerates the scratch file r4_fa1_spectrum_cases.npz (52ca71bd0f612cf8). r4_damped_check, r4_pc_port_face and r4_per_mode_crude need it.
- r4_purge_corners needs a copy of 02-combustion/src (its sha is asserted) and a scratch directory.

END REVIEW-COMBUSTION-R4
```
