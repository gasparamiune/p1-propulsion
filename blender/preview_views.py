#!/usr/bin/env python3
"""preview_views.py — Vistas del ensamblaje del waterjet sin Blender (matplotlib, sombreado plano).

Genera blender/renders/vista_*.png: lateral (x–z) y planta (x–y) en marcha (boquilla recta, bucket
arriba), con la boquilla a +25° y con el bucket abajo, más una perspectiva. Casco de referencia
semitransparente omitido (se dibuja la flotación). Verificación visual rápida del CAD.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "04_diseno"))
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent / "renders"

COLORS = {"INT": "#3b6ea8", "PMP": "#7f8c8d", "DRV": "#5d6d7e", "MOT": "#2c3e50", "STE": "#c0392b",
          "REV": "#8e44ad", "CTL": "#e08a1e", "ELE": "#27ae60", "BAT": "#16a085", "REF": "#bdc3c7"}


def scene(steer=0.0, bucket=0, include_ref=False):
    import params as P
    from build_all import load_parts, loc_matrix
    p = P.load()
    items = []
    for m in load_parts():
        meta = m.META
        if meta.get("group") == "ref" and not include_ref:
            continue
        f = ROOT / "04_diseno" / "stl" / "asm" / f"{meta['id']}.stl"
        if not f.exists():
            continue
        mesh = trimesh.load(f, force="mesh")
        for L in m.placements(p, steer, bucket):
            mm = mesh.copy()
            mm.apply_transform(np.array(loc_matrix(L)))
            items.append((meta["id"], mm))
    return p, items


def light(normals, d=np.array([0.4, -0.5, 0.75])):
    d = d / np.linalg.norm(d)
    return 0.35 + 0.65 * np.clip(np.abs(normals @ d), 0, 1)


def ortho(ax, items, axes=(0, 2), depth_axis=1, depth_sign=-1):
    polys, cols, depth = [], [], []
    for pid, m in items:
        base = np.array(matplotlib.colors.to_rgb(COLORS[pid.split("-")[1]]))
        tri = m.triangles
        sh = light(m.face_normals)
        for t, s in zip(tri, sh):
            polys.append(t[:, axes])
            cols.append(np.clip(base * s, 0, 1))
            depth.append(depth_sign * t[:, depth_axis].mean())
    order = np.argsort(depth)
    pc = PolyCollection([polys[i] for i in order], facecolors=[cols[i] for i in order], edgecolors="none")
    ax.add_collection(pc)


def reference(ax, p, view):
    import json
    sz = json.loads((ROOT / "resultados" / "sizing.json").read_text(encoding="utf-8"))
    if view == "side":
        ax.plot([0, 0], [0, p.inp["boat"]["transom_height_m"] * 1000], color="#888", lw=2, label="espejo")
        ax.plot([0, 1400], [0, 0], color="#888", lw=2)                       # fondo del casco
        ax.axhline(sz["hydrostatics"]["draft_m"] * 1000, color="#1f77b4", ls="--", lw=1, label="flotación en reposo")
        ax.legend(loc="upper left", fontsize=8)
        ax.invert_xaxis()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import params as P
    pp = P.load()
    states = [("marcha", 0.0, 0), ("boquilla25", pp.steer_max, 0), ("reversa", 0.0, 1)]
    for name, s, bk in states:
        p, items = scene(s, bk)
        fig, ax = plt.subplots(figsize=(13, 6.5))
        ortho(ax, items, (0, 2), 1, -1)
        reference(ax, p, "side")
        ax.set_aspect("equal"); ax.autoscale(); ax.grid(alpha=0.2)
        ax.set_xlabel("x [mm] desde el espejo (proa ←)"); ax.set_ylabel("z [mm] sobre la quilla")
        ax.set_title(f"P1-J — vista lateral ({name}: δ={s:.0f}°, bucket {'abajo' if bk else 'arriba'})")
        fig.tight_layout(); fig.savefig(OUT / f"vista_lateral_{name}.png", dpi=110); plt.close(fig)
        if name != "reversa":
            fig, ax = plt.subplots(figsize=(13, 6))
            ortho(ax, items, (0, 1), 2, 1)
            ax.set_aspect("equal"); ax.autoscale(); ax.grid(alpha=0.2); ax.invert_xaxis()
            ax.set_xlabel("x [mm] (proa ←)"); ax.set_ylabel("y [mm] (babor ↑)")
            ax.set_title(f"P1-J — planta ({name})")
            fig.tight_layout(); fig.savefig(OUT / f"vista_planta_{name}.png", dpi=110); plt.close(fig)
    # perspectiva
    p, items = scene(0.0, 0)
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")
    for pid, m in items:
        base = np.array(matplotlib.colors.to_rgb(COLORS[pid.split("-")[1]]))
        sh = light(m.face_normals)
        pc = Poly3DCollection(m.triangles, facecolors=np.clip(base[None, :] * sh[:, None], 0, 1), edgecolors="none")
        ax.add_collection3d(pc)
    ax.set_xlim(-450, 1550); ax.set_ylim(-500, 500); ax.set_zlim(-100, 500)
    ax.set_box_aspect((2000, 1000, 600))
    ax.view_init(elev=24, azim=-130)
    ax.set_title("P1-J — perspectiva (en marcha)")
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    fig.tight_layout(); fig.savefig(OUT / "vista_perspectiva.png", dpi=110); plt.close(fig)
    print(f"vistas: {len(list(OUT.glob('vista_*.png')))} PNG en {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
