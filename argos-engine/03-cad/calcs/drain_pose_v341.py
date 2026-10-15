"""DRAIN POSE screen (research hypothesis, coordinator 2026-10-13): can a gimbal pose within the 7 deg command cone, set from the
measured specific-force direction, make the FD-07 hose rise monotonically toward its fixed end at a vehicle tilt?  (v1, Mechanical)

Hypothesis H-DP: for a vehicle tilt theta_v toward az psi (specific force -u, u = 'up' in the airframe frame), some gimbal pose
(alpha, beta) with |pose| <= 7 deg leaves no vapour pocket in the hose (hose bore pocket <= 0.5 cm3, the bore-step micro-trap allowance
of segment_traps v1.3) with the posed hose >= 3 mm from the bay wall, the case and the TEE/riser.
Comparator: neutral pose (0, 0).  Refuted if no pose clears the hose at 10 deg in the worst direction, or if the clearing pose breaks a
clearance.  Tested at theta_v = 2, 4, 10 deg in 8 directions (0 deg for reference).
Model: the path proxy of coil_tilt_screen_v341 (series path TEE side passage -> FD-07A -> hose -> FD-07B -> fixed leg -> 30 mm into
the vertical wall line; at every point the bore volume above the lowest crown ahead of it is a pocket) with the engine-side items
rotated by R_pose(alpha, beta) and the hose at the posed linear-frame shape parts_feed.hose_centreline_at (uniform EI: the shape does
not depend on EI); FD-07B, the fixed leg and the wall line stay with the airframe.  Poses: 1 deg grid inside the 7 deg cone (149).
Clearances as coil_reroute_v341.evaluate (bay wall r 70, case r 31.75 about the posed engine axis, TEE/riser), at every pose.
Proxy only (centreline pockets, quasi-static hose, no hose sag under 8 m/s2 or pressure); a chosen pose would need segment_traps on the
posed CAD.  Output: calcs/drain_pose_v341_v1.json.  RESEARCH PROPOSAL screen, DERIVED from the CAD v3.4.1 route.
"""
from __future__ import annotations
import json, math, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import parts_feed as pf
import tvc_kinematics as tk
import coil_reroute_v341 as cr
from coil_tilt_screen_v341 import pockets, A_HOSE, A_TUBE

OUT = HERE / "drain_pose_v341_v1.json"
CONE = 7.0
MICRO = 0.5


def series_path_pose(f, S, a, b):
    R = tk.R_pose(a, b)
    t = pf.FEED["tee"]
    d = f["d"]
    P0 = f["Pe"] - (t["side_socket_depth"] + 3.0) * d
    pts, rad, part = [], [], []
    for s in np.linspace(0.0, 1.0, 12):
        pts.append(R @ (P0 + s * (f["Q"] - P0))); rad.append(A_TUBE); part.append("FD-07A/TEE side")
    H = pf.hose_centreline_at(S, a, b)
    for p in H[1:]:
        pts.append(p); rad.append(A_HOSE); part.append("hose")
    for s in np.linspace(0.0, 1.0, 12)[1:]:
        pts.append(f["Fq"] + s * (f["Fe"] - f["Fq"])); rad.append(A_TUBE); part.append("FD-07B")
    wall = np.asarray(f["wall"])
    k_top = int(np.argmax(wall[:, 2] >= f["V0"][2] + 30.0))
    for p in wall[1:k_top]:
        pts.append(p); rad.append(A_TUBE); part.append("fixed leg + wall foot")
    return np.array(pts), np.array(rad), np.array(part), H, R


def clearances(f, H, R):
    t = pf.FEED["tee"]
    od = pf.FEED["hose"]["od"]
    s_arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(H, axis=0), axis=1))])
    r = np.hypot(H[:, 0], H[:, 1])
    cw = cr.R_WALL - (r + od / 2)
    ez = R @ np.array([0.0, 0.0, 1.0])
    ax_ = H @ ez
    cc = np.linalg.norm(H - np.outer(ax_, ez), axis=1) - cr.R_CASE - od / 2
    m = s_arc > 25.0
    tee0, tee1 = R @ np.array([t["axis_xy"][0], t["axis_xy"][1], t["z_bot"]]), R @ np.array([t["axis_xy"][0], t["axis_xy"][1], t["z_top"]])
    ris1 = R @ np.array([t["axis_xy"][0], t["axis_xy"][1], 156.0])
    dt = np.minimum(cr.seg_dist(H[m], tee0, tee1) - t["od"] / 2, cr.seg_dist(H[m], tee1, ris1) - 9.525 / 2) - od / 2
    return float(cw.min()), float(cc.min()), float(dt.min())


def main():
    t0 = time.time()
    S = {}
    pf._HOSE_U.clear()
    f = pf.route(S)
    poses = [(float(a), float(b)) for a in range(-7, 8) for b in range(-7, 8) if a * a + b * b <= CONE * CONE + 1e-9]
    pre = {}
    for a, b in poses:
        P, rad, part, H, R = series_path_pose(f, S, a, b)
        w, c, te = clearances(f, H, R)
        pre[(a, b)] = (P, rad, part, {"wall": round(w, 2), "case": round(c, 2), "tee": round(te, 2), "ok": bool(min(w, c, te) >= cr.CLR)})
    n_ok = sum(1 for v in pre.values() if v[3]["ok"])
    print("poses", len(poses), "clearance-feasible", n_ok, flush=True)
    cases = [(0.0, 0.0)] + [(th, az) for th in (2.0, 4.0, 10.0) for az in range(0, 360, 45)]
    rows = []
    for th, az in cases:
        u = np.array([math.sin(math.radians(th)) * math.cos(math.radians(az)), math.sin(math.radians(th)) * math.sin(math.radians(az)),
                      math.cos(math.radians(th))])
        res = []
        for (a, b), (P, rad, part, clr) in pre.items():
            v, by, spill = pockets(P, rad, part, u)
            hose_like = by.get("hose", 0.0) + by.get("FD-07A/TEE side", 0.0) + by.get("FD-07B", 0.0)
            res.append({"pose": (a, b), "hose_cm3": by.get("hose", 0.0), "hose_and_sleeves_cm3": round(hose_like, 3),
                        "fixed_leg_cm3": by.get("fixed leg + wall foot", 0.0), "total_cm3": round(v, 3), "clr": clr})
        neutral = [r for r in res if r["pose"] == (0.0, 0.0)][0]
        feas = [r for r in res if r["clr"]["ok"]]
        best = min(feas, key=lambda r: (r["hose_cm3"], math.hypot(*r["pose"])))
        best_any = min(res, key=lambda r: (r["hose_cm3"], math.hypot(*r["pose"])))
        clear = [r for r in feas if r["hose_cm3"] <= MICRO]
        row = {"tilt_deg": th, "toward_az_deg": float(az), "neutral": neutral, "best_feasible": best,
               "best_ignoring_clearance": best_any if best_any["pose"] != best["pose"] else "same",
               "n_feasible_poses_clearing_hose": len(clear),
               "clearing_pose_min_norm": (min(clear, key=lambda r: math.hypot(*r["pose"]))["pose"] if clear else None)}
        rows.append(row)
        print(f"tilt {th:4.1f} az {az:5.1f}: neutral hose {neutral['hose_cm3']:.3f} | best feasible pose {best['pose']} hose {best['hose_cm3']:.3f} "
              f"(fixed leg {best['fixed_leg_cm3']:.3f}, clr {best['clr']}) | clearing poses {len(clear)}", flush=True)
    worst10 = max([r for r in rows if r["tilt_deg"] == 10.0], key=lambda r: r["best_feasible"]["hose_cm3"])
    verdict = {}
    for th in (2.0, 4.0, 10.0):
        rr = [r for r in rows if r["tilt_deg"] == th]
        verdict[f"{th:.0f}"] = {"directions_cleared_by_a_pose": sum(1 for r in rr if r["n_feasible_poses_clearing_hose"] > 0),
                                "of": len(rr),
                                "neutral_hose_max_cm3": max(r["neutral"]["hose_cm3"] for r in rr),
                                "best_pose_hose_max_cm3": max(r["best_feasible"]["hose_cm3"] for r in rr),
                                "fixed_leg_max_at_best_cm3": max(r["best_feasible"]["fixed_leg_cm3"] for r in rr)}
    refuted = worst10["n_feasible_poses_clearing_hose"] == 0
    # proxy check: neutral-pose hose pocket of the proxy against the voxel trap run on the CAD (segment_traps_v341_v1, barrier model)
    chk = None
    vox = HERE / "segment_traps_v341_v1.json"
    if vox.exists():
        tv = json.loads(vox.read_text())["tilt_sensitivity"]
        chk = []
        for r in rows:
            if r["tilt_deg"] != 10.0:
                continue
            vv = [t_ for t_ in tv if t_["model"] == "barrier" and t_["tilt_deg"] == 10.0 and abs(t_["toward_az_deg"] - r["toward_az_deg"]) < 1e-6]
            if vv:
                chk.append({"toward_az_deg": r["toward_az_deg"], "proxy_hose_cm3": r["neutral"]["hose_cm3"], "voxel_hose_cm3": vv[0]["split"]["hose_bore_cm3"]})
    out = {"id": "drain_pose_v341", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/drain_pose_v341.py",
           "method": __doc__, "hypothesis": "H-DP (research proposal): a gimbal pose within the 7 deg cone clears the hose of vapour pockets at a vehicle tilt",
           "comparator": "neutral pose", "refutation": "no pose clears the hose at 10 deg in the worst direction, or the clearing pose breaks a clearance",
           "cone_deg": CONE, "n_poses": len(poses), "n_poses_clearance_ok": n_ok, "micro_allowance_cm3": MICRO,
           "verdict_by_tilt": verdict, "worst_10deg_direction": {"toward_az_deg": worst10["toward_az_deg"], "best_feasible": worst10["best_feasible"],
                                                                   "neutral": worst10["neutral"]},
           "H_DP_refuted_at_10deg": bool(refuted), "proxy_check_neutral_10deg_vs_voxel": chk, "rows": rows,
           "tag": "RESEARCH PROPOSAL screen; DERIVED proxy (centreline pockets on the linear-frame posed hose); not a two-phase model",
           "t_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(verdict, indent=1))
    print("refuted at 10 deg:", refuted, "t", out["t_s"])


if __name__ == "__main__":
    main()
