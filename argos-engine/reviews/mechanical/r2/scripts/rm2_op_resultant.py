"""REV-MECH-2 (independent reviewer) helper, own code; reads FEA3D stored decks/fields read-only via rm2_repost / rm2_modal.
Origin: scratchpad helper op_resultant2.py, copied unchanged below this docstring for the review record (2026-10-20).
"""
import sys, json, math
import numpy as np
sys.path.insert(0, "/home/claude/work/shared-fallback/engine/reviews/mechanical/r2/scripts")
import rm2_repost as RP
import rm2_modal as MM
runs = sys.argv[1:]
for rs in runs:
    run, state = rs.split(":")
    z, meta = RP.load_deck(run, state)
    X = np.zeros((int(z["nodes_id"].max()) + 2, 3)); X[z["nodes_id"]] = z["nodes_x"]
    elem, ebody = {}, {}
    for es in meta["bodies"]:
        for row in z[f"E_{es}"]:
            elem[int(row[0])] = row[1:]; ebody[int(row[0])] = es
    i = [s["i"] for s in meta["steps"] if s["name"] == "OP"][0]
    DL = z[f"DL_{i}"]
    byb = {}
    tot = np.zeros(3)
    for eid, face, p in DL:
        conn = elem[int(eid)]; fl = RP.FACES[int(face) - 1]; nodes = conn[list(fl)]; P = X[nodes]
        ce, cf = X[conn[:4]].mean(0), P[:3].mean(0)
        fs = np.zeros(3)
        for s_, t_, w in MM.GP:
            N, dNs, dNt = MM.tri6_N(s_, t_)
            n = np.cross(dNs @ P, dNt @ P)
            if n @ (cf - ce) < 0: n = -n
            fs += -p * n * w
        tot += fs
        byb[ebody[int(eid)]] = byb.get(ebody[int(eid)], 0.0) + fs[2]
    CL = z[f"CL_{i}"]
    cl = np.zeros(3)
    for nd, dof, v in CL:
        cl[int(dof) - 1] += v
    # engine axis: rotate into the engine frame if posed
    m = json.loads((RP.RUNS / run / "model.json").read_text())
    Rg = np.asarray(m["Rg"]["engine"]) if "Rg" in m and "engine" in m["Rg"] else np.eye(3)
    T = tot + cl
    print(f"{run}: |F| {np.linalg.norm(T):.3f} N/MPa, engine-axial {T @ (Rg @ np.array([0, 0, 1.0])):.3f}; dload by body z(global): " +
          ", ".join(f"{k[2:]} {v:.1f}" for k, v in byb.items()))
