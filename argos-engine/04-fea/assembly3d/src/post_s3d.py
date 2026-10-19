"""FEA3D F2 (S-3D gimbal on CAD v3.5.1) post-processing of the 9 range-cone poses (neutral, alpha+/-, beta+/-, 4 combined at 7 deg).

usage: post_s3d.py RUN[,RUN...] [state=B1_21.65]
Runs: pose_<name>_c71 (asm v1.2, coarse=2, lever roots refined, steps OP,GX,GY,GZ,EAX,EAY,R1,R2; COLD: no TH step; allowables at the
B1_21.65 node temperatures as in F1 LC3; the hot increment is added afterwards by lc3_bound.py envpfx=s3d_env_ out=_s3d).
Load cases (successor fea3d 2026-10-19; S-3D v1.1 case set (04-fea/structural/gimbal_strength.py) re-stated on the current loads;
superposition of the unit steps, linear elastic):
  GS   both servos at stall: rod forces at +/-F_d(pose) (4 sign corners; mechanical.json v2.1 tvc_actuation.design_loads
       F_rod_centre_N 441 / F_rod_7deg_N 552, DERIVED) realised by the engine angular acceleration they produce (EAX, EAY solved so the
       two FE rod forces equal the corner values: the stall moment is reacted by the engine inertia, not by a fictitious support)
       + OP x Pc_max 2.501 MPa + flight inertia 0.61 g lateral (8 dirs) + axial {0, 4.04 g} (gnc.json v3.1 SIM max)
       + hose end force 31.2 N (hose_end_reactions_v341_v1, EI 0.184 N m2, at the 8 deg stop: bound for 7 deg) as an equivalent
       lateral g on the model along the lateral direction (DERIVED approximation: force through the gimbal right, point of action not;
       the hose moment goes into the rods, which are prescribed here).  SF 1.5 / 2.0.  Envelopes the flight case LC1 at the cone
       poses (rod forces inside the corner box, convexity).
  TD   touchdown, servos holding (rigid): OP {0, Pc_max} + 6.29 g lateral (8 dirs) + hose equivalent + axial {0, 5.43 g} + 79.28 rad/s2
       in 4 directions of the (EAX, EAY) plane (gnc.json v3.1 design_limit_loads touchdown SIM max); rod forces from statics (reported
       against the 609 N stall limit: above it the servo back-drives and the engine goes to the stop = F1 LC3).  SF 1.5 / 2.0.
  LC6  hard landing (loadcases v1 LC6, ASSUMED envelope; also the F4 10 g axial envelope): 10 g axial (both signs) + 3 g lateral
       (8 dirs), no thrust; rods from statics.  SF 1.5 / 2.0.
  LC2F stuck-pintle thrust 907.7 N (combustion, loadcases v2 LC2F) as OP scaled to that net thrust + flight inertia (8 dirs, axial
       {0, 4.04 g}); SF 1.0 yield / 1.5 ultimate; gimbal / mount parts only (the pressure parts are not at a defined Pc in this case).
Outputs results/s3d_<run>.json (per case: per-part min MS regular / all, rod forces, connector and ICD envelopes) and
results/s3d_env_<run>.npz (vM / principal envelopes of GS + TD + LC6 for the hot bound).  Units mm, N, MPa.
"""
from __future__ import annotations
import sys, json, math, time
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF        # noqa: E402
import post_lc3 as PL       # noqa: E402
import asm3d as A3          # noqa: E402

RUNS, RES = PF.RUNS, PF.RES
PC_MAX = PF.PC_MAX
G = A3.G_MM / 1000.0
F_D = {"centre": 441.0, "7deg": 552.0}       # N, mechanical.json v2.1 tvc_actuation.design_loads (DERIVED, lead governs)
F_STALL = 609.0                                # N, mechanical.json v2.1 F_rod_stop_N / stall_load_on_structure (DERIVED)
G_LAT_FL, G_AX_FL = 0.61, 4.04                 # g, gnc.json v3.1 flight SIM max
G_LAT_TD, G_AX_TD, ALPHA_TD = 6.29, 5.43, 79.28  # g, g, rad/s2, gnc.json v3.1 touchdown SIM max
LC6_AX, LC6_LAT = 10.0, 3.0                    # g, loadcases v1 LC6 (ASSUMED envelope)
T_STUCK = 907.7                                # N, loadcases v2 LC2F stuck-pintle thrust (combustion)
HOSE_F = 31.2                                  # N, hose_end_reactions_v341_v1 EI 0.184 N m2 at the 8 deg stop
NLAT = 8


def rows_merge(a, b):
    """Per (part, set) keep the lower MS row; keep the lower MS_ult separately."""
    out = {}
    for r in a + b:
        k = (r["part"], r["set"])
        if k not in out:
            out[k] = dict(r)
            continue
        o = out[k]
        mu = [x for x in (o.get("MS_ult"), r.get("MS_ult")) if x is not None]
        if r["MS"] < o["MS"]:
            out[k] = dict(r)
        if mu:
            out[k]["MS_ult"] = min(mu)
    return list(out.values())


def run(name, state="B1_21.65"):
    t0 = time.time()
    M, meta = PF.load_model(name)
    steps = meta["steps"]
    F = PF.load_fields(name, state)
    names, body, T, X = PF.node_arrays(M, name, state)
    reg, srep, sing = PF.singular_sets(M, X, ex_r=1.0)
    RF = PF.reactions(name, state, steps)
    mj = json.loads((RUNS / name / "mass.json").read_text())
    g_hose = HOSE_F / (mj["group_model_kg"]["engine"] * G)
    SF_ = PL.spring_forces_per_step(M, F, steps)
    rods = sorted([k for k in SF_ if k.startswith("ROD_")])
    s = {st: np.array([SF_[r][st] for r in rods]) for st in steps}      # rod tension (+) per unit step
    op_z = abs(float(sum(RF["OP"].values())[2]))                         # N per MPa, this run's OP net axial (airframe reaction)
    amp = math.hypot(meta["alpha"], meta["beta"])
    fd = F_D["centre"] if amp < 1.0 else F_D["7deg"]
    S2 = np.column_stack([s["EAX"], s["EAY"]])                         # rod tensions per unit angular acceleration
    cases = {}
    env = None
    nn = F["S_OP"].shape[0]
    brittle_nodes = np.zeros(nn, bool)
    for nm, b in M.bodies.items():
        if b.mat in PF.BRITTLE:
            brittle_nodes[b.noff:b.noff + len(b.X0)] = True
    S_OP = F["S_OP"].astype(np.float64)

    def lat(ph, g):
        return {"GX": g * math.cos(ph), "GY": g * math.sin(ph)}

    def build(cid):
        subs, info = [], []
        for k in range(NLAT):
            ph = 2 * math.pi * k / NLAT
            if cid == "GS":
                for gz in (0.0, G_AX_FL):
                    for c1 in (+1, -1):
                        for c2 in (+1, -1):
                            co = {"OP": PC_MAX, **lat(ph, G_LAT_FL + g_hose), "GZ": gz}
                            tL = sum(c * s[st] for st, c in co.items())
                            tt = np.array([c1 * fd, c2 * fd])
                            ea = np.linalg.solve(S2, tt - tL)
                            co.update({"EAX": float(ea[0]), "EAY": float(ea[1])})
                            subs.append(co)
                            info.append({"lat_dir_deg": round(math.degrees(ph), 1), "GZ_g": gz, "rod_target_N": tt.tolist(),
                                         "engine_ang_accel_rad_s2": float(np.hypot(*ea))})
            elif cid in ("TD0", "TDP"):
                for gz in (0.0, G_AX_TD):
                    for q in range(4):
                        ps = math.pi / 2 * q
                        co = {"OP": (PC_MAX if cid == "TDP" else 0.0), **lat(ph, G_LAT_TD + g_hose), "GZ": gz,
                              "EAX": ALPHA_TD * math.cos(ps), "EAY": ALPHA_TD * math.sin(ps)}
                        subs.append(co)
                        info.append({"lat_dir_deg": round(math.degrees(ph), 1), "GZ_g": gz, "ang_dir_deg": 90 * q})
            elif cid == "LC6":
                for gz in (LC6_AX, -LC6_AX):
                    subs.append({"OP": 0.0, **lat(ph, LC6_LAT), "GZ": gz})
                    info.append({"lat_dir_deg": round(math.degrees(ph), 1), "GZ_g": gz})
            elif cid == "LC2F":
                for gz in (0.0, G_AX_FL):
                    subs.append({"OP": T_STUCK / op_z, **lat(ph, G_LAT_FL), "GZ": gz})
                    info.append({"lat_dir_deg": round(math.degrees(ph), 1), "GZ_g": gz})
        for co, i_ in zip(subs, info):
            t = sum(c * s[st] for st, c in co.items())
            i_["rod_tension_N"] = {r: float(v) for r, v in zip(rods, t)}
        return subs, info

    spec = [("GS", 1.5, 2.0), ("TD0", 1.5, 2.0), ("TDP", 1.5, 2.0), ("LC6", 1.5, 2.0), ("LC2F", 1.0, 1.5)]
    for cid, sfy, sfu in spec:
        subs, info = build(cid)
        rows, ev = PF.part_margins(M, names, body, T, X, reg, F, cid, subs, sfy, sfu, state)
        for r in rows:
            si = next((i for i, c in enumerate(subs) if all(abs(c.get(k, 0) - v) < 1e-3 for k, v in r["subcase"].items())), None)
            r["subcase_info"] = ({k: v for k, v in info[si].items() if k != "rod_tension_N"} if si is not None else None)
        if cid == "LC2F":
            rows = [r for r in rows if r["part"] in PF.GIMBAL_PARTS]
        if cid != "LC2F":           # envelopes for the hot bound (SF 1.5 / 2.0 cases only)
            if env is None:
                env = {k: np.full(nn, -np.inf, np.float32) for k in ("vm", "vmD", "s1", "s1D")}
                env.update({k: np.full(nn, np.inf, np.float32) for k in ("s3", "s3D")})
            idx = np.nonzero(brittle_nodes)[0]
            for co, S, Sm in ev:
                D = S - co["OP"] * S_OP
                env["vm"] = np.maximum(env["vm"], PF.vm(S).astype(np.float32))
                env["vmD"] = np.maximum(env["vmD"], PF.vm(D).astype(np.float32))
                s1, s3 = PF.principal(S[idx])
                d1, d3 = PF.principal(D[idx])
                env["s1"][idx] = np.maximum(env["s1"][idx], s1)
                env["s3"][idx] = np.minimum(env["s3"][idx], s3)
                env["s1D"][idx] = np.maximum(env["s1D"][idx], d1)
                env["s3D"][idx] = np.minimum(env["s3D"][idx], d3)
        del ev
        # connectors, ICD
        con_env = {}
        for lab, d in SF_.items():
            vals = [sum(c * d[st] for st, c in co.items()) for co in subs]
            k = int(np.argmax(np.abs(vals)))
            con_env[lab] = {"max_abs_N": float(abs(vals[k])), "value_N": float(vals[k]), "si": k}
        icd_env = {}
        for si, co in enumerate(subs):
            tab, tot = PF.icd_table(M, PF.combine_rf(RF, co))
            for rr in tab:
                h = icd_env.setdefault(rr["hole"], {"max_shear_N": 0.0, "max_radial_out_N": -1e9})
                if rr["shear_in_screw_N"] > h["max_shear_N"]:
                    h["max_shear_N"], h["si_shear"] = rr["shear_in_screw_N"], si
                h["max_radial_out_N"] = max(h["max_radial_out_N"], rr["radial_N"])
        rmax = {r: float(max(abs(i_["rod_tension_N"][r]) for i_ in info)) for r in rods}
        cases[cid] = {"SF": [sfy, sfu], "n_subcases": len(subs), "margins": rows, "rod_max_abs_N": rmax,
                      "rod_over_stall": bool(max(rmax.values()) > F_STALL + 1e-6),
                      "connectors_envelope": con_env, "icd_envelope": icd_env,
                      "subcases": info if cid == "GS" else None}
        worst = sorted([r for r in rows if r["set"] == "regular"], key=lambda r: r["MS"])[:4]
        print(f"[s3d {name} {cid}] rods max |F| {rmax}; worst: " + "; ".join(
            f"{r['part']} {r['MS']:+.3f}/{(r['MS_ult'] if r['MS_ult'] is not None else float('nan')):+.3f}" for r in worst), flush=True)
    # TD = TD0 u TDP
    cases["TD"] = {"note": "TD0 (Pc 0) and TDP (Pc_max) merged", "margins": rows_merge(cases["TD0"]["margins"], cases["TDP"]["margins"]),
                   "rod_max_abs_N": {r: max(cases["TD0"]["rod_max_abs_N"][r], cases["TDP"]["rod_max_abs_N"][r]) for r in rods}}
    regm = np.zeros(nn, bool)
    regm[:len(reg)] = reg
    np.savez_compressed(RES / f"s3d_env_{name}.npz", reg=regm, **env)
    out = {"run": name, "state_for_allowables": state, "version": A3.VERSION, "date": time.strftime("%Y-%m-%d"),
           "variant": meta["variant"], "pose_deg": [meta["alpha"], meta["beta"]], "cone_amplitude_deg": amp, "F_d_N": fd,
           "hose_equiv_lateral_g": g_hose, "OP_net_axial_N_per_MPa": op_z, "doc": __doc__.split("usage:")[0].strip(),
           "singular": srep, "cases": cases}
    (RES / f"s3d_{name}.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"[s3d {name}] {time.time() - t0:.1f} s", flush=True)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    opts = dict(x.split("=", 1) for x in a[1:])
    for nm in a[0].split(","):
        run(nm, opts.get("state", "B1_21.65"))
