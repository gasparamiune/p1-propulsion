"""m2_relight_seg44_plot v1 (GNC, 2026-10-13): figure of m2_relight_seg44 v1.2 (relight_seg44.json).

Panel a: A1 landing success P against the relight planning value for the liquid line and the 44 cm3 vapour-full start
(A1_none + A1J_none pooled, 1000 paired runs per point, Wilson 95 % bars; W 1.05 s, so no ECU abort; sim6 lights at the drawn
delay). Panel b: expected P against the probability that the segment is liquid at RELIGHT (four A1 bases pooled, 2000 paired runs
per state): v3 (plan 0.81 s, W 0.65 s; Combustion: every 44 cm3 vapour-full relight aborted, an abort counted as a lost landing,
ASSUMED), fallback (b) (plan 1.21 s, W 1.05 s), (b') (plan 0.81 s, W 1.05 s); dashed: the best planning value of panel a on the
two no-growth bases. Panel c: light-minus-plan error against P per case (four bases).
Env: GNC_SEG44_OUT (default out/relight_seg44)."""
import json
import os
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

VERSION = "m2_relight_seg44_plot v1"
OUT = os.environ.get("GNC_SEG44_OUT", "/home/claude/work/space/out/relight_seg44")


def main():
    d = json.load(open(os.path.join(OUT, "relight_seg44.json")))
    fig, ax = plt.subplots(1, 3, figsize=(16.5, 5.0))
    pc = d["plan_curve"]
    for st, col, lab in (("liq", "tab:blue", "liquid line"), ("vap44F", "tab:red", "44 cm3 vapour-full")):
        cc = pc["curve"][st]
        x = np.array([float(k) for k in cc])
        o = np.argsort(x)
        P = np.array([cc[k]["P"] for k in cc])[o]
        lo = np.array([cc[k]["ci95"][0] for k in cc])[o]
        hi = np.array([cc[k]["ci95"][1] for k in cc])[o]
        ax[0].errorbar(x[o], P, yerr=[P - lo, hi - P], color=col, marker="o", capsize=3, label=lab)
    ax[0].axvline(d["plan_baseline_s"], color="0.5", ls=":", lw=1)
    ax[0].axvline(d["plan_fallback_s"], color="0.5", ls=":", lw=1)
    ax[0].text(d["plan_baseline_s"], 0.932, " v3 0.81 s", fontsize=8, color="0.3")
    ax[0].text(d["plan_fallback_s"], 0.932, " (b) 1.21 s", fontsize=8, color="0.3", ha="right")
    ax[0].set_xlabel("relight planning value t_ign_est [s]")
    ax[0].set_ylabel("A1 success P (sim6 6-DOF)")
    ax[0].set_title("a) P vs planning value (A1_none + A1J_none, n = 1000 each, W 1.05 s)", fontsize=9)
    ax[0].set_ylim(0.93, 1.0)
    ax[0].grid(alpha=0.3)
    ax[0].legend(fontsize=8, loc="lower center")
    dec = d["decision"]["by_state"]["vap44F"]["table"]
    p = np.array([r["p_liquid"] for r in dec])
    ax[1].plot(p, [r["P_v3"] for r in dec], "k-o", ms=3, label="v3: plan 0.81 s, W 0.65 s (vapour-full aborts)")
    ax[1].plot(p, [r["P_fallback_b"] for r in dec], "r-o", ms=3, label="(b): plan 1.21 s, W 1.05 s")
    ax[1].plot(p, [r["P_alt_bprime"] for r in dec], "g-o", ms=3, label="(b'): plan 0.81 s, W 1.05 s")
    bp = pc["expected_P_best_plan"]
    ax[1].plot([r["p_liquid"] for r in bp], [r["P_best"] for r in bp], "m--", lw=1.2,
               label="best plan of panel a (2 bases), W 1.05 s")
    for r in bp:
        if r["p_liquid"] in (0.0, 0.5, 0.9, 1.0):
            ax[1].annotate(f"{r['best_plan_s']:.2f} s", (r["p_liquid"], r["P_best"]), textcoords="offset points", xytext=(0, 5),
                           fontsize=7, color="m", ha="center")
    be = d["decision"]["by_state"]["vap44F"]["break_even_p_liquid_v3_vs_b"]
    ax[1].axvline(be, color="0.5", ls=":", lw=1)
    ax[1].text(be - 0.01, 0.945, f"v3 = (b) at p = {be:.3f}", fontsize=7, color="0.3", ha="right")
    ax[1].set_xlabel("probability that the MV-to-seat segment is liquid at RELIGHT (else 44 cm3 vapour-full)")
    ax[1].set_ylabel("expected P")
    ax[1].set_title("b) expected P (4 bases pooled; an aborted relight = lost landing, ASSUMED)", fontsize=9)
    ax[1].set_ylim(0.90, 1.0)
    ax[1].grid(alpha=0.3)
    ax[1].legend(fontsize=7, loc="lower right")
    for base, bb in d["by_base"].items():
        for key, x in bb.items():
            lmp = x["light_minus_plan_s_min_p50_max"]
            st = key.split("_p")[0] if key != "baseline" else "liq"
            col = {"liq": "tab:blue", "vap44F": "tab:red", "vap34F": "tab:orange", "vap44F69": "tab:purple"}.get(st, "k")
            ax[2].errorbar(lmp[1], x["P"], xerr=[[lmp[1] - lmp[0]], [lmp[2] - lmp[1]]], color=col, marker="o", ms=3, lw=0.6,
                           alpha=0.7, capsize=2)
    for st, col in (("liquid", "tab:blue"), ("44 cm3 vapour-full", "tab:red"), ("34 cm3 vapour", "tab:orange"),
                    ("44 cm3, 0.69 s purge", "tab:purple")):
        ax[2].plot([], [], "o", color=col, label=st)
    ax[2].axvline(0.0, color="0.5", ls=":", lw=1)
    ax[2].set_xlabel("light minus plan [s] (median, bars min..max)")
    ax[2].set_ylabel("P (500 runs per point)")
    ax[2].set_title("c) every case: early (<0) and late (>0) lights", fontsize=9)
    ax[2].set_ylim(0.92, 1.0)
    ax[2].grid(alpha=0.3)
    ax[2].legend(fontsize=7, loc="lower left")
    fig.suptitle(f"ARGOS H1 A1 relight: vapour-start fallback cost ({d['version']}, {d['sim']}); SIM, not physical validation",
                 fontsize=10)
    fig.tight_layout()
    p = os.path.join(OUT, "relight_seg44_v1.png")
    fig.savefig(p, dpi=130)
    print("wrote", p)


if __name__ == "__main__":
    main()
