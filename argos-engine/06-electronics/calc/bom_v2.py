"""Priced bill of materials v2 (v2.2), ARGOS engine ECU and engine electronics (06-electronics), 2026-10-13.
v2.2 (firmware v2.10, schematic v2.5): purge-window parts (U571-U575, J512) and the FA-1 photodiode head (J902) via the grouped BOM;
item 208 (bleed valve) REPLACED by the LEAD l.160 (6) / 166 (3) specification (no candidate verified yet: research note in the
v2.10 report); RE-14 bench rows (Coriolis, reference gauge, bleed plumbing, N2 purge supply, decade box, transducer simulator, catch
volume); LEAD 172 (2) stand dynamic Pc channel B-DPC-1 (PCB 113B24 + NI 9234); LEAD 161 (6) GSE anemometer; RE-22 O2-clean and
medium-temperature notes on every N2O-wetted row. LEAD 194 (7) (same v2.2 file, re-run 2026-10-13): B-DPC-1 sensor 113B24 -> 113B22
(>= 100 bar abs with the proof rating; qty 3 = head + line end + spare), NI 9234 row with the coupling and compliance values, reference
calibrator row with the hydraulic pump for the 070BG over-range row.

Reads:
  ../hardware/kicad/argos_ecu_bom_grouped.csv  (ECU schematic v2.5, KiCad-exported netlist)
  parts_db.py                                  (catalogue prices recorded 2026-10-11 with URLs)
  ../results/pintle_mini_servo_v1.json         (MKS HV69 catalogue price recorded 2026-10-12 with URLs)
Writes:
  ../results/bom_v2p2.csv   one row per purchasable line
  ../results/bom_v2p2.json  rows + summary (counts, per-currency subtotals of the KNOWN catalogue prices only)
  ../results/bom_v2p2.txt   short summary

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

VERSION = "v2.2"   # v2.2 2026-10-13: schematic v2.5, item 208 replaced, RE-14/RE-22, B-DPC-1, anemometer (v2.1: bleed provision)
DATE = "2026-10-13"
SHIP_TO = "Soenderborg, DK-6400, Denmark"
GROUPED = os.path.join(HERE, "..", "hardware", "kicad", "argos_ecu_bom_grouped.csv")
SERVO_STUDY = os.path.join(HERE, "..", "results", "pintle_mini_servo_v1.json")
OUT = os.path.join(HERE, "..", "results")

MOUSER = "Mouser Electronics (mouser.dk)"
DIGIKEY = "Digi-Key (digikey.dk)"
FARNELL = "Farnell (dk.farnell.com)"
TOQ = "TO-QUOTE"
O2 = ("RE-22: N2O-wetted - oxygen-clean (oil/grease-free, cleaned and bagged per ASTM G93 / CGA G-4.1 class, TO-CONFIRM with the "
      "vendor); medium-temperature class must cover flashing N2O (1 atm saturation about -88 C, LITERATURE) - vendor rating TO-VERIFY")


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
            spare="1", note=pref + "; " + O2),
        row("D vehicle sensors", "J602 J603", 2, "TE M3234-000005-170BG", "P_feed and P_tank, 0-170 bar g (proof 340 bar)",
            MOUSER, FARNELL + "; RS Components (dk.rs-online.com)", "M3234-000005-170BG", tag="DESIGN (pc_transducer_v2; lead line 73)",
            spare="1", note="P_feed J602 on the FS-01 MV-outlet block (MECH); " + O2),
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
            spare="1", note=O2),
        row("D vehicle sensors", "J608 J614", 3, "Analog Devices (Maxim) DS18B20", "tank wall x2 and bay temperature (#3) on 1-Wire",
            MOUSER, DIGIKEY, "DS18B20+ (TO-92) or stainless probe version", tag="DESIGN", spare="1"),
        row("D vehicle sensors", "J609", 1, "NTC 10k thermistor (B-value TO-SELECT), ring lug", "pintle-servo bracket temperature (HV69 flag 60 C)",
            MOUSER, DIGIKEY, "10k NTC ring-lug type", tag="DESIGN"),
        row("D vehicle sensors", "J902", 1, "FA-1 flame-light head: Si photodiode + logarithmic transimpedance amplifier, window, 5 V, 0-5 V out",
            "torch / main flame light confirmation (firmware v2.10 FA-1: valid 0.02-4.80 V, rise 0.20 V placeholder set by IGN-1); head "
            "design, optics, window material and mounting TO-DEFINE (Electronics + Combustion port)", MOUSER, DIGIKEY,
            "photodiode (Hamamatsu S1336 class) + log TIA (TI LOG114 class): AS-RECALLED part families, TO-SELECT", tag="DESIGN",
            spare="1", note="no flight heritage claimed; IGN-1 measures dark level, spark-flash rejection and lit rise"),
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
        row("F bleed", "J509 J510 (V1 V2)", 2, "head-end bleed valve, NC 2/2, 12 V DC coil, seat >= 2.0 mm or Kv >= 0.11 m3/h VERIFIED at 55 bar, "
            "medium class covering flashing N2O, <= 0.15 kg each (LEAD l.160 (6), 166 (3)) - REPLACES v2.1 item 208 (Burkert 6027 1.0 mm)",
            "V1 (upstream) and V2 (downstream), in series, fixed side; decided path: 0.707 mm restrictor per tap upstream of V1, valves >= 4 x "
            "the restriction capacity (Kv >= 0.11 m3/h DERIVED: 4 x a 1.0 mm Cd 0.7 orifice); peak-and-hold drive with fast release",
            "TO-SELECT: no qualifying candidate. Screened and NOT qualifying: Burkert 6027 family (LEAD l.160 (6) rejected the 1.0 mm HP; "
            "the 1.5 mm variant fails Kv); open lead: NOS / Holley (via EU distributor), criteria not shown",
            "screening 2026-10-13, no part verified on all four criteria (v2.10 report, valve research)", "", None, "", TOQ,
            "Screened (not qualifying): burkert.com article 20095720 (6027, 1.50 mm, 0-150 bar, 12 V, oxide ceramics); tameson 369597 (Kv 0.07 m3/h). "
            "Open lead: NOS 18020BNOS Powershot listing (orifice 5/64 in = 1.98 mm, PTFE plunger, 12 V, 8.6 or 10.3 A conflicting)",
            tag="LEAD l.160 (6) / RE-05", spare="1", owner=own,
            note="Burkert 6027 1.5 mm does NOT qualify (Kv 0.07 < 0.11 m3/h, N2O service unstated; the 6027 HP 1.0 mm was rejected in "
                 "LEAD l.160 (6), recorded again in l.186 (4)): not a candidate. NOS 18020BNOS is an N2O part but seat 1.98 mm < 2.0, max "
                 "pressure, mass and Kv not stated, coil 8.6-10.3 A needs peak-and-hold and a +12V_ARM rail upgrade (RE-09). Listings seen "
                 "(not quotes, not delivered DK-6400 prices): Burkert USD 754.26 excl. VAT (tameson.com, US); NOS CAD 316.33 (jbspowercentre.com). "
                 "LEAD 194 (1): the bleed valves are FA-1 listing candidates; at selection the body proof and the closed-seat pressure rating "
                 "are checked against the FA-1 period domain (head side; FA1S about 151 bar abs until Mechanical lists the period). " + O2),
        row("F bleed", "J511 (P_mid)", 1, "TE Connectivity M3234-000005-170BG class pressure transducer (0-170 bar g, 0.5-4.5 V)",
            "P_mid between V1 and V2 (fixed-side tee, mid volume <= 0.5 cm3 ICD) -> LMV331 comparator 9.86 / 8.86 bar g",
            MOUSER, DIGIKEY, "", None, "", TOQ, "TE M3200 series datasheet (range code availability TO-VERIFY at quote)",
            tag="DATASHEET", spare="1", owner="Electronics", note=O2 + "; V2 side sees flashing N2O on every purge"),
        row("F bleed", "J508 backshell", 3, "thin-film resistors 1 % 0.25 W axial: 82.5k (R0 end of line), 9.53k (R1 OPEN), 17.8k (R2 CLOSED)",
            "MV switch ladder resistors in the J508 mating backshell (potted); values calc/hbleed_provision_v1.py", MOUSER, DIGIKEY, "",
            None, "", TOQ, "calc/hbleed_provision_v1.json", tag="DESIGN", spare="3", owner="Electronics"),
        row("F bleed", "J509 J510 J511 harness", 1, "harness: 2 x 2-wire valve leads (18 AWG, fixed side) + 3-wire P_mid lead (shielded) + JST GH / "
            "Micro-Fit housings and contacts", "routing on the fixed side only (no gimbal crossing); lengths TO-VERIFY from the CAD",
            MOUSER, DIGIKEY, "", None, "", TOQ, "", tag="DESIGN", owner="Electronics"),
        row("F bleed", "bleed plumbing", 1, "bleed tee (head end), 2 x precision restrictor 0.707 mm (one per tap, upstream of V1), -2 (1/8 in) "
            "stainless line and fittings, V1-V2 mid block with the P_mid port (mid volume <= 0.5 cm3)",
            "decided path (LEAD 2026-10-13; 1.0 mm equivalent); RE-14", "Swagelok (authorised distributor for Denmark, via swagelok.com)",
            "The Lee Company (precision restrictors) / O'Keefe Controls (orifices)", "restrictor Lohm / orifice part TO-SELECT", None, "", TOQ, "",
            tag="DESIGN (RE-14)", owner="Mechanical (fittings, routing) / Electronics (B-BLEED-1)", spare="2 restrictors", note=O2),
    ]


def harness_rows():
    R = "AS-RECALLED part family, TO-VERIFY at quote"
    return [
        row("F harness", "J401-J404 J501-J507 J616", 13, "Molex Micro-Fit 3.0 receptacle housings (2/3/4-way) + female crimp terminals",
            "mating halves for the Micro-Fit headers", MOUSER, DIGIKEY, "43645-0x00 housings + 43030 crimps (" + R + ")", tag="DESIGN",
            spare="+50 % terminals"),
        row("F harness", "J201 J508 J512 J601-J604 J608-J614 J620 J901 J902", 18, "JST GH housings (GHR-0xV-S) + SSHL crimp contacts",
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
        row("F harness", "J512", 1, "FC -> ECU PURGE_EN discrete lead (2-wire twisted, JST GH 2-way at the ECU; FC end TO-DEFINE)",
            "hardware purge window enable (schematic v2.5, LEAD 166 (3))", MOUSER, DIGIKEY, "", tag="DESIGN", owner="Electronics + GNC (FC end)"),
        row("F harness", "J902", 1, "photodiode head lead (3-wire shielded, JST GH 3-way)", "FA-1 head to ECU ADC2 CH3", MOUSER, DIGIKEY, "",
            tag="DESIGN"),
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
        row("H test stand + bench", "B-DPC-1 sensor", 3, "PCB Piezotronics 113B22 ICP dynamic pressure sensor (5 kpsi = 344.75 bar at +/-5 V; "
            "maximum pressure 15 kpsi = 1034 bar)",
            "stand dynamic Pc channel for IGN-1 and the T series (LEAD 172 (2); >= 100 bar abs with a proof rating, LEAD 194 (7) / R3-10): "
            "1.0 mV/psi +/-10 % (14.5 mV/bar), >= 500 kHz resonance, <= 1 us rise, 0.001 Hz LF (-5 %), DTC >= 500 s, -73..+135 C, flash "
            "1649 C, Invar diaphragm, 10-32 coax; flush (seal rings 065A02) or recess (seal sleeve 065A05), clamp nut 060A03 5/16-24; two in "
            "use (head flush, end of a flight-like 0.3 m sense line next to the 070BG) + one spare", "PCB Piezotronics (pcb.com) via EU office",
            "Kistler (kistler.com) piezo high-frequency class, >= 100 bar range (model TO-SELECT)", "113B22 + mounting adapter TO-SELECT", None,
            "", TOQ, "pcb.com 113B22 product page (read 2026-10-13; spec sheet file 113b22_g.pdf, revision not stated on the page)",
            tag="DATASHEET", owner="Electronics (channel) / Mechanical (port)", spare="1",
            note="replaces the 113B24 (1 kpsi = 69 bar FS, BOM v2.2-v2.9): fails the >= 100 bar abs range (LEAD 194 (7)). IEPE: PCB lists "
                 "20-30 V excitation; NI 9234 compliance 19 V max with the 8-14 V bias leaves >= 5 V of positive swing (DERIVED), "
                 "TO-VERIFY with PCB/NI. Thermal protection (RTV/ablative) for the hybrid chamber TO-VERIFY with PCB. The 1 kHz flight "
                 "LIGHT_SPIKE values are lower bounds; this channel is the evidence"),
        row("H test stand + bench", "B-DPC-1 DAQ", 1, "NI 9234 (4 ch, 24-bit, +/-5 V, 51.2 kS/s/ch, IEPE 2.0 mA / 19 V compliance, AC coupled "
            "-3 dB 0.5 Hz, AA filter 0.45 fs passband / 100 dB at 0.55 fs, simultaneous) + CompactDAQ chassis",
            "digitises the two 113B22 at >= 51.2 kS/s with anti-alias (>= 10-20 kHz signal band); AC coupled, so static levels come from the "
            "070BG chain", "National Instruments (ni.com, DK sales)", "other IEPE DAQ with true anti-alias (TO-SELECT)",
            "NI 9234 + cDAQ chassis TO-SELECT", None, "", TOQ, "NI 9234 datasheet 374238A-02 (Oct 2015); ni.com NI 9234 specifications "
            "377849B-01 (Feb 2025)", tag="DATASHEET", owner="Electronics",
            note="common time base with the ECU log and CAN capture (over_thrust_v3); cable: low-noise coax 10-32, length TO-DEFINE"),
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
        # v2.2 RE-14 bench equipment and test supplies (REVIEW-ELECTRONICS RE-14)
        row("H test stand + bench", "CF-3 / B-BLEED-1", 1, "Coriolis mass-flow meter, liquid N2O service, 0-200 g/s class, response <= 100 ms",
            "cold-flow reference (CF-3) and bleed flow 31 g/s (B-BLEED-1)", "Endress+Hauser (endress.com, DK)", "Emerson Micro Motion / Bronkhorst",
            "model TO-SELECT", tag="DESIGN (RE-14)", owner="Electronics + Mechanical", note=O2),
        row("H test stand + bench", "B-PT-1 / B-PC-1", 1, "reference pressure gauge / calibrator, 0-100 bar, uncertainty <= 0.05 bar (B-PT-1), traceable cert, "
            "with a hydraulic hand test pump to >= 100 bar g",
            "end-to-end transducer check at >= 6 pressures (residual <= 0.3 bar, within 3 months of flight), B-PC-1 zero/drift and the B-PC-1 "
            "over-range row on the spare 070BG (70-100 bar g, below the 140 bar g proof; LEAD 194 (7))",
            "Fluke Calibration / Druck (Baker Hughes) via " + FARNELL, "WIKA (wika.dk)", "model TO-SELECT", tag="DESIGN (RE-14, LEAD 172 guard band)"),
        row("H test stand + bench", "safing purge", 1, "N2 cylinder (industrial, >= 50 L at 200 bar) + regulator + flow indication >= 10 g/s + purge hose",
            "LEAD 172 (1) safing: N2 purge >= 60 s at >= 10 g/s (>= 0.6 kg per purge), then hold >= 15 min", "Air Liquide Danmark / Linde Gas DK",
            "Strandmøllen (DK)", "cylinder rental + regulator TO-SELECT", tag="LEAD 172 (1)", owner="Founders (GSE) / Electronics (procedure)",
            note="flow indication accuracy and setting TO-DEFINE in bench plan v3 (B-SAFE-1)"),
        row("H test stand + bench", "decade box", 1, "resistance decade box 1 ohm - 10 Mohm, 0.1 %", "MV ladder, mode strap and NTC channel checks (RE-15)",
            FARNELL, MOUSER, "model TO-SELECT", tag="DESIGN (RE-14)"),
        row("H test stand + bench", "transducer simulator", 1, "ratiometric 0.5-4.5 V transducer simulator (or precision voltage source + divider) "
            "with +5V_SNS tracking", "B-FC-1 / HIL: Pc, P_feed, P_tank, P_mid injection incl. invalid windows", FARNELL, "",
            "build or buy TO-SELECT", tag="DESIGN (RE-14, RE-28 HIL)"),
        row("H test stand + bench", "catch volume", 1, "back-pressured catch volume for cold flows (ENG-16, l.67), relief and vent to safe area",
            "cold-flow back pressure and N2O capture", "Swagelok (authorised distributor for Denmark)", "pressure-vessel fabricator TO-SELECT",
            "design TO-DEFINE (Mechanical)", tag="DESIGN (RE-14)", owner="Mechanical / Founders (GSE)", note=O2),
    ]


# ------------------------------------------------------------------------------------------------------------------------- I. GSE
def gse_rows():
    return [
        row("I GSE", "wind", 1, "anemometer at 3 m with 10-min statistics (mean W10 and sigma_u), >= 1 Hz logging, mast",
            "launch commit PROVISIONAL (LEAD l.161 (6)): W10 < 6 m/s AND sigma_u(3 m) <= 1.0 m/s over the 10 min before ARM",
            "Gill Instruments (gillinstruments.com, UK; WindSonic class)", "Vaisala (WMT700 class) / Thies Clima", "model TO-SELECT", tag="LEAD l.161 (6)",
            owner="Founders (GSE) / GNC (rule)", note="ultrasonic or cup: the sigma_u statistic needs >= 1 Hz samples; logger and time base TO-DEFINE"),
    ]


def main():
    a_rows, n_lines, n_sym = ecu_pcb_rows()
    rows = a_rows + ecu_mech_rows() + actuator_rows() + sensor_rows() + driven_rows() + bleed_rows() + harness_rows() + power_rows() + stand_rows() + gse_rows()
    for i, r in enumerate(rows, 1):
        r["line"] = i
        r.move_to_end("line", last=False)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "bom_v2p2.csv"), "w", newline="") as f:
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
                                                  "schematic": "ECU v2.5 (KiCad 7.0.11; ERC result in erc/argos_ecu_erc.rpt)"},
                    "parts_db.py": {"sha256_16": sha16(os.path.join(HERE, "parts_db.py")), "access": parts_db.ACCESS},
                    "pintle_mini_servo_v1.json": {"sha256_16": sha16(SERVO_STUDY)}}),
        ("rows", len(rows)), ("rows_catalogue_priced", n_cat), ("rows_to_quote", n_toq), ("rows_no_purchase", n_np),
        ("sections", sections),
        ("known_catalogue_subtotal_by_currency", {k: round(v, 2) for k, v in known.items()}),
        ("known_subtotal_note", "listing prices incl. the vendor's local VAT, before shipping; NOT DK-6400 quotes and NOT a total"),
        ("total", "UNKNOWN: %d rows are TO-QUOTE (no zero and no 'from' prices used); currencies not converted" % n_toq),
        ("blocked", ["ECU PCB fabrication cannot be quoted before layout",
                     "TPS552882 footprint is a placeholder (TI RPM0026A land pattern needed)",
                     "LTC4365 order suffix and UV threshold TO-CONFIRM (analog.com 403 at the proxy)",
                     "bleed valve not selected: no candidate verified on seat/Kv at 55 bar, flashing-N2O class, 12 V and <= 0.15 kg (v2.10)",
                     "bleed peak-and-hold driver not drawn: coil data of the selected valve needed (calc/bleed_driver_v1.py)"]),
        ("tags", "CATALOGUE = vendor listing read and recorded with date and URL; TO-QUOTE = named vendor, price unknown; "
                 "NO PURCHASE = PCB feature or item owned and priced by another discipline"),
    ])
    with open(os.path.join(OUT, "bom_v2p2.json"), "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=1, ensure_ascii=False)
    lines = ["bom_v2 (Electronics %s): %d rows; %d CATALOGUE-priced, %d TO-QUOTE, %d no purchase; ship to %s"
             % (DATE, len(rows), n_cat, n_toq, n_np, SHIP_TO),
             "ECU PCB from argos_ecu_bom_grouped.csv %s: %d lines, %d symbols" % (sha16(GROUPED), n_lines, n_sym)]
    for k, v in sections.items():
        lines.append("  %-34s %3d rows (%d TO-QUOTE, %d catalogue, %d no purchase)" % (k, v["lines"], v["to_quote"], v["catalogue"], v["no_purchase"]))
    lines.append("known catalogue subtotal (listing prices, NOT a total, NOT DK-6400 quotes): " +
                 ", ".join("%.2f %s" % (v, k) for k, v in known.items()))
    lines.append("TOTAL: " + summary["total"])
    with open(os.path.join(OUT, "bom_v2p2.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
