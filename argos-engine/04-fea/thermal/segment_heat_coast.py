"""Heat drawn by the trapped N2O in the head-end bore during a coast (04-fea/thermal, v1, 2026-10-13, Mechanical).

Lead relay 2026-10-13 item 5 (retained vapour): in flight the vapour retained in the MV-to-seat segment must stay <= 19 cm3
at RELIGHT, i.e. a mean segment heat input <= 24 W from MECO to RELIGHT (~22 s, ~528 J) if all vapour is retained.
This script gives the head-end part of that heat input from the 2-D axisymmetric thermal runs (run_thermal.py):
  - the N2O-wetted edges are the COAST-step *FILM lines of the run deck whose film coefficient equals the static-N2O
    value (ax_thermal G_N2O_COAST / A_n2o; the manifold bore r < 5.25 mm from the seat to the stem-seal gland, i.e. the
    TC-03 insert, TC-05 needle, TC-02 head and TC-04 bonnet bore walls);
  - Q(t) = sum h A (T_edge - T_N2O) with T_edge the Simpson mean of the 3 edge nodes (CAX6) and A = 2 pi r_mid L;
  - E = trapezoid integral over the frd samples between MECO and RELIGHT (frd every ~1 s in coasts);
  - per-part split and bore-wall temperatures at MECO and RELIGHT.
The run's own coast BC sets h (G 1 W/K = Combustion default; --g_n2o_coast 10 W/K run = heat-draw bound: a stiffer sink
pulls more heat from the soaking metal).  The off-axis head/bonnet drillings, FD-01 block, riser, coil, wall line and the
MV/FS-01 module are NOT in this model; segment_heat_budget.py adds them.

Also written: mean-temperature histories (ignition -> relight) of the head/bonnet regions around the E1-M off-axis
drillings (REGIONS, thermal-mesh frame: head top 178.02, cap bottom 150.02), used as far-field temperatures by
segment_heat_budget.py (the 2-D section is cut at az 214 deg, so the drillings themselves are not in the mesh).

usage: segment_heat_coast.py <label> [<label> ...]   ->  segment_heat_coast_v1.json (merged per label)
"""
from __future__ import annotations
import json, math, sys, re
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ax_thermal as at

RUNS = Path("/home/claude/work/mechanical/runs/thermal")
OUT = HERE / "segment_heat_coast_v1.json"
W = [1 / 6, 1 / 6, 4 / 6]          # Simpson weights (corner, corner, mid) for the edge-mean temperature
REGIONS = {"head_filter_bore": ("ENG-TC-02", 9.5, 30.5, 157.02, 171.02),      # radial 14 mm filter bore, axis z_cap_bot + 14
           "head_axial_8mm": ("ENG-TC-02", 12.0, 20.0, 171.02, 178.02),        # axial 8 mm at r 16 to the head top
           "bonnet_boss": ("ENG-TC-04", 8.0, 20.0, 178.02, 204.02)}            # bonnet axial 8 mm + cross-drilling


def coast_film_edges(inp, h_model):
    """[(elem0, face, T_N2O_K, h_mW_mm2K)] of the first COAST step static-N2O film lines, plus (t_meco, t_relight)."""
    lines = Path(inp).read_text().splitlines()
    for k, l in enumerate(lines):                       # first coast AFTER a burn (the deck opens with a 0 -> 0.001 s pre-step)
        m = re.match(r"\*\* COAST ([\d.]+) -> ([\d.]+) s", l)
        if m and float(m.group(1)) > 0.01:
            break
    else:
        raise SystemExit(f"{inp}: no inter-burn COAST step")
    t0, t1 = float(m.group(1)), float(m.group(2))
    out, blk = [], None
    for l in lines[k + 1:]:
        if l.startswith("*END STEP"):
            break
        if l.startswith("*"):
            blk = l.strip()
            continue
        if blk == "*FILM":
            e, f, T, h = [s.strip() for s in l.split(",")]
            if abs(float(h) - h_model) <= 1e-6 * h_model:
                out.append((int(e) - 1, int(f[1:]), float(T), float(h)))
    return out, (t0, t1)


def main(labels, mesh_from=None):
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    res["script"] = "04-fea/thermal/segment_heat_coast.py v1"
    res["note"] = __doc__.split("\n\n")[1]
    for lab in labels:
        run = RUNS / lab
        meta = json.loads((run / f"{lab}_meta.json").read_text())
        h_model = meta["h_n2o_coast_W_m2K"] * 1e-3
        edges, (tm, tr) = coast_film_edges(run / f"{lab}.inp", h_model)
        mrun = RUNS / mesh_from if mesh_from else run           # a running job has no envelope_nodes.npz yet: same mesh from a twin run
        d = np.load(mrun / "envelope_nodes.npz", allow_pickle=True)
        if mesh_from:
            mm = json.loads((mrun / f"{mesh_from}_meta.json").read_text())
            assert (mm["n_nodes"], mm["n_elems"]) == (meta["n_nodes"], meta["n_elems"]), "mesh_from run has a different mesh"
        X, E, pn = d["X"], d["E"], d["pn"]
        geo = []
        for e, f, TN, h in edges:
            i, j, k = at.EDGE_NODES[f]
            n = (E[e, i], E[e, j], E[e, k])
            p0, p1 = X[n[0]], X[n[1]]
            L = float(np.linalg.norm(p1 - p0))
            A = 2 * math.pi * 0.5 * (p0[0] + p1[0]) * L              # mm2
            geo.append((n, A, h, TN, str(pn[e]), 0.5 * (p0[1] + p1[1])))
        A_tot = sum(g[1] for g in geo)
        parts = sorted({g[4] for g in geo})
        want = sorted({q for g in geo for q in g[0]})
        ts, Q, Qp, Tw = [], [], {p: [] for p in parts}, []
        reg_ids = {}
        for k_, (p_, r0, r1, z0, z1) in REGIONS.items():
            ids = np.unique(E[pn == p_])
            reg_ids[k_] = [int(q) for q in ids if r0 <= X[q][0] <= r1 and z0 <= X[q][1] <= z1]
        reg_t, reg_T = [], {k_: [] for k_ in REGIONS}
        for t, vals in at.read_frd_nt(run / f"{lab}.frd"):
            if t > tr + 0.6:
                break
            reg_t.append(t)
            for k_, ids in reg_ids.items():
                reg_T[k_].append(float(np.mean([vals[q + 1] for q in ids])))
            if t < tm - 1e-6:
                continue
            q, qp, tw = 0.0, dict.fromkeys(parts, 0.0), []
            for n, A, h, TN, p, zc in geo:
                Te = sum(w * vals[x + 1] for w, x in zip(W, n))
                dq = h * A * (Te - TN) * 1e-3                         # mW -> W
                q += dq
                qp[p] += dq
                tw.append(Te)
            ts.append(t); Q.append(q); Tw.append((min(tw), float(np.dot([g[1] for g in geo], tw) / A_tot), max(tw)))
            for p in parts:
                Qp[p].append(qp[p])
        ts, Q = np.array(ts), np.array(Q)
        c = (ts >= tm - 1e-6) & (ts <= tr + 1e-6)
        Ec = float(np.trapezoid(Q[c], ts[c]))
        dur = float(ts[c][-1] - ts[c][0])
        row = {"meco_s": tm, "relight_s": tr, "coast_s": round(tr - tm, 3), "frd_samples_in_coast": int(c.sum()),
               "G_N2O_COAST_W_K": round(meta["h_n2o_coast_W_m2K"] * meta["A_n2o_mm2"] * 1e-6, 3), "h_coast_W_m2K": round(h_model * 1e3, 1),
               "A_wetted_mm2": round(A_tot, 1), "T_N2O_coast_K": geo[0][3], "material_overrides": meta.get("material_overrides"),
               "config_overrides": meta.get("config_overrides"),
               "E_coast_J": round(Ec, 1), "P_mean_W": round(Ec / dur, 2) if dur > 0 else None,
               "P_max_W": round(float(Q[c].max()), 2), "t_P_max_s": round(float(ts[c][int(np.argmax(Q[c]))]), 2),
               "E_by_part_J": {p: round(float(np.trapezoid(np.array(Qp[p])[c], ts[c])), 1) for p in parts},
               "wall_T_K_at_meco": [round(v, 1) for v in Tw[int(np.argmin(np.abs(ts - tm)))]],
               "wall_T_K_at_relight": [round(v, 1) for v in Tw[int(np.argmin(np.abs(ts - tr)))]],
               "wall_T_note": "(min, area mean, max) of the wetted-edge temperatures",
               "series": {"t_s": [round(float(v), 2) for v in ts[c]], "Q_W": [round(float(v), 2) for v in Q[c]]},
               "regions": {"def": {k_: {"part": v[0], "r_mm": v[1:3], "z_mm": v[3:5], "n_nodes": len(reg_ids[k_])} for k_, v in REGIONS.items()},
                           "t_s": [round(float(v), 3) for v in reg_t], "T_mean_K": {k_: [round(v, 2) for v in vv] for k_, vv in reg_T.items()}}}
        if dur > 0:
            row["E_22s_extrapolated_J"] = round(Ec + max(0.0, 22.0 - (tr - tm)) * float(Q[c][-1]), 1)
        res.setdefault("runs", {})[lab] = row
        print(lab, json.dumps({k: v for k, v in row.items() if k not in ("series", "regions")}))
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    args = sys.argv[1:]
    mf = None
    if "--mesh_from" in args:
        i = args.index("--mesh_from"); mf = args[i + 1]; args = args[:i] + args[i + 2:]
    main(args, mesh_from=mf)
