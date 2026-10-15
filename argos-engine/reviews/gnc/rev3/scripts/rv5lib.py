"""REV-GNC-5 reviewer helpers (independent of the author's evaluation code; only the staged SIM tables are read)."""
import csv, gzip, io, json, math, os, hashlib
HUB = "/home/claude/work/shared-fallback/engine"
R3 = f"{HUB}/01-systems-gnc/staging_v3.1/rev3"
T3 = f"{R3}/tables/fly"
T2 = f"{HUB}/01-systems-gnc/staging_v3.1/rev2/results/rg01_refly"
MAIN = ("A1_none", "A1J_pc")
ALL4 = ("A1_none", "A1J_pc", "A1_pc", "A1J_none")
_C = {}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def _read(p):
    if p in _C:
        return _C[p]
    if p.endswith(".gz"):
        with gzip.open(p, "rt") as f:
            rows = list(csv.DictReader(f))
    else:
        rows = list(csv.DictReader(open(p)))
    _C[p] = rows
    return rows


def path3(base, arm):
    return os.path.join(T3, f"rf_{base}_{arm.replace('|', '_')}.csv.gz")


def path2(base, arm):
    p = os.path.join(T2, f"rf_{base}_{arm.replace('|', '_')}.csv.gz")
    return p if os.path.exists(p) else p[:-3]


def load3(base, arm):
    p = path3(base, arm)
    return _read(p) if os.path.exists(p) else None


def load2(base, arm):
    p = path2(base, arm)
    return _read(p) if os.path.exists(p) else None


def col(rows, k):
    return [float(r[k]) for r in rows]


def ok(rows):
    return [float(r["ok"]) > 0.5 for r in rows]


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n; den = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / den, (c + h) / den)


def p_exact(lost, gained):
    """exact two-sided McNemar p (binomial, 1/2) on the discordant pairs."""
    n = lost + gained
    if n == 0:
        return 1.0
    k = min(lost, gained)
    s = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * s)


def paired(ref_rows, case_rows, ref_ok=None, case_ok=None):
    """pair by the 'run' column; returns lost (ref ok, case fail), gained, P_ref, P_case, p."""
    ra = {int(float(r["run"])): o for r, o in zip(ref_rows, ref_ok if ref_ok is not None else ok(ref_rows))}
    rb = {int(float(r["run"])): o for r, o in zip(case_rows, case_ok if case_ok is not None else ok(case_rows))}
    keys = sorted(set(ra) & set(rb))
    if len(keys) != len(ra) or len(keys) != len(rb):
        raise RuntimeError(f"run sets differ: {len(ra)} / {len(rb)} / common {len(keys)}")
    lost = sum(1 for k in keys if ra[k] and not rb[k]); gained = sum(1 for k in keys if (not ra[k]) and rb[k])
    return dict(n=len(keys), P_ref=sum(ra[k] for k in keys) / len(keys), P_case=sum(rb[k] for k in keys) / len(keys),
                lost=lost, gained=gained, p=p_exact(lost, gained))


def pooled(pairs):
    """pool several paired() results (concatenated pairs, e.g. A1_none + A1J_pc)."""
    n = sum(d["n"] for d in pairs); lost = sum(d["lost"] for d in pairs); gained = sum(d["gained"] for d in pairs)
    Pr = sum(d["P_ref"] * d["n"] for d in pairs) / n; Pc = sum(d["P_case"] * d["n"] for d in pairs) / n
    return dict(n=n, P_ref=Pr, P_case=Pc, lost=lost, gained=gained, p=p_exact(lost, gained),
                loses=(Pc < Pr and p_exact(lost, gained) < 0.05), gains=(Pc > Pr and p_exact(lost, gained) < 0.05))


def fmt(d):
    tag = " LOSES" if d.get("loses") else (" GAINS" if d.get("gains") else "")
    return f"{d['P_case']:.4f} vs {d['P_ref']:.4f} -{d['lost']}/+{d['gained']} p {d['p']:.3g}{tag}"


def q(xs, ps=(0, 50, 100)):
    xs = sorted(x for x in xs if x == x)
    if not xs:
        return None
    out = []
    for p in ps:
        if p == 0:
            out.append(xs[0])
        elif p == 100:
            out.append(xs[-1])
        else:  # linear interpolation as numpy default
            pos = (len(xs) - 1) * p / 100.0; lo = int(math.floor(pos)); hi = min(lo + 1, len(xs) - 1)
            out.append(xs[lo] + (xs[hi] - xs[lo]) * (pos - lo))
    return [round(x, 4) for x in out]
