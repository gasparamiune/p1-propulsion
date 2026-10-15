"""m2_mechv2_mc v1.1 (2026-10-12; v1.1 adds the re-tuned reduced-bandwidth cases _rt): GNC v3 re-baseline Monte Carlo on mechanical.json v2 (interface set GNC_IFACE = v3c:
combustion.json v2.3, mechanical.json v2, electronics.json v1). Same 500 draws (seed 101) as every case.

mechanical.json v2 is read natively by run6 v2.6 (mass properties from the CAD v3.3 solids + v3.4 pintle stack, pivot at
RV-1 0.203 m, fixed TVC module from the CAD, axis stiffness = FEA structure + rods at 9 poses in series with the ASSUMED
servo, MC U(552.5, 1681) N m/rad, hose hinge stiffness U(1.73, 17.48) N m/rad); no relay overrides.
Every case flies the v3 flight software: command tracker 2000 deg/s2 + attitude reference governor 40 deg/s WITH the
ratchet (att_ref_mode 1), lift-ramp shutdown with the 72 % pre-MECO throttle-down, relight start rule 20 %, NC-closed
relight timeline (sequence time from combustion.json on the start delay and on the planning value), on the
torque/speed-limited servo pair at 6.6 V (as-drawn chain), n 4.8, N2O 2.00 kg (lead tank), no roll RCS, A-D (drogue + fins).
Cases: J_int 0 / 1.6e-3 (Electronics central) / 2.7e-3 (upper), with and without the ECU notch (Q1, -12 dB) centred on
each run's own landing-burn rocking mode x a mistune factor U(1 - w, 1 + w) (w 0.15 = one fixed centre per axis set
from B-TVC-1; w 0.05 = tuned on the measured mode), the landing attitude bandwidth x 0.75 (att_wn 4.5 rad/s, the
fallback branch at the B-TVC-1 gate), the 12.5 % floor, and the stiffness target adopted by the lead (structure + rods
3,100-5,200 N m/rad in series with the servo range, electronics.json 58-174 N m/rad x n^2).
Hypotheses (as m2_csi_v3_mc): one stiffness value for both axes per run, rotor inertia lumped on the engine side,
mount damping U(0.02, 0.10).
Env: GNC_V3C_CASES (comma list; default all), GNC_OUT (default out/mechv2_mc), GNC_SUFFIX (default m2)."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/mechv2_mc")
os.environ.setdefault("GNC_SUFFIX", "m2")
import m2_mc6 as M  # noqa: E402
import m2_meco_mc as MM  # noqa: E402  (NC-closed relight sequence time from combustion.json)
from gncsim import run6 as R, sim6 as s6  # noqa: E402

src = R.sources()
if str(src["mech"].get("version")) == "v1":
    raise SystemExit("m2_mechv2_mc needs mechanical.json >= v2 (GNC_IFACE = iface_v3c)")
RELAY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "relay",
                     "lead_relay_mech_fea_k_20261012.json")
relay = json.load(open(RELAY))
J_C = relay["J_int_servo_output_kgm2"]["v"]["central"]          # Electronics servo_jint_estimate_v1 via the lead relay
J_HI = relay["J_int_servo_output_kgm2"]["v"]["range"][1]
n_m = src["mech"]["tvc_actuation"]["gear_ratio_n"]["v"]
Ks_out = src["el"]["actuators"]["tvc_A"]["stiffness"]["v"]["servo_output_Nm_per_rad"]   # ASSUMED in electronics.json
KS_ENG = (Ks_out[0] * n_m ** 2, Ks_out[1] * n_m ** 2)            # two servos, Cardan mixing: per-axis factor n^2
K_STRUCT_TARGET = (3100.0, 5200.0)    # GNC ENG-07d target adopted by the lead 2026-10-12 (hard minimum, goal) [N m/rad]


def series(a, b):
    return 1.0 / (1.0 / a + 1.0 / b)


K_TGT = (series(K_STRUCT_TARGET[0], KS_ENG[0]), series(K_STRUCT_TARGET[1], KS_ENG[1]))
PROV = dict(M.BASE, rcs=False, m_fixed=2.00)
ACT = dict(act_model=1, servo_V=6.6, act_n=n_m, supply_chain=M.ACT_CHAINS["D"], supply_Vrest=None)
FSW = dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, att_ref_mode=1, toff_model=1, meco_td=0.72, relight_start=0.20)
NC = dict(t_ign_add=MM.NCS["slots"], t_ign_est=R.DEF["t_ign_est"] + MM.NCS["slots"])
N15 = dict(gim_notch_track=1.0, gim_notch_mis_w=0.15, gim_notch_q=1.0, gim_notch_db=-12.0)
N5 = dict(gim_notch_track=1.0, gim_notch_mis_w=0.05, gim_notch_q=1.0, gim_notch_db=-12.0)
B = dict(PROV, **ACT, **FSW, **NC)
CASES = {
    "m2_J0": (dict(B, act_Jint=0.0), "v3 FSW on mechanical.json v2, J 0, low-pass only"),
    "m2_J1.6": (dict(B, act_Jint=J_C), "v3 FSW on mechanical.json v2, J 1.6e-3, low-pass only"),
    "m2_J1.6_n15": (dict(B, act_Jint=J_C, **N15), "J 1.6e-3 + notch Q1 -12 dB, mistune U(0.85, 1.15)"),
    "m2_J1.6_n5": (dict(B, act_Jint=J_C, **N5), "J 1.6e-3 + notch Q1 -12 dB, mistune U(0.95, 1.05)"),
    "m2_J2.7_n15": (dict(B, act_Jint=J_HI, **N15), "J 2.7e-3 + notch Q1 -12 dB, mistune U(0.85, 1.15)"),
    "m2_J1.6_wn4.5": (dict(B, act_Jint=J_C, att_wn=4.5), "J 1.6e-3, landing attitude bandwidth x 0.75, low-pass only"),
    "m2_J1.6_wn4.5_n15": (dict(B, act_Jint=J_C, att_wn=4.5, **N15), "J 1.6e-3, landing bandwidth x 0.75 + notch +/-15 %"),
    "m2_J1.6_tgt": (dict(B, act_Jint=J_C, rock_K_eng=K_TGT), f"J 1.6e-3, structure at the target 3,100-5,200 N m/rad in "
                                                             f"series with the servo: K U({K_TGT[0]:.0f}, {K_TGT[1]:.0f}), "
                                                             "low-pass only"),
    "m2_J1.6_tgt_n15": (dict(B, act_Jint=J_C, rock_K_eng=K_TGT, **N15), "J 1.6e-3, stiffness target + notch +/-15 %"),
    "m2_J1.6_f125_n15": (dict(B, act_Jint=J_C, floor=0.125, **N15), "12.5 % floor, J 1.6e-3 + notch +/-15 %"),
    # v1.1: the reduced-bandwidth fallback with the outer loops re-tuned by the same factor (lateral PD bandwidth lat_wn
    # 1.0 -> 0.75 rad/s, terminal lateral-velocity gain kt_lat 1.5 -> 1.125 1/s), so that the loop separation of the
    # baseline is kept; tests whether the P cost of att_wn 4.5 is a tuning artefact
    "m2_J1.6_wn4.5_rt": (dict(B, act_Jint=J_C, att_wn=4.5, lat_wn=0.75, kt_lat=1.125),
                         "J 1.6e-3, landing bandwidth x 0.75 with the lateral loops re-tuned x 0.75, low-pass only"),
    "m2_J1.6_wn4.5_rt_n15": (dict(B, act_Jint=J_C, att_wn=4.5, lat_wn=0.75, kt_lat=1.125, **N15),
                             "J 1.6e-3, landing bandwidth x 0.75, lateral loops x 0.75 + notch +/-15 %"),
}


def main():
    out_dir = os.environ["GNC_OUT"]; suf = os.environ["GNC_SUFFIX"]
    os.makedirs(out_dir, exist_ok=True)
    names = [x for x in os.environ.get("GNC_V3C_CASES", ",".join(CASES)).split(",") if x]
    p_sum = os.path.join(out_dir, f"mc6_summary_{suf}.json")
    allsum = json.load(open(p_sum))["cases"] if os.path.exists(p_sum) else {}
    for name in names:
        over, note = CASES[name]
        out, rows = M.run_case(name, over, note)
        allsum[name] = out
        M.write_csv(os.path.join(out_dir, f"mc6_runs_{name}_{suf}.csv"), rows)
        s = out["summary"]
        print(f"{name:20s} P {s['success']:.3f} [{s['ci95'][0]:.3f},{s['ci95'][1]:.3f}] fails {s['fail_modes']} "
              f"m_liftoff {out['m_liftoff_kg']:.3f} ({out['cpu_s']:.0f}s)", flush=True)
        with open(p_sum, "w") as f:
            json.dump(dict(version=f"m2_mechv2_mc v1 {suf}", sim=s6.SIM6_VERSION, n=M.N, iface=R.IFACE,
                           interfaces={k: (src[k] or {}).get("version") for k in ("comb", "mech", "el")},
                           K_s_engine_axis=KS_ENG, K_struct_target=K_STRUCT_TARGET, K_target_series=K_TGT,
                           J_central=J_C, J_upper=J_HI, cases=allsum), f, indent=1, default=float)


if __name__ == "__main__":
    main()
