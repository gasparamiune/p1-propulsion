"""GVCC pass-0 finding (lead 2026-10-20 04:05Z: GVCC withdrawn; keep the pass-0 result as a recorded finding).
Free-ring J1 closure computed on the GVLO B1 field (v352_NF2b_GVLO frd) at the MAXIMUM designed clearance c0 = 0.078 mm radial
(57.25 H8 upper bore with 57.20 f7 lower shaft): gap g(t) = c0 + dgap(t), dgap = (eps_TC01 - eps_TC02) * r_m per land (area x r weighted
secant strain of each part within +/-1 mm of the land).  Evidence: DERIVED (free-ring rule on a SIM field); one-way (the field is GVLO's,
J1 open at 0.090 mm); no coupled iteration was completed."""
import json, hashlib
from pathlib import Path
import numpy as np
WD = Path(__file__).resolve().parent
s = json.loads((WD / "gvcc_state.json").read_text())
p = s["passes"][0]
H = p["history"]
t = np.array(H["t"])
out = {"what": "GVCC pass-0 J1 closure finding (GVCC withdrawn by lead 04:05Z, stopped 03:48Z in pass 1; no coupled result)",
       "basis": {"c0_mm": 0.078, "fit": "bore 57.25 H8 upper (57.296) / plug 57.20 f7 lower (57.140)", "r_m_mm": 28.6125,
                 "field": "v352_NF2b_GVLO (J1 0.090 / J2 0.110 / J3 0.240 mm gas + radiation, kmul 1.0)", "field_dir": p["dir"],
                 "rule": "free ring: dgap = (eps_TC01 - eps_TC02) * r_m, area x r weighted mean secant strain within +/-1 mm of each land",
                 "lands_thermal_z_mm": {"L1": [110.0575, 113.0575], "L2": [117.9075, 120.9075], "L3": [125.7575, 143.5575]},
                 "evidence": "DERIVED (one-way, on a SIM field)"},
       "GVLO_TC02_max_C": p["TC02_max_C"], "GVLO_TC02_t_s": p["TC02_t_s"], "lands": {}}
burn = t <= 21.651 + 1e-6
for L in ("L1", "L2", "L3"):
    g = np.array(H[L])
    i = int(np.argmin(g))
    ib = int(np.argmin(np.abs(t - 21.651)))
    out["lands"][L] = {"gap_min_mm": round(float(g.min()), 4), "t_gap_min_s": round(float(t[i]), 3),
                       "gap_end_of_burn_mm": round(float(g[ib]), 4), "gap_burn_min_mm": round(float(g[burn].min()), 4),
                       "gap_soak_max_mm": round(float(g[~burn].max()), 4) if (~burn).any() else None,
                       "gap_end_mm": round(float(g[-1]), 4), "t_end_s": round(float(t[-1]), 3),
                       "closed_ever": bool((g <= 0).any())}
out["finding"] = ("At the maximum designed clearance J1 never closes in the B1 burn or soak on the GVLO field: minimum radial gaps L1 %.4f / "
                  "L2 %.4f / L3 %.4f mm (GVLO assumed 0.090 mm).  Option (a) withdrawn: no J1 drawing note; the J1 fit stays as designed."
                  % tuple(out["lands"][L]["gap_min_mm"] for L in ("L1", "L2", "L3")))
dst = WD / "gvcc_pass0_finding_v352_v1.json"
dst.write_text(json.dumps(out, indent=1))
print(json.dumps(out["lands"], indent=1)); print(out["finding"])
print("sha16", hashlib.sha256(dst.read_bytes()).hexdigest()[:16], "state sha16", hashlib.sha256((WD / "gvcc_state.json").read_bytes()).hexdigest()[:16])
