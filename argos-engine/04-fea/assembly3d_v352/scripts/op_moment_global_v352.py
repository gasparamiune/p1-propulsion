"""OP-step moment residue of the L1 global models and of the R3 hot-bound base, against the R3 pose runs (fea3d 2026-10-20, report
9B.3 / section 4; companion of op_moment_check_v352.py, same quadrature and statics).  Python only, no solve; the decks are streamed
read-only and nothing is written to the run tree.

Per (run, state) deck: the load step named in model.json ('OP'; for TB runs also 'BL') is rebuilt (*DLOAD C3D10 face pressures, 6-point
degree-4 rule on the quadratic face, outward normal away from the element's 4th corner; *CLOAD nodal forces): total force (checked
against pressure.json OP_net / BL_net), moment about the pivot, Q about the two gimbal axes, the statics rod tensions t = A^-1 (-Q)
(A from model.json rod_geom; the rods are the only moment path about the gimbal axes), the number of TC-09 faces at a fractional p/Pc
and the TC-09 lateral (engine-frame) pressure force.  The physical OP moment about the pivot is zero (closed cavity, axisymmetric exit
on the engine axis through the pivot), so Q is a discretisation residue.  Tags: DERIVED on SIM.  Not physical approval.
usage: FEA3D_CAD=v352 op_moment_global_v352.py -> results/v352/op_moment_global_v352.json"""
from __future__ import annotations
import sys, json, lzma, gzip
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import op_moment_check_v352 as OM      # noqa: E402  (FACES, SH quadrature, sha16)

RUNS, RES = OM.RUNS, OM.RES
CASES = [("lc1v351_c71", "B1_21.65", "v3.5.1 L1 global (LC1; CAD v3.5.1, asm v1.2)"),
         ("lc1v352g", "B1_21.65", "v3.5.2 L1 global (LC1 / LC2 GVLO)"),
         ("fa1v352n", "A1_22.2", "v3.5.2 L1 global (FA-1)"),
         ("tb352g", "TB", "v3.5.2 L1 global (TB70 / TBS GVLO)"),
         ("lc1v352hbg3", "B1_21.65", "v3.5.2 R3 hot-bound base (TC-09 level 1.8, as the R3 poses)")]


def parse(p, stepno):
    nodes, elems, eset, dload, cload = {}, {}, {}, [], []
    mode, cur, step = None, None, 0
    op = lzma.open if p.suffix == ".xz" else gzip.open
    with op(p, "rt") as fh:
        for line in fh:
            if line.startswith("**"):
                continue
            if line.startswith("*"):
                kw = line.strip().upper()
                if kw.startswith("*NODE") and not any(s in kw for s in ("PRINT", "FILE", "OUTPUT")):
                    mode = "node"
                elif kw.startswith("*ELEMENT") and "OUTPUT" not in kw:
                    mode = "elem"
                    cur = next((q.split("=", 1)[1].strip() for q in kw.split(",") if q.strip().startswith("ELSET")), None)
                elif kw.startswith("*STEP"):
                    step += 1
                    mode = None
                elif kw.startswith("*DLOAD") and step == stepno:
                    mode = "dload"
                elif kw.startswith("*CLOAD") and step == stepno:
                    mode = "cload"
                elif kw.startswith("*END STEP") and step == stepno:
                    break
                else:
                    mode = None
                continue
            if mode == "node":
                q = line.split(",")
                nodes[int(q[0])] = (float(q[1]), float(q[2]), float(q[3]))
            elif mode == "elem":
                q = [int(x) for x in line.replace(",", " ").split()]
                if len(q) == 11:
                    elems[q[0]] = q[1:]
                    eset[q[0]] = cur
            elif mode == "dload":
                q = [x.strip() for x in line.split(",")]
                if q[1].upper().startswith("P"):
                    dload.append((int(q[0]), int(q[1][1:]), float(q[2])))
            elif mode == "cload":
                q = line.split(",")
                cload.append((int(q[0]), int(q[1]), float(q[2])))
    return nodes, elems, eset, dload, cload


def one(run, state, label, stepname):
    model = json.loads((RUNS / run / "model.json").read_text())
    stepno = model["steps"].index(stepname) + 1
    p = next(RUNS / run / state / f"f1.inp.{e}" for e in ("xz", "gz") if (RUNS / run / state / f"f1.inp.{e}").exists())
    nodes, elems, eset, dload, cload = parse(p, stepno)
    Re = np.asarray(model["Rg"]["engine"])
    aX, aY = np.array([1.0, 0, 0]), np.asarray(model["Rg"]["ring"]) @ np.array([0, 1.0, 0])
    rg, rg_src = model.get("rod_geom"), run
    if not rg:      # lc1v351_c71's model.json predates the rod_geom record: the neutral rod geometry of the same CAD (pose_neutral_c71)
        rg_src = "pose_neutral_c71"
        rg = json.loads((RUNS / rg_src / "model.json").read_text())["rod_geom"]
    A = np.zeros((2, 2))
    for j, i in enumerate(sorted(rg, key=int)):
        g = rg[i]
        m = np.cross(np.asarray(g["lever_eye"]), -np.asarray(g["e_push_on_engine"]))
        A[:, j] = [m @ aX, m @ aY]
    Ft, Mt, F09, n09, nfrac = np.zeros(3), np.zeros(3), np.zeros(3), 0, 0
    for e, fc, pv in dload:
        con = elems[e]
        fn = OM.FACES[fc]
        X = np.array([nodes[con[i - 1]] for i in fn])
        opp = [i for i in (1, 2, 3, 4) if i not in fn[:3]][0]
        xo = np.array(nodes[con[opp - 1]])
        Av, MA = np.zeros(3), np.zeros(3)
        for N, dxi, det, w in OM.SH:
            nA = np.cross(dxi @ X, det @ X)
            Av += w * nA
            MA += w * np.cross(N @ X, nA)
        sg = 1.0 if Av @ (X[:3].mean(axis=0) - xo) > 0 else -1.0
        F, M = -pv * sg * Av, -pv * sg * MA
        Ft += F
        Mt += M
        if eset[e] == "B_TC09":
            F09 += F
            n09 += 1
            nfrac += pv < 0.9999
    CF = {}
    for n, dof, v in cload:
        CF.setdefault(n, np.zeros(3))[dof - 1] += v
    for n, fv in CF.items():
        Ft += fv
        Mt += np.cross(np.array(nodes[n]), fv)
    pj = json.loads((RUNS / run / "pressure.json").read_text())
    Q = np.array([Mt @ aX, Mt @ aY])
    return {"run": run, "state": state, "label": label, "step": stepname, "deck": str(p.relative_to(RUNS.parent)), "deck_sha16": OM.sha16(p),
            "cad": model.get("cad"), "version": model.get("version"), "TC09_nodes": model["bodies"]["TC-09"]["n"],
            "n_pressure_faces": len(dload), "total_F_N_per_MPa": Ft.round(4).tolist(),
            "pressure_json_net_N_per_MPa": [round(x, 4) for x in pj.get(f"{stepname}_net_N_per_MPa", [float('nan')] * 3)],
            "total_M_about_pivot_Nmm_per_MPa": Mt.round(2).tolist(), "Q_gimbal_axes_Nmm_per_MPa": Q.round(2).tolist(),
            "Q_magnitude_Nm_per_MPa": round(float(np.hypot(*Q)) / 1000.0, 3),
            "rods_statics_N_per_MPa": np.linalg.solve(A, -Q).round(3).tolist(), "rod_geom_from": rg_src,
            "TC09_faces": n09, "TC09_fractional_faces": int(nfrac), "TC09_lateral_F_engine_N_per_MPa": (Re.T @ F09)[:2].round(3).tolist()}


def main():
    out = {"doc": __doc__.split("usage:")[0].strip(), "rows": []}
    for run, state, label in CASES:
        steps = ["OP"] + (["BL"] if "BL" in json.loads((RUNS / run / "model.json").read_text())["steps"] else [])
        for st in steps:
            r = one(run, state, label, st)
            out["rows"].append(r)
            print(f"{run:12s} {state:9s} {st}: F {r['total_F_N_per_MPa']} (json {r['pressure_json_net_N_per_MPa']}) Q {r['Q_gimbal_axes_Nmm_per_MPa']} "
                  f"|Q| {r['Q_magnitude_Nm_per_MPa']} N m/MPa rods {r['rods_statics_N_per_MPa']} TC-09 faces {r['TC09_faces']} fractional "
                  f"{r['TC09_fractional_faces']} lateral {r['TC09_lateral_F_engine_N_per_MPa']}", flush=True)
    pc = json.loads((RES / "v352" / "op_moment_check_v352.json").read_text())
    out["R3_pose_reference"] = [{k: d[k] for k in ("run", "deck_sha16", "Q_gimbal_axes_Nmm_per_MPa", "rods_OP_statics_N_per_MPa")} for d in pc["decks"]]
    out["files_sha16"] = {"v352/op_moment_check_v352.json": OM.sha16(RES / "v352" / "op_moment_check_v352.json")}
    (RES / "v352" / "op_moment_global_v352.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
