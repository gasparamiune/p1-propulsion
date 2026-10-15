import json, re, sys
J = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev2/results/gnc_json/gnc_v3.1_staging_rev2.json"
d = json.load(open(J))
flat = []
def walk(x, p):
    if isinstance(x, dict):
        for k, v in x.items(): walk(v, p + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, p + f"[{i}]")
    else:
        flat.append((p, str(x)))
walk(d, "")
pats = sys.argv[1:]
for pat in pats:
    rx = re.compile(pat)
    hits = [(p, s) for p, s in flat if rx.search(s) or rx.search(p)]
    print(f"## {pat}: {len(hits)} hits")
    for p, s in hits[:12]:
        m = rx.search(s)
        ctx = s[max(0, m.start() - 160): m.start() + 220] if m else s[:200]
        print(f"   {p[:110]} :: {ctx}")
