"""Free corridor for a FIXED 1/8 in bleed line in the engine bay (03-cad/src/calcs, v1, 2026-10-13, Mechanical).

Question (REV-ELEC-1 RE-10, coordinator 2026-10-13): CAD run 6 must state the bleed topology, i.e. a route from the crossing hose (fixed end
next to FD-07B, gimbal plane) to the valve cluster V1/V2 and the overboard vent.  A fixed line between the gimbal plane and the upper bay
must stay >= 3 mm outside everything that moves with the engine at every pose, and inside the 140 mm bay wall.

Method: the engine-group solids (CAD v3.4.1 rev B, config.V34_ON, pivot frozen) are tessellated (0.2 mm) and every vertex is rotated through
the gimbal cone: the 8 deg stop in 72 directions (5 deg) plus the 7 deg range corners; for each azimuth bin (2 deg) and height bin (5 mm)
the largest swept radius is kept.  A fixed line of OD d at the wall (clip band 1 mm) needs r_swept <= 70 - 1 - d - 3.  The FD-08 3/8 in
line (OD 9.53) uses the sector 216-223 deg found the same way (feed_route_v34).  Hoses and pushrods are not engine-rigid and are reported
separately by the make_all clearance checks.  Output: bleed_corridor_v35_v1.json.  Tags: SIM (CAD geometry), no tolerance stack.
"""
from __future__ import annotations
import json, math, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import config, build, tvc_kinematics as tk          # noqa: E402

R_BAY, CLIP, CLEAR = 70.0, 1.0, 3.0
LINES = {"1/8in": 3.175, "3/16in": 4.76, "1/4in": 6.35, "3/8in_FD08": 9.53}


def main():
    t0 = time.time()
    P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True, overrides=config.V34_ON)
    pts = []
    for p in reg:
        for (T, g) in p.placements:
            if build.group_of(g) != "engine":
                continue
            vs, _ = p.shape.tessellate(0.2)
            V = np.array([[v.x, v.y, v.z] for v in vs])
            if len(V):
                pts.append((np.c_[V, np.ones(len(V))] @ T.T)[:, :3])
    X = np.vstack(pts)
    X = X[X[:, 2] > 40.0]                                    # the fixed line runs above the coil band
    stop, rng = P["gimbal_stop_deg"]["v"], P["gimbal_range_deg"]["v"]
    poses = [tk.cone_to_ab(stop, float(d)) for d in np.arange(0.0, 360.0, 5.0)] + [(a, b) for a in (-rng, 0, rng) for b in (-rng, 0, rng)]
    az_bins, z_bins = np.arange(0.0, 360.0, 2.0), np.arange(40.0, 360.0, 5.0)
    Rmax = np.zeros((len(az_bins), len(z_bins)))
    for (a, b) in poses:
        Y = X @ tk.R_pose(a, b).T
        r = np.hypot(Y[:, 0], Y[:, 1])
        az = (np.degrees(np.arctan2(Y[:, 1], Y[:, 0])) % 360.0)
        ia = np.clip((az / 2.0).astype(int), 0, len(az_bins) - 1)
        iz = np.clip(((Y[:, 2] - 40.0) / 5.0).astype(int), 0, len(z_bins) - 1)
        np.maximum.at(Rmax, (ia, iz), r)
    out = {"id": "bleed_corridor_v35", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/bleed_corridor_v35.py",
           "cad": "CAD v3.4.1 rev B engine group (config.V34_ON), pivot frozen", "n_vertices": int(len(X)), "poses": len(poses),
           "bins": {"az_deg": 2.0, "z_mm": 5.0}, "rule": f"r_swept_max <= {R_BAY} - {CLIP} - OD - {CLEAR} over the whole vertical run", "corridors": {}}
    zr = (z_bins >= 90.0) & (z_bins <= 250.0)
    env = Rmax[:, zr].max(axis=1)
    out["swept_rmax_z90_250_by_az"] = {f"{a:.0f}": round(float(v), 2) for a, v in zip(az_bins, env)}
    for nm, od in LINES.items():
        lim = R_BAY - CLIP - od - CLEAR
        ok = env <= lim
        runs, cur = [], None
        for a, o in zip(az_bins, ok):
            if o and cur is None:
                cur = [a, a + 2.0]
            elif o:
                cur[1] = a + 2.0
            elif cur is not None:
                runs.append(cur); cur = None
        if cur is not None:
            runs.append(cur)
        out["corridors"][nm] = {"OD_mm": od, "r_swept_limit_mm": round(lim, 2), "free_sectors_deg": runs}
    # top of the swept engine (for the fixed cluster floor) and the swept radius at the gimbal-plane band
    out["swept_top_z_mm"] = round(float(max((X @ tk.R_pose(a, b).T)[:, 2].max() for (a, b) in poses)), 2)
    out["t_s"] = round(time.time() - t0, 1)
    (HERE / "bleed_corridor_v35_v1.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("corridors", "swept_top_z_mm", "t_s")}, indent=1))


if __name__ == "__main__":
    main()
