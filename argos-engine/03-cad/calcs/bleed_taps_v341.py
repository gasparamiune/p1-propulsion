"""Head-end bleed taps on the CAD v3.4.1 segment: retained vapour that buoyancy alone cannot bring to a vent (v1, 2026-10-13, Mechanical).

Coordinator 2026-10-13: "state whether one bleed at T4 purges the whole re-routed segment or the FD-01 top still needs a second one".
Lead A1 RELIGHT CONFIGURATION: bleed at the T4 port (S12 plug location), forced purge (MV open, pintle seated, bleed open >= 2-3 s).
Method: segment_traps_v34.py v1.3 geometry, voxels and maximin spill analysis unchanged (MV closed geometry, both filter-element models),
with extra vents (tap inlets) added to the S1 back-relief vent:
  T4      crown of the T4 port cavity at its outer end (r 20.3, z_x + 4.05): the bleed fitting must take vapour from the CAVITY CROWN
          (an on-axis orifice would leave the upper half of the port, the cross-drilling crown and the bore top: ~0.6 cm3, ESTIMATE);
  FD01    crown of the FD-01 radial drilling at its outer end (r 41.5, z_f + 3.7) = the plug of that drilling (second tap).
Attitudes: nozzle-down +Z, 10 and 20 deg in 8 directions (as the trap run).  Output per case: retained flow-path volume (trapped +
unreached), split into hose bore, sleeves, wall line, upstream / downstream of the element (downstream = the S1-only barrier model's
isolated region), and the residual OUTSIDE the hose / sleeves / wall line (what a purge flow that clears the hose humps would still
leave by buoyancy in the head end and the TEE/riser).  Buoyancy only: a forced purge can also drag bubbles with the flow (hose humps,
Fr criterion, see headend_bleed_concept) but cannot push them through the element below its bubble point (barrier model).
Output: calcs/bleed_taps_v341_v1.json.  DERIVED (CAD v3.4.1 DESIGN geometry, voxel 0.25 mm); no two-phase flow model; no test.
v1.1 (2026-10-13): --tilts / --out options.  Lead: design attitude at relight theta <= 2 deg (GNC relight attitude p99 0.63 deg,
max 0.75 deg); run with --tilts 1,2 --out bleed_taps_v341_v1p1.json.  The 10 / 20 deg rows of v1 stay as robustness information.
"""
from __future__ import annotations
import argparse, json, math, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import segment_traps_v34 as st

OUT = HERE / "bleed_taps_v341_v1.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tilts", default="10,20")
    ap.add_argument("--out", default=OUT.name)
    ap.add_argument("--cfgs", default="S1+T4,S1+T4+FD01", help="v1.1: vent sets; S1 alone = no bleed tap")
    a_ = ap.parse_args()
    TILTS = tuple(float(x) for x in a_.tilts.split(",") if x)
    out_path = HERE / a_.out
    CFGS = [tuple(c.split("+")) for c in a_.cfgs.split(",") if c]
    t0 = time.time()
    import build, config
    from calcs.inlet_e1m import E1M
    import parts_inlet
    P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True, overrides=config.V34_ON)
    spec, excl, vents, stn = st.all_spec(S, P)
    lab_names = [s_[-2] for s_ in spec]
    lab_kind = [s_[-1] for s_ in spec]
    a = math.radians(E1M["az_deg"])
    ux = np.array([math.cos(a), math.sin(a), 0.0])
    taps = {"T4": ux * (28.2 - 7.6 - 0.3) + np.array([0, 0, stn["z_x"] + 8.7 / 2 - 0.3]),
            "FD01": ux * 41.5 + np.array([0, 0, stn["z_f"] + 3.7])}
    ka, la, ek = st.voxelise(spec, excl)
    (kb, lb), (ko, lo) = st.element_variants(ka, la, ek, lab_names)
    geo = {"barrier": (kb, lb), "open_element": (ko, lo)}
    # downstream mask from the S1-only barrier model (as segment_traps v1.3)
    Xb = st.key_to_xyz(kb)
    Eb = st.build_graph(kb)
    vi_s1 = np.nonzero(np.linalg.norm(Xb - vents["S1_check"], axis=1) <= max(1.0, 2 * st.H))[0]
    _, reach_b, _ = st.spill_levels(Xb @ np.array([0, 0, 1.0]), Eb, vi_s1)
    kdown = kb[~reach_b]
    down = {"barrier": ~reach_b, "open_element": np.isin(ko, kdown) | np.isin(ko, ek)}
    hose_like = np.array([any(t in n for t in ("FD-07 hose", "FD-07A", "FD-07B", "FD-08 wall")) for n in lab_names])
    path = np.array([k == "path" for k in lab_kind])
    v = lambda m: round(float(m.sum() * st.H ** 3 / 1e3), 4)
    rows = []
    att = [(0.0, 0.0)] + [(th, k * 45.0) for th in TILTS for k in range(8)]
    for model, (k_, l_) in geo.items():
        X_ = st.key_to_xyz(k_)
        E_ = st.build_graph(k_)
        vidx = {"S1": np.nonzero(np.linalg.norm(X_ - vents["S1_check"], axis=1) <= max(1.0, 2 * st.H))[0]}
        for tn, tp in taps.items():
            vidx[tn] = np.nonzero(np.linalg.norm(X_ - tp, axis=1) <= 1.0)[0]
        print(model, {k: len(i) for k, i in vidx.items()}, flush=True)
        for cfg in CFGS:
            vi = np.unique(np.concatenate([vidx[c] for c in cfg]))
            for th, az in att:
                up = np.array([math.sin(math.radians(th)) * math.cos(math.radians(az)), math.sin(math.radians(th)) * math.sin(math.radians(az)),
                               math.cos(math.radians(th))])
                r, e, s, trapped, T = st.analyse(k_, l_, lab_names, lab_kind, X_, up, vi, E_, f"{model} {'+'.join(cfg)} {th:.0f}/{az:.0f}")
                reach = np.isfinite(s)
                ret = (trapped | ~reach) & path[l_]
                dn = down[model]
                row = {"model": model, "vents": "+".join(cfg), "tilt_deg": th, "toward_az_deg": az,
                       "retained_flow_path_cm3": v(ret), "hose_bore_cm3": v(ret & np.array(["FD-07 hose" in n for n in lab_names])[l_]),
                       "sleeves_wall_line_cm3": v(ret & np.array([any(t in n for t in ("FD-07A", "FD-07B", "FD-08 wall")) for n in lab_names])[l_]),
                       "upstream_cm3": v(ret & ~dn), "downstream_cm3": v(ret & dn),
                       "residual_outside_hose_and_lines_cm3": v(ret & ~hose_like[l_]),
                       "dead_end_retained_cm3": v((trapped | ~reach) & ~path[l_]),
                       "pockets": [{kk: p[kk] for kk in ("vol_cm3", "top_at", "top_xyz_mm", "top_e_mm", "spill_e_mm", "flow_path_cm3")} for p in r["pockets"][:4]]}
                rows.append(row)
                print(json.dumps({kk: row[kk] for kk in row if kk != "pockets"}), [(p["vol_cm3"], p["top_at"][:24]) for p in row["pockets"][:3]], flush=True)
    summ = {}
    for model in geo:
        for cfg in ["+".join(c) for c in CFGS]:
            rr = [r for r in rows if r["model"] == model and r["vents"] == cfg]
            d = {}
            for th in (0.0,) + TILTS:
                tt = [r for r in rr if r["tilt_deg"] == th]
                d[f"{th:.0f}"] = {"flow_path_max_cm3": max(r["retained_flow_path_cm3"] for r in tt),
                                  "flow_path_min_cm3": min(r["retained_flow_path_cm3"] for r in tt),
                                  "residual_outside_hose_and_lines_max_cm3": max(r["residual_outside_hose_and_lines_cm3"] for r in tt),
                                  "hose_bore_max_cm3": max(r["hose_bore_cm3"] for r in tt),
                                  "upstream_max_cm3": max(r["upstream_cm3"] for r in tt), "downstream_max_cm3": max(r["downstream_cm3"] for r in tt)}
            summ[f"{model}|{cfg}"] = d
    out = {"id": "bleed_taps_v341", "version": "v1" if TILTS == (10.0, 20.0) else "v1.1", "tilts_deg": TILTS, "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/bleed_taps_v341.py",
           "method": __doc__, "cad": "CAD v3.4.1 (config.V34_ON) incl. feed, pivot iterated", "voxel_mm": st.H,
           "taps_xyz_mm": {k: [round(float(x), 2) for x in p] for k, p in taps.items()}, "summary": summ, "rows": rows,
           "tag": "DERIVED (buoyancy-only maximin analysis on the DESIGN geometry); sweep by the purge flow and two-phase effects not modelled",
           "t_s": round(time.time() - t0, 1)}
    out_path.write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(summ, indent=1))
    print("done", out["t_s"])


if __name__ == "__main__":
    main()
