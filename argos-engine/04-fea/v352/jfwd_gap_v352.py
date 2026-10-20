"""J-FWD TC-01 wall cells: hand scaling from js4 (CAD fit gap 0.025 mm) to the drawing gaps (H8 / f7 0.040-0.078 mm radial), lead 07:43Z
item 3: 'the TC-01 wall at the hole in the open-fit regime, where the whole screw force bends the wall ... give a hand scaling of the
TC-01 wall cells (seat P+Q, ligament, hole bearing) from js4 to the drawing max gap as a cross-check' (FEA3D runs the spot-face seat at
FIT_CLEARANCE 0.078 first).  Mechanical, 2026-10-20, v1.  CALC; every number DERIVED unless tagged; a cross-check, not a closure.

Model: the per-screw two-regime joint of jfwd_embed_v352_v1 (js4-consistent: k_sh 56 kN/mm from js4's 1.4 kN per 0.025 mm, clamped-wall
k_c, k_b calibrated to js4's +927 N), installation at the +25 % preload 3750 N with no embedding credit (the strength case), rev-3 B1
GVLO row histories (as jfwd_embed v1).  At each state and gap: screw force F_S, fit contact F_c and the part of the screw force that
pulls the wall in (bends the shell) F_sh = F_S - F_c (with the fit open F_c = 0, F_sh = F_S).
Scaling rule (stated, not proven): the wall stress that the preload causes is linear in F_sh (shell bending + membrane around the hole);
the head-seat bearing is linear in F_S; the pressure-driven (primary) stresses do not depend on the fit gap.  Cells:
 - seat P+Q at the soaks (no pressure: preload + thermal only): bound = the whole js4 P+Q scaled by F_sh(g) / F_sh(0.025) (the thermal
   share is scaled too, so this over-estimates); the F_S ratio is shown beside it;
 - flat-seat head bearing at the soaks: scaled by F_S(g) / F_S(0.025);
 - FA1S hole bearing (V / (d t)), ligament Pm+Pb and shear-out: primary (the shear V from the pressure end load; the preload is a
   self-limiting radial load, secondary): unchanged by the gap; the FA1S P+Q at the seat is bounded by FEA3D's FA1S ligament stress
   plus s_Q x F_sh(g), s_Q = js4 soak P+Q / F_sh (MPa per kN, the largest soak state; the thermal share counted as preload), against
   2 Fty(45.6 C);
 - band Neuber (local strain) is not scaled here (it needs FEA3D's split).
FE inputs (FEA3D, relayed by the lead 07:21Z and in CHANGELOG 236 (3) / (12), [DERIVED], spot-face seat): soak seat P+Q vs 2 Fty(T)
+0.645 / +0.577 / +0.598 (SOAK 64.7 s / SOAK70 / SOAK52, GVLO), soak flat-seat bearing +1.40 minimum, FA1S hole bearing +0.232 / +0.519,
seat ligament Pm+Pb +0.798 / +0.939, shear-out bound +0.644."""
import json, math, hashlib
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_gap_v352_v1.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
SRC = (J / "jfwd_embed_v352.py").read_text().split("# ---- embedding: residual preload")[0]
NS = {"__file__": str(J / "jfwd_embed_v352.py")}
exec(compile(SRC, str(J / "jfwd_embed_v352.py") + "(head)", "exec"), NS)
state, deltas, ROWS, K_B, K_SH, K_C, GAPS, F_MAX = (NS[k] for k in ("state", "deltas", "ROWS", "K_B", "K_SH", "K_C", "GAPS", "F_MAX"))
EMB = json.loads((J / "jfwd_embed_v352_v1.json").read_text())

FE = {"seat_PQ_soak": {"SOAK": 0.645, "SOAK70": 0.577, "SOAK52": 0.598}, "head_bearing_soak_min": 1.40,
      "FA1S": {"hole_bearing": [0.232, 0.519], "ligament_PmPb": [0.798, 0.939], "shear_out": [0.644, None]}}
t, T01, T02 = ROWS["GVLO"]
STATES = {"SOAK": 64.7, "SOAK70": 70.7, "SOAK52": 51.7}


def at(T01_, T02_, g):
    _, dw, dr = deltas(T01_, T02_)
    FS, u, Fc, sl = (float(x) for x in state(F_MAX, g, dw, dr, 0.0, K_B))
    return {"F_S_N": round(FS), "F_c_N": round(Fc), "F_sh_N": round(FS - Fc), "fit": "closed" if Fc > 0 else ("SLACK" if sl else "open"),
            "u_um": round(u * 1e3, 2), "d_w_um": round(dw * 1e3, 2), "d_r_um": round(dr * 1e3, 2)}


rows = {}
for nm, ts in STATES.items():
    i = int(np.argmin(np.abs(t - ts)))
    r = {"bound": "GVLO", "t_frame_s": round(float(t[i]), 3), "T01_C": round(float(T01[i]), 1), "T02_tap_C": round(float(T02[i]), 1), "gaps": {}}
    for gn, g in GAPS.items():
        r["gaps"][gn] = at(float(T01[i]), float(T02[i]), g)
    b = r["gaps"]["CAD_nominal_js4"]
    for gn, v in r["gaps"].items():
        v["ratio_F_sh"] = round(v["F_sh_N"] / b["F_sh_N"], 3)
        v["ratio_F_S"] = round(v["F_S_N"] / b["F_S_N"], 3)
        ms0 = FE["seat_PQ_soak"][nm]
        v["seat_PQ_MS_bound_Fsh"] = round((1.0 + ms0) / v["ratio_F_sh"] - 1.0, 3)
        v["seat_PQ_MS_Fs"] = round((1.0 + ms0) / v["ratio_F_S"] - 1.0, 3)
        v["head_bearing_MS_from_FE_min"] = round((1.0 + FE["head_bearing_soak_min"]) / v["ratio_F_S"] - 1.0, 3)
    rows[nm] = r
# the frame of the largest screw force at each gap (any GVLO frame), for the head bearing
mx = {}
for gn, g in GAPS.items():
    best = None
    for i in range(len(t)):
        v = at(float(T01[i]), float(T02[i]), g)
        if best is None or v["F_S_N"] > best[1]["F_S_N"]:
            best = (i, v)
    mx[gn] = dict(best[1], t_s=round(float(t[best[0]]), 3), T01_C=round(float(T01[best[0]]), 1))
# FA1S: cold joint at 45.6 C (engine at the ignition soak), no pressure effect on the fit (the screw row lies forward of both glands)
fa = {}
for gn, g in GAPS.items():
    fa[gn] = at(45.6, 45.6, g)
b = fa["CAD_nominal_js4"]
# preload (secondary) stress sensitivity of the seat wall from js4's soak P+Q (no pressure at the soak): s_Q = P+Q / F_sh, the largest of
# the three soak states (upper bound: the thermal share of the soak P+Q is counted as preload)
tab = NS["tab"]
sQ = {nm: (2.0 * tab("AL6061-T6", "Fty", r["T01_C"]) / (1.0 + FE["seat_PQ_soak"][nm])) / (r["gaps"]["CAD_nominal_js4"]["F_sh_N"] / 1e3) for nm, r in rows.items()}
S_Q = max(sQ.values())
FTY45, FTU45 = tab("AL6061-T6", "Fty", 45.6), tab("AL6061-T6", "Ftu", 45.6)
sig_lig = FTY45 / (1.0 + FE["FA1S"]["ligament_PmPb"][0])            # FEA3D's FA1S seat-ligament stress (yield basis), MPa
for gn, v in fa.items():
    v["ratio_F_sh"] = round(v["F_sh_N"] / b["F_sh_N"], 3)
    v["primary_cells_unchanged_by_gap"] = {"hole_bearing_MS": FE["FA1S"]["hole_bearing"], "ligament_PmPb_MS": FE["FA1S"]["ligament_PmPb"],
                                           "shear_out_MS": FE["FA1S"]["shear_out"][0]}
    pq = sig_lig + S_Q * v["F_sh_N"] / 1e3
    v["FA1S_seat_PQ_bound"] = {"sigma_MPa": round(pq, 1), "rule": "FEA3D FA1S ligament stress + s_Q x F_sh (the whole preload share added on top)",
                               "allow_2Fty_45.6C_MPa": round(2.0 * FTY45, 1), "MS": round(2.0 * FTY45 / pq - 1.0, 3)}
FA1S_NOTE = {"s_Q_MPa_per_kN_by_soak_state": {k: round(x, 1) for k, x in sQ.items()}, "s_Q_used": round(S_Q, 1),
             "FE_FA1S_ligament_stress_MPa": round(sig_lig, 1), "Fty_Ftu_45.6C_MPa": [round(FTY45, 1), round(FTU45, 1)],
             "classification": ("FA1S hole bearing, shear-out and ligament Pm / Pm+Pb are primary (the shear V of the pressure end load in a "
                                "bearing-type joint) and do not depend on the fit gap; the preload pull on the wall is a self-limiting radial "
                                "load (secondary, Q): it enters the P+Q check, bounded here")}
screw = {gn: EMB["torque_rows_3.0_4.0Nm"][f"3Nm|{gn}"]["first_firing"] for gn in GAPS}
out = {"id": "jfwd_gap_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"jfwd_embed_v352.py": sha(J / "jfwd_embed_v352.py"), "jfwd_embed_v352_v1.json": sha(J / "jfwd_embed_v352_v1.json"),
                  "k_sh_N_mm": round(K_SH), "k_c_N_mm": round(K_C), "k_b_N_mm": round(K_B), "F_V_N": F_MAX, "gaps_mm": GAPS,
                  "FE_beside": FE},
       "soak_states": rows, "max_screw_force_frame": mx, "FA1S_cold": fa, "FA1S_note": FA1S_NOTE, "screw_first_firing_from_jfwd_embed": screw}
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
for nm, r in rows.items():
    print(nm, r["t_frame_s"], r["T01_C"], r["T02_tap_C"], {gn: (v["F_S_N"], v["F_c_N"], v["F_sh_N"], v["fit"], v["ratio_F_sh"], v["seat_PQ_MS_bound_Fsh"], v["seat_PQ_MS_Fs"])
                                                       for gn, v in r["gaps"].items()})
print("max", {gn: (v["F_S_N"], v["fit"], v["t_s"]) for gn, v in mx.items()})
print("FA1S", {gn: (v["F_S_N"], v["F_c_N"], v["F_sh_N"], v["fit"], v["ratio_F_sh"], v["FA1S_seat_PQ_bound"]["sigma_MPa"], v["FA1S_seat_PQ_bound"]["MS"]) for gn, v in fa.items()}, FA1S_NOTE)
print("screw", {gn: (v["MS_min"], v["check"], v["F_S_N"]) for gn, v in screw.items()})
