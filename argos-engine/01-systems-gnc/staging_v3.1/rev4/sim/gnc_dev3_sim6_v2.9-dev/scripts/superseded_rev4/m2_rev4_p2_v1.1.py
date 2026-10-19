"""m2_rev4_p2 v1.1 (GNC rev4, 2026-10-13): P2 apogee re-fly on the FROZEN massprops v3.5.1 (lead CHANGELOG 206 (1)).

v1.1 (lead message of 2026-10-13 after REV-GNC-5 RV5-01, to be CHANGELOG line 208; replaces the 204 (3) rule):
  A1 apogee = the highest 5 m band h for which h AND every lower flown band show
    (i)  no significant pooled loss (two main bases A1_none + A1J_pc, paired, exact McNemar, lower with p < 0.05) against
         the v3d reference st|G73|h285, with the dip onset FIXED at 80 g on both arms (upper end of the R3-17 bracket,
         until the OI-32 outlet geometry sets the true onset), and
    (ii) a one-sided 95 % upper bound on the pooled P deficit <= delta = 1.0 pp. Basis: the normal approximation for
         paired proportions used by REV-GNC-5 (reviews/gnc/rev3/scripts/v07_p2.py): d = (lost - gained) / n,
         se = sqrt(lost + gained - (lost - gained)^2 / n) / n, UB = d + 1.645 se. Newcombe's hybrid score bound (method
         10, z 1.645) is reported beside it as a robustness check, not as the rule.
  Both conditions are applied to h and to every lower flown band (the lead's list reads 'h and every lower flown band
  show: (i) AND (ii)'); the reading with (ii) on h only is reported too. Per line state (liq, pw); the decision value is
  the lower of the two. The sweep extends down until a band passes; a statement is written when no band >= 200 m passes.
  N: 500 runs per base; on candidate bands the run range 500-999 is added (part 'ext' for the case, part 'refext' for the
  v3d reference on iface_v3d, rev2 pins), so N = 1000 per base where both tables carry it; N is stated per band.
  Candidate band and the band above: also flown on the two other bases (A1_pc, A1J_none; per base and four-base pooled
  results, informational). Purge sensitivity G80 (line 203 (3), RV5-07): SIL flow basis 32.0 g/s x the 2.5 s schedule =
  80 g, booked at the same rate (as rev2's G76); the ECU both-open cap <= 2.55 s does not truncate the 2.5 s scheduled
  flow (line 203 (3)), so the sim's flow-time cap stays 2.5 s.
  The 204 (3) reading of v1.0 (no loss at the flown 60 g, 69 g and 80 g onsets) is kept in the output as SUPERSEDED.
  part 'mc' is unchanged from v1.0 (the v3.5.1 sweep tables were flown with v1.0, kept in superseded_rev4/).

Flights: the rev3 fly loop m2_rev3_fly v1.1 .fly (itself m2_rg01_refly v1.3) run unchanged for runs 0-499: sim6 v2.9-dev
(gnc_dev3), FSW-R2, decided purge G73, decided release rule, Combustion v2.4 line-state tables, seed 101, bases A1_none
and A1J_pc, line states liq and pw. The 500-999 extension uses a copy of that loop with a run range on the 1000-run draw
(R.draw is sequential per run, so runs 0-499 of the 1000-run draw equal the 500-run draw: checked on every draw value, and
the first runs are re-flown and compared column for column with the stored tables before any extension is flown).
Arms: st|<purge>|<variant>|h<h>, variant in (v351, v351t, v352L) from out/rev4/mass_v351/mass_v351_vs_v3d.json
(m2_mass_v351 v1.0); the variant's derived interface set and pin list must be the active GNC_IFACE / GNC_IFACE_PIN.
Env: m2r3_env.sh + GNC_IFACE / GNC_IFACE_PIN of the variant; GNC_P2_PARTS (mc, ext, refext, eval), GNC_P2_VARIANTS,
GNC_P2_STATES, GNC_P2_BASES, GNC_P2_BANDS ('v351=250:200;v351t=270:220'), GNC_P2_EXT ('v351:235,230' = arms extended to
1000 runs), GNC_P2_G80 ('v351:235' = G80 arms), GNC_P2_PURGES (mc: G73,G80), GNC_P2_OUT (default out/rev4/p2).
SIM only; DERIVED statistics; no physical validation."""
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from collections import OrderedDict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_rev3_fly as F3  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

F = F3.F
VERSION = "m2_rev4_p2 v1.1"
SP = "/home/claude/work/space"
OUT = os.environ.get("GNC_P2_OUT", f"{SP}/out/rev4/p2")
PARTS = os.environ.get("GNC_P2_PARTS", "mc,eval").split(",")
MASS = f"{SP}/out/rev4/mass_v351/mass_v351_vs_v3d.json"
REF_DIR = f"{SP}/out/rev3/fly"
HUBR3 = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev3"
RD_PATH = f"{SP}/gnc_dev6/scripts/m2_rev3_reserve_dip.py"
IFACE_V3D = f"{SP}/iface_v3d"
PIN_V3D = f"{SP}/gnc_dev29/data/pins/pins_rev2.sha256"
BASES = ("A1_none", "A1J_pc")
EXTRA = ("A1_pc", "A1J_none")
STATES = ("liq", "pw")
DEFAULT_BANDS = OrderedDict(v351=(250, 200), v351t=(270, 220), v352L=(270, 220))
ONSETS = OrderedDict([("flown_60g", None), ("125N_62g", 62.0), ("250N_69g", 69.0), ("500N_80g", 80.0)])
RULE_ONSETS = ("flown_60g", "250N_69g", "500N_80g")      # v1.0 reading of 204 (3), SUPERSEDED by line 208
ONSET_L208 = 80.0
DELTA_PP = 1.0
Z1 = 1.645
N0, NX = 500, 1000
N_CHECK = 4
F.PURGE.setdefault("G80", dict(F.GSEQ, prg_mdot=0.0320, prg_mdot_hat=0.0320))


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def _rd():
    spec = importlib.util.spec_from_file_location("m2_rev3_reserve_dip_v11", RD_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def bands():
    out = OrderedDict((k, v) for k, v in DEFAULT_BANDS.items())
    for spec in [x for x in os.environ.get("GNC_P2_BANDS", "").split(";") if x.strip()]:
        k, v = spec.split("=")
        hi, lo = (int(x) for x in v.split(":"))
        out[k.strip()] = (hi, lo)
    return OrderedDict((k, list(range(hi, lo - 1, -5))) for k, (hi, lo) in out.items())


def _vlist(env):
    """'v351:235,230;v351t:250' -> {v351: [235, 230], v351t: [250]}"""
    out = OrderedDict()
    for spec in [x for x in os.environ.get(env, "").split(";") if x.strip()]:
        k, v = spec.split(":")
        out[k.strip()] = [int(x) for x in v.split(",") if x.strip()]
    return out


def variants():
    return json.load(open(MASS))["simulator"]["variants"]


def arm(st, v, h, purge="G73"):
    return f"{st}|{purge}|{v}|h{h}"


def register():
    """Add the P2 v3.5.1 arms to m2_rev3_fly.ARMS (the rev3 fly() reads its spec from there)."""
    vs = variants()
    names = []
    g80 = _vlist("GNC_P2_G80")
    for v, hs in bands().items():
        s = vs[v]
        for h in sorted(set(hs) | set(g80.get(v, [])), reverse=True):
            for pu in ("G73", "G80"):
                if pu == "G73" and h not in hs:
                    continue
                if pu == "G80" and h not in g80.get(v, []):
                    continue
                for st in STATES:
                    nm = arm(st, v, h, pu)
                    F3.ARMS[nm] = dict(state=st, purge=pu, plat="", bases=BASES + EXTRA,
                                       ex=dict(h_target=float(h), ballast=float(s["ballast_kg"]),
                                               ballast_z=float(s["ballast_z_m"])),
                                       iface=s["iface"], pin=s["pin"], group=f"P2_{v}", ref=f"{st}|G73|h285", variant=v)
                    names.append(nm)
    return names


def _check_iface(spec):
    iface = os.path.realpath(os.environ.get("GNC_IFACE", ""))
    pin = os.path.realpath(os.environ.get("GNC_IFACE_PIN", ""))
    return os.path.realpath(spec["iface"]) == iface and os.path.realpath(spec["pin"]) == pin, iface, pin


def _gz(p):
    with open(p, "rb") as fi, gzip.GzipFile(p + ".gz", "wb", mtime=0) as fo:
        fo.write(fi.read())
    os.remove(p)


def _meta(spec, base, nm, rows, t0, p, iface, pin, run_range=(0, N0)):
    ok = np.array([r["ok"] for r in rows]) > 0.5
    ex = int(np.sum([r["exhausted"] > 0.5 for r in rows]))
    liq = 1e3 * np.array([r["liq_left"] for r in rows])
    p07z = F.engine_bay_mid()[0]
    meta = dict(version=VERSION, fly_loop=f"{F3.VERSION} fly() (unchanged)" if run_range == (0, N0) else
                f"{F3.VERSION} fly() body with a run range {run_range} on the {run_range[1]}-run draw",
                base=base, arm=nm, run_range=list(run_range), spec={k: v for k, v in spec.items() if k != "bases"},
                cfg_extra=F3.cfg_extra(spec, p07z), purge_settings=F.PURGE[spec["purge"]], iface=iface, pin=pin,
                pin_sha16=sha16(pin), mech_sha16=sha16(os.path.join(iface, "mechanical.json")),
                mass_file=dict(path=MASS, sha256_16=sha16(MASS)), sim=s6.SIM6_VERSION, wall_s=round(time.time() - t0, 1),
                P=float(ok.mean()), exhausted=ex, liq_left_g_p01_of_landed=(float(np.percentile(liq[ok], 1)) if ok.any() else None),
                table_sha16=sha16(p + ".gz"))
    if spec.get("variant"):
        ms = variants()[spec["variant"]]
        want = json.load(open(MASS))["simulator"]["derived_mechanical_json"]["v352L" if spec["variant"] == "v352L" else "v351"]["sha256_16"]
        if meta["mech_sha16"] != want:
            raise RuntimeError(f"derived mechanical.json changed since m2_mass_v351 ({meta['mech_sha16']} != {want})")
        meta["variant"] = dict(name=spec["variant"], label=ms["label"], landing_mass_delta_kg=ms["landing_mass_delta_kg"])
    return meta


def part_mc():
    """N = 500 flights (runs 0-499) with m2_rev3_fly.fly unchanged (v1.0 behaviour)."""
    os.makedirs(os.path.join(OUT, "meta"), exist_ok=True)
    names = register()
    vsel = [x for x in os.environ.get("GNC_P2_VARIANTS", "v351").split(",") if x]
    ssel = [x for x in os.environ.get("GNC_P2_STATES", ",".join(STATES)).split(",") if x]
    bsel = [x for x in os.environ.get("GNC_P2_BASES", ",".join(BASES)).split(",") if x]
    psel = [x for x in os.environ.get("GNC_P2_PURGES", "G73").split(",") if x]
    hsel = _vlist("GNC_P2_ONLY")
    p07z = F.engine_bay_mid()[0]
    print(f"{VERSION} mc: GNC_IFACE {os.environ.get('GNC_IFACE')}; variants {vsel}; states {ssel}; bases {bsel}; purges "
          f"{psel}; only {dict(hsel) or 'all bands'}; mass file {sha16(MASS)}", flush=True)
    for nm in names:
        spec = F3.ARMS[nm]
        h = int(spec["ex"]["h_target"])
        if spec["variant"] not in vsel or spec["state"] not in ssel or spec["purge"] not in psel:
            continue
        if hsel and h not in hsel.get(spec["variant"], []):
            continue
        ok_if, iface, pin = _check_iface(spec)
        if not ok_if:
            print(f"skip {nm}: needs GNC_IFACE {spec['iface']} and pin {spec['pin']}", flush=True)
            continue
        for base in bsel:
            p = os.path.join(OUT, F3.fname(base, nm))
            if os.path.exists(p) or os.path.exists(p + ".gz"):
                print("exists", base, nm, flush=True)
                continue
            t0 = time.time()
            rows, cfg = F3.fly(base, nm, p07z)
            F.M.write_csv(p, rows)
            _gz(p)
            meta = _meta(spec, base, nm, rows, t0, p, iface, pin)
            json.dump(meta, open(os.path.join(OUT, "meta", F3.fname(base, nm) + ".json"), "w"), indent=1)
            print(f"{base:9s} {nm:22s}: P {meta['P']:.3f} exhausted {meta['exhausted']} liq p01 "
                  f"{meta['liq_left_g_p01_of_landed']} g ({time.time() - t0:.0f} s)", flush=True)


# ------------------------------------------------------------------------------------------------- run-range extension
def fly_range(base, name, p07z, lo, hi):
    """m2_rev3_fly.fly with a run range [lo, hi) on the hi-run draw (same body, same per-run settings)."""
    spec = F3.ARMS[name]
    st = spec["state"]
    stc = "pw" if st == "bf" else st
    cfg, m = F.base_cfg(base, stc, F3.cfg_extra(spec, p07z))
    jr = json.load(open(F.TG))["j_ref"]
    F.MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    D = R.draw(np.random.default_rng(101), hi, cfg)
    ms = F.MV.case_specs()["tot_cal_comp"]
    rows = []
    for i in range(lo, hi):
        c, disp = F.MV.run_cfg_case(cfg, D[i], ms, i, "base")
        c.update(F.DEC)
        c.update(F.PURGE[spec["purge"]])
        c.update(F.PLAT[spec["plat"]])
        if spec.get("gex"):
            c.update(spec["gex"])
        if st == "bf":
            c.update(F.BLEED)
        res = R.fly(c, disp, nrec=10)[0]
        row = R.flat_row(i, D[i], res, R.success(res), cfg)
        row["m_n2o"] = m
        row["mest_kcal"] = float(c.get("mest_kcal", float("nan")))
        rows.append(row)
    return rows, cfg


def _same(a, b):
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if a is None or b is None:
        return a is None and b is None
    return float(a) == float(b) or (np.isnan(float(a)) and np.isnan(float(b)))


def load_rows(p):
    with gzip.open(p, "rt") as f:
        return list(csv.DictReader(f))


def ext_check(base, name, p07z, stored):
    """(a) runs 0-499 of the 1000-run draw equal the 500-run draw on every value; (b) runs 0..N_CHECK-1 re-flown with
    fly_range equal the stored table column for column."""
    spec = F3.ARMS[name]
    cfg, m = F.base_cfg(base, "pw" if spec["state"] == "bf" else spec["state"], F3.cfg_extra(spec, p07z))
    D5 = R.draw(np.random.default_rng(101), N0, cfg)
    D10 = R.draw(np.random.default_rng(101), NX, cfg)
    draw_ok = all(set(a) == set(b) and all(_same(a[k], b[k]) for k in a) for a, b in zip(D5, D10[:N0]))
    rows, _ = fly_range(base, name, p07z, 0, N_CHECK)
    ref = load_rows(stored)[:N_CHECK]
    bad = []
    for r, q in zip(rows, ref):
        for k, v in r.items():
            a, b = float(v), float(q[k])
            if not ((np.isnan(a) and np.isnan(b)) or a == b):
                bad.append([int(r["run"]), k, a, b])
    return dict(draw_prefix_equal=bool(draw_ok), rows_checked=N_CHECK, row_mismatches=bad[:10], n_mismatch=len(bad),
                stored=stored, stored_sha16=sha16(stored), ok=bool(draw_ok and not bad))


def part_ext(ref=False):
    """Runs 500-999: 'ext' for the case arms in GNC_P2_EXT, 'refext' for the v3d reference st|G73|h285."""
    sub = "refext" if ref else "ext"
    os.makedirs(os.path.join(OUT, sub, "meta"), exist_ok=True)
    register()
    bsel = [x for x in os.environ.get("GNC_P2_BASES", ",".join(BASES)).split(",") if x]
    ssel = [x for x in os.environ.get("GNC_P2_STATES", ",".join(STATES)).split(",") if x]
    p07z = F.engine_bay_mid()[0]
    iface = os.path.realpath(os.environ.get("GNC_IFACE", ""))
    pin = os.path.realpath(os.environ.get("GNC_IFACE_PIN", ""))
    if ref:
        if iface != os.path.realpath(IFACE_V3D) or pin != os.path.realpath(PIN_V3D):
            raise RuntimeError(f"refext needs GNC_IFACE {IFACE_V3D} and pin {PIN_V3D}")
        names = [f"{st}|G73|h285" for st in ssel]
    else:
        names = [arm(st, v, h) for v, hs in _vlist("GNC_P2_EXT").items() for h in hs for st in ssel]
    for nm in names:
        spec = F3.ARMS[nm]
        if not ref:
            ok_if, _i, _p = _check_iface(spec)
            if not ok_if:
                print(f"skip {nm}: needs GNC_IFACE {spec['iface']}", flush=True)
                continue
        for base in bsel:
            p = os.path.join(OUT, sub, F3.fname(base, nm).replace(".csv", "_x500.csv"))
            if os.path.exists(p + ".gz"):
                print("exists", base, nm, flush=True)
                continue
            stored = (ref_table(base, nm.split("|")[0]) if ref else os.path.join(OUT, F3.fname(base, nm) + ".gz"))
            if not os.path.exists(stored):
                print(f"skip {base} {nm}: the 500-run table {stored} is missing", flush=True)
                continue
            t0 = time.time()
            chk = ext_check(base, nm, p07z, stored)
            json.dump(chk, open(os.path.join(OUT, sub, "meta", os.path.basename(p) + ".check.json"), "w"), indent=1)
            if not chk["ok"]:
                raise RuntimeError(f"extension check failed for {base} {nm}: {chk}")
            rows, cfg = fly_range(base, nm, p07z, N0, NX)
            F.M.write_csv(p, rows)
            _gz(p)
            meta = _meta(spec, base, nm, rows, t0, p, iface, pin, run_range=(N0, NX))
            meta["extension_check"] = dict(ok=chk["ok"], draw_prefix_equal=chk["draw_prefix_equal"], rows=N_CHECK)
            json.dump(meta, open(os.path.join(OUT, sub, "meta", os.path.basename(p) + ".json"), "w"), indent=1)
            print(f"{sub} {base:9s} {nm:22s} runs {N0}-{NX - 1}: P {meta['P']:.3f} exhausted {meta['exhausted']} "
                  f"(check ok; {time.time() - t0:.0f} s)", flush=True)


# --------------------------------------------------------------------------------------------------------- evaluation
def ref_table(base, st):
    """rev3 v3d reference table, verified against the hub rev3 MANIFEST."""
    fn = F3.fname(base, f"{st}|G73|h285") + ".gz"
    p = os.path.join(REF_DIR, fn)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    man = {}
    for ln in open(os.path.join(HUBR3, "MANIFEST_rev3.sha256")):
        if ln.strip():
            a, b = ln.split(None, 1)
            man[b.strip().lstrip("*").lstrip("./")] = a
    if man.get(f"tables/fly/{fn}") != h:
        raise RuntimeError(f"reference {fn} does not match the hub rev3 MANIFEST")
    return p


def outcome(rows, onset):
    ok = np.array([float(r["ok"]) for r in rows]) > 0.5
    run = np.array([int(float(r["run"])) for r in rows])
    if onset is None:
        return ok, run
    liq = 1e3 * np.array([float(r["liq_left"]) for r in rows])
    return ok & (liq - onset >= 0.0), run


def wilson(k, n, z):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def stats(a, b):
    """Paired reference a / case b (bool arrays): exact McNemar, deficit, one-sided 95 % upper bounds (pp)."""
    from scipy.stats import binomtest
    n = int(len(a))
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    p = float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0
    d = (lost - gained) / n
    se = math.sqrt(max(lost + gained - (lost - gained) ** 2 / n, 0.0)) / n
    # Newcombe (1998) method 10, one-sided 95 % (z 1.645), deficit = p_ref - p_case
    n11 = int(np.sum(a & b)); n00 = int(np.sum(~a & ~b))
    p1, p2 = a.mean(), b.mean()
    l1, u1 = wilson(int(a.sum()), n, Z1)
    l2, u2 = wilson(int(b.sum()), n, Z1)
    num = n11 * n00 - lost * gained
    if num > 0:
        num = max(num - n / 2.0, 0.0)
    den = math.sqrt(max((n11 + lost) * (gained + n00) * (n11 + gained) * (lost + n00), 0.0))
    phi = num / den if den > 0 else 0.0
    ubn = d + math.sqrt(max((u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2, 0.0))
    return OrderedDict(n=n, P_ref=round(float(p1), 4), P_case=round(float(p2), 4), lost=lost, gained=gained,
                       p_exact=float(f"{p:.3g}"), loses=bool(p2 < p1 and p < 0.05), deficit_pp=round(100 * d, 3),
                       ub95_pp=round(100 * (d + Z1 * se), 3), ub95_newcombe_pp=round(100 * ubn, 3))


def _rows(base, nm, case=True):
    """(rows over runs 0..N-1, N, files): 500-run table plus the 500-999 extension if present."""
    if case:
        p0 = os.path.join(OUT, F3.fname(base, nm) + ".gz")
        px = os.path.join(OUT, "ext", F3.fname(base, nm).replace(".csv", "_x500.csv") + ".gz")
    else:
        p0 = ref_table(base, nm.split("|")[0])
        px = os.path.join(OUT, "refext", F3.fname(base, nm).replace(".csv", "_x500.csv") + ".gz")
    if not os.path.exists(p0):
        return None, 0, []
    rows = load_rows(p0)
    files = [(p0, sha16(p0))]
    if os.path.exists(px):
        rows = rows + load_rows(px)
        files.append((px, sha16(px)))
    return rows, len(rows), files


def paired(bases, ref_nm, case_nm, onset, nmax=None):
    """Pooled paired outcomes over bases at the common N per base (min of reference and case N)."""
    A, B, Ns, files = [], [], [], []
    for b in bases:
        rr, nr, fr = _rows(b, ref_nm, case=False) if ref_nm.endswith("|G73|h285") else _rows(b, ref_nm)
        rc, nc, fc = _rows(b, case_nm)
        if rr is None or rc is None:
            return None
        n = min(nr, nc) if nmax is None else min(nr, nc, nmax)
        a, ra = outcome(rr[:n], onset)
        c, rc_ = outcome(rc[:n], onset)
        if not np.array_equal(ra, rc_) or not np.array_equal(ra, np.arange(n)):
            raise RuntimeError(f"not paired: {b} {case_nm} vs {ref_nm}")
        A.append(a); B.append(c); Ns.append(n); files += fr + fc
    s = stats(np.concatenate(A), np.concatenate(B))
    s["N_per_base"] = dict(zip(bases, Ns))
    return s, files


def rule_l208(bands_stats):
    """bands_stats: {h: stats} for the flown bands. Highest h such that h and every lower flown band pass (i) and (ii);
    and the reading with (ii) on h only."""
    hs = sorted(bands_stats)
    pi = {h: not bands_stats[h]["loses"] for h in hs}
    pii = {h: bands_stats[h]["ub95_pp"] <= DELTA_PP for h in hs}
    best = None
    for h in hs:
        if pi[h] and pii[h]:
            best = h
        else:
            break
    best_h_only = None
    for h in hs:
        if not pi[h]:
            break
        if pii[h]:
            best_h_only = h
    return dict(band_m=best, band_m_reading_ub_on_h_only=best_h_only, pattern=OrderedDict(
        (h, ("P" if (pi[h] and pii[h]) else ("L" if not pi[h] else "U"))) for h in hs),
        legend="P pass; L significant loss at 80 g; U no significant loss but UB95 > delta", lowest_flown=hs[0] if hs else None)


def part_eval():
    RD = _rd()
    register()
    vs = variants()
    res = OrderedDict(version=VERSION, date=time.strftime("%Y-%m-%d"), sim=s6.SIM6_VERSION,
                      rule_l208=("A1 apogee = the highest 5 m band h for which h and every lower flown band show (i) no "
                                 "significant pooled loss (A1_none + A1J_pc, paired exact McNemar, lower with p < 0.05) "
                                 "against the v3d reference st|G73|h285 with the dip onset FIXED at 80 g on both arms, and (ii) "
                                 "a one-sided 95 % upper bound on the pooled P deficit <= 1.0 pp (normal approximation for "
                                 "paired proportions, REV-GNC-5 v07_p2 basis); per line state, decision = the lower state "
                                 "(lead message 2026-10-13 after REV-GNC-5 RV5-01, CHANGELOG line 208)"),
                      superseded_rule=("204 (3) reading of v1.0: no loss at the flown 60 g, 69 g and 80 g onsets, highest "
                                       "qualifying band, no margin, no monotonicity (SUPERSEDED by line 208; kept as record)"),
                      withdrawn=dict(planning_value_250m="WITHDRAWN (lead, RV5-02): <= 245 m TO-VERIFY by this P2"),
                      mass_file=dict(path=MASS, sha256_16=sha16(MASS)),
                      reserve_dip_script=dict(path=RD_PATH, sha256_16=sha16(RD_PATH), version=RD.VERSION),
                      delta_pp=DELTA_PP, onset_g=ONSET_L208, references={}, variants=OrderedDict())
    for st in STATES:
        for b in BASES + EXTRA:
            rr, n, fr = _rows(b, f"{st}|G73|h285", case=False)
            res["references"][f"{b}|{st}"] = dict(N=n, files=fr)
    g80 = _vlist("GNC_P2_G80")
    for v, hs in bands().items():
        ve = OrderedDict(label=vs[v]["label"], landing_mass_delta_kg=vs[v]["landing_mass_delta_kg"],
                         ballast=[vs[v]["ballast_kg"], vs[v]["ballast_z_m"]], states=OrderedDict())
        for st in STATES:
            se = OrderedDict(bands=OrderedDict())
            for h in sorted(hs):
                nm = arm(st, v, h)
                pr = paired(BASES, f"{st}|G73|h285", nm, ONSET_L208)
                if pr is None:
                    continue
                s, files = pr
                e = OrderedDict(l208=s)
                # per base and four-base (where flown)
                pb = OrderedDict()
                for b in BASES + EXTRA:
                    q = paired((b,), f"{st}|G73|h285", nm, ONSET_L208)
                    if q is not None:
                        pb[b] = q[0]
                        rc, nc, fc = _rows(b, nm)
                        ok = np.array([float(r["ok"]) for r in rc]) > 0.5
                        pb[b]["P_flown_N"] = round(float(ok.mean()), 4)
                        pb[b]["exhausted"] = int(np.sum(np.array([float(r["exhausted"]) for r in rc]) > 0.5))
                e["per_base"] = pb
                if all(b in pb for b in BASES + EXTRA):
                    e["four_base_pooled_informational"] = paired(BASES + EXTRA, f"{st}|G73|h285", nm, ONSET_L208)[0]
                # SUPERSEDED 204 (3) reading at N 500 (v1.0)
                old = OrderedDict()
                for k, on in ONSETS.items():
                    old[k] = paired(BASES, f"{st}|G73|h285", nm, on, nmax=N0)[0]
                e["superseded_204_3"] = dict(onsets=old, qualifies=bool(not any(old[k]["loses"] for k in RULE_ONSETS)))
                if h in g80.get(v, []):
                    g = paired(BASES, f"{st}|G73|h285", arm(st, v, h, "G80"), ONSET_L208)
                    if g is not None:
                        e["G80_vs_v3d_ref"] = g[0]
                        e["G80_vs_same_band_G73"] = paired(BASES, nm, arm(st, v, h, "G80"), ONSET_L208)[0]
                e["files"] = files
                se["bands"][h] = e
            bs = {h: e["l208"] for h, e in se["bands"].items()}
            se["rule_l208"] = rule_l208(bs) if bs else None
            q = [h for h, e in se["bands"].items() if e["superseded_204_3"]["qualifies"]]
            se["superseded_204_3_highest"] = max(q) if q else None
            ve["states"][st] = se
        hq = [ve["states"][st]["rule_l208"]["band_m"] if ve["states"][st]["rule_l208"] else None for st in STATES]
        ve["band_l208_all_states_m"] = (min(hq) if hq and all(x is not None for x in hq) else None)
        flown = [h for st in STATES for h in ve["states"][st]["bands"]]
        ve["lowest_flown_m"] = min(flown) if flown else None
        ve["no_band_at_or_above_200m"] = bool(flown) and (ve["band_l208_all_states_m"] is None
                                                         or ve["band_l208_all_states_m"] < 200)
        res["variants"][v] = ve
    p = os.path.join(OUT, "p2_rev4.json")
    json.dump(res, open(p, "w"), indent=1, default=float)
    print("wrote", p, sha16(p))
    for v, ve in res["variants"].items():
        if not any(ve["states"][st]["bands"] for st in STATES):
            continue
        print(f"== {v} (+{ve['landing_mass_delta_kg']} kg): line-208 band all states {ve['band_l208_all_states_m']} "
              f"(lowest flown {ve['lowest_flown_m']}; no band >= 200 m: {ve['no_band_at_or_above_200m']})")
        for st, se in ve["states"].items():
            r = se["rule_l208"]
            if r is None:
                continue
            print(f"  {st}: band {r['band_m']} (ub on h only: {r['band_m_reading_ub_on_h_only']}) pattern "
                  f"{''.join(r['pattern'].values())} from {min(r['pattern'])} m; superseded 204(3) {se['superseded_204_3_highest']}")
            for h, e in se["bands"].items():
                s = e["l208"]
                print(f"    h{h}: N {s['N_per_base']} P {s['P_case']:.4f}/{s['P_ref']:.4f} -{s['lost']}/+{s['gained']} "
                      f"p {s['p_exact']:.3g}{' L' if s['loses'] else ''} deficit {s['deficit_pp']:+.2f} pp UB95 "
                      f"{s['ub95_pp']:.2f} (Newcombe {s['ub95_newcombe_pp']:.2f}) | ex "
                      + "/".join(str(e['per_base'][b]['exhausted']) for b in BASES if b in e['per_base'])
                      + ("" if "G80_vs_v3d_ref" not in e else
                         f" | G80 {e['G80_vs_v3d_ref']['P_case']:.4f} UB {e['G80_vs_v3d_ref']['ub95_pp']:.2f}"
                         f"{' L' if e['G80_vs_v3d_ref']['loses'] else ''}"))


if __name__ == "__main__":
    if "mc" in PARTS:
        part_mc()
    if "ext" in PARTS:
        part_ext(ref=False)
    if "refext" in PARTS:
        part_ext(ref=True)
    if "eval" in PARTS:
        part_eval()
