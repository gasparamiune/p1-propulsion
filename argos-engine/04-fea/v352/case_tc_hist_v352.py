"""v3.5.2 (b) package input (lead 2026-10-20 ~04:13Z, items 2-4): node temperature histories from the v3.5.2 axisymmetric thermal runs
(merged NF2b B1 + A1, gap variants GVLO / GVHI B1), streamed once from each <label>.frd.gz (nothing unzipped on disk).

Writes tb70/hist/<label>_hist.npz:
  t_s                    all output frames of the run (s, total time)
  od_nodes / od_X / od_T case OD nodes of ENG-TC-01 (r >= r_OD - 0.05 mm): ids, (r, z) mm thermal frame, T (K) [frame, node] float32
  part_max / parts       maximum temperature of every part per frame (K)
  n_<PN> / X_<PN> / T_<PN>  all nodes of ENG-TC-01, ENG-TC-02, ENG-TC-03: ids, (r, z), T (K) [frame, node] float32
  info                   json: label, inj_face z, r_OD, n_frames, segments, steps, frd sha256/16
Node ids: envelope_nodes.npz holds 0-based X indices; the frd node id is index + 1 (ax_thermal writes nodes q+1 in X order).
Evidence class of the content: SIM (CalculiX thermal) as produced by run_thermal.py; this script only reads.
Mechanical, 2026-10-20.  Usage: case_tc_hist_v352.py <label> [<label> ...]"""
import sys, json, gzip, hashlib, time
from pathlib import Path
import numpy as np

RUNS = Path("/home/claude/work/mechanical/runs/thermal")
OUT = Path(__file__).resolve().parent / "hist"
PARTS_FULL = ("ENG-TC-01", "ENG-TC-02", "ENG-TC-03")


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def main(label):
    rd = RUNS / label
    t0 = time.time()
    z = np.load(rd / "envelope_nodes.npz", allow_pickle=True)
    X, E, pn = z["X"], z["E"], z["pn"]
    meta = json.loads(next(rd.glob("*_meta.json")).read_text())
    nodes_of = {}
    for e, p in zip(E, pn):
        nodes_of.setdefault(str(p), set()).update(int(n) for n in e)
    parts = sorted(nodes_of)
    pidx = {p: np.array(sorted(nodes_of[p]), int) for p in parts}
    case = pidx["ENG-TC-01"]
    r_od = float(X[case, 0].max())
    od = case[X[case, 0] >= r_od - 0.05]
    frd = next(rd.glob("*.frd.gz"))
    N = len(X)
    ts, rows = [], []
    with gzip.open(frd, "rt") as fh:
        t, inblk, vals = None, False, None
        for line in fh:
            if line.startswith("  100CL"):
                t = float(line[12:24])
                continue
            if line.startswith(" -4  NDTEMP"):
                inblk, vals = True, []
                continue
            if inblk:
                if line.startswith(" -1"):
                    vals.append(line)
                elif line.startswith(" -3"):
                    inblk = False
                    ids = (int(vals[0][3:13]), int(vals[-1][3:13]))
                    assert len(vals) == N and ids == (1, N), (label, t, len(vals), ids)
                    rows.append(np.array([float(v[13:25]) for v in vals], np.float32))
                    ts.append(t)
    A = np.vstack(rows)                                    # [frame, node] K
    out = {"t_s": np.array(ts), "od_nodes": od, "od_X": X[od], "od_T": A[:, od], "parts": np.array(parts),
           "part_max": np.vstack([A[:, pidx[p]].max(axis=1) for p in parts])}
    for p in PARTS_FULL:
        k = p.replace("ENG-", "").replace("-", "")
        out[f"n_{k}"], out[f"X_{k}"], out[f"T_{k}"] = pidx[p], X[pidx[p]], A[:, pidx[p]]
    info = {"label": label, "frd": frd.name, "frd_sha256_16": sha16(frd), "n_frames": len(ts), "n_nodes": N, "r_OD_mm": r_od,
            "n_od_nodes": int(len(od)), "inj_face_z_mm": float(meta["case"]["monitors"]["insert_TC03_face"][1]), "segments_s": meta["segments_s"], "steps": meta["steps"],
            "gap_variant": (meta.get("gap_variant") or {}).get("name", "merged (perfect contact)"), "t_read_s": round(time.time() - t0, 1)}
    out["info"] = np.array(json.dumps(info))
    OUT.mkdir(exist_ok=True)
    f = OUT / f"{label}_hist.npz"
    np.savez_compressed(f, **out)
    info["out"] = str(f)
    info["out_sha256_16"] = sha16(f)
    print(json.dumps(info))


if __name__ == "__main__":
    for lab in sys.argv[1:]:
        main(lab)
