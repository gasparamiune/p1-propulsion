# verify every "path (sha16)" or "path (sha256/16 sha16)" citation in the JSON that resolves to an existing hub/work file
import json, re, sys, os, hashlib
J = sys.argv[1]
HUB = "/home/claude/work/shared-fallback/engine"
d = json.load(open(J))
flat = []
def walk(x, p):
    if isinstance(x, dict):
        for k, v in x.items(): walk(v, p + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, p + f"[{i}]")
    elif isinstance(x, str): flat.append((p, x))
walk(d, "")
rx = re.compile(r"((?:/home/claude/work/[\w./-]+|(?:reviews|interfaces|0[0-7]-[\w-]+|out)/[\w./*-]+))\s*\((?:sha256/16\s+)?([0-9a-f]{16})\)")
seen = {}
for p, s in flat:
    for m in rx.finditer(s):
        path, h = m.group(1), m.group(2)
        seen.setdefault((path, h), []).append(p)
# also dict-style file/sha256 pairs
def walk2(x, p):
    if isinstance(x, dict):
        f = x.get("file"); h = x.get("sha256") or x.get("sha256_16")
        if isinstance(f, str) and isinstance(h, str):
            seen.setdefault((f, h[:16]), []).append(p)
        for k, v in x.items(): walk2(v, p + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x): walk2(v, p + f"[{i}]")
walk2(d, "")
res = {"ok": 0, "mismatch": [], "missing": [], "glob": []}
for (path, h), ps in sorted(seen.items()):
    if "*" in path:
        res["glob"].append((path, h)); continue
    cands = [path] if path.startswith("/") else [os.path.join(HUB, path), os.path.join(HUB, "01-systems-gnc/staging_v3.1", path), os.path.join("/home/claude/work/space", path)]
    f = next((c for c in cands if os.path.isfile(c)), None)
    if not f:
        res["missing"].append((path, h, ps[0])); continue
    a = hashlib.sha256(open(f, "rb").read()).hexdigest()[:16]
    if a == h: res["ok"] += 1
    else: res["mismatch"].append((path, h, a, ps[0]))
print("citations", len(seen), "ok", res["ok"], "mismatch", len(res["mismatch"]), "missing/unreadable", len(res["missing"]), "glob", len(res["glob"]))
for x in res["mismatch"]: print("MISMATCH", x)
for x in res["missing"][:80]: print("MISSING", x)
