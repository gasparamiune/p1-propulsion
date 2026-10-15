"""Solver budget probe: mesh the case at size h, internal pressure 1 MPa on the bore, fix one end ring, solve with ccx SPOOLES
(and optionally ITERATIVE CHOLESKY); record wall time and peak RSS."""
import sys, time, subprocess, os, resource, gmsh, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
brep, h, solver, wd = sys.argv[1], float(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
wd.mkdir(parents=True, exist_ok=True)
PERM = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0); gmsh.option.setNumber("General.NumThreads", 1)
gmsh.model.occ.importShapes(brep); gmsh.model.occ.synchronize()
gmsh.option.setNumber("Mesh.MeshSizeMax", h); gmsh.option.setNumber("Mesh.MeshSizeMin", 0.5)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12); gmsh.option.setNumber("Mesh.ElementOrder", 2)
gmsh.option.setNumber("Mesh.Algorithm3D", 10); gmsh.option.setNumber("Mesh.Optimize", 1); gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
gmsh.model.mesh.generate(3)
tags, X, _ = gmsh.model.mesh.getNodes(); X = X.reshape(-1, 3)
et, etags, en = gmsh.model.mesh.getElements(3)
conn = np.array([e for t, e in zip(et, en) if t == 11][0]).reshape(-1, 10)
gmsh.finalize()
idx = {int(t): i + 1 for i, t in enumerate(tags)}
conn = np.vectorize(idx.get)(conn)[:, PERM]
r = np.hypot(X[:, 0], X[:, 1])
FACES = {1: (0, 1, 2), 2: (0, 3, 1), 3: (1, 3, 2), 4: (2, 3, 0)}
from collections import defaultdict
fc = defaultdict(list)
for e, c in enumerate(conn):
    for f, (a, b, d) in FACES.items():
        fc[tuple(sorted((c[a], c[b], c[d])))].append((e + 1, f))
bore = [v[0] for k, v in fc.items() if len(v) == 1 and all(r[n - 1] < 29.0 for n in k) and all(-140 < X[n - 1, 2] < 0 for n in k)]
fix = [i + 1 for i in range(len(X)) if X[i, 2] > 139.4]
with open(wd / "t.inp", "w") as f:
    f.write("*NODE\n"); [f.write(f"{i+1},{x[0]:.6f},{x[1]:.6f},{x[2]:.6f}\n") for i, x in enumerate(X)]
    f.write("*ELEMENT,TYPE=C3D10,ELSET=EALL\n"); [f.write(f"{e+1}," + ",".join(map(str, c)) + "\n") for e, c in enumerate(conn)]
    f.write("*NSET,NSET=NFIX\n"); [f.write(f"{n}\n") for n in fix]
    f.write("*MATERIAL,NAME=AL\n*ELASTIC\n68900,0.33\n*SOLID SECTION,ELSET=EALL,MATERIAL=AL\n*BOUNDARY\nNFIX,1,3\n")
    f.write(f"*STEP\n*STATIC{', SOLVER=' + solver if solver != 'SPOOLES' else ''}\n*DLOAD\n")
    [f.write(f"{e},P{fa},1.0\n") for e, fa in bore]
    f.write("*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n")
print("nodes", len(X), "elems", len(conn), "bore faces", len(bore), "fix", len(fix), flush=True)
from ccxrun import run_ccx
print(solver, run_ccx("t", wd, threads=2))
