# ARGOS H1: Combustion and propulsion report (02-combustion)

Version 2.3, 2026-10-12. Owner: Combustion and Propulsion. Interface: `interfaces/combustion.json` v2.3 (sha256/16 `d9ec54fbf450e243`). Status: second pass (M2), digital only, *Por revisar* (no independent review yet).

Tag legend:
- REQ: founder or lead requirement.
- LEAD: lead decision.
- LITERATURE: cited source; LITERATURE-UNVERIFIED means quoted from memory and not re-checked.
- CEA: NASA CEA through RocketCEA.
- SIM: our simulation.
- DERIVED: calculation from tagged inputs.
- ASSUMED: engineering assumption with a stated band.
- TO-QUOTE / TO-VERIFY: open procurement or verification items.

No number in this report is MEASURED.

## 0. Checkpoint

**Claim.** The engine closes on paper at every point of the gnc.json v1 and v2 duty cycles:
- 500 N at sea level;
- the 25 % throttle requirement, the 20 % target and the 12.5 % stretch floor;
- three or more starts per flight.

The engine itself:
- an N2O/ABS hybrid with a printed straight-port grain (S230);
- a servo-driven pintle injector behind a normally-closed isolation valve;
- a spark-ignited N2O/propane torch;
- a conical graphite-throat nozzle with eps 2.

The closure rests on three unmeasured assumptions:
- the regression law, band x0.6-1.5 on the coefficient;
- the pintle discharge coefficient, Cd 0.6-0.8;
- the combustion efficiency, eta_c* 0.92 (band 0.85-0.96).

This is a design basis for cold-flow and static-fire testing. It is not a demonstrated engine. A higher-fidelity model is not proof of higher accuracy (AGENTS.md).

**Configuration** (combustion.json v2.3):
- Grain: S230 ABS, OD 53.5 mm, L 230 mm, centred straight port of 25 mm.
- Case: 6061-T6 tube, 63.5 x 3.175 mm, with a 1.6 mm liner in the grain zone (mechanical.json v1).
- Chambers: pre-chamber 30 mm, post-chamber 40 mm.
- Pintle:
  - 5.5 mm seat, 15 deg needle, 4 mm stroke, 3 mm stem;
  - rolling-guide carriage with a spring of 0.25 N m + 0.12 N m/rad (LEAD 2026-10-12);
  - 17-4PH needle H900 on a 17-4PH H1150 seat.
- Feed: NC isolation valve Cv >= 3; filter <= 15 um at Cv >= 2.2.
- Nozzle: conical, Dt 13.724 mm, eps 2.0, graphite insert.
- Igniter: N2O/propane torch.
- Tank: 2.00 kg in 3.17 L, self-pressurised at 15-25 C.
- Duty cycles: gnc.json v1 and gnc.json v2 (published 2026-10-12 20:34Z).
- Model assumptions: eta_c* 0.92, eta_cf 0.975, Cd 0.70, r = 5.77e-5 G_ox^0.5 (x0.6-1.5), non-equilibrium tank with E = 100-1000.
- Software: Python 3 in /opt/engine-venv with rocketcea 1.2.3, cantera 3.2.0, CoolProp 8.0.0, numpy 2.5.4, scipy 1.18.1, numba 0.68.0. OpenFOAM v1912 is used for the plume (05-plume-cfd).

**Sources** (full citations are in the script docstrings):
- Thermochemistry and fuels:
  - NASA CEA through RocketCEA.
  - Cantera with GRI-3.0 thermodynamics.
  - NIST Chemistry WebBook.
  - Walters, Hackett & Lyon, FAA "Heats of Combustion of High Temperature Polymers".
  - Wilkey, Thibaudeau & Whitmore, Appl. Sci. 16(16) 8063 (2026), and Walker, USU MS thesis 2015 (ABS composition).
  - Polymer Handbook (polymerisation enthalpies, LITERATURE-UNVERIFIED).
- N2O, tank and injector:
  - CoolProp 8 (Lemmon & Span EOS) against ESDU 91022.
  - Dyer, Zilliac, Sadhwani, Karabeyoglu & Cantwell, AIAA 2007-5702 (NHNE model).
  - Zilliac & Karabeyoglu, AIAA 2005-3549, and Zimmerman, Waxman, Cantwell & Zilliac, AIAA 2013-4045 (tank models).
  - Whitmore & Chandler (equilibrium tank).
- Regression and stability:
  - Karabeyoglu et al., JPP 21(6) 2005 (hybrid thermal lag and low-frequency instability).
  - Boughaba & Hendrick, EUCASS 2013 (regression anchor).
  - Zilliac & Karabeyoglu, AIAA 2006-4504 (flux-exponent band).
- Heat transfer, nozzle and throat:
  - Bartz, Jet Propulsion 27(1) 1957; Huzel & Huang 1992.
  - Rao 1958 practice for throat radii.
  - Summerfield and Schmucker separation criteria.
  - Rotondi, Migliorino, Bianchi, Kamps & Nagata, JPP 40(3) 2024 (graphite erosion kinetics and measured N2O/HDPE rates).
  - Thakre & Yang, JPP 24(4) 2008.
  - Modest, Radiative Heat Transfer (emissivity band).
- Interfaces read:
  - gnc.json v2 (20:34Z) and v1; mechanical.json v1.
  - Mechanical CAD and calculation notes v3.1-v3.4, including pintle_inline_v34 v2, v2.1 and v2.2 (read-only).
  - electronics.json v1; ENGINE-BASELINE-v0; CHANGELOG to line 45.

**Files:**
- Hub `/home/claude/work/shared-fallback/engine/02-combustion/`:
  - `src/`: 42 scripts.
  - `data/`: v1, `thermo/` and `v2/`, which holds the duty-cycle histories, engine maps, thermal BC CSVs and as-published interface copies.
  - `figs/v2/`: 26 PNG.
  - `inputs/`: snapshots of the gnc.json files that were used.
- Interface: `interfaces/combustion.json` v2.3, plus an append-only CHANGELOG line.
- Working runs: `/home/claude/work/combustion/`.
- Section 14 indexes the files.

**Tests / verification:**
- CoolProp agrees with ESDU 91022 within 0.98 % up to 300 K (§2.1).
- The injector lookup table agrees with direct evaluation within 0.5 % (self-test).
- c* stays within +/-0.3 % across every ABS card and heat-of-formation source (§1.2).
- gnc.json v2 reports its engine model's oxidiser-per-impulse error against these runs as -0.46 % to +0.09 %.
- Mechanical's pintle C1/C2 numbers for v2, v2.1 and v2.2 are reproduced exactly with force law L0, as an assert in `src/needle_force_v2p3.py`.
- Each interface writer asserts its input hashes and asserts that every key outside the edited ones is unchanged. The published file was read back more than 10 s after writing.
- Not run: `npm test` and `npm run build`, because no application code was touched and the repository is read-only for this role. No physical test exists yet.

**Unknowns** (full list in §11): regression law; two-phase Cd; eta_c*; low-flux combustion at the floor; ignition delay; graphite erosion kinetics and grade; roll torque and thrust misalignment; needle force versus lift; seat friction, break-out and leak rate.

**Next closure:**
1. Founders: cold flows CF-1 to CF-3 and the pintle bench B-PNT-1 (§10). These measure Cd_eff, force versus lift, leak rate, break-out torque and closing time.
2. Static fires T1-T2, which measure (a, n), eta_c*, roll torque and head-end temperatures.
3. Combustion re-runs with the measured Cd and regression law: maps, duty cycles, the ENG-05 tail-off with the measured closing curve, and erosion with the measured bore.
4. Mechanical thermal FEA with the BC CSVs (OI-4, OI-5, OI-15).
5. An independent reviewer records criteria and verdict in `public/engineering/supervision.json`.

## Contents

1. Thermochemistry
2. N2O tank and feed
3. Throttle and shutoff architecture (with the pintle force, seat and seal review)
4. Grain and internal ballistics
5. Nozzle and throat erosion
6. Heat loads
7. Ignition, restart, start-up and shutdown
8. Combustion stability
9. N2O hazard list
10. Cold-flow and static-fire test plan
11. Unknowns
12. Remaining mismatches and open interface issues
13. Failures and superseded evidence
14. File index and reproduction

## 1. Thermochemistry

### 1.1 Method

RocketCEA (NASA CEA) computes shifting and frozen equilibrium over Pc 3-30 bar and O/F 2-10 (`src/thermo_tables.py` writes `data/thermo/*_v1.{csv,json}`). Outputs:
- c*, Tc, gamma and MW;
- Isp_SL and Isp_vac against eps, aware of Schmucker separation;
- transport properties (mu, cp, Pr, k) in the chamber and at the throat;
- exit composition at eps 2.

The oxidiser card is CEA "N2O", an ideal gas at 298.15 K. Cantera (GRI-3.0 thermodynamics) supplies the delivered-state compositions for the erosion model and the plume afterburning post-processor.

### 1.2 Fuel cards and heats of formation

The lead's v0 card, C15H17N with hf +62.6 kJ/mol (+296 kJ/kg), was checked against three independent routes (`src/cea_cards.py`).

Table 1.1. ABS and PETG cards. c* is ideal shifting equilibrium at 25 bar (CEA). Source of hf: DERIVED from the stated LITERATURE.

| Card | Basis | hf [kJ/kg] | c* peak [m/s] | O/F at peak |
|---|---|---|---|---|
| ABS_LEAD_v0 | lead v0, C15H17N +62.6 kJ/mol (ASSUMED) | +296 | 1601 | 5.50 |
| ABS_TYP_v1 (design card) | monomer hf + polymerisation enthalpy, composition A/B/S 0.24/0.185/0.575 | +476 | 1601 | 5.50 |
| ABS_FAA_v1 | FAA bomb calorimetry Qc 39.84 kJ/g | +452 | 1603 | 5.50 |
| ABS_FAAGC_v1 | FAA group contribution Qc 39.43 kJ/g | +42 | 1597 | 5.50 |
| ABS_SRICH / BRICH / ARICH_v1 | composition corners of the published ranges | +458 / +458 / +494 | 1600 / 1603 / 1600 | 5.50 / 5.75 / 5.50 |
| ABS_USU5043_v1 | 50:43:7 B:A:S (withdrawn USU record) | +711 | 1611 | 5.25 |
| PETG_NOM / LO / HI_v1 | PET hf -704 / -812 / -441 kJ/mol, CHDM 0.31 (ASSUMED) | -3406 / -3902 / -2197 | 1538 / 1529 / 1562 | 3.75 / 4.00 / 3.50 |
| PARABS50_v1 | 50/50 wt paraffin/ABS (research option) | n/a | 1608 | 6.25 |

Findings:
- The v0 value is not reproduced by any source. The spread of ABS heat of formation (+42 to +494 kJ/kg) moves c* by no more than +/-0.3 %, so it does not matter for performance. ABS_TYP_v1 is the design card.
- PETG reaches 3-4.5 % lower c* at a much lower optimum O/F (3.5-4). PETG as a backup therefore needs its own grain design with more fuel surface or length, and its own regression law.
- Paraffin/ABS is listed as a research option only.

Research proposal, paraffin/ABS composite:
- Hypothesis: higher regression gives a shorter grain at the same O/F.
- Comparator: S230 ABS.
- Evidence: none of our own; the composite concept is from the USU literature (McCulley et al. 2012, LITERATURE-UNVERIFIED).
- Refutation criterion: measured regression gain below 1.5x, or a print or structural defect.

### 1.3 Performance against O/F

Table 1.2. N2O/ABS_TYP_v1 at Pc 25 bar, shifting equilibrium, ideal (CEA).

| O/F | c* [m/s] | Tc [K] | MW | gamma_c | Isp_vac eps 2 [s] | Isp_SL eps 2 [s] | pe/pa eps 2 |
|---|---|---|---|---|---|---|---|
| 3.00 | 1449 | 2446 | 22.53 | 1.2133 | 215.3 | 203.3 | 2.68 |
| 4.00 | 1548 | 3009 | 24.27 | 1.2297 | 230.4 | 217.6 | 2.73 |
| 5.00 | 1595 | 3296 | 25.85 | 1.1787 | 237.7 | 224.6 | 2.89 |
| 5.50 | 1601 | 3354 | 26.41 | 1.1635 | 239.1 | 225.9 | 3.00 |
| 6.00 | 1600 | 3379 | 26.85 | 1.1548 | 239.3 | 226.1 | 3.11 |
| 7.00 | 1585 | 3380 | 27.52 | 1.1472 | 237.5 | 224.4 | 3.22 |
| 8.00 | 1566 | 3353 | 28.00 | 1.1449 | 234.8 | 221.9 | 3.24 |
| 9.00 | 1548 | 3316 | 28.35 | 1.1448 | 232.0 | 219.2 | 3.23 |
| 10.00 | 1530 | 3275 | 28.62 | 1.1459 | 229.3 | 216.6 | 3.21 |

Stoichiometric O/F is 8.17 (CEA, `chamber_port_state_v2.json`).

### 1.4 Liquid-N2O injection

Table 1.3 compares liquid N2O injected at 20 C with gas N2O at 298 K. The effective hf of the liquid is 70.82 kJ/mol (CEA + CoolProp, `data/thermo/n2o_liquid_correction_v1.json`).

| Pc [bar] | O/F | c* gas [m/s] | c* liquid [m/s] | dc* [%] | Tc gas [K] | Tc liquid [K] |
|---|---|---|---|---|---|---|
| 25.00 | 7.76 | 1571 | 1554 | -1.10 | 3361 | 3310 |
| 13.25 | 5.48 | 1594 | 1574 | -1.26 | 3292 | 3235 |
| 6.18 | 3.70 | 1522 | 1491 | -1.99 | 2827 | 2736 |
| 4.36 | 3.11 | 1453 | 1425 | -1.91 | 2491 | 2391 |

The engine maps use the gas card with eta_c* 0.92, so this 1-2 % penalty is not applied separately. It lies inside the eta_c* band. eta_c* measured in T1-T2 with liquid injection will include it.

### 1.5 Design O/F and its shift with throttle

The O/F is not a free choice in a hybrid. With n = 0.5:
- fuel flow scales as G_ox^0.5 x (burning area), so O/F scales as mdot_ox^0.5;
- the port diameter drops out (D^(2n-1) = 1), so at n = 0.5 the O/F at a given oxidiser flow does not drift as the port opens. With n < 0.5 it would rise; with n > 0.5 it would fall. The measured n decides this.

Consequences for the S230 grain:
- O/F is 10.4 at 100 % (initial port) and 4.06 at 12.5 %. 10.4 / sqrt(241/36.5) = 4.05.
- The 100 % point is lean of the c* optimum (O/F 5.5-6). That costs about 4 % in c* (1530 against 1601 m/s ideal) and leaves an oxidiser-rich exhaust: about 7 % O2 in the chamber, and no plume afterburning (05-plume-cfd).
- The floor runs close to the low-pressure c* optimum (5.25 at 4.36 bar).
- The lean 100 % point is the cost of a short grain. S260 lowers the A1 mean O/F only from 8.9 to 7.8 (Table 4.2), and the gimbal sweep makes length expensive.

## 2. N2O tank and feed

### 2.1 Properties

CoolProp 8.0 (`NitrousOxide`, Lemmon & Span) is compared with ESDU 91022 in `src/n2o_validation.py` and `data/v2/n2o_validation_v2.json`.

Table 2.1. Maximum absolute deviation [%] (LITERATURE against LITERATURE).

| T band | P_sat | rho_l | rho_v | h_fg |
|---|---|---|---|---|
| 230-290 K | 0.33 | 0.60 | 0.72 | 0.29 |
| 290-300 K | 0.15 | 0.19 | 0.98 | 0.92 |
| 300-305 K | 0.14 | 0.09 | 2.22 | 2.08 |
| 305-309.5 K | 0.09 | 4.88 | 3.37 | 47.61 |

Validity:
- About 1 % property uncertainty up to 300 K (27 C), about 2 % to 305 K.
- Within 4 K of the critical point (Tc 309.52 K in CoolProp against 309.57 K in ESDU; Pc 72.5 bar) the representations diverge. The 30-36 C range is a hazard regime, never a design point. The requirement is 20 +/- 3 C (ENG-12).
- CoolProp 8 has no N2O transport properties. CO2 at the same reduced temperature is used as a surrogate (ASSUMED), for the tank heat-transfer closure only.

### 2.2 Blowdown models and the thrust ceiling against time

Two tank models are used:
- Equilibrium, Whitmore & Chandler type (`src/tank.py`).
- Two-control-volume non-equilibrium, Zilliac & Karabeyoglu type (`src/tank_nheq.py`). Its evaporation enhancement factor E is not calibrated, so it runs as a band: E = 100 and 1000.

The baseline tank (LEAD 2026-10-12) holds 2.00 kg in 3.17 L, conditioned to 15-25 C. Saturation pressure is 45.0 / 50.5 / 56.5 bar at 15 / 20 / 25 C (CoolProp).

Table 2.2. Continuous 500 N command from t = 0 on the baseline tank: S230 grain, Dyer pintle Cd 0.70 (SIM, `data/v2/ceiling_vs_time_BLtank_v2.csv`).

| Tank model | T0 [C] | Ceiling at t=0 [N] | 500 N held [s] | Liquid end [s] | Ceiling at liquid end [N] | P_tank at liquid end [bar] | N2O used [kg] | Impulse to liquid end [N s] |
|---|---|---|---|---|---|---|---|---|
| eq | 15 | 666 | 5.81 | 7.31 | 445 | 29.7 | 1.737 | 3611 |
| eq | 20 | 719 | 7.01 | 7.08 | 492 | 32.8 | 1.704 | 3541 |
| eq | 25 | 771 | 6.93 | 6.93 | 544 | 36.2 | 1.669 | 3467 |
| neq E1e2 | 15 | 666 | 4.06 | 7.50 | 423 | 28.2 | 1.737 | 3616 |
| neq E1e2 | 20 | 719 | 6.15 | 7.12 | 467 | 31.1 | 1.704 | 3542 |
| neq E1e2 | 25 | 771 | 6.92 | 6.92 | 516 | 34.4 | 1.666 | 3461 |
| neq E1e3 | 15 | 666 | 5.73 | 7.22 | 450 | 29.9 | 1.717 | 3570 |
| neq E1e3 | 20 | 719 | 6.97 | 6.97 | 497 | 33.2 | 1.678 | 3486 |
| neq E1e3 | 25 | 771 | 6.77 | 6.77 | 551 | 36.9 | 1.630 | 3387 |

- The old gnc.json v1 tank (2.06 L, 1.30 kg) holds 500 N for 2.63-4.56 s (`ceiling_vs_time_v2.csv`).
- On every gnc.json v2 cycle the ceiling never limits. The minimum ceiling is 556-598 N, the minimum dP/Pc is 0.55-0.80, and liquid left over oxidiser used is 0.27-0.51, which meets the GNC reserve rule (>= 0.20 + 0.03).

### 2.3 N2 supercharge trade

Table 2.3. DC-A1 v1 profile, equilibrium tank, N2 treated as insoluble (ASSUMPTION). SIM, `data/v2/supercharge_trade_v2.json`.

| Option | P start [bar] | P at MECO [bar] | P at relight [bar] | P end [bar] | Note |
|---|---|---|---|---|---|
| SP0 self-pressurised 20 C | 50.5 | 41.9 | 41.8 | 37.2 | baseline |
| SP1 self 25 C | 56.5 | 46.1 | 46.0 | 40.7 | ground heater, removed at liftoff |
| SP1 self 28 C | 60.3 | 48.8 | 48.7 | 42.9 | ground heater |
| SP2 N2 pad 60 bar | 59.9 | 45.3 | 45.2 | 39.8 | 5.5 g N2 |
| SP3 regulated 55 bar | 54.8 | 55.0 | 55.0 | 55.0 | 44.9 g N2 from a 0.21 L, 300 bar bottle |

Recommendation (DERIVED, recorded as a v2 decision): self-pressurised N2O conditioned to 15-25 C with a heater blanket that is removed at liftoff. Supercharge is not baselined:
- Heating to 25 C adds 4.3 bar at MECO; an N2 pad adds 3.4 bar and needs a fill system and a bottle.
- Regulated N2 adds about 13 bar at the end, but adds a 300 bar system, a regulator and a cost, all TO-QUOTE (Sønderborg DK-6400).
- The landing margin is already met: the ceiling is >= 556 N on all v2 cycles.
- The N2 options also carry an unverified solubility effect, since N2 dissolves in N2O.

### 2.4 Propellant settling for relight

Table 2.4. Settling before relight (DERIVED from the GNC acceleration histories). Files: `settling_v2.json` and `settling_v2wip_preview.json`. The v2 rows were run on the 19:15Z working copy; its accelerations differ from the published files by no more than 1e-4 m/s2.

| Duty cycle | Coast [s] | a_min [m/s2] | Time a<0 [s] | Settled before relight [s] | a mean, last 0.5 s [m/s2] | Bond | t_settle [s] |
|---|---|---|---|---|---|---|---|
| DC-A1 (gnc v1) | 22.16 | -1.20 | 6.63 | 14.96 | 9.82 | 6442 | 0.25 |
| DC-A2 (gnc v1) | 12.78 | -1.15 | 6.60 | 3.13 | 1.77 | 1158 | 0.58 |
| DC-A1 (gnc v2) | 20.92 | -1.24 | 6.66 | 13.93 | 9.76 | 6400 | 0.25 |
| DC-A2 (gnc v2) | 11.26 | -1.18 | 3.54 | 2.20 | 2.43 | 1595 | 0.50 |

- During 3.5-6.7 s of each coast the axial specific force is negative, down to -1.2 m/s2. The liquid moves forward and the outlet can uncover.
- Before relight, drag or the drogue resettles it. The Bond number of 1158-6442 means gravity dominates; the settled interval is 2.2-15 s against a 0.25-0.58 s settle estimate.
- No dip tube or baffle is needed for these cycles.
- Condition, proposed (DERIVED): the relight permissive requires a positive axial specific force for at least t_settle with margin. A2 v2 has 2.2 s against 0.5 s.
- The igniter sequence also requires P_feed >= 0.5 P_tank. Otherwise the priming rule applies (§7).

### 2.5 Injector two-phase flow and Cd

Three models are compared (`src/injector.py`, `src/injector_compare.py`):
- SPI (incompressible);
- HEM (homogeneous equilibrium, isentropic);
- Dyer NHNE, the non-equilibrium blend of the two. It is the baseline.

The upstream state is metastable liquid after the line loss. At the max-thrust point the ratio G_model/G_Dyer is 0.64-0.68 for HEM and 1.34-1.37 for SPI.

Table 2.5. Thrust ceiling against Cd with the Dyer model (SIM, `injector_compare_v2.json`).

| T [C] | Cd 0.50 | Cd 0.60 | Cd 0.70 | Cd 0.80 | Limit at Cd 0.8 |
|---|---|---|---|---|---|
| 15 | 563 N | 619 N | 666 N | 669 N | dP/Pc 0.25 |
| 20 | 603 N | 666 N | 719 N | 747 N | dP/Pc 0.25 |
| 25 | 642 N | 712 N | 771 N | 822 N | stroke |

Worst model case: HEM at 15 C with Cd 0.6 is equivalent to Dyer with Cd_eff 0.407, which gives a 498.6 N ceiling.

Acceptance criterion (DERIVED): Cd_eff measured in N2O cold flow, relative to Dyer, must be >= 0.41. This keeps the 15 C ceiling at or above 500 N. Cd is measured first in water (single-phase Cd against lift), then in N2O against back-pressure (§10).

### 2.6 Feed line, hose, sense line, priming

Table 2.6. Feed budget at 0.26 kg/s and 20 C (DERIVED, `feed_line_checks_v2.json`).

| Item | Value |
|---|---|
| Total dp, Cv 3 valve + Cv 2.2 filter | 117.1 kPa |
| Total dp, Cv 1.5 valve + Cv 1.0 filter (v1 values) | 285.3 kPa |
| Line-loss budget used by every simulation | 270.4 kPa |

Line elements:
- Hose: -6 PTFE-lined braid across the gimbal, accepted. Velocity 6.3 m/s at 0.241 kg/s and 6.5-7.1 m/s at 0.26 kg/s; friction 8-17 kPa; slow-closure surge 14-106 kPa (40-150 ms closure, 0.4-0.8 m line).
- Pc sense line: 1/8 in tube (1.6 mm ID), <= 0.3 m long, transducer dead volume <= 0.3 cm3. Natural frequency is >= 144 Hz in N2O-like gas and >= 188 Hz in N2. Phase lag at 50 Hz is <= 0.64 deg (Bergh-Tijdeman-type lumped model, DERIVED).
- Trapped-liquid relief (<= 7.5 MPa) is required between the isolation valve and the pintle.

Table 2.7. Upper-bound gas temperature from adiabatic compression when the isolation valve opens fast onto a dead-ended line (DERIVED).

| P_tank [bar] | N2 ideal [K] | N2 CoolProp [K] | N2O vapour CoolProp [K] |
|---|---|---|---|
| 45 | 870 | 847 | 614 |
| 52 | 907 | 879 | 630 |
| 60 | 944 | 913 | 646 |

Priming rule (DERIVED, in combustion.json):
- First start with an unprimed line (P_feed < 0.5 P_tank): move the pintle to a 0.10 mm bleed lift before the isolation valve moves, so the line vents through the injector. The isolation valve opening ramp is >= 0.3 s.
- Relight with a primed line: normal sequence.

## 3. Throttle and shutoff architecture

### 3.1 Trade and decision

Three architectures were compared (`src/throttle_trade.py`), evaluated at the v1-grain points. The S230 points need 6 % more oxidiser flow at 100 %, which does not change the ranking.
- (a) V-ball valve upstream with a fixed injector.
- (b) Variable-area pintle.
- (c) Valve with a showerhead.

Table 3.1. Throttle trade (SIM/DERIVED, `throttle_trade_v2.json`).

| Throttle % | Pc [bar] | mdot_ox [g/s] | (b) lift [mm] | (b) dP/Pc | (b) dF/dh [N/mm] | (a,c) vapour quality after valve | (a,c) dP/Pc | (a) manifold tau [ms] | (c) manifold tau [ms] |
|---|---|---|---|---|---|---|---|---|---|
| 100 | 24.99 | 226.6 | 1.765 | 0.94 | 177 | 0.028 | 0.94 | 0.0 | 0.2 |
| 75 | 19.11 | 168.5 | 1.164 | 1.58 | 242 | 0.028 | 1.54 | 0.0 | 0.2 |
| 50 | 13.25 | 113.0 | 0.711 | 2.78 | 319 | 0.118 | 2.08 | 0.0 | 0.2 |
| 25 | 7.36 | 61.3 | 0.358 | 5.84 | 390 | 0.273 | 2.27 | 0.1 | 0.4 |
| 20 | 6.18 | 51.5 | 0.296 | 7.16 | 410 | 0.304 | 2.33 | 0.1 | 0.4 |
| 12.5 | 4.36 | 36.3 | 0.205 | 10.57 | 371 | 0.355 | 2.43 | 0.1 | 0.5 |

Criteria:
- Flashing. (b) meters at the injector with single-phase liquid upstream. (a) and (c) flash between valve and injector, with vapour quality 0.27-0.36 at <= 25 % throttle.
- Chug margin. At 12.5 %, dP/Pc is 10.6 for (b) against 2.4 for (a) and (c).
- Linearity. For (b), dF/dh varies by 2.3x over the range and K_h by 2.7x (Table 3.3); this is handled by gain scheduling.
- Response. The chamber fills in 4 ms; manifold time constants are <= 0.5 ms.
- Shutoff tightness. (b) gives two barriers, the seat and the NC valve.
- Cost and buildability. (b) needs custom machining; (a) uses a COTS V-ball valve.
- N2O compatibility. All three need oxygen cleaning.

Decision (LEAD 2026-10-11, confirmed by the v2 trade): a servo-driven variable-area pintle at the head end, plus a separate normally-closed main isolation valve upstream, on the tank side and off the gimbal. The isolation valve has Cv >= 3, MEOP 70 bar and closes in <= 0.15 s. Its price is TO-QUOTE (Sønderborg DK-6400).

### 3.2 Flow area against position

A(h) = pi h sin(a) (D_s - h sin(a) cos(a)), with a = 15 deg and D_s = 5.5 mm. A is 15.2 mm2 at the 4.2 mm stop.

Files:
- `data/pintle_area_vs_lift_v1.csv`: geometric area.
- `data/v2/engine_S230/throttle_map_v2.csv`: lift for each thrust fraction. Axes are P_tank 35-55 bar, D_port 25-45 mm and fraction 0.125-1.
- The ceiling column is the lower of the 4 mm stroke and the lift where dP/Pc reaches 0.25.

Lift is 1.916 mm at 100 % and 0.207 mm at 12.5 % (20 C, initial port).

### 3.3 Actuator requirements (for Mechanical and Electronics)

| Item | Value | Tag |
|---|---|---|
| Stroke | 4.0 mm; mechanical stop 4.2 mm | v1 / Mechanical |
| Position resolution | <= 10 um. A 0.5 % F_max deadband open-loop needs 16 um at 100 % and 6.8 um at 12.5 %. Closed loop it is 0.13 bar Pc at 100 % and 0.17 bar at the floor (OI-13). | DERIVED |
| Full-stroke time | The v1 value of 0.08 s is retired (no combustion basis). ENG-05 (< 10 % thrust within 0.10 s) from 100 % needs <= 0.205 s. From 75 %, a 0.25 s drive gives 0.082 s. | SIM, LEAD |
| MECO rule | GNC throttles down to <= 75 % before MECO. The spring assists closing. Closing time at 25 bar is measured in B-PNT-1. | LEAD 2026-10-12 |
| Slew and response | >= 2 F_max/s and t10-90 <= 0.15 s (gnc.json v2 ENG-03). The start ramp cap is <= 2500 N/s. | gnc.json v2 / DERIVED |
| Needle forces | Law and envelope in §3.5 | DERIVED |
| Servo environment | HV69 rated -10 to 60 C; mount limit 50 C in flight, including relight (OI-15) | Mechanical/Electronics |

Shutdown tail-off with the pintle closing in 0.08 / 0.149 / 0.240 / 0.250 / 0.400 s full stroke (SIM):
- time to < 10 % from 100 % is 0.052 / 0.078 / 0.115 / 0.119 / 0.182 s;
- tail-off impulse is 16.4 N s at 0.08 s and 36.3 N s at 0.25 s.

### 3.4 Plant model for the Pc loop

Pc(s)/h(s) = K_h [ (1 - phi)/(tau_c s + 1) + phi/(tau_f s + 1) ]. The model is fitted to +3 % lift steps of the quasi-1D model with the tank frozen at 50.5 bar (SIM, `engine_S230/plant_valve_to_pc_v2.json`).

| Throttle % | Lift h0 [mm] | Pc0 [bar] | K_h [bar/mm] | dF/dh [N/mm] | tau_c [ms] | tau_f [ms] | phi |
|---|---|---|---|---|---|---|---|
| 100 | 1.900 | 25.03 | 7.55 | 159 | 4.0 | 107 | 0.060 |
| 50 | 0.751 | 13.22 | 13.65 | 290 | 4.0 | 181 | 0.094 |
| 25 | 0.366 | 7.34 | 17.77 | 378 | 4.0 | 316 | 0.089 |
| 12.5 | 0.206 | 4.37 | 20.11 | 369 | 4.0 | 528 | 0.053 |

- The injection and vaporisation delay is 3-10 ms (ASSUMED).
- K_h grows 2.7x toward the floor, so a gain-scheduled closed Pc loop is needed.
- The slow fuel/thermal mode (0.3-1.5 Hz) lies inside the 2.3 Hz Pc-loop bandwidth of gnc.json v2 (OI-2).

### 3.5 Pintle force law, seat and seal (v2.3 review of Mechanical's pintle v2)

**Stem.** Mechanical reduced the stem through the seal from 4 mm to 3 mm.
- The stem area is not in the injector flow model. Flow passes the seat annulus; the stem only sets the bonnet pressure area. The throttle map is unchanged.
- Bonnet volume increases by 0.14 cm3. Stem conduction falls from 2.3e-3 to 1.3e-3 W/K, which leaves the head-end BC unchanged.
- Pressure areas: A_seat = 23.758 mm2; A_stem = 7.069 mm2.

**Force law.** + is the closing direction. Script: `src/needle_force_v2p3.py`; output `data/v2/needle_force_bounds_v2p3.{csv,json}`.
- Mechanical's v2-v2.2 law blends to the opening bound -dp A_stem after 0.1 mm of lift. This is L0. It is conservative for the closing check C1, but not for the opening check C2. The seat gap keeps metering at every lift, so a closing pressure force persists.
- L1 (central) uses the geometric throat. L2 (upper bound) uses the seated area at every lift.

Unlit at 70 bar, L1 gives 115.1 / 100.6 / 86.7 / 61.0 / 37.9 / 17.6 / 13.9 N at h = 0 / 0.5 / 1 / 2 / 3 / 4 / 4.2 mm. L2 stays at 115.1 N at every lift.

Bounds:
- Seated at 70 bar: +115.1 N.
- L0 open bound: -48.8 N.
- Hot-fire envelope over the map:
  - L0 minimum -38.1 N;
  - L1 -12.6 to +77.7 N;
  - L2 maximum +82.0 N.
- L1 and L2 differ by up to 163.9 N at MEOP above 0.1 mm lift.

Flashing at the gap moves the force toward L0. B-PNT-1 measures F(h, P).

Rule, adopted by the lead: C1 (spring closing) is evaluated on L0; C2 (servo opening) on L1, with L2 as the sensitivity case.

**Re-run with Mechanical's own code** (`pintle_inline_v34.py`, sha256/16 10f5130fb51147ea). L0 reproduces Mechanical exactly:
- v2: 0.59 / 0.05;
- v2.1: 0.593 / 0.05 / 0.082;
- v2.2: 0.597 / 0.537 / 0.047 / 0.094.

Table 3.4. C2 opening margins at the 7.4 V servo rail. The requirement is >= 1.5 (SIM with Mechanical's servo_torque).

| Configuration | Flight hot-fire line (L1 / L2) | Start to 0.3 mm, 70 bar (L1 / L2) | Start, 50.5 bar (L1 / L2) | Unlit full stroke at MEOP, ground (L1 / L2) |
|---|---|---|---|---|
| S3, 0.30/0.10, PTFE mu 0.20 (lead baseline at the time) | 1.47 / 1.37 | 1.32 / 1.28 | 1.50 / 1.46 | 1.11 / 0.81 |
| v2 spring, PTFE mu 0.18 (0.18/0.175) | 1.89 / 1.67 | | | |
| v2.1 spring, PTFE mu 0.10 (0.19/0.17) | 1.85 / 1.64 | | | |
| **Rolling guide, plain pins, 0.25/0.12 (adopted)** | **1.62 / 1.62** | | | |

Spring feasibility window (`src/pintle_spring_window_v2p3.py`, `data/v2/pintle_spring_window_v2p3.json`):
- Criteria: C1 >= 0 under L0 with the -10 % spring; flight C2 <= 0.60 N m under L1/L2 with the +10 % spring.
- PTFE mu 0.20: one feasible spring under L1 (0.21/0.15, MEOP assist only 0.004 N m) and none under L2. There is no robust spring.
- PTFE mu 0.10: 138 (L1) and 117 (L2) feasible springs.
- Rolling guide, hypothetical: 272/257 feasible springs with plain pins (T0 0.10-0.33 N m) and 335/322 with ball pins.
- The adopted 0.25/0.12 spring gives a MEOP closing assist of 0.108 N m and a nominal seat load of 292 N.
- The final guide and pins are Mechanical's. Their v2.3 run carries L1/L2 natively and supersedes these hypothetical rolling-guide numbers.

**Seat.** Metal-to-metal 17-4PH: a 15 deg cone on a 5.5 mm sharp-edged seat with a 0.3 mm lapped land (land area 5.184 mm2). It is not a polymer seat.

Table 3.5. Seat loads and land contact pressure (DERIVED). Normal factor on the land is 3.864 at mu 0 and 1.823 at mu 0.3.

| Case | S3 load [N] | Land pressure, mu 0 / 0.3 [MPa] | Adopted 0.25/0.12 load [N] | Land pressure, mu 0 / 0.3 [MPa] |
|---|---|---|---|---|
| -10 % spring, bench | 315.1 | 234.9 / 110.8 | 262.6 | 195.7 / 92.3 |
| nominal | 350.1 | 261.0 / 123.1 | 291.8 | 217.5 / 102.6 |
| +10 % | 385.1 | 287.0 / 135.4 | 321.0 | 239.3 / 112.9 |
| +10 % at MEOP 70 bar | 500.3 | 372.9 / 175.9 | 436.1 | 325.1 / 153.4 |
| +10 % at 7.5 MPa relief | 508.6 | 379.1 / 178.9 | 444.4 | 331.2 / 156.3 |
| +10 % at 10.5 MPa proof (ASSUMED 1.5x) | 558.7 | 416.4 / 196.5 | 494.5 | 368.6 / 173.9 |

Room-temperature Fty is 724 MPa for H1150 (LITERATURE-UNVERIFIED). Operating land pressure is 15-52 % of Fty under S3, and at most 331 MPa (46 %) with the adopted spring. The seat is elastic.

Hot soak. The lumped head bound with the CAD face disc gives 363-424 K in flight and 488 K on the ground. The disc band gives 339-586 K in flight and 424-685 K on the ground.
- Fty at 316 C is about 0.85 x the RT value (AS RECALLED), so the land sees 62 % of hot Fty.
- Creep is negligible below about 370 C for a 1 h soak (AS RECALLED; TO-VERIFY against maker data).
- A bare face (disc lost) reaches 836-996 K, above the 894 K H1150 ageing temperature. Inspect or re-harden the seat after any disc loss.

Conditions, all adopted by the lead:
- Needle and stem in H900, seat in H1150. The hardness difference counters galling (TO-VERIFY).
- Lapped contact band >= 0.24 mm all round, checked by bluing. A 0.15 mm band would reach 758 MPa at the relief load and coin the land; 0.24 mm gives 474 MPa.
- PFPE film on the land.
- Keep both parts 17-4PH. A Nitronic 60 seat would shift the seat line by about 16 um of lift per 300 K, and its annealed Fty (about 414 MPa, AS RECALLED) is close to the land pressure.

Self-locking. tan 15 deg = 0.268, so the cone wedges if the seat friction coefficient exceeds 0.27.

Table 3.6. Crack-open margin at MEOP against seat friction (Mechanical's servo_torque, guide amplification included).

| Configuration | mu 0 | 0.3 | 0.4 | 0.5 | 0.6 |
|---|---|---|---|---|---|
| S3, PTFE 0.20 | 1.68 | 1.55 | 1.31 | 1.17 | 1.08 |
| Rolling guide, 0.25/0.12 | 2.14 | 2.01 | 1.75 | 1.60 | 1.49 |

B-PNT-1 measures the break-out torque after a dwell closed at MEOP.

Polymer seat: not feasible. Land pressure of 111-379 MPa exceeds the compressive strength of PTFE (about 10-15 MPa), PCTFE (about 30-50 MPa) and PEEK (about 120 MPa), all AS RECALLED. PCTFE is also limited to about 150 C against the 339-586 K soak band.

Leak tightness:
- A lapped metal seat's leak rate cannot be predicted. The seat is pressure-assisted, so low pressure governs: spring only, 315 N, 18.2 N/mm.
- Proposed acceptance: <= 1 scc/min of N2 (TO-AGREE).
- Combustion ceiling for a coast: 10 % of the 8.74 g hard-start inventory over 22.2 s, i.e. 0.039 g/s.
- Until the leak is measured, the NC isolation valve stays closed during coasts (LEAD operating rule). Trapped-liquid relief stays.

**Rod seal.** A spring-energised PTFE-family seal is suitable in principle for a 3 mm rod in N2O at 7.0 MPa tank MEOP and 10.5 MPa proof (ASSUMED).
- Temperature range: from -88.5 C (N2O normal boiling point, venting; CoolProp) up to the bonnet temperature from Mechanical's FEA. The PTFE jacket limit is about 260 C (AS RECALLED).
- Vendor classes, all TO-VERIFY per part:
  - Trelleborg Turcon Variseal M2 (rod);
  - Saint-Gobain OmniSeal 103A class;
  - Parker FlexiSeal;
  - Bal Seal canted-coil.
- Specification:
  - virgin PTFE or an oxygen-compatible filled jacket;
  - Elgiloy, Hastelloy or 17-7PH spring;
  - oxygen-cleaned, PFPE lubricant only;
  - split or open gland;
  - rod Ra 0.1-0.2 um, H900.
- Friction is 1-5 N (DERIVED). Mechanical's ASSUMED 18.75 N is conservative.
- Price TO-QUOTE (Sønderborg DK-6400).

**Stem buckling.** Link compression is <= 385 N, i.e. 54 MPa on the 3 mm stem. Euler load over an ASSUMED 40 mm free length is 4.8 kN, a margin of 13. Mechanical confirms the free length.

**Operating rules** (LEAD 2026-10-12, sent to Electronics and GNC):
1. Hold the ignition lift until Pc confirms light; a no-light abort closes the pintle.
2. N2O cold flows go into a back-pressured catch volume; full-stroke checks use N2 at <= 3.5 MPa.
3. Keep the NC isolation valve closed during coasts until the seat leak rate is measured.

### 3.6 Failure case and the MEOP basis

Table 3.7. Pintle stuck at full stroke (4 mm), initial port (SIM, `full_stroke_failure_case_v2.json`).

| T [C] | P_v [bar] | Cd | Pc [bar] | F [N] | O/F | dP/Pc |
|---|---|---|---|---|---|---|
| 15 | 45.0 | 0.60 | 30.7 | 619 | 11.68 | 0.358 |
| 15 | 45.0 | 0.70 | 32.9 | 666 | 12.13 | 0.257 |
| 15 | 45.0 | 0.80 | 34.7 | 704 | 12.50 | 0.188 |
| 20 | 50.5 | 0.60 | 32.9 | 666 | 12.14 | 0.414 |
| 20 | 50.5 | 0.70 | 35.4 | 719 | 12.64 | 0.301 |
| 20 | 50.5 | 0.80 | 37.5 | 764 | 13.05 | 0.223 |
| 25 | 56.5 | 0.60 | 35.1 | 712 | 12.57 | 0.480 |
| 25 | 56.5 | 0.70 | 37.9 | 771 | 13.12 | 0.355 |
| 25 | 56.5 | 0.80 | 40.3 | 822 | 13.58 | 0.265 |
| 30 | 63.1 | 0.60 | 37.0 | 753 | 12.95 | 0.562 |
| 30 | 63.1 | 0.70 | 40.1 | 818 | 13.55 | 0.421 |
| 30 | 63.1 | 0.80 | 42.9 | 876 | 14.05 | 0.319 |

LEAD decisions taken on this basis:
- chamber MEOP 45 bar;
- proof 67.5 bar, which also covers a blocked nozzle at tank pressure (63.1 bar at 30 C) below yield;
- software Pc cap 25 bar;
- ECU over-pressure abort at about 30 bar.

## 4. Grain and internal ballistics

### 4.1 Regression law

No verified N2O/ABS (or N2O/PETG) regression law was found in the literature accessed. Design law: r = a G_ox^n, with:
- a = 5.77e-5 m/s (kg/m2/s)^-n, ASSUMED. It is anchored to about 1 mm/s at 300 kg/m2s for HTPB/N2O (Boughaba & Hendrick, EUCASS 2013, citing literature).
- n = 0.5, ASSUMED. The band 0.35-0.68 covers GOX polymer laws with n 0.50-0.68 (Zilliac & Karabeyoglu, AIAA 2006-4504).

Every result is checked at x0.6 and x1.5 on a. The quasi-1D model resolves the local flux G_ox(x). An alternative total-flux law is available, and a length exponent is not added separately.

Static fires T1-T2 measure (a, n) by mass loss and port bore at several fluxes. PETG has no law at all and needs its own tests.

### 4.2 Port geometry and length

The v1 helical port was rejected for two reasons:
- On the v1 B1 cycle it burned through (web -3.12 mm at 15.0 s).
- It is a roll-torque source.

The LEAD decision of 2026-10-12 is a centred straight round port, S230. The length was minimised under three constraints:
- residual web >= 1 mm at the x1.5 regression bound;
- thrust ceiling;
- gimbal sweep.

Initial G_ox at the head end is 491 kg/m2s at 100 %. No flooding or blow-off limit for N2O/ABS was found; T1 at 100 % checks it.

Table 4.1. Grain trade over the gnc.json v1 cycles (SIM, `grain_trade_v2.csv`).

| Variant | DC | Regression x | Impulse [N s] | O/F mean | Isp mean [s] | Web end [mm] | Min ceiling [N] | Fuel [kg] |
|---|---|---|---|---|---|---|---|---|
| S200 | A1 | 1.0 | 1855 | 10.39 | 185.4 | 9.47 | 549 | 0.090 |
| S230 (v2) | A1 | 1.0 | 1852 | 8.90 | 188.2 | 9.53 | 558 | 0.101 |
| S260 | A1 | 1.0 | 1851 | 7.77 | 190.3 | 9.58 | 565 | 0.113 |
| S200 | B1 | 1.5 | 2744 | 4.22 | 166.8 | 0.92 | 590 | 0.321 |
| S230 (v2) | B1 | 1.5 | 2745 | 3.65 | 163.2 | 0.94 | 593 | 0.369 |
| S260 | B1 | 1.5 | 2750 | 3.22 | 160.2 | 0.97 | 595 | 0.415 |
| v1 helix L200 | B1 | 1.0 | 2746 | 4.52 | 167.3 | -3.12 (burn-through at 15.0 s) | 579 | 0.303 |

### 4.3 Chambers, efficiency and model

Chambers:
- Pre-chamber 30 mm long: vaporisation and distribution at the head end.
- Post-chamber 40 mm long: mixing. The diameter of both is 53.9 mm.
- Initial free volume is 2.846e-4 m3 and L* is 1.92 m.
- At 100 % the mean port mixture stays oxidiser-rich along the whole port (exit O/F 10.4 against stoichiometric 8.17). Mixing finishes in the post-chamber and nozzle. At <= 50 % the mean O/F crosses stoichiometric inside the port (`chamber_port_state_v2.json` and figure).

eta_c* is 0.92, ASSUMED with a band of 0.85-0.96; no source specific to N2O/ABS was found. eta_cf is 0.975, ASSUMED.

The quasi-1D model (`src/grain_q1d.py`) couples:
- the tank, equilibrium or two-CV non-equilibrium;
- the feed loss and the Dyer pintle table;
- a chamber filling ODE with CEA c*(Pc, O/F) x eta_c*;
- N axial port cells holding D(x), G_ox(x), G(x), cumulative fuel and local O/F;
- the CEA Cf with Schmucker separation;
- the throat history from the erosion model.

Fuel response lags the quasi-steady law by the solid thermal time kappa/r^2, a first-order form (ASSUMED; physics after Karabeyoglu et al. 2005). Control is feed-forward inversion of the map every 10 ms, limited by the dP/Pc >= 0.25 ceiling and the 4 mm stroke.

Table 4.2. Operating points: S230, 20 C tank (50.5 bar), initial port 25 mm (SIM). Lift and dP/Pc come from the map row at 50 bar. T0 delivered = eta_c*^2 Tc.

| Throttle % | F [N] | Pc [bar] | O/F | mdot_ox [g/s] | mdot_f [g/s] | Isp_SL [s] | Lift [mm] | dP/Pc | Tc CEA [K] | T0 del. [K] |
|---|---|---|---|---|---|---|---|---|---|---|
| 100 | 500.0 | 25.01 | 10.43 | 241.0 | 23.1 | 193.1 | 1.916 | 0.91 | 3257 | 2757 |
| 75 | 375.0 | 19.10 | 8.99 | 179.0 | 19.9 | 192.2 | 1.252 | 1.55 | n/a | n/a |
| 50 | 250.0 | 13.20 | 7.34 | 119.1 | 16.2 | 188.4 | 0.755 | 2.74 | 3303 | 2795 |
| 40 | 200.0 | 10.85 | 6.58 | 95.9 | 14.6 | 184.6 | 0.588 | 3.58 | n/a | n/a |
| 25 | 125.0 | 7.33 | 5.32 | 62.6 | 11.8 | 171.4 | 0.367 | 5.80 | n/a | n/a |
| 20 | 100.0 | 6.16 | 4.85 | 52.0 | 10.7 | 162.5 | 0.301 | 7.10 | 3158 | 2673 |
| 15 | 75.0 | 4.98 | 4.34 | 41.7 | 9.6 | 149.0 | 0.238 | 9.02 | n/a | n/a |
| 12.5 | 62.5 | 4.37 | 4.06 | 36.5 | 9.0 | 140.2 | 0.207 | 10.43 | 2953 | 2500 |

Max-thrust point: c* delivered 1401 m/s, gamma 1.147, MW 28.72, chamber fill time constant 3.4 ms (DERIVED; the step fit gives 4 ms).

### 4.4 Duty-cycle results

Table 4.3. S230 over the gnc.json v2 cycles (published 20:34Z). The inputs were the 19:15Z working copy, whose F_N and F_cmd_N histories are identical to the published files (`inputs/gnc_v2_published_20261012T2034/MANIFEST.txt`). SIM, `data/v2/dc_gncv2wip/summary_v2.json`.

| DC | Regression x | Tank | Burn [s] | Impulse [N s] (GNC) | N2O [kg] | Fuel [kg] | O/F mean | Web end [mm] | Liquid left [kg] | Min ceiling [N] | Tracking rms [N] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | 1.0 | 3.17 L / 2.00 kg | 7.40 | 2528 (2504) | 1.222 | 0.137 | 8.95 | 8.17 | 0.477 | 578 | 22.85 |
| A1 | 1.5 | 3.17 L / 2.00 kg | 7.40 | 2528 (2504) | 1.126 | 0.198 | 5.69 | 6.01 | 0.579 | 598 | 21.89 |
| A1 | 0.6 | 3.17 L / 2.00 kg | 7.40 | 2539 (2504) | 1.334 | 0.084 | 15.80 | 10.22 | 0.359 | 556 | 21.89 |
| A2 | 1.0 | 4.02 L / 2.54 kg | 8.89 | 3080 (3057) | 1.493 | 0.164 | 9.11 | 7.18 | 0.667 | 579 | 21.96 |
| B1 | 1.0 | 3.87 L / 2.44 kg | 19.04 | 2871 (2842) | 1.437 | 0.242 | 5.93 | 4.57 | 0.641 | 581 | 17.54 |
| B1 | 1.5 | 3.87 L / 2.44 kg | 19.05 | 2868 (2842) | 1.379 | 0.355 | 3.89 | 1.31 | 0.702 | 594 | 16.73 |
| B2 | 1.0 | 2.87 L / 1.81 kg | 14.49 | 2078 (2050) | 1.043 | 0.182 | 5.74 | 6.55 | 0.499 | 584 | 20.62 |

No cycle is ever ceiling-limited (0.00 s). The A2 and B1 tanks are larger than the lead baseline (OI-1).

Table 4.4. S230 over the gnc.json v1 cycles (SIM; non-equilibrium tank with E 1000 in flight; ASSUMED 15 L ground tank for C and D).

| DC | Regression x | Burn [s] | Impulse [N s] | N2O [kg] | Fuel [kg] | O/F mean | Isp mean [s] | Web end [mm] | Liquid left [kg] | Min ceiling [N] | Min dP/Pc |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | 0.6 | 5.83 | 1863 | 0.985 | 0.062 | 15.87 | 181.4 | 11.19 | 0.110 | 533 | 0.51 |
| A1 | 1.0 | 5.83 | 1852 | 0.902 | 0.101 | 8.90 | 188.2 | 9.53 | 0.195 | 558 | 0.55 |
| A1 | 1.5 | 5.83 | 1860 | 0.833 | 0.148 | 5.63 | 193.3 | 7.75 | 0.268 | 579 | 0.60 |
| A2 | 1.0 | 7.73 | 2520 | 1.222 | 0.138 | 8.87 | 189.0 | 8.12 | 0.258 | 548 | 0.61 |
| B1 | 1.0 | 20.73 | 2748 | 1.391 | 0.251 | 5.54 | 170.6 | 4.30 | 0.607 | 581 | 0.79 |
| B1 | 1.5 | 20.74 | 2745 | 1.347 | 0.368 | 3.65 | 163.2 | 0.94 | 0.655 | 593 | 0.82 |
| B2 | 1.0 | 14.72 | 1994 | 1.007 | 0.181 | 5.58 | 171.2 | 6.60 | 1.026 | 623 | 0.81 |
| B2 | 1.5 | 14.72 | 1992 | 0.973 | 0.264 | 3.68 | 164.1 | 3.91 | 1.063 | 635 | 0.83 |
| C | 1.0 | 36.32 | 4230 | 2.161 | 0.404 | 5.35 | 168.2 | 0 (burn-through 46.4 s) | 6.943 | 638 | 5.08 |
| D | 1.0 | 49.81 | 13160 | 7.018 | 0.404 | 17.37 | 180.9 | 0 (burn-through 24.1 s) | 1.665 | 528 | 0.50 |

- A round port leaves no sliver; the residual fuel is the remaining web.
- Residual web rule: >= 1 mm at the x1.5 bound on every flight cycle. The ABS thermal layer kappa/r is 0.1-0.3 mm. B1 is the limiting cycle: 1.31 mm on gnc v2 and 0.94 mm on gnc v1 (OI-10).
- With one grain, ground cycles C and D burn through. The test plan splits C into two grain loads and D into three.
- The A1 cycle at x0.6 has a cumulative mean O/F of 15.9, beyond the clamp at O/F 14 used in the c* lookup. Its O/F and Isp are approximate.

### 4.5 All-max-thrust case

Table 2.2 above is the continuous 500 N case. The Pc(t) and F(t) history for the thermal load case is `data/v2/engine_S230_BL/maxthrust_BLtank_neqE1e+03_T20C.csv`.

## 5. Nozzle and throat erosion

### 5.1 Expansion ratio

Table 5.1. Ideal sea-level Isp [s] against eps, with Schmucker separation (CEA/DERIVED, `nozzle_perf_v2.json`).

| Throttle % | Pc [bar] | O/F | eps 1.5 | eps 2.0 | eps 2.5 | eps 3.0 | eps 4.0 |
|---|---|---|---|---|---|---|---|
| 100 | 25.01 | 10.43 | 206.0 | 215.6 | 220.9 | 224.1 | 226.8 |
| 50 | 13.20 | 7.34 | 203.6 | 210.6 | 213.4 | 213.9 | 211.2 |
| 20 | 6.16 | 4.85 | 183.5 | 182.5 | 177.3 | 175.4 | 175.4 |
| 12.5 | 4.37 | 4.06 | 163.9 | 158.2 | 158.2 | 158.2 | 158.2 |

Table 5.2. Separation and side-load bound (DERIVED, `nozzle_perf_v2.csv`). The side-load bound assumes half the circumference attached and half separated.

| Throttle % | eps | pe/pa | Schmucker psep/pa | Summerfield separation | Schmucker separation | eps_sep | Side-load bound [N] |
|---|---|---|---|---|---|---|---|
| 100 | 2.0 | 3.199 | 0.519 | no | no | n/a | 0 |
| 25 | 2.0 | 0.891 | 0.517 | no | no | n/a | 0 |
| 20 | 2.0 | 0.723 | 0.514 | no | no | n/a | 0 |
| 15 | 2.0 | 0.564 | 0.509 | no | no | n/a | 0 |
| 12.5 | 2.0 | 0.485 | 0.506 | no | yes (at the lip) | 1.94 | 0.0 |
| 20 | 3.0 | 0.383 | 0.449 | yes | yes | 2.64 | 3.5 |
| 15 | 3.0 | 0.297 | 0.443 | yes | yes | 2.17 | 8.7 |
| 12.5 | 3.0 | 0.254 | 0.440 | yes | yes | 1.94 | 11.2 |
| 12.5 | 1.8 (eroded throat) | 0.580 | 0.529 | no | no | n/a | 0 |

Decision: eps 2.0 (DERIVED). The flow stays attached down to 15 %, with incipient lip separation at 12.5 % (Schmucker eps_sep 1.94; Summerfield attached). The cost against eps 3 is 8.5 s of ideal Isp at 100 % (215.6 against 224.1).

### 5.2 Contour

Conical nozzle, `data/v2/nozzle_contour_v2.csv` as (x_face, x_throat, r) in metres. The v1 shape is shifted +30 mm for S230. In CAD, +Z forward gives z = x_exit_face - x_face.
- Convergent half-angle 45 deg (DERIVED, compact).
- Throat radius of curvature 10.293 mm upstream (1.5 Rt) and 2.621 mm downstream (0.382 Rt), per Rao 1958 and Huzel & Huang practice (LITERATURE).
- Divergent half-angle 15 deg. Divergence factor lambda = (1 + cos a)/2 = 0.983 (LITERATURE).
- Throat at x_face 0.32767 m, exit at 0.33862 m. Gas-path length from the injector face to the exit is 0.3386 m.

### 5.3 Graphite insert

Specification (DERIVED from the density and porosity sensitivity of the erosion model):
- isomolded or extruded fine-grain graphite;
- bulk density >= 1.80-1.85 g/cm3;
- ash <= 0.1 %.

The grade and its allowables come from the maker's datasheet: TO-QUOTE (Sønderborg DK-6400). The envelope is Mechanical's CAD v3.1: 44 mm OD with a 30 x 6.5 mm aft spigot through a 6 mm lip. The gas side is unchanged; the models used the v3.0 slice of 44 x 32 mm.

### 5.4 Erosion per flight and life

Model (`src/nozzle.py`, `src/erosion_dc.py`):
- 1-D radial transient conduction at the throat.
- Bartz h_g(T_w) and a radiation band.
- Semi-global surface kinetics as tabulated by Rotondi et al., JPP 2024: C + H2O, C + CO2, C + OH, C + O, and Nagle-Strickland-Constable for O2.
- Film mass transfer (Chilton-Colburn).

Three estimates are run:
- Nominal: delivered composition.
- Conservative: CEA ideal composition with T0 = Tc.
- Literature-scaled: measured N2O/HDPE rates, scaled with (Pc/35 bar)^0.68 and binned by O/F, after a 1.5 s onset.

Table 5.3. Throat recession per flight over the gnc.json v1 cycles with S230 (SIM, `erosion_S230/erosion_dc_v2.json`).

| Duty cycle | Nominal [mm] | Nominal dAt/At [%] | Nominal Tw max [K] | Conservative [mm] | Conservative dAt/At [%] | Conservative Tw max [K] | Literature-scaled [mm] | q_in max [MW/m2] |
|---|---|---|---|---|---|---|---|---|
| A1, x1 | 0.040 | 1.16 | 1514 | 0.169 | 4.98 | 1761 | 0.159-0.237 | 27.1 |
| A2, x1 | 0.057 | 1.66 | 1561 | 0.241 | 7.16 | 1825 | 0.275-0.400 | 27.1 |
| B1, x1 | 0.028 | 0.82 | 1685 | 0.176 | 5.20 | 1966 | 0.065-0.101 | 27.1 |
| B2, x1 | 0.020 | 0.59 | 1571 | 0.126 | 3.71 | 1825 | 0.049-0.081 | 27.1 |
| A1, x1.5 | 0.017 | 0.49 | 1587 | 0.121 | 3.57 | 1837 | 0.033-0.080 | 29.3 |
| A1, x0.6 | 0.035 | 1.02 | 1437 | 0.151 | 4.45 | 1663 | 0.209-0.298 | 25.3 |

Life rule (DERIVED): replace the insert when dA_t/A_t reaches 5 %, measured with a pin gauge or bore scan after every firing. That allows 1.0 (conservative) to 4.3 (nominal) A1 flights per insert.

Effect of erosion:
- 5 % throat growth changes the Pc-to-thrust map by about 5 % (F = Cf Pc At) and lowers eps toward 1.9.
- An 11 % growth (eps 1.8) costs 3.1 s of ideal Isp at 100 %.
- The Pc loop and the map should use the measured bore.

## 6. Heat loads

### 6.1 Gas-side boundary conditions

The Bartz (1957) closed form uses CEA frozen transport properties, the recovery factor Pr^(1/3) and T_aw from the delivered T0 (`src/heat.py`, `src/thermal_bc_v2.py`).

Table 6.1. Boundary conditions for the FEA (DERIVED, `thermal_bc_summary_v2.json`).

| Point | Throttle % | Pc [bar] | O/F | T0 del. [K] | Peak q at Tw 600 K [MW/m2] | Peak h_g [W/m2K] | x of peak from throat [mm] | T_aw [K] | CSV |
|---|---|---|---|---|---|---|---|---|---|
| max | 100 | 25.01 | 10.43 | 2757 | 21.92 | 10259 | 0.0 | 2737 | thermal_bc_max_v2.csv |
| 75pct | 75 | 19.10 | 8.99 | 2783 | 18.09 | 8362 | 0.0 | 2763 | thermal_bc_75pct_v2.csv |
| 50pct | 50 | 13.20 | 7.34 | 2795 | 13.78 | 6338 | 0.0 | 2774 | thermal_bc_50pct_v2.csv |
| 20pct | 20 | 6.16 | 4.85 | 2668 | 7.43 | 3640 | -0.5 | 2642 | thermal_bc_20pct_v2.csv |
| floor12p5 | 12.5 | 4.37 | 4.06 | 2496 | 5.34 | 2865 | -0.5 | 2463 | thermal_bc_floor12p5_v2.csv |

CSV columns:
- x_face, x_throat, r, region, A/At, Mach, p, T_static, T_aw;
- h_g at Tw 600 K and 1500 K;
- h_g with equilibrium properties;
- q_conv, the q_rad band, and an uncertainty factor.

Uncertainty factors:
- nozzle 0.7-1.3;
- pre- and post-chamber 0.5-2. Bartz is outside its validity there (recirculating flow); h_g is 889 W/m2K and q is 1.9 MW/m2 at 100 %.

Equilibrium-property Bartz gives 3.0x h_g at the throat (30.9 kW/m2K). It is kept as an upper sensitivity, not as the baseline: with equilibrium properties the driving potential should be an enthalpy difference.

Radiation: gas plus soot emissivity 0.05-0.20 (ASSUMED), path 0.9 D. That gives 0.12-0.49 MW/m2 at the throat and 0.16-0.65 MW/m2 in the chamber.

Cold-wall start transient (coupled insert model): incident 27.1-31.6 MW/m2.

Grain zone: while the web is >= 1 mm, the burning fuel surface (about 700-900 K, ASSUMED) shields the case and liner. After burnout, which happens only in the ground cycles, use the post-chamber rows.

Duty-cycle timing:
- Pc(t), O/F(t), F(t) and the coasts are explicit in `data/v2/dc_g3/*.csv` (gnc v1) and `data/v2/dc_gncv2wip/*.csv` (gnc v2).
- The head end has `headend_bc_<DC>_v2.csv`.

### 6.2 Throat insert soak-back and the retention lip (OI-5)

Table 6.2. Soak into a lumped 0.15 kg retainer (DERIVED lumped/1-D, insert 0.081 kg, v3.0 geometry; the v3.1 insert is larger, so FEA is required).

| DC | Contact h [W/m2K] | Retainer | Last shutdown [s] | Tw at shutdown [K] | Insert mean [K] | Retainer at shutdown [K] | Retainer peak [K] | Peak after shutdown [s] | Retainer at 900 s [K] |
|---|---|---|---|---|---|---|---|---|---|
| B1 | 2000 | Al | 20.7 | 1521 | 1229 | 709 | 920 | 33 | 625 |
| B1 | 2000 | steel | 20.7 | 1569 | 1292 | 890 | 1084 | 22 | 612 |
| B1 | 500 | Al | 20.7 | 1646 | 1385 | 477 | 847 | 102 | 616 |
| B1 | 150 | Al | 20.7 | 1707 | 1467 | 359 | 758 | 255 | 619 |
| A1 | 2000 | Al | 28.0 | 1176 | 877 | 538 | 663 | 32 | 509 |
| A1 | 2000 | steel | 28.0 | 1224 | 929 | 632 | 774 | 24 | 517 |
| A1 | 500 | Al | 28.0 | 1254 | 962 | 444 | 634 | 97 | 505 |
| A1 | 150 | Al | 28.0 | 1326 | 1042 | 354 | 588 | 251 | 505 |

Reading, per the lead note of 2026-10-12:
- 240 C (513 K) is Mechanical's v3.1 allowable for the aluminium lip at 51 MPa.
- A 0.15 kg aluminium retainer peaks at 588-920 K, above that allowable. About 0.6 kg of aluminium (about 540 J/K) in good contact gives 435-532 K.
- The steel rows (774-1084 K) are to be compared with a steel temperature-dependent allowable. That allowable is not defined here. They are not a failure.

Governing cases (LEAD), with numbers from `soakback_relight_v2.csv` (DERIVED). TS-1 is the relight after the MECO coast with pressure, at Pc 25 bar (normal) and 45 bar (MEOP):
- A cycles, coasts of 11.3-22.2 s treated as adiabatic.
- Retainer at relight: 302-558 K with aluminium brackets; 324-540 K with a 0.30 kg steel retainer.
- At the landing-burn Pc maximum (17.7-22.5 bar): 303-562 K (Al).
- The in-burn maximum, 305-597 K (Al), occurs at the end of the landing burn at Pc 1.0-2.9 bar.
- The aft land behind 5 mm of phenolic is at 303-335 K at relight.

TS-2 is the post-landing soak judged for reuse (3600 s, A and B cycles):
- Retainer peak 408-920 K, 0-3195 s above 150 C.
- Aft land peak 493-699 K, 874-2106 s above 150 C.

Action (Mechanical): choose retainer material, mass and interlayer. Mechanical's thermal FEA of the v3.1/v3.2 insert supersedes these lumped bounds.

### 6.3 Post-chamber wall (OI-4)

Table 6.3. Phenolic liner plus 3.175 mm 6061 case (DERIVED 1-D; no char or ablation credit and no axial conduction, so conservative).

| DC | Liner | h_g | Case peak [C] | Time of peak [s] | Case at last shutdown [K] | Liner surface max [K] |
|---|---|---|---|---|---|---|
| A1 | 1.6 mm | x1 / x2 | 364 / 452 | 51 | 507 / 556 | 1956 / 2238 |
| A1 | 3.0 mm | x1 / x2 | 287 / 353 | 90 | 416 / 441 | 1956 / 2238 |
| A1 | 5.0 mm | x1 / x2 | 220 / 269 | 166 | 332 / 341 | 1956 / 2238 |
| B1 | 1.6 mm | x1 / x2 | 641 / 780 | 41 | 757 / 874 | 2044 / 2331 |
| B1 | 3.0 mm | x1 / x2 | 474 / 563 | 82 | 464 / 508 | 2147 / 2406 |
| B1 | 5.0 mm | x1 / x2 | 360 / 426 | 160-161 | 321 / 330 | 2160 / 2416 |

Every case exceeds the 192 C aft-land allowable. The insulator thickness and material come from Mechanical's thermal FEA with the BC CSVs (band x0.5-2).

### 6.4 Head end and servo (OI-15)

Lumped head bound: T_aw = T0, no char credit, gnc v1/v2 A1/A2/B1, h_g x0.5-2. CAD v3.2 has a 2 mm face disc and a 0.44 kg head.

| Case | Head temperature |
|---|---|
| At relight | 37-66 C (x1: 46-55 C) |
| Maximum in flight | 41-110 C (x1: 53-82 C) |
| Post-landing soak peak | 66-190 C, at 61-65 s after the last shutdown |
| Ground DC-C | 106-200 C in operation; soak peak 151-272 C |

Heat into the head in flight (CAD disc, x1):
- 7.8-18.3 kJ through the face;
- 7.4-12.2 kJ through the pre-chamber case joint;
- N2O removes 2.5-5.7 kJ.

The forward case node behind 1.6 mm of phenolic reaches 106-454 C in flight; this joins OI-4.

Consequence: the HV69 mount (-10 to 60 C rating; 50 C mount limit in flight) must not rely on a cool head. Measures:
- keep the 2 mm face disc;
- a low-conductance bracket foot (G10 or PEEK washers, stainless or titanium screws);
- consider a thicker pre-chamber insulator;
- at T1, thermocouples on the face-disc back, head top, bracket foot and servo case.

## 7. Ignition, restart, start-up and shutdown

### 7.1 Trade and choice

Criterion weights (engineering judgement, DERIVED, `ignition_v2.json`):
- restarts >= 3: 3;
- reliability with N2O: 3;
- hard-start risk: 2;
- mass on the gimbal: 1;
- electrical energy and HV: 1;
- extra fluids or hazmat: 2;
- buildability and cost: 2;
- evidence base: 2.

| Option | Score | Main reasons |
|---|---|---|
| Torch, N2O/propane, spark | 0.800 | Independent of grain state. A hot jet of about 3 kW for 0.3-0.6 s. Restarts limited only by propane. Needs a propane cylinder, 2 NC solenoids, 2 check valves and a plug. Widely used on amateur and university hybrids. |
| Arc-ABS (USU type) | 0.675 | No extra fluid. Relights are shown with GOX; with N2O the published work needed more arc power or an O2 assist (LITERATURE-UNVERIFIED). Electrodes in every grain. 200-1000 V class supply. |
| Pyrotechnic cartridges | 0.637 | Excellent first start, but one cartridge per start, debris, and explosives rules in Denmark (TO-VERIFY). |
| Catalytic N2O decomposition | 0.525 | 50-200 W preheat for minutes. Bed poisoning. Decomposition can propagate upstream into the feed. |

Decision: the spark-ignited N2O/propane torch, firing radially into the pre-chamber.

Research proposal, arc-ABS:
- Hypothesis: arc ignition of printed ABS with N2O meets >= 3 starts and +/-50 ms latency scatter with no propane system.
- Comparator: the torch.
- Evidence: GOX literature only.
- Refutation criterion: in a bench series, any no-light, or latency scatter above +/-50 ms.

### 7.2 Torch specification

Sizing is DERIVED/CEA (`ignition_v2.json`):
- Operating point: torch Pc 3 bar, O/F 5.5, throat 2 mm, c* 1586 m/s, Tc 2852 K.
- Flow: mdot 0.594 g/s, of which propane 0.091 g/s and N2O 0.503 g/s; enthalpy flux 3.03 kW.
- Per 0.6 s start: 0.055 g propane and 0.302 g N2O.
- Orifices:
  - N2O 0.131 mm at 20 C (Dyer model, Cd 0.65 ASSUMED; 0.128-0.137 mm over 10-25 C);
  - propane 0.254 mm (Cd 0.80 ASSUMED);
  - both calibrated by weighing.
- Torch Pc of 3 bar keeps the outlet choked into a cold chamber and stays below the propane vapour pressure down to about 0 C (4.7 bar).
- Envelope (for Mechanical): body <= 45 mm long and <= 20 mm diameter, on a radial boss at x_face 0.015 m, axis inclined 30 deg inward and aft.
- Electrical (for Electronics): 12 V; coil primary peak 4 A; spark 50 mJ at 50 Hz for 0.5 s; two solenoids at 12 V, 0.8 A each, for 0.6 s; 15 J per start.
- Mass: 0.2-0.3 kg (ASSUMED).
- Starts: >= 3 per flight, limited by propane and N2O consumption.

### 7.3 Sequence

Arm preconditions:
- tank at 15-25 C;
- pintle seated, encoder healthy;
- isolation valve closed;
- continuity of the spark primary and both solenoids;
- Pc reads ambient +/- 0.1 bar. This replaces gnc.json's "chamber purged": no purge gas is carried in flight (OI-12).

Start sequence (t from the start command):
- t = -0.8 s, unprimed line only: 0.10 mm bleed lift before the isolation valve moves; valve ramp >= 0.3 s.
- t = -0.3 s: primed line, open the isolation valve with the pintle seated. Unprimed line: the valve is now fully open and the pintle returns to its seat. Flow is vapour-first through a warm line.
- t = 0: torch solenoids open. t = 0.02 s: spark train starts. t = 0.10 s: flame confirmation (photodiode or 0.25 mm thermocouple, Electronics selects).
- t = 0.12 s: pintle to the ignition lift, 12.5-20 % flow (about 0.2-0.3 mm). The lift is held until Pc confirms (LEAD rule).
- t = 0.35 s: ignition check. Pc must exceed 3.0 bar abs (combustion gives 4.4-6.2 bar; cold N2O flow about 1.5 bar). Otherwise ABORT.
- After the check: ramp at <= 2500 N/s. This is a cap; the drive must deliver >= 2 F_max/s.
- t = 0.4 s: propane solenoid closed before Pc exceeds 5 bar. t = 0.6 s: N2O torch solenoid closed and spark off.

No-light abort:
- pintle, torch and isolation valve all close;
- wait >= 5 s for the chamber to vent N2O, with no retry into a pooled chamber;
- one automatic retry in flight only if the GNC margin permits; on the ground, safe the stand.

The hard-start inventory, the N2O admitted at the ignition lift before Pc confirms, is 8.74 g (SIM).

Shutdown:
- the pintle closes at full drive speed; the closing speed is set by the ENG-05 tail-off (§3.3);
- the isolation valve closes after the pintle seats (<= 0.15 s);
- trapped liquid is relieved;
- the chamber vents through the nozzle, and the grain smoulders briefly.

Relight:
- same sequence from t = 0, after the settling check (§2.4);
- the torch fires into a hot, fuel-rich chamber.
- The isolation valve is closed during coasts (LEAD rule, §3.5). The v2.3 sequence text still says it "may stay open"; see §12.

Flashback:
- a check valve on each torch line (cracking <= 0.3 bar) rated to 45 bar and hot gas;
- the torch body is sized for MEOP and checked for 30 s exposure (Mechanical);
- no N2O purge through the torch during the main burn;
- no heat source or adiabatic compression upstream of the injector;
- clean, PFPE-lubricated hardware only.

Purge: ground tests use an N2 purge of 5-10 s after shutdown and before a re-start attempt. In flight, no purge gas is carried.

Model transients (SIM, ASSUMED torch-to-main delay of 0.10 s and 30 % preheated regression):
- relights in A1/A2 reach 10 % thrust at 0.10-0.11 s and 90 % at 0.28-0.29 s;
- the DC-D first start has t10-90 of 0.04 s;
- step starts to 12.5 % / 20 % reach 90 % at 0.52-0.53 / 0.43-0.44 s for any drive speed.

Ignition delay is the least certain input.

## 8. Combustion stability

Table 8.1. Feed-coupled (chug) stability and acoustic frequencies (DERIVED, `stability_v2.json`). Model: double-time-lag (Crocco/Summerfield class) with the hybrid fuel path. Karabeyoglu-type hybrid low-frequency modes are not modelled.

| Port [mm] | Throttle % | Pc [bar] | O/F | dP/Pc | GM (tau 1 ms) | GM (tau 10 ms) | tau_crit | Thermal lag [ms] | f thermal lag [Hz] | f Helmholtz [Hz] | f 1L [Hz] | f 1T [Hz] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 100 | 25.01 | 10.43 | 0.93 | 21.8 | 4.7 | inf | 73 | 2.2 | 1125 | 1460 | 10407 |
| 25 | 75 | 19.10 | 8.99 | 1.58 | 34.0 | 7.5 | inf | 99 | 1.6 | 1138 | 1477 | 10524 |
| 25 | 50 | 13.20 | 7.34 | 2.78 | 56.8 | 12.5 | inf | 149 | 1.1 | 1155 | 1499 | 10686 |
| 25 | 25 | 7.33 | 5.32 | 5.86 | 106.0 | 23.7 | inf | 283 | 0.6 | 1180 | 1532 | 10916 |
| 25 | 20 | 6.16 | 4.85 | 7.18 | 121.5 | 27.2 | inf | 340 | 0.5 | 1186 | 1539 | 10965 |
| 25 | 12.5 | 4.37 | 4.06 | 10.54 | 172.4 | 38.6 | inf | 485 | 0.3 | 1190 | 1544 | 11003 |
| 38 | 100 | 25.01 | 10.43 | 0.93 | 31.9 | 5.6 | inf | 170 | 0.9 | 1710 | 1460 | 10407 |
| 38 | 12.5 | 4.37 | 4.06 | 10.54 | 251.6 | 45.5 | inf | 1121 | 0.1 | 1808 | 1544 | 11003 |

Requirement (DERIVED): injector dP/Pc >= 0.25 everywhere. This is the ceiling rule; the minimum on the flight cycles is 0.50-0.83.

Chug:
- the gain margin is >= 4.7 at a 10 ms delay;
- the critical delay is infinite at every point;
- the pintle makes the floor the stiffest point.

Acoustics:
- 1L is about 1.5 kHz, Helmholtz 1.1-1.8 kHz and 1T about 10-11 kHz;
- all are far above the actuator band;
- the Pc sense line (>= 144 Hz) sits between the loop band and the acoustics.

Hybrid low-frequency modes:
- Thermal-lag and boundary-layer coupled modes fall in a 0.3-2 Hz band, which overlaps the slow plant mode (§3.4).
- Their amplitude is not predicted; the solid-phase response model is not included.
- Mitigation: the pre- and post-chambers, and a closed Pc loop with gain scheduling.
- Test requirement: T2 and T3 with 1 kHz Pc logging at every throttle level.

## 9. N2O hazard list

| # | Hazard | Mechanism and numbers | Control |
|---|---|---|---|
| H1 | Exothermic decomposition | N2O -> N2 + 1/2 O2 releases about 1.86 MJ/kg (hf N2O(g) +82 kJ/mol, NIST, LITERATURE). It is triggered by heat, adiabatic compression, catalytic surfaces or a hot cavity. | No heat source upstream of the injector. No N2O purge through a hot torch. Clean, PFPE-lubricated hardware only. Keep combustion and decomposition out of the feed (check valves; pintle seated before the valve opens on a hot chamber). |
| H2 | Adiabatic compression on priming | A dead-ended line compressed by a fast valve reaches 847-913 K (N2) or 614-646 K (N2O vapour) at 45-60 bar (Table 2.7). | Priming rule (bleed lift before the valve moves; valve ramp >= 0.3 s). No fast-opening valves into vapour-filled lines. |
| H3 | Trapped liquid (hydraulic lock) | Liquid between closed valves warms and its pressure rises steeply. | Relief <= 7.5 MPa between the isolation valve and the pintle. Relief on every lockable volume of the ground panel. |
| H4 | Near-critical tank | Tc 36.4 C, Pc 72.5 bar. Psat is 63.1 bar at 30 C, near the 70 bar tank MEOP. Properties change steeply and CoolProp/ESDU diverge (§2.1). | Condition to 15-25 C. Heater blanket with an independent over-temperature cut-off. Sun and heat shielding. Tank relief and burst disc per Mechanical. |
| H5 | Particles and galling debris | Particles in oxidiser service are ignition sources, and the metal-to-metal 17-4PH seat can gall. | Filter <= 15 um. H900/H1150 hardness difference, PFPE film. Oxygen cleaning of every wetted part. Inspect the seat after B-PNT-1 cycling. |
| H6 | Material compatibility | Hydrocarbon greases and some elastomers are incompatible with oxidisers. | PTFE, PCTFE, PFPE. Elastomers only where the maker rates them for N2O (TO-VERIFY per part). No silicone or hydrocarbon lubricants. |
| H7 | Cold burns and embrittlement | Venting liquid reaches -88.5 C at 1 atm (CoolProp). | Gloves and face shield. Seals and polymers rated for venting temperatures. |
| H8 | Asphyxia and anaesthetic exposure | N2O displaces air and is an anaesthetic gas. | Fill and vent outdoors or in ventilated areas. Vent lines routed away from people. |
| H9 | Pooled N2O in the chamber after a no-light | A later spark into pooled oxidiser causes a hard start. | Abort waits >= 5 s for venting, with no retry into a pooled chamber. Ground N2 purge before a re-start. The hard-start inventory is 8.74 g at the ignition lift. |
| H10 | Seat leak during coast | Leaked liquid flashes and leaves vapour in the feed, risking a hard start at relight. | NC valve closed during coasts until the leak rate is measured (proposed <= 1 scc/min N2; ceiling 0.039 g/s). |
| H11 | Over-pressure | A stuck-open pintle gives 30.7-42.9 bar Pc; a blocked nozzle gives tank pressure. | MEOP 45 bar, proof 67.5 bar, software cap 25 bar, abort at about 30 bar. Pc transducer range per OI-6. |
| H12 | Combustion products | Fuel-rich exhaust and a smouldering grain release CO and nitrogen-containing species (ABS contains acrylonitrile). | Remote operation. Treat the stand area as toxic until ventilated. |
| H13 | Pressure-system failure | Hose whip; tank or fitting burst. | Restrained hoses. Proof testing per Mechanical. Remote filling. Exclusion zone set by the founders under local rules. |

## 10. Cold-flow and static-fire test plan

Physical execution belongs to the founders. Combustion supplies the method, the measurands and the acceptance numbers. Every N2O test is remote, uses metal hardware, and vents into a back-pressured catch volume (LEAD rule).

| ID | Test | Hardware | Measured | Acceptance / use |
|---|---|---|---|---|
| CF-0 | PETG fit-check and low-pressure water visualisation | PETG copies of the pintle body, needle and head | Assembly, stroke and linkage kinematics; spray fan shape and symmetry against lift; gross leak paths; sensor port positions | Qualitative only (see the limits below) |
| CF-1 | Water cold flow, metal injector | Machined pintle, Coriolis or weigh tank | Single-phase Cd(h) at several dP; lift repeatability and hysteresis | Cd_liquid map; input to CF-3 |
| CF-2 | N2 flow and leak tests | Metal pintle and valves | Seat leak at 5 and 70 bar, before and after cycling and after a soak; full stroke with N2 at <= 3.5 MPa; filter and valve dP | Leak <= 1 scc/min N2 (proposed, TO-AGREE); valve Cv >= 3, filter Cv >= 2.2 |
| B-PNT-1 | Pintle bench (Mechanical/Electronics; combustion items listed) | Flight-like pintle and HV69 | F(h, P) at 3.5 / 5.5 / 7.0 MPa (N2, then N2O) by load cell or servo current; break-out after a dwell closed at MEOP; closing time at 25 bar and MEOP; guide friction; HV69 travel >= 103 deg; unpowered spring closing at the MEOP-equivalent needle load | C2 >= 1.5 under the measured law; C1 >= 0; ENG-05 tail-off re-run with the measured closing curve |
| CF-3 | N2O cold flow into a back-pressured catch volume | Metal injector, flight valve, filter and hose | mdot(h, P_tank, T) at 15 / 20 / 25 C with back-pressure 1-25 bar; feed pressure oscillations; line temperature during priming | Cd_eff against Dyer >= 0.41; maps re-run with the measured Cd |
| IGN-1 | Torch bench | Torch, solenoids, check valves | Orifice flows by weighing at 10 / 20 / 25 C; spark reliability; flame-confirmation sensor; latency and its scatter over a series (proposed >= 30 lights, ASSUMED sample size); torch body temperature over 30 s at Pc | Zero no-lights in the series; latency scatter within +/-50 ms |
| T1 | Short static fire, 3-5 s at 50-100 % | Flight-like engine on a stand with a 6-axis balance or two load cells | Pc (1 kHz), F, roll torque (resolution well below 0.02 N m), thrust misalignment, mdot_ox (tank load cell), grain mass and bore before and after, throat bore, thermocouples (face-disc back, head top, bracket foot, servo case, post-chamber case, retainer) | First (a, n) and eta_c* point; RCS decision (LEAD: delete only if roll torque <= 0.02 N m); head-end BC replaced by measurement |
| T2 | Throttle steps 100 -> 50 -> 25 % | As T1 | Plant K_h and tau; low-frequency modes; regression at several fluxes | (a, n) band; Pc-loop tuning |
| T3 | Floor holds at 20 % and 12.5 % | As T1 | Combustion efficiency and stability at G_ox 25-74 kg/m2s; lip separation and side load; Isp | Stretch floor accepted or rejected |
| T4 | Duty cycle with coasts and relights (DC-D: 3 starts, grain split into 3 loads; DC-C into 2) | As T1 | Relight latency, soak temperatures, erosion per cycle | Erosion and life rule; TS-1 and TS-2 data |

What a PETG cold-flow part can and cannot do:
- It can:
  - check fit, stroke and linkage kinematics before metal is cut;
  - show the spray-fan shape and symmetry against lift with water at a few bar at room temperature;
  - check sensor and port positions;
  - check how the parts are handled.
- It cannot:
  - carry N2O at all (oxidiser compatibility, ignition hazard);
  - represent flashing two-phase flow;
  - survive the -88.5 C venting temperature or the 45-70 bar pressures;
  - stand in for the metal seat in leak or break-out tests;
  - give an acceptance Cd, because its surface finish, sharp edges and land differ from the machined part;
  - stand in for the metal under force-versus-lift loads, because it bends and creeps;
  - represent any thermal or combustion behaviour.

## 11. Unknowns

Each unknown is listed with the test that closes it.

1. N2O/ABS regression law (a, n) and its band: T1-T2.
2. Pintle Cd for two-phase N2O at every lift: CF-1 water, then CF-3 N2O. Acceptance Cd_eff >= 0.41.
3. eta_c* of the straight port at O/F 4-10 (assumed 0.92, band 0.85-0.96), including the 1-2 % liquid-N2O c* penalty: T1-T2.
4. Low-flux combustion at the 12.5 % stretch floor (G_ox about 25-74 kg/m2s): T3.
5. Ignition delay with the torch (assumed 0.10 s torch-to-main plus 30 % preheat): IGN-1, T1.
6. Graphite grade, density and erosion kinetics: bore measurement after each firing.
7. Residual roll torque and thrust misalignment of the straight port: T1.
8. Plume afterburning and radiation: the CFD gives fast-chemistry bounds only (05-plume-cfd).
9. Head-end gas temperature and heat transfer. The bound uses T_aw = T0 and Bartz outside its validity: T1 thermocouples.
10. Pintle closing time under load at 25 bar and at MEOP: B-PNT-1.
11. Needle pressure force against lift (L0-L2 differ by up to 163.9 N at MEOP): B-PNT-1 with N2, then N2O.
12. Seat friction, break-out after a dwell at MEOP, and leak rate: B-PNT-1 and CF-2.
13. N2O transport properties (CO2 surrogate) in the tank heat-transfer closure, and the tank enhancement factor E: tank pressure history in T1-T4.
14. PETG regression law and grain design: only if the backup is used.

## 12. Remaining mismatches and open interface issues

| ID | Item | Combustion value | Other value | Owner / status |
|---|---|---|---|---|
| OI-1 | N2O load | Lead baseline 2.00 kg / 3.17 L (A1 flies it) | gnc.json v2 sizes A2 at 2.54 kg and B1 at 2.44 kg (B2 1.81 kg) | GNC re-runs A2/B1 on 3.17 L, or the lead re-opens the tank size |
| OI-2 | Engine map in the GNC Monte Carlo | throttle_map_v2.csv plus the plant fit (K_h x2.7) | gnc.json v2 flies the v1 map x relay factors | GNC re-runs; latency and repeatability measured at T1/T3 |
| OI-3 | Grain in CAD | S230, 0.404 kg, gas path 0.3386 m | CAD v2 shows L 0.200 m, 0.369 kg | Mechanical CAD v3.x and mass budget |
| OI-4 | Post-chamber insulator | Case 220-269 C (A1) and 360-426 C (B1) behind 5 mm | Aft-land allowable 192 C | Mechanical thermal FEA |
| OI-5 | Insert retention lip | Al retainer 0.15 kg: 588-920 K | Al lip allowable 240 C at 51 MPa; steel allowable undefined | Mechanical retainer choice and FEA (TS-1, TS-2) |
| OI-6 | Pc transducer | MEOP 45 bar, proof 67.5 bar, failure up to 42.9 bar; <= 0.1 bar resolution near 3 bar | electronics.json v1: 0-34.5 bar | Electronics selects 0-69 bar, or accepts saturation and confirms proof survival |
| OI-7 | Valve and filter | Isolation Cv >= 3; filter <= 15 um, Cv >= 2.2 | v1 Cv 1.5 / 40 um; CAD v3.3/v3.4 TC-04 still shows a 40 um screen | Mechanical CAD v3.4 or an in-line housing; TO-QUOTE (Sønderborg DK-6400) |
| OI-8 | ECU sequence | ignition_v2.json sequence; torch flame sensor; priming rule | Not yet implemented | Electronics |
| OI-9 | Roll torque | Helical source removed; residual unknown | GNC RCS-off threshold 0.03 N m; lead rule 0.02 N m | T1 measurement |
| OI-10 | Residual web | B1 1.31 mm (gnc v2) and 0.94 mm (gnc v1) at x1.5 | Rule >= 1 mm | Keep B1 within 19 s of burn, or lengthen the grain after T1-T2 |
| OI-11 | Pintle force and spring | Resolved: rolling guide plus 0.25/0.12; C1 on L0, C2 on L1/L2 | Mechanical pintle v2.3 carries L1/L2 natively | Rework after the thermal FEA and mechanical.json v2 |
| OI-12 | Relight precondition | Chamber "vented" (Pc within 0.1 bar of ambient) | gnc.json v2 says "purged" | Read "purged" as "vented"; N2 purge on the ground only |
| OI-13 | Deadband and resolution | 16 um at 100 % and 6.8 um at the floor open-loop; 0.13-0.17 bar closed-loop | gnc.json v2: 0.5 % F_max deadband | Electronics and Mechanical; bench with the measured plant |
| OI-14 | ENG-05 shutdown | Needs <= 0.205 s full stroke from 100 % | Electronics S3 dynamics: from 100 % at 3.5 MPa, 0.106-0.122 s to < 10 % thrust (fails) | Resolved by the lead: pre-MECO throttle-down to <= 75 % required |
| OI-15 | Servo thermal | Head 37-66 C at relight; soak 66-190 C | HV69 mount limit 50 C | Mechanical FEA and bracket design; T1 thermocouples |
| internal | Relight text in v2.3 | igniter.sequence.relight: "the isolation valve may stay open between burns" | Lead rule recorded in pintle_actuator.lead_decision_v2p3: valve closed during coasts | The lead rule governs; text to be corrected in the next revision |
| internal | Pintle check basis | The adopted-spring numbers use a hypothetical rolling_18mm guide with plain pins | Mechanical's final guide and pins | Mechanical v2.3 re-run supersedes them |

## 13. Failures and superseded evidence

All of these are kept as evidence.

| Item | What happened | Consequence |
|---|---|---|
| v1 helical grain (L 200) | Burned through on B1: web -3.12 mm at 15.0 s; also a roll-torque source | S230 straight port (LEAD) |
| eps 3 nozzle | Separates at <= 20 %; side-load bound 3.5-11.2 N | eps 2.0 |
| Mechanical pintle force law v2-v2.2 | Unconservative for opening: the closing pressure force persists while the gap meters | S3 failed C2 under L1 (1.28-1.47); rolling guide adopted |
| First pintle force answer | Used the v2 spring before the S3 baseline change | Recomputed on S3; failure reported to the lead and Mechanical |
| Pintle full-stroke 0.08 s | Carried from the v1 ENG-03 target; no combustion basis | Retired in v2.2; drive sized by the GNC v2 requirements and ENG-05 |
| actuator_rate_check_v2 run 1 | Start rule tested against the 2500 N/s cap instead of the >= 1000 N/s requirement | Patched analytically; run-1 file kept |
| headend_thermal_v2 run 1 | No re-radiation and a one-way joint gave an unphysical case node of 670-1890 K | v2.2b supersedes it; file kept |
| A1 x0.6 O/F | Cumulative O/F 15.9 beyond the O/F 14 c* table clamp | Values approximate; flagged |
| CoolProp transport | No N2O viscosity or conductivity model | CO2 surrogate (ASSUMED) |
| Early interface-writer drafts | Hand-typed numbers | Every value now computed from data, with asserts |

## 14. File index and reproduction

All paths are under the hub `/home/claude/work/shared-fallback/engine/02-combustion/`.

| Area | Scripts (`src/`) | Data and figures |
|---|---|---|
| Thermochemistry | `cea_cards.py`, `thermo_tables.py`, `perf_tables.py` | `data/thermo/*` (shifting and frozen tables, `hf_sensitivity_v1.csv`, `n2o_liquid_correction_v1.json`); `figs/v2/thermo_cstar_Tc_v2.png` |
| N2O and tank | `n2o.py`, `n2o_validation.py`, `tank.py`, `tank_nheq.py`, `tank_trades.py` | `n2o_validation_v2.*`, `supercharge_trade_*_v2.*`, `settling_v2*.json`, `ceiling_vs_time*_v2.csv`; figures `n2o_validation_v2.png`, `supercharge_v2.png`, `ceiling_vs_time*_v2.png` |
| Injector and feed | `injector.py`, `injector_compare.py`, `feed_line_checks.py` | `injector_compare_v2.*`, `injector_G_table_v2.npz`, `feed_line_checks_v2.json`; figure `injector_models_v2.png` |
| Throttle and pintle | `throttle_trade.py`, `actuator_rate_check.py`, `failure_cases.py`, `needle_force_v2p3.py`, `pintle_spring_window_v2p3.py` | `throttle_trade_v2.*`, `engine_S230/throttle_map_v2.csv`, `engine_S230/plant_valve_to_pc_v2.json`, `actuator_rate_check_v2.json`, `full_stroke_failure_case_v2.json`, `needle_force_bounds_v2p3.*`, `pintle_spring_window_v2p3.json`; figures `throttle_map_v2.png`, `plant_v2.png`, `actuator_rate_check_v2.png` |
| Grain and duty cycles | `grain_q1d.py`, `run_dc.py`, `run_dc_extra.py`, `plot_dc.py`, `chamber_port_state.py`, `m1_design.py` | `grain_trade_v2.csv`, `dc*/`, `engine_S230*/`, `chamber_port_state_v2.json`; figures `dc_DC-*_v2.png`, `grain_trade_v2.png`, `chamber_port_state_v2.png` |
| Nozzle and erosion | `nozzle.py`, `nozzle_perf.py`, `erosion_dc.py` | `nozzle_contour_v2.csv`, `nozzle_perf_v2.*`, `throat_props_v2.json`, `erosion*/`; figures `nozzle_eps_trade_v2.png`, `nozzle_sep_v2.png`, `erosion_v2.png` |
| Heat loads | `heat.py`, `thermal_bc_v2.py`, `soakback.py`, `soakback_sens.py`, `soakback_relight.py`, `headend_thermal_v2.py` | `thermal_bc_*_v2.csv`, `thermal_bc_summary_v2.json`, `soakback*_v2.*`, `headend_bc_*_v2.csv`, `headend_thermal_v2.json`; figures `thermal_bc_v2.png`, `soakback_v2.png`, `soakback_wall_v2.png`, `headend_thermal_v2.png` |
| Ignition and stability | `ignition_v2.py`, `stability.py` | `ignition_v2.json`, `stability_v2.*`; figure `stability_v2.png` |
| Interface and tables | `write_interface_v1.py`, `write_interface_v2.py`, `write_interface_v2p3.py`, `build_report_tables.py`, `make_figs_v2.py`, `summary_figs.py` | `combustion_interface_v2*_as_published.json` (v2, v2.1, v2.2, v2.3) |

Reproduction:
- Every script states its usage in its docstring.
- `python src/build_report_tables.py data` regenerates all the tables of this report from the data files.
- Inputs used from GNC are frozen in `inputs/` (snapshots with a MANIFEST).
