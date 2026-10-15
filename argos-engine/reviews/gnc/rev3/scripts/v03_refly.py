"""REV-GNC-5 v03: re-fly a sample of staged rev3 arms with the STAGED code (hub rev3 sim/gncsim_v2.12-dev, the staged
m2_rev3_fly v2.2 and the rev2-staged m2_rg01_refly v1.3 chain, work-area paths redirected to hub copies only) and compare
each new table byte for byte with the staged table (gunzipped) and with the table_sha16 in the staged meta.
Usage: python -I v03_refly.py <tree> <outdir> <base:arm> [<base:arm> ...]
Reads only hub / scratch files; an audit hook records any open() outside the hub, the scratch and the Python install.
SIM reproduction only; matching tables show that the computation repeats, nothing about physics."""
import gzip, hashlib, json, os, sys, time
TREE, OUTD = sys.argv[1], sys.argv[2]
JOBS = [a.split(":", 1) for a in sys.argv[3:]]
HUB = "/home/claude/work/shared-fallback/engine"
STAGED = f"{HUB}/01-systems-gnc/staging_v3.1/rev3/tables/fly"
SCR = os.path.realpath(os.environ["RV_ALLOW"])
OUTSIDE = []
def _audit(ev, args):
    if ev == "open" and isinstance(args[0], (str, bytes)):
        p = args[0].decode() if isinstance(args[0], bytes) else args[0]
        rp = os.path.realpath(p)
        if not (rp.startswith(HUB) or rp.startswith(SCR) or rp.startswith(("/opt/", "/usr/", "/proc/", "/dev/", "/etc/", "/tmp/claude-0/")) or rp.startswith(sys.prefix)):
            OUTSIDE.append(rp)
sys.addaudithook(_audit)
sys.path.insert(0, TREE)
sys.path.insert(0, os.path.join(TREE, "scripts"))
import m2_rev3_fly as RF  # noqa: E402  (staged v2.2, paths redirected)
from gncsim import sim6 as s6  # noqa: E402
def sha(b): return hashlib.sha256(b).hexdigest()
os.makedirs(OUTD, exist_ok=True)
p07z = RF.F.engine_bay_mid()[0]
print(f"v03: {RF.VERSION}; sim {s6.SIM6_VERSION[:60]}; GNC_IFACE {os.environ.get('GNC_IFACE')}; pin {os.path.basename(os.environ.get('GNC_IFACE_PIN',''))}; P07 z {p07z}", flush=True)
res = []
for base, arm in JOBS:
    fn = RF.fname(base, arm)
    t0 = time.time()
    rows, cfg = RF.fly(base, arm, p07z)
    p = os.path.join(OUTD, fn)
    RF.F.M.write_csv(p, rows)
    mine = open(p, "rb").read()
    st = gzip.open(os.path.join(STAGED, fn + ".gz"), "rb").read()
    meta = json.load(open(os.path.join(STAGED, "meta", fn + ".json")))
    same = mine == st
    r = dict(base=base, arm=arm, wall_s=round(time.time() - t0, 1), sha16_mine=sha(mine)[:16], sha16_staged_gunzip=sha(st)[:16],
             table_sha16_meta=meta.get("table_sha16"), staged_sim=meta.get("sim", "")[:40], byte_identical=same,
             P_mine=sum(float(x["ok"]) > 0.5 for x in rows) / len(rows), P_meta=meta.get("P"))
    if not same:
        import csv, io
        a = list(csv.DictReader(io.StringIO(mine.decode()))); b = list(csv.DictReader(io.StringIO(st.decode())))
        ka, kb = list(a[0].keys()), list(b[0].keys())
        common = [k for k in kb if k in ka]
        diffs = [(i, k, a[i][k], b[i][k]) for i in range(min(len(a), len(b))) for k in common if a[i][k] != b[i][k]]
        r.update(n_rows=(len(a), len(b)), cols_only_mine=[k for k in ka if k not in kb], cols_only_staged=[k for k in kb if k not in ka],
                 n_common_cols=len(common), n_field_diffs_common=len(diffs), first_diffs=diffs[:8],
                 identical_on_staged_columns=(len(a) == len(b) and not diffs and not [k for k in kb if k not in ka]))
    with open(p, "rb") as fi, gzip.GzipFile(p + ".gz", "wb", mtime=0) as fo:
        fo.write(fi.read())
    os.remove(p)
    res.append(r)
    print(json.dumps(r), flush=True)
print("outside-hub/scratch opens:", sorted(set(OUTSIDE))[:20], flush=True)
json.dump(dict(results=res, outside_opens=sorted(set(OUTSIDE))), open(os.path.join(OUTD, f"v03_{int(time.time())}.json"), "w"), indent=1)
