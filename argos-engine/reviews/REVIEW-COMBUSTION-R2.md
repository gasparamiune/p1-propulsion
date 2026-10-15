# REV-COMB-2: Independent re-review of Combustion v2.4 and plume v2.2b

## 0. Checkpoint (docs/SUPERVISION-WORKFLOW.md form)

**Delivered by.** Combustion and Propulsion (author). Handback 2026-10-13, CHANGELOG line 169; installed by the lead in line 170.

**Reviewed by.** Independent Combustion and Propulsion reviewer (REV-COMB-2).
- I authored none of the reviewed files.
- My files are only in `reviews/combustion/r2/`.

**Date.** 2026-10-13.

**Claim (verdict).**
- 02-combustion v2.4: REVISE (targeted).
- 05-plume-cfd v2.2b: ACCEPT.
- REV-COMB-1 status: 13 CLOSED, 7 PARTLY CLOSED, 0 OPEN.
- New findings: 0 BLOCKING, 4 MAJOR, 6 MINOR, 3 NOTE.

**Configuration.** See §1; sha256/16 is given for every file read.

**Sources.**
- The author's files (§1).
- REV-COMB-1.
- CHANGELOG lines 140–170.
- REQUIREMENTS rev 2 and its amendments (l.101–117).
- REV-ELEC-1 (RE-01, RE-02, RE-05) and REV-GNC-2 §5.
- Tools: Cantera 3.2.0 (GRI-3.0 species and thermo), CoolProp 8.0.0 (HEOS N2O), RocketCEA (NASA CEA), numpy 2.5.4, scipy 1.18.1.

**Files.** Reviewer scripts and outputs (§1.3).

**Tests.**
- Seven reviewer scripts.
- Each was run with `python -I`, one process at a time, nice 10, single thread (NUMBA/OMP 1).
- Each asserts the hashes of its inputs.
- The author's code is never imported.

**Unknowns.** §9. **Next closure.** §10.

**What I did not touch.** I edited no report, interface, CHANGELOG, REQUIREMENTS or SUPERVISION.json.

## 1. Scope and configuration

### 1.1 Reviewed (author)

**Reports and interface.**
- 02-combustion/REPORT.md v2.4 `32e366bd78437dc0`
- REVISION-RESPONSE.md `ee951fb865c1459d`
- interfaces/combustion.json v2.4 `469727032124329f`
- CF-4-SPEC.md `c9e1efbb18177155`
- T1-T4-REGRESSION-SPEC.md `25a207af8fe61f21`
- 05-plume-cfd/REPORT.md v2.2b (= REPORT_v2p2b.txt) `140b3c59f8323bba`
- 02-combustion/HANDBACK-SUMMARY.md `1d760e9e197429d8`
- combustion.json v2.3 `d9ec54fbf450e243`. Used only for the key-retention check; iface_v3c copy, byte-identical to the former hub file per line 161 (10).

**Scripts** (read for method and inputs only).
- src/late_light_spike_v2p4.py `e8aad73cb6972cb3`
- hard_start_multivolume_v2p4.py `dd8aadf76f59113e`
- hard_start_v2p4.py `00a966bb1572d075`
- purge_vented_mass_v2p4.py `59f617429125dc16`
- retained_vapour_v341_v2p4.py `41ab5746143e28e3`
- rg01_line_states_v2p4.py `a7f68a1a84286f9b`
- meop_basis_v2p4.py `63c1d736097fed6b`
- fd01_element_deficit_v2p4.py `ad9a9b7290bc2c0a`

**Data** (used as comparison values).
- data/v2p4/late_light_spike_v2p4.json `57fce738164fd571`
- purge_vented_mass_v2p4.json `0038561f71a51502`
- rg01_line_states_v2p4.json `2939549811d4c381`
- purge_duration_v2p4_trade.json.raw.json.gz `02c30eb2e6569e8d`
- data/v2/v2p4/hard_start_v2p4.json `1bdcf295ce6f7413`
- hard_start_multivolume_v2p4.json `a804970397b24857`
- meop_basis_v2p4.json `4aa310a7c7d925a6`
- meop_cv36_check_v2p4.json `6fdf07cee1958d00`

### 1.2 Context

- REVIEW-COMBUSTION.md (REV-COMB-1) `54ceaa46e9e17594`
- CHANGELOG.md `7b9c322369b394f5`
- REQUIREMENTS.md `080df16aacf9dcfd`
- electronics.json v2 `da067408c1594814`
- mechanical.json v2 `4f024ed4ccb4618c`
- gnc.json v3 `3e97c378cfebee95`
- REVIEW-ELECTRONICS.md `471d830c8d00dd85`
- REVIEW-GNC-R1.md `a5c6b147c830b67e`

### 1.3 Reviewer artefacts (reviews/combustion/r2/)

| Script | Output | Purpose |
|---|---|---|
| r2_vented_trace.py `bed15d36df8c06e6` | r2_vented_trace.json `96f38468a78784ca` | My own streamer of the raw purge trade; minimum and maximum records per Tp on the decided path (2c) |
| r2_json_scan.py `8ed13f634e5fe60e` | r2_json_scan.json `369b409396befb53` | v2.3 key retention; "raw" near 30 bar or A4; the superseded_v2p4 list (2j) |
| r2_superseded_scan.py `bd8566f3aa75d2cd` | r2_superseded_scan.json `7bd35451224fda83` | 25 superseded or contradicted values checked against live JSON leaves and live report lines |
| r2_late_light.py `716819d45c493f1b` | r2_late_light.json `584af85da73345de`; log `88a2779bdb65ba74` (464 s) | Independent three-node late-light / FA-1 model; the author's construct as written |
| r2_late_light_v2.py `48ed04654be9b347` | r2_late_light_init005.json `b89cc4eac0eac456`; log `c46074e28be4ef2d` (146 s) | The same model with the chamber vapour counted once |
| r2_fd01_energy.py `06d5ab62cf086382` | r2_fd01_energy.json `e2876e484213e823` | FD-01 deficit (four readings); decomposition and expansion energy; capillary bubble point |
| r2_meop_cstar.py `de42a5bd4710624f` | r2_meop_cstar.json `4034443abc7806b6` | MEOP-row closure with an independent equilibrium c*; OI-28 arithmetic |

A scratch check (not in the hub) compared the equilibrium-table lookup in r2_late_light with direct Cantera UV equilibrium at four states. Pressure agreed within 0.003 %.

## 2. Criteria and method

**Criteria.**
- **C1.** Each RC response is true in the cited section and file.
- **C2.** The evidence tag (SIM, DERIVED, ASSUMED, LITERATURE or LEAD) is correct.
- **C3.** The status is honest under REV-COMB-1's closure criteria as written.
- **C4.** The new numbers reproduce at first order or better with independent code.
- **C5.** combustion.json v2.4 and the report agree with lead lines 160–170, the REQUIREMENTS amendments and the author's own superseded_v2p4 list.
- **C6.** Safety rules (aborts, purge, safing) say the same thing in the report, the interface and the specifications.

**Method.**
- I read the changed sections.
- I scanned live JSON leaves and live report lines by script, excluding §13, which is the historical record.
- I ran an independent late-light network with equilibrium thermochemistry.
- I ran independent FD-01, energy and c* checks.
- I traced the author's raw purge records to find the cause of the anomaly.

**Not done.**
- I did not re-run the author's purge Monte Carlo, P_abort, latency sampling or erosion.
- I did not independently derive the full-stroke injector flow behind the MEOP rows.

Agreement with the author shows only that a computation repeats on the same ASSUMED construct. It is not physical evidence.

## 3. Verdict per REV-COMB-1 finding

| RC | Author | Reviewer | Basis | Gate for the remainder |
|---|---|---|---|---|
| RC-01 (BLOCKING) sequence and aborts | Partly | **PARTLY CLOSED** | Present: epochs E0–E3, torch gate 0.16 s, W 0.40 / 0.65 / 0.35 s, A5 replaced by LIGHT_SPIKE, 2oo2 E1, A16, drogue predicate. Missing: line 166 (3)/(4) is not implemented (R2-01). The stand safing rule contradicts itself (R2-02). REV-ELEC-1 is REVISE. | SIL/HIL freeze, IGN-1, first static fire |
| RC-02 (BLOCKING) hard start | Partly | **PARTLY CLOSED** | The decomposition bound reproduces (§4 2a). FA-1 is unbounded by decision, and its pulse spec is a single point at an ASSUMED O/F (R2-03). | Mechanical FA-1 pulse check, IGN-1, A1 |
| RC-03 (MAJOR) relight latency | Partly | **PARTLY CLOSED** | Distributions delivered; arithmetic consistent. The PURGE NOT RUN rows are mislabelled in Table 2.15 (R2-08). The GNC re-fly is pending. | GNC RG-01 re-fly, T4 |
| RC-04 (MAJOR) trapped liquid, relief, safing | Closed | **PARTLY CLOSED** | Report §2.7 and §10.2 are done. REV-COMB-1's closure criterion ("relief specification is in combustion.json") is unmet: there is no v2.4 relief or MAWP key, and the live v1 key still says "<= 7.5 MPa" (R2-05). | CF-3 |
| RC-05 (MAJOR) stored energy | Closed | **CLOSED (digital)** | Table reproduced (§6). The "as recalled" constants (17.9 m/kg^(1/3), API 521 C1) stay TO-VERIFY before the exclusion-zone decision. | CF-3, T1 (founders) |
| RC-06 (MAJOR) throat-insert life | Closed | **PARTLY CLOSED** | Withdrawn in the report, but `thermal_and_loads.flights_per_insert_A1` = [1.0, 4.3] is still live with a DERIVED tag (R2-05). | ENG-06 freeze, spares |
| RC-07 (MAJOR) regression band | Closed | **CLOSED** (band run) | The new T1–T4 measurement specification has its own finding (R2-04). | B1 |
| RC-08 (MINOR) MEOP basis | Closed (accepted) | **CLOSED** | The combustion-side closure reproduces; the author is conservative by 0.9–1.6 %. Guard band missing (R2-07). The 42.85 bar key is still live (R2-05). | ENG-09 freeze |
| RC-09 (MINOR) eta_cf | Partly | **CLOSED** by line 170 (1) | Arithmetic verified: 25.67 bar and 487.0 N. ENG-01 compliance at the low end of the band is a T1 result. The response text predates line 170 (R2-09). | T1 |
| RC-10 (MINOR) CFD wording | Closed | **CLOSED** | Plume l.13 and Table 8.2. HANDBACK-SUMMARY l.80 has been replaced. | – |
| RC-11 (MINOR) correlation claim | Closed | **CLOSED** (report) | Plume l.8–13. HANDBACK-SUMMARY l.74 still says "+0.5 %" (R2-12). | – |
| RC-12 (MINOR) relief vs MEOP | Closed | **CLOSED** in the report | §2.7: tank relief set at 6.9 MPa, MAWP ≥ 8.42 MPa, proof ≥ 10.5 MPa. Not in the interface. ENG-09 rev 2 (a lead file) still says "trapped-liquid relief ≤ 7.5 MPa" (R2-05). | CF-3 |
| RC-13 (MINOR) consistency | Closed | **PARTLY CLOSED** | (b) "15–25 C" contradicts the amended ENG-12 (15–24 C at ARM) in §2.1–2.3, H4 and the JSON. (d) A JSON open issue still offers 0–69 bar. (g) The JSON keeps 0.039 g/s (R2-05). | next patch |
| RC-14 (MINOR) cleaning | Closed | **CLOSED** (procedural) | Standards cited "as recalled", TO-VERIFY. | CF-1 |
| RC-15 (MINOR) material data | Partly | **PARTLY CLOSED** | Status is honest; OI-25 has owners. | drawing release |
| RC-16 (NOTE) L* | Closed (accepted) | **CLOSED** | – | – |
| RC-17 (NOTE) Bartz | Closed | **CLOSED** | – | – |
| RC-18 (NOTE) eroded throat | Closed | **CLOSED** | – | – |
| RC-19 (NOTE) CFD presentation | Closed | **CLOSED** (report) | Items (a)–(e) are in plume v2.2b. HANDBACK-SUMMARY l.86–87 keep the old figures (R2-12). | – |
| RC-20 (NOTE) interface hygiene | Closed | **CLOSED** | Tags added; gnc.json v3 published. | – |

**Acceptance criteria (REV-COMB-1 §10).**
1. Partly: R2-01 is open, REV-ELEC-1 is REVISE, and IGN-1 is pending.
2. Partly: the relief specification is not in the interface, and the safing rule contradicts itself (R2-02).
3. Partly: the GNC re-fly is pending.
4. Closed, with R2-04 on the measurement specification.
5. Closed except RC-13 (partly) and RC-15.
6. The re-review scope was respected.

## 4. New claims since v2.3 (brief items 2a–2j)

### 2a. Late-light peaks (decomposition)

**Model.** My own three-node network: head 58.67 cm³, port, aft 119.53 cm³, throat 147.9 mm².
- Each node is in chemical equilibrium at its own (u, ρ), from Cantera TV tables. The author instead uses a calorically perfect gas with κ fitted at 40 kg/m³.
- Reactant enthalpy is taken from CoolProp.
- The author's construct is kept unchanged: vapour by node volume; spray × t_res at the head; top-hat tf; pool at q; continuing flow at the lift.

**Two readings of the construct.**
- "As written": an inert initial gas at the cold-flow pressure. This counts the chamber vapour twice.
- "Vapour once": the initial gas is cut to 5 %.

| State | Author, sharp / rounded [bar] | Vapour once [bar] | As written [bar] |
|---|---|---|---|
| Pad 15 C | 43.7 / 40.6 | 42.1 / 38.7 | 44.5 / 41.5 |
| Pad 20 C | 43.1 / 40.1 | 41.4 / 38.3 | 43.9 / 41.1 |
| Pad 25 C | 42.0 / 39.3 | 40.3 / 37.4 | 42.8 / 40.2 |
| A1 relight | 37.8 / 36.7 | 36.1 / 34.9 | 38.8 / 37.7 |

**Verdict: plausible and reproduced.** The author's values sit inside my bracket.
- With the rounded entrance, the 45 bar MEOP holds for decomposition in every variant I ran. The maximum is 42.24 bar, with the port exit restricted to 1.0 A_port instead of the author's 50 A_port.
- With the sharp entrance, that variant reaches 45.15 bar for 0.02 ms. This supports line 160 (4), which made the rounded entrance REQUIRED.
- Phase-specific enthalpies (vapour and pool at chamber h_g, spray at chamber h_f) lower the pad peaks by 0.4–1.0 bar and leave A1 unchanged. The author's tank-liquid basis is therefore conservative.
- Model-form limits are in R2-11.

### 2b. FA-1 (fuel-assisted fast part at relight)

**At O/F 8 the author's figures reproduce.** The author gives 48.9–75.5 bar at tf 1 ms, above MEOP for ≤ 3.0 ms. My bracket contains this:

| Case (O/F 8, tf 1 ms) | Vapour once | As written |
|---|---|---|
| t_res 0.02, no pool | 44.7–45.1 bar | 52.0–52.3 bar |
| t_res 0.06, no pool | 65.5–67.3 bar | 73.0–74.6 bar |
| With pool, q 2 MW/m² | 69.6–71.2 bar; 2.4–2.5 ms above MEOP | 77.1–78.6 bar; 3.3–3.5 ms above MEOP |

**But O/F 8 is not a bound on fuel.** It is an ASSUMED fuel fraction, and the pressure rises as the fast part gets richer:

| O/F | Closed-volume UV of fast part, vapour once [bar] | Peak at tf 1 ms, vapour once / as written [bar] | Max time > 45 bar over tf 1–7 ms, vapour once / as written [ms] | Max time > 67.5 bar [ms] |
|---|---|---|---|---|
| 12 | 65.2 | 61.7–63.2 / 68.9–70.3 | 1.84 / 2.70 | 0 / 0.10 |
| 10 | 68.9 | 65.0–66.6 / 72.5–73.9 | 2.12 / 3.00 | 0 / 0.40 |
| 8 | 74.0 | 69.6–71.2 / 77.1–78.6 | 2.50 / 3.46 | 0.14 / 0.78 |
| 6 | 81.4 | 76.0–77.8 / 83.9–85.4 | 3.06 / 4.16 | 0.62 / 1.22 |
| 5 | 86.0 | 79.8–81.5 / 86.5–88.0 | 3.44 / 4.54 | 0.84 / 1.36 |
| 4 | 89.3 | 82.2–84.0 / 86.4–88.0 | 3.60 / 4.58 | 0.96 / 1.34 |

**Further results.**
- Time above MEOP is non-monotonic in tf. Its maximum falls at tf 3–7 ms, between the author's grid points (1, 5, 10 ms).
- The aft node peaks at 96–97 % of the head (68.3–85.2 bar). The pulse therefore loads the nozzle joint and the aft closure, not only the head.
- **Missing datum:** the fuel-vapour inventory in the warm 32.2 mm port at the moment of light. It is not modelled.
- Torch propane is not the fuel source. At 0.055 g per 0.6 s start (combustion.json `igniter.torch_sizing`) it only moves the fast part to about O/F 39.

**Is "3 ms" conservative for Mechanical?** Only at O/F 8 in the "vapour once" reading. It is not an envelope, and for the case shell the duration is not the governing quantity:
- The breathing-mode period of a 6061 shell with R ≈ 30 mm is about 0.04 ms (DERIVED; c ≈ 5.1 km/s). The response is quasi-static, so the peak governs.
- Duration and impulse govern parts with periods of 1–5 ms (gimbal, thrust mount, pintle linkage).
- The thrust spike is about 1.3–1.8 kN for 1–4 ms (DERIVED; Cf 1.25–1.35 ASSUMED).
- The impulse above P0 over 25 ms is 580–760 bar·ms, about half of it from the pool.
- ENG-09's minimum factors put the yield design point at 67.5 bar and the ultimate design point at 90 bar. The tf 1 ms envelope (70–88 bar) lies between them.

See R2-03.

### 2c. Purge on the decided path

**Flows and timing: confirmed.**
- My per-tap flows at the coast state (289.5 K, 46.47 bar) are 15.63 g/s liquid (Dyer, Cd 0.70) and 4.25 g/s vapour. The author has 15.62 / 4.25. The 31.24 g/s total is confirmed.
- The needed time of 1.9 s becomes 1.94 s with the element (1.9 / 0.978).
- "≤ 73.0 g at 2.5 s" is consistent: it is below the 78.1 g all-liquid figure because flow starts with vapour.
- P_abort 0 and the 1.9 s itself (queue model, slip brackets, ASSUMED Cd) were not reproduced. CF-4 is their gate.

**Vented-mass anomaly: cause found.** From my own streamer over the 181 440 raw records:
- At every flow time, all 20 lowest records come from the barrier-element bracket (unlined, HI wet, run380, slip s 1.0 or swall).
- In that bracket, T4 vents its 2.86 cm³ downstream crown in about 0.1 s.
- It then stalls while the FD-01 queue front is vapour, venting only regrowth at about 1.3 g/s.
- The minimum therefore rises at only about 5.5 g/s: 3.17 g at 0.5 s and 5.93 g at 1.0 s.
- The "~0.12 s of no flow" in line 170 (3) is the integrated shortfall against 8.49 g/s at 0.5 s (1.07 g / 8.49 g/s). It is not a dead time.

**Does it matter?**
- It does not move 1.9 s, 2.5 s, 73.0 g or 76 g.
- It falsifies two sentences in §9.1 (R2-06).
- Physically, a capillary barrier at a wetted 15 µm element holds about 0.70 kPa (σ 2.62 mN/m from CoolProp; bubble point 4σ/d). That is 1.5 × 10⁻⁴ of the 45.5 bar purge ΔP. If "barrier" means capillary blocking, the T4 stall cannot happen under purge flow; the bracket is a model construct.
- It does matter for the RG-16 minimum envelope.
- It also matters for CF-4 P4: "≥ 80 % of model" must name the bracket and the phase (R2-06).

### 2d. FD-01 element deficit

My four readings, with the element taken as an orifice of Cd·A 1.57 mm² (ASSUMED):

| Reading | Deficit |
|---|---|
| Incompressible series | 1.50 % |
| Metastable liquid (Dyer, κ < 1) | 1.08 % |
| Equilibrium flashing in the element (restrictor inlet quality 0.8 %, p_mid 45.87 bar) | 2.17 % |
| Vapour | 0.57 % |

**Verdict: "≤ 2.2 %" reproduces.**

**Remaining limits.**
- A sintered or mesh element follows a Darcy–Forchheimer law, not an orifice law.
- Loading over life raises its ΔP.
- The 1.57 mm² rating must be stated at a defined test fluid and flow.

The author's trigger (re-run the two-flow grid if measured Cd·A < 0.63 mm²) is the right control.

### 2e. Stored energy

| Quantity | Reviewer | Author |
|---|---|---|
| Decomposition energy, gas | 1.854 MJ/kg | 1.854 |
| Decomposition energy, liquid at 20 C | 1.599 MJ/kg | 1.603 |
| Flight tank, decomposition | 0.772 kg TNT / 16.4 m | 0.774 / 16.4 |
| Flight tank, expansion at 20 C | 126.6 kJ = 0.030 kg TNT / 5.6 m | 0.030 / 5.6 |
| Flight tank, expansion at 35 C | 0.038 kg TNT | 0.040 |
| A1 residual, expansion at 20 C | 0.0141 kg TNT / 4.33 m | 0.014 / 4.3 |
| Ground tank (from 4.01 kg TNT) | 28.4 m | 28.4 |

**Verdict: reproduced.**

**"As recalled" constants that the table and the relief sizing rest on.** All must be verified before the founders fix the exclusion zone:
- 17.9 m/kg^(1/3) scaled distance for 6.9 kPa. My own recollection of the K45 correspondence is also unverified.
- The API 521 fire-heat form with C1 43.2 / 70.9 kW.
- Taylor-bubble Froude numbers 0.63 / 0.35.
- Mica/vermiculite rating of 900 C.
- Flexible-graphite oxidation limits.
- PEEK/FKM seat temperature class.
- 17-4PH strengths.

TNT equivalence by energy at 100 % yield is a bound, as the author says.

### 2f. MEOP basis 44.33 bar, margin 0.67 bar

**Combustion-side closure: reproduced.** I computed Pc = η·c*_eq·ṁ_ox(1 + 1/OF)/At using my own RocketCEA c* (my own cards, built from the same ABS_TYP data).

| | Row 1 | Row 2 | Row 3 | Row 4 |
|---|---|---|---|---|
| Reviewer [bar] | 44.62 | 45.87 | 43.84 | 43.27 |
| Author [bar] | 45.01 | 46.27 | 44.26 | 43.96 |

The author is conservative by 0.9–1.6 %. The full-stroke injector flow (Dyer at 4 mm with line loss) was not re-derived.

**What the margin means.**
- 0.67 bar equals about 0.9 K of tank temperature (Table 3.8 slope: 0.72–0.73 bar/K) or about 1.1 bar of tank pressure.
- The interlock (24 C; 55.28 bar abs = 54.27 bar g on the 170BG) has no measurement guard band.
- Cd at full stroke enters directly. The author's own v2.3 rows give about 0.28 bar per 0.01 of Cd, so Cd 0.85 adds about 1.4 bar.

See R2-07.

### 2g. eta_cf band 0.95–0.975 and OI-28

**Arithmetic confirmed.**
- 25.01 × 0.975 / 0.95 = 25.67 bar. The author's 25.63 includes Cf(Pc).
- 499.8 × 0.95 / 0.975 = 487.0 N.

**Consequence of line 170 (1).** The 25 bar cap stays, so if T1 measures the low end of the band, ENG-01's 500 N is not met. That is a requirement deviation the owner may override.

**Verdict: consistent.** The REVISION-RESPONSE wording "the lead chooses" is superseded (R2-09).

### 2h. Latency

**Consistent.**
- Purged worst-case E0→E2 is 0.626 s against the 0.81 s plan.
- The liquid line is 0.499 s.
- Both are consistent with the pocket shifts.
- P_abort 0.242 / 1.0 match the JSON.

**JSON labels are correct:** `E0_E2_all_s` versus `E0_E2_given_light_quantiles_5pct_s`.

**Report Table 2.15 is not.** It prints the PURGE NOT RUN values (1.12–1.32 s, beyond the 0.81 s deadline) under a caption saying that a light requires E1→E2 ≤ W (R2-08).

### 2i. T1–T4 regression specification

**The signature at T1 is small.** At 100 % thrust (O/F 10.4), the total-flux signature r(0.97)/r(0.10) = [(1 + 0.97/OF)/(1 + 0.10/OF)]^n is:
- 1.028 for n 0.35;
- 1.041 for n 0.5;
- 1.056 for n 0.68.

The specification's 1.08–1.12 applies at O/F 4–6, which means deep throttle only.

**Station.** x/L 0.97 is 6.9 mm from the aft face, less than one port diameter.
- It is the right station for the gate's a_meas, because that is where burn-through happens.
- It is the wrong place for the only aft station of the law decision: post-chamber recirculation and radiation can mimic or mask a 3–6 % signature.

**Decision rule.** The "2σ on two firings" rule sets no required σ. The listed uncertainty terms (gauge, station position, burn time, flux history) leave out the dominant systematics:
- post-shutdown melt and soak-back;
- the melt/char layer and ovality at the measured surface;
- print density along the grain;
- start and tail-off transients.

**"Errs safe whichever law holds."**
- Plausible for the web gate: a_meas at the aft station includes the aft enhancement for the T1–T4 flux history.
- Not demonstrated for B1 phases at lower O/F than the calibration firings. The aft enhancement is 1.04 at O/F 10.4 but 1.08 at O/F 5 (n 0.5).
- Non-detection, the expected outcome at T1's O/F, keeps the less safe gate.

See R2-04.

### 2j. igniter.sequence and the abort matrix against lines 160, 164, 166 and 168

**Consistent.**
- PURGE at E0 − 2.90 s (start[0].t_s −2.9).
- ECU cap of 2.5 s flow plus measured valve times (start[0]).
- A5 deleted and replaced by LIGHT_SPIKE (abort_if_no_ignition[3], start[5], abort_matrix_v2p4.A5).
- E1 2oo2 (start[3], fa1_supervision).
- Torch supervision from E1 to E2, A16 (start[3], abort_matrix_v2p4.A16).
- BLEED_FAULT log-only, with a pad go/no-go (abort_matrix_v2p4.A14).
- Drogue predicate as restated in line 168 (drogue_release_hold.v.lead_predicate_line168).

**Still "raw", or contradicting a lead line.**
- `abort_matrix_v2p4.v.A4`: "Pc > 30 bar raw for 5 ms". "Filtered" occurs nowhere in combustion.json for the 30 bar abort.
- `abort_matrix_v2p4.v.A14`: "closure not confirmed by E0 − 0.05 s". This contradicts line 166 (3).
- `igniter.sequence.v.start[0]`: "closure confirmed before E1 or BLEED_FAULT … (relight proceeds)". It does not command V2 closed and has no stand abort.
- `igniter.sequence.v.start[3]`: E1 is defined without the closure-or-deadline term.
- `igniter.sequence.v.arm_preconditions[0]`: "tank 15-25 C (ENG-12)". ENG-12 has been amended to 15–24 C.
- `igniter.sequence.v.abort_if_no_ignition[1]`: "wait >= 5 s".
- `igniter.sequence.tag`: "CHANGELOG 153-164", although parts of 166 and 168 are folded in.
- `igniter.model_transients`: 90 % at 0.28–0.29 s, which contradicts §7.7.

See R2-01, R2-02 and R2-05.

## 5. New findings

### R2-01 (MAJOR): the sequence and abort text does not implement lead line 166 (3)/(4)

**Gates:** SIL/HIL freeze; IGN-1 (E1 definition); CF-4 (P6); A1.

**Evidence.**

*A4 channel.*
- Line 166 (4) puts the 30 bar firmware abort on the FILTERED channel with 5 ms persistence. It amends the word "raw" in line 160 (2).
- REQUIREMENTS l.115 repeats this: "filtered channel, 5 ms".
- The REPORT still says raw at:
  - l.22 (§0);
  - l.1765 (A4 row);
  - l.2035 (H11);
  - l.2087 (FA-1 detection);
  - l.2265 (OI-18);
  - l.1866, which records line 160 and needs an amendment note.
- The JSON says raw in `abort_matrix_v2p4.v.A4`.

*E1 closure term.* Line 166 (3) defines E1 as torch confirmed (2oo2) AND [closure confirmed OR closure deadline reached], with the deadline ≤ the torch gate.
- At the deadline in flight, the lift proceeds, BLEED_FAULT goes to the FC, and V2 is commanded closed.
- On the stand it remains an abort.
- The REPORT carries only the line-160 wording ("before E1") in the E1 row (l.1638), the A14 row (l.1775) and the PURGE text (l.1695).
- The JSON start[0] and start[3] do the same.

*Three different deadlines.*

| Source | Deadline |
|---|---|
| JSON A14 | "by E0 − 0.05 s" (this is the flow-end time, not a confirmation deadline) |
| JSON start[0] and REPORT | "before E1" |
| Lead line 166 (3) | ≤ torch gate (0.16 s) |
| electronics.json v2 | E0 + 0.15 s, consistent with the lead |

Combustion is the odd one out.

*Configuration statements.* §0 Configuration (l.34) says the lead decisions are folded in "to CHANGELOG line 164". The handback (line 169) says "to 168". In fact 166 (1) and 168 are folded in; 166 (3) and (4) are not.

**Required action.**
1. Replace "raw" with "filtered, 5 ms (LEAD line 166 (4))" in all six report places and in A4. Keep l.1866 as the record of line 160, with an amendment note.
2. Write E1 and A14 exactly as line 166 (3), including "V2 commanded closed" and the stand abort. Align CF-4 P6.
3. Correct the §0 configuration line and the igniter.sequence tag.

### R2-02 (MAJOR): two incompatible stand safing rules after a no-light

**Gates:** first static fire (T1); every later stand no-light.

**Evidence.**
- §7.6 (l.1903) withdraws the v2.3 rule "wait >= 5 s". The basis: wall conduction alone needs 5–27 s for 6.5–15 g of liquid.
- The §7.6 replacement:
  1. N2 purge ≥ 60 s at ≥ 10 g/s;
  2. hold ≥ 15 min before approach, with Pc at ambient and the head thermocouples falling;
  3. then safing.
- The old rule is still live in three places:
  - H9 (l.2033): "Ground: >= 5 s wait, N2 purge, safing";
  - §10.2 (l.2161): "wait >= 5 s; N2 purge";
  - `igniter.sequence.v.abort_if_no_ignition[1]`: "ground: wait >= 5 s".
- These texts govern when people approach the stand.

**Required action.** Use one rule, the §7.6 rule, in all four places, and cite it from the test plan.

### R2-03 (MAJOR): the FA-1 pulse specification is one point at an ASSUMED fuel fraction

**Gates:** Mechanical FA-1 pulse check (the load must be fixed before the check is run); IGN-1; A1 flight acceptance.

**Evidence** (§4 2b; r2_late_light.json and r2_late_light_init005.json).
- **What was specified.** Line 164 (8) asks Mechanical for a "≤ 3 ms, 75.5 bar abs head-pulse check". These are the grid maxima at O/F 8 with tf ∈ {1, 5, 10} ms. At O/F 8 they reproduce within my bracket (71.2–78.6 bar, 2.5–3.5 ms).
- **O/F is not bounded.**
  - The closed-volume UV pressure of the fast part is 74.0, 81.4, 86.0 and 89.3 bar at O/F 8, 6, 5 and 4.
  - At tf 1 ms the vented peaks are 76–84 bar (vapour once) and 84–88 bar (as written).
  - Time above MEOP reaches 3.6 / 4.6 ms; time above proof reaches 0.96 / 1.36 ms.
- **Duration.** It is non-monotonic in tf and peaks between the author's grid points.
- **Aft end.** The aft node carries 96–97 % of the head peak, but the J1 316L lip check was set at 63.1 bar (line 145).
- **Missing datum.** The fuel-vapour inventory at the moment of light (after an 18.67 s coast, warm 32.2 mm port).
- **Consequence.**
  - The peak governs the shell (§4 2b).
  - The envelope lies between ENG-09's yield design point (67.5 bar) and ultimate design point (90 bar).
  - Whether parts yield, or approach ultimate, depends on the as-designed margins, which only Mechanical can state.

**Required action.**
1. Combustion either:
   - (a) bounds the fuel-vapour inventory at light from the coast thermal state; or
   - (b) publishes an FA-1 envelope covering O/F 4–12, tf 1–7 ms in 1 ms steps, t_res 0.02 / 0.06, and pool none / q 2.

   The envelope is a family of pressure histories with, for each: head and aft peak, rise time, time above 45 and 67.5 bar, and impulse. Only the O/F × tf loop needs adding to the existing script.
2. The lead restates the pulse-check load as an envelope:
   - quasi-static at the envelope peak for the shell, closures, bolts and J1 lip;
   - DLF or impulse for parts with periods of 1–5 ms.
3. The FMEA records the consequence as "yield possible; ultimate margin not demonstrated" until Mechanical reports the capacities.

### R2-04 (MAJOR): the T1–T4 law decision cannot resolve the signature, and non-detection defaults to the less safe gate

**Gates:** T1–T4 reduction; B1. REQUIREMENTS l.117 adopts x/L 0.97.

**Evidence.**
- §4 2i; specification l.9, 15, 16, 17 and 20 (duplicated in REPORT l.2199–2201).
- The signature at T1's O/F 10.4 is only 1.03–1.06.
- No σ target is set, and the dominant systematic terms are missing.
- x/L 0.97 sits inside the aft-end region.
- Line 168 (6) applies the stricter rule ("OR a_meas ≥ 1.25 → change the grain") only "if T1–T4 show the total-flux law". If the true law is total-flux but it goes undetected, REV-GNC-2's 11 of 483 runs below 1 mm of web remain.

**Required action.**
1. Reverse the burden of proof: apply the line 168 (6) rule unless the oxidiser-flux law is positively shown at the required σ.
2. For the law decision, add aft stations at x/L 0.80–0.90. Keep a_meas at 0.97 for the gate.
3. State the required σ of the ratio (about ≤ 1.5 % to resolve n 0.5 at O/F 10) and the repeat measurements that reach it.
4. Add the missing systematic terms.
5. Demonstrate "errs safe" against the B1 cycles' O/F history, including the low-O/F phases.

### R2-05 (MINOR): superseded values still live in combustion.json v2.4; relief specification absent

**Gates:** next interface publication, before the GNC re-fly freeze and the ENG-06 freeze; CF-3 for the relief.

**Evidence** (r2_superseded_scan, r2_json_scan). All 2600 v2.3 keys are kept, which is right for compatibility. But values that the author's own superseded_v2p4 list withdraws are still live without a SUPERSEDED tag:
- `thermal_and_loads.flights_per_insert_A1` = [1.0, 4.3], tagged DERIVED.
- `operating_points.pressure_limits.full_stroke_failure_S230_max_bar` = 42.85, and `...full_stroke_failure_S230.v[11].Pc_bar` = 42.85.
- `…seat_and_seal_review_v2p3.v.b_seat.leak_tightness` gives 0.039 g/s (from 8.74 g).

Other stale values:
- `valves_and_actuators.priming_rule.v[1]`: "valve left open". MV is closed in coasts.
- `isolation_valve.trapped_liquid_relief`: "≤ 7.5 MPa" (v1). This is now superseded by the back-relief check and the 9.5 MPa disc; the tank relief is 6.9 MPa and MAWP 8.42 MPa.
- `igniter.model_transients`: 0.28–0.29 s.
- `open_interface_issues[5]`: 0–69 bar.
- `decisions.tank_pressurisation` and arm_preconditions[0]: 15–25 C. The same range appears in REPORT §2.1–2.3 and H4.

No v2.4 key gives relief set points or MAWP. RC-04's closure criterion is therefore unmet.

**Required action.**
1. Tag or replace each stale value. Never leave a withdrawn value behind a DERIVED tag.
2. Add a `relief_v2p4` block:
   - tank set 6.9 MPa;
   - fire relieving 8.35 MPa;
   - MAWP 8.42 MPa;
   - proof 10.5 MPa;
   - back-relief check Cv ≥ 0.1;
   - disc 9.5 MPa ± 5 %.
3. For the lead: the ENG-09 text still says "trapped-liquid relief ≤ 7.5 MPa".

### R2-06 (MINOR): vented-mass statements contradict their own table; the barrier bracket; CF-4 P4

**Gates:** CF-4 (P4, P5); GNC RG-16.

**Evidence** (§9.1 l.2069–2070; cause and physics in §4 2c).

| Statement | Table says |
|---|---|
| "Before 0.5 s: m(t) lies between 8.49 t … and 31.24 t" | minimum 3.2 g at 0.5 s, below the 4.25 g lower bound |
| "the maximum is all-liquid flow from the start" | 11.9 g against 15.6 g at 0.5 s; 72.9 g against 78.1 g at 2.5 s |

**Required action.**
1. Correct both sentences.
2. State that the minimum before liquid arrival comes from the barrier-element bracket, and that its T4 stall is a model construct (bubble point about 0.7 kPa against 45.5 bar).
3. Define P4 per tap and per phase (vapour, then liquid), and name the bracket used. A real T4 will not reproduce the stall, so P4 cannot pass or fail on it.

### R2-07 (MINOR): the MEOP margin of 0.67 bar has no guard band

**Gates:** ENG-09 freeze; SIL/HIL freeze (interlock); CF-1 and CF-3.

**Evidence.**
- The margin equals about 0.9 K, or about 1.1 bar of tank pressure.
- The interlock thresholds sit exactly at 24 C and 55.28 bar abs, with no allowance for channel uncertainty.
- Two inputs are unmeasured: full-stroke Cd (ASSUMED at the top of the band, 0.80) and the hardware line loss at about 0.38 kg/s. Cd 0.85 alone adds about 1.4 bar.

**Required action.**
1. Electronics states the total channel uncertainty of T_tank and P_tank, and the thresholds are set below 24 C / 55.28 bar by that amount.
2. CF-1 and CF-3 acceptance includes full-stroke Cd ≤ 0.80 and line loss ≥ the modelled value at the failure flow. Otherwise MEOP is restated.

### R2-08 (MINOR): Table 2.15 PURGE NOT RUN rows

**Gate:** GNC RG-01 re-fly inputs.

**Evidence.**
- The caption (l.692) says a light requires E1→E2 ≤ W 0.65 s.
- Rows l.701–702 print 1.121–1.318 s. These are the JSON's `E0_E2_all_s`: all samples, not limited by W, and beyond the 0.81 s plan, where A2 aborts.

**Required action.** Label the rows "all samples, would-be (A2 aborts beyond W)" and point to `E0_E2_given_light_quantiles_5pct_s`.

### R2-09 (MINOR): text consistency after lines 145, 146 and 170

**Gates:** Mechanical FE re-run and nozzle drawing release; text.

**Evidence.**
- J1 was CONFIRMED in line 146, but:
  - §6.5 l.1564 still says "pending agreement";
  - OI-22 (l.2269) says "Agree J1 or J2";
  - the JSON key is `nozzle_joint.v.proposal_J1`.
- l.1565 makes "the lip stays at or below its present 250 C in-burn" a hot-layer requirement. Line 145 says 250 C was a goal, and J1's lip runs at 342 C.
- Segment heat input is 0.83–9.0 kJ in §2.7 (l.379) but 0.88–9.87 kJ in §6.4 (l.1542).
- REVISION-RESPONSE RC-09 says "the lead chooses"; line 170 (1) has since decided.
- OI-27 (l.2274) is already done: HANDBACK-SUMMARY l.80 was replaced.

**Required action.** Align the text with these decisions.

### R2-10 (MINOR): the Pc evidence chain cannot resolve the events it is meant to measure

**Gates:** IGN-1; T1–T3 instrumentation.

**Evidence.**
- LIGHT_SPIKE exists so that "IGN-1/T1 measure whether real lights spike" (line 160 (1)). The modelled spikes last 1–3 ms; raw time above 30 bar is ≤ 1.9 ms.
- The plan logs Pc at 1 kHz (l.2124, l.2194), and the ECU monitor runs at 1 kHz.
- The report places the 1L and Helmholtz modes at 1.1–1.8 kHz (l.1996). Logging them at 1 kHz (l.2004, l.2017) aliases them.
- REV-ELEC-1 reports sense-line overshoot in the transducer model.

**Required action.**
1. Specify the stand dynamic Pc channel (the "fast high-range channel" adopted in the A7 row): ≥ 10–20 kHz, anti-alias filter, flush mount or a characterised short sense line.
2. Label flight LIGHT_SPIKE values logged at 1 kHz as lower bounds.

### R2-11 (NOTE): late-light model form

**Double counting of the chamber vapour.** The construct counts it twice.
- In the author's constant-cv gas this adds about P0.
- In my equilibrium gas it raises the peaks by about 6 % (decomposition) and about 10 % (FA-1), because cv varies with temperature and, for FA-1, because of recombination.
- The author's values sit between my two readings, and the decomposition conclusion holds in both.

**Other model-form effects.**
- The κ fitted at 40 kg/m³ overstates the closed-volume pressure at the fast-part density (6.6 kg/m³) by about 3.7 % for O/F 8 products. This is conservative. It is exact for decomposition.
- Throat outflow uses frozen γ (c* 1511 m/s) instead of equilibrium (1569 m/s). This vents about 4 % faster and is slightly non-conservative.
- At tf 1 ms the nodes are lumped across a 230 mm port. Acoustic transit is about 0.3 ms in hot products and about 1 ms in cold vapour, so local wave peaks are not bounded.

A 1-D gas-dynamic run of the worst FA-1 row would close these.

### R2-12 (NOTE): plume HANDBACK-SUMMARY wording

- Line 74 still says "+0.5 %".
- Line 86 still says "<= 179 K".
- Line 87 says "About 0 K at the v2 point" without the stream-B bound.
- The header still cites the v2.3 interface.
- The plume report v2.2b itself is correct. This file belongs to the lead.

### R2-13 (NOTE): interface configuration for cross-checks

- mechanical.json v2 (`4f024ed4ccb4618c`, 2026-10-12 23:04) predates lines 160–166. It has no restrictor, element, rounded-entrance, MEOP or MAWP keys. Combustion's values for these can be checked only against CHANGELOG line 162 and 03-cad/calcs.
- electronics.json v2 still shows:
  - A5 OPEN;
  - BLEED_FAULT at E0 + 0.15 s;
  - the 2.0 s hold;
  - the Burkert 6027 HP (REV-ELEC-1 RE-16).

This is not a Combustion defect. It is a configuration item for the lead.

## 6. Recomputation table (reviewer vs author)

| Quantity | Author | Reviewer | Difference | Reviewer method |
|---|---|---|---|---|
| Late light 15 C, sharp / rounded [bar] | 43.74 / 40.61 | 42.09–44.50 / 38.73–41.50 | −3.8 to +1.7 % / −4.6 to +2.2 % | Equilibrium-table three-node network; vapour once / as written |
| Late light A1, sharp / rounded [bar] | 37.77 / 36.67 | 36.11–38.75 / 34.90–37.67 | −4.4 to +2.6 % / −4.8 to +2.7 % | Same |
| Decomposition, worst variant, rounded / sharp [bar] | – | 42.24 / 45.15 | – | Port exit 1.0 A_port |
| FA-1 O/F 8, tf 1, t_res 0.02, no pool [bar] | 48.9 / 49.2 | 44.7–52.0 / 45.1–52.3 | −9 to +6 % | Same |
| FA-1 O/F 8, tf 1, t_res 0.06, no pool [bar] | 70.4 / 71.9 | 65.5–73.0 / 67.3–74.6 | −7 to +4 % | Same |
| FA-1 O/F 8, tf 1, pool q 2 [bar] | 75.5 (max) | 71.2–78.6 | −6 to +4 % | Same |
| FA-1 O/F 8, time > 45 bar [ms] | ≤ 3.0 | 2.50–3.46 | – | tf 1–7 ms |
| FA-1 O/F 4–6, tf 1 ms [bar] | not computed | 76.0–88.0 | – | O/F sweep |
| FA-1 max time > 45 bar, O/F 4–12 [ms] | – | 3.60 / 4.58 | – | Vapour once / as written |
| Purge per tap, liquid / vapour [g/s] | 15.62 / 4.25 | 15.63 / 4.25 | 0 % | Dyer and HEM (CoolProp), own code |
| FD-01 deficit, flashing / incompressible | ≤ 2.2 % | 2.17 % / 1.50 % | agree | Four readings |
| Needed time with element [s] | ≤ 1.94 | 1.94 | agree | 1.9 / 0.978 |
| Vented-mass minimum at 0.5 / 1.0 s [g] | 3.2 / 5.9 | 3.17 / 5.93 | agree; cause traced | Own raw-record streamer |
| Capillary bubble point, 15 µm | – | 0.70 kPa (ΔP 4547 kPa) | – | CoolProp σ, 4σ/d |
| Decomposition energy, gas / liquid at 20 C [MJ/kg] | 1.854 / 1.603 | 1.854 / 1.599 | 0 / −0.3 % | Cantera + CoolProp |
| Flight tank, decomposition [kg TNT / m] | 0.774 / 16.4 | 0.772 / 16.4 | −0.3 % | Same |
| Flight tank expansion, 20 / 35 C [kg TNT] | 0.030 / 0.040 | 0.0303 / 0.0380 | +1 / −5 % | Isentropic, CoolProp |
| A1 residual expansion, 20 C [kg TNT / m] | 0.014 / 4.3 | 0.0141 / 4.33 | agree | Same |
| MEOP closure rows [bar] | 45.01 / 46.27 / 44.26 / 43.96 | 44.62 / 45.87 / 43.84 / 43.27 | −0.9 to −1.6 % | RocketCEA c*_eq, η 0.96 |
| MEOP margin in tank terms | 0.67 bar | ≈ 0.9 K ≈ 1.1 bar | – | Table 3.8 slope |
| OI-28: Pc at η_cf 0.95 / thrust at 25 bar | 25.63–25.7 bar / 487 N | 25.67 bar / 487.0 N | agree | Scaling |
| T1–T4 signature at O/F 10.4, n 0.35–0.68 | 1.08–1.12 (stated for O/F 4–6) | 1.028–1.056 | – | Total-flux law at x/L 0.97 / 0.10 |
| v2.3 keys kept in v2.4 | 2600 | 2600 of 2600 | – | Key-path diff |

## 7. Plume v2.2b against RC-10, RC-11 and RC-19

**RC-10: CLOSED.**
- l.13: "grid-insensitive within +/-0.15 %, with no observed convergence … R = 1.09 … GCI undefined … 3x deviation bound".
- Fine-level dependence flagged (l.13, l.48).
- Mach-disk p 11.4 marked "degenerate".
- Far-field GCIs "withdrawn" (Table 8.2).
- Future method stated (l.322).

**RC-11: CLOSED.**
- l.8: "the Lewis-Carlson value, 2.66 De, lies inside the CFD band 2.58-2.77 De".
- "about 1 %" for the 1-D thrust comparison.
- The v1 operating point is named (l.13).

**RC-19: CLOSED.**
- (a) `_raw` renders kept out of publishable sets (l.163).
- (b) 172–182 K with f_ext 181.8 K.
- (c) Stream-B bound beside it: plume maximum 2705 → 3011 K at the v2 point.
- (d) and (e) disclosed.

**Residual.** Wording in the lead's HANDBACK-SUMMARY (R2-12). No re-run was needed, and none was made.

**05-plume-cfd v2.2b: ACCEPT.**

## 8. Interface consistency

**combustion.json v2.4 against the REQUIREMENTS amendments.**

| Item | Status |
|---|---|
| ENG-12, 15–24 C | violated (R2-05) |
| 30 bar abort filtered / 5 ms (line 166) | violated (R2-01) |
| E1 2oo2 AND closure-or-deadline | only partly present (R2-01) |
| ENG-09 interlock | present |
| Drogue predicate, line 168 | present |
| BLEED_FAULT log-only | present |
| Rounded entrance | present |
| PURGE and ECU cap | present |
| ENG-01 at the cap; x/L 0.97 (l.117) | present (R2-04 applies to x/L 0.97) |

**Against other interfaces.**
- electronics.json v2: its BLEED_FAULT at E0 + 0.15 s matches line 166 (3); Combustion's "E0 − 0.05 s" and "before E1" do not. Its stale points are listed in R2-13.
- mechanical.json v2: cannot be cross-checked; it predates the decisions (R2-13).

**superseded_v2p4 list (11 entries).**
- 3 of the withdrawn values remain live in 4 v2.3 keys:
  - 0.039 g/s;
  - 42.85 bar (two keys);
  - [1.0, 4.3] flights per insert (R2-05).
- The remaining entries appear only as explicit supersession records or trade-history rows: 44.9 bar, about 50 g, 0.8 mm per tap, E0 − 2.40 s, A5, 2.5 + 0.3 s, 15.91 cm³. I did not scan for the PTFE lining.

**Other checks.**
- v2.3 key retention: 2600 of 2600.
- RC-20 tags: present.

## 9. What remains undemonstrated

1. **The FA-1 and late-light numbers are simulations on an ASSUMED construct.** Every number rests on assumed values: fast-part definition, t_res, tf, f_ret, q and fuel fraction, all on lumped nodes. There is no measurement. FA-1 is controlled by the fuel-vapour inventory at an A1 relight, which is unknown.
2. **Structural capacity under the FA-1 pulse.** Shell, closures, bolts and J1 lip remain unknown until Mechanical runs its check on an envelope.
3. **Purge P_abort, the 1.9 s needed time and the slip brackets.** These rest on the queue model and an ASSUMED Cd of 0.70. CF-4 (≥ 5 runs per state and attitude) gives the first evidence.
4. **FD-01 element.** Its real ΔP law, rating condition and loading over life.
5. **MEOP basis inputs.** Full-stroke Cd, line loss at the failure flow, and interlock channel accuracy.
6. **Regression law form and a.** These depend on T1–T4, whose resolving power is still to be specified (R2-04).
7. **Stored-energy distances and relief sizing.** These depend on "as recalled" constants.
8. **Electronics implementation.** A4 on the filtered channel, the E1 closure term, A16, LIGHT_SPIKE and the hardware purge window (REV-ELEC-1 still open).
9. **Pc acquisition bandwidth** for the spike and stability evidence (R2-10).
10. **Plume ground-plane case and far-field mixing.** These are limits stated by the author.

Matching hashes and reproduced numbers are not physical approval of any of these.

## 10. Next closure (in order)

1. **Combustion v2.4a patch** (text and interface only; no re-runs). Re-review covers only the changed lines.
   - R2-01: A4 filtered; E1 and A14 per line 166 (3); §0 and tags.
   - R2-02: one safing rule.
   - R2-05: supersede or replace the live values; add relief_v2p4.
   - R2-08 and R2-09.
2. **FA-1 envelope (R2-03).** Combustion delivers it before Mechanical's pulse check is scheduled. The lead restates the load: envelope; quasi-static peak; DLF or impulse for low-frequency parts; aft end and J1 included. The FMEA consequence is updated.
3. **T1–T4 specification revision (R2-04)**, with GNC: burden of proof, stations, σ target, systematic terms, B1 O/F history.
4. **§9.1 sentences and CF-4 P4 per tap and per phase (R2-06)**, with a note to GNC on the RG-16 minimum.
5. **Interlock guard band and CF-1 / CF-3 acceptance items (R2-07)**, with Electronics.
6. **IGN-1 and T1–T3 dynamic Pc channel specification (R2-10).**
7. **Physical gates (founders):** CF-3, then IGN-1 (≥ 30 lights, including photodiode false positives), then CF-4, then T1–T4.

## 11. Overall verdict

**02-combustion v2.4: REVISE (targeted).**
- Reproduced independently: the decomposition hard-start bound, purge flows, FD-01 deficit, stored energy, MEOP closure and OI-28 arithmetic. The response is largely honest.
- Four MAJOR findings remain:
  - the sequence and interface do not implement line 166 (3)/(4);
  - two stand safing rules coexist;
  - the FA-1 pulse load is one point at an ASSUMED fuel fraction;
  - the T1–T4 law decision defaults to the less safe gate.
- Three of the author's "Closed" statuses (RC-04, RC-06, RC-13) are not supported by the interface.
- None of this requires re-running the decomposition grid, the purge grid or the MEOP basis. The FA-1 envelope needs only an O/F × tf loop in the existing script.

**05-plume-cfd v2.2b: ACCEPT.** The RC-10, RC-11 and RC-19 wording is in place. The leftover wording in the summary file is R2-12, for the lead.
