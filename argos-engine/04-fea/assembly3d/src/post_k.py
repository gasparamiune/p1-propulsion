"""FEA3D F3 (RM1-08, ENG-11): gimbal-axis rotational stiffness K_alpha / K_beta of the engine held by the TVC actuator chains.

usage: post_k.py RUN[,RUN...] [state=B1_21.65]
  runs solved with steps containing EAX and EAY (unit angular acceleration of engine + ring about the outer axis X / of the engine about
  the inner axis (ring Y)); rods = SPRINGA with the Mechanical chain stiffness (servo output RIGID).

K_FE = M_axis / theta_axis with M = moment of the applied unit inertial loads about the pivot (reaction moment carried by the chains)
and theta = engine rotation about the same axis: (a) mass-weighted best-fit rigid rotation of all engine nodes, (b) best-fit rotation
of the nozzle exit region (NZ-01 + TC-09 aft of z -200: thrust-line pointing).  Compliance split: rods (spring elongations), the rest
= structure (collar, pins / needles / washers, ring, posts, brackets, horns).  Servo output compliance added in series afterwards:
K_servo,engine = 2 a^2 k_s / r_eff^2 (both chains, arm a about the axis, horn radius r_eff), k_s = 58-174 N m/rad per servo (line 13
range, TO-VERIFY by bench test).  Units: N, mm, rad -> reported in N m/rad.  fea3d 2026-10-13.
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF        # noqa: E402
import post_modal as PMd    # noqa: E402
import asm_build as AB      # noqa: E402
import asm3d as A3          # noqa: E402

RUNS, RES = PF.RUNS, PF.RES
K_SERVO = (58.0, 174.0)          # N m/rad per servo output (Mechanical line 13 range; ASSUMED until bench B-TVC)
V5C = (3133.0, 7406.0)           # N m/rad, GNC V5c range (comparison)


def run_k(name, state):
    M, meta = PF.load_model(name)
    steps = meta["steps"]
    for st in steps:                               # rebuild the unit loads exactly as run_f1.build did
        if st == "EAX":
            AB.inertial(M, st, ("ang", np.array([1.0, 0, 0]), {"engine", "ring"}))
        elif st == "EAY":
            AB.inertial(M, st, ("ang", M.Rg["ring"] @ np.array([0, 1.0, 0]), {"engine"}))
    Z = np.load(RUNS / name / state / "fields.npz")
    N1 = M.next_n + 1
    X = np.zeros((N1, 3))
    for nm, b in M.bodies.items():
        X[b.noff:b.noff + len(b.X0)] = M.Xp[nm]
    for nid, (x, g) in M.extra.items():
        if nid < N1:
            X[nid] = M.posed(np.asarray(x)[None], g)[0]
    m, grp, _ = PMd.lumped_masses(M) if hasattr(M, "mass_el") else (None, None, None)
    if m is None:
        M.mass_el = []
        m, grp, _ = PMd.lumped_masses(M)
    eng = np.concatenate([b.noff + np.arange(len(b.X0)) for nm, b in M.bodies.items() if b.grp == "engine"])
    sub = eng[:: max(1, len(eng) // 8000)]
    A_eng = PMd.rigid_fit_op(X[sub], m[sub] / m[sub].sum())
    noz = []
    for nm in ("NZ-01", "TC-09"):
        b = M.bodies[nm]
        sel = np.nonzero(M.Xp[nm] @ (M.Rg["engine"] @ np.array([0, 0, 1.0])) < -200.0)[0]
        noz.append(b.noff + sel)
    noz = np.concatenate(noz)
    nsub = noz[:: max(1, len(noz) // 4000)]
    A_noz = PMd.rigid_fit_op(X[nsub], np.ones(len(nsub)) / len(nsub))
    rods = {b_["label"]: b_ for b_ in M.bush if b_["label"].startswith("ROD_")}
    axes = {"EAX": np.array([1.0, 0, 0]), "EAY": M.Rg["ring"] @ np.array([0, 1.0, 0])}
    out = {"run": name, "state": state, "pose_deg": [M.alpha, M.beta], "variant": meta["variant"], "k_chain_N_per_mm": M.k_chain,
           "bearing": M.bk, "axes": {}}
    for st in ("EAX", "EAY"):
        if f"U_{st}" not in Z.files:
            continue
        U = Z[f"U_{st}"].astype(np.float64)[:N1]
        if "U_TH" in Z.files:
            U = U - Z["U_TH"].astype(np.float64)[:N1]
        ax = axes[st]
        Fl = np.zeros((N1, 3))
        for n, v in M.loads.get(st, {}).items():
            Fl[int(n)] += v
        Mom = np.cross(X, Fl).sum(0)                    # moment of the applied inertial loads about the pivot (N mm)
        M_ax = float(Mom @ ax)
        rb = A_eng @ U[sub].ravel()
        th = float(rb[3:] @ ax)
        rbn = A_noz @ U[nsub].ravel()
        thn = float(rbn[3:] @ ax)
        # rods: spring force and moment share
        rod = {}
        th_rods_num = 0.0
        for lab, bu in rods.items():
            H, L = int(bu["A"]), int(bu["B"])
            e = AB.unit(X[L] - X[H])
            dl = float((U[L] - U[H]) @ e)
            k = float(bu["springs"][0][3])
            Fr = -k * dl                                  # + = compression
            arm = float(np.cross(X[L], e) @ ax)          # moment about the axis of a unit push on the engine at the lever eye
            rod[lab] = {"elongation_mm": dl, "force_N_compression_pos": Fr, "arm_mm": arm, "moment_Nmm": Fr * arm}
            th_rods_num += arm * arm * k
        K_fe = abs(M_ax / th) if th else None
        K_rods_only = th_rods_num                        # sum k a^2 (N mm/rad), rods alone (rigid structure)
        C_struct = (1.0 / K_fe - 1.0 / K_rods_only) if K_fe else None
        arms = [abs(r["arm_mm"]) for r in rod.values()]
        r_eff = []
        g = A3.tvc_geometry()
        for sv in g["servos"]:
            r_eff.append(g["r_h"])
        res = {"M_applied_Nmm": M_ax, "theta_engine_rad": th, "theta_nozzle_rad": thn,
               "K_FE_engine_Nm_per_rad": K_fe / 1e3 if K_fe else None, "K_FE_nozzle_Nm_per_rad": abs(M_ax / thn) / 1e3 if thn else None,
               "K_rods_only_Nm_per_rad": K_rods_only / 1e3, "structure_compliance_share": (C_struct * K_fe) if K_fe else None,
               "rods": rod, "servo_series": {}}
        for ks in K_SERVO:
            k_srod = ks * 1e3 / (g["r_h"] ** 2)          # N/mm at the horn eye (horn normal to the rod)
            K_serv = sum(k_srod * a * a for a in arms)  # N mm/rad
            for lab_, Kf in (("engine", K_fe), ("nozzle", abs(M_ax / thn) if thn else None)):
                if Kf:
                    Kt = 1.0 / (1.0 / Kf + 1.0 / K_serv)
                    res["servo_series"][f"k_s{ks:g}_{lab_}"] = {"K_servo_engine_Nm_per_rad": K_serv / 1e3, "K_total_Nm_per_rad": Kt / 1e3}
        out["axes"]["alpha (outer, X)" if st == "EAX" else "beta (inner, ring Y)"] = res
    return out


def main(argv):
    names = argv[0].split(",")
    opts = dict(a.split("=", 1) for a in argv[1:])
    state = opts.get("state", "B1_21.65")
    allr = [run_k(nm, state) for nm in names]
    tag = opts.get("tag", names[0])
    (RES / f"k_{tag}.json").write_text(json.dumps({"date": "2026-10-13", "version": A3.VERSION, "servo_k_range_Nm_per_rad": K_SERVO,
                                                   "V5c_range_Nm_per_rad": V5C, "runs": allr}, indent=1, default=float))
    for r in allr:
        for axn, a in r["axes"].items():
            print(f"{r['run']:<22} {str(r['pose_deg']):<28} {axn:<22} K_FE eng {a['K_FE_engine_Nm_per_rad']:9.0f} noz {a['K_FE_nozzle_Nm_per_rad']:9.0f} "
                  f"rods-only {a['K_rods_only_Nm_per_rad']:9.0f} struct share {a['structure_compliance_share']:.3f} | "
                  + " ".join(f"{k}: {v['K_total_Nm_per_rad']:.0f}" for k, v in a["servo_series"].items()))


if __name__ == "__main__":
    main(sys.argv[1:])
