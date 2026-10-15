"""m2_drogue_window v1 (GNC, 2026-10-13): A1 time available under the drogue before the relight command, and the body-axis
specific force over that window, for option (d) (early main-valve opening under the drogue; lead request 2026-10-13 after
Electronics' REV-GNC-1 answers: "the time available from drogue inflation to the relight command (p01 / p50), and the f_z
history over that window, so Combustion can size the migration").

Flights: the 500 Monte Carlo runs of the A1 baseline v28_liq_p0.81_A1_none_k2 re-flown with the 1 ms recorder, exactly as
m2_coast_accel_a1 v1 (same configuration, stations, specific-force reconstruction; every run checked against its Monte Carlo
row). Window: drogue deployment (sim6 phase 3, at the ESTIMATED apogee) to the relight command (sim6 t_relight). sim6 has a
quasi-steady massless canopy: no inflation time, opening or snatch load. The window from INFLATION is therefore the window below
minus the real inflation time (UNKNOWN; TO-DEFINE from the drogue design or a drop test) and the f_z below has no opening
transient.
Planning-value dependence: the relight command moves earlier when the planning value grows (the stopping-distance rule plans on
the latest ignition). The shift is read run by run from the Monte Carlo tables of the same draws (relight_v28 / relight_seg44
case CSVs, column t_relight) for the planning values flown there.
Outputs (GNC_DW_OUT, default out/drogue_window): drogue_window_v1.json, drogue_window_envelope_v1.csv (f_z at the seat and at the
main valve, p01 / p50 / p99 against the time since the drogue deployment), drogue_window_runs_v1.csv.
Env: GNC_IFACE, GNC_ACT_RATE (as m2_coast_accel_a1), GNC_DW_OUT, GNC_DW_N (500)."""
import csv
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_coast_accel_a1 as CA  # noqa: E402  (sets the GNC_* defaults of the A1 baseline; run6 / sim6)

VERSION = "m2_drogue_window v1"
R, s6, V = CA.R, CA.s6, CA.V
OUT = os.environ.get("GNC_DW_OUT", f"{CA.S}/drogue_window")
NRUN = int(os.environ.get("GNC_DW_N", "500"))
DT, GRID, G0 = CA.DT, CA.GRID, CA.G0
SEG44 = f"{CA.S}/relight_seg44"
PLANS = ((0.91, "liq"), (1.01, "liq"), (1.09, "liq"), (1.21, "liq"), (1.48, "liqP"))
LEVELS = (0.5, 0.8, 0.9)        # settled-acceleration levels [g] for the continuous time before the relight command (descriptive)


def cont_above(t, g, level, t_end):
    """time from the last sample below `level` [g] to t_end (continuous time above the level just before the relight command)."""
    k = np.where(g < level)[0]
    return float(t_end - t[k[-1]]) if len(k) else float(t_end - t[0])


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    case, cfg, D, mc_rows, ncfg, med = CA.fly_case()
    res, rec, info = R.fly(dict(ncfg, noise=False, wind=0.0, gust=False, rec_dt=DT), nrec=120000)
    st = CA.stations(info)
    k = int(round(GRID / DT))
    runs, env_seat, env_mv, mism = [], [], [], 0
    for i in range(NRUN):
        c, disp = R.run_cfg(cfg, D[i])
        res, rec, _ = R.fly(dict(c, rec_dt=DT), disp, nrec=120000)
        mrow = mc_rows[i]
        bad = [f for f in mrow if f in s6.RES_NAMES and f != "nrec" and not (float(mrow[f]) == float(res[f]) or
                                                                         (np.isnan(float(mrow[f])) and np.isnan(float(res[f]))))]
        mism += int(bool(bad))
        w = CA.window(res, rec, st)
        if w is None or not np.isfinite(w["t_dro"]):
            runs.append(dict(run=i, window=None))
            continue
        t = w["t"]
        dd = t >= w["t_dro"]
        td, fs, fm = t[dd], w["fz_seat"][dd], w["fz_mv"][dd]
        g = fs / G0
        r = dict(run=i, success=bool(R.success(res)), reproduces_mc_row=not bad, t_apogee_s=w["t_apo"], t_drogue_s=w["t_dro"],
                 t_relight_cmd_s=w["tr"], h_drogue_m=float(w["h"][dd][0]), h_relight_cmd_m=float(w["h"][-1]),
                 vz_relight_cmd_mps=float(w["vz"][-1]),
                 drogue_to_relight_cmd_s=float(w["tr"] - w["t_dro"]), fz_seat_mean_mps2=float(fs.mean()),
                 fz_seat_min_mps2=float(fs.min()), t_fz_seat_min_after_drogue_s=float(td[int(np.argmin(fs))] - w["t_dro"]),
                 fz_seat_p05_mps2=float(np.percentile(fs, 5)), time_fz_le_0_s=float(np.sum(fs <= 0.0) * DT),
                 fz_mv_mean_mps2=float(fm.mean()), fz_mv_min_mps2=float(fm.min()),
                 fz_seat_first_1s_mean_mps2=float(fs[td < w["t_dro"] + 1.0].mean()),
                 fz_seat_last_1s_mean_mps2=float(fs[td >= w["tr"] - 1.0].mean()))
        for L in LEVELS:
            r[f"continuous_above_{L:g}g_before_cmd_s"] = cont_above(td, g, L, w["tr"])
        runs.append(r)
        idx = np.arange(0, len(td), k)
        env_seat.append(fs[idx])
        env_mv.append(fm[idx])
        if (i + 1) % 100 == 0:
            print(f"  {i + 1} runs ({time.time() - t0:.0f} s)", flush=True)
    ok = [r for r in runs if r.get("window", 1) is not None]
    L_ = max(len(x) for x in env_seat)
    A = np.full((len(env_seat), L_), np.nan)
    B = np.full((len(env_mv), L_), np.nan)
    for j, (a, b) in enumerate(zip(env_seat, env_mv)):
        A[j, :len(a)] = a
        B[j, :len(b)] = b
    n = np.sum(np.isfinite(A), axis=0)
    p_env = os.path.join(OUT, "drogue_window_envelope_v1.csv")
    with open(p_env, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["t_since_drogue_deploy_s", "n_runs", "fz_seat_p01_mps2", "fz_seat_p50_mps2", "fz_seat_p99_mps2",
                     "fz_mv_p01_mps2", "fz_mv_p50_mps2", "fz_mv_p99_mps2"])
        for j in range(L_):
            if n[j] < 5:
                continue
            wr.writerow([f"{j * GRID:.3f}", int(n[j])] + [f"{np.nanpercentile(A[:, j], q):.5g}" for q in (1, 50, 99)] +
                        [f"{np.nanpercentile(B[:, j], q):.5g}" for q in (1, 50, 99)])
    p_runs = os.path.join(OUT, "drogue_window_runs_v1.csv")
    keys = list(ok[0].keys())
    with open(p_runs, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=keys)
        wr.writeheader()
        for r in ok:
            wr.writerow(r)

    def pct(key):
        x = np.array([r[key] for r in ok], float)
        return dict(p01=float(np.percentile(x, 1)), p05=float(np.percentile(x, 5)), p50=float(np.percentile(x, 50)),
                    p99=float(np.percentile(x, 99)), min=float(x.min()), max=float(x.max()), n=int(len(x)))
    stats = {kk: pct(kk) for kk in keys if kk not in ("run", "success", "reproduces_mc_row")}
    # planning-value dependence of the relight command time (same draws, Monte Carlo tables)
    base = list(csv.DictReader(open(os.path.join(V.OUT, f"mc6_runs_{case}_v28.csv"))))
    t_b = np.array([float(r["t_relight"]) for r in base])
    shift = {}
    for pl, stt in PLANS:
        p = os.path.join(SEG44, f"mc6_runs_v31_{stt}_p{pl:.2f}_A1_none_k2.csv")
        if not os.path.exists(p):
            shift[f"{pl:.2f}"] = None
            continue
        rr = list(csv.DictReader(open(p)))
        tt = np.array([float(r["t_relight"]) for r in rr])
        m = (tt > 0) & (t_b > 0)
        dlt = tt[m] - t_b[m]
        win = np.array([r["drogue_to_relight_cmd_s"] for r in ok])
        shift[f"{pl:.2f}"] = dict(case=os.path.basename(p), n=int(m.sum()), dt_cmd_s_p01_p50_p99=[float(np.percentile(dlt, q)) for q in (1, 50, 99)],
                                  window_s_p01_p50=[float(np.percentile(win + np.median(dlt), 1)), float(np.percentile(win + np.median(dlt), 50))],
                                  note="window shifted by the median command-time change (same runs)")
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE, mc_case=case, n_runs=NRUN, seed=101,
               request=("lead 2026-10-13 (option d, early MV opening under the drogue): time available from drogue inflation to "
                        "the relight command (p01 / p50) and the f_z history over that window"),
               configuration=dict(base="A1_none (gnc.json v3 A1 baseline, no throat growth)", fsw="v2.7 provisional, k_est_asc 2, ratchet",
                                  relight_planning_value_s=CA.PLAN, drogue="nose drogue, CdA 0.5 m2 x U(0.85, 1.15) (ASSUMED), "
                                  "deployed at the estimated apogee"),
               stations=st, checks=dict(runs_reproducing_mc_row=NRUN - mism, of=NRUN, runs_with_window=len(ok)),
               window_definition=("drogue deployment (sim6 phase 3 at the estimated apogee) to the relight command; sim6 has no "
                                  "inflation time: subtract the real inflation time (UNKNOWN, TO-DEFINE) to get the window from inflation"),
               stats=stats, plan_dependence=shift,
               sign="f_z > 0 = apparent gravity toward the engine end (liquid settles aft toward the seat, vapour is driven forward)",
               limitations=["no canopy inflation, opening or snatch load (quasi-steady massless canopy)",
                            "rigid-body specific force; no line fluid dynamics", "main-valve station ASSUMED (GNC ledger)",
                            "planning value 0.81 s; a later plan moves the relight command earlier (plan_dependence)"],
               files=dict(envelope=os.path.basename(p_env), runs=os.path.basename(p_runs)),
               tags=dict(values="SIM (sim6/run6 v2.7.1-dev 6-DOF Monte Carlo)", inflation_time="UNKNOWN"), cpu_s=time.time() - t0)
    with open(os.path.join(OUT, "drogue_window_v1.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for kk in ("drogue_to_relight_cmd_s", "fz_seat_mean_mps2", "fz_seat_min_mps2", "time_fz_le_0_s", "continuous_above_0.5g_before_cmd_s",
               "continuous_above_0.9g_before_cmd_s", "h_drogue_m", "h_relight_cmd_m", "vz_relight_cmd_mps"):
        print(kk, {q: round(v, 3) for q, v in stats[kk].items()}, flush=True)
    print("plan dependence", json.dumps(shift), flush=True)
    print("wrote", OUT, f"({time.time() - t0:.0f} s), mismatches {mism}", flush=True)


if __name__ == "__main__":
    main()
