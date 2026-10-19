"""FEA3D LC3 post-processing: max thrust at the 8 deg conical stop + gnc.json v3.1 limit inertial loads + actuator runaway onto the stop.

usage: post_lc3.py RUN[,RUN...] [state=B1_21.65]
Runs: pose_stopXXX (posename stopXXX, coarse=2, steps OP,GX,GY,GZ,EAX,EAY,R1,R2,BUMP; no TH step: the solved fields are COLD,
allowables are read at the B1_21.65 node temperatures; thermal + manifold stresses are added afterwards by lc3_bound.py).

Load combination (successor fea3d, 2026-10-15; all coefficients x the unit steps, superposition):
  OP x Pc_max 2.501 MPa (operating pressure distribution, vacuum outside: ~528 N vacuum / ~500 N sea-level thrust)
  lateral 6.29 g at the pivot (gnc.json design_limit_loads.lateral_accel_at_pivot_touchdown_g, SIM max) in 8 fixed-frame directions
  axial GZ in {0 (static fire / hold-down: the full thrust reaches the mount), 5.43 g (axial_accel_touchdown_g, SIM max)}
  body angular acceleration 79.28 rad/s2 (body_angular_accel_touchdown_rad_s2, SIM max) about the lateral direction that maximises /
      minimises the actuator moment toward the stop (2 signs); EAX = engine + ring about the outer axis X, EAY = engine about the inner axis
  bumper force fb in {0 (actuator holding, no push), fb_run (actuator runaway onto the stop: the largest fb for which the actuator
      moment toward the stop <= M_stop 41.14 N m (mechanical.json v2.1 tvc_actuation.design_loads.M_engine_stop_Nm, as-built 8.4 V
      stall) AND each rod force <= F_rod_stop 609 N (same block, lead design value; stall-limited actuator))}.
  The touchdown set envelopes the flight set (0.61 g, 4.04 g, 11.01 rad/s2): every flight coefficient lies inside the convex hull of the
  touchdown sub-cases and von Mises / max principal are convex in the stress tensor (min principal concave), so the envelope is attained
  at the vertices.  Max thrust with touchdown inertia and a runaway onto the stop is a BOUNDING combination (stated, conservative).
Rod forces are NOT free parameters: the two rod springs are the only gimbal-axis moment path, so for a given fb statics fixes them; the
R1/R2 unit pairs (applied across the rod springs) are reported for the check only and not combined.
Units: mm, N, MPa, K (moments N mm in the arrays, N m in the summary).  Engine frame +Z forward, pivot origin.
"""
from __future__ import annotations
import sys, json, math, time
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF        # noqa: E402
import asm3d as A3          # noqa: E402

RUNS, RES = PF.RUNS, PF.RES
PC_MAX = PF.PC_MAX
G_LAT = 6.29        # g, gnc.json v3.1 design_limit_loads.lateral_accel_at_pivot_touchdown_g (SIM max of 500 runs)
G_AX = (0.0, 5.43)  # g, 0 = static fire / hold-down; 5.43 = axial_accel_touchdown_g (SIM max)
ALPHA = 79.28       # rad/s2, body_angular_accel_touchdown_rad_s2 (SIM max)
M_STOP = 41.14e3    # N mm, mechanical.json v2.1 tvc_actuation.design_loads.M_engine_stop_Nm (DERIVED as-built, runaway onto the stop)
F_ROD_STOP = 609.0  # N, mechanical.json v2.1 F_rod_stop_N (lead) - comparison only
SFY, SFU = 1.5, 2.0
NLAT = 8


def rod_springs(M):
    out = []
    for lab, e, n1, n2, k in M.springA:
        if lab.startswith("ROD_"):
            x1, x2 = M.xyzp([n1])[0], M.xyzp([n2])[0]
            d = x2 - x1
            out.append((lab, int(n1), int(n2), float(k), d / np.linalg.norm(d)))
    return out


def spring_forces_per_step(M, F, steps):
    """{label: {step: force N (tension +)}} for every SPRINGA (rods, bearings, J-FWD, feet ...)."""
    out = {}
    X = {}
    for lab, e, n1, n2, k in M.springA:
        if n1 not in X:
            X[n1] = M.xyzp([n1])[0]
        if n2 not in X:
            X[n2] = M.xyzp([n2])[0]
        d = X[n2] - X[n1]
        e12 = d / np.linalg.norm(d)
        out[lab] = {st: float(k * (F[f"U_{st}"][n2] - F[f"U_{st}"][n1]) @ e12) for st in steps}
    return out


def run(name, state="B1_21.65"):
    t0 = time.time()
    M, meta = PF.load_model(name)
    steps = meta["steps"]
    F = PF.load_fields(name, state)
    names, body, T, X = PF.node_arrays(M, name, state)
    reg, srep, sing = PF.singular_sets(M, X, ex_r=1.0)
    RF = PF.reactions(name, state, steps)
    Rg = {k: np.asarray(v) for k, v in meta["Rg"].items()}
    aX, aY = np.array([1.0, 0, 0]), Rg["ring"] @ np.array([0, 1.0, 0])
    # ------------------------------------------------------------------ rod moment matrix (tension + ; moment on the engine)
    rg = meta.get("rod_geom")
    if not rg:   # refinement runs without R1/R2 steps: same pose and rod geometry as the base pose run (only the GM-02 mesh differs)
        import re as _re
        base = _re.sub(r"_gm0[12]r\d", "", name)
        rg = json.loads((RUNS / base / "model.json").read_text())["rod_geom"]
        print(f"[lc3 {name}] rod geometry taken from {base}", flush=True)
    A = np.zeros((2, 2))
    for j, i in enumerate(sorted(rg, key=int)):
        xL, e = np.asarray(rg[i]["lever_eye"]), np.asarray(rg[i]["e_push_on_engine"])
        m = np.cross(xL, -e)                   # tension t pulls the lever eye toward the horn: force -t e
        A[:, j] = [m @ aX, m @ aY]
    SF_ = spring_forces_per_step(M, F, steps)
    rods = sorted([k for k in SF_ if k.startswith("ROD_")])
    s = {st: np.array([SF_[r][st] for r in rods]) for st in steps}          # rod tension per unit step
    Q = {st: A @ s[st] for st in steps}                                     # rods' reaction moment (N mm) per unit step
    bu = meta["bumper"]
    xc, nout = np.asarray(bu["contact_point_mm"]), np.asarray(bu["n_out"])
    mb = np.cross(xc, -nout)
    Qbump = np.array([mb @ aX, mb @ aY])                                     # moment of the unit bumper force on the engine
    QB = Q["BUMP"]
    u = QB / np.linalg.norm(QB)                                              # actuator moment direction INTO the stop
    chk = {"Q_rods_BUMP_Nmm": QB.tolist(), "Q_bumper_force_Nmm": Qbump.tolist(),
           "equilibrium_residual_rel": float(np.linalg.norm(QB + Qbump) / np.linalg.norm(Qbump)),
           "R1_rod1_absorbed_fraction": float(-SF_[rods[0]]["R1"]) if "R1" in steps else None,
           "R2_rod2_absorbed_fraction": float(-SF_[rods[1]]["R2"]) if "R2" in steps else None}
    # angular-acceleration direction extremising the into-stop moment
    qx, qy = Q["EAX"] @ u, Q["EAY"] @ u
    psi = math.atan2(qy, qx)
    subs, info = [], []
    for k in range(NLAT):
        ph = 2 * math.pi * k / NLAT
        for gz in G_AX:
            for sg in (+1.0, -1.0):
                co = {"OP": PC_MAX, "GX": G_LAT * math.cos(ph), "GY": G_LAT * math.sin(ph), "GZ": gz,
                      "EAX": sg * ALPHA * math.cos(psi), "EAY": sg * ALPHA * math.sin(psi)}
                QL = sum(c * Q[st] for st, c in co.items())
                tL = sum(c * s[st] for st, c in co.items())
                # runaway: maximise fb subject to (i) actuator moment into the stop <= M_stop and (ii) |rod force| <= F_rod_stop per rod
                # (stall-limited; mechanical.json v2.1).  Rod forces are affine in fb: t = tL + fb s_B.
                lims = [((M_STOP - QL @ u) / np.linalg.norm(QB), "M_stop 41.14 N m")]
                for j_, r_ in enumerate(rods):
                    sb = s["BUMP"][j_]
                    if abs(sb) > 1e-9:
                        lims.append((((-F_ROD_STOP if sb < 0 else F_ROD_STOP) - tL[j_]) / sb, f"{r_} at {F_ROD_STOP:.0f} N"))
                fb_run, gov = min(lims, key=lambda z: z[0])
                for mode, fb in (("hold", 0.0), ("runaway", max(fb_run, 0.0))):
                    c2 = dict(co, BUMP=fb)
                    t = tL + fb * s["BUMP"]
                    subs.append(c2)
                    info.append({"lat_dir_deg": round(math.degrees(ph), 1), "GZ_g": gz, "ang_sign": sg, "mode": mode, "fb_N": float(fb),
                                 "rod_tension_N": {r: float(v) for r, v in zip(rods, t)},
                                 "actuator_moment_into_stop_Nm": float((A @ t) @ u / 1e3),
                                 "actuator_moment_Nm": (A @ t / 1e3).tolist(), "load_moment_into_stop_Nm": float(-(QL @ u) / 1e3),
                                 "runaway_limit": (gov if mode == "runaway" else None)})
    rows, ev = PF.part_margins(M, names, body, T, X, reg, F, "LC3", subs, SFY, SFU, state)
    for r in rows:
        si = next(i for i, c in enumerate(subs) if all(abs(c.get(k, 0) - v) < 1e-3 for k, v in r["subcase"].items()))
        r["subcase_info"] = {k: v for k, v in info[si].items() if k != "rod_tension_N"}
    # ------------------------------------------------------------------ envelopes for the hot bound (lc3_bound.py)
    nn = F["S_OP"].shape[0]
    env = {k: np.full(nn, -np.inf, np.float32) for k in ("vm", "vmD", "s1", "s1D")}
    env.update({k: np.full(nn, np.inf, np.float32) for k in ("s3", "s3D")})
    S_OP = F["S_OP"].astype(np.float64)
    brittle_nodes = np.zeros(nn, bool)
    for nm, b in M.bodies.items():
        if b.mat in PF.BRITTLE:
            brittle_nodes[b.noff:b.noff + len(b.X0)] = True
    for co, S, Sm in ev:
        D = S - co["OP"] * S_OP
        env["vm"] = np.maximum(env["vm"], PF.vm(S).astype(np.float32))
        env["vmD"] = np.maximum(env["vmD"], PF.vm(D).astype(np.float32))
        idx = np.nonzero(brittle_nodes)[0]
        s1, s3 = PF.principal(S[idx])
        d1, d3 = PF.principal(D[idx])
        env["s1"][idx] = np.maximum(env["s1"][idx], s1)
        env["s3"][idx] = np.minimum(env["s3"][idx], s3)
        env["s1D"][idx] = np.maximum(env["s1D"][idx], d1)
        env["s3D"][idx] = np.minimum(env["s3D"][idx], d3)
    regm = np.zeros(nn, bool)
    regm[:len(reg)] = reg
    np.savez_compressed(RES / f"lc3_env_{name}.npz", reg=regm, **env)
    # ------------------------------------------------------------------ reactions (ICD), connectors, displacement
    icd_env, totals = {}, []
    for si, co in enumerate(subs):
        rfc = PF.combine_rf(RF, co)
        tab, tot = PF.icd_table(M, rfc)
        totals.append({"si": si, **tot})
        for rr in tab:
            h = icd_env.setdefault(rr["hole"], {"x_mm": rr["x_mm"], "max_shear_N": 0.0, "max_radial_out_N": -1e9, "min_radial_N": 1e9,
                                                "max_abs_axial_N": 0.0, "max_abs_tangential_N": 0.0})
            if rr["shear_in_screw_N"] > h["max_shear_N"]:
                h["max_shear_N"], h["si_shear"] = rr["shear_in_screw_N"], si
            h["max_radial_out_N"] = max(h["max_radial_out_N"], rr["radial_N"])
            h["min_radial_N"] = min(h["min_radial_N"], rr["radial_N"])
            h["max_abs_axial_N"] = max(h["max_abs_axial_N"], abs(rr["axial_N"]))
            h["max_abs_tangential_N"] = max(h["max_abs_tangential_N"], abs(rr["tangential_N"]))
    con_env = {}
    for lab, d in SF_.items():
        vals = [sum(c * d[st] for st, c in co.items()) for co in subs]
        k = int(np.argmax(np.abs(vals)))
        con_env[lab] = {"max_abs_N": float(abs(vals[k])), "value_N": float(vals[k]), "si": k}
    U0 = sum(c * F[f"U_{st}"] for st, c in subs[0].items())
    umax = {}
    for si in (0, 1):
        U = sum(c * F[f"U_{st}"] for st, c in subs[si].items())
        for nm in names:
            b = M.bodies[nm]
            umax[nm] = max(umax.get(nm, 0.0), float(np.linalg.norm(U[b.noff:b.noff + len(b.X0)], axis=1).max()))
    eq = {st: {"sum_RF_N": [float(c) for c in sum(RF[st].values())]} for st in steps}
    rod_c = {r: float(max(-i_["rod_tension_N"][r] for i_ in info)) for r in rods}
    out = {"run": name, "state_for_allowables": state, "version": A3.VERSION, "date": "2026-10-15", "variant": meta["variant"],
           "pose_deg": [meta["alpha"], meta["beta"]], "stop_azimuth_deg": meta["variant"].get("stop"),
           "case": {"id": "LC3", "title": f"LC3 at the 8 deg stop (azimuth {meta['variant'].get('stop')}): Pc {PC_MAX * 10:.2f} bar OP + "
                    f"{G_LAT} g lateral (8 dirs) + axial {G_AX} g + {ALPHA} rad/s2 + actuator runaway onto the stop {M_STOP / 1e3} N m "
                    f"(bumper) or hold; COLD (no thermal, no manifold); allowables at the {state} node temperature",
                    "criterion": "SF 1.5 yield / 2.0 ultimate (ENG-10, 188 (9) nominal); brittle s1/St, s3/Sc SF 2.0", "n_subcases": len(subs)},
           "rod_moment_matrix_Nmm_per_N": A.tolist(), "axes": {"outer_X": aX.tolist(), "inner_Y": aY.tolist()},
           "bumper": bu, "checks": chk, "psi_ang_deg": math.degrees(psi), "subcases": info,
           "rod_max_compression_N": rod_c, "F_rod_stop_mechanical_json_N": F_ROD_STOP,
           "fb_run_range_N": [float(min(i_["fb_N"] for i_ in info if i_["mode"] == "runaway")),
                              float(max(i_["fb_N"] for i_ in info if i_["mode"] == "runaway"))],
           "margins": rows, "singular": srep, "icd_envelope": icd_env,
           "icd_totals_envelope": {"max_abs_F_on_airframe_N": np.max(np.abs([t_["F_total_on_airframe_N"] for t_ in totals]), axis=0).tolist(),
                                   "max_abs_M_about_pivot_Nmm": np.max(np.abs([t_["M_total_about_pivot_Nmm"] for t_ in totals]), axis=0).tolist()},
           "connectors_envelope": con_env, "max_abs_U_mm": umax, "equilibrium_unit_steps": eq}
    (RES / f"f1_post_lc3_{name}.json").write_text(json.dumps(out, indent=1, default=float))
    worst = sorted([r for r in rows if r["set"] == "regular"], key=lambda r: r["MS"])[:6]
    print(f"[lc3 {name}] {time.time() - t0:.1f} s; fb_run {out['fb_run_range_N']}; rods max compression {rod_c}; eq residual "
          f"{chk['equilibrium_residual_rel']:.2e}; worst: " + "; ".join(f"{r['part']} {r['MS']:+.3f}/{(r['MS_ult'] if r['MS_ult'] is not None else float('nan')):+.3f}" for r in worst), flush=True)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    opts = dict(x.split("=", 1) for x in a[1:])
    for nm in a[0].split(","):
        run(nm, opts.get("state", "B1_21.65"))
