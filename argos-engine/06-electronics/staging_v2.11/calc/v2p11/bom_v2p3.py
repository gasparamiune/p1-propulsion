"""Priced bill of materials v2.3 (Electronics v2.11), ARGOS engine ECU and engine electronics (06-electronics), 2026-10-21.

v2.3 = the v2.2 rows (calc/bom_v2.py, unchanged and re-used as the row builder: lines 1-250 keep their v2.2 numbers, so the
CHANGELOG 216 (6) row references 237 / 238 / 244 / 245 / 250 still point at the same items) with in-place amendments, plus the
v2.11 delta rows appended from line 251. Every amendment is listed in the JSON summary ('amendments': line, field, old, new, basis).

What changes (LEAD CHANGELOG lines 203, 205, 206 (3), 215 / 216, 230, 243 (3); REV-ELEC-2 R2-14, R2-20):
  * Flight Pc (J601), P_feed (J602) and P_mid (J511) move to the C1 transducer Kulite XTL-190SM-2000A (calc/v2p11/pc_transducer_v3.py,
    results/pc_transducer_v3.json) with an INA333 bridge amplifier per channel; the TE 070BG stays for P_torch (J901) and as the
    B-PC-1 static-level reference, plus one spare reserved for the over-range row (hydraulic only, never returned to N2O service);
    the TE 170BG stays for P_tank (J603). Line 219 (P_mid 170BG class) is superseded (NO PURCHASE, kept so the numbering holds).
  * Comparator values re-derived for the C1 transfer (U330 tap 47.5k / 47.5k, threshold 174k / 29.4k; U570 806k, 10.5k / 2.05k).
  * Ride-through BOM variant (LEAD 216 (3), CANDIDATE): C330 = 2 x 270 nF C0G in parallel (540 nF), fitted ONLY in the ride-through
    build; the default build keeps C330 220 nF.
  * Hardware both-commanded-open timer (LEAD 166 (3) / 216 (5)): U576-U579 (74LVC1G08 x 2, LTC6993-2, 74LVC1G74) + RSET / DIVCODE.
  * R2-14: O2-clean / medium notes on rows 212 (SOL1) and 214 (SOL3); row 245: medium separation, the hydraulic pump reserved for
    units that never see N2O (or a recorded re-cleaning). R2-20: row 250 says HARD (LEAD 181 (6)), not PROVISIONAL.
  * Case-TC rows carry the adopted abort A = 423.15 K (LEAD 243 (3)) and the start / ARM limits; the B-TC-1 reference row is added.
  * Fallback IEPE conditioner for the 113B22 (LEAD 203 (7)); TE / PCB / NI inquiries are founder actions (bench plan v4, not rows).

THE KiCad SCHEMATIC IS NOT UPDATED: hardware/kicad is still v2.5. Every v2.11 board part below is a DESIGN row from config.h and the
pc_transducer_v3 / hbleed timer derivations; reference designators of the new parts are TO-ASSIGN in schematic v2.6 (not drawn).

Reads:  ../bom_v2.py (row builder v2.2) and what it reads; ../../results/pc_transducer_v3.json (C1 values, masses)
Writes: ../../results/bom_v2p3.csv / .json / .txt
Rules (unchanged from v2.2): every row names a vendor and ships to Soenderborg, DK-6400; no invented prices (only CATALOGUE listing
prices with a recorded source; everything new here is TO-QUOTE); no 0 and no 'from' prices; currencies not converted.
"""
import csv
import hashlib
import json
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CALC = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, CALC)
import bom_v2 as B  # noqa: E402  (v2.2 generator; importing it runs nothing)

VERSION = "v2.3"
DATE = "2026-10-21"
OUT = os.path.normpath(os.path.join(CALC, "..", "results"))
PCX = os.path.join(OUT, "pc_transducer_v3.json")
TOQ = B.TOQ
O2 = B.O2
row = B.row
ACCESS_DS = "retrieved 2026-10-13 (pc_transducer_v3.json B_candidates_datasheet)"

# delta-row line numbers (the order of delta_rows(); checked in main() against each row's part text)
L_KULITE, L_INA, L_OPA, L_RG, L_REFDIV, L_RFI, L_BIAS, L_R574, L_BREAK, L_C330B, L_U576, L_U577, L_U578, L_DIV, L_IEPE, L_BTC = range(251, 267)
LINE_CHECK = {L_KULITE: "Kulite XTL-190SM-2000A", L_INA: "TI INA333", L_OPA: "TI OPA2333", L_RG: "1.27k 0.1 %", L_REFDIV: "0.1 % thin film",
              L_RFI: "per channel:", L_BIAS: "10M 1 %", L_R574: "806k 1 %", L_BREAK: "4-way + shield in-line", L_C330B: "270 nF 50 V C0G",
              L_U576: "TI SN74LVC1G08DBVR", L_U577: "Analog Devices LTC6993IS6-2", L_U578: "TI SN74LVC1G74DCUR", L_DIV: "63.4k 0.1 %",
              L_IEPE: "4-channel ICP", L_BTC: "thermocouple reference"}


def sha16(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def v22_rows():
    a_rows, n_lines, n_sym = B.ecu_pcb_rows()
    rows = (a_rows + B.ecu_mech_rows() + B.actuator_rows() + B.sensor_rows() + B.driven_rows() + B.bleed_rows() + B.harness_rows()
            + B.power_rows() + B.stand_rows() + B.gse_rows())
    for i, r in enumerate(rows, 1):
        r["line"] = i
        r.move_to_end("line", last=False)
    return rows, n_lines, n_sym


AMEND = []


def at(rows, line, refs, part_prefix):
    r = rows[line - 1]
    if r["line"] != line or r["refs"] != refs or not r["part"].startswith(part_prefix):
        raise ValueError("v2.2 row %d is not the expected item: %r / %r" % (line, r["refs"], r["part"][:50]))
    return r


def amend(r, field, new, basis):
    old = r[field]
    if field == "note" and old and not new.startswith(old):
        raise ValueError("note amendments append to the v2.2 note")
    AMEND.append(OrderedDict([("line", r["line"]), ("field", field), ("old", old), ("new", new), ("basis", basis)]))
    r[field] = new


def find_ref(rows, ref):
    hits = [r for r in rows if r["section"] == "A ECU PCB" and ref in r["refs"].split()]
    if len(hits) != 1:
        raise ValueError("reference %s found %d times in the grouped rows" % (ref, len(hits)))
    return hits[0]


SCH = "schematic v2.6 NOT drawn (KiCad v2.5 still shows %s)"


def amend_rows(rows, pcx):
    c1 = pcx["B_candidates_datasheet"]["C1"]
    # ---- D sensors: 070BG / 170BG keep the channels that do not move to C1 (LEAD 205, 206 (3); pc_transducer_v3 'supersedes')
    r = at(rows, 199, "J601 J901", "TE M3234-000005-070BG")
    amend(r, "refs", "J901 (P_torch); B-PC-1 static-level reference", "LEAD 205: J601 (flight Pc) moves to C1, line %d" % L_KULITE)
    amend(r, "description", "P_torch on the torch body port (J901) and the B-PC-1 static-level reference on the calibration manifold; "
          "0-70 bar g, 0.5-4.5 V ratiometric, 1/4-18 NPT, Packard A", "pc_transducer_v3 'supersedes'; config.h kPcXdcrSel note")
    amend(r, "spare_recommended", "1, RESERVED for the B-PC-1 over-range row (70-100 bar g, hydraulic only, never returned to N2O "
          "service; LEAD 203 (2) / 216 (6))", "LEAD 216 (6)")
    amend(r, "tag", "DESIGN (pc_transducer_v3: kept for P_torch and the stand static reference; LEAD 205)", "LEAD 205")
    r = at(rows, 200, "J602 J603", "TE M3234-000005-170BG")
    amend(r, "refs", "J603 (P_tank)", "LEAD 206 (3): J602 (P_feed) moves to C1, line %d" % L_KULITE)
    amend(r, "qty", 1, "LEAD 206 (3)")
    amend(r, "description", "P_tank, 0-170 bar g (proof 340 bar)", "LEAD 206 (3)")
    amend(r, "note", r["note"] + "; v2.3: P_feed (J602) is on the C1 Kulite (line %d)" % L_KULITE, "LEAD 206 (3)")
    # ---- case TC rows: adopted abort and the v2.11 limits (LEAD 243 (3); Part A rulings 2026-10-20T21:46:49Z / 21:51:07Z)
    r = at(rows, 203, "J605 J606", "type K thermocouple, IEC 60584 Class 1")
    amend(r, "description", "case TCs az 90 / az 270, junction 13.5 +/- 0.5 mm aft of the injector face (case abort 423.15 K with 0.20 s "
          "persistence, LEAD 243 (3); start / ARM limit 403.15 K; stand T0 ARM limit 297.15 K)", "LEAD 243 (3) + Part A rulings")
    amend(r, "note", "channel tolerance: calc/v2p11/case_tc_channel_v1.py (false-trip side 7.78 K worst case inside +12.3 K; low side "
          "9.05 + 0.630 r K); B-TC-1 measures tau <= 0.25 s and |offset| <= 0.6 K (bench plan v4)", "Part A (LEAD ACCEPTED)")
    r = at(rows, 204, "J607", "type K thermocouple")
    amend(r, "description", "nozzle-holder TC (TC3: in-burn abort and, v2.11, the ARM refusal limit; 523.15 K ASSUMED)",
          "Part A ruling (TC3 nozzle-holder limit at ARM ACCEPTED)")
    # ---- FA-1 head: the S17 dead-vehicle result needs the main-chamber view (FLAMEOUT_OPT)
    r = at(rows, 210, "J902", "FA-1 flame-light head")
    amend(r, "note", r["note"] + "; v2.11 S17: the R2 dead-vehicle release margin at late Pc-loss onsets rests on the photodiode "
          "VIEWING THE MAIN CHAMBER (FLAMEOUT_OPT proven with the torch closed); with a torch-only view the 0.5 / 0.8 s windows release "
          "dead vehicles at onsets 43-50 ms (SIM): optics and mounting must give the main-chamber view (TO-DEFINE with Combustion)",
          "S17 v2.11 (sc_v211_r2.inc)")
    # ---- R2-14 O2 notes on the owner-selected N2O valves
    r = at(rows, 212, "J502", "SOL1 torch N2O solenoid valve")
    amend(r, "note", r["note"] + "; R2-14: N2O-wetted - " + O2, "REV-ELEC-2 R2-14")
    r = at(rows, 214, "J507", "SOL3 tank vent solenoid valve")
    amend(r, "note", r["note"] + "; R2-14: N2O-wetted (tank vapour and liquid at the vent) - " + O2, "REV-ELEC-2 R2-14")
    # ---- F bleed: P_mid moves to C1
    r = at(rows, 219, "J511 (P_mid)", "TE Connectivity M3234-000005-170BG class")
    amend(r, "part", "SUPERSEDED in v2.3 by line %d (was: %s)" % (L_KULITE, r["part"]), "LEAD 206 (3)")
    amend(r, "qty", 0, "LEAD 206 (3)")
    amend(r, "price_basis", "NO PURCHASE (superseded in v2.3: P_mid is a C1 Kulite channel, line %d)" % L_KULITE, "LEAD 206 (3)")
    amend(r, "delivered_price_DK6400", "n/a", "superseded row")
    r = at(rows, 221, "J509 J510 J511 harness", "harness: 2 x 2-wire valve leads")
    amend(r, "note", "v2.3: the P_mid lead becomes the C1 integral 4-core shielded cable (0.914 m) to a 4-way + shield break "
          "connector (line %d); the 3-wire P_mid lead is deleted" % L_BREAK, "LEAD 206 (3)")
    # ---- F harness: connectors follow the transducer change
    r = at(rows, 224, "J201 J508 J512 J601-J604 J608-J614 J620 J901 J902", "JST GH housings")
    amend(r, "note", "v2.3: J601, J602 and J511 become 4-way + shield bridge inputs (schematic v2.6 NOT drawn): housing sizes and "
          "counts TO-UPDATE at layout", "LEAD 205 / 206 (3)")
    r = at(rows, 225, "transducers", "Packard A / Metri-Pack 150 3-way mating connector kit")
    amend(r, "qty", 3, "v2.3: Packard A only on the 070BG (J901, B-PC-1 reference) and the 170BG (J603)")
    amend(r, "description", "M3200 connector code 4 mates (J901 070BG, B-PC-1 reference 070BG, J603 170BG)", "v2.3")
    # ---- H bench: the B-DPC-1 and DAQ rows, the reference gauge (R2-14), the RFQ rows of 216 (6)
    r = at(rows, 237, "B-DPC-1 sensor", "PCB Piezotronics 113B22")
    amend(r, "note", r["note"] + "; v2.3: the flight sense line is deleted (LEAD 205): the second in-use unit moves from the line end "
          "to the stand reference port next to the B-PC-1 070BG (position TO-DEFINE with Mechanical); RFQ founder action (LEAD 216 (6))",
          "LEAD 205 / 216 (6)")
    r = at(rows, 238, "B-DPC-1 DAQ", "NI 9234")
    amend(r, "note", r["note"] + ("; v2.3: fallback IEPE conditioner if PCB / NI do not confirm the 113B22 at 19 V compliance: line %d "
          "(LEAD 203 (7)); RFQ founder action (LEAD 216 (6))" % L_IEPE), "LEAD 203 (7) / 216 (6)")
    r = at(rows, 244, "CF-3 / B-BLEED-1", "Coriolis mass-flow meter")
    amend(r, "note", r["note"] + "; RFQ founder action (LEAD 216 (6)); B-BLEED-1 measures mdot for the measured-time cap form "
          "(LEAD 216 (5))", "LEAD 216 (5) / (6)")
    r = at(rows, 245, "B-PT-1 / B-PC-1", "reference pressure gauge / calibrator")
    amend(r, "note", "R2-14 MEDIUM SEPARATION: the hydraulic hand pump and its fluid are used ONLY on units that never see N2O (the "
          "reserved over-range 070BG of line 199 and bench-only units); an N2O-wetted transducer (C1 units, flight 070BG / 170BG) is "
          "checked with clean dry N2 (gas calibrator or N2 cylinder + regulator) or, after any hydraulic contact, re-cleaned to the "
          "O2-clean class with a recorded re-cleaning before N2O service; RFQ founder action (LEAD 216 (6)); range covers the C1 "
          "B-PC-1 points (absolute: add the barometric reading)", "REV-ELEC-2 R2-14; LEAD 216 (6)")
    r = at(rows, 250, "wind", "anemometer at 3 m")
    amend(r, "description", "launch commit HARD for A1 (LEAD 181 (6); was PROVISIONAL in l.161 (6)): W10 < 6 m/s AND sigma_u(3 m) <= "
          "1.0 m/s over the 10 min before ARM; v2.11 S17: the R2 v2 0.8 s window is confirmed only inside W10 < 6 m/s", "REV-ELEC-2 R2-20")
    amend(r, "tag", "LEAD 181 (6) HARD (l.161 (6) superseded)", "REV-ELEC-2 R2-20")
    amend(r, "note", r["note"] + "; mast + logger with a UTC time base are founder actions (LEAD 216 (6)); RFQ (LEAD 216 (6))",
          "LEAD 216 (6)")
    # ---- A ECU PCB: comparator value changes for the C1 transfer (pc_transducer_v3 F / G)
    F = pcx["F_hw_comparator_U330"]["values"]["v"]
    G = pcx["G_pmid_comparator_U570"]["values"]["v"]
    chg = [("R330", "100k 0.1%", "47.5k 0.1%", F["R330"], "U330 tap 1/2 (pc_transducer_v3 F)"),
           ("R331", "31.6k 0.1%", "47.5k 0.1%", F["R331"], "U330 tap 1/2, Rth 23.75k"),
           ("R332", "237k 0.1%", "174k 0.1%", F["R332"], "U330 threshold: trip 32.59 bar abs nominal (31.08-34.11)"),
           ("R576", "10.2k", "10.5k", G["R576"], "U570 reference: rise 11.08 / fall 10.07 bar abs"),
           ("R577", "1.74k", "2.05k", G["R577"], "U570 reference")]
    for ref, old_v, new_v, val, why in chg:
        rr = find_ref(rows, ref)
        if rr["refs"] != ref or not rr["part"].startswith(old_v):
            raise ValueError("unexpected grouped row for %s: %r" % (ref, rr["part"]))
        amend(rr, "part", new_v + ", " + rr["part"].split(", ", 1)[1], "pc_transducer_v3 (%s = %.0f ohm)" % (ref, val))
        amend(rr, "description", rr["description"] + " | v2.11: " + why + "; " + SCH % old_v, "pc_transducer_v3")
    # the v2.2 basis text of these rows describes the 070BG values: replace it with the v2.11 derivation (same source, F / G)
    rth = F["R330"] * F["R331"] / (F["R330"] + F["R331"])
    k_thr = F["R333"] / (F["R332"] + F["R333"])
    vref_pm = 5.0 * G["R577"] / (G["R576"] + G["R577"])
    Ff = pcx["F_hw_comparator_U330"]
    lo, hi = Ff["trip_range_abs_Pa"]["v"]
    new_tags = {
        "R330": "DESIGN (DERIVED v2.11: tap %.1f/%.1f = %.3f on the C1 INA333 output, Rth %.2f kOhm; pc_transducer_v3 F)"
                % (F["R331"] / 1e3, (F["R330"] + F["R331"]) / 1e3, Ff["tap_ratio"]["v"], rth / 1e3),
        "R331": "DESIGN (pc_transducer_v3 F: tap 1/2 with R330)",
        "R332": "DESIGN (DERIVED v2.11 ratiometric threshold %.1f/%.1f x 5 V = %.4f V = PC_SIG %.4f V = %.2f bar abs on C1; circuit band "
                "%.2f-%.2f bar abs (LMV331 Vio / Iib, 0.1 %% ratios); pc_transducer_v3 F)"
                % (F["R333"] / 1e3, (F["R332"] + F["R333"]) / 1e3, 5.0 * k_thr, Ff["pc_sig_trip_V"]["v"],
                   Ff["trip_nominal_Pa_abs"]["v"] / 1e5, lo / 1e5, hi / 1e5),
        "R333": "DESIGN (value kept; Rth %.2f kOhm ~ tap Rth %.2f kOhm, bias currents roughly cancel; pc_transducer_v3 F)"
                % (F["R332"] * F["R333"] / (F["R332"] + F["R333"]) / 1e3, rth / 1e3),
        "R576": "DESIGN (DERIVED v2.11 ratiometric reference %.4f V: rise %.2f / fall %.2f bar abs on C1; pc_transducer_v3 G)"
                % (vref_pm, pcx["G_pmid_comparator_U570"]["trip_rise_Pa_abs"]["v"] / 1e5,
                   pcx["G_pmid_comparator_U570"]["release_Pa_abs"]["v"] / 1e5),
        "R577": "DESIGN (pc_transducer_v3 G: reference divider with R576)",
    }
    for ref, t in new_tags.items():
        amend(find_ref(rows, ref), "tag", t, "pc_transducer_v3 (v2.2 basis text described the 070BG values)")
    rr = find_ref(rows, "R574")
    if rr["refs"] != "R203 R574 R652 R653":
        raise ValueError("R574 group changed")
    amend(rr, "refs", "R203 R652 R653", "R574 moves to line %d (806k)" % L_R574)
    amend(rr, "qty", 3, "R574 moves to line %d" % L_R574)
    rc = find_ref(rows, "C330")
    if rc["refs"] != "C330" or not rc["part"].startswith("220nF/50V C0G"):
        raise ValueError("C330 row changed")
    amend(rc, "description", rc["description"] + " | v2.11 DEFAULT build (no ride-through): 220 nF kept, tau = 23.75k x 220 nF = "
          "5.225 ms on the C1 tap; the ride-through variant adds C330B (line %d) and fits 270 nF here: 540 nF" % L_C330B, "pc_transducer_v3 F; LEAD 216 (3)")
    amend(rc, "tag", "DESIGN (DERIVED v2.11: tau = 23.75k x 220 nF = 5.225 ms, default build; ride-through build 540 nF -> 12.825 ms "
          "nominal, 12.10-13.55 ms with the C0G and resistor tolerances (config.h kRideCmpTau*); the v2.10 basis (x0.17 at the ~180 Hz "
          "sense-line resonance) lapsed with the line deletion, LEAD 205)", "pc_transducer_v3 F; LEAD 205, 216 (3)")


def delta_rows(pcx):
    c1 = pcx["B_candidates_datasheet"]["C1"]
    c2 = pcx["B_candidates_datasheet"]["C2"]
    m = pcx["H_mass"]["v"]
    e = pcx["E_conditioning"]
    S = "J v2.11 delta"
    ds = "Kulite XTL-190 (M) datasheet, distributor copy " + c1["source"].split("(distributor copy ")[1].split(";")[0]
    rows = [
        row(S + " / D sensors", "J601 (Pc) J602 (P_feed) J511 (P_mid)", 3,
            "Kulite XTL-190SM-2000A (ordering code TO-VERIFY with Kulite)",
            "C1 PREFERRED, one family for Pc / P_feed / P_mid (LEAD 205, 206 (3)): leadless silicon bridge, 0-2000 psia = 137.9 bar abs, "
            "proof 1.5 x rated = 206.8 bar, burst 3 x rated = 344.7 bar, operating -55..+175 C, compensated 25-80 C as standard (order "
            "20-120 C: 'any 100 F range on request'), 10 V rated / 12 V max excitation (run at +5V_SNS), 100 mV FSO at 10 V, "
            "NL+H+R 0.1 % typ / 0.5 % max FSO, vibration 100 g 10-2000 Hz, M5 x 0.8 (190SM, short body), hex 3/8 in, 4.0 g excl. "
            "cable, 4-core 30 AWG shielded integral cable 914 mm, torque <= 1.7 N m",
            "Kulite Semiconductor Products (kulite.com; EU sales office TO-CONFIRM)",
            "C2 ALTERNATE (Pc only): Kistler 4007D100FDS1 (kistler.com, Kistler Nordic) - needs Kistler amplifier compensation",
            "XTL-190SM-2000A + compensated range 20-120 C + O2-clean processing + FKM (or metal) seal instead of the silicone O-ring",
            None, "", TOQ, ds + "; " + ACCESS_DS + "; revision letter TO-VERIFY against kulite.com before order",
            "DATASHEET", spare="1", owner="Electronics (channel) / Mechanical (CC-2 seat, BL-08, FD-01 ports)",
            note="mass %.1f g per channel (body %.1f g DATASHEET + cable %.1f g ASSUMED 10 g/m); P_feed + P_mid %.1f g vs %.0f g carried -> "
                 "%+.3f kg (pc_transducer_v3 H); the Pc unit adds %.1f g on the gimballed head (the 070BG + sense line it replaces is "
                 "not in the mechanical.json v2.2 ledger: MISSING). Media: wetted 15-5 SS / SiO2 + the supplied silicone O-ring (DATASHEET "
                 "'consult factory'): replace the seal; no flight heritage claimed. " % (m["per_channel_g"], m["body_g"], m["cable_g"],
                 m["P_feed_plus_P_mid_g"], m["carried_g"], m["delta_kg"], m["per_channel_g"]) + O2),
        row(S + " / A ECU PCB", "bridge amplifiers (refs TO-ASSIGN, schematic v2.6)", 3, "TI INA333AIDGKR",
            "Pc / P_feed / P_mid bridge amplifier on +5V_SNS, G %.1f (RG E96), output = the existing PC_SIG / PFEED_SIG / P_MID_SIG net"
            % e["gain"]["v"]["G_E96"], B.MOUSER, B.DIGIKEY, "INA333AIDGKR (MSOP-8; order code TO-CONFIRM)", tag="DATASHEET (TI SBOS445C) / "
            "DESIGN (pc_transducer_v3 E)", spare="2", note=SCH % "the 070BG 3-wire inputs"),
        row(S + " / A ECU PCB", "REF buffers (refs TO-ASSIGN)", 2, "TI OPA2333AIDGKR",
            "buffered select-on-test REF divider of +5V_SNS for the three INA333 (one dual per two channels)", B.MOUSER, B.DIGIKEY,
            "OPA2333AIDGKR (MSOP-8; order code TO-CONFIRM)", tag="DESIGN (pc_transducer_v3 E)", spare="1", note=SCH % "no REF buffer"),
        row(S + " / A ECU PCB", "RG (refs TO-ASSIGN)", 3, "1.27k 0.1 % 25 ppm/K thin film, 0603 + select-on-test kit E96 946-1911 ohm",
            "INA333 gain resistor, chosen from each unit's calibration sheet (FSO spread 0.75-1.5 x nominal ASSUMED)", B.MOUSER, B.DIGIKEY,
            "value + tolerance as stated; MPN TO-SELECT at quote", tag="DESIGN (pc_transducer_v3 E gain)", spare="kit of E96 values",
            note=SCH % "no RG"),
        row(S + " / A ECU PCB", "REF trim dividers (refs TO-ASSIGN)", 6, "0.1 % thin film 0603, select-on-test (REF 0.141-0.859 V)",
            "zero trim so that 0 bar abs reads 0.10 Vexc (B-PC-1), the comparators see the trimmed zero", B.MOUSER, B.DIGIKEY,
            "values at B-PC-1; MPN TO-SELECT", tag="DESIGN (pc_transducer_v3 E zero_trim)", spare="kit", note=SCH % "no REF divider"),
        row(S + " / A ECU PCB", "RFI filters (refs TO-ASSIGN)", 15, "per channel: 2 x 1.00k 0.1 %, 1 x 10 nF C0G (differential), "
            "2 x 1 nF C0G (common mode), 0603", "bridge-input RFI filter, three channels (6 R + 3 C + 6 C)", B.MOUSER, B.DIGIKEY,
            "MPN TO-SELECT", tag="DESIGN (pc_transducer_v3 E topology)", spare="cut-tape minimum", note=SCH % "no filter"),
        row(S + " / A ECU PCB", "open-wire bias (refs TO-ASSIGN)", 6, "10M 1 % 0603", "SIG+ to GND and SIG- to +5V_SNS per channel "
            "(open SIG reads LOW -> PC_SENSOR)", B.MOUSER, B.DIGIKEY, "MPN TO-SELECT", tag="DESIGN (pc_transducer_v3 E open_wire)",
            spare="cut-tape minimum", note=SCH % "no bias"),
        row(S + " / A ECU PCB", "R574", 1, "806k 1 %, 0603", "U570 hysteresis feedback (P_mid comparator, C1 transfer)", B.MOUSER,
            B.DIGIKEY, "MPN TO-SELECT", tag="DESIGN (pc_transducer_v3 G)", spare="cut-tape minimum", note=SCH % "1M in the R203 group"),
        row(S + " / F harness", "J601 J602 J511 breaks", 3, "4-way + shield in-line connector pair at the harness break of each C1 "
            "integral cable (Kulite option CMR-S1-E-04P at the sensor end, DATASHEET 'optional connector'; or a sealed 4-way + drain)",
            "C1 cable to the ECU harness; red +exc, black -exc, green +out, white -out (XTEL sheet wiring, XTL TO-VERIFY)",
            "Kulite (with the transducer)", B.MOUSER + " (sealed circular 5-way class)", "TO-SELECT", tag="DATASHEET (option) / DESIGN",
            spare="1", note="cable may be shortened to the harness break (TO-VERIFY with Kulite); routing: Pc crosses the gimbal (service "
            "loop rule of line 227)"),
        row(S + " / A ECU PCB", "C330B (ride-through variant only)", 1, "270 nF 50 V C0G 5 %, 1206 or 1210 (part TO-SELECT; second "
            "footprint in parallel with C330)", "RIDE-THROUGH BOM VARIANT (LEAD 216 (3), CANDIDATE): C330 = C330B = 270 nF -> 540 nF, "
            "tau = 23.75k x 540 nF = 12.825 ms nominal (12.100 min, 13.552 max, config.h kRideCmpTau*), FIXED over the whole burn; "
            "DO NOT FIT in the default build", B.MOUSER, B.DIGIKEY, "C0G 270 nF 50 V; MPN TO-SELECT (AS-RECALLED: available in 1206/1210)",
            tag="DESIGN (config.h kRideCmpTauNom_s)", spare="2", note=SCH % "C330 only (220 nF); the variant also changes C330 to 270 nF"),
        row(S + " / A ECU PCB", "U576 U579", 2, "TI SN74LVC1G08DBVR", "both-open timer: U576 BOTH = V1 drive AND V2 drive (after the "
            "PURGE_WIN gating); U579 V1 gate = U574 output AND U578 /Q", B.MOUSER, B.DIGIKEY, "SN74LVC1G08DBVR", tag="DESIGN (config.h "
            "kHbleedHwBoth*, LEAD 166 (3) / 216 (5))", spare="1", note=SCH % "no timer"),
        row(S + " / A ECU PCB", "U577", 1, "Analog Devices LTC6993IS6-2", "both-open timer one-shot: rising edge, RETRIGGERABLE, POL 1 "
            "(output low for tOUT, the rising edge at the end clocks U578); tOUT = 2^21 x 63.4k / 50k x 1 us = 2.659 s (+/- 3.1 %)",
            B.MOUSER, B.DIGIKEY, "LTC6993IS6-2#TRMPBF (suffix TO-CONFIRM)", tag="DATASHEET (LTC6993 Rev F, as U572) / DESIGN", spare="1",
            note=SCH % "no timer"),
        row(S + " / A ECU PCB", "U578", 1, "TI SN74LVC1G74DCUR", "both-open timer latch: CLK = U577 OUT, D = BOTH, CLR_N = BOTH",
            B.MOUSER, B.DIGIKEY, "SN74LVC1G74DCUR (VSSOP-8)", tag="DESIGN", spare="1", note=SCH % "no timer"),
        row(S + " / A ECU PCB", "U577 RSET + DIVCODE", 3, "63.4k 0.1 % 25 ppm/K (RSET); 887k 1 % (R1, V+ to DIV) and 1.00M 1 % (R2, DIV "
            "to GND): DIVCODE 8 = POL 1, NDIV 2^21 (VDIV/V+ 0.53125 +/- 0.015)", "U577 timing", B.MOUSER, B.DIGIKEY, "MPN TO-SELECT",
            tag="DESIGN; DIVCODE table AS-RECALLED from LTC6993 Rev F Table 1 (DIVCODE 7 = POL 0 / 8 = POL 1 at NDIV 2^21): TO-VERIFY "
            "before layout", spare="cut-tape minimum", note=SCH % "no timer"),
        row(S + " / H bench", "B-DPC-1 fallback IEPE", 1, "4-channel ICP / IEPE signal conditioner with >= 24 V compliance (PCB "
            "Piezotronics 482C series class, e.g. 482C05: AS-RECALLED model, TO-VERIFY with PCB)",
            "fallback for the 113B22 excitation if PCB / NI do not confirm operation at the NI 9234 19 V compliance (LEAD 203 (7)): the "
            "conditioner excites the sensors, the NI 9234 then runs with IEPE OFF, AC coupled", "PCB Piezotronics (pcb.com) via EU office",
            "Kistler 5134 class IEPE coupler (AS-RECALLED, TO-VERIFY)", "model TO-SELECT", tag="AS-RECALLED part family (LEAD 203 (7))",
            owner="Electronics", note="bought only if the PCB / NI inquiry answers 'not at 19 V' (bench plan v4 founder block)"),
        row(S + " / H bench", "B-TC-1 reference", 1, "thermocouple reference: dry-block or liquid-bath calibrator to >= 200 C with a "
            "reference probe (<= 0.3 K) + a type K reference junction readout; heater block for the step test",
            "B-TC-1 (bench plan v4): case-TC channel offset (|offset| <= 0.6 K) and time constant (tau <= 0.25 s) in situ, with servos, "
            "pintle rail and spark running (EMI term)", "Fluke Calibration via " + B.FARNELL, "WIKA (wika.dk) / Omega (omega.co.uk)",
            "model TO-SELECT (only if not already owned)", tag="DESIGN (case_tc_channel_v1; Part A ruling: B-TC-1 row)", owner="Electronics"),
    ]
    return rows


def main():
    pcx = json.load(open(PCX))
    rows, n_lines, n_sym = v22_rows()
    if len(rows) != 250:
        raise ValueError("v2.2 row count changed: %d" % len(rows))
    amend_rows(rows, pcx)
    new = delta_rows(pcx)
    for i, r in enumerate(new, len(rows) + 1):
        r["line"] = i
        r.move_to_end("line", last=False)
    rows += new
    by = {r["line"]: r for r in rows}
    for ln, pre in LINE_CHECK.items():
        if not by[ln]["part"].startswith(pre):
            raise ValueError("delta line %d is %r, expected %r" % (ln, by[ln]["part"][:40], pre))
    if len(rows) != max(LINE_CHECK):
        raise ValueError("delta rows and LINE_CHECK disagree")
    with open(os.path.join(OUT, "bom_v2p3.csv"), "w", newline="") as f:
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
    v22 = os.path.join(OUT, "bom_v2p2.csv")
    summary = OrderedDict([
        ("id", "bom"), ("version", VERSION), ("date", DATE), ("owner", "electronics (06-electronics)"), ("ship_to", B.SHIP_TO),
        ("basis", "v2.2 rows 1-250 (calc/bom_v2.py, numbering kept) + amendments + v2.11 delta rows 251-%d" % len(rows)),
        ("inputs", {"bom_v2.py": {"sha256_16": sha16(os.path.join(CALC, "bom_v2.py")), "version": B.VERSION},
                    "argos_ecu_bom_grouped.csv": {"sha256_16": sha16(B.GROUPED), "lines": n_lines, "symbols": n_sym,
                                                  "schematic": "ECU v2.5 (KiCad 7.0.11) - NOT updated for v2.11 (v2.6 not drawn)"},
                    "pc_transducer_v3.json": {"sha256_16": sha16(PCX)},
                    "bom_v2p2.csv (v2.2 record)": {"sha256_16": sha16(v22) if os.path.exists(v22) else "MISSING"}}),
        ("rows", len(rows)), ("rows_catalogue_priced", n_cat), ("rows_to_quote", n_toq), ("rows_no_purchase", n_np),
        ("sections", sections), ("amendments", AMEND), ("n_amendments", len(AMEND)),
        ("known_catalogue_subtotal_by_currency", {k: round(v, 2) for k, v in known.items()}),
        ("known_subtotal_note", "listing prices incl. the vendor's local VAT, before shipping; NOT DK-6400 quotes and NOT a total"),
        ("total", "UNKNOWN: %d rows are TO-QUOTE (no zero and no 'from' prices used); currencies not converted" % n_toq),
        ("rfq_rows_LEAD_216_6", [237, 238, 244, 245, 250]),
        ("blocked", ["ECU PCB fabrication cannot be quoted before layout",
                     "schematic v2.6 NOT drawn: the v2.11 board parts (C1 bridge amplifiers, comparator values, C330B variant, U576-U579 "
                     "timer) exist as DESIGN rows from config.h / pc_transducer_v3 only; KiCad v2.5 still shows the 070BG chain",
                     "TPS552882 footprint is a placeholder (TI RPM0026A land pattern needed)",
                     "LTC4365 order suffix and UV threshold TO-CONFIRM (analog.com 403 at the proxy)",
                     "LTC6993 DIVCODE 8 (POL 1) for U577 is AS-RECALLED from Table 1: TO-VERIFY before layout",
                     "bleed valve not selected (v2.10 screening; LEAD 206 (4) search continues)",
                     "Kulite ordering code, compensated band and seal option TO-VERIFY with Kulite (RFQ)"]),
        ("tags", "CATALOGUE = vendor listing read and recorded with date and URL; TO-QUOTE = named vendor, price unknown; "
                 "NO PURCHASE = PCB feature, item owned and priced by another discipline, or a superseded v2.2 row kept for numbering"),
    ])
    with open(os.path.join(OUT, "bom_v2p3.json"), "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=1, ensure_ascii=False)
    lines = ["bom_v2p3 (Electronics %s, %s): %d rows (v2.2 1-250 kept + %d delta); %d CATALOGUE-priced, %d TO-QUOTE, %d no purchase; "
             "%d amendments; ship to %s" % (VERSION, DATE, len(rows), len(new), n_cat, n_toq, n_np, len(AMEND), B.SHIP_TO),
             "ECU PCB from argos_ecu_bom_grouped.csv %s (schematic v2.5, NOT updated for v2.11): %d lines, %d symbols"
             % (sha16(B.GROUPED), n_lines, n_sym)]
    for k, v in sections.items():
        lines.append("  %-34s %3d rows (%d TO-QUOTE, %d catalogue, %d no purchase)" % (k, v["lines"], v["to_quote"], v["catalogue"],
                                                                                       v["no_purchase"]))
    lines.append("known catalogue subtotal (listing prices, NOT a total, NOT DK-6400 quotes): " +
                 ", ".join("%.2f %s" % (v, k) for k, v in known.items()))
    lines.append("TOTAL: " + summary["total"])
    with open(os.path.join(OUT, "bom_v2p3.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
