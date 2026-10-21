"""Standard hardware, O-rings and seals of CAD v3.5.1 (REV-MECH-1 RM1-12, lead CHANGELOG 188 (11)), v1, 2026-10-13, Mechanical.

usage: hardware_v351.py [OUT.json]      (default 03-cad/src/data/hardware_v351.json)

One line per fastener / dowel / insert / O-ring / seal / washer kind that the CAD does NOT model as a solid (the modelled COTS
items ENG-HW-20/21/22/25, the custom studs GM-18/GM-20 and the spacers GM-19 are already BOM lines of their own).  Each line:
standard, size, length, grade, quantity, host part and joint, group (engine / ring / horn / pushrod / fixed / hose / airframe-ICD),
unit mass and its evidence class, tightening torque and its basis, status and the open action.

Sources of the lines: the CAD part notes and drawing fits (census scripts v351/gm/hw_census.py, v351/hw/hole_census.py on the
v3.5.1 dev build: hole diameters and lengths per part) and the joint calculations (04-fea/structural/joints.py).
Lengths: grip from the CAD hole census + thread engagement >= 1.5 d into aluminium where the tapped depth allows; the
standard length below the tip-to-hole-bottom limit is chosen; every choice is printed in 'L_basis'.

Mass evidence: CALC = nominal geometry of the standard (head dimensions AS RECALLED from the standard tables, threaded shank at the
pitch diameter) x density (engmat); NOT a supplier DATASHEET mass.  The lead's rule (188 (11)) keeps the 0.20 kg hardware
allowance in the mass properties until DATASHEET masses replace the CALC values: this file gives the CALC total for comparison only.
Torque: DESIGN where a part note fixes it; otherwise DERIVED T = K F d with K 0.20 (ASSUMED, lubricated stainless thread) and
F = 0.65 Rp0.2,min As (ASSUMED assembly preload target, the J-BON rule of joints.py); As from the ISO 898-1 formula with the
ISO 261 coarse pitch.  Thread-strip capacity of the tapped aluminium at that preload is NOT yet checked line by line (open).
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src" if (HERE.parent / "src").is_dir() else HERE.parent     # hub: 03-cad/calcs + 03-cad/src; dev: src/calcs
sys.path.insert(0, str(SRC.parents[1] / "04-fea" / "src"))
import engmat   # noqa: E402

VERSION = "v1"
PITCH = {2.0: 0.40, 2.5: 0.45, 3.0: 0.50, 4.0: 0.70, 5.0: 0.80, 6.0: 1.00}          # ISO 261 coarse
RP02 = {"A2-70": 450e6, "A4-70": 450e6, "A4-80": 600e6, "10.9": 940e6, "12.9": 1100e6}  # ISO 3506-1 / ISO 898-1 minima (Pa)
RHO = {"A2-70": engmat.MATERIALS["SS304"]["rho"]["v"], "A4-70": engmat.MATERIALS["SS-A4-70"]["rho"]["v"],
       "A4-80": engmat.MATERIALS["SS-A4-80"]["rho"]["v"], "10.9": engmat.MATERIALS["STEEL"]["rho"]["v"],
       "12.9": engmat.MATERIALS["STEEL"]["rho"]["v"], "FKM": engmat.MATERIALS["FKM"]["rho"]["v"],
       "FFKM": engmat.MATERIALS["FFKM"]["rho"]["v"], "Cu": engmat.MATERIALS["COPPER"]["rho"]["v"],
       "steel": engmat.MATERIALS["STEEL"]["rho"]["v"], "304": engmat.MATERIALS["SS304"]["rho"]["v"]}
# head dimensions (dk, k, socket across-flats s, socket depth t) in mm: nominal values of the standards, AS RECALLED (TO-VERIFY)
HEAD = {"ISO 4762": {2.0: (3.8, 2.0, 1.5, 1.0), 2.5: (4.5, 2.5, 2.0, 1.1), 3.0: (5.5, 3.0, 2.5, 1.3), 4.0: (7.0, 4.0, 3.0, 2.0),
                     5.0: (8.5, 5.0, 4.0, 2.5)},
        "DIN 7984": {3.0: (5.5, 2.0, 2.0, 1.2), 4.0: (7.0, 2.8, 2.5, 1.6), 5.0: (8.5, 3.5, 3.0, 2.0)},
        "ISO 7380-1": {3.0: (5.7, 1.65, 2.0, 1.0), 4.0: (7.6, 2.2, 2.5, 1.3), 5.0: (9.5, 2.75, 3.0, 1.6)},
        "ISO 10642": {3.0: (6.72, 1.86, 2.0, 1.1), 4.0: (8.96, 2.48, 2.5, 1.5), 5.0: (11.2, 3.1, 3.0, 1.9)}}
# AS568 (inside diameter, cross-section) in mm: AS568 dash-number table, AS RECALLED (TO-VERIFY against the supplier sheet)
AS568 = {"010": (6.07, 1.78), "012": (9.25, 1.78), "013": (10.82, 1.78), "016": (15.60, 1.78), "226": (47.22, 3.53), "229": (56.74, 3.53)}
K_NUT = 0.20                    # ASSUMED nut factor
PRE_FRAC = 0.65                 # ASSUMED preload fraction of Rp0.2


def As(d):
    P = PITCH[d]
    d2, d3 = d - 0.649519 * P, d - 1.226869 * P
    return math.pi / 4.0 * ((d2 + d3) / 2.0) ** 2


def screw_mass_g(std, d, L, grade):
    dk, k, s, t = HEAD[std][d]
    if std == "ISO 10642":                      # countersunk: L includes the head
        v_head = math.pi * k / 12.0 * (dk ** 2 + dk * d + d ** 2)
        L_sh = L - k
    elif std == "ISO 7380-1":                   # button head: spherical cap
        v_head = math.pi * k * (3.0 * (dk / 2.0) ** 2 + k ** 2) / 6.0
        L_sh = L
    else:
        v_head = math.pi / 4.0 * dk ** 2 * k
        L_sh = L
    v_sock = math.sqrt(3.0) / 2.0 * s ** 2 * t
    d2 = d - 0.649519 * PITCH[d]
    v = v_head - v_sock + math.pi / 4.0 * d2 ** 2 * L_sh
    return v * 1e-9 * RHO[grade] * 1e3


def torque(d, grade):
    F = PRE_FRAC * RP02[grade] * As(d) * 1e-6
    return K_NUT * F * d * 1e-3, F


def oring_mass_g(dash, mat):
    ID, cs = AS568[dash]
    return math.pi * (ID + cs) * math.pi / 4.0 * cs ** 2 * 1e-9 * RHO[mat] * 1e3


L = []


def screw(id_, item, std, d, Lmm, grade, qty, host, joint, group, L_basis, torque_Nm=None, torque_src=None, status="DEFINED",
          action="", loctite="", note=""):
    T_d, F = torque(d, grade)
    if torque_Nm is None:
        torque_Nm, torque_src = round(T_d, 2), (f"DERIVED: T = {K_NUT} x F x d, F = {PRE_FRAC} x Rp0.2,min {RP02[grade]/1e6:.0f} MPa x As "
                                                f"{As(d):.2f} mm2 = {F:.0f} N (K and preload fraction ASSUMED)")
    m = screw_mass_g(std, d, Lmm, grade)
    L.append({"id": id_, "kind": "screw", "item": item, "standard": std, "size": f"M{d:g}", "length_mm": Lmm, "grade": grade,
              "qty": qty, "host": host, "joint": joint, "group": group, "L_basis": L_basis,
              "unit_mass_g": round(m, 3), "mass_evidence": "CALC (standard nominal geometry AS RECALLED x engmat density); DATASHEET TO-FETCH",
              "torque_Nm": torque_Nm, "torque_basis": torque_src, "thread_locker": loctite, "status": status, "action": action, "note": note})


def other(id_, kind, item, standard, size, qty, host, joint, group, unit_mass_g, mass_evidence, status="DEFINED", action="", note="",
          material=""):
    L.append({"id": id_, "kind": kind, "item": item, "standard": standard, "size": size, "length_mm": None, "grade": material,
              "qty": qty, "host": host, "joint": joint, "group": group, "L_basis": "", "unit_mass_g": (round(unit_mass_g, 3) if unit_mass_g is not None else None),
              "mass_evidence": mass_evidence, "torque_Nm": None, "torque_basis": "", "thread_locker": "", "status": status, "action": action,
              "note": note})


def oring(id_, dash, mat, qty, host, joint, group, note=""):
    ID, cs = AS568[dash]
    other(id_, "o-ring", f"O-ring AS568-{dash} {mat}", "SAE AS568", f"-{dash} (ID {ID} x CS {cs} mm, AS RECALLED)", qty, host, joint, group,
          oring_mass_g(dash, mat), f"CALC (torus at AS568 nominal dims x {mat} density {RHO[mat]:.0f} ASSUMED); DATASHEET TO-FETCH",
          note=note, material=mat)


# ---------------------------------------------------------------------------------------------------------------- ENGINE (gimballed)
screw("HW-101", "J-FWD forward-closure radial screw (case TC-01 to head plug TC-02)", "ISO 7380-1", 5.0, 10, "A4-80", 8, "ENG-TC-01/ENG-TC-02",
      "J-FWD", "engine",
      "case wall 3.14 at the 5.5 hole (hole census) + plug gap 0.025 + engagement 6.83 = 10.0; v3.5.1 TC-02 taps deepened to drill 4.2 x 9.0, "
      "M5-6H full thread 8.0 (v3.5 6.42 deep: M5 x 10 bottomed, M5 x 8 gave 4.84 mm engagement vs joints.py LE 6.0)",
      status="DEFINED (A4-80 in ISO 7380-1 availability TO-VERIFY at quote; fallback ISO 4762 A4-80 needs a head-clearance check)",
      action="spot face on the case OD (dk 9.5 head on R 31.75: sagitta 0.36 mm) TO-DEFINE on the TC-01 drawing",
      note="lead 177 (2) A4-80; 194: yield at 93 bar abs (0.1 < T <= 1 ms) / FA1S until the J-FWD period is shown (modal closure)")
screw("HW-102", "J-BON bonnet screw (TC-04 on TC-02)", "ISO 4762", 4.0, 12, "A4-70", 4, "ENG-TC-04/ENG-TC-02", "J-BON", "engine",
      "TC-04 flange 4.99 (M4 clearance 4.5, hole census) + engagement 7.0 in the 10 deep M4 tap of TC-02 (tip 3.0 above the hole bottom)",
      action="head clearance to the TC-04 boss and the PD-01 frame not modelled: TO-VERIFY in CAD")
screw("HW-103", "FD-01 inlet block screw (into TC-02 flat)", "DIN 7984", 3.0, 16, "A4-70", 2, "ENG-FD-01/ENG-TC-02", "J-FD01", "engine",
      "DESIGN (FD-01 note: 2x M3 DIN 7984 A4-70 x 16); FD-01 clearance 3.01 / 10.5 under the counterbores, TC-02 M3 tap 8 deep",
      torque_Nm=1.0, torque_src="DESIGN (FD-01 note)",
      action="engagement differs between the two holes (grip 3.0 vs 10.5 in the hole census): length per hole TO-VERIFY on the drawing")
screw("HW-104", "BL-01 bleed tap block screw (into the TC-04 boss)", "ISO 4762", 2.5, 12, "A4-70", 2, "ENG-BL-01/ENG-TC-04", "J-BL01", "engine",
      "BL-01 block 8.0 (M2.5 clearance 2.7, hole census) + engagement 4.0 (1.6 d); TC-04 M2.5 taps are a drawing operation (not cut in the solid)",
      action="TC-04 drawing: 2x M2.5-6H x 6 full thread at the BL-01 pattern")
screw("HW-105", "PD-01 frame foot screw through the G11 isolator washer PD-11 (into TC-02)", "ISO 4762", 3.0, 12, "A2-70", 4,
      "ENG-PD-01/ENG-PD-11/ENG-TC-02", "J-PD01", "engine",
      "PD-01 foot 4.0-5.0 + G11 washer 2.0 + engagement 5.0-6.0 in the 8 deep M3 tap of TC-02 (r 26)",
      torque_Nm=0.6, torque_src="DESIGN (PD-11 note: limited to 0.6 N m, G11 creep TO-VERIFY)")
screw("HW-106", "PD-02 crank housing to the PD-01 shelf and cap", "ISO 4762", 3.0, 8, "A2-70", 4, "ENG-PD-02/ENG-PD-01", "J-PD02", "engine",
      "PD-01 shelf / cap clearance 2.0 + engagement 6 in the PD-02 22 mm through tap (hole census)")
screw("HW-107", "HV69 pintle servo ear screw through the G11 pad PD-12 (into PD-01)", "ISO 4762", 2.0, 8, "A2-70", 4,
      "ENG-PD-08 servo/ENG-PD-12/ENG-PD-01", "J-HV69", "engine",
      "servo ear ~2.5 ASSUMED + G11 pad 1.5 + G11 washer (not modelled) + engagement 3.5 in the 4 deep M2 tap",
      status="TO-VERIFY (servo ear thickness from the HV69 sheet)")
screw("HW-108", "MGNR09R rail screw (into the PD-01 rail plate)", "ISO 4762", 3.0, 8, "A2-70", 3, "ENG-PD-19/ENG-PD-01", "J-RAIL", "engine",
      "DESIGN (PD-19 note: 3x M3 x 8, HIWIN rail counterbores)", status="DEFINED (rail counterbore depth per HIWIN sheet TO-VERIFY)")
screw("HW-109", "PD-07 carriage plate to the MGN09H block", "ISO 4762", 3.0, 6, "A2-70", 4, "ENG-PD-07/ENG-PD-08", "J-CARR", "engine",
      "PD-07 plate 3.0-3.5 (hole census) + engagement in the MGN09H block thread (depth ~3 ASSUMED from the catalogue copy, TO-VERIFY)",
      status="TO-VERIFY (block thread depth)")
screw("HW-110", "PD-03 cover screw (into PD-02 end face)", "ISO 4762", 2.0, 6, "A2-70", 3, "ENG-PD-03/ENG-PD-02", "J-PD03", "engine",
      "PD-03 clearance 4.0 (hole census) + 2.0 engagement (M2 taps not modelled in PD-02: drawing operation)",
      status="TO-VERIFY (PD-02 end-face tap depth >= 4)", action="lengthen to M2 x 8 if the PD-02 tap is >= 5 deep")
screw("HW-111", "PD-05 dog-hub clamp screw", "ISO 4762", 2.0, 6, "A2-70", 1, "ENG-PD-05", "J-PD05", "engine",
      "clamp screw (not modelled); length per the hub slot TO-DEFINE", status="TO-DEFINE")
screw("HW-112", "PD-10 radiation shield screw through the G11 stand-offs", "ISO 4762", 2.0, 8, "A2-70", 2, "ENG-PD-10/ENG-PD-20/ENG-PD-01", "J-PD10",
      "engine", "shield 0.5 + stand-off 2.0 + engagement ~5 (servo-plate tap depth TO-VERIFY)", status="TO-VERIFY")
screw("HW-113", "Collar clamp screw (GM-01 clearance + counterbore into GM-02 tapped)", "DIN 7984", 3.0, 10, "A4-70", 4, "ENG-GM-01/ENG-GM-02",
      "J-COLLAR", "engine",
      "GM-01 grip 5.05 under the 6.0 counterbore + engagement 4.95 (1.65 d) in the 8 deep GM-02 tap (7075-T6)",
      torque_Nm=1.0, torque_src="DESIGN (GM-01/02 note)")
screw("HW-114", "Horn radial pinch-clamp screw", "ISO 4762", 3.0, 10, "12.9", 2, "ENG-GM-16", "J-HORN", "horn",
      "pinch slot geometry not modelled; length TO-VERIFY", status="TO-VERIFY", loctite="Loctite 243")
screw("HW-115", "EL-03 encoder holder screw (into the GM-03 ring)", "ISO 4762", 2.0, 6, "A2-70", 2, "ENG-EL-03/ENG-GM-03", "J-EL03", "ring",
      "holder flange ~1.5 ASSUMED + engagement in the 4.79 deep M2 tap (hole census)", status="TO-VERIFY (holder by Electronics)")
# ---------------------------------------------------------------------------------------------------------------- FIXED (airframe side of the gimbal)
screw("HW-120", "Yoke post to the upper thrust ring GM-09 (counterbored from the top)", "ISO 4762", 5.0, 12, "A4-70", 4, "ENG-GM-09/ENG-GM-08",
      "J-FRAME-U", "fixed", "GM-09 grip 4.5 under the 9.5 x 5.5 counterbore + engagement 7.5 (1.5 d) in the 12 deep post tap (tip 4.5 above the bottom)")
screw("HW-121", "Yoke post to the lower ring GM-10 (counterbored from below)", "ISO 4762", 5.0, 12, "A4-70", 4, "ENG-GM-10/ENG-GM-08",
      "J-FRAME-L", "fixed", "GM-10 grip 4.5 under the 9.5 x 5.5 counterbore + engagement 7.5 in the 12 deep post tap")
other("HW-122", "dowel", "Dowel pin 4 m6 x 16, hardened (posts to rings)", "ISO 8734", "4 m6 x 16", 4, "ENG-GM-08/ENG-GM-09/ENG-GM-10",
      "J-FRAME", "fixed", math.pi / 4.0 * 4.0 ** 2 * 16.0 * 1e-9 * RHO["steel"] * 1e3, "CALC (cylinder x 7850)",
      note="8 deep in the post + 8 of the 10 through hole in the ring (hole census)")
screw("HW-123", "TVC servo bracket to the lower ring GM-10 (counterbored from below)", "ISO 4762", 4.0, 12, "A4-70", 8,
      "ENG-GM-10/ENG-GM-13/ENG-GM-14", "J-BRKT", "fixed",
      "GM-10 grip 5.5 under the 8 x 4.5 counterbore + engagement 6.5 (1.6 d) in the 10 deep bracket tap (tip 3.5 above the bottom)")
screw("HW-124", "TVC servo ear screw (servo to bracket GM-13/14)", "ISO 4762", 4.0, 10, "A4-70", 8, "TVC servo/ENG-GM-13/ENG-GM-14", "J-SERVO",
      "fixed", "servo ear ~3 ASSUMED + washer 0.8 + engagement ~6 in the 10.5 deep ear tap", status="TO-VERIFY (servo ear thickness, received servo)")
screw("HW-125", "Airframe screw into the upper thrust ring GM-09 (radial, 8x) - ICD-AIRFRAME", "ISO 10642", 5.0, 10, "A4-70", 8,
      "airframe skin/ENG-GM-09", "ICD-1 thrust mount", "fixed",
      "skin thickness TO-DEFINE (ICD-AIRFRAME); 10 = skin 2 ASSUMED + engagement 8 in the 10.97 deep radial tap (hole census)",
      status="TO-DEFINE (ICD-AIRFRAME: head type, grade, skin thickness)", note="joints.py 16 x M5 airframe ring screws: A4-70 class ASSUMED")
screw("HW-126", "Airframe screw into the lower ring GM-10 (radial, 8x) - ICD-AIRFRAME", "ISO 10642", 5.0, 10, "A4-70", 8, "airframe skin/ENG-GM-10",
      "ICD-1 thrust mount", "fixed", "as HW-125", status="TO-DEFINE (ICD-AIRFRAME)")
screw("HW-127", "FD-09 hose-end clamp foot screw into GM-09 (with helicoil)", "ISO 4762", 4.0, 12, "A4-70", 2, "ENG-FD-09/ENG-GM-09", "J-FD09",
      "fixed", "DESIGN (FD-09 note: 2x M4 x 12 A4-70 into GM-09, helicoil 1.5 D); foot 6.0 + 6.0 engagement",
      action="GM-09 drawing: 2x M4 STI (helicoil) holes at az 284.5 r 57.5/64.5 (not cut in the GM-09 solid)")
other("HW-128", "insert", "Wire thread insert M4 x 1.5 D free-running, 304 (Helicoil class)", "DIN 8140", "M4 x 6", 2, "ENG-GM-09", "J-FD09", "fixed",
      None, "TO-FETCH (supplier sheet); inside the allowance", status="DEFINED (maker TO-SELECT)")
screw("HW-129", "FD-09 clamp cap screw", "ISO 4762", 3.0, 20, "A4-70", 2, "ENG-FD-09", "J-FD09", "fixed",
      "cap clearance 12.6 (hole census) + engagement 7.4 in the 7.9 deep base tap (tip 0.5 above the bottom: TIGHT)",
      action="FD-09 base drawing: M3 tap full thread >= 8.5 (drill 9.5); otherwise M3 x 16 gives only 3.4 engagement")
screw("HW-130", "P-clip FD-11 screw into the airframe insert / rivet nut (ICD)", "ISO 7380-1", 4.0, 8, "A4-70", 3, "ENG-FD-11/airframe",
      "J-PCLIP", "fixed", "P-clip band + tab ~1.6 + rivet-nut grip; length TO-DEFINE with the airframe insert (ICD-AIRFRAME)",
      status="TO-DEFINE (ICD)")
screw("HW-131", "FD-08F line flange screw (into FS-01A)", "ISO 4762", 4.0, 12, "A4-70", 2, "ENG-FD-08F/ENG-FS-01A", "J-FD08F", "fixed",
      "flange 6.0 (hole census) + engagement 6.0 in the 7.99 deep FS-01A tap (tip 2.0 above the bottom)")
screw("HW-132", "FD-12F tank-line flange screw (into FS-01B)", "ISO 4762", 4.0, 12, "A4-70", 2, "ENG-FD-12F/ENG-FS-01B", "J-FD12F", "fixed",
      "flange 6.0 + engagement 6.0 in the 6.99 deep FS-01B tap (tip 1.0 above the bottom: TIGHT)",
      action="FS-01B drawing: M4 tap full thread >= 7.5 at the FD-12F pattern")
screw("HW-133", "MV-P body screw FS-01A to FS-01B", "ISO 4762", 4.0, 25, "A4-70", 4, "ENG-FS-01A/ENG-FS-01B", "J-MVP", "fixed",
      "FS-01A clearance 15.8 (through) + engagement 9.2 in the 10.0 deep FS-01B tap (tip 0.8 above the bottom: TIGHT)",
      action="FS-01B drawing: M4 tap full thread >= 10 (drill 12) or M4 x 22 (DIN 912) with 6.2 engagement")
screw("HW-134", "MV-P cover FS-06 screw (into FS-01B)", "ISO 4762", 3.0, 12, "A4-70", 4, "ENG-FS-06/ENG-FS-01B", "J-FS06", "fixed",
      "FS-06 clearance 6.0 + engagement 6.0 in the 8.0 deep FS-01B tap")
screw("HW-135", "MV follower FS-08 screw on the FS-04 rod top", "ISO 10642", 3.0, 8, "A4-70", 1, "ENG-FS-08/ENG-FS-04", "J-FS08", "fixed",
      "FS-08 3.0 (countersunk flush with the hardened face ASSUMED) + engagement 5 in the 6.0 deep rod tap", status="TO-VERIFY (screw form)")
screw("HW-136", "FS-15 bracket to FS-01A/B", "ISO 4762", 4.0, 12, "A4-70", 2, "ENG-FS-15/ENG-FS-01A/B", "J-FS15", "fixed",
      "FS-15 5.0 + engagement 7.0 in the 7.99-10.0 deep FS-01 taps")
screw("HW-137", "FS-15 bracket to the airframe wall (radial, ICD-2)", "ISO 4762", 5.0, 10, "A4-70", 2, "ENG-FS-15/airframe", "ICD-2", "fixed",
      "FS-15 4.0 + airframe insert grip TO-DEFINE", status="TO-DEFINE (ICD-2)")
screw("HW-138", "Bleed valve to manifold BL-07 (sub-base screws, per valve)", "ISO 4762", 3.0, 25, "A4-70", 8, "ENG-BL-05/ENG-BL-07", "J-BL05",
      "fixed", "valve not selected: 4 screws per valve ASSUMED", status="TO-SELECT (valve)")
screw("HW-139", "Bleed manifold BL-07 to the airframe (ICD-14)", "ISO 4762", 4.0, 12, "A4-70", 2, "ENG-BL-07/airframe", "ICD-14", "fixed",
      "mount TO-DEFINE (ICD-14): 2 screws ASSUMED", status="TO-DEFINE (ICD-14)")
# ---------------------------------------------------------------------------------------------------------------- O-rings, seals, washers
oring("HW-150", "226", "FKM", 2, "ENG-TC-02 plug glands (S01/S02)", "J-FWD seal", "engine", note="FKM 90A (TC-02 note)")
oring("HW-151", "016", "FFKM", 1, "ENG-TC-03 flange (S03)", "TC-03 seat seal", "engine", note="v3.5.1 TB1: under the flange behind TC-10")
oring("HW-152", "013", "FKM", 1, "ENG-TC-04 bonnet face (S04)", "J-BON seal", "engine", note="FKM 75")
oring("HW-153", "012", "FKM", 1, "ENG-TC-04 transfer face (S05)", "E1-M transfer", "engine", note="FKM 75")
oring("HW-154", "010", "FKM", 1, "ENG-FD-01 cartridge cap face", "J-FD01 seal", "engine", note="FKM 75")
oring("HW-155", "013", "FKM", 1, "ENG-FD-02 cartridge radial", "filter cap", "engine", note="FKM 75")
oring("HW-156", "229", "FKM", 1, "ENG-TC-09 rod gland on the case land (S13)", "J-AFT seal", "engine", note="FKM 75")
oring("HW-157", "012", "FKM", 2, "ENG-FD-08F / ENG-FD-12F face seals", "line flanges", "fixed", note="FKM 75")
other("HW-158", "seal", "Spring-energised PTFE rod seal 4 mm (pintle stem, TC-04)", "maker catalogue", "rod 4 mm", 1, "ENG-TC-04", "stem seal",
      "engine", None, "TO-FETCH; inside the allowance", status="TO-SELECT (maker)", note="TO-VERIFY in N2O (TC-04 note)")
other("HW-159", "bushing", "PTFE / 25 % glass guide bushing (pintle stem, TC-04)", "maker catalogue", "4 mm", 1, "ENG-TC-04", "stem guide",
      "engine", None, "TO-FETCH; inside the allowance", status="TO-SELECT")
other("HW-160", "o-ring", "BL-01 face O-ring (FFKM/FKM, N2O)", "SAE AS568", "TO-SELECT", 1, "ENG-BL-01", "J-BL01 seal", "engine", None,
      "TO-FETCH; inside the allowance", status="TO-SELECT (size and groove)")
other("HW-161", "seal", "BL-02 M8x1 port seal (bonded seal or O-ring boss)", "maker catalogue", "M8x1", 1, "ENG-BL-02/ENG-FD-01", "J-BL02",
      "engine", None, "TO-FETCH; inside the allowance", status="TO-SELECT")
other("HW-162", "washer", "Crush washer M10 copper (torch IG-01 nose)", "DIN 7603 A", "10 x 14 x 1", 1, "ENG-IG-01/ENG-TC-02", "torch port",
      "engine", math.pi / 4.0 * (14.0 ** 2 - 10.0 ** 2) * 1.0 * 1e-9 * RHO["Cu"] * 1e3, "CALC (annulus x 8900)", material="Cu")
other("HW-163", "washer", "Port seals of the M10x1 transducer ports (P_feed FD-01, P_manifold TC-04) and the Pc port", "maker catalogue",
      "M10x1 / Pc port", 3, "ENG-FD-01/ENG-TC-04/ENG-TC-02", "sensor ports", "engine", None, "TO-FETCH; inside the allowance",
      status="TO-SELECT (with Electronics' transducers)")
other("HW-164", "fitting", "MSS-1 thermocouple compression fitting 1/16 tube x 1/8-27 NPT male (Swagelok SS-100-1-2 class)", "maker catalogue",
      "1/16 x 1/8 NPT", 1, "ENG-FD-05", "MSS-1", "engine", None, "TO-FETCH; inside the allowance", status="TO-SELECT")
other("HW-165", "seal", "MV-P balance-piston seal (FS-04 groove) and poppet seat seal", "maker catalogue", "11.9 piston / 14 seat", 2,
      "ENG-FS-04/ENG-FS-02", "MV-P", "fixed", None, "TO-FETCH; inside the allowance", status="TO-SELECT")
other("HW-166", "seal", "Bleed valve sub-base O-rings (2 per valve)", "SAE AS568", "TO-SELECT", 4, "ENG-BL-05/ENG-BL-07", "J-BL05", "fixed",
      None, "TO-FETCH; inside the allowance", status="TO-SELECT (valve)")
other("HW-167", "washer", "G11 isolator washers under the HV69 ears (not modelled)", "in-house", "M2", 4, "ENG-PD-12", "J-HV69", "engine",
      math.pi / 4.0 * (5.0 ** 2 - 2.2 ** 2) * 1.0 * 1e-9 * engmat.MATERIALS["G11"]["rho"]["v"] * 1e3, "CALC (5/2.2 x 1 ASSUMED x 1900)",
      status="TO-DEFINE (size)")
other("HW-168", "clip", "Bundle clip BL-04 bleed hose to the FD-07 coil", "TO-DESIGN", "", 2, "ENG-BL-04/ENG-FD-07", "hose bundle", "hose",
      None, "TO-FETCH; inside the allowance", status="TO-DESIGN")
other("HW-169", "consumable", "Thread locker / retaining compounds: Loctite 243 (GM-18, GM-20, HW-25, TC-05 stem), 648 (GM-04/05 pins), "
      "638 (PD-18), AA 3090 (EL-06); oxygen-compatible thread sealant on N2O ports TO-SELECT", "maker", "", 1, "various", "", "engine", 0.0,
      "negligible (g-level), inside the allowance", status="DEFINED")


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC / "data" / "hardware_v351.json"
    tot = {}
    unknown = []
    for r in L:
        if r["unit_mass_g"] is None:
            unknown.append(r["id"])
            continue
        tot[r["group"]] = tot.get(r["group"], 0.0) + r["unit_mass_g"] * r["qty"]
    res = {"id": "ENG-HARDWARE", "version": VERSION, "cad_version": "v3.5.1", "date": "2026-10-13", "owner": "mechanical",
           "basis": __doc__.strip().splitlines()[0], "rules": {"K_nut": K_NUT, "preload_fraction_Rp02": PRE_FRAC,
                                                             "mass": "CALC values are NOT datasheet masses; lead 188 (11) allowance 0.20 kg stays"},
           "lines": L, "n_lines": len(L), "n_items": sum(r["qty"] for r in L),
           "calc_mass_by_group_g": {k: round(v, 2) for k, v in sorted(tot.items())},
           "calc_mass_total_g": round(sum(tot.values()), 2),
           "lines_without_mass": unknown,
           "allowance": {"kg": 0.20, "source": "lead CHANGELOG 188 (11)", "status": "CARRIED (no DATASHEET masses yet)",
                         "note": "the CALC total excludes the lines without mass (valve screws included, valves' seals and COTS seals not)"}}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    print(f"{out}: {len(L)} lines, {res['n_items']} items, CALC {res['calc_mass_total_g']} g by group {res['calc_mass_by_group_g']}; "
          f"without mass {unknown}")


if __name__ == "__main__":
    main()
