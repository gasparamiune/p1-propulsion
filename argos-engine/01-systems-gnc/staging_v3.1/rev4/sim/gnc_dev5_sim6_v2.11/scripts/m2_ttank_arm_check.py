"""m2_ttank_arm_check v1 (GNC, 2026-10-13): effect of the tank-temperature draw above the new ARM range on the published Monte
Carlo cases (lead note 2026-10-13: tank ARM range 15-24 C, ignition interlock at 24 C; if the dispersions draw T_tank up to 25 C,
record it as a small conservative difference; no re-run needed).

The run6 draw is T0 ~ U(288.15, 298.15) K = U(15, 25) C (ASSUMED, all v3 cases). This script re-reads the Monte Carlo CSVs (no
flight is re-run) and compares the runs drawn above 24 C (T0 > 297.15 K, outside the ARM range) with the others: success rate
(Wilson 95 % intervals, Fisher exact test), engine-on counter and liquid left (medians, Spearman rank correlation with T0 over all
runs), and whether the published duty-cycle runs (p99 / max) were drawn above 24 C. 'Conservative' is checked per output, not
assumed.
Env: none. Output: out/ttank_arm_check/ttank_arm_check_v1.json."""
import csv
import json
import os
import numpy as np
from scipy.stats import fisher_exact, spearmanr

VERSION = "m2_ttank_arm_check v1"
S = "/home/claude/work/space/out"
OUT = f"{S}/ttank_arm_check"
T_ARM_MAX_K = 273.15 + 24.0     # REQ lead 2026-10-13: ARM range 15-24 C (ignition interlock at 24 C)
CASES = {
    "v28_liq_p0.81_A1_none_k2": f"{S}/relight_v28/mc6_runs_v28_liq_p0.81_A1_none_k2_v28.csv",
    "v28_liq_p0.81_A1_pc_k2": f"{S}/relight_v28/mc6_runs_v28_liq_p0.81_A1_pc_k2_v28.csv",
    "tg_B1_none_k2 (85 m)": f"{S}/throat_growth/mc6_runs_tg_B1_none_k2_tg.csv",
    "tg_B1_pc_k2 (85 m)": f"{S}/throat_growth/mc6_runs_tg_B1_pc_k2_tg.csv",
    "tgl_B1_lead62_none_k2 (62 m)": f"{S}/duty_cycles_v3_1/mc/mc6_runs_tgl_B1_lead62_none_k2.csv",
    "tgl_B1_lead62_pc_k2 (62 m)": f"{S}/regband/mc6_runs_tgl_B1_lead62_pc_k2_rb.csv",
}
HUB_CSV = {
    "v28_liq_p0.81_A1_none_k2": "01-systems-gnc/results/relight_v28/mc6_runs_v28_liq_p0.81_A1_none_k2_v28.csv.gz",
    "v28_liq_p0.81_A1_pc_k2": "01-systems-gnc/results/relight_v28/mc6_runs_v28_liq_p0.81_A1_pc_k2_v28.csv.gz",
    "tg_B1_none_k2 (85 m)": "01-systems-gnc/results/throat_growth/mc6_runs_tg_B1_none_k2_tg.csv.gz",
    "tg_B1_pc_k2 (85 m)": "01-systems-gnc/results/throat_growth/mc6_runs_tg_B1_pc_k2_tg.csv.gz",
    "tgl_B1_lead62_none_k2 (62 m)": "01-systems-gnc/staging_v3.1/results/b1_62m_mc/mc6_runs_tgl_B1_lead62_none_k2.csv.gz",
    "tgl_B1_lead62_pc_k2 (62 m)": "01-systems-gnc/results/regband/mc6_runs_tgl_B1_lead62_pc_k2_rb.csv.gz",
}
DC_INDEXES = [f"{S}/duty_cycles_v3/duty_cycles_index_v3.json", f"{S}/duty_cycles_v3_1/duty_cycles_records_b1_62m_v3.1.json"]


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, c - h), min(1.0, c + h)]


def main():
    os.makedirs(OUT, exist_ok=True)
    out = dict(version=VERSION, date="2026-10-13", arm_range_C=[15.0, 24.0], drawn_range_C=[15.0, 25.0],
               draw="run6: T0 ~ U(288.15, 298.15) K (ASSUMED), all v3 Monte Carlo cases", cases={}, duty_cycle_runs={})
    for name, p in CASES.items():
        if not os.path.exists(p):
            out["cases"][name] = "missing"
            continue
        rr = list(csv.DictReader(open(p)))
        T = np.array([float(r["T0"]) for r in rr])
        ok = np.array([float(r["ok"]) for r in rr]) > 0.5
        bt = np.array([float(r["burn_time"]) for r in rr])
        liq = np.array([float(r["liq_left"]) for r in rr])
        hot = T > T_ARM_MAX_K
        tab = [[int(np.sum(ok[hot])), int(np.sum(~ok[hot]))], [int(np.sum(ok[~hot])), int(np.sum(~ok[~hot]))]]
        rho_bt, p_bt = spearmanr(T, bt)
        rho_lq, p_lq = spearmanr(T, liq)
        out["cases"][name] = dict(
            csv=os.path.relpath(p, S), csv_hub=HUB_CSV[name], n=len(rr), n_above_24C=int(hot.sum()),
            P_above_24C=float(ok[hot].mean()), P_above_24C_ci95=wilson(int(ok[hot].sum()), int(hot.sum())),
            P_in_arm_range=float(ok[~hot].mean()), P_in_arm_range_ci95=wilson(int(ok[~hot].sum()), int((~hot).sum())),
            P_all=float(ok.mean()), fisher_exact_p=float(fisher_exact(tab)[1]),
            counter_median_above_24C_s=float(np.median(bt[hot])), counter_median_in_range_s=float(np.median(bt[~hot])),
            counter_p99_all_s=float(np.percentile(bt, 99)), counter_p99_in_range_s=float(np.percentile(bt[~hot], 99)),
            spearman_T0_counter=[float(rho_bt), float(p_bt)],
            liquid_left_median_above_24C_kg=float(np.median(liq[hot])), liquid_left_median_in_range_kg=float(np.median(liq[~hot])),
            spearman_T0_liquid_left=[float(rho_lq), float(p_lq)])
        c = out["cases"][name]
        print(f"{name:30s} hot {c['n_above_24C']:3d}/{c['n']} P hot {c['P_above_24C']:.3f} vs in-range {c['P_in_arm_range']:.3f} "
              f"(Fisher p {c['fisher_exact_p']:.2f}); counter median {c['counter_median_above_24C_s']:.2f} vs "
              f"{c['counter_median_in_range_s']:.2f} s, p99 all {c['counter_p99_all_s']:.2f} vs in-range {c['counter_p99_in_range_s']:.2f} s; "
              f"rho(T0, counter) {rho_bt:+.2f} (p {p_bt:.1e})", flush=True)
    for ip in DC_INDEXES:
        if not os.path.exists(ip):
            continue
        d = json.load(open(ip))
        for c in d.get("cycles", []) + d.get("records", []):
            T0 = (c.get("dispersions") or {}).get("_T0")
            if T0 is None:
                continue
            out["duty_cycle_runs"][c["name"]] = dict(T0_K=T0, T0_C=T0 - 273.15, above_24C=bool(T0 > T_ARM_MAX_K))
    hot_dc = [k for k, v in out["duty_cycle_runs"].items() if v["above_24C"]]
    out["duty_cycle_runs_above_24C"] = hot_dc
    with open(os.path.join(OUT, "ttank_arm_check_v1.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("duty-cycle runs above 24 C:", hot_dc, flush=True)
    print("wrote", os.path.join(OUT, "ttank_arm_check_v1.json"))


if __name__ == "__main__":
    main()
