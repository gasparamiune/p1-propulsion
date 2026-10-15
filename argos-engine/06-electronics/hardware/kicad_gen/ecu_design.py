"""ARGOS engine ECU v2.5 - schematic content (parts, pins, nets), 06-electronics, 2026-10-13.
v2.5 (2026-10-13, firmware v2.10; LEAD CHANGELOG 166 (3), 172, 175): HARDWARE PURGE WINDOW - FC discrete PURGE_EN on J512 (1k series,
100k pull-down, ESD, 74LVC1G17 Schmitt U571) triggers a non-retriggerable one-shot U572 LTC6993-1 (rising edge; RSET 75.0k 0.1 %,
DIVCODE 7 = R1 1.00M / R2 887k, NDIV 2^21, POL 0: tOUT = 2^21 x 75k/50k x 1 us = 3.146 s, max error 3.0 % + 0.1 %: 3.05-3.24 s;
DATASHEET LTC6993 Rev F Table 1 / ElecChar). PURGE_WIN = PURGE_EN AND one-shot (U573). Each bleed drive is ANDed with PURGE_WIN on
its own IC: V1 = pin 15 (shared with HTR_PERMIT_CMD, pins are short) AND PURGE_WIN (U574) -> U304 2A2; V2 = pin 24 AND PURGE_WIN
(U575) -> U307. The shared pin can no longer open V1 outside the FC-opened, time-limited window (lead option for short pins). The
window covers the scheduled POWERED span (fill step + 2.5 s flow + vent, <= 3.00 s with the 20 ms FC lead, config.h); it does not
equal the 2.61 s both-open firmware cap (a cap-length one-shot would cut the scheduled flow) - report. Latent failure: a stuck-high
window chain (U571-U573) is invisible to the pad BIT -> pre-flight check with PURGE_EN low (bench plan v3 B-BLEED-1 / CHK-PW).
ADC2 CH3 = FA-1 flame-light head on J902 (12.7k/4.02k 0.1 % divider 0.240, 22 nF C0G 2.4 kHz, ESD, 100k open-head pull-down;
firmware v2.10 kPhotoMin/Max); the PREG diagnostic moves to TP902 (not read). Bleed peak-and-hold: architecture stated, not
drawn (coil data of the replacement valve unknown; calc/bleed_driver_v1.py); the drawn channels keep the SS14 + SMAJ24A fast-release
clamp (release energy check in the same calc).
v2.4 (2026-10-13, firmware v2.9): head-end bleed PROVISION drawn (LEAD 2026-10-13 A1 relight configuration (2); supersedes the v2.3
"not drawn, fallback only" note below): V1 drive BLEED_A on U304 2A2->2Y2 from pin 15 (shared with HTR_PERMIT_CMD: the heater works only
in SAFE with the ARM plug out / ARM bus off, the valve rail +12V_ARM only with the ARM bus on - the HAL ORs both), V2 drive BLEED_B on
pin 24 through its OWN buffer U307 74AHCT1G125 (/OE = watchdog; V1 and V2 drives share no IC), low-side channels Q580/Q590 on +12V_ARM
to J509/J510 (fixed-side valves; coil voltage TO-VERIFY: the Burkert 6027 HP page lists 24 V DC). P_mid: TE M3234 170BG on J511 ->
LMV331 U570 with hysteresis (rise 9.86 / fall 8.86 bar g, calc/hbleed_provision_v1.py) -> 2N7002 Q570 switching R572 33.2k into the
MV switch ladder. Pin 23 = MV_LADDER (A9): R_top 10k to +3V3; R0 82.5k (end of line), R1 9.53k (OPEN), R2 17.8k (CLOSED) sit in the MV
switch connector backshell (harness item, BOM); pin 24 freed for BLEED_B. Firmware: sensor_scale mvLadderDecode (mv_ladder_table.h).
v2.3 (2026-10-13): brings the schematic level with firmware v2.3-v2.8.3 and the LEAD hardware decisions it was written
against (the v2.2 schematic still showed the 2026-10-12 state):
  - TVC power chain (LEAD 2026-10-12 TVC supply decision (1)): 2 x AOD4185 in parallel, F401 deleted (F101 25 A + firmware e-fuse).
  - Pintle rail (LEAD 2026-10-13, calc/pintle_rail_v3.py, pintle_rail_ovtrip_v1.py): new sheet Pintle_Rail - TPS552882 buck-boost
    with its EXTERNAL buck-leg MOSFETs (DR1H/DR1L; missed in pintle_rail_v1/v2), FB 24.9k/4.75k, 2 x 220 uF polymer, LTC4365 OV
    disconnect 8.2 V (OV filter 1.0 nF, tau 9.4 us), /FAULT -> MV holding-magnet gate AND (U306); J403 pin 2 = PRAIL.
  - Second ADS131M04 (firmware v2.7): P_torch (070BG), PRAIL, pintle current (INA181A2 on the 12 mOhm sense resistor), PREG.
  - Three more MAX31856 (TC4 bore-top K, TC5/TC6 manifold state sensors MSS-1/MSS-2 type T, LEAD 2026-10-13).
  - SPI0 chip selects through an SN74LVC138A decoder (pins 8/9/10/20 -> 8 CS lines; no free Teensy pin otherwise).
  - Mode strap J620 (firmware v2.8, LEAD 2026-10-13) on pin 17 (spark current now TP502 only); bay DS18B20 #3 (J614).
  - GSE tank-heater interlock J616 HTR_ILK (LEAD 2026-10-12 condition (b), firmware v2.3 heater permit) on pin 15 (12 V rail
    sense dropped). Head-end bleed (option (a)): HELD AS FALLBACK ONLY (LEAD 2026-10-13, retained-vapour fix = coil re-route);
    not drawn - budget line in electronics.json v2 (U304 spare channel 2A2->2Y2, a SOL1-type 12 V channel, pin 15 shared).
  - Text only: Pc/P_torch TE M3200 070BG, P_feed/P_tank 170BG (LEAD 2026-10-13); OVP trip 31.47 bar g on the 070BG.
  Values of the new blocks: calc/ecu_v2p3_values_v1.py (reads this file). Datasheets read 2026-10-13 (WebFetch, ti.com):
  TI TPS552882 (pin functions, application section, compensation equations), TI CSD17578Q5A (SLPS526), TI SN74LVC138A
  (SCAS291W). LTC4365: the values read on 2026-10-12/13 for pintle_rail_v3 (OV 492.5-507.5 mV); the UV-pin threshold is
  ASSUMED equal (analog.com is blocked at the proxy, TO-CONFIRM).
v2.1 (lead decision 2026-10-12, chamber MEOP 45 bar): Pc transducer 0-1000 psig (was 0-500 psig, saturated in the
pintle-runaway / blocked-nozzle cases); independent hardware chamber over-pressure trip (LMV331 comparator on PC_SIG ->
SN74LVC1G175 latch -> 3-input ARM AND gate SN74LVC1G11, status to Teensy pin 29 = OVP_OK).
v2.2 (Combustion v2 relay + lead decisions 2026-10-12): OVP comparator filter C330 47 nF -> 220 nF (tau 5.3 ms, rejects
the 144-188 Hz Pc sense-line resonance); roll RCS provision = SOL4/SOL5 each drive one thruster pair (2 coils) through
a 4-pin Micro-Fit (J504/J505).

Single source of truth for the KiCad project (make_ecu_kicad.py), the pin map and the connector list.
Every connection is explicit: part pin number -> net name. None = deliberately unconnected (no-connect flag).
Values carry their basis in the 'Spec' field: DATASHEET (doc id), DERIVED (formula), DESIGN (choice), ASSUMED.
Datasheet documents read this session (2026-10-11/12): TI SLVSD26C (TPS54202), TI SCES586E (SN74LVC1G123),
TI SCLS228O (SN74AHCT244), AOS AOD4185 Rev4.2, AOS AO3400A Rev3.1, Diodes DS37023 Rev6-2 (DMN6075S),
onsemi ISL9V3040-F085C/D Rev3 (ISL9V3040), Maxim 19-7534 Rev0 (MAX31856), TI SBAS890 (ADS131M04 pinout),
Pololu #2895 product page (U3V70F12), PJRC Teensy 4.1 page/card, TI SLCS136V (LMV331), TI SCES560G (SN74LVC1G175),
TI SCES487I (SN74LVC1G11). Other parts: KiCad 7.0.11 library pinout,
manufacturer datasheet not re-read this session (flagged 'pinout per KiCad lib').
"""

PROJECT = 'argos_ecu'

# Teensy 4.1 pin allocation v2.3 (pin label -> net). 42 edge I/O, all 42 used (pin 29 = OVP_OK since v2.1; no spare).
# v2.3: 8/9/10/20 drive the SN74LVC138A CS decoder (was ADC_CS, TC1_CS, TC2_CS, TC3_CS); 15 = HTR_PERMIT_CMD (was V12_SENSE);
# 17 = MODE_SENSE (was IGN_ISENSE).
TEENSY_PINMAP = {
    '0': ('SOL3_VENT_CMD', 'out', 'FlexPWM: tank vent solenoid (VBAT, PWM hold), not ARM-gated, watchdog-gated'),
    '1': ('SOL4_ROLL_CW_CMD', 'out', 'roll RCS provision: CW thruster pair, 2 coils (12 V, ARM-gated)'),
    '2': ('TVC_A_PWM', 'out', 'FlexPWM4.2 333 Hz servo TVC-A (pitch)'),
    '3': ('TVC_B_PWM', 'out', 'FlexPWM4.2 333 Hz servo TVC-B (yaw)'),
    '4': ('PINTLE_PWM', 'out', 'FlexPWM2.0 333 Hz pintle throttle servo'),
    '5': ('MV_OPENER_PWM', 'out', 'FlexPWM2.1 333 Hz main-valve opener servo'),
    '6': ('MV_LATCH_CMD', 'out', 'main-valve holding magnet (ARM-gated)'),
    '7': ('ADC_DRDY', 'in', 'ADS131M04 ADC1 data ready (4 kSPS); ADC2 shares the clock, its DRDY goes to TP901 (polled)'),
    '8': ('CS_A0', 'out', 'SPI0 CS decoder U203 address A (LSB)'),
    '9': ('CS_A1', 'out', 'SPI0 CS decoder U203 address B'),
    '10': ('CS_A2', 'out', 'SPI0 CS decoder U203 address C (MSB): Y0 ADC1, Y1 ADC2, Y2-Y7 TC1-TC6'),
    '11': ('MOSI0', 'out', 'SPI0 MOSI'),
    '12': ('MISO0', 'in', 'SPI0 MISO (ADC1, ADC2 and 6 TC, 33 ohm per device)'),
    '13': ('SCK0', 'out', 'SPI0 SCK (on-board LED)'),
    '14': ('VBAT_SENSE', 'ain', 'A0 battery voltage /4.03'),
    '15': ('HTR_PERMIT_CMD', 'out', 'GSE tank-heater permit via U305 (SAFE; hardware cut at plug / ARM bus / watchdog) AND bleed V1 via U574 (AND PURGE_WIN, v2.5) -> U304 2A2 (+12V_ARM only)'),
    '16': ('IBAT_SENSE', 'ain', 'A2 battery current, INA181A1 x20 on 2 mOhm (25 A/V)'),
    '17': ('MODE_SENSE', 'ain', 'A3 mode strap J620 resistor code: FLIGHT 2.27 V, STAND 1.65 V, open 3.30 V, both 1.35 V'),
    '18': ('NTC_SERVO', 'ain', 'A4 pintle-servo bracket NTC 10k'),
    '19': ('V5SNS_SENSE', 'ain', 'A5 transducer excitation /2 (ratiometric correction)'),
    '20': ('CS_EN_N', 'out', 'SPI0 CS decoder enable (G2A, active low; 10k pull-up: no device selected in reset)'),
    '21': ('ARM_PLUG_SENSE', 'ain', 'A7 arming-plug voltage /4.03 (upstream of ARM switch)'),
    '22': ('ARM_BUS_SENSE', 'ain', 'A8 ARM bus voltage /4.03 (proves switch closed)'),
    '23': ('MV_LADDER', 'ain', 'A9 v2.4 ladder: MV OPEN / CLOSED switches + P_mid comparator (calc/hbleed_provision_v1.py)'),
    '24': ('BLEED_B_CMD', 'out', 'head-end bleed V2 command via U575 (AND PURGE_WIN, v2.5) -> U307 (ARM-gated, watchdog /OE)'),
    '25': ('ONEWIRE', 'io', '1-Wire DS18B20 tank wall temperatures'),
    '26': ('MOSI1', 'out', 'SPI1 MOSI to AS5048A encoders'),
    '27': ('SCK1', 'out', 'SPI1 SCK to encoders (1 MHz over cable)'),
    '28': ('SPARK_CMD', 'out', 'spark coil dwell pulses (ARM-gated, AC-coupled gate)'),
    '29': ('OVP_OK', 'in', 'hardware Pc over-pressure latch U331 Q: high = OK; low = tripped, ARM bus forced off'),
    '30': ('CAN_RX', 'in', 'CAN3 CRX3 (FD-capable) from MCP2562FD'),
    '31': ('CAN_TX', 'out', 'CAN3 CTX3 to MCP2562FD'),
    '32': ('SOL1_TORCH_OX_CMD', 'out', 'torch N2O solenoid (12 V, ARM-gated)'),
    '33': ('SOL2_TORCH_FUEL_CMD', 'out', 'torch propane solenoid (12 V, ARM-gated)'),
    '34': ('SOL5_ROLL_CCW_CMD', 'out', 'roll RCS provision: CCW thruster pair, 2 coils (12 V, ARM-gated)'),
    '35': ('ENC_A_CS', 'out', 'AS5048A gimbal axis A CS'),
    '36': ('ENC_B_CS', 'out', 'AS5048A gimbal axis B CS'),
    '37': ('ENC_P_CS', 'out', 'AS5048A pintle crank CS'),
    '38': ('ARM_REQ', 'out', 'ARM switch request (AND watchdog OK AND OVP_OK); rising edge re-arms the OVP latch'),
    '39': ('MISO1', 'in', 'SPI1 MISO from encoders (47 ohm per encoder)'),
    '40': ('TVC_PWR_CMD', 'out', 'TVC servo power switch (watchdog-gated)'),
    '41': ('WDI', 'out', 'external watchdog kick (rising edge each healthy 1 ms tick)'),
}

FP = {
    'R0603': 'Resistor_SMD:R_0603_1608Metric', 'R1206': 'Resistor_SMD:R_1206_3216Metric',
    'R2512': 'Resistor_SMD:R_2512_6332Metric', 'C0603': 'Capacitor_SMD:C_0603_1608Metric',
    'C0805': 'Capacitor_SMD:C_0805_2012Metric', 'C1206': 'Capacitor_SMD:C_1206_3216Metric',
    'CP10': 'Capacitor_SMD:CP_Elec_10x10.5', 'CP8': 'Capacitor_SMD:CP_Elec_8x10.5', 'CP6': 'Capacitor_SMD:CP_Elec_6.3x7.7',
    'SOT23': 'Package_TO_SOT_SMD:SOT-23', 'SOT23-5': 'Package_TO_SOT_SMD:SOT-23-5', 'SOT23-6': 'Package_TO_SOT_SMD:SOT-23-6',
    'TSOT23-5': 'Package_TO_SOT_SMD:TSOT-23-5', 'DPAK': 'Package_TO_SOT_SMD:TO-252-2', 'SOT323': 'Package_TO_SOT_SMD:SOT-323_SC-70',
    'SOIC8': 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'SSOP8': 'Package_SO:SSOP-8_2.95x2.8mm_P0.65mm',
    'TSSOP14': 'Package_SO:TSSOP-14_4.4x5mm_P0.65mm', 'TSSOP20': 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',
    'TSSOP16': 'Package_SO:TSSOP-16_4.4x5mm_P0.65mm', 'TSOT23-8': 'Package_TO_SOT_SMD:TSOT-23-8',
    'C1210': 'Capacitor_SMD:C_1210_3225Metric', 'TDSON8': 'Package_TO_SOT_SMD:TDSON-8-1',
    'L_XAL1010': 'Inductor_SMD:L_Coilcraft_XAL1010-XXX', 'TPS_RPM': 'argos_ecu:TI_RPM0026A_PLACEHOLDER',
    'SMA': 'Diode_SMD:D_SMA', 'SOD923': 'Diode_SMD:D_SOD-923', 'L0603': 'Inductor_SMD:L_0603_1608Metric',
    'L_SRN6045': 'Inductor_SMD:L_Bourns_SRN6045TA',
    'MF2': 'Connector_Molex:Molex_Micro-Fit_3.0_43650-0200_1x02_P3.00mm_Horizontal',
    'MF3': 'Connector_Molex:Molex_Micro-Fit_3.0_43650-0300_1x03_P3.00mm_Horizontal',
    'MF4': 'Connector_Molex:Molex_Micro-Fit_3.0_43650-0400_1x04_P3.00mm_Horizontal',
    'GH2': 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal',
    'GH3': 'Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal',
    'GH4': 'Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal',
    'GH5': 'Connector_JST:JST_GH_SM05B-GHS-TB_1x05-1MP_P1.25mm_Horizontal',
    'GH6': 'Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal',
    'XT60': 'Connector_AMASS:AMASS_XT60PW-M_1x02_P7.20mm_Horizontal',
    'XT30': 'Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal',
    'TB2': 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MPT-0,5-2-2.54_1x02_P2.54mm_Horizontal',
    'HDR3': 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
    'FUSE_MINI': 'Fuse:Fuseholder_Blade_Mini_Keystone_3568', 'FUSE1206': 'Fuse:Fuse_1206_3216Metric',
    'TP': 'TestPoint:TestPoint_Pad_D1.5mm', 'MH': 'MountingHole:MountingHole_3.2mm_M3',
    'OSC': 'Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',
}

# ------------------------------------------------------------------------------------------- helpers
def P(ref, lib, sym, value, nets, fp='', rot=0, small=False, units=None, unit_dx=30.48, unit_dy=0.0, **fields):
    return {'ref': ref, 'lib': lib, 'sym': sym, 'value': value, 'nets': {str(k): v for k, v in nets.items()},
            'footprint': fp, 'rot': rot, 'small': small, 'units': units, 'unit_dx': unit_dx, 'unit_dy': unit_dy,
            'fields': {k: v for k, v in fields.items() if v}}


def DNP(parts, reason):
    """v2.3: mark parts Do-Not-Populate (KiCad dnp flag + DNP field read by the grouped BOM)."""
    for p in parts:
        p['dnp'] = True
        p['fields']['DNP'] = 'DNP: ' + reason
    return parts


def R(ref, value, n1, n2, fp='R0603', horiz=True, spec='', mpn='', fn=''):
    return P(ref, 'Device', 'R', value, {1: n1, 2: n2}, FP[fp], rot=90 if horiz else 0, small=True,
             Spec=spec, MPN=mpn, Function=fn)


def C(ref, value, n1, n2, fp='C0603', horiz=False, spec='', mpn='', fn=''):
    return P(ref, 'Device', 'C', value, {1: n1, 2: n2}, FP[fp], rot=90 if horiz else 0, small=True,
             Spec=spec, MPN=mpn, Function=fn)


def CP(ref, value, npos, nneg, fp='CP10', spec='', mpn='', fn=''):
    return P(ref, 'Device', 'C_Polarized', value, {1: npos, 2: nneg}, FP[fp], rot=0, small=True,
             Spec=spec, MPN=mpn, Function=fn)


def FUSE(ref, value, n1, n2, fp, spec='', mpn='', fn=''):
    return P(ref, 'Device', 'Fuse', value, {1: n1, 2: n2}, FP[fp], rot=90, small=True, Spec=spec, MPN=mpn, Function=fn)


def NFET(ref, sym, value, g, d, s, fp='SOT23', spec='', mpn='', fn=''):
    lib = 'Transistor_FET'
    return P(ref, lib, sym, value, {1: g, 2: s, 3: d}, FP[fp], small=True, Spec=spec, MPN=mpn or value, Function=fn)


def CONN(ref, n, value, nets, fp, fn, spec='', mpn=''):
    return P(ref, 'Connector_Generic', 'Conn_01x%02d' % n, value, {i + 1: v for i, v in enumerate(nets)}, FP[fp],
             Function=fn, Spec=spec, MPN=mpn)


def TP(ref, net):
    return P(ref, 'Connector', 'TestPoint', 'TP_' + net.replace('+', ''), {1: net}, FP['TP'], small=True,
             Function='test point ' + net)


# 2-key / clamp solenoid low-side channel
def solenoid_channel(prefix, n, gate_net, supply, conn_ref, fn, fast=True, coils=1):
    """Low-side DMN6075S + 100R gate + 100k pull-down + SS14 (+ SMAJ24A in series for fast release).
    coils=2 (v2.2 roll RCS provision): one channel drives a thruster pair, 4-pin connector with a +/low-side pair per coil."""
    g, d, k = prefix + '_GATE', prefix + '_DRAIN', prefix + '_CLAMP'
    parts = [
        R('R%d' % n, '100', gate_net, g, spec='DESIGN gate damping', fn=fn + ' gate'),
        R('R%d' % (n + 1), '100k', g, 'GND', horiz=False, spec='DESIGN off when undriven', fn=fn + ' gate pull-down'),
        NFET('Q%d' % n, 'DMN6075S', 'DMN6075S-7', g, d, 'GND',
             spec='DATASHEET DS37023 Rev6-2: 60 V, 2.0 A, RDS(on) <=120 mOhm @4.5 V', fn=fn),
    ]
    if fast:
        parts += [
            P('D%d' % n, 'Diode', 'SS14', 'SS14', {2: d, 1: k}, FP['SMA'], rot=0, small=True,
              Spec='freewheel path', Function=fn + ' freewheel'),
            P('D%d' % (n + 1), 'Diode', 'SMAJ24A', 'SMAJ24A', {1: k, 2: supply}, FP['SMA'], rot=0, small=True,
              Spec='DERIVED fast release: Vds_max ~ Vsupply + 0.5 + 29.5 V < 60 V', Function=fn + ' clamp'),
        ]
    else:
        parts += [P('D%d' % n, 'Diode', 'SS14', 'SS14', {2: d, 1: supply}, FP['SMA'], rot=0, small=True,
                    Spec='freewheel (PWM hold)', Function=fn + ' freewheel')]
    if coils == 2:
        parts.append(CONN(conn_ref, 4, fn, [supply, d, supply, d], 'MF4',
                          fn + ' (Micro-Fit 3.0 4-pin: coil 1 pins 1 +/2 low side, coil 2 pins 3 +/4 low side)'))
    else:
        parts.append(CONN(conn_ref, 2, fn, [supply, d], 'MF2', fn + ' (Micro-Fit 3.0, pin1 +, pin2 low side)'))
    return parts


# ------------------------------------------------------------------------------------------- sheets
def sheet_power():
    g = []
    g.append(('Battery input, main fuse, current sense, transient clamp', [
        CONN('J101', 2, 'BATT_2S_XT60', ['VBAT_IN', 'GND'], 'XT60', 'battery 2S LiPo input (pin1 +, pin2 -; verify AMASS polarity marking)'),
        FUSE('F101', '25A', 'VBAT_IN', 'VBAT_F', 'FUSE_MINI', spec='DESIGN: >= 1.3 x 18.4 A two-servo stall transient; slow-blow class',
             mpn='Littelfuse 0297025 (ATM 25 A) + Keystone 3568 holder', fn='main fuse'),
        P('R101', 'Device', 'R', '2m 1% 3W', {1: 'VBAT_F', 2: 'VBAT'}, FP['R2512'], rot=90, small=True,
          Spec='DERIVED: 50 A x 2 mOhm x 20 = 2.0 V at A2 (Teensy ADC 3.3 V FS)', Function='battery current shunt'),
        P('U101', 'Amplifier_Current', 'INA181', 'INA181A1IDBVR', {1: 'IBAT_SENSE_RAW', 2: 'GND', 3: 'VBAT_F', 4: 'VBAT', 5: 'GND', 6: '+3V3'},
          FP['SOT23-6'], Spec='gain 20 V/V (A1); CM -0.2..26 V; pinout per KiCad lib', Function='battery current amplifier'),
        R('R102', '1k', 'IBAT_SENSE_RAW', 'IBAT_SENSE', spec='DERIVED RC 1.6 kHz anti-alias for 1 kHz sampling'),
        C('C101', '100nF/50V X7R', 'IBAT_SENSE', 'GND'),
        P('D101', 'Diode', 'SMAJ10A', 'SMAJ10A', {1: 'VBAT', 2: 'GND'}, FP['SMA'], small=True,
          Spec='DESIGN: standoff 10 V > 8.4 V; clamps servo regeneration/ESD below LT1761 20 V abs max', Function='VBAT TVS'),
        CP('C102', '470uF/16V low-ESR', 'VBAT', 'GND', 'CP10', spec='DESIGN servo transient reservoir', fn='VBAT bulk'),
    ]))
    g.append(('Logic supply path: 2 A fuse, Schottky, 1 mF hold-up', [
        FUSE('F102', '2A', 'VBAT', 'VBAT_LF', 'FUSE1206', mpn='Littelfuse 0466002 (1206, 2 A fast)', fn='logic branch fuse'),
        P('D102', 'Diode', 'SS34', 'SS34', {2: 'VBAT_LF', 1: 'VLOGIC'}, FP['SMA'], small=True,
          Spec='DESIGN blocks back-feed so servo sag does not drain hold-up', Function='logic OR diode'),
        CP('C103', '1000uF/16V', 'VLOGIC', 'GND', 'CP10',
           spec='DERIVED hold-up: 0.5 C (7.0^2-4.5^2)/2.9 W = 5 ms at peak logic load', fn='logic hold-up'),
    ]))
    g.append(('5 V buck TPS54202 (TI SLVSD26C 5 V design: 15 uH, 2x22 uF, 100k/13.3k, 75 pF)', [
        P('U102', 'Regulator_Switching', 'TPS54202DDC', 'TPS54202DDCR',
          {1: 'GND', 2: 'SW5', 3: 'VLOGIC', 4: 'FB5', 5: None, 6: 'BOOT5'}, FP['SOT23-6'],
          Spec='DATASHEET SLVSD26C: VIN 4.5-28 V, 2 A, 500 kHz, VREF 0.596 V +/-2.5 %, EN float = enabled',
          Function='+5V logic buck'),
        C('C104', '10uF/25V X7R', 'VLOGIC', 'GND', 'C1206'), C('C105', '10uF/25V X7R', 'VLOGIC', 'GND', 'C1206'),
        C('C106', '100nF/50V X7R', 'VLOGIC', 'GND'),
        C('C107', '100nF/50V X7R', 'BOOT5', 'SW5', horiz=True, spec='DATASHEET SLVSD26C 0.1 uF BOOT'),
        P('L101', 'Device', 'L', '15uH', {1: 'SW5', 2: '+5V'}, FP['L_SRN6045'], rot=90, small=True,
          Spec='DATASHEET SLVSD26C 5 V design 15 uH; Isat >= 3.9 A (current-limit max) TO-VERIFY part', Function='buck inductor'),
        C('C108', '22uF/25V X7R', '+5V', 'GND', 'C1206'), C('C109', '22uF/25V X7R', '+5V', 'GND', 'C1206'),
        R('R103', '100k 1%', '+5V', 'FB5', horiz=False, spec='DERIVED 0.596 x (1+100/13.3) = 5.08 V'),
        R('R104', '13.3k 1%', 'FB5', 'GND', horiz=False),
        C('C110', '75pF C0G', '+5V', 'FB5', spec='DATASHEET SLVSD26C feed-forward'),
    ]))
    g.append(('Low-noise LDOs: +3V3A (ADC AVDD), +3V3_ENC (encoder cables), +5V_SNS (transducers)', [
        P('U103', 'Regulator_Linear', 'MIC5205-3.3YM5', 'MIC5205-3.3YM5', {1: '+5V', 2: 'GND', 3: '+5V', 4: 'BP3A', 5: '+3V3A'},
          FP['SOT23-5'], Spec='150 mA LDO; pinout per KiCad lib', Function='+3V3A for ADS131M04 AVDD'),
        C('C111', '1uF/25V X7R', '+5V', 'GND'), C('C112', '470pF C0G', 'BP3A', 'GND'), C('C113', '2.2uF/16V X7R', '+3V3A', 'GND'),
        P('U104', 'Regulator_Linear', 'MIC5205-3.3YM5', 'MIC5205-3.3YM5', {1: '+5V', 2: 'GND', 3: '+5V', 4: 'BP3E', 5: '+3V3_ENC'},
          FP['SOT23-5'], Spec='150 mA LDO, separate so a cable short cannot pull down MCU 3V3', Function='+3V3_ENC encoder supply'),
        C('C114', '1uF/25V X7R', '+5V', 'GND'), C('C115', '470pF C0G', 'BP3E', 'GND'), C('C116', '2.2uF/16V X7R', '+3V3_ENC', 'GND'),
        P('U105', 'Regulator_Linear', 'LT1761-5', 'LT1761ES5-5', {1: 'VLOGIC', 2: 'GND', 3: 'VLOGIC', 4: 'BYP5S', 5: '+5V_SNS'},
          FP['TSOT23-5'], Spec='100 mA low-noise LDO; 3 x 5 mA transducers; pinout per KiCad lib', Function='+5V_SNS transducer excitation'),
        C('C117', '1uF/25V X7R', 'VLOGIC', 'GND'), C('C118', '10nF C0G', 'BYP5S', '+5V_SNS'), C('C119', '10uF/16V X7R', '+5V_SNS', 'GND', 'C0805'),
    ]))
    g.append(('Battery voltage sense, test points, mounting', [
        R('R105', '10k 0.1%', 'VBAT', 'VBAT_SENSE', horiz=False, spec='DERIVED 13.3 V full scale (ratio 0.248)'),
        R('R106', '3.3k 0.1%', 'VBAT_SENSE', 'GND', horiz=False),
        C('C120', '100nF/50V X7R', 'VBAT_SENSE', 'GND'),
        TP('TP101', 'VBAT'), TP('TP102', 'VLOGIC'), TP('TP103', '+5V'), TP('TP104', '+3V3'), TP('TP105', 'GND'),
        P('H101', 'Mechanical', 'MountingHole', 'M3', {}, FP['MH'], small=True, Function='mounting hole'),
        P('H102', 'Mechanical', 'MountingHole', 'M3', {}, FP['MH'], small=True, Function='mounting hole'),
        P('H103', 'Mechanical', 'MountingHole', 'M3', {}, FP['MH'], small=True, Function='mounting hole'),
        P('H104', 'Mechanical', 'MountingHole', 'M3', {}, FP['MH'], small=True, Function='mounting hole'),
    ]))
    return g


def sheet_mcu():
    from custom_symbols import teensy_pad
    nets = {teensy_pad('VIN'): '+5V', '1': 'GND', '47': 'GND', '34': 'GND', '15': '+3V3', '46': '+3V3'}
    for lab, (net, _, _) in TEENSY_PINMAP.items():
        nets[teensy_pad(lab)] = net
    g = []
    g.append(('MCU: PJRC Teensy 4.1 on 2x24 sockets (cut VUSB-VIN pads; USB is service only)', [
        P('U201', None, 'Teensy41', 'Teensy_4.1', nets, 'argos_ecu:Teensy41_Socket',
          Spec='DATASHEET PJRC: 600 MHz i.MX RT1062, 3.3 V I/O NOT 5 V tolerant, 3.3 V out 250 mA max',
          MPN='PJRC Teensy 4.1 (DEV-16771)', Function='engine ECU MCU'),
        CP('C201', '100uF/16V', '+5V', 'GND', 'CP6', fn='VIN bulk'),
        C('C202', '100nF/50V X7R', '+5V', 'GND'),
    ]))
    g.append(('CAN FD transceiver MCP2562FD (CAN3, 1 Mbit/s classic, FD-ready), split termination, ESD', [
        P('U202', 'Interface_CAN_LIN', 'MCP2562-E-SN', 'MCP2562FD-E/SN',
          {1: 'CAN_TX', 2: 'GND', 3: '+5V', 4: 'CAN_RX', 5: '+3V3', 6: 'CANL', 7: 'CANH', 8: 'GND'}, FP['SOIC8'],
          Spec='MCP2562FD pin-compatible with MCP2562 symbol; STBY tied low = normal mode; VIO 3.3 V; pinout per KiCad lib',
          Function='CAN transceiver'),
        C('C203', '100nF/50V X7R', '+5V', 'GND'), C('C204', '100nF/50V X7R', '+3V3', 'GND'),
        R('R201', '60.4 1%', 'CANH', 'CAN_SPLIT', spec='DESIGN split termination 120 ohm (ECU is one bus end)'),
        R('R202', '60.4 1%', 'CANL', 'CAN_SPLIT'),
        C('C205', '4.7nF/50V C0G', 'CAN_SPLIT', 'GND'),
        P('D201', 'Power_Protection', 'NUP2105L', 'NUP2105L', {1: 'CANH', 2: 'CANL', 3: 'GND'}, FP['SOT23'], small=True,
          Spec='CAN bus ESD/surge protector; pinout per KiCad lib', Function='CAN ESD'),
        CONN('J201', 4, 'CAN_FC', ['CANH', 'CANL', 'GND', 'CAN_SHIELD'], 'GH4', 'CAN to flight computer / test-stand bridge'),
        R('R203', '1M', 'CAN_SHIELD', 'GND', horiz=False, spec='DESIGN shield drain: RC to GND (no DC ground loop)'),
        C('C206', '10nF/100V X7R', 'CAN_SHIELD', 'GND'),
    ]))
    # v2.3: 8 SPI0 devices (ADC1, ADC2, 6 x MAX31856) on the 4 pins that carried 4 CS lines in v2.2. HAL rule: change A2..A0 only
    # while CS_EN_N is high (an address change while enabled can glitch another CS for a few ns), then pull CS_EN_N low and wait
    # >= 1 us [DESIGN] before the first SCLK edge: covers the decoder tpd (6.7 ns max, SCAS291W) and the device CS setup times
    # (MAX31856 19-7534, ADS131M04 SBAS890: not re-read this session).
    g.append(('SPI0 chip-select decoder SN74LVC138A (v2.3): CS_A2..A0 + CS_EN_N -> ADC1, ADC2, TC1-TC6; all CS high in reset', [
        P('U203', '74xx', '74HC138', 'SN74LVC138APWR',
          {1: 'CS_A0', 2: 'CS_A1', 3: 'CS_A2', 4: 'CS_EN_N', 5: 'GND', 6: '+3V3', 8: 'GND', 16: '+3V3',
           15: 'ADC1_CS', 14: 'ADC2_CS', 13: 'TC1_CS', 12: 'TC2_CS', 11: 'TC3_CS', 10: 'TC4_CS', 9: 'TC5_CS', 7: 'TC6_CS'},
          FP['TSSOP16'], Spec='DATASHEET TI SCAS291W: pinout = KiCad 74HC138 symbol (A,B,C = A0..A2; G2A,G2B = ~E0,~E1; G1 = E2); '
                              'VCC 1.65-3.6 V, inputs to 5.5 V, tpd A->Y 6.7 ns max at 3.3 V', MPN='SN74LVC138APWR',
          Function='SPI0 CS decoder'),
        C('C207', '100nF/50V X7R', '+3V3', 'GND'),
        R('R204', '10k', 'CS_EN_N', '+3V3', horiz=False, spec='DESIGN decoder disabled (all CS high) while the MCU pins are high-Z'),
        R('R205', '100k', 'CS_A0', 'GND', horiz=False, spec='DESIGN defined address in reset'),
        R('R206', '100k', 'CS_A1', 'GND', horiz=False), R('R207', '100k', 'CS_A2', 'GND', horiz=False),
    ]))
    return g


def sheet_safety():
    g = []
    g.append(('Arming plug (physical break) and ARM high-side switch (soft start)', [
        FUSE('F301', '15A', 'VBAT', 'VBAT_ARMF', 'FUSE_MINI', mpn='Littelfuse 0297015 (ATM 15 A) + Keystone 3568', fn='ARM branch fuse'),
        CONN('J301', 2, 'ARM_PLUG_XT30', ['VBAT_ARMF', 'ARM_PLUG'], 'XT30',
             'arming plug socket: insert-to-arm XT30 shorting plug (red tag) breaks igniter, valve, pintle power'),
        P('Q301', 'Device', 'Q_PMOS_GDS', 'AOD4185', {1: 'ARM_GATE', 2: 'ARM_BUS', 3: 'ARM_PLUG'}, FP['DPAK'], small=True,
          Spec='DATASHEET AOS Rev4.2: -40 V, -40 A, RDS(on) <= 20 mOhm @ -4.5 V, VGS +/-20 V', MPN='AOD4185',
          Function='ARM bus switch'),
        R('R301', '47k', 'ARM_GATE', 'ARM_PLUG', horiz=False, spec='DESIGN off-state pull-up'),
        R('R302', '4.7k', 'ARM_GATE', 'ARM_GATE_DRV', spec='DERIVED |VGS| on = 8.4 x 47/51.7 = 7.6 V'),
        C('C301', '47nF/50V X7R', 'ARM_GATE', 'ARM_BUS', horiz=True,
          spec='DERIVED Miller soft start ~24 V/ms (inrush ~ C_bus x dV/dt); off ~6 ms (bench verify)'),
        NFET('Q302', '2N7002', '2N7002', 'ARM_EN', 'ARM_GATE_DRV', 'GND', fn='ARM switch driver'),
        R('R303', '100k', 'ARM_EN', 'GND', horiz=False, spec='DESIGN off when U301 unpowered'),
        P('U301', '74xGxx', '74LVC1G11', 'SN74LVC1G11DBVR', {1: 'ARM_REQ', 3: 'WD_OK', 6: 'OVP_OK', 2: 'GND', 4: 'ARM_EN', 5: '+3V3'},
          FP['SOT23-6'], Spec='DATASHEET SCES487I: ARM_EN = ARM_REQ AND WD_OK AND OVP_OK (three independent conditions); Ioff',
          Function='ARM permit AND (v2.1: 3 inputs)'),
        C('C302', '100nF/50V X7R', '+3V3', 'GND'),
        R('R304', '100k', 'ARM_REQ', 'GND', horiz=False, spec='DESIGN MCU reset (high-Z) = no ARM'),
        R('R305', '10k 0.1%', 'ARM_PLUG', 'ARM_PLUG_SENSE', horiz=False), R('R306', '3.3k 0.1%', 'ARM_PLUG_SENSE', 'GND', horiz=False),
        C('C303', '100nF/50V X7R', 'ARM_PLUG_SENSE', 'GND'),
        R('R307', '10k 0.1%', 'ARM_BUS', 'ARM_BUS_SENSE', horiz=False), R('R308', '3.3k 0.1%', 'ARM_BUS_SENSE', 'GND', horiz=False),
        C('C304', '100nF/50V X7R', 'ARM_BUS_SENSE', 'GND'),
        P('U302', 'Regulator_Linear', 'MIC5205-5.0YM5', 'MIC5205-5.0YM5', {1: 'ARM_BUS', 2: 'GND', 3: 'ARM_BUS', 4: 'BP5A', 5: '+5V_ARM'},
          FP['SOT23-5'], Spec='gate-drive rail exists only when ARM bus is live (hardware interlock)', Function='+5V_ARM'),
        C('C305', '1uF/25V X7R', 'ARM_BUS', 'GND'), C('C306', '470pF C0G', 'BP5A', 'GND'), C('C307', '2.2uF/16V X7R', '+5V_ARM', 'GND'),
        TP('TP301', 'ARM_BUS'), TP('TP302', '+5V_ARM'),
    ]))
    g.append(('Independent hardware watchdog SN74LVC1G123 (tw = K R C = 1.0-1.1 x 100k x 470nF = 47-52 ms)', [
        P('U303', '74xGxx', '74LVC1G123', 'SN74LVC1G123DCTR',
          {1: 'GND', 2: 'WDI', 3: 'WD_CLR', 4: 'GND', 5: 'WD_OK', 6: 'WD_C', 7: 'WD_RC', 8: '+3V3'}, FP['SSOP8'],
          units=[1, 2], unit_dx=30.48,
          Spec='DATASHEET SCES586E: B rising-edge retrigger with A low; K ~1.0-1.1 at 3.3 V; Ioff; no Q-bar output',
          Function='hardware watchdog (retriggerable monostable)'),
        R('R309', '100k 1%', 'WD_RC', '+3V3', horiz=False, spec='DATASHEET Rext >= 1 kOhm at VCC >= 3 V'),
        C('C308', '470nF/16V C0G/film', 'WD_C', 'WD_RC', horiz=True, spec='timing capacitor (C0G or PPS film for stability)'),
        R('R310', '10k', 'WD_CLR', '+3V3', horiz=False), C('C309', '100nF/50V X7R', '+3V3', 'GND'),
        R('R311', '100k', 'WD_OK', 'GND', horiz=False, spec='DESIGN WD_OK low when unpowered'),
        NFET('Q303', '2N7002', '2N7002', 'WD_OK', 'OE_ARM_N', 'GND', fn='/OE driver ARM buffer'),
        R('R312', '10k', 'OE_ARM_N', '+5V_ARM', horiz=False, spec='DATASHEET SCLS228O: OE pulled to VCC = high-Z at power up'),
        NFET('Q304', '2N7002', '2N7002', 'WD_OK', 'OE_SAFE_N', 'GND', fn='/OE driver SAFE buffer'),
        R('R313', '10k', 'OE_SAFE_N', '+5V', horiz=False),
        TP('TP303', 'WD_OK'),
    ]))
    # v2.1 lead decision 2026-10-12 (chamber MEOP 45 bar; ECU over-pressure abort ~30 bar). Independent of the MCU:
    # comparator on the transducer signal -> latch -> third input of the ARM AND gate. Values computed and toleranced
    # by calc/ovp_threshold_v1.py (reads this file). Firmware trips first at 30.0 bar abs; this path is the backup.
    g.append(('Hardware chamber over-pressure trip (~31 bar g): LMV331 -> SN74LVC1G175 latch -> ARM AND; re-armed only by an ARM_REQ rising edge', [
        R('R330', '100k 0.1%', 'PC_SIG', 'OVP_PC', horiz=False, spec='DERIVED tap 31.6/131.6 = 0.2401 (same scale as the ADC divider), Rth 24.0 kOhm'),
        R('R331', '31.6k 0.1%', 'OVP_PC', 'GND', horiz=False),
        C('C330', '220nF/50V C0G', 'OVP_PC', 'GND', 'C1206',
          spec='DERIVED tau = 24.0k x 220n = 5.3 ms: x0.17 at the ~180 Hz sense-line resonance (COMB v2), adds ~5 ms to the trip'),
        R('R332', '237k 0.1%', '+5V_SNS', 'OVP_REF', horiz=False,
          spec='DERIVED ratiometric threshold 29.4/266.4 x 5 V = 0.5518 V = PC_SIG 2.298 V = 31.47 bar g on the 070BG '
               '(calc/pc_transducer_v2.py; 31.0 bar g on the superseded 01KPG basis)'),
        R('R333', '29.4k 0.1%', 'OVP_REF', 'GND', horiz=False, spec='Rth 26.2 kOhm ~ tap Rth (bias currents roughly cancel)'),
        C('C331', '100nF/50V X7R', 'OVP_REF', 'GND', spec='reference filter 2.6 ms (DC reference; latch state at power-up is irrelevant, set by ARM_REQ)'),
        P('U330', 'Comparator', 'LMV331', 'LMV331IDBVR', {1: 'OVP_REF', 2: 'GND', 3: 'OVP_PC', 4: 'OVP_TRIP_N', 5: '+5V_SNS'}, FP['SOT23-5'],
          Spec='DATASHEET SLCS136V: Vio <= 9 mV, Iib <= 400 nA (-40..125 C), VICR -0.1..4.2 V at 5 V, open collector; '
               'on +5V_SNS so the inputs never exceed its supply', MPN='LMV331IDBVR', Function='Pc over-pressure comparator'),
        C('C332', '100nF/50V X7R', '+5V_SNS', 'GND'),
        R('R334', '10k', 'OVP_TRIP_N', '+3V3', horiz=False, spec='DESIGN pull-up to the latch rail (output low = over-pressure)'),
        C('C333', '1nF/50V C0G', 'OVP_TRIP_N', 'GND', spec='DESIGN EMI shunt at /CLR (10 us release)'),
        P('U331', '74xGxx', '74LVC1G175', 'SN74LVC1G175DBVR', {1: 'ARM_REQ', 2: 'GND', 3: '+3V3', 4: 'OVP_OK', 5: '+3V3', 6: 'OVP_TRIP_N'},
          FP['SOT23-6'], Spec='DATASHEET SCES560G: /CLR low forces Q low (asynchronous); Q <- D = 1 on the ARM_REQ rising edge; Ioff',
          MPN='SN74LVC1G175DBVR', Function='over-pressure latch (OVP_OK)'),
        C('C334', '100nF/50V X7R', '+3V3', 'GND'),
        R('R335', '100k', 'OVP_OK', 'GND', horiz=False, spec='DESIGN OVP_OK low when U331 unpowered'),
        TP('TP330', 'OVP_PC'), TP('TP331', 'OVP_REF'), TP('TP332', 'OVP_TRIP_N'), TP('TP333', 'OVP_OK'),
    ]))
    g.append(('ARM-gated gate buffer U304 SN74AHCT244 on +5V_ARM (/OE = watchdog)', [
        P('U304', '74xx', '74AHCT244', 'SN74AHCT244PWR',
          {1: 'OE_ARM_N', 19: 'OE_ARM_N', 10: 'GND', 20: '+5V_ARM',
           2: 'MV_LATCH_CMD', 18: 'MV_LATCH_GB', 4: 'SOL1_TORCH_OX_CMD', 16: 'SOL1_G', 6: 'SOL2_TORCH_FUEL_CMD', 14: 'SOL2_G',
           8: 'SPARK_CMD', 12: 'SPARK_DRV', 17: 'SOL4_ROLL_CW_CMD', 3: 'SOL4_G', 15: 'SOL5_ROLL_CCW_CMD', 5: 'SOL5_G',
           13: 'BLEED_A_GATED', 7: 'BLEED_A_G', 11: 'GND', 9: None}, FP['TSSOP20'],
          Spec='DATASHEET SCLS228O: VIH 2.0 V (3.3 V MCU OK), inputs -0.5..7 V independent of VCC',
          Function='ARM-gated 5 V gate drive'),
        C('C310', '100nF/50V X7R', '+5V_ARM', 'GND'),
        R('R314', '100k', 'MV_LATCH_CMD', 'GND', horiz=False), R('R315', '100k', 'SOL1_TORCH_OX_CMD', 'GND', horiz=False),
        R('R316', '100k', 'SOL2_TORCH_FUEL_CMD', 'GND', horiz=False), R('R317', '100k', 'SPARK_CMD', 'GND', horiz=False),
        R('R318', '100k', 'SOL4_ROLL_CW_CMD', 'GND', horiz=False), R('R319', '100k', 'SOL5_ROLL_CCW_CMD', 'GND', horiz=False),
    ]))
    # v2.3 (LEAD 2026-10-13 pintle-rail decision): an LTC4365 OV-disconnect trip releases the MV holding magnet in hardware,
    # independent of the firmware PRAIL path (ADC2 CH1 -> PINTLE_FAULT).
    g.append(('MV holding-magnet permit (v2.3): MV_LATCH_G = MV latch command AND PRAIL_OK (LTC4365 /FAULT, pintle sheet)', [
        P('U306', '74xGxx', '74LVC1G08', 'SN74LVC1G08DBVR', {1: 'MV_LATCH_GB', 2: 'PRAIL_OK', 3: 'GND', 4: 'MV_LATCH_G', 5: '+5V_ARM'},
          FP['SOT23-5'], Spec='2-input AND, inputs to 5.5 V, Ioff; on +5V_ARM (exists only with the ARM bus on); pinout per KiCad lib '
                             '(TI DBV), datasheet not re-read this session', MPN='SN74LVC1G08DBVR',
          Function='MV latch permit AND'),
        C('C312', '100nF/50V X7R', '+5V_ARM', 'GND'),
        R('R329', '100k', 'MV_LATCH_GB', 'GND', horiz=False, spec='DESIGN defined input while U304 is high-Z (watchdog) or unpowered'),
        TP('TP304', 'MV_LATCH_GB'),
    ]))
    g.append(('SAFE-allowed buffer U305 SN74AHCT244 on +5V: servo PWM 3.3->5 V (always on), vent + TVC power (watchdog)', [
        P('U305', '74xx', '74AHCT244', 'SN74AHCT244PWR',
          {1: 'GND', 19: 'OE_SAFE_N', 10: 'GND', 20: '+5V',
           2: 'TVC_A_PWM', 18: 'TVC_A_SIG_B', 4: 'TVC_B_PWM', 16: 'TVC_B_SIG_B', 6: 'PINTLE_PWM', 14: 'PINTLE_SIG_B',
           8: 'MV_OPENER_PWM', 12: 'MVOP_SIG_B', 17: 'SOL3_VENT_CMD', 3: 'SOL3_G', 15: 'TVC_PWR_CMD', 5: 'TVC_PWR_DRV',
           13: 'GND', 7: None, 11: 'HTR_PERMIT_CMD', 9: 'HTR_PERMIT_DRV'}, FP['TSSOP20'],
          Spec='servo inputs need >= 3.5 V class pulses over cable (5 V push-pull)', Function='servo PWM / SAFE outputs'),
        C('C311', '100nF/50V X7R', '+5V', 'GND'),
        R('R320', '100k', 'TVC_A_PWM', 'GND', horiz=False), R('R321', '100k', 'TVC_B_PWM', 'GND', horiz=False),
        R('R322', '100k', 'PINTLE_PWM', 'GND', horiz=False), R('R323', '100k', 'MV_OPENER_PWM', 'GND', horiz=False),
        R('R324', '100k', 'SOL3_VENT_CMD', 'GND', horiz=False), R('R325', '100k', 'TVC_PWR_CMD', 'GND', horiz=False),
        R('R328', '100k', 'HTR_PERMIT_CMD', 'GND', horiz=False, spec='DESIGN heater permit off while the MCU pin is high-Z'),
    ]))
    return g


def sheet_actuators():
    g = []
    # v2.3 (LEAD 2026-10-12 TVC supply decision (1), calc/tvc_supply_budget_v1.py): F401 deleted (hard shorts cleared by F101 25 A,
    # firmware e-fuse kEfuse_A on the pad), second AOD4185 in parallel; servo leads crimped to Micro-Fit (JR plug cut off), AWG18.
    g.append(('TVC servo power switch (watchdog-gated, soft start): 2 x AOD4185 in parallel, no branch fuse (v2.3), reservoirs', [
        P('Q401', 'Device', 'Q_PMOS_GDS', 'AOD4185', {1: 'TVC_GATE', 2: 'TVC_PWR', 3: 'VBAT'}, FP['DPAK'], small=True,
          Spec='DATASHEET AOS Rev4.2 (see Q301)', MPN='AOD4185', Function='TVC power switch A'),
        P('Q403', 'Device', 'Q_PMOS_GDS', 'AOD4185', {1: 'TVC_GATE', 2: 'TVC_PWR', 3: 'VBAT'}, FP['DPAK'], small=True,
          Spec='DATASHEET AOS Rev4.2; in parallel with Q401 (LEAD 2026-10-12)', MPN='AOD4185', Function='TVC power switch B'),
        R('R401', '47k', 'TVC_GATE', 'VBAT', horiz=False), R('R402', '4.7k', 'TVC_GATE', 'TVC_GATE_DRV'),
        C('C401', '47nF/50V X7R', 'TVC_GATE', 'TVC_PWR', horiz=True,
          spec='Miller soft start; C401 >> Cgd of two AOD4185, ramp about unchanged (B-PWR-1 verifies)'),
        NFET('Q402', '2N7002', '2N7002', 'TVC_PWR_DRV', 'TVC_GATE_DRV', 'GND', fn='TVC switch driver'),
        R('R403', '100k', 'TVC_PWR_DRV', 'GND', horiz=False),
        CP('C402', '470uF/16V low-ESR', 'TVC_PWR', 'GND', 'CP10', fn='TVC servo reservoir'),
        CP('C403', '220uF/16V low-ESR', 'ARM_BUS', 'GND', 'CP8', fn='MV-opener servo reservoir (the pintle servo is on PRAIL since v2.3)'),
        TP('TP401', 'TVC_PWR'),
    ]))
    g.append(('Servo connectors (Micro-Fit 3.0: 1 signal, 2 V+, 3 GND), 220 ohm series, ESD', [
        R('R404', '220', 'TVC_A_SIG_B', 'TVC_A_SIG', spec='DESIGN series termination/current limit'),
        R('R405', '220', 'TVC_B_SIG_B', 'TVC_B_SIG'), R('R406', '220', 'PINTLE_SIG_B', 'PINTLE_SIG'),
        R('R407', '220', 'MVOP_SIG_B', 'MVOP_SIG'),
        P('U401', 'Power_Protection', 'SRV05-4', 'SRV05-4', {1: 'TVC_A_SIG', 3: 'TVC_B_SIG', 4: 'PINTLE_SIG', 6: 'MVOP_SIG', 5: '+5V', 2: 'GND'},
          FP['SOT23-6'], Spec='ESD array; pinout per KiCad lib', Function='servo signal ESD'),
        CONN('J401', 3, 'SERVO_TVC_A', ['TVC_A_SIG', 'TVC_PWR', 'GND'], 'MF3',
             'servo TVC-A pitch (Savox SB-2292SG; lead crimped to Micro-Fit, JR plug cut off, v2.3)'),
        CONN('J402', 3, 'SERVO_TVC_B', ['TVC_B_SIG', 'TVC_PWR', 'GND'], 'MF3',
             'servo TVC-B yaw (Savox SB-2292SG; lead crimped to Micro-Fit, JR plug cut off, v2.3)'),
        CONN('J403', 3, 'SERVO_PINTLE', ['PINTLE_SIG', 'PRAIL', 'GND'], 'MF3',
             'pintle throttle servo MKS HV69 on the regulated rail PRAIL 7.49 V typ (crosses the gimbal, service loop)'),
        CONN('J404', 3, 'SERVO_MV_OPENER', ['MVOP_SIG', 'ARM_BUS', 'GND'], 'MF3', 'main-valve opener servo'),
    ]))
    return g


def sheet_igniter():
    g = []
    g.append(('12 V boost on ARM bus (Pololu U3V70F12): spark coil, torch and roll solenoids', [
        P('PS501', None, 'Pololu_U3V70F12', 'U3V70F12', {1: 'ARM_BUS', 2: None, 3: 'GND', 4: '+12V_ARM', 5: 'GND'},
          'argos_ecu:Pololu_U3V70_WireAttach',
          Spec='DATASHEET Pololu #2895: VIN 2.9-12 V, 12 V +/-4 %, input 6 A prolonged / 7 A seconds / 10 A cycle limit; EN pulled up to VIN (left open)',
          MPN='Pololu 2895', Function='12 V boost'),
        CP('C501', '100uF/16V', 'ARM_BUS', 'GND', 'CP6', spec='DATASHEET Pololu: >= 33 uF electrolytic near VIN'),
        CP('C502', '470uF/25V low-ESR', '+12V_ARM', 'GND', 'CP10', spec='DERIVED coil peak share: dV ~1.2 V at 470 uF'),
        TP('TP501', '+12V_ARM'),       # v2.3: the 12 V sense divider R501/R502/C503 is deleted (pin 15 = HTR_PERMIT_CMD); bench reads TP501
    ]))
    g.append(('Spark coil driver: logic-level ignition IGBT, AC-coupled gate (hardware max dwell), current sense', [
        C('C504', '2.2uF/16V X7R', 'SPARK_DRV', 'SPARK_AC', 'C0805', horiz=True,
          spec='DERIVED tau = 2.2 uF x (R505 || RGE 10-26k) = 18-37 ms: 3 ms dwell keeps VGE >= 4.2 V; stuck-high gate < VGE(th) after 24-50 ms'),
        R('R503', '47k', 'SPARK_AC', 'GND', horiz=False),
        P('D501', 'Diode', 'BAT54W', 'BAT54W', {1: 'GND', 3: 'SPARK_AC'}, FP['SOT323'], small=True,
          Spec='clamps negative gate swing; pinout per KiCad lib', Function='gate clamp'),
        R('R504', '100', 'SPARK_AC', 'SPARK_G'),
        P('Q501', 'Device', 'Q_NIGBT_GCE', 'ISL9V3040D3ST', {1: 'SPARK_G', 2: 'COIL_N', 3: 'IGN_SHUNT'}, FP['DPAK'], small=True,
          Spec='DATASHEET onsemi ISL9V3040-F085C/D Rev3: BVCER 400 V clamp, ESCIS 300 mJ, VCE(sat) 1.25 V @ 6 A VGE 4 V, VGEM +/-10 V',
          MPN='ISL9V3040D3ST-F085C', Function='spark coil switch'),
        P('R505', 'Device', 'R', '20m 1% 1W', {1: 'IGN_SHUNT', 2: 'GND'}, FP['R2512'], rot=0, small=True,
          Spec='DERIVED 4 A x 20 mOhm x 20 = 1.6 V', Function='coil current shunt'),
        P('U501', 'Amplifier_Current', 'INA181', 'INA181A1IDBVR', {1: 'IGN_ISENSE_RAW', 2: 'GND', 3: 'IGN_SHUNT', 4: 'GND', 5: 'GND', 6: '+3V3'},
          FP['SOT23-6'], Spec='gain 20; low-side', Function='coil current amplifier'),
        R('R506', '1k', 'IGN_ISENSE_RAW', 'IGN_ISENSE'), C('C505', '100nF/50V X7R', 'IGN_ISENSE', 'GND'),
        TP('TP502', 'IGN_ISENSE'),     # v2.3: no longer read by the Teensy (pin 17 = MODE_SENSE); bench scope point, 2.5 A/V
        CONN('J501', 2, 'SPARK_COIL', ['+12V_ARM', 'COIL_N'], 'MF2',
             'spark coil primary (COMB: 12 V, 4 A peak ASSUMED; coil primary >= 3 ohm so steady current <= 4 A)'),
    ]))
    g.append(('Torch solenoids (12 V, ARM-gated)', solenoid_channel('SOL1', 510, 'SOL1_G', '+12V_ARM', 'J502', 'SOL1 torch N2O') +
              solenoid_channel('SOL2', 520, 'SOL2_G', '+12V_ARM', 'J503', 'SOL2 torch propane')))
    g.append(('Roll RCS provision (LEAD 2026-10-12: 2 reserved channels, one N2O-vapour thruster pair each; 12 V, ARM-gated; '
              '<= 0.75 A per coil ASSUMED, no valve chosen)',
              solenoid_channel('SOL4', 530, 'SOL4_G', '+12V_ARM', 'J504', 'SOL4 roll CW pair', coils=2) +
              solenoid_channel('SOL5', 540, 'SOL5_G', '+12V_ARM', 'J505', 'SOL5 roll CCW pair', coils=2)))
    g.append(('Main-valve holding magnet (ARM bus, fast release; gate from U306 = command AND PRAIL_OK since v2.3)',
              solenoid_channel('MVL', 550, 'MV_LATCH_G', 'ARM_BUS', 'J506', 'MV latch magnet')))

    vent = [
        FUSE('F501', '3A', 'VBAT', 'VBAT_VENTF', 'FUSE1206', mpn='Littelfuse 0466003 (1206, 3 A fast)', fn='vent branch fuse'),
        R('R560', '100', 'SOL3_G', 'SOL3_GATE'), R('R561', '100k', 'SOL3_GATE', 'GND', horiz=False),
        NFET('Q560', 'AO3400A', 'AO3400A', 'SOL3_GATE', 'SOL3_DRAIN', 'GND',
             spec='DATASHEET AOS Rev3.1: 30 V, 5.7 A, RDS(on) <= 32 mOhm @4.5 V', fn='SOL3 vent switch'),
        P('D560', 'Diode', 'SS14', 'SS14', {2: 'SOL3_DRAIN', 1: 'VBAT_VENTF'}, FP['SMA'], small=True, Spec='freewheel (PWM hold)',
          Function='vent freewheel'),
        CONN('J507', 2, 'SOL3_VENT', ['VBAT_VENTF', 'SOL3_DRAIN'], 'MF2', 'SOL3 tank vent (VBAT 6.6-8.4 V, PWM hold; coil class to suit 2S)'),
    ]
    g.append(('Tank vent solenoid (VBAT, PWM-capable, SAFE-allowed, watchdog-gated)', vent))
    g.append(('v2.4 MV switch + P_mid ladder on pin 23 (R0/R1/R2 in the J508 mating backshell; calc/hbleed_provision_v1.py)', [
        CONN('J508', 3, 'MV_LADDER', ['MV_LADDER_RAW', 'GND', 'GND'], 'GH3',
             'MV switch ladder: pin 1 node, pins 2-3 return (R0 82.5k EOL, R1 9.53k + OPEN sw, R2 17.8k + CLOSED sw in the backshell)'),
        R('R570', '10k', 'MV_LADDER_RAW', '+3V3', horiz=False, spec='DESIGN ladder top, 0.1 % / 1 % thin film (ratiometric to the ADC ref)'),
        R('R571', '1k', 'MV_LADDER_RAW', 'MV_LADDER', spec='DESIGN pin protection'),
        C('C570', '100nF/50V X7R', 'MV_LADDER', 'GND'),
        R('R572', '33.2k', 'MV_LADDER_RAW', 'PMID_FET_D', spec='DESIGN ladder R3 (P_mid high), 1 % thin film'),
        NFET('Q570', '2N7002', '2N7002', 'PMID_CMP', 'PMID_FET_D', 'GND', fn='P_mid ladder switch'),
    ]))
    g.append(('v2.4 P_mid comparator (between bleed V1 and V2): 170BG on J511 -> LMV331, rise 9.86 / fall 8.86 bar g', [
        CONN('J511', 3, 'P_MID', ['+5V_SNS', 'P_MID_SIG', 'GND'], 'GH3', 'P_mid transducer TE M3234 170BG class (fixed-side tee)'),
        R('R573', '4.75k', 'P_MID_SIG', 'PMID_INP', spec='DESIGN hysteresis input resistor'),
        R('R574', '1M', 'PMID_CMP', 'PMID_INP', spec='DESIGN hysteresis feedback (1.0 bar)'),
        R('R575', '10k', 'PMID_CMP', '+5V_SNS', horiz=False, spec='DESIGN open-collector pull-up (high = P_mid high)'),
        R('R576', '10.2k', '+5V_SNS', 'PMID_REF', spec='DESIGN ratiometric reference 0.7286 V'),
        R('R577', '1.74k', 'PMID_REF', 'GND', horiz=False),
        R('R578', '100k', 'P_MID_SIG', 'GND', horiz=False, spec='DESIGN unplugged transducer reads LOW: pad BIT step S2 fails -> BLEED_FAULT'),
        C('C571', '100nF/50V X7R', '+5V_SNS', 'GND'), C('C572', '100nF/50V X7R', 'PMID_REF', 'GND'),
        C('C573', '10nF/50V X7R', 'PMID_INP', 'GND'),
        P('U570', 'Comparator', 'LMV331', 'LMV331IDBVR', {1: 'PMID_INP', 2: 'GND', 3: 'PMID_REF', 4: 'PMID_CMP', 5: '+5V_SNS'}, FP['SOT23-5'],
          Spec='DATASHEET SLCS136V (as U330): open collector, VICR -0.1..4.2 V at 5 V', MPN='LMV331IDBVR', Function='P_mid comparator'),
    ]))
    g.append(('v2.5 hardware purge window (LEAD CHANGELOG 166 (3)): PURGE_WIN = FC PURGE_EN AND one-shot 3.05-3.24 s; V1 = pin 15 AND '
              'PURGE_WIN (U574), V2 = pin 24 AND PURGE_WIN (U575); window chain on +3V3', [
        CONN('J512', 2, 'PURGE_EN', ['PURGE_EN_IN', 'GND'], 'GH2',
             'FC discrete PURGE_EN (1 signal, 2 GND); FC drive level 3.3 or 5 V TO-VERIFY (ICD); open wire = no window'),
        P('D592', 'Diode', 'ESD9B5.0ST5G', 'ESD9B5.0ST5G', {1: 'PURGE_EN_IN', 2: 'GND'}, FP['SOD923'], small=True,
          Spec='5 V bidirectional ESD; pinout per KiCad lib', Function='PURGE_EN ESD'),
        R('R592', '1k', 'PURGE_EN_IN', 'PURGE_EN_F', spec='DESIGN series protection (harness)'),
        R('R593', '100k', 'PURGE_EN_F', 'GND', horiz=False, spec='DESIGN open wire / FC unpowered = window closed'),
        C('C575', '1nF/50V C0G', 'PURGE_EN_F', 'GND', spec='DESIGN 1 us EMI filter (TRIG needs >= 5 ns, DATASHEET LTC6993 tWIDTH)'),
        P('U571', '74xGxx', '74LVC1G17', 'SN74LVC1G17DBVR', {1: None, 2: 'PURGE_EN_F', 3: 'GND', 4: 'PURGE_EN_B', 5: '+3V3'}, FP['SOT23-5'],
          Spec='Schmitt buffer, 5 V tolerant input on 3.3 V (3.3 or 5 V FC level); pinout per KiCad lib (TI DBV)', MPN='SN74LVC1G17DBVR',
          Function='PURGE_EN input buffer'),
        P('U572', 'Timer', 'LTC6993xS6-1', 'LTC6993IS6-1', {1: 'PURGE_EN_B', 2: 'GND', 3: 'OS_SET', 4: 'OS_DIV', 5: '+3V3', 6: 'PURGE_OS'},
          'Package_TO_SOT_SMD:TSOT-23-6',
          Spec='DATASHEET LTC6993 Rev F: -1 = rising edge, NON-retriggerable; tOUT = NDIV x RSET/50k x 1 us; NDIV >= 512 error 1.7 % typ, '
               '2.3 % / 3.0 % max; OUT held low in start-up (500 tMASTER ~ 0.75 ms), POL 0 stays low; I grade -40..85 C',
          MPN='LTC6993IS6-1#TRMPBF', Function='purge window one-shot'),
        R('R594', '75.0k 0.1%', 'OS_SET', 'GND', horiz=False, spec='DERIVED tOUT = 2097152 x 75.0k/50k x 1 us = 3.146 s (RSET range 50k-800k)'),
        R('R595', '1.00M 1%', '+3V3', 'OS_DIV', spec='DATASHEET Table 1 DIVCODE 7 R1 (VDIV/V+ 0.46875 +/-0.015)'),
        R('R596', '887k 1%', 'OS_DIV', 'GND', horiz=False, spec='DATASHEET Table 1 DIVCODE 7 R2: NDIV 2^21, POL 0'),
        C('C576', '100nF/50V X7R', '+3V3', 'GND', spec='U572 bypass'),
        P('U573', '74xGxx', '74LVC1G08', 'SN74LVC1G08DBVR', {1: 'PURGE_EN_B', 2: 'PURGE_OS', 3: 'GND', 4: 'PURGE_WIN', 5: '+3V3'},
          FP['SOT23-5'], Spec='2-input AND, pinout per KiCad lib (as U306)', MPN='SN74LVC1G08DBVR',
          Function='PURGE_WIN = PURGE_EN AND one-shot'),
        C('C577', '100nF/50V X7R', '+3V3', 'GND', spec='U571/U573 bypass'),
        P('U574', '74xGxx', '74LVC1G08', 'SN74LVC1G08DBVR', {1: 'HTR_PERMIT_CMD', 2: 'PURGE_WIN', 3: 'GND', 4: 'BLEED_A_GATED', 5: '+3V3'},
          FP['SOT23-5'], Spec='V1 gate AND (own IC); output LVC 3.3 V into AHCT (VIH 2.0 V)', MPN='SN74LVC1G08DBVR',
          Function='bleed V1 = pin 15 AND PURGE_WIN'),
        P('U575', '74xGxx', '74LVC1G08', 'SN74LVC1G08DBVR', {1: 'BLEED_B_CMD', 2: 'PURGE_WIN', 3: 'GND', 4: 'BLEED_B_GATED', 5: '+3V3'},
          FP['SOT23-5'], Spec='V2 gate AND (own IC, not shared with V1)', MPN='SN74LVC1G08DBVR',
          Function='bleed V2 = pin 24 AND PURGE_WIN'),
        C('C578', '100nF/50V X7R', '+3V3', 'GND', spec='U574/U575 bypass'),
        TP('TP570', 'PURGE_WIN'), TP('TP571', 'PURGE_OS'),
    ]))
    g.append(('head-end bleed valves V1 / V2 (NC, in series, fixed side; +12V_ARM low-side; V2 buffer U307 separate from U304; v2.5 inputs gated by U574/U575)', [
        P('U307', '74xGxx', '74AHCT1G125', 'SN74AHCT1G125DBVR', {1: 'OE_ARM_N', 2: 'BLEED_B_GATED', 3: 'GND', 4: 'BLEED_B_G', 5: '+5V_ARM'},
          FP['SOT23-5'], Spec='DATASHEET-class AHCT: TTL inputs (3.3 V MCU OK), /OE = watchdog as U304', MPN='SN74AHCT1G125DBVR',
          Function='ARM-gated V2 gate buffer'),
        C('C574', '100nF/50V X7R', '+5V_ARM', 'GND'),
        R('R579', '100k', 'BLEED_B_CMD', 'GND', horiz=False, spec='DESIGN defined input in reset'),
    ] + solenoid_channel('BLA', 580, 'BLEED_A_G', '+12V_ARM', 'J509', 'bleed V1 (upstream, T4)')
      + solenoid_channel('BLB', 590, 'BLEED_B_G', '+12V_ARM', 'J510', 'bleed V2 (downstream)')))
    return g


def sheet_sensors():
    g = []
    adc_nets = {1: '+3V3A', 2: 'GND', 3: 'PC_AIN', 4: 'GND', 6: 'PFEED_AIN', 5: 'GND', 7: 'PTANK_AIN', 8: 'GND',
                10: 'LC_AINP', 9: 'LC_AINN', 20: '+3V3', 12: 'ADC1_CS', 14: 'SCK0', 16: 'MOSI0', 15: 'ADC_DOUT',
                13: 'ADC_DRDY', 11: 'ADC_SYNC_N', 17: 'ADC_CLK', 18: 'ADC_CAP', 19: 'GND'}
    g.append(('24-bit ADC1 ADS131M04 (4 kSPS, decimated to 1 kHz in firmware), 8.192 MHz clock shared with ADC2', [
        P('U601', None, 'ADS131M04_PW', 'ADS131M04IPWR', adc_nets, FP['TSSOP20'],
          Spec='DATASHEET SBAS890: +/-1.2 V/gain FS, 1.2 V internal ref, CLKIN 8.192 MHz -> 4 kSPS at OSR 1024',
          Function='Pc / feed / tank / load-cell ADC'),
        C('C601', '1uF/16V X7R', '+3V3A', 'GND'), C('C602', '100nF/50V X7R', '+3V3A', 'GND'),
        C('C603', '1uF/16V X7R', '+3V3', 'GND'), C('C604', '100nF/50V X7R', '+3V3', 'GND'),
        C('C605', '220nF/16V X7R', 'ADC_CAP', 'GND', spec='DATASHEET SBAS890 CAP pin 220 nF'),
        R('R601', '10k', 'ADC_SYNC_N', '+3V3', horiz=False, spec='DESIGN: reset by SPI RESET command'),
        R('R602', '33', 'ADC_DOUT', 'MISO0', spec='DESIGN shared-MISO series resistor'),
        P('Y601', 'Oscillator', 'ASE-xxxMHz', '8.192MHz', {1: '+3V3', 2: 'GND', 3: 'ADC_CLK_RAW', 4: '+3V3'}, FP['OSC'],
          Spec='3.3 V CMOS oscillator, Abracon ASE series (orderable code TO-CONFIRM)', Function='ADC clock'),
        C('C606', '100nF/50V X7R', '+3V3', 'GND'),
        R('R603', '33', 'ADC_CLK_RAW', 'ADC_CLK'),
    ]))
    pres = []
    for i, (tag, ref0, conn, fn) in enumerate([('PC', 610, 'J601', 'Pc chamber pressure (TE M3234-000005-070BG 0-70 bar g, OI-6; fixed side on the 1/8 in sense line)'),
                                                ('PFEED', 620, 'J602', 'injector feed pressure (TE M3200 170BG 0-170 bar g, LEAD 2026-10-13; gimballed side)'),
                                                ('PTANK', 630, 'J603', 'tank pressure (TE M3200 170BG 0-170 bar g, LEAD 2026-10-13)')]):
        pres += [
            CONN(conn, 3, tag + '_XDCR', ['+5V_SNS', tag + '_SIG', 'GND'], 'GH3', fn + ' (1 +5V_SNS, 2 signal, 3 GND)'),
            R('R%d' % ref0, '12.7k 0.1%', tag + '_SIG', tag + '_AIN',
              spec='DERIVED divider 4.02/(12.7+4.02) = 0.240: 4.5 V -> 1.082 V, 5.0 V -> 1.202 V (FS 1.2 V)'),
            R('R%d' % (ref0 + 1), '4.02k 0.1%', tag + '_AIN', 'GND', horiz=False),
            C('C%d' % ref0, '22nF/50V C0G', tag + '_AIN', 'GND',
              spec='DERIVED anti-alias: 1/(2 pi 3.05k 22n) = 2.4 kHz; ADC sinc3 + 4:1 average + 120 Hz IIR follow'),
        ]
    pres += [
        P('U602', 'Power_Protection', 'SRV05-4', 'SRV05-4', {1: 'PC_SIG', 3: 'PFEED_SIG', 4: 'PTANK_SIG', 6: 'NTC_EXT', 5: '+5V_SNS', 2: 'GND'},
          FP['SOT23-6'], Spec='ESD array; pinout per KiCad lib', Function='transducer/NTC ESD'),
        R('R640', '10k 0.1%', '+5V_SNS', 'V5SNS_SENSE', horiz=False), R('R641', '10k 0.1%', 'V5SNS_SENSE', 'GND', horiz=False),
        C('C640', '100nF/50V X7R', 'V5SNS_SENSE', 'GND'),
    ]
    g.append(('Pressure transducers (0.5-4.5 V ratiometric on +5V_SNS): divider + anti-alias RC', pres))
    g.append(('Load cell (test stand, ADC CH3 PGA 64-128) with 2.5 V precision excitation', [
        CONN('J604', 5, 'LOAD_CELL', ['+2V5_EXC', 'GND', 'LC_SIGP', 'LC_SIGN', 'GND'], 'GH5',
             'load cell bridge (1 EXC+, 2 EXC-, 3 SIG+, 4 SIG-, 5 shield); empty in flight'),
        P('U603', 'Reference_Voltage', 'ADR4525', 'ADR4525BRZ', {2: '+5V', 4: 'GND', 6: '+2V5_EXC'}, FP['SOIC8'],
          Spec='2.5 V reference, +/-10 mA class; 350 ohm bridge draws 7.1 mA; pinout per KiCad lib', Function='bridge excitation'),
        C('C650', '1uF/16V X7R', '+5V', 'GND'), C('C651', '1uF/16V X7R', '+2V5_EXC', 'GND'),
        R('R650', '1k 0.1%', 'LC_SIGP', 'LC_AINP'), R('R651', '1k 0.1%', 'LC_SIGN', 'LC_AINN'),
        C('C652', '100nF/50V C0G', 'LC_AINP', 'LC_AINN', 'C1206', spec='DERIVED differential fc = 1/(2 pi 2k 100n) = 0.8 kHz'),
        C('C653', '10nF/50V C0G', 'LC_AINP', 'GND'), C('C654', '10nF/50V C0G', 'LC_AINN', 'GND'),
        R('R652', '1M', 'LC_SIGP', 'GND', horiz=False, spec='DESIGN defined reading with no load cell'),
        R('R653', '1M', 'LC_SIGN', 'GND', horiz=False),
    ]))
    for k, (cs, fn) in enumerate([('TC1_CS', 'case forward'), ('TC2_CS', 'case aft'), ('TC3_CS', 'nozzle holder')]):
        n = k + 1
        b = 660 + 10 * k
        g.append(('Thermocouple %d (%s): MAX31856, K type, 100 ohm + 100 nF + 10 nF filter (Maxim 19-7534 Fig. 8)' % (n, fn), [
            P('U%d' % (604 + k), 'Sensor_Temperature', 'MAX31856', 'MAX31856MUD+',
              {1: 'GND', 2: 'TC%d_N' % n, 3: 'TC%d_N' % n, 4: 'TC%d_P' % n, 5: '+3V3', 7: None, 8: '+3V3', 9: cs, 10: 'SCK0',
               11: 'TC%d_SDO' % n, 12: 'MOSI0', 13: None, 14: 'GND'}, FP['TSSOP14'],
              Spec='DATASHEET 19-7534: BIAS to T-, SPI CPHA=1 <= 5 MHz, ~10 S/s auto mode, SDO high-Z when CS high',
              Function='TC%d %s' % (n, fn)),
            C('C%d' % b, '100nF/50V X7R', '+3V3', 'GND'),
            R('R%d' % b, '100', 'TC%d_P_EXT' % n, 'TC%d_P' % n), R('R%d' % (b + 1), '100', 'TC%d_N_EXT' % n, 'TC%d_N' % n),
            C('C%d' % (b + 1), '100nF/50V C0G', 'TC%d_P' % n, 'TC%d_N' % n, 'C1206', horiz=True),
            C('C%d' % (b + 2), '10nF/50V C0G', 'TC%d_P' % n, 'GND'), C('C%d' % (b + 3), '10nF/50V C0G', 'TC%d_N' % n, 'GND'),
            R('R%d' % (b + 2), '33', 'TC%d_SDO' % n, 'MISO0'),
            CONN('J%d' % (605 + k), 2, 'TC%d_K' % n, ['TC%d_P_EXT' % n, 'TC%d_N_EXT' % n], 'TB2',
                 'K thermocouple %s (screw terminal next to U%d for isothermal cold junction)' % (fn, 604 + k)),
        ]))
    g.append(('1-Wire DS18B20 bus (tank wall #1/#2, bay #3) and pintle-servo bracket NTC', [
        CONN('J608', 3, 'ONEWIRE_TTANK', ['+3V3', 'ONEWIRE_EXT', 'GND'], 'GH3', '1-Wire DS18B20 #1/#2 tank wall'),
        CONN('J614', 3, 'ONEWIRE_BAY', ['+3V3', 'ONEWIRE_EXT', 'GND'], 'GH3',
             '1-Wire DS18B20 #3 bay temperature at the TVC servo bracket (v2.3; LEAD 2026-10-13 bay ARM inhibit), same bus as J608'),
        R('R690', '4.7k', 'ONEWIRE', '+3V3', horiz=False), R('R691', '100', 'ONEWIRE', 'ONEWIRE_EXT'),
        P('D690', 'Diode', 'ESD9B3.3ST5G', 'ESD9B3.3ST5G', {1: 'ONEWIRE_EXT', 2: 'GND'}, FP['SOD923'], small=True,
          Spec='3.3 V bidirectional ESD; pinout per KiCad lib', Function='1-Wire ESD'),
        CONN('J609', 2, 'NTC_SERVO', ['NTC_EXT', 'GND'], 'GH2', 'NTC 10k B3950 on pintle-servo bracket'),
        R('R692', '10k 0.1%', '+3V3', 'NTC_EXT', horiz=False, spec='ratiometric to Teensy ADC reference'),
        R('R693', '1k', 'NTC_EXT', 'NTC_SERVO'), C('C690', '100nF/50V X7R', 'NTC_SERVO', 'GND'),
    ]))
    # v2.3: harness straps and GSE interfaces (firmware v2.8 mode strap; firmware v2.3 heater permit)
    g.append(('Mode strap J620 (v2.3; firmware v2.8): resistor code on Teensy A3 (pin 17), ratiometric to +3V3', [
        CONN('J620', 3, 'MODE_STRAP', ['MODE_A', 'MODE_B', 'GND'], 'GH3',
             'mode strap: FLIGHT harness links pin 2 (MODE_B) to pin 3; STAND harness links pin 1 (MODE_A) to pin 3; open or both = INVALID'),
        R('R694', '10.0k 1%', '+3V3', 'MODE_SENSE', horiz=False,
          spec='DERIVED levels: open 3.30 V, FLIGHT (B low) 2.27 V, STAND (A low) 1.65 V, both low 1.35 V; HAL thresholds 2.79 / 1.96 / 1.50 V '
               '(calc/ecu_v2p3_values_v1.py)'),
        R('R695', '10.0k 1%', 'MODE_SENSE', 'MODE_A', spec='DESIGN STAND leg'),
        R('R696', '22.1k 1%', 'MODE_SENSE', 'MODE_B', spec='DESIGN FLIGHT leg'),
        C('C691', '100nF/50V X7R', 'MODE_SENSE', 'GND', spec='DERIVED tau <= 1.0 ms (static input)'),
        P('D691', 'Diode', 'ESD9B3.3ST5G', 'ESD9B3.3ST5G', {1: 'MODE_A', 2: 'GND'}, FP['SOD923'], small=True,
          Spec='3.3 V bidirectional ESD; pinout per KiCad lib', Function='strap ESD'),
        P('D692', 'Diode', 'ESD9B3.3ST5G', 'ESD9B3.3ST5G', {1: 'MODE_B', 2: 'GND'}, FP['SOD923'], small=True,
          Spec='3.3 V bidirectional ESD; pinout per KiCad lib', Function='strap ESD'),
    ]))
    g.append(('GSE tank-heater interlock J616 HTR_ILK (v2.3, LEAD 2026-10-12 condition (b)): coil loop closed only with the firmware '
              'permit (U305, watchdog OK) AND no arming plug AND ARM bus off', [
        CONN('J616', 2, 'HTR_ILK', ['HTR_ILK_SW', 'GND'], 'MF2',
             'GSE heater contactor coil loop: GSE coil supply (<= 28 V DC, <= 1.0 A; flyback diode in the GSE) -> coil -> pin 1; '
             'pin 2 = return (GSE 0 V tied to ECU GND)'),
        NFET('Q616', 'DMN6075S', 'DMN6075S-7', 'HTR_G', 'HTR_ILK_SW', 'GND',
             spec='DATASHEET DS37023 Rev6-2: 60 V, 2.0 A, RDS(on) <= 120 mOhm @4.5 V', fn='heater interlock switch'),
        P('D616', 'Diode', 'SMAJ33A', 'SMAJ33A', {1: 'HTR_ILK_SW', 2: 'GND'}, FP['SMA'], small=True,
          Spec='DESIGN coil-flyback clamp: standoff 33 V above a 28 V GSE coil supply, below the 60 V switch rating (clamp voltage '
               'TO-CONFIRM on the SMAJ33A datasheet)', Function='interlock clamp'),
        R('R654', '4.7k', 'HTR_PERMIT_DRV', 'HTR_G', spec='DESIGN lets Q617/Q618 override the U305 drive (~1 mA)'),
        R('R655', '100k', 'HTR_G', 'GND', horiz=False, spec='DESIGN open when U305 is high-Z (watchdog) or unpowered'),
        NFET('Q617', '2N7002', '2N7002', 'HTR_INH_PLUG', 'HTR_G', 'GND', fn='heater inhibit: arming plug present'),
        R('R656', '47k', 'ARM_PLUG', 'HTR_INH_PLUG', spec='DERIVED VGS = VBAT x 100/147 = 4.5-5.7 V at 6.6-8.4 V'),
        R('R657', '100k', 'HTR_INH_PLUG', 'GND', horiz=False),
        NFET('Q618', '2N7002', '2N7002', 'HTR_INH_BUS', 'HTR_G', 'GND', fn='heater inhibit: ARM bus on'),
        R('R658', '47k', 'ARM_BUS', 'HTR_INH_BUS'),
        R('R659', '100k', 'HTR_INH_BUS', 'GND', horiz=False),
        TP('TP616', 'HTR_G'),
    ]))
    for k, (ax, cs, fn) in enumerate([('A', 'ENC_A_CS', 'gimbal axis A'), ('B', 'ENC_B_CS', 'gimbal axis B'), ('P', 'ENC_P_CS', 'pintle crank')]):
        b = 700 + 10 * k
        e = 'ENC%s_' % ax
        g.append(('Encoder %s: AS5048A (3.3 V mode) over shielded cable, 47 ohm series, ESD' % fn, [
            CONN('J%d' % (610 + k), 6, 'ENC_' + ax, ['+3V3_ENC', 'GND', e + 'CS_EXT', e + 'SCK_EXT', e + 'MOSI_EXT', e + 'MISO_EXT'], 'GH6',
                 'AS5048A %s (1 3V3, 2 GND, 3 CSn, 4 CLK, 5 MOSI, 6 MISO)' % fn),
            R('R%d' % b, '47', cs, e + 'CS_EXT'), R('R%d' % (b + 1), '47', 'SCK1', e + 'SCK_EXT'),
            R('R%d' % (b + 2), '47', 'MOSI1', e + 'MOSI_EXT'), R('R%d' % (b + 3), '47', e + 'MISO_EXT', 'MISO1'),
            P('U%d' % (610 + k), 'Power_Protection', 'SRV05-4', 'SRV05-4',
              {1: e + 'CS_EXT', 3: e + 'SCK_EXT', 4: e + 'MOSI_EXT', 6: e + 'MISO_EXT', 5: '+3V3_ENC', 2: 'GND'}, FP['SOT23-6'],
              Spec='ESD array; pinout per KiCad lib', Function='encoder ESD'),
            C('C%d' % b, '1uF/16V X7R', '+3V3_ENC', 'GND'),
        ]))
    return g


def sheet_pintle_rail():
    """v2.3: pintle servo rail (LEAD 2026-10-13 adoption of calc/pintle_rail_v3.py) - values derived in calc/ecu_v2p3_values_v1.py."""
    g = []
    tps = {3: 'ARM_BUS', 4: 'PR_EN', 15: 'PR_MODE', 7: 'GND', 8: 'PR_FSW', 17: 'PR_ILIM', 18: 'PR_COMP', 16: None,
           10: 'GND', 9: 'GND', 24: 'GND',
           2: 'PR_DR1H', 22: 'PR_BOOT1', 23: 'PR_SW1', 1: 'PR_DR1L', 21: 'PR_SW2', 25: 'PR_SW2', 20: 'PR_BOOT2',
           26: 'PR_VOUT', 11: 'PR_VOUT', 12: 'PR_VOUT', 13: 'PREG', 14: 'PR_FB', 5: 'PR_PG', 6: 'PR_CC', 19: 'PR_VCC'}
    g.append(('Pintle servo rail 7.49 V: TPS552882 four-switch buck-boost (boost leg integrated, buck leg = external Q801/Q802), '
              'FPWM 400 kHz, output current limit 4.0-4.33 A on R807', [
        P('U801', None, 'TPS552882_RPM', 'TPS552882RPMR', tps, FP['TPS_RPM'],
          Spec='DATASHEET TI TPS552882 (pin functions, VREF 1.188-1.212 V, VSNS 48-52 mV, VCC 5.0-5.4 V, GEA 190 uA/V typ); '
               'footprint is a PLACEHOLDER (RPM0026A land pattern TO-DRAW)', MPN='TPS552882RPMR', Function='pintle rail buck-boost'),
        P('Q801', 'Transistor_FET', 'CSD17578Q5A', 'CSD17578Q5A', {1: 'PR_SW1', 2: 'PR_SW1', 3: 'PR_SW1', 4: 'PR_DR1H', 5: 'ARM_BUS'},
          FP['TDSON8'], small=True,
          Spec='DATASHEET TI SLPS526: 30 V, RDS(on) <= 9.3 mOhm @4.5 V, Qg 7.9 nC typ, VGS(th) 1.1-1.9 V; driven from BOOT1 '
               '(VCC 5.2 V typ) - candidate, losses in calc/ecu_v2p3_values_v1.py', MPN='CSD17578Q5A', Function='buck leg high side'),
        P('Q802', 'Transistor_FET', 'CSD17578Q5A', 'CSD17578Q5A', {1: 'GND', 2: 'GND', 3: 'GND', 4: 'PR_DR1L', 5: 'PR_SW1'},
          FP['TDSON8'], small=True, Spec='DATASHEET TI SLPS526 (as Q801); driven from VCC', MPN='CSD17578Q5A',
          Function='buck leg low side'),
        P('L801', 'Device', 'L', '4.7uH', {1: 'PR_SW1', 2: 'PR_SW2'}, FP['L_XAL1010'], rot=90, small=True,
          Spec='DATASHEET TPS552882 application: Coilcraft XAL1010-472ME 4.7 uH, 10 mOhm max, 25.4 A sat (needs Isat >= 8 A + '
               'ripple); a 6 x 6 mm part is the likely size fit, TO-CONFIRM', MPN='Coilcraft XAL1010-472ME', Function='buck-boost inductor'),
        C('C801', '10uF/25V X7R', 'ARM_BUS', 'GND', 'C1210', spec='DATASHEET ~20 uF effective input (start point)'),
        C('C802', '10uF/25V X7R', 'ARM_BUS', 'GND', 'C1210'), C('C803', '10uF/25V X7R', 'ARM_BUS', 'GND', 'C1210'),
        C('C804', '10uF/25V X7R', 'ARM_BUS', 'GND', 'C1210'),
        C('C805', '22uF/16V X7R', 'PR_VOUT', 'GND', 'C1210', spec='pintle_rail_v2/v3 output ceramics 4 x 22 uF'),
        C('C806', '22uF/16V X7R', 'PR_VOUT', 'GND', 'C1210'), C('C807', '22uF/16V X7R', 'PR_VOUT', 'GND', 'C1210'),
        C('C808', '22uF/16V X7R', 'PR_VOUT', 'GND', 'C1210'),
        C('C809', '100nF/50V X7R', 'PR_BOOT1', 'PR_SW1', horiz=True, spec='DATASHEET 0.1 uF BOOT1-SW1'),
        C('C810', '100nF/50V X7R', 'PR_BOOT2', 'PR_SW2', horiz=True, spec='DATASHEET 0.1 uF BOOT2-SW2'),
        C('C811', '10uF/16V X7R', 'PR_VCC', 'GND', 'C0805', spec='DATASHEET VCC needs > 4.7 uF ceramic (10 uF for DC-bias derating)'),
        R('R801', '49.9k 1%', 'PR_FSW', 'GND', horiz=False, spec='DATASHEET 49.9 kOhm = 400 kHz'),
        R('R802', '41.2k 1%', 'PR_ILIM', 'GND', horiz=False,
          spec='DERIVED pintle_rail_v2: average inductor limit ~8 A (Eq. 5 extraction garbled: TO-CONFIRM on the PDF)'),
        R('R803', '0R', 'PR_MODE', 'GND', horiz=False, spec='DATASHEET MODE resistor table: 0 Ohm = internal VCC, forced PWM'),
        R('R804', '26.7k 1%', 'ARM_BUS', 'PR_EN', horiz=False,
          spec='DERIVED EN/UVLO 1.23 V x (1 + 26.7/10.0) = 4.51 V rising (4.40-4.62 V); 5 uA hysteresis current -> ~0.13 V'),
        R('R805', '10.0k 1%', 'PR_EN', 'GND', horiz=False),
        R('R806', '28.0k 1%', 'PR_COMP', 'PR_COMP_RC', spec='DERIVED Eq. 24 (f_c 5 kHz at 6.0 V in / 4.33 A, C_eff 396 uF): 28.06 kOhm'),
        C('C812', '12nF/50V C0G', 'PR_COMP_RC', 'GND', spec='DERIVED Eq. 25: 12.2 nF'),
        C('C813', '100pF/50V C0G', 'PR_COMP', 'GND', spec='DERIVED Eq. 26 with 7 mOhm polymer ESR: 99 pF'),
        P('R807', 'Device', 'R', '12m 1% 1W', {1: 'PR_VOUT', 2: 'PREG'}, FP['R2512'], rot=90, small=True,
          Spec='DERIVED output current limit VSNS 48-52 mV / 12 mOhm = 4.0-4.33 A (pintle_rail_v2); Kelvin sense to ISP/ISN',
          Function='output current sense'),
        R('R808', '24.9k 0.1% 10ppm', 'PREG', 'PR_FB', horiz=False,
          spec='LEAD 2026-10-13 adopted divider B: 1.2 V x (1 + 24.9/4.75) = 7.49 V typ, static worst 7.62 V (pintle_rail_v3)'),
        R('R809', '4.75k 0.1% 10ppm', 'PR_FB', 'GND', horiz=False),
        R('R810', '100k', 'PR_PG', 'PR_VCC', horiz=False, spec='open-drain pull-up'),
        R('R811', '100k', 'PR_CC', 'PR_VCC', horiz=False, spec='pull-up (CC output type not stated beyond O: harmless if push-pull)'),
        TP('TP801', 'PR_PG'), TP('TP802', 'PR_CC'), TP('TP803', 'PR_SW1'),
    ]))
    g.append(('OV/UV disconnect LTC4365 (LEAD 2026-10-13): OV 8.20 V (8.06-8.34 V), filter tau 9.4 us; /FAULT -> PRAIL_OK -> U306 '
              '(MV latch released in hardware); servo-side rail PRAIL to J403 and ADC2 CH1', [
        P('U802', 'Power_Management', 'LTC4365xTS8', 'LTC4365HTS8',
          {1: 'PREG', 2: 'PR_UV', 3: 'PR_OV', 4: 'GND', 5: 'PR_SHDN_N', 6: 'PRAIL_OK', 7: 'PRAIL', 8: 'PR_GATE'}, FP['TSOT23-8'],
          Spec='DATASHEET ADI LTC4365 Rev B (as read for pintle_rail_v3): OV 492.5-507.5 mV H grade, fault 2 us, gate off 4 us, '
               'retry 26-49 ms; UV threshold ASSUMED the same 0.5 V (TO-CONFIRM, analog.com blocked)', MPN='LTC4365HTS8 (order suffix TO-CONFIRM)',
          Function='pintle rail OV/UV disconnect'),
        P('Q803', 'Transistor_FET', 'CSD17578Q5A', 'CSD17578Q5A', {1: 'PRAIL', 2: 'PRAIL', 3: 'PRAIL', 4: 'PR_GATE', 5: 'PREG'},
          FP['TDSON8'], small=True,
          Spec='DATASHEET TI SLPS526: RDS(on) <= 9.3 mOhm @4.5 V; LTC4365 gate drive above VOUT is 3.0-4.2 V at VIN 5 V (DATASHEET) and '
               'not read at 7.5 V: enhancement TO-CONFIRM (B-PWR-1 measures the drop at 4 A)', MPN='CSD17578Q5A',
          Function='OV disconnect switch'),
        R('R812', '154k 0.1%', 'PREG', 'PR_OV', horiz=False, spec='DESIGN pintle_rail_v3: 0.5 V x (1 + 154/10.0) = 8.20 V'),
        R('R813', '10.0k 0.1%', 'PR_OV', 'GND', horiz=False),
        C('C814', '1nF/50V C0G', 'PR_OV', 'GND', spec='DESIGN pintle_rail_ovtrip_v1: tau = 9.39k x 1.0 nF = 9.4 us; margin 0.134 V '
                                                     'with allowances, fail-high peak 8.69 V for <= 29 us'),
        R('R814', '90.9k 1%', 'PREG', 'PR_UV', horiz=False, spec='DERIVED UV 0.5 V x (1 + 90.9/10.0) = 5.05 V (firmware PRAIL lost < 5.5 V)'),
        R('R815', '10.0k 1%', 'PR_UV', 'GND', horiz=False),
        R('R816', '100k', 'PREG', 'PR_SHDN_N', horiz=False, spec='DESIGN disconnect always enabled'),
        R('R817', '10k', 'PRAIL_OK', '+5V_ARM', horiz=False, spec='DESIGN open-drain pull-up to the U306 logic rail'),
        CP('C815', '220uF/16V polymer', 'PRAIL', 'GND', 'CP8',
           spec='LEAD 2026-10-13 (b): 2 x 220 uF polymer at the servo connector J403 (layout), ESR ~7 mOhm pair ASSUMED in pintle_rail_ovtrip_v1',
           fn='pintle servo reservoir'),
        CP('C816', '220uF/16V polymer', 'PRAIL', 'GND', 'CP8', fn='pintle servo reservoir'),
        TP('TP804', 'PREG'), TP('TP805', 'PRAIL'), TP('TP806', 'PRAIL_OK'),
    ]))
    g.append(('Pintle rail current sense (firmware v2.6 stall current path): INA181A2 x50 across R807', [
        P('U803', 'Amplifier_Current', 'INA181', 'INA181A2IDBVR', {1: 'IPINT_OUT', 2: 'GND', 3: 'PR_VOUT', 4: 'PREG', 5: 'GND', 6: '+5V'},
          FP['SOT23-6'], Spec='gain 50 V/V (A2): 0.60 V/A on 12 mOhm; CM -0.2..26 V; pinout per KiCad lib', MPN='INA181A2IDBVR',
          Function='pintle rail current amplifier'),
        C('C817', '100nF/50V X7R', '+5V', 'GND'),
    ]))
    return g


def sheet_sensors_b():
    """v2.3: ADC2 (firmware v2.7 channels) and thermocouples TC4-TC6 (firmware v2.7/v2.8)."""
    g = []
    adc2 = {1: '+3V3A', 2: 'GND', 3: 'PTORCH_AIN', 4: 'GND', 6: 'PRAIL_AIN', 5: 'GND', 7: 'IPINT_AIN', 8: 'GND',
            10: 'PHOTO_AIN', 9: 'GND', 20: '+3V3', 12: 'ADC2_CS', 14: 'SCK0', 16: 'MOSI0', 15: 'ADC2_DOUT',
            13: 'ADC2_DRDY', 11: 'ADC_SYNC_N', 17: 'ADC_CLK', 18: 'ADC2_CAP', 19: 'GND'}
    g.append(('ADC2 ADS131M04 (v2.3): CH0 P_torch, CH1 PRAIL, CH2 pintle current, CH3 FA-1 photodiode head (v2.5; PREG retired to TP902); clock, SYNC and SPI0 shared with ADC1; '
              'OSR 4096 -> 1 kSPS, read once per 1 ms tick', [
        P('U901', None, 'ADS131M04_PW', 'ADS131M04IPWR', adc2, FP['TSSOP20'],
          Spec='DATASHEET SBAS890: +/-1.2 V FS at gain 1, internal 1.2 V ref; DRDY polled (TP901); no SYNC pin from the MCU: '
               'frame phase vs ADC1 arbitrary (< 1 ms)', Function='P_torch / rail / pintle-current ADC'),
        C('C901', '1uF/16V X7R', '+3V3A', 'GND'), C('C902', '100nF/50V X7R', '+3V3A', 'GND'),
        C('C903', '1uF/16V X7R', '+3V3', 'GND'), C('C904', '100nF/50V X7R', '+3V3', 'GND'),
        C('C905', '220nF/16V X7R', 'ADC2_CAP', 'GND', spec='DATASHEET SBAS890 CAP pin 220 nF'),
        R('R901', '33', 'ADC2_DOUT', 'MISO0', spec='DESIGN shared-MISO series resistor'),
        TP('TP901', 'ADC2_DRDY'),
    ]))
    g.append(('Torch chamber pressure P_torch (RC-01 flame gate, firmware v2.7): TE M3200 070BG on a standoff, Pc chain', [
        CONN('J901', 3, 'PTORCH_XDCR', ['+5V_SNS', 'PTORCH_SIG', 'GND'], 'GH3',
             'torch chamber pressure TE M3234-000005-070BG (1 +5V_SNS, 2 signal, 3 GND)'),
        R('R910', '12.7k 0.1%', 'PTORCH_SIG', 'PTORCH_AIN', spec='DERIVED as R610: divider 0.240, 4.5 V -> 1.082 V'),
        R('R911', '4.02k 0.1%', 'PTORCH_AIN', 'GND', horiz=False),
        C('C910', '22nF/50V C0G', 'PTORCH_AIN', 'GND', spec='DERIVED anti-alias 2.4 kHz (as C610)'),
        P('D910', 'Diode', 'ESD9B5.0ST5G', 'ESD9B5.0ST5G', {1: 'PTORCH_SIG', 2: 'GND'}, FP['SOD923'], small=True,
          Spec='5 V bidirectional ESD (signal 0.5-4.5 V); pinout per KiCad lib', Function='P_torch ESD'),
    ]))
    g.append(('Pintle rail sense: PRAIL (servo side, firmware loss detection < 5.5 V), rail current; PREG test point only (v2.5)', [
        R('R920', '22.6k 0.1%', 'PRAIL', 'PRAIL_AIN',
          spec='DERIVED 2.49/25.09 = 1/10.08 (1/10.15 with the 330 kOhm ADC load): 7.49 V -> 0.74 V, FS 12.1 V, 24.5 V -> 2.43 V'),
        R('R921', '2.49k 0.1%', 'PRAIL_AIN', 'GND', horiz=False),
        C('C920', '22nF/50V C0G', 'PRAIL_AIN', 'GND', spec='DERIVED 1/(2 pi 2.24k 22n) = 3.2 kHz'),
        R('R930', '12.7k 0.1%', 'IPINT_OUT', 'IPINT_AIN',
          spec='DERIVED 0.60 V/A x 0.240 = 0.144 V/A at the ADC; FS 8.3 A = INA181 swing limit, above the 4.33 A regulator limit'),
        R('R931', '4.02k 0.1%', 'IPINT_AIN', 'GND', horiz=False),
        C('C930', '22nF/50V C0G', 'IPINT_AIN', 'GND'),
        TP('TP902', 'PREG'),   # v2.5: PREG no longer read (ADC2 CH3 = photodiode head); bench diagnostic point
    ]))
    g.append(('v2.5 FA-1 flame-light head (photodiode + log transimpedance amplifier, remote head on J902) -> ADC2 CH3 (firmware v2.10 '
              'Inputs::photo_V, valid 0.02-4.80 V at the head)', [
        CONN('J902', 3, 'PHOTO_HEAD', ['+5V_SNS', 'PHOTO_SIG', 'GND'], 'GH3',
             'FA-1 photodiode head (1 +5V_SNS, 2 output 0-5 V, 3 GND); head design / part TO-SELECT (BOM row), current <= 5 mA ASSUMED'),
        R('R940', '12.7k 0.1%', 'PHOTO_SIG', 'PHOTO_AIN', spec='DERIVED as R910: 0.240, 4.80 V -> 1.154 V < 1.2 V FS'),
        R('R941', '4.02k 0.1%', 'PHOTO_AIN', 'GND', horiz=False),
        C('C940', '22nF/50V C0G', 'PHOTO_AIN', 'GND', spec='DERIVED anti-alias 2.4 kHz (as C910)'),
        R('R942', '100k', 'PHOTO_SIG', 'GND', horiz=False, spec='DESIGN open head reads ~0 V -> below kPhotoMin_V 0.02 V = invalid'),
        P('D940', 'Diode', 'ESD9B5.0ST5G', 'ESD9B5.0ST5G', {1: 'PHOTO_SIG', 2: 'GND'}, FP['SOD923'], small=True,
          Spec='5 V bidirectional ESD; pinout per KiCad lib', Function='photodiode head ESD'),
    ]))
    for k, (cs, fn, typ) in enumerate([('TC4_CS', 'bore-top / manifold (firmware v2.7, CF-3/T1 evidence)', 'K'),
                                       ('TC5_CS', 'MSS-1 inlet-block manifold state sensor (LEAD 2026-10-13)', 'T'),
                                       ('TC6_CS', 'MSS-2 NC-valve-outlet manifold state sensor (LEAD 2026-10-13)', 'T')]):
        n = k + 4
        b = 950 + 10 * k
        g.append(('Thermocouple %d (%s): MAX31856, type %s, 100 ohm + 100 nF + 10 nF filter (Maxim 19-7534 Fig. 8)' % (n, fn, typ), [
            P('U%d' % (904 + k), 'Sensor_Temperature', 'MAX31856', 'MAX31856MUD+',
              {1: 'GND', 2: 'TC%d_N' % n, 3: 'TC%d_N' % n, 4: 'TC%d_P' % n, 5: '+3V3', 7: None, 8: '+3V3', 9: cs, 10: 'SCK0',
               11: 'TC%d_SDO' % n, 12: 'MOSI0', 13: None, 14: 'GND'}, FP['TSSOP14'],
              Spec='DATASHEET 19-7534: thermocouple type set in CR1 (K/T), SPI CPHA=1 <= 5 MHz, SDO high-Z when CS high',
              Function='TC%d %s' % (n, fn)),
            C('C%d' % b, '100nF/50V X7R', '+3V3', 'GND'),
            R('R%d' % b, '100', 'TC%d_P_EXT' % n, 'TC%d_P' % n), R('R%d' % (b + 1), '100', 'TC%d_N_EXT' % n, 'TC%d_N' % n),
            C('C%d' % (b + 1), '100nF/50V C0G', 'TC%d_P' % n, 'TC%d_N' % n, 'C1206', horiz=True),
            C('C%d' % (b + 2), '10nF/50V C0G', 'TC%d_P' % n, 'GND'), C('C%d' % (b + 3), '10nF/50V C0G', 'TC%d_N' % n, 'GND'),
            R('R%d' % (b + 2), '33', 'TC%d_SDO' % n, 'MISO0'),
            CONN('J%d' % (904 + k), 2, 'TC%d_%s' % (n, typ), ['TC%d_P_EXT' % n, 'TC%d_N_EXT' % n], 'TB2',
                 'type %s thermocouple %s (screw terminal next to U%d, isothermal cold junction)' % (typ, fn, 904 + k)),
        ]))
    return g


SHEETS = [
    ('Power', 'power.kicad_sch', 'Power input, protection, rails', sheet_power),
    ('MCU_CAN', 'mcu_can.kicad_sch', 'MCU Teensy 4.1 and CAN', sheet_mcu),
    ('Safety_Arming', 'safety_arming.kicad_sch', 'Arming, watchdog, output buffers', sheet_safety),
    ('Actuators', 'actuators.kicad_sch', 'Servo actuators, TVC power switch', sheet_actuators),
    ('Igniter_Valves', 'igniter_valves.kicad_sch', '12 V boost, spark, solenoid drivers', sheet_igniter),
    ('Sensors', 'sensors.kicad_sch', 'Sensors A, encoders, strap, heater ILK', sheet_sensors),
    ('Pintle_Rail', 'pintle_rail.kicad_sch', 'Pintle rail TPS552882 + LTC4365', sheet_pintle_rail),
    ('Sensors_B', 'sensors_b.kicad_sch', 'ADC2, P_torch, rail sense, TC4-TC6', sheet_sensors_b),
]

POWER_NETS = ['GND', 'VBAT', 'VLOGIC', '+5V', '+3V3', '+3V3A', '+3V3_ENC', '+5V_SNS', '+2V5_EXC', 'ARM_BUS', '+5V_ARM',
              '+12V_ARM', 'TVC_PWR', 'PREG']
