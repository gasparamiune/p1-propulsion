"""7.1 connector test: two hex blocks joined ONLY by a bushing (SPRINGA A->aux, aux tied by *EQUATION to B), A, B = *RIGID BODY refs.
Variant 'eqref': as in the assembly model.  Variant 'spring2': SPRING2 directly between A and B (coincident), no aux / equations.
Applied load on block E must pass 100 % through the springs (no other path)."""
import sys, numpy as np
var = sys.argv[1]
nodes, elems = {}, []
def block(y0, nid0, eid0):
    xs = [-5, 0, 5]; ys = [y0, y0 + 5, y0 + 10]; zs = [-5, 0, 5]
    idx = {}
    n = nid0
    for k, z in enumerate(zs):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                nodes[n] = (x, y, z); idx[(i, j, k)] = n; n += 1
    e = eid0
    for k in range(2):
        for j in range(2):
            for i in range(2):
                c = [idx[(i, j, k)], idx[(i + 1, j, k)], idx[(i + 1, j + 1, k)], idx[(i, j + 1, k)],
                     idx[(i, j, k + 1)], idx[(i + 1, j, k + 1)], idx[(i + 1, j + 1, k + 1)], idx[(i, j + 1, k + 1)]]
                elems.append((e, c)); e += 1
    return idx
iE = block(1.0, 1, 1)       # engine block y 1..11
iR = block(-11.0, 101, 101) # ring block y -11..-1
pinset = [iE[(i, 0, k)] for i in range(3) for k in range(3)]
seatset = [iR[(i, 2, k)] for i in range(3) for k in range(3)]
fixset = [iR[(i, 0, k)] for i in range(3) for k in range(3)]
loadset = [iE[(i, 2, k)] for i in range(3) for k in range(3)]
A, Arot, B, Brot = 201, 202, 203, 204
nodes[A] = (0, 0, 0); nodes[Arot] = (0, 0, 0); nodes[B] = (0, 0, 0); nodes[Brot] = (0, 0, 0)
L = []
L.append("*NODE")
aux = {}
if var == "eqref":
    for d, n in ((1, 211), (2, 212), (3, 213)):
        v = [0, 0, 0]; v[d - 1] = 1.0
        nodes[n] = tuple(v); aux[d] = n
for n, x in sorted(nodes.items()):
    L.append(f"{n}, {x[0]}, {x[1]}, {x[2]}")
L.append("*ELEMENT, TYPE=C3D8, ELSET=EALL")
for e, c in elems:
    L.append(f"{e}, " + ", ".join(map(str, c)))
L.append("*NSET, NSET=PIN\n" + ", ".join(map(str, pinset)))
L.append("*NSET, NSET=SEAT\n" + ", ".join(map(str, seatset)))
L.append("*NSET, NSET=FIX\n" + ", ".join(map(str, fixset)))
L.append("*NSET, NSET=LOADS\n" + ", ".join(map(str, loadset)))
L.append(f"*NSET, NSET=CONN\n{A}, {B}" + ("".join(f", {n}" for n in aux.values())))
L.append("*MATERIAL, NAME=AL\n*ELASTIC\n70000., 0.33\n*DENSITY\n2.7e-9")
L.append("*SOLID SECTION, ELSET=EALL, MATERIAL=AL")
L.append(f"*RIGID BODY, NSET=PIN, REF NODE={A}, ROT NODE={Arot}")
L.append(f"*RIGID BODY, NSET=SEAT, REF NODE={B}, ROT NODE={Brot}")
k = 1.0e5
if var == "eqref":
    for d, n in aux.items():
        for dd in (1, 2, 3):
            L.append(f"*EQUATION\n2\n{n}, {dd}, 1.0, {B}, {dd}, -1.0")
    L.append("*ELEMENT, TYPE=SPRINGA, ELSET=SPR")
    for d, n in aux.items():
        L.append(f"{300 + d}, {A}, {n}")
    L.append(f"*SPRING, ELSET=SPR\n\n{k}")
else:
    for d in (1, 2, 3):
        L.append(f"*ELEMENT, TYPE=SPRING2, ELSET=SP{d}\n{300 + d}, {A}, {B}")
        L.append(f"*SPRING, ELSET=SP{d}\n{d}, {d}\n{k}")
L.append("*BOUNDARY\nFIX, 1, 3")
for st, (d, F) in enumerate(((1, 10.0), (3, 10.0), (2, 10.0)), 1):
    L.append("*STEP\n*STATIC")
    L.append("*CLOAD")
    for n in loadset:
        L.append(f"{n}, {d}, {F / len(loadset)}")
    L.append("*NODE PRINT, NSET=FIX, TOTALS=ONLY\nRF")
    L.append("*NODE PRINT, NSET=CONN\nU")
    L.append("*EL PRINT, ELSET=" + ("SPR" if var == "eqref" else "SP1") + "\nS")
    L.append("*END STEP")
open(f"t_{var}.inp", "w").write("\n".join(L) + "\n")
print("wrote", f"t_{var}.inp", "aux", aux)
