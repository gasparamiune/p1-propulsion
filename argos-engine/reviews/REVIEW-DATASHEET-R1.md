# REVIEW-DATASHEET-R1 (REV-DS-1)

Independent review of the ARGOS H1 engine technical datasheet rev1-draft (PDF 8e7d007d128dfb58, 151 pages), returned by the reviewer 2026-10-21T14:28:20Z with report stamp 14:25:25Z (date -u); its interim batches reached the lead with stamps 13:41:04Z and 14:05Z (section 8 of the review explains both stamps). Saved here by the lead on 2026-10-21T14:30:45Z (date -u), verbatim from the reviewer's final message: the harness does not let a subagent write a report file, so the handback text is the review. One word is redacted by the lead in section 3 (h): the name of a private benchmark, shown as [private benchmark name]. Reviewer artefacts: `reviews/datasheet/r1/` (`MANIFEST_REV-DS-1.sha256` cfb00a6b53fe9118, 17 entries, verified by the lead 17/17 OK at 14:30:23Z); `scripts/form_check.py` is kept out of public pushes. Verdict: ACCEPT WITH CORRECTIONS on three conditions (section 1); the final rev1 build and its independent check follow. Lead dispositions: the next lead CHANGELOG line. Simulation and calculation only; nothing here is physical approval, and no hardware has been tested.

---

BEGIN REVIEW-DATASHEET-R1

REV-DS-1: independent review (max rigour) of the ARGOS H1 engine technical datasheet rev1-draft
Report stamp: 2026-10-21T14:25:25Z (date -u, run immediately before this handback)

Object under review:
- 07-datasheet/out/rev1/ARGOS-H1-ENGINE-DATASHEET_rev1-draft.pdf, 8e7d007d128dfb58 (29,363,606 B, 151 A4 pages).
- trace.json 4e8fcae9ddf5d941 (4912 traces), sources.json 8cce7342052151e3 (86 sources), datasheet.html f33c3b2bfdd7522a, qa_report.json a425922dce4d9d3e.
- Generator build_datasheet.py v0.3.0.
- CHANGELOG lines 1-264 are the build basis (head -n 264 sha16 f7efe784da3944c5). Line 265 is the author's result line for this draft and holds no decision or action.

Every finding below is on draft PDF 8e7d007d128dfb58. No final rev1 build exists at 14:19Z (out/rev1 holds only the draft).

Evidence tags used in this report: SIM, CALC, DERIVED, DECIDED (LEAD / DESIGN / REQ), DATASHEET, ASSUMED. Numbers I computed are tagged [DERIVED, REV-DS-1]. A hash match or a rendered page is not physical approval. Nothing here is physical approval, and no hardware has been tested.

====================================================================
1. VERDICT: ACCEPT WITH CORRECTIONS
====================================================================
The verdict holds on three conditions:
(1) The final rev1 build applies D1-01 to D1-13 and the lead's rulings of 13:48:32Z and 14:06:22Z.
(2) An independent check of the final build passes against data/final_build_checklist_rev1draft.json. That check re-runs the re-trace, the form check and the privacy scan, and confirms that CHANGELOG lines 1-264 are unchanged (or that any new lines are reviewed).
(3) The draft 8e7d007d128dfb58 is not published as it is.

Why this verdict:
- No finding is BLOCKING.
- There are 5 MAJOR findings (D1-01, -02, -03, -04, -06) and 8 MINOR (D1-05, D1-07 to D1-13).
- Every MAJOR has an exact correction that is mechanical: a status label, a register row, or printing founder actions in full. None needs new engineering.
- D1-01 to D1-12 are already ACCEPTED by the lead and sent to the author. D1-13 and the RA-06 addition to D1-06 are new in this report.
- Traceability is sound: 100 of 100 headline values match, and all 25 harness mismatches resolve by hand.

On a strict reading (any open MAJOR means REVISE), the draft is REVISE until the final build passes the checklist. The findings and corrections are the same either way.

====================================================================
2. FINDINGS (build: draft PDF 8e7d007d128dfb58)
====================================================================
D1-01 MAJOR [ACCEPTED by the lead, 13:48:32Z]
- Where: p36 T529; p45 §9.10 item 1 (T4030-T4032).
- Problem: the superseded TC-02 plug-fit band [0.040, 0.0761] mm is shown as the current closure, with no mark. The draft states R2-B correctly on p5, p37, p56 and p60, so it contradicts itself.
- Governing value: R2-B (254 (1)), g in [0.040, 0.0631] mm [DECIDED LEAD].
- Correction:
  - Keep the T529 quote and add "[superseded: R2-B [0.040, 0.0631] mm, 254 (1); band re-size done, band v1 1ba3147b42edfeed]".
  - Add a §9.10 header note for item 1. Set its closure to "R2-B select fit (254 (1)); stays a found negative at the drawn fit".
  - Add C-11 (band vs R2-B) to §13.3.

D1-02 MAJOR [ACCEPTED]
- Where: p47 §10.3 T4150/T4151; p51 OI-PURGE-CAP T4436-T4439.
- Problem: the both-open cap 2.55 s (v2.11) is shown as DECIDED. p24-26 give 2.43 s flow / 2.39 s cap, FINAL in 256 (2) [DECIDED LEAD; DERIVED values].
- Correction:
  - At T4150 add "v2.11 value; superseded by 256 (2) FINAL: 2.43 s flow, 2.39 s cap, conditions (a)-(d), (d1), (d2) of 256 (2) / 257 (2) / 258 (2); implemented in v2.12 (v4.1), PENDING REVIEW".
  - Set the OI-PURGE-CAP closure to "lead decision made, 256 (2); open: measured-time form after CF-4 / B-BLEED-1".
  - Add C-12.

D1-03 MAJOR [ACCEPTED, with the lead's clarification]
- Where: p48 T4170 and T4177, p49 T4275, T4130 (kPcRezeroMax max 30000); p50 T4409-T4411; the p47 sentence "not shown as values here".
- Correction for 70000 Pa and 30000 Pa:
  - Keep DECIDED only as DESIGN (Electronics v2.11 design value), never LEAD, and print the unit Pa.
  - Add "not accepted, 253 (5) (R3-01); 264 (2): 0.30 bar on the compensated residual, 0.76 / 0.46 bar; v4.1 implementation PENDING REVIEW (REV-ELEC-4)".
- Correction for T4409-T4411 (0.30 / 0.76 / 0.46 bar): keep DECIDED LEAD (264 (2)) and add "PENDING REVIEW (v4.1 implementation; v4.1 holds kIgnBaseCheck_Pa 76000)".
- Reword the p47 sentence and add C-13.

D1-04 MAJOR [ACCEPTED as ruled]
- Where: §13.3, p60-61. The contradiction register is incomplete.
- Correction:
  - C-09: add a "retired" row with its reason.
  - Add these rows:
    - C-11: band vs R2-B.
    - C-12: purge cap 2.55 vs 2.39 s.
    - C-13: v2.11 BASE constants vs 264 (2).
    - C-14: combustion-side P_torch text vs 264 (4), with pointers at p6 T803 and p26 T1427 ("its proof (>= 166.14 bar abs, or isolation) ... Electronics v2.12 items"; "P_torch 0-70 bar class").
    - C-15: relight 4.6 s vs 264 (5).
    - C-16: OI-A1-BASE-AMB vs 264 (3). The item moves to closed; any named residual stays open.
  - C-05 cites 259 (6); C-06 cites 261 (2) and 264 (5), with the re-run OPEN.
  - Rulings to print:
    - C-01: rows-v8 6c694fa7147fb511 governs.
    - C-02: v4 is the source of record (253); "STAGED" is stale.
    - C-03: the 210 m record is OPEN; the 300 m comparators stay labelled; B1 governs sizing.
    - C-04: R2-B governs.
    - C-07: the hub path governs.
    - C-08: mechanical.json v2.4 governs.
    - C-10: 264 (4) governs; the re-base is OPEN.
- C-17 (lead: "if the sources disagree"): not needed. The §12.5 spread 3133-7406 N·m/rad is the V5c plant range on CAD v3.3 (CHANGELOG 188 (7); 227 "V5c plant (CAD v3.3)"). The §3.3 values are the CAD v3.5.2 R3 table, a different stiffness model, so no two sources disagree about one quantity. Label the 3133-7406 as "V5c plant, CAD v3.3 (188 (7), 227)" and point to §3.3. The spread status goes in D1-13.

D1-05 MINOR [ACCEPTED; lead Q1, staged by the author]
- Where: p7 T892, 166.14 bar.
- Correction:
  - Change DECIDED to DERIVED, unit bar abs: "1.1 x FA1S 151.04 bar abs [DERIVED]; 256 (5) R4-12, 264 (4)". The p7 ladder chart label must agree.
  - p47 T4159: keep the quote "166.1 ... 230 (2)" and add "[requirement 166.14 bar abs DERIVED, 256 (R4-12), 264 (4)]".

D1-06 MAJOR [ACCEPTED; RA-06 is new in this report]
- Where: §12.3, p56-57. Founder actions are incomplete against CHANGELOG 240-264, and some cannot be carried out as printed. Lead ruling 14:06:22Z: founder actions, gates and build procedures are never cut, and C4 prints in full as "Annex C4", referenced from §12.3.
- (a) RA-03 is missing from the whole datasheet. Only a fragment sits inside the stale T529 quote. Add a row (240 (5); 241 (8) C1):
  - bore-side break R0.2 maximum (R0.1-R0.2);
  - spot-face side 0.1 maximum;
  - deburr after match-drilling;
  - rework before anodise;
  - 100 % 10x inspection before assembly.
- (b) RA-08: the T-F1 routes are not printed (T1204 is cut; T4732 only refers to them). T-F1 is a gate before the first static fire. Print them (241 (8), 249 (3), 254 (2)):
  - (i) handbook data with full citation, or
  - (ii) coupons from the same heat / lot, at least 3 exposed and 3 control, EN ISO 6892-1 / ASTM B557, on the A 175 rows with A 150 beside;
  - re-base to A 165 only after B-TC-1.
- (c) RA-07: C4 (T4738) stops at step 1. Print C4 in full as Annex C4 (241 (8) C4, 246 (2) C4). Its steps:
  - gate J-F1;
  - hole pins GO 5.50 / NO-GO 5.62; tap gauging; plugs and band;
  - S01/S02 lubricant TO-SELECT (oxygen-clean, FKM- and N2O-compatible);
  - clock and push; shoulder 2.00 +/-0.02 on the gap gauge, TO-CONFIRM;
  - registration screws first;
  - flight screws one at a time, each with a new oriented HW-170, at the J-F1 lot torque by M-T1J, never re-torqued;
  - proof / leak test.
- (d) RA-19: the B-TC-1 row (T4730) has no acceptance limit. Add "verify tau <= 0.25 s and the static terms on the DESIGN install, else the tolerance is re-derived" (249).
- (e) RA-26: there is no CF-4 / B-BLEED-1 row. Add one (256 (2), 257 (2), 258 (2)), or point §12.6 to §7.5:
  - measured Cd x A >= 0.91 x the Cd 0.70 value (>= 0.95 x with the FD-01 element bound), else re-size;
  - after CF-4, re-set kPurgeFlow_s and the cap from the measured Cd x A, never above 2.43 / 2.39 s;
  - conditions (d1) and (d2).
- (f) Also missing from §12.3:
  - RA-15: the C6 path 3 screw qualification test (TO-DEFINE; 243 (5), 254 (6)). It is on p37 only.
  - RA-32: the 264 (2) stand fallback rule (coefficient 0 only with k <= 2 default / k <= 1 B-PC-1-shown, by F-10, and k x 0.0248 bar/K x (T0 - T_cal) inside 0.5 bar at ARM). It is in §10.8 only.
  - RA-18: T4725 is cut before "HIGH (>= 4.75 V = 146.5 bar abs)".
- (g) NEW, RA-06 (241 (8) C3; 245 (4) F2; 246 (2) C3b). §12.3 names only "two GSE shoulder screws" and "the index pin in the drill fixture" (T4733). Add make/buy rows that point to the BOM GSE lines (p15/p21):
  - ENG-TC-12, J-FWD hole-plug set (TO-DRAW / TO-QUOTE, delivered DK-6400);
  - ENG-TC-13, registration shoulder-screw pair (TO-DRAW / TO-QUOTE);
  - the match-drill fixture with index pin and guide bushings (TO-DRAW).

D1-07 MINOR [ACCEPTED]
- Problem: DECIDED pills set at the call site on results. A SIM / DERIVED / CALC result keeps its own tag.
- Corrections:
  - p9 T942: CALC / DERIVED, with SIM for "P(landing) 0.982".
  - p9 T944 (rocking 16.0-27.8 Hz): SIM / DERIVED.
  - p9 T912: SIM.
  - p22 and p56 T1205: CALC on SIM, "accepted, 249 (3)".
  - p48 T4182: SIM (SIL).
  - p49 T4342 (kBayArmMax_K 318.15, source tag "LEAD approx 45 C, TO-DEFINE"): TO-VERIFY / TO-DEFINE.
  - TC-01 J-FWD cell -0.075 / +0.239, which is CALC on p34 (T2018) and SIM on p37 (T2265). Lead ruling: use the class margin_matrix_v352.json 6c694fa7147fb511 gives, in both places. The matrix gives:
    - /rows[TC-01]/cells/J-FWD/governing[0] (SOAK, IN718 seat line P+Q, MS_y -0.075): "CALC / DERIVED";
    - governing[1] (FA1S (ii) hole bearing, MS_u +0.239): "CALC".
    So T2265 becomes CALC, as T2018 already is.

D1-08 MINOR [ACCEPTED]
- §10.5 p48 prints values at 4 significant figures. Print them at source precision (423.1 K is not A = 150 C):

  | T-id | Printed | Source |
  |---|---|---|
  | T4232 | 423.1 | 423.15 |
  | T4235 | 403.1 | 403.15 |
  | T4233 | 523.1 | 523.15 |
  | T4236 | 333.1 | 333.15 |
  | T4200 | 0.01282 | 0.012825 |

- §10.3 values have no unit (T4142, T4144, T4148, T4150, T4152, T4154, T4170). The same holds in §10.4 / §10.5 (for example T4192, 0.005 s). Add the units.
- The §2.3 ladder on p7 mixes bar and bar abs. Give the basis per row: FA-1, FA1S and the transducer proofs are bar abs in their sources. Drop the trailing zeros beyond source precision (25.00, 30.00, 45.00, 67.50, 206.80).

D1-09 MINOR [ACCEPTED]
- Where: §12.6 p58. The bench plan v4 rows carry DECIDED pills and "nothing: executable now" (T4814). 253 (5) says no bench row is executed from v4.
- Correction: mark the table "v4, for information, not for execution (253 (5)); v5 PENDING REVIEW", and drop or annotate "executable now".

D1-10 MINOR [ACCEPTED]
- Where: §7.9 p27, T1544/T1545, "one relight of about 4.6 s".
- Correction: put the 264 (5) statement in §7.9 itself (it is now only in §10.8 / §12.4): T4 demonstrates relight latency from a soaked state, not a 4.59 s landing-length relight. Add C-15 as well.

D1-11 MINOR [ACCEPTED]
- Where: p25 "§2.8" and p26 "§2.7". This datasheet has no such sections.
- Correction: write "combustion REPORT §2.8" and "combustion REPORT §2.7".

D1-12 MINOR [ACCEPTED]
- Where: p29, p32 and p33 print the literal "*Por revisar*".
- Correction: render it as plain text, with "(to be reviewed)" if it is kept.

D1-13 MINOR [NEW in this report]
- Where: p58 §12.5 ENG-11 row (T4798-T4800); p9 §3.3 (T914-T921).
- Problem: the requirement row prints "Alpha/beta spread across poses <= +-20 %" (REQUIREMENTS.md line 62) with no status.
- On the CAD v3.5.2 R3 table (k_table_r3_v352.json f3c7cfbcfb98bcd7, 17 poses, SIM), FE coupled beta runs 3971.84-7172.12 N·m/rad. The requirement does not define "spread", so I give three definitions [DERIVED, REV-DS-1]. Beta exceeds +-20 % under all three; alpha passes under all three:

  | Spread definition | beta | alpha |
  |---|---|---|
  | half-range over mid-range | 28.7 % | 12.3 % |
  | maximum deviation from the 17-pose mean | 29.4 % | 15.8 % |
  | maximum deviation from neutral | 31.1 % | 13.2 % |

- History:
  - CHANGELOG 187, RM1-08: "spread -39.5/+38.3 % vs +-20 % FAILS" (V5c).
  - 188 (7) left the spread to GNC's loop-robustness assessment: if robust, the lead amends the spread requirement; otherwise Mechanical stiffens.
  - I found no amendment in lines 189-265 (grep).
  - T747 / RV7-01 says the K_s band is not robust across J.
- The hard minimum >= 3,100 N·m/rad holds on the FE values (beta minimum 3972 [SIM]).
- Correction:
  - In the §12.5 ENG-11 row add: "Spread element: not met on the v3.5.2 R3 FE beta values (+-28.7 % half-range over mid-range, DERIVED from §3.3); OPEN under 188 (7): GNC robustness assessment, then the lead amends the requirement or Mechanical stiffens; see §3.3 and open item 11b."
  - Add a one-line status under §3.3.
  - Owners per 188 (7): GNC (assessment), lead (amendment), Mechanical (stiffening).

NOTES (no severity; the lead's dispositions of 14:06:22Z are in brackets)
- N-01: the 262 (1)-(2) process quotes ("Gaspar tapped 'Three agents'", "a fresh agent, effort max") on p5, p55 and p146 are hygiene only, not a privacy breach. [The quotes stay.]
- N-02: §9.3 has no owner column; the owners are in §9.10 items 7 and 8. [Add "Owners: see §9.10".]
- N-03: ENG-11 names two different quantities:
  - §3.2 GNC servo output stiffness K_s, design-to 100-110 N·m/rad [DERIVED];
  - §12.5 REQ axis stiffness >= 3,100 N·m/rad.
  Batch 2 called the §3.3 range "3972-9337". Precisely, it is alpha 7294-9337 and beta 3972-7172 N·m/rad [SIM]. [Print "ENG-11 (REQ): gimbal axis stiffness >= 3,100 N·m/rad" (REQUIREMENTS.md line 62) and "GNC row 8: servo output stiffness K_s". Label 3133-7406 with its CAD version (V5c, CAD v3.3) and point to §3.3.]
- N-04: §9.1 quotes CAD manifest issues a94851ae4dc22cc4 (441 rows) and 0658b176e918f91f (448 rows). The manifest of record is a4713d45b3b24a0f (456 rows). [Add the pointer.]
- N-05: p18 T183, the supplier cell of ENG-HW-20, is cut at "...2026-10-13); pri". The author's staged cut fix covers it; check it in the final.

====================================================================
3. CRITERIA (a)-(i)
====================================================================
(a) Traceability: DONE, OK.
- Headline re-trace: 100 values (the brief asks for at least 60), weighted to the headlines, on 23 pages. Classes: DERIVED 45, SIM 23, DECIDED 22, CALC 7, DATASHEET 2, ASSUMED 1. All MATCH: 82 by the harness, 18 by hand.
- Full harness run over all 4912 traces: 4624 source matches, 25 harness mismatches and 263 not compared.
- All 25 harness mismatches match by hand:

  | Kind | Count |
  |---|---|
  | sha / identity rows T708-T725 | 16 |
  | two-group regex (T742, T745) | 2 |
  | CSV columns (T895) | 1 |
  | verbatim text with a sentence split (T900-T902) | 3 |
  | pointer KeyError resolved to the right node (T4863, T4865) | 2 |
  | path exists, sha 5b1c9336d7b8db50 (T4869) | 1 |

- The 263 not compared are 255 generator formulas and 8 wildcard / bin / unparsed-CL aggregates.
- Generator values spot-checked by recomputation, all matching: T698-T705 (negative counts), T966 (not-in-GLB list), and the 72 clearance values.
- Untagged values: 0.
- Sources: 85 of 86 are byte-identical to sources.json. The CHANGELOG differs only by the appended line 265.

(b) Currency: OK, except D1-01, D1-02, D1-03, D1-09 and D1-10.
- Versions of record match disk [DERIVED, identity]:
  - SET v3.5.2 final 621481ddeccc228b
  - BOM 9234c953c5b6beb8
  - MP c1ff170be0ac8cc5
  - CMB v2.4d 7dbf425c12300658
  - MEC v2.4 66bc53d88d444679
  - GNC v3.2 bde317782574cbd9
  - ELE v4 11f7896ad0d0613b (source of record per 253)
  - MMX 6c694fa7147fb511
  - CAD manifest a4713d45b3b24a0f (456 rows)
- v4.1 c862375163393adc and the bench plan v5 are registered PENDING. CLR is labelled as run on the interim set.

(c) Negatives: OK, except D1-13 and N-02.
- 33 governing negative cells, all classed [DERIVED from MMX]: MF 9, TS-183 9, BR 7, CH 3, TS-212 2, BT 2, DC 1.
- 11 information-column negatives (T2264 [DERIVED]), shown as information; one is UNCLASSIFIED.
- Owners are in §9.10.

(d) Review status: OK. REV-COMB-4 ACCEPT WITH CORRECTIONS, REV-GNC-7 PUBLISHABLE WITH CORRECTIONS, REV-ELEC-3 ACCEPT WITH COMMENTS, REV-ELEC-4 PENDING, and no independent review of FEA3D v3.5.2: all printed as such.

(e) Founder actions: NOT OK as printed (D1-06).
- The reference set is RA-01 to RA-36 from CHANGELOG 240-264; line 265 has no action.
- 25 are present and correct: RA-01, 02, 04, 05, 09-14, 16, 17, 20, 22-25, 27, 28, 30, 31, 33-36.
- RA-18 and RA-29 are present with a defect (D1-06 (f), D1-10).
- RA-21 is superseded by 264 (4) and printed as RA-33.
- 8 are missing, cut or partial: RA-03, 06, 07, 08, 15, 19, 26, 32.
- Each item is doable once printed in full.

(f) Renders: OK.
- All 16 views come from GLB 4bcc264f683e128f. That GLB is in the FINAL v3.5.2 CAD dir and its manifest row matches. BOM 9234c953c5b6beb8; render manifest 9e3d1d0e8156ad4a.
- Captions are correct.
- PDF assets against the v3.5.2 render PNGs: mean absolute RGB difference at most 2.91 of 255, after compositing on white and trimming [DERIVED]. This checks where the pictures came from, not what they show.

(g) Form: OK, except D1-08, D1-11 and D1-12.
- Footer on 151 of 151 pages; all 42 font entries embedded; 29,363,606 B (under 100 MB).
- 4865 internal HTML links, 0 broken, 0 external.
- Prices: "TO-QUOTE" appears 275 times and "DK-6400" 33 times; no price is 0 or "from". Two dated catalogue references sit beside TO-QUOTE (to DK-6400) and are not prices of record: INA HK0808-B, GBP 5.16 ex VAT (p18 T183), and MKS HV69, EUR 62.99 (p58 T4847).

(h) Privacy and hygiene: OK. No e-mail address, model identifier, [private benchmark name], OsoCordobes or repository name, credential or work path. The PDF metadata (Title, Creator Chromium, Producer Skia/PDF m141) is clean. See N-01.

(i) Contradictions: NOT OK as printed (D1-04; my view on C-17 is under D1-04).

====================================================================
4. RE-TRACE TABLE (100 headline values; full data in data/retrace_headline_rev1draft.json a0b98286db4ca41f)
====================================================================
Column "Class" is the draft's tag. "(manual)" means matched by hand. "…" in a pointer repeats the pointer of the row above.

| # | T-id | Value shown | Page | Class | Source and pointer | Source value | Match |
|---|---|---|---|---|---|---|---|
| 1 | T036 | 500 N | 1,7,14 | SIM | CMB /operating_points/throttle_points_20C_initial_port/0/F_N | 500.0 | MATCH |
| 2 | T037 | 193.1 s | 1,7 | SIM | CMB …/0/Isp_SL_s | 193.1 | MATCH |
| 3 | T039 | 2.50 MPa (25.0 bar) | 1 | SIM | CMB …/0/Pc_Pa | 2501007.0 Pa | MATCH |
| 4 | T040 | 100 N | 1,7 | SIM | CMB …/5/F_N | 100.0 | MATCH |
| 5 | T041 | 5.343 kg | 1,14 | DERIVED | MP /states/wet/all/m_kg | 5.34303 | MATCH |
| 6 | T043 | 593.3 mm | 1,10 | DERIVED | MAN /instances/*/bounds_mm | 593.3 | MATCH |
| 7 | T046 | 139.5 x 140.2 x 593.3 mm | 1,10 | DERIVED | MAN /instances/*/bounds_mm | 139.5 | MATCH |
| 8 | T047 | 140.2 mm (inside T046) | 1,10 | DERIVED | MAN /instances/*/bounds_mm | 140.23 | MATCH |
| 9 | T038 | O/F 10.44 | 7,29 | SIM | CMB …/0/OF | 10.435 | MATCH |
| 10 | T772 | 62.5-500 N (12.5-100 %): Pc 4.37-25.01 bar abs; O/F 4.06-10.… | 6 | SIM | DSIC line 11 "Throttle range" col 1 | same text | MATCH |
| 11 | T775 | 500 N held 4.06-7.01 s; liquid end 6.77-7.50 s … | 6 | SIM | DSIC line 12 "Burn time and total impulse at a 500 N hold" col 1 | same text | MATCH |
| 12 | T778 | 2968.2 N s, O/F 9.05, Isp 190.7 s (T0 294.12 K) … | 6 | SIM | DSIC line 13 "Mission burns (2.0 kg tank, 3.167 L)" col 1 | same text | MATCH |
| 13 | T812 | 25.01 bar | 7 | SIM | CMB …/0/Pc_Pa | 25.01007 bar | MATCH |
| 14 | T813 | 241.0 g/s | 7 | SIM | CMB …/0/mdot_ox_kg_s | 240.99 g/s | MATCH |
| 15 | T814 | 23.09 g/s | 7 | SIM | CMB …/0/mdot_fuel_kg_s | 23.09 g/s | MATCH |
| 16 | T871 | 62.5 N | 7 | SIM | CMB …/7/F_N | 62.5 | MATCH |
| 17 | T872 | 4.37 bar | 7 | SIM | CMB …/7/Pc_Pa | 4.36985 bar | MATCH |
| 18 | T873 | O/F 4.06 | 7 | SIM | CMB …/7/OF | 4.059 | MATCH |
| 19 | T874 | 140.2 s | 7 | SIM | CMB …/7/Isp_SL_s | 140.2 | MATCH |
| 20 | T880 | 25.00 bar | 7 | DECIDED | CMB /operating_points/pressure_limits/normal_cap_Pa/v | 25.0 bar | MATCH (D1-08 zeros) |
| 21 | T881 | 30.00 bar | 7 | DECIDED | CMB …/abort_Pa/v | 30.0 bar | MATCH (D1-08) |
| 22 | T882 | 45.00 bar | 7 | DECIDED | CMB …/chamber_MEOP_Pa/v | 45.0 bar | MATCH (D1-08) |
| 23 | T883 | 67.50 bar | 7 | DECIDED | CMB …/proof_Pa/v | 67.5 bar | MATCH (D1-08) |
| 24 | T884 | 44.33 bar | 7 | SIM | CMB /meop_basis_v2p4/v/basis_bar | 44.33 | MATCH |
| 25 | T885 | 93.64 bar | 7 | SIM | CMB /fa1_spectra_damped_v2p4b/v/head_all_band_maxima_bar_abs/T_le_0p1ms/zeta0 | 93.641 | MATCH |
| 26 | T886 | 120.30 bar | 7 | SIM | CMB …/T_0p1_to_1ms/zeta0 | 120.302 | MATCH |
| 27 | T887 | 146.88 bar | 7 | SIM | CMB …/T_1_to_20ms/zeta0 | 146.881 | MATCH |
| 28 | T890 | 151.04 bar | 7,8 | DERIVED | CMB /fa1_p_torch_v2p4c/v/design_case [regex FA1S ([\d.]+) bar] | 151.04 | MATCH |
| 29 | T892 | 166.14 bar | 7 | DECIDED (to DERIVED, D1-05) | DSIC row "Pc transducer proof" (line 21) [regex >= ([\d.]+) bar abs] | 166.14 | MATCH (class D1-05) |
| 30 | T894 | 206.80 bar | 7 | DATASHEET | DSIC row "Pc transducer proof" (line 21) [regex XTL-190SM-2000A pick] | 206.8 | MATCH (D1-08) |
| 31 | T744 | design-to 100 N m/rad | 4,9 | DERIVED | DSIG line 29 "ENG-11 servo output stiffness K_s" col 2 | 100 | MATCH |
| 32 | T745 | 110 N m/rad | 4,9 | DERIVED | same row, regex group 2 | 110 | MATCH (manual) |
| 33 | T746 | servo J 1.6e-03 kg m² | 4,9 | ASSUMED | same row [regex servo J] | 0.0016 | MATCH |
| 34 | T914 | 7294 N m/rad | 9 | SIM | KTAB /range_over_posted_R3_poses/FE_coupled_alpha/min | 7293.95 | MATCH |
| 35 | T915 | 9337 N m/rad | 9 | SIM | KTAB …/FE_coupled_alpha/max | 9337.08 | MATCH |
| 36 | T939 | gear ratio 4.8 | 9 | DECIDED | MEC /tvc_actuation/gear_ratio_n | 4.8 | MATCH |
| 37 | T943 | 37.95 N m | 9 | DERIVED | MEC /tvc_actuation/hinge_moment_design_Nm | 37.95 | MATCH |
| 38 | T946 | 7.0 deg | 9 | DECIDED | MEC /gimbal/range_deg | 7.0 | MATCH |
| 39 | T947 | 8.0 deg | 9 | DERIVED | MEC /gimbal/mechanical_stop_deg | 8.0 | MATCH |
| 40 | T967 | 2.8210 kg | 13 | DERIVED | MP /states/wet/engine/m_kg | 2.82102 | MATCH |
| 41 | T968 | 2.7380 kg | 13 | DERIVED | MP /states/mid/engine/m_kg | 2.73802 | MATCH |
| 42 | T969 | 2.6550 kg | 13 | DERIVED | MP /states/burnout/engine/m_kg | 2.65502 | MATCH |
| 43 | T970 | 2.3967 kg | 13 | DERIVED | MP /states/nograin/engine/m_kg | 2.39666 | MATCH |
| 44 | T1004 | -2.993, 1.050, 12.688 mm | 13 | DERIVED | MEC /gimballed_mass_properties_v352/states/nograin/engine/cg_mm | [-2.993, 1.05, 12.688] | MATCH |
| 45 | T1008 | 17.44 kg | 14,53 | DERIVED | DSIG row "4" col 4 (line 25) [regex liftoff mass] | 17.44 | MATCH |
| 46 | T1010 | 2.92 | 14,53 | DERIVED | DSIG row "4" col 2 (line 25) | 2.92 | MATCH |
| 47 | T1237 | 423.15 K (150 °C) | 22 | DECIDED | ELE /abort_matrix/causes/5/thresholds/kCaseOverTemp_K | 423.15 | MATCH |
| 48 | T1238 | 403.15 K (130 °C) | 22 | DECIDED | ELE …/kCaseRelightMax_K | 403.15 | MATCH |
| 49 | T4132 | 423.15 K (150 °C) | 47 | DECIDED | ELE /sensors/thermocouples/case_abort | 423.15 | MATCH |
| 50 | T4133 | 403.15 K (130 °C) | 47 | DECIDED | ELE /sensors/thermocouples/relight_refusal | 403.15 | MATCH |
| 51 | T4142 | 423.15 | 47 | DECIDED | ELE /limits_v2p11/0/value | 423.15 | MATCH (unit D1-08) |
| 52 | T4144 | 403.15 | 47 | DECIDED | ELE /limits_v2p11/1/value | 403.15 | MATCH (unit D1-08) |
| 53 | T1326 | 2.43 s | 25 | DECIDED | CMB /igniter_sequence_fields_v2p4c/v/fields/3 | 2.43 | MATCH |
| 54 | T1330 | 2.39 s | 25 | DECIDED | CMB …/fields/5 | 2.39 | MATCH |
| 55 | T1445 | 2.43 s | 26 | DERIVED | CMB /purge_decision_v2p4c/v/flow_s | 2.43 | MATCH |
| 56 | T1446 | 2.38 s | 26 | DERIVED | CMB …/both_open_overlap_s | 2.38 | MATCH |
| 57 | T1447 | 2.39 s | 26 | DERIVED | CMB …/cap_both_open_s | 2.39 | MATCH |
| 58 | T1448 | 2.44 s | 26 | DERIVED | CMB …/flow_at_cap_s | 2.44 | MATCH |
| 59 | T4150 | 2.55 | 47 | DECIDED | ELE /limits_v2p11/4/value | 2.55 | MATCH (status D1-02, unit D1-08) |
| 60 | T2018 | -0.075 / +0.239 | 34 | CALC | MMXMD line 7 "TC-01" col 18 | -0.075 / +0.239 | MATCH |
| 61 | T2021 | -0.482 (LC6 soak u) | 34 | DERIVED | MMXMD line 7 col 21 | same | MATCH |
| 62 | T2027 | -0.271 (TB70 u) | 34 | DERIVED | MMXMD line 8 "TC-02" col 21 | same | MATCH |
| 63 | T2033 | -0.201 (TB70 u) | 34 | DERIVED | MMXMD line 9 "TC-03" col 21 | same | MATCH |
| 64 | T2039 | -0.008 (F2 hot bound u) | 34 | DERIVED | MMXMD line 10 "TC-04" col 21 | same | MATCH |
| 65 | T2051 | -0.520 (LC1 y) | 34 | DERIVED | MMXMD line 12 "NZ-01" col 21 | same | MATCH |
| 66 | T2063 | -0.392 (TB70 y) | 34 | DERIVED | MMXMD line 14 "NZ-03" col 21 | same | MATCH |
| 67 | T2075 | -0.336 (TB70 y) | 34 | DERIVED | MMXMD line 16 "FD-01" col 21 | same | MATCH |
| 68 | T2156 | +0.650 / +0.278 | 34 | CALC | MMXMD line 30 "HW-101 (J-FWD)" col 18 | same | MATCH |
| 69 | T2265 | -0.075 / +0.239 (drawn fit) | 37 | SIM (to CALC, D1-07) | MMXMD line 7 "TC-01" col 18 | same | MATCH (class D1-07) |
| 70 | T2274 | MS -0.988 | 37 | CALC | LCF /governing/ii_assembly_from_zero\|Kf3.0\|worst_of_histories\|3750/MS_cycles_vs_50 | -0.988 | MATCH |
| 71 | T2275 | N_allow 0.6 | 37 | CALC | LCF …/N_allow | 0.6 | MATCH |
| 72 | T3398 | J-FWD cell +0.650 / +0.278 | 42 | CALC | MMX /rows/23/cells/J-FWD/value | [0.65, 0.278] | MATCH |
| 73 | T3402 | +0.278 | 42 | CALC | MMX /rows/23/cells/J-FWD/rows/1/MS_u | 0.278 | MATCH |
| 74 | T3404 | preload included 0.065 (information) … | 42 | CALC | MMX /rows/23/cells/J-FWD/rows/1/note | same text | MATCH |
| 75 | T4127 | proof 206.8 bar abs | 47 | DATASHEET | CL L264(4) [from "P_torch (J901" to "... and C1."] | 206.8 | MATCH |
| 76 | T4128 | required 166.14 bar abs | 47 | DERIVED | CL L264(4), same clip | 166.14 | MATCH |
| 77 | T4170 | 70000.0 | 48 | DECIDED (to DESIGN, D1-03) | ELE /limits_v2p11/14/value | 70000.0 | MATCH (status and unit D1-03) |
| 78 | T4177 | 70000.0 | 48 | DECIDED (to DESIGN, D1-03) | ELE /light_rule/kIgnBaseCheck_Pa | 70000.0 | MATCH (D1-03) |
| 79 | T4409 | 0.30 bar | 50 | DECIDED LEAD | CL L264(2) [regex kPcRezeroMax_Pa stays] | 0.3 | MATCH (add PENDING REVIEW, D1-03) |
| 80 | T4410 | 0.76 bar | 50 | DECIDED LEAD | CL L264(2) [regex kIgnBaseCheck_Pa] | 0.76 | MATCH (D1-03) |
| 81 | T4411 | 0.46 bar | 50 | DECIDED LEAD | CL L264(2) | 0.46 | MATCH (D1-03) |
| 82 | T4566 | 210 m. Profile: TVC ascent, nose drogue at apogee, relight, … | 53 | DECIDED | DSIG line 22 "Mission set: A1 apogee target" col 2 | same text | MATCH |
| 83 | T4572 | P = 0.9835 = P(sim6 landing AND >= 80 g liquid) | 53 | SIM | DSIG line 24 "A1 landing P at 210 m" col 2 | same text | MATCH |
| 84 | T698 | 33 negative cells | 1,5,35 | DERIVED | generator; recount from MMX / expected_margins_rows_v8.json | 33 | MATCH (manual) |
| 85 | T699 | BR 7 | 5,35 | DERIVED | same recount | 7 | MATCH (manual) |
| 86 | T700 | BT 2 | 5,35 | DERIVED | same recount | 2 | MATCH (manual) |
| 87 | T701 | CH 3 | 5,35 | DERIVED | same recount | 3 | MATCH (manual) |
| 88 | T702 | DC 1 | 5,35 | DERIVED | same recount | 1 | MATCH (manual) |
| 89 | T703 | MF 9 | 5,35 | DERIVED | same recount | 9 | MATCH (manual) |
| 90 | T704 | TS-183 9 | 5,35 | DERIVED | same recount | 9 | MATCH (manual) |
| 91 | T705 | TS-212 2 | 5,35 | DERIVED | same recount | 2 | MATCH (manual) |
| 92 | T708 | SET v3.5.2 final, sha16 621481ddeccc228b | 4 | DERIVED | SET (file sha) | disk = sources.json | MATCH (manual) |
| 93 | T711 | BOM v3.5.2, 9234c953c5b6beb8 | 4 | DERIVED | BOM (file sha) | identity | MATCH (manual) |
| 94 | T712 | MP v3.5.2, c1ff170be0ac8cc5 | 4 | DERIVED | MP (file sha) | identity | MATCH (manual) |
| 95 | T713 | CMB v2.4d, 7dbf425c12300658 | 4 | DERIVED | CMB (file sha) | identity | MATCH (manual) |
| 96 | T715 | MEC v2.4, 66bc53d88d444679 | 4 | DERIVED | MEC (file sha) | identity | MATCH (manual) |
| 97 | T717 | GNC v3.2, bde317782574cbd9 | 4 | DERIVED | GNC (file sha) | identity | MATCH (manual) |
| 98 | T719 | ELE v4, 11f7896ad0d0613b | 4 | DERIVED | ELE (file sha) | identity | MATCH (manual) |
| 99 | T721 | MMX v352, 6c694fa7147fb511 | 4 | DERIVED | MMX (file sha) | identity | MATCH (manual) |
| 100 | T742 | 120 N m/rad (rev0 window, SUPERSEDED) | 4 | DERIVED | CL L258(1) [regex "window (\d+)-(\d+) is withdrawn", group 2] | "window 100-120" gives 120 | MATCH (manual) |

====================================================================
5. IMAGES PAGE, IMG-01 to IMG-17 (separate block; does not change the verdict)
====================================================================
Claims file: 7dd84753b00f6f47. Page: argos-engine-images.v352.html 674e2080b0f921e4. Data: data/img_claims_check.json c0c276e2efbca7ea.

| Claim | Result | Basis and notes |
|---|---|---|
| IMG-01 | OK | set_v3.5.2.json date 2026-10-20; 11 changed PNs. Note: ENG-NZ-06 is new, not changed. |
| IMG-02 | OK | GM-01, GM-02, TC-01, TC-02, TC-03 and NZ-01 are all among the 11. |
| IMG-03 | OK | mechanical.json v2.4 design_changes_v352, ENG-HW-101 8 to 10 screws, IN718 M5 x 10.7. |
| IMG-04 | OK | BOM n_lines 107, n_instances 142. |
| IMG-05 | OK | iso_meta visible bbox 139.4 x 140.2 x 593.3 mm [DERIVED]. |
| IMG-06 | OK | 5.34303 kg wet, 4.91867 kg without grain [CALC / DERIVED, not weighed]. |
| IMG-07 | OK | -0.06618 kg against v3.5.1. |
| IMG-08 | OK | Grain OD 53.5 mm, 2 x 115 mm, 25 mm port; throat 13.724 mm, exit 19.409 mm, eps 2.0. |
| IMG-09 | WRONG (one sentence) | Correct text and sources below. |
| IMG-10 | OK | CalculiX 2.21; global L1 176,707 nodes; lever-root and J-FWD sub-models. |
| IMG-11 | OK | Note: TB70 / TBS governs 8 of the 26 chart rows and is not named. |
| IMG-12 | OK | GM-01 +0.005 and GM-02 +0.034 are LC6 soak all-node values at an ID rigid-connector node; 9 of 26 below zero; one DC cell (TC-01 J-FWD -0.075). |
| IMG-13 | OK | 26 rows and 33 negative cells equal rows v8. Note: TC-03 has no "changed in v3.5.2" mark, although it is in the CAD changed list (the matrix flag changed_v352 is false). |
| IMG-14 | OK | SF 1.5 / 2.0 normal; abnormal 1.0 / 1.5; FA-1 1.0. |
| IMG-15 | OK | DSIG rows 4, 5, 9: 17.44 / 16.11 / <= 16.15 kg (massprops v3.5.1). |
| IMG-16 | OK | P 0.9835 = P(landing AND >= 80 g liquid), N 1000 per base [SIM]; not for flight acceptance until row 11a. Notes: acceptance also waits for the canopy-delay bound; the profile has a nose-drogue descent; the basis is massprops v3.5.1. |
| IMG-17 | OK | RPL v2.2b: grid at v1 Pc 24.99 bar, O/F 7.76; v2 O/F 10.435, coarse only. |

IMG-09 correction:
- Page text (line 254): "The envelope is the bounding box of the 3D model. The forward-joint screws and two other small parts are not in the 3D model, so they do not show in the renders."
- Correct text: "The envelope is the bounding box of the 3D model. The 3D model has no standard hardware: none of the 57 hardware lines of the BOM (ENG-HW-101 to ENG-HW-170, 174 items: screws, washers and disc springs, O-rings, seals, dowel pins, thread inserts, clips, a bushing, a fitting and a thread-locker line) is in it, among them the ten forward-joint screws ENG-HW-101 and the disc springs under their heads ENG-HW-170; nor is the transport lock ENG-GM-12 (two half rings, removed before flight). So they do not show in the renders."
- Hardware counts by kind [DERIVED, BOM /hardware/lines kind and qty]:

  | Kind | Lines | Items |
  |---|---|---|
  | screw | 34 | 126 |
  | washer (includes the 10 disc springs ENG-HW-170) | 4 | 18 |
  | O-ring | 9 | 11 |
  | seal | 4 | 8 |
  | dowel | 1 | 4 |
  | insert | 1 | 2 |
  | clip | 1 | 2 |
  | bushing | 1 | 1 |
  | fitting | 1 | 1 |
  | consumable | 1 | 1 |
  | total | 57 | 174 |

- Sources:
  - 03-cad/v3.5.2/BOM_v3.5.2.json 9234c953c5b6beb8: /hardware/n_lines 57, /hardware/n_items 174, /hardware/lines[*]; /lines ENG-GM-12 (groups "lock", category "GSE (not flight)"); /gse_lines_excluded_from_flight_mass.
  - GLB 4bcc264f683e128f: 149 nodes, none named ENG-HW-1xx or ENG-GM-12.
  - 07-datasheet/build/renders/v3.5.2/iso_meta.json d9985e8966a7f30f: /pns lists 111 PNs, none from /hardware. ENG-GM-12 is the only BOM /lines PN that is absent.
  - The datasheet draft §4.2 T966 [DERIVED] says the same.
- Do not write "no hardware is modelled". ENG-HW-20, -21, -22, -22-IR and -25 are BOM /lines parts and are in the GLB (family_HW render). Only the /hardware section is absent. The PROVISION lines (ENG-BL-06N, ENG-TK-OUT), the contingency line ENG-NZ-05 (qty 0) and the GSE tool lines ENG-TC-12/-13 are not modelled by definition.

====================================================================
6. TO VERIFY IN THE FINAL BUILD (full list: data/final_build_checklist_rev1draft.json e2cc78f1a0b50551)
====================================================================
- Findings: D1-01 to D1-13 as corrected above, including:
  - C-09 retired, C-11 to C-16 present, pointers at T803 and T1427, and the cites 259 (6) and 264 (5);
  - the DESIGN pill on 70000 / 30000 Pa;
  - PENDING REVIEW on T4409-T4411;
  - T2265 shown as CALC;
  - Annex C4 printed in full and the RA-06 rows;
  - the ENG-11 spread status.
- The lead's notes: "Owners: see §9.10"; ENG-11 as two named quantities; 3133-7406 labelled "V5c plant, CAD v3.3" with a pointer to §3.3; the §9.1 manifest-of-record pointer a4713d45b3b24a0f.
- The author's staged fixes:
  - (a) Appendix A at source precision, computed values at 6 significant figures;
  - (b) §1.1 ICD row "Airframe ICD (out of the finish scope, CHANGELOG 222; no value is taken from it)";
  - (c) ovr-6 retires OVR-02, -03, -07 and -08, keeps them verbatim under "retired" and names them in §13.1;
  - Q1 (166.14 DERIVED; the table and the ladder label agree);
  - text cuts end at a word with a visible "...", and row traces keep the full name (includes N-05);
  - the p11 label clip is fixed;
  - "PRELIMINARY · rev1" on the cover and in the running header.
- Form and privacy re-scan; renders from GLB 4bcc264f683e128f.
- Re-run scripts/retrace.py on the final trace.json and sources.json.

====================================================================
7. FILES (hub reviews/datasheet/r1/; sha256/16; MANIFEST rows are "<sha256>  <relpath>")
====================================================================
MANIFEST_REV-DS-1.sha256: cfb00a6b53fe9118. It has 17 rows, and scripts/verify_manifest.py reports 17 OK, 0 FAIL, 0 MISSING.

| File | sha256/16 | Note |
|---|---|---|
| scripts/check_renders.py | 6264350e710455a0 | |
| scripts/form_check.py | 7db9b8828dc9fc14 | |
| scripts/retrace.py | 3f489c9e52cbd99a | changed in phase B: masks "[working copy; path not printed]", hub-relative source join, CL clip [from "A" to "B"], --hub |
| scripts/verify_manifest.py | 779c2d6f269629ef | |
| data/expected_margins_rows_v8.json | 386a667672863cf1 | |
| data/final_build_checklist_rev1draft.json | e2cc78f1a0b50551 | new |
| data/form_check_rev1draft.json | 068b81ae1f561007 | new |
| data/founder_actions_check_rev1draft.json | 34bb698012b5ed34 | new |
| data/founder_actions_reference_L240-L261.json | e24dd791febccf3f | |
| data/img_claims_check.json | c0c276e2efbca7ea | new; holds the IMG-09 correction |
| data/render_check_phaseA.json | 0ae59f2c04beff0b | |
| data/render_check_rev1draft.json | 73e5bf8249845b5c | new |
| data/retrace_headline_rev1draft.json | a0b98286db4ca41f | new |
| data/retrace_rev0_test.json | be37695d05fed7d1 | |
| data/retrace_summary_rev1draft.json | 8879c78b97e02a11 | new |
| data/rev0_test_ids.txt | caed4e7527eb7c7c | |
| data/sources_of_record_expected.txt | 7b1f6b251f44a0ca | |

- The folder totals 239,708 B (18 files), within the 15 MB budget.
- The meta in some data files names /dev/shm/rev_ds1/draft/ copies. Those copies were byte-identical (by sha16) to the 07-datasheet/out/rev1 originals.
- /dev/shm/rev_ds1/ has been removed.
- Free disk at 14:25:25Z: 2,176,655,360 B (above the 2.0 GB floor). No process of mine is running.

====================================================================
8. PROCESS DISCLOSURES AND NOT RUN
====================================================================
Disclosures:
- Batch 2 said "Stamp 14:05Z (date -u)". That stamp was not taken from a date -u run immediately before the send. The readings were 14:03:01Z before the send and 14:04:52Z after it, so the stamp is later than the send.
- Batch 1's stamp, 13:41:04Z, came from a date -u run a few commands before the send, not immediately before it.
- Correction to batch 2 status line (a): the headline split is 82 by the harness and 18 by hand, not 89 / 11. All 100 match.
- Correction to batch 2: "all 86 sources match" should read 85 of 86 byte-identical, with the CHANGELOG differing only by the appended line 265 (as the next sentence there said).
- At about 14:20Z I briefly re-created /dev/shm/rev_ds1 for a pdftotext extraction of p55-57 (to confirm RA-06), then removed it.

NOT RUN:
- The final-build check: no final build exists yet (checklist provided).
- Individual recomputation of the 255 generator-formula values beyond the spot checks in 3 (a). Reason: time box; their inputs are traced values that match.
- A text check of 22 chart values (p7, p8, p35 SVG). They cannot be read as text, but their trace source values match.
- 13 values split by line wrap in pdftotext were spot-checked as present rather than all matched.

END REVIEW-DATASHEET-R1
