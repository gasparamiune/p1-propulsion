"""TC-01 bore mid-bay at the J-FWD screw plane: hand bracket of the preload-only (cold) wall bending and the soak P+Q from FEA3D's js4 values to
every fit gap (the drawing H8 / f7, the CAD 0.025 and the contingency H7 / h6, H7 / g6 of jfwd_fit v1), at 3.0 and 4.0 N m (F_max, no
embedding credit).  Mechanical, 2026-10-20, v1.  A cross-check beside FEA3D's 0.078 seat run (lead 08:10Z), not a closure.  CALC; DERIVED.

Classification (lead 08:10Z: 'At the 0.078 drawing gap the whole preload bends the wall, so the primary may go negative there'): with the fit
open, the wall bending at the screw plane is in equilibrium with the installed screw force (load-controlled: primary); with the fit closed,
the shell pull is limited by the gap, F_sh = k_sh g (displacement-limited).  jfwd_gap v1 classed the whole preload pull as secondary and kept
the primary cells unchanged by the gap: that holds for the pressure-driven cells only (hole bearing, ligament Pm, shear-out), not for the
preload bending of the wall; this file brackets that part.
Scaling (stated, not proven): the mid-bay ring bending is driven by the net inward force on the ring, F_sh = F_S - F_c (ring under 10 radial
point loads); js4 (0.025, mu 0, 3750 N): F_sh 1400 N cold (the gap-closing force), mid-bay preload-only 88.4 MPa (FEA3D, relayed 08:04Z);
sigma_pre(g) = 88.4 x F_sh_cold(g) / F_sh_cold(0.025) (both from the jfwd_embed v1 model: 1480 N at js4, FEA3D
"about 1.4 kN").  Soak: js4 soak mid-bay Pm+Pb 190 MPa (P+Q +0.79) at the js4 soak frame (GVLO 64.651 s,
F_sh 3793 N in the jfwd_embed v1 model); the whole value is scaled by F_sh_soak(g) / 3793 (the thermal ring bending is scaled too: upper
bound).  Allowables engmat 6061-T6 (ASTM minimum x ASM 10 000 h ratio): the preload-only primary against 158 C (the soak temperature at which
the preload persists; FEA3D's basis) and 20 C, SF 1.5 / 2.0; P+Q against 2 Fty(158 C)."""
import json, hashlib, sys
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "tc01_midbay_preload_v352_v1.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
SRC = (J / "jfwd_embed_v352.py").read_text().split("# ---- embedding: residual preload")[0]
NS = {"__file__": str(J / "jfwd_embed_v352.py")}
exec(compile(SRC, str(J / "jfwd_embed_v352.py") + "(head)", "exec"), NS)
state, deltas, ROWS, K_B, K_SH, tab, TH, K_NUT = (NS[k] for k in ("state", "deltas", "ROWS", "K_B", "K_SH", "tab", "TH", "K_NUT"))
JS4_PRE_MPA, JS4_SOAK_PMPB = 88.4, 190.0
t, T01, T02 = ROWS["GVLO"]
i_s = int(np.argmin(np.abs(t - 64.651)))
_, dw_s, dr_s = deltas(float(T01[i_s]), float(T02[i_s]))
FS4, u4, Fc4, _ = (float(x) for x in state(3750.0, 0.025, dw_s, dr_s, 0.0, K_B))
FSH4_SOAK = FS4 - Fc4
FSc4, uc4, Fcc4, _ = (float(x) for x in state(3750.0, 0.025, 0.0, 0.0, 0.0, K_B))
JS4_FSH_COLD = FSc4 - Fcc4          # the model's js4 cold shell pull (FEA3D: 'about 1.4 kN'); normalising here reproduces 88.4 MPa at 0.025
Fty158, Ftu158 = tab("AL6061-T6", "Fty", 158.0), tab("AL6061-T6", "Ftu", 158.0)
Fty20, Ftu20 = tab("AL6061-T6", "Fty", 20.0), tab("AL6061-T6", "Ftu", 20.0)
GAPS = {"H7h6_min": 0.0, "H7h6_mean": 0.01225, "H7h6_max": 0.0245, "H7g6_min": 0.005, "H7g6_mean": 0.01725, "H7g6_max": 0.0295,
        "CAD_0.025_js4": 0.025, "H8f7_min": 0.040, "H8f7_mean": 0.059, "H8f7_max": 0.078}
rows = {}
for tq in (3.0, 4.0):
    Fmax = 1.25 * tq * 1e3 / (K_NUT * TH["d"])
    for gn, g in GAPS.items():
        FSc, uc, Fcc, _ = (float(x) for x in state(Fmax, g, 0.0, 0.0, 0.0, K_B))
        fsh_c = FSc - Fcc
        FSs, us, Fcs, _ = (float(x) for x in state(Fmax, g, dw_s, dr_s, 0.0, K_B))
        fsh_s = FSs - Fcs
        sp = JS4_PRE_MPA * fsh_c / JS4_FSH_COLD
        sq = JS4_SOAK_PMPB * fsh_s / FSH4_SOAK
        rows[f"{gn}|{tq:g}Nm"] = {"gap_mm": g, "F_max_N": round(Fmax), "cold": {"fit": "closed" if Fcc > 0 else "open", "F_sh_N": round(fsh_c),
                                  "sigma_pre_MPa": round(sp, 1), "MS_158C": [round(Fty158 / (1.5 * sp) - 1.0, 3), round(Ftu158 / (2.0 * sp) - 1.0, 3)],
                                  "MS_20C": [round(Fty20 / (1.5 * sp) - 1.0, 3), round(Ftu20 / (2.0 * sp) - 1.0, 3)]},
                                  "soak_GVLO_64.651s": {"fit": "closed" if Fcs > 0 else "open", "F_S_N": round(FSs), "F_sh_N": round(fsh_s),
                                                        "PQ_PmPb_bound_MPa": round(sq, 1), "MS_PQ_vs_2Fty158": round(2.0 * Fty158 / sq - 1.0, 3)}}
out = {"id": "tc01_midbay_preload_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"jfwd_embed_v352.py": sha(J / "jfwd_embed_v352.py"), "js4_midbay_preload_only_MPa": JS4_PRE_MPA, "model_js4_F_sh_cold_N": round(JS4_FSH_COLD),
                  "js4_soak_PmPb_MPa": JS4_SOAK_PMPB, "model_js4_soak_F_sh_N": round(FSH4_SOAK), "k_sh_N_mm": round(K_SH), "k_b_N_mm": round(K_B),
                  "allowables_MPa": {"Fty_158": round(Fty158, 1), "Ftu_158": round(Ftu158, 1), "Fty_20": round(Fty20, 1), "Ftu_20": round(Ftu20, 1)},
                  "soak_frame": {"t_s": round(float(t[i_s]), 3), "T01_C": round(float(T01[i_s]), 1), "T02_C": round(float(T02[i_s]), 1)}},
       "rows": rows}
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16], "js4 soak F_sh model", round(FSH4_SOAK))
for k, r in rows.items():
    print(f"{k:22s} cold {r['cold']['fit']:6s} F_sh {r['cold']['F_sh_N']:5d} sig {r['cold']['sigma_pre_MPa']:6.1f} MS158 {r['cold']['MS_158C']} MS20 {r['cold']['MS_20C']} | soak {r['soak_GVLO_64.651s']['fit']:6s} F_sh {r['soak_GVLO_64.651s']['F_sh_N']:5d} PQ {r['soak_GVLO_64.651s']['PQ_PmPb_bound_MPa']:6.1f} {r['soak_GVLO_64.651s']['MS_PQ_vs_2Fty158']:+.3f}")
