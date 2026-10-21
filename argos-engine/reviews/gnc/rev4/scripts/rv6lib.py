"""REV-GNC-6 reviewer helpers (independent of the author's evaluation code; only staged SIM tables are read).
Statistics: exact two-sided McNemar on discordant pairs; UB95 of the paired deficit by the normal approximation
specified in line 208 (d + 1.645 se); Newcombe (1998) method-10 hybrid score bound implemented here independently;
Wilson intervals.  DERIVED from SIM tables; nothing here is physical approval."""
import csv, gzip, hashlib, math, os
HUB = "/home/claude/work/shared-fallback/engine"
STG = f"{HUB}/01-systems-gnc/staging_v3.1"
R4 = f"{STG}/rev4"
P2 = f"{R4}/out_rev4/p2"
T3 = f"{STG}/rev3/tables/fly"
MAIN = ("A1_none", "A1J_pc")
EXTRA = ("A1_pc", "A1J_none")
ALL4 = MAIN + EXTRA
Z1 = 1.645
_C = {}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def read(p):
    if p in _C:
        return _C[p]
    with (gzip.open(p, "rt") if p.endswith(".gz") else open(p)) as f:
        rows = list(csv.DictReader(f))
    _C[p] = rows
    return rows


def fn(base, arm):
    return f"rf_{base}_{arm.replace('|', '_')}.csv.gz"


def case_files(base, st, v, h, purge="G73"):
    a = f"{st}|{purge}|{v}|h{h}"
    p0 = os.path.join(P2, fn(base, a))
    px = os.path.join(P2, "ext", fn(base, a).replace(".csv.gz", "_x500.csv.gz"))
    return [p for p in (p0, px) if os.path.exists(p)]


def ref_files(base, st):
    a = f"{st}|G73|h285"
    p0 = os.path.join(T3, fn(base, a))
    px = os.path.join(P2, "refext", fn(base, a).replace(".csv.gz", "_x500.csv.gz"))
    return [p for p in (p0, px) if os.path.exists(p)]


def rows_of(files):
    out = []
    for p in files:
        out += read(p)
    return out


def outcome(rows, onset=80.0):
    """dict run -> success (ok AND 1000 liq_left >= onset; onset None = flown ok)."""
    d = {}
    for r in rows:
        o = float(r["ok"]) > 0.5
        if onset is not None:
            o = o and (1e3 * float(r["liq_left"]) - onset >= 0.0)
        k = int(float(r["run"]))
        if k in d:
            raise RuntimeError(f"duplicate run {k}")
        d[k] = o
    return d


def p_exact(lost, gained):
    n = lost + gained
    if n == 0:
        return 1.0
    k = min(lost, gained)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / den, (c + h) / den)


def counts(ref, case, runs=None):
    """paired 2x2 over the common runs (raises if run sets differ unless runs is given)."""
    if runs is None:
        if set(ref) != set(case):
            raise RuntimeError(f"run sets differ {len(ref)} / {len(case)}")
        runs = sorted(ref)
    a = sum(1 for k in runs if ref[k] and case[k])
    b = sum(1 for k in runs if ref[k] and not case[k])
    c = sum(1 for k in runs if (not ref[k]) and case[k])
    d = sum(1 for k in runs if (not ref[k]) and not case[k])
    return a, b, c, d


def stats(a, b, c, d):
    """a both ok, b lost (ref ok, case fail), c gained, d both fail."""
    n = a + b + c + d
    p1, p2 = (a + b) / n, (a + c) / n
    diff = (b - c) / n
    se = math.sqrt(max(b + c - (b - c) ** 2 / n, 0.0)) / n
    l1, u1 = wilson(a + b, n, Z1)
    l2, u2 = wilson(a + c, n, Z1)
    num = a * d - b * c
    if num > 0:
        num = max(num - n / 2.0, 0.0)
    den = math.sqrt(max((a + b) * (c + d) * (a + c) * (b + d), 0))
    phi = num / den if den > 0 else 0.0
    ubn = diff + math.sqrt(max((u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2, 0.0))
    p = p_exact(b, c)
    return dict(n=n, P_ref=round(p1, 4), P_case=round(p2, 4), lost=b, gained=c, p=float(f"{p:.4g}"),
                loses=bool(p2 < p1 and p < 0.05), deficit_pp=round(100 * diff, 3), ub95_pp=round(100 * (diff + Z1 * se), 3),
                ub95_newcombe_pp=round(100 * ubn, 3))


def pooled_counts(pairs):
    return tuple(sum(x[i] for x in pairs) for i in range(4))


def rule_pass(s, delta=1.0):
    return (not s["loses"]) and s["ub95_pp"] <= delta + 1e-12


def q(xs, p):
    """numpy-linear percentile, unrounded."""
    xs = sorted(x for x in xs if x == x)
    pos = (len(xs) - 1) * p / 100.0
    lo = int(math.floor(pos)); hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)
