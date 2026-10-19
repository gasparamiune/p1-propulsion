"""Free-body closure of the gimbal connector paths per unit step (REPORT 7.1; fea3d 2026-10-19).

Engine group: sum of connector forces ON the engine (inner bearing radial springs, inner washer, rods) + load applied to the engine = 0.
Ring group:   outer connector forces ON the ring + inner bearing / washer forces ON the ring + load applied to the ring = 0.
Applied loads: unit g steps -> -m_group x 9.80665 N x direction (group masses = mass.json group_model_kg, body force -rho a);
OP / PM / TZ (loads on engine parts only) -> applied on the engine = -(sum of airframe reactions) ; TH -> 0; R1/R2 -> +1 N along the rod
on the lever eye; BUMP -> -n_out on the TC-01 patch (unit pairs, model.json rod_geom / bumper).
Connector force = k (u_B-side aux - u_A) . e (linear SPRINGA along the undeformed posed direction).  N.
usage: check_fbd.py RUN STATE
"""
from __future__ import annotations
import sys, json
import numpy as np
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF        # noqa: E402

G = PF.A3.G_MM / 1000.0       # the solver value (9.810 m/s2, asm3d G_MM), not 9.80665: GRAV and item loads use it


def main(run, state):
    M, meta = PF.load_model(run)
    mj = json.loads((PF.RUNS / run / "mass.json").read_text())
    gm = mj["group_model_kg"]
    steps = meta.get("steps") or PF.STEPS_DEFAULT
    F = PF.load_fields(run, state)
    try:
        RF = PF.reactions(run, state, steps)
    except Exception:
        RF = {}
    out = {"run": run, "state": state, "steps": {}}
    XA = {b["label"]: M.xyzp([int(b["A"])])[0] for b in M.bush}
    XB = {b["label"]: M.xyzp([int(b["B"])])[0] for b in M.bush}
    Mg = {}
    for st in steps:
        if f"U_{st}" not in F or st.startswith("FREQ"):
            continue
        U = F[f"U_{st}"].astype(np.float64)
        if st != "TH" and "U_TH" in F:
            U = U - F["U_TH"].astype(np.float64)
        g = PF.connector_forces(M, U)
        eng, ring_in, ring_out = np.zeros(3), np.zeros(3), np.zeros(3)
        mom = np.zeros(3)                      # moment about the pivot of the connector forces on the engine (N mm)
        for base, d in g.items():
            for lab, v in d.items():
                fv = v["force_N"] * np.asarray(v["dir"])
                if base.startswith(("BRG_IN", "WSH_IN")):
                    eng += fv; ring_in -= fv
                    mom += np.cross(XA[base], fv)
                elif base.startswith(("BRG_OUT", "WSH_OUT")):
                    ring_out += fv
        # rods: A = horn eye ref, B = lever eye (engine); force on the engine = -f e (tension pulls the lever eye toward the horn)
        for base, d in g.items():
            if base.startswith("ROD"):
                for lab, v in d.items():
                    eng += -v["force_N"] * np.asarray(v["dir"])
                    mom += np.cross(XB[base], -v["force_N"] * np.asarray(v["dir"]))
        dirs = {"GX": np.array([1.0, 0, 0]), "GY": np.array([0, 1.0, 0]), "GZ": np.array([0, 0, 1.0])}
        if st in dirs:
            app_e = -gm["engine"] * G * dirs[st]
            app_r = -gm["ring"] * G * dirs[st]
        elif st == "TH":
            app_e = np.zeros(3); app_r = np.zeros(3)
        elif st in ("R1", "R2") and meta.get("rod_geom"):
            rg = meta["rod_geom"].get(st[1]) or meta["rod_geom"].get(int(st[1]))
            app_e = np.asarray(rg["e_push_on_engine"], float); app_r = np.zeros(3)     # +1 N on the lever eye (run_f1 / asm_build.rod_pair)
            app_m = np.cross(np.asarray(rg["lever_eye"], float), app_e)
        elif st == "BUMP" and meta.get("bumper"):
            app_e = -np.asarray(meta["bumper"]["n_out"], float); app_r = np.zeros(3)   # -n_out on the TC-01 patch (asm_build.bumper_pair)
            app_m = np.cross(np.asarray(meta["bumper"]["contact_point_mm"], float), app_e)   # patch resultant at the contact point (ASSUMED centroid)
        elif st in RF:
            tot = sum((np.asarray(v) for v in RF[st].values()), np.zeros(3))
            if "TH" in RF:
                tot = tot - sum((np.asarray(v) for v in RF["TH"].values()), np.zeros(3))
            app_e = -tot; app_r = np.zeros(3)
        else:
            continue
        if st in dirs:
            Mg[st] = (mom.copy(), dirs[st])
        mres = (mom + app_m) if "app_m" in locals() and st in ("R1", "R2", "BUMP") else None
        # sign convention of connector_forces: f > 0 = tension; force on node A = +f e, on B = -f e.  For BRG_IN / WSH_IN A = engine.
        res_e = eng + app_e
        res_r = ring_in + ring_out * -1.0 + app_r      # outer: A = ring -> force on ring = +f e ... see note
        res_r2 = ring_in + ring_out + app_r
        ref = max(np.linalg.norm(app_e), 1e-9)
        out["steps"][st] = {"applied_engine_N": app_e.round(4).tolist(), "connectors_on_engine_N": eng.round(4).tolist(),
                            "engine_residual_N": res_e.round(4).tolist(), "engine_closure_pct": (100.0 * (1 - np.linalg.norm(res_e) / ref) if np.linalg.norm(app_e) > 1e-3 else None),
                            "ring_residual_N": res_r2.round(4).tolist(), "applied_ring_N": app_r.round(4).tolist(),
                            "connector_moment_on_engine_Nmm": mom.round(3).tolist()}
        if mres is not None:
            out["steps"][st].update({"applied_moment_Nmm": app_m.round(3).tolist(), "moment_residual_Nmm": mres.round(3).tolist(),
                                     "moment_closure_pct": 100.0 * (1 - np.linalg.norm(mres) / max(np.linalg.norm(app_m), 1e-9))})
            print(f"      moment: applied {np.round(app_m, 2)} conn {np.round(mom, 2)} resid {np.round(mres, 3)} N mm", flush=True)
        if "app_m" in locals():
            del app_m
        print(f"{run}/{state} {st:4s} applied_eng {np.round(app_e, 3)} conn_on_eng {np.round(eng, 3)} resid {np.round(res_e, 3)} | ring resid {np.round(res_r2, 3)}", flush=True)
    if len(Mg) == 3:
        # engine CG implied by the connector moments of the three unit g steps: M_conn = m g (r x d)  ->  least squares for r
        m_e = gm["engine"] * G
        A_ = np.vstack([-m_e * np.array([[0, -d[2], d[1]], [d[2], 0, -d[0]], [-d[1], d[0], 0]]) for _, d in Mg.values()])
        b_ = np.concatenate([mv for mv, _ in Mg.values()])
        r, *_ = np.linalg.lstsq(A_, b_, rcond=None)
        out["engine_cg_implied_by_connector_moments_mm"] = r.round(3).tolist()
        out["engine_cg_fit_residual_Nmm"] = float(np.linalg.norm(A_ @ r - b_))
        print(f"engine CG implied by the g-step connector moments: {np.round(r, 3)} mm (fit residual {out['engine_cg_fit_residual_Nmm']:.3f} N mm)")
    (PF.RES / f"fbd_{run}_{state}.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
