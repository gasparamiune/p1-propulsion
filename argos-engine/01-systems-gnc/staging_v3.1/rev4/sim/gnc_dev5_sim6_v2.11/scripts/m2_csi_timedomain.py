"""Time-domain check of the CSI finding in the nonlinear 6-DOF (sim6 v2.2, flexible engine mount).

For the RV-1c baseline flight (A-D, fins, 20 % floor, 3 m/s wind + gusts, sensor noise, 0.1 deg misalignment,
1 mm CG offset) the landing burn is flown with the engine-mount stiffness at the low and high ends of
mechanical.json, rocking damping 0.02 / 0.05, actuator bandwidth at the low/nominal/high end of electronics.json,
with the baseline structural command low-pass + 100 deg/s command slew limit, and without both. Reported: success, touchdown state, the RMS engine-angle
oscillation above 10 Hz during the landing burn (a growing or sustained rocking oscillation shows up here) and
the peak hinge (linkage) torque. Output OUT/csi_timedomain_<SUFFIX>.json
"""
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
I = {n: i for i, n in enumerate(s6.REC_NAMES)}


def hf_rms(x, dt, f_lo=10.0):
    x = x - np.mean(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), dt)
    X[f < f_lo] = 0.0
    return float(np.sqrt(np.mean(np.fft.irfft(X, len(x)) ** 2)))


def main():
    src = R.sources()
    mech, el = src["mech"], src["el"]
    kax = mech["tvc_actuation"]["axis_stiffness_Nm_per_rad"]["v"]
    wr = el["actuators"]["tvc_A"]["dynamics_for_GNC"]["v"]
    wn0 = wr["omega_n_rad_s"]
    cfg0 = R.cfg_of(profile="A-D", fins=True, floor=0.20)
    m, _ = R.size_load(cfg0)
    m *= 1.15
    rows = []
    for lpf in (0.0, 50.0):
        for K in kax:
            for zr in (0.02, 0.05):
                for wa in (wr["omega_n_range_rad_s"][0], wn0, wr["omega_n_range_rad_s"][1]):
                    cfg = R.cfg_of(**dict(cfg0, m_n2o=m, wind=3.0, gust=True, seed=11, rec_dt=0.002, gim_lpf_w=lpf,
                                          gim_cmd_rate=R.DEF["gim_cmd_rate"] if lpf > 0 else 0.0))
                    res, rec, info = R.fly(cfg, disp=dict(rock_K=K, rock_zeta=zr, gim_wn_f=wa / wn0, mis_x=np.radians(0.1),
                                                         cg_x=0.001), nrec=40000)
                    land = rec[(rec[:, I["phase"]] >= 5) & (rec[:, I["F"]] > 30)]
                    hx = hf_rms(np.radians(land[:, I["dgx"]]), 0.002) if len(land) > 64 else float("nan")
                    hy = hf_rms(np.radians(land[:, I["dgy"]]), 0.002) if len(land) > 64 else float("nan")
                    r = dict(lpf_rad_s=lpf, K_Nm_rad=K, zeta_rock=zr, w_act=wa, success=R.success(res),
                             td_vz=float(res["td_vz"]), td_vh=float(res["td_vh"]), td_tilt=float(res["td_tilt"]),
                             td_rate=float(res["td_rate"]), max_gim_deg=float(res["max_gim"]), max_hinge_Nm=float(res["max_hinge"]),
                             max_gim_rate_dps=float(res["max_gim_rate"]), hf_rms_deg=float(np.degrees(np.hypot(hx, hy))),
                             crash=float(res["crash"]))
                    rows.append(r)
                    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    out = dict(version=f"m2_csi_timedomain {SUFFIX}", sim=s6.SIM6_VERSION, m_n2o=m, rows=rows,
               note="hf_rms_deg: RMS of the engine angle above 10 Hz during the landing burn (engine-angle oscillation)")
    with open(os.path.join(OUT, f"csi_timedomain_{SUFFIX}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main()
