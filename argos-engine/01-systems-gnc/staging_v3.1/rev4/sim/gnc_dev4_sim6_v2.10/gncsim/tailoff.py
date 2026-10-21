"""tailoff v1 (2026-10-12): GNC reduced model of the pintle-closing shutdown (ENG-05) and its calibration against
Combustion's grain_q1d v2 shutdown runs (combustion.json v2.2 valves_and_actuators.pintle_actuator.speed_checks,
file actuator_rate_check_v2.json).

Model (same equations as the sim6 v2.6 shutdown branch, toff_model = 1):
    lift command  l_r(t) = l0 - v_s t (>= 0),  l0 = lift at the pre-shutdown thrust on the static table
    actuator      l_a' = (l_r - l_a) / lag_a
    thrust        F_q = table(l_a);  F' = (F_q - F) / lag_c;  F = 0 below 0.5 N
The static table is Combustion's pre-shutdown (lift, thrust) points at the chosen full-stroke time plus a cut-off
lift l_cut where thrust reaches zero. lag_a, lag_c and l_cut are fitted by GNC to Combustion's time to 10 % and
tail-off impulse for the five pre-shutdown levels (DERIVED; Combustion assumes a 10 ms actuator lag and a ~4 ms
chamber lag). Nothing here is hard-coded from another discipline: the table, the speed and the targets are read
from the Combustion file at run time, and the fitted constants are stored with the sha256 of that file.
"""
import hashlib
import json
import os
import shutil

import numpy as np

FIT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tailoff",
                        "tailoff_fit_v1.json")


def checks_path(comb):
    """Path of Combustion's actuator speed-check file: env GNC_ACT_RATE, else combustion.json speed_checks.file."""
    p = os.environ.get("GNC_ACT_RATE")
    if p:
        return p
    pa = comb.get("valves_and_actuators", {}).get("pintle_actuator", {})
    sc = pa.get("speed_checks", {})
    if "file" not in sc:
        raise KeyError("combustion.json " + str(comb.get("version")) + " has no valves_and_actuators.pintle_actuator."
                       "speed_checks.file (needs combustion.json >= v2.2)")
    return sc["file"]


def load_checks(comb, snap_dir=None):
    """(dict, sha256, path) of the speed-check file; copied to snap_dir when given."""
    p = checks_path(comb)
    from . import engine_v2 as _ev2
    _ev2.pin_check(p)         # v2.9-dev (REV-GNC-2 N4): the actuator speed-check file must match the pin list when set
    b = open(p, "rb").read()
    if snap_dir:
        os.makedirs(snap_dir, exist_ok=True)
        q = os.path.join(snap_dir, os.path.basename(p))
        if os.path.abspath(q) != os.path.abspath(p):
            shutil.copy2(p, q)
    return json.loads(b), hashlib.sha256(b).hexdigest(), p


def table(chk, full_stroke):
    """(lift_mm[5], F_N[5], v_s mm/s, targets) at the given full-stroke time; targets = [(F0, t10, impulse)]."""
    sh = sorted([s for s in chk["shutdown"] if abs(float(s["full_stroke_s"]) - full_stroke) < 1e-6],
                key=lambda s: s["F_before_N"])
    if len(sh) != 5:
        raise ValueError(f"expected 5 shutdown levels at full stroke {full_stroke} s, found {len(sh)}")
    sr = [x for x in chk["start_rule"] if abs(float(x["full_stroke_s"]) - full_stroke) < 1e-6]
    if len(sr) != 1:
        raise ValueError(f"no start_rule entry at full stroke {full_stroke} s")
    tl = [float(s["lift_before_mm"]) for s in sh]
    tf = [float(s["F_before_N"]) for s in sh]
    tg = [(float(s["F_before_N"]), float(s["t_to_10pct_of_F_before_s"]), float(s["tailoff_impulse_Ns"])) for s in sh]
    return tl, tf, float(sr[0]["speed_mm_s"]), tg


def simulate(F0, tl, tf, vs, lag_a, lag_c, l_cut, dt=1e-3):
    """(t10 [s], impulse [N s]) of a shutdown from F0 with the reduced model (discrete, same update order as sim6)."""
    xl = np.array([l_cut] + list(tl)); xf = np.array([0.0] + list(tf))
    l_r = float(np.interp(F0, xf, xl)); l_a = l_r; Fa = F0; imp = 0.0; t = 0.0; t10 = None
    for _ in range(5000):
        l_r = max(0.0, l_r - vs * dt)
        l_a += (l_r - l_a) * dt / max(lag_a, dt)
        Fq = float(np.interp(l_a, xl, xf))
        Fa += (Fq - Fa) * dt / max(lag_c, dt)
        t += dt
        if Fa < 0.5:
            Fa = 0.0
        imp += Fa * dt
        if t10 is None and Fa < 0.1 * F0:
            t10 = t
        if Fa == 0.0:
            break
    return t10, imp


def fit(chk, full_stroke, dt=1e-3):
    """Grid fit of (l_cut, lag_a, lag_c) to Combustion's (t10, impulse); levels above 300 N weigh double (MECO)."""
    tl, tf, vs, tg = table(chk, full_stroke)
    best = None
    for lc in np.arange(0.0, 0.0601, 0.005):
        for la in np.arange(0.0, 0.0121, 0.001):
            for lcc in np.arange(0.001, 0.0061, 0.001):
                err = 0.0
                for F0, t10c, impc in tg:
                    t10, imp = simulate(F0, tl, tf, vs, la, lcc, lc, dt)
                    w = 2.0 if F0 > 300.0 else 1.0
                    err += w * (((imp - impc) / max(impc, 1.0)) ** 2 + 0.25 * ((t10 - t10c) / 0.005) ** 2)
                if best is None or err < best[0]:
                    best = (err, float(lc), float(la), float(lcc))
    res = []
    for F0, t10c, impc in tg:
        t10, imp = simulate(F0, tl, tf, vs, best[2], best[3], best[1], dt)
        res.append(dict(F0_N=F0, t10_comb_s=t10c, t10_gnc_s=round(t10, 4), imp_comb_Ns=impc, imp_gnc_Ns=round(imp, 3),
                        imp_err_pct=round(100.0 * (imp / impc - 1.0), 2), t10_err_ms=round(1000.0 * (t10 - t10c), 1)))
    return dict(full_stroke_s=full_stroke, speed_mm_s=vs, lift_mm=tl, thrust_N=tf, l_cut_mm=best[1], lag_a_s=best[2],
                lag_c_s=best[3], cost=best[0], residuals=res)


def calibration(sha, full_stroke, path=FIT_PATH):
    """Stored GNC fit for this speed-check file (sha256) and full stroke; KeyError when absent or stale."""
    if not os.path.exists(path):
        raise KeyError("no tail-off calibration " + path + " (run scripts/m2_tailoff_fit.py)")
    d = json.load(open(path))
    for c in d["fits"]:
        if c["source_sha256"] == sha and abs(c["full_stroke_s"] - full_stroke) < 1e-9:
            return c
    raise KeyError(f"tail-off calibration stale: no fit for sha256 {sha[:16]} at full stroke {full_stroke} s "
                   "(re-run scripts/m2_tailoff_fit.py)")


def tail_impulse(F0, tl, tf, vs, lag, l_cut):
    """Predictor (guidance) impulse: (1/v_s) int_{l_cut}^{l0} F(l) dl + F0 lag (same as sim6._tail_imp)."""
    xl = np.array([l_cut] + list(tl)); xf = np.array([0.0] + list(tf))
    l0 = float(np.interp(F0, xf, xl))
    ll = np.linspace(l_cut, l0, 2001)
    return float(np.trapezoid(np.interp(ll, xl, xf), ll)) / vs + F0 * lag
