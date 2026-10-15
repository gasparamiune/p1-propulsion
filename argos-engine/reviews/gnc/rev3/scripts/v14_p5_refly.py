"""REV-GNC-5 v14: re-fly a sample of P5 (RG-16 latency) arms with the staged v2.12 tree and the staged m2_rev3_p5 v1.0
(work-area paths redirected to hub copies) and compare each table byte for byte with the staged p5 table (flown with
sim6 v2.11-dev).  Usage: python -I v14_p5_refly.py <tree> <outdir> <arm> [<arm> ...].  SIM reproduction only."""
import gzip, hashlib, json, os, sys, time
TREE, OUTD = sys.argv[1], sys.argv[2]
HUB = "/home/claude/work/shared-fallback/engine"
STAGED = f"{HUB}/01-systems-gnc/staging_v3.1/rev3/tables/p5"
SCR = os.path.realpath(os.environ["RV_ALLOW"])
OUTSIDE = []
def _audit(ev, args):
    if ev == "open" and isinstance(args[0], (str, bytes)):
        p = args[0].decode() if isinstance(args[0], bytes) else args[0]
        rp = os.path.realpath(p)
        if not (rp.startswith(HUB) or rp.startswith(SCR) or rp.startswith(("/opt/", "/usr/", "/proc/", "/dev/", "/etc/", "/tmp/claude-0/")) or rp.startswith(sys.prefix)):
            OUTSIDE.append(rp)
sys.addaudithook(_audit)
sys.path.insert(0, TREE); sys.path.insert(0, os.path.join(TREE, "scripts"))
os.environ["GNC_P5_OUT"] = OUTD
import m2_rev3_p5 as P  # noqa: E402
from gncsim import sim6 as s6  # noqa: E402
os.makedirs(OUTD, exist_ok=True)
if P.FF.MV.COMB is None:
    P.FF.MV.COMB = P.FF.MV.comb_draws(500)
A = P.arms()
print("v14:", P.VERSION, s6.SIM6_VERSION[:70], "N", P.N, flush=True)
res = []
for name in sys.argv[3:]:
    t0 = time.time()
    rows = P.fly_arm(A[name])
    p = P.fname(name)
    P.M.write_csv(p, rows)
    mine = open(p, "rb").read()
    st = gzip.open(os.path.join(STAGED, os.path.basename(p) + ".gz"), "rb").read()
    r = dict(arm=name, wall_s=round(time.time() - t0, 1), byte_identical=(mine == st), sha16_mine=hashlib.sha256(mine).hexdigest()[:16],
             sha16_staged_gunzip=hashlib.sha256(st).hexdigest()[:16], P=sum(x["ok"] for x in rows) / len(rows))
    with open(p, "rb") as fi, gzip.GzipFile(p + ".gz", "wb", mtime=0) as fo:
        fo.write(fi.read())
    os.remove(p)
    res.append(r); print(json.dumps(r), flush=True)
print("outside-hub/scratch opens:", sorted(set(OUTSIDE)), flush=True)
json.dump(dict(results=res, outside_opens=sorted(set(OUTSIDE))), open(os.path.join(OUTD, f"v14_{int(time.time())}.json"), "w"), indent=1)
