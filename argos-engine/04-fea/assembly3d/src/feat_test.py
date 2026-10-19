"""Feature probe for ccx 2.21: TIE between non-conforming tet10 meshes, DISTRIBUTING coupling with force+moment, MASS + GRAV,
SPRING2, EQUATION.  Two blocks 10x10x10 (A z 0-10, B z 10-20), A bottom fixed; B top: distributing coupling (ref node)."""
import sys, numpy as np, gmsh
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ccxrun import run_ccx
wd = Path(sys.argv[1]); wd.mkdir(parents=True, exist_ok=True)
PERM = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]
def block(z0, h):
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.occ.addBox(0, 0, z0, 10, 10, 10); gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", h); gmsh.option.setNumber("Mesh.MeshSizeMin", h)
    gmsh.option.setNumber("Mesh.ElementOrder", 2); gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
    gmsh.model.mesh.generate(3)
    tags, X, _ = gmsh.model.mesh.getNodes(); X = X.reshape(-1, 3)
    et, etg, en = gmsh.model.mesh.getElements(3)
    c = np.array([e for t, e in zip(et, en) if t == 11][0]).reshape(-1, 10)
    gmsh.finalize()
    idx = {int(t): i for i, t in enumerate(tags)}
    return X, np.vectorize(idx.get)(c)[:, PERM]
XA, CA = block(0, 2.0); XB, CB = block(10, 1.4)
nA = len(XA); X = np.vstack([XA, XB]); C = np.vstack([CA, CB + nA]) + 1
FACES = {1: (0, 1, 2), 2: (0, 3, 1), 3: (1, 3, 2), 4: (2, 3, 0)}
def faces(conn, e0, pred):
    from collections import defaultdict
    d = defaultdict(list)
    for e, c in enumerate(conn):
        for f, (a, b, cc) in FACES.items():
            d[tuple(sorted((c[a], c[b], c[cc])))].append((e0 + e + 1, f))
    return [v[0] for k, v in d.items() if len(v) == 1 and all(pred(n) for n in k)]
z = X[:, 2]
fA_top = faces(C[:len(CA)], 0, lambda n: abs(z[n - 1] - 10) < 1e-6)
fB_bot = faces(C[len(CA):], len(CA), lambda n: abs(z[n - 1] - 10) < 1e-6)
fB_top = faces(C[len(CA):], len(CA), lambda n: abs(z[n - 1] - 20) < 1e-6)
fix = [i + 1 for i in range(nA) if abs(z[i]) < 1e-6]
ref = len(X) + 1; mref = len(X) + 2
with open(wd / "f.inp", "w") as f:
    f.write("*NODE, NSET=NALL\n"); [f.write(f"{i+1},{x[0]},{x[1]},{x[2]}\n") for i, x in enumerate(X)]
    f.write(f"{ref},5,5,25\n{mref},5,5,15\n")
    f.write("*ELEMENT,TYPE=C3D10,ELSET=EA\n"); [f.write(f"{e+1}," + ",".join(map(str, c)) + "\n") for e, c in enumerate(C[:len(CA)])]
    f.write("*ELEMENT,TYPE=C3D10,ELSET=EB\n"); [f.write(f"{len(CA)+e+1}," + ",".join(map(str, c)) + "\n") for e, c in enumerate(C[len(CA):])]
    f.write(f"*ELEMENT,TYPE=MASS,ELSET=EM\n{len(C)+1},{mref}\n*MASS,ELSET=EM\n1.0E-3\n")
    f.write("*NSET,NSET=NFIX\n"); [f.write(f"{n}\n") for n in fix]
    f.write("*SURFACE,NAME=SA_TOP,TYPE=ELEMENT\n"); [f.write(f"{e},S{fa}\n") for e, fa in fA_top]
    f.write("*SURFACE,NAME=SB_BOT,TYPE=ELEMENT\n"); [f.write(f"{e},S{fa}\n") for e, fa in fB_bot]
    f.write("*SURFACE,NAME=SB_TOP,TYPE=ELEMENT\n"); [f.write(f"{e},S{fa}\n") for e, fa in fB_top]
    f.write("*MATERIAL,NAME=AL\n*ELASTIC\n70000,0.3\n*DENSITY\n2.7E-9\n*SOLID SECTION,ELSET=EA,MATERIAL=AL\n*SOLID SECTION,ELSET=EB,MATERIAL=AL\n")
    f.write("*TIE,NAME=T1,POSITION TOLERANCE=0.1,ADJUST=NO\nSB_BOT,SA_TOP\n")
    f.write(f"*COUPLING,REF NODE={ref},SURFACE=SB_TOP,CONSTRAINT NAME=C1\n*DISTRIBUTING\n1,6\n")
    f.write("*BOUNDARY\nNFIX,1,3\n")
    # mass node tied to B mid-height via a distributing coupling on B's lateral face x=10? simpler: spring2 to a B node
    nb = [i + 1 for i in range(nA, len(X)) if abs(X[i, 0] - 10) < 1e-6 and abs(X[i, 2] - 15) < 0.8][0]
    f.write(f"*ELEMENT,TYPE=SPRING2,ELSET=ES\n{len(C)+2},{mref},{nb}\n*SPRING,ELSET=ES\n1,1\n1.0E6\n")
    f.write(f"*ELEMENT,TYPE=SPRING2,ELSET=ES2\n{len(C)+3},{mref},{nb}\n*SPRING,ELSET=ES2\n2,2\n1.0E6\n")
    f.write(f"*ELEMENT,TYPE=SPRING2,ELSET=ES3\n{len(C)+4},{mref},{nb}\n*SPRING,ELSET=ES3\n3,3\n1.0E6\n")
    f.write(f"*STEP\n*STATIC\n*CLOAD\n{ref},1,100.\n{ref},4,1000.\n*NODE PRINT,NSET=NFIX\nRF\n*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n")
    f.write(f"*STEP\n*STATIC\n*CLOAD,OP=NEW\n*DLOAD,OP=NEW\nEA,GRAV,9810.,0.,0.,-1.\nEB,GRAV,9810.,0.,0.,-1.\nEM,GRAV,9810.,0.,0.,-1.\n*NODE PRINT,NSET=NFIX,TOTALS=ONLY\nRF\n*END STEP\n")
print(run_ccx("f", wd, threads=1))
print(open(wd / "f.dat").read())
mA = 1000 * 2.7e-9; print("expected step2 RF_z", (2 * mA + 1e-3) * 9810, "step1 RF_x -100, moment about x 1000 -> RF couple")
