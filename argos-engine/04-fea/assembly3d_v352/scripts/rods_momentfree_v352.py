"""F2 rod forces with the OP-moment artefact removed: the statics estimate beside each affected row (fea3d 2026-10-20, report 9B.2 /
9B.3; lead 22:24:34Z: "Put the moment-free statics estimate beside each affected row").  Python only, no solve; the decks are streamed
read-only through op_moment_check_v352.deck() and nothing is written to the run tree.

Per R3 cone pose (pose_<cone>_v352r3R3):
  * OP step from the deck: applied moment Q about the two gimbal axes, the statics rod tensions t = A^-1 (-Q) (A = the rod moment matrix
    of the pose) and the same with the two TC-09 aft-boundary faces at p/Pc 1.0 ('TC-09 boundary removed'; the uniform residual correction
    re-balanced at the wetted-area centroid; op_moment_check_v352 method);
  * check: the statics OP rods against the OP unit rods recovered from the post (rodstep_cones_v352.json);
  * the posted sub-cases of GS / TD0 / TDP / LC6 / LC2F (s3d_pose_<cone>_v352r3R3.json: stored coefficients) recombined with the unit rods
    of rodstep_cones_v352.json, three ways:
      as_found     the posted OP unit rods (reproduces the post),
      tc09_removed the OP unit rods of the 'TC-09 boundary removed' statics (the moment-free statics estimate of the lead's note; the
                   remaining Q of about [294, 755] N mm/MPa is the residue of the other faces, the same kind as v3.5.1's),
      op_zero      OP unit rods 0 (the physical statics: the pressure resultant of a closed cavity with an axisymmetric exit has no moment
                   about the pivot);
    TD0 / TDP / LC6 / LC2F: rods by statics (max |rod| per case); GS: the rods are prescribed at +/-F_d, so EAX / EAY are re-solved for
    each corner exactly as post_s3d does and the engine angular-acceleration range is given.
Only the rod forces and the GS angular acceleration are estimated here; part stresses, connector and hole loads are not (they would
need a re-solve).  Tags: DERIVED on SIM.  Not physical approval.
usage: FEA3D_CAD=v352 rods_momentfree_v352.py -> results/v352/rods_momentfree_v352.json"""
from __future__ import annotations
import sys, json, math, hashlib
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import op_moment_check_v352 as OM      # noqa: E402  (deck(): OP load from the solver deck, statics rods, TC-09 boundary removed)

RES = Path("/home/claude/work/fea3d/results")
CONES = ["neutral", "alpha+", "alpha-", "beta+", "beta-", "combined045", "combined135", "combined225", "combined315"]
STEPS = ["OP", "GX", "GY", "GZ", "EAX", "EAY"]
F_D = {"centre": 441.0, "7deg": 552.0}      # N, as post_s3d (mechanical.json v2.1, DERIVED)
RODS = ("ROD_1", "ROD_2")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main():
    rs = json.loads((RES / "v352" / "rodstep_cones_v352.json").read_text())
    out = {"doc": __doc__.split("usage:")[0].strip(), "files_sha16": {"v352/rodstep_cones_v352.json": sha16(RES / "v352" / "rodstep_cones_v352.json")},
           "poses": {}}
    for p in CONES:
        run = f"pose_{p}_v352r3R3"
        dk = OM.deck(run)
        post = RES / f"s3d_pose_{p}_v352r3R3.json"
        out["files_sha16"][post.name] = sha16(post)
        out["files_sha16"][dk["deck"]] = dk["deck_sha16"]
        d = json.loads(post.read_text())
        u = rs["poses"][p]["v352_R3"]["unit_rod_N"]
        s = {st: np.array([u[r][st] for r in RODS]) for st in STEPS}
        op_post = s["OP"].copy()
        op_var = {"as_found": op_post, "tc09_removed": np.asarray(dk["TC09_boundary_removed"]["rods_OP_statics_N_per_MPa"]), "op_zero": np.zeros(2)}
        S2 = np.column_stack([s["EAX"], s["EAY"]])
        rec = {"deck": {k: dk[k] for k in ("deck", "deck_sha16", "Q_gimbal_axes_Nmm_per_MPa", "rods_OP_statics_N_per_MPa", "TC09_boundary_removed",
                                            "TC09_deficit_F_engine_N_per_MPa", "total_F_N_per_MPa", "pressure_json_OP_net_N_per_MPa")},
               "OP_unit_rods_from_post_N_per_MPa": op_post.round(4).tolist(),
               "statics_vs_post_max_abs_diff_N_per_MPa": float(np.max(np.abs(np.asarray(dk["rods_OP_statics_N_per_MPa"]) - op_post))),
               "cases": {}}
        for c in ("GS", "TD0", "TDP", "LC6", "LC2F"):
            cc = d["cases"][c]
            co_list, info = cc["subcase_coefs"], cc.get("subcases") or []
            res = {}
            for var, opr in op_var.items():
                sv = dict(s)
                sv["OP"] = opr
                if c == "GS":
                    aa, tmax = [], 0.0
                    for co, i_ in zip(co_list, info):
                        tt = np.asarray([i_["rod_tension_N"][r] for r in RODS])      # the prescribed corner (+/-F_d)
                        tL = sum(float(co.get(st, 0.0)) * sv[st] for st in ("OP", "GX", "GY", "GZ"))
                        ea = np.linalg.solve(S2, tt - tL)
                        aa.append(float(np.hypot(*ea)))
                        tmax = max(tmax, float(np.max(np.abs(tt))))
                    res[var] = {"ang_accel_rad_s2": [min(aa), max(aa)], "rod_abs_max_N": tmax}
                else:
                    t = [sum(float(co.get(st, 0.0)) * sv[st] for st in STEPS) for co in co_list]
                    res[var] = {"rod_abs_max_N": float(np.max(np.abs(t))),
                                "rod_max_N": {r: float(np.max([x[j] for x in t])) for j, r in enumerate(RODS)},
                                "rod_min_N": {r: float(np.min([x[j] for x in t])) for j, r in enumerate(RODS)}}
            if c == "GS":
                res["check_post_ang_accel_rad_s2"] = [min(i_["engine_ang_accel_rad_s2"] for i_ in info), max(i_["engine_ang_accel_rad_s2"] for i_ in info)]
            else:
                res["check_post_rod_abs_max_N"] = float(max(cc["rod_max_abs_N"].values()))
            rec["cases"][c] = res
        out["poses"][p] = rec
        g, td = rec["cases"]["GS"], max(rec["cases"]["TD0"]["as_found"]["rod_abs_max_N"], rec["cases"]["TDP"]["as_found"]["rod_abs_max_N"])
        print(f"{p:12s} Q {dk['Q_gimbal_axes_Nmm_per_MPa']} OP rods post {op_post.round(3).tolist()} statics {dk['rods_OP_statics_N_per_MPa']} "
              f"tc09rm {dk['TC09_boundary_removed']['rods_OP_statics_N_per_MPa']} | TD {td:.0f} -> "
              f"{max(rec['cases'][k]['tc09_removed']['rod_abs_max_N'] for k in ('TD0', 'TDP')):.0f} / "
              f"{max(rec['cases'][k]['op_zero']['rod_abs_max_N'] for k in ('TD0', 'TDP')):.0f} | LC2F {rec['cases']['LC2F']['as_found']['rod_abs_max_N']:.0f} -> "
              f"{rec['cases']['LC2F']['tc09_removed']['rod_abs_max_N']:.0f} / {rec['cases']['LC2F']['op_zero']['rod_abs_max_N']:.0f} | GS aa "
              f"{[round(x) for x in g['as_found']['ang_accel_rad_s2']]} -> {[round(x) for x in g['tc09_removed']['ang_accel_rad_s2']]} / "
              f"{[round(x) for x in g['op_zero']['ang_accel_rad_s2']]}", flush=True)
    # envelopes over the 9 poses
    env = {}
    for var in ("as_found", "tc09_removed", "op_zero"):
        env[var] = {
            "TD_rod_abs_max_N": [min(max(out["poses"][p]["cases"][k][var]["rod_abs_max_N"] for k in ("TD0", "TDP")) for p in CONES),
                                 max(max(out["poses"][p]["cases"][k][var]["rod_abs_max_N"] for k in ("TD0", "TDP")) for p in CONES)],
            "LC6_rod_abs_max_N": [min(out["poses"][p]["cases"]["LC6"][var]["rod_abs_max_N"] for p in CONES),
                                  max(out["poses"][p]["cases"]["LC6"][var]["rod_abs_max_N"] for p in CONES)],
            "LC2F_rod_abs_max_N": [min(out["poses"][p]["cases"]["LC2F"][var]["rod_abs_max_N"] for p in CONES),
                                   max(out["poses"][p]["cases"]["LC2F"][var]["rod_abs_max_N"] for p in CONES)],
            "GS_ang_accel_rad_s2": [min(out["poses"][p]["cases"]["GS"][var]["ang_accel_rad_s2"][0] for p in CONES),
                                    max(out["poses"][p]["cases"]["GS"][var]["ang_accel_rad_s2"][1] for p in CONES)]}
    out["envelope_9_poses"] = env
    out["max_statics_vs_post_diff_N_per_MPa"] = max(out["poses"][p]["statics_vs_post_max_abs_diff_N_per_MPa"] for p in CONES)
    (RES / "v352" / "rods_momentfree_v352.json").write_text(json.dumps(out, indent=1))
    print("envelope", json.dumps(env))
    print("max |statics - post| OP rods N/MPa:", out["max_statics_vs_post_diff_N_per_MPa"])


if __name__ == "__main__":
    main()
