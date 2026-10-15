import sys; sys.path.insert(0, ".")
from rvlib import *
B2 = ("A1_none", "A1J_pc"); B4 = ("A1_none", "A1J_pc", "A1_pc", "A1J_none")
def P(base, arm):
    r = load(base, arm); 
    if r is None: return None
    o = ok(r); k = sum(o); n = len(o); lo, hi = wilson(k, n)
    ex = sum(1 for x in r if float(x["exhausted"]) > 0.5)
    return k, n, lo, hi, ex
print("== P|lit per state (k/n, Wilson95, exhausted)")
for arm in ("liq|none", "liq|G73", "pw|G73", "pl|G73", "e19|G73", "liqP|G73", "pwP|G73", "nrLO|none", "nrLO|G73z", "bf|G73"):
    s = []
    for b in B4:
        x = P(b, arm)
        if x: s.append(f"{b}:{x[0]/x[1]:.3f}[{x[2]:.3f},{x[3]:.3f}] ex{x[4]}")
    print(f"{arm:12s}", " | ".join(s))
def pooled(ref, case, bases):
    a, b = [], []
    for bs in bases:
        ra, rb = load(bs, ref), load(bs, case)
        if ra is None or rb is None: return None
        assert [x["run"] for x in ra] == [x["run"] for x in rb]
        a += ok(ra); b += ok(rb)
    return mcnemar(a, b)
print("== paired vs liq|none (main2 pooled, per base, all4)")
for arm in ("liq|G73", "pw|G73", "pl|G73", "e19|G73", "liq|G76", "pw|G76", "liq|PS10", "pw|PS10", "liqP|G73", "pwP|G73", "nrLO|none", "nrLO|G73z", "bf|G73"):
    m2 = pooled("liq|none", arm, B2); s = f"{arm:10s} main2 {fmt(m2)}"
    for b in B2: s += f" || {b} {fmt(pooled('liq|none', arm, (b,)))}"
    m4 = pooled("liq|none", arm, B4)
    if m4: s += f" || all4 {fmt(m4)}"
    print(s)
print("== vs liq|G73 (line-state effect)")
for arm in ("pw|G73", "pl|G73", "e19|G73", "pwP|G73"):
    print(f"{arm:10s} main2 {fmt(pooled('liq|G73', arm, B2))}  all4 {fmt(pooled('liq|G73', arm, B4)) if pooled('liq|G73', arm, B4) else ''}")
print("liqP|G73 vs liq|G73 main2", fmt(pooled("liq|G73", "liqP|G73", B2)))
print("pwP|G73 vs liqP|G73 main2", fmt(pooled("liqP|G73", "pwP|G73", B2)))
print("liqP|G73 vs liq|none A1_none", fmt(pooled("liq|none", "liqP|G73", ("A1_none",))))
print("== plateau arms")
for arm, ref in (("pw|G73|L400", "liq|G73|L400"), ("pw|G73|L400", "liq|none|L400"), ("pw|G73|L400o", "liq|G73|L400o"), ("pw|G73|L400o", "pw|G73"), ("e19|G73|L400", "liq|G73|L400"), ("e19|G73|L400", "liq|none|L400"), ("e19|G73|L400", "e19|G73"), ("liq|G73|L400", "liq|none|L400"), ("liq|none|L400", "liq|none"), ("pw|G73|L400", "pw|G73"), ("bf|G73|L400", "liq|none|L400")):
    print(f"{arm:14s} vs {ref:14s} main2 {fmt(pooled(ref, arm, B2))}")
