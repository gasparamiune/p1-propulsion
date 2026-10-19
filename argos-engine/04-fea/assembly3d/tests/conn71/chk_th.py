import json, re, sys, numpy as np
for var in sys.argv[1:]:
    meta = json.load(open(f"u_{var}.json")); k = meta["k"]
    txt = open(f"u_{var}.dat").read()
    blocks = re.split(r"S T E P", txt)[1:]
    Us = []
    for b in blocks:
        m = re.search(r"displacements \(vx,vy,vz\) for set CONN.*?\n\n(.*?)(\n\n|\Z)", b, re.S)
        U = {}
        for line in m.group(1).strip().splitlines():
            p = line.split(); U[int(p[0])] = np.array(list(map(float, p[1:4])))
        Us.append(U)
    U0 = Us[0]
    print(var, "TH step: A1-B1 rel (um)", np.round((U0[501] - U0[503]) * 1e3, 2), "A2-B2", np.round((U0[505] - U0[507]) * 1e3, 2))
    for si, U in enumerate(Us[1:], 1):
        tot = np.zeros(3)
        if var.startswith("eqref"):
            for lab, d, A, a in meta["spr"]:
                e = np.zeros(3); e[d - 1] = 1.0
                tot += k * (((U[a] - U0[a]) - (U[A] - U0[A])) @ e) * e
        else:
            for lab, A, B, dirs in meta["bush"]:
                for d, v in dirs:
                    e = np.zeros(3); e[d - 1] = 1.0
                    tot += k * (((U[B] - U0[B]) - (U[A] - U0[A])) @ e) * e
        rod = k * (0 - (U[meta["rodE"]][2] - U0[meta["rodE"]][2]))
        print(var, "load step", si, "springs on E (increment, undeformed dirs):", np.round(tot, 3), "rod", round(rod, 4))
