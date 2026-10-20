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
changes CAD.  Writes v352/texts/item_c_tf1_texts_v352_v3.json."""
import json, hashlib, math, sys
from pathlib import Path
import numpy as np

T = Path("/home/claude/work/mechanical/v352/texts")
EXP = T / "tf1_exposure_v352_v1.json"
OUT = T / "item_c_tf1_texts_v352_v3.json"
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat
AL = engmat.MATERIALS["AL6061-T6"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


J = Path("/home/claude/work/mechanical/v352/jfwd")
D3 = Path("/home/claude/work/mechanical/v352/engine/03-cad")
INP = {"tf1_exposure": (EXP, "d23e72f089cca33a"),
       "rows_v7": (J / "jfwd_in718_rows_v352_v7.json", "6113d28b64d0dba5"), "spring_v4": (J / "jfwd_spring_v352_v4.json", "a277b996c2d61b83"),
       "head_fillet_v1": (J / "jfwd_head_fillet_v352_v1.json", "337883c3f2076a32"), "tap_wall_v1": (J / "jfwd_tapwall_v352_v1.json", "bcb21243d57af998"),
       "K_js5_v2": (J / "jfwd_embed_fit_js5_v352_v2.json", "e2624bf729633fb8"), "screw_lcf_v2": (J / "jfwd_screw_lcf_v352_v2.json", "6acdaa2febdf3f6c"),
       "hardware_v1.7": (D3 / "src/data/hardware_v352.json", "c2c7b13d3a0086e3"),
       "rev5_drawing_texts_v1": (T / "rev5_drawing_texts_v352_v1.json", "3eed41f8c4f8a64f")}
X = {}
for k, (p, s16) in INP.items():
    assert sha(p) == s16, (k, p, sha(p))
    X[k] = json.loads(Path(p).read_text())
R7, SP4, HF1, TW1, JS2, LC2, HW, DT = (X[k] for k in ("rows_v7", "spring_v4", "head_fillet_v1", "tap_wall_v1", "K_js5_v2", "screw_lcf_v2",
                                                      "hardware_v1.7", "rev5_drawing_texts_v1"))
assert HW["version"] == "v1.7"


def al(k, Tc):
    return float(np.interp(Tc, AL[k]["T_C"], AL[k]["v"])) / 1e6


E = X["tf1_exposure"]
B = E["bounds"]
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
JF1 = R7["J_F1"]
F_CAP, F_MIN, T_LOT, KW = JF1["maximum_N"], JF1["minimum_N_today_K_window"], JF1["torque_Nm_today_K_window"], JF1["K_window"]
assert (F_CAP, F_MIN, T_LOT, KW) == (3750.0, 2057.6, 2.747, [0.1465, 0.267])
FP = R7["route_i_spring_footprint"]
A_REG, A_FF = FP["areas_mm2"]["registered_stack_0.4865_F2"], FP["areas_mm2"]["full_float_0.557"]
assert (A_REG, A_FF) == (46.06, 45.352) and FP["quoted_flat_bearing_basis"] == "registered_stack_0.4865_F2"
F3 = SP4["fillet"]["F3_adopted"]
assert F3["da_mm"] == [5.55, 5.8]
GEOc = SP4["geometry_length_tip_engagement"]["cases"]
GA, GB = GEOc["spring A t 0.5: 10.7 +/-0.1"], GEOc["spring B t 0.4: 10.6 +/-0.1"]
assert (GA["L_e_gap_bound_mm"], GB["L_e_gap_bound_mm"]) == (7.294, 7.294)
TWW = TW1["walls_mm"]
assert (TWW["ruled_+/-0.25deg_net_GOVERNING"], TWW["+/-0.5deg_net_info"]) == (1.6355, 1.5415)
HG = HF1["governing_and_thread_root_comparison"]["3750"]
LCFt = (HG["i_firing"]["thread_root_N_allow"], HG["i_firing"]["thread_root_MS"], HG["ii_assembly_from_zero"]["thread_root_N_allow"],
        HG["ii_assembly_from_zero"]["thread_root_MS"])
LCFf = (HG["i_firing"]["fillet_N_allow"], HG["i_firing"]["fillet_MS"], HG["ii_assembly_from_zero"]["fillet_N_allow"],
        HG["ii_assembly_from_zero"]["fillet_MS"])
assert LCFt == (11.9, -0.762, 0.9, -0.982) and LCFf == (1140.3, 21.806, 30.9, -0.382)
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
    "each side (5.82) is the inner boundary of the HW-170 disc-spring footprint on the flat (rows v7 route_i_spring_footprint: spring De "
    f"9.85 / Di 5.32 at its limits, {A_REG} mm2 at the registered stack 0.4865 (lead 17:55:55Z F2), {A_FF} mm2 at full float 0.557); the "
    f"head bears on the spring, with da {F3['da_mm'][0]:.2f}-{F3['da_mm'][1]:.2f} stated on the ENG-HW-101-IN718 drawing (F3; it replaces the "
    "v2 'da 5.7 TO-VERIFY'); the v2 basis (head on the flat, float 0.397, rows v5) is superseded. "
    "(h) hole position (ADOPTED, lead 14:34Z; datums as checked in the rev-5 CAD and ACCEPTED 17:55:55Z): datum A = the axis of the "
    "forward seal-land bore 57.25 H8; datum B = the TC-01 forward end face, from which the hole row is dimensioned (12.000 BASIC from B); "
    "each hole axis 0.10 dia to A|B; the d11.2 spot face (rev-5 cutter, P(i)-1) coaxial with its hole within 0.10 dia. The rows v7 "
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
    "J-FWD build and every re-assembly (v3: route (i), lead 16:53Z R2 / R3, 17:55:55Z F1 / F2, 18:36:37Z): "
    "0. GATE: J-F1 complete on the flight lots (ENG-HW-101-IN718 screws, HW-170 springs, LOCTITE 243): it sets the lot torque T_lot and "
    "carries the spring items (K with the spring under the head, the spring flattening, the crack-on torque) and the Fuji Prescale "
    "footprint item (TO-VERIFY) (hardware_v352 v1.7 HW-101 test). "
    "1. inspect the hole edges and the bore per C1 (e); gauge the ten TC-01 holes with the pins GO 5.50 / NO-GO 5.62 and record each "
    "hole's size (ENG-TC-13 is selected to it; a hole that takes the 5.62 pin is rejected, C1 (g)); gauge the ten TC-02 taps M5-6H GO / "
    "NO-GO (cured locker removed by a thread chaser only, no re-tap); clean. "
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
    "spring B; never mixed in one joint) with a NEW HW-170 disc spring under the head (orientation per the ENG-HW-101-IN718 drawing, "
    "TO-DEFINE), LOCTITE 243 (flight lot) on the screw thread only, never on the spring or the flat; tighten to the J-F1 LOT TORQUE by "
    f"method M-T1J (T_lot = {F_CAP:.0f} N x K_min(lot) x 5 mm, so that the lot's K_min gives a maximum preload of {F_CAP:.0f} N or less, "
    f"lead 17:55:55Z F1; today's K window {KW[0]}-{KW[1]}: {T_LOT:.3f} N m, minimum {F_MIN:.1f} N); record per hole: hole number and its "
    "pin size, screw and spring lot, torque, wrench (ID and calibration date). "
    "8. remove the two shoulder screws LAST and replace each with a flight screw per step 7, recorded. "
    "9. never re-torque a fitted screw; a screw removed for any reason is replaced by a new screw and a new spring (single-use, C6 (3)); "
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
    f"(183 (1)(c); jfwd_screw_lcf_v352_v2.json, Kf 3.0: per firing N_allow {LCFt[0]} (MS {LCFt[1]:+.3f}), assembly from zero N_allow "
    f"{LCFt[2]} (MS {LCFt[3]:+.3f})); the head-to-shank fillet from zero is a FOUND NEGATIVE that does not govern (jfwd_head_fillet_v352_v1."
    f"json: N_allow {LCFf[2]} (MS {LCFf[3]:+.3f}); per firing {LCFf[0]} (MS {LCFf[1]:+.3f}); Kt LITERATURE, secondary via AMESweb citing "
    "Pilkey 2005, the Pilkey page and the T-head Kt TO-SOURCE; the no-spring head-end resultants carried over ASSUMED); the thread root "
    "governs. Both are quoted as negative, never as passing. Closure paths 2 (FE levers, (b1) / select-fit band after chain E) and 3 "
    "(qualification test, TO-DEFINE, founder) remain; path 1 (MJ thread) closed NOT SOURCED. HW-170 disc-spring reuse TO-RULE (Mechanical "
    "proposes: new with the screw at every assembly).")
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
C8["open_items"] = ["ENG-HW-101-IN718 drawing TO-DRAW (F3 head form; pilot coaxiality dia 0.02 TO-CONFIRM with the maker; spring orientation "
                    "TO-DEFINE)", "ENG-TC-13 drawing TO-DRAW (shoulder length, material, size steps)",
                    "match-drill fixture with the index pin and the guide bushings: shop tooling TO-DRAW (not BOM lines)",
                    "head-shoulder gap gauge 2.00 +/-0.02 TO-CONFIRM (rev-5 TC-02 tap note)",
                    "J-F1 Prescale film grade TO-SELECT; footprint TO-VERIFY", "HW-170 reuse TO-RULE",
                    "LOCTITE 243 tap-zone temperature at the R1 abort TB states TO-VERIFY (hardware v1.7 thread_locker)",
                    "J-F1b cycle temperature against the about 160 C spring relaxation basis TO-RULE"]
C["C8_jfwd_drawing_texts_rev5"] = C8

# ------------------------------------------------------------------------------------------------ T-F1
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
    tb_rows.append(r)
cells_T = sorted({lo["ENG-TC-02"]["part_max"]["max_C"], lo["ENG-TC-01"]["part_max"]["max_C"], 150.0, 175.0, 200.0, 225.0, 250.0}
                 | {r["GVLO"]["TC-02_TB_field_max_C"] for r in tb_rows})
eng = {f"{t:g}": {"Fty_MPa": round(al("Fty", t), 1), "Ftu_MPa": round(al("Ftu", t), 1)} for t in cells_T}
tb_txt = "; ".join(f"A {r['abort_C']:g} C: TC-02 {r['GVLO']['TC-02_TB_field_max_C']:.1f} | {r['GVHI']['TC-02_TB_field_max_C']:.1f} C, "
                   f"shifted-history time above 150 C TC-02 {r['GVLO']['TC-02_shifted_history_t_above_150C_s']:.0f} | "
                   f"{r['GVHI']['TC-02_shifted_history_t_above_150C_s']:.0f} s, TC-01 {r['GVLO']['TC-01_shifted_history_t_above_150C_s']:.0f} | "
                   f"{r['GVHI']['TC-01_shifted_history_t_above_150C_s']:.0f} s, margin to the nominal end-of-burn case maximum "
                   f"{r['GVLO']['shift_K']:+.1f} | {r['GVHI']['shift_K']:+.1f} K"
                   + (" (NOMINAL TRIP on " + "/".join(b for b in ("GVLO", "GVHI") if r[b]["nominal_trip"]) + ")" if (r["GVLO"]["nominal_trip"] or r["GVHI"]["nominal_trip"]) else "")
                   for r in tb_rows)
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
    "TB STATE per trial case-abort value A [ASSUMED surrogate, sax.py: the end-of-burn field shifted uniformly so that the TC-01 maximum "
    "equals A; the shifted-history times apply the same shift to the whole B1 history and are for sizing only]: " + tb_txt + ". "
    "ROUTE (i), sourced allowables, no test: obtain short-time exposure data for 6061-T6 from a public, citable document (for example "
    "MIL-HDBK-5J chapter 3, the 6061 elevated-temperature strength curves with exposure time, or EN 1999-1-2 Table 1a, the 6061-T6 "
    "strength ratios for short exposure) and record document, edition, figure or table, page, URL and access date. Read, at each part "
    "maximum (nominal as above; TB at the adopted abort value) and for an exposure no shorter than the cumulative time above 150 C of the "
    "planned firings, (1) the strength at temperature and (2) the room-temperature strength after the exposure. PASS when (1) is at least "
    f"the value the cells used (engmat 10,000 h, e.g. Fty / Ftu {e02['Fty_MPa']} / {e02['Ftu_MPa']} MPa at {m02:g} C and "
    f"{e01['Fty_MPa']} / {e01['Ftu_MPa']} MPa at {m01:g} C; the full table is in this json) and (2) meets the T6 minimums of the stock's "
    "own specification "
    "(engmat basis ASTM B221 / B241: Fty 240 / Ftu 260 MPa); otherwise T-F3 (the line-212 design change). "
    "ROUTE (ii), coupon test on the same stock (the heat / lot of the TC-01 tube and of the TC-02 bar): expose coupons in a calibrated oven "
    "(+/-3 K) at the TB part maximum of the adopted abort value, and no lower than the nominal part maximum, for the cumulative hot time of "
    f"the planned firings (at least the {LIFE}-cycle values above, plus every planned TB / abort test event at its shifted-history time); "
    "then room-temperature tensile tests (EN ISO 6892-1 or ASTM B557) on at least 3 exposed and 3 unexposed control coupons per stock, same "
    "orientation, and hardness (plus eddy-current conductivity if available) on every coupon. PASS when every exposed coupon meets the T6 "
    "minimums of the stock specification (Rp0.2, Rm and elongation); hardness and conductivity are recorded as the screening trend, not the "
    "pass rule. Optional: one hot tensile at the part maximum after the exposure, at least the engmat value at that temperature. If any "
    "exposed coupon fails, (d) stays OPEN and the design goes to T-F3. "
    "No recalled or estimated value may replace either route. Until one closes, every quoted TC-01 / TC-02 row carries (d) OPEN; in the "
    "abort search, (d) is reported OPEN per abort value with the times above.")

out = {"id": "item_c_tf1_texts_v352", "version": "v3", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {**{k: {"path": str(p), "sha256_16": s16} for k, (p, s16) in INP.items()},
                  "engmat_AL6061-T6_Fty": AL["Fty"]["src"], "engmat_AL6061-T6_Ftu": AL["Ftu"]["src"]},
       "tags": {"head_fillet_Kt": ("LITERATURE (secondary, via AMESweb citing Pilkey 2005); the Pilkey page and the T-head Kt TO-SOURCE (lead "
                                   "18:36:37Z; the file's own tag reads 'WEB-SOURCED, BOOK PAGE TO-SOURCE; T-head NOT SOURCED')"),
                "head_end_resultants": "ASSUMED (the no-spring FE head-end resultants carried over, lead 18:36:37Z)",
                "under_head_full_float": "ASSUMED (mean-pressure scaling on the spring footprint, lead 17:55:55Z F1 FLAG)"},
       "changes_vs_v2": {"C1 (g)": "route (i) spring footprint on the flat (rows v7), da 5.55-5.80 drawn (F3)",
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
       "item_C": C, "item_C_geometry_checks": geo, "T-F1": TF1, "T-F1_TB_table": tb_rows, "T-F1_engmat_10000h_values_used_by_the_cells": eng}
V2 = json.loads((T / "item_c_tf1_texts_v352_v2.json").read_text())
assert sha(T / "item_c_tf1_texts_v352_v2.json") == "0c679900bb41e408"
for k in ("C1_TC01_drawing_callout_rev5",):
    a, b = V2["item_C"][k], C[k]
    assert a[:a.index("(g) hole size")] == b[:b.index("(g) hole size")], "C1 (a)-(f) changed"
for k in ("C2_bore_lead_in_rev5", "C3_fitting_aid_GSE", "C5_record_why_not_moved", "C7_datasheet_residuals_gland1"):
    assert V2["item_C"][k] == C[k], k
assert V2["T-F1"] == TF1 and V2["T-F1_TB_table"] == tb_rows and V2["T-F1_engmat_10000h_values_used_by_the_cells"] == eng
assert V2["item_C_geometry_checks"] == geo
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
for k in ("C1_TC01_drawing_callout_rev5", "C3b_registration_shoulder_screws_GSE", "C4_assembly_step_founder_procedure", "C6_founder_action_list_related"):
    print("==", k)
    print(C[k])
print(json.dumps(C8["lead_items_18_36_37Z_item5"], indent=1))
