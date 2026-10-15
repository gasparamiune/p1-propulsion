#!/usr/bin/env python3
"""REV-MECH-1, 2026-10-13 - free differential thermal growth across the TC-01 (6061-T6, external M63x1.5 6e) / TC-09 (IN718,
internal 6H) thread interface, from the S-AX deck temperatures of a given state (own parser).  Interface nodes: TC-01 nodes
coincident (|dX| < 1e-6 mm) with TC-09 nodes.  Free radial growth difference per node:
   du = r * [alpha_Al(T1) (T1 - 20) - alpha_718(T9) (T9 - 20)]   (author's mean CTEs from 20 C, materials_v1p4, linear interp.)
compared with half the 6e fundamental deviation on the pitch diameter, es = -(50 + 11 P) um = 66.5 um for P = 1.5 (ISO 965-1,
AS RECALLED) -> 33.25 um radial.  Positive du = the aluminium male grows more (clearance closes).  DERIVED (free growth; no
pressure, no constraint) - an indicator for the tie choice, not a stress result.
Usage: python -I rm1_thread_fit_T.py <materials_json> <out_json> <label=sax.inp> [<label=sax.inp> ...]
"""
import json
import sys

import numpy as np


def parse(inp):
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
    return nodes, elems, elsets, temps


def main():
    M = json.load(open(sys.argv[1]))["materials"]
    out = sys.argv[2]
    aA, aI = M["AL6061-T6"]["alpha"], M["IN718"]["alpha"]
    al = lambda T: float(np.interp(T, aA["T_C"], aA["v"]))
    a7 = lambda T: float(np.interp(T, aI["T_C"], aI["v"]))
    res = {"who": "REV-MECH-1", "half_6e_allowance_mm": 0.06650 / 2.0, "states": {}}
    for arg in sys.argv[3:]:
        lab, inp = arg.split("=", 1)
        nodes, elems, elsets, temps = parse(inp)
        n01 = sorted({q for e in elsets["P_TC_01"] for q in elems[e]})
        n09 = sorted({q for e in elsets["P_TC_09"] for q in elems[e]})
        X9 = np.array([nodes[i] for i in n09])
        rows = []
        for i in n01:
            r, z = nodes[i]
            d = np.hypot(X9[:, 0] - r, X9[:, 1] - z)
            k = int(np.argmin(d))
            if d[k] < 1e-6 and r > 30.0:          # thread band (r ~ 30.6-31.5); excludes the TC-08 / bore interfaces
                T1, T9 = temps[i] - 273.15, temps[n09[k]] - 273.15
                du = r * (al(T1) * (T1 - 20.0) - a7(T9) * (T9 - 20.0))
                rows.append((z, r, T1, T9, du))
        if not rows:
            res["states"][lab] = {"pairs": 0}
            continue
        A = np.array(rows)
        res["states"][lab] = {"deck": inp, "pairs": len(rows), "z_range_mm": [float(A[:, 0].min()), float(A[:, 0].max())],
                              "r_range_mm": [float(A[:, 1].min()), float(A[:, 1].max())],
                              "T_TC01_C": [float(A[:, 2].min()), float(A[:, 2].max())],
                              "T_TC09_C": [float(A[:, 3].min()), float(A[:, 3].max())],
                              "du_free_mm": [float(A[:, 4].min()), float(A[:, 4].max())],
                              "du_max_over_half_6e": float(A[:, 4].max() / (0.0665 / 2.0))}
    open(out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
