"""Fast-chemistry afterburning post-processor (Combustion / 05-plume-cfd v3).

Conserved-scalar (mixture fraction Z) + Cantera (GRI-3.0 thermo) equilibrium, FAST-CHEMISTRY ASSUMPTION (labelled).
  stream 2 (Z = 0): dry air (N2 0.78084, O2 0.20946, Ar 0.00934, CO2 0.00036) at 288.15 K.
  stream 1 (Z = 1): exhaust, elements of the CEA chamber composition at the CFD operating point.
  cell state from the CFD: Z, static pressure p, velocity |u|; total enthalpy h0 = Z h0_1 + (1-Z) h0_2 (unity Lewis
     number / equal turbulent diffusivities), static h = h0 - |u|^2/2.
  Exhaust energy (stream A, primary): h0_1 = mass-weighted mean over the CFD nozzle-exit plane of
     h_eq(T_cfd, p_cfd) + |u|^2/2, with h_eq the enthalpy of the exhaust elements in local TP equilibrium. The c* deficit
     (eta_c* 0.92) is treated as lost, as in the CFD inflow (T0 = eta^2 Tc).
  Three temperatures per cell at the same (Z, h, p):
     T_eq    : HP equilibrium of the whole mixture (exhaust reacts with entrained air: complete afterburning);
     T_inert : exhaust in its own local equilibrium (recombination allowed), air INERT (no afterburning), common T;
               solved by bisection on a tabulated h_eq,exh(T, p) (TP equilibria, 10 K x 18 pressures);
     dT_ab = T_eq - T_inert : afterburning temperature rise (CO/H2/radicals + air O2). It is zero by construction in
               the pure-exhaust core (check reported: max |T_eq - T_inert| for Z > 0.999);
     T_ab_cfd = T_cfd + dT_ab : CFD temperature with the fast-chemistry afterburning increment (used for the
               synthetic image; keeps the CFD calorically-perfect-gas temperature level).
  Gas-model check: T_inert - T_cfd in the exhaust core measures how well the CFD calorically perfect exhaust gas
     (gamma 1.13676) represents an equilibrium exhaust along the expansion / Mach-disk compression.
  Stream B (upper bound, labelled): h0_1 = h(Tc, Pc, X_chamber), the full propellant enthalpy (c* deficit released by
     fast chemistry in the plume); T_eqB only.
History (kept as evidence, 05-plume-cfd REPORT):
  v1: full-enthalpy stream mixed with the frozen exit composition: frozen T up to 3942 K in the core, inconsistent.
  v2: frozen exit composition calibrated to the exit plane; dT = T_eq - T_frozen conflated afterburning with
      exhaust recombination (dT up to 537 K at Z = 1.000, i.e. with no air) and frozen-cp vs CFD-gas mismatch
      (T_frz - T_cfd -538..+436 K in the core). Replaced by the equilibrium-inert reference above.
Not represented: finite-rate kinetics (ignition delay of CO/H2 in the cool, fast near-field mixing layer), turbulence-
chemistry interaction (mean Z instead of a Z-PDF), soot, radiation losses.
usage: python afterburn.py RUN/final.npz OUT.npz [--frac 1.0]
"""
from __future__ import annotations
import json, math, os, sys, time
import numpy as np
import cantera as ct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

AIR_X = {'N2': 0.78084, 'O2': 0.20946, 'AR': 0.00934, 'CO2': 0.00036}
PA, TA = 101325.0, 288.15
TG = np.arange(200.0, 3800.0 + 1e-9, 10.0)                 # K, uniform (table)
PG = np.exp(np.linspace(math.log(0.05e5), math.log(40e5), 18))   # Pa, log-uniform


def cea_streams(frac=1.0, OF_override=None, Pc_override=None):
    import plume2s as P
    J, pts, Rbody = P.load_geometry()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
    import cea_cards
    from rocketcea.cea_obj import CEA_Obj
    cea_cards.register_all()
    tp = [p for p in J['operating_points']['throttle_points_20C_initial_port'] if abs(p['fraction'] - frac) < 1e-6][0]
    Pc, OF = tp['Pc_Pa'], tp['OF']
    if OF_override is not None:      # composition sensitivity (e.g. v2 S230 exhaust on a v1 flow field), 2026-10-12
        OF = float(OF_override)
    if Pc_override is not None:
        Pc = float(Pc_override)
    eps = J['gas_path']['nozzle']['expansion_ratio']['v']
    c = CEA_Obj(oxName='N2O', fuelName='ABS_TYP_v1')
    Pc_psia = Pc / 6894.757
    mw, mf = c.get_SpeciesMoleFractions(Pc=Pc_psia, MR=OF, eps=eps, frozen=0, frozenAtThroat=0, min_fraction=1e-7)
    Tc = c.get_Tcomb(Pc=Pc_psia, MR=OF) / 1.8          # degR -> K
    temps = c.get_Temperatures(Pc=Pc_psia, MR=OF, eps=eps)
    Te = temps[2] / 1.8
    gas = ct.Solution('gri30.yaml')
    names = set(gas.species_names)

    def comp(idx):
        X = {}
        dropped = 0.0
        for k, v in mf.items():
            n = k.strip('*').upper() if k.strip('*') not in names else k.strip('*')
            n = 'AR' if n.upper() == 'AR' else n
            if n in names:
                X[n] = X.get(n, 0.0) + v[idx]
            else:
                dropped += v[idx]
        s = sum(X.values())
        return {k: v / s for k, v in X.items()}, dropped
    Xc, dc = comp(1); Xe, de = comp(3)
    gas.TPX = Tc, Pc, Xc
    h0 = gas.enthalpy_mass
    Yc = gas.Y.copy()
    g2 = ct.Solution('gri30.yaml'); g2.TPX = Tc, Pc, Xc; g2.equilibrate('HP')   # consistency: Cantera vs CEA Tc
    pe = Pc / c.get_PcOvPe(Pc=Pc_psia, MR=OF, eps=eps)
    gas.TPX = Te, pe, Xe
    Ye = gas.Y.copy()
    gas.TPX = TA, PA, AIR_X
    h_air = gas.enthalpy_mass; Ya = gas.Y.copy()

    def elem_per_kg(Y):
        gas.TPY = 1000.0, PA, Y
        return {e: gas.elemental_mass_fraction(e) / gas.atomic_weight(e) for e in ('C', 'H', 'O', 'N')}
    E1 = elem_per_kg(Yc); E2 = elem_per_kg(Ya)
    beta1 = E1['O'] - 2 * E1['C'] - 0.5 * E1['H']
    beta2 = E2['O'] - 2 * E2['C'] - 0.5 * E2['H']
    Zst = beta2 / (beta2 - beta1) if beta1 < 0 else float('nan')
    info = dict(frac=frac, Pc=Pc, OF=OF, Tc_cea=Tc, Te_cea=Te, pe_cea=pe, Tc_cantera_check=g2.T, h0_exhaust=h0,
                h_air=h_air, X_chamber=Xc, X_exit=Xe, dropped_mole_fraction=dict(chamber=dc, exit=de), Z_st=Zst,
                excess_O_per_kg_exhaust=beta1)
    return info, Yc, Ye, Ya


def exh_eq_table(Yx):
    """h_eq(T, p) [J/kg] of the exhaust elements in TP equilibrium on (TG, PG)."""
    gas = ct.Solution('gri30.yaml')
    H = np.empty((len(TG), len(PG))); nfail = 0
    for b, p in enumerate(PG):
        gas.TPY = 2500.0, p, Yx
        for a, T in enumerate(TG):
            try:
                gas.TP = T, p
                gas.equilibrate('TP')
            except Exception:
                nfail += 1
                gas.TPY = T, p, Yx
            H[a, b] = gas.enthalpy_mass
    return H, nfail


def air_table(Ya):
    gas = ct.Solution('gri30.yaml')
    out = np.empty(len(TG))
    for a, T in enumerate(TG):
        gas.TPY = T, PA, Ya
        out[a] = gas.enthalpy_mass
    return out


def _pidx(p):
    lp = np.log(np.clip(p, PG[0], PG[-1]))
    s = (lp - math.log(PG[0])) / (math.log(PG[1]) - math.log(PG[0]))
    s = np.clip(s, 0, len(PG) - 1 - 1e-9)
    ip = s.astype(int)
    return ip, s - ip


def h_exh(T, ip, wp, H):
    t = np.clip((T - TG[0]) / (TG[1] - TG[0]), 0, len(TG) - 1 - 1e-9)
    it = t.astype(int); wt = t - it
    return ((1 - wt) * ((1 - wp) * H[it, ip] + wp * H[it, ip + 1])
            + wt * ((1 - wp) * H[it + 1, ip] + wp * H[it + 1, ip + 1]))


def h_air_T(T, Ha):
    return np.interp(T, TG, Ha)


def solve_T_inert(h, z, p, H, Ha, it=45):
    ip, wp = _pidx(p)
    lo = np.full(h.shape, TG[0]); hi = np.full(h.shape, TG[-1])
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        f = z * h_exh(mid, ip, wp, H) + (1 - z) * h_air_T(mid, Ha) - h
        lo = np.where(f < 0, mid, lo); hi = np.where(f >= 0, mid, hi)
    T = 0.5 * (lo + hi)
    clamped = (T < TG[0] + 1.0) | (T > TG[-1] - 1.0)
    return T, clamped


def exit_plane_h0(d, H, Ye):
    """Mass-weighted stagnation enthalpy of the CFD nozzle-exit plane: equilibrium (primary) and frozen-exit-
    composition (v2, for the record) thermo."""
    m = json.loads(str(d['meta']))
    Nn = m['grid']['Nn']; jc = m['grid']['jc']
    i = Nn - 1
    gas = ct.Solution('gri30.yaml')
    num_eq = num_fr = den = 0.0
    for j in range(jc):
        if d['region'][i, j] == 3:
            continue
        T, p = float(d['T'][i, j]), float(d['p'][i, j])
        ke = 0.5 * float(d['u'][i, j] ** 2 + d['v'][i, j] ** 2)
        w = float(d['rho'][i, j] * d['u'][i, j] * d['rc'][i, j])
        ip, wp = _pidx(np.array([p]))
        num_eq += w * (float(h_exh(np.array([T]), ip, wp, H)[0]) + ke)
        gas.TPY = T, p, Ye
        num_fr += w * (gas.enthalpy_mass + ke); den += w
    return num_eq / den, num_fr / den


def process(fn, out, frac=1.0, zmin=2e-3, OF_override=None, Pc_override=None):
    t0 = time.time()
    d = np.load(fn, allow_pickle=False)
    Z = np.clip(d['Y'], 0, 1); p = d['p']; KE = 0.5 * (d['u'] ** 2 + d['v'] ** 2); region = d['region']
    Tcfd = d['T']
    info, Yc, Ye, Ya = cea_streams(frac, OF_override, Pc_override)
    if OF_override is not None or Pc_override is not None:
        info['composition_override'] = dict(OF=OF_override, Pc=Pc_override, note='exhaust composition from CEA at the override '
                                            'O/F/Pc; flow field (T, p, u, Z) from the CFD run at its own O/F: SENSITIVITY only')
    H, nfail_tab = exh_eq_table(Yc)
    Ha = air_table(Ya)
    h0A, h0A_frz = exit_plane_h0(d, H, Ye)
    info.update(h0_exhaust_A_eq=h0A, h0_exhaust_A_frozen_v2=h0A_frz, h0_exhaust_B_full=info['h0_exhaust'],
                table=dict(T_K=[float(TG[0]), float(TG[-1]), float(TG[1] - TG[0])],
                           p_Pa=[float(PG[0]), float(PG[-1]), len(PG)], tp_equilibrium_failures=nfail_tab),
                note=('A: exhaust energy calibrated to the CFD exit plane with equilibrium thermo (c* deficit lost, as '
                      'in the CFD); B: full propellant enthalpy (c* deficit released by fast chemistry) = upper bound'))
    gas = ct.Solution('gri30.yaml')
    sh = Z.shape
    Teq = np.full(sh, np.nan); TeqB = np.full(sh, np.nan)
    XCO = np.zeros(sh); XOH = np.zeros(sh); XCO2 = np.zeros(sh); XO2 = np.zeros(sh); XH2 = np.zeros(sh)
    fluid = region != 3
    sel = (Z > zmin) & fluid
    idx = np.argwhere(sel)
    hA = Z * h0A + (1 - Z) * info['h_air'] - KE
    hB = Z * info['h0_exhaust'] + (1 - Z) * info['h_air'] - KE
    nfail = 0
    iCO, iOH, iCO2, iO2, iH2 = (gas.species_index(s) for s in ('CO', 'OH', 'CO2', 'O2', 'H2'))
    Tin = np.full(sh, np.nan)
    Ti, clamped = solve_T_inert(hA[sel], Z[sel], p[sel], H, Ha)
    Tin[sel] = Ti
    for i, j in idx:
        z = Z[i, j]
        Ymix = z * Yc + (1 - z) * Ya
        try:
            # start from a TP equilibrium at the inert-air temperature: setting HP directly on the radical-rich chamber
            # composition needs T < 200 K in the over-expanded core (438 failures on the coarse grid in the first try)
            gas.TPY = min(max(float(Tin[i, j]), 300.0), 3700.0), p[i, j], Ymix
            gas.equilibrate('TP')
            gas.HP = hA[i, j], p[i, j]
            gas.equilibrate('HP')
            Teq[i, j] = gas.T
            X = gas.X
            XCO[i, j] = X[iCO]; XOH[i, j] = X[iOH]; XCO2[i, j] = X[iCO2]; XO2[i, j] = X[iO2]; XH2[i, j] = X[iH2]
            gas.HP = hB[i, j], p[i, j]
            gas.equilibrate('HP')
            TeqB[i, j] = gas.T
        except Exception:
            nfail += 1
    dT = np.where(sel, Teq - Tin, 0.0)
    Tab = np.where(sel & np.isfinite(dT), Tcfd + dT, Tcfd)
    info['cells_processed'] = int(len(idx)); info['cells_failed'] = nfail
    info['inert_solver_clamped_cells'] = int(clamped.sum())
    x = d['xc'] / json.loads(str(d['meta']))['grid']['De']
    core = (Z > 0.999) & fluid & np.isfinite(Teq) & np.isfinite(Tin)
    if core.any():
        e = (Teq - Tin)[core]
        info['check_Teq_minus_Tinert_core_K'] = dict(n=int(core.sum()), mean=float(e.mean()), max_abs=float(np.abs(e).max()))

    def stats(m):
        e = (Tin - Tcfd)[m]
        if e.size == 0:
            return None
        k = np.argmax(np.where(m, np.abs(Tin - Tcfd), -1))
        return dict(n=int(e.size), mean=float(e.mean()), p5=float(np.percentile(e, 5)), p50=float(np.median(e)),
                    p95=float(np.percentile(e, 95)), max_abs=float(np.abs(e).max()),
                    at_x_De=float(x.flat[k]), T_cfd_there=float(Tcfd.flat[k]), T_inert_there=float(Tin.flat[k]))
    ok = fluid & np.isfinite(Tin)
    info['gas_model_check_Tinert_minus_Tcfd_K'] = dict(
        exit_plane_core=stats(ok & (Z > 0.999) & (np.abs(x + 0.0) < 0.05)),
        nozzle_and_chamber=stats(ok & (Z > 0.999) & (x < 0)),
        plume_core_Z_gt_0p999=stats(ok & (Z > 0.999) & (x > 0)),
        plume_mixing_Z_0p05_0p999=stats(ok & (Z > 0.05) & (Z <= 0.999) & (x > 0)))
    info['runtime_s'] = time.time() - t0
    np.savez_compressed(out, T_eq=Teq, T_inert=Tin, dT_ab=dT, T_ab_cfd=Tab, T_eqB=TeqB, X_CO=XCO, X_OH=XOH,
                        X_CO2=XCO2, X_O2=XO2, X_H2=XH2, Z=Z, info=json.dumps(info, default=float))
    return info


if __name__ == '__main__':
    frac = 1.0
    if '--frac' in sys.argv:
        frac = float(sys.argv[sys.argv.index('--frac') + 1])
    OFo = float(sys.argv[sys.argv.index('--OF') + 1]) if '--OF' in sys.argv else None
    Pco = float(sys.argv[sys.argv.index('--Pc') + 1]) if '--Pc' in sys.argv else None
    info = process(sys.argv[1], sys.argv[2], frac, OF_override=OFo, Pc_override=Pco)
    print(json.dumps({k: v for k, v in info.items() if k not in ('X_chamber', 'X_exit')}, indent=1, default=float))
