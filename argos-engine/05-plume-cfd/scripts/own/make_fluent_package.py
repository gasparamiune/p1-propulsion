"""Build 05-plume-cfd/fluent-crosscheck/ (Combustion v2): geometry (STEP + CSV), Fluent meshes (<= 128k cells for the
Student licence), gas properties, boundary conditions, solver settings, an UNTESTED journal template, the results of the
primary solvers (own plume2s + OpenFOAM) to compare against, and a fill-in template for the Fluent results.

usage: python make_fluent_package.py OUTDIR VALIDATION_DIR
  VALIDATION_DIR = output of validate_plume.py (results/key_results_v2.csv, results/centreline_*_v2.csv, validation_v2.json)
"""
from __future__ import annotations
import csv, json, math, os, shutil, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import plume2s as P

PA, TA = 101325.0, 288.15
RU = 8314.462618


def domain_outline(level=1.0):
    J, pts, Rbody = P.load_geometry()
    g = P.Grid(pts, Rbody, level=level)
    xs = pts[:, 0] - pts[-1, 0]; rs = pts[:, 1]
    sel = xs >= g.x_in - 1e-12
    wall = [(g.x_in, g.r_in)] + [(x, r) for x, r in zip(xs[sel], rs[sel]) if x > g.x_in + 1e-9]
    L = float(g.X[-1, 0]); Rout = float(g.R[0, -1]); xb = float(g.X[0, -1])
    outline = ([(g.x_in, 0.0), (L, 0.0), (L, Rout), (xb, Rout), (xb, Rbody), (0.0, Rbody), (0.0, g.Re)]
               + wall[::-1][1:])
    edges = {
        'axis': [(g.x_in, 0.0), (L, 0.0)],
        'outlet': [(L, 0.0), (L, Rout)],
        'farfield': [(L, Rout), (xb, Rout)],
        'coflow': [(xb, Rout), (xb, Rbody)],
        'body_wall': [(xb, Rbody), (0.0, Rbody)],
        'base': [(0.0, Rbody), (0.0, g.Re)],
        'nozzle_wall': wall[::-1],
        'inlet': [(g.x_in, g.r_in), (g.x_in, 0.0)],
    }
    return g, outline, edges


def write_geometry(outdir):
    g, outline, edges = domain_outline()
    gd = os.path.join(outdir, 'geometry'); os.makedirs(gd, exist_ok=True)
    with open(os.path.join(gd, 'domain_edges_mm.csv'), 'w', newline='') as f:
        f.write('# 2D axisymmetric fluid domain, x along the axis (nozzle exit plane at x = 0), y = radius, millimetres. '
                'Named edges = boundary zones. Source: interfaces/combustion.json v1 nozzle contour (unchanged in v2).\n')
        w = csv.writer(f); w.writerow(['edge', 'point', 'x_mm', 'y_mm'])
        for k, pts in edges.items():
            for i, (x, y) in enumerate(pts):
                w.writerow([k, i, f'{x*1e3:.5f}', f'{y*1e3:.5f}'])
    with open(os.path.join(gd, 'domain_outline_curve_mm.txt'), 'w') as f:
        for i, (x, y) in enumerate(outline + [outline[0]]):
            f.write(f'1 {i+1} {x*1e3:.5f} {y*1e3:.5f} 0.0\n')
    ok = False; area = None
    try:
        import cadquery as cq
        wire = cq.Wire.makePolygon([cq.Vector(x * 1e3, y * 1e3, 0) for x, y in outline], close=True)
        face = cq.Face.makeFromWires(wire)
        cq.exporters.export(cq.Workplane('XY').add(face), os.path.join(gd, 'domain_2d_axisym_mm.step'))
        ok = True; area = face.Area()
    except Exception as e:
        print('STEP export failed:', e)
    return dict(step=ok, face_area_mm2=area, De_mm=g.De * 1e3, Rt_mm=g.Rt * 1e3, Re_mm=g.Re * 1e3, x_in_mm=g.x_in * 1e3,
                r_in_mm=g.r_in * 1e3, Rbody_mm=g.Rbody * 1e3, L_down_mm=float(g.X[-1, 0]) * 1e3,
                R_out_mm=float(g.R[0, -1]) * 1e3, x_b_mm=float(g.X[0, -1]) * 1e3, x_throat_mm=g.x_t * 1e3)


def write_meshes(outdir):
    import write_fluent_mesh as W
    md = os.path.join(outdir, 'mesh'); os.makedirs(md, exist_ok=True)
    info = {}
    for level, name in ((0.5, 'argos_plume_coarse_20k.msh'), (1.0, 'argos_plume_medium_80k.msh')):
        g, nodes, cid, zones = W.build(level)
        v = W.verify(g, nodes, cid, zones)
        if v['bad_orientation'] or v['cells_with_not_4_faces']:
            raise SystemExit(f'mesh verification failed {v}')
        info[name] = dict(level=level, verify=v, **W.write(os.path.join(md, name), g, nodes, cid, zones, level),
                          min_cell_dx_mm=float(g.dI[g.region != 3].min() * 1e3), min_cell_dr_mm=float(g.dJ[g.region != 3].min() * 1e3))
    info['fine_320k_note'] = 'The fine level (plume2s level 2, ~320k cells) exceeds the Student limit and is not exported.'
    json.dump(info, open(os.path.join(md, 'mesh_info.json'), 'w'), indent=1, default=int)
    return info


def gas(outdir):
    sys.path.insert(0, os.path.join(HERE, '..', 'openfoam'))
    import make_case
    J, pts, Rbody = make_case.load_interface()
    cs = make_case.chamber_state(J, 1.0)
    g, R, T0, p0 = cs['gamma_eff'], cs['R_eff'], cs['T0'], cs['Pc']
    cp = g * R / (g - 1)
    # inlet static state at A/At = 2.56 (subsonic, isentropic)
    from scipy.optimize import brentq
    AR = lambda M: (1 / M) * ((2 / (g + 1)) * (1 + (g - 1) / 2 * M * M)) ** ((g + 1) / (2 * (g - 1)))
    Min = brentq(lambda M: AR(M) - 2.56, 1e-3, 0.999)
    p_in = p0 * (1 + (g - 1) / 2 * Min ** 2) ** (-g / (g - 1))
    T_in = T0 / (1 + (g - 1) / 2 * Min ** 2)
    out = dict(
        version='v2', date='2026-10-12',
        operating_point=dict(thrust_N=500.0, Pc_Pa=p0, OF=cs['OF'], note='combustion.json v1 max-thrust point (O/F 7.76); '
                             'the v2 grain runs O/F ~10.5 at max with the nominal law (inside the regression band 7-15): '
                             'the plume CFD stays at the v1 point (see 05-plume-cfd/REPORT.md)'),
        exhaust=dict(model='calorically perfect ideal gas calibrated on CEA (shifting) so that pe/pc at eps 2 matches CEA',
                     gamma=g, R_J_kgK=R, molecular_weight_kg_kmol=RU / R, cp_J_kgK=cp,
                     viscosity_Pa_s=1.004e-4, thermal_conductivity_W_mK=1.004e-4 * cp / 0.693,
                     transport_note='CEA frozen chamber values (thermal_bc_max_v1.csv header); irrelevant for the inviscid case, '
                                    'negligible against turbulent transport in the plume',
                     T0_K=T0, T0_note='delivered stagnation temperature eta_c*^2 Tc with eta_c* 0.92 (Tc CEA 3361 K)',
                     cstar_delivered_m_s=cs['cstar_del']),
        air=dict(gamma=1.4, R_J_kgK=287.05, molecular_weight_kg_kmol=RU / 287.05, cp_J_kgK=1.4 * 287.05 / 0.4,
                 viscosity_Pa_s=1.79e-5, thermal_conductivity_W_mK=0.0253),
        mixture=dict(species=['exhaust', 'air'], density='ideal-gas (mixture R = sum Y_i R_i)', cp='mixing-law (mass weighted)',
                     reactions='none (frozen): afterburning is a post-processed fast-chemistry estimate in the own solver',
                     turbulent_Schmidt=0.7, turbulent_Prandtl=0.7),
        inlet=dict(location_x_mm=None, area_ratio=2.56, total_pressure_Pa=p0, total_temperature_K=T0, Y_exhaust=1.0,
                   M_estimate=Min, static_pressure_estimate_Pa=p_in, static_temperature_estimate_K=T_in,
                   direction='own solver: flow angle varies linearly from 0 on the axis to -45 deg (convergent wall angle) at '
                             'the wall; Fluent: normal-to-boundary is acceptable (difference confined to the convergent)'),
        ambient=dict(p_Pa=PA, T_K=TA, coflow_velocity_m_s=5.0, Y_exhaust=0.0),
        expected=dict(mdot_throat_kg_s_own_medium=0.25397, thrust_exit_N_own_medium=500.6))
    return out


def write_setup(outdir, gasd, geo):
    sd = os.path.join(outdir, 'setup'); os.makedirs(sd, exist_ok=True)
    gasd['inlet']['location_x_mm'] = geo['x_in_mm']
    json.dump(gasd, open(os.path.join(sd, 'gas_and_bc_v2.json'), 'w'), indent=1, default=float)
    e, a = gasd['exhaust'], gasd['air']
    with open(os.path.join(sd, 'gas_properties_v2.csv'), 'w', newline='') as f:
        f.write('# Two-species non-reacting mixture for the Fluent cross-check (SI). Exhaust = CEA-calibrated perfect gas '
                '(combustion.json v1 max-thrust point). SIM/CEA.\n')
        w = csv.writer(f); w.writerow(['species', 'molecular_weight_kg_kmol', 'cp_J_kgK', 'gamma', 'R_J_kgK', 'viscosity_Pa_s',
                                       'thermal_conductivity_W_mK'])
        w.writerow(['exhaust', f"{e['molecular_weight_kg_kmol']:.4f}", f"{e['cp_J_kgK']:.2f}", f"{e['gamma']:.6f}", f"{e['R_J_kgK']:.4f}",
                    e['viscosity_Pa_s'], f"{e['thermal_conductivity_W_mK']:.4f}"])
        w.writerow(['air', f"{a['molecular_weight_kg_kmol']:.4f}", f"{a['cp_J_kgK']:.2f}", '1.4', '287.05', a['viscosity_Pa_s'],
                    a['thermal_conductivity_W_mK']])
    i = gasd['inlet']
    with open(os.path.join(sd, 'boundary_conditions_v2.csv'), 'w', newline='') as f:
        f.write('# Fluent boundary conditions by mesh zone name (zones are named in the .msh files). Absolute pressures: set the '
                'operating pressure to 0 Pa. SI.\n')
        w = csv.writer(f)
        w.writerow(['zone', 'fluent_type', 'settings'])
        w.writerow(['inlet', 'pressure-inlet', f"total p {i['total_pressure_Pa']:.0f} Pa; total T {i['total_temperature_K']:.2f} K; "
                    f"supersonic/initial gauge p {i['static_pressure_estimate_Pa']:.0f} Pa; Y_exhaust 1; turbulence: intensity 5 %, "
                    f"hydraulic diameter {2*geo['r_in_mm']:.2f} mm"])
        w.writerow(['coflow', 'velocity-inlet', 'axial velocity 5 m/s; T 288.15 K; Y_exhaust 0; intensity 1 %, viscosity ratio 10 '
                    '(entrainment inflow upstream of the base plane)'])
        w.writerow(['outlet', 'pressure-outlet', 'p 101325 Pa; backflow T 288.15 K; backflow Y_exhaust 0; backflow intensity 1 %, ratio 10'])
        w.writerow(['farfield', 'pressure-outlet', 'p 101325 Pa; backflow T 288.15 K; backflow Y_exhaust 0 (entrainment boundary)'])
        w.writerow(['axis', 'axis', '-'])
        for z in ('nozzle_wall', 'base', 'body_wall'):
            w.writerow([z, 'wall', 'adiabatic; specified shear 0 (slip) to match the own solver (no nozzle boundary layer). '
                        'Optional extra run: no-slip with SST to show the boundary-layer effect.'])


JOURNAL = r""";; ARGOS-H1 plume cross-check - Fluent TUI journal TEMPLATE (UNTESTED: no Fluent licence was available to the author).
;; The README lists the same steps for the GUI, which are the reference. Check each command against your Fluent version.
/file/read-case mesh/argos_plume_medium_80k.msh
/mesh/check
/define/models/axisymmetric? yes
/define/models/solver/density-based-implicit yes
/define/operating-conditions/operating-pressure 0
/define/models/energy? yes
;; case F1 (inviscid): /define/models/viscous/inviscid yes
/define/models/viscous/kw-sst? yes
/define/models/species/species-transport? yes mixture-template
;; materials: create 'exhaust' (ideal-gas, cp and MW from setup/gas_properties_v2.csv) and 'air' with the listed cp,
;; mixture species = exhaust, air (last species = air); reactions off -> done in the GUI (Materials panel)
;; boundary conditions: setup/boundary_conditions_v2.csv (GUI Boundary Conditions panel)
/solve/set/discretization-scheme/amg-c 1
/solve/set/courant-number 1
/solve/initialize/hyb-initialization
/solve/iterate 500
/solve/set/courant-number 5
/solve/iterate 5000
/file/write-case-data argos_plume_F3_medium.cas.h5
"""


README = """# Fluent cross-check package: ARGOS-H1 hybrid engine plume (100 % thrust, sea level)

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
| Chamber stagnation pressure p0 | {p0:.0f} Pa |
| Delivered stagnation temperature T0 | {T0:.1f} K (`eta_c*^2 Tc`) |
| Exhaust gas | perfect gas, gamma {g:.5f}, R {R:.3f} J/kg/K (MW {MW:.3f}), cp {cp:.1f} J/kg/K. Calibrated so that pe/pc at eps 2 equals CEA. |
| Ambient | 101325 Pa, 288.15 K |
| Coflow | 5 m/s around the 44 mm body |

### Expected results

Primary solver ({grid_label}), from `results/{vfile}`:

- throat mass flow {mdot:.4f} kg/s (1-D: {mdot1d:.4f} kg/s)
- exit-plane thrust {F:.1f} N (1-D ideal x divergence factor: {F1d:.1f} N)
- underexpanded exit: pe/pa {pe:.2f}, Me {Me:.2f} (1-D)
- Mach disk at x/De {xmd:.2f} (Lewis-Carlson correlation: {xmd_lc:.2f})
- shock-cell spacing from the axis Mach maxima: first {sp1:.2f} De, mean of three {sp3:.2f} De; Prandtl-Pack/Tam: {ls:.2f} De.
  The spacing still moves with the grid ({grid_note}); compare it on the same mesh.
- {unsteady_note}
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
   - Create the fluid `exhaust` from `setup/gas_properties_v2.csv`: ideal-gas, constant cp {cp:.1f} J/kg/K, molecular
     weight {MW:.4f} kg/kmol.
   - Set the air cp to 1004.7 J/kg/K.
   - Mixture properties:
     - density: ideal-gas
     - cp: mixing-law
     - viscosity and conductivity: mass-weighted or ideal-gas mixing law (minor effect)
     - mass diffusivity: dilute approximation with the default value. Turbulent Schmidt number 0.7.
   - For the single-gas check (F1s), give air the exhaust properties.
5. **Boundary conditions:** set each zone as in `setup/boundary_conditions_v2.csv`.
   - The walls are **slip**: specified shear 0. This is how the own solver and the OpenFOAM inviscid case treat them.
   - The inlet total pressure is {p0:.0f} Pa and the total temperature {T0:.2f} K.
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
"""


def write_results(outdir, vdir):
    rd = os.path.join(outdir, 'results'); os.makedirs(rd, exist_ok=True)
    src = os.path.join(vdir, 'results')
    n = 0
    if os.path.isdir(src):
        for f in os.listdir(src):
            if f.endswith('.csv') or f.endswith('.json'):
                shutil.copy(os.path.join(src, f), os.path.join(rd, f)); n += 1
    with open(os.path.join(rd, 'fluent_results_template_v2.csv'), 'w', newline='') as f:
        f.write('# Fill in one row per Fluent case (same definitions as key_results_v2.csv). Units SI; x, r in exit diameters.\n')
        w = csv.writer(f)
        w.writerow(['case', 'mesh', 'model', 'flux_scheme', 'iterations', 'thrust_exit_N', 'mdot_throat_kg_s', 'x_mach_disk_De',
                    'r_mach_disk_De', 'M_before_disk', 'peak1_x_De', 'peak2_x_De', 'peak3_x_De', 'peak4_x_De', 'T_axis_10De_K',
                    'T_axis_20De_K', 'Z_axis_20De', 'r_half_Z_20De', 'notes'])
        for c in ('F1s', 'F3', 'F3s'):
            w.writerow([c] + [''] * 18)
    return n


if __name__ == '__main__':
    out, vdir = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    geo = write_geometry(out)
    mi = write_meshes(out)
    gd = gas(out)
    write_setup(out, gd, geo)
    open(os.path.join(out, 'setup', 'fluent_journal_template.jou'), 'w').write(JOURNAL)
    e = gd['exhaust']
    # v2.1: explicit file (v2.0 took the last sorted validation_v*.json, which is validation_v2_2level.json once the
    # superseded two-level copy exists)
    vfile = 'validation_v2.json'; VJ = json.load(open(os.path.join(vdir, 'results', vfile)))
    run = 'own_f_2s_rans' if 'own_f_2s_rans' in VJ['correlations'] else 'own_m_2s_rans'
    cc, tv, od = VJ['correlations'][run], VJ['thrust_vs_1d'][run], VJ['one_d']
    lvl = ('own_c_2s_rans_t3p25', 'own_m_2s_rans_t3p25', 'own_f_2s_rans')
    if not all(k in VJ['correlations'] for k in lvl):
        lvl = ('own_c_2s_rans', 'own_m_2s_rans', 'own_f_2s_rans')
    gl = [(k, VJ['correlations'][k]['spacing_first_mach']) for k in lvl if k in VJ['correlations']]
    grid_note = 'first spacing at t 3.25 ms ' + ', '.join(f"{k.split('_')[1]} {v:.2f} De" for k, v in gl)
    tb = VJ.get('temporal_band', {})
    bm, bc = tb.get('medium_v1_2.50_3.25ms') or {}, tb.get('coarse_v1_2.50_3.25ms') or {}
    def rng(b, q, f='{:.2f}'):
        return (f.format(b[q]['min']) + '-' + f.format(b[q]['max'])) if q in b else 'n/a'
    unsteady_note = ('The own solution is unsteady (shear-layer/Mach-disk motion; validation_v2.json temporal_band, '
                     'window 2.5-3.25 ms): Mach disk x/De ' + rng(bc, 'x_mach_disk_De') + ' (coarse), ' + rng(bm, 'x_mach_disk_De') +
                     ' (medium); first Mach maximum x/De ' + rng(bm, 'machpk1_x_De') + ' (medium); axis T at 10 De ' +
                     rng(bm, 'T_axis_10De_K', '{:.0f}') + ' K (medium). A steady Fluent result is compared with these bands, '
                     'not with one instant.')
    open(os.path.join(out, 'README.md'), 'w').write(README.format(p0=gd['inlet']['total_pressure_Pa'], T0=e['T0_K'], g=e['gamma'],
                                                                 R=e['R_J_kgK'], MW=e['molecular_weight_kg_kmol'], cp=e['cp_J_kgK'],
                                                                 grid_label='fine grid' if run == 'own_f_2s_rans' else 'medium grid',
                                                                 vfile=vfile, mdot=tv['mdot_cfd'], mdot1d=od['mdot'], F=tv['F_cfd'],
                                                                 F1d=od['F_ideal_lambda_N'], pe=od['pe_over_pa'], Me=od['Me'],
                                                                 xmd=cc['x_md_cfd'], xmd_lc=od['x_md_lewis_carlson_De'],
                                                                 sp1=cc['spacing_first_mach'], sp3=cc['spacing_mean3_mach'],
                                                                 ls=od['Ls_prandtl_pack_tam_De'], grid_note=grid_note,
                                                                 unsteady_note=unsteady_note))
    n = write_results(out, vdir)
    sd = os.path.join(out, 'scripts'); os.makedirs(sd, exist_ok=True)
    for f in ('make_fluent_package.py', 'write_fluent_mesh.py', 'plume2s.py', 'validate_plume.py', 'post_plume.py'):
        shutil.copy(os.path.join(HERE, f), os.path.join(sd, f))
    print(json.dumps(dict(geometry=geo, meshes={k: v for k, v in mi.items() if k.endswith('.msh')}, results_files=n), indent=1, default=float))
