"""rg02_mc_repro v1 (independent GNC review, 2026-10-13): re-fly the first N runs of published Monte Carlo cases and compare
them field by field with the published run tables.

Method
  - The author's simulator and scripts are executed from a COPY (env RG_SIMCOPY, default the reviewer scratchpad copy). The
    script first checks that every *.py file of the copy is byte-identical (sha256) to the hub 01-systems-gnc/sim, so the
    hub is never written to (numba cache and interface snapshots go to the copy / RG_SCRATCH).
  - Interface set: env GNC_IFACE = a copy of iface_v3c; checked here against the hub interface files (sha256).
  - Case construction uses the author's own case builders (m2_relight_v28.case_over, m2_regband_mc.cases): this tests
    reproducibility of the published rows, not the correctness of the model (that is reviewed separately).
  - Draws: numpy default_rng(101) for N = 500 runs (the add-on generators 20261013 / 20261017 / 20261018 as in run6.draw);
    the first n runs are flown and compared.
Output: rg02_mc_repro.json next to this script.
Run (one core): NUMBA_NUM_THREADS=1 nice -n 10 /opt/engine-venv/bin/python -I rg02_mc_repro.py [case:n ...]
"""
import csv
import gzip
import hashlib
import json
import os
import sys
import time

sys.dont_write_bytecode = True
SCR = os.environ.get("RG_SCRATCH", "/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad")
COPY = os.environ.get("RG_SIMCOPY", f"{SCR}/simcopy")
HUB = "/home/claude/work/shared-fallback/engine"
HUBSIM = f"{HUB}/01-systems-gnc/sim"
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("GNC_IFACE", f"{SCR}/iface_v3c")
os.environ.setdefault("GNC_ACT_RATE", f"{SCR}/iface_v3c/actuator_rate_check_v2.json")
os.environ.setdefault("NUMBA_CACHE_DIR", f"{SCR}/numba_cache")
os.environ.setdefault("NUMBA_NUM_THREADS", "1")
for k in ("GNC_OUT", "GNC_V28_OUT", "GNC_RB_OUT", "GNC_TG_OUT"):
    os.environ[k] = f"{SCR}/out/{k.lower()}"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def check_copy():
    bad = []
    n = 0
    for sub in ("gncsim", "scripts"):
        for fn in sorted(os.listdir(f"{HUBSIM}/{sub}")):
            if fn.endswith(".py"):
                n += 1
                if sha(f"{HUBSIM}/{sub}/{fn}") != sha(f"{COPY}/{sub}/{fn}"):
                    bad.append(f"{sub}/{fn}")
    for fn in ("data/regband/regband_model_v1.json", "data/tailoff/tailoff_fit_v1.json"):
        n += 1
        if sha(f"{HUBSIM}/{fn}") != sha(f"{COPY}/{fn}"):
            bad.append(fn)
    ifc = {}
    for fn in ("combustion.json", "mechanical.json", "electronics.json"):
        ifc[fn] = sha(f"{os.environ['GNC_IFACE']}/{fn}") == sha(f"{HUB}/interfaces/{fn}")
    return dict(files_checked=n, mismatched=bad, iface_identical_to_hub=ifc)


def rows(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:
        return list(csv.DictReader(f))


def compare(pub_rows, new_rows):
    keys = [k for k in new_rows[0].keys() if k in pub_rows[0]]
    maxd = {}
    ok_mis = 0
    n_exact_rows = 0
    for a, b in zip(pub_rows, new_rows):
        row_exact = True
        if int(float(a["ok"])) != int(b["ok"]):
            ok_mis += 1
        for k in keys:
            try:
                x, y = float(a[k]), float(b[k])
            except (TypeError, ValueError):
                continue
            if x != x and y != y:
                continue
            d = abs(x - y)
            rel = d / max(abs(x), 1e-12)
            if d > 0:
                row_exact = False
            if k not in maxd or rel > maxd[k]:
                maxd[k] = rel
        n_exact_rows += int(row_exact)
    worst = sorted(maxd.items(), key=lambda t: -t[1])[:6]
    return dict(n=len(new_rows), fields=len(keys), ok_mismatches=ok_mis, rows_bit_identical=n_exact_rows,
                worst_relative_field_diffs=worst)


def main():
    t0 = time.time()
    chk = check_copy()
    out = dict(script="rg02_mc_repro v1", copy=COPY, copy_check=chk, cases={})
    if chk["mismatched"]:
        print("COPY DIFFERS FROM HUB", chk["mismatched"])
        out["aborted"] = "copy differs"
        json.dump(out, open(os.path.join(HERE, "rg02_mc_repro.json"), "w"), indent=1)
        return
    sys.path.insert(0, COPY)
    sys.path.insert(0, f"{COPY}/scripts")
    import numpy as np
    from gncsim import run6 as R
    import m2_relight_v28 as RV
    import m2_regband_mc as RBM
    req = sys.argv[1:] or ["v28_liq_p0.81_A1_none_k2:100", "v28_fault_p1.41_A1_none_k2:60", "rbl_B1_lead62_pc_k2:100"]
    tabs = RV.e0e2_tables()
    for item in req:
        name, n = item.split(":")
        n = int(n)
        t1 = time.time()
        if name.startswith("v28_"):
            parts = name.split("_")             # v28_<state>_p<plan>_<base...>_k2
            st, plan = parts[1], float(parts[2][1:])
            base = "_".join(parts[3:-1])
            if st == "fault":
                over = RV.case_over(base, None, plan, tabs, fixed=RV.SEQ_FAULT)
            elif st.startswith("fs"):
                over = RV.case_over(base, st[2:], plan, tabs, add=RV.PREP_RERUN)
            else:
                over = RV.case_over(base, st, plan, tabs)
            pub = rows(f"{HUB}/01-systems-gnc/results/relight_v28/mc6_runs_{name}_v28.csv.gz")
        else:
            over = RBM.cases(None)[name][0]
            pub = rows(f"{HUB}/01-systems-gnc/results/regband/mc6_runs_{name}_rb.csv.gz")
        over = dict(over)
        m = float(over.pop("m_fixed"))
        cfg = R.cfg_of(**dict(over, m_n2o=m))
        D = R.draw(np.random.default_rng(101), 500, cfg)
        new = []
        for i in range(n):
            res = R.run_one(cfg, D[i])
            new.append(R.flat_row(i, D[i], res, R.success(res), cfg))
        cmp_ = compare(pub[:n], new)
        cmp_["cpu_s"] = time.time() - t1
        cmp_["P_published_first_n"] = float(np.mean([float(r["ok"]) for r in pub[:n]]))
        cmp_["P_reflown_first_n"] = float(np.mean([r["ok"] for r in new]))
        out["cases"][name] = cmp_
        print(name, json.dumps(cmp_), flush=True)
        json.dump(out, open(os.path.join(HERE, "rg02_mc_repro.json"), "w"), indent=1)
    out["total_s"] = time.time() - t0
    json.dump(out, open(os.path.join(HERE, "rg02_mc_repro.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
