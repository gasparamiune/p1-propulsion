import json, sys
ST = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev2/results/bitcheck_v29/"
mine = json.load(open(sys.argv[1]))
r1 = json.load(open(ST + "bitcheck_v29_run1_FAIL.json")); r2 = json.load(open(ST + "bitcheck_v29.json"))
def flat(d, p=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items(): out.update(flat(v, f"{p}/{k}"))
    elif isinstance(d, list):
        for i, v in enumerate(d): out.update(flat(v, f"{p}[{i}]"))
    else: out[p] = d
    return out
for part, ref in (("A0", r1), ("A1", r1), ("K", r1), ("V", r1), ("RF", r1), ("G", r2), ("N", r2)):
    a, b = flat(mine["parts"][part]), flat(ref["parts"][part])
    keys = set(a) | set(b); diff = []
    for k in sorted(keys):
        x, y = a.get(k, "<missing>"), b.get(k, "<missing>")
        if x != y:
            if isinstance(x, str) and isinstance(y, str) and ("/" in x or "/" in y): continue   # paths differ by design
            diff.append((k, x, y))
    print(f"part {part}: leaves {len(keys)}, differing (non-path) {len(diff)}")
    for d in diff[:8]: print("   ", d)
print("mine code hashes", mine.get("code_sha256_16"), "author run2", r2.get("code_sha256_16"))
