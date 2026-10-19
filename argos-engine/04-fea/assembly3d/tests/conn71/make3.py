"""7.1 connector test v2 (statically determinate gimbal analogue): block E (y 1..11) held by two pin bushings to two grounded blocks
R1 (y -11..-1) and R2 (y 13..23) + one axial rod spring (blocks rotation about the pin axis Y).  Pins/seats are *RIGID BODY sets.
Bushing radial X,Z at both pins, axial Y at pin 1 only (like the assembly).  Variant eqref: SPRINGA A->aux, aux tied to B by *EQUATION.
Variant spring2: SPRING2 directly between coincident A and B.  Loads OP=NEW per step.  Expect sum of spring forces on E = applied."""
import sys
var = sys.argv[1]
WSH = var.endswith("_wsh")
var0 = var.replace("_wsh", "")
nodes, elems = {}, []
def block(y0, nid0, eid0):
    xs = [-5, 0, 5]; ys = [y0, y0 + 5, y0 + 10]; zs = [-5, 0, 5]
    idx = {}; n = nid0
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
iE = block(1.0, 1, 1); iR1 = block(-11.0, 101, 101); iR2 = block(13.0, 301, 301)
face = lambda ix, j: [ix[(i, j, k)] for i in range(3) for k in range(3)]
sets = {"PIN1": face(iE, 0), "PIN2": face(iE, 2), "SEAT1": face(iR1, 2), "SEAT2": face(iR2, 0),
        "FIX": face(iR1, 0) + face(iR2, 2)}
loadset = [iE[(i, 1, k)] for i in range(3) for k in range(3)]
refs = {"PIN1": (501, 502, (0, 0, 0)), "SEAT1": (503, 504, (0, 0, 0)), "PIN2": (505, 506, (0, 12, 0)), "SEAT2": (507, 508, (0, 12, 0))}
for r, (n, nr, x) in refs.items():
    nodes[n] = x; nodes[nr] = x
rodE, rodG = iE[(2, 1, 2)], 601             # rod: E corner (5, 6, 5) -> grounded node (5, 6, 25) along Z
nodes[rodG] = (5, 6, 25)
L = []
bush = [("B1", 501, 503, [(1, (1, 0, 0)), (3, (0, 0, 1))] + ([] if WSH else [(2, (0, 1, 0))])), ("B2", 505, 507, [(1, (1, 0, 0)), (3, (0, 0, 1))])]
if WSH:
    nodes[511] = (0, 0, 0); nodes[513] = (0, 0, 0)         # washer refs (RBE3-like averages of 4 PIN1 / 4 SEAT1 nodes)
    bush.append(("W1", 511, 513, [(2, (0, 1, 0))]))
aux = []
nid = 700
spr = []
if var0 == "eqref":
    for lab, A, B, dirs in bush:
        for d, v in dirs:
            nodes[nid] = tuple(nodes[A][q] + v[q] for q in range(3)); aux.append((nid, B)); spr.append((lab, d, A, nid)); nid += 1
L.append("*NODE")
for n, x in sorted(nodes.items()):
    L.append(f"{n}, {x[0]}, {x[1]}, {x[2]}")
L.append("*ELEMENT, TYPE=C3D8, ELSET=EALL")
for e, c in elems:
    L.append(f"{e}, " + ", ".join(map(str, c)))
for s, v in sets.items():
    L.append(f"*NSET, NSET={s}\n" + "\n".join(", ".join(map(str, v[i:i + 8])) for i in range(0, len(v), 8)))
L.append("*NSET, NSET=LOADS\n" + ", ".join(map(str, loadset)))
cn = [r[0] for r in refs.values()] + [a for a, _ in aux] + [rodE] + ([511, 513] if WSH else [])
L.append("*NSET, NSET=CONN\n" + "\n".join(", ".join(map(str, cn[i:i + 8])) for i in range(0, len(cn), 8)))
L.append("*NSET, NSET=GRODS\n601")
L.append("*MATERIAL, NAME=AL\n*ELASTIC\n70000., 0.33")
L.append("*SOLID SECTION, ELSET=EALL, MATERIAL=AL")
for r, (n, nr, x) in refs.items():
    L.append(f"*RIGID BODY, NSET={r}, REF NODE={n}, ROT NODE={nr}")
k = 1.0e5
if WSH:
    pw = [iE[(0, 0, 0)], iE[(2, 0, 0)], iE[(0, 0, 2)], iE[(2, 0, 2)]]
    sw = [iR1[(0, 2, 0)], iR1[(2, 2, 0)], iR1[(0, 2, 2)], iR1[(2, 2, 2)]]
    for ref, pts in ((511, pw), (513, sw)):
        for dd in (1, 2, 3):
            L.append("*EQUATION\n5\n" + f"{ref}, {dd}, 1.0, " + ", ".join(f"{q}, {dd}, -0.25" for q in pts))
if var0 == "eqref":
    for a, B in aux:
        for dd in (1, 2, 3):
            L.append(f"*EQUATION\n2\n{a}, {dd}, 1.0, {B}, {dd}, -1.0")
    L.append("*ELEMENT, TYPE=SPRINGA, ELSET=SPR")
    for i, (lab, d, A, a) in enumerate(spr):
        L.append(f"{800 + i}, {A}, {a}")
    L.append(f"*SPRING, ELSET=SPR\n\n{k}")
else:
    i = 0
    for lab, A, B, dirs in bush:
        for d, v in dirs:
            L.append(f"*ELEMENT, TYPE=SPRING2, ELSET=SQ{i}\n{800 + i}, {A}, {B}")
            L.append(f"*SPRING, ELSET=SQ{i}\n{d}, {d}\n{k}")
            i += 1
L.append(f"*ELEMENT, TYPE=SPRINGA, ELSET=ROD\n900, {rodE}, {rodG}\n*SPRING, ELSET=ROD\n\n{k}")
L.append("*BOUNDARY\nFIX, 1, 3\n601, 1, 3")
for d in (1, 2, 3):
    L.append("*STEP\n*STATIC\n*CLOAD, OP=NEW")
    for n in loadset:
        L.append(f"{n}, {d}, {10.0 / len(loadset)}")
    L.append("*NODE PRINT, NSET=FIX, TOTALS=ONLY\nRF")
    L.append("*NODE PRINT, NSET=GRODS, TOTALS=ONLY\nRF")
    L.append("*NODE PRINT, NSET=CONN\nU")
    L.append("*END STEP")
open(f"u_{var}.inp", "w").write("\n".join(L) + "\n")
import json; json.dump({"spr": spr, "k": k, "bush": bush, "rodE": rodE, "rodG": rodG}, open(f"u_{var}.json", "w"))
print("ok", var)
