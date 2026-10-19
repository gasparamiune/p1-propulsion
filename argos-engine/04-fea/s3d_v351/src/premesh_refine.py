"""Pre-mesh the refined bodies of queued runs (same cache tag as asm3d.Model) and print node counts.  usage: premesh_refine.py 'BODY:x/y/z/r/h;...' [level]"""
import sys, json, hashlib, time
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import mesh_all
spec, level = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
ref = {}
for part in spec.split(";"):
    bn, nums = part.split(":")
    ref.setdefault(bn, []).append(tuple(float(x) for x in nums.split("/")))
rtag = "_r" + hashlib.sha256(json.dumps(ref, sort_keys=True).encode()).hexdigest()[:8]
tot = 0
for bn, balls in ref.items():
    t0 = time.time()
    d = mesh_all.mesh_body(bn, level, balls=balls, tag=rtag)
    m = json.loads(str(d["meta"]))
    tot += m["n_nodes"]
    print(f"{rtag} {bn:6s} nodes {m['n_nodes']:7d} tets {m['n_tets']:7d} qmin {m['q_min']:.3f} q<0.1 {m['n_q_below_0.1']} inv {m['n_inverted']} t {time.time()-t0:.1f}s", flush=True)
print("refined bodies total nodes", tot)
