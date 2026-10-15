"""Per-part peak temperatures from a (possibly partial) thermal .frd using the part elsets of the .inp (04-fea/thermal tools, v1, 2026-10-12).
Usage: python frd_part_peaks.py <run_dir> [t_max_s]   (reads <label>.inp and a copy of <label>.frd)"""
import sys, re, shutil, tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ax_thermal as at


def part_nodes(inp):
    elem_nodes, sets, cur, mode = {}, {}, None, None
    for line in open(inp):
        if line.startswith("*"):
            u = line.upper()
            if u.startswith("*ELEMENT"):
                mode = "E"
            elif u.startswith("*ELSET") and "ELSET=P_" in u:
                mode = "S"; cur = line.split("=")[1].strip(); sets[cur] = []
            else:
                mode = None
            continue
        if mode == "E":
            p = [int(x) for x in line.replace(",", " ").split()]
            elem_nodes[p[0]] = p[1:]
        elif mode == "S":
            sets[cur] += [int(x) for x in line.replace(",", " ").split()]
    return {k: np.unique(np.concatenate([elem_nodes[e] for e in v])) for k, v in sets.items()}


def main(run_dir, tmax=None):
    run_dir = Path(run_dir)
    inp = next(run_dir.glob("*.inp")); frd = inp.with_suffix(".frd")
    tmp = Path(tempfile.mkdtemp()) / "c.frd"; shutil.copy(frd, tmp)
    pn = part_nodes(inp)
    peak = {k: (-1.0, 0.0, 0) for k in pn}
    X = {}
    with open(inp) as fh:
        mode = False
        for line in fh:
            if line.startswith("*"):
                mode = line.upper().startswith("*NODE,") or line.upper().startswith("*NODE\n")
                continue
            if mode:
                q = line.split(",")
                X[int(q[0])] = (float(q[1]), float(q[2]))
    for t, vals in at.read_frd_nt(tmp):
        if tmax is not None and t > tmax:
            break
        T = np.zeros(max(vals) + 1); T[np.fromiter(vals.keys(), int)] = np.fromiter(vals.values(), float)
        for k, nn in pn.items():
            j = int(np.argmax(T[nn])); v = T[nn][j]
            if v > peak[k][0]:
                peak[k] = (v, t, int(nn[j]))
    tmp.unlink()
    for k, (v, t, n) in sorted(peak.items()):
        print(f"{k:14s} max {v - 273.15:8.1f} C at t {t:8.2f} s  node {n} (r, z) = {X.get(n)}")


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else None)
