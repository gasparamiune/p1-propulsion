"""m2_release_rule v1.1 (GNC, 2026-10-13): coordinator relay of the light-detection fix (2026-10-13): does the adopted drogue
release rule move P? sim6 v2.8-dev amendment R.

Rule change: drogue release on E2 (relative light confirmation: Pc rise >= 0.8 bar above the pre-lift baseline, held 10 ms;
Combustion ignition_detect_v2p4: E2 14.0-15.5 ms after main ignition, against 18.5 ms - 0.60 s on the old 3.0 bar absolute
rule) AND measured Pc >= 3.0 bar abs (fixed, not tied to the floor). The v2.8 6-DOF released at F > 0.5 x floor (50 N at the
A1 floor 0.20: map Pc 3.72 bar); the new rule releases at the map thrust of 3.0 bar abs (rel_F, run6 DERIVED, 37.2 N).
E2 timing in the 6-DOF: the light is drawn from RC-03 E0 -> E2 on the OLD rule (start_latency_v2p4: confirmation 19.5-25.5 ms
after main ignition in its Part 1 runs); the relative rule confirms 14.0-15.5 ms after main ignition, so E2 and the ramp it
starts come 4-11.5 ms earlier. Arms: rel1 = new rule, light unchanged; rel1_e2m10 = new rule and the light 10 ms earlier (the
early side of the 4-11.5 ms shift); v1.1: rel1_dt400 = new rule with the release held 0.4 s after the 6-DOF light (bracket of
the fuel-starved start relayed by the coordinator: lit Pc 2.4-3.4 bar abs for 0.1-0.4 s, below the 3.0 bar release threshold
for up to 0.4 s; the 6-DOF thrust ramp itself is unchanged, so this isolates the longer drogue attachment, not the lower
thrust of the plateau, which belongs to the RG-01 start-transient re-fly).
Bases (seed 101, 500 runs, paired exact McNemar against the stored v2.8 tables): A1_none and A1J_pc, liquid plan 0.81 s
(relight NOT CLOSED, RG-01: this is a rule-sensitivity check, not a relight acceptance).
Output: <out>/rel_<base>_<arm>.csv, <out>/release_rule.json"""
import csv
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_REL_OUT", f"{S}/release_rule")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_eng03_rate as E  # noqa: E402
import m2_mc6 as M  # noqa: E402

VERSION = "m2_release_rule v1.1"
PARTS = os.environ.get("GNC_REL_PARTS", "mc,eval").split(",")
SPLIT = os.environ.get("GNC_REL_SPLIT", "0/1")
N = 500
BASES = ("A1_none", "A1J_pc")
ARMS = {"rel1": dict(rel_mode=1), "rel1_e2m10": dict(rel_mode=1, _dt_ign=-0.010), "rel1_dt400": dict(rel_mode=1, rel_dt=0.4)}


def cfg_of(base):
    over, csvp, bj = E.base_ref(base)
    m = json.load(open(bj))["m_n2o_mc_kg"]
    return R.cfg_of(**dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(m))), csvp


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    jobs = [(b, a) for b in BASES for a in ARMS]
    for base, arm in jobs[k::n]:
        p = os.path.join(OUT, f"rel_{base}_{arm}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_REL_FORCE") != "1":
            print("exists", base, arm, flush=True)
            continue
        cfg, _ = cfg_of(base)
        D = R.draw(np.random.default_rng(101), N, cfg)
        t0 = time.time()
        rows = []
        for i in range(N):
            c, disp = R.run_cfg(cfg, D[i])
            c.update({kk: v for kk, v in ARMS[arm].items() if not kk.startswith("_")})
            if "_dt_ign" in ARMS[arm]:
                c["t_ign"] = float(c["t_ign"]) + ARMS[arm]["_dt_ign"]
            res = R.fly(c, disp, nrec=10)[0]
            row = R.flat_row(i, D[i], res, R.success(res), cfg)
            row.update(rel_t=float(res["rel_t"]), rel_Fpc=float(res["rel_Fpc"]))
            rows.append(row)
        M.write_csv(p, rows)
        print(f"{base} {arm}: P {np.mean([r['ok'] for r in rows]):.3f} ({time.time() - t0:.0f} s)", flush=True)


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
    return dict({f"p{q:02d}": float(np.percentile(x, q)) for q in qs}, min=float(x.min()), max=float(x.max()), n=int(x.size))


def part_eval():
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[1].strip(), cases={})
    for base in BASES:
        cfg, refp = cfg_of(base)
        ref = rows_csv(refp)
        par = R.build(dict(cfg, rel_mode=1))[0]
        relF = float(par[{n: i for i, n in enumerate(s6.PAR_NAMES)}["rel_F"]])
        for arm in ARMS:
            rows = rows_csv(os.path.join(OUT, f"rel_{base}_{arm}.csv"))
            if not rows or not ref:
                continue
            ok = col(rows, "ok") > 0.5
            okr = col(ref, "ok") > 0.5
            rt = col(rows, "rel_t")
            e = dict(arm=ARMS[arm], rel_F_N=relF, vs_stored=mcnemar(okr, ok),
                     P_wilson=[float(x) for x in R.wilson(int(ok.sum()), len(ok))],
                     release_after_light_ms=pct(1e3 * rt[rt >= 0]), released_runs=int(np.sum(rt >= 0)),
                     td_vz=pct(col(rows, "td_vz")), td_vh=pct(col(rows, "td_vh")),
                     td_vz_shift=pct(col(rows, "td_vz") - col(ref, "td_vz")),
                     liq_left_shift_g=pct(1e3 * (col(rows, "liq_left") - col(ref, "liq_left"))),
                     failures=[int(r["run"]) for r, o in zip(rows, ok) if not o])
            out["cases"][f"{base}|{arm}"] = e
    with open(os.path.join(OUT, "release_rule.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for k, v in out["cases"].items():
        m_ = v["vs_stored"]
        print(f"{k:22s} P {m_['P_case']:.3f} vs {m_['P_ref']:.3f} (-{m_['lost']}/+{m_['gained']}, p {m_['p_exact']:.3g}) release "
              f"after light p50/p99 {v['release_after_light_ms']['p50']:.1f}/{v['release_after_light_ms']['p99']:.1f} ms "
              f"(rel_F {v['rel_F_N']:.1f} N) | td_vz shift p01/p99 {v['td_vz_shift']['p01']:+.3f}/{v['td_vz_shift']['p99']:+.3f}",
              flush=True)


def main():
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()
