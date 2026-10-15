# Independent review: Combustion & Propulsion (02-combustion) and Plume CFD (05-plume-cfd)

| | |
|---|---|
| Reviewer | Independent reviewer (agent), not the author |
| Date | 2026-10-12 |
| Requirements basis | `00-requirements/REQUIREMENTS.md` rev 2 (sha256/16 `88e50538159a93ed`). Rev-1 citations in the reviewed reports are judged against rev 2. They are treated as minor unless they change a conclusion (lead instruction). |
| Status | Review of digital deliverables only. Nothing in this review is MEASURED. Agreement between independent calculations, matching hashes or a correct render are not physical approval. |
| Reviewer files | `reviews/combustion/`: 12 scripts and 12 JSON outputs (§12) |

## 1. Scope and files reviewed

| File | Version | sha256/16 | Lines |
|---|---|---|---|
| `02-combustion/REPORT.md` | v2.3 | `59f69506fb5aa935` | 1108 |
| `02-combustion/HANDBACK-SUMMARY.md` | v2.3 | `efce17f348ca309e` | 131 |
| `05-plume-cfd/REPORT.md` | v2.1a / v2.2 | `7ce61efce1014e9f` | 321 |
| `interfaces/combustion.json` | v2.3 | **`d9ec54fbf450e243`** | 5966 |
| `05-plume-cfd/validation/results/validation_v2.json` | v2.1a | `cbfbce89c41689f3` | – |
| `05-plume-cfd/validation/results/afterburn_grid_time_v2.json` | v2.2 | `847fb22352cdca20` | – |
| `02-combustion/data/v2/erosion_S230/erosion_dc_v2.json` | v2 | `72513ca3e3df86a6` | – |

Also read, only to see which method and inputs the author used:
- `02-combustion/src/` (`grain_q1d.py`, `actuator_rate_check.py`, `nozzle.py`, `erosion_dc.py`, `heat.py`, `m1_design.py`).
- `data/v2/feed_line_checks_v2.json`, `data/v2/actuator_rate_check_v2.json`.
- `05-plume-cfd/ownruns/*/run.json`, `openfoam_cases/*/0/U` and `case_meta.json`.
- The render and synthetic-photo PNGs.

Context, where lead lines govern:
- `interfaces/gnc.json` v2 (`7089d7b34808cc31`)
- `interfaces/mechanical.json` v2 (`4f024ed4ccb4618c`)
- `interfaces/electronics.json` v1 (`42fe12e15baa6e3e`)
- `interfaces/CHANGELOG.md` (53 lines, `90945b8fb75711db`, up to and including the provisional hose-routing decision)
- `00-requirements/TEAM-CHARTER.md` (`9b5e35a774ac4b3e`)
- `01-systems-gnc/duty_cycles/*_v1.csv` and `*_v2.csv`

## 2. Method

- **Independence.** Every check uses the reviewer's own scripts. The author's code was read only to identify methods and inputs; the author's results are used only as comparison values.
- **Fuel card.** The ABS card was rebuilt from the stated molar composition: A/B/S 0.24/0.185/0.575, giving C6.06 H6.43 N0.24 at 82.63 g/mol. It uses the author's design hf of 476.4 kJ/kg.
- **Tools.** `/opt/engine-venv/bin/python -I` with RocketCEA 1.2.3, Cantera 3.2.0 (GRI-3.0), CoolProp 8.0.0 and SciPy, run on one core under `nice`.
- **CFD.** Not re-run. The run logs, `run.json` files and result JSON were read.
- **Missing data.** Where a check needs data that do not exist, it is stated and classed as open. This applies to all test data, the B1 85 m profile, gnc.json v3, ignition delay, the reaction time of pooled N2O and fragment data.

| Script | Checks | sha256/16 |
|---|---|---|
| `rc01_cea.py` | CEA shifting and frozen, plus Cantera HP equilibrium and nozzle integration, at O/F 8.9, 10.4 and 10.435; hf sensitivity | `c557e2241aed4b74` |
| `rc02_sizing.py` | Dt, De and mdot for 500 N at sea level with eta_c* 0.92 and eta_cf 0.975 | `c620841209ded91c` |
| `rc03_injector.py` | Pintle area law. Dyer NHNE with the HEM term evaluated at P2 and at its choked maximum. HEM and SPI bounds, full-stroke failure, cold flow at the ignition lifts | `4c21c6a39f9123d9` |
| `rc03b_meop_corner.py` | MEOP basis across line-loss law, eta_c* and tank temperature | `65c6b35d45f9dea8` |
| `rc04_bartz.py` | Bartz throat flux for 4 property sets and 3 throat curvature radii | `3f27e46e0f388e8b` |
| `rc05_grain.py` | L* from the published contour. 0-D grain over the gnc v2 duty cycles with my own CEA map; a and n bands | `ed8c731c7961fc98` |
| `rc06_separation.py` | Summerfield and Schmucker at the Table 4.2 points and for an eroded throat | `23ad7e6389160f2a` |
| `rc07_plume.py` | Lewis-Carlson, fully expanded jet, Prandtl-Pack/Tam, Harper-Bourne & Fisher | `4a8de03db6e8b770` |
| `rc08_erosion.py` | Diffusion-limited ceiling, NSC O2 kinetics, and the author's literature-scaled method applied to my own v1 and v2 histories | `fb35bba62e1e35fc` |
| `rc09_safety.py` | Table 2.7 compression; hard-start inventory and constant-volume bound; stored energy; trapped liquid; residual tank | `52813f4cf5663eac` |
| `rc10_gci.py` | Convergence ratio and GCI from the three-level data; implied nozzle efficiency; Pc for 500 N against eta_cf | `6b9a29bc938ce50a` |
| `rc11_scan.py` | Text scan for MEASURED, prices, TO-QUOTE, Sønderborg, AS RECALLED and untagged JSON values | `6ebad84dd15b9924` |

## 3. Recomputation (reviewer against author)

| # | Item | Reviewer | Author | Diff | Verdict |
|---|---|---|---|---|---|
| 1 | CEA shifting, Pc 25.01 bar, O/F 10.435, eps 2: c*, Tc, gamma_ch, MW, Isp_vac, Isp_SL | 1522.8 m/s, 3257 K, 1.1467, 28.72, 228.1 s, 215.6 s (Cantera HP c* 1523.7) | 1522.8, 3257, 1.1467, 28.72, –, 215.6 | <= 0.03 % | Confirmed |
| 2 | Same point, delivered (eta_c* 0.92; T0 = eta_c*^2 Tc; eta_cf applied to Cf_vac) | c* 1401.0, T0 2757 K, Isp_SL 193.1 s | 1401, 2757, 193.1 | 0.0 % | Confirmed |
| 3 | CEA at O/F 10.4 (the brief's point) | c* 1523.4, Tc 3259, gamma 1.1466, Isp_SL 215.6; delivered 1401.5 / 2758 / 193.1 | Design point is 10.435 | – | Consistent |
| 4 | CEA at O/F 8.9 | c* 1549.6, Tc 3320, gamma 1.1448, Isp_SL 219.5; delivered 1425.6 / 2810 / 196.6 | Tables give about 1549.8 / 3320 / 219.5 | <= 0.02 % | Confirmed |
| 5 | hf sensitivity (lower-hf card) | -0.2 % on c* | +/-0.3 % | – | Confirmed |
| 6 | Dt / De for 500 N at sea level, 25.01 bar | 13.724 / 19.409 mm; mdot 0.2641 kg/s | 13.724 / 19.409 | 0.00 % (+0.02 % at 25.00 bar) | Confirmed |
| 7 | Pintle mdot at 1.916 mm, 20 C, Pc 25.01 bar. Dyer NHNE with HEM at its choked maximum (36.2 bar), Cd 0.70, line loss 270.4 kPa | 0.2412 kg/s (0.2429 with a flow-scaled line loss). Bounds: HEM 0.1595 (0.69x), SPI 0.3277 (1.42x). With HEM evaluated at Pc instead: 0.2308 | 0.24099; HEM 0.64-0.68x, SPI 1.34-1.37x | +0.10 % (+0.8 %) | Confirmed |
| 8 | Stuck full-stroke pintle, author's line law, 30 C, Cd 0.8 | 42.4 bar | 42.85 | -1.0 % | Confirmed; basis is not conservative (RC-08) |
| 9 | Bartz throat flux, author's method: mean Rc 0.941 Rt, frozen CEA properties, T0 2757 K, Tw 600 K | 21.92 MW/m2 (h_g 10 259 W/m2K, T_aw 2737 K) | 21.92 | 0.0 % | Confirmed |
| 10 | Bartz sensitivity | Rc band 20.2-24.0; Cantera delivered properties 21.16; ideal gas state 26.0-28.4 | Stated band x0.7-1.3 (15.3-28.5) | Inside band | Confirmed |
| 11 | L* (free volume from the published contour, initial port) | 2.03 m (300.9 cm3) | 1.92 m (284.6 cm3) | +5.7 % | NOTE (RC-16) |
| 12 | End web, n 0.5, gnc v2 cycles (a x0.6 / x1.0 / x1.5) | A1 10.08 / 8.10 / 5.93; A2 at x1.0 7.07; B1 x1.0 4.77 and x1.5 1.47; B2 x1.0 6.74 mm | 10.22 / 8.17 / 6.01; 7.18; 4.57 and 1.31; 6.55 | <= 0.2 mm | Confirmed |
| 13 | End web, n band not run by the author (laws re-anchored at r(300) = 1 mm/s) | B1: n 0.35 at x1.0 leaves 3.03 mm; n 0.35 at x1.5 burns through at 17.4 s. B2: n 0.35 x1.5 leaves 1.97 mm. A1: n 0.35 x1.5 leaves 5.26 mm | Not run | – | MAJOR (RC-07) |
| 14 | Separation at 12.5 %, eps 2 (Pc 4.37 bar, O/F 4.06) | pe/pa 0.485 against Schmucker 0.506: incipient separation, eps_sep 1.935 (frozen: 0.465 / 0.499, 1.89). 15 % stays attached (+10.8 % margin). Summerfield (0.4) attached throughout | 0.485 / 0.506 / 1.94 | 0 % | Confirmed |
| 15 | Separation with an eroded throat (eps 1.8, constant mass flow) | pe/pa 0.522 against 0.529: still incipient | Author held Pc constant | – | NOTE (RC-18) |
| 16 | Mach-disk location, Lewis-Carlson, pe/pa 3.20-3.24 | 2.663 De (v1 CFD gas); 2.666 (v2 CFD gas, CEA shifting); 2.680 (frozen) | CFD fine 2.676; author's LC 2.663 | +0.5 % against fine; CFD band 2.58-2.77 | Consistent; claim over-precise (RC-11) |
| 17 | First shock-cell length | Prandtl-Pack/Tam 4.78-4.82 De; Harper-Bourne & Fisher 4.03-4.06 De (constant from memory) | CFD 3.96 (first), 4.10 (mean of 3); band 3.7-4.4 | -2.4 % against HB-F | Consistent |
| 18 | Graphite throat erosion, order of magnitude | Diffusion ceiling 0.59 mm/s (B 0.172). NSC O2-only: 0.65 / 4.3 / 11 / 26 um/s at 1500 / 1800 / 2000 / 2500 K. Author's literature-scaled method on my histories: A1 v1 0.151-0.230 mm; A1 v2 0.239-0.365 mm per flight | A1 v1: nominal 0.040, conservative 0.169, literature 0.159-0.237 mm | Literature method reproduced to within -5 % | Life claim not supported (RC-06) |
| 19 | CFD grid convergence (three levels, r = 2) | mdot: R 0.55, p 0.87, GCI 0.111 %. Thrust: R 1.09, which is monotone divergence; GCI undefined | Thrust 0.152 % (labelled a 3x bound); mdot 0.111 % | – | mdot confirmed; thrust wording (RC-10) |
| 20 | Table 2.7: isentropic compression from 1.0 bar, 293 K | To 45 / 52 / 60 bar: N2 ideal 870 / 907 / 944 K, N2 CoolProp 847 / 879 / 913 K, N2O 614 / 630 / 646 K. To 63.1 and 70 bar: N2 925-950 K, N2O 652-664 K | Identical at 45-60 bar | 0 K | Confirmed |
| 21 | Decomposition energy, N2O to N2 + 1/2 O2 | 1.854 MJ/kg as gas at 298 K; 1.603 MJ/kg as saturated liquid at 20 C | 1.86 MJ/kg | -0.3 % | Confirmed; add the liquid basis |

## 4. Findings

Severity definitions used here:
- **BLOCKING:** must be closed before the deliverable can serve its stated purpose. The report's stated purpose is to be the design basis for N2O cold-flow, torch and static-fire tests.
- **MAJOR:** must be closed before the named test or requirement freeze, or the claim must be withdrawn.
- **MINOR:** correct in the next revision.
- **NOTE:** observation only.

| ID | Severity | Title | Gates |
|---|---|---|---|
| RC-01 | BLOCKING | Ignition, shutdown and abort logic contradicts the author's own hazard rules and the lead's fail-safe rule | IGN-1, T1, ECU (OI-8) |
| RC-02 | BLOCKING | Hard-start inventory understated; its consequence is not bounded | T1 |
| RC-03 | MAJOR | Relight latency of the adopted sequence (valve closed in coasts) not shown; ENG-04 | GNC MC, T4 |
| RC-04 | MAJOR | Trapped liquid, relief operation and post-test / post-landing safing | CF-3, T1-T4, flight |
| RC-05 | MAJOR | Stored energy, stand-off inputs and relief sizing missing | CF-3, T1 |
| RC-06 | MAJOR | Throat-insert life ("1-4 A1 flights", now in ENG-06) not supported on the v2 cycles | ENG-06 freeze, spares |
| RC-07 | MAJOR | Regression exponent band stated but not run; the B1 web corner burns through | B1, ENG-06 envelope |
| RC-08 | MINOR | MEOP basis uses a non-conservative line loss and eta_c* | ENG-09 |
| RC-09 | MINOR | eta_cf 0.975 has no viscous allowance; ENG-01 at the 25 bar cap has zero margin | ENG-01 |
| RC-10 | MINOR | CFD grid-convergence wording and method | 05 text |
| RC-11 | MINOR | Over-precise correlation claim; operating point not named in the claim | 05 text |
| RC-12 | MINOR | Relief set point above MEOP on the N2O side | ENG-09 |
| RC-13 | MINOR | Rev-1 citations and internal consistency | Text |
| RC-14 | MINOR | Oxygen cleaning and cold-flow procedure details | CF-1 to CF-3 |
| RC-15 | MINOR | Load-bearing unverified material data | Seat and seal drawing release |
| RC-16 | NOTE | L* volume | – |
| RC-17 | NOTE | Bartz throat curvature and gas state | – |
| RC-18 | NOTE | Floor separation with an eroded throat | – |
| RC-19 | NOTE | CFD presentation details | – |
| RC-20 | NOTE | Interface hygiene | – |

### RC-01 (BLOCKING): ignition, shutdown and abort logic

**Evidence.**

1. **N2O-only flow through a hot torch.**
   - The start sequence closes propane at t = 0.4 s and the N2O torch solenoid at t = 0.6 s (`REPORT.md:912`; `combustion.json` `igniter.sequence.v.start[8]` and `[9]`).
   - The same report forbids this. It says "no N2O purge through the torch during the main burn" (`REPORT.md:935`) and "No N2O purge through a hot torch" (H1, `REPORT.md:985`).
   - The JSON gives the reason: "a hot N2O-filled cavity is a decomposition site" (`flashback_and_backflow[2]`).
   - At the 20 % ignition lift, main Pc passes 5 bar at 0.218-0.232 s (`actuator_rate_check_v2.json`, start traces). That is close to the propane supply pressure (6.4 bar at 10 C, `start[8]`). Propane flow will therefore fall off before 0.4 s, so the N2O-only interval can begin near 0.22 s.
2. **Fixed-time propane cut.** The rule "propane closed before Pc exceeds 5 bar" is implemented as a fixed time (0.4 s). It is violated at the 20 % lift, where Pc is 5.0 bar at 0.22 s and 5.4 bar at 0.35 s (same file).
3. **Ungated N2O admission.** Torch-flame confirmation at t = 0.10 s does not gate the pintle step at t = 0.12 s, and the JSON allows "fallback = timing only" (`start[4]`). With no torch flame, the sequence admits N2O into a chamber that has no ignition source. The abort or retry that follows is the hard-start path (RC-02).
4. **Hot dead-ended torch N2O line.**
   - The torch N2O line is dead-ended at the torch-inlet check valve while "the torch body sees Pc and soak heat" (`flashback_and_backflow[1]`). That is the same hot-N2O-cavity mechanism.
   - No temperature limit is set.
   - The T1 thermocouple list (`REPORT.md:1011`) has no torch or check-valve channel; IGN-1 measures only the torch body.
5. **Undefined abort actions.**
   - No action is defined for the ECU over-pressure abort at about 30 bar (ENG-09, H11) or for PINTLE_FAULT (ENG-13).
   - The only shutdown path closes the NC valve "after the pintle seats (<= 0.15 s)" (`REPORT.md:923`; `shutdown[1]`).
   - The lead's rule is that the NC valve is the fail-safe shutoff and closes when de-energised (CHANGELOG; ENG-16). With a jammed or runaway pintle, a valve closure that waits for the pintle to seat never comes.
6. **In-flight no-light rule cannot work.**
   - The report says "wait >= 5 s ... one automatic retry in flight only if the GNC margin permits" (`REPORT.md:914-917`).
   - A1 relights at 36.5-37.3 m and descends at 21.3-21.6 m/s (`gnc.json` `flight_profile`), which is about 1.7 s from impact.
   - This is a ground rule written as a flight rule.

**Impact.** OI-8 asks Electronics to implement this sequence. As written, it would encode three hazards: an oxidiser-only hot-torch interval, an ungated N2O admission, and a fail-safe path that depends on the part that has failed. These are the most credible initiators of decomposition or a hard start in IGN-1 and T1.

**Fix.**
- **Torch valves.**
  - Close both torch valves on the Pc-confirmation event, not on a clock.
  - Close N2O first or both together; choose which by IGN-1.
  - Never allow N2O-only flow through a hot torch. If an N2O sweep is kept, justify it with torch-wall and check-valve temperatures and a flame-quench or arrestor check of the 1/8 in line at tank pressure.
- **Flame-confirmation gate.** Make torch-flame confirmation a hard gate for the pintle step in flight. Allow timing-only operation for ground tests only, with a documented reduced inventory.
- **Abort matrix.**
  - Add a matrix of trigger, action and time covering over-pressure, PINTLE_FAULT, no-light, Pc-sensor fault and link loss.
  - Every abort de-energises the NC valve immediately and commands the pintle closed in parallel.
  - Normal shutdown keeps the order pintle-then-valve, with a timeout on seat confirmation.
- **Torch N2O line.** Provide a thermal stand-off with a measured temperature limit at the check valve, or vent the line after use. Add thermocouples in IGN-1 and T1.
- **In-flight no-light policy.** Agree it with GNC and the lead (immediate retry or accept the loss), separately from the ground rule.

**Closure criterion.** §7.3 and `igniter.sequence` v2.4 are consistent with ENG-04, -05, -09, -13 and -16, and have been reviewed by Electronics (OI-8).

### RC-02 (BLOCKING): hard start

**Evidence.**

1. **Inventory covers one lift only.** The quoted inventory of 8.74 g (`REPORT.md:919`, H9 at `:993`, coast leak ceiling at `:501`) is mdot_cold 0.038 kg/s x 0.23 s at the 12.5 % lift only (`actuator_rate_check.py`). The sequence allows ignition lifts of 12.5-20 % (`REPORT.md:909`).
2. **Reviewer inventory.**
   - Dyer cold flow into 1.5 bar is 36.5 g/s at 0.207 mm and 52.8 g/s at 0.301 mm. Over 0.12-0.35 s that admits 8.4 g and 12.1 g.
   - Including the closing time of 0.05-0.15 s, the inventory is about 15 g.
   - Flash quality into 1.0-1.5 bar is 0.55-0.57, so about 45 % stays liquid at -81 to -88 C.
3. **Constant-volume bound.** Cantera UV equilibrium in 285-301 cm3 with 1 bar of air gives:
   - 165-207 bar for 8.74 g
   - 229-287 bar for 12.1 g
   - 283-354 bar for 15 g

   MEOP is 45 bar and proof is 67.5 bar.
4. **Vented estimate.**
   - The gas vent time constant through the throat is 3.8-4.7 ms.
   - A quasi-steady estimate, P ≈ (m/tau_r)·c*/At with c* ≈ 1130 m/s for decomposition products, gives this: 12.1 g exceeds MEOP if it reacts in less than about 20 ms, and exceeds proof if it reacts in less than about 13 ms.
   - Reaction with the grain raises these figures. The reaction time of a pooled cryogenic liquid is unknown.
5. **Wait time and orientation.** Evaporating 12 g of pooled liquid needs about 4.5 kJ, and no calculation supports "wait >= 5 s". Stand orientation is not specified; a horizontal chamber can hold about 20 cm3 of liquid below the throat lip.
6. **Thin check margin at 12.5 %.** At the 12.5 % lift, the model gives 3.71-3.73 bar at the 0.35 s check against the 3.0 bar threshold, and that is with zero main ignition delay (settled Pc 4.33 bar). A lower lift reduces inventory but raises the risk of false aborts. The report does not present this trade.

**Impact.** The first static fire is the most likely hard-start event. A bound 2.5-5x above proof is not closed by stating an inventory.

**Fix.**
- Tabulate inventory against ignition lift and check time.
- Add a vented 0-D chamber estimate of peak Pc against reaction time.
- Choose the lift and check time so the credible case stays below proof, and record the margin.
- Specify vertical, nozzle-down firing for IGN-1 and T1-T4, or a drain or purge.
- Justify the wait after a no-light with evaporation, venting and N2 purge.
- Recompute the coast leak ceiling.
- For T1, use a proof-tested chamber and remote operation, and add a burst disc or blow-out on the stand side if the bound requires it.

**Closure criterion.** A written bound and the chosen lift and check time appear in REPORT v2.4 and combustion.json.

### RC-03 (MAJOR): relight latency with the NC valve closed in coasts

**Evidence.**

1. **Interface text contradicts the rule.** The lead rule closes the NC valve during coasts (CHANGELOG pintle v2.3, rule iii; REQUIREMENTS rev 2 §1 step 6 and ENG-05). `combustion.json` `igniter.sequence.v.relight[0]` still says "same as start from t = 0 (the isolation valve may stay open between burns in flight)". This is the known mismatch acknowledged at `REPORT.md:927-930`.
2. **Relight needs the valve step.** Under the rule, relight needs the t = -0.3 s valve step (`start[1]`). Electronics' NC valve is cocked open by a servo in about 0.3 s per opening (`electronics.json` `actuators.main_valve`).
3. **Quoted model is not the adopted sequence.** The quoted model transients ("relights reach 90 % at 0.28-0.29 s", `REPORT.md:941-944`) assume three things that differ from the adopted sequence:
   - a 0.10 s torch-to-main delay with instantaneous main ignition;
   - a direct step to the commanded lift;
   - no ignition-lift hold, no 0.35 s check and no valve step.
4. **Reviewer estimate (arithmetic, not a simulation).** Inputs:
   - Pc confirmation at 0.22-0.35 s.
   - A ramp of 1000-2500 N/s from 62-100 N up to 90 % of the 200-300 N relight command in the gnc A1 v2 duty cycle.
   - A lag of about 0.03 s.

   This gives t90 of about 0.3-0.6 s from the torch command and about 0.6-0.9 s from the valve command.
5. **Requirement.** ENG-04 requires <= 0.5 s (target 0.3 s). Flight software plans on 0.6 s; the GNC Monte Carlo draws latency from U(0.2, 0.6) s and gets P 0.984. A start straight to 12.5 % already takes 0.52-0.53 s.

**Impact.** P(landing) 0.994 rests on a latency distribution that the adopted sequence may not meet. A later relight costs height and propellant: in the gnc latency sweep, a mean of 0.8 s puts the relight at 31.6-37.5 m.

**Fix.**
- Simulate the adopted sequence: valve step, lift hold, confirmation-gated ramp, an ignition-delay band (for example 0.05-0.3 s), and both a primed line and a line partly filled with vapour.
- Publish the resulting latency distribution in combustion.json.
- Define which command epoch ENG-04 counts from, and whether flight software pre-opens the valve.
- Correct `relight[0]`.
- GNC re-runs the Monte Carlo with the new distribution.

**Closure criterion.** The distribution is published, the Monte Carlo has been re-run, and the lead states ENG-04 status.

### RC-04 (MAJOR): trapped liquid, relief operation, post-operation safing

**Evidence.**

1. **Relief basis undefined.** H3 (`REPORT.md:987`) and `REPORT.md:324` say "relief <= 7.5 MPa" without a set basis, destination or capacity. `combustion.json` `shutdown[2]` says "relieved to the tank side". The isolation-valve MEOP is 7.0 MPa (RC-12).
2. **The relief will lift within a few kelvin (reviewer, CoolProp).**
   - For liquid N2O, (dP/dT) at constant density is 0.38-0.53 MPa/K.
   - A liquid-full segment filled at 15-25 C reaches 7.5 MPa after warming by only 4.5-5.5 K.
3. **Heating beyond that drives the pressure far past the set point.**
   - At constant density the pressure would be 12-18 MPa at 40 C, 20-29 MPa at 60 C, 33-45 MPa at 90 C and 59-78 MPa at 150 C.
   - Holding 7.5 MPa means expelling 60-87 % of the trapped mass.
   - For reference, the N2O critical point is 309.5 K and 7.245 MPa.
4. **Heat sources reach the segment.**
   - The head soaks to 363-424 K in flight and 488 K on the ground (§3.5, hot soak).
   - The provisional O3b hose routing (CHANGELOG line 53, pending Combustion acceptance) coils the stagnant N2O hose 3-15 mm from a case at 136-178 C. That is a heat source upstream of the injector, which H1 rules out.
   - The relief will therefore operate on every coast with the valve closed and after every landing or test.
5. **No safing after landing or test.**
   - A1 lands with about 0.61 kg of N2O (DERIVED from rev 2: 2.00 - 1.738/1.25).
   - The tank pressure rises from 5.05 MPa at 20 C to 7.12 MPa at 50 C and 7.67 MPa at 60 C; the relief lifts near 56 C.
   - There is no post-landing or post-test safing procedure, no hang-fire wait, no approach rule and no remote vent or dump. ENG-16 and charter rule 8 require a remote vent.

**Impact.**
- N2O is discharged near hot hardware.
- Vapour forms in the feed before relight. That gives a vapour-first start, a shift in metering and a hard-start risk.
- A crew may approach a pressurised, hot vehicle or stand.

**Fix.**
- **Relief.** Specify it either as differential relief back to the tank side (a check valve around the NC valve, with the cracking pressure stated) or as an external vent routed away from hot parts. Size it for the soak heating rate.
- **O3b hose.** Before accepting the routing, run a thermal check of stagnant N2O in the hose for the coast and post-landing cases.
- **Relight after soak.** Add handling for vapour in the line at relight.
- **Safing.** Add a post-landing and post-test procedure: time-out, remote vent of tank and feed, approach criteria, and handling of residual N2O.
- **Hazard list.** Update H1 and H3, and add a post-landing hazard.

**Closure criterion.** The relief specification is in combustion.json, the safing procedure is in §10, and the CHANGELOG carries Combustion's reply to the O3b request.

### RC-05 (MAJOR): stored energy, stand-off inputs, relief sizing

**Evidence.**
- **Stand-off.** H13 says "Exclusion zone set by the founders under local rules" (`REPORT.md:997`). Charter rule 8 requires "Every firing is remote, with a documented safe distance."
- **Relief sizing.** The report does not size relief capacity for a fire or heater-runaway case, and has no two-phase relief calculation.
- **Ground tank.** The ASSUMED 15 L ground tank for duty cycles C and D (`REPORT.md:640`; DC-D uses 7.0 kg of N2O) is absent from the hazard list.

Reviewer's stored-energy figures (TNT equivalent at 4.184 MJ/kg):

| Inventory | Mass | Decomposition energy | TNT equivalent |
|---|---|---|---|
| Flight load | 2.00 kg | 3.2-3.7 MJ | 0.77-0.89 kg |
| A1 residual after landing | 0.61 kg | 1.0-1.1 MJ | 0.23-0.27 kg |
| 15 L ground tank (85 % fill, 20 C) | 10.4 kg | 16.6-19.2 MJ | 4.0-4.6 kg |

Order of magnitude only: with a scaled distance from memory (about 17.9 m·kg^-1/3 for 6.9 kPa), the distances are 16-17 m for the flight load and 28-30 m for the ground tank. Fragments are not included; they usually govern, and no fragment data exist.

**Impact.** The founders have no engineering input for setting the exclusion zone, and the relief capacity is unknown.

**Fix.**
- Add a stored-energy table for each vessel and test, giving decomposition and burst energy.
- Add fragment considerations, and name and cite the standard the founders will apply.
- Size the reliefs for the flight tank and the ground tank (fire and heater-runaway cases, two-phase method).
- Add the ground tank to the hazard list.

**Closure criterion.** The table and the sizing calculation are in v2.4. The distance itself remains the founders' decision.

### RC-06 (MAJOR): throat-insert life

**Evidence.**
- **Stale cycles.** Table 5.3 (`REPORT.md:723`) uses the gnc.json v1 cycles, where the A1 burn is 5.83 s. On the v2 cycles, A1 burns 7.40 s (Table 4.3; 7.64 s in my run).
- **Omitted column.** The life rule (`REPORT.md:734`; `combustion.json` `flights_per_insert_A1` [1.0, 4.3]) quotes only two of the author's three models:
  - nominal: 1.16 % per flight;
  - conservative: 4.98 % per flight.

  It omits the author's own literature-scaled column: 0.159-0.237 mm per flight, which is 4.6-7.0 % per flight, or 0.7-1.1 flights per insert.
- **Requirement.** ENG-06 rev 2 has adopted "1-4 A1 flights per insert".

Reviewer check: I re-applied the author's literature method to my own 0-D histories. The method bins rates by O/F, scales them by (Pc/35)^0.68 and applies a 1.5 s onset. It reproduces the v1 A1 result (0.151-0.230 mm against the author's 0.159-0.237), and then gives:

| Cycle and regression factor | Recession per flight | dAt/At per flight | Flights per insert (5 % limit) |
|---|---|---|---|
| A1 v2, x1.0 | 0.239-0.365 mm | 7.1-10.9 % | 0.46-0.71 |
| A1 v2, x0.6 | – | – | 0.36-0.51 |
| A1 v2, x1.5 (O/F falls below 7) | – | – | 1.6-4.4 |
| B1 v2 | – | – | 0.48-1.03 |
| B2 v2 | – | – | 0.68-1.52 |

The v2 100 % point is oxidiser-rich (O/F 10.4, X_O2 6.5 % at the edge). That is more oxidising than the near-stoichiometric N2O/HDPE bin the anchor data come from.

**Impact.**
- A single A1 flight may exceed the 5 % replacement limit.
- The Pc-to-thrust map can shift by 7-11 % within one flight.
- eps falls toward 1.85-1.9, which increases floor separation.
- The spares count and cost are affected.

**Fix.**
- Re-run Table 5.3 on the gnc v2 cycles, and on v3 when it is published.
- Quote life as the spread across all three methods (about 0.5-4 A1 flights), and plan on the literature-anchored case until bore data from T1 and T4 exist.
- Make sure the Pc loop handles throat growth within a flight.
- A denser graphite grade, a larger insert or a coating may be proposed as a labelled research item.

**Closure criterion.** Table 5.3 and the life statement are corrected, and the lead corrects the ENG-06 text.

### RC-07 (MAJOR): regression exponent band not run

**Evidence.**
- **Band not run.** §4.1 (`REPORT.md:554-562`) states n 0.35-0.68, but only the a band (x0.6-1.5) is run, at n 0.5.
- **Web rule.** The web rule is >= 1 mm at x1.5 on every flight cycle (notes to Table 4.4). B1 v2 at x1.5 leaves 1.31 mm (author) or 1.47 mm (reviewer).
- **Reviewer runs.** With the laws re-anchored at r(300 kg/m2s) = 1.0 mm/s:

| Cycle and law | Result |
|---|---|
| B1 v2, n 0.35, a x1.0 | 3.03 mm web left |
| B1 v2, n 0.35, a x1.5 | Burns through at 17.4 s of the 19.1 s cycle |
| B2 v2, n 0.35, a x1.5 | 1.97 mm web left |
| A1 v2, n 0.35, a x1.5 | 5.26 mm web left |
| n 0.68 | Benign on all cycles |

**Impact.** B1 is the ENG-06 thermal envelope. In a plausible corner of the regression law, it can burn through to the liner.

**Fix.**
- Run the n band.
- Define the web rule over the whole (a, n) envelope.
- Show whether the 85 m cap on B1 restores the margin; the profile is not yet available to the reviewer.
- Add a liner burn-through margin.

**Closure criterion.** A table of web against (a, n) exists for B1 (85 m) and B2.

### RC-08 (MINOR): MEOP basis

**Evidence.** The Table 3.7 basis is 42.85 bar (30 C, Cd 0.8). It uses the simulation line-loss law 2.5 bar x (mdot/0.25)^2, which gives about 0.75 MPa at the failure flow. The designed hardware (Cv 3 valve plus Cv 2.2 filter) gives 117 kPa at 0.26 kg/s (Table 2.6), or about 0.36 MPa at 0.45 kg/s.

Reviewer's stuck-pintle Pc at 30 C, Cd 0.8:

| Line-loss assumption | eta_c* 0.92 | eta_c* 0.96 |
|---|---|---|
| Author's law | 42.4 bar | 43.6 bar |
| Designed hardware | 44.3 bar | 45.4 bar |
| Zero line loss | 46.0 bar | 47.1 bar |

At the 25 C conditioning limit, the maximum is 44.0 bar.

**Fix.** Either state the basis with the hardware line loss and the top of the eta band (about 47 bar), or justify 45 bar through the ARM tank-temperature interlock (<= 25 C). This is a lead decision. Proof at 67.5 bar still covers all cases.

### RC-09 (MINOR): eta_cf and the 25 bar cap

**Evidence.** Thrust from CFD divided by ideal 1-D thrust at the same Pc:

| Run | Wall model | F / F_ideal |
|---|---|---|
| Own solver, fine grid | Inviscid (slip) | 0.9755 |
| OpenFOAM | Slip | 0.962 |
| OpenFOAM SST (coarse, 1.0-1.15 ms) | No-slip | 0.9525 |

The own solver's figure equals the assumed eta_cf, leaving no room for viscous loss. Between the two OpenFOAM runs, no-slip walls cost 1.0 %.

Reviewer's Pc required for 500 N, against the 25 bar cap (ENG-01):

| eta_cf | 0.975 | 0.965 | 0.96 | 0.95 |
|---|---|---|---|---|
| Pc for 500 N | 25.01 bar | 25.27 bar | 25.40 bar | 25.67 bar |

**Fix.**
- Carry eta_cf as a band of 0.95-0.975 in the maps.
- State the Pc needed for 500 N at the low end of the band.
- The lead decides between raising the cap and accepting less thrust.
- Measure eta_cf at T1.

### RC-10 (MINOR): CFD grid-convergence wording and method

**Evidence.**
- **Thrust is not grid-converged.**
  - The report says "grid-converged to 0.15 %" (`05-plume-cfd/REPORT.md:13`; HANDBACK line 80).
  - For thrust, e21 is 0.254 N and e32 is 0.233 N, so R = 1.09. That is monotone divergence, for which GCI is undefined.
  - The 0.152 % figure is a 3x deviation bound, not a GCI. The mdot GCI of 0.111 % is confirmed.
- **Fine level is not independent.**
  - The fine level started from the medium state at 3.0 ms and ran 0.25 ms (`f_2s_100/run.json`). It is at the same physical time but does not have an independent history beyond about 8-10 De.
  - Medium and fine Mach-disk x agree to 3e-5 De, so p = 11.4 is degenerate.
  - The core-length GCI (4.2 %, p 1.06) rests on a far field inherited from the medium run.
- **Temporal bands are thin.**
  - They use 4 snapshots over 0.75 ms, for the coarse and medium levels only.
  - A 2-sigma estimate from 4 autocorrelated samples is crude.
  - The window is shorter than 2 convective times beyond 20 De.

**Fix.**
- Replace "grid-converged" with "grid-insensitive within +/-0.15 %, no observed convergence".
- Flag the fine-level dependence, and withdraw the far-field GCIs.
- In future runs, take time means over at least 3-5 ms per level, with autocorrelation-corrected errors, and apply GCI to the means.

### RC-11 (MINOR): correlation claim and operating point

**Evidence.**
- **Lewis-Carlson.** "Within 0.5 % of Lewis-Carlson" (`05-plume-cfd/REPORT.md:8`) is arithmetically correct (2.676 against 2.663 De). But the medium-grid band is 2.58-2.74 De and the coarse band 2.64-2.77 De, and the coarse run at the v2 point gives +1.6 %.
- **1-D thrust.** "Within 1 %" of 1-D is -0.98 % on the fine grid but -1.08 % on the coarse grid and -1.09 % at the v2 point.
- **Operating point.** The claim paragraph does not name the v1 operating point (O/F 7.76) that every grid level uses; only line 29 states it.

**Fix.**
- Write "Lewis-Carlson 2.66 De lies inside the CFD band 2.58-2.77 De".
- Write "about 1 %" for the 1-D thrust comparison.
- Name the operating point in the claim.

### RC-12 (MINOR): relief set point against MEOP on the N2O side

**Evidence.**
- **Set points.** Tank MEOP is 7.0 MPa (ENG-09) and the isolation-valve MEOP is 7.0 MPa (combustion.json). The relief is set at about 7.5 MPa (ENGINE-BASELINE-v0), and the trapped-liquid relief at <= 7.5 MPa (ENG-09).
- **Consequence.** Parts can therefore see 7.5 MPa plus accumulation, about 8.25 MPa at an ASSUMED 10 %. A part designed to SF 1.5 on yield at 7.0 MPa then has a yield SF of only 1.27-1.40.
- **Partly handled.** The author already checks the seat at 7.5 MPa.

**Fix (lead).**
- Either set MEOP at or above the relief set point plus tolerance and accumulation, or set the relief at or below MEOP.
- Check COTS valve and hose ratings against the chosen value.

### RC-13 (MINOR): rev-1 citations and internal consistency

**Evidence.**

| Item | Report text | Rev 2 or current state |
|---|---|---|
| (a) Throttle floor | "the 25 % throttle requirement, the 20 % target" (`REPORT.md:21`) | ENG-02 requires <= 20 %; 25 % is a flight fallback only. Conclusion unchanged, since 20 % closes |
| (b) Tank temperature | "The requirement is 20 +/- 3 C (ENG-12)" (`REPORT.md:227`) | Rev 2 says 15-25 C, as does the report's own arm limit (`:899`) |
| (c) Heater at ARM | Not in the arm preconditions | ENG-12: heater hard-disabled at ARM |
| (d) Pc transducer | OI-6 "0-69 bar" | ENG-09 ">= 70 bar". 68.9 bar covers the 67.5 bar proof but not the letter |
| (e) Duty-cycle claim | "closes at every point of the gnc v1 and v2 duty cycles" (`:19`) | OI-1 showed A2 and B1 v2 needing 2.54 and 2.44 kg; superseded by the lead (A2 removed, B1 capped at 85 m) |
| (f) Mechanical input | Configuration cites mechanical.json v1 | v2 (`4f024ed4ccb4618c`) was published after the handback |
| (g) Leak ceiling | `:501` | Inherits the 8.74 g inventory (RC-02) |

**Fix.** Align all of these in v2.4.

### RC-14 (MINOR): oxygen cleaning and cold-flow procedure

**Evidence.**
- **Cleaning.** H5 and H6 require oxygen cleaning but name no standard, verification method or acceptance criterion.
- **Water before N2O.** CF-1 (water) runs before CF-3 (N2O) on the same injector, with no drying or re-cleaning step between them.
- **Catch volume.** The back-pressured catch volume (`REPORT.md:1001`) is itself a closed N2O volume. It needs relief, cleanliness and a vent path.

**Fix.**
- Name the cleaning standard and the inspection.
- Add drying, re-cleaning and a leak check between the water and N2O tests.
- Specify the catch volume's relief and vent.

### RC-15 (MINOR): load-bearing unverified data

**Evidence.**
- **Metal seat.** These values carry the metal-seat verdict (land at 46 % of Fty cold, 62 % hot):
  - 17-4PH H1150 Fty of 724 MPa (LITERATURE-UNVERIFIED, `REPORT.md:472`);
  - hot Fty of 0.85x at 316 C and negligible creep below 370 C (AS RECALLED, `:475-476`).
- **Rod seal.** The PTFE jacket limit of about 260 C (AS RECALLED, `:505`) sits inside the head soak band of 339-586 K (up to 313 C).

**Fix.**
- Verify the 17-4PH values against maker data or MMPDS before the seat and seal drawings are released.
- Check the rod-seal temperature in Mechanical's FEA.

### RC-16 (NOTE): L*

I get a free volume of 300.9 cm3, including 28.3 cm3 of convergent taken from the published contour; the author uses 284.6 cm3. L* is 2.03 m against 1.92 m. No conclusion changes, but the report should state which volume it uses.

### RC-17 (NOTE): Bartz

- **Curvature not stated.** 21.92 MW/m2 is reproduced exactly with the mean throat Rc (0.941 Rt; `nozzle.py:167`, `m1_design.py:277`). The report text (`REPORT.md:697, 745`) does not say which Rc was used.
- **Spread.** The Rc band gives 20.2-24.0 MW/m2. With no eta credit, the flux is 26.0-28.4, still inside the x0.7-1.3 band.
- **Gas state.** T0 = eta_c*^2 Tc may under-predict local streak heating.

### RC-18 (NOTE): eroded-throat separation

With At +11 % (eps 1.8) at constant mass flow (Pc -10 %), pe/pa is 0.522 against Schmucker's 0.529. Separation is still incipient. The author held Pc constant instead. The eps 2.0 decision is unaffected.

### RC-19 (NOTE): CFD presentation

- **(a) Image labels.**
  - Verified: burned-in labels on `blender/final/argos_plume_artistic_side.png` ("ARTISTIC RENDER ... NOT a measurement") and `ownruns/m_2s_100/fig/m2s_synth_photo.png` ("QUALITATIVE synthetic image").
  - The `_raw.png` renders carry no caption; only their file names say "artistic". Keep them out of publishable sets.
- **(b) Afterburn figure.** The report says afterburning is "<= 179 K", but the Richardson extrapolation f_ext is 181.8 K. Quote 172-182 K.
- **(c) v2 point.** "Adds nothing at the v2 point" holds for equilibrium exhaust. Quote the c*-deficit stream-B bound beside it.
- **(d) Floor gas.** The floor sweep uses v1 gas (O/F 3.11, T0 2108 K), whereas the v2.3 floor is O/F 4.06, T0 2500 K. This is disclosed, and a v2-composition afterburn sensitivity is given (1322 K).
- **(e) Ground plane.** Floor afterburning is fuel-rich: 1300-1500 K on the axis at 17-20 De (0.33-0.39 m). This matters for the landing ground-plane case, which is listed as the next closure.

### RC-20 (NOTE): interface hygiene

- **Untagged values.** Two nested objects in combustion.json carry a value with no tag: `thermal_and_loads.head_end_bc.v.n2o_side.v.props_100pct` and `props_12p5pct`.
- **Missing gnc v3 (for the lead).** ENG-06 rev 2 cites gnc.json v3, which has not been published; gnc.json is still v2 (`7089d7b34808cc31`).

### Confirmed good practice

- **Tags.** The tag legend is applied throughout.
- **MEASURED.** No value is presented as MEASURED; the only occurrence is the disclaimer.
- **Failures kept as evidence.** These include:
  - the v2.0 grid comparison at mismatched times;
  - the v2.1 negative GCI;
  - the retired 0.08 s full-stroke time;
  - the B1 v1 web of 0.94 mm;
  - the run-1 actuator file.
- **Unknowns.** They are listed together with the tests that close them (§11).
- **Prices.** The scan found no currency amounts, no "from" prices and no zero prices. Every price is TO-QUOTE to Sønderborg DK-6400 (5 times in REPORT, 3 in the JSON, 1 in HANDBACK).
- **Images.** They are labelled and kept separate from engineering claims.

## 5. CFD verification and validation (task 2)

1. **Is GCI applied correctly?**
   - Yes for mdot (monotone, p 0.87).
   - It is not applicable to thrust (R 1.09, divergent), to Mach-disk x (degenerate) or to far-field quantities, where the fine level inherits the medium state.
   - Comparing all levels at equal physical time correctly fixes the v2.0 time mismatch, which is kept as evidence. But equal time is not equal history (RC-10).
2. **Are temporal bands sound?**
   - In principle yes. They are the right tool for an unsteady under-expanded jet and better than single snapshots.
   - The sample is 4 snapshots over 0.75 ms, with no band for the fine level. That supports a qualitative "not resolvable" verdict and nothing stronger (RC-10).
3. **Do the conclusions follow from the evidence?**
   - **Thrust** about 1 % below 1-D: supported. The loss comes from inviscid divergence and the 2-D throat; viscous loss is not modelled (RC-09).
   - **Mach disk** at 2.6-2.8 De, consistent with Lewis-Carlson 2.66-2.68: supported, but the claim is over-precise (RC-11).
   - **Shock cells** of about 4 De: supported. Harper-Bourne & Fisher gives 4.0-4.1 De (constant from memory). Prandtl-Pack does not apply here, as the report states.
   - **Afterburn:** a mean-field fast-chemistry bound, adequately labelled. Quote f_ext (RC-19).
   - **Floor:** the normal shock and subsonic pocket are plausible. As the report states, slip walls cannot predict separation.
4. **Are the images labelled and kept apart?** Yes (RC-19a). No engineering claim relies on the images.

## 6. Evidence rigour (task 3)

- **Tags.** Every number in the reports is tagged. In the JSON, only two nested values lack tags (RC-20).
- **MEASURED.** None.
- **Unknowns and failures.** Kept (§4 good practice).
- **Load-bearing values quoted from memory.**
  - 17-4PH strength and creep, and the PTFE temperature limit (RC-15).
  - The regression anchor, a secondary citation tagged ASSUMED. It is flagged as unknown 1 and carries the web margins (RC-07).
  - The turbulence constants in 05. These are LITERATURE-UNVERIFIED, but covered by the x0.5 and x2 sensitivity runs.
- **Reviewer's own recalled constants.** The NSC rates, the Harper-Bourne & Fisher factor and the overpressure scaled distance are all labelled as recalled. None of them is used as acceptance evidence.
- **Prices.** Compliant (ENG-14).

## 7. Consistency: report against combustion.json v2.3 and lead decisions (task 4)

| # | Item | REPORT v2.3 | combustion.json v2.3 | Lead / rev 2 | Status |
|---|---|---|---|---|---|
| C1 | Valve state in coasts | Closed (LEAD); mismatch flagged at `:930` | `relight[0]`: "may stay open" | Closed until seat leak is measured (CHANGELOG; ENG-05) | Known mismatch; lead rule governs |
| C2 | Relight start point | "same sequence from t = 0" (`:928`) | `relight[0]`: same | Needs the t = -0.3 s valve step | RC-03 |
| C3 | Fail-safe and abort | Valve closes after the pintle seats (`:923`) | `shutdown[1]`: same | NC valve is the fail-safe; PINTLE_FAULT closes the main valve (ENG-13, ENG-16) | RC-01 |
| C4 | Torch N2O after propane cut | 0.4 s / 0.6 s (`:912`) against "no N2O purge" (`:935`) | `start[8-9]` against `flashback[2]` | ENG-05: no flashback or decomposition in the feed | RC-01 |
| C5 | Trapped-liquid relief | "<= 7.5 MPa" (`:324`, H3) | "to the tank side" (`shutdown[2]`); "<= 7.5 MPa" (`isolation_valve`) | ENG-09: "<= 7.5 MPa" | Destination undefined (RC-04) |
| C6 | Relief against MEOP | Tank MEOP 7.0, relief 7.5 MPa | `isolation_valve.MEOP` 7.0 MPa | ENG-09: tank 7.0 MPa plus relief | RC-12 |
| C7 | Hard-start inventory | 8.74 g at 12.5 % (`:919`) | Ignition lift 12.5-20 % (`start[5]`) | ENG-04 lift-hold rule | RC-02 |
| C8 | Throttle floor | "25 % requirement, 20 % target" (`:21`) | – | ENG-02: <= 20 % | RC-13 |
| C9 | Tank temperature | "20 +/- 3 C (ENG-12)" (`:227`); arm 15-25 C (`:899`) | Arm 15-25 C | ENG-01 and ENG-12: 15-25 C | Rev 2 governs; RC-13 |
| C10 | Heater at ARM | Absent | Absent | ENG-12: hard-disabled | RC-13 |
| C11 | Pc transducer range | OI-6: 0-69 bar | – | ENG-09: >= 70 bar | RC-13 |
| C12 | Insert life | 1.0-4.3 A1 flights, from v1 cycles | `flights_per_insert_A1` [1.0, 4.3] | ENG-06: "1-4" | RC-06 |
| C13 | MEOP basis | 42.85 bar | `full_stroke_failure_S230_max` 42.85 | MEOP 45 bar | RC-08 |
| C14 | Pc sense line | >= 144 Hz, <= 0.64 deg (dead volume <= 0.3 cm3) | 125-230 Hz, <= 0.87 deg (dead volume 0.1-0.5 cm3) | – | Consistent (different dead-volume ranges); no action |
| C15 | Mechanical input | mechanical.json v1 | – | v2 published later | RC-13 |
| C16 | Hose routing | -6 hose accepted on hydraulics | `hose` | O3b coil beside a 136-178 C case, pending Combustion (CHANGELOG line 53) | RC-04 |
| C17 | Duty cycles | gnc v1 and v2 | – | ENG-06 cites gnc v3, unpublished | RC-20 |

## 8. N2O safety review (task 5)

| Topic | Report coverage | Reviewer assessment | Ref |
|---|---|---|---|
| Decomposition and initiators | H1: heat, compression, catalytic surface, hot cavity; 1.86 MJ/kg | Energy confirmed: 1.85 MJ/kg as gas, 1.60 as liquid. Missing initiators: N2O-only flow through the hot torch; the dead-ended torch N2O line at a hot check valve; stagnant N2O in a hose beside a hot case (O3b); a hot seat after disc loss (836-996 K) combined with seat leakage | RC-01, RC-04 |
| Adiabatic compression | H2, Table 2.7, priming rule | Table 2.7 reproduced exactly. At 63-70 bar the gas reaches 652-664 K (N2O) and 925-950 K (N2). The rule is adequate, but the >= 0.3 s valve ramp must be a verified property of the servo-cocked valve | Confirmed |
| Contamination and O2 cleaning | H5, H6 | No standard, no verification, no step for the water-to-N2O transition | RC-14 |
| Relief sizing | H3; H4 "per Mechanical" | No capacity, destination or set basis; set point above MEOP | RC-04, RC-05, RC-12 |
| Hard start | H9: 8.74 g | Inventory 8.4-15 g; constant-volume bound 165-354 bar; no vented estimate | RC-02 |
| Trapped liquid | H3 | The relief will cycle after 4.5-5.5 K of warming; soak to 40-150 C | RC-04 |
| Cold-flow rules | §10 (LEAD rule) | Sound. Add the catch volume's relief and vent, and a drying step | RC-14 |
| Static-fire stand-off | H13: left to the founders | No stored-energy input; ground tank absent | RC-05 |
| Ignition and abort logic | §7.3 | Contradictions; undefined aborts; in-flight retry not feasible | RC-01, RC-03 |
| Post-test and post-landing safing | Absent | 0.61 kg residual; 7.1 MPa at 50 C; no remote vent | RC-04 |
| Near-critical tank | H4 | Adequate. Add the heater hard-disable at ARM | RC-13 |

## 9. Requirements traceability (REQUIREMENTS rev 2)

| Requirement | Combustion role | Evidence in the deliverable | Reviewer result | Status |
|---|---|---|---|---|
| ENG-01: 500 N sea level, tank 15-25 C, Pc capped at 25 bar | Owns | Map and CEA give 500 N at 25.01 bar; Cd_eff >= 0.41 holds the 15 C ceiling | Sizing confirmed (0.00 %); zero margin to eta_cf at the cap | Shown by analysis; margin open until CF-3 and T1 (RC-09) |
| ENG-02: floor <= 20 %, stretch 12.5 %, stable combustion | Owns | Table 4.2; separation in Table 5.2 | 20 % attached (+41 % margin) and 12.5 % incipient confirmed; stability not predicted | Shown on paper; stability open until T3 |
| ENG-03: t10-90 limit, ramp >= 1000 N/s | Affects | Speed checks; Electronics S3 (all 33 steps pass) | Not re-run | Shown by SIM (other owners); open until B-PNT-1 and T2 |
| ENG-04: >= 3 starts, <= 0.5 s to 90 %, ignition-lift hold | Owns igniter and sequence | Torch design; DC-D has 3 starts; model transients | Latency of the adopted sequence not shown; a 12.5 % start takes 0.52-0.53 s | >= 3 starts shown on paper; latency not shown (RC-03) |
| ENG-05: shutdown <= 0.10 s, no flashback or decomposition, valve closed in coasts | Owns tail-off and feed safety | 0.082-0.083 s from 75 % | Flashback and decomposition controls are contradicted at the torch; JSON relight text | Partly shown; interface text non-compliant (RC-01, C1) |
| ENG-06: duty cycles (gnc v3), grain per flight, insert replaced at 5 % (1-4 flights), B1 envelope | Owns grain and insert | Tables 4.3, 4.4, 5.3 | Life 0.46-0.71 A1 flights on v2 with the literature method; n-band corner burns through; gnc v3 absent | Non-compliance risk (RC-06, RC-07) |
| ENG-07, 07b-d: TVC | Supplies mass flow and grain mass and CG history | – | – | Not owned; inputs supplied |
| ENG-08: sweep and hose rule | Supplies hose hydraulics; O3b acceptance pending | -6 hose accepted | Thermal issue with O3b | Open (RC-04) |
| ENG-09: MEOP 45 bar, proof 67.5 bar, abort at about 30 bar, relief <= 7.5 MPa, transducer >= 70 bar | Shares | Table 3.7, H11, OI-6 | MEOP corner 44.3-47.1 bar; abort action undefined; relief above MEOP; 69 against 70 bar | Partly shown (RC-08, RC-01, RC-12, RC-13) |
| ENG-10, ENG-11 | Not owned | – | – | Not applicable |
| ENG-12: propellants, grain, eps, insert | Owns definitions | §0 configuration | Consistent: 2.00 kg / 3.17 L; S230 53.5 x 230 mm, 25 mm port, 0.404 kg; eps 2.0. Stale 20 +/- 3 C citation; heater at ARM missing | Shown; minor text fixes (RC-13) |
| ENG-13: ECU interlocks and abort rules | Supplies the sequence (OI-8) | §7.3 | Abort matrix missing; no in-flight policy | Open (RC-01) |
| ENG-14: cost, TO-QUOTE to DK-6400, no zero or "from" prices | Owns its BOM lines | Scan | Clean | Shown |
| ENG-15: manufacturability | Affects | Printed grain; 17-4PH H900/H1150; lapped seat | Heat-treatment and lapping services not quoted | Open (Mechanical and BOM) |
| ENG-16: safety | Shares | §9, §10 | Gaps in sequence logic, hard start, relief, stand-off, safing and remote vent | Not yet compliant (RC-01, -02, -04, -05, -14) |

## 10. Verdicts and acceptance criteria

**02-combustion (REPORT v2.3, combustion.json v2.3, HANDBACK-SUMMARY): REVISE.**

I reproduced the following independently, to within 0.1-1 %, and found nothing that invalidates the paper design point:
- thermochemistry and sizing;
- injector model;
- throat heat flux;
- floor separation;
- grain at n 0.5.

The report's stated use is as the basis for N2O tests, and for that use it needs revision. Acceptance criteria for v2.4:
1. **Before IGN-1 and T1:** RC-01 and RC-02 are closed (sequence, abort matrix, hard-start bound, chosen lift and check time), and Electronics has reviewed them.
2. **Before CF-3 with the flight valve and hose:** RC-04 (relief specification and safing) and RC-05 (stored-energy table and relief sizing) are closed.
3. **Before the next GNC baseline:** the RC-03 latency distribution is delivered and the GNC Monte Carlo is re-run.
4. **Before ENG-06 is frozen:** the RC-06 and RC-07 tables are produced on current cycles.
5. **Minor items:** RC-08 to RC-15 are corrected or explicitly accepted by the lead.
6. **Re-review scope:** only the changed sections are re-reviewed. The confirmed core (CEA, sizing, injector, Bartz, separation, plume correlations) is not repeated unless its inputs change.

**HANDBACK-SUMMARY** follows the report. Update lines 79-80 per RC-10.

**05-plume-cfd (REPORT v2.1a / v2.2): ACCEPT WITH COMMENTS.**
- **Next revision:** make the wording changes in RC-10, RC-11 and RC-19 (a)-(c).
- **eta_cf band:** feed the OpenFOAM no-slip evidence (-1 %) into the eta_cf band (RC-09).
- **No re-run needed** for the present uses: thrust, near-field shock structure and the afterburn bound.
- **Far-field mixing results** remain model-dependent, as the author states. Do not use them for thermal design until the ground-plane case and measurements exist.

These verdicts concern digital deliverables only. No hardware has been tested. Recording the verdict in the project's supervision record is the lead's action.

## 11. What remains unverifiable until test

| Open item | Closed by |
|---|---|
| Two-phase pintle Cd, and the choice of model (HEM 0.69x / SPI 1.42x of Dyer) | CF-1, CF-3 |
| Regression law (a, n), eta_c*, and eta_cf including viscous loss | T1-T2 |
| Ignition delay, torch reliability and the relight latency distribution | IGN-1, T1, T4 |
| Throat erosion and insert life | Bore measurement after T1 and T4 |
| Low-frequency stability and combustion efficiency at the floor; lip separation and side load at 12.5 % | T3 |
| Seat leak and break-out after a dwell; closing time at 25 bar and at MEOP | B-PNT-1, CF-2 |
| Head-end and hose soak temperatures; trapped-liquid relief cycling | T1 and T4 thermocouples and feed pressure |
| Roll torque and thrust misalignment | T1 |

Items no planned test will close:
- **Reaction time of pooled N2O after a no-light.** It should not be tested deliberately. Bound it by design and procedure.
- **Plume afterburning, radiation and ground interaction.** No measurement is planned; the ground-plane CFD case is the next closure.
- **Fragment and blast hazard of the vessels.** No data exist; this rests on the standard the founders apply.

## 12. Reviewer files (`reviews/combustion/`)

**Scripts:**
- `rc01_cea.py` `c557e2241aed4b74`
- `rc02_sizing.py` `c620841209ded91c`
- `rc03_injector.py` `4c21c6a39f9123d9`
- `rc03b_meop_corner.py` `65c6b35d45f9dea8`
- `rc04_bartz.py` `3f27e46e0f388e8b`
- `rc05_grain.py` `ed8c731c7961fc98`
- `rc06_separation.py` `23ad7e6389160f2a`
- `rc07_plume.py` `4a8de03db6e8b770`
- `rc08_erosion.py` `fb35bba62e1e35fc`
- `rc09_safety.py` `52813f4cf5663eac`
- `rc10_gci.py` `6b9a29bc938ce50a`
- `rc11_scan.py` `6ebad84dd15b9924`

**Outputs:**
- `rc01_cea.json` `45f1f78f75613cea`
- `rc02_sizing.json` `7b211fd6957ca475`
- `rc03_injector.json` `c15176bf563f5a80`
- `rc03b_meop_corner.json` `90ef93ce0bf3d570`
- `rc04_bartz.json` `4f656c28d0521a1c`
- `rc05_grain.json` `fc419ac23cd3313c`
- `rc06_separation.json` `b5b1ec68ed8e1896`
- `rc07_plume.json` `d9f6e6df512da65b`
- `rc08_erosion.json` `b32a37829edddd4a`
- `rc09_safety.json` `e8e831c0068d8b0d`
- `rc10_gci.json` `d7944125149870f8`
- `rc11_scan.json` `915d9af9684054fc`

Run with `/opt/engine-venv/bin/python -I <script>` from the folder. Each script writes its JSON next to itself. `rc03b` imports `rc03`, and `rc08` imports `rc05`. No author or specialist file was modified.
