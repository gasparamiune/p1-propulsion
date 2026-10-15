"""m2_bitcheck_v212 v1.1 (GNC rev3, 2026-10-13): sim6 / run6 v2.12-dev (amendment V3, pv2_rhF) against v2.11-dev.

History: v1.0 (61f6c1ae37ec5273, snapshot rev3_notes/m2_bitcheck_v212_v1.0_snapshot.py) failed its own functional part B
(bitcheck_v212_func.json d1165a5ebed4fd0f, kept): it required the recorded command to equal pv2_rhF 'nowhere else' in the
flight, but the guidance itself commands exactly 500 N on the ascent burn (phase 1, ceiling) and, through the command
quantisation, exactly 200 N on isolated landing-burn records (phase 6) (probe rev3_notes/v212_func_probe.py). That is a test
criterion defect, not a patch defect; the hold blocks were 15 / 9 / 20 records (0.30 / 0.18 / 0.40 s at 20 ms records).
v1.1 checks the block after the relight (t >= t_relight): the first contiguous block of Fcmd == pv2_rhF after the relight
has length pv2_rh +- two records, and every other record at that value after the relight lies outside the block and its
neighbours and in a later phase (reported, with phase and time). Part A (off = identical) is unchanged and is not re-flown.

Part A (off = identical): the same cases are flown in two trees (GNC_TREE = gnc_dev5 with sim6 v2.11-dev 8ae4ecdc5ac910dc,
then gnc_dev6 with sim6 v2.12-dev) with pv2_rhF at its default (0, off): the decided A1 path (records), the R2 flame-out path,
the unpurged nrLO start, the V2 release hold (pv2_rh 0.22, records), the V2 start-level hold with the cold-flow bound
(records), and the stuck-pintle fault of amendment F on five onsets (as m2_bitcheck_v211). Every result common to both
versions and every common record column must be bit-identical.
Part B (functional, gnc_dev6 only): nrLO|none with (pv2_rh, pv2_rhF) = (0.30 s, 200 N), (0.19 s, 500 N), (0.40 s, 200 N): the
release comes pv2_rh after E2 (+ one step), the profile time equals pv2_rh within 2 ms, the recorded ECU command equals pv2_rhF
on one contiguous block of length pv2_rh (+- two 20 ms records) after the relight (v1.1 criterion, see History); with Pc
invalid and the V2 start-level hold armed the command stays at 62.5 N (V2 (i) takes precedence).
Usage: GNC_TREE=<tree> GNC_BC_OUT=<npz> python m2_bitcheck_v212.py fly   (once per tree), then
       python m2_bitcheck_v212.py compare <npz v2.11> <npz v2.12> <out json>; python m2_bitcheck_v212.py func <out json>.
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
import m2_bitcheck_v211 as B11  # noqa: E402  (fly_case / fly_fault / FCASES of the v2.11 check, unchanged)
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_bitcheck_v212 v1.1"
PCF2 = dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2)
CASES = B11.CASES + [
    ("nrLO_rh220", "A1_none", "nrLO", "none", "", dict(pv2_on=1, pv2_rh=0.22), 6, 2),
    ("pcfR2_hold_fo_cb", "A1J_pc", "pw", "G73", "", dict(PCF2, pcf_fo=1, pv2_on=1, pv2_hold=1, pv2_Fh=62.5, pv2_cold=1,
                                                        pcf_Facc=1e9, pcf_tmax=0.8), 6, 1),
]
FCASES = B11.FCASES


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def part_fly():
    out = {}
    for name, base, st, pu, pl, ex, n, nrec in CASES:
        r, recs = B11.fly_case(base, st, pu, pl, ex, n, nrec)
        out[f"{name}|res"] = r
        for k, rc in enumerate(recs):
            out[f"{name}|rec{k}"] = rc
        print(name, "done", flush=True)
    for name, on, lv, br, kind, n, nrec in FCASES:
        r, recs = B11.fly_fault(on, lv, br, kind, n, nrec)
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
        A = a[f"{name}|res"][:, ia_r]; Bm = b[f"{name}|res"][:, ib_r]
        same = bool(np.array_equal(A, Bm, equal_nan=True))
        nd = int(np.sum(~((A == Bm) | (np.isnan(A) & np.isnan(Bm)))))
        recs = []
        k = 0
        while f"{name}|rec{k}" in a.files and f"{name}|rec{k}" in b.files:
            X = a[f"{name}|rec{k}"]; Y = b[f"{name}|rec{k}"]
            ok = X.shape[0] == Y.shape[0] and np.array_equal(X[:, ia_c], Y[:, ib_c], equal_nan=True)
            recs.append(dict(rows=int(X.shape[0]), identical=bool(ok)))
            same = same and ok
            k += 1
        rep["cases"][f"{name}|v2.12 pv2_rhF off"] = dict(runs=int(A.shape[0]), results_identical=bool(np.array_equal(A, Bm, equal_nan=True)),
                                                         differing_values=nd, records=recs)
        rep["all_identical"] = rep["all_identical"] and same
    json.dump(rep, open(pout, "w"), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "cases"}, indent=1))
    for k, v in rep["cases"].items():
        print(k, v["results_identical"], v["differing_values"], [r["identical"] for r in v["records"]])
    print("ALL IDENTICAL" if rep["all_identical"] else "DIFFERENCES FOUND", flush=True)


def part_func(pout):
    assert "pv2_rhF" in s6.PAR_NAMES, "functional part needs the v2.12-dev tree"
    ri = {k: i for i, k in enumerate(s6.RES_NAMES)}
    ci = {k: i for i, k in enumerate(s6.REC_NAMES)}
    out = dict(version=VERSION, sim=s6.SIM6_VERSION, sim6_sha16=sha16(s6.__file__), run6_sha16=sha16(R.__file__), checks={})
    allp = True
    for H, Fp in ((0.30, 200.0), (0.19, 500.0), (0.40, 200.0)):
        r, recs = B11.fly_case("A1_none", "nrLO", "none", "", dict(pv2_on=1, pv2_rh=H, pv2_rhF=Fp), 6, 6)
        relt, prof, fmx = r[:, ri["rel_t"]], r[:, ri["pv3_rhp_s"]], r[:, ri["pv3_Frhp_max"]]
        blocks = []
        for j, rc in enumerate(recs):
            t = rc[:, ci["t"]]
            dt_rec = float(np.median(np.diff(t)))
            on = (np.abs(rc[:, ci["Fcmd"]] - Fp) < 1e-9) & (t >= r[j, ri["t_relight"]])
            idx = np.where(on)[0]
            if not len(idx):
                blocks.append(dict(n_records=0, ok=False))
                continue
            brk = np.where(np.diff(idx) > 1)[0]
            first = idx[:brk[0] + 1] if len(brk) else idx
            rest = idx[len(first):]
            ph0 = float(rc[first[0], ci["phase"]])
            rest_ok = bool(np.all(rest > first[-1] + 1) and np.all(rc[rest, ci["phase"]] > ph0))
            b_ = dict(n_records=int(len(first)), rec_dt=round(dt_rec, 4), length_s=round(len(first) * dt_rec, 3),
                      t_start=round(float(t[first[0]]), 3), t_end=round(float(t[first[-1]]), 3), phase=ph0,
                      F_truth_at_start=round(float(rc[first[0], ci["F"]]), 1),
                      F_truth_max_in_block=round(float(rc[first, ci["F"]].max()), 1),
                      cmd_after_block=round(float(rc[first[-1] + 1, ci["Fcmd"]]), 1) if first[-1] + 1 < len(rc) else None,
                      other_records_at_value_after_relight=[(round(float(t[k]), 2), float(rc[k, ci["phase"]])) for k in rest],
                      other_records_later_phase=rest_ok)
            b_["ok"] = bool(abs(b_["length_s"] - H) <= 2 * dt_rec + 1e-9 and rest_ok)
            blocks.append(b_)
        ok_rel = bool(np.all((relt >= H - 1e-6) & (relt <= H + 1.5e-3)))
        ok_prof = bool(np.all(np.abs(prof - H) <= 2.0e-3))
        ok_blk = all(b_["ok"] for b_ in blocks)
        e = dict(H=H, F_profile=Fp, rel_t=[round(float(x), 4) for x in relt], profile_s=[round(float(x), 4) for x in prof],
                 F_truth_max=[round(float(x), 1) for x in fmx], blocks=blocks, release_ok=ok_rel, profile_time_ok=ok_prof,
                 command_block_ok=ok_blk, ok=[bool(x) for x in r[:, ri["ok"]] > 0.5] if "ok" in ri else None)
        e["pass_"] = ok_rel and ok_prof and ok_blk
        allp = allp and e["pass_"]
        out["checks"][f"nrLO|rh{H}|F{Fp:g}"] = e
        print(f"rh {H} F {Fp}: rel_t {e['rel_t'][:3]} profile {e['profile_s'][:3]} Fmax {e['F_truth_max'][:3]} blocks "
              f"{[(b_['n_records'], b_.get('length_s'), b_.get('t_start'), len(b_.get('other_records_at_value_after_relight', []))) for b_ in blocks]} "
              f"-> {'PASS' if e['pass_'] else 'FAIL'}", flush=True)
    # precedence: Pc invalid with the V2 start-level hold armed and the V3 profile requested -> the command stays at 62.5 N
    r, recs = B11.fly_case("A1J_pc", "pw", "G73", "", dict(PCF2, pv2_on=1, pv2_hold=1, pv2_Fh=62.5, pv2_rh=0.30, pv2_rhF=200.0,
                                                          pcf_Facc=1e9, pcf_tmax=0.8), 4, 4)
    n200 = [int(np.sum(np.abs(rc[:, ci["Fcmd"]] - 200.0) < 1e-9)) for rc in recs]
    n625 = [int(np.sum(np.abs(rc[:, ci["Fcmd"]] - 62.5) < 1e-9)) for rc in recs]
    e = dict(records_at_200N=n200, records_at_62p5N=n625, pass_=bool(all(x == 0 for x in n200) and all(x > 0 for x in n625)))
    allp = allp and e["pass_"]
    out["checks"]["precedence_V2_hold_over_V3"] = e
    print("precedence:", e, flush=True)
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
