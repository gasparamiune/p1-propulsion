"""m2_rev4_v32fix v1.0 (GNC rev4, 2026-10-13): author's recomputation of the REV-GNC-5 numbers that the corrected v3.2
proposals rely on (lead CHANGELOG line 208: correct the v3.2 proposals per REV-GNC-5 after P2). DERIVED from the staged rev3
SIM tables (work-area copies under out/rev3/fly, each checked against the hub MANIFEST_rev3) and the staged rev3 evaluation
files; nothing is re-flown here.

  RV5-03  pooled (A1_none + A1J_pc) exact McNemar of the line-194 ECU-hold comparator arms against the release at E2
          (nrLO|none|h285) and against liq|none|h285
  RV5-04  gate-delay tolerance D_crit(L) = slack + lead_nom - L per run (m2_rev3_p6 v1.1 definitions) for L = 2.4, 2.1, 1.9,
          1.3 s on e19 / liq / pw |G73|h285, four bases where flown; P by realised commit lead in the finer bins (2.4-2.9,
          2.1-2.4, 1.9-2.1, 1.7-1.9, 1.5-1.7, 1.3-1.5, < 1.3 s) for the nominal and the L400 contingency arms
  RV5-05  e19|G73|L400|h285 against liq|none|L400|h285 (the F6 comparator) split at W10 = 6 m/s, and with the 80 g dip
          onset applied to both arms
  RV5-09 / RV5-10  read from the staged rev3 evaluation (r2v2 thresholds mode 3 at both windows; rg16w _fr variants)
Usage: python m2_rev4_v32fix.py (no env needed beyond m2r3_env.sh). DERIVED only; not physical approval."""
import csv
import gzip
import hashlib
import json
import math
import os
import time
from collections import OrderedDict

import numpy as np
from scipy.stats import binomtest

VERSION = "m2_rev4_v32fix v1.0"
SP = "/home/claude/work/space"
FLY = f"{SP}/out/rev3/fly"
HUBR3 = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev3"
OUT = f"{SP}/out/rev4/v32"
MAIN = ("A1_none", "A1J_pc")
ALL4 = ("A1_none", "A1J_pc", "A1_pc", "A1J_none")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


_MAN = {}


def manifest():
    if not _MAN:
        for ln in open(os.path.join(HUBR3, "MANIFEST_rev3.sha256")):
            if ln.strip():
                a, b = ln.split(None, 1)
                _MAN[b.strip().lstrip("*").lstrip("./")] = a
    return _MAN


def table(base, arm):
    fn = f"rf_{base}_{arm.replace('|', '_')}.csv.gz"
    p = os.path.join(FLY, fn)
    if not os.path.exists(p):
        return None, None
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if manifest().get(f"tables/fly/{fn}") != h:
        raise RuntimeError(f"{fn} does not match the hub rev3 MANIFEST")
    with gzip.open(p, "rt") as f:
        return list(csv.DictReader(f)), dict(path=p, sha256_16=h[:16])


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def ok_of(rows, onset_g=None):
    ok = col(rows, "ok") > 0.5
    if onset_g is not None:
        ok = ok & (1e3 * col(rows, "liq_left") - onset_g >= 0.0)
    return ok


def mcn(a, b):
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    p = float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0
    return OrderedDict(n=int(len(a)), P_ref=round(float(a.mean()), 4), P_case=round(float(b.mean()), 4), lost=lost,
                       gained=gained, p_exact=float(f"{p:.3g}"), loses=bool(b.mean() < a.mean() and p < 0.05))


def pooled(ref, case, bases=MAIN, onset_g=None, mask_fn=None):
    A, B, src = [], [], []
    for b in bases:
        r0, s0 = table(b, ref)
        r1, s1 = table(b, case)
        if r0 is None or r1 is None:
            return None
        if not np.array_equal(col(r0, "run"), col(r1, "run")):
            raise RuntimeError("not paired")
        a, c = ok_of(r0, onset_g), ok_of(r1, onset_g)
        if mask_fn is not None:
            m = mask_fn(r0)
            a, c = a[m], c[m]
        A.append(a); B.append(c); src += [s0, s1]
    out = mcn(np.concatenate(A), np.concatenate(B))
    out["tables"] = src
    return out


def rv5_03():
    out = OrderedDict()
    for arm in ("nrLO|none|rh300c200|h285", "nrLO|none|rh400c200|h285", "nrLO|none|rh190c500|h285", "nrLO|none|rh300|h285"):
        e = OrderedDict()
        e["vs_release_at_E2"] = pooled("nrLO|none|h285", arm)
        e["vs_liq_none"] = pooled("liq|none|h285", arm)
        e["per_base_vs_release_at_E2"] = {b: pooled("nrLO|none|h285", arm, bases=(b,)) for b in MAIN}
        for k in ("vs_release_at_E2", "vs_liq_none"):
            if e[k]:
                e[k] = {kk: vv for kk, vv in e[k].items() if kk != "tables"} | {"tables": e[k]["tables"]}
        for b in MAIN:
            if e["per_base_vs_release_at_E2"][b]:
                e["per_base_vs_release_at_E2"][b].pop("tables", None)
        out[arm] = e
    return out


def q(x, ps=(0, 1, 50)):
    x = np.asarray(x, float)
    return OrderedDict((("min" if p == 0 else f"p{p:02d}"), round(float(np.percentile(x, p)), 3)) for p in ps)


def rv5_04():
    gd = OrderedDict()
    for name in ("e19|G73|h285", "liq|G73|h285", "pw|G73|h285"):
        for b in ALL4:
            rows, src = table(b, name)
            if rows is None:
                continue
            t0, top, tgo = col(rows, "pgg_t0"), col(rows, "pgg_topen"), col(rows, "pgg_tgo")
            slack = t0 - top
            fired = tgo > 0.0
            lead_nom = np.where(fired, tgo - t0, 2.90)
            e = OrderedDict(table=src, n=len(rows), slack_min_s=round(float(slack.min()), 3))
            for L in (2.4, 2.1, 1.9, 1.3):
                e[f"D_crit_lead_below_{L}s"] = q(slack + lead_nom - L)
            gd[f"{b}|{name}"] = e
    # per-base minimum over the three tables and the A1_none-relative offset
    mins = OrderedDict()
    for b in ALL4:
        ks = [k for k in gd if k.startswith(b + "|")]
        if ks:
            mins[b] = OrderedDict((f"{L}s", min(gd[k][f"D_crit_lead_below_{L}s"]["min"] for k in ks)) for L in (2.4, 2.1, 1.9, 1.3))
    off = {b: round(mins[b]["2.1s"] - mins["A1_none"]["2.1s"], 3) for b in mins}
    # P by realised lead, finer bins, pooled over the contingency arms and the main bases
    bins = ((2.4, 2.9), (2.1, 2.4), (1.9, 2.1), (1.7, 1.9), (1.5, 1.7), (1.3, 1.5), (0.0, 1.3))
    lb = OrderedDict()
    for plat, pre in (("nominal", "e19|G73|ant"), ("L400", "e19|G73|L400|ant")):
        L, F_, O = [], [], []
        srcs = []
        for x in (13, 17, 21, 25):
            for b in MAIN:
                rows, src = table(b, f"{pre}{x}|h285")
                if rows is None:
                    continue
                srcs.append(src)
                tgo, t0 = col(rows, "pgg_tgo"), col(rows, "pgg_t0")
                L.append(tgo - t0); F_.append(tgo > 0.0); O.append(col(rows, "ok") > 0.5)
        lead, fired, ok = np.concatenate(L), np.concatenate(F_), np.concatenate(O)
        tab = OrderedDict()
        for lo, hi in bins:
            m = fired & (lead >= lo) & (lead < hi)
            n, k = int(m.sum()), int(ok[m].sum())
            tab[f"{lo:.1f}-{hi:.1f} s"] = OrderedDict(n=n, ok=k, P=round(k / n, 4) if n else None)
        tab["not fired before E0"] = OrderedDict(n=int((~fired).sum()), ok=int(ok[~fired].sum()))
        lb[plat] = dict(bins=tab, tables=srcs)
    return OrderedDict(gate_delay=gd, D_crit_min_per_base=mins, offset_vs_A1_none_s=off, lead_bins=lb)


def rv5_05():
    ref, case = "liq|none|L400|h285", "e19|G73|L400|h285"
    out = OrderedDict()
    out["all"] = pooled(ref, case)
    out["W10_ge_6"] = pooled(ref, case, mask_fn=lambda r: col(r, "wind") >= 6.0)
    out["W10_lt_6"] = pooled(ref, case, mask_fn=lambda r: col(r, "wind") < 6.0)
    out["all_80g_onset_both"] = pooled(ref, case, onset_g=80.0)
    out["W10_lt_6_80g_onset_both"] = pooled(ref, case, onset_g=80.0, mask_fn=lambda r: col(r, "wind") < 6.0)
    per = OrderedDict()
    for b in MAIN:
        rows, src = table(b, case)
        per[b] = dict(P=round(float(ok_of(rows).mean()), 4), P_80g=round(float(ok_of(rows, 80.0).mean()), 4),
                      P_W10_lt6=round(float(ok_of(rows)[col(rows, "wind") < 6.0].mean()), 4))
    out["per_base"] = per
    for k in list(out):
        if isinstance(out[k], dict) and "tables" in out[k]:
            out[k]["tables"] = out[k]["tables"][:2] + ["..."]
    return out


def staged_reads():
    d = json.load(open(os.path.join(HUBR3, "results", "rev3_results.json")))
    th = d["P4_R2v2"]["thresholds"]
    m3 = OrderedDict()
    for w in ("0.5s", "0.8s"):
        e = th[f"mode3|w{w}"]
        m3[w] = OrderedDict((reg, OrderedDict(flameout_design_max_N=e[reg]["flameout_design_max_N"],
                                             flameout_margin_N_at_T_rev2=e[reg]["at_T_rev2"]["flameout_margin_N"],
                                             flameout_released=e[reg]["at_T_rev2"]["flameout_released"],
                                             fo_cb130_max_N=e[reg]["flameout_sensitivities_max_N"]["fo_cb130"]))
                            for reg in ("all_winds", "W10_lt6"))
    wb = d["P5_RG16_allowance"]["windowed_budget"]
    fr = OrderedDict()
    for case in ("A1|H_cal_comp_path", "B1|H_cal_comp"):
        fr[case] = OrderedDict((v, OrderedDict(total_pct=wb[case]["strict_total_pct"][v], margin_pp=wb[case]["strict_margin_pp"][v],
                                               passes=wb[case]["strict_pass"][v]))
                               for v in ("white", "ar5ms", "ar20ms", "ar100ms", "ar5ms_fr", "ar20ms_fr", "ar100ms_fr"))
    return OrderedDict(source=dict(path=os.path.join(HUBR3, "results", "rev3_results.json"),
                                   sha256_16=sha16(os.path.join(HUBR3, "results", "rev3_results.json"))),
                       RV5_09_mode3=m3, RV5_10_fr_variants=fr)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    res = OrderedDict(version=VERSION, date=time.strftime("%Y-%m-%d"), tag="DERIVED from staged rev3 SIM tables / evaluation",
                      RV5_03=rv5_03(), RV5_04=rv5_04(), RV5_05=rv5_05(), staged=staged_reads())
    p = os.path.join(OUT, "v32_recompute.json")
    json.dump(res, open(p, "w"), indent=1, default=float)
    print("wrote", p, sha16(p), f"({time.time() - t0:.0f} s)")
    for arm, e in res["RV5_03"].items():
        print("RV5-03", arm, {k: (e[k]["P_case"], e[k]["P_ref"], e[k]["lost"], e[k]["gained"], e[k]["p_exact"]) for k in ("vs_release_at_E2", "vs_liq_none") if e[k]})
    print("RV5-04 D_crit min per base", json.dumps(res["RV5_04"]["D_crit_min_per_base"]), "offsets", res["RV5_04"]["offset_vs_A1_none_s"])
    for plat, e in res["RV5_04"]["lead_bins"].items():
        print("RV5-04 lead bins", plat, {k: (v["n"], v.get("P")) for k, v in e["bins"].items()})
    for k, v in res["RV5_05"].items():
        if k != "per_base":
            print("RV5-05", k, (v["P_case"], v["P_ref"], v["lost"], v["gained"], v["p_exact"], v["n"]))
    print("RV5-05 per base", res["RV5_05"]["per_base"])
    print("RV5-09", json.dumps(res["staged"]["RV5_09_mode3"]))
    print("RV5-10", {c: {v: (x["margin_pp"], x["passes"]) for v, x in e.items()} for c, e in res["staged"]["RV5_10_fr_variants"].items()})


if __name__ == "__main__":
    main()
