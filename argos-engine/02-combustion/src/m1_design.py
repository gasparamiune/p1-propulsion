"""Milestone M1 first-pass design (Combustion, combustion.json v1, 2026-10-11).

One command regenerates: nozzle sizing, gas-path geometry, nozzle contour CSV, pintle flow-area law
and force envelope, a coupled max-thrust blowdown run (equilibrium tank + Dyer injector + lumped
helical-port grain + quasi-steady chamber + CEA nozzle), thermal boundary-condition CSVs (Bartz) at
100 %, 50 % and the 12.5 % stretch floor, and interfaces/combustion.json v1.

Fidelity: FIRST PASS. Lumped (0D) port, equilibrium tank, ASSUMED regression law and efficiencies.
The deep-work models (quasi-1D port, non-equilibrium tank, duty cycles) supersede these numbers in v2.
Usage:  python m1_design.py [--out <dir>] [--publish]
"""
from __future__ import annotations
import argparse, csv, json, math, os, sys, datetime
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cea_cards
from perf_tables import Perf, PA_SL, G0
import n2o
from tank import EquilibriumTank
import heat

ENGINE_ROOT = os.environ.get('ENGINE_ROOT', '/mnt/project-files/engine')

# ----------------------------------------------------------------------------------------------
# Inputs (every value tagged)
# ----------------------------------------------------------------------------------------------
INP = dict(
    F_max=(500.0, 'REQ founder: max thrust sea level [N]'),
    Pc_max=(25e5, 'REQ/LEAD v0 baseline chamber pressure at max thrust [Pa]'),
    OF_design=(7.0, 'DERIVED: lean of c* peak (5.5) so throttling sweeps through the optimum (floor_trade)'),
    eps=(2.0, 'DERIVED: floor separation trade (Schmucker) for 8:1 stretch, see eps_floor_trade'),
    eta_cstar=(0.92, 'ASSUMED (band 0.85-0.96; Nytrox/ABS 0.961 measured, USU thesis; HTPB/N2O lab motors 0.85-0.95)'),
    eta_cfv=(0.975, 'ASSUMED: 15 deg cone divergence lambda=0.983 x 0.992 other losses'),
    fuel_card=('ABS_TYP_v1', 'DERIVED card (cea_cards.py): C6.06H6.43N0.24, hf=+39.4 kJ/mol'),
    rho_fuel=(1000.0, 'ASSUMED printed ABS density [kg/m3] (filament 1.04; FDM parts 0.975-1.01: Walker 2015, McFarland & Antunes 2019); weigh grains'),
    reg_a=(0.0577e-3, 'ASSUMED N2O/ABS regression coefficient [m/s per (kg/m2/s)^n]; anchored to ~1 mm/s at 300 kg/m2/s for HTPB/N2O (Boughaba & Hendrick, EUCASS 2013, citing lit.); NO verified N2O/ABS law found -> band x0.6..x1.5'),
    reg_n=(0.5, 'ASSUMED flux exponent (band 0.35-0.68; GOX polymer laws n=0.50-0.68, Zilliac & Karabeyoglu AIAA 2006-4504 Table 2)'),
    helix_factor=(1.5, 'ASSUMED helical-port regression amplification for N2O (GOX/ABS up to 3.0x: Walker, USU MS thesis 2015; N2O UNVERIFIED) band 1.0-2.5'),
    L_grain=(0.200, 'DERIVED: shortest grain giving O/F~7.6 at max thrust with nominal law [m]'),
    D_port0=(0.025, 'DERIVED: initial port diameter [m] (G_ox0 ~ 450 kg/m2/s at max)'),
    D_grain=(0.0535, 'DERIVED: grain OD [m] = liner ID 53.95 mm - 0.45 mm diametral clearance'),
    helix_offset=(0.004, 'DERIVED: helical port centreline radius [m] (Rh = 2*offset/D_port0 = 0.32)'),
    helix_pitch=(0.050, 'DERIVED: helix pitch [m]'),
    case_OD=(0.0635, 'LEAD v0 placeholder 6061-T6 2.5 in tube [m] (Mechanical owns)'),
    case_wall=(0.003175, 'LEAD v0 placeholder [m]'),
    liner_t=(0.0016, 'DERIVED: phenolic liner wall [m] (Mechanical owns final)'),
    L_pre=(0.030, 'DERIVED: pre-chamber length [m] (spray flash-vaporisation + flame holding)'),
    L_post=(0.040, 'DERIVED: post-chamber length [m] (L/D 0.75, mixing for eta_c*)'),
    conv_half_angle=(45.0, 'DERIVED: convergent half-angle [deg] (compact)'),
    div_half_angle=(15.0, 'DERIVED: conical divergent half-angle [deg]'),
    Rtu_over_Rt=(1.5, 'LITERATURE: throat upstream radius of curvature (Rao/Huzel & Huang practice)'),
    Rtd_over_Rt=(0.382, 'LITERATURE: throat downstream radius of curvature (Rao 1958 practice)'),
    R_fillet_conv=(0.008, 'DERIVED: chamber-to-convergent fillet [m]'),
    # pintle
    pintle_seat_D=(0.0055, 'DERIVED: pintle seat (orifice) diameter [m]'),
    pintle_cone_half=(15.0, 'DERIVED: metering cone half-angle [deg]'),
    pintle_stroke=(0.0040, 'DERIVED: mechanical stroke [m] (usable 0.30-4.0 mm)'),
    pintle_stem_D=(0.004, 'DERIVED: stem diameter through the forward seal [m]'),
    pintle_Cd=(0.70, 'ASSUMED annular sharp-edged Cd (range 0.6-0.8); measure in water + N2O cold flow'),
    dp_line_ref=(2.5e5, 'ASSUMED tank->pintle line loss at 0.25 kg/s [Pa] (isolation valve + flex hose + fittings), scales with mdot^2'),
    dp_over_pc_min=(0.25, 'DERIVED stability rule: injector dP/Pc >= 0.25 sets the thrust ceiling (chug, see stability section)'),
    # tank (Mechanical/GNC own; placeholders)
    tank_V=(2.5e-3, 'LEAD v0 placeholder [m3]'),
    tank_m=(1.6, 'LEAD v0 placeholder N2O load [kg]'),
    tank_T0=(293.15, 'REQ ENG-12 conditioning 20 +/- 3 C [K]'),
)
V = {k: v[0] for k, v in INP.items()}


def tagged(v, tag, **kw):
    d = {'v': v, 'tag': tag}
    d.update(kw)
    return d


# ----------------------------------------------------------------------------------------------
def load_perf(out_data):
    fn = os.path.join(out_data, f"perf_table_{V['fuel_card']}_shifting_v1.json")
    if not os.path.exists(fn):
        from perf_tables import build
        build(V['fuel_card'], out_dir=out_data)
    return Perf(fn)


def thrust_from_pc(P, Pc, OF, eps, At, eta_cfv=None):
    eta_cfv = V['eta_cfv'] if eta_cfv is None else eta_cfv
    cf, es, pepa = P.cf_amb(Pc, OF, eps)
    e_eff = es if es else eps
    F = (eta_cfv * P.cf_vac(Pc, OF, e_eff) - e_eff * PA_SL / Pc) * Pc * At
    return F, es, pepa


def size_nozzle(P):
    At = 1.4e-4
    for _ in range(40):
        F, _, _ = thrust_from_pc(P, V['Pc_max'], V['OF_design'], V['eps'], At)
        At *= V['F_max'] / F
    cs = P.cstar(V['Pc_max'], V['OF_design']) * V['eta_cstar']
    mdot = V['Pc_max'] * At / cs
    return dict(At=At, Dt=math.sqrt(4 * At / math.pi), De=math.sqrt(4 * At * V['eps'] / math.pi), mdot=mdot,
                mox=mdot * V['OF_design'] / (1 + V['OF_design']), mf=mdot / (1 + V['OF_design']),
                cstar_del=cs, Isp=V['F_max'] / (mdot * G0), pe_pa=P.pe_pc(V['Pc_max'], V['OF_design'], V['eps']) * V['Pc_max'] / PA_SL)


# ----------------------------------------------------------------------------------------------
def pintle_area(h, Ds=None, alpha_deg=None):
    """Geometric minimum annular area between a sharp-edged seat (diameter Ds) and a conical
    needle (half-angle alpha) lifted by h from the seated position: frustum of slant s = h sin(a),
    A = pi s (Ds - s cos a), valid while it is below the open-seat area pi Ds^2/4; beyond that point
    the seat itself limits the flow (A = pi Ds^2/4). Monotonic in h."""
    Ds = V['pintle_seat_D'] if Ds is None else Ds
    a = math.radians(V['pintle_cone_half'] if alpha_deg is None else alpha_deg)
    h = np.asarray(h, dtype=float)
    s = np.clip(h, 0, None) * math.sin(a)
    A_seat = math.pi * Ds ** 2 / 4
    # frustum area reaches A_seat at s* (smaller root of pi s (Ds - s cos a) = A_seat)
    disc = Ds ** 2 - 4 * math.cos(a) * A_seat / math.pi
    s_star = (Ds - math.sqrt(max(disc, 0.0))) / (2 * math.cos(a))
    A = np.where(s < s_star, math.pi * s * (Ds - s * math.cos(a)), A_seat)
    return float(A) if A.ndim == 0 else A


def pintle_lift_for_area(A):
    from scipy.optimize import brentq
    if A <= 0:
        return 0.0
    A_seat = math.pi * V['pintle_seat_D'] ** 2 / 4
    if A >= A_seat * 0.9999:
        return float('nan')   # beyond seat-limited area: not reachable
    return brentq(lambda h: pintle_area(h) - A, 0.0, 0.05)


def pintle_forces(P1, P2):
    """Axial pressure force on the needle (+ = toward chamber = closing) for seated and fully open
    states, reference geometry (seat Ds, stem ds through forward seal to ambient)."""
    As = math.pi * V['pintle_stem_D'] ** 2 / 4
    Aseat = math.pi * V['pintle_seat_D'] ** 2 / 4
    F_closed = (P1 - P2) * Aseat - (P1 - PA_SL) * As
    F_open_worst = -(P1 - PA_SL) * As      # tip region recovers to ~P1 when wide open
    return F_closed, F_open_worst


# ----------------------------------------------------------------------------------------------
def nozzle_contour(Dt, eps, x_conv_start, Rc):
    """Gas-path contour from injector face to nozzle exit, points (x from injector face, r).
    Returns list of dict rows and key stations."""
    Rt = Dt / 2; Re = Rt * math.sqrt(eps)
    th_c = math.radians(V['conv_half_angle']); th_d = math.radians(V['div_half_angle'])
    R1 = V['R_fillet_conv']; Rtu = V['Rtu_over_Rt'] * Rt; Rtd = V['Rtd_over_Rt'] * Rt
    rows = []
    # throat-relative construction, then shift
    # upstream throat arc: centre at (0, Rt+Rtu); from angle -th_c to 0
    r_arc_u_start = Rt + Rtu * (1 - math.cos(th_c)); x_arc_u_start = -Rtu * math.sin(th_c)
    # fillet: centre at (xf, Rc - R1); ends at angle th_c down
    r_fillet_end = Rc - R1 * (1 - math.cos(th_c))
    dx_line = (r_fillet_end - r_arc_u_start) / math.tan(th_c)
    x_fillet_end = x_arc_u_start - dx_line
    x_fillet_start = x_fillet_end - R1 * math.sin(th_c)
    shift = x_conv_start - x_fillet_start     # x_from_face = x_throat_rel + shift
    pts = []
    for th in np.linspace(0, th_c, 12):
        pts.append((x_fillet_start + R1 * math.sin(th), Rc - R1 * (1 - math.cos(th)), 'conv_fillet'))
    for s in np.linspace(0, 1, 8)[1:]:
        pts.append((x_fillet_end + s * dx_line, r_fillet_end - s * (r_fillet_end - r_arc_u_start), 'conv_cone'))
    for th in np.linspace(th_c, 0, 16)[1:]:
        pts.append((-Rtu * math.sin(th), Rt + Rtu * (1 - math.cos(th)), 'throat_up'))
    for th in np.linspace(0, th_d, 8)[1:]:
        pts.append((Rtd * math.sin(th), Rt + Rtd * (1 - math.cos(th)), 'throat_down'))
    x_d0 = Rtd * math.sin(th_d); r_d0 = Rt + Rtd * (1 - math.cos(th_d))
    Ld = (Re - r_d0) / math.tan(th_d)
    for s in np.linspace(0, 1, 12)[1:]:
        pts.append((x_d0 + s * Ld, r_d0 + s * (Re - r_d0), 'div_cone'))
    for (x, r, reg) in pts:
        rows.append(dict(x_face=x + shift, x_throat=x, r=r, region=reg))
    st = dict(x_throat_face=shift, x_exit_face=x_d0 + Ld + shift, L_div=x_d0 + Ld, L_conv=-x_fillet_start,
              Re=Re, Rt=Rt)
    return rows, st


# ----------------------------------------------------------------------------------------------
class Engine0D:
    """Lumped engine for M1: equilibrium tank, line loss, Dyer pintle, helical single port."""
    def __init__(self, P, noz, tank=None):
        self.P = P; self.noz = noz
        self.At = noz['At']
        self.tank = tank or EquilibriumTank(V['tank_V'], V['tank_m'], V['tank_T0'])
        self.Dp = V['D_port0']
        self.CdA_max = V['pintle_Cd'] * pintle_area(V['pintle_stroke'] * 0.999)

    def mdot_fuel(self, mox, Dp):
        Ap = math.pi * Dp ** 2 / 4
        G = mox / Ap
        r = V['helix_factor'] * V['reg_a'] * G ** V['reg_n']
        return V['rho_fuel'] * r * math.pi * Dp * V['L_grain'], r, G

    def dp_line(self, mox):
        return V['dp_line_ref'] * (mox / 0.25) ** 2

    def chamber_for_mox(self, mox):
        mf, r, G = self.mdot_fuel(mox, self.Dp)
        OF = mox / mf
        Pc = 15e5
        for _ in range(40):
            Pc_new = (mox + mf) * self.P.cstar(Pc, OF) * V['eta_cstar'] / self.At
            if abs(Pc_new - Pc) < 1.0:
                break
            Pc = Pc_new
        return Pc_new, mf, OF, r, G

    def mox_for_pc(self, Pc_target):
        from scipy.optimize import brentq
        return brentq(lambda m: self.chamber_for_mox(m)[0] - Pc_target, 1e-4, 1.0)

    def operate(self, Pc_cmd):
        """Quasi-steady operating point for a Pc command, saturating on pintle area and on the
        dP/Pc stability ceiling. Returns dict."""
        tk = self.tank
        mox = self.mox_for_pc(Pc_cmd)
        P1 = tk.P - self.dp_line(mox)
        Pc_ceiling = P1 / (1 + V['dp_over_pc_min'])
        limit = None
        if Pc_cmd > Pc_ceiling:
            Pc_cmd = Pc_ceiling; limit = 'dP/Pc ceiling'
            mox = self.mox_for_pc(Pc_cmd)
            P1 = tk.P - self.dp_line(mox)
        G = n2o.G_dyer(P1, tk.T, Pc_cmd)
        CdA = mox / G
        if CdA > self.CdA_max:
            # pintle saturated: find Pc where CdA_max*G(P1,Pc) = mox(Pc)
            from scipy.optimize import brentq
            def res(Pc):
                m = self.mox_for_pc(Pc)
                return self.CdA_max * n2o.G_dyer(tk.P - self.dp_line(m), tk.T, Pc) - m
            Pc_cmd = brentq(res, 2e5, Pc_cmd)
            mox = self.mox_for_pc(Pc_cmd); P1 = tk.P - self.dp_line(mox)
            CdA = self.CdA_max; limit = 'pintle full open'
        Pc, mf, OF, r, G = self.chamber_for_mox(mox)
        F, es, pepa = thrust_from_pc(self.P, Pc, OF, V['eps'], self.At)
        h = pintle_lift_for_area(CdA / V['pintle_Cd'])
        return dict(Pc=Pc, mox=mox, mf=mf, OF=OF, r=r, G=G, F=F, Isp=F / ((mox + mf) * G0), P1=P1,
                    CdA=CdA, h=h, sep=es, pe_pa=pepa, limit=limit, dP_over_Pc=(P1 - Pc) / Pc)

    def step(self, op, dt):
        self.Dp += 2 * op['r'] * dt
        self.tank.step(op['mox'], dt)


def run_max_thrust(P, noz, dt=0.05, t_end=12.0):
    eng = Engine0D(P, noz)
    rows = []
    t = 0.0
    while t <= t_end and eng.tank.liquid:
        op = eng.operate(V['Pc_max'])
        rows.append(dict(t=t, P_tank=eng.tank.P, T_tank=eng.tank.T, m_tank=eng.tank.m, m_liq=eng.tank.m_l, **op,
                         D_port=eng.Dp))
        eng.step(op, dt)
        t += dt
    return rows, eng


# ----------------------------------------------------------------------------------------------
def thermal_bc(P, noz, contour_rows, st, Pc, OF, label, out_dir, x_grain0, x_grain1):
    """Bartz h_g(x), T_aw(x), p(x) along the full gas path for one operating point."""
    from rocketcea.cea_obj_w_units import CEA_Obj
    cea_cards.register_all()
    c = CEA_Obj(oxName='N2O', fuelName=V['fuel_card'], pressure_units='Pa', cstar_units='m/s',
                temperature_units='K', isp_units='sec', specific_heat_units='J/kg-K',
                viscosity_units='poise', thermal_cond_units='W/cm-degC')
    cp_e, mu_e, k_e, Pr_e = c.get_Chamber_Transport(Pc=Pc, MR=OF, eps=V['eps'], frozen=0)
    cp_f, mu_f, k_f, Pr_f = c.get_Chamber_Transport(Pc=Pc, MR=OF, eps=V['eps'], frozen=1)
    mu_e *= 0.1; mu_f *= 0.1   # poise -> Pa s
    T0 = P.Tc(Pc, OF) * V['eta_cstar'] ** 2       # delivered stagnation temperature estimate
    cstar = P.cstar(Pc, OF) * V['eta_cstar']
    gam = c.get_Throat_MolWt_gamma(Pc=Pc, MR=OF, eps=V['eps'])[1]
    Dt = noz['Dt']; Rt = Dt / 2; Rc_thr = 0.5 * (V['Rtu_over_Rt'] + V['Rtd_over_Rt']) * Rt
    At = noz['At']
    out = []
    # chamber stations (pre-chamber, grain-port exit plane region, post-chamber walls)
    R_ch = V['D_grain'] / 2 + 0.0002
    def station(x, r, region, supersonic, unc):
        A = math.pi * r * r
        Ar = A / At
        M = heat.mach_from_area(Ar, gam, supersonic)
        f = 1 + (gam - 1) / 2 * M * M
        p = Pc * f ** (-gam / (gam - 1))
        Tst = T0 / f
        hg600 = heat.bartz_h(Pc, cstar, Dt, Rc_thr, mu_f, cp_f, Pr_f, T0, gam, Ar, M, 600.0)
        hg1500 = heat.bartz_h(Pc, cstar, Dt, Rc_thr, mu_f, cp_f, Pr_f, T0, gam, Ar, M, 1500.0)
        hg_eq = heat.bartz_h(Pc, cstar, Dt, Rc_thr, mu_e, cp_e, Pr_e, T0, gam, Ar, M, 600.0)
        Taw = heat.t_aw(T0, gam, M, Pr_f)
        qrad_lo = heat.radiation_flux(Tst, 600.0, 0.05); qrad_hi = heat.radiation_flux(Tst, 600.0, 0.20)
        out.append(dict(x_face_m=round(x, 6), x_throat_m=round(x - st['x_throat_face'], 6), r_m=round(r, 6), region=region,
                        A_over_At=round(Ar, 4), Mach=round(M, 4), p_Pa=round(p, 1), T_static_K=round(Tst, 1),
                        T_aw_K=round(Taw, 1), h_g_Tw600_W_m2K=round(hg600, 1), h_g_Tw1500_W_m2K=round(hg1500, 1),
                        h_g_eqprops_Tw600_W_m2K=round(hg_eq, 1),
                        q_conv_Tw600_W_m2=round(hg600 * (Taw - 600.0), 0),
                        q_rad_band_W_m2=f"{qrad_lo:.0f}-{qrad_hi:.0f}", uncertainty_factor=unc))
    for x in np.linspace(0.0, x_grain0, 4):
        station(x, R_ch, 'pre-chamber wall (injector face at x=0)', False, '0.5-2 (Bartz outside validity; recirculating flow)')
    out.append(dict(x_face_m=round(x_grain0, 6), region='GRAIN PORT: case/liner shielded by fuel web until burnout; '
                    'gas-side BC is the burning fuel surface (T_surf ~ 700-900 K, ASSUMED); after burnout use post-chamber row'))
    out.append(dict(x_face_m=round(x_grain1, 6), region='end of grain'))
    for x in np.linspace(x_grain1, contour_rows[0]['x_face'], 4):
        station(x, R_ch, 'post-chamber wall', False, '0.5-2 (jet from port, recirculation)')
    for row in contour_rows:
        sup = row['x_throat'] > 0
        station(row['x_face'], row['r'], row['region'], sup, '0.7-1.3 (Bartz, nozzle)')
    fn = os.path.join(out_dir, f'thermal_bc_{label}_v1.csv')
    keys = ['x_face_m', 'x_throat_m', 'r_m', 'region', 'A_over_At', 'Mach', 'p_Pa', 'T_static_K', 'T_aw_K',
            'h_g_Tw600_W_m2K', 'h_g_Tw1500_W_m2K', 'h_g_eqprops_Tw600_W_m2K', 'q_conv_Tw600_W_m2', 'q_rad_band_W_m2',
            'uncertainty_factor']
    with open(fn, 'w', newline='') as f:
        f.write(f'# Thermal BC v1 {label}: Pc={Pc:.0f} Pa, O/F={OF:.2f}, T0(delivered)={T0:.0f} K, gamma_t={gam:.4f}, '
                f'frozen props mu={mu_f:.3e} Pa s cp={cp_f:.0f} J/kgK Pr={Pr_f:.3f}; equilibrium cp={cp_e:.0f} Pr={Pr_e:.3f}. '
                f'Bartz 1957 (see heat.py). SIM m1_design.py. x_face: axial distance from injector face toward nozzle exit [m].\n')
        w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
        w.writeheader()
        for r in out:
            w.writerow(r)
    peak = max((r for r in out if 'h_g_Tw600_W_m2K' in r), key=lambda r: r['q_conv_Tw600_W_m2'])
    return fn, peak, dict(T0=T0, cp_f=cp_f, mu_f=mu_f, Pr_f=Pr_f, cp_e=cp_e, Pr_e=Pr_e, gamma_t=gam)


# ----------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, '..'))
    ap.add_argument('--publish', action='store_true')
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    d_data = os.path.join(out, 'data'); os.makedirs(d_data, exist_ok=True)
    P = load_perf(d_data)
    noz = size_nozzle(P)
    print('nozzle', {k: (round(v, 6) if isinstance(v, float) else v) for k, v in noz.items()})

    # ---- geometry
    liner_ID = V['case_OD'] - 2 * V['case_wall'] - 2 * V['liner_t']
    x_grain0 = V['L_pre']; x_grain1 = V['L_pre'] + V['L_grain']; x_conv0 = x_grain1 + V['L_post']
    Rc = V['D_grain'] / 2 + 0.0002
    contour, st = nozzle_contour(noz['Dt'], V['eps'], x_conv0, Rc)
    fn_cont = os.path.join(d_data, 'nozzle_contour_v1.csv')
    with open(fn_cont, 'w', newline='') as f:
        f.write('# Gas-path contour v1 (Combustion, 2026-10-11). x_face_m from injector face toward exit; x_throat_m from throat '
                '(+ downstream); r_m radius. Upstream of the first row the wall is the post-chamber cylinder r=%.5f m. '
                'CAD: +Z forward => z = (x_exit - x_face).\n' % Rc)
        w = csv.DictWriter(f, fieldnames=['x_face_m', 'x_throat_m', 'r_m', 'region'])
        w.writeheader()
        for r in contour:
            w.writerow(dict(x_face_m=round(r['x_face'], 7), x_throat_m=round(r['x_throat'], 7), r_m=round(r['r'], 7), region=r['region']))

    # ---- pintle law
    hs = np.linspace(0, V['pintle_stroke'], 41)
    fn_pin = os.path.join(d_data, 'pintle_area_vs_lift_v1.csv')
    with open(fn_pin, 'w', newline='') as f:
        f.write('# Pintle (needle in sharp-edged seat) geometric flow area vs lift, v1. Seat D=%.4f m, cone half-angle %.1f deg. '
                'CdA = Cd*A with Cd ASSUMED %.2f. DERIVED m1_design.py\n' % (V['pintle_seat_D'], V['pintle_cone_half'], V['pintle_Cd']))
        f.write('lift_m,area_m2,CdA_m2,area_fraction_of_max\n')
        Amax = pintle_area(V['pintle_stroke'])
        for h in hs:
            A = pintle_area(h)
            f.write(f'{h:.6f},{A:.4e},{A*V["pintle_Cd"]:.4e},{A/Amax:.4f}\n')

    # ---- operating map at nominal tank (20 C) and cold tank (5 C) for thrust fractions
    fracs = [1.0, 0.75, 0.5, 0.25, 0.2, 0.125]
    opmap = []
    for Tt in [293.15, 278.15]:
        eng = Engine0D(P, noz, tank=EquilibriumTank(V['tank_V'], V['tank_m'], Tt))
        for fr in fracs:
            # find Pc giving F = fr*F_max at initial port
            from scipy.optimize import brentq
            def resF(Pc):
                mox = eng.mox_for_pc(Pc); Pc2, mf, OF, r, G = eng.chamber_for_mox(mox)
                return thrust_from_pc(P, Pc2, OF, V['eps'], eng.At)[0] - fr * V['F_max']
            try:
                Pcf = brentq(resF, 1.6e5, 30e5)
                op = eng.operate(Pcf)
            except Exception as e:
                op = dict(error=str(e)); Pcf = float('nan')
            op.update(frac=fr, T_tank=Tt, P_tank=eng.tank.P)
            opmap.append(op)
    fn_map = os.path.join(d_data, 'throttle_map_initial_port_v1.csv')
    keys = ['T_tank', 'P_tank', 'frac', 'F', 'Pc', 'mox', 'mf', 'OF', 'Isp', 'G', 'P1', 'dP_over_Pc', 'CdA', 'h', 'pe_pa', 'sep', 'limit']
    with open(fn_map, 'w', newline='') as f:
        f.write('# Throttle map v1 at initial port (lumped model). SIM m1_design.py. sep = separation area ratio (Schmucker) or blank.\n')
        w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore'); w.writeheader()
        for r in opmap:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
    for r in opmap:
        if 'F' in r:
            print(f"T={r['T_tank']-273.15:4.0f}C {r['frac']*100:5.1f}%  F={r['F']:6.1f} Pc={r['Pc']/1e5:5.2f} mox={r['mox']:.4f} OF={r['OF']:4.2f} "
                  f"Isp={r['Isp']:5.1f} G={r['G']:5.0f} dP/Pc={r['dP_over_Pc']:5.2f} h={r['h']*1e3:5.3f}mm sep={r['sep']} lim={r['limit']}")

    # ---- max-thrust blowdown
    rows, eng = run_max_thrust(P, noz)
    fn_mt = os.path.join(d_data, 'max_thrust_case_v1.csv')
    keys = ['t', 'P_tank', 'T_tank', 'm_tank', 'm_liq', 'P1', 'Pc', 'F', 'mox', 'mf', 'OF', 'Isp', 'G', 'D_port', 'CdA', 'h', 'dP_over_Pc', 'pe_pa', 'limit']
    with open(fn_mt, 'w', newline='') as f:
        f.write('# Max-thrust case v1: Pc command 25 bar held until the dP/Pc>=0.25 ceiling or pintle saturation; equilibrium adiabatic tank '
                '1.6 kg / 2.5 L / 20 C; lumped helical port. Ends at liquid depletion. SIM m1_design.py (FIRST PASS).\n')
        w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore'); w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
    t_burn = rows[-1]['t']
    imp = sum(r['F'] for r in rows) * 0.05
    m_fuel_burn = sum(r['mf'] for r in rows) * 0.05
    print(f"max-thrust run: t_liq={t_burn:.2f}s impulse={imp:.0f} Ns fuel burnt={m_fuel_burn:.3f} kg D_port end={rows[-1]['D_port']*1e3:.1f} mm")
    for r in rows[::10]:
        print(f" t={r['t']:4.1f} Ptank={r['P_tank']/1e5:5.1f} Pc={r['Pc']/1e5:5.2f} F={r['F']:6.1f} OF={r['OF']:4.2f} mox={r['mox']:.4f} G={r['G']:5.0f} h={r['h']*1e3:.2f} dP/Pc={r['dP_over_Pc']:.2f} {r['limit']}")

    # ---- thermal BCs
    pts = {}
    for lab, fr in [('max', 1.0), ('50pct', 0.5), ('floor12p5', 0.125)]:
        r = [o for o in opmap if o['T_tank'] == 293.15 and o['frac'] == fr][0]
        fn, peak, props = thermal_bc(P, noz, contour, st, r['Pc'], r['OF'], lab, d_data, x_grain0, x_grain1)
        pts[lab] = dict(file=fn, peak=peak, props=props, Pc=r['Pc'], OF=r['OF'])
        print(lab, 'peak h', peak['h_g_Tw600_W_m2K'], 'q', peak['q_conv_Tw600_W_m2'], 'at x_throat', peak['x_throat_m'], 'Taw', peak['T_aw_K'])

    # ---- grain mass, chamber volume, L*
    grain_vol = math.pi / 4 * (V['D_grain'] ** 2 - V['D_port0'] ** 2) * V['L_grain']
    grain_mass = grain_vol * V['rho_fuel']
    Vc = math.pi / 4 * Rc ** 2 * 4 * (V['L_pre'] + V['L_post']) + math.pi / 4 * V['D_port0'] ** 2 * V['L_grain']
    Lstar = Vc / noz['At']
    gam_c = P.gamma(V['Pc_max'], V['OF_design'])
    Gam = math.sqrt(gam_c) * (2 / (gam_c + 1)) ** ((gam_c + 1) / (2 * (gam_c - 1)))
    tau_fill = Lstar / (noz['cstar_del'] * Gam ** 2)

    # pintle force envelope
    Fc_meop, Fo_meop = pintle_forces(7.0e6, PA_SL)
    Fc_nom, Fo_nom = pintle_forces(50.5e5, PA_SL)

    res = dict(noz=noz, contour=fn_cont, stations=st, opmap=opmap, maxrun=rows, thermal=pts, grain_mass=grain_mass,
               Vc=Vc, Lstar=Lstar, tau_fill=tau_fill, liner_ID=liner_ID, x_grain0=x_grain0, x_grain1=x_grain1,
               x_conv0=x_conv0, Rc=Rc, F_pintle=dict(closed_MEOP=Fc_meop, open_MEOP=Fo_meop, closed_20C=Fc_nom, open_20C=Fo_nom),
               t_burn=t_burn, impulse=imp, m_fuel_burn=m_fuel_burn, fn_map=fn_map, fn_mt=fn_mt, fn_pin=fn_pin)
    json.dump(res, open(os.path.join(d_data, 'm1_design_results_v1.json'), 'w'), indent=1, default=float)
    print(f"grain mass {grain_mass:.3f} kg, Vc {Vc*1e6:.0f} cm3, L* {Lstar:.2f} m, tau_fill {tau_fill*1e3:.2f} ms")
    print('pintle forces [N] closed@MEOP', round(Fc_meop, 1), 'open@MEOP', round(Fo_meop, 1), 'closed@20C', round(Fc_nom, 1), 'open@20C', round(Fo_nom, 1))
    print('stations', st)
    return res


if __name__ == '__main__':
    main()
