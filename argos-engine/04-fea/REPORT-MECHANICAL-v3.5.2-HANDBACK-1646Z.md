<!-- Placed by the engine lead on 2026-10-20 from Mechanical's text handback of 16:46Z. The harness asks subagents to return reports as text rather than write report files, so the lead keeps this copy as the record. The text below is verbatim. The lead's rulings on it (16:53:21Z) are in CHANGELOG line 243. -->

# REPORT-MECHANICAL v3.5.x: v3.5.2 Mechanical state at handback

**The report file was not written.** I tried to write this report to hub `04-fea/REPORT-MECHANICAL-v3.5.x.md`, and the harness refused it: "Subagents should return findings as text, not write report files". I did not work around the refusal, so the file does not exist. Everything below is the report. If you want it in the hub, you can place it there yourself.

- **Author:** Mechanical (Senior Mechanical successor), 2026-10-20, 16:46Z (from date -u).
- **Baseline:** v3.5.1 is FROZEN; all of this work is v3.5.2.
- **Status of every number:** SIM / CALC / DERIVED unless tagged otherwise. Nothing here is physical approval. Negatives are shown as found. You own every decision: this report proposes and applies nothing.

## 1 Summary

The J-FWD re-map is done and published. It runs on FEA3D's ADOPTED envelope v3 (`fea3d/results/v352/jfwd_soak_envelope_v352_v3.json`, 0872de4ea7e3601d), whose basis is "worst computed instance, not a proven bound". The re-map comprises:
- relax v7;
- rows v6, corrected to THE ROW;
- screw LCF v2;
- spring v3.

Published together with it:
- the 239 (10) K_js5 re-run of the embedding / fit / J-F1 rows;
- the (b) package with the abort recommendation;
- the item C / T-F1 texts;
- T-F2 rev 4.

Results:
- **Abort value:** Mechanical recommends A = 150 C (423.15 K) on the case TC station.
- **Found negatives:**
  - the no-slack requirement (239 (3));
  - the seat-line = ring-line P+Q rows at the soak states;
  - the screw LCF, 183 (1)(c).
- **Slack fix, for your ruling:**
  - Route (i), disc spring: seats every case, but centring only works with a geometry proposal.
  - Route (iii), open negative plus the preload-retention audit: the joint opens 9.95 / 7.72 um.

## 2 Published state (hub /home/claude/work/shared-fallback/engine)

**Manifests and CHANGELOG**
- **04-fea/v352:** `MANIFEST_v352.sha256` b0e477763cb603db, 162 rows, `sha256sum -c` OK; 36 files new or changed.
  - The 4 replaced scripts went to `history/` and are kept beside the new ones as _v6 / _v4 / _v2 / _v1 copies at the same shas: relax 9465eaeac9af407f, rows 802559c3a4e10834, spring 6301f56f42d4a7ae, LCF 9c110e7a8e53b820.
  - So the hub's relax v6, rows v4, spring v2 and LCF v1 jsons still sit next to the exact scripts that made them.
- **03-cad/v3.5.2:** still INTERIM (interim_r4h6), MANIFEST e25b45808a8f9cf6, 212 rows, `-c` OK at 16:44Z. The FINAL set waits for rev 5, after your slack-fix ruling.
- **CHANGELOG:** Mechanical line 242 appended under flock and verified: 242 lines, sha16 cedc01e1bb6be918.
- **My messages to you:** 16:40:02Z (full results) and 16:43:42Z (CHANGELOG sha).

**Files (script -> json, sha16)**

| Item | Script | Output |
|---|---|---|
| relax v7 | `jfwd_relax_v352.py` 82221fdf0035f338 | `_v7.json` 345e27062d54ad20 |
| rows v6 | `jfwd_in718_rows_v352.py` d44587001b0b3c36 | `_v6.json` dbdb965a4160ec6e |
| LCF v2 | `jfwd_screw_lcf_v352.py` 099134dde5574c61 | `_v2.json` 6acdaa2febdf3f6c |
| spring v3 | `jfwd_spring_v352.py` 04f3079e634c77da | `_v3.json` 150900bd77dc5fc9 |
| K_js5 re-run | `jfwd_embed_fit_js5_v352.py` 671c61b55f9a086f | `_v1.json` 939b7f3708928613 |
| (b) package | `bpkg/bpkg_abort_v352.py` 83297d813ac71014 | `bpkg_abort_v352_v1.json` 4b6f849e76708a24 |
| texts | - | `texts/item_c_tf1_texts_v352_v2.json` 0c679900bb41e408 (v1 8e1ba704f5684cce); `texts/tf1_exposure_v352_v1.json` d23e72f089cca33a |
| T-F2 rev 4 | `contact/tf2_r4_refine_v352.py` 12b49b75fcc1b40d | `_v1.json` 202d3b0c36dee729, plus the driver, base driver, 6 per-bound / per-level jsons and chain10 / chain11 |
| 2(a) record | - | `jfwd_screw_lcf_sourced_v352_v1.json` b553cfe8d0bd1908 (superseded by the BK column of LCF v2) |

**Not published:** rows v5 (4d12e0187ac1a9c4). It was mapped on envelope v2 and superseded before publication, and no file cites it by sha. FEA3D's A_ROW v2 (a22a235548867570) names it for A_ROW 38.171 mm2; rows v6 carries the same 38.171.

## 3 J-FWD on the adopted envelope v3

**relax v7 (accepted at 16:07Z as the method)**
- k_b bracket, A4-80: lo 403,723 / hi 1,061,522 N/mm (from (a'') / (b2) SOAK70, 5623.6 / 7471.8 N).
- k_b, IN718 (x E ratio 1.0363): 418,365 / 1,100,023 N/mm. k_sh 33,433 N/mm.
- Seat and ring families coincide on (b2)'s ring.

| k_b end | Unseated of 24 | F_S min | Cold end |
|---|---|---|---|
| hi | 12 (both families) | -323 N at 14.501 s | 317 N |
| lo | 9 | -239 N | 372 N |

FOUND NEGATIVE: the no-slack requirement (239 (3)) fails. The select-fit cannot fix it: no gap from 0 to 0.120 mm seats all 24 cases.

**rows v6 (your 16:07Z items (2) and (3) applied)**

THE ROW is the drawn M5 x 10.2 +/-0.1 on the rev-5 flat with the TC-01 wall seated: L_e min 7.314 mm at the 0.078 gap bound, A_n 68.13 mm2 (gap 0: 7.392 mm, information).

Thread MS_y:

| State | 3750 N | 4096 N |
|---|---|---|
| PRELOAD | +1.516 | +1.303 |
| SOAK70 | +0.090 | +0.046 (flag) |
| SOAK | +0.107 | +0.062 |
| SOAK52 | +0.048 (flag) | +0.008 (flag) |
| FA1S | +1.811 | +1.544 |

- **J-F1 maximum:** MS_y 0 is reached at 4164 N, so the 4096 N maximum holds. MS_y 0.05 would need 3736 N, below the 3750 N nominal: not practical.
- **Screw length:** 10.2 +/-0.1 is RULED (tip 0.365 mm). 10.0 is a record (L_e 7.114, tip 0.565). 10.4 and 10.5 are not allowed (tip below 0.2).
- **Superseded records:** 63.48 and L 10.0 are kept only as labelled SUPERSEDED records.
- **Labels:** the IN718 key is "IN718 M5 flight L 10.2 +/-0.1 (RULED, ENG-HW-101-IN718; k_b calibrated on the FE L 10.0, length effect ASSUMED small)". The A4-80_FE sub-rows are renamed "INFO_js5_history_A4-80_withdrawn_*".

FOUND NEGATIVE (MS_PQ against 2 Fty, 3750 / 4096 N; seat line = ring line):

| State | P+Q |
|---|---|
| SOAK70 | -0.059 / -0.061 |
| SOAK | -0.075 / -0.076 |
| SOAK52 | -0.015 / -0.017 |

The head-force bounds go down to -0.183.

SECONDARY, screw fibre yield (3750 / 4096 N):

| State | Fibre |
|---|---|
| SOAK70 | -0.217 / -0.266 |
| SOAK | -0.257 / -0.305 |
| SOAK52 | -0.201 / -0.247 |

The shakedown minimum is +0.827.

Watch rows:
- Under-head Neuber at SOAK52, 4096 N: +0.015.
- TC-01 flat bearing: min +0.076 on the minimum ring (A_ROW 38.171 mm2), +0.026 on the union basis.
- Screw tension: min +0.586.

**LCF v2**
- The universal slopes (AMS 5663 minimum RA) govern, per your 15:46Z ruling.
- The BK column is labelled "LITERATURE via the UWaterloo FD+E database (JTE10109J, 1974), unread, TO-VERIFY, information only". The universal slopes give the lower life in all 306 rows.

FOUND NEGATIVE, worst of the instances (N_allow at 4096 / 3750 N):

| Kf | Per firing | From zero | Stable re-assembly (info) |
|---|---|---|---|
| 3.0 | 8.9 / 11.9 (MS -0.822 / -0.762; BK 24.16 / 30.47) | 0.7 / 0.9 | 2.6 / 3.5 |
| 2.2 | 47.7 / 68.0 | 2.4 / 3.1 | - |
| 3.8 | 3.0 / 3.9 | 0.3 / 0.4 | - |

**K_js5 re-run (239 (10), DONE; the script asserts it reproduces relax v7)**
- **Cold after embedding:** every drawing gap stays seated. At 2250 N with 21 um embedding the minimum is 772 / 701 N (lo / hi).
- **First firing at 4096 N, no embedding credit:** 5823 / 6762 N in the 1-DOF model (information).
- **In-service minimum:** -239 / -323 N.
- **Torque window without slack:** EMPTY over 2250-5461 N. F_S min is the same at every preload, because the first-firing wall set at the Fty(T) cap absorbs the installation preload.
- **J-F1 maximum:** stays 4164 N (K_min 0.1441 at 3.0 N m). The 2250-4096 N band holds.
- **Contingency fits H7/h6 and H7/g6:** they do not remove the slack. At their minimum gaps the head goes SLACK cold after embedding.
- **K_js4 rows:** stay as found, information only.

## 4 Slack-fix inputs, for your ruling

**Route (i): spring A (DIN 2093 A10 17-7 PH, derated)**

It seats all 24 cases at both k_b ends and on both families:

| R | F_S min, hi end | F_S min, lo end |
|---|---|---|
| 0 | +334.5 N | +336.6 N |
| 0.2 | +269.6 N | +271.4 N |
| 0.4 | +203.7 N | +205.1 N |

- Lift is at most 20.26 um. The spring is solid at every hot frame and stays seated for any R below 0.9999.
- Spring B, hi end: +198.3 / +159.1 / +119.7 N at R 0 / 0.2 / 0.4.
- Geometry: L 10.7, tip 0.305 mm, A_n 67.93 mm2, thread minimum +0.005.
- Head on the spring: MS +3.999 at ID 5.2. The da 5.7 row is AS RECALLED, TO-VERIFY.

FOUND, geometry:
- z-centring passes only with a d11.2 cutter: positional stack 0.328, full float 0.547 mm, against a tolerable e of 0.20 / 0.30 / 0.55 for d10.5 / d10.7 / d11.2.
- Overhang is 1.631-3.408 mm2, i.e. 97.15-94.05 % of the face is supported.

Proposals, not applied:
- P(i)-1: cutter d11.2 +0.1/0 (TO-CHECK in CAD);
- P(i)-2: accept the sliver with a drawing note;
- P(i)-3: custom spring OD of about 8.9 or less (TO-QUOTE).

Open for route (i):
- Schnorr quote with relaxation data at 160 C;
- HW-101-IN718 drawing (pilot 5.15 h9, undercut r >= 0.2);
- J-F1 spring items;
- TC-02 tap position (TO-DEFINE).

**Route (iii): open negative plus the preload-retention audit**
- Opening = |F_S min| x (1/k_b + 1/k_sh) = 9.95 um (hi) / 7.72 um (lo). This replaces the 6.5 um in line 241.
- Unseated: 12 / 9 of 24 cases. The cold residual is at least 317 / 372 N.

**Alternative (a): added series compliance**
- 5.285 / 4.138 um/kN, equal to 15.0 / 11.7 mm of extra free length at A_s. It does not fit.

Neither route changes any strength row.

## 5 (b) package

**Abort value**
- Mechanical recommends A = 150 C (423.15 K) on the case TC station; you set the value.
- **Seat:** (a)-(c) and no leak pass for TB70 at SF 1.5 / 2.0 and TBS at SF 1.0 / 1.5, on both bounds.
- **False-trip margins:**
  - +12.3 K to the rev-3 merged perfect-contact armed maximum (137.74 C);
  - +32.9 K to GVHI;
  - +41.8 K to GVLO.
- **Time above 150 C:** TC-02 stays above 150 C for 35.6 / 29.7 s after the trip (ASSUMED shifted history), against 640-1192 s at 165-175 C.
- **(d):** OPEN at every A (T-F1 gate).
- **The 175 C value of 188 (5):** cannot be shown against a sourced allowable.
- **Electronics:** must confirm its channel tolerance fits inside 12.3 K. 135 C would trip a nominal burn in the merged bound.

**Screw life (2(b) and C6)**
- A replace-every-N-firings life limit is NOT VIABLE at Kf 3.0 or 3.8 (below one firing).
- At Kf 2.2 it gives 2 firings at 4096 N and 3 at 3750 N.
- So 183 (1)(c) stays FOUND NEGATIVE and C6 stays OPEN.

**Bending-reduction proposals (2(c), proposed only)**
1. **Cut the soak bending.**
   - At Kf 3.0 it must fall by 35.8 % / 30.6 % (4096 / 3750 N). In the largest case M must go from 5338.8 to 3429.6 N mm.
   - At Kf 2.2 it must fall by 1 %; at Kf 3.8 by 55.9 %.
   - The from-zero row cannot be closed by bending alone.
   - Levers: the seat footprint and the shell pull. Each needs an FE instance.
2. **MJ-form root:** Kf TO-SOURCE, mating TO-CHECK.
3. **Lower J-F1 maximum:** helps the from-zero row only. 239 (3) already fails at both install ends.
4. **Longer grip:** needs +1.8 mm against a 0.5 mm budget. Does not fit.
5. **Spring:** does not reduce the soak fibre.

## 6 T-F2 rev 4 (promised in line 238)

**Seat matrix (236 (9)(b); stick-edge zone d = 1.0 mm)**
- 183 (1) (a), (b) and (c) pass at every burn and TB state on both bounds.
- The combined MS at the case SF is negative only at the hot states. These are TS-183 candidates, with (d) OPEN. Example, LC1 B1_19 GVLO: TC-02 +0.116 / -0.072; TC-03 at the undercut R0.6 -0.087 / -0.170.

**Refinement flag**
- At the TBS TB reference, the regular cells at the entry-tangent edge miss the 5 % test (+8-9 % per halving).
- They are quoted at h 0.1 with the h 0.05 estimate beside them; the verdicts hold at the estimate.

**n46040 model-fidelity note**
- At LC2 B1_1, the TC-03 regular minimum is at the undercut root: +0.286 / +0.169 (GVHI +0.269 / +0.153). The flange-bottom corner does not govern.
- T-F2 agrees with S-AX (+2.564 / +2.241), not with FEA3D's global model (-0.076 / -0.159). The 4x difference stays a model-fidelity note.

## 7 For your rulings (proposals only; no CAD change)

**Decisions**
- the slack fix, route (i) or (iii);
- C6 (screw life);
- the abort value;
- the P+Q band, only if (b1) is still negative.

**Rev-5 drawing items**
- **TC-01 bore:** 57.15 +/-0.10 (minimum wall 3.088 mm at the h9 OD).
- **Aft thread class:** the fits list says 6e and the notes say 6g. 6e is the rows' basis.
- **Axis B:** name the feature that defines it (proposal: the 57.25 H8 forward bore) and reference r_flat, the OD runout and the hole position to A|B.
- **Union basis:** the unsupported region under the head is the union of the head's da circle and the hole's edge-break circle. That leaves 36.401 mm2 of bearing area, 1.77 mm2 less than the ruled 38.171. I recommend it as the basis; the flat bearing MS on it is +0.026.

**Wording correction:** the rows v6 fix note says the 24-case minimum is "set by 2250 N". The 4096 N cases reach the same minimum. No number changes.

## 8 Open after this report

- **After chain E:** (b2'), (b1) and js5b join the envelope, then relax, rows, LCF and spring are re-mapped.
- **Rev 5** (items 6 and 8 of line 241, plus any slack fix), then:
  - the FINAL 03-cad set;
  - `interfaces/mechanical.json` for v3.5.2 (still v2.1, 2026-10-13);
  - the datasheet.
- **T-F1:** needs sourced allowables or coupons.
- **Route (i) quotes.**

## 9 Process record

- No solver or thermal run this segment. No ccx of mine is running; the ccx at PID 21023 is FEA3D's chain E.
- Nothing was deleted. The 23 refused v3.4.1 res.npz files were untouched.
- I wrote only to:
  - `/home/claude/work/mechanical/` (work tree and PROGRESS, updated 16:46Z);
  - hub 04-fea/v352 (the publish);
  - the CHANGELOG, through flock.
- The report write to hub 04-fea was refused and not worked around.
- Free disk was 2.45-2.53 GB, above the 2048 MiB floor.
- Every stamp is from `date -u`. I messaged only "main".
- Nothing from the invalid 16:33Z run (the v3.4.1 mesh under the v3.5.1 thermal) is in any table here.
