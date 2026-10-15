"""m2_csi_v3_mc v1 (2026-10-12): ENG-07d in the 6-DOF Monte Carlo on Mechanical's FEA axis stiffness (lead request
2026-10-12). The baseline MC draws the engine-axis mount stiffness from the mechanical.json v1 servo-stiffness range
rescaled to n 4.8 (U(1336, 4009) N m/rad); here the bounds are replaced by the FEA envelope (structure in series with
the servo, both axes, centre and alpha +7 deg; data/relay/lead_relay_mech_fea_k_20261012.json), with the same random
numbers (paired with the baseline draws, seed 101). Every case flies the proposed v2.6 flight software (command tracker
2000 deg/s2 + attitude reference governor 40 deg/s, lift-ramp shutdown with the 72 % pre-MECO throttle-down, relight
start rule 20 %) on the torque/speed-limited servo pair at 6.6 V (as-drawn chain), N2O 2.00 kg, no roll RCS.
Notch cases: ECU notch centred on each run's own landing-burn rocking mode times a mistune factor drawn U(1 - w, 1 + w)
from a separate generator (B-TVC-1 measurement error + in-flight shift); Q and depth from env GNC_FK_NOTCH ('Q,depth').
The FEA cases also set the wet engine inertia about the pivot to the CAD v3.3 value relayed with the FEA (0.052 kg m2;
the 6-DOF otherwise uses the mechanical.json v1 mass properties, 0.047 kg m2), as m2_csi_v3 does.
Hypotheses: one stiffness value for both axes per run (the 6-DOF has one rocking K), rotor inertia lumped on the engine
side (conservative), mount damping U(0.02, 0.10) as in the baseline MC.
Env: GNC_FK_CASES (comma list), GNC_OUT (default out/csi_v3_mc), GNC_SUFFIX (default fk), GNC_FK_NOTCH, GNC_FK_MIS_W."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/csi_v3_mc")
os.environ.setdefault("GNC_SUFFIX", "fk")
import m2_mc6 as M  # noqa: E402
from gncsim import sim6 as s6  # noqa: E402

RELAY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "relay",
                     "lead_relay_mech_fea_k_20261012.json")
relay = json.load(open(RELAY))
_kc = relay["K_series_centre_Nm_per_rad"]["v"]
_k7 = relay["K_series_alpha_p7deg_Nm_per_rad"]["v"]
_all = _kc["alpha"] + _kc["beta"] + _k7["alpha"] + _k7["beta"]
K_FEA = (min(_all), max(_all))                       # FEA envelope on the engine axis [N m/rad]
J_C = relay["J_int_servo_output_kgm2"]["v"]["central"]
J_HI = relay["J_int_servo_output_kgm2"]["v"]["range"][1]
q_, d_ = [float(x) for x in os.environ.get("GNC_FK_NOTCH", "1,-12").split(",")]
W_MIS = float(os.environ.get("GNC_FK_MIS_W", "0.15"))
PROV = dict(M.BASE, rcs=False, m_fixed=2.00)
ACT = dict(act_model=1, servo_V=6.6, act_n=4.8, supply_chain=M.ACT_CHAINS["D"], supply_Vrest=None)
FSW = dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, toff_model=1, meco_td=0.72, relight_start=0.20)
I_CAD = relay["I_pivot_wet_kgm2"]["v"]                # CAD v3.3 wet engine inertia about the pivot (relayed with the FEA)
FEA = dict(rock_K_eng=K_FEA, eng_I_pivot_wet=I_CAD)
NOTCH = dict(gim_notch_track=1.0, gim_notch_mis_w=W_MIS, gim_notch_q=q_, gim_notch_db=d_)
CASES = {
    "fk_oldK_J1.6": (dict(PROV, **ACT, **FSW, act_Jint=J_C), "v2.6 FSW, J 1.6e-3, baseline stiffness range U(1336, 4009) "
                                                              "(= m2_meco mr_J1.6_fix_td72; determinism check)"),
    "fk_J0_lpf": (dict(PROV, **ACT, **FSW, **FEA, act_Jint=0.0), "FEA stiffness, J 0, low-pass only"),
    "fk_J1.6_lpf": (dict(PROV, **ACT, **FSW, **FEA, act_Jint=J_C), "FEA stiffness, J 1.6e-3 (Electronics central), low-pass only"),
    "fk_J1.6_notch": (dict(PROV, **ACT, **FSW, **FEA, **NOTCH, act_Jint=J_C), f"FEA stiffness, J 1.6e-3, + notch Q{q_:g} {d_:g} dB "
                                                                            f"at the run's mode x U({1 - W_MIS:g}, {1 + W_MIS:g})"),
    "fk_J2.7_lpf": (dict(PROV, **ACT, **FSW, **FEA, act_Jint=J_HI), "FEA stiffness, J 2.7e-3 (upper end), low-pass only"),
    "fk_J2.7_notch": (dict(PROV, **ACT, **FSW, **FEA, **NOTCH, act_Jint=J_HI), f"FEA stiffness, J 2.7e-3, + notch Q{q_:g} {d_:g} dB"),
    "fk_J1.6_f125_lpf": (dict(PROV, **ACT, **FSW, **FEA, act_Jint=J_C, floor=0.125), "12.5 % floor, FEA stiffness, J 1.6e-3, "
                                                                                   "low-pass only"),
    "fk_J1.6_f125_notch": (dict(PROV, **ACT, **FSW, **FEA, **NOTCH, act_Jint=J_C, floor=0.125), f"12.5 % floor, FEA stiffness, "
                                                                                              f"J 1.6e-3, + notch Q{q_:g} {d_:g} dB"),
}


def main():
    out_dir = os.environ["GNC_OUT"]; suf = os.environ["GNC_SUFFIX"]
    os.makedirs(out_dir, exist_ok=True)
    names = [x for x in os.environ.get("GNC_FK_CASES", ",".join(CASES)).split(",") if x]
    p_sum = os.path.join(out_dir, f"mc6_summary_{suf}.json")
    allsum = json.load(open(p_sum))["cases"] if os.path.exists(p_sum) else {}
    for name in names:
        over, note = CASES[name]
        out, rows = M.run_case(name, over, note)
        out["K_FEA_engine_axis_Nm_per_rad"] = K_FEA
        allsum[name] = out
        M.write_csv(os.path.join(out_dir, f"mc6_runs_{name}_{suf}.csv"), rows)
        s = out["summary"]
        print(f"{name:22s} P {s['success']:.3f} [{s['ci95'][0]:.3f},{s['ci95'][1]:.3f}] fails {s['fail_modes']} "
              f"({out['cpu_s']:.0f}s)", flush=True)
        with open(p_sum, "w") as f:
            json.dump(dict(version=f"m2_csi_v3_mc v1 {suf}", sim=s6.SIM6_VERSION, n=M.N, relay=RELAY, K_FEA=K_FEA,
                           notch=dict(Q=q_, depth_dB=d_, mistune_halfwidth=W_MIS), cases=allsum), f, indent=1, default=float)


if __name__ == "__main__":
    main()
