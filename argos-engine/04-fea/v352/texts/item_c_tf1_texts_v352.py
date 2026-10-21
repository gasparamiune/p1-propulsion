"""Item C texts (O-ring passage over the J-FWD holes; v3.5.2 rev 5 + founder procedure) and the T-F1 founder action text, as ruled:
item C 239 (13) (lead 09:45Z), amended 10:08Z (bore-side break R0.1-R0.2), callout ruled 10:15Z, gland basis 10:10Z (240 (5), (6));
T-F1 239 (12) (lead 09:59Z: two routes, no recalled or estimated values, (d) OPEN per abort value with the time above 150 C per firing).
Mechanical, 2026-10-20, v3 (v2 script kept as item_c_tf1_texts_v352_v2.py, v1 as item_c_tf1_texts_v352_v1.py).  Text only; the numbers come
from tf1_exposure_v352_v1.json [SIM thermal; ASSUMED TB surrogate as tagged], engmat AL6061-T6 (10,000 h basis, LITERATURE) and, for v3,
the accepted J-FWD route (i) files (rows v7, spring v4, head fillet v1, tap wall v1, K_js5 v2, screw LCF v2; sha asserted), hardware_v352
v1.7 and the rev-5 drawing texts and GSE lines (rev5_drawing_texts_v352_v1.json).
v2 (lead 14:34Z): C1 (a)-(f), C2, C3, C4, C5, C6, C7 and T-F1 ACCEPTED as written in v1 (T-F1 as a GATE before the first static fire);
C1 (g) Option A ADOPTED; C1 (h) ADOPTED; C6 (2) carries the pins; C6 (3) OPEN until the slack-fix ruling.
v3 (lead 18:36:37Z item 5, 'the drawing texts (+/-0.25 deg index pin, C4 shoulder-screw registration, J-F1 torque cap at 3750 N, the
Prescale item, single-use screws with the fillet in the inspection)'; rulings 16:53Z R2 / R3 / R4, 17:55:55Z F1-F5, 18:36:37Z):
C1 (g) / (h) restated for route (i) (the spring footprint on the flat, da 5.55-5.80 drawn, F3) and the accepted datums (A = 57.25 H8 bore
axis, B = TC-01 forward end face; the v2 datum FLAG closed); C4 rewritten (hole and tap gauging, the gap-gauge head setting of rev 5 in
place of 'until seated', the F2 registration with ENG-TC-13, the J-F1 lot torque M-T1J with the 3750 N cap and the Prescale item as a gate,
the single-use rule); C6 (2) / (3) the single-use founder rule with the head-to-shank fillet in the removed-screw inspection (LEAD ADDITION
18:36:37Z) and the C6 OPEN status; new C3b (ENG-TC-13 GSE) and C8 (the drawing texts: TC-01 / TC-02 rev 5, ENG-HW-101-IN718, HW-170,
M-T1J, J-F1) with the lead's five items located and asserted.  C1 (a)-(f), C2, C3, C5, C7 and T-F1 are unchanged from v2.  Nothing here
changes CAD.  Writes v352/texts/item_c_tf1_texts_v352_v3.json.
v4 (2026-10-21, lead 2026-10-21T05:50:45Z re-map brief R1-R12; v3 218df5556b279878 / json 7d857240da06f4eb kept as
item_c_tf1_texts_v352_v3.py): the J-FWD inputs move to the re-map files on FEA3D-2's FINAL envelope v6 43a5d78b67c615fc and the cD
input record 5a41c8d74897bdda (rows v8, spring v5, head fillet v2, K_js5 v3, screw LCF v3; the tap wall stays v1, R11), with the band
record jfwd_pq_band_v352_v1.json (R2) and the J-F1b / LOCTITE record jf1b_loctite_v352_v1.json (248 (7)).  T-F1 is RESTATED on the
A 175 rows with the A 150 rows beside (R9; tf1_exposure_v352_v2.json; numbers unchanged).  C1 (g) / (h) cite rows v8 (the footprint
block is unchanged); C4 steps 1 / 7 / 9, C6 (3) / (4) and the C8 open items carry the 248 (7) rulings (HW-170 single-use, the spring
orientation, J-F1b, the post-abort rule, LOCTITE 243 at TB_a150) and the band; new C9 holds the founder texts (R10: the orientation
drawing note and assembly step, HW-170 single-use, J-F1b, the post-abort joint replacement rule, the stand T0 rule as a cross-reference;
R2: the TC-02 select-fit band text; R8: the CAD basis).  C1 (a)-(f), C2, C3, C3b, C5, C7 and the geometry checks are unchanged from v3.
Nothing here changes CAD: the parts / BOM / hardware strings are not edited (the drawing texts below supersede them where they differ,
until the lead rules a data update).  C9 (6) and its drawing-text twin are RESTATED to the lead ruling R2-B (2026-10-21T07:37:34Z;
quoted verbatim, ASCII as written: SELECT FIT to the measured TC-01 bore, flag-free band [0.040, 0.0631] mm; the data strings stay
unedited in v3.5.2, superseded by the drawing note); C4 step 1, C8 open_items[8] and C9 (5) follow it.  Writes
v352/texts/item_c_tf1_texts_v352_v4.json and the drawing-text set
v352/texts/jfwd_drawing_texts_v352_v1.json (for 03-cad/v3.5.2/texts/)."""
import json, hashlib, math, sys
from pathlib import Path
import numpy as np

T = Path("/home/claude/work/mechanical/v352/texts")
EXP = T / "tf1_exposure_v352_v2.json"
OUT = T / "item_c_tf1_texts_v352_v4.json"
OUT_DT = T / "jfwd_drawing_texts_v352_v1.json"
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat
AL = engmat.MATERIALS["AL6061-T6"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


J = Path("/home/claude/work/mechanical/v352/jfwd")
D3 = Path("/home/claude/work/mechanical/v352/engine/03-cad")
INP = {"tf1_exposure": (EXP, "d60f5da3ce3e5cb7"), "tf1_exposure_v1": (T / "tf1_exposure_v352_v1.json", "d23e72f089cca33a"),
       "rows_v8": (J / "jfwd_in718_rows_v352_v8.json", "af072cc2e70711ca"), "spring_v5": (J / "jfwd_spring_v352_v5.json", "7d2e27d74f202418"),
       "head_fillet_v2": (J / "jfwd_head_fillet_v352_v2.json", "704f55ecb7a18dea"), "tap_wall_v1": (J / "jfwd_tapwall_v352_v1.json", "bcb21243d57af998"),
       "K_js5_v3": (J / "jfwd_embed_fit_js5_v352_v3.json", "6ab5d369ef8594ce"), "screw_lcf_v3": (J / "jfwd_screw_lcf_v352_v3.json", "b6ff0ea0f731c7dc"),
       "pq_band_v1": (J / "jfwd_pq_band_v352_v1.json", "1ba3147b42edfeed"), "jf1b_loctite_v1": (J / "jf1b_loctite_v352_v1.json", "2ba9d10745f3f651"),
       "hardware_v1.7": (D3 / "src/data/hardware_v352.json", "c2c7b13d3a0086e3"),
       "rev5_drawing_texts_v1": (T / "rev5_drawing_texts_v352_v1.json", "3eed41f8c4f8a64f"),
       "item_c_tf1_texts_v3": (T / "item_c_tf1_texts_v352_v3.json", "7d857240da06f4eb")}
X = {}
for k, (p, s16) in INP.items():
    assert sha(p) == s16, (k, p, sha(p))
    X[k] = json.loads(Path(p).read_text())
R8, SP5, HF2, TW1, JS3, LC3, HW, DT = (X[k] for k in ("rows_v8", "spring_v5", "head_fillet_v2", "tap_wall_v1", "K_js5_v3", "screw_lcf_v3",
                                                      "hardware_v1.7", "rev5_drawing_texts_v1"))
BD, JL, V3 = X["pq_band_v1"], X["jf1b_loctite_v1"], X["item_c_tf1_texts_v3"]
assert (R8["version"], SP5["version"], HF2["version"], JS3["version"], LC3["version"], BD["version"]) == ("v8", "v5", "v2", "v3", "v3", "v1")
assert HW["version"] == "v1.7"


def al(k, Tc):
    return float(np.interp(Tc, AL[k]["T_C"], AL[k]["v"])) / 1e6


E = X["tf1_exposure"]
B = E["bounds"]
assert E["version"] == "v2" and B == X["tf1_exposure_v1"]["bounds"]
R9 = E["T-F1_exposure_basis_R9"]
lo, hi = B["GVLO"]["parts"], B["GVHI"]["parts"]
LIFE = 50


def pair(f):
    return f"{f(lo)} | {f(hi)}"


# ------------------------------------------------------------------------------------------------ geometry checks behind the C texts
R_BORE = 57.25 / 2.0
sag = R_BORE - math.sqrt(R_BORE ** 2 - 2.75 ** 2)                    # contour depth over the d5.5 plug face
wall_min, wall_max = 31.313 - (57.25 + 0.046) / 2.0, 31.333 - 57.25 / 2.0  # r_flat 31.313 +0.020/0 (rev 5 rule), bore 57.25 H8
key_err = {f"{a} deg": round(sag * math.sin(math.radians(a)) ** 2, 4) for a in (5, 10, 15)}
geo = {"contour_sagitta_over_d5.5_mm": round(sag, 4), "wall_at_hole_drawn_range_mm": [round(wall_min, 3), round(wall_max, 3)],
       "fixed_length_window_for_0_to_0.05_recess_mm": [round(wall_max - 0.05, 3), round(wall_min, 3)],
       "keying_error_at_plug_edge_mm": key_err, "lead_in_clearance_to_hole_row_mm": round(12.0 - 2.75 - 3.5, 2),
       "note": ("CALC: a cylindrical contour rotated by theta about the plug axis misses the bore by sag x sin^2(theta) at the plug edge; "
                "one fixed plug length cannot hold 0-0.05 below the bore over the drawn wall range (window "
                f"{wall_max - 0.05:.3f}-{wall_min:.3f} mm), hence plugs finished to the measured wall")}

# ------------------------------------------------------------------------------------------------ v3 values read from the accepted files
JF1 = R8["J_F1"]
F_CAP, F_MIN, T_LOT, KW = JF1["maximum_N"], JF1["minimum_N_today_K_window"], JF1["torque_Nm_today_K_window"], JF1["K_window"]
assert (F_CAP, F_MIN, T_LOT, KW) == (3750.0, 2057.6, 2.747, [0.1465, 0.267])
FP = R8["route_i_spring_footprint"]
A_REG, A_FF = FP["areas_mm2"]["registered_stack_0.4865_F2"], FP["areas_mm2"]["full_float_0.557"]
assert (A_REG, A_FF) == (46.06, 45.352) and FP["quoted_flat_bearing_basis"] == "registered_stack_0.4865_F2"
F3 = SP5["fillet"]["F3_adopted"]
assert F3["da_mm"] == [5.55, 5.8]
GEOc = SP5["geometry_length_tip_engagement"]["cases"]
GA, GB = GEOc["spring A t 0.5: 10.7 +/-0.1"], GEOc["spring B t 0.4: 10.6 +/-0.1"]
assert (GA["L_e_gap_bound_mm"], GB["L_e_gap_bound_mm"]) == (7.294, 7.294)
TWW = TW1["walls_mm"]
assert (TWW["ruled_+/-0.25deg_net_GOVERNING"], TWW["+/-0.5deg_net_info"]) == (1.6355, 1.5415)
HG = HF2["governing_and_thread_root_comparison"]["3750"]
LCFt = (HG["i_firing"]["thread_root_N_allow"], HG["i_firing"]["thread_root_MS"], HG["ii_assembly_from_zero"]["thread_root_N_allow"],
        HG["ii_assembly_from_zero"]["thread_root_MS"])
LCFf = (HG["i_firing"]["fillet_N_allow"], HG["i_firing"]["fillet_MS"], HG["ii_assembly_from_zero"]["fillet_N_allow"],
        HG["ii_assembly_from_zero"]["fillet_MS"])
assert LCFt == (5.6, -0.888, 0.6, -0.988) and LCFf == (1092.0, 20.84, 29.3, -0.414)
_g = LC3["governing"]
assert (_g["i_firing|Kf3.0|worst_of_histories|3750"]["N_allow"], _g["i_firing|Kf3.0|worst_of_histories|3750"]["MS_cycles_vs_50"],
        _g["ii_assembly_from_zero|Kf3.0|worst_of_histories|3750"]["N_allow"], _g["ii_assembly_from_zero|Kf3.0|worst_of_histories|3750"]["MS_cycles_vs_50"]) == LCFt
K22 = (_g["i_firing|Kf2.2|worst_of_histories|3750"]["N_allow"], _g["i_firing|Kf2.2|worst_of_histories|3750"]["MS_cycles_vs_50"])
assert K22 == (26.9, -0.462)
_gi = LC3["governing_info_M_x_ratio"]["i_firing|Kf3.0|3750"]
MXI = (_gi["N_allow"], _gi["MS_cycles_vs_50"], float(_gi["case"].split("info_Mx")[1]))
assert MXI == (1.3, -0.974, 1.4764)
# v4: the band (R2), J-F1b / LOCTITE (248 (7)), the spring numbers for the orientation note
BR = BD["RESULT"]
assert BR["band_mm_radial"] == [0.04, 0.0686] and BR["closes_seat_line"] and BR["lead_CALC_check"]["computed_[0.040,0.0684]_window_mm"] == 0.0108
OPT_A = BR["drawn_options"]["57.20 -0.030/-0.040 (57.160-57.170)"]
OPT_E = BR["drawn_options"]["57.20 -0.030/-0.041 (57.159-57.170)"]
assert (OPT_A["MS_min_3750_criterion"]["MS"], OPT_A["MS_min_4096_info"]["MS"], OPT_E["MS_min_3750_criterion"]["MS"], OPT_E["MS_min_4096_info"]["MS"]) == (0.0054, 0.0035, 0.001, -0.0008)
SEAT8 = {st: R8["states"][st]["rows"]["3750"]["seat_line_d6p051_z0_PQ"] for st in ("SOAK70", "SOAK", "SOAK52")}
assert {st: (v["MS_PQ_2Fty"], v["from"]) for st, v in SEAT8.items()} == {"SOAK70": (-0.059, "(b2)"), "SOAK": (-0.075, "(b2) rep"), "SOAK52": (-0.033, "(b1)")}
T0I = BR["stand_T0_24C_info"]
# ---- lead ruling R2-B (2026-10-21T07:37:34Z), quoted verbatim (ASCII as written); C9 (6), C4 step 1, C8 open_items[8], C9 (5) follow it
R2B = ("LEAD RULING R2-B (2026-10-21T07:37:34Z): the ENG-TC-02 plug OD is a SELECT FIT to its own measured TC-01 bore, "
       "flag-free band: radial gap g in [0.040, 0.0631] mm, i.e. D_meas - 0.1262 <= OD <= D_meas - 0.080 mm (window 0.0462 mm "
       "on the diameter, less 2U, U the expanded (k=2) uncertainty of the bore and OD measurements, TO-DEFINE); bore and OD "
       "measured at 20 +/- 1 C and recorded with the paired TC-01 / TC-02 serials; the TC-02 OD is finished last, from a blank "
       "with finishing stock, to the measured bore. Basis: jfwd_pq_band_v352_v1.json 1ba3147b42edfeed [CALC on SIM]: seat-line "
       "MS >= +0.05 at 3750 N at the band edge, and positive in the ASSUMED +4 K stand T0 24 C information case (MS 0 there at "
       "g 0.0638). Option A (drawn 57.20 -0.030/-0.040, MS +0.005, FLAG) is not adopted (information only). The parts / BOM / "
       "hardware data strings stay unedited in v3.5.2 and are superseded by this drawing note. The seat-line P+Q stays NOT "
       "shown mesh-converged (R4 MF note); this is CALC on SIM, not physical approval.")
assert R2B.isascii() and "D_meas - 0.1262 <= OD <= D_meas - 0.080" in R2B and sha(J / "jfwd_pq_band_v352_v1.json") in R2B
G_R2B = BR["g_for_MS_+0.05_3750_mm"]
assert G_R2B == 0.0631 and f"[0.040, {G_R2B}] mm" in R2B and f"D_meas - {2 * G_R2B:.4f} <= OD <= D_meas - {2 * 0.040:.3f} mm" in R2B
assert f"(window {2 * (G_R2B - 0.040):.4f} mm on the diameter" in R2B and f"MS 0 there at g {T0I['g_at_MS0_+4K_min_mm']:.4f})" in R2B
assert f"MS {OPT_A['MS_min_3750_criterion']['MS']:+.3f}, FLAG" in R2B
assert "D_meas - 0.1262 <= OD <= D_meas - 0.080 (window 0.0462 mm)" in BR["select_fit"]["flag_free_variant"]


def _edge(kb, f):
    return min((BD["per_key"][f"{kb}|{fam}|{f}"]["per_state"][st]["MS_at_gap_new_points"][str(G_R2B)], st)
               for fam in ("seat", "ring") for st in ("SOAK70", "SOAK", "SOAK52"))


E631 = {(kb, f): _edge(kb, f) for kb in ("hi", "lo") for f in (3750, 4096)}
assert E631[("hi", 3750)][0] >= 0.05 and E631[("lo", 3750)][0] >= 0.05
PS_HI = BD["per_key"]["hi|seat|3750"]["per_state"]


def _p4(st, g):                   # ASSUMED +4 K, FE P+Q unchanged: (1 + MS) x Fty(T_line + 4 K) / Fty(T_line) - 1 (band-file values)
    t = T0I["per_state"][st]
    return (1 + PS_HI[st]["MS_at_gap_new_points"][g]) * t["Fty_at_T_line_+4K_MPa"] / t["Fty_at_T_line_MPa"] - 1


assert all(abs(_p4(st, "0.0686") - T0I["per_state"][st]["MS_at_band_edge_+4K"]) < 1.5e-4 for st in PS_HI)   # reproduces the band file
P4 = min((round(_p4(st, str(G_R2B)), 4), st) for st in PS_HI)
assert P4[0] > 0
G0 = {kb: BD["per_key"][f"{kb}|seat|3750"]["g_max_at_MS0_mm"] for kb in ("hi", "lo")}
assert G0 == {"hi": 0.06862, "lo": 0.06892} and all(BD["per_key"][f"{kb}|ring|3750"]["g_max_at_MS0_mm"] == G0[kb] for kb in G0)
JB, LT = JL["J_F1b"], JL["LOCTITE_243_tap_zone_TB_a150"]
assert (JB["peak_C"], JB["T_zone_max_C"], JB["governing_state"]) == (175.0, 160.29, "SOAK70")
assert (LT["GVLO"]["TB_a150_tap_zone_max_C"], LT["GVHI"]["TB_a150_tap_zone_max_C"], LT["GVLO"]["shifted_history_ASSUMED_info"]["tap_zone_max_C"],
        LT["GVHI"]["shifted_history_ASSUMED_info"]["tap_zone_max_C"]) == (128.0, 116.0, 148.7, 146.9)
PA = (LT["GVLO"]["shifted_history_ASSUMED_info"]["jfwd_TC01_zone_max_C"], LT["GVHI"]["shifted_history_ASSUMED_info"]["jfwd_TC01_zone_max_C"])
assert PA == (201.4, 164.0)
SPA = SP5["springs"]["A_DIN2093_A10_17-7PH"]
assert SPA["De_Di_t_l0_h0_mm"][:3] == [10.0, 5.2, 0.5] and SP5["runs"]["A_DIN2093_A10_17-7PH|R0.00|lo|seat"]["F_flat_derated_N"] == 360.0
assert SP5["runs"]["B_Lesjofors_7909_1.4310|R0.00|lo|seat"]["F_flat_derated_N"] == 206.5
assert not HG["i_firing"]["fillet_governs"] and not HG["ii_assembly_from_zero"]["fillet_governs"]
H101 = next(L for L in HW["lines"] if L["id"] == "HW-101")
H170 = next(L for L in HW["lines"] if L["id"] == "HW-170")
MT1J = HW["rules"]["tightening_methods"]["M-T1J"]
GSE = {L["pn"]: L for L in DT["gse_tool_lines"]}
assert set(GSE) == {"ENG-TC-12", "ENG-TC-13"}

C = {}
C["C1_TC01_drawing_callout_rev5"] = (
    "TC-01 drawing, 10x d5.5 J-FWD holes (rev 5): "
    "(a) bore-side edge: break R0.1-R0.2, blended and polished, burr-free, no chamfer or step; R0.2 is a HARD MAXIMUM: a hole whose break "
    "exceeds R0.2 after rework is rejected or re-assessed, never accepted on sight. "
    "(b) flat-side (spot-face) edge of the hole: break 0.1 max. "
    "(c) spot-face flat-to-OD edge: break 0.1 max. "
    "(d) deburr after match-drilling with TC-02 and after any rework, before anodise. "
    "(e) 100 % inspection at 10x before assembly: no burr, nick or raised metal at the hole edges or on the bore within 3 mm of a hole. "
    "(f) drawing note: bearing length = wall at the hole minus both breaks (2.665 - 0.2 - 0.1 = 2.365 mm at the drawing-limit wall; the "
    "FA1S hole bearing is quoted at this length, +0.005 / +0.239, CHANGELOG 240 (5)). "
    "(g) hole size (ADOPTED, lead 14:34Z, Option A): d5.5 +0.12/0 (H12). ENG-HW-101-IN718 in-service gauge pins GO 5.50 / NO-GO 5.62; the "
    "line-231 post-FA-1 hole check uses the 5.62 pin. Route (i) (lead 16:53Z R2): the drawn maximum 5.62 plus the 0.1 flat-side break "
    "each side (5.82) is the inner boundary of the HW-170 disc-spring footprint on the flat (rows v8 route_i_spring_footprint, unchanged from rows v7: spring De "
    f"9.85 / Di 5.32 at its limits, {A_REG} mm2 at the registered stack 0.4865 (lead 17:55:55Z F2), {A_FF} mm2 at full float 0.557); the "
    f"head bears on the spring, with da {F3['da_mm'][0]:.2f}-{F3['da_mm'][1]:.2f} stated on the ENG-HW-101-IN718 drawing (F3; it replaces the "
    "v2 'da 5.7 TO-VERIFY'); the v2 basis (head on the flat, float 0.397, rows v5) is superseded. "
    "(h) hole position (ADOPTED, lead 14:34Z; datums as checked in the rev-5 CAD and ACCEPTED 17:55:55Z): datum A = the axis of the "
    "forward seal-land bore 57.25 H8; datum B = the TC-01 forward end face, from which the hole row is dimensioned (12.000 BASIC from B); "
    "each hole axis 0.10 dia to A|B; the d11.2 spot face (rev-5 cutter, P(i)-1) coaxial with its hole within 0.10 dia. The rows v8 "
    "flat-bearing row takes the registered stack (tangential 0.4865, F2; axial 0.3705, F4) with the OD 63.5 h9 and its 0.04 runout to A. "
    "The v2 drawing-consistency FLAG (A had been the end face) is CLOSED by these datums: r_flat 31.313 +0.020/0 from A and the OD runout "
    "0.04 to A read as radial quantities from the bore axis.")
C["C2_bore_lead_in_rev5"] = (
    "TC-01 forward bore lead-in 15 deg x 3.5 (x 0.938 mm), replacing 15 deg x 3.0 (x 0.804, which missed Parker PTD5705-EN Fig. 2.24 "
    f"x > y by 0.0005 mm at the worst stack); it ends {geo['lead_in_clearance_to_hole_row_mm']:.2f} mm clear of the hole row (holes 12 mm "
    "from the end, r 2.75).")
C["C3_fitting_aid_GSE"] = (
    "ENG-TC-12 J-FWD hole plug set (GSE, not flight mass; TO-DRAW; TO-QUOTE, or made from POM rod): 10 plugs and 1 retaining band. "
    "Plug: POM, shank d5.5 -0.02/-0.05; a head shoulder seats on the spot face and sets the depth positively; the inner end is contoured "
    f"R28.6 (the 57.25 bore; contour depth {sag:.3f} mm over the d5.5 face) with the contour axis parallel to the bore axis, keyed by a tab "
    "on the head in a slot of the band (+/-15 deg is enough: the contour error at the plug edge is "
    f"{key_err['15 deg']:.3f} mm at 15 deg [CALC]). "
    "Length from the shoulder to the contour centre = the wall measured at that hole (flat to bore along the hole axis) minus "
    "0.025 +/- 0.010, so the end sits 0.015-0.035 below the bore surface (inside the ruled 0 to 0.05; never proud); plugs numbered to "
    f"their holes. Reason: the drawn wall at the hole spans {wall_min:.3f}-{wall_max:.3f} mm, wider than the 0.05 window, so one fixed "
    "length cannot meet it at every stack [CALC]. Band: a split ring over the ten heads on the TC-01 OD that holds each plug against the "
    "passing ring's outward push. The plugs come out only after both rings have passed the hole row. "
    "BOM line (rev 5): 'ENG-TC-12 | J-FWD hole plug set, 10 plugs + band, O-ring passage aid | GSE (not flight) | POM | qty 1 set | "
    "TO-DRAW / TO-QUOTE | used at every TC-02 insertion'.")
C["C3b_registration_shoulder_screws_GSE"] = (
    "ENG-TC-13 J-FWD registration shoulder screw pair (GSE, not flight mass; TO-DRAW / TO-QUOTE; lead 17:55:55Z F2, ADOPTED into C4): "
    "two shoulder screws, the shoulder selected to the pin-gauged sizes of their TC-01 holes (d5.5 H12; pins GO 5.50 / NO-GO 5.62), M5 "
    "into the TC-02 taps; they go into two opposite holes before any flight screw and come out last, each replaced by a flight screw "
    "(C4 steps 6 and 8); never left in the engine; shoulder length, material and the shoulder size steps TO-DRAW. BOM line (v3.5.2 "
    f"BOM): '{GSE['ENG-TC-13']['pn']} | {GSE['ENG-TC-13']['name']} | {GSE['ENG-TC-13']['groups']} | {GSE['ENG-TC-13']['material']} | "
    f"qty {GSE['ENG-TC-13']['qty']} | {GSE['ENG-TC-13']['drawing']} / TO-QUOTE'.")
C["C4_assembly_step_founder_procedure"] = (
    "J-FWD build and every re-assembly (v3: route (i), lead 16:53Z R2 / R3, 17:55:55Z F1 / F2, 18:36:37Z; v4: the 248 (7) rulings and the "
    "lead 2026-10-21T05:50:45Z re-map R2 / R10): "
    "0. GATE: J-F1 complete on the flight lots (ENG-HW-101-IN718 screws, HW-170 springs, LOCTITE 243): it sets the lot torque T_lot and "
    "carries the spring items (K with the spring under the head, the spring flattening, the crack-on torque) and the Fuji Prescale "
    "footprint item (TO-VERIFY) (hardware_v352 v1.7 HW-101 test). "
    "1. inspect the hole edges and the bore per C1 (e); gauge the ten TC-01 holes with the pins GO 5.50 / NO-GO 5.62 and record each "
    "hole's size (ENG-TC-13 is selected to it; a hole that takes the 5.62 pin is rejected, C1 (g)); gauge the ten TC-02 taps M5-6H GO / "
    "NO-GO (cured locker removed by a thread chaser only, no re-tap); check the TC-02 plug OD against its select-fit pairing record to "
    "this TC-01 bore (C9 (6): bore and OD at 20 +/- 1 C, D_meas - 0.1262 <= OD <= D_meas - 0.080, less 2U); clean. "
    "2. fit the ten ENG-TC-12 plugs in their numbered holes from outside, contour aligned, band on. "
    "3. lubricate S01 and S02 with the selected lubricant (FKM- and N2O-compatible, TO-SELECT with a datasheet; oxygen-clean per the "
    "wetted-part rule); fit them into the TC-02 grooves with an even stretch over a cone, no twist (check the mould line). "
    "4. clock TC-02 to the match marks BEFORE the rings enter the lead-in, then push it in axially without rotation until the head "
    "shoulder stands 2.00 +/-0.02 from the TC-01 forward end face on the gap gauge (rev-5 TC-02 tap note, TO-CONFIRM; TC-02 does not seat "
    "axially on TC-01, lead 16:53Z R4; v2 read 'until seated'). "
    "5. remove the band and the plugs; look through each hole (10x loupe or borescope) for rubber debris or a cut ring; ANY debris: "
    "withdraw TC-02, replace both rings and repeat from step 1. "
    "6. REGISTRATION (lead 17:55:55Z F2): fit the two GSE shoulder screws ENG-TC-13 (not flight), selected to the pin-gauged sizes of "
    "their holes, into two opposite holes before any flight screw. "
    "7. fit the flight screws ONE AT A TIME into the other eight holes: a NEW ENG-HW-101-IN718 (M5 x 10.7 with spring A; M5 x 10.6 with "
    "spring B; never mixed in one joint) with a NEW HW-170 disc spring under the head, ORIENTED per C9 (1): concave (hollow) side DOWN on "
    "the TC-01 flat (outer edge on the flat), convex side UP to the head (inner edge toward the head), centred on the 5.15 h9 pilot, NEVER "
    "inverted; LOCTITE 243 (flight lot) on the screw thread only, never on the spring or the flat; tighten to the J-F1 LOT TORQUE by "
    f"method M-T1J (T_lot = {F_CAP:.0f} N x K_min(lot) x 5 mm, so that the lot's K_min gives a maximum preload of {F_CAP:.0f} N or less, "
    f"lead 17:55:55Z F1; today's K window {KW[0]}-{KW[1]}: {T_LOT:.3f} N m, minimum {F_MIN:.1f} N); record per hole: hole number and its "
    "pin size, screw and spring lot, torque, wrench (ID and calibration date). "
    "8. remove the two shoulder screws LAST and replace each with a flight screw per step 7, recorded. "
    "9. never re-torque a fitted screw; a screw removed for any reason is replaced by a new screw and a new spring (single-use, C6 (3)); "
    "removed springs are scrapped (HW-170 SINGLE-USE, C9 (2)); after any case-TC or TB-state abort the whole joint counts as used (C6 (4)); "
    "removed screws are bagged and labelled with their hole number for the C6 (3) inspection; then the proof / leak test.")
C["C5_record_why_not_moved"] = (
    "Parker Praedifa PTD5705-EN 2.5.2: a cross-drilled port shears the O-ring as it leaves the drilled area, and the first remedy is to "
    "reposition the holes; 2.5.6: bores 'must be removed or covered'. Moving the holes is not possible: S01 and S02 must sit between the "
    "chamber and the holes (dry holes), and TC-02 can only enter from the forward end. The internal chamfer (Fig. 2.26) and the balancing "
    "groove (Fig. 2.27) change the J-FWD wall and the plug fit contact and are NOT adopted. The fitting aid covers the holes, as 2.5.6 "
    "requires; the R0.1-R0.2 break is capped by the bearing length and the screw bending arm (an R0.4 + 0.1 break gives the FA1S hole bearing -0.070 at the nominal wall / -0.080 at the limit wall).")
C["C6_founder_action_list_related"] = (
    "(1) S01 and S02 are replaced after any FA-1-class event, together with the line-231 J-FWD inspection (lead 10:10Z rule). "
    "(2) Line-231 post-FA-1 inspection list: the ten J-FWD screws and their HW-170 disc springs replaced (new, single-use, (3)); the ten "
    "holes gauged for elongation and bearing set with the HW-101 pins GO 5.50 / NO-GO 5.62 (C1 (g)); a hole that takes the 5.62 pin is "
    "rejected; hole edges and the bore within 3 mm of a hole at 10x for nicks or raised metal; S01 / S02 replaced; the removed screws "
    "inspected per (3). "
    "(3) J-FWD screw life: SINGLE-USE founder rule until C6 closes (lead 16:53Z R3): the J-FWD screws are new at every assembly, never "
    "reused or re-torqued; removed screws are kept per hole and inspected at 10x plus dye penetrant at the thread root AND the "
    "head-to-shank fillet (LEAD ADDITION 18:36:37Z), as data. C6 is OPEN: the screw LCF at the thread root is a FOUND NEGATIVE "
    f"(183 (1)(c); jfwd_screw_lcf_v352_v3.json on rows v8, SOAK (b1) as solved, Kf 3.0: per firing N_allow {LCFt[0]} (MS {LCFt[1]:+.3f}), "
    f"assembly from zero N_allow "
    f"{LCFt[2]} (MS {LCFt[3]:+.3f}); the Kf 2.2 sensitivity row per firing N_allow {K22[0]} (MS {K22[1]:+.3f}; v2 +0.360: SIGN CHANGE in "
    f"v3); with (b1)'s moment x {MXI[2]} (R5, information) per firing N_allow {MXI[0]} (MS {MXI[1]:+.3f})); the head-to-shank fillet from "
    f"zero is a FOUND NEGATIVE that does not govern (jfwd_head_fillet_v352_v2."
    f"json: N_allow {LCFf[2]} (MS {LCFf[3]:+.3f}); per firing {LCFf[0]} (MS {LCFf[1]:+.3f}); Kt LITERATURE, secondary via AMESweb citing "
    "Pilkey 2005, the Pilkey page and the T-head Kt TO-SOURCE; the no-spring head-end resultants carried over ASSUMED); the thread root "
    "governs. Both are quoted as negative, never as passing. Closure paths 2 (FE levers: (b1) is solved and entered, rows v8 under C1 / "
    "R5, and the row stays negative; the P+Q select-fit band, C9 (6), is sized for the seat line and takes no screw credit) and 3 "
    "(qualification test, TO-DEFINE, founder) remain; path 1 (MJ thread) closed NOT SOURCED. HW-170 disc spring SINGLE-USE (lead "
    "19:53:27Z, CHANGELOG 248 (7)): a new spring with each new screw at every J-FWD assembly; removed springs are scrapped (C9 (2)). "
    "(4) POST-ABORT RULE (founder rule, lead 248 (7)): after any case-TC or TB-state abort the J-FWD joint counts as used: the ten "
    "ENG-HW-101-IN718 screws and their HW-170 springs are replaced (new, single-use) and the TC-01 holes (pins GO 5.50 / NO-GO 5.62) and "
    "the TC-02 taps (M5-6H GO / NO-GO) are gauged before the next run; this stands beside the 60 bar abs rule of the LC-TB70 envelope "
    "(lc_tb70_envelope_v1.json, unchanged: 'any head excursion above 60.0 bar abs: replace all J-FWD screws (HW-101) and gauge the TC-01 "
    "holes / TC-02 taps before the next run', the line-231 inspect-or-replace rule in head-trace form). Reason: the post-abort soak "
    f"(ASSUMED shifted history, J-FWD band up to {PA[0]} C GVLO / {PA[1]} C GVHI, jf1b_loctite_v352_v1.json) is not a rows or J-F1b "
    "state. OPEN (lead CHANGELOG 253 (8), (10); Mechanical's next round, not this re-map): the TB-state aborts are HW_OVERPRESSURE, "
    "PC_OVERPRESSURE and HARD_START by the lead's PROVISIONAL definition (the case-TC OVER_TEMP abort is in F-14), Mechanical to confirm; "
    "the 60 bar abs rule is a head-trace threshold, not an abort type, so as written a normal light whose head peak exceeds 60 bar abs "
    "also triggers it (above 58.1 bar abs the LC-TB70 envelope has only the abnormal bases: Z2 SF 1.0 / 1.5, Z3 FA-1 SF 1.0); 185 of "
    "896 FA-1 grid head peaks exceed 60 bar abs [SIM grid fraction, not a probability]; whether the rule stands for normal lights stays "
    "OPEN until REV-COMB-4 says whether those peaks are physical; Electronics states the logged quantity and threshold that detect it.")
C["C7_datasheet_residuals_gland1"] = (
    "Gland-1 FA1S closes at MS +0.082 on FNST's one-side extrusion limit 0.30 mm (1500 psi row, no interpolation), with the full 0.2772 mm "
    "diametral gap taken as one side (nothing centres the plug), entered at the FA-1 fluid bound 93.64 bar abs = 1343 psig (the chart's "
    "own axis); Apple Rubber Illustration 5.2 halved at 1343 psi gives +0.16 (support); no back-up ring. Residual: the two makers' curves "
    "differ in shape (FNST / Apple 0.48 at 1500 psi) and neither prints a cycle, time or temperature basis.")

# ------------------------------------------------------------------------------------------------ C8: the drawing texts (lead 18:36:37Z item 5)
DTP = DT["parts"]
C8 = {
    "what": ("the J-FWD drawing texts of v3.5.2 rev 5 as they stand for the hub update of lead 18:36:37Z item 5: the TC-01 / TC-02 rev-5 "
             "texts from the dev rev-5 source (rev5_drawing_texts_v352_v1.json; the FINAL 03-cad v3.5.2 set, released by the lead "
             "19:09:50Z, carries them), and the ENG-HW-101-IN718 / HW-170 / M-T1J / J-F1 texts of hardware_v352 v1.7 (published with the FINAL 03-cad "
             "v3.5.2 set, data/hardware_v352.json)"),
    "ENG-TC-01_rev5": {"notes": DTP["ENG-TC-01"]["notes"], "datum": DTP["ENG-TC-01"]["dwg"]["datum"],
                       "jfwd_fits_items": DTP["ENG-TC-01"]["jfwd_fits_items"]},
    "ENG-TC-02_rev5": {"notes": DTP["ENG-TC-02"]["notes"], "datum": DTP["ENG-TC-02"]["dwg"]["datum"],
                       "jfwd_fits_items": DTP["ENG-TC-02"]["jfwd_fits_items"]},
    "ENG-HW-101-IN718": {k: H101[k] for k in ("item", "standard", "size", "length_mm", "grade", "head_form_F3", "L_basis", "torque_Nm",
                                               "torque_basis", "thread_locker", "status", "action", "oxygen_service", "assembly_note", "test")},
    "HW-170": {k: H170[k] for k in ("item", "standard", "size", "grade", "qty", "L_basis", "status", "action", "assembly_note")},
    "M-T1J": MT1J,
    "GSE_lines": {pn: {k: L[k] for k in ("pn", "name", "qty", "material", "process", "drawing", "notes", "groups")} for pn, L in GSE.items()},
}
txt = {"TC01": json.dumps(C8["ENG-TC-01_rev5"]), "TC02": json.dumps(C8["ENG-TC-02_rev5"]), "HW101": json.dumps(C8["ENG-HW-101-IN718"]),
       "HW170": json.dumps(C8["HW-170"]), "MT1J": MT1J, "TC13": json.dumps(C8["GSE_lines"]["ENG-TC-13"]),
       "C4": C["C4_assembly_step_founder_procedure"], "C6": C["C6_founder_action_list_related"]}
ITEMS = {   # lead 18:36:37Z item 5: each text and where it stands (substring asserted in that text)
    "+/-0.25 deg index pin (F5)": [("TC02", "within +/-0.25 deg by an index pin in the match-drill fixture"),
                                   ("TC01", "within +/-0.25 deg by the index pin of the match-drill fixture"),
                                   ("HW101", "clocking +/-0.25 deg by an index pin in the drill fixture (F5)")],
    "C4 shoulder-screw registration (F2)": [("C4", "REGISTRATION (lead 17:55:55Z F2): fit the two GSE shoulder screws ENG-TC-13"),
                                            ("TC01", "REGISTRATION by two GSE shoulder screws ENG-TC-13"),
                                            ("MT1J", "C4 registration (lead 17:55:55Z F2): two GSE shoulder screws ENG-TC-13"),
                                            ("HW101", "C4 registration (lead 17:55:55Z F2)"), ("TC13", "two opposite holes")],
    "J-F1 torque cap at 3750 N (F1)": [("C4", "maximum preload of 3750 N or less"), ("TC01", "maximum preload capped at 3750 N"),
                                       ("MT1J", "T_lot = 3750 N x K_min(lot) x 5 mm"), ("HW101", "MAXIMUM preload is <= 3750 N on every")],
    "Prescale item (F1, TO-VERIFY)": [("C4", "Fuji Prescale footprint item (TO-VERIFY)"), ("TC01", "Fuji Prescale footprint item, TO-VERIFY"),
                                      ("HW101", "Fuji Prescale pressure-film footprint")],
    "single-use screws with the fillet in the inspection (R3 + LEAD ADDITION 18:36:37Z)": [
        ("C6", "dye penetrant at the thread root AND the head-to-shank fillet"), ("C4", "single-use, C6 (3)"),
        ("TC01", "dye penetrant at the thread root AND the head-to-shank fillet"),
        ("HW101", "dye penetrant at the thread root AND the head-to-shank fillet")]}
for k, v in ITEMS.items():
    for where, a in v:
        assert a in txt[where], (k, where, a)
C8["lead_items_18_36_37Z_item5"] = {k: [{"in": where, "text": a} for where, a in v] for k, v in ITEMS.items()}
C8["where_codes"] = {"TC01": "C8 ENG-TC-01_rev5 (TC-01 drawing, rev 5)", "TC02": "C8 ENG-TC-02_rev5 (TC-02 drawing, rev 5)",
                     "HW101": "C8 ENG-HW-101-IN718 (hardware v1.7 HW-101; the ENG-HW-101-IN718 drawing is TO-DRAW)",
                     "MT1J": "C8 M-T1J (hardware v1.7 tightening method)", "TC13": "C8 GSE_lines ENG-TC-13 (BOM GSE line)",
                     "C4": "item C4", "C6": "item C6"}
C8["open_items"] = ["ENG-HW-101-IN718 drawing TO-DRAW (F3 head form; pilot coaxiality dia 0.02 TO-CONFIRM with the maker); the spring "
                    "orientation is DEFINED in C9 (1) and goes on that drawing (the installation convention AS RECALLED, TO-VERIFY on the maker's sheet)",
                    "ENG-TC-13 drawing TO-DRAW (shoulder length, material, size steps)",
                    "match-drill fixture with the index pin and the guide bushings: shop tooling TO-DRAW (not BOM lines)",
                    "head-shoulder gap gauge 2.00 +/-0.02 TO-CONFIRM (rev-5 TC-02 tap note)",
                    "J-F1 Prescale film grade TO-SELECT; footprint TO-VERIFY",
                    "HW-170 reuse RULED single-use (248 (7), C9 (2)); the maker's relaxation data at about 160 C TO-QUOTE",
                    "LOCTITE 243 tap zone at TB_a150 128.0 / 116.0 C ACCEPTED as below 150 C (248 (7)); Henkel's service range and the hot-strength "
                    "fractions TO-VERIFY (founder)",
                    "J-F1b RULED (248 (7), C9 (3)): peak 175 C, dwell >= 10 min; the heating method TO-DEFINE by the test owner",
                    "TC-02 plug OD band (C9 (6)) RULED (R2-B, 07:37:34Z): select fit to the measured TC-01 bore, flag-free band [0.040, 0.0631] mm; "
                    "the parts / BOM string 'plug 57.20 f7' is not edited, superseded by C9 (6)",
                    "C9 (5) stand T0 rule: the J-FWD rows are at T0 20 C (no hot-day FE run, 249 (2)); the band edge at T0 24 C is information only"]
C["C8_jfwd_drawing_texts_rev5"] = C8

# ------------------------------------------------------------------------------------------------ C9: founder texts of the re-map (R2, R8, R10)
WIN, SEL = BR["fit_windows"], BR["select_fit"]
C9 = {
    "(1)_HW-170_orientation": {
        "drawing_note_ENG-HW-101-IN718_and_HW-170": (
            "HW-170 DISC SPRING ORIENTATION (route (i); Mechanical, DERIVED from the rows v8 load path; lead 248 (7)): one spring under each "
            "head, never stacked; concave (hollow) side DOWN, its outer edge (De 10.0, 9.85 min) bearing on the TC-01 spot-face flat; convex "
            "(crowned) side UP, its inner edge (Di 5.2, 5.32 max) toward the screw head; centred on the 5.15 h9 pilot of the F3 head; NEVER "
            "inverted (an inverted spring is removed and scrapped, C9 (2))."),
        "assembly_step": "C4 step 7 (the spring ORIENTED per C9 (1) as each flight screw is fitted; checked by eye before the screw engages)",
        "derivation": (
            "DERIVED; the DIN EN 16983 / DIN 2093 installation convention (load through the upper inner edge and the lower outer edge) is AS "
            "RECALLED, TO-VERIFY on the maker's sheet (Schnorr 001 500 A / Lesjofors 7909). The rows take the spring flat (solid) at every J-F1 "
            f"preload (derated F_flat {SP5['runs']['A_DIN2093_A10_17-7PH|R0.00|lo|seat']['F_flat_derated_N']:.0f} N spring A / "
            f"{SP5['runs']['B_Lesjofors_7909_1.4310|R0.00|lo|seat']['F_flat_derated_N']} N spring B against the {F_MIN} N minimum, "
            "jfwd_spring_v352_v5.json); in the cool frames after embedding the spring force falls below F_flat (spring A F_S min "
            f"{SP5['runs']['A_DIN2093_A10_17-7PH|R0.00|lo|seat']['F_S_min_N']} / {SP5['runs']['A_DIN2093_A10_17-7PH|R0.00|hi|seat']['F_S_min_N']} N "
            "at k_b lo / hi, R 0, the spring active in those frames), where the spring carries the load at its edges. Standard orientation: "
            "the outer edge (r 4.925-5.00) bears on the flat (the d11.2 spot face, with the disclosed tangential overhang, P(i)-2) and the head "
            "meets the crown at its bearing-face inner corner (da 5.55-5.80, r 2.775-2.90; F3); the T-head Kt at that corner is NOT SOURCED "
            "(disclosed with the head-fillet rows). Inverted: the inner edge (r 2.60-2.66) would sit inside the "
            "5.82 hole-plus-break edge (r 2.91) with no support, and the outer edge (r 4.925 min) lies outside the ISO 7380-1 head (dk 9.5 "
            "max, r 4.75), so the head would ride on the spring's bowl: the load path the rows assume would not exist.")},
    "(2)_HW-170_single_use": (
        "HW-170 disc spring SINGLE-USE (lead 19:53:27Z, CHANGELOG 248 (7)): a new spring with each new ENG-HW-101-IN718 screw at every "
        "J-FWD assembly; removed springs are scrapped, never refitted or measured for reuse; the rows assume an as-new spring; the maker's "
        "relaxation data at about 160 C is TO-QUOTE with the spring (delivered to Sonderborg DK-6400). HW-170 drawing / BOM note: "
        "'SINGLE-USE: scrap on removal'."),
    "(3)_J-F1b": (
        "J-F1b (the optional J-F1 extension of hardware v1.7 HW-101; rule lead 19:53:27Z, PEAK 175 C ACCEPTED 21:17:03Z, dwell CORRECTED, "
        "CHANGELOG 248 (7); work-tree record jf1b_loctite_v352_v1.json 2ba9d10745f3f651, read-only [SIM]): 5 of the J-F1 joints (with the "
        "spring, the load washer kept in; J-F1 coupons, never flight hardware), the cycle 20 -> 175 C -> 20 C, at least 10 min at the peak "
        "from when the spring flat reaches the peak, 10 cycles as in hardware v1.7, residual preload and breakaway torque recorded after "
        "each cycle as data for the preload-retention audit (the check on the relaxation model). Peak 175 C = max(160 C, the governing "
        f"SOAK70 zone maximum {JB['T_zone_max_C']} C + 10 C) rounded up to 5 C (the js5 screw set alone gives 170 C, information); the "
        "10 min is more than ten times the governing state's 53.0 s above (zone maximum - 10 C). METHOD: a uniform oven cycle puts the tap "
        "LOCTITE 243 at 175 C against 97.7 C in service, so it is allowed only once Henkel's service range for 243 is verified to cover "
        "175 C (AS RECALLED -55 to +180 C, TO-VERIFY); otherwise the spring and head zone are heated locally and the tap temperature is "
        "recorded; TO-DEFINE by the test owner (founder). The post-abort soak is not a J-F1b state (C9 (4))."),
    "(4)_post_abort_joint_replacement": C["C6_founder_action_list_related"][C["C6_founder_action_list_related"].index("(4) POST-ABORT RULE"):],
    "(5)_stand_T0_cross_reference": (
        "STAND T0 RULE (founder action, lead CHANGELOG 249 (2); cross-reference only, not a Mechanical rule): B1-length stand burns only "
        "with the engine soaked at a stand ambient <= 24 C (facility thermometer) [DERIVED]; in stand mode v2.11 refuses ARM if TC1 or TC2 "
        "reads > 24 C (backstop); the founder pre-fire checklist row is the control; re-derive after B-TC-1 as T0_max = 20 + (12.26 - "
        "e_hi,cal) / 0.96; the A1 flight has no T0 rule. The J-FWD rows use the B1 thermal fields as solved (T0 20 C; no hot-day FE run). "
        f"INFORMATION (jfwd_pq_band_v352_v1.json, ASSUMED uniform +4 K on the seat-line temperature, FE P+Q unchanged): at T0 24 C the band "
        f"edge {BR['band_mm_radial'][1]} mm would read MS {T0I['MS_at_band_edge_+4K_min']:+.3f} (SOAK) and MS 0 would need g <= "
        f"{T0I['g_at_MS0_+4K_min_mm']:.4f} mm; at the ruled R2-B edge g {G_R2B} mm it would read MS {P4[0]:+.3f} ({P4[1]}, k_b hi, 3750 N) "
        "[CALC, ASSUMED +4 K]; not a criterion."),
    "(6)_TC-02_select_fit_band_R2": (
        "ENG-TC-02 PLUG OD, J-FWD SEAT-LINE BAND (lead 2026-10-21T05:50:45Z R2, restated to the lead ruling R2-B; jfwd_pq_band_v352_v1.json "
        "on relax v8, the final anchors s6 + C1; the TC-01 bore 57.25 H8, 57.250-57.296): " + R2B + " At the ruled edge g "
        f"{G_R2B} mm [CALC on SIM, jfwd_pq_band_v352_v1.json]: seat-line MS {E631[('hi', 3750)][0]:+.4f} (k_b hi) / "
        f"{E631[('lo', 3750)][0]:+.4f} (k_b lo) at 3750 N ({E631[('hi', 3750)][1]}); 4096 N information {E631[('hi', 4096)][0]:+.4f} / "
        f"{E631[('lo', 4096)][0]:+.4f}; ASSUMED +4 K information (stand T0 24 C, k_b hi, 3750 N) {P4[0]:+.4f} ({P4[1]}). INFORMATION: "
        f"MS 0 at g {G0['hi']} mm (k_b hi) / {G0['lo']} mm (k_b lo) at 3750 N. "
        "The drawn 57.20 f7 (radial 0.040-0.078) leaves the seat line a FOUND NEGATIVE "
        f"(rows v8 at 3750 N: SOAK {SEAT8['SOAK']['MS_PQ_2Fty']:+.3f} {SEAT8['SOAK']['from']}, SOAK70 {SEAT8['SOAK70']['MS_PQ_2Fty']:+.3f}, "
        f"SOAK52 {SEAT8['SOAK52']['MS_PQ_2Fty']:+.3f} {SEAT8['SOAK52']['from']} under C1); the line-240 band [0.040, 0.0761] does not close it "
        f"at its upper edge (MS {BR['line_240_band_[0.040,0.0761]']['MS_min_at_0.0761_3750']['MS']:+.3f}). The edge is set by SOAK ((b2) rep "
        "366.8 MPa at 158.0 C), not SOAK52 (370.3 MPa under C1 at 152.7 C). MS >= +0.05 would need g <= "
        f"{BR['g_for_MS_+0.05_3750_mm']:.4f} (select fit only). Lead CALC 'about 0.011 mm' CONFIRMED: "
        f"{BR['lead_CALC_check']['computed_[0.040,0.0684]_window_mm']} mm at 0.0684 (the 4096 N edge), "
        f"{BR['lead_CALC_check']['computed_[0.040,0.0686]_window_mm']} mm at 0.0686 (the 3750 N edge). MF NOTE (R4): the seat-line P+Q is NOT "
        "shown mesh-converged (s9 -> s6 +12 to +18 %, s6 -> cD -1.5 to -7.3 %, not monotonic); the FE are at g 0.078, outside the band, so "
        "the band MS are the model's scaling of the 0.078 FE [DERIVED], quoted as found. The band acts on the seat line only; the screw "
        "rows take no credit. No CAD change: the TC-02 STEP is unchanged."),
    "(7)_CAD_basis_R8": "CAD BASIS (lead R8): " + R8["cad_basis_R8"] + "; quoted in the rows (rows v8 cad_basis_R8) and in these texts.",
}
assert (SP5["runs"]["A_DIN2093_A10_17-7PH|R0.00|lo|seat"]["F_S_min_N"], SP5["runs"]["A_DIN2093_A10_17-7PH|R0.00|hi|seat"]["F_S_min_N"]) == (335.2, 333.1)
assert SP5["runs"]["A_DIN2093_A10_17-7PH|R0.00|lo|seat"]["F_S_min_N"] < SP5["runs"]["A_DIN2093_A10_17-7PH|R0.00|lo|seat"]["F_flat_derated_N"]
assert C9["(4)_post_abort_joint_replacement"].startswith("(4) POST-ABORT RULE (founder rule, lead 248 (7))")
C["C9_founder_texts_remap_v352"] = C9

# ------------------------------------------------------------------------------------------------ T-F1
ROLE = {"TB": "BASIS (R9; CHANGELOG 249 (3): the A 175 rows, tb352g GVLO / tb352h GVHI)",
        "TB_a150": "BESIDE (the reading-equals-truth case; A = 150 C, 249 (1) ACCEPTED)",
        "TB_a165": "re-base candidate only after B-TC-1 calibrates the channel, by the lead (249 (3))",
        "TB_a135": "closed abort search record", "TB_a120": "closed abort search record", "TB_a105": "closed abort search record"}
tb_rows = []
for stn in ("TB", "TB_a165", "TB_a150", "TB_a135", "TB_a120", "TB_a105"):
    r = {"abort_C": B["GVLO"]["TB_surrogate_per_abort"][stn]["abort_C"]}
    for bd in ("GVLO", "GVHI"):
        x = B[bd]["TB_surrogate_per_abort"][stn]
        r[bd] = {"shift_K": x["shift_K"], "TC-02_TB_field_max_C": x["ENG-TC-02"]["TB_state_field_max_C"],
                 "TC-01_TB_field_max_C": x["ENG-TC-01"]["TB_state_field_max_C"],
                 "TC-02_shifted_history_t_above_150C_s": x["ENG-TC-02"]["shifted_history_ASSUMED"]["t_above_150C_s"],
                 "TC-01_shifted_history_max_C": x["ENG-TC-01"]["shifted_history_ASSUMED"]["max_C"],
                 "TC-01_shifted_history_t_above_150C_s": x["ENG-TC-01"]["shifted_history_ASSUMED"]["t_above_150C_s"],
                 "nominal_trip": x["shift_K"] < 0}
    r["row"] = stn
    r["role_R9"] = ROLE[stn]
    tb_rows.append(r)
cells_T = sorted({lo["ENG-TC-02"]["part_max"]["max_C"], lo["ENG-TC-01"]["part_max"]["max_C"], 150.0, 175.0, 200.0, 225.0, 250.0}
                 | {r["GVLO"]["TC-02_TB_field_max_C"] for r in tb_rows})
eng = {f"{t:g}": {"Fty_MPa": round(al("Fty", t), 1), "Ftu_MPa": round(al("Ftu", t), 1)} for t in cells_T}
def tb_one(r):
    return (f"A {r['abort_C']:g} C: TC-02 {r['GVLO']['TC-02_TB_field_max_C']:.1f} | {r['GVHI']['TC-02_TB_field_max_C']:.1f} C, "
            f"shifted-history time above 150 C TC-02 {r['GVLO']['TC-02_shifted_history_t_above_150C_s']:.1f} | "
            f"{r['GVHI']['TC-02_shifted_history_t_above_150C_s']:.1f} s, TC-01 {r['GVLO']['TC-01_shifted_history_t_above_150C_s']:.1f} | "
            f"{r['GVHI']['TC-01_shifted_history_t_above_150C_s']:.1f} s (TC-01 shifted-history maximum {r['GVLO']['TC-01_shifted_history_max_C']:.1f} | "
            f"{r['GVHI']['TC-01_shifted_history_max_C']:.1f} C), margin to the nominal end-of-burn case maximum "
            f"{r['GVLO']['shift_K']:+.1f} | {r['GVHI']['shift_K']:+.1f} K"
            + (" (NOMINAL TRIP on " + "/".join(b for b in ("GVLO", "GVHI") if r[b]["nominal_trip"]) + ")" if (r["GVLO"]["nominal_trip"] or r["GVHI"]["nominal_trip"]) else ""))


TBR = {r["row"]: r for r in tb_rows}
A175, A150 = TBR["TB"], TBR["TB_a150"]
for stn, blk in (("TB", R9["basis_A175_TB_both_bounds"]), ("TB_a150", R9["beside_A150_reading_equals_truth"]), ("TB_a165", R9["A165_rebase_condition"]["rows_record"])):
    for bd in ("GVLO", "GVHI"):
        x, r = blk[bd], TBR[stn][bd]
        assert (x["ENG-TC-02"]["TB_state_field_max_C"], x["ENG-TC-02"]["shifted_history_ASSUMED"]["t_above_150C_s"], x["ENG-TC-01"]["shifted_history_ASSUMED"]["max_C"],
                x["ENG-TC-01"]["shifted_history_ASSUMED"]["t_above_150C_s"], x["shift_K"]) == (
            r["TC-02_TB_field_max_C"], r["TC-02_shifted_history_t_above_150C_s"], r["TC-01_shifted_history_max_C"], r["TC-01_shifted_history_t_above_150C_s"], r["shift_K"]), (stn, bd)
assert (A175["GVLO"]["TC-02_TB_field_max_C"], A175["GVLO"]["TC-02_shifted_history_t_above_150C_s"], A175["GVLO"]["TC-01_shifted_history_max_C"],
        A175["GVLO"]["TC-01_shifted_history_t_above_150C_s"], A175["GVHI"]["TC-02_TB_field_max_C"], A175["GVHI"]["TC-02_shifted_history_t_above_150C_s"],
        A175["GVHI"]["TC-01_shifted_history_max_C"]) == (248.4, 1192.0, 257.1, 1435.8, 233.0, 929.7, 243.4)     # lead 249 (3), verbatim numbers
assert not any(A175[b]["nominal_trip"] or A150[b]["nominal_trip"] for b in ("GVLO", "GVHI"))
assert all(B[b]["parts"][pt]["part_max"]["max_C"] <= B["GVLO"]["parts"][pt]["part_max"]["max_C"] for b in ("GVLO", "GVHI") for pt in ("ENG-TC-01", "ENG-TC-02"))
assert A175["GVLO"]["TC-02_TB_field_max_C"] >= A175["GVHI"]["TC-02_TB_field_max_C"] and A175["GVLO"]["TC-01_TB_field_max_C"] == A175["GVHI"]["TC-01_TB_field_max_C"] == 175.0
t02, t01 = lo["ENG-TC-02"], lo["ENG-TC-01"]
m02, m01 = t02["part_max"]["max_C"], t01["part_max"]["max_C"]
e02, e01 = eng[f"{m02:g}"], eng[f"{m01:g}"]
TF1 = (
    "T-F1. Short-time exposure allowables for the 6061-T6 parts TC-01 (case tube) and TC-02 (injector head / forward closure). "
    "GATE: before the first static fire. "
    "WHY: criterion 183 (1)(d) / 188 (5) needs each part's temperature within a SOURCED time-at-temperature limit. The usable limit on "
    "file for 6061-T6 is 150 C (long time). The strength cells use the engmat 10,000 h allowables (conservative for strength), so (d) is "
    "reported OPEN, never as passed, for TC-01 and TC-02; it gates nominal operation as well as the abort value. "
    "PREDICTED EXPOSURE [SIM, v3.5.2 rev-4 thermal, B1 p99 tg711, gap-conductance bounds GVLO | GVHI]: "
    f"TC-02 part maximum {pair(lambda p: p['ENG-TC-02']['part_max']['max_C'])} C at the end of burn, above 150 C for "
    f"{pair(lambda p: p['ENG-TC-02']['part_max']['t_above_150C_s'])} s per firing. "
    f"TC-01 part maximum {pair(lambda p: p['ENG-TC-01']['part_max']['max_C'])} C at the chamber bore about 14 mm aft of the injector face, "
    f"in the soak ({pair(lambda p: p['ENG-TC-01']['part_max']['t_of_max_s'])} s), above 150 C for "
    f"{pair(lambda p: p['ENG-TC-01']['part_max']['t_above_150C_s'])} s per firing; at the J-FWD screw row "
    f"{pair(lambda p: p['ENG-TC-01']['jfwd_row']['max_C'])} C, {pair(lambda p: p['ENG-TC-01']['jfwd_row']['t_above_150C_s'])} s above "
    f"150 C; while pressurised (burn) TC-01 stays at or below {pair(lambda p: p['ENG-TC-01']['burn_max_C'])} C. "
    f"Over the {LIFE}-cycle design life (183 (1)(c)) the cumulative time above 150 C is TC-02 "
    f"{LIFE * t02['part_max']['t_above_150C_s'] / 60:.1f} | {LIFE * hi['ENG-TC-02']['part_max']['t_above_150C_s'] / 60:.1f} min and "
    f"TC-01 {LIFE * t01['part_max']['t_above_150C_s'] / 3600:.1f} | {LIFE * hi['ENG-TC-01']['part_max']['t_above_150C_s'] / 3600:.1f} h "
    "(part maxima). "
    "EXPOSURE BASIS, TB STATE (RESTATED, lead 2026-10-21T05:50:45Z R9; CHANGELOG 249 (3)) [ASSUMED surrogate, sax.py: the end-of-burn "
    "field shifted uniformly so that the TC-01 maximum equals A; the shifted-history times apply the same shift to the whole B1 history "
    "and are for sizing only]: the basis is the A 175 rows (TB; FEA3D's tb352g GVLO / tb352h GVHI; both gap-conductance bounds; they cover "
    "a TC-01 rise rate r <= about 22.8 K/s): " + tb_one(A175) + "; BESIDE them the reading-equals-truth case at the adopted abort value "
    "(A stays 150 C, 249 (1)): " + tb_one(A150) + ". On the A 175 rows criteria (a)-(c) PASS on both bounds (lowest TC-02 TBS +0.409 / "
    "+0.745, lead 249 (3)); (d) is OPEN (this action). Re-basing T-F1 to the A 165 rows is possible only after B-TC-1 calibrates the "
    "channel (tol_lo 10.28 K, TC-01 maximum 161.82 C), by the lead, before T-F1 is run; the A 165 / 135 / 120 / 105 rows stay in the json "
    "table (T-F1_TB_table) as the record of the closed abort search. "
    "ROUTE (i), sourced allowables, no test: obtain short-time exposure data for 6061-T6 from a public, citable document (for example "
    "MIL-HDBK-5J chapter 3, the 6061 elevated-temperature strength curves with exposure time, or EN 1999-1-2 Table 1a, the 6061-T6 "
    "strength ratios for short exposure) and record document, edition, figure or table, page, URL and access date. Read, at each part "
    "maximum (nominal as above; TB on the A 175 basis rows, both bounds) and for an exposure no shorter than the cumulative time above 150 C of the "
    "planned firings, (1) the strength at temperature and (2) the room-temperature strength after the exposure. PASS when (1) is at least "
    f"the value the cells used (engmat 10,000 h, e.g. Fty / Ftu {e02['Fty_MPa']} / {e02['Ftu_MPa']} MPa at {m02:g} C and "
    f"{e01['Fty_MPa']} / {e01['Ftu_MPa']} MPa at {m01:g} C; the full table is in this json) and (2) meets the T6 minimums of the stock's "
    "own specification "
    "(engmat basis ASTM B221 / B241: Fty 240 / Ftu 260 MPa); otherwise T-F3 (the line-212 design change). "
    "ROUTE (ii), coupon test on the same stock (the heat / lot of the TC-01 tube and of the TC-02 bar): expose coupons in a calibrated oven "
    f"(+/-3 K) at the TB part maximum of the A 175 basis rows and no lower than the nominal part maximum (GVLO, the hotter bound: TC-02 at "
    f"{max(A175['GVLO']['TC-02_TB_field_max_C'], m02):.1f} C, its A 175 TB state; TC-01 at {max(A175['GVLO']['TC-01_TB_field_max_C'], m01):.1f} C, "
    f"its nominal soak maximum, above its {A175['GVLO']['TC-01_TB_field_max_C']:.0f} C TB state), for the cumulative hot time of the planned firings (at least "
    f"the {LIFE}-cycle values above, plus every planned TB / abort test event at its A 175 shifted-history time above 150 C, TC-02 "
    f"{A175['GVLO']['TC-02_shifted_history_t_above_150C_s']:.1f} s and TC-01 {A175['GVLO']['TC-01_shifted_history_t_above_150C_s']:.1f} s "
    "GVLO); "
    "then room-temperature tensile tests (EN ISO 6892-1 or ASTM B557) on at least 3 exposed and 3 unexposed control coupons per stock, same "
    "orientation, and hardness (plus eddy-current conductivity if available) on every coupon. PASS when every exposed coupon meets the T6 "
    "minimums of the stock specification (Rp0.2, Rm and elongation); hardness and conductivity are recorded as the screening trend, not the "
    "pass rule. Optional: one hot tensile at the part maximum after the exposure, at least the engmat value at that temperature. If any "
    "exposed coupon fails, (d) stays OPEN and the design goes to T-F3. "
    "No recalled or estimated value may replace either route. Until one closes, every quoted TC-01 / TC-02 row carries (d) OPEN; (d) "
    "is reported OPEN on the A 175 basis rows, with the A 150 rows beside them.")

out = {"id": "item_c_tf1_texts_v352", "version": "v4", "date": "2026-10-21", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {**{k: {"path": str(p), "sha256_16": s16} for k, (p, s16) in INP.items()},
                  "engmat_AL6061-T6_Fty": AL["Fty"]["src"], "engmat_AL6061-T6_Ftu": AL["Ftu"]["src"]},
       "tags": {"head_fillet_Kt": ("LITERATURE (secondary, via AMESweb citing Pilkey 2005); the Pilkey page and the T-head Kt TO-SOURCE (lead "
                                   "18:36:37Z; the file's own tag reads 'WEB-SOURCED, BOOK PAGE TO-SOURCE; T-head NOT SOURCED')"),
                "head_end_resultants": "ASSUMED (the no-spring FE head-end resultants carried over, lead 18:36:37Z)",
                "under_head_full_float": "ASSUMED (mean-pressure scaling on the spring footprint, lead 17:55:55Z F1 FLAG)",
                "spring_orientation": "DERIVED from the rows v8 load path; the DIN EN 16983 / DIN 2093 installation convention AS RECALLED, TO-VERIFY",
                "band": "CALC / DERIVED on relax v8 (the model's scaling of the g 0.078 FE); MF note R4",
                "T0_24C_band_edge": "INFORMATION, ASSUMED uniform +4 K",
                "TB_rows": "SIM thermal / ASSUMED sax.py surrogate (tf1_exposure v1 numbers, restated v2)"},
       "changes_vs_v3": {"inputs": "rows v8, spring v5, head fillet v2, K_js5 v3, screw LCF v3 (tap wall v1 stays, R11); band v1; jf1b_loctite v1; tf1_exposure v2",
                         "C1 (g) / (h)": "cite rows v8 (route_i_spring_footprint unchanged from rows v7)",
                         "C4": "step 1 checks the plug OD against the C9 (6) band; step 7 the spring ORIENTED per C9 (1); step 9 springs scrapped, the post-abort rule",
                         "C6": "(3) LCF v3 / head fillet v2 numbers, the Kf 2.2 sign change, the R5 information, path 2 status, HW-170 SINGLE-USE; new (4) post-abort rule",
                         "C8": "open items updated to the 248 (7) rulings, the band and the T0 cross-reference (the drawing-text copies of rev 5 / hardware v1.7 unchanged)",
                         "C9": "new: founder texts (1) orientation, (2) HW-170 single-use, (3) J-F1b, (4) post-abort, (5) stand T0 cross-reference, (6) TC-02 band, (7) CAD basis",
                         "T-F1": "RESTATED (R9): the A 175 basis rows with the A 150 rows beside; routes (i) / (ii) on the A 175 basis; (d) OPEN on the A 175 rows; the table rows carry their R9 role",
                         "unchanged": "C1 (a)-(f), C2, C3, C3b, C5, C7, the geometry checks, the engmat table, the PREDICTED EXPOSURE and the 50-cycle text of T-F1"},
       "changes_v2_to_v3_record": {"C1 (g)": "route (i) spring footprint on the flat (rows v7), da 5.55-5.80 drawn (F3)",
                         "C1 (h)": "datums A = 57.25 H8 bore axis, B = TC-01 forward end face (17:55:55Z); the v2 datum FLAG closed; d11.2 spot face",
                         "C3b": "new: ENG-TC-13 registration shoulder screw pair (GSE, F2)",
                         "C4": "rewritten: J-F1 gate (lot torque, spring items, Prescale), hole / tap gauging, gap-gauge head setting (rev 5; v2 "
                               "'until seated'), F2 registration, one-at-a-time flight screws with new springs to the J-F1 lot torque (M-T1J, "
                               "3750 N cap), shoulder screws out last, single-use",
                         "C6": "(2) springs replaced with the screws; (3) the single-use founder rule with the head-to-shank fillet in the "
                               "removed-screw inspection (LEAD ADDITION 18:36:37Z), C6 OPEN with the thread-root and fillet LCF rows",
                         "C8": "new: the drawing texts (TC-01 / TC-02 rev 5, ENG-HW-101-IN718, HW-170, M-T1J, J-F1, GSE lines) with the lead's "
                               "five 18:36:37Z item-5 texts located and asserted",
                         "unchanged": "C1 (a)-(f), C2, C3, C5, C7, T-F1 (text and tables identical to v2)"},
       "item_C": C, "item_C_geometry_checks": geo, "T-F1": TF1, "T-F1_TB_table": tb_rows, "T-F1_engmat_10000h_values_used_by_the_cells": eng,
       "T-F1_exposure_basis_R9": {k: R9[k] for k in ("rule", "criteria_status", "abort_value", "closed_abort_search_record")}}
for k in ("C1_TC01_drawing_callout_rev5",):
    a, b = V3["item_C"][k], C[k]
    assert a[:a.index("(g) hole size")] == b[:b.index("(g) hole size")], "C1 (a)-(f) changed"
    assert a.replace("rows v7 route_i_spring_footprint: spring De", "rows v8 route_i_spring_footprint, unchanged from rows v7: spring De").replace(
        "within 0.10 dia. The rows v7 ", "within 0.10 dia. The rows v8 ") == b, "C1 (g) / (h) changed beyond the rows citation"
for k in ("C2_bore_lead_in_rev5", "C3_fitting_aid_GSE", "C3b_registration_shoulder_screws_GSE", "C5_record_why_not_moved", "C7_datasheet_residuals_gland1"):
    assert V3["item_C"][k] == C[k], k
for k in ("what", "ENG-TC-01_rev5", "ENG-TC-02_rev5", "ENG-HW-101-IN718", "HW-170", "M-T1J", "GSE_lines", "lead_items_18_36_37Z_item5", "where_codes"):
    assert V3["item_C"]["C8_jfwd_drawing_texts_rev5"][k] == C8[k], k
assert V3["item_C_geometry_checks"] == geo and V3["T-F1_engmat_10000h_values_used_by_the_cells"] == eng
for a, b in zip(V3["T-F1_TB_table"], tb_rows):
    assert {k: b[k] for k in a} == a
cut3, cut4 = V3["T-F1"].index("TB STATE per trial case-abort value A"), TF1.index("EXPOSURE BASIS, TB STATE (RESTATED")
assert V3["T-F1"][:cut3] == TF1[:cut4], "T-F1 text before the TB paragraph changed"
# ---- the drawing-text set for 03-cad/v3.5.2/texts/ (subset of C9; nothing in the 03-cad data is edited)
DTX = {"id": "jfwd_drawing_texts_v352", "version": "v1", "date": "2026-10-21", "owner": "mechanical",
       "basis": ("J-FWD drawing texts of the v3.5.2 re-map (lead 2026-10-21T05:50:45Z R2 / R8 / R10, the TC-02 band restated to the lead "
                 "ruling R2-B 2026-10-21T07:37:34Z; CHANGELOG 248 (7)), produced by "
                 "04-fea/v352/texts/item_c_tf1_texts_v352.py v4 from its C9 block; DERIVED / CALC on SIM inputs as tagged there, none of it "
                 "physical approval.  These texts SUPERSEDE, where they differ, the strings still carried by src/parts_engine.py, "
                 "BOM_v3.5.2.csv / .json and data/hardware_v352.json ('plug 57.20 f7 (-0.030/-0.060)', 'orientation TO-DEFINE', 'reuse of a "
                 "removed spring TO-RULE'); those files are not edited by this publication (no CAD change; the lead rules any data update)."),
       "source": {"script": "04-fea/v352/texts/item_c_tf1_texts_v352.py (v4)", "json": "04-fea/v352/texts/item_c_tf1_texts_v352_v4.json"},
       "ENG-TC-02": {"plug_OD_seat_line_band_R2": C9["(6)_TC-02_select_fit_band_R2"]},
       "ENG-HW-101-IN718": {"HW-170_orientation_note": C9["(1)_HW-170_orientation"]["drawing_note_ENG-HW-101-IN718_and_HW-170"]},
       "HW-170": {"orientation_note": C9["(1)_HW-170_orientation"]["drawing_note_ENG-HW-101-IN718_and_HW-170"],
                  "single_use_note": C9["(2)_HW-170_single_use"]},
       "assembly_and_founder_rules": {"C4_step_7_orientation": C9["(1)_HW-170_orientation"]["assembly_step"],
                                      "post_abort_joint_replacement": C9["(4)_post_abort_joint_replacement"],
                                      "J-F1b": C9["(3)_J-F1b"], "stand_T0_cross_reference": C9["(5)_stand_T0_cross_reference"]},
       "analysis_basis_note_R8": C9["(7)_CAD_basis_R8"]}
s_dt = json.dumps(DTX, indent=1)
OUT_DT.write_text(s_dt)
print(OUT_DT, hashlib.sha256(s_dt.encode()).hexdigest()[:16])
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
for k in ("C4_assembly_step_founder_procedure", "C6_founder_action_list_related"):
    print("==", k)
    print(C[k])
print("== C9")
print(json.dumps(C9, indent=1))
print("== T-F1 (from EXPOSURE BASIS)")
print(TF1[cut4:])
