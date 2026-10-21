"""REV-MECH-2 (independent reviewer) helper, own code; reads FEA3D stored decks/fields read-only via rm2_repost / rm2_modal.
Origin: scratchpad helper reentrant_hist.py, copied unchanged below this docstring for the review record (2026-10-20).
"""
import sys, json
import numpy as np
sys.path.insert(0, "/home/claude/work/shared-fallback/engine/reviews/mechanical/r2/scripts")
import rm2_repost as RP
z, meta = RP.load_deck("fa1_c71", "A1_22.2")
mesh = RP.Mesh(z, meta)
tot = np.zeros(6, int)
edges_bins = [30, 40, 50, 60, 80, 120, 181]
print("re-entrant (concave, > 30 deg) edges per body by facet turn angle bins", edges_bins)
for nm in mesh.names:
    nodes, ne, turn = mesh.reentrant_nodes(nm)
    h, _ = np.histogram(turn, bins=edges_bins)
    tot += h
    if ne:
        print(f"  {nm:7s} edges {ne:5d} nodes {len(nodes):5d} | " + " ".join(f"{a}-{b}:{c}" for a, b, c in zip(edges_bins[:-1], edges_bins[1:], h)))
print("  total", tot.tolist(), "share 30-40 deg %.2f" % (tot[0] / tot.sum()), "share 30-50 %.2f" % (tot[:2].sum() / tot.sum()))
