#!/usr/bin/env python3
"""REV-MECH-1, 2026-10-13 - second exact re-run check (state B1_21.65) and an ESTIMATE of the effect of the TC-09 / NZ-02 radial
contact that the linear S-AX does not carry, on the LC1 margin of the TC-09 holder (own code; no author module imported).

1. Re-run equality: the author's deck runs/structural/L1_TC09IN718_thJ1revB_TC09IN/B1_21.65/sax.inp re-solved (ccx 2.21, nice 15,
   1 thread); the five unit responses parsed from the new .frd are compared with the author's res.npz (exact equality).
2. LC1 combination (coefficients read in sax.py combos(): OP = Pc_max 2.501007 MPa, PM = 7.0 MPa, G = 35.8/9.80665 g) at the stored
   governing TC-09 node (25.0, -204.75): von Mises vs the author's stored 295.6 MPa (repeatability of the combination).
3. Interface pairs TC-09 bore / NZ-02 OD (coincident node pairs, |dX| < 1e-6 mm): radial gap change g = (u_r(TC-09) - u_r(NZ-02))
   for LC1; negative = interpenetration (author convention, normal pointing from NZ-02 to TC-09 = +r).
4. ESTIMATE: superpose, at each TC-09 bore node of the closed zone, the plane-stress compound-cylinder response to the local
   interference delta = -g (linear in delta; coefficients from rm1_hand_checks.json, carbon-phenolic E 7/12/20 GPa ASSUMED):
   added sigma_r = -p, added sigma_theta = s_theta; recompute von Mises and MS = Fty(T)/(1.5 vm) - 1 with the author's IN718 table
   (DATASHEET, linear in T).  This is a bound-type estimate (no friction, plane stress, ASSUMED stack moduli), not an FE result.
Usage: python -I rm1_tc09_contact_superpose.py <rerun_dir> <author_state_dir> <materials_json> <hand_checks_json> <out_json>
"""
import json
import sys
from pathlib import Path

import numpy as np


def parse_inp(inp):
    nodes, elems, elsets, temps = {}, {}, {}, {}
    mode, cur = None, None
    with open(inp) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("**"):
                continue
            if line.startswith("*"):
                kw = line.upper()
                cur = None
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
                else:
                    mode = None
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


def parse_frd(frd, n):
    steps, cur, block, ncomp, arr = [], None, None, 0, None
    with open(frd) as fh:
        for line in fh:
            key = line[:3]
            if key == " -4":
                name = line[3:].split()[0]
                block = name if name in ("DISP", "STRESS") else None
                if block:
                    ncomp = 3 if block == "DISP" else 6
                    arr = np.full((n, ncomp), np.nan)
                continue
            if block is None or key == " -5":
                continue
            if key == " -1":
                nid = int(line[3:13])
                arr[nid - 1, :] = [float(line[13 + 12 * k: 25 + 12 * k]) for k in range(ncomp)]
            elif key == " -3":
                if block == "DISP":
                    cur = {"DISP": arr}
                else:
                    cur["STRESS"] = arr
                    steps.append(cur)
                block = None
    return steps


def vm(s):
    sx, sy, sz, txy, tyz, tzx = (s[..., k] for k in range(6))
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3.0 * (txy ** 2 + tyz ** 2 + tzx ** 2))


def main():
    rerun, author, mats, hand, out = (Path(a) for a in sys.argv[1:6])
    A = np.load(author / "res.npz", allow_pickle=False)
    n = A["U1"].shape[0]
    st = parse_frd(rerun / "sax.frd", n)
    U = np.array([s["DISP"] for s in st])
    S = np.array([s["STRESS"] for s in st])
    mine = {"U1": U[0], "S1": S[0], "U_OP": U[1] - U[0], "S_OP": S[1] - S[0], "U_BL": U[2] - U[0], "S_BL": S[2] - S[0],
            "U_PM": U[3] - U[0], "S_PM": S[3] - S[0], "U_G": U[4] - U[0], "S_G": S[4] - S[0]}
    eq = {k: bool(np.array_equal(A[k], v)) for k, v in mine.items()}
    res = {"who": "REV-MECH-1", "state": "B1_21.65", "unit_responses_exactly_equal": eq, "all_equal": all(eq.values()),
           "dat_identical": (rerun / "sax.dat").read_bytes() == (author / "sax.dat").read_bytes()}
    nodes, elems, elsets, temps = parse_inp(rerun / "sax.inp")
    c = {"OP": 2.501007, "PM": 7.0, "G": 35.8 / 9.80665}
    SLC1 = mine["S1"] + c["OP"] * mine["S_OP"] + c["PM"] * mine["S_PM"] + c["G"] * mine["S_G"]
    ULC1 = mine["U1"] + c["OP"] * mine["U_OP"] + c["PM"] * mine["U_PM"] + c["G"] * mine["U_G"]
    p09 = sorted({q for e in elsets["P_TC_09"] for q in elems[e]})
    p02 = sorted({q for e in elsets["P_NZ_02"] for q in elems[e]})
    X09 = np.array([nodes[i] for i in p09])
    X02 = np.array([nodes[i] for i in p02])
    j = int(np.argmin(np.hypot(X09[:, 0] - 25.0, X09[:, 1] + 204.75)))
    g_id = p09[j]
    res["LC1_governing_TC09_recheck"] = {"node": g_id, "r_z": nodes[g_id], "vm_reviewer": float(vm(SLC1[g_id - 1])),
                                         "vm_author_stored": 295.6, "T_C": temps[g_id] - 273.15}
    # coincident pairs TC-09 / NZ-02
    pairs = []
    for a_i, (r, z) in zip(p02, X02):
        d = np.hypot(X09[:, 0] - r, X09[:, 1] - z)
        k = int(np.argmin(d))
        if d[k] < 1e-6:
            pairs.append((p09[k], a_i))
    # keep the OD (radial) interface: r of the pair >= 24.9
    pairs = [(b, a) for (b, a) in pairs if nodes[b][0] >= 24.9]
    M = json.loads(mats.read_text())["materials"]["IN718"]
    TF, VF = np.array(M["Fty"]["T_C"]), np.array(M["Fty"]["v"]) / 1e6
    H = json.loads(hand.read_text())["EXTRA_TC09_NZ02_interference_bound"]["cases"]
    rows = []
    for (b, a) in sorted(pairs, key=lambda q: nodes[q[0]][1]):
        gap = float(ULC1[b - 1, 0] - ULC1[a - 1, 0])
        T = temps[b] - 273.15
        fty = float(np.interp(T, TF, VF))
        s = SLC1[b - 1].copy()
        row = {"node_TC09": b, "r_z": nodes[b], "gap_change_mm": gap, "T_C": T, "Fty_MPa": fty,
               "vm_FE": float(vm(s)), "MS_FE_SF1.5": fty / (1.5 * float(vm(s))) - 1}
        delta = max(0.0, -gap)
        for h in H:
            k = delta / 0.137
            ds = np.zeros(6)
            ds[0] = -h["p_contact_r25_MPa"] * k            # sigma_r (x = r)
            ds[2] = h["added_hoop_TC09_bore_MPa"] * k       # sigma_theta (z = hoop in CAX)
            v2 = float(vm(s + ds))
            row[f"vm_with_contact_Ecp{int(h['E_carbon_phenolic_MPa'] / 1000)}GPa"] = v2
            row[f"MS_with_contact_Ecp{int(h['E_carbon_phenolic_MPa'] / 1000)}GPa"] = fty / (1.5 * v2) - 1
        rows.append(row)
    res["interface_pairs"] = len(rows)
    res["rows"] = rows
    if rows:
        res["min_gap_change_mm"] = min(r["gap_change_mm"] for r in rows)
        res["max_gap_change_mm"] = max(r["gap_change_mm"] for r in rows)
        res["min_MS_FE_on_interface"] = min(r["MS_FE_SF1.5"] for r in rows)
        for key in [k for k in rows[0] if k.startswith("MS_with_contact")]:
            res[f"min_{key}"] = min(r[key] for r in rows)
    out.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1, default=float))
    for r in rows[:: max(1, len(rows) // 12)]:
        print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}))


if __name__ == "__main__":
    main()
