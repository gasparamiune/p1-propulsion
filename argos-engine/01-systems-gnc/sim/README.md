# GNC simulation package (`gncsim`): Space/GNC, ARGOS H1 engine team

Version: sim v2.7.1-dev (2026-10-13). The 6-DOF is `sim6`/`run6 v2.7.1-dev` and the 1-D `sim1d v1.2` stays the
independent reference. This package supports `interfaces/gnc.json` v3. The v2.5 README (gnc.json v2) is kept as
`README_v2.5.md`, and the gncsim files published with gnc.json v2 are kept unchanged in `history/gncsim_hub_v2/`. The
gnc.json v2 scripts that changed since (`m2_actuator_study.py`, `m2_analysis.py`, `m2_mc6.py`, `m2_vehicle.py`) are kept
unchanged in `history/scripts_hub_v2/`.

Owner: Space/GNC (`01-systems-gnc`). Units are SI. Environment: `/opt/engine-venv` (Python 3.13, numpy, scipy,
numba, CoolProp, RocketCEA, python-control, matplotlib).

Everything here is simulation or derivation; none of it is hardware validation. Every parameter carries a tag
(REQ / DATASHEET / LITERATURE / SIM / DERIVED / ASSUMED), in one of three places:
- `gncsim/params.py` or `gncsim/vehicle.py`;
- `run6.build(...)[5]["tags"]`;
- the interface JSON it was read from.

Scripts read the interface JSON at run time (`GNC_IFACE`) and never hard-code another discipline's numbers. The
values the lead relayed before publication are named constants in the scripts, with the CHANGELOG line they come from.

## What changed since v2.5

All new options are off by default. With every option off, each version reproduces the stored runs of the previous
one bit for bit, field by field:

| Version | Check script | What it compares |
|---|---|---|
| v2.6 | `m2_bitcheck_v26.py` | v2.6 options off vs the stored v2.5 runs |
| v2.7 | `m2_bitcheck_v27.py` | v2.7 options off vs the stored v2.6 runs |
| v2.7.1-dev | `m2_bitcheck_v271.py` | parts A–E below |

The `m2_bitcheck_v271.py` parts are:
- **A:** options off vs the stored v2.6 runs.
- **B:** v2.7 options on with the new options off, vs the stored v2.7-dev runs.
- **C:** the regression band at its nominal corner, vs the stored runs.
- **D:** the 6-DOF regression-band effect vs the reduced model.
- **E:** the start-delay quantile option.

### v2.6 (flight software v2.6, lead decisions 2026-10-12)

- Gimbal command tracker: 100 deg/s, 2000 deg/s².
- Attitude reference governor with a ratchet (`att_ref_mode 1`).
- Lift-ramp shutdown model (`gncsim/tailoff.py`), fitted to Combustion's runs (`data/tailoff/tailoff_fit_v1.json`).
- Pre-MECO throttle-down.
- Relight start rule.
- Start-delay shift (`t_ign_add`), applied to the nominal (sizing) flight as well.
- Per-axis ENG-07d notch, fixed or tracking the run's own rocking mode.
- Engine-axis stiffness override.
- Wet engine inertia override.

### v2.7 (flight software v2.7, PROVISIONAL, lead 2026-10-13)

- In-flight throat-area growth. Per-run growth is drawn from its own generator. The ECU Pc-loop model applies, and
  the growth uses the CF change of the expanded nozzle.
- Thrust-effectiveness estimator, `k_est_asc 2`. It runs on the B-profile ascent, apex and floor descent, and in
  every landing burn. It is gated at h_est > 1 m, has a signed nominal axial-force model, and its floor and top-up
  commands are divided by k_hat in [0.8, 1.25].
- `k_est_asc 1` was rejected and is kept as evidence.

### v2.7.1-dev (2026-10-13)

- `reg_band` / `reg_a` / `reg_n`: the regression-law band (`gncsim/regband.py`, review RC-07).
  - The oxidiser and fuel flow per delivered thrust are multiplied by φ(a, n, X).
  - X is the oxidiser burned at map flow.
  - The φ tables come from Combustion's RC-07 corner runs (`data/regband/regband_model_v1.json`).
  - Per-run (a, n) are drawn from their own generator, seed 20261017.
- `t_ign_q`: the relight start delay is drawn from a quantile table, for example Combustion RC-03 E0→E2. It uses its own
  generator (seed 20261018), and the nominal flight flies the table median.

Every per-run draw that an option adds comes from its own generator. The main draw table (seed 101) is therefore
unchanged, and cases pair run by run.

## Layout (additions since v2.5)

| Path | Content |
|---|---|
| `gncsim/tailoff.py` | reduced lift-ramp shutdown model (v2.6) |
| `gncsim/regband.py` | regression-band reduced model reader and knot interpolation (v2.7.1-dev) |
| `data/tailoff/tailoff_fit_v1.json` | GNC fit of the shutdown model to Combustion's runs |
| `data/regband/regband_model_v1.json` | φ tables of the regression band, hypotheses H1–H4, validation |
| `data/relay/lead_relay_mech_fea_k_20261012.json` | lead relay of the Mechanical FEA stiffness and the Electronics J_int estimate |
| `history/gncsim_hub_v2/` | the gncsim modules published with gnc.json v2 (sim6 v2.5), unchanged |

### Scripts of gnc.json v3 (`scripts/`)

| Script | Purpose |
|---|---|
| `m2_prop_closure.py`, `m2_prop_closure_eval.py` | propellant closure on combustion.json v2.3 + mechanical.json v2 (+25 % rule) |
| `m2_mech_v2_check.py`, `m2_mechv2_mc.py` | mechanical.json v2 reading checks and the re-baseline Monte Carlo (ENG-07d set) |
| `m2_csi_v3*.py`, `m2_n_sweep.py` | ENG-07d linear CSI, frequency and stiffness targets, linkage-ratio sweep |
| `m2_ctrlfix_*.py`, `m2_meco_*.py`, `m2_tailoff_fit.py` | flight software v2.6 evidence (tracker, governor, MECO, relight, tail-off) |
| `m2_v26_tests.py`, `m2_bitcheck_v26.py`, `m2_repro_check.py`, `m2_rebaseline_compare.py` | v2.6 verification and attribution |
| `m2_throat_mc.py`, `m2_v27_tests.py`, `m2_bitcheck_v27.py`, `m2_kest2_forensics.py` | throat growth, k_est_asc 2, v2.7 verification |
| `m2_duty_cycles_v3.py`, `m2_duty_cycles_disp.py`, `m2_dc_burn_check.py`, `m2_dc_index_diff.py` | duty cycles v3 (nominal and dispersed sizing cases) and their checks |
| `m2_abort_tailoff.py`, `m2_relight_seq_sens.py` | abort tail-off bracket; relight sequence sensitivity |
| `m2_relight_181.py`, `m2_rl181_trace.py` | A1 at the 1.81 s planning value (v2.7 sequence); recorded flights of selected draws |
| `m2_regband_model.py`, `m2_regband_mc.py` | regression band: reduced model, B1 Monte Carlo at 85 m, apex cap search, the lead's 62 m cap (v1.1) |
| `m2_bitcheck_v271.py` | v2.7.1-dev checks A–E |
| `m2_relight_v28.py` | A1 relight on the v2.8 design (v1.2): planning-value sweep over the line states, full set at 0.81 / 1.41 s, fault path and fault spread, option (c) paired verification and the stale-flag analysis |
| `m2_dc_a1_v28_record.py` | A1 p99 cycle of the v2.8 liquid-line lights (a record, not a sizing case) |
| `m2_fc_thrust.py` | FC_THRUST accelerometer thrust estimate: error, latency, false aborts, stuck-pintle detection. Staged, NOT RUN for gnc.json v3 (no `results/fc_thrust`) |
| `m2_vehicle.py` | reference vehicle v3d |
| `m2_gnc_json_v3.py` | assembles `interfaces/gnc.json` v3 from the results (every number read from a result or interface file) |
| `m2_stage_hub_v3.py` | stages this folder and checks that every path gnc.json v3 names exists |

The v2 scripts are unchanged and still listed in `README_v2.5.md`.

## Results (`../results/`)

Each study writes its JSON summary into a subfolder, together with the Monte Carlo run tables. Tables over
100 kB are gzipped (`.csv.gz`).

The subfolders are: `prop_closure` (pc2 basis), `prop_closure_eval`, `mech_v2_check`, `mechv2_mc`, `csi_v3c`, `csi_v3`,
`n_sweep`, `ctrlfix`, `meco`, `v26_checks`, `v26_checks_v3c`, `results_v3a`, `throat_growth`, `throat_growth_a1k2`,
`v27_checks`, `abort_tailoff`, `relight_seq_sens`, `relight_181`, `relight_v28`, `regband`, `v271_checks` and
`duty_cycles_v3_checks`.

The duty cycles are in `../duty_cycles/`. The index is `duty_cycles_index_v3.json`; its `records` hold the v2.8 A1
record cycles. The reference vehicle is in `../vehicle/`.

## Running the v3 chain

```
cd 01-systems-gnc/sim
export GNC_IFACE=<folder with combustion.json v2.3, mechanical.json v2, electronics.json v1, throttle_map_v2.csv,
                  actuator_rate_check_v2.json>       # the interface set iface_v3c (sha256 in gnc.json inputs_read)
export GNC_ACT_RATE=$GNC_IFACE/actuator_rate_check_v2.json NUMBA_NUM_THREADS=1
PY="nice -n 10 /opt/engine-venv/bin/python"
$PY scripts/m2_prop_closure.py && $PY scripts/m2_prop_closure_eval.py
$PY scripts/m2_mech_v2_check.py && $PY scripts/m2_mechv2_mc.py && $PY scripts/m2_csi_v3.py && $PY scripts/m2_n_sweep.py
$PY scripts/m2_throat_mc.py && $PY scripts/m2_v27_tests.py && $PY scripts/m2_bitcheck_v27.py && $PY scripts/m2_kest2_forensics.py
$PY scripts/m2_duty_cycles_v3.py && $PY scripts/m2_duty_cycles_disp.py && $PY scripts/m2_dc_burn_check.py
$PY scripts/m2_abort_tailoff.py && $PY scripts/m2_relight_seq_sens.py && $PY scripts/m2_relight_181.py
$PY scripts/m2_regband_model.py && $PY scripts/m2_regband_mc.py && $PY scripts/m2_bitcheck_v271.py
$PY scripts/m2_relight_v28.py && $PY scripts/m2_dc_a1_v28_record.py     # m2_fc_thrust.py: not run for v3
$PY scripts/m2_vehicle.py && $PY scripts/m2_gnc_json_v3.py
```

Each script's docstring names its environment variables, inputs and outputs. Output folders default to the GNC
work area and are overridden with `GNC_*_OUT`.

Some scripts read work-area files of other disciplines that were not in the hub when they ran. For example,
`m2_regband_model.py` reads Combustion's band runs and `m2_relight_v28.py` reads Combustion's RC-03 file. Each such
script records the path, whether the file was in the hub, and its sha256.

Timing: the first call of each process compiles the numba kernels (about 30 s). A 500-run case then takes 30–80 s
on one core.

## Known limitations added since v2.5

**Thrust-effectiveness estimator (k_est_asc 2).**
- It is PROVISIONAL until the independent GNC review.
- The Monte Carlo gives the FSW a constant mass-estimate error, N(0, 3 %), ASSUMED.
- A flow-integrating mass estimate, with its drifting error, is not flown.

**Throat growth.**
- The 7–11 % band is literature-scaled, not measured.
- Its onset and non-uniformity are unknown.

**Regression band** (`regband` v1). These are hypotheses, not validated facts:
- **H1:** the corner effect is a function of the oxidiser burned, which holds for B1-like hops only.
- **H2:** growth and band compose multiplicatively.
- **H3:** liquid depletion cuts the thrust, with no vapour-phase burn (conservative).
- **H4:** the band is independent of the isp_scale draw (it may double count; conservative).
- The band distribution is uniform × uniform because no recommended distribution was published.
- The law itself is ASSUMED (Combustion RC-07) until T1–T4.

**Relight start delay (`t_ign_q`).**
- The 6-DOF lights at the drawn E0→E2 delay (Pc confirmation) and builds thrust with its own closed-loop lag.
- The E0→E2 distributions are Combustion SIM on ASSUMED delay distributions.
- The v2.8 sequence times are Electronics SIL / design values, and the torch gate is PROVISIONAL.

**Relight v2.8 and option (c)** (`m2_relight_v28.py` v1.2).
- Option (c) is flown as a fixed planning value per case (1.41 s on the fault cases). The ECU flag itself, its
  transitions in the coast and its staleness are not simulated; the stale-flag rule is a decision on these results.
- The fault-path spread (line-state E0→E2 + 0.56 s prep re-run) is DERIVED from the 1.37 − 0.81 s difference, and
  the spread after the prep is ASSUMED to follow the preopened tables.
- The staleness limit 0.3 s (3 frames at 10 Hz) is ASSUMED until Electronics publishes it.

**FC_THRUST study** (`m2_fc_thrust.py`, staged, NOT RUN for gnc.json v3; FC_THRUST is an open item).
- It reconstructs the accelerometer estimate on recorded flights with the sim6 measurement model, using other noise
  samples from the same model.
- CAN transport latency is not included.
- The open-loop thrust band on Pc loss is bounded by the lead's 1.143 factor only. Its lower end is unknown.

**Limitations carried from v2.5.** These still hold:
- no in-flight attitude aiding;
- quasi-steady drogue;
- tail-first aero unknown to about ×2;
- ASSUMED rocking damping, servo stiffness and hose and leg properties;
- no structural failure model;
- relight success is assumed (no-light accounting is separate, in gnc.json `no_light_accounting`).
