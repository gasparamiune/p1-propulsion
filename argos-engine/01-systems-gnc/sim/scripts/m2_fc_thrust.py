"""m2_fc_thrust v1 (GNC, 2026-10-13): accelerometer thrust estimate for the FC_THRUST CAN frame and the over-thrust abort.

Lead decision 2026-10-13 (interfaces/CHANGELOG.md, over_thrust_abort): firmware v2.7 flies open loop on Pc loss; an
accelerometer over-thrust abort uses the CAN frame FC_THRUST (ID 0x024, >= 100 Hz, sequence, accelerometer thrust in 0.1 N
steps, valid flag, CRC-8, raw or lightly filtered, tau <= 20 ms); provisional threshold 650 N held 20 ms (500 N x 1.143 Cd band
x 1.10 estimate error, ASSUMED); a stale (> 50 ms) or invalid estimate only raises a flag. GNC publishes the estimate's 3-sigma
error and latency, the false-abort rate (Pc-lost branch) and the stuck-pintle detection time (670-876 N), and confirms or
proposes the threshold.

Estimate (FC side, what FC_THRUST carries): F_acc = m_est f_z + D_model, f_z = measured axial specific force (IMU), m_est =
FSW mass estimate, D_model = the k_est_asc 2 nominal axial-force model (rho 1.2; + going up nose-first, - going down
tail-first); first-order low-pass tau at the 1 kHz IMU rate, sampled at the 100 Hz frame rate, 0.1 N steps.
Reconstruction on recorded 6-DOF flights (sim6/run6 v2.7.1-dev, 1 ms recorder): true thrust F, true axial specific force at
the CG (fax), body rates, CG station, true mass, vz; the run's own IMU draws (a_sf, a_bz) and FSW mass-estimate error
(m_est_err, ASSUMED N(0, 0.03)) from the Monte Carlo draw table; white noise with the sim's IMU class density and the
thrust-proportional vibration term (vib_sigma 2.0 m/s2 at F_max, ASSUMED) from an own generator (seed 20261019 + run):
the sim6 measurement model (fm = fimu (1 + a_sf) + b_a + (a_vrw / sqrt(dt) + vib F / F_max) N(0, 1)) with other noise
samples (statistically equivalent, not the same samples). The sim's own k_hat channel (tau 0.1 s) is compared as a check of
the reconstruction (same mass error and scale factor).
Branches (A1 at the v2.8 relight planning value GNC_FCT_PLAN with the liquid-line start delay, B1 85 m; FSW v2.7 k_est_asc 2;
pc2 bases, no growth):
  H  healthy, Pc loop valid (thrust_scale ~ N(1, 0.05) as drawn)
  L  Pc lost from ignition at the top of the open-loop band: thrust_scale = 1.143 on every run (lead's Cd band factor; worst
     case for false aborts; the other draws unchanged)
  S  stuck pintle: synthetic thrust ramp at 2.5 / 3.6 kN/s from 500 N (ascent) or 150 N (landing) to 670 / 876 N, through each
     H run's error terms (scale x mass error, bias, noise at that thrust), random frame phase; detection time from the ramp
     start and misses (no abort within 2 s)
Armed window: h_est > 1 m after liftoff until touchdown (the accelerometer reads the ground reaction on the legs).
Env: GNC_IFACE, GNC_ACT_RATE, GNC_FCT_OUT (out/fc_thrust), GNC_FCT_N (runs per branch, default 200), GNC_FCT_PLAN (A1
relight planning value, default 0.65), GNC_FCT_PARTS (fly,eval)."""
import json
import os
import sys
import time
import numpy as np
from scipy.signal import lfilter
from scipy.stats import norm

os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_prop_closure as PC  # noqa: E402

VERSION = "m2_fc_thrust v1"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_FCT_OUT", f"{S}/fc_thrust")
NR = int(os.environ.get("GNC_FCT_N", "200"))
PLAN = float(os.environ.get("GNC_FCT_PLAN", "0.65"))
PARTS = os.environ.get("GNC_FCT_PARTS", "fly,eval").split(",")
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
DT = 1.0e-3
FRAME = 0.010            # REQ lead: >= 100 Hz
TAUS = (0.0, 0.010, 0.020)   # raw at the 1 kHz IMU rate, 10 ms, 20 ms (REQ lead: tau <= 20 ms)
HOLD = 0.020             # REQ lead: held 20 ms
THR = (600.0, 620.0, 635.0, 650.0, 675.0)
CD_TOP = 1.143           # REQ lead (Cd band factor of the provisional threshold), ASSUMED there
STUCK = dict(F_final_N=(670.0, 876.0), rate_N_s=(2500.0, 3600.0), F0_N=(500.0, 150.0))   # REQ lead relay (stuck-pintle case)


def cfgs():
    import m2_relight_v28 as V   # liquid-line E0->E2 table (Combustion RC-03 preopened liquid), same construction as the relight study
    tq = tuple(V.e0e2_tables()["liq"]["quantiles_5pct_s"])
    a1 = dict(PC.DC["A1"], k_est_asc=2, t_ign_add=0.0, t_ign_est=PLAN, t_ign_q=tq)
    b1 = dict(PC.DC["B1"], h_target=85.0, k_est_asc=2)
    return {"A1": R.cfg_of(**dict(a1, m_n2o=PC.M_TANK)), "B1": R.cfg_of(**dict(b1, m_n2o=PC.M_TANK))}, (tq is not None)


def lp(x, tau):
    if tau <= 0.0:
        return x.copy()
    a = DT / (tau + DT)
    y, _ = lfilter([a], [1.0, -(1.0 - a)], x, zi=[(1.0 - a) * x[0]])
    return y


def held(above, nhold):
    """index of the first frame at which 'above' has been true on nhold + 1 consecutive frames (span >= HOLD), else -1."""
    run = 0
    for k, a in enumerate(above):
        run = run + 1 if a else 0
        if run > nhold:
            return k
    return -1


def fly_one(cfg, dr, tsc=None):
    d = dict(dr)
    if tsc is not None:
        d["thrust_scale"] = float(tsc)
    c, disp = R.run_cfg(cfg, d)
    c = dict(c, rec_dt=DT)
    par = R.build(c, disp)[0]
    res, rec, _ = R.fly(c, disp, nrec=100000)
    return par, res, rec


def reconstruct(par, rec, rng, prof):
    F = rec[:, I["F"]]
    Fmax = par[PN["Fmax"]]
    rz = par[PN["z_imu"]] - rec[:, I["zcg"]]
    fimu = rec[:, I["fax"]] - (rec[:, I["wx"]] ** 2 + rec[:, I["wy"]] ** 2) * rz
    vib = np.where(F > 1.0, par[PN["vib_sigma"]] * F / Fmax, 0.0)
    fm = fimu * (1.0 + par[PN["a_sf"]]) + par[PN["a_bz"]] + (par[PN["a_vrw"]] / np.sqrt(DT) + vib) * rng.standard_normal(len(F))
    m_est = rec[:, I["m"]] * (1.0 + par[PN["mest"]])
    vz = rec[:, I["vz"]]
    legs = np.ones(len(F), bool) if prof == "B1" else (rec[:, I["phase"]] >= 4)
    cda = np.where(vz > 0.0, par[PN["kest_cda_nf"]], par[PN["drag_cda_nom"]]) + np.where(legs, par[PN["kest_cda_legs"]], 0.0)
    dd = 0.5 * 1.2 * cda * vz * vz
    return fm * m_est + np.where(vz > 0.0, dd, -dd)


def frames(x, phase0=0):
    k = int(round(FRAME / DT))
    return x[phase0::k]


def evaluate_run(par, res, rec, Facc_raw, prof):
    t = rec[:, I["t"]]
    F = rec[:, I["F"]]
    Fmax = par[PN["Fmax"]]
    hest = rec[:, I["hest"]]
    td = float(res["td_t"]) if res["td_t"] > 0 else t[-1]
    # armed: h_est > 1 m after the first time it exceeds 1 m, until touchdown
    up = np.where(hest > 1.0)[0]
    armed = np.zeros(len(t), bool)
    if len(up):
        armed[up[0]:] = True
    armed &= (t < td) & (hest > 1.0)
    out = {}
    for tau in TAUS:
        ya = lp(Facc_raw, tau)
        yt = lp(F, tau)
        fa, ft, am = frames(ya), frames(yt), frames(armed)
        fa = np.round(fa * 10.0) / 10.0            # 0.1 N steps
        burn = am & (ft > 0.15 * Fmax)
        e = fa[burn] / ft[burn] - 1.0 if burn.any() else np.array([])
        nh = int(round(HOLD / FRAME))
        ab = {}
        for T in THR:
            k = held(am & (fa > T), nh)
            ab[f"{T:g}"] = (float(k * FRAME) if k >= 0 else None)
        out[f"tau{1e3 * tau:g}ms"] = dict(err_mean=float(e.mean()) if len(e) else None, err_std=float(e.std()) if len(e) else None,
                                          err_min=float(e.min()) if len(e) else None, err_max=float(e.max()) if len(e) else None,
                                          err_samples=e, Facc_max_armed_N=float(fa[am].max()) if am.any() else None,
                                          F_true_max_armed_N=float(ft[am].max()) if am.any() else None, abort_time_s=ab)
    # sim k_hat check: k_hat (tau 0.1 s, landing burn / B ascent) vs (1 + m_est_err) x thrust_scale x (1 + a_sf) (expected bias)
    kh = rec[:, I["keff"]]
    ph = rec[:, I["phase"]]
    sel = armed & (F > 0.3 * Fmax) & ((ph == 5) | (prof == "B1"))
    exp_k = (1.0 + par[PN["mest"]]) * par[PN["thrust_scale"]] * (1.0 + par[PN["a_sf"]])
    out["k_hat_check"] = dict(k_hat_median=float(np.median(kh[sel])) if sel.any() else None, expected=float(exp_k))
    out["bias_terms"] = dict(m_est_err=float(par[PN["mest"]]), a_sf=float(par[PN["a_sf"]]), a_bz=float(par[PN["a_bz"]]),
                             thrust_scale=float(par[PN["thrust_scale"]]))
    out["ok"] = bool(R.success(res))
    return out


def stuck_detect(bias_factor, a_bz_N, noise_sd_fn, F0, Ff, rate, tau, T, rng):
    """detection time [s] from the ramp start, or None (miss within 2 s)."""
    n = int(2.5 / DT)
    tt = np.arange(n) * DT - 0.5
    Ft = np.where(tt < 0.0, F0, np.minimum(F0 + rate * np.maximum(tt, 0.0), Ff))
    x = bias_factor * Ft + a_bz_N + noise_sd_fn(Ft) * rng.standard_normal(n)
    y = lp(x, tau)
    ph = int(rng.integers(0, int(round(FRAME / DT))))
    fy = np.round(y[ph::int(round(FRAME / DT))] * 10.0) / 10.0
    ft = tt[ph::int(round(FRAME / DT))]
    k = held(fy > T, int(round(HOLD / FRAME)))
    if k < 0:
        return None
    return float(ft[k]) if ft[k] >= 0.0 else -1.0   # -1: above the threshold before the failure (false alarm at F0)


def part_fly():
    os.makedirs(OUT, exist_ok=True)
    C, has_tq = cfgs()
    store = {}
    for prof, cfg in C.items():
        D = R.draw(np.random.default_rng(101), 500, cfg)
        for br, tsc in (("H", None), ("L", CD_TOP)):
            t0 = time.time()
            rows = []
            for i in range(NR):
                par, res, rec = fly_one(cfg, D[i], tsc)
                rng = np.random.default_rng(20261019 + i + (0 if br == "H" else 100000) + (0 if prof == "A1" else 200000))
                Fr = reconstruct(par, rec, rng, prof)
                ev = evaluate_run(par, res, rec, Fr, prof)
                ev["run"] = i
                ev["m_at_liftoff_kg"] = float(rec[0, I["m"]])
                ev["a_vrw"] = float(par[PN["a_vrw"]])
                ev["vib_sigma"] = float(par[PN["vib_sigma"]])
                ev["m_mean_armed_kg"] = float(np.mean(rec[:, I["m"]]))
                rows.append(ev)
            store[f"{prof}|{br}"] = rows
            print(f"{prof} {br}: {NR} runs in {time.time() - t0:.0f} s; P {np.mean([r['ok'] for r in rows]):.3f}", flush=True)
    np.save(os.path.join(OUT, "fc_thrust_runs.npy"), np.array([store], dtype=object), allow_pickle=True)
    with open(os.path.join(OUT, "fc_thrust_meta.json"), "w") as f:
        json.dump(dict(version=VERSION, sim=s6.SIM6_VERSION, n_runs=NR, a1_plan=PLAN, a1_liquid_start_delay_table=has_tq), f)


def part_eval():
    store = np.load(os.path.join(OUT, "fc_thrust_runs.npy"), allow_pickle=True)[0]
    meta = json.load(open(os.path.join(OUT, "fc_thrust_meta.json")))
    out = dict(version=VERSION, date="2026-10-13", sim=meta["sim"], runs_per_branch=meta["n_runs"], a1_planning_value_s=meta["a1_plan"],
               a1_liquid_start_delay_table=meta["a1_liquid_start_delay_table"],
               estimate="F_acc = m_est f_z + D_model (signed), first-order low-pass at 1 kHz, 100 Hz frames, 0.1 N steps",
               thresholds_N=list(THR), hold_s=HOLD, frame_s=FRAME, cd_top=CD_TOP, stuck_case=STUCK, branches={})
    pooled = {}
    for key, rows in store.items():
        prof, br = key.split("|")
        b = {}
        for tl in [f"tau{1e3 * t:g}ms" for t in TAUS]:
            e = np.concatenate([r[tl]["err_samples"] for r in rows if len(r[tl]["err_samples"])])
            bias = np.array([r[tl]["err_mean"] for r in rows if r[tl]["err_mean"] is not None])
            sd = np.array([r[tl]["err_std"] for r in rows if r[tl]["err_std"] is not None])
            fmx = np.array([r[tl]["Facc_max_armed_N"] for r in rows if r[tl]["Facc_max_armed_N"] is not None])
            ftm = np.array([r[tl]["F_true_max_armed_N"] for r in rows if r[tl]["F_true_max_armed_N"] is not None])
            ab = {T: [r[tl]["abort_time_s"][T] for r in rows] for T in rows[0][tl]["abort_time_s"]}
            b[tl] = dict(err_pooled_p0135_p50_p99865=[float(np.percentile(e, 0.135)), float(np.median(e)), float(np.percentile(e, 99.865))],
                         err_3sigma_pooled=float(max(-np.percentile(e, 0.135), np.percentile(e, 99.865))),
                         err_per_run_bias_sd=float(bias.std()), err_per_run_bias_min_max=[float(bias.min()), float(bias.max())],
                         err_within_run_sd_median_max=[float(np.median(sd)), float(sd.max())],
                         Facc_max_armed_p50_p99_max_N=[float(np.median(fmx)), float(np.percentile(fmx, 99)), float(fmx.max())],
                         F_true_max_armed_p50_max_N=[float(np.median(ftm)), float(ftm.max())],
                         false_aborts={T: dict(n=int(sum(x is not None for x in v)), of=len(v),
                                               upper95=float(1.0 - 0.05 ** (1.0 / len(v))) if not any(x is not None for x in v) else None)
                                       for T, v in ab.items()},
                         n_samples=int(len(e)))
            if br == "H":
                pooled.setdefault(tl, []).append(e)
        kh = [(r["k_hat_check"]["k_hat_median"], r["k_hat_check"]["expected"]) for r in rows if r["k_hat_check"]["k_hat_median"]]
        b["k_hat_check_sim"] = dict(n=len(kh), median_ratio=float(np.median([a / x for a, x in kh])) if kh else None,
                                    ratio_p01_p99=[float(np.percentile([a / x for a, x in kh], 1)), float(np.percentile([a / x for a, x in kh], 99))] if kh else None,
                                    note="sim6 k_hat (tau 0.1 s) / ((1 + m_est_err) thrust_scale (1 + a_sf)): ~1 confirms the error model")
        b["P"] = float(np.mean([r["ok"] for r in rows]))
        b["bias_sd_terms"] = dict(m_est_err_sd=float(np.std([r["bias_terms"]["m_est_err"] for r in rows])),
                                  a_sf_sd=float(np.std([r["bias_terms"]["a_sf"] for r in rows])))
        out["branches"][key] = b
        print(f"{key}: P {b['P']:.3f} | 3sigma (tau 20 ms) {100 * b['tau20ms']['err_3sigma_pooled']:.2f} % | bias sd "
              f"{100 * b['tau20ms']['err_per_run_bias_sd']:.2f} % | F_acc max p99/max {b['tau20ms']['Facc_max_armed_p50_p99_max_N'][1]:.0f}/"
              f"{b['tau20ms']['Facc_max_armed_p50_p99_max_N'][2]:.0f} N | false aborts " +
              ", ".join(f"{T}: {v['n']}" for T, v in b['tau20ms']['false_aborts'].items()), flush=True)
    # error budget (pooled healthy A1 + B1, armed burning frames)
    eb = {}
    for tl, es in pooled.items():
        e = np.concatenate(es)
        eb[tl] = dict(p0135=float(np.percentile(e, 0.135)), p99865=float(np.percentile(e, 99.865)), sd=float(e.std()), mean=float(e.mean()),
                      three_sigma=float(max(-np.percentile(e, 0.135), np.percentile(e, 99.865))))
    out["error_3sigma_healthy_pooled"] = eb
    # decomposition: the FSW mass-estimate error (ASSUMED N(0, 0.03), constant per run) vs the rest (scale factor, bias, noise,
    # drag model, gimbal cosine, rotation terms): e_rest = (1 + e) / (1 + m_est_err) - 1 per frame
    rest = []
    for key in ("A1|H", "B1|H"):
        for r in store[key]:
            x = r["tau20ms"]["err_samples"]
            if len(x):
                rest.append((1.0 + x) / (1.0 + r["bias_terms"]["m_est_err"]) - 1.0)
    er = np.concatenate(rest)
    sd_rest = float(er.std())
    sens = {}
    for sm in (0.005, 0.01, 0.02, 0.03):
        s3 = 3.0 * float(np.sqrt(sm * sm + sd_rest * sd_rest))
        sens[f"{sm:g}"] = dict(three_sigma=s3, window_N=[float(500.0 * CD_TOP * (1 + s3)), float(670.0 * (1 - s3))],
                               window_exists=bool(500.0 * CD_TOP * (1 + s3) < 670.0 * (1 - s3)),
                               p_miss_670N_at_650N=float(norm.cdf((650.0 / 670.0 - 1.0 - float(er.mean())) / np.sqrt(sm * sm + sd_rest * sd_rest))),
                               p_false_571N_at_650N=float(norm.sf((650.0 / 571.5 - 1.0 - float(er.mean())) / np.sqrt(sm * sm + sd_rest * sd_rest))))
    out["error_decomposition_tau20ms"] = dict(
        rest_mean=float(er.mean()), rest_sd=sd_rest, rest_p0135_p99865=[float(np.percentile(er, 0.135)), float(np.percentile(er, 99.865))],
        mass_estimate_error_sd_assumed=0.03,
        sensitivity_to_mass_estimate_sd=sens,
        note="rest = scale factor, bias, vibration and white noise after the filter, drag-model error, gimbal cosine, rotation "
             "terms; the mass-estimate error dominates the 3-sigma error")
    # stuck-pintle detection through each healthy run's error terms (A1 and B1 H rows)
    rng = np.random.default_rng(20261020)
    det = {}
    H = store["A1|H"] + store["B1|H"]
    for tau in (0.010, 0.020):
        for T in THR:
            for F0 in STUCK["F0_N"]:
                for Ff in STUCK["F_final_N"]:
                    for rate in STUCK["rate_N_s"]:
                        ts, miss, early = [], 0, 0
                        for r in H:
                            bt = r["bias_terms"]
                            bf = (1.0 + bt["m_est_err"]) * (1.0 + bt["a_sf"])
                            mm = r["m_mean_armed_kg"] * (1.0 + bt["m_est_err"])
                            sdf = (lambda F_, r=r, mm=mm: mm * (r["a_vrw"] / np.sqrt(DT) + r["vib_sigma"] * F_ / 500.0))
                            x = stuck_detect(bf, mm * bt["a_bz"], sdf, F0, Ff, rate, tau, T, rng)
                            if x is None:
                                miss += 1
                            elif x < 0:
                                early += 1
                            else:
                                ts.append(x)
                        key = f"tau{1e3 * tau:g}ms|T{T:g}|F0 {F0:g}|Ff {Ff:g}|rate {rate:g}"
                        det[key] = dict(n=len(H), miss=miss, alarm_before_failure=early,
                                        t_detect_p50_p99_max_s=[float(np.median(ts)), float(np.percentile(ts, 99)), float(max(ts))] if ts else None)
    out["stuck_pintle_detection"] = det
    for k in [k for k in det if "tau20ms" in k and ("T650" in k or "T620" in k)]:
        print(k, det[k], flush=True)
    # Gaussian extrapolation on the healthy 3-sigma (tau 20 ms): false-abort and miss probabilities per threshold
    sd = eb["tau20ms"]["sd"]
    mu = eb["tau20ms"]["mean"]
    ext = {}
    for T in THR:
        ext[f"{T:g}"] = dict(
            p_false_abort_at_571N_Pc_lost_top=float(norm.sf((T / (500.0 * CD_TOP) - 1.0 - mu) / sd)),
            p_false_abort_at_525N_healthy_3sigma_top=float(norm.sf((T / 525.0 - 1.0 - mu) / sd)),
            p_miss_670N=float(norm.cdf((T / 670.0 - 1.0 - mu) / sd)),
            p_miss_876N=float(norm.cdf((T / 876.0 - 1.0 - mu) / sd)))
    out["gaussian_extrapolation_tau20ms"] = dict(model="relative error ~ N(mean, sd) of the pooled healthy frames; steady thrust at the "
                                                       "named level; per-flight (the bias is per run)", mean=mu, sd=sd, by_threshold_N=ext)
    lo, hi = 500.0 * CD_TOP, 670.0
    out["threshold_window"] = dict(
        healthy_max_N=lo, stuck_min_N=hi,
        max_relative_3sigma_error_for_a_window=float((hi - lo) / (hi + lo)),
        window_at_measured_3sigma_N=[float(lo * (1 + eb["tau20ms"]["three_sigma"])), float(hi * (1 - eb["tau20ms"]["three_sigma"]))])
    with open(os.path.join(OUT, "fc_thrust.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "fc_thrust.json"))


if __name__ == "__main__":
    if "fly" in PARTS:
        part_fly()
    if "eval" in PARTS:
        part_eval()
