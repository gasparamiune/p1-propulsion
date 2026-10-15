# ARGOS H1 — GNC rev1: response to REV-GNC-1

| Field | Value |
|---|---|
| Version | v1, 2026-10-13 |
| Owner | GNC (01-systems-gnc) |
| Status | STAGED, not published |
| gnc.json v3 (3e97c378cfebee95) and REPORT-v3 | Unchanged |
| A1 relight | NOT CLOSED (RG-01 BLOCKING) |

**Conventions.**
- **Tags:**
  - REQ, DATASHEET, LITERATURE, SIM, DERIVED and ASSUMED, as defined in the brief.
  - PROPOSAL means a GNC proposal awaiting a lead decision.
  - DESIGN means a value adopted by a cited lead decision.
- **Statistics:**
  - P is the share of Monte Carlo flights that meet the touchdown criteria.
  - Every run uses seed 101 and 500 runs per base.
  - "Pooled" means 1000 paired runs, from two bases or two profiles.
- **"Loses":** P is below the comparator with an exact McNemar p < 0.05. Whether the case stays within 1 % is reported beside it.
- **Evidence level:**
  - Everything here is simulation or derived evidence. None of it is physical validation.
  - Passing tests, matching hashes or a working UI is not product acceptance.
  - More degrees of freedom are not presented as more accuracy.

## 1. CHECKPOINT

### Claim
- **REV-GNC-1 is answered item by item (§3):**
  - 9 items are fixed: RG-03, 05, 07, 09, 10, 16, 17, 18, 20.
  - 9 items are fixed on the GNC side, with the rest deferred to a named gate: RG-02, 04, 06, 08, 11, 12, 13, 15, 19.
  - RG-01 is open and BLOCKING, partly addressed.
  - RG-14 is deferred.
  - In RG-16 item 3, I dispute the reviewer's hypothesis with evidence.
- **Release rule.** The decided drogue-release rule is implemented in sim6 as amendments R and S, bit-checked, and flown with Combustion's fuel-starved start plateau. It is mapped onto the Electronics v2.9 telemetry.
- **Purge and bleed.**
  - The pre-scheduled purge mass is flown in the A1 reserve.
  - θ at RELIGHT stays at or below 0.76° with a balanced 1.0 mm purge.
  - A stuck-open bleed bracket at 1.0 mm is flown.
- **ENG-07.** On the re-routed coil at 6.6 V, a pressurised hose EI up to 0.25 N·m² does not lose P; EI 0.5 does.
- **RG-16.** The over-thrust monitor keeps a margin of at least 56 N to 650 N with the adopted estimator.
- **What this report does NOT claim:**
  - relight closure;
  - physical validation;
  - superiority of any proposal.

### Configuration
- **Simulator.** sim6 v2.8-dev with amendments M, W, F, P, R and S.
  - sim6.py f9094b63e64f2324, run6.py 35b5c808487b9339.
  - Every amendment is off by default and gives bit-identical results when off.
  - m2_bitcheck_v28 v1.5: ALL PASSED.
- **Interfaces.**
  - Frozen snapshot /home/claude/work/space/iface_v3c, selected with GNC_IFACE.
  - Actuator data from actuator_rate_check_v2.json, selected with GNC_ACT_RATE.
- **FSW record.** fsw_config_record_v1.json v1.4 (08c85849a5da950d):
  - 8 bases;
  - an as-flown table of 54 study arms;
  - a check() function that raises on any mismatch;
  - GNC_PC_RATCHET=1 recorded explicitly.
- **Run environment.**
  - Python /opt/engine-venv, NUMBA_NUM_THREADS=1, at most 2 processes, nice 10.
  - No package was installed.

### Sources (read-only; sha256/16)
- **Reviews and interfaces:**
  - reviews/REVIEW-GNC.md (REV-GNC-1).
  - interfaces/electronics.json v2 (da067408c1594814) and 06-electronics/REPORT-v2.9-HANDBACK.md.
  - interfaces/gnc.json v3 (3e97c378cfebee95) and the staging file gnc_v3.1_staging.json (695a069e8fc8dc53).
- **Other specialists' workdir files:**
  - Combustion drogue_hold_check_v2p4.json (70820e0038be39a7).
  - Electronics calc/make_interface_json_v2.py (a67f76f1bfc9176f).
- **CHANGELOG lines:**
  - Lead decisions: 111, 113, 126, 142, 154, 156.
  - Electronics: 112, 123.
  - Combustion: 155.
- **Relayed data:**
  - Mechanical's v3.4.1 coil stiffness matrix.
  - Electronics bleed flows (DERIVED, hbleed_provision_v1): 11.3 / 20.1 / 31.3 g/s at 0.6 / 0.8 / 1.0 mm.

### Files
**Hub: 01-systems-gnc/staging_v3.1/rev1/** (MANIFEST_rev1.sha256 2dbe49919289f0ac, 387 files)
- sim/gncsim_v2.8-dev_MWFPRS/: the simulator.
- sim/patches/: amendment diffs and the pre-amendment backups.
- scripts/: every m2_*.py as run.
- results/: 24 folders of JSON results, with the Monte Carlo CSVs gzipped.

**Key results (sha256/16):**

| File | Hash |
|---|---|
| rev1_items.json (values for v3.1) | 799258458f0142a5 |
| fsw_config_record_v1.json | 08c85849a5da950d |
| start_transient.json | d2a2ef14b5565d41 |
| purge_cost.json | c591330634246228 |
| purge_bleed_1mm/purge_bleed.json | 872a021fc9be0b93 |
| relight_attitude_ps10/relight_attitude_v1.json | 06296daef74e8d95 |
| eng07_6v6.json | 162650b8752f9ca7 |
| rg16_fct_terms.json | 3e6d85f0400f70d3 |
| rg11a_growth.json | 87aca2eaa0ea4fe3 |
| v28_checks_v15/bitcheck_v28.json | e1c6d9b6b5292718 |

**Other locations:**
- **interfaces/CHANGELOG.md:** lines 157 and 158, append only.
- **Dev tree:** /home/claude/work/space/gnc_dev28. Outputs are in /home/claude/work/space/out.

**Scripts changed this segment:**
- New: m2_purge_cost v1.0.1.
- Updated:
  - m2_fsw_record v1.4;
  - m2_rev1_items v1.2;
  - m2_stage_hub_rev1 v1.4;
  - m2_relight_attitude v1.1 (one arm added, in its own output folder);
  - m2_purge_bleed v1.2 (1.0 mm arms and arm selection);
  - m2_start_transient (evaluation re-run only).
- Backups are kept in /home/claude/work/space.

**Cleanup:**
- Deleted my scratch folders dp/, ff_mini/ and pb_smoke/, and the scripts wait_bit15.sh and wait_st.sh.
- Deleted two stale partial-staging sub-manifests in the hub: results/fsw_record/MANIFEST.sha256 and results/release_rule/MANIFEST.sha256.

### Tests and verification
- **bitcheck v1.5 ALL PASSED:**
  - A: 0 mismatches. A1_none 12 runs / 1104 values; A1J_pc 18 / 1656; rbl_B1 10 / 920.
  - C: 4000 points, maximum difference 0.
  - D and E pass. F passes with a maximum difference of 0.0014 N.
  - P1–P5 pass.
  - R1–R4 pass; rel_F = 37.159 N.
  - S1: A1_none and A1J_pc each 500 runs / 74 000 values, 0 mismatches, 0 persistence releases.
  - S2: release at 0.100 s on the persistence branch.
  - S3: release at 0.008 s on the Pc branch.
  - S4: branch lost.
  - S5: st_F 27.31 N, rel_Frise 22.92 N.
  - S6: B1 20 runs, 0 mismatches.
- **Identity checks:**
  - The re-flown purge_bleed references are byte-identical to the stored ones (A1_ref 097bd0700a611050, B1_ref b9132370755212ba).
  - The relight-attitude 1 ms recorder matches over 3 runs.
  - The ENG-07 control arm has 0 mismatches.
  - The rg11a identity holds.
  - Re-evaluating the start transient with the Combustion file gave identical P lines.
- **FSW record:** every v1.3 fsw_sha16 and par_sha16 is unchanged in v1.4.
- **Staging and CHANGELOG:**
  - Staging: 10 s read-back and an independent re-hash, 0 mismatches.
  - CHANGELOG: read back 10 s after each append.
- **Not run:**
  - npm test and npm run build (GNC changed no app code);
  - SIL/HIL;
  - hardware.

### Unknowns (data missing, not invented)

| Unknown | What it affects | Who closes it |
|---|---|---|
| Pressurised hose EI, and other lines across the gimbal (Mechanical bleed line adds 0.5–2 N·m/rad) | ENG-07 limit lies in (0.25, 0.5] N·m² | B-FD-1 |
| Canopy pendulum motion and riser elasticity (the drogue is modelled as quasi-steady and massless) | θ at RELIGHT; release transient | Canopy data via the ICD to Lauty |
| Retained vapour after the re-route; CF-4 void; P_abort and start delay with the purge | RG-01 | Combustion, Mechanical |
| π_s (line-state probabilities); p_nl,ign (no-light probability) | RG-02 P_total | Mechanical soak-back; torch qualification |
| Plateau oxidiser flow; combustion roughness (0.48 bar tolerance, unmeasured) | Release branch; unbooked mass ≤ 14.7 g | IGN-1, T1 |
| Pc offset; baseline P0 (ISA 1.013 + torch 0.3 bar, ASSUMED) | Rise threshold rel_Frise | B-PC-1 |
| Stuck-open bleed physics (additive or subtractive; phase at the bleed); final orifice | A1 0.896–0.974; B1 0.368–0.990 at 1.0 mm | Combustion, the Electronics plant, B-BLEED-1 |
| Probability of a stuck-open bleed (double or common-cause fault) | Risk = probability × consequence | FMEA (Electronics, Mechanical) |
| Unusable liquid residual (3 %, ASSUMED) | A1 minimum usable reserve 55–65 g | Tank outflow test |
| k, u_k, the regression law (a, n), throat growth g, and the growth law beyond J_ref | Cap; A1 reserve | T1–T4 |
| IMU group delay, FC/ECU scheduling, CAN, axial modes | RG-19 latency budget | FC owner, HIL |
| Pad slope | Tip-over margin | ICD-AIRFRAME |
| HV69 servo speed under load | ENG-07 | B-TVC-1 |
| Weighing scale at ARM | RG-16 budget | Founders (TO-DEFINE) |
| ACEMA turbulence statistics | Launch commit | Site data |
| Behaviour if Pc goes invalid between E2 and release | Drogue held while lit | Lead, Electronics, GNC fault arm |
| Live hub combustion.json no longer has igniter.sequence | Reproducibility against the live hub | v3.1 build (re-pin inputs) |

### Next closure (ordered)
1. **RG-01 re-fly**, once Combustion publishes the tables for the re-routed coil with the pre-scheduled purge at θ ≤ 2° and CF-4 is decided.
   - Fly with the decided release rule, the plateau bracket, the purge mass at the chosen orifice in the A1 reserve and a balanced vent.
   - Report per line state, paired against the liquid plan.
2. **Lead decision on the bleed orifice.** GNC recommends 0.8 mm or less (§2.3).
3. **sim6 amendments,** each with its own API, hypotheses, tests and review:
   - a. a purge-trigger gate with a duration cap;
   - b. freezing k_est_asc and the apex predictor on Pc invalid, then re-flying the Pc-lost fault arms;
   - c. a fault arm for Pc going invalid between E2 and release;
   - d. research only: an in-flight response to the bleed leak flag.
4. **B-FD-1:** pressurised EI ≤ 0.25 N·m², preferably K_max ≤ 17.2 N·m/rad at 7.4 V.
5. **Lead decisions, then gnc.json v3.1:**
   - Decisions needed on: launch commit, cap rule, purge gate, UNKNOWN → 1.41 s, the FC release predicate, and the Pc-invalid case.
   - Then fold rev1_items into gnc.json v3.1 and refresh inputs_read (RG-12).
6. **Electronics:**
   - fix the planning-key lookup (OI-GNC-V3);
   - implement the filtered-only hold;
   - confirm that UNKNOWN forces the prep path.
7. **SIL/HIL:**
   - trace match against the FSW record (HIL-TR-1);
   - end-to-end latency budget (RG-19).
8. **Independent review.** A reviewer other than GNC records the rev1 set in supervision.json.

## 2. RESULTS BY TOPIC

### 2.1 Relight attitude θ (SIM)
θ is the angle between the body +z axis and the specific force at the hose station (z_pivot + 0.073 m, ASSUMED).
- **Setup:** flown-estimator FSW, 500 runs, 1 ms recording.

| Case | θ at RELIGHT, p50/p95/p99/max (°) | Notes |
|---|---|---|
| No purge | 0.11/0.45/0.63/0.75 | 0 runs above 1°. Per-run maximum over the last 5 s: 0.30/0.78/0.96/1.30 |
| Lateral vent (2.1 N, ASSUMED) | 1.18/1.46/1.63/1.85 | Per-run maximum over the last 5 s up to 2.57 |
| Balanced vent, 0.8 mm | 0.12/0.43/0.63/0.72 | — |
| Balanced vent, 1.0 mm (new arm PS10_nojet) | 0.12/0.42/0.61/0.76 | 0 of 500 runs above 1°. During the purge: pooled p99 0.54, max 1.28 |

- With a balanced or axial vent, the lead's θ ≤ 2° is met in the model.
- A lateral vent leaves only 0.15° of margin at its maximum.
- The governing limit is the drogue model: a real canopy's pendulum swing adds directly to θ.
- The sim6 output prg_tilt_* is the body tilt from vertical (p99 about 5° under the drogue). It is NOT θ.

### 2.2 Release rule and start transient
**Rule and model**
- **The rule (DESIGN, line 142).** Release at E2 AND [Pc ≥ 3.0 bar abs OR the 0.8 bar rise held continuously to E2 + 0.10 s].
- **sim6 parameters (amendments R and S):**
  - rel_F = 37.16 N, the map thrust at 3.0 bar abs.
  - rel_Frise = 22.92 N, the map thrust at 2.113 bar abs: ISA 1.013 + torch 0.3 (ASSUMED) + 0.8 bar.
  - rel_to = 0.10 s.

**Release bracket** (release held after the light; pooled):

| Hold | Lost / gained | p |
|---|---|---|
| 0 ms | −1/+2 | — |
| 100 ms | −4/+4 | — |
| 200 ms | −11/+5 | 0.21 |
| 400 ms | −21/+6 | 0.0059 (2 A1J crashes) |

**Plateau arms against the decided rule without a plateau** (reference P: A1_none 0.990, A1J_pc 0.984, pooled 0.987):

| Arm | Plateau | A1_none | A1J_pc | Pooled | p |
|---|---|---|---|---|---|
| L100 | 2.4 bar × 0.1 s | 0.992 | 0.984 | −2/+3 | 1 |
| L400 | 2.4 bar × 0.4 s | 0.986 | 0.978 | −7/+2 | 0.18 |
| L400_nto (branch off) | 2.4 bar × 0.4 s | 0.982 | 0.978 | −13/+6 | 0.167 |
| M400 | 2.9 bar × 0.4 s | 0.990 | 0.978 | −7/+4 | 0.549 |
| H400 | 3.6 bar × 0.4 s | 0.992 | 0.974 | −7/+3 | 0.344 |
| L400_te (planner + 0.3 s) | 2.4 bar × 0.4 s | 0.972 | 0.968 | −23/+6 | 0.0023, LOSES |

- **Release times:**
  - L400_nto releases at 404–405 ms.
  - H400 releases at 7–13 ms.
- **Persistence branch on versus off** (L400 against L400_nto): −10/+12, p 0.832. The branch does not change P; its value is that it bounds how long the drogue is held.
- **Vertical speed at the end of the plateau** (p01): −26.8 m/s for L400, −24.2 m/s for L400_nto.
- **Liquid left versus the decided rule** (p50, A1_none): L100 +5.8 g, L400 +10.7 g, L400_nto +25.4 g, M400 +9.7 g, H400 +4.4 g, L400_te −15.2 g.
- **Unbooked oxidiser during the plateau:** at most 3.7 g (0.1 s) and 14.7 g (0.4 s). This uses Combustion's A1 relight oxidiser flow of 31.6–36.7 g/s.
- **Combustion's drogue-hold check (line 155):**
  - The rise holds on all 288 lit corners.
  - The minimum margin is 0.74 bar (0.48 bar if the torch only raises the baseline).
  - No unlit case reaches 0.8 bar.
  - The worst corner sits at 2.60–2.62 bar abs, between the flown arms L and M, and neither of them loses.
  - Conclusion: the relight planner must NOT add the plateau.

**FC implementation (DESIGN mapping onto Electronics v2.9)**
- **Frame and predicate:**
  - TLM_FAST 0x100 at 500 Hz. The state is d1 & 0x0F.
  - While the drogue is attached, on each new frame, release when b4 AND [(d2-d3 ≠ 0xFFFF AND d2-d3 ≥ 300 kPa abs) OR b7].
  - b4 is set at RUN entry; the E2 time comes from EVENT 0x120.
  - The release is one latched command.
- **SIL evidence (Electronics):**
  - b7 held in 273 of 273 lit runs.
  - E2 → Pc 3.0 bar: p95 34 ms, max 43 ms.
  - E2 occurs 16–18 ms after the light.
- **sim6 differences:**
  - sim6 places E2 at the light, so it releases 16–18 ms earlier than the firmware. This is well inside the +100 ms band that does not change P.
  - Firmware v2.9 evaluates the hold on the filtered AND the raw channel. The lead has decided on the filtered channel only (line 156), not yet implemented.
  - A hold cleared by noise falls back on the Pc branch. That outcome is bounded by arm L400_nto.

### 2.3 Purge, A1 reserve and stuck-open bleed
**Forced purge** (m2_purge_bleed v1.1; flown-estimator FSW; v2.8 release model; 0.8 mm, 20.0 g/s of liquid)

| Arm | P | Lost / gained | Notes |
|---|---|---|---|
| P25 | 0.988 | −2/+1 | 2.60–3.41 s; 52–68 g; starts at 92–139 m |
| P25_nojet | 0.990 | −1/+1 | — |
| P20_06 | 0.992 | −1/+2 | — |
| P25_nobook | 0.988 | — | — |
| P25_wait | 0.988 | — | — |
| P25_lead0 | 0.988 | — | 163 truncated purges |
| P25_early40 | 0.986 | −4/+2 | — |
| P25_late50 (closure confirmation +50 ms) | 0.990 | −2/+2 | — |
| P30 | 0.988 | −4/+3 | 6 of 500 purge starts are spurious, at 10.15–10.54 s and 301–304 m (drogue deployment); up to 13.9 s and 278 g |

- The P30 behaviour leads to the purge-gate PROPOSAL in rev1_items: evaluate the trigger only once the drogue descent is quasi-steady, and cap the purge duration.

**Pre-scheduled purge in the A1 reserve** (m2_purge_cost; stored v2.8 FSW; decided rule; balanced vent)
- The modelled purge lasts 2.58–3.43 s, longer than the ECU's 2.5 s, so these results are upper bounds.

| Arm | Flow | Purge mass p50/max | A1_none | A1J_pc | Pooled | Exhausted |
|---|---|---|---|---|---|---|
| PS10 | 31.3 g/s | 94.5/107.4 g | 0.990 (−2/+2) | 0.978 (−5/+2) | −7/+4, p 0.549 | 2 + 2 (runs 14 and 108; decided rule 0) |
| PS08 | 20.1 g/s | 60.5/68.9 g | — | — | −4/+2, p 0.688 | 1 + 0 |
| PS10_L400 (with plateau) | 31.3 g/s | — | — | — | −11/+3, p 0.057 (within 1 %) | — |

- PS10: liquid left p01 is 100 g (A1_none) and 92 g (A1J_pc).
- Under the decided rule, the minimum liquid left is 114.1 g (A1_none) and 123.7 g (A1J_pc). This includes the unusable 3 % (ASSUMED), so the worst usable reserve is 55–65 g.
- A 76 g purge therefore exhausts the two lowest-reserve draws; a 50 g purge leaves at least 5 g.

**Stuck-open bleed** (both series valves open; the FSW is not aware of it)
- **At 19.4 g/s or less (v1.1):**

  | Arm | P | Lost / gained | p | Exhausted |
  |---|---|---|---|---|
  | A1 S194_0 | 0.968 | −13/+2 | 0.0074 | 11 |
  | A1 S194_1 (subtractive) | 0.972 | — | 0.0225 | — |
  | A1 S194_0_nojet | 0.970 | — | — | — |
  | A1 S1285_0 | 0.986 | — | — | — |
  | A1 S063_0 | 0.986 | — | — | — |
  | B1 B194_0 | 0.922 | −36/+3 | — | 31 |
  | B1 B194_0_nojet | 0.930 | — | — | — |
  | B1 B1285_0 | 0.982 | — | — | — |
  | B1 B063_0 | 0.992 | — | — | — |
  | B1 B194_1 | 0.994 | — | — | — |

- **At 31.3 g/s, 1.0 mm, balanced vent (v1.2):**

  | Arm | Mode | P | Lost / gained | p | Exhausted | Notes |
  |---|---|---|---|---|---|---|
  | A1 S313_0 | Additive | 0.896 | −49/+2 | 1.2e-12 | 48 | — |
  | A1 S313_1 | Subtractive | 0.974 | −10/+2 | 0.039 | — | — |
  | B1 B313_0 | Additive | 0.368 | −312/+2 | — | 315 | m_est error at end of burn +2.9 to +4.9 % |
  | B1 B313_1 | Subtractive | 0.990 | −3/+4 | — | — | — |

- **Which case applies.** The Electronics SIL shows the injector flow dropping only 1 g/s while the bleed carries 11–31 g/s, which points to the additive case. That plant is ASSUMED.
- **Detection.** Only the P_mid leak monitor sees the fault, at +0.21 s.
- **Conclusion (GNC):** use a bleed orifice of 0.8 mm or less. At 1.0 mm, both the purge cost and the double-fault consequence grow.
- **PROPOSAL (research, not flown): FSW response to the leak flag.**
  - Hypothesis: if the FSW books the leak at the orifice flow from the moment the flag rises and switches to an early landing, part of the additive-case loss is recovered.
  - Comparator: S313_0, B313_0 and B194_0 on the same draws, with no response.
  - Refutation: no significant gain, or a new loss in the no-fault arms caused by false flags.
- **Purge booking.** The RG-16 booking residual bound of 29.1 g holds for 0.8 mm. At 1.0 mm it scales to about 45 g (DERIVED ratio, not recomputed).

### 2.4 ENG-07 (6.6 V degraded plug)
- **Setup:**
  - Pooled A1_none + rbl_B1, 1000 runs; baseline P 0.994.
  - R = the command-slew rule; P = the physical actuator (act_model 1).
- **Origin of the earlier 0.982:**
  - It comes from arm AD_prov_act_n48_6V6 (sim6 v2.5): act_model 1 at 6.60 V, n 4.8, 100 °/s, hose_K U(0.20, 1.97).
  - The 95.3 °/s value was never flown.

**v3.4 coil** (the °/s values in brackets are the commanded slew rates)

| Arm | EI 0 | EI 0.05 | EI 0.25 | EI 0.5 |
|---|---|---|---|---|
| R66 | −0/+1 | −0/+2 (95.94 °/s) | −2/+1 (85.48 °/s) | −9/+1, p 0.0215, LOSES (72.39 °/s) |
| R74 | — | — | −1/+0 | −5/+1, p 0.219 |
| Rv66 | — | −4/+1 | −8/+2, p 0.109 | — |
| P66 | −0/+1 | −0/+1 | −1/+0 | −5/+1, p 0.219 |
| P74 | — | — | — | −5/+1 |

**Re-routed coil v3.4.1**
- The stiffness matrix is K = [[64.459, 32.728], [32.728, 56.563]] × EI. Its eigenvalues are 93.476 × EI and 27.546 × EI.

| Arm | EI 0.05 | EI 0.184 (K 17.2) | EI 0.25 (K 23.37) | EI 0.5 (K 46.74) |
|---|---|---|---|---|
| RR66 | −0/+0 | −4/+0, p 0.125 | −7/+1, p 0.070 | −135/+1, LOSES (A1 0.738) |
| RR74 | — | −4/+1 | −5/+1 | −10/+1, p 0.0117, LOSES |
| RRv66 | — | −7/+1, p 0.070 | — | — |
| PR66 | — | −3/+1 | −4/+1 | −9/+1, p 0.0215, LOSES |
| PR74 | — | — | — | −9/+1, LOSES |

- **Limit.** The EI limit lies in (0.25, 0.5] N·m². EI ≤ 0.25 is equivalent to K_max ≤ 23.4 N·m/rad, counting all lines across the gimbal.
- **7.4 V.** Raising the supply to 7.4 V does not recover EI 0.5.
- **Lead criterion.** The lead's K_max ≤ 17.2 N·m/rad at 7.4 V is supported and preferred, because the EI 0.25 point sits near the decision threshold (p 0.070).
- **ENG-07b.** p99 ≤ 66 ms in every act_model 1 arm.
- **Mechanical gates** (K_EI0.25, MBR_dynamic_100, plan_ok) are all False as relayed. B-FD-1 is needed.

### 2.5 RG-16 mass budget and the FC_THRUST margin
- **Mass budget:**
  - A1: 1.408 % at end of burn, 1.344 % in the FC window.
  - B1: 1.88 % and 2.21 %.
- **Mass offsets flown:**
  - purge booking −29.1 g;
  - unbooked purge +68.2 g;
  - stuck bleed A1 +101.8 g, B1 +361.2 g.
- **Held maximum** (threshold 650 N; nominal 571.5 N):

| Case | Held max (N) | Margin to 650 N (N) | Missed 670 N cases |
|---|---|---|---|
| A1 H_cal_pbk | 575.7 | 74.3 | 0 |
| A1 Llo_re_pbk | 449.5 | — | 0 |
| A1 Llo_cmd_pbk | 448.8 | — | 1 of 1000 (run 137) |
| A1 H_cal_pnb | 579.0 | — | 0 |
| A1 Lhi_re_pnb | 591.7 | — | 0 |
| A1 Lhi_cmd_pnb | 593.9 | 56.1 | 0 |
| A1 H_cal_blf | 580.1 | — | 0 |
| B1 H_cal_blf | 583.7 | — | 1 of 1000 (run 119; onset 8.79 s; b −11.32 %) |
| B1 H_cal_comp_blf | 584.3 | — | 0 |

- There were 0 alarms before fault onset in every case.
- **A1 offset between k_hat and F_acc:**
  - The total is −1.36 %: lever arm −0.85, thrust direction −0.20, aero −0.18, bias −0.004 percentage points.
  - The first and second halves of the landing burn show −1.67 % and −1.27 %.
  - After compensation, −0.18 % remains.
  - B1: −0.05 %.

### 2.6 Cap rule (RG-04, RG-11b): PROPOSAL
- **Rule inputs:**
  - k = delivered thrust per propellant flow, with uncertainty u_k;
  - the 2σ region of the regression law (a, n);
  - throat growth g, with uncertainty u_g.
- **Grid.** 0.25 m steps, fine enough to resolve the 10 ms MECO steps.
- **B1 corner cap** at k = 1.00 / 0.97 / 0.95 / 0.90:
  - this study: 62.5 / 60.0 / 57.5 / 51.5 m;
  - v2.7: 62.75 / 59.5 / 56.25 / 51.0 m;
  - the reviewer's rg11: 62.92 / 59.65 / 56.43 / 50.79 m.
- **Lowest k at which the cap still reaches 62 m:**
  - B1 corner: only at k ≥ 1.00;
  - B1 centre: down to 0.87;
  - A1: down to 0.92.
- **Conditional MC:**
  - B1 corner, k 1.00, 62 m: 0.992.
  - B1 corner, k 0.97, 62 m: 0.990 (2 exhausted).
  - B1 corner, k 0.97, at its own cap: 0.996.
  - A1 at k 1.00 / 0.97 / 0.95 / 0.90: 0.986 / 0.988 / 0.996 / 0.980 (5 exhausted at 0.90).
- **The reviewer's ×0.90 case.** The reviewer applied ×0.90 on top of the per-run draw of k, which explains their 0.950. Holding k fixed at 0.90 gives 0.980.

### 2.7 Growth beyond J_ref (RG-11a)
- **Emulation:** a J-proportional growth law, emulated by doubling J_ref and g in the truth model, with the FSW unchanged.
- **Caps:** unchanged.
- **Band MC:**
  - P 0.994 → 0.994;
  - exhausted 0 → 0;
  - J > J_ref in 28.8 % of runs (maximum 1.192);
  - maximum growth 10.97 → 12.15 %.
- **Corner:**
  - P 0.992 → 0.992;
  - exhausted 1 → 1;
  - maximum growth 12.56 %.
- **Identity:** holds.

### 2.8 Fuel web and burn limit (RG-03, RG-10)
- **Model:** sim6 amendment W adds a web state, a burn limit at t(web = 1 mm) using 1.1 × a, and a Pc-based apex predictor.
- **Results:**
  - Arm W1p: 0.994 (−2/+1).
  - Without the limit action, 19 runs reach a web below 1 mm near touchdown.
  - A gate of a_meas ≥ 1.25 leaves 0 of 364 runs below 1 mm.
  - W2p: 0.930 (−34/+1).
  - Apex height: p99 rises from 66.10 to 68.99 m; maximum 69.96 m.
- **Safety area:** should be sized on about 70 m.
- **Published:** band records selected by fuel burned, by O/F and by the longest burns.

### 2.9 Launch commit (RG-06): PROPOSAL
- **Criterion:** mean wind W10 < 6 m/s AND turbulence σu at 3 m ≤ 1.0 m/s.
- **Measurement:**
  - both averaged over the 10 minutes before ARM;
  - anemometer at 3 m;
  - W10 obtained with a power law (α 0.14) or from a 10 m mast.
- **At the limit:**
  - B1: 1.000 [0.992, 1.000];
  - A1: 1.000.
- **Over the full map:**
  - B1: 0.993;
  - A1: 0.985.
- **Assumption:** treating the 10-minute σ as the model's Dryden turbulence intensity is a model-form ASSUMPTION.
- **Site data:** TO-DEFINE.

### 2.10 Fault flights (RG-18)
- **Faults flown:**
  - thrust stuck at 670 N and at 876 N;
  - from ascent and from landing;
  - with Pc valid and with Pc lost;
  - with every detector active.
- **Results:**
  - Faults missed: 0. False decisions: 0.
  - A1: 0 of 800 (Wilson upper bound 0.48 %).
  - B1: 0 of 1192 (0.32 %).
  - Decision time p99: 45–301 ms.
- **Consequence of a forced miss:**
  - A1 apex 445–553 m;
  - B1 apex 183–435 m;
  - touchdown at −26 to −64 m/s.
- **Mitigations:**
  - The geofence proposal catches every B1 miss.
  - Valid window: "no drogue load", with a tether rule for flight C.

### 2.11 B1 62 m on the ENG-07d actuator basis (RG-07)
- 6.6 V: 0.992 (−3/+1, p 0.625).
- 7.4 V: 0.992.
- With the burn limit: 0.998.

### 2.12 No-light accounting (RG-02)
- **Formula:** P_total = Σ π_s · P_6DOF|s,lit · (1 − p_abort,s) · (1 − p_nl).
  - The sum runs over line states s.
  - Results are reported per state, with no weighted mean.
- **44 cm³ segment** (liquid / vapLO / vapHI / vap44F):

| Plan | Liquid | vapLO | vapHI | vap44F |
|---|---|---|---|---|
| v3 plan, W 0.65 | 0.990 | 0.016 | 0 | 0 |
| plan 0.91 / W 0.85 | 0.989 | 0.807 | 0.586 | 0.445 |
| (b) plan 1.21 / W 1.05 | 0.953 | 0.994 | 0.992 | 0.995 |
| (a-0) prep path, W 0.88 / plan 1.60 | 0.975 | 0.991 | 0.990 | 0.990 |

- The reviewer's R7 value is reproduced on the superseded 21.4 cm³ rows.
- These rows predate the coil re-route and will be redone in the RG-01 re-fly.

### 2.13 FSW record (RG-13)
v1.4 contains:
- 8 bases, including the stored v2.8 bases;
- an as-flown table of 54 entries;
- the release rule mapped onto TLM_FAST;
- relight-planning key paths checked directly in the files.

**CORRECTION.** v1.3 named the decided-rule base, which uses the flown mass estimator, as the start-transient comparator. That was wrong.
- The release-rule, start-transient and purge-cost arms fly the stored v2.8 FSW.
- Their comparators use that same FSW.
- So no P value changes.

m2_purge_bleed flew without fct_comp, while the purge2.5 base records fct_comp 1.

### 2.14 Simulator amendments and bit-check
- **Amendments:**
  - M: flown mass estimator.
  - W: web state, burn-limit action, Pc-based apex predictor.
  - F: stuck-throttle fault, in-loop detectors, abort, geofence.
  - P: forced purge, stuck-open bleed, bleed jet.
  - R: release rule (E2 AND Pc ≥ 3.0 bar).
  - S: start plateau and persistence branch.
- **Status:** all amendments are off by default. Bit-check v1.5 ALL PASSED (§1).

## 3. REVISION-RESPONSE (RG-01 to RG-20)

**RG-01 (BLOCKING): OPEN, partly fixed; deferred to the RG-01 re-fly**
- **Required actions 1–3:** done on the 44 cm³ rows (CHANGELOG line 118 and rg02):
  - On the v3 plan, vapour states abort 98–100 % of the time.
  - The zero-abort and early-light comparators are published.
- **Item 4:** done.
  - The ECU cannot detect vapour (line 112 (1)).
  - The flag is not used to exclude vapour (line 113 (1)).
- **Item 5:** 0.81 s and 1.41 s are not frozen (line 111 (2)).
- **Lead fix:** coil re-route (line 126), trap 13.53 cm³ against the zero-abort limit of 18.86 cm³.
- **New in rev1:**
  - θ at RELIGHT;
  - the decided rule flown with the plateau;
  - the purge mass in the A1 reserve;
  - the stuck-open bracket.
- **Still missing:**
  - Combustion's tables for the re-routed coil with the purge at θ ≤ 2°;
  - CF-4;
  - canopy data;
  - B-FD-1;
  - the GNC re-fly.

**RG-02: FIXED**
- The accounting is done per line state on the v2.8 and 44 cm³ rows.
- R7 is reproduced.
- The demonstration rule is stated.
- **Deferred inputs:**
  - π_s (Mechanical soak-back);
  - p_nl (torch qualification).

**RG-03: FIXED**
1. The lead withdrew "covers" for fuel, web and O/F (line 111 (4)).
2. Records by fuel burned, by O/F and by the longest high-a burns are published.
3. The burn limit is implemented in sim6 and the FSW, with its action, and flown (W1p 0.994).
4. Item 4 is handled under RG-04.

**RG-04: FIXED as a rule; values deferred to T1–T4**
- The cap rule is written in measured quantities, with the corner and a conditional MC (§2.6).
- **Clarification:** the reviewer's A1 ×0.90 multiplies the per-run draw. With k fixed at 0.90, P is 0.980.

**RG-05: FIXED by the lead (line 111 (1))**
- ENG-03 requires at least 5 F_max/s, i.e. 2500 N/s, under load, as flown.
- GNC rate-map evidence (line 120): all −0.07 %, p 0.875.

**RG-06: FIXED as a PROPOSAL (§2.9); deferred to ACEMA site data**

**RG-07: FIXED (§2.11)**

**RG-08: PARTLY FIXED**
- **Rationale restated.** The flag hold lasts at most 19.8 s, against a drain time of 6.1–7.4 min: a factor of at least 18.
- **Electronics flag (TLM_RELIGHT at 50 Hz):**
  - UNKNOWN on an encoder fault or P_feed invalid.
  - UNPRIMED when the lift exceeds 0.10 mm for 20 ms.
  - Both force the prep path (line 112 (3)).
- **FC mapping:** recorded.
- **Deferred:** simulating the flag in the loop, including a late flip (sim6 amendment, SIL).

**RG-09: FIXED by the lead**
- Thermal governance is set per quantity (line 111 (3)).
- The A1 early-light cycles are available for the peak checks.

**RG-10: FIXED**
- The Pc-based apex predictor is flown: apex p99 68.99 m, maximum 69.96 m.
- The safety area is apex-based (line 111 (3)).

**RG-11:**
- (a) Quantified and P-neutral (§2.7). The law is stated as frozen above J_ref, with this sensitivity.
- (b) FIXED: the cap search uses the 0.25 m grid.
- (c) Handled under RG-16.
- (d) No action: CA ±30 % gives p ≥ 0.45.
- (e) Model limits are documented. Canopy data will come via the ICD.

**RG-12: PARTLY FIXED**
- **Lead:** REQUIREMENTS aligned (line 111 (3)): ENG-04 deviation recorded, ENG-07 OPEN at the v2 load, B-TVC-1 text corrected.
- **GNC:** the ENG-07 EI limit is now bracketed (§2.4).
- **Deferred:**
  - inputs_read, to the v3.1 build;
  - the RC-03 and RC-07 copies in the hub, to Combustion.
- **Note:** the live hub combustion.json has drifted, so GNC runs are pinned to iface_v3c.

**RG-13: FIXED on the GNC side**
- Versioned, hashed FSW record v1.4 with an as-flown table and check().
- The ratchet setting is recorded explicitly.
- One error was found in v1.3 and corrected (§2.13).
- **Deferred:** the firmware-to-sim trace match (HIL-TR-1).

**RG-14: DEFERRED**
- The pad-slope specification will be defined in ICD-AIRFRAME (line 111 (9)).

**RG-15: rule FIXED, simulator deferred**
- **Rule (line 113 (2)):**
  - FC_THRUST never freezes.
  - k_est_asc and the apex predictor freeze when Pc reads 0xFFFF.
- **Gap:** sim6 still updates k_est from F/tsc without checking Pc validity.
- **Deferred:** the sim6 amendment and the re-fly of the Pc-lost arms.
- The other confirmations are acknowledged.

**RG-16: FIXED**
- The requirement is now a total burn budget (§2.5).
- The estimator is flown with errors in the flow.
- The 650 N threshold is re-checked on both sides: held maximum ≤ 593.9 N.
- The A1 offset is explained by the lever arm, thrust direction and aero terms.
- **DISPUTED: the reviewer's comparison-window hypothesis.** The offset appears in both halves of the landing burn (−1.67 % and −1.27 %), so a window difference does not explain it.

**RG-17: FIXED**
- Bounds corrected: 0 of 500 error sets gives 0.60 %; 0 of 200 gives 1.49 %.
- Results are reported per profile.
- The tail criterion is replaced by a margin on the budgeted error.

**RG-18: FIXED (§2.10)**
- The valid window is defined (line 111 (6)).

**RG-19: PARTLY FIXED**
- Electronics' known-term budget: 78.6 ms mean, 84.1 ms maximum (line 123).
- GNC decision time: p99 45–301 ms.
- **Deferred to HIL and T1–T4:**
  - IMU group delay;
  - FC scheduling;
  - axial modes.

**RG-20: FIXED**
- The builder defect is fixed.
- The v3 rebuild was checked: 7 differences, none numeric.

## 4. COORDINATOR AND LEAD ITEMS ACKNOWLEDGED

**a. Vapour fix**
- The coil re-route is the baseline: trap 13.53 cm³, zero-abort limit 18.86 cm³; widening W is rejected.
- Re-route criterion: K_max ≤ 17.2 N·m/rad at 7.4 V, wall ≥ 3 mm.
- The GNC evidence supports the stiffness criterion. The wall is for Mechanical.

**b. Forced purge and stuck bleed**
- **Provision:** two NC valves in series. The purge runs at least 2–3 s and ends at the lift, and the bleed is confirmed closed before E1.
- **Decisions:**
  - CF-4 decides.
  - The lead has now made it pre-scheduled.
- **GNC work done:**
  - all purge arms;
  - the trigger-gate proposal;
  - the purge mass in the reserve;
  - the stuck-open bracket at 0.6–1.0 mm.

**c. ENG-07 provenance and EI limit:** answered in §2.4.

**d. Drogue release and E2 rule**
- **Light detection (relative):**
  - rise ≥ 0.8 bar over [E1 − 20 ms, E1], held for 10 ms;
  - floor 1.8 bar;
  - used in rel_Frise.
- **E2 timing:** 16–18 ms after the light. The lead accepted it (line 154 (4)).

**e. Relight attitude**
- Answered in §2.1.
- The drain pose was dropped, so no work was done on it.

**f. Lead decisions on the vent and canopy**
- **θ ≤ 2°:** met in the model with a balanced or axial vent.
- **Lateral vent:** not recommended.
- **Canopy data:** to come via the ICD to Lauty.

**g. Decided release rule (line 142)**
- Implemented, bit-checked, flown and mapped to the telemetry.
- The filtered-only hold (line 156) is recorded.

**h. Electronics hand-back**
1. b4/b7 predicate and the d1 mask: done.
2. Planning keys: present in gnc.json v3. The finding is disputed with file evidence. v3.1 keeps the same paths.
3. Purge mass in the A1 reserve: flown now. It also goes into the RG-01 re-fly.
4. E2 timing: no action.

**i. Lead decisions on the hand-back (line 154)**
- **Pre-scheduled purge:** the 0.81 s plan holds and its cost is flown.
- **OI-A5-LATE:** no GNC action. Lights up to the deadline are inside the plan.
- **Bleed coil:** a 12 V coil is preferred. Not a GNC item.
- **E2 latency and A3 margin:** both accepted.
- **d1 mask:** applied.

**j. Earlier lead decisions** (ENG-03 map, HV69 servo, B1 wind under 6 m/s, burn limit with 1.1 × a, "85 m covers 62 m" withdrawn): all consistent with rev1.

**k. Contact.** No SendMessage was needed this segment, and no hearthbot tool was used.
