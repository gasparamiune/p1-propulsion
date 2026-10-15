"""REV-GNC-5 v09: independent recomputation of P5 (RG-16 allowance) from the staged rev3 data.
(1) Latency consequence from the staged p5 tables: P (landing criteria), velocity gained during the 0.5 s allowance
    (flt_vzdec - flt_vzpl), apex p99 (h_max) per arm.
(2) Windowed miss-side budget from the staged frame streams (rev3/streams/rg16w/*.npz: fa_<variant>_i, ft_i, sel_i) with
    the reviewer's own code (REV-GNC-3 detector-output form, rewritten here): r = fa/ft - 1; H1 = min of r over 3 consecutive
    selected frames; MW = max of H1 over W consecutive valid positions; s = (p50 - p1)/2.326; total = 3 hypot(s, s_mass) +
    bias (+ max(0, shift) in the strict form, shift = single-frame median - windowed median); passes iff 670 (1 - total) >
    650 (allowed 2.985 %).  A1 terms from the staged rev2 rg16_fct_terms_v2.json; B1 random/bias from the staged rev1
    mest_budget_v1.json, B1 |b_sys median| taken from the author's rg16w.json (AUTHOR INPUT, <= 0.05 pp; its source file is
    not in the hub).  SIM streams on ASSUMED noise models -> DERIVED.  Usage: python -I v09_p5.py <out.json>"""
import json, sys, os, gzip, csv
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv
HUB = "/home/claude/work/shared-fallback/engine"
R3 = f"{HUB}/01-systems-gnc/staging_v3.1/rev3"
ALLOW = 1.0 - 650.0 / 670.0
Z = 2.326
T2 = json.load(open(f"{HUB}/01-systems-gnc/staging_v3.1/rev2/results/rg16_v2/rg16_fct_terms_v2.json"))
MB = json.load(open(f"{HUB}/01-systems-gnc/staging_v3.1/rev1/results/mass_est_v2/mest_budget_v1.json"))
AW = json.load(open(f"{R3}/results/eval/rg16w.json"))
out = dict(script="v09_p5 (REV-GNC-5)", tag="SIM streams/tables; DERIVED", p5={}, budget={})
# (1) latency consequence
for fn in sorted(os.listdir(f"{R3}/tables/p5")):
    rows = list(csv.DictReader(gzip.open(f"{R3}/tables/p5/{fn}", "rt")))
    ok = np.array([float(r["ok"]) > 0.5 for r in rows])
    hm = np.array([float(r["h_max"]) for r in rows])
    d = dict(n=len(rows), P=round(float(ok.mean()), 4), apex_p99=round(float(np.percentile(hm, 99)), 3), apex_max=round(float(hm.max()), 3))
    if "flt_vzdec" in rows[0]:
        vd = np.array([float(r["flt_vzdec"]) for r in rows]); vp = np.array([float(r["flt_vzpl"]) for r in rows])
        tdec = np.array([float(r["flt_tdec"]) for r in rows])
        m = tdec > 0
        if m.any():
            dv = vd[m] - vp[m]
            d.update(n_dec=int(m.sum()), dv_p01_p50_p99=[round(float(np.percentile(dv, p)), 3) for p in (1, 50, 99)])
    out["p5"][fn.replace(".csv.gz", "")] = d
# (2) windowed budget
VARS = ("white", "ar5ms", "ar20ms", "ar100ms", "tone10Hz", "tone30Hz", "ar5ms_fr", "ar20ms_fr", "ar100ms_fr", "tone10Hz_fr", "tone30Hz_fr")
CASES = {"A1_H_cal_comp_path": ("A1", "H_cal_comp_path"), "A1_H_cal_path": ("A1", "H_cal_path"),
         "B1_H_cal_comp": ("B1", "H_cal_comp"), "B1_H_cal": ("B1", "H_cal")}


def terms(prof, c):
    if prof == "A1":
        m = T2["budget"][c]["miss_side"]
        return m["mass_1sigma"], m["bias_sum"], "rg16_fct_terms_v2.json (staged rev2)"
    fc = MB["bases"]["tgl_B1_lead62_pc_k2"]["line"]["fc"]
    bsys = abs(AW["cases"][f"B1|{c}"]["terms"]["b_sys_median"])
    return fc["random_rss_1sigma"], fc["bias_linear_bound"] + bsys, "mest_budget_v1.json (staged rev1) + |b_sys| AUTHOR INPUT"


def line(x, E, s_mass, bias):
    p1, p50 = np.percentile(x, 1), np.percentile(x, 50)
    s = (p50 - p1) / Z
    tot = 3.0 * float(np.hypot(s, s_mass)) + bias
    sh = float(np.median(E) - p50)
    strict = tot + max(0.0, sh)
    return dict(n=int(len(x)), p1=float(p1), p50=float(p50), s=float(s), total_pct=round(100 * tot, 4), strict_total_pct=round(100 * strict, 4),
                passes=bool(670 * (1 - tot) > 650), strict_passes=bool(670 * (1 - strict) > 650),
                strict_margin_pp=round(100 * (ALLOW - strict), 4))


for case, (prof, c) in CASES.items():
    z = np.load(f"{R3}/streams/rg16w/rg16w_{case}.npz", allow_pickle=False)
    n = len([k for k in z.files if k.startswith("ft_")])
    s_mass, bias, src = terms(prof, c)
    res = dict(terms=dict(s_mass=s_mass, bias=bias, source=src), variants={})
    for v in VARS:
        E, H1, M50 = [], [], []
        for i in range(n):
            fa = z[f"fa_{v}_{i}"].astype(float); ft = z[f"ft_{i}"].astype(float); sel = z[f"sel_{i}"].astype(bool)
            okf = ft > 1.0
            r = np.full(len(fa), np.nan); r[okf] = fa[okf] / ft[okf] - 1.0
            E.append(r[sel])
            if len(fa) < 3:
                continue
            s3 = swv(sel, 3).all(axis=1)
            e1 = swv(np.where(np.isnan(r), np.inf, r), 3).min(axis=1)
            H1.append(e1[s3])
            if len(e1) >= 50:
                full = swv(s3, 50).all(axis=1)
                mx = swv(np.where(s3, e1, -np.inf), 50).max(axis=1)
                M50.append(mx[full])
        E = np.concatenate(E); H1 = np.concatenate(H1); M50 = np.concatenate(M50)
        res["variants"][v] = dict(single=line(E, E, s_mass, bias), held=line(H1, E, s_mass, bias), W500=line(M50, E, s_mass, bias))
        a = AW["cases"][f"{prof}|{c}"]["vib"].get(v, {}).get("strict_windowed_500ms", {})
        res["variants"][v]["author_W500"] = dict(n=a.get("n"), strict_total_pct=(round(100 * a["strict_total"], 4) if "strict_total" in a else None),
                                                 strict_passes=a.get("strict_passes"))
    out["budget"][case] = res
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(f"allowed {100 * ALLOW:.4f} %")
for k, d in out["p5"].items():
    print(f"  {k:24s} P {d['P']:.3f} apex p99 {d['apex_p99']:8.3f} max {d['apex_max']:8.3f} dv {d.get('dv_p01_p50_p99')} (n_dec {d.get('n_dec')})")
for case, res in out["budget"].items():
    print(f"== {case}: s_mass {100 * res['terms']['s_mass']:.4f} % bias {100 * res['terms']['bias']:.4f} % ({res['terms']['source']})")
    for v, d in res["variants"].items():
        w = d["W500"]; a = d["author_W500"]
        print(f"   {v:12s} W500 n {w['n']:6d} p1 {100 * w['p1']:+.4f} p50 {100 * w['p50']:+.4f} total {w['total_pct']:.4f} strict {w['strict_total_pct']:.4f} "
              f"{'PASS' if w['strict_passes'] else 'FAIL'} margin {w['strict_margin_pp']:+.4f} pp | author n {a['n']} strict {a['strict_total_pct']} {a['strict_passes']}"
              f" | single {d['single']['total_pct']:.3f} held {d['held']['strict_total_pct']:.3f}")
