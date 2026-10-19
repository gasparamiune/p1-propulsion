# Lead presentation chart: lowest margin of each part over every load case
# (data: hub 04-fea/assembly3d/tables/margin_matrix_v351.json, SIM; chart is DERIVED presentation only)
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = "/home/claude/work/shared-fallback/engine/04-fea/assembly3d/tables/margin_matrix_v351.json"
OUT = sys.argv[1]
CASE_NAMES = {
    "LC1": "max thrust (hot)", "FA1S": "pressure spike (bound)", "FA1Q": "pressure spike",
    "FA1D": "pressure spike", "FA1U": "pressure spike", "FA1T": "thrust spike",
    "LC3 cold": "gimbal at stop", "LC3 hot bound (DERIVED)": "gimbal at stop + engine heat (bound)",
    "LC3 lever root R3": "gimbal at stop, refined mesh", "GS": "servos at stall",
    "TD": "touchdown", "LC6": "LC6", "LC2F": "LC2F", "F2 hot bound (DERIVED)": "servos at stall + engine heat (bound)",
}
d = json.load(open(SRC))
rows = []
for r in d["rows"]:
    best = None
    for col, cell in r["cells"].items():
        for k in (0, 1):
            v = cell[k] if isinstance(cell, list) and len(cell) > k else None
            if isinstance(v, (int, float)) and (best is None or v < best[0]):
                best = (v, col)
    lc1 = [v for v in (r["cells"].get("LC1") or [None, None])[:2] if isinstance(v, (int, float))]
    gs = [v for v in (r["cells"].get("GS") or [None, None])[:2] if isinstance(v, (int, float))]
    rows.append((r["part"], r["material"], best[0], best[1], min(lc1) if lc1 else None, min(gs) if gs else None))
rows.sort(key=lambda x: x[2])
fig, ax = plt.subplots(figsize=(9, 8.5), dpi=150)
y = range(len(rows))
vals = [min(v, 3.0) for _, _, v, _, _, _ in rows]
cols = ["#c0392b" if v < 0 else ("#e67e22" if v < 0.25 else "#4a7fb5") for _, _, v, _, _, _ in rows]
ax.barh(list(y), vals, color=cols, height=0.65)
ax.set_yticks(list(y))
ax.set_yticklabels([f"{p} ({m.replace('AL', 'Al ')})" for p, m, _, _, _, _ in rows], fontsize=8)
ax.invert_yaxis()
ax.axvline(0, color="black", lw=1)
for i, (p, m, v, c, lc1, gs) in enumerate(rows):
    lab = f"{v:+.2f}  {CASE_NAMES.get(c, c)}" if v < 3 else f">+3  {CASE_NAMES.get(c, c)}"
    if p == "TC-01":
        lab += ";  +0.23 on the provisional period reading"
    elif v < 0 and lc1 is not None and lc1 < 0 and c != "LC1":
        lab += f";  max thrust alone {lc1:+.2f}"
    elif v < 0 and gs is not None and gs < 0 and c != "GS":
        lab += f";  servos at stall {gs:+.2f}"
    x = max(min(v, 3.0), 0.0)
    ax.text(x + 0.04, i, lab, va="center", fontsize=7.2)
ax.set_xlim(-0.6, 4.6)
ax.set_xlabel("Lowest margin of safety over every load case (below 0 = fails the criterion)", fontsize=9)
ax.set_title("ARGOS H1 engine, 3D FEA of the assembled engine (CAD v3.5.1)\nLowest margin per part across all load cases", fontsize=10)
fig.text(0.01, 0.005, "Simulation (CalculiX), not physical approval. Data: 04-fea/assembly3d/tables/margin_matrix_v351.json. "
         "Red = negative, orange = below +0.25.", fontsize=6.5, color="#555")
fig.tight_layout(rect=(0, 0.02, 1, 1))
fig.savefig(OUT)
print("rows", len(rows), "negatives", [(p, round(v, 3), c) for p, _, v, c, _, _ in rows if v < 0])
