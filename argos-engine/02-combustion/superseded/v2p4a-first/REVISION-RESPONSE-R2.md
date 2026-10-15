# Revision response R2: Combustion v2.4a to REV-COMB-2

2026-10-13. Author: Combustion and Propulsion (v2.4a; the v2.4 author handed the section over). Review: `reviews/REVIEW-COMBUSTION-R2.md` (`e6bf189fb271e652`), verdict REVISE (targeted). Lead decisions folded in to CHANGELOG line 177; Mechanical status quoted to line 179.

Files answered (hub `02-combustion/` unless stated; sha256/16):
- `REPORT.md` v2.4a (`97815f01af417804`);
- `interfaces/combustion.json` v2.4a (`7d1cef9b912eef4d`);
- `CF-4-SPEC.md` v2.0 (`a94211a295fe0224`);
- `T1-T4-REGRESSION-SPEC.md` v2 (`bbf0ea642453dc7a`).

The v2.4 files are archived under `superseded/v2p4/`. The v2.4 interface is kept as `data/v2/combustion_interface_v2p4_as_published.json` (`469727032124329f`).

Status words:
- **Closed in text:** the requested change is made, and its evidence is cited.
- **Open:** a stated part stays open, with an owner.

Nothing here is a physical result or an approval. A reviewer other than the author records the verdict. Evidence tags are those of the report: SIM, DERIVED, ASSUMED, DATASHEET, LITERATURE, DESIGN, LEAD, TO-VERIFY, MISSING.

## Summary

| Item | Status | Where (REPORT v2.4a unless stated) |
|---|---|---|
| R2-01 (MAJOR) line 166 (3)/(4) not implemented | Closed in text | §0 items 1 and 12; §2.8 items 9, 15 and the Closure row; §7.3 E1 row, bleed bullet and PURGE text; §7.4 A4 and A14; §7.6 line-160 record with an amendment note; H11; §9.1 detection; OI-18; JSON `igniter.sequence`, `abort_matrix_v2p4` (A4, A14), `cf4_gate` P6 |
| R2-02 (MAJOR) two stand safing rules | Closed in text | §7.6, H9, §10.2; JSON `abort_if_no_ignition[1]` and `stand_safing_v2p4a` |
| R2-03 (MAJOR) FA-1 single point | Closed on paper; physical evidence open | §7.6 envelope (Tables 7.6a and 7.6b), §9.1 FA-1, H14, OI-17; `fa1_envelope_v2p4a.json`; load set by LEAD line 173 and checked by Mechanical (line 176) |
| R2-04 (MAJOR) T1-T4 law decision | Closed in the specification | `T1-T4-REGRESSION-SPEC.md` v2; §10.4; JSON `t1t4_law_v2` |
| R2-05 (MINOR) stale interface values; no relief block | Closed in the interface | JSON v2.4a: SUPERSEDED tags, `relief_v2p4a`, `superseded_v2p4a`; §2.7 relief row; 15-24 C in §2.1-2.3 and H4 |
| R2-06 (MINOR) vented-mass sentences; CF-4 P4 | Closed in text | §9.1; CF-4 v2.0 P4 and P5; `vented_mass_brackets_v2p4a.json` |
| R2-07 (MINOR) no guard band | Closed in text; the channel uncertainty is open (Electronics) | §3.6; §10 v2.4a amendments; JSON `interlock_guard_band`; OI-33 |
| R2-08 (MINOR) Table 2.15 rows | Closed in text | Table 2.15 caption and the PURGE NOT RUN rows |
| R2-09 (MINOR) J1, lip, segment heat, RC-09, OI-27 | Closed in text | §0 items 10 and 11; §6.4; §6.5; H19; OI-22, OI-27, OI-28; `REVISION-RESPONSE.md` RC-09 note; JSON `nozzle_joint` |
| R2-10 (MINOR) Pc evidence chain | Closed in text; the channel itself is open (Electronics, founders) | §8; §10 T1 row, IGN-1, v2.4a amendments; JSON `pc_dynamic_channel`; OI-34 |
| R2-11 (NOTE) late-light model form | Partly: sensitivity done; 1-D run open | §7.6 FA-1 bullets; `fa1_outflow_sens_v2p4a.json`; OI-36 |
| R2-12 (NOTE) plume HANDBACK-SUMMARY | Done by the lead (line 172 (7)) | – |
| R2-13 (NOTE) interface configuration | Recorded for the lead | §0 Configuration; OI-37 |

## Item by item

### R2-01 (MAJOR): line 166 (3)/(4)

Required:
1. "raw" -> "filtered, 5 ms (LEAD line 166 (4))" in the six places and in A4, with line 1866 kept as the record of line 160 plus an amendment note.
2. E1 and A14 exactly as line 166 (3), including "V2 commanded closed" and the stand abort; align CF-4 P6.
3. Correct the §0 configuration line and the igniter.sequence tag.

Done:
- **A4.** It is now on the FILTERED channel for 5 ms in §0 item 1, the A4 row, H11, the FA-1 detection bullet (§9.1) and OI-18. The A4 row also carries the line-166 (4) figure: filtered light-spike peak <= 21.4 bar abs. The §7.6 record of line 160 keeps "5 ms raw" and gains the note "[Amended by LEAD line 166 (4) …]". In the JSON, `abort_matrix_v2p4.v.A4` reads filtered.
- **E1 term.** E1 = torch confirmed (2oo2) AND [closure confirmed OR the closure deadline reached]. The deadline is at or before the torch gate (E0 + 0.16 s); Electronics sets it at E0 + 0.15 s (electronics.json v2). At the deadline in flight, BLEED_FAULT goes to the FC (log-only, line 168), V2 is commanded closed and the lift proceeds. On the stand it is an abort. This text is in the E1 row (§7.3), the bleed bullet, the PURGE text, the §2.8 Closure row and items 9 and 15, the A14 row, the §9.1 detection bullet and CF-4 P6 (a)/(b)/(c). In the JSON it is in `start[0]`, `start[3]` and A14.
- **E0 - 0.05 s** is kept only as the scheduled flow end.
- **Configuration.** "to CHANGELOG line 177". The `igniter.sequence` tag now cites LEAD 153-177.

Open: none in text. The SIL/HIL freeze and IGN-1 gates stay with Electronics and the founders.

### R2-02 (MAJOR): one stand safing rule

Done. One rule (LEAD line 172 (1)) now appears in all four places:
- H9;
- §10.2;
- `igniter.sequence.v.abort_if_no_ignition[1]`;
- §7.6, which also states that it is the one rule.

The rule: N2 purge >= 60 s at >= 10 g/s; then a hold of >= 15 min before anyone approaches, with Pc at ambient and the head thermocouples falling; then safing. "wait >= 5 s" is marked as withdrawn wherever it is quoted. The new JSON block `stand_safing_v2p4a` holds the rule.

### R2-03 (MAJOR): FA-1 envelope

Done (option (b), with a first-order look at (a)).

**Envelope.** `src/fa1_envelope_v2p4a.py` (`a6b71cb487c9642e`) produces `data/v2p4a/fa1_envelope_v2p4a.json` (`64b328150025fa1e`). It is the author's construct, re-run after the v2.4 case is first reproduced to 1e-6 bar. The grid:
- 896 cases: O/F 3-12 (3 and 3.5 added beyond the request), tf 1-7 ms in 1 ms steps, t_res 0.02 / 0.06 s, pool none / q 2 MW/m2;
- two vapour readings ("vapour once" baseline, "as written" upper bracket) and both entrances;
- per case: head and aft histories, peak, rise time, time above 45 / 67.5 / 90 bar (total and longest continuous) and impulse.

**Results** (SIM on an ASSUMED construct):
- Head peak 83.0 bar abs (baseline, rounded entrance), 84.8 (sharp) and 88.0 (upper bracket).
- Aft peak 0.95-1.00 of the head.
- Time above 45 bar <= 3.65 ms (4.45 ms in the bracket); above 67.5 bar <= 1.0 ms (1.3 ms); never above 90 bar.
- Impulse <= 726 bar ms (757 in the bracket).
- Thrust <= 1.77 kN; SDOF equivalent <= 3.05 kN, against 3.48-3.60 kN for the interim 1.8 kN x 4 ms load.
- Pressure DLF <= 1.007 at periods <= 0.1 ms, and 1.05-1.20 at 0.25-1 ms (equivalent static <= 89.0 / 102.0 bar abs).
- Fuel-basis sensitivity +1.8-2.8 %.

These match the reviewer's O/F 4-6 values within 1-2 %.

**O/F bound.** The first-order fuel-vapour bound does not exclude O/F < 4. Within the construct, however, the closed-volume pressure peaks at O/F 3.5-4 and falls below that, so the O/F 3.5-4 rows bound. The inventory itself is MISSING, and IGN-1 and T4 on the dynamic channel are the evidence.

**Lead and Mechanical.** The lead fixed the load in line 173. Mechanical reported margins in line 176, and the lead acted in line 177 (TC-09 to Inconel 718, J-FWD, gimbal bearings). Mechanical then put TC-09 in Inconel 718 into CAD v3.5 (line 178) and moved J-FWD to A4-80 screws (yield MS +0.29 at 92 bar, ultimate +0.61 at 102 bar; line 179). The bearing selection is OPEN: it needs C0 >= 1.80 kN per bearing from a maker datasheet. The FMEA consequence is "yield possible; ultimate not demonstrated" until those actions are in CAD v3.5 (§9.1).

Open:
- the fuel-vapour inventory at light;
- the gimbal bearing selection (Mechanical, line 179);
- IGN-1.

### R2-04 (MAJOR): T1-T4 law decision

Done in `T1-T4-REGRESSION-SPEC.md` v2 (`bbf0ea642453dc7a`). The computation is `t1t4_law_resolution_v2p4a.json` (`05b5ae5c20e04bd8`).

1. **Burden reversed** (LEAD line 172 (3)). The 1.25 gate is the default. It is relaxed only when the oxidiser-flux law is positively shown: S_meas + 1.645 σ < S_total on the T3 holds and on one T1 or T2 firing, with σ(S) <= 1.5 %.
2. **Stations.** The law stations are x/L 0.80, 0.85 and 0.90. a_meas stays at x/L 0.97.
3. **σ and repeats.** σ(S) <= 1.5 %. Repeats follow N = ceil(s1^2 / (σt^2 - s_s^2)) (Table R). The T3 holds carry the decision: P(show) is 0.79-1.00 over the band at σ 1.5 %, against 0.24-1.00 for T1 at 100 %.
4. **Systematic terms.** Eight terms with ASSUMED residual targets: soak-back (N2 quench; two-duration differential), char and melt layer (witness sectioning), ovality (>= 4 diameters), print density (density map), transients, spray, aft-end flow and station position.
5. **Errs safe**, over 78 B1 records (30 at 85 m and 48 at 62 m; O/F down to 1.78; DERIVED):
   - A T1-only calibration does NOT err safe with the full allowance: ρ_max is 1.068, which leaves 3.0 % of the 10 %.
   - With a T3 hold it does: ρ_max is 1.004 at 20 % and 0.990 at 12.5 %.
   - Proposal for the lead: a_meas,gate = max(1, ρ_max) x a_meas whenever the oxidiser-flux law is not shown.

A first pass of the computation had four defects:
- the wrong DC-D file;
- start rows read as run rows;
- the analytic model burning past burn-through;
- the 62 m records counted in the 85 m group.

All four were corrected before use and are recorded in §13. The model now reproduces the q1d web on DC-D (14.25 against 14.24 mm).

Open: the lead's decision on the errs-safe correction; T1-T3 data.

### R2-05 (MINOR): stale interface values; relief block

Done in combustion.json v2.4a (`write_interface_v2p4a.py`, `bb72351d5719b99e`). All 2831 v2.4 keys are kept and 175 are added.

**Tagged SUPERSEDED or replaced:**
- `flights_per_insert_A1`;
- both 42.85 bar keys;
- `b_seat.leak_tightness` (0.039 g/s);
- `priming_rule[1]` and `[2]`;
- `trapped_liquid_relief` (<= 7.5 MPa);
- `model_transients` (0.28-0.29 s);
- `open_interface_issues[5]` (0-69 bar, CLOSED);
- `tank_pressurisation` and `arm_preconditions[0]` (now 15-24 C at ARM; the 25 C computed ranges are marked as bounds).

**New block `relief_v2p4a`:**
- tank relief 6.9 MPa;
- fire relieving 8.35 MPa;
- MAWP >= 8.42 MPa;
- proof >= 10.5 MPa;
- back-relief check Cv >= 0.1;
- disc 9.5 MPa ± 5 %.

Line 172 (6) calls the block "relief_v2p4", and the brief calls it relief_v2p4a. The block records both names; the content is the same.

The report's 15-25 C passages (§2.1-2.3, H4) are changed. `superseded_v2p4a` lists every v2.4a supersession.

The ENG-09 text belongs to the lead, who superseded it in line 172 (6).

### R2-06 (MINOR): vented mass and CF-4 P4

Done (`vented_mass_brackets_v2p4a.json` `8e8ca9329c74a01f`).

The §9.1 sentences now say:
- **Open-element bracket.** Its minimum is the all-vapour line 8.49 t up to 1.0 s.
- **Barrier-element bracket.** Its minimum lies below that line until 1.6 s: 3.17 g at 0.5 s and 5.93 g at 1.0 s. The cause is the T4 stall behind a capillary barrier, a model construct (bubble point about 0.7 kPa against 45.5 bar) that a real T4 will not reproduce.
- **Maximum.** It is not all-liquid flow: 11.9 g at 0.5 s and 72.9 g at 2.5 s, against 15.6 g and 78.1 g on the all-liquid line.

CF-4 v2.0 changes:
- P4 is per tap and per phase: vapour >= 3.4 g/s and liquid >= 12.5 g/s per tap, against the open-element reading. It is never judged on the barrier stall.
- P5 names the brackets.

The RG-16 note to GNC is covered. LEAD line 172 (8) has GNC fly the published table and report separately. GNC rev2 (line 174) reports that its miss-side failure is not caused by these minima.

### R2-07 (MINOR): guard band

Done in text (LEAD line 172 (4)).

- **Size of the margin** (DERIVED from the Table 3.8 slopes). The 0.67 bar margin equals about 0.92 K, or 1.14 bar of P_tank.
- **Thresholds.** They sit below 24 C and 55.28 bar abs by the total channel uncertainty, which Electronics states (MISSING; OI-33).
- **CF-1 / CF-3 acceptance.** Full-stroke Cd <= 0.80, and a line loss at the failure flow >= the model. Otherwise MEOP is restated.

This is in §3.6, the §10 v2.4a amendments, H4 and JSON `interlock_guard_band`.

### R2-08 (MINOR): Table 2.15

Done. The PURGE NOT RUN rows now read "All samples, would-be (A2 aborts beyond W)", and the caption names `E0_E2_given_light_quantiles_5pct_s`.

The LO row also gives the given-light values: median 0.480 s, p95 0.576 s, max 0.628 s. It notes that every such light is followed by the 23.4 cm3 gap (see the line-175 check below). The HI row says that there is no light within W.

### R2-09 (MINOR): text consistency

Done:
- **J1.** It is CONFIRMED (line 146) in §0 item 11, the §6.5 header, H19, OI-4/OI-5, OI-22 and §13. J2 is marked as not selected. The JSON `nozzle_joint` carries the J1 status.
- **Lip.** 250 C was a goal, not a limit (line 145). With J1 the lip runs at about 342 C.
- **Segment heat.** §6.4 now gives 0.83-9.0 kJ on CAD v3.4.1 (831-9011 J). The 0.88-9.87 kJ were Mechanical's totals on the superseded v3.4 route (875-9872 J).
- **RC-09.** Decided by line 170 (1): the 25 bar cap stays, and the rated thrust is about 487 N at the eta_cf low end. This is reflected in §0 item 10, in OI-28 and in a note added to the RC-09 row of `REVISION-RESPONSE.md`. The original response is archived.
- **OI-27.** Marked Done.

### R2-10 (MINOR): Pc evidence chain

Done in text (LEAD line 172 (5)).

**Stand dynamic channel**, for IGN-1 and T1-T3:
- >= 10-20 kHz with an anti-alias filter;
- a flush mount or a characterised short sense line (resonance measured);
- a range >= 100 bar abs, to cover the FA-1 envelope.

**Flight.** LIGHT_SPIKE values logged at 1 kHz are lower bounds.

This is in §8 (both test requirements), §10 (T1 row, IGN-1, v2.4a amendments), H14, the §9.1 detection bullet, JSON `pc_dynamic_channel` and OI-34. The T1-T4 specification v2 logs on the same channel.

Open: the channel hardware and its price, TO-QUOTE (Sønderborg DK-6400; Electronics, founders).

### R2-11 (NOTE): late-light model form

Partly closed.

| Effect | Status |
|---|---|
| Vapour double count | Kept as the "as written" upper bracket. The baseline counts it once. |
| κ | Kept, since it is conservative (+3.7 % at 6.6 kg/m3); stated under "Not modelled". |
| Frozen outflow | Area-scaling sensitivity (`fa1_outflow_sens_v2p4a.json` `540a78f8b9634f76`; a first-order emulation, ASSUMED). The peak rises 0.5-0.6 % at tf 1 ms and 1.4-1.6 % at tf 3 ms for a 3.7 % area reduction (1.1-1.3 % / 3.0-3.5 % at 8 %). Time above 45 bar rises 0.15-0.55 ms. The 92 bar design value becomes about 92.2 bar (92.9 at 8 %), inside the 102 bar sensitivity. |
| Lumped nodes (wave peaks) | Not bounded. A 1-D gas-dynamic run of the worst row is OPEN (OI-36, Combustion). |

### R2-12 (NOTE): plume HANDBACK-SUMMARY

Done by the lead (line 172 (7); HANDBACK-SUMMARY `d12c8862bf5524a4`). Combustion did not edit that file.

### R2-13 (NOTE): interface configuration

Recorded for the lead in the §0 Configuration line and as OI-37:
- mechanical.json v2.1 (line 179) adds the bleed topology and the FA-1 per-part tables, but it has no MEOP, MAWP or rounded-entrance keys and still quotes the tank relief as "<= 7.5 MPa";
- electronics.json v2, as reviewed, shows A5 OPEN, the 2.0 s hold and the Burkert 6027 HP.

Combustion's v2.4a uses electronics.json v2's BLEED_FAULT time, E0 + 0.15 s, as the closure deadline. It is consistent with line 166 (3).

## Checks requested by the lead after GNC rev2 (CHANGELOG line 175 (3))

Both checks are in `src/unpurged_start_check_v2p4a.py` (`41fad4500f472bd4`), which writes `data/v2p4a/unpurged_start_check_v2p4a.json` (`4c745dcfbf09aef7`). The run took 27 s. The script first reproduces the rg01 ignition set (seed 2024, 200 000 samples) and six published P_abort values. The decomposition, purge and MEOP grids were not re-run.

### Check 1: unpurged start at the late-commit point

**Verdict: hazard outside the abort model.** The provisional rule is refuted as written (SIM on ASSUMED delays; DERIVED line states).

**Why the abort model misses it.** The model behind Table 2.15 ends at E2. A light inside a liquid slug counts as a success, and the voids behind that slug are not followed.

**What happens in the PURGE NOT RUN LO worst state** (12.5 cm3 pocket, 11.2 cm3 slug, 23.4 cm3 gap):
1. Every light within W (P 0.758) is in the first slug.
2. The 23.4 cm3 vapour gap follows every light. It arrives 0-0.091 s after E2 on the 2500 N/s ramp to 200 N (median 0.053 s), or at most 0.193 s with the flow held at the lift. It lasts 0.139-0.156 s on the ramp, or 0.365 s at the lift flow.
3. E2 in the latency model is Pc > 3 bar abs, so the drogue-release term (Pc valid AND >= 300 kPa abs) is already true at E2.
4. In the gap the A3 ratio is <= 0.24 at 62.5-500 N (CEA c*; n 0.35-0.68 ASSUMED; flame assumed to survive), below the 0.40 threshold.
5. A3 therefore trips after the release in 0.712 of the starts (0.94 of the lights). The lined reference state gives 0.819.

**Consequence.** This is GNC's "dead vehicle released" class (about -32 m/s at touchdown, line 174), not the abort under the drogue (about -22 m/s). It leaves no successful relight, so P_total is about 0, not 0.75.

**Population.** At 0-2 deg, over unweighted bracket cases, the mean P(released, then A3) is:

| Records | Mean P(released, then A3) |
|---|---|
| Unlined LO | 0.58 |
| Lined LO | 0.52 |
| Unlined HI | 0.22 |
| Lined HI | 0.44 |

**States without the hazard.**
- **Purged states:** no post-light gap.
- **HI worst state:** it never lights within W, so it brings no new hazard.
- **Least state:** a 4-11 ms dip, below the A3 detection.

**FA-1 interaction.**
- At 200 N there is no liquid re-admission.
- On a 500 N ramp, 25 % of the trips re-admit up to 3.56 g with the flow held, or 0.53 g with linear closing, against the 2.141 g fast part. This matters only if the flame went out in the gap, which is not modelled.

**Proposal for the lead.** No commit by the plain trigger - 1.7 s means no relight on that pass, as A14 already does for a fail-closed bleed. A ride-through mode is a research option only:
- **Hypothesis:** with the drogue release held on unpurged starts, the torch kept on and A3 adapted, the flame survives the 0.14-0.37 s gap.
- **Comparator:** the no-relight rule.
- **Evidence:** CF-4 run O-3 and IGN-1.
- **Refutation:** a flame-out or an A3 trip in the gap.

The finding is in REPORT §2.8 (Table 2.16), H20, B-6, OI-31 and JSON `purge_commit_rule_v2p4a`.

### Check 2: tank outlet coverage during PURGE

**Verdict: covered quasi-statically, with a large margin, IF the outlet is on the aft bulkhead of an axial tank.** This is not a final verdict (DERIVED; CoolProp; GNC SIM inputs `purge_outlet_inputs.json` `47b4deb96ea22043`).

**Geometry used.** mechanical.json v1 concept: ID 95.25 mm, length 0.4449 m, flat bulkheads. It is not yet in CAD.

**Results.**
- Depth over the aft bulkhead: 126-133 mm at the 766 g minimum, and 193-202 mm at 1170 g.
- Drop of the free surface at the wall:
  - 2.3 mm at the 2.71 deg specific-force angle;
  - 5.7 mm at the 6.86 deg largest tilt.
- The wall uncovers only beyond 69.3 deg.
- Lubin-Springer dip height: 7.9 mm (LITERATURE; applicability to N2O TO-VERIFY).
- Ekman spin-up: >= 359 s (ν 0.5-2e-7 m2/s, ASSUMED), so no drain vortex forms in 2.9 s.
- First slosh mode: 2.92 Hz.

**MISSING:**
- the outlet position and diameter;
- any dip tube, sump, anti-vortex plate or screen;
- the orientation, and which bulkhead is aft;
- the bulkhead face near the outlet;
- a slosh amplitude (sim6 is lumped);
- the specific-force angle over the 500 runs (six records were given).

Owners: Mechanical and GNC (OI-32).

**New finding.** The 2.71 deg specific-force angle in the same records is above the 2 deg basis of the purge model. The purge was not re-run, per the brief; this is OPEN (OI-35). CF-4 v2.0 adds 3 deg runs.

### Commit wording

The PURGE text says: "PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge (LEAD line 175 (3), PROVISIONAL)". It appears in:
- REPORT §0 item 12;
- §2.8 item 18 and the Sequence row;
- the §7.3 PURGE bullet;
- §7.7;
- H17 and B-5;
- JSON `igniter.sequence.v.start[0]` and `purge_commit_rule_v2p4a`.

Line 164's "the FC delays T_fire" is marked as withdrawn wherever it appeared. What follows a missed commit is left to the lead (OI-31).

## Tests run (digital)

- Every v2.4a script asserts its input hashes.
- The FA-1 envelope reproduces the v2.4 case to 1e-6 bar.
- The unpurged check reproduces six published P_abort values.
- The T1-T4 model reproduces the q1d web.
- `build_report_v2p4a.py` applies 104 edits. Each edit matches exactly once, and each anchor is unique.
- A stale-phrase scan of the report and the interface leaves only withdrawn, superseded or flow-end wording.
- No physical test exists. Matching hashes and passing scripts are not approval.
