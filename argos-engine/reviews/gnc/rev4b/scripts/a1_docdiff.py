"""REV-GNC-7 (a): document diff of the gnc.json v3.2 candidate against the published v3.1 (read-only)."""
import json, hashlib, sys, re
H = "/home/claude/work/shared-fallback/engine"
V31 = f"{H}/interfaces/gnc.json"
C = f"{H}/01-systems-gnc/staging_v3.1/rev4b/v32/gnc_v3.2_rev4b.json"
KD = f"{H}/01-systems-gnc/staging_v3.1/rev4b/v32/gnc_v3.2_rev4b_keydiff.json"
CL = f"{H}/interfaces/CHANGELOG.md"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
a = json.load(open(V31)); b = json.load(open(C))
def flat(x, p=""):
    out = {}
    if isinstance(x, dict):
        if not x: out[p] = x
        for k, v in x.items(): out.update(flat(v, f"{p}/{k}"))
    elif isinstance(x, list):
        if not x: out[p] = x
        for i, v in enumerate(x): out.update(flat(v, f"{p}[{i}]"))
    else:
        out[p] = x
    return out
fa, fb = flat(a), flat(b)
changed = sorted(k for k in fa if k in fb and fa[k] != fb[k]); added = sorted(k for k in fb if k not in fa); removed = sorted(k for k in fa if k not in fb)
# top-level / second-level key diff (the author's keydiff granularity is unknown; report both)
def keys2(x, depth=3, p=""):
    s = set()
    if isinstance(x, dict) and depth > 0:
        for k, v in x.items():
            s.add(f"{p}/{k}"); s |= keys2(v, depth - 1, f"{p}/{k}")
    return s
res = dict(v31=dict(path=V31, sha16=sha(V31), version=a.get("version")), candidate=dict(path=C, sha16=sha(C), version=b.get("version")),
           leaf_changed=len(changed), leaf_added=len(added), leaf_removed=len(removed), removed_leaves=removed[:50])
kd = json.load(open(KD))
res["author_keydiff_sha16"] = sha(KD)
res["author_keydiff_top"] = {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in kd.items()} if isinstance(kd, dict) else str(type(kd))
# verbatim lead lines
L = open(CL, encoding="utf-8").read().split("\n")
vb = b.get("lead_decisions_2026-10-19", {}).get("rev4b_lines_204_227", {}).get("verbatim", {})
vchk = {}
for k, v in vb.items():
    try:
        n = int(k)
    except ValueError:
        vchk[k] = "non-numeric key"; continue
    vchk[k] = "EXACT" if v == L[n - 1] else ("EXACT (strip)" if v.strip() == L[n - 1].strip() else f"DIFF (len {len(v)} vs {len(L[n-1])})")
res["verbatim_lines"] = vchk
# open items
oi = b.get("open_items", [])
res["open_items_n_v31"] = len(a.get("open_items", [])); res["open_items_n_v32"] = len(oi)
res["open_items_new"] = [dict(i=i, text=(x if isinstance(x, str) else json.dumps(x))[:600], has_owner=bool(re.search(r"(?i)owner", x if isinstance(x, str) else json.dumps(x))))
                         for i, x in enumerate(oi) if i >= len(a.get("open_items", []))]
res["open_items_changed_old"] = [i for i in range(min(len(oi), len(a.get("open_items", [])))) if oi[i] != a["open_items"][i]]
json.dump(res, open(sys.argv[1], "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("open_items_new", "removed_leaves")}, indent=1)[:3000])
print("removed leaves:", removed)
for x in res["open_items_new"]: print(f"[{x['i']}] owner={x['has_owner']} :: {x['text'][:400]}")
print("changed old open items:", res["open_items_changed_old"])
