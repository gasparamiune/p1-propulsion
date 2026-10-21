"""Duty-cycle CSVs v2 (gnc.json v2) for Combustion (grain/thermal) and Mechanical (transient FEA, gimbal).

(a) full flight   : DC-A1 A-D baseline (nose drogue + aft fins, 300 m) from the 6-DOF, 5 m/s wind + Dryden gusts
                    (one seeded realisation: representative gimbal activity); DC-A2 A-F free-fall 300 m envelope
                    (finless, TVC flip, relight at ~140 m / 54 m/s, zero wind)
(b) hop           : DC-B1 continuous-burn hop 100 m and DC-B2 50 m (6-DOF, 5 m/s wind + gusts)
(c) tethered hover: DC-C designed test sequence (open-loop thrust/gimbal command history)
(d) static fire   : DC-D qualification profile (throttle steps, sines, 3 starts, gimbal sweeps)
Engine map: interfaces/combustion.json v1 throttle map x combustion v2 relay factors (S230 straight port; gncsim.engine_v2,
data/relay/engine_correction_v2.json). Flights: sim6 v2.4, RV-1c ledger v3c (mechanical.json v1 engine module + relay
growth, 146 mm body, roll RCS, structural command filter, flexible engine mount).
"""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6, run1d  # noqa: E402
from gncsim.propulsion import _bilin  # noqa: E402
import m1_duty_cycles as m1  # noqa: E402

OUT = os.environ.get("GNC_DC_OUT", "/home/claude/work/space/out/duty_cycles_v2")
os.makedirs(OUT, exist_ok=True)
COLS = ["t_s", "F_N", "F_cmd_N", "throttle_frac", "mdot_ox_kgps", "mdot_fuel_kgps", "Pc_Pa", "P_tank_Pa",
        "T_tank_K", "a_axial_specific_mps2", "h_m", "v_mps", "m_kg", "z_cg_m", "I_transverse_kgm2",
        "I_roll_kgm2", "gimbal_x_cmd_deg", "gimbal_y_cmd_deg", "gimbal_x_deg", "gimbal_y_deg",
        "hinge_moment_est_Nm", "tilt_deg", "phase"]
I = {n: i for i, n in enumerate(s6.REC_NAMES)}


def flight(name, over, wind, seed, note):
    cfg = R.cfg_of(**over)
    m, _ = R.size_load(cfg)
    m *= 1.15
    cfg = R.cfg_of(**dict(over, m_n2o=m, wind=wind, gust=wind > 0, seed=seed, wind_dir=0.7, rec_dt=0.01))
    res, rec, info = R.fly(cfg, nrec=12000)
    tab = R.sources()["tab"]
    F = rec[:, I["F"]]
    pc = np.array([_bilin(tab["Fg"], tab["Dg"], tab["pc"], f, tab["Dg"][0]) if f > 1 else 1.0e5 for f in F])
    rows = np.column_stack([rec[:, I["t"]], F, rec[:, I["Fcmd"]], F / 500.0, rec[:, I["mox"]], rec[:, I["mf"]], pc,
                            rec[:, I["Ptank"]], rec[:, I["Ttank"]], rec[:, I["fax"]], rec[:, I["z"]] - info["zcg0"]
                            + 0.0, rec[:, I["vz"]], rec[:, I["m"]], rec[:, I["zcg"]], rec[:, I["It"]], rec[:, I["Ir"]],
                            rec[:, I["dcx"]], rec[:, I["dcy"]], rec[:, I["dgx"]], rec[:, I["dgy"]], rec[:, I["hinge"]],
                            rec[:, I["tilt"]], rec[:, I["phase"]]])
    # h_m column: CG height above its liftoff value (= feet height above ground before leg compression)
    t = rec[:, 0]
    meta = dict(name=name, source=f"SIM {s6.SIM6_VERSION} 6-DOF, engine: {info['tags']['engine_model'][1]}, dt 1 ms, "
                                  f"recorded 10 ms",
                config={k: v for k, v in over.items()}, wind_mps_at_10m=wind, seed=seed, m_n2o_kg=m,
                tank_V_m3=info["tank_V"], m_liftoff_kg=info["m_liftoff"],
                summary={k: float(res[k]) for k in ["landed", "td_vz", "td_vh", "td_tilt", "td_rate", "prop_used",
                                                    "h_max", "h_ign", "v_ign", "burn_time", "starts", "max_gim",
                                                    "max_gim_rate", "max_hinge", "max_axial_g", "peak_leg_force"]},
                success=R.success(res), total_impulse_Ns=float(np.trapezoid(F, t)), burn_time_s=float(res["burn_time"]),
                starts=int(res["starts"]), max_axial_specific_mps2=float(np.nanmax(rows[:, 9])),
                max_gimbal_deg=float(res["max_gim"]), max_gimbal_rate_dps=float(res["max_gim_rate"]), note=note)
    return rows, meta


def to_v2(rows_v1):
    """m1 test-sequence rows (19 columns) -> v2 layout (actual gimbal = command, hinge/tilt unknown)."""
    n = rows_v1.shape[0]
    nanv = np.full(n, np.nan)
    return np.column_stack([rows_v1[:, :18], rows_v1[:, 16], rows_v1[:, 17], nanv, nanv, rows_v1[:, 18]])


def write(name, rows, meta):
    p = os.path.join(OUT, name + ".csv")
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for row in rows:
            w.writerow([("%.6g" % x) if np.isfinite(x) else "" for x in row])
    meta["file"] = name + ".csv"
    meta["columns"] = COLS
    return meta


def main():
    idx = {"version": "duty_cycles v2", "date": "2026-10-12", "owner": "Space/GNC", "vehicle": "RV-1c",
           "units": "SI; throttle_frac = F / 500 N; a_axial_specific = specific force along the body axis; "
                    "gimbal angles at the engine (after actuator dynamics/backlash); hinge = actuator hinge-moment "
                    "estimate (inertial + hose + friction) per axis max",
           "phase_codes": {**m1.PHASE_NAMES, 99: "test"}, "cycles": [],
           "supersedes": "duty_cycles v1 (1-D, ENGINE-BASELINE placeholder map, zero gimbal columns)",
           "engine_model": R.build(R.cfg_of(profile="A-D", fins=True, m_n2o=1.5))[5]["tags"]["engine_model"][1],
           "sim": s6.SIM6_VERSION}
    for name, over, wind, seed, note in [
            ("DC-A1_full_flight_drogue_fins_300m_v2", dict(profile="A-D", fins=True), 5.0, 7,
             "baseline flight; one seeded 5 m/s + gust realisation"),
            ("DC-A2_full_flight_freefall_300m_v2", dict(profile="A-F", fins=False), 0.0, 7,
             "envelope: free-fall relight at ~130 m and ~56 m/s (longest high-thrust landing burn)"),
            ("DC-B1_hop_100m_floor20_v2", dict(profile="B"), 5.0, 7, "continuous-burn hop 100 m"),
            ("DC-B2_hop_50m_floor20_v2", dict(profile="B", h_target=50.0), 5.0, 7, "continuous-burn hop 50 m")]:
        rows, meta = flight(name, over, wind, seed, note)
        idx["cycles"].append(write(name, rows, meta))
    # test sequences with the combustion.json v1 map
    run1d._TAB = R.sources()["tab"]
    m_hover = R.build(R.cfg_of(profile="A-D", fins=True, m_n2o=1.45))[5]["m_liftoff"]  # RV-1c liftoff mass
    rows, meta = m1.tethered_hover_dc(m_vehicle=round(m_hover, 2))
    meta["name"] = "DC-C_tethered_hover_v2"
    meta["source"] += "; combustion.json v1 map"
    idx["cycles"].append(write(meta["name"], to_v2(rows), meta))
    rows, meta = m1.static_fire_dc()
    meta["name"] = "DC-D_static_fire_qualification_v2"
    meta["source"] += "; combustion.json v1 map"
    idx["cycles"].append(write(meta["name"], to_v2(rows), meta))
    run1d._TAB = None
    longest = max(c["burn_time_s"] for c in idx["cycles"] if c["name"].startswith(("DC-A", "DC-B")))
    idx["longest_flight_burn_s"] = longest
    dcd = [c for c in idx["cycles"] if c["name"].startswith("DC-D")][0]
    idx["qualification_check"] = dict(DC_D_burn_s=dcd["burn_time_s"], ratio_to_longest_flight=dcd["burn_time_s"] / longest)
    with open(os.path.join(OUT, "duty_cycles_index_v2.json"), "w") as f:
        json.dump(idx, f, indent=1, default=float)
    for c in idx["cycles"]:
        print(f"{c['name']:42s} burn {c['burn_time_s']:6.2f} s  I {c['total_impulse_Ns']:7.0f} N s  starts {c.get('starts')}"
              f"  ok {c.get('success')}")
    print("longest flight burn", round(longest, 2), "DC-D ratio", round(idx["qualification_check"]["ratio_to_longest_flight"], 2))


if __name__ == "__main__":
    main()
