"""F2 / LC3 rod-force change v3.5.1 -> v3.5.2: the cause, from the solver decks and the posts (fea3d 2026-10-20, written after the
22:10:56Z date -u reading; report section 9B).  Python only, no solve; the decks are streamed read-only (xz / gz), nothing is written
to the run tree.

Statics: the two rod springs are the only moment path about the two gimbal axes (post_lc3 note), so a unit step's rod tensions follow
from the step's applied moment about those axes alone: t = A^-1 (-Q), A = the rod moment matrix from rod_geom (as post_lc3).  An OP
(chamber pressure) step on a closed cavity with an axisymmetric exit has its resultant on the engine axis, i.e. no moment about the pivot;
any moment the model carries is a discretisation residue of the pressure faces (the uniform 'residual correction' traction of
pressure.json removes the lateral FORCE imbalance, not the moment).
This script records, per deck (OP step: *DLOAD element-face pressures on C3D10 faces, 6-point degree-4 rule on the quadratic face,
outward normal away from the element's 4th corner; *CLOAD nodal forces):
  total force / moment (checked against pressure.json OP_net and the FBD connector moment), per-part contributions, the lateral (engine
  frame) pressure force per part, the statics rod tensions, and the same with the two TC-09 aft-boundary faces at p = 1.0 (the uniform
  residual correction re-balanced at the wetted-area centroid) = 'TC-09 boundary removed';
per LC3 post (stop045: c71, v352L1 = asm v1.2 on CAD v3.5.2, v352L1x = asm v1.3 tiex, v352r3R3): the unit-step rod tensions recovered
  by least squares from the 32 hold sub-cases (rank 5, residual ~1e-13);
per FBD file: the engine CG implied by the connector moments (inertial steps).
Tags: SIM inputs, DERIVED (statics, quadrature).  Not physical approval.
usage: FEA3D_CAD=v352 op_moment_check_v352.py -> results/v352/op_moment_check_v352.json"""
from __future__ import annotations
import sys, json, lzma, gzip, math, hashlib
from pathlib import Path
import numpy as np

RUNS = Path("/home/claude/work/fea3d/runs")
RES = Path("/home/claude/work/fea3d/results")
DECKS = ["pose_alpha+_c71", "pose_alpha+_v352r3R3", "pose_stop045_v352r3R3"]
LC3 = ["f1_post_lc3_pose_stop045_c71.json", "f1_post_lc3_pose_stop045_v352L1.json", "f1_post_lc3_pose_stop045_v352L1x.json",
       "f1_post_lc3_pose_stop045_v352r3R3.json"]
FBD = ["fbd_pose_stop045_c71_B1_21.65.json", "v352/fbd_pose_stop045_v352L1_B1_21.65.json", "v352/fbd_pose_stop045_v352L1x_B1_21.65.json",
       "fbd_pose_alpha+_v352r3R3_B1_21.65.json", "fbd_pose_neutral_v352r3R3_B1_21.65.json"]
FACES = {1: (1, 2, 3, 5, 6, 7), 2: (1, 4, 2, 8, 9, 5), 3: (2, 4, 3, 9, 10, 6), 4: (3, 4, 1, 10, 8, 7)}
_a, _b, _wa, _wb = 0.445948490915965, 0.091576213509771, 0.223381589678011, 0.109951743655322
QP = [(_a, _a, _wa), (1 - 2 * _a, _a, _wa), (_a, 1 - 2 * _a, _wa), (_b, _b, _wb), (1 - 2 * _b, _b, _wb), (_b, 1 - 2 * _b, _wb)]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def shape(xi, et):
    z = 1 - xi - et
    N = np.array([z * (2 * z - 1), xi * (2 * xi - 1), et * (2 * et - 1), 4 * z * xi, 4 * xi * et, 4 * et * z])
    dxi = np.array([-(4 * z - 1), 4 * xi - 1, 0.0, 4 * (z - xi), 4 * et, -4 * et])
    det = np.array([-(4 * z - 1), 0.0, 4 * et - 1, -4 * xi, 4 * xi, 4 * (z - et)])
    return N, dxi, det


SH = [shape(x, e) + (0.5 * w,) for x, e, w in QP]      # Dunavant weights are area fractions: x 1/2 on the unit reference triangle


def deck_path(run):
    for ext in ("xz", "gz"):
        p = RUNS / run / "B1_21.65" / f"f1.inp.{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(run)


def parse(run):
    p = deck_path(run)
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
                elif kw.startswith("*DLOAD") and step == 1:
                    mode = "dload"
                elif kw.startswith("*CLOAD") and step == 1:
                    mode = "cload"
                elif kw.startswith("*END STEP") and step == 1:
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
    return p, nodes, elems, eset, dload, cload


def deck(run):
    p, nodes, elems, eset, dload, cload = parse(run)
    model = json.loads((RUNS / run / "model.json").read_text())
    Re = np.asarray(model["Rg"]["engine"])
    aX, aY = np.array([1.0, 0, 0]), np.asarray(model["Rg"]["ring"]) @ np.array([0, 1.0, 0])
    rg = model["rod_geom"]
    A = np.zeros((2, 2))
    for j, i in enumerate(sorted(rg, key=int)):
        xL, e = np.asarray(rg[i]["lever_eye"]), np.asarray(rg[i]["e_push_on_engine"])
        m = np.cross(xL, -e)
        A[:, j] = [m @ aX, m @ aY]
    rng = sorted((b["noff"] + 1, b["noff"] + b["n"], nm) for nm, b in model["bodies"].items())
    part = lambda n: next((nm for a, b, nm in rng if a <= n <= b), "extra")
    per = {}
    Ftot, Mtot, Aw, Cw, Fdef, Mdef, frac09 = np.zeros(3), np.zeros(3), 0.0, np.zeros(3), np.zeros(3), np.zeros(3), []
    for e, fc, pv in dload:
        con = elems[e]
        fn = FACES[fc]
        X = np.array([nodes[con[i - 1]] for i in fn])
        opp = [i for i in (1, 2, 3, 4) if i not in fn[:3]][0]
        xo = np.array(nodes[con[opp - 1]])
        Av, MA = np.zeros(3), np.zeros(3)
        for N, dxi, det, w in SH:
            nA = np.cross(dxi @ X, det @ X)
            Av += w * nA
            MA += w * np.cross(N @ X, nA)
        cen = X[:3].mean(axis=0)
        sg = 1.0 if Av @ (cen - xo) > 0 else -1.0
        F, M = -pv * sg * Av, -pv * sg * MA
        r = per.setdefault(f"pressure {eset[e]}", {"F": np.zeros(3), "M": np.zeros(3), "n": 0})
        r["F"] += F
        r["M"] += M
        r["n"] += 1
        Ftot += F
        Mtot += M
        a = float(np.linalg.norm(Av))
        Aw += a
        Cw += a * cen
        if eset[e] == "B_TC09" and pv < 0.9999:
            Fdef += -(1.0 - pv) * sg * Av
            Mdef += -(1.0 - pv) * sg * MA
            frac09.append({"element": e, "face": fc, "p_over_Pc": pv, "centroid_engine_mm": (Re.T @ cen).round(2).tolist(),
                           "area_mm2": round(a, 3), "normal_engine": (Re.T @ (sg * Av / a)).round(3).tolist()})
    CF = {}
    for n, dof, v in cload:
        CF.setdefault(n, np.zeros(3))[dof - 1] += v
    for n, fv in CF.items():
        M = np.cross(np.array(nodes[n]), fv)
        r = per.setdefault(f"nodal {part(n)}", {"F": np.zeros(3), "M": np.zeros(3), "n": 0})
        r["F"] += fv
        r["M"] += M
        r["n"] += 1
        Ftot += fv
        Mtot += M
    cw = Cw / Aw
    Fd_e = Re.T @ Fdef
    dFc = Re @ np.array([-Fd_e[0], -Fd_e[1], 0.0])
    Mclean = Mtot + Mdef + np.cross(cw, dFc)
    Q, Qc = np.array([Mtot @ aX, Mtot @ aY]), np.array([Mclean @ aX, Mclean @ aY])
    pj = json.loads((RUNS / run / "pressure.json").read_text())
    return {"run": run, "deck": str(p.relative_to(RUNS.parent)), "deck_sha16": sha16(p), "cad": model.get("cad"), "version": model.get("version"),
            "tb1": model["variant"].get("tb1"), "tiex": model["variant"].get("tiex"), "n_pressure_faces": len(dload), "n_nodal_load_nodes": len(CF),
            "total_F_N_per_MPa": Ftot.round(4).tolist(), "pressure_json_OP_net_N_per_MPa": [round(x, 4) for x in pj["OP_net_N_per_MPa"]],
            "total_M_about_pivot_Nmm_per_MPa": Mtot.round(2).tolist(), "Q_gimbal_axes_Nmm_per_MPa": Q.round(2).tolist(),
            "rod_moment_matrix_Nmm_per_N": A.round(3).tolist(), "rods_OP_statics_N_per_MPa": np.linalg.solve(A, -Q).round(3).tolist(),
            "per_part": {k: {"F": v["F"].round(4).tolist(), "F_lateral_engine_frame": (Re.T @ v["F"])[:2].round(4).tolist(),
                             "QX": round(float(v["M"] @ aX), 2), "QY": round(float(v["M"] @ aY), 2), "n": v["n"]} for k, v in sorted(per.items())},
            "TC09_fractional_faces": frac09, "TC09_deficit_F_engine_N_per_MPa": Fd_e.round(4).tolist(), "wetted_area_mm2": round(Aw, 1),
            "wetted_centroid_posed_mm": cw.round(2).tolist(),
            "TC09_boundary_removed": {"Q_gimbal_axes_Nmm_per_MPa": Qc.round(2).tolist(), "rods_OP_statics_N_per_MPa": np.linalg.solve(A, -Qc).round(3).tolist()}}


def lc3_unit(fn):
    d = json.loads((RES / fn).read_text())
    rows, T = [], {"ROD_1": [], "ROD_2": []}
    for s in d["subcases"]:
        if s["mode"] != "hold":
            continue
        ph = math.radians(s["lat_dir_deg"])
        rows.append([2.501, 6.29 * math.cos(ph), 6.29 * math.sin(ph), s["GZ_g"], s["ang_sign"] * 79.28])
        for r in T:
            T[r].append(s["rod_tension_N"][r])
    C = np.array(rows)
    out = {"post": fn, "post_sha16": sha16(RES / fn), "version": d["version"], "tb1": d["variant"].get("tb1"), "tiex": d["variant"].get("tiex")}
    for r, t in T.items():
        x, _, rk, _ = np.linalg.lstsq(C, np.array(t), rcond=None)
        out[r] = {"OP_N_per_MPa": round(x[0], 3), "G_lat_X_N_per_g": round(x[1], 3), "G_lat_Y_N_per_g": round(x[2], 3), "GZ_N_per_g": round(x[3], 3),
                  "EA_N_per_rad_s2": round(x[4], 4), "rank": int(rk), "max_residual_N": float(np.abs(np.array(t) - C @ x).max())}
    return out


def main():
    out = {"doc": __doc__.split("usage:")[0].strip(), "decks": [deck(r) for r in DECKS], "lc3_unit_rods": [lc3_unit(f) for f in LC3],
           "fbd_engine_cg_mm": {f: json.loads((RES / f).read_text()).get("engine_cg_implied_by_connector_moments_mm") for f in FBD},
           "fbd_sha16": {f: sha16(RES / f) for f in FBD}}
    (RES / "v352" / "op_moment_check_v352.json").write_text(json.dumps(out, indent=1, default=float))
    for d in out["decks"]:
        print(d["run"], d["cad"], d["version"], "F", d["total_F_N_per_MPa"], "vs", d["pressure_json_OP_net_N_per_MPa"], "Q", d["Q_gimbal_axes_Nmm_per_MPa"],
              "rods", d["rods_OP_statics_N_per_MPa"], "| TC-09 boundary removed: Q", d["TC09_boundary_removed"]["Q_gimbal_axes_Nmm_per_MPa"], "rods",
              d["TC09_boundary_removed"]["rods_OP_statics_N_per_MPa"], "| TC-09 fractional faces", len(d["TC09_fractional_faces"]))
    for u in out["lc3_unit_rods"]:
        print(u["post"], u["version"], u["tb1"], u["tiex"], "OP", u["ROD_1"]["OP_N_per_MPa"], u["ROD_2"]["OP_N_per_MPa"], "GX", u["ROD_1"]["G_lat_X_N_per_g"],
              u["ROD_2"]["G_lat_X_N_per_g"], "GY", u["ROD_1"]["G_lat_Y_N_per_g"], u["ROD_2"]["G_lat_Y_N_per_g"])
    print(json.dumps(out["fbd_engine_cg_mm"]))


if __name__ == "__main__":
    main()
