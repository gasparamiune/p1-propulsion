"""Reviewer helpers (REV-GNC-3): independent statistics, no author code imported."""
import csv, gzip, math, os
D = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev2/results/rg01_refly"
def load(base, arm, d=D):
    p = os.path.join(d, f"rf_{base}_{arm.replace('|','_')}.csv.gz")
    if not os.path.exists(p):
        p2 = p[:-3]
        if os.path.exists(p2):
            return list(csv.DictReader(open(p2)))
        return None
    with gzip.open(p, "rt") as f:
        return list(csv.DictReader(f))
def f(r, k):
    return float(r[k])
def ok(rows):
    return [float(r["ok"]) > 0.5 for r in rows]
def wilson(k, n, z=1.959963984540054):
    if n == 0: return (float("nan"),)*2
    p = k/n; den = 1 + z*z/n; c = p + z*z/(2*n); h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return ((c-h)/den, (c+h)/den)
def binom_two_sided_half(k, n):
    """exact two-sided p for X~Bin(n,1/2) at min count k (McNemar exact)."""
    if n == 0: return 1.0
    k = min(k, n-k)
    s = sum(math.comb(n, i) for i in range(0, k+1)) / 2**n
    return min(1.0, 2*s)
def mcnemar(a, b):
    """a = reference ok list, b = case ok list (paired by run). lost = ref ok & case fail."""
    assert len(a) == len(b)
    lost = sum(1 for x, y in zip(a, b) if x and not y)
    gained = sum(1 for x, y in zip(a, b) if (not x) and y)
    p = binom_two_sided_half(lost, lost+gained)
    Pa = sum(a)/len(a); Pb = sum(b)/len(b)
    return dict(P_ref=Pa, P_case=Pb, lost=lost, gained=gained, p=p, loses=(Pb < Pa and p < 0.05))
def fmt(m):
    return f"{m['P_case']:.4f} vs {m['P_ref']:.4f} -{m['lost']}/+{m['gained']} p {m['p']:.3g}{' LOSES' if m['loses'] else ''}"
