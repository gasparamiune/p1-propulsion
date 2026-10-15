"""m2_mass_est v2 (GNC, 2026-10-13): the flight-software MASS ESTIMATOR flown in the 6-DOF (sim6 v2.8-dev amendment M) - error
budget with bias and random parts, the Pc-lost rule, and the FC_THRUST 650 N threshold re-checked on both sides.

Review REV-GNC-1 RG-16 (MAJOR): (1) state the <= 1 % requirement as a total budget over the burn (weighing at ARM, integration: map,
c*, growth; Pc-lost behaviour) with bias and random parts separated; (2) GNC specifies the estimator and flies it in sim6 with the
errors in the FLOW, not only in the thrust; (3) explain the A1 k_hat offset (m2_khat_offset v1.1); (4) re-check 650 N against
the budget's systematic terms on both sides. Lead decision 2026-10-13: the m_est propagation without Pc is specified by GNC inside
this budget.

ESTIMATOR (FSW specification, sim6 v2.8-dev amendment M, verified by m2_bitcheck_v28 v1.1 parts G and H):
  ARM       m_hat = weighed mass (scale error w, per flight: RANDOM)
  start     m_hat -= FSW allowance per start (4.35 g); truth U(0, 8.7 g) (Combustion: N2O admitted before the ignition check): RANDOM
  Pc valid  dm_hat/dt = -[mdot_map(F_pc) k_cal (1 + g_hat) + dq]; F_pc = Pc-implied thrust; k_cal = FSW flow calibration
            (static-fire residual: BIAS per engine; or nominal map, uncalibrated: BIAS = the engine's c* error); g_hat =
            0.09 min(1, J_hat / J_ref) (REQ ENG-06 rev 2 band middle; BIAS per engine against the truth growth U(0.07, 0.11));
            dq = Pc transducer offset after the pad auto-zero x flow per Pc (RANDOM per flight)
  Pc lost   (ECU open loop, PC_SENSOR; truth thrust AND flow per command x k, k = 1.143 or 1 / 1.143 = the lead's Cd band edges,
            BIAS per engine and flight condition): inside the FC_THRUST valid window the rocket equation on the accelerometer,
            dm_hat/dt = -F_acc / c_map(F_acc) = -mdot_map(F_acc) k_cal (F_acc = m_hat f_z + D_model; it carries the relative
            error at the loss and does not drift with k); outside the window the map flow at a first-order model of the commanded
            thrust (tau 45.5 ms, ENG-03); a loss before liftoff is a pad abort (not flown: the from-ignition cases bound a loss just
            after liftoff)
  option    kest_comp 1: accelerometer axial specific force corrected to the CG with the gyro rates, divided by the encoder
            cos(delta) (k_hat and F_acc)
PRIORS: comb (Combustion's bands: isp_scale = eta_c* / 0.92, eta_c* U(0.85, 0.96); thrust_scale = eta_cf / 0.975, eta_cf U(0.95,
  0.975); ASSUMED uniform, own generator 20261021, the m2_mass_est v1 'comb' draws) for the MC part; the fct part uses the GNC brief
  draws as m2_fc_thrust v1.1 (comparability with the v3.1 FC_THRUST results).
PART mc (RES only, 500 runs per case, seed-101 draws, the bases' N2O loads; error draws from an own generator 20261023 + run, the
  same in every case = paired):
  mode0      legacy guidance mass m (1 + m_est_err), m_est_err ~ N(0, 3 %) (ASSUMED, run6 draw): the P comparator
  ideal      flown estimator with exact knowledge (k_cal = 1 / isp_scale, g_hat = the run's growth, J_ref exact; no sensor errors)
  src_*      one source on top of ideal: w20 (w ~ N(0, 20 g)), pcteb (TEB 1.5 %FS as 3 sigma), pccal (0.1 %FS), starts, cal15
             (k_cal residual N(0, 1.5 %)), uncal (nominal map), gmodel (g_hat 0.09 band middle), gnone (no growth model)
  tot_cal    w20 + pccal + starts + cal15 + gmodel (the calibrated FSW); tot_uncal: w20 + pcteb + starts + uncal + gmodel;
             tot_cal_comp = tot_cal + kest_comp 1
  PCL (A1_none, B1 62 m without growth): pclhi / pcllo = truth flow and thrust per command x 1.143 / / 1.143 from ignition;
             mode0 comparator, re (RE in the window), cmd (commanded-thrust model only), re_comp (re + kest_comp 1); FSW errors
             w20 + starts + cal15 (Pc lost: no dq, no growth learning)
PART fct (1 ms records, m2_fc_thrust v1.1 configurations A1 0.81 s liquid / B1 85 m, pc2 no growth, brief draws, N_FCT runs):
  F_acc rebuilt as m2_fc_thrust.reconstruct with the FLOWN m_hat (record mhe, mex) instead of m (1 + m_est_err); tau 20 ms filter,
  100 Hz frames at a random phase, 0.1 N steps, held maximum over 3 frames in the fc window (an abort at T happens iff it exceeds
  T); relative error eps = F_acc / F_true - 1 of the filtered streams at the fc frames past the 0.1 s guard with F_true > 300 N.
  Cases: H_cal (tot_cal errors, Pc valid), H_cal_comp, Lhi_re / Lhi_cmd / Lhi_re_comp (thrust_scale 1.143, flow x 1.143, Pc lost
  from ignition: the FALSE-ABORT side), Llo_re / Llo_cmd / Llo_re_comp (/ 1.143: the under-read side).
  Missed-detection side: the SYSTEMATIC relative error of the flight at an onset instant, b = (noise-free F_acc - a_bz m_hat) /
  F_true - 1 (flown m_hat error, accelerometer scale factor, IMU lever arm, nozzle direction, drag-model residual; averaged over
  20 ms), at 5 onset instants per run evenly spaced in the fc window past the guard with F_true > 300 N; a stuck full-stroke ramp
  from the flight thrust at the onset to 670 N at 2.5 kN/s and to 876 N at 3.6 kN/s is passed through x = (1 + b) F + a_bz m_hat +
  noise (m2_fc_thrust v1.1 stuck_series: same noise model, tau 20 ms, frames, 3-frame hold) and detected at T = 650 N within
  2 s (miss otherwise; an alarm before the onset is a false abort). b is taken as relative at the flight thrust (the additive
  lever-arm, direction and drag terms are relatively smaller at 670 N: conservative). eps (noisy per-frame relative error of the
  filtered stream, F_true > 300 N) is reported for reference only: a per-frame statistic is not a detection statistic.
Env: GNC_IFACE, GNC_ACT_RATE (v3c set), GNC_MEST2_PARTS (mc,eval,fct,fcteval), GNC_MEST2_SPLIT k/n, GNC_MEST2_N (500),
GNC_MEST2_NFCT (200), GNC_MEST2_OUT (out/mass_est_v2)."""
import csv
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
import m2_eng03_rate as E  # noqa: E402
import m2_throat_mc as TG  # noqa: E402

VERSION = "m2_mass_est v2"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_MEST2_OUT", f"{S}/mass_est_v2")
PARTS = os.environ.get("GNC_MEST2_PARTS", "mc,eval").split(",")
SPLIT = os.environ.get("GNC_MEST2_SPLIT", "0/1")
NR = int(os.environ.get("GNC_MEST2_N", "500"))
NFCT = int(os.environ.get("GNC_MEST2_NFCT", "200"))
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
# ------------------------------------------------------------------ sources (values and tags)
ETA_CS = (0.85, 0.96, 0.92)       # ASSUMED combustion.json v2.3 (eta_c* assumed 0.92, band 0.85-0.96)
ETA_CF = (0.95, 0.975, 0.975)     # ASSUMED rc09_etacf_band_v2p4.json (CFD band 0.95-0.975)
START_MAX_KG = 0.0087             # SIM combustion.json v2.3 (N2O admitted before the 0.35 s ignition check)
PC_FS = 3.447e6                   # DATASHEET electronics.json v1 TE M3234 0-500 psig
SIG_P = dict(teb3=0.015 * PC_FS / 3.0, cal=0.001 * PC_FS)   # ASSUMED readings of the DATASHEET band / REQUIREMENT candidate
FLOW_PER_PC = 0.1035e-6           # DERIVED throttle_map_v2.csv: (mdot_ox + mdot_f) / Pc = 0.101-0.106 kg/s/MPa over 62-500 N [kg/s/Pa]
SIG_W = 0.020                     # REQUIREMENT candidate: ARM weighing 1 sigma [kg] (scale TO-DEFINE)
SIG_CAL_FLOW = 0.015              # REQUIREMENT candidate: static-fire flow-calibration residual 1 sigma
G_HAT = 0.09                      # REQ ENG-06 rev 2 band 0.07-0.11, middle
CD_BAND = 1.143                   # REQ lead (Cd band factor of the 650 N threshold), ASSUMED there
TAU_CMD = 0.100 / 2.197           # REQ ENG-03 closed-loop t10-90 100 ms (first-order equivalent)
RNG_COMB = 20261021
RNG_ERR = 20261023
BASES = ("A1_pc", "A1_none", "rbl_B1_lead62_pc_k2", "tgl_B1_lead62_pc_k2")
PCL_BASES = ("A1_none", "B1_62_none")
SRC = dict(w20=dict(w=SIG_W), pcteb=dict(sp=SIG_P["teb3"]), pccal=dict(sp=SIG_P["cal"]), starts=dict(starts=True),
           cal15=dict(kcal="cal"), uncal=dict(kcal="nominal"), gmodel=dict(ghat="model"), gnone=dict(ghat="none"))


def case_specs():
    c = {"mode0": dict(mode=0), "ideal": dict(mode=1)}
    for k, v in SRC.items():
        c["src_" + k] = dict(mode=1, **v)
    c["tot_cal"] = dict(mode=1, w=SIG_W, sp=SIG_P["cal"], starts=True, kcal="cal", ghat="model")
    c["tot_uncal"] = dict(mode=1, w=SIG_W, sp=SIG_P["teb3"], starts=True, kcal="nominal", ghat="model")
    c["tot_cal_comp"] = dict(c["tot_cal"], comp=1)
    return c


def pcl_specs():
    c = {}
    for tag, k in (("pclhi", CD_BAND), ("pcllo", 1.0 / CD_BAND)):
        c[f"mode0_{tag}"] = dict(mode=0, pcl_k=k)
        base = dict(mode=1, pcl_k=k, w=SIG_W, starts=True, kcal="cal", ghat="none", pcl=True)
        c[f"{tag}_re"] = dict(base, pcl_re=1)
        c[f"{tag}_cmd"] = dict(base, pcl_re=0)
        c[f"{tag}_re_comp"] = dict(base, pcl_re=1, comp=1)
    return c


def base_cfg(base):
    if base == "B1_62_none":
        over, _, bjson = E.base_ref("tgl_B1_lead62_pc_k2")
        over = dict(over, throat_g_band=None, throat_jref=None)
    else:
        over, _, bjson = E.base_ref(base)
    m = json.load(open(bjson))["m_n2o_mc_kg"]
    return R.cfg_of(**dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(m)))


def comb_draws(n):
    rg = np.random.default_rng(RNG_COMB)
    out = []
    for _ in range(n):
        ecs = rg.uniform(ETA_CS[0], ETA_CS[1])
        ecf = rg.uniform(ETA_CF[0], ETA_CF[1])
        out.append((float(ecs / ETA_CS[2]), float(ecf / ETA_CF[2])))
    return out


def err_draws(i):
    rg = np.random.default_rng(RNG_ERR + i)
    return dict(zw=rg.standard_normal(), zp=rg.standard_normal(), u1=rg.uniform(0.0, START_MAX_KG),
                u2=rg.uniform(0.0, START_MAX_KG), zc=rg.standard_normal())


def run_cfg_case(cfg, dr, spec, i, prior):
    """(c, disp) of run i under a case spec."""
    d = dict(dr)
    if prior == "comb":
        isc_, tsc_ = COMB[i]
        d["isp_scale"], d["thrust_scale"] = isc_, tsc_
    isc_d = float(d["isp_scale"])
    k = spec.get("pcl_k")
    if k is not None:
        if prior == "fct":
            d["thrust_scale"] = float(k)          # m2_fc_thrust v1.1 L branch convention (every run at the band edge)
        else:
            d["thrust_scale"] = float(d["thrust_scale"]) * k
        d["isp_scale"] = isc_d / k                # flow per command x k (Cd error: thrust and flow scale together)
    c, disp = R.run_cfg(cfg, d)
    if spec.get("mode", 0) < 1:
        return c, disp
    ed = err_draws(i)
    tg_ = float(d.get("throat_g") or 0.0) if (cfg.get("throat_g_band") or cfg.get("throat_g", 0.0)) else 0.0
    jref = float(cfg.get("throat_jref") or 0.0)
    kc = spec.get("kcal", "exact")
    kcal = 1.0 / isc_d if kc == "exact" else ((1.0 / isc_d) * (1.0 + SIG_CAL_FLOW * ed["zc"]) if kc == "cal" else 1.0)
    gh = spec.get("ghat", "exact")
    ghat = tg_ if gh == "exact" else (G_HAT if gh == "model" else 0.0)
    st = spec.get("starts", False)
    c = dict(c, mest_mode=1, mest_w=spec.get("w", 0.0) * ed["zw"], mest_dq=spec.get("sp", 0.0) * ed["zp"] * FLOW_PER_PC,
             mest_kcal=kcal, mest_ghat=ghat, mest_jref=jref if jref > 0.0 else (TG_JREF_DEFAULT if ghat > 0.0 else 0.0),
             mest_s1=(ed["u1"] - 0.5 * START_MAX_KG) if st else 0.0, mest_s2=(ed["u2"] - 0.5 * START_MAX_KG) if st else 0.0,
             mest_pcl_t=0.0 if spec.get("pcl") else -1.0, mest_pcl_re=float(spec.get("pcl_re", 1)), mest_tau=TAU_CMD,
             kest_comp=int(spec.get("comp", 0)))
    if spec.get("comp"):
        c["kest_comp"] = 1
    return c, disp


TG_JREF_DEFAULT = 1.0    # placeholder J_ref for a growth model on a base without growth (A1_none: set from the A1 nominal below)
COMB = None


def jobs():
    j = [(b, n) for b in BASES for n in case_specs()]
    j += [(b, n) for b in PCL_BASES for n in pcl_specs()]
    return j


RES_KEYS = ("mest_e_b1end", "mest_e_end", "mest_e_min_lit", "mest_e_max_lit", "mest_e_maxabs_fc")


def part_mc():
    global COMB, TG_JREF_DEFAULT
    os.makedirs(OUT, exist_ok=True)
    COMB = comb_draws(max(NR, 500))
    jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
    k, n = (int(x) for x in SPLIT.split("/"))
    specs = dict(case_specs(), **pcl_specs())
    for base, name in jobs()[k::n]:
        p = os.path.join(OUT, f"mest2_{base}_{name}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_MEST2_FORCE") != "1":
            print("exists", base, name, flush=True)
            continue
        t0 = time.time()
        cfg = base_cfg(base)
        TG_JREF_DEFAULT = float(jr["A1" if base.startswith("A1") else "B1"])
        D = R.draw(np.random.default_rng(101), 500, cfg)
        rows = []
        for i in range(NR):
            c, disp = run_cfg_case(cfg, D[i], specs[name], i, "comb")
            res, _, _ = R.fly(c, disp, nrec=10)
            row = dict(run=i, ok=int(R.success(res)), td_vz=float(res["td_vz"]), td_vh=float(res["td_vh"]),
                       landed=float(res["landed"]), m_est_err=float(D[i]["m_est_err"]), isp_scale=COMB[i][0],
                       thrust_scale=COMB[i][1], throat_g=float(D[i].get("throat_g") or 0.0), wind=float(D[i]["_wind"]))
            row.update({kk: float(res[kk]) for kk in RES_KEYS})
            rows.append(row)
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        ok = np.mean([r["ok"] for r in rows])
        eb = np.array([r["mest_e_b1end"] for r in rows])
        ee = np.array([r["mest_e_end"] for r in rows])
        print(f"{base:22s} {name:16s}: P {ok:.3f} e_b1end rms {100 * np.sqrt(np.mean(eb ** 2)):.3f} % mean {100 * eb.mean():+.3f} | "
              f"e_end rms {100 * np.sqrt(np.mean(ee ** 2)):.3f} % mean {100 * ee.mean():+.3f} ({time.time() - t0:.0f} s)", flush=True)


def stats(x):
    x = np.asarray(x, float)
    return dict(rms=float(np.sqrt(np.mean(x ** 2))), mean=float(x.mean()), sd=float(x.std()), p01=float(np.percentile(x, 1)),
                p99=float(np.percentile(x, 99)), max_abs=float(np.max(np.abs(x))))


def mcnemar(a, b):
    from scipy.stats import binomtest
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    return dict(dP=float(b.mean() - a.mean()), lost=lost, gained=gained,
                p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0)


def part_eval():
    specs = dict(case_specs(), **pcl_specs())
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE, n_runs=NR,
               requirement="flight-computer mass-estimate error <= 1 % (1 sigma) throughout the burn (lead 2026-10-13, provisional)",
               sources=dict(
                   weighing=dict(sigma_kg=SIG_W, kind="RANDOM per flight", tag="REQUIREMENT candidate (scale TO-DEFINE)"),
                   pc_offset=dict(sigma_Pa=SIG_P, flow_per_Pc_kg_s_Pa=FLOW_PER_PC, kind="RANDOM per flight (after the pad auto-zero)",
                                  tag="DATASHEET electronics.json v1 TE M3234 (teb3 = TEB 1.5 %FS as 3 sigma, ASSUMED reading; cal = "
                                      "0.1 %FS REQUIREMENT candidate); flow per Pc DERIVED throttle_map_v2"),
                   starts=dict(max_kg=START_MAX_KG, kind="RANDOM per start", tag="SIM combustion.json v2.3; truth U(0, 8.7 g), FSW 4.35 g (ASSUMED)"),
                   flow_calibration=dict(sigma=SIG_CAL_FLOW, kind="BIAS per engine", tag="REQUIREMENT candidate (static-fire residual)"),
                   uncalibrated_map=dict(kind="BIAS per engine", tag="ASSUMED comb prior: eta_c* U(0.85, 0.96) / 0.92 (combustion.json v2.3)"),
                   growth_model=dict(g_hat=G_HAT, kind="BIAS per engine", tag="REQ ENG-06 rev 2 band 0.07-0.11 (truth U(0.07, 0.11) per run)"),
                   regression_band=dict(kind="BIAS per engine", tag="ASSUMED combustion.json regression law band (B1 rbl base)"),
                   pc_lost_flow=dict(k=CD_BAND, kind="BIAS per engine / condition", tag="REQ lead Cd band 1.143 (ASSUMED there)")),
               cases={k: {kk: (vv if not isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in specs.items()},
               by_base={})
    for base in BASES + PCL_BASES:
        bb = {}
        ref = {}
        for name in specs:
            p = os.path.join(OUT, f"mest2_{base}_{name}.csv")
            if not os.path.exists(p):
                continue
            rows = list(csv.DictReader(open(p)))
            ok = np.array([int(r["ok"]) for r in rows]) > 0
            x = dict(P=float(ok.mean()), ci95=TG.wilson(int(ok.sum()), len(ok)), n=len(rows))
            if specs[name].get("mode", 0) >= 1:
                for kk in RES_KEYS:
                    x[kk] = stats([float(r[kk]) for r in rows])
            ref[name] = ok
            bb[name] = x
        # paired comparisons: every mode-1 case against its mode-0 comparator (same prior and truth)
        for name, x in bb.items():
            if specs[name].get("mode", 0) < 1:
                continue
            cmp_ = "mode0" if not specs[name].get("pcl_k") else ("mode0_pclhi" if specs[name]["pcl_k"] > 1.0 else "mode0_pcllo")
            if cmp_ in ref:
                x["vs_" + cmp_] = mcnemar(ref[cmp_], ref[name])
        if bb:
            out["by_base"][base] = bb
    # budget: per profile, per source, e at the burn ends (rms) and the largest |e| in the FC window (p99); bias sources also by
    # their bound (max |e| over runs: a per-engine bias is one draw of the band)
    bud = {}
    for base, bb in out["by_base"].items():
        if "ideal" not in bb:
            continue
        rows = {}
        for k_ in ["ideal"] + ["src_" + s for s in SRC] + ["tot_cal", "tot_uncal", "tot_cal_comp"]:
            if k_ not in bb:
                continue
            x = bb[k_]
            rows[k_] = dict(kind=("RANDOM" if k_[4:] in ("w20", "pcteb", "pccal", "starts") else ("BIAS" if k_.startswith("src_") else
                                                                                             ("-" if k_ == "ideal" else "TOTAL"))),
                            e_b1end_rms=x["mest_e_b1end"]["rms"], e_b1end_mean=x["mest_e_b1end"]["mean"],
                            e_end_rms=x["mest_e_end"]["rms"], e_end_mean=x["mest_e_end"]["mean"],
                            e_end_max_abs=x["mest_e_end"]["max_abs"], fc_maxabs_p99=x["mest_e_maxabs_fc"]["p99"],
                            fc_maxabs_max=x["mest_e_maxabs_fc"]["max_abs"])
        rnd = [r_ for k_, r_ in rows.items() if r_["kind"] == "RANDOM" and k_ != "src_pcteb"]
        bias_cal = [rows[k_] for k_ in ("src_cal15", "src_gmodel") if k_ in rows]
        if rnd and bias_cal:
            rss = float(np.sqrt(sum(r_["e_end_rms"] ** 2 for r_ in rnd)))
            lin = float(sum(r_["e_end_max_abs"] for r_ in bias_cal))
            rows["budget_calibrated"] = dict(kind="RSS random (w20, pccal, starts) 1 sigma + linear sum of the bias bounds (cal15, gmodel)",
                                             random_rss_1sigma_end=rss, bias_bound_sum_end=lin,
                                             total_3sigma_plus_bias_end=3.0 * rss + lin)
        bud[base] = rows
    out["budget"] = bud
    with open(os.path.join(OUT, "mass_est_v2.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for base, bb in out["by_base"].items():
        print("==", base, flush=True)
        for name, x in bb.items():
            s_ = f"   {name:16s} P {x['P']:.3f}"
            if "mest_e_end" in x:
                s_ += (f" | e_b1end rms {100 * x['mest_e_b1end']['rms']:.3f} mean {100 * x['mest_e_b1end']['mean']:+.3f} | e_end rms "
                       f"{100 * x['mest_e_end']['rms']:.3f} mean {100 * x['mest_e_end']['mean']:+.3f} max|e| {100 * x['mest_e_end']['max_abs']:.3f}"
                       f" | fc max|e| p99 {100 * x['mest_e_maxabs_fc']['p99']:.3f} max {100 * x['mest_e_maxabs_fc']['max_abs']:.3f} %")
            for kk, vv in x.items():
                if kk.startswith("vs_"):
                    s_ += f" | {kk} dP {vv['dP']:+.3f} -{vv['lost']}/+{vv['gained']} p {vv['p_exact']:.3g}"
            print(s_, flush=True)
    print("wrote", os.path.join(OUT, "mass_est_v2.json"), flush=True)


# ================================================================== part fct: FC_THRUST 650 N on both sides with the flown m_hat
FCT_CASES = {
    "H_cal": dict(mode=1, w=SIG_W, sp=SIG_P["cal"], starts=True, kcal="cal", ghat="none"),
    "H_cal_comp": dict(mode=1, w=SIG_W, sp=SIG_P["cal"], starts=True, kcal="cal", ghat="none", comp=1),
    "Lhi_re": dict(mode=1, pcl_k=CD_BAND, w=SIG_W, starts=True, kcal="cal", ghat="none", pcl=True, pcl_re=1),
    "Lhi_cmd": dict(mode=1, pcl_k=CD_BAND, w=SIG_W, starts=True, kcal="cal", ghat="none", pcl=True, pcl_re=0),
    "Lhi_re_comp": dict(mode=1, pcl_k=CD_BAND, w=SIG_W, starts=True, kcal="cal", ghat="none", pcl=True, pcl_re=1, comp=1),
    "Llo_re": dict(mode=1, pcl_k=1.0 / CD_BAND, w=SIG_W, starts=True, kcal="cal", ghat="none", pcl=True, pcl_re=1),
    "Llo_cmd": dict(mode=1, pcl_k=1.0 / CD_BAND, w=SIG_W, starts=True, kcal="cal", ghat="none", pcl=True, pcl_re=0),
    "Llo_re_comp": dict(mode=1, pcl_k=1.0 / CD_BAND, w=SIG_W, starts=True, kcal="cal", ghat="none", pcl=True, pcl_re=1, comp=1)}
EPS_Q = (0.1, 1.0, 5.0, 50.0, 95.0, 99.0, 99.9)
T_ABORT = 650.0
F_STUCK = 670.0


def reconstruct_flown(par, rec, rng, prof, comp, noise=True):
    import m2_fc_thrust as FT
    F = rec[:, I["F"]]
    Fmax = par[PN["Fmax"]]
    rz = par[PN["z_imu"]] - rec[:, I["zcg"]]
    lev = (rec[:, I["wx"]] ** 2 + rec[:, I["wy"]] ** 2) * rz
    fimu = rec[:, I["fax"]] - lev
    vib = np.where(F > 1.0, par[PN["vib_sigma"]] * F / Fmax, 0.0)
    fm = fimu * (1.0 + par[PN["a_sf"]]) + par[PN["a_bz"]]
    if noise:
        fm = fm + (par[PN["a_vrw"]] / np.sqrt(FT.DT) + vib) * rng.standard_normal(len(F))
    m_hat = rec[:, I["mex"]] * (1.0 + rec[:, I["mhe"]])
    vze = rec[:, I["vze"]]
    cda = np.where(vze > 0.0, par[PN["kest_cda_nf"]], par[PN["drag_cda_nom"]]) + np.where(FT.legs_state(par, rec, prof),
                                                                                          par[PN["kest_cda_legs"]], 0.0)
    dd = 0.5 * 1.2 * cda * vze * vze
    cd = np.ones(len(F))
    if comp:
        fm = fm + lev                          # FSW compensation with the gyro rates (truth rates here: gyro error negligible)
        cd = np.cos(np.radians(rec[:, I["dgx"]])) * np.cos(np.radians(rec[:, I["dgy"]]))
    return (fm * m_hat + np.where(vze > 0.0, dd, -dd)) / cd


def part_fct():
    import m2_fc_thrust as FT
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    C, _ = FT.cfgs()
    jobs_ = [(p, c) for p in ("A1", "B1") for c in FCT_CASES][k::n]
    for prof, name in jobs_:
        p = os.path.join(OUT, f"fct2_{prof}_{name}.json")
        if os.path.exists(p) and os.environ.get("GNC_MEST2_FORCE") != "1":
            print("exists", prof, name, flush=True)
            continue
        t0 = time.time()
        cfg = C[prof]
        D = R.draw(np.random.default_rng(101), 500, cfg)
        spec = FCT_CASES[name]
        rows = []
        pooled = []
        for i in range(NFCT):
            c, disp = run_cfg_case(cfg, D[i], spec, i, "fct")
            c = dict(c, rec_dt=FT.DT)
            par = R.build(c, disp)[0]
            res, rec, _ = R.fly(c, disp, nrec=100000)
            rng = np.random.default_rng(20261019 + i + (0 if name.startswith("H") else 100000) + (0 if prof == "A1" else 200000))
            Fr = reconstruct_flown(par, rec, rng, prof, spec.get("comp", 0))
            air, fc, lit, drog = FT.windows(par, res, rec, prof)
            p0 = int(rng.integers(0, FT.KF))
            fa = np.round(FT.filt(Fr, 0.020)[p0::FT.KF] * 10.0) / 10.0
            ft = FT.filt(rec[:, I["F"]], 0.020)[p0::FT.KF]
            fw = fc[p0::FT.KF]
            fs = (fc & (FT.open_time(fc) >= FT.GUARD))[p0::FT.KF]
            hm, kh = FT.held_max(fa, fw)
            sel = fs & (ft > 300.0)
            eps = fa[sel] / ft[sel] - 1.0
            pooled.append(eps.astype(np.float32))
            mhe = rec[:, I["mhe"]]
            # missed-detection side: systematic relative error at onset instants, stuck ramps through it
            Fnf = reconstruct_flown(par, rec, None, prof, spec.get("comp", 0), noise=False)
            m_hat = rec[:, I["mex"]] * (1.0 + mhe)
            Ft_ = rec[:, I["F"]]
            ok_on = np.where(fc & (FT.open_time(fc) >= FT.GUARD) & (Ft_ > 300.0))[0]
            ons = ok_on[np.linspace(0, len(ok_on) - 1, 5).astype(int)] if len(ok_on) >= 5 else ok_on
            st = []
            rs = np.random.default_rng(20261024 + i + (0 if prof == "A1" else 200000))
            for j in ons:
                w_ = slice(max(j - 10, 0), j + 10)
                b = float(np.mean(Fnf[w_] - par[PN["a_bz"]] * m_hat[w_]) / np.mean(Ft_[w_]) - 1.0)
                F0 = float(Ft_[j])
                for Ff, rate in ((670.0, 2500.0), (876.0, 3600.0)):
                    tf_, hs_ = FT.stuck_series(1.0 + b, par[PN["a_bz"]] * float(m_hat[j]), float(m_hat[j]), par[PN["a_vrw"]],
                                               par[PN["vib_sigma"]], par[PN["Fmax"]], F0, Ff, rate, 0.020, rs)
                    td_, pre_, tc_ = FT.detect(tf_, hs_, T_ABORT, F0, rate)
                    st.append(dict(t_on=float(rec[j, I["t"]]), b=b, F0=F0, Ff=Ff, miss=bool(td_ is None and not pre_), pre=bool(pre_),
                                   t_detect=td_))
            rows.append(dict(run=i, stuck=st, ok=bool(R.success(res)), held_max_fc_N=float(hm), held_max_Ftrue_N=float(ft[kh]) if kh >= 0 else None,
                             Ftrue_max_fc_N=float(ft[fw].max()) if fw.any() else None,
                             eps_min=float(eps.min()) if len(eps) else None, eps_p01=float(np.percentile(eps, 1)) if len(eps) else None,
                             eps_med=float(np.median(eps)) if len(eps) else None,
                             miss_share_670=float(np.mean(F_STUCK * (1.0 + eps) <= T_ABORT)) if len(eps) else None,
                             mhe_fc_min=float(mhe[fc].min()) if fc.any() else None, mhe_fc_max=float(mhe[fc].max()) if fc.any() else None,
                             mhe_end=float(res["mest_e_end"]), n_frames=int(sel.sum())))
        allx = np.concatenate(pooled) if pooled else np.zeros(0)
        stk = [x for r in rows for x in r["stuck"]]
        bsys = np.array([x["b"] for x in stk if x["Ff"] == 670.0])
        stuck_sum = {}
        for Ff in (670.0, 876.0):
            xs = [x for x in stk if x["Ff"] == Ff]
            tdv = np.array([x["t_detect"] for x in xs if x["t_detect"] is not None])
            stuck_sum[f"{Ff:g}"] = dict(cases=len(xs), misses=int(sum(x["miss"] for x in xs)), pre_onset_alarms=int(sum(x["pre"] for x in xs)),
                                        runs_with_miss=len({r["run"] for r in rows for x in r["stuck"] if x["Ff"] == Ff and x["miss"]}),
                                        t_detect_p50_p99_max_s=[float(np.percentile(tdv, 50)), float(np.percentile(tdv, 99)), float(tdv.max())] if len(tdv) else None)
        hmx = np.array([r["held_max_fc_N"] for r in rows])
        out = dict(version=VERSION, profile=prof, case=name, spec=spec, n=len(rows), sim=s6.SIM6_VERSION,
                   P=float(np.mean([r["ok"] for r in rows])),
                   held_max_fc_N=dict(max=float(hmx.max()), p99=float(np.percentile(hmx, 99)), p50=float(np.median(hmx)),
                                      runs_above_650=int(np.sum(hmx > T_ABORT)), margin_to_650_N=float(T_ABORT - hmx.max())),
                   eps_pooled=dict(n_frames=int(len(allx)), quantiles_pct=list(EPS_Q),
                                   values=[float(np.percentile(allx, q)) for q in EPS_Q] if len(allx) else None,
                                   share_miss_670_at_650=float(np.mean(F_STUCK * (1.0 + allx) <= T_ABORT)) if len(allx) else None),
                   runs_with_any_miss_exposure=int(sum(1 for r in rows if (r["miss_share_670"] or 0.0) > 0.0)),
                   b_sys_at_onsets=dict(n=int(len(bsys)), quantiles_pct=[0.1, 1.0, 5.0, 50.0, 95.0, 99.0, 99.9],
                                        values=[float(np.percentile(bsys, q)) for q in (0.1, 1.0, 5.0, 50.0, 95.0, 99.0, 99.9)] if len(bsys) else None,
                                        min=float(bsys.min()) if len(bsys) else None),
                   stuck=stuck_sum,
                   mhe_fc_min_max=[float(np.min([r["mhe_fc_min"] for r in rows if r["mhe_fc_min"] is not None])),
                                   float(np.max([r["mhe_fc_max"] for r in rows if r["mhe_fc_max"] is not None]))],
                   cpu_s=time.time() - t0, runs=rows)
        with open(p, "w") as f:
            json.dump(out, f, indent=1, default=float)
        print(f"{prof} {name:12s}: P {out['P']:.3f} held max {out['held_max_fc_N']['max']:.1f} N (p99 {out['held_max_fc_N']['p99']:.1f}; "
              f">650: {out['held_max_fc_N']['runs_above_650']}) | b_sys p0.1/p1/p5/p50 "
              f"{[round(100 * v, 2) for v in (out['b_sys_at_onsets']['values'] or [])[:4]]} % min {100 * (out['b_sys_at_onsets']['min'] or 0):.2f} | "
              f"stuck 670: miss {stuck_sum['670']['misses']}/{stuck_sum['670']['cases']} pre {stuck_sum['670']['pre_onset_alarms']}; 876: miss "
              f"{stuck_sum['876']['misses']}/{stuck_sum['876']['cases']} | "
              f"m_hat err fc [{100 * out['mhe_fc_min_max'][0]:.2f}, {100 * out['mhe_fc_min_max'][1]:.2f}] % ({out['cpu_s']:.0f} s)", flush=True)


def part_fcteval():
    out = dict(version=VERSION, date="2026-10-13", threshold_N=T_ABORT, stuck_N=F_STUCK, cases={})
    for prof in ("A1", "B1"):
        for name in FCT_CASES:
            p = os.path.join(OUT, f"fct2_{prof}_{name}.json")
            if os.path.exists(p):
                d = json.load(open(p))
                d.pop("runs", None)
                out["cases"][f"{prof}|{name}"] = d
    with open(os.path.join(OUT, "fct_mest_v2.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "fct_mest_v2.json"), flush=True)


def main():
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()
    if "fct" in PARTS:
        part_fct()
    if "fcteval" in PARTS:
        part_fcteval()


if __name__ == "__main__":
    main()
