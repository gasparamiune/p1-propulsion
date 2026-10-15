"""OpenFOAM v1912 rhoCentralFoam case generator: N2O/ABS nozzle + plume, 2D axisymmetric wedge.
(Combustion / 05-plume-cfd, v1, 2026-10-11)

Reads the gas-path contour and the operating point from interfaces/combustion.json (never hard-coded),
computes the chamber state with CEA (RocketCEA, card ABS_TYP_v1) and calibrates a single calorically
perfect 'exhaust gas' (gamma_eff, MW_eff) that reproduces CEA shifting-equilibrium exit pressure ratio
at the design area ratio and the delivered c* (T0 = Tc * eta_c*^2).  SINGLE-GAS MODEL: the ambient
air is represented by the same gas at 288 K; the error this causes is quantified with the own two-species
solver (plume2s) - see REPORT.md.

Domain (x along the axis, exit plane at x=0, units of exit diameter De):
  nozzle interior from the convergent (A/At = AR_IN) to the exit; plume to X_DOWN*De downstream,
  R_OUT*De radially; ambient region beside the nozzle body (cylinder r = R_BODY) from -X_UP*De.
Usage: python make_case.py <case_dir> --level {coarse,medium,fine} --model {inviscid,sst}
       [--frac 1.0] [--endTime 3e-3] [--wedge 20]

Wedge angle note: rhoCentralFoam's Courant number (centralCourantNo.H) sums amaxSf over ALL faces, including the
two wedge faces, whose c*|Sf| contribution scales as c/(r sin(theta/2)); with a 5 deg wedge this artefact (not a
stability limit: no flux crosses a wedge face) cut the time step by ~5-10x on the near-axis cells.  Vertices are
placed at (x, r, +-r tan(theta/2)) so the cell-centre y equals the radius; then face areas and volumes reproduce the
axisymmetric finite-volume metrics exactly for any theta (the p/r hoop term is exact); the remaining wedge-angle
error is the Gauss-gradient hoop strain v*cos(theta/2)/r (viscous/turbulence terms only): 1.5 % at 20 deg.
"""
from __future__ import annotations
import argparse, csv, json, math, os, sys
import numpy as np

ENGINE = os.environ.get('ENGINE_ROOT', '/mnt/project-files/engine')
SRC = os.environ.get('COMB_SRC', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
sys.path.insert(0, os.path.abspath(SRC))

PA = 101325.0
TA = 288.15
RU = 8314.462618

LEVELS = {  # cells: radial core, radial shear (Re..Rbody), radial outer, axial conv, axial div, plume first dx [m], growth
    'coarse': dict(n_core=16, n_shear=12, n_outer=34, n_conv=18, n_div=14, dx0=0.6e-3, n_up=16),
    'medium': dict(n_core=32, n_shear=24, n_outer=60, n_conv=36, n_div=28, dx0=0.3e-3, n_up=28),
    'fine':   dict(n_core=64, n_shear=48, n_outer=110, n_conv=72, n_div=56, dx0=0.15e-3, n_up=50),
}
X_DOWN, R_OUT, X_UP = 45.0, 12.0, 4.0
AR_IN = 2.56            # A/At at the domain inlet in the convergent (r_in = 1.6 Rt)


CFD_INPUTS = os.environ.get('CFD_INPUTS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'inputs'))


def load_interface():
    """Frozen CFD inputs: combustion.json v1 + nozzle_contour_v1.csv copied into cfd/inputs/ (identical to the published
    v1 files; the shared mount became unavailable on 2026-10-12). Set CFD_INPUTS to use another snapshot."""
    J = json.load(open(os.path.join(CFD_INPUTS, 'combustion_v1.json')))
    cont_fn = os.path.join(CFD_INPUTS, 'nozzle_contour_v1.csv')
    rows = []
    with open(cont_fn) as f:
        for line in f:
            if line.startswith('#') or line.startswith('x_face'):
                continue
            p = line.strip().split(',')
            rows.append((float(p[1]), float(p[2])))   # x_throat, r
    pts = np.array(rows)
    Rbody = J['gas_path']['graphite_throat_insert_envelope']['outer_diameter_m']['v'] / 2
    # 2026-10-12: operating-point override. CFD_OPPOINTS = path of another combustion.json (e.g. v2.1 S230 points):
    # only operating_points.throttle_points_20C_initial_port is taken from it; the nozzle geometry (throat
    # coordinates), body radius and eps stay the v1 snapshot (the v2 contour is the v1 shape shifted by +30 mm in
    # x_face only). Default (variable unset): unchanged v1 behaviour.
    op = os.environ.get('CFD_OPPOINTS')
    if op:
        J2 = json.load(open(op))
        J['operating_points'] = dict(J['operating_points'])
        J['operating_points']['throttle_points_20C_initial_port'] = J2['operating_points']['throttle_points_20C_initial_port']
        J['_oppoints_source'] = dict(path=os.path.abspath(op), version=J2.get('version'), date=J2.get('date'))
    return J, pts, Rbody


def chamber_state(J, frac=1.0):
    """Delivered chamber state for the operating point 'frac' of max thrust (initial port, 20 C)."""
    import cea_cards
    from rocketcea.cea_obj_w_units import CEA_Obj
    cea_cards.register_all()
    tp = [p for p in J['operating_points']['throttle_points_20C_initial_port'] if abs(p['fraction'] - frac) < 1e-6][0]
    Pc, OF = tp['Pc_Pa'], tp['OF']
    eps = J['gas_path']['nozzle']['expansion_ratio']['v']
    eta = 0.92
    c = CEA_Obj(oxName='N2O', fuelName='ABS_TYP_v1', pressure_units='Pa', cstar_units='m/s', temperature_units='K',
                isp_units='sec', sonic_velocity_units='m/s')
    Tc = c.get_Tcomb(Pc=Pc, MR=OF)
    cstar = c.get_Cstar(Pc=Pc, MR=OF)
    pcpe = c.get_PcOvPe(Pc=Pc, MR=OF, eps=eps)
    MWc, gc = c.get_Chamber_MolWt_gamma(Pc=Pc, MR=OF, eps=eps)
    MWe, ge = c.get_exit_MolWt_gamma(Pc=Pc, MR=OF, eps=eps)
    # gamma_eff: perfect gas reproducing CEA pe/pc at the same area ratio
    from scipy.optimize import brentq
    def pe_pc_perfect(g):
        def AR(M):
            return (1 / M) * ((2 / (g + 1)) * (1 + (g - 1) / 2 * M * M)) ** ((g + 1) / (2 * (g - 1)))
        M = brentq(lambda M: AR(M) - eps, 1.0001, 10)
        return (1 + (g - 1) / 2 * M * M) ** (-g / (g - 1)), M
    g_eff = brentq(lambda g: pe_pc_perfect(g)[0] - 1 / pcpe, 1.05, 1.6)
    pe_pc, Me = pe_pc_perfect(g_eff)
    T0 = Tc * eta ** 2
    cstar_del = cstar * eta
    Gam = math.sqrt(g_eff) * (2 / (g_eff + 1)) ** ((g_eff + 1) / (2 * (g_eff - 1)))
    R_eff = (cstar_del * Gam) ** 2 / T0           # c* = sqrt(R T0)/Gamma
    MW_eff = RU / R_eff
    cp_eff = g_eff * R_eff / (g_eff - 1)
    return dict(Pc=Pc, OF=OF, eps=eps, Tc=Tc, T0=T0, cstar=cstar, cstar_del=cstar_del, pcpe_cea=pcpe, gamma_chamber=gc,
                gamma_exit_cea=ge, MW_chamber=MWc, MW_exit=MWe, gamma_eff=g_eff, MW_eff=MW_eff, R_eff=R_eff, cp_eff=cp_eff,
                Me=Me, pe=Pc * pe_pc, frac=frac)


def header(cls, obj, loc='""'):
    return ("FoamFile\n{\n    version     2.0;\n    format      ascii;\n    class       %s;\n    location    %s;\n"
            "    object      %s;\n}\n" % (cls, loc, obj))


def grading_for(n, L, d0):
    """simpleGrading expansion ratio (last/first) so that n cells with first size d0 span L (geometric)."""
    from scipy.optimize import brentq
    if abs(L / n - d0) / d0 < 1e-3:
        return 1.0
    f = lambda r: d0 * (r ** n - 1) / (r - 1) - L
    r = brentq(f, 1.000001, 1.5) if L / n > d0 else brentq(f, 0.5, 0.999999)
    return r ** (n - 1)


def n_for(L, d0, growth):
    return int(math.ceil(math.log(1 + L * (growth - 1) / d0) / math.log(growth)))


def write_mesh(case, pts, st, lev, Rbody, wedge_deg):
    Rt = pts[:, 1].min()
    i_t = int(np.argmin(pts[:, 1]))
    Re = pts[-1, 1]; De = 2 * Re
    x_e = pts[-1, 0]
    # inlet in the convergent at r = sqrt(AR_IN)*Rt (upstream of throat)
    r_in = math.sqrt(AR_IN) * Rt
    up = pts[:i_t + 1]
    k = np.where(up[:, 1] <= r_in)[0][0]
    x_in = np.interp(r_in, [up[k, 1], up[k - 1, 1]], [up[k, 0], up[k - 1, 0]])
    conv = [(x_in, r_in)] + [tuple(p) for p in up[k:]]
    div = [tuple(p) for p in pts[i_t:]]
    x_t = pts[i_t, 0]
    # shift so exit plane is x=0
    sh = -x_e
    conv = [(x + sh, r) for x, r in conv]; div = [(x + sh, r) for x, r in div]
    x_in += sh; x_t += sh; x_e = 0.0
    L_down = X_DOWN * De; R_out = R_OUT * De; x_b = -X_UP * De
    a = math.radians(wedge_deg / 2)
    V = []
    def vid(x, r, side):
        if r == 0.0:
            p = (x, 0.0, 0.0)
        else:
            p = (x, r, (1 if side > 0 else -1) * r * math.tan(a))   # y = r exactly (planar wedge faces)
        for i, q in enumerate(V):
            if max(abs(q[0] - p[0]), abs(q[1] - p[1]), abs(q[2] - p[2])) < 1e-12:
                return i
        V.append(p)
        return len(V) - 1
    P2 = dict(A0=(x_in, 0.0), A1=(x_in, r_in), T0=(x_t, 0.0), T1=(x_t, Rt), E0=(0.0, 0.0), E1=(0.0, Re),
              E2=(0.0, Rbody), E3=(0.0, R_out), O0=(L_down, 0.0), O1=(L_down, Re), O2=(L_down, Rbody), O3=(L_down, R_out),
              U2=(x_b, Rbody), U3=(x_b, R_out))
    vb = {k: vid(*v, -1) for k, v in P2.items()}
    vf = {k: vid(*v, +1) for k, v in P2.items()}
    # plume axial cells
    growth = 1.0055 if lev['dx0'] >= 0.3e-3 else 1.0028
    if lev['dx0'] >= 0.6e-3:
        growth = 1.011
    n_pl = n_for(L_down, lev['dx0'], growth)
    g_pl = grading_for(n_pl, L_down, lev['dx0'])
    # outer radial: first cell ~ shear-region cell size, geometric to R_out
    d_sh = (Rbody - Re) / lev['n_shear']
    g_out = grading_for(lev['n_outer'], R_out - Rbody, d_sh)
    # ambient upstream axial: last cell ~ dx0*2 at x=0
    g_up = 1.0 / grading_for(lev['n_up'], -x_b, max(2 * lev['dx0'], 0.5e-3))
    blocks = []
    def hexb(c00, c10, c11, c01, n1, n2, grad):
        # c00=(x0,r0) c10=(x1,r0) c11=(x1,r1) c01=(x0,r1); back side then front
        blocks.append("    hex (%d %d %d %d %d %d %d %d) (%d %d 1) simpleGrading (%s)" % (
            vb[c00], vb[c10], vb[c11], vb[c01], vf[c00], vf[c10], vf[c11], vf[c01], n1, n2, grad))
    hexb('A0', 'T0', 'T1', 'A1', lev['n_conv'], lev['n_core'], '1 1 1')
    hexb('T0', 'E0', 'E1', 'T1', lev['n_div'], lev['n_core'], '1 1 1')
    hexb('E0', 'O0', 'O1', 'E1', n_pl, lev['n_core'], f'{g_pl:.6f} 1 1')
    hexb('E1', 'O1', 'O2', 'E2', n_pl, lev['n_shear'], f'{g_pl:.6f} 1 1')
    hexb('E2', 'O2', 'O3', 'E3', n_pl, lev['n_outer'], f'{g_pl:.6f} {g_out:.6f} 1')
    hexb('U2', 'E2', 'E3', 'U3', lev['n_up'], lev['n_outer'], f'{g_up:.6f} {g_out:.6f} 1')
    def pl(pts2, side):
        s = []
        for x, r in pts2:
            if r == 0:
                s.append('(%.9g 0 0)' % x)
            else:
                s.append('(%.9g %.9g %.9g)' % (x, r, side * r * math.tan(a)))
        return ' '.join(s)
    edges = []
    for side, vv in [(-1, vb), (1, vf)]:
        edges.append("    polyLine %d %d (%s)" % (vv['A1'], vv['T1'], pl(conv[1:-1], side)))
        edges.append("    polyLine %d %d (%s)" % (vv['T1'], vv['E1'], pl(div[1:-1], side)))
    def face(a1, a2):
        return "(%d %d %d %d)" % (vb[a1], vb[a2], vf[a2], vf[a1])
    bnd = f"""boundary
(
    inlet {{ type patch; faces ({face('A0','A1')}); }}
    nozzleWall {{ type wall; faces ({face('A1','T1')} {face('T1','E1')}); }}
    base {{ type wall; faces ({face('E1','E2')}); }}
    body {{ type wall; faces ({face('U2','E2')}); }}
    coflow {{ type patch; faces ({face('U2','U3')}); }}
    farfield {{ type patch; faces ({face('U3','E3')} {face('E3','O3')}); }}
    outlet {{ type patch; faces ({face('O0','O1')} {face('O1','O2')} {face('O2','O3')}); }}
    axis {{ type empty; faces ({face('A0','T0')} {face('T0','E0')} {face('E0','O0')}); }}
    front {{ type wedge; faces (
        ({vf['A0']} {vf['T0']} {vf['T1']} {vf['A1']}) ({vf['T0']} {vf['E0']} {vf['E1']} {vf['T1']}) ({vf['E0']} {vf['O0']} {vf['O1']} {vf['E1']})
        ({vf['E1']} {vf['O1']} {vf['O2']} {vf['E2']}) ({vf['E2']} {vf['O2']} {vf['O3']} {vf['E3']}) ({vf['U2']} {vf['E2']} {vf['E3']} {vf['U3']}) ); }}
    back {{ type wedge; faces (
        ({vb['A0']} {vb['A1']} {vb['T1']} {vb['T0']}) ({vb['T0']} {vb['T1']} {vb['E1']} {vb['E0']}) ({vb['E0']} {vb['E1']} {vb['O1']} {vb['O0']})
        ({vb['E1']} {vb['E2']} {vb['O2']} {vb['O1']}) ({vb['E2']} {vb['E3']} {vb['O3']} {vb['O2']}) ({vb['U2']} {vb['U3']} {vb['E3']} {vb['E2']}) ); }}
);
"""
    txt = header('dictionary', 'blockMeshDict') + "convertToMeters 1;\nvertices\n(\n" + \
        "\n".join("    (%.9g %.9g %.9g)" % p for p in V) + "\n);\nblocks\n(\n" + "\n".join(blocks) + "\n);\nedges\n(\n" + \
        "\n".join(edges) + "\n);\n" + bnd + "mergePatchPairs ();\n"
    os.makedirs(os.path.join(case, 'system'), exist_ok=True)
    open(os.path.join(case, 'system', 'blockMeshDict'), 'w').write(txt)
    ncell = (lev['n_conv'] + lev['n_div']) * lev['n_core'] + n_pl * (lev['n_core'] + lev['n_shear'] + lev['n_outer']) + lev['n_up'] * lev['n_outer']
    return dict(De=De, Re=Re, Rt=Rt, x_in=x_in, x_t=x_t, r_in=r_in, L_down=L_down, R_out=R_out, x_b=x_b, n_pl=n_pl,
                ncell=ncell, Rbody=Rbody, dx0=lev['dx0'])


def write_fields(case, cs, geo, model):
    z = os.path.join(case, '0'); os.makedirs(z, exist_ok=True)
    wall_U = 'noSlip' if model == 'sst' else 'slip'
    U_co = 5.0
    # inlet guess
    files = {}
    files['p'] = header('volScalarField', 'p', '"0"') + f"""dimensions [1 -1 -2 0 0 0 0];
internalField uniform {PA};
boundaryField
{{
    inlet {{ type totalPressure; rho none; psi thermo:psi; p0 uniform {cs['Pc']:.1f}; gamma {cs['gamma_eff']:.6f}; value uniform {cs['Pc']:.1f}; }}
    nozzleWall {{ type zeroGradient; }}
    base {{ type zeroGradient; }}
    body {{ type zeroGradient; }}
    coflow {{ type zeroGradient; }}
    farfield {{ type totalPressure; rho none; psi thermo:psi; p0 uniform {PA}; gamma {cs['gamma_eff']:.6f}; value uniform {PA}; }}
    outlet {{ type waveTransmissive; field p; psi thermo:psi; gamma {cs['gamma_eff']:.6f}; fieldInf {PA}; lInf {0.2*geo['L_down']:.4f}; value uniform {PA}; }}
    axis {{ type empty; }}
    front {{ type wedge; }}
    back {{ type wedge; }}
}}
"""
    files['T'] = header('volScalarField', 'T', '"0"') + f"""dimensions [0 0 0 1 0 0 0];
internalField uniform {TA};
boundaryField
{{
    inlet {{ type totalTemperature; T0 uniform {cs['T0']:.2f}; gamma {cs['gamma_eff']:.6f}; value uniform {cs['T0']:.2f}; }}
    nozzleWall {{ type zeroGradient; }}
    base {{ type zeroGradient; }}
    body {{ type zeroGradient; }}
    coflow {{ type fixedValue; value uniform {TA}; }}
    farfield {{ type inletOutlet; inletValue uniform {TA}; value uniform {TA}; }}
    outlet {{ type inletOutlet; inletValue uniform {TA}; value uniform {TA}; }}
    axis {{ type empty; }}
    front {{ type wedge; }}
    back {{ type wedge; }}
}}
"""
    files['U'] = header('volVectorField', 'U', '"0"') + f"""dimensions [0 1 -1 0 0 0 0];
internalField uniform (0 0 0);
boundaryField
{{
    inlet {{ type pressureInletOutletVelocity; value uniform (0 0 0); }}
    nozzleWall {{ type {wall_U}; }}
    base {{ type {wall_U}; }}
    body {{ type {wall_U}; }}
    coflow {{ type fixedValue; value uniform ({U_co} 0 0); }}
    farfield {{ type pressureInletOutletVelocity; value uniform (0 0 0); }}
    outlet {{ type inletOutlet; inletValue uniform (0 0 0); value uniform (0 0 0); }}
    axis {{ type empty; }}
    front {{ type wedge; }}
    back {{ type wedge; }}
}}
"""
    files['Z'] = header('volScalarField', 'Z', '"0"') + """dimensions [0 0 0 0 0 0 0];
internalField uniform 0;
boundaryField
{
    inlet { type fixedValue; value uniform 1; }
    nozzleWall { type zeroGradient; }
    base { type zeroGradient; }
    body { type zeroGradient; }
    coflow { type fixedValue; value uniform 0; }
    farfield { type inletOutlet; inletValue uniform 0; value uniform 0; }
    outlet { type inletOutlet; inletValue uniform 0; value uniform 0; }
    axis { type empty; }
    front { type wedge; }
    back { type wedge; }
}
"""
    if model == 'sst':
        # inlet turbulence: 5 % intensity of ~ 150 m/s chamber-side velocity, length 0.1*r_in
        Uin = 150.0; I = 0.05; Lt = 0.1 * geo['r_in']
        k_in = 1.5 * (I * Uin) ** 2; om_in = math.sqrt(k_in) / (0.09 ** 0.25 * Lt)
        k_a = 1.5 * (0.01 * U_co) ** 2 + 1e-4; om_a = 100.0
        def turb(name, dims, vin, va, wall):
            return header('volScalarField', name, '"0"') + f"""dimensions {dims};
internalField uniform {va:.6g};
boundaryField
{{
    inlet {{ type fixedValue; value uniform {vin:.6g}; }}
    nozzleWall {{ {wall} }}
    base {{ {wall} }}
    body {{ {wall} }}
    coflow {{ type fixedValue; value uniform {va:.6g}; }}
    farfield {{ type inletOutlet; inletValue uniform {va:.6g}; value uniform {va:.6g}; }}
    outlet {{ type inletOutlet; inletValue uniform {va:.6g}; value uniform {va:.6g}; }}
    axis {{ type empty; }}
    front {{ type wedge; }}
    back {{ type wedge; }}
}}
"""
        files['k'] = turb('k', '[0 2 -2 0 0 0 0]', k_in, k_a, f'type kqRWallFunction; value uniform {k_a:.6g};')
        files['omega'] = turb('omega', '[0 0 -1 0 0 0 0]', om_in, om_a, f'type omegaWallFunction; value uniform {om_a:.6g};')
        files['nut'] = header('volScalarField', 'nut', '"0"') + """dimensions [0 2 -1 0 0 0 0];
internalField uniform 0;
boundaryField
{
    inlet { type calculated; value uniform 0; }
    nozzleWall { type nutkWallFunction; value uniform 0; }
    base { type nutkWallFunction; value uniform 0; }
    body { type nutkWallFunction; value uniform 0; }
    coflow { type calculated; value uniform 0; }
    farfield { type calculated; value uniform 0; }
    outlet { type calculated; value uniform 0; }
    axis { type empty; }
    front { type wedge; }
    back { type wedge; }
}
"""
        files['alphat'] = header('volScalarField', 'alphat', '"0"') + """dimensions [1 -1 -1 0 0 0 0];
internalField uniform 0;
boundaryField
{
    inlet { type calculated; value uniform 0; }
    nozzleWall { type compressible::alphatWallFunction; Prt 0.85; value uniform 0; }
    base { type compressible::alphatWallFunction; Prt 0.85; value uniform 0; }
    body { type compressible::alphatWallFunction; Prt 0.85; value uniform 0; }
    coflow { type calculated; value uniform 0; }
    farfield { type calculated; value uniform 0; }
    outlet { type calculated; value uniform 0; }
    axis { type empty; }
    front { type wedge; }
    back { type wedge; }
}
"""
    for k, v in files.items():
        open(os.path.join(z, k), 'w').write(v)


def write_constant(case, cs, model):
    c = os.path.join(case, 'constant'); os.makedirs(c, exist_ok=True)
    if model == 'sst':
        transport = """    transport
    {
        As          1.458e-06;
        Ts          110.4;
    }"""
        ttype = 'sutherland'
    else:
        transport = """    transport
    {
        mu          0;
        Pr          1;
    }"""
        ttype = 'const'
    open(os.path.join(c, 'thermophysicalProperties'), 'w').write(header('dictionary', 'thermophysicalProperties', '"constant"') + f"""
thermoType
{{
    type            hePsiThermo;
    mixture         pureMixture;
    transport       {ttype};
    thermo          hConst;
    equationOfState perfectGas;
    specie          specie;
    energy          sensibleInternalEnergy;
}}
// Single calorically perfect 'exhaust gas' calibrated to CEA (make_case.py): gamma_eff={cs['gamma_eff']:.5f}, MW_eff={cs['MW_eff']:.4f}
mixture
{{
    specie
    {{
        molWeight   {cs['MW_eff']:.6f};
    }}
    thermodynamics
    {{
        Cp          {cs['cp_eff']:.4f};
        Hf          0;
    }}
{transport}
}}
""")
    if model == 'sst':
        tp = """simulationType RAS;
RAS
{
    RASModel        kOmegaSST;
    turbulence      on;
    printCoeffs     on;
}
"""
    else:
        tp = "simulationType laminar;\n"
    open(os.path.join(c, 'turbulenceProperties'), 'w').write(header('dictionary', 'turbulenceProperties', '"constant"') + tp)


def write_system(case, cs, geo, model, endTime, nproc, writeInterval):
    s = os.path.join(case, 'system'); os.makedirs(s, exist_ok=True)
    De = geo['De']
    # sample lines for post-processing (axis, lines at several x/De)
    fo_z = f"""    Ztransport
    {{
        type            scalarTransport;
        libs            ("libsolverFunctionObjects.so");
        field           Z;
        phi             phi;
        rho             rho;
        bounded01       true;
        {'alphaD 1; alphaDt 1.428571;' if model == 'sst' else 'D 1e-12;'}
        nCorr           0;
        resetOnStartUp  false;
        writeControl    writeTime;
    }}"""
    open(os.path.join(s, 'controlDict'), 'w').write(header('dictionary', 'controlDict', '"system"') + f"""
application     rhoCentralFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         {endTime:.6g};
deltaT          1e-9;
writeControl    adjustableRunTime;
writeInterval   {writeInterval:.6g};
purgeWrite      0;
writeFormat     binary;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable true;
adjustTimeStep  yes;
maxCo           0.25;
maxDeltaT       1;
// functionObjects disabled: every functionObject (scalarTransport, MachNo, even a bare
// fieldMinMax) aborts this OpenFOAM v1912 Debian build at "Starting time loop" with
// "FOAM FATAL IO ERROR: error in IOstream "sha1" for operation operator<<(Ostream&, const word&)".
// Recorded as FAILURE-CFD-01 in 05-plume-cfd/REPORT.md; Mach and mixture fraction are post-processed.
functions
{{
}}
""")
    div_extra = """    div(phi,k)      Gauss vanLeer;
    div(phi,omega)  Gauss vanLeer;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;""" if model == 'sst' else ""
    open(os.path.join(s, 'fvSchemes'), 'w').write(header('dictionary', 'fvSchemes', '"system"') + f"""
fluxScheme      Kurganov;
ddtSchemes      {{ default Euler; }}
gradSchemes     {{ default cellLimited Gauss linear 1; }}
divSchemes
{{
    default         none;
    div(tauMC)      Gauss linear;
    div(phi,Z)      Gauss vanLeer;
{div_extra}
}}
laplacianSchemes {{ default Gauss linear corrected; }}
interpolationSchemes
{{
    default         linear;
    reconstruct(rho) vanLeer;
    reconstruct(U)  vanLeerV;
    reconstruct(T)  vanLeer;
}}
snGradSchemes   {{ default corrected; }}
wallDist        {{ method meshWave; }}
""")
    open(os.path.join(s, 'fvSolution'), 'w').write(header('dictionary', 'fvSolution', '"system"') + """
solvers
{
    "(rho|rhoU|rhoE)" { solver diagonal; }
    U { solver smoothSolver; smoother GaussSeidel; nSweeps 2; tolerance 1e-09; relTol 0.01; }
    e { $U; tolerance 1e-10; relTol 0; }
    "(k|omega)" { solver smoothSolver; smoother GaussSeidel; tolerance 1e-10; relTol 0; }
    Z { solver smoothSolver; smoother GaussSeidel; tolerance 1e-10; relTol 0; }
}
""")
    open(os.path.join(s, 'decomposeParDict'), 'w').write(header('dictionary', 'decomposeParDict', '"system"') + f"""
numberOfSubdomains {nproc};
method          scotch;
""")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('case')
    ap.add_argument('--level', default='medium', choices=list(LEVELS))
    ap.add_argument('--model', default='sst', choices=['inviscid', 'sst'])
    ap.add_argument('--frac', type=float, default=1.0)
    ap.add_argument('--endTime', type=float, default=3e-3)
    ap.add_argument('--write', type=float, default=1e-4)
    ap.add_argument('--wedge', type=float, default=20.0)
    ap.add_argument('--nproc', type=int, default=2)
    a = ap.parse_args()
    J, pts, Rbody = load_interface()
    cs = chamber_state(J, a.frac)
    lev = LEVELS[a.level]
    geo = write_mesh(a.case, pts, None, lev, Rbody, a.wedge)
    write_fields(a.case, cs, geo, a.model)
    write_constant(a.case, cs, a.model)
    write_system(a.case, cs, geo, a.model, a.endTime, a.nproc, a.write)
    meta = dict(level=a.level, model=a.model, frac=a.frac, chamber=cs, geometry=geo, wedge_deg=a.wedge,
                interface_version=J['version'], X_DOWN=X_DOWN, R_OUT=R_OUT, X_UP=X_UP, AR_IN=AR_IN)
    json.dump(meta, open(os.path.join(a.case, 'case_meta.json'), 'w'), indent=1, default=float)
    print(json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in cs.items()}))
    print('cells ~', geo['ncell'], 'De', geo['De'], 'n_plume', geo['n_pl'])


if __name__ == '__main__':
    main()
