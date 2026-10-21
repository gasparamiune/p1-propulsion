"""J-FWD screw: N, V, M along the whole shank + the exact shear-plane resultant and the load balance (fea3d 2026-10-20 ~10:50Z;
lead 10:24Z: '(b2) at FA1S: N, V and M along the shank, the maximum M on the threaded length near the shear plane and where it sits;
load balance: 10 x V at the shear plane against the applied FA1S head load (P_gauge x pi/4 x 57.25^2) and where any difference goes').

Per step (global J-FWD job or seat patch; DERIVED from the SIM .frd):
  sections   stress resultants over the screw disc r' <= 2.5 (jfwd_post.section_force: nodal-averaged S, quadratic interpolation) on a
             grid from the tip + 0.3 to under the head: 0.1 mm over x' 26.0 .. 29.6, 0.25 mm elsewhere; N (along the axis, + tension),
             V (perpendicular), M (bending about the section centre); the screw is BONDED to TC-02 over x' x_tap_lo .. 28.6, so the sections
             there are the screw's own internal forces with the bonded thread as an elastic foundation.  M_max on the threaded length
             (x' <= 28.6) and over the shank in TC-01 (x' >= 28.625), with x'.
  plane      EXACT shear-plane resultant: the sum of the screw nodal internal forces f = sum_e int B^T sigma dV (jfwd_cforce.body_forces, the
             deck's E(T), alpha(T)) over the screw nodes on the tip side of the gap (x' < 28.61): those nodes carry only the thread ties
             (and, in a patch, the prescribed cut-boundary reactions), the gap nodes carry nothing, so the sum is the force TC-02 passes into
             the screw = (N_plane, V_plane).  Check: screw BEAR-node forces at x' < 28.61 excluding the tie nodes (expected 0; 11:10Z: the 10:40Z field included the tie nodes).
  balance    (global job) the applied TC-02 axial load per sector = P x TC02_total_axial_per_MPa (the deck closes it to pi 28.625^2 / 10
             per MPa = P pi/4 57.25^2 / 10 per screw); split (jfwd_seatforce.decompose, every TC-02 node in one class) into the thread
             ties (-> screw), the FIT contact (TC-02 FIT nodes: internal force minus the consistent pressure loads, tie force removed at
             the tap-mouth tie nodes, symmetry reaction removed on the planes), the ground springs, the symmetry planes and the
             unclassified rest; 10 x V_plane vs P pi/4 57.25^2.  (fea3d 11:05Z: the 10:40Z version took the FIT z without subtracting the
             consistent pressure loads and without the tie correction at the tap-mouth nodes; its 'remainder 222 N' is withdrawn.)
usage: jfwd_shank.py JOB [STEP ...] [upto=K]  -> jfwd/runs/JOB/shank.json"""
from __future__ import annotations
import sys, json, math, gzip
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_sub as JS        # noqa: E402
import jfwd_deck as JD       # noqa: E402
import jfwd_post as JP       # noqa: E402
import jfwd_midbay as JM     # noqa: E402
import jfwd_cforce as JC     # noqa: E402

TK = 273.15
MATS = {"AL": ([[6.890e4, 293.15], [6.620e4, 373.15], [6.340e4, 423.15], [6.0e4, 473.15], [5.58e4, 523.15], [5.1e4, 573.15]], 0.33,
               [[2.32e-5, 293.15], [2.36e-5, 373.15], [2.43e-5, 473.15], [2.52e-5, 573.15]]),
        "A480": ([[1.93e5, 293.15], [1.8721e5, 373.15], [1.7949e5, 473.15], [1.72735e5, 573.15], [1.6598e5, 673.15]], 0.29,
                 [[1.6e-5, 293.15], [1.6e-5, 373.15], [1.65e-5, 473.15], [1.7e-5, 573.15], [1.75e-5, 673.15]])}
X_PLANE = 28.61


def grid(x_lo, x_hi):
    a = list(np.arange(x_lo, 26.0, 0.25)) + list(np.arange(26.0, 29.6001, 0.1)) + list(np.arange(29.75, x_hi + 1e-9, 0.25))
    return [round(float(v), 3) for v in a if x_lo <= v <= x_hi]


def main(job, steps=None, upto=None):
    wd = JD.RUNS / job
    meta = json.loads((wd / "meta.json").read_text())
    patch = meta.get("kind") == "seat_submodel"
    tag = meta["mesh"]
    mj = JS.use_mesh(tag)
    shift = mj["shift"]
    m = dict(np.load(JD.OUT / f"model_{tag}.npz", allow_pickle=False))
    X, T, B = m["X"], m["T"], m["B"]
    keep = np.ones(len(T), bool)
    gmeta = meta
    if patch:
        S = dict(np.load(JD.OUT / f"seat_{meta['seat_tag']}.npz", allow_pickle=False))
        keep = S["keep"]
        gmeta = json.loads((JD.RUNS / meta["global_job"] / "meta.json").read_text())
    frd = wd / f"{job}.frd"
    if frd.exists():
        by = JP.read_frd_steps(frd, len(X), upto)
    else:
        JP.open = lambda p, mode="r", errors=None: gzip.open(str(p) + ".gz", "rt", errors=errors)
        try:
            by = JP.read_frd_steps(frd, len(X), upto)
        finally:
            del JP.open
    names = meta["steps"]
    JSFC = [None]
    esc = np.nonzero(keep & (B == "SCREW"))[0]
    locsc = JP.Locator(X, T[esc])
    nsc = np.unique(T[esc])
    xs = JD.loc(X[nsc])[0]
    tip_side = nsc[xs < X_PLANE]
    bear_nodes = np.unique(np.concatenate([m["fcn"][m["bear_m"] & keep[m["fe"]]].ravel(), m["fmn"][m["bear_m"] & keep[m["fe"]]].ravel()]))
    bear_tip = np.setdiff1d(np.intersect1d(bear_nodes, tip_side), m["new_thr"])   # 11:10Z: tie nodes excluded (they carry the tie force)
    x_lo = float(JS.GEO["x_tip"]) + 0.3
    x_hi = float(JS.GEO["x_seat"]) - 0.05
    xg = grid(x_lo, x_hi)
    out = {"job": job, "patch": patch, "mesh": tag, "doc": __doc__.split("usage:")[0].strip(), "x_plane_cut_mm": X_PLANE,
           "x_tap_lo": JS.GEO["x_tap_lo"], "x_tip": JS.GEO["x_tip"], "x_seat": JS.GEO["x_seat"], "brk_r": JS.GEO.get("brk_r", 0.0),
           "brk_c": JS.GEO.get("brk_c", 0.0), "n_tip_side_nodes": int(len(tip_side)), "n_bear_nodes_tip_side": int(len(bear_tip)),
           "evidence": "SIM (.frd) + DERIVED (stress resultants, exact nodal internal forces)", "steps": {}}
    for k, nm in enumerate(names):
        if (k + 1) not in by or "STRESS" not in by[k + 1]:
            continue
        if steps and nm not in steps:
            continue
        F = by[k + 1]
        Sx, U = F["STRESS"], F["DISP"][:, :3]
        if nm in ("SEAT", "PRELOAD"):
            Tn = np.full(len(X), 293.15)
            pc = 0.0
        else:
            sdef = gmeta["step_defs"][nm]
            pc = float(sdef[0])
            Tn = JM.step_temps(m, shift, sdef)
            Tn = np.where(np.isfinite(Tn), Tn, 293.15)
        secs = []
        for x in xg:
            s = JP.section_force(locsc, Sx, x)
            secs.append({"x": x, "N": round(s["N"], 1), "V": round(s["V"], 1), "M": round(s["M_bend_Nmm"], 1), "min_bary": round(s["min_bary"], 3)})
        thr = [s for s in secs if s["x"] <= 28.6 and s["min_bary"] > -0.05]
        sh = [s for s in secs if s["x"] >= 28.625 and s["min_bary"] > -0.05]
        e_, nu_, a_ = MATS["A480"]
        f = JC.body_forces(X, T[esc], U, Tn, e_, nu_, a_)
        Fp = f[tip_side].sum(0)
        Np = float(Fp @ JD.EN)
        Vp_vec = Fp - Np * JD.EN
        rec = {"label": (gmeta["step_defs"].get(nm, [None, None, nm])[2] if nm not in ("SEAT", "PRELOAD") else nm), "Pc_MPa": pc,
               "sections": secs,
               "M_max_threaded": (max(thr, key=lambda s: s["M"]) if thr else None),
               "M_max_shank_in_TC01": (max(sh, key=lambda s: s["M"]) if sh else None),
               "plane_exact": {"N_N": round(Np, 1), "V_N": round(float(np.linalg.norm(Vp_vec)), 1),
                               "V_vec_N": [round(float(v), 1) for v in Vp_vec], "V_axial_z_N": round(float(Vp_vec[2]), 1),
                               "bear_nodes_tip_side_nontie_force_N": round(float(np.linalg.norm(f[bear_tip].sum(0))), 2) if len(bear_tip) else 0.0}}
        if not patch and pc > 0:
            import jfwd_seatforce as JSF
            if JSFC[0] is None:
                JSFC[0] = JSF.Ctx.__new__(JSF.Ctx)
                JSF.Ctx.__init__(JSFC[0], job)
            dec = JSF.decompose(JSFC[0], nm, F)
            sh = dec["shell_TC02"]
            P_ref = pc * math.pi / 4 * 57.25 ** 2
            P_fe = pc * float(gmeta.get("TC02_axial_per_MPa_N", math.pi * 28.625 ** 2 / 10.0))
            app_z = sh["applied_on_TC02_vec_N"][2]
            tie_z = sh["tie_vec_on_TC02_N"][2]
            fit_z = dec["seat_TC02"]["z_on_TC02_N"]
            spr_z = sh["springs_vec_N"][2]
            sym_z = sh["sym_reaction_vec_N"][2]
            unc_z = sh["unclassified_vec_N"][2]
            rec["balance"] = {"P_gauge_MPa": pc, "ref_head_load_full_N": round(P_ref, 1), "ref_head_load_per_screw_N": round(P_ref / 10, 1),
                              "FE_applied_TC02_axial_per_sector_N": round(P_fe, 1), "FE_applied_TC02_z_from_loads_N": app_z,
                              "ten_x_V_plane_N": round(10 * float(np.linalg.norm(Vp_vec)), 1),
                              "V_plane_over_ref_per_screw": round(float(np.linalg.norm(Vp_vec)) / (P_ref / 10), 4),
                              "tie_z_on_TC02_N": tie_z, "FIT_contact_z_on_TC02_N": fit_z, "springs_z_on_TC02_N": spr_z,
                              "sym_z_on_TC02_N": sym_z, "unclassified_z_on_TC02_N": unc_z,
                              "remainder_N": round(app_z + tie_z + fit_z + spr_z + sym_z + unc_z, 2),
                              "scale_to_ref_if_FIT_z_not_credited": round((P_ref / 10) / max(-tie_z, 1e-9), 4),
                              "note": "TC-02 z balance (jfwd_seatforce.decompose, exact): applied (pressure + cap + M14) + tie + FIT contact + springs "
                                      "+ symmetry + unclassified = 0; at mu 0 the FIT z force is the tap-mouth / TC-01 hole-edge contact"}
        out["steps"][nm] = rec
        mt, ms = rec["M_max_threaded"], rec["M_max_shank_in_TC01"]
        print(f"{nm}: plane N {rec['plane_exact']['N_N']} V {rec['plane_exact']['V_N']} | M_max thread {mt['M'] if mt else None} at x' {mt['x'] if mt else None}"
              f" | M_max shank {ms['M'] if ms else None} at x' {ms['x'] if ms else None} | bear tip-side non-tie {rec['plane_exact']['bear_nodes_tip_side_nontie_force_N']}"
              + (f" | balance {rec['balance']}" if 'balance' in rec else ""), flush=True)
    (wd / "shank.json").write_text(json.dumps(out, indent=1))
    print("wrote", wd / "shank.json")
    return out


if __name__ == "__main__":
    a = [x for x in sys.argv[2:] if "=" not in x]
    kw = dict(x.split("=", 1) for x in sys.argv[2:] if "=" in x)
    main(sys.argv[1], a or None, int(kw["upto"]) if "upto" in kw else None)
