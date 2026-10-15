"""REV-GNC-5 v08: independent recomputation of P3 (285 m coverage) from the staged rev3 SIM tables and the staged rev2 300 m
tables (rev2/results/rg01_refly): P (Wilson) per base, pooled exact McNemar against liq|none|h285, liq|G73|h285 and the
same arm at 300 m (main2 and, where four bases exist, all4); failures by W10 bin; the dip-onset re-count; and the p99
duty-cycle pick (smallest engine-on counter >= the 99th percentile, numpy-linear) with the staged record files' hashes.
SIM tables -> DERIVED.  Usage: python -I v08_p3.py <out.json>"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rv5lib as L

ARMS = ["liq|none|h285", "liq|G73|h285", "pw|G73|h285", "pl|G73|h285", "e19|G73|h285", "liq|none|L400|h285", "liqP|G73|h285",
        "pwP|G73|h285", "liq|G73|L400|h285", "pw|G73|L400|h285", "e19|G73|L400|h285", "nrLO|G73z|h285", "nrLO|none|h285"]


def at300(nm):
    return nm.replace("|h285", "")


def bases(load, nm):
    return [b for b in L.ALL4 if load(b, nm) is not None]


def pool(load_ref, ref, load_case, case, bs, onset=None):
    prs = []
    for b in bs:
        ra = load_ref(b, ref); rb = load_case(b, case)
        oa = L.ok(ra); ob = L.ok(rb)
        if onset is not None:
            oa = [o and 1e3 * float(r["liq_left"]) >= onset for o, r in zip(oa, ra)]
            ob = [o and 1e3 * float(r["liq_left"]) >= onset for o, r in zip(ob, rb)]
        prs.append(L.paired(ra, rb, oa, ob))
    return L.pooled(prs)


out = dict(script="v08_p3 (REV-GNC-5)", tag="SIM tables; DERIVED statistics", arms={}, dc={})
for nm in ARMS:
    bs = bases(L.load3, nm)
    e = dict(per_base={}, pooled={})
    for b in bs:
        rows = L.load3(b, nm); o = L.ok(rows); k = sum(o); n = len(o)
        w = L.col(rows, "wind")
        binf = {}
        for lo, hi in ((0, 2), (2, 4), (4, 6), (6, 8)):
            idx = [i for i, x in enumerate(w) if lo <= x < hi]
            binf[f"{lo}-{hi}"] = f"{sum(1 for i in idx if not o[i])}/{len(idx)}"
        e["per_base"][b] = dict(P=round(k / n, 4), wilson=[round(x, 4) for x in L.wilson(k, n)], fail_by_W10=binf,
                                P_80g=round(sum(1 for r, x in zip(rows, o) if x and 1e3 * float(r["liq_left"]) >= 80.0) / n, 4))
    main = [b for b in L.MAIN if b in bs]
    refs = [("liq|none|h285" if "L400" not in nm else "liq|none|L400|h285"), ("liq|G73|h285" if "L400" not in nm else "liq|G73|L400|h285")]
    for ref in refs:
        if ref == nm:
            continue
        rb = [b for b in main if L.load3(b, ref) is not None]
        e["pooled"][f"vs {ref}|main2"] = pool(L.load3, ref, L.load3, nm, rb)
        b4 = [b for b in bs if L.load3(b, ref) is not None]
        if len(b4) == 4:
            e["pooled"][f"vs {ref}|all4"] = pool(L.load3, ref, L.load3, nm, b4)
    # against the same arm at 300 m (staged rev2 tables)
    b3 = [b for b in bs if L.load2(b, at300(nm)) is not None]
    m3 = [b for b in main if b in b3]
    if m3:
        e["pooled"]["vs 300m|main2"] = pool(L.load2, at300(nm), L.load3, nm, m3)
    if len(b3) == 4:
        e["pooled"]["vs 300m|all4"] = pool(L.load2, at300(nm), L.load3, nm, b3)
        e["pooled"]["vs 300m|all4|80g"] = pool(L.load2, at300(nm), L.load3, nm, b3, onset=80.0)
    e["sha16"] = {b: L.sha16(L.path3(b, nm)) for b in bs}
    e["exhausted_285_vs_300"] = [sum(sum(float(r["exhausted"]) > 0.5 for r in L.load3(b, nm)) for b in bs),
                                 sum(sum(float(r["exhausted"]) > 0.5 for r in L.load2(b, at300(nm))) for b in b3) if b3 else None]
    # paired split by the HARD launch-commit wind rule (W10 < 6 m/s), main bases, against liq|none at the same start model
    rr = "liq|none|L400|h285" if "L400" in nm else "liq|none|h285"
    if rr != nm:
        for lab, cond in (("W10<6", lambda x: x < 6.0), ("W10>=6", lambda x: x >= 6.0)):
            lost = gained = nn = 0
            for b in main:
                ra = L.load3(b, rr); rb = L.load3(b, nm); oa = L.ok(ra); ob = L.ok(rb)
                assert [r["run"] for r in ra] == [r["run"] for r in rb]
                for i, r in enumerate(rb):
                    if cond(float(r["wind"])):
                        nn += 1; lost += oa[i] and not ob[i]; gained += ob[i] and not oa[i]
            e["pooled"][f"vs {rr}|main2|{lab}"] = dict(n=nn, lost=lost, gained=gained, p=L.p_exact(lost, gained))
    out["arms"][nm] = e
# duty-cycle p99 pick
DC = f"{L.R3}/duty_cycles"
for b, rec in (("A1_none", "DC-A1_full_flight_285m_disp_p99_kest2_liqG73_A1none_rev3"), ("A1J_pc", "DC-A1_full_flight_285m_disp_p99_kest2_liqG73_A1Jpc_rev3")):
    rows = L.load3(b, "liq|G73|h285")
    bt = L.col(rows, "burn_time")
    xs = sorted(bt); pos = (len(xs) - 1) * 0.99; lo = int(pos); p99 = xs[lo] + (xs[lo + 1] - xs[lo]) * (pos - lo)   # unrounded
    cand = sorted((x, int(float(r["run"]))) for x, r in zip(bt, rows) if x >= p99 - 1e-12)
    pick = cand[0]
    f = f"{DC}/{rec}.csv"
    out["dc"][b] = dict(p99=p99, pick_burn_time=round(pick[0], 4), pick_run=pick[1], file_sha16=L.sha16(f) if os.path.exists(f) else None,
                        max_burn_time=round(max(bt), 4))
json.dump(out, open(sys.argv[1], "w"), indent=1)
for nm, e in out["arms"].items():
    print(f"{nm:22s} " + " ".join(f"{b} {d['P']:.3f}" for b, d in e["per_base"].items()) + "  fails/W10 " +
          "; ".join(f"{b}:{','.join(d['fail_by_W10'].values())}" for b, d in e["per_base"].items()))
    for k, d in e["pooled"].items():
        print(f"     {k:30s} " + (L.fmt(d) if "P_case" in d else f"n {d['n']} -{d['lost']}/+{d['gained']} p {d['p']:.3g}"))
    print(f"     exhausted 285 m / 300 m (same bases): {e['exhausted_285_vs_300']}")
print("duty-cycle pick:", json.dumps(out["dc"]))
