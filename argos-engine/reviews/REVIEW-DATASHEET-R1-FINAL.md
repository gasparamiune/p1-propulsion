# REVIEW-DATASHEET-R1-FINAL (REV-DS-1, final check)

Independent check of the ARGOS H1 engine technical datasheet rev1 FINAL (`07-datasheet/out/rev1/ARGOS-H1-ENGINE-DATASHEET_rev1.pdf` e44ce71c0aecd4e5, 161 pages) against the checklist `reviews/datasheet/r1/data/final_build_checklist_rev1draft.json` e2cc78f1a0b50551, the lead GO conditions and the lead rulings. Returned by the reviewer 2026-10-21T16:54:25Z (transcript) with report stamp 16:53:34Z (date -u). Saved here by the lead on 2026-10-21T16:56:03Z (date -u), verbatim from the reviewer's final message: the harness does not let a subagent write a report file, so the handback text is the review. Reviewer artefacts: `reviews/datasheet/r1/final/` (six files), listed with the earlier ones in `reviews/datasheet/r1/MANIFEST_REV-DS-1.sha256` f840cb4854807a59, 23 entries, verified by the lead 23/23 OK at 16:55Z. The draft review is `reviews/REVIEW-DATASHEET-R1.md`. Verdict: PASS WITH NOTES, 0 BLOCKING; the final may be published; notes N-1 to N-8 change no value and go to the next build. Lead disposition: CHANGELOG line 268. A hash match or a rendered page is not physical approval, and no hardware has been tested.

```text
BEGIN REVIEW-DATASHEET-R1-FINAL
DRAFT PDF: REV-DS-1 no longer needs the draft PDF 8e7d007d128dfb58. This check did not open it. I used out/rev1/trace_rev1-draft.json 4e8fcae9ddf5d941 only to map draft trace IDs to the final ones, and I do not need that file any more either.

Reviewer: REV-DS-1 (independent; same brief b84261ade095ef07). Stamp 2026-10-21T16:53:34Z (date -u, read just before this return). Everything below is DERIVED by REV-DS-1 from the files. A hash match or a rendered page is not physical approval, and no hardware has been tested.

VERDICT: PASS WITH NOTES. 0 BLOCKING. The final (PDF e44ce71c0aecd4e5, 161 pages) may be published. The 8 notes below change no value. N-2 is the only gap against a GO label condition. I recommend fixing it in the next build; it does not block.

1. CHECKLIST (final_build_checklist_rev1draft.json e2cc78f1a0b50551), item by item
| Item | Result | Evidence in the final |
|---|---|---|
| D1-01 | PASS | p36 T524 (draft T529) and p45 §9.10 item 1 T4039-T4042: [0.040, 0.0761] is marked "[superseded: R2-B [0.040, 0.0631] mm ... 254 (1) T525; band re-size done, band v1 1ba3147b42edfeed T528]". C-11 is present and C-04 says "See also C-11". |
| D1-02 | PASS | 2.55 s is marked as the v2.11 value, superseded. p51 OI-PURGE-CAP is closed with FINAL 2.43 / 2.39 s and (d) (d1) (d2), labelled ACCEPTED (REV-ELEC-4, line 266) T027. C-12 is present. The checklist's "PENDING REVIEW" wording is superseded by the promotion (266 (7)). |
| D1-03 | PASS | The 70000 / 30000 Pa rows are DECIDED Design value (v2.11), never LEAD, with the 253 (5) note. T4326-T4328 (0.30 / 0.76 / 0.46 bar) are DECIDED Lead 264 (2); 0.76 / 0.46 carries ACCEPTED (REV-ELEC-4, line 266). The kIgnBaseDrift basis is SUSPENDED UNTIL v2.13. C-13 is present. |
| D1-04 | PASS | §13.3 p66-68: C-09 is retired with its reason; C-11 to C-16 are present; the C-14 pointers sit at T801 / T1436 (draft T803 / T1427). C-05 cites 259 (6) and C-06 cites 264 (5). C-16 is closed with its residual open. "See also" pointers: C-04 to C-11, C-10 to C-14, and back. |
| D1-05 | PASS | T892 is 166.14 bar abs DERIVED, with basis 256 (R4-12) and 264 (4); the p7 ladder label agrees. T4198 (draft T4159) keeps the quote and adds the note. |
| D1-06 | PASS | §12.3 p58-62 has RA-03; B-TC-1 tau <= 0.25 s; T-F1 routes (i)/(ii) in full; the RA-06 rows ENG-TC-12, ENG-TC-13 and the match-drill fixture; RA-15; RA-32 with T024 / T025; the post-abort rule in full, including "HIGH side (transducer output >= 4.75 V = 146.5 bar abs)"; and the CF-4 / B-BLEED-1 row on p61 (T4867-T4869: >= 0.91 x Cd 0.70, re-set rule, (d1)/(d2)). Annex C4 (p61-62) prints steps 0-9 in full: gate J-F1; pins GO 5.50 / NO-GO 5.62; tap gauging; plugs and band; S01/S02 lubricant TO-SELECT; clock and push to 2.00 +/-0.02 TO-CONFIRM; registration screws first; flight screws one at a time with a new oriented HW-170 at the J-F1 lot torque by M-T1J; never re-torqued; proof / leak test. Check-T5 reports the texts identical (T4941 / T4942). |
| D1-07 | PASS | T950 CALC, T952 SIM, T914 SIM, T1214 CALC, T4404 TO-VERIFY (draft T942 / T944 / T912 / T1205 / T4342). Draft T4182 is split into T4233-T4238, each with its own tag. Draft T2018 / T2265 are now the one trace T2030, CALC on p34 and p37, per the 14:30:54Z ruling. |
| D1-08 | PASS | §10.5 p48-49 is at source precision (423.15, 403.15, 523.15, 333.15 K; 0.012825 s). §10.3 units and the §2.3 ladder (bar vs bar abs) are correct. For Appendix A see N-1. |
| D1-09 | PASS | §12.6 p64 heading: "for information, not for execution ... 266 (7)". T4997 "nothing: executable now" carries "[not for execution ... T4929]". |
| D1-10 | PASS | §7.9 p28 T1553-T1556 carries 264 (5), and 261 (2) is marked superseded (C-15). |
| D1-11 | PASS | p25 / p26 read "combustion REPORT §2.8" / "§2.7". |
| D1-12 | PASS | "Por revisar" appears 0 times; the text prints "to be reviewed". |
| D1-13 | PASS | §3.3 p9 is per axis: alpha 7294-9337 and beta 3972-7172 N m/rad SIM. Beta is ±28.7 % (T944) against ±20 % (T941, tagged "DERIVED (GNC csi_v3)" in REQUIREMENTS.md). OPEN under 188 (7) T945. The hard minimum holds (beta min 3971.84 SIM T920). The §12.5 row on p62 has the status sentence, the owners and "open item 11b". |
| notes | PASS | "Owners: see §9.10"; ENG-11 (REQ) and "GNC row 8: servo output stiffness K_s" both named; "V5c plant, CAD v3.3 (188 (7) T945, 227 T4983)"; §9.1 manifest of record a4713d45b3b24a0f, 456 rows. |
| staged | PASS with notes | (b) the §1.1 ICD row is exact. (c) OVR-02/-03/-07/-08 are retired and named in §13.1. Q1 is in. The cover reads "PRELIMINARY · rev1". The N-05 cut is fixed (p18 "2026-10-13) …"). The p11 label clip is fixed. Open points: (a) Appendix A precision, N-1; one cut inside a path, N-6; the p11 leader lines, N-7; the header word order, N-3. |
| form | PASS | 161 pages; footer and status line on 161/161; 43 fonts, all embedded; 31,046,954 B; 5237 internal links, 0 broken, 0 external; TO-QUOTE 287; DK-6400 39. Section refs left unresolved are the same set as the draft (external REPORT / RPL §). |
| sources | PASS | See section 4. CHANGELOG: head -n 264 is f7efe784da3944c5 (unchanged); the build cites 266 lines, 4cde8acb297d195c. Lines 265-266 are new since the draft, and I checked line 266 against the build. Line 267, c0882e222a113756, was added after the build; the file is now 267 lines, 9d912f1ecfd9c1f3. |
| extra: TC-01 J-FWD class | PASS | T2030 is CALC in both places. |
| extra: ENG-11 spread | PASS | ±28.7 %, matching my 0.2872. |
| extra: IMG-09 | PASS | T974 (p4, p10): all 57 standard-hardware lines and ENG-GM-12 are not in the GLB. |

2. GO CONDITIONS (LEAD-TO-DS-GO-FINAL-1448Z 8e4b1b23dab8694d)
- **Promoted v4.1:** PASS. T020-T023: c862375163393adc, with v4 11f7896ad0d0613b kept. The review table has the REV-ELEC-4 row (ACCEPT WITH COMMENTS, 0/1/5/11, 70b7103472eebab4).
- **266 (6) carve-out:** PASS. T024 is verbatim on p47-48, p52, p57, p60, p61 and p62. The consequences (T025: A1 FLIGHT NO-GO; stand on the fallback only within 264 (2) with k <= 2 / k <= 1; F-10 MISSING; no stand relight, T4 waits; option (b) stays the design) are on p60 and p62.
- **Labels at the value:** PASS with N-2. ACCEPTED (REV-ELEC-4, line 266) T027 appears 26 times (p26, p47-52, p54). SUSPENDED UNTIL v2.13 (266 (6)) is on p5, p47-50, p52-54, p64 and p68.
- **266 (7) corrections:** PASS. C-02 superseded; TC4 = C1 seat TC (U904, J904, BOM 205); the E4-02 eps_max table sits next to every "within 5 % at k = 3" in §10, §12; E4-03 to E4-06; bench plan v5 is held by T4929.
- **266 (8) items:** PASS. T030 QUEUED (p5, p61, p62). T031 routed: E4-N08 to Combustion and the lead at B-BLEED-1; the SEAT_STEP FC rule and the release predicate to GNC and the lead with v2.13.

3. LEAD RULINGS: every ruling in 1324Z, 1345Z, BATCH1-1347Z, BATCH2-1405Z and FULLREVIEW-1430Z is applied. I re-hashed all five files plus GO-1448Z and the author report 464aa7c7be62e50b; all match. This covers:
- Q1;
- the nine contradictions plus C-11 to C-16, and C-09 retired;
- C-17 not used;
- the D1-13 sentence;
- the REV-DS-1 row verbatim (p57 T4738);
- the status word, with one deviation in order (N-3).

4. HARNESS on the final (scripts unmodified)
- **retrace.py 3f489c9e52cbd99a:** 5105 traces; 4812 MATCH, 268 not compared, 25 flagged. This reproduces the author's counts.
  - All 25 flags resolve:
    - 19 identity rows (file name plus sha) match disk and sources.json;
    - 3 combustion REPORT sentence splits, 2 two-group regexes and 1 csv locator are the same kinds as the rows I verified by hand on the draft.
  - The only source sha change is the CHANGELOG append; all 139 cited line shas are unchanged.
  - The 22 display flags are chart values (T888, T899, and T2184-T2222 on p35).
  - The 14 pdf-shown flags are all printed on their pages (wrapped).
- **form_check.py:** as in the form row above.
- **check_renders.py:** all OK (GLB 4bcc264f683e128f, BOM 9234c953c5b6beb8, 16 views). Its output is byte-identical to render_check_phaseA.json (renders and CAD unchanged; run without the assets argument).
- **asset_diff.py (new):** the final assets differ from the v3.5.2 render PNGs by at most 3.75/255 (family_PD; iso.jpg 3.17; iso.png 0.0). This shows only where the pictures came from. For line 268: 266 (3)'s "at most 2.9 / 255" was the draft's figure.

5. PRIVACY re-scan: the only agent_words hits are the 2 on p5.
- T756 is kept under N-01.
- T758 ("resumed 12:51Z at effort max"; "p1 PR #5 cf92b16..4c852a7"; "names the private benchmark") contains no secret, credential, e-mail, model identifier, benchmark name, private path or content from the OsoCordobes/ARGOS-H1 repository. "Effort max" is a run setting, and the PR and commit range are the project's own push record. I agree with the lead's ruling that T758 stays; it is not BLOCKING.
- form_check_final.json stores only those 2 hits.

6. NOTES (none blocking; exact fixes)
- **N-1, Appendix A:** about 19 converted values print float noise (T812 "25.010070000000002 bar", T044 "140.23000000000002 mm", T880-T882 "25.000000000000004 bar"). Fix: round converted display values to 6 significant figures (staged (a)).
- **N-2, p69-70 §14 and p61:** the v4.1 open-issue texts T4510, T4525, T4643, T4648, T4653 and T4658, and the F-10 inquiry T4910 ("the firmware residual budget uses k = 3 and the SIL S13T sweeps k 1-3"), show option (b) residual / S13T outcomes without "SUSPENDED UNTIL v2.13 (266 (6))". T4648 also keeps "about 5 % at k = 3" without the E4-02 correction, and T4510 (purge) lacks the ACCEPTED label. §10.9 carries all of these, and T4929 holds the bench plan. Fix: one line under the §14 heading ("rows from electronics.json v4.1 /open_issues carry the §10.9 labels and corrections: SUSPENDED UNTIL v2.13 (266 (6)) for option (b) / S13T rows, ACCEPTED (REV-ELEC-4, line 266) for the purge row, E4-02 replaces 'about 5 % at k = 3'"), and the SUSPENDED mark after T4910.
- **N-3, running header:** it reads "· PRELIMINARY · rev1 ·"; the 1345Z text is "· rev1 · PRELIMINARY ·". Fix: swap, or the lead accepts the order. The cover matches.
- **N-4, lead-side:** 266 (3), quoted at p57 T4739, says "86 of 86 sources match". It should be 85 of 86 plus the appended CHANGELOG line. Its "14:05Z" batch stamp was not a date -u reading (disclosed at 14:25Z).
- **N-5, known item:** p5 T030, p61 and p62 show v2.13 "QUEUED, NOT STARTED (the founder says when)". That is the record as of line 266; v2.13 has been running since 15:33:17Z (founder "Start now" at 15:28:53Z). Line 268 records it, and no rebuild is needed. I agree.
- **N-6, p154 T4680:** an Appendix A cut falls inside a path ("payload_n500/p…"). Fix: cut at the "/".
- **N-7, p11 group strip:** the leaders of "injector head assembly" and "throat insert and sleeve" touch "+251 mm" and "CAD z -232". The text stays readable. Fix: offset the lower-row leaders.
- **N-8, p5 §1.5 T757:** the quoted 264 (1) "PENDING REVIEW" has no superseded mark. p52 T022 has one. Fix: add "[superseded by the promotion, 266 (7) T023]".

7. NEW FILES (hub reviews/datasheet/r1/; sha256/16, bytes). All are added to MANIFEST_REV-DS-1.sha256, now f840cb4854807a59 with 23 rows; verify_manifest gives 23/23 OK and the 17 old rows were re-verified first.
- final/data/final_check_rev1final.json efcb8e9fbcd98965 8,683
- final/data/retrace_summary_final.json 9a6933861e93b4d1 10,645
- final/data/form_check_final.json 3ed706373cd905b6 8,350
- final/data/render_check_final.json 0ae59f2c04beff0b 10,812
- final/data/asset_diff_final.json 168802f5eec5e843 642
- final/scripts/asset_diff.py 7da006dd632f34d7 1,480
- Folder: 280,921 B (41,213 B net-new). Free disk at 16:53:34Z: 2,319,142,912 B. /dev/shm/rev_ds1 was removed at 16:52Z. I wrote no CHANGELOG line.

8. PROCESS DISCLOSURES
- (a) At about 16:28Z one read-only command used cd, including a subshell cd into out/rev1/assets. This is against the brief. It had no effect, and I recomputed the asset listing hash without cd (efc6efcd03261385, which matches).
- (b) At 16:38-16:41Z one of my own commands hung: a wrong CHANGELOG path left a variable empty, so sha256sum and head read stdin. I killed only my own processes by PID (17064, 17201-17203, shell 17058). No file was changed. The correct path is interfaces/CHANGELOG.md.
END REVIEW-DATASHEET-R1-FINAL
```
