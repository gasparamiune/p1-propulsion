"""fea_plot.py — Mapas de tensión sobre la superficie (matplotlib, sin pantalla)."""
from __future__ import annotations

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, Normalize  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

# Paleta (skill dataviz): secuencial = un solo tono azul claro→oscuro; divergente = azul ↔ gris ↔ rojo
SEQ = LinearSegmentedColormap.from_list("seq_blue", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
DIV = LinearSegmentedColormap.from_list("div_br", ["#184f95", "#6da7ec", "#f0efec", "#ec8b8a", "#b8312f"])
INK, INK2, SURF = "#1f1f1e", "#5c5b57", "#fcfcfb"


def _surface(S, body=None):
    tri = S.ftri
    if body is not None and S.fbody is not None:
        tri = tri[S.fbody == body]
    return tri


def _shade(normals, light=(0.4, -0.6, 0.7)):
    L = np.asarray(light) / np.linalg.norm(light)
    return 0.72 + 0.28 * np.abs(normals @ L)


def stress_figure(S, val, title, path, body=None, views=((25, -60), (25, 120)), diverging=False,
                  label="σ [MPa]", vmax=None, mark=None, deform=None, scale=0.0, axis_labels=("x", "y", "z")):
    tri = _surface(S, body)
    P = S.X if deform is None else S.X + scale * deform
    face_val = val[tri].mean(axis=1)
    if diverging:
        lim = vmax if vmax is not None else max(np.percentile(np.abs(face_val), 99.5), 1e-6)
        norm = TwoSlopeNorm(vcenter=0.0, vmin=-lim, vmax=lim)
        cmap = DIV
    else:
        top = vmax if vmax is not None else np.percentile(face_val, 99.5)
        norm = Normalize(vmin=0.0, vmax=max(top, 1e-6))
        cmap = SEQ
    rgba = cmap(norm(face_val))
    n = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    rgba[:, :3] *= _shade(n)[:, None]
    verts = P[tri]
    lo, hi = verts.reshape(-1, 3).min(0), verts.reshape(-1, 3).max(0)
    fig = plt.figure(figsize=(5.2 * len(views) + 0.8, 5.0), facecolor=SURF)
    for i, (el, az) in enumerate(views):
        ax = fig.add_subplot(1, len(views), i + 1, projection="3d", facecolor=SURF)
        pc = Poly3DCollection(verts, facecolors=rgba, edgecolors="none", linewidths=0)
        ax.add_collection3d(pc)
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
        ax.set_box_aspect(hi - lo)
        ax.view_init(elev=el, azim=az)
        for a, lab in zip((ax.xaxis, ax.yaxis, ax.zaxis), axis_labels):
            a.set_pane_color((0.99, 0.99, 0.985, 1.0))
            a.label.set_color(INK2)
        ax.set_xlabel(axis_labels[0] + " [mm]", fontsize=7, color=INK2)
        ax.set_ylabel(axis_labels[1] + " [mm]", fontsize=7, color=INK2)
        ax.set_zlabel(axis_labels[2] + " [mm]", fontsize=7, color=INK2)
        ax.tick_params(labelsize=6, colors=INK2)
        if mark is not None:
            ax.scatter(*np.asarray(mark)[:, None], s=40, c="none", edgecolors=INK, linewidths=1.2, depthshade=False)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, ax=fig.axes, shrink=0.75, pad=0.02, fraction=0.03)
    cb.set_label(label, color=INK, fontsize=9)
    cb.ax.tick_params(labelsize=7, colors=INK2)
    fig.suptitle(title, fontsize=10, color=INK, x=0.02, ha="left")
    fig.savefig(path, dpi=110, facecolor=SURF)
    plt.close(fig)
    return str(path)
