# REV-GNC-4 (a): the author's own self-check rule re-applied by the reviewer (to test the 32 / 0 claim only)
import json, re, sys
d = json.load(open(sys.argv[1]))
P = d["rev2p1_document_self_check"]["patterns"]
MK = ("SUPERSEDED", "WITHDRAWN", "NOT ADOPTED", "NOT adopted", "REFUTED", "REPLACED", "HISTORY", "NOT armed", "not armed")
hits = []
def walk(x, path):
    if isinstance(x, dict):
        for k, v in x.items(): walk(v, path + [str(k)])
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, path + [str(i)])
    elif isinstance(x, str):
        for n, pat in P.items():
            for m in re.finditer(pat, x):
                win = x[max(0, m.start() - 200): m.end() + 200]
                ok = any("superseded" in p.lower() for p in path) or x.startswith(("SUPERSEDED", "HISTORY")) or any(k in win for k in MK)
                hits.append((n, "/".join(path), ok))
walk(d, [])
h2 = [h for h in hits if not h[1].startswith("rev2p1_document_self_check")]
print("author rule: hits", len(h2), "unmarked", sum(1 for h in h2 if not h[2]), "(excluding the self-check block, whose pattern strings match themselves:", len(hits) - len(h2), ")")
