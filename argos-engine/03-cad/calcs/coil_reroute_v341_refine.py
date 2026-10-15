"""FD-07 coil re-route, refined local search (CAD v3.4.1 feed, v2 of coil_reroute_v341, 2026-10-13, Mechanical).

coil_reroute_v341_v1.json (432 candidates) left ONE candidate through every geometric gate, and only with a 15 mm rigid hose
end (ferrule length ASSUMED below the 25 mm ESTIMATE) and 0.1-0.2 mm margins.  This driver searches around it with the same
evaluate() (coil_reroute_v341.py, unchanged method; v1.1 of the script adds the SLSQP end residuals), with the realistic 20 / 25 mm
ferrule, the TEE side-socket aim -6..-12 mm, fixed end z 72 / 74, az 297-303, r 54-56 and four plan limits.
Output: calcs/coil_reroute_v341_v2.json.  DERIVED (linear frame on CAD route candidates; EI ASSUMED; hose data as v1).
"""
from __future__ import annotations
import itertools, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import coil_reroute_v341 as cr
import parts_feed as pf

OUT = HERE / "coil_reroute_v341_v2.json"


def main():
    t0 = time.time()
    pf.FEED["hose"].update(cr.HOSE_NEW)
    pf.FEED["ferrule"].update(cr.FERRULE_NEW)
    rows = []
    grid = itertools.product((74.0, 72.0), (300.0, 297.0, 303.0), (55.0, 54.0, 56.0),
                             ((41.5, 56.0, 52.0), (41.5, 55.0, 51.0), (41.5, 57.0, 53.0), (41.5, 56.0, 50.0)),
                             (25.0, 20.0), (-10.0, -8.0, -12.0, -6.0))
    for z_end, fq_az, fq_r, (rmp, rmax, rpref), flen, aim in grid:
        p = {"z_end": z_end, "fq_az": fq_az, "fq_r": fq_r, "R_min_plan": rmp, "r_max": rmax, "r_pref": rpref,
             "ferrule.len": flen, "tee.side_aim": aim}
        rec = cr.evaluate(p)
        rows.append(rec)
        print(json.dumps({k: rec.get(k) for k in ("params", "feasible", "why", "length_mm", "wall_clr_stop_mm", "case_clr_stop_mm",
                                                  "tee_riser_clr_stop_mm", "Rmin_stop_mm", "EI_breakeven_Nm2", "plan_end_err_mm",
                                                  "pass_all_but_dynamic")}), flush=True)
    geo = [r for r in rows if r.get("feasible") and all(r["gates"][k] for k in ("saddle_75", "wall_3", "case_3", "tee_3", "MBR_static_30", "monotonic"))
           and r.get("plan_end_err_mm", 9.0) < 0.5]
    geo.sort(key=lambda r: (r["K_max_per_EI"],))
    for rec in geo[:3]:
        full = cr.evaluate(rec["params"], eng07=True)
        rec.update({k: v for k, v in full.items() if k.startswith("ENG07")})
        print("ENG07", json.dumps(rec["params"]), {k: rec[k] for k in rec if k.startswith("ENG07")}, flush=True)
    out = {"id": "coil_reroute_v341", "version": "v2 (refined local search)", "date": "2026-10-13", "owner": "mechanical",
           "script": "03-cad/src/calcs/coil_reroute_v341_refine.py (evaluate() of coil_reroute_v341.py v1.1)",
           "method": __doc__, "hose_model": {**cr.HOSE_NEW, "ferrule": cr.FERRULE_NEW, "MBR_static_gate_mm": cr.MBR_STATIC, "MBR_dynamic_mm": cr.MBR_DYN},
           "rows": rows, "n_geometric_pass": len(geo), "geometric_pass_sorted_by_K": [r["params"] for r in geo],
           "tag": "DERIVED (linear frame on CAD route candidates; EI ASSUMED; hose data sourced, see coil_reroute_v341.py)",
           "t_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print("done", out["t_s"], "geometric pass", len(geo))


if __name__ == "__main__":
    main()
