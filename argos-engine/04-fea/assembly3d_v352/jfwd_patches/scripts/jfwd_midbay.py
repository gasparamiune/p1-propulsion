"""J-FWD TC-01 bore mid-bay and ring between the screws at the soak steps (lead 2026-10-20 07:51Z (d)): P+Q and LC6.  DERIVED from the SIM
stress field of a J-FWD sub-model run (.frd / .frd.gz, streamed), no new run.  fea3d 2026-10-20.

The sector boundaries az 0 / az 36 are the mid-bay planes between two screws (cyclic symmetry, u_theta = 0 there).  Per soak step:
  * mid-bay SCLs: full-wall radial lines r 28.627 -> 31.748 on az 0.02 and 35.98 deg, z' = -6 .. +6 mm (0.5 mm) about the TC-01 hole
    axis (z = Z_SCREW - shift); components in (r, theta, z); Pm, Pm+Pb (= P+Q at the soak: preload + thermal, no pressure), the peak on
    the line and the line temperature (interpolated nodal field);
  * ring sweep: the same lines on the screw plane z' = 0 (and z' = +-1.5, +-3.0) from the hole edge (delta = asin(2.76 / 28.627)) to the
    mid-bay, both sides; on the spot-face mesh the line ends on the flat (r = 31.313 / cos delta inside the d10.5 cutter);
  * nodal (S-AX LC6 basis): TC-01 nodes with |z'| <= 4 mm, >= 1 mm from the hole wall and, on the OD / flat, >= 1 mm outside the
    head footprint (head r 4.75): max vM per zone (bore r < 28.65, OD / flat, all), and the mid-bay nodes (|az - 0| or |az - 36| <= 1 deg).
Criteria at the point temperature (engmat AL6061-T6 Fty / Ftu at T):
  P+Q  vs 2 Fty(T)                                  (shakedown; the 231 (1) / S-AX SCL criterion for the secondary soak stress)
  LC6  vs Fty(T) / 1.5 and Ftu(T) / 2.0             (S-AX LC6: combined elastic stress at the soak state, SF 1.5 / 2.0; the touchdown
                                                     inertia adds <= 13 N shear and <= 5 N axial per screw in the global model, i.e.
                                                     < 0.5 % of the screw force, so LC6 = the soak field with the LC6 factors)
usage: jfwd_midbay.py JOB -> jfwd/runs/JOB/midbay.json"""
from __future__ import annotations
import sys, json, math, gzip
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_sub as JS        # noqa: E402
import jfwd_deck as JD       # noqa: E402
import jfwd_post as JP       # noqa: E402
import jfwd_ligament as JL   # noqa: E402

R_IN = JS.R_BORE01 + 0.002
HR = JS.GEO["hole_r"]
TK = 273.15


def r_out_line(delta, zp):
    """exit radius of the radial line at azimuth offset delta (rad) from the screw axis, at z' (mm) about the TC-01 hole axis."""
    return JS.r_out(delta, zp)


def line(loc, S, Tn, az, z, ro, n=41):
    a = np.array([R_IN * math.cos(az), R_IN * math.sin(az), z])
    b = np.array([ro * math.cos(az), ro * math.sin(az), z])
    s = np.linspace(0, 1, n)
    P = a[None] + s[:, None] * (b - a)[None]
    Sv, best = loc.interp(S, P)
    Tl, _ = loc.interp(Tn[:, None], P)
    sc = JL.cyl(Sv, np.full(n, az))
    sm = np.trapezoid(sc, s, axis=0)
    sb = 6.0 * np.trapezoid(sc * (0.5 - s)[:, None, None], s, axis=0)
    vm_l = np.array([JL.vm33(x) for x in sc])
    j = int(np.argmax(vm_l))
    Tm = float(np.trapezoid(Tl[:, 0], s)) - TK
    return {"Pm": JL.vm33(sm), "PmPb": max(JL.vm33(sm + sb), JL.vm33(sm - sb)), "peak": float(vm_l[j]), "peak_at": "bore" if j < n // 3 else ("OD" if j > 2 * n // 3 else "mid"),
            "T_mean_C": Tm, "T_peak_C": float(Tl[j, 0]) - TK, "t_mm": float(ro - R_IN), "min_bary": float(best.min()), "s_m_rtz": JL.t6(sm), "s_b_rtz": JL.t6(sb)}


def crit(rec):
    Fy = JP.tab("AL6061-T6", "Fty", rec["T_mean_C"])
    Fu = JP.tab("AL6061-T6", "Ftu", rec["T_mean_C"])
    Fyp = JP.tab("AL6061-T6", "Fty", rec["T_peak_C"])
    Fup = JP.tab("AL6061-T6", "Ftu", rec["T_peak_C"])
    rec.update({"Fty_MPa": round(Fy, 1), "MS_PQ_2Fty": round(2 * Fy / max(rec["PmPb"], 1e-9) - 1, 3),
                "MS_LC6_SCL_y": round(Fy / (1.5 * max(rec["PmPb"], 1e-9)) - 1, 3), "MS_LC6_SCL_u": round(Fu / (2.0 * max(rec["PmPb"], 1e-9)) - 1, 3),
                "MS_LC6_peak_y": round(Fyp / (1.5 * max(rec["peak"], 1e-9)) - 1, 3), "MS_LC6_peak_u": round(Fup / (2.0 * max(rec["peak"], 1e-9)) - 1, 3)})
    for k in ("Pm", "PmPb", "peak", "T_mean_C", "T_peak_C", "t_mm"):
        rec[k] = round(rec[k], 2 if k == "t_mm" else 1)
    rec["min_bary"] = round(rec["min_bary"], 4)
    return rec


def step_temps(m, shift, sdef):
    tc = sdef[1]
    if isinstance(tc, (list, tuple)) and len(tc) == 3 and tc[0] == "map":
        Tn, _ = JD.mapped_temps(m, shift, tc[1], tc[2])
        return Tn
    Tn = np.full(len(m["X"]), np.nan)
    for part, key in (("TC-01", "n01"), ("TC-02", "n02"), ("SCREW", "nsc")):
        Tn[m[key]] = tc[part] + TK
    return Tn


def main(job):
    wd = JD.RUNS / job
    meta = json.loads((wd / "meta.json").read_text())
    tag = meta["mesh"]
    mj = JS.use_mesh(tag)
    shift = mj["shift"]
    m = dict(np.load(JD.OUT / f"model_{tag}.npz", allow_pickle=False))
    X, T, B = m["X"], m["T"], m["B"]
    frd = wd / f"{job}.frd"
    if frd.exists():
        by_step = JP.read_frd_steps(frd, len(X), UPTO)
    else:
        JP.open = lambda p, mode="r", errors=None: gzip.open(str(p) + ".gz", "rt", errors=errors)
        try:
            by_step = JP.read_frd_steps(frd, len(X), UPTO)
        finally:
            del JP.open
    names = meta["steps"]
    loc01 = JP.Locator(X, T[np.nonzero(B == "TC-01")[0]])
    n01 = m["n01"]
    zc = JS.Z_SCREW - shift
    xa1, ya1, za1, ra1 = JD.loc(X, -shift)
    d_hole = ra1 - HR
    r_n = np.hypot(X[:, 0], X[:, 1])
    az_n = np.degrees(np.arctan2(X[:, 1], X[:, 0]))
    zp_n = X[:, 2] - zc
    # nodal zones (TC-01): |z'| <= 4, >= 1 mm from the hole wall; OD / flat nodes >= 1 mm outside the head footprint
    on_bore = r_n[n01] < JS.R_BORE01 + 0.03
    xo = JS.x_out(ya1[n01], za1[n01])
    on_out = (xa1[n01] > xo - 0.03) & ~on_bore
    zone = (np.abs(zp_n[n01]) <= 4.0) & (d_hole[n01] >= 1.0) & ~(on_out & (ra1[n01] < JS.GEO["head_r"] + 1.0))
    midbay = zone & ((np.abs(az_n[n01]) <= 1.0) | (np.abs(az_n[n01] - JS.SECTOR) <= 1.0))
    out = {"job": job, "mesh": tag, "seat": JS.GEO.get("seat"), "doc": __doc__.split("usage:")[0].strip(), "z_hole_plane": round(zc, 3), "steps": {}}
    for k, nm in enumerate(names):
        if (k + 1) not in by_step or not (nm.startswith("SOAK") or nm in ("PRELOAD", "FA1S", "LC2N")) or "STRESS" not in by_step[k + 1]:
            continue
        S = by_step[k + 1]["STRESS"]
        sdef = meta.get("step_defs", {}).get(nm) or JD.STEPS.get(nm) or (0.0, {"TC-01": 20.0, "TC-02": 20.0, "SCREW": 20.0}, nm)
        Tn = step_temps(m, shift, sdef)
        o = {"T_rule": "mapped S-AX" if isinstance(sdef[1], (list, tuple)) else "uniform per part"}
        # mid-bay z sweep
        mb = []
        for az_deg in (0.02, JS.SECTOR - 0.02):
            az = math.radians(az_deg)
            delta = math.radians(az_deg - JS.AZ_SCREW)
            for zp in np.arange(-6.0, 6.0001, 0.5):
                rec = line(loc01, S, Tn, az, zc + zp, r_out_line(delta, zp))
                rec.update({"az_deg": az_deg, "z_prime_mm": round(float(zp), 2)})
                mb.append(crit(rec))
        o["midbay_SCL"] = mb
        o["midbay_governing"] = {"PQ": min(mb, key=lambda r: r["MS_PQ_2Fty"]), "LC6_peak_u": min(mb, key=lambda r: r["MS_LC6_peak_u"]),
                                 "LC6_peak_y": min(mb, key=lambda r: r["MS_LC6_peak_y"])}
        # ring sweep (screw plane and z' = +-1.5, +-3)
        dmin = math.asin((HR + 0.01) / R_IN)
        dmax = math.radians(JS.AZ_SCREW - 0.02)
        ring = []
        for zp in (0.0, -1.5, 1.5, -3.0, 3.0):
            for d in np.linspace(dmin, dmax, 25):
                for sgn in (-1, +1):
                    az = math.radians(JS.AZ_SCREW) + sgn * d
                    rec = line(loc01, S, Tn, az, zc + zp, r_out_line(sgn * d, zp))
                    rec.update({"delta_deg": round(math.degrees(sgn * d), 3), "z_prime_mm": zp})
                    ring.append(crit(rec))
        o["ring_governing_excl_hole_edge_line"] = {
            key: min([r for r in ring if abs(abs(r["delta_deg"]) - math.degrees(dmin)) > 2e-3], key=lambda r: r[key])
            for key in ("MS_PQ_2Fty", "MS_LC6_peak_u", "MS_LC6_peak_y")}
        o["ring_hole_edge_line_info"] = min([r for r in ring if abs(abs(r["delta_deg"]) - math.degrees(dmin)) <= 2e-3], key=lambda r: r["MS_PQ_2Fty"])
        o["ring_rows_z0"] = [r for r in ring if r["z_prime_mm"] == 0.0 and (r["delta_deg"] > 0)][::4]
        # nodal LC6 (S-AX basis) per zone
        vv = JP.vm(S[n01])
        Tc = Tn[n01] - TK
        Fy = np.array([JP.tab("AL6061-T6", "Fty", t) for t in Tc])
        Fu = np.array([JP.tab("AL6061-T6", "Ftu", t) for t in Tc])
        msy = Fy / (1.5 * np.maximum(vv, 1e-9)) - 1
        msu = Fu / (2.0 * np.maximum(vv, 1e-9)) - 1
        mspq = 2 * Fy / np.maximum(vv, 1e-9) - 1
        nod = {}
        for lab, msk in (("bore", zone & on_bore), ("OD_or_flat", zone & on_out), ("all_in_zone", zone), ("midbay_nodes", midbay)):
            if not msk.any():
                continue
            j = int(np.argmin(np.where(msk, msu, np.inf)))
            n = int(n01[j])
            nod[lab] = {"node": n + 1, "vm_MPa": round(float(vv[j]), 1), "T_C": round(float(Tc[j]), 1), "MS_LC6_y": round(float(msy[j]), 3),
                        "MS_LC6_u": round(float(msu[j]), 3), "MS_PQ_nodal_2Fty": round(float(mspq[j]), 3),
                        "r_az_z": [round(float(r_n[n]), 3), round(float(az_n[n]), 2), round(float(X[n, 2]), 3)], "z_prime": round(float(zp_n[n]), 3),
                        "d_hole_mm": round(float(d_hole[n]), 3), "n_nodes": int(msk.sum())}
        o["nodal_LC6"] = nod
        out["steps"][nm] = o
        g = o["midbay_governing"]
        print(nm, "midbay P+Q", {k_: g["PQ"][k_] for k_ in ("az_deg", "z_prime_mm", "PmPb", "T_mean_C", "MS_PQ_2Fty", "MS_LC6_SCL_y", "MS_LC6_SCL_u")},
              "| LC6 peak", {k_: g["LC6_peak_u"][k_] for k_ in ("az_deg", "z_prime_mm", "peak", "peak_at", "T_peak_C", "MS_LC6_peak_y", "MS_LC6_peak_u")})
        rg = o["ring_governing_excl_hole_edge_line"]
        print("   ring P+Q", {k_: rg["MS_PQ_2Fty"][k_] for k_ in ("delta_deg", "z_prime_mm", "PmPb", "MS_PQ_2Fty", "t_mm")},
              "| ring LC6 peak", {k_: rg["MS_LC6_peak_u"][k_] for k_ in ("delta_deg", "z_prime_mm", "peak", "peak_at", "MS_LC6_peak_y", "MS_LC6_peak_u")})
        for lab, v in nod.items():
            print("   nodal", lab, v)
    if UPTO is not None:
        out["partial_upto_ccx_step"] = UPTO
    (wd / ("midbay.json" if UPTO is None else "midbay_partial.json")).write_text(json.dumps(out, indent=1, default=float))


UPTO = None
if __name__ == "__main__":
    if len(sys.argv) > 2:
        UPTO = int(sys.argv[2])      # 08:40Z: partial post of a running job (ccx steps <= UPTO) -> midbay_partial.json
    main(sys.argv[1])
