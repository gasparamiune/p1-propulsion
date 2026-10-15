> Restored 2026-10-12 23:35Z by the lead from a local copy, because the shared mount is down. The copy on the mount may hold later minor edits; this restored text governs until the mount returns.

# Engine team charter (v1, 2026-10-11)

Project: a cheap rocket that lifts off, cuts its engine, and lands itself upright under engine power with nozzle aiming. Launch target: ACEMA, Argentina, 1 Sept 2027. Build and testing happen in Sønderborg, Denmark.
Founder: Gaspar (mechatronics engineer). His brother Lauty owns the airframe and structure. **This team owns the engine and propulsion system only:** tank, valves, plumbing, injector, chamber, grain, nozzle, igniter, gimbal and TVC actuators, engine controller, and engine sensors.

## Team

| Role | Owns (write access) | Interface file |
|---|---|---|
| Lead engineer (director, integrates and decides) | `00-requirements/`, `reviews/`, `README.md` | `interfaces/ENGINE-BASELINE-v0.json` |
| Senior Space / systems and GNC | `01-systems-gnc/` | `interfaces/gnc.json` |
| Senior Combustion | `02-combustion/`, `05-plume-cfd/` | `interfaces/combustion.json` |
| Senior Mechanical | `03-cad/`, `04-fea/` | `interfaces/mechanical.json`, `interfaces/ICD-AIRFRAME.md` |
| Senior Electronics | `06-electronics/` | `interfaces/electronics.json` |

All paths are under `/mnt/project-files/engine/`. You never write in another owner's folder or interface file. You read everything.

## Founder decisions (2026-10-11), and what they are not

- The engine is an N2O hybrid with a 3D-printed fuel grain, throttled and restartable through oxidiser flow control.
- Max thrust is **500 N** at sea level.
- Metal hot parts ordered online are allowed. **A PETG fit-check prototype of every part comes first.** It is non-firing unless a part is explicitly cleared for water cold-flow.
- Nozzle aiming was delegated to the lead, who chose a **two-axis gimbal of the whole thrust chamber**. That choice can be revisited only by a written trade that shows a better option.
- Cost is the main driver: PETG printing, COTS parts, and online CNC services at comparable prices.

## Rules of evidence (non-negotiable)

1. **SI units everywhere.** Data files carry versions (`v1`, `v2`, …) and a date. CAD is in STEP millimetres with +Z as the engine axis pointing forward (from nozzle to injector). GLB files are in metres with +Y up.
2. **Tag every number** by its source:
   - `REQ`: a founder or lead requirement
   - `MEASURED`: no measurements exist yet
   - `DATASHEET`: give the vendor and part number
   - `LITERATURE`: give the citation
   - `CEA`, `SIM` or `FEA`: say which run produced it
   - `DERIVED`: a hand calculation, with the script path
   - `ASSUMED`: a placeholder with a stated range
3. **Do not invent data.** When a value is unknown, say so and give a defensible range with its source. If a literature value can't be verified, label it unverified. Missing data goes in an "Unknowns" list. It never gets silently filled.
4. **Keep fidelity levels separate.** Concept geometry, solid CAD, mass budget, simulation, and physical validation are different things. A simulation that runs, a mesh that converges, or a UI that renders is not physical approval. No hardware has been tested. Every result is a prediction until a test measures it.
5. **Keep contradictions and failures as evidence.** A failed check is reported, not deleted. A design that fails a margin is shown failing, then fixed and re-run.
6. **Prices:** quote for delivery to Sønderborg, Denmark, 6400. Never use 0 or a "from" price for an unknown cost. Write `TO-QUOTE` with the vendor you would ask.
7. **Innovations are welcome as labelled research proposals.** Give the hypothesis, the comparator, the evidence, and the refutation criterion. Never claim proven superiority.
8. **Safety (N2O):**
   - N2O can decompose explosively when heated, adiabatically compressed, or contaminated with hydrocarbons.
   - The design must have oxygen-clean, compatible materials: PTFE, FKM or Viton seals, PFPE (Krytox) grease only, no hydrocarbon lubricants in oxidiser wetted paths.
   - It must have no flashback path into the feed, and a slow-opening fill.
   - It must have a tank relief valve and a remote vent/dump.
   - It must have hardware arming interlocks.
   - Every firing is remote, with a documented safe distance.

## Checkpoint format (each deliverable)

Every specialist ends with `<folder>/REPORT.md`. It opens with a checkpoint block with these headings:
- **Claim:** what is now true, in one paragraph.
- **Configuration:** versions of the inputs and interface files used.
- **Sources:** literature, datasheets, CEA runs.
- **Files:** what was produced, with paths.
- **Tests / verification:** analytic cross-checks, convergence studies, reimport checks, and their results, including failures.
- **Unknowns:** what is missing and how to close it.
- **Next closure:** the single most important next step.

## Coordination protocol (how the four of you work together)

You run in parallel. You coordinate through files and through the lead.

1. **Start** by reading:
   - `00-requirements/REQUIREMENTS.md`
   - this charter
   - `interfaces/ENGINE-BASELINE-v0.json`
   - every other `interfaces/*.json` that already exists
2. **Milestone M1 (publish early).** Publish v1 of your interface file as soon as your first-pass numbers exist, before your deep work. The others are waiting on it. What each discipline publishes is listed in its brief. Append one line to `interfaces/CHANGELOG.md` for each publication or change, in the form `date | owner | file vN | what changed | why`. Append only, and re-read the file after writing.
3. **Re-read before each major step.** Re-read the other interface files before each major step: CAD regeneration, FEA run, CFD run, final report. Build your scripts so they **read** interface JSON, never hard-code another discipline's numbers. Regeneration then costs one command.
4. **Conflicts:**
   - If you need a change in another discipline's interface, append a `REQUEST` line to the CHANGELOG naming the owner.
   - If it blocks you or changes a founder decision, message the lead with `SendMessage` to `"main"`. Keep messages rare, specific, and with numbers.
   - The lead decides cross-discipline conflicts.
5. **Milestone M2 (finish).** Before writing your final report, re-read all interface files at their latest version. Make your outputs consistent with them, or list each mismatch under "Open interface issues" in your report.
6. **Never** call any `mcp__hearthbot__` tool. Only the lead talks to the founder.

## Shared compute (4 CPU cores, 15 GB RAM, about 25 GB disk for everyone)

- Python environment: `/opt/engine-venv/bin/python`. It has numpy, scipy, matplotlib, numba, cadquery 2.8, gmsh 4.15, meshio, pyvista, trimesh, cantera 3.2, CoolProp 8, rocketcea, scikit-fem, python-control, ezdxf.
- System tools:
  - `ccx` (CalculiX 2.21)
  - `gmsh`
  - OpenFOAM v1912 (solvers such as `rhoCentralFoam` and `blockMesh` are on PATH in `/usr/bin`, environment file `/usr/share/openfoam/etc/bashrc`)
  - `gfortran`, `ffmpeg`, `xvfb-run`
- You may install more tools with `apt-get` or `/opt/engine-venv/bin/pip`. Add them to `tools/setup_env.sh` by appending a line with your role as a comment.
- **Budget:**
  - Combustion CFD: ≤ 2 cores and ≤ 5 GB.
  - Mechanical FEA: ≤ 2 cores and ≤ 6 GB (`OMP_NUM_THREADS=2`).
  - Space and Electronics: ≤ 1 core. Run heavy Monte Carlo with `nice -n 10`.
- Run long jobs in the background with logs. Check progress without busy-waiting.
- Put heavy scratch (meshes, CFD time directories) in `/home/claude/work/<role>/`. That container disk is not persistent, so copy curated results and **all scripts** to the shared folder. Keep each discipline's shared output under about 300 MB.
- The shared folder is a network mount, so do not run solvers with heavy I/O directly in it.
- GitHub and most vendor sites are blocked by the network policy. PyPI and the Ubuntu archive work. Web search may work, so try it for literature and datasheets, and cite what you used.
- The repo `/home/claude/ARGOS-H1` (Spanish, brother's earlier hopper study) is **read-only**: no commits, no pushes. Its avionics choices are Teensy 4.0, ADIS16470 IMU, a LiDAR rangefinder, and ZED-F9P GNSS. Its method (per-part files, BOM, mass ledger with unknowns, traceable calculations) is reusable. Its R12 aluminium box-frame CAD and its cold-gas propulsion are not.

