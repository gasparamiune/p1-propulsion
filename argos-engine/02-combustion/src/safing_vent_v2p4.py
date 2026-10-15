"""Remote tank vent: blow-down time of the flight tank through a top (vapour-space) vent (Combustion v2.4, RC-04 / RC-05
safing; 2026-10-13).

Purpose: size the remote vent that ENG-16 and charter rule 8 require, for (i) a scrubbed pad launch or an aborted
ground test with the full load, (ii) the post-landing residual of A1, (iii) the residual after a heat soak.
Model (DERIVED, CoolProp equilibrium fluid):
  * rigid tank V 3.167 L (LEAD 3.17 L); fluid homogeneous in equilibrium; the vent draws saturated vapour from the top
    while two-phase (h_out = h_g), the fluid state when single-phase;
  * vent mass flux = Cd x G_HEM(state), Cd 0.80 (ASSUMED sharp orifice), G_HEM = isentropic homogeneous-equilibrium flux
    maximised over the throat pressure (choking) to 1 atm, tabulated along the saturated-vapour line;
  * wall: 6061 tank 1.44 kg (run_dc.make_tank wall mass), c 900 J/kg K; two bounds:
      'adiabatic' : no heat from the wall or the ambient (pressure falls fastest; cold liquid is left behind),
      'wall_eq'   : wall at the fluid temperature (its heat capacity joins the fluid) plus ambient natural convection
                    10 W/m2 K x 0.17 m2 to 20 C air (ASSUMED) (slower pressure fall, more complete evaporation).
  Reported: time to 10 bar and 2 bar gauge-equivalent absolute (11 / 3 bar abs), mass left, fluid temperature.
usage: python -I safing_vent_v2p4.py OUTDIR
"""
from __future__ import annotations
import json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP

FL = 'NitrousOxide'; PA = 101325.0
V = 3.1670975e-3; M_W = 1.44; C_W = 900.0; hA_amb = 10.0 * 0.17; T_AMB = 293.15; CD = 0.80


def hem_flux(P0, h0, n=80):
    s0 = CP.PropsSI('S', 'P', P0, 'H', h0, FL)
    best = 0.0
    for p in np.linspace(PA * 1.01, P0 * 0.999, n):
        try:
            rho = CP.PropsSI('D', 'P', p, 'S', s0, FL); h = CP.PropsSI('H', 'P', p, 'S', s0, FL)
        except ValueError:
            continue
        best = max(best, rho * math.sqrt(max(2 * (h0 - h), 0.0)))
    return best


TT = np.linspace(190.0, 308.0, 40)
GV = np.array([hem_flux(CP.PropsSI('P', 'T', T, 'Q', 1, FL), CP.PropsSI('H', 'T', T, 'Q', 1, FL)) for T in TT])


def state_DU(m, U):
    rho = m / V; u = U / m
    P = CP.PropsSI('P', 'D', rho, 'U', u, FL); T = CP.PropsSI('T', 'D', rho, 'U', u, FL)
    try:
        x = CP.PropsSI('Q', 'D', rho, 'U', u, FL)
    except ValueError:
        x = -1.0
    return P, T, x


def T_from_E(m, E):
    """Wall at the fluid temperature: E = m u(rho, T) + M_W C_W T. Solve for T (brentq)."""
    from scipy.optimize import brentq
    rho = m / V
    f = lambda T: m * CP.PropsSI('U', 'D', rho, 'T', T, FL) + M_W * C_W * T - E
    return brentq(f, 185.0, 420.0, xtol=1e-4)


def props_DT(m, T):
    rho = m / V
    P = CP.PropsSI('P', 'D', rho, 'T', T, FL)
    try:
        x = CP.PropsSI('Q', 'D', rho, 'T', T, FL)
    except ValueError:
        x = -1.0
    if not (0.0 <= x <= 1.0):
        x = -1.0
    return P, x


def blowdown(m0, T0, d_mm, mode, t_max=3600.0):
    A = math.pi / 4 * (d_mm * 1e-3) ** 2
    rho0 = m0 / V
    U = m0 * CP.PropsSI('U', 'T', T0, 'D', rho0, FL)
    m = m0; t = 0.0
    E = U + M_W * C_W * T0
    P, x = props_DT(m, T0); T = T0
    out = dict(P0_bar=round(P / 1e5, 3), T0_K=T0, m0_kg=m0)
    marks = {'11bar': None, '3bar': None}
    dt = 0.05
    while t < t_max and P > 1.2e5 and m > 1e-3:
        if 0.0 <= x <= 1.0:
            G = float(np.interp(T, TT, GV)); h_out = CP.PropsSI('H', 'T', T, 'Q', 1, FL)
        else:
            h_out = CP.PropsSI('H', 'D', m / V, 'T', T, FL)
            G = hem_flux(P, h_out, n=30)
        md = CD * A * G
        Q = hA_amb * (T_AMB - T) if mode == 'wall_eq' else 0.0
        dm = min(md * dt, 0.5 * m)
        m -= dm
        if mode == 'wall_eq':
            E += -dm * h_out + Q * dt
            T = T_from_E(m, E)
            P, x = props_DT(m, T)
        else:
            U += -dm * h_out
            P, T, x = state_DU(m, U)
        t += dt
        for k, lim in (('11bar', 11e5), ('3bar', 3e5)):
            if marks[k] is None and P <= lim:
                marks[k] = dict(t_s=round(t, 1), m_left_kg=round(m, 4), T_K=round(T, 1), quality=round(x, 3))
        dt = 0.05 if t < 10 else (0.2 if t < 120 else 1.0)
    out.update(t_end_s=round(t, 1), P_end_bar=round(P / 1e5, 3), m_end_kg=round(m, 4), T_end_K=round(T, 1), marks=marks)
    return out


def main(outdir):
    cases = {'scrub_full_load_20C': (2.00, 293.15), 'A1_residual_0p61kg_20C': (0.61, 293.15),
             'A1_residual_0p555kg_280K': (0.5553, 280.5), 'A1_residual_0p61kg_soaked_40C': (0.61, 313.15)}
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/safing_vent_v2p4.py',
               note='DERIVED CoolProp blow-down through a top vent, Cd 0.80 ASSUMED, HEM choked flux; wall 1.44 kg 6061; two '
                    'heat bounds (adiabatic / wall-equilibrium + 10 W/m2K ambient); vent line losses not included', cases={})
    for cname, (m0, T0) in cases.items():
        for d in (1.0, 2.0, 3.0):
            for mode in ('adiabatic', 'wall_eq'):
                key = f'{cname}|d{d:.1f}mm|{mode}'
                o = blowdown(m0, T0, d, mode)
                res['cases'][key] = o
                print(key, json.dumps(o), flush=True)
    fn = os.path.join(outdir, 'safing_vent_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1])
