"""Hardware list v3.5.2 = hardware_v351.json + lead CHANGELOG 206 (2b) Ti-6Al-4V screws (Mechanical, 2026-10-13, v1).
Ti only where v352/ti/ti_screws_v352_v1.json leaves no exclusion at the CONSERVATIVE 100 mm R3 distance (line of sight not credited):
HW-121 (J-FRAME-L, 157.2 mm from FD-05) and HW-123 (J-BRKT, 161.6 mm from FD-07B).  HW-126 (ICD-1L, 159.8 mm) is a Ti candidate that
needs the airframe ICD agreement: kept A4-70 here (lead: to the ICD-AIRFRAME discussion).  The 50 mm option (HW-113 / HW-115 / HW-124,
-8.4 g) was DECLINED by the lead (R3 stays 100 mm).  v1.1: thread locker LOCTITE 222 on HW-115 (EL-03 M2), lead request.
Preload kept at the v3.5.1 A4-70 value (0.65 x 450 MPa x As); torque from a torque-tension test of the anodised + lubricated Ti screw."""
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
