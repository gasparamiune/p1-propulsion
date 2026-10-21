"""FEA3D LC3 HOT BOUND: thermal + manifold stresses added to the cold LC3 stop-pose envelopes by sub-additivity (fea3d successor 2026-10-15).

  von Mises is a semi-norm of the stress tensor:  vm(A + B) <= vm(A) + vm(B);  Weyl:  s1(A + B) <= s1(A) + s1(B),  s3(A + B) >= s3(A) + s3(B).
  A = thermo-pressure field of the L1 neutral run (TH + OP x Pc_max + PM x 7 MPa, NO LC1 inertia) at each S-AX thermal state
      B1_21.65 / B1_19 / B1_2 / B1_1  (so hot LC3 = A + D exactly, up to the pose-mesh mapping);
  D = LC3 increment over the cold OP field (lateral, axial, angular, bumper / runaway), envelope over the 64 sub-cases and the 8 stop poses
      (results/lc3_env_pose_stopXXX.npz from post_lc3.py).
  Engine-group bodies meshed identically in both runs (TC-01, GM-01, GM-02): node-wise  vm <= vm_LC1(n) + vmD(n).
  Engine pressure parts meshed coarser in the pose runs (level 2): vm <= vm_LC1(n) + max_part vmD  (maximum over the part's REGULAR
      nodes of the pose model: conservative away from idealisation singularities, which are excluded in both runs).
  Ring / fixed / horn bodies (thrust direction changes with the pose, so LC1 is not a base):  vm <= vm_LC3cold(n) + vm(TH + 7 x PM incr.)(n)
      with the LC1-run thermal + manifold field at the state (identical L1 meshes).
  Brittle parts: s1 <= s1_LC1(n) + max_part s1D ;  s3 >= s3_LC1(n) + min_part s3D ; char zone (T > T_char): primary s3 only.
  Allowables at the node temperature of the state; SF 1.5 / 2.0 (LC3 nominal operating, 188 (9)); brittle SF 2.0.
The result is a LOWER BOUND on the hot LC3 margin (exact sum not available: the pose runs carry no TH step).  Units mm, N, MPa, K.
usage: lc3_bound.py [lc1_run=lc1v351_design_rigid] [poses=pose_stop000,...]
"""
from __future__ import annotations
import sys, json, math, time
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF        # noqa: E402
import asm3d as A3          # noqa: E402

RES = PF.RES
SFY, SFU = 1.5, 2.0
SAME_MESH_ENGINE = ["TC-01", "GM-01", "GM-02"]


def main(lc1="lc1v351_design_rigid", poses=None):
    t0 = time.time()
    poses = poses or [f"pose_stop{d:03d}" for d in range(0, 360, 45)]
    M, meta = PF.load_model(lc1)
    names = list(M.bodies)
    pm = {p: json.loads((PF.RUNS / p / "model.json").read_text()) for p in poses}
    envs = {p: dict(np.load(RES / f"lc3_env_{p}.npz")) for p in poses}
    # per body: node-local envelopes over the poses (same-mesh bodies) and part maxima (all bodies)
    loc, pmax = {}, {}
    for nm in names:
        n_l1 = len(M.bodies[nm].X0)
        acc = {"vm": None, "vmD": None}
        mx = {"vmD": -np.inf, "s1D": -np.inf, "s3D": np.inf}
        for p in poses:
            bm = pm[p]["bodies"][nm]
            sl = slice(bm["noff"], bm["noff"] + bm["n"])
            e = envs[p]
            rg = e["reg"][sl] if "reg" in e else np.ones(bm["n"], bool)     # part maxima over the REGULAR nodes of the pose model
            mx["vmD"] = max(mx["vmD"], float(np.max(np.where(rg, e["vmD"][sl], -np.inf))))
            if np.isfinite(e["s1D"][sl]).any():
                mx["s1D"] = max(mx["s1D"], float(np.max(np.where(rg, e["s1D"][sl], -np.inf))))
                mx["s3D"] = min(mx["s3D"], float(np.min(np.where(rg, e["s3D"][sl], np.inf))))
            if bm["n"] == n_l1:
                for k in ("vm", "vmD"):
                    v = e[k][sl].astype(np.float64)
                    acc[k] = v if acc[k] is None else np.maximum(acc[k], v)
        loc[nm] = acc
        pmax[nm] = mx
    out = {"lc1_run": lc1, "poses": poses, "date": "2026-10-15", "method": __doc__.split("usage:")[0].strip(), "states": {}, "part_max_increment": pmax}
    for state in ("B1_21.65", "B1_19", "B1_2", "B1_1"):
        F = PF.load_fields(lc1, state)
        _, body, T, X = PF.node_arrays(M, lc1, state)
        reg, _, _ = PF.singular_sets(M, X, ex_r=1.0)
        # A = thermo-pressure field of LC1 WITHOUT the LC1 inertia (hot LC3 = TH + OP Pc_max + 7 PM + D exactly; D carries all LC3 inertia)
        Ss = [PF.combine(F, "S", {"OP": PF.PC_MAX, "PM": PF.P_MAN})]
        S_th = F["S_TH"].astype(np.float64)
        S_pm = 7.0 * (F["S_PM"].astype(np.float64) - S_th)
        rows = []
        for nm in names:
            b = M.bodies[nm]
            nodes = b.noff + np.arange(len(b.X0))
            mat = b.mat
            Mt = A3.engmat.MATERIALS[mat]
            a1, a2 = PF.allowables(mat, T[nodes])
            Tc = T[nodes] - 273.15
            brittle = mat in PF.BRITTLE
            msk = reg[nodes]
            if brittle:
                s1 = np.max([PF.principal(S[nodes])[0] for S, _ in Ss], axis=0)
                s3 = np.min([PF.principal(S[nodes])[1] for S, _ in Ss], axis=0)
                s3m = np.min([PF.principal(Sm[nodes])[1] for _, Sm in Ss], axis=0)
                s1b = s1 + max(pmax[nm]["s1D"], 0.0)
                s3b, s3mb = s3 + min(pmax[nm]["s3D"], 0.0), s3m + min(pmax[nm]["s3D"], 0.0)
                T_char = Mt["T_char_C"]["v"] if "T_char_C" in Mt else None
                char = (Tc > T_char) if T_char is not None else np.zeros(len(nodes), bool)
                big = np.full(len(nodes), np.inf)
                ms_t = np.where(s1b > 0, a1 / (SFU * np.maximum(s1b, 1e-9)) - 1.0, np.inf) if a1 is not None else big
                ms_c = np.where(s3b < 0, a2 / (SFU * np.maximum(-s3b, 1e-9)) - 1.0, np.inf) if a2 is not None else big
                ms = np.minimum(ms_t, ms_c)
                ms_ch = np.where(s3mb < 0, a2 / (SFU * np.maximum(-s3mb, 1e-9)) - 1.0, np.inf) if a2 is not None else big
                ms = np.where(char, ms_ch, ms)
                msu = ms
                how = "LC1 principal + part-max LC3 increment (Weyl)"
            else:
                if b.grp == "engine":
                    v1 = np.max([PF.vm(S[nodes]) for S, _ in Ss], axis=0)
                    if nm in SAME_MESH_ENGINE and loc[nm]["vmD"] is not None:
                        vb = v1 + loc[nm]["vmD"]
                        how = "LC1 vm + node-wise LC3 increment (same mesh)"
                    else:
                        vb = v1 + pmax[nm]["vmD"]
                        how = "LC1 vm + part-max LC3 increment (pose mesh coarser)"
                else:
                    if loc[nm]["vm"] is None:
                        raise RuntimeError(f"{nm}: pose mesh differs from L1")
                    vb = loc[nm]["vm"] + PF.vm(S_th[nodes] + S_pm[nodes])
                    how = "LC3 cold vm (8 poses) + LC1-run thermal + manifold vm (node-wise)"
                ms = a1 / (SFY * np.maximum(vb, 1e-9)) - 1.0
                msu = a2 / (SFU * np.maximum(vb, 1e-9)) - 1.0
            for tag, m_ in (("regular", msk), ("all", np.ones(len(nodes), bool))):
                if not m_.any():
                    continue
                i = int(np.argmin(np.where(m_, ms, np.inf)))
                x = X[nodes[i]]
                rows.append({"part": nm, "set": tag, "state": state, "MS_bound": float(ms[i]),
                             "MS_ult_bound": (float(np.min(np.where(m_, msu, np.inf))) if not brittle else None), "method": how,
                             "T_C": float(Tc[i]), "r_theta_z": [round(math.hypot(x[0], x[1]), 3), round(math.degrees(math.atan2(x[1], x[0])), 1), round(float(x[2]), 3)]})
        out["states"][state] = rows
        print(f"[lc3_bound {state}] {time.time() - t0:.1f} s", flush=True)
    summ = {}
    for st, rows in out["states"].items():
        for r in rows:
            if r["set"] != "regular":
                continue
            k = r["part"]
            if k not in summ or r["MS_bound"] < summ[k]["MS_bound"]:
                summ[k] = dict(r)
    out["summary_min_over_states_regular"] = summ
    (RES / "f1_lc3_hot_bound.json").write_text(json.dumps(out, indent=1, default=float))
    for k, r in sorted(summ.items(), key=lambda kv: kv[1]["MS_bound"]):
        print(f"  {k:7s} {r['MS_bound']:+.3f} / {(r['MS_ult_bound'] if r['MS_ult_bound'] is not None else float('nan')):+.3f}  {r['state']}  {r['method']}")


if __name__ == "__main__":
    o = dict(x.split("=", 1) for x in sys.argv[1:])
    main(o.get("lc1_run", "lc1v351_design_rigid"), o["poses"].split(",") if "poses" in o else None)
