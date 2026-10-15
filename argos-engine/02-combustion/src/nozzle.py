"""Nozzle and throat analyses (Combustion v2, brief task 5).

1. Separation (Summerfield p_w/p_a <= 0.4; Schmucker p_sep/p_a = (1.88 M - 1)^-0.64) across the throttle range for the
   nominal and eroded throat; separated length/area and a side-load upper bound.
2. Throat thermal response + chemical erosion of the graphite insert (1-D radial transient conduction at the throat
   station, Bartz gas-side h_g(T_w), gas radiation band, surface-reaction enthalpy) driven by Pc(t), O/F(t) histories.
   Surface kinetics (semi-global, k = A T^b exp(-E/RT), rate = k p_i,w^n, kg/m2/s with p in atm), as tabulated by
   M. Rotondi, M.T. Migliorino, D. Bianchi, L. Kamps, H. Nagata, 'Computational Analysis and Regression Laws for Nozzle
   Erosion Prediction in Hybrid Rockets', JPP 40(3) 2024, 439-459 (from Bradley et al. and Chelliah et al.):
     C + H2O -> CO + H2 : A 4.8e5,  E 288 kJ/mol, b 0,    n 0.5
     C + CO2 -> 2 CO    : A 9.0e3,  E 285 kJ/mol, b 0,    n 0.5
     C + OH  -> CO + H  : A 3.61e2, E 0,          b -0.5, n 1
     C + O   -> CO      : A 6.655e2,E 0,          b -0.5, n 1
     C + 1/2 O2 -> CO   : Nagle-Strickland-Constable, k5 2.4e3 (125.6 kJ/mol), k6 2.13e1 (-17.17), k7 5.35e-1 (63.64),
                          k8 1.81e7 (406.1); Y = 1/(1 + k8/(k7 p)); rate = k5 p Y/(1 + k6 p) + k7 p (1 - Y)
   (H2O/CO2 entries agree with Thakre & Yang, JPP 24(4) 2008, Table 1.)  Wall partial pressures from a per-species
   film mass-transfer balance with rho_e u_e C_m = h_g/cp (Chilton-Colburn, Le = 1); blowing correction neglected
   (B' < 0.05).  Edge composition: CEA shifting equilibrium at the throat for (Pc, O/F).
   Validation anchor (measured, N2O/HDPE, graphite 1850 kg/m3, 25-50 bar, Rotondi et al. 2024): 0.018-0.048 mm/s
   (O/F 4.8-6, fuel-rich) and 0.098-0.139 mm/s (O/F 7.4-10.7, near stoichiometric) full-duration averages; onset after
   1.5-4 s of wall heating.
3. Soak-back: insert -> metal sleeve contact conductance, lumped sleeve, after shutdown.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cea_cards
import heat
from perf_tables import Perf, PA_SL, G0

RU = 8.314462618
SIG = 5.670374419e-8
ATM = 101325.0
SPECIES = ['H2O', 'CO2', 'OH', 'O', 'O2', 'CO', 'H2', 'N2', 'H', 'NO']
MW = dict(H2O=18.015, CO2=44.01, OH=17.007, O=15.999, O2=31.998, CO=28.01, H2=2.016, N2=28.013, H=1.008, NO=30.006)
# reaction enthalpy per kg carbon consumed (298 K standard formation enthalpies, kJ/mol: H2O(g) -241.8, CO2 -393.5,
# CO -110.5, OH +39.0, O +249.2, H +218.0) -> + = endothermic (absorbs heat from the wall)
DH_PER_MOLC = {'H2O': (-110.5) - (-241.8), 'CO2': 2 * (-110.5) - (-393.5), 'OH': (-110.5 + 218.0) - 39.0,
               'O': -110.5 - 249.2, 'O2': -110.5}
KIN = {'H2O': (4.8e5, 288e3, 0.0, 0.5), 'CO2': (9.0e3, 285e3, 0.0, 0.5), 'OH': (3.61e2, 0.0, -0.5, 1.0),
       'O': (6.655e2, 0.0, -0.5, 1.0)}
NSC = dict(k5=(2.4e3, 125.6e3), k6=(2.13e1, -17.17e3), k7=(5.35e-1, 63.64e3), k8=(1.81e7, 406.1e3))
NU_SP = {'H2O': 1.0, 'CO2': 1.0, 'OH': 1.0, 'O': 1.0, 'O2': 0.5}   # mol species per mol C


def rate_species(sp, Tw, p_atm):
    """Kinetic carbon removal rate [kg C/m2/s] by species sp at wall temperature Tw and partial pressure p [atm]."""
    if p_atm <= 0:
        return 0.0
    if sp == 'O2':
        k = {n: A * math.exp(-E / (RU * Tw)) for n, (A, E) in NSC.items()}
        Y = 1.0 / (1.0 + k['k8'] / (k['k7'] * p_atm))
        return k['k5'] * p_atm * Y / (1 + k['k6'] * p_atm) + k['k7'] * p_atm * (1 - Y)
    A, E, b, n = KIN[sp]
    return A * Tw ** b * math.exp(-E / (RU * Tw)) * p_atm ** n


def erosion_rate(Tw, p_w, X_e, MW_e, rho_u_Cm, mode='coupled'):
    """Total carbon mass flux [kg/m2/s] and per-species split, with film diffusion (mode 'coupled'), pure kinetics
    ('kinetic', wall = edge composition) or pure diffusion limit ('diffusion', wall concentration -> 0)."""
    out = {}; tot = 0.0; qchem = 0.0
    for sp in ('H2O', 'CO2', 'OH', 'O', 'O2'):
        Xe = X_e.get(sp, 0.0)
        if Xe <= 0:
            continue
        Ye = Xe * MW[sp] / MW_e
        conv = 12.011 / (MW[sp] * NU_SP[sp])          # kg C per kg species consumed
        m_diff_max = rho_u_Cm * Ye * conv
        if mode == 'diffusion':
            m = m_diff_max
        elif mode == 'kinetic':
            m = rate_species(sp, Tw, Xe * p_w / ATM)
        else:
            lo, hi = 0.0, Ye
            for _ in range(50):          # find Y_w: rho_u_Cm (Ye - Yw) conv = rate(Yw)
                Yw = 0.5 * (lo + hi)
                Xw = Yw * MW_e / MW[sp]
                f = rho_u_Cm * (Ye - Yw) * conv - rate_species(sp, Tw, Xw * p_w / ATM)
                if f > 0:
                    lo = Yw
                else:
                    hi = Yw
            m = rho_u_Cm * (Ye - Yw) * conv
        out[sp] = m; tot += m; qchem += m / 0.012011 * DH_PER_MOLC[sp] * 1e3
    return tot, out, qchem


class ThroatProps:
    """CEA throat state table over (Pc, O/F): T0, cstar, gamma_t, frozen transport, throat composition."""
    PC = np.array([2.0, 3.0, 4.5, 6.0, 8.0, 10.0, 13.0, 16.0, 20.0, 25.0, 30.0])
    OF = np.array([1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 7.76, 8.5, 9.5, 11.0, 14.0])

    def __init__(self, fn=os.path.join(HERE, '..', 'data', 'v2', 'throat_props_v2.json')):
        if os.path.exists(fn):
            self.t = json.load(open(fn))
        else:
            self.t = self._build(); json.dump(self.t, open(fn, 'w'))
        from scipy.interpolate import RegularGridInterpolator as RGI
        self.f = {k: RGI((np.log(self.PC), self.OF), np.array(v), bounds_error=False, fill_value=None)
                  for k, v in self.t.items()}

    def _build(self):
        from rocketcea.cea_obj_w_units import CEA_Obj
        cea_cards.register_all()
        c = CEA_Obj(oxName='N2O', fuelName='ABS_TYP_v1', pressure_units='bar', cstar_units='m/s', temperature_units='K',
                    specific_heat_units='J/kg-K', viscosity_units='poise', thermal_cond_units='W/cm-degC')
        keys = ['T0', 'cstar', 'gam_t', 'cp_f', 'mu_f', 'Pr_f', 'MW_t'] + ['X_' + s for s in SPECIES]
        T = {k: np.zeros((len(self.PC), len(self.OF))) for k in keys}
        for i, pc in enumerate(self.PC):
            for j, of in enumerate(self.OF):
                T['T0'][i, j] = c.get_Tcomb(Pc=pc, MR=of); T['cstar'][i, j] = c.get_Cstar(Pc=pc, MR=of)
                mw, g = c.get_Throat_MolWt_gamma(Pc=pc, MR=of, eps=2.0); T['gam_t'][i, j] = g; T['MW_t'][i, j] = mw
                cp, mu, k, pr = c.get_Chamber_Transport(Pc=pc, MR=of, eps=2.0, frozen=1)
                T['cp_f'][i, j] = cp; T['mu_f'][i, j] = mu * 0.1; T['Pr_f'][i, j] = pr
                _, mf = c.get_SpeciesMoleFractions(Pc=pc, MR=of, eps=2.0, frozen=0, frozenAtThroat=0, min_fraction=1e-6)
                for s in SPECIES:
                    v = mf.get(s, mf.get('*' + s, [0, 0, 0, 0]))
                    T['X_' + s][i, j] = v[2] if len(v) > 2 else 0.0
        # delivered-state edge composition: Cantera equilibrium (gri30) at the delivered static throat temperature
        # T* = T0 eta_c*^2 * 2/(gam+1) and the throat pressure, elemental composition of ABS_TYP_v1 + N2O at O/F
        import cantera as ct
        fuel = cea_cards.build_cards()['ABS_TYP_v1'][1]
        gas = ct.Solution('gri30.yaml')
        Mf = fuel['M'] / 1000.0
        for s in SPECIES:
            T['Xd_' + s] = np.zeros((len(self.PC), len(self.OF)))
        for i, pc in enumerate(self.PC):
            for j, of in enumerate(self.OF):
                nf = 1.0 / Mf; nox = of / 0.0440128           # mol per kg fuel
                el = {'C': fuel['C'] * nf, 'H': fuel['H'] * nf, 'N': fuel['N'] * nf + 2 * nox, 'O': nox}
                g = T['gam_t'][i, j]
                Tst = T['T0'][i, j] * 0.92 ** 2 * 2 / (g + 1)
                pt = pc * 1e5 * (2 / (g + 1)) ** (g / (g - 1))
                # exact element balance via gri30 species: fuel C:H:N as HCN + C2H2 + H2, oxidiser as N2O
                hcn = fuel['N'] * nf; c2h2 = (el['C'] - hcn) / 2; h2 = (fuel['H'] * nf - 2 * c2h2 - hcn) / 2
                comp = {'HCN': hcn, 'C2H2': c2h2, 'H2': max(h2, 0.0), 'N2O': nox}
                comp = {k: v for k, v in comp.items() if v > 0 and k in gas.species_names}
                gas.TPX = Tst, pt, comp
                gas.equilibrate('TP')
                for s in SPECIES:
                    T['Xd_' + s][i, j] = gas[s].X[0]
        return {k: v.tolist() for k, v in T.items()}

    def __call__(self, Pc, OF):
        pt = (math.log(min(max(Pc / 1e5, self.PC[0]), self.PC[-1])), min(max(OF, self.OF[0]), self.OF[-1]))
        return {k: float(f(pt)) for k, f in self.f.items()}


GRAPHITE = dict(rho=1850.0, eps_surf=0.85,
                tag='DATASHEET class: isomolded fine-grain graphite 1.85 g/cm3 (e.g. Olmec Y472/Y595 1.85 g/cm3, k 115-125 W/mK RT; '
                    'Rotondi et al. 2024 test graphite 1850 kg/m3). k(T), cp(T) typical-isotropic-graphite trends, LITERATURE-UNVERIFIED.')


def k_graphite(T):
    return 120.0 * (300.0 / np.maximum(T, 300.0)) ** 0.55          # ~120 RT -> ~45 W/mK at 1800 K (typical trend)


def cp_graphite(T):
    T = np.maximum(T, 250.0)
    return 2100.0 - 1650.0 * np.exp(-(T - 250.0) / 650.0)            # ~470 at 250 K, ~1300 at 800 K, ~2050 at 2500 K


class ThroatInsert:
    """1-D radial conduction in the insert at the throat station (r_t -> r_o) + lumped metal sleeve."""
    def __init__(self, Rt=0.006862, Ro=0.022, n=40, T0=293.15, m_sleeve=0.15, c_sleeve=900.0, hc=2000.0, Lax=0.032,
                 Dt0=0.013724, Rc_thr=0.5 * (1.5 + 0.382) * 0.006862):
        self.Rt0 = Rt; self.Rt = Rt; self.Ro = Ro; self.n = n
        self.T = np.full(n, T0); self.Ts = T0
        self.m_s = m_sleeve; self.c_s = c_sleeve; self.hc = hc; self.Lax = Lax
        self.Dt0 = Dt0; self.Rc = Rc_thr
        self.recession = 0.0; self.hist = []

    def grid(self):
        r = np.linspace(self.Rt, self.Ro, self.n + 1)
        return r

    def step(self, dt, Pc, OF, TP, on, eps_gas=0.10, mode='coupled', comp='delivered', eta_T=0.92):
        r = self.grid(); rc = 0.5 * (r[1:] + r[:-1]); dr = r[1] - r[0]
        Tw = float(self.T[0])
        q_in = 0.0; mdotC = 0.0; split = {}; hg = 0.0
        if on and Pc > 1.5e5:
            p = TP(Pc, OF)
            g = p['gam_t']; Dt = 2 * self.Rt
            cstar = p['cstar'] * eta_T
            T0d = p['T0'] * eta_T ** 2
            hg = heat.bartz_h(Pc, cstar, Dt, self.Rc, p['mu_f'], p['cp_f'], p['Pr_f'], T0d, g, 1.0, 1.0, Tw)
            Taw = heat.t_aw(T0d, g, 1.0, p['Pr_f'])
            pw = Pc * (2 / (g + 1)) ** (g / (g - 1))
            X = {s: p[('Xd_' if comp == 'delivered' else 'X_') + s] for s in SPECIES}
            mdotC, split, qchem = erosion_rate(Tw, pw, X, p['MW_t'], hg / p['cp_f'], mode)
            Tg = T0d / (1 + (g - 1) / 2)
            q_in = hg * (Taw - Tw) + eps_gas * SIG * (Tg ** 4 - Tw ** 4) - qchem
        # implicit (backward-Euler) conduction, properties lagged; surface flux linearised q = q0 - B (T_w - T_w,old)
        B = 0.0
        if on and Pc > 1.5e5:
            B = hg + 4 * eps_gas * SIG * Tw ** 3
        n = self.n
        k = k_graphite(self.T); cp = cp_graphite(self.T); rho = GRAPHITE['rho']
        kf = 0.5 * (k[1:] + k[:-1])
        C = rho * cp * rc * dr / dt                       # per unit length per radian
        a = np.zeros(n); b = np.zeros(n); c = np.zeros(n); d = C * self.T.copy()
        cond = kf * r[1:-1] / dr                          # conductance between cells i and i+1
        b += C
        b[:-1] += cond; c[:-1] = -cond
        b[1:] += cond; a[1:] = -cond
        # inner surface (cell 0): r_t * (q0 - B (T0_new - T0_old))
        d[0] += r[0] * (q_in + B * Tw); b[0] += r[0] * B
        # outer surface to sleeve: r_o * hc (T_n - Ts), sleeve treated explicitly-lagged
        b[-1] += r[-1] * self.hc; d[-1] += r[-1] * self.hc * self.Ts
        # Thomas algorithm
        cp_ = np.zeros(n); dp_ = np.zeros(n)
        cp_[0] = c[0] / b[0]; dp_[0] = d[0] / b[0]
        for i in range(1, n):
            m = b[i] - a[i] * cp_[i - 1]
            cp_[i] = c[i] / m if i < n - 1 else 0.0
            dp_[i] = (d[i] - a[i] * dp_[i - 1]) / m
        Tn = np.zeros(n); Tn[-1] = dp_[-1]
        for i in range(n - 2, -1, -1):
            Tn[i] = dp_[i] - cp_[i] * Tn[i + 1]
        self.T = Tn
        q_out = self.hc * (self.T[-1] - self.Ts)
        self.Ts += dt * q_out * 2 * math.pi * self.Ro * self.Lax / (self.m_s * self.c_s)
        rr = mdotC / GRAPHITE['rho']
        self.Rt += rr * dt; self.recession += rr * dt
        return dict(Tw=Tw, q_in=q_in, mdotC=mdotC, rr=rr, split=split, Ts=self.Ts)


def run_history(t, Pc, OF, on, TP, dt=2e-3, mode='coupled', eps_gas=0.10, T0=293.15, record=0.05, comp='delivered', eta_T=0.92):
    ins = ThroatInsert(T0=T0)
    out = []; tn = t[0]; k = 0; nxt = t[0]
    while tn <= t[-1]:
        i = min(np.searchsorted(t, tn), len(t) - 1)
        s = ins.step(dt, float(Pc[i]), float(OF[i]) if np.isfinite(OF[i]) else 5.0, TP, bool(on[i]), eps_gas, mode, comp, eta_T)
        if tn >= nxt:
            out.append(dict(t=tn, Pc=float(Pc[i]), OF=float(OF[i]), Tw=s['Tw'], q_in=s['q_in'], rr_mm_s=s['rr'] * 1e3,
                            recession_mm=ins.recession * 1e3, T_sleeve=ins.Ts, T_back=float(ins.T[-1])))
            nxt += record
        tn += dt
    return ins, out


def separation_table(P, opmap_rows, eps_list=(2.0, 1.9, 1.8)):
    """Separation check for each throttle point and eroded expansion ratios."""
    rows = []
    for row in opmap_rows:
        Pc, OF = row['Pc_Pa'], row['OF']
        for eps in eps_list:
            pe = P.pe_pc(Pc, OF, eps) * Pc
            Me = P.mach(Pc, OF, eps)
            sch = (1.88 * Me - 1) ** -0.64
            cf, es, pepa = P.cf_amb(Pc, OF, eps)
            rows.append(dict(frac=row['frac'], Pc_Pa=Pc, OF=OF, eps=eps, pe_pa=pe / PA_SL, Me=Me,
                             summerfield_sep=pe / PA_SL < 0.4, schmucker_psep_pa=sch, schmucker_sep=pe / PA_SL < sch,
                             eps_sep=es if es else ''))
    return rows


if __name__ == '__main__':
    TP = ThroatProps()
    print(TP(25e5, 7.76))
