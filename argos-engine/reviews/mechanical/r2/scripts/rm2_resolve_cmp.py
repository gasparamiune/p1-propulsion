"""REV-MECH-2 (independent reviewer): cheap re-solve check of FEA3D's stored unit fields.

The FEA3D deck runs/fa1_c71/A1_22.2/f1.inp.gz was cut after its second step (lines 1-561367: model + step TH + step OP, unchanged
text) and re-solved with the installed CalculiX 2.21 (ccx) by the reviewer.  This script parses the reviewer's ASCII .frd (own parser)
and compares DISP and STRESS of both steps with FEA3D's stored fields.npz (U_TH, S_TH, U_OP, S_OP), over all nodes and at the
governing nodes used in the review (TC-01 8314 / 580, TC-02 25946 / 27955), and re-computes the FA1S von Mises there from the
re-solved fields (OP x 15.1038 + PM is not re-solved, so only the OP part is compared; the FA1S check uses the stored PM increment).

usage: python -I rm2_resolve_cmp.py <rs.frd> <fields.npz> <out.json>
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np


def read_frd(path):
    blocks = []          # list of (name, ncomp, {node: values})
    cur = None
    with open(path, "rt", errors="replace") as f:
        for line in f:
            if line.startswith(" -4"):
                parts = line.split()
                cur = {"name": parts[1], "ncomp": int(parts[2]), "data": {}}
                continue
            if cur is None:
                continue
            if line.startswith(" -5"):
                continue
            if line.startswith(" -1"):
                nd = int(line[3:13])
                n = cur["ncomp"]
                vals = []
                for i in range(n):
                    s = line[13 + 12 * i: 25 + 12 * i]
                    if not s.strip():
                        break
                    vals.append(float(s))
                cur["data"][nd] = vals
                continue
            if line.startswith(" -3"):
                blocks.append(cur)
                cur = None
    return blocks


def vm(S):
    sx, sy, sz, txy, tyz, tzx = (S[..., k] for k in range(6))
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3.0 * (txy ** 2 + tyz ** 2 + tzx ** 2))


def main(frd, npz, outp):
    B = read_frd(frd)
    F = np.load(npz)
    disp = [b for b in B if b["name"] == "DISP"]
    strs = [b for b in B if b["name"] == "STRESS"]
    out = {"frd": str(frd), "n_blocks": len(B), "blocks": [(b["name"], len(b["data"])) for b in B], "steps": {}}
    for k, st in enumerate(("TH", "OP")):
        res = {}
        for lab, blk, key, nc in (("U", disp[k], f"U_{st}", 3), ("S", strs[k], f"S_{st}", 6)):
            A = F[key].astype(np.float64)
            nodes = np.array(sorted(n for n in blk["data"] if n < len(A)))
            R = np.array([blk["data"][n][:nc] for n in nodes])
            S0 = A[nodes, :nc]
            d = R - S0
            res[lab] = {"n_nodes": int(len(nodes)), "max_abs_diff": float(np.abs(d).max()),
                        "max_abs_ref": float(np.abs(S0).max()),
                        "rel_norm_diff": float(np.linalg.norm(d) / max(np.linalg.norm(S0), 1e-30))}
            if lab == "S":
                v0, v1 = vm(S0), vm(R)
                res[lab]["vm_max_abs_diff_MPa"] = float(np.abs(v1 - v0).max())
                res[lab]["vm_max_rel_diff_over_vm_gt_1MPa"] = float(np.max(np.abs(v1 - v0)[v0 > 1.0] / v0[v0 > 1.0]))
                gov = {}
                for nd in (8314, 580, 25946, 27955):
                    if nd in blk["data"]:
                        gov[str(nd)] = {"vm_stored": float(vm(A[nd, :6])), "vm_resolved": float(vm(np.array(blk["data"][nd][:6])))}
                res[lab]["governing_nodes"] = gov
        out["steps"][st] = res
    # FA1S von Mises at the governing nodes from the re-solved TH/OP and the stored PM increment (FEA3D combination rule:
    # S = S_TH + sum c_i (S_i - S_TH))
    fa1s = {}
    for nd in (8314, 580, 25946, 27955):
        sth_r = np.array(strs[0]["data"][nd][:6])
        sop_r = np.array(strs[1]["data"][nd][:6])
        sth = F["S_TH"][nd, :6].astype(np.float64)
        spm = F["S_PM"][nd, :6].astype(np.float64)
        s_res = sth_r + 15.1038 * (sop_r - sth_r) + 7.0 * (spm - sth)
        s_sto = sth + 15.1038 * (F["S_OP"][nd, :6].astype(np.float64) - sth) + 7.0 * (spm - sth)
        fa1s[str(nd)] = {"vm_FA1S_resolved_MPa": float(vm(s_res)), "vm_FA1S_stored_MPa": float(vm(s_sto))}
    out["FA1S_governing_vm"] = fa1s
    Path(outp).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
