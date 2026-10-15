"""Temperature histories from an axisymmetric thermal run (04-fea/thermal, v1, 2026-10-13, Mechanical).

Reads runs/thermal/<label>/<label>.frd (ASCII NDTEMP blocks, all sampled times) once and writes <label>/histories.npz with
the time vector and the temperature (K) history of node groups used by the lumped networks:
  case_OD_z<z0>_<z1>   mean and max over the ENG-TC-01 outer-surface nodes (r >= r_OD - 0.05 mm) in each 5 mm z band, z 20-180 mm
  head_top_r<r0>_<r1>  mean over the head-top face nodes (ENG-TC-02, z = 178.59 +/- 0.05) in radial bands
  bonnet_OD / bonnet_top  ENG-TC-04 outer cylinder and top-face nodes
Node coordinates come from envelope_nodes.npz (X = (r, z) mm), parts from the element part names.
"""
from __future__ import annotations
import sys, json, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ax_thermal as at

RUNS = Path("/home/claude/work/mechanical/runs/thermal")


def groups(run):
    d = np.load(run / "envelope_nodes.npz", allow_pickle=True)
    X, E, pn = d["X"], d["E"], d["pn"]
    nodes_of = {}
    for e, p in zip(E, pn):
        nodes_of.setdefault(str(p), set()).update(int(n) for n in e)
    # E holds 0-based indices into X; the frd node id is index + 1 (ax_thermal writes nodes q+1 in X order)
    def sel(part, cond):
        ids = [n for n in nodes_of.get(part, ()) if cond(X[n])]
        return sorted(ids)
    g = {}
    case = nodes_of["ENG-TC-01"]
    r_od = max(X[n][0] for n in case)
    for z0 in range(20, 180, 5):
        ids = sel("ENG-TC-01", lambda x, z0=z0: x[0] >= r_od - 0.05 and z0 <= x[1] < z0 + 5)
        if ids:
            g[f"case_OD_z{z0}_{z0 + 5}"] = ids
    head = nodes_of["ENG-TC-02"]
    z_top = max(X[n][1] for n in head)
    for r0, r1 in ((0, 8), (8, 14), (14, 20), (20, 26), (26, 32)):
        ids = sel("ENG-TC-02", lambda x, r0=r0, r1=r1: abs(x[1] - z_top) < 0.05 and r0 <= x[0] < r1)
        if ids:
            g[f"head_top_r{r0}_{r1}"] = ids
    if "ENG-TC-04" in nodes_of:
        bon = nodes_of["ENG-TC-04"]
        r_b = max(X[n][0] for n in bon)
        z_b = max(X[n][1] for n in bon)
        g["bonnet_OD"] = sel("ENG-TC-04", lambda x: x[0] >= r_b - 0.05)
        g["bonnet_top"] = sel("ENG-TC-04", lambda x: abs(x[1] - z_b) < 0.05)
        g["_geom_bonnet"] = {"r_OD_mm": float(r_b), "z_top_mm": float(z_b)}
    g["_geom"] = {"case_r_OD_mm": float(r_od), "head_z_top_mm": float(z_top)}
    return g


def main(label):
    run = RUNS / label
    t0 = time.time()
    g = groups(run)
    geom = {k: g.pop(k) for k in [k for k in g if k.startswith("_")]}
    want = sorted({n for ids in g.values() for n in ids})
    ts, rows = [], []
    for t, vals in at.read_frd_nt(run / f"{label}.frd"):
        ts.append(t)
        rows.append([vals.get(n + 1, np.nan) for n in want])
    A = np.array(rows)
    col = {n: i for i, n in enumerate(want)}
    out = {"t_s": np.array(ts)}
    for k, ids in g.items():
        sub = A[:, [col[n] for n in ids]]
        out[k + "_mean"] = np.nanmean(sub, axis=1)
        out[k + "_max"] = np.nanmax(sub, axis=1)
    np.savez(run / "histories.npz", **out)
    meta = {"label": label, "groups": {k: len(v) for k, v in g.items()}, "geom": geom, "n_times": len(ts), "t_read_s": round(time.time() - t0, 1)}
    (run / "histories_meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta))


if __name__ == "__main__":
    main(sys.argv[1])
