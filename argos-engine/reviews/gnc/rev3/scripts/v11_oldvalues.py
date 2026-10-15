"""REV-GNC-5 v11: scan for values withdrawn by CHANGELOG line 194 in the staged rev3 results.
Withdrawn: the E2 + 0.22 s hold (and the 0.25 s companion arm), the 60 g ASSUMED residual as the reserve basis (replaced by
the R3-17 dip onset), the lit model 62.5 N x pcf_k.  For every occurrence in rev3_results.json and in the staged eval
JSONs: the JSON path, and whether a marker (SUPERSEDED / WITHDRAWN / WITHDRAWN_MODEL / 60 g basis tag / dip-onset
adjustment) sits on the item, on its key, or on an enclosing dict's status/tag/note; and whether any live proposal
(proposed_for_v3p2 items) cites such a value without its marker.  Text scan only (DERIVED); no physics.
Usage: python -I v11_oldvalues.py <out.json>"""
import json, sys, os, re
HUB = "/home/claude/work/shared-fallback/engine"
R3 = f"{HUB}/01-systems-gnc/staging_v3.1/rev3"
RES = json.load(open(f"{R3}/results/rev3_results.json"))
PAT = {"hold_0p22_0p25": re.compile(r"rh220|rh250|0\.22 s|0\.25 s|E2 \+ 0\.22|pv2_rh['\"]?: ?0\.2[25]"),
       "lit_62p5_pcf_k": re.compile(r"lit_k\d+|62\.5 N x pcf_k|pcf_k|lit_min|lit_margin|lit_not_released"),
       "residual_60g": re.compile(r"60 g|60g|usable_reserve_g_60g|3 % of the liquid")}
MARK = re.compile(r"SUPERSEDED|WITHDRAWN|withdrawn|superseded|ASSUMED|dip onset|dip_onset|P_adjusted|60 g basis|60g_basis|flown_60g|NOT FLOWN|PENDING")


def walk(x, path, ctx, hits):
    """ctx: concatenated status/tag/note/marker text of enclosing dicts."""
    if isinstance(x, dict):
        local = " ".join(str(x[k]) for k in x if k in ("status", "tag", "note", "label", "reading", "residual_basis", "definition", "P_success_note"))
        for k, v in x.items():
            p = f"{path}/{k}"
            own = " ".join(str(v[q]) for q in ("status", "tag", "note") if q in v) if isinstance(v, dict) else ""
            for name, rx in PAT.items():
                if rx.search(str(k)):
                    hits.append(dict(kind=name, path=p, where="key", marked=bool(MARK.search(str(k)) or MARK.search(ctx + " " + local + " " + own))))
            walk(v, p, ctx + " " + local, hits)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, f"{path}[{i}]", ctx, hits)
    elif isinstance(x, str):
        for name, rx in PAT.items():
            for m in rx.finditer(x):
                s = max(0, m.start() - 160); e = min(len(x), m.end() + 160)
                win = x[s:e]
                hits.append(dict(kind=name, path=path, where="text", snippet=win.replace("\n", " "),
                                 marked=bool(MARK.search(win)) or bool(MARK.search(ctx))))


out = dict(script="v11_oldvalues (REV-GNC-5)", tag="text scan; DERIVED", rev3_results={}, eval_files={}, proposals={})
hits = []
walk(RES, "", "", hits)
summ = {}
for h in hits:
    top = h["path"].split("/")[1] if h["path"].count("/") >= 1 else h["path"]
    s = summ.setdefault(f"{h['kind']}|{top}", dict(n=0, unmarked=0, unmarked_paths=[]))
    s["n"] += 1
    if not h["marked"]:
        s["unmarked"] += 1
        if len(s["unmarked_paths"]) < 12:
            s["unmarked_paths"].append(h["path"] + (" :: " + h.get("snippet", "")[:220] if h.get("snippet") else ""))
out["rev3_results"] = summ
# eval JSONs: does each file carry a version / status that marks superseded content?
for fn in sorted(os.listdir(f"{R3}/results/eval")):
    t = open(f"{R3}/results/eval/{fn}").read()
    out["eval_files"][fn] = {k: len(rx.findall(t)) for k, rx in PAT.items()}
    out["eval_files"][fn]["markers"] = {m: t.count(m) for m in ("SUPERSEDED", "WITHDRAWN", "WITHDRAWN_MODEL")}
    try:
        j = json.loads(t)
        out["eval_files"][fn]["version"] = j.get("version") if isinstance(j, dict) else None
    except Exception:
        pass
# proposals: text of each live item and of its cited evidence block
items = RES["proposed_for_v3p2"]["items"]
for i, it in enumerate(items):
    txt = json.dumps(it)
    out["proposals"][i] = dict(path=it["path"], evidence=it["evidence"],
                               mentions={k: [m.group(0) for m in rx.finditer(txt)] for k, rx in PAT.items()},
                               marked_in_text=bool(MARK.search(txt)))
json.dump(out, open(sys.argv[1], "w"), indent=1)
for k, v in sorted(out["rev3_results"].items()):
    print(f"{k:42s} n {v['n']:3d} unmarked {v['unmarked']:3d}")
    for p in v["unmarked_paths"]:
        print("      ", p[:330])
print("eval files:")
for k, v in out["eval_files"].items():
    print("  ", k, v)
print("proposals:")
for k, v in out["proposals"].items():
    print("  ", k, v["path"][:60], "| mentions", {a: b for a, b in v["mentions"].items() if b}, "| marked", v["marked_in_text"])
