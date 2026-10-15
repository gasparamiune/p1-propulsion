"""Tessellation + pyvista helpers for renders and quick-look checks."""
from __future__ import annotations
import numpy as np
import pyvista as pv


def to_pv(shape, tol=0.05, ang=0.3):
    vs, ts = shape.tessellate(tol, ang)
    if not ts:
        return None
    v = np.array([[p.x, p.y, p.z] for p in vs])
    f = np.hstack([[3, *t] for t in ts])
    return pv.PolyData(v, f)


def color_of(material):
    import engmat
    return engmat.color(material)
