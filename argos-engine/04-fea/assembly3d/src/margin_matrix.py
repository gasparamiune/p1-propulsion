"""Every part x every case: minimum margins on CAD v3.5.1, asm v1.2 (fea3d 2026-10-19), for the final handback / Mechanical.

Sources (all SIM unless the column says DERIVED): results/tables/f1_part_margins.json (F1: LC1 4 states, FA1Q/D/U/S/T, LC3 cold 8 stop poses
L1 regular set, LC3 hot lower bound = DERIVED), results/f1_lever_root_GM0x_c71.json (R3 lever-root refinement, LC3 cold),
results/s3d_summary_v351.json (F2 at the 9 cone poses: GS, TD, LC6, LC2F; both lever roots at R3 inside the regular set).
Cell = MS_y / MS_u; '-' = case not evaluated for that part; n/a = no allowable (e.g. carbon-phenolic / graphite ultimate).
usage: margin_matrix.py -> results/tables/margin_matrix_v351.{md,json}
"""
from __future__ import annotations
import json, math
from pathlib import Path

RES = Path("/home/claude/work/fea3d/results")


def f(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    return f"{x:+.3f}" if abs(x) < 100 else ">+99"


def main():
    f1 = {r["part"]: r for r in json.loads((RES / "tables" / "f1_part_margins.json").read_text())}
    s3 = json.loads((RES / "s3d_summary_v351.json").read_text())["per_case"]
    lr = {}
    for p in ("GM-01", "GM-02"):
        fp = RES / f"f1_lever_root_{p.replace('-', '')}_c71.json"
        if fp.exists():
            lv = json.loads(fp.read_text())["levels"]
            r3 = [v for k, v in lv.items() if "r3" in k]
            if r3:
                lr[p] = (r3[0]["MS_regular"], r3[0]["MS_ult_regular"])
    parts = list(f1) + [p for c in ("GS", "TD", "LC6", "LC2F") for p in s3.get(c, {}) if p not in f1]
    parts = list(dict.fromkeys(parts))
    cols = ["LC1", "FA1Q", "FA1S", "FA1T", "LC3 cold", "LC3 hot bound (DERIVED)", "LC3 lever root R3", "GS", "TD", "LC6", "LC2F"]
    rows = []
    for p in parts:
        a = f1.get(p, {})
        c = {}
        c["LC1"] = (a.get("LC1_MS_y"), a.get("LC1_MS_u"), a.get("LC1_state"))
        for k in ("FA1Q", "FA1S", "FA1T"):
            c[k] = (a.get(f"{k}_MS_y"), a.get(f"{k}_MS_u"), None)
        c["LC3 cold"] = (a.get("LC3cold_MS_y"), a.get("LC3cold_MS_u"), a.get("LC3cold_pose"))
        c["LC3 hot bound (DERIVED)"] = (a.get("LC3hot_bound_MS_y"), a.get("LC3hot_bound_MS_u"), None)
        c["LC3 lever root R3"] = (*lr[p], None) if p in lr else (None, None, None)
        for k in ("GS", "TD", "LC6", "LC2F"):
            r = s3.get(k, {}).get(p)
            c[k] = (r["MS"], r.get("MS_ult_min", r.get("MS_ult")), r.get("pose")) if r else (None, None, None)
        vals = [(v[0], k, "y") for k, v in c.items() if v[0] is not None and not (isinstance(v[0], float) and math.isnan(v[0]))] + \
               [(v[1], k, "u") for k, v in c.items() if v[1] is not None and not (isinstance(v[1], float) and math.isnan(v[1]))]
        mn = min(vals) if vals else (None, None, None)
        rows.append({"part": p, "material": a.get("material"), "cells": {k: list(v) for k, v in c.items()}, "min": list(mn)})
    (RES / "tables" / "margin_matrix_v351.json").write_text(json.dumps({"doc": __doc__.split("usage:")[0].strip(), "columns": cols, "rows": rows}, indent=1, default=float))
    L = ["| part | material | " + " | ".join(cols) + " | min (case) |", "|---|---|" + "---|" * len(cols) + "---|"]
    for r in rows:
        cells = []
        for k in cols:
            y, u, _ = r["cells"][k]
            cells.append("-" if y is None and u is None else f"{f(y)} / {f(u)}")
        mn = r["min"]
        L.append(f"| {r['part']} | {r['material'] or ''} | " + " | ".join(cells) + f" | {f(mn[0])} ({mn[1]} {mn[2]}) |" if mn[0] is not None else " | - |")
    (RES / "tables" / "margin_matrix_v351.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
