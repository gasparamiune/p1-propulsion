import json, re, sys, numpy as np
for var in sys.argv[1:]:
    meta = json.load(open(f"u_{var}.json"))
    txt = open(f"u_{var}.dat").read()
    blocks = re.split(r"S T E P", txt)[1:]
    for si, b in enumerate(blocks, 1):
        m = re.search(r"displacements \(vx,vy,vz\) for set CONN.*?\n\n(.*?)(\n\n|\Z)", b, re.S)
        U = {}
        for line in m.group(1).strip().splitlines():
            p = line.split(); U[int(p[0])] = np.array(list(map(float, p[1:4])))
        tot = np.zeros(3)
        k = meta["k"]
        if var.startswith("eqref"):
            for lab, d, A, a in meta["spr"]:
                e = np.zeros(3); e[d - 1] = 1.0
                tot += k * ((U[a] - U[A]) @ e) * e
        else:
            for lab, A, B, dirs in meta["bush"]:
                for d, v in dirs:
                    e = np.zeros(3); e[d - 1] = 1.0
                    tot += k * ((U[B] - U[A]) @ e) * e
        rod = k * (0 - U[meta["rodE"]][2])
        print(var, "step", si, "springs on E:", np.round(tot, 4), " rod Z on E:", round(rod, 6), " | B refs U:", [np.round(U[n] * 1e6, 2).tolist() for n in (503, 507)])
