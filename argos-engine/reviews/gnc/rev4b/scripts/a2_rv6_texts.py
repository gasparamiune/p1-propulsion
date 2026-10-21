"""REV-GNC-7 (a): every quoted RV6-01..14 correction text of REVIEW-GNC-R4.md (lines 254-316) searched verbatim in the
v3.2 candidate (exact substring over all string leaves); paths reported."""
import json, re, sys
H = "/home/claude/work/shared-fallback/engine"
R = open(f"{H}/reviews/REVIEW-GNC-R4.md", encoding="utf-8").read().split("\n")[253:316]
b = json.load(open(f"{H}/01-systems-gnc/staging_v3.1/rev4b/v32/gnc_v3.2_rev4b.json"))
flat = []
def walk(x, p):
    if isinstance(x, dict):
        for k, v in x.items(): walk(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, f"{p}[{i}]")
    elif isinstance(x, str): flat.append((p, x))
walk(b, "")
cur = None; out = []
for ln in R:
    m = re.match(r"^(RV6-\d\d) ", ln)
    if m: cur = m.group(1)
    for q in re.findall(r'"([^"]{40,})"', ln):
        # the review quotes old text after 'replace' and new text after 'with'; record both, mark which
        pre = ln[:ln.find(q)][-40:].lower()
        role = "old" if re.search(r"replace\s*$|replace \"$|replace$", pre.strip().rstrip('"').strip()) else "new"
        locs = [p for p, s in flat if q in s]
        live = [p for p in locs if "superseded" not in p.lower() and "verbatim" not in p.lower()]
        out.append(dict(id=cur, role=role, text=q[:140] + ("..." if len(q) > 140 else ""), n_chars=len(q), found=len(locs), live_paths=live[:6],
                        all_paths=locs[:6]))
json.dump(out, open(sys.argv[1], "w"), indent=1)
for o in out:
    print(f"{o['id']} {o['role']:3s} found {o['found']} live {len(o['live_paths'])} :: {o['text'][:110]}")
    if o['found'] == 0 or (o['role'] == 'old' and o['live_paths']): print("      ->", o['all_paths'])
