"""RC-08 order-of-magnitude graphite throat erosion (reviewer, not the author).

Three independent estimates:
 (1) Diffusion-limited ceiling (film theory, Spalding): mdot_C'' = (h_g/cp) ln(1 + B), B = sum_i Y_i,e s_i,
     s_i = kg C removed per kg of oxidising species (C+1/2O2->CO 0.750, C+O->CO 0.750, C+OH->CO+H 0.706,
     C+H2O->CO+H2 0.667, C+NO->CO+1/2N2 0.400, C+CO2->2CO 0.273).  Edge composition: Cantera GRI-3.0 equilibrium with the
     reviewer's ABS card (delivered state 2757 K and ideal HP state) at Pc 25.01 bar, O/F 10.435.  h_g/cp from the
     reviewer's Bartz run (rc04_bartz.json, delivered-state properties, mean Rc).  Graphite 1850 kg/m3 (anchor grade).
 (2) O2-only surface kinetics, Nagle-Strickland-Constable [LITERATURE, constants as recalled, x12 g/mol convention],
     wall partial pressure = edge X_O2 x throat static pressure (no film depletion): an upper bound on the O2 term.
 (3) Literature-scaled, the author's method re-applied by the reviewer to the reviewer's own 0-D engine histories over
     the gnc.json v2 duty cycles: N2O/HDPE measured averages (Rotondi et al., JPP 40(3) 2024, as quoted by the author)
     O/F >= 7: 0.098-0.139 mm/s, 4.8-7: 0.018-0.048 mm/s, < 4.8: 0; x (Pc/35 bar)^0.68; after a 1.5 s cumulative onset.
     Also re-run on the v1 A1 cycle to compare with the author's Table 5.3 (0.159-0.237 mm).
Insert life rule (author / ENG-06 rev 2): replace at dAt/At = 5 %  ->  allowed radial recession Rt (sqrt(1.05) - 1).
Usage: python -I rc08_erosion.py -> rc08_erosion.json
"""
import json, math, os, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cantera as ct
import rc05_grain as G

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, '..', '..'))
PC, OF = 25.01e5, 10.435
RHO_GR = 1850.0
RT_MM = 13.724 / 2
S = {'O2': 0.750, 'O': 0.750, 'OH': 12.011 / 17.007, 'H2O': 12.011 / 18.015, 'NO': 12.011 / 30.006, 'CO2': 12.011 / 44.01}
RCAL = 1.98720  # cal/mol/K


def edge_state(T=None):
    g = ct.Solution('gri30.yaml')
    g.TPX = 298.15, ct.one_atm, 'N2O:1'
    h_n2o = g.enthalpy_mass
    h_mix = (OF * h_n2o + 476.4e3) / (1 + OF)
    n_ox = OF / (1 + OF) / 0.044013; n_fu = 1 / (1 + OF) / (G.M / 1000)
    nC, nH, nN, nO = n_fu * G.C, n_fu * G.H, n_fu * G.N + 2 * n_ox, n_ox
    g.TPX = 2500, PC, {'CO2': nC, 'H2O': nH / 2, 'N2': nN / 2, 'O2': (nO - 2 * nC - nH / 2) / 2}
    g.HP = h_mix, PC
    g.equilibrate('HP')
    if T is not None:
        g.TP = T, PC
        g.equilibrate('TP')
    Y = {k: float(g.Y[g.species_index(k)]) for k in S}
    X = {k: float(g.X[g.species_index(k)]) for k in S}
    return dict(T=g.T, Y=Y, X=X, B=sum(Y[k] * S[k] for k in S))


def nsc_rate(Tw, p_o2_atm):
    kA = 20.0 * math.exp(-30000 / (RCAL * Tw)); kB = 4.46e-3 * math.exp(-15200 / (RCAL * Tw))
    kT = 1.51e5 * math.exp(-97000 / (RCAL * Tw)); kZ = 21.3 * math.exp(4100 / (RCAL * Tw))
    chi = 1 / (1 + kT / (kB * p_o2_atm))
    w = 12 * (kA * p_o2_atm * chi / (1 + kZ * p_o2_atm) + kB * p_o2_atm * (1 - chi))  # g/cm2/s
    return w * 10.0  # kg/m2/s


def history(path, a, n, dt=0.02):
    t, F = G.load_dc(path)
    tg = np.arange(t[0], t[-1], dt)
    Fg = np.interp(tg, t, F)
    D = G.D0; rows = []
    for ti, Fi in zip(tg, Fg):
        if Fi < 5.0:
            rows.append((ti, 0.0, float('nan'), False)); continue
        mo = G.mox_for(Fi, D, a, n)
        F_, mf, of, Pc = G.thrust_for(mo, D, a, n)
        rows.append((ti, Pc, of, True))
        D = math.sqrt(D ** 2 + 4 * mf * dt / (math.pi * G.RHO_F * G.LG))
    return rows, dt


def literature(rows, dt):
    lo = hi = cum = 0.0; t_hi = t_mid = 0.0
    for ti, Pc, of, on in rows:
        if not on:
            continue
        cum += dt
        if of >= 7.0:
            t_hi += dt
        elif of >= 4.8:
            t_mid += dt
        if cum < 1.5:
            continue
        sc = (Pc / 35e5) ** 0.68
        if of >= 7.0:
            lo += 0.098e-3 * sc * dt; hi += 0.139e-3 * sc * dt
        elif of >= 4.8:
            lo += 0.018e-3 * sc * dt; hi += 0.048e-3 * sc * dt
    return lo * 1e3, hi * 1e3, t_hi, t_mid, cum


def main():
    out = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12')
    bz = json.load(open(os.path.join(HERE, 'rc04_bartz.json')))
    r2 = bz['results']['P2_delivered_state_cantera|Rc_mean']
    g_star = r2['h_g'] / r2['props']['cp']
    p_t_atm = PC * 0.5745 / 101325.0   # throat static ~0.574 Pc for gamma ~1.15
    diff = {}
    for lab, T in (('delivered_2757K', 2757.0), ('ideal_HP', None)):
        es = edge_state(T)
        mdc = g_star * math.log(1 + es['B'])
        diff[lab] = dict(T=es['T'], B=es['B'], Y=es['Y'], X=es['X'], g_star_kg_m2s=g_star, mdotC_kg_m2s=mdc,
                         rate_mm_s=mdc / RHO_GR * 1e3)
        print(f"diffusion ceiling {lab}: T {es['T']:.0f} K, B {es['B']:.4f}, X_O2 {es['X']['O2']:.4f}, h_g/cp {g_star:.2f} kg/m2s "
              f"-> {mdc:.3f} kg/m2s = {mdc/RHO_GR*1e3:.3f} mm/s")
    out['diffusion_ceiling'] = diff
    xo2 = diff['delivered_2757K']['X']['O2']
    kin = {}
    for Tw in (1500.0, 1800.0, 2000.0, 2500.0):
        w = nsc_rate(Tw, xo2 * p_t_atm)
        kin[str(int(Tw))] = dict(p_O2_atm=xo2 * p_t_atm, rate_kg_m2s=w, rate_um_s=w / RHO_GR * 1e6)
        print(f"NSC O2 only at Tw {Tw:.0f} K, p_O2 {xo2*p_t_atm:.2f} atm: {w/RHO_GR*1e6:.2f} um/s")
    out['nsc_O2_kinetic'] = kin
    dr_allow = RT_MM * (math.sqrt(1.05) - 1)
    out['allowed_recession_mm_at_5pct'] = dr_allow
    dcdir = os.path.join(HUB, '01-systems-gnc/duty_cycles')
    cases = [('A1_v2', 'DC-A1_full_flight_drogue_fins_300m_v2.csv', (0.6, 1.0, 1.5)),
             ('A1_v1', 'DC-A1_full_flight_drogue_300m_v1.csv', (1.0,)),
             ('B1_v2', 'DC-B1_hop_100m_floor20_v2.csv', (1.0,)),
             ('B2_v2', 'DC-B2_hop_50m_floor20_v2.csv', (1.0,)),
             ('A2_v2_removed_from_plan', 'DC-A2_full_flight_freefall_300m_v2.csv', (1.0,))]
    lit = {}
    for name, fn, scs in cases:
        for sc in scs:
            rows, dt = history(os.path.join(dcdir, fn), 5.77e-5 * sc, 0.5)
            lo, hi, t_hi, t_mid, burn = literature(rows, dt)
            dA = [100 * (((RT_MM + x) / RT_MM) ** 2 - 1) for x in (lo, hi)]
            fl = [dr_allow / x if x > 0 else float('inf') for x in (hi, lo)]
            lit[f'{name}|x{sc}'] = dict(burn_s=burn, t_OF_ge7_s=t_hi, t_OF_4p8_7_s=t_mid, recession_mm=[lo, hi],
                                        dAt_At_pct=dA, flights_per_insert_5pct=fl)
            print(f"literature-scaled {name} x{sc}: burn {burn:.2f} s (O/F>=7 {t_hi:.2f} s, 4.8-7 {t_mid:.2f} s) -> "
                  f"{lo:.3f}-{hi:.3f} mm, dAt/At {dA[0]:.1f}-{dA[1]:.1f} %, flights/insert {fl[0]:.2f}-{fl[1]:.2f}")
    out['literature_scaled_reviewer_histories'] = lit
    out['author_table_5_3_A1_v1_x1'] = dict(nominal_mm=0.040, conservative_mm=0.169, literature_mm=[0.159, 0.237],
                                            life_claim_flights=[1.0, 4.3])
    json.dump(out, open(os.path.join(HERE, 'rc08_erosion.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main()
