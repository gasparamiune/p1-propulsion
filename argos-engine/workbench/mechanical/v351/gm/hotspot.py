"""Collar GM-01 LC3 hot spot at betam7: stress tensor and principal directions at the peak and nearby nodes (diagnostic, v3.5.1)."""
import sys, json, math
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/engine/04-fea/structural")
sys.path.insert(0, "/home/claude/work/mechanical/engine/04-fea/src")
import gimbal_strength as gs
pose = sys.argv[1] if len(sys.argv) > 1 else "betam7"
z = np.load(f"/home/claude/work/mechanical/runs/structural/s3d/{pose}/unit.npz", allow_pickle=True)
S_u = z["S"].astype(np.float64); XYZ = z["XYZ"]
sets = {k: np.array(v) for k, v in json.loads(str(z["sets"])).items()}
E = {k: np.array(v) for k, v in json.loads(str(z["E"])).items()}
meta = json.loads(str(z["meta"])); sm = meta["stiff_meta"]; ab = (sm["alpha"], sm["beta"])
mp = gs.mass_props()
elem_nodes = {}
for body, arr in E.items():
    for row in arr:
        elem_nodes[int(row[0])] = row[1:]
nodes = np.unique(np.concatenate([elem_nodes[int(e)] for e in sets["P_GM01_0"]]))
best = None
for phi in np.arange(0, 360, 15.0):
    for rel in (0.0, 90.0, 180.0, 270.0):
        M, F = gs.case_loads("LC3", ab, mp, -88.8, phi, rel)
        c = gs.unit_vectors((M, F))
        S = np.tensordot(c, S_u[:, nodes, :], axes=(0, 0))
        vm = gs.vm6(S)
        j = int(np.argmax(vm))
        if best is None or vm[j] > best[0]:
            best = (float(vm[j]), phi, rel, nodes[j], c)
vmax, phi, rel, nmax, c = best
print("pose", pose, "ab", ab, "LC3 worst vm", round(vmax, 1), "phi", phi, "rel", rel, "node", nmax, XYZ[nmax].round(2))
S = np.tensordot(c, S_u[:, nodes, :], axes=(0, 0)); vm = gs.vm6(S)
d = np.linalg.norm(XYZ[nodes] - XYZ[nmax], axis=1)
order = np.argsort(-vm)
print("top nodes (vm, xyz, r, az, dist from peak)")
for k in order[:15]:
    x, y, zz = XYZ[nodes[k]]
    print(f"  {vm[k]:7.1f} {XYZ[nodes[k]].round(2)} r {math.hypot(x,y):6.2f} az {math.degrees(math.atan2(y,x)):7.2f} d {d[k]:5.2f}")
# principal stresses at the peak: S order (xx, yy, zz, xy, xz, yz) assumed CalculiX
s = S[np.where(nodes == nmax)[0][0]]
T = np.array([[s[0], s[3], s[4]], [s[3], s[1], s[5]], [s[4], s[5], s[2]]])
w, V = np.linalg.eigh(T)
print("principal", w.round(1)); print("dirs", V.T.round(3))
for rr in (0.75, 1.5, 3.0, 5.0):
    m = (d > rr - 0.4) & (d < rr + 0.4)
    print(f"ring {rr} mm: max vm {vm[m].max():.1f} mean {vm[m].mean():.1f}")
