"""REV-GNC-6 v03: re-fly a decision-relevant SUBSET of the staged rev4 P2 runs with the STAGED code (hub
staging_v3.1/rev4/sim/gnc_dev3_sim6_v2.9-dev, work-area paths redirected to scratch copies of staged files only) and
compare every re-flown row with the staged row, field by field (CSV strings as written by the staged writer).
Run selection per (base, arm): every run that is discordant between the case and the v3d reference at the 80 g onset
(those runs carry the McNemar statistic) plus a seeded sample of concordant runs, in both halves (0-499 from the 500-run
draw, as m2_rev3_fly.fly; 500-999 from the 1000-run draw, as m2_rev4_p2.fly_range). The draw-prefix claim (runs 0-499 of
the 1000-run draw equal the 500-run draw) is checked on every drawn value.
Env RV6_FULL=1: re-fly every staged run of the job (0-999) and keep the re-flown table (gzip, mtime 0).
Usage: python -I v03_refly4.py <tree> <outdir> <mode case|ref> <job> [<job> ...]   job = base:state:h (case) or base:state (ref)
Reads only hub / scratch files; an audit hook records opens outside the hub, the scratch and the Python install.
SIM reproduction only: matching rows show that the computation repeats, nothing about physics."""
import csv, gzip, io, json, os, random, sys, time
TREE, OUTD, MODE = sys.argv[1], sys.argv[2], sys.argv[3]
JOBS = sys.argv[4:]
HUB = "/home/claude/work/shared-fallback/engine"
SCR = os.path.realpath(os.environ["RV_ALLOW"])
OUTSIDE = []


def _audit(ev, args):
    if ev == "open" and isinstance(args[0], (str, bytes)):
        p = args[0].decode() if isinstance(args[0], bytes) else args[0]
        rp = os.path.realpath(p)
        if not (rp.startswith(HUB) or rp.startswith(SCR) or rp.startswith(("/opt/", "/usr/", "/proc/", "/dev/", "/etc/", "/tmp/claude-0/")) or rp.startswith(sys.prefix)):
            OUTSIDE.append(rp)


sys.addaudithook(_audit)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import rv6lib as L  # noqa: E402
sys.path.insert(0, TREE)
sys.path.insert(0, os.path.join(TREE, "scripts"))
import numpy as np  # noqa: E402
import m2_rev4_p2 as P  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402
F3, F = P.F3, P.F
os.makedirs(OUTD, exist_ok=True)
p07z = F.engine_bay_mid()[0]
P.register()
print(f"v03r4: {P.VERSION} / {F3.VERSION}; sim {s6.SIM6_VERSION[:70]}; GNC_IFACE {os.environ.get('GNC_IFACE')}; "
      f"pin {os.path.basename(os.environ.get('GNC_IFACE_PIN', ''))}; P07 z {p07z}", flush=True)


def pick(base, st, h):
    """discordant runs at 80 g between case (v351 h) and reference, + 8 concordant per half (seeded)."""
    ref = L.outcome(L.rows_of(L.ref_files(base, st)), 80.0)
    case = L.outcome(L.rows_of(L.case_files(base, st, "v351", h)), 80.0)
    disc = sorted(k for k in case if case[k] != ref[k])
    rng = random.Random(f"{base}{st}{h}")
    conc = []
    for lo, hi in ((0, 500), (500, 1000)):
        pool = [k for k in range(lo, hi) if k in case and case[k] == ref[k]]
        conc += sorted(rng.sample(pool, min(8, len(pool))))
    return disc, conc


def fly_subset(base, name, runs, ndraw):
    spec = F3.ARMS[name]
    st = spec["state"]
    cfg, m = F.base_cfg(base, st, F3.cfg_extra(spec, p07z))
    jr = json.load(open(F.TG))["j_ref"]
    F.MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    D = R.draw(np.random.default_rng(101), ndraw, cfg)
    ms = F.MV.case_specs()["tot_cal_comp"]
    rows = []
    for i in runs:
        c, disp = F.MV.run_cfg_case(cfg, D[i], ms, i, "base")
        c.update(F.DEC)
        c.update(F.PURGE[spec["purge"]])
        c.update(F.PLAT[spec["plat"]])
        if spec.get("gex"):
            c.update(spec["gex"])
        res = R.fly(c, disp, nrec=10)[0]
        row = R.flat_row(i, D[i], res, R.success(res), cfg)
        row["m_n2o"] = m
        row["mest_kcal"] = float(c.get("mest_kcal", float("nan")))
        rows.append(row)
    return rows, cfg


def as_strings(rows):
    p = os.path.join(OUTD, f"_tmp_{os.getpid()}.csv")
    F.M.write_csv(p, rows)
    out = list(csv.DictReader(open(p)))
    os.remove(p)
    return out


def draw_prefix_check(base, st, name):
    spec = F3.ARMS[name]
    cfg, m = F.base_cfg(base, st, F3.cfg_extra(spec, p07z))
    D5 = R.draw(np.random.default_rng(101), 500, cfg)
    D10 = R.draw(np.random.default_rng(101), 1000, cfg)

    def same(a, b):
        if isinstance(a, (tuple, list)):
            return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
        if a is None or b is None:
            return a is None and b is None
        fa, fb = float(a), float(b)
        return fa == fb or (np.isnan(fa) and np.isnan(fb))
    return all(set(a) == set(b) and all(same(a[k], b[k]) for k in a) for a, b in zip(D5, D10[:500]))


res = []
for job in JOBS:
    parts = job.split(":")
    if MODE == "case":
        base, st, h = parts[0], parts[1], int(parts[2])
        name = f"{st}|G73|v351|h{h}"
        files = L.case_files(base, st, "v351", h)
        disc, conc = pick(base, st, h)
        spec = F3.ARMS[name]
        meta0 = json.load(open(os.path.join(L.P2, "meta", F3.fname(base, name) + ".json")))
        cfg_meta = meta0.get("cfg_extra")
        cfg_mine = F3.cfg_extra(spec, p07z)
    else:
        base, st = parts[0], parts[1]
        name = f"{st}|G73|h285"
        files = L.ref_files(base, st)
        # reference: the discordant runs of the 210 and 215 m liq/pw case arms + 8 concordant per half
        disc = set()
        for h in (210, 215):
            d, c = pick(base, st, h)
            disc |= set(d)
        disc = sorted(disc)
        rng = random.Random(f"ref{base}{st}")
        conc = []
        for lo, hi in ((0, 500), (500, 1000)):
            conc += sorted(rng.sample([k for k in range(lo, hi) if k not in disc], 8))
        cfg_meta = cfg_mine = None
    staged = {int(float(r["run"])): r for r in L.rows_of(files)}
    t0 = time.time()
    dp = draw_prefix_check(base, st, name)
    runs = sorted(set(disc) | set(conc))
    if os.environ.get("RV6_FULL") == "1":
        runs = sorted(staged)
    lo_runs = [k for k in runs if k < 500]
    hi_runs = [k for k in runs if k >= 500]
    rows = []
    if lo_runs:
        rows += fly_subset(base, name, lo_runs, 500)[0]
    if hi_runs:
        rows += fly_subset(base, name, hi_runs, 1000)[0]
    mine = as_strings(rows)
    if os.environ.get("RV6_FULL") == "1":
        import gzip as _gz
        fo = os.path.join(OUTD, F3.fname(base, name) + f"_rv6_n{len(mine)}.csv.gz")
        p_ = fo[:-3]
        F.M.write_csv(p_, rows)
        with open(p_, "rb") as fi, _gz.GzipFile(fo, "wb", mtime=0) as g:
            g.write(fi.read())
        os.remove(p_)
    nbad, first = 0, []
    cols_mine = list(mine[0].keys())
    cols_st = list(next(iter(staged.values())).keys())
    for r in mine:
        k = int(float(r["run"]))
        s = staged[k]
        d = [(k, c, r[c], s.get(c)) for c in cols_st if r.get(c) != s.get(c)]
        if d:
            nbad += 1
            first += d[:3]
    out = dict(mode=MODE, base=base, arm=name, files=[(os.path.basename(p), L.sha16(p)) for p in files],
               n_runs=len(mine), n_discordant=len(disc), n_concordant_sample=len(conc), runs_lo=len(lo_runs), runs_hi=len(hi_runs),
               draw_prefix_equal=dp, cfg_extra_mine=cfg_mine, cfg_extra_staged_meta=cfg_meta,
               cols_equal=(cols_mine == cols_st), n_rows_differing=nbad, first_diffs=first[:8],
               identical=(nbad == 0 and cols_mine == cols_st), wall_s=round(time.time() - t0, 1))
    res.append(out)
    print(json.dumps(out), flush=True)
print("outside-hub/scratch opens:", sorted(set(OUTSIDE))[:20], flush=True)
json.dump(dict(results=res, outside_opens=sorted(set(OUTSIDE)), sim=s6.SIM6_VERSION, p2_version=P.VERSION,
               fly_version=F3.VERSION), open(os.path.join(OUTD, f"v03r4_{MODE}_{int(time.time())}.json"), "w"), indent=1)
