"""M2 Monte Carlo analysis (gnc.json v2): case table, paired comparisons, failure drivers, loads, plots.

Reads GNC_OUT/mc6_summary_<SUFFIX>.json and mc6_runs_<case>_<SUFFIX>.csv (scripts/m2_mc6.py).
Writes GNC_RES (default /home/claude/work/space/out/results_v2):
  mc6_cases_summary_v2.csv / .json   one row per case (success, Wilson 95 % CI, percentiles, loads, RCS use)
  mc6_paired_v2.csv                  McNemar exact test of each A-D variant against the baseline (same draws)
  mc6_failure_drivers_v2.csv         Spearman rank correlation with failure + medians in failed vs all runs
  PNG plots (touchdown scatter, case success with CI, success by wind, miss distance, sensitivity, loads,
  gimbal/7 deg decision, flight time line from the DC-A1 duty cycle)
Run: nice -n 10 python scripts/m2_analysis.py
"""
import csv
import json
import os
import sys
import numpy as np
from scipy.stats import binomtest, spearmanr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
DC = os.environ.get("GNC_DC_OUT", "/home/claude/work/space/out/duty_cycles_v2")
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
os.makedirs(RES, exist_ok=True)
BASE = "AD_fins_f20"
RCS_ISP_S = (50.0, 40.0, 65.0)   # ASSUMED N2O-vapour cold-gas Isp at sea level (nominal, low, high) [s]
RCS_THRUST_N = 1.0               # two 0.5 N nozzles fire together (one couple) [N] (run6 rcs_thrust x 2)


def load_rows(case):
    p = os.path.join(OUT, f"mc6_runs_{case}_{SUFFIX}.csv")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        rows = list(csv.DictReader(f))
    return [{k: float(v) if v not in ("", "nan") else np.nan for k, v in r.items()} for r in rows]


def wcsv(path, rows):
    keys = []
    for x in rows:
        for k in x:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for x in rows:
            w.writerow(x)


def pct(rows, key, p, landed=True):
    x = np.array([r[key] for r in rows if (r["landed"] > 0.5 or not landed) and np.isfinite(r[key])])
    return float(np.percentile(x, p)) if x.size else float("nan")


def main():
    S = json.load(open(os.path.join(OUT, f"mc6_summary_{SUFFIX}.json")))
    cases = S["cases"]
    data = {c: load_rows(c) for c in cases}
    base_rows = data.get(BASE)
    table = []
    paired = []
    for c, cs in cases.items():
        rows = data[c]
        if not cs.get("closes", True) or rows is None:
            table.append(dict(case=c, note=cs.get("note"), closes=False))
            continue
        s = cs["summary"]
        n = s["n"]
        k = int(round(s["success"] * n))
        rcs_t99 = s.get("rcs_time_p99", float("nan"))
        row = dict(case=c, note=cs["note"], vehicle=cs.get("vehicle"), sim=cs.get("sim", S.get("sim")),
                   engine_model=cs.get("engine_model", "combustion.json v1 map"), n=n, success=s["success"], ci95_lo=s["ci95"][0],
                   ci95_hi=s["ci95"][1], failures=n - k,
                   fail_modes=";".join(f"{a}:{b}" for a, b in sorted(s["fail_modes"].items())),
                   m_n2o_sized_kg=cs["m_n2o_sized_kg"], m_n2o_mc_kg=cs["m_n2o_mc_kg"], tank_V_L=cs["tank_V_L"],
                   m_liftoff_kg=cs["m_liftoff_kg"], ballast_kg=(cs["ballast"] or {}).get("ballast_kg", 0.0),
                   td_vz_p99=s["td_vz_p99"], td_vh_p50=s["td_vh_p50"], td_vh_p99=s["td_vh_p99"],
                   td_tilt_p99=s["td_tilt_p99"], td_rate_p99=s["td_rate_p99"], td_miss_p50=s["td_miss_p50"],
                   td_miss_p95=s["td_miss_p95"], td_miss_max=s["td_miss_max"], prop_used_p50=s["prop_used_p50"],
                   prop_used_p99=s["prop_used_p99"], liq_left_p01=s["liq_left_p01"], exhausted=s["exhausted"],
                   h_max_p01=s["h_max_p01"], h_max_p50=s["h_max_p50"], h_max_p99=s["h_max_p99"],
                   h_ign_p50=s["h_ign_p50"], v_ign_p50=s["v_ign_p50"], hslam_frac=s["hslam_frac"],
                   max_gim_p99=s["max_gim_p99"], gim_sat_frac_p99=s["gim_sat_frac_p99"],
                   max_gim_rate_p99=s["max_gim_rate_p99"], max_gim_acc_p99=s["max_gim_acc_p99"],
                   max_hinge_p99=s["max_hinge_p99"], max_hinge_max=s.get("max_hinge_max"),
                   max_hinge_td_p99=s.get("max_hinge_td_p99"), max_hinge_td_max=s.get("max_hinge_td_max"),
                   max_axial_g_flt_p99=s.get("max_axial_g_flt_p99"), max_axial_g_flt_max=s.get("max_axial_g_flt_max"),
                   max_axial_g_td_p99=s.get("max_axial_g_td_p99"), max_axial_g_td_max=s.get("max_axial_g_td_max"),
                   max_lat_g_eng_flt_p99=s.get("max_lat_g_eng_flt_p99"), max_lat_g_eng_flt_max=s.get("max_lat_g_eng_flt_max"),
                   max_lat_g_eng_td_p99=s.get("max_lat_g_eng_td_p99"), max_lat_g_eng_td_max=s.get("max_lat_g_eng_td_max"),
                   max_alpha_flt_p99=s.get("max_alpha_flt_p99"), max_alpha_flt_max=s.get("max_alpha_flt_max"),
                   max_alpha_td_p99=s.get("max_alpha_td_p99"), max_alpha_td_max=s.get("max_alpha_td_max"),
                   peak_leg_force_p99=s["peak_leg_force_p99"], peak_leg_force_max=s.get("peak_leg_force_max"),
                   max_rate_coast_p50=s["max_rate_coast_p50"], max_rate_coast_p99=s["max_rate_coast_p99"],
                   tumble_coast=s["tumble_coast"], max_tilt_land_p99=s["max_tilt_land_p99"],
                   td_roll_rate_p99=s["td_roll_rate_p99"], max_roll_rate_p99=s["max_roll_rate_p99"],
                   rcs_time_p99_s=rcs_t99, rcs_n2o_p99_kg=RCS_THRUST_N * rcs_t99 / (RCS_ISP_S[0] * R.G0),
                   rcs_n2o_p99_kg_isp_low=RCS_THRUST_N * rcs_t99 / (RCS_ISP_S[1] * R.G0),
                   att_err_td_p99=s["att_err_td_p99"], nav_h_err_td_p99=s["nav_h_err_td_p99"], max_q_p99=s["max_q_p99"])
        # paired comparison against the baseline (same draw sequence for RV-1c A-D variants)
        if base_rows is not None and c != BASE and len(rows) == len(base_rows):
            pairable = cs.get("vehicle") == "RV-1c"
            b = sum(1 for x, y in zip(base_rows, rows) if x["ok"] > 0.5 and y["ok"] < 0.5)
            cc = sum(1 for x, y in zip(base_rows, rows) if x["ok"] < 0.5 and y["ok"] > 0.5)
            pv = binomtest(min(b, cc), b + cc, 0.5).pvalue if b + cc > 0 else 1.0
            # check the draws are the same (pairing valid): compare the wind column
            same = all(abs(x["wind"] - y["wind"]) < 1e-9 for x, y in zip(base_rows, rows))
            paired.append(dict(case=c, base=BASE, pairable=bool(pairable and same), base_ok_case_fail=b,
                               base_fail_case_ok=cc, mcnemar_exact_p=pv,
                               delta_success=(sum(y["ok"] for y in rows) - sum(x["ok"] for x in base_rows)) / len(rows)))
            row["paired_delta_vs_base"] = paired[-1]["delta_success"]
            row["mcnemar_p_vs_base"] = pv if paired[-1]["pairable"] else float("nan")
        # wind bins
        for wb in s["by_wind"]:
            row[f"P_wind_{wb['wind_lo']:.0f}_{wb['wind_hi']:.0f}"] = wb["success"]
        table.append(row)
    wcsv(os.path.join(RES, "mc6_cases_summary_v2.csv"), table)
    json.dump(dict(version="mc6 cases summary v2", sim=S["sim"], n=S["n"], load_margin=S["load_margin"],
                   criteria=S["criteria"], rcs_isp_assumed_s=RCS_ISP_S, cases=table),
              open(os.path.join(RES, "mc6_cases_summary_v2.json"), "w"), indent=1, default=float)
    wcsv(os.path.join(RES, "mc6_paired_v2.csv"), paired)

    # failure drivers (baseline + pooled A-D RV-1c variants with the same configuration family)
    keys = ["wind", "gust_scale", "g_bias_dps", "a_bias_h", "align_deg", "t_ign", "tau_f", "thrust_scale", "isp_scale",
            "dry_scale", "m_est_err", "dz_air", "cg_off_mm", "mis_deg", "gim_wn_f", "gim_delay_add", "hose_K", "rock_K",
            "rock_zeta", "slosh_zeta", "drogue_f", "T0", "rho0", "roll", "legs_mu", "legs_k_f", "legs_c_f",
            "k_base_lead", "k_nose_trail", "crossflow", "ca_tf", "k_retro", "gnss_bv", "gnss_bh", "baro_b", "roll_abs"]
    drivers = []
    for c in [BASE, "AD_prov_2kg", "AD_nofins_f20", "AD_fins_f25", "AD_fins_f40", "AD_fins_f20_BMI088", "AD_fins_f20_norcs",
              "AD_fins_f20_norcs_r05", "AF_nofins_f20", "B_f20"]:
        rows = data.get(c)
        if not rows:
            continue
        fail = np.array([1.0 - r["ok"] for r in rows])
        if fail.sum() == 0:
            continue
        lst = []
        for k in keys:
            if k not in rows[0]:
                continue
            x = np.array([r[k] for r in rows])
            if not np.all(np.isfinite(x)) or x.std() == 0:
                continue
            rho = float(spearmanr(x, fail).statistic)
            lst.append((k, rho, float(np.median(x[fail > 0.5])), float(np.median(x))))
        lst.sort(key=lambda t: -abs(t[1]))
        for rank, (k, rho, mf, ma) in enumerate(lst[:10], 1):
            drivers.append(dict(case=c, rank=rank, parameter=k, spearman_rho_with_failure=rho, median_in_failed=mf,
                                median_all=ma, n_failed=int(fail.sum())))
    wcsv(os.path.join(RES, "mc6_failure_drivers_v2.csv"), drivers)

    # ------------------------------------------------------------------ plots
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    crit = S["criteria"]
    if base_rows:
        L = [r for r in base_rows if r["landed"] > 0.5]
        ok = np.array([r["ok"] for r in L]) > 0.5
        fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
        vz = np.abs([r["td_vz"] for r in L]); vh = np.array([r["td_vh"] for r in L])
        ti = np.array([r["td_tilt"] for r in L]); ra = np.array([r["td_rate"] for r in L])
        axs[0].scatter(vh[ok], vz[ok], s=8, c="C0", label="success")
        axs[0].scatter(vh[~ok], vz[~ok], s=18, c="C3", marker="x", label="failure")
        axs[0].axvline(crit["vh"], color="k", ls="--", lw=0.8); axs[0].axhline(crit["vz"], color="k", ls="--", lw=0.8)
        axs[0].set_xlabel("touchdown lateral speed [m/s]"); axs[0].set_ylabel("touchdown vertical speed [m/s]")
        axs[0].legend(fontsize=8)
        axs[1].scatter(ti[ok], ra[ok], s=8, c="C0"); axs[1].scatter(ti[~ok], ra[~ok], s=18, c="C3", marker="x")
        axs[1].axvline(crit["tilt"], color="k", ls="--", lw=0.8); axs[1].axhline(crit["rate"], color="k", ls="--", lw=0.8)
        axs[1].set_xlabel("touchdown tilt [deg]"); axs[1].set_ylabel("touchdown tilt rate [deg/s]")
        b = cases[BASE]["summary"]
        fig.suptitle(f"Baseline {BASE} (RV-1c, A-D): {len(base_rows)} dispersed runs, P = {b['success']:.3f} "
                     f"[{b['ci95'][0]:.3f}, {b['ci95'][1]:.3f}] (SIM {S['sim']})")
        for a_ in axs:
            a_.grid(alpha=0.3)
        fig.tight_layout(); fig.savefig(os.path.join(RES, "mc6_touchdown_scatter_v2.png"), dpi=130); plt.close(fig)
        # miss distance
        fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
        for c, col in ((BASE, "C0"), ("AD_fins_f20_upwind", "C2"), ("AF_nofins_f20", "C1")):
            rows = data.get(c)
            if not rows:
                continue
            Lc = [r for r in rows if r["landed"] > 0.5]
            axs[0].scatter([r["td_x"] for r in Lc], [r["td_y"] for r in Lc], s=5, c=col, label=c)
            m = np.sort([r["td_miss"] for r in Lc])
            axs[1].plot(m, np.arange(1, len(m) + 1) / len(m), color=col, label=c)
        axs[0].plot(0, 0, "k+", ms=12); axs[0].set_aspect("equal"); axs[0].legend(fontsize=7)
        axs[0].set_xlabel("x [m] (pad at origin)"); axs[0].set_ylabel("y [m]")
        axs[1].set_xlabel("miss distance from the pad [m]"); axs[1].set_ylabel("cumulative fraction")
        axs[1].legend(fontsize=7)
        for a_ in axs:
            a_.grid(alpha=0.3)
        fig.suptitle("Touchdown points: drogue drift dominates; upwind ascent bias (pad wind measured) shrinks the miss")
        fig.tight_layout(); fig.savefig(os.path.join(RES, "mc6_miss_v2.png"), dpi=130); plt.close(fig)
    # case success with CI
    tc = [t for t in table if t.get("closes", True) is not False and "success" in t]
    fig, ax = plt.subplots(figsize=(9, 0.32 * len(tc) + 1.2))
    for i, t in enumerate(tc):
        col = "C0" if t["case"] == BASE else ("C2" if t["case"] == "AD_prov_2kg" else ("C3" if t["ci95_hi"] < 0.95 else "0.3"))
        ax.errorbar(t["success"], i, xerr=[[t["success"] - t["ci95_lo"]], [t["ci95_hi"] - t["success"]]], fmt="o",
                    color=col, capsize=3)
    ax.set_yticks(range(len(tc))); ax.set_yticklabels([t["case"] for t in tc], fontsize=8)
    ax.invert_yaxis(); ax.set_xlabel("success probability (Wilson 95 % interval), 500 runs per case")
    ax.axvline(0.99, color="k", ls=":", lw=0.8)
    ax.grid(alpha=0.3)
    ax.set_title("6-DOF Monte Carlo cases (criteria vz <= 2, vh <= 0.5 m/s, tilt <= 5 deg, rate <= 10 deg/s)")
    fig.tight_layout(); fig.savefig(os.path.join(RES, "mc6_cases_success_v2.png"), dpi=130); plt.close(fig)
    # success by wind
    fig, ax = plt.subplots(figsize=(8, 4))
    for c, col in ((BASE, "C0"), ("AD_nofins_f20", "C3"), ("AD_fins_f20_BMI088", "C1"), ("AF_nofins_f20", "C2"),
                   ("B_f20", "C4"), ("AD_fins_f20_nolpf", "C5")):
        if c not in cases or not cases[c].get("closes", True):
            continue
        wb = cases[c]["summary"]["by_wind"]
        xm = [0.5 * (w["wind_lo"] + w["wind_hi"]) for w in wb]
        ax.plot(xm, [w["success"] for w in wb], "o-", color=col, label=c)
    ax.set_xlabel("mean wind at 10 m [m/s] (bin centre; gusts on, Dryden scale x U(0.5, 1.5))")
    ax.set_ylabel("success probability in bin"); ax.grid(alpha=0.3); ax.legend(fontsize=7)
    ax.set_title("Success by wind bin (500 runs per case, wind U(0, 8) m/s)")
    fig.tight_layout(); fig.savefig(os.path.join(RES, "mc6_success_by_wind_v2.png"), dpi=130); plt.close(fig)
    # sensitivity (baseline): Spearman with failure and with td_vh, td_vz
    if base_rows:
        sens = cases[BASE]["sensitivity"]
        fig, axs = plt.subplots(1, 3, figsize=(13, 4))
        for a_, key, ttl in ((axs[0], "failure", "failure indicator"), (axs[1], "td_vh", "|touchdown lateral speed|"),
                             (axs[2], "td_vz", "|touchdown vertical speed|")):
            lst = sens.get(key, [])[:8]
            a_.barh([x[0] for x in lst][::-1], [x[1] for x in lst][::-1], color="C0")
            a_.set_title(f"Spearman rho with {ttl}", fontsize=9); a_.grid(alpha=0.3)
        fig.suptitle(f"Sensitivity ranking, baseline {BASE}")
        fig.tight_layout(); fig.savefig(os.path.join(RES, "mc6_sensitivity_v2.png"), dpi=130); plt.close(fig)
        # loads
        fig, axs = plt.subplots(1, 4, figsize=(15, 3.6))
        for a_, key, lab in ((axs[0], "max_axial_g_flt", "axial specific force, flight [g]"),
                             (axs[0], "max_axial_g_td", "axial, touchdown [g]"),
                             (axs[1], "max_lat_g_eng_flt", "lateral at pivot, flight [g]"),
                             (axs[1], "max_lat_g_eng_td", "lateral at pivot, touchdown [g]"),
                             (axs[2], "max_hinge", "hinge (mount torque), lit [N m]"),
                             (axs[2], "max_hinge_td", "hinge after touchdown [N m]"),
                             (axs[3], "peak_leg_force", "peak total leg force [N]")):
            x = [r[key] for r in base_rows if np.isfinite(r.get(key, np.nan))]
            if x:
                a_.hist(x, bins=40, alpha=0.6, label=lab)
        for a_ in axs:
            a_.legend(fontsize=7); a_.grid(alpha=0.3)
        fig.suptitle(f"Engine-mount load maxima per run, baseline {BASE} (limit-load inputs; SIM, not measured)")
        fig.tight_layout(); fig.savefig(os.path.join(RES, "mc6_loads_v2.png"), dpi=130); plt.close(fig)
    # gimbal limit decision
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.8))
    for c, col in ((BASE, "C0"), ("AD_fins_f20_gim6", "C1"), ("AD_fins_f20_gim5", "C3"), ("AD_fins_f20_nolpf", "C5")):
        rows = data.get(c)
        if not rows:
            continue
        axs[0].hist([r["max_gim"] for r in rows], bins=40, alpha=0.5, color=col, label=c)
        axs[1].hist([r["gim_sat_frac"] for r in rows], bins=40, alpha=0.5, color=col, label=c)
        axs[2].hist([r["max_hinge"] for r in rows], bins=40, alpha=0.5, color=col, label=c)
    axs[0].set_xlabel("max engine angle per run [deg]"); axs[1].set_xlabel("fraction of burn time saturated")
    axs[2].set_xlabel("max hinge (mount) torque while lit [N m]")
    for a_ in axs:
        a_.legend(fontsize=7); a_.grid(alpha=0.3)
    fig.suptitle("Gimbal vector limit 7 / 6 / 5 deg and the unfiltered comparator")
    fig.tight_layout(); fig.savefig(os.path.join(RES, "mc6_gimbal_v2.png"), dpi=130); plt.close(fig)
    # roll-control decision: success vs engine roll-torque amplitude, RCS off / on (same draws, torque scaled)
    sweep = [("AD_fins_f20_norcs_r0", 0.0, False), ("AD_fins_f20_norcs_r005", 0.005, False),
             ("AD_fins_f20_norcs_r01", 0.01, False), ("AD_fins_f20_norcs", 0.02, False),
             ("AD_fins_f20_norcs_r03", 0.03, False), ("AD_fins_f20_norcs_r04", 0.04, False),
             ("AD_fins_f20_norcs_r05", 0.05, False), ("AD_fins_f20_norcs_r10", 0.10, False),
             (BASE, 0.02, True), ("AD_fins_f20_r10", 0.10, True)]
    srows = []
    for c, amp, rcs in sweep:
        if c not in cases or not cases[c].get("closes", True):
            continue
        sm = cases[c]["summary"]
        srows.append(dict(case=c, roll_amp_Nm=amp, rcs=rcs, success=sm["success"], ci95_lo=sm["ci95"][0],
                          ci95_hi=sm["ci95"][1], fail_modes=";".join(f"{a}:{b}" for a, b in sorted(sm["fail_modes"].items())),
                          max_roll_rate_p99_dps=sm["max_roll_rate_p99"], td_roll_rate_p99_dps=sm["td_roll_rate_p99"],
                          td_rate_p99_dps=sm["td_rate_p99"], td_tilt_p99_deg=sm["td_tilt_p99"],
                          rcs_time_p99_s=sm.get("rcs_time_p99", float("nan"))))
    if srows:
        wcsv(os.path.join(RES, "mc6_roll_sweep_v2.csv"), srows)
        fig, axs = plt.subplots(1, 2, figsize=(11, 4))
        for rcs, col, lab in ((False, "C3", "roll RCS off"), (True, "C0", "roll RCS on (2 x 0.5 N couple)")):
            sr = [r for r in srows if r["rcs"] == rcs]
            if not sr:
                continue
            x = [r["roll_amp_Nm"] for r in sr]
            y = [r["success"] for r in sr]
            e = [[r["success"] - r["ci95_lo"] for r in sr], [r["ci95_hi"] - r["success"] for r in sr]]
            axs[0].errorbar(x, y, yerr=e, fmt="o-", color=col, capsize=3, label=lab)
            axs[1].plot(x, [r["max_roll_rate_p99_dps"] for r in sr], "o-", color=col, label=lab + ": max roll rate p99")
        axs[0].set_xlabel("engine roll torque amplitude at F_max [N m] (MC U(-a, a))")
        axs[0].set_ylabel("success probability (Wilson 95 %)"); axs[0].legend(fontsize=8); axs[0].grid(alpha=0.3)
        axs[1].set_xlabel("engine roll torque amplitude at F_max [N m]"); axs[1].set_ylabel("roll rate p99 [deg/s]")
        axs[1].legend(fontsize=8); axs[1].grid(alpha=0.3)
        fig.suptitle("Roll-control decision: success vs engine roll torque (same 500 draws, torque scaled)")
        fig.tight_layout(); fig.savefig(os.path.join(RES, "mc6_roll_sweep_v2.png"), dpi=130); plt.close(fig)
    # flight time line (DC-A1 v2 duty cycle)
    p = os.path.join(DC, "DC-A1_full_flight_drogue_fins_300m_v2.csv")
    if os.path.exists(p):
        with open(p) as f:
            rr = list(csv.DictReader(f))

        def col(k):
            return np.array([float(x[k]) if x[k] != "" else np.nan for x in rr])
        t = col("t_s")
        fig, axs = plt.subplots(4, 1, figsize=(10, 9), sharex=True)
        axs[0].plot(t, col("h_m"), label="h (CG above liftoff) [m]"); axs[0].set_ylabel("h [m]")
        ax2 = axs[0].twinx(); ax2.plot(t, col("v_mps"), color="C1"); ax2.set_ylabel("v_z [m/s]", color="C1")
        axs[1].plot(t, col("F_N"), label="F"); axs[1].plot(t, col("F_cmd_N"), ls=":", label="F_cmd")
        axs[1].set_ylabel("thrust [N]"); axs[1].legend(fontsize=7)
        axs[2].plot(t, col("gimbal_x_deg"), label="gimbal x"); axs[2].plot(t, col("gimbal_y_deg"), label="gimbal y")
        axs[2].plot(t, col("gimbal_x_cmd_deg"), ls=":", lw=0.8, label="cmd x"); axs[2].set_ylabel("gimbal [deg]")
        axs[2].legend(fontsize=7)
        axs[3].plot(t, col("tilt_deg"), label="tilt"); axs[3].plot(t, col("hinge_moment_est_Nm"), label="hinge [N m]")
        axs[3].set_ylabel("tilt [deg] / hinge [N m]"); axs[3].legend(fontsize=7); axs[3].set_xlabel("t [s]")
        for a_ in axs:
            a_.grid(alpha=0.3)
        fig.suptitle("DC-A1 v2: baseline A-D flight, one seeded 5 m/s + gust realisation (6-DOF sim6)")
        fig.tight_layout(); fig.savefig(os.path.join(RES, "flight_timeline_DC-A1_v2.png"), dpi=130); plt.close(fig)
    for t in table:
        if "success" in t:
            print(f"{t['case']:24s} P {t['success']:.3f} [{t['ci95_lo']:.3f},{t['ci95_hi']:.3f}] "
                  f"d {t.get('paired_delta_vs_base', 0):+.3f} p {t.get('mcnemar_p_vs_base', float('nan')):.3g} "
                  f"N2O {t['m_n2o_mc_kg']:.2f} gim99 {t['max_gim_p99']:.2f} sat99 {t['gim_sat_frac_p99']:.3f} "
                  f"hinge99 {t['max_hinge_p99']:.1f} vh99 {t['td_vh_p99']:.2f} miss50 {t['td_miss_p50']:.0f}")
        else:
            print(t["case"], "NO CLOSURE")


if __name__ == "__main__":
    main()
