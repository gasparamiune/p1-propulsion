"""Remesh-mode boundary extrapolation of the seat patches s6L12 / s9L12 / sDL12 (FEA3D-2, 2026-10-21; lead 2026-10-21 note on the cD setup:
"put the s6 patch's maximum boundary extrapolation beside cD's 0.043 mm (9 nodes over 0.01 mm); say where those nodes sit relative to the two
Balls and the governing line, and whether the d11.2 flats are the cause").  Read-only on jfwd/model_*.npz and jfwd/seat_*.npz; no solve.
Per prescribed node (the patch boundary, js5's s5 field interpolated, jfwd_seat.py build remesh mode): the distance outside the global s5
element, estimated as in jfwd_seat.py (-min barycentric x the element size cbrt(1.414 |det|)); the nodes over 0.01 mm with body, screw-local
x' / y' / z', r, az, r' from the hole axis, distance to the nearest cD Ball centre and to the governing line d+6.051 z'0 (bore r 28.625 to the
flat x' 31.313), and whether the node lies on the spot-face flat region (x' within 0.01 of 31.313 and r' <= 5.6, the d11.2 cutter radius).
usage: jfwd_patch_extrap_nodes_v352.py -> results/v352/jfwd_patch_extrap_nodes_v352.json  [DERIVED]"""
import json, math, hashlib
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/fea3d/jfwd")
OUT = Path("/home/claude/work/fea3d/results/v352/jfwd_patch_extrap_nodes_v352.json")
AZ, ZS, SHIFT = 18.0, 127.513, 0.24
C0 = np.array([0.0, 0.0, ZS])
EN = np.array([math.cos(math.radians(AZ)), math.sin(math.radians(AZ)), 0.0])
ET1 = np.array([-math.sin(math.radians(AZ)), math.cos(math.radians(AZ)), 0.0])
ET2 = np.array([0.0, 0.0, 1.0])
AZL = math.radians(AZ + 6.051)
ZC = ZS - SHIFT
BALLS = [np.array([r * math.cos(AZL), r * math.sin(AZL), ZC]) for r in (28.652, 31.313 / math.cos(math.radians(6.051)) - 0.03)]
L0 = np.array([28.625 * math.cos(AZL), 28.625 * math.sin(AZL), ZC])
L1 = np.array([31.313 / math.cos(math.radians(6.051)) * math.cos(AZL), 31.313 / math.cos(math.radians(6.051)) * math.sin(AZL), ZC])


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def seg_dist(P):
    d = L1 - L0
    t = np.clip(((P - L0) @ d) / (d @ d), 0.0, 1.0)
    return np.linalg.norm(P - (L0 + t[:, None] * d), axis=1)


def main():
    mg = np.load(J / "model_s5.npz")
    Xg, Tg = mg["X"], mg["T"]
    out = {"doc": __doc__.split("usage:")[0].strip(), "inputs_sha16": {"model_s5.npz": sha16(J / "model_s5.npz")}, "patches": {}}
    for tag, mt in (("s6L12", "s6"), ("s9L12", "s9"), ("sDL12", "sD")):
        S = np.load(J / f"seat_{tag}.npz")
        m = np.load(J / f"model_{mt}.npz")
        out["inputs_sha16"][f"seat_{tag}.npz"] = sha16(J / f"seat_{tag}.npz")
        out["inputs_sha16"][f"model_{mt}.npz"] = sha16(J / f"model_{mt}.npz")
        X = m["X"]
        pres, iel, best = S["pres"], S["interp_el"], S["interp_best"]
        Te = Tg[iel]
        det = np.linalg.det(np.stack([Xg[Te[:, 1]] - Xg[Te[:, 0]], Xg[Te[:, 2]] - Xg[Te[:, 0]], Xg[Te[:, 3]] - Xg[Te[:, 0]]], 2))
        dist = np.where(best < 0, -best * np.cbrt(1.414 * np.abs(det)), 0.0)
        body = np.full(len(X), "", dtype=object)
        for bb, key in (("TC-01", "n01"), ("TC-02", "n02"), ("SCREW", "nsc")):
            body[m[key]] = bb
        k = np.nonzero(dist > 0.01)[0]
        k = k[np.argsort(-dist[k])]
        P = X[pres[k]]
        rel = P - C0
        xa, ya, za = rel @ EN, rel @ ET1, rel @ ET2
        rows = []
        for i, kk in enumerate(k):
            rp = math.hypot(ya[i], za[i])
            rows.append({"node": int(pres[kk]), "body": body[pres[kk]], "extrap_mm": round(float(dist[kk]), 4), "x_prime": round(float(xa[i]), 3),
                         "y_prime": round(float(ya[i]), 3), "z_prime": round(float(za[i]), 3), "r": round(float(math.hypot(P[i, 0], P[i, 1])), 3),
                         "az_deg": round(math.degrees(math.atan2(P[i, 1], P[i, 0])), 2), "r_prime_hole_axis": round(rp, 3),
                         "to_nearest_ball_centre_mm": round(float(min(np.linalg.norm(P[i] - b) for b in BALLS)), 2),
                         "to_governing_line_mm": round(float(seg_dist(P[i:i + 1])[0]), 2),
                         "on_flat_region": bool(abs(xa[i] - 31.313) < 0.01 and rp <= 5.6)})
        out["patches"][tag] = {"n_prescribed": int(len(pres)), "max_extrap_mm": round(float(dist.max()), 4), "n_gt_0p01mm": int(len(k)),
                               "min_bary": round(float(best.min()), 4), "nodes_gt_0p01mm": rows,
                               "min_distance_to_ball_centre_mm": round(min(r["to_nearest_ball_centre_mm"] for r in rows), 2) if rows else None,
                               "any_on_flat_region": any(r["on_flat_region"] for r in rows)}
    OUT.write_text(json.dumps(out, indent=1))
    for tag, v in out["patches"].items():
        print(tag, v["max_extrap_mm"], v["n_gt_0p01mm"], "min to Ball", v["min_distance_to_ball_centre_mm"], "on flat", v["any_on_flat_region"],
              "bodies", sorted(set(r["body"] for r in v["nodes_gt_0p01mm"])), "surfaces r", sorted(set(round(r["r"], 2) for r in v["nodes_gt_0p01mm"])))
    print(OUT, sha16(OUT))


if __name__ == "__main__":
    main()
