"""FD-07 coil: tilt robustness screen of steeper re-routes (v1, 2026-10-13, Mechanical).

Why: segment_traps_v341_v1.json (CAD v3.4.1, coil z 72 -> 74) meets the nominal targets (flow-path retained 12.0 / 13.8 cm3, barrier /
open element; hose only in the 0.52 cm3 bore-step micro-trap) but at a 10 deg swing the nearly level coil and fixed leg form low points:
hose bore retained up to 15.7 cm3 and flow-path retained 13.7-28.9 / 15.5-30.7 cm3 over 8 directions.  A path keeps its pockets
closed at a tilt theta only if its crown rises along the path at least as fast as the tilt lowers it: dz/ds >= tan(theta) on every
level run (coil + fixed leg).
Screen: candidates with a higher fixed end (z_end 85-115), larger plan radius, evaluated with coil_reroute_v341.evaluate (gates at the
8 deg stop: wall / case / TEE >= 3 mm, static MBR >= 30, K per EI, nominal saddle >= 75) plus a path-pocket proxy at 10 and 20 deg
(36 directions): along the series path TEE side passage -> FD-07A -> hose -> FD-07B -> fixed leg -> foot of the vertical wall line, the
volume of bore lying above the lowest crown AHEAD of it (circular-segment area above that level; bore radius 5.25 hose / 3.87 tube),
and the spill level of the head end (lowest crown on the path).  The fixed leg of route() stays LEVEL at z_end (an inclined leg is
not modelled: its pocket is reported separately), so the proxy shows how much a steeper coil alone recovers.
Proxy only: the trap volume of a chosen candidate comes from segment_traps on its CAD.  Output: calcs/coil_tilt_screen_v341_v1.json.
DERIVED (CAD route candidates; EI ASSUMED).
"""
from __future__ import annotations
import itertools, json, math, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import parts_feed as pf
import coil_reroute_v341 as cr
import coil_route_trade_v34 as ct

OUT = HERE / "coil_tilt_screen_v341_v1.json"
A_HOSE, A_TUBE = 10.5 / 2, 7.747 / 2


def seg_area_above(h, a):
    """Area of a circle (radius a) above a chord at height h from the centre."""
    h = np.clip(h, -a, a)
    return a * a * np.arccos(h / a) - h * np.sqrt(np.maximum(a * a - h * h, 0.0))


def series_path(f):
    t = pf.FEED["tee"]
    d = f["d"]
    P0 = f["Pe"] - (t["side_socket_depth"] + 3.0) * d
    pts, rad, part = [], [], []
    for s in np.linspace(0.0, 1.0, 12):
        pts.append(P0 + s * (f["Q"] - P0)); rad.append(A_TUBE); part.append("FD-07A/TEE side")
    for p in f["hose"][1:]:
        pts.append(p); rad.append(A_HOSE); part.append("hose")
    for s in np.linspace(0.0, 1.0, 12)[1:]:
        pts.append(f["Fq"] + s * (f["Fe"] - f["Fq"])); rad.append(A_TUBE); part.append("FD-07B")
    wall = np.asarray(f["wall"])
    k_top = int(np.argmax(wall[:, 2] >= f["V0"][2] + 30.0))        # up to 30 mm into the vertical wall line
    for p in wall[1:k_top]:
        pts.append(p); rad.append(A_TUBE); part.append("fixed leg + wall foot")
    return np.array(pts), np.array(rad), np.array(part)


def pockets(P, a, part, u):
    seg = np.diff(P, axis=0)
    ds = np.linalg.norm(seg, axis=1)
    tng = seg / ds[:, None]
    Pm = 0.5 * (P[1:] + P[:-1])
    am = 0.5 * (a[1:] + a[:-1])
    e = Pm @ u
    av = am * np.sqrt(np.maximum(1.0 - (tng @ u) ** 2, 1e-6))     # vertical half-extent of the bore
    crown = e + av
    ahead = np.minimum.accumulate(crown[::-1])[::-1]                # lowest crown at or ahead of s
    h = (ahead - e) / np.maximum(av, 1e-9) * am                      # level relative to the centre, in bore-radius units * a
    frac_area = seg_area_above(h, am)
    vol = np.where(crown > ahead + 1e-9, frac_area * ds, 0.0)
    by = {}
    for pn in np.unique(part[1:]):
        by[str(pn)] = round(float(vol[part[1:] == pn].sum() / 1e3), 3)
    return float(vol.sum() / 1e3), by, float(ahead[0])


def tilt_metrics(f, deg):
    P, a, part = series_path(f)
    rows = []
    for az in range(0, 360, 10):
        u = np.array([math.sin(math.radians(deg)) * math.cos(math.radians(az)), math.sin(math.radians(deg)) * math.sin(math.radians(az)),
                      math.cos(math.radians(deg))])
        v, by, spill = pockets(P, a, part, u)
        rows.append({"az": az, "pocket_cm3": round(v, 3), "by_part": by, "head_spill_e_mm": round(spill, 2)})
    w = max(rows, key=lambda r: r["pocket_cm3"])
    return {"max_pocket_cm3": w["pocket_cm3"], "at_az": w["az"], "by_part_at_max": w["by_part"],
            "min_head_spill_e_mm": min(r["head_spill_e_mm"] for r in rows), "rows": rows}


def main():
    t0 = time.time()
    rows = []
    base = {"z_end": 74.0, "fq_az": 303.0, "fq_r": 54.0, "R_min_plan": 41.5, "r_max": 56.0, "r_pref": 50.0, "ferrule.len": 15.0, "tee.side_aim": -12.0}
    grid = [base] + [dict(base, **{"z_end": z, "fq_az": az, "fq_r": fr, "r_max": rm, "r_pref": rp})
                     for z, az, fr, (rm, rp) in itertools.product((85.0, 95.0, 105.0, 115.0), (303.0, 315.0), (56.0, 58.0),
                                                                  ((58.0, 54.0), (60.0, 56.0)))]
    for p in grid:
        rec = cr.evaluate(p)
        if rec.get("feasible"):
            save = ct._set(p)
            pf._HOSE_U.clear()
            try:
                f = pf.route({})
                rec["tilt10"] = tilt_metrics(f, 10.0)
                rec["tilt20"] = tilt_metrics(f, 20.0)
                rec["tilt0"] = tilt_metrics(f, 0.0)
            finally:
                for sec, dd in save.items():
                    pf.FEED[sec].clear()
                    pf.FEED[sec].update(dd)
                pf._HOSE_U.clear()
        rows.append(rec)
        print(json.dumps({"p": {k: p[k] for k in ("z_end", "fq_az", "fq_r", "r_max")}, "feas": rec.get("feasible"), "why": rec.get("why"),
                          "wall": rec.get("wall_clr_stop_mm"), "case": rec.get("case_clr_stop_mm"), "tee": rec.get("tee_riser_clr_stop_mm"),
                          "Rmin": rec.get("Rmin_stop_mm"), "K/EI": rec.get("K_max_per_EI"), "EIbe": rec.get("EI_breakeven_Nm2"),
                          "len": rec.get("length_mm"), "mono": rec.get("hose_monotonic_rise"),
                          "p0": rec.get("tilt0", {}).get("max_pocket_cm3"),
                          "p10": rec.get("tilt10", {}).get("max_pocket_cm3"), "p10by": rec.get("tilt10", {}).get("by_part_at_max"),
                          "spill10": rec.get("tilt10", {}).get("min_head_spill_e_mm"), "p20": rec.get("tilt20", {}).get("max_pocket_cm3")}), flush=True)
    out = {"id": "coil_tilt_screen_v341", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/coil_tilt_screen_v341.py",
           "method": __doc__, "rows": [{k: v for k, v in r.items() if k not in ("worst",)} for r in rows],
           "tag": "DERIVED proxy (path pockets along the centreline; trap volumes of a chosen route need segment_traps); EI ASSUMED",
           "t_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print("done", out["t_s"])


if __name__ == "__main__":
    main()
