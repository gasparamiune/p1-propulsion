"""REV-GNC-6 v01: independent recomputation of the rev4 P2 line-208 band (A1 = 210 m claim) from the staged per-run
tables (rev4/out_rev4/p2 + ext, v3d reference rev3/tables/fly + rev4 p2/refext).  Exact two-sided McNemar (own code),
UB95 = d + 1.645 se (line 208), Newcombe method-10 bound (own code), dip onset fixed at 80 g on both arms.
Also: per-half split (runs 0-499 / 500-999), onset sensitivity, four-base pooled, G80 / v351t / v352 arms, a paired
bootstrap of the band selection (B = 2000, resampling runs within each base), the 'every lower band' vs 'h only' readings,
and a check of the reference tables against the hashes the author cites.  SIM tables -> DERIVED.
Usage: python -I v01_p2_band.py <out.json>"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rv6lib as L

OUT = sys.argv[1]
au = json.load(open(f"{L.P2}/p2_rev4.json"))
res = dict(script="v01_p2_band (REV-GNC-6)", tag="DERIVED from SIM tables", author_file_sha16=L.sha16(f"{L.P2}/p2_rev4.json"))

# reference files vs the hashes cited by the author (work-area paths -> staged copies by basename)
refchk = {}
for k, v in au["references"].items():
    base, st = k.split("|")
    mine = L.ref_files(base, st)
    cited = [(os.path.basename(p), h) for p, h in v["files"]]
    refchk[k] = dict(cited=cited, staged=[(os.path.basename(p), L.sha16(p)) for p in mine],
                     match=[(os.path.basename(p), L.sha16(p)) for p in mine] == cited, N=len(L.rows_of(mine)))
res["reference_hash_check"] = refchk

BANDS = list(range(200, 255, 5))


def pair(base, st, v, h, onset=80.0, purge="G73", runs=None):
    cf = L.case_files(base, st, v, h, purge)
    if not cf:
        return None
    case = L.outcome(L.rows_of(cf), onset)
    ref = L.outcome(L.rows_of(L.ref_files(base, st)), onset)
    common = sorted(set(case) & set(ref))
    if runs is not None:
        common = [k for k in common if k in runs]
    if sorted(case) != common and runs is None:
        raise RuntimeError(f"case runs not a subset of reference runs {base} {st} {v} {h}")
    return L.counts(ref, case, common), len(common), [L.sha16(p) for p in cf]


def band_eval(st, v, bases=L.MAIN, onset=80.0, purge="G73", runs=None, bands=BANDS):
    out = {}
    for h in bands:
        prs = [pair(b, st, v, h, onset, purge, runs) for b in bases]
        if any(x is None for x in prs):
            continue
        s = L.stats(*L.pooled_counts([x[0] for x in prs]))
        s["N_per_base"] = [x[1] for x in prs]
        s["per_base"] = {b: L.stats(*x[0]) for b, x in zip(bases, prs)}
        s["case_sha16"] = {b: x[2] for b, x in zip(bases, prs)}
        out[h] = s
    return out


def band_of(ev, delta=1.0, reading="all"):
    hs = sorted(ev)
    best = None
    for i, h in enumerate(hs):
        lower = hs[: i + 1]
        if reading == "all":
            okk = all(L.rule_pass(ev[x], delta) for x in lower)
        else:  # (i) on h and every lower band, (ii) on h only
            okk = all(not ev[x]["loses"] for x in lower) and ev[h]["ub95_pp"] <= delta + 1e-12
        if okk:
            best = h
    return best


def pattern(ev, delta=1.0):
    return {h: ("L" if s["loses"] else ("U" if s["ub95_pp"] > delta + 1e-12 else "P")) for h, s in sorted(ev.items())}


main = {}
for st in ("liq", "pw"):
    ev = band_eval(st, "v351")
    main[st] = dict(bands={h: {k: s[k] for k in ("n", "N_per_base", "P_ref", "P_case", "lost", "gained", "p", "loses",
                                                   "deficit_pp", "ub95_pp", "ub95_newcombe_pp")} for h, s in ev.items()},
                    per_base={h: {b: {k: s["per_base"][b][k] for k in ("P_ref", "P_case", "lost", "gained", "p", "ub95_pp")}
                                  for b in s["per_base"]} for h, s in ev.items()},
                    pattern=pattern(ev), band_all=band_of(ev), band_h_only=band_of(ev, reading="h"))
    # author comparison
    a = au["variants"]["v351"]["states"][st]["bands"]
    cmp = {}
    for h, s in ev.items():
        x = a.get(str(h), {}).get("l208")
        if x:
            cmp[h] = dict(same=(x["lost"], x["gained"], round(x["ub95_pp"], 2), round(x["ub95_newcombe_pp"], 2)) ==
                          (s["lost"], s["gained"], round(s["ub95_pp"], 2), round(s["ub95_newcombe_pp"], 2)),
                          author=(x["lost"], x["gained"], x["p_exact"], x["ub95_pp"], x["ub95_newcombe_pp"]),
                          mine=(s["lost"], s["gained"], s["p"], s["ub95_pp"], s["ub95_newcombe_pp"]))
    main[st]["author_compare"] = cmp
res["v351_main_N1000"] = main
res["decision_band_lower_state"] = min(main["liq"]["band_all"], main["pw"]["band_all"])

# per-half split and onset sensitivity (liq and pw, main bases)
halves = {}
for st in ("liq", "pw"):
    for nm, rr in (("runs_0_499", set(range(0, 500))), ("runs_500_999", set(range(500, 1000)))):
        ev = band_eval(st, "v351", runs=rr, bands=[h for h in BANDS if h <= 235])
        halves[f"{st}|{nm}"] = dict(pattern=pattern(ev), band_all=band_of(ev),
                                    ub95={h: s["ub95_pp"] for h, s in ev.items()},
                                    lost_gained={h: (s["lost"], s["gained"], s["p"]) for h, s in ev.items()})
res["halves"] = halves
ons = {}
for st in ("liq", "pw"):
    for on in (None, 62.0, 69.0, 80.0, 90.0, 100.0):
        ev = band_eval(st, "v351", onset=on)
        ons[f"{st}|{on}"] = dict(pattern=pattern(ev), band_all=band_of(ev), ub95_210=ev[210]["ub95_pp"], lg_210=(ev[210]["lost"], ev[210]["gained"]))
res["onset_sensitivity"] = ons

# four-base pooled at 210 / 215 (runs 0-499 on all four, the N common to every table), and per extra base
four = {}
for st in ("liq", "pw"):
    for h in (210, 215):
        prs = [pair(b, st, "v351", h, runs=set(range(500))) for b in L.ALL4]
        s = L.stats(*L.pooled_counts([x[0] for x in prs]))
        s["per_base"] = {b: L.stats(*x[0]) for b, x in zip(L.ALL4, prs)}
        # also four-base with the main bases at N=1000 (author's 'informational' may use that)
        prs2 = [pair(b, st, "v351", h) for b in L.ALL4]
        s2 = L.stats(*L.pooled_counts([x[0] for x in prs2]))
        four[f"{st}|h{h}"] = dict(N500_all4=s, main1000_extra500=s2, pass_N500=L.rule_pass(s), pass_mixed=L.rule_pass(s2))
res["four_base"] = four

# sensitivity arms (N=500 per base)
sens = {}
for v, purge in (("v351", "G80"), ("v351t", "G73"), ("v352", "G73")):
    for st in ("liq", "pw"):
        ev = band_eval(st, v, purge=purge, bands=[210, 215])
        sens[f"{v}|{purge}|{st}"] = dict(pattern=pattern(ev), band_all=band_of(ev),
                                         stats={h: {k: s[k] for k in ("N_per_base", "P_ref", "P_case", "lost", "gained", "p", "ub95_pp", "ub95_newcombe_pp")} for h, s in ev.items()})
# G80 vs G73 at the same band (runs 0-499)
for st in ("liq", "pw"):
    prs = []
    for b in L.MAIN:
        g73 = L.outcome(L.rows_of(L.case_files(b, st, "v351", 210)), 80.0)
        g80 = L.outcome(L.rows_of(L.case_files(b, st, "v351", 210, "G80")), 80.0)
        prs.append(L.counts(g73, g80, sorted(g80)))
    sens[f"G80_vs_G73|{st}|h210"] = L.stats(*L.pooled_counts(prs))
res["sensitivity_arms"] = sens

# paired bootstrap of the band selection (resample runs 0-999 within each base, same indices for every band and for
# reference and case; bands 200-235 carry N=1000; 240-250 (N=500) all lose and are treated as L)
B = int(os.environ.get("RV6_B", "2000"))
rng = random.Random(20261019)
cache = {}
for st in ("liq", "pw"):
    for b in L.MAIN:
        ref = L.outcome(L.rows_of(L.ref_files(b, st)), 80.0)
        for h in range(200, 240, 5):
            case = L.outcome(L.rows_of(L.case_files(b, st, "v351", h)), 80.0)
            cache[(st, b, h)] = [(ref[k], case[k]) for k in range(1000)]
boot = {}
for st in ("liq", "pw"):
    hist = {}
    for _ in range(B):
        idx = {b: [rng.randrange(1000) for _ in range(1000)] for b in L.MAIN}
        ev = {}
        for h in range(200, 240, 5):
            a = bb = c = d = 0
            for b in L.MAIN:
                col = cache[(st, b, h)]
                for i in idx[b]:
                    r, x = col[i]
                    if r and x: a += 1
                    elif r: bb += 1
                    elif x: c += 1
                    else: d += 1
            ev[h] = L.stats(a, bb, c, d)
        bd = band_of(ev)
        if bd == 235:
            bd = ">=235"
        hist[str(bd)] = hist.get(str(bd), 0) + 1
    boot[st] = dict(B=B, band_hist=dict(sorted(hist.items())))
# joint (lower state) distribution needs the same resample for both states: redo jointly
histj = {}
rng = random.Random(7)
for _ in range(B):
    idx = {b: [rng.randrange(1000) for _ in range(1000)] for b in L.MAIN}
    bands_st = []
    for st in ("liq", "pw"):
        ev = {}
        for h in range(200, 240, 5):
            a = bb = c = d = 0
            for b in L.MAIN:
                col = cache[(st, b, h)]
                for i in idx[b]:
                    r, x = col[i]
                    if r and x: a += 1
                    elif r: bb += 1
                    elif x: c += 1
                    else: d += 1
            ev[h] = L.stats(a, bb, c, d)
        bands_st.append(band_of(ev) if band_of(ev) is not None else 0)
    k = str(min(bands_st))
    histj[k] = histj.get(k, 0) + 1
boot["decision_lower_state"] = dict(B=B, band_hist=dict(sorted(histj.items())))
res["bootstrap_band"] = boot

json.dump(res, open(OUT, "w"), indent=1, default=str)
for st in ("liq", "pw"):
    m = main[st]
    print(st, "pattern", m["pattern"], "band(all)", m["band_all"], "band(h-only)", m["band_h_only"])
    for h, s in m["bands"].items():
        print(f"   h{h} N{s['N_per_base']} {s['P_case']:.4f} vs {s['P_ref']:.4f} -{s['lost']}/+{s['gained']} p {s['p']} "
              f"d {s['deficit_pp']} UB {s['ub95_pp']} (Nc {s['ub95_newcombe_pp']}) author_same {m['author_compare'].get(h, {}).get('same')}")
print("decision band", res["decision_band_lower_state"])
print("ref hash check", {k: v["match"] for k, v in refchk.items()}, {k: v["N"] for k, v in refchk.items()})
print("halves", {k: (v["pattern"], v["band_all"]) for k, v in halves.items()})
print("onsets", {k: (v["band_all"], v["ub95_210"], v["lg_210"]) for k, v in ons.items()})
print("four-base", {k: (v["N500_all4"]["lost"], v["N500_all4"]["gained"], v["N500_all4"]["p"], v["N500_all4"]["ub95_pp"], v["pass_N500"],
                        v["main1000_extra500"]["lost"], v["main1000_extra500"]["gained"], v["main1000_extra500"]["ub95_pp"], v["pass_mixed"]) for k, v in four.items()})
for k, v in sens.items():
    print("sens", k, v if "pattern" not in v else (v["pattern"], v["band_all"], {h: (s["lost"], s["gained"], s["p"], s["ub95_pp"]) for h, s in v["stats"].items()}))
print("bootstrap", json.dumps(boot))
