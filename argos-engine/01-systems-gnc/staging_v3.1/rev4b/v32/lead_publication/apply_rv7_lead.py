"""Lead's independent apply of the REV-GNC-7 corrections (rv7_v32_corrections.json) to the gnc.json v3.2 candidate.
Usage: python3 -I apply_rv7_lead.py OUT.json [--rename-mode inplace|end]
Semantics: replace = the string at path holds `old` exactly once and it becomes `new`; set = the key / index at path
takes `new`; append = the list at path gains `new`; rename = the key at path becomes `new_key` (value kept)."""
import json, sys, hashlib
H = "/home/claude/work/shared-fallback/engine/"
CAND = H + "01-systems-gnc/staging_v3.1/rev4b/v32/gnc_v3.2_rev4b.json"
CORR = H + "reviews/gnc/rev4b/data/b/rv7_v32_corrections.json"
s16 = lambda b: hashlib.sha256(b).hexdigest()[:16]
craw = open(CAND, "rb").read(); assert s16(craw) == "43d58c4aff164b86"
kraw = open(CORR, "rb").read(); assert s16(kraw) == "f7c0c6051efd5a08"
doc = json.loads(craw); corr = json.loads(kraw)
assert corr["candidate_sha16"] == "43d58c4aff164b86" and corr["n_ops"] == len(corr["ops"]) == 34
mode = sys.argv[sys.argv.index("--rename-mode") + 1] if "--rename-mode" in sys.argv else "inplace"

def resolve(path):
    """Return (parent, key) for a slash path; dict keys may themselves contain '/'."""
    segs = path.split("/"); x = doc; i = 0; trail = []
    while True:
        # choose the token for this level
        if isinstance(x, list):
            tok = int(segs[i]); j = i + 1
        else:
            j = None
            for k in range(len(segs), i, -1):  # longest key match first
                cand = "/".join(segs[i:k])
                if cand in x: j = k; tok = cand; break
            if j is None:
                assert len(segs) - i == 1, ("unresolved", path, segs[i:])
                tok = segs[i]; j = i + 1  # new key at the last level
        if j == len(segs): return x, tok
        x = x[tok]; i = j

log = []
for n, o in enumerate(corr["ops"]):
    par, key = resolve(o["path"])
    op = o["op"]
    if op == "replace":
        cur = par[key]; assert isinstance(cur, str), (n, type(cur))
        c = cur.count(o["old"]); assert c == 1, (n, "old count", c)
        par[key] = cur.replace(o["old"], o["new"])
    elif op == "set":
        if isinstance(par, list): assert 0 <= key < len(par), (n, key, len(par))
        existed = (key in par) if isinstance(par, dict) else True
        par[key] = o["new"]; log.append((n, "set", "replaced" if existed else "added"))
    elif op == "append":
        tgt = par[key]; assert isinstance(tgt, list), n
        tgt.append(o["new"])
    elif op == "rename":
        assert isinstance(par, dict) and key in par and o["new_key"] not in par, n
        if mode == "inplace":
            items = [(o["new_key"] if k == key else k, v) for k, v in par.items()]
            par.clear(); par.update(items)
        else:
            par[o["new_key"]] = par.pop(key)
    else:
        raise SystemExit(f"unknown op {op} at {n}")
out = json.dumps(doc, indent=1, ensure_ascii=False).encode()
open(sys.argv[1], "wb").write(out)
print("ops applied", len(corr["ops"]), "rename mode", mode, "out sha16", s16(out), "bytes", len(out))
print("set ops:", log)
