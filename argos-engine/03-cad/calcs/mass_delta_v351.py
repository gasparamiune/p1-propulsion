"""Per-part and per-group mass delta between two mass_variant_v351.py outputs, v1, 2026-10-13, Mechanical.

usage: mass_delta_v351.py BASE.json VARIANT.json [OUT.json]
Prints every part whose mass changed by more than 0.1 g (per group) and the group/total deltas (wet and burnout).
"""
from __future__ import annotations
import json, sys
from pathlib import Path


def main():
    A = json.loads(Path(sys.argv[1]).read_text())
    B = json.loads(Path(sys.argv[2]).read_text())
    rows = []
    for pn in sorted(set(A["parts"]) | set(B["parts"])):
        a = A["parts"].get(pn, {}).get("m_by_group_kg", {})
        b = B["parts"].get(pn, {}).get("m_by_group_kg", {})
        for g in sorted(set(a) | set(b)):
            d = b.get(g, 0.0) - a.get(g, 0.0)
            if abs(d) > 1e-4:
                rows.append({"pn": pn, "group": g, "base_kg": round(a.get(g, 0.0), 5), "variant_kg": round(b.get(g, 0.0), 5), "delta_kg": round(d, 5),
                             "tag_variant": B["parts"].get(pn, {}).get("tag", "")[:120]})
    out = {"base": sys.argv[1], "variant": sys.argv[2], "overrides_variant": B.get("overrides_extra"), "rows": rows, "states": {}}
    for st in ("wet", "burnout"):
        ga, gb = A["states"][st]["groups_kg"], B["states"][st]["groups_kg"]
        out["states"][st] = {"groups_delta_kg": {g: round(gb.get(g, 0.0) - ga.get(g, 0.0), 5) for g in sorted(set(ga) | set(gb))},
                             "total_delta_kg": round(B["states"][st]["total_kg"] - A["states"][st]["total_kg"], 5)}
    for r in rows:
        print(f"{r['pn']:16s} {r['group']:8s} {r['base_kg']*1e3:9.2f} g -> {r['variant_kg']*1e3:9.2f} g  d {r['delta_kg']*1e3:+8.2f} g")
    for st, d in out["states"].items():
        print(st, d)
    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
