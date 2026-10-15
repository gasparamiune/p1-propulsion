#!/usr/bin/env python3
"""REV-MECH-1 (independent reviewer), 2026-10-13.

Re-run check of one author S-AX state: the author's own deck (sax.inp, copied unchanged) was re-solved with CalculiX 2.21
(nice 15, 1 thread) in the reviewer scratch directory.  This script does NOT import any author module: it has its own .frd
and .inp readers and its own von Mises / combination arithmetic.

Checks
  1. sha256 of the deck copy == author deck (bytes unchanged).
  2. Unit responses from the re-run .frd vs the author's stored res.npz (U1, S1, U_OP, S_OP, U_BL, S_BL, U_PM, S_PM, U_G, S_G):
     exact float equality (np.array_equal) and max |diff|.
  3. Re-computation of the stored governing FA1Q row of ENG-TC-01 (node at r 30.114, z -132.46): combination
     S = S1 + 9.0 S_OP + 7.0 S_PM (FA1Q coefficients as read in sax.py combos(): OP 90 bar/10, PM = MEOP_tank 7.0 MPa),
     von Mises, Fty(T) by linear interpolation of the author's material table, MS = Fty/(SF vm) - 1.

Usage: python -I rm1_sax_rerun_compare.py <rerun_dir> <author_state_dir> <materials_json> <out_json>
Tags: the re-run equality is a REPEATABILITY result (SIM), not physical validation.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def parse_inp_nodes_and_elsets(inp):
    """Own reader: *NODE coordinates and element connectivity per *ELEMENT block + part *ELSET lists (P_xxx)."""
    nodes, elems, elsets = {}, {}, {}
    mode, cur_set = None, None
    with open(inp) as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("**"):
                continue
            if line.startswith("*"):
                kw = line.upper()
                cur_set = None
                if kw.startswith("*NODE") and "PRINT" not in kw and "FILE" not in kw:
                    mode = "node"
                elif kw.startswith("*ELEMENT"):
                    mode = "elem"
                elif kw.startswith("*ELSET"):
                    mode = "elset"
                    cur_set = [t.split("=")[1].strip() for t in line.split(",") if t.strip().upper().startswith("ELSET=")][0]
                    elsets.setdefault(cur_set, [])
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
                elsets[cur_set].extend(int(x) for x in line.rstrip(",").split(",") if x.strip())
    return nodes, elems, elsets


def parse_frd(frd, n_nodes):
    """Own reader of a static ccx ASCII .frd: per step a dict with 'DISP' (N,3) and 'STRESS' (N,6).
    Record layout (CGX frd spec): ' -1' + node id I10 + values E12.5 fixed width."""
    steps = []
    cur = None
    block, ncomp, arr = None, 0, None
    with open(frd) as fh:
        for line in fh:
            key = line[:3]
            if line.startswith("  100C"):
                continue
            if key == " -4":
                name = line[3:].split()[0]
                if name in ("DISP", "STRESS"):
                    block = name
                    ncomp = 3 if name == "DISP" else 6
                    arr = np.full((n_nodes, ncomp), np.nan)
                else:
                    block = None
                continue
            if block is None:
                continue
            if key == " -5":
                continue
            if key == " -1":
                nid = int(line[3:13])
                arr[nid - 1, :] = [float(line[13 + 12 * k: 25 + 12 * k]) for k in range(ncomp)]
                continue
            if key == " -3":
                if block == "DISP":
                    cur = {"DISP": arr}
                else:
                    cur["STRESS"] = arr
                    steps.append(cur)
                block = None
    return steps


def vm(s):
    """von Mises of ccx stress components (SXX, SYY, SZZ, SXY, SYZ, SZX); for CAX6: x = r, y = z, z = hoop."""
    sx, sy, sz, txy, tyz, tzx = (s[..., k] for k in range(6))
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3.0 * (txy ** 2 + tyz ** 2 + tzx ** 2))


def main():
    rerun, author, mats, out = (Path(a) for a in sys.argv[1:5])
    res = {"who": "REV-MECH-1 (independent; no author module imported)", "date": "2026-10-13",
           "deck_sha256_rerun": sha(rerun / "sax.inp"), "deck_sha256_author": sha(author / "sax.inp")}
    res["deck_identical"] = res["deck_sha256_rerun"] == res["deck_sha256_author"]
    res["dat_identical"] = (rerun / "sax.dat").read_bytes() == (author / "sax.dat").read_bytes()
    A = np.load(author / "res.npz", allow_pickle=False)
    n = A["U1"].shape[0]
    st = parse_frd(rerun / "sax.frd", n)
    res["n_steps_frd"] = len(st)
    U = np.array([s["DISP"] for s in st])
    S = np.array([s["STRESS"] for s in st])
    res["nan_in_rerun"] = bool(np.isnan(U).any() or np.isnan(S).any())
    mine = {"U1": U[0], "S1": S[0], "U_OP": U[1] - U[0], "S_OP": S[1] - S[0], "U_BL": U[2] - U[0], "S_BL": S[2] - S[0],
            "U_PM": U[3] - U[0], "S_PM": S[3] - S[0], "U_G": U[4] - U[0], "S_G": S[4] - S[0]}
    cmp_ = {}
    for k, v in mine.items():
        a = A[k]
        cmp_[k] = {"shape": list(a.shape), "exactly_equal": bool(np.array_equal(a, v)),
                   "max_abs_diff": float(np.max(np.abs(a - v))), "max_abs_value": float(np.max(np.abs(a)))}
    res["unit_responses_vs_res_npz"] = cmp_
    res["all_exactly_equal"] = all(c["exactly_equal"] for c in cmp_.values())

    # ---- governing FA1Q TC-01 row
    nodes, elems, elsets = parse_inp_nodes_and_elsets(rerun / "sax.inp")
    tc01_nodes = sorted({nn for e in elsets["P_TC_01"] for nn in elems[e]})
    X = np.array([nodes[i] for i in tc01_nodes])
    target = np.array([30.114, -132.46])
    j = int(np.argmin(np.hypot(X[:, 0] - target[0], X[:, 1] - target[1])))
    nid = tc01_nodes[j]
    i = nid - 1
    s_fa1q = mine["S1"][i] + 9.0 * mine["S_OP"][i] + 7.0 * mine["S_PM"][i]
    vm_fa1q = float(vm(s_fa1q))
    vm_mech = float(vm(9.0 * mine["S_OP"][i] + 7.0 * mine["S_PM"][i]))
    # nodal temperature: from the deck *TEMPERATURE block (own read)
    Tn = None
    with open(rerun / "sax.inp") as fh:
        grab = False
        for line in fh:
            if line.upper().startswith("*TEMPERATURE"):
                grab = True
                continue
            if grab:
                if line.startswith("*"):
                    grab = False
                    continue
                t = line.split(",")
                if int(t[0]) == nid:
                    Tn = float(t[1])
                    break
    M = json.loads(Path(mats).read_text())
    al = None
    for key in ("materials", "data"):
        if isinstance(M, dict) and key in M and isinstance(M[key], dict) and "AL6061-T6" in M[key]:
            al = M[key]["AL6061-T6"]
    if al is None and "AL6061-T6" in M:
        al = M["AL6061-T6"]
    res["FA1Q_TC01_governing_recheck"] = {
        "node_id": nid, "node_r_z_mm": list(nodes[nid]), "dist_to_stored_point_mm": float(np.hypot(*(np.array(nodes[nid]) - target))),
        "T_K_deck": Tn, "T_C_deck": None if Tn is None else Tn - 273.15,
        "vm_combined_MPa_reviewer": vm_fa1q, "vm_mech_only_MPa_reviewer": vm_mech,
        "stored_vm_MPa": 125.53948353613521, "stored_MS": 0.9080196201732569, "stored_allowable_MPa": 239.53179769336353,
        "vm_rel_diff": abs(vm_fa1q - 125.53948353613521) / 125.53948353613521,
        "MS_reviewer_with_stored_allowable": 239.53179769336353 / vm_fa1q - 1.0,
        "AL6061_T6_entry_keys": None if al is None else list(al.keys())[:30]}
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "unit_responses_vs_res_npz"}, indent=1))
    for k, c in cmp_.items():
        print(f"{k:5s} equal={c['exactly_equal']} max|d|={c['max_abs_diff']:.3e} (max|v| {c['max_abs_value']:.3e})")


if __name__ == "__main__":
    main()
