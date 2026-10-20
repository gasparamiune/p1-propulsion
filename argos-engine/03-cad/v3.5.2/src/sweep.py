"""Swept envelope of the gimballed engine about the pivot vs the engine-bay wall (CAD v3.2).

For every engine-group solid (and the ring group), the neutral tessellation (edges densified to <= 3 mm) is
rotated about horizontal axes through the pivot by 0..theta_stop in the radially outward and inward sense
(r', z') = (r cos t +/- z sin t, z cos t -/+ r sin t).  This is the exact envelope of all tilts up to the conical
stop for rotations about axes in the pivot plane (the Cardan twist about the engine axis is second order and
does not change radii).  Results per 5 mm z band (engine frame, neutral axes): max swept radius, the part that
sets it, clearance to the bay radius, and the forward/aft extent of the swept envelope.  Fixed parts are
checked statically against the same wall.
"""
from __future__ import annotations
import math
import numpy as np


def _points(shape, tol=0.1, seg=3.0):
    vs, ts = shape.tessellate(tol, 0.2)
    V = np.array([[p.x, p.y, p.z] for p in vs])
    pts = [V]
    for t in ts:
        a, b, c = V[t[0]], V[t[1]], V[t[2]]
        for p, q in ((a, b), (b, c), (c, a)):
            L = np.linalg.norm(q - p)
            if L > seg:
                n = int(L // seg) + 1
                w = np.linspace(0, 1, n + 1)[1:-1, None]
                pts.append(p + w * (q - p))
    return np.vstack(pts)


def swept_envelope(inst, theta_deg, groups=("engine",), dz=5.0, n_t=9):
    th = math.radians(theta_deg)
    bands = {}
    zext = [float("inf"), -float("inf"), "", ""]
    for (pn, i, g, s, body) in inst:
        if g not in groups:
            continue
        Q = _points(s)
        r = np.hypot(Q[:, 0], Q[:, 1])
        z = Q[:, 2]
        for t in np.linspace(0.0, th, n_t):
            c, sn = math.cos(t), math.sin(t)
            for sgn in (1.0, -1.0):
                rr = r * c + sgn * z * sn
                zz = z * c - sgn * r * sn
                ok = rr >= 0
                rr, zz = rr[ok], zz[ok]
                if len(zz) == 0:
                    continue
                if zz.min() < zext[0]:
                    zext[0], zext[2] = float(zz.min()), f"{pn}#{i}"
                if zz.max() > zext[1]:
                    zext[1], zext[3] = float(zz.max()), f"{pn}#{i}"
                k = np.floor(zz / dz).astype(int)
                order = np.argsort(-rr)
                seen = set()
                for idx in order:
                    kk = int(k[idx])
                    if kk in seen:
                        continue
                    seen.add(kk)
                    if rr[idx] > bands.get(kk, (0.0, ""))[0]:
                        bands[kk] = (float(rr[idx]), f"{pn}#{i}")
    return bands, zext


def static_envelope(inst, groups=("fixed",), dz=5.0):
    bands = {}
    for (pn, i, g, s, body) in inst:
        if g not in groups:
            continue
        Q = _points(s)
        r = np.hypot(Q[:, 0], Q[:, 1])
        k = np.floor(Q[:, 2] / dz).astype(int)
        for kk in np.unique(k):
            m = float(r[k == kk].max())
            if m > bands.get(int(kk), (0.0, ""))[0]:
                bands[int(kk)] = (m, f"{pn}#{i}")
    return bands


def report(inst, P, R_bay_mm=None, dz=5.0):
    stop = P["gimbal_stop_deg"]["v"]
    R_bay = R_bay_mm if R_bay_mm is not None else P["engine_bay_ID"]["v"] * 500.0
    eng, zext = swept_envelope(inst, stop, ("engine",), dz)
    ring, zext_r = swept_envelope(inst, stop, ("ring",), dz)
    fixed = static_envelope(inst, ("fixed",), dz)
    rows = []
    for kk in sorted(set(eng) | set(ring) | set(fixed)):
        e, rg, f = eng.get(kk, (0.0, "")), ring.get(kk, (0.0, "")), fixed.get(kk, (0.0, ""))
        m = max((e, rg, f), key=lambda t: t[0])
        rows.append({"z0_mm": kk * dz, "z1_mm": (kk + 1) * dz, "r_engine_swept_mm": round(e[0], 2), "by_engine": e[1],
                     "r_ring_swept_mm": round(rg[0], 2), "r_fixed_mm": round(f[0], 2), "by_fixed": f[1],
                     "r_max_mm": round(m[0], 2), "clearance_mm": round(R_bay - m[0], 2)})
    worst = min(rows, key=lambda r: r["clearance_mm"])
    over = [r for r in rows if r["clearance_mm"] < P["airframe_clear"]["v"] * 1e3]
    return {"theta_stop_deg": stop, "R_bay_mm": R_bay, "required_clear_mm": P["airframe_clear"]["v"] * 1e3,
            "engine_swept_z_extent_mm": [round(zext[0], 1), round(zext[1], 1)], "z_extent_set_by": zext[2:],
            "worst_band": worst, "bands_below_required_clearance": over, "bands": rows}


def required_bay(rep, margin_mm=3.0):
    """Smallest bay radius that keeps margin_mm over every band, and the radius needed per z zone."""
    rmax = max(r["r_max_mm"] for r in rep["bands"])
    return {"R_required_mm": round(rmax + margin_mm, 1), "ID_required_mm": round(2 * (rmax + margin_mm), 1)}
