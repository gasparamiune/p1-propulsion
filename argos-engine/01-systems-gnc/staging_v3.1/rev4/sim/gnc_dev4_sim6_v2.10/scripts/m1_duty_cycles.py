"""Duty-cycle CSVs (v1) for Combustion (grain/thermal) and Mechanical (transient FEA).

(a) full flight   : DC-A1 drogue-stabilised 300 m (baseline), DC-A2 free-fall 300 m (envelope)
(b) hop           : DC-B1 continuous-burn hop 100 m (20 % floor), DC-B2 50 m
(c) tethered hover: DC-C  designed test sequence (open-loop thrust/gimbal command history)
(d) static fire   : DC-D  qualification profile (throttle steps, sines, 3 starts, gimbal sweeps)
Flights come from gncsim.sim1d (nominal, zero dispersion). Test sequences are commanded
histories passed through the same first-order/slew engine model and steady throttle map.
Columns (SI): see COLS. Gimbal histories for (a)/(b) come from the 6-DOF in gnc.json v2.
"""
import json
import os
import sys
import csv
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run1d as r, sizing, vehicle as veh, params as prm  # noqa: E402
from gncsim.propulsion import _bilin  # noqa: E402

OUT = os.environ.get("GNC_DC_OUT", "/home/claude/work/space/out/duty_cycles")
os.makedirs(OUT, exist_ok=True)
G0 = 9.80665
COLS = ["t_s", "F_N", "F_cmd_N", "throttle_frac", "mdot_ox_kgps", "mdot_fuel_kgps", "Pc_Pa", "P_tank_Pa",
        "T_tank_K", "a_axial_specific_mps2", "h_m", "v_mps", "m_kg", "z_cg_m", "I_transverse_kgm2",
        "I_roll_kgm2", "gimbal_x_cmd_deg", "gimbal_y_cmd_deg", "phase"]
PHASE_NAMES = {0: "pad", 1: "ascent", 2: "coast_or_floor_coast", 3: "descent", 4: "relight_wait",
               5: "landing_burn", 6: "terminal", 7: "shutdown", 8: "landed", 20: "test"}


def massprops_cols(rec_m_liq, rec_m_tank_total, rec_m_fuel, rho_l=785.0, tank_V=2.5e-3, pivot="mid"):
    geo = veh.reference_geometry(pivot=pivot)
    led = veh.mass_ledger(geo, tank_V=tank_V)
    mp = veh.build_mp(geo, led, tank_V=tank_V)
    out = np.zeros(8)
    zc, it, ir = [], [], []
    for ml, mt, mf in zip(rec_m_liq, rec_m_tank_total, rec_m_fuel):
        veh.massprops(mp, ml, max(mt - ml, 0.0), rho_l, mf, out)
        zc.append(out[1]); it.append(out[2]); ir.append(out[3])
    return np.array(zc), np.array(it), np.array(ir)


def flight_dc(name, pk, m_n2o, floor=0.20):
    V = sizing.tank_volume_for(m_n2o)
    par = r.make_par(floor=floor, m_n2o=m_n2o, tank_V=V, **pk)
    res, rec = r.fly(par, rec_dt=0.01)
    C = {k: i for i, k in enumerate(r.REC_COLS)}
    t = rec[:, 0]
    tab = r.tables()
    D0 = 0.030
    pc = np.array([_bilin(tab["Fg"], tab["Dg"], tab["pc"], F, D0) if F > 1 else 1.0e5
                   for F in rec[:, C["F_N"]]])
    # tank total mass from the ledger-independent bookkeeping: m - dry - fuel
    m_tank_total = rec[:, C["m_kg"]] - par[r.s.I_M_DRY] - rec[:, C["m_fuel_kg"]]
    zc, it, ir = massprops_cols(rec[:, C["m_n2o_liquid_kg"]], m_tank_total, rec[:, C["m_fuel_kg"]], tank_V=V)
    rows = np.column_stack([t, rec[:, C["F_N"]], rec[:, C["F_cmd_N"]], rec[:, C["F_N"]] / 500.0,
                            rec[:, C["mdot_ox_kgps"]], rec[:, C["mdot_fuel_kgps"]], pc, rec[:, C["P_tank_Pa"]],
                            rec[:, C["T_tank_K"]], rec[:, C["a_axial_specific_mps2"]], rec[:, C["h_m"]],
                            rec[:, C["v_mps"]], rec[:, C["m_kg"]], zc, it, ir, np.zeros_like(t), np.zeros_like(t),
                            rec[:, C["phase"]]])
    meta = dict(name=name, source="SIM gncsim.sim1d v1.2 guidance nominal (zero dispersion), dt 1 ms, recorded 10 ms",
                profile=pk, m_n2o_kg=m_n2o, tank_V_m3=V, floor_frac=floor, summary={k: float(v) for k, v in res.items()},
                total_impulse_Ns=float(np.trapezoid(rows[:, 1], t)), burn_time_s=float(res["burn_time"]),
                starts=int(res["starts"]), max_axial_specific_mps2=float(rows[:, 9].max()),
                note="gimbal columns zero in v1 (vertical model); 6-DOF gimbal histories in v2")
    return rows, meta


def engine_response(t, Fcmd, tau=0.0455, slew=5.0 * 500.0, Fmax=500.0, floor=100.0, ign_delay=0.4):
    """Pass a commanded thrust history through the GNC engine model (lag, slew, ignition delay)."""
    F = np.zeros_like(t)
    lit_since = None
    for k in range(1, len(t)):
        dt = t[k] - t[k - 1]
        c = Fcmd[k]
        if c > 0 and lit_since is None:
            lit_since = t[k]
        if c <= 0:
            lit_since = None
        if lit_since is not None and t[k] - lit_since < ign_delay:
            target = 0.0
        else:
            target = c
        if target > 0:
            dF = (target - F[k - 1]) / tau * dt
            dF = np.clip(dF, -slew * dt, slew * dt)
            F[k] = F[k - 1] + dF
        else:
            F[k] = F[k - 1] * np.exp(-dt / 0.035)
    return F


def map_columns(F):
    tab = r.tables()
    D0 = 0.030
    mox = np.array([_bilin(tab["Fg"], tab["Dg"], tab["mox"], f, D0) if f > 1 else 0.0 for f in F])
    mf = np.array([_bilin(tab["Fg"], tab["Dg"], tab["mf"], f, D0) if f > 1 else 0.0 for f in F])
    pc = np.array([_bilin(tab["Fg"], tab["Dg"], tab["pc"], f, D0) if f > 1 else 1.0e5 for f in F])
    return mox, mf, pc


def tethered_hover_dc(m_vehicle=13.0):
    dt = 0.01
    t = np.arange(0.0, 50.0, dt)
    W = m_vehicle * G0
    c = np.zeros_like(t)
    gx = np.zeros_like(t); gy = np.zeros_like(t)
    for k, tt in enumerate(t):
        if tt < 0.05:
            c[k] = 0
        elif tt < 2.5:
            c[k] = 100.0                      # ignition and floor check on the pad
        elif tt < 4.5:
            c[k] = 100.0 + (0.85 * W - 100.0) * (tt - 2.5) / 2.0
        elif tt < 5.5:
            c[k] = 0.85 * W + (1.08 * W - 0.85 * W) * (tt - 4.5)
        elif tt < 22.0:
            c[k] = 1.0 * W * (1 - 0.004 * (tt - 5.5))     # hover, mass falling ~0.08 kg/s
            if 9.0 <= tt < 13.0:                          # throttle doublets +-8 % for system ID
                c[k] *= 1.08 if int((tt - 9.0) / 1.0) % 2 == 0 else 0.92
            if 14.0 <= tt < 20.0:                         # gimbal chirp 0.5 -> 4 Hz, +-2 deg, x then y
                f = 0.5 + (4.0 - 0.5) * (tt - 14.0) / 6.0
                ph = 2 * np.pi * (0.5 * (tt - 14.0) + 0.5 * (3.5 / 6.0) * (tt - 14.0) ** 2)
                if tt < 17.0:
                    gx[k] = 2.0 * np.sin(ph)
                else:
                    gy[k] = 2.0 * np.sin(ph)
        elif tt < 25.0:
            c[k] = 0.9 * W
        elif tt < 27.0:
            c[k] = 100.0
        elif tt < 37.0:
            c[k] = 0.0                                    # shutdown, 10 s pause
        elif tt < 39.0:
            c[k] = 100.0                                  # relight at floor
        elif tt < 45.0:
            c[k] = 1.02 * W
        elif tt < 46.5:
            c[k] = 100.0
        else:
            c[k] = 0.0
    F = engine_response(t, c)
    mox, mf, pc = map_columns(F)
    rows = np.column_stack([t, F, c, F / 500.0, mox, mf, pc, np.full_like(t, np.nan), np.full_like(t, np.nan),
                            np.full_like(t, np.nan), np.full_like(t, np.nan), np.full_like(t, np.nan),
                            np.full_like(t, m_vehicle), np.full_like(t, np.nan), np.full_like(t, np.nan),
                            np.full_like(t, np.nan), gx, gy, np.full_like(t, 20)])
    meta = dict(name="DC-C_tethered_hover_v1", source="DERIVED designed test sequence through GNC engine model "
                "(tau 45.5 ms, slew 2500 N/s, ignition delay 0.4 s)", m_vehicle_kg=m_vehicle,
                total_impulse_Ns=float(np.trapezoid(F, t)), burn_time_s=float(np.sum(F > 5) * dt), starts=2,
                note="tether limits height to ~1 m; hover thrust ~W; throttle doublets +-8 %; gimbal chirp "
                     "0.5-4 Hz +-2 deg; shutdown + relight at 37 s. Tank columns NaN (ground-fed or flight tank "
                     "per test plan).")
    return rows, meta


def static_fire_dc():
    dt = 0.01
    seg = []   # (duration, thrust_cmd(t_local) callable, gimbal (gx, gy) callable)
    Z = lambda tl: (0.0, 0.0)  # noqa: E731
    seg.append((0.5, lambda tl: 0.0, Z))
    seg.append((3.0, lambda tl: 500.0, Z))                                           # start 1, full thrust
    for lvl in [400, 300, 200, 100, 62.5, 100]:
        seg.append((1.5, (lambda L: (lambda tl: L))(lvl), Z))                        # throttle staircase
    for _ in range(2):
        seg.append((1.0, lambda tl: 500.0, Z)); seg.append((1.0, lambda tl: 100.0, Z))  # large steps
    for f in [0.5, 1.0, 2.0, 4.0]:
        seg.append((2.0, (lambda fr: (lambda tl: 300.0 + 100.0 * np.sin(2 * np.pi * fr * tl)))(f), Z))
    seg.append((2.0, lambda tl: 500.0, lambda tl: (7.0 * np.sin(2 * np.pi * 0.5 * tl), 0.0)))   # gimbal x sweep
    seg.append((2.0, lambda tl: 500.0, lambda tl: (0.0, 7.0 * np.sin(2 * np.pi * 0.5 * tl))))   # gimbal y sweep
    seg.append((2.0, lambda tl: 500.0, lambda tl: (7.0 * np.cos(2 * np.pi * 0.5 * tl),
                                                    7.0 * np.sin(2 * np.pi * 0.5 * tl))))      # circle
    seg.append((2.0, lambda tl: 100.0, lambda tl: (7.0 * np.sin(2 * np.pi * 0.5 * tl), 0.0)))   # floor + gimbal
    seg.append((10.0, lambda tl: 0.0, Z))                                            # shutdown, coast
    seg.append((2.0, lambda tl: 100.0, Z))                                           # start 2 (relight) at floor
    seg.append((6.0, lambda tl: 100.0 + 330.0 * max(0.0, 1.0 - abs(tl - 2.0) / 4.0), Z))  # landing-burn shape
    seg.append((8.0, lambda tl: 0.0, Z))
    seg.append((2.0, lambda tl: 100.0, Z))                                           # start 3 at floor
    seg.append((8.0, lambda tl: 130.0, Z))                                           # long near-hover dwell
    seg.append((1.0, lambda tl: 0.0, Z))
    t_all, c_all, gx_all, gy_all = [], [], [], []
    t0 = 0.0
    for dur, fc, fg in seg:
        tl = np.arange(0.0, dur, dt)
        t_all.append(t0 + tl)
        c_all.append(np.array([fc(x) for x in tl]))
        gg = np.array([fg(x) for x in tl])
        gx_all.append(gg[:, 0]); gy_all.append(gg[:, 1])
        t0 += dur
    t = np.concatenate(t_all); c = np.concatenate(c_all)
    gx = np.concatenate(gx_all); gy = np.concatenate(gy_all)
    F = engine_response(t, c)
    mox, mf, pc = map_columns(F)
    nanv = np.full_like(t, np.nan)
    rows = np.column_stack([t, F, c, F / 500.0, mox, mf, pc, nanv, nanv, nanv, nanv, nanv, nanv, nanv, nanv, nanv,
                            gx, gy, np.full_like(t, 20)])
    meta = dict(name="DC-D_static_fire_qualification_v1",
                source="DERIVED qualification sequence through GNC engine model; stretch floor 62.5 N step included",
                total_impulse_Ns=float(np.trapezoid(F, t)), burn_time_s=float(np.sum(F > 5) * dt), starts=3,
                note="Qualification covers: full thrust, staircase to the 12.5 % stretch floor, floor<->100 % "
                     "steps, throttle sines 0.5-4 Hz, +-7 deg gimbal sweeps and circle at full thrust and at the "
                     "floor, 3 starts (relight after 10 s and 8 s), a landing-burn-shaped profile and an 8 s "
                     "near-hover dwell. Accumulated burn >= 1.25 x the longest flight duty (see index).")
    return rows, meta


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


def main(m_n2o_a1=1.30, m_n2o_a2=1.75, m_n2o_b=2.35):
    idx = {"version": "duty_cycles v1", "date": "2026-10-11", "owner": "Space/GNC",
           "units": "SI; throttle_frac = F / 500 N; a_axial_specific = specific force along body axis",
           "phase_codes": PHASE_NAMES, "cycles": []}
    pkA1 = dict(profile=0, h_target=300.0, descent="drogue", drogue_CdA=0.5, kd=0.6, t_ign_est=0.6)
    pkA2 = dict(profile=0, h_target=300.0, t_ign_est=0.6)
    for name, pk, m in [("DC-A1_full_flight_drogue_300m_v1", pkA1, m_n2o_a1),
                        ("DC-A2_full_flight_freefall_300m_v1", pkA2, m_n2o_a2),
                        ("DC-B1_hop_100m_floor20_v1", dict(profile=1, h_target=100.0), m_n2o_b),
                        ("DC-B2_hop_50m_floor20_v1", dict(profile=1, h_target=50.0), m_n2o_b)]:
        rows, meta = flight_dc(name, pk, m)
        idx["cycles"].append(write(name, rows, meta))
    rows, meta = tethered_hover_dc()
    idx["cycles"].append(write(meta["name"], rows, meta))
    rows, meta = static_fire_dc()
    idx["cycles"].append(write(meta["name"], rows, meta))
    longest = max(c["burn_time_s"] for c in idx["cycles"] if c["name"].startswith("DC-A") or c["name"].startswith("DC-B"))
    idx["longest_flight_burn_s"] = longest
    with open(os.path.join(OUT, "duty_cycles_index_v1.json"), "w") as f:
        json.dump(idx, f, indent=1, default=float)
    for c in idx["cycles"]:
        print(f"{c['name']:42s} burn {c['burn_time_s']:6.2f} s  I {c['total_impulse_Ns']:7.0f} N s  starts {c.get('starts')}")
    print("longest flight burn", round(longest, 2))
    return idx


if __name__ == "__main__":
    main()
