"""REV-GNC-3 reviewer: +0.60 kg (A1 re-fly tables and B1 m2_b1_m60 tables), independent statistics (rvlib)."""
import sys, gzip, csv, json, math
sys.path.insert(0, "."); from rvlib import *
B2 = ("A1_none", "A1J_pc")
def exh(rows): return sum(1 for r in rows if float(r["exhausted"]) > 0.5)
def P(rows): x = ok(rows); return sum(x)/len(x)
print("== A1 +0.60 kg")
for arm, ref in (("liq|none|m60", "liq|none"), ("liq|G73|m60", "liq|G73"), ("pw|G73|m60", "pw|G73")):
    A, Bb = [], []
    for b in B2:
        ra, rb = load(b, ref), load(b, arm)
        m = mcnemar(ok(ra), ok(rb)); A += ok(ra); Bb += ok(rb)
        print(f"  {b:8s} {arm:13s} vs {ref:9s}: {fmt(m)} | exhausted {exh(ra)} -> {exh(rb)}")
    print(f"  pooled   {arm:13s} vs {ref:9s}: {fmt(mcnemar(A, Bb))}")
print("== exhausted per base vs apogee target (liq, pw) with m60")
for st in ("liq", "pw"):
    for h in ("", "_h290", "_h280", "_h275"):
        arm = f"{st}|G73|m60" + h.replace("_", "|")
        e = [exh(load(b, arm)) for b in B2]; p = [round(P(load(b, arm)), 3) for b in B2]
        runs = [sorted(int(float(r["run"])) for r in load(b, arm) if float(r["exhausted"]) > 0.5) for b in B2]
        print(f"  {arm:18s} exhausted {e} P {p} runs {runs}")
print("== B1 (m2_b1_m60 csv)")
DB = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev2/results/b1_m60"
def rb(n):
    with gzip.open(f"{DB}/b1_{n}.csv.gz", "rt") as f: return list(csv.DictReader(f))
ref, m60, blf = rb("ref"), rb("m60"), rb("blf31")
for n, r in (("m60", m60), ("blf31", blf)):
    m = mcnemar(ok(ref), ok(r)); k = sum(ok(r))
    print(f"  {n}: {fmt(m)} wilson {wilson(k, len(r))} exhausted {exh(ref)} -> {exh(r)}")
def pct(x, p):
    x = sorted(x); i = (len(x)-1)*p/100; lo = math.floor(i); hi = math.ceil(i); return x[lo] + (x[hi]-x[lo])*(i-lo)
print("  apex p50", round(pct([float(r['h_max']) for r in ref], 50), 3), "->", round(pct([float(r['h_max']) for r in m60], 50), 3))
for n, r in (("ref", ref), ("m60", m60)):
    w = [1e3*float(x["web_t_end"]) for x in r]; acted = sum(1 for x in r if float(x["web_tL"]) >= 0.0)
    print(f"  {n}: web_end min {min(w):.3f} mm, <1 mm {sum(1 for v in w if v < 1.0)}, limit acted {acted}/500")
json.dump(dict(ref=[ok(ref)], m60=[ok(m60)]), open("/dev/null", "w"))
