"""m2_n_sweep v1 (2026-10-12): linkage-ratio sweep n = 4.8-6.0 for the lead (low priority, CSI-only, no Monte Carlo).
For each n: worst-direction engine slew at 7 deg and 7.4 V under the 3.19 N m hinge load, and the minimum structure +
rod stiffness per axis that puts the lumped rocking mode at the ENG-07d frequency targets (22 Hz = notch tuned within
+/-5 % on the B-TVC-1 measured mode; 25 Hz = notch +/-15 % or low-pass only with mode damping >= 0.05), at J_int
1.6e-3 kg m2 (Electronics central) and servo output stiffness 58 / 116 / 174 N m/rad (electronics.json ASSUMED range).

Model (stated hypotheses):
  * stiffness and rotor inertia on the engine axis scale with n^2 (two servos, Cardan mixing: per-axis factor n^2;
    reproduces mechanical.json v2 smin_T/smax_T at n 4.8), structure in series, rotor lumped on the engine side;
  * the frequency targets are properties of the loop (m2_csi_v3 ftarget: margins depend on K, I_piv and J only through
    the rocking frequency and damping), so they are taken as independent of n;
  * slew: servo on its linear torque-speed line at 7.4 V (electronics.json DATASHEET), one servo carrying the worst
    direction (mixing n / sqrt(2) per servo per axis), effective ratio at 7 deg n_e = n k(psi): k fitted so that n 4.8
    reproduces mechanical.json v2 (111.2 deg/s at 7.4 V), with the horn angle growing as sin(psi) proportional to n
    (psi 37.39 deg at n 4.8 from mechanical.json); the crank and rod-tilt factor beyond 1/cos(psi) is held at its
    n 4.8 value. This is an extrapolation of the as-built kinematics; Mechanical's exact kinematics supersede it.
Output: <GNC_OUT>/n_sweep.json (default out/n_sweep)."""
import json
import os
import sys
import numpy as np
from scipy.optimize import brentq

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/n_sweep")
RELAY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "relay",
                     "lead_relay_mech_fea_k_20261012.json")
F_TARGETS = {"22 Hz (notch tuned +/-5 %)": 22.0, "25 Hz (notch +/-15 % or LPF zeta >= 0.05)": 25.0}   # GNC ftarget (SIM)


def main():
    src = R.sources()
    mech, el = src["mech"], src["el"]
    if str(mech.get("version")) == "v1":
        raise SystemExit("needs mechanical.json >= v2")
    ta = mech["tvc_actuation"]
    n0 = ta["gear_ratio_n"]["v"]
    psi0 = ta["servo_angle_range_deg"]["v"]["cmd_7deg"]["psi_max_deg"][0]
    rate0 = ta["rate_engine_dps_under_3.19Nm"]["v"]["7.4"]["worst_dps"]
    M = 3.19                                                         # mechanical.json load case of the rate table [N m]
    tvc = el["actuators"]["tvc_A"]
    Ts = tvc["stall_torque_Nm"]["v"]["7.4V"]
    wnl = tvc["noload_speed_dps"]["v"]["7.4V"]
    Ks_out = tvc["stiffness"]["v"]["servo_output_Nm_per_rad"]
    Ks_list = [Ks_out[0], 0.5 * (Ks_out[0] + Ks_out[1]), Ks_out[1]]
    J = json.load(open(RELAY))["J_int_servo_output_kgm2"]["v"]["central"]
    I_land = mech["gimballed_mass_properties"]["end_of_max_thrust_case"]["I_pivot_kgm2"]["v"][0][0]

    def rate(n_e):
        return wnl * (1.0 - M / (n_e * Ts)) / n_e

    ne0 = brentq(lambda x: rate(x) - rate0, n0, 6.0 * n0)        # effective ratio at 7 deg reproducing Mechanical
    k_rest = ne0 / (n0 / np.cos(np.radians(psi0)))
    rows = []
    for n in np.round(np.arange(4.8, 6.01, 0.2), 2):
        s_psi = np.sin(np.radians(psi0)) * n / n0
        if s_psi >= 1.0:
            rows.append(dict(n=float(n), note="horn beyond 90 deg at 7 deg")); continue
        psi = np.degrees(np.arcsin(s_psi))
        ne = n / np.cos(np.radians(psi)) * k_rest
        r = dict(n=float(n), psi_7deg_deg=float(psi), n_eff_7deg=float(ne), slew_7deg_7V4_dps=float(rate(ne)),
                 slew_centre_7V4_dps=float(rate(n)), I_eff_landing=float(I_land + J * n * n), K_struct_min={})
        for lab, f in F_TARGETS.items():
            Kt = (2 * np.pi * f) ** 2 * (I_land + J * n * n)
            d = {}
            for ks in Ks_list:
                kse = ks * n * n
                d[f"K_s_{ks:g}"] = None if Kt >= kse else float(1.0 / (1.0 / Kt - 1.0 / kse))
            d["K_total_req"] = float(Kt)
            d["K_s_min_rigid_structure"] = float(Kt / (n * n))
            r["K_struct_min"][lab] = d
        rows.append(r)
        k22 = r["K_struct_min"]["22 Hz (notch tuned +/-5 %)"]; k25 = r["K_struct_min"]["25 Hz (notch +/-15 % or LPF zeta >= 0.05)"]
        fmt = lambda v: "  none" if v is None else f"{v:6.0f}"  # noqa: E731
        print(f"n {n:4.1f}: psi(7deg) {psi:5.1f} deg, slew 7deg/7.4V {rate(ne):6.1f} deg/s (centre {rate(n):6.1f}) | "
              f"22 Hz K_struct @K_s 58/116/174: {fmt(k22['K_s_58'])} {fmt(k22['K_s_116'])} {fmt(k22['K_s_174'])} "
              f"(K_s rigid {k22['K_s_min_rigid_structure']:.0f}) | 25 Hz: {fmt(k25['K_s_58'])} {fmt(k25['K_s_116'])} "
              f"{fmt(k25['K_s_174'])} (K_s rigid {k25['K_s_min_rigid_structure']:.0f})")
    out = dict(version="m2_n_sweep v1", date="2026-10-12", interfaces={k: (src[k] or {}).get("version") for k in ("mech", "el", "comb")},
               calibration=dict(n0=n0, psi0_deg=psi0, rate0_dps=rate0, n_eff0=float(ne0), k_rest=float(k_rest), M_Nm=M,
                                Ts_7V4=Ts, wnl_7V4=wnl), J_central=J, I_landing=I_land, f_targets=F_TARGETS, rows=rows,
               note="CSI-only, lumped rotor; slew extrapolated from the n 4.8 as-built kinematics (Mechanical supersedes)")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "n_sweep.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main()
