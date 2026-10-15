# Fluent cross-check package: ARGOS-H1 hybrid engine plume (100 % thrust, sea level)

Combustion / 05-plume-cfd / fluent-crosscheck **v2.1**, 2026-10-12 (v2.1: comparison numbers from the time-matched
validation v2.1; the own solution is unsteady, see the band below).

**Status:** prepared by Combustion. Not run in Fluent: no licence was available to the author. Nothing here has been
reviewed independently yet (*Por revisar*).

**Primary results:** the own solver *plume2s*, cross-checked against OpenFOAM `rhoCentralFoam`. Fluent is a third,
independent cross-check. The comparison numbers are in `results/`.

## 1. What to compute

A 2-D axisymmetric case: the N2O/ABS nozzle (exit ratio 2, 15 deg cone) and the free plume at sea level.

| Item | Value |
|---|---|
| Throat diameter | 13.724 mm |
| Exit diameter De | 19.409 mm |
| Chamber stagnation pressure p0 | 2499311 Pa |
| Delivered stagnation temperature T0 | 2844.9 K (`eta_c*^2 Tc`) |
| Exhaust gas | perfect gas, gamma 1.13676, R 296.931 J/kg/K (MW 28.001), cp 2468.1 J/kg/K. Calibrated so that pe/pc at eps 2 equals CEA. |
| Ambient | 101325 Pa, 288.15 K |
| Coflow | 5 m/s around the 44 mm body |

### Expected results

Primary solver (fine grid), from `results/validation_v2.json`:

- throat mass flow 0.2542 kg/s (1-D: 0.2558 kg/s)
- exit-plane thrust 500.8 N (1-D ideal x divergence factor: 505.8 N)
- underexpanded exit: pe/pa 3.24, Me 2.01 (1-D)
- Mach disk at x/De 2.68 (Lewis-Carlson correlation: 2.66)
- shock-cell spacing from the axis Mach maxima: first 3.96 De, mean of three 4.10 De; Prandtl-Pack/Tam: 4.82 De.
  The spacing still moves with the grid (first spacing at t 3.25 ms c 4.13 De, m 3.97 De, f 3.96 De); compare it on the same mesh.
- The own solution is unsteady (shear-layer/Mach-disk motion; validation_v2.json temporal_band, window 2.5-3.25 ms): Mach disk x/De 2.64-2.77 (coarse), 2.58-2.74 (medium); first Mach maximum x/De 6.76-7.17 (medium); axis T at 10 De 2050-2297 K (medium). A steady Fluent result is compared with these bands, not with one instant.
- `results/*_2level.*` are the superseded v2.0 comparison (levels at different times), kept as evidence only.

## 2. Files

- `mesh/argos_plume_coarse_20k.msh` and `mesh/argos_plume_medium_80k.msh`: Fluent ASCII 2-D meshes.
  - Units are metres. x is the symmetry axis, y is the radius ≥ 0.
  - Named zones: `inlet`, `coflow`, `outlet`, `farfield`, `axis`, `nozzle_wall`, `base`, `body_wall`, and the fluid `fluid`.
  - These are the own solver's coarse and medium grids, cell for cell, so the comparison has no interpolation error.
  - Face orientation was verified when written (`mesh/mesh_info.json`).
  - If Fluent reports left-handed faces, run `/mesh/repair-improve/repair-face-handedness`.
  - The fine level (~320k cells) is over the Student limit and is not included.
- `geometry/domain_2d_axisym_mm.step`, `geometry/domain_edges_mm.csv`, `geometry/domain_outline_curve_mm.txt`: the same fluid
  domain in millimetres, for remeshing in Fluent Meshing or ANSYS Meshing.
  - Recipe to stay under 128k cells: about 64 cells across the nozzle radius and 32 axial cells in each of the convergent
    and divergent.
  - Plume cells grow from 0.33 mm at the exit plane at a ratio ≤ 1.006 axially, out to x = 45 De and r = 12 De.
- `setup/gas_properties_v2.csv`, `setup/boundary_conditions_v2.csv`, `setup/gas_and_bc_v2.json`: gas properties and
  boundary conditions per zone.
- `setup/fluent_journal_template.jou`: a TUI journal. It is **untested**; the GUI steps below are the reference.
- `results/key_results_v2.csv`: own solver (coarse, medium and fine where available) and OpenFOAM numbers to compare against.
- `results/centreline_<run>_v2.csv`: axis profiles (x/De, Mach, p/pa, T, Z, u).
- `results/fluent_results_template_v2.csv`: the table to fill in with the Fluent results.

## 3. Set-up steps (Fluent GUI, Student edition)

1. **Launch and read the mesh**
   - Launch Fluent 2D, double precision.
   - File > Read > Mesh: `mesh/argos_plume_coarse_20k.msh` first (fast), then the medium mesh.
   - Run Mesh > Check. The minimum volume must be positive.
2. **General**
   - Solver Type: Density-Based.
   - 2D Space: **Axisymmetric**.
   - Time: Steady.
   - Operating Conditions: operating pressure **0 Pa**, so all pressures below are absolute.
3. **Models**
   - Energy: on.
   - Viscous: case F1 Inviscid; case F3 k-omega SST. Leave the optional compressibility correction off, and record which
     setting you used.
   - Species Transport: on, no reactions. Mixture of two species, `exhaust` and `air` (air last).
4. **Materials**
   - Create the fluid `exhaust` from `setup/gas_properties_v2.csv`: ideal-gas, constant cp 2468.1 J/kg/K, molecular
     weight 28.0013 kg/kmol.
   - Set the air cp to 1004.7 J/kg/K.
   - Mixture properties:
     - density: ideal-gas
     - cp: mixing-law
     - viscosity and conductivity: mass-weighted or ideal-gas mixing law (minor effect)
     - mass diffusivity: dilute approximation with the default value. Turbulent Schmidt number 0.7.
   - For the single-gas check (F1s), give air the exhaust properties.
5. **Boundary conditions:** set each zone as in `setup/boundary_conditions_v2.csv`.
   - The walls are **slip**: specified shear 0. This is how the own solver and the OpenFOAM inviscid case treat them.
   - The inlet total pressure is 2499311 Pa and the total temperature 2844.87 K.
6. **Solution methods**
   - Formulation: Implicit.
   - Flux: Roe-FDS. AUSM is an alternative; note which one you used.
   - Gradient: least squares cell based.
   - Flow and turbulence: second-order upwind. Start first order for about 300 iterations, then switch.
7. **Initialisation and run**
   - Initialise with hybrid initialisation, or standard initialisation at ambient conditions (101325 Pa, 288.15 K, Y = 0)
     followed by a patch of the nozzle interior (x < 0, r < 10 mm) to p0 and T0.
   - Courant number 1 for 500 iterations, then 5.
   - Monitors:
     - mass flow at `inlet`. Expect about 0.254 kg/s for the full 2π. If you get about 0.0404 kg/s, the report is per
       radian; multiply all integrals by 2π.
     - thrust on a line surface in the exit plane. Create the line from (-0.00001, 0) to (-0.00001, 0.0097) m and define
       the custom field `rho*u^2 + p - 101325`. Report the area integral.
     - axis Mach number at x = 2.5 De = 0.0485 m.
   - Converged when the scaled residuals are below 1e-4 and the mass flow and thrust change by less than 0.1 % over 1000
     iterations.
8. **Post-processing**
   - Create a line surface on the axis from (-0.02, 1e-6) to (0.87, 1e-6).
   - Export Mach, absolute pressure, static temperature and exhaust mass fraction along it as ASCII.
   - Extract the comparison quantities as in `validate_plume.py`:
     - Mach disk: the axis station where the Mach number drops from above 1 to below 1, for x/De < 8.
     - Mach-disk radius: the subsonic pocket just behind it.
     - Shock-cell peaks: axis pressure maxima downstream of the disk.
   - Fill in `results/fluent_results_template_v2.csv`.

## 4. Cases

| Case | Mesh | Model | Compare with (results/) |
|---|---|---|---|
| F1s | coarse, then medium | inviscid, single gas | own_c_1s_inv, of_c_1s_inv |
| F3 | coarse and medium | SST, two species | own_c_2s_rans, own_m_2s_rans |
| F3s (optional) | coarse | SST, single gas | own_c_1s_rans, of_c_1s_sst |

## 5. How to read the comparison

The three codes share the geometry, the gas calibration and the boundary conditions. They differ in:

- numerical scheme: HLLC-MUSCL (own), Kurganov-Tadmor central (OpenFOAM), Roe or AUSM (Fluent)
- turbulence model: own algebraic eddy viscosity with a compressibility factor, SST (OpenFOAM, Fluent)
- for OpenFOAM, a 20-degree wedge instead of a 2-D axisymmetric formulation

Inviscid near-field results should agree:

- Mach-disk position and radius within a few cells
- thrust and mass flow within about 0.5 %

Turbulent far-field results (core length, centreline temperature decay) are model-dependent and are expected to differ by
tens of percent. That spread is the modelling uncertainty, not an error to be tuned away.

Not modelled by any of the three: afterburning chemistry, soot, radiation, and the nozzle boundary layer. See
05-plume-cfd/REPORT.md.
