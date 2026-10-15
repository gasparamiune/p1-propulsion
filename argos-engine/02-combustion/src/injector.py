"""N2O injector flow (Combustion v2): SPI / HEM / Dyer NHNE models with a fast lookup table, pintle area law.

Models (mass flux G = mdot / (Cd A)):
  SPI  : G = sqrt(2 rho_1 (P1 - P2))
  HEM  : G = max_{p >= P2} rho(p, s1) sqrt(2 (h1 - h(p, s1)))     (isentropic homogeneous equilibrium; max = choking)
  Dyer : G = k/(1+k) G_SPI + 1/(1+k) G_HEM,  k = sqrt((P1 - P2)/(Pv(T1) - P2))
         J. Dyer, G. Zilliac, A. Sadhwani, A. Karabeyoglu, B. Cantwell, AIAA 2007-5702.
Upstream state (v2 change): liquid at T1 and P1.  P1 > Pv(T1): compressed (subcooled, e.g. after N2 supercharge);
P1 <= Pv(T1): metastable liquid after the feed-line loss, approximated by saturated-liquid properties at T1
(rho, h, s of the liquid are nearly pressure-independent).  v1 clamped P1 up to Pv (ignored the line loss in the
flux; the operating point was unaffected because the pintle lift absorbed it, ~5 % on the lift-flow map).
Table: G(T1, P1/Pv, P2/P1) on a regular grid; trilinear interpolation (error vs direct evaluation reported by
self-test < 0.5 %).
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import CoolProp.CoolProp as CP
from scipy.interpolate import RegularGridInterpolator

F = 'NitrousOxide'
_AS = CP.AbstractState('HEOS', F)
HERE = os.path.dirname(os.path.abspath(__file__))
TAB_FN = os.path.join(HERE, '..', 'data', 'v2', 'injector_G_table_v2.npz')

T1_GRID = np.arange(258.15, 305.16, 1.25)
R1_GRID = np.array([0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.875, 0.9, 0.925, 0.95, 0.975, 1.0, 1.025, 1.05, 1.1, 1.15, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8])
R2_GRID = np.concatenate([np.linspace(0.04, 0.9, 87), np.linspace(0.905, 0.995, 19)])


def psat(T):
    _AS.update(CP.QT_INPUTS, 0.0, float(T)); return _AS.p()


def inlet(P1, T1):
    pv = psat(T1)
    if P1 > pv * 1.0005:
        _AS.update(CP.PT_INPUTS, float(P1), float(T1))
    else:
        _AS.update(CP.QT_INPUTS, 0.0, float(T1))
    return dict(rho=_AS.rhomass(), h=_AS.hmass(), s=_AS.smass(), pv=pv)


def isentrope(st, n=240, pmin=1.0e5):
    """rho, h along the isentrope s1 from min(P1,Pv) down to pmin (two-phase region)."""
    ps = np.geomspace(pmin, st['pv'] * 0.99995, n)
    rho = np.empty(n); h = np.empty(n)
    for i, p in enumerate(ps):
        _AS.update(CP.PSmass_INPUTS, float(p), st['s'])
        rho[i] = _AS.rhomass(); h[i] = _AS.hmass()
    return ps, rho, h


def g_models(P1, T1, P2s, st=None, ise=None):
    """SPI, HEM, Dyer flux arrays for downstream pressures P2s (direct evaluation)."""
    st = st or inlet(P1, T1)
    ps, rho, h = ise if ise is not None else isentrope(st)
    gh_curve = rho * np.sqrt(np.clip(2 * (st['h'] - h), 0, None))
    P2s = np.atleast_1d(P2s)
    spi = np.sqrt(np.clip(2 * st['rho'] * (P1 - P2s), 0, None))
    hem = np.empty_like(P2s)
    for i, p2 in enumerate(P2s):
        if p2 >= st['pv']:
            hem[i] = np.sqrt(max(2 * st['rho'] * (P1 - p2), 0.0))      # never flashes: single phase
        else:
            m = ps >= p2
            hem[i] = gh_curve[m].max() if m.any() else 0.0
    k = np.where(st['pv'] > P2s, np.sqrt(np.clip((P1 - P2s), 0, None) / np.clip(st['pv'] - P2s, 1e-9, None)), np.inf)
    with np.errstate(invalid="ignore", divide="ignore"):
        dyer = np.where(np.isfinite(k), k / (1 + k) * spi + 1 / (1 + k) * hem, spi)
    return spi, hem, dyer, k


def build_table(fn=TAB_FN):
    G = np.zeros((3, len(T1_GRID), len(R1_GRID), len(R2_GRID)))
    for i, T1 in enumerate(T1_GRID):
        pv = psat(T1)
        for j, r1 in enumerate(R1_GRID):
            P1 = r1 * pv
            st = inlet(P1, T1)
            ise = isentrope(st)
            spi, hem, dyer, k = g_models(P1, T1, R2_GRID * P1, st, ise)
            G[0, i, j] = spi; G[1, i, j] = hem; G[2, i, j] = dyer
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    np.savez_compressed(fn, G=G, T1=T1_GRID, R1=R1_GRID, R2=R2_GRID)
    return fn


class GTable:
    def __init__(self, fn=TAB_FN):
        if not os.path.exists(fn):
            build_table(fn)
        d = np.load(fn)
        self.g = {m: RegularGridInterpolator((d['T1'], d['R1'], d['R2']), d['G'][k], bounds_error=False, fill_value=None)
                  for k, m in enumerate(('spi', 'hem', 'dyer'))}
        self.T1 = d['T1']
        self._pv = np.array([psat(t) for t in self.T1])

    def pv(self, T1):
        return float(np.interp(T1, self.T1, self._pv))

    def G(self, P1, T1, P2, model='dyer'):
        pv = self.pv(T1)
        r1 = P1 / pv; r2 = min(max(P2 / P1, R2_GRID[0]), R2_GRID[-1])
        return float(self.g[model]((T1, r1, r2)))


# ---------------------------------------------------------------------------------------------------------------
# pintle geometry (identical to combustion.json v1: seat 5.5 mm, 15 deg metering cone)
SEAT_D = 0.0055; CONE_HALF = 15.0; STROKE = 0.004


def pintle_area(h, Ds=SEAT_D, alpha_deg=CONE_HALF):
    a = math.radians(alpha_deg)
    h = np.asarray(h, dtype=float)
    s = np.clip(h, 0, None) * math.sin(a)
    A_seat = math.pi * Ds ** 2 / 4
    disc = Ds ** 2 - 4 * math.cos(a) * A_seat / math.pi
    s_star = (Ds - math.sqrt(max(disc, 0.0))) / (2 * math.cos(a))
    A = np.where(s < s_star, math.pi * s * (Ds - s * math.cos(a)), A_seat)
    return float(A) if A.ndim == 0 else A


def pintle_lift(A):
    from scipy.optimize import brentq
    A_seat = math.pi * SEAT_D ** 2 / 4
    if A <= 0:
        return 0.0
    if A >= pintle_area(STROKE) * 0.99999:
        return STROKE
    return brentq(lambda h: pintle_area(h) - A, 0.0, STROKE)


if __name__ == '__main__':
    import time
    t0 = time.time()
    if '--build' in sys.argv or not os.path.exists(TAB_FN):
        print('built', build_table(), f'{time.time()-t0:.1f}s')
    gt = GTable()
    # self-test vs direct evaluation at off-grid points
    rng = np.random.default_rng(1); errs = []
    for _ in range(40):
        T1 = rng.uniform(263, 300); r1 = rng.uniform(0.75, 1.5); P1 = r1 * psat(T1); P2 = rng.uniform(0.05, 0.95) * P1
        d = g_models(P1, T1, np.array([P2]))[2][0]; t = gt.G(P1, T1, P2)
        errs.append(abs(t / d - 1))
    print(f'table vs direct Dyer: max err {100*max(errs):.2f} %, mean {100*np.mean(errs):.3f} %')
