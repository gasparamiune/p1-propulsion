"""J-FWD embedding / fit / J-F1 band rows on K_js5, v2: RE-STATED AT THE J-F1 BAND CAPPED AT 3750 N (lead 17:55:55Z F1: 'Re-state the
rows that depend on the minimum at the new minimum: about 2060 N with today's K range scaled by 3750 / 4096, or the J-F1 lot result.
That covers the cold-after-embedding seating and the K_js5 rows.  If any turns negative, stop and tell me.').  Mechanical, 2026-10-20,
v2 (v1 671c61b55f9a086f / json 939b7f3708928613 kept as jfwd_embed_fit_js5_v352_v1.py).  CALC on SIM temperatures; DERIVED unless
tagged.  No solver run, no thermal run.
v2 band: J-F1 torque = 3750 x K_min x d = 3750 x 0.1465 x 5 = 2746.9 N mm (2.747 N m on today's K window 0.1465-0.267); minimum
2746.9 / (0.267 x 5) = 2057.6 N (= 2250 x 3750 / 4096 within the rounding of 2250); the J-F1 lot result replaces both when it exists.
The band ends 2057.6 / 3750 N are GOVERNING; 2250 / 3000 / 4096 N are information (superseded band, v1).  Re-stated:
  A  cold embedding at 2057.6 / 2746.9 (K 0.20 at the J-F1 torque) / 3750 N (2250 / 3000 / 4096 information);
  B  first firing at the 3750 N maximum (4096 information);
  C  in-service minimum after embedding: the 24-case grid RE-RUN at 2057.6 / 3750 N (relax v7's 2250 / 4096 grid kept as information);
  D  the sweep adds 2057.6 and 2746.9 N; K quoted at the J-F1 torque 2.747 N m (3.0 N m information);
  E  rows v7 (THE ROW, route (i), A_n 67.93 mm2): the 3750 N cap against the FE-anchored thread maximum;
  F  the contingency-fit gap sweep RE-RUN at 2057.6 / 3750 N.
This is the NO-SPRING K_js5 joint (rows A-F as v1).  Route (i) (spring A solid under the head, lead 16:53Z R2) is jfwd_spring v4, which
carries the route-(i) 24-case and its cold end at the same band.
v1 notes follow (band 2250-4096 N at 3.0 N m, rows v6).
J-FWD embedding / fit / J-F1 band rows re-run on K_js5 (CHANGELOG 239 (10): 'jfwd_embed, jfwd_fit and the J-F1 band rows are re-run on
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
import importlib.util, json, math, hashlib, time
from pathlib import Path

T0 = time.time()
J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_embed_fit_js5_v352_v2.json"
RELAX_PY = J / "jfwd_relax_v352.py"
RELAXJ = J / "jfwd_relax_v352_v7.json"
ROWSJ = J / "jfwd_in718_rows_v352_v7.json"
V1J = J / "jfwd_embed_fit_js5_v352_v1.json"
EMB4J = J / "jfwd_embed_v352_v1.json"
FIT4J = J / "jfwd_fit_v352_v1.json"
ENV_SHA16 = "0872de4ea7e3601d"
ROWS7_SHA16, V1J_SHA16 = "6113d28b64d0dba5", "939b7f3708928613"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]

_spec = importlib.util.spec_from_file_location("jfwd_relax_v7", RELAX_PY)
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)
rel = json.loads(RELAXJ.read_text())
rws = json.loads(ROWSJ.read_text())
emb4 = json.loads(EMB4J.read_text())
v1 = json.loads(V1J.read_text())
assert R.ENV_SHA16 == ENV_SHA16 and rel["inputs"]["fea3d_soak_envelope"]["sha256_16_at_read"] == ENV_SHA16, "envelope"
assert sha(ROWSJ) == ROWS7_SHA16 and rws["version"] == "v7" and rws["inputs"]["fea3d_soak_envelope"]["sha256_16"] == ENV_SHA16, "rows v7"
assert sha(V1J) == V1J_SHA16 and v1["version"] == "v1", "js5 v1 json"
INK = R.IN_KEY
assert any(k.startswith(INK + "|") for k in rel["verdict_24"]), "relax v7 json carries another IN718 key"

END = {}
for end in ("lo", "hi"):
    scr, ksh, kb, c = R.opt_params(INK, end, "seat")
    v = rel["verdict_24"][f"{INK}|{end}|seat"]
    assert round(kb) == v["k_b_N_mm"] and round(ksh) == v["k_sh_N_mm"] and abs(c - v["c"]) < 1e-5, (end, kb, ksh, c)
    END[end] = (scr, ksh, kb, c)
# the module reproduces relax v7 exactly (one case per end, at relax v7's own installation keys)
for end in ("lo", "hi"):
    scr, ksh, kb, c = END[end]
    case = rel["verdict_24"][f"{INK}|{end}|seat"]["min_case"]
    gn, iname, en, gv = case.split("|")
    x = R.run_case(R.INSTALL[iname], R.GAPS[gn], R.EMB[en], R.ROWS4[gv], c, ksh, kb, scr)
    ref = rel["cases_24"][f"{INK}|{end}|seat"][case]
    assert x["firing_2"]["F_S_min_N"] == ref["firing_2"]["F_S_min_N"] and x["firing_2"]["cold_end_F_S_N"] == ref["firing_2"]["cold_end_F_S_N"], (end, case)

# ---- the J-F1 band (lead 17:55:55Z F1)
D_NOM = 5.0
K_WIN = (0.1465, 0.267)                 # today's J-F1 K window (CHANGELOG: K >= 0.1465 / K <= 0.267)
F_CAP = 3750.0                          # J-F1 maximum, CAPPED (F1)
T_JF1 = F_CAP * K_WIN[0] * D_NOM        # 2746.875 N mm = 2.747 N m
F_MIN = T_JF1 / (K_WIN[1] * D_NOM)      # 2057.58 N
F_NOM = T_JF1 / (0.20 * D_NOM)          # 2746.9 N at K 0.20
assert abs(F_MIN - rws["J_F1"]["minimum_N_today_K_window"]) < 0.05 and rws["J_F1"]["maximum_N"] == F_CAP, "rows v7 J_F1 band"
BAND = {"J-F1_min_2058": F_MIN, "J-F1_max_3750": F_CAP}
GAPS_DRAW = dict(R.GAPS)
GAPS_INFO = {"CAD_0.025_js4_info": 0.025, "H7h6_min_info": 0.0, "H7h6_max_info": 0.0245, "H7g6_min_info": 0.005, "H7g6_max_info": 0.0295}
INST_A = {"J-F1_min_2058": F_MIN, "nominal_2747_K0.20": F_NOM, "J-F1_max_3750": F_CAP,
          "superseded_min_2250_info": 2250.0, "superseded_nominal_3000_info": 3000.0, "superseded_max_4096_info": 4096.0}
GOV = ("J-F1_min_2058", "nominal_2747_K0.20", "J-F1_max_3750")
mn = lambda x: min(x["firing_1"]["F_S_min_N"], x["firing_2"]["F_S_min_N"])

# ---- A: cold embedding
A = {}
for end, (scr, ksh, kb, c) in END.items():
    for gn, g in dict(GAPS_DRAW, **GAPS_INFO).items():
        for iname, FV in INST_A.items():
            for en, f in R.EMB.items():
                FS0, u0, Fc0, _ = R.state_s(FV, g, 0.0, 0.0, 0.0, 0.0, ksh, kb)
                FS1, u1, Fc1, _ = R.state_s(FV, g, 0.0, 0.0, f, 0.0, ksh, kb)
                A[f"{end}|{gn}|{iname}|{en}"] = {
                    "gap_mm": g, "F_install_N": round(FV, 1), "f_Z_um": round(f * 1e3, 1),
                    "column": "GOVERNING" if iname in GOV else "INFORMATION (superseded band)",
                    "installed_fit": "closed" if Fc0 > 0 else "open", "installed_fit_contact_N": round(Fc0),
                    "F_after_embedding_N": round(max(FS1, 0.0)), "F_after_embedding_signed_N": round(FS1, 1), "loss_N": round(FV - max(FS1, 0.0)),
                    "fit_after": "closed" if Fc1 > 0 else ("SLACK" if FS1 <= 0 else "open"), "fit_contact_after_N": round(Fc1),
                    "wall_lift_um": round(max(u1, 0.0) * 1e3, 2), "F_to_close_gap_cold_N": round(ksh * g)}
# v1 reproduced at the superseded keys (same model, same inputs)
for k, x in A.items():
    end, gn, iname, en = k.split("|")
    old = {"superseded_min_2250_info": "J-F1_min_2250", "superseded_nominal_3000_info": "nominal_3000_K0.20_3Nm",
           "superseded_max_4096_info": "J-F1_max_4096"}.get(iname)
    if old:
        y = v1["A_cold_embedding"][f"{end}|{gn}|{old}|{en}"]
        assert x["F_after_embedding_N"] == y["F_after_embedding_N"] and x["fit_after"] == y["fit_after"], (k, x["F_after_embedding_N"], y["F_after_embedding_N"])

# ---- B: first firing at the 3750 N maximum (4096 information), no embedding credit (1-DOF model, information)
B = {}
for end, (scr, ksh, kb, c) in END.items():
    for gn, g in GAPS_DRAW.items():
        for gv, fr in R.ROWS4.items():
            for FV, col in ((F_CAP, "GOVERNING"), (4096.0, "INFORMATION (superseded maximum)")):
                x = R.run_case(FV, g, 0.0, fr, c, ksh, kb, scr)
                f1 = x["firing_1"]
                B[f"{end}|{gn}|{gv}|{FV:.0f}"] = {"column": col, "F_S_max_N": f1["F_S_max_N"], "F_S_min_N": f1["F_S_min_N"],
                                                  "wall_set_after_firing_1_um": x["wall_set_after_firing_1_um"],
                                                  "wall_yield_frames": f1["wall_yield_frames"], "screw_set_after_firing_1_um": x["screw_set_after_firing_1_um"],
                                                  "fibre_max_MPa": f1["fibre_max_MPa"], "max_seat_over_Fty": f1["max_sig_over_Fty"],
                                                  "cold_end_F_S_N": f1["cold_end_F_S_N"]}
for k, x in B.items():
    if k.endswith("|4096"):
        y = v1["B_first_firing_4096_no_embedding_model_info"][k[:-5]]
        assert x["F_S_max_N"] == y["F_S_max_N"], (k, x["F_S_max_N"], y["F_S_max_N"])


# ---- C: in-service minimum after embedding: the 24-case grid RE-RUN at the band
def band_summary(d, k_min):
    j = min(d, key=lambda k: mn(d[k]))
    jf = max(d, key=lambda k: d[k]["firing_2"]["fibre_max_MPa"] / max(d[k]["firing_2"]["Rp_at_fibre_max_MPa"], 1e-9))
    lo_keys = [k for k in d if k.split("|")[1] == k_min]
    return {"n_cases": len(d), "all_seated": all(x["heads_seated_both_firings"] for x in d.values()),
            "n_unseated": sum(1 for x in d.values() if not x["heads_seated_both_firings"]),
            "unseated_cases": [k for k, x in d.items() if not x["heads_seated_both_firings"]],
            "F_S_min_N": mn(d[j]), "min_case": j,
            "F_S_max_N": max(max(x["firing_1"]["F_S_max_N"], x["firing_2"]["F_S_max_N"]) for x in d.values()),
            "installed_cold_after_embedding_min_N_at_J_F1_min": min(d[k]["installed_cold_after_embedding_N"] for k in lo_keys),
            "cold_end_F_S_min_N_at_J_F1_min": min(d[k]["firing_2"]["cold_end_F_S_N"] for k in lo_keys),
            "cold_end_F_S_min_N_all": min(x["firing_2"]["cold_end_F_S_N"] for x in d.values()),
            "max_wall_set_um": max(x["wall_set_after_firing_2_um"] for x in d.values()),
            "max_screw_set_um": max(x["screw_set_after_firing_2_um"] for x in d.values()),
            "fibre_over_Rp_max": round(d[jf]["firing_2"]["fibre_max_MPa"] / d[jf]["firing_2"]["Rp_at_fibre_max_MPa"], 3),
            "screw_shakedown_min_MS": min(x["screw_shakedown"]["MS"] for x in d.values()),
            "max_seat_over_Fty": max(max(x["firing_1"]["max_sig_over_Fty"], x["firing_2"]["max_sig_over_Fty"]) for x in d.values())}


GRID, C24 = {}, {}
for end, (scr, ksh, kb, c) in END.items():
    GRID[end] = R.run_grid(GAPS_DRAW, BAND, ksh, kb, c, scr)
    C24[end] = band_summary(GRID[end], "J-F1_min_2058")
    rv7 = rel["worse_end_quoted"][f"{INK}|seat"]["both_ends"][end]
    C24[end]["relax_v7_at_2250_4096_info"] = {"F_S_min_N": rv7["F_S_min_N"], "n_unseated": rv7["n_unseated"],
                                              "cold_end_F_S_min_2250_N": rv7["cold_end_F_S_min_2250_N"], "max_wall_set_um": rv7["max_wall_set_um"]}
C = {}
for end in END:
    cs = GRID[end]
    for gn in GAPS_DRAW:
        for en in R.EMB:
            sel = {k: x for k, x in cs.items() if k.split("|")[0] == gn and k.split("|")[2] == en}
            j = min(sel, key=lambda k: mn(sel[k]))
            C[f"{end}|{gn}|{en}"] = {"F_S_min_any_frame_N": mn(sel[j]), "min_case": j,
                                     "slack_frames_max": max(x["firing_1"]["slack_frames"] + x["firing_2"]["slack_frames"] for x in sel.values()),
                                     "n_unseated_of_4": sum(1 for x in sel.values() if not x["heads_seated_both_firings"]),
                                     "cold_after_embedding_min_N": min(x["installed_cold_after_embedding_N"] for x in sel.values()),
                                     "cold_end_after_firing_2_min_N": min(x["firing_2"]["cold_end_F_S_N"] for x in sel.values()),
                                     "wall_set_max_um": max(x["wall_set_after_firing_2_um"] for x in sel.values())}

# ---- D: torque window without slack (24-case grid per installation preload)
F_SWEEP = (F_MIN, 2250.0, F_NOM, 3000.0, F_CAP, 4096.0, 4164.0, 5461.0)
D = {}
for end, (scr, ksh, kb, c) in END.items():
    for FV in F_SWEEP:
        d = R.run_grid(GAPS_DRAW, {f"F{FV:.0f}": FV}, ksh, kb, c, scr)
        j = min(d, key=lambda k: mn(d[k]))
        D[f"{end}|{FV:.0f}"] = {"F_install_N": round(FV, 1), "K_at_J_F1_torque_2.747Nm": round(T_JF1 / (FV * D_NOM), 4),
                                "K_at_3Nm_info": round(3.0e3 / (FV * D_NOM), 4), "K_at_4Nm_superseded": round(4.0e3 / (FV * D_NOM), 4),
                                "all_seated": all(x["heads_seated_both_firings"] for x in d.values()),
                                "n_unseated_of_12": sum(1 for x in d.values() if not x["heads_seated_both_firings"]), "F_S_min_N": mn(d[j]),
                                "min_case": j, "cold_end_F_S_min_N": min(x["firing_2"]["cold_end_F_S_N"] for x in d.values()),
                                "installed_cold_after_embedding_min_N": min(x["installed_cold_after_embedding_N"] for x in d.values()),
                                "max_wall_set_um": max(x["wall_set_after_firing_2_um"] for x in d.values())}
        if f"{end}|{FV:.0f}" in {f"{e}|{F:.0f}" for e in END for F in (2250.0, 3000.0, 4096.0, 4164.0, 5461.0)}:
            y = v1["D_torque_window_without_slack"]["rows"][f"{end}|{FV:.0f}"]
            assert D[f"{end}|{FV:.0f}"]["F_S_min_N"] == y["F_S_min_N"] and D[f"{end}|{FV:.0f}"]["n_unseated_of_12"] == y["n_unseated_of_12"], (end, FV)
window = {end: [D[f"{end}|{FV:.0f}"]["F_install_N"] for FV in F_SWEEP if D[f"{end}|{FV:.0f}"]["all_seated"]] for end in END}
fsmin_same = {end: len({D[f"{end}|{FV:.0f}"]["F_S_min_N"] for FV in F_SWEEP}) == 1 for end in END}

# ---- E: the J-F1 maximum (rows v7, FE-anchored, THE ROW route (i))
fx = rws["TC02_thread_shear_full_row"]["fixes"]["a_lower_J-F1_max"]
trow = rws["TC02_thread_shear_full_row"]["rows"]
cap_rows = {st: r["3750"]["THE_ROW"]["MS_y"] for st, r in trow.items() if "3750" in r and "THE_ROW" in r["3750"]}
cap_min = min(cap_rows, key=cap_rows.get)
E = {"source": {"path": str(ROWSJ), "sha256_16": sha(ROWSJ)},
     "basis": "rows v7 FE-anchored N on THE ROW (route (i): ENG-HW-101-IN718 M5 x 10.7 +/-0.1 over spring A t 0.44-0.52; A_n 67.93 mm2, "
              "L_e 7.294 mm at the 0.078 gap bound)",
     "F_max_for_MS_y_0_N": fx["F_max_for_MS_y_0_N"], "F_max_for_MS_y_0.05_N": fx["F_max_for_MS_y_0.05_N"],
     "J_F1_cap_N": F_CAP, "MS_y_at_cap_by_state": cap_rows, "MS_y_at_cap_min": {"state": cap_min, "MS_y": cap_rows[cap_min]},
     "K_min_at_J_F1_torque_for_MS_y_0": round(T_JF1 / (fx["F_max_for_MS_y_0_N"] * D_NOM), 4),
     "K_min_at_J_F1_torque_for_MS_y_0.05": round(T_JF1 / (fx["F_max_for_MS_y_0.05_N"] * D_NOM), 4),
     "J_F1_band_N": [round(F_MIN, 1), F_CAP], "J_F1_torque_Nm": round(T_JF1 / 1e3, 4), "J_F1_K_window": list(K_WIN),
     "governing_state": fx["governing_state"], "N_from": fx["N_from"],
     "verdict": (f"the J-F1 band {F_MIN:.1f}-{F_CAP:.0f} N ({T_JF1 / 1e3:.3f} N m, K {K_WIN[0]}-{K_WIN[1]}) lies inside the FE-anchored "
                 f"thread maximum {fx['F_max_for_MS_y_0_N']} N (MS_y 0, {fx['governing_state']} {fx['N_from']}, THE ROW A_n 67.93); at the "
                 f"3750 N cap MS_y = {cap_rows[cap_min]:+.3f} ({cap_min}) < 0.05: FLAG (lead F1); MS_y >= 0.05 would need "
                 f"{fx['F_max_for_MS_y_0.05_N']} N")}


# ---- F: contingency fits on K_js5: the relax v7 gap sweep RE-RUN at the band (seat family; seat and ring coincide on envelope v3)
def gap_cap_band(scr, ksh, kb, c):
    seated = lambda g: all(x["heads_seated_both_firings"] for x in R.run_grid({f"g{g:.4f}": g}, BAND, ksh, kb, c, scr).values())
    grid = [round(0.040 + 0.0025 * k, 4) for k in range(0, 33)]
    sweep = {g: seated(g) for g in grid}
    below = {round(0.0025 * k, 4): seated(0.0025 * k) for k in range(0, 16)}
    return {"sweep_0.040_0.120": sweep, "below_0.040_info": below,
            "any_gap_0.040_to_0.120_seats_all": any(sweep.values()), "any_gap_0_to_0.0375_seats_all": any(below.values())}


FB = {}
for end, (scr, ksh, kb, c) in END.items():
    FB[f"{end}|seat"] = gap_cap_band(scr, ksh, kb, c)
sf = rel["select_fit_gap_cap_IN718"]
F = {"at_band_2058_3750": FB,
     "from_relax_v7_at_2250_4096_info": {k: {"g_cap_mm": v["g_cap_mm"], "note": v.get("note"),
                                             "any_gap_0_to_0.0375_seats_all": any(v["below_0.040_info"].values()),
                                             "any_gap_0.040_to_0.120_seats_all": any(v["sweep_0.040_0.120"].values())} for k, v in sf.items()},
     "H7h6_H7g6": ("the contingency fits (radial 0-0.0245 / 0.005-0.0295) lie inside the 0-0.0375 sweep: "
                   + ("no gap seats all 24 at either k_b end at the 2058-3750 N band either" if not any(v["any_gap_0_to_0.0375_seats_all"] or v["any_gap_0.040_to_0.120_seats_all"] for v in FB.values())
                      else "SOME GAP SEATS ALL 24 at the 2058-3750 N band (see at_band_2058_3750)")
                   + ", so a tighter fit does not remove the slack on K_js5 (no spring)"),
     "gland_1_and_assembly": "jfwd_fit v1 gland-1 / assembly rows depend on the clearance only, not on K or the preload: they stand as found for a contingency fit"}

# ---- K_js4 record
K4 = {"jfwd_embed_v352_v1.json": sha(EMB4J), "jfwd_fit_v352_v1.json": sha(FIT4J),
      "k_sh_js4_N_mm": emb4["stiffness_js4_consistent"]["k_sh_N_mm_from_js4"], "k_b_js4_calibrated_N_mm": emb4["stiffness_js4_consistent"]["k_b_calibrated_N_mm"],
      "status": "AS FOUND, information only (239 (10)); superseded by K_js5 (relax v7) and the FE-anchored rows v7"}

# ---- the stop test (lead F1: 'If any turns negative, stop and tell me')
gov_A = {k: v for k, v in A.items() if k.split("|")[1] in GAPS_DRAW and k.split("|")[2] in GOV}
a_min = {end: min((v for k, v in gov_A.items() if k.startswith(end + "|") and k.split("|")[2] == "J-F1_min_2058"),
                  key=lambda v: v["F_after_embedding_signed_N"]) for end in END}
a_min_key = {end: min((k for k in gov_A if k.startswith(end + "|") and k.split("|")[2] == "J-F1_min_2058"),
                      key=lambda k: gov_A[k]["F_after_embedding_signed_N"]) for end in END}
v1_a = {end: min((v for k, v in v1["A_cold_embedding"].items() if k.startswith(end + "|") and k.split("|")[1] in GAPS_DRAW and k.split("|")[2] == "J-F1_min_2250"),
                 key=lambda v: v["F_after_embedding_N"])["F_after_embedding_N"] for end in END}
turned = []
for k, v in gov_A.items():
    if v["fit_after"] == "SLACK" or v["F_after_embedding_signed_N"] <= 0.0:
        turned.append(f"A {k}: cold after embedding {v['F_after_embedding_signed_N']} N (SLACK)")
for end in END:
    if C24[end]["cold_end_F_S_min_N_at_J_F1_min"] <= 0:
        turned.append(f"C {end}: cold end after firing 2 at 2058 N {C24[end]['cold_end_F_S_min_N_at_J_F1_min']} N")
    if C24[end]["installed_cold_after_embedding_min_N_at_J_F1_min"] <= 0:
        turned.append(f"C {end}: installed cold after embedding at 2058 N {C24[end]['installed_cold_after_embedding_min_N_at_J_F1_min']} N")
known_neg = {end: {"F_S_min_N": C24[end]["F_S_min_N"], "n_unseated_of_24": C24[end]["n_unseated"],
                   "relax_v7_at_2250_4096": C24[end]["relax_v7_at_2250_4096_info"]["F_S_min_N"]} for end in END}
b_max = {end: max((v for k, v in B.items() if k.startswith(end + "|") and k.endswith("|3750")), key=lambda v: v["F_S_max_N"]) for end in END}
slack_cold = sorted(k for k, v in A.items() if k.split("|")[1] in GAPS_INFO and k.split("|")[2] in GOV and v["fit_after"] == "SLACK")
_n_per_gap = 2 * len(GOV) * len(R.EMB)
slack_cold_txt = "; ".join(f"{gn.replace('_info', '')} (gap {GAPS_INFO[gn]:g}) {sum(1 for k in slack_cold if k.split('|')[1] == gn)} of {_n_per_gap} rows"
                           for gn in GAPS_INFO if any(k.split("|")[1] == gn for k in slack_cold)) or "none"
stmt = (f"On K_js5 (k_sh {END['lo'][1]:.0f} N/mm), IN718 flight screw, NO SPRING, at the J-F1 band capped at 3750 N ({T_JF1 / 1e3:.3f} N m, "
        f"{F_MIN:.1f}-{F_CAP:.0f} N): cold after embedding every drawing gap keeps the head seated (2057.6 N, sensitivity 21 um: minimum "
        f"{a_min['lo']['F_after_embedding_signed_N']:.0f} / {a_min['hi']['F_after_embedding_signed_N']:.0f} N at k_b lo / hi, fit "
        f"{a_min['lo']['fit_after']} / {a_min['hi']['fit_after']}; v1 at 2250 N: {v1_a['lo']} / {v1_a['hi']} N); the 24-case grid at 2057.6 / 3750 N "
        f"reaches the same in-service minimum as relax v7 at 2250 / 4096 N ({C24['lo']['F_S_min_N']} / {C24['hi']['F_S_min_N']} N, "
        f"{C24['lo']['n_unseated']} / {C24['hi']['n_unseated']} of 24 unseated: the KNOWN no-spring negative of 239 (3), unchanged; route (i) "
        f"answers it, jfwd_spring v4); its cold end after firing 2 at 2057.6 N is {C24['lo']['cold_end_F_S_min_N_at_J_F1_min']} / "
        f"{C24['hi']['cold_end_F_S_min_N_at_J_F1_min']} N; the first firing at 3750 N without embedding credit reaches {b_max['lo']['F_S_max_N']} / "
        f"{b_max['hi']['F_S_max_N']} N in the 1-DOF model; the torque window without slack is "
        + ("EMPTY" if not any(window.values()) else f"{window}")
        + f" over {F_SWEEP[0]:.0f}-{F_SWEEP[-1]:.0f} N (F_S min "
        + ("identical at every preload" if all(fsmin_same.values()) else "varies with the preload")
        + f"); the 3750 N cap sits inside the FE-anchored thread maximum {E['F_max_for_MS_y_0_N']} N (THE ROW A_n 67.93; MS_y "
          f"{E['MS_y_at_cap_min']['MS_y']:+.3f} at the cap, FLAG); the contingency fits do not remove the slack; at their minimum gaps the head "
          f"goes SLACK cold after embedding ({slack_cold_txt}; information fits, not drawn).  Turned negative at the new minimum (drawing gaps): "
        + ("NONE" if not turned else "; ".join(turned)) + ".")

out = {"id": "jfwd_embed_fit_js5_v352", "version": "v2", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "status": "CALC on SIM temperatures; DERIVED unless tagged; negatives SHOWN AS FOUND; not physical approval",
       "inputs": {"relax_module": {"path": str(RELAX_PY), "sha256_16": sha(RELAX_PY)}, "relax_v7": {"path": str(RELAXJ), "sha256_16": sha(RELAXJ)},
                  "rows_v7": {"path": str(ROWSJ), "sha256_16": sha(ROWSJ)}, "js5_v1": {"path": str(V1J), "sha256_16": sha(V1J)},
                  "fea3d_soak_envelope": {"sha256_16": ENV_SHA16},
                  "screw_key": INK, "k_b_N_mm": {e: round(v[2]) for e, v in END.items()}, "k_sh_N_mm": round(END["lo"][1]), "k_c_N_mm": round(R.K_C),
                  "c_seat_MPa_per_N": {e: round(v[3], 5) for e, v in END.items()}, "f_Z_um": {k: round(v * 1e3, 1) for k, v in R.EMB.items()},
                  "gaps_drawing_mm": GAPS_DRAW, "gaps_information_mm": GAPS_INFO},
       "J_F1_band": {"cap_N": F_CAP, "min_N": round(F_MIN, 1), "torque_Nmm": round(T_JF1, 1), "K_window": list(K_WIN), "nominal_K0.20_N": round(F_NOM, 1),
                     "rule": "lead 17:55:55Z F1: J-F1 sets the flight-lot torque so the lot's K_min gives <= 3750 N; the minimum is the lot's K_max "
                             "result (today's K window: 2057.6 N, = 2250 x 3750 / 4096 within rounding)",
                     "columns": {"governing": list(GOV), "information": [k for k in INST_A if k not in GOV]}},
       "A_cold_embedding": A, "B_first_firing_3750_no_embedding_model_info": B,
       "C_in_service_24_case_at_band": {"by_end": C24, "by_gap_and_embedding": C},
       "C_relax_v7_at_2250_4096_info": v1["C_in_service_minimum_after_embedding_relax_v7"],
       "D_torque_window_without_slack": {"rows": D, "window_N_by_end": window, "F_S_min_identical_over_preloads": fsmin_same},
       "A_cold_embedding_slack_at_contingency_gaps_info": {"rows": slack_cold, "summary": slack_cold_txt, "rows_per_gap": _n_per_gap},
       "E_J_F1_maximum_rows_v7": E, "F_contingency_fits_K_js5": F, "K_js4_record": K4,
       "stop_test_lead_F1": {"turned_negative_at_new_minimum": turned, "verdict": "NONE TURNED NEGATIVE" if not turned else "STOP: TELL THE LEAD",
                             "known_no_spring_negative_unchanged_239_3": known_neg,
                             "a_min_case": a_min_key},
       "statement": stmt, "t_run_s": round(time.time() - T0, 1)}
s = json.dumps(out, indent=1, default=float)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16], out["t_run_s"])
print(stmt)
print("STOP-TEST:", out["stop_test_lead_F1"]["verdict"], turned)
for end in END:
    print("C24", end, {k: C24[end][k] for k in ("all_seated", "n_unseated", "F_S_min_N", "min_case", "installed_cold_after_embedding_min_N_at_J_F1_min",
                                                 "cold_end_F_S_min_N_at_J_F1_min", "max_wall_set_um", "fibre_over_Rp_max", "screw_shakedown_min_MS")})
for k, v in A.items():
    if k.split("|")[1] in GAPS_DRAW and k.split("|")[2] in GOV:
        print("A", k, v["F_after_embedding_signed_N"], v["fit_after"], v["installed_fit"], v["loss_N"])
for k, v in D.items():
    print("D", k, {kk: v[kk] for kk in ("all_seated", "n_unseated_of_12", "F_S_min_N", "cold_end_F_S_min_N", "installed_cold_after_embedding_min_N", "max_wall_set_um")})
for k, v in FB.items():
    print("F", k, v["any_gap_0.040_to_0.120_seats_all"], v["any_gap_0_to_0.0375_seats_all"])
print("E", E["verdict"])
