#!/usr/bin/env python3
"""preview_views.py — Vistas del ensamblaje sin Blender (matplotlib, sombreado plano).

Genera blender/renders/vista_*.png: lateral (x–z), planta (x–y), frontal (y–z) y perspectiva,
en marcha (φ=0) y basculada (φ=φmax), con espejo, flotación y fondo del bote como referencia.
Sirve de respaldo cuando bpy no está disponible y como verificación visual rápida.
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

COLORS = {"MNT": "#3b6ea8", "HSG": "#e08a1e", "DRV": "#7a7a7a", "PRP": "#c0392b", "STR": "#8e44ad",
          "ELE": "#27ae60", "SAF": "#f1c40f"}


def scene(steer=0.0, tilt=0.0, include_free=False):
    import params as P
    from build_all import load_parts, loc_matrix
    p = P.load()
    items = []
    for m in load_parts():
        meta = m.META
        if meta["frame"] == "boat_free" and not include_free:
            continue
        mesh = trimesh.load(ROOT / "04_diseno" / "stl" / "asm" / f"{meta['id']}.stl", force="mesh")
        for L in m.placements(p, steer, tilt):
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
    t, H = p.tr_t, p.tr_H
    zwl = p.layout["z_wl_mm"]
    if view == "side":
        ax.fill([-t, 0, 0, -t], [-H, -H, 0, 0], color="#bbbbbb", zorder=0, label="espejo")
        ax.plot([-900, 0], [-H, -H], color="#888", lw=2)            # fondo del bote
        ax.axhline(zwl, color="#1f77b4", ls="--", lw=1, label="flotación")
        ax.legend(loc="lower left", fontsize=8)
    elif view == "top":
        W = p.inp["boat"]["transom"]["top_width_mm"]
        ax.fill([-t, 0, 0, -t], [-W / 2, -W / 2, W / 2, W / 2], color="#bbbbbb", zorder=0)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import params as P
    pp = P.load()
    states = [("marcha", 0.0, 0.0), ("basculada", 0.0, pp.tilt_range), ("dir35", pp.steer_range, 0.0)]
    for name, s, t in states:
        p, items = scene(s, t)
        fig, ax = plt.subplots(figsize=(13, 6.5))
        ortho(ax, items, (0, 2), 1, -1)
        reference(ax, p, "side")
        ax.set_aspect("equal"); ax.autoscale(); ax.grid(alpha=0.2)
        ax.set_xlabel("x [mm] (popa →)"); ax.set_ylabel("z [mm]")
        ax.set_title(f"P1 — vista lateral ({name}: ψ={s:.0f}°, φ={t:.0f}°)")
        fig.tight_layout(); fig.savefig(OUT / f"vista_lateral_{name}.png", dpi=110); plt.close(fig)
        if name != "basculada":
            fig, ax = plt.subplots(figsize=(13, 6))
            ortho(ax, items, (0, 1), 2, 1)
            reference(ax, p, "top")
            ax.set_aspect("equal"); ax.autoscale(); ax.grid(alpha=0.2)
            ax.set_xlabel("x [mm]"); ax.set_ylabel("y [mm] (babor ↑)")
            ax.set_title(f"P1 — planta ({name})")
            fig.tight_layout(); fig.savefig(OUT / f"vista_planta_{name}.png", dpi=110); plt.close(fig)
    # perspectiva
    p, items = scene(0.0, 0.0)
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")
    for pid, m in items:
        base = np.array(matplotlib.colors.to_rgb(COLORS[pid.split("-")[1]]))
        sh = light(m.face_normals)
        pc = Poly3DCollection(m.triangles, facecolors=np.clip(base[None, :] * sh[:, None], 0, 1), edgecolors="none")
        ax.add_collection3d(pc)
    ax.set_xlim(-300, 1300); ax.set_ylim(-500, 500); ax.set_zlim(-650, 350)
    ax.set_box_aspect((1600, 1000, 1000))
    ax.view_init(elev=22, azim=-58)
    ax.set_title("P1 — perspectiva (en marcha)")
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    fig.tight_layout(); fig.savefig(OUT / "vista_perspectiva.png", dpi=110); plt.close(fig)
    print(f"vistas: {len(list(OUT.glob('vista_*.png')))} PNG en {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
