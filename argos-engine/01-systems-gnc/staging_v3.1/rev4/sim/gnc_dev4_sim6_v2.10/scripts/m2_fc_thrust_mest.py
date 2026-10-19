"""m2_fc_thrust_mest v1 (GNC, 2026-10-13): FC_THRUST over-thrust abort against the FSW mass-estimate error (sensitivity on the
m2_fc_thrust v1.1 flights).

Question. m2_fc_thrust v1.1 shows that, with the ASSUMED FSW mass-estimate error N(0, 3 %), no held-20 ms threshold keeps the
Pc-lost false aborts at 0/1000 AND detects every stuck full-stroke pintle at the low end of the range (670 N): at 650 N, 6.3 % of
the 670 N cases are missed. Which mass-estimate accuracy closes that gap, and which threshold then fits? The v1.1 answer
(error_decomposition.sensitivity_to_mass_estimate_sd_tau20ms) is a per-frame normal model; this script answers it on the same
flights and noise samples.

Method (paired with v1.1):
 - Re-fly the v1.1 H and L branches (draws seed 101, the same per-run noise generators, the same frame phase) and rebuild F_acc
   exactly as v1.1. Check: every per-run held maximum and frame phase equals the stored v1.1 value.
 - Scale the run's mass-estimate error e -> c e with c = s / 0.03 for s = 0.5, 1, 1.5, 2, 3 % in the FC estimate only:
   F_acc_c = (F_acc - D_model) (1 + c e) / (1 + e) + D_model, exact because F_acc - D_model = m (1 + e) f_meas. The flight
   (FSW guidance with its own m_est) is unchanged: only the monitor's input changes. The run6 draw is N(0, 0.03) with a sample
   sd of about 3.09 %, so each scale's sample sd is about 1.03 s.
 - Stuck pintle: v1.1's synthetic ramps through each healthy run's error terms with e -> c e, the same noise samples (generator
   seed 20261020 re-created for each scale, v1.1 loop order). Per case, the held maximum after the onset (hm_post) and before it
   (hm_pre) give the result for every threshold: miss at T <=> hm_pre <= T and hm_post <= T (no abort within 2 s). Check: scale
   1 reproduces v1.1's miss counts on the 5 N grid.
 - Normal fits of the Pc-lost held maxima (per profile) and of hm_post (670 N cases) give tail estimates beyond 1/1000 and
   1/4000; they are model-dependent and labelled as such.
Outputs (GNC_FCT_OUT, default out/fc_thrust): fc_thrust_mest_runs_<prof>.npy (fly), fc_thrust_mest.json, fc_thrust_mest_v1.png.
Env: GNC_IFACE, GNC_ACT_RATE (as m2_fc_thrust), GNC_FCT_OUT, GNC_FCM_PARTS (fly,eval), GNC_FCT_PROFILES (A1,B1)."""
import json
import os
import sys
import time
import numpy as np
from scipy.stats import norm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_fc_thrust as FT  # noqa: E402  (sets the GNC_* defaults of v1.1 and imports run6 / sim6)

VERSION = "m2_fc_thrust_mest v1"
OUT = FT.OUT
PARTS = os.environ.get("GNC_FCM_PARTS", "fly,eval").split(",")
PROFILES = FT.PROFILES
SD0 = 0.03                                   # run6 draw m_est_err ~ N(0, 0.03) (ASSUMED there)
SDS = (0.005, 0.01, 0.015, 0.02, 0.03)       # mass-estimate error sd studied (DESIGN question, not a datum)
TG = np.arange(600.0, 681.0, 5.0)            # thresholds on the v1.1 grid (reproduction check)
TF = np.arange(580.0, 700.01, 1.0)           # fine grid for the normal-fit tails
TSEL = (600.0, 610.0, 620.0, 625.0, 630.0, 635.0, 640.0, 645.0, 650.0)   # detection times reported
R, I, PN, KF, DT = FT.R, FT.I, FT.PN, FT.KF, FT.DT
VNAMES = [v for v, _ in FT.VARS]


def dmodel(par, rec, prof):
    """the D_model term of m2_fc_thrust.reconstruct (k_est_asc 2 axial-force model on the estimated vz)."""
    vze = rec[:, I["vze"]]
    cda = np.where(vze > 0.0, par[PN["kest_cda_nf"]], par[PN["drag_cda_nom"]]) + np.where(FT.legs_state(par, rec, prof),
                                                                                          par[PN["kest_cda_legs"]], 0.0)
    dd = 0.5 * 1.2 * cda * vze * vze
    return np.where(vze > 0.0, dd, -dd)


def part_fly(prof):
    C, _ = FT.cfgs()
    cfg = C[prof]
    D = R.draw(np.random.default_rng(101), 500, cfg)
    ref = np.load(os.path.join(OUT, f"fc_thrust_runs_{prof}.npy"), allow_pickle=True)[0]
    store, checks = {}, {}
    for br, tsc in (("H", None), ("L", FT.CD_TOP)):
        t0 = time.time()
        rows, nbad, dmax = [], 0, 0.0
        for i in range(FT.NR):
            par, res, rec = FT.fly_one(cfg, D[i], tsc)
            rng = np.random.default_rng(20261019 + i + (0 if br == "H" else 100000) + (0 if prof == "A1" else 200000))
            Fr = FT.reconstruct(par, rec, rng, prof)
            ev = FT.evaluate_run(par, res, rec, Fr, prof, rng)
            r0 = ref[f"{prof}|{br}"][i]
            same = (ev["frame_phase"] == r0["frame_phase"]) and all(ev[v]["held_max_fc_N"] == r0[v]["held_max_fc_N"] for v in VNAMES)
            nbad += int(not same)
            p0 = ev["frame_phase"]
            e = float(par[PN["mest"]])
            Dm = dmodel(par, rec, prof)
            _, fc, _, _ = FT.windows(par, res, rec, prof)
            fw = fc[p0::KF]
            fs = (fc & (FT.open_time(fc) >= FT.GUARD))[p0::KF]
            F = rec[:, I["F"]]
            Fmax = par[PN["Fmax"]]
            row = dict(run=i, e=e, ok=ev["ok"], hm={}, err_hi={})
            fts = {v: FT.filt(F, tau)[p0::KF] for v, tau in FT.VARS}
            for sd in SDS:
                c = sd / SD0
                Frc = Fr if sd == SD0 else (Fr - Dm) * (1.0 + c * e) / (1.0 + e) + Dm
                for v, tau in FT.VARS:
                    fa = np.round(FT.filt(Frc, tau)[p0::KF] * 10.0) / 10.0
                    hm, k = FT.held_max(fa, fw)
                    row["hm"][f"{sd:g}|{v}"] = hm
                    if sd == SD0 and k >= 0:
                        dmax = max(dmax, abs(float(Dm[p0::KF][k])))
                    if br == "H":
                        ft = fts[v]
                        b_ = fs & (ft > 0.15 * Fmax) & (ft >= 450.0)
                        row["err_hi"][f"{sd:g}|{v}"] = (fa[b_] / ft[b_] - 1.0).astype(np.float32)
            rows.append(row)
            if (i + 1) % 100 == 0:
                print(f"  {prof} {br}: {i + 1} runs ({time.time() - t0:.0f} s), v1.1 mismatches {nbad}", flush=True)
        store[f"{prof}|{br}"] = rows
        checks[f"{prof}|{br}"] = dict(runs=len(rows), v11_mismatch=nbad, D_model_abs_max_at_held_max_N=dmax)
        print(f"{prof} {br}: {FT.NR} runs in {time.time() - t0:.0f} s; v1.1 mismatches {nbad}; |D_model| at the held max <= "
              f"{dmax:.1f} N", flush=True)
    np.save(os.path.join(OUT, f"fc_thrust_mest_runs_{prof}.npy"), np.array([dict(store=store, checks=checks)], dtype=object),
            allow_pickle=True)


def upper95_zero(n):
    """exact one-sided 95 % upper bound of a rate with 0 events in n trials (Clopper-Pearson)."""
    return float(1.0 - 0.05 ** (1.0 / n))


def part_eval():
    st, chk, ref = {}, {}, {}
    for prof in PROFILES:
        x = np.load(os.path.join(OUT, f"fc_thrust_mest_runs_{prof}.npy"), allow_pickle=True)[0]
        st.update(x["store"])
        chk.update(x["checks"])
        ref.update(np.load(os.path.join(OUT, f"fc_thrust_runs_{prof}.npy"), allow_pickle=True)[0])
    F11 = json.load(open(os.path.join(OUT, "fc_thrust.json")))
    Hrows = [r for k in ref if k.endswith("|H") for r in ref[k]]      # v1.1 order: A1 H then B1 H
    nH = len(Hrows)
    out = dict(version=VERSION, date="2026-10-13", base=F11["version"], sim=F11["sim"], runs_per_branch=F11["runs_per_branch"],
               mass_error_sd_studied=list(SDS), base_draw_sd=SD0,
               sample_sd_of_the_base_draw={k: float(np.std([r["e"] for r in rows])) for k, rows in st.items()},
               method=("paired re-evaluation of the m2_fc_thrust v1.1 flights: F_acc_c = (F_acc - D_model)(1 + c e)/(1 + e) + "
                       "D_model with c = sd / 0.03 (FC estimate only, flights unchanged); stuck-pintle ramps with e -> c e and the "
                       "same noise samples; miss at T <=> no held-20 ms excursion above T before the onset and none within 2 s "
                       "after it"),
               checks=dict(fly=chk), by_sd={})
    # ---- stuck pintle: per case hm_pre / hm_post / detection times (same rng stream as v1.1 for every scale)
    stuck = {}
    for sd in SDS:
        c = sd / SD0
        rng = np.random.default_rng(20261020)
        for v, tau in FT.VARS:
            for F0 in FT.STUCK["F0_N"]:
                for Ff in FT.STUCK["F_final_N"]:
                    for rate in FT.STUCK["rate_N_s"]:
                        pre, post, tsel = np.empty(nH), np.empty(nH), np.full((nH, len(TSEL)), np.nan)
                        for j, r in enumerate(Hrows):
                            bt = r["bias_terms"]
                            e = c * bt["m_est_err"]
                            bf = (1.0 + e) * (1.0 + bt["a_sf"])
                            mm = r["m_mean_burn_kg"] * (1.0 + e)
                            tf, hs = FT.stuck_series(bf, mm * bt["a_bz"], mm, r["a_vrw"], r["vib_sigma"], r["Fmax"], F0, Ff, rate,
                                                     tau, rng)
                            a = tf >= 0.0
                            pre[j] = hs[~a].max()
                            post[j] = hs[a].max()
                            for q, T in enumerate(TSEL):
                                k = np.where(a & (hs > T))[0]
                                if len(k) and pre[j] <= T:
                                    tsel[j, q] = tf[k[0]]
                        stuck[(sd, v, F0, Ff, rate)] = (pre, post, tsel)
        print(f"stuck sd {sd:g} done", flush=True)
    # reproduction of v1.1 miss counts at scale 1
    rep = dict(compared=0, mismatches=0)
    for v in VNAMES:
        for T in TG:
            row = F11["threshold_summary"][f"{v}|{T:g}"]
            for Ff in FT.STUCK["F_final_N"]:
                m = sum(int(np.sum((stuck[(SD0, v, F0, Ff, rt)][0] <= T) & (stuck[(SD0, v, F0, Ff, rt)][1] <= T)))
                        for F0 in FT.STUCK["F0_N"] for rt in FT.STUCK["rate_N_s"])
                rep["compared"] += 1
                rep["mismatches"] += int(m != row[f"miss_{Ff:g}"])
    out["checks"]["stuck_v11_miss_counts_at_sd_0.03"] = rep
    # ---- per sd and variant
    for sd in SDS:
        bys = {}
        for v in VNAMES:
            hmL = {p: np.array([r["hm"][f"{sd:g}|{v}"] for r in st[f"{p}|L"]]) for p in PROFILES}
            hmH = {p: np.array([r["hm"][f"{sd:g}|{v}"] for r in st[f"{p}|H"]]) for p in PROFILES}
            hL = np.concatenate([hmL[p] for p in PROFILES])
            hH = np.concatenate([hmH[p] for p in PROFILES])
            fitL = {p: (float(hmL[p].mean()), float(hmL[p].std())) for p in PROFILES}
            eh = np.concatenate([r["err_hi"][f"{sd:g}|{v}"] for p in PROFILES for r in st[f"{p}|H"]]).astype(float)
            s670 = [stuck[(sd, v, F0, 670.0, rt)] for F0 in FT.STUCK["F0_N"] for rt in FT.STUCK["rate_N_s"]]
            s876 = [stuck[(sd, v, F0, 876.0, rt)] for F0 in FT.STUCK["F0_N"] for rt in FT.STUCK["rate_N_s"]]
            post670 = np.concatenate([s[1] for s in s670])
            pre670 = np.concatenate([s[0] for s in s670])
            post876 = np.concatenate([s[1] for s in s876])
            pre876 = np.concatenate([s[0] for s in s876])
            mu6, sd6 = float(post670.mean()), float(post670.std())
            grid = {}
            for T in TG:
                grid[f"{T:g}"] = dict(
                    false_L={p: int(np.sum(hmL[p] > T)) for p in PROFILES}, false_L_pooled=int(np.sum(hL > T)),
                    false_H_pooled=int(np.sum(hH > T)),
                    false_L_gauss_max=float(max(norm.sf((T - fitL[p][0]) / fitL[p][1]) for p in PROFILES)),
                    miss_670=int(np.sum((pre670 <= T) & (post670 <= T))), early_670=int(np.sum(pre670 > T)),
                    miss_670_gauss=float(norm.cdf((T - mu6) / sd6)),
                    miss_876=int(np.sum((pre876 <= T) & (post876 <= T))), early_876=int(np.sum(pre876 > T)))
            # thresholds: zero observed Pc-lost / healthy false aborts, zero observed 670 N misses, balanced normal-fit tails
            t_fa0 = next((float(T) for T in TG if grid[f"{T:g}"]["false_L_pooled"] == 0 and grid[f"{T:g}"]["false_H_pooled"] == 0),
                         None)
            t_m0 = next((float(T) for T in TG[::-1] if grid[f"{T:g}"]["miss_670"] == 0 and grid[f"{T:g}"]["early_670"] == 0
                         and grid[f"{T:g}"]["early_876"] == 0), None)
            gFA = np.array([max(norm.sf((T - fitL[p][0]) / fitL[p][1]) for p in PROFILES) for T in TF])
            gMS = norm.cdf((TF - mu6) / sd6)
            jb = int(np.argmin(np.maximum(gFA, gMS)))
            tb = float(TF[jb])
            tdet = {}
            for q, T in enumerate(TSEL):
                for Ff, ss in ((670.0, s670), (876.0, s876)):
                    tt = np.concatenate([s[2][:, q] for s in ss])
                    tt = tt[np.isfinite(tt)]
                    tdet[f"T{T:g}|{Ff:g}N"] = ([float(np.median(tt)), float(np.percentile(tt, 99)), float(tt.max())]
                                               if len(tt) else None)
            # detection time from the onset, worst (F0, rate) combination
            tdet_case = {}
            for T_ in (620.0, 630.0, 635.0, 650.0):
                q = TSEL.index(T_)
                for F0 in FT.STUCK["F0_N"]:
                    for Ff in FT.STUCK["F_final_N"]:
                        for rt in FT.STUCK["rate_N_s"]:
                            tt = stuck[(sd, v, F0, Ff, rt)][2][:, q]
                            tt = tt[np.isfinite(tt)]
                            tdet_case[f"T{T_:g}|F0 {F0:g}|Ff {Ff:g}|rate {rt:g}"] = (
                                [float(np.median(tt)), float(np.percentile(tt, 99)), float(tt.max())] if len(tt) else None)
            bys[v] = dict(
                err_F_ge_450N=dict(p0135=float(np.percentile(eh, 0.135)), p99865=float(np.percentile(eh, 99.865)),
                                   three_sigma=float(max(-np.percentile(eh, 0.135), np.percentile(eh, 99.865))),
                                   mean=float(eh.mean()), sd=float(eh.std()), frames=int(len(eh))),
                held_max_L_p50_p99_max_N={p: [float(np.median(hmL[p])), float(np.percentile(hmL[p], 99)), float(hmL[p].max())]
                                          for p in PROFILES},
                held_max_H_max_N=float(hH.max()),
                normal_fit_L_mean_sd_N={p: list(fitL[p]) for p in PROFILES},
                stuck670_held_post_mean_sd_min_N=[mu6, sd6, float(post670.min())],
                grid=grid,
                threshold_zero_false_aborts_N=t_fa0, threshold_zero_670_misses_N=t_m0,
                window_observed=(t_fa0 is not None and t_m0 is not None and t_fa0 <= t_m0),
                balanced_threshold_normal_fit=dict(T_N=tb, p_false_abort_Pc_lost=float(gFA[jb]), p_miss_670=float(gMS[jb])),
                detection_time_from_onset_p50_p99_max_s=tdet, detection_time_by_case_s=tdet_case)
        out["by_sd"][f"{sd:g}"] = bys
        x = bys["tau20ms"]
        g = x["grid"]
        print(f"sd {sd:g} tau20: 3s {100 * x['err_F_ge_450N']['three_sigma']:.2f} % | FA0 at {x['threshold_zero_false_aborts_N']} "
              f"| miss0 at {x['threshold_zero_670_misses_N']} | balanced {x['balanced_threshold_normal_fit']} | 620: "
              f"{g['620']} | 650: {g['650']}", flush=True)
    # reproduction of the v1.1 held-max statistics at scale 1 (Pc-lost false aborts at 650 N)
    rp = {}
    for v in VNAMES:
        for p in PROFILES:
            a = int(sum(1 for r in st[f"{p}|L"] if r["hm"][f"{SD0:g}|{v}"] > 650.0))
            b = F11["branches"][f"{p}|L"][v]["false_aborts"]["fc|650"]["n"]
            rp[f"{p}|L|{v}|650"] = [a, b]
    out["checks"]["false_aborts_650_vs_v11"] = rp
    out["checks"]["err_3sigma_tau20_F_ge_450N_vs_v11"] = [out["by_sd"][f"{SD0:g}"]["tau20ms"]["err_F_ge_450N"]["three_sigma"],
                                                          F11["error_3sigma_healthy_pooled"]["tau20ms"]["three_sigma_F_ge_450N"]]
    out["note"] = ("false_L: Pc-lost runs (thrust_scale 1.143) whose held maximum in the fc window exceeds T (of 500 per profile); "
                   "false_H: healthy runs (of 1000); miss_670 / miss_876: stuck-pintle cases (of 4000: 1000 healthy-run error sets "
                   "x F0 500 / 150 N x 2.5 / 3.6 kN/s) without an abort within 2 s; early_*: held excursion above T before the onset "
                   "(an alarm at F0, counted apart); *_gauss: normal fits (model-dependent tails); one-sided 95 % upper bound with 0 "
                   f"observed: {100 * upper95_zero(1000):.2f} % per Pc-lost flight (1000 flights). The 4000 stuck cases reuse the "
                   "1000 healthy-run error sets (4 ramp cases each), and a miss is driven by the run's bias, so the effective "
                   f"sample for a miss rate is about 1000 (0 observed: upper 95 % {100 * upper95_zero(1000):.2f} %), not 4000")
    with open(os.path.join(OUT, "fc_thrust_mest.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("checks", json.dumps(out["checks"])[:1500], flush=True)
    plot(out)
    print("wrote", os.path.join(OUT, "fc_thrust_mest.json"), flush=True)


def plot(out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
    cols = dict(zip([f"{s:g}" for s in SDS], ("tab:green", "tab:olive", "tab:blue", "tab:orange", "tab:red")))
    for ax, v in zip(axs, ("tau20ms", "box10ms")):
        for sd in [f"{s:g}" for s in SDS]:
            x = out["by_sd"][sd][v]
            T = np.array([float(t) for t in x["grid"]])
            fa = np.array([g["false_L_pooled"] for g in x["grid"].values()]) / 1000.0
            ms = np.array([g["miss_670"] for g in x["grid"].values()]) / 4000.0
            ax.semilogy(T, np.where(fa > 0, fa, np.nan), "o-", color=cols[sd], ms=3, lw=1.2,
                        label=f"mass sd {100 * float(sd):g} %: Pc-lost false aborts (of 1000)")
            ax.semilogy(T, np.where(ms > 0, ms, np.nan), "s--", color=cols[sd], ms=3, lw=1.0,
                        label=f"mass sd {100 * float(sd):g} %: 670 N missed (of 4000)")
        ax.axvline(650, color="k", lw=0.8, ls=":")
        ax.set_ylim(1e-4, 1.0)
        ax.set_xlabel("threshold T [N], held 20 ms (3 frames)")
        ax.set_ylabel("fraction (empirical; points at zero not drawn)")
        ax.set_title(f"{v}: Pc-lost false aborts vs stuck 670 N misses by FSW mass-estimate error", fontsize=9)
        ax.grid(alpha=0.3, which="both")
        ax.legend(fontsize=6, loc="lower left", ncol=2)
    fig.text(0.01, 0.01, "SIM m2_fc_thrust_mest v1 on the m2_fc_thrust v1.1 flights (sim6/run6 v2.7.1-dev, 500 runs per profile and "
                         "branch); mass-estimate error scaled in the FC estimate only; vibration 2 m/s2 at F_max ASSUMED",
             fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    p = os.path.join(OUT, "fc_thrust_mest_v1.png")
    fig.savefig(p, dpi=110)
    print("wrote", p, flush=True)


if __name__ == "__main__":
    if "fly" in PARTS:
        for p_ in PROFILES:
            part_fly(p_)
    if "eval" in PARTS:
        part_eval()
