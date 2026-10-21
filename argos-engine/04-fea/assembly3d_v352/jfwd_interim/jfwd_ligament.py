"""J-FWD TC-01 net-ligament SCL averaged across the ligament (fea3d 2026-10-20 ~07:05Z; replaces the 'TC01_net_ligament_hole_flank'
lines of jfwd_post.py as the CHANGELOG 231 (1)(i) net-ligament value).  DERIVED from the SIM stress field of the run (.frd / .frd.gz,
streamed), no new run.

Why: the jfwd_post.py hole-flank line (offset 2.80 mm from the hole axis, then turned radial through its mid-point azimuth) lies, over its
inner ~1.1 mm, up to 0.11 mm INSIDE the hole (radial line at 5.30 deg: r sin(5.30 deg) < 2.75 for r < 29.77), so it was extrapolated
(min barycentric -0.20 / -0.34); and a hole-edge line carries the in-plane concentration, which for a typical ligament of a uniform hole
pattern is peak F (ASME VIII-2 Table 5.6, 'perforated shell, typical ligament': Pm = membrane averaged through the ligament cross section,
Pb = bending averaged across the ligament width with its gradient through the plate, peak F).

Per frd step:
  * ligament average on the hole-centre plane z = Z_SCREW - shift, TC-01 net section r 28.627 .. 31.748, az 0 .. 18 - asin(2.75 / r) and
    18 + asin(2.75 / r) .. 36 (the hole cut exactly): Gauss-Legendre in r and az, dA = r dr dtheta, stress tensor rotated to (r, theta, z)
    at each point before averaging; Pm = vM(<s>), Pm+Pb = max vM(<s> +- <s_b>), <s_b> = (6 / A) int s (0.5 - (r - r_in) / t) dA;
    per side and both sides (by cyclic symmetry the two sides are the two halves of one full ligament); the section force int s_zz dA is
    printed as a check against the screw load;
  * stations: full-wall radial lines at azimuth offsets delta >= asin(2.76 / 28.627) (wholly in the material), linearised in (r, theta, z);
    the first station is the corrected hole-edge line (local, in-plane Kt: information, the local check is the Neuber (iii));
  * spot-face sensitivity (lead 06:17Z, DERIVED): per station the local wall t'(delta) = min(R_OD, 31.313 / cos(delta)) - R_bore
    (d10.5 flat at x' 31.313), membrane x t / t', bending x (t / t')^2 (same force and moment per unit width), recombined:
    Pm' = sum(s_m t dw) / sum(t' dw), Pb' = sum(k^2 s_b dw) / sum(dw);
  * TC-02 band also excluding 1 mm about the TC-01 hole-edge footprint on the TC-02 OD (the FIT contact edge), beside the published band
    (> 1 mm from the tap), and the position of the FIT CPRESS maximum against that footprint.
usage: jfwd_ligament.py JOB  -> jfwd/runs/JOB/ligament.json"""
from __future__ import annotations
import sys, json, math, gzip
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_sub as JS     # noqa: E402
import jfwd_deck as JD    # noqa: E402
import jfwd_post as JP    # noqa: E402

R_IN, R_OUT = JS.R_BORE01 + 0.002, JS.R_OD - 0.002
X_SEAT = 31.313
HR = JS.GEO["hole_r"]


def cyl(Sv, az):
    """(n,6) global [xx yy zz xy yz zx] -> (n,3,3) in (r, theta, z) at azimuth az (rad)."""
    s = np.zeros((len(Sv), 3, 3))
    s[:, 0, 0], s[:, 1, 1], s[:, 2, 2] = Sv[:, 0], Sv[:, 1], Sv[:, 2]
    s[:, 0, 1] = s[:, 1, 0] = Sv[:, 3]
    s[:, 1, 2] = s[:, 2, 1] = Sv[:, 4]
    s[:, 0, 2] = s[:, 2, 0] = Sv[:, 5]
    c, sn = np.cos(az), np.sin(az)
    R = np.zeros((len(Sv), 3, 3))
    R[:, 0, 0], R[:, 0, 1] = c, sn
    R[:, 1, 0], R[:, 1, 1] = -sn, c
    R[:, 2, 2] = 1.0
    return np.einsum("nij,njk,nlk->nil", R, s, R)


def vm33(s):
    s = np.asarray(s)
    return float(math.sqrt(0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2)
                           + 3 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[0, 2] ** 2)))


def t6(s):
    return [round(float(s[0, 0]), 2), round(float(s[1, 1]), 2), round(float(s[2, 2]), 2),
            round(float(s[0, 1]), 2), round(float(s[1, 2]), 2), round(float(s[0, 2]), 2)]


def lig_average(loc, S, zc, nr=10, naz=48):
    """2026-10-20 08:35Z: on a spot-face mesh the section also excludes the material removed by the d10.5 flat (r > x_seat / cos(delta)
    for |delta| < acos(x_seat / r)), and the through-wall coordinate of the bending weight uses the local wall t(delta) = r_out - R_IN."""
    gr, wr = np.polynomial.legendre.leggauss(nr)
    ga, wa = np.polynomial.legendre.leggauss(naz)
    out = {}
    tot = {"A": 0.0, "Sm": np.zeros((3, 3)), "Sb": np.zeros((3, 3)), "Fz": 0.0, "minb": 1.0}
    t = R_OUT - R_IN
    spot = JS.GEO.get("seat") == "spot"
    xs = JS.GEO.get("x_seat", JS.R_OD) - 0.002
    for side in ("-", "+"):
        P, W, AZ, SS = [], [], [], []
        for xi, wi in zip(gr, wr):
            r = R_IN + 0.5 * (xi + 1) * t
            dh = math.asin(min(HR / r, 1.0))
            if spot and r > xs:
                dh = max(dh, math.acos(min(xs / r, 1.0)))
            if side == "-":
                a0, a1 = math.radians(0.02), math.radians(JS.AZ_SCREW) - dh
            else:
                a0, a1 = math.radians(JS.AZ_SCREW) + dh, math.radians(JS.SECTOR - 0.02)
            az = a0 + 0.5 * (ga + 1) * (a1 - a0)
            w = wi * 0.5 * t * wa * 0.5 * (a1 - a0) * r
            P.append(np.column_stack([r * np.cos(az), r * np.sin(az), np.full(naz, zc)]))
            W.append(w)
            AZ.append(az)
            tl = np.array([JS.r_out(a_ - math.radians(JS.AZ_SCREW), 0.0) - R_IN for a_ in az]) if spot else np.full(naz, t)
            SS.append((r - R_IN) / tl)
        P, W, AZ, SS = np.vstack(P), np.concatenate(W), np.concatenate(AZ), np.concatenate(SS)
        Sv, best = loc.interp(S, P)
        sc = cyl(Sv, AZ)
        A = W.sum()
        Sm = np.einsum("n,nij->ij", W, sc) / A
        Sb = 6.0 * np.einsum("n,nij->ij", W * (0.5 - SS), sc) / A
        Fz = float((W * sc[:, 2, 2]).sum())
        out["side" + side] = {"A_mm2": round(float(A), 3), "width_mid_mm": round(float(A / t), 3), "Pm": round(vm33(Sm), 1),
                              "PmPb": round(max(vm33(Sm + Sb), vm33(Sm - Sb)), 1), "s_m_rtz": t6(Sm), "s_b_rtz": t6(Sb),
                              "Fz_N": round(Fz, 1), "min_bary": round(float(best.min()), 4)}
        tot["A"] += A
        tot["Sm"] += Sm * A
        tot["Sb"] += Sb * A
        tot["Fz"] += Fz
        tot["minb"] = min(tot["minb"], float(best.min()))
    Sm, Sb = tot["Sm"] / tot["A"], tot["Sb"] / tot["A"]
    out["both"] = {"A_mm2": round(tot["A"], 3), "Pm": round(vm33(Sm), 1), "PmPb": round(max(vm33(Sm + Sb), vm33(Sm - Sb)), 1),
                   "s_m_rtz": t6(Sm), "s_b_rtz": t6(Sb), "Fz_N": round(tot["Fz"], 1), "min_bary": round(tot["minb"], 4)}
    return out


def station(loc, S, zc, az, n=41, ro=None):
    ro = R_OUT if ro is None else ro
    a = np.array([R_IN * math.cos(az), R_IN * math.sin(az), zc])
    b = np.array([ro * math.cos(az), ro * math.sin(az), zc])
    s = np.linspace(0, 1, n)
    P = a[None] + s[:, None] * (b - a)[None]
    Sv, best = loc.interp(S, P)
    sc = cyl(Sv, np.full(n, az))
    sm = np.trapezoid(sc, s, axis=0)
    sb = 6.0 * np.trapezoid(sc * (0.5 - s)[:, None, None], s, axis=0)
    return sm, sb, float(best.min())


def stations(loc, S, zc, nst=40):
    """both sides; delta from asin(2.76 / R_IN) to the sector boundary; returns list of dicts and the seat-scaled ligament average."""
    dmin = math.asin((HR + 0.01) / R_IN)
    dmax = math.radians(JS.AZ_SCREW - 0.02)
    edges = np.linspace(dmin, dmax, nst + 1)
    mids = 0.5 * (edges[1:] + edges[:-1])
    dws = (edges[1:] - edges[:-1]) * 0.5 * (R_IN + R_OUT)
    t = R_OUT - R_IN
    rows, acc = [], {"cad": [np.zeros((3, 3)), np.zeros((3, 3)), 0.0, 0.0], "seat": [np.zeros((3, 3)), np.zeros((3, 3)), 0.0, 0.0]}
    minb = 1.0
    smax = {"cad": None, "seat": None}
    spot = JS.GEO.get("seat") == "spot"
    for d, dw in zip(mids, dws):
        tp = min(JS.R_OD, X_SEAT / math.cos(d)) - JS.R_BORE01
        k = JS.R_OD - JS.R_BORE01
        k = k / tp
        ro = JS.r_out(d, 0.0) if spot else None
        if spot:                       # 08:35Z: spot-face mesh: the FE wall is the seat wall; no scaling ('cad' = 'seat' = FE geometry)
            k = 1.0
            t = ro - R_IN
            tp = t
        for sgn in (-1, +1):
            az = math.radians(JS.AZ_SCREW) + sgn * d
            sm, sb, bb = station(loc, S, zc, az, ro=ro)
            minb = min(minb, bb)
            # CAD: area-weighted membrane, width-weighted bending
            acc["cad"][0] += sm * t * dw
            acc["cad"][1] += sb * dw
            acc["cad"][2] += t * dw
            acc["cad"][3] += dw
            acc["seat"][0] += sm * t * dw          # same force per unit width on the thinner wall
            acc["seat"][1] += (k ** 2) * sb * dw
            acc["seat"][2] += tp * dw
            acc["seat"][3] += dw
            for key, kk in (("cad", 1.0), ("seat", k)):
                pq = max(vm33(kk * sm + kk * kk * sb), vm33(kk * sm - kk * kk * sb))
                if smax[key] is None or pq > smax[key]["PmPb"]:
                    smax[key] = {"PmPb": round(pq, 1), "Pm": round(vm33(kk * sm), 1), "delta_deg": round(math.degrees(d), 3),
                                 "side": "+" if sgn > 0 else "-", "t_mm": round(tp if key == "seat" else t, 3), "min_bary": round(bb, 4)}
            if d == mids[0] or abs(d - mids[len(mids) // 4]) < 1e-12 or abs(d - mids[len(mids) // 2]) < 1e-12 or d == mids[-1]:
                rows.append({"delta_deg": round(math.degrees(d), 3), "side": "+" if sgn > 0 else "-",
                             "y_mid_mm": round(0.5 * (R_IN + R_OUT) * math.sin(d), 3), "t_seat_mm": round(tp, 3),
                             "Pm": round(vm33(sm), 1), "PmPb": round(max(vm33(sm + sb), vm33(sm - sb)), 1),
                             "Pm_seat": round(vm33(k * sm), 1), "PmPb_seat": round(max(vm33(k * sm + k * k * sb), vm33(k * sm - k * k * sb)), 1),
                             "min_bary": round(bb, 4)})
    res = {}
    for key, (Sm, Sb, A, Wd) in acc.items():
        Sm_, Sb_ = Sm / A, Sb / Wd
        res[key] = {"Pm": round(vm33(Sm_), 1), "PmPb": round(max(vm33(Sm_ + Sb_), vm33(Sm_ - Sb_)), 1), "s_m_rtz": t6(Sm_), "s_b_rtz": t6(Sb_),
                    "station_max_PmPb": smax[key]}
    return rows, res, minb


def wall_scl(loc, S, P0, d, step=0.02, smax=40.0, tol=-0.05, n=41):
    """SCL from P0 (a surface node) along the unit direction d to the first exit from the body mesh (best bary < tol); linearised
    in the global components (the line has one direction).  Returns t, Pm, Pm+Pb, peak, end point."""
    ss = np.arange(0.002, smax, step)
    P = P0[None] + ss[:, None] * d[None]
    _, _, best = loc.bary(P)
    out = np.nonzero(best < tol)[0]
    s_end = float(ss[out[0] - 1]) if len(out) else float(ss[-1])
    a, b = P0 + 0.002 * d, P0 + s_end * d
    r = JP.linearise(loc, S, a, b, n=n)
    r.update({"from_mm": [round(float(c), 3) for c in a], "to_mm": [round(float(c), 3) for c in b], "dir": [round(float(c), 4) for c in d]})
    return r


def edge_profile(vm_n, dist, Fty, bins=((0.0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 4.0))):
    """RM2-01 (f) form: max von Mises and MS_y (SF 1) per distance band from the hole / tap surface."""
    rows = []
    for lo, hi in bins:
        m = (dist >= lo) & (dist < hi)
        if not m.any():
            continue
        j = int(np.argmax(np.where(m, vm_n, -1)))
        rows.append({"band_mm": [lo, hi], "vm_max_MPa": round(float(vm_n[j]), 1), "MS_y_SF1": round(float(Fty[j] / max(vm_n[j], 1e-9) - 1), 3),
                     "local_index": j})
    return rows


def main(job):
    wd = JD.RUNS / job
    meta = json.loads((wd / "meta.json").read_text())
    tag = meta["mesh"]
    JS.use_mesh(tag)                 # 08:35Z: seat geometry (spot face)
    m = dict(np.load(JD.OUT / f"model_{tag}.npz", allow_pickle=False))
    mj = json.loads((JD.OUT / f"mesh_{tag}.json").read_text())
    shift = mj["shift"]
    X, T, B = m["X"], m["T"], m["B"]
    frd = wd / f"{job}.frd"
    if frd.exists():
        by_step = JP.read_frd_steps(frd, len(X), UPTO)
    else:
        JP.open = lambda p, mode="r", errors=None: gzip.open(str(p) + ".gz", "rt", errors=errors)   # stream the .frd.gz
        try:
            by_step = JP.read_frd_steps(frd, len(X))
        finally:
            del JP.open
    names = meta["steps"]
    loc01 = JP.Locator(X, T[np.nonzero(B == "TC-01")[0]])
    loc02 = JP.Locator(X, T[np.nonzero(B == "TC-02")[0]])
    n01 = m["n01"]
    # fea3d 09:56Z: a partial run has no post.json yet -> take the step temperatures from post_partial.json (before: 20 C fallback)
    post = {"steps": {}}
    for _pf in ("post.json", "post_partial.json"):
        if (wd / _pf).exists():
            post = json.loads((wd / _pf).read_text())
            break
    _, _, _, ra1 = JD.loc(X, -shift)
    d_hole = ra1 - HR
    zc = JS.Z_SCREW - shift
    n02 = m["n02"]
    xa, ya, za, ra = JD.loc(X)
    d_tap = np.where(xa >= JS.GEO["x_tap_lo"], np.abs(ra - JS.GEO["shank_r"]),
                     np.hypot(np.maximum(ra - JS.GEO["shank_r"], 0.0), JS.GEO["x_tap_lo"] - xa))
    psi = np.linspace(0, 2 * math.pi, 2880, endpoint=False)
    yp, zp = HR * np.cos(psi), HR * np.sin(psi)
    xp = np.sqrt(JS.R_BORE01 ** 2 - yp ** 2)
    E = JD.C0[None] + np.array([0, 0, -shift])[None] + xp[:, None] * JD.EN[None] + yp[:, None] * JD.ET1[None] + zp[:, None] * JD.ET2[None]
    d_e01 = cKDTree(E).query(X[n02])[0]
    out = {"job": job, "doc": __doc__.split("usage:")[0].strip(), "z_hole_plane": round(zc, 3), "shift": shift, "seat": JS.GEO.get("seat"),
           "note_seat": ("spot-face mesh: 'ligament_avg_CAD' and the 'cad' / 'seat' station averages are all on the FE spot-face geometry "
                         "(no scaling)") if JS.GEO.get("seat") == "spot" else "CAD seat mesh; 'seat' = [DERIVED] spot-face scaling", "steps": {}}
    for k, nm in enumerate(names):
        if (k + 1) not in by_step:
            continue
        F = by_step[k + 1]
        S = F["STRESS"]
        o = {"ligament_avg_CAD": lig_average(loc01, S, zc)}
        rows, res, minb = stations(loc01, S, zc)
        o["stations"] = rows
        o["station_average"] = res
        o["stations_min_bary"] = round(minb, 4)
        # TC-02 band variants
        s2 = JP.vm(S[n02])
        rec = {}
        for lab, msk in (("band_gt1_tap", d_tap[n02] > 1.0), ("band_gt1_tap_and_gt1_TC01_hole_edge", (d_tap[n02] > 1.0) & (d_e01 > 1.0))):
            j = int(np.argmax(np.where(msk, s2, -1)))
            rec[lab] = {"vm_MPa": round(float(s2[j]), 1), "node": int(n02[j]) + 1, "X_mm": X[n02[j]].round(3).tolist(),
                        "x_prime": round(float(xa[n02[j]]), 3), "d_tap_mm": round(float(d_tap[n02[j]]), 3), "d_TC01_hole_edge_mm": round(float(d_e01[j]), 3)}
        o["TC02_band"] = rec
        # TC-02 through-wall SCL at the band node of this step and at node 13503 (lead 07:21Z condition): radial, inward from the OD
        pst = post["steps"].get(nm, {})
        T02 = float(pst.get("TC-02", {}).get("band", {}).get("T_C", 20.0)) if pst else 20.0
        Fty2 = JP.tab("AL6061-T6", "Fty", T02)
        Ftu2 = JP.tab("AL6061-T6", "Ftu", T02)
        walls = {}
        for lab, nid in (("node_13503", 13503), ("band_node", rec["band_gt1_tap"]["node"])):
            P0 = X[nid - 1]
            er = np.array([P0[0], P0[1], 0.0]) / math.hypot(P0[0], P0[1])
            w_ = wall_scl(loc02, S, P0, -er)
            w_.update({"node": nid, "T_C": T02, "Fty_MPa": round(Fty2, 1), "Ftu_MPa": round(Ftu2, 1),
                       "MS_y_Pm_SF1": round(Fty2 / max(w_["Pm"], 1e-9) - 1, 3), "MS_y_PmPb_SF1": round(Fty2 / max(w_["PmPb"], 1e-9) - 1, 3),
                       "MS_u_Pm_SF1": round(Ftu2 / max(w_["Pm"], 1e-9) - 1, 3), "MS_u_PmPb_SF1": round(Ftu2 / max(w_["PmPb"], 1e-9) - 1, 3)})
            walls[lab] = w_
        o["TC02_wall_SCL"] = walls
        # RM2-01 (f) hole-edge profiles (max vM per distance band; MS_y at SF 1 against Fty at the node temperature of the post)
        prof = {}
        for part, nodes, dist in (("TC-01", n01, d_hole), ("TC-02", n02, d_tap)):
            Tp = float(pst.get(part, {}).get("band", {}).get("T_C", 20.0)) if pst else 20.0
            Fty_p = np.full(len(nodes), JP.tab("AL6061-T6", "Fty", Tp))
            vv = JP.vm(S[nodes])
            rows_ = edge_profile(vv, dist[nodes], Fty_p)
            for r_ in rows_:
                j = r_.pop("local_index")
                r_["node"] = int(nodes[j]) + 1
                r_["T_C_used"] = Tp
            prof[part] = rows_
        o["edge_profile_RM2_01f"] = prof
        if "CONTACT" in F:
            C = F["CONTACT"]
            cp = C[:, 3] if C.shape[1] > 3 else None
            if cp is not None:
                j = int(np.argmax(np.where(np.isin(np.arange(len(X)), n02), np.abs(cp), -1)))
                o["FIT_CPRESS_max_on_TC02"] = {"CPRESS_MPa": round(float(abs(cp[j])), 1), "node": j + 1, "X_mm": X[j].round(3).tolist(),
                                               "d_tap_mm": round(float(d_tap[j]), 3),
                                               "d_TC01_hole_edge_mm": round(float(cKDTree(E).query(X[j])[0]), 3)}
        out["steps"][nm] = o
        lb = o["ligament_avg_CAD"]["both"]
        print(nm, "lig CAD both Pm %.1f PmPb %.1f Fz %.1f A %.2f minb %.3f | -: %s | +: %s | stations CAD %s seat %s | TC02 %s | %s" % (
            lb["Pm"], lb["PmPb"], lb["Fz_N"], lb["A_mm2"], lb["min_bary"],
            {k_: o["ligament_avg_CAD"]["side-"][k_] for k_ in ("Pm", "PmPb", "Fz_N")}, {k_: o["ligament_avg_CAD"]["side+"][k_] for k_ in ("Pm", "PmPb", "Fz_N")},
            {k_: res["cad"][k_] for k_ in ("Pm", "PmPb", "station_max_PmPb")}, {k_: res["seat"][k_] for k_ in ("Pm", "PmPb", "station_max_PmPb")},
            {k_: (v["vm_MPa"], v["d_tap_mm"], v["d_TC01_hole_edge_mm"]) for k_, v in rec.items()}, o.get("FIT_CPRESS_max_on_TC02")))
        for r_ in rows:
            print("    ", r_)
    if UPTO is not None:
        out["partial_upto_ccx_step"] = UPTO
    (wd / ("ligament.json" if UPTO is None else "ligament_partial.json")).write_text(json.dumps(out, indent=1, default=float))


UPTO = None
if __name__ == "__main__":
    if len(sys.argv) > 2:
        UPTO = int(sys.argv[2])      # 08:35Z: partial post of a running job (ccx steps <= UPTO)
    main(sys.argv[1])
