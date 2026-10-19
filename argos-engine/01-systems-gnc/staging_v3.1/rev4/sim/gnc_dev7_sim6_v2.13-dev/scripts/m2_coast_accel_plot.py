"""m2_coast_accel_plot v1 (GNC, 2026-10-13): figure of m2_coast_accel_a1 v1 (A1 axial specific force at the pintle seat from MECO
to the relight command: p01-p99 band and median of 500 dispersed runs, nominal, min-accel run), two alignments.
Env: GNC_CA_OUT (out/coast_accel_a1). Output: coast_accel_a1_v1.png."""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = os.environ.get("GNC_CA_OUT", "/home/claude/work/space/out/coast_accel_a1")


def main():
    meta = json.load(open(os.path.join(OUT, "coast_accel_a1_v1.json")))
    fig, axs = plt.subplots(2, 1, figsize=(10, 8))
    for ax, al, xl in ((axs[0], "meco", "time since the MECO command [s]"),
                       (axs[1], "relight", "time relative to the relight command [s]")):
        d = np.genfromtxt(os.path.join(OUT, f"coast_accel_a1_envelope_{al}_v1.csv"), delimiter=",", names=True)
        x = d["t_since_meco_s"] if al == "meco" else d["t_minus_relight_cmd_s"]
        ax.fill_between(x, d["fz_seat_p01_mps2"], d["fz_seat_p99_mps2"], color="0.8", label="p01-p99, 500 dispersed runs")
        ax.plot(x, d["fz_seat_p50_mps2"], "k-", lw=1.0, label="p50")
        ax.plot(x, d["fz_seat_nominal_mps2"], "b--", lw=1.0, label="nominal (no dispersion, no wind)")
        mr = [v for k, v in meta["extreme_runs"].items() if k.startswith("min_accel_run")][0]
        ax.plot(x, d["fz_seat_min_accel_run_mps2"], "r-", lw=0.7, label=f"min-accel run {mr['run']} (lowest f_z)")
        ax.axhline(0.0, color="k", lw=0.5)
        ax.axhline(9.80665, color="0.5", lw=0.5, ls=":")
        ax.set_ylim(-2.5, 12.0)
        ax.set_xlabel(xl)
        ax.set_ylabel("axial specific force at the seat f_z [m/s2]")
        ax.grid(alpha=0.3)
        if al == "meco":
            st = meta["dispersed"]["coast_up_s"]
            ax.axvspan(0.0, 0.1, color="orange", alpha=0.3, label="tail-off (off scale, up to ~25 m/s2)")
            ax.text(3.0, -2.2, f"coast up: f_z < 0 for {meta['dispersed']['time_fz_below_0g_s']['p50']:.1f} s (p50), "
                               f"mean {meta['dispersed']['fz_seat_coast_up_mean_mps2']['p50']:.2f} m/s2", fontsize=8)
            ax.text(10.5, 2.0, f"drogue descent (deployed at apogee, coast up {st['p50']:.1f} s p50)", fontsize=8)
        ax.legend(fontsize=7, loc="upper right")
    axs[0].set_title("A1 (v2.8 relight, plan 0.81 s, k_est_asc 2): body-axial specific force; f_z > 0 = apparent gravity "
                     "toward the engine end (liquid aft, vapour driven toward the main valve)", fontsize=8)
    fig.text(0.01, 0.005, "SIM sim6/run6 v2.7.1-dev, m2_coast_accel_a1 v1; drogue quasi-steady (no opening load); seat station "
                          "mechanical.json v2 (DERIVED+ESTIMATE)", fontsize=7)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    p = os.path.join(OUT, "coast_accel_a1_v1.png")
    fig.savefig(p, dpi=120)
    print("wrote", p)


if __name__ == "__main__":
    main()
