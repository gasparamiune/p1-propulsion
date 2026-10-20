"""S-AX v352r4 output shrink check (lead 07:18Z: 'write each new S-AX state's res.npz as float32 with np.savez_compressed, after
checking on the first state that the margin tables are unchanged to the reported digits').  Mechanical, 2026-10-20, v1.
On the first state solved in float64 (argv[1], in the run dir of the current SAX_* environment): evaluate() with the float64 res.npz,
then the same file stored as float32 (np.savez_compressed), evaluate() again; compare every number of the margin rows, SCL rows,
interface rows and displacement rows at the reported digits (MS 3 decimals, stresses / temperatures 1 decimal, displacements and gaps
4 decimals); report the sizes.  If every compared value is equal, the float32 file replaces the float64 one (its sha256/16 is kept in
meta) and the chain continues in float32; otherwise the float64 file is restored and the chain stops (exit 2).
Output: v352/checks/sax_f32_check_<run dir>_<state>_v1.json."""
import json, os, sys, time
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/structural")
import sax

st = sys.argv[1]
level = 1.0
rd = sax.run_dir(level) / st
p = rd / "res.npz"
assert p.exists(), p
z = np.load(p, allow_pickle=True)
meta = json.loads(str(z["meta"]))
assert meta.get("res_dtype", "float64") == "float64" and all(z[k].dtype == np.float64 for k in z.files if k != "meta"), "first state must be float64"
t0 = time.time()
ev64 = sax.evaluate(level, states=[st])
sha64, b64 = sax.sha16(p), p.stat().st_size
meta32 = dict(meta, res_dtype="float32", f32_from_float64={"sha256_16": sha64, "bytes": b64, "check": "v352/checks/sax_f32_check.py"})
p32 = rd / "res_f32_tmp.npz"
np.savez_compressed(p32, **{k: z[k].astype(np.float32) for k in z.files if k != "meta"}, meta=json.dumps(meta32, default=float))
p64 = rd / "res_f64_tmp.npz"
os.replace(p, p64)
os.replace(p32, p)
ev32 = sax.evaluate(level, states=[st])

DIG = {"MS": 3, "MPa": 1, "_C": 1, "mm": 4}


def digits(k):
    for s, n in (("MS", 3), ("_mm", 4), ("mm_", 4), ("MPa", 1), ("_C", 1), ("_N", 1)):
        if s in k:
            return n
    return 4


def flat(o, pre=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, f"{pre}.{k}" if pre else str(k))
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            yield from flat(v, f"{pre}[{i}]")
    else:
        yield pre, o


n_cmp, diffs = 0, []
for sec in ("rows", "scl", "interfaces", "displacements"):
    a, b = ev64.get(sec, []), ev32.get(sec, [])
    if len(a) != len(b):
        diffs.append({"section": sec, "what": "row count", "f64": len(a), "f32": len(b)})
        continue
    for ra, rb in zip(a, b):
        fa, fb = dict(flat(ra)), dict(flat(rb))
        for k in fa:
            va, vb = fa[k], fb.get(k)
            if isinstance(va, float) and isinstance(vb, float):
                n_cmp += 1
                nd = digits(k.split(".")[-1])
                if not (np.isfinite(va) and np.isfinite(vb)):
                    if not (va == vb or (np.isnan(va) and np.isnan(vb))):
                        diffs.append({"section": sec, "key": k, "f64": va, "f32": vb})
                elif round(va, nd) != round(vb, nd):
                    diffs.append({"section": sec, "case": ra.get("case"), "part": ra.get("part"), "key": k, "f64": va, "f32": vb, "digits": nd})
            elif va != vb and not (isinstance(va, float) or isinstance(vb, float)):
                n_cmp += 1
                diffs.append({"section": sec, "key": k, "f64": str(va)[:80], "f32": str(vb)[:80]})
ok = not diffs
b32 = p.stat().st_size
if ok:
    p64.unlink()
else:
    os.replace(p, rd / "res_f32_rejected.npz")
    os.replace(p64, p)
out = {"id": "sax_f32_check", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "method": __doc__.strip(),
       "run_dir": sax.run_dir(level).name, "state": st, "n_rows": {s: len(ev64.get(s, [])) for s in ("rows", "scl", "interfaces", "displacements")},
       "n_values_compared": n_cmp, "n_differences_at_reported_digits": len(diffs), "differences": diffs[:50],
       "bytes_float64": b64, "bytes_float32": b32, "ratio": round(b32 / b64, 3), "float64_sha256_16": sha64,
       "float32_sha256_16": sax.sha16(p) if ok else None, "verdict": "float32 ADOPTED for the rest of the run" if ok else "float32 REJECTED: float64 kept",
       "t_s": round(time.time() - t0, 1)}
fo = f"/home/claude/work/mechanical/v352/checks/sax_f32_check_{sax.run_dir(level).name}_{st}_v1.json"
open(fo, "w").write(json.dumps(out, indent=1, default=float))
print(fo, out["verdict"], "compared", n_cmp, "diffs", len(diffs), "bytes", b64, "->", b32, flush=True)
sys.exit(0 if ok else 2)
