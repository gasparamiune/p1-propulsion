"""FEA3D mesh-convergence study at the governing locations (RM1-05 / brief F1; fea3d successor 2026-10-15).

Levels: L1 (global level 1.0; runs lc1v351_design_rigid for B1_*, fa1_v351 for A1_22.2), R2 = conv_r2, R3 = conv_r3 (same model, local
gmsh Ball refinement around each point; balls in run_f1 'refine').  Same thermal map, loads and connectors at every level.
Combinations (no lateral sub-cases; they change these values by < 1 %, see the L1 post):
  B1_*  : LC1-core  = TH + OP x 2.501 MPa + PM x 7 MPa + GZ x 4.04 g
  A1_22.2: FA1S-core = TH + OP x 15.104 MPa (151.04 bar abs) + PM x 7 MPa
Metrics per point (sphere R_M = 3 mm around the L1 governing node, nodes of the governing part only):
  q_max_reg : maximum over REGULAR nodes (outside 1.0 mm of every idealisation singularity: tie patch edges, RBE3 / rigid patches,
              re-entrant CAD edges, bad tets) of the governing quantity (von Mises for metals, s1 for the graphite insert)
  q_max_all : same over all nodes (singular points included: grows without bound at a true singularity)
  MS_min_reg: the part criterion (as post_f1) minimum over the regular nodes in the sphere
  h_loc     : mean tet edge length of the elements within 1 mm of the point (mm)
Richardson / GCI (Celik et al. 2008, J. Fluids Eng. 130 078001, procedure as recalled) on q_max_reg with the measured h ratios.
usage: post_conv.py
"""
from __future__ import annotations
import sys, json, math, time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF        # noqa: E402
import asm3d as A3          # noqa: E402

RES = PF.RES
R_M = 3.0
POINTS = {
    "NZ-01 throat (B1_1)": ("NZ-01", "B1_1", (3.231, 5.618, -223.344), "-s3"),       # compression governs the graphite throat (s1 < 0 there)
    "TC-03 flange corner (B1_1)": ("TC-03", "B1_1", (-9.8, 0.0, 105.513), "vm"),
    "TC-02 TB1 tie end (B1_19)": ("TC-02", "B1_19", (-5.856, 0.0, 107.513), "vm"),
    "TC-01 J-FWD hole / bore (FA1S, A1_22.2)": ("TC-01", "A1_22.2", (13.952, 24.965, 125.492), "vm"),
}
LEVELS = [("L1", {"B1": "lc1v351_design_rigid", "A1": "fa1_v351"}), ("R2", {"B1": "conv_r2", "A1": "conv_r2"}),
          ("R3", {"B1": "conv_r3", "A1": "conv_r3"})]


def core(state):
    if state.startswith("A1"):
        return {"OP": 2.0 * 75.519 / 10.0, "PM": 7.0}, 1.0, 1.0
    return {"OP": PF.PC_MAX, "PM": PF.P_MAN, "GZ": PF.G_AX_FLIGHT}, 1.5, 2.0


def gci(h, q):
    """h, q ordered fine -> coarse (3 levels).  Returns observed order p, extrapolated q, GCI_fine (Fs 1.25)."""
    h1, h2, h3 = h
    f1, f2, f3 = q
    r21, r32 = h2 / h1, h3 / h2
    e21, e32 = f2 - f1, f3 - f2
    if e21 == 0 or e32 == 0 or r21 <= 1.0 or r32 <= 1.0:
        return {"p": None, "q_ext": None, "GCI_fine": None, "note": "degenerate (zero change or ratio <= 1)"}
    if abs(e32 / e21) < 1.0:
        # RM2-03 (REV-MECH-2, adopted CHANGELOG 234 (3)): the fine-level change is larger than the coarse-level change -> not converging
        # (not in the asymptotic range): no observed order and no GCI.  (The fixed-point iteration below can return a spurious p.)
        return {"p": None, "q_ext": None, "GCI_fine": None, "oscillatory": bool(np.sign(e32 / e21) < 0), "r21": r21, "r32": r32,
                "e21": e21, "e32": e32, "ratio_e32_e21": e32 / e21,
                "note": "|e32/e21| < 1: the change grows with refinement (not in the asymptotic range): no order, no GCI (RM2-03)"}
    s = np.sign(e32 / e21)
    p = 1.0
    ok = False
    for _ in range(200):
        try:
            qq = math.log((r21 ** p - s) / (r32 ** p - s)) if (r21 ** p - s) > 0 and (r32 ** p - s) > 0 else 0.0
            pn = abs(math.log(abs(e32 / e21)) + qq) / math.log(r21)
        except (OverflowError, ValueError, ZeroDivisionError):
            break
        if abs(pn - p) < 1e-8:
            ok = True
            p = pn
            break
        p = pn
        if p > 12.0:
            break
    if not ok:
        return {"p": None, "q_ext": None, "GCI_fine": None, "oscillatory": bool(s < 0), "r21": r21, "r32": r32,
                "note": "fixed-point iteration for the observed order did not converge (non-monotone or not asymptotic): no GCI"}
    ext = (r21 ** p * f1 - f2) / (r21 ** p - 1.0)
    ea = abs((f1 - f2) / f1)
    g = 1.25 * ea / (r21 ** p - 1.0)
    osc = bool(s < 0)
    return {"p": p, "q_ext": ext, "GCI_fine": g, "oscillatory": osc, "r21": r21, "r32": r32}


def main():
    t0 = time.time()
    out = {"date": "2026-10-15", "revised": "2026-10-20 RM2-03: gci() returns no order / GCI when |e32/e21| < 1", "R_M_mm": R_M, "method": __doc__.split("usage:")[0].strip(), "points": {}}
    cache = {}
    for lev, runs in LEVELS:
        for key, (part, state, P, qty) in POINTS.items():
            run = runs["A1" if state.startswith("A1") else "B1"]
            if not (PF.RUNS / run / state / "fields.npz").exists():
                print(f"[conv] missing {run}/{state}", flush=True)
                continue
            if run not in cache:
                cache.clear()
                M, meta = PF.load_model(run)
                cache[run] = M
            M = cache[run]
            names, body, T, X = PF.node_arrays(M, run, state)
            reg, srep, sing = PF.singular_sets(M, X, ex_r=1.0)
            F = PF.load_fields(run, state)
            co, sfy, sfu = core(state)
            S, Sm = PF.combine(F, "S", co)
            b = M.bodies[part]
            g = b.noff + np.arange(len(b.X0))
            d = np.linalg.norm(X[g] - np.asarray(P), axis=1)
            sel = d <= R_M
            gi = g[sel]
            a1, a2 = PF.allowables(b.mat, T[gi])
            if qty in ("s1", "-s3"):
                s1, s3 = PF.principal(S[gi])
                q = s1 if qty == "s1" else -s3
                ms = np.minimum(np.where(s1 > 0, a1 / (2.0 * np.maximum(s1, 1e-9)) - 1, np.inf),
                                np.where(s3 < 0, a2 / (2.0 * np.maximum(-s3, 1e-9)) - 1, np.inf))
            else:
                q = PF.vm(S[gi])
                ms = a1 / (sfy * np.maximum(q, 1e-9)) - 1.0
            msu = (a2 / (sfu * np.maximum(q, 1e-9)) - 1.0) if (qty == "vm" and a2 is not None) else None
            rg = reg[gi]
            # local element size
            T4 = b.T10[:, :4]
            E = X[b.noff + T4]
            near = np.linalg.norm(X[b.noff + b.T10] - np.asarray(P), axis=2).min(1) <= 1.0     # any of the 10 nodes within 1 mm
            ed = np.concatenate([np.linalg.norm(E[:, i] - E[:, j], axis=1)[near] for i, j in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))])
            kk = int(np.argmax(np.where(rg, q, -np.inf))) if rg.any() else None
            row = {"level": lev, "run": run, "state": state, "n_nodes_model": int(M.n_mesh), "n_nodes_part": int(len(g)),
                   "n_nodes_sphere": int(sel.sum()), "n_regular_sphere": int(rg.sum()), "h_loc_mm": float(ed.mean()) if len(ed) else None,
                   "q": qty, "q_max_reg_MPa": (float(q[kk]) if kk is not None else None), "q_max_all_MPa": float(q.max()),
                   "MS_min_reg": (float(np.min(np.where(rg, ms, np.inf))) if rg.any() else None), "MS_min_all": float(ms.min()),
                   "MS_u_min_reg": (float(np.min(np.where(rg, msu, np.inf))) if (msu is not None and rg.any()) else None),
                   "xyz_qmax_reg": ([round(float(c), 3) for c in X[gi[kk]]] if kk is not None else None),
                   "T_C_at_qmax": (float(T[gi[kk]] - 273.15) if kk is not None else None), "combination": co}
            if rg.any():
                km = int(np.argmin(np.where(rg, ms, np.inf)))
                row.update({"MSgov_xyz": [round(float(c), 3) for c in X[gi[km]]], "MSgov_q_MPa": float(q[km]), "MSgov_T_C": float(T[gi[km]] - 273.15),
                            "MSgov_dist_to_point_mm": float(d[sel][km])})
            out["points"].setdefault(key, {"part": part, "state": state, "point_mm": P, "levels": []})["levels"].append(row)
            print(f"[conv {lev} {key}] MSgov q {row.get('MSgov_q_MPa')} T {row.get('MSgov_T_C')} at {row.get('MSgov_xyz')} d {row.get('MSgov_dist_to_point_mm')}", flush=True)
            print(f"[conv {lev} {key}] h {row['h_loc_mm']} q_reg {row['q_max_reg_MPa']} q_all {row['q_max_all_MPa']:.1f} MS {row['MS_min_reg']} ({time.time() - t0:.0f} s)", flush=True)
    for key, d in out["points"].items():
        L = {r["level"]: r for r in d["levels"]}
        if all(k in L for k in ("L1", "R2", "R3")) and all(L[k]["q_max_reg_MPa"] for k in ("L1", "R2", "R3")):
            h = [L["R3"]["h_loc_mm"], L["R2"]["h_loc_mm"], L["L1"]["h_loc_mm"]]
            d["gci_q_max_reg"] = gci(h, [L["R3"]["q_max_reg_MPa"], L["R2"]["q_max_reg_MPa"], L["L1"]["q_max_reg_MPa"]])
            d["change_R2_to_R3_pct"] = 100.0 * (L["R3"]["q_max_reg_MPa"] / L["R2"]["q_max_reg_MPa"] - 1.0)
            d["change_L1_to_R2_pct"] = 100.0 * (L["R2"]["q_max_reg_MPa"] / L["L1"]["q_max_reg_MPa"] - 1.0)
            d["q_all_growth_L1_to_R3"] = L["R3"]["q_max_all_MPa"] / L["L1"]["q_max_all_MPa"]
    op = Path(sys.argv[1]) if len(sys.argv) > 1 else RES / "f1_convergence.json"
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", op)


if __name__ == "__main__":
    main()
