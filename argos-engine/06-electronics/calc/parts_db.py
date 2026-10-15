"""Electronics parts database, ARGOS engine ECU (06-electronics), v1 2026-10-11.

Every value carries a tag per TEAM-CHARTER rule 2:
  DATASHEET   vendor/manufacturer document or vendor listing; URL + access date in 'src'
  ASSUMED     placeholder with stated range; to be replaced by measurement or datasheet
  DERIVED     computed in a script (path given)
Conflicts between sources are kept side by side ('conflict' key), never averaged.
Prices: as listed by the named vendor on the access date, currency as listed. Unknown -> 'TO-QUOTE <vendor>'.
SI units in derived quantities; vendor units are preserved where quoted (kg-cm, s/60deg, psi).
"""
ACCESS = "2026-10-11"

SOURCES = {
    "SAVOX_2292_LINDINGER": "https://lindinger.at/en/RC-ELECTRONICS/Servos-Accessories/Servos-Digital-Brushless-Low-High-Voltage/SAVOEX-SB-2292SG-7-4V-31KG-0-07s-BRUSHLESS-DIGITAL-HV-SERVO-BLACK-LINE/9738546",
    "SAVOX_2292_RCMODELSHOP": "https://rc-modelshop.com/product/savox-sb-2292sg-hv-bl-digital-servo-0-055s-45kg-8-4v/",
    "SAVOX_2292_GATOR": "https://gator-rc.com/savox-sb2292sg-monster-performance-brushless-servo-black-edition-055sec-624-9oz-at-8-4v",
    "SAVOX_2292_RCTEAM": "https://www.rcteam.com/en/products/savox-sb-2292sg-black-edition-servo-31kg-0-07s-7-4v-metal",
    "SAVOX_2290_RCMODELSHOP": "https://rc-modelshop.com/product/savox-sb-2290sg-hv-bl-digital-servo-0-11s-70kg-8-4v/",
    "SAVOX_2290_AUTOPARTNER": "https://autopartner.jetshop.se/elektronik/servon/savox/savox-sb-2290sg-servo-65kg-0-11s-8-4v-alu-brushless-staldrev",
    "SAVOX_2290_SERVODB": "https://servodatabase.com/servo/savox/sb2290sg",
    "SAVOX_2274_LINDINGER": "https://www.lindinger.at/en/RC-ELECTRONICS/Servos-Accessories/Servos-Digital-Brushless-Low-High-Voltage/SAVOEX-SB-2274SG-7-4V-25KG-0-08s-BRUSHLESS-DIGITAL-HV-SERVO/9704026",
    "FEETECH_STS3250_OPENELAB": "https://openelab.io/products/feetech-sts3250-c002-servo-12v",
    "TE_M3200_DS": "https://www.farnell.com/datasheets/3007269.pdf  (TE Connectivity 'M3200 Pressure Transducer', header 'M3200 08/2018')",
    "TE_M327L_RS": "https://uk.rs-online.com/web/p/pressure-sensors/2074698",
    "HONEYWELL_PX3_DS": "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2404021430_Honeywell-PX3AN1BH150PSAAX_C3239418.pdf (Honeywell 32313757-H-EN, Issue H 10/22)",
    "PJRC_T41": "https://www.pjrc.com/store/teensy41.html",
    "ELECTROKIT_T41": "https://www.electrokit.com/produkt/teensy-4-1/",
    "WHITMORE_2014": "Whitmore S.A., Merkley D., Inkley N., 'Power Efficient, Restart-Capable Acrylonitrile-Butadiene-Styrene Arc Ignitor for Hybrid Rockets', 28th AIAA/USU Small Satellite Conf., SSC14-X-7, 2014. https://digitalcommons.usu.edu/cgi/viewcontent.cgi?article=3072&context=smallsat",
}

def dsv(v, src, note=""):
    return {"v": v, "tag": "DATASHEET", "src": src, "accessed": ACCESS, "note": note}

def asv(v, rng=None, note=""):
    d = {"v": v, "tag": "ASSUMED", "note": note}
    if rng is not None:
        d["range"] = rng
    return d

KGCM_TO_NM = 0.0980665   # 1 kg-cm = 0.0980665 N m (definition of kgf)

# ---------------------------------------------------------------------------------------------
# Actuators
# ---------------------------------------------------------------------------------------------
SB2292SG = {
    "model": "Savox SB-2292SG (HV brushless digital servo, steel gears, aluminium case)",
    "vendor_pn": "SB-2292SG (Lindinger item 9738546)",
    "suppliers": [
        {"vendor": "Lindinger (AT)", "price": 119.99, "cur": "EUR", "note": "incl. VAT plus shipping; in stock", "src": SOURCES["SAVOX_2292_LINDINGER"]},
        {"vendor": "rc-modelshop (EE)", "price": 135.00, "cur": "EUR", "note": "VAT status not stated; ~10 days to other EU", "src": SOURCES["SAVOX_2292_RCMODELSHOP"]},
        {"vendor": "RC Team (FR)", "price": 129.90, "cur": "EUR", "note": "listing", "src": SOURCES["SAVOX_2292_RCTEAM"]},
    ],
    "voltage_V": dsv([6.0, 8.4], SOURCES["SAVOX_2292_RCMODELSHOP"]),
    "speed_s_per_60deg": dsv({"6.0": 0.085, "7.4": 0.07, "8.4": 0.055}, SOURCES["SAVOX_2292_GATOR"], "consistent across 4 listings"),
    "torque_kgcm": dsv({"6.0": 22.0, "7.4": 31.0, "8.4": 45.0}, SOURCES["SAVOX_2292_GATOR"],
                       "CONFLICT: Lindinger technical-data table lists 27/36/50 kg-cm; design uses the LOWER set"),
    "torque_kgcm_conflict": dsv({"6.0": 27.0, "7.4": 36.0, "8.4": 50.0}, SOURCES["SAVOX_2292_LINDINGER"], "not used"),
    "stall_current_A": dsv({"6.0": 7.5, "7.4": 9.2}, SOURCES["SAVOX_2292_GATOR"],
                           "8.4 V value not published; identical numbers appear in SB-2290SG listings -> treat as family value, MEASURE"),
    "running_current_A": dsv({"6.0": 0.18, "7.4": 0.22}, SOURCES["SAVOX_2292_GATOR"], "no-load running"),
    "idle_current_A": dsv(0.005, SOURCES["SAVOX_2292_GATOR"]),
    "mass_kg": dsv(0.081, SOURCES["SAVOX_2292_RCMODELSHOP"], "CONFLICT: Lindinger table 0.079 kg"),
    "dims_mm": dsv([40.3, 20.2, 38.7], SOURCES["SAVOX_2292_RCMODELSHOP"], "L x W x H body; CONFLICT: Lindinger table H = 40.3 mm; reserve 40.3"),
    "spline": dsv("25T, 6.0 mm (Futaba-type)", SOURCES["SAVOX_2292_LINDINGER"]),
    "pulse_us": dsv({"range": [800, 2200], "neutral": 1500, "operating": [1000, 2000], "operating_travel_deg": 100,
                     "max": [900, 2100], "max_travel_deg": 130}, SOURCES["SAVOX_2292_GATOR"]),
    "refresh_Hz": dsv(333, SOURCES["SAVOX_2292_GATOR"]),
    "resolution": dsv("12-bit (4096)", SOURCES["SAVOX_2292_RCTEAM"]),
    "deadband_us": asv(1.0, [0.5, 3.0], "not published by Savox; typical digital-servo value; MEASURE on bench"),
    "backlash_deg_output": asv(0.2, [0.05, 0.5], "steel spur train, not published; MEASURE"),
    "op_temp_C": dsv([-10, 50], SOURCES["SAVOX_2292_GATOR"], "pintle unit on the engine head needs thermal standoff"),
    "wire": dsv("300 +/- 5 mm lead, JR/universal plug", SOURCES["SAVOX_2292_GATOR"]),
    "mount_pattern": asv("standard-size servo flange, 4 holes ~Ø4.5 on ~49.5 x 10 mm (typical class value)", None,
                         "NOT from a Savox drawing: Mechanical must verify on the received unit before machining"),
}

SB2290SG = {
    "model": "Savox SB-2290SG (comparator, high torque)",
    "speed_s_per_60deg": dsv({"6.0": 0.16, "7.4": 0.13, "8.4": 0.11}, SOURCES["SAVOX_2290_RCMODELSHOP"]),
    "torque_kgcm": dsv({"6.0": 45.0, "7.4": 55.0, "8.4": 70.0}, SOURCES["SAVOX_2290_RCMODELSHOP"],
                       "CONFLICT: autopartner.jetshop.se lists 40/50/65 kg-cm"),
    "torque_kgcm_conflict": dsv({"6.0": 40.0, "7.4": 50.0, "8.4": 65.0}, SOURCES["SAVOX_2290_AUTOPARTNER"]),
    "stall_current_A": dsv({"6.0": 7.5, "7.4": 9.2}, SOURCES["SAVOX_2290_AUTOPARTNER"], "servodatabase lists 7.2-10.5 A"),
    "mass_kg": dsv(0.081, SOURCES["SAVOX_2290_RCMODELSHOP"]),
    "price": {"vendor": "rc-modelshop (EE)", "price": 139.00, "cur": "EUR", "src": SOURCES["SAVOX_2290_RCMODELSHOP"]},
}

SB2274SG = {
    "model": "Savox SB-2274SG (comparator, fast/low torque)",
    "speed_s_per_60deg": dsv({"6.0": 0.105, "7.4": 0.08}, SOURCES["SAVOX_2274_LINDINGER"]),
    "torque_kgcm": dsv({"6.0": 20.0, "7.4": 25.0}, SOURCES["SAVOX_2274_LINDINGER"]),
    "voltage_V": dsv([6.0, 7.4], SOURCES["SAVOX_2274_LINDINGER"], "NOT rated for 8.4 V: cannot run from a full 2S pack directly"),
    "mass_kg": dsv(0.069, SOURCES["SAVOX_2274_LINDINGER"]),
    "price": {"vendor": "Lindinger (AT)", "price": 92.99, "cur": "EUR", "note": "listed 'no longer available'", "src": SOURCES["SAVOX_2274_LINDINGER"]},
}

STS3250 = {
    "model": "Feetech STS3250-C002 (comparator: serial-bus smart servo with magnetic encoder)",
    "voltage_V": dsv([6.0, 12.0], SOURCES["FEETECH_STS3250_OPENELAB"]),
    "stall_torque_kgcm_12V": dsv(50.0, SOURCES["FEETECH_STS3250_OPENELAB"]),
    "gear_ratio": dsv(345, SOURCES["FEETECH_STS3250_OPENELAB"], "no-load speed not stated by vendor"),
    "price": {"vendor": "OpenELAB (EU)", "price": 68.95, "cur": "EUR", "note": "incl. VAT", "src": SOURCES["FEETECH_STS3250_OPENELAB"]},
}

# ---------------------------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------------------------
M3200 = {
    "family": "TE Connectivity M3200 industrial pressure transducer",
    "doc": SOURCES["TE_M3200_DS"],
    "output_code_3": dsv("0.5-4.5 V ratiometric, 5 V +/- 0.25 V supply", SOURCES["TE_M3200_DS"]),
    "supply_current_A": dsv(0.005, SOURCES["TE_M3200_DS"], "analog voltage output"),
    "rise_time_s": dsv(0.002, SOURCES["TE_M3200_DS"], "10-90 %, analog voltage output: < 2 ms"),
    "accuracy": dsv({"BFSL_pctFS": 0.25, "zero_offset_pctFS_25C": 0.5, "TEB_pctFS": 1.5, "stability_pctFS_per_yr": 0.25},
                    SOURCES["TE_M3200_DS"], "TEB over compensated -20..85 C"),
    "temp_C": dsv({"compensated": [-20, 85], "operating": [-40, 125]}, SOURCES["TE_M3200_DS"]),
    "wetted": dsv("17-4PH stainless one-piece body; port code 5 (1/4-18 NPT) has no O-ring; G1/4 (code B) uses NBR O-ring",
                  SOURCES["TE_M3200_DS"], "use code 5 for N2O service (no elastomer); oxygen-clean before use"),
    "port_code_5": dsv("1/4-18 NPT male, 2-3 turns from finger tight", SOURCES["TE_M3200_DS"]),
    "proof_burst": dsv({"proof_x_rated": 2.0, "burst_x_rated": 5.0}, SOURCES["TE_M3200_DS"]),
    "connector_code_4": dsv("Packard A (Metri-Pack 150 type) 3-pin", SOURCES["TE_M3200_DS"]),
    "envelope_reservation_mm": asv([30.0, 30.0, 80.0], None,
                                   "SPACE RESERVATION incl. mated connector and cable bend; TE drawing dims not retrieved (te.com blocked); verify"),
    "mass_kg": asv(0.050, [0.035, 0.070], "not stated in datasheet text; weigh on receipt"),
    "price_ref": {"vendor": "RS UK (M327L-000006-500PG, different output code)", "price": 66.25, "cur": "GBP", "note": "excl. VAT, 1 off", "src": SOURCES["TE_M327L_RS"]},
}

PX3 = {
    "family": "Honeywell PX3 heavy-duty transducer (comparator)",
    "doc": SOURCES["HONEYWELL_PX3_DS"],
    "max_range_bar": dsv(50, SOURCES["HONEYWELL_PX3_DS"], "too low for tank MEOP 70 bar"),
    "response_s": dsv(0.002, SOURCES["HONEYWELL_PX3_DS"], "10-90 %"),
    "TEB_pctFS": dsv(1.0, SOURCES["HONEYWELL_PX3_DS"], "-20..85 C"),
    "seal": dsv("internal O-ring silicone or HNBR; N2O not in listed media", SOURCES["HONEYWELL_PX3_DS"], "rejected for N2O-wetted service"),
}

TEENSY41 = {
    "model": "PJRC Teensy 4.1 (SparkFun DEV-16771)",
    "cpu": dsv("NXP i.MX RT1062 ARM Cortex-M7 600 MHz, 1024 KB RAM (512 KB TCM), 8 MB flash", SOURCES["PJRC_T41"]),
    "io": dsv({"digital_io": 55, "breadboard_pins": 42, "pwm": 35, "analog_in": 18, "uart": 8, "spi": 3, "i2c": 3,
               "can": "3 (1 with CAN FD)", "sd": "microSD, native 4-bit SDIO", "ethernet": "10/100 DP83825 PHY"}, SOURCES["PJRC_T41"]),
    "adc_note": dsv("10-bit default, 12-bit hardware, ~10 usable bits", SOURCES["PJRC_T41"]),
    "current_A_600MHz": dsv(0.100, SOURCES["PJRC_T41"], "page text says 'Teensy 4.0' in that sentence"),
    "ext_3v3_max_A": dsv(0.250, SOURCES["PJRC_T41"], "recommended external load on 3.3 V pin"),
    "vusb_vin": dsv("cut VUSB-VIN pads to power from VIN with USB connected", SOURCES["PJRC_T41"]),
    "logic": dsv("3.3 V, inputs NOT 5 V tolerant", SOURCES["PJRC_T41"]),
    "dims_mm": asv([61.0, 18.0], None, "2.4 x 0.7 in board outline (PJRC drawing; text not retrieved) - verify"),
    "price": {"vendor": "Electrokit (SE)", "price": 379.0, "cur": "SEK", "note": "incl. 25 % VAT, in stock 42 pcs", "src": SOURCES["ELECTROKIT_T41"]},
}

IGNITER_LIT = {
    "whitmore2014_hvps": dsv("UltraVolt 8C-30C series HV DC/DC (10 kV max)", SOURCES["WHITMORE_2014"]),
    "whitmore2014_current_limit_A": dsv(0.0145, SOURCES["WHITMORE_2014"], "14.25-14.5 mA used"),
    "whitmore2014_power_W": dsv([2.0, 10.0], SOURCES["WHITMORE_2014"], "8 W micro-hybrid, <4 W 75 mm motor"),
    "whitmore2014_energy_J": dsv([1.6, 5.0], SOURCES["WHITMORE_2014"], "'2-4 J' in conclusion"),
    "whitmore2014_window_s": dsv([1.0, 2.0], SOURCES["WHITMORE_2014"]),
    "whitmore2014_oxidiser": dsv("most effective with GOX; N2O demonstrated", SOURCES["WHITMORE_2014"],
                                  "N2O applicability is Combustion's call"),
}
