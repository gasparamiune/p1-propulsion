"""m2_coast_accel_a1 v1 (GNC, 2026-10-13): A1 body-axis specific force from MECO to the relight command, nominal and 500-run
dispersed (Combustion request relayed by the lead 2026-10-13: does vapour in the MV-to-seat segment vent toward the tank or stay
trapped at the engine end during the coast and the drogue descent; Combustion's in-flight criterion: retained vapour <= 19 cm3).

Configuration: the A1 baseline of the v2.8 relight study (m2_relight_v28 case v28_liq_p0.81_A1_none_k2): profile A-D 300 m, nose
drogue + aft fins, FSW v2.7 provisional (k_est_asc 2, ratchet), relight planning value 0.81 s (REQ lead 2026-10-13), liquid-line
start-delay table (Combustion RC-03 E0->E2), N2O 2.00 kg, no throat growth, pc2 configuration; iface_v3c; sim6/run6 v2.7.1-dev.
Dispersed: the 500 Monte Carlo runs of that case (seed 101; start-delay generator 20261018) re-flown with the 1 ms recorder; every
run is checked field by field against its Monte Carlo CSV row. Nominal: no dispersion, no wind, no sensor noise, start delay =
median of the liquid-line table (the m2_relight_v28 nominal convention).

Quantity: specific force f = non-gravitational force / mass in body axes (what an ideal accelerometer reads). Body +z points to
the nose (thrust direction). f_z at the CG = sim6 fb[2] (recorded 'fax'); f_x, f_y are reconstructed from the recorded inertial
velocity and attitude, f = R(q)^T (dv/dt + g z_world), and the same reconstruction of f_z is checked against 'fax'. At a body
station z_s on the axis: f_s = f_CG + alpha x r + w x (w x r), r = (0, 0, z_s - z_cg) (gimbal deflection of the seat and the CG
lateral offset, 2 mm sd, neglected).
Stations: pintle seat z = z_pivot + z_seat (mechanical.json v2 envelope.stations_from_pivot_m.z_seat, DERIVED+ESTIMATE); main
valve z = GNC mass-ledger placement of P09 'NC isolation valve' (tank bottom - 0.05 m, ASSUMED: mechanical.json v2 gives no
station for the isolation valve).
Sign: f_z > 0 = apparent gravity toward the engine end: liquid settles aft toward the seat, vapour is driven forward toward the
main valve and the tank. f_z < 0 = vapour driven aft toward the seat (engine end). Whether the vapour vents or is trapped, and
the 19 cm3 criterion, are Combustion's judgement (line routing, high points, valve state, surface tension).
Window: MECO command (sim6 t_meco; it starts the shutdown tail-off) to the relight command (sim6 t_relight, phase 4 entry; the
light follows after the start delay). Sub-phases: tail-off (delivered thrust > 1 N after MECO), coast up (to the true apogee,
first vz < 0), drogue descent (drogue deployed at the ESTIMATED apogee, sim6 phase 3; quasi-steady massless canopy: no inflation
time, opening or snatch load modelled; the drogue stays attached until the relight thrust exceeds half the floor).
Model limits: the liquid in the 6-DOF is a settled column with an axial slosh mass (no free-surface or line fluid dynamics); the
specific force is a rigid-body quantity.
Env: GNC_IFACE, GNC_ACT_RATE, GNC_CA_OUT (out/coast_accel_a1), GNC_CA_N (500), GNC_V28_OUT (out/relight_v28).
Outputs: coast_accel_a1_v1.json, coast_accel_a1_envelope_meco_v1.csv, coast_accel_a1_envelope_relight_v1.csv,
coast_accel_a1_runs_v1.csv, coast_accel_a1_series_v1.csv."""
import csv
import json
import os
import sys
import time
import numpy as np

os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_relight_v28 as V  # noqa: E402

VERSION = "m2_coast_accel_a1 v1"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_CA_OUT", f"{S}/coast_accel_a1")
NRUN = int(os.environ.get("GNC_CA_N", "500"))
PLAN = 0.81              # REQ lead 2026-10-13: relight planning value of the v2.8 design
BASE = "A1_none"
DT = 1.0e-3              # sim step and recorder step [s]
GRID = 0.010             # output grid [s]
G0 = s6.G0
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
LEVELS_G = (-0.1, 0.0, 0.1, 0.5)   # time-below levels for f_z [g] (descriptive; no criterion implied)


def stations(info):
    mech = R.sources()["mech"]
    zs = float(mech["envelope"]["stations_from_pivot_m"]["z_seat"]["v"])
    z_seat = float(info["z_pivot"]) + zs
    mv = [it for it in info["ledger"] if str(it.get("name", "")).startswith("P09")]
    z_mv = float(mv[0]["z"]) if mv else float(info["geo"]["tank_z_bot_inner"]) - 0.05
    return dict(z_pivot_m=float(info["z_pivot"]), z_seat_from_pivot_m=zs, z_seat_m=z_seat, z_mv_m=z_mv,
                z_seat_tag="DERIVED+ESTIMATE mechanical.json v2 (envelope.stations_from_pivot_m.z_seat + frames.rv1_station_of_pivot_m)",
                z_mv_tag="ASSUMED GNC mass ledger P09 placement (tank bottom - 0.05 m); no isolation-valve station in mechanical.json v2")


def specific_force(rec):
    """body-axis specific force [m/s2] at the CG for records 1..n-1 from dv/dt and the attitude of the previous record (the
    attitude the sim used for that step); returns fx, fy, fz (length n-1) and the record gaps (dt > 1.5 ms)."""
    t = rec[:, I["t"]]
    v = rec[:, [I["vx"], I["vy"], I["vz"]]]
    dt = np.diff(t)
    a = np.diff(v, axis=0) / dt[:, None]
    a[:, 2] += G0
    w, x, y, z = (rec[:-1, I[k]] for k in ("q0", "q1", "q2", "q3"))
    A, B, C = a[:, 0], a[:, 1], a[:, 2]
    fx = (1 - 2 * (y * y + z * z)) * A + 2 * (x * y + w * z) * B + 2 * (x * z - w * y) * C
    fy = 2 * (x * y - w * z) * A + (1 - 2 * (x * x + z * z)) * B + 2 * (y * z + w * x) * C
    fz = 2 * (x * z + w * y) * A + 2 * (y * z - w * x) * B + (1 - 2 * (x * x + y * y)) * C
    return fx, fy, fz, int(np.sum(dt > 1.5 * DT))


def at_station(fx, fy, fz, wx, wy, wz, ax, ay, r):
    """specific force at a body station on the axis, r = z_s - z_cg (arrays)."""
    return fx + ay * r + wx * wz * r, fy - ax * r + wy * wz * r, fz - (wx * wx + wy * wy) * r


def window(res, rec, st):
    """per-run window arrays (1 ms) from the MECO command to the relight command; None when either is missing."""
    t = rec[:, I["t"]]
    tm, tr = float(res["t_meco"]), float(res["t_relight"])
    if not (tm > 0.0 and tr > tm):
        return None
    fx, fy, fz, gaps = specific_force(rec)
    k = np.arange(1, len(t))                       # records with a reconstructed specific force
    sel = k[(t[k] >= tm) & (t[k] < tr)]
    j = sel - 1                                    # index into fx/fy/fz
    tt = t[sel]
    wx, wy, wz = rec[sel, I["wx"]], rec[sel, I["wy"]], rec[sel, I["wz"]]
    gw = [np.gradient(rec[:, I[c]], t) for c in ("wx", "wy")]
    ax, ay = gw[0][sel], gw[1][sel]
    zcg = rec[sel, I["zcg"]]
    fax = rec[sel, I["fax"]]
    sx, sy, sz = at_station(fx[j], fy[j], fz[j], wx, wy, wz, ax, ay, st["z_seat_m"] - zcg)
    mx, my, mz = at_station(fx[j], fy[j], fz[j], wx, wy, wz, ax, ay, st["z_mv_m"] - zcg)
    vz = rec[sel, I["vz"]]
    ph = rec[sel, I["phase"]]
    F = rec[sel, I["F"]]
    i_apo = np.where(vz < 0.0)[0]
    t_apo = float(tt[i_apo[0]]) if len(i_apo) else float("nan")
    i_dro = np.where(ph >= 3)[0]
    t_dro = float(tt[i_dro[0]]) if len(i_dro) else float("nan")
    i_off = np.where(F > 1.0)[0]
    t_toff_end = float(tt[i_off[-1]]) + DT if len(i_off) else tm
    return dict(t=tt, tm=tm, tr=tr, t_apo=t_apo, t_dro=t_dro, t_toff_end=t_toff_end, fz_cg=fax, fz_rec=fz[j], fx=fx[j],
                fy=fy[j], fz_seat=sz, flat_seat=np.hypot(sx, sy), fz_mv=mz, flat_mv=np.hypot(mx, my), wmag=np.sqrt(wx * wx + wy * wy + wz * wz),
                h=rec[sel, I["z"]], vz=vz, phase=ph, F=F, gaps=gaps)


def describe(w):
    """per-run descriptors on the seat-station axial specific force (1 ms samples)."""
    t, f = w["t"], w["fz_seat"]
    g = f / G0
    up = (t >= w["t_toff_end"]) & (t < (w["t_apo"] if np.isfinite(w["t_apo"]) else w["tr"]))
    dd = t >= (w["t_dro"] if np.isfinite(w["t_dro"]) else w["tr"])
    adverse = np.where(f <= 0.0)[0]
    t_last_adv = float(t[adverse[-1]]) if len(adverse) else float(w["tm"])
    below_half = np.where(g < 0.5)[0]
    t_last_half = float(t[below_half[-1]]) if len(below_half) else float(w["tm"])
    lat_ang = np.degrees(np.arctan2(w["flat_seat"], np.abs(f)))
    out = dict(t_meco_s=w["tm"], t_tailoff_end_s=w["t_toff_end"], t_apogee_s=w["t_apo"], t_drogue_s=w["t_dro"],
               t_relight_cmd_s=w["tr"], window_s=w["tr"] - w["tm"], coast_up_s=(w["t_apo"] - w["t_toff_end"]),
               descent_s=(w["tr"] - w["t_dro"]),
               fz_seat_min_mps2=float(f.min()), t_fz_seat_min_s=float(t[int(np.argmin(f))]),
               fz_seat_coast_up_mean_mps2=float(f[up].mean()) if up.any() else None,
               fz_seat_coast_up_min_mps2=float(f[up].min()) if up.any() else None,
               fz_seat_descent_mean_mps2=float(f[dd].mean()) if dd.any() else None,
               fz_seat_descent_min_mps2=float(f[dd].min()) if dd.any() else None,
               descent_time_fz_below_0_s=float(np.sum(f[dd] <= 0.0) * DT) if dd.any() else None,
               fz_mv_min_mps2=float(w["fz_mv"].min()), fz_mv_descent_min_mps2=float(w["fz_mv"][dd].min()) if dd.any() else None,
               fz_seat_last_1s_mean_mps2=float(f[t >= w["tr"] - 1.0].mean()),
               adverse_impulse_mps=float(np.sum(np.minimum(f, 0.0)) * DT),
               settled_before_relight_s=float(w["tr"] - t_last_adv),
               above_half_g_before_relight_s=float(w["tr"] - t_last_half),
               lateral_angle_max_deg_when_fz_gt_0p1g=float(lat_ang[g > 0.1].max()) if (g > 0.1).any() else None,
               flat_seat_max_mps2=float(w["flat_seat"].max()), rate_max_dps=float(np.degrees(w["wmag"].max())),
               seat_minus_cg_fz_maxabs_mps2=float(np.max(np.abs(f - w["fz_cg"]))),
               mv_minus_seat_fz_maxabs_mps2=float(np.max(np.abs(w["fz_mv"] - f))),
               recon_fz_vs_fax_maxabs_mps2=float(np.max(np.abs(w["fz_rec"] - w["fz_cg"]))), record_gaps=w["gaps"])
    for L in LEVELS_G:
        out[f"time_fz_below_{L:g}g_s"] = float(np.sum(g < L) * DT)
    return out


def grid_values(w, align):
    """values on the 10 ms grid: align 'meco' -> t - t_meco = 0, 0.01, ...; 'relight' -> t - t_relight = -0.01, -0.02, ..."""
    k = int(round(GRID / DT))
    if align == "meco":
        idx = np.arange(0, len(w["t"]), k)
    else:
        idx = np.arange(len(w["t"]) - 1, -1, -k)
    return idx


def fly_case():
    tabs = V.e0e2_tables()
    over = V.case_over(BASE, "liq", PLAN, tabs)
    cfg = R.cfg_of(**dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(over["m_fixed"])))
    case = V.cname(BASE, "liq", PLAN)
    mc_rows = list(csv.DictReader(open(os.path.join(V.OUT, f"mc6_runs_{case}_v28.csv"))))
    D = R.draw(np.random.default_rng(101), 500, cfg)
    q = tabs["liq"]["quantiles_5pct_s"]
    med = float(np.interp(0.5, np.linspace(0, 1, 21), q))
    ncfg = R.cfg_of(**dict({k: v for k, v in V.base_over(BASE).items() if k != "m_fixed"}, t_ign=med, t_ign_est=PLAN,
                           m_n2o=PC.M_TANK))
    return case, cfg, D, mc_rows, ncfg, med


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    case, cfg, D, mc_rows, ncfg, med = fly_case()
    res, rec, info = R.fly(dict(ncfg, noise=False, wind=0.0, gust=False, rec_dt=DT), nrec=120000)
    st = stations(info)
    wn = window(res, rec, st)
    nominal = dict(describe(wn), success=R.success(res), start_delay_s=med)
    series = {"nominal": wn}
    print(f"nominal: MECO {wn['tm']:.3f} s apogee {wn['t_apo']:.3f} s drogue {wn['t_dro']:.3f} s relight cmd {wn['tr']:.3f} s; "
          f"fz_seat min {nominal['fz_seat_min_mps2']:.3f} m/s2; recon check {nominal['recon_fz_vs_fax_maxabs_mps2']:.2e}", flush=True)
    runs, wins, mism_runs = [], {}, []
    G_meco, G_rel = [], []
    for i in range(NRUN):
        c, disp = R.run_cfg(cfg, D[i])
        res, rec, info_i = R.fly(dict(c, rec_dt=DT), disp, nrec=120000)
        mrow = mc_rows[i]
        mism = [k for k in mrow if k in s6.RES_NAMES and k != "nrec" and not (float(mrow[k]) == float(res[k]) or
                                                             (np.isnan(float(mrow[k])) and np.isnan(float(res[k]))))]
        if mism:
            mism_runs.append(dict(run=i, fields=mism[:8]))
        w = window(res, rec, st)
        row = dict(run=i, run_seed=int(D[i]["_seed"]), success=bool(R.success(res)), reproduces_mc_row=not mism,
                   start_delay_s=float(D[i]["_t_ign_q"]), wind_mps=float(D[i]["_wind"]), drogue_f=float(D[i]["drogue_f"]),
                   T0_K=float(D[i]["_T0"]))
        if w is None:
            row["window"] = None
            runs.append(row)
            continue
        row.update(describe(w))
        runs.append(row)
        for align, store in (("meco", G_meco), ("relight", G_rel)):
            idx = grid_values(w, align)
            store.append(np.column_stack([w["fz_seat"][idx], w["fz_cg"][idx], w["flat_seat"][idx], w["fz_mv"][idx]]))
        wins[i] = w
        if (i + 1) % 50 == 0:
            print(f"  {i + 1} runs ({time.time() - t0:.0f} s)", flush=True)
    ok = [r for r in runs if r.get("window", 1) is not None]
    # extreme runs
    i_min = min(ok, key=lambda r: r["fz_seat_min_mps2"])["run"]
    i_adv = max(ok, key=lambda r: r["time_fz_below_0g_s"])["run"]
    i_set = min(ok, key=lambda r: r["fz_seat_descent_mean_mps2"] if r["fz_seat_descent_mean_mps2"] is not None else 1e9)["run"]
    i_rel = min(ok, key=lambda r: r["settled_before_relight_s"])["run"]
    ext = {"min_accel_run (lowest instantaneous f_z at the seat)": i_min,
           "longest_adverse_run (longest time with f_z <= 0)": i_adv,
           "weakest_descent_run (lowest mean f_z over the drogue descent)": i_set,
           "shortest_settled_before_relight_run (shortest time from the last f_z <= 0 to the relight command)": i_rel}
    for lab, i in ext.items():
        series[f"run{i:03d}"] = wins[i]
    # envelopes
    def env(store, align):
        L = max(len(x) for x in store)
        A = np.full((len(store), L, 4), np.nan)
        for k, x in enumerate(store):
            A[k, :len(x)] = x
        n = np.sum(np.isfinite(A[:, :, 0]), axis=0)
        P = {q_: np.nanpercentile(A, q_, axis=0) for q_ in (1, 50, 99)}
        tgrid = np.arange(L) * GRID if align == "meco" else -(np.arange(L) * GRID + DT)
        cols = ["t_since_meco_s" if align == "meco" else "t_minus_relight_cmd_s", "n_runs",
                "fz_seat_p01_mps2", "fz_seat_p50_mps2", "fz_seat_p99_mps2", "fz_cg_p01_mps2", "fz_cg_p50_mps2", "fz_cg_p99_mps2",
                "flat_seat_p50_mps2", "flat_seat_p99_mps2", "fz_mv_p01_mps2", "fz_mv_p50_mps2", "fz_mv_p99_mps2",
                "fz_seat_nominal_mps2", "fz_seat_min_accel_run_mps2"]
        idn = grid_values(wn, align)
        nomv = np.full(L, np.nan)
        nomv[:len(idn)] = wn["fz_seat"][idn]
        wm = wins[i_min]
        idm = grid_values(wm, align)
        minv = np.full(L, np.nan)
        minv[:len(idm)] = wm["fz_seat"][idm]
        rows = []
        for k in range(L):
            if n[k] < 5:
                continue
            rows.append([tgrid[k], n[k], P[1][k, 0], P[50][k, 0], P[99][k, 0], P[1][k, 1], P[50][k, 1], P[99][k, 1],
                         P[50][k, 2], P[99][k, 2], P[1][k, 3], P[50][k, 3], P[99][k, 3], nomv[k], minv[k]])
        if align == "relight":
            rows = rows[::-1]
        return cols, rows
    files = {}
    for align, store in (("meco", G_meco), ("relight", G_rel)):
        cols, rows = env(store, align)
        p = os.path.join(OUT, f"coast_accel_a1_envelope_{align}_v1.csv")
        with open(p, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(cols)
            for r in rows:
                wr.writerow([("%.6g" % x) if np.isfinite(x) else "" for x in r])
        files[align] = p
    # per-run table
    keys = list(ok[0].keys())
    p = os.path.join(OUT, "coast_accel_a1_runs_v1.csv")
    with open(p, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        wr.writeheader()
        for r in runs:
            wr.writerow({k: r.get(k) for k in keys})
    files["runs"] = p
    # time series (10 ms) of the nominal and the extreme runs
    p = os.path.join(OUT, "coast_accel_a1_series_v1.csv")
    with open(p, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["series", "t_s", "t_since_meco_s", "t_minus_relight_cmd_s", "phase", "h_m", "vz_mps", "F_N", "fz_cg_mps2",
                     "fx_cg_mps2", "fy_cg_mps2", "fz_seat_mps2", "flat_seat_mps2", "fz_mv_mps2", "rate_dps"])
        for name, w in series.items():
            for k in grid_values(w, "meco"):
                wr.writerow([name] + ["%.6g" % x for x in (w["t"][k], w["t"][k] - w["tm"], w["t"][k] - w["tr"], w["phase"][k], w["h"][k],
                                                            w["vz"][k], w["F"][k], w["fz_cg"][k], w["fx"][k], w["fy"][k], w["fz_seat"][k],
                                                            w["flat_seat"][k], w["fz_mv"][k], np.degrees(w["wmag"][k]))])
    files["series"] = p

    def pct(key, rows=ok):
        x = np.array([r[key] for r in rows if r.get(key) is not None], float)
        return dict(p01=float(np.percentile(x, 1)), p50=float(np.percentile(x, 50)), p99=float(np.percentile(x, 99)),
                    min=float(x.min()), max=float(x.max()), n=int(len(x)))
    stats = {k: pct(k) for k in ("window_s", "coast_up_s", "descent_s", "fz_seat_min_mps2", "fz_seat_coast_up_mean_mps2",
                                 "fz_seat_coast_up_min_mps2", "fz_seat_descent_mean_mps2", "fz_seat_descent_min_mps2",
                                 "fz_seat_last_1s_mean_mps2", "adverse_impulse_mps", "settled_before_relight_s",
                                 "descent_time_fz_below_0_s", "fz_mv_min_mps2", "fz_mv_descent_min_mps2",
                                 "above_half_g_before_relight_s", "lateral_angle_max_deg_when_fz_gt_0p1g", "flat_seat_max_mps2",
                                 "rate_max_dps", "seat_minus_cg_fz_maxabs_mps2", "mv_minus_seat_fz_maxabs_mps2")}
    for L in LEVELS_G:
        stats[f"time_fz_below_{L:g}g_s"] = pct(f"time_fz_below_{L:g}g_s")
    rc = max(r["recon_fz_vs_fax_maxabs_mps2"] for r in ok)
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE, mc_case=case,
               mc_csv=os.path.relpath(os.path.join(V.OUT, f"mc6_runs_{case}_v28.csv"), S),
               mc_csv_hub=f"01-systems-gnc/results/relight_v28/mc6_runs_{case}_v28.csv.gz", n_runs=NRUN, seed=101,
               purpose=("Combustion request relayed by the lead 2026-10-13: A1 body-axis acceleration from MECO to the relight, "
                        "nominal and dispersed (p01/p50/p99 envelope and the min-accel run), to judge whether vapour in the "
                        "MV-to-seat segment vents toward the tank or stays trapped at the engine end (in flight retained vapour "
                        "<= 19 cm3, Combustion criterion)"),
               configuration=dict(profile="A-D 300 m, nose drogue + aft fins", fsw="v2.7 provisional, k_est_asc 2, ratchet",
                                  relight_planning_value_s=PLAN, start_delay="Combustion RC-03 E0->E2 liquid-line table "
                                  "(m2_relight_v28 e0e2_tables)", n2o_kg=PC.M_TANK, throat_growth="none",
                                  nominal_start_delay_s=med),
               stations=st,
               definitions=dict(
                   specific_force="non-gravitational force / mass in body axes (ideal accelerometer); body +z toward the nose",
                   fz_cg="sim6 fb[2] (recorded fax) at the CG",
                   fx_fy="reconstructed: R(q)^T (dv/dt + g z_world) from the recorded inertial velocity and attitude",
                   at_station="f_CG + alpha x r + w x (w x r), r = (0, 0, z_s - z_cg); seat gimbal deflection neglected",
                   sign="f_z > 0: apparent gravity toward the engine end (vapour driven forward toward the main valve / tank); "
                        "f_z < 0: vapour driven aft toward the seat",
                   window="sim6 t_meco (MECO command, start of the tail-off) to sim6 t_relight (relight command, phase 4); "
                          "the light follows after the start delay",
                   coast_up="tail-off end (last delivered thrust > 1 N) to the true apogee (first vz < 0)",
                   descent="drogue deployment (sim6 phase 3 at the estimated apogee) to the relight command",
                   settled_before_relight_s="relight command minus the last instant with f_z <= 0 at the seat",
                   above_half_g_before_relight_s="relight command minus the last instant with f_z < 0.5 g at the seat",
                   adverse_impulse_mps="integral of min(f_z, 0) over the window at the seat",
                   envelope="p01 / p50 / p99 over the runs whose window covers that instant (n_runs column), 10 ms grid, "
                            "aligned at MECO and, separately, at the relight command",
                   g=f"G0 = {G0} m/s2"),
               nominal=nominal,
               dispersed=stats,
               extreme_runs={lab: dict(run=i, **{k: v for k, v in runs[i].items() if k not in ("run",)}) for lab, i in ext.items()},
               checks=dict(runs_reproducing_mc_row=int(sum(r["reproduces_mc_row"] for r in runs)), of=len(runs),
                           mismatches=mism_runs[:10], runs_without_window=int(sum(1 for r in runs if r.get("window", 1) is None)),
                           success_rate=float(np.mean([r["success"] for r in runs])),
                           recon_fz_vs_fax_maxabs_mps2=rc, record_gaps_total=int(sum(r["record_gaps"] for r in ok))),
               limitations=[
                   "drogue: quasi-steady massless canopy deployed at the estimated apogee, no inflation time, opening or snatch "
                   "load (sim6 aero); a real deployment adds a transient (sign f_z > 0 for a nose-attached drogue on a "
                   "descending vehicle) that is not in these numbers (UNKNOWN amplitude)",
                   "liquid: settled column + axial slosh mass in the 6-DOF; no free-surface, bubble or line fluid dynamics",
                   "main-valve station ASSUMED (GNC ledger); the hose routing between the valve and the seat is not modelled; "
                   "the seat-to-valve difference in f_z is listed (mv_minus_seat_fz_maxabs_mps2) and is small against the "
                   "values themselves",
                   "tank temperature drawn U(15, 25) C (run6 _T0); the ARM range is 15-24 C (lead 2026-10-13); no effect on "
                   "the coast specific force beyond the burn history",
                   "MECO and relight logic of FSW v2.7 provisional; values change with the FSW, the drogue size (CdA 0.5 m2 x "
                   "U(0.85, 1.15), ASSUMED) and the apex"],
               files={k: os.path.basename(v) for k, v in files.items()},
               tags=dict(values="SIM (sim6/run6 v2.7.1-dev 6-DOF Monte Carlo)", stations="see stations", criterion_19cm3="Combustion"),
               cpu_s=time.time() - t0)
    with open(os.path.join(OUT, "coast_accel_a1_v1.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps(dict(nominal=nominal, extremes=ext, checks=out["checks"]), indent=1, default=float)[:4000], flush=True)
    for k in ("fz_seat_min_mps2", "fz_seat_coast_up_mean_mps2", "fz_seat_descent_mean_mps2", "settled_before_relight_s",
              "time_fz_below_0g_s", "coast_up_s", "descent_s"):
        print(k, stats[k], flush=True)
    print("wrote", OUT, f"({time.time() - t0:.0f} s)", flush=True)


if __name__ == "__main__":
    main()
