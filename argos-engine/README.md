# ARGOS H1 engine: self-landing hybrid rocket engine

This folder is the engine work for the ARGOS H1 rocket: a 500 N N2O/ABS hybrid engine that has to lift the rocket, throttle down, and bring it back to an upright landing, steering with a two-axis gimbal. It is a separate project from P1-J (the waterjet in the rest of this repository), and nothing outside `argos-engine/` was changed.

**Status: design, simulation and review drafts. Nothing here is physically validated.** No part has been built, fired or measured. Every number carries an evidence tag (see below), and "frozen" only means a design baseline the analyses were run on. A passing test, a hash match or a clean render is not physical approval.

Snapshot: 2026-10-21 (final package). The decision trail is `interfaces/CHANGELOG.md` (268 entries).

## Final package (2026-10-21)

- **Start with the datasheet:** `07-datasheet/out/rev1/ARGOS-H1-ENGINE-DATASHEET_rev1.pdf` (PRELIMINARY rev1, 161 pages). It is built from the FINAL CAD v3.5.2 and the interface files. Every value is traced to its source and carries an evidence tag. It reflects the decision log up to line 266, so it still shows firmware v2.13 as queued and not started; v2.13 started the same day (line 268). Line 267 records the datasheet's build and line 268 its independent check, which passed with notes that change no value (`reviews/REVIEW-DATASHEET-R1-FINAL.md`). One note matters to a reader: §14 repeats the electronics open issues without the "SUSPENDED UNTIL v2.13" label; until the next build, §10.9 and the carve-out govern.
- **CAD v3.5.2** is the FINAL part set (`03-cad/v3.5.2/`, manifest of 456 rows). It is a design model, not released for fabrication.
- **3D FEA:** the assembled-engine FEA on CAD v3.5.2 is done (`04-fea/assembly3d_v352/REPORT-FEA3D-v352.md`). Its margin matrix covers every part under every load case (datasheet §9.2 and §9.3).
- **Electronics:** firmware v2.12 and `interfaces/electronics.json` v4.1 passed review with comments (REV-ELEC-4). One fix is still open, firmware v2.13: during ignition, a fault on the C1 seat temperature sensor could fake the "lit" signal. Until v2.13 is written and reviewed, the seat-temperature correction is not used for any start with ignition, so **the A1 flight is NO-GO**. v2.13 is in progress and follows in a later push.

Open problems this package does not close (details, owners and closure paths are in the datasheet, §1.4, §9.3, §12.3 and §12.4):

- 9 of the 26 parts are below zero margin in at least one load case (33 governing negative cells), each with its class and planned closure.
- The FEA3D v3.5.2 results have no independent review. The last mechanical review, REV-MECH-2 (on the CAD v3.5.1 run), was REVISE.
- The J-FWD joint seat line is not shown mesh-converged, and the J-FWD screw low-cycle fatigue stays open (single-use screws, founder rule C6).
- The founder gate T-F1 (short-time exposure of the 6061-T6 case and head, datasheet §6.2) is open.
- The seat-temperature correction of the chamber-pressure zero has open residuals: the per-serial coefficient and its calibration temperature (bench step B-PC-1), the thermal-zero maximum (F-10, MISSING) and the seat sensor mount (MISSING).
- Gimbal axis stiffness ENG-11: the hard minimum of 3,100 N·m/rad per axis holds, but the spread across gimbal poses (±20 %) is not met on the beta axis (±28.7 %), and the first rocking mode falls below its 25 Hz minimum when the servo is at the low end of its assumed stiffness (SIM / DERIVED, datasheet §3.3).
- The FA-1 hard-start class Z3 v2 is a stand rule: the 1 kHz flight record is only a lower bound, so Z3 v2 is not evaluated in flight, and in flight the joint cannot be replaced before the relight (open).
- The flight consequence of a flagged first light is open (the A1 relight inhibit is PROVISIONAL).
- The shorter T4 static-fire relight is adopted, but its length waits for a re-run.
- The P_torch threshold re-base is open.
- The A1 flight T0 range of 0-40 °C is an ASSUMED design range; the founders confirm it against the launch-site climate.

## Engine at a glance (2026-10-15 snapshot)

These are the 2026-10-15 values, on CAD v3.5.1. The datasheet rev1 holds the current values on CAD v3.5.2; where they differ, the datasheet governs.

| Item | Value | Evidence |
|---|---|---|
| Propellants | N2O (self-pressurised, heated tank) / printed ABS grain | decision |
| Rated thrust | 500 N at Pc 25 bar (software cap), O/F 10.4, Isp 193 s | SIM |
| Throttle | 5:1 (100-500 N) by servo pintle in the injector; 8:1 stretch | requirement; floor only measurable by static fire |
| Physical worst case | 876 N at Pc 42.9 bar (pintle stuck open, 30 °C tank, Cd 0.80); 30 bar abort | SIM |
| Total impulse, full 2.0 kg N2O | about 3,900 N·s (3,730-4,060), class L; 500 N held 4-7 s, burn 9-13 s | SIM |
| Throat / exit | 13.72 mm / 19.41 mm (expansion ratio 2.0) | CALC |
| Grain | two ABS halves, 53.5 mm OD × 115 mm each, 25 mm port, about 0.42 kg | CALC |
| TVC | two-axis whole-engine gimbal, 8° stop, ≥ 100°/s slew, pivot at mid-burn CG | SIM / decision |
| CAD baseline | v3.5.1 (frozen): 5.409 kg with full grain and no N2O, tank excluded | CAD massprops |
| Envelope | 139.5 × 140.2 × 593.3 mm (594.8 mm at gimbal stop); needs ≥ 140 mm bay bore down to the nozzle | measured from STEP/GLB |
| N2O tank | concept only: 6061 tube 101.6 × 3.175 mm, 445 mm internal, 2.00 kg N2O; not in the CAD | ASSUMED / ESTIMATE |
| Reference vehicle | about 17.4 kg at liftoff, first-flight apogee about 210 m | SIM; airframe ASSUMED |
| Landing success | 98.4 % in the 6-DOF Monte Carlo (earlier, lighter vehicle) | SIM |

The airframe (tube, fins, legs, avionics bay) belongs to Lauty and is not designed here. Everything about it in these files is an ASSUMED reference vehicle (RV-1c, `01-systems-gnc/vehicle/`).

## Where to start

| Folder | What is in it |
|---|---|
| `00-requirements/` | `REQUIREMENTS.md`, `TEAM-CHARTER.md`, `ICD-AIRFRAME.md` (airframe interface draft) |
| `interfaces/` | `CHANGELOG.md` (every decision, numbered), and the published interface files `gnc.json`, `combustion.json`, `mechanical.json`, `electronics.json` |
| `01-systems-gnc/` | 6-DOF flight and landing simulation, Monte Carlo results, duty cycles, reference vehicle, `REPORT-v3.md` |
| `02-combustion/` | internal ballistics, throttle, ignition, purge and relight analyses, `REPORT.md`, test specs `CF-4-SPEC.md`, `T1-T4-REGRESSION-SPEC.md` |
| `03-cad/` | the part set: `v3.5.2/` (FINAL: assembly, parts, BOM, mass properties, checks and the 456-row manifest); `v3.5.1/` (the earlier frozen baseline), v3.4.1 and v3.5 kept for the trail; parts, drawings, calcs, checks |
| `04-fea/` | structural, thermal and stiffness FEA (CalculiX), load cases, materials; the 3D assembled-engine FEA on CAD v3.5.2 (`assembly3d_v352/`) and its v3.5.2 checks (`v352/`) |
| `05-plume-cfd/` | combustion plume CFD at max thrust (own solver runs, OpenFOAM cases, Fluent cross-check package, Blender visualisation, validation), `REPORT.md` |
| `06-electronics/` | engine computer: hardware (KiCad), firmware, calculations; the v2.10 and v2.11 handbacks; the v2.11 and v2.12 deliveries in `staging_v2.11/` and `staging_v2.12/`, with bench plan v5 in `docs/` |
| `07-datasheet/` | datasheet generator (`gen/`) and the datasheet `out/rev1/ARGOS-H1-ENGINE-DATASHEET_rev1.pdf` (PRELIMINARY rev1); the rev0 draft in `out/` is superseded |
| `reviews/` | independent reviews per discipline and `SUPERVISION.json`, the verdict register |
| `gallery/` | the image page (CAD renders, plume fields, landing scatter) |
| `workbench/` | the specialists' working code and notes that are not already in the folders above, including the 2026-10-15 state of the 3D assembled FEA (`workbench/fea3d/PROGRESS.md`); the finished runs are in `04-fea/` |
| `lead/` | the lead's roster log, decision-application scripts and review extracts |

Units are SI. GLB files are in metres with +Y up. STEP files are in millimetres with +Z forward and the origin at the gimbal pivot.

## Review state

Independent reviewers, not the authors, gave these verdicts (`reviews/SUPERVISION.json`). None is a physical acceptance.

| Review | Verdict |
|---|---|
| Combustion (REV-COMB-1 to 4) | REVISE, REVISE (targeted) twice, then ACCEPT WITH CORRECTIONS |
| Plume CFD (REV-PLUME-1/2) | ACCEPT WITH COMMENTS, then ACCEPT |
| GNC (REV-GNC-1 to 7) | REVISE, CONDICIONADO ×2, then PUBLISHABLE WITH CORRECTIONS ×4 |
| Electronics (REV-ELEC-1 to 4) | REVISE, REVISE, then ACCEPT WITH COMMENTS twice; REV-ELEC-4 carves the seat-temperature correction out of every start with ignition until firmware v2.13 is reviewed |
| Mechanical/FEA (REV-MECH-1/2) | REVISE; CAD v3.5 not freezable (v3.5.1 was then frozen by a lead decision, CHANGELOG 206); REV-MECH-2 on the CAD v3.5.1 3D FEA: REVISE. CAD v3.5.2 was released FINAL by a lead decision; its FEA3D results have no independent review |
| Datasheet (REV-DS-1) | ACCEPT WITH CORRECTIONS on the rev1 draft; final check of rev1: PASS WITH NOTES (0 BLOCKING; 8 notes that change no value, for the next build; `reviews/REVIEW-DATASHEET-R1-FINAL.md`) |

Known open problems, kept as evidence: see "Final package" above. Also:

- The N2O tank, its end caps and the airframe are not in the CAD.
- O-ring and phenolic insulator replacement intervals are not set yet.
- Prices are TO-QUOTE (delivered to Sønderborg, DK-6400). No price is zero or a "from" price.

## Evidence tags

SIM (simulation output), CALC (hand or script calculation), DERIVED (computed from other tagged values), DATASHEET (manufacturer data), LITERATURE, ASSUMED (a placeholder until measured or designed), TO-VERIFY, MISSING, AS RECALLED, TO-QUOTE.

## Left out of this folder

GitHub caps files at 100 MB and the raw solver output runs to many gigabytes, so this folder carries every result, script, report and model, but not the bulk solver dumps. Left out:

- three raw dumps that duplicate their processed JSON: `02-combustion/data/v2p4/purge_duration_v2p4_trade.json.raw.json.gz` (28.7 MB), `02-combustion/data/v2/v2p4/purge_duration_v2p4_trade.json.raw.json.gz` (28.7 MB), `02-combustion/data/v2/v2p4/retained_vapour_v341_v2p4.json.raw.json.gz` (10.9 MB);
- the specialists' raw run directories: CalculiX run folders and meshes, plume CFD working cases, GNC Monte Carlo raw streams, electronics SIL raw results, scratch folders and compiled caches (their sizes as of 2026-10-15: mechanical about 6.4 GB, 3D FEA about 0.7 GB, plume about 0.65 GB, GNC about 1.5 GB, electronics about 1.1 GB; the v3.5.2 runs added more).

Their summaries and the scripts that regenerate them are included. The raw dumps live only in the cloud workspace, which is not permanent.
