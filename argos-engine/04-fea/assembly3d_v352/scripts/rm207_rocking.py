"""RM2-07 (REV-MECH-2, CHANGELOG 234): engine rocking pair WITH the servo in series AND the servo inertia J (fea3d 2026-10-20).
J = servo rotor + gear-train inertia at the servo output shaft, 1.6e-3 kg m2 (range 0.76-2.7e-3), SB-2292SG DATASHEET-derived,
ASSUMED, TO-VERIFY at B-TVC-1; ADDED to the engine inertia I_piv through the kinematic factor (CHANGELOG 227 (2); GNC convention):
  servo i turns phi_i = dL_i / r_eff,i with dL_i = sum_j a_ij theta_j  ->  reflected inertia matrix J G, G = B^T B, B_ij = a_ij / r_eff,i
  (at neutral: g = G_jj = 2 (37.806 / 11.139)^2 = 23.04).
(1) neutral (the modal pose), published method: f = f_FE,rigid-servo x sqrt(K_tot / K_same-mesh) (9A), then x sqrt(I / (I + J g)) with
    the modal effective inertia about the pivot I (SIM, modal_v351ca2b_c71).
(2) all 17 poses, lumped 2-DOF [DERIVED]: K_tot = (C_FE + A^-T diag(r_eff^2/k_s) A^-1)^-1 (k_*_c71_v352.json), inertia
    diag(I_R) + J G with I_R = K_same / (2 pi f_FE)^2 (Rayleigh-consistent with the modal run, neutral), eigenvalues of the 2 x 2.
usage: rm207_rocking.py -> results/v352/rocking_servo_J_v352.json
"""
import json, math
from pathlib import Path
import numpy as np

RES = Path("/home/claude/work/fea3d/results")
J_SET = {"J_low": 0.76e-3, "J_nom": 1.6e-3, "J_high": 2.7e-3}
KS = ("58", "174")
ms = json.loads((RES / "modal_summary_v351.json").read_text())
em = {e["dof"]: e for e in ms["engine_mount_modes"] if e["dof"] in ("r_x", "r_y")}
ax_of = {"r_x": 0, "r_y": 1}
runs = []
for fn in ("k_stop_c71_v352.json", "k_cone_c71_v352.json"):
    runs += json.loads((RES / fn).read_text())["runs"]
neu = [r for r in runs if r["run"] == "pose_neutral_c71"][0]


def G_of(r):
    A = np.array(r["servo_kinematics"]["arm_matrix_mm"])             # rows alpha, beta; columns rods 1, 2
    re = np.array([r["servo_kinematics"]["r_eff_mm"]["1"], r["servo_kinematics"]["r_eff_mm"]["2"]])
    B = (A / re[None, :]).T                                            # B[i, j] = a_ij / r_eff,i
    return B.T @ B, A, re


out = {"tag": "DERIVED (SIM modal + SIM K; k_s ASSUMED 58 / 174 N m/rad TO-VERIFY B-TVC; J ASSUMED GNC SB-2292SG datasheet-derived, TO-VERIFY B-TVC-1)",
       "J_kgm2": J_SET, "J_basis": "CHANGELOG 227 (2): servo rotor + gear train at the output shaft, ADDED to I_piv via the kinematic factor",
       "neutral": {}, "poses": []}
G0, A0, re0 = G_of(neu)
out["neutral"]["g_kinematic"] = [G0[0, 0], G0[1, 1]]
out["neutral"]["arm_mm"] = A0.tolist()
out["neutral"]["r_eff_mm"] = re0.tolist()
for dof, e in em.items():
    j = ax_of[dof]
    I = e["I_eff_kgm2"]
    row = {"axis": "alpha (outer, X)" if j == 0 else "beta (inner, ring Y)", "I_eff_kgm2": I, "f_FE_rigid_servo_Hz": e["f_FE_rigid_servo_Hz"]}
    for ks in KS:
        f0 = e[f"f_with_servo_k{ks}_Hz_DERIVED"]
        row[f"k_s{ks}"] = {"f_J_free_Hz": f0, **{k: f0 * math.sqrt(I / (I + J * G0[j, j])) for k, J in J_SET.items()},
                            "factor_J_nom": math.sqrt(I / (I + J_SET["J_nom"] * G0[j, j]))}
    out["neutral"]["beta" if j == 1 else "alpha"] = row
IR = np.array([em["r_x"]["K_static_same_mesh_Nm_per_rad"] / (2 * math.pi * em["r_x"]["f_FE_rigid_servo_Hz"]) ** 2,
               em["r_y"]["K_static_same_mesh_Nm_per_rad"] / (2 * math.pi * em["r_y"]["f_FE_rigid_servo_Hz"]) ** 2])
out["I_R_kgm2"] = IR.tolist()
allf = {ks: {k: [] for k in ["J_free"] + list(J_SET)} for ks in KS}
for r in runs:
    G, A, re = G_of(r)
    Cfe = np.array(r["two_axis"]["C_FE_rad_per_Nmm"]) * 1e3           # rad / (N m)
    Ai = np.linalg.inv(A * 1e-3)                                        # A in m
    pr = {"run": r["run"], "pose_deg": r["pose_deg"], "r_eff_mm": re.tolist(), "g_diag": [G[0, 0], G[1, 1]]}
    for ks in KS:
        k_s = float(ks)
        Cs = Ai.T @ np.diag((re * 1e-3) ** 2 / k_s) @ Ai                # rad / (N m)
        Kt = np.linalg.inv(Cfe + Cs)
        res = {}
        for k, J in [("J_free", 0.0)] + list(J_SET.items()):
            Mm = np.diag(IR) + J * G
            w2 = np.sort(np.real(np.linalg.eigvals(np.linalg.solve(Mm, Kt))))
            f = np.sqrt(w2) / (2 * math.pi)
            res[k] = f.tolist()
            allf[ks][k] += f.tolist()
        pr[f"k_s{ks}"] = res
    out["poses"].append(pr)
out["pose_range_Hz"] = {ks: {k: [min(v), max(v)] for k, v in d.items()} for ks, d in allf.items()}
out["pose_range_note"] = "lumped 2-DOF over the 17 poses (8 stops at 8 deg, neutral, 8 cone poses at 7 deg), rigid airframe"
(RES / "v352" / "rocking_servo_J_v352.json").write_text(json.dumps(out, indent=1))
n = out["neutral"]
for a in ("beta", "alpha"):
    for ks in KS:
        v = n[a][f"k_s{ks}"]
        print(a, ks, " J-free %.2f  J 0.76e-3 %.2f  1.6e-3 %.2f  2.7e-3 %.2f  factor %.3f" % (v["f_J_free_Hz"], v["J_low"], v["J_nom"], v["J_high"], v["factor_J_nom"]))
print("g", n["g_kinematic"], "I_R", IR)
for ks in KS:
    print("poses k_s", ks, {k: [round(x, 2) for x in v] for k, v in out["pose_range_Hz"][ks].items()})
