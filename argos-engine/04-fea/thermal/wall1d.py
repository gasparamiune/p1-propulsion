"""1-D transient wall-stack screening (Mechanical, v1 2026-10-12): phenolic insulator over a metal shell.

Purpose: reproduce Combustion's soakback_v2.json wall_stack numbers (3 mm phenolic on 6061: case 557-595 K after A1,
860-905 K B1 bounding) with an independent implementation, then screen insulator thickness and shell material
before the 2-D axisymmetric CalculiX model (04-fea/thermal).  Planar (thin-wall) implicit finite differences,
temperature-dependent k(T), cp(T) from engmat; perfect contact between layers.

BCs: gas side h_g (W/m2K) to T_aw during the burn, then natural convection 10 W/m2K to 300 K plus radiation
(eps 0.85) to 300 K (inner surface sees the open cavity: an upper bound on post-burn cooling of the hot face is
avoided by also running an adiabatic-inner variant); outer side h_out to 300 K + radiation eps_out.
No pyrolysis/ablation (conservative for the shell: pyrolysis gas and recession carry heat away).
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import engmat
SIG = 5.670374e-8


def props(mat):
    def k(T): return np.array([engmat.prop(mat, "k", t - 273.15) for t in np.atleast_1d(T)])
    def cp(T): return np.array([engmat.prop(mat, "cp", t - 273.15) for t in np.atleast_1d(T)])
    return engmat.rho(mat), k, cp


def run(layers, h_g, T_aw, t_burn, t_end=900.0, inner_post="convrad", h_out=10.0, eps_out=0.3, eps_in=0.85, dt=0.05, n_per_mm=6,
        T0=293.15, char_k=None):
    """layers: [(mat, thickness_m)] from the gas side outward.  Returns dict with time histories."""
    xs, mats = [], []
    for mat, t in layers:
        n = max(4, int(round(t * 1e3 * n_per_mm)))
        xs += [t / n] * n
        mats += [mat] * n
    dx = np.array(xs)
    N = len(dx)
    T = np.full(N, T0)
    P = {m: props(m) for m in set(mats)}
    rho = np.array([P[m][0] for m in mats])
    hist = {"t": [], "T_gas_face": [], "T_shell_in": [], "T_shell_out": [], "T_shell_max": []}
    shell = [i for i, m in enumerate(mats) if m == layers[-1][0]]
    t = 0.0
    while t < t_end - 1e-9:
        k = np.empty(N); cp = np.empty(N)
        for m in set(mats):
            idx = [i for i, mm in enumerate(mats) if mm == m]
            k[idx] = P[m][1](T[idx]); cp[idx] = P[m][2](T[idx])
            if char_k is not None and m == "PHENOLIC":
                hot = T[idx] > 600.0
                k[np.array(idx)[hot]] = char_k
        C = rho * cp * dx / dt
        kf = 2.0 / (dx[:-1] / k[:-1] + dx[1:] / k[1:])          # interface conductance
        A = np.zeros((N, N)); b = C * T
        for i in range(N - 1):
            A[i, i] += kf[i]; A[i, i + 1] -= kf[i]; A[i + 1, i + 1] += kf[i]; A[i + 1, i] -= kf[i]
        A[np.arange(N), np.arange(N)] += C
        burning = t < t_burn
        # gas side (node 0, half-cell treated as full cell surface)
        if burning:
            A[0, 0] += h_g; b[0] += h_g * T_aw
        elif inner_post == "convrad":
            hr = eps_in * SIG * (T[0] ** 2 + 300.0 ** 2) * (T[0] + 300.0)
            A[0, 0] += 10.0 + hr; b[0] += (10.0 + hr) * 300.0
        hr_o = eps_out * SIG * (T[-1] ** 2 + 300.0 ** 2) * (T[-1] + 300.0)
        A[-1, -1] += h_out + hr_o; b[-1] += (h_out + hr_o) * 300.0
        T = np.linalg.solve(A, b)
        t += dt
        if abs(t / 1.0 - round(t / 1.0)) < dt / 2:
            hist["t"].append(round(t, 2)); hist["T_gas_face"].append(float(T[0])); hist["T_shell_in"].append(float(T[shell[0]]))
            hist["T_shell_out"].append(float(T[-1])); hist["T_shell_max"].append(float(T[shell].max()))
    i = int(np.argmax(hist["T_shell_max"]))
    return {"T_shell_peak_K": round(hist["T_shell_max"][i], 1), "t_peak_s": hist["t"][i], "T_face_max_K": round(max(hist["T_gas_face"]), 0),
            "T_shell_end_K": round(hist["T_shell_max"][-1], 1), "hist": hist}


if __name__ == "__main__":
    out = {"id": "wall1d", "version": "v1", "date": "2026-10-12", "doc": __doc__.strip().splitlines()[0], "cases": []}
    hg, Taw = 920.0, 0.95 * 2845.0             # Combustion soakback_v2.json wall_stack row (post-chamber, max thrust)
    for (tb, lab) in ((5.83, "A1 5.83 s"), (20.7, "B1 20.7 s bounding")):
        for hgf in (1.0, 2.0):
            for layers in ([("PHENOLIC", 0.003), ("AL6061-T6", 0.003175)],
                           [("PHENOLIC", 0.0035), ("SS316L", 0.0025)], [("PHENOLIC", 0.0035), ("TI6AL4V", 0.0025)],
                           [("PHENOLIC", 0.0035), ("AL6061-T6", 0.0025)],
                           [("PHENOLIC", 0.005), ("AL6061-T6", 0.0025)], [("PHENOLIC", 0.007), ("AL6061-T6", 0.0025)]):
                for post in ("convrad", "adiabatic"):
                    r = run(layers, hg * hgf, Taw, tb, inner_post=post)
                    row = {"burn": lab, "h_g": hg * hgf, "layers": layers, "inner_post": post, **{k: v for k, v in r.items() if k != "hist"}}
                    out["cases"].append(row)
                    print(f"{lab:18s} hg x{hgf:.0f} {str(layers):58s} post {post:9s}: shell peak {r['T_shell_peak_K']:6.1f} K at {r['t_peak_s']:5.0f} s, face max {r['T_face_max_K']:5.0f} K, 900 s {r['T_shell_end_K']:.0f} K", flush=True)
    Path(__file__).with_name("wall1d_v1.json").write_text(json.dumps(out, indent=1))
