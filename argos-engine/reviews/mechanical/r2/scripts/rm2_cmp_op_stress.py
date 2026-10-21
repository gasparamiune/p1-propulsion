"""REV-MECH-2 (independent reviewer) helper, own code; reads FEA3D stored decks/fields read-only via rm2_repost / rm2_modal.
Origin: scratchpad helper cmp_op_stress.py, copied unchanged below this docstring for the review record (2026-10-20).
"""
import sys, json, math
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/claude/work/shared-fallback/engine/reviews/mechanical/r2/scripts")
import rm2_repost as RP
zm, mm = RP.load_deck("modal_v351ca2b_c71", "B1_21.65")
Xm = np.zeros((int(zm["nodes_id"].max()) + 2, 3)); Xm[zm["nodes_id"]] = zm["nodes_x"]
Fm = np.load(RP.RUNS / "modal_v351ca2b_c71/B1_21.65/fields.npz")
run = "pose_neutral_c71"
zp, mp = RP.load_deck(run, "B1_21.65")
Xp = np.zeros((int(zp["nodes_id"].max()) + 2, 3)); Xp[zp["nodes_id"]] = zp["nodes_x"]
Fp = np.load(RP.RUNS / run / "B1_21.65/fields.npz")
print([k for k in Fp.files][:40])
Sm = Fm["S_OP"].astype(float)
Sp = Fp["S_OP"].astype(float) if "S_OP" in Fp.files else None
Ep = zp["E_B_TC01"][:, 1:]; tc1p = np.unique(Ep)
tree = cKDTree(Xp[tc1p])
def vm(s): return float(RP.vm(s[None])[0])
for nd in (2785, 2800):
    d, j = tree.query(Xm[nd])
    ndp = int(tc1p[j])
    print(f"modal node {nd} {Xm[nd].round(3)} -> pose_neutral node {ndp} dist {d:.4f} mm; vM S_OP modal {vm(Sm[nd]):.3f} pose {vm(Sp[ndp]):.3f}; "
          f"S modal {Sm[nd].round(3)} pose {Sp[ndp].round(3)}")
# overall TC-01 comparison for nodes that coincide
Em = zm["E_B_TC01"][:, 1:]; tc1m = np.unique(Em)
d, j = tree.query(Xm[tc1m])
ok = d < 1e-3
print("TC-01 coincident nodes:", ok.sum(), "of", len(tc1m))
a = RP.vm(Sm[tc1m[ok]]); b = RP.vm(Sp[tc1p[j[ok]]])
zz = Xm[tc1m[ok], 2]
for lo, hi in ((115, 140), (100, 115), (-150, 100), (-160, -150)):
    m = (zz >= lo) & (zz < hi)
    if m.any():
        r = a[m] / np.maximum(b[m], 1e-9)
        print(f"  z [{lo},{hi}): n {m.sum()} vM modal/pose median {np.median(r):.4f} p05 {np.percentile(r,5):.4f} p95 {np.percentile(r,95):.4f}")
