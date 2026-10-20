"""REV-MECH-2 (independent reviewer) helper, own code; reads FEA3D stored decks/fields read-only via rm2_repost / rm2_modal.
Origin: scratchpad helper jfwd_probe.py, copied unchanged below this docstring for the review record (2026-10-20).
"""
import sys, json, math
from pathlib import Path
import numpy as np
sys.path.insert(0, "/home/claude/work/shared-fallback/engine/reviews/mechanical/r2/scripts")
import rm2_repost as RP
from scipy.spatial import cKDTree
run, state = "fa1_c71", "A1_22.2"
z, meta = RP.load_deck(run, state)
mesh = RP.Mesh(z, meta)
model = json.loads((RP.RUNS / run / "model.json").read_text())
F = dict(np.load(RP.RUNS / run / state / "fields.npz"))
S_, rep = RP.singular_sets(mesh, model, z)
reg, dist, cls = RP.regular_mask(mesh, S_)
T = np.full(len(mesh.X), 293.15)
Tt = z["T_0"]; T[Tt[:, 0].astype(int)] = Tt[:, 1]
S, Sm = RP.combine(F, "S", {"OP": 15.1038, "PM": 7.0})
v = RP.vm(S)
print("rbe labels:", [k for k in model["rbe"]][:40])
rb_tree = {k: cKDTree(mesh.X[[x for x in d["nodes"] if x <= mesh.n_mesh]]) for k, d in model["rbe"].items() if any(x <= mesh.n_mesh for x in d["nodes"])}
for nd in (25946, 580, 8314, 27955, 41165):
    x = mesh.X[nd]
    dd = {k: float(t.query(x)[0]) for k, t in rb_tree.items()}
    k0 = min(dd, key=dd.get)
    print(nd, "r th z", round(math.hypot(x[0], x[1]), 3), round(math.degrees(math.atan2(x[1], x[0])), 2), round(x[2], 3),
          "body", mesh.names[mesh.node_body[nd]], "vm", round(float(v[nd]), 1), "T", round(T[nd] - 273.15, 1),
          "nearest rbe", k0, round(dd[k0], 3), "in sets:", [k for k, s in S_.items() if nd in set(s.tolist())], "reg", bool(reg[nd]))
# profile of MS vs distance from the hole edge for J-FWD holes, per body (TC-01, TC-02)
holes = [math.radians(22.5 + 45 * k) for k in range(8)]
zc = 127.51
for nm, a in (("TC-01", 2.75), ("TC-02", 2.1)):
    nodes = mesh.bodies[nm]["nodes"]
    X = mesh.X[nodes]
    best = []
    for th in holes:
        ax = np.array([math.cos(th), math.sin(th), 0.0])
        rel = X - np.array([0, 0, zc])
        along = rel @ ax
        perp = rel - np.outer(along, ax)
        rho = np.linalg.norm(perp, axis=1)
        near = (np.abs(rho - a) < 6) & (along > 15)
        best.append((near, rho, along))
    Fy = RP.allow(mesh.bodies[nm]["mat"], "Fty", T[nodes])
    ms = Fy / v[nodes] - 1
    # distance from hole edge = rho - a (in-plane), use min over holes
    rho_all = np.full(len(nodes), np.inf); 
    for near, rho, along in best:
        rho_all = np.where(near & (rho < rho_all), rho, rho_all)
    e = rho_all - a
    print(nm, "J-FWD hole-edge profile (FA1S, MS_y = Fty/vM - 1, min over 8 holes):")
    for lo, hi in ((-0.3, 0.05), (0.05, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 6.0)):
        m = (e >= lo) & (e < hi)
        if m.any():
            i = np.argmin(np.where(m, ms, np.inf))
            nd = int(nodes[i])
            print(f"   edge dist [{lo:4.2f},{hi:4.2f}) mm: n {int(m.sum()):5d} minMS {ms[i]:+.3f} vm {v[nd]:.1f} node {nd} reg {bool(reg[nd])} class {cls[nd]} d {dist[nd]:.3f}")
