"""Small transient lumped thermal network (04-fea/thermal, v1, 2026-10-13, Mechanical).

Nodes carry a heat capacity C (J/K); a node can be a boundary with a prescribed temperature history T(t) (K).
Links: conduction/convection G (W/K, may be a function of time), grey-body radiation  q = sigma A_eff (Ta^4 - Tb^4) with
A_eff from the two-surface enclosure formula, heat sources Q(t) (W).  Backward Euler in time, Newton on the radiation terms.
Verified by tests in lumped_selftest() (analytic RC decay, two-node radiative equilibrium).
"""
from __future__ import annotations
import math
import numpy as np

SIGMA = 5.670374419e-8


def a_eff(A1, eps1, F12, A2=None, eps2=None):
    """Grey two-surface exchange area: 1 / [(1-e1)/(e1 A1) + 1/(A1 F12) + (1-e2)/(e2 A2)]; A2/eps2 None -> large surface (term 0)."""
    r = (1 - eps1) / (eps1 * A1) + 1.0 / (A1 * F12)
    if A2 is not None and eps2 is not None:
        r += (1 - eps2) / (eps2 * A2)
    return 1.0 / r


class Net:
    def __init__(self):
        self.names, self.C, self.T0, self.bc = [], [], [], []
        self.G, self.R, self.Q = [], [], []

    def node(self, name, C, T0=293.15, bc=None):
        self.names.append(name); self.C.append(float(C)); self.T0.append(float(T0)); self.bc.append(bc)
        return len(self.names) - 1

    def idx(self, n):
        return n if isinstance(n, int) else self.names.index(n)

    def cond(self, a, b, G):
        self.G.append((self.idx(a), self.idx(b), G))

    def rad(self, a, b, Aeff):
        self.R.append((self.idx(a), self.idx(b), float(Aeff)))

    def src(self, a, Qf):
        self.Q.append((self.idx(a), Qf))

    def solve(self, t_end, dt, t0=0.0, record_every=1):
        n = len(self.names)
        T = np.array(self.T0, float)
        for i, f in enumerate(self.bc):
            if f is not None:
                T[i] = f(t0)
        C = np.array(self.C)
        free = np.array([f is None for f in self.bc])
        ts, out = [t0], [T.copy()]
        t, k = t0, 0
        while t < t_end - 1e-9:
            h = min(dt, t_end - t)
            t += h
            Tn = T.copy()
            for i, f in enumerate(self.bc):
                if f is not None:
                    Tn[i] = f(t)
            for _ in range(30):
                Fv = np.zeros(n); J = np.zeros((n, n))
                for a, b, G in self.G:
                    g = G(t) if callable(G) else G
                    q = g * (Tn[a] - Tn[b])
                    Fv[a] -= q; Fv[b] += q
                    J[a, a] -= g; J[a, b] += g; J[b, b] -= g; J[b, a] += g
                for a, b, A in self.R:
                    q = SIGMA * A * (Tn[a] ** 4 - Tn[b] ** 4)
                    da, db = 4 * SIGMA * A * Tn[a] ** 3, 4 * SIGMA * A * Tn[b] ** 3
                    Fv[a] -= q; Fv[b] += q
                    J[a, a] -= da; J[a, b] += db; J[b, b] -= db; J[b, a] += da
                for a, Qf in self.Q:
                    Fv[a] += Qf(t) if callable(Qf) else Qf
                res = C * (Tn - T) / h - Fv
                Jm = np.diag(C / h) - J
                idx = np.where(free)[0]
                d = np.linalg.solve(Jm[np.ix_(idx, idx)], -res[idx])
                Tn[idx] += d
                if np.max(np.abs(d)) < 1e-6:
                    break
            T = Tn
            k += 1
            if k % record_every == 0 or t >= t_end - 1e-9:
                ts.append(t); out.append(T.copy())
        return np.array(ts), np.array(out)


def lumped_selftest():
    # 1) RC decay to a fixed 300 K boundary: tau = C/G = 100 s, T(200) = 300 + 100 e^-2
    n = Net(); n.node("m", 100.0, 400.0); n.node("b", 0.0, 300.0, bc=lambda t: 300.0); n.cond("m", "b", 1.0)
    t, T = n.solve(200.0, 0.05)
    e1 = abs(T[-1, 0] - (300 + 100 * math.exp(-2))) / 100
    # 2) radiative equilibrium of a small node between two boundaries with equal A_eff: T^4 = (T1^4 + T2^4)/2
    n2 = Net(); n2.node("s", 1.0, 300.0); n2.node("h", 0, 500.0, bc=lambda t: 500.0); n2.node("c", 0, 300.0, bc=lambda t: 300.0)
    n2.rad("h", "s", 1e-3); n2.rad("s", "c", 1e-3)
    t2, T2 = n2.solve(5000.0, 10.0)
    e2 = abs(T2[-1, 0] - ((500 ** 4 + 300 ** 4) / 2) ** 0.25)
    return {"rc_decay_rel_err": e1, "rad_equilibrium_abs_err_K": e2, "pass": bool(e1 < 2e-3 and e2 < 0.01)}


if __name__ == "__main__":
    print(lumped_selftest())
