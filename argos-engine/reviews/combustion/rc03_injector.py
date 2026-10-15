"""RC-03 independent pintle mass-flow check (reviewer, not the author).

Model (reviewer's own implementation): Dyer et al. AIAA 2007-5702 non-homogeneous non-equilibrium (NHNE) blend
    G = Cd [ k/(1+k) G_SPI + 1/(1+k) G_HEM ],  k = sqrt((P1 - P2)/(Pv - P2))
    G_SPI = sqrt(2 rho_l (P1 - P2));  G_HEM = rho_2s sqrt(2 (h1 - h_2s)), isentropic two-phase equilibrium to P2;
    HEM evaluated (i) at P2 = Pc and (ii) choked = max over P' in [Pc, P1].
Upstream: saturated tank at T; injector inlet P1 = Psat(T) - dP_line (author budget 270.4 kPa, and a
flow-scaled variant); liquid treated as metastable at T (rho_l, h_l, s_l = saturated liquid at T).
Geometry: A(h) = pi h sin(a) (Ds - h sin(a) cos(a)), a = 15 deg, Ds = 5.5 mm (author's stated geometry).
Properties: CoolProp 'NitrousOxide'.  Combustion side for the full-stroke case: RocketCEA with the reviewer's
ABS card; fuel flow mdot_f = rho_f L a 2 sqrt(pi) mdot_ox^0.5 (exact for n = 0.5 G_ox law, any port D).
Usage: python -I rc03_injector.py -> rc03_injector.json
"""
import json, math, os
import numpy as np
import CoolProp.CoolProp as CP
from scipy.optimize import brentq
from rocketcea.cea_obj import add_new_fuel
from rocketcea.cea_obj_w_units import CEA_Obj

HERE = os.path.dirname(os.path.abspath(__file__))
FL = 'NitrousOxide'
A_DEG, DS = 15.0, 5.5e-3
G0, PA, EPS = 9.80665, 101325.0, 2.0
AT = math.pi / 4 * 0.013724 ** 2
RHO_F, L_G, A_REG = 1000.0, 0.230, 5.77e-5
KF = RHO_F * L_G * A_REG * 2 * math.sqrt(math.pi)

xA, xB, xS = 0.24, 0.185, 0.575
C = 3 * xA + 4 * xB + 8 * xS; H = 3 * xA + 6 * xB + 8 * xS; N = xA
M = C * 12.011 + H * 1.008 + N * 14.007
add_new_fuel('RV3_ABS', f"fuel RV3_ABS C {C:.5f} H {H:.5f} N {N:.5f} wt%=100.00 h,kj/mol={476.4 * M / 1000:.4f} t(k)=298.15 rho=1.04\n")
CEA = CEA_Obj(oxName='N2O', fuelName='RV3_ABS', pressure_units='bar', cstar_units='m/s', temperature_units='K', isp_units='sec')


def area(h):
    a = math.radians(A_DEG)
    return math.pi * h * math.sin(a) * (DS - h * math.sin(a) * math.cos(a))


def G_models(T, P1, P2):
    Pv = CP.PropsSI('P', 'T', T, 'Q', 0, FL)
    rho_l = CP.PropsSI('D', 'T', T, 'Q', 0, FL)
    h1 = CP.PropsSI('H', 'T', T, 'Q', 0, FL)
    s1 = CP.PropsSI('S', 'T', T, 'Q', 0, FL)
    g_spi = math.sqrt(2 * rho_l * max(P1 - P2, 0.0))

    def g_hem(p):
        rho2 = CP.PropsSI('D', 'P', p, 'S', s1, FL)
        h2 = CP.PropsSI('H', 'P', p, 'S', s1, FL)
        return rho2 * math.sqrt(max(2 * (h1 - h2), 0.0))
    g_hem_p2 = g_hem(P2)
    ps = np.linspace(P2, P1 - 1.0, 200)
    gh = np.array([g_hem(p) for p in ps])
    i = int(np.argmax(gh))
    g_hem_ch = gh[i]
    k = math.sqrt(max(P1 - P2, 0.0) / (Pv - P2))
    dyer = k / (1 + k) * g_spi + 1 / (1 + k) * g_hem_p2
    dyer_ch = k / (1 + k) * g_spi + 1 / (1 + k) * g_hem_ch
    return dict(Pv=Pv, rho_l=rho_l, k=k, G_SPI=g_spi, G_HEM_P2=g_hem_p2, G_HEM_choked=g_hem_ch,
                P_choke_HEM=float(ps[i]), G_Dyer=dyer, G_Dyer_HEMchoked=dyer_ch)


def mdot_ox(h, T, Pc, Cd=0.70, dp_line=270.4e3, model='G_Dyer_HEMchoked'):
    Pv = CP.PropsSI('P', 'T', T, 'Q', 0, FL)
    g = G_models(T, Pv - dp_line, Pc)
    return Cd * area(h) * g[model], g


def engine_point(mox, Pc_guess=25e5):
    """Self-consistent Pc for a given oxidiser flow (n = 0.5 law, eta_c* 0.92)."""
    mf = KF * math.sqrt(mox)
    of = mox / mf
    Pc = Pc_guess
    for _ in range(50):
        cstar = CEA.get_Cstar(Pc=Pc / 1e5, MR=of)
        Pn = (mox + mf) * 0.92 * cstar / AT
        if abs(Pn - Pc) < 10:
            break
        Pc = 0.5 * (Pc + Pn)
    isp_v, cs, _ = CEA.get_IvacCstrTc(Pc=Pc / 1e5, MR=of, eps=EPS)
    cf_vac = isp_v * G0 / cs
    F = (0.975 * cf_vac - EPS * PA / Pc) * Pc * AT
    return dict(Pc=Pc, OF=of, mf=mf, F=F)


def main():
    out = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12')
    # (1) 100 % thrust point at the author's lift 1.916 mm, 20 C, Pc 25.01 bar
    T = 293.15
    m_p2, g = mdot_ox(1.916e-3, T, 25.01e5, model='G_Dyer')   # HEM taken at P2 (beyond its choke point)
    m = m_ch = mdot_ox(1.916e-3, T, 25.01e5)[0]                # HEM choked (adopted)
    m_hem, _ = mdot_ox(1.916e-3, T, 25.01e5, model='G_HEM_choked')
    m_spi, _ = mdot_ox(1.916e-3, T, 25.01e5, model='G_SPI')
    # flow-scaled line loss variant (dp ~ mdot^2, 270.4 kPa at 0.26 kg/s)
    dpl = 270.4e3 * (m / 0.26) ** 2
    m_fs, _ = mdot_ox(1.916e-3, T, 25.01e5, dp_line=dpl)
    Cd_implied = 0.70 * 0.24099 / m
    out['point_100pct'] = dict(lift_mm=1.916, T_K=T, Pc_bar=25.01, area_mm2=area(1.916e-3) * 1e6, models=g,
                               mdot_Dyer_HEMchoked=m_ch, mdot_Dyer_HEM_at_P2=m_p2, mdot_HEM_choked_Cd07=m_hem, mdot_SPI_Cd07=m_spi,
                               mdot_Dyer_flow_scaled_line=m_fs, author_mdot=0.24099,
                               d_pct=100 * (m / 0.24099 - 1), Cd_to_match_author=Cd_implied,
                               ratio_HEMch_over_Dyer=g['G_HEM_choked'] / g['G_Dyer'], ratio_SPI_over_Dyer=g['G_SPI'] / g['G_Dyer'])
    print(f"100 %: A {area(1.916e-3)*1e6:.3f} mm2, mdot Dyer(HEM choked) {m:.4f} kg/s (author 0.24099, {100*(m/0.24099-1):+.2f} %), "
          f"Dyer w/ HEM at P2 {m_p2:.4f}, HEM {m_hem:.4f}, SPI {m_spi:.4f}, flow-scaled line {m_fs:.4f}; "
          f"HEM/Dyer {g['G_HEM_choked']/g['G_Dyer']:.3f} (P_choke {g['P_choke_HEM']/1e5:.1f} bar) SPI/Dyer {g['G_SPI']/g['G_Dyer']:.3f}, k {g['k']:.3f}")
    # (2) full stroke 4 mm, self-consistent chamber, T 15-30 C, Cd 0.6-0.8 (author Table 3.7)
    rows = []
    for Tc in (15.0, 20.0, 25.0, 30.0):
        T = 273.15 + Tc
        for Cd in (0.6, 0.7, 0.8):
            Pc = 30e5
            for _ in range(40):
                mo, _ = mdot_ox(4.0e-3, T, Pc, Cd=Cd)
                ep = engine_point(mo, Pc)
                if abs(ep['Pc'] - Pc) < 20:
                    break
                Pc = 0.5 * (Pc + ep['Pc'])
            Pv = CP.PropsSI('P', 'T', T, 'Q', 0, FL)
            rows.append(dict(T_C=Tc, Cd=Cd, Pv_bar=Pv / 1e5, mdot_ox=mo, Pc_bar=ep['Pc'] / 1e5, F_N=ep['F'], OF=ep['OF'],
                             dP_over_Pc=(Pv - 270.4e3 - ep['Pc']) / ep['Pc']))
            r = rows[-1]
            print(f"full stroke T {Tc:4.1f} C Cd {Cd:.1f}: mdot_ox {mo:.4f} Pc {r['Pc_bar']:.2f} bar F {r['F_N']:.0f} N O/F {r['OF']:.2f} dP/Pc {r['dP_over_Pc']:.3f}")
    out['full_stroke'] = rows
    # (3) cold-flow inventory at the ignition lifts (into ~1.5 bar), for the hard-start check
    cold = {}
    for frac, h in (('12.5pct', 0.207e-3), ('20pct', 0.301e-3)):
        mo, _ = mdot_ox(h, 293.15, 1.5e5)
        cold[frac] = dict(lift_mm=h * 1e3, mdot_cold_kg_s=mo, admitted_0p23s_g=mo * 0.23 * 1e3)
        print(f"cold flow at {frac} lift into 1.5 bar: {mo*1e3:.1f} g/s -> {mo*0.23*1e3:.1f} g in the 0.12-0.35 s window")
    out['cold_ignition_lift'] = cold
    json.dump(out, open(os.path.join(HERE, 'rc03_injector.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main()
