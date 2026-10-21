"""Surface triangulation of non-meshed CAD instances (servos, PD-02, igniter ...) for proximity tests.  Cached npz."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

ROOT = Path("/home/claude/work/fea3d")


def instance_surface(stem, h=0.5):
    out = ROOT / "geom" / "samples" / f"{stem}_h{h:g}.npz"
    if out.exists():
        z = np.load(out)
        return z["X"], z["T"]
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.occ.importShapes(str(ROOT / "geom" / "v35_neutral" / f"{stem}.brep"))
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeMin", h / 4)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
    gmsh.model.mesh.generate(2)
    tags, xyz, _ = gmsh.model.mesh.getNodes()
    X = xyz.reshape(-1, 3)
    idx = {int(t): i for i, t in enumerate(tags)}
    T = []
    for dim, tag in gmsh.model.getEntities(2):
        et, el, en = gmsh.model.mesh.getElements(2, tag)
        for a, b in zip(et, en):
            if a == 2:
                T.append(np.asarray([idx[int(x)] for x in b]).reshape(-1, 3))
    gmsh.finalize()
    T = np.vstack(T)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, X=X, T=T)
    return X, T


def dist_to_surface(P, X, T, k=8):
    """Distance from points P to a triangulated surface (exact point-triangle distance over k nearest triangles)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import fe3d
    c = X[T].mean(axis=1)
    d, _, _ = fe3d.project_points(P, X, np.hstack([T, T]), c, k=k)
    return d
