"""FD-07 coil re-route, local optimisation on the CLOSED route (CAD v3.4.1 feed, v3 of coil_reroute_v341, 2026-10-13, Mechanical).

parts_feed v3.4.1 closes the SLSQP plan-curve end residuals (0-6 mm, 0-2 deg in coil_reroute_v341 v1/v2: the hose solid did not meet
the fixed ferrule).  The closure moves the coil by up to the residual, and the stop clearances move with it (v1 best candidate:
wall 3.19 -> 2.46 mm, case 3.09 -> 4.32 mm), so the grid results of v1/v2 are screening only.  This driver maximises the smallest
clearance margin at the 8 deg stop on the closed route:
    J = min(wall - 3, case - 3, TEE/riser - 3, (R_min,stop - 30) / 2) - 0.005 (K_max/EI - 80)          [mm]
over fixed-end az / r / z, plan limits, TEE side-socket aim and the sleeve angle, for a fixed rigid hose-end length (ferrule 25 mm =
ESTIMATE of the crimp sleeve; 20 mm = a short-sleeve requirement to the hose maker), Nelder-Mead from the best v2 screening points.
Saddle >= 75 holds by construction (TEE side port z 72 -> crown 75.87; monotonic rise to z_end >= 72).
Output: calcs/coil_reroute_v341_v3.json.  DERIVED (linear frame on CAD route candidates; EI ASSUMED; hose data as v1).
"""
from __future__ import annotations
import json, math, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import coil_reroute_v341 as cr
import parts_feed as pf

OUT = HERE / "coil_reroute_v341_v3.json"
NAMES = ["fq_az", "fq_r", "r_max", "r_pref", "tee.side_aim", "z_end", "ferrule_in_deg", "R_min_plan"]
LO = np.array([290.0, 52.5, 54.0, 48.0, -18.0, 72.0, 0.0, 40.0])
HI = np.array([308.0, 57.5, 58.5, 55.0, -2.0, 77.0, 20.0, 45.0])
LOG = []


def to_params(x, flen):
    v = LO + (HI - LO) * (0.5 - 0.5 * np.cos(np.pi * np.clip(x, 0.0, 1.0)))      # smooth box map
    p = {k: round(float(val), 3) for k, val in zip(NAMES, v)}
    p["r_pref"] = min(p["r_pref"], p["r_max"] - 1.0)
    p["ferrule.len"] = flen
    return p


def from_params(p):
    v = np.array([p[k] for k in NAMES], float)
    u = (v - LO) / (HI - LO)
    return np.arccos(np.clip(1.0 - 2.0 * u, -1.0, 1.0)) / np.pi


def J_of(rec):
    if not rec.get("feasible"):
        return -20.0 if "diverged" in (rec.get("why") or "") else -10.0
    m = min(rec["wall_clr_stop_mm"] - 3.0, rec["case_clr_stop_mm"] - 3.0, rec["tee_riser_clr_stop_mm"] - 3.0, (rec["Rmin_stop_mm"] - 30.0) / 2.0)
    if not rec["gates"]["saddle_75"] or not rec["gates"]["monotonic"]:
        m -= 5.0
    return float(m - 0.005 * (rec["K_max_per_EI"] - 80.0))


def run(flen, starts, budget=110):
    best = None
    for x0p in starts:
        cache = {}

        def f(x):
            p = to_params(x, flen)
            key = tuple(sorted(p.items()))
            if key in cache:
                return cache[key]
            rec = cr.evaluate(p)
            j = J_of(rec)
            LOG.append({"flen": flen, "params": p, "J": round(j, 3), **{k: rec.get(k) for k in ("feasible", "why", "wall_clr_stop_mm", "case_clr_stop_mm",
                        "tee_riser_clr_stop_mm", "Rmin_stop_mm", "K_max_per_EI", "EI_breakeven_Nm2", "length_mm", "plan_residual_before_closure")}})
            print(json.dumps(LOG[-1], default=float), flush=True)
            cache[key] = -j
            return -j
        x0 = from_params({**x0p, "ferrule_in_deg": x0p.get("ferrule_in_deg", 10.0), "R_min_plan": x0p.get("R_min_plan", 41.5)})
        simplex = [x0] + [np.clip(x0 + 0.08 * np.eye(len(NAMES))[i] * (1 if x0[i] < 0.9 else -1), 0, 1) for i in range(len(NAMES))]
        r = minimize(f, x0, method="Nelder-Mead", options={"maxfev": budget, "initial_simplex": np.array(simplex), "xatol": 2e-3, "fatol": 0.01})
        cand = (-r.fun, to_params(r.x, flen))
        if best is None or cand[0] > best[0]:
            best = cand
    return best


def main():
    t0 = time.time()
    pf.FEED["hose"].update(cr.HOSE_NEW)
    pf.FEED["ferrule"].update(cr.FERRULE_NEW)
    starts = [{"fq_az": 300.0, "fq_r": 55.0, "r_max": 56.0, "r_pref": 52.0, "tee.side_aim": -12.0, "z_end": 74.0},
              {"fq_az": 297.0, "fq_r": 54.0, "r_max": 56.0, "r_pref": 50.0, "tee.side_aim": -12.0, "z_end": 74.0},
              {"fq_az": 300.0, "fq_r": 55.0, "r_max": 56.0, "r_pref": 52.0, "tee.side_aim": -10.0, "z_end": 72.0}]
    res = {}
    for flen in (25.0, 20.0):
        J, p = run(flen, starts)
        full = cr.evaluate(p, eng07=True)
        res[str(flen)] = {"J_mm": round(J, 3), "params": p, "record": full}
        print("BEST", flen, round(J, 3), json.dumps(p), {k: full.get(k) for k in ("wall_clr_stop_mm", "case_clr_stop_mm", "tee_riser_clr_stop_mm",
              "Rmin_stop_mm", "K_max_per_EI", "EI_breakeven_Nm2")}, flush=True)
    out = {"id": "coil_reroute_v341", "version": "v3 (closed route, Nelder-Mead)", "date": "2026-10-13", "owner": "mechanical",
           "script": "03-cad/src/calcs/coil_reroute_v341_opt.py (evaluate() of coil_reroute_v341.py v1.1, parts_feed v3.4.1 closed route)",
           "method": __doc__, "bounds": {"names": NAMES, "lo": LO.tolist(), "hi": HI.tolist()}, "best": res, "log": LOG,
           "tag": "DERIVED (linear frame on CAD route candidates; EI ASSUMED; hose data sourced, see coil_reroute_v341.py)",
           "t_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print("done", out["t_s"])


if __name__ == "__main__":
    main()
