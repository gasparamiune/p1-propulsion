"""F2 (S-3D on CAD v3.5.1) chart: per gimbal part, min(MS_y, MS_u) by case (fea3d 2026-10-19).
S3D-C1: GS / TD / LC6 / LC2F (9 cone poses, lever roots refined R3), SR = F1 LC3 runaway (L1 regular set) and its R3 lever-root value, FA1T.
Values from results/s3d_summary_v351.json (SIM).  Bars clipped at +3 (labels give the true value).  usage: chart_s3d.py
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import sys
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
from charts_f1 import foot               # noqa: E402

W = Path("/home/claude/work/fea3d")
S = json.loads((W / "results" / "s3d_summary_v351.json").read_text())
PARTS = ["GM-01", "GM-02", "GM-03", "GM-16a", "GM-16b", "GM-08a", "GM-08b", "GM-09", "GM-10", "GM-13", "GM-14"]
CASES = [("GS servo stall (SF 1.5/2.0)", "GS", "#C44E52"), ("TD touchdown", "TD", "#4C72B0"), ("LC6 10 g landing", "LC6", "#55A868"),
         ("LC2F stuck pintle (SF 1.0/1.5)", "LC2F", "#8172B3"), ("SR runaway = F1 LC3, L1 set", "SR", "#DD8452"),
         ("SR lever root R3", "SR_R3", "#937860"), ("FA1T thrust spike (SF 1.0)", "FA1T", "#64B5CD")]


def val(part, c):
    pc = S["per_case"]
    if c == "SR_R3":
        r = pc.get("SR", {}).get(part, {})
        v = [r.get("R3_MS"), r.get("R3_MS_ult")]
    else:
        r = pc.get(c, {}).get(part)
        if not r:
            return None
        v = [r.get("MS"), r.get("MS_ult_min", r.get("MS_ult"))]
    v = [x for x in v if x is not None]
    return min(v) if v else None


fig, ax = plt.subplots(figsize=(13, 6.5))
n = len(CASES)
w = 0.8 / n
x = np.arange(len(PARTS))
for j, (lab, c, col) in enumerate(CASES):
    vals = [val(p, c) for p in PARTS]
    h = [min(v, 3.0) if v is not None else np.nan for v in vals]
    bars = ax.bar(x + (j - n / 2 + 0.5) * w, h, w, label=lab, color=col)
    for xi, v in zip(x + (j - n / 2 + 0.5) * w, vals):
        if v is not None and v < 0.5:
            ax.text(xi, min(v, 3.0) + (0.04 if v >= 0 else -0.04), f"{v:+.2f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=6.5, rotation=90)
ax.axhline(0, color="k", lw=0.8)
ax.set_xticks(x)
ax.set_xticklabels(PARTS)
ax.set_ylim(-0.6, 3.75)
ax.set_ylabel("min(MS yield, MS ultimate) [-]  (bars clipped at +3)")
ax.set_title("S3D-C1  Gimbal parts, CAD v3.5.1: minimum margin by case (envelope over the 9 cone poses; SR over the 8 stop poses)  [asm v1.2]\n"
             "cold; lever roots of GM-01 / GM-02 refined (R3) in the cone runs; labels on bars below +0.5", fontsize=10)
ax.legend(fontsize=8, ncol=4, loc="upper center")
ax.grid(axis="y", alpha=0.3)
foot(fig)
fig.tight_layout(rect=(0, 0.02, 1, 1))
out = W / "figs" / "s3d" / "S3D-C1_gimbal_margins.png"
fig.savefig(out, dpi=140)
print("wrote", out)
