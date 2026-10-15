#!/usr/bin/env python3
"""REV-MECH-1, 2026-10-13 - temperature of NZ-02 (carbon-phenolic sleeve) at its two radial interfaces in the LC1 state B1_21.65
(deck temperatures, own parser), over the axial band where the TC-09 / NZ-02 radial gap closes in LC1 (z -229.6 .. -210.75 from
rm1_tc09_contact_B1_21.65.json), and the author's carbon-phenolic Sc(T) (materials_v1p4, ASSUMED, linear in T) at those
temperatures, to compare with the ESTIMATED contact pressure (rm1_hand_checks.json, 34-39.5 MPa).  ESTIMATE, not an FE result.
Usage: python -I rm1_nz02_interface_T.py <sax.inp> <materials_json> <contact_json> <out_json>
"""
import json
import sys
from pathlib import Path

import numpy as np


def parse(inp):
    nodes, elems, elsets, temps = {}, {}, {}, {}
    mode, cur = None, None
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
    inp, mats, con, out = (Path(a) for a in sys.argv[1:5])
    nodes, elems, elsets, temps = parse(inp)
    C = json.loads(con.read_text())
    zs = [r["r_z"][1] for r in C["rows"] if r["gap_change_mm"] < 0]
    z0, z1 = min(zs), max(zs)
    n02 = sorted({q for e in elsets["P_NZ_02"] for q in elems[e]})
    X = np.array([nodes[i] for i in n02])
    T = np.array([temps[i] - 273.15 for i in n02])
    band = (X[:, 1] >= z0 - 1e-6) & (X[:, 1] <= z1 + 1e-6)
    r_in, r_out = X[band, 0].min(), X[band, 0].max()
    M = json.loads(mats.read_text())["materials"]["CARBON-PHENOLIC"]
    sc = lambda t: float(np.interp(t, M["Sc"]["T_C"], np.array(M["Sc"]["v"]) / 1e6))
    res = {"who": "REV-MECH-1", "state": "B1_21.65 (LC1)", "z_band_mm": [z0, z1], "NZ02_r_range_in_band_mm": [r_in, r_out],
           "T_char_C_author": M["T_char_C"]["v"], "Sc_table_author": {"T_C": M["Sc"]["T_C"], "MPa": [v / 1e6 for v in M["Sc"]["v"]],
                                                                  "tag": M["Sc"]["tag"]}}
    for lab, rr in (("ID_side", r_in), ("OD_side", r_out)):
        m = band & (np.abs(X[:, 0] - rr) < 0.05)
        t = T[m]
        res[lab] = {"r_mm": rr, "n_nodes": int(m.sum()), "T_C_min": float(t.min()), "T_C_max": float(t.max()),
                    "Sc_at_Tmax_MPa": sc(float(t.max())), "Sc_at_Tmin_MPa": sc(float(t.min())),
                    "fraction_above_T_char": float(np.mean(t > M["T_char_C"]["v"]))}
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
