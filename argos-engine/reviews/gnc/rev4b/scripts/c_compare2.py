"""REV-GNC-7 (c): row-by-row comparison of the reviewer's reproduction JSONs (m2_eng11_fe v1.0 run unchanged) with the author's
staged rev4b/eng11_fe/results/eng11fe_<V>.json: pass flag, worst upper GM, first failing corner, corner counts."""
import json, os, sys
A = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev4b/eng11_fe/results"
def nt(x):  # drop the wall-time field t_s (machine timing, not a result)
    if isinstance(x, dict): return {k: nt(v) for k, v in x.items() if k != "t_s"}
    if isinstance(x, list): return [nt(v) for v in x]
    return x
out = {}
for p in sys.argv[2:]:
    if not os.path.exists(p): continue
    m = json.load(open(p))
    if "variant" not in m:  # the check part: compare its result blocks (inputs differ only by the reviewer's paths)
        a = json.load(open(os.path.join(A, "eng11fe_check.json")))
        blocks = [k for k in m if k.startswith("c") and k[1].isdigit()] + ["passed"]
        out["check"] = dict(file=p, blocks=blocks, identical_blocks=[k for k in blocks if nt(m.get(k)) == nt(a.get(k))],
                            differing_blocks=[k for k in blocks if nt(m.get(k)) != nt(a.get(k))], note="t_s (wall time) ignored",
                            input_sha_same=all(m["inputs"]["files"][k]["sha256_16"] == a["inputs"]["files"][k]["sha256_16"] for k in a["inputs"]["files"] if k in m["inputs"]["files"] and k != "m2_eng11"))
        continue
    v = m["variant"]; a = json.load(open(os.path.join(A, f"eng11fe_{v}.json")))
    same = 0; diff = []
    for k, r in m["rows"].items():
        q = a["rows"].get(k)
        keys = ("pass_6dB", "gm_up_min_dB", "first_fail", "n_eval", "n_corners", "n_below_6dB")
        if q is not None and all(r.get(x) == q.get(x) for x in keys): same += 1
        else: diff.append(dict(row=k, mine={x: r.get(x) for x in keys}, author=None if q is None else {x: q.get(x) for x in keys}))
    out[v] = dict(file=p, rows_compared=len(m["rows"]), identical=same, differing=diff, author_rows=len(a["rows"]))
json.dump(out, open(sys.argv[1], "w"), indent=1)
for v, r in out.items():
    if v == "check": print(f"check  identical blocks {r['identical_blocks']}; differing {r['differing_blocks']}; input shas same (bar m2_eng11 redirect) {r['input_sha_same']}")
    else: print(f"{v:6s} identical {r['identical']}/{r['rows_compared']} (author rows {r['author_rows']}); differing {len(r['differing'])}")
