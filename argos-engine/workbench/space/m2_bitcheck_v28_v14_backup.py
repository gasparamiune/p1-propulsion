"""m2_bitcheck_v28 v1.4 (GNC, 2026-10-13; v1.4: part R, sim6 amendment R; first X2 run failed on a one-step record-stamp offset in the test, kept in
out/v28_checks_FP/bitcheck_FP_xp_run1.log; the expectation was corrected, the sim was not changed): checks of sim6/run6 v2.8-dev (ENG-03 state-dependent thrust-rate map, servo latency and
servo stage, rate-aware feed-forward; all off by default).
A  options off vs stored sim6 v2.7.1-dev Monte Carlo runs: v28_liq_p0.81_A1_none_k2, v28_liq_p0.81_A1J_pc_k2 (relight_v28) and
   rbl_B1_lead62_pc_k2 (regband): first K runs + every failed run, every stored result field compared exactly
B  T-RM1: map ON with every rate 1e9 N/s, capped (rmap_cap 1), closing from the map: the limits equal slew x F_max exactly, so
   the runs must equal the stored ones (plumbing identity)
C  T-RM2: the sim6 lookup (_rmap) against its numpy twin at 4000 random points, 30 % of them outside the grid (clamping)
D  T-RM3: nominal A1 and B1 flights (no dispersion, 1 ms recorder) with the Electronics map ON, capped / closing 2500 (R1) and
   uncapped both ways (R3): the delivered thrust rate never exceeds the map rate at the recorded (tank pressure, thrust) state
   (tolerance: one step of the lookup change) and the opening limit binds somewhere
E  T-LAT: servo latency 4 ms on the nominal B1 flight: delivered thrust during the pad hold equals the no-latency thrust shifted
   by 4 ms
F  T-DRV: Electronics drive model B (R2 arm) on the nominal B1 flight: the recorded drive state Fdrv equals a numpy twin of
   model B driven by the recorded target Ftg, tank pressure and thrust scale (map limits, tau_p, tau_v)
v1.1 (sim6 v2.8-dev amendment M: flown mass estimator, Pc-lost rule, lever-arm / direction compensation; A-F re-run on it):
G  T-MEST: mest_mode 1 on dispersed A1 and B1 flights (m2_fc_thrust v1.1 configurations, no throat growth, no regression band) with
   isp_scale 1 and m_est_err 0: (G1) every error source zero -> the recorded estimate error mhe (against the exact truth mass)
   stays below 1e-9 and the flight outcome equals the mest_mode 0 outcome (touchdown differences reported: mode 0 guides on the
   10 ms tank-solve mass); (G2) weighing error w only -> mhe = w / m; (G3) calibration
   factor k only -> mhe = -(k - 1) (m0 - m) / m; (G4) flow offset dq only -> mhe = -dq t_burn / m; (G5) start errors s1, s2 only ->
   mhe = (s1 [+ s2 after the second start]) / m (evaluated on the 1 ms record against the exact truth mass mex; tolerance 1e-5
   relative plus one recorder step of timing; G1 tolerance 1e-9)
H  T-KCOMP: kest_comp 1 on 40 A1 healthy flights: the median over runs of the per-run median of k_hat / ((1 + m_est_err)
   thrust_scale (1 + a_sf)) - 1 in the landing-burn window moves from about -1.3 % (m2_khat_offset v1.1) to within +/- 0.5 %
v1.2 (sim6 v2.8-dev amendment W: fuel-web state, burn limit and action, B predictor on Pc; A, G, H re-run on it):
W  T-WEB (m2_web_limit part check): W-1 web_on 1 with action 0 and bpred_pc 0 leaves every non-web result of 20 B1 band flights
   unchanged; W-2 truth web equals a numpy integration of the 1 ms record of the oxidiser flow (1e-9 m); W-3 FSW web equals a
   numpy integration of the 1 ms record of the Pc-implied thrust through the oxidiser map (2e-6 m: map port from the previous
   step's recorded fuel mass). Part A (options off) covers web_on 0 and bpred_pc 0.
v1.3 (sim6 v2.8-dev amendments F: stuck-pintle fault, in-loop detectors and abort; P: A-relight forced purge and stuck-open
bleed; part A covers flt_on 0, prg_on 0 and blf_on 0; every other part re-run on the F + P code):
X  T-FAULT (amendment F): X1 flt_on 1 with the onset never reached and the flight detectors armed (geofence off): no decision and
   every non-fault result equal to flt_on 0 on 20 dispersed flights per profile (geofence trips reported, not acted on); X2 Pc
   valid, linkage failure (enc 0), FC_THRUST off, stuck 670 N from 0.5 s on the nominal B1 and A1 flights (1 ms record): the
   over-pressure trip is the decision (source 2) and comes exactly det_op_t - 2 dt after the first recorded Pc-equivalent thrust
   above det_op_F (the record stamp is the end of the step, t += dt precedes the record, and the persistence counter includes the
   first step: 3 consecutive 1 ms samples); X3 abort sequencing on the X2 flights: MV commanded abt_lat after the decision and
   seated abt_seat later (one step), tail-off impulse after the seat = abt_imp (2 %); X4 Pc lost, encoder sees the jam,
   FC_THRUST off: the decision is PINTLE_FAULT (source 3) exactly det_pf_t - dt after the first recorded |F / tsc - Fcmd| >
   det_pf_dF (elapsed-time path from the first deviating step; same record stamp); X5 linkage failure from the
   A1 ascent with every detector off: the normal shutdown seats the MV abt_sdenc + abt_seat after the shutdown (one step), no
   lockout, the fault re-activates at the relight (2 activations)
P  T-PURGE (amendment P): P1 prg_on 1 with no purge flow, no jet and no booking: every non-P result equal to prg_on 0 on 20
   dispersed A1 flights; P2 defaults on the same flights: purge mass = prg_mdot x duration (one step), no lift wait (prg_prio 1),
   duration > 0; P3 nominal A1, 1 ms record: the exact truth mass falls by prg_mdot x duration across the purge (no engine flow;
   two steps); P4 nominal A1, flown estimator with every error source zero: booking at the true flow keeps |mhe| < 1e-9 through
   the purge, no booking leaves mhe = prg_mass / m after it (1e-6); P5 nominal B1, stuck bleed from ignition, additive bracket,
   jet 105.8 m/s at azimuth 0 vs no jet: in the floor phase the mean gimbal angle about the jet axis moves by -F_jet / F (rad)
   within 20 %, the other axis by less than 20 % of it
v1.4 (sim6 v2.8-dev amendment R: drogue release rule; part A covers rel_mode 0):
R  T-REL: R1 rel_mode 1 with the release pressure set to the map Pc at 0.5 x the floor thrust and rel_dt 0: every non-R result
   equal to rel_mode 0 on 20 dispersed A1 flights (plumbing identity: the two rules then release at the same step); R2 nominal
   A1, rel_mode 1 (3.0 bar abs, rel_dt 0), 1 ms record: the release comes at the first recorded Pc-equivalent thrust >= rel_F
   after the light (one step), rel_Fpc >= rel_F; R3 the same with rel_dt 0.2 s: the release waits for the E2 gate (rel_t within
   one step of 0.2 s); R4 rel_F = the map thrust at 3.0 bar abs (np.interp on the run6 table) and inside (30, 40) N
Env: GNC_IFACE, GNC_ACT_RATE (v3c set), GNC_RES (default out/v28_checks), GNC_BIT_K (8), GNC_BIT_PARTS (A,B,C,D,E,F,G,H,W,X,P,R).
Output: GNC_RES/bitcheck_v28.json"""
import csv
import json
import os
import sys
import numpy as np

os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_eng03_rate as E  # noqa: E402

S = "/home/claude/work/space/out"
RES = os.environ.get("GNC_RES", f"{S}/v28_checks")
K = int(os.environ.get("GNC_BIT_K", "8"))
PARTS = os.environ.get("GNC_BIT_PARTS", "A,B,C,D,E,F,G,H,W,X,P,R").split(",")
N = 500
I = {n: i for i, n in enumerate(s6.REC_NAMES)}


def compare(cfg, rows, label, only_first=False):
    D = R.draw(np.random.default_rng(101), N, cfg)
    idx = list(range(K)) + ([] if only_first else [i for i, r in enumerate(rows) if int(float(r["ok"])) == 0 and i >= K])
    mism, nf = [], 0
    for i in idx:
        res = R.run_one(cfg, D[i])
        for k in rows[i]:
            if k in s6.RES_NAMES:
                nf += 1
                a = float(rows[i][k]); b = float(res[k])
                if not (a == b or (np.isnan(a) and np.isnan(b))):
                    mism.append(dict(run=i, field=k, ref=a, new=b))
    print(f"{label}: runs {len(idx)} values {nf} mismatches {len(mism)} {mism[:3]}", flush=True)
    return dict(runs_checked=len(idx), failed_runs_included=len(idx) - K, values_compared=nf, mismatches=len(mism), first=mism[:10])


def cfg_of_base(base):
    over, bcsv, bjson = E.base_ref(base)
    m = json.load(open(bjson))["m_n2o_mc_kg"]
    return R.cfg_of(**dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(m))), list(csv.DictReader(open(bcsv))), bcsv


def main():
    os.makedirs(RES, exist_ok=True)
    out = dict(tool="m2_bitcheck_v28 v1.4", sim=s6.SIM6_VERSION, iface=os.environ.get("GNC_IFACE"), parts={})
    ok_all = True
    m = E.load_map()
    # A
    A = {}
    for base in (("A1_none", "A1J_pc", "rbl_B1_lead62_pc_k2") if "A" in PARTS else ()):
        cfg, rows, p = cfg_of_base(base)
        A[base] = dict(compare(cfg, rows, f"A {base} (v2.7.1-dev ref)"), reference=p)
        ok_all &= A[base]["mismatches"] == 0
    out["parts"]["A_options_off_vs_v2.7.1-dev"] = A
    # B
    big = dict(m, open_N_per_s=(np.full(np.shape(m["open_N_per_s"]), 1e9)).tolist(),
               close_N_per_s=(np.full(np.shape(m["close_N_per_s"]), 1e9)).tolist())
    Bp = {}
    for base in (("A1_none", "rbl_B1_lead62_pc_k2") if "B" in PARTS else ()):
        cfg, rows, p = cfg_of_base(base)
        cfg = dict(cfg, rate_map=big, rmap_close=1, rmap_cap=1)
        Bp[base] = dict(compare(cfg, rows, f"B T-RM1 {base} (huge capped map)", only_first=True), reference=p)
        ok_all &= Bp[base]["mismatches"] == 0
    out["parts"]["B_T-RM1_capped_huge_map_identity"] = Bp
    # C
    cfg, _, _ = cfg_of_base("A1_none")
    par = R.build(dict(cfg, rate_map=m))[0]
    rng = np.random.default_rng(7)
    Ps, Fs = np.asarray(m["P_tank_Pa"]), np.asarray(m["F_N"])
    err = 0.0
    nout = 0
    for k in range(4000):
        P = rng.uniform(Ps[0] - 0.6e6, Ps[-1] + 0.6e6) if k % 10 < 3 else rng.uniform(Ps[0], Ps[-1])
        F = rng.uniform(0.0, 560.0) if k % 10 < 3 else rng.uniform(Fs[0], Fs[-1])
        nout += int(P < Ps[0] or P > Ps[-1] or F < Fs[0] or F > Fs[-1])
        for which, off in (("open_N_per_s", s6.P_rmap_o0), ("close_N_per_s", s6.P_rmap_c0)):
            a = s6._rmap(par, P, F, off)
            b = E.interp_map(m, P, F, which)
            err = max(err, abs(a - b))
    C = dict(points=4000, outside_grid=nout, max_abs_diff_N_per_s=err, passed=bool(err < 1e-6))
    print("C T-RM2 lookup:", C, flush=True)
    ok_all &= C["passed"]
    out["parts"]["C_T-RM2_lookup"] = C
    # D
    Dd = {}
    for lab, base in (("A1", "A1_none"), ("B1", "rbl_B1_lead62_pc_k2")):
        cfg, _, _ = cfg_of_base(base)
        for arm, ov in (("R1", dict(rate_map=m, rmap_close=0, rmap_cap=1)), ("R3", dict(rate_map=m, rmap_close=1, rmap_cap=0))):
            res, rec, _ = R.fly(dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.001, **ov), nrec=200000)
            n = int(res["nrec"])
            t, F, Pt, ts = rec[:n, I["t"]], rec[:n, I["F"]], rec[:n, I["Ptank"]], rec[:n, I["tsc"]]
            dF = np.diff(F) / np.diff(t)
            ro = np.array([E.interp_map(m, Pt[k], F[k] / ts[k], "open_N_per_s") * ts[k] for k in range(n - 1)])
            rc = np.array([E.interp_map(m, Pt[k], F[k] / ts[k], "close_N_per_s") * ts[k] for k in range(n - 1)])
            if arm == "R1":
                ro = np.minimum(ro, 2500.0)
                rc = np.full_like(rc, 2500.0)
            lit_ = rec[:n, I["Fcmd"]] > 0.0          # sim6 records Fcmd only while lit (start / shutdown transients excluded)
            on = (F[:-1] > 1.0) & (F[1:] > 1.0) & lit_[:-1] & lit_[1:]
            # tolerance: the lookup is evaluated at the state of the step (Fa_ before the update) and the tank pressure is updated every
            # 10 ms; 2 % of the rate covers the change of the lookup over one step
            exc_o = float(np.max((dF - 1.02 * ro)[on])) if np.any(on) else 0.0
            exc_c = float(np.max((-dF - 1.02 * rc)[on & (rec[:n - 1, I["phase"]] != 2)])) if np.any(on) else 0.0
            near = float(np.mean(np.abs(dF[on] - ro[on]) < 0.02 * ro[on])) if np.any(on) else 0.0
            Dd[f"{lab}|{arm}"] = dict(rise_rate_excess_N_per_s=exc_o, fall_rate_excess_N_per_s=exc_c, share_steps_at_open_limit=near,
                                      bind_t=float(res["rmap_bind_t"]), bind_land=float(res["rmap_bind_land"]),
                                      bind_asc=float(res["rmap_bind_asc"]), P_tank_min_MPa=float(res["rmap_pt_min"]) / 1e6,
                                      P_tank_trigger_MPa=float(res["pt_trigger"]) / 1e6, landed_ok=bool(R.success(res)),
                                      passed=bool(exc_o <= 1.0 and (arm == "R1" or exc_c <= 1.0) and res["rmap_bind_t"] > 0))
            print(f"D T-RM3 {lab} {arm}:", Dd[f"{lab}|{arm}"], flush=True)
            ok_all &= Dd[f"{lab}|{arm}"]["passed"]
    out["parts"]["D_T-RM3_rate_bounded_by_map"] = dict(cases=Dd, note=(
        "excess = max over lit steps (recorded command > 0) of the delivered thrust rate minus 1.02 x the map rate at the recorded "
        "state; shutdown transients (not lit) follow the sim6 shutdown model, not the map; R1 closing at 2500 N/s"))
    # E
    cfg, _, _ = cfg_of_base("rbl_B1_lead62_pc_k2")
    r0, c0, _ = R.fly(dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.001), nrec=200000)
    r1, c1, _ = R.fly(dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.001, thr_lat=0.004), nrec=200000)
    t0, F0 = c0[:, I["t"]], c0[:, I["F"]]
    F1 = c1[:, I["F"]]
    zt = c0[:, I["z"]]
    hold = np.where(np.abs(zt - zt[0]) < 1e-9)[0]
    kk = hold[(hold >= 4) & (hold < len(F1))]
    dmax = float(np.max(np.abs(F1[kk] - F0[kk - 4]))) if len(kk) else None
    Ee = dict(hold_steps=int(len(kk)), max_abs_diff_N=dmax, passed=bool(dmax is not None and dmax < 0.05 * 500.0 * 0.004 * 5.0))
    print("E T-LAT:", Ee, flush=True)
    out["parts"]["E_T-LAT_latency_shift"] = dict(Ee, note=("pad hold (vehicle not moving): F with 4 ms latency vs F without, shifted by "
                                                          "4 steps; the tank pressure differs slightly (different flow history), "
                                                          "tolerance 0.5 N"))
    ok_all &= Ee["passed"]
    # F
    pB = m["model_B"]
    tp, tv = float(pB["tau_p_s"]), float(pB["tau_v_s"])
    rF, cF, _ = R.fly(dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.001, rate_map=m, rmap_close=0, rmap_cap=1, thr_drive=1,
                           thr_lat=float(pB["latency_s"]), thr_tau_p=tp, thr_tau_v=tv), nrec=200000)
    n = int(rF["nrec"])
    Ftg, Fdr, Pt, tsc = cF[:n, I["Ftg"]], cF[:n, I["Fdrv"]], cF[:n, I["Ptank"]], cF[:n, I["tsc"]]
    on = np.where(Ftg > 0.0)[0]
    k0, k1 = int(on[0]), int(on[-1])
    seg = np.where(np.diff(on) > 1)[0]
    if len(seg):
        k1 = int(on[seg[0]])
    dtr = 0.001
    Fd, vd = 0.0, 0.0
    err = []
    for k in range(k0, k1 + 1):
        ro = min(E.interp_map(m, Pt[k], Fd / tsc[k], "open_N_per_s") * tsc[k], 2500.0)
        rc = 2500.0
        vc = (Ftg[k] - Fd) / tp
        vc = min(max(vc, -rc), ro)
        vd += (vc - vd) * dtr / tv
        Fd += vd * dtr
        if Fd < 0.0:
            Fd, vd = 0.0, 0.0
        err.append(abs(Fd - Fdr[k]))
    err = np.array(err)
    Ff = dict(steps=int(len(err)), max_abs_diff_N=float(err.max()), p99_abs_diff_N=float(np.percentile(err, 99)),
              bind_t=float(rF["rmap_bind_t"]), landed_ok=bool(R.success(rF)), passed=bool(err.max() < 1.0))
    print("F T-DRV:", Ff, flush=True)
    out["parts"]["F_T-DRV_model_B_twin"] = dict(Ff, note=("numpy twin of Electronics' model B on the recorded target; the tank pressure is "
                                                         "updated every 10 ms in sim6 (recorded at the end of the step): tolerance 1 N"))
    ok_all &= Ff["passed"]
    if "G" in PARTS:
        G, okg = part_g()
        out["parts"]["G_T-MEST_estimator_identities"] = G
        ok_all &= okg
    if "H" in PARTS:
        H, okh = part_h()
        out["parts"]["H_T-KCOMP_khat_compensation"] = H
        ok_all &= okh
    if "W" in PARTS:
        import m2_web_limit as WL
        Wc = WL.part_check()
        out["parts"]["W_T-WEB_web_state_and_limit"] = Wc
        ok_all &= bool(Wc["passed"])
    if "X" in PARTS:
        X, okx = part_x()
        out["parts"]["X_T-FAULT_amendment_F"] = X
        ok_all &= okx
    if "P" in PARTS:
        Pp, okp = part_p()
        out["parts"]["P_T-PURGE_amendment_P"] = Pp
        ok_all &= okp
    if "R" in PARTS:
        Rr, okr = part_r()
        out["parts"]["R_T-REL_amendment_R"] = Rr
        ok_all &= okr
    out["all_passed"] = bool(ok_all)
    with open(os.path.join(RES, "bitcheck_v28.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("ALL PASSED" if ok_all else "SOME CHECKS FAILED", flush=True)


def part_g():
    import m2_fc_thrust as FT
    C, _ = FT.cfgs()
    G, ok = {}, True
    for prof in ("A1", "B1"):
        cfg = C[prof]
        dr = dict(R.draw(np.random.default_rng(101), N, cfg)[3])
        dr.update(isp_scale=1.0, m_est_err=0.0)
        c, disp = R.run_cfg(cfg, dr)
        c = dict(c, rec_dt=0.001)
        res0, rec0, _ = R.fly(c, disp, nrec=100000)
        cases = (("G1_all_zero", dict()), ("G2_weigh", dict(mest_w=0.10)), ("G3_kcal", dict(mest_kcal=1.02)),
                 ("G4_dq", dict(mest_dq=0.002)), ("G5_starts", dict(mest_s1=0.004, mest_s2=-0.003)))
        for lab, ov in cases:
            res1, rec1, _ = R.fly(dict(c, mest_mode=1, **ov), disp, nrec=100000)
            n = int(res1["nrec"])
            m = rec1[:n, I["mex"]]           # exact truth mass (sim6 amendment M record)
            e = rec1[:n, I["mhe"]]
            F = rec1[:n, I["F"]]
            t = rec1[:n, I["t"]]
            if lab == "G1_all_zero":
                ref = np.zeros(n)
            elif lab == "G2_weigh":
                ref = 0.10 / m
            elif lab == "G3_kcal":
                ref = -0.02 * (m[0] - m) / m
            elif lab == "G4_dq":
                # the estimator integrates dq over the steps with F > 0 (F recorded after the step)
                tb = np.cumsum(np.where(F > 0.0, 0.001, 0.0))
                ref = -0.002 * tb / m
            else:
                st = np.zeros(n)
                on = F > 0.0
                rise = np.where(on & ~np.r_[False, on[:-1]])[0]
                if len(rise):
                    st[rise[0]:] += 0.004
                if len(rise) > 1:
                    st[rise[1]:] += -0.003
                ref = st / m
            # one-step timing tolerance at the step changes (record taken at the step end; F > 0 test vs the estimator's own)
            d = np.abs(e - ref)
            # +/- one recorder step of timing (the estimate is recorded from the start of the step, F at its end) and 1e-5 relative:
            # the recorded truth mass mex combines the top-of-step mass properties with the end-of-step tank mass (one step of
            # flow, up to ~3e-6 relative here); the first record (the first start is applied within step 0) is skipped
            tol = 1e-5 + np.abs(np.diff(np.r_[ref[0], ref])) + np.abs(np.diff(np.r_[ref, ref[-1]]))
            bad = int(np.sum((d > tol)[1:]))
            r_ = dict(max_abs_e=float(np.max(np.abs(e))), max_abs_dev=float(d.max()), steps_out_of_tol=bad, n=n,
                      landed_ok=bool(R.success(res1)))
            if lab == "G1_all_zero":
                # the flight is not bit-identical to mest_mode 0: mode 0 guides on the massprops mass (tank split of the last
                # 10 ms solve), mode 1 on the exact integral; the touchdown state is reported, the identity is on the estimate
                r_["touchdown_diff_vs_mode0"] = {k: float(res1[k]) - float(res0[k]) for k in ("td_vz", "td_vh", "td_tilt", "td_t", "prop_used")}
                r_["passed"] = bool(r_["max_abs_e"] < 1e-9 and R.success(res1) == R.success(res0))
            else:
                r_["passed"] = bool(bad == 0)
            G[f"{prof}|{lab}"] = r_
            ok &= r_["passed"]
            print(f"G T-MEST {prof} {lab}:", r_, flush=True)
    return G, ok


def part_h():
    import m2_fc_thrust as FT
    C, _ = FT.cfgs()
    cfg = C["A1"]
    D = R.draw(np.random.default_rng(101), N, cfg)
    PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
    med = {}
    for comp in (0, 1):
        rr = []
        for i in range(40):
            c, disp = R.run_cfg(cfg, D[i])
            c = dict(c, rec_dt=0.001, kest_comp=comp)
            par = R.build(c, disp)[0]
            res, rec, _ = R.fly(c, disp, nrec=100000)
            F = rec[:, I["F"]]
            ph = rec[:, I["phase"]]
            _, fc, _, _ = FT.windows(par, res, rec, "A1")
            sel = fc & (F > 0.3 * par[PN["Fmax"]]) & (ph == 5)
            if sel.sum() < 50:
                continue
            ek = (1.0 + par[PN["mest"]]) * par[PN["thrust_scale"]] * (1.0 + par[PN["a_sf"]])
            rr.append(float(np.median(rec[sel, I["keff"]] / ek - 1.0)))
        med[comp] = (float(np.median(rr)), len(rr))
    H = dict(median_ratio_minus_1_uncomp=med[0][0], median_ratio_minus_1_comp=med[1][0], runs=med[1][1],
             passed=bool(abs(med[1][0]) < 0.005 and med[0][0] < -0.008))
    print("H T-KCOMP:", H, flush=True)
    return H, H["passed"]



def nominal(cfg, **kw):
    return R.fly(dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.001, **kw), nrec=200000)


def part_x():
    X, ok = {}, True
    PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
    bases = (("A1", "A1_none"), ("B1", "rbl_B1_lead62_pc_k2"))
    # X1
    for prof, base in bases:
        cfg, _, _ = cfg_of_base(base)
        D = R.draw(np.random.default_rng(101), N, cfg)
        mism, dec, geo = [], 0, 0
        for i in range(20):
            c, disp = R.run_cfg(cfg, D[i])
            r0 = R.fly(c, disp, nrec=10)[0]
            r1 = R.fly(dict(c, flt_on=1, flt_ph=1, flt_t=1.0e9), disp, nrec=10)[0]
            dec += int(r1["flt_tdec"] >= 0.0)
            geo += int(r1["flt_tr_geo"] >= 0.0)
            mm = [k for k in s6.RES_NAMES if not k.startswith(("flt_", "fct_")) and
                  not (r0[k] == r1[k] or (np.isnan(r0[k]) and np.isnan(r1[k])))]
            if mm:
                mism.append(dict(run=i, fields=mm[:6]))
        r_ = dict(runs=20, decisions=dec, geofence_trips_not_acted=geo, mismatches=mism, passed=bool(dec == 0 and not mism))
        X[f"X1_{prof}_armed_no_onset"] = r_
        ok &= r_["passed"]
        print(f"X1 {prof}:", r_, flush=True)
    for prof, base in bases:
        cfg, _, _ = cfg_of_base(base)
        par = R.build(dict(cfg, flt_on=1))[0]
        dt = float(par[PN["dt"]])
        # X2 / X3
        res, rec, _ = nominal(cfg, flt_on=1, flt_ph=1, flt_t=0.5, flt_F=670.0, flt_rate=2500.0, flt_enc=0, flt_pcl=0, det_fct=0,
                              det_pf=0)
        n = int(res["nrec"])
        t, F, ts, st = rec[:n, I["t"]], rec[:n, I["F"]], rec[:n, I["tsc"]], rec[:n, I["flts"]]
        k0 = int(np.argmax((F / np.where(ts > 0, ts, 1.0)) > par[PN["det_op_F"]]))
        d2 = float(res["flt_tr_op"]) - float(t[k0])
        x2 = dict(first_above_s=float(t[k0]), trip_s=float(res["flt_tr_op"]), delay_s=d2, det_op_t=float(par[PN["det_op_t"]]),
                  source=float(res["flt_src"]), decision_s=float(res["flt_tdec"]),
                  expected_delay_s=float(par[PN["det_op_t"]] - 2 * dt),
                  passed=bool(abs(d2 - (par[PN["det_op_t"]] - 2 * dt)) <= 1e-9 and res["flt_src"] == 2.0 and
                              res["flt_tdec"] == res["flt_tr_op"]))
        X[f"X2_{prof}_overpressure_timing"] = x2
        ok &= x2["passed"]
        print(f"X2 {prof}:", x2, flush=True)
        seat = float(res["flt_tseat"])
        k3 = (st == 3) & (t >= seat - 1e-9)
        imp = float(np.sum(F[k3]) * dt)
        x3 = dict(mv_cmd_minus_dec_s=float(res["flt_tmv"] - res["flt_tdec"]), seat_minus_mv_s=float(res["flt_tseat"] - res["flt_tmv"]),
                  abt_lat=float(par[PN["abt_lat"]]), abt_seat=float(par[PN["abt_seat"]]), tailoff_impulse_Ns=imp,
                  abt_imp=float(par[PN["abt_imp"]]),
                  passed=bool(abs(res["flt_tmv"] - res["flt_tdec"] - par[PN["abt_lat"]]) <= dt + 1e-9 and
                              abs(res["flt_tseat"] - res["flt_tmv"] - par[PN["abt_seat"]]) <= dt + 1e-9 and
                              abs(imp / par[PN["abt_imp"]] - 1.0) < 0.02))
        X[f"X3_{prof}_abort_sequence"] = x3
        ok &= x3["passed"]
        print(f"X3 {prof}:", x3, flush=True)
        # X4
        res, rec, _ = nominal(cfg, flt_on=1, flt_ph=1, flt_t=0.5, flt_F=670.0, flt_rate=2500.0, flt_enc=1, flt_pcl=1, det_fct=0)
        n = int(res["nrec"])
        t, F, ts, Fc, st = rec[:n, I["t"]], rec[:n, I["F"]], rec[:n, I["tsc"]], rec[:n, I["Fcmd"]], rec[:n, I["flts"]]
        act = (st == 1) | (st == 2)
        dev = act & (np.abs(F / np.where(ts > 0, ts, 1.0) - Fc) > par[PN["det_pf_dF"]])
        k4 = int(np.argmax(dev))
        d4 = float(res["flt_tr_pf"]) - float(t[k4])
        x4 = dict(first_dev_s=float(t[k4]), trip_s=float(res["flt_tr_pf"]), delay_s=d4, det_pf_t=float(par[PN["det_pf_t"]]),
                  det_pf_dF_N=float(par[PN["det_pf_dF"]]), source=float(res["flt_src"]),
                  expected_delay_s=float(par[PN["det_pf_t"]] - dt),
                  passed=bool(abs(d4 - (par[PN["det_pf_t"]] - dt)) <= 1e-9 and res["flt_src"] == 3.0))
        X[f"X4_{prof}_pintle_fault_timing"] = x4
        ok &= x4["passed"]
        print(f"X4 {prof}:", x4, flush=True)
    # X5 (A1 only: relight)
    cfg, _, _ = cfg_of_base("A1_none")
    par = R.build(dict(cfg, flt_on=1))[0]
    dt = float(par[PN["dt"]])
    res = nominal(cfg, flt_on=1, flt_ph=1, flt_t=0.5, flt_F=670.0, flt_rate=2500.0, flt_enc=0, flt_pcl=1, det_fct=0, det_op=0,
                  det_pf=0)[0]
    x5 = dict(t_shutdown=float(res["flt_tsd"]), t_seat=float(res["flt_tseat"]), seat_minus_sd_s=float(res["flt_tseat"] - res["flt_tsd"]),
              expected_s=float(par[PN["abt_sdenc"]] + par[PN["abt_seat"]]), activations=float(res["flt_n_on"]),
              decision=float(res["flt_tdec"]),
              passed=bool(abs(res["flt_tseat"] - res["flt_tsd"] - par[PN["abt_sdenc"]] - par[PN["abt_seat"]]) <= 2 * dt + 1e-9 and
                          res["flt_n_on"] == 2.0 and res["flt_tdec"] < 0.0))
    X["X5_A1_linkage_normal_close_relight"] = x5
    ok &= x5["passed"]
    print("X5 A1:", x5, flush=True)
    return X, ok


def part_p():
    Pp, ok = {}, True
    PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
    cfg, _, _ = cfg_of_base("A1_none")
    par = R.build(dict(cfg, prg_on=1))[0]
    dt = float(par[PN["dt"]])
    md = float(par[PN["prg_mdot"]])
    D = R.draw(np.random.default_rng(101), N, cfg)
    mism, mass_err, waits, durs = [], 0.0, 0, []
    for i in range(20):
        c, disp = R.run_cfg(cfg, D[i])
        r0 = R.fly(c, disp, nrec=10)[0]
        r1 = R.fly(dict(c, prg_on=1, prg_mdot=0.0, prg_jet=0, prg_book=0), disp, nrec=10)[0]
        mm = [k for k in s6.RES_NAMES if not k.startswith(("prg_", "blf_")) and
              not (r0[k] == r1[k] or (np.isnan(r0[k]) and np.isnan(r1[k])))]
        if mm:
            mism.append(dict(run=i, fields=mm[:6]))
        r2 = R.fly(dict(c, prg_on=1), disp, nrec=10)[0]
        mass_err = max(mass_err, abs(r2["prg_mass"] - md * r2["prg_dur"]))
        waits += int(r2["prg_wait"] > 1e-9)
        durs.append(float(r2["prg_dur"]))
    p1 = dict(runs=20, mismatches=mism, passed=not mism)
    p2 = dict(runs=20, max_abs_mass_err_kg=mass_err, step_mass_kg=md * dt, waits=waits, dur_min_s=min(durs), dur_max_s=max(durs),
              passed=bool(mass_err <= md * dt + 1e-12 and waits == 0 and min(durs) > 0.0))
    Pp["P1_A1_plumbing_identity"] = p1
    Pp["P2_A1_purge_accounting"] = p2
    ok &= p1["passed"] and p2["passed"]
    print("P1:", p1, flush=True)
    print("P2:", p2, flush=True)
    # P3 / P4
    dr = dict(D[3]); dr.update(isp_scale=1.0, m_est_err=0.0)
    out_ = {}
    for book in (1, 0):
        c, disp = R.run_cfg(cfg, dr)
        res, rec, _ = R.fly(dict(c, rec_dt=0.001, prg_on=1, prg_book=book, mest_mode=1), disp, nrec=200000)
        n = int(res["nrec"])
        t, mex, mhe = rec[:n, I["t"]], rec[:n, I["mex"]], rec[:n, I["mhe"]]
        t0, t1 = float(res["prg_t0"]), float(res["prg_t0"] + res["prg_dur"])
        ka = int(np.argmin(np.abs(t - t0))); kb = int(np.argmin(np.abs(t - t1)))
        out_[book] = dict(res=res, dm=float(mex[ka] - mex[kb]), dur=float(t[kb] - t[ka]), mhe_max_in=float(np.max(np.abs(mhe[ka:kb + 1]))),
                          mhe_after=float(mhe[kb + 5]), m_after=float(mex[kb + 5]))
    r1 = out_[1]
    p3 = dict(mass_drop_kg=r1["dm"], expected_kg=md * r1["dur"], duration_s=r1["dur"],
              passed=bool(abs(r1["dm"] - md * r1["dur"]) <= 2 * md * dt + 1e-9))
    p4 = dict(book1_max_abs_mhe=r1["mhe_max_in"], book0_mhe_after=out_[0]["mhe_after"],
              book0_expected=float(out_[0]["res"]["prg_mass"] / out_[0]["m_after"]),
              passed=bool(r1["mhe_max_in"] < 1e-9 and abs(out_[0]["mhe_after"] - out_[0]["res"]["prg_mass"] / out_[0]["m_after"]) < 1e-6))
    Pp["P3_A1_truth_mass"] = p3
    Pp["P4_A1_fsw_booking"] = p4
    ok &= p3["passed"] and p4["passed"]
    print("P3:", p3, flush=True)
    print("P4:", p4, flush=True)
    # P5
    cfgB, _, _ = cfg_of_base("rbl_B1_lead62_pc_k2")
    parB = R.build(dict(cfgB, blf_on=1))[0]
    fj = float(parB[PN["blf_mdot"]] * parB[PN["bl_vj"]])
    resj, recj, _ = nominal(cfgB, blf_on=1, blf_ph=0, blf_mode=0)
    res0, rec0, _ = nominal(cfgB, blf_on=1, blf_ph=0, blf_mode=0, bl_vj=0.0)
    n = min(int(resj["nrec"]), int(res0["nrec"]))
    ph = rec0[:n, I["phase"]]
    tt = rec0[:n, I["t"]]
    sel = ((ph == 2) | (ph == 3)) & (tt > 2.0) & (rec0[:n, I["F"]] > 1.0) & (recj[:n, I["F"]] > 1.0)
    Fm = float(np.mean(rec0[:n, I["F"]][sel]))
    dgy = float(np.mean(recj[:n, I["dgy"]][sel]) - np.mean(rec0[:n, I["dgy"]][sel]))
    dgx = float(np.mean(recj[:n, I["dgx"]][sel]) - np.mean(rec0[:n, I["dgx"]][sel]))
    exp_ = float(np.degrees(-fj / Fm))
    p5 = dict(F_jet_N=fj, F_mean_N=Fm, steps=int(sel.sum()), d_dgy_deg=dgy, d_dgx_deg=dgx, expected_d_dgy_deg=exp_,
              passed=bool(abs(dgy - exp_) <= 0.2 * abs(exp_) and abs(dgx) <= 0.2 * abs(exp_)))
    Pp["P5_B1_jet_trim"] = p5
    ok &= p5["passed"]
    print("P5:", p5, flush=True)
    return Pp, ok


def part_r():
    Rr, ok = {}, True
    PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
    cfg, _, _ = cfg_of_base("A1_none")
    par, _, _, _, tab, _ = R.build(dict(cfg, rel_mode=1))
    dt = float(par[PN["dt"]])
    pcm = np.asarray(tab["pc"], float)[:, 0]
    Fgm = np.asarray(tab["Fg"], float)
    floorF = float(par[PN["floor"]] * par[PN["Fmax"]])
    # R4
    relF = float(par[PN["rel_F"]])
    r4 = dict(rel_F_N=relF, expected_N=float(np.interp(3.0e5, pcm, Fgm)), floor_N=floorF,
              passed=bool(relF == float(np.interp(3.0e5, pcm, Fgm)) and 30.0 < relF < 40.0))
    Rr["R4_rel_F_derivation"] = r4
    ok &= r4["passed"]
    print("R4:", r4, flush=True)
    # R1: release pressure at the map Pc of 0.5 x floor -> same release step as rel_mode 0
    pc_half = float(np.interp(0.5 * floorF, Fgm, pcm))
    D = R.draw(np.random.default_rng(101), N, cfg)
    mism, rel_ = [], []
    for i in range(20):
        c, disp = R.run_cfg(cfg, D[i])
        r0 = R.fly(c, disp, nrec=10)[0]
        r1 = R.fly(dict(c, rel_mode=1, rel_Pc=pc_half, rel_dt=0.0), disp, nrec=10)[0]
        mm = [k for k in s6.RES_NAMES if not k.startswith("rel_") and not (r0[k] == r1[k] or (np.isnan(r0[k]) and np.isnan(r1[k])))]
        if mm:
            mism.append(dict(run=i, fields=mm[:6]))
        rel_.append((float(r0["rel_t"]), float(r1["rel_t"])))
    r1_ = dict(runs=20, rel_Pc_bar=pc_half / 1e5, mismatches=mism, rel_t_equal=bool(all(a == b for a, b in rel_)),
               passed=bool(not mism and all(a == b for a, b in rel_)))
    Rr["R1_A1_rule_identity"] = r1_
    ok &= r1_["passed"]
    print("R1:", r1_, flush=True)
    # R2 / R3: nominal A1 on the 1 ms record
    for tag, rdt in (("R2", 0.0), ("R3", 0.2)):
        res, rec, _ = nominal(cfg, rel_mode=1, rel_dt=rdt)
        n = int(res["nrec"])
        t, ph, F, tsc = rec[:n, I["t"]], rec[:n, I["phase"]], rec[:n, I["F"]], rec[:n, I["tsc"]]
        k5 = int(np.argmax(ph == 5))            # first record of phase 5: stamp = t5 + dt
        t5 = float(t[k5] - dt)
        tr = t5 + float(res["rel_t"])            # release step time (before the step increment)
        fpc = F / np.where(tsc > 0, tsc, 1.0)
        pre = (t >= t5) & (t <= tr - 2.0 * dt + 1e-9)
        around = (t >= tr - dt - 1e-9) & (t <= tr + dt + 1e-9)
        first_cross = float(t[pre & (fpc >= relF)][0]) if np.any(pre & (fpc >= relF)) else None
        if tag == "R2":
            r_ = dict(t_light_s=t5, rel_t_s=float(res["rel_t"]), rel_Fpc_N=float(res["rel_Fpc"]), rel_F_N=relF,
                      crossing_before_release=first_cross, crossing_at_release=bool(np.any(fpc[around] >= relF)),
                      passed=bool(res["rel_Fpc"] >= relF and first_cross is None and np.any(fpc[around] >= relF)
                                  and res["relight_ok"] > 0.5))
        else:
            r_ = dict(t_light_s=t5, rel_t_s=float(res["rel_t"]), rel_dt_s=rdt, rel_Fpc_N=float(res["rel_Fpc"]),
                      passed=bool(rdt - 1e-9 <= res["rel_t"] <= rdt + dt + 1e-9 and res["rel_Fpc"] >= relF))
        Rr[f"{tag}_A1_nominal_release"] = r_
        ok &= r_["passed"]
        print(f"{tag}:", r_, flush=True)
    return Rr, ok


if __name__ == "__main__":
    main()
