"""plume2s - own 2D axisymmetric two-species nozzle + plume solver (Combustion / 05-plume-cfd, v1, 2026-10-11).

Purpose: independent check of the OpenFOAM rhoCentralFoam runs, and the model that distinguishes exhaust from air.

Equations: axisymmetric compressible Navier-Stokes (Reynolds-averaged, algebraic eddy viscosity in the plume only;
the nozzle interior and walls are inviscid/slip), finite volume on a single logical structured grid with a masked
solid band (nozzle wall + base), cells weighted by r (per radian):  d(U V)/dt = -sum_f F.n A_f + S V.
  U = (rho, rho u, rho v, E, rho Y)   Y = exhaust mass fraction = mixture fraction Z (frozen, non-reacting).
Thermo: two calorically perfect species. Exhaust: (gamma_e, R_e) calibrated on CEA (same calibration as the
OpenFOAM case, make_case.chamber_state); air: gamma 1.4, R 287.05. Mixture cp = Y cp_e + (1-Y) cp_a,
R = Y R_e + (1-Y) R_a (ideal mixing, h = cp T, common zero at 0 K).  'single' mode: every cell uses the exhaust
(gamma_e, R_e), i.e. the OpenFOAM single-gas model, while Y is still carried as a passive scalar.
Fluxes: HLLC (Toro, Riemann Solvers and Numerical Methods for Fluid Dynamics, 3rd ed. 2009, Sec. 10.4) with
Einfeldt/Davis wave-speed bounds; HLLE on faces next to a strong transverse pressure jump (Quirk 1994 type
carbuncle cure); MUSCL on primitive variables with the van Leer limiter in index space; SSP-RK2 (Heun) in time.
Axisymmetric source: radial momentum (p - tau_thth) * A_quad (exact for uniform pressure with r_mid face areas).
Turbulence (plume region, option): uniform exchange coefficient per axial station (Prandtl's second hypothesis),
  see eddy_viscosity(): mixing-layer value from the incompressible vorticity-thickness growth 0.18 (Brown & Roshko 1974),
  developed-jet value nu_t = 0.028 dU r_1/2 (Pope 2000), compressibility factor Phi(Mc) = 0.23 + 0.77 exp(-3.4 Mc^2)
  (fit to the 'Langley curve', attributed to Dimotakis 1991), Pr_t = Sc_t = 0.7 (ASSUMED, free-shear range 0.5-0.9).
  All constants LITERATURE-UNVERIFIED (quoted from memory); sensitivity runs with x0.5 / x2 viscosity are reported.
  [v1 first attempt: Prandtl mixing length l = 0.071 delta |omega| per column -> column-to-column delta jumps gave
  spotty mu_t up to 1.5 Pa s and destroyed the jet under local time stepping: kept as FAILURE-CFD-02 in REPORT.md]
Hypotheses that limit what this model can show: no chemistry in the flow (afterburning is a post-processed
fast-chemistry estimate), no soot, no radiation, no turbulence-chemistry interaction, no nozzle boundary layer
(no viscous separation prediction), perfect-gas exhaust with frozen calibrated gamma.
"""
from __future__ import annotations
import json, math, os, sys, time
import numpy as np
from numba import njit

G = 2           # ghost layers
GA, RA = 1.4, 287.05
PA, TA = 101325.0, 288.15


# ----------------------------------------------------------------------------------------------- grid
def geometric(n, L, d0):
    """Growth ratio g so that n cells starting at d0 span L."""
    from scipy.optimize import brentq
    if abs(L / n - d0) < 1e-12:
        return 1.0
    f = lambda g: d0 * (g ** n - 1) / (g - 1) - L
    return brentq(f, 1.0 + 1e-9, 2.0) if L / n > d0 else brentq(f, 0.3, 1 - 1e-9)


class Grid:
    """Logical structured grid; level factor f = 0.5 (coarse), 1 (medium), 2 (fine); vertices are nested."""
    BASE = dict(n_conv=32, n_div=32, n_core=40, n_shear=32, n_outer=80, n_amb=48, dx0=0.325e-3, g_pl=1.006)

    def __init__(self, contour, Rbody, level=1.0, X_DOWN=45.0, R_OUT=12.0, X_UP=4.0, AR_IN=2.56):
        B = self.BASE
        f = level
        pts = np.asarray(contour)
        i_t = int(np.argmin(pts[:, 1]))
        Rt = pts[i_t, 1]; Re = pts[-1, 1]; De = 2 * Re
        xs = pts[:, 0] - pts[-1, 0]             # exit plane at x = 0
        r_in = math.sqrt(AR_IN) * Rt
        up_r = pts[:i_t + 1, 1]; up_x = xs[:i_t + 1]
        k = np.where(up_r <= r_in)[0][0]
        x_in = float(np.interp(r_in, [up_r[k], up_r[k - 1]], [up_x[k], up_x[k - 1]]))
        x_t = xs[i_t]
        self.Rt, self.Re, self.De, self.x_in, self.x_t, self.r_in, self.Rbody = Rt, Re, De, x_in, x_t, r_in, Rbody
        self.level = f
        wall_x = xs; wall_r = pts[:, 1]
        def Rw(x):
            return np.interp(x, wall_x, wall_r)
        # --- counts at this level (medium counts * f)
        def cnt(n):
            m = n * f
            assert abs(m - round(m)) < 1e-9, 'level factor must give integer counts'
            return int(round(m))
        nc, nd, ncore, nsh, nout, namb = (cnt(B['n_conv']), cnt(B['n_div']), cnt(B['n_core']), cnt(B['n_shear']),
                                          cnt(B['n_outer']), cnt(B['n_amb']))
        # nozzle axial positions: parametric in medium index s (cosine clustering toward the throat on both sides)
        def x_noz(s):
            s = np.asarray(s, float)
            out = np.empty_like(s)
            a = s <= B['n_conv']
            t = s[a] / B['n_conv']                                       # 0..1 inlet->throat
            out[a] = x_in + (x_t - x_in) * (0.6 * t + 0.4 * np.sin(0.5 * np.pi * t))   # throat cells ~0.5x inlet cells
            t = (s[~a] - B['n_conv']) / B['n_div']                       # 0..1 throat->exit
            out[~a] = x_t + (0.0 - x_t) * (0.35 * (1 - np.cos(0.5 * np.pi * t)) + 0.65 * t)
            return out
        Nn_m = B['n_conv'] + B['n_div']
        s_noz = np.arange(0, Nn_m * f + 1) / f
        Xn = x_noz(s_noz)
        Nn = len(Xn) - 1
        # ambient beside the body: x from x_b to 0 with n_amb (medium) cells, clustered at x = 0
        x_b = -X_UP * De
        # we need the same number of i-cells as the nozzle block -> Nn cells; geometric toward 0
        d_end = (Xn[-1] - Xn[-2])
        s_amb = np.arange(0, Nn + 1)
        g_a = geometric(Nn, -x_b, max(d_end, 1e-5))
        Xa = -(d_end * (g_a ** (Nn - s_amb) - 1) / (g_a - 1))
        Xa[0] = x_b; Xa[-1] = 0.0
        # plume axial: geometric in medium index
        L = X_DOWN * De
        g = B['g_pl']; dx0 = B['dx0']
        Np_m = int(math.ceil(math.log(1 + L * (g - 1) / dx0) / math.log(g)))
        Np_m += Np_m % 2
        if f > 1:
            Np_m = int(math.ceil(Np_m / 2) * 2)
        s_pl = np.arange(0, Np_m * f + 1) / f
        Xp = dx0 * (g ** s_pl - 1) / (g - 1)
        Xp *= L / Xp[-1]
        Np = len(Xp) - 1
        # radial (plume / ambient)
        r_core = Re * np.arange(0, B['n_core'] * f + 1) / (B['n_core'] * f)
        r_sh = Re + (Rbody - Re) * np.arange(0, B['n_shear'] * f + 1) / (B['n_shear'] * f)
        R_out = R_OUT * De
        d_sh_m = (Rbody - Re) / B['n_shear']
        g_o = geometric(B['n_outer'], R_out - Rbody, d_sh_m)
        s_o = np.arange(0, B['n_outer'] * f + 1) / f
        r_out = Rbody + d_sh_m * (g_o ** s_o - 1) / (g_o - 1)
        r_out[-1] = R_out
        Rp = np.concatenate([r_core, r_sh[1:], r_out[1:]])
        NI = Nn + Np; NJ = len(Rp) - 1
        jc, js = ncore, ncore + nsh                  # first solid j, first ambient j (for i < Nn)
        X = np.zeros((NI + 1, NJ + 1)); R = np.zeros((NI + 1, NJ + 1))
        for i in range(Nn + 1):
            xw = Xn[i]; rw = Rw(xw)
            for j in range(jc + 1):
                X[i, j] = xw; R[i, j] = rw * j / jc
            for j in range(js, NJ + 1):
                X[i, j] = Xa[i]; R[i, j] = Rp[j]
            for j in range(jc + 1, js):              # solid band (never used for fluxes)
                t = (j - jc) / (js - jc)
                X[i, j] = (1 - t) * xw + t * Xa[i]; R[i, j] = (1 - t) * rw + t * Rp[js]
        X[Nn, :] = 0.0; R[Nn, :] = Rp                # exit plane: core vertices coincide (uniform in [0, Re])
        for i in range(Nn + 1, NI + 1):
            X[i, :] = Xp[i - Nn]; R[i, :] = Rp
        self.X, self.R = X, R
        self.NI, self.NJ, self.Nn, self.jc, self.js = NI, NJ, Nn, jc, js
        mask = np.zeros((NI + 2 * G, NJ + 2 * G), np.int8)
        mask[:G, :] = 2; mask[-G:, :] = 2; mask[:, :G] = 2; mask[:, -G:] = 2
        mask[G:G + Nn, G + jc:G + js] = 1
        self.mask = mask
        region = np.ones((NI, NJ), np.int8)          # 1 plume
        region[:Nn, :jc] = 0                         # nozzle
        region[:Nn, jc:js] = 3                       # solid
        region[:Nn, js:] = 2                         # ambient beside body
        self.region = region
        self._metrics()

    def _metrics(self):
        X, R = self.X, self.R
        NI, NJ = self.NI, self.NJ
        # i-faces: edge (i,j)->(i,j+1); normal toward +i
        ex = X[:, 1:] - X[:, :-1]; er = R[:, 1:] - R[:, :-1]
        L = np.hypot(ex, er); L[L == 0] = 1e-30
        self.nxI = er / L; self.nrI = -ex / L; self.LI = L
        self.AI = L * 0.5 * (R[:, 1:] + R[:, :-1])
        # j-faces: edge (i,j)->(i+1,j); normal toward +j
        ex = X[1:, :] - X[:-1, :]; er = R[1:, :] - R[:-1, :]
        L = np.hypot(ex, er); L[L == 0] = 1e-30
        self.nxJ = -er / L; self.nrJ = ex / L; self.LJ = L
        self.AJ = L * 0.5 * (R[1:, :] + R[:-1, :])
        # cells (quad vertices a=(i,j) b=(i+1,j) c=(i+1,j+1) d=(i,j+1))
        xa, ra = X[:-1, :-1], R[:-1, :-1]; xb, rb = X[1:, :-1], R[1:, :-1]
        xc_, rc_ = X[1:, 1:], R[1:, 1:]; xd, rd = X[:-1, 1:], R[:-1, 1:]
        A = 0.5 * ((xa * rb - xb * ra) + (xb * rc_ - xc_ * rb) + (xc_ * rd - xd * rc_) + (xd * ra - xa * rd))
        # polygon centroid
        def cr(x1, r1, x2, r2):
            return (r1 + r2) * (x1 * r2 - x2 * r1)
        def cx(x1, r1, x2, r2):
            return (x1 + x2) * (x1 * r2 - x2 * r1)
        Asafe = np.where(np.abs(A) > 1e-30, A, 1e-30)
        rcen = (cr(xa, ra, xb, rb) + cr(xb, rb, xc_, rc_) + cr(xc_, rc_, xd, rd) + cr(xd, rd, xa, ra)) / (6 * Asafe)
        xcen = (cx(xa, ra, xb, rb) + cx(xb, rb, xc_, rc_) + cx(xc_, rc_, xd, rd) + cx(xd, rd, xa, ra)) / (6 * Asafe)
        self.Aq = A; self.xc = xcen; self.rc = rcen; self.V = A * rcen
        # characteristic lengths (distance between opposite face midpoints)
        mxI = 0.5 * (X[:, 1:] + X[:, :-1]); mrI = 0.5 * (R[:, 1:] + R[:, :-1])
        self.dI = np.hypot(mxI[1:] - mxI[:-1], mrI[1:] - mrI[:-1])
        mxJ = 0.5 * (X[1:, :] + X[:-1, :]); mrJ = 0.5 * (R[1:, :] + R[:-1, :])
        self.dJ = np.hypot(mxJ[:, 1:] - mxJ[:, :-1], mrJ[:, 1:] - mrJ[:, :-1])
        fl = self.region != 3
        assert np.all(A[fl] > 0), 'negative/zero cell area in fluid region'

    def summary(self):
        return dict(NI=self.NI, NJ=self.NJ, cells=int((self.region != 3).sum()), Nn=self.Nn, jc=self.jc, js=self.js,
                    De=self.De, Rt=self.Rt, Re=self.Re, x_in=self.x_in, x_t=self.x_t, Rbody=self.Rbody,
                    L_down=float(self.X[-1, 0]), R_out=float(self.R[0, -1]), min_dI=float(self.dI[self.region != 3].min()),
                    min_dJ=float(self.dJ[self.region != 3].min()))


# ----------------------------------------------------------------------------------------------- kernels
@njit(cache=True, error_model="numpy")
def _props(Y, cpe, Re_, single):
    if single:
        return cpe, Re_
    y = min(max(Y, 0.0), 1.0)
    cpa = GA * RA / (GA - 1.0)
    return y * cpe + (1.0 - y) * cpa, y * Re_ + (1.0 - y) * RA


@njit(cache=True, error_model="numpy")
def prim_to_cons(rho, u, v, p, Y, cpe, Re_, single, out):
    cp, R = _props(Y, cpe, Re_, single)
    cv = cp - R
    T = p / (rho * R)
    out[0] = rho; out[1] = rho * u; out[2] = rho * v
    out[3] = rho * (cv * T + 0.5 * (u * u + v * v)); out[4] = rho * Y


@njit(cache=True, error_model="numpy")
def cons2prim(U, W, Tg, Gam, mask, cpe, Re_, single):
    NIg, NJg = U.shape[0], U.shape[1]
    nbad = 0
    for i in range(NIg):
        for j in range(NJg):
            rho = U[i, j, 0]
            if rho < 1e-6:
                rho = 1e-6; U[i, j, 0] = rho; nbad += 1
            u = U[i, j, 1] / rho; v = U[i, j, 2] / rho
            Y = U[i, j, 4] / rho
            if Y < 0.0:
                Y = 0.0; U[i, j, 4] = 0.0
            elif Y > 1.0:
                Y = 1.0; U[i, j, 4] = rho
            cp, R = _props(Y, cpe, Re_, single)
            cv = cp - R
            e = U[i, j, 3] / rho - 0.5 * (u * u + v * v)
            T = e / cv
            if T < 20.0:
                T = 20.0; U[i, j, 3] = rho * (cv * T + 0.5 * (u * u + v * v)); nbad += 1
            W[i, j, 0] = rho; W[i, j, 1] = u; W[i, j, 2] = v; W[i, j, 3] = rho * R * T; W[i, j, 4] = Y
            Tg[i, j] = T; Gam[i, j] = cp / cv
    return nbad


@njit(cache=True, error_model="numpy")
def _lim(a, b):
    # van Leer
    if a * b <= 0.0:
        return 0.0
    return 2.0 * a * b / (a + b)


@njit(cache=True, error_model="numpy")
def _flux(rL, uL, vL, pL, YL, gL, rR, uR, vR, pR, YR, gR, nx, nr, hll, F):
    """HLLC (hll=False) or HLLE (hll=True) flux per unit area across a face with unit normal (nx, nr)."""
    unL = uL * nx + vL * nr; utL = -uL * nr + vL * nx
    unR = uR * nx + vR * nr; utR = -uR * nr + vR * nx
    cL = math.sqrt(gL * pL / rL); cR = math.sqrt(gR * pR / rR)
    EL = pL / (gL - 1.0) + 0.5 * rL * (uL * uL + vL * vL)
    ER = pR / (gR - 1.0) + 0.5 * rR * (uR * uR + vR * vR)
    # Einfeldt (Roe-averaged) bounds
    sL = math.sqrt(rL); sR = math.sqrt(rR)
    ub = (sL * unL + sR * unR) / (sL + sR)
    HL = (EL + pL) / rL; HR = (ER + pR) / rR
    Hb = (sL * HL + sR * HR) / (sL + sR)
    utb = (sL * utL + sR * utR) / (sL + sR)
    gb = 0.5 * (gL + gR)
    c2 = (gb - 1.0) * (Hb - 0.5 * (ub * ub + utb * utb))
    cb = math.sqrt(c2) if c2 > 0 else 0.5 * (cL + cR)
    SL = min(unL - cL, ub - cb); SR = max(unR + cR, ub + cb)
    # physical fluxes (normal frame)
    fL0 = rL * unL; fL1 = rL * unL * unL + pL; fL2 = rL * unL * utL; fL3 = (EL + pL) * unL; fL4 = rL * unL * YL
    fR0 = rR * unR; fR1 = rR * unR * unR + pR; fR2 = rR * unR * utR; fR3 = (ER + pR) * unR; fR4 = rR * unR * YR
    if SL >= 0.0:
        f0, f1, f2, f3, f4 = fL0, fL1, fL2, fL3, fL4
    elif SR <= 0.0:
        f0, f1, f2, f3, f4 = fR0, fR1, fR2, fR3, fR4
    elif hll:
        d = 1.0 / (SR - SL)
        f0 = (SR * fL0 - SL * fR0 + SL * SR * (rR - rL)) * d
        f1 = (SR * fL1 - SL * fR1 + SL * SR * (rR * unR - rL * unL)) * d
        f2 = (SR * fL2 - SL * fR2 + SL * SR * (rR * utR - rL * utL)) * d
        f3 = (SR * fL3 - SL * fR3 + SL * SR * (ER - EL)) * d
        f4 = (SR * fL4 - SL * fR4 + SL * SR * (rR * YR - rL * YL)) * d
    else:
        Ss = (pR - pL + rL * unL * (SL - unL) - rR * unR * (SR - unR)) / (rL * (SL - unL) - rR * (SR - unR))
        if not (SL < Ss < SR):
            d = 1.0 / (SR - SL)
            f0 = (SR * fL0 - SL * fR0 + SL * SR * (rR - rL)) * d
            f1 = (SR * fL1 - SL * fR1 + SL * SR * (rR * unR - rL * unL)) * d
            f2 = (SR * fL2 - SL * fR2 + SL * SR * (rR * utR - rL * utL)) * d
            f3 = (SR * fL3 - SL * fR3 + SL * SR * (ER - EL)) * d
            f4 = (SR * fL4 - SL * fR4 + SL * SR * (rR * YR - rL * YL)) * d
        elif Ss >= 0.0:
            k = rL * (SL - unL) / (SL - Ss)
            u0 = k; u1 = k * Ss; u2 = k * utL
            u3 = k * (EL / rL + (Ss - unL) * (Ss + pL / (rL * (SL - unL)))); u4 = k * YL
            f0 = fL0 + SL * (u0 - rL); f1 = fL1 + SL * (u1 - rL * unL); f2 = fL2 + SL * (u2 - rL * utL)
            f3 = fL3 + SL * (u3 - EL); f4 = fL4 + SL * (u4 - rL * YL)
        else:
            k = rR * (SR - unR) / (SR - Ss)
            u0 = k; u1 = k * Ss; u2 = k * utR
            u3 = k * (ER / rR + (Ss - unR) * (Ss + pR / (rR * (SR - unR)))); u4 = k * YR
            f0 = fR0 + SR * (u0 - rR); f1 = fR1 + SR * (u1 - rR * unR); f2 = fR2 + SR * (u2 - rR * utR)
            f3 = fR3 + SR * (u3 - ER); f4 = fR4 + SR * (u4 - rR * YR)
    F[0] = f0; F[1] = f1 * nx - f2 * nr; F[2] = f1 * nr + f2 * nx; F[3] = f3; F[4] = f4


@njit(cache=True, error_model="numpy")
def _gamma_of(Y, cpe, Re_, single):
    cp, R = _props(Y, cpe, Re_, single)
    return cp / (cp - R)


@njit(cache=True, error_model="numpy")
def convective_residual(W, Gam, mask, nxI, nrI, AI, nxJ, nrJ, AJ, Aq, cpe, Re_, single, order, res):
    """res[i,j,:] (interior indexing, no ghosts) = -sum of convective fluxes*area + pressure hoop source."""
    NI = res.shape[0]; NJ = res.shape[1]
    for i in range(NI):
        for j in range(NJ):
            for k in range(5):
                res[i, j, k] = 0.0
    F = np.zeros(5)
    WL = np.zeros(5); WR = np.zeros(5)
    # ---- i-faces
    for f in range(NI + 1):
        ia = f - 1 + G; ib = f + G
        for j in range(NJ):
            jj = j + G
            mL = mask[ia, jj]; mR = mask[ib, jj]
            A = AI[f, j]
            if A <= 0.0:
                continue
            nx = nxI[f, j]; nr = nrI[f, j]
            if (mL == 1 and mR == 0) or (mL == 0 and mR == 1):
                # slip wall: linearised reflective Riemann pressure
                if mL == 0:
                    c = ia; sgn = 1.0
                else:
                    c = ib; sgn = -1.0
                rho = W[c, jj, 0]; un = sgn * (W[c, jj, 1] * nx + W[c, jj, 2] * nr); p = W[c, jj, 3]
                cs = math.sqrt(Gam[c, jj] * p / rho)
                ps = p + rho * un * (abs(un) + cs + un) if un > 0 else p + rho * un * cs
                if ps < 0.05 * p:
                    ps = 0.05 * p
                if mL == 0:
                    res[f - 1, j, 1] -= ps * nx * A; res[f - 1, j, 2] -= ps * nr * A
                else:
                    res[f, j, 1] += ps * nx * A; res[f, j, 2] += ps * nr * A
                continue
            if mL == 1 or mR == 1 or (mL == 2 and mR == 2):
                continue
            # MUSCL
            for k in range(5):
                wa = W[ia, jj, k]; wb = W[ib, jj, k]
                sa = 0.0; sb = 0.0
                if order == 2:
                    if mask[ia - 1, jj] != 1:
                        sa = _lim(wa - W[ia - 1, jj, k], wb - wa)
                    if mask[ib + 1, jj] != 1:
                        sb = _lim(wb - wa, W[ib + 1, jj, k] - wb)
                WL[k] = wa + 0.5 * sa; WR[k] = wb - 0.5 * sb
            if WL[0] <= 0.0 or WL[3] <= 0.0 or WR[0] <= 0.0 or WR[3] <= 0.0:
                for k in range(5):
                    WL[k] = W[ia, jj, k]; WR[k] = W[ib, jj, k]
            # carbuncle sensor: strong pressure variation across the face's transverse direction
            hll = False
            for c in (ia, ib):
                pm = W[c, jj - 1, 3]; pp = W[c, jj + 1, 3]
                if abs(pp - pm) > 0.5 * min(pp, pm) and (pp - pm) * W[c, jj, 2] > 0.0:
                    hll = True
            gL = _gamma_of(WL[4], cpe, Re_, single); gR = _gamma_of(WR[4], cpe, Re_, single)
            _flux(WL[0], WL[1], WL[2], WL[3], WL[4], gL, WR[0], WR[1], WR[2], WR[3], WR[4], gR, nx, nr, hll, F)
            if f - 1 >= 0 and mL == 0:
                for k in range(5):
                    res[f - 1, j, k] -= F[k] * A
            if f < NI and mR == 0:
                for k in range(5):
                    res[f, j, k] += F[k] * A
    # ---- j-faces
    for i in range(NI):
        ii = i + G
        for f in range(NJ + 1):
            ja = f - 1 + G; jb = f + G
            A = AJ[i, f]
            if A <= 0.0:
                continue
            mL = mask[ii, ja]; mR = mask[ii, jb]
            nx = nxJ[i, f]; nr = nrJ[i, f]
            if (mL == 1 and mR == 0) or (mL == 0 and mR == 1):
                if mL == 0:
                    c = ja; sgn = 1.0
                else:
                    c = jb; sgn = -1.0
                rho = W[ii, c, 0]; un = sgn * (W[ii, c, 1] * nx + W[ii, c, 2] * nr); p = W[ii, c, 3]
                cs = math.sqrt(Gam[ii, c] * p / rho)
                ps = p + rho * un * (abs(un) + cs + un) if un > 0 else p + rho * un * cs
                if ps < 0.05 * p:
                    ps = 0.05 * p
                if mL == 0:
                    res[i, f - 1, 1] -= ps * nx * A; res[i, f - 1, 2] -= ps * nr * A
                else:
                    res[i, f, 1] += ps * nx * A; res[i, f, 2] += ps * nr * A
                continue
            if mL == 1 or mR == 1 or (mL == 2 and mR == 2):
                continue
            for k in range(5):
                wa = W[ii, ja, k]; wb = W[ii, jb, k]
                sa = 0.0; sb = 0.0
                if order == 2:
                    if mask[ii, ja - 1] != 1:
                        sa = _lim(wa - W[ii, ja - 1, k], wb - wa)
                    if mask[ii, jb + 1] != 1:
                        sb = _lim(wb - wa, W[ii, jb + 1, k] - wb)
                WL[k] = wa + 0.5 * sa; WR[k] = wb - 0.5 * sb
            if WL[0] <= 0.0 or WL[3] <= 0.0 or WR[0] <= 0.0 or WR[3] <= 0.0:
                for k in range(5):
                    WL[k] = W[ii, ja, k]; WR[k] = W[ii, jb, k]
            hll = False
            for c in (ja, jb):
                pm = W[ii - 1, c, 3]; pp = W[ii + 1, c, 3]
                if abs(pp - pm) > 0.5 * min(pp, pm) and (pp - pm) * W[ii, c, 1] > 0.0:
                    hll = True
            gL = _gamma_of(WL[4], cpe, Re_, single); gR = _gamma_of(WR[4], cpe, Re_, single)
            _flux(WL[0], WL[1], WL[2], WL[3], WL[4], gL, WR[0], WR[1], WR[2], WR[3], WR[4], gR, nx, nr, hll, F)
            if f - 1 >= 0 and mL == 0:
                for k in range(5):
                    res[i, f - 1, k] -= F[k] * A
            if f < NJ and mR == 0:
                for k in range(5):
                    res[i, f, k] += F[k] * A
    # ---- axisymmetric pressure source (radial momentum)
    for i in range(NI):
        for j in range(NJ):
            if mask[i + G, j + G] == 0:
                res[i, j, 2] += W[i + G, j + G, 3] * Aq[i, j]


@njit(cache=True, error_model="numpy")
def cell_gradients(W, Tg, mask, nxI, nrI, LI, nxJ, nrJ, LJ, Aq, grad):
    """Planar Green-Gauss gradients of (u, v, T, Y) at fluid cells; grad[i,j,q,0:2] = (d/dx, d/dr)."""
    NI = Aq.shape[0]; NJ = Aq.shape[1]
    for i in range(NI):
        for j in range(NJ):
            ii = i + G; jj = j + G
            for q in range(4):
                grad[i, j, q, 0] = 0.0; grad[i, j, q, 1] = 0.0
            if mask[ii, jj] != 0:
                continue
            # four faces: (neighbour index, normal sign, face arrays)
            for side in range(4):
                if side == 0:
                    ni, nj = ii - 1, jj; nx = -nxI[i, j]; nr = -nrI[i, j]; L = LI[i, j]
                elif side == 1:
                    ni, nj = ii + 1, jj; nx = nxI[i + 1, j]; nr = nrI[i + 1, j]; L = LI[i + 1, j]
                elif side == 2:
                    ni, nj = ii, jj - 1; nx = -nxJ[i, j]; nr = -nrJ[i, j]; L = LJ[i, j]
                else:
                    ni, nj = ii, jj + 1; nx = nxJ[i, j + 1]; nr = nrJ[i, j + 1]; L = LJ[i, j + 1]
                solid = mask[ni, nj] == 1
                for q in range(4):
                    if q == 0:
                        a = W[ii, jj, 1]; b = a if solid else W[ni, nj, 1]
                    elif q == 1:
                        a = W[ii, jj, 2]; b = a if solid else W[ni, nj, 2]
                    elif q == 2:
                        a = Tg[ii, jj]; b = a if solid else Tg[ni, nj]
                    else:
                        a = W[ii, jj, 4]; b = a if solid else W[ni, nj, 4]
                    fv = 0.5 * (a + b)
                    grad[i, j, q, 0] += fv * nx * L
                    grad[i, j, q, 1] += fv * nr * L
            for q in range(4):
                grad[i, j, q, 0] /= Aq[i, j]; grad[i, j, q, 1] /= Aq[i, j]


@njit(cache=True, error_model="numpy")
def eddy_viscosity(W, Gam, grad, region, rc, Nn, Cl, use_phi, mut):
    """Uniform-exchange-coefficient (Prandtl 1942 'second hypothesis') eddy viscosity per axial station of the plume.
    Column quantities: dU = u_max - u_amb, vorticity thickness d_w = dU / max|du/dr|, half-velocity radius r_half.
      mixing-layer regime: nu_ml = k_ml * d_w * dU,   k_ml = 0.18/(8 pi) = 0.0072 from the incompressible single-stream
        vorticity-thickness growth d(d_w)/dx ~ 0.18 (Brown & Roshko 1974) for an erf profile with U_conv = dU/2;
      developed round jet: nu_j = 0.028 * dU * r_half (Pope 2000, Turbulent Flows, uniform-viscosity fit for the round jet);
      blend w = min(1, d_w / (1.4 r_half)) (1.4 r_half = d_w of a Gaussian jet profile);
      nu_t = Cl/0.071 * Phi(Mc) * [(1-w) nu_ml + w nu_j],  Phi = 0.23 + 0.77 exp(-3.4 Mc^2), Mc = dU/(c_jet + c_amb);
    applied uniformly across the jet with a taper chi = clip((u - u_amb)/(0.05 dU), 0, 1); smoothed 1-2-1 along x twice.
    mu_t = rho * nu_t.  (Cl is kept as a multiplier for sensitivity runs: Cl = 0.071 -> factor 1.)"""
    NI = mut.shape[0]; NJ = mut.shape[1]
    for i in range(NI):
        for j in range(NJ):
            mut[i, j] = 0.0
    ncol = NI - Nn
    nu = np.zeros(ncol); dUc = np.zeros(ncol); uac = np.zeros(ncol)
    for k in range(ncol):
        i = Nn + k; ii = i + G
        jm = 0; um = -1e30
        for j in range(NJ):
            u = W[ii, j + G, 1]
            if u > um:
                um = u; jm = j
        ua = W[ii, NJ - 1 + G, 1]
        du = um - ua
        uac[k] = ua; dUc[k] = du
        if du < 20.0:
            continue
        # max |du/dr| outboard of the velocity maximum (outer shear layer)
        gmax = 1e-12
        for j in range(jm, NJ):
            gr = abs(grad[i, j, 0, 1])
            if gr > gmax:
                gmax = gr
        dw = du / gmax
        # half-velocity radius (outermost crossing of 0.5 dU)
        rh = rc[i, jm]
        for j in range(NJ - 1, jm, -1):
            if W[ii, j + G, 1] - ua >= 0.5 * du:
                rh = rc[i, j]; break
        if rh < 1e-6:
            rh = 1e-6
        w = dw / (1.4 * rh)
        if w > 1.0:
            w = 1.0
        nml = 0.0072 * dw * du
        nj = 0.028 * du * rh
        phi = 1.0
        if use_phi:
            cj = math.sqrt(Gam[ii, jm + G] * W[ii, jm + G, 3] / W[ii, jm + G, 0])
            ca = math.sqrt(Gam[ii, NJ - 1 + G] * W[ii, NJ - 1 + G, 3] / W[ii, NJ - 1 + G, 0])
            Mc = du / (cj + ca)
            phi = 0.23 + 0.77 * math.exp(-3.4 * Mc * Mc)
        nu[k] = (Cl / 0.071) * phi * ((1.0 - w) * nml + w * nj)
    # smoothing along x (1-2-1, twice)
    for rep in range(2):
        tmp = nu.copy()
        for k in range(1, ncol - 1):
            nu[k] = 0.25 * tmp[k - 1] + 0.5 * tmp[k] + 0.25 * tmp[k + 1]
    for k in range(ncol):
        if nu[k] <= 0.0 or dUc[k] < 20.0:
            continue
        i = Nn + k; ii = i + G
        for j in range(NJ):
            chi = (W[ii, j + G, 1] - uac[k]) / (0.05 * dUc[k])
            if chi <= 0.0:
                continue
            if chi > 1.0:
                chi = 1.0
            mut[i, j] = W[ii, j + G, 0] * nu[k] * chi


@njit(cache=True, error_model="numpy")
def viscous_residual(W, Tg, mask, grad, mut, nxI, nrI, AI, nxJ, nrJ, AJ, Aq, rc, cpe, Re_, single, Prt, Sct, res):
    """Adds turbulent (eddy-viscosity) diffusive fluxes and the hoop-stress source; fluid-fluid faces only."""
    NI = Aq.shape[0]; NJ = Aq.shape[1]
    cpa = GA * RA / (GA - 1.0)
    g = np.empty((4, 2))
    for dirn in range(2):
        nf_i = NI + 1 if dirn == 0 else NI
        nf_j = NJ if dirn == 0 else NJ + 1
        for fi in range(nf_i):
            for fj in range(nf_j):
                if dirn == 0:
                    a_i, a_j, b_i, b_j = fi - 1, fj, fi, fj
                    A = AI[fi, fj]; nx = nxI[fi, fj]; nr = nrI[fi, fj]
                else:
                    a_i, a_j, b_i, b_j = fi, fj - 1, fi, fj
                    A = AJ[fi, fj]; nx = nxJ[fi, fj]; nr = nrJ[fi, fj]
                if A <= 0.0:
                    continue
                if a_i < 0 or b_i >= NI or a_j < 0 or b_j >= NJ:
                    continue      # no turbulent flux through domain boundaries
                if mask[a_i + G, a_j + G] != 0 or mask[b_i + G, b_j + G] != 0:
                    continue
                mu = 0.5 * (mut[a_i, a_j] + mut[b_i, b_j])
                if mu <= 0.0:
                    continue
                for q in range(4):
                    for d in range(2):
                        g[q, d] = 0.5 * (grad[a_i, a_j, q, d] + grad[b_i, b_j, q, d])
                uf = 0.5 * (W[a_i + G, a_j + G, 1] + W[b_i + G, b_j + G, 1])
                vf = 0.5 * (W[a_i + G, a_j + G, 2] + W[b_i + G, b_j + G, 2])
                Yf = 0.5 * (W[a_i + G, a_j + G, 4] + W[b_i + G, b_j + G, 4])
                Tf = 0.5 * (Tg[a_i + G, a_j + G] + Tg[b_i + G, b_j + G])
                rf = 0.5 * (rc[a_i, a_j] + rc[b_i, b_j])
                div = g[0, 0] + g[1, 1] + (vf / rf if rf > 1e-12 else 0.0)
                txx = mu * (2 * g[0, 0] - 2.0 / 3.0 * div)
                trr = mu * (2 * g[1, 1] - 2.0 / 3.0 * div)
                txr = mu * (g[0, 1] + g[1, 0])
                cp, R = _props(Yf, cpe, Re_, single)
                kt = mu * cp / Prt
                rD = mu / Sct
                dTn = g[2, 0] * nx + g[2, 1] * nr
                dYn = g[3, 0] * nx + g[3, 1] * nr
                dh = 0.0 if single else (cpe - cpa) * Tf       # h_e - h_a at the face
                Fx = txx * nx + txr * nr
                Fr = txr * nx + trr * nr
                Fe = uf * Fx + vf * Fr + kt * dTn + dh * rD * dYn
                Fy = rD * dYn
                # diffusive flux leaves a toward b with sign -(...); residual = +F*A to a, -F*A to b
                res[a_i, a_j, 1] += Fx * A; res[a_i, a_j, 2] += Fr * A; res[a_i, a_j, 3] += Fe * A; res[a_i, a_j, 4] += Fy * A
                res[b_i, b_j, 1] -= Fx * A; res[b_i, b_j, 2] -= Fr * A; res[b_i, b_j, 3] -= Fe * A; res[b_i, b_j, 4] -= Fy * A
    # hoop stress source: -tau_thth * Aq
    for i in range(NI):
        for j in range(NJ):
            if mask[i + G, j + G] != 0 or mut[i, j] <= 0.0:
                continue
            v = W[i + G, j + G, 2]; r = rc[i, j]
            div = grad[i, j, 0, 0] + grad[i, j, 1, 1] + v / r
            tth = mut[i, j] * (2 * v / r - 2.0 / 3.0 * div)
            res[i, j, 2] -= tth * Aq[i, j]


@njit(cache=True, error_model="numpy")
def fill_ghosts(U, W, Tg, Gam, mask, rc_in, Nn, jc, js, p0, T0, alpha_conv, r_in, Uco, cpe, Re_, single):
    """Boundary ghost cells (2 layers): inlet / coflow (i<0), outlet (i>=NI), axis (j<0), farfield (j>=NJ)."""
    NIg, NJg = U.shape[0], U.shape[1]
    NI = NIg - 2 * G; NJ = NJg - 2 * G
    ge = cpe / (cpe - Re_)
    cpa = GA * RA / (GA - 1.0)
    out = np.zeros(5)
    # ---- left (i = -1, -2)
    for j in range(NJ):
        jj = j + G
        if j < jc:
            # subsonic total-pressure inlet, exhaust, flow angle varying linearly to the wall angle
            p = W[G, jj, 3]
            if p > 0.999 * p0:
                p = 0.999 * p0
            M2 = 2.0 / (ge - 1.0) * ((p0 / p) ** ((ge - 1.0) / ge) - 1.0)
            T = T0 / (1.0 + 0.5 * (ge - 1.0) * M2)
            rho = p / (Re_ * T)
            V = math.sqrt(M2 * ge * Re_ * T)
            th = -alpha_conv * rc_in[j] / r_in
            u = V * math.cos(th); v = V * math.sin(th); Y = 1.0
        elif j >= js:
            p = W[G, jj, 3]; T = TA; Y = 0.0
            cp, R = _props(Y, cpe, Re_, single)
            rho = p / (R * T); u = Uco; v = 0.0
        else:
            p = PA; T = TA; Y = 0.0
            cp, R = _props(Y, cpe, Re_, single)
            rho = p / (R * T); u = 0.0; v = 0.0
        for gI in range(G):
            W[gI, jj, 0] = rho; W[gI, jj, 1] = u; W[gI, jj, 2] = v; W[gI, jj, 3] = p; W[gI, jj, 4] = Y
    # ---- right (outlet)
    for j in range(NJ):
        jj = j + G
        c = NI - 1 + G
        rho = W[c, jj, 0]; u = W[c, jj, 1]; v = W[c, jj, 2]; p = W[c, jj, 3]; Y = W[c, jj, 4]
        a = math.sqrt(Gam[c, jj] * p / rho)
        if u < 0.0:
            Y = 0.0; p = PA
            cp, R = _props(Y, cpe, Re_, single)
            rho = PA / (R * TA)
        elif u < a:
            p = PA
        for gI in range(G):
            q = NI + G + gI
            W[q, jj, 0] = rho; W[q, jj, 1] = u; W[q, jj, 2] = v; W[q, jj, 3] = p; W[q, jj, 4] = Y
    # ---- bottom (axis): mirror
    for i in range(NIg):
        for gJ in range(G):
            src = G + gJ; dst = G - 1 - gJ
            for k in range(5):
                W[i, dst, k] = W[i, src, k]
            W[i, dst, 2] = -W[i, src, 2]
    # ---- top (farfield)
    for i in range(NIg):
        c = NJ - 1 + G
        rho = W[i, c, 0]; u = W[i, c, 1]; v = W[i, c, 2]; p = W[i, c, 3]; Y = W[i, c, 4]
        if v < 0.0:
            Y = 0.0
            cp, R = _props(Y, cpe, Re_, single)
            V2 = u * u + v * v
            T = TA - 0.5 * V2 / cp
            p = PA - 0.5 * (PA / (R * TA)) * V2
            rho = p / (R * T)
        else:
            a = math.sqrt(Gam[i, c] * p / rho)
            if v < a:
                p = PA
        for gJ in range(G):
            q = NJ + G + gJ
            W[i, q, 0] = rho; W[i, q, 1] = u; W[i, q, 2] = v; W[i, q, 3] = p; W[i, q, 4] = Y
    # ghost conservative + T, gamma
    for i in range(NIg):
        for j in range(NJg):
            if mask[i, j] == 2:
                prim_to_cons(W[i, j, 0], W[i, j, 1], W[i, j, 2], W[i, j, 3], W[i, j, 4], cpe, Re_, single, out)
                for k in range(5):
                    U[i, j, k] = out[k]
                cp, R = _props(W[i, j, 4], cpe, Re_, single)
                Tg[i, j] = W[i, j, 3] / (W[i, j, 0] * R); Gam[i, j] = cp / (cp - R)


@njit(cache=True, error_model="numpy")
def time_step(W, Gam, mask, dI, dJ, mut, CFL, Prt):
    NI = dI.shape[0]; NJ = dI.shape[1]
    dt = 1e30
    for i in range(NI):
        for j in range(NJ):
            if mask[i + G, j + G] != 0:
                continue
            rho = W[i + G, j + G, 0]; u = W[i + G, j + G, 1]; v = W[i + G, j + G, 2]; p = W[i + G, j + G, 3]
            c = math.sqrt(Gam[i + G, j + G] * p / rho)
            s = (abs(u) + c) / dI[i, j] + (abs(v) + c) / dJ[i, j]
            nu = mut[i, j] / rho * max(1.0, Gam[i + G, j + G] / Prt)
            s += 2.0 * nu * (1.0 / dI[i, j] ** 2 + 1.0 / dJ[i, j] ** 2)
            d = CFL / s
            if d < dt:
                dt = d
    return dt


@njit(cache=True, error_model="numpy")
def local_time_step(W, Gam, mask, dI, dJ, mut, CFL, Prt, dtl):
    """Per-cell pseudo time step (local time stepping, steady state only)."""
    NI = dI.shape[0]; NJ = dI.shape[1]
    for i in range(NI):
        for j in range(NJ):
            dtl[i, j] = 0.0
            if mask[i + G, j + G] != 0:
                continue
            rho = W[i + G, j + G, 0]; u = W[i + G, j + G, 1]; v = W[i + G, j + G, 2]; p = W[i + G, j + G, 3]
            c = math.sqrt(Gam[i + G, j + G] * p / rho)
            s = (abs(u) + c) / dI[i, j] + (abs(v) + c) / dJ[i, j]
            nu = mut[i, j] / rho * max(1.0, Gam[i + G, j + G] / Prt)
            s += 2.0 * nu * (1.0 / dI[i, j] ** 2 + 1.0 / dJ[i, j] ** 2)
            dtl[i, j] = CFL / s


@njit(cache=True, error_model="numpy")
def update(U, U0, res, V, mask, dt, a0, a1):
    """U = a0*U0 + a1*(U + dt*res/V) on fluid cells (dt: global scalar)."""
    NI = V.shape[0]; NJ = V.shape[1]
    for i in range(NI):
        for j in range(NJ):
            if mask[i + G, j + G] != 0:
                continue
            for k in range(5):
                U[i + G, j + G, k] = a0 * U0[i + G, j + G, k] + a1 * (U[i + G, j + G, k] + dt * res[i, j, k] / V[i, j])


@njit(cache=True, error_model="numpy")
def update_local(U, U0, res, V, mask, dtl, a0, a1):
    """Same with a per-cell time step array (LTS); returns the L2 norm of the density residual res/V."""
    NI = V.shape[0]; NJ = V.shape[1]
    s = 0.0; n = 0
    for i in range(NI):
        for j in range(NJ):
            if mask[i + G, j + G] != 0:
                continue
            r0 = res[i, j, 0] / V[i, j]
            s += r0 * r0; n += 1
            for k in range(5):
                U[i + G, j + G, k] = a0 * U0[i + G, j + G, k] + a1 * (U[i + G, j + G, k] + dtl[i, j] * res[i, j, k] / V[i, j])
    return math.sqrt(s / max(n, 1))


# ----------------------------------------------------------------------------------------------- driver
class Solver:
    def __init__(self, grid, gas, single=False, turbulent=True, Cl=0.071, use_phi=True, Prt=0.7, Sct=0.7,
                 CFL=0.5, Uco=5.0, order=2):
        self.g = grid
        self.gas = dict(gas)
        self.single = bool(single); self.turb = bool(turbulent); self.Cl = Cl; self.use_phi = use_phi
        self.Prt = Prt; self.Sct = Sct; self.CFL = CFL; self.Uco = Uco; self.order = order
        NI, NJ = grid.NI, grid.NJ
        self.U = np.zeros((NI + 2 * G, NJ + 2 * G, 5)); self.W = np.zeros_like(self.U)
        self.Tg = np.zeros((NI + 2 * G, NJ + 2 * G)); self.Gam = np.zeros_like(self.Tg)
        self.res = np.zeros((NI, NJ, 5)); self.grad = np.zeros((NI, NJ, 4, 2)); self.mut = np.zeros((NI, NJ))
        self.rc_in = np.ascontiguousarray(grid.rc[0, :])
        self.t = 0.0; self.nstep = 0
        self.alpha_conv = math.radians(45.0)
        self.set_gas(gas)
        self.init_ambient()

    def set_gas(self, gas):
        self.gas = dict(gas)
        ge, Re_ = gas['gamma_e'], gas['R_e']
        self.cpe = ge * Re_ / (ge - 1.0); self.Re_ = Re_
        self.p0 = gas['p0']; self.T0 = gas['T0']

    def init_ambient(self):
        out = np.zeros(5)
        prim_to_cons(PA / ((RA if not self.single else self.Re_) * TA), 0.0, 0.0, PA, 0.0, self.cpe, self.Re_, self.single, out)
        self.U[:, :, :] = out[None, None, :]
        self._prims()

    def _prims(self):
        n = cons2prim(self.U, self.W, self.Tg, self.Gam, self.g.mask, self.cpe, self.Re_, self.single)
        return n

    def rhs(self):
        g = self.g
        self._prims()
        fill_ghosts(self.U, self.W, self.Tg, self.Gam, g.mask, self.rc_in, g.Nn, g.jc, g.js, self.p0, self.T0,
                    self.alpha_conv, g.r_in, self.Uco, self.cpe, self.Re_, self.single)
        convective_residual(self.W, self.Gam, g.mask, g.nxI, g.nrI, g.AI, g.nxJ, g.nrJ, g.AJ, g.Aq, self.cpe, self.Re_,
                            self.single, self.order, self.res)
        if self.turb:
            cell_gradients(self.W, self.Tg, g.mask, g.nxI, g.nrI, g.LI, g.nxJ, g.nrJ, g.LJ, g.Aq, self.grad)
            eddy_viscosity(self.W, self.Gam, self.grad, g.region, g.rc, g.Nn, self.Cl, self.use_phi, self.mut)
            viscous_residual(self.W, self.Tg, g.mask, self.grad, self.mut, g.nxI, g.nrI, g.AI, g.nxJ, g.nrJ, g.AJ,
                             g.Aq, g.rc, self.cpe, self.Re_, self.single, self.Prt, self.Sct, self.res)

    def step_lts(self):
        """One SSP-RK2 pseudo-time iteration with local time steps; returns L2 of d(rho)/dt (stage 1)."""
        g = self.g
        if not hasattr(self, 'dtl'):
            self.dtl = np.zeros((g.NI, g.NJ))
        self.rhs()
        local_time_step(self.W, self.Gam, g.mask, g.dI, g.dJ, self.mut, self.CFL, self.Prt, self.dtl)
        U0 = self.U.copy()
        r = update_local(self.U, U0, self.res, g.V, g.mask, self.dtl, 0.0, 1.0)
        self.rhs()
        update_local(self.U, U0, self.res, g.V, g.mask, self.dtl, 0.5, 0.5)
        self.nstep += 1
        return r

    def step(self, dt_fixed=None):
        g = self.g
        self.rhs()
        dt = time_step(self.W, self.Gam, g.mask, g.dI, g.dJ, self.mut, self.CFL, self.Prt) if dt_fixed is None else dt_fixed
        U0 = self.U.copy()
        update(self.U, U0, self.res, g.V, g.mask, dt, 0.0, 1.0)
        self.rhs()
        update(self.U, U0, self.res, g.V, g.mask, dt, 0.5, 0.5)
        self.t += dt; self.nstep += 1
        return dt

    # ---- diagnostics
    def fields(self):
        self._prims()
        s = (slice(G, -G), slice(G, -G))
        W = self.W[s]; T = self.Tg[s]; gam = self.Gam[s]
        c = np.sqrt(gam * W[..., 3] / W[..., 0])
        M = np.hypot(W[..., 1], W[..., 2]) / c
        return dict(rho=W[..., 0].copy(), u=W[..., 1].copy(), v=W[..., 2].copy(), p=W[..., 3].copy(), Y=W[..., 4].copy(),
                    T=T.copy(), gamma=gam.copy(), M=M, mut=self.mut.copy())

    def exit_plane(self):
        """Mass flow [kg/s] and thrust [N] from momentum + pressure integral over the nozzle exit plane (2*pi*sum)."""
        g = self.g; f = g.Nn
        mdot = 0.0; F = 0.0
        for j in range(g.jc):
            A = g.AI[f, j] * 2 * math.pi
            # face state: average of the two adjacent cells
            wa = self.W[f - 1 + G, j + G]; wb = self.W[f + G, j + G]
            w = 0.5 * (wa + wb)
            mdot += w[0] * w[1] * A
            F += (w[0] * w[1] * w[1] + w[3] - PA) * A
        return mdot, F

    def throat_mdot(self):
        g = self.g
        f = int(np.argmin(np.abs(g.X[:g.Nn + 1, 0] - g.x_t)))
        m = 0.0
        for j in range(g.jc):
            A = g.AI[f, j] * 2 * math.pi
            w = 0.5 * (self.W[f - 1 + G, j + G] + self.W[f + G, j + G])
            m += w[0] * (w[1] * g.nxI[f, j] + w[2] * g.nrI[f, j]) * A
        return m

    def save(self, fn, extra=None):
        F = self.fields()
        mdot, thrust = self.exit_plane()
        meta = dict(t=self.t, nstep=self.nstep, single=self.single, turbulent=self.turb, Cl=self.Cl, use_phi=self.use_phi,
                    Prt=self.Prt, Sct=self.Sct, CFL=self.CFL, gas=self.gas, mdot_exit=mdot, thrust_exit=thrust,
                    mdot_throat=self.throat_mdot(), grid=self.g.summary(), level=self.g.level)
        if extra:
            meta.update(extra)
        np.savez_compressed(fn, xc=self.g.xc, rc=self.g.rc, X=self.g.X, R=self.g.R, region=self.g.region,
                            U=self.U, meta=json.dumps(meta, default=float), **F)

    def load_state(self, fn):
        d = np.load(fn, allow_pickle=False)
        self.U[:] = d['U']
        m = json.loads(str(d['meta']))
        self.t = m['t']; self.nstep = m['nstep']
        self._prims()

    def init_from(self, other_fn):
        """Initialise from a saved solution on a nested grid (coarser by 2 or same level)."""
        d = np.load(other_fn, allow_pickle=False)
        Uo = d['U'][G:-G, G:-G]
        NIo, NJo = Uo.shape[0], Uo.shape[1]
        NI, NJ = self.g.NI, self.g.NJ
        if (NIo, NJo) == (NI, NJ):
            self.U[G:-G, G:-G] = Uo
        elif (2 * NIo, 2 * NJo) == (NI, NJ):
            self.U[G:-G, G:-G] = np.repeat(np.repeat(Uo, 2, axis=0), 2, axis=1)
        else:
            raise ValueError('grids are not nested by 2')
        self._prims()


def chamber_gas(frac=1.0, J=None):
    """Exhaust calibration identical to the OpenFOAM case (make_case.chamber_state)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'openfoam'))
    import make_case
    if J is None:
        J, pts, Rbody = make_case.load_interface()
    cs = make_case.chamber_state(J, frac)
    return dict(gamma_e=cs['gamma_eff'], R_e=cs['R_eff'], p0=cs['Pc'], T0=cs['T0'], OF=cs['OF'], frac=frac,
                Tc=cs['Tc'], cstar_del=cs['cstar_del'], Me=cs['Me'], pe=cs['pe'], eps=cs['eps'])


def load_geometry():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'openfoam'))
    import make_case
    J, pts, Rbody = make_case.load_interface()
    return J, pts, Rbody
