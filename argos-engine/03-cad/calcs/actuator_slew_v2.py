"""ENG-07 gimbal slew at the mechanical.json v2 hinge load - exact linkage kinematics, every pose and motion direction at 7 deg
(03-cad/src/calcs, v2, 2026-10-13, Mechanical).

Asked (independent GNC review REV-GNC-1 / coordinator 2026-10-13; gnc.json requests): recompute the engine slew rate with the
v2 non-inertial hinge terms (sum 4.867 N m incl. the hose upper term 2.136 N m; 5.175 N m with the hose at the 20 N m/rad routing
limit) instead of the v1 sum 3.19 N m, at the 7.4 V nominal plug and the 6.6 V case, worst vector direction at 7 deg.

Model (v1 actuator_loads.py method, extended):
  * linkage: tvc_kinematics.geometry(P) (servo frames, horn r_h, lever eye r_e, fixed pushrods; identical in v3.3 and v3.4: the
    V5c stiffening changes the lever section, not the eye points); horn angles psi_i(alpha, beta) from the closed-form solve,
    Jacobian J = d psi / d(alpha, beta) by central differences (rad/rad).
  * slew metric = angular speed of the thrust axis |e_dot| (exact: |e_dot|^2 = alpha_dot^2 cos^2 beta + beta_dot^2 for
    R = Rx(alpha) Ry(beta)); for radial motion it equals theta_dot (the v1 metric).
  * at a pose on the 7 deg cone (azimuth phi of the tilt) the motion direction chi is scanned in the tangent plane
    (chi 0 = outward radial, 90 = tangential counter-clockwise, 180 = inward); the hinge load is a moment of magnitude L
    opposing the tilting angular velocity (e x e_dot); generalised forces Q = (M . e_x, M . Rx(alpha) e_y); servo torques
    from J^T tau = -Q.
  * servo: linear torque-speed line omega = omega_nl (1 - tau/T_stall) (Electronics ASSUMED shape, electronics.json v1);
    a servo whose load aids its motion is capped at omega_nl (as v1).  Quasi-static: rotor and linkage inertia are not in the
    rate (they are GNC's 6-DOF terms); joints frictionless (pushrod-joint friction acts on the servo: listed as an unknown).
Loads (N m, opposing the motion):
  L_v1 3.19 (Electronics v1 non-inertial sum, the published 111.2 deg/s basis), L_v2 4.867 (mechanical.json v2 terms: vehicle
  angular acceleration 0.607 + axial 0.0158 + lateral 0.0196 + hose radial L0.40 upper 2.136 + bearing seals 0.04 + thrust
  misalignment 0.758 + nozzle side load 1.291), L_hose20 5.175 (hose at the 20 N m/rad routing limit x 7 deg = 2.443),
  L_O3b 3.683 (v3.4 O3b coil: K <= 7.79 N m/rad at EI 0.5 ASSUMED, hose_routing_trade_v2 -> 0.952 N m at 7 deg).
Servo points (stall N m, no-load deg/s): Electronics tvc_slew_check_v1 / electronics.json v1, as actuator_loads v1.
Output: calcs/actuator_slew_v2.json + calcs/tvc_rate_vs_angle_mech_v2.csv.
"""
from __future__ import annotations
import json, math, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import config
import tvc_kinematics as tk
from actuator_loads import SERVO, SERVO_SRC, jac

OUT = HERE / "actuator_slew_v2.json"
CSV = HERE / "tvc_rate_vs_angle_mech_v2.csv"
TERMS_V2 = {"vehicle_angular_accel": 0.607, "axial_accel": 0.0158, "lateral_accel": 0.0196, "hose_radial_L0.40_upper": 2.136,
            "bearing_seal_friction": 0.04, "thrust_misalignment": 0.758, "nozzle_side_load_floor": 1.291}
TH7 = math.radians(7.0)
HOSE_20 = 20.0 * TH7
HOSE_O3B = 7.79 * TH7
L_V2 = sum(TERMS_V2.values())
LOADS = {"L_v1_3.19": 3.19, "L_v2_terms": L_V2, "L_v2_hose_at_20Nm_rad": L_V2 - TERMS_V2["hose_radial_L0.40_upper"] + HOSE_20,
         "L_v34_O3b_coil_EI0.5": L_V2 - TERMS_V2["hose_radial_L0.40_upper"] + HOSE_O3B, "no_load": 0.0}
VOLTS = ("6.6", "7.4", "8.4")


def frame(a_deg, b_deg):
    a, b = math.radians(a_deg), math.radians(b_deg)
    e = np.array([math.sin(b), -math.sin(a) * math.cos(b), math.cos(a) * math.cos(b)])
    dEa = np.array([0.0, -math.cos(a) * math.cos(b), -math.sin(a) * math.cos(b)])
    dEb = np.array([math.cos(b), math.sin(a) * math.sin(b), -math.cos(a) * math.sin(b)])
    ex, ey2 = np.array([1.0, 0.0, 0.0]), np.array([0.0, math.cos(a), math.sin(a)])
    return e, np.column_stack([dEa, dEb]), ex, ey2


def rates_at_pose(g, theta_deg, phi_deg, chis_deg, Ts, wnl, L):
    """Max |e_dot| (deg/s) for every motion direction chi at the pose (theta, phi); also the limiting servo per chi."""
    a, b = tk.cone_to_ab(theta_deg, phi_deg)
    J = jac(g, a, b)
    e, A, ex, ey2 = frame(a, b)
    ph = math.radians(phi_deg)
    th = math.radians(theta_deg)
    h_ = np.array([math.cos(ph), math.sin(ph), 0.0])
    e_t = -math.sin(th) * np.array([0, 0, 1.0]) + math.cos(th) * h_          # outward radial (along the great circle)
    e_p = np.array([-math.sin(ph), math.cos(ph), 0.0])                        # tangential (counter-clockwise)
    out_w, out_lim = [], []
    Apinv = np.linalg.pinv(A)
    for chi in chis_deg:
        c = math.radians(chi)
        ed = math.cos(c) * e_t + math.sin(c) * e_p                            # unit |e_dot| (1 rad/s)
        qd = Apinv @ ed                                                       # (alpha_dot, beta_dot) rad/s per rad/s of slew
        psid = J @ qd                                                         # servo rad/s per rad/s of slew
        wperp = np.cross(e, ed)                                               # tilting angular velocity direction (unit)
        M = -L * wperp
        Q = np.array([M @ ex, M @ ey2])
        tau = np.linalg.solve(J.T, -Q)
        lim = []
        for i in range(2):
            if abs(psid[i]) < 1e-12:
                lim.append(float("inf"))
                continue
            drive = tau[i] * math.copysign(1.0, psid[i])                    # > 0: servo works against the load
            w = wnl * (1.0 - max(drive, 0.0) / Ts)                            # deg/s at the servo
            lim.append(w / abs(psid[i]))                                      # deg/s of slew (psid is rad/rad)
        k = int(np.argmin(lim))
        out_w.append(lim[k])
        out_lim.append(k + 1)
    return np.array(out_w), np.array(out_lim), J


def main():
    t0 = time.time()
    P, _ = config.build()
    g = tk.geometry(P)
    phis = np.arange(0.0, 360.0, 1.0)
    chis = np.arange(0.0, 360.0, 1.0)
    res = {"id": "ENG-07-slew-v2", "version": "v2", "date": "2026-10-13", "owner": "mechanical",
           "script": "03-cad/src/calcs/actuator_slew_v2.py", "supersedes": "actuator_loads_v1.json rate_vs_angle (kept: v1 load 3.19 N m)",
           "method": __doc__.split("\n\n")[1], "loads_Nm": {k: round(v, 4) for k, v in LOADS.items()}, "terms_v2_Nm": TERMS_V2,
           "servo_points": {v: {"stall_Nm": SERVO[v][0], "noload_dps": SERVO[v][1]} for v in VOLTS}, "servo_src": SERVO_SRC,
           "linkage": {"r_h_mm": round(g["r_h"], 3), "r_e_mm": round(g["r_e"], 3), "n": round(g["n"], 3), "L_pushrod_mm": round(g["L_pr"], 2),
                       "lever_phi_deg": P["tvc_lever_phi_deg"]["v"]}, "cases": {}}
    # Jacobian table at 7 deg (published for GNC / Electronics)
    jt = []
    for ph in np.arange(0.0, 360.0, 15.0):
        a, b = tk.cone_to_ab(7.0, ph)
        J = jac(g, a, b)
        psi = [r["psi"] for r in tk.pose_all(g, a, b)]
        jt.append({"phi_deg": float(ph), "alpha_deg": round(a, 4), "beta_deg": round(b, 4), "psi_deg": [round(x, 3) for x in psi],
                   "J_rad_per_rad": [[round(float(x), 5) for x in row] for row in J]})
    a0, b0 = 0.0, 0.0
    J0 = jac(g, a0, b0)
    res["jacobian"] = {"centre": [[round(float(x), 5) for x in row] for row in J0], "at_7deg_every_15deg": jt,
                       "note": "psi_i servo horn angle (deg), J = d psi_i / d(alpha, beta), engine pose R = Rx(alpha) Ry(beta), tilt azimuth phi (axis toward phi)"}
    csv_rows = []
    for V in VOLTS:
        Ts, wnl = SERVO[V]
        for lname, L in LOADS.items():
            worst_all = (1e9, None, None, None)
            worst_out = (1e9, None, None)
            worst_in = (1e9, None)
            worst_tan = (1e9, None)
            for ph in phis:
                w, lim, _ = rates_at_pose(g, 7.0, ph, chis, Ts, wnl, L)
                k = int(np.argmin(w))
                if w[k] < worst_all[0]:
                    worst_all = (float(w[k]), float(ph), float(chis[k]), int(lim[k]))
                if w[0] < worst_out[0]:
                    worst_out = (float(w[0]), float(ph), int(lim[0]))
                if w[180] < worst_in[0]:
                    worst_in = (float(w[180]), float(ph))
                wt = min(w[90], w[270])
                if wt < worst_tan[0]:
                    worst_tan = (float(wt), float(ph))
            wc, limc, _ = rates_at_pose(g, 0.0, 0.0, chis, Ts, wnl, L)
            kc = int(np.argmin(wc))
            case = {"V": float(V), "load_Nm": round(L, 4),
                    "worst_any_motion_at_7deg": {"dps": round(worst_all[0], 2), "pose_phi_deg": worst_all[1], "motion_chi_deg": worst_all[2],
                                                  "limiting_servo": worst_all[3]},
                    "worst_outward_at_7deg": {"dps": round(worst_out[0], 2), "pose_phi_deg": worst_out[1], "limiting_servo": worst_out[2]},
                    "worst_inward_at_7deg": {"dps": round(worst_in[0], 2), "pose_phi_deg": worst_in[1]},
                    "worst_tangential_at_7deg": {"dps": round(worst_tan[0], 2), "pose_phi_deg": worst_tan[1]},
                    "worst_at_centre": {"dps": round(float(wc[kc]), 2), "motion_chi_deg": float(chis[kc])},
                    "ENG07_100dps": {"outward": bool(worst_out[0] >= 100.0), "any_direction": bool(worst_all[0] >= 100.0)}}
            res["cases"][f"{V}V|{lname}"] = case
            print(V, lname, json.dumps({k: v for k, v in case.items() if k.startswith("worst")}))
            if lname in ("L_v2_terms", "L_v2_hose_at_20Nm_rad", "L_v34_O3b_coil_EI0.5", "no_load"):
                for th in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0):
                    wmin, arg = 1e9, None
                    for ph in (phis[::5] if th > 0 else [0.0]):
                        w, lim, _ = rates_at_pose(g, th, ph, chis[::5], Ts, wnl, L)
                        k = int(np.argmin(w))
                        if w[k] < wmin:
                            wmin, arg = float(w[k]), (float(ph), float(chis[::5][k]))
                    wo = min(rates_at_pose(g, th, ph, [0.0], Ts, wnl, L)[0][0] for ph in (phis[::5] if th > 0 else [0.0]))
                    csv_rows.append((V, lname, round(L, 3), th, round(wo, 2), round(wmin, 2), arg[0], arg[1]))
    # hose stiffness at which the 7.4 V worst outward / any-direction rate equals 100 deg/s
    Ts, wnl = SERVO["7.4"]
    base = L_V2 - TERMS_V2["hose_radial_L0.40_upper"]
    def worst(L, outward):
        m = 1e9
        for ph in phis[::2]:
            w, _, _ = rates_at_pose(g, 7.0, ph, ([0.0] if outward else chis[::2]), Ts, wnl, L)
            m = min(m, float(w.min()))
        return m
    be = {}
    for outward in (True, False):
        lo, hi = 0.0, 40.0
        if worst(base + lo * TH7, outward) < 100.0:
            be["outward" if outward else "any_direction"] = "below 100 deg/s even with a zero-stiffness hose"
            continue
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            if worst(base + mid * TH7, outward) >= 100.0:
                lo = mid
            else:
                hi = mid
        be["outward" if outward else "any_direction"] = round(lo, 2)
    res["hose_K_breakeven_7V4_Nm_per_rad"] = {"v": be, "note": "largest hose hinge stiffness (per axis, linear, x 7 deg) with the other v2 terms "
                                                             "for which the 7.4 V worst rate at 7 deg is >= 100 deg/s (2-deg scan)"}
    with open(CSV, "w") as f:
        f.write("# ENG-07 slew vs gimbal angle, exact linkage kinematics (calcs/actuator_slew_v2.py); worst over pose azimuth (5 deg) and "
                "motion direction (5 deg); quasi-static, linear torque-speed line\n")
        f.write("V_servo,load_case,load_Nm,theta_deg,worst_outward_dps,worst_any_direction_dps,at_phi_deg,at_chi_deg\n")
        for r in csv_rows:
            f.write(",".join(str(x) for x in r) + "\n")
    res["csv"] = "03-cad/src/calcs/tvc_rate_vs_angle_mech_v2.csv"
    res["unknowns"] = ["servo torque-speed line shape (ASSUMED linear) and the plug-to-servo voltage drop (Electronics; values are at the servo)",
                       "pushrod spherical-joint friction (acts on the servo torque, ~mu F r_ball, not in this rate)",
                       "rotor/linkage inertia (GNC 6-DOF); B-TVC-1 measures slew and acceleration at 6.6 / 7.4 V under the v2 load"]
    res["t_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res["hose_K_breakeven_7V4_Nm_per_rad"]), res["t_s"])


if __name__ == "__main__":
    main()
