"""m2_khat_offset v1.1 (GNC, 2026-10-13): diagnostic of the A1 k_hat offset (review REV-GNC-1 RG-16 item 3).

Finding under review (staging v3.1, fc_thrust.json k_hat_check_sim): the sim6 thrust-effectiveness estimate k_hat (tau 0.1 s) divided
by the error-model value (1 + m_est_err) thrust_scale (1 + a_sf) has median 0.986 in A1 (landing burn) and 0.999 in B1 (85 m hop).
Reviewer hypothesis: the comparison windows differ (the A1 estimator runs only in the landing burn).
Candidate terms (each computed per 1 ms sample from the recorded 6-DOF truth, then the per-run median over the comparison window
fc & F > 0.3 F_max & (phase 5 or B1), then the median over runs, as in the original check):
  dir    thrust direction: cos(delta) - 1 (engine angles dgx, dgy; body-axis thrust component)
  aero   axial aerodynamic force residual: (A_z + s d_model) / F, A_z = m f_ax - F cos(delta) (truth non-thrust axial force at the CG:
         aerodynamics; ground and drogue excluded by the window), d_model the FSW nominal model on the estimated vertical velocity
  bias   accelerometer bias a_bz m / F
  lever  IMU lever-arm term -(wx^2 + wy^2) r_z m / F
  lag    k_hat (sim, noisy, filtered) against the noise-free k_raw filtered with the same tau, and against k_raw unfiltered
The sum of the terms is checked against the noise-free k_raw ratio (closure), and the aerodynamic residual is regressed on the run
draws (ca_tf, k_retro, rho0, wind) and on the velocity state (|v_rel| / |vz|, vz_est - vz).
v1.1: per-run percentiles (p01 / p50 / p99 over the window samples) of each term and of the total, the total with the lever arm
compensated (FSW adds (wx^2 + wy^2) r_z from its gyro rates and CG model) and with lever arm and direction compensated (encoder
angles), and the body-rate magnitude in the window.
Configuration: m2_fc_thrust v1.1 branch H (A1 plan 0.81 s with the liquid-line start table, B1 85 m; k_est_asc 2; seed-101 draws).
Env: GNC_KHO_N (runs per profile, 200), GNC_KHO_OUT (out/khat_offset)."""
import json
import os
import sys
import time
import numpy as np
from scipy.signal import lfilter

os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_fc_thrust as FT  # noqa: E402

VERSION = "m2_khat_offset v1.1"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_KHO_OUT", f"{S}/khat_offset")
NR = int(os.environ.get("GNC_KHO_N", "200"))
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
DT = 1.0e-3


def lp(x, tau):
    a = DT / (tau + DT)
    y, _ = lfilter([a], [1.0, -(1.0 - a)], x, zi=[(1.0 - a) * x[0]])
    return y


def one(par, res, rec, prof, dr):
    t = rec[:, I["t"]]
    F = rec[:, I["F"]]
    Fmax = par[PN["Fmax"]]
    ph = rec[:, I["phase"]]
    air, fc, lit, drog = FT.windows(par, res, rec, prof)
    sel = fc & (F > 0.3 * Fmax) & ((ph == 5) | (prof == "B1"))
    if sel.sum() < 50:
        return None
    m = rec[:, I["m"]]
    mest = par[PN["mest"]]
    asf = par[PN["a_sf"]]
    abz = par[PN["a_bz"]]
    tsc0 = par[PN["thrust_scale"]]
    tsc = rec[:, I["tsc"]]
    rz = par[PN["z_imu"]] - rec[:, I["zcg"]]
    fax = rec[:, I["fax"]]
    lev = -(rec[:, I["wx"]] ** 2 + rec[:, I["wy"]] ** 2) * rz
    fimu = fax + lev
    dx, dy = np.radians(rec[:, I["dgx"]]), np.radians(rec[:, I["dgy"]])
    cosd = np.cos(dx) * np.cos(dy)
    vze = rec[:, I["vze"]]
    vz = rec[:, I["vz"]]
    cda = np.where(vze > 0.0, par[PN["kest_cda_nf"]], par[PN["drag_cda_nom"]]) + np.where(FT.legs_state(par, rec, prof),
                                                                                          par[PN["kest_cda_legs"]], 0.0)
    d = 0.5 * 1.2 * cda * vze * vze
    sd = np.where(vze > 0.0, d, -d)
    Fs = np.maximum(F, 1e-6)
    Fmod = Fs / tsc
    exp_k = (1.0 + mest) * tsc0 * (1.0 + asf)
    kraw_nf = ((fimu * (1.0 + asf) + abz) * m * (1.0 + mest) + sd) / Fmod
    tau = par[PN["k_est_tau"]]
    # filter the noise-free k_raw only where the sim's estimator runs (it holds k_hat elsewhere): emulate by filtering inside
    # each contiguous estimator-active block, starting from the sim's k_hat at the block start
    kh = rec[:, I["keff"]]
    est_on = (F > 0.15 * Fmax * tsc) & (((ph == 5) | (ph == 6)) if prof == "A1" else ((ph >= 1) & (ph <= 3) & (rec[:, I["hest"]] > 1.0)))
    kf = kh.copy()
    on_idx = np.where(est_on)[0]
    if len(on_idx):
        brk = np.where(np.diff(on_idx) > 1)[0]
        starts = np.r_[on_idx[0], on_idx[brk + 1]]
        ends = np.r_[on_idx[brk], on_idx[-1]]
        a = DT / tau
        for s0, e0 in zip(starts, ends):
            y = kh[s0 - 1] if s0 > 0 else 1.0
            for j in range(s0, e0 + 1):
                y += (kraw_nf[j] - y) * a
                kf[j] = y
    Az = m * fax - F * cosd
    terms = dict(dir=cosd - 1.0, aero=(Az * (1.0 + mest) * (1.0 + asf) + sd) / (Fs * (1.0 + mest) * (1.0 + asf)),
                 bias=abz * m / (Fs * (1.0 + asf)), lever=lev * m / Fs)
    ratio_nf = kraw_nf / (tsc / tsc0) / exp_k - 1.0          # tsc / tsc0 = in-flight growth factor (1 without growth)
    ratio_kh = kh / exp_k - 1.0
    ratio_kf = kf / (tsc / tsc0) / exp_k - 1.0
    med = lambda x: float(np.median(x[sel]))  # noqa: E731
    pq = lambda x: [float(v) for v in np.percentile(x[sel], (1, 50, 99))]  # noqa: E731
    wt = np.degrees(np.sqrt(rec[:, I["wx"]] ** 2 + rec[:, I["wy"]] ** 2))
    out = dict(n_sel=int(sel.sum()), ratio_kh=med(ratio_kh), ratio_kf_nf=med(ratio_kf), ratio_kraw_nf=med(ratio_nf),
               terms={k: med(v) for k, v in terms.items()}, closure=med(ratio_nf - sum(terms.values())),
               Az_N=med(Az), d_model_N=med(d), F_N=med(F), vz=med(vz), vze=med(vze), vze_minus_vz=med(vze - vz),
               Vrel_over_vz=med(np.sqrt(np.maximum(rec[:, I["qdyn"]], 0.0) * 2.0 / 1.2) / np.maximum(np.abs(vz), 1e-3)),
               qdyn=med(rec[:, I["qdyn"]]), cos_delta=med(cosd), t_sel=[float(t[sel][0]), float(t[sel][-1])],
               growth_factor=med(tsc / tsc0), m_kg=med(m),
               draws=dict(ca_tf=dr["_ca_tf"], k_retro=dr["_k_retro"], rho0=dr["_rho0"], wind=dr["_wind"], mest=float(mest),
                          a_sf=float(asf), a_bz=float(abz), thrust_scale=float(tsc0)),
               ok=bool(R.success(res)))
    out["pct"] = dict(total=pq(ratio_nf), total_lever_comp=pq(ratio_nf - terms["lever"]),
                      total_lever_dir_comp=pq(ratio_nf - terms["lever"] - terms["dir"]),
                      **{k: pq(v) for k, v in terms.items()}, body_rate_deg_s=pq(wt))
    out["r_z_m"] = med(rz)
    # where in the window: first 0.5 s of the window against the rest (transient after the light / drogue release)
    t0 = t[sel][0]
    early = sel & (t < t0 + 0.5)
    late = sel & (t >= t0 + 0.5)
    out["ratio_kh_early_late"] = [float(np.median(ratio_kh[early])) if early.any() else None,
                                  float(np.median(ratio_kh[late])) if late.any() else None]
    out["aero_early_late"] = [float(np.median(terms["aero"][early])) if early.any() else None,
                              float(np.median(terms["aero"][late])) if late.any() else None]
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    C, _ = FT.cfgs()
    res_all = {}
    for prof in ("A1", "B1"):
        cfg = C[prof]
        D = R.draw(np.random.default_rng(101), 500, cfg)
        rows = []
        t0 = time.time()
        for i in range(NR):
            par, res, rec = FT.fly_one(cfg, D[i])
            r = one(par, res, rec, prof, D[i])
            if r is not None:
                r["run"] = i
                rows.append(r)
        res_all[prof] = rows
        print(f"{prof}: {len(rows)} runs ({time.time() - t0:.0f} s)", flush=True)
    summ = {}
    for prof, rows in res_all.items():
        g = lambda k: np.array([r[k] for r in rows], float)  # noqa: E731
        tm = {k: float(np.median([r["terms"][k] for r in rows])) for k in rows[0]["terms"]}
        aero = np.array([r["terms"]["aero"] for r in rows])
        X = np.column_stack([np.ones(len(rows))] + [np.array([r["draws"][k] for r in rows]) for k in ("ca_tf", "k_retro", "rho0", "wind")]
                            + [g("Vrel_over_vz"), g("vze_minus_vz")])
        coef, *_ = np.linalg.lstsq(X, aero, rcond=None)
        pred = X @ coef
        r2 = float(1.0 - np.sum((aero - pred) ** 2) / np.sum((aero - aero.mean()) ** 2))
        summ[prof] = dict(n=len(rows), ratio_kh_median=float(np.median(g("ratio_kh"))), ratio_kf_nf_median=float(np.median(g("ratio_kf_nf"))),
                          ratio_kraw_nf_median=float(np.median(g("ratio_kraw_nf"))), terms_median=tm,
                          closure_median=float(np.median(g("closure"))),
                          Az_N_median=float(np.median(g("Az_N"))), d_model_N_median=float(np.median(g("d_model_N"))),
                          F_N_median=float(np.median(g("F_N"))), vz_median=float(np.median(g("vz"))),
                          vze_minus_vz_median=float(np.median(g("vze_minus_vz"))), Vrel_over_vz_median=float(np.median(g("Vrel_over_vz"))),
                          ratio_kh_early_late_median=[float(np.median([r["ratio_kh_early_late"][j] for r in rows if r["ratio_kh_early_late"][j] is not None])) for j in (0, 1)],
                          aero_early_late_median=[float(np.median([r["aero_early_late"][j] for r in rows if r["aero_early_late"][j] is not None])) for j in (0, 1)],
                          pct_median_over_runs={k: [float(np.median([r["pct"][k][j] for r in rows])) for j in range(3)] for k in rows[0]["pct"]},
                          pct_p01_p99_over_runs={k: [float(np.percentile([r["pct"][k][0] for r in rows], 1)),
                                                     float(np.percentile([r["pct"][k][2] for r in rows], 99))] for k in rows[0]["pct"]},
                          r_z_m_median=float(np.median([r["r_z_m"] for r in rows])),
                          aero_regression=dict(columns=["const", "ca_tf", "k_retro", "rho0", "wind", "Vrel_over_vz", "vze_minus_vz"],
                                               coef=coef.tolist(), r2=r2))
        print(prof, json.dumps(summ[prof], indent=None, default=float), flush=True)
    with open(os.path.join(OUT, "khat_offset.json"), "w") as f:
        json.dump(dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE, n_runs=NR, summary=summ, runs=res_all,
                       note=("ratio = k / ((1 + m_est_err) thrust_scale (1 + a_sf)) - 1; per-run median over fc & F > 0.3 F_max & "
                             "(phase 5 or B1), then the median over runs; terms: dir = cos(delta) - 1, aero = axial non-thrust force "
                             "residual (A_z + s d_model) / F, bias = a_bz m / F, lever = IMU lever-arm term")), f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "khat_offset.json"), flush=True)


if __name__ == "__main__":
    main()
