"""m2_bitcheck_v211 v1.0 (GNC rev3, 2026-10-13): sim6 / run6 v2.11-dev (amendment L, flt_dla) against v2.10-dev.

Part A (off = identical): the same cases are flown in two trees (GNC_TREE = gnc_dev4 with sim6 v2.10-dev 1f92061d41db894a, then
gnc_dev5 with sim6 v2.11-dev) with flt_dla at its default (-1, off): the decided A1 path (records), the R2 flame-out path, the
unpurged nrLO start, and the stuck-pintle fault of amendment F on all five onsets with every detector armed (A1 and B1, Pc
valid and Pc lost, encoder-visible and linkage failure, 670 and 876 N) plus a MISS arm (detectors off, records). Every result
common to both versions and every common record column must be bit-identical.
Part B (functional, gnc_dev5 only): with every detector off and flt_dla 0.5 the decision (source 5) falls 0.5 s (+- one step)
after the plateau onset whenever the engine is still lit then, never before the plateau; flt_dla 0 decides at the plateau
onset; the MV seats abt_lat + abt_seat after the decision; a run whose flight software shut the engine down before the
allowance has no forced decision in that activation (plateau clock restarts at a re-activation).
Usage: GNC_TREE=<tree> GNC_BC_OUT=<npz> python m2_bitcheck_v211.py fly   (once per tree), then
       python m2_bitcheck_v211.py compare <npz v2.10> <npz v2.11> <out json>; python m2_bitcheck_v211.py func <out json>.
Env as m2r3_env.sh (strict mode, pins_rev3). SIM only."""
import hashlib
import json
import os
import sys
import numpy as np

TREE = os.environ.get("GNC_TREE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, TREE)
sys.path.insert(0, os.path.join(TREE, "scripts"))
import m2_rg01_refly as F  # noqa: E402
import m2_fault_f as FF  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_bitcheck_v211 v1.0"
S = "/home/claude/work/space/out"
PCF2 = dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2)
CASES = [  # name, base, state, purge, plateau, extra, n runs, records
    ("dec_pw", "A1_none", "pw", "G73", "", {}, 12, 2),
    ("pcfR2fo", "A1J_pc", "pw", "G73", "", dict(PCF2, pcf_fo=1), 8, 1),
    ("nrLO_none", "A1_none", "nrLO", "none", "", {}, 6, 0),
]
FCASES = [  # name, onset, level, branch, kind, n runs, records
    ("A1asc_L670_Lhi", "A1asc", "L670", "Lhi_blind", "det", 12, 1),
    ("A1asc_L876_Venc", "A1asc", "L876", "Venc", "det", 8, 0),
    ("A1land_L670_Llo_enc", "A1land", "L670", "Llo_enc", "det", 8, 0),
    ("B1asc_L670_Vblind", "B1asc", "L670", "Vblind", "det", 8, 0),
    ("B1floor_L670_Lhi", "B1floor", "L670", "Lhi_blind", "det", 12, 1),
    ("B1land_L876_Venc", "B1land", "L876", "Venc", "det", 8, 0),
    ("B1floor_L670_MISS", "B1floor", "L670", "Lhi_blind", "miss", 8, 1),
]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def fly_case(base, st, pu, pl, ex, n, nrec):
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
        r, rec, info = R.fly(c, disp, nrec=(4500 if i < nrec else 10))
        res.append([r[k] for k in s6.RES_NAMES])
        if i < nrec:
            recs.append(rec)
    return np.array(res), recs


def fly_fault(on, lv, br, kind, n, nrec, extra=None):
    """The m2_fault_f v1.1 arm (same draws, onsets, frame phases), with optional extra parameters."""
    prof, ph, _ = FF.ONS[on]
    F_, rate_ = FF.LEV[lv]
    sk, pcl, enc = FF.BR[br]
    if FF.MV.COMB is None:
        FF.MV.COMB = FF.MV.comb_draws(500)
    jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
    FF.MV.TG_JREF_DEFAULT = float(jr["A1" if prof == "A1" else "B1"])
    cfg, D = FF.cfg_for(prof, "V" if sk == "V" else "L")
    spec = FF.spec_of(sk)
    tt, fph = FF.onset_draws(on, n)
    res, recs = [], []
    for i in range(n):
        c, disp = FF.MV.run_cfg_case(cfg, D[i], spec, i, "comb")
        c = dict(c, flt_on=1, flt_ph=ph, flt_t=float(tt[i]), flt_F=F_, flt_rate=rate_, flt_enc=enc, flt_pcl=pcl,
                 fct_ph=float(fph[i]), fct_comp=1)
        if kind in ("miss", "dla"):
            c.update(det_fct=0, det_op=0, det_pf=0)
        if extra:
            c.update(extra)
        r, rec, info = R.fly(c, disp, nrec=(6000 if i < nrec else 10))
        res.append([r[k] for k in s6.RES_NAMES])
        if i < nrec:
            recs.append(rec)
    return np.array(res), recs


def part_fly():
    out = {}
    for name, base, st, pu, pl, ex, n, nrec in CASES:
        r, recs = fly_case(base, st, pu, pl, ex, n, nrec)
        out[f"{name}|res"] = r
        for k, rc in enumerate(recs):
            out[f"{name}|rec{k}"] = rc
        print(name, "done", flush=True)
    for name, on, lv, br, kind, n, nrec in FCASES:
        r, recs = fly_fault(on, lv, br, kind, n, nrec)
        out[f"{name}|res"] = r
        for k, rc in enumerate(recs):
            out[f"{name}|rec{k}"] = rc
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
    for name in [c[0] for c in CASES] + [c[0] for c in FCASES]:
        A = a[f"{name}|res"][:, ia_r]; B = b[f"{name}|res"][:, ib_r]
        same = bool(np.array_equal(A, B, equal_nan=True))
        nd = int(np.sum(~((A == B) | (np.isnan(A) & np.isnan(B)))))
        recs = []
        k = 0
        while f"{name}|rec{k}" in a.files and f"{name}|rec{k}" in b.files:
            X = a[f"{name}|rec{k}"]; Y = b[f"{name}|rec{k}"]
            ok = X.shape[0] == Y.shape[0] and np.array_equal(X[:, ia_c], Y[:, ib_c], equal_nan=True)
            recs.append(dict(rows=int(X.shape[0]), identical=bool(ok)))
            same = same and ok
            k += 1
        rep["cases"][f"{name}|v2.11 flt_dla off"] = dict(runs=int(A.shape[0]), results_identical=bool(np.array_equal(A, B, equal_nan=True)),
                                                         differing_values=nd, records=recs)
        rep["all_identical"] = rep["all_identical"] and same
    json.dump(rep, open(pout, "w"), indent=1)
    print(json.dumps(rep, indent=1)[:2500])
    print("ALL IDENTICAL" if rep["all_identical"] else "DIFFERENCES FOUND", flush=True)


def part_func(pout):
    assert "flt_dla" in s6.PAR_NAMES, "functional part needs the v2.11-dev tree"
    ri = {k: i for i, k in enumerate(s6.RES_NAMES)}
    ci = {k: i for i, k in enumerate(s6.REC_NAMES)}
    dt = float(R.DEF.get("dt", 0.001)) if hasattr(R, "DEF") else 0.001
    out = dict(version=VERSION, sim=s6.SIM6_VERSION, sim6_sha16=sha16(s6.__file__), run6_sha16=sha16(R.__file__), checks={})
    lat, seat = float(R.DEF["abt_lat"]), float(R.DEF["abt_seat"])
    allp = True
    for on, br in (("A1asc", "Lhi_blind"), ("A1land", "Vblind"), ("B1asc", "Vblind"), ("B1floor", "Lhi_blind"), ("B1land", "Vblind")):
        for dla in (0.5, 0.0):
            r, recs = fly_fault(on, "L670", br, "dla", 10, 2, dict(flt_dla=dla))
            tpl, dec, src, seat_t = r[:, ri["flt_tpl"]], r[:, ri["flt_tdec"]], r[:, ri["flt_src"]], r[:, ri["flt_tseat"]]
            t0 = r[:, ri["flt_t0"]]
            forced = dec >= 0.0
            d_ = dec - tpl
            ok_t = bool(np.all(np.abs(d_[forced] - dla) <= 1.5e-3))
            ok_src = bool(np.all(src[forced] == 5.0))
            ok_seat = bool(np.all(np.abs((seat_t - dec)[forced & (seat_t >= 0)] - lat - seat) <= 2.5e-3))
            ok_pl = bool(np.all(tpl[t0 >= 0] >= t0[t0 >= 0]))
            unforced = [dict(run=int(k), t0=float(t0[k]), tpl=float(tpl[k]), t_shutdown=float(r[k, ri["flt_tsd"]]),
                             activations=int(r[k, ri["flt_n_on"]]), end=int(r[k, ri["flt_end"]]), t_meco=float(r[k, ri["t_meco"]]))
                        for k in np.where((t0 >= 0) & ~forced)[0]]
            tr = []
            for k, rc in enumerate(recs):
                if not forced[k]:
                    continue
                sel = (rc[:, ci["t"]] >= t0[k] - 0.02) & (rc[:, ci["t"]] <= dec[k] + 0.3)
                tr.append(dict(run=k, t=[round(x, 3) for x in rc[sel, ci["t"]][::5]], F=[round(x, 1) for x in rc[sel, ci["F"]][::5]],
                               vz=[round(x, 2) for x in rc[sel, ci["vz"]][::5]], flts=[int(x) for x in rc[sel, ci["flts"]][::5]]))
            e = dict(n=int(len(r)), onset_reached=int(np.sum(t0 >= 0)), forced=int(forced.sum()),
                     dec_minus_plateau_s=[round(float(x), 4) for x in d_[forced]],
                     plateau_minus_onset_s=[round(float(x), 4) for x in (tpl - t0)[t0 >= 0]],
                     seat_minus_dec_s=[round(float(x), 4) for x in (seat_t - dec)[forced & (seat_t >= 0)]],
                     unforced=unforced, decision_time_ok=ok_t, source_ok=ok_src, seat_ok=ok_seat, plateau_after_onset=ok_pl,
                     traces=tr[:1])
            e["pass_"] = ok_t and ok_src and ok_seat and ok_pl
            allp = allp and e["pass_"]
            out["checks"][f"{on}|{br}|dla{dla}"] = e
            print(f"{on}|{br}|dla{dla}: forced {e['forced']}/{e['onset_reached']} dec-pl {e['dec_minus_plateau_s'][:4]} "
                  f"seat-dec {e['seat_minus_dec_s'][:3]} unforced {len(unforced)} -> {'PASS' if e['pass_'] else 'FAIL'}", flush=True)
    out["all_pass"] = allp
    json.dump(out, open(pout, "w"), indent=1)
    print("ALL PASS" if allp else "FAILURES", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "fly":
        part_fly()
    elif sys.argv[1] == "compare":
        part_compare(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "func":
        part_func(sys.argv[2])
