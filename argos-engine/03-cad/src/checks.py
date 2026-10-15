"""Geometric verification of the posed assembly (CAD v3).  Every result is written to 03-cad/checks/ including
failures (brief: keep failing checks as evidence).

  * validity            BRepCheck on every part shape
  * reimport            STEP export -> re-import -> volume and bbox comparison (done in exports.py)
  * interference        boolean common volume between instances, all pairs at neutral, relatively moving pairs at
                        every pose of build.pose_list (range corners and the conical stop in 8 directions);
                        intended overlaps (threads modelled at the major diameter in minor-diameter holes) are
                        whitelisted with a reason
  * clearance           exact minimum distance (BRepExtrema) between relatively moving neighbours and to the
                        engine-bay wall (a tube of the required ID) at every pose
  * sweep               swept radius of the moving groups vs the engine-bay ID (zone and required ID)
"""
from __future__ import annotations
import math, json, time, itertools
import numpy as np
import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepCheck import BRepCheck_Analyzer
from geom import bbox, tube

# intended overlaps (modelled interference): (pnA, pnB) unordered -> reason
WHITELIST = {
    ("ENG-GM-18", "ENG-GM-01"): "M4 thread of the lever pivot stud in the tapped cheek (modelled at major/minor diameter)",
    ("ENG-GM-18", "ENG-GM-02"): "M4 thread of the lever pivot stud in the tapped cheek",
    ("ENG-GM-20", "ENG-GM-16"): "M4 thread of the horn-joint shoulder screw in the tapped horn eye",
    ("ENG-HW-25", "ENG-GM-15"): "M3 horn screw in the servo output shaft (shaft thread not modelled)",
    ("ENG-HW-25", "ENG-GM-16"): "countersunk M3 horn screw in the horn hub",
    ("ENG-TC-04", "ENG-TC-17"): "guide pins pressed in the bonnet flange (nominal press fit)",
    ("ENG-IG-01", "ENG-TC-02"): "torch M10x1 thread in the head port (envelope)",
    ("ENG-GM-15", "ENG-GM-16"): "servo spline inside the horn hub (spline modelled as a 6 mm cylinder in a 5.9 mm bore)",
    ("ENG-HW-22", "ENG-GM-17"): "GE outer ring pressed in the 14 N7 eye (nominal)",
    ("ENG-TC-03", "ENG-TC-02"): "M14x1 seat-insert thread modelled at the major diameter in the 13.0 tap drill",
    ("ENG-TC-14", "ENG-TC-13"): "servo spline inside the crank clamp hub (spline modelled as a 6 mm cylinder)",
    ("ENG-IG-02", "ENG-IG-01"): "cartridge check valves are inside the torch inlet bores (envelope)",
    ("ENG-FD-07", "ENG-FD-07A"): "hose end inside its crimp sleeve (the hose is crimped in the sleeve; the swept tube's end cap meets the sleeve "
                                 "face tilted by the hose polyline, 0.75 deg at neutral, and by the linear frame pose model at the corner poses)",
    ("ENG-FD-07", "ENG-FD-07B"): "hose end inside its crimp sleeve (as FD-07/FD-07A)",
    ("ENG-BL-04", "ENG-BL-04A"): "v3.5 bleed hose end at its crimp sleeve (end-cap tilt of the bundled pose model, as FD-07/FD-07A)",
    ("ENG-BL-04", "ENG-BL-04B"): "v3.5 bleed hose end at its crimp sleeve (as BL-04/BL-04A)",
}

# v3.4.1 rev B: parts whose CAD shape is intentionally more than one solid (every other part must be exactly one; rev A had the PD-04
# crankshaft as 3 disconnected solids and nobody flagged it)
EXPECTED_SOLIDS = {"ENG-GM-12": (2, "transport lock: 2 half rings"),
                   "ENG-PD-01": (2, "pintle drive frame: pieces A and B joined through PD-02")}

# v3.4.1 rev B: a whitelisted pair whose common volume exceeds its cap (mm3) is reported as NOT whitelisted (the reason above covers
# only the end-cap tilt: 15 mm3 = tilt of about 3 deg on the 16.2/10.5 mm hose section)
WHITELIST_CAP = {("ENG-FD-07", "ENG-FD-07A"): 15.0, ("ENG-FD-07", "ENG-FD-07B"): 15.0,
                 ("ENG-BL-04", "ENG-BL-04A"): 15.0, ("ENG-BL-04", "ENG-BL-04B"): 15.0}   # v3.5 bleed hose ends (6.4 mm section)

# designed contacts between RELATIVELY MOVING bodies (distance 0 is the design, not a clash): (pnA, pnB) -> reason;
# entries with a pose prefix apply only at those poses
EXPECTED_CONTACT = {
    ("ENG-GM-04", "ENG-HW-20"): "inner pin in the gimbal bearing bore (608 inner ring / v3.5.1 HK0808 needles run on the pin; bearing modelled as one solid)",
    ("ENG-GM-05", "ENG-HW-20"): "outer pin in the gimbal bearing bore (post bearings; 608 or v3.5.1 HK0808)",
    ("ENG-GM-06", "ENG-HW-20"): "inner-axis spacer / thrust washer on the bearing face (608 or v3.5.1 HK0808)",
    ("ENG-GM-07", "ENG-HW-20"): "outer-axis spacer / thrust washer on the bearing face (608 or v3.5.1 HK0808)",
    ("ENG-HW-21", "ENG-HW-20"): "DIN 6799 clip at the bearing face (axial float; 608 or v3.5.1 HK0808)",
    ("ENG-HW-22", "ENG-HW-22-IR"): "spherical sliding surface of the GE bearing",
    ("ENG-GM-11", "ENG-TC-01", "stop"): "conical PU bumper line contact with the case at the 8 deg stop (design)",
    ("ENG-EL-03", "ENG-EL-06"): "AS5048A chip-to-magnet air gap (inner axis, design 0.5-2 mm; reservation boxes 0.8 mm)",
    ("ENG-EL-04", "ENG-EL-06"): "AS5048A chip-to-magnet air gap (outer axis, design 0.5-2 mm; reservation boxes 0.8 mm)",
    # v3.5 (run 6): A1 head-end bleed joints (parts_bleed.py) - every one a designed face/port contact
    ("ENG-BL-01", "ENG-TC-04"): "bleed tap block seated on the TC-04 boss top (O-ring face seal, 2 x M2.5)",
    ("ENG-BL-01", "ENG-BL-03A"): "T4 leg tube end at the BL-01 port face (fitting TO-SELECT)",
    ("ENG-BL-02", "ENG-FD-01"): "tap adapter shoulder on the FD-01 +y face (M8x1, bonded seal)",
    ("ENG-BL-02", "ENG-BL-03A"): "T4 leg tube end at the BL-02 tee top port",
    ("ENG-BL-02", "ENG-BL-03E"): "common line tube end at the BL-02 tee bottom port",
    ("ENG-BL-03E", "ENG-BL-04A"): "common line tube end at the BL-04A elbow port",
    ("ENG-BL-03F", "ENG-BL-04B"): "fixed line tube end at the BL-04B sleeve stub",
    ("ENG-BL-03F", "ENG-BL-10"): "fixed line tube end at the BL-10 inlet fitting",
    ("ENG-BL-10", "ENG-BL-07"): "inlet fitting seated on the V1 pad edge",
    ("ENG-BL-05", "ENG-BL-07"): "bleed valve sub-base on its manifold pad",
    ("ENG-BL-08", "ENG-BL-07"): "P_mid transducer on the manifold boss",
    ("ENG-BL-06", "ENG-BL-07"): "vent bulkhead fitting on the V2 pad edge",
}


def _ec(a, b, pose=""):
    for k, why in EXPECTED_CONTACT.items():
        if {k[0], k[1]} == {a, b} and (len(k) == 2 or pose.startswith(k[2])):
            return why
    return ""


def _wl(a, b, v=None):
    why = WHITELIST.get((a, b)) or WHITELIST.get((b, a))
    cap = WHITELIST_CAP.get((a, b)) or WHITELIST_CAP.get((b, a))
    if why and cap is not None and v is not None and v > cap:
        return ""
    return why


def volume(shape):
    pr = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, pr)
    return pr.Mass()


def _common_raw(a, b):
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    op.SetFuzzyValue(1e-5)
    op.Build()
    if not op.IsDone():
        return float("nan")
    return volume(cq.Shape.cast(op.Shape()))


PERTURB_LOG = []


def common_volume(a, b, tol=0.5, d=3e-3):
    """Boolean common volume (mm3).  OCC returns wrong results for some solids that touch on coincident faces
    (v3.2: TC-08 seated on the TC-09 bore step gave the whole TC-08 volume, 38131 mm3, at every fuzzy value).
    When the raw result exceeds `tol`, b is shifted by +/-d mm along x, y and z and the smallest result is kept:
    a real overlap changes by ~area x d, a coincident-face artefact collapses to ~0.  Logged in PERTURB_LOG."""
    from geom import apply, T_trans
    v0 = _common_raw(a, b)
    if not (v0 > tol):
        return v0
    vals = [v0]
    for dx, dy, dz in ((0, 0, d), (0, 0, -d), (d, 0, 0), (-d, 0, 0), (0, d, 0), (0, -d, 0)):
        vals.append(_common_raw(a, apply(b, T_trans(dx, dy, dz))))
    v = min(x for x in vals if x == x)
    if v < 0.5 * v0:
        PERTURB_LOG.append({"raw_mm3": round(v0, 3), "perturbed_min_mm3": round(v, 3), "note": "coincident-face boolean artefact suppressed"})
    return v


def min_distance(a, b):
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    if not d.IsDone():
        return float("nan"), None, None
    p1, p2 = d.PointOnShape1(1), d.PointOnShape2(1)
    return d.Value(), (p1.X(), p1.Y(), p1.Z()), (p2.X(), p2.Y(), p2.Z())


def bb_overlap(b1, b2, pad=0.0):
    return not (b1[3] + pad < b2[0] or b2[3] + pad < b1[0] or b1[4] + pad < b2[1] or b2[4] + pad < b1[1]
                or b1[5] + pad < b2[2] or b2[5] + pad < b1[2])


def validity(reg):
    out = []
    for p in reg:
        ok = BRepCheck_Analyzer(p.shape.wrapped).IsValid()
        n = len(p.shape.Solids())
        exp = EXPECTED_SOLIDS.get(p.pn, (1, ""))
        out.append({"pn": p.pn, "valid": bool(ok), "n_solids": n, "n_solids_expected": exp[0], "solids_ok": n == exp[0],
                    "solids_note": exp[1]})
    return out


def interference_at_pose(inst, all_pairs, vol_tol=0.5):
    """inst: [(pn, idx, group, shape, body)].  all_pairs=True checks every pair (static assembly at neutral);
    otherwise only pairs on different rigid bodies (relative motion)."""
    bbs = [bbox(t[3]) for t in inst]
    hits = []
    for i, j in itertools.combinations(range(len(inst)), 2):
        pa, ia, ga, sa, ba = inst[i]
        pb, ib, gb, sb, bb_ = inst[j]
        if not all_pairs and ba == bb_:
            continue
        if not bb_overlap(bbs[i], bbs[j]):
            continue
        v = common_volume(sa, sb)
        if v > vol_tol:
            rec = {"a": f"{pa}#{ia}", "ga": ba, "b": f"{pb}#{ib}", "gb": bb_, "common_mm3": round(v, 2),
                   "whitelisted": _wl(pa, pb, v) or ""}
            if _wl(pa, pb) and not rec["whitelisted"]:
                rec["whitelist_cap_exceeded"] = True
            hits.append(rec)
    return hits


def clearances_at_pose(inst, pad=6.0, limit=3.0, pose=""):
    """Exact minimum distance for pairs on different rigid bodies whose boxes are within `pad` mm.  Returns pairs
    closer than `limit` (mm), each flagged with the designed-contact reason when it is one."""
    bbs = [bbox(t[3]) for t in inst]
    close = []
    for i, j in itertools.combinations(range(len(inst)), 2):
        pa, ia, ga, sa, ba = inst[i]
        pb, ib, gb, sb, bb_ = inst[j]
        if ba == bb_:
            continue
        if not bb_overlap(bbs[i], bbs[j], pad):
            continue
        if _wl(pa, pb):
            continue
        d, p1, p2 = min_distance(sa, sb)
        if d < limit:
            close.append({"a": f"{pa}#{ia}", "ga": ba, "b": f"{pb}#{ib}", "gb": bb_, "dist_mm": round(d, 3),
                          "at": [round(c, 1) for c in p1] if p1 else None, "expected_contact": _ec(pa, pb, pose)})
    return close


def wall_clearance(inst, R_bay, z0, z1, groups=None):
    """Minimum distance from every instance to the engine-bay wall (cylinder R_bay over z0..z1, mm)."""
    wall = tube(2 * R_bay + 20.0, 2 * R_bay, z0, z1)
    wb = bbox(wall)
    res = []
    for (pn, i, g, s, body) in inst:
        if groups is not None and g not in groups:
            continue
        b = bbox(s)
        rmax_box = max(math.hypot(x, y) for x in (b[0], b[3]) for y in (b[1], b[4]))
        if rmax_box < R_bay - 8.0 or b[5] < z0 or b[2] > z1:
            continue
        d, p1, p2 = min_distance(s, wall)
        res.append({"inst": f"{pn}#{i}", "group": g, "dist_mm": round(d, 3), "at": [round(c, 1) for c in p1] if p1 else None})
    return sorted(res, key=lambda r: r["dist_mm"])


def swept_radius(inst, groups, dz=5.0, tol=0.1):
    """Max radius per z band (dz) of the given groups from a fine tessellation with densified edges."""
    out = {}
    for (pn, i, g, s, body) in inst:
        if g not in groups:
            continue
        vs, ts = s.tessellate(tol, 0.2)
        V = np.array([[p.x, p.y, p.z] for p in vs])
        pts = [V]
        for t in ts:
            a, b, c = V[t[0]], V[t[1]], V[t[2]]
            for p, q in ((a, b), (b, c), (c, a)):
                L = np.linalg.norm(q - p)
                if L > 3.0:
                    n = int(L // 3.0) + 1
                    w = np.linspace(0, 1, n + 1)[1:-1, None]
                    pts.append(p + w * (q - p))
        Q = np.vstack(pts)
        r = np.hypot(Q[:, 0], Q[:, 1])
        kz = np.floor(Q[:, 2] / dz).astype(int)
        for k in np.unique(kz):
            m = r[kz == k].max()
            key = int(k)
            if m > out.get(key, (0, ""))[0]:
                out[key] = (float(m), f"{pn}#{i}")
    return out


# ------------------------------------------------------------------------------------------------ v3.5.1 bay-wall sweep (lead 182 (5))
BAY_SWEEP_RULE = ("every moving instance (rigid engine/ring/horn/pushrod groups with their kinematics and the flexible hoses FD-07/BL-04) "
                  "r <= R_bore - min_clear (lead CHANGELOG 182 (5) / 188 (2): 140 mm bore, >= 1.0 mm, i.e. r <= 69.0 mm) at every tilt "
                  "0..stop (1 deg steps, incl. 7 and 8 deg) in n_dir directions plus the stop polygon of build.pose_list; signed per instance; "
                  "r = distance from the bay (neutral engine) axis")
FIXED_WALL_RULE = ("every fixed instance r_max <= R_bore (on the bore, not in it; lead CHANGELOG 188 (2)) unless whitelisted as an intended "
                   "through-wall item")
FIXED_WALL_WHITELIST = {"ENG-BL-06": "V2 vent bulkhead fitting through the bay wall at az 112 (airframe ICD-14)"}


def bay_wall_sweep(reg, S, P, R_bore=70.0, min_clear=1.0, n_dir=72, dtheta=1.0, tol=0.05, refine_within=0.5, z_range=(-260.0, 380.0)):
    """Per moving instance: the largest radius from the bay axis over n_dir tilt directions x tilts 0..gimbal stop (step dtheta, deg).

    Moving = groups engine, ring, horn, pushrod (rigid, exact pose transforms of build.posed_instances) and the flexible hoses
    ENG-FD-07 / ENG-BL-04 (centreline of the pose model + OD/2: an upper bound).  Rigid parts: tessellation vertices (chordal
    tolerance tol); r is convex along straight edges, so the vertex maximum is exact for straight-edged faces and within tol for
    curved ones (r_ub = r_vertex + tol).  Points that cannot reach the part's neutral maximum (r + |z| sin(stop) below it) are
    pruned.  Instances within refine_within of the limit are re-measured exactly (BRepExtrema to the bore tube) at the worst pose.
    Discretisation: direction step 360/n_dir deg -> radius error <= |z| sin(stop) (1 - cos(half step)) (0.03 mm at z 250);
    tilt step dtheta -> <= |p| (dtheta/2)^2 / 2 (0.004 mm at 100 mm, 1 deg).  SIM (CAD geometry), no tolerance stack."""
    import build, parts_gimbal, parts_feed, tvc_kinematics as tk
    stop = float(P["gimbal_stop_deg"]["v"])
    lim = R_bore - min_clear
    thetas = list(np.arange(dtheta, stop + 1e-9, dtheta))
    if abs(thetas[-1] - stop) > 1e-9:
        thetas.append(stop)
    rng = float(P["gimbal_range_deg"]["v"])
    if all(abs(t - rng) > 1e-9 for t in thetas):
        thetas.append(rng)
    dirs = [k * 360.0 / n_dir for k in range(n_dir)]
    poses = [(0.0, 0.0, 0.0, 0.0)] + [(th, d) + tuple(tk.cone_to_ab(th, d)) for d in dirs for th in thetas]
    # v3.5.1 (lead 188 (2)): plus the stop polygon = every stop pose of build.pose_list (8 directions + the stop toward the fixed hose end)
    stop_poly = []
    for nm, a, b in build.pose_list(P, S):
        if nm.startswith("stop"):
            v = tk.R_pose(a, b) @ np.array([0.0, 0.0, 1.0])
            th_ = math.degrees(math.acos(max(-1.0, min(1.0, v[2]))))
            d_ = (math.degrees(math.atan2(-v[1], v[0])) if th_ > 1e-9 else 0.0) % 360.0
            poses.append((round(th_, 4), round(d_, 3), a, b))
            stop_poly.append({"pose": nm, "alpha_deg": round(a, 4), "beta_deg": round(b, 4), "tilt_deg": round(th_, 4)})
    track = {"range": rng, "stop": stop}
    frames = {i: parts_gimbal.tvc_pose_frames(S, a, b) for i, (th, d, a, b) in enumerate(poses)}
    sin_s = math.sin(math.radians(stop))
    res = []
    for p in reg:
        for k, (T, g) in enumerate(p.placements):
            grp = build.group_of(g)
            flex = grp in ("hose", "line") and p.pn in ("ENG-FD-07", "ENG-BL-04")
            if grp not in ("engine", "ring", "horn", "pushrod") and not flex:
                continue
            best = (-1.0, None, None)
            if flex:
                import parts_bleed
                od = (parts_bleed.BLEED["hose"]["od"] if p.pn == "ENG-BL-04" else parts_feed.FEED["hose"]["od"])
                per_tf = {kk_: -1.0 for kk_ in track}
                for i, (th, d, a, b) in enumerate(poses):
                    X = parts_feed.hose_centreline_at(S, a, b) if (th > 0) else np.asarray(S["feed"]["hose"], float)
                    if p.pn == "ENG-BL-04":
                        X = parts_bleed.hose_offset(S["feed"]["hose"], X, tk.R_pose(a, b)) if th > 0 else parts_bleed.hose_offset(S["feed"]["hose"])
                    X = X[(X[:, 2] >= z_range[0]) & (X[:, 2] <= z_range[1])]
                    if not len(X):
                        continue
                    r = np.hypot(X[:, 0], X[:, 1]) + od / 2.0
                    j = int(np.argmax(r))
                    for kk_, tt_ in track.items():
                        if abs(th - tt_) < 1e-6 and r[j] > per_tf[kk_]:
                            per_tf[kk_] = float(r[j])
                    if r[j] > best[0]:
                        best = (float(r[j]), i, X[j])
                res.append({"inst": f"{p.pn}#{k}", "pn": p.pn, "group": grp, "kind": "flex (centreline + OD/2 upper bound)",
                            "r_at_range_mm": round(per_tf["range"], 3), "r_at_stop_mm": round(per_tf["stop"], 3),
                            "r_max_mm": round(best[0], 3), "r_ub_mm": round(best[0], 3),
                            "pose": {"tilt_deg": poses[best[1]][0], "dir_deg": poses[best[1]][1], "alpha_deg": round(poses[best[1]][2], 3),
                                     "beta_deg": round(poses[best[1]][3], 3)}, "at_mm": [round(float(c), 2) for c in best[2]],
                            "clear_to_bore_mm": round(R_bore - best[0], 3), "ok": bool(best[0] <= lim)})
                continue
            per_t = {kk_: -1.0 for kk_ in track}
            vs, _ = p.shape.tessellate(tol, 0.1)
            V = np.array([[v.x, v.y, v.z] for v in vs])
            if not len(V):
                continue
            V4 = np.c_[V, np.ones(len(V))]
            for i, (th, d, a, b) in enumerate(poses):
                if grp == "horn":
                    Tp = frames[i][int(g.split(":")[1])]["horn"]
                elif grp == "pushrod" or g.startswith("pushrod:"):
                    _, kk, item = g.split(":")
                    Tp = frames[i][int(kk)][item]
                else:
                    Tp = build.group_T(grp, a, b) @ T
                Y = (V4 @ Tp.T)[:, :3]
                if i == 0 and grp in ("engine", "ring"):
                    r0 = np.hypot(Y[:, 0], Y[:, 1])
                    keep = (r0 + np.abs(Y[:, 2]) * sin_s + 0.01) >= r0.max()
                    V4 = (np.c_[Y[keep], np.ones(int(keep.sum()))] @ np.linalg.inv(Tp).T)      # pruned set back in the part frame
                    Y = Y[keep]
                m = (Y[:, 2] >= z_range[0]) & (Y[:, 2] <= z_range[1])
                if not m.any():
                    continue
                r = np.hypot(Y[m, 0], Y[m, 1])
                j = int(np.argmax(r))
                for kk_, tt_ in track.items():
                    if abs(th - tt_) < 1e-6 and r[j] > per_t[kk_]:
                        per_t[kk_] = float(r[j])
                if r[j] > best[0]:
                    best = (float(r[j]), i, Y[m][j])
            if best[1] is None:
                continue
            th, d, a, b = poses[best[1]]
            res.append({"inst": f"{p.pn}#{k}", "pn": p.pn, "group": grp, "kind": "rigid (tessellation vertices)",
                        "r_at_range_mm": round(per_t["range"], 3), "r_at_stop_mm": round(per_t["stop"], 3),
                        "tilt_to_limit_deg": (round(stop + (lim - per_t["stop"]) / max(per_t["stop"] - per_t["range"], 1e-6) * (stop - rng), 2)
                                              if per_t["stop"] > per_t["range"] + 1e-6 else None),
                        "r_max_mm": round(best[0], 3), "r_ub_mm": round(best[0] + tol, 3),
                        "pose": {"tilt_deg": th, "dir_deg": d, "alpha_deg": round(a, 3), "beta_deg": round(b, 3)},
                        "at_mm": [round(float(c), 2) for c in best[2]], "clear_to_bore_mm": round(R_bore - best[0] - tol, 3),
                        "ok": bool(best[0] + tol <= lim)})
    # exact re-measure near or over the limit (BRepExtrema to the bore tube at the worst pose)
    by_inst = {}
    for r in res:
        if r["kind"].startswith("rigid") and r["r_ub_mm"] > lim - refine_within:
            by_inst.setdefault((r["pose"]["alpha_deg"], r["pose"]["beta_deg"]), []).append(r)
    for (a, b), rows in by_inst.items():
        inst = {f"{pn}#{i}": s for (pn, i, gg, s, body) in build.posed_instances(reg, S, a, b, groups=("engine", "ring", "horn", "pushrod"))}
        wall = tube(2 * R_bore + 20.0, 2 * R_bore, z_range[0], z_range[1])
        for r in rows:
            s = inst.get(r["inst"])
            if s is None:
                continue
            dist, p1, p2 = min_distance(s, wall)
            r["exact_dist_to_bore_mm"] = round(dist, 3)
            r["exact_note"] = "BRepExtrema distance to the bore tube at the worst sampled pose (0 = touching or crossing the bore)"
            if dist > 1e-6:
                r["clear_to_bore_mm"] = round(dist, 3)
                r["ok"] = bool(dist >= min_clear)
    res.sort(key=lambda r: r["clear_to_bore_mm"])
    return {"rule": BAY_SWEEP_RULE, "R_bore_mm": R_bore, "min_clear_mm": min_clear, "r_limit_mm": lim, "stop_deg": stop,
            "signed": "clear_to_bore_mm = R_bore - r_ub (negative = inside the wall); ok = clear_to_bore_mm >= min_clear",
            "stop_polygon_poses": stop_poly, "range_deg": rng,
            "n_dir": n_dir, "tilts_deg": [round(t, 3) for t in thetas], "n_poses": len(poses), "z_range_mm": list(z_range),
            "n_instances": len(res), "fail": [r["inst"] for r in res if not r["ok"]], "rows": res}


def fixed_wall_check(reg, S, R_bore=70.0, tol=0.05, z_range=(-260.0, 380.0), whitelist=None):
    """Fixed instances (group fixed; the fixed halves of flexible items are covered by the moving sweep) against the bore: r_max of the
    tessellation vertices + tol, signed (r_max - R_bore > 0 = into the wall), exact BRepExtrema penetration test for instances within
    0.2 mm of the bore.  Pass: r <= R_bore (+0.01 mm modelling contact) or whitelisted.  SIM (CAD geometry), no tolerance stack."""
    import build
    wl = dict(FIXED_WALL_WHITELIST if whitelist is None else whitelist)
    rows = []
    wall = tube(2 * R_bore + 20.0, 2 * R_bore, z_range[0], z_range[1])
    for pn, i, grp, shp, body in build.posed_instances(reg, S, 0.0, 0.0):
        if grp != "fixed":
            continue
        vs, _ = shp.tessellate(tol, 0.1)
        V = np.array([[v.x, v.y, v.z] for v in vs])
        if not len(V):
            continue
        m = (V[:, 2] >= z_range[0]) & (V[:, 2] <= z_range[1])
        if not m.any():
            continue
        r = np.hypot(V[m, 0], V[m, 1])
        rmax = float(r.max())
        row = {"inst": f"{pn}#{i}", "pn": pn, "r_max_mm": round(rmax, 3), "into_wall_mm": round(rmax - R_bore, 3),
               "whitelisted": pn in wl, "whitelist_reason": wl.get(pn, "")}
        if rmax > R_bore - 0.2:
            inter = shp.intersect(wall)
            vol = float(sum(sol.Volume() for sol in inter.Solids())) if inter is not None else 0.0
            row["volume_beyond_bore_mm3"] = round(vol, 4)
        row["ok"] = bool(row["whitelisted"] or (rmax <= R_bore + 0.01 and row.get("volume_beyond_bore_mm3", 0.0) < 1e-3))
        rows.append(row)
    rows.sort(key=lambda q: -q["r_max_mm"])
    return {"rule": FIXED_WALL_RULE, "R_bore_mm": R_bore, "whitelist": wl, "n_instances": len(rows),
            "fail": [q["inst"] for q in rows if not q["ok"]], "rows": rows}
