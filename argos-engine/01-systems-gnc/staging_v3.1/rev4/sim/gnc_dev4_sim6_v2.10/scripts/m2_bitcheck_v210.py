"""m2_bitcheck_v210 v1.0 (GNC rev3, 2026-10-13): sim6 / run6 v2.10-dev (amendment V2) against v2.9-dev.

Part A (off = identical): the same paired cases are flown in two trees (GNC_TREE = gnc_dev3 with sim6 v2.9-dev f90e0ba8e993ad60,
then gnc_dev4 with sim6 v2.10-dev) with amendment V2 off, and with pv2_on 1 but every V2 option at its neutral value (baseline
mode 0, no hold, no cold flow, no release hold); every result common to both versions and every common record column must be
bit-identical. Part B (functional, gnc_dev4 only): command hold at 62.5 N (record trace), cold-flow thrust against Combustion's
start-level values (12.5-13.3 N, DERIVED), release hold >= E2 + 0.22 s, statistics mode (no release with pcf_Facc 1e9).
Usage: GNC_TREE=<tree> GNC_BC_OUT=<npz> python m2_bitcheck_v210.py fly   (once per tree), then
       python m2_bitcheck_v210.py compare <npz v2.9> <npz v2.10> <out json>; python m2_bitcheck_v210.py func <out json>.
Env as m2r3_env.sh (strict mode; pin list with the cold-flow tables for part B). SIM only."""
import hashlib
import json
import os
import sys
import numpy as np

TREE = os.environ.get("GNC_TREE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, TREE)
sys.path.insert(0, os.path.join(TREE, "scripts"))
import m2_rg01_refly as F  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_bitcheck_v210 v1.0"
V2_NEUTRAL = dict(pv2_on=1, pv2_hold=0, pv2_bl=0, pv2_cold=0, pv2_ck=1.0, pv2_rh=0.0)
PCF2 = dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2)
CASES = [  # name, base, state, purge, plateau, extra, n runs, records
    ("dec_pw", "A1_none", "pw", "G73", "", {}, 24, 2),
    ("dec_liq_none_L400", "A1J_pc", "liq", "none", "L400", {}, 12, 0),
    ("nrLO_G73z", "A1_none", "nrLO", "G73z", "", {}, 8, 0),
    ("pcfR2", "A1_none", "pw", "G73", "", PCF2, 16, 2),
    ("pcfR2fo", "A1J_pc", "pw", "G73", "", dict(PCF2, pcf_fo=1), 12, 2),
    ("pcfR2k875L400", "A1_none", "pw", "G73", "L400", dict(PCF2, pcf_k=0.875), 12, 0),
    ("pcfR1fo", "A1_none", "pw", "G73", "", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=1, pcf_fo=1), 6, 0),
    ("pcfR2dt10", "A1J_pc", "pw", "G73", "", dict(PCF2, pcf_dt=0.010), 8, 0),
]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def fly_case(base, st, pu, pl, ex, n, nrec, v2=None):
    cfg, m = F.base_cfg(base, st, dict(h_target=285.0))
    jr = json.load(open(F.TG))["j_ref"]
    F.MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    D = R.draw(np.random.default_rng(101), F.N, cfg)
    ms = F.MV.case_specs()["tot_cal_comp"]
    res, recs = [], []
    for i in range(n):
        c, disp = F.MV.run_cfg_case(cfg, D[i], ms, i, "base")
        c.update(F.DEC)
        c.update(F.PURGE[pu])
        c.update(F.PLAT[pl])
        c.update(ex)
        if v2:
            c.update(v2)
        r, rec, info = R.fly(c, disp, nrec=(4500 if i < nrec else 10))
        res.append([r[k] for k in s6.RES_NAMES])
        if i < nrec:
            recs.append(rec)
    return np.array(res), recs


def part_fly():
    out = {}
    v210 = "pv2_on" in s6.PAR_NAMES
    for name, base, st, pu, pl, ex, n, nrec in CASES:
        r, recs = fly_case(base, st, pu, pl, ex, n, nrec)
        out[f"{name}|res"] = r
        for k, rc in enumerate(recs):
            out[f"{name}|rec{k}"] = rc
        if v210:
            r2, recs2 = fly_case(base, st, pu, pl, ex, n, nrec, V2_NEUTRAL)
            out[f"{name}|v2n|res"] = r2
            for k, rc in enumerate(recs2):
                out[f"{name}|v2n|rec{k}"] = rc
        print(name, "done", flush=True)
    p = os.environ["GNC_BC_OUT"]
    np.savez_compressed(p, res_names=np.array(s6.RES_NAMES), rec_names=np.array(s6.REC_NAMES),
                        sim=np.array(s6.SIM6_VERSION), sim6_sha16=np.array(sha16(s6.__file__)),
                        run6_sha16=np.array(sha16(R.__file__)), **out)
    print("wrote", p, flush=True)


def part_compare(pa, pb, pout):
    a = np.load(pa, allow_pickle=False)
    b = np.load(pb, allow_pickle=False)
    ra, rb = list(a["res_names"]), list(b["res_names"])
    ca, cb = list(a["rec_names"]), list(b["rec_names"])
    common_r = [k for k in ra if k in rb]
    common_c = [k for k in ca if k in cb]
    ia_r = [ra.index(k) for k in common_r]; ib_r = [rb.index(k) for k in common_r]
    ia_c = [ca.index(k) for k in common_c]; ib_c = [cb.index(k) for k in common_c]
    rep = dict(version=VERSION, a=dict(path=pa, sim=str(a["sim"]), sim6_sha16=str(a["sim6_sha16"]), run6_sha16=str(a["run6_sha16"])),
               b=dict(path=pb, sim=str(b["sim"]), sim6_sha16=str(b["sim6_sha16"]), run6_sha16=str(b["run6_sha16"])),
               common_results=len(common_r), new_results=[k for k in rb if k not in ra], common_record_columns=len(common_c),
               new_record_columns=[k for k in cb if k not in ca], cases={}, all_identical=True)
    for name, *_ in CASES:
        for var in ("", "v2n|"):
            kb = f"{name}|{var}res"
            if kb not in b.files:
                continue
            A = a[f"{name}|res"][:, ia_r]; B = b[kb][:, ib_r]
            same = bool(np.array_equal(A, B, equal_nan=True))
            nd = int(np.sum(~((A == B) | (np.isnan(A) & np.isnan(B)))))
            recs = []
            k = 0
            while f"{name}|rec{k}" in a.files and f"{name}|{var}rec{k}" in b.files:
                X = a[f"{name}|rec{k}"]; Y = b[f"{name}|{var}rec{k}"]
                ok = X.shape[0] == Y.shape[0] and np.array_equal(X[:, ia_c], Y[:, ib_c], equal_nan=True)
                recs.append(dict(rows=int(X.shape[0]), identical=bool(ok)))
                same = same and ok
                k += 1
            rep["cases"][f"{name}|{'v2.10 off' if var == '' else 'v2.10 pv2_on neutral'}"] = dict(
                runs=int(A.shape[0]), results_identical=bool(np.array_equal(A, B, equal_nan=True)), differing_values=nd,
                records=recs)
            rep["all_identical"] = rep["all_identical"] and same
    json.dump(rep, open(pout, "w"), indent=1)
    print(json.dumps(rep, indent=1)[:3000])
    print("ALL IDENTICAL" if rep["all_identical"] else "DIFFERENCES FOUND", flush=True)


def part_func(pout):
    """Functional checks of amendment V2 on gnc_dev4 (A1_none / A1J_pc, pw|G73|h285, Pc invalid from E2)."""
    assert "pv2_on" in s6.PAR_NAMES, "functional part needs the v2.10-dev tree"
    ri = {k: i for i, k in enumerate(s6.RES_NAMES)}
    ci = {k: i for i, k in enumerate(s6.REC_NAMES)}
    ct = R.cold_tables()
    out = dict(version=VERSION, sim=s6.SIM6_VERSION, sim6_sha16=sha16(s6.__file__), run6_sha16=sha16(R.__file__),
               cold_tables=ct["src"], checks={})
    # (1) hold, lit, k 0.875: command trace 62.5 N from the onset to the release; thrust settles at 62.5 x tsc
    hold = dict(PCF2, pcf_k=0.875, pv2_on=1, pv2_hold=1, pv2_bl=3)
    r, recs = fly_case("A1_none", "pw", "G73", "", hold, 3, 3)
    tr = []
    for k, rc in enumerate(recs):
        t, ph, Fc, Fv = rc[:, ci["t"]], rc[:, ci["phase"]], rc[:, ci["Fcmd"]], rc[:, ci["F"]]
        t0 = r[k, ri["pcf_t0"]]
        w = (t >= t0 + 0.02) & (t < t0 + r[k, ri["pv2_hold_s"]] - 0.02)
        tr.append(dict(run=k, onset_t=float(t0), hold_s=float(r[k, ri["pv2_hold_s"]]), released=int(r[k, ri["pcf_rel"]]),
                       release_after_light_s=float(r[k, ri["pcf_relt"]]), fa_at_release_N=float(r[k, ri["pv2_fa_rel"]]),
                       Fcmd_in_hold_min_max=[float(Fc[w].min()) if w.any() else None, float(Fc[w].max()) if w.any() else None],
                       F_in_hold_max=float(Fv[w].max()) if w.any() else None, phases_in_hold=sorted(set(int(x) for x in ph[w])),
                       landed=float(r[k, ri["landed"]]), td_vz=float(r[k, ri["td_vz"]])))
    out["checks"]["hold_trace_lit_k875"] = dict(
        expect="Fcmd = 62.5 N throughout the hold (records every 20 ms); release by R2 (pcf_rel 2) or abort", runs=tr,
        pass_=all(x["Fcmd_in_hold_min_max"][0] == 62.5 and x["Fcmd_in_hold_min_max"][1] == 62.5 for x in tr
                  if x["Fcmd_in_hold_min_max"][0] is not None))
    # (2) flame-out + cold bound at the hold: F_cold at the onset tank pressure vs Combustion's start-level value
    fo = dict(PCF2, pcf_fo=1, pv2_on=1, pv2_hold=1, pv2_bl=3, pv2_cold=1)
    r, recs = fly_case("A1J_pc", "pw", "G73", "", fo, 6, 2)
    rows = []
    for k in range(r.shape[0]):
        P0 = r[k, ri["pv2_Pt0"]]
        ref = float(np.interp(P0, ct["P"], [np.interp(np.interp(62.5, ct["cmds"], cl), ct["lifts"], Fb)
                                            for cl, Fb in zip(ct["cl"], ct["Fb"])]))
        rows.append(dict(run=k, Pt0_bar=round(P0 / 1e5, 3), Fcl_max_N=round(r[k, ri["pv2_Fcl_max"]], 3),
                         table_at_P0_N=round(ref, 3), l_max_mm=round(r[k, ri["pv2_l_max"]], 4),
                         mcold_g=round(1e3 * r[k, ri["pv2_mcold"]], 2), aborted=int(r[k, ri["pcf_abt"]]),
                         released=int(r[k, ri["pcf_rel"]]), s5_modes=[round(r[k, ri[f"pv2_s5_{m}"]], 2) for m in range(4)]))
    out["checks"]["cold_flow_bound_at_hold"] = dict(
        expect="peak cold-flow thrust = bound at the 62.5 N lift and the onset tank pressure (12.5-13.3 N over 40-46.5 bar, "
               "Combustion log); the vehicle holds the drogue (abort) unless R2 releases", runs=rows,
        pass_=all(abs(x["Fcl_max_N"] - x["table_at_P0_N"]) < 0.02 * x["table_at_P0_N"] for x in rows))
    for k, rc in enumerate(recs):
        sel = (rc[:, ci["t"]] >= r[k, ri["pcf_t0"]] - 0.05) & (rc[:, ci["t"]] <= r[k, ri["pcf_t0"]] + 0.9)
        out["checks"][f"cold_flow_trace_run{k}"] = dict(
            t=[round(x, 3) for x in rc[sel, ci["t"]]], Fcmd=[round(x, 2) for x in rc[sel, ci["Fcmd"]]],
            F=[round(x, 2) for x in rc[sel, ci["F"]]], Fcl=[round(x, 2) for x in rc[sel, ci["Fcl"]]],
            lift_mm=[round(x, 4) for x in rc[sel, ci["lift"]]], pfa=[round(x, 2) for x in rc[sel, ci["pfa"]]],
            phase=[int(x) for x in rc[sel, ci["phase"]]])
    # (3) release hold 0.22 s (Pc valid, unpurged start nrLO|none): release no earlier than E2 + 0.22 s
    r, _ = fly_case("A1_none", "nrLO", "none", "", dict(pv2_on=1, pv2_rh=0.22), 8, 0)
    r0, _ = fly_case("A1_none", "nrLO", "none", "", {}, 8, 0)
    out["checks"]["release_hold_0p22"] = dict(
        expect="rel_t >= 0.22 s with the hold (Pc branch at E2 otherwise)",
        rel_t_hold=[round(x, 4) for x in r[:, ri["rel_t"]]], rel_t_no_hold=[round(x, 4) for x in r0[:, ri["rel_t"]]],
        blocked=[int(x) for x in r[:, ri["pv2_rhb"]]],
        pass_=bool(np.all((r[:, ri["rel_t"]] >= 0.22 - 1e-6) | (r[:, ri["rel_t"]] < 0))))
    # (4) statistics mode: no release with pcf_Facc 1e9, window to 0.8 s, statistics recorded for all four modes
    stt = dict(PCF2, pcf_k=0.875, pcf_Facc=1e9, pcf_tmax=0.8, pv2_on=1, pv2_hold=1)
    r, _ = fly_case("A1_none", "pw", "G73", "", stt, 4, 0)
    out["checks"]["stats_mode"] = dict(
        expect="pcf_rel 0, pcf_abt 1, s5 / s8 finite for the 4 modes",
        s5=[[round(r[k, ri[f"pv2_s5_{m}"]], 2) for m in range(4)] for k in range(r.shape[0])],
        s8=[[round(r[k, ri[f"pv2_s8_{m}"]], 2) for m in range(4)] for k in range(r.shape[0])],
        pass_=bool(np.all(r[:, ri["pcf_rel"]] == 0) and np.all(r[:, ri["pcf_abt"]] > 0.5)
                   and np.all(r[:, [ri[f"pv2_s8_{m}"] for m in range(4)]] > -999.0)))
    out["all_pass"] = all(v.get("pass_", True) for v in out["checks"].values())
    json.dump(out, open(pout, "w"), indent=1)
    for k, v in out["checks"].items():
        if "pass_" in v:
            print(k, "PASS" if v["pass_"] else "FAIL", flush=True)
    print(json.dumps({k: v for k, v in out["checks"].items() if not k.startswith("cold_flow_trace")}, indent=1)[:6000])


if __name__ == "__main__":
    if sys.argv[1] == "fly":
        part_fly()
    elif sys.argv[1] == "compare":
        part_compare(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "func":
        part_func(sys.argv[2])
