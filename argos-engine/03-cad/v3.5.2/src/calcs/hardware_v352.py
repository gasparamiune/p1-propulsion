"""Hardware list v3.5.2 = hardware_v351.json + lead CHANGELOG 206 (2b) Ti-6Al-4V screws (Mechanical, 2026-10-13, v1).
Ti only where v352/ti/ti_screws_v352_v1.json leaves no exclusion at the CONSERVATIVE 100 mm R3 distance (line of sight not credited):
HW-121 (J-FRAME-L, 157.2 mm from FD-05) and HW-123 (J-BRKT, 161.6 mm from FD-07B).  HW-126 (ICD-1L, 159.8 mm) is a Ti candidate that
needs the airframe ICD agreement: kept A4-70 here (lead: to the ICD-AIRFRAME discussion).  The 50 mm option (HW-113 / HW-115 / HW-124,
-8.4 g) was DECLINED by the lead (R3 stays 100 mm).  v1.1: thread locker LOCTITE 222 on HW-115 (EL-03 M2), lead request.
Preload kept at the v3.5.1 A4-70 value (0.65 x 450 MPa x As); torque from a torque-tension test of the anodised + lubricated Ti screw.
v1.2 (2026-10-20, lead resume items 1-3 + 11, CHANGELOG 230 / 231): HW-101 10x M5 x 10 A4-80 (J-FWD per line 231 (1): fastener count,
no case land, no spot face); HW-103 J-FD01 relocated to 3x M4 DIN 7984 A4-80 (HW-103 2x M4 x 20 + HW-103B 1x M4 x 16; the v3.5.1 lower M3 ran through the
FD-01 riser socket / FD-03 riser tube); HW-127 J-FD09 A4-80 1.8 N m (v352/jfd/joints_v352_v1.json); every screw line gets a tightening
method and a preload scatter (BOM torque + method columns)."""
import json, hashlib, copy
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "data" / "hardware_v351.json"
OUT = HERE.parent / "data" / "hardware_v352.json"
TI = {"HW-121": "J-FRAME-L 157.2 mm from FD-05", "HW-123": "J-BRKT 161.6 mm from FD-07B"}
RHO = {"A4-70": 8000.0, "A4-80": 8000.0, "A2-70": 7900.0}
d = json.loads(SRC.read_text())
o = copy.deepcopy(d)
o.update({"id": "hardware_v352", "version": "v1.1", "cad_version": "v3.5.2", "date": "2026-10-13",
          "basis": d["basis"] + " | v3.5.2: lead CHANGELOG 206 (2b) Ti-6Al-4V screws (v352/ti/ti_screws_v352_v1.json, sha256/16 recorded below)"})
tif = Path("/home/claude/work/mechanical/v352/ti/ti_screws_v352_v1.json")
o["ti_basis"] = {"file": "04-fea/v352/ti_screws_v352_v1.json", "sha256_16": hashlib.sha256(tif.read_bytes()).hexdigest()[:16],
                 "rule_R3_mm": 100.0, "strength": "DATASHEET: ASTM F468 alloy Ti 5 (R56400) Rm >= 896 MPa, Rp0.2 >= 827 MPa (TorqBolt table, "
                 "accessed 2026-10-13); Accu Ltd Grade 5 >= 895 MPa", "anti_galling": "AMS 2488 Type 2 anodise + PFPE thread lubricant; no helicoil under Ti"}
for L in o["lines"]:
    if L["id"] in TI:
        g0 = L["grade"]
        L["grade_v351"] = g0
        L["grade"] = "Ti-6Al-4V (ASTM F468 R56400)"
        L["unit_mass_g"] = round(L["unit_mass_g"] * 4430.0 / RHO[g0], 3)
        L["mass_evidence"] = f"CALC ({g0} CALC unit mass x 4430/{RHO[g0]:.0f}); DATASHEET TO-FETCH"
        L["torque_basis"] = ("v3.5.2: preload kept at the v3.5.1 A4-70 value 0.65 x 450 MPa x As; torque from a torque-tension test of the "
                             "anodised + PFPE-lubricated Ti screw (K TO-VERIFY); v3.5.1 value shown until then")
        L["status"] = "DEFINED v3.5.2 (Ti, lead 206 (2b)); " + L["status"]
        L["note"] = (L.get("note", "") + f" | v3.5.2 Ti: {TI[L['id']]} (R3 100 mm); preload over -20..+80 C in ti_screws_v352_v1.json").strip(" |")
    if L["id"] == "HW-115":            # v1.1 (lead, after CHANGELOG 209): thread locker on the EL-03 M2 holder screws
        L["thread_locker"] = ("LOCTITE 222 (Henkel; low strength, fasteners < 6.35 mm, removable with hand tools, application -55..150 C, "
                              "breakaway 6.0 N m on M10 steel; DATASHEET https://www.henkel-adhesives.com/za/en/product/threadlockers/loctite_222.html, "
                              "accessed 2026-10-13); activator need on the passive substrates (A2-70 screw, anodised 6061 tap) TO-VERIFY with Henkel")
        L["note"] = (L.get("note", "") + " | v3.5.2 v1.1: A2-70 M2 on a 1.5 mm grip keeps 2 % of the assembly preload after 7 um embedding "
                     "+ -20 C (ti_screws_v352_v1.json, DERIVED): preload alone does not hold it; thread locker specified (lead)").strip(" |")
    if L["id"] == "HW-126":
        L["note"] = (L.get("note", "") + " | v3.5.2: Ti candidate (159.8 mm from FD-07, -7.47 g) referred to the ICD-AIRFRAME discussion "
                     "(lead, after CHANGELOG 209); A4-70 until agreed").strip(" |")
# ---------------------------------------------------------------- v1.2 (2026-10-19): items 2, 3, 11 and the tightening method of every screw
import sys as _sys
_sys.path.insert(0, str(HERE))
import hardware_v351 as H                       # same CALC mass / torque rules as v3.5.1 (nominal geometry AS RECALLED, TO-VERIFY)
JF = Path("/home/claude/work/mechanical/v352/jfd/joints_v352_v1.json")
JSHA = hashlib.sha256(JF.read_bytes()).hexdigest()[:16]
o.update({"version": "v1.2", "date": "2026-10-20",
          "basis": o["basis"] + " | v1.2 (2026-10-20): J-FWD HW-101 10x M5 x 10 A4-80 (item 11 per lead 231 (1)), J-FD01 3x M4 A4-80 (item 2), "
                   "J-FD09 A4-80 1.8 N m (item 3), tightening method + preload scatter per screw line (04-fea/v352/joints_v352_v1.json)"})
o["rules"]["tightening_methods"] = {
    "M-T1": "torque-controlled: calibrated setting torque wrench (ISO 6789-1 Type II; tool tolerance per its class, TO-VERIFY at purchase), "
            "screws snugged then taken to the final torque in one pass, opposite-pair / cross order on multi-screw patterns; threads clean, "
            "lubrication state as on the drawing (the K basis); N2O-system joints: oxygen-compatible PFPE grease only",
    "M-T2": "as M-T1 with a calibrated setting torque screwdriver (ISO 6789-1 Type II) for final torques below 1 N m",
    "M-T1L": "as M-T1 (M-T2 tool below 1 N m) on threads coated with the thread locker of the line (cure per the maker sheet "
             "before load); torque applied on the wet locker",
    "M-T1Ti": "as M-T1; torque from a torque-tension test of the anodised (AMS 2488 Type 2) + PFPE-lubricated Ti screw (K TO-VERIFY); "
              "the v3.5.1 A4-70 torque shown until that test",
    "M-NONE": "not a torque joint (dowel, insert, seal, washer, clip, consumable)"}
o["rules"]["preload_scatter"] = ("+/-25 % about F = T / (K d), K 0.20 (both ASSUMED; the FEA3D F4 basis, alpha_A = 1.25 / 0.75 = 1.67): the "
                                  "joint margins of 04-fea/assembly3d F4 and 04-fea/v352/joints_v352_v1.json use it; a torque-tension test "
                                  "on the original parts that shows a wider scatter re-opens those joints")
o["rules"]["joint_basis_v352"] = {"file": "04-fea/v352/joints_v352_v1.json", "sha256_16": JSHA}
NEW103B = None
for L in o["lines"]:
    if L["id"] == "HW-101":                     # lead CHANGELOG 231 (1): J-FWD sized at FA1S SF 1.0 on (i)-(iii); fastener count before case wall
        L["qty"] = 10
        L["length_mm"] = 10
        L["unit_mass_g"] = round(H.screw_mass_g("ISO 7380-1", 5.0, 10, "A4-80"), 3)
        L["L_basis"] = ("v3.5.1 geometry kept: case wall 3.125 at the 5.5 hole (no spot face; the button head seats on the OD r 31.75) + plug "
                        "gap 0.025 + engagement 6.85 in the TC-02 M5-6H tap (drill 4.2 x 9.0, full thread 8.0) = 10.0; 10 holes at az 18 + 36k deg, "
                        "match-drilled TC-01 / TC-02")
        L["status"] = "DEFINED v3.5.2 (lead CHANGELOG 231 (1); FEA3D one-sector contact sub-model re-check pending)"
        L["action"] = ("v3.5.1 'spot face TO-DEFINE' CLOSED: no spot face (it would cut the case bearing to +0.19 / -0.05 at 10 / 8 screws); "
                       "inspect-or-replace after any Pc excursion above 60 bar abs (v352/jfwd/jfwd_v352_v1.json)")
        L["torque_basis"] = L["torque_basis"] + " | v3.5.2: unchanged (preload is not a strength item in this bearing-type joint)"
        L["note"] = (L.get("note", "") + f" | v3.5.2 (lead 231 (1)): 8 -> 10 screws; FA1S 151.04 bar abs SF 1.0 min MS +0.077 (screw shear yield on "
                     "the minor area at 45 C; +0.137 at 20 C), case bearing +0.34 / +0.65, TC-02 tap mouth Neuber +0.62 (04-fea/v352/jfwd_v352_v1.json)").strip(" |")
    if L["id"] == "HW-103":
        L.update({"item": "FD-01 inlet block screw, lower pair (FD-01 ears into the TC-02 flat r 29.5)", "size": "M4", "length_mm": 20,
                  "grade": "A4-80", "qty": 2,
                  "L_basis": ("v3.5.2: FD-01 ear grip 11.5 (cbore d8 seat r 41.0 to the flat r 29.5) + engagement 8.5 (2.1 d) in the TC-02 M4 "
                              "tap (drill 3.3 x 10.5, full thread 9.0: tip 0.5 short of the thread end) = 20.0; y +/-8.5 at zb+5 beside the "
                              "riser socket (1.41 mm FD-01 web)"),
                  "unit_mass_g": round(H.screw_mass_g("DIN 7984", 4.0, 20, "A4-80"), 3),
                  "torque_Nm": 1.8, "torque_basis": f"DESIGN v3.5.2 (04-fea/v352/joints_v352_v1.json {JSHA}: F4 bounding MS +0.122 / Phi0.2 "
                                                     "+0.403 at +/-25 %; window 1.5-2.0 N m: 1.5 N m +0.198 (slip), 2.1 N m -0.003)",
                  "status": "DEFINED v3.5.2 (FEA3D re-check pending)",
                  "action": "the v3.5.1 J-FD01 (2x M3 A4-70 x 16, 1.0 N m) could not be assembled: lower screw axis through the FD-01 riser socket "
                            "and the FD-03 riser tube (v352/jfd/probe_fd01.py); replaced",
                  "note": "lead 2026-10-19 item 2 (FEA3D F4 -0.41 / -0.20 on the v3.5.1 joint)"})
        NEW103B = dict(L)
    if L["id"] == "HW-127":
        L.update({"grade": "A4-80", "torque_Nm": 1.8, "unit_mass_g": round(H.screw_mass_g("ISO 4762", 4.0, 12, "A4-80"), 3),
                  "torque_basis": f"DESIGN v3.5.2 (04-fea/v352/joints_v352_v1.json {JSHA}: F4 bounding MS EI 0.184 +0.476 / EI 0.5 +0.221; "
                                  "Phi0.2 +0.66 / +0.586 at +/-25 %; 1.5 N m: EI 0.5 slip -0.241, A4-70 at 1.8 N m: EI 0.5 -0.085)",
                  "status": "DEFINED v3.5.2 (FEA3D re-check pending)",
                  "note": (L.get("note", "") + " | v3.5.2 item 3: A4-70 2.05 N m gave F4 -0.167 (EI 0.5) / -0.011 (EI 0.184)").strip(" |")})
idx = [i for i, L in enumerate(o["lines"]) if L["id"] == "HW-103"][0]
NEW103B.update({"id": "HW-103B", "item": "FD-01 inlet block screw, upper (FD-01 body into the TC-02 flat r 29.5, above the passages)",
                "length_mm": 16, "qty": 1, "unit_mass_g": round(H.screw_mass_g("DIN 7984", 4.0, 16, "A4-80"), 3),
                "L_basis": ("v3.5.2: FD-01 grip 10.5 (cbore d8 seat r 40.0 to the flat r 29.5) + engagement 5.5 (1.38 d, below the 1.5 d "
                            "rule: host-thread strip checked in joints_v352_v1.json, not governing) in the TC-02 M4 tap (drill 3.3 x 7.5, full "
                            "thread 6.5: tip 1.0 short of the thread end) = 16.0; y 0 at zb+24"), "action": "", "note": "lead 2026-10-19 item 2"})
o["lines"].insert(idx + 1, NEW103B)
# ---------------------------------------------------------------- v1.3 (2026-10-20): lead CHANGELOG 234 (1)(b)/(c) J-FWD preload re-check
JP = Path("/home/claude/work/mechanical/v352/jfwd/jfwd_preload_v352_v1.json")
JPD = json.loads(JP.read_text())
JPSHA = hashlib.sha256(JP.read_bytes()).hexdigest()[:16]
SEL = JPD["selected"]
o.update({"version": "v1.3", "basis": o["basis"] + f" | v1.3 (2026-10-20): HW-101 {SEL['torque_Nm']:g} N m M-T1L LOCTITE 243 (lead 234 (1)(b)/(c); "
                                                    f"04-fea/v352/jfwd_preload_v352_v1.json {JPSHA})"})
for L in o["lines"]:
    if L["id"] == "HW-101":
        lc2, fa = SEL["LC2_margins"], SEL["FA1S_margins"]
        L["torque_Nm"] = SEL["torque_Nm"]
        L["torque_basis"] = (f"DESIGN v3.5.2 (lead 234 (1)(b); 04-fea/v352/jfwd_preload_v352_v1.json {JPSHA}): 5.53 N m failed the LC2 combined "
                             "check (-0.031 at 78.6 C, max preload +25 %); "
                             f"{SEL['torque_Nm']:g} N m -> F_nom {SEL['preload_N']['F_nom']:.0f} N, range {SEL['preload_N']['F_min_-25pc']:.0f}-"
                             f"{SEL['preload_N']['F_max_+25pc']:.0f} N (K 0.20, +/-25 %, ASSUMED); LC2 SF 1.5/2.0 yield combined "
                             f"{lc2['LC2_78.6C_ruled']['MS_y_combined']:+.3f} (78.6 C) / {lc2['LC2_100C_thermal']['MS_y_combined']:+.3f} (100 C bound + "
                             f"thermal rise), ult interaction {lc2['LC2_78.6C_ruled']['MS_u_interaction']:+.3f}; FA1S ult interaction "
                             f"{fa['MS_u_interaction_maxpreload_thermal']:+.3f}, shear-only yield {fa['MS_y_shear_only_minor']:+.3f} (relaxation argument)")
        L["thread_locker"] = ("LOCTITE 243 (Henkel, medium strength) or an equivalent medium-strength anaerobic locker rated -55..+180 C "
                              "(DATASHEET-distributor: Hoffmann Group 083301 243, https://www.hoffmann-group.com/MT/en/mbbridge/p/083301-243, "
                              "accessed 2026-10-20; Henkel TDS new formulation 03-2010 https://static.rapidonline.com/pdf/12-4132o_v1.pdf, accessed "
                              "2026-10-20: works on passive substrates; hot strength charts and the wet-locker K TO-VERIFY); joint max 119.7 C (SIM)")
        L["action"] = (L["action"] + " | v1.3 intervals (ASSUMED until a test): replace all 10 HW-101 at every J-FWD disassembly and at the latest "
                       "every 10 firings, and after any Pc above 60 bar abs; gauge the TC-01 holes (pins GO 5.50 / NO-GO 5.68) and the TC-02 taps "
                       "(M5-6H GO / NO-GO) after firing 1, every 5 firings, at every HW-101 replacement and after any Pc above 45 bar abs; "
                       "torque-tension test of HW-101 with the locker in a 6061-T6 coupon TO-DO (acceptance: max preload at "
                       f"{SEL['torque_Nm']:g} N m <= {SEL['K_validity']['LC2_78.6C_thermal'][1]:.0f} N)")
        L["status"] = "DEFINED v3.5.2 (lead CHANGELOG 231 (1), 234 (1)(b)/(c); FEA3D one-sector contact sub-model re-check pending)"
        # lead 2026-10-20 (after 234): oxygen service of the locker on the N2O-wetted, oxygen-clean TC-02, and the founder test J-F1
        TW = json.loads(Path("/home/claude/work/mechanical/v352/checks/test_interim352b_v1.json").read_text())["tc02_jfwd_tap_walls"]
        tw = {t["az_deg"]: t["min_wall_mm_from_M5_major"] for t in TW["taps"]}
        tw_num = [v for v in tw.values() if not isinstance(v, str)]
        L["oxygen_service"] = (
            "DRY SIDE (CAD, v3.5.2): all 10 J-FWD taps (M5-6H, drill 4.2 x 9.0 radial at z 127.513, M5 major z 125.01-130.01) lie forward "
            "of both AS568-226 bore seals (glands g1 z 106.51-111.36, g2 z 114.36-119.21; chamber side = aft of the injector face z 103.51): "
            "5.8 mm from the M5 major to the g2 forward wall, in the dry plug / bore annulus that is closed only by the head shoulder on the "
            "case end (ambient). No tap breaks into any N2O, torch or Pc passage: minimum wall from the M5 major diameter to any other "
            f"TC-02 cavity {min(tw_num):.3f} mm (torch passage, az 18 / 342), {tw.get(126.0)} mm (az 126), > 4.0 mm at the other 7 "
            "(checks/test_interim352b_v1.json, CAD probe bisection; repeated on the final set). Exposure only after a double-seal "
            "failure, then to chamber gas. So the anaerobic methacrylate locker is acceptable on this joint; no tap needs a "
            "non-adhesive locking method")
        L["assembly_note"] = (
            "Oxygen service (TC-02 N2O-wetted, oxygen-clean, Krytox only): apply LOCTITE 243 only AFTER the oxygen cleaning of TC-01 / TC-02 "
            "and after the plug is installed with its O-rings; apply it to the screw thread only (the first 3-4 engaged threads, one small "
            "drop per screw, no excess), never into the tap or the TC-01 hole first; wipe any squeeze-out at the TC-01 OD with a "
            "lint-free wipe; keep the locker, the wipes and gloved fingers away from the seal lands, glands, the manifold bore, the torch "
            "and Pc passages and every other wetted bore (wetted ports capped during the operation); torque M-T1L on the wet locker, cure "
            "per the maker sheet before any pressurisation; on removal clean the cured locker out of the taps by a thread chaser only (no "
            "re-tap), then gauge (M5-6H GO / NO-GO) before re-installation")
        L["test"] = {
            "id": "J-F1", "owner": "founder (lead 2026-10-20 founder test list)",
            "what": ("torque-tension of ISO 7380-1 M5 x 10 A4-80 (flight lot) with LOCTITE 243 (flight lot) into a 6061-T6 M5-6H tap "
                     "(drill 4.2 x 9.0, 8.0 full thread, TC-02 surface state) through a 3.125 mm 6061-T6 wall coupon with a 5.5 hole and the "
                     "R 31.75 seat, preload by a through-hole load washer (grip restored) or ultrasonic elongation, at 4.0 N m by M-T1L"),
            "samples": "10 screws, one per fresh tap; plus 3 of the taps re-used 3 times after chaser cleaning (the replacement procedure): 19 readings",
            "acceptance": ("maximum preload <= 6144 N on every reading (K >= 0.130: LC2 combined check with the thermal rise at 78.6 C); "
                           "minimum preload >= 3000 N on every reading (K <= 0.267: the 6.0 kN friction / retention figure); a reading "
                           "below 3000 N does not reopen the strength margins (bearing-type joint) but re-issues the retention statement and "
                           "halves the gauge interval"),
            "optional_J-F1b": ("5 of the J-F1 joints with the load washer kept in: 10 oven cycles 20 -> 120 C, residual preload and "
                               "breakaway torque recorded; sets the 10-firing HW-101 replacement interval (ASSUMED until then)")}
        L["note"] = (L.get("note", "") + f" | v1.3: at {SEL['torque_Nm']:g} N m the friction capacity at F_min cold (6.00 kN, mu 0.2 ASSUMED) is "
                     "below the LC1 joint load 6.44 kN: the joint can settle into bearing at a normal firing (shear pins; LC1 case bearing "
                     "41 MPa); TC-02 internal-thread shear at the max preload + thermal rise: soak 119.7 C "
                     f"{SEL['TC02_internal_thread_shear']['soak_119.7C']['MS_y']:+.3f} (5.53 N m: "
                     f"{SEL['TC02_internal_thread_shear']['at_5.53Nm_soak_MS_y']:+.3f})").strip(" |")
# ---------------------------------------------------------------- v1.4 (2026-10-20): lead 'J-FWD 3.0 N m ACCEPTED' (after the gap-variant soak
# check: 4.0 N m fails the GVLO soak screw tension); J-F1 acceptance from all checks incl. the gap variants; 2.5 N m fallback rows
JP2 = Path("/home/claude/work/mechanical/v352/jfwd/jfwd_preload_v352_v2.json")
JPD2 = json.loads(JP2.read_text())
JPSHA2 = hashlib.sha256(JP2.read_bytes()).hexdigest()[:16]
SEL2, JF1, FB = JPD2["selected"], JPD2["J-F1_acceptance"], JPD2["fallback_2.5Nm"]
VR = JPD2["selected_variant_rows"]["rows"]
JVSHA = JPD2["selected_variant_rows"]["source"].split()[-1]
T2 = SEL2["torque_Nm"]
o.update({"version": "v1.4", "basis": o["basis"] + f" | v1.4 (2026-10-20): HW-101 {T2:.1f} N m M-T1L LOCTITE 243 (lead: 'J-FWD 3.0 N m ACCEPTED'; "
                                                    f"04-fea/v352/jfwd_preload_v352_v2.json {JPSHA2}, jfwd_variant_v352_v2.json {JVSHA}); "
                                                    f"J-F1 acceptance <= {JF1['max_preload_N']:.0f} N"})
for L in o["lines"]:
    if L["id"] == "HW-101":
        lc2, fa = SEL2["LC2_margins"], SEL2["FA1S_margins"]
        L["torque_Nm"] = T2
        L["torque_basis"] = (
            f"DESIGN v3.5.2 (lead 2026-10-20 'J-FWD 3.0 N m ACCEPTED'; 04-fea/v352/jfwd_preload_v352_v2.json {JPSHA2}, jfwd_variant_v352_v2.json "
            f"{JVSHA}): 5.53 N m failed the LC2 combined check (-0.031 at 78.6 C, max preload +25 %); 4.0 N m (v1.3) fails the GVLO gap-variant "
            f"soak screw tension ({JPD2['selection_basis'].split('MS ')[1].split(' ')[0]}); {T2:.1f} N m -> F_nom {SEL2['preload_N']['F_nom']:.0f} N, range "
            f"{SEL2['preload_N']['F_min_-25pc']:.0f}-{SEL2['preload_N']['F_max_+25pc']:.0f} N (K 0.20, +/-25 %, ASSUMED); LC2 SF 1.5/2.0 yield combined "
            f"{lc2['LC2_78.6C_ruled']['MS_y_combined']:+.3f} (78.6 C) / {lc2['LC2_100C_thermal']['MS_y_combined']:+.3f} (100 C bound + thermal rise), ult "
            f"interaction {lc2['LC2_78.6C_ruled']['MS_u_interaction']:+.3f}; gap variants, every B1 frame: LC2 yield >= "
            f"{min(VR[k]['LC2_MS_y_min'] for k in VR):+.3f}, soak screw tension GVLO {VR['GVLO_ksh_x1']['soak_MS_y_min']:+.3f} (k_sh x0.5 "
            f"{VR['GVLO_ksh_x0.5']['soak_MS_y_min']:+.3f}, x1.5 {VR['GVLO_ksh_x1.5']['soak_MS_y_min']:+.3f}, shown as found), GVHI "
            f"{VR['GVHI_ksh_x1']['soak_MS_y_min']:+.3f}, merged {VR['merged_ksh_x1']['soak_MS_y_min']:+.3f}; FA1S ult interaction "
            f"{fa['MS_u_interaction_maxpreload_thermal']:+.3f}, shear-only yield {fa['MS_y_shear_only_minor']:+.3f} (relaxation argument)")
        L["thread_locker"] = ("LOCTITE 243 (Henkel, medium strength) or an equivalent medium-strength anaerobic locker rated -55..+180 C "
                              "(DATASHEET-distributor: Hoffmann Group 083301 243, https://www.hoffmann-group.com/MT/en/mbbridge/p/083301-243, "
                              "accessed 2026-10-20; Henkel TDS new formulation 03-2010 https://static.rapidonline.com/pdf/12-4132o_v1.pdf, accessed "
                              "2026-10-20: works on passive substrates; hot strength charts and the wet-locker K TO-VERIFY); "
                              + SEL2["thread_locker"].split("; ", 1)[1])
        L["action"] = (L["action"].split(" | v1.3 intervals")[0] + f" | v1.4 intervals (ASSUMED until a test): replace all 10 HW-101 (M-T1L at {T2:.1f} "
                       "N m, fresh LOCTITE 243) at every J-FWD disassembly and at the latest every 10 firings, and after any Pc above 60 bar abs; "
                       "gauge the TC-01 holes (pins GO 5.50 / NO-GO 5.68) and the TC-02 taps (M5-6H GO / NO-GO) after firing 1, every 5 firings, at "
                       "every HW-101 replacement and after any Pc above 45 bar abs; torque-tension test J-F1 TO-DO (acceptance: max preload at "
                       f"{T2:.1f} N m <= {JF1['max_preload_N']:.0f} N, min >= {JF1['min_preload_N']:.0f} N)")
        L["status"] = "DEFINED v3.5.2 (lead CHANGELOG 231 (1), 234 (1)(b)/(c), 2026-10-20 3.0 N m decision; FEA3D one-sector contact sub-model re-check pending)"
        L["test"]["what"] = L["test"]["what"].replace("at 4.0 N m by M-T1L", f"at {T2:.1f} N m by M-T1L")
        assert f"at {T2:.1f} N m by M-T1L" in L["test"]["what"]
        L["test"]["acceptance"] = (
            f"maximum preload <= {JF1['max_preload_N']:.0f} N on every reading (K >= {JF1['K_min']:.4f}; governing: {JF1['governing']}; with the "
            f"case-shell stiffness k_sh x1.5 the limit is {JF1['k_sh_x1.5_sensitivity']['max_preload_N']:.0f} N, K >= "
            f"{JF1['k_sh_x1.5_sensitivity']['K_min']:.4f}); minimum preload >= {JF1['min_preload_N']:.0f} N on every reading (K <= "
            f"{JF1['K_max']:.3f}: the -25 % scatter bound of the retention statement); a reading below the minimum does not reopen the strength "
            "margins (bearing-type joint) but re-issues the retention statement and halves the gauge interval; a reading above the maximum "
            f"goes to the lead: the {FB['torque_Nm']:g} N m fallback keeps the same {FB['J-F1_limit']['max_preload_N']:.0f} N limit (K >= "
            f"{FB['J-F1_limit']['K_min']:.4f})")
        L["fallback_2.5Nm"] = {
            "torque_Nm": FB["torque_Nm"], "preload_N": FB["preload_N"], "LC2_margins": FB["LC2_margins"], "FA1S_margins": FB["FA1S_margins"],
            "LC1_bearing": {"friction_kN": FB["LC1_bearing_retention"]["friction_mu0.2_kN"], "LC1_joint_load_kN": FB["LC1_bearing_retention"]["LC1_joint_load_kN"],
                            "case_bearing_MS_y_u": [FB["LC1_bearing_retention"]["LC1_case_bearing"]["case_MS_y"], FB["LC1_bearing_retention"]["LC1_case_bearing"]["case_MS_u"]]},
            "soak_variant_screw_tension_MS_y": FB["soak_variant_screw_tension_MS_y"], "J-F1_limit": FB["J-F1_limit"],
            "source": f"04-fea/v352/jfwd_preload_v352_v2.json {JPSHA2}"}
        L["note"] = (L.get("note", "").split(" | v1.3:")[0] + f" | v1.4: at {T2:.1f} N m the friction capacity (mu 0.2 ASSUMED) is "
                     f"{SEL2['retention']['friction_mu0.2_ASSUMED_kN']['F_min_cold']:.2f} kN at F_min and "
                     f"{SEL2['retention']['friction_mu0.2_ASSUMED_kN']['F_nom_cold']:.2f} kN at F_nom (cold), both below the LC1 joint load "
                     f"{SEL2['retention']['joint_load_kN']['LC1_25.01bar']:.2f} kN: the joint settles into bearing at a normal firing (shear pins; LC1 "
                     "case bearing 41 MPa); TC-02 internal-thread shear at the max preload + thermal rise: soak 119.7 C "
                     f"{SEL2['TC02_internal_thread_shear']['soak_119.7C']['MS_y']:+.3f}, gap variants min "
                     f"{min(VR[k]['thread_MS_y_min'] for k in VR if k.endswith('_ksh_x1')):+.3f} (5.53 N m soak: "
                     f"{SEL2['TC02_internal_thread_shear']['at_5.53Nm_soak_MS_y']:+.3f})").strip(" |")
# ---------------------------------------------------------------- v1.5 (2026-10-20): J-FWD head seat (a) d10.5 spot face ADOPTED (lead 07:21Z)
# text only: L basis, action, status, note and the J-F1 coupon seat; no torque, mass, quantity or acceptance change
JS = Path("/home/claude/work/mechanical/v352/jfwd/jfwd_seat_v352_v1.json")
JE = Path("/home/claude/work/mechanical/v352/jfwd/jfwd_embed_v352_v1.json")
JSD, JED = json.loads(JS.read_text()), json.loads(JE.read_text())
JSSHA, JESHA = hashlib.sha256(JS.read_bytes()).hexdigest()[:16], hashlib.sha256(JE.read_bytes()).hexdigest()[:16]
o.update({"version": "v1.5", "basis": o["basis"] + " | v1.5 (2026-10-20): J-FWD head seat (a) d10.5 spot face ADOPTED (lead 07:21Z): HW-101 L basis, "
                                                  f"action, status, note and the J-F1 coupon seat restated (04-fea/v352/jfwd_seat_v352_v1.json {JSSHA}, "
                                                  f"jfwd_embed_v352_v1.json {JESHA}); no torque, mass, quantity or acceptance change"})
for L in o["lines"]:
    if L["id"] == "HW-101":
        cn, cl = JSD["tc01_seat_cells"]["abs_nominal_wall"], JSD["tc01_seat_cells"]["abs_drawing_limit_wall"]
        eg, hd, fe = JSD["tc02_engagement"], JSD["flat_seat_head_bearing"], JSD["FE_beside"]["TC01_seat_FA1S"]
        mn = JED["in_service_minimum_after_embedding"]["a_spot_face|basis_um|CAD_nominal_js4"]
        L["L_basis"] = (f"v3.5.2 head seat (a) (lead 07:21Z): the button head seats on a d10.5 flat spot face at r 31.313 (TC-01 drawing; depth 0.437 at "
                        f"the screw axis): case wall {cn['t_wall_at_hole_mm']:.3f} at the 5.5 hole + plug gap 0.025 (CAD; 0.040-0.078 on the drawing, H8 / f7) "
                        f"+ engagement {eg['L_e_CAD_mm']:.3f} (drawing {eg['L_e_drawing_mm'][0]:.3f}-{eg['L_e_drawing_mm'][1]:.3f}) in the TC-02 M5-6H tap (drill "
                        f"4.2 x 9.0, full thread 8.0: tip {eg['tip_short_of_full_thread_end_mm_CAD']:.2f} short of the full-thread end) = 10.0; 10 holes at az "
                        "18 + 36k deg, match-drilled TC-01 / TC-02 (the v1.2-v1.4 basis, wall 3.125 with the head on the OD r 31.75 and engagement 6.85, is "
                        "superseded)")
        old = "v3.5.1 'spot face TO-DEFINE' CLOSED: no spot face (it would cut the case bearing to +0.19 / -0.05 at 10 / 8 screws); "
        assert L["action"].startswith(old), L["action"][:120]
        L["action"] = ("v3.5.1 'spot face TO-DEFINE': ADOPTED as head seat (a), d10.5 flat at r 31.313 (lead 07:21Z, on FEA3D's [DERIVED] FA1S seat "
                       "checks; the line-contact seat on the R31.75 OD was class DC, CHANGELOG 236 (12)); the v1.2-v1.4 'CLOSED: no spot face' is "
                       "superseded; " + L["action"][len(old):])
        L["status"] = ("DEFINED v3.5.2 (lead CHANGELOG 231 (1), 234 (1)(b)/(c), 2026-10-20 3.0 N m decision; head seat (a) adopted 07:21Z; FEA3D's "
                       "mu 0.2 seat run on the rev-4 TC-01 (PRELOAD, SOAK70 / SOAK, FA1S, LC2N) closes the TC-01 cells: pending)")
        L["note"] = (L["note"] + f" | v1.5 head seat (a), hand at FA1S 151.04 bar abs SF 1.0, 45.6 C, V {cn['V_per_screw_N']:.1f} N (04-fea/v352/"
                     f"jfwd_seat_v352_v1.json {JSSHA}): case bearing {cn['hole_bearing']['MS_y']:+.3f} / {cn['hole_bearing']['MS_u']:+.3f} at the wall "
                     f"{cn['t_wall_at_hole_mm']:.3f} ({cl['hole_bearing']['MS_y']:+.3f} / {cl['hole_bearing']['MS_u']:+.3f} at the drawing-limit wall "
                     f"{cl['t_wall_at_hole_mm']:.3f}), shear-out {cn['shear_out']['MS_y']:+.3f} / {cn['shear_out']['MS_u']:+.3f}, ligament Pm+Pb "
                     f"{cn['ligament_PmPb']['MS_y']:+.3f} / {cn['ligament_PmPb']['MS_u']:+.3f}, flat-seat head bearing {hd['FA1S']['MS_y']:+.2f} (soak "
                     f"{hd['soak_first_firing_js4_consistent']['MS_y']:+.2f}); FE (FEA3D, [DERIVED]): bearing {fe['hole_bearing_MS'][0]:+.3f} / "
                     f"{fe['hole_bearing_MS'][1]:+.3f}, ligament {fe['seat_ligament_PmPb_MS'][0]:+.3f} / {fe['seat_ligament_PmPb_MS'][1]:+.3f}, shear-out bound "
                     f"{fe['shear_out_bound_MS']:+.3f}, band Neuber {fe['band_neuber_MS_membrane_bending2'][0]:+.3f} / {fe['band_neuber_MS_membrane_bending2'][1]:+.3f}; "
                     "screw rows unchanged by the seat; preload after flat-seat embedding (VDI 2230 f_Z 8 um basis, js4-consistent stiffness; 04-fea/v352/"
                     f"jfwd_embed_v352_v1.json {JESHA}): F_min {mn['F_min_inst_N']} N -> {mn['F_cold_after_embedding_N']} N cold, "
                     f"{mn['F_min_any_frame_N']} N minimum in the burn (CAD gap 0.025, {mn['at']['bound']} {mn['at']['t_s']:.1f} s) against the "
                     f"{mn['need_fit_closed_cold_N']} N fit-closing need (MS {mn['MS_vs_fit_closing_cold']:+.3f}): the head stays seated, the fit is not "
                     "held closed at F_min (bearing-type joint)")
        w0 = "through a 3.125 mm 6061-T6 wall coupon with a 5.5 hole and the R 31.75 seat"
        assert w0 in L["test"]["what"], L["test"]["what"]
        L["test"]["what"] = L["test"]["what"].replace(w0, "through a 2.69 mm 6061-T6 wall coupon with a 5.5 hole and the head seat (a): a d10.5 flat, Ra 1.6 "
                                                          "max, square to the hole within 0.05 (the TC-01 spot-face state; the under-head friction is part "
                                                          "of K)")
# v1.5 HW-150 (text only, 2026-10-20 ~08:15Z): the AS568-226 size text carried the -225 ID (47.22, AS RECALLED in hardware_v351.py); corrected
# to the sourced dimensions used by 04-fea/v352/gland_fwd_v352_v1.json.  The CALC unit mass is HELD at the v1.4 value (no mass change in v1.5):
# the torus on the sourced ID is stated beside it for the lead's ruling (it moves the massprops hardware sum, max(0.20 kg, CALC), by +0.37 g).
FNST = ("Freudenberg-NOK Sealing Technologies, 'O-Ring Design Quick Reference', p. 16 (AS568-226: ID 1.984 +/- 0.018 in, CS 0.139 +/- 0.004 in), "
        "https://fst.com/~/media/files/fst,-d-,com/markets/mobility/broschueren/fnst%20o-ring%20reference%20as568%20sizes.ashx, accessed 2026-10-20")
import math
for L in o["lines"]:
    if L["id"] == "HW-150":
        assert L["size"] == "-226 (ID 47.22 x CS 3.53 mm, AS RECALLED)", L["size"]
        m_src = math.pi * (50.39 + 3.53) * math.pi / 4.0 * 3.53 ** 2 * 1e-9 * 1900.0 * 1e3
        L["size"] = "-226 (ID 50.39 +/- 0.46 x CS 3.53 +/- 0.10 mm, DATASHEET: " + FNST + ")"
        L["note"] = (L["note"] + " | v1.5: size text corrected (v1.0-v1.4 '-226 (ID 47.22 x CS 3.53 mm, AS RECALLED)': 47.22 is the -225 ID); unit "
                     f"mass {L['unit_mass_g']:.3f} g HELD (CALC on the superseded ID; torus on the sourced ID x FKM 1900 ASSUMED = {m_src:.3f} g, "
                     f"{m_src - L['unit_mass_g']:+.3f} g per ring, {2 * (m_src - L['unit_mass_g']):+.2f} g for the 2 rings): carried only on the lead's "
                     "ruling (massprops / massdelta re-run); the other AS568 sizes of this list stay AS RECALLED (TO-SOURCE)")
        L["mass_evidence"] = L["mass_evidence"] + f" | v1.5: HELD on the superseded ID 47.22 (sourced-ID torus {m_src:.3f} g, not carried)"
o["basis"] = o["basis"] + (" | v1.5 HW-150: AS568-226 size text corrected to the sourced ID 50.39 / CS 3.53 (FNST p. 16; was the -225 ID 47.22, "
                           "AS RECALLED); unit mass held, +0.37 g for the 2 rings stated for the lead's ruling")
TQ_METHOD = {}
for L in o["lines"]:
    if L["kind"] != "screw":
        L["tightening_method"], L["preload_scatter"] = "M-NONE", ""
        continue
    t = L.get("torque_Nm")
    if str(L.get("grade", "")).startswith("Ti-6Al-4V"):
        m = "M-T1Ti"
    elif L.get("thread_locker") or "Loctite" in L.get("note", "") or L["id"] == "HW-114":
        m = "M-T1L"
    elif t is not None and t < 1.0:
        m = "M-T2"
    else:
        m = "M-T1"
    L["tightening_method"] = m
    L["preload_scatter"] = "+/-25 % (ASSUMED, K 0.20)"
    TQ_METHOD[L["id"]] = m
o["n_lines"] = len(o["lines"])
o["n_items"] = sum(L["qty"] for L in o["lines"])
byg = {}
tot = 0.0
for L in o["lines"]:
    if L.get("unit_mass_g") is not None:
        m = L["unit_mass_g"] * L["qty"]
        byg[L["group"]] = byg.get(L["group"], 0.0) + m
        tot += m
o["calc_mass_by_group_g"] = {k: round(v, 2) for k, v in byg.items()}
o["calc_mass_total_g"] = round(tot, 2)
o["delta_vs_v351_g"] = round(tot - d["calc_mass_total_g"], 2)
OUT.write_text(json.dumps(o, indent=1))
print(OUT, o["calc_mass_by_group_g"], o["calc_mass_total_g"], "delta", o["delta_vs_v351_g"], hashlib.sha256(OUT.read_bytes()).hexdigest()[:16])
