# ARGOS H1 engine: self-landing hybrid rocket engine

This folder is the engine work for the ARGOS H1 rocket: a 500 N N2O/ABS hybrid engine that has to lift the rocket, throttle down, and bring it back to an upright landing, steering with a two-axis gimbal. It is a separate project from P1-J (the waterjet in the rest of this repository), and nothing outside `argos-engine/` was changed.

**Status: design, simulation and review drafts. Nothing here is physically validated.** No part has been built, fired or measured. Every number carries an evidence tag (see below), and "frozen" only means a design baseline the analyses were run on. A passing test, a hash match or a clean render is not physical approval.

Snapshot: 2026-10-15. The decision trail is `interfaces/CHANGELOG.md` (216 entries).

## Engine at a glance

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
| `03-cad/` | the part set: `v3.5.1/` (frozen baseline: STEP, GLB, BOM, mass properties, assembly manifest), parts, drawings, calcs, checks; older v3.4.1 and v3.5 kept for the trail; `v3.5.2/` is a mass sensitivity, not a new baseline |
| `04-fea/` | structural, thermal and stiffness FEA (CalculiX), load cases, materials |
| `05-plume-cfd/` | combustion plume CFD at max thrust (own solver runs, OpenFOAM cases, Fluent cross-check package, Blender visualisation, validation), `REPORT.md` |
| `06-electronics/` | engine computer: hardware (KiCad), firmware, calculations, `REPORT-v2.10-HANDBACK.md` |
| `07-datasheet/` | datasheet generator and `out/ARGOS-H1-ENGINE-DATASHEET_rev0-draft.pdf` (draft, superseded numbers in places) |
| `reviews/` | independent reviews per discipline and `SUPERVISION.json`, the verdict register |
| `gallery/` | the image page (CAD renders, plume fields, landing scatter) |
| `workbench/` | the specialists' working code and notes that are not already in the folders above, including the unfinished 3D assembled FEA (`workbench/fea3d/PROGRESS.md`) |
| `lead/` | the lead's roster log, decision-application scripts and review extracts |

Units are SI. GLB files are in metres with +Y up. STEP files are in millimetres with +Z forward and the origin at the gimbal pivot.

## Review state

Independent reviewers, not the authors, gave these verdicts (`reviews/SUPERVISION.json`). None is a physical acceptance.

| Review | Verdict |
|---|---|
| Combustion (REV-COMB-1/2/3) | REVISE, then REVISE (targeted) twice |
| Plume CFD (REV-PLUME-1/2) | ACCEPT WITH COMMENTS, then ACCEPT |
| GNC (REV-GNC-1 to 5) | REVISE, CONDICIONADO ×2, then PUBLISHABLE WITH CORRECTIONS ×2 |
| Electronics (REV-ELEC-1/2) | REVISE, REVISE |
| Mechanical/FEA (REV-MECH-1) | REVISE; CAD v3.5 not freezable (v3.5.1 was then frozen by a lead decision, CHANGELOG 206) |

Known open problems, kept as evidence:

- The max-thrust FEA shows negative margins on the graphite throat insert (NZ-01), the TC-02 head and the gimbal ring under the current models; design changes and founder tests (N-F1 and others) are the planned paths.
- The 3D assembled-engine FEA is unfinished (`workbench/fea3d/`): the max-thrust case, the FA-1 case and three of the eight gimbal-at-stop poses (0°, 45° and 90° azimuth) are done; the modal run exceeded its memory cap, and the other five stop poses and the nine cone poses have not run.
- The N2O tank, its end caps and the airframe are not in the CAD.
- O-ring and phenolic insulator replacement intervals are not set yet.
- Prices are TO-QUOTE (delivered to Sønderborg, DK-6400). No price is zero or a "from" price.

## Evidence tags

SIM (simulation output), CALC (hand or script calculation), DERIVED (computed from other tagged values), DATASHEET (manufacturer data), LITERATURE, ASSUMED (a placeholder until measured or designed), TO-VERIFY, MISSING, AS RECALLED, TO-QUOTE.

## Left out of this folder

GitHub caps files at 100 MB and the raw solver output is about 11 GB, so this folder carries every result, script, report and model, but not the bulk solver dumps. Left out:

- three raw dumps that duplicate their processed JSON: `02-combustion/data/v2p4/purge_duration_v2p4_trade.json.raw.json.gz` (28.7 MB), `02-combustion/data/v2/v2p4/purge_duration_v2p4_trade.json.raw.json.gz` (28.7 MB), `02-combustion/data/v2/v2p4/retained_vapour_v341_v2p4.json.raw.json.gz` (10.9 MB);
- the specialists' raw run directories: CalculiX run folders and meshes (mechanical about 6.4 GB, 3D FEA about 0.7 GB), plume CFD working cases (about 0.65 GB), GNC Monte Carlo raw streams (about 1.5 GB), electronics SIL raw results (about 1.1 GB), scratch folders and compiled caches.

Their summaries and the scripts that regenerate them are included. The raw dumps live only in the cloud workspace, which is not permanent.
