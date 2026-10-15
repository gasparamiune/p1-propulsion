"""Custom KiCad symbols for the ARGOS engine ECU (06-electronics), v1 2026-10-12.

Pin data sources (DATASHEET): see PIN_SOURCES. Symbols are drawn as plain boxes; electrical pin types are
chosen for ERC (bidirectional GPIO, power_in/power_out rails)."""
import math

from sexpr import Q

PIN_SOURCES = {
    'Teensy41': 'PJRC Teensy 4.1 pinout card / https://www.pjrc.com/store/teensy41.html (accessed 2026-10-11); '
                'edge pins only (2 x 24 at 2.54 mm, rows 15.24 mm apart); pad numbering is DIP-style (this project)',
    'ADS131M04_PW': 'TI ADS131M04 datasheet (SBAS890), TSSOP-20 (PW) pin functions (accessed 2026-10-11 via ti.com)',
    'Pololu_U3V70F12': 'Pololu item #2895 product page (accessed 2026-10-12): pins VIN, VOUT, ENABLE, GND; '
                       'hole pattern NOT taken from a drawing -> footprint is a wire-attach placeholder',
}


def _fx(size=1.27, hide=False, justify=None):
    e = ['effects', ['font', ['size', size, size]]]
    if justify:
        e.append(['justify'] + justify.split())
    if hide:
        e.append('hide')
    return e


def _prop(k, v, x=0, y=0, ang=0, hide=False, justify=None):
    return ['property', Q(k), Q(v), ['at', x, y, ang], _fx(hide=hide, justify=justify)]


def _pin(ptype, num, name, x, y, ang, length=2.54, hide=False):
    p = ['pin', ptype, 'line', ['at', x, y, ang], ['length', length]]
    if hide:
        p.append('hide')
    p += [['name', Q(name), _fx()], ['number', Q(num), _fx()]]
    return p


def power_rail(net, ground=False, desc=None):
    """Power symbol named PWR_<net>; pin name == value == net (works with KiCad 7 and 8 naming rules)."""
    name = 'PWR_' + net.replace('+', 'P').replace('-', 'N').replace('.', 'V')
    if ground:
        gfx = [['polyline', ['pts', ['xy', 0, 0], ['xy', 0, -1.27], ['xy', 1.27, -1.27], ['xy', 0, -2.54],
                             ['xy', -1.27, -1.27], ['xy', 0, -1.27]],
                ['stroke', ['width', 0], ['type', 'default']], ['fill', ['type', 'none']]]]
        vy = -3.81
    else:
        gfx = [['polyline', ['pts', ['xy', -0.762, 1.27], ['xy', 0, 2.54], ['xy', 0.762, 1.27]],
                ['stroke', ['width', 0], ['type', 'default']], ['fill', ['type', 'none']]],
               ['polyline', ['pts', ['xy', 0, 0], ['xy', 0, 2.54]],
                ['stroke', ['width', 0], ['type', 'default']], ['fill', ['type', 'none']]]]
        vy = 3.556
    return ['symbol', Q(name), ['power'], ['pin_names', ['offset', 0]], ['in_bom', 'yes'], ['on_board', 'yes'],
            _prop('Reference', '#PWR', 0, -6.35 if ground else -3.81, hide=True),
            _prop('Value', net, 0, vy),
            _prop('Footprint', '', hide=True), _prop('Datasheet', '', hide=True),
            _prop('ki_keywords', 'global power', hide=True),
            _prop('ki_description', desc or ('Power symbol creates a global net named "%s"' % net), hide=True),
            ['symbol', Q(name + '_0_1')] + gfx,
            ['symbol', Q(name + '_1_1'), _pin('power_in', '1', net, 0, 0, 270 if ground else 90, 0, hide=True)]]


def box_symbol(name, ref, value, left, right, top=(), bottom=(), width=None, pitch=2.54, fp='', ds='~',
               desc='', keywords='', fp_filter=''):
    """Box symbol. left/right/top/bottom: lists of (number, name, type) or None for a gap."""
    nl, nr = len(left), len(right)
    rows = max(nl, nr)
    h = (rows + 1) * pitch
    if width is None:
        longest = max([len(p[1]) for p in list(left) + list(right) if p] + [4])
        width = max(15.24, round((longest * 1.27 * 2 + 5.08) / 2.54) * 2.54)
    nt, nb = len(top), len(bottom)
    width = max(width, (max(nt, nb) + 1) * pitch)
    x0, x1 = -width / 2, width / 2
    y1 = h / 2
    y0 = -h / 2
    # snap outward to 2.54 so pin ends land on grid and the last pin row stays inside the body
    x0 = -math.ceil(width / 2 / 2.54 - 1e-9) * 2.54
    x1 = -x0
    y1 = math.ceil(h / 2 / 2.54 - 1e-9) * 2.54
    y0 = -y1
    pins = []
    L = 2.54
    for i, p in enumerate(left):
        if p:
            pins.append(_pin(p[2], p[0], p[1], x0 - L, y1 - pitch * (i + 1), 0, L))
    for i, p in enumerate(right):
        if p:
            pins.append(_pin(p[2], p[0], p[1], x1 + L, y1 - pitch * (i + 1), 180, L))
    for i, p in enumerate(top):
        if p:
            pins.append(_pin(p[2], p[0], p[1], x0 + pitch * (i + 1), y1 + L, 270, L))
    for i, p in enumerate(bottom):
        if p:
            pins.append(_pin(p[2], p[0], p[1], x0 + pitch * (i + 1), y0 - L, 90, L))
    body = ['rectangle', ['start', x0, y1], ['end', x1, y0], ['stroke', ['width', 0.254], ['type', 'default']],
            ['fill', ['type', 'background']]]
    node = ['symbol', Q(name), ['pin_names', ['offset', 1.016]], ['in_bom', 'yes'], ['on_board', 'yes'],
            _prop('Reference', ref, x0, y1 + 1.27, justify='left bottom'),
            _prop('Value', value, x0, y0 - 1.27, justify='left top'),
            _prop('Footprint', fp, hide=True), _prop('Datasheet', ds, hide=True),
            _prop('ki_keywords', keywords, hide=True), _prop('ki_description', desc, hide=True)]
    if fp_filter:
        node.append(_prop('ki_fp_filters', fp_filter, hide=True))
    node.append(['symbol', Q(name + '_0_1'), body])
    node.append(['symbol', Q(name + '_1_1')] + pins)
    return node


# Teensy 4.1 edge pins, physical DIP-style numbering (1..24 down the left/USB-at-top row, 25..48 up the right row)
# (pad, label, type). GPIO are bidirectional. 3.3V: first pad power_out (on-board regulator), second passive
# (same net) to avoid a false power_out/power_out ERC conflict.
TEENSY41_LEFT = [(1, 'GND', 'power_in')] + [(2 + i, str(i), 'bidirectional') for i in range(13)] + \
                [(15, '3.3V', 'power_out')] + [(16 + i, str(24 + i), 'bidirectional') for i in range(9)]
TEENSY41_RIGHT_TOP_DOWN = [(48, 'VIN', 'power_in'), (47, 'GND', 'power_in'), (46, '3.3V', 'passive')] + \
                          [(45 - i, str(23 - i), 'bidirectional') for i in range(11)] + \
                          [(34, 'GND', 'power_in')] + [(33 - i, str(41 - i), 'bidirectional') for i in range(9)]

TEENSY41_FUNC = {  # alternate-function hints shown in the pin names (DATASHEET PJRC card)
    '0': '0/RX1/CRX2', '1': '1/TX1/CTX2', '7': '7/RX2', '8': '8/TX2', '10': '10/CS', '11': '11/MOSI',
    '12': '12/MISO', '13': '13/SCK/LED', '14': '14/A0', '15': '15/A1', '16': '16/A2', '17': '17/A3',
    '18': '18/A4', '19': '19/A5', '20': '20/A6', '21': '21/A7', '22': '22/A8/CTX1', '23': '23/A9/CRX1',
    '24': '24/A10', '25': '25/A11', '26': '26/A12/MOSI1', '27': '27/A13/SCK1', '30': '30/CRX3',
    '31': '31/CTX3', '38': '38/A14/CS1', '39': '39/A15/MISO1', '40': '40/A16', '41': '41/A17',
}


def teensy41():
    def lab(p):
        num, nm, t = p
        return (str(num), TEENSY41_FUNC.get(nm, nm), t)
    left = [lab(p) for p in TEENSY41_LEFT]
    right = [lab(p) for p in TEENSY41_RIGHT_TOP_DOWN]
    return box_symbol('Teensy41', 'U', 'Teensy_4.1', left, right, width=38.1,
                      fp='argos_ecu:Teensy41_Socket', ds='https://www.pjrc.com/store/teensy41.html',
                      desc='PJRC Teensy 4.1 (i.MX RT1062) on 2x24 sockets; edge pins only; cut VUSB-VIN pads',
                      keywords='teensy mcu imxrt1062')


def teensy_pad(label):
    """Pad number for a Teensy pin label ('0'..'41', 'VIN', ...); GND/3.3V return the first pad."""
    for num, nm, t in TEENSY41_LEFT + TEENSY41_RIGHT_TOP_DOWN:
        if nm == label:
            return str(num)
    raise KeyError(label)


def ads131m04_pw():
    left = [('1', 'AVDD', 'power_in'), ('3', 'AIN0P', 'input'), ('4', 'AIN0N', 'input'), ('6', 'AIN1P', 'input'),
            ('5', 'AIN1N', 'input'), ('7', 'AIN2P', 'input'), ('8', 'AIN2N', 'input'), ('10', 'AIN3P', 'input'),
            ('9', 'AIN3N', 'input'), ('2', 'AGND', 'power_in')]
    right = [('20', 'DVDD', 'power_in'), ('12', '~{CS}', 'input'), ('14', 'SCLK', 'input'), ('16', 'DIN', 'input'),
             ('15', 'DOUT', 'tri_state'), ('13', '~{DRDY}', 'output'), ('11', '~{SYNC}/~{RESET}', 'input'),
             ('17', 'CLKIN', 'input'), ('18', 'CAP', 'passive'), ('19', 'DGND', 'power_in')]
    return box_symbol('ADS131M04_PW', 'U', 'ADS131M04IPWR', left, right, width=22.86,
                      fp='Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',
                      ds='https://www.ti.com/lit/ds/symlink/ads131m04.pdf',
                      desc='4-ch simultaneous-sampling 24-bit delta-sigma ADC, 64 kSPS, PGA 1-128, internal 1.2 V ref',
                      keywords='adc delta-sigma 24bit simultaneous', fp_filter='TSSOP*4.4x6.5mm*P0.65mm*')


def pololu_u3v70f12():
    left = [('1', 'VIN', 'power_in'), ('2', 'ENABLE', 'input'), ('3', 'GND', 'power_in')]
    right = [('4', 'VOUT', 'power_out'), None, ('5', 'GND', 'passive')]
    return box_symbol('Pololu_U3V70F12', 'PS', 'U3V70F12', left, right, width=15.24,
                      fp='argos_ecu:Pololu_U3V70_WireAttach', ds='https://www.pololu.com/product/2895',
                      desc='Pololu 12 V step-up module U3V70F12 (VIN 2.9-12 V, ~6 A prolonged input, EN pull-up 100k to VIN)',
                      keywords='boost module 12V')
