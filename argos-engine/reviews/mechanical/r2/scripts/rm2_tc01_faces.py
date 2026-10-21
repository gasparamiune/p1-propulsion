"""REV-MECH-2 (independent reviewer) helper, own code; reads FEA3D stored decks/fields read-only via rm2_repost / rm2_modal.
Origin: scratchpad helper tc01_faces.py, copied unchanged below this docstring for the review record (2026-10-20).
"""
import sys, json, math
import numpy as np
sys.path.insert(0, "/home/claude/work/shared-fallback/engine/reviews/mechanical/r2/scripts")
import rm2_repost as RP
import rm2_modal as MM
res = {}
for run, state in (("fa1_c71", "A1_22.2"), ("pose_alpha-_c71", "B1_21.65"), ("modal_v351ca2b_c71", "B1_21.65")):
    z, meta = RP.load_deck(run, state)
    X = np.zeros((int(z["nodes_id"].max()) + 2, 3)); X[z["nodes_id"]] = z["nodes_x"]
    m = json.loads((RP.RUNS / run / "model.json").read_text())
    Rg = np.asarray(m["Rg"]["engine"]) if "engine" in m.get("Rg", {}) else np.eye(3)
    elem, ebody = {}, {}
    for es in meta["bodies"]:
        for row in z[f"E_{es}"]:
            elem[int(row[0])] = row[1:]; ebody[int(row[0])] = es
    i = [s["i"] for s in meta["steps"] if s["name"] == "OP"][0]
    rows = []
    for eid, face, p in z[f"DL_{i}"]:
        if ebody[int(eid)] != "B_TC01": continue
        conn = elem[int(eid)]; fl = RP.FACES[int(face) - 1]; nodes = conn[list(fl)]; P = X[nodes] @ Rg   # engine frame
        ce, cf = (X[conn[:4]] @ Rg).mean(0), P[:3].mean(0)
        fs = np.zeros(3); A = 0
        for s_, t_, w in MM.GP:
            N, dNs, dNt = MM.tri6_N(s_, t_)
            n = np.cross(dNs @ P, dNt @ P)
            if n @ (cf - ce) < 0: n = -n
            fs += -p * n * w; A += np.linalg.norm(n) * w
        nz = -fs[2] / p / A if p else 0
        rows.append((cf[2], math.hypot(cf[0], cf[1]), fs[2], A, nz, p))
    res[run] = np.array(rows)
bins = [-160, -150, -140, -100, 0, 50, 100, 105, 108, 110, 112, 114]
print("TC-01 OP DLOAD Fz (N/MPa) and area (mm2) by z band, engine frame; faces with |n_z| > 0.3 counted separately")
for lo, hi in zip(bins[:-1], bins[1:]):
    line = f"z [{lo:5d},{hi:5d})"
    for run, R in res.items():
        m = (R[:, 0] >= lo) & (R[:, 0] < hi)
        ax = m & (np.abs(R[:, 4]) > 0.3)
        line += f" | {run[:10]}: Fz {R[m, 2].sum():8.2f} A {R[m, 3].sum():8.1f} axialfaces {ax.sum():3d} Fz_ax {R[ax, 2].sum():8.2f} r[{(R[ax,1].min() if ax.any() else 0):.2f},{(R[ax,1].max() if ax.any() else 0):.2f}]"
    print(line)
