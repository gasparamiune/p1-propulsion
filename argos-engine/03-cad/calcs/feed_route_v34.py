"""Feed route on CAD v3.4 (Option A, lead 2026-10-13): fixed 3/8 wall-line corridor, module station, coil fixed-end azimuth (v1, Mechanical).

Lead decision 2026-10-13 (Option A): MV-P/FS-01 module at the zone top, fixed 3/8 x 0.035 in line down the bay wall to the O3b coil
fixed end.  hose_routing_trade_v2 found the wall-line corridor on CAD v3.3 + an ESTIMATED HV69 stack envelope (best azimuths need
3.3 mm relief).  This script repeats the corridor on the CAD v3.4 solids (HV69 stack PD-01..20, E1-M inlet, torch, Pc port) and fixes:
  - the wall-line azimuth: per 1 deg, the relief the swept engine (8 deg cone, 24 directions x 4 angles) needs so that a 3/8 line on the
    wall (centre r = 70 - 1 clip band - 4.76 = 64.24 mm) keeps 3 mm; z from the coil fixed end (45) to the module bottom;
  - the module bottom station: highest swept engine point + 3 mm;
  - the coil sweep angle from the riser-foot TEE (az 180, side nose along -Y = +az) to the chosen fixed-end azimuth.
Rules as hose_routing_trade_v2 (bay R 70, 3 mm moving-to-fixed and moving-to-wall).  Output: calcs/feed_route_v34_v1.json.
"""
from __future__ import annotations
import sys, json, math, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2] / "04-fea" / "src"))
import hose_routing_trade_v2 as h2

OUT = HERE / "feed_route_v34_v1.json"
OD = 9.525
R_LINE = h2.R_WALL - h2.CLIP_T - OD / 2


def main():
    import build, config, sweep
    t0 = time.time()
    P, S, reg, clog = build.build(include=("engine", "gimbal"), iterate_cg=True, overrides=config.V34_ON)
    inst = build.posed_instances(reg, S, 0.0, 0.0)
    pts, tags = [], []
    for (pn, i, g, s, body) in inst:
        if g != "engine":
            continue
        Q = sweep._points(s)
        pts.append(Q)
        tags += [f"{pn}#{i}"] * len(Q)
    Q, tags = np.vstack(pts), np.array(tags)
    env = h2.envelope(Q, tags, dz=2.0, dphi=1.0, swept=True)
    # highest swept engine point
    zmax, who = -1e9, ""
    for k in range(24):
        psi = 2 * math.pi * k / 24
        a = np.array([-math.sin(psi), math.cos(psi), 0.0])
        for th in np.linspace(0, h2.STOP, 5):
            X = Q @ h2.hrt.rodrigues(a, math.radians(th)).T
            j = int(np.argmax(X[:, 2]))
            if X[j, 2] > zmax:
                zmax, who = float(X[j, 2]), str(tags[j])
    z_mod = zmax + h2.CLR
    # corridor per 1 deg over the coil fixed end .. module bottom
    pe = np.array([v[1] for v in env.values()])
    we = np.array([v[2] for v in env.values()])
    rows = []
    for phi in np.arange(0.0, 360.0, 1.0):
        c = np.array([R_LINE * math.cos(math.radians(phi)), R_LINE * math.sin(math.radians(phi))])
        m = (pe[:, 2] >= 40.0) & (pe[:, 2] <= z_mod)
        d = np.hypot(pe[m, 0] - c[0], pe[m, 1] - c[1]) - OD / 2
        j = int(np.argmin(d))
        rows.append({"phi_deg": float(phi), "min_gap_mm": round(float(d[j]), 2), "at_z_mm": round(float(pe[m][j, 2]), 1), "by": str(we[m][j]),
                     "relief_needed_mm": round(max(0.0, h2.CLR - float(d[j])), 2)})
    ok = [r for r in rows if r["relief_needed_mm"] == 0.0]
    # contiguous free sectors
    sectors, cur = [], None
    for r in rows:
        if r["relief_needed_mm"] == 0.0:
            cur = [r["phi_deg"], r["phi_deg"]] if cur is None else [cur[0], r["phi_deg"]]
        elif cur is not None:
            sectors.append(cur)
            cur = None
    if cur is not None:
        if sectors and sectors[0][0] == 0.0:
            sectors[0] = [cur[0] - 360.0, sectors[0][1]]
        else:
            sectors.append(cur)
    best = sorted(sectors, key=lambda s: -(s[1] - s[0]))
    out = {"id": "feed_route_v34", "version": "v1", "date": "2026-10-13", "script": "03-cad/src/calcs/feed_route_v34.py",
           "method": __doc__.split("\n\n")[0], "cad": "v3.4 build (config.V34_ON), engine group, pivot iterated",
           "line": {"od_mm": OD, "centre_r_mm": round(R_LINE, 2), "clip_band_mm": h2.CLIP_T, "clearance_rule_mm": h2.CLR},
           "engine_swept_top_mm": round(zmax, 2), "engine_swept_top_by": who, "module_bottom_min_mm": round(z_mod, 2),
           "free_sectors_deg": [[round(a, 0), round(b, 0)] for a, b in best], "n_free_deg": len(ok),
           "corridor_every_deg": rows, "t_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "corridor_every_deg"}, indent=1))
    for r in rows[::10]:
        print(r)


if __name__ == "__main__":
    main()
