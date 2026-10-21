"""Diagnostic: strain-energy share of every SPRINGA set per mode (mass-normalised modes: total SE = omega^2/2)."""
import sys, gzip, json, math, re
import numpy as np
run = sys.argv[1]; nmodes = int(sys.argv[2]) if len(sys.argv) > 2 else 6
sd = f"/home/claude/work/fea3d/runs/{run}/B1_21.65"
txt = gzip.open(f"{sd}/f1.inp.gz", "rt").read().splitlines()
nodes, sets, k = {}, {}, {}
i = 0; mode = None; cur = None
while i < len(txt):
    L = txt[i]
    u = L.upper()
    if u.startswith("*NODE") and "FILE" not in u and "PRINT" not in u:
        mode = "node"
    elif u.startswith("*ELEMENT") and "SPRINGA" in u:
        mode = "spr"; cur = re.search(r"ELSET=(\w+)", L).group(1); sets[cur] = []
    elif u.startswith("*SPRING") and "ELSET" in u:
        nm = re.search(r"ELSET=(\w+)", L).group(1)
        j = i + 1
        while txt[j].strip() == "":
            j += 1
        k[nm] = float(txt[j].split(",")[0]); mode = None; i = j
    elif u.startswith("*"):
        mode = None
    elif mode == "node":
        p = L.split(",")
        nodes[int(p[0])] = np.array([float(x) for x in p[1:4]])
    elif mode == "spr":
        p = [int(x) for x in L.split(",")[:3]]
        sets[cur].append((p[1], p[2]))
    i += 1
Z = np.load(f"{sd}/fields.npz")
U = Z["U_FREQ"].astype(np.float64)
md = json.load(open(f"{sd}/modal.json"))
f = np.array([m["f_Hz"] for m in md["modes"]])
print("sets", {s: (len(v), k.get(s)) for s, v in sets.items()})
for m in range(nmodes):
    om2 = (2 * math.pi * f[m]) ** 2
    tot = om2 / 2
    row = {}
    for s, pairs in sets.items():
        e = 0.0
        for a, b in pairs:
            d = nodes[b] - nodes[a]; d /= np.linalg.norm(d)
            de = (U[m, b] - U[m, a]) @ d
            e += 0.5 * k[s] * de * de
        row[s] = e / tot
    print(f"mode {m+1} f {f[m]:.1f} Hz spring SE shares", {s: round(v, 4) for s, v in row.items()}, "sum", round(sum(row.values()), 4))
