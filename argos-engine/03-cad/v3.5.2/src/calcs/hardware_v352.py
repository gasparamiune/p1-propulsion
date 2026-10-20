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
