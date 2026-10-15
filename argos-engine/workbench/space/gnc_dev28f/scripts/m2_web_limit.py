"""m2_web_limit v1 (GNC, 2026-10-13): review REV-GNC-1 RG-03 (burn limit implemented in sim6 and in the flight-software model,
action at the limit defined, the 62 m band flown with it; band records selected by fuel burned, by O/F and the high-a longest
burns) and RG-10 (B apex predictor on the Pc-implied thrust). sim6 / run6 v2.8-dev amendment W.

Law (Combustion law_for_gnc, burn_limit_proxy_v2p4.json; DERIVED proxy of SIM grain_q1d v2.4, ASSUMED until T1-T4): uniform port
D from 25 mm, web w = (53.5 mm - D) / 2, dD/dt = 2 k 1.0e-3 (G_ox / 300)^n, G_ox = 4 mdot_ox / (pi D^2), no regression without
oxidiser flow. Truth: k = a x 1.016 (Combustion verification: the quasi-steady proxy needs k x 1.004-1.016 to match grain_q1d
t(w = 1 mm); the largest factor is used), n of the run, the run's oxidiser flow (map x growth feed x band phi_ox). Flight
software: k = 1.1 a_meas (lead rule), n = n_meas -/+ DN (both ends; the earlier limit governs), oxidiser flow = map at the
Pc-implied thrust x calibration (1 / isp_scale)(1 + 0.015 z) x (1 + growth model 0.09 min(1, J / J_ref)).
Measurement draws (own generator seed RNG_MEAS, the other draws unchanged): a_meas = a (1 + SIG_A z1), n_meas = n + SIG_N z2 (both
ASSUMED: T1-T4 scatter unknown), DN = 0.05 (ASSUMED half-width of the measured-n band).
Gating (lead rule 2026-10-13): an engine with a_meas >= 1.25 and n_meas <= 0.4 gets a grain change (it does not fly this grain);
statistics are given on the gated population and on the full band.

Base: rbl_B1_lead62_pc_k2 (m2_regband_mc v1.1): B1 62 m, FSW v2.7 provisional (k_est_asc 2 + ratchet), N2O 2.00 kg, growth
U(0.07, 0.11) + ECU Pc loop, regression band U(0.6, 1.5) x U(0.35, 0.68); 500 runs, seed 101 (band 20261017, growth 20261013).
Cases (paired run by run):
  W0       burn-limit monitor only (web_act 0), predictor as v2.7 (true thrust): flight identical to the stored rbl CSV (check)
  W0p      monitor + bpred_pc 1: RG-10 re-run against W0
  W1p      DEFINED ACTION (web_act 1) + bpred_pc 1: the proposed baseline
  W2p      shutdown at t_L (web_act 2) + bpred_pc 1: comparison only (why the limit is not an in-flight shutdown)
  W1p_s10  as W1p with SIG_A 0.10 (measurement-scatter sensitivity)
  W1p_tot  as W1p with truth k = a x 1.149 (Combustion's total-flux-law factor: the case where a_meas is NOT taken at the
           station of largest local regression)
Parts (GNC_WEB_PARTS, default check,mc,eval,records):
  check    W-1 flight identity web_on 1 / act 0 against web_on 0 (all non-web results, 20 runs); W-2 truth web against an
           independent numpy integration of the 1 ms record of the oxidiser flow; W-3 FSW web against a numpy integration of the
           1 ms record of the Pc-implied thrust through the map; W-4 bpred_pc 0 identical to v2.8-dev amendment M (part A of
           m2_bitcheck_v28 covers web_on 0)
  mc       the cases (GNC_WEB_SPLIT k/n)
  eval     web_limit.json: P (paired exact McNemar), web statistics, t_L phase, truth web at t_L and at touchdown, by-region
           tables, RG-10 apex statistics, fuel / O/F against the 85 m sizing populations
  records  re-fly the selected W1p runs with the 10 ms recorder: DC-B1_hop_62m_band_{fuelmax,fuelp99,ofmax,ofp99,higha_max,
           webmin}_v3.1.csv in the duty-cycle v3 format + duty_cycles_records_b1_62m_band_v3.1.json
Env: GNC_IFACE, GNC_ACT_RATE, GNC_WEB_OUT (default out/web_limit), GNC_WEB_PARTS, GNC_WEB_SPLIT, GNC_WEB_CASES."""
import csv
import hashlib
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_WEB_OUT", f"{S}/web_limit")
os.environ.setdefault("GNC_DC_OUT", os.path.join(OUT, "records"))
os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
from gncsim.propulsion import _bilin  # noqa: E402
from gncsim.vehicle import grain_port  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_regband_mc as RBM  # noqa: E402
import m2_duty_cycles_v3 as DC3  # noqa: E402
import m2_duty_cycles_disp as DD  # noqa: E402

VERSION = "m2_web_limit v1"
PARTS = os.environ.get("GNC_WEB_PARTS", "check,mc,eval,records").split(",")
SPLIT = os.environ.get("GNC_WEB_SPLIT", "0/1")
BASE = "rbl_B1_lead62_pc_k2"
N = 500
SEED = 101
RNG_MEAS = 20261025           # own generator: per-run measurement draws (a_meas, n_meas, flow calibration)
SIG_A = 0.05                  # ASSUMED relative 1-sigma of measured a (T1-T4 scatter unknown)
SIG_N = 0.03                  # ASSUMED 1-sigma of measured n
DN = 0.05                     # ASSUMED half-width of the measured-n band used by the FSW (both ends evaluated)
SIG_CAL = 0.015               # ASSUMED static-fire oxidiser-flow calibration residual (as m2_mass_est_v2 SIG_CAL_FLOW)
K_QS = 1.016                  # DERIVED Combustion burn_limit_proxy_v2p4 verification: k_quasi_steady_range max
K_TOT = 1.149                 # DERIVED Combustion burn_limit_proxy_v2p4 summary: k_total_law_range max
G_HAT = 0.09                  # DESIGN FSW growth model end value (as m2_mass_est_v2 G_HAT)
GATE_A, GATE_N = 1.25, 0.40   # REQ lead rule 2026-10-13: grain change if a >= 1.25 x nominal with n <= 0.4
REF_CSV = os.path.join(RBM.OUT, f"mc6_runs_{BASE}_rb.csv")
V3_INDEX = f"{S}/duty_cycles_v3/duty_cycles_index_v3.json"
CASES = {
    "W0": dict(web_act=0, bpred_pc=0, sig_a=SIG_A, kqs=K_QS, note="burn-limit monitor only, B predictor on the true thrust (v2.7)"),
    "W0p": dict(web_act=0, bpred_pc=1, sig_a=SIG_A, kqs=K_QS, note="monitor, B predictor on the Pc-implied thrust (RG-10)"),
    "W1p": dict(web_act=1, bpred_pc=1, sig_a=SIG_A, kqs=K_QS, note="DEFINED ACTION + RG-10 predictor (proposed baseline)"),
    "W2p": dict(web_act=2, bpred_pc=1, sig_a=SIG_A, kqs=K_QS, note="shutdown at t_L + RG-10 predictor (comparison only)"),
    "W1p_s10": dict(web_act=1, bpred_pc=1, sig_a=0.10, kqs=K_QS, note="as W1p, measured-a scatter 10 %"),
    "W1p_tot": dict(web_act=1, bpred_pc=1, sig_a=SIG_A, kqs=K_TOT, note="as W1p, truth k = a x 1.149 (total-flux-law factor)"),
}
WEB_KEYS = ("web_t_end", "web_t_t1", "web_t_t0", "web_f_end", "web_tL", "web_tL_phase", "web_tL_h", "web_t_at_tL", "web_acted")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def base_cfg():
    over, comp, note = RBM.cases(None)[BASE]
    over = dict(over)
    m = over.pop("m_fixed")
    return R.cfg_of(**dict(over, m_n2o=float(m))), over, float(m), note


def meas_draws(n):
    rg = np.random.default_rng(RNG_MEAS)
    return rg.standard_normal((n, 3))


def web_over(dr, z, spec, jref):
    a, n = float(dr["reg_a"]), float(dr["reg_n"])
    am = a * (1.0 + spec["sig_a"] * z[0])
    nm = n + SIG_N * z[1]
    return dict(web_on=1, web_kt=a * spec["kqs"], web_nt=n, web_kf=1.1 * am, web_nf1=nm - DN, web_nf2=nm + DN,
                web_kcal=(1.0 / float(dr["isp_scale"])) * (1.0 + SIG_CAL * z[2]), web_ghat=G_HAT, web_jref=jref,
                web_act=spec["web_act"], bpred_pc=spec["bpred_pc"]), am, nm


def fly_case(spec, cfg, D, Z, nrun=N, rec_dt=None, nrec=10, runs=None):
    jref = float(cfg.get("throat_jref") or 0.0)
    out = []
    for i in (range(nrun) if runs is None else runs):
        c, disp = R.run_cfg(cfg, D[i])
        wo, am, nm = web_over(D[i], Z[i], spec, jref)
        c = dict(c, **wo)
        if rec_dt is not None:
            c["rec_dt"] = rec_dt
        res, rec, info = R.fly(c, disp, nrec=nrec)
        out.append((i, res, rec, info, am, nm))
    return out


def row_of(i, dr, res, am, nm, cfg):
    r = R.flat_row(i, dr, res, R.success(res), cfg)
    r["a_meas"] = am
    r["n_meas"] = nm
    r["gated_out"] = int(am >= GATE_A and nm <= GATE_N)
    return r


def part_check():
    """W-1 .. W-3 (W-4: m2_bitcheck_v28 part A covers web_on 0)."""
    cfg, over, m, _ = base_cfg()
    D = R.draw(np.random.default_rng(SEED), N, cfg)
    Z = meas_draws(N)
    out = {}
    # W-1: web_on 1 / act 0 / bpred_pc 0 must not change the flight
    mism = []
    for i in range(20):
        c, disp = R.run_cfg(cfg, D[i])
        r0 = R.fly(c, disp, nrec=10)[0]
        wo, _, _ = web_over(D[i], Z[i], CASES["W0"], float(cfg.get("throat_jref") or 0.0))
        r1 = R.fly(dict(c, **wo), disp, nrec=10)[0]
        mm = [k for k in s6.RES_NAMES if k not in WEB_KEYS and not (r0[k] == r1[k] or (np.isnan(r0[k]) and np.isnan(r1[k])))]
        if mm:
            mism.append(dict(run=i, fields=mm[:6]))
    out["W1_flight_identity_act0"] = dict(runs=20, mismatches=mism, passed=not mism)
    # W-2 / W-3: numpy twins on the 1 ms record of 3 runs (one high-a run included)
    hi = [j for j in range(2, N) if float(D[j]["reg_a"]) > 1.35][:1]
    picks = [0, 1] + hi
    tw = []
    par_cache = {}
    for i in picks:
        c, disp = R.run_cfg(cfg, D[i])
        wo, am, nm = web_over(D[i], Z[i], CASES["W0"], float(cfg.get("throat_jref") or 0.0))
        c = dict(c, **wo, rec_dt=1e-3)
        res, rec, info = R.fly(c, disp, nrec=40000)
        par, apar, comp, mp, tab, info2 = R.build(c, disp)
        par_cache[i] = par
        I = {n_: k for k, n_ in enumerate(s6.REC_NAMES)}
        t = rec[:, I["t"]]
        mox = rec[:, I["mox"]]
        dt = float(par[s6.P_dt])
        Dt = float(par[s6.P_web_D0]); Do = float(par[s6.P_web_Do])
        wt = np.zeros(len(t))
        for k in range(len(t)):
            if mox[k] > 0.0:
                G = 4.0 * mox[k] / (np.pi * Dt * Dt)
                Dt = min(Do, Dt + 2.0 * par[s6.P_web_kt] * 1.0e-3 * (G / 300.0) ** par[s6.P_web_nt] * dt)
            wt[k] = 0.5 * (Do - Dt)
        d_t = float(np.max(np.abs(wt - rec[:, I["wt"]])))
        # FSW twin: Pc-implied thrust (record Fpc) through the oxidiser map at the port of the recorded fuel mass (1 step lag
        # allowed: the record's fuel mass is the end-of-step value, the map uses the start-of-step port)
        Fpc = rec[:, I["Fpc"]]
        mfu = rec[:, I["mfuel"]]
        D1 = D2 = float(par[s6.P_web_D0]); J = 0.0
        wf = np.zeros(len(t))
        for k in range(len(t)):
            if Fpc[k] > 0.0:
                J += (Fpc[k] / par[s6.P_Fmax]) ** 0.68 * dt
                gw = par[s6.P_web_ghat] * min(1.0, J / par[s6.P_web_jref]) if par[s6.P_web_jref] > 0 else 0.0
                mfp = mfu[k - 1] if k > 0 else par[s6.P_m_fuel0]
                Dp = grain_port(mp, mfp)
                q = _bilin(tab["Fg"], tab["Dg"], tab["mox"], Fpc[k], Dp) * par[s6.P_web_kcal] * (1.0 + gw)
                if q > 0.0:
                    D1 = min(Do, D1 + 2.0 * par[s6.P_web_kf] * 1.0e-3 * (4.0 * q / (np.pi * D1 * D1) / 300.0) ** par[s6.P_web_nf1] * dt)
                    D2 = min(Do, D2 + 2.0 * par[s6.P_web_kf] * 1.0e-3 * (4.0 * q / (np.pi * D2 * D2) / 300.0) ** par[s6.P_web_nf2] * dt)
            wf[k] = 0.5 * (Do - max(D1, D2))
        d_f = float(np.max(np.abs(wf - rec[:, I["wf"]])))
        tw.append(dict(run=i, reg_a=float(D[i]["reg_a"]), reg_n=float(D[i]["reg_n"]), steps=len(t), truth_max_abs_diff_m=d_t,
                       fsw_max_abs_diff_m=d_f, truth_web_end_mm=1e3 * float(res["web_t_end"]),
                       fsw_web_end_mm=1e3 * float(res["web_f_end"]), tL=float(res["web_tL"]),
                       passed=bool(d_t < 1e-9 and d_f < 2e-6)))
    out["W2_W3_numpy_twins"] = dict(runs=tw, passed=all(x["passed"] for x in tw),
                                    tolerance=dict(truth_m=1e-9, fsw_m=2e-6, note="FSW: map port from the recorded fuel "
                                                   "mass of the previous step (exact replay not possible from the record)"))
    out["passed"] = bool(out["W1_flight_identity_act0"]["passed"] and out["W2_W3_numpy_twins"]["passed"])
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "web_check.json"), "w") as f:
        json.dump(dict(version=VERSION, sim=s6.SIM6_VERSION, **out), f, indent=1, default=float)
    print("check:", json.dumps({k: (v.get("passed") if isinstance(v, dict) else v) for k, v in out.items()}), flush=True)
    for x in tw:
        print("   ", x, flush=True)
    return out


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    cfg, over, m, note = base_cfg()
    D = R.draw(np.random.default_rng(SEED), N, cfg)
    Z = meas_draws(N)
    k, n = (int(x) for x in SPLIT.split("/"))
    sel = os.environ.get("GNC_WEB_CASES")
    names = [c for c in CASES if (not sel or c in sel.split(","))][k::n]
    for name in names:
        p = os.path.join(OUT, f"web_{name}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_WEB_FORCE") != "1":
            print("exists", name, flush=True)
            continue
        t0 = time.time()
        rows = [row_of(i, D[i], res, am, nm, cfg) for (i, res, rec, info, am, nm) in fly_case(CASES[name], cfg, D, Z)]
        M.write_csv(p, rows)
        ok = np.array([r["ok"] for r in rows]) > 0.5
        tl = np.array([r["web_tL"] for r in rows])
        w0 = np.array([r["web_t_t0"] for r in rows])
        print(f"{name:8s}: P {ok.mean():.3f}  t_L reached {int(np.sum(tl >= 0))}  truth burn-through {int(np.sum(w0 >= 0))}  "
              f"truth w<1mm {int(np.sum(np.array([r['web_t_t1'] for r in rows]) >= 0))} ({time.time() - t0:.0f} s)", flush=True)


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def mcnemar(a, b):
    from scipy.stats import binomtest
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    return dict(P_ref=float(a.mean()), P_case=float(b.mean()), lost=lost, gained=gained,
                p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0, n=int(len(a)))


def pct(x, qs=(1, 50, 99)):
    x = np.asarray(x, float)
    if x.size == 0:
        return None
    return dict({f"p{q:02d}": float(np.percentile(x, q)) for q in qs}, min=float(x.min()), max=float(x.max()), n=int(x.size))


def wilson(k, n):
    lo, hi = R.wilson(k, n)
    return [float(lo), float(hi)]


def fuel_of(rows, m_fuel0):
    fb = m_fuel0 - col(rows, "fuel_left")
    ox = col(rows, "prop_used") - fb
    return fb, ox, ox / np.maximum(fb, 1e-9)


def case_stats(rows, m_fuel0, mask=None):
    ok = col(rows, "ok") > 0.5
    keep = np.ones(len(rows), bool) if mask is None else mask
    t0w = col(rows, "web_t_t0")
    t1w = col(rows, "web_t_t1")
    tL = col(rows, "web_tL")
    wend = col(rows, "web_t_end")
    td = col(rows, "td_t")
    bt = col(rows, "burn_time")
    burn = t0w >= 0.0
    v1 = t1w >= 0.0
    hit = tL >= 0.0
    okw = ok & ~burn
    k = keep
    fb, ox, of = fuel_of(rows, m_fuel0)
    ph = col(rows, "web_tL_phase")
    d = dict(n=int(k.sum()), P_landing=float(ok[k].mean()), P_landing_wilson=wilson(int(ok[k].sum()), int(k.sum())),
             P_landing_and_no_burnthrough=float(okw[k].mean()),
             P_landing_and_no_burnthrough_wilson=wilson(int(okw[k].sum()), int(k.sum())),
             truth_burnthrough_runs=int((burn & k).sum()), truth_web_below_1mm_runs=int((v1 & k).sum()),
             truth_web_below_1mm_wilson=wilson(int((v1 & k).sum()), int(k.sum())),
             limit_reached_runs=int((hit & k).sum()), limit_reached_wilson=wilson(int((hit & k).sum()), int(k.sum())),
             limit_phase_counts={str(int(p)): int(np.sum((ph == p) & hit & k)) for p in np.unique(ph[hit & k])},
             truth_web_end_mm=pct(1e3 * wend[k]),
             truth_web_end_mm_landed_ok=pct(1e3 * wend[k & ok]),
             fsw_web_end_mm=pct(1e3 * col(rows, "web_f_end")[k]),
             truth_web_at_tL_mm=pct(1e3 * col(rows, "web_t_at_tL")[hit & k]),
             height_at_tL_m=pct(col(rows, "web_tL_h")[hit & k]),
             time_tL_to_touchdown_s=pct((td - tL)[hit & k & (td > 0)]),
             tL_s=pct(tL[hit & k]),
             burn_time_s=pct(bt[k]), h_max_m=pct(col(rows, "h_max")[k]),
             fuel_burned_kg=pct(fb[k]), mean_OF=pct(of[k]),
             truth_w1_minus_touchdown_s=pct((t1w - td)[v1 & k]),
             runs_limit_not_reached_but_truth_below_1mm=int(np.sum(v1 & ~hit & k)),
             runs_truth_below_1mm_before_tL=int(np.sum(v1 & hit & (t1w < tL) & k)))
    return d


def regions(rows):
    a, n = col(rows, "reg_a"), col(rows, "reg_n")
    ok = col(rows, "ok") > 0.5
    v1 = col(rows, "web_t_t1") >= 0
    hit = col(rows, "web_tL") >= 0
    burn = col(rows, "web_t_t0") >= 0
    out = []
    for al, ah in ((0.6, 0.9), (0.9, 1.2), (1.2, 1.5001)):
        for nl, nh in ((0.35, 0.46), (0.46, 0.57), (0.57, 0.6801)):
            m = (a >= al) & (a < ah) & (n >= nl) & (n < nh)
            if m.sum() == 0:
                continue
            out.append(dict(a=[al, min(ah, 1.5)], n=[nl, min(nh, 0.68)], runs=int(m.sum()), P=float(ok[m].mean()),
                            P_wilson=wilson(int(ok[m].sum()), int(m.sum())), limit_reached=int((hit & m).sum()),
                            truth_below_1mm=int((v1 & m).sum()), truth_burnthrough=int((burn & m).sum()),
                            truth_web_end_min_mm=float(1e3 * col(rows, "web_t_end")[m].min())))
    return out


def part_eval():
    cfg, over, m, note = base_cfg()
    m_fuel0 = None
    par = R.build(cfg)[0]
    m_fuel0 = float(par[s6.P_m_fuel0])
    ref = rows_csv(REF_CSV)
    C = {k: rows_csv(os.path.join(OUT, f"web_{k}.csv")) for k in CASES}
    C = {k: v for k, v in C.items() if v}
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, base=BASE, base_note=note, n_runs=N, seed=SEED,
               measurement=dict(seed=RNG_MEAS, sig_a_rel=SIG_A, sig_n=SIG_N, n_band_half_width=DN, flow_cal_sig=SIG_CAL,
                                growth_model=G_HAT, tags="ASSUMED (T1-T4 scatter unknown)"),
               law=dict(source="Combustion law_for_gnc, /home/claude/work/combustion/data/v2/v2p4/burn_limit_proxy_v2p4.json "
                               "(workdir; hub publication pending)",
                        sha256_16=sha16("/home/claude/work/combustion/data/v2/v2p4/burn_limit_proxy_v2p4.json"),
                        truth_k=f"a x {K_QS} (W1p_tot: a x {K_TOT})", fsw_k="1.1 x a_meas", fsw_n=f"n_meas -/+ {DN}",
                        limit_web_m=0.001, tags="DERIVED proxy of SIM grain_q1d v2.4; ASSUMED until T1-T4"),
               gating=dict(rule=f"grain change if a_meas >= {GATE_A} and n_meas <= {GATE_N} (lead 2026-10-13)"),
               reference_csv=dict(path=REF_CSV, sha256_16=sha16(REF_CSV)), cases={})
    okr = col(ref, "ok") > 0.5
    for k, rows in C.items():
        ok = col(rows, "ok") > 0.5
        gate = col(rows, "gated_out") < 0.5
        e = dict(note=CASES[k]["note"], spec={kk: vv for kk, vv in CASES[k].items() if kk != "note"},
                 vs_stored_rbl=mcnemar(okr, ok),
                 full_band=case_stats(rows, m_fuel0), gated=case_stats(rows, m_fuel0, gate),
                 gated_out_runs=int((~gate).sum()), regions=regions(rows))
        if k == "W0":
            same = [kk for kk in s6.RES_NAMES if kk in ref[0] and kk not in WEB_KEYS and kk != "nrec" and
                    not np.array_equal(col(ref, kk), col(rows, kk), equal_nan=True)]
            e["identical_to_stored_rbl_fields_differing"] = same
        if k != "W0" and "W0" in C:
            e["vs_W0"] = mcnemar(col(C["W0"], "ok") > 0.5, ok)
            e["vs_W0_gated"] = mcnemar((col(C["W0"], "ok") > 0.5)[gate], ok[gate])
        if k not in ("W0", "W0p") and "W0p" in C:
            e["vs_W0p"] = mcnemar(col(C["W0p"], "ok") > 0.5, ok)
        out["cases"][k] = e
    if "W0" in C and "W0p" in C:
        h0, h1 = col(C["W0"], "h_max"), col(C["W0p"], "h_max")
        dh = h1 - h0
        out["RG10_apex"] = dict(W0=pct(h0, (50, 99)), W0p=pct(h1, (50, 99)),
                                shift_m=dict(mean=float(dh.mean()), sd=float(dh.std(ddof=1)), min=float(dh.min()), max=float(dh.max())),
                                P=mcnemar(col(C["W0"], "ok") > 0.5, col(C["W0p"], "ok") > 0.5),
                                t_boost_end_s=dict(W0=pct(col(C["W0"], "t_meco"), (50, 99)), W0p=pct(col(C["W0p"], "t_meco"), (50, 99))),
                                note="reviewer rg13 (scratch copy): P 0.996 -> 0.994, apex p99 66.10 -> 68.99 m, max 67.48 -> "
                                     "69.96 m, mean shift +0.44 m")
    # fuel / O/F against the 85 m sizing populations (RG-03 item 1)
    s85 = {}
    for c85 in ("tg_B1_none_k2", "tg_B1_pc_k2"):
        p = RBM.TG_CSV.get(c85)
        r85 = rows_csv(p) if p else None
        if r85:
            fb, ox, of = fuel_of(r85, m_fuel0)
            s85[c85] = dict(csv=p, fuel_burned_kg=pct(fb, (99,)), mean_OF=pct(of, (99,)), burn_time_s=pct(col(r85, "burn_time"), (99,)))
    out["sizing_85m_populations"] = s85
    with open(os.path.join(OUT, "web_limit.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for k, e in out["cases"].items():
        fb_, gt_ = e["full_band"], e["gated"]
        print(f"{k:8s} P {fb_['P_landing']:.3f} (gated {gt_['P_landing']:.3f}, n {gt_['n']}) vs stored {e['vs_stored_rbl']['lost']}/"
              f"{e['vs_stored_rbl']['gained']} | limit {fb_['limit_reached_runs']} (gated {gt_['limit_reached_runs']}) phases "
              f"{fb_['limit_phase_counts']} | truth <1mm {fb_['truth_web_below_1mm_runs']} (gated {gt_['truth_web_below_1mm_runs']}) "
              f"burn-through {fb_['truth_burnthrough_runs']} (gated {gt_['truth_burnthrough_runs']}) | web end p01 "
              f"{fb_['truth_web_end_mm']['p01']:.2f} mm min {fb_['truth_web_end_mm']['min']:.2f}", flush=True)
    if "RG10_apex" in out:
        print("RG-10:", json.dumps(out["RG10_apex"], default=float)[:600], flush=True)
    print("85 m sizing:", json.dumps(s85, default=float)[:600], flush=True)


SEL = [("DC-B1_hop_62m_band_fuelmax_v3.1", "fuel", "max"), ("DC-B1_hop_62m_band_fuelp99_v3.1", "fuel", "p99"),
       ("DC-B1_hop_62m_band_ofmax_v3.1", "of", "max"), ("DC-B1_hop_62m_band_ofp99_v3.1", "of", "p99"),
       ("DC-B1_hop_62m_band_higha_max_v3.1", "higha", "max"), ("DC-B1_hop_62m_band_webmin_v3.1", "webmin", "min")]


def pick_runs(rows, m_fuel0):
    fb, ox, of = fuel_of(rows, m_fuel0)
    a = col(rows, "reg_a")
    bt = col(rows, "burn_time")
    w = col(rows, "web_t_end")
    out = {}
    for name, var, rule in SEL:
        if var == "higha":
            cand = np.where(a >= 1.2)[0]
            i = int(cand[np.argmax(bt[cand])])
            val = float(bt[i])
        elif var == "webmin":
            i = int(np.argmin(w))
            val = float(w[i])
        else:
            x = fb if var == "fuel" else of
            if rule == "max":
                i = int(np.argmax(x))
            else:
                p = np.percentile(x, 99)
                cand = [j for j in range(len(x)) if x[j] >= p]
                i = min(cand, key=lambda j: x[j])
            val = float(x[i])
        out[name] = (i, var, rule, val)
    return out


def part_records():
    cfg, over, m, note = base_cfg()
    par = R.build(cfg)[0]
    m_fuel0 = float(par[s6.P_m_fuel0])
    rows = rows_csv(os.path.join(OUT, "web_W1p.csv"))
    D = R.draw(np.random.default_rng(SEED), N, cfg)
    Z = meas_draws(N)
    picks = pick_runs(rows, m_fuel0)
    fb, ox, of = fuel_of(rows, m_fuel0)
    os.makedirs(DC3.OUT, exist_ok=True)
    recs = []
    I = DD.I
    for name, (i, var, rule, val) in picks.items():
        (j, res, rec, info, am, nm), = fly_case(CASES["W1p"], cfg, D, Z, rec_dt=0.01, nrec=8000, runs=[i])
        mrow = rows[i]
        mm = [k for k in s6.RES_NAMES if k in mrow and k != "nrec" and not (float(mrow[k]) == float(res[k]) or
                                                                         (np.isnan(float(mrow[k])) and np.isnan(float(res[k]))))]
        rws = DD.rows_of(rec, info)
        t = rec[:, I["t"]]; F = rec[:, I["F"]]
        mox, mf = rec[:, I["mox"]], rec[:, I["mf"]]
        n2o = float(np.sum(0.5 * (mox[1:] + mox[:-1]) * np.diff(t)))
        fuel = float(np.sum(0.5 * (mf[1:] + mf[:-1]) * np.diff(t)))
        on = (F > 1.0) & (mf > 0)
        ofr = mox[on] / mf[on]
        wt, wf = rec[:, I["wt"]], rec[:, I["wf"]]
        meta = dict(name=name, kind="record_b1_62m_band", generator=VERSION,
                    source=f"SIM {s6.SIM6_VERSION} 6-DOF, engine: {info['tags']['engine_model'][1]}, dt 1 ms, recorded 10 ms; "
                           f"Monte Carlo run {i} of case W1p (base {BASE}) re-flown",
                    purpose="RECORD (review RG-03 item 2): B1 62 m with the regression band, the burn limit and the RG-10 "
                            "predictor; selected by " + {"fuel": "fuel burned", "of": "mean O/F", "higha": "thrust-on time among a >= 1.2",
                                                          "webmin": "smallest truth web at the end"}[var] + f" ({rule}); NOT a sizing case",
                    selection=dict(variable=var, rule=rule, value=val, n_runs=len(rows),
                                   population_p99_max=dict(fuel_kg=[float(np.percentile(fb, 99)), float(fb.max())],
                                                           OF=[float(np.percentile(of, 99)), float(of.max())])),
                    mc_case="W1p", run_index=i, run_seed=int(D[i]["_seed"]), reproduces_mc_row=not mm, mismatched_fields=mm[:10],
                    regression=dict(a=float(D[i]["reg_a"]), n=float(D[i]["reg_n"]), a_meas=am, n_meas=nm,
                                    gated_out_by_lead_rule=bool(am >= GATE_A and nm <= GATE_N)),
                    dispersions={k: (float(D[i][k]) if D[i].get(k) is not None else None) for k in
                                 ("thrust_scale", "isp_scale", "dry_scale", "m_est_err", "_wind", "_wind_dir", "_gust_scale",
                                  "_T0", "_rho0", "_t_ign", "_k_retro", "_ca_tf", "throat_g")},
                    summary={k: float(res[k]) for k in ["landed", "td_vz", "td_vh", "td_tilt", "td_rate", "prop_used", "liq_left",
                                                        "h_max", "burn_time", "max_gim", "max_hinge", "throat_g_end", "throat_J",
                                                        "fuel_left"] + list(WEB_KEYS)},
                    success=R.success(res), burn_time_s=DC3.burn_of(t, F)[0], engine_on_counter_s=float(res["burn_time"]),
                    total_impulse_Ns=float(np.trapezoid(F, t)), n2o_burned_kg=n2o, fuel_burned_kg=fuel,
                    OF_overall=n2o / fuel if fuel > 0 else None,
                    OF_range_burning=[float(ofr.min()), float(ofr.max())] if ofr.size else None,
                    web_truth_end_mm=1e3 * float(wt[-1]), web_fsw_end_mm=1e3 * float(wf[-1]),
                    web_truth_min_mm=1e3 * float(np.min(wt)), burn_limit_t_L_s=float(res["web_tL"]),
                    Pc_max_Pa=float(np.max(rws[:, 6])), wind_mps_at_10m=float(D[i]["_wind"]),
                    note="web columns are not in the v3 file format: the truth and FSW web histories are in "
                         f"{name}_web.csv (t_s, web_truth_m, web_fsw_m)")
        meta.update(DC3.axial_stats(rws, rec[:, I["legF"]]))
        meta = DC3.write(name, rws, meta)
        meta["file"] = "01-systems-gnc/staging_v3.1/duty_cycles/" + name + ".csv"
        pw = os.path.join(DC3.OUT, name + "_web.csv")
        with open(pw, "w", newline="") as f:
            w_ = csv.writer(f)
            w_.writerow(["t_s", "web_truth_m", "web_fsw_m"])
            for k in range(len(t)):
                w_.writerow(["%.6g" % t[k], "%.6g" % wt[k], "%.6g" % wf[k]])
        meta["web_file"] = "01-systems-gnc/staging_v3.1/duty_cycles/" + name + "_web.csv"
        meta["web_file_sha256"] = DC3.sha(pw)
        recs.append(meta)
        print(f"{name:36s} run {i:3d} {var} {rule} {val:.4g} | a {D[i]['reg_a']:.3f} n {D[i]['reg_n']:.3f} thrust-on "
              f"{meta['burn_time_s']:.2f} s fuel {fuel:.3f} kg O/F {meta['OF_overall']:.2f} web end {meta['web_truth_end_mm']:.2f} mm "
              f"t_L {res['web_tL']:.2f} ok {meta['success']} reproduces {meta['reproduces_mc_row']}", flush=True)
    idx = dict(version="duty_cycles v3 records (B1 62 m regression band)", status="v3.1 STAGING", date="2026-10-13",
               owner="Space/GNC", generator=VERSION, sim=s6.SIM6_VERSION, interface_set=R.IFACE,
               request="review REV-GNC-1 RG-03 item 2: band records selected by fuel burned and by O/F, plus the high-a runs "
                       "with the longest burns",
               units=json.load(open(V3_INDEX))["units"] if os.path.exists(V3_INDEX) else None,
               columns=DC3.COLS, burn_time_definition=DC3.BURN_DEF, max_axial_definition=DC3.AX_DEF, records=recs,
               note="records, not sizing cases; the selection population is W1p (500 runs: band + growth + burn limit + RG-10 "
                    "predictor); the a / n draws are epistemic per engine (RG-04): these records span the band, they are not "
                    "a probability statement about one engine")
    p = os.path.join(DC3.OUT, "duty_cycles_records_b1_62m_band_v3.1.json")
    with open(p, "w") as f:
        json.dump(idx, f, indent=1, default=float)
    print("wrote", p, flush=True)


def main():
    if "check" in PARTS:
        part_check()
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()
    if "records" in PARTS:
        part_records()


if __name__ == "__main__":
    main()
