"""FD-07 coil re-route, grid on the CLOSED route (CAD v3.4.1 feed, v4 of coil_reroute_v341, 2026-10-13, Mechanical).

The Nelder-Mead run (coil_reroute_v341_opt.py, log runs/coil_reroute_v341_opt_stopped_noisy.log, kept as evidence) was stopped:
the SLSQP plan curve lands on different local optima for parameter changes of 0.01 deg (K_max/EI 99.9 -> 112.6, case clearance
4.24 -> 1.69 mm), so the objective is not smooth and a simplex search only samples that noise.  Each parameter set is
deterministic, so a grid of candidates on the closed route (parts_feed v3.4.1) is evaluated and the best realised geometry is
taken.  Ferrule (rigid hose-end sleeve) 15 / 20 / 25 mm.  Same evaluate() and gates as coil_reroute_v341.py.
Output: calcs/coil_reroute_v341_v4.json.  DERIVED (linear frame on CAD route candidates; EI ASSUMED).
"""
from __future__ import annotations
import itertools, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import coil_reroute_v341 as cr
import parts_feed as pf

OUT = HERE / "coil_reroute_v341_v4.json"


def J_of(rec):
    if not rec.get("feasible"):
        return None
    return min(rec["wall_clr_stop_mm"] - 3.0, rec["case_clr_stop_mm"] - 3.0, rec["tee_riser_clr_stop_mm"] - 3.0, (rec["Rmin_stop_mm"] - 30.0) / 2.0)


def main():
    t0 = time.time()
    pf.FEED["hose"].update(cr.HOSE_NEW)
    pf.FEED["ferrule"].update(cr.FERRULE_NEW)
    rows = []
    grid = list(itertools.product((20.0, 15.0), (300.0, 297.0, 303.0), (55.0, 54.0),
                                  ((56.0, 52.0), (56.0, 50.0), (57.0, 53.0), (55.0, 51.0)), (-12.0, -10.0, -8.0, -14.0)))
    grid += list(itertools.product((25.0,), (300.0, 297.0), (55.0, 54.0), ((56.0, 52.0), (55.0, 51.0)), (-12.0, -10.0, -8.0)))
    for flen, fq_az, fq_r, (rmax, rpref), aim in grid:
        p = {"z_end": 74.0, "fq_az": fq_az, "fq_r": fq_r, "R_min_plan": 41.5, "r_max": rmax, "r_pref": rpref, "ferrule.len": flen, "tee.side_aim": aim}
        rec = cr.evaluate(p)
        rec["J_mm"] = J_of(rec)
        rows.append(rec)
        print(json.dumps({k: rec.get(k) for k in ("params", "feasible", "why", "J_mm", "wall_clr_stop_mm", "case_clr_stop_mm", "tee_riser_clr_stop_mm",
                                                  "Rmin_stop_mm", "K_max_per_EI", "EI_breakeven_Nm2", "length_mm", "plan_residual_before_closure")}, default=float), flush=True)
    best = {}
    for flen in (25.0, 20.0, 15.0):
        c = [r for r in rows if r["params"]["ferrule.len"] == flen and r.get("J_mm") is not None and r["gates"]["saddle_75"] and r["gates"]["monotonic"]]
        c.sort(key=lambda r: (-r["J_mm"], r["K_max_per_EI"]))
        best[str(flen)] = [{"params": r["params"], "J_mm": r["J_mm"]} for r in c[:5]]
    out = {"id": "coil_reroute_v341", "version": "v4 (closed route, grid)", "date": "2026-10-13", "owner": "mechanical",
           "script": "03-cad/src/calcs/coil_reroute_v341_grid_closed.py (evaluate() of coil_reroute_v341.py v1.1, parts_feed v3.4.1 closed route)",
           "method": __doc__, "rows": rows, "best_by_ferrule": best,
           "tag": "DERIVED (linear frame on CAD route candidates; EI ASSUMED; hose data sourced, see coil_reroute_v341.py)", "t_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print("done", out["t_s"])


if __name__ == "__main__":
    main()
