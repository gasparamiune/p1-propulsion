"""Hardware list v3.5.2 = hardware_v351.json + lead CHANGELOG 206 (2b) Ti-6Al-4V screws (Mechanical, 2026-10-13, v1).
Ti only where v352/ti/ti_screws_v352_v1.json leaves no exclusion at the CONSERVATIVE 100 mm R3 distance (line of sight not credited):
HW-121 (J-FRAME-L, 157.2 mm from FD-05) and HW-123 (J-BRKT, 161.6 mm from FD-07B).  HW-126 (ICD-1L, 159.8 mm) is a Ti candidate that
needs the airframe ICD agreement: kept A4-70 here (lead: to the ICD-AIRFRAME discussion).  The 50 mm option (HW-113 / HW-115 / HW-124,
-8.4 g) was DECLINED by the lead (R3 stays 100 mm).  v1.1: thread locker LOCTITE 222 on HW-115 (EL-03 M2), lead request.
Preload kept at the v3.5.1 A4-70 value (0.65 x 450 MPa x As); torque from a torque-tension test of the anodised + lubricated Ti screw.
v1.2 (2026-10-20, lead resume items 1-3 + 11, CHANGELOG 230 / 231): HW-101 10x M5 x 10 A4-80 (J-FWD per line 231 (1): fastener count,
no case land, no spot face); HW-103 J-FD01 relocated to 3x M4 DIN 7984 A4-80 (HW-103 2x M4 x 20 + HW-103B 1x M4 x 16; the v3.5.1 lower M3 ran through the
FD-01 riser socket / FD-03 riser tube); HW-127 J-FD09 A4-80 1.8 N m (v352/jfd/joints_v352_v1.json); every screw line gets a tightening
method and a preload scatter (BOM torque + method columns).
v1.7 (2026-10-20, lead 16:53Z R2 / R3, 17:55:55Z F1-F5, 18:36:37Z): J-FWD route (i): HW-101 = ENG-HW-101-IN718 (F3 head form, M5 x 10.7, J-F1 lot
torque <= 3750 N, method M-T1J with the C4 registration, single-use) and HW-170 disc spring x 10; numbers read from the accepted v352/jfwd files."""
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
# ---------------------------------------------------------------- v1.6 (2026-10-20): lead 08:40Z item 3 'HW-150 sourced size (AS568-226, ID 50.39 x
# CS 3.53) accepted. Publish massdelta v7 (+0.37 g)': the HW-150 CALC unit mass moves to the torus on the sourced ID (FKM 1900 kg/m3 ASSUMED).
for L in o["lines"]:
    if L["id"] == "HW-150":
        m_old = L["unit_mass_g"]
        m_src = math.pi * (50.39 + 3.53) * math.pi / 4.0 * 3.53 ** 2 * 1e-9 * 1900.0 * 1e3
        L["unit_mass_g"] = round(m_src, 3)
        L["note"] = (L["note"] + f" | v1.6 (lead 08:40Z item 3, sourced size accepted): unit mass {m_old:.3f} -> {L['unit_mass_g']:.3f} g (torus on the "
                     f"sourced ID 50.39 x CS 3.53, FKM 1900 kg/m3 ASSUMED), {2 * (L['unit_mass_g'] - m_old):+.2f} g for the 2 rings (massdelta v7)")
        L["mass_evidence"] = (L["mass_evidence"] + f" | v1.6: CARRIED (lead 08:40Z item 3): CALC torus pi (ID + CS) x pi CS^2 / 4 on the sourced "
                              "AS568-226 ID 50.39 / CS 3.53 (FNST p. 16) x FKM 1900 kg/m3 ASSUMED; DATASHEET ring mass TO-FETCH")
o.update({"version": "v1.6", "basis": o["basis"] + " | v1.6 (2026-10-20, lead 08:40Z item 3): HW-150 unit mass on the sourced AS568-226 size "
          "(CALC torus, FKM 1900 kg/m3 ASSUMED): +0.37 g for the 2 rings; massprops and massdelta v7 re-run"})
# ---------------------------------------------------------------- v1.7 (2026-10-20): J-FWD route (i) (lead 16:53Z R2 / R3, 17:55:55Z F1-F5, 18:36:37Z)
# HW-101 becomes ENG-HW-101-IN718 (IN718, ISO 7380-1 head form with the F3 head: pilot 5.15 h9 x 0.25-0.30, undercut fillet r 0.2-0.3 into the
# head, da 5.55-5.80; M5 x 10.7 +/-0.1 with spring A, M5 x 10.6 +/-0.1 with spring B); torque set per flight lot by J-F1 (maximum 3750 N);
# single-use founder rule (R3) with the removed-screw inspection at the thread root and the head-to-shank fillet (18:36:37Z); J-F1 gains the
# spring items and the pressure-film footprint item; new line HW-170, the disc spring under each head (spring A baseline, spring B alternate).
# Every number below is read from the accepted v352/jfwd result files (sha asserted); nothing is typed except the ruled texts and tagged constants.
V17 = Path("/home/claude/work/mechanical/v352/jfwd")
V17F = {"rows_v7": (V17 / "jfwd_in718_rows_v352_v7.json", "6113d28b64d0dba5"), "spring_v4": (V17 / "jfwd_spring_v352_v4.json", "a277b996c2d61b83"),
        "head_fillet_v1": (V17 / "jfwd_head_fillet_v352_v1.json", "337883c3f2076a32"), "tap_wall_v1": (V17 / "jfwd_tapwall_v352_v1.json", "bcb21243d57af998"),
        "K_js5_v2": (V17 / "jfwd_embed_fit_js5_v352_v2.json", "e2624bf729633fb8"), "screw_lcf_v2": (V17 / "jfwd_screw_lcf_v352_v2.json", "6acdaa2febdf3f6c")}
V17D = {}
for _k, (_p, _s) in V17F.items():
    assert hashlib.sha256(_p.read_bytes()).hexdigest()[:16] == _s, (_k, _p)
    V17D[_k] = json.loads(_p.read_text())
R7, SP4, HF1, TW1, JS2, LC2 = (V17D[k] for k in ("rows_v7", "spring_v4", "head_fillet_v1", "tap_wall_v1", "K_js5_v2", "screw_lcf_v2"))
JF1 = R7["J_F1"]
F_CAP, F_MIN, T_LOT, KW = JF1["maximum_N"], JF1["minimum_N_today_K_window"], JF1["torque_Nm_today_K_window"], JF1["K_window"]
assert (F_CAP, F_MIN, T_LOT, KW) == (3750.0, 2057.6, 2.747, [0.1465, 0.267]), (F_CAP, F_MIN, T_LOT, KW)
ST3 = ("SOAK70", "SOAK", "SOAK52")
row = lambda st, k: R7["states"][st]["rows"]["3750"][k]
ROW7 = {st: R7["TC02_thread_shear_full_row"]["rows"][st]["3750"]["THE_ROW"]["MS_y"] for st in ST3 + ("FA1S",)}   # the line-245 file values
UH7 = {st: row(st, "TC01_under_head_band_neuber")["MS_strain"] for st in ST3 + ("FA1S",)}
FB7 = {st: row(st, "TC01_flat_bearing")["MS_vs_Fbry"] for st in ST3}
FB7ff = {st: row(st, "TC01_flat_bearing")["MS_by_spring_basis"]["full_float_0.557"] for st in ST3}
TEN7 = min(row(st, "screw_tension_234_1b")["MS_y"] for st in ST3)
HOS7 = min(row(st, "head_on_spring_IN718")["MS_y"] for st in ST3 + ("FA1S", "PRELOAD"))
PQ7 = {st: row(st, "seat_line_d6p051_z0_PQ")["MS_PQ_2Fty"] for st in ST3}
assert all(PQ7[st] == row(st, "ring_line_PQ")["MS_PQ_2Fty"] for st in ST3)
FIB7 = {st: row(st, "screw_fibre_soak")["MS_y_fibre"] for st in ST3}
SHK7 = min(row(st, "screw_fibre_soak")["MS_shakedown"] for st in ST3)
assert (ROW7["SOAK52"], ROW7["SOAK"], UH7["SOAK52"]) == (0.045, 0.104, 0.039), (ROW7, UH7)
HG = HF1["governing_and_thread_root_comparison"]["3750"]
TWc = TW1["rows"]["3750"]["cases"]
TWg = min((v["TC02_thread_T"]["MS_y"], k) for k, v in TWc.items() if k.endswith("ruled_+/-0.25deg_net_GOVERNING"))
TWp = min(v["TC02_thread_T"]["MS_y"] for k, v in TWc.items() if "FA-1_pulse_75.5bar_abs|ruled_+/-0.25deg" in k)
assert (TWg[0], TWp) == (0.814, 0.902), (TWg, TWp)
SPR = SP4["springs"]
SA, SB = SPR["A_DIN2093_A10_17-7PH"], SPR["B_Lesjofors_7909_1.4310"]
GEO = SP4["geometry_length_tip_engagement"]["cases"]
GA, GB = GEO["spring A t 0.5: 10.7 +/-0.1"], GEO["spring B t 0.4: 10.6 +/-0.1"]
assert (GA["L_e_gap_bound_mm"], GB["L_e_gap_bound_mm"], GA["A_n_gap_bound_mm2"]) == (7.294, 7.294, 67.93)
SEAT = SP4["lead_16_07Z_item5_seated_and_solid"]
FSA = {r: (SEAT[f"A_DIN2093_A10_17-7PH|R{r}|lo|seat"]["F_S_min_N"], SEAT[f"A_DIN2093_A10_17-7PH|R{r}|hi|seat"]["F_S_min_N"]) for r in ("0.00", "0.20", "0.40")}
FSB = {r: (SEAT[f"B_Lesjofors_7909_1.4310|R{r}|lo|seat"]["F_S_min_N"], SEAT[f"B_Lesjofors_7909_1.4310|R{r}|hi|seat"]["F_S_min_N"]) for r in ("0.00", "0.20", "0.40")}
assert all(v["all_seated"] and v["solid_at_every_hot_frame_all_cases"] for v in SEAT.values())
FTP = SP4["route_i_pilot_centring_and_overhang"]["A_supp_mm2_by_basis"]
ENV = SP4["cad_envelope_check_rev5_v2"]["by_config"]
JSs = JS2["stop_test_lead_F1"]
assert JSs["verdict"] == "NONE TURNED NEGATIVE" and SP4["stop_test_lead_F1"]["verdict"] == "NONE TURNED NEGATIVE"
EMB = JS2["A_cold_embedding"]
EMBlo = min(v["F_after_embedding_N"] for k, v in EMB.items() if k.startswith("lo|H8f7_") and "|J-F1_min_2058|" in k)
EMBhi = min(v["F_after_embedding_N"] for k, v in EMB.items() if k.startswith("hi|H8f7_") and "|J-F1_min_2058|" in k)
assert (EMBlo, EMBhi) == (754, 692), (EMBlo, EMBhi)
LCFg = (HG["i_firing"]["thread_root_N_allow"], HG["i_firing"]["thread_root_MS"], HG["ii_assembly_from_zero"]["thread_root_N_allow"],
        HG["ii_assembly_from_zero"]["thread_root_MS"])
RHO_IN718 = H.engmat.MATERIALS["IN718"]["rho"]["v"]            # LITERATURE (engmat: Special Metals 718, 8.19 g/cm3)
RHO_SPR = H.engmat.MATERIALS["SS-SPRING"]["rho"]["v"]          # LITERATURE (engmat SS-SPRING: 1.4310 / 17-7PH springs, 7.9 g/cm3)
assert (RHO_IN718, RHO_SPR) == (8190.0, 7900.0)


def _m_in718(L_mm, pilot_len=0.30, pilot_d=5.15):
    """CALC unit mass of ENG-HW-101-IN718: the hardware_v351 ISO 7380-1 M5 rule (nominal head AS RECALLED, d2 shank over L) at IN718
    density, plus the pilot ring (pilot_d over d2, longest pilot 0.30); the undercut-fillet groove (r 0.2-0.3) is not subtracted (< 0.1 mm3)."""
    d2 = 5.0 - 0.649519 * H.PITCH[5.0]
    v_pilot = math.pi / 4.0 * (pilot_d ** 2 - d2 ** 2) * pilot_len
    return H.screw_mass_g("ISO 7380-1", 5.0, L_mm, "A4-80") * RHO_IN718 / H.RHO["A4-80"] + v_pilot * 1e-9 * RHO_IN718 * 1e3


M101A, M101B = _m_in718(10.7), _m_in718(10.6)
M170A = math.pi / 4.0 * (SA["De_Di_t_l0_h0_mm"][0] ** 2 - SA["De_Di_t_l0_h0_mm"][1] ** 2) * SA["De_Di_t_l0_h0_mm"][2] * 1e-9 * RHO_SPR * 1e3
M170B = math.pi / 4.0 * (SB["De_Di_t_l0_h0_mm"][0] ** 2 - SB["De_Di_t_l0_h0_mm"][1] ** 2) * SB["De_Di_t_l0_h0_mm"][2] * 1e-9 * RHO_SPR * 1e3
SRCSHA = ", ".join(f"jfwd/{p.name} {s}" for p, s in V17F.values())
REG = ("C4 registration (lead 17:55:55Z F2): two GSE shoulder screws ENG-TC-13 (not flight), selected to the pin-gauged TC-01 holes, go into "
       "two opposite holes before any flight screw; the flight screws are fitted one at a time, each taken to the lot torque and recorded "
       "(hole number, screw and spring lot, torque, wrench); the two shoulder screws come out last and are replaced by flight screws, recorded")
SINGLE = ("SINGLE-USE founder rule until C6 closes (lead 16:53Z R3): J-FWD screws are new at every assembly, never reused or re-torqued; "
          "removed screws are kept per hole and inspected at 10x plus dye penetrant at the thread root AND the head-to-shank fillet "
          "(lead 18:36:37Z), as data")
o["rules"]["tightening_methods"]["M-T1J"] = (
    "J-FWD (HW-101, lead 17:55:55Z F1 / F2, 16:53Z R3): as M-T1L (wet thread locker of the line, cure per the maker sheet before load) with "
    "the final torque SET PER FLIGHT LOT by J-F1: T_lot = 3750 N x K_min(lot) x 5 mm, so that the lot's K_min gives <= 3750 N (today's K "
    f"window {KW[0]}-{KW[1]}: {T_LOT:.3f} N m, minimum {F_MIN:.1f} N at K {KW[1]}); the disc spring HW-170 under each head; " + REG
    + "; never re-torqued (single-use, R3)")
for L in o["lines"]:
    if L["id"] != "HW-101":
        continue
    v16 = {k: L.get(k) for k in ("item", "standard", "length_mm", "grade", "unit_mass_g", "torque_Nm")}
    assert v16["grade"] == "A4-80" and v16["length_mm"] == 10 and v16["torque_Nm"] == 3.0, v16
    m_old = L["unit_mass_g"]
    L.update({
        "item": "J-FWD forward-closure radial screw ENG-HW-101-IN718 (case TC-01 to head plug TC-02), with the disc spring HW-170 under the head",
        "standard": "ENG-HW-101-IN718 (Mechanical drawing, TO-DRAW): ISO 7380-1 button-head form with the F3 head",
        "size": "M5-6g", "length_mm": 10.7, "grade": "IN718 (UNS N07718, AMS 5662 bar aged to AMS 5663)",
        "head_form_F3": {"pilot": "5.15 h9 x 0.25-0.30 long, full diameter from the bearing face, coaxial to the pitch cylinder within dia 0.02 "
                                  "(TO-CONFIRM with the maker)",
                         "under_head_fillet": "undercut fillet r 0.2-0.3 into the head, entirely above the bearing face",
                         "da_mm": SP4["fillet"]["F3_adopted"]["da_mm"], "da_note": "stated on the drawing (F3; the head-on-spring row stops being AS RECALLED)",
                         "lengths": "one head form: spring A on L 10.7 +/-0.1 (baseline), spring B on L 10.6 +/-0.1 (alternate): L_e 7.294 (THE ROW)",
                         "pilot_vs_flat": SP4["fillet"]["F3_adopted"]["pilot_vs_flat"], "ruling": "lead 16:53Z R2, 17:55:55Z F3 ADOPTED"},
        "L_basis": (f"v3.5.2 route (i) (lead 16:53Z R2): the head bears on the disc spring HW-170 (solid at every hot frame) on the rev-5 TC-01 "
                    f"flat (cutter d11.2, r_flat 31.313 +0.020/0 from datum A): spring A t {GA['t_solid_min_max_mm'][0]}-{GA['t_solid_min_max_mm'][1]} + "
                    f"wall {GA['wall_at_hole_mm'][0]}-{GA['wall_at_hole_mm'][1]} at the d5.5 H12 hole + plug gap 0-0.078 (H8 / f7) + engagement in the "
                    f"TC-02 M5-6H tap (drill 4.2 x 9.0, full thread 8.0): L 10.7 +/-0.1 gives L_e min {GA['L_e_gap_bound_mm']} at the gap bound "
                    f"(A_n {GA['A_n_gap_bound_mm2']} mm2, THE ROW; {GA['L_e_gap0_mm']} at gap 0) and a tip {GA['tip_clearance_to_full_thread_end_min_mm']} "
                    f"min short of the full-thread end; spring B (t {GB['t_solid_min_max_mm'][0]}-{GB['t_solid_min_max_mm'][1]}) on L 10.6 +/-0.1 gives the "
                    f"same L_e; 10 holes at az 18 + 36k deg, 12.000 BASIC from datum B (TC-01 fwd end face), position 0.10 to A|B, match-drilled "
                    "TC-01 / TC-02 with clocking +/-0.25 deg by an index pin in the drill fixture (F5); the v1.5 L 10.0 on the d10.5 flat and the "
                    "no-spring L 10.2 are superseded records (rows v7 keeps 10.2 as the record row)"),
        "unit_mass_g": round(M101A, 3),
        "mass_evidence": (f"CALC (hardware_v351 ISO 7380-1 M5 rule: nominal head AS RECALLED + d2 shank x L 10.7, plus the pilot ring 5.15 x 0.30; "
                          f"x IN718 {RHO_IN718:.0f} kg/m3 LITERATURE, engmat 'Special Metals 718'); the undercut-fillet groove not subtracted; "
                          f"L 10.6 (spring B) {M101B:.3f} g; v1.6 A4-80 M5 x 10 {m_old:.3f} g; DATASHEET TO-FETCH"),
        "torque_Nm": T_LOT,
        "torque_basis": (f"DESIGN v3.5.2 (lead 17:55:55Z F1, ACCEPTED 18:36:37Z): J-F1 sets the torque on the FLIGHT LOT so that the lot's K_min "
                         f"gives <= {F_CAP:.0f} N (T_lot = {F_CAP:.0f} N x K_min x 5 mm); with today's K window {KW[0]}-{KW[1]} (the v1.4 J-F1 "
                         f"bounds) T = {T_LOT:.3f} N m and the minimum is {F_MIN:.1f} N at K {KW[1]}; the {F_CAP:.0f} N column (FE-anchored) "
                         "governs every J-FWD row and 4096 N is information; the rows that depend on the minimum are re-stated at "
                         f"{F_MIN:.1f} N (K_js5 v2: cold after embedding min {EMBlo} / {EMBhi} N at k_b lo / hi over the drawing gaps, head "
                         "seated; spring v4: all 24 seated): NONE TURNED NEGATIVE; a lot whose "
                         f"minimum falls below {F_MIN:.1f} N goes to the lead (the rows are re-stated at the lot result); the v1.4 3.0 N m / "
                         "2250-4096 N basis and the 2.5 N m fallback are superseded (sources: " + SRCSHA + ")"),
        "thread_locker": (L["thread_locker"] + " | v1.7: kept on the IN718 screw (no ruling removes it); the wet-locker K WITH THE SPRING under the "
                          "head is a J-F1 item; screw temperature in the soak states up to 158.6 C (SOAK70, tap-wall v1 screw_forces), TC-02 thread "
                          "94.9-97.7 C: below the 180 C rating; at the R1 abort TB states (TC-02 TB field maximum 223.4 / 208.0 C, not located at the "
                          "taps) the tap-zone temperature against the 180 C rating is TO-VERIFY"),
        "status": ("DEFINED v3.5.2 route (i) (lead 16:53Z R2 / R3, 17:55:55Z F1-F5, rows v7 and companions ACCEPTED 18:36:37Z): "
                   "ENG-HW-101-IN718 TO-DRAW (F3 head form) and TO-QUOTE; C6 OPEN (screw LCF FOUND NEGATIVE; closure paths 2 (FE levers, "
                   "(b1) / select-fit band after chain E) and 3 (qualification test, TO-DEFINE, founder)): single-use founder rule"),
        "action": (SINGLE + "; " + REG + "; at every J-FWD assembly gauge the TC-01 holes (pins GO 5.50 / NO-GO 5.62, C1 (g)) and the TC-02 taps "
                   "(M5-6H GO / NO-GO; cured locker removed by a thread chaser only, no re-tap); gauge also after firing 1, every 5 firings and "
                   "after any Pc above 45 bar abs (v1.4 gauge rule kept: each is a disassembly, so new screws follow); after any Pc above 60 bar "
                   "abs the line-231 J-FWD inspection (C6 (2) list); the v1.4 10-firing replacement interval and the J-F1b interval purpose are "
                   "superseded by the single-use rule"),
        "note": (f"v1.7 route (i) rows at the J-F1 cap {F_CAP:.0f} N (04-fea/v352/jfwd_in718_rows_v352_v7.json 6113d28b64d0dba5; GOVERNING "
                 f"column; SIM / CALC / DERIVED): THE ROW (TC-02 thread shear, A_n 67.93) MS_y SOAK52 {ROW7['SOAK52']:+.3f} (FLAG), SOAK70 "
                 f"{ROW7['SOAK70']:+.3f}, SOAK {ROW7['SOAK']:+.3f}, FA1S {ROW7['FA1S']:+.3f}; under-head at full float [ASSUMED mean-pressure "
                 f"scaling on the spring footprint, no edge loading] SOAK52 {UH7['SOAK52']:+.3f} (FLAG), SOAK70 {UH7['SOAK70']:+.3f}, SOAK "
                 f"{UH7['SOAK']:+.3f}, FA1S {UH7['FA1S']:+.3f}; TC-01 flat bearing on the registered stack 0.4865 (F2) SOAK52 {FB7['SOAK52']:+.3f}, "
                 f"SOAK70 {FB7['SOAK70']:+.3f}, SOAK {FB7['SOAK']:+.3f} (full float {FB7ff['SOAK52']:+.3f} / {FB7ff['SOAK70']:+.3f} / "
                 f"{FB7ff['SOAK']:+.3f}); screw tension min {TEN7:+.3f}; head on spring >= {HOS7:+.2f}. FOUND NEGATIVES (unchanged, shown as found): "
                 f"seat = ring line P+Q (2 Fty) SOAK70 {PQ7['SOAK70']:+.3f}, SOAK {PQ7['SOAK']:+.3f}, SOAK52 {PQ7['SOAK52']:+.3f}; screw fibre "
                 f"yield SOAK70 {FIB7['SOAK70']:+.3f}, SOAK {FIB7['SOAK']:+.3f}, SOAK52 {FIB7['SOAK52']:+.3f} (shakedown >= {SHK7:+.3f}); screw "
                 f"LCF at the thread root (C6, 183 (1)(c); jfwd_screw_lcf_v352_v2.json 6acdaa2febdf3f6c, Kf 3.0): per firing N_allow {LCFg[0]} "
                 f"(MS {LCFg[1]:+.3f}), from zero {LCFg[2]} (MS {LCFg[3]:+.3f}). Head-to-shank fillet (jfwd_head_fillet_v352_v1.json "
                 f"337883c3f2076a32; Kt LITERATURE, secondary via AMESweb (Pilkey 2005 stepped bar), book page and T-head Kt TO-SOURCE; the no-spring "
                 f"FE head-end resultants carried over ASSUMED): static MS_y {HG['static']['MS_y_net']:+.3f} / MS_u {HG['static']['MS_u_net']:+.3f}; "
                 f"LCF per firing N_allow {HG['i_firing']['fillet_N_allow']} (MS {HG['i_firing']['fillet_MS']:+.3f}), from zero "
                 f"{HG['ii_assembly_from_zero']['fillet_N_allow']} (MS {HG['ii_assembly_from_zero']['fillet_MS']:+.3f}, FOUND NEGATIVE, not "
                 f"governing: the thread root governs). Tap wall to the torch passage (jfwd_tapwall_v352_v1.json bcb21243d57af998, CALC, wall "
                 f"1.6355 net at +/-0.25 deg): governing {TWg[1].split('|')[0]} with 102 bar abs MS_y {TWg[0]:+.3f}, the 75.5 bar FA-1 pulse "
                 f"{TWp:+.3f}; P_torch and its distribution TO-CONFIRM (REV-COMB-4). No-spring record (K_js5 v2 e2624bf729633fb8): the 239 (3) "
                 f"negative (-239 / -323 N, 9 / 12 of 24 unseated) is unchanged and answered by route (i). History: the A4-80 rows and texts of "
                 "v1.2-v1.6 are in hardware_v352 v1.6 (0ed3f31d3e166f85)"),
        "oxygen_service": (L["oxygen_service"].replace("minimum wall from the M5 major diameter to any other TC-02 cavity 1.906 mm (torch passage, "
                                                       "az 18 / 342)", "minimum wall from the M5 major diameter to any other TC-02 cavity 1.906 mm "
                                                       "CAD nominal (torch passage, az 18 / 342; 1.6355 net at the +/-0.25 deg clocking, F5, tap-wall "
                                                       f"v1 MS_y {TWg[0]:+.3f})")),
        "assembly_note": (L["assembly_note"] + " | v1.7: one HW-170 disc spring under each head (spring A with L 10.7, spring B with L 10.6; never "
                          "mixed in one joint); spring orientation TO-DEFINE on the ENG-HW-101-IN718 drawing (the spring is flat above its derated "
                          f"F_flat {SEAT['A_DIN2093_A10_17-7PH|R0.00|lo|seat']['F_flat_derated_N']:.0f} N, far below the {F_MIN:.1f} N minimum, so the "
                          "rows take the flat annulus); the locker never on the spring or the flat; " + REG + "; " + SINGLE),
    })
    assert "1.906 mm CAD nominal" in L["oxygen_service"], "oxygen_service text anchor moved"
    L["test"] = {
        "id": "J-F1", "owner": "founder (lead 2026-10-20 founder test list)",
        "what": ("torque-tension of ENG-HW-101-IN718 (flight lot: IN718 AMS 5662 / 5663, F3 head: pilot 5.15 h9 x 0.25-0.30, undercut fillet "
                 "r 0.2-0.3, da 5.55-5.80; M5 x 10.7 +/-0.1) with the HW-170 disc spring under the head (flight lot, spring A; with M5 x 10.6 "
                 "if spring B is bought) and LOCTITE 243 (flight lot), into a 6061-T6 M5-6H tap (drill 4.2 x 9.0, 8.0 full thread, TC-02 "
                 "surface state) through a 2.69 mm 6061-T6 wall coupon with a d5.5 H12 hole and the rev-5 head-seat flat (cutter d11.2, Ra 1.6 "
                 "max, square to the hole within 0.05: the TC-01 state; the spring and the under-head friction are part of K); preload by a "
                 "through-hole load washer (grip restored) or ultrasonic elongation, M-T1J"),
        "samples": ("10 screws, one per fresh tap; plus 3 of the taps re-used 3 times after chaser cleaning with a NEW screw and spring each time "
                    "(the single-use rule): 19 readings"),
        "acceptance": (f"sets the lot torque: T_lot = {F_CAP:.0f} N x K_min(lot) x 5 mm so that the MAXIMUM preload is <= {F_CAP:.0f} N on every "
                       f"reading (lead 17:55:55Z F1; FE-anchored cap); the lot MINIMUM = T_lot / (K_max(lot) x 5 mm) is reported: the rows are "
                       f"stated at {F_MIN:.1f} N (today's K window {KW[0]}-{KW[1]}, {T_LOT:.3f} N m); a lot minimum below {F_MIN:.1f} N goes to "
                       "the lead and the minimum-dependent rows (cold-after-embedding seating, K_js5) are re-stated at the lot result; a reading "
                       "below the minimum does not reopen the strength rows (bearing-type joint) but re-issues the retention statement"),
        "spring_items": ("lead 16:53Z R2 'J-F1 gains the spring items': (1) K WITH THE SPRING under the head (the lot K window above is "
                         "measured with it); (2) the spring FLATTENING: the spring is flat (solid) at every reading, by the head-height change "
                         "against the derated F_flat (spring A about 360-411 N, spring B 236 N basis), recorded; (3) the CRACK-ON (breakaway) "
                         "torque of every reading, recorded"),
        "pressure_film_item": (f"TO-VERIFY (lead 17:55:55Z F1): Fuji Prescale pressure-film footprint of the spring on the flat at the J-F1 "
                               f"maximum (film grade TO-SELECT for the expected pressure range), on at least 3 readings: the supported area "
                               f"against the rows v7 basis ({FTP['registered_stack_0.4865_F2']} mm2 at the registered stack 0.4865, "
                               f"{FTP['full_float_0.557']} at full float); it also covers the spring-footprint FE run, which is not run "
                               "unless disk space appears (line 245 (6))"),
        "optional_J-F1b": ("5 of the J-F1 joints (with the spring) with the load washer kept in: 10 oven cycles 20 -> 120 C, residual preload and "
                           "breakaway torque recorded, as data for the preload-retention audit (16:53Z R2: the check on the relaxation model); "
                           "its v1.4 purpose (the 10-firing replacement interval) is superseded by the single-use rule; the cycle temperature "
                           "against the about 160 C spring relaxation basis is TO-RULE"),
        "superseded": "v1.4-v1.6 J-F1 (A4-80 M5 x 10, 3.0 N m, acceptance 2250-4096 N, 2.5 N m fallback): hardware_v352 v1.6 0ed3f31d3e166f85"}
    L["fallback_2.5Nm"] = {"status": "SUPERSEDED v1.7 (lead 17:55:55Z F1: the torque is set per flight lot by J-F1; the 2.5 N m A4-80 fallback "
                                     "and its margins are records of hardware_v352 v1.6 0ed3f31d3e166f85)"}
    L["v1_6_record"] = v16 | {"note": "hardware_v352 v1.6 values of this line (A4-80 basis), superseded by v1.7"}
assert not any(L["id"] == "HW-170" for L in o["lines"])
o["lines"].append({
    "id": "HW-170", "kind": "washer",
    "item": "J-FWD disc spring under each ENG-HW-101-IN718 head (route (i), lead 16:53Z R2): spring A baseline",
    "standard": "DIN EN 16983 (previously DIN 2093) group 1, series A",
    "size": (f"A10: De {SA['De_Di_t_l0_h0_mm'][0]} x Di {SA['De_Di_t_l0_h0_mm'][1]} x t {SA['De_Di_t_l0_h0_mm'][2]}, l0 "
             f"{SA['De_Di_t_l0_h0_mm'][3]}, h0 {SA['De_Di_t_l0_h0_mm'][4]} mm (DATASHEET: Schnorr brochure p. 11 row 001 500 A)"),
    "length_mm": None, "grade": "1.4568 (17-7 PH)", "qty": 10, "host": "ENG-TC-01", "joint": "J-FWD", "group": "engine",
    "L_basis": (f"one per screw under the head, on the rev-5 TC-01 flat (cutter d11.2, r_flat 31.313 +0.020/0 from A); solid at every hot "
                f"frame (spring v4); the thickness enters the HW-101 length (spring A t {GA['t_solid_min_max_mm'][0]}-{GA['t_solid_min_max_mm'][1]} "
                f"with L 10.7, spring B t {GB['t_solid_min_max_mm'][0]}-{GB['t_solid_min_max_mm'][1]} with L 10.6; L_e 7.294); t tolerance "
                f"{SP4['geometry_length_tip_engagement']['basis']['t_tol_src']}; drawing note on TC-01: 'disc spring may overhang the flat's "
                "tangential edges' (P(i)-2, ACCEPTED 16:53Z)"),
    "unit_mass_g": round(M170A, 3),
    "mass_evidence": (f"CALC (flat annulus De 10 / Di 5.2 x t 0.5 x SS-SPRING {RHO_SPR:.0f} kg/m3 LITERATURE, engmat); spring B (t 0.4) "
                      f"{M170B:.3f} g; DATASHEET TO-FETCH"),
    "torque_Nm": None, "torque_basis": "", "thread_locker": "",
    "status": ("DEFINED v3.5.2 route (i) (lead 16:53Z R2): spring A (DIN 2093 A10, 17-7 PH, Schnorr 001 500 A in 1.4568) is the baseline, "
               "spring B (Lesjofors 7909) the alternate; both TO-QUOTE delivered to DK-6400 with relaxation data at about 160 C"),
    "action": ("TO-QUOTE spring A and spring B delivered to DK-6400 with the maker's relaxation data at about 160 C (R2); relaxation R "
               "TO-SOURCE (spring v4: seated for any R < 0.9999); reuse of a removed spring TO-RULE (Mechanical proposes: new with the screw at "
               "every assembly, as HW-101)"),
    "note": (f"spring v4 (04-fea/v352/jfwd_spring_v352_v4.json a277b996c2d61b83, CALC / DATASHEET; harness reproduces relax v7) at the J-F1 band "
             f"{F_MIN:.1f}-{F_CAP:.0f} N: all 24 cases seated at both k_b ends and both families, R 0 to 0.80, both springs; spring A F_S min "
             f"{FSA['0.00'][0]} / {FSA['0.00'][1]} N (k_b lo / hi) at R 0, {FSA['0.20'][0]} / {FSA['0.20'][1]} at R 0.2, {FSA['0.40'][0]} / "
             f"{FSA['0.40'][1]} at R 0.4; spring B {FSB['0.00'][0]} / {FSB['0.00'][1]}, {FSB['0.20'][0]} / {FSB['0.20'][1]}, {FSB['0.40'][0]} / "
             f"{FSB['0.40'][1]}; derating 0.925 (tolerance) x 0.946 (E at 160 C proxy) x (1 - R); supported area on the flat "
             f"{FTP['registered_stack_0.4865_F2']} mm2 at the registered stack 0.4865 (F2), {FTP['full_float_0.557']} at full float; CAD (checks/"
             f"test_rev5_jfwd_v2.json 32c41e1e207f9d64): spring to FD-04 >= {min(v['min_FD04_spring_mm'] for v in ENV.values()):.3f} mm, head "
             f">= {min(v['min_FD04_head_mm'] for v in ENV.values()):.3f} mm; the springs are hardware lines, not CAD solids"),
    "oxygen_service": "dry side (as HW-101): outside both bore seals; not N2O-wetted",
    "assembly_note": "fitted with its screw (HW-101 assembly note); orientation TO-DEFINE on the ENG-HW-101-IN718 drawing",
    "spring_A": {"part": SA["part"], "material": SA["material"], "De_Di_t_l0_h0_mm": SA["De_Di_t_l0_h0_mm"], "F_flat_basis_N": SA["F_flat_basis_N"],
                 "basis_scale_note": SA["basis_scale_note"], "src": SA["src"], "ruled_as": "Schnorr 001 500 A in 1.4568 (R2)"},
    "spring_B_alternate": {"part": SB["part"], "material": SB["material"], "De_Di_t_l0_h0_mm": SB["De_Di_t_l0_h0_mm"],
                           "F_flat_basis_N": SB["F_flat_basis_N"], "src": SB["src"], "screw_length_mm": 10.6, "unit_mass_g_CALC": round(M170B, 3)},
    "test": {"id": "J-F1", "owner": "founder (with HW-101)", "samples": "every J-F1 reading of HW-101 carries a new HW-170 of the flight lot",
             "acceptance": "the HW-101 J-F1 spring items (K with the spring, flattening, crack-on torque) and the pressure-film footprint item"}})
o["jfwd_route_i_basis"] = {k: {"path": f"04-fea/v352/{p.name}", "sha256_16": s} for k, (p, s) in V17F.items()}
o.update({"version": "v1.7", "basis": o["basis"] + (
    " | v1.7 (2026-10-20, lead 16:53Z R2 / R3, 17:55:55Z F1-F5, 18:36:37Z): J-FWD route (i): HW-101 = ENG-HW-101-IN718 (IN718 AMS 5662 / "
    "5663, F3 head: pilot 5.15 h9 x 0.25-0.30, undercut fillet r 0.2-0.3, da 5.55-5.80; M5 x 10.7 +/-0.1, spring B with 10.6), torque set per "
    f"flight lot by J-F1 (<= {F_CAP:.0f} N; today {T_LOT:.3f} N m, minimum {F_MIN:.1f} N), method M-T1J with the C4 registration, single-use "
    f"founder rule; HW-170 disc spring x 10 (spring A Schnorr 001 500 A in 1.4568, spring B Lesjofors 7909); CALC mass HW-101 {m_old:.3f} -> "
    f"{M101A:.3f} g, HW-170 {M170A:.3f} g ({10 * (M101A - m_old) + 10 * M170A:+.2f} g in all); rows: 04-fea/v352 rows v7 and companions")})
TQ_METHOD = {}
for L in o["lines"]:
    if L["kind"] != "screw":
        L["tightening_method"], L["preload_scatter"] = "M-NONE", ""
        continue
    t = L.get("torque_Nm")
    if L["id"] == "HW-101" and "M-T1J" in o["rules"]["tightening_methods"]:     # v1.7: J-F1 lot torque, C4 registration, single-use
        m = "M-T1J"
    elif str(L.get("grade", "")).startswith("Ti-6Al-4V"):
        m = "M-T1Ti"
    elif L.get("thread_locker") or "Loctite" in L.get("note", "") or L["id"] == "HW-114":
        m = "M-T1L"
    elif t is not None and t < 1.0:
        m = "M-T2"
    else:
        m = "M-T1"
    L["tightening_method"] = m
    L["preload_scatter"] = ("J-F1 flight lot (lead 17:55:55Z F1): T_lot = 3750 N x K_min(lot) x 5 mm; today's K window 0.1465-0.267 gives "
                            "2057.6-3750 N at 2.747 N m (replaces +/-25 % about K 0.20 for this line)") if m == "M-T1J" else "+/-25 % (ASSUMED, K 0.20)"
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
