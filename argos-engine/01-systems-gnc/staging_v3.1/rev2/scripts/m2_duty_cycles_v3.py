"""m2_duty_cycles_v3 v1.3 (2026-10-13; v1.3: AXIAL-LOAD FIELDS - max_axial_specific_mps2 is the maximum over the whole
record, leg contact included (touchdown load case; for a failed landing the crash impact in the leg spring-damper model,
not a design load); the index adds the airborne and leg-contact maxima (sim6 leg force), the time / phase / thrust / leg
force of the overall maximum and max_axial_definition; index revision 2026-10-13c; time histories unchanged.
v1.2: BURN-TIME DEFINITION - index burn_time_s is now the thrust-on time of the file
(sum of the 10 ms record steps with F > 1 N, all burns; resolution +/-0.01 s per burn edge); the sim6 result burn_time, an
engine-on counter that excludes the shutdown tail-off and keeps counting after propellant exhaustion until the cut, moves to
engine_on_counter_s (Combustion query relayed by the lead 2026-10-13: DC-B1 disp max thrust ends at 23.59 s vs 24.09 s in
the index). Retained v2 entries get the same definition from their files (v2 index value kept as burn_time_s_v2_index).
Time histories unchanged. v1.1: relight placeholder of the lead decision 2026-10-13, NC-closed sequence
0.8 s + 0.3 s on the start delay and on the planning value = 1.1 / 1.7 s, until the Combustion v2.4 RC-03 latency
distribution; the v1 files at 0.8 s are kept as out/duty_cycles_v3_v1_rl0.8): duty cycles v3 for gnc.json v3 (lead decision on OI-1, 2026-10-12: option (a);
tank 2.00 kg / 3.17 L; A1 = baseline flight; B1 development hop capped at 85 m; B2 unchanged; A2 removed from the
2.00 kg plan; reference-governor ratchet adopted).

Published here (sim6/run6 v2.6 6-DOF on the interface set GNC_IFACE = iface_v3c: combustion.json v2.3 map as published,
mechanical.json v2, electronics.json v1; N2O 2.00 kg, roll RCS not fitted):
  DC-A1_full_flight_drogue_fins_300m_v3  A-D, nose drogue + aft fins, 300 m
  DC-B1_hop_85m_floor20_v3               B, continuous-burn hop, 85 m, 20 % floor
Both with the v3 flight software (command tracker 2000 deg/s2, reference governor 40 deg/s with the ratchet, lift-ramp
shutdown with the 72 % pre-MECO throttle-down, relight start rule 20 %, NC-closed relight timeline) on the as-drawn
actuator chain (torque/speed-limited servo pair, n 4.8, 6.6 V at the plug at double stall), reflected rotor inertia
1.6e-3 kg m2 (Electronics central) and the ENG-07d notch (Q1, -12 dB) centred on the run's own landing-burn rocking mode,
flexible engine mount at the low end of the mechanical.json v2 axis stiffness. One seeded realisation of 5 m/s wind +
Dryden gusts (seed 7, direction 0.7 rad, as in v2): representative gimbal activity, not an envelope.
Retained from v2 in the index (files unchanged, not re-flown): DC-B1 v2 (100 m, 19.0 s) as the CONSERVATIVE THERMAL
ENVELOPE (lead: Mechanical's thermal FEA uses it), DC-B2 v2 (50 m hop, mission unchanged), DC-A2 v2 (removed from the
2.00 kg plan; reference for the 2.20 kg / 3.49 L fallback), DC-C v2 and DC-D v2 (designed test sequences).
Columns and phase codes as v2. Pc_Pa from the published map at the flown thrust (the v2.3 map gives Pc as a function of
thrust only). Env: GNC_IFACE, GNC_ACT_RATE, GNC_DC_OUT (default out/duty_cycles_v3), GNC_DC_V2 (v2 index folder)."""
import csv
import hashlib
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
from gncsim.propulsion import _bilin  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_meco_mc as MM  # noqa: E402  (NC-closed relight sequence time from combustion.json)

VERSION = "m2_duty_cycles_v3 v1.3"
RL_ADD = float(os.environ.get("GNC_DC_RL_ADD", "0.3"))   # lead decision 2026-10-13 (placeholder)
OUT = os.environ.get("GNC_DC_OUT", "/home/claude/work/space/out/duty_cycles_v3")
DC_V2 = os.environ.get("GNC_DC_V2", "/home/claude/work/space/out/duty_cycles_v2")
HUB_DC = "01-systems-gnc/duty_cycles/"
COLS = ["t_s", "F_N", "F_cmd_N", "throttle_frac", "mdot_ox_kgps", "mdot_fuel_kgps", "Pc_Pa", "P_tank_Pa",
        "T_tank_K", "a_axial_specific_mps2", "h_m", "v_mps", "m_kg", "z_cg_m", "I_transverse_kgm2",
        "I_roll_kgm2", "gimbal_x_cmd_deg", "gimbal_y_cmd_deg", "gimbal_x_deg", "gimbal_y_deg",
        "hinge_moment_est_Nm", "tilt_deg", "phase"]
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
M_TANK = 2.00            # REQ lead decision 2026-10-12 (OI-1 option (a)): N2O 2.00 kg in 3.17 L
TRAP = 0.03              # ASSUMED trapped liquid fraction of the load (closure rule, as m2_prop_closure)
RESERVE = 0.25           # REQ lead '+25 %' rule (usable liquid at touchdown >= 25 % of the N2O burned)
H_B1 = 85.0              # REQ lead decision 2026-10-12: B1 development hop capped at 85 m

src = R.sources()
if str(src["mech"].get("version")) == "v1":
    raise SystemExit("m2_duty_cycles_v3 needs mechanical.json >= v2 (GNC_IFACE = iface_v3c)")
RELAY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "relay",
                     "lead_relay_mech_fea_k_20261012.json")
J_C = json.load(open(RELAY))["J_int_servo_output_kgm2"]["v"]["central"]   # Electronics servo_jint_estimate_v1 (relay)
n_m = src["mech"]["tvc_actuation"]["gear_ratio_n"]["v"]
ACT = dict(act_model=1, servo_V=6.6, act_n=n_m, supply_chain=M.ACT_CHAINS["D"], supply_Vrest=None, act_Jint=J_C)
NOTCH = dict(gim_notch_track=1.0, gim_notch_q=1.0, gim_notch_db=-12.0)
FSW = dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, att_ref_mode=1, toff_model=1)
FSW_A = dict(FSW, meco_td=0.72, relight_start=0.20, t_ign_add=MM.NCS["slots"] + RL_ADD,
             t_ign_est=R.DEF["t_ign_est"] + MM.NCS["slots"] + RL_ADD)
CYCLES = [
    ("DC-A1_full_flight_drogue_fins_300m_v3", dict(profile="A-D", fins=True, rcs=False, floor=0.20, **FSW_A, **ACT, **NOTCH),
     "BASELINE flight (lead 2026-10-12): A-D 300 m, nose drogue + aft fins; one seeded 5 m/s + gust realisation"),
    ("DC-B1_hop_85m_floor20_v3", dict(profile="B", h_target=H_B1, fins=False, rcs=False, floor=0.20, **FSW, **ACT, **NOTCH),
     "development hop capped at 85 m (lead 2026-10-12); continuous burn, 20 % floor; one seeded 5 m/s + gust realisation"),
]
RETAINED_V2 = {
    "DC-B1_hop_100m_floor20_v2": "CONSERVATIVE THERMAL ENVELOPE (lead 2026-10-12): 100 m hop, 19.0 s burn; no longer a flight "
                                 "cycle (B1 capped at 85 m); Mechanical's thermal FEA uses it. Flown on sim6 v2.4, "
                                 "mechanical.json v1, combustion.json v1 map x relay factors, N2O sized 2.44 kg (v2 rule)",
    "DC-B2_hop_50m_floor20_v2": "B2 50 m hop: mission unchanged (lead 2026-10-12); v2 file retained, not re-flown (sim6 v2.4, "
                                "mechanical.json v1, v1 map x relay factors)",
    "DC-A2_full_flight_freefall_300m_v2": "REMOVED from the 2.00 kg plan (lead 2026-10-12); kept as the reference for the 2.20 kg / "
                                          "3.49 L fallback only. Note: dispersed A2 flights tumble in the coast and reach "
                                          "213-266 m (gnc.json v3 propellant_closure_v3)",
    "DC-C_tethered_hover_v2": "designed test sequence (unchanged)",
    "DC-D_static_fire_qualification_v2": "designed test sequence (unchanged); qualification ratio re-checked below",
}


BURN_DEF = ("burn_time_s = thrust-on time of the file: sum of the 10 ms record steps with delivered thrust F > 1 N (all "
            "burns; +/-0.01 s per burn edge). engine_on_counter_s = sim6 result burn_time (flight-software burn state on): it "
            "excludes the shutdown tail-off and, on a propellant-limited run, includes zero-thrust time after liquid "
            "depletion until the cut. Index revision 2026-10-13b; earlier v1 / v2 / v3 indexes gave the counter as "
            "burn_time_s (Combustion query relayed by the lead 2026-10-13)")


def burn_of(t, F, thr=1.0):
    """thrust-on time [s] (record steps with F > thr), burns [[t_first, t_last], ...] and the last thrust time."""
    t = np.asarray(t, float); F = np.asarray(F, float)
    dt = np.diff(t, prepend=0.0)
    on = F > thr
    if not on.any():
        return 0.0, [], float("nan")
    e = np.diff(np.concatenate([[0], on.astype(int), [0]]))
    a, b = np.where(e == 1)[0], np.where(e == -1)[0] - 1
    return float(np.sum(dt[on])), [[float(t[i]), float(t[j])] for i, j in zip(a, b)], float(t[on][-1])


def burn_of_csv(p):
    d = np.genfromtxt(p, delimiter=",", names=True)
    return burn_of(d["t_s"], d["F_N"])


AX_DEF = ("max_axial_specific_mps2 = maximum of the a_axial_specific_mps2 column over the whole record, leg contact included "
          "(pad and touchdown, leg spring-damper contact model of sim6): for a landing at ~1 m/s it is the touchdown load case, "
          "for a FAILED landing it is the crash impact, not a design load. max_axial_specific_airborne_mps2 = maximum over the "
          "records without leg contact (sim6 leg force = 0: powered ascent, coast, descent, landing burn before contact); "
          "max_axial_specific_leg_contact_mps2 = maximum with leg contact. max_axial_at_s / max_axial_phase / max_axial_thrust_N / "
          "max_axial_leg_force_N locate the overall maximum. Index revision 2026-10-13c (fields added, no value changed)")
INDEX_REVISION = {"revision": "2026-10-13c", "history": [
    "2026-10-13a: dispersed duty cycles added (m2_duty_cycles_disp v1)",
    "2026-10-13b: burn_time_s = thrust-on time of the file; the engine-on counter moved to engine_on_counter_s (Combustion query)",
    "2026-10-13c: max_axial_specific_airborne_mps2, max_axial_specific_leg_contact_mps2 and the location of the overall maximum "
    "added with max_axial_definition (the overall maximum of the two failed max runs is the touchdown crash impact); files "
    "unchanged"]}


def axial_stats(rows, legF):
    """maxima of the axial specific force column (index 9) of a duty-cycle row array, split by leg contact (sim6 legF)."""
    a, F = rows[:, 9], rows[:, 1]
    legF = np.asarray(legF, float)
    i = int(np.nanargmax(a))
    air = legF <= 0.0
    return dict(max_axial_specific_airborne_mps2=float(np.nanmax(a[air])) if air.any() else None,
                max_axial_specific_leg_contact_mps2=float(np.nanmax(a[~air])) if (~air).any() else None,
                max_axial_at_s=float(rows[i, 0]), max_axial_phase=int(rows[i, 22]), max_axial_thrust_N=float(F[i]),
                max_axial_leg_force_N=float(legF[i]))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def flight(name, over, note, wind=5.0, seed=7):
    cfg = R.cfg_of(**dict(over, m_n2o=M_TANK, wind=wind, gust=wind > 0, seed=seed, wind_dir=0.7, rec_dt=0.01))
    res, rec, info = R.fly(cfg, nrec=12000)
    tab = src["tab"]
    F = rec[:, I["F"]]
    pc = np.array([_bilin(tab["Fg"], tab["Dg"], tab["pc"], f, tab["Dg"][0]) if f > 1 else 1.0e5 for f in F])
    rows = np.column_stack([rec[:, I["t"]], F, rec[:, I["Fcmd"]], F / 500.0, rec[:, I["mox"]], rec[:, I["mf"]], pc,
                            rec[:, I["Ptank"]], rec[:, I["Ttank"]], rec[:, I["fax"]], rec[:, I["z"]] - info["zcg0"],
                            rec[:, I["vz"]], rec[:, I["m"]], rec[:, I["zcg"]], rec[:, I["It"]], rec[:, I["Ir"]],
                            rec[:, I["dcx"]], rec[:, I["dcy"]], rec[:, I["dgx"]], rec[:, I["dgy"]], rec[:, I["hinge"]],
                            rec[:, I["tilt"]], rec[:, I["phase"]]])
    t = rec[:, I["t"]]
    n2o_burned = float(np.sum(0.5 * (rec[1:, I["mox"]] + rec[:-1, I["mox"]]) * np.diff(t)))
    liq = float(res["liq_left"])
    usable = liq - TRAP * M_TANK
    tags = info["tags"]
    meta = dict(name=name, source=f"SIM {s6.SIM6_VERSION} 6-DOF, engine: {tags['engine_model'][1]}, dt 1 ms, recorded 10 ms",
                config={k: (v if not isinstance(v, (np.floating, np.integer)) else float(v)) for k, v in over.items()},
                wind_mps_at_10m=wind, seed=seed, m_n2o_kg=M_TANK, tank_V_m3=info["tank_V"], m_liftoff_kg=info["m_liftoff"],
                rock_K_flown_Nm_per_rad=float(tags["rock_K"][0]) if "rock_K" in tags else None,
                notch_f_Hz=float(tags["gim_notch_f"][0]) if "gim_notch_f" in tags else None,
                notch_tag=tags["gim_notch_f"][1] if "gim_notch_f" in tags else None,
                summary={k: float(res[k]) for k in ["landed", "td_vz", "td_vh", "td_tilt", "td_rate", "prop_used", "liq_left",
                                                    "h_max", "h_ign", "v_ign", "burn_time", "starts", "max_gim",
                                                    "max_gim_rate", "max_hinge", "max_axial_g", "peak_leg_force",
                                                    "act_sat_max_dur", "act_Vmin"] if k in res},
                n2o_burned_kg=n2o_burned, usable_liquid_left_kg=usable,
                reserve_frac_this_flight=usable / n2o_burned if n2o_burned > 0 else float("nan"),
                reserve_note="this seeded windy flight; the closure basis is the nominal no-wind flight (gnc.json v3 "
                             "propellant_closure_v3)",
                success=R.success(res), total_impulse_Ns=float(np.trapezoid(F, t)), burn_time_s=burn_of(t, F)[0],
                engine_on_counter_s=float(res["burn_time"]), burns_s=burn_of(t, F)[1], thrust_end_s=burn_of(t, F)[2],
                starts=int(res["starts"]), max_axial_specific_mps2=float(np.nanmax(rows[:, 9])),
                max_gimbal_deg=float(res["max_gim"]), max_gimbal_rate_dps=float(res["max_gim_rate"]),
                max_hinge_est_Nm=float(res["max_hinge"]), note=note)
    meta.update(axial_stats(rows, rec[:, I["legF"]]))
    return rows, meta


def write(name, rows, meta):
    p = os.path.join(OUT, name + ".csv")
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for row in rows:
            w.writerow([("%.6g" % x) if np.isfinite(x) else "" for x in row])
    meta["file"] = HUB_DC + name + ".csv"
    meta["sha256"] = sha(p)
    meta["columns"] = COLS
    return meta


def main():
    os.makedirs(OUT, exist_ok=True)
    v2 = json.load(open(os.path.join(DC_V2, "duty_cycles_index_v2.json")))
    v2c = {c["name"]: c for c in v2["cycles"]}
    iface = R.IFACE
    man = os.path.join(iface, "MANIFEST.sha256")
    idx = {"version": "duty_cycles v3", "date": "2026-10-13", "owner": "Space/GNC", "generator": VERSION,
           "vehicle": "RV-1c on mechanical.json v2 (ledger v3d)", "sim": s6.SIM6_VERSION,
           "interfaces": {k: (src[k] or {}).get("version") for k in ("comb", "mech", "el")}, "interface_set": iface,
           "interface_manifest": open(man).read().split("\n") if os.path.exists(man) else None,
           "flight_software": dict(FSW_A, note="B profile: no MECO / relight keys (single continuous burn)",
                                  relight_placeholder=f"lead decision 2026-10-13: NC-closed sequence {MM.NCS['slots']:.2f} s + "
                                                      f"{RL_ADD:.2f} s on the start delay and on the planning value "
                                                      "(placeholder until the Combustion v2.4 RC-03 latency distribution)"),
           "actuation": dict(ACT, notch=NOTCH, note="as-drawn chain at 6.6 V (validation voltage), J central, notch tracking "
                                                   "the run's landing-burn rocking mode (mistune 1.0)"),
           "lead_decision": "OI-1 option (a), 2026-10-12: tank 2.00 kg / 3.17 L; A1 baseline; B1 capped at 85 m; B2 unchanged; "
                            "A2 removed from the 2.00 kg plan (2.20 kg / 3.49 L fallback documented); ratchet adopted",
           "units": v2["units"], "phase_codes": v2["phase_codes"], "columns": COLS,
           "engine_model": None, "cycles": [], "retained_v2": [], "supersedes": "duty_cycles v2 (sim6 v2.4, mechanical.json v1, "
                                                                                 "combustion.json v1 map x relay factors)"}
    for name, over, note in CYCLES:
        rows, meta = flight(name, over, note)
        idx["engine_model"] = meta["source"].split("engine: ")[1].split(", dt")[0]
        idx["cycles"].append(write(name, rows, meta))
        s = meta["summary"]
        print(f"{name:40s} ok {meta['success']} burn {meta['burn_time_s']:6.2f} s I {meta['total_impulse_Ns']:7.0f} N s "
              f"starts {meta['starts']} apex {s['h_max']:.1f} m td_vz {s['td_vz']:.2f} N2O burned {meta['n2o_burned_kg']:.3f} "
              f"reserve {100 * meta['reserve_frac_this_flight']:.1f} % max gim {meta['max_gimbal_deg']:.2f} deg "
              f"rate {meta['max_gimbal_rate_dps']:.0f} deg/s hinge {meta['max_hinge_est_Nm']:.2f} N m", flush=True)
    for name, status in RETAINED_V2.items():
        c = v2c[name]
        p = os.path.join(DC_V2, name + ".csv")
        ton, burns, tend = burn_of_csv(p)
        idx["retained_v2"].append(dict(name=name, status=status, file=HUB_DC + name + ".csv",
                                       sha256=sha(p) if os.path.exists(p) else None, burn_time_s=ton, burns_s=burns,
                                       thrust_end_s=tend, burn_time_s_v2_index=c["burn_time_s"],
                                       total_impulse_Ns=c["total_impulse_Ns"], starts=c.get("starts"),
                                       m_n2o_kg=c.get("m_n2o_kg"), source=c.get("source")))
    idx["burn_time_definition"] = BURN_DEF
    idx["max_axial_definition"] = AX_DEF
    idx["index_revision"] = INDEX_REVISION
    flights_now = [c["burn_time_s"] for c in idx["cycles"]] + [c["burn_time_s"] for c in idx["retained_v2"]
                                                               if c["name"].startswith("DC-B2")]
    longest_now = max(flights_now)
    env_c = [c for c in idx["retained_v2"] if c["name"].startswith("DC-B1")][0]
    env = env_c["burn_time_s"]
    dcd = [c for c in idx["retained_v2"] if c["name"].startswith("DC-D")][0]["burn_time_s"]
    idx["longest_flight_burn_current_plan_s"] = longest_now
    idx["conservative_thermal_envelope_burn_s"] = env
    idx["conservative_thermal_envelope_engine_on_counter_s"] = env_c["burn_time_s_v2_index"]
    idx["longest_flight_engine_on_counter_current_plan_s"] = max(
        [c["engine_on_counter_s"] for c in idx["cycles"]] + [c["burn_time_s_v2_index"] for c in idx["retained_v2"]
                                                            if c["name"].startswith("DC-B2")])
    idx["qualification_check"] = dict(DC_D_burn_s=dcd, ratio_to_longest_current_flight=dcd / longest_now,
                                      ratio_to_conservative_envelope=dcd / env, definition="thrust-on times (burn_time_definition)")
    with open(os.path.join(OUT, "duty_cycles_index_v3.json"), "w") as f:
        json.dump(idx, f, indent=1, default=float)
    print("longest current flight burn", round(longest_now, 2), "s; envelope", round(env, 2), "s; DC-D ratio",
          round(dcd / longest_now, 2), "/", round(dcd / env, 2))


if __name__ == "__main__":
    main()
