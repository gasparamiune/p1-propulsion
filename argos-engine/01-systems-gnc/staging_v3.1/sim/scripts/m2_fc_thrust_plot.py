"""m2_fc_thrust_plot v1 (GNC, 2026-10-13): figure of m2_fc_thrust v1.1 (FC_THRUST over-thrust abort): threshold sweep (Pc-lost
false aborts per flight, empirical and normal-fit, and stuck-pintle misses at 670 / 876 N) and the per-run held maxima of the
accelerometer estimate (healthy and Pc-lost) against the stuck-pintle levels, for the tau 20 ms and box 10 ms variants.
Env: GNC_FCT_OUT (out/fc_thrust). Output: fc_thrust_v1.1.png."""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = os.environ.get("GNC_FCT_OUT", "/home/claude/work/space/out/fc_thrust")


def main():
    d = json.load(open(os.path.join(OUT, "fc_thrust.json")))
    store = {}
    for prof in ("A1", "B1"):
        p = os.path.join(OUT, f"fc_thrust_runs_{prof}.npy")
        if os.path.exists(p):
            store.update(np.load(p, allow_pickle=True)[0])
    fig, axs = plt.subplots(2, 2, figsize=(12, 8.5))
    for col, v in enumerate(("tau20ms", "box10ms")):
        ax = axs[0, col]
        T = np.array(sorted({float(k.split("|")[1]) for k in d["threshold_summary"] if k.startswith(v + "|")}))
        rows = [d["threshold_summary"][f"{v}|{t:g}"] for t in T]
        for prof, c in (("A1", "tab:blue"), ("B1", "tab:green")):
            n = d["runs_per_branch"]
            emp = np.array([r.get(f"false_L_{prof}", 0) for r in rows]) / n
            gau = np.array([r.get(f"false_L_{prof}_gauss", np.nan) for r in rows])
            ax.semilogy(T, np.where(emp > 0, emp, np.nan), "o-", color=c, ms=3, label=f"Pc lost {prof}: false aborts (MC, {n} runs)")
            ax.semilogy(T, gau, "--", color=c, lw=1, label=f"Pc lost {prof}: normal fit of held maxima")
        for Ff, c in ((670, "tab:red"), (876, "tab:purple")):
            m = np.array([r[f"miss_{Ff}"] for r in rows]) / np.array([r[f"n_{Ff}"] for r in rows])
            nn = int(rows[0][f"n_{Ff}"])
            lab = (f"stuck {Ff} N: missed (no abort in 2 s, of {nn})" if (m > 0).any()
                   else f"stuck {Ff} N: none missed in {nn} at any T (not drawn)")
            ax.semilogy(T, np.where(m > 0, m, np.nan), "s-", color=c, ms=3, label=lab)
        ax.axvline(650, color="k", lw=0.8, ls=":")
        ax.set_ylim(1e-6, 1.2)
        ax.set_xlabel("threshold T [N], held 20 ms")
        ax.set_ylabel("probability per flight / per failure")
        ax.set_title(f"{v}: threshold sweep", fontsize=9)
        ax.grid(alpha=0.3, which="both")
        ax.legend(fontsize=6.5, loc="lower left")
        ax = axs[1, col]
        bins = np.arange(440, 760, 5)
        for key, c, lab in (("A1|H", "tab:blue", "A1 healthy"), ("B1|H", "tab:cyan", "B1 healthy"),
                            ("A1|L", "tab:orange", "A1 Pc lost (1.143)"), ("B1|L", "tab:red", "B1 Pc lost (1.143)")):
            if key in store:
                hm = np.array([r[v]["held_max_fc_N"] for r in store[key]])
                ax.hist(hm, bins=bins, histtype="step", color=c, label=f"{lab}: held max of F_acc")
        H = [r for k in ("A1|H", "B1|H") if k in store for r in store[k]]
        bf = np.array([(1 + r["bias_terms"]["m_est_err"]) * (1 + r["bias_terms"]["a_sf"]) for r in H])
        ax.hist(670.0 * bf, bins=bins, histtype="stepfilled", alpha=0.25, color="tab:red", label="stuck 670 N x run bias factor")
        ax.axvline(650, color="k", lw=0.8, ls=":")
        ax.axvline(571.5, color="0.4", lw=0.8, ls="--")
        ax.set_xlabel("N")
        ax.set_ylabel("runs")
        ax.set_title(f"{v}: per-run held maximum (fc window) vs the stuck-pintle level", fontsize=9)
        ax.legend(fontsize=6.5, loc="upper left")
        ax.grid(alpha=0.3)
    fig.text(0.01, 0.005, "SIM m2_fc_thrust v1.1 on sim6/run6 v2.7.1-dev; FSW mass-estimate error N(0, 3 %) and vibration 2 m/s2 at "
                          "F_max ASSUMED; CAN / ECU latency and the IMU internal filter not included", fontsize=7)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    p = os.path.join(OUT, "fc_thrust_v1.1.png")
    fig.savefig(p, dpi=110)
    print("wrote", p)


if __name__ == "__main__":
    main()
