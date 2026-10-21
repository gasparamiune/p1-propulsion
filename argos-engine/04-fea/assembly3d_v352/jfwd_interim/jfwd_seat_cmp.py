"""J-FWD local seat sub-model: comparison post (fea3d 2026-10-20 ~09:00Z; lead 08:17Z condition: the mu 0 patch must reproduce the
global run's under-head, hole-bearing and seat P+Q values at the same steps within ~5 %, else the patch is enlarged; then mu 0.2).
DERIVED from the SIM fields of the patch run and of its global run (.frd), on IDENTICAL node / face / line sets (patch interior), no new run.

Per common state (PRELOAD, SOAK52, SOAK, SOAK70, FA1S):
  under-head   TC-01 band (>= 1 mm from the hole wall) max von Mises (a) under the head (r' <= head r + 1.5 mm from the hole axis, through
               the wall) and (b) over the whole patch interior (|y'|, |z'| <= L - 2 mm, not prescribed); node, position, T; Neuber local
               strain n 15 / 30 against eps_L (jfwd_post.neuber_check, Mechanical (iii) form) at the node temperature;
  forces       exact K u resultants over the patch elements (jfwd_cforce.body_forces): screw head on the seat along the axis (screw
               tension), shank bearing shear (perpendicular to the axis), FIT radial on TC-01 (bore nodes not prescribed); the screw section
               forces (stress resultants, x' 28.7 .. 31.0);
  hole bearing V_bear / (D t), D 5.0, t 2.688 (FE spot-face wall), against Fbry / Fbru = 1.40 Fty / 1.60 Ftu at the hole temperature;
  seat P+Q     full-wall radial SCLs (r, theta, z) at z' 0, +-1.5, +-3 mm, delta from the hole edge to 12 deg, both sides: 'seat' lines (end
               on the d10.5 flat), 'ring' lines (end on the OD), the hole-edge line (information); max Pm+Pb per family, MS_PQ = 2 Fty(T) /
               Pm+Pb - 1 at the line temperature;
  contact      faces in contact, area, max CPRESS, and the slip fraction (|CSHEAR| >= 0.98 mu CPRESS) at mu > 0, per pair;
  relax seat lines (lead 09:47Z): the EXACT 54-line seat set of jfwd_relax (+ the hole-edge lines, information), line by line, with the
               per-line relative difference patch vs global (mu 0 check <= 5 % per line), MS_PQ per line and the z' 0 gradient rows
               (+6.05 / +6.57 / +7.09 / +7.61 deg and the mirrors).
Relative differences patch vs global; |rel| > 5 % is flagged.
usage: jfwd_seat_cmp.py PATCH_JOB [OTHER_PATCH_JOB]  -> jfwd/runs/PATCH_JOB/compare.json (OTHER: patch-size sensitivity rows)"""
from __future__ import annotations
import sys, json, math, gzip
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_sub as JS        # noqa: E402
import jfwd_deck as JD       # noqa: E402
import jfwd_post as JP       # noqa: E402
import jfwd_midbay as JM     # noqa: E402
import jfwd_cforce as JC     # noqa: E402

TK = 273.15
HR = JS.GEO["hole_r"]
STATES = ["PRELOAD", "SOAK52", "SOAK", "SOAK70", "FA1S"]
MATS = {"AL": ([[6.890e4, 293.15], [6.620e4, 373.15], [6.340e4, 423.15], [6.0e4, 473.15], [5.58e4, 523.15], [5.1e4, 573.15]], 0.33,
               [[2.32e-5, 293.15], [2.36e-5, 373.15], [2.43e-5, 473.15], [2.52e-5, 573.15]]),
        "A480": ([[1.93e5, 293.15], [1.8721e5, 373.15], [1.7949e5, 473.15], [1.72735e5, 573.15], [1.6598e5, 673.15]], 0.29,
                 [[1.6e-5, 293.15], [1.6e-5, 373.15], [1.65e-5, 473.15], [1.7e-5, 573.15], [1.75e-5, 673.15]])}


def frd_by_name(wd, job, n, names):
    frd = wd / f"{job}.frd"
    if frd.exists():
        by = JP.read_frd_steps(frd, n)
    else:
        JP.open = lambda p, mode="r", errors=None: gzip.open(str(p) + ".gz", "rt", errors=errors)
        try:
            by = JP.read_frd_steps(frd, n)
        finally:
            del JP.open
    return {nm: by[k + 1] for k, nm in enumerate(names) if (k + 1) in by and "STRESS" in by[k + 1]}


def rel(a, b):
    if a is None or b is None or abs(b) < 1e-9:
        return None
    return round((a - b) / abs(b), 4)


class Ctx:
    def __init__(self, pjob):
        self.wd = JD.RUNS / pjob
        self.meta = json.loads((self.wd / "meta.json").read_text())
        self.gjob = self.meta["global_job"]
        self.gmeta = json.loads((JD.RUNS / self.gjob / "meta.json").read_text())
        tag = self.meta["mesh"]
        self.mj = JS.use_mesh(tag)
        self.shift = self.mj["shift"]
        m = dict(np.load(JD.OUT / f"model_{tag}.npz", allow_pickle=False))
        self.m = m
        S = dict(np.load(JD.OUT / f"seat_{self.meta['seat_tag']}.npz", allow_pickle=False))
        self.S = S
        X, T, B = m["X"], m["T"], m["B"]
        self.X, self.T, self.B = X, T, B
        keep = S["keep"]
        self.keep = keep
        L = self.meta["L_mm"]
        self.L = L
        inK = np.zeros(len(X), bool)
        inK[S["nodes"]] = True
        isP = np.zeros(len(X), bool)
        isP[S["pres"]] = True
        self.isP = isP
        xa1, ya1, za1, ra1 = JD.loc(X, -self.shift)
        self.xa1, self.ya1, self.za1, self.ra1 = xa1, ya1, za1, ra1
        self.d_hole = ra1 - HR
        n01 = m["n01"]
        intr = inK[n01] & ~isP[n01] & (np.abs(ya1[n01]) <= L - 2.0) & (np.abs(za1[n01]) <= L - 2.0)
        self.n01i = n01[intr]
        band = self.d_hole[self.n01i] >= 1.0
        self.band_all = self.n01i[band]
        self.band_head = self.n01i[band & (ra1[self.n01i] <= JS.GEO["head_r"] + 1.5)]
        self.loc01 = JP.Locator(X, T[np.nonzero(keep & (B == "TC-01"))[0]])
        self.locsc = JP.Locator(X, T[np.nonzero(keep & (B == "SCREW"))[0]])
        nodes = lambda key: np.unique(np.concatenate([m["fcn"][S[f"f_{key}"]].ravel(), m["fmn"][S[f"f_{key}"]].ravel()]))
        cons = np.unique(np.concatenate([m[k].ravel() for k in ("sec", "new_sec", "thr", "new_thr")]))
        hs = np.setdiff1d(nodes("head_m"), cons)                   # screw head face (HEAD master)
        bs = np.setdiff1d(np.setdiff1d(nodes("bear_m"), hs), cons)  # screw shank in the TC-01 hole (BEAR master)
        fm = nodes("fit_m")
        fm = fm[~isP[fm]]                                          # TC-01 bore (FIT master), not prescribed
        assert not isP[hs].any() and not isP[bs].any()
        self.hs, self.bs, self.fm = hs, bs, fm
        az = np.arctan2(X[:, 1], X[:, 0])
        self.er = np.stack([np.cos(az), np.sin(az), np.zeros(len(X))], 1)
        self.Tcache = {}
        # restricted contact masks (patch faces) for jfwd_post.contact_summary
        self.mr = dict(m)
        for k in ("head_s", "head_m", "bear_s", "bear_m", "fit_s", "fit_m"):
            msk = np.zeros(len(m["fe"]), bool)
            msk[S[f"f_{k}"]] = True
            self.mr[k] = msk

    def temps(self, st):
        if st not in self.Tcache:
            if st in ("PRELOAD", "SEAT"):
                Tn = np.full(len(self.X), 293.15)
            else:
                Tn = JM.step_temps(self.m, self.shift, self.gmeta["step_defs"][st])
            self.Tcache[st] = np.where(np.isfinite(Tn), Tn, 293.15)
        return self.Tcache[st]


def quantities(c, F, st, mu):
    X, m = c.X, c.m
    S, U = F["STRESS"], F["DISP"][:, :3]
    Tn = c.temps(st)
    o = {}
    # under-head band and interior band
    for lab, ns in (("under_head_band", c.band_head), ("interior_band", c.band_all)):
        v = JP.vm(S[ns])
        j = int(np.argmax(v))
        n = int(ns[j])
        Tc = float(Tn[n]) - TK
        nb = JP.neuber_check(float(v[j]), Tc)
        o[lab] = {"vm_MPa": round(float(v[j]), 1), "node": n + 1, "x_prime": round(float(c.xa1[n]), 3), "y_prime": round(float(c.ya1[n]), 3),
                  "z_prime": round(float(c.za1[n]), 3), "r_prime": round(float(c.ra1[n]), 3), "d_hole_mm": round(float(c.d_hole[n]), 3),
                  "T_C": round(Tc, 1), "Fty_MPa": round(JP.tab("AL6061-T6", "Fty", Tc), 1),
                  "MS_y_SF1_elastic": round(JP.tab("AL6061-T6", "Fty", Tc) / max(float(v[j]), 1e-9) - 1, 3),
                  "neuber_MS_strain_n15": nb["n15"]["MS_strain"], "neuber_MS_strain_n30": nb["n30"]["MS_strain"],
                  "neuber_eps_n15": nb["n15"]["eps_local"], "eps_limit": nb["eps_limit"]}
    # all-node max under the head (contact edge, information)
    ns = c.n01i[c.ra1[c.n01i] <= JS.GEO["head_r"] + 1.5]
    v = JP.vm(S[ns])
    j = int(np.argmax(v))
    o["under_head_all_node_info"] = {"vm_MPa": round(float(v[j]), 1), "node": int(ns[j]) + 1, "r_prime": round(float(c.ra1[ns[j]]), 3),
                                     "d_hole_mm": round(float(c.d_hole[ns[j]]), 3), "x_prime": round(float(c.xa1[ns[j]]), 3)}
    # exact forces over the patch elements
    f = np.zeros((len(X), 3))
    for b, mt in (("TC-01", "AL"), ("TC-02", "AL"), ("SCREW", "A480")):
        e, nu, a = MATS[mt]
        f += JC.body_forces(X, c.T[c.keep & (c.B == b)], U, Tn, e, nu, a)
    head = f[c.hs].sum(0)
    bear = f[c.bs].sum(0)
    bperp = bear - (bear @ JD.EN) * JD.EN
    fit = float((f[c.fm] * c.er[c.fm]).sum())
    o["forces"] = {"HEAD_axial_N": round(float(head @ JD.EN), 1), "BEAR_shear_N": round(float(np.linalg.norm(bperp)), 1),
                   "FIT_radial_TC01_patch_N": round(fit, 1)}
    secs = [JP.section_force(c.locsc, S, x) for x in (28.70, 29.0, 29.5, 30.2, 31.0)]
    o["screw_sections"] = {f"x{s['x_prime_mm']}": {"N": round(s["N"], 1), "V": round(s["V"], 1), "M": round(s["M_bend_Nmm"], 1)} for s in secs}
    # hole bearing
    hn = c.n01i[np.abs(c.d_hole[c.n01i]) < 0.05]
    T01 = float(np.mean(Tn[hn])) - TK if len(hn) else 20.0
    Fty, Ftu = JP.tab("AL6061-T6", "Fty", T01), JP.tab("AL6061-T6", "Ftu", T01)
    sbr = o["forces"]["BEAR_shear_N"] / (5.0 * 2.688)
    o["hole_bearing"] = {"sigma_br_MPa": round(sbr, 1), "T_hole_C": round(T01, 1), "Fbry_MPa": round(1.40 * Fty, 1), "Fbru_MPa": round(1.60 * Ftu, 1),
                         "MS_y_SF1": round(1.40 * Fty / max(sbr, 1e-9) - 1, 3), "MS_u_SF1": round(1.60 * Ftu / max(sbr, 1e-9) - 1, 3)}
    # seat / ring lines within 12 deg
    zc = JS.Z_SCREW - c.shift
    dmin = math.asin((HR + 0.01) / JM.R_IN)
    fam = {"seat": [], "ring": [], "hole_edge": []}
    for zp in (0.0, -1.5, 1.5, -3.0, 3.0):
        for k, d in enumerate(np.linspace(dmin, math.radians(12.0), 14)):
            for sgn in (-1, +1):
                ro = JS.r_out(sgn * d, zp)
                fm_ = "hole_edge" if k == 0 else ("seat" if ro < JS.R_OD - 0.01 else "ring")
                r = JM.line(c.loc01, S, Tn, math.radians(JS.AZ_SCREW) + sgn * d, zc + zp, ro)
                Fy = JP.tab("AL6061-T6", "Fty", r["T_mean_C"])
                Fu = JP.tab("AL6061-T6", "Ftu", r["T_mean_C"])
                fam[fm_].append({"delta_deg": round(math.degrees(sgn * d), 3), "z_prime_mm": zp, "t_mm": round(r["t_mm"], 3),
                                 "Pm": round(r["Pm"], 1), "PmPb": round(r["PmPb"], 1), "peak": round(r["peak"], 1), "T_mean_C": round(r["T_mean_C"], 1),
                                 "MS_PQ_2Fty": round(2 * Fy / max(r["PmPb"], 1e-9) - 1, 3),
                                 "MS_y_Pm_SF1": round(Fy / max(r["Pm"], 1e-9) - 1, 3), "MS_u_PmPb_SF1": round(Fu / max(r["PmPb"], 1e-9) - 1, 3),
                                 "min_bary": round(r["min_bary"], 4)})
    o["lines"] = {k: max(v, key=lambda r: r["PmPb"]) for k, v in fam.items() if v}
    o["lines_max_Pm"] = {k: max(v, key=lambda r: r["Pm"]) for k, v in fam.items() if v}
    # 2026-10-20 ~09:55Z (lead 09:47Z (1)): the EXACT jfwd_relax seat-line set, line by line (same 25-point delta grid dmin .. AZ_SCREW - 0.02,
    # z' 0 / -1.5 / +1.5 / -3 / +3, lines ending on the d10.5 flat = 'seat', the k = 0 line = 'hole_edge'; same JM.line, same r_out), so the
    # mu 0 reproduction check (<= 5 % per line) and the mu 0.2 table use the 54 seat lines of js5's relax post with no moved or dropped line
    rl = []
    dmax = math.radians(JS.AZ_SCREW - 0.02)
    for zp in (0.0, -1.5, 1.5, -3.0, 3.0):
        for k, d in enumerate(np.linspace(dmin, dmax, 25)):
            for sgn in (-1, +1):
                ro = JS.r_out(sgn * d, zp)
                fm_ = "hole_edge" if k == 0 else ("seat" if ro < JS.R_OD - 0.01 else "ring")
                if fm_ == "ring":
                    continue
                r = JM.line(c.loc01, S, Tn, math.radians(JS.AZ_SCREW) + sgn * d, zc + zp, ro)
                Fy = JP.tab("AL6061-T6", "Fty", r["T_mean_C"])
                rl.append({"family": fm_, "delta_deg": round(math.degrees(sgn * d), 3), "z_prime_mm": zp, "t_mm": round(r["t_mm"], 3),
                           "Pm": round(r["Pm"], 1), "PmPb": round(r["PmPb"], 1), "peak": round(r["peak"], 1), "T_mean_C": round(r["T_mean_C"], 1),
                           "Fty_T_MPa": round(Fy, 1), "MS_PQ_2Fty": round(2 * Fy / max(r["PmPb"], 1e-9) - 1, 3),
                           "Pm_over_Fty": round(r["Pm"] / Fy, 3), "PmPb_over_Fty": round(r["PmPb"] / Fy, 3), "min_bary": round(r["min_bary"], 4)})
    o["relax_seat_lines"] = rl
    o["contact"] = JP.contact_summary(c.mr, F, mu)
    return o


def flat(o, pre=""):
    """numeric leaves of interest for the relative comparison."""
    keys = {}
    for lab in ("under_head_band", "interior_band"):
        keys[f"{lab}.vm_MPa"] = o[lab]["vm_MPa"]
        keys[f"{lab}.neuber_eps_n15"] = o[lab]["neuber_eps_n15"]
    keys["forces.HEAD_axial_N"] = o["forces"]["HEAD_axial_N"]
    keys["forces.BEAR_shear_N"] = o["forces"]["BEAR_shear_N"]
    keys["forces.FIT_radial_TC01_patch_N"] = o["forces"]["FIT_radial_TC01_patch_N"]
    keys["hole_bearing.sigma_br_MPa"] = o["hole_bearing"]["sigma_br_MPa"]
    for k, v in o["lines"].items():
        keys[f"lines.{k}.PmPb"] = v["PmPb"]
        keys[f"lines.{k}.Pm"] = o["lines_max_Pm"][k]["Pm"]
    keys["contact.HEAD.max_CPRESS_MPa"] = (o.get("contact") or {}).get("HEAD", {}).get("max_CPRESS_MPa")
    keys["contact.HEAD.area_in_contact_mm2"] = (o.get("contact") or {}).get("HEAD", {}).get("area_in_contact_mm2")
    return keys


def line_cmp(qp, qg):
    """per-line patch vs global on the exact relax seat-line set (lead 09:47Z (1)): rel. difference of Pm+Pb and Pm, both MS_PQ."""
    G = {(r["family"], r["delta_deg"], r["z_prime_mm"]): r for r in qg["relax_seat_lines"]}
    out = []
    for r in qp["relax_seat_lines"]:
        g = G.get((r["family"], r["delta_deg"], r["z_prime_mm"]))
        out.append({"family": r["family"], "delta_deg": r["delta_deg"], "z_prime_mm": r["z_prime_mm"], "t_mm": r["t_mm"], "T_mean_C": r["T_mean_C"],
                    "PmPb_patch": r["PmPb"], "PmPb_global": g["PmPb"] if g else None, "rel_PmPb": rel(r["PmPb"], g["PmPb"]) if g else None,
                    "Pm_patch": r["Pm"], "Pm_global": g["Pm"] if g else None, "rel_Pm": rel(r["Pm"], g["Pm"]) if g else None,
                    "MS_PQ_patch": r["MS_PQ_2Fty"], "MS_PQ_global": g["MS_PQ_2Fty"] if g else None,
                    "Pm_over_Fty_patch": r["Pm_over_Fty"], "PmPb_over_Fty_patch": r["PmPb_over_Fty"]})
    return out


def zgrad(lines, deltas=(6.051, 6.57, 7.089, 7.607)):
    """z' 0 gradient rows (lead 09:47Z (1)): +6.05 / +6.57 / +7.09 / +7.61 and the mirrors."""
    out = []
    for d in deltas:
        for sgn in (+1, -1):
            for r in lines:
                if r["family"] == "seat" and r["z_prime_mm"] == 0.0 and abs(r["delta_deg"] - sgn * d) < 0.002:
                    out.append(r)
    return out


def compare(pjob, other=None):
    c = Ctx(pjob)
    mu = float(c.meta["mu"])
    FP = frd_by_name(c.wd, pjob, len(c.X), c.meta["steps"])
    FG = frd_by_name(JD.RUNS / c.gjob, c.gjob, len(c.X), c.gmeta["steps"])
    out = {"job": pjob, "doc": __doc__.split("usage:")[0].strip(), "global_job": c.gjob, "mu": mu, "L_mm": c.L, "xcut_mm": c.meta["xcut_mm"],
           "global_mu": c.gmeta["mu"], "n_band_head_nodes": int(len(c.band_head)), "n_band_interior_nodes": int(len(c.band_all)),
           "steps": {}, "flags_gt_5pct": []}
    gpost = JD.RUNS / c.gjob / "post.json"
    gp = json.loads(gpost.read_text())["steps"] if gpost.exists() else {}
    if "SEAT" in FP:
        qs = quantities(c, FP["SEAT"], "SEAT", mu)
        out["seat_step"] = {"forces": qs["forces"], "s_seat": c.meta.get("s_seat"),
                            "note": "SEAT: boundary s x U_PRELOAD, d1 prescribed; proportional-path check: HEAD force / preload vs s"}
        out["seat_step"]["HEAD_over_preload"] = round(qs["forces"]["HEAD_axial_N"] / float(c.meta["preload_N"]), 4)
    for st in STATES:
        if st not in FP or st not in FG:
            continue
        qp = quantities(c, FP[st], st, mu)
        qg = quantities(c, FG[st], st, float(c.gmeta["mu"]))
        fp, fg = flat(qp), flat(qg)
        rr = {k: rel(fp[k], fg[k]) for k in fp}
        rec = {"patch": qp, "global_same_sets": qg, "rel_patch_vs_global": rr}
        ce = (gp.get(st) or {}).get("contact_exact")
        if ce:
            rec["global_full_model_exact"] = {k: ce.get(k) for k in ("HEAD_on_screw_along_axis_N", "BEAR_shear_perp_axis_N", "FIT_radial_on_TC01_N")}
        g_band = (gp.get(st) or {}).get("TC-01", {}).get("band")
        if g_band:
            rec["global_full_model_TC01_band"] = {k: g_band.get(k) for k in ("vm_max_MPa", "node", "x_prime", "dist_hole_or_tap_mm", "T_C")}
            rec["global_band_node_in_patch_interior"] = bool(g_band["node"] - 1 in set(c.band_all.tolist()))
        for k, v in rr.items():
            if v is not None and abs(v) > 0.05 and mu == float(c.gmeta["mu"]):
                out["flags_gt_5pct"].append([st, k, v, fp[k], fg[k]])
        lc = line_cmp(qp, qg)
        rec["relax_seat_lines_cmp"] = lc
        rec["z0_gradient"] = zgrad(lc)
        ns = [r for r in lc if r["family"] == "seat"]
        rec["relax_seat_lines_summary"] = {
            "n_seat_lines": len(ns), "n_hole_edge_lines": len(lc) - len(ns),
            "max_abs_rel_PmPb": max((abs(r["rel_PmPb"]) for r in ns if r["rel_PmPb"] is not None), default=None),
            "max_abs_rel_Pm": max((abs(r["rel_Pm"]) for r in ns if r["rel_Pm"] is not None), default=None),
            "n_lines_rel_gt_5pct": sum(1 for r in ns if (r["rel_PmPb"] is not None and abs(r["rel_PmPb"]) > 0.05) or (r["rel_Pm"] is not None and abs(r["rel_Pm"]) > 0.05)),
            "min_MS_PQ_patch": min((r["MS_PQ_patch"] for r in ns), default=None),
            "n_lines_MS_PQ_patch_negative": sum(1 for r in ns if r["MS_PQ_patch"] < 0),
            "n_lines_Pm_gt_Fty_patch": sum(1 for r in ns if r["Pm_over_Fty_patch"] > 1.0)}
        if mu == float(c.gmeta["mu"]):
            for r in ns:
                for kk in ("rel_PmPb", "rel_Pm"):
                    if r[kk] is not None and abs(r[kk]) > 0.05:
                        out["flags_gt_5pct"].append([st, f"relax_seat_line d{r['delta_deg']} z'{r['z_prime_mm']} {kk}", r[kk],
                                                     r["PmPb_patch"] if kk == "rel_PmPb" else r["Pm_patch"],
                                                     r["PmPb_global"] if kk == "rel_PmPb" else r["Pm_global"]])
        out["steps"][st] = rec
        print("   relax seat lines", rec["relax_seat_lines_summary"])
        print(st, "| under-head band P %.1f G %.1f (%s) | BEAR P %.1f G %.1f | HEAD P %.1f G %.1f | seat PmPb P %s G %s | ring PmPb P %s G %s" % (
            qp["under_head_band"]["vm_MPa"], qg["under_head_band"]["vm_MPa"], rr["under_head_band.vm_MPa"],
            qp["forces"]["BEAR_shear_N"], qg["forces"]["BEAR_shear_N"], qp["forces"]["HEAD_axial_N"], qg["forces"]["HEAD_axial_N"],
            qp["lines"].get("seat", {}).get("PmPb"), qg["lines"].get("seat", {}).get("PmPb"),
            qp["lines"].get("ring", {}).get("PmPb"), qg["lines"].get("ring", {}).get("PmPb")))
        if mu > 0:
            print("     contact", {k: (v.get("slip_area_fraction"), v.get("max_CPRESS_MPa"), v.get("area_in_contact_mm2")) for k, v in (qp["contact"] or {}).items()})
    if other:
        oc = json.loads((JD.RUNS / other / "compare.json").read_text())
        sens = {}
        for st, rec in out["steps"].items():
            if st in oc["steps"]:
                fa, fb = flat(rec["patch"]), flat(oc["steps"][st]["patch"])
                sens[st] = {k: rel(fa[k], fb[k]) for k in fa}
        out["sensitivity_vs"] = {"job": other, "L_mm": oc["L_mm"], "xcut_mm": oc["xcut_mm"], "rel": sens}
    (c.wd / "compare.json").write_text(json.dumps(out, indent=1, default=float))
    print("flags > 5 %:", out["flags_gt_5pct"])
    return out


if __name__ == "__main__":
    compare(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
