#!/usr/bin/env python3
"""REV-MECH-1, 2026-10-13 - temperature of the TC-01 case at the gimbal collar band (groove OD, r >= 31.0 mm, |z| <= 10 mm) in a
given S-AX state deck (own parser), to test the gimbal_strength.py assumption 'ring 60 C ASSUMED' in flight (LC1/LC3 state
B1_21.65 = end of the max-thrust burn).  DERIVED from the SIM thermal field mapped into the deck.
Usage: python -I rm1_collar_band_T.py <sax.inp> <out_json>
"""
import json
import sys

import numpy as np


def main():
    inp, out = sys.argv[1], sys.argv[2]
    nodes, elems, elsets, temps = {}, {}, {}, {}
    mode = cur = None
    for raw in open(inp):
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            kw = line.upper()
            mode = None
            if kw.startswith("*NODE") and "PRINT" not in kw and "FILE" not in kw:
                mode = "node"
            elif kw.startswith("*ELEMENT"):
                mode = "elem"
            elif kw.startswith("*ELSET"):
                mode = "elset"
                cur = [t.split("=")[1].strip() for t in line.split(",") if t.strip().upper().startswith("ELSET=")][0]
                elsets.setdefault(cur, [])
            elif kw.startswith("*TEMPERATURE"):
                mode = "temp"
            continue
        if mode == "node":
            t = line.split(",")
            nodes[int(t[0])] = (float(t[1]), float(t[2]))
        elif mode == "elem":
            t = [int(x) for x in line.rstrip(",").split(",") if x.strip()]
            elems[t[0]] = t[1:]
        elif mode == "elset":
            elsets[cur].extend(int(x) for x in line.rstrip(",").split(",") if x.strip())
        elif mode == "temp":
            t = line.split(",")
            temps[int(t[0])] = float(t[1])
    n01 = sorted({q for e in elsets["P_TC_01"] for q in elems[e]})
    X = np.array([nodes[i] for i in n01])
    T = np.array([temps[i] - 273.15 for i in n01])
    m = (X[:, 0] >= 31.0) & (np.abs(X[:, 1]) <= 10.0)
    res = {"who": "REV-MECH-1", "deck": inp, "collar_band_nodes": int(m.sum()), "collar_band_T_C": [float(T[m].min()), float(T[m].max())],
           "TC01_T_C": [float(T.min()), float(T.max())], "author_assumption": "gimbal_strength.py: ring/frame/horns 60 C ASSUMED in flight"}
    open(out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
