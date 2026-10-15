"""m2_csi_v3_td v1.1 (2026-10-12): time-domain cross-check of the ENG-07d linear CSI result (m2_csi_v3) in the nonlinear
6-DOF (sim6 v2.6 dev): landing burn of the lead baseline (A-D, N2O 2.00 kg, no RCS) with the torque/speed-limited servo
pair (act_model 1, n 4.8, 7.6 V fixed plug voltage), the engine-mount stiffness at Mechanical's FEA corners (structure in
series with the servo, data/relay/lead_relay_mech_fea_k_20261012.json), J_int 0 / 1.6e-3 kg m2, mount damping 0.02 / 0.05,
low-pass 50 rad/s with and without the ENG-07d notch (ECU default Q 1, -12 dB; env GNC_TD_NOTCH) centred on the build's
rocking mode (as B-TVC-1 would measure it).
3 m/s wind + gusts, sensor noise, 0.1 deg misalignment, 1 mm CG offset (as m2_csi_timedomain v2).
Reported: success, touchdown state, RMS of the engine angle above 10 Hz in the landing burn (a growing or sustained
rocking oscillation shows up here), peak hinge moment and gimbal rate.
v1.1: every corner is flown twice, with the v2.5 control law (what the linear model represents) and with the proposed
v2.6 flight software (command tracker 2000 deg/s2 + attitude reference governor 40 deg/s, lift-ramp shutdown with the
72 % pre-MECO throttle-down, relight start rule 20 %); the tracker's acceleration limit bounds any rocking oscillation
in the command, which the linear model does not represent.
The wet engine inertia about the pivot is set to the CAD v3.3 value relayed with the FEA (run6 v2.6 eng_I_pivot_wet), as
in m2_csi_v3; the notch is centred on the 6-DOF's own landing-burn mode.
Env: GNC_OUT (default out/csi_v3), GNC_CSI_TAG (default fea). Output OUT/csi_v3_td_<TAG>.json"""
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/csi_v3")
TAG = os.environ.get("GNC_CSI_TAG", "fea")
NQ, ND = [float(x) for x in os.environ.get("GNC_TD_NOTCH", "1,-12").split(",")]   # ECU firmware default Q and depth
RELAY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "relay",
                     "lead_relay_mech_fea_k_20261012.json")
I = {n: i for i, n in enumerate(s6.REC_NAMES)}


def hf_rms(x, dt, f_lo=10.0):
    x = x - np.mean(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), dt)
    X[f < f_lo] = 0.0
    return float(np.sqrt(np.mean(np.fft.irfft(X, len(x)) ** 2)))


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    relay = json.load(open(RELAY))
    n = relay["n_linkage"]["v"]
    Kc = relay["K_series_centre_Nm_per_rad"]["v"]
    Ks = sorted(set([min(Kc["beta"]), min(Kc["alpha"]), max(Kc["alpha"])]))
    J = relay["J_int_servo_output_kgm2"]["v"]["central"]
    mech = R.sources()["mech"]
    n_m = mech["tvc_actuation"]["gear_ratio_n"]["v"]
    fk = (n / n_m) ** 2
    base = dict(profile="A-D", fins=True, floor=0.20, rcs=False, m_n2o=2.00, act_model=1, servo_V=7.6, act_n=n,
                wind=3.0, gust=True, seed=11, rec_dt=0.002, eng_I_pivot_wet=relay["I_pivot_wet_kgm2"]["v"])
    FSW = {"v2.5": {}, "v2.6": dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, toff_model=1, meco_td=0.72, relight_start=0.20)}
    rows = []
    for fsw, Jv in [(a, b) for a in FSW for b in (0.0, J)]:
        fo = FSW[fsw]
        for K in Ks:
            for zr in (0.02, 0.05):
                for nt in ("lpf", "lpf+notch"):
                    cfg = R.cfg_of(**dict(base, act_Jint=Jv, **fo))
                    par, apar, comp, mp, tab, info = R.build(cfg, dict(R.DISP, rock_K=K / fk, rock_zeta=zr))
                    Ip = None
                    o = np.zeros(8)
                    s6.massprops(mp, 0.3, 0.0, par[s6.P_rho_l_nom], par[s6.P_m_fuel0] * 0.75, o)
                    m_, zcg, It, Ir, me, ze, Ie, Dp = o
                    le = mp[15] - ze
                    Ip = Ie + me * le * le
                    f_r = float(np.sqrt(K / (Ip + Jv * n * n)) / (2 * np.pi))
                    if nt == "lpf+notch":
                        cfg = R.cfg_of(**dict(base, act_Jint=Jv, gim_notch_f=f_r, gim_notch_q=NQ, gim_notch_db=ND, **fo))
                    res, rec, info = R.fly(cfg, disp=dict(rock_K=K / fk, rock_zeta=zr, mis_x=np.radians(0.1), cg_x=0.001),
                                           nrec=40000)
                    land = rec[(rec[:, I["phase"]] >= 5) & (rec[:, I["F"]] > 30)]
                    hx = hf_rms(np.radians(land[:, I["dgx"]]), 0.002) if len(land) > 64 else float("nan")
                    hy = hf_rms(np.radians(land[:, I["dgy"]]), 0.002) if len(land) > 64 else float("nan")
                    r = dict(fsw=fsw, J_int=Jv, K_Nm_rad=K, zeta_rock=zr, filter=nt, f_rock_6dof_Hz=f_r, success=R.success(res),
                             td_vz=float(res["td_vz"]), td_vh=float(res["td_vh"]), td_tilt=float(res["td_tilt"]),
                             td_rate=float(res["td_rate"]), max_gim_deg=float(res["max_gim"]), max_hinge_Nm=float(res["max_hinge"]),
                             max_gim_rate_dps=float(res["max_gim_rate"]), hf_rms_deg=float(np.degrees(np.hypot(hx, hy))),
                             crash=float(res["crash"]), act_sat_max_dur_s=float(res["act_sat_max_dur"]))
                    rows.append(r)
                    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, f"({time.time() - t0:.0f}s)",
                          flush=True)
    out = dict(version=f"m2_csi_v3_td v1.1 {TAG}", sim=s6.SIM6_VERSION, relay=RELAY, rows=rows,
               note=f"hf_rms_deg: RMS of the engine angle above 10 Hz during the landing burn; notch Q {NQ:g}, {ND:g} dB centred on the 6-DOF landing-burn mode")
    with open(os.path.join(OUT, f"csi_v3_td_{TAG}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main()
