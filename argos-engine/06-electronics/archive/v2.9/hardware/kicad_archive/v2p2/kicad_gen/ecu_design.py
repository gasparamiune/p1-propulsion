"""ARGOS engine ECU v2.2 - schematic content (parts, pins, nets), 06-electronics, 2026-10-12.
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

# Teensy 4.1 pin allocation v2.1 (pin label -> net). 42 edge I/O, all 42 used (pin 29 = OVP_OK since v2.1; no spare).
TEENSY_PINMAP = {
    '0': ('SOL3_VENT_CMD', 'out', 'FlexPWM: tank vent solenoid (VBAT, PWM hold), not ARM-gated, watchdog-gated'),
    '1': ('SOL4_ROLL_CW_CMD', 'out', 'roll RCS provision: CW thruster pair, 2 coils (12 V, ARM-gated)'),
    '2': ('TVC_A_PWM', 'out', 'FlexPWM4.2 333 Hz servo TVC-A (pitch)'),
    '3': ('TVC_B_PWM', 'out', 'FlexPWM4.2 333 Hz servo TVC-B (yaw)'),
    '4': ('PINTLE_PWM', 'out', 'FlexPWM2.0 333 Hz pintle throttle servo'),
    '5': ('MV_OPENER_PWM', 'out', 'FlexPWM2.1 333 Hz main-valve opener servo'),
    '6': ('MV_LATCH_CMD', 'out', 'main-valve holding magnet (ARM-gated)'),
    '7': ('ADC_DRDY', 'in', 'ADS131M04 data ready (4 kSPS)'),
    '8': ('ADC_CS', 'out', 'ADS131M04 chip select (SPI0)'),
    '9': ('TC1_CS', 'out', 'MAX31856 #1 CS (case forward)'),
    '10': ('TC2_CS', 'out', 'MAX31856 #2 CS (case aft)'),
    '11': ('MOSI0', 'out', 'SPI0 MOSI'),
    '12': ('MISO0', 'in', 'SPI0 MISO (ADC + 3 TC, 33 ohm per device)'),
    '13': ('SCK0', 'out', 'SPI0 SCK (on-board LED)'),
    '14': ('VBAT_SENSE', 'ain', 'A0 battery voltage /4.03'),
    '15': ('V12_SENSE', 'ain', 'A1 12 V ARM rail /5.7'),
    '16': ('IBAT_SENSE', 'ain', 'A2 battery current, INA181A1 x20 on 2 mOhm (25 A/V)'),
    '17': ('IGN_ISENSE', 'ain', 'A3 spark coil current, INA181A1 x20 on 20 mOhm (2.5 A/V)'),
    '18': ('NTC_SERVO', 'ain', 'A4 pintle-servo bracket NTC 10k'),
    '19': ('V5SNS_SENSE', 'ain', 'A5 transducer excitation /2 (ratiometric correction)'),
    '20': ('TC3_CS', 'out', 'MAX31856 #3 CS (nozzle holder)'),
    '21': ('ARM_PLUG_SENSE', 'ain', 'A7 arming-plug voltage /4.03 (upstream of ARM switch)'),
    '22': ('ARM_BUS_SENSE', 'ain', 'A8 ARM bus voltage /4.03 (proves switch closed)'),
    '23': ('MV_OPEN_SW', 'in', 'main valve OPEN microswitch (low = actuated)'),
    '24': ('MV_CLOSED_SW', 'in', 'main valve CLOSED microswitch (low = actuated)'),
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
          spec='DERIVED ratiometric threshold 29.4/266.4 x 5 V = 0.5518 V = PC_SIG 2.298 V = 31.0 bar g (calc/ovp_threshold_v1.py)'),
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
           2: 'MV_LATCH_CMD', 18: 'MV_LATCH_G', 4: 'SOL1_TORCH_OX_CMD', 16: 'SOL1_G', 6: 'SOL2_TORCH_FUEL_CMD', 14: 'SOL2_G',
           8: 'SPARK_CMD', 12: 'SPARK_DRV', 17: 'SOL4_ROLL_CW_CMD', 3: 'SOL4_G', 15: 'SOL5_ROLL_CCW_CMD', 5: 'SOL5_G',
           13: 'GND', 7: None, 11: 'GND', 9: None}, FP['TSSOP20'],
          Spec='DATASHEET SCLS228O: VIH 2.0 V (3.3 V MCU OK), inputs -0.5..7 V independent of VCC',
          Function='ARM-gated 5 V gate drive'),
        C('C310', '100nF/50V X7R', '+5V_ARM', 'GND'),
        R('R314', '100k', 'MV_LATCH_CMD', 'GND', horiz=False), R('R315', '100k', 'SOL1_TORCH_OX_CMD', 'GND', horiz=False),
        R('R316', '100k', 'SOL2_TORCH_FUEL_CMD', 'GND', horiz=False), R('R317', '100k', 'SPARK_CMD', 'GND', horiz=False),
        R('R318', '100k', 'SOL4_ROLL_CW_CMD', 'GND', horiz=False), R('R319', '100k', 'SOL5_ROLL_CCW_CMD', 'GND', horiz=False),
    ]))
    g.append(('SAFE-allowed buffer U305 SN74AHCT244 on +5V: servo PWM 3.3->5 V (always on), vent + TVC power (watchdog)', [
        P('U305', '74xx', '74AHCT244', 'SN74AHCT244PWR',
          {1: 'GND', 19: 'OE_SAFE_N', 10: 'GND', 20: '+5V',
           2: 'TVC_A_PWM', 18: 'TVC_A_SIG_B', 4: 'TVC_B_PWM', 16: 'TVC_B_SIG_B', 6: 'PINTLE_PWM', 14: 'PINTLE_SIG_B',
           8: 'MV_OPENER_PWM', 12: 'MVOP_SIG_B', 17: 'SOL3_VENT_CMD', 3: 'SOL3_G', 15: 'TVC_PWR_CMD', 5: 'TVC_PWR_DRV',
           13: 'GND', 7: None, 11: 'GND', 9: None}, FP['TSSOP20'],
          Spec='servo inputs need >= 3.5 V class pulses over cable (5 V push-pull)', Function='servo PWM / SAFE outputs'),
        C('C311', '100nF/50V X7R', '+5V', 'GND'),
        R('R320', '100k', 'TVC_A_PWM', 'GND', horiz=False), R('R321', '100k', 'TVC_B_PWM', 'GND', horiz=False),
        R('R322', '100k', 'PINTLE_PWM', 'GND', horiz=False), R('R323', '100k', 'MV_OPENER_PWM', 'GND', horiz=False),
        R('R324', '100k', 'SOL3_VENT_CMD', 'GND', horiz=False), R('R325', '100k', 'TVC_PWR_CMD', 'GND', horiz=False),
    ]))
    return g


def sheet_actuators():
    g = []
    g.append(('TVC servo power switch (watchdog-gated, soft start) and reservoirs', [
        FUSE('F401', '15A', 'VBAT', 'VBAT_TVCF', 'FUSE_MINI', mpn='Littelfuse 0297015 (ATM 15 A) + Keystone 3568', fn='TVC branch fuse'),
        P('Q401', 'Device', 'Q_PMOS_GDS', 'AOD4185', {1: 'TVC_GATE', 2: 'TVC_PWR', 3: 'VBAT_TVCF'}, FP['DPAK'], small=True,
          Spec='DATASHEET AOS Rev4.2 (see Q301)', MPN='AOD4185', Function='TVC power switch'),
        R('R401', '47k', 'TVC_GATE', 'VBAT_TVCF', horiz=False), R('R402', '4.7k', 'TVC_GATE', 'TVC_GATE_DRV'),
        C('C401', '47nF/50V X7R', 'TVC_GATE', 'TVC_PWR', horiz=True, spec='Miller soft start'),
        NFET('Q402', '2N7002', '2N7002', 'TVC_PWR_DRV', 'TVC_GATE_DRV', 'GND', fn='TVC switch driver'),
        R('R403', '100k', 'TVC_PWR_DRV', 'GND', horiz=False),
        CP('C402', '470uF/16V low-ESR', 'TVC_PWR', 'GND', 'CP10', fn='TVC servo reservoir'),
        CP('C403', '220uF/16V low-ESR', 'ARM_BUS', 'GND', 'CP8', fn='pintle/MV-opener servo reservoir'),
        TP('TP401', 'TVC_PWR'),
    ]))
    g.append(('Servo connectors (Micro-Fit 3.0: 1 signal, 2 V+, 3 GND), 220 ohm series, ESD', [
        R('R404', '220', 'TVC_A_SIG_B', 'TVC_A_SIG', spec='DESIGN series termination/current limit'),
        R('R405', '220', 'TVC_B_SIG_B', 'TVC_B_SIG'), R('R406', '220', 'PINTLE_SIG_B', 'PINTLE_SIG'),
        R('R407', '220', 'MVOP_SIG_B', 'MVOP_SIG'),
        P('U401', 'Power_Protection', 'SRV05-4', 'SRV05-4', {1: 'TVC_A_SIG', 3: 'TVC_B_SIG', 4: 'PINTLE_SIG', 6: 'MVOP_SIG', 5: '+5V', 2: 'GND'},
          FP['SOT23-6'], Spec='ESD array; pinout per KiCad lib', Function='servo signal ESD'),
        CONN('J401', 3, 'SERVO_TVC_A', ['TVC_A_SIG', 'TVC_PWR', 'GND'], 'MF3', 'servo TVC-A pitch (Savox SB-2292SG)'),
        CONN('J402', 3, 'SERVO_TVC_B', ['TVC_B_SIG', 'TVC_PWR', 'GND'], 'MF3', 'servo TVC-B yaw (Savox SB-2292SG)'),
        CONN('J403', 3, 'SERVO_PINTLE', ['PINTLE_SIG', 'ARM_BUS', 'GND'], 'MF3', 'pintle throttle servo (crosses gimbal, service loop)'),
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
        R('R501', '47k 0.1%', '+12V_ARM', 'V12_SENSE', horiz=False, spec='DERIVED 18.8 V full scale'),
        R('R502', '10k 0.1%', 'V12_SENSE', 'GND', horiz=False), C('C503', '100nF/50V X7R', 'V12_SENSE', 'GND'),
        TP('TP501', '+12V_ARM'),
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
        CONN('J501', 2, 'SPARK_COIL', ['+12V_ARM', 'COIL_N'], 'MF2',
             'spark coil primary (COMB: 12 V, 4 A peak ASSUMED; coil primary >= 3 ohm so steady current <= 4 A)'),
    ]))
    g.append(('Torch solenoids (12 V, ARM-gated)', solenoid_channel('SOL1', 510, 'SOL1_G', '+12V_ARM', 'J502', 'SOL1 torch N2O') +
              solenoid_channel('SOL2', 520, 'SOL2_G', '+12V_ARM', 'J503', 'SOL2 torch propane')))
    g.append(('Roll RCS provision (LEAD 2026-10-12: 2 reserved channels, one N2O-vapour thruster pair each; 12 V, ARM-gated; '
              '<= 0.75 A per coil ASSUMED, no valve chosen)',
              solenoid_channel('SOL4', 530, 'SOL4_G', '+12V_ARM', 'J504', 'SOL4 roll CW pair', coils=2) +
              solenoid_channel('SOL5', 540, 'SOL5_G', '+12V_ARM', 'J505', 'SOL5 roll CCW pair', coils=2)))
    g.append(('Main-valve holding magnet (ARM bus, fast release)', solenoid_channel('MVL', 550, 'MV_LATCH_G', 'ARM_BUS', 'J506', 'MV latch magnet')))
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
    g.append(('Main-valve position switches (to GND when actuated)', [
        CONN('J508', 3, 'MV_SWITCHES', ['MV_OPEN_SW_RAW', 'MV_CLOSED_SW_RAW', 'GND'], 'GH3', 'MV OPEN / CLOSED microswitches'),
        R('R570', '10k', 'MV_OPEN_SW_RAW', '+3V3', horiz=False), R('R571', '10k', 'MV_CLOSED_SW_RAW', '+3V3', horiz=False),
        R('R572', '4.7k', 'MV_OPEN_SW_RAW', 'MV_OPEN_SW'), R('R573', '4.7k', 'MV_CLOSED_SW_RAW', 'MV_CLOSED_SW'),
        C('C570', '100nF/50V X7R', 'MV_OPEN_SW', 'GND'), C('C571', '100nF/50V X7R', 'MV_CLOSED_SW', 'GND'),
    ]))
    return g


def sheet_sensors():
    g = []
    adc_nets = {1: '+3V3A', 2: 'GND', 3: 'PC_AIN', 4: 'GND', 6: 'PFEED_AIN', 5: 'GND', 7: 'PTANK_AIN', 8: 'GND',
                10: 'LC_AINP', 9: 'LC_AINN', 20: '+3V3', 12: 'ADC_CS', 14: 'SCK0', 16: 'MOSI0', 15: 'ADC_DOUT',
                13: 'ADC_DRDY', 11: 'ADC_SYNC_N', 17: 'ADC_CLK', 18: 'ADC_CAP', 19: 'GND'}
    g.append(('24-bit ADC ADS131M04 (4 kSPS, decimated to 1 kHz in firmware), 8.192 MHz clock', [
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
    for i, (tag, ref0, conn, fn) in enumerate([('PC', 610, 'J601', 'Pc chamber pressure (TE M3234-...-01KPG 0-1000 psig, fixed side on 1/8 in sense line)'),
                                                ('PFEED', 620, 'J602', 'injector feed pressure (TE M3234-...-01KPG, gimballed side)'),
                                                ('PTANK', 630, 'J603', 'tank pressure (TE M3234-...-01KPG)')]):
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
    g.append(('Tank wall 1-Wire (DS18B20) and pintle-servo bracket NTC', [
        CONN('J608', 3, 'ONEWIRE_TTANK', ['+3V3', 'ONEWIRE_EXT', 'GND'], 'GH3', '1-Wire DS18B20 x2 tank wall'),
        R('R690', '4.7k', 'ONEWIRE', '+3V3', horiz=False), R('R691', '100', 'ONEWIRE', 'ONEWIRE_EXT'),
        P('D690', 'Diode', 'ESD9B3.3ST5G', 'ESD9B3.3ST5G', {1: 'ONEWIRE_EXT', 2: 'GND'}, FP['SOD923'], small=True,
          Spec='3.3 V bidirectional ESD; pinout per KiCad lib', Function='1-Wire ESD'),
        CONN('J609', 2, 'NTC_SERVO', ['NTC_EXT', 'GND'], 'GH2', 'NTC 10k B3950 on pintle-servo bracket'),
        R('R692', '10k 0.1%', '+3V3', 'NTC_EXT', horiz=False, spec='ratiometric to Teensy ADC reference'),
        R('R693', '1k', 'NTC_EXT', 'NTC_SERVO'), C('C690', '100nF/50V X7R', 'NTC_SERVO', 'GND'),
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


SHEETS = [
    ('Power', 'power.kicad_sch', 'Power input, protection, rails', sheet_power),
    ('MCU_CAN', 'mcu_can.kicad_sch', 'MCU Teensy 4.1 and CAN', sheet_mcu),
    ('Safety_Arming', 'safety_arming.kicad_sch', 'Arming, watchdog, output buffers', sheet_safety),
    ('Actuators', 'actuators.kicad_sch', 'Servo actuators, TVC power switch', sheet_actuators),
    ('Igniter_Valves', 'igniter_valves.kicad_sch', '12 V boost, spark, solenoid drivers', sheet_igniter),
    ('Sensors', 'sensors.kicad_sch', 'ADC, pressure, load cell, TC, encoders', sheet_sensors),
]

POWER_NETS = ['GND', 'VBAT', 'VLOGIC', '+5V', '+3V3', '+3V3A', '+3V3_ENC', '+5V_SNS', '+2V5_EXC', 'ARM_BUS', '+5V_ARM',
              '+12V_ARM', 'TVC_PWR']
