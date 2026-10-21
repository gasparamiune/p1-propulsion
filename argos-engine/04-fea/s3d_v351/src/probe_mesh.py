import sys, time, gmsh, numpy as np
from pathlib import Path
brep = sys.argv[1]; h = float(sys.argv[2]); hmin = float(sys.argv[3]); curv = int(sys.argv[4]) if len(sys.argv) > 4 else 12
t0 = time.time()
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0); gmsh.option.setNumber("General.NumThreads", 1)
gmsh.model.occ.importShapes(brep); gmsh.model.occ.synchronize()
faces = gmsh.model.getEntities(2); edges = gmsh.model.getEntities(1)
print("faces", len(faces), "edges", len(edges))
gmsh.option.setNumber("Mesh.MeshSizeMax", h); gmsh.option.setNumber("Mesh.MeshSizeMin", hmin)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", curv); gmsh.option.setNumber("Mesh.ElementOrder", 2)
gmsh.option.setNumber("Mesh.Algorithm3D", 10); gmsh.option.setNumber("Mesh.Optimize", 1)
gmsh.option.setNumber("Mesh.HighOrderOptimize", 0)
gmsh.model.mesh.generate(3)
tags, X, _ = gmsh.model.mesh.getNodes()
et, etags, en = gmsh.model.mesh.getElements(3)
n10 = sum(len(e) for t, e in zip(et, etags) if t == 11)
print("nodes", len(tags), "tet10", n10, "t", round(time.time() - t0, 1))
gmsh.finalize()
