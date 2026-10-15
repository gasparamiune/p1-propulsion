"""Engine and tank models for GNC (placeholders until interfaces/combustion.json exists).

Steady throttle map (per step, quasi-steady):
    G_ox  = mdot_ox / (pi D_port^2 / 4)                      [kg/m2/s]
    r     = a * G_ox^n                                        [m/s]   (ASSUMED placeholder law, baseline v0)
    mdot_f= rho_f * pi * D_port * L_grain * r                 [kg/s]
    O/F   = mdot_ox / mdot_f
    Pc    = (mdot_ox + mdot_f) * eta_cstar * c*(Pc, O/F) / A_t  (fixed point)
    F     = (mdot_ox + mdot_f) * g0 * eta_cstar * eta_cf * Isp_SL,CEA(Pc, O/F)
    Isp_SL,CEA includes RocketCEA's separation estimate at low Pc (eps = 3).
Thrust ceiling: pintle fully open, mdot_ox = K_inj * sqrt(P_tank - Pc)  (single-phase
incompressible form; the Dyer two-phase model is Combustion's). K_inj is calibrated so that
F = F_max at the design tank pressure (ASSUMED: Psat(15 C) = 4.50 MPa, ENG-01 '>= 15 C').
Above that pressure the engine is limited to F_max (chamber MEOP).

Tank: homogeneous-equilibrium self-pressurised N2O, liquid drawn from the bottom (settled),
wall heat capacity optionally in thermal equilibrium with the fluid (ASSUMED participation
factor). Energy: d(U_fluid + C_wall T)/dt = -mdot_out * h_l(T).

All numbers carry tags in gncsim/params.py. SI units.
"""
import numpy as np
from numba import njit
from . import tables

G0 = 9.80665

_cea = tables.build_cea_table()
_n2o = tables.build_n2o_table()
CEA_PC = np.ascontiguousarray(_cea["pc_bar"] * 1e5)        # Pa
CEA_OF = np.ascontiguousarray(_cea["of"])
CEA_CSTAR = np.ascontiguousarray(_cea["cstar"])              # m/s, ideal
CEA_ISPSL = np.ascontiguousarray(_cea["isp_sl"])             # s, ideal at SL ambient
CEA_SEP = np.ascontiguousarray(_cea["separated"])
N2O_T = np.ascontiguousarray(_n2o["T"])
N2O_P = np.ascontiguousarray(_n2o["p"])
N2O_RL = np.ascontiguousarray(_n2o["rho_l"])
N2O_RV = np.ascontiguousarray(_n2o["rho_v"])
N2O_UL = np.ascontiguousarray(_n2o["u_l"])
N2O_UV = np.ascontiguousarray(_n2o["u_v"])
N2O_HL = np.ascontiguousarray(_n2o["h_l"])


@njit(cache=True)
def _interp1(xg, yg, x):
    n = xg.shape[0]
    if x <= xg[0]:
        return yg[0]
    if x >= xg[n - 1]:
        return yg[n - 1]
    lo, hi = 0, n - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xg[mid] <= x:
            lo = mid
        else:
            hi = mid
    w = (x - xg[lo]) / (xg[hi] - xg[lo])
    return yg[lo] * (1.0 - w) + yg[hi] * w


@njit(cache=True)
def _bilin(xg, yg, z, x, y):
    # clamp then bilinear interpolation on a regular-or-irregular grid
    nx, ny = xg.shape[0], yg.shape[0]
    if x < xg[0]:
        x = xg[0]
    if x > xg[nx - 1]:
        x = xg[nx - 1]
    if y < yg[0]:
        y = yg[0]
    if y > yg[ny - 1]:
        y = yg[ny - 1]
    i = 0
    while i < nx - 2 and xg[i + 1] < x:
        i += 1
    j = 0
    while j < ny - 2 and yg[j + 1] < y:
        j += 1
    wx = (x - xg[i]) / (xg[i + 1] - xg[i])
    wy = (y - yg[j]) / (yg[j + 1] - yg[j])
    return (z[i, j] * (1 - wx) * (1 - wy) + z[i + 1, j] * wx * (1 - wy)
            + z[i, j + 1] * (1 - wx) * wy + z[i + 1, j + 1] * wx * wy)


@njit(cache=True)
def steady_point(mdot_ox, D_port, At, eta_cs, eta_cf, a_reg, n_reg, rho_f, L_grain, isp_scale):
    """Return (F, mdot_total, mdot_f, Pc, OF, Isp) for a given oxidiser flow and port diameter."""
    if mdot_ox <= 1e-6:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    Ap = np.pi * D_port * D_port / 4.0
    G = mdot_ox / Ap
    r = a_reg * G ** n_reg
    mdot_f = rho_f * np.pi * D_port * L_grain * r
    of = mdot_ox / mdot_f
    mdot = mdot_ox + mdot_f
    pc = 20e5
    for _ in range(30):  # fixed point on Pc (c* depends weakly on Pc)
        cs = eta_cs * _bilin(CEA_PC, CEA_OF, CEA_CSTAR, pc, of)
        pc_new = mdot * cs / At
        if abs(pc_new - pc) < 1.0:
            pc = pc_new
            break
        pc = 0.5 * (pc + pc_new)
    isp = eta_cs * eta_cf * _bilin(CEA_PC, CEA_OF, CEA_ISPSL, pc, of) * isp_scale
    F = mdot * G0 * isp
    return F, mdot, mdot_f, pc, of, isp


@njit(cache=True)
def mdot_ox_for_thrust(F, D_port, At, eta_cs, eta_cf, a_reg, n_reg, rho_f, L_grain, isp_scale):
    """Invert the steady map by bisection: oxidiser flow giving thrust F (monotonic map)."""
    if F <= 0.0:
        return 0.0
    lo, hi = 1e-5, 2.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        f = steady_point(mid, D_port, At, eta_cs, eta_cf, a_reg, n_reg, rho_f, L_grain, isp_scale)[0]
        if f < F:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-7:
            break
    return 0.5 * (lo + hi)


@njit(cache=True)
def thrust_ceiling(P_tank, D_port, K_inj, At, eta_cs, eta_cf, a_reg, n_reg, rho_f, L_grain,
                   isp_scale, F_cap):
    """Max thrust with the pintle fully open at tank pressure P_tank (capped at F_cap)."""
    lo, hi = 0.0, 1.5
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        F, mdot, mf, pc, of, isp = steady_point(mid, D_port, At, eta_cs, eta_cf, a_reg, n_reg,
                                                rho_f, L_grain, isp_scale)
        dp = P_tank - pc
        flow = K_inj * np.sqrt(dp) if dp > 0 else 0.0
        if flow > mid:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-7:
            break
    F = steady_point(0.5 * (lo + hi), D_port, At, eta_cs, eta_cf, a_reg, n_reg, rho_f, L_grain,
                     isp_scale)[0]
    return min(F, F_cap)


# ----------------------------------------------------------------------------- tank
@njit(cache=True)
def sat_props(T):
    return (_interp1(N2O_T, N2O_P, T), _interp1(N2O_T, N2O_RL, T), _interp1(N2O_T, N2O_RV, T),
            _interp1(N2O_T, N2O_UL, T), _interp1(N2O_T, N2O_UV, T), _interp1(N2O_T, N2O_HL, T))


@njit(cache=True)
def tank_solve(m, E, V, C_wall):
    """Equilibrium tank: find T such that fluid internal energy + wall heat = E.
    Returns T, P, m_liquid, m_vapor, h_l."""
    lo, hi = N2O_T[0], N2O_T[N2O_T.shape[0] - 1]
    T = 0.5 * (lo + hi)
    for _ in range(60):
        T = 0.5 * (lo + hi)
        p, rl, rv, ul, uv, hl = sat_props(T)
        v = V / m
        x = (v - 1.0 / rl) / (1.0 / rv - 1.0 / rl)
        if x < 0.0:
            x = 0.0
        if x > 1.0:
            x = 1.0
        e = m * ((1 - x) * ul + x * uv) + C_wall * T
        if e > E:
            hi = T
        else:
            lo = T
        if hi - lo < 1e-6:
            break
    p, rl, rv, ul, uv, hl = sat_props(T)
    v = V / m
    x = (v - 1.0 / rl) / (1.0 / rv - 1.0 / rl)
    if x < 0.0:
        x = 0.0
    if x > 1.0:
        x = 1.0
    return T, p, m * (1 - x), m * x, hl


@njit(cache=True)
def tank_init(m_load, T0, V, C_wall):
    p, rl, rv, ul, uv, hl = sat_props(T0)
    v = V / m_load
    x = (v - 1.0 / rl) / (1.0 / rv - 1.0 / rl)
    if x < 0.0:
        x = 0.0
    E = m_load * ((1 - x) * ul + x * uv) + C_wall * T0
    return E


def tank_fill_check(m_load, T0, V):
    """Python helper: liquid fill fraction at T0 (for sizing checks)."""
    import CoolProp.CoolProp as CP
    rl = CP.PropsSI('D', 'T', T0, 'Q', 0, 'NitrousOxide')
    rv = CP.PropsSI('D', 'T', T0, 'Q', 1, 'NitrousOxide')
    v = V / m_load
    x = (v - 1 / rl) / (1 / rv - 1 / rl)
    Vl = m_load * (1 - x) / rl
    return Vl / V, x
