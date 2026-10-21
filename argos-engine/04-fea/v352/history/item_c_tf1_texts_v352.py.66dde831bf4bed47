"""Item C texts (O-ring passage over the J-FWD holes; v3.5.2 rev 5 + founder procedure) and the T-F1 founder action text, as ruled:
item C 239 (13) (lead 09:45Z), amended 10:08Z (bore-side break R0.1-R0.2), callout ruled 10:15Z, gland basis 10:10Z (240 (5), (6));
T-F1 239 (12) (lead 09:59Z: two routes, no recalled or estimated values, (d) OPEN per abort value with the time above 150 C per firing).
Mechanical, 2026-10-20, v2 (v1 script kept as item_c_tf1_texts_v352_v1.py).  Text only; the numbers come from tf1_exposure_v352_v1.json
[SIM thermal; ASSUMED TB surrogate as tagged] and engmat AL6061-T6 (10,000 h basis, LITERATURE).
v2 (lead 14:34Z): C1 (a)-(f), C2, C3, C4, C5, C6, C7 and T-F1 ACCEPTED as written in v1 (T-F1 as a GATE before the first static fire);
C1 (g) Option A ADOPTED (d5.5 +0.12/0, H12; HW-101 gauge pins GO 5.50 / NO-GO 5.62; the line-231 check uses the 5.62 pin); C1 (h)
ADOPTED (hole position 0.10 dia to A|B, spot face coaxial within 0.10 dia, datum B named on the drawing); C6 (2) carries the pins; C6 (3)
stays OPEN until the slack-fix ruling.  Nothing here changes CAD (rev 5 carries the callouts).  Writes v352/texts/item_c_tf1_texts_v352_v2.json."""
import json, hashlib, math, sys
from pathlib import Path
import numpy as np

T = Path("/home/claude/work/mechanical/v352/texts")
EXP = T / "tf1_exposure_v352_v1.json"
OUT = T / "item_c_tf1_texts_v352_v2.json"
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat
AL = engmat.MATERIALS["AL6061-T6"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def al(k, Tc):
    return float(np.interp(Tc, AL[k]["T_C"], AL[k]["v"])) / 1e6


E = json.loads(EXP.read_text())
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
    "(g) hole size (ADOPTED, lead 14:34Z, Option A): d5.5 +0.12/0 (H12). ENG-HW-101 in-service gauge pins GO 5.50 / NO-GO 5.62 (the "
    "5.68 NO-GO pin of hardware_v352 v1.4 is superseded); the line-231 post-FA-1 hole check uses the 5.62 pin. The drawn maximum 5.62 "
    "sets the head-bearing ring inner boundary (max(5.62 + 2 x 0.1 break, da 5.7 TO-VERIFY) = 5.82) and the screw float 0.397 mm of the "
    "TC-01 flat-bearing rows (rows v5). "
    "(h) hole position (ADOPTED, lead 14:34Z): position of each hole axis 0.10 dia to A|B; the d10.5 spot face coaxial with its hole "
    "within 0.10 dia. Datum B is NAMED on the drawing (the frame is 'fwd end face A, axis B'; proposal: B = the axis of the 57.25 H8 "
    "forward bore, rows v5 rev5_drawing_items). Rows v5 carry "
    "the eccentricity (float 0.397 + position 0.05) with the OD 63.5 h9 and its 0.04 runout. Drawing consistency FLAG for rev 5: the "
    "r_flat rule 31.313 +0.020/0 'from datum A' and the OD runout 0.04 'to A' are radial quantities and should read 'from / to axis B' "
    "(A is the forward end face).")
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
C["C4_assembly_step_founder_procedure"] = (
    "J-FWD build and every re-assembly: "
    "1. inspect the hole edges and the bore per C1 (e); clean. "
    "2. fit the ten ENG-TC-12 plugs in their numbered holes from outside, contour aligned, band on. "
    "3. lubricate S01 and S02 with the selected lubricant (FKM- and N2O-compatible, TO-SELECT with a datasheet; oxygen-clean per the "
    "wetted-part rule); fit them into the TC-02 grooves with an even stretch over a cone, no twist (check the mould line). "
    "4. clock TC-02 to the match marks BEFORE the rings enter the lead-in, then push it in axially without rotation until seated. "
    "5. remove the band and the plugs; look through each hole (10x loupe or borescope) for rubber debris or a cut ring; ANY debris: "
    "withdraw TC-02, replace both rings and repeat from step 1. "
    "6. fit the ten ENG-HW-101-IN718 screws per J-F1 (LOCTITE 243, 3.0 N m), then the proof / leak test.")
C["C5_record_why_not_moved"] = (
    "Parker Praedifa PTD5705-EN 2.5.2: a cross-drilled port shears the O-ring as it leaves the drilled area, and the first remedy is to "
    "reposition the holes; 2.5.6: bores 'must be removed or covered'. Moving the holes is not possible: S01 and S02 must sit between the "
    "chamber and the holes (dry holes), and TC-02 can only enter from the forward end. The internal chamfer (Fig. 2.26) and the balancing "
    "groove (Fig. 2.27) change the J-FWD wall and the plug fit contact and are NOT adopted. The fitting aid covers the holes, as 2.5.6 "
    "requires; the R0.1-R0.2 break is capped by the bearing length and the screw bending arm (an R0.4 + 0.1 break gives the FA1S hole bearing -0.070 at the nominal wall / -0.080 at the limit wall).")
C["C6_founder_action_list_related"] = (
    "(1) S01 and S02 are replaced after any FA-1-class event, together with the line-231 J-FWD inspection (lead 10:10Z rule). "
    "(2) Line-231 post-FA-1 inspection list: the ten J-FWD screws replaced; the ten holes gauged for elongation and bearing set with "
    "the HW-101 pins GO 5.50 / NO-GO 5.62 (C1 (g)); a hole that takes the 5.62 pin is rejected; hole edges and the bore within 3 mm of a "
    "hole at 10x for nicks or raised metal; S01 / S02 replaced. "
    "(3) J-FWD screw life limit: OPEN until the slack-fix ruling (the screw LCF row 183 (1)(c) is a FOUND NEGATIVE, "
    "jfwd_screw_lcf_v352_v1.json; quoted as negative, never as passing; the life-limit rows of 2(b) are in bpkg_abort_v352_v1.json).")
C["C7_datasheet_residuals_gland1"] = (
    "Gland-1 FA1S closes at MS +0.082 on FNST's one-side extrusion limit 0.30 mm (1500 psi row, no interpolation), with the full 0.2772 mm "
    "diametral gap taken as one side (nothing centres the plug), entered at the FA-1 fluid bound 93.64 bar abs = 1343 psig (the chart's "
    "own axis); Apple Rubber Illustration 5.2 halved at 1343 psi gives +0.16 (support); no back-up ring. Residual: the two makers' curves "
    "differ in shape (FNST / Apple 0.48 at 1500 psi) and neither prints a cycle, time or temperature basis.")

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

out = {"id": "item_c_tf1_texts_v352", "version": "v2", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"tf1_exposure": {"path": str(EXP), "sha256_16": sha(EXP)}, "engmat_AL6061-T6_Fty": AL["Fty"]["src"], "engmat_AL6061-T6_Ftu": AL["Ftu"]["src"]},
       "item_C": C, "item_C_geometry_checks": geo, "T-F1": TF1, "T-F1_TB_table": tb_rows, "T-F1_engmat_10000h_values_used_by_the_cells": eng}
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
print(json.dumps(geo, indent=1))
print(TF1)
