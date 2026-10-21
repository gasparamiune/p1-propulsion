"""REV-MECH-2 (independent reviewer) helper, own code; reads FEA3D stored decks/fields read-only via rm2_repost / rm2_modal.
Origin: scratchpad helper op_faces.py, copied unchanged below this docstring for the review record (2026-10-20).
"""
import sys, json, math
import numpy as np
sys.path.insert(0, "/home/claude/work/shared-fallback/engine/reviews/mechanical/r2/scripts")
import rm2_repost as RP
import rm2_modal as MM
out = {}
for run, state in (("fa1_c71", "A1_22.2"), ("modal_v351ca2b_c71", "B1_21.65")):
    z, meta = RP.load_deck(run, state)
    X = np.zeros((int(z["nodes_id"].max()) + 2, 3)); X[z["nodes_id"]] = z["nodes_x"]
    elem, ebody = {}, {}
    for es in meta["bodies"]:
        for row in z[f"E_{es}"]:
            elem[int(row[0])] = row[1:]; ebody[int(row[0])] = es
    i = [s["i"] for s in meta["steps"] if s["name"] == "OP"][0]
    DL = z[f"DL_{i}"]
    rows = []
    for eid, face, p in DL:
        conn = elem[int(eid)]; fl = RP.FACES[int(face) - 1]; nodes = conn[list(fl)]; P = X[nodes]
        ce, cf = X[conn[:4]].mean(0), P[:3].mean(0)
        nA = np.zeros(3)
        for s_, t_, w in MM.GP:
            N, dNs, dNt = MM.tri6_N(s_, t_)
            n = np.cross(dNs @ P, dNt @ P)
            if n @ (cf - ce) < 0: n = -n
            nA += n * w
        A = np.linalg.norm(nA)
        rows.append((ebody[int(eid)], p, A, nA[2], math.hypot(cf[0], cf[1]), cf[2]))
    out[run] = rows
    print("==", run)
    for b in sorted(set(r[0] for r in rows)):
        R = [r for r in rows if r[0] == b]
        A = sum(r[2] for r in R); Az = sum(r[3] for r in R); Fz = -sum(r[1] * r[3] for r in R)
        pm = sum(r[1] * r[2] for r in R) / A
        zs = [r[5] for r in R]; rs = [r[4] for r in R]
        print(f"  {b:8s} faces {len(R):5d} area {A:9.1f} mm2  sum nz dA {Az:9.2f}  Fz {Fz:9.2f} N/MPa  mean p {pm:.4f}  z [{min(zs):.1f},{max(zs):.1f}] r [{min(rs):.2f},{max(rs):.2f}]")
# NZ-03 detail: z/r histograms
for run in out:
    R = [r for r in out[run] if r[0] == "B_NZ03"]
    zs = np.array([r[5] for r in R]); rs = np.array([r[4] for r in R]); fz = np.array([-r[1] * r[3] for r in R])
    print(run, "NZ-03 faces by z band (Fz):")
    for lo in np.arange(np.floor(zs.min()), zs.max() + 1, 2.0):
        m = (zs >= lo) & (zs < lo + 2)
        if m.any():
            print(f"   z [{lo:.0f},{lo+2:.0f}) n {m.sum():4d} r [{rs[m].min():.2f},{rs[m].max():.2f}] Fz {fz[m].sum():8.2f}")
