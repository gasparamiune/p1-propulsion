"""m2_bitcheck_v28 v1 (GNC, 2026-10-13): checks of sim6/run6 v2.8-dev (ENG-03 state-dependent thrust-rate map, servo latency and
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
Env: GNC_IFACE, GNC_ACT_RATE (v3c set), GNC_RES (default out/v28_checks), GNC_BIT_K (8). Output: GNC_RES/bitcheck_v28.json"""
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
    out = dict(tool="m2_bitcheck_v28 v1", sim=s6.SIM6_VERSION, iface=os.environ.get("GNC_IFACE"), parts={})
    ok_all = True
    m = E.load_map()
    # A
    A = {}
    for base in ("A1_none", "A1J_pc", "rbl_B1_lead62_pc_k2"):
        cfg, rows, p = cfg_of_base(base)
        A[base] = dict(compare(cfg, rows, f"A {base} (v2.7.1-dev ref)"), reference=p)
        ok_all &= A[base]["mismatches"] == 0
    out["parts"]["A_options_off_vs_v2.7.1-dev"] = A
    # B
    big = dict(m, open_N_per_s=(np.full(np.shape(m["open_N_per_s"]), 1e9)).tolist(),
               close_N_per_s=(np.full(np.shape(m["close_N_per_s"]), 1e9)).tolist())
    Bp = {}
    for base in ("A1_none", "rbl_B1_lead62_pc_k2"):
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
    out["all_passed"] = bool(ok_all)
    with open(os.path.join(RES, "bitcheck_v28.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("ALL PASSED" if ok_all else "SOME CHECKS FAILED", flush=True)


if __name__ == "__main__":
    main()
