"""Per-unit-step rod tensions at the 9 range-cone poses, recovered from the S-3D posts (fea3d 2026-10-20, report section 9B.3).
Python only, no solve; the posts are read, nothing else.

For each cone pose and each model (v3.5.1 c71 posts: CAD v3.5.1, asm v1.2; v3.5.2 R3 posts: CAD v3.5.2, asm v1.3, rev-3 levers at R3),
the rod tensions of the stored GS sub-cases (64 per pose; GS is the only case whose post stores per-sub-case rod tensions) are fitted,
by least squares, as a linear combination of the unit steps OP (N/MPa), GX / GY / GZ (N/g) and EAX / EAY (N per rad/s2) with the stored
sub-case coefficients (rank and the largest residual are recorded; rank 6 = unique).  Check: the recovered unit rods, recombined with the
stored coefficients of TD0 / TDP / LC6 / LC2F, reproduce the stored per-rod maxima rod_max_abs_N of those cases (largest difference
recorded).  Tags: DERIVED on SIM.  Not physical approval.
usage: rodstep_cones_v352.py -> results/v352/rodstep_cones_v352.json"""
import json, hashlib
from pathlib import Path
import numpy as np

RES = Path("/home/claude/work/fea3d/results")
CONES = ["neutral", "alpha+", "alpha-", "beta+", "beta-", "combined045", "combined135", "combined225", "combined315"]
STEPS = ["OP", "GX", "GY", "GZ", "EAX", "EAY"]
MODELS = {"v351_c71": "s3d_pose_{}_c71.json", "v352_R3": "s3d_pose_{}_v352r3R3.json"}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def unit(fp):
    d = json.loads(fp.read_text())
    C, T = [], {"ROD_1": [], "ROD_2": []}
    for c in ("GS", "TD0", "TDP", "LC6", "LC2F"):
        cc = d["cases"].get(c) or {}
        for co, info in zip(cc.get("subcase_coefs") or [], cc.get("subcases") or []):
            C.append([float(co.get(st, 0.0)) for st in STEPS])
            for r in T:
                T[r].append(info["rod_tension_N"][r])
    C = np.array(C)
    sol, res = {}, {}
    for r, t in T.items():
        t = np.array(t)
        x, *_ = np.linalg.lstsq(C, t, rcond=None)
        sol[r] = dict(zip(STEPS, [round(float(v), 4) for v in x]))
        res[r] = float(np.max(np.abs(C @ x - t)))
    chk = 0.0
    for c in ("TD0", "TDP", "LC6", "LC2F"):
        cc = d["cases"].get(c) or {}
        for j, r in enumerate(("ROD_1", "ROD_2")):
            t = [sum(float(co.get(st, 0.0)) * sol[r][st] for st in STEPS) for co in cc.get("subcase_coefs") or []]
            if t and r in (cc.get("rod_max_abs_N") or {}):
                chk = max(chk, abs(max(abs(x) for x in t) - cc["rod_max_abs_N"][r]))
    return {"unit_rod_N": sol, "fit_resid_max_N": res, "rank": int(np.linalg.matrix_rank(C)), "n_subcases": len(C),
            "check_other_cases_rod_max_abs_diff_N": chk,
            "version": d.get("version"), "OP_net_axial_N_per_MPa": d.get("OP_net_axial_N_per_MPa")}


def main():
    out = {"doc": __doc__.split("usage:")[0].strip(), "files_sha16": {}, "poses": {}, "ranges": {}}
    for p in CONES:
        out["poses"][p] = {}
        for tag, pat in MODELS.items():
            fp = RES / pat.format(p)
            out["files_sha16"][fp.name] = sha16(fp)
            out["poses"][p][tag] = unit(fp)
    for tag in MODELS:
        out["ranges"][tag] = {}
        for st in STEPS:
            out["ranges"][tag][st] = {r: [min(out["poses"][p][tag]["unit_rod_N"][r][st] for p in CONES),
                                          max(out["poses"][p][tag]["unit_rod_N"][r][st] for p in CONES)] for r in ("ROD_1", "ROD_2")}
        out["ranges"][tag]["max_fit_resid_N"] = max(max(out["poses"][p][tag]["fit_resid_max_N"].values()) for p in CONES)
        out["ranges"][tag]["ranks"] = sorted({out["poses"][p][tag]["rank"] for p in CONES})
        out["ranges"][tag]["max_check_other_cases_N"] = max(out["poses"][p][tag]["check_other_cases_rod_max_abs_diff_N"] for p in CONES)
    (RES / "v352" / "rodstep_cones_v352.json").write_text(json.dumps(out, indent=1))
    for tag in MODELS:
        g = out["ranges"][tag]
        print(tag, "ranks", g["ranks"], "max resid %.1e N" % g["max_fit_resid_N"], "check TD0/TDP/LC6/LC2F rod maxima %.1e N" % g["max_check_other_cases_N"])
        for st in STEPS:
            print("   %-4s ROD_1 %+7.2f .. %+7.2f   ROD_2 %+7.2f .. %+7.2f" % (st, *g[st]["ROD_1"], *g[st]["ROD_2"]))


if __name__ == "__main__":
    main()
