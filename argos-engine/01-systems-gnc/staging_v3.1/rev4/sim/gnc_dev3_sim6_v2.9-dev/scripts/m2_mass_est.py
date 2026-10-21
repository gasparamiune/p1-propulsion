"""m2_mass_est v1 (GNC, 2026-10-13): flight-computer MASS ESTIMATOR specification check and error budget.

Lead decision 2026-10-13 (interfaces/CHANGELOG.md, FC_THRUST): NEW REQUIREMENT (provisional) flight-computer mass-estimate error
<= 1 % (1 sigma) throughout the burn; GNC specifies the mass estimator; founder action: weigh the loaded vehicle at ARM (scale
range / resolution TO-DEFINE). Lead request: spec and error budget covering pad weighing, flow integration, accelerometer
cross-check and drift through the burn.

Candidate estimators (flight-software side; all start from the ARM weighing m_ARM):
  FM0  flow integration on the ECU chamber pressure: m_hat = m_ARM - sum(starts) - int mdot_map(Pc_meas) dt, mdot_map =
       Combustion's throttle map (the sim6 map: flow at the Pc-implied thrust F_pc), no throat-growth model
  FM1  FM0 with a throat-growth model: mdot_map x (1 + g_hat(t)), g_hat = 0.09 x min(1, J / J_ref) (the middle of the ENG-06
       rev 2 band 0.07-0.11 and the sim6 growth law J = int (F_pc / F_max)^0.68 dt; the FSW computes J from its own Pc)
  RE   rocket equation on the accelerometer while airborne, lit and free of the drogue (the FC_THRUST valid window):
       dm_hat/dt = -(m_hat f_meas + D_model) / c_map(Pc); FM0 elsewhere (pad, drogue attached, after touchdown)
Error sources (per flight unless noted; tags in SOURCES):
  weighing at ARM (absolute, N(0, sigma_w)); start transients (N2O admitted before the Pc rise: truth U(0, 8.7 g) per start, the
  FSW subtracts 4.35 g; Combustion's 8.7 g bound before the 0.35 s ignition check); Pc transducer residual after the pre-start
  auto-zero (constant additive dP, N(0, sigma_P)); flow-map truth (c* x throat area): in the flight set itself (see PRIORS);
  thrust-per-Pc (Cf) truth for RE: in the flight set; accelerometer scale factor and bias (IMU class of the configuration);
  drag-model error for RE: in the flight set (the k_est_asc 2 nominal model against the dispersed aerodynamics).
PRIORS (two flight sets per profile, 500 runs each, all other draws = the seed-101 MC draws):
  brief  the GNC Monte Carlo draws: thrust_scale N(1, 0.05), isp_scale N(1, 0.05) (brief C.7, ASSUMED)
  comb   Combustion's bands: isp_scale = eta_c* / 0.92 with eta_c* U(0.85, 0.96); thrust_scale = eta_cf / 0.975 with eta_cf
         U(0.95, 0.975) (combustion.json v2.3 and rc09_etacf_band_v2p4.json, ASSUMED uniform; own generator seed 20261021)
FSW calibration cases (what-if on the FSW side only; the truth is the flight):
  uncal  the FSW uses the nominal map (no static-fire calibration)
  cal    the FSW map is scaled by the flight's true flow factor x (1 + N(0, sigma_cal_flow)) and, for RE, the true Cf factor x
         (1 + N(0, sigma_cal_cf)): the residual after static-fire calibration (sigma values are REQUIREMENTS to test, not data)
Profiles: A1pc (gnc.json v3 A1 baseline, plan 0.81 s, liquid-line start table, k_est_asc 2, throat growth band 0.07-0.11 with
the Pc loop), A1none (same without growth), B1pc (85 m hop, k_est_asc 2, growth band with the Pc loop).
Outputs: e = m_hat / m - 1 per run and error draw (K draws per run): at the end of each burn, maximum |e| over the lit time and
over the FC_THRUST valid window, RMS profile against time from the first ignition; per-source one-at-a-time contributions;
consistency check of the recorded flows against the 6-DOF mass; requirement allocation.
Parts (GNC_MEST_PARTS): fly (records and per-run reductions -> npz), eval (statistics -> mass_est.json); GNC_MEST_PROFILES,
GNC_MEST_PRIORS, GNC_MEST_N (runs, 500), GNC_MEST_K (error draws per run, 64), GNC_MEST_OUT (out/mass_est)."""
import json
import os
import sys
import time
import numpy as np

os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_relight_v28 as V  # noqa: E402
import m2_throat_mc as TG  # noqa: E402
import m2_fc_thrust as FT  # noqa: E402

VERSION = "m2_mass_est v1"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_MEST_OUT", f"{S}/mass_est")
PARTS = os.environ.get("GNC_MEST_PARTS", "fly,eval").split(",")
PROFILES = os.environ.get("GNC_MEST_PROFILES", "A1pc,A1none,B1pc").split(",")
PRIORS = os.environ.get("GNC_MEST_PRIORS", "brief,comb").split(",")
NR = int(os.environ.get("GNC_MEST_N", "500"))
K = int(os.environ.get("GNC_MEST_K", "64"))
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
DT_REC = 0.005   # record step [s] (the 6-DOF integrates at 1 ms)
G0 = 9.80665
# ------------------------------------------------------------------ sources (values and tags)
ETA_CS = (0.85, 0.96, 0.92)      # combustion.json v2.3 unknowns: eta_c* assumed 0.92, band 0.85-0.96 (ASSUMED)
ETA_CF = (0.95, 0.975, 0.975)    # rc09_etacf_band_v2p4.json: band 0.95-0.975, design 0.975 (ASSUMED from CFD)
START_MAX_KG = 0.0087            # combustion.json v2.3: N2O admitted to an unlit chamber before the 0.35 s ignition check 8.7 g (SIM)
G_HAT_END = 0.09                 # middle of REQ ENG-06 rev 2 growth band 0.07-0.11 (TG.BAND)
PC_FS = 3.447e6                  # electronics.json v1: TE M3234 0-500 psig = 0-34.47 bar (DATASHEET)
SIG_P = dict(teb3=0.015 * PC_FS / 3.0, bfsl=0.0025 * PC_FS, cal=0.001 * PC_FS)
# teb3: TEB 1.5 %FS (-20..85 C) read as a 3-sigma bound (ASSUMED reading of the DATASHEET band); bfsl: BFSL 0.25 %FS as 1 sigma
# (ASSUMED); cal: 0.1 %FS after a bench calibration over the sensor temperature range (REQUIREMENT candidate, not data)
SIG_W = (0.010, 0.020, 0.050)    # weighing 1 sigma candidates [kg] (allocation study; scale TO-DEFINE)
SIG_CAL_FLOW, SIG_CAL_CF = 0.015, 0.005   # static-fire calibration residuals (REQUIREMENT candidates, not data)
SEG_VAP_KG = (0.0059, 0.0080)    # DERIVED CoolProp: 44 cm3 of saturated N2O vapour at 15 / 24 C (vapour-start fallback)
RNG_COMB = 20261021              # own generator for the comb prior draws
RNG_ERR = 20261022               # own generator for the K error draws (+ run index)


def cfg_of(prof):
    tabs = V.e0e2_tables()
    if prof.startswith("A1"):
        over = V.case_over("A1_pc" if prof == "A1pc" else "A1_none", "liq", V.SEQ_WORST, tabs)
    else:
        jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
        over = dict(PC.DC["B1"], h_target=85.0, k_est_asc=2, m_fixed=PC.M_TANK, throat_jref=jr["B1"], throat_loop=1,
                    throat_g_band=TG.BAND)
    over = dict(over)
    m = float(over.pop("m_fixed"))
    return R.cfg_of(**dict(over, m_n2o=m)), over


def draws(cfg, prior):
    D = R.draw(np.random.default_rng(101), M_N(), cfg)
    if prior == "comb":
        rg = np.random.default_rng(RNG_COMB)
        for d in D:
            ecs = rg.uniform(ETA_CS[0], ETA_CS[1])
            ecf = rg.uniform(ETA_CF[0], ETA_CF[1])
            d["isp_scale"] = float(ecs / ETA_CS[2])
            d["thrust_scale"] = float(ecf / ETA_CF[2])
    return D


def M_N():
    return max(NR, 500)


def pc_of_f():
    """Pc as a function of the Pc-implied thrust: throttle_map_v2 rows at P_tank 5.0 MPa, port 25 mm (the map is the same for
    every port diameter at this tank pressure)."""
    import csv
    rows = [x for x in csv.reader(open(os.path.join(R.IFACE, "throttle_map_v2.csv"))) if x and not x[0].startswith("#")]
    h = rows[0]
    a = []
    for x in rows[1:]:
        try:
            a.append([float(x[h.index(k)]) for k in ("P_tank_Pa", "D_port_m", "F_N", "Pc_Pa")])
        except ValueError:
            continue
    a = np.array(a)
    m = (np.abs(a[:, 0] - 5.0e6) < 1.0) & (np.abs(a[:, 1] - 0.025) < 1e-6)
    o = np.argsort(a[m, 2])
    return a[m, 2][o], a[m, 3][o]


F_TAB, PC_TAB = None, None


def pc_from_fpc(fpc):
    global F_TAB, PC_TAB
    if F_TAB is None:
        F_TAB, PC_TAB = pc_of_f()
    # linear through the map points; below the lowest map point Pc ~ F (proportional to the first point)
    return np.where(fpc >= F_TAB[0], np.interp(fpc, F_TAB, PC_TAB), fpc * PC_TAB[0] / F_TAB[0])


def cumtrapz0(y, dt):
    c = np.zeros_like(y)
    c[..., 1:] = np.cumsum(0.5 * (y[..., 1:] + y[..., :-1]) * dt, axis=-1)
    return c


def fly_one(cfg, dr, prof):
    c, disp = R.run_cfg(cfg, dr)
    c = dict(c, rec_dt=DT_REC)
    par = R.build(c, disp)[0]
    res, rec, info = R.fly(c, disp, nrec=40000)
    return par, res, rec, info, c


# estimator configurations: est FM / RE; flow model of the FM part: true (the 6-DOF flow: isolates sensor terms), map (nominal
# Combustion map, uncalibrated), cal (map scaled by the flight's true c* factor x (1 + N(0, SIG_CAL_FLOW)), i.e. after a static-fire
# calibration); ghat: FSW throat-growth model on (FM1) or off (FM0); sp: Pc transducer 1 sigma [Pa]; sw: weighing 1 sigma [kg];
# starts: rand (truth U(0, 8.7 g) per start, FSW subtracts 4.35 g) or nominal (truth = FSW value); imu: accelerometer scale factor
# and bias drawn from the IMU class (RE only); rc: RE c-error model exact / map (c_true / c_map = tsc0 isc (1 + kc g)) / cal
CONFIGS = {
    "FM_ideal":            dict(est="FM", flow="true", ghat=0, sp=0.0, sw=0.0, starts="nominal"),
    "RE_ideal":            dict(est="RE", flow="true", ghat=0, sp=0.0, sw=0.0, starts="nominal", imu=False, rc="exact"),
    "FM0_uncal_teb3_w20":  dict(est="FM", flow="map", ghat=0, sp=SIG_P["teb3"], sw=0.020, starts="rand"),
    "FM1_uncal_teb3_w20":  dict(est="FM", flow="map", ghat=1, sp=SIG_P["teb3"], sw=0.020, starts="rand"),
    "FM1_uncal_bfsl_w20":  dict(est="FM", flow="map", ghat=1, sp=SIG_P["bfsl"], sw=0.020, starts="rand"),
    "RE_uncal_teb3_w20":   dict(est="RE", flow="map", ghat=1, sp=SIG_P["teb3"], sw=0.020, starts="rand", imu=True, rc="map"),
    "FM1_cal_pccal_w20":   dict(est="FM", flow="cal", ghat=1, sp=SIG_P["cal"], sw=0.020, starts="rand"),
    "FM0_cal_pccal_w20":   dict(est="FM", flow="cal", ghat=0, sp=SIG_P["cal"], sw=0.020, starts="rand"),
    "RE_cal_pccal_w20":    dict(est="RE", flow="cal", ghat=1, sp=SIG_P["cal"], sw=0.020, starts="rand", imu=True, rc="cal"),
    "FM1_cal_pccal_w10":   dict(est="FM", flow="cal", ghat=1, sp=SIG_P["cal"], sw=0.010, starts="rand"),
    "FM1_cal_pccal_w50":   dict(est="FM", flow="cal", ghat=1, sp=SIG_P["cal"], sw=0.050, starts="rand"),
    # one-at-a-time sources
    "src_weigh_w10":       dict(est="FM", flow="true", ghat=0, sp=0.0, sw=0.010, starts="nominal"),
    "src_weigh_w20":       dict(est="FM", flow="true", ghat=0, sp=0.0, sw=0.020, starts="nominal"),
    "src_weigh_w50":       dict(est="FM", flow="true", ghat=0, sp=0.0, sw=0.050, starts="nominal"),
    "src_pc_teb3":         dict(est="FM", flow="true", ghat=0, sp=SIG_P["teb3"], sw=0.0, starts="nominal"),
    "src_pc_bfsl":         dict(est="FM", flow="true", ghat=0, sp=SIG_P["bfsl"], sw=0.0, starts="nominal"),
    "src_pc_cal":          dict(est="FM", flow="true", ghat=0, sp=SIG_P["cal"], sw=0.0, starts="nominal"),
    "src_starts":          dict(est="FM", flow="true", ghat=0, sp=0.0, sw=0.0, starts="rand"),
    "src_flowmap_FM0":     dict(est="FM", flow="map", ghat=0, sp=0.0, sw=0.0, starts="nominal"),
    "src_flowmap_FM1":     dict(est="FM", flow="map", ghat=1, sp=0.0, sw=0.0, starts="nominal"),
    "src_flowmap_cal_FM1": dict(est="FM", flow="cal", ghat=1, sp=0.0, sw=0.0, starts="nominal"),
    "src_flowmap_cal_FM0": dict(est="FM", flow="cal", ghat=0, sp=0.0, sw=0.0, starts="nominal"),
    "src_RE_imu_only":     dict(est="RE", flow="true", ghat=0, sp=0.0, sw=0.0, starts="nominal", imu=True, rc="exact"),
    "src_RE_c_map":        dict(est="RE", flow="true", ghat=0, sp=0.0, sw=0.0, starts="nominal", imu=False, rc="map"),
    "src_RE_c_cal":        dict(est="RE", flow="true", ghat=0, sp=0.0, sw=0.0, starts="nominal", imu=False, rc="cal"),
}


def j_ref_of(prof):
    jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
    return float(jr["A1" if prof.startswith("A1") else "B1"])


def reduce_run(par, res, rec, prof, cfg_imu, run, prior):
    """per-run reductions for every estimator configuration (K error draws per run)."""
    t = rec[:, I["t"]]
    n = len(t)
    dtv = np.diff(t)
    F = rec[:, I["F"]]
    Fpc = rec[:, I["Fpc"]]
    m = rec[:, I["m"]]
    mdot = rec[:, I["mox"]] + rec[:, I["mf"]]
    g = rec[:, I["thg"]]
    tsc0 = par[PN["thrust_scale"]]
    isc = par[PN["isp_scale"]]
    loop = par[PN["throat_loop"]] > 0.5
    thr_ff = (1.0 + g) if loop else np.ones(n)
    on = F > 0.0
    mdot_map = np.where(on, mdot * isc / thr_ff, 0.0)       # the nominal map's flow at the Pc-implied thrust
    Fmax = par[PN["Fmax"]]
    J = np.r_[0.0, np.cumsum(np.where(on[1:], (np.maximum(Fpc[1:], 0.0) / Fmax) ** 0.68, 0.0) * dtv)]
    gU = np.minimum(1.0, J / j_ref_of(prof))                 # FSW growth shape (its own Pc-implied thrust, sim6 law)
    Pc = np.where(on, pc_from_fpc(Fpc), 0.0)
    kcg = np.where(on & (Fpc > 1.0), (F / np.maximum(Fpc, 1e-9)) / (tsc0 * (1.0 + g)) - 1.0, 0.0)
    fax = rec[:, I["fax"]]
    pr_ = "A1" if prof.startswith("A1") else "B1"
    air, fcw, lit, drog = FT.windows(par, res, rec, pr_)
    vze = rec[:, I["vze"]]
    cda = np.where(vze > 0.0, par[PN["kest_cda_nf"]], par[PN["drag_cda_nom"]]) + np.where(FT.legs_state(par, rec, pr_),
                                                                                          par[PN["kest_cda_legs"]], 0.0)
    dd = 0.5 * 1.2 * cda * vze * vze
    Ds = np.where(vze > 0.0, dd, -dd)
    rise = on & ~np.r_[False, on[:-1]]
    Ns = np.cumsum(rise)
    nst = int(Ns[-1])
    q_true = np.r_[0.0, np.cumsum(0.5 * (mdot[1:] + mdot[:-1]) * dtv)]
    dm6 = m[0] - m
    lit_idx = np.where(on)[0]
    i_end = int(lit_idx[-1]) if len(lit_idx) else n - 1
    cons = dict(consumed_6dof_kg=float(dm6[i_end]), consumed_quadrature_kg=float(q_true[i_end]),
                rel_diff=float((q_true[i_end] - dm6[i_end]) / max(dm6[i_end], 1e-9)))
    rng = np.random.default_rng(RNG_ERR + run + (100000 if prior == "comb" else 0))
    Kd = K
    s_true = rng.uniform(0.0, START_MAX_KG, size=(Kd, max(nst, 1)))
    s_cum_true = np.zeros((Kd, n))
    for j in range(nst):
        s_cum_true += np.where(Ns[None, :] >= j + 1, s_true[:, j:j + 1], 0.0)
    s_cum_hat = 0.5 * START_MAX_KG * Ns.astype(float)
    zw = rng.standard_normal(Kd)
    zp = rng.standard_normal(Kd)
    imu = R.IMU[cfg_imu]
    a_sf = rng.normal(0.0, imu["a_sf"], Kd)
    a_bz = rng.normal(0.0, imu["a_bias"], Kd)
    zcf = rng.standard_normal(Kd)
    zcc = rng.standard_normal(Kd)
    out = dict(cons=cons, t_ign0=float(t[lit_idx[0]]) if len(lit_idx) else 0.0, i_end=i_end, m0=float(m[0]),
               m_end=float(m[i_end]), consumed_frac_end=float(dm6[i_end] / m[i_end]), n_starts=nst, isc=float(isc),
               tsc0=float(tsc0), g_end=float(g[i_end]), throat_g=float(par[PN["throat_g"]]), gU_end=float(gU[i_end]),
               J_end=float(J[i_end]), kcg_end=float(kcg[i_end]))
    fall = on & ~np.r_[on[1:], False]
    ends = np.where(fall)[0]
    out["burn_end_idx"] = ends.tolist()
    out["burn_end_t"] = [float(t[i]) for i in ends]
    c_true = np.where(on, F / np.maximum(mdot, 1e-12), 1.0)
    tg = np.arange(0.0, 60.0, 0.25)
    gidx = np.minimum(np.searchsorted(t, out["t_ign0"] + tg), n - 1)
    gvalid = on[gidx] & (out["t_ign0"] + tg <= t[-1])

    def cumtr(y):
        c = np.zeros_like(y)
        c[:, 1:] = np.cumsum(0.5 * (y[:, 1:] + y[:, :-1]) * dtv[None, :], axis=1)
        return c

    def fm_flow(cf):
        if cf["flow"] == "true":
            base = np.broadcast_to(mdot[None, :], (Kd, n))
        else:
            kg = (1.0 + G_HAT_END * gU) if cf["ghat"] else np.ones(n)
            base = mdot_map[None, :] * kg[None, :]
            if cf["flow"] == "cal":
                base = base / isc * (1.0 + SIG_CAL_FLOW * zcf[:, None])
        dP = cf["sp"] * zp[:, None]
        return np.where(Pc[None, :] > 0.0, base * (1.0 + dP / np.maximum(Pc[None, :], 1.0)), 0.0)

    red = {}
    for name, cf in CONFIGS.items():
        flow = fm_flow(cf)
        m0h = m[0] + cf["sw"] * zw
        if cf["est"] == "FM":
            mh = m0h[:, None] - s_cum_hat[None, :] - cumtr(flow)
        else:
            if cf["rc"] == "exact":
                rc = np.ones((Kd, n))
            elif cf["rc"] == "map":
                rc = np.broadcast_to((tsc0 * isc * (1.0 + kcg))[None, :], (Kd, n))
            else:
                rc = ((1.0 + SIG_CAL_FLOW * zcf) / (1.0 + SIG_CAL_CF * zcc))[:, None] * (1.0 + kcg)[None, :]
            if cf.get("imu"):
                fm_ = fax[None, :] * (1.0 + a_sf[:, None]) + a_bz[:, None]
            else:
                fm_ = np.broadcast_to(fax[None, :], (Kd, n))
            kre = rc / c_true[None, :]                   # 1 / c_hat
            act = fcw & on
            both = act[1:] & act[:-1]                    # intervals integrated by the rocket equation
            dq = 0.5 * (flow[:, 1:] + flow[:, :-1]) * dtv[None, :]
            dsh = np.diff(s_cum_hat)
            a_ = fm_ * kre
            b_ = Ds[None, :] * kre
            # semi-implicit trapezoid: m_i = m_{i-1} (1 - alpha_i) + beta_i, solved as a linear recurrence (vectorised)
            alpha = np.where(both[None, :], 0.5 * (a_[:, 1:] + a_[:, :-1]) * dtv[None, :], 0.0)
            beta = np.where(both[None, :], -0.5 * (b_[:, 1:] + b_[:, :-1]) * dtv[None, :], -dq) - dsh[None, :]
            gam = 1.0 - alpha
            Pg = np.cumprod(gam, axis=1)
            x0 = (m0h - s_cum_hat[0])[:, None]
            mh = np.empty((Kd, n))
            mh[:, :1] = x0
            mh[:, 1:] = Pg * (x0 + np.cumsum(beta / Pg, axis=1))
        mt = (m[0] - q_true)[None, :] - (s_cum_true if cf["starts"] == "rand" else s_cum_hat[None, :])
        e = mh / mt - 1.0
        r = dict(e_end=e[:, i_end].astype(np.float32),
                 e_burn_ends=e[:, ends].astype(np.float32) if len(ends) else np.zeros((Kd, 0), np.float32),
                 maxabs_lit=(np.max(np.abs(e[:, on]), axis=1) if on.any() else np.zeros(Kd)).astype(np.float32),
                 maxabs_fc=(np.max(np.abs(e[:, fcw & on]), axis=1) if (fcw & on).any() else np.zeros(Kd)).astype(np.float32))
        rms = np.sqrt(np.mean(e[:, gidx] ** 2, axis=0))
        rms[~gvalid] = np.nan
        r["rms_grid"] = rms.astype(np.float32)
        red[name] = r
    out["red"] = red
    return out


def part_fly():
    os.makedirs(OUT, exist_ok=True)
    for prof in PROFILES:
        cfg, over = cfg_of(prof)
        for prior in PRIORS:
            p = os.path.join(OUT, f"mest_{prof}_{prior}.npz")
            if os.path.exists(p) and os.environ.get("GNC_MEST_FORCE") != "1":
                print("exists", p, flush=True)
                continue
            t0 = time.time()
            D = draws(cfg, prior)[:NR]
            runs = []
            oks = []
            for i, dr in enumerate(D):
                par, res, rec, info, c = fly_one(cfg, dr, prof)
                runs.append(reduce_run(par, res, rec, prof, cfg["imu"], i, prior))
                oks.append(float(R.success(res)))
                if i % 50 == 0:
                    print(f"{prof} {prior} run {i} ({time.time() - t0:.0f} s)", flush=True)
            names = list(runs[0]["red"].keys())
            arr = {}
            for nm in names:
                for kk in ("e_end", "maxabs_lit", "maxabs_fc", "rms_grid"):
                    arr[f"{nm}|{kk}"] = np.stack([r["red"][nm][kk] for r in runs])
            meta = [{k: v for k, v in r.items() if k != "red"} for r in runs]
            for j, r in enumerate(runs):
                for nm in names:
                    meta[j].setdefault("e_burn_ends", {})[nm] = r["red"][nm]["e_burn_ends"].tolist()
            np.savez_compressed(p, ok=np.array(oks), **arr)
            with open(p.replace(".npz", "_meta.json"), "w") as f:
                json.dump(dict(version=VERSION, profile=prof, prior=prior, n=len(runs), K=K, cpu_s=time.time() - t0,
                               config={k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v))
                                       for k, v in over.items() if k not in ("t_ign_q",)},
                               imu=cfg["imu"], runs=meta), f, default=float)
            print(f"wrote {p} ({time.time() - t0:.0f} s), P {np.mean(oks):.3f}", flush=True)


def stats_of(x):
    x = np.asarray(x, float).ravel()
    return dict(rms=float(np.sqrt(np.mean(x ** 2))), mean=float(np.mean(x)), std=float(np.std(x)),
                p99_abs=float(np.percentile(np.abs(x), 99)), max_abs=float(np.max(np.abs(x))),
                frac_abs_gt_1pct=float(np.mean(np.abs(x) > 0.01)))


def part_eval():
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE, requirement=(
        "flight-computer mass-estimate error <= 1 % (1 sigma) throughout the burn (lead 2026-10-13, provisional)"),
        sources=dict(
            eta_c_star=dict(v=ETA_CS, tag="ASSUMED combustion.json v2.3 (assumed 0.92, band 0.85-0.96; T1 measures)"),
            eta_cf=dict(v=ETA_CF, tag="ASSUMED rc09_etacf_band_v2p4.json (CFD band 0.95-0.975; T1 measures)"),
            start_transient_max_kg=dict(v=START_MAX_KG, tag="SIM combustion.json v2.3 (N2O admitted before the 0.35 s ignition "
                                        "check); truth U(0, 8.7 g) per start, FSW subtracts 4.35 g (ASSUMED)"),
            pc_sensor=dict(v=dict(full_scale_Pa=PC_FS, sigma_Pa=SIG_P), tag="DATASHEET electronics.json v1 (BFSL 0.25 %FS, TEB "
                           "1.5 %FS -20..85 C, auto-zero before each start); teb3 = TEB as 3 sigma, bfsl = BFSL as 1 sigma "
                           "(ASSUMED readings); cal = 0.1 %FS bench-calibrated (REQUIREMENT candidate)"),
            growth_model=dict(v=G_HAT_END, tag="REQ ENG-06 rev 2 band 0.07-0.11 (middle); sim6 growth law (F_pc/F_max)^0.68"),
            calibration=dict(v=dict(flow=SIG_CAL_FLOW, cf=SIG_CAL_CF), tag="REQUIREMENT candidates for the static-fire calibration"),
            seg_vapour_kg=dict(v=SEG_VAP_KG, tag="DERIVED CoolProp, 44 cm3 saturated vapour 15 / 24 C (vapour-start fallback)"),
            imu="run6 IMU class of the configuration (a_sf, a_bias)"),
        profiles={})
    for prof in PROFILES:
        for prior in PRIORS:
            p = os.path.join(OUT, f"mest_{prof}_{prior}.npz")
            if not os.path.exists(p):
                continue
            z = np.load(p)
            meta = json.load(open(p.replace(".npz", "_meta.json")))
            runs = meta["runs"]
            names = sorted({k.split("|")[0] for k in z.files if "|" in k})
            pr = dict(n=meta["n"], K=meta["K"], P_flights=float(np.mean(z["ok"])), imu=meta["imu"],
                      consumed_frac_end_p50_p99_max=[float(np.percentile([r["consumed_frac_end"] for r in runs], q)) for q in (50, 99, 100)],
                      flow_consistency_rel_diff_max_abs=float(np.max(np.abs([r["cons"]["rel_diff"] for r in runs]))),
                      g_end_min_max=[float(min(r["g_end"] for r in runs)), float(max(r["g_end"] for r in runs))],
                      n_starts=sorted({r["n_starts"] for r in runs}), configs={})
            tgrid = np.arange(0.0, 60.0, 0.25)
            for nm in names:
                e_end = z[f"{nm}|e_end"]
                ml = z[f"{nm}|maxabs_lit"]
                mf = z[f"{nm}|maxabs_fc"]
                rg = z[f"{nm}|rms_grid"]
                # RMS over runs and draws at each grid time (only where lit in that run)
                with np.errstate(invalid="ignore"):
                    prof_rms = np.sqrt(np.nanmean(rg.astype(float) ** 2, axis=0))
                    nlit = np.sum(~np.isnan(rg), axis=0)
                keep = nlit >= max(10, int(0.05 * len(rg)))
                c = dict(e_end=stats_of(e_end), maxabs_lit=stats_of(ml), maxabs_fc=stats_of(mf),
                         rms_profile=dict(t_from_first_ignition_s=[float(x) for x in tgrid[keep]],
                                          rms=[float(x) for x in prof_rms[keep]], n_runs_lit=[int(x) for x in nlit[keep]]),
                         rms_profile_max=float(np.nanmax(prof_rms[keep])) if keep.any() else None)
                # per-burn ends (A1: ascent MECO, landing; B1: one burn)
                be = [r["e_burn_ends"][nm] for r in runs]
                nb = min(len(b[0]) if len(b) and len(b[0]) else 0 for b in be) if be else 0
                c["e_at_burn_ends_rms"] = [float(np.sqrt(np.mean(np.concatenate([np.asarray(b)[:, j] for b in be]) ** 2)))
                                           for j in range(nb)] if nb else []
                pr["configs"][nm] = c
            out["profiles"][f"{prof}|{prior}"] = pr
            print(f"== {prof} {prior}: P {pr['P_flights']:.3f}, consumed/m_end p50/p99/max {pr['consumed_frac_end_p50_p99_max']}, "
                  f"flow consistency {pr['flow_consistency_rel_diff_max_abs']:.2e}, g_end {pr['g_end_min_max']}", flush=True)
            for nm, c in pr["configs"].items():
                print(f"   {nm:22s} end rms {c['e_end']['rms'] * 100:.3f} % (mean {c['e_end']['mean'] * 100:+.3f}) p99 "
                      f"{c['e_end']['p99_abs'] * 100:.3f} | max|e| lit rms {c['maxabs_lit']['rms'] * 100:.3f} p99 "
                      f"{c['maxabs_lit']['p99_abs'] * 100:.3f} >1% {c['maxabs_lit']['frac_abs_gt_1pct'] * 100:.2f} % | fc p99 "
                      f"{c['maxabs_fc']['p99_abs'] * 100:.3f} | profile max rms {100 * (c['rms_profile_max'] or float('nan')):.3f} % | "
                      f"burn ends rms {[round(100 * x, 3) for x in c['e_at_burn_ends_rms']]}", flush=True)
    with open(os.path.join(OUT, "mass_est.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "mass_est.json"), flush=True)


def main():
    if "fly" in PARTS:
        part_fly()
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()
