"""rg04_b1_bound v1 (independent GNC review, 2026-10-13): does the B1 85 m dispersed sizing set bound the B1 62 m flights
with the regression band, on load metrics other than the engine-on counter?

Inputs (read only): the published Monte Carlo run tables (500 runs, seed 101, same draws in every case)
  62 m : regband/mc6_runs_rbl_B1_lead62_pc_k2_rb   (band + growth, J_ref of the no-band 62 m flight)
         regband/mc6_runs_tgl_B1_lead62_pc_k2_rb   (growth only)
  85 m : throat_growth/mc6_runs_tg_B1_none_k2_tg   (source of DC-B1 85 m p99 / max, no growth, no band)
         throat_growth/mc6_runs_tg_B1_pc_k2_tg     (source of the tg711 cycles, growth, no band)
         regband/mc6_runs_rb_B1_pc_k2_rb           (85 m with band + growth: NOT a sizing case, shown for reference)
Metrics per run: engine-on counter (burn_time), total propellant (prop_used), fuel burned (grain 0.404 kg - fuel_left),
N2O burned (prop_used - fuel burned), mean O/F, throat erosion integral (throat_J), oxidiser at end (reg_X_end).
Grain mass 0.404 kg: gnc.json v3 reference_vehicle (DATASHEET of the ledger v3d). The thermal / erosion relevance of each
metric is a Combustion / Mechanical judgement; this script only reports whether the 62 m values exceed the 85 m sizing values.
Output: rg04_b1_bound.json
"""
import csv
import gzip
import json
import os

import numpy as np

HUB = "/home/claude/work/shared-fallback/engine/01-systems-gnc/results"
HERE = os.path.dirname(os.path.abspath(__file__))
GRAIN = 0.404
CASES = {
    "62m_band_growth (rbl)": "regband/mc6_runs_rbl_B1_lead62_pc_k2_rb.csv.gz",
    "62m_growth_only (tgl)": "regband/mc6_runs_tgl_B1_lead62_pc_k2_rb.csv.gz",
    "85m_none (tg_B1_none_k2, DC p99/max source)": "throat_growth/mc6_runs_tg_B1_none_k2_tg.csv.gz",
    "85m_growth (tg_B1_pc_k2, tg711 source)": "throat_growth/mc6_runs_tg_B1_pc_k2_tg.csv.gz",
    "85m_band_growth (rb_B1_pc_k2, reference)": "regband/mc6_runs_rb_B1_pc_k2_rb.csv.gz",
}
DC = {  # duty_cycles_index_v3 (rev d) values of the sizing files
    "DC-B1_85m_p99_kest2_v3 (run 121)": dict(burn_time=21.734, prop_used=1.8102460118139654),
    "DC-B1_85m_max_kest2_v3 (run 211)": dict(burn_time=24.090, prop_used=1.9272730543889534),
    "DC-B1_85m_p99_kest2_tg711_v3 (run 264)": dict(burn_time=21.614, prop_used=1.860591653505506),
    "DC-B1_85m_max_kest2_tg711_v3 (run 211)": dict(burn_time=23.927, prop_used=1.9342270898989469),
}


def load(fn):
    with gzip.open(os.path.join(HUB, fn), "rt") as f:
        rows = list(csv.DictReader(f))
    g = lambda k: np.array([float(r[k]) if r.get(k) not in (None, "", "nan") else np.nan for r in rows])
    fuel = GRAIN - g("fuel_left")
    prop = g("prop_used")
    n2o = prop - fuel
    return dict(run=g("run"), ok=g("ok"), burn_time=g("burn_time"), prop_used=prop, fuel_burned=fuel, n2o_burned=n2o,
                of_mean=n2o / np.where(fuel > 1e-6, fuel, np.nan), throat_J=g("throat_J"), reg_X_end=g("reg_X_end"),
                reg_a=g("reg_a"), reg_n=g("reg_n"), h_max=g("h_max"), exhausted=g("exhausted"))


def q(x):
    x = x[np.isfinite(x)]
    if x.size == 0:
        return dict(p50=None, p99=None, max=None, min=None)
    return dict(p50=float(np.percentile(x, 50)), p99=float(np.percentile(x, 99)), max=float(np.max(x)), min=float(np.min(x)))


def main():
    D = {k: load(v) for k, v in CASES.items()}
    out = dict(script="rg04_b1_bound v1", inputs=CASES, grain_kg=GRAIN, metrics={}, dc_index_values=DC)
    for m in ("burn_time", "prop_used", "fuel_burned", "n2o_burned", "of_mean", "throat_J", "reg_X_end", "h_max"):
        out["metrics"][m] = {k: q(d[m]) for k, d in D.items()}
    # 62 m runs above the 85 m sizing values, metric by metric
    ref_none = D["85m_none (tg_B1_none_k2, DC p99/max source)"]
    ref_pc = D["85m_growth (tg_B1_pc_k2, tg711 source)"]
    rb62 = D["62m_band_growth (rbl)"]
    exceed = {}
    for m in ("burn_time", "prop_used", "fuel_burned", "n2o_burned", "throat_J", "of_mean"):
        p99_none = float(np.percentile(ref_none[m][np.isfinite(ref_none[m])], 99))
        mx_none = float(np.nanmax(ref_none[m]))
        p99_pc = float(np.percentile(ref_pc[m][np.isfinite(ref_pc[m])], 99))
        mx_pc = float(np.nanmax(ref_pc[m]))
        x = rb62[m]
        exceed[m] = dict(p99_85m_none=p99_none, max_85m_none=mx_none, p99_85m_growth=p99_pc, max_85m_growth=mx_pc,
                         n62_over_p99_85m_none=int(np.sum(x > p99_none)), n62_over_max_85m_none=int(np.sum(x > mx_none)),
                         n62_over_p99_85m_growth=int(np.sum(x > p99_pc)), n62_over_max_85m_growth=int(np.sum(x > mx_pc)),
                         max_62m=float(np.nanmax(x)))
    out["rbl_62m_vs_85m_sizing_population"] = exceed
    # the regression corners: fuel burned and O/F of the 62 m band runs by a-scale tercile
    a = rb62["reg_a"]
    terc = {}
    for lo, hi in ((0.6, 0.9), (0.9, 1.2), (1.2, 1.5001)):
        s = (a >= lo) & (a < hi)
        terc[f"a {lo}-{hi:.1f}"] = dict(n=int(np.sum(s)), fuel_burned=q(rb62["fuel_burned"][s]), of_mean=q(rb62["of_mean"][s]),
                                        n2o_burned=q(rb62["n2o_burned"][s]), burn_time=q(rb62["burn_time"][s]))
    out["rbl_by_a_scale"] = terc
    # the sizing files' own propellant numbers vs the 62 m population
    out["rbl_prop_used_over_DC_files"] = {k: int(np.sum(rb62["prop_used"] > v["prop_used"])) for k, v in DC.items()}
    with open(os.path.join(HERE, "rg04_b1_bound.json"), "w") as f:
        json.dump(out, f, indent=1)
    for m, v in out["metrics"].items():
        print(m)
        for k, s in v.items():
            if s["p50"] is None:
                print(f"   {k:45s} (column absent)")
                continue
            print(f"   {k:45s} p50 {s['p50']:.4f} p99 {s['p99']:.4f} max {s['max']:.4f} min {s['min']:.4f}")
    print(json.dumps(exceed, indent=1))
    print(json.dumps(terc, indent=1))
    print(out["rbl_prop_used_over_DC_files"])


if __name__ == "__main__":
    main()
