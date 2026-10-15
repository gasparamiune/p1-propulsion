"""Probe (GNC rev3, 2026-10-13): where the recorded ECU command equals the V3 profile value outside the hold block
(m2_bitcheck_v212 v1.0 functional FAIL). SIM only; diagnostic, not a deliverable."""
import os, sys
import numpy as np
TREE = "/home/claude/work/space/gnc_dev6"
sys.path.insert(0, TREE); sys.path.insert(0, os.path.join(TREE, "scripts"))
import m2_bitcheck_v211 as B11
from gncsim import sim6 as s6
ci = {k: i for i, k in enumerate(s6.REC_NAMES)}
ri = {k: i for i, k in enumerate(s6.RES_NAMES)}
for H, Fp in ((0.30, 200.0), (0.19, 500.0)):
    r, recs = B11.fly_case("A1_none", "nrLO", "none", "", dict(pv2_on=1, pv2_rh=H, pv2_rhF=Fp), 6, 6)
    for j, rc in enumerate(recs[:3]):
        on = np.abs(rc[:, ci["Fcmd"]] - Fp) < 1e-9
        idx = np.where(on)[0]
        br = np.where(np.diff(idx) > 1)[0]
        blocks = np.split(idx, br + 1)
        print(f"H {H} F {Fp} run {j}: t_relight {r[j, ri['t_relight']]:.3f} rel_t {r[j, ri['rel_t']]:.3f} blocks:")
        for b in blocks[:6]:
            k0, k1 = b[0], b[-1]
            print(f"   t {rc[k0, ci['t']]:.3f}..{rc[k1, ci['t']]:.3f} n {len(b)} phase {rc[k0, ci['phase']]:.0f}..{rc[k1, ci['phase']]:.0f} "
                  f"Fceil {rc[k0, ci['Fceil']]:.1f} F {rc[k0, ci['F']]:.1f} z {rc[k0, ci['z']]:.1f} dgx {rc[k0, ci['dgx']]:.2f}")
        if len(blocks) > 1:
            print("   n_blocks", len(blocks))
        k = blocks[0][0]
        print("   around block start:", [(round(float(rc[i, ci['t']]), 2), round(float(rc[i, ci['Fcmd']]), 1)) for i in range(max(0, k - 3), k + 2)])
        k = blocks[0][-1]
        print("   around block end:", [(round(float(rc[i, ci['t']]), 2), round(float(rc[i, ci['Fcmd']]), 1)) for i in range(k - 1, min(len(rc), k + 4))])
