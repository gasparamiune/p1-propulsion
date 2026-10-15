#!/usr/bin/env python3
"""Build interfaces/electronics.json v2 (Electronics, 06-electronics), 2026-10-13.

Supersedes electronics.json v1 (2026-10-11, sha256/16 42fe12e15baa6e3e; archived as 06-electronics/results/electronics_v1.json).
v1 keys are kept; their content is updated where v1 is superseded, and every superseded v1 value is named in 'superseded_v1'.

Single-source rule: numbers come from the files that own them, read here:
  firmware/src/core/config.h, engine_params.h, mech_params.h, protocol.h, types.h   (firmware v2.8.3 design values and tags)
  results/*.json                                                                     (Electronics calcs)
  results/sil_v2p8_3/MANIFEST_v1.json (+ v2.8.2 manifest, v2.8.1 test log)          (SIL record)
  hardware/kicad/pin_map_v2p4.csv, erc/netlist_crosscheck.txt, erc/argos_ecu_erc.rpt (ECU schematic v2.4)
  <engine>/interfaces/gnc.json, CHANGELOG.md, electronics.json (v1)                  (other teams' values and lead decisions)
Lead decisions are cited by CHANGELOG line number; the script checks a marker string on each cited line so a wrong citation fails.
Nothing here is hardware validation: SIL, calculation and schematic checks only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
RES = os.path.join(ROOT, 'results')
CORE = os.path.join(ROOT, 'firmware', 'src', 'core')
KICAD = os.path.join(ROOT, 'hardware', 'kicad')
DATE = '2026-10-13'
READ = OrderedDict()   # every file read -> sha256/16


def rd(path: str, mode: str = 'r'):
    with open(path, 'rb') as f:
        b = f.read()
    READ[os.path.relpath(path, ROOT) if path.startswith(ROOT) else path] = hashlib.sha256(b).hexdigest()[:16]
    return b if mode == 'rb' else b.decode('utf-8')


def jload(path: str):
    return json.loads(rd(path))


def tv(v, tag, **kw):
    d = OrderedDict([('v', v), ('tag', tag)])
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ firmware constants
UNIT = [('_radps2', 'rad/s^2'), ('_radps', 'rad/s'), ('_rad', 'rad'), ('_Paps', 'Pa/s'), ('_Nps', 'N/s'), ('_mps', 'm/s'),
        ('_Pa', 'Pa'), ('_Hz', 'Hz'), ('_ohm', 'ohm'), ('_us', 'us'), ('_dB', 'dB'), ('_ps', '1/s'), ('_s', 's'), ('_N', 'N'),
        ('_K', 'K'), ('_V', 'V'), ('_A', 'A'), ('_m', 'm')]


def unit_of(name: str) -> str:
    for suf, u in UNIT:
        if name.endswith(suf):
            return u
    return '-'


def parse_constexpr(text: str, ns: str):
    out = OrderedDict()
    for m in re.finditer(r'constexpr\s+(?:float|double|int|bool|uint16_t|uint8_t)\s+(\w+)\s*=\s*([^;]+);[ \t]*(?://[ \t]*(.*))?', text):
        name, expr, com = m.group(1), m.group(2).strip(), (m.group(3) or '').strip()
        tag = re.match(r'\[([^\]]*)\]', com)
        if name in out and out[name]['expr'] != expr:   # SIL what-if branch defined first from a macro: keep the literal one
            if re.fullmatch(r'[0-9.eE+-]+f?', expr):
                out[name] = {'expr': expr, 'tag': tag.group(1) if tag else com[:120], 'ns': ns}
            continue
        out.setdefault(name, {'expr': expr, 'tag': tag.group(1) if tag else com[:120], 'ns': ns})
    return out


class Cfg:
    def __init__(self):
        self.d = OrderedDict()
        for fn, ns in (('engine_params.h', 'eng'), ('mech_params.h', 'mech'), ('config.h', 'cfg')):
            for k, v in parse_constexpr(rd(os.path.join(CORE, fn)), ns).items():
                self.d[(ns, k)] = v
        self.val = {}
        for _ in range(6):   # resolve references iteratively
            for (ns, k), v in self.d.items():
                if (ns, k) in self.val:
                    continue
                e = v['expr']
                e = re.sub(r'\b(eng|mech|cfg)::(\w+)', lambda m: '__%s__%s' % (m.group(1), m.group(2)), e)
                e = re.sub(r'(\d)f\b', r'\1', e)
                if e in ('true', 'false'):
                    self.val[(ns, k)] = (e == 'true')
                    continue
                env = {}
                ok = True
                for nm in set(re.findall(r'\b(__\w+__\w+|k\w+)\b', e)):
                    if nm.startswith('__'):
                        _, ns2, k2 = nm.split('__', 2)
                        key = (ns2, k2)
                    else:
                        key = (ns, nm) if (ns, nm) in self.d else ('eng', nm) if ('eng', nm) in self.d else ('mech', nm)
                    if key in self.val and not isinstance(self.val[key], bool):
                        env[nm] = self.val[key]
                    else:
                        ok = False
                if not ok or re.search(r'[a-jl-zA-Z_]\w*\s*\(', e) or '?' in e:
                    continue
                try:
                    self.val[(ns, k)] = float(eval(e, {'__builtins__': {}}, env))
                except Exception:
                    pass

    def __call__(self, name: str, ns: str = 'cfg', digits: int = 6):
        key = (ns, name)
        if key not in self.d:
            raise KeyError('%s::%s not found' % (ns, name))
        v = self.val.get(key)
        if isinstance(v, float):
            v = float('%.*g' % (digits, v))
        return OrderedDict([('v', v), ('unit', unit_of(name)), ('tag', self.d[key]['tag']),
                            ('src', '%s %s' % ({'cfg': 'config.h', 'eng': 'engine_params.h', 'mech': 'mech_params.h'}[ns], name))])


# ------------------------------------------------------------------------------------------------ CHANGELOG citations
class Changelog:
    def __init__(self, path):
        self.lines = rd(path).split('\n')

    def cite(self, n: int, marker: str, chars: int = 220):
        line = self.lines[n - 1]
        if marker not in line:
            raise SystemExit('CHANGELOG line %d does not contain %r' % (n, marker))
        parts = [p.strip() for p in line.split('|')]
        text = parts[3] if len(parts) > 3 else line
        return 'CHANGELOG line %d (%s, %s): %s' % (n, parts[1], parts[0], text[:chars] + ('...' if len(text) > chars else ''))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default='/home/claude/work/shared-fallback/engine')
    ap.add_argument('--out', default=os.path.join(RES, 'electronics_v2.json'))
    a = ap.parse_args()
    ENG = a.engine_root
    C = Cfg()
    CL = Changelog(os.path.join(ENG, 'interfaces', 'CHANGELOG.md'))
    v1_path = os.path.join(ENG, 'interfaces', 'electronics.json')
    v1 = jload(v1_path)
    if v1.get('version') != 'v1':
        raise SystemExit('hub electronics.json is not v1 (%s): build v2 from the archived v1 instead' % v1.get('version'))
    v1_sha = READ[v1_path]
    gnc_path = os.path.join(ENG, 'interfaces', 'gnc.json')
    gnc = jload(gnc_path)
    gnc_sha = READ[gnc_path]
    ign = gnc['requirements']['ignition']

    fw_first = rd(os.path.join(CORE, 'config.h')).split('\n', 1)[0]
    fw_ver = re.search(r'\((v[0-9][0-9.]*)', fw_first).group(1)
    man = jload(os.path.join(RES, 'sil_v2p9', 'MANIFEST_v1.json'))
    man2 = jload(os.path.join(RES, 'sil_v2p8_2', 'MANIFEST_v1.json'))
    t281 = rd(os.path.join(RES, 'sil_v2p8_1', 'test_core_v2p8_1.txt')).strip().split('\n')[-1]
    s6 = jload(os.path.join(RES, 'sil_v2p8_3', 'S6_aborts.json'))
    s10 = jload(os.path.join(RES, 'sil_v2p8_3', 'S10_relight_v2p8.json'))
    s8 = jload(os.path.join(RES, 'sil_v2p8_3', 'S8_priming.json'))
    s5 = jload(os.path.join(RES, 'sil_v2p8_3', 'S5_mc.json'))
    s5_rows = list(csv.DictReader(rd(os.path.join(RES, 'sil_v2p8_3', 'S5_mc.csv')).splitlines()))
    s5_causes = OrderedDict()
    for r in s5_rows:
        s5_causes[r['abort']] = s5_causes.get(r['abort'], 0) + 1
    s5_v27 = list(csv.DictReader(rd(os.path.join(RES, 'sil_v2p7', 'S5_mc.csv')).splitlines()))
    s5_v27_causes = OrderedDict()
    for r in s5_v27:
        s5_v27_causes[r['abort']] = s5_v27_causes.get(r['abort'], 0) + 1
    idm_path = os.path.join(RES, 'ignition_detect_margin_v1.json')
    idm = jload(idm_path) if os.path.exists(idm_path) else None

    rail = jload(os.path.join(RES, 'pintle_rail_v3.json'))
    ecuv = jload(os.path.join(RES, 'ecu_v2p3_values_v1.json'))
    ot3 = jload(os.path.join(RES, 'over_thrust_v3.json'))
    rmap_path = os.path.join(RES, 'pintle_rate_map_v1.json')
    rmap = jload(rmap_path)
    eng03 = jload(os.path.join(RES, 'eng03_slew_check_v1.json'))
    fp1 = jload(os.path.join(RES, 'fault_path_v1.json'))
    fp2 = jload(os.path.join(RES, 'fault_path_v2.json'))
    pct = jload(os.path.join(RES, 'pc_transducer_v2.json'))
    latch = jload(os.path.join(RES, 'mv_latch_magnet_v1.json'))
    sup = jload(os.path.join(RES, 'tvc_supply_budget_v1.json'))
    servo = jload(os.path.join(RES, 'pintle_mini_servo_v1.json'))
    hv69 = [c for c in servo['candidates'] if c.get('id') == 'MKS HV69'][0]
    bom = jload(os.path.join(RES, 'bom_v2p1.json'))['summary']
    xc = rd(os.path.join(KICAD, 'erc', 'netlist_crosscheck.txt'))
    erc = rd(os.path.join(KICAD, 'erc', 'argos_ecu_erc.rpt'))
    pins = list(csv.DictReader(rd(os.path.join(KICAD, 'pin_map_v2p4.csv')).splitlines()))
    proto = rd(os.path.join(CORE, 'protocol.h'))
    types_h = rd(os.path.join(CORE, 'types.h'))

    # ---- parsed protocol / enum facts
    ids = OrderedDict((m.group(1), int(m.group(2), 16)) for m in re.finditer(r'ID_(\w+)\s*=\s*(0x[0-9A-Fa-f]+)', proto))
    tlmr = OrderedDict((m.group(1), m.group(2)) for m in re.finditer(r'constexpr uint8_t (\w+) = (1u << \d|PRIMED);', proto.split('namespace tlmr')[1].split('}')[0]))
    abort_enum = OrderedDict()
    for m in re.finditer(r'^\s*([A-Z_]+) = (\d+),?\s*(?://\s*(.*))?$', types_h.split('enum class Abort')[1].split('};')[0], re.M):
        abort_enum[m.group(1)] = int(m.group(2))
    for m in re.finditer(r'\b([A-Z_]+) = (\d+)\b', types_h.split('enum class Abort')[1].split('};')[0]):
        abort_enum.setdefault(m.group(1), int(m.group(2)))
    xm = re.search(r'components (\d+), nets (\d+) .*pins (\d+) of (\d+) intended\s*\nerrors (\d+), warnings (\d+)', xc)
    em = re.search(r'ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)', erc)
    sheets = re.findall(r'\*\*\*\*\* Sheet (\S+)', erc)

    # ---------------------------------------------------------------------------------------------------- document
    doc = OrderedDict()
    doc['id'] = 'electronics'
    doc['version'] = 'v2'
    doc['date'] = DATE
    doc['owner'] = 'electronics (06-electronics)'
    doc['status'] = ('DESIGN + SIL + schematic. Firmware %s runs only in SIL; the ECU v2.3 schematic passes ERC and a netlist cross-check; '
                     'no board has been built and nothing here is hardware-validated. Values carry tags; open items are listed in '
                     'open_issues, and the bench plan (06-electronics/docs/bench_plan_v2.md) is where each is closed.' % fw_ver)
    doc['units'] = v1['units']
    doc['supersedes'] = OrderedDict([('file', 'electronics.json v1 (2026-10-11)'), ('sha256_16', v1_sha),
                                     ('archive', '06-electronics/results/electronics_v1.json')])
    doc['scripts'] = ['06-electronics/calc/make_interface_json_v2.py (this file)', '06-electronics/calc/bom_v2.py',
                      '06-electronics/calc/ecu_v2p3_values_v1.py', '06-electronics/calc/fault_path_v2.py',
                      '06-electronics/calc/ignition_detect_margin_v1.py', '06-electronics/calc/pintle_rail_v3.py',
                      '06-electronics/calc/over_thrust_v3.py', '06-electronics/calc/pintle_rate_map_v1.py',
                      '06-electronics/firmware/tools/sil_manifest_v1.py', '06-electronics/hardware/kicad_gen/run_all.sh']
    doc['inputs'] = OrderedDict([('gnc.json', '%s %s' % (gnc.get('version'), gnc_sha)),
                                 ('firmware', '%s (SIL record %s, source tree %s)' % (fw_ver, man['record_sha256_16'], man['tree_sha256'][:16])),
                                 ('generated_headers', OrderedDict((k, [(r['source'], r.get('version_named', '(not named in the header)'), r['sha_at_generation'], r['status'])
                                                                         for r in v['refs']]) for k, v in man['generated_headers'].items()))])

    doc['change_summary_v1_to_v2'] = [
        'firmware: v1 had no firmware; v2 publishes firmware %s (SIL only) with its manifest, test record and four pre-existing SIL FAILs and their dispositions' % fw_ver,
        'pintle actuator: Savox SB-2292SG on VBAT (v1) -> MKS HV69 on a regulated 7.49 V pintle rail (TPS552882 + LTC4365 OV disconnect)',
        'main valve: spring-closed ball valve with servo opener (v1) -> MV-P balanced poppet with the SB-2292SG cam opener, over-centre latch magnet and dashpot (lead line 91)',
        'transducers: Pc 0-34.5 bar / feed and tank 0-68.9 bar (v1) -> Pc and P_torch 070BG, P_feed and P_tank 170BG; hardware OVP comparator 31.47 bar g',
        'new channels: ADC2 (P_torch, pintle rail, rail current, regulator output), TC4-TC6 (bore top, MSS-1, MSS-2), bay DS18B20, mode strap, GSE heater interlock',
        'CAN: + FC_THRUST 0x024, CMD_AUX 0x028, TLM_RELIGHT 0x102; Pc-invalid markers (RG-15); EVENT codes enumerated',
        'relight: v2.8 design (valve and torch at E0, lift at E1, W from the lift), TLM_RELIGHT PRIMED = DIRECT PATH, stale-flag rule',
        'aborts: 27 causes (v1 listed 7 fail-safe states); over-thrust abort from the FC accelerometer estimate (650 N, 3 frames)',
        'ECU schematic v2.3 (KiCad 7.0.11, 9 sheets, ERC 0/0) and pin map; BOM v2 (TO-QUOTE, ship to DK-6400)']

    # ---------------------------------------------------------------------------------------------------- firmware + SIL
    fails = man['sil_fail_lines']
    doc['firmware'] = OrderedDict([
        ('version', fw_ver), ('target', 'PJRC Teensy 4.1 (i.MX RT1062); HAL for the hardware NOT written (core runs in SIL and test_core)'),
        ('record', OrderedDict([('manifest', '06-electronics/results/sil_v2p9/MANIFEST_v1.json'), ('record_sha256_16', man['record_sha256_16']),
                                ('tree_sha256_16', man['tree_sha256'][:16]), ('n_files', man['n_files'])])),
        ('unit_tests', OrderedDict([('v2.8.1', t281), ('v2.8.2', man2['test_core']['summary']), (fw_ver, man['test_core']['summary']),
                                    ('note', 'test_core runs 1-2 of v2.8.3 (254/258, 256/258) failed on Electronics expectations, not on the code; kept')])),
        ('sil_scenarios_v2p8_3', OrderedDict([
            ('S5_dispersed_pad_start_MC', OrderedDict([('runs', s5['runs']), ('aborts', s5['aborts']), ('abort_codes', s5_causes),
                                                       ('v2.7_abort_codes', s5_v27_causes),
                                                       ('note', 'code 3 NO_IGNITION on a LIT plant from v2.8.1 on: see open_issues OI-IGN-DET')])),
            ('S6_abort_paths', '%d/%d' % (s6['passed'], s6['total'])), ('S8_priming', '%d/%d' % (s8['passed'], s8['total'])),
            ('S10_relight_v2p8', '%d/%d' % (s10['passed'], s10['total'])),
            ('fail_lines', fails)])),
        ('arm_build', '53 double-promotion warnings (unchanged; listed in open_issues)'),
        ('gnc_conformance_RG13', OrderedDict([
            ('law', 'gnc.json v3 flight_software.gimbal_command_tracker (sim6) ahead of the 50 rad/s low-pass'),
            ('rate', C('kGncShapeSlew_radps', 'eng')), ('accel', C('kGncShapeAccel_radps2', 'eng')),
            ('lowpass_w', C('kGncShapeW_radps', 'eng')), ('lowpass_zeta', C('kGncShapeZeta', 'eng')),
            ('trace_match', tv('3.93e-8 rad tracker, 2.54e-8 rad chain vs a double-precision sim6 transcription', 'SIL test_core v2.8.3')),
            ('finding', 'v2.4-v2.8.2 ran the gnc.json v2 plain 100 deg/s limiter (engine_params.h generated from gnc.json v2 7089d7b34808cc31); fixed in v2.8.3'),
            ('btvc1_bypass', 'B-TVC-1 bypass mode keeps the plain limiter (actuator characterisation)')])),
        ('W_build_constant', OrderedDict([
            ('flight_relight_W', C('kIgnWindowRelightLong_s')), ('flight_first_start_W', C('kIgnWindowFirst_s')),
            ('stand_R1_W', C('kIgnWindowFirstStand_s')), ('stand_R2_W', C('kIgnWindowRelightStand_s')),
            ('rule', 'W is a compile-time constant. SIL_WHATIF_RELIGHT_W exists only for SIL what-if builds: config.h #errors unless '
                     'ECU_SIL_TEST_HOOKS is defined, so a flight, Teensy or test_core build cannot carry it (coordinator: keep W a build constant)')])),
    ])

    doc['sil_fail_dispositions'] = [
        OrderedDict([('id', 'S6 gimbal_jam_moving_cmd'), ('checks', 'gimbal jam at 3.0 s under a 2 deg alpha 1 Hz sine -> GIMBAL_FAULT abort'),
                     ('why_fails', 'on the as-built 135/225 deg linkage the per-axis mismatch reaches 1.0 deg (1.41 deg along servo A), below the 1.5 deg '
                                   'threshold (kGimbalFaultErr_rad); the 4 deg case is detected. Detection bound >= 3 deg per axis / >= 2.12 deg along a servo line'),
                     ('flight_path', True), ('disposition', 'FIX'),
                     ('closure', 'servo-frame mismatch metric (proposal); needs the GNC false-abort trade before implementation; until then a jammed '
                                 'gimbal under small commands is caught only by the encoder-vs-command error at larger amplitude')]),
        OrderedDict([('id', 'S6 throat_blocked_70pct_500N_24C_Cd0p8'), ('checks', 'over-pressure abort and plant Pc <= MEOP 45 bar abs'),
                     ('why_fails', 'hardware trip first (HW_OVERPRESSURE, abort +8 ms; expected firmware PC_OVERPRESSURE) and plant Pc max 53.4 bar abs > MEOP '
                                   '(< proof 67.5 bar); the peak comes 9-18 ms after the block, before any detection can act'),
                     ('flight_path', True), ('disposition', 'ACCEPTED-WITH-REASON'),
                     ('closure', 'Combustion v2.4 accepted it as fault load case LC-TB70 (58.1 bar abs, > 45 bar 72 ms) and LC-TB-S; the assembled FEA closes it. '
                                 + CL.cite(101, 'S6 throat block acceptable', 120))]),
        OrderedDict([('id', 'S6 throat_blocked_70pct_500N_24C_Cd0p8_ballvalve_v2p7_compare'), ('checks', 'same case with the superseded ball valve'),
                     ('why_fails', 'same as above; MV closed +105 ms (ball) vs +46 ms (MV-P)'), ('flight_path', False), ('disposition', 'OBSOLETE'),
                     ('closure', 'kept as comparison evidence for the superseded ball-valve concept (lead line 91 adopted MV-P)')]),
        OrderedDict([('id', 'S9 lit_bias_minus_1p034bar_TEB'), ('checks', 'light detection on a pad first start (W 0.40 s) with a -1.034 bar post-zero bias (M3200 TEB)'),
                     ('why_fails', 'true Pc 3.69 bar abs, measured max 2.66 < 3.0 bar abs -> NO_IGNITION on a lit engine (fail-safe); detection holds to '
                                   '-0.60 bar bias, lost at -0.80; 2 x BFSL passes; unlit +TEB max 1.87 bar abs'),
                     ('flight_path', True), ('disposition', 'FIX (raised from ACCEPTED-WITH-REASON on the S5 evidence)'),
                     ('closure', 'the same margin fails without any bias in the dispersed S5 pad-start MC (OI-IGN-DET); Combustion sets the light threshold '
                                 'inside 1.87-2.66 bar abs or a larger ignition lift; B-PC-1 residual <= 0.60 bar stays a condition')]),
    ]

    # ---------------------------------------------------------------------------------------------------- CAN
    doc['can_interface'] = OrderedDict([
        ('physical', v1['can_interface']['physical']), ('bus', v1['can_interface']['bus']),
        ('e2e', tv('8-bit rolling sequence per ID + CRC-8 (SAE J1850 poly 0x1D, init 0xFF, final XOR 0xFF) over the preceding payload bytes; '
                   'CMD_STATE key = 0xA500 | (cmd XOR 0x5A); ABORT magic 0xA5 0x5A', 'DESIGN protocol.h')),
        ('ids_parsed_from_protocol_h', OrderedDict(('0x%03X' % v, k) for k, v in ids.items())),
        ('frames', OrderedDict([
            ('0x010 FC->ECU ABORT (event, sent 3x)', 'len 5: [0xA5][0x5A][abort code][seq][crc8]'),
            ('0x020 FC->ECU CMD_FAST 500 Hz', 'len 8: [seq][thrust setpoint u16 0.1 N][gimbal a i16 0.001 deg][gimbal b i16 0.001 deg][crc8]'),
            ('0x024 FC->ECU FC_THRUST >= 100 Hz', 'len 5: [seq][thrust estimate u16 0.1 N][flags b0 valid][crc8]; accelerometer estimate, tau 20 ms'),
            ('0x028 FC->ECU CMD_AUX >= 50 Hz while wanted', 'len 4: [seq][roll bits b0 CW b1 CCW][~roll bits][crc8]; dead-man 50 ms'),
            ('0x030 FC->ECU CMD_STATE event + 10 Hz', 'len 7: [seq][cmd][arg u16][key u16][crc8]; cmd = Cmd enum (types.h)'),
            ('0x100 ECU->FC TLM_FAST 500 Hz', 'len 8: [seq][state][Pc u16 kPa abs, 0xFFFF = invalid (RG-15)][pintle lift u16 um][fault bits u16]'),
            ('0x101 ECU->FC TLM_GIMBAL 500 Hz', 'len 8: [seq][flags][gimbal a meas i16][gimbal b meas i16][thrust u16 0.1 N, 0xFFFF when Pc invalid]'),
            ('0x102 ECU->FC TLM_RELIGHT 50 Hz', 'len 8: [seq][state][flags][relight worst u16 ms][P_feed/P_tank %, 0xFF invalid][refuse reason][crc8]'),
            ('0x110 ECU->FC TLM_SLOW 50 Hz', 'NOT DEFINED in v2.8.3 (page layout TO-DEFINE before the HAL)'),
            ('0x120 ECU->FC EVENT', 'len 8: [code][state][t_ms u32][arg u16]; each event sent 3x 10 ms apart')])),
        ('tlm_relight_flags', OrderedDict((k, v) for k, v in tlmr.items())),
        ('rg15_pc_invalid', 'TLM_FAST d2-d3 = 0xFFFF and TLM_GIMBAL d6-d7 = 0xFFFF while the Pc channel is invalid; the latched PC_SENSOR fault bit stays '
                            'in TLM_FAST d6-d7. FC: k_est_asc and the B apex predictor freeze on the marker; FC_THRUST keeps running (lead line 113)'),
        ('bus_load', v1['can_interface']['bus_load']),
        ('flight_computer_side', v1['can_interface']['flight_computer_side'])])

    # ---------------------------------------------------------------------------------------------------- relight interface
    doc['relight_interface'] = OrderedDict([
        ('sequence_v2p8', 'RELIGHT at the planned T_fire: NC valve latch + opener ramp and torch at E0, ignition lift at E1 on torch confirmation '
                          '(gate %.2f s), W %.2f s from the lift; worst E0 -> Pc-confirm deadline %.2f s (direct path)'
         % (C('kTorchGate_s')['v'], C('kIgnWindowRelightLong_s')['v'], C('kTorchGate_s')['v'] + C('kIgnWindowRelightLong_s')['v'])),
        ('torch_gate', C('kTorchGate_s')), ('W_flight_relight', C('kIgnWindowRelightLong_s')),
        ('prep_path_bound_s', tv(fp2['bounds_s']['prep_path'], 'DERIVED config.h (bleed 0.06 + ramp 0.35 + hold 0.15 + 0.81)')),
        ('primed_flag', 'PRIMED = DIRECT PATH (protocol.h alias tlmr::DIRECT_PATH). It is NOT a liquid or vapour detector: P_feed = P_sat in both '
                        'phases and the MSS TCs read Tsat either way (lead line 113 (1)); flight planning must not use it to exclude vapour'),
        ('states', 'NONE (VALID 0), PRIMED, UNPRIMED, UNKNOWN (P_feed or P_tank invalid, or a coast pintle anomaly: encoder invalid or lift > 0.10 mm '
                   'for 20 ms, RG-08); POST_ABORT b6: PRIMED never shown after an abort'),
        ('rate', tv('50 Hz in every state (>= 10 Hz required in COAST)', 'DESIGN protocol.h')),
        ('fc_planning_from_gnc', OrderedDict([('relight_planning_value_s', ign['relight_planning_value_s']['v']),
                                              ('option_c_unprimed_s', (lambda x: x['v'] if isinstance(x, dict) and 'v' in x else x)(ign['relight_planning_value_s']['option_c_unprimed_s'])),
                                              ('stale_or_missing_flag', (lambda x: x['v'] if isinstance(x, dict) and 'v' in x else x)(ign['relight_planning_value_s']['stale_or_missing_flag'])),
                                              ('source', 'gnc.json %s requirements.ignition (%s)' % (gnc.get('version'), gnc_sha))])),
        ('freeze_status', CL.cite(111, 'NOT frozen for SIL/HIL', 200)),
        ('retained_vapour_fix', CL.cite(126, 'COIL RE-ROUTE', 260)),
        ('mv_early_open_sketch', 'DROPPED (lead line 126: option (d) has no effect, Mechanical segment_traps_v34 13.947 vs 13.939 cm3); no firmware state added'),
        ('head_end_bleed', OrderedDict([
            ('status', 'FALLBACK only (lead line 126); no design (coordinator)'),
            ('budget_line', 'one ARM-gated spare channel U304 2A2 (pin 13) -> 2Y2 (pin 7) driving a SOL1-type DMN6075S low-side switch on +12V_ARM; '
                            'coil <= 0.75 A ASSUMED (~9 W while open), inside the U3V70F12 budget if not overlapping spark/torch; no Teensy pin free: '
                            'share pin 15 with the heater permit (separated in hardware by the ARM state) or add an I/O expander')])),
        ('fault_path', OrderedDict([
            ('v1_44cm3_whole_segment_vapour', fp1['findings']),
            ('v2_lead_targets', fp2['findings']),
            ('v2_sil', 'results/fault_path_v2.json (%s, %s)' % (fp2['sil_scenario'], fp2['inputs']['CHANGELOG.md']['line'])),
            ('pending', fp2['pending'])])),
    ])

    # ---------------------------------------------------------------------------------------------------- abort matrix
    AB = OrderedDict([
        ('CMD', ('FC ABORT frame 0x010 or CMD_STATE ABORT', [])),
        ('HARD_START', ('Pc above the over-pressure limit during IGNITION', ['kPcOverPressureAbs_Pa', 'kPcOverPressureTime_s'])),
        ('BLEED_FAULT', ('v2.9 head-end bleed: pad BIT step failed, V1 closure not confirmed by E0 + kHbleedCloseConfirm_s, or (stand) path / leak fault',
                         ['kHbleedCloseConfirm_s', 'kHbleedLeakTime_s', 'kHbleedPathBy_s'])),
        ('NO_IGNITION', ('v2.9: no light by the relative rule (rise >= kIgnRise_Pa over P0, floor, kIgnConfirmRelN ticks) within W from the lift command (v2.6-v2.8.3 text: Pc (filtered and raw, kIgnitionConfirmN ticks) not above the light threshold)',
                         ['kIgnRise_Pa', 'kIgnConfirmRelN', 'kIgnWindowFirst_s', 'kIgnWindowRelightLong_s', 'kIgnWindowFirstStand_s'])),
        ('FLAMEOUT', ('RUN: gauge Pc below the floor or below a fraction of the expected Pc', ['kFlameoutPc_Pa', 'kFlameoutFrac', 'kFlameoutTime_s'])),
        ('PC_BAND', ('RUN after settling: |Pc - Pc_ref| above both band limits', ['kPcBandFrac', 'kPcBandMin_Pa', 'kPcBandTime_s', 'kRunSettle_s'])),
        ('OVER_TEMP', ('case TC (az 90/270, armed only while the MV is latched or OPEN) or nozzle holder above limit, in a burn or PREPRESS; '
                       'servo-bracket NTC only flags', ['kCaseOverTemp_K', 'kNozzleHolderOverTemp_K', 'kServoBracketOverTemp_K', 'kOverTempTime_s'])),
        ('TANK_OVERPRESSURE', ('P_tank above limit in ARMED/PREPRESS (never aborts a burn)', ['kTankOverPressure_Pa', 'kTankOverPressureTime_s'])),
        ('GIMBAL_FAULT', ('command-model vs encoder mismatch while burning (allowance grows with the model rate)', ['kGimbalFaultErr_rad', 'kGimbalFaultTime_s', 'kGimbalFaultRateWin_s'])),
        ('PINTLE_FAULT', ('pintle rail lost (LTC4365 trip / regulator failure), jam, encoder invalid at ARM', ['kPrailLost_V', 'kPrailLostTime_s', 'kPintleStallTime_s', 'kPintleStallTimeI_s'])),
        ('LINK_LOST', ('no valid CMD_FAST: SAFE/ARMED/PREPRESS -> SAFE; RUN -> SHUTDOWN by default', ['kLinkDegraded_s', 'kLinkLost_s'])),
        ('PREPRESS_FAIL', ('feed not primed (P_feed > fraction of P_tank) in time, bleed lift not confirmed, MV not open', ['kPrepressTimeout_s', 'kFeedPrimedFrac'])),
        ('PC_SENSOR', ('Pc transducer output outside the window: IGNITION and stand abort; flight RUN continues open loop', ['kPcSensorMin_V', 'kPcSensorMax_V', 'kPcSensorLossStand_s'])),
        ('BATT_LOW', ('VBAT low in pad states before the first start (flag in flight); ARM refused below the rest-voltage rule', ['kBattLow_V', 'kBattLowTime_s', 'kBattArmMin_V'])),
        ('MV_FAULT', ('MV CLOSED switch missing at ARM; direct relight OPEN switch missing by the deadline: stand abort, flight flag', ['kMvOpenBy_s', 'kMvCloseConfirm_s'])),
        ('ARM_LOST', ('arming plug removed or ARM bus not on 50 ms after the request', [])),
        ('WATCHDOG', ('hardware watchdog reset: reboot lands in SAFE; a lit-session marker becomes a relight lockout', ['kHwWatchdog_s'])),
        ('PC_OVERPRESSURE', ('firmware Pc above the over-pressure limit outside IGNITION', ['kPcOverPressureAbs_Pa', 'kPcOverPressureTime_s'])),
        ('HW_OVERPRESSURE', ('hardware comparator latch (31.47 bar g on the 070BG): ARM bus already off in hardware', ['kHwOvpTime_s'])),
        ('TVC_SUPPLY', ('pad only: predicted both-stall TVC plug voltage below the minimum', ['kTvcSupplyMin_V', 'kTvcSupplyTime_s'])),
        ('OVERCURRENT', ('firmware e-fuse before the first start', ['kEfuse_A', 'kEfuseTime_s'])),
        ('MAINT_JAM', ('ARM refused: a pintle jam recorded in NV memory and not cleared (bearing A rule)', [])),
        ('TORCH_FAULT', ('no torch flame (P_torch) by the gate: abort before the pintle step', ['kTorchGate_s', 'kTorchLitAbs_Pa', 'kTorchConfirmN'])),
        ('RELIGHT_LOCKOUT', ('ARM/IGNITE/RELIGHT refused after an abort following a lit burn or on a relight, until CLEAR_LOCKOUT (ground)', [])),
        ('OVER_THRUST', ('flight RUN: FC_THRUST above the threshold on consecutive fresh valid frames (with or without a valid Pc; never on the stand)',
                         ['kOverThrust_N', 'kOverThrustFrames', 'kFcThrustRate_Hz', 'kFcThrustStale_s'])),
        ('MODE_MISMATCH', ('ARM refused: strap invalid, or strap and load-cell reading disagree', [])),
        ('BAY_HOT', ('ARM refused: bay temperature above the limit or no valid reading', ['kBayArmMax_K'])),
        ('TANK_HOT', ('ARM refused: tank temperature (max of wall DS18B20 and Tsat(P_tank)) above the limit or none valid', ['kTankIgnMax_K']))])
    matrix = []
    for name, code in abort_enum.items():
        if name == 'NONE':
            continue
        trig, keys = AB.get(name, ('(not described)', []))
        th = OrderedDict()
        for k in keys:
            try:
                th[k] = C(k)
            except KeyError:
                th[k] = C(k, 'eng')
        matrix.append(OrderedDict([('code', code), ('cause', name), ('trigger', trig), ('thresholds', th)]))
    if len(matrix) != 28:   # v2.9: + BLEED_FAULT
        raise SystemExit('abort enum parse found %d causes, expected 28' % len(matrix))
    doc['abort_matrix'] = OrderedDict([
        ('actions', 'every abort de-energises the NC valve at once and commands the pintle closed in parallel (lead line 56); no in-flight relight '
                    'retry after a no-light; normal shutdown: pintle first, MV on seat confirmation or the timeout'),
        ('mv_seat_timeout', C('kMvSeatTimeout_s')),
        ('causes', matrix)])

    # ---------------------------------------------------------------------------------------------------- over-thrust / FC_THRUST
    b = ot3['rg19_end_to_end_budget']
    doc['over_thrust'] = OrderedDict([
        ('rule', 'flight RUN, FC_THRUST > %.0f N on %d consecutive fresh valid frames; stale > %.0f ms or b0 = 0 -> flag only; never on the stand'
         % (C('kOverThrust_N')['v'], C('kOverThrustFrames')['v'], C('kFcThrustStale_s')['v'] * 1e3)),
        ('threshold', C('kOverThrust_N')), ('frames', C('kOverThrustFrames')), ('rate', C('kFcThrustRate_Hz')), ('stale', C('kFcThrustStale_s')),
        ('valid_window', CL.cite(111, 'no drogue load', 160) + ' (FC sets b0). Firmware comment in protocol.h still says "drogue released": '
                         'comment-only correction for the next release'),
        ('rg15', CL.cite(113, 'must NOT freeze on PC_SENSOR', 200)),
        ('rg19_budget_known_terms_s', b['step_onset_to_mv_seated_known_terms_s']),
        ('rg19_terms', [OrderedDict((k, t.get(k)) for k in ('id', 'term', 'mean_s', 'max_s', 'tag', 'owner', 'verify')) for t in b['terms']]),
        ('imu', tv('ADIS16470 filter / decimation delay UNKNOWN (analog.com refused by the egress proxy, not retried)', 'UNKNOWN')),
        ('proposed_allocations', 'IMU-to-estimator <= 5 ms, FC scheduling <= 2 ms (Electronics proposal, FC owner to accept)'),
        ('source', 'results/over_thrust_v3.json')])

    # ---------------------------------------------------------------------------------------------------- ENG-03 pintle rate
    doc['eng03_pintle_rate'] = OrderedDict([
        ('requirement', CL.cite(121, 'ENG-03 AMENDED', 260)),
        ('gnc_result', CL.cite(120, 'ENG-03 rate map in the 6-DOF', 260)),
        ('rate_map', OrderedDict([('file', '06-electronics/results/pintle_rate_map_v1.json'), ('sha256_16', READ[os.path.relpath(rmap_path, ROOT)]),
                                  ('summary', rmap['summary']), ('reduced_model_for_gnc', rmap['reduced_model_for_gnc'])])),
        ('quasi_static_check', eng03['verdict']['A_quasi_static']),
        ('start_ramp', C('kStartRamp_Nps', 'eng')),
        ('b_pnt_1', 'HV69 torque-speed line under load (0.42-0.55 N m at 7.335 and 7.49 V); closed-loop t10-90 <= 100 ms under load with the drive in the loop; '
                    'until then B1 launch commit mean wind < 6 m/s (lead line 121)')])

    # ---------------------------------------------------------------------------------------------------- pintle rail
    tps, fets, ltc = ecuv['tps552882'], ecuv['external_fets'], ecuv['ltc4365']
    doc['pintle_rail'] = OrderedDict([
        ('adopted', CL.cite(62, 'PINTLE RAIL', 240)),
        ('publish_v3', rail['publish']),
        ('schematic_v2p3_values', OrderedDict([('tps552882', tps), ('external_fets', fets), ('ltc4365', ltc)])),
        ('finding', 'the TPS552882 integrates only the boost-leg FETs: the buck leg needs two external FETs driven by DR1H/DR1L (missed in pintle_rail_v1/v2; '
                    'drawn in v2.3 with CSD17578Q5A, losses in ecu_v2p3_values_v1)'),
        ('to_confirm', ['LTC4365 UV threshold = OV threshold ASSUMED (datasheet blocked)', 'Q803 enhancement at the LTC4365 gate drive',
                        'TPS552882 compensation equations 22, 24-26 (garbled extraction) and phase margin at B-PWR-1',
                        'RPM0026A land pattern (placeholder footprint)'])])

    # ---------------------------------------------------------------------------------------------------- ECU hardware (v1 'ecu' key)
    ecu = OrderedDict(v1['ecu'])
    ecu['schematic'] = OrderedDict([
        ('version', 'v2.4 (KiCad 7.0.11, generated from hardware/kicad_gen/ecu_design.py; v2.4 = head-end bleed provision drawn)'),
        ('erc', tv('%s errors, %s warnings, %d sheets' % (em.group(2), em.group(3), len(sheets)), 'KiCad eeschema ERC (GUI on Xvfb)')),
        ('netlist_crosscheck', tv('components %s, nets %s, pins %s of %s intended, errors %s, warnings %s' % xm.groups(), 'check_netlist.py v1')),
        ('negative_control', 'PREG PWR_FLAG removed -> 1 error power_pin_not_driven U802 pin 1 (erc/negative_control_v2p3)'),
        ('files', '06-electronics/hardware/kicad (README.md lists them)'),
        ('placeholders', ['TI_RPM0026A_PLACEHOLDER (NOT FOR FABRICATION)', 'Pololu_U3V70_WireAttach (wire pads only)', 'Teensy41_Socket (verify vs PJRC drawing)'])])
    ecu['pin_map'] = [OrderedDict([('pin', p['teensy_pin']), ('net', p['net']), ('dir', p['direction']), ('function', p['function'])]) for p in pins]
    ecu['cs_decoder'] = ecuv['cs_decoder']
    ecu['mode_strap'] = ecuv['mode_strap']
    ecu['adc2'] = ecuv['adc2']
    ecu['heater_interlock'] = ecuv['heater_interlock']
    ecu['superseded_v1'] = ['pcb_outline_mm / mount_holes / enclosure_envelope_mm / connector_edges stay DESIGN reservations from v1: no layout yet',
                            'mass_kg 0.16 ASSUMED (v1) not re-estimated for v2.3 (two more ICs sheets): re-weigh after the board is built']
    doc['ecu'] = ecu

    # ---------------------------------------------------------------------------------------------------- actuators (v1 key)
    act = OrderedDict()
    for k in ('tvc_A', 'tvc_B'):
        blk = OrderedDict((kk, vv) for kk, vv in v1['actuators'][k].items()
                          if kk not in ('linkage_proposal', 'engine_side_at_n7_7V4', 'hinge_moment_assumed_Nm', 'margins_7V4', 'stiffness',
                                        'dynamics_for_GNC', 'resolution_deg_engine', 'backlash_deg_engine'))
        blk['superseded_v1'] = 'linkage, engine-side, hinge-moment, margin, stiffness and dynamics fields of v1 are superseded by mechanical.json v2 (as-built 135/225 deg linkage), gnc.json v3 and the TVC calcs below'
        blk['supply'] = OrderedDict([('switch', 'Q401 + Q403 AOD4185 on VBAT, watchdog-gated (F401 removed)'), ('budget', sup['verdict']),
                                     ('pad_rule', C('kTvcSupplyMin_V')), ('arm_rule', C('kBattArmMin_V'))])
        blk['temperature'] = 'SB-2292SG rated -10..50 C: bay <= 45 C at ARM (BAY_HOT, lead line 91); in flight within limits (Mechanical pre36)'
        act[k] = blk
    act['pintle_throttle'] = OrderedDict([
        ('model', 'MKS HV69 (%s)' % hv69['pn']), ('rail', 'PRAIL 7.49 V typ (TPS552882 + LTC4365, see pintle_rail)'),
        ('datasheet_class', OrderedDict((k, hv69.get(k)) for k in ('dims_mm', 'mass_g', 'V_range', 'T_kgcm', 's60', 'stall_A', 'T_op_C', 'deadband_us', 'spline'))),
        ('tags', 'DATASHEET via retailer copies of MKS data (TO-CONFIRM with MKS); see pintle_mini_servo_v1.json'),
        ('mechanism', 'crank r and linkage per Mechanical pintle v2.3/v2.4 (PLANNED v3.4); spring closes the unpowered servo (B-PNT-1 back-drive check)'),
        ('jam', OrderedDict([('detection', rail['publish']['jam_detection']), ('design_load', CL.cite(62, 'JAM DESIGN LOAD', 120))])),
        ('pulse', OrderedDict([('centre', C('kPintleCenter_us')), ('us_per_deg', C('kPintleUsPerDeg')), ('min', C('kPintleMin_us')), ('max', C('kPintleMax_us'))])),
        ('eng03', 'see eng03_pintle_rate'),
        ('superseded_v1', 'v1 SB-2292SG pintle actuator on VBAT, force_assumed_N, full_stroke_time_s and stroke_resolution_um')])
    act['main_valve'] = OrderedDict([
        ('concept', CL.cite(91, 'MV-P balanced poppet ADOPTED', 200)),
        ('opener', 'Savox SB-2292SG on ARM_BUS (J404), cam; ramp %.2f s, cock hold %.2f s' % (C('kMvOpenRampSlow_s')['v'], C('kMvCockHold_s')['v'])),
        ('latch_magnet', OrderedDict([('design', latch['selected']), ('open', latch['open'])])),
        ('hardware_gate', 'MV_LATCH_G = MV_LATCH_GB AND PRAIL_OK (U306): an LTC4365 trip drops the latch without firmware'),
        ('spec_v1', CL.cite(88, 'MV ACTUATOR SPEC v1', 260)),
        ('close_time', tv('MV-P dashpot ~30 ms ESTIMATE (Mechanical); B-MV-1 bound 0.10 s with flow 0.05-0.26 kg/s (Combustion)', 'MECH/COMB')),
        ('position', 'OPEN/CLOSED microswitches J508'),
        ('superseded_v1', 'v1 ball valve with torsion spring, one-way dog and latch coil; Swagelok 62 ball fails the opener torque 14x (Mechanical)')])
    doc['actuators'] = act

    # ---------------------------------------------------------------------------------------------------- igniter (v1 key)
    doc['igniter'] = OrderedDict([
        ('type', 'torch: spark coil (IGBT, hardware-limited dwell) + SOL1 N2O and SOL2 propane solenoids (12 V, ARM-gated); P_torch flame confirmation'),
        ('torch_gate', C('kTorchGate_s')), ('torch_lit', C('kTorchLitAbs_Pa')), ('torch_confirm_ticks', C('kTorchConfirmN')),
        ('torch_arm_zero_max', C('kTorchArmZeroMax_Pa')), ('chamber_vented_for_spark', C('kPcVentedMax_Pa')),
        ('spark_dwell', C('kSparkDwell_s')), ('light_threshold', tv('v2.9 relative rule (light_rule_v2p9); eng::kIgnitionPcAbs_Pa 3.0 bar abs WITHDRAWN (LEAD 2026-10-13)', 'LEAD')),
        ('ignition_lift_table', tv('17-row lift-vs-T_tank table 0.1928-0.2520 mm (config.h kIgnLiftTab_m, CF-3 temperature-dependent table; '
                                   'start_monitors_v2p9.cf3_lift_table)', 'CF-3 pending / DERIVED')),
        ('timing_only_ground_start', 'SET_TORCH_GATE with the key, stand only (finite load cell), first start of the arming session'),
        ('superseded_v1', 'v1 arc / spark-coil / pyro channel options (igniter selected by Combustion: torch)')])

    # ---------------------------------------------------------------------------------------------------- sensors (v1 key)
    dec = pct['A_ranges']['decision']['v'] if 'decision' in pct['A_ranges'] else pct['D_summary']
    sens = OrderedDict()
    sens['pressure_transducers'] = OrderedDict([
        ('selection', tv(dec, 'DESIGN pc_transducer_v2; lead line 73 (3)')),
        ('connectors', 'Pc J601, P_feed J602 (FS-01 MV-outlet block, Mechanical), P_tank J603, P_torch J901 (pc_transducer_v2 text says J610: wrong, J610 is ENC_A)'),
        ('hw_ovp', tv('31.47 bar g = 32.48 bar abs nominal on the 070BG; band 30.90-34.06 bar abs; firmware abort 30 bar abs', 'DERIVED pc_transducer_v2 C')),
        ('fault_window', OrderedDict([('min', C('kPcSensorMin_V')), ('max', C('kPcSensorMax_V'))])),
        ('auto_zero', OrderedDict([('Pc', C('kAutoZeroTime_s')), ('P_torch_arm_max', C('kTorchArmZeroMax_Pa'))]))])
    sens['thermocouples'] = OrderedDict([
        ('channels', ['TC1 type K case az 90 (MAX31856 U604)', 'TC2 type K case az 270 (U605)', 'TC3 type K nozzle holder (U606)',
                      'TC4 type K bore top (U904; CF-3/T1 evidence, flight TO-DEFINE)', 'TC5 type T MSS-1 riser-foot TEE (U905)',
                      'TC6 type T MSS-2 NC-valve outlet FS-01 (U906)']),
        ('correction', 'CHANGELOG line 84 said "ECU carries 7 MAX31856": the firmware inputs and the v2.3 schematic carry 6 MAX31856 plus the servo-bracket NTC'),
        ('case_abort', C('kCaseOverTemp_K')), ('relight_refusal', C('kCaseRelightMax_K')),
        ('mss_role', 'flight: telemetry only (lead line 83); stand rules R1/R2 (R3 deleted, lead line 107)')])
    sens['temperature_other'] = ['DS18B20 x2 tank wall + #3 bay (TVC bracket) on 1-Wire (J608/J614)', 'NTC 10k pintle-servo bracket (J609, flag 60 C)']
    sens['encoders'] = 'AS5048A x3 (gimbal A/B J610/J611, pintle crank J612), SPI1 1 MHz over cable'
    sens['load_cell'] = v1['sensors']['load_cell_test_stand']
    sens['stand_fast_pc'] = CL.cite(79, 'Stand-only fast high-range Pc channel adopted', 120)
    sens['imu'] = 'FC side (ADIS16470 per the GNC/FC record): filter delay UNKNOWN (over_thrust)'
    sens['superseded_v1'] = 'v1 Pc 500PG and feed/tank 01KPG codes; TC list (4 x K); ADXL1002 option'
    doc['sensors'] = sens

    # ---------------------------------------------------------------------------------------------------- power, rates, link, fail-safe, harness (v1 keys)
    pb = OrderedDict(v1['power_budget'])
    pb['rails'] = OrderedDict(v1['power_budget']['rails'])
    pb['rails']['PRAIL'] = 'pintle servo rail 7.49 V typ (TPS552882 on ARM_BUS) behind the LTC4365 OV disconnect'
    pb['rails']['VBAT_SERVO'] = 'TVC servos A/B on VBAT through the watchdog-gated Q401 + Q403 (the MV opener is on ARM_BUS, the pintle on PRAIL)'
    pb['arm_bus_peak_vs_F301'] = tv('TO-CHECK: MV opener stall 9.2 A at 7.4 V (DATASHEET) / 10.4 A at 8.4 V (ASSUMED) + pintle rail input <= 4.33 A + 12 V boost loads '
                                    'vs F301 15 A (Littelfuse 0297015 curve)', 'OPEN')
    pb['heater_interlock'] = 'J616 GSE heater permit: <= 28 V, <= 1 A at the contact; hardware cut by ARM plug or ARM bus'
    pb['superseded_v1'] = 'v1 fusing (logic 1 A, IGN 5 A, SOL 3 A) -> v2.3: F101 25 A main, F102 2 A logic, F301 15 A ARM, F501 3 A 12 V boost'
    pb['fusing'] = OrderedDict([('F101', '25 A ATM main'), ('F102', '2 A 1206 logic'), ('F301', '15 A ATM ARM bus'), ('F501', '3 A 1206 12 V boost')])
    doc['power_budget'] = pb
    lr = OrderedDict(v1['loop_rates_and_latency'])
    lr['tick'] = C('kDt_s')
    lr['fc_command_period'] = C('kFcCmdPeriod_s')
    lr['hw_watchdog'] = C('kHwWatchdog_s')
    lr['tlm_relight_Hz'] = tv(50, 'DESIGN protocol.h')
    lr['fc_thrust_Hz'] = C('kFcThrustRate_Hz')
    lr['end_to_end_over_thrust'] = 'see over_thrust.rg19_budget_known_terms_s'
    doc['loop_rates_and_latency'] = lr
    doc['link_loss'] = OrderedDict([('degraded_after', C('kLinkDegraded_s')), ('lost_after', C('kLinkLost_s')),
                                    ('action_on_lost', v1['link_loss']['action_on_lost'])])
    fs = OrderedDict(v1['fail_safe_states'])
    fs['ECU power loss'] = 'MV latch drops -> MV-P spring + pressure bias close it (dashpot ~30 ms ESTIMATE); the pintle spring closes the unpowered HV69 (B-PNT-1 back-drive check); igniter dead'
    fs['pintle rail fail-high'] = 'LTC4365 OV disconnect 8.06-8.34 V: servo unpowered, spring closes; PRAIL_OK low drops the MV latch in hardware (U306); firmware PINTLE_FAULT abort'
    fs['Pc over-pressure'] = 'hardware comparator latch 31.47 bar g removes the ARM bus independent of firmware; firmware abort at 30 bar abs'
    fs['superseded_v1'] = 'v1 "latch drops -> spring closes main valve (ball valve)"'
    doc['fail_safe_states'] = fs
    h = OrderedDict(v1['harness_across_gimbal'])
    h['bundle'] = ('Pc (3 + shield), pintle servo HV69 (3 x AWG20 on PRAIL), pintle encoder (4 + shield), case TCs x2 + nozzle holder TC (K), '
                   'bore-top TC (stand), servo-bracket NTC (2); P_feed no longer crosses: J602 sits on the fixed-side FS-01 block (Mechanical); '
                   'MSS-1 side of the gimbal TO-CONFIRM with Mechanical')
    h['lengths'] = 'TO-DEFINE on the CAD v3.4 solids (the coil re-route changes the crossing)'
    doc['harness_across_gimbal'] = h

    # ---------------------------------------------------------------------------------------------------- GSE, BOM, bench plan
    doc['gse_interface'] = OrderedDict([
        ('arming_plug', 'J301 XT30, remove-before-flight shorting link; removes the ARM bus in hardware'),
        ('mode_strap', 'J620 [MODE_A, MODE_B, GND]: FLIGHT plug grounds MODE_B, STAND plug grounds MODE_A; open or both = invalid -> ARM refused; '
                       'stand also needs a finite load-cell reading (MODE_MISMATCH otherwise)'),
        ('heater_permit', 'J616 [HTR_ILK_SW, GND]: low-side permit for the GSE tank heater, <= 28 V and <= 1 A; SAFE only'),
        ('can', 'J201 to the FC (flight) or the test-stand box (same protocol encoders)'),
        ('stand_arm_loop', 'burst-disc break-wire in series with the stand ARM loop (lead line 88/89)'),
        ('umbilical', v1['power_budget'].get('ground_power'))])
    doc['bom'] = OrderedDict([('file', '06-electronics/results/bom_v2p1.csv (v2.1: + head-end bleed provision)'), ('summary', bom)])
    doc['bench_plan'] = OrderedDict([
        ('file', '06-electronics/docs/bench_plan_v2.md'),
        ('tests', ['LEAK-1', 'B-PWR-1', 'B-PWR-2', 'B-ECU-1', 'B-IGN-1', 'B-MV-1', 'B-TVC-1', 'B-PNT-1', 'B-PC-1', 'B-FC-1', 'HIL-OT-1',
                   'HIL-TR-1', 'CF-3', 'CF-4', 'B-BLEED-1', 'IGN-1', 'T1-T4 F_acc'])])

    # ---------------------------------------------------------------------------------------------------- open issues
    idm_txt = None
    if idm:
        lp = idm['lit_pc_30ms_after_light_bar_abs']
        idm_txt = ('replay of all %d S5 runs: lit Pc 30 ms after the light min %.2f / p05 %.2f / p50 %.2f / p95 %.2f bar abs vs threshold %.1f; %.1f %% below'
                   % (idm['n'], lp['min'], lp['p05'], lp['p50'], lp['p95'], idm['light_threshold_bar_abs']['v'], 100 * idm['frac_below_threshold']))
    doc['open_issues'] = [
        OrderedDict([('id', 'OI-IGN-DET'), ('severity', 'HIGH (cross-discipline)'),
                     ('issue', 'light-detection margin at the v2.8 ignition lift: S5 dispersed pad-start MC %d/%d NO_IGNITION on a LIT plant since v2.8.1 '
                               '(v2.7 at 20 %% lift: 0). The lit plant Pc at 0.2039 mm sits at the 3.0 bar abs threshold (nominal replay 3.02 bar abs; '
                               'low-Cd/low-efficiency replay plateau 2.84-2.99 bar abs)' % (s5_causes.get('3', 0), s5['runs'])
                               + ('; ' + idm_txt if idm_txt else '')),
                     ('owner', 'Combustion (threshold and lift) + Electronics (detection logic)'),
                     ('closure', 'Combustion states the lit Pc at the ignition lift over its band; options: threshold inside 1.87-2.66 bar abs (S9 bounds), larger '
                                 'lift (inventory), or detection on the rise above the measured cold-flow plateau; IGN-1/T1 measure')]),
        OrderedDict([('id', 'OI-RELIGHT-A1'), ('severity', 'HIGH'), ('issue', 'A1 relight not frozen (RG-01): re-routed segment volume and the GNC re-fly pending; '
                                                                             'drained-segment fault path to re-run on the published re-route'),
                     ('owner', 'Mechanical / Electronics / GNC'), ('closure', 'fault_path_v2 --segment-json <re-route file>; GNC re-fly')]),
        OrderedDict([('id', 'OI-GIMBAL-JAM'), ('severity', 'MEDIUM'), ('issue', 'S6 gimbal_jam_moving_cmd FAIL (small-amplitude jam undetected)'),
                     ('owner', 'Electronics + GNC'), ('closure', 'servo-frame mismatch metric after the GNC false-abort trade')]),
        OrderedDict([('id', 'OI-TB-MEOP'), ('severity', 'ACCEPTED'), ('issue', 'S6 throat block Pc 53.4 bar abs > MEOP for 72 ms'),
                     ('owner', 'Mechanical FEA'), ('closure', 'LC-TB70 / LC-TB-S in the assembled FEA')]),
        OrderedDict([('id', 'OI-HAL'), ('severity', 'HIGH'), ('issue', 'hardware HAL not written; TLM_SLOW 0x110 undefined; 53 ARM double-promotion warnings'),
                     ('owner', 'Electronics'), ('closure', 'HAL v1 with B-ECU-1')]),
        OrderedDict([('id', 'OI-FC'), ('severity', 'HIGH'), ('issue', 'GNC tracker / FSW not yet in the flight computer; IMU filter delay unknown; RG-16 mass budget'),
                     ('owner', 'FC owner + GNC'), ('closure', 'B-FC-1, HIL-OT-1')]),
        OrderedDict([('id', 'OI-TIMEBASE'), ('severity', 'MEDIUM'), ('issue', 'no common time base yet for DAQ, CAN analyser and ECU'),
                     ('owner', 'Electronics'), ('closure', '1 Hz sync GPIO into the stand DAQ; alignment <= 1 ms (bench_plan_v2)')]),
        OrderedDict([('id', 'OI-PFEED-SPOF'), ('severity', 'MEDIUM'), ('issue', 'P_feed is a single point for the relight path choice (invalid -> UNKNOWN -> prep path) and S1'),
                     ('owner', 'Electronics'), ('closure', 'accepted fail-safe direction; second transducer only if the stand shows dropouts')]),
        OrderedDict([('id', 'OI-LATE-FLIP'), ('severity', 'MEDIUM'), ('issue', 'a coast encoder loss after the last TLM_RELIGHT frame flips the path late (S10 evidence case)'),
                     ('owner', 'GNC planning'), ('closure', 'GNC stale-flag rule covers it only if the FC plans on the last fresh frame')]),
        OrderedDict([('id', 'OI-B1-WIND'), ('severity', 'MEDIUM'), ('issue', 'B1 launch commit mean wind < 6 m/s until B-PNT-1 shows the drive lag inside the MC tau'),
                     ('owner', 'Electronics bench'), ('closure', 'B-PNT-1 closed-loop t10-90')]),
        OrderedDict([('id', 'OI-RAIL'), ('severity', 'MEDIUM'), ('issue', 'LTC4365 UV ASSUMED; Q803 enhancement; RPM0026A footprint placeholder; ARM-bus peak vs F301'),
                     ('owner', 'Electronics'), ('closure', 'datasheet read (proxy) or bench; B-PWR-1/2')]),
        OrderedDict([('id', 'OI-MV-CAM'), ('severity', 'LOW'), ('issue', 'MV-P opener cam-limited 61 ms opening (bench B-MV-1)'),
                     ('owner', 'Mechanical + Electronics'), ('closure', 'B-MV-1')]),
        OrderedDict([('id', 'OI-TRIM'), ('severity', 'LOW'), ('issue', 'map-trim plateau (Pc loop trim authority +/-40 %) not yet characterised on hardware'),
                     ('owner', 'Electronics + Combustion'), ('closure', 'T1-T4 logs')]),
        OrderedDict([('id', 'OI-DOC'), ('severity', 'LOW'), ('issue', 'pc_transducer_v2 labels P_torch J610 (is J901); protocol.h FC_THRUST valid-window comment wording'),
                     ('owner', 'Electronics'), ('closure', 'next calc / firmware release')]),
    ]
    doc['requests'] = [
        'Mechanical: publish the re-routed MV-to-seat segment volume (coil re-route, v3.4.1) -> Electronics re-runs fault_path_v2 drained case',
        'Combustion: lit chamber Pc at the v2.8 ignition lift (0.2039 mm) over the c*/regression/Cd band, and the light threshold it supports (OI-IGN-DET)',
        'GNC: sim6 F_acc / gimbal trace vectors for HIL trace match (RG-13, HIL-TR-1); re-fly A1 relight with the fault_path_v2 slug times (RG-01)',
        'FC owner: ADIS16470 filter setting and its group delay; FC scheduling budget (RG-19)',
        'Founders: confirm owned bench instruments (scope, e-load, PSU, DAQ) so bom_v2 section H can drop those lines']
    doc['coordinator_items_reported'] = OrderedDict([
        ('PRIMED', 'PRIMED = DIRECT_PATH alias in protocol.h; not a vapour detector'),
        ('RG-15', 'FC_THRUST does not freeze on PC_SENSOR; k_est_asc and the B apex predictor freeze on the 0xFFFF markers'),
        ('MV_early_open', 'DROPPED'), ('bleed', 'fallback budget line only (relight_interface.head_end_bleed)'),
        ('W', 'build constant (firmware.W_build_constant)'),
        ('fault_path', 'slugs 13.5 / 19 cm3 run on fw v2.8.3; drained case provisional on the v3.4 segment until the re-route volume is published')])

    # ---------------------------------------------------------------------------------------------------- v2.9 additions (2026-10-13)
    ign = jload(os.path.join(RES, 'ignition_rule_sil_v1.json'))
    fp3 = jload(os.path.join(RES, 'fault_path_v3.json'))
    hbp = jload(os.path.join(RES, 'hbleed_provision_v1.json'))
    s12 = json.loads(re.sub(r'\bnan\b', 'null', rd(os.path.join(RES, 'sil_v2p9', 'S12_bleed.json'))))
    s5 = json.loads(re.sub(r'\bnan\b', 'null', rd(os.path.join(RES, 'sil_v2p9', 'S5_mc.json'))))
    po = ign['post']
    doc['light_rule_v2p9'] = OrderedDict([
        ('rule', tv('P0 = mean of filtered/raw gauge Pc over [E1 - 20 ms, E1]; |P0| > residual + 0.1 bar -> ambient (BASE_AMB); light (E2) = filtered AND raw '
                    'rise over P0 >= 0.8 bar with filtered AND raw Pc >= floor, for 10 consecutive 1 kHz ticks; legacy 3.0 bar abs rule WITHDRAWN', 'LEAD/COMB')),
        ('kIgnRise_Pa', C('kIgnRise_Pa')), ('kIgnConfirmRelN', C('kIgnConfirmRelN')), ('kIgnPreN', C('kIgnPreN')),
        ('kIgnFloorAbs_Pa', tv('1.8e5 Pa abs until B-PC-1 shows residual <= 0.3 bar, then 2.0e5 (kBpc1Shown)', 'LEAD/COMB')),
        ('kIgnBaseCheck_Pa', tv('residual + 0.1 bar (0.7 bar now, 0.4 bar after B-PC-1)', 'LEAD')),
        ('sil_a1_relight_mc', OrderedDict([('runs_lit', 300), ('pad_aborts_before_relight', po['lit_runs_pad_abort_before_relight']),
                                           ('pad_abort_cause', 'TVC_SUPPLY (pre-existing pad refusal at the battery-R corners, also in S5 v2.8.3)'),
                                           ('light_rule_aborts', po['lit_light_rule_aborts']), ('unlit_false_lights', ign['A_relative']['unlit_false_lights']),
                                           ('E2_minus_light_ms', po['E2_minus_light_ms']), ('A3_ratio_min', po['A3_ratio_min']),
                                           ('unlit_rise_max_Pa', ign['A_relative']['unlit_rise_max_Pa_max']),
                                           ('residual_corners_B', '%d cases, %d fail' % (ign['B_cases'], ign['B_fail'])),
                                           ('tag', 'SIL (ASSUMED/SIM plant); target E2 <= ~15 ms after light NOT met: 16-18 ms = plant rise + 50 Hz filter + 10 ms')])),
        ('sil_s5_pad_mc', OrderedDict([('runs', s5['runs']), ('aborts', s5['aborts']), ('light_to_E2_ms_max', s5.get('light_to_E2_ms_max')),
                                       ('note', 'v2.8.3: 31 NO_IGNITION on lit pad starts (legacy rule); v2.9: 0; the 27 TVC_SUPPLY + 1 PC_OVERPRESSURE are unchanged')])),
    ])
    doc['start_monitors_v2p9'] = OrderedDict([
        ('A3', tv('(Pc - P0)/(Pc_map_lo - P0) < 0.40 for 20 ms in RUN; Pc_map_lo = min(40 ms-lagged map, instantaneous map) at the encoder lift; '
                  'denominator >= 0.5 bar (the lagged map alone false-tripped on fast throttle-downs: SIL finding)', 'LEAD/COMB + DESIGN')),
        ('A5', tv('8.0 bar abs for 5 ms from E1 to the ramp start (unchanged); with the 10 ms light confirmation a fast late light can trip A5 first', 'LEAD/COMB')),
        ('A7', tv('HOLD band from E1 (lo P0 - 0.3 bar), START band E2->E3 (lo = A3 threshold on the map, hi 1.3 x max(map, 5.3 bar)), RUN_MAP after E3 '
                  '(0.7..1.3 x map); 50 ms; IGNITION / stand -> PC_SENSOR abort, flight RUN -> flag; A7 kept ARMED E1->E3 with the lit-start band; '
                  'the rate criterion is not implemented (written reason: no Combustion rate bound yet)', 'LEAD/COMB + DESIGN')),
        ('E3', tv('first RUN tick with the ramp done and Pc >= P0 + 0.9 (setpoint - P0), or E2 + 0.6 s', 'DESIGN')),
        ('cf3_lift_table', tv('17 rows 0.1928-0.2520 mm vs T_tank (A1 row 286.7 K 0.2178 mm vs the flat 0.2039 mm); warm rows reach 37.4 g/s, +0.8 % over 37.1 g/s', 'CF-3 pending / DERIVED')),
    ])
    doc['drogue_release_support'] = OrderedDict([
        ('rule_owner', 'FC (LEAD decision 2026-10-13 CHANGELOG): release at E2 AND [measured Pc >= 3.0 bar abs OR the 0.8 bar rise held continuously to E2 + 0.10 s]'),
        ('ecu_publishes', [tv('TLM_FAST 0x100 at 500 Hz: d1 b0-b3 state (decoders mask d1 & 0x0F), b4 E2 of this start, b5 rise now (filtered AND raw over P0), '
                              'b6 rise held since E2 (cleared at the first tick without it), b7 rise held to E2 + kDrogueRiseHold_s (latched); d2-d3 Pc kPa abs '
                              '(0xFFFF = invalid), d6-d7 fault bits incl. PC_SENSOR', 'DESIGN protocol.h (tlmf::)'),
                           tv('E2 timestamp = EVENT 0x120 STATE (RUN entry) t_ms', 'DESIGN')]),
        ('kDrogueRiseHold_s', C('kDrogueRiseHold_s')),
        ('sil_a1_relight', OrderedDict([('rise_held_to_E2_0p10_s', '%d of %d lit runs' % (po['drogue_rise_held_to_E2_0p10'], po['E2_minus_light_ms']['n'])),
                                        ('E2_to_Pc_3bar_ms', po['drogue_E2_to_Pc3bar_ms']), ('E2_to_release_ms', po['drogue_E2_to_release_ms']),
                                        ('limit', 'the SIL plant does not reproduce the GNC fuel-starved plateau (2.4-3.4 bar abs for 0.1-0.4 s)')])),
        ('tests', 'test_core (25)-(26): bits, latch at E2 + 100 ms, dip clears held, d1 packing, log v10 tlm_flags'),
    ])
    doc['head_end_bleed_provision'] = OrderedDict([
        ('architecture', tv('2 NC valves in series (V1 at the engine-side tee of the T4 crown + FD-01 radial taps via one -2 line across the gimbal; '
                            'V1 and V2 on the fixed side), restriction downstream of V2, P_mid transducer between them; ECU drives V1 on pin 15 (U304) and '
                            'V2 on pin 24 (U307), low-side on +12V_ARM (J509/J510); P_mid comparator on the pin 23 ladder', 'DESIGN / MECH v3.4.1 relay')),
        ('pad_bit', 'PREPRESS steps S0-S4 (valve pattern vs P_mid); any failure -> BLEED_FAULT'),
        ('purge', tv('PURGE state: MV open, pintle seated, V1+V2 open, t_purge %.1f s; pre-scheduled (Cmd PURGE) or sequence-integrated (RELIGHT); '
                     'PINTLE_FAULT / encoder / MV OPEN / P_feed fill checks active; V1-first closure confirmed by P_mid, else BLEED_FAULT at E0 + 0.15 s'
                     % C('kPurgeRelight_s')['v'], 'LEAD + DESIGN')),
        ('in_burn_stuck_open', 'invisible on P_feed (0.016 bar) and Pc (SIL -0.02..-0.05 bar); seen only by the P_mid leak monitor at +0.21 s: flight flag + EVENT, '
                               'stand BLEED_FAULT; V2-only stuck open is latent until the next pad BIT; the next purge relight then ends BLEED_FAULT (V1 unconfirmable)'),
        ('ladder', hbp['ladder']), ('pmid_comparator', hbp['pmid_comparator']), ('vent_time', hbp['vent_time']), ('coil', hbp['coil']),
        ('sil_s12', OrderedDict([('cases', len(s12['cases'])), ('fail', sum(1 for c in s12['cases'] if not c['pass']))])),
        ('sil_s11_fault_path_v3', [OrderedDict([('run', r['tag']), ('unreached_cm3', r['unreached_cm3']),
                                                ('cases', [OrderedDict([('case', c['case']), ('V_cm3', c['V_cm3']), ('first_abort', c['first_abort']),
                                                                        ('cmd_to_E2_s', c['cmd_to_E2_s'])]) for c in r['cases']])]) for r in fp3['runs']]),
    ])
    doc['log_v10'] = tv('LogRecord v10 = 150 bytes (1 kHz): + hbleed io/flags/BIT, P0, rise, det flags, A3 ratio, map Pc, seq4 flags, tlm_flags', 'DESIGN protocol.h')
    doc['sil_fail_dispositions'] = [d for d in doc['sil_fail_dispositions'] if not d['id'].startswith('S9 lit_bias_minus')] + [
        OrderedDict([('id', 'S6 hard_start_0p20s / 0p25s_delay_late_light_inside_W (NEW in v2.9)'),
                     ('checks', 'a late light (0.20 / 0.25 s delay, inside W) continues (v2.8.3: PASS)'),
                     ('why_fails', 'HARD_START (A5 8.0 bar abs for 5 ms) at IGNITION +283 / +331 ms: the 10 ms relative confirmation lets A5 persist first; '
                                   'plant Pc max 26.9 / 28.6 bar abs (< 30 bar A4, < MEOP 45)'),
                     ('flight_path', True), ('disposition', 'OPEN (LEAD/COMB): accept A5 aborting these starts, or change A5/the confirmation'),
                     ('closure', 'lead decision; no firmware change made by Electronics')]),
        OrderedDict([('id', 'S9 +/-1.034 bar TEB cases (relative rule)'),
                     ('checks', 'light detection at the full 070BG TEB post-zero bias'),
                     ('why_fails', '-TEB: lit, RUN +22 ms after light, then A3 on the biased ratio; +TEB unlit: filtered 1.87 bar abs > 1.8 floor -> false E2 -> '
                                   'RUN -> A3 FLAMEOUT at IGNITION +0.14 s'),
                     ('flight_path', True), ('disposition', 'OPEN (LEAD): outside the adopted +/-0.6 bar residual band'),
                     ('closure', 'B-PC-1 residual <= 0.3 bar -> floor 2.0 bar abs (> 1.87)')]),
    ]
    def oi(i, sev, issue, owner):
        return OrderedDict([('id', i), ('severity', sev), ('issue', issue), ('owner', owner)])
    doc['open_issues'] += [
        oi('OI-A5-LATE', 'HIGH', 'v2.9 light rule (10 ms) + unchanged A5 (8.0 bar abs, 5 ms): S6 late lights 0.20/0.25 s inside W now abort HARD_START '
           '(v2.8.3 continued; plant Pc max 26.9/28.6 bar abs)', 'LEAD / Combustion'),
        oi('OI-TEB-FALSE-LIGHT', 'MEDIUM', 'S9 +1.034 bar post-zero bias: unlit filtered 1.87 bar abs > floor 1.8 -> false E2 -> RUN -> A3 FLAMEOUT +0.14 s; '
           'closed by B-PC-1 <= 0.3 bar (floor 2.0)', 'LEAD / Electronics (B-PC-1)'),
        oi('OI-E2-LATENCY', 'LOW', 'E2 - light 16-18 ms in SIL (target ~15 ms): plant rise + 50 Hz filter + 10 ms persistence; IGN-1 measures', 'Combustion / Electronics'),
        oi('OI-A3-MARGIN', 'MEDIUM', 'A3 ratio minimum 0.454 at the A1 relight MC (threshold 0.40) during the start ramp; after E3 0.719', 'Combustion'),
        oi('OI-BLEED-COIL', 'HIGH', 'Burkert 6027 HP: 24 V DC listed, ECU valve rail +12V_ARM (U3V70F12); 2 x 16 W -> +2.7 A for ~2.6 s per purge at 12 V; '
           '12 V coil or a 24 V boost, rail budget and valve mass TO-VERIFY; HP seat PEEK/FKM medium -10..80 C and N2O compatibility TO-VERIFY',
           'Electronics / Mechanical'),
        oi('OI-BLEED-VOL', 'MEDIUM', 'unreached vapour with taps (2 deg 4.84 cm3, 10 deg 15.91 cm3) from an UNPUBLISHED Mechanical workdir file', 'Mechanical'),
    ]
    for o in doc['open_issues']:
        if o.get('id') == 'OI-IGN-DET':
            o['status_v2p9'] = ('CLOSED IN SIL by the LEAD relative light rule (firmware v2.9): S5 pad MC NO_IGNITION 31/300 (v2.8.3) -> 0/300; '
                                'A1 relight MC 0 light-rule aborts / 0 unlit false lights; hardware evidence = IGN-1 / B-PC-1')
    doc['change_summary_v1_to_v2'].append('v2.9 update (2026-10-13): relative light rule, A3/A5/A7/E3 start monitors, CF-3 lift table, coast re-zero, head-end '
                                          'bleed provision (PURGE, pad BIT, P_mid ladder; schematic v2.4, BOM v2.1), drogue-release telemetry (TLM_FAST d1 '
                                          'b4-b7), log v10 (150 B); SIL record sil_v2p9 (S6: 2 NEW late-light HARD_START fails; S9 TEB cases re-dispositioned)')
    doc['coordinator_items_reported']['drogue_release_support'] = ('TLM_FAST d1 b4-b7 + EVENT STATE t_ms implemented (firmware v2.9, tests (25)-(26)); '
                                                                   'SIL A1: rise held to E2 + 0.10 s in all lit runs, E2 -> Pc 3.0 bar abs max 43 ms')
    doc['inputs']['files_read_sha256_16'] = READ
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('electronics.json v2 -> %s (%d top-level keys, %d abort causes, %d pins, %d open issues)'
          % (a.out, len(doc), len(matrix), len(pins), len(doc['open_issues'])))


if __name__ == '__main__':
    main()
