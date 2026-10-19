"""m2_fc_thrust v1.1 (GNC, 2026-10-13): accelerometer thrust estimate for the FC_THRUST CAN frame and the over-thrust abort.

v1.1 = GNC review of v1 before its first run (v1 was staged with gnc.json v3 as NOT RUN; kept in the v3 hub tree). Changes:
 (1) A1 relight planning value 0.81 s (adopted by the lead 2026-10-13); v1 defaulted to 0.65 s.
 (2) D_model on the FSW's estimated vertical velocity (sim6 kx[2,1], recorded 'vze') and the leg term from the leg state of the
     profile (B1 hops from its legs, legs_mode 1; A1 deploys them at the relight command, phase 4): exactly the sim6 k_est_asc 2
     model. v1 used the true vz.
 (3) Two arming windows. 'air' (v1): h_est > 1 m after liftoff until touchdown, any engine state. 'fc' (GNC proposal for the
     FC_THRUST valid flag): 'air' AND engine lit (ECU RUN) AND drogue not attached (A1: drogue deployment at the estimated apogee
     to the release at relight thrust > 0.5 floor). Outside 'fc' the FC sends valid = 0 and the ECU only raises a flag.
 (4) Filter variants: raw (the 1 kHz sample at the frame instant), box10 (mean of the 10 samples of the frame), first-order
     tau 10 ms and tau 20 ms (REQ lead: raw or lightly filtered, tau <= 20 ms); 100 Hz frames at a random phase per run.
 (5) Per-run HELD MAXIMUM: the largest level the frame stream exceeds on 3 consecutive frames (20 ms span, REQ lead hold).
     An abort at threshold T happens if and only if the held maximum exceeds T, so one statistic answers every threshold.
 (6) Latency: noise-free step and ramp responses through each filter, the frame sampling and the 20 ms hold.
 (7) Stuck-pintle detection timed from the failure onset and from the true threshold crossing; thresholds swept.
 (8) 500 runs per branch (all draws of seed 101); profiles in separate processes (GNC_FCT_PROFILES); threshold sweep.

Lead decision 2026-10-13 (interfaces/CHANGELOG.md, over_thrust_abort): firmware v2.7 flies open loop on Pc loss; an
accelerometer over-thrust abort uses the CAN frame FC_THRUST (ID 0x024, >= 100 Hz, sequence, accelerometer thrust in 0.1 N
steps, valid flag, CRC-8, raw or lightly filtered, tau <= 20 ms); provisional threshold 650 N held 20 ms (500 N x 1.143 Cd band
x 1.10 estimate error, ASSUMED); a stale (> 50 ms) or invalid estimate only raises a flag. GNC publishes the estimate's 3-sigma
error and latency, the false-abort rate (Pc-lost branch) and the stuck-pintle detection time (670-876 N), and confirms or
proposes the threshold.

Estimate (FC side): F_acc = m_est f_z + D_model; f_z = measured axial specific force at the IMU; m_est = FSW mass estimate;
D_model = the k_est_asc 2 nominal axial-force model (rho 1.2; + going up nose-first with CdA_nf, - going down tail-first with
CdA_nom, + CdA_legs with the legs out) on the estimated vertical velocity.
Reconstruction on recorded 6-DOF flights (sim6/run6 v2.7.1-dev, 1 ms recorder): true thrust, true axial specific force at the
CG (fax), body rates, CG station, true mass, estimated vertical velocity; the run's own IMU draws (a_sf, a_bz) and FSW
mass-estimate error (m_est_err, ASSUMED N(0, 0.03)) from the Monte Carlo draw table; white noise with the sim's IMU class
density and the thrust-proportional vibration term (vib_sigma 2.0 m/s2 at F_max, ASSUMED) from an own generator (seed 20261019
+ run): the sim6 measurement model fm = fimu (1 + a_sf) + b_a + (a_vrw / sqrt(dt) + vib F / F_max) N(0, 1) with other noise
samples (statistically equivalent, not the same samples). The sim's own k_hat channel (tau 0.1 s) is compared as a check of the
reconstruction (same mass error and scale factor).
Branches (A1 at the v2.8 planning value with the liquid-line start delay; B1 85 m, the sizing height, more high-thrust exposure
than the 62 m cap; FSW v2.7 k_est_asc 2; pc2 bases, no throat growth):
  H  healthy, Pc loop valid (thrust_scale ~ N(1, 0.05) as drawn)
  L  Pc lost from ignition at the top of the open-loop band: thrust_scale = 1.143 on every run (lead's Cd band factor; worst
     case for false aborts; the other draws unchanged)
  S  stuck pintle: synthetic thrust ramp at 2.5 / 3.6 kN/s from 500 N (ascent) or 150 N (landing) to 670 / 876 N, through each
     H run's error terms (scale x mass error, bias, noise at that thrust), random frame phase; detection time from the failure
     onset and from the true crossing of the threshold; miss = no abort within 2 s
Env: GNC_IFACE, GNC_ACT_RATE, GNC_FCT_OUT (out/fc_thrust), GNC_FCT_N (runs per branch, 500), GNC_FCT_PLAN (A1 relight planning
value, 0.81), GNC_FCT_PARTS (fly,eval), GNC_FCT_PROFILES (A1,B1)."""
import json
import os
import sys
import time
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.signal import lfilter
from scipy.stats import norm

os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_prop_closure as PC  # noqa: E402

VERSION = "m2_fc_thrust v1.1"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_FCT_OUT", f"{S}/fc_thrust")
NR = int(os.environ.get("GNC_FCT_N", "500"))
PLAN = float(os.environ.get("GNC_FCT_PLAN", "0.81"))
PARTS = os.environ.get("GNC_FCT_PARTS", "fly,eval").split(",")
PROFILES = os.environ.get("GNC_FCT_PROFILES", "A1,B1").split(",")
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
DT = 1.0e-3
FRAME = 0.010            # REQ lead: >= 100 Hz
KF = int(round(FRAME / DT))
HOLD = 0.020             # REQ lead: held 20 ms
NH = int(round(HOLD / FRAME))   # 2: the condition on NH + 1 = 3 consecutive frames spans 20 ms
VARS = (("raw", 0.0), ("box10ms", -1.0), ("tau10ms", 0.010), ("tau20ms", 0.020))
THR = (600.0, 620.0, 635.0, 650.0, 675.0)
TGRID = np.arange(560.0, 721.0, 5.0)
CD_TOP = 1.143           # REQ lead (Cd band factor of the provisional threshold), ASSUMED there
STUCK = dict(F_final_N=(670.0, 876.0), rate_N_s=(2500.0, 3600.0), F0_N=(500.0, 150.0))   # REQ lead relay (stuck-pintle case)
BANDS = ((75.0, 300.0), (300.0, 450.0), (450.0, 1.0e9))
GUARD = 0.100            # error statistics skip the first 0.1 s after the fc window opens (filter settling after the pad, the
                         # MECO / relight gaps and the drogue release; the held maximum keeps every fc frame)


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


def filt(x, tau):
    """filter variant: tau > 0 first order, 0 raw, < 0 mean of the last KF samples (the frame)."""
    if tau < 0.0:
        c = np.cumsum(np.concatenate([[0.0], x]))
        y = np.empty_like(x)
        y[KF - 1:] = (c[KF:] - c[:-KF]) / KF
        y[:KF - 1] = c[1:KF] / np.arange(1, KF)
        return y
    return lp(x, tau)


def held_series(fa):
    """minimum over NH + 1 consecutive frames ending at frame k (NaN for k < NH)."""
    out = np.full(len(fa), -np.inf)
    if len(fa) > NH:
        out[NH:] = sliding_window_view(fa, NH + 1).min(axis=1)
    return out


def held_max(fa, am):
    """largest level exceeded on NH + 1 consecutive armed frames, and the frame index where that hold completes."""
    if len(fa) <= NH:
        return -np.inf, -1
    W = sliding_window_view(fa, NH + 1).min(axis=1)
    A = sliding_window_view(am, NH + 1).all(axis=1)
    if not A.any():
        return -np.inf, -1
    Wm = np.where(A, W, -np.inf)
    j = int(np.argmax(Wm))
    return float(Wm[j]), j + NH


def fly_one(cfg, dr, tsc=None):
    d = dict(dr)
    if tsc is not None:
        d["thrust_scale"] = float(tsc)
    c, disp = R.run_cfg(cfg, d)
    c = dict(c, rec_dt=DT)
    par = R.build(c, disp)[0]
    res, rec, _ = R.fly(c, disp, nrec=100000)
    return par, res, rec


def legs_state(par, rec, prof):
    n = len(rec)
    if par[PN["legs_mode"]] > 0.5:
        return np.ones(n, bool)
    return rec[:, I["phase"]] >= 4 if prof == "A1" else np.zeros(n, bool)


def reconstruct(par, rec, rng, prof):
    F = rec[:, I["F"]]
    Fmax = par[PN["Fmax"]]
    rz = par[PN["z_imu"]] - rec[:, I["zcg"]]
    fimu = rec[:, I["fax"]] - (rec[:, I["wx"]] ** 2 + rec[:, I["wy"]] ** 2) * rz
    vib = np.where(F > 1.0, par[PN["vib_sigma"]] * F / Fmax, 0.0)
    fm = fimu * (1.0 + par[PN["a_sf"]]) + par[PN["a_bz"]] + (par[PN["a_vrw"]] / np.sqrt(DT) + vib) * rng.standard_normal(len(F))
    m_est = rec[:, I["m"]] * (1.0 + par[PN["mest"]])
    vze = rec[:, I["vze"]]
    cda = np.where(vze > 0.0, par[PN["kest_cda_nf"]], par[PN["drag_cda_nom"]]) + np.where(legs_state(par, rec, prof),
                                                                                          par[PN["kest_cda_legs"]], 0.0)
    dd = 0.5 * 1.2 * cda * vze * vze
    return fm * m_est + np.where(vze > 0.0, dd, -dd)


def windows(par, res, rec, prof):
    t = rec[:, I["t"]]
    F = rec[:, I["F"]]
    hest = rec[:, I["hest"]]
    td = float(res["td_t"]) if res["td_t"] > 0 else t[-1]
    up = np.where(hest > 1.0)[0]
    air = np.zeros(len(t), bool)
    if len(up):
        air[up[0]:] = True
    air &= (t < td) & (hest > 1.0)
    lit = rec[:, I["Fcmd"]] > 0.0          # sim6 records Fcmd only while lit
    drog = np.zeros(len(t), bool)
    t_rel = float(res["t_relight"])
    if prof == "A1":
        i3 = np.where(rec[:, I["phase"]] >= 3)[0]
        if len(i3):
            thr = 0.5 * par[PN["floor"]] * par[PN["Fmax"]] * par[PN["thrust_scale"]]
            r_ = np.where((t >= t_rel) & (F > thr))[0] if t_rel > 0.0 else np.array([], int)
            drog[i3[0]:(r_[0] if len(r_) else len(t))] = True
    return air, air & lit & ~drog, lit, drog


def open_time(mask):
    """time [s] since the mask last became true (0 where false)."""
    n = len(mask)
    idx = np.arange(n)
    rise = mask & ~np.concatenate([[False], mask[:-1]])
    start = np.maximum.accumulate(np.where(rise, idx, 0))
    return np.where(mask, (idx - start) * DT, 0.0)


def evaluate_run(par, res, rec, Fr, prof, rng):
    t = rec[:, I["t"]]
    F = rec[:, I["F"]]
    Fmax = par[PN["Fmax"]]
    ph = rec[:, I["phase"]]
    air, fc, lit, drog = windows(par, res, rec, prof)
    p0 = int(rng.integers(0, KF))
    out = dict(frame_phase=p0)
    tf = t[p0::KF]
    Ff = F[p0::KF]
    aw, fw = air[p0::KF], fc[p0::KF]
    fs = (fc & (open_time(fc) >= GUARD))[p0::KF]
    for name, tau in VARS:
        fa = np.round(filt(Fr, tau)[p0::KF] * 10.0) / 10.0      # 0.1 N steps
        ft = filt(F, tau)[p0::KF]
        burn = fs & (ft > 0.15 * Fmax)
        tr_ = fw & ~fs & (ft > 0.15 * Fmax)
        e = fa[burn] / ft[burn] - 1.0
        eN = fa[burn] - ft[burn]
        bands = {}
        for lo, hi in BANDS:
            m_ = (ft[burn] >= lo) & (ft[burn] < hi)
            bands[f"{lo:g}-{hi:g}"] = dict(n=int(m_.sum()), mean=float(e[m_].mean()) if m_.any() else None,
                                           sd=float(e[m_].std()) if m_.any() else None)
        hm_a, ka = held_max(fa, aw)
        hm_f, kf_ = held_max(fa, fw)
        out[name] = dict(err=e.astype(np.float32), errN=eN.astype(np.float32), ftrue=ft[burn].astype(np.float32),
                         err_mean=float(e.mean()) if len(e) else None, err_sd=float(e.std()) if len(e) else None,
                         err_hi_mean=bands["450-1e+09"]["mean"], bands=bands,
                         held_max_air_N=hm_a, held_max_air_t=float(tf[ka]) if ka >= 0 else None,
                         held_max_air_Ftrue_N=float(Ff[ka]) if ka >= 0 else None,
                         held_max_air_phase=int(ph[p0::KF][ka]) if ka >= 0 else None,
                         held_max_air_lit=bool(lit[p0::KF][ka]) if ka >= 0 else None,
                         held_max_fc_N=hm_f, held_max_fc_t=float(tf[kf_]) if kf_ >= 0 else None,
                         held_max_fc_Ftrue_N=float(Ff[kf_]) if kf_ >= 0 else None,
                         Ftrue_max_fc_N=float(Ff[fw].max()) if fw.any() else None,
                         guard_overread_max_N=float((fa[tr_] - ft[tr_]).max()) if tr_.any() else None,
                         guard_Facc_max_N=float(fa[tr_].max()) if tr_.any() else None,
                         Facc_max_fc_N=float(fa[fw].max()) if fw.any() else None,
                         Facc_min_air_coast_N=float(fa[aw & ~lit[p0::KF]].min()) if (aw & ~lit[p0::KF]).any() else None,
                         Facc_max_air_coast_N=float(fa[aw & ~lit[p0::KF]].max()) if (aw & ~lit[p0::KF]).any() else None)
    kh = rec[:, I["keff"]]
    sel = fc & (F > 0.3 * Fmax) & ((ph == 5) | (prof == "B1"))
    exp_k = (1.0 + par[PN["mest"]]) * par[PN["thrust_scale"]] * (1.0 + par[PN["a_sf"]])
    out["k_hat_check"] = dict(k_hat_median=float(np.median(kh[sel])) if sel.any() else None, expected=float(exp_k))
    out["bias_terms"] = dict(m_est_err=float(par[PN["mest"]]), a_sf=float(par[PN["a_sf"]]), a_bz=float(par[PN["a_bz"]]),
                             thrust_scale=float(par[PN["thrust_scale"]]))
    out["window_s"] = dict(air=float(air.sum() * DT), fc=float(fc.sum() * DT), lit_air=float((air & lit).sum() * DT),
                           drogue_and_lit=float((drog & lit).sum() * DT), fc_above_400N=float((fc & (F > 400.0)).sum() * DT))
    out["ok"] = bool(R.success(res))
    out["Fmax"] = float(Fmax)
    return out


def part_fly(prof):
    os.makedirs(OUT, exist_ok=True)
    C, has_tq = cfgs()
    cfg = C[prof]
    store = {}
    D = R.draw(np.random.default_rng(101), 500, cfg)
    for br, tsc in (("H", None), ("L", CD_TOP)):
        t0 = time.time()
        rows = []
        for i in range(NR):
            par, res, rec = fly_one(cfg, D[i], tsc)
            rng = np.random.default_rng(20261019 + i + (0 if br == "H" else 100000) + (0 if prof == "A1" else 200000))
            Fr = reconstruct(par, rec, rng, prof)
            ev = evaluate_run(par, res, rec, Fr, prof, rng)
            ev["run"] = i
            ev["a_vrw"] = float(par[PN["a_vrw"]])
            ev["vib_sigma"] = float(par[PN["vib_sigma"]])
            F = rec[:, I["F"]]
            ev["m_mean_burn_kg"] = float(np.mean(rec[F > 0.3 * par[PN["Fmax"]], I["m"]])) if (F > 0.3 * par[PN["Fmax"]]).any() else float(rec[0, I["m"]])
            rows.append(ev)
            if (i + 1) % 100 == 0:
                print(f"  {prof} {br}: {i + 1} runs ({time.time() - t0:.0f} s)", flush=True)
        store[f"{prof}|{br}"] = rows
        print(f"{prof} {br}: {NR} runs in {time.time() - t0:.0f} s; P {np.mean([r['ok'] for r in rows]):.3f}", flush=True)
    np.save(os.path.join(OUT, f"fc_thrust_runs_{prof}.npy"), np.array([store], dtype=object), allow_pickle=True)
    with open(os.path.join(OUT, f"fc_thrust_meta_{prof}.json"), "w") as f:
        json.dump(dict(version=VERSION, sim=s6.SIM6_VERSION, n_runs=NR, a1_plan=PLAN, a1_liquid_start_delay_table=has_tq), f)


def latency_table():
    """noise-free responses: step 0 -> 1 at t = 1 s (delay to 50 % / 90 % at the frame stream, mean over the 10 frame phases and
    max), ramp lag (steady state), and the abort decision delay for a step from 0 to 2 T (frame wait + filter + 20 ms hold)."""
    n = 3000
    tt = np.arange(n) * DT
    out = {}
    for name, tau in VARS:
        d50, d90, dab = [], [], []
        for p0 in range(KF):
            x = np.where(tt >= 1.0 - 1e-12, 1.0, 0.0)
            y = filt(x, tau)[p0::KF]
            tf = tt[p0::KF]
            d50.append(float(tf[np.where(y >= 0.5)[0][0]] - 1.0))
            d90.append(float(tf[np.where(y >= 0.9)[0][0]] - 1.0))
            hs = held_series(y)
            dab.append(float(tf[np.where(hs > 0.5)[0][0]] - 1.0))
        xr = np.maximum(tt - 1.0, 0.0)
        yr = filt(xr, tau)
        lag = float(np.mean((xr - yr)[2000:2500]))
        out[name] = dict(step_delay_50pct_mean_max_s=[float(np.mean(d50)), float(np.max(d50))],
                         step_delay_90pct_mean_max_s=[float(np.mean(d90)), float(np.max(d90))],
                         ramp_lag_s=lag, frame_staleness_s=[0.0, FRAME - DT],
                         abort_decision_delay_step_to_2T_mean_max_s=[float(np.mean(dab)), float(np.max(dab))])
    return out


def stuck_series(bf, a_bz_N, mm, a_vrw, vib, Fmax, F0, Ff, rate, tau, rng):
    n = int(2.5 / DT)
    tt = np.arange(n) * DT - 0.5
    Ft = np.where(tt < 0.0, F0, np.minimum(F0 + rate * np.maximum(tt, 0.0), Ff))
    x = bf * Ft + a_bz_N + mm * (a_vrw / np.sqrt(DT) + vib * Ft / Fmax) * rng.standard_normal(n)
    p0 = int(rng.integers(0, KF))
    fy = np.round(filt(x, tau)[p0::KF] * 10.0) / 10.0
    return tt[p0::KF], held_series(fy)


def detect(tf, hs, T, F0, rate):
    """(t_detect from the onset or None, alarm before the onset, t from the true crossing of T)."""
    over = hs > T
    pre = over & (tf < 0.0)
    if pre.any():
        return None, True, None
    k = np.where(over)[0]
    if not len(k):
        return None, False, None
    td_ = float(tf[k[0]])
    tc = (T - F0) / rate if T > F0 else 0.0
    return td_, False, td_ - tc


def part_eval():
    store, meta = {}, {}
    for prof in PROFILES:
        store.update(np.load(os.path.join(OUT, f"fc_thrust_runs_{prof}.npy"), allow_pickle=True)[0])
        meta[prof] = json.load(open(os.path.join(OUT, f"fc_thrust_meta_{prof}.json")))
    m0 = meta[PROFILES[0]]
    out = dict(version=VERSION, date="2026-10-13", sim=m0["sim"], runs_per_branch=m0["n_runs"], a1_planning_value_s=m0["a1_plan"],
               a1_liquid_start_delay_table=m0["a1_liquid_start_delay_table"], b1_height_m=85.0,
               estimate="F_acc = m_est f_z + D_model (sim6 k_est_asc 2 model on the estimated vz), 0.1 N steps, 100 Hz frames",
               variants={k: ("1 kHz sample at the frame instant" if v == 0 else "mean of the 10 samples of the frame" if v < 0
                             else f"first-order low-pass tau {1e3 * v:g} ms at 1 kHz") for k, v in VARS},
               windows=dict(air="h_est > 1 m after liftoff until touchdown, any engine state (v1)",
                            fc="air AND engine lit (ECU RUN) AND drogue not attached (GNC proposal for the FC_THRUST valid flag)",
                            error_statistics=f"fc frames with true thrust > 0.15 F_max, after the first {GUARD:g} s of each fc "
                                             "window segment (filter settling); held maxima and false aborts use every fc frame"),
               hold=dict(s=HOLD, frames=NH + 1, rule="abort if F_acc > T on 3 consecutive frames (20 ms span)"),
               thresholds_N=list(THR), cd_top=CD_TOP, stuck_case=STUCK, branches={})
    pooled = {v: [] for v, _ in VARS}
    pooledN = {v: [] for v, _ in VARS}
    pooledF = {v: [] for v, _ in VARS}
    for key, rows in store.items():
        prof, br = key.split("|")
        b = dict(P=float(np.mean([r["ok"] for r in rows])), n=len(rows))
        for v, _ in VARS:
            e = np.concatenate([r[v]["err"] for r in rows if len(r[v]["err"])]).astype(float)
            eN = np.concatenate([r[v]["errN"] for r in rows if len(r[v]["errN"])]).astype(float)
            fT = np.concatenate([r[v]["ftrue"] for r in rows if len(r[v]["ftrue"])]).astype(float)
            bias = np.array([r[v]["err_mean"] for r in rows if r[v]["err_mean"] is not None])
            sd = np.array([r[v]["err_sd"] for r in rows if r[v]["err_sd"] is not None])
            hm_f = np.array([r[v]["held_max_fc_N"] for r in rows])
            hm_a = np.array([r[v]["held_max_air_N"] for r in rows])
            ftm = np.array([r[v]["Ftrue_max_fc_N"] for r in rows if r[v]["Ftrue_max_fc_N"] is not None])
            hi = fT >= 450.0
            fa_ = {}
            for T in THR:
                for wn, hm in (("fc", hm_f), ("air", hm_a)):
                    k = int(np.sum(hm > T))
                    fa_[f"{wn}|{T:g}"] = dict(n=k, of=len(hm), upper95=float(1.0 - 0.05 ** (1.0 / len(hm))) if k == 0 else None)
            b[v] = dict(err_p0135_p50_p99865=[float(np.percentile(e, 0.135)), float(np.median(e)), float(np.percentile(e, 99.865))],
                        err_3sigma=float(max(-np.percentile(e, 0.135), np.percentile(e, 99.865))),
                        err_3sigma_F_ge_450N=float(max(-np.percentile(e[hi], 0.135), np.percentile(e[hi], 99.865))) if hi.sum() > 100 else None,
                        errN_p0135_p99865_F_ge_450N=[float(np.percentile(eN[hi], 0.135)), float(np.percentile(eN[hi], 99.865))] if hi.sum() > 100 else None,
                        per_run_bias_sd=float(bias.std()), per_run_bias_min_max=[float(bias.min()), float(bias.max())],
                        within_run_sd_median_max=[float(np.median(sd)), float(sd.max())],
                        held_max_fc_p50_p99_max_N=[float(np.median(hm_f)), float(np.percentile(hm_f, 99)), float(hm_f.max())],
                        held_max_air_p50_p99_max_N=[float(np.median(hm_a)), float(np.percentile(hm_a, 99)), float(hm_a.max())],
                        held_max_fc_mean_sd_N=[float(hm_f.mean()), float(hm_f.std())],
                        Ftrue_max_fc_p50_max_N=[float(np.median(ftm)), float(ftm.max())],
                        guard_window_overread_max_N=float(max([r[v]["guard_overread_max_N"] for r in rows if r[v]["guard_overread_max_N"] is not None], default=float("nan"))),
                        guard_window_Facc_max_N=float(max([r[v]["guard_Facc_max_N"] for r in rows if r[v]["guard_Facc_max_N"] is not None], default=float("nan"))),
                        false_aborts=fa_, n_frames=int(len(e)), n_frames_F_ge_450N=int(hi.sum()))
            if br == "H":
                pooled[v].append(e)
                pooledN[v].append(eN)
                pooledF[v].append(fT)
        # where the 'air' held maximum sits (coasts / drogue / burn) for tau 20 ms
        b["air_held_max_location_tau20ms"] = dict(
            lit=int(sum(1 for r in rows if r["tau20ms"]["held_max_air_lit"])), not_lit=int(sum(1 for r in rows if r["tau20ms"]["held_max_air_lit"] is False)),
            coast_Facc_min_max_N=[float(min(r["tau20ms"]["Facc_min_air_coast_N"] for r in rows if r["tau20ms"]["Facc_min_air_coast_N"] is not None)) if any(r["tau20ms"]["Facc_min_air_coast_N"] is not None for r in rows) else None,
                                  float(max(r["tau20ms"]["Facc_max_air_coast_N"] for r in rows if r["tau20ms"]["Facc_max_air_coast_N"] is not None)) if any(r["tau20ms"]["Facc_max_air_coast_N"] is not None for r in rows) else None])
        kh = [(r["k_hat_check"]["k_hat_median"], r["k_hat_check"]["expected"]) for r in rows if r["k_hat_check"]["k_hat_median"]]
        rat = [a / x for a, x in kh]
        b["k_hat_check_sim"] = dict(n=len(kh), median_ratio=float(np.median(rat)) if kh else None,
                                    ratio_p01_p99=[float(np.percentile(rat, 1)), float(np.percentile(rat, 99))] if kh else None,
                                    note="sim6 k_hat (tau 0.1 s) / ((1 + m_est_err) thrust_scale (1 + a_sf)): ~1 confirms the error model")
        b["windows_s_p50"] = {k: float(np.median([r["window_s"][k] for r in rows])) for k in rows[0]["window_s"]}
        b["bias_sd_terms"] = dict(m_est_err_sd=float(np.std([r["bias_terms"]["m_est_err"] for r in rows])),
                                  a_sf_sd=float(np.std([r["bias_terms"]["a_sf"] for r in rows])))
        out["branches"][key] = b
        x = b["tau20ms"]
        print(f"{key}: P {b['P']:.3f} | tau20 3sigma {100 * x['err_3sigma']:.2f} % (F>=450 N {100 * (x['err_3sigma_F_ge_450N'] or 0):.2f} %) "
              f"| bias sd {100 * x['per_run_bias_sd']:.2f} % | held max fc p50/p99/max {x['held_max_fc_p50_p99_max_N']} | F true max "
              f"{x['Ftrue_max_fc_p50_max_N']} | false fc@650 {x['false_aborts']['fc|650']['n']} air@650 {x['false_aborts']['air|650']['n']}",
              flush=True)
    # pooled healthy error (A1 + B1 H, fc window, burning frames)
    eb = {}
    for v, _ in VARS:
        e = np.concatenate(pooled[v])
        eN = np.concatenate(pooledN[v])
        fT = np.concatenate(pooledF[v])
        hi = fT >= 450.0
        eb[v] = dict(p0135=float(np.percentile(e, 0.135)), p99865=float(np.percentile(e, 99.865)), mean=float(e.mean()), sd=float(e.std()),
                     three_sigma=float(max(-np.percentile(e, 0.135), np.percentile(e, 99.865))),
                     three_sigma_F_ge_450N=float(max(-np.percentile(e[hi], 0.135), np.percentile(e[hi], 99.865))),
                     mean_sd_F_ge_450N=[float(e[hi].mean()), float(e[hi].std())],
                     errN_p0135_p99865_F_ge_450N=[float(np.percentile(eN[hi], 0.135)), float(np.percentile(eN[hi], 99.865))],
                     n_frames=int(len(e)), n_frames_F_ge_450N=int(hi.sum()))
    out["error_3sigma_healthy_pooled"] = eb
    # decomposition: FSW mass-estimate error (constant per run) vs the rest
    sens, dec = {}, {}
    for v, _ in VARS:
        rest, rest_hi = [], []
        for key in [k for k in store if k.endswith("|H")]:
            for r in store[key]:
                x = r[v]["err"].astype(float)
                if len(x):
                    rr_ = (1.0 + x) / (1.0 + r["bias_terms"]["m_est_err"]) - 1.0
                    rest.append(rr_)
                    rest_hi.append(rr_[r[v]["ftrue"] >= 450.0])
        er = np.concatenate(rest)
        erh = np.concatenate(rest_hi)
        dec[v] = dict(rest_mean=float(er.mean()), rest_sd=float(er.std()),
                      rest_p0135_p99865=[float(np.percentile(er, 0.135)), float(np.percentile(er, 99.865))],
                      rest_mean_sd_F_ge_450N=[float(erh.mean()), float(erh.std())],
                      rest_p0135_p99865_F_ge_450N=[float(np.percentile(erh, 0.135)), float(np.percentile(erh, 99.865))])
        if v == "tau20ms":
            for sm in (0.005, 0.01, 0.015, 0.02, 0.03):
                s_ = float(np.sqrt(sm * sm + erh.std() ** 2))
                mu = float(erh.mean())
                sens[f"{sm:g}"] = dict(sd_total_F_ge_450N=s_, three_sigma=3.0 * s_,
                                       window_N=[float(500.0 * CD_TOP * (1 + mu + 3 * s_)), float(670.0 * (1 + mu - 3 * s_))],
                                       window_exists_3sigma=bool(500.0 * CD_TOP * (1 + mu + 3 * s_) < 670.0 * (1 + mu - 3 * s_)),
                                       p_miss_670N_at={f"{T:g}": float(norm.cdf((T / 670.0 - 1.0 - mu) / s_)) for T in THR},
                                       p_over_T_at_571p5N={f"{T:g}": float(norm.sf((T / (500.0 * CD_TOP) - 1.0 - mu) / s_)) for T in THR})
    out["error_decomposition"] = dict(by_variant=dec, mass_estimate_error_sd_assumed=0.03,
                                      sensitivity_to_mass_estimate_sd_tau20ms=sens,
                                      note="rest = (1 + e) / (1 + m_est_err) - 1: scale factor, bias, vibration and white noise after "
                                           "the filter, drag-model error, gimbal cosine, rotation terms. Steady-state Gaussian "
                                           "per frame; the per-flight bias is the mass error plus the scale factor")
    # threshold sweep on the held maxima (fc window): empirical and Gaussian (normal fit of the per-run held maximum)
    sweep = {}
    for key, rows in store.items():
        for v, _ in VARS:
            hm = np.array([r[v]["held_max_fc_N"] for r in rows])
            mu, sd = float(hm.mean()), float(hm.std())
            sweep[f"{key}|{v}"] = dict(held_max_mean_sd_N=[mu, sd],
                                       emp={f"{T:g}": int(np.sum(hm > T)) for T in TGRID},
                                       gauss={f"{T:g}": float(norm.sf((T - mu) / sd)) for T in TGRID})
    out["threshold_sweep_fc"] = dict(n_runs_per_branch=len(next(iter(store.values()))), by_case=sweep,
                                     note="false abort at T <=> per-run held maximum (fc window) > T; 'gauss' = normal fit of "
                                          "the per-run held maxima (extrapolation, model-dependent in the tail)")
    # stuck-pintle detection through each healthy run's error terms (A1 and B1 H rows)
    rng = np.random.default_rng(20261020)
    det = {}
    Hrows = [r for k in store if k.endswith("|H") for r in store[k]]
    acc = {}
    for v, tau in VARS:
        for F0 in STUCK["F0_N"]:
            for Ff in STUCK["F_final_N"]:
                for rate in STUCK["rate_N_s"]:
                    res_T = {T: dict(ts=[], tc=[], miss=0, early=0) for T in TGRID}
                    for r in Hrows:
                        bt = r["bias_terms"]
                        bf = (1.0 + bt["m_est_err"]) * (1.0 + bt["a_sf"])
                        mm = r["m_mean_burn_kg"] * (1.0 + bt["m_est_err"])
                        tf, hs = stuck_series(bf, mm * bt["a_bz"], mm, r["a_vrw"], r["vib_sigma"], r["Fmax"], F0, Ff, rate, tau, rng)
                        for T in TGRID:
                            td_, early, tc = detect(tf, hs, T, F0, rate)
                            d = res_T[T]
                            if early:
                                d["early"] += 1
                            elif td_ is None:
                                d["miss"] += 1
                            else:
                                d["ts"].append(td_)
                                d["tc"].append(tc)
                    for T in TGRID:
                        d = res_T[T]
                        key = f"{v}|T{T:g}|F0 {F0:g}|Ff {Ff:g}|rate {rate:g}"
                        det[key] = dict(n=len(Hrows), miss=d["miss"], alarm_before_failure=d["early"],
                                        t_detect_from_onset_p50_p99_max_s=[float(np.median(d["ts"])), float(np.percentile(d["ts"], 99)),
                                                                           float(max(d["ts"]))] if d["ts"] else None,
                                        t_detect_from_true_crossing_p50_p99_max_s=[float(np.median(d["tc"])), float(np.percentile(d["tc"], 99)),
                                                                                   float(max(d["tc"]))] if d["tc"] and Ff > T else None)
                        acc[(v, T, F0, Ff, rate)] = det[key]
    out["stuck_pintle_detection"] = dict(by_case={k: v for k, v in det.items() if float(k.split("|T")[1].split("|")[0]) in THR},
                                         note="synthetic ramp through each healthy run's bias factor (1 + m_est_err)(1 + a_sf), "
                                              "accelerometer bias and noise at that thrust; random frame phase; detection = held "
                                              "20 ms above T; miss = no detection within 2 s; alarm_before_failure = above T at F0")
    # summary table per threshold (tau 20 ms and box 10 ms): L-branch false aborts (fc) and stuck misses / times
    summ = {}
    for v in ("tau20ms", "box10ms", "tau10ms", "raw"):
        for T in TGRID:
            row = {}
            for prof in PROFILES:
                c = sweep.get(f"{prof}|L|{v}")
                if c:
                    row[f"false_L_{prof}"] = c["emp"][f"{T:g}"]
                    row[f"false_L_{prof}_gauss"] = c["gauss"][f"{T:g}"]
                c = sweep.get(f"{prof}|H|{v}")
                if c:
                    row[f"false_H_{prof}"] = c["emp"][f"{T:g}"]
            for Ff in STUCK["F_final_N"]:
                ms = [acc[(v, T, F0, Ff, rate)] for F0 in STUCK["F0_N"] for rate in STUCK["rate_N_s"]]
                row[f"miss_{Ff:g}"] = int(sum(m["miss"] for m in ms))
                row[f"early_{Ff:g}"] = int(sum(m["alarm_before_failure"] for m in ms))
                row[f"n_{Ff:g}"] = int(sum(m["n"] for m in ms))
                tt_ = [m["t_detect_from_onset_p50_p99_max_s"][1] for m in ms if m["t_detect_from_onset_p50_p99_max_s"]]
                row[f"t99_onset_{Ff:g}_s"] = float(max(tt_)) if tt_ else None
            summ[f"{v}|{T:g}"] = row
    out["threshold_summary"] = summ
    out["latency"] = latency_table()
    out["latency_note"] = ("estimate latency at the FC output = filter delay (step 50 % / 90 %, ramp lag) + frame staleness 0-9 ms "
                           "(the ECU holds the last frame); NOT included: IMU internal digital filter and sample delay (part not "
                           "chosen: DATASHEET needed), FC task scheduling, CAN transport and ECU scheduling (Electronics), "
                           "airframe axial dynamics between the engine and the IMU (rigid body in sim6)")
    # Gaussian extrapolation on the pooled healthy error at high thrust (tau 20 ms): per-flight probabilities at steady thrust
    mu, sd = eb["tau20ms"]["mean_sd_F_ge_450N"]
    out["gaussian_extrapolation_tau20ms"] = dict(
        model="relative error at F >= 450 N ~ N(mean, sd) of the pooled healthy frames (bias + noise per frame; the held 20 ms "
              "rule removes most of the noise, so this overstates the noise part); steady thrust at the named level",
        mean=mu, sd=sd, by_threshold_N={f"{T:g}": dict(p_above_at_571p5N=float(norm.sf((T / (500.0 * CD_TOP) - 1.0 - mu) / sd)),
                                                       p_below_at_670N=float(norm.cdf((T / 670.0 - 1.0 - mu) / sd)),
                                                       p_below_at_876N=float(norm.cdf((T / 876.0 - 1.0 - mu) / sd))) for T in THR})
    lo, hi_ = 500.0 * CD_TOP, 670.0
    out["threshold_window"] = dict(healthy_max_N=lo, stuck_min_N=hi_, max_relative_3sigma_error_for_a_window=float((hi_ - lo) / (hi_ + lo)),
                                   geometric_mean_N=float(np.sqrt(lo * hi_)),
                                   window_at_measured_3sigma_tau20ms_F_ge_450N=[float(lo * (1 + eb["tau20ms"]["three_sigma_F_ge_450N"])),
                                                                                float(hi_ * (1 - eb["tau20ms"]["three_sigma_F_ge_450N"]))])
    with open(os.path.join(OUT, "fc_thrust.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for v in ("tau20ms", "box10ms"):
        for T in THR:
            print(v, T, summ[f"{v}|{T:g}"], flush=True)
    print("latency", json.dumps(out["latency"], indent=0)[:1500], flush=True)
    print("wrote", os.path.join(OUT, "fc_thrust.json"))


if __name__ == "__main__":
    if "fly" in PARTS:
        for p in PROFILES:
            part_fly(p)
    if "eval" in PARTS:
        part_eval()
