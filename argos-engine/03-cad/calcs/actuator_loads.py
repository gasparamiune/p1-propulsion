"""TVC actuator loads and slew rate over the gimbal range -- exact Cardan kinematics of the as-built linkage
(calcs/actuator_loads.py v1, 2026-10-12, Mechanical).

Linkage: tvc_kinematics.geometry(P) (servo frames, horn r_h, lever eye r_e, fixed-length pushrod); the horn angle
psi_i(alpha, beta) is solved in closed form for every engine pose R = Rx(alpha) Ry(beta).

Relations used (quasi-static, rigid links, frictionless joints; ASSUMPTIONS listed in the output):
  * Jacobian J = d psi / d(alpha, beta) by central differences of the exact solve (rad/rad).
  * Virtual work: sum tau_i dpsi_i = M_a dalpha + M_b dbeta  ->  generalised gimbal moments M = J^T tau.
  * Pushrod force F_i = tau_i / lambda_i with lambda_i = |((P_h - C) x e_rod) . e_shaft| (exact moment arm).
  * Servo speed: linear torque-speed line omega = omega_nl (1 - tau/tau_stall) (shape ASSUMED by Electronics,
    electronics.json v1 torque_speed_model); a servo whose load aids the motion is capped at omega_nl.
  * Slew rate along a cone direction phi from tilt theta outward: (alpha, beta)(theta) = cone_to_ab(theta, phi);
    psi_dot = J d(alpha,beta)/dtheta theta_dot; hinge load L opposes the motion, servo torques tau = L J^-T u.

Load cases written for the FEA (04-fea/src/loadcases.py reads the JSON):
  GS  both servos at 8.4 V stall pushing together (all four sign combinations), anywhere inside the 7 deg cone and
      at the 8 deg stop: max engine moment |M|, max rod force, horn/lever-stud loads.
  SR  servo runaway into the 8 deg conical stop: stalled servo(s) at the stop pose; bumper reaction = J^T tau.
Design values = max(lead 2026-10-12 numbers, these as-built values) -- the lead's numbers were computed by
Electronics for r_h 10 / r_e 48 (n 4.8) and are kept as a floor.
"""
from __future__ import annotations
import json, math, sys, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import config
import tvc_kinematics as tk

LEAD = {"M_engine_GS_Nm": 35.3, "F_rod_centre_N": 441.0, "F_rod_7deg_N": 552.0, "F_rod_stop_N": 609.0,
        "src": "lead decision 2026-10-12 (Electronics tvc_slew_check_v1, r_h 10 / r_e 48, n 4.8, 8.4 V stall both servos)"}
# Electronics tvc_slew_check_v1 servo points (Ts N m, w_nl deg/s) -- Savox SB-2292SG, datasheet 6.0/7.4/8.4 V + their interpolation
SERVO = {"6.6": (2.54, 764.0), "7.4": (3.04, 857.0), "7.6": (3.31, 897.5), "7.8": (3.59, 938.0), "8.0": (3.86, 984.0), "8.4": (4.413, 1091.0)}
SERVO_SRC = "electronics.json v1 (stall 2.157/3.04/4.413 N m at 6.0/7.4/8.4 V; no-load 706/857/1091 deg/s) + Electronics tvc_slew_check_v1 interpolation (6.6/7.8/8.0 V); 7.6 V = mean of 7.4/7.8"
L_SLEW = 3.19     # N m: Electronics' non-inertial hinge load (tvc_slew_check_v1 'slew load ... non-inertial terms summed')
L_GNC = {"p99": 15.6, "max": 19.5}   # N m: GNC sim6 v2.3 mount torque (lead 2026-10-12)


def jac(g, a, b, h=1e-3):
    J = np.zeros((2, 2))
    for j, (da, db) in enumerate([(h, 0.0), (0.0, h)]):
        p1 = np.array([r["psi"] for r in tk.pose_all(g, a + da, b + db)])
        p0 = np.array([r["psi"] for r in tk.pose_all(g, a - da, b - db)])
        J[:, j] = (p1 - p0) / (2 * h)              # deg/deg = rad/rad
    return J


def lever_arms(g, a, b):
    out = []
    for sv, r in zip(g["servos"], tk.pose_all(g, a, b)):
        e = r["P_l"] - r["P_h"]
        e = e / np.linalg.norm(e)
        lam = abs(float(np.cross(r["P_h"] - sv["C"], e) @ sv["sd"]))       # mm
        out.append({"psi_deg": r["psi"], "lambda_mm": lam, "rod_tilt_deg": r["rod_tilt_deg"]})
    return out


def rate_along(g, theta, phi, Ts, wnl, L):
    """Max outward tilt rate (deg/s) at cone angle theta (deg) in direction phi (deg)."""
    h = 0.01
    a0, b0 = tk.cone_to_ab(theta, phi)
    a1, b1 = tk.cone_to_ab(theta + h, phi)
    dab = np.array([a1 - a0, b1 - b0]) / h               # d(alpha,beta)/dtheta (deg/deg)
    J = jac(g, a0, b0)
    dpsi = J @ dab                                        # servo deg per engine deg
    u = dab / np.linalg.norm(dab)
    try:
        tau = L * np.linalg.solve(J.T, u)                 # servo torques that balance a load L opposing the motion
    except np.linalg.LinAlgError:
        return float("nan"), dpsi, None
    s = []
    for i in range(2):
        if abs(dpsi[i]) < 1e-9:
            continue
        load = tau[i] * np.sign(dpsi[i])                  # > 0: servo pushes in its direction of motion
        w = wnl * (1.0 - max(load, 0.0) / Ts)
        s.append(w / abs(dpsi[i]))
    return (min(s) if s else float("inf")), dpsi, tau


def run(P=None):
    if P is None:
        P, _ = config.build()
    g = tk.geometry(P)
    cmd, stop = P["gimbal_range_deg"]["v"], P["gimbal_stop_deg"]["v"]
    out = {"id": "ENG-TVC-ACTUATOR-LOADS", "version": "v1", "date": "2026-10-12", "owner": "mechanical",
           "linkage": {"r_h_mm": round(g["r_h"], 3), "r_e_mm": round(g["r_e"], 3), "n": round(g["n"], 3), "L_pushrod_mm": round(g["L_pr"], 2),
                       "u_eye_mm": round(g["u_eye"], 3), "t_eye_mm": round(g["t_eye"], 3), "lever_phi_deg": P["tvc_lever_phi_deg"]["v"],
                       "src": "tvc_kinematics.geometry(P), CAD v3.3 config " + config.CONFIG_VERSION},
           "assumptions": ["rigid links, frictionless joints, quasi-static (inertia of the servo rotor and linkage excluded from the rate)",
                           "linear torque-speed line (Electronics ASSUMED shape); aiding load capped at no-load speed",
                           f"slew hinge load {L_SLEW} N m opposing the motion (Electronics' non-inertial sum); GNC p99/max mount torque used for holding checks",
                           "servo stall torques " + SERVO_SRC]}
    # ---------------------------------------------------------------- range scan: horn angles, lever arms, Jacobian
    dirs = np.arange(0.0, 360.0, 5.0)
    scan = {}
    for name, th in (("centre", 0.0), ("cmd_7deg", cmd), ("stop_8deg", stop)):
        lam_min, psi_ext, Mmax, Fmax = [1e9, 1e9], [[1e9, -1e9], [1e9, -1e9]], 0.0, [0.0, 0.0]
        worst = None
        for ph in (dirs if th > 0 else [0.0]):
            a, b = tk.cone_to_ab(th, ph)
            la = lever_arms(g, a, b)
            J = jac(g, a, b)
            for i in range(2):
                lam_min[i] = min(lam_min[i], la[i]["lambda_mm"])
                psi_ext[i] = [min(psi_ext[i][0], la[i]["psi_deg"]), max(psi_ext[i][1], la[i]["psi_deg"])]
            Ts = SERVO["8.4"][0]
            for s1 in (1, -1):
                for s2 in (1, -1):
                    tau = np.array([s1 * Ts, s2 * Ts])
                    M = J.T @ tau
                    if np.linalg.norm(M) > Mmax:
                        Mmax, worst = float(np.linalg.norm(M)), {"dir_deg": float(ph), "signs": [s1, s2], "M_Nm": [round(float(x), 2) for x in M]}
            for i in range(2):
                Fmax[i] = max(Fmax[i], Ts / (la[i]["lambda_mm"] * 1e-3))
        scan[name] = {"theta_deg": th, "psi_range_deg": [[round(x, 2) for x in p] for p in psi_ext],
                      "lambda_min_mm": [round(x, 3) for x in lam_min],
                      "GS_8V4_both_stall": {"M_engine_max_Nm": round(Mmax, 2), "worst": worst,
                                            "F_rod_max_N": [round(x, 1) for x in Fmax]}}
    out["range_scan"] = scan
    # ---------------------------------------------------------------- SR: runaway into the stop (single servo stalled, other holding)
    sr = {"note": "servo runaway at 8.4 V stall drives the engine onto the 8 deg conical stop; rod force = Ts / lambda at the stop pose; "
                  "the stop reaction carries J^T tau (both servos stalled in the worst sign combination is the GS-at-stop bound)",
          "F_rod_max_N": scan["stop_8deg"]["GS_8V4_both_stall"]["F_rod_max_N"],
          "M_engine_at_stop_max_Nm": scan["stop_8deg"]["GS_8V4_both_stall"]["M_engine_max_Nm"]}
    out["SR"] = sr
    # ---------------------------------------------------------------- design loads = max(lead, as-built)
    asb = {"M_engine_GS_Nm": max(scan["cmd_7deg"]["GS_8V4_both_stall"]["M_engine_max_Nm"], scan["centre"]["GS_8V4_both_stall"]["M_engine_max_Nm"]),
           "F_rod_centre_N": max(scan["centre"]["GS_8V4_both_stall"]["F_rod_max_N"]),
           "F_rod_7deg_N": max(scan["cmd_7deg"]["GS_8V4_both_stall"]["F_rod_max_N"]),
           "F_rod_stop_N": max(scan["stop_8deg"]["GS_8V4_both_stall"]["F_rod_max_N"]),
           "M_engine_stop_Nm": scan["stop_8deg"]["GS_8V4_both_stall"]["M_engine_max_Nm"]}
    des = {k: max(LEAD.get(k, 0.0), asb[k]) for k in asb}
    des["governs"] = {k: ("lead" if LEAD.get(k, 0.0) >= asb[k] else "as-built") for k in asb}
    out["design_loads"] = {"as_built": {k: round(v, 2) for k, v in asb.items()}, "lead": LEAD,
                           "design": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in des.items()},
                           "tag": "DERIVED: max(lead 2026-10-12, as-built exact kinematics at 8.4 V stall); SF per charter ENG-10 (1.5 yield / 2.0 ult) applied in hand_calcs/FEA"}
    # ---------------------------------------------------------------- holding: servo torque needed for the GNC mount torque
    hold = {}
    for name, th in (("centre", 0.0), ("cmd_7deg", cmd)):
        worst_tau = 0.0
        for ph in (dirs if th > 0 else [0.0]):
            a, b = tk.cone_to_ab(th, ph)
            J = jac(g, a, b)
            for ang in np.arange(0, 360, 15):
                u = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
                tau = np.linalg.solve(J.T, L_GNC["p99"] * u)
                worst_tau = max(worst_tau, float(np.max(np.abs(tau))))
        hold[name] = {"servo_torque_for_GNC_p99_15.6Nm_worst_Nm": round(worst_tau, 3),
                      "margin_vs_stall": {v: round(SERVO[v][0] / worst_tau, 2) for v in ("7.4", "8.4")}}
    out["holding_GNC_p99"] = hold
    # ---------------------------------------------------------------- rate vs angle
    rate = {"load_Nm": L_SLEW, "rows": []}
    worst_summary = {}
    for V, (Ts, wnl) in SERVO.items():
        wmin, wdir = 1e9, None
        for th in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0):
            row_alpha = rate_along(g, th, 90.0, Ts, wnl, L_SLEW)[0]     # tilt toward +Y = pure alpha (outer axis)
            row_beta = rate_along(g, th, 0.0, Ts, wnl, L_SLEW)[0]       # tilt toward +X = pure beta (inner axis)
            per_dir = [(rate_along(g, th, ph, Ts, wnl, L_SLEW)[0], ph) for ph in dirs]
            w, ph = min(per_dir)
            nl = min(rate_along(g, th, p, Ts, wnl, 0.0)[0] for p in dirs)
            rate["rows"].append({"V": float(V), "theta_deg": th, "alpha_dps": round(row_alpha, 1), "beta_dps": round(row_beta, 1),
                                 "worst_dps": round(w, 1), "worst_dir_deg": ph, "worst_noload_dps": round(nl, 1)})
            if w < wmin:
                wmin, wdir = w, (th, ph)
        worst_summary[V] = {"min_loaded_rate_dps_over_7deg_cone": round(wmin, 1), "at_theta_dir_deg": wdir,
                            "meets_ENG07_100dps": bool(wmin >= 100.0)}
    rate["summary"] = worst_summary
    out["rate_vs_angle"] = rate
    out["travel"] = tk.travel_table(g, stop_deg=stop, cmd_deg=cmd)
    return out


def write_csv(out, path):
    rows = out["rate_vs_angle"]["rows"]
    with open(path, "w") as f:
        f.write("# TVC slew rate vs gimbal angle, as-built CAD v3.3 linkage (calcs/actuator_loads.py v1); "
                f"r_h {out['linkage']['r_h_mm']} mm, r_e {out['linkage']['r_e_mm']} mm, n {out['linkage']['n']}; load {L_SLEW} N m\n")
        f.write("V_servo,theta_deg,alpha_dps,beta_dps,worst_dps,worst_dir_deg,worst_noload_dps\n")
        for r in rows:
            f.write(f"{r['V']},{r['theta_deg']},{r['alpha_dps']},{r['beta_dps']},{r['worst_dps']},{r['worst_dir_deg']},{r['worst_noload_dps']}\n")


if __name__ == "__main__":
    o = run()
    dst = HERE / "actuator_loads_v1.json"
    dst.write_text(json.dumps(o, indent=1, default=float))
    write_csv(o, HERE / "tvc_rate_vs_angle_mech_v1.csv")
    print(json.dumps({k: o[k] for k in ("linkage", "design_loads", "holding_GNC_p99", "travel")}, indent=1, default=float))
    print(json.dumps(o["range_scan"], indent=1, default=float))
    print(json.dumps(o["rate_vs_angle"]["summary"], indent=1))
