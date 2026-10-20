"""J-FWD embedding / fit / J-F1 band rows re-run on K_js5 (CHANGELOG 239 (10): 'jfwd_embed, jfwd_fit and the J-F1 band rows are re-run on
K_js5; the K_js4 rows stay as found, information only').  Mechanical, 2026-10-20, v1.  CALC on SIM temperatures; DERIVED unless tagged.
No solver run, no thermal run.

Model: the relax v7 joint machinery, imported unchanged from jfwd_relax_v352.py (the 1-DOF screw / shell / fit model with the wall-yield
cap and the screw-set cap, K_js5 k_sh 33,433 N/mm, clamped-wall k_c, the IN718 flight screw 'IN718 M5 flight L 10.2 +/-0.1' with k_b at
both ends of the bracket (A4-80 x E ratio 1.0363: lo 418,365 / hi 1,100,023 N/mm; calibrated on the FE L 10.0, length effect ASSUMED
small), the seat-line coefficient c of each end (the seat and ring families coincide on the adopted envelope v3 0872de4ea7e3601d), the
rev-4 GVLO / GVHI row histories, two firings, embedding f_Z basis 8 / sensitivity 21 um (jfwd_embed v1, VDI 2230 guide values, MESYS
manual, LITERATURE; sensitivity ASSUMED)).  The relax v7 json is asserted: the module re-runs one of its 24 cases exactly.

Rows (each per k_b end):
  A  cold embedding: installed fit state and preload after embedding (no firing) at the J-F1 band ends 2250 / 4096 N and 3000 N (K 0.20
     at 3.0 N m), on the H8 / f7 drawing gaps 0.040 / 0.059 / 0.078, with the CAD 0.025 and the lead-08:10Z contingency fits H7/h6
     (0-0.0245) and H7/g6 (0.005-0.0295) as information;
  B  first firing at the 4096 N J-F1 maximum, no embedding credit: the 1-DOF model's maximum screw force, wall set and seat state
     (information: the model caps the seat at Fty(T) by wall set; the quoted screw and thread rows are rows v6, FE-anchored);
  C  in-service minimum after embedding (from relax v7's 24 cases, no recompute): per gap and embedding level, both firings;
  D  the torque window without slack: the 24-case grid at installation preloads 2250 / 3000 / 3750 / 4096 / 4164 / 5461 N (3.0 N m at
     J-F1's K window 0.1465-0.267 spans 2250-4096 N; 4.0 N m, superseded, would span 3000-5461 N);
  E  the J-F1 maximum: rows v6 (FE-anchored on THE ROW, A_n 68.13 mm2) restated with K_min at 3.0 N m;
  F  the contingency fits on K_js5: relax v7's gap sweep below the 0.040 drawing minimum (no gap seats all 24); the gland-1 / assembly rows
     of jfwd_fit v1 depend on the clearance only and stand as found.
The K_js4 rows (jfwd_embed_v352_v1.json, jfwd_fit_v352_v1.json: k_sh 56 kN/mm, k_b 157,898 N/mm calibrated to js4's +927 N, A4 screw)
stay as found, information only."""
import importlib.util, json, math, hashlib
from pathlib import Path

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_embed_fit_js5_v352_v1.json"
RELAX_PY = J / "jfwd_relax_v352.py"
RELAXJ = J / "jfwd_relax_v352_v7.json"
ROWSJ = J / "jfwd_in718_rows_v352_v6.json"
EMB4J = J / "jfwd_embed_v352_v1.json"
FIT4J = J / "jfwd_fit_v352_v1.json"
ENV_SHA16 = "0872de4ea7e3601d"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]

_spec = importlib.util.spec_from_file_location("jfwd_relax_v7", RELAX_PY)
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)
rel = json.loads(RELAXJ.read_text())
rws = json.loads(ROWSJ.read_text())
emb4 = json.loads(EMB4J.read_text())
assert R.ENV_SHA16 == ENV_SHA16 and rel["inputs"]["fea3d_soak_envelope"]["sha256_16_at_read"] == ENV_SHA16, "envelope"
assert rws["version"] == "v6" and rws["inputs"]["fea3d_soak_envelope"]["sha256_16"] == ENV_SHA16, "rows v6"
INK = R.IN_KEY
assert any(k.startswith(INK + "|") for k in rel["verdict_24"]), "relax v7 json carries another IN718 key"

END = {}
for end in ("lo", "hi"):
    scr, ksh, kb, c = R.opt_params(INK, end, "seat")
    v = rel["verdict_24"][f"{INK}|{end}|seat"]
    assert round(kb) == v["k_b_N_mm"] and round(ksh) == v["k_sh_N_mm"] and abs(c - v["c"]) < 1e-5, (end, kb, ksh, c)
    END[end] = (scr, ksh, kb, c)
# the module reproduces relax v7 exactly (one case per end)
for end in ("lo", "hi"):
    scr, ksh, kb, c = END[end]
    case = rel["verdict_24"][f"{INK}|{end}|seat"]["min_case"]
    gn, iname, en, gv = case.split("|")
    x = R.run_case(R.INSTALL[iname], R.GAPS[gn], R.EMB[en], R.ROWS4[gv], c, ksh, kb, scr)
    ref = rel["cases_24"][f"{INK}|{end}|seat"][case]
    assert x["firing_2"]["F_S_min_N"] == ref["firing_2"]["F_S_min_N"] and x["firing_2"]["cold_end_F_S_N"] == ref["firing_2"]["cold_end_F_S_N"], (end, case)

TORQUE, D_NOM = 3.0, 5.0
K_WIN = (0.1465, 0.267)          # J-F1 K window at 3.0 N m (CHANGELOG: maximum 4096 N (K >= 0.1465), minimum >= 2250 N (K <= 0.267))
GAPS_DRAW = dict(R.GAPS)
GAPS_INFO = {"CAD_0.025_js4_info": 0.025, "H7h6_min_info": 0.0, "H7h6_max_info": 0.0245, "H7g6_min_info": 0.005, "H7g6_max_info": 0.0295}
INST_A = {"J-F1_min_2250": 2250.0, "nominal_3000_K0.20_3Nm": 3000.0, "J-F1_max_4096": 4096.0}

# ---- A: cold embedding
A = {}
for end, (scr, ksh, kb, c) in END.items():
    for gn, g in dict(GAPS_DRAW, **GAPS_INFO).items():
        for iname, FV in INST_A.items():
            for en, f in R.EMB.items():
                FS0, u0, Fc0, _ = R.state_s(FV, g, 0.0, 0.0, 0.0, 0.0, ksh, kb)
                FS1, u1, Fc1, _ = R.state_s(FV, g, 0.0, 0.0, f, 0.0, ksh, kb)
                A[f"{end}|{gn}|{iname}|{en}"] = {
                    "gap_mm": g, "F_install_N": FV, "f_Z_um": round(f * 1e3, 1),
                    "installed_fit": "closed" if Fc0 > 0 else "open", "installed_fit_contact_N": round(Fc0),
                    "F_after_embedding_N": round(max(FS1, 0.0)), "loss_N": round(FV - max(FS1, 0.0)),
                    "fit_after": "closed" if Fc1 > 0 else ("SLACK" if FS1 <= 0 else "open"), "fit_contact_after_N": round(Fc1),
                    "wall_lift_um": round(max(u1, 0.0) * 1e3, 2), "F_to_close_gap_cold_N": round(ksh * g)}

# ---- B: first firing at the 4096 N maximum, no embedding credit (1-DOF model, information)
B = {}
for end, (scr, ksh, kb, c) in END.items():
    for gn, g in GAPS_DRAW.items():
        for gv, fr in R.ROWS4.items():
            x = R.run_case(4096.0, g, 0.0, fr, c, ksh, kb, scr)
            f1 = x["firing_1"]
            B[f"{end}|{gn}|{gv}"] = {"F_S_max_N": f1["F_S_max_N"], "F_S_min_N": f1["F_S_min_N"], "wall_set_after_firing_1_um": x["wall_set_after_firing_1_um"],
                                     "wall_yield_frames": f1["wall_yield_frames"], "screw_set_after_firing_1_um": x["screw_set_after_firing_1_um"],
                                     "fibre_max_MPa": f1["fibre_max_MPa"], "max_seat_over_Fty": f1["max_sig_over_Fty"],
                                     "cold_end_F_S_N": f1["cold_end_F_S_N"]}

# ---- C: in-service minimum after embedding (relax v7 24 cases, no recompute)
C = {}
for end in END:
    cs = rel["cases_24"][f"{INK}|{end}|seat"]
    for gn in GAPS_DRAW:
        for en in R.EMB:
            sel = {k: x for k, x in cs.items() if k.split("|")[0] == gn and k.split("|")[2] == en}
            mn = lambda x: min(x["firing_1"]["F_S_min_N"], x["firing_2"]["F_S_min_N"])
            j = min(sel, key=lambda k: mn(sel[k]))
            C[f"{end}|{gn}|{en}"] = {"F_S_min_any_frame_N": mn(sel[j]), "min_case": j,
                                     "slack_frames_max": max(x["firing_1"]["slack_frames"] + x["firing_2"]["slack_frames"] for x in sel.values()),
                                     "n_unseated_of_4": sum(1 for x in sel.values() if not x["heads_seated_both_firings"]),
                                     "cold_after_embedding_min_N": min(x["installed_cold_after_embedding_N"] for x in sel.values()),
                                     "cold_end_after_firing_2_min_N": min(x["firing_2"]["cold_end_F_S_N"] for x in sel.values()),
                                     "wall_set_max_um": max(x["wall_set_after_firing_2_um"] for x in sel.values())}

# ---- D: torque window without slack (24-case grid per installation preload)
F_SWEEP = (2250.0, 3000.0, 3750.0, 4096.0, 4164.0, 5461.0)
D = {}
for end, (scr, ksh, kb, c) in END.items():
    for FV in F_SWEEP:
        d = R.run_grid(GAPS_DRAW, {f"F{FV:.0f}": FV}, ksh, kb, c, scr)
        mn = lambda x: min(x["firing_1"]["F_S_min_N"], x["firing_2"]["F_S_min_N"])
        j = min(d, key=lambda k: mn(d[k]))
        D[f"{end}|{FV:.0f}"] = {"F_install_N": FV, "K_at_3Nm": round(TORQUE * 1e3 / (FV * D_NOM), 4), "K_at_4Nm_superseded": round(4.0e3 / (FV * D_NOM), 4),
                                "all_seated": all(x["heads_seated_both_firings"] for x in d.values()),
                                "n_unseated_of_12": sum(1 for x in d.values() if not x["heads_seated_both_firings"]), "F_S_min_N": mn(d[j]),
                                "min_case": j, "cold_end_F_S_min_N": min(x["firing_2"]["cold_end_F_S_N"] for x in d.values()),
                                "max_wall_set_um": max(x["wall_set_after_firing_2_um"] for x in d.values())}
window = {end: [D[f"{end}|{FV:.0f}"]["F_install_N"] for FV in F_SWEEP if D[f"{end}|{FV:.0f}"]["all_seated"]] for end in END}
fsmin_same = {end: len({D[f"{end}|{FV:.0f}"]["F_S_min_N"] for FV in F_SWEEP}) == 1 for end in END}

# ---- E: the J-F1 maximum (rows v6, FE-anchored, THE ROW)
fx = rws["TC02_thread_shear_full_row"]["fixes"]["a_lower_J-F1_max"]
E = {"source": {"path": str(ROWSJ), "sha256_16": sha(ROWSJ)}, "basis": "rows v6 FE-anchored N on THE ROW (A_n 68.13 mm2, L_e 7.314 mm at the 0.078 gap bound)",
     "F_max_for_MS_y_0_N": fx["F_max_for_MS_y_0_N"], "F_max_for_MS_y_0.05_N": fx["F_max_for_MS_y_0.05_N"],
     "K_min_at_3Nm_for_MS_y_0": round(TORQUE * 1e3 / (fx["F_max_for_MS_y_0_N"] * D_NOM), 4),
     "K_min_at_3Nm_for_MS_y_0.05": round(TORQUE * 1e3 / (fx["F_max_for_MS_y_0.05_N"] * D_NOM), 4),
     "J_F1_band_at_3Nm_N": [round(TORQUE * 1e3 / (K_WIN[1] * D_NOM)), round(TORQUE * 1e3 / (K_WIN[0] * D_NOM))],
     "J_F1_K_window": list(K_WIN), "governing_state": fx["governing_state"], "N_from": fx["N_from"],
     "verdict": (f"the ruled J-F1 band 2250-4096 N (3.0 N m, K {K_WIN[0]}-{K_WIN[1]}) lies inside the FE-anchored thread maximum "
                 f"{fx['F_max_for_MS_y_0_N']} N (MS_y 0, {fx['governing_state']} {fx['N_from']}); MS_y >= 0.05 would need "
                 f"{fx['F_max_for_MS_y_0.05_N']} N (K >= {TORQUE * 1e3 / (fx['F_max_for_MS_y_0.05_N'] * D_NOM):.4f}), below the 3750 N nominal")}

# ---- F: contingency fits on K_js5 (relax v7 gap sweep)
sf = rel["select_fit_gap_cap_IN718"]
F = {"from_relax_v7": {k: {"g_cap_mm": v["g_cap_mm"], "note": v["note"],
                           "any_gap_0_to_0.0375_seats_all": any(v["below_0.040_info"].values()),
                           "any_gap_0.040_to_0.120_seats_all": any(v["sweep_0.040_0.120"].values())} for k, v in sf.items()},
     "H7h6_H7g6": "the contingency fits (radial 0-0.0245 / 0.005-0.0295) lie inside relax v7's 0-0.0375 sweep: no gap seats all 24 at either k_b "
                  "end, so a tighter fit does not remove the slack on K_js5 (on K_js4, jfwd_fit v1 gave a window 2.40-4.64 N m with the "
                  "sensitivity embedding at H7/g6 max: superseded, information only)",
     "gland_1_and_assembly": "jfwd_fit v1 gland-1 / assembly rows (extrusion gap at the maximum clearance, burn closure and thermal interference "
                             "at the minimum clearance) depend on the clearance only, not on K: they stand as found for a contingency fit"}

# ---- K_js4 record
K4 = {"jfwd_embed_v352_v1.json": sha(EMB4J), "jfwd_fit_v352_v1.json": sha(FIT4J),
      "k_sh_js4_N_mm": emb4["stiffness_js4_consistent"]["k_sh_N_mm_from_js4"], "k_b_js4_calibrated_N_mm": emb4["stiffness_js4_consistent"]["k_b_calibrated_N_mm"],
      "J_F1_max_js4_model_N": {k: v["F_inst_max_N"] for k, v in emb4["allowed_installation_preload_no_embedding"].items()},
      "status": "AS FOUND, information only (239 (10)); superseded by K_js5 (relax v7) and the FE-anchored rows v6"}

slack_cold = sorted(k for k, v in A.items() if k.split("|")[1] in GAPS_INFO and v["fit_after"] == "SLACK")
_n_per_gap = 2 * len(INST_A) * len(R.EMB)
slack_cold_txt = "; ".join(f"{gn.replace('_info', '')} (gap {GAPS_INFO[gn]:g}) {sum(1 for k in slack_cold if k.split('|')[1] == gn)} of {_n_per_gap} rows"
                           for gn in GAPS_INFO if any(k.split("|")[1] == gn for k in slack_cold)) or "none"
A_SLACK_INFO = {"rows": slack_cold, "summary": slack_cold_txt, "rows_per_gap": _n_per_gap}
a_min = {end: min((v for k, v in A.items() if k.startswith(end + "|") and k.split("|")[1] in GAPS_DRAW and k.split("|")[2] == "J-F1_min_2250"),
                  key=lambda v: v["F_after_embedding_N"]) for end in END}
b_max = {end: max((v for k, v in B.items() if k.startswith(end + "|")), key=lambda v: v["F_S_max_N"]) for end in END}
stmt = (f"On K_js5 (k_sh {END['lo'][1]:.0f} N/mm) with the IN718 flight screw: cold after embedding every drawing gap keeps the head seated "
        f"(2250 N, sensitivity 21 um: minimum {a_min['lo']['F_after_embedding_N']} / {a_min['hi']['F_after_embedding_N']} N at k_b lo / hi, fit "
        f"{a_min['lo']['fit_after']} / {a_min['hi']['fit_after']}); the first firing at 4096 N without embedding credit reaches "
        f"{b_max['lo']['F_S_max_N']} / {b_max['hi']['F_S_max_N']} N in the 1-DOF model (wall set {b_max['lo']['wall_set_after_firing_1_um']} / "
        f"{b_max['hi']['wall_set_after_firing_1_um']} um; the quoted screw and thread rows stay rows v6); the in-service minimum after embedding is "
        f"{min(v['F_S_min_any_frame_N'] for k, v in C.items() if k.startswith('lo|'))} / {min(v['F_S_min_any_frame_N'] for k, v in C.items() if k.startswith('hi|'))} N "
        f"(relax v7, FOUND NEGATIVE, 239 (3)); the torque window without slack is "
        + ("EMPTY" if not any(window.values()) else f"{window}")
        + f" over installation preloads {F_SWEEP[0]:.0f}-{F_SWEEP[-1]:.0f} N at both k_b ends (F_S min "
        + ("identical at every preload: the first-firing wall set at the Fty(T) seat cap absorbs the installation preload" if all(fsmin_same.values()) else "varies with the preload")
        + f"); the J-F1 maximum stays the FE-anchored {E['F_max_for_MS_y_0_N']} N (MS_y 0, THE ROW), so the ruled 2250-4096 N band holds; the "
          f"contingency fits do not remove the slack, and at their minimum gaps the head goes SLACK cold after embedding ({slack_cold_txt}): "
          f"with the fit closed the embedding acts through the stiff closed-fit joint. The K_js4 rows stay as found, information only.")

out = {"id": "jfwd_embed_fit_js5_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "status": "CALC on SIM temperatures; DERIVED unless tagged; negatives SHOWN AS FOUND; not physical approval",
       "inputs": {"relax_module": {"path": str(RELAX_PY), "sha256_16": sha(RELAX_PY)}, "relax_v7": {"path": str(RELAXJ), "sha256_16": sha(RELAXJ)},
                  "rows_v6": {"path": str(ROWSJ), "sha256_16": sha(ROWSJ)}, "fea3d_soak_envelope": {"sha256_16": ENV_SHA16},
                  "screw_key": INK, "k_b_N_mm": {e: round(v[2]) for e, v in END.items()}, "k_sh_N_mm": round(END["lo"][1]), "k_c_N_mm": round(R.K_C),
                  "c_seat_MPa_per_N": {e: round(v[3], 5) for e, v in END.items()}, "f_Z_um": {k: round(v * 1e3, 1) for k, v in R.EMB.items()},
                  "gaps_drawing_mm": GAPS_DRAW, "gaps_information_mm": GAPS_INFO, "J_F1_K_window_3Nm": list(K_WIN)},
       "A_cold_embedding": A, "B_first_firing_4096_no_embedding_model_info": B, "C_in_service_minimum_after_embedding_relax_v7": C,
       "D_torque_window_without_slack": {"rows": D, "window_N_by_end": window, "F_S_min_identical_over_preloads": fsmin_same},
       "A_cold_embedding_slack_at_contingency_gaps_info": A_SLACK_INFO, "E_J_F1_maximum_rows_v6": E, "F_contingency_fits_K_js5": F, "K_js4_record": K4, "statement": stmt}
s = json.dumps(out, indent=1, default=float)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
print(stmt)
for k, v in D.items():
    print("D", k, {kk: v[kk] for kk in ("all_seated", "n_unseated_of_12", "F_S_min_N", "cold_end_F_S_min_N", "max_wall_set_um")})
for k, v in C.items():
    print("C", k, v["F_S_min_any_frame_N"], v["n_unseated_of_4"], v["cold_after_embedding_min_N"], v["cold_end_after_firing_2_min_N"])
for k, v in B.items():
    print("B", k, v["F_S_max_N"], v["wall_set_after_firing_1_um"], v["max_seat_over_Fty"])
