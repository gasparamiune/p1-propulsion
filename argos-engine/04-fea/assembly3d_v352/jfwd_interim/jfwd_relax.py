"""J-FWD TC-01 wall: preload-only and preload + soak wall stress against Fty(T), and the shell pull, for Mechanical's preload-relaxation
bound (lead 2026-10-20 08:40Z ruling 1).  DERIVED from the SIM stress field of a J-FWD sub-model run (.frd / .frd.gz, streamed) and its
post (post.json / post_partial.json contact_exact); no new run.  fea3d 2026-10-20 ~08:55Z.

Classification (lead 08:40Z): the preload pull on the TC-01 wall is SECONDARY (imposed by tightening; wall yielding relaxes it; the wall's
travel is bounded by the fit gap): the preload-only wall bending is INFORMATION; the criterion is P+Q <= 2 Fty(T) at the soak steps.

Per soak step s (temperature field T_s exactly as in the deck: mapped S-AX field or uniform rows):
  lines   full-wall radial SCLs in (r, theta, z) (jfwd_midbay.line), on the PRELOAD stress field (preload only, 20 C solve) and on the soak
          stress field (preload + soak), both with the line temperature of T_s:
            mid-bay  az 0.02 / 35.98 deg, z' -6 .. +6 mm (0.5 mm) about the TC-01 hole axis;
            ring     z' 0, +-1.5, +-3 mm, delta from the hole edge to the mid-bay, lines ending on the OD R31.75;
            seat     the same lines ending on the d10.5 spot-face flat (x' 31.313), the hole-edge line excluded;
            hole-edge line (delta = asin(2.76 / 28.627)): local in-plane Kt, information;
          per family: the governing line by preload-only Pm+Pb / Fty(T) and by soak Pm+Pb / 2 Fty(T), each with its partner value;
  nodes   TC-01 nodes |z'| <= 4 mm, >= 1 mm from the hole wall, outside the head footprint + 1 mm on the OD / flat (jfwd_midbay zones):
          max vM / Fty(T_node) per zone (bore, OD, flat, mid-bay +-1 deg), preload-only and preload + soak;
  shell pull F_sh = screw force (exact K u head resultant) - FIT radial contact force on TC-01 (exact), at PRELOAD and each soak step.
usage: jfwd_relax.py JOB [UPTO] -> jfwd/runs/JOB/relax.json (relax_partial.json with UPTO)"""
from __future__ import annotations
import sys, json, math, gzip
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_sub as JS        # noqa: E402
import jfwd_deck as JD       # noqa: E402
import jfwd_post as JP       # noqa: E402
import jfwd_midbay as JM     # noqa: E402

TK = 273.15
HR = JS.GEO["hole_r"]


def fty(T):
    return JP.tab("AL6061-T6", "Fty", T)


def fam_lines(loc, S, Tn, zc):
    out = []
    for az_deg in (0.02, JS.SECTOR - 0.02):
        az = math.radians(az_deg)
        delta = math.radians(az_deg - JS.AZ_SCREW)
        for zp in np.arange(-6.0, 6.0001, 0.5):
            r = JM.line(loc, S, Tn, az, zc + zp, JS.r_out(delta, zp))
            r.update({"family": "midbay", "az_deg": az_deg, "delta_deg": round(math.degrees(delta), 3), "z_prime_mm": round(float(zp), 2)})
            out.append(r)
    dmin = math.asin((HR + 0.01) / JM.R_IN)
    dmax = math.radians(JS.AZ_SCREW - 0.02)
    for zp in (0.0, -1.5, 1.5, -3.0, 3.0):
        for k, d in enumerate(np.linspace(dmin, dmax, 25)):
            for sgn in (-1, +1):
                ro = JS.r_out(sgn * d, zp)
                fam = "hole_edge" if k == 0 else ("seat" if ro < JS.R_OD - 0.01 else "ring")
                r = JM.line(loc, S, Tn, math.radians(JS.AZ_SCREW) + sgn * d, zc + zp, ro)
                r.update({"family": fam, "delta_deg": round(math.degrees(sgn * d), 3), "z_prime_mm": zp})
                out.append(r)
    return out


def rnd(r):
    o = {k: r[k] for k in ("family", "delta_deg", "z_prime_mm") if k in r}
    for k in ("Pm", "PmPb", "peak", "T_mean_C", "t_mm"):
        o[k] = round(float(r[k]), 2 if k == "t_mm" else 1)
    o["peak_at"] = r["peak_at"]
    return o


def pair_rec(p, s):
    """p: preload-only line, s: the same line at the soak (None if not landed); both at the soak-step line temperature."""
    T = p["T_mean_C"]
    Fy = fty(T)
    o = {"line": {k: p[k] for k in ("family", "delta_deg", "z_prime_mm")}, "t_mm": round(p["t_mm"], 3), "T_soak_mean_C": round(T, 1),
         "Fty_T_MPa": round(Fy, 1),
         "preload_only": {"Pm": round(p["Pm"], 1), "PmPb": round(p["PmPb"], 1), "peak": round(p["peak"], 1), "peak_at": p["peak_at"],
                          "Pm_over_Fty": round(p["Pm"] / Fy, 3), "PmPb_over_Fty": round(p["PmPb"] / Fy, 3), "peak_over_Fty": round(p["peak"] / Fy, 3),
                          "PmPb_exceeds_Fty": bool(p["PmPb"] > Fy)}}
    if s is not None:
        o["preload_plus_soak"] = {"Pm": round(s["Pm"], 1), "PmPb": round(s["PmPb"], 1), "peak": round(s["peak"], 1), "peak_at": s["peak_at"],
                                  "Pm_over_Fty": round(s["Pm"] / Fy, 3), "PmPb_over_Fty": round(s["PmPb"] / Fy, 3), "peak_over_Fty": round(s["peak"] / Fy, 3),
                                  "MS_PQ_2Fty": round(2 * Fy / max(s["PmPb"], 1e-9) - 1, 3),
                                  "PmPb_exceeds_Fty": bool(s["PmPb"] > Fy), "Pm_exceeds_Fty": bool(s["Pm"] > Fy)}
    return o


def main(job, upto=None):
    wd = JD.RUNS / job
    meta = json.loads((wd / "meta.json").read_text())
    tag = meta["mesh"]
    mj = JS.use_mesh(tag)
    shift = mj["shift"]
    m = dict(np.load(JD.OUT / f"model_{tag}.npz", allow_pickle=False))
    X, T, B = m["X"], m["T"], m["B"]
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
    kP = names.index("PRELOAD") + 1
    if kP not in by or "STRESS" not in by[kP]:
        raise SystemExit("PRELOAD step not in the frd yet")
    SP = by[kP]["STRESS"]
    pj = wd / "post.json"
    if not pj.exists() or upto is not None:
        pj = wd / "post_partial.json"
    post = json.loads(pj.read_text())["steps"] if pj.exists() else {}
    loc01 = JP.Locator(X, T[np.nonzero(B == "TC-01")[0]])
    n01 = m["n01"]
    zc = JS.Z_SCREW - shift
    xa1, ya1, za1, ra1 = JD.loc(X, -shift)
    d_hole = ra1 - HR
    r_n = np.hypot(X[:, 0], X[:, 1])
    az_n = np.degrees(np.arctan2(X[:, 1], X[:, 0]))
    zp_n = X[:, 2] - zc
    on_bore = r_n[n01] < JS.R_BORE01 + 0.03
    xo = JS.x_out(ya1[n01], za1[n01])
    on_out = (xa1[n01] > xo - 0.03) & ~on_bore
    on_flat = on_out & (np.hypot(ya1[n01], za1[n01]) <= JS.SPOT["r_flat"]) & (JS.GEO.get("seat") == "spot")
    zone = (np.abs(zp_n[n01]) <= 4.0) & (d_hole[n01] >= 1.0) & ~(on_out & (ra1[n01] < JS.GEO["head_r"] + 1.0))
    zones = {"bore": zone & on_bore, "OD": zone & on_out & ~on_flat, "flat_outside_head+1mm": zone & on_flat,
             "midbay_nodes": zone & ((np.abs(az_n[n01]) <= 1.0) | (np.abs(az_n[n01] - JS.SECTOR) <= 1.0))}
    vP = JP.vm(SP[n01])

    def fsh(st):
        ce = (post.get(st) or {}).get("contact_exact")
        if not ce:
            return None
        return {"screw_force_N": ce["HEAD_on_screw_along_axis_N"], "FIT_radial_N": ce["FIT_radial_on_TC01_N"],
                "F_sh_N": round(ce["HEAD_on_screw_along_axis_N"] - ce["FIT_radial_on_TC01_N"], 1),
                "BEAR_shear_N": ce.get("BEAR_shear_perp_axis_N")}
    out = {"job": job, "doc": __doc__.split("usage:")[0].strip(), "mesh": tag, "seat": JS.GEO.get("seat"), "mu": meta.get("mu"),
           "FIT_clearance_mm": meta.get("FIT_clearance_mm"), "preload_N": meta.get("preload_N"), "z_hole_plane": round(zc, 3),
           "shell_pull": {"PRELOAD": fsh("PRELOAD")}, "steps": {}}
    for k, nm in enumerate(names):
        if not nm.startswith("SOAK"):
            continue
        sdef = meta["step_defs"][nm]
        Tn = JM.step_temps(m, shift, sdef)
        landed = (k + 1) in by and "STRESS" in by[k + 1]
        Ss = by[k + 1]["STRESS"] if landed else None
        pre = fam_lines(loc01, SP, Tn, zc)
        soak = fam_lines(loc01, Ss, Tn, zc) if landed else [None] * len(pre)
        o = {"T_rule": "mapped S-AX " + "/".join(sdef[1][1:]) if isinstance(sdef[1], (list, tuple)) else "uniform per part " + json.dumps(sdef[1]),
             "soak_landed": bool(landed), "families": {}}
        for fam in ("midbay", "ring", "seat", "hole_edge"):
            idx = [i for i, r in enumerate(pre) if r["family"] == fam]
            if not idx:
                continue
            gp = max(idx, key=lambda i: pre[i]["PmPb"] / fty(pre[i]["T_mean_C"]))
            rec = {"governing_by_preload_only": pair_rec(pre[gp], soak[gp])}
            if landed:
                gs = max(idx, key=lambda i: soak[i]["PmPb"] / fty(pre[i]["T_mean_C"]))
                rec["governing_by_soak_PQ"] = pair_rec(pre[gs], soak[gs])
            rec["n_lines"] = len(idx)
            rec["n_lines_preload_PmPb_gt_Fty"] = int(sum(pre[i]["PmPb"] > fty(pre[i]["T_mean_C"]) for i in idx))
            rec["n_lines_preload_Pm_gt_Fty"] = int(sum(pre[i]["Pm"] > fty(pre[i]["T_mean_C"]) for i in idx))
            if landed:
                rec["n_lines_soak_PmPb_gt_Fty"] = int(sum(soak[i]["PmPb"] > fty(pre[i]["T_mean_C"]) for i in idx))
                rec["n_lines_soak_PmPb_gt_2Fty"] = int(sum(soak[i]["PmPb"] > 2 * fty(pre[i]["T_mean_C"]) for i in idx))
                # 2026-10-20 ~09:40Z: membrane exceedance (relaxation bound: Pm > Fty(T) = net-section yield of the wall line)
                rec["n_lines_soak_Pm_gt_Fty"] = int(sum(soak[i]["Pm"] > fty(pre[i]["T_mean_C"]) for i in idx))
                gm = max(idx, key=lambda i: soak[i]["Pm"] / fty(pre[i]["T_mean_C"]))
                rec["governing_by_soak_Pm"] = pair_rec(pre[gm], soak[gm])
            # compact profile (2026-10-20 ~09:10Z): [delta_deg, z_prime_mm, t_mm, Pm, PmPb, peak (preload only)] + [Pm, PmPb (soak)]
            # + (~09:40Z) [T_mean_C, Fty_T_MPa] of each line at this step's temperature
            rec["profile_cols"] = (["delta_deg", "z_prime_mm", "t_mm", "Pm_pre", "PmPb_pre", "peak_pre"] + (["Pm_soak", "PmPb_soak"] if landed else [])
                                   + ["T_mean_C", "Fty_T_MPa"])
            rec["profile"] = [[pre[i]["delta_deg"], pre[i]["z_prime_mm"], round(float(pre[i]["t_mm"]), 3), round(float(pre[i]["Pm"]), 1),
                               round(float(pre[i]["PmPb"]), 1), round(float(pre[i]["peak"]), 1)]
                              + ([round(float(soak[i]["Pm"]), 1), round(float(soak[i]["PmPb"]), 1)] if landed else [])
                              + [round(float(pre[i]["T_mean_C"]), 1), round(float(fty(pre[i]["T_mean_C"])), 1)] for i in idx]
            o["families"][fam] = rec
        # nodes
        Tc = Tn[n01] - TK
        Fy = np.array([fty(t) for t in Tc])
        vS = JP.vm(Ss[n01]) if landed else None
        nod = {}
        for lab, msk in zones.items():
            if not msk.any():
                continue
            rr = {}
            for key, vv in (("preload_only", vP), ("preload_plus_soak", vS)):
                if vv is None:
                    continue
                j = int(np.argmax(np.where(msk, vv / Fy, -1)))
                n = int(n01[j])
                rr[key] = {"node": n + 1, "vm_MPa": round(float(vv[j]), 1), "T_C": round(float(Tc[j]), 1), "Fty_T_MPa": round(float(Fy[j]), 1),
                           "vm_over_Fty": round(float(vv[j] / Fy[j]), 3), "r_az_z": [round(float(r_n[n]), 3), round(float(az_n[n]), 2), round(float(X[n, 2]), 3)],
                           "d_hole_mm": round(float(d_hole[n]), 3), "vm_exceeds_Fty": bool(vv[j] > Fy[j])}
                if key == "preload_plus_soak":
                    rr[key]["MS_PQ_nodal_2Fty_info"] = round(float(2 * Fy[j] / max(vv[j], 1e-9) - 1), 3)
            rr["n_nodes"] = int(msk.sum())
            nod[lab] = rr
        o["nodal"] = nod
        out["shell_pull"][nm] = fsh(nm)
        out["steps"][nm] = o
        print(nm, o["T_rule"], "landed" if landed else "(preload-only rows at this step's T)")
        for fam, rec in o["families"].items():
            g = rec["governing_by_preload_only"]
            s_ = g.get("preload_plus_soak", {})
            print("   %-9s pre-gov line %-34s T %5.1f Fty %5.1f | preload Pm %5.1f PmPb %5.1f (x%.3f Fty) | +soak Pm %s PmPb %s (x%s Fty, MS_PQ %s)" % (
                fam, json.dumps(g["line"]), g["T_soak_mean_C"], g["Fty_T_MPa"], g["preload_only"]["Pm"], g["preload_only"]["PmPb"],
                g["preload_only"]["PmPb_over_Fty"], s_.get("Pm"), s_.get("PmPb"), s_.get("PmPb_over_Fty"), s_.get("MS_PQ_2Fty")))
            if "governing_by_soak_PQ" in rec:
                g = rec["governing_by_soak_PQ"]
                s_ = g["preload_plus_soak"]
                print("   %-9s soak-gov line %-33s T %5.1f | preload PmPb %5.1f (x%.3f) | +soak Pm %5.1f PmPb %5.1f (x%.3f Fty) MS_PQ %+.3f" % (
                    "", json.dumps(g["line"]), g["T_soak_mean_C"], g["preload_only"]["PmPb"], g["preload_only"]["PmPb_over_Fty"],
                    s_["Pm"], s_["PmPb"], s_["PmPb_over_Fty"], s_["MS_PQ_2Fty"]))
        for lab, rr in nod.items():
            print("   nodal %-22s" % lab, {kk: (v["vm_MPa"], v["T_C"], v["vm_over_Fty"], v["node"]) for kk, v in rr.items() if isinstance(v, dict)})
    print("shell pull", json.dumps(out["shell_pull"]))
    if upto is not None:
        out["partial_upto_ccx_step"] = upto
    (wd / ("relax.json" if upto is None else "relax_partial.json")).write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
