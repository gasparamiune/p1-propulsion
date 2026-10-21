#!/usr/bin/env python3
"""Hot-bound base residue (lead 22:54:03Z (3)): the OP-moment residue inside the LC3 / F2 hot-bound bases, report-only, no re-solve.

lc3_bound: hot = A + D with A = base TH + OP x Pc_max + PM x 7 (R3 neutral base hbg3 / hbh3) and D = sub-case - OP x Pc_max of the
SAME pose (post_lc3 / post_s3d: D = S - co['OP'] S_OP).  So the base OP rods (residue t_base Pc_max) enter through A, and each pose's own
OP rods (t_pose Pc_max) are taken out of D.  Implied rod force of A + D:
  * rods prescribed in the cold sub-case (LC3 runaway: fb_run, 609 N; GS: EAX / EAY at the +/-F_d corners, 441-552 N): prescribed +
    (t_base - t_pose) Pc_max  -> the base residue is REPLACED by the prescribed rods, to within the pose difference;
  * rods reacting inertia (TD, LC6): inertia reactions + t_base Pc_max -> the base residue ADDS (+86 / +66 N).
Governing pose of each GM-01 / GM-02 hot-bound cell = the pose whose increment envelope vmD is largest at the cell node (the bound uses the
node-wise maximum over the poses).  Estimate of the effect [DERIVED; ASSUMED linear in the lever rod force with the whole vmD rod-driven,
an upper estimate]: dvm = vmD(n) |d_rod| / F_prescribed.  t_base = the R3 neutral OP rods (same R3 neutral mesh and OP load; ASSUMED).
Writes results/v352/hb_base_residue_v352.json only.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path("/home/claude/work/fea3d")
RES = ROOT / "results"
PC_MAX = 2.501
OUT = RES / "v352" / "hb_base_residue_v352.json"
STOPS = ["stop000", "stop045", "stop090", "stop135", "stop180", "stop225", "stop270", "stop315"]
CONES = ["neutral", "alpha+", "alpha-", "beta+", "beta-", "combined045", "combined135", "combined225", "combined315"]
LEVER_ROD = {"GM-01": 0, "GM-02": 1}            # servo 1 lever on GM-01 (ROD_1), servo 2 lever on GM-02 (ROD_2)


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def cell(path, part):
    """the lower of the GVLO (g3) and GVHI (h3) lever-root extracts: summary_min_over_states_regular (= all-node at these nodes)."""
    rows = []
    for v in ("g3", "h3"):
        q = Path(str(path).replace("g3", v))
        r = dict(json.loads(q.read_text())["summary_min_over_states_regular"][part])
        r["base"] = v
        rows.append(r)
    return min(rows, key=lambda s: s["MS_ult_bound"])


def main():
    m = json.loads((RES / "v352" / "icd_momentfree_v352.json").read_text())["runs"]
    t = {k.replace("pose_", "").replace("_v352r3R3", ""): np.asarray(v["OP_rods_statics_N_per_MPa"]) for k, v in m.items()}
    t_base = t["neutral"]
    out = {"id": "hb_base_residue_v352", "doc": __doc__, "evidence": "DERIVED (statics of the posted rods; envelope read-back); ASSUMED where stated",
           "Pc_max_MPa": PC_MAX, "t_base_N_per_MPa": t_base.tolist(), "base_residue_N": (t_base * PC_MAX).round(1).tolist(), "cells": {}, "ranges": {}, "files_sha16": {}}
    srcs = {"LC3": ("f1_lc3_hot_bound_v352g3_x.json", "lc3_env_pose_{}_v352r3R3.npz", STOPS, 609.0, "LC3 runaway (fb_run, rods prescribed)"),
            "F2": ("f1_lc3_hot_bound_s3d_v352g3_x.json", "s3d_env_pose_{}_v352r3R3.npz", CONES, None, "GS (rods prescribed at +/-F_d) / TD, LC6 (inertia)")}
    for case, (hb, envp, poses, Fp, what) in srcs.items():
        dd = np.array([(t_base - t[p]) * PC_MAX for p in poses])
        out["ranges"][case] = {"poses": poses, "d_rod_N": dd.round(1).tolist(), "ROD_1_min_max_N": [float(dd[:, 0].min()), float(dd[:, 0].max())],
                               "ROD_2_min_max_N": [float(dd[:, 1].min()), float(dd[:, 1].max())], "rods": what}
        for part, ir in LEVER_ROD.items():
            c = cell(RES / hb, part)
            n = int(c["node"])
            vmD = {p: float(np.load(RES / envp.format(p))["vmD"][n]) for p in poses}
            pg = max(vmD, key=vmD.get)
            d_rod = (t_base - t[pg]) * PC_MAX
            F = Fp if Fp else (441.0 if pg == "neutral" else 552.0)
            dvm = vmD[pg] * abs(d_rod[ir]) / F
            out["cells"][f"{case} {part}"] = {
                "cell_MS_bound": [round(c["MS_bound"], 4), round(c["MS_ult_bound"], 4)], "node": n, "state": c["state"], "base": c.get("base"),
                "vmD_by_pose_MPa": {p: round(v, 2) for p, v in vmD.items()}, "governing_pose": pg,
                "lever_rod": ("ROD_1", "ROD_2")[ir], "d_rod_N": d_rod.round(2).tolist(),
                "sign_on_lever_rod": ("+ (A + D carries more tension than prescribed)" if d_rod[ir] > 0 else "- (less tension than prescribed)"),
                "F_prescribed_N": F, "d_rod_over_F": round(abs(d_rod[ir]) / F, 4), "dvm_upper_estimate_MPa": round(dvm, 2)}
        for v in ("g3", "h3"):
            out["files_sha16"][hb.replace("g3", v)] = sha16(RES / hb.replace("g3", v))
    out["files_sha16"]["v352/icd_momentfree_v352.json"] = sha16(RES / "v352" / "icd_momentfree_v352.json")
    out["files_sha16"]["scripts/hb_base_residue_v352.py"] = sha16(Path(__file__))
    OUT.write_text(json.dumps(out, indent=1))
    for k, v in out["cells"].items():
        print(k, v["cell_MS_bound"], "n%d" % v["node"], v["governing_pose"], v["lever_rod"], v["d_rod_N"], v["sign_on_lever_rod"][:2],
              "dF/F", v["d_rod_over_F"], "dvm<=", v["dvm_upper_estimate_MPa"], "vmD", v["vmD_by_pose_MPa"][v["governing_pose"]])
    for k, v in out["ranges"].items():
        print(k, "ROD_1", v["ROD_1_min_max_N"], "ROD_2", v["ROD_2_min_max_N"])


if __name__ == "__main__":
    main()
