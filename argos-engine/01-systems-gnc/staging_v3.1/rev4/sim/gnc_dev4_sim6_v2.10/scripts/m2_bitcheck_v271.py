"""m2_bitcheck_v271 v2 (GNC, 2026-10-13): checks of sim6/run6 v2.7.1-dev (regression-law band option, gncsim.regband; start-delay
quantile option t_ign_q). v2 adds part E and re-runs A-D on the code with the t_ign_q option (v1 result kept as
bitcheck_v271_pre_tq.json).
A  options off vs stored sim6 v2.6 Monte Carlo runs (the m2_bitcheck_v27 references: pc_A1_2kg, pc_B1_h85_2kg, m2_J1.6_n15)
B  v2.7 options ON (k_est_asc 2, throat growth, relight 1.81 s) with the band off vs stored sim6 v2.7-dev runs
   (tg_B1_pc_k2, tg_A1_none_k2, rl181e_A1_none_k2)
C  T-RB1: band ON at the nominal corner (a x1.0, n 0.5: phi = 1 exactly) vs the stored tg_B1_pc_k2 runs: must be identical
D  T-RB2: nominal B1 85 m flights (no dispersion, k_est_asc 2) at the 3 x 3 corners: 6-DOF oxidiser burned / no-band flight vs
   the model's prediction integrated on the no-band flight's own X history (the guidance closes the loop, so a small
   difference is expected; reported, not gated)
E  T-TQ: start-delay quantile option t_ign_q: E1 the main draw table is unchanged with the option on (pairing); E2 a constant
   table gives that delay on every run; E3 Combustion-like table: on recorded flights (1 ms recorder) the time from the relight
   command to thrust onset equals the drawn start delay within one integration step; E4 the nominal (sizing) flight uses the
   table median
For A-C: re-fly the first K runs and every failed run, compare every result field stored in the reference CSV exactly.
Env: GNC_IFACE (v3c set), GNC_RES (default out/v271_checks), GNC_BIT_K (8). Output: GNC_RES/bitcheck_v271.json"""
import csv
import json
import os
import sys
import numpy as np

os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6, regband as RB  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_duty_cycles_disp as DD  # noqa: E402

S = "/home/claude/work/space/out"
RES = os.environ.get("GNC_RES", f"{S}/v271_checks")
K = int(os.environ.get("GNC_BIT_K", "8"))
N = 500
V26_REFS = [(f"{S}/prop_closure_m2/mc6_summary_pc2.json", f"{S}/prop_closure_m2/mc6_runs_%s_pc2.csv", "pc_A1_2kg"),
            (f"{S}/prop_closure_m2/mc6_summary_pc2.json", f"{S}/prop_closure_m2/mc6_runs_%s_pc2.csv", "pc_B1_h85_2kg"),
            (f"{S}/mechv2_mc/mc6_summary_m2.json", f"{S}/mechv2_mc/mc6_runs_%s_m2.csv", "m2_J1.6_n15")]
I = {n: i for i, n in enumerate(s6.REC_NAMES)}


def compare(cfg, rows, label):
    D = R.draw(np.random.default_rng(101), N, cfg)
    idx = list(range(K)) + [i for i, r in enumerate(rows) if int(float(r["ok"])) == 0 and i >= K]
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


def cfg_from_over(over):
    over = dict(over)
    m = over.pop("m_fixed")
    return R.cfg_of(**dict(over, m_n2o=float(m)))


def main():
    os.makedirs(RES, exist_ok=True)
    out = dict(tool="m2_bitcheck_v271 v2", sim=s6.SIM6_VERSION, regband=RB.VERSION, iface=os.environ.get("GNC_IFACE"), parts={})
    ok_all = True
    # A
    A = {}
    for summ, pat, c in V26_REFS:
        cs = json.load(open(summ))["cases"][c]
        assert "v2.6" in cs["sim"], cs["sim"]
        cfg = {k: (tuple(v) if isinstance(v, list) else v) for k, v in cs["config"].items()}
        cfg["m_n2o"] = cs["m_n2o_mc_kg"]
        cfg = R.cfg_of(**cfg)
        A[c] = dict(compare(cfg, list(csv.DictReader(open(pat % c))), f"A {c} (v2.6 ref)"), reference=pat % c)
        ok_all &= A[c]["mismatches"] == 0
    out["parts"]["A_options_off_vs_v2.6"] = A
    # B and C
    co, jr = DD.case_over()
    B = {}
    for c in ("tg_B1_pc_k2", "tg_A1_none_k2"):
        over, csvp = co[c]
        B[c] = dict(compare(cfg_from_over(over), list(csv.DictReader(open(csvp))), f"B {c} (v2.7-dev ref)"), reference=csvp)
        ok_all &= B[c]["mismatches"] == 0
    rl = dict(PC.DC["A1"], m_fixed=PC.M_TANK, t_ign_add=0.56, t_ign_est=1.81, k_est_asc=2)
    p = f"{S}/relight_181/mc6_runs_rl181e_A1_none_k2_rl181.csv"
    B["rl181e_A1_none_k2"] = dict(compare(cfg_from_over(rl), list(csv.DictReader(open(p))), "B rl181e_A1_none_k2 (v2.7-dev ref)"),
                                  reference=p)
    ok_all &= B["rl181e_A1_none_k2"]["mismatches"] == 0
    out["parts"]["B_v27_options_on_band_off_vs_v2.7-dev"] = B
    over, csvp = co["tg_B1_pc_k2"]
    C = dict(compare(cfg_from_over(dict(over, reg_a=1.0, reg_n=0.5)), list(csv.DictReader(open(csvp))),
                     "C T-RB1 band at the nominal corner"), reference=csvp)
    ok_all &= C["mismatches"] == 0
    out["parts"]["C_T-RB1_nominal_corner_identity"] = C
    # D
    B1 = dict(PC.DC["B1"], h_target=85.0, k_est_asc=2)
    cfg0 = R.cfg_of(**dict(B1, m_n2o=PC.M_TANK))
    res0, rec0, _ = R.fly(dict(cfg0, noise=False, wind=0.0, gust=False, rec_dt=0.01), nrec=8000)
    t = rec0[:, I["t"]]; dt = np.diff(t, prepend=0.0)
    mox0 = rec0[:, I["mox"]]
    X0 = np.cumsum(mox0 * dt)
    ox0 = float(np.sum(mox0 * dt))
    Dd = {}
    for a in (0.6, 1.0, 1.5):
        for n in (0.35, 0.5, 0.68):
            xs, po, pu = RB.knots(a, n)
            pred = float(np.sum(np.interp(X0, xs, po) * mox0 * dt)) / ox0
            r1, rec1, _ = R.fly(dict(R.cfg_of(**dict(B1, m_n2o=PC.M_TANK, reg_a=a, reg_n=n)), noise=False, wind=0.0, gust=False,
                                     rec_dt=0.01), nrec=8000)
            t1 = rec1[:, I["t"]]; dt1 = np.diff(t1, prepend=0.0)
            ox1 = float(np.sum(rec1[:, I["mox"]] * dt1))
            Dd[f"{a}|{n}"] = dict(ox_ratio_6dof=ox1 / ox0, ox_ratio_model_on_reference_history=pred,
                                  diff=ox1 / ox0 - pred, X_end_kg=float(r1["reg_X_end"]),
                                  impulse_ratio=float(np.sum(rec1[:, I["F"]] * dt1) / np.sum(rec0[:, I["F"]] * dt)))
            print(f"D a{a} n{n}: 6-DOF ox ratio {ox1 / ox0:.4f} model {pred:.4f} diff {ox1 / ox0 - pred:+.4f} | impulse ratio "
                  f"{Dd[f'{a}|{n}']['impulse_ratio']:.4f} | X_end {r1['reg_X_end']:.3f} kg", flush=True)
    out["parts"]["D_T-RB2_corner_effect_on_nominal_B1"] = dict(cases=Dd, max_abs_diff=max(abs(v["diff"]) for v in Dd.values()),
                                                                note="not gated: the closed loop changes the thrust history")
    # E
    E = {}
    A1b = dict(PC.DC["A1"], m_fixed=PC.M_TANK, k_est_asc=2)
    tq = tuple(float(x) for x in np.linspace(0.126, 0.499, 21) ** 1.0)
    cfg_off = cfg_from_over(dict(A1b, t_ign_add=0.0, t_ign_est=0.81))
    cfg_on = cfg_from_over(dict(A1b, t_ign_add=0.0, t_ign_est=0.81, t_ign_q=tq))
    D0 = R.draw(np.random.default_rng(101), N, cfg_off)
    D1 = R.draw(np.random.default_rng(101), N, cfg_on)
    diff_keys = set()
    for a_, b_ in zip(D0, D1):
        for k in a_:
            va, vb = a_[k], b_[k]
            same = (va == vb) if not isinstance(va, tuple) else all(x == y for x, y in zip(va, vb))
            if not same:
                diff_keys.add(k)
    extra = sorted(set(D1[0]) - set(D0[0]))
    E["E1_main_draws_unchanged"] = dict(keys_differing=sorted(diff_keys), keys_added=extra, ok=not diff_keys)
    print("E1 main draws unchanged:", not diff_keys, "added", extra, flush=True)
    ok_all &= not diff_keys
    cfg_c = cfg_from_over(dict(A1b, t_ign_add=0.0, t_ign_est=0.81, t_ign_q=tuple([0.37] * 21)))
    Dc = R.draw(np.random.default_rng(101), N, cfg_c)
    sdc = np.array([R.run_cfg(cfg_c, d)[0]["t_ign"] for d in Dc])
    E["E2_constant_table"] = dict(value=0.37, min=float(sdc.min()), max=float(sdc.max()), ok=bool(np.all(sdc == 0.37)))
    print("E2 constant table:", E["E2_constant_table"], flush=True)
    ok_all &= E["E2_constant_table"]["ok"]
    e3 = []
    for i in range(K):
        u = D1[i]["_t_ign_u"]
        sd_indep = float(np.interp(u, np.linspace(0.0, 1.0, 21), np.array(tq)))
        c, disp = R.run_cfg(cfg_on, D1[i])
        res, rec, _ = R.fly(dict(c, rec_dt=0.001), disp, nrec=120000)
        t, ph, F = rec[:, I["t"]], rec[:, I["phase"]], rec[:, I["F"]]
        i4 = int(np.where(ph >= 4)[0][0])
        i5 = int(np.where((ph >= 5) & (F > 0.0))[0][0])
        dl = float(t[i5] - t[i4])
        e3.append(dict(run=i, u=u, start_delay_draw=D1[i]["_t_ign_q"], start_delay_independent=sd_indep, cmd_to_onset_s=dl,
                       t_relight_res=float(res["t_relight"]), t_relight_rec=float(t[i4]), err_s=dl - D1[i]["_t_ign_q"]))
        print(f"E3 run {i}: u {u:.3f} delay {D1[i]['_t_ign_q']:.4f} (indep {sd_indep:.4f}) cmd->onset {dl:.4f} s "
              f"err {1e3 * (dl - D1[i]['_t_ign_q']):+.2f} ms", flush=True)
    ok3 = all(abs(x["err_s"]) <= 1.0e-3 + 1e-9 and x["start_delay_draw"] == x["start_delay_independent"] for x in e3)
    E["E3_cmd_to_onset_equals_draw"] = dict(runs=e3, tolerance_s=1.0e-3, ok=bool(ok3),
                                           note="recorder at the 1 ms integration step; onset = first record with phase >= 5 and F > 0")
    ok_all &= ok3
    par = R.build(cfg_on)[0]
    tn = float(par[s6.PAR_NAMES.index("t_ign")])
    E["E4_nominal_uses_table_median"] = dict(t_ign_nominal=tn, table_median=float(np.interp(0.5, np.linspace(0, 1, 21), tq)),
                                             ok=abs(tn - float(np.interp(0.5, np.linspace(0, 1, 21), tq))) < 1e-12)
    print("E4:", E["E4_nominal_uses_table_median"], flush=True)
    ok_all &= E["E4_nominal_uses_table_median"]["ok"]
    out["parts"]["E_T-TQ_start_delay_quantile_option"] = E
    out["bit_identical_A_B_C"] = bool(ok_all)
    with open(os.path.join(RES, "bitcheck_v271.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("A-C identical and E passed:", ok_all)


if __name__ == "__main__":
    main()
