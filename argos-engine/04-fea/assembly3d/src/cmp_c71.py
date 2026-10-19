#!/usr/bin/env python3
"""Compare per-part minimum margins of a legacy (asm v1.1) post file with its v1.2 (REPORT 7.1 fix) re-solve.
usage: cmp_c71.py LEGACY_JSON C71_JSON [set=regular] -> prints a table and writes results/cmp_<c71 stem>.json (fea3d 2026-10-19)."""
import json, sys
from pathlib import Path
RES = Path("/home/claude/work/fea3d/results")
a, b = (json.loads((RES / f).read_text()) for f in sys.argv[1:3])
want = dict(x.split("=") for x in sys.argv[3:] if "=" in x).get("set", "regular")


def table(d):
    out = {}
    for st, sd in d["states"].items():
        for cid, cd in sd["cases"].items():
            for m in cd["margins"]:
                if m.get("set") != want:
                    continue
                k = (cid, st, m["part"])
                out[k] = (m.get("MS"), m.get("MS_ult"))
    return out


def lc3(d):
    out = {}
    for m in d.get("margins", []):
        if m.get("set") != want:
            continue
        k = ("LC3", d.get("run", "?").replace("_c71", ""), m["part"])
        cur = out.get(k)
        if cur is None or (m.get("MS") is not None and m["MS"] < cur[0]):
            out[k] = (m.get("MS"), m.get("MS_ult"))
    return out


ta, tb = (table(a), table(b)) if "states" in a else (lc3(a), lc3(b))
rows = []
for k in sorted(set(ta) | set(tb)):
    va, vb = ta.get(k, (None, None)), tb.get(k, (None, None))
    d = None if None in (va[0], vb[0]) else vb[0] - va[0]
    rows.append({"case": k[0], "state": k[1], "part": k[2], "MS_y_v11": va[0], "MS_y_v12": vb[0], "MS_u_v11": va[1], "MS_u_v12": vb[1], "dMS_y": d})
big = sorted([r for r in rows if r["dMS_y"] is not None], key=lambda r: -abs(r["dMS_y"]))
print(f"{len(rows)} rows; largest |dMS_y|:")
for r in big[:25]:
    f = lambda v: "-" if v is None else f"{v:+.3f}"   # noqa: E731
    print(f"{r['case']:6s} {r['state']:9s} {r['part']:8s} y {f(r['MS_y_v11'])} -> {f(r['MS_y_v12'])}  u {f(r['MS_u_v11'])} -> {f(r['MS_u_v12'])}  d {f(r['dMS_y'])}")
(RES / f"cmp_{Path(sys.argv[2]).stem}.json").write_text(json.dumps({"legacy": sys.argv[1], "v12": sys.argv[2], "set": want, "rows": rows}, indent=1))
