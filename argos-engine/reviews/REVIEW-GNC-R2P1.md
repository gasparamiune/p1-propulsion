REVIEW-GNC-R2P1 (REV-GNC-4): independent document check of GNC staging v3.1 rev2.1

**Who and what**
- Reviewer: the same independent reviewer as REV-GNC-3, not an author of rev2.1. Date 2026-10-13, effort max.
- Declared limitation: some numbers in rev2.1 are my own REV-GNC-3 numbers (RG-16, V probes, G tables). For checks (c) and (e) I am therefore checking citations of my own work.
- Object: hub 01-systems-gnc/staging_v3.1/rev2p1/.
  - MANIFEST_rev2p1.sha256 02c554a2f0fe68fa: 12/12 OK at the start and again at hand-back.
  - JSON c2860bd89c1e5920, still unchanged at hand-back.
- Scope: the gnc.json v3.1 publication gate (RV3-01).
  - No flights were run.
  - The rev3 flights were not reviewed.
  - Nothing outside my scratch area and hub reviews/gnc/rev2p1/ was written.

## 1. Verdict

**PUBLISHABLE WITH CORRECTIONS. Not publishable as staged.** Because of RV4-01 (BLOCKING), publication must wait until C1 is applied. All five corrections are text: folds of decided lead lines and fixes to citations. None needs a flight or a new computation.

**Mandatory corrections**

- **C1 (RV4-01):** fold lead line 186 (1)–(2) into these keys:
  - status
  - requirements.ignition.relight_conditions
  - flight_software.rev2p1_entries.purge_commit_rule and the R2 entry
  - rev2.amendment_G_late_commit.finding
  - open_items[32]
  - pending_inputs_rev2p1 (combustion_unpurged_start, cold_flow_bound)
  - checkpoint unknowns[2]
  - fmea_inputs_rev2p1
  - the W10 entry under launch_commit_rev2p1
  - the rev3 plan and open items
  - the fold map

  Move the old text under *_superseded keys rather than deleting it.
- **C2 (RV4-02):** add a validity statement. The figures are at ledger v3d and are not demonstrated for CAD v3.5.
- **C3 (RV4-03):** mark or scope the stale items.
- **C4 (RV4-04):** fix four citations.
- **C5 (RV4-05):** define the rev3 items, add pointers in changes_from_v3, and replace the staging wording at publication.

**Recommended, not gating:** RV4-06 and RV4-07.

**Re-review rule**
- No further independent review is needed if two conditions hold:
  - the diff against c2860bd89c1e5920 touches only the keys named in C1–C5 (plus the fold map and open items);
  - no GNC-computed numbers are added.
- Any new computed number, such as an F_cold re-fly or the v3.5 flights, needs its own check.

## 2. Findings

### RV4-01 — BLOCKING

**Gates**
- gnc.json v3.1 publication, until C1 is applied.
- SIL/HIL freeze and A1: the purge-commit rule and the R2 command hold must enter the flight-software requirements before freeze, and the A1 FMEA must be updated.
- B1 and FC_THRUST arming: none identified.

This is not an author error: line 186 was appended after GNC's result (line 184).

**Evidence (t10 v2)**
- Unmarked hits: C09 ×5, C10 ×2, C11 ×1, C15 ×2, C16 ×3.
- Required checks R01, R02 and R07: NO.

**Stale text at each location**

| Key | Stale text |
|---|---|
| status | "L* = 1.7 s if an unpurged start is LO, 1.3 s if HI; FSW interim 1.7 s" |
| relight_conditions.v | "interim 1.7 s; else the relight proceeds unpurged" |
| purge_commit_rule.v | "(interim 1.7 s; 1.3 s if HI); else no purge, relight unpurged" |
| G finding | break-even "against PURGE NOT RUN LO, P_total ~0.75"; H20/OI-31 "pending a lead decision" |
| open_items[32]; pending combustion_unpurged_start | "not decided by the lead" |
| cold_flow_bound | "0 / 5 / 10 N parametric" |
| unknowns[2] | "cold-flow apparent thrust unbounded" |
| fmea v[3] | PURGE NOT RUN, HI only |
| fmea v[4] | "R2 holds the drogue", from flights with no cold flow modelled |

**Why it blocks**
- **Line 186 (1), unpurged relight.**
  - At the worst PURGE NOT RUN states, an unpurged start has P 0 under both LO and HI. The outcome is released-then-A3: a dead vehicle at about −32 m/s.
  - The lead therefore decided: below L* = 1.3 s, no purge and no unpurged relight.
  - If published as staged, the flight-software entry would put the refuted behaviour into the interface.
- **Line 186 (2), cold flow against the R2 threshold (37.16 N).**
  - At a 200 N command, cold-flow apparent thrust is 35.6–37.5 N. That alone reaches the threshold, so without the command hold R2 could release a dead vehicle.
  - At the 62.5 N start level the bound is 12.5–13.3 N. This exceeds the all-winds margin of 4.16 N.
  - Inside W10 < 6 m/s the margin is 16.31 N. About 3.0 N remains (16.31 − 13.3, my own arithmetic).
  - Chamber heat pick-up is TO-VERIFY.
  - So the "R2 holds" FMEA entry now depends on both the command hold and the W10 rule.

**Required changes (C1)**
1. L* = 1.3 s for both brackets. Below it, no purge and no unpurged relight on that pass (drogue descent, vehicle loss).
2. Mark the P_total ~0.75 premise REFUTED.
3. Mark H20/OI-31 as decided by line 186 (1). LO/HI stays open (CF-4, T4).
4. Add the R2 command hold (start level 62.5 N until release, while the drogue is attached with Pc invalid) to relight_conditions and to the flight-software R2 entry.
5. Replace "unbounded" with Combustion's DERIVED bound (cold_flow_thrust_v2p4a.csv e094c4be80d12f66). Keep heat pick-up as TO-VERIFY (CF-3, T series).
6. FMEA:
   - the PURGE NOT RUN entry covers LO and HI;
   - add the loss of a below-L* pass;
   - qualify v[4]: no cold flow was modelled, and the hold relies on the command hold and on W10 < 6 m/s.
7. In the W10 "why" text, state that the W10 rule now also carries the R2 flame-out margin.
8. Add to the rev3 plan:
   - the alternative relight, release held to ≥ E2 + 0.22 s; the lead adopts it only if it gains P without the released-dead-vehicle hazard;
   - the R2 v2 re-fly with F_cold(lift, P_tank).
9. Add 186 (1)–(6) to the fold map. Items (3)–(6) can be marked "no GNC change" or given their effect.

### RV4-02 — MAJOR

**Gates**
- Publication (C2 is mandatory).
- A1: the 285 m target and its P and reserve figures are not demonstrated for CAD v3.5.
- SIL/HIL freeze: the rev3 flights at the v3.5 (then v3.5.1) ledger must come first.
- B1: the same statement applies. The +0.60 kg B1 probe does not cover +0.87 to +1.17 kg.

**Evidence**
- Status (2) does give the growth: CAD v3.5 against ledger v3d is +1.168 kg. It also says "the 0.10 kg trigger is met; flights at the v3.5 ledger are rev3 P2".
- But no section says that the P, reserve, closure and trim figures were computed at ledger v3d (18 items, 13.6706 kg). t10 R05 is NO.
- The growth runs from +0.868 kg (valves at target) to +1.168 kg (valves ASSUMED). That is about 3–17 times my DERIVED first re-exhaustion at 285 m, which was 0.07–0.28 kg (REV-GNC-3).
- The document's own +0.60 kg probe (rev2.apogee_trim.decision) already shows exhaustions at every flown target from 300 m down to 275 m.

**Required (C2):** add that statement to the status, flight_profile, propellant closure and apogee-trim sections. It adds no new numbers.

### RV4-03 — MINOR (gate: publication, C3)

Each item below is stale and is not marked.
- **300 m targets** (t10 N01 ×5):
  - flight_profile.mission_plan_v3.v.A1.apogee_target_m = 300.0, under a REQ tag;
  - propellant_closure_v3 table DC-A1 and DC-A2 h_target_m = 300.0;
  - the A1 and A2 h_target sweeps start at 300.0.

  None of these sections carries a status. A1 is 285 m (lines 175 (1) and 181 (6)).
- **Duty cycle.** duty_cycles.v.current keeps DC-A1_full_flight_drogue_fins_300m_v3 as "BASELINE flight ... A-D 300 m". It does not say whether that record remains the envelope for 285 m.
- **Pre-R2 release predicate** (C12). rev1_items.v.drogue_release_rule holds "RELEASE iff b4 AND [(d2-d3 != 0xFFFF AND d2-d3 >= 300 kPa abs) OR b7]" and "no value is proposed here". R2 has been adopted (181 (4)).
- **Unscoped "0.81 s plan holds"** (C13) in rev1_items.v.purge_cost_A1_reserve.decision. Line 181 (2) scopes it to the predictor path.
- **Pivot station** (C14). conventions.stations says "RV-1c: pivot at 0.2223 m = mechanical.json frames.rv1_station_of_pivot_m". Both mechanical.json v2 and vehicle_v3d.json give 0.203 m.
- **Build basis** (R03). publication_note.built_on and bases name only sim6/run6 v2.6 / v2.7.1-dev and iface_v3c. The rev2 and rev2.1 evidence runs on v2.9-dev with iface_v3d (combustion.json v2.4).

### RV4-04 — MINOR (gate: publication, C4)

1. **Wrong source file for the W10 winds** (C18). launch_commit_rev2p1.v[1].why cites s04_wind.out (40ac5dc493ea98e1) for W10 6.96–7.84 m/s.
   - s04 holds no per-run winds.
   - The values are in s03_trim.out (819a79cf0db42fda): failing-run winds 6.956–7.836 m/s, n 24.
   - They are also in REVIEW-GNC-R2.md §4.2 (fabfc81fa1d70327, lines 224 and 526).
2. **Run count** (C17). The G finding says "in every run where the plain trigger fired (2000 runs; …)".
   - The plain trigger fired in 649 of the 2000 runs (s15_g_decided.out be3a6105746f9bce, line 5).
   - The 2.66 s minimum lead is over those 649 runs.
   - The copy of this sentence in finding_superseded_rev2p1 is history and can stay.
3. **RG-16 margin** (C19). "RG-16 margin 0.012 %" appears in pending_inputs_rev2p1.vibration_spectrum and in checkpoint unknowns[1].
   - It is my number and is not attributed: D2 strict window 0.5 s, 2.973 % against 2.985 % (rv_rg16_budget.json 65939777a57180ec).
   - Its unit is percentage points; the relative margin is 0.4 %.
4. **W < 6 m/s probe** (R06). reviewer_probes.inside_W10_lt6_N is {t05_max 18.75, t08_max 20.06, n 364}.
   - Its base is not stated: it is the A1_none probe (REVIEW line 330).
   - The binding value that line 186 (2) uses, A1J_pc 20.85 N at 0.5 s (REVIEW line 317), is missing.

### RV4-05 — MINOR (gate: publication, C5)

- **Undefined labels** (R04). "rev3 P2/P3/P4/P5/P6/P7/P9" appears 29 times across 25 strings.
  - No key defines them.
  - next_closure only says "GNC rev3 (line 181 items 2-8)".
- **Change list.** changes_from_v3 (6 entries) has no pointers to changes_rev2 and changes_rev2p1.
- **Staging wording** (U01–U04):
  - version "v3.1-staging-rev2.1";
  - status "NOT PUBLISHED";
  - supersedes "nothing yet (staging)…";
  - the checkpoint's "status Por revisar".

### RV4-06 — NOTE (not gating)

- **Canopy.** 181 (2) "canopy dynamics remain TO-VERIFY" appears only inside the verbatim block.
- **B1 grain gate.** The 181 (9) cost of 27.2 % of draws appears only inside the verbatim block.
- **Full bit-check run.** 181 (8)/RV3-07: the full bit-check v1.2 run is deferred to "rev3 P9" without an open item.
- **Bay wall.** 182 (5): at the 8° stop the gimballed engine reaches r 70.6 mm against the 70.0 mm bore. If the stop is reduced to fix this, TVC authority changes. There is no GNC open item for it.
- **m60 per-base loss.** Comparator M60-purge-liq-A1none is −6/+0 (p 0.031), LOSES per base.
  - The m60 statement reports only the pooled and mass-effect rows.
  - Its "none loses by the rule" is correct for those rows.
- **Fold-map wording.** The fold map says "175 (5): SUPERSEDED by 181 (4)". In fact 181 (4) adopts R2; only the 0.8 s proposal was not adopted.
- **Margin rounding.** In line 186 (2), 4.16 N = 37.16 − 33.0 (rounded). With 32.98 N it is 4.18 N. The difference is immaterial, but the fold should quote 4.16 N as the lead's value.

### RV4-07 — NOTE (gate: mass change control for A1/B1; no publication effect)

- **ASSUMED share.** 0.701 kg of the +1.168 kg is ASSUMED, about 60 %:
  - bleed fixed side 0.65 kg, of which the valve pair is 0.60 kg;
  - EL-11/12, 0.05 kg;
  - horns, 0.001 kg.

  Fasteners and the torch line are not in CAD v3.5. The author lists this as an open item.
- **Ledger P00 label.** Ledger v3d P00 says "half pushrods", but its 2.1565 kg is the mechanical.json v2 dry group, which excludes horns and pushrods. The author caught the same error in P07 only.
- **BOM against massprops.** BOM quantity × unit-mass sums differ from the massprops groups by up to 0.024 kg, because some rows belong to several groups. Using massprops, as the author did, is correct.
- **Inputs outside the hub.** Two cited inputs are not in the hub, and the JSON says so:
  - S10_review_foldin.json (0e5d91c74aa88fe3);
  - relight_latency_sup_v2p4.json (f0ea1eb9905919ce).

  Copies in the hub would make the published file self-contained.

## 3. Results by check

**(a) RV3-01 (a)–(f): all fixed or marked.**
- I used my own patterns, not the author's: 38 broad patterns (t01), triaged by hand, then t10 v2.
- t10 v2 patterns C01–C08 cover the RV3-01 items: 650 N confirmed, ≤ 1 % at 1 sigma, budget OPEN, "costs no P", time-only term, pcf_tmax 0.8, provisional support, 0.30 kg. All have 0 unmarked hits.
- The author's own rule reproduces as 32 hits / 0 unmarked (t13).
- My scan also found the stale items that the author's patterns did not cover (RV4-03).

**(b) Lead lines folded faithfully.**
- Lines 175, 177 and 181–183 are byte-identical to the CHANGELOG (t12), and the pinned hash of lines 174–183 (09521fead2bdf7d8) matches.
- Present:
  - the L* rule (now superseded by line 186; see RV4-01);
  - R2 with pcf_tmax 0.5 s, and 0.8 s NOT ADOPTED;
  - the RG-16 PROVISIONAL 0.5 s allowance, strict form, no window-gain credit;
  - FC_THRUST NOT armed on A1 (status (3), the fc_thrust entry, FMEA v[0]);
  - the 0.10 kg trigger;
  - W10 < 6 m/s AND sigma_u ≤ 1.0 m/s, HARD for A1;
  - Pc VALID at launch commit, for A1 and B1.
- Gaps are listed in RV4-06.

**(c) G basis cited correctly.**
- The per-delay and per-lead loss values match s08 (abd636cdac9d11ec).
- The −39/+3 comparison (p 5.6e-9) matches the PLAT-e19-liqnone comparator row.
- "0.81 s plan holds" is scoped to the predictor path in the status and in the G finding.
- Exceptions: the unscoped copy in rev1_items (RV4-03) and the 2000-versus-649 wording (RV4-04).

**(d) RV3-08 and RV3-09 closed.**
- G6 pass criterion: passed = decided arm clean AND P30 reproduced AND gate-off CA arm flags the starts. Part G uses it.
- My re-derivation:
  - run 1 (187d4d6ac8d5848d): FAIL, because it has no P30 arm;
  - run 2 (e945cc883b459701): PASS. P30 gives 6 starts above 200 m (max 304.0 m), gate-off CA flags 6, and the decided arm has 0 (max 129.6 m).
- Tool v1.1 → v1.2 contains additions only.
- The code-hash table matches the staged sim (sim6 f90e0ba8e993ad60, run6 b054a222eff38b6e).
- Comparators: I recomputed all 69, not just a sample, from the 100 rev2 tables, each checked against MANIFEST_rev2. Zero differences, including every LOSES row.

**(e) Attribution.**
- No GNC claim presents my RG-16 or V-probe numbers as its own, except the unattributed "0.012 %" (RV4-04).
- t09 flagged 111 numeric hits. The others are either attributed REVIEWER, GNC's own data tables, or unrelated quantities that happen to share digits.
- Citations: 156 path/hash citations, 153 verified.
  - 1 is a historical CHANGELOG hash, as expected.
  - 2 are outside the hub (RV4-07).

**(f) Mass arithmetic correct.**

| Quantity | Value |
|---|---|
| Landing mass growth | +1.16777 kg |
| Same, with valves at the 2 × 0.15 kg target | +0.86777 kg |
| Gimballed mass growth | +0.23672 kg |
| TVC inertia about the pivot, dry | +4.94 / +5.45 % |
| TVC inertia about the pivot, wet | +4.83 / +5.32 % |
| TVC inertia about the pivot, mid | +4.85 / +5.35 % |

- The +1.16777 kg equals the sum of the nine mapping deltas. It also equals the massprops no-grain module (4.78537 kg) minus v3d P00+P06+P07+P09+P10 (3.6176 kg).
- Gimballed: 2.39322 − 2.1565 = +0.23672 kg.
- The inertia changes match the stated +4.8 to +5.5 %.
- The ledger v3d total is 13.6706 kg.
- Hub and work-area inputs are hash-identical: massprops 8c11e1e136fc59d8, BOM 503e412b31fe4794, ledger e4fb6a40c28751cc, mechanical.json v2 4f024ed4ccb4618c.

**(g) What would mislead a reader if published now.**
- Substantive: RV4-01 and RV4-02.
- Text: RV4-03, RV4-04 and RV4-05.
- No hand edits after the build: the builder re-run reproduces the JSON byte for byte (t14).

## 4. Checkpoint

**Claim**
- Staging rev2.1 closes RV3-01 (a)–(f), RV3-08 and RV3-09, and folds lines 175 and 181–183 faithfully.
- It is not publishable as staged, for two reasons: line 186 supersedes its L* and cold-flow statements, and it does not say its figures are valid only at ledger v3d.
- With C1–C5 applied and the post-check passing, it is publishable as gnc.json v3.1. Its evidence is simulation only.

**Configuration**

| Item | Hash |
|---|---|
| MANIFEST_rev2p1 | 02c554a2f0fe68fa |
| JSON | c2860bd89c1e5920 |
| comparators_rev2p1 | d5678ffbdbbd7a65 |
| bit29_g6_recheck | 5cd21d96c4f85e89 |
| mass_v35_vs_v3d | ee89a8c0dff34d89 |
| builder | 0e6c1c753f3deb4d |
| CHANGELOG (186 lines) | b53a35db05dc76ba |
| vehicle_v3d.json z_pivot_m | value 0.203 |

**Sources**
- Lead lines 175, 177 and 181–186.
- REVIEW-GNC-R2.md (fabfc81fa1d70327) and the reviews/gnc/rev2 logs: s03 819a79cf0db42fda, s04 40ac5dc493ea98e1, s08 abd636cdac9d11ec, s15 be3a6105746f9bce, rv_rg16_budget.json 65939777a57180ec.
- The MANIFEST_rev2 tables.
- massprops, BOM, ledger and mechanical.json (hashes above).

**Files**
- Hub reviews/gnc/rev2p1/:
  - scripts/: t01–t17, rvlib, guard_run, env.sh, repro/builder_copy.py;
  - logs/: 18 files;
  - results/: t01_hits.json, t06_comparators.json 66bcaf754089eb6c, t10_postcheck_rev2p1.json dec2cacd45e0548c.
- MANIFEST_REV-GNC-4.sha256 e3d4413e5ed10b94 covers 41 files; `sha256sum -c` passes.
- The t17 test files are rebuilt by the script and are not published.
- No staging, interface, CHANGELOG, REQUIREMENTS or supervision file was modified.

**Tests**

| Test | Result |
|---|---|
| t01 | 38-pattern scan |
| t04 | Citation check |
| t06 | 69/69 comparators, 0 differences |
| t07/t08 | Mass |
| t09 | Attribution |
| t10 v2 | Staged file: exit 1 (20/5/11) |
| t11 | G6 |
| t12 | Lead lines verbatim |
| t13 | Author rule 32/0 |
| t14 | Builder byte-identical |
| t15/t16 | Quotes and source checks |
| t17 | Mock-corrected file passes; reinserted stale phrase is caught |

All runs used nice 10 and one process at a time.

**Unknowns**
- Whether L* = 1.3 s and the release-hold alternative gain P (rev3; not reviewed).
- LO/HI (CF-4, T4).
- Cold-flow heat pick-up (CF-3).
- Canopy dynamics.
- Valve masses (ASSUMED), fasteners, the torch line, the EL-11/12 overlap with P12, and massprops v3.5.1.
- The measured IMU vibration spectrum: the RG-16 margin is 0.012 percentage points on an ASSUMED white model.
- t10 checks wording, not meaning.

**Next closure**
1. GNC applies C1–C5 as staging rev2.2. GNC does not write interfaces/gnc.json.
2. The lead runs the post-check on the candidate file:
   `/opt/engine-venv/bin/python -I reviews/gnc/rev2p1/scripts/t10_postcheck.py <candidate.json> <out.json>`
   - It must exit 0.
   - Add `--publication` for the final file.
3. The lead reads the diff against c2860bd89c1e5920 and checks it is limited to the C1–C5 keys.
4. The lead publishes v3.1 and registers REV-GNC-4 in supervision.
5. Any new computed numbers get their own independent check.

Matching hashes and a passing post-check show only that the document repeats its sources. This is a simulation/document check only, not physical approval.
