"""Priced bill of materials v2, ARGOS engine ECU and engine electronics (06-electronics), 2026-10-13.

Reads:
  ../hardware/kicad/argos_ecu_bom_grouped.csv  (ECU schematic v2.4, KiCad-exported netlist, 449 symbols / 182 lines)
  parts_db.py                                  (catalogue prices recorded 2026-10-11 with URLs)
  ../results/pintle_mini_servo_v1.json         (MKS HV69 catalogue price recorded 2026-10-12 with URLs)
Writes:
  ../results/bom_v2p1.csv   one row per purchasable line
  ../results/bom_v2p1.json  rows + summary (counts, per-currency subtotals of the KNOWN catalogue prices only)
  ../results/bom_v2p1.txt   short summary

Rules (charter + founder brief):
  * Every row names a vendor to quote from and ships to Soenderborg, DK-6400 (Denmark).
  * No price is invented. A row has a price only where a named vendor's catalogue page was read and recorded with its date
    (price_basis CATALOGUE). Those are listing prices, NOT DK-6400 quotes: the delivered price (DK VAT, shipping, duty) is
    TO-QUOTE for every row. Unknown prices stay 'TO-QUOTE'; no zero and no 'from' prices are used.
  * Currencies are not converted (no dated exchange-rate source in this calc); subtotals are kept per currency.
  * Tags: DATASHEET / DESIGN / ASSUMED / AS-RECALLED (memory, TO-VERIFY at quote) / LEAD / MECH / COMB.
"""
import csv
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts_db  # noqa: E402

VERSION = "v2.1"   # v2.1 2026-10-13: head-end bleed provision (schematic v2.4, calc/hbleed_provision_v1.py)
DATE = "2026-10-13"
SHIP_TO = "Soenderborg, DK-6400, Denmark"
GROUPED = os.path.join(HERE, "..", "hardware", "kicad", "argos_ecu_bom_grouped.csv")
SERVO_STUDY = os.path.join(HERE, "..", "results", "pintle_mini_servo_v1.json")
OUT = os.path.join(HERE, "..", "results")

MOUSER = "Mouser Electronics (mouser.dk)"
DIGIKEY = "Digi-Key (digikey.dk)"
FARNELL = "Farnell (dk.farnell.com)"
TOQ = "TO-QUOTE"


def sha16(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def row(section, refs, qty, part, desc, vendor, vendor_alt="", order_key="", price=None, cur="", basis=TOQ, src="",
        tag="DESIGN", spare="", owner="Electronics", note=""):
    if price is not None and (price <= 0 or basis != "CATALOGUE"):
        raise ValueError("a price must be a positive catalogue value with a source: " + part)
    if price is None and basis != TOQ and not basis.startswith("NO PURCHASE"):
        raise ValueError("an unpriced row must be TO-QUOTE or NO PURCHASE: " + part)
    if not vendor:
        raise ValueError("every row needs a named vendor: " + part)
    return OrderedDict([
        ("section", section), ("refs", refs), ("qty", qty), ("spare_recommended", spare), ("part", part),
        ("description", desc), ("vendor", vendor), ("vendor_alt", vendor_alt), ("order_key", order_key),
        ("unit_price", "" if price is None else price), ("currency", cur), ("price_basis", basis), ("price_source", src),
        ("delivered_price_DK6400", "TO-QUOTE (DK VAT, shipping and duty to " + SHIP_TO + ")"
         if not basis.startswith("NO PURCHASE") else "n/a"),
        ("tag", tag), ("owner", owner), ("note", note)])


# ---------------------------------------------------------------------------------------------------------------- A. ECU PCB
# Connector order keys come from the KiCad footprint names (stock KiCad 7.0.11 library); order suffixes are confirmed at quote.
CONN_FROM_FP = [
    (r"JST_GH_(SM\d\dB-GHS-TB)", "JST {0} (GH 1.25 mm, top entry SMD); order suffix TO-CONFIRM"),
    (r"Molex_Micro-Fit_3.0_(43650-0\d00)", "Molex {0} (Micro-Fit 3.0 right-angle header)"),
    (r"AMASS_(XT60PW-M)", "AMASS {0} (XT60 PCB male, horizontal)"),
    (r"AMASS_(XT30PW-M)", "AMASS {0} (XT30 PCB male, horizontal)"),
    (r"TerminalBlock_Phoenix_(MPT-0,5-2-2.54)", "Phoenix Contact MPT 0,5/2-2,54 (2-pole 2.54 mm terminal block); order no. TO-CONFIRM"),
    (r"Fuseholder_Blade_Mini_Keystone_(\d+)", "Keystone {0} mini-blade fuse holder (from footprint)"),
]


def conn_key(fp):
    for pat, fmt in CONN_FROM_FP:
        m = re.search(pat, fp)
        if m:
            return fmt.format(m.group(1))
    return ""


def pkg(fpn):
    """Package text from a stock KiCad footprint name (R_0603_1608Metric -> 0603; CP_Elec_10x10.5 -> electrolytic 10x10.5 mm)."""
    m = re.match(r"[RC]_(\d{4})_", fpn)
    if m:
        return m.group(1)
    m = re.match(r"CP_Elec_([\dx.]+)", fpn)
    if m:
        return "SMD electrolytic/polymer " + m.group(1) + " mm"
    m = re.match(r"L_(\w+?)_(\w+)", fpn)
    if m:
        return m.group(1) + " " + m.group(2) + " footprint"
    return fpn


def ecu_pcb_rows():
    rows = []
    with open(GROUPED, newline="") as f:
        lines = list(csv.DictReader(f))
    n_sym = sum(int(r["qty"]) for r in lines)
    for r in lines:
        refs, qty, val, fp, mpn = r["refs"], int(r["qty"]), r["value"], r["footprint"], r["mpn"]
        first = refs.split()[0]
        prefix = re.match(r"[A-Z]+", first).group(0)
        fpn = fp.split(":")[-1]
        desc = (r["function"] or r["value"])[:160]
        spec = r["spec_source"][:160]
        if prefix == "TP":
            rows.append(row("A ECU PCB", refs, qty, val, "test pad (copper pad on the PCB)", "PCB fabricator (section B)",
                            order_key=fpn, basis="NO PURCHASE (PCB copper pad)", tag="DESIGN"))
            continue
        if prefix == "H":
            rows.append(row("A ECU PCB", refs, qty, "M3 mounting hole", "plated hole on the PCB; hardware in section B",
                            "PCB fabricator (section B)", order_key=fpn, basis="NO PURCHASE (PCB hole)", tag="DESIGN"))
            continue
        if first == "U201":
            t = parts_db.TEENSY41
            p = t["price"]
            rows.append(row("A ECU PCB", refs, qty, "PJRC Teensy 4.1 (SparkFun DEV-16771)", "MCU module on 2 x 1x24 sockets",
                            "Electrokit (electrokit.com, SE)", "PJRC (pjrc.com, US)", "Teensy 4.1", p["price"], p["cur"],
                            "CATALOGUE", p["src"] + " (accessed " + parts_db.ACCESS + "; " + p["note"] + ")",
                            "DATASHEET (vendor listing)", spare="1 (bench/HIL board)"))
            continue
        if first == "PS501":
            rows.append(row("A ECU PCB", refs, qty, "Pololu U3V70F12 (item #2895)", "12 V boost module on the ARM bus (spark coil, solenoids)",
                            "Pololu (pololu.com, US)", "EU Pololu reseller (TO-SELECT at quote)", "2895", tag="DATASHEET (Pololu #2895)",
                            spare="1"))
            continue
        if first == "L801":
            rows.append(row("A ECU PCB", refs, qty, "Coilcraft XAL1010-472ME", "pintle-rail inductor 4.7 uH",
                            "Coilcraft (coilcraft.com, direct)", MOUSER, "XAL1010-472ME", tag="DESIGN (pintle_rail_v3, ecu_v2p3_values_v1)",
                            spare="1"))
            continue
        if first == "U801":
            rows.append(row("A ECU PCB", refs, qty, "TI TPS552882RPMR", "pintle-rail buck-boost controller (VQFN-HR 26)",
                            MOUSER, DIGIKEY, "TPS552882RPMR", tag="DESIGN (pintle_rail_v3)", spare="2 (VQFN-HR hand rework risk)",
                            note="footprint in KiCad is TI_RPM0026A_PLACEHOLDER (NOT FOR FABRICATION): use TI's RPM0026A land pattern"))
            continue
        if first == "U802":
            rows.append(row("A ECU PCB", refs, qty, "Analog Devices LTC4365HTS8", "pintle-rail OV/UV disconnect (H grade, TSOT-23-8)",
                            MOUSER, DIGIKEY, "LTC4365HTS8 + tape/lead-free order suffix TO-CONFIRM", tag="DESIGN (pintle_rail_v3)",
                            spare="1", note="ADI page shows only a 'from' price (not used); analog.com blocked at the proxy (403)"))
            continue
        if prefix == "J":
            key = conn_key(fp)
            rows.append(row("A ECU PCB", refs, qty, key.split(" (")[0] if key else val, "board connector: " + desc,
                            MOUSER, DIGIKEY, key or fpn, tag="DESIGN (footprint = stock KiCad 7.0.11)", spare="",
                            note="mating half in section F"))
            continue
        if prefix == "F":
            rows.append(row("A ECU PCB", refs, qty, mpn or val, "fuse: " + desc, MOUSER, DIGIKEY, mpn or val,
                            tag="DESIGN", spare=str(qty * 2), note="holder: " + (conn_key(fp) or fpn)))
            continue
        if prefix in ("U", "Q", "D", "Y"):
            rows.append(row("A ECU PCB", refs, qty, mpn or val, desc or val, MOUSER, DIGIKEY, mpn or val,
                            tag="DESIGN (" + (spec or "ecu_design.py") + ")", spare="1" if prefix == "U" else str(max(2, qty // 2))))
            continue
        # passives (R, C, L101): generic value + package; MPN chosen at quote against the stated tolerance/dielectric
        rows.append(row("A ECU PCB", refs, qty, val + ", " + pkg(fpn),
                        desc or ("passive " + val), MOUSER, DIGIKEY,
                        "value + package + tolerance/dielectric as stated; MPN TO-SELECT at quote", tag="DESIGN (" + (spec or "ecu_design.py") + ")",
                        spare="cut-tape minimum (>= 10 per value)"))
    return rows, len(lines), n_sym


# ------------------------------------------------------------------------------------------------- B. ECU mechanics, PCB fab
def ecu_mech_rows():
    return [
        row("B ECU PCB fab + mechanics", "PCB", 1, "4-layer FR-4 PCB, 1.6 mm, ~120 x 60 mm (DESIGN reservation)",
            "bare board for the v2.3 schematic", "JLCPCB (jlcpcb.com, CN)", "Eurocircuits (eurocircuits.com, BE); PCBWay (CN)",
            "Gerbers after layout", tag="DESIGN (electronics.json v1 pcb_outline_mm)", spare="fab minimum lot (typ. 5)",
            note="BLOCKED: no layout yet, so it cannot be quoted"),
        row("B ECU PCB fab + mechanics", "U201 sockets", 2, "1x24 female header 2.54 mm, through-hole",
            "Teensy 4.1 sockets (footprint Teensy41_Socket)", MOUSER, DIGIKEY, "1x24 2.54 mm female header; MPN TO-SELECT",
            tag="DESIGN", spare="2"),
        row("B ECU PCB fab + mechanics", "H101-H104", 4, "M3 x 8 mm standoff + M3 screw (A2 stainless or nylon)",
            "board mounting", MOUSER, "local hardware supplier", "M3 standoff/screw set", tag="DESIGN", spare="4"),
        row("B ECU PCB fab + mechanics", "ENCL", 1, "ECU enclosure, reservation 128 x 68 x 32 mm (PETG print or 1 mm aluminium)",
            "ECU enclosure on the fixed thrust structure", "Hammond Manufacturing via " + MOUSER, "founder 3D print (PETG)",
            "size TO-SELECT after layout", tag="DESIGN (electronics.json v1 enclosure_envelope_mm)", note="model TO-SELECT after layout"),
        row("B ECU PCB fab + mechanics", "ARM plug", 1, "XT30 female with a shorting link (remove-before-flight arming plug) + flag",
            "arming plug for J301", "Lindinger (lindinger.at, AT)", MOUSER, "XT30 female + RBF flag", tag="DESIGN", spare="1"),
    ]


# -------------------------------------------------------------------------------------------------------------- C. actuators
def actuator_rows():
    s = parts_db.SB2292SG
    lp = s["suppliers"][0]
    alts = "; ".join("%s %.2f %s (%s)" % (x["vendor"], x["price"], x["cur"], x["note"]) for x in s["suppliers"][1:])
    hv = json.load(open(SERVO_STUDY))
    hv69 = [c for c in hv["candidates"] if c.get("id") == "MKS HV69"]
    if len(hv69) != 1:
        raise ValueError("MKS HV69 entry not found once in pintle_mini_servo_v1.json")
    hvp = hv69[0]["price"][0]
    if hvp["vendor"] != "Lindinger (AT)":
        raise ValueError("unexpected first HV69 price entry: " + hvp["vendor"])
    return [
        row("C actuators", "J401 J402 J404", 3, "Savox SB-2292SG", "TVC servo A (pitch), TVC servo B (yaw), MV-P opener servo",
            "Lindinger (lindinger.at, AT)", alts, "Lindinger item 9738546", lp["price"], lp["cur"], "CATALOGUE",
            lp["src"] + " (accessed " + parts_db.ACCESS + "; " + lp["note"] + ")", "DATASHEET (vendor listing)", spare="1 (bench damage risk)",
            note="SB-2292SG rated -10..50 C: bay <= 45 C at ARM (lead line 91)"),
        row("C actuators", "J403", 1, "MKS HV69", "pintle throttle servo on PRAIL 7.49 V (ENG-03 rate map, B-PNT-1)",
            "Lindinger (lindinger.at, AT)", "Aloft Hobbies / Extreme Flight (US; listed sold out 2026-10-12)", hv69[0]["pn"],
            hvp["v"], hvp["cur"], "CATALOGUE", hv69[0]["src"][0] + " (2026-10-12; " + hvp["note"] + ")",
            "DATASHEET (vendor listing; MKS data via retailer copies)", spare="1 (B-PNT-1 torque-speed test to stall)"),
    ]


# ------------------------------------------------------------------------------------------------------------ D. sensors
def sensor_rows():
    m = parts_db.M3200
    ref = m["price_ref"]
    pref = "price reference only, NOT this part: RS UK %s %.2f %s %s" % (ref["vendor"], ref["price"], ref["cur"], ref["note"])
    return [
        row("D vehicle sensors", "J601 J901", 2, "TE M3234-000005-070BG", "Pc and P_torch, 0-70 bar g, 0.5-4.5 V ratiometric, 1/4-18 NPT, Packard A",
            MOUSER, FARNELL + "; RS Components (dk.rs-online.com)", "M3234-000005-070BG", tag="DESIGN (pc_transducer_v2; lead line 73)",
            spare="1", note=pref + "; oxygen-clean before N2O service"),
        row("D vehicle sensors", "J602 J603", 2, "TE M3234-000005-170BG", "P_feed and P_tank, 0-170 bar g (proof 340 bar)",
            MOUSER, FARNELL + "; RS Components (dk.rs-online.com)", "M3234-000005-170BG", tag="DESIGN (pc_transducer_v2; lead line 73)",
            spare="1", note="P_feed J602 on the FS-01 MV-outlet block (MECH)"),
        row("D vehicle sensors", "J610 J611 J612", 3, "ams-OSRAM AS5048A on a small sensor PCB (or the AS5048A adapter board)",
            "gimbal axis A/B and pintle crank angle, 14-bit SPI", MOUSER, DIGIKEY,
            "AS5048A IC (TSSOP-14) or ams adapter board; exact order code TO-CONFIRM", tag="DATASHEET (electronics.json v1)", spare="1"),
        row("D vehicle sensors", "magnets", 3, "diametric NdFeB magnet dia. 6 x 2.5-3 mm", "AS5048A target magnets",
            "supermagnete (supermagnete.de, DE)", MOUSER, "diametric 6 x 2.5 mm; grade TO-SELECT", tag="DATASHEET class (electronics.json v1)",
            spare="3"),
        row("D vehicle sensors", "J605 J606", 2, "type K thermocouple, IEC 60584 Class 1, bonded/spot-welded pad", "case TCs az 90 / az 270 (case abort 448.15 K, 0.2 s)",
            "TC Ltd (tc.co.uk, UK)", "Omega Engineering (omega.co.uk)", "type K, glass-braid or MI 1.5 mm; length TO-DEFINE", tag="LEAD line 91 / MECH",
            spare="1"),
        row("D vehicle sensors", "J607", 1, "type K thermocouple", "nozzle-holder TC (flag 523.15 K ASSUMED)",
            "TC Ltd (tc.co.uk, UK)", "Omega Engineering (omega.co.uk)", "type K; length TO-DEFINE", tag="DESIGN"),
        row("D vehicle sensors", "J904", 1, "type K MI thermocouple", "bore-top / manifold TC (CF-3/T1 evidence; flight use TO-DEFINE)",
            "TC Ltd (tc.co.uk, UK)", "Omega Engineering (omega.co.uk)", "type K MI; length TO-DEFINE", tag="DESIGN (fw v2.7)"),
        row("D vehicle sensors", "J905 J906", 2, "type T thermocouple, IEC 60584 Class 1, MI 316 SS 1/16 in, ungrounded",
            "MSS-1 (riser-foot TEE, sheath >= 200 mm) and MSS-2 (NC-valve outlet, FS-01)", "TC Ltd (tc.co.uk, UK)",
            "Omega Engineering (omega.co.uk)", "type T MI 1/16 in 316 SS ungrounded; length MSS-1 >= 200 mm", tag="LEAD lines 75, 83; MECH line 86",
            spare="1"),
        row("D vehicle sensors", "TC fittings", 2, "Swagelok SS-100-1-2BT (1/16 in tube x 1/8 MNPT bored-through)",
            "MSS-1/MSS-2 compression fittings, oxygen-cleaned", "Swagelok (authorised distributor for Denmark, via swagelok.com)", "",
            "SS-100-1-2BT + O2-clean suffix TO-CONFIRM", tag="DESIGN (Electronics proposal, lead line 75)", owner="Electronics + Mechanical (port)",
            spare="1"),
        row("D vehicle sensors", "J608 J614", 3, "Analog Devices (Maxim) DS18B20", "tank wall x2 and bay temperature (#3) on 1-Wire",
            MOUSER, DIGIKEY, "DS18B20+ (TO-92) or stainless probe version", tag="DESIGN", spare="1"),
        row("D vehicle sensors", "J609", 1, "NTC 10k thermistor (B-value TO-SELECT), ring lug", "pintle-servo bracket temperature (HV69 flag 60 C)",
            MOUSER, DIGIKEY, "10k NTC ring-lug type", tag="DESIGN"),
    ]


# ------------------------------------------------------------------------------------- E. driven items owned elsewhere (no price)
def driven_rows():
    owner_note = "selected and priced by the owning discipline; ECU channel limits in electronics.json v2"
    rows = []
    for refs, part, desc, owner in [
        ("J501", "spark coil + torch spark plug", "torch igniter, IGBT driver with hardware-limited dwell", "Combustion"),
        ("J502", "SOL1 torch N2O solenoid valve (12 V)", "torch oxidiser valve", "Combustion / Mechanical"),
        ("J503", "SOL2 torch propane solenoid valve (12 V)", "torch fuel valve", "Combustion / Mechanical"),
        ("J507", "SOL3 tank vent solenoid valve (VBAT, PWM hold)", "tank vent", "Mechanical"),
        ("J504 J505", "SOL4/SOL5 roll RCS valve pairs (12 V)", "roll provision", "GNC / Mechanical"),
        ("J506", "MV-P over-centre latch magnet (<= 4 W)", "MV-P holding magnet", "Mechanical (MV-P)"),
        ("J508", "MV-P OPEN/CLOSED microswitches (sealed)", "valve position", "Mechanical (MV-P)"),
    ]:
        rows.append(row("E driven items owned elsewhere", refs, 1, part, desc, "owner's vendor (see owner)", "",
                        "", basis="NO PURCHASE here (owner: " + owner + ")", tag="interface", owner=owner, note=owner_note))
    return rows


# ------------------------------------------------------------------------------------------------------------------ F. harness
def bleed_rows():
    """v2.1: head-end bleed PROVISION, off-board items (the board parts U307, U570, Q570, Q580/Q590 ... come from the grouped BOM)."""
    own = "Mechanical (valve, fittings) / Electronics (coil drive, P_mid chain)"
    return [
        row("F bleed", "J509 J510 (V1 V2)", 2, "Burkert 6027 HP class NC 2/2 solenoid valve, stainless G1/4, PEEK/FKM seat, orifice 1.0 mm",
            "head-end bleed V1 (upstream, T4) and V2 (downstream), in series, fixed side; DS: 1.0 mm 0-250 bar DC (air/water), switching "
            "DC open 20-30 / close 50-80 ms, medium -10..80 C (HP PEEK/FKM), coil 42 (K) 16 W cold (column mapping TO-VERIFY)",
            "Burkert Fluid Control Systems (DK sales office)", "Parker Hannifin (high-pressure miniature NC valve)", "", None, "", TOQ,
            "ds6027-standard-eu-en.pdf (WebFetch summary 2026-10-13)", tag="DATASHEET", spare="1", owner=own,
            note="coil voltage: product page lists 24 V DC / 230 V AC; the ECU drive is +12V_ARM -> 12 V DC coil TO-VERIFY or a 24 V "
                 "boost (open issue); mass not stated TO-VERIFY; N2O compatibility of PEEK/FKM TO-VERIFY with the vendor"),
        row("F bleed", "J511 (P_mid)", 1, "TE Connectivity M3234-000005-170BG class pressure transducer (0-170 bar g, 0.5-4.5 V)",
            "P_mid between V1 and V2 (fixed-side tee, mid volume <= 0.5 cm3 ICD) -> LMV331 comparator 9.86 / 8.86 bar g",
            MOUSER, DIGIKEY, "", None, "", TOQ, "TE M3200 series datasheet (range code availability TO-VERIFY at quote)",
            tag="DATASHEET", spare="1", owner="Electronics"),
        row("F bleed", "J508 backshell", 3, "thin-film resistors 1 % 0.25 W axial: 82.5k (R0 end of line), 9.53k (R1 OPEN), 17.8k (R2 CLOSED)",
            "MV switch ladder resistors in the J508 mating backshell (potted); values calc/hbleed_provision_v1.py", MOUSER, DIGIKEY, "",
            None, "", TOQ, "calc/hbleed_provision_v1.json", tag="DESIGN", spare="3", owner="Electronics"),
        row("F bleed", "J509 J510 J511 harness", 1, "harness: 2 x 2-wire valve leads (18 AWG, fixed side) + 3-wire P_mid lead (shielded) + JST GH / "
            "Micro-Fit housings and contacts", "routing on the fixed side only (no gimbal crossing); lengths TO-VERIFY from the CAD",
            MOUSER, DIGIKEY, "", None, "", TOQ, "", tag="DESIGN", owner="Electronics"),
    ]


def harness_rows():
    R = "AS-RECALLED part family, TO-VERIFY at quote"
    return [
        row("F harness", "J401-J404 J501-J507 J616", 13, "Molex Micro-Fit 3.0 receptacle housings (2/3/4-way) + female crimp terminals",
            "mating halves for the Micro-Fit headers", MOUSER, DIGIKEY, "43645-0x00 housings + 43030 crimps (" + R + ")", tag="DESIGN",
            spare="+50 % terminals"),
        row("F harness", "J201 J508 J601-J604 J608-J614 J620 J901", 16, "JST GH housings (GHR-0xV-S) + SSHL crimp contacts",
            "mating halves for the GH headers", MOUSER, DIGIKEY, "GHR-0xV-S + SSHL-002T-P0.2 (" + R + ")", tag="DESIGN", spare="+50 % contacts"),
        row("F harness", "transducers", 4, "Packard A / Metri-Pack 150 3-way mating connector kit", "M3200 connector code 4 mates",
            MOUSER, "Aptiv distributor", "per TE M3200 datasheet connector code 4; MPN TO-SELECT", tag="DATASHEET (TE M3200)", spare="1"),
        row("F harness", "J101", 1, "XT60 female + AWG14 silicone lead", "battery lead", "Lindinger (lindinger.at, AT)", MOUSER, "XT60 female",
            tag="DESIGN", spare="1"),
        row("F harness", "gimbal crossing", 1, "PTFE/FEP-insulated AWG20 (servo) + shielded AWG26 4-core (encoder) + K/T extension wire, glass sleeve",
            "service loop across the gimbal (>= 100 mm free length, bend radius >= 10 x OD)", "TC Ltd (extension wire)", MOUSER + " (Alpha Wire / similar)",
            "lengths after CAD v3.4 routing", tag="DESIGN (electronics.json v1 harness_across_gimbal)", note="lengths TO-DEFINE on the v3.4 solids"),
        row("F harness", "CAN", 1, "twisted pair + GND + shield, <= 2 m, JST GH 4-way both ends", "FC <-> ECU CAN", MOUSER, DIGIKEY,
            "CAN cable (120 ohm class)", tag="DESIGN"),
        row("F harness", "J620", 1, "mode-strap plug (FLIGHT and STAND variants, resistor-coded per ecu_v2p3_values_v1)", "harness mode strap",
            MOUSER, "", "JST GH 3-way housing with the strap wiring", tag="LEAD line 85", spare="1 of each variant"),
        row("F harness", "J616", 1, "GSE heater-permit cable (<= 28 V, <= 1 A)", "tank-heater interlock to GSE", MOUSER, "",
            "Micro-Fit 2-way cable", tag="DESIGN"),
    ]


# ------------------------------------------------------------------------------------------------------------------- G. power
def power_rows():
    return [
        row("G power", "battery", 1, "LiPo 2S1P 2.2 Ah, >= 25C, XT60", "flight pack (VBAT 6.6-8.4 V)", "Lindinger (lindinger.at, AT)", "",
            "2S 2200 mAh >= 25C; model TO-SELECT", tag="DESIGN (electronics.json v1)", spare="1",
            note="ARM rest-voltage rule >= 8.1 V (LEAD 2026-10-12)"),
        row("G power", "fuses", 1, "ATM mini-blade fuse assortment (15 A, 25 A)", "spares for F101/F301", MOUSER, "", "Littelfuse 0297015 / 0297025",
            tag="DESIGN"),
    ]


# ----------------------------------------------------------------------------------------------- H. test stand + bench instruments
def stand_rows():
    return [
        row("H test stand + bench", "stand box", 1, "test-stand box: Teensy 4.1 + CAN transceiver + e-stop + key switch + burst-disc break-wire loop",
            "FC emulator on the stand (same protocol encoders as the FC and SIL)", "Electrokit (electrokit.com, SE)", MOUSER,
            "Teensy 4.1 + MCP2562FD + enclosure", tag="DESIGN (protocol.h; lead line 88 break-wire)", note="enclosure and switches TO-SELECT"),
        row("H test stand + bench", "J604", 1, "S-type load cell, 1 kN, 2 mV/V class", "thrust (stand); read by ADC1 CH3 (PGA 64-128)",
            "HBK - Hottinger Brüel & Kjær (hbkworld.com, DK)", "other S-type maker (TO-SELECT)", "model TO-SELECT", tag="DESIGN (electronics.json v1)"),
        row("H test stand + bench", "fast Pc", 1, "stand-only fast high-range Pc transducer, range >= 135 bar (>= 2 x proof 67.5 bar), bandwidth >= 10 kHz",
            "hard-start / throat-block evidence (lead line 79)", "Kistler (kistler.com)", "TE Connectivity / Kulite distributor", "model TO-SELECT",
            tag="LEAD line 79 (COMB proposal)", note="mount on a stand-only port (MECH)"),
        row("H test stand + bench", "stand DAQ", 1, "stand DAQ >= 4 ch, >= 10 kS/s per channel, hardware-timed, external sync/trigger input",
            "fast Pc, load cell copy, manifold-tip TC, sync GPIO (common time base <= 1 ms, over_thrust_v3)", "LabJack (labjack.com, US) via EU reseller",
            "National Instruments (ni.com)", "model TO-SELECT", tag="DESIGN (RG-19 common time base)", note="founders may already own a DAQ"),
        row("H test stand + bench", "CAN analyser", 1, "USB CAN 2.0B analyser with hardware timestamps", "CAN capture on the common time base",
            "PEAK-System (peak-system.com, DE)", "Kvaser (kvaser.com, SE)", "PCAN-USB class; model TO-SELECT", tag="DESIGN (over_thrust_v3)"),
        row("H test stand + bench", "manifold tip", 1, "type K or T MI thermocouple, stand-only manifold tip", "T4 evidence instrumentation (MECH line 86)",
            "TC Ltd (tc.co.uk, UK)", "Omega Engineering (omega.co.uk)", "MI 1 mm; length TO-DEFINE", tag="LEAD line 87"),
        row("H test stand + bench", "B-PNT-1 rig", 1, "rotary torque sensor + brake/load for the HV69 torque-speed line (0.42-0.55 N m, 7.335/7.49 V)",
            "B-PNT-1 servo characterisation", "HBK - Hottinger Brüel & Kjær (hbkworld.com, DK)", "Lorenz Messtechnik (DE)",
            "range ~1 N m class; model TO-SELECT", tag="DESIGN (bench_plan_v2 B-PNT-1)", owner="Electronics + Mechanical"),
        row("H test stand + bench", "instruments", 1, "oscilloscope >= 4 ch >= 100 MHz with a current probe; electronic load >= 5 A; bench PSU 0-30 V >= 15 A; DMM",
            "B-PWR-1/2, B-IGN, B-MV-1 measurements", "Rohde & Schwarz / Keysight / Rigol via " + FARNELL, "",
            "only if not already owned", tag="DESIGN", note="founders may already own these"),
    ]


def main():
    a_rows, n_lines, n_sym = ecu_pcb_rows()
    rows = a_rows + ecu_mech_rows() + actuator_rows() + sensor_rows() + driven_rows() + bleed_rows() + harness_rows() + power_rows() + stand_rows()
    for i, r in enumerate(rows, 1):
        r["line"] = i
        r.move_to_end("line", last=False)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "bom_v2p1.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    known = OrderedDict()
    for r in rows:
        if r["price_basis"] == "CATALOGUE":
            known.setdefault(r["currency"], 0.0)
            known[r["currency"]] += float(r["unit_price"]) * int(r["qty"])
    n_toq = sum(1 for r in rows if r["price_basis"] == TOQ)
    n_cat = sum(1 for r in rows if r["price_basis"] == "CATALOGUE")
    n_np = sum(1 for r in rows if r["price_basis"].startswith("NO PURCHASE"))
    sections = OrderedDict()
    for r in rows:
        s = sections.setdefault(r["section"], {"lines": 0, "to_quote": 0, "catalogue": 0, "no_purchase": 0})
        s["lines"] += 1
        s["to_quote"] += r["price_basis"] == TOQ
        s["catalogue"] += r["price_basis"] == "CATALOGUE"
        s["no_purchase"] += r["price_basis"].startswith("NO PURCHASE")
    summary = OrderedDict([
        ("id", "bom"), ("version", VERSION), ("date", DATE), ("owner", "electronics (06-electronics)"),
        ("ship_to", SHIP_TO),
        ("inputs", {"argos_ecu_bom_grouped.csv": {"sha256_16": sha16(GROUPED), "lines": n_lines, "symbols": n_sym,
                                                  "schematic": "ECU v2.3 (KiCad 7.0.11, ERC 0/0)"},
                    "parts_db.py": {"sha256_16": sha16(os.path.join(HERE, "parts_db.py")), "access": parts_db.ACCESS},
                    "pintle_mini_servo_v1.json": {"sha256_16": sha16(SERVO_STUDY)}}),
        ("rows", len(rows)), ("rows_catalogue_priced", n_cat), ("rows_to_quote", n_toq), ("rows_no_purchase", n_np),
        ("sections", sections),
        ("known_catalogue_subtotal_by_currency", {k: round(v, 2) for k, v in known.items()}),
        ("known_subtotal_note", "listing prices incl. the vendor's local VAT, before shipping; NOT DK-6400 quotes and NOT a total"),
        ("total", "UNKNOWN: %d rows are TO-QUOTE (no zero and no 'from' prices used); currencies not converted" % n_toq),
        ("blocked", ["ECU PCB fabrication cannot be quoted before layout",
                     "TPS552882 footprint is a placeholder (TI RPM0026A land pattern needed)",
                     "LTC4365 order suffix and UV threshold TO-CONFIRM (analog.com 403 at the proxy)"]),
        ("tags", "CATALOGUE = vendor listing read and recorded with date and URL; TO-QUOTE = named vendor, price unknown; "
                 "NO PURCHASE = PCB feature or item owned and priced by another discipline"),
    ])
    with open(os.path.join(OUT, "bom_v2p1.json"), "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=1, ensure_ascii=False)
    lines = ["bom_v2 (Electronics %s): %d rows; %d CATALOGUE-priced, %d TO-QUOTE, %d no purchase; ship to %s"
             % (DATE, len(rows), n_cat, n_toq, n_np, SHIP_TO),
             "ECU PCB from argos_ecu_bom_grouped.csv %s: %d lines, %d symbols" % (sha16(GROUPED), n_lines, n_sym)]
    for k, v in sections.items():
        lines.append("  %-34s %3d rows (%d TO-QUOTE, %d catalogue, %d no purchase)" % (k, v["lines"], v["to_quote"], v["catalogue"], v["no_purchase"]))
    lines.append("known catalogue subtotal (listing prices, NOT a total, NOT DK-6400 quotes): " +
                 ", ".join("%.2f %s" % (v, k) for k, v in known.items()))
    lines.append("TOTAL: " + summary["total"])
    with open(os.path.join(OUT, "bom_v2p1.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
