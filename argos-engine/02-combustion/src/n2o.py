"""N2O properties (CoolProp 'NitrousOxide') and two-phase injector flow models (Combustion v1).

Property source: CoolProp 8 NitrousOxide = Lemmon & Span short reference EOS
  (E.W. Lemmon, R. Span, "Short Fundamental Equations of State for 20 Industrial Fluids",
   J. Chem. Eng. Data 51 (2006) 785-850). Validation vs published saturation data: n2o_validation.py.

Injector models (mass flux G = mdot / (Cd*A) unless stated):
  SPI  : G = sqrt(2 rho_l1 (P1 - P2))                      (single-phase incompressible)
  HEM  : G = max_{p in [P2, P1]} rho(p, s1) sqrt(2 (h1 - h(p, s1)))   isentropic, homogeneous
         equilibrium; the max over p captures choking (critical flow) when P2 < p_crit.
  Dyer : G = (kappa/(1+kappa)) G_SPI + (1/(1+kappa)) G_HEM,  kappa = sqrt((P1-P2)/(Pv1-P2))
         J. Dyer, G. Zilliac, A. Sadhwani, A. Karabeyoglu, B. Cantwell, "Modeling Feed System Flow
         Physics for Self-Pressurizing Propellants", AIAA 2007-5702.
         (kappa = ratio of bubble-growth time to liquid residence time; saturated inlet -> kappa = 1.)
Units SI. P in Pa, T in K.
"""
from __future__ import annotations
import numpy as np
import CoolProp.CoolProp as CP
from functools import lru_cache

FLUID = 'NitrousOxide'
T_CRIT = CP.PropsSI('Tcrit', FLUID)
P_CRIT = CP.PropsSI('pcrit', FLUID)
RHO_CRIT = CP.PropsSI('rhocrit', FLUID)
T_TRIPLE = CP.PropsSI('Ttriple', FLUID)

_AS = CP.AbstractState('HEOS', FLUID)


def psat(T):
    _AS.update(CP.QT_INPUTS, 0.0, float(T))
    return _AS.p()


def tsat(P):
    _AS.update(CP.PQ_INPUTS, float(P), 0.0)
    return _AS.T()


def sat_props(T):
    """Saturated liquid and vapour properties at temperature T."""
    out = {}
    _AS.update(CP.QT_INPUTS, 0.0, float(T))
    out['P'] = _AS.p(); out['rho_l'] = _AS.rhomass(); out['h_l'] = _AS.hmass(); out['s_l'] = _AS.smass()
    out['u_l'] = _AS.umass(); out['cp_l'] = _AS.cpmass()
    _AS.update(CP.QT_INPUTS, 1.0, float(T))
    out['rho_v'] = _AS.rhomass(); out['h_v'] = _AS.hmass(); out['s_v'] = _AS.smass(); out['u_v'] = _AS.umass()
    out['cp_v'] = _AS.cpmass()
    out['h_fg'] = out['h_v'] - out['h_l']
    return out


def _state_ps(p, s):
    _AS.update(CP.PSmass_INPUTS, float(p), float(s))
    return _AS.rhomass(), _AS.hmass()


def upstream_state(P1, T1):
    """Upstream liquid state. If P1 >= Psat(T1) the liquid is subcooled (supercharged);
    if P1 is within 0.1 % of Psat the state is taken as saturated liquid (Q=0)."""
    pv = psat(T1)
    if P1 <= pv * 1.001:
        _AS.update(CP.QT_INPUTS, 0.0, float(T1))
        P1 = _AS.p()
    else:
        _AS.update(CP.PT_INPUTS, float(P1), float(T1))
    return dict(P=P1, T=T1, rho=_AS.rhomass(), h=_AS.hmass(), s=_AS.smass(), pv=pv)


def G_spi(P1, T1, P2):
    st = upstream_state(P1, T1)
    return np.sqrt(max(2.0 * st['rho'] * (st['P'] - P2), 0.0))


def G_hem(P1, T1, P2, n=60, return_pcrit=False):
    """HEM mass flux with choking: maximise rho*sqrt(2 dh) over downstream pressure >= P2."""
    st = upstream_state(P1, T1)
    p_hi = min(st['P'], st['pv']) * 0.9999   # flashing starts at the vapour pressure
    if P2 >= p_hi:
        # subcooled liquid that never reaches Pv: single phase
        g = np.sqrt(max(2.0 * st['rho'] * (st['P'] - P2), 0.0))
        return (g, P2) if return_pcrit else g
    ps = np.linspace(max(P2, 0.2e5), p_hi, n)
    best_g, best_p = 0.0, P2
    for p in ps:
        rho2, h2 = _state_ps(p, st['s'])
        dh = st['h'] - h2
        if dh <= 0:
            continue
        g = rho2 * np.sqrt(2.0 * dh)
        if g > best_g:
            best_g, best_p = g, p
    # refine around the maximum (golden section) only if the maximum is interior (choked)
    if best_p > ps[0] + 1e-9:
        a, b = max(P2, best_p - (ps[1] - ps[0])), min(p_hi, best_p + (ps[1] - ps[0]))
        gr = (np.sqrt(5) - 1) / 2
        f = lambda p: -_state_ps(p, st['s'])[0] * np.sqrt(max(2.0 * (st['h'] - _state_ps(p, st['s'])[1]), 0.0))
        c, d = b - gr * (b - a), a + gr * (b - a)
        fc, fd = f(c), f(d)
        for _ in range(30):
            if fc < fd:
                b, d, fd = d, c, fc
                c = b - gr * (b - a); fc = f(c)
            else:
                a, c, fc = c, d, fd
                d = a + gr * (b - a); fd = f(d)
        best_p = 0.5 * (a + b); best_g = -f(best_p)
    return (best_g, best_p) if return_pcrit else best_g


def kappa_dyer(P1, T1, P2):
    st = upstream_state(P1, T1)
    pv = st['pv']
    if pv <= P2:
        return np.inf
    return np.sqrt(max(st['P'] - P2, 0.0) / (pv - P2))


def G_dyer(P1, T1, P2):
    k = kappa_dyer(P1, T1, P2)
    gs = G_spi(P1, T1, P2)
    gh = G_hem(P1, T1, P2)
    if not np.isfinite(k):
        return gs
    return (k / (1 + k)) * gs + (1 / (1 + k)) * gh


def mdot(model, CdA, P1, T1, P2):
    f = dict(spi=G_spi, hem=G_hem, dyer=G_dyer)[model]
    return CdA * f(P1, T1, P2)


if __name__ == '__main__':
    print(f"Tc={T_CRIT:.3f} K Pc={P_CRIT/1e6:.4f} MPa rho_c={RHO_CRIT:.1f}")
    T1 = 293.15
    P1 = psat(T1)
    print(f"saturated at 20 C: P={P1/1e5:.2f} bar")
    for P2 in [40e5, 30e5, 25e5, 15e5, 6e5, 4.5e5, 1e5]:
        print(f"P2={P2/1e5:5.1f} bar  SPI={G_spi(P1,T1,P2):8.0f}  HEM={G_hem(P1,T1,P2):8.0f}  Dyer={G_dyer(P1,T1,P2):8.0f}  kappa={kappa_dyer(P1,T1,P2):.3f}")
    g, pc = G_hem(P1, T1, 1e5, return_pcrit=True)
    print(f"HEM critical (choke) pressure from saturated 20 C: {pc/1e5:.2f} bar, ratio {pc/P1:.3f}")
