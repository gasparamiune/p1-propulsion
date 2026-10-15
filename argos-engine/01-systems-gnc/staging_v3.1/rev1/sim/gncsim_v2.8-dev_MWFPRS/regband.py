"""regband v1 (2026-10-13): GNC reduced model of the fuel-regression-law band (review RC-07; combustion.json regression_law:
a x0.6-1.5, n 0.35-0.68, both ASSUMED) for the 6-DOF, as built and validated by scripts/m2_regband_model.py from Combustion's
band runs of GNC's duty cycles (02-combustion data/v2/dc_gncv3_band, grain_q1d v2.4).

Model (sim6 v2.7.1-dev, reg_on; off by default):
    mdot_ox = mdot_ox,map x phi_ox(a, n, X)     mdot_f = mdot_f,map x phi_f(a, n, X)
    X = cumulative oxidiser at the map flows (kg), integrated by sim6 before phi is applied
phi tables: Combustion corner run / nominal-corner run (a x1.0, n 0.5), flow per delivered thrust, per 0.05 kg bin of X, on the
calibration cycle DC-B1 85 m dispersed p99 (k_est_asc 2, no growth); bilinear in (a, n) between the 3 x 3 corners; linear in X
between bin centres, end values held. Scope: B1-like hops (validated on the other B1 cycles within about 2 % of the oxidiser per
delivered impulse); NOT valid for the A1 profile (errors up to ~10 %: hypothesis H1 fails there).
Nothing is typed in: the tables come from the model file (sha256 recorded by the caller)."""
import json
import os

import numpy as np

VERSION = "regband v1"
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "regband", "regband_model_v1.json")
NK_MAX = 40
_CACHE = {}


def load(path=None):
    p = path or os.environ.get("GNC_REGBAND_MODEL") or MODEL_PATH
    if p not in _CACHE:
        with open(p) as f:
            _CACHE[p] = json.load(f)
    return _CACHE[p], p


def knots(a, n, path=None):
    """(x knots [kg], phi_ox, phi_f) for regression scale a (x nominal) and exponent n."""
    M, _ = load(path)
    T = M["tables"]
    ag = np.array(M["band"]["a_scale"], dtype=float)
    ng = np.array(M["band"]["n"], dtype=float)
    a = float(np.clip(a, ag[0], ag[-1]))
    n = float(np.clip(n, ng[0], ng[-1]))
    i = min(int(np.searchsorted(ag, a, side="right")) - 1, len(ag) - 2)
    j = min(int(np.searchsorted(ng, n, side="right")) - 1, len(ng) - 2)
    u = (a - ag[i]) / (ag[i + 1] - ag[i])
    w = (n - ng[j]) / (ng[j + 1] - ng[j])
    xs = np.array(T["x_centres_kg"], dtype=float)
    po = np.zeros_like(xs)
    pf = np.zeros_like(xs)
    for di, wa in ((0, 1.0 - u), (1, u)):
        for dj, wn in ((0, 1.0 - w), (1, w)):
            if wa * wn == 0.0:
                continue
            c = T["filled"][f"{float(ag[i + di])}|{float(ng[j + dj])}"]
            po = po + wa * wn * np.array(c["phi_ox"], dtype=float)
            pf = pf + wa * wn * np.array(c["phi_f"], dtype=float)
    if xs.size > NK_MAX:
        raise ValueError(f"regband model has {xs.size} knots > NK_MAX {NK_MAX}")
    return xs, po, pf


def phi(xs, ys, X):
    """Same interpolation as sim6._reg_phi (ends held)."""
    return float(np.interp(X, xs, ys))
