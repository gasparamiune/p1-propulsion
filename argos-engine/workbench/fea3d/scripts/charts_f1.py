"""FEA3D F1 datasheet charts (matplotlib; fea3d successor 2026-10-15).

C1  per-part minimum margin of safety by load case (regular node set, part criterion of post_f1 / post_lc3 / lc3_bound)
C2  airframe interface: per-hole screw shear and axial load envelopes (rigid airframe; compliant if available)
C3  mesh convergence at the governing locations (q_max over regular nodes within 3 mm vs local edge length)
All values SIM (FE, CalculiX 2.21) unless the label says otherwise; not physical approval.  Units: MPa, N, mm.
usage: charts_f1.py [c1] [c2] [c3]
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402

W = Path("/home/claude/work/fea3d")
TAB = W / "results" / "tables"
OUT = W / "figs" / "f1"
FOOT = "ARGOS H1 engine | FEA3D (CalculiX 2.21, C3D10) on CAD v3.5.1 (STEP 4ca22820c796b670) | SIM - not physical approval | fea3d 2026-10-15"


def foot(fig):
    fig.text(0.01, 0.005, FOOT, fontsize=7, color="dimgray", ha="left", va="bottom")


def c1():
    rows = json.loads((TAB / "f1_part_margins.json").read_text())
    cols = [("LC1 steady max thrust, hot (SF 1.5 yield / 2.0 ult)", "LC1", "#4C72B0"),
            ("FA-1 min of FA1Q/D/U/S/T (SF 1.0, CHANGELOG 194)", None, "#DD8452"),
            ("LC3 cold, 8 deg stop (SF 1.5 / 2.0)", "LC3cold", "#55A868"),
            ("LC3 hot lower bound (SF 1.5 / 2.0)", "LC3hot_bound", "#8172B3")]

    def yu(r, k):
        v = [r.get(f"{k}_MS_y"), r.get(f"{k}_MS_u")]
        v = [x for x in v if x is not None]
        return min(v) if v else None

    def fa1(r):
        v = [r.get(k) for k in ("FA1Q_MS_y", "FA1D_MS_y", "FA1U_MS_y", "FA1S_MS_y", "FA1T_MS_y", "FA1Q_MS_u", "FA1U_MS_u", "FA1S_MS_u", "FA1T_MS_u")]
        v = [x for x in v if x is not None]
        return min(v) if v else None
    rows = sorted(rows, key=lambda r: r["min_MS"])
    parts = [r["part"] for r in rows]
    n = len(parts)
    fig, ax = plt.subplots(figsize=(11, 0.42 * n + 3.0))
    hgt = 0.2
    cap = 3.0
    for j, (lab, key, colr) in enumerate(cols):
        vals = [fa1(r) if key is None else yu(r, key) for r in rows]
        y = np.arange(n) + (j - 1.5) * hgt
        v = np.array([np.nan if x is None else min(x, cap) for x in vals])
        bars = ax.barh(y, v, height=hgt, color=colr, label=lab, edgecolor="none")
        for yi, x in zip(y, vals):
            if x is None:
                continue
            txt = f"{x:+.2f}" if x < cap else f">{cap:.0f} ({x:+.1f})" if x < 999 else ">+999"
            ax.text(min(x, cap) + (0.03 if x >= 0 else -0.03), yi, txt, va="center", ha="left" if x >= 0 else "right", fontsize=6.5,
                    color="firebrick" if x < 0 else "black")
    ax.axvline(0.0, color="firebrick", lw=1.2)
    ax.set_yticks(np.arange(n))
    ax.set_yticklabels([f"{r['part']} ({r['material']})" for r in rows], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(-1.0, cap + 0.6)
    ax.set_xlabel("MS = allowable / (SF x stress) - 1; bar = min(yield, ultimate) criterion  (axis clipped at +3)", fontsize=8)
    ax.grid(axis="x", ls=":", lw=0.6)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.045), ncol=2, fontsize=8, framealpha=0.9)
    ax.set_title("F1-C1  Minimum margin of safety per part and load case (regular node set; metals von Mises vs Fty(T), brittle s1/St, s3/Sc SF 2.0)\n"
                 "LC1 = max of B1_21.65/B1_19/B1_2/B1_1 S-AX thermal states; FA-1 per CHANGELOG 194; LC3 = 8 stop poses x 64 sub-cases", fontsize=9)
    foot(fig)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    out = OUT / "F1-C1_part_margins.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print("wrote", out)


def c2():
    d = json.loads((TAB / "f1_icd_airframe.json").read_text())
    cases = [k for k in d]
    holes = sorted(d[cases[0]]["holes"].keys(), key=lambda h: (h.split("_")[1], int(h.split("_")[-1])))
    fig, axs = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True)
    x = np.arange(len(holes))
    wd = 0.8 / len(cases)
    colrs = ["#4C72B0", "#DD8452", "#C44E52", "#55A868", "#8172B3", "#937860"]
    for j, c in enumerate(cases):
        H = d[c]["holes"]
        sh = [H[h]["max_shear_N"] if h in H else np.nan for h in holes]
        ax_ = [H[h]["max_radial_out_N"] if h in H else np.nan for h in holes]
        axs[0].bar(x + (j - (len(cases) - 1) / 2) * wd, sh, width=wd, color=colrs[j % 6], label=c)
        axs[1].bar(x + (j - (len(cases) - 1) / 2) * wd, ax_, width=wd, color=colrs[j % 6], label=c)
    axs[0].set_ylabel("max screw shear per hole (N)\n= hypot(tangential, axial Z)")
    axs[1].set_ylabel("max radial pull-out per hole (N)\n(tension along the screw)")
    axs[1].set_xticks(x)
    axs[1].set_xticklabels(holes, rotation=60, fontsize=7)
    for a in axs:
        a.grid(axis="y", ls=":", lw=0.6)
    axs[0].legend(fontsize=8, ncol=3)
    axs[0].set_title("F1-C2  Airframe interface: 16 x M5 hole reaction envelopes (engine -> airframe; rigid airframe unless 'compliant')\n"
                     "M5 screws are radial through the airframe wall: shear = transverse to the screw, pull-out = radial outward; envelope over states / sub-cases / poses", fontsize=9)
    foot(fig)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    out = OUT / "F1-C2_airframe_holes.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print("wrote", out)


def c3():
    d = json.loads((W / "results" / "f1_convergence.json").read_text())
    pts = d["points"]
    fig, axs = plt.subplots(1, len(pts), figsize=(4.2 * len(pts), 4.6))
    axs = np.atleast_1d(axs)
    for a, (key, p) in zip(axs, pts.items()):
        L = sorted(p["levels"], key=lambda r: -r["h_loc_mm"])
        h = [r["h_loc_mm"] for r in L]
        qr = [r["q_max_reg_MPa"] for r in L]
        qa = [r["q_max_all_MPa"] for r in L]
        a.plot(h, qr, "o-", color="#4C72B0", label="max over regular nodes")
        a.plot(h, qa, "s--", color="#C44E52", label="max over all nodes (incl. singular)")
        for r, hh, q in zip(L, h, qr):
            a.annotate(f"{r['level']}\nMS {r['MS_min_reg']:+.3f}" if r["MS_min_reg"] is not None else r["level"], (hh, q),
                       textcoords="offset points", xytext=(4, -22), fontsize=7)
        g = p.get("gci_q_max_reg")
        if g and g.get("q_ext") is not None:
            a.axhline(g["q_ext"], color="gray", ls=":", lw=1)
            a.text(min(h), g["q_ext"], f" Richardson {g['q_ext']:.1f} (p {g['p']:.2f}, GCI {100 * g['GCI_fine']:.1f} %)", fontsize=7, va="bottom")
        a.invert_xaxis()
        a.set_xlabel("local mean tet edge h (mm)")
        a.set_ylabel(("s1" if p["levels"][0]["q"] == "s1" else "von Mises") + " (MPa)")
        a.set_title(key, fontsize=9)
        a.grid(ls=":", lw=0.6)
        a.legend(fontsize=7)
    fig.suptitle("F1-C3  Mesh convergence at the governing locations (L1 global -> R2 -> R3 local ball refinement; same loads, ties and thermal map)", fontsize=9)
    foot(fig)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    out = OUT / "F1-C3_convergence.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    which = sys.argv[1:] or ["c1", "c2"]
    for w in which:
        globals()[w]()
