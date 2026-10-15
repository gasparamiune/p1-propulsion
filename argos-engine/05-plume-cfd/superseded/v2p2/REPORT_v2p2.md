# ARGOS H1: Max-thrust combustion and plume simulation (05-plume-cfd)

Version v2.1a for validation and v2.2 for the time-matched afterburn, 2026-10-12. Owner: Combustion and Propulsion. Status: digital simulation only, *Por revisar*. A simulation is a prediction, not a measurement.

## 0. Checkpoint

**Claim.** At 500 N on the eps 2 nozzle (pe/pa 3.24), the exhaust forms an under-expanded jet with a Mach reflection:
- a small Mach disk at x = 2.68 De, within 0.5 % of the Lewis-Carlson correlation;
- a train of shock cells about 4 De long;
- a turbulent mixing layer that closes the potential core at 13-15 De;
- a hot jet that crosses the full 45 De domain.

Thrust and mass flow are grid-converged to 0.15 % and 0.11 % and agree with 1-D theory within 1 %. The other structure quantities are bounded by the jet's own unsteadiness, not by the grid; bands are reported.

Afterburning in air, under the fast-chemistry assumption:
- adds at most 179 K at O/F 7.76;
- adds nothing at the v2 point (O/F 10.4, oxidiser-rich);
- adds up to 1476 K at the fuel-rich 12.5 % floor.

The images labelled QUALITATIVE or ARTISTIC are not radiation predictions.

**Configuration:**
- 2-D axisymmetric domain:
  - starts in the convergent at x = -19.3 mm from the exit (A/At 2.56; total conditions equal the chamber state);
  - extends 45 De downstream and 12 De radially;
  - 44 mm engine body with a base; 5 m/s co-flow; quiescent sea-level air at 101325 Pa and 288.15 K.
- Exhaust gas: calibrated perfect gas with gamma 1.13676 and R 296.93 J/kg K (MW 28.00, cp 2468 J/kg K), chosen so that pe/pc at eps 2 matches CEA. Air: gamma 1.4, R 287.05. Two species with mixture fraction Z, non-reacting.
- Operating points:
  - v1 (combustion.json v1): Pc 24.99 bar, O/F 7.76, T0 = eta_c*^2 Tc = 2844.9 K. All grid levels, sensitivities and OpenFOAM runs use it.
  - v2 (combustion.json v2.1 S230 point): Pc 25.01 bar, O/F 10.435, T0 2757 K.
  - Floor sweep 100 -> 20 -> 12.5 %, with v1 gas at 12.5 %: p0 4.36 bar, O/F 3.11, T0 2108 K.
- Solvers:
  - own solver `plume2s` (numba): HLLC with Einfeldt bounds, HLLE next to strong transverse pressure jumps, MUSCL with a van Leer limiter, SSP-RK2; axisymmetric source; algebraic eddy viscosity in the plume; inviscid slip walls in the nozzle.
  - OpenFOAM v1912 `rhoCentralFoam` (Kurganov-Tadmor), on a 20 deg wedge.
- Afterburning: post-processed with Cantera 3.2 (GRI-3.0 thermodynamics), fast chemistry.

**Sources:**
- Toro, *Riemann Solvers and Numerical Methods for Fluid Dynamics* (3rd ed. 2009, HLLC); Quirk 1994 (carbuncle cure).
- Turbulence closure (constants LITERATURE-UNVERIFIED, so a x0.5 / x2 sensitivity is reported): Brown & Roshko 1974 (mixing-layer growth); Pope 2000 (round-jet eddy viscosity); Dimotakis 1991 ("Langley curve" compressibility factor).
- Lewis & Carlson 1964 (Mach disk location).
- Prandtl-Pack/Tam shock-cell spacing (weak-shock vortex-sheet result).
- Modest, *Radiative Heat Transfer* (Rayleigh soot emission for the synthetic image).
- NASA CEA through RocketCEA (chamber state and calibration).

**Files:** hub `/home/claude/work/shared-fallback/engine/05-plume-cfd/` (458 files, 202 MB), indexed in §11.

**Tests / verification:**
- Three grid levels at the same physical time (3.25 ms) with GCI and an oscillatory 3x bound.
- Grid differences tested against the temporal scatter (2 sigma).
- CFD thrust against 1-D theory; Mach disk and shock-cell spacing against correlations.
- Own solver against OpenFOAM (inviscid, and RANS against SST).
- Single-gas error quantified; turbulence x0.5 / x2 and no-compressibility-factor sensitivities.
- v2 operating point against v1.
- Afterburn GCI at matched time.

**Unknowns** (§10, §12): soot, radiation, finite-rate and turbulence-chemistry effects, the nozzle boundary layer and real separation, ground impingement, and three-dimensional effects at gimbal angles.

**Next closure** (§12):
- A Fluent cross-check by a third party.
- A ground-plane landing case.
- A floor case with a viscous nozzle wall to predict separation.
- A static-fire photo and video comparison (shock-diamond spacing, luminous length).

## 1. Chamber state and port flame

The chamber state at max thrust comes from CEA at the quasi-1D grain model's operating point (02-combustion §4). At the v2 point: Tc 3257 K, MW 28.72, gamma 1.147.

Composition (mole fractions): N2 0.583, CO2 0.116, H2O 0.076, O2 0.072, CO 0.068, NO 0.032, OH 0.028.

The port flame figure is `../02-combustion/figs/v2/chamber_port_state_v2.png` (data `chamber_port_state_v2.json`). It shows:
- G_ox(x), regression r(x), cumulative O/F(x) and boundary-layer thickness (5.0 mm at the aft end at 100 %, 0.40 R);
- the stoichiometric O/F line (8.17) that marks the diffusion-flame zone in the wall boundary layer.

At 100 % the cross-section mean stays oxidiser-rich along the whole port, and mixing completes in the post-chamber and nozzle. At <= 50 % the mean O/F crosses stoichiometric inside the port.

## 2. Model and numerics

| Item | Own solver plume2s | OpenFOAM rhoCentralFoam |
|---|---|---|
| Equations | Axisymmetric RANS, algebraic eddy viscosity in the plume; inviscid nozzle | Euler, or k-omega SST (Prt 0.85) |
| Gas | Two species (exhaust, air) with transported Z; "single" mode = exhaust gas everywhere | Single gas (exhaust everywhere) |
| Grid | Structured, masked solid band. Coarse 270 x 76 (20,008 fluid cells), medium 80,032, fine 1080 x 304 (320,128); minimum cell 0.33 / 0.17 / 0.08 mm | blockMesh wedge, 17,176 cells (coarse), 20 deg wedge |
| Mixture fraction | Transported | Not available (FAILURE-CFD-01): reconstructed from total enthalpy as Z_T, valid only for unit turbulent Prandtl/Schmidt numbers |
| Time | Time-accurate, CFL 0.5. Coarse to 4.0 ms; medium to 3.0 ms, continued to 3.25 ms; fine from the medium 3.0 ms state to 3.25 ms | Time-accurate; stopped at the 2 h wall-clock limit (inviscid 1.0 ms, SST 1.15 ms) |

Turbulence closure:
- Exchange coefficient uniform per axial station: the mixing-layer value comes from the vorticity-thickness growth 0.18; the developed-jet value is nu_t = 0.028 dU r_1/2.
- Compressibility factor Phi(Mc) = 0.23 + 0.77 exp(-3.4 Mc^2).
- Pr_t = Sc_t = 0.7.

The fine run covers 0.25 ms of its own time. That is about two flow-through times of the first 10 De (u about 1700 m/s), so the fine level validates the near field (<= 10-15 De), not the far field.

## 3. Results at max thrust (v1 point; fine grid unless stated)

Structure:
- Under-expanded exit: Me 2.01, pe/pa 3.24 (1-D), fully expanded Mj 2.62.
- Mach reflection with a small Mach disk at x = 2.676 De. Its radius oscillates in time and is not grid-converged (0.02-0.14 De).
- Peak Mach before the disk 3.66-3.69.
- Shock cells: first spacing 3.96 De, mean of three 4.10 De.
- Potential core (axis Z >= 0.95) 14.9 De.
- Axis T: 2222 K at 10 De and 2058 K at 20 De.
- Starting jet front at 44.7-44.9 De at 3-4 ms, which is the domain end.

Figures, under `ownruns/<run>/fig/`. Fields, each as `_full` (0-45 De) and `_near` (0-15 De):
- Mach `*_mach_*`;
- p/pa `*_p_pa_*`;
- T `*_T_*`;
- density `*_rho_*`;
- numerical schlieren |grad rho| `*_schlieren_*`;
- mixture fraction `*_Z_*`;
- fast-chemistry equilibrium temperature `*_Teq_*`;
- afterburning rise `*_dTab_*`;
- CFD temperature plus the afterburn increment `*_Tcfd_ab_*`;
- CO and OH mole fractions `*_XCO_*`, `*_XOH_*`.

Line plots: `*_centreline.png`, `*_afterburn_axis.png`, `*_afterburn_radial.png`.

Runs: `f_2s_100` (fine), `m_2s_100` (medium), `c_2s_100` (coarse), `c_2s_100_v2op` (v2 point), `c_2s_sweep` (floor, prefix `c2s_floor`). Axes are in exit diameters, x from the exit plane.

## 4. Afterburning (fast chemistry, labelled)

Method (`scripts/own/afterburn.py` v3):
- Each cell is a mixture of stream 1 (exhaust elements) and stream 2 (dry air).
- T_eq is the HP equilibrium of the whole mixture. T_inert has the exhaust in its own equilibrium and the air inert.
- dT_ab = T_eq - T_inert is the afterburning rise. It is zero by construction in the pure-exhaust core; the check gives a mean of 0.17 K.
- The exhaust energy is the mass-weighted exit-plane enthalpy. An upper bound "stream B" releases the c* deficit and is reported separately.

| Case | O/F | dT_ab max [K] | Location | Note |
|---|---|---|---|---|
| v1 point, time-matched 3.25 ms (coarse / medium / fine) | 7.76 | 174.0 / 177.3 / 179.2 | x 5.9-6.3 De, r 0.67-0.70 De, Z 0.91 (near Z_st 0.93) | GCI 1.8 % (p 0.78). Grid differences lie inside the temporal band 172-178 K, so not resolvable. V(dT_ab > 100 K) 0.00056-0.00069 m3 |
| v2 point (S230) | 10.435 | 0.44 | n/a | Oxidiser-rich exhaust (no Z_st): nothing to burn. The v1 run post-processed with v2 composition gives 0.47 K |
| 12.5 % floor (v1 gas) | 3.11 | 1476 | Axis, x 20 De | Fuel-rich: CO and H2 burn with entrained air |
| 12.5 % floor (v2 composition) | 4.06 | 1322 | Axis, x 16.8 De | Sensitivity |

Gas-model check, v1 point: in the strongly expanded core the calibrated perfect gas is 222 K warmer on average than an equilibrium exhaust at the same enthalpy (5th-95th percentile -504 to +30 K). Core temperatures before the Mach disk carry that uncertainty.

## 5. Throttle-floor (overexpanded) case and the sweep

Run `c_2s_sweep`, coarse, started from the 4 ms state of `c_2s_100`.
- Inflow ramp: 100 -> 20 % between 4.0 and 5.5 ms; hold to 6.0 ms; 20 -> 12.5 % by 6.5 ms; hold to 8.0 ms.
- The ramp is quasi-steady and time-compressed by about 200x. It shows how the pattern changes, not the real 0.3-0.5 s transient.

At 12.5 %:
- Thrust 61.8 N against 62.5 N in the map.
- Axis Mach 2.49 at 0.19 De, then a strong normal shock down to Mach 0.06 at 0.65 De, giving a subsonic pocket. Downstream the flow sits around Mach 1.0-1.2.
- The nozzle walls are inviscid, so the CFD cannot show the incipient lip separation that Schmucker predicts at 12.5 % (02-combustion §5.1).

Figures: `ownruns/c_2s_sweep/fig/c2s_floor_*`.

## 6. Animations

| File | Content | Frames |
|---|---|---|
| `anim/startup_500N_medium.mp4` and `.gif` | Start-up transient to 500 N (Pc 25 bar), medium grid (80k cells), 0-3 ms. Top half Mach, bottom half numerical schlieren; x 0-30 De | 61 frames at 12 fps (5.1 s), 1104 x 340 |
| `anim/sweep_100_20_12p5_coarse.mp4` and `.gif` | Throttle sweep 100 -> 20 % (hold) -> 12.5 % floor (hold), coarse grid, quasi-steady time-compressed inflow. Mach and schlieren; x 0-25 De | 161 frames at 12 fps (13.4 s), 1304 x 386 |

## 7. Images of "the fire coming out of the engine"

- **Synthetic photo** (QUALITATIVE), `scripts/own/synth_photo.py`. Line-of-sight (forward Abel) integration of grey soot-proxy emission at 630, 550 and 460 nm.
  - Soot volume fraction is f_v = 1e-7 Z rho/rho_ref (ASSUMED), with C_abs 4.9 (ASSUMED).
  - Temperature is the CFD T plus the fast-chemistry increment.
  - Files: `ownruns/m_2s_100/fig/m2s_synth_photo.png` (with `_frozenT` for comparison), `c_2s_100/fig/c2s_synth_photo.png`, `c_2s_100_v2op/fig/c2s_v2op_synth_photo.png`, `c_2s_sweep/fig/c2s_floor_synth_photo.png`.
- **Blender Cycles renders** (ARTISTIC), `blender/final/argos_plume_artistic_{side,threequarter}.png` (with `_raw` versions). The CFD density and temperature fields are revolved in a volume shader with Wien-weighted blackbody emission. Exposure, colour, coefficients and camera were chosen for appearance; nothing in these images is a measurement or a validated radiation result. Inputs: `blender/m2s_fields/`. Test renders are kept in `blender/tests/`.

## 8. Validation

Table 8.1. Thrust and mass flow against 1-D theory. 1-D at the v1 point: F ideal x lambda = 505.79 N (lambda 0.98296), mdot 0.25582 kg/s.

| Run | F [N] | dF vs 1-D [%] | mdot [kg/s] | dmdot [%] |
|---|---|---|---|---|
| Own coarse, 2 species | 500.33 | -1.08 | 0.25363 | -0.86 |
| Own medium | 500.56 | -1.03 | 0.25397 | -0.72 |
| Own fine | 500.82 | -0.98 | 0.25415 | -0.65 |
| Own coarse, single gas, inviscid | 500.44 | -1.06 | 0.25363 | -0.86 |
| OpenFOAM inviscid (exit fields) | 493.96 | -2.34 | 0.25171 | -1.61 |
| OpenFOAM SST (exit fields) | 488.99 | -3.32 | 0.24987 | -2.33 |
| Own coarse at the v2 point (against its own 1-D: 505.91 N) | 500.41 | -1.09 | 0.26181 | -0.86 |

The remaining 1 % deficit of the own solver is consistent with its inviscid nozzle and the 2-D throat. It is not interpreted further.

Table 8.2. Three-level grid study at the same time, 3.25 ms. GCI on the fine level, safety factor 1.25 for monotone data; 3 x max-deviation bound when oscillatory or when p < 0.5.

| Quantity | Coarse | Medium | Fine | p | GCI fine [%] | Resolvable against 2 sigma temporal scatter? |
|---|---|---|---|---|---|---|
| Thrust [N] | 500.33 | 500.56 | 500.82 | -0.12 | 0.152 (3x bound) | yes |
| Throat mdot [kg/s] | 0.25363 | 0.25397 | 0.25415 | 0.87 | 0.111 | yes |
| Mach disk x [De] | 2.775 | 2.676 | 2.676 | 11.4 | ~0 (asymptotic range not shown) | no |
| Mach disk r [De] | 0.138 | 0.019 | 0.059 | osc. | 600 | no |
| M max before disk | 3.673 | 3.664 | 3.688 | osc. | 1.9 | no |
| First Mach max x [De] | 6.79 | 6.99 | 6.97 | osc. | 8.7 | no |
| First spacing [De] | 4.13 | 3.97 | 3.96 | 4.8 | 0.007 | no |
| Mean spacing of 3 [De] | 4.17 | 4.09 | 4.10 | osc. | 6.5 | no |
| Axis T at 10 De [K] | 2128 | 2207 | 2222 | 2.4 | 0.19 | no |
| Axis T at 20 De [K] | 2061 | 2072 | 2058 | osc. | 2.1 | no |
| Core length, Z 0.95 [De] | 13.22 | 14.35 | 14.90 | 1.06 | 4.2 | no |

The jet is unsteady: the shear layer and Mach disk move. Temporal bands over 2.5-3.25 ms:

| Quantity | Coarse | Medium |
|---|---|---|
| Mach disk x [De] | 2.64-2.77 | 2.58-2.74 |
| First Mach max [De] | 6.56-7.26 | 6.76-7.17 |
| First spacing [De] | 3.76-4.40 | 3.70-4.44 |
| Axis T at 10 De [K] | 2033-2240 | 2050-2297 |
| Core length [De] | 12.8-13.8 | 13.6-14.8 |

Report these bands, not single values. Cell size at the Mach disk is 0.066 / 0.033 / 0.016 De (coarse / medium / fine).

Table 8.3. Correlations. Each is used within, or outside, its stated validity.

| Quantity | CFD | Correlation | Deviation | Validity |
|---|---|---|---|---|
| Mach disk x | 2.676 De (fine) | Lewis & Carlson: 0.69 Me sqrt(gamma pe/pa) De = 2.663 De | +0.5 % | Within range (Me about 2, pe/pa 3.2) |
| Shock-cell spacing | 3.96-4.10 De (fine); bands 3.7-4.4 | Prandtl-Pack/Tam: 4.82 De | -15 to -18 % | Weak-shock vortex-sheet result, used outside its range: this jet has a Mach disk. Not a pass/fail |
| Reflection type | Mach reflection, small disk | pe/pa about 3.2 with Me 2 lies in the Mach-disk regime | Consistent | The brief's eps 3 / pe/pa 1.6 case would be a weaker structure; eps is 2 here |

Table 8.4. Code-to-code checks. Values are own against OpenFOAM. OpenFOAM stopped at 1.0 / 1.15 ms with its jet front at 11.3 / 17.9 De, so comparisons are meaningful upstream of about 8 De only.

| Quantity | Own inviscid vs OF inviscid (1 ms) | Own RANS vs OF SST |
|---|---|---|
| Exit-plane thrust from fields [N] | 500.1 vs 494.0 (+1.25 %) | 500.1 vs 489.0 (+2.3 %) |
| Exit mdot [kg/s] | 0.2541 vs 0.2517 (+0.93 %) | 0.2541 vs 0.2499 (+1.7 %) |
| Mach disk x [De] | 2.709 vs 2.644 (+2.5 %) | 2.644 vs 2.841 (-7.0 %) |
| M max before disk | 3.690 vs 3.714 (-0.6 %) | 3.638 vs 3.805 (-4.4 %) |
| Axis rms, 0-8 De | M 0.45, p/pa 0.36, T 81 K | M 0.53, p/pa 0.35, T 264 K |

Table 8.5. Model sensitivities, all coarse grid. Single gas is compared with the two-species RANS run at 4 ms. The x0.5, x2 and no-Phi runs are compared with the two-species frame at 3 ms.

| Quantity | Single gas (exhaust everywhere) | Eddy viscosity x0.5 | Eddy viscosity x2 | No compressibility factor | v2 point vs v1 |
|---|---|---|---|---|---|
| Thrust | 0.000 % | +0.01 % | -0.02 % | -0.06 % | +0.01 % |
| Mach disk x | 0 % | -4.7 % | none found | none found | +2.5 % |
| Axis T at 20 De | -15.5 % (1861 vs 2204 K) | +3.3 % | -13 % | -41 % | -5.4 % |
| Axis T at 40 De | -30 % | +32 % | -23 % | -82 % | -5.7 % |
| Core length | -2.9 % | +124 % (30 De) | -57 % (5.7 De) | -79 % (2.9 De) | 0 % |
| Half-width of Z at 20 De | -20 % | -3.6 % | -72 % | -99 % | 0 % |

Reading:
- Thrust, mdot and the near-nozzle shock structure are insensitive to the gas and turbulence models.
- The mixing quantities (core length, far-field temperature, plume width) are set by the turbulence closure and are not predictive without measurement.
- The single-gas model is acceptable for thrust and the first shock cells. It underestimates the far-plume temperature by 15-30 %.

Afterburn grid and time study (`validation/results/afterburn_grid_time_v2.json`, v2.2):
- At 3.25 ms the coarse / medium / fine maxima are 174.0 / 177.3 / 179.2 K (GCI 1.8 %).
- The temporal band is 172.2-178.4 K (coarse) and 175.5-177.9 K (medium).
- The grid effect is not resolvable against the scatter; report 172-179 K.

Validation figures, in `validation/figs/`:
- `validation_grid_v2.png`: three levels.
- `validation_codes_v2.png`: own solver against OpenFOAM.
- `validation_models_v2.png`: gas and turbulence sensitivities.
- `validation_unsteady_v2.png`: temporal bands.
- `validation_v2op_v2.png`: v2 point against v1.
- `afterburn_grid_time_v2.png`.

## 9. Fluent cross-check package (prepared, not run)

`fluent-crosscheck/` v2.1 contains:
- README with GUI steps;
- coarse (20k) and medium (80k) meshes as Fluent `.msh` files, cell for cell identical to the own grids;
- the domain as STEP (mm) and edge CSVs, for remeshing under the 128k Student limit;
- gas properties and BCs as CSV/JSON;
- an untested TUI journal;
- comparison results and a template to fill in.

Limitation: the package is built at the v1 operating point (O/F 7.76, T0 2844.9 K), not the S230 v2 point. Per Table 8.5 the v2 point changes thrust by +0.01 %, the Mach disk by +2.5 % and axis temperatures by -5 to -6 %, so the shock-structure comparison stays valid; afterburning does not.

No Fluent licence was available to the author.

## 10. What the model cannot show

- **Soot and radiation.** There is no soot model and no radiative transfer. The synthetic photo uses an ASSUMED soot proxy.
- **Finite-rate chemistry and turbulence-chemistry interaction.** Afterburning is a fast-chemistry, mean-Z equilibrium bound. Real afterburning is lower, and possibly zero if the mixture quenches.
- **Nozzle boundary layer.** There is no nozzle boundary layer, so no viscous separation is predicted; at the floor this matters. The nozzle walls are slip.
- **Turbulence.** Turbulence is an algebraic closure with LITERATURE-UNVERIFIED constants. Mixing lengths are model-dependent (Table 8.5).
- **Exhaust gas model.** The exhaust is a calorically perfect gas with frozen calibrated gamma, which gives core temperature errors up to about -500/+30 K in the strongly expanded region (§4).
- **Geometry and setting.** The model is axisymmetric only (no gimbal angle, no 3-D structure) and has no ground plane, so no landing impingement or recirculation is modelled.
- **Duration.** Simulated time is 3-4 ms. The far field (> 15 De) is not statistically stationary, and the fine level covers only 0.25 ms.
- **No acoustics or plume loads on the vehicle.**

## 11. Case files, scripts and reproduction

| Path | Content |
|---|---|
| `scripts/own/plume2s.py`, `run_plume.py` | Solver and driver. Each run's exact arguments are in `ownruns/<run>/run.json`. Example: coarse is `run_plume.py OUT --level 0.5 --tend 4e-3 --frame 5e-5`; fine is `--level 2 --init m_2s_100/final.npz --keep_time --tend 3.25e-3`; the sweep adds `--ramp` with the segments in its run.json |
| `scripts/own/post_plume.py`, `validate_plume.py`, `frame_snapshot.py`, `test_grid.py` | Field figures, validation (v2.1a) and grid tests |
| `scripts/own/afterburn.py`, `afterburn_timegrid.py`, `plot_afterburn.py` | Afterburning v3 and the time-matched grid study (v2.2) |
| `scripts/own/synth_photo.py`, `make_anim.py`, `blender_prep.py`, `blender_render.py`, `blender_caption.py` | Images and animations |
| `scripts/own/of_post.py`, `diag_lts.py`, `make_fluent_package.py`, `write_fluent_mesh.py` | OpenFOAM post-processing (Z_T), FAILURE-CFD-02 diagnostics, Fluent package |
| `scripts/openfoam/make_case.py`, `openfoam_cases/run_serial.sh` | OpenFOAM case generator (wedge blockMesh). The `CFD_OPPOINTS` environment variable selects another combustion.json; leave it unset for the v1-point cases |
| `openfoam_cases/of_c100_inv/`, `of_c100_sst/` | Complete cases (`0/`, `constant/`, `system/`, last time directory, logs, `case_meta.json`) |
| `ownruns/<run>/` | `final.npz`, `history.csv`, `run.json`, snapshots, afterburn fields and figures. Also run logs, queue and lane scripts, and `lane_logs/` |
| `validation/results/` | `validation_v2.json` (v2.1a), `key_results_v2.csv`, centreline CSVs, `afterburn_grid_time_v2.json`; superseded `*_2level.*` and `validation_v2p1_firstrun_negative_gci.json` |
| `inputs/` | `combustion_v1.json` and `nozzle_contour_v1.csv` as used |

## 12. Failures, superseded evidence, unknowns and next closure

Failures and superseded evidence (all kept):
- **FAILURE-CFD-01.** OpenFOAM v1912 function objects (scalarTransport and Mach) crashed. Z is reconstructed from total enthalpy, and Mach is post-processed.
- **Wedge time step.** The wedge-face Courant term forced a tiny time step; a 20 deg wedge with tan vertex placement raised it from 8.3e-9 to 2.65e-8 s.
- **FAILURE-CFD-02.** The first closure used a Prandtl mixing length per column. Column-to-column jumps gave spotty mu_t up to 1.5 Pa s and destroyed the jet under local time stepping. Diagnostics are in `ownruns/failed_lts/`. It was replaced by the per-station exchange coefficient.
- **Broken mount.** Runs written to the broken network mount failed; their logs are in `ownruns/failed_mount/`. They were re-run locally.
- **Afterburn v1 and v2.** v1 gave a frozen T up to 3942 K, which is inconsistent. v2 conflated recombination with afterburning (537 K at Z = 1). Both are superseded by v3; their files are kept as `*_superseded`.
- **Validation v2.0.** It compared levels at different times; kept as `*_2level.*`. The GCI oscillatory safety-factor bug is fixed in v2.1.
- **First v2.1 run.** It gave a negative thrust GCI (p -0.12). v2.1a applies the 3x bound for p < 0.5.
- **Exit-plane field integral.** In v2.0 it under-read by 2.6 %. The solver integral is now primary; field and solver integrals agree within 0.05 % on the fine grid.
- **Packaging and queue issues.** `make_fluent_package` once picked the wrong file, and job 092 produced no frames; both are corrected. Job 093 was stopped deliberately and is not a failure.
- **OpenFOAM runtime.** Both runs stopped at the 2 h limit.

Unknowns:
- the real afterburning amount;
- luminous length and soot;
- separation at the floor;
- ground effect at landing;
- far-field mixing (model-dependent).

Next closure:
1. A Fluent run of the package by a third party; compare against the temporal bands.
2. A floor case with a viscous nozzle wall and a separation check.
3. A landing case with a ground plane at the landing height from gnc.json.
4. Static-fire high-speed video: shock-diamond spacing (expect about 4 De) and luminous plume. Compare with the QUALITATIVE synthetic image, not the ARTISTIC renders.
